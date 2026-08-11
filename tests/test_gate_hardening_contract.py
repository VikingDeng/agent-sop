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

    def test_installed_overlay_references_are_runtime_stable(self) -> None:
        expected = "~/.codex/runtime-current/skeletons/contestos-adaptive-overlay-v2.md"
        self.assertIn(expected, self.read("codex/AGENTS.global.md"))
        self.assertIn(expected, self.read("codex/AGENTS.workspace.md"))

    def test_router_source_and_strict_opt_in_are_structural(self) -> None:
        readme = self.read("codex/README.md")
        self.assertIn("--routing-profile strict", readme)
        self.assertIn("advisory", readme)
        hooks = json.loads(self.read("codex/hooks/hooks.json"))
        managed_commands = [
            hook["command"]
            for registrations in hooks["hooks"].values()
            for registration in registrations
            for hook in registration["hooks"]
            if hook.get("type") == "command"
        ]
        self.assertEqual(len(managed_commands), 5)
        self.assertTrue(all(command.startswith("/usr/bin/python3 ") for command in managed_commands))
        self.assertIn('"Stop"', self.read("codex/hooks/hooks.json"))

    def test_supervisor_document_has_a_formal_version_marker(self) -> None:
        supervisor = self.read("sop/tier0-core/autonomous-supervisor.md")
        self.assertRegex(supervisor, r"(?:^|\n)- \*\*版本\*\*:\s*v\d+", msg="missing formal version marker")

    def test_development_runtime_is_single_source_and_artifact_proportional(self) -> None:
        supervisor = self.read("sop/tier0-core/autonomous-supervisor.md")
        contract = self.read("sop/tier1-skeleton/write-contract.md")
        drift = self.read("sop/tier1-skeleton/drift-check.md")
        overlay = self.read("skeletons/contestos-adaptive-overlay-v2.md")
        methodology = self.read("sop/_METHODOLOGY.md")

        self.assertIn("唯一通用运行时决策源", supervisor)
        self.assertIn("跨 session 与交接连续性（条件触发）", supervisor)
        self.assertIn("物理存在本身都不是门禁", contract)
        self.assertNotIn("[AUTO] REQUIREMENTS + NON_GOALS", contract)
        self.assertNotIn("每次提交(product)", drift)
        self.assertIn("默认不新增映射表", drift)
        self.assertIn("开发 v1 的 canonical mapping", overlay)
        self.assertIn("不与 `tier0-core/autonomous-supervisor.md` 形成平行运行时", methodology)
        self.assertNotIn("步骤数 ≥6", methodology)

    def test_competition_runtime_covers_real_formats_without_fixed_ceremony(self) -> None:
        overlay = self.read("skeletons/contestos-adaptive-overlay-v2.md")
        competition = self.read("sop/tier1-skeleton/run-competition.md")
        package = self.read("sop/tier1-skeleton/package-submission.md")
        proxy = self.read("sop/tier1-skeleton/build-local-proxy.md")
        profile = self.read("sop/tier0-core/profile-code.md")
        patches = self.read("sop/tier1-skeleton/maintain-patch-series.md")

        self.assertIn("竞赛 v1 的 canonical mapping", overlay)
        self.assertIn("产品型黑客松是组合路径", overlay)
        self.assertIn("打包不等于外部提交", overlay)
        for axis in ("判定轴", "反馈轴", "工件轴", "环境轴", "事件轴", "外部动作包络"):
            self.assertIn(axis, competition)
        for family in ("算法、exact-output、interactive", "数据/榜单", "Kernel/系统优化", "agent/隐藏运行时评测", "产品型黑客松", "论文到 notebook"):
            self.assertIn(family, competition)
        self.assertIn("一次授权可以覆盖包络内的后续提交", competition)
        self.assertIn("只完成本地打包与核验，不执行", package)
        self.assertNotIn("git_dirty=false", package)
        self.assertIn("`local proxy first` 不是无条件门禁", proxy)
        self.assertIn("不是所有优化前都必须运行 heavyweight profiler", profile)
        self.assertIn("仅仅“基于 starter repo 开发”不自动触发", patches)

    def test_strict_router_profile_remains_available(self) -> None:
        self.assertEqual(POLICY.MAX_CONCURRENT_OPEN_THREADS, 2)
        self.assertEqual(POLICY.MAX_RISK_REVIEWERS_PER_SESSION, 1)
        self.assertEqual(
            POLICY.GLOBAL_LOOP_BUDGET,
            {"initial": 1, "review": 1, "correction": 1, "re_review": 1},
        )


if __name__ == "__main__":
    unittest.main()
