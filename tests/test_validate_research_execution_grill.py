from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_research_execution_grill.py"
SPEC = importlib.util.spec_from_file_location("grill_validator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def legacy_payload(root: Path) -> dict:
    proposal = root / "legacy-proposal.md"; proposal.write_text("approved proposal", encoding="utf-8")
    payload = {
        "schema_version": 1, "proposal_id": "legacy", "proposal_source": str(proposal),
        "proposal_hash": file_hash(proposal), "controller_context_id": "controller",
        "checkpoint": "pre_implementation", "status": "implementation_ready",
        "claims": [{"id": "C1", "text": "Claim"}], "non_goals": ["No redesign"], "ambiguities": [],
        "claim_experiment_matrix": [{"claim_id": "C1", "experiment_id": "E1", "metric": "metric", "oracle": "oracle", "success_criterion": "pass", "kill_criterion": "fail"}],
        "baseline_fairness": {"rows": [{"baseline": "base", "comparability": {field: {"status": "matched", "evidence": "evidence"} for field in MODULE.BASELINE_DIMENSIONS}}]},
        "design": {
            "experimental_unit": "task", "replication_unit": "seed", "assignment": "paired", "blocking_strategy": "family",
            "nuisance_factors": ["family"], "primary_estimand": "difference", "target_effect_or_mde": "0.1", "variance_basis": "pilot",
            "sample_size_or_seed_plan": "five", "analysis_plan": "paired", "multiplicity_policy": "one", "missing_data_policy": "fail",
            "holdout": {"access": "sealed", "tuning_access": False, "evidence": "manifest", "unsealing_authority": "owner"},
            "sequential_analysis": {"optional_stopping_allowed": False, "registered_max_looks": 1, "evidence": "plan"},
        },
        "oracle_attack": {"independence": {"independent": True, "shared_implementation_path": False, "evidence": "separate"}, "rows": [{"risk": "shortcut", "detection": "control", "control_type": "negative_control"}]},
        "pilot_scale": {
            "pilot_pass_conditions": [{"id": "P1", "measure": "correct", "operator": "==", "threshold": "pass"}],
            "scale_conditions": [{"id": "S1", "measure": "effect", "operator": ">=", "threshold": 0.0}],
            "kill_conditions": [{"id": "K1", "measure": "failure", "operator": ">=", "threshold": 0.2}],
            "scale_requires_all_conditions": True, "stop_on_any_kill": True, "max_interim_looks": 1, "interim_look_schedule": ["pilot"],
        },
        "reproducibility": {"env_lock": "lock", "code_ref_policy": "clean", "data_ref_policy": "manifest", "manifest_path": "manifest"},
        "budget": {"limits": {"gpu_hours": 1}, "stop_rule": "halt"},
        "review_plan": [{"reviewer_type": "internal_blind_gpt", "reviewer_id": "r1", "reviewer_context_id": "review", "reviewer_model": "gpt-5.6-terra"}],
        "reviews": [{"reviewer_type": "internal_blind_gpt", "reviewer_id": "r1", "reviewer_context_id": "review", "reviewer_model": "gpt-5.6-terra", "status": "pass"}],
        "unresolved_human_gates": [],
    }
    core = MODULE.grill_core_hash(payload)
    packet = root / "legacy-packet.json"; packet.write_bytes(MODULE.canonical_json({"schema_version": 1, "proposal_id": "legacy", "proposal_hash": payload["proposal_hash"], "checkpoint": "pre_implementation", "grill_core_hash": core}))
    review = root / "legacy-review.json"
    payload["reviews"][0].update({"input_artifact": str(packet), "input_hash": file_hash(packet), "artifact": str(review)})
    review.write_bytes(MODULE.canonical_json({"schema_version": 1, "reviewer_type": "internal_blind_gpt", "reviewer_id": "r1", "reviewer_context_id": "review", "reviewer_model": "gpt-5.6-terra", "input_hash": file_hash(packet), "proposal_hash": payload["proposal_hash"], "grill_core_hash": core, "verdict": "pass", "findings": []}))
    payload["reviews"][0]["artifact_hash"] = file_hash(review)
    return payload


class SignedFixture:
    def __init__(self, root: Path, keys: dict[str, Path], policy: Path, action: str, reviewers: int = 1, correction: bool = False, blocked_reviewer: int | None = None, proposal_path: Path | None = None) -> None:
        self.root = root
        self.keys = keys
        self.policy = policy
        self.action = action
        self.reviewers = reviewers
        self.correction = correction
        self.blocked_reviewer = blocked_reviewer
        self.proposal_path = proposal_path
        self.counter = 0
        self.artifact_path = root / "execution-grill.json"
        self.payload = self._build()
        self._write_artifact()

    def _name(self, prefix: str) -> Path:
        self.counter += 1
        return self.root / f"{self.counter:03d}-{prefix}.json"

    def sign_json(self, value: dict, identity: str, prefix: str, namespace: str | None = None) -> tuple[Path, Path]:
        path = self._name(prefix)
        path.write_bytes(MODULE.canonical_json(value))
        subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-q", "-f", str(self.keys[identity]), "-n", namespace or MODULE.V2_ATTESTATION_NAMESPACE, str(path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return path, Path(str(path) + ".sig")

    def _base(self) -> dict:
        proposal = self.proposal_path or self.root / "proposal.md"
        if not proposal.exists():
            proposal.write_text("approved proposal", encoding="utf-8")
        plan = [
            {
                "reviewer_id": f"reviewer-{index + 1}",
                "signer_identity": f"reviewer-{index + 1}",
                "reviewer_type": "internal_blind_gpt",
                "reviewer_context_id": f"review-context-{index + 1}",
                "reviewer_model": "gpt-5.6-terra",
            }
            for index in range(self.reviewers)
        ]
        return {
            "schema_version": 3,
            "protocol_version": MODULE.PROTOCOL_VERSION,
            "proposal_id": "proposal-v2",
            "proposal_source": str(proposal),
            "proposal_hash": file_hash(proposal),
            "controller_context_id": "controller-context",
            "checkpoint_id": "checkpoint-v3",
            "lineage_id": "lineage-v2",
            "checkpoint_generation": 1,
            "status": "blocked",
            "authorization": "none",
            "claims": [{"id": "C1", "text": "The method improves the primary metric."}],
            "non_goals": ["Do not redesign the approved proposal."],
            "ambiguities": [],
            "claim_experiment_matrix": [{
                "claim_id": "C1", "experiment_id": "E1", "metric": "primary_metric",
                "oracle": "independent evaluator", "success_criterion": "lower bound exceeds zero",
                "kill_criterion": "correctness fails",
            }],
            "baseline_fairness": {"rows": [{
                "baseline": "strong baseline",
                "comparability": {
                    field: {"status": "matched", "evidence": "frozen evidence"}
                    for field in MODULE.BASELINE_DIMENSIONS
                },
            }]},
            "design": {
                "experimental_unit": "task", "replication_unit": "seed", "assignment": "paired",
                "blocking_strategy": "task family", "nuisance_factors": ["family"],
                "primary_estimand": "paired difference", "target_effect_or_mde": "0.03",
                "variance_basis": "frozen pilot", "sample_size_or_seed_plan": "five seeds",
                "analysis_plan": "paired interval", "multiplicity_policy": "one primary",
                "missing_data_policy": "failures count as failures",
                "holdout": {"access": "sealed", "tuning_access": False, "evidence": "manifest", "unsealing_authority": "owner"},
                "sequential_analysis": {"optional_stopping_allowed": False, "registered_max_looks": 1, "evidence": "plan"},
            },
            "oracle_attack": {
                "independence": {"independent": True, "shared_implementation_path": False, "evidence": "separate path"},
                "rows": [{"risk": "shortcut", "detection": "negative control", "control_type": "negative_control"}],
            },
            "reproducibility": {"env_lock": "lock", "code_ref_policy": "immutable commit", "data_ref_policy": "manifest", "manifest_path": "manifest.json"},
            "stage_dependencies": copy.deepcopy(MODULE.V2_STAGE_DEPENDENCIES),
            "action_contracts": {action: {"required_passed_stages": prefix} for action, prefix in MODULE.V2_ACTION_PREFIX.items()},
            "artifacts": [],
            "review_plan": plan,
            "review_plan_hash": MODULE.canonical_sha256(plan),
            "review_history": [],
            "current_review_ids": [],
            "unresolved_human_gates": [],
            "budget": {"phase0_limits": {"gpu_hours": 2}, "scale_limits": {"gpu_hours": 10}, "stop_rule": "halt at bound"},
        }

    def _artifact(self, payload: dict, artifact_id: str, kind: str, consumer: str, source: dict, consumes: list[str], signer: str | None, attested_action: str | None) -> dict:
        source_path = self._name(f"source-{artifact_id}")
        source_path.write_bytes(MODULE.canonical_json(source))
        artifact = {
            "id": artifact_id,
            "kind": kind,
            "evidence_class": MODULE.V2_STAGE_EVIDENCE[MODULE.V2_KIND_STAGE[kind]],
            "producer_stage": MODULE.V2_KIND_STAGE[kind],
            "consumer_stage": consumer,
            "source_path": str(source_path),
            "source_sha256": file_hash(source_path),
            "semantic_sha256": MODULE.canonical_sha256(source),
            "consumes": list(consumes),
            "provides": [],
        }
        payload["artifacts"].append(artifact)
        for dependency in consumes:
            next(item for item in payload["artifacts"] if item["id"] == dependency)["provides"].append(artifact_id)
        if signer is not None:
            artifact.update({"attested_action": attested_action, "signer_identity": signer})
            consumed = [
                {"artifact_id": item, "semantic_sha256": next(row for row in payload["artifacts"] if row["id"] == item)["semantic_sha256"]}
                for item in consumes
            ]
            attestation = {
                "schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION,
                "proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"],
                "checkpoint_id": payload["checkpoint_id"], "lineage_id": payload["lineage_id"],
                "requested_action": attested_action, "artifact_id": artifact_id,
                "artifact_kind": kind, "evidence_class": artifact["evidence_class"],
                "source_sha256": artifact["source_sha256"], "semantic_sha256": artifact["semantic_sha256"],
                "consumed_artifacts": consumed,
            }
            attestation_path, signature_path = self.sign_json(attestation, signer, f"attestation-{artifact_id}")
            artifact["attestation_path"] = str(attestation_path)
            artifact["signature_path"] = str(signature_path)
        return artifact

    def resign_artifact(self, artifact: dict, source: dict) -> None:
        source_path = Path(artifact["source_path"])
        source_path.write_bytes(MODULE.canonical_json(source))
        artifact["source_sha256"] = file_hash(source_path)
        artifact["semantic_sha256"] = MODULE.canonical_sha256(source)
        consumed = [
            {"artifact_id": item, "semantic_sha256": next(row for row in self.payload["artifacts"] if row["id"] == item)["semantic_sha256"]}
            for item in artifact["consumes"]
        ]
        attestation = {
            "schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION,
            "proposal_id": self.payload["proposal_id"], "proposal_hash": self.payload["proposal_hash"],
            "checkpoint_id": self.payload["checkpoint_id"], "lineage_id": self.payload["lineage_id"],
            "requested_action": artifact["attested_action"], "artifact_id": artifact["id"],
            "artifact_kind": artifact["kind"], "evidence_class": artifact["evidence_class"],
            "source_sha256": artifact["source_sha256"], "semantic_sha256": artifact["semantic_sha256"],
            "consumed_artifacts": consumed,
        }
        attestation_path, signature_path = self.sign_json(attestation, artifact["signer_identity"], f"resigned-{artifact['id']}")
        artifact["attestation_path"] = str(attestation_path)
        artifact["signature_path"] = str(signature_path)

    def resign_review(self, row: dict, review: dict, signer: str, name: str) -> None:
        source, signature = self.sign_json(review, signer, name)
        semantic = MODULE.canonical_sha256(review)
        row.update({
            "source_path": str(source),
            "source_sha256": file_hash(source),
            "semantic_sha256": semantic,
            "attestation_sha256": semantic,
            "signature_path": str(signature),
        })

    def _pilot_scale(self) -> dict:
        return {
            "pilot_pass_conditions": [{"id": "P1", "measure": "correctness", "operator": "==", "threshold": "pass"}],
            "scale_conditions": [{"id": "S1", "measure": "effect_lower_bound", "operator": ">=", "threshold": 0.0}],
            "kill_conditions": [{"id": "K1", "measure": "failure_rate", "operator": ">=", "threshold": 0.2}],
            "scale_requires_all_conditions": True,
            "stop_on_any_kill": True,
            "max_interim_looks": 1,
            "interim_look_schedule": ["after frozen Phase 0"],
            "pilot_evidence_artifact_id": "phase0-result",
        }

    def _build(self) -> dict:
        payload = self._base()
        code = self._artifact(payload, "code-test", "code_test", "static_acquisition", {"tests_passed": True, "test_manifest_hash": "sha256:tests"}, [], None, None)
        stage_count = {"static_acquisition": 1, "human_oracle": 2, "phase0_launch": 3, "scale_launch": 4}[self.action]
        registry = bundle = labels = derivation = reproduction = capability = raw = result = None
        if stage_count >= 2:
            registry_source = {"proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"], "sources": []}
            registry = self._artifact(payload, "registry", "registry", "static_acquisition", registry_source, [code["id"]], "acquisition", "human_oracle")
            bundle_source = {
                "proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"],
                "registry_semantic_sha256": registry["semantic_sha256"], "blinded": True, "items": [],
            }
            bundle = self._artifact(payload, "bundle", "blinded_audit_bundle", "human_oracle", bundle_source, [registry["id"]], "acquisition", "human_oracle")
        if stage_count >= 3 and bundle is not None:
            labels = self._artifact(
                payload, "labels", "human_labels", "phase0_launch",
                {"proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"], "bundle_semantic_sha256": bundle["semantic_sha256"], "sealed": True, "labels": []},
                [bundle["id"]], "oracle", "phase0_launch",
            )
            derivation = self._artifact(
                payload, "derivation", "human_derivation", "phase0_launch",
                {"proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"], "bundle_semantic_sha256": bundle["semantic_sha256"], "sealed": True, "derivation": {}},
                [bundle["id"]], "oracle", "phase0_launch",
            )
            provisional_manifest = MODULE.v2_evidence_manifest_hash(payload)
            reproduction = self._artifact(
                payload, "reproduction", "clean_reproduction", "phase0_launch",
                {"bundle_semantic_sha256": bundle["semantic_sha256"], "evidence_manifest_hash": provisional_manifest, "manifest_semantic_sha256": "sha256:manifest", "clean": True},
                [bundle["id"]], "runtime", "phase0_launch",
            )
            capability = self._artifact(
                payload, "capability", "capability_evidence", "phase0_launch",
                {name: True for name in MODULE.V2_CAPABILITIES},
                [bundle["id"]], "runtime", "phase0_launch",
            )
            payload["phase0_requirements"] = {
                "registry_artifact_id": registry["id"], "bundle_artifact_id": bundle["id"],
                "labels_artifact_id": labels["id"], "derivation_artifact_id": derivation["id"],
                "reproduction_artifact_id": reproduction["id"], "capability_artifact_id": capability["id"],
            }
        if stage_count >= 4 and bundle is not None and labels is not None and derivation is not None and reproduction is not None and capability is not None:
            payload["pilot_scale"] = self._pilot_scale()
            raw_source = {
                "conditions": {"P1": "pass", "S1": 0.01, "K1": 0.1},
                "bundle_semantic_sha256": bundle["semantic_sha256"],
                "evidence_manifest_hash": MODULE.v2_evidence_manifest_hash(payload),
            }
            raw = self._artifact(payload, "phase0-raw", "phase0_raw_result", "phase0_launch", raw_source, [labels["id"], derivation["id"], reproduction["id"], capability["id"]], "runtime", "scale_launch")
            evidence_source = {
                "schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION,
                "proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"],
                "checkpoint": "pre_scale", "requested_action": "scale_launch",
                "pilot_plan_hash": MODULE.v2_pilot_plan_hash(payload["pilot_scale"]),
                "bundle_semantic_sha256": bundle["semantic_sha256"],
                "evidence_manifest_hash": MODULE.v2_evidence_manifest_hash(payload),
                "condition_results": [
                    {"condition_id": item, "observed": value, "source_artifact_id": raw["id"], "source_json_pointer": f"/conditions/{item}"}
                    for item, value in raw_source["conditions"].items()
                ],
            }
            result = self._artifact(payload, "phase0-result", "phase0_result", "scale_launch", evidence_source, [raw["id"]], "runtime", "scale_launch")
        provided = {stage: [row["id"] for row in payload["artifacts"] if row["producer_stage"] == stage] for stage in MODULE.V2_STAGES}
        payload["stages"] = []
        for index, stage in enumerate(MODULE.V2_STAGES):
            stage_provided = provided[stage]
            stage_required = sorted({
                dependency
                for item in stage_provided
                for dependency in next(row for row in payload["artifacts"] if row["id"] == item)["consumes"]
                if next(row for row in payload["artifacts"] if row["id"] == dependency)["producer_stage"] != stage
            })
            payload["stages"].append({"id": stage, "status": "passed" if index < stage_count else "pending", "required_artifacts": stage_required, "provided_artifacts": stage_provided})
        payload["evidence_manifest_hash"] = MODULE.v2_evidence_manifest_hash(payload)
        payload["core_hash"] = MODULE.v3_action_core_hash(payload, self.action)
        self._reviews(payload)
        self._lineage(payload)
        return payload

    def _reviews(self, payload: dict) -> None:
        payload["review_history"] = []
        payload["current_review_ids"] = []

    def _make_reviews(
        self, payload: dict, action: str, opened_hash: str, core: str,
        manifest: str, phase: str, blocked_index: int | None,
    ) -> list[dict]:
        rows = []
        for index, plan in enumerate(payload["review_plan"]):
            verdict = "blocked" if blocked_index == index else "pass"
            review = {
                "schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION,
                "proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"],
                "requested_action": action, "opened_event_hash": opened_hash,
                "core_hash": core, "evidence_manifest_hash": manifest,
                "plan_hash": payload["review_plan_hash"], "reviewer_id": plan["reviewer_id"],
                "reviewer_context_id": plan["reviewer_context_id"], "reviewer_model": plan["reviewer_model"],
                "signer_principal": plan["signer_identity"], "signer_role": "reviewer",
                "phase": phase, "verdict": verdict,
                "findings": [] if verdict == "pass" else [{"id": "F1", "severity": "high", "status": "open", "summary": "blocking finding"}],
            }
            source, signature = self.sign_json(review, plan["signer_identity"], f"review-{action}-{phase}-{index}")
            semantic = MODULE.canonical_sha256(review)
            rows.append({
                "event": "review", "review_id": f"{action}-{phase}-{index}",
                "reviewer_id": plan["reviewer_id"], "phase": phase,
                "core_hash": core, "evidence_manifest_hash": manifest,
                "requested_action": action, "opened_event_hash": opened_hash,
                "source_path": str(source), "source_sha256": file_hash(source),
                "semantic_sha256": semantic, "attestation_sha256": semantic,
                "signature_path": str(signature),
            })
        return rows

    def _cycle_hash(self, payload: dict, rows: list[dict]) -> tuple[str, str]:
        first = rows[0]
        planned = [{
            "reviewer_id": row["reviewer_id"], "signer_principal": row["signer_identity"],
            "signer_role": "reviewer", "reviewer_context_id": row["reviewer_context_id"],
            "reviewer_model": row["reviewer_model"],
        } for row in sorted(payload["review_plan"], key=lambda item: item["reviewer_id"])]
        reviews = []
        blocked = False
        for row in sorted(rows, key=lambda item: item["reviewer_id"]):
            review = json.loads(Path(row["source_path"]).read_text())
            blocked = blocked or review["verdict"] == "blocked"
            reviews.append({
                "reviewer_id": row["reviewer_id"],
                "signer_principal": next(item for item in payload["review_plan"] if item["reviewer_id"] == row["reviewer_id"])["signer_identity"],
                "reviewer_context_id": review["reviewer_context_id"],
                "verdict": review["verdict"], "findings": sorted(review["findings"], key=lambda item: item["id"]),
                "source_sha256": row["source_sha256"], "semantic_sha256": row["semantic_sha256"],
                "attestation_sha256": row["attestation_sha256"],
            })
        projection = {
            "requested_action": first["requested_action"], "opened_event_hash": first["opened_event_hash"],
            "core_hash": first["core_hash"], "evidence_manifest_hash": first["evidence_manifest_hash"],
            "review_plan_hash": payload["review_plan_hash"], "phase": first["phase"],
            "planned_reviewers": planned, "reviews": reviews,
        }
        return MODULE.canonical_sha256(projection), "blocked" if blocked else "pass"

    def _lineage(self, payload: dict) -> None:
        payload["review_history"] = []
        payload["current_review_ids"] = []
        events = []
        previous = MODULE.V3_EMPTY_LEDGER_TAIL

        def append_event(event_type: str, action: str | None, bindings: dict[str, str], outcome: str | None = None) -> dict:
            nonlocal previous
            body = {
                "seq": len(events), "previous_event_hash": previous, "event_type": event_type,
                "checkpoint_id": payload["checkpoint_id"], "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"], "lineage_id": payload["lineage_id"],
                "protocol_version": MODULE.PROTOCOL_VERSION, "requested_action": action,
                "signer_principal": "lineage", "signer_role": "lineage_authority",
                "bindings": bindings, "expected_ledger_tail": previous, "outcome": outcome,
            }
            event_hash = MODULE.canonical_sha256(body)
            envelope = {"body": body, "event_hash": event_hash}
            _source, signature = self.sign_json(
                envelope, "lineage", f"event-{len(events)}",
                namespace=MODULE.V3_LINEAGE_NAMESPACE,
            )
            row = {"body": body, "event_hash": event_hash, "signature_path": str(signature)}
            events.append(row)
            previous = event_hash
            return row

        append_event("checkpoint_opened", None, {"action_order": ",".join(MODULE.V2_ACTIONS)})
        action_position = MODULE.V2_ACTIONS.index(self.action)
        for position, action in enumerate(MODULE.V2_ACTIONS[:action_position + 1]):
            current_core = MODULE.v3_action_core_hash(payload, action)
            current_manifest = MODULE.v3_action_evidence_manifest_hash(payload, self.artifact_path, action, {row["id"]: row for row in payload["artifacts"]})
            is_current = action == self.action
            opened_core = "sha256:" + "0" * 64 if is_current and self.correction else current_core
            opened_manifest = "sha256:" + "1" * 64 if is_current and self.correction else current_manifest
            opened = append_event("action_opened", action, {
                "core_hash": opened_core, "evidence_manifest_hash": opened_manifest,
                "review_plan_hash": payload["review_plan_hash"],
            })
            initial_blocked = 0 if is_current and self.correction else (self.blocked_reviewer if is_current else None)
            initial_rows = self._make_reviews(payload, action, opened["event_hash"], opened_core, opened_manifest, "initial", initial_blocked)
            payload["review_history"].extend(initial_rows)
            final_rows = initial_rows
            correction_event = None
            if is_current and self.correction:
                initial_cycle_hash, _initial_verdict = self._cycle_hash(payload, initial_rows)
                correction_event = append_event("correction_applied", action, {
                    "opened_event_hash": opened["event_hash"],
                    "before_core_hash": opened_core, "after_core_hash": current_core,
                    "before_manifest_hash": opened_manifest, "after_manifest_hash": current_manifest,
                    "initial_review_cycle_hash": initial_cycle_hash,
                })
                final_rows = self._make_reviews(
                    payload, action, opened["event_hash"], current_core, current_manifest,
                    "re_review", self.blocked_reviewer,
                )
                payload["review_history"].extend(final_rows)
            if is_current:
                payload["current_review_ids"] = [row["review_id"] for row in final_rows]
            cycle_hash, verdict = self._cycle_hash(payload, final_rows)
            if verdict == "blocked" and not (is_current and self.correction):
                continue
            outcome = "authorized" if verdict == "pass" else "architecture_reset_required"
            bindings = {
                "opened_event_hash": opened["event_hash"],
                "final_core_hash": current_core, "final_manifest_hash": current_manifest,
                "review_cycle_hash": cycle_hash,
                "review_phase": "re_review" if correction_event else "initial",
                "review_verdict": verdict,
            }
            if correction_event:
                bindings["correction_event_hash"] = correction_event["event_hash"]
            append_event("action_finalized", action, bindings, outcome)
            if outcome == "architecture_reset_required":
                break
        self.ledger = self.root / "lineage-ledger.json"
        self.ledger.write_bytes(MODULE.canonical_json({"schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION, "events": events}))
        self.tail_hash = previous

    def _write_artifact(self) -> None:
        self.artifact_path.write_bytes(MODULE.canonical_json(self.payload))

    def refresh_file(self) -> None:
        self._write_artifact()

    def argv(self, action: str | None = None) -> list[str]:
        return [
            str(self.artifact_path), "--required-authorization", action or self.action,
            "--trust-policy", str(self.policy), "--trust-policy-sha256", MODULE.canonical_sha256(json.loads(self.policy.read_text())),
            "--lineage-ledger", str(self.ledger), "--lineage-tail-sha256", str(self.tail_hash),
        ]


class GrillValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.key_temp = tempfile.TemporaryDirectory()
        root = Path(cls.key_temp.name)
        identities = {
            "acquisition": ["acquisition_attestor"],
            "oracle": ["human_oracle"],
            "runtime": ["runtime_attestor"],
            "lineage": ["lineage_authority"],
            "reviewer-1": ["reviewer"],
            "reviewer-2": ["reviewer"],
        }
        cls.keys: dict[str, Path] = {}
        rows = []
        for identity, roles in identities.items():
            key = root / identity
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", identity, "-f", str(key)], check=True)
            cls.keys[identity] = key
            public_key = key.with_suffix(".pub").read_text(encoding="utf-8").strip()
            rows.append({"identity": identity, "roles": roles, "public_key": public_key})
        cls.policy = root / "trust-policy.json"
        cls.policy.write_bytes(MODULE.canonical_json({"schema_version": 1, "protocol_version": MODULE.PROTOCOL_VERSION, "namespace": MODULE.V2_ATTESTATION_NAMESPACE, "identities": rows}))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.key_temp.cleanup()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def fixture(self, action: str, **kwargs) -> SignedFixture:
        return SignedFixture(self.root, self.keys, self.policy, action, **kwargs)

    def run_main(self, fixture: SignedFixture, action: str | None = None, argv: list[str] | None = None) -> tuple[int, str]:
        fixture.refresh_file()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = MODULE.main(argv if argv is not None else fixture.argv(action))
        return code, stdout.getvalue() + stderr.getvalue()

    def assert_failure(self, fixture: SignedFixture, diagnostic: str, code: int = 1, action: str | None = None) -> None:
        actual, output = self.run_main(fixture, action)
        self.assertEqual(actual, code, output)
        self.assertIn(diagnostic, output)

    def argv_with_role_removed(self, fixture: SignedFixture, identity: str, role: str) -> list[str]:
        policy = json.loads(self.policy.read_text(encoding="utf-8"))
        row = next(item for item in policy["identities"] if item["identity"] == identity)
        row["roles"] = [item for item in row["roles"] if item != role]
        path = self.root / f"policy-without-{identity}-{role}.json"
        path.write_bytes(MODULE.canonical_json(policy))
        argv = fixture.argv()
        argv[argv.index("--trust-policy") + 1] = str(path)
        argv[argv.index("--trust-policy-sha256") + 1] = MODULE.canonical_sha256(policy)
        return argv

    def add_signed_human_decision(self, fixture: SignedFixture) -> dict:
        payload = fixture.payload
        bundle = next(row for row in payload["artifacts"] if row["kind"] == "blinded_audit_bundle")
        decision_source = {
            "proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"],
            "ambiguity_id": "A1", "resolution": "use proposal semantics", "approved_by": "owner",
        }
        decision = fixture._artifact(payload, "decision-A1", "human_decision", "phase0_launch", decision_source, [bundle["id"]], "oracle", "phase0_launch")
        human_stage = next(row for row in payload["stages"] if row["id"] == "human_oracle")
        human_stage["provided_artifacts"].append(decision["id"])
        payload["ambiguities"] = [{
            "id": "A1", "severity": "high", "question": "Which semantics?", "source": "human decision",
            "status": "resolved", "resolution": "use proposal semantics",
            "resolution_authority": "human_decision", "decision_artifact_id": decision["id"],
        }]
        new_manifest = MODULE.v2_evidence_manifest_hash(payload)
        reproduction = next(row for row in payload["artifacts"] if row["kind"] == "clean_reproduction")
        reproduction_source = json.loads(Path(reproduction["source_path"]).read_text())
        reproduction_source["evidence_manifest_hash"] = new_manifest
        fixture.resign_artifact(reproduction, reproduction_source)
        payload["evidence_manifest_hash"] = new_manifest
        payload["core_hash"] = MODULE.v2_core_hash(payload)
        payload["review_history"] = []; payload["current_review_ids"] = []
        fixture._reviews(payload); fixture._lineage(payload)
        return decision

    def test_zero_state_code_readiness_authorizes_static_acquisition(self) -> None:
        fixture = self.fixture("static_acquisition")
        self.assertEqual([row["kind"] for row in fixture.payload["artifacts"]], ["code_test"])
        self.assertEqual(self.run_main(fixture)[0], 0)

    def test_static_acquisition_authorizes_human_oracle_without_labels(self) -> None:
        fixture = self.fixture("human_oracle")
        self.assertNotIn("human_labels", {row["kind"] for row in fixture.payload["artifacts"]})
        self.assertEqual(self.run_main(fixture)[0], 0)

    def test_phase0_launch_authorizes_with_signed_human_runtime_and_review_evidence(self) -> None:
        self.assertEqual(self.run_main(self.fixture("phase0_launch"))[0], 0)

    def test_scale_launch_authorizes_after_signed_phase0_evidence(self) -> None:
        self.assertEqual(self.run_main(self.fixture("scale_launch"))[0], 0)

    def test_payload_status_and_authorization_are_informational_only(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["status"] = "claimed-ready"
        fixture.payload["authorization"] = "claimed-authorized"
        self.assertEqual(self.run_main(fixture)[0], 0)

    def test_code_only_human_oracle_is_contract_invalid(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.action = "human_oracle"
        fixture.payload["review_history"] = []
        fixture.payload["current_review_ids"] = []
        fixture._reviews(fixture.payload)
        fixture._lineage(fixture.payload)
        code, output = self.run_main(fixture, "human_oracle")
        self.assertEqual(code, 1, output)
        self.assertIn("minimum_evidence.human_oracle: missing required artifact kind registry", output)

    def test_missing_required_authorization_is_non_authorizing(self) -> None:
        fixture = self.fixture("static_acquisition")
        self.assertEqual(self.run_main(fixture, argv=[str(fixture.artifact_path)])[0], 3)

    def test_missing_trust_policy_is_operational_blocked(self) -> None:
        fixture = self.fixture("static_acquisition")
        argv = fixture.argv()
        start = argv.index("--trust-policy")
        del argv[start:start + 4]
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 3)
        self.assertIn("trust_policy", output)

    def test_wrong_trust_policy_pin_is_operational_blocked(self) -> None:
        fixture = self.fixture("static_acquisition")
        argv = fixture.argv(); argv[argv.index("--trust-policy-sha256") + 1] = "sha256:" + "0" * 64
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 3); self.assertIn("pin mismatch", output)

    def test_missing_static_signature_is_contract_error(self) -> None:
        fixture = self.fixture("human_oracle")
        Path(fixture.payload["artifacts"][1]["signature_path"]).unlink()
        self.assert_failure(fixture, "detached signature is missing", 1)

    def test_forged_static_signature_is_contract_error(self) -> None:
        fixture = self.fixture("human_oracle")
        signature = Path(fixture.payload["artifacts"][1]["signature_path"])
        signature.write_text("forged", encoding="utf-8")
        self.assert_failure(fixture, "verification failed", 1)

    def test_wrong_static_signer_role_is_contract_error(self) -> None:
        fixture = self.fixture("human_oracle")
        code, output = self.run_main(fixture, argv=self.argv_with_role_removed(fixture, "acquisition", "acquisition_attestor"))
        self.assertEqual(code, 1); self.assertIn("lacks required role acquisition_attestor", output)

    def test_agent_self_declared_human_role_cannot_authorize(self) -> None:
        fixture = self.fixture("phase0_launch")
        code, output = self.run_main(fixture, argv=self.argv_with_role_removed(fixture, "oracle", "human_oracle"))
        self.assertEqual(code, 1); self.assertIn("lacks required role human_oracle", output)

    def test_review_requires_planned_reviewer_signer(self) -> None:
        fixture = self.fixture("static_acquisition")
        code, output = self.run_main(fixture, argv=self.argv_with_role_removed(fixture, "reviewer-1", "reviewer"))
        self.assertEqual(code, 1); self.assertIn("trusted reviewer role", output)

    def test_runtime_evidence_requires_runtime_attestor(self) -> None:
        fixture = self.fixture("phase0_launch")
        code, output = self.run_main(fixture, argv=self.argv_with_role_removed(fixture, "runtime", "runtime_attestor"))
        self.assertEqual(code, 1); self.assertIn("lacks required role runtime_attestor", output)

    def test_signed_runtime_unavailability_is_operational_blocked(self) -> None:
        fixture = self.fixture("phase0_launch")
        capability = next(row for row in fixture.payload["artifacts"] if row["kind"] == "capability_evidence")
        source = json.loads(Path(capability["source_path"]).read_text())
        source["runtime_available"] = False
        fixture.resign_artifact(capability, source)
        code, output = self.run_main(fixture)
        self.assertEqual(code, 3, output)
        self.assertIn("OPERATIONAL_BLOCKED", output)
        self.assertIn("signed runtime capability unavailable: runtime_available", output)

    def test_malformed_signed_capability_is_contract_error(self) -> None:
        fixture = self.fixture("phase0_launch")
        capability = next(row for row in fixture.payload["artifacts"] if row["kind"] == "capability_evidence")
        source = json.loads(Path(capability["source_path"]).read_text())
        source["runtime_available"] = "false"
        fixture.resign_artifact(capability, source)
        code, output = self.run_main(fixture)
        self.assertEqual(code, 1, output)
        self.assertNotIn("OPERATIONAL_BLOCKED", output)
        self.assertIn("runtime_available: expected an exact boolean", output)

    def test_unsigned_capability_is_contract_error(self) -> None:
        fixture = self.fixture("phase0_launch")
        capability = next(row for row in fixture.payload["artifacts"] if row["kind"] == "capability_evidence")
        Path(capability["signature_path"]).unlink()
        code, output = self.run_main(fixture)
        self.assertEqual(code, 1, output)
        self.assertNotIn("OPERATIONAL_BLOCKED", output)
        self.assertIn("detached signature is missing", output)

    def test_static_schema_rejects_hidden_forbidden_content(self) -> None:
        fixture = self.fixture("human_oracle")
        registry = next(row for row in fixture.payload["artifacts"] if row["kind"] == "registry")
        path = Path(registry["source_path"]); value = json.loads(path.read_text()); value["scientific_metrics"] = [1]
        path.write_bytes(MODULE.canonical_json(value))
        self.assert_failure(fixture, "keys must be exactly")

    def test_bundle_proposal_mismatch_is_rejected(self) -> None:
        fixture = self.fixture("human_oracle")
        bundle = next(row for row in fixture.payload["artifacts"] if row["kind"] == "blinded_audit_bundle")
        path = Path(bundle["source_path"]); value = json.loads(path.read_text()); value["proposal_id"] = "wrong"; path.write_bytes(MODULE.canonical_json(value))
        self.assert_failure(fixture, "bundle proposal binding mismatch")

    def test_bundle_registry_mismatch_is_rejected(self) -> None:
        fixture = self.fixture("human_oracle")
        bundle = next(row for row in fixture.payload["artifacts"] if row["kind"] == "blinded_audit_bundle")
        path = Path(bundle["source_path"]); value = json.loads(path.read_text()); value["registry_semantic_sha256"] = "sha256:wrong"; path.write_bytes(MODULE.canonical_json(value))
        self.assert_failure(fixture, "bundle is not bound")

    def test_reproduction_bundle_mismatch_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        artifact = next(row for row in fixture.payload["artifacts"] if row["kind"] == "clean_reproduction")
        path = Path(artifact["source_path"]); value = json.loads(path.read_text()); value["bundle_semantic_sha256"] = "sha256:wrong"; path.write_bytes(MODULE.canonical_json(value))
        self.assert_failure(fixture, "reproduction bundle binding mismatch")

    def test_reproduction_manifest_mismatch_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        artifact = next(row for row in fixture.payload["artifacts"] if row["kind"] == "clean_reproduction")
        path = Path(artifact["source_path"]); value = json.loads(path.read_text()); value["evidence_manifest_hash"] = "sha256:wrong"; path.write_bytes(MODULE.canonical_json(value))
        self.assert_failure(fixture, "exact evidence manifest")

    def test_omitted_opposing_reviewer_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2)
        omitted = fixture.payload["current_review_ids"][-1]
        fixture.payload["review_history"] = [row for row in fixture.payload["review_history"] if row["review_id"] != omitted]
        self.assert_failure(fixture, "retained complete signed review cycle")

    def test_blocked_review_prevents_authorization(self) -> None:
        fixture = self.fixture("phase0_launch", blocked_reviewer=0)
        self.assertEqual(self.run_main(fixture)[0], 3)

    def test_open_high_finding_prevents_authorization(self) -> None:
        fixture = self.fixture("phase0_launch")
        row = fixture.payload["review_history"][0]; source = Path(row["source_path"]); review = json.loads(source.read_text())
        review["findings"] = [{"id": "F", "severity": "high", "status": "open", "summary": "block"}]
        source.write_bytes(MODULE.canonical_json(review))
        self.assertEqual(self.run_main(fixture)[0], 1)

    def test_malformed_case_varied_finding_enum_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        row = fixture.payload["review_history"][0]; source = Path(row["source_path"]); review = json.loads(source.read_text())
        review["findings"] = [{"id": "F", "severity": "High", "status": "Open", "summary": "bad enum"}]
        source.write_bytes(MODULE.canonical_json(review))
        self.assert_failure(fixture, "malformed exact enum")

    def test_stale_review_core_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        fixture.payload["review_history"][0]["core_hash"] = "sha256:" + "1" * 64
        self.assert_failure(fixture, "source.core_hash: stale or mismatched binding")

    def test_stale_review_action_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        fixture.payload["review_history"][0]["requested_action"] = "human_oracle"
        self.assert_failure(fixture, "source.requested_action: stale or mismatched binding")

    def test_valid_correction_complete_rereview_authorizes(self) -> None:
        self.assertEqual(self.run_main(self.fixture("phase0_launch", reviewers=2, correction=True))[0], 0)

    def test_correction_requires_retained_blocked_initial_review_cycle(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2, correction=True)
        initial_id = next(
            row["review_id"] for row in fixture.payload["review_history"]
            if row["phase"] == "initial" and row["requested_action"] == "phase0_launch"
        )
        fixture.payload["review_history"] = [
            row for row in fixture.payload["review_history"] if row["review_id"] != initial_id
        ]
        self.assert_failure(fixture, "correction lacks its retained complete signed blocked initial review cycle")

    def test_same_reviewer_altered_initial_row_cannot_substitute_for_signed_cycle(self) -> None:
        fixture = self.fixture("phase0_launch", correction=True)
        row = next(
            item for item in fixture.payload["review_history"]
            if item["phase"] == "initial" and item["requested_action"] == "phase0_launch"
        )
        review = json.loads(Path(row["source_path"]).read_text())
        review["findings"][0]["summary"] = "different blocked finding"
        source, signature = fixture.sign_json(review, "reviewer-1", "substitute-initial-review")
        semantic = MODULE.canonical_sha256(review)
        row.update({
            "source_path": str(source), "source_sha256": file_hash(source),
            "semantic_sha256": semantic, "attestation_sha256": semantic,
            "signature_path": str(signature),
        })
        self.assert_failure(fixture, "correction lacks its retained complete signed blocked initial review cycle")

    def test_prepare_correction_binds_complete_blocked_initial_review_cycle(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2, correction=True)
        ledger = json.loads(fixture.ledger.read_text())
        correction_index = next(
            index for index, row in enumerate(ledger["events"])
            if row["body"]["event_type"] == "correction_applied"
        )
        ledger["events"] = ledger["events"][:correction_index]
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        fixture.tail_hash = ledger["events"][-1]["event_hash"]
        initial_rows = [
            row for row in fixture.payload["review_history"]
            if row["phase"] == "initial" and row["requested_action"] == "phase0_launch"
        ]
        fixture.payload["current_review_ids"] = [row["review_id"] for row in initial_rows]
        expected_cycle_hash, expected_verdict = fixture._cycle_hash(fixture.payload, initial_rows)
        self.assertEqual(expected_verdict, "blocked")
        candidate = self.root / "correction-candidate.json"
        argv = [
            str(fixture.artifact_path), "--prepare-event", "correction_applied",
            "--requested-action", "phase0_launch", "--candidate-out", str(candidate),
            "--trust-policy", str(self.policy),
            "--trust-policy-sha256", MODULE.canonical_sha256(json.loads(self.policy.read_text())),
            "--lineage-ledger", str(fixture.ledger),
            "--lineage-tail-sha256", fixture.tail_hash,
        ]
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 5, output)
        envelope = json.loads(candidate.read_text())
        self.assertEqual(
            envelope["body"]["bindings"]["initial_review_cycle_hash"],
            expected_cycle_hash,
        )

    def test_correction_requires_distinct_before_core(self) -> None:
        fixture = self.fixture("phase0_launch", correction=True)
        ledger = json.loads(fixture.ledger.read_text())
        correction = next(row for row in ledger["events"] if row["body"]["event_type"] == "correction_applied")
        correction["body"]["bindings"]["after_core_hash"] = correction["body"]["bindings"]["before_core_hash"]
        correction["body"]["bindings"]["after_manifest_hash"] = correction["body"]["bindings"]["before_manifest_hash"]
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        self.assert_failure(fixture, "correction must change core or manifest")

    def test_correction_without_complete_rereview_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2, correction=True)
        omitted = fixture.payload["current_review_ids"][-1]
        fixture.payload["review_history"] = [row for row in fixture.payload["review_history"] if row["review_id"] != omitted]
        self.assert_failure(fixture, "retained complete signed review cycle")

    def test_duplicate_review_identity_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        fixture.payload["review_history"].append(copy.deepcopy(fixture.payload["review_history"][0]))
        self.assert_failure(fixture, "review_id: missing or duplicate")

    def test_second_correction_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch", correction=True)
        ledger = json.loads(fixture.ledger.read_text())
        final = next(row for row in ledger["events"] if row["body"]["event_type"] == "action_finalized" and row["body"]["requested_action"] == "phase0_launch")
        correction = next(row for row in ledger["events"] if row["body"]["event_type"] == "correction_applied")
        final["body"]["event_type"] = "correction_applied"
        final["body"]["outcome"] = None
        final["body"]["bindings"] = copy.deepcopy(correction["body"]["bindings"])
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        self.assert_failure(fixture, "second correction")

    def test_second_rereview_cycle_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch", correction=True)
        rereview = next(row for row in fixture.payload["review_history"] if row.get("phase") == "re_review")
        extra = copy.deepcopy(rereview)
        extra["review_id"] = "second-rereview"
        extra["core_hash"] = "sha256:" + "f" * 64
        fixture.payload["review_history"].append(extra)
        self.assert_failure(fixture, "stale or mismatched binding")

    def test_blocked_rereview_is_terminal(self) -> None:
        fixture = self.fixture("phase0_launch", correction=True, blocked_reviewer=0)
        self.assertEqual(self.run_main(fixture)[0], 3)

    def test_terminal_scale_rereview_revokes_every_prior_action(self) -> None:
        fixture = self.fixture("scale_launch", correction=True, blocked_reviewer=0)
        for action in MODULE.V2_ACTIONS:
            with self.subTest(action=action):
                code, output = self.run_main(fixture, action)
                self.assertEqual(code, 3, output)
                self.assertIn("not yet authorized", output)

    def test_project_local_vn_reset_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        ledger = json.loads(fixture.ledger.read_text())
        duplicate = copy.deepcopy(ledger["events"][0])
        duplicate["body"]["seq"] = len(ledger["events"])
        duplicate["body"]["previous_event_hash"] = ledger["events"][-1]["event_hash"]
        duplicate["body"]["expected_ledger_tail"] = ledger["events"][-1]["event_hash"]
        duplicate["event_hash"] = MODULE.canonical_sha256(duplicate["body"])
        ledger["events"].append(duplicate)
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        self.assert_failure(fixture, "checkpoint may open exactly once")

    def test_lineage_tail_pin_mismatch_is_operational_blocked(self) -> None:
        fixture = self.fixture("static_acquisition")
        ledger = json.loads(fixture.ledger.read_text())
        ledger["events"][1]["body"]["expected_ledger_tail"] = "sha256:stale"
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        self.assert_failure(fixture, "stale expected ledger tail")

    def test_lineage_truncation_fails_external_tail_pin(self) -> None:
        fixture = self.fixture("phase0_launch")
        ledger = json.loads(fixture.ledger.read_text()); ledger["events"] = ledger["events"][:-1]
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        code, output = self.run_main(fixture)
        self.assertEqual(code, 1); self.assertIn("external pin does not match observed canonical ledger tail", output)

    def test_missing_lineage_signature_is_operational_blocked(self) -> None:
        fixture = self.fixture("static_acquisition")
        ledger = json.loads(fixture.ledger.read_text()); Path(ledger["events"][0]["signature_path"]).unlink()
        code, output = self.run_main(fixture)
        self.assertEqual(code, 1); self.assertIn("detached signature is missing", output)

    def test_append_only_lineage_authorizes_all_four_actions_sequentially(self) -> None:
        fixture = self.fixture("scale_launch")
        fixture.payload["review_history"] = []
        fixture.payload["current_review_ids"] = []
        fixture.ledger.write_bytes(MODULE.canonical_json({
            "schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION, "events": [],
        }))

        def prepare_and_append(event_type: str, action: str | None) -> dict:
            candidate = self.root / f"candidate-{event_type}-{action or 'checkpoint'}.json"
            ledger_before = json.loads(fixture.ledger.read_text())
            tail = (
                ledger_before["events"][-1]["event_hash"]
                if ledger_before["events"] else MODULE.V3_EMPTY_LEDGER_TAIL
            )
            argv = [
                str(fixture.artifact_path), "--prepare-event", event_type,
                "--candidate-out", str(candidate),
                "--trust-policy", str(self.policy),
                "--trust-policy-sha256", MODULE.canonical_sha256(json.loads(self.policy.read_text())),
                "--lineage-ledger", str(fixture.ledger),
                "--lineage-tail-sha256", tail,
            ]
            if action is not None:
                argv.extend(["--requested-action", action])
            code, output = self.run_main(fixture, argv=argv)
            self.assertEqual(code, 5, output)
            envelope = json.loads(candidate.read_text())
            self.assertEqual(envelope["body"]["previous_event_hash"], tail)
            self.assertEqual(envelope["body"]["expected_ledger_tail"], tail)
            subprocess.run(
                ["ssh-keygen", "-Y", "sign", "-q", "-f", str(self.keys["lineage"]),
                 "-n", MODULE.V3_LINEAGE_NAMESPACE, str(candidate)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            ledger = json.loads(fixture.ledger.read_text())
            existing_hashes = [row["event_hash"] for row in ledger["events"]]
            ledger["events"].append({
                "body": envelope["body"], "event_hash": envelope["event_hash"],
                "signature_path": str(candidate) + ".sig",
            })
            fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
            fixture.tail_hash = envelope["event_hash"]
            self.assertEqual([row["event_hash"] for row in ledger["events"][:-1]], existing_hashes)
            return envelope

        prepare_and_append("checkpoint_opened", None)
        for action in MODULE.V2_ACTIONS:
            opened = prepare_and_append("action_opened", action)
            bindings = opened["body"]["bindings"]
            reviews = fixture._make_reviews(
                fixture.payload, action, opened["event_hash"], bindings["core_hash"],
                bindings["evidence_manifest_hash"], "initial", None,
            )
            fixture.payload["review_history"].extend(reviews)
            fixture.payload["current_review_ids"] = [row["review_id"] for row in reviews]
            prepare_and_append("action_finalized", action)
            code, output = self.run_main(fixture, action=action)
            self.assertEqual(code, 0, output)

    def test_candidate_prepare_is_nonauthorizing_and_no_overwrite(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["review_history"] = []
        fixture.payload["current_review_ids"] = []
        fixture.ledger.write_bytes(MODULE.canonical_json({
            "schema_version": 3, "protocol_version": MODULE.PROTOCOL_VERSION, "events": [],
        }))
        fixture.tail_hash = MODULE.V3_EMPTY_LEDGER_TAIL
        candidate = self.root / "checkpoint-candidate.json"
        argv = [
            str(fixture.artifact_path), "--prepare-event", "checkpoint_opened",
            "--candidate-out", str(candidate), "--trust-policy", str(self.policy),
            "--trust-policy-sha256", MODULE.canonical_sha256(json.loads(self.policy.read_text())),
            "--lineage-ledger", str(fixture.ledger),
            "--lineage-tail-sha256", MODULE.V3_EMPTY_LEDGER_TAIL,
        ]
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 5, output)
        self.assertTrue(candidate.is_file())
        envelope = json.loads(candidate.read_text())
        self.assertEqual(envelope["body"]["expected_ledger_tail"], MODULE.V3_EMPTY_LEDGER_TAIL)
        self.assertEqual(self.run_main(fixture)[0], 3)
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 1, output)
        self.assertIn("already exists", output)

    def test_prepare_authorization_alias_emits_canonical_stdout_candidate(self) -> None:
        fixture = self.fixture("static_acquisition")
        ledger = json.loads(fixture.ledger.read_text())
        ledger["events"] = ledger["events"][:-1]
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        tail = ledger["events"][-1]["event_hash"]
        argv = [
            str(fixture.artifact_path), "--prepare-authorization", "static_acquisition",
            "--trust-policy", str(self.policy),
            "--trust-policy-sha256", MODULE.canonical_sha256(json.loads(self.policy.read_text())),
            "--lineage-ledger", str(fixture.ledger),
            "--lineage-tail-sha256", tail,
        ]
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 5, output)
        envelope = json.loads(output)
        self.assertEqual(envelope["body"]["event_type"], "action_finalized")
        self.assertEqual(envelope["event_hash"], MODULE.canonical_sha256(envelope["body"]))

    def test_prepare_rejects_wrong_external_tail_pin(self) -> None:
        fixture = self.fixture("static_acquisition")
        ledger = json.loads(fixture.ledger.read_text())
        ledger["events"] = ledger["events"][:-1]
        fixture.ledger.write_bytes(MODULE.canonical_json(ledger))
        argv = [
            str(fixture.artifact_path), "--prepare-authorization", "static_acquisition",
            "--trust-policy", str(self.policy),
            "--trust-policy-sha256", MODULE.canonical_sha256(json.loads(self.policy.read_text())),
            "--lineage-ledger", str(fixture.ledger),
            "--lineage-tail-sha256", "sha256:" + "0" * 64,
        ]
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 1, output)
        self.assertIn("zero tail is never a valid external pin", output)

    def test_required_authorization_rejects_stale_external_tail_pin(self) -> None:
        fixture = self.fixture("static_acquisition")
        argv = fixture.argv()
        argv[argv.index("--lineage-tail-sha256") + 1] = "sha256:" + "f" * 64
        code, output = self.run_main(fixture, argv=argv)
        self.assertEqual(code, 1, output)
        self.assertIn("external pin does not match observed canonical ledger tail", output)

    def test_minimum_evidence_reports_one_missing_kind_per_action(self) -> None:
        cases = {
            "static_acquisition": ({}, {}, set(), "code_test"),
            "human_oracle": (
                {"registry": {"id": "registry", "kind": "registry"}},
                {"registry": {}}, {"registry"}, "blinded_audit_bundle",
            ),
            "phase0_launch": (
                {
                    kind: {"id": kind, "kind": kind}
                    for kind in ("human_labels", "clean_reproduction", "capability_evidence")
                },
                {}, {"human_labels", "clean_reproduction", "capability_evidence"},
                "human_derivation",
            ),
            "scale_launch": (
                {
                    kind: {"id": kind, "kind": kind}
                    for kind in ("blinded_audit_bundle", "phase0_result")
                },
                {}, {"blinded_audit_bundle", "phase0_result"}, "phase0_raw_result",
            ),
        }
        for action, (artifacts, sources, verified, missing) in cases.items():
            with self.subTest(action=action):
                errors: list[str] = []
                MODULE.validate_v3_minimum_evidence(action, artifacts, sources, verified, errors)
                self.assertIn(
                    f"minimum_evidence.{action}: missing required artifact kind {missing}",
                    errors,
                )

    def test_dag_self_edge_is_rejected(self) -> None:
        fixture = self.fixture("human_oracle")
        fixture.payload["artifacts"][0]["consumes"] = ["code-test"]
        fixture.payload["artifacts"][0]["provides"] = ["code-test"]
        self.assert_failure(fixture, "self edge")

    def test_dag_cycle_is_rejected(self) -> None:
        fixture = self.fixture("human_oracle")
        fixture.payload["artifacts"][0]["consumes"] = ["registry"]
        fixture.payload["artifacts"][1]["provides"].append("code-test")
        self.assert_failure(fixture, "dependency cycle")

    def test_dag_future_edge_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        code = fixture.payload["artifacts"][0]
        labels = next(row for row in fixture.payload["artifacts"] if row["kind"] == "human_labels")
        code["consumes"] = [labels["id"]]; labels["provides"].append(code["id"])
        self.assert_failure(fixture, "future-stage dependency")

    def test_dag_inverse_provides_is_required(self) -> None:
        fixture = self.fixture("human_oracle")
        fixture.payload["artifacts"][0]["provides"] = []
        self.assert_failure(fixture, "inverse provides edge")

    def test_scale_raw_result_binding_is_recomputed(self) -> None:
        fixture = self.fixture("scale_launch")
        result = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_result")
        path = Path(result["source_path"]); evidence = json.loads(path.read_text()); evidence["condition_results"][1]["observed"] = -0.5; path.write_bytes(MODULE.canonical_json(evidence))
        self.assert_failure(fixture, "does not match bound raw result")

    def test_scale_result_is_bound_to_exact_frozen_bundle(self) -> None:
        fixture = self.fixture("scale_launch")
        result = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_result")
        path = Path(result["source_path"]); evidence = json.loads(path.read_text()); evidence["bundle_semantic_sha256"] = "sha256:wrong"; path.write_bytes(MODULE.canonical_json(evidence))
        self.assert_failure(fixture, "bundle_semantic_sha256: stale or mismatched")

    def test_scale_raw_result_rejects_other_valid_signed_bundle(self) -> None:
        fixture = self.fixture("scale_launch")
        payload = fixture.payload
        registry = next(row for row in payload["artifacts"] if row["kind"] == "registry")
        designated_bundle = next(row for row in payload["artifacts"] if row["id"] == payload["phase0_requirements"]["bundle_artifact_id"])
        alternate_source = {
            "proposal_id": payload["proposal_id"], "proposal_hash": payload["proposal_hash"],
            "registry_semantic_sha256": registry["semantic_sha256"], "blinded": True,
            "items": [{"artifact_id": "alternate-input", "semantic_sha256": "sha256:alternate"}],
        }
        alternate_bundle = fixture._artifact(
            payload, "bundle-B", "blinded_audit_bundle", "human_oracle",
            alternate_source, [registry["id"]], "acquisition", "human_oracle",
        )
        next(row for row in payload["stages"] if row["id"] == "static_acquisition")["provided_artifacts"].append(alternate_bundle["id"])
        evidence_hash = MODULE.v2_evidence_manifest_hash(payload)
        reproduction = next(row for row in payload["artifacts"] if row["kind"] == "clean_reproduction")
        reproduction_source = json.loads(Path(reproduction["source_path"]).read_text())
        reproduction_source["evidence_manifest_hash"] = evidence_hash
        fixture.resign_artifact(reproduction, reproduction_source)
        raw = next(row for row in payload["artifacts"] if row["kind"] == "phase0_raw_result")
        raw_source = json.loads(Path(raw["source_path"]).read_text())
        raw_source["bundle_semantic_sha256"] = alternate_bundle["semantic_sha256"]
        raw_source["evidence_manifest_hash"] = evidence_hash
        fixture.resign_artifact(raw, raw_source)
        result = next(row for row in payload["artifacts"] if row["kind"] == "phase0_result")
        result_source = json.loads(Path(result["source_path"]).read_text())
        result_source["bundle_semantic_sha256"] = designated_bundle["semantic_sha256"]
        result_source["evidence_manifest_hash"] = evidence_hash
        fixture.resign_artifact(result, result_source)
        payload["evidence_manifest_hash"] = evidence_hash
        payload["core_hash"] = MODULE.v2_core_hash(payload)
        payload["review_history"] = []
        payload["current_review_ids"] = []
        fixture._reviews(payload)
        fixture._lineage(payload)
        self.assert_failure(
            fixture,
            "pilot_scale.raw_result.phase0-raw.bundle_semantic_sha256: must match the exact",
        )

    def test_every_scale_manifest_evidence_identity_is_content_bound(self) -> None:
        fixture = self.fixture("scale_launch")
        artifacts = {row["id"]: row for row in fixture.payload["artifacts"]}
        manifest = MODULE.v3_action_evidence_manifest(
            fixture.payload, fixture.artifact_path, "scale_launch", artifacts,
        )
        baseline = MODULE.canonical_sha256(manifest)
        identity_fields = ("source_sha256", "semantic_sha256", "signature_identity", "attestation_payload")
        for row_index, row in enumerate(manifest):
            for field in identity_fields:
                if row[field] is None:
                    continue
                with self.subTest(artifact=row["id"], field=field):
                    changed = copy.deepcopy(manifest)
                    changed[row_index][field] = {"changed": True} if field == "attestation_payload" else "changed"
                    self.assertNotEqual(MODULE.canonical_sha256(changed), baseline)
            for dependency_index, _dependency in enumerate(row["consumed_artifacts"]):
                with self.subTest(artifact=row["id"], consumed=dependency_index):
                    changed = copy.deepcopy(manifest)
                    changed[row_index]["consumed_artifacts"][dependency_index]["semantic_sha256"] = "sha256:changed"
                    self.assertNotEqual(MODULE.canonical_sha256(changed), baseline)
        self.assertIn("phase0-raw", {row["id"] for row in manifest})
        self.assertIn("phase0-result", {row["id"] for row in manifest})

    def test_resigned_scale_runtime_change_invalidates_final_event_manifest(self) -> None:
        fixture = self.fixture("scale_launch")
        raw = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_raw_result")
        raw_source = json.loads(Path(raw["source_path"]).read_text())
        raw_source["conditions"]["S1"] = 0.02
        fixture.resign_artifact(raw, raw_source)
        result = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_result")
        result_source = json.loads(Path(result["source_path"]).read_text())
        next(item for item in result_source["condition_results"] if item["condition_id"] == "S1")["observed"] = 0.02
        fixture.resign_artifact(result, result_source)
        self.assert_failure(fixture, "action_finalized evidence manifest binding is stale")

    def test_scale_kill_gate_is_recomputed(self) -> None:
        fixture = self.fixture("scale_launch")
        raw = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_raw_result")
        path = Path(raw["source_path"]); value = json.loads(path.read_text()); value["conditions"]["K1"] = 0.3; path.write_bytes(MODULE.canonical_json(value))
        result = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_result")
        result_path = Path(result["source_path"]); evidence = json.loads(result_path.read_text()); next(item for item in evidence["condition_results"] if item["condition_id"] == "K1")["observed"] = 0.3; result_path.write_bytes(MODULE.canonical_json(evidence))
        self.assert_failure(fixture, "kill condition triggered")

    def test_scale_failed_condition_is_rejected(self) -> None:
        fixture = self.fixture("scale_launch")
        raw = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_raw_result")
        path = Path(raw["source_path"]); value = json.loads(path.read_text()); value["conditions"]["S1"] = -0.1; path.write_bytes(MODULE.canonical_json(value))
        result = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_result")
        result_path = Path(result["source_path"]); evidence = json.loads(result_path.read_text()); next(item for item in evidence["condition_results"] if item["condition_id"] == "S1")["observed"] = -0.1; result_path.write_bytes(MODULE.canonical_json(evidence))
        self.assert_failure(fixture, "required condition failed")

    def test_scale_requires_signed_pilot_evidence(self) -> None:
        fixture = self.fixture("scale_launch")
        fixture.payload["pilot_scale"]["pilot_evidence_artifact_id"] = "missing"
        self.assert_failure(fixture, "signed phase0_result")

    def test_scale_boolean_cannot_equal_numeric_threshold(self) -> None:
        fixture = self.fixture("scale_launch")
        fixture.payload["pilot_scale"]["scale_conditions"][0].update(operator="==", threshold=1)
        result = next(row for row in fixture.payload["artifacts"] if row["kind"] == "phase0_result")
        path = Path(result["source_path"]); evidence = json.loads(path.read_text()); next(item for item in evidence["condition_results"] if item["condition_id"] == "S1")["observed"] = True; path.write_bytes(MODULE.canonical_json(evidence))
        self.assert_failure(fixture, "incompatible observation type")

    def test_nonfinite_phase0_budget_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        fixture.payload["budget"]["phase0_limits"]["gpu_hours"] = math.inf
        fixture.artifact_path.write_text(json.dumps(fixture.payload).replace("Infinity", "1e999"), encoding="utf-8")
        stdout = io.StringIO(); stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = MODULE.main(fixture.argv())
        self.assertEqual(code, 1); self.assertIn("positive finite number", stdout.getvalue() + stderr.getvalue())

    def test_placeholder_claim_is_rejected(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["claims"][0]["text"] = "TODO: choose metric"
        self.assert_failure(fixture, "id and text are required")

    def test_every_claim_requires_mapping(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["claims"].append({"id": "C2", "text": "Second claim"})
        self.assert_failure(fixture, "uncovered claims")

    def test_unresolved_blocking_ambiguity_prevents_phase0(self) -> None:
        fixture = self.fixture("phase0_launch")
        fixture.payload["ambiguities"] = [{"id": "A1", "severity": "high", "question": "Which semantics?", "source": "proposal:1", "status": "unresolved"}]
        self.assert_failure(fixture, "unresolved blocking ambiguity")

    def test_signed_bound_human_decision_can_resolve_blocking_ambiguity(self) -> None:
        fixture = self.fixture("phase0_launch")
        self.add_signed_human_decision(fixture)
        self.assertEqual(self.run_main(fixture)[0], 0)

    def test_human_decision_binding_mismatch_is_rejected(self) -> None:
        fixture = self.fixture("phase0_launch")
        decision = self.add_signed_human_decision(fixture)
        path = Path(decision["source_path"]); value = json.loads(path.read_text()); value["ambiguity_id"] = "A2"; path.write_bytes(MODULE.canonical_json(value))
        self.assert_failure(fixture, "ambiguity_id binding mismatch")

    def test_unresolved_human_gate_prevents_phase0(self) -> None:
        fixture = self.fixture("phase0_launch")
        fixture.payload["unresolved_human_gates"] = ["H1"]
        self.assert_failure(fixture, "requires an empty list")

    def test_reviewer_model_allowlist_is_enforced(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["review_plan"][0]["reviewer_model"] = "gpt-fake"
        self.assert_failure(fixture, "type/model")

    def test_human_or_self_asserted_external_review_cannot_substitute(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["review_plan"][0]["reviewer_type"] = "external_review"
        self.assert_failure(fixture, "type/model")

    def test_reviewer_context_must_be_independent(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["review_plan"][0]["reviewer_context_id"] = fixture.payload["controller_context_id"]
        self.assert_failure(fixture, "context must be independent")

    def test_distinct_reviewer_ids_cannot_share_signer_identity(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2)
        fixture.payload["review_plan"][1]["signer_identity"] = fixture.payload["review_plan"][0]["signer_identity"]
        fixture.payload["review_plan_hash"] = MODULE.canonical_sha256(fixture.payload["review_plan"])
        fixture._lineage(fixture.payload)
        self.assert_failure(
            fixture,
            "signer_identity: missing or duplicate across planned reviewer slots",
        )

    def test_distinct_reviewer_ids_cannot_share_reviewer_context(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2)
        fixture.payload["review_plan"][1]["reviewer_context_id"] = fixture.payload["review_plan"][0]["reviewer_context_id"]
        fixture.payload["review_plan_hash"] = MODULE.canonical_sha256(fixture.payload["review_plan"])
        fixture._lineage(fixture.payload)
        self.assert_failure(
            fixture,
            "reviewer_context_id: missing or duplicate across planned reviewer slots",
        )

    def test_reviewer_cannot_swap_signer_between_initial_and_rereview(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2, correction=True)
        row = next(
            item for item in fixture.payload["review_history"]
            if item["requested_action"] == "phase0_launch"
            and item["phase"] == "re_review"
            and item["reviewer_id"] == "reviewer-1"
        )
        review = json.loads(Path(row["source_path"]).read_text())
        review["signer_principal"] = "reviewer-2"
        fixture.resign_review(row, review, "reviewer-2", "swapped-rereview-signer")
        self.assert_failure(
            fixture,
            "reviewer_id cannot swap signer/context between review phases",
        )

    def test_reviewer_cannot_swap_context_between_initial_and_rereview(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2, correction=True)
        row = next(
            item for item in fixture.payload["review_history"]
            if item["requested_action"] == "phase0_launch"
            and item["phase"] == "re_review"
            and item["reviewer_id"] == "reviewer-1"
        )
        review = json.loads(Path(row["source_path"]).read_text())
        review["reviewer_context_id"] = "review-context-2"
        fixture.resign_review(row, review, "reviewer-1", "swapped-rereview-context")
        self.assert_failure(
            fixture,
            "reviewer_id cannot swap signer/context between review phases",
        )

    def test_valid_two_reviewer_independent_plan_authorizes(self) -> None:
        fixture = self.fixture("phase0_launch", reviewers=2)
        self.assertEqual(self.run_main(fixture)[0], 0)

    def test_review_plan_hash_is_frozen(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["review_plan_hash"] = "sha256:" + "0" * 64
        self.assert_failure(fixture, "canonical frozen plan mismatch")

    def test_required_checkpoint_pre_scale_is_not_authorization(self) -> None:
        fixture = self.fixture("scale_launch")
        code, output = self.run_main(fixture, argv=[str(fixture.artifact_path), "--required-checkpoint", "pre_scale"])
        self.assertEqual(code, 1); self.assertIn("non-authorizing", output)

    def test_audit_v1_rejects_schema_v3(self) -> None:
        fixture = self.fixture("static_acquisition")
        code, output = self.run_main(fixture, argv=[str(fixture.artifact_path), "--audit-v1"])
        self.assertEqual(code, 1); self.assertIn("reject schema v3", output)

    def test_v2_requires_matching_audit_and_returns_distinct_exit(self) -> None:
        fixture = self.fixture("static_acquisition")
        fixture.payload["schema_version"] = 2
        fixture.payload["protocol_version"] = MODULE.LEGACY_V2_PROTOCOL_VERSION
        fixture.refresh_file()
        self.assertEqual(MODULE.main([str(fixture.artifact_path)]), 1)
        self.assertEqual(MODULE.main([str(fixture.artifact_path), "--audit-v1"]), 1)
        self.assertEqual(MODULE.main([str(fixture.artifact_path), "--audit-v2"]), 4)

    def test_v1_normal_mode_cannot_authorize(self) -> None:
        path = self.root / "v1.json"; path.write_text('{"schema_version":1}', encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(MODULE.main([str(path)]), 1)
        self.assertIn("cannot authorize", output.getvalue())

    def test_v1_audit_has_distinct_non_authorizing_exit(self) -> None:
        path = self.root / "v1.json"; path.write_bytes(MODULE.canonical_json(legacy_payload(self.root)))
        self.assertEqual(MODULE.main([str(path), "--audit-v2"]), 1)
        self.assertEqual(MODULE.main([str(path), "--audit-v1"]), 4)


if __name__ == "__main__":
    unittest.main()
