"""Pure Research Execution Grill v3 lifecycle state machine.

This module owns sequencing and authorization decisions only.  It deliberately
does not read files, parse JSON, invoke subprocesses, verify signatures, or
evaluate scientific evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Action(str, Enum):
    STATIC_ACQUISITION = "static_acquisition"
    HUMAN_ORACLE = "human_oracle"
    PHASE0_LAUNCH = "phase0_launch"
    SCALE_LAUNCH = "scale_launch"


ACTION_ORDER = tuple(Action)
EMPTY_LEDGER_TAIL = "EMPTY"


class EventType(str, Enum):
    CHECKPOINT_OPENED = "checkpoint_opened"
    ACTION_OPENED = "action_opened"
    CORRECTION_APPLIED = "correction_applied"
    ACTION_FINALIZED = "action_finalized"


class Outcome(str, Enum):
    AUTHORIZED = "authorized"
    ARCHITECTURE_RESET_REQUIRED = "architecture_reset_required"


class ReviewPhase(str, Enum):
    INITIAL = "initial"
    RE_REVIEW = "re_review"


class ReviewVerdict(str, Enum):
    PASS = "pass"
    BLOCKED = "blocked"


class DecisionKind(str, Enum):
    VALID = "valid"
    AUTHORIZED = "authorized"
    NOT_AUTHORIZED = "not_authorized"
    VALIDATION_ERROR = "validation_error"
    OPERATIONAL_BLOCKED = "operational_blocked"


@dataclass(frozen=True)
class ValidatedEvent:
    seq: int
    previous_event_hash: str | None
    event_hash: str
    event_type: EventType
    requested_action: Action | None
    expected_ledger_tail: str | None
    bindings: tuple[tuple[str, str], ...] = ()
    outcome: Outcome | None = None

    def binding(self, name: str) -> str | None:
        for key, value in self.bindings:
            if key == name:
                return value
        return None


@dataclass(frozen=True)
class ActionState:
    action: Action
    opened_event_hash: str
    initial_core_hash: str
    initial_manifest_hash: str
    review_plan_hash: str
    initial_review_cycle_hash: str | None = None
    correction_event_hash: str | None = None
    final_core_hash: str | None = None
    final_manifest_hash: str | None = None
    outcome: Outcome | None = None


@dataclass(frozen=True)
class MachineResult:
    decision: DecisionKind
    message: str
    finalized_actions: tuple[Action, ...] = ()
    action_states: tuple[ActionState, ...] = ()
    open_action: Action | None = None
    terminal: bool = False
    tail_hash: str | None = None


def _error(message: str, *, finalized: list[Action], states: list[ActionState], tail: str | None) -> MachineResult:
    return MachineResult(
        DecisionKind.VALIDATION_ERROR,
        message,
        tuple(finalized),
        tuple(states),
        states[-1].action if states and states[-1].outcome is None else None,
        any(state.outcome is Outcome.ARCHITECTURE_RESET_REQUIRED for state in states),
        tail,
    )


def _required(event: ValidatedEvent, *names: str) -> str | None:
    for name in names:
        if not event.binding(name):
            return name
    return None


def _bindings_are_exact(event: ValidatedEvent, names: set[str]) -> bool:
    return {key for key, _value in event.bindings} == names


def evaluate(events: Iterable[ValidatedEvent]) -> MachineResult:
    """Validate an immutable event stream and derive its lifecycle state."""

    finalized: list[Action] = []
    states: list[ActionState] = []
    checkpoint_opened = False
    terminal = False
    tail: str | None = EMPTY_LEDGER_TAIL

    for position, event in enumerate(events):
        if event.seq != position:
            return _error(f"event[{position}]: non-contiguous seq", finalized=finalized, states=states, tail=tail)
        if event.previous_event_hash != tail:
            return _error(f"event[{position}]: previous_event_hash mismatch", finalized=finalized, states=states, tail=tail)
        if event.expected_ledger_tail != tail:
            return _error(f"event[{position}]: stale expected ledger tail", finalized=finalized, states=states, tail=tail)
        if not event.event_hash:
            return _error(f"event[{position}]: event_hash is required", finalized=finalized, states=states, tail=tail)
        if terminal:
            return _error(f"event[{position}]: event after terminal architecture reset", finalized=finalized, states=states, tail=tail)

        if event.event_type is EventType.CHECKPOINT_OPENED:
            if position != 0 or checkpoint_opened:
                return _error(f"event[{position}]: checkpoint may open exactly once at seq 0", finalized=finalized, states=states, tail=tail)
            if event.requested_action is not None or event.outcome is not None:
                return _error(f"event[{position}]: checkpoint_opened cannot carry action/outcome", finalized=finalized, states=states, tail=tail)
            if not _bindings_are_exact(event, {"action_order"}):
                return _error(f"event[{position}]: checkpoint bindings must be exact", finalized=finalized, states=states, tail=tail)
            if event.binding("action_order") != ",".join(action.value for action in ACTION_ORDER):
                return _error(f"event[{position}]: checkpoint action order mismatch", finalized=finalized, states=states, tail=tail)
            checkpoint_opened = True

        elif event.event_type is EventType.ACTION_OPENED:
            if not checkpoint_opened:
                return _error(f"event[{position}]: action before checkpoint_opened", finalized=finalized, states=states, tail=tail)
            if states and states[-1].outcome is None:
                return _error(f"event[{position}]: cannot open while another action is active", finalized=finalized, states=states, tail=tail)
            if len(finalized) >= len(ACTION_ORDER) or event.requested_action is not ACTION_ORDER[len(finalized)]:
                return _error(f"event[{position}]: action skip, reopen, or out-of-order open", finalized=finalized, states=states, tail=tail)
            missing = _required(event, "core_hash", "evidence_manifest_hash", "review_plan_hash")
            if missing:
                return _error(f"event[{position}]: action_opened missing {missing}", finalized=finalized, states=states, tail=tail)
            if not _bindings_are_exact(event, {"core_hash", "evidence_manifest_hash", "review_plan_hash"}):
                return _error(f"event[{position}]: action_opened bindings must be exact", finalized=finalized, states=states, tail=tail)
            if event.outcome is not None:
                return _error(f"event[{position}]: action_opened cannot carry outcome", finalized=finalized, states=states, tail=tail)
            states.append(ActionState(
                event.requested_action,
                event.event_hash,
                event.binding("core_hash") or "",
                event.binding("evidence_manifest_hash") or "",
                event.binding("review_plan_hash") or "",
            ))

        elif event.event_type is EventType.CORRECTION_APPLIED:
            if not states or states[-1].outcome is not None:
                return _error(f"event[{position}]: correction without an open action", finalized=finalized, states=states, tail=tail)
            current = states[-1]
            if event.requested_action is not current.action:
                return _error(f"event[{position}]: correction action mismatch", finalized=finalized, states=states, tail=tail)
            if current.correction_event_hash is not None:
                return _error(f"event[{position}]: second correction or correction branch", finalized=finalized, states=states, tail=tail)
            missing = _required(
                event,
                "opened_event_hash",
                "before_core_hash",
                "after_core_hash",
                "before_manifest_hash",
                "after_manifest_hash",
                "initial_review_cycle_hash",
            )
            if missing:
                return _error(f"event[{position}]: correction missing {missing}", finalized=finalized, states=states, tail=tail)
            if not _bindings_are_exact(event, {
                "opened_event_hash", "before_core_hash", "after_core_hash",
                "before_manifest_hash", "after_manifest_hash", "initial_review_cycle_hash",
            }):
                return _error(f"event[{position}]: correction bindings must be exact", finalized=finalized, states=states, tail=tail)
            if event.binding("opened_event_hash") != current.opened_event_hash:
                return _error(f"event[{position}]: correction opened-event mismatch", finalized=finalized, states=states, tail=tail)
            if (
                event.binding("before_core_hash") != current.initial_core_hash
                or event.binding("before_manifest_hash") != current.initial_manifest_hash
            ):
                return _error(f"event[{position}]: correction before-state mismatch or branch", finalized=finalized, states=states, tail=tail)
            if (
                event.binding("after_core_hash") == current.initial_core_hash
                and event.binding("after_manifest_hash") == current.initial_manifest_hash
            ):
                return _error(f"event[{position}]: correction must change core or manifest", finalized=finalized, states=states, tail=tail)
            states[-1] = ActionState(
                current.action, current.opened_event_hash, current.initial_core_hash,
                current.initial_manifest_hash, current.review_plan_hash,
                initial_review_cycle_hash=event.binding("initial_review_cycle_hash"),
                correction_event_hash=event.event_hash,
                final_core_hash=event.binding("after_core_hash"),
                final_manifest_hash=event.binding("after_manifest_hash"),
            )

        elif event.event_type is EventType.ACTION_FINALIZED:
            if not states or states[-1].outcome is not None:
                return _error(f"event[{position}]: finalization without an open action", finalized=finalized, states=states, tail=tail)
            current = states[-1]
            if event.requested_action is not current.action:
                return _error(f"event[{position}]: finalization action mismatch", finalized=finalized, states=states, tail=tail)
            missing = _required(event, "opened_event_hash", "final_core_hash", "final_manifest_hash", "review_cycle_hash", "review_phase", "review_verdict")
            if missing:
                return _error(f"event[{position}]: action_finalized missing {missing}", finalized=finalized, states=states, tail=tail)
            expected_final_bindings = {
                "opened_event_hash", "final_core_hash", "final_manifest_hash",
                "review_cycle_hash", "review_phase", "review_verdict",
            }
            if current.correction_event_hash is not None:
                expected_final_bindings.add("correction_event_hash")
            if not _bindings_are_exact(event, expected_final_bindings):
                return _error(f"event[{position}]: action_finalized bindings must be exact", finalized=finalized, states=states, tail=tail)
            if event.binding("opened_event_hash") != current.opened_event_hash:
                return _error(f"event[{position}]: finalization opened-event mismatch", finalized=finalized, states=states, tail=tail)
            expected_core = current.final_core_hash or current.initial_core_hash
            expected_manifest = current.final_manifest_hash or current.initial_manifest_hash
            if event.binding("final_core_hash") != expected_core or event.binding("final_manifest_hash") != expected_manifest:
                return _error(f"event[{position}]: finalization core/manifest mismatch", finalized=finalized, states=states, tail=tail)
            correction_hash = event.binding("correction_event_hash")
            if current.correction_event_hash is None:
                if correction_hash is not None or event.binding("review_phase") != ReviewPhase.INITIAL.value:
                    return _error(f"event[{position}]: initial finalization correction/phase mismatch", finalized=finalized, states=states, tail=tail)
                if event.binding("review_verdict") != ReviewVerdict.PASS.value or event.outcome is not Outcome.AUTHORIZED:
                    return _error(f"event[{position}]: blocked initial review requires correction", finalized=finalized, states=states, tail=tail)
            else:
                if correction_hash != current.correction_event_hash or event.binding("review_phase") != ReviewPhase.RE_REVIEW.value:
                    return _error(f"event[{position}]: re-review correction/phase mismatch", finalized=finalized, states=states, tail=tail)
                verdict = event.binding("review_verdict")
                expected_outcome = Outcome.AUTHORIZED if verdict == ReviewVerdict.PASS.value else Outcome.ARCHITECTURE_RESET_REQUIRED
                if verdict not in {ReviewVerdict.PASS.value, ReviewVerdict.BLOCKED.value} or event.outcome is not expected_outcome:
                    return _error(f"event[{position}]: re-review verdict/outcome mismatch", finalized=finalized, states=states, tail=tail)
            states[-1] = ActionState(
                current.action, current.opened_event_hash, current.initial_core_hash,
                current.initial_manifest_hash, current.review_plan_hash,
                current.initial_review_cycle_hash, current.correction_event_hash,
                expected_core, expected_manifest,
                event.outcome,
            )
            if event.outcome is Outcome.AUTHORIZED:
                finalized.append(current.action)
            else:
                terminal = True

        tail = event.event_hash

    open_action = states[-1].action if states and states[-1].outcome is None else None
    return MachineResult(
        DecisionKind.VALID,
        "event stream is valid",
        tuple(finalized),
        tuple(states),
        open_action,
        terminal,
        tail,
    )


def authorization(result: MachineResult, action: Action) -> MachineResult:
    """Return the exact action authorization decision for a valid state."""

    if result.decision is DecisionKind.VALIDATION_ERROR:
        return result
    if result.terminal:
        return MachineResult(
            DecisionKind.NOT_AUTHORIZED,
            f"{action.value} is revoked by terminal architecture_reset_required",
            result.finalized_actions,
            result.action_states,
            result.open_action,
            result.terminal,
            result.tail_hash,
        )
    if action in result.finalized_actions:
        return MachineResult(
            DecisionKind.AUTHORIZED,
            f"{action.value} is finalized and authorized",
            result.finalized_actions,
            result.action_states,
            result.open_action,
            result.terminal,
            result.tail_hash,
        )
    return MachineResult(
        DecisionKind.NOT_AUTHORIZED,
        f"{action.value} is not yet authorized",
        result.finalized_actions,
        result.action_states,
        result.open_action,
        result.terminal,
        result.tail_hash,
    )


def operational_blocked(message: str, state: MachineResult | None = None) -> MachineResult:
    """Represent an unavailable external capability separately from invalid state."""

    state = state or MachineResult(DecisionKind.VALID, "no state")
    return MachineResult(
        DecisionKind.OPERATIONAL_BLOCKED,
        message,
        state.finalized_actions,
        state.action_states,
        state.open_action,
        state.terminal,
        state.tail_hash,
    )
