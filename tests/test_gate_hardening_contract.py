from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "codex/hooks/weighted_routing_policy.py"
SPEC = importlib.util.spec_from_file_location("weighted_routing_policy_contract", POLICY_PATH)
assert SPEC and SPEC.loader
POLICY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = POLICY
SPEC.loader.exec_module(POLICY)


class GateHardeningContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_global_loop_budget_is_frozen_in_policy_and_supervisor(self) -> None:
        self.assertEqual(
            POLICY.GLOBAL_LOOP_BUDGET,
            {
                "initial": 1,
                "review": 1,
                "correction": 1,
                "re_review": 1,
            },
        )
        supervisor = self.read("sop/tier0-core/autonomous-supervisor.md")
        self.assertIn("总计只允许一次 initial implementation、一次 consolidated correction batch 和一次 independent re-review", supervisor)
        self.assertIn("不得静默 fallback 或创建 vN+1", supervisor)
        for relative in (
            "sop/tier0-core/autonomous-supervisor.md",
            "codex/AGENTS.global.md",
            "codex/AGENTS.workspace.md",
            "codex/README.md",
            "codex/ROUTING_ACCEPTANCE.md",
        ):
            text = self.read(relative).lower()
            self.assertNotIn("per tier", text, relative)
            self.assertNotIn("same tier", text, relative)
            self.assertNotIn("luna -> terra -> sol", text, relative)

    def test_thread_lifecycle_and_limit_recovery_are_explicit(self) -> None:
        self.assertEqual(POLICY.MAX_CONCURRENT_OPEN_THREADS, 2)
        text = self.read("sop/tier0-core/autonomous-supervisor.md")
        for phrase in (
            "max_concurrent_threads_per_session",
            "completed threads should be closed",
            "agent-thread-limit",
            "retry the same eligible spawn at most once",
            "reuse an already-open eligible Luna/Terra thread",
            "never Luna model unavailability",
        ):
            self.assertIn(phrase, text)

    def test_package_identity_trust_boundary_and_recontract_schema_are_explicit(self) -> None:
        texts = (
            self.read("sop/tier0-core/autonomous-supervisor.md"),
            self.read("codex/AGENTS.global.md"),
            self.read("codex/AGENTS.workspace.md"),
            self.read("codex/README.md"),
            self.read("codex/ROUTING_ACCEPTANCE.md"),
        )
        for text in texts:
            lowered = text.lower()
            self.assertIn("supervisor", lowered)
            self.assertIn("not cryptographic", lowered)
            self.assertIn("guardrail", lowered)
            self.assertIn("paraphras", lowered)
            self.assertIn("relabel", lowered)
        supervisor = texts[0]
        for marker in (
            "RECONTRACT_OLD_PACKAGE_ID",
            "RECONTRACT_NEW_PACKAGE_ID",
            "RECONTRACT_OLD_CONTRACT_SHA256",
            "RECONTRACT_NEW_CONTRACT_SHA256",
            "RECONTRACT_REASON",
            "RECONTRACT_SCOPE_ACCEPTANCE_DELTA",
        ):
            self.assertIn(marker, supervisor)

    def test_sol_default_zero_and_ordinary_review_terra_are_frozen(self) -> None:
        self.assertEqual(POLICY.MAX_RISK_REVIEWERS_PER_SESSION, 1)
        self.assertEqual(POLICY.ROLE_MODEL_FAMILIES["reviewer"], "terra")
        self.assertEqual(POLICY.ROLE_MODEL_FAMILIES["risk_reviewer"], "sol")
        global_text = self.read("codex/AGENTS.global.md")
        self.assertIn("Child Sol budget defaults to zero", global_text)
        self.assertIn("Ordinary gate/validator review is Terra", global_text)

    def test_grill_bootstrap_and_experiment_gates_are_split(self) -> None:
        grill = self.read("sop/tier1-skeleton/research-execution-grill.md")
        skill = self.read("codex/skills/research-execution-grill/SKILL.md")
        for text in (grill, skill):
            self.assertIn("bootstrap/evidence_acquisition", text)
            self.assertIn("experiment_authorization", text)
            self.assertIn("dependency cycle", text)
            self.assertIn("authoritative", text)
            self.assertIn("append", text)
            self.assertNotIn("pilot artifact", text.lower())
            for phrase in (
                "MUST NOT",
                "subpilot",
                "scientific metrics",
                "inspect outcomes for adaptation",
                "scientific claims",
                "required artifact IDs",
                "provided artifact IDs",
                "disjointness",
            ):
                self.assertIn(phrase, text)

    def test_skill_workflow_numbering_is_monotonic(self) -> None:
        skill = self.read("codex/skills/research-execution-grill/SKILL.md")
        self.assertEqual(skill.count("\n8. Run:"), 1)
        self.assertEqual(skill.count("\n9. Continue"), 1)


if __name__ == "__main__":
    unittest.main()
