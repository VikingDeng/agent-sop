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

    def test_runtime_bootstrap_loads_current_layers_not_legacy_skeletons(self) -> None:
        global_agents = self.read("codex/AGENTS.global.md")
        for expected in (
            "runtime-current/sop/tier0-core/autonomous-supervisor.md",
            "runtime-current/codex/CODEX-ADAPTER.md",
            "runtime-current/sop/tier1-skeleton/run-development.md",
            "runtime-current/sop/tier1-skeleton/research-execution-grill.md",
            "runtime-current/sop/tier1-skeleton/run-competition.md",
        ):
            self.assertIn(expected, global_agents)
        self.assertNotIn("runtime-current/skeletons/contestos-adaptive-overlay-v2.md", global_agents)
        self.assertIn("legacy inputs used only when a project explicitly selects one", global_agents)

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
        self.assertTrue(all(command.startswith("python3 ") for command in managed_commands))
        self.assertIn('"SessionStart"', self.read("codex/hooks/hooks.json"))

    def test_kernel_is_versioned_and_platform_independent(self) -> None:
        kernel = self.read("sop/tier0-core/autonomous-supervisor.md")
        adapter = self.read("codex/CODEX-ADAPTER.md")
        self.assertRegex(kernel, r"(?:^|\n)- \*\*版本\*\*:\s*v\d+")
        for state in ("RESOLVE", "CONTRACT", "EXECUTE", "VERIFY", "DELIVER"):
            self.assertIn(state, kernel)
        for platform_term in ("WCU =", "Luna 优先", "Terra 承担", "Sol 承担", "PACKAGE_ID"):
            self.assertNotIn(platform_term, kernel)
        for adapter_term in ("WCU =", "Luna", "Terra", "Sol", "SessionStart", "sub-agent"):
            self.assertIn(adapter_term, adapter)
        self.assertIn("平台遥测可以辅助审计", kernel)
        self.assertIn("缺失本身不能", kernel)

    def test_development_profile_is_claim_driven_not_a_product_checklist(self) -> None:
        profile = self.read("sop/tier1-skeleton/run-development.md")
        self.assertIn("最小 domain model", profile)
        self.assertIn("critical journeys", profile)
        self.assertIn("单个 ranking/recommendation 不能冒充 comparison", profile)
        self.assertIn("真实 render oracle", profile)
        self.assertIn("partial/ENV-BLOCKED", profile)
        self.assertIn("不机械要求 CRUD", profile)
        self.assertIn("固定技术栈", profile)
        self.assertIn("speculative runtime fallback", profile)
        self.assertIn("调用方可观察行为", profile)
        self.assertIn("默认值、显式 opt-in、错误/清理与资源状态保持", profile)
        self.assertIn("方向直接进入实现，不追加 discovery 仪式", profile)
        self.assertIn("不因缺少价值证据而重新搜索或 pivot", profile)
        self.assertIn("不能自行改题", profile)
        self.assertIn("真实价值信号", profile)
        self.assertIn("不因已有代码而扩展功能", profile)
        self.assertIn("能力已交付", profile)
        self.assertIn("价值仍未建立", profile)
        for hardcoded in ("filter/sort/pagination", "desktop 与 mobile", "create/read/update"):
            self.assertNotIn(hardcoded, profile)

    def test_direction_search_is_bounded_and_does_not_reopen_frozen_work(self) -> None:
        kernel = self.read("sop/tier0-core/autonomous-supervisor.md")
        bootstrap = self.read("codex/AGENTS.global.md")
        self.assertIn("方向是否已经冻结", kernel)
        self.assertIn("已批准 proposal", kernel)
        self.assertIn("而不是自动搜索替代方向", kernel)
        self.assertIn("最能改变排序的 probe", kernel)
        self.assertIn("不以先写出的实现或已投入成本代替选择依据", kernel)
        self.assertIn("Do not reopen a direction already selected", bootstrap)
        self.assertIn("otherwise proceed directly", bootstrap)

    def test_long_running_scheduler_is_conditional_and_cannot_own_verdict(self) -> None:
        adapter = self.read("codex/CODEX-ADAPTER.md")
        self.assertIn("contract-ready + oracle-ready", adapter)
        self.assertIn("用户明确要求长程/持续推进", adapter)
        self.assertIn("不要求固定文件名", adapter)
        self.assertIn("`replayable`、`resume_only` 还是 `externally_effectful`", adapter)
        self.assertIn("不能选择产品/研究方向", adapter)
        self.assertIn("`timeout` 是 `INCOMPLETE/UNKNOWN`", adapter)
        self.assertIn("fresh agent + compact continuity record", adapter)
        self.assertNotIn("必须创建 continuity", adapter)

    def test_public_api_contract_oracle_challenges_semantics_without_universal_matrix(self) -> None:
        oracle = self.read("sop/tier0-core/build-oracle.md")
        self.assertIn("public API/兼容 contract", oracle)
        self.assertIn("默认行为与显式 opt-in", oracle)
        self.assertIn("资源状态保持", oracle)
        self.assertIn("没有这种歧义或失败路径时不制造行为矩阵", oracle)

    def test_research_profile_preserves_method_and_uses_ai_statistics(self) -> None:
        grill = self.read("sop/tier1-skeleton/research-execution-grill.md")
        experiment = self.read("sop/tier1-skeleton/run-experiment.md")
        statistics = self.read("sop/tier1-skeleton/statistics-oracle.md")
        self.assertIn("method-fidelity mapping", grill)
        self.assertIn("baseline parity", grill)
        self.assertIn("negative control/ablation", grill)
        self.assertIn("speculative catch-and-continue", experiment)
        self.assertIn("replication unit", statistics)
        self.assertIn("paired/nested/crossed", statistics)
        self.assertIn("CI overlap", statistics)
        self.assertIn("不能强制每项结果", statistics)
        self.assertIn("paper_eligible=false", grill)

    def test_environment_and_reproduction_evidence_are_claim_proportional(self) -> None:
        lock_env = self.read("sop/tier0-core/lock-env.md")
        reproduce = self.read("sop/tier0-core/reproduce-result.md")
        experiment = self.read("sop/tier1-skeleton/run-experiment.md")
        presentation = self.read(
            "sop/tier1-skeleton/references/research-evidence-presentation.md"
        )

        self.assertIn("**版本**: v2", lock_env)
        self.assertIn("二者不是默认产物", lock_env)
        self.assertIn("claim 明确要求可重建", lock_env)
        self.assertNotIn("发布、confirmatory evidence、跨机器复现", lock_env)
        self.assertIn("`git_dirty=false` 不是环境正确性的替代证据", lock_env)
        self.assertIn("**版本**: v2", reproduce)
        self.assertIn("不是每个 diagnostic", reproduce)
        self.assertIn("不规定通用 `{N_SEEDS}`", reproduce)
        self.assertIn("dirty tree 本身不是失败", reproduce)
        self.assertIn("`REPLAYED`", reproduce)
        self.assertIn("只有达到预声明 independence level", reproduce)
        self.assertIn("execution-relevant untracked", reproduce)
        self.assertIn("content-tree hash", reproduce)
        self.assertIn("不是每个实验的默认前置门禁", experiment)
        self.assertIn("普通 `git diff` 单独不够", experiment)
        self.assertIn("不可恢复/含糊的代码/环境身份", presentation)
        self.assertIn("outcome-relevant environment identity", presentation)

        methodology = self.read("sop/_METHODOLOGY.md")
        paper_playbook = self.read(
            "sop/tier2-activity/references/paper-module-playbook.md"
        )
        self.assertIn("**版本**: v6", methodology)
        self.assertIn("保存本次 resolved identity", methodology)
        self.assertNotIn("Checkpoint 分三型", methodology)
        self.assertIn("不是 checkpoint 状态机", methodology)
        self.assertIn("不机械补齐清单", paper_playbook)

        for legacy_gate in (
            "要求 git 干净",
            "复现跑在干净环境、`git_dirty=false`",
            "多次(≥`{N_SEEDS}`)",
        ):
            self.assertNotIn(legacy_gate, reproduce)

    def test_competition_profile_covers_full_projects_and_deadline_reserve(self) -> None:
        competition = self.read("sop/tier1-skeleton/run-competition.md")
        package = self.read("sop/tier1-skeleton/package-submission.md")
        for axis in ("判定轴", "反馈轴", "工件轴", "环境轴", "事件轴", "外部动作包络"):
            self.assertIn(axis, competition)
        for family in ("算法、exact-output、interactive", "数据/榜单", "Kernel/系统优化", "agent/隐藏运行时评测", "产品型黑客松", "论文到 notebook"):
            self.assertIn(family, competition)
        self.assertIn("time reserve", competition)
        self.assertIn("last-known-good", competition)
        self.assertIn("随机 tournament", competition)
        self.assertIn("一次授权可以覆盖包络内的后续提交", competition)
        self.assertIn("只完成本地打包与核验，不执行", package)
        self.assertNotIn("根 Agent 或 Luna", competition)

    def test_skill_registry_is_not_a_second_router(self) -> None:
        adapters = self.read("SKILL-ADAPTERS.md")
        registry = json.loads(self.read("skill-registry.yaml"))
        self.assertIn("Strong no-Skill baseline", adapters)
        self.assertIn("Minimal reminder", adapters)
        self.assertIn("Full Skill", adapters)
        self.assertIn("禁止运行时调用 `find-skills`", adapters)
        self.assertFalse(any(entry["lifecycle"]["promoted"] for entry in registry["entries"]))
        self.assertTrue(all("model_route" not in entry for entry in registry["entries"]))

    def test_strict_router_profile_remains_available(self) -> None:
        self.assertEqual(POLICY.MAX_CONCURRENT_OPEN_THREADS, 2)
        self.assertEqual(POLICY.MAX_RISK_REVIEWERS_PER_SESSION, 1)
        self.assertEqual(
            POLICY.GLOBAL_LOOP_BUDGET,
            {"initial": 1, "review": 1, "correction": 1, "re_review": 1},
        )


if __name__ == "__main__":
    unittest.main()
