from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "research_grill_state_machine",
    ROOT / "scripts/research_grill_state_machine.py",
)
assert SPEC and SPEC.loader
SM = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SM
SPEC.loader.exec_module(SM)


def event(
    rows: list,
    event_type,
    action=None,
    bindings: dict[str, str] | None = None,
    outcome=None,
    *,
    expected_tail: str | None = None,
):
    previous = rows[-1].event_hash if rows else SM.EMPTY_LEDGER_TAIL
    row = SM.ValidatedEvent(
        seq=len(rows),
        previous_event_hash=previous,
        event_hash=f"sha256:event-{len(rows)}",
        event_type=event_type,
        requested_action=action,
        expected_ledger_tail=previous if expected_tail is None else expected_tail,
        bindings=tuple(sorted((bindings or {}).items())),
        outcome=outcome,
    )
    rows.append(row)
    return row


def checkpoint(rows: list):
    return event(
        rows,
        SM.EventType.CHECKPOINT_OPENED,
        bindings={"action_order": ",".join(action.value for action in SM.ACTION_ORDER)},
    )


def opened(rows: list, action, suffix: str = "A"):
    return event(
        rows,
        SM.EventType.ACTION_OPENED,
        action,
        {
            "core_hash": f"core-{suffix}",
            "evidence_manifest_hash": f"manifest-{suffix}",
            "review_plan_hash": "plan",
        },
    )


def finalized(rows: list, action, opened_row, suffix: str = "A"):
    return event(
        rows,
        SM.EventType.ACTION_FINALIZED,
        action,
        {
            "opened_event_hash": opened_row.event_hash,
            "final_core_hash": f"core-{suffix}",
            "final_manifest_hash": f"manifest-{suffix}",
            "review_cycle_hash": f"review-{suffix}",
            "review_phase": "initial",
            "review_verdict": "pass",
        },
        SM.Outcome.AUTHORIZED,
    )


class ResearchGrillStateMachineTests(unittest.TestCase):
    def test_event_and_result_models_are_frozen(self) -> None:
        rows = []
        row = checkpoint(rows)
        with self.assertRaises(FrozenInstanceError):
            row.seq = 2
        state = SM.evaluate(rows)
        with self.assertRaises(FrozenInstanceError):
            state.tail_hash = "changed"

    def test_empty_stream_is_valid_and_nonauthorizing(self) -> None:
        state = SM.evaluate(())
        self.assertEqual(state.decision, SM.DecisionKind.VALID)
        self.assertEqual(SM.authorization(state, SM.Action.STATIC_ACQUISITION).decision, SM.DecisionKind.NOT_AUTHORIZED)

    def test_all_actions_finalize_as_exact_prefix(self) -> None:
        rows = []
        checkpoint(rows)
        for index, action in enumerate(SM.ACTION_ORDER):
            opened_row = opened(rows, action, str(index))
            finalized(rows, action, opened_row, str(index))
        state = SM.evaluate(rows)
        self.assertEqual(state.finalized_actions, SM.ACTION_ORDER)
        self.assertEqual(SM.authorization(state, SM.Action.SCALE_LAUNCH).decision, SM.DecisionKind.AUTHORIZED)

    def test_action_before_checkpoint_is_rejected(self) -> None:
        rows = []
        opened(rows, SM.Action.STATIC_ACQUISITION)
        self.assertIn("before checkpoint", SM.evaluate(rows).message)

    def test_multiple_checkpoint_opens_are_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        checkpoint(rows)
        self.assertIn("exactly once", SM.evaluate(rows).message)

    def test_action_skip_is_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        opened(rows, SM.Action.HUMAN_ORACLE)
        self.assertIn("skip", SM.evaluate(rows).message)

    def test_reopen_is_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        first = opened(rows, SM.Action.STATIC_ACQUISITION)
        finalized(rows, SM.Action.STATIC_ACQUISITION, first)
        opened(rows, SM.Action.STATIC_ACQUISITION, "again")
        self.assertIn("reopen", SM.evaluate(rows).message)

    def test_open_while_action_active_is_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        opened(rows, SM.Action.STATIC_ACQUISITION)
        opened(rows, SM.Action.HUMAN_ORACLE, "B")
        self.assertIn("another action", SM.evaluate(rows).message)

    def test_stale_expected_tail_is_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        event(
            rows,
            SM.EventType.ACTION_OPENED,
            SM.Action.STATIC_ACQUISITION,
            {"core_hash": "c", "evidence_manifest_hash": "m", "review_plan_hash": "p"},
            expected_tail="sha256:stale",
        )
        self.assertIn("stale expected ledger tail", SM.evaluate(rows).message)

    def test_non_contiguous_seq_is_rejected(self) -> None:
        rows = []
        first = checkpoint(rows)
        rows[0] = SM.ValidatedEvent(
            2, first.previous_event_hash, first.event_hash, first.event_type,
            first.requested_action, first.expected_ledger_tail, first.bindings, first.outcome,
        )
        self.assertIn("non-contiguous", SM.evaluate(rows).message)

    def test_initial_blocked_cannot_finalize(self) -> None:
        rows = []
        checkpoint(rows)
        opened_row = opened(rows, SM.Action.STATIC_ACQUISITION)
        event(
            rows,
            SM.EventType.ACTION_FINALIZED,
            SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "final_core_hash": "core-A", "final_manifest_hash": "manifest-A",
                "review_cycle_hash": "review", "review_phase": "initial",
                "review_verdict": "blocked",
            },
            SM.Outcome.ARCHITECTURE_RESET_REQUIRED,
        )
        self.assertIn("requires correction", SM.evaluate(rows).message)

    def test_one_correction_and_passing_rereview_authorize(self) -> None:
        rows = []
        checkpoint(rows)
        opened_row = opened(rows, SM.Action.STATIC_ACQUISITION)
        correction = event(
            rows,
            SM.EventType.CORRECTION_APPLIED,
            SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "before_core_hash": "core-A", "after_core_hash": "core-B",
                "before_manifest_hash": "manifest-A", "after_manifest_hash": "manifest-B",
                "initial_review_cycle_hash": "initial-review-A",
            },
        )
        event(
            rows,
            SM.EventType.ACTION_FINALIZED,
            SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "correction_event_hash": correction.event_hash,
                "final_core_hash": "core-B", "final_manifest_hash": "manifest-B",
                "review_cycle_hash": "review-B", "review_phase": "re_review",
                "review_verdict": "pass",
            },
            SM.Outcome.AUTHORIZED,
        )
        state = SM.evaluate(rows)
        self.assertEqual(state.finalized_actions, (SM.Action.STATIC_ACQUISITION,))
        self.assertEqual(state.action_states[-1].initial_review_cycle_hash, "initial-review-A")

    def test_correction_requires_signed_initial_review_cycle_binding(self) -> None:
        rows = []
        checkpoint(rows)
        opened_row = opened(rows, SM.Action.STATIC_ACQUISITION)
        event(
            rows, SM.EventType.CORRECTION_APPLIED, SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "before_core_hash": "core-A", "after_core_hash": "core-B",
                "before_manifest_hash": "manifest-A", "after_manifest_hash": "manifest-B",
            },
        )
        self.assertIn("initial_review_cycle_hash", SM.evaluate(rows).message)

    def test_second_correction_is_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        opened_row = opened(rows, SM.Action.STATIC_ACQUISITION)
        bindings = {
            "opened_event_hash": opened_row.event_hash,
            "before_core_hash": "core-A", "after_core_hash": "core-B",
            "before_manifest_hash": "manifest-A", "after_manifest_hash": "manifest-B",
            "initial_review_cycle_hash": "initial-review-A",
        }
        event(rows, SM.EventType.CORRECTION_APPLIED, SM.Action.STATIC_ACQUISITION, bindings)
        event(rows, SM.EventType.CORRECTION_APPLIED, SM.Action.STATIC_ACQUISITION, bindings)
        self.assertIn("second correction", SM.evaluate(rows).message)

    def test_correction_branch_is_rejected(self) -> None:
        rows = []
        checkpoint(rows)
        opened_row = opened(rows, SM.Action.STATIC_ACQUISITION)
        event(
            rows, SM.EventType.CORRECTION_APPLIED, SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "before_core_hash": "different", "after_core_hash": "core-C",
                "before_manifest_hash": "manifest-A", "after_manifest_hash": "manifest-C",
                "initial_review_cycle_hash": "initial-review-A",
            },
        )
        self.assertIn("branch", SM.evaluate(rows).message)

    def test_blocked_rereview_is_terminal_and_forbids_later_event(self) -> None:
        rows = []
        checkpoint(rows)
        opened_row = opened(rows, SM.Action.STATIC_ACQUISITION)
        correction = event(
            rows, SM.EventType.CORRECTION_APPLIED, SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "before_core_hash": "core-A", "after_core_hash": "core-B",
                "before_manifest_hash": "manifest-A", "after_manifest_hash": "manifest-B",
                "initial_review_cycle_hash": "initial-review-A",
            },
        )
        event(
            rows, SM.EventType.ACTION_FINALIZED, SM.Action.STATIC_ACQUISITION,
            {
                "opened_event_hash": opened_row.event_hash,
                "correction_event_hash": correction.event_hash,
                "final_core_hash": "core-B", "final_manifest_hash": "manifest-B",
                "review_cycle_hash": "review", "review_phase": "re_review",
                "review_verdict": "blocked",
            },
            SM.Outcome.ARCHITECTURE_RESET_REQUIRED,
        )
        opened(rows, SM.Action.HUMAN_ORACLE, "C")
        self.assertIn("after terminal", SM.evaluate(rows).message)

    def test_terminal_result_revokes_every_previously_authorized_action(self) -> None:
        rows = []
        checkpoint(rows)
        for index, action in enumerate(SM.ACTION_ORDER[:3]):
            opened_row = opened(rows, action, str(index))
            finalized(rows, action, opened_row, str(index))
        scale_open = opened(rows, SM.Action.SCALE_LAUNCH, "scale-A")
        correction = event(
            rows, SM.EventType.CORRECTION_APPLIED, SM.Action.SCALE_LAUNCH,
            {
                "opened_event_hash": scale_open.event_hash,
                "before_core_hash": "core-scale-A", "after_core_hash": "core-scale-B",
                "before_manifest_hash": "manifest-scale-A", "after_manifest_hash": "manifest-scale-B",
                "initial_review_cycle_hash": "initial-review-scale",
            },
        )
        event(
            rows, SM.EventType.ACTION_FINALIZED, SM.Action.SCALE_LAUNCH,
            {
                "opened_event_hash": scale_open.event_hash,
                "correction_event_hash": correction.event_hash,
                "final_core_hash": "core-scale-B", "final_manifest_hash": "manifest-scale-B",
                "review_cycle_hash": "review-scale-B", "review_phase": "re_review",
                "review_verdict": "blocked",
            },
            SM.Outcome.ARCHITECTURE_RESET_REQUIRED,
        )
        state = SM.evaluate(rows)
        self.assertTrue(state.terminal)
        for action in SM.ACTION_ORDER:
            with self.subTest(action=action.value):
                decision = SM.authorization(state, action)
                self.assertEqual(decision.decision, SM.DecisionKind.NOT_AUTHORIZED)
                self.assertIn("revoked", decision.message)

    def test_operational_block_is_distinct_from_validation_error(self) -> None:
        blocked = SM.operational_blocked("runtime unavailable")
        self.assertEqual(blocked.decision, SM.DecisionKind.OPERATIONAL_BLOCKED)
        invalid = SM.evaluate([SM.ValidatedEvent(1, None, "h", SM.EventType.CHECKPOINT_OPENED, None, None)])
        self.assertEqual(invalid.decision, SM.DecisionKind.VALIDATION_ERROR)


if __name__ == "__main__":
    unittest.main()
