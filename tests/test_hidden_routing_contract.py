from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "evaluations/open-quality-v1"
HIDDEN_PATH = EVAL_ROOT / "routing-hidden-cases.json"
VALIDATOR = EVAL_ROOT / "validate_and_score.py"


class HiddenRoutingContractTests(unittest.TestCase):
    def test_hidden_suite_is_small_balanced_and_not_installed(self) -> None:
        payload = json.loads(HIDDEN_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "open-quality-routing-hidden-cases-v1")
        self.assertEqual(len(payload["cases"]), 8)
        self.assertEqual(
            Counter(row["task_class"] for row in payload["cases"]),
            {
                "open_product": 2,
                "research_ideation": 2,
                "approved_research_execution": 2,
                "simple_bounded_change": 2,
            },
        )
        self.assertTrue(all(row["id"].startswith("hidden_") for row in payload["cases"]))

        installer_path = ROOT / "scripts/install_codex_runtime.py"
        spec = importlib.util.spec_from_file_location("hidden_suite_installer", installer_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        self.assertFalse(any("routing-hidden-cases.json" in item for item in installer.SNAPSHOT_FILES))

    def test_hidden_stage_reuses_closed_routing_output(self) -> None:
        cases = json.loads(HIDDEN_PATH.read_text(encoding="utf-8"))["cases"]
        rows = []
        for case in cases:
            for arm in ("A", "B", "C"):
                rows.append({
                    "case_id": case["id"],
                    "arm": arm,
                    "replicate": 1,
                    "routing": {
                        "schema_version": "open-quality-routing-v1",
                        "case_id": case["id"],
                        **case["expected"],
                        "decisive_facts": ["fresh evaluator-held case"],
                        "next_action": "Follow the bounded routing decision.",
                    },
                    "run_id": f"run-{case['id']}-{arm}",
                    "reported_wcu": 1,
                    "reported_wcu_complete": True,
                })
        with tempfile.TemporaryDirectory() as raw_tmp:
            result_path = Path(raw_tmp) / "hidden-routing-results.jsonl"
            result_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--stage",
                    "routing-hidden",
                    "--routing-results",
                    str(result_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["decision"], "ROUTING_DIAGNOSTIC_ONLY_UNVERIFIED")
        self.assertEqual(report["routing_suite"], "evaluator_hidden_noisy")
        self.assertFalse(report["promotion_eligible"])
        self.assertEqual(report["reported_exact_accuracy"], {"A": 1.0, "B": 1.0, "C": 1.0})

    def test_hidden_stage_rejects_malformed_output_without_traceback(self) -> None:
        malformed_base = {
            "case_id": "hidden_product_01",
            "arm": "A",
            "replicate": 1,
            "routing": {
                "schema_version": "open-quality-routing-v1",
                "case_id": "hidden_product_01",
                "primary_mode": "fast_path",
                "overlays": [],
                "user_decision": "not_needed",
                "decisive_facts": ["bounded"],
                "next_action": "Make the bounded edit.",
            },
            "run_id": "malformed-hidden-run",
            "reported_wcu": 1,
            "reported_wcu_complete": True,
        }
        malformed_rows = []
        for mutation in (
            {"routing": None},
            {"replicate": []},
            {"case_id": []},
            {"routing": {**malformed_base["routing"], "overlays": [{}]}},
        ):
            malformed_rows.append({**malformed_base, **mutation})
        for index, malformed in enumerate(malformed_rows):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as raw_tmp:
                result_path = Path(raw_tmp) / "malformed-hidden-routing.jsonl"
                result_path.write_text(json.dumps(malformed) + "\n", encoding="utf-8")
                completed = subprocess.run(
                    [
                        sys.executable, str(VALIDATOR), "--stage", "routing-hidden",
                        "--routing-results", str(result_path),
                    ],
                    cwd=ROOT, check=False, capture_output=True, text=True,
                )
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["decision"], "PACKAGE_INVALID")
            self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
