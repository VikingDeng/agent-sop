from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_research_execution_grill.py"
SPEC = importlib.util.spec_from_file_location("grill_validator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_payload() -> dict:
    return {
        "schema_version": 1,
        "proposal_id": "proposal-1",
        "proposal_source": "docs/proposal.md",
        "proposal_hash": "sha256:abc",
        "controller_context_id": "controller-1",
        "checkpoint": "pre_implementation",
        "status": "implementation_ready",
        "claims": [{"id": "C1", "text": "The method improves the primary metric."}],
        "non_goals": ["Do not redesign the approved proposal."],
        "ambiguities": [],
        "claim_experiment_matrix": [{
            "claim_id": "C1",
            "experiment_id": "E1",
            "metric": "primary metric",
            "oracle": "independent evaluator",
            "success_criterion": "lower bound exceeds zero",
            "kill_criterion": "correctness fails or lower bound does not exceed zero",
        }],
        "baseline_fairness": {"rows": [{
            "baseline": "strong baseline",
            "comparability": {
                "data": {"status": "matched", "evidence": "same frozen split manifest"},
                "model": {"status": "matched", "evidence": "same model hash"},
                "tuning_budget": {"status": "matched", "evidence": "same trial cap"},
                "inference_budget": {"status": "matched", "evidence": "same token cap"},
                "tools": {"status": "matched", "evidence": "same tool allowlist"},
                "stopping_rule": {"status": "matched", "evidence": "same stop rule"},
                "judge": {"status": "matched", "evidence": "same blind judge"},
            },
        }]},
        "design": {
            "experimental_unit": "task",
            "replication_unit": "seed",
            "assignment": "paired",
            "blocking_strategy": "block by task family",
            "nuisance_factors": ["task family"],
            "primary_estimand": "paired mean pass-rate difference",
            "target_effect_or_mde": "delta 0.03",
            "variance_basis": "frozen baseline pilot",
            "sample_size_or_seed_plan": "paired power plan with five seeds",
            "analysis_plan": "paired interval and preregistered robustness analysis",
            "multiplicity_policy": "one primary endpoint; Holm for secondary endpoints",
            "missing_data_policy": "failures count as failures; no silent exclusion",
            "holdout": {
                "access": "sealed",
                "tuning_access": False,
                "evidence": "split manifest hash and access log",
                "unsealing_authority": "named final-evaluation owner",
            },
            "sequential_analysis": {
                "optional_stopping_allowed": False,
                "registered_max_looks": 1,
                "evidence": "one frozen pilot look in the preregistration",
            },
        },
        "oracle_attack": {
            "independence": {
                "independent": True,
                "shared_implementation_path": False,
                "evidence": "separate reference evaluator and fixtures",
            },
            "rows": [{
                "risk": "shortcut",
                "detection": "negative control",
                "control_type": "negative_control",
            }],
        },
        "pilot_scale": {
            "pilot_pass_conditions": [
                {"id": "P1", "measure": "correctness", "operator": "==", "threshold": "pass"}
            ],
            "scale_conditions": [
                {"id": "S1", "measure": "effect_lower_bound", "operator": ">=", "threshold": 0.0}
            ],
            "kill_conditions": [
                {"id": "K1", "measure": "failure_rate", "operator": ">=", "threshold": 0.2}
            ],
            "scale_requires_all_conditions": True,
            "stop_on_any_kill": True,
            "max_interim_looks": 1,
            "interim_look_schedule": ["after frozen pilot completion"],
        },
        "reproducibility": {
            "env_lock": "lockfile",
            "code_ref_policy": "clean commit",
            "data_ref_policy": "versioned manifest",
            "manifest_path": "runs/manifest.json",
        },
        "budget": {"limits": {"gpu_hours": 1}, "stop_rule": "halt at limit"},
        "review_plan": [{
            "reviewer_type": "internal_blind_gpt",
            "reviewer_id": "review-1",
            "reviewer_context_id": "review-context-1",
            "reviewer_model": "gpt-5.6-sol",
        }],
        "reviews": [{
            "reviewer_type": "internal_blind_gpt",
            "reviewer_id": "review-1",
            "reviewer_context_id": "review-context-1",
            "reviewer_model": "gpt-5.6-sol",
            "input_hash": "sha256:packet",
            "artifact": "reviews/review-1.md",
            "artifact_hash": "sha256:review",
            "status": "pass",
        }],
        "unresolved_human_gates": [],
    }


class GrillValidatorTests(unittest.TestCase):
    def run_payload(self, payload: dict, required_checkpoint: str | None = None) -> int:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = root / "proposal.md"
            proposal.write_text("approved proposal", encoding="utf-8")
            payload["proposal_source"] = str(proposal)
            payload["proposal_hash"] = "sha256:" + hashlib.sha256(proposal.read_bytes()).hexdigest()
            pilot_observations = payload.pop("_test_pilot_observations", None)
            pilot_source_observations = payload.pop(
                "_test_pilot_source_observations",
                pilot_observations,
            )
            if pilot_observations is not None:
                evidence = root / "pilot-evidence.json"
                raw_results = root / "pilot-raw-results.json"
                raw_results.write_text(
                    json.dumps({"conditions": pilot_source_observations}),
                    encoding="utf-8",
                )
                raw_results_hash = "sha256:" + hashlib.sha256(raw_results.read_bytes()).hexdigest()
                payload["pilot_scale"]["pilot_evidence"] = str(evidence)
                evidence.write_text(json.dumps({
                    "schema_version": 1,
                    "proposal_id": payload["proposal_id"],
                    "proposal_hash": payload["proposal_hash"],
                    "checkpoint": "pre_scale",
                    "pilot_plan_hash": MODULE.pilot_plan_hash(payload["pilot_scale"]),
                    "condition_results": [
                        {
                            "condition_id": condition_id,
                            "observed": observed,
                            "source_artifact": str(raw_results),
                            "source_hash": raw_results_hash,
                            "source_json_pointer": f"/conditions/{condition_id}",
                        }
                        for condition_id, observed in pilot_observations.items()
                    ],
                }), encoding="utf-8")
                payload["pilot_scale"]["pilot_evidence_hash"] = (
                    "sha256:" + hashlib.sha256(evidence.read_bytes()).hexdigest()
                )
            core_hash = MODULE.grill_core_hash(payload)
            for index, row in enumerate(payload["reviews"]):
                packet = root / f"review-packet-{index}.json"
                packet.write_text(json.dumps({
                    "schema_version": 1,
                    "proposal_id": payload["proposal_id"],
                    "proposal_hash": payload["proposal_hash"],
                    "checkpoint": payload["checkpoint"],
                    "grill_core_hash": core_hash,
                }), encoding="utf-8")
                review = root / f"review-{index}.json"
                row["input_artifact"] = str(packet)
                row["input_hash"] = "sha256:" + hashlib.sha256(packet.read_bytes()).hexdigest()
                row["artifact"] = str(review)
                findings = row.pop("_test_findings", [])
                review.write_text(json.dumps({
                    "schema_version": 1,
                    "reviewer_type": row["reviewer_type"],
                    "reviewer_id": row["reviewer_id"],
                    "reviewer_context_id": row.get("reviewer_context_id"),
                    "reviewer_model": row.get("reviewer_model"),
                    "input_hash": row["input_hash"],
                    "proposal_hash": payload["proposal_hash"],
                    "grill_core_hash": core_hash,
                    "verdict": row["status"],
                    "findings": findings,
                }), encoding="utf-8")
                row["artifact_hash"] = "sha256:" + hashlib.sha256(review.read_bytes()).hexdigest()
            path = root / "artifact.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            args = [str(path)]
            if required_checkpoint is not None:
                args.extend(["--required-checkpoint", required_checkpoint])
            return MODULE.main(args)

    def test_ready_artifact_passes(self) -> None:
        self.assertEqual(self.run_payload(valid_payload()), 0)

    def test_structurally_valid_blocked_artifact_is_not_a_pass(self) -> None:
        payload = valid_payload()
        payload["status"] = "blocked"
        self.assertEqual(self.run_payload(payload), 3)

    def test_unresolved_p0_cannot_claim_ready(self) -> None:
        payload = valid_payload()
        payload["ambiguities"] = [{
            "id": "A1",
            "severity": "p0",
            "question": "Which update order is authoritative?",
            "status": "unresolved",
        }]
        self.assertEqual(self.run_payload(payload), 1)

    def test_self_asserted_external_review_type_is_rejected(self) -> None:
        payload = copy.deepcopy(valid_payload())
        payload["reviews"][0]["reviewer_type"] = "external_review"
        self.assertEqual(self.run_payload(payload), 1)

    def test_reviewer_must_use_an_independent_context(self) -> None:
        payload = valid_payload()
        payload["reviews"][0]["reviewer_context_id"] = payload["controller_context_id"]
        self.assertEqual(self.run_payload(payload), 1)

    def test_every_claim_requires_an_experiment_mapping(self) -> None:
        payload = valid_payload()
        payload["claims"].append({"id": "C2", "text": "A second claim."})
        self.assertEqual(self.run_payload(payload), 1)

    def test_pre_scale_requires_pilot_evidence(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "scale_ready"
        self.assertEqual(self.run_payload(payload), 1)

    def test_pre_scale_structured_results_unlock_scale(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "scale_ready"
        payload["_test_pilot_observations"] = {"P1": "pass", "S1": 0.01, "K1": 0.1}
        self.assertEqual(self.run_payload(payload), 0)

    def test_pre_scale_rejects_unstructured_pilot_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "pilot.txt"
            evidence.write_text("pilot looked good", encoding="utf-8")
            payload = valid_payload()
            payload["checkpoint"] = "pre_scale"
            payload["status"] = "scale_ready"
            payload["pilot_scale"]["pilot_evidence"] = str(evidence)
            payload["pilot_scale"]["pilot_evidence_hash"] = (
                "sha256:" + hashlib.sha256(evidence.read_bytes()).hexdigest()
            )
            self.assertEqual(self.run_payload(payload), 1)

    def test_failed_scale_condition_cannot_unlock_scale(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "scale_ready"
        payload["_test_pilot_observations"] = {"P1": "pass", "S1": -0.01, "K1": 0.1}
        self.assertEqual(self.run_payload(payload), 1)

    def test_triggered_kill_condition_cannot_unlock_scale(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "scale_ready"
        payload["_test_pilot_observations"] = {"P1": "pass", "S1": 0.01, "K1": 0.2}
        self.assertEqual(self.run_payload(payload), 1)

    def test_failed_pilot_can_be_recorded_as_structurally_valid_blocked(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "blocked"
        payload["_test_pilot_observations"] = {"P1": "fail", "S1": -0.01, "K1": 0.2}
        self.assertEqual(self.run_payload(payload), 3)

    def test_pilot_observation_must_match_bound_raw_result(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "scale_ready"
        payload["_test_pilot_observations"] = {"P1": "pass", "S1": 0.01, "K1": 0.1}
        payload["_test_pilot_source_observations"] = {"P1": "pass", "S1": -0.01, "K1": 0.1}
        self.assertEqual(self.run_payload(payload), 1)

    def test_human_review_cannot_substitute_for_internal_blind_review(self) -> None:
        payload = valid_payload()
        payload["reviews"][0]["reviewer_type"] = "human_domain_reviewer"
        payload["reviews"][0]["evidence_source"] = "signed project record"
        self.assertEqual(self.run_payload(payload), 1)

    def test_review_artifact_verdict_must_match_row(self) -> None:
        payload = valid_payload()
        original_load = MODULE.load_json_object

        def contradictory(path: Path, label: str, errors: list[str]):
            result = original_load(path, label, errors)
            if result is not None and label.endswith(".artifact"):
                result["verdict"] = "blocked"
            return result

        MODULE.load_json_object = contradictory
        try:
            self.assertEqual(self.run_payload(payload), 1)
        finally:
            MODULE.load_json_object = original_load

    def test_resolved_blocking_ambiguity_requires_authoritative_evidence(self) -> None:
        payload = valid_payload()
        payload["ambiguities"] = [{
            "id": "A1",
            "severity": "p0",
            "question": "Which method semantics are authoritative?",
            "source": "controller convention",
            "status": "resolved",
            "resolution": "use the conventional default",
            "resolution_authority": "controller",
        }]
        self.assertEqual(self.run_payload(payload), 1)

    def test_unsafe_structured_scientific_gates_are_rejected(self) -> None:
        payload = valid_payload()
        payload["baseline_fairness"]["rows"][0]["data"] = "unmatched"
        payload["design"]["holdout_policy"] = "used for tuning"
        payload["oracle_attack"]["shared_path_analysis"] = "paths are shared"
        payload["pilot_scale"]["scale_gate"] = "always scale"
        payload["pilot_scale"]["stop_rule"] = "never stop"
        self.assertEqual(self.run_payload(payload), 1)

    def test_passing_review_cannot_hide_open_blocking_finding(self) -> None:
        payload = valid_payload()
        original_load = MODULE.load_json_object

        def open_critical(path: Path, label: str, errors: list[str]):
            result = original_load(path, label, errors)
            if result is not None and label.endswith(".artifact"):
                result["findings"] = [{
                    "id": "F1",
                    "severity": "critical",
                    "status": "open",
                    "summary": "oracle is not independent",
                }]
            return result

        MODULE.load_json_object = open_critical
        try:
            self.assertEqual(self.run_payload(payload), 1)
        finally:
            MODULE.load_json_object = original_load

    def test_one_pass_cannot_override_another_blocked_current_review(self) -> None:
        payload = valid_payload()
        payload["review_plan"].append({
            "reviewer_type": "internal_blind_gpt",
            "reviewer_id": "review-2",
            "reviewer_context_id": "review-context-2",
            "reviewer_model": "gpt-5.6-sol",
        })
        payload["reviews"].append({
            "reviewer_type": "internal_blind_gpt",
            "reviewer_id": "review-2",
            "reviewer_context_id": "review-context-2",
            "reviewer_model": "gpt-5.6-sol",
            "input_hash": "sha256:packet-2",
            "artifact": "reviews/review-2.json",
            "artifact_hash": "sha256:review-2",
            "status": "blocked",
            "_test_findings": [{
                "id": "F2",
                "severity": "high",
                "status": "open",
                "summary": "scale evidence is incomplete",
            }],
        })
        self.assertEqual(self.run_payload(payload), 1)

    def test_internal_review_model_must_be_gpt(self) -> None:
        payload = valid_payload()
        payload["reviews"][0]["reviewer_model"] = "claude-opus"
        self.assertEqual(self.run_payload(payload), 1)

    def test_gpt_prefixed_fake_model_is_rejected(self) -> None:
        payload = valid_payload()
        payload["review_plan"][0]["reviewer_model"] = "gpt-claude-opus"
        payload["reviews"][0]["reviewer_model"] = "gpt-claude-opus"
        self.assertEqual(self.run_payload(payload), 1)

    def test_deleting_a_preregistered_blocked_review_is_rejected(self) -> None:
        payload = valid_payload()
        payload["review_plan"].append({
            "reviewer_type": "internal_blind_gpt",
            "reviewer_id": "review-2",
            "reviewer_context_id": "review-context-2",
            "reviewer_model": "gpt-5.6-sol",
        })
        self.assertEqual(self.run_payload(payload), 1)

    def test_prefixed_placeholder_is_rejected(self) -> None:
        payload = valid_payload()
        payload["claims"][0]["text"] = "TODO: choose metric after pilot"
        self.assertEqual(self.run_payload(payload), 1)

    def test_embedded_and_literal_placeholders_are_rejected(self) -> None:
        for text in ("metric TBD after pilot", "PLACEHOLDER"):
            with self.subTest(text=text):
                payload = valid_payload()
                payload["claims"][0]["text"] = text
                self.assertEqual(self.run_payload(payload), 1)

    def test_boolean_observation_cannot_equal_numeric_threshold(self) -> None:
        payload = valid_payload()
        payload["checkpoint"] = "pre_scale"
        payload["status"] = "scale_ready"
        for key in ("pilot_pass_conditions", "scale_conditions", "kill_conditions"):
            payload["pilot_scale"][key][0]["operator"] = "=="
            payload["pilot_scale"][key][0]["threshold"] = 1
        payload["_test_pilot_observations"] = {"P1": True, "S1": True, "K1": False}
        self.assertEqual(self.run_payload(payload), 1)

    def test_single_character_proposal_locator_is_valid(self) -> None:
        payload = valid_payload()
        payload["ambiguities"] = [{
            "id": "A1",
            "severity": "p0",
            "question": "Which semantics?",
            "source": "proposal:1",
            "status": "resolved",
            "resolution": "use the exact semantics at locator 1",
            "resolution_authority": "proposal_source",
        }]
        self.assertEqual(self.run_payload(payload), 0)

    def test_unknown_ambiguity_severity_and_empty_locator_are_rejected(self) -> None:
        payload = valid_payload()
        payload["ambiguities"] = [{
            "id": "A1",
            "severity": "blocker",
            "question": "Which semantics?",
            "source": "proposal:",
            "status": "resolved",
            "resolution": "use one variant",
            "resolution_authority": "proposal_source",
        }]
        self.assertEqual(self.run_payload(payload), 1)

    def test_blocking_proposal_resolution_requires_nonempty_locator(self) -> None:
        payload = valid_payload()
        payload["ambiguities"] = [{
            "id": "A1",
            "severity": "p0",
            "question": "Which semantics?",
            "source": "proposal:",
            "status": "resolved",
            "resolution": "use one variant",
            "resolution_authority": "proposal_source",
        }]
        self.assertEqual(self.run_payload(payload), 1)

    def test_human_decision_must_be_structured_and_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            decision = Path(directory) / "decision.txt"
            decision.write_text("trust me", encoding="utf-8")
            payload = valid_payload()
            payload["ambiguities"] = [{
                "id": "A1",
                "severity": "p0",
                "question": "Which semantics?",
                "source": "human decision required",
                "status": "resolved",
                "resolution": "use one variant",
                "resolution_authority": "human_decision",
                "decision_artifact": str(decision),
                "decision_artifact_hash": "sha256:" + hashlib.sha256(decision.read_bytes()).hexdigest(),
            }]
            self.assertEqual(self.run_payload(payload), 1)

    def test_non_finite_budget_is_rejected(self) -> None:
        payload = valid_payload()
        payload["budget"]["limits"]["gpu_hours"] = float("inf")
        self.assertNotEqual(self.run_payload(payload), 0)

    def test_required_checkpoint_blocks_wrong_action_gate(self) -> None:
        self.assertEqual(self.run_payload(valid_payload(), "pre_scale"), 1)


if __name__ == "__main__":
    unittest.main()
