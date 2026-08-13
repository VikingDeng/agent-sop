from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "evaluations/open-quality-v1"


class OpenQualityContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_router_separates_fast_search_execute_verify_and_recontract(self) -> None:
        kernel = self.read("sop/tier0-core/autonomous-supervisor.md")
        option_search = self.read("sop/tier2-activity/option-search.md")
        self.assertIn("可逆小任务", kernel)
        self.assertIn("已批准 proposal", kernel)
        self.assertIn("未冻结 material fork", kernel)
        self.assertIn("re-contract/HUMAN", kernel)
        self.assertIn("以下情况**不触发**", option_search)
        self.assertIn("approved proposal", option_search)
        self.assertIn("主 Agent 可在原授权内选择", option_search)
        self.assertIn("同样合理且会改变对用户的结果语义", option_search)

    def test_option_search_has_decision_evidence_without_process_counts(self) -> None:
        option_search = self.read("sop/tier2-activity/option-search.md")
        for semantic in (
            "candidate packet",
            "核心操作",
            "影响上限",
            "collision / counterexample",
            "decisive probe",
            "falsifier / kill condition",
            "最近邻",
            "no viable option",
        ):
            self.assertIn(semantic, option_search)
        self.assertIn("没有固定候选数、Agent 数、轮次或并行方式", option_search)
        self.assertIn("不创建、修改或弱化 outcome contract", option_search)

    def test_development_candidate_requires_golden_slice_and_real_product_evidence(self) -> None:
        profile = self.read("sop/tier1-skeleton/run-development.md")
        for semantic in (
            "交付等级",
            "golden implementation",
            "hero/dashboard/card 模板",
            "真实 render/browser oracle",
            "console/request/runtime",
            "未主导该视觉实现的观察者",
            "Proof-of-Work",
            "能力已交付",
            "价值仍未建立",
        ):
            self.assertIn(semantic, profile)
        self.assertIn("非 UI 交付不触发 browser gate", profile)
        self.assertIn("小任务不创建独立报告", profile)

    def test_research_ideation_and_approved_execution_remain_separate(self) -> None:
        root_readme = self.read("README.md")
        research = self.read("sop/tier1-skeleton/research-execution-grill.md")
        option_search = self.read("sop/tier2-activity/option-search.md")
        self.assertIn("idea 尚未批准 → Option Search", root_readme)
        self.assertIn("proposal 已批准 → Research Execution", root_readme)
        self.assertIn("不替换已批准 idea", research)
        self.assertIn("已经选定的产品方向、冻结的架构或 approved proposal", option_search)

    def test_adapter_keeps_judgment_expensive_and_mechanical_work_bounded(self) -> None:
        adapter = self.read("codex/CODEX-ADAPTER.md")
        for semantic in (
            "根 Agent/Sol 保留问题定义",
            "Terra 适合并行做只读",
            "Luna 只在问题、输入、Oracle 和停止条件已经稳定",
            "并行用于增加独立证据",
            "选择与核心不变式裁决保持串行",
            "contract-ready",
            "oracle-ready",
            "state-ready",
            "decomposition-ready",
            "局部补丁只增加复杂度",
            "已作决定及其证据/理由",
            "当前最佳 artifact",
            "必须交给用户的授权分叉",
        ):
            self.assertIn(semantic, adapter)

    def test_routing_fixture_is_balanced_and_protects_simple_work(self) -> None:
        manifest = json.loads((EVAL_ROOT / "routing-cases.json").read_text(encoding="utf-8"))
        cases = manifest["cases"]
        self.assertEqual(len(cases), 24)
        self.assertEqual(len({case["id"] for case in cases}), 24)
        self.assertEqual(sum(case["pilot"] for case in cases), 12)
        for task_class in (
            "open_product",
            "research_ideation",
            "approved_research_execution",
            "simple_bounded_change",
        ):
            self.assertEqual(sum(case["task_class"] == task_class for case in cases), 6)
        simple = [case for case in cases if case["task_class"] == "simple_bounded_change"]
        self.assertTrue(simple)
        self.assertTrue(all(case["expected"]["primary_mode"] == "fast_path" for case in simple))
        self.assertTrue(all(case["expected"]["overlays"] == [] for case in simple))
        material_recontract = next(case for case in cases if case["id"] == "research_04")
        self.assertEqual(material_recontract["expected"]["primary_mode"], "re_contract")
        self.assertEqual(material_recontract["expected"]["user_decision"], "required_now")
        for case_id in ("idea_01", "idea_03", "research_04"):
            case = next(case for case in cases if case["id"] == case_id)
            self.assertNotIn("durable_goal", case["expected"]["overlays"])

    def test_eval_contract_is_frozen_and_machine_checked(self) -> None:
        readme = (EVAL_ROOT / "README.md").read_text(encoding="utf-8")
        schema = json.loads((EVAL_ROOT / "routing-output.schema.json").read_text(encoding="utf-8"))
        self.assertIn("497b5ba436a1a0392af01db3f2fecd3aa53e95e9", readme)
        for arm in ("A — raw", "B — main", "C — candidate"):
            self.assertIn(arm, readme)
        for isolation_rule in (
            "unique `HOME` and `CODEX_HOME`",
            "current\n`main` checkout",
            "parent/global `AGENTS.md`",
        ):
            self.assertIn(isolation_rule, readme)
        for metric in ("Blind quality", "WCU", "Rework", "Variance"):
            self.assertIn(metric, readme)
        self.assertIn("simple", readme)
        self.assertIn("unpromoted", readme)
        self.assertIn("Delete", readme)
        self.assertIn("outcome-fixtures.json", readme)
        self.assertIn("study-manifest", readme)
        self.assertIn("re_contract", schema["properties"]["primary_mode"]["enum"])
        static_result = subprocess.run(
            [sys.executable, str(EVAL_ROOT / "validate_and_score.py"), "--validate-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(static_result.returncode, 0, static_result.stderr)
        static_report = json.loads(static_result.stdout)
        self.assertEqual(static_report["decision"], "STATIC_CONTRACT_VALID")
        self.assertFalse(static_report["promotion_eligible"])
        self.assertFalse(static_report["all_outcome_inputs_materialized"])
        self.assertEqual(
            static_report["pilot_bundle_verification"],
            "RUN_FIXTURES_VERIFY_COMMAND",
        )
        self.assertEqual(static_report["pilot_routing_cases"], 12)
        self.assertEqual(static_report["pilot_outcome_fixture_contracts"], 4)
        result = subprocess.run(
            [sys.executable, str(EVAL_ROOT / "validate_and_score.py"), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self_test = json.loads(result.stdout)
        for check in (
            "complete_synthetic_is_unverified",
            "missing_slot_rejected",
            "manifest_mismatch_rejected",
            "duplicate_path_and_assignment_rejected",
            "changed_acceptance_rejected",
            "assignment_plan_mismatch_rejected",
            "fixture_network_ceiling_rejected",
            "symlink_path_rejected",
            "symlink_evidence_root_rejected",
            "symlink_evidence_root_ancestor_rejected",
            "manifest_and_results_paths_reserved",
            "identical_final_bytes_across_arms_valid",
        ):
            self.assertTrue(self_test[check], check)

    def test_outcome_contracts_are_balanced_hashed_and_not_claimed_as_runs(self) -> None:
        manifest = json.loads(
            (EVAL_ROOT / "outcome-fixtures.json").read_text(encoding="utf-8")
        )
        fixtures = manifest["fixtures"]
        self.assertEqual(len(fixtures), 12)
        self.assertEqual(len({fixture["id"] for fixture in fixtures}), 12)
        for task_class in (
            "open_product",
            "research_ideation",
            "approved_research_execution",
            "simple_bounded_change",
        ):
            self.assertEqual(
                sum(fixture["task_class"] == task_class for fixture in fixtures), 3
            )
            self.assertEqual(
                sum(
                    fixture["task_class"] == task_class and fixture["pilot"]
                    for fixture in fixtures
                ),
                1,
            )
        self.assertEqual(
            {fixture["id"] for fixture in fixtures if fixture["pilot"]},
            {"out_product_02", "out_idea_01", "out_research_02", "out_simple_02"},
        )
        for fixture in fixtures:
            for field in ("prompt", "input_artifact", "oracle_contract", "blind_rubric"):
                actual = hashlib.sha256(fixture[field].encode("utf-8")).hexdigest()
                self.assertEqual(fixture[f"{field}_sha256"], actual)
        evolution = self.read("EVOLUTION.md")
        self.assertIn("NOT_ESTABLISHED", evolution)
        self.assertIn("no outcome evidence yet", evolution)

    def test_study_manifest_is_closed_and_binds_materialized_inputs(self) -> None:
        schema = json.loads(
            (EVAL_ROOT / "study-manifest.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        binding = schema["$defs"]["outcomeBinding"]
        self.assertFalse(binding["additionalProperties"])
        self.assertNotIn("allOf", binding)
        for field in (
            "fixture_hash",
            "prompt_sha256",
            "oracle_contract_sha256",
            "blind_rubric_sha256",
            "materialized_input_ref",
            "materialized_input_sha256",
        ):
            self.assertIn(field, binding["required"])

    def test_package_validator_has_no_local_promotion_authority(self) -> None:
        protocol = self.read("evaluations/open-quality-v1/_study_protocol.py")
        cli = self.read("evaluations/open-quality-v1/validate_and_score.py")
        self.assertIn("PACKAGE_COMPLETE_UNVERIFIED", protocol)
        self.assertIn("INDEPENDENT_SIGNED_EVALUATOR_OR_HUMAN_REQUIRED", protocol)
        self.assertNotIn('"PASS_PROMOTION"', protocol)
        self.assertNotIn('"ADVANCE_TO_PROMOTION"', protocol)
        self.assertIn("promotion_eligible", cli)

    def test_old_self_reported_promotion_interface_is_rejected(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(EVAL_ROOT / "validate_and_score.py"),
                "--stage",
                "promotion",
                "--results",
                "synthetic-results.jsonl",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("PASS_PROMOTION", result.stdout)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_ci_runs_repository_contract(self) -> None:
        workflow = self.read(".github/workflows/validate.yml")
        self.assertIn("runs-on: ubuntu-24.04", workflow)
        self.assertIn(
            "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5",
            workflow,
        )
        self.assertIn(
            "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6",
            workflow,
        )
        self.assertIn('python-version: "3.12.11"', workflow)
        self.assertIn("requirements-ci.txt", workflow)
        requirements = self.read("evaluations/open-quality-v1/requirements-ci.txt")
        self.assertIn("jsonschema==4.25.1", requirements)
        self.assertIn("python3 scripts/validate_sop_repo.py", workflow)
        self.assertIn("validate_and_score.py --validate-only", workflow)
        self.assertIn("validate_and_score.py --self-test", workflow)
        self.assertIn("fixtures/verify_fixtures.py", workflow)
        self.assertIn("python3 -m unittest discover", workflow)
        self.assertIn("git diff --check", workflow)


if __name__ == "__main__":
    unittest.main()
