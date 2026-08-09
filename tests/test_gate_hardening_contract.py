from __future__ import annotations

import importlib.util
import json
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


class AdaptiveSopContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_global_contract_is_outcome_driven_and_process_soft(self) -> None:
        global_text = self.read("codex/AGENTS.global.md")
        supervisor = self.read("sop/tier0-core/autonomous-supervisor.md")
        combined = global_text + supervisor
        for phrase in (
            "The contract governs the result, not a prescribed path",
            "验收硬，过程软",
            "边界硬，策略软",
            "持续收敛而非固定轮次",
            "not brittle eligibility laws",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("Model unavailability permits a transparent lowest-cost fallback", self.read("codex/AGENTS.workspace.md"))
        self.assertIn("版本**: v6", supervisor)
        for phrase in (
            "执行模式诚实",
            "探索/调参集",
            "final holdout",
            "transductive adaptation",
            "fresh untouched",
            "显式更正",
            "20,000",
            "substantial behavior",
            "Git/外部交付状态",
        ):
            self.assertIn(phrase, supervisor)

    def test_default_policy_does_not_require_coordination_metadata(self) -> None:
        global_text = self.read("codex/AGENTS.global.md")
        supervisor = self.read("sop/tier0-core/autonomous-supervisor.md")
        self.assertIn("Use package IDs", global_text)
        self.assertIn("only when they materially improve coordination", global_text)
        self.assertIn("只在运行时协调确有帮助", supervisor)
        self.assertIn("CODEX_ROUTER_ENFORCEMENT=strict", self.read("codex/README.md"))
        self.assertIn("CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3", self.read("codex/hooks/hooks.json"))
        self.assertIn("not machine-verifiable", self.read("codex/README.md"))
        hooks = json.loads(self.read("codex/hooks/hooks.json"))
        managed_commands = [
            hook["command"]
            for registrations in hooks["hooks"].values()
            for registration in registrations
            for hook in registration["hooks"]
            if hook.get("type") == "command"
        ]
        self.assertEqual(len(managed_commands), 5)
        self.assertTrue(
            all(command.startswith("CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3 ") for command in managed_commands)
        )
        self.assertIn("--profile sol-supervisor", self.read("codex/README.md"))
        self.assertIn('"Stop"', self.read("codex/hooks/hooks.json"))

    def test_strict_router_profile_remains_available(self) -> None:
        self.assertEqual(POLICY.MAX_CONCURRENT_OPEN_THREADS, 2)
        self.assertEqual(POLICY.MAX_RISK_REVIEWERS_PER_SESSION, 1)
        self.assertEqual(
            POLICY.GLOBAL_LOOP_BUDGET,
            {"initial": 1, "review": 1, "correction": 1, "re_review": 1},
        )
        acceptance = self.read("codex/ROUTING_ACCEPTANCE.md")
        self.assertIn("Strict profile", acceptance)
        self.assertIn("historical invariants", acceptance)

    def test_grill_is_adaptive_by_default(self) -> None:
        grill = self.read("sop/tier1-skeleton/research-execution-grill.md")
        skill = self.read("codex/skills/research-execution-grill/SKILL.md")
        for text in (grill, skill):
            self.assertIn("adaptive", text.lower())
            self.assertIn("claim", text.lower())
            self.assertIn("oracle", text.lower())
            self.assertIn("scale", text.lower())
        self.assertIn("允许合并、跳过、重排或新增阶段", grill)
        self.assertIn("没有人工标签的研究不需要 `human_oracle`", grill)
        self.assertIn("Do not require human labels", skill)

    def test_signed_v3_is_explicitly_optional_but_still_fail_closed(self) -> None:
        reference = self.read("sop/tier1-skeleton/references/research-execution-grill-artifact.md")
        grill = self.read("sop/tier1-skeleton/research-execution-grill.md")
        validator = self.read("scripts/validate_research_execution_grill.py")
        state_machine = self.read("scripts/research_grill_state_machine.py")
        self.assertIn("optional high-assurance profile", reference)
        self.assertIn("可选 strict signed-v3 profile", grill)
        for phrase in (
            "--required-authorization",
            "--prepare-event",
            "PREPARED_NOT_AUTHORIZED",
            "architecture_reset_required",
            "research-execution-grill-v3",
        ):
            self.assertIn(phrase, reference + validator + state_machine)
        self.assertNotIn("subprocess", state_machine.split("class Action", 1)[1])
        self.assertNotIn("open(", state_machine)

    def test_failure_policy_allows_explicit_quality_preserving_fallback(self) -> None:
        principles = self.read("PRINCIPLES.md")
        fallback = self.read("sop/tier0-core/no-fallback-review.md")
        self.assertIn("允许重试、换工具、换模型", principles)
        self.assertIn("允许显式且质量等价的自适应路径", fallback)
        self.assertIn("禁止的是静默降级", principles)

    def test_run_experiment_uses_strict_v3_only_when_selected(self) -> None:
        run = self.read("sop/tier1-skeleton/run-experiment.md")
        self.assertIn("如果项目显式选择 signed v3 strict profile", run)
        self.assertIn("strict v3 仅在项目显式选择时", run)
        self.assertIn("普通低成本 dry run", run)


if __name__ == "__main__":
    unittest.main()
