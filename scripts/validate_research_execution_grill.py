#!/usr/bin/env python3
"""Fail-closed validator for a research execution Grill artifact."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from research_grill_state_machine import (
        ACTION_ORDER as V3_ACTION_ORDER,
        EMPTY_LEDGER_TAIL as V3_EMPTY_LEDGER_TAIL,
        Action as V3Action,
        DecisionKind as V3DecisionKind,
        EventType as V3EventType,
        Outcome as V3Outcome,
        ValidatedEvent as V3ValidatedEvent,
        authorization as v3_authorization,
        evaluate as evaluate_v3_events,
    )
except ModuleNotFoundError:  # imported as a repository module in unit tests
    from scripts.research_grill_state_machine import (
        ACTION_ORDER as V3_ACTION_ORDER,
        EMPTY_LEDGER_TAIL as V3_EMPTY_LEDGER_TAIL,
        Action as V3Action,
        DecisionKind as V3DecisionKind,
        EventType as V3EventType,
        Outcome as V3Outcome,
        ValidatedEvent as V3ValidatedEvent,
        authorization as v3_authorization,
        evaluate as evaluate_v3_events,
    )


READY_STATUSES = {"implementation_ready", "scale_ready"}
CHECKPOINTS = {"pre_implementation", "pre_scale"}
LEGACY_V2_PROTOCOL_VERSION = "research-execution-grill-v2"
PROTOCOL_VERSION = "research-execution-grill-v3"
V2_SCHEMA_VERSION = 2
V3_SCHEMA_VERSION = 3
REVIEWER_TYPES = {
    "internal_blind_gpt",
    "human_domain_reviewer",
    "external_human_reviewer",
}
BLOCKING_SEVERITIES = {"p0", "critical", "high"}
AMBIGUITY_SEVERITIES = BLOCKING_SEVERITIES | {"medium", "low"}
FINDING_SEVERITIES = BLOCKING_SEVERITIES | {"medium", "low", "info"}
PARITY_STATES = {"matched", "not_applicable", "mismatch_mitigated"}
BASELINE_DIMENSIONS = (
    "data",
    "model",
    "tuning_budget",
    "inference_budget",
    "tools",
    "stopping_rule",
    "judge",
)
PLACEHOLDER = re.compile(
    r"(?i)(?:(?:^|[^a-z0-9_])(?:todo|tbd|fixme|unknown|placeholder|n/?a)(?=$|[^a-z0-9_])|待定|待补|占位)"
)
ALLOWED_GPT_MODELS = {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"}
MISSING = object()


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not PLACEHOLDER.search(value.strip())


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def require_string(payload: dict[str, Any], key: str, errors: list[str]) -> None:
    if not nonempty_string(payload.get(key)):
        errors.append(f"{key}: expected a non-placeholder string")


def require_string_list(payload: dict[str, Any], key: str, errors: list[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(nonempty_string(item) for item in value):
        errors.append(f"{key}: expected a non-empty list of non-placeholder strings")


def resolve_reference(value: Any, artifact_path: Path) -> Path | None:
    if not nonempty_string(value):
        return None
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else artifact_path.parent / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def grill_core_hash(payload: dict[str, Any]) -> str:
    """Hash the reviewable contract without the review rows that attest to it."""
    core = copy.deepcopy(payload)
    for key in ("reviews", "review_history", "core_hash", "convergence_state", "current_review_ids"):
        core.pop(key, None)
    # Review artifact content carries this hash, so attestations must not make
    # the hash recursively depend on themselves. Their IDs, kinds, and
    # provenance remain in the core; the review lifecycle validates content.
    for artifact in core.get("artifacts", []):
        if isinstance(artifact, dict) and artifact.get("kind") == "review":
            artifact["content"] = {"review_attestation": "excluded-from-core-hash"}
            artifact["canonical_sha256"] = "review-attestation-excluded"
    encoded = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def pilot_plan_hash(section: dict[str, Any]) -> str:
    """Hash the preregistered pilot/scale plan without its post-pilot evidence."""
    plan = copy.deepcopy(section)
    plan.pop("pilot_evidence", None)
    plan.pop("pilot_evidence_hash", None)
    encoded = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_json_object(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_json_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{label}: expected strict JSON object: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}: expected a JSON object")
        return None
    return value


def load_json_value(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_json_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{label}: expected strict JSON: {exc}")
        return MISSING


def resolve_json_pointer(value: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return MISSING
    current = value
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return MISSING
    return current


def strict_scalar_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isfinite(left) and math.isfinite(right) and left == right
    return type(left) is type(right) and left == right


def validate_hashed_file(
    payload: dict[str, Any],
    path_key: str,
    hash_key: str,
    artifact_path: Path,
    errors: list[str],
) -> None:
    path = resolve_reference(payload.get(path_key), artifact_path)
    if path is None:
        errors.append(f"{path_key}: expected a local file path")
        return
    if not path.is_file():
        errors.append(f"{path_key}: file does not exist: {path}")
        return
    if path.stat().st_size == 0:
        errors.append(f"{path_key}: file is empty: {path}")
        return
    expected = payload.get(hash_key)
    if not nonempty_string(expected):
        errors.append(f"{hash_key}: required")
        return
    actual = sha256_file(path)
    if expected != actual:
        errors.append(f"{hash_key}: content hash mismatch")


def validate_claims(payload: dict[str, Any], errors: list[str]) -> set[str]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims: expected a non-empty list")
        return set()
    ids: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claims[{index}]: expected an object")
            continue
        if not nonempty_string(claim.get("id")) or not nonempty_string(claim.get("text")):
            errors.append(f"claims[{index}]: id and text are required")
            continue
        claim_id = claim["id"].strip()
        if claim_id in ids:
            errors.append(f"claims[{index}]: duplicate id {claim_id!r}")
        ids.add(claim_id)
    return ids


def validate_ambiguities(
    payload: dict[str, Any], ready: bool, artifact_path: Path, errors: list[str]
) -> None:
    rows = payload.get("ambiguities")
    if not isinstance(rows, list):
        errors.append("ambiguities: expected a list")
        return
    required = ("id", "severity", "question", "source", "status")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"ambiguities[{index}]: expected an object")
            continue
        for field in required:
            if not nonempty_string(row.get(field)):
                errors.append(f"ambiguities[{index}].{field}: required")
        status = str(row.get("status") or "").strip().lower()
        severity = str(row.get("severity") or "").strip().lower()
        if severity not in AMBIGUITY_SEVERITIES:
            errors.append(f"ambiguities[{index}].severity: invalid")
        if status not in {"resolved", "unresolved"}:
            errors.append(f"ambiguities[{index}].status: expected resolved or unresolved")
        if status == "resolved" and not nonempty_string(row.get("resolution")):
            errors.append(f"ambiguities[{index}].resolution: required when resolved")
        if status == "resolved" and severity in BLOCKING_SEVERITIES:
            authority = row.get("resolution_authority")
            if authority not in {"proposal_source", "human_decision"}:
                errors.append(
                    f"ambiguities[{index}].resolution_authority: blocking resolutions require proposal_source or human_decision"
                )
            elif authority == "proposal_source":
                source = str(row.get("source") or "").strip().lower()
                if not re.match(r"^proposal:\s*\S.*$", source):
                    errors.append(f"ambiguities[{index}].source: proposal resolution requires a non-empty proposal:<locator>")
            else:
                validate_hashed_file(
                    row,
                    "decision_artifact",
                    "decision_artifact_hash",
                    artifact_path=artifact_path,
                    errors=errors,
                )
                decision_path = resolve_reference(row.get("decision_artifact"), artifact_path)
                if decision_path is not None and decision_path.is_file() and decision_path.stat().st_size > 0:
                    decision = load_json_object(
                        decision_path,
                        f"ambiguities[{index}].decision_artifact",
                        errors,
                    )
                    if decision is not None:
                        expected = {
                            "schema_version": 1,
                            "authority": "human_decision",
                            "proposal_id": payload.get("proposal_id"),
                            "proposal_hash": payload.get("proposal_hash"),
                            "ambiguity_id": row.get("id"),
                            "resolution": row.get("resolution"),
                        }
                        for field, value in expected.items():
                            if decision.get(field) != value:
                                errors.append(f"ambiguities[{index}].decision_artifact.{field}: mismatched")
                        for field in ("approved_by", "evidence_source"):
                            if not nonempty_string(decision.get(field)):
                                errors.append(f"ambiguities[{index}].decision_artifact.{field}: required")
                        validate_hashed_file(
                            decision,
                            "evidence_artifact",
                            "evidence_artifact_hash",
                            decision_path.resolve(),
                            errors,
                        )
                        evidence_path = resolve_reference(decision.get("evidence_artifact"), decision_path.resolve())
                        if evidence_path is not None and evidence_path.resolve() == decision_path.resolve():
                            errors.append(f"ambiguities[{index}].decision_artifact: evidence must be a distinct file")
        if ready and status != "resolved" and severity in BLOCKING_SEVERITIES:
            errors.append(f"ambiguities[{index}]: blocking ambiguity remains unresolved")


def validate_claim_matrix(
    payload: dict[str, Any], claim_ids: set[str], errors: list[str]
) -> None:
    rows = payload.get("claim_experiment_matrix")
    if not isinstance(rows, list) or not rows:
        errors.append("claim_experiment_matrix: expected a non-empty list")
        return
    covered: set[str] = set()
    fields = (
        "claim_id",
        "experiment_id",
        "metric",
        "oracle",
        "success_criterion",
        "kill_criterion",
    )
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"claim_experiment_matrix[{index}]: expected an object")
            continue
        for field in fields:
            if not nonempty_string(row.get(field)):
                errors.append(f"claim_experiment_matrix[{index}].{field}: required")
        if nonempty_string(row.get("claim_id")):
            covered.add(row["claim_id"].strip())
    missing = sorted(claim_ids - covered)
    if missing:
        errors.append("claim_experiment_matrix: uncovered claims=" + ",".join(missing))


def validate_baselines(payload: dict[str, Any], errors: list[str]) -> None:
    section = payload.get("baseline_fairness")
    if not isinstance(section, dict):
        errors.append("baseline_fairness: expected an object")
        return
    rows = section.get("rows")
    if isinstance(rows, list) and rows:
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"baseline_fairness.rows[{index}]: expected an object")
                continue
            if not nonempty_string(row.get("baseline")):
                errors.append(f"baseline_fairness.rows[{index}].baseline: required")
            for legacy in (*BASELINE_DIMENSIONS, "parity", "mismatch_analysis"):
                if legacy in row:
                    errors.append(f"baseline_fairness.rows[{index}].{legacy}: legacy duplicate semantic field is forbidden")
            comparability = row.get("comparability")
            if not isinstance(comparability, dict):
                errors.append(f"baseline_fairness.rows[{index}].comparability: expected an object")
                continue
            for field in BASELINE_DIMENSIONS:
                item = comparability.get(field)
                if not isinstance(item, dict):
                    errors.append(f"baseline_fairness.rows[{index}].comparability.{field}: expected an object")
                    continue
                if item.get("status") not in PARITY_STATES:
                    errors.append(f"baseline_fairness.rows[{index}].comparability.{field}.status: invalid")
                if not nonempty_string(item.get("evidence")):
                    errors.append(f"baseline_fairness.rows[{index}].comparability.{field}.evidence: required")
                if item.get("status") == "mismatch_mitigated" and not nonempty_string(item.get("mitigation")):
                    errors.append(f"baseline_fairness.rows[{index}].comparability.{field}.mitigation: required")
        return
    if not nonempty_string(section.get("not_applicable_reason")):
        errors.append("baseline_fairness: rows or not_applicable_reason is required")


def validate_object_strings(
    payload: dict[str, Any], section_name: str, fields: tuple[str, ...], errors: list[str]
) -> None:
    section = payload.get(section_name)
    if not isinstance(section, dict):
        errors.append(f"{section_name}: expected an object")
        return
    for field in fields:
        if not nonempty_string(section.get(field)):
            errors.append(f"{section_name}.{field}: required")


def validate_design(payload: dict[str, Any], errors: list[str]) -> None:
    validate_object_strings(
        payload,
        "design",
        (
            "experimental_unit",
            "replication_unit",
            "assignment",
            "blocking_strategy",
            "primary_estimand",
            "target_effect_or_mde",
            "variance_basis",
            "sample_size_or_seed_plan",
            "analysis_plan",
            "multiplicity_policy",
            "missing_data_policy",
        ),
        errors,
    )
    section = payload.get("design")
    if isinstance(section, dict):
        for legacy in ("holdout_policy", "holdout_access", "interim_look_policy"):
            if legacy in section:
                errors.append(f"design.{legacy}: legacy duplicate semantic field is forbidden")
        nuisance = section.get("nuisance_factors")
        if not isinstance(nuisance, list) or not nuisance or not all(nonempty_string(item) for item in nuisance):
            errors.append("design.nuisance_factors: expected a non-empty list of non-placeholder strings")
        holdout = section.get("holdout")
        if not isinstance(holdout, dict):
            errors.append("design.holdout: expected an object")
        else:
            if holdout.get("access") not in {"sealed", "final_evaluation_only"}:
                errors.append("design.holdout.access: expected sealed or final_evaluation_only")
            if holdout.get("tuning_access") is not False:
                errors.append("design.holdout.tuning_access: must be false")
            for field in ("evidence", "unsealing_authority"):
                if not nonempty_string(holdout.get(field)):
                    errors.append(f"design.holdout.{field}: required")
        sequential = section.get("sequential_analysis")
        if not isinstance(sequential, dict):
            errors.append("design.sequential_analysis: expected an object")
        else:
            if sequential.get("optional_stopping_allowed") is not False:
                errors.append("design.sequential_analysis.optional_stopping_allowed: must be false")
            registered_looks = sequential.get("registered_max_looks")
            if not isinstance(registered_looks, int) or isinstance(registered_looks, bool) or registered_looks < 0:
                errors.append("design.sequential_analysis.registered_max_looks: expected a non-negative integer")
            if not nonempty_string(sequential.get("evidence")):
                errors.append("design.sequential_analysis.evidence: required")


def validate_oracle_attack(payload: dict[str, Any], errors: list[str]) -> None:
    section = payload.get("oracle_attack")
    rows = section.get("rows") if isinstance(section, dict) else None
    if not isinstance(rows, list) or not rows:
        errors.append("oracle_attack.rows: expected a non-empty list")
        return
    for legacy in ("oracle_independent", "shared_path_analysis"):
        if legacy in section:
            errors.append(f"oracle_attack.{legacy}: legacy duplicate semantic field is forbidden")
    independence = section.get("independence")
    if not isinstance(independence, dict):
        errors.append("oracle_attack.independence: expected an object")
    else:
        if independence.get("independent") is not True:
            errors.append("oracle_attack.independence.independent: must be true")
        if independence.get("shared_implementation_path") is not False:
            errors.append("oracle_attack.independence.shared_implementation_path: must be false")
        if not nonempty_string(independence.get("evidence")):
            errors.append("oracle_attack.independence.evidence: required")
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not nonempty_string(row.get("risk")) or not nonempty_string(row.get("detection")):
            errors.append(f"oracle_attack.rows[{index}]: risk and detection are required")
            continue
        if row.get("control_type") not in {"detection", "negative_control", "both"}:
            errors.append(f"oracle_attack.rows[{index}].control_type: invalid")


def validate_budget(payload: dict[str, Any], errors: list[str]) -> None:
    section = payload.get("budget")
    if not isinstance(section, dict):
        errors.append("budget: expected an object")
        return
    limits = section.get("limits")
    if not isinstance(limits, dict) or not limits:
        errors.append("budget.limits: expected at least one resource limit")
    else:
        for key, value in limits.items():
            if (
                not nonempty_string(key)
                or not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value <= 0
            ):
                errors.append(f"budget.limits.{key}: expected a positive number")
    if not nonempty_string(section.get("stop_rule")):
        errors.append("budget.stop_rule: required")


def validate_conditions(section: dict[str, Any], key: str, errors: list[str]) -> None:
    rows = section.get(key)
    if not isinstance(rows, list) or not rows:
        errors.append(f"pilot_scale.{key}: expected a non-empty list")
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"pilot_scale.{key}[{index}]: expected an object")
            continue
        for field in ("id", "measure", "operator"):
            if not nonempty_string(row.get(field)):
                errors.append(f"pilot_scale.{key}[{index}].{field}: required")
        operator = row.get("operator")
        if operator not in {">=", "<=", "==", "in", "not_in"}:
            errors.append(f"pilot_scale.{key}[{index}].operator: invalid")
        threshold = row.get("threshold")
        scalar_threshold = nonempty_string(threshold) or (
            isinstance(threshold, (int, float))
            and not isinstance(threshold, bool)
            and math.isfinite(threshold)
        )
        collection_threshold = (
            operator in {"in", "not_in"}
            and isinstance(threshold, list)
            and bool(threshold)
            and all(
                nonempty_string(item)
                or (
                    isinstance(item, (int, float))
                    and not isinstance(item, bool)
                    and math.isfinite(item)
                )
                for item in threshold
            )
        )
        if not (scalar_threshold or collection_threshold):
            errors.append(f"pilot_scale.{key}[{index}].threshold: required finite number or non-placeholder string")
        if operator in {">=", "<="} and not (
            isinstance(threshold, (int, float))
            and not isinstance(threshold, bool)
            and math.isfinite(threshold)
        ):
            errors.append(f"pilot_scale.{key}[{index}].threshold: numeric comparison requires a finite number")
        if operator in {"in", "not_in"} and not collection_threshold:
            errors.append(f"pilot_scale.{key}[{index}].threshold: membership comparison requires a non-empty list")


def condition_holds(condition: dict[str, Any], observed: Any) -> bool | None:
    operator = condition.get("operator")
    threshold = condition.get("threshold")
    if operator in {">=", "<="}:
        if not (
            isinstance(observed, (int, float))
            and not isinstance(observed, bool)
            and math.isfinite(observed)
            and isinstance(threshold, (int, float))
            and not isinstance(threshold, bool)
            and math.isfinite(threshold)
        ):
            return None
        return observed >= threshold if operator == ">=" else observed <= threshold
    if operator == "==":
        if isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
            if not (
                isinstance(observed, (int, float))
                and not isinstance(observed, bool)
                and math.isfinite(observed)
            ):
                return None
            return observed == threshold
        if isinstance(threshold, str):
            if not isinstance(observed, str):
                return None
            return observed == threshold
        if type(observed) is not type(threshold):
            return None
        return observed == threshold
    if operator in {"in", "not_in"} and isinstance(threshold, list):
        if isinstance(observed, bool):
            return None
        result = any(
            observed == candidate
            and (
                type(observed) is type(candidate)
                or (
                    isinstance(observed, (int, float))
                    and not isinstance(observed, bool)
                    and isinstance(candidate, (int, float))
                    and not isinstance(candidate, bool)
                )
            )
            for candidate in threshold
        )
        return result if operator == "in" else not result
    return None


def validate_review_plan(payload: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    rows = payload.get("review_plan")
    if not isinstance(rows, list) or not rows:
        errors.append("review_plan: expected at least one preregistered reviewer")
        return {}
    planned: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        label = f"review_plan[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: expected an object")
            continue
        for field in ("reviewer_id", "reviewer_type"):
            if not nonempty_string(row.get(field)):
                errors.append(f"{label}.{field}: required")
        reviewer_id = str(row.get("reviewer_id") or "").strip()
        reviewer_type = str(row.get("reviewer_type") or "").strip()
        if reviewer_type not in REVIEWER_TYPES:
            errors.append(f"{label}.reviewer_type: invalid")
        if reviewer_id in planned:
            errors.append(f"{label}.reviewer_id: duplicate {reviewer_id!r}")
        elif reviewer_id:
            planned[reviewer_id] = row
        if reviewer_type == "internal_blind_gpt":
            for field in ("reviewer_context_id", "reviewer_model"):
                if not nonempty_string(row.get(field)):
                    errors.append(f"{label}.{field}: required for internal GPT review")
            if str(row.get("reviewer_context_id") or "").strip() == str(
                payload.get("controller_context_id") or ""
            ).strip():
                errors.append(f"{label}: reviewer context must differ from controller context")
            if row.get("reviewer_model") not in ALLOWED_GPT_MODELS:
                errors.append(f"{label}.reviewer_model: model is not in the allowed GPT/Codex set")
    return planned


def validate_pilot_evidence(
    payload: dict[str, Any],
    section: dict[str, Any],
    ready: bool,
    artifact_path: Path,
    errors: list[str],
) -> None:
    if not nonempty_string(section.get("pilot_evidence")):
        errors.append("pilot_scale.pilot_evidence: required for pre_scale")
        return
    validate_hashed_file(
        section,
        "pilot_evidence",
        "pilot_evidence_hash",
        artifact_path,
        errors,
    )
    evidence_path = resolve_reference(section.get("pilot_evidence"), artifact_path)
    if evidence_path is None or not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        return
    evidence = load_json_object(evidence_path, "pilot_scale.pilot_evidence", errors)
    if evidence is None:
        return
    expected = {
        "schema_version": 1,
        "proposal_id": payload.get("proposal_id"),
        "proposal_hash": payload.get("proposal_hash"),
        "checkpoint": "pre_scale",
        "pilot_plan_hash": pilot_plan_hash(section),
    }
    for field, value in expected.items():
        if evidence.get(field) != value:
            errors.append(f"pilot_scale.pilot_evidence.{field}: stale or mismatched")

    conditions: dict[str, tuple[str, dict[str, Any]]] = {}
    for group in ("pilot_pass_conditions", "scale_conditions", "kill_conditions"):
        rows = section.get(group)
        if not isinstance(rows, list):
            continue
        for index, condition in enumerate(rows):
            if not isinstance(condition, dict) or not nonempty_string(condition.get("id")):
                continue
            condition_id = str(condition["id"]).strip()
            if condition_id in conditions:
                errors.append(f"pilot_scale.{group}[{index}].id: duplicate condition id {condition_id!r}")
            else:
                conditions[condition_id] = (group, condition)

    results = evidence.get("condition_results")
    if not isinstance(results, list) or not results:
        errors.append("pilot_scale.pilot_evidence.condition_results: expected a non-empty list")
        return
    observed_by_id: dict[str, Any] = {}
    for index, result in enumerate(results):
        label = f"pilot_scale.pilot_evidence.condition_results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{label}: expected an object")
            continue
        condition_id = result.get("condition_id")
        if not nonempty_string(condition_id):
            errors.append(f"{label}.condition_id: required")
            continue
        condition_id = str(condition_id).strip()
        if condition_id in observed_by_id:
            errors.append(f"{label}.condition_id: duplicate result {condition_id!r}")
            continue
        if "observed" not in result:
            errors.append(f"{label}.observed: required")
            continue
        observed = result["observed"]
        if isinstance(observed, float) and not math.isfinite(observed):
            errors.append(f"{label}.observed: must be finite")
            continue
        if not isinstance(observed, (str, int, float, bool)):
            errors.append(f"{label}.observed: expected a scalar JSON value")
            continue
        if isinstance(observed, str) and not nonempty_string(observed):
            errors.append(f"{label}.observed: expected a non-placeholder string")
            continue
        for field in ("source_artifact", "source_hash", "source_json_pointer"):
            if not nonempty_string(result.get(field)):
                errors.append(f"{label}.{field}: required")
        validate_hashed_file(
            result,
            "source_artifact",
            "source_hash",
            evidence_path.resolve(),
            errors,
        )
        source_path = resolve_reference(result.get("source_artifact"), evidence_path.resolve())
        if source_path is not None and source_path.is_file() and source_path.stat().st_size > 0:
            source_value = load_json_value(source_path, f"{label}.source_artifact", errors)
            if source_value is not MISSING:
                pointed_value = resolve_json_pointer(source_value, result.get("source_json_pointer"))
                if pointed_value is MISSING:
                    errors.append(f"{label}.source_json_pointer: does not resolve")
                elif not strict_scalar_equal(observed, pointed_value):
                    errors.append(f"{label}.observed: does not match the bound source value")
        observed_by_id[condition_id] = observed

    missing = sorted(set(conditions) - set(observed_by_id))
    extra = sorted(set(observed_by_id) - set(conditions))
    if missing:
        errors.append(f"pilot_scale.pilot_evidence.condition_results: missing condition ids {missing}")
    if extra:
        errors.append(f"pilot_scale.pilot_evidence.condition_results: unknown condition ids {extra}")

    for condition_id, (group, condition) in conditions.items():
        if condition_id not in observed_by_id:
            continue
        holds = condition_holds(condition, observed_by_id[condition_id])
        if holds is None:
            errors.append(
                f"pilot_scale.pilot_evidence.condition_results[{condition_id!r}]: observed value is incompatible with operator"
            )
        elif ready and group in {"pilot_pass_conditions", "scale_conditions"} and not holds:
            errors.append(f"pilot_scale.{group}[{condition_id!r}]: ready status requires this condition to pass")
        elif ready and group == "kill_conditions" and holds:
            errors.append(f"pilot_scale.kill_conditions[{condition_id!r}]: ready status is forbidden when kill condition triggers")


def validate_reviews(
    payload: dict[str, Any], ready: bool, artifact_path: Path, errors: list[str]
) -> None:
    planned = validate_review_plan(payload, errors)
    rows = payload.get("reviews")
    if not isinstance(rows, list) or not rows:
        errors.append("reviews: expected at least one review")
        return
    passed_internal = False
    seen_reviewers: set[str] = set()
    expected_core_hash = grill_core_hash(payload)
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"reviews[{index}]: expected an object")
            continue
        reviewer_type = str(row.get("reviewer_type") or "")
        reviewer_id = str(row.get("reviewer_id") or "").strip()
        if reviewer_id in seen_reviewers:
            errors.append(f"reviews[{index}].reviewer_id: duplicate {reviewer_id!r}")
        elif reviewer_id:
            seen_reviewers.add(reviewer_id)
        plan_row = planned.get(reviewer_id)
        if plan_row is None:
            errors.append(f"reviews[{index}].reviewer_id: reviewer is not preregistered")
        else:
            for field in ("reviewer_type", "reviewer_context_id", "reviewer_model"):
                if plan_row.get(field) != row.get(field):
                    errors.append(f"reviews[{index}].{field}: differs from preregistered review plan")
        if reviewer_type not in REVIEWER_TYPES:
            errors.append(f"reviews[{index}].reviewer_type: invalid or self-asserted external type")
        for field in ("reviewer_id", "artifact", "artifact_hash", "status"):
            if not nonempty_string(row.get(field)):
                errors.append(f"reviews[{index}].{field}: required")
        if row.get("status") not in {"pass", "blocked"}:
            errors.append(f"reviews[{index}].status: expected pass or blocked")
        packet = {
            "input_artifact": row.get("input_artifact"),
            "input_hash": row.get("input_hash"),
        }
        validate_hashed_file(packet, "input_artifact", "input_hash", artifact_path, errors)
        packet_path = resolve_reference(row.get("input_artifact"), artifact_path)
        review_path = resolve_reference(row.get("artifact"), artifact_path)
        validate_hashed_file(row, "artifact", "artifact_hash", artifact_path, errors)
        if packet_path is not None and review_path is not None and packet_path.resolve() == review_path.resolve():
            errors.append(f"reviews[{index}]: input and review artifact must be distinct files")

        packet_payload = None
        if packet_path is not None and packet_path.is_file() and packet_path.stat().st_size > 0:
            packet_payload = load_json_object(packet_path, f"reviews[{index}].input_artifact", errors)
        elif packet_path is not None and packet_path.is_file():
            errors.append(f"reviews[{index}].input_artifact: packet is empty")
        if packet_payload is not None:
            expected_packet = {
                "schema_version": 1,
                "proposal_id": payload.get("proposal_id"),
                "proposal_hash": payload.get("proposal_hash"),
                "checkpoint": payload.get("checkpoint"),
                "grill_core_hash": expected_core_hash,
            }
            for field, expected in expected_packet.items():
                if packet_payload.get(field) != expected:
                    errors.append(f"reviews[{index}].input_artifact.{field}: stale or mismatched")

        review_payload = None
        if review_path is not None and review_path.is_file() and review_path.stat().st_size > 0:
            review_payload = load_json_object(review_path, f"reviews[{index}].artifact", errors)
        elif review_path is not None and review_path.is_file():
            errors.append(f"reviews[{index}].artifact: review artifact is empty")
        if reviewer_type == "internal_blind_gpt":
            for field in ("reviewer_context_id", "reviewer_model"):
                if not nonempty_string(row.get(field)):
                    errors.append(f"reviews[{index}].{field}: required for internal GPT review")
            reviewer_context = str(row.get("reviewer_context_id") or "").strip()
            controller_context = str(payload.get("controller_context_id") or "").strip()
            if reviewer_context == controller_context:
                errors.append(f"reviews[{index}]: reviewer context must differ from controller context")
            reviewer_model = str(row.get("reviewer_model") or "").strip().lower()
            if reviewer_model and reviewer_model not in ALLOWED_GPT_MODELS:
                errors.append(f"reviews[{index}].reviewer_model: model is not in the allowed GPT/Codex set")
        elif reviewer_type in {"human_domain_reviewer", "external_human_reviewer"}:
            if not nonempty_string(row.get("evidence_source")):
                errors.append(f"reviews[{index}].evidence_source: required for human review")
        if review_payload is not None:
            expected_review = {
                "schema_version": 1,
                "reviewer_type": reviewer_type,
                "reviewer_id": row.get("reviewer_id"),
                "input_hash": row.get("input_hash"),
                "proposal_hash": payload.get("proposal_hash"),
                "grill_core_hash": expected_core_hash,
                "verdict": row.get("status"),
            }
            if reviewer_type == "internal_blind_gpt":
                expected_review["reviewer_context_id"] = row.get("reviewer_context_id")
                expected_review["reviewer_model"] = row.get("reviewer_model")
            for field, expected in expected_review.items():
                if review_payload.get(field) != expected:
                    errors.append(f"reviews[{index}].artifact.{field}: stale, contradictory, or mismatched")
            findings = review_payload.get("findings")
            if not isinstance(findings, list):
                errors.append(f"reviews[{index}].artifact.findings: expected a list")
            else:
                for finding_index, finding in enumerate(findings):
                    label = f"reviews[{index}].artifact.findings[{finding_index}]"
                    if not isinstance(finding, dict):
                        errors.append(f"{label}: expected an object")
                        continue
                    for field in ("id", "severity", "status", "summary"):
                        if not nonempty_string(finding.get(field)):
                            errors.append(f"{label}.{field}: required")
                    severity = str(finding.get("severity") or "").strip().lower()
                    finding_status = str(finding.get("status") or "").strip().lower()
                    if severity not in FINDING_SEVERITIES:
                        errors.append(f"{label}.severity: invalid")
                    if finding_status not in {"open", "resolved"}:
                        errors.append(f"{label}.status: expected open or resolved")
                    if ready and severity in BLOCKING_SEVERITIES and finding_status != "resolved":
                        errors.append(f"{label}: ready contract contains an unresolved blocking finding")
        if ready and row.get("status") == "blocked":
            errors.append(f"reviews[{index}]: ready contract contains a blocked current review")
        if reviewer_type == "internal_blind_gpt" and row.get("status") == "pass":
            passed_internal = True
    if ready and not passed_internal:
        errors.append("reviews: ready status requires a passing internal_blind_gpt review")
    missing_reviewers = sorted(set(planned) - seen_reviewers)
    if missing_reviewers:
        errors.append(f"reviews: missing preregistered reviewers {missing_reviewers}")


def validate_v1(
    payload: dict[str, Any], artifact_path: Path, required_checkpoint: str | None = None
) -> tuple[list[str], bool]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version: expected 1")
    for key in ("proposal_id", "proposal_source", "proposal_hash", "controller_context_id"):
        require_string(payload, key, errors)
    validate_hashed_file(payload, "proposal_source", "proposal_hash", artifact_path, errors)
    checkpoint = payload.get("checkpoint")
    if checkpoint not in CHECKPOINTS:
        errors.append("checkpoint: expected pre_implementation or pre_scale")
    if required_checkpoint is not None and checkpoint != required_checkpoint:
        errors.append(f"checkpoint: action requires {required_checkpoint}")
    status = payload.get("status")
    if status not in READY_STATUSES | {"blocked"}:
        errors.append("status: expected blocked, implementation_ready, or scale_ready")
    if checkpoint == "pre_implementation" and status == "scale_ready":
        errors.append("status: scale_ready is invalid for pre_implementation")
    if checkpoint == "pre_scale" and status == "implementation_ready":
        errors.append("status: implementation_ready is invalid for pre_scale")
    ready = status in READY_STATUSES

    claim_ids = validate_claims(payload, errors)
    require_string_list(payload, "non_goals", errors)
    validate_ambiguities(payload, ready, artifact_path, errors)
    validate_claim_matrix(payload, claim_ids, errors)
    validate_baselines(payload, errors)
    validate_design(payload, errors)
    validate_oracle_attack(payload, errors)
    pilot_scale = payload.get("pilot_scale")
    if not isinstance(pilot_scale, dict):
        errors.append("pilot_scale: expected an object")
    else:
        for legacy in (
            "pilot_pass_criteria",
            "scale_gate",
            "kill_criteria",
            "interim_look_policy",
            "stop_rule",
            "scale_requires_all_criteria",
            "stop_on_failure",
        ):
            if legacy in pilot_scale:
                errors.append(f"pilot_scale.{legacy}: legacy duplicate semantic field is forbidden")
        for key in ("pilot_pass_conditions", "scale_conditions", "kill_conditions"):
            validate_conditions(pilot_scale, key, errors)
        if pilot_scale.get("scale_requires_all_conditions") is not True:
            errors.append("pilot_scale.scale_requires_all_conditions: must be true")
        if pilot_scale.get("stop_on_any_kill") is not True:
            errors.append("pilot_scale.stop_on_any_kill: must be true")
        looks = pilot_scale.get("max_interim_looks")
        if not isinstance(looks, int) or isinstance(looks, bool) or looks < 0:
            errors.append("pilot_scale.max_interim_looks: expected a non-negative integer")
        schedule = pilot_scale.get("interim_look_schedule")
        if not isinstance(schedule, list) or not all(nonempty_string(item) for item in schedule):
            errors.append("pilot_scale.interim_look_schedule: expected a list of non-placeholder strings")
        elif isinstance(looks, int) and not isinstance(looks, bool) and len(schedule) != looks:
            errors.append("pilot_scale.interim_look_schedule: length must equal max_interim_looks")
        design = payload.get("design")
        sequential = design.get("sequential_analysis") if isinstance(design, dict) else None
        if isinstance(sequential, dict) and sequential.get("registered_max_looks") != looks:
            errors.append("pilot_scale.max_interim_looks: must match design.sequential_analysis.registered_max_looks")
    if checkpoint == "pre_scale" and isinstance(pilot_scale, dict):
        validate_pilot_evidence(payload, pilot_scale, ready, artifact_path, errors)
    validate_object_strings(
        payload,
        "reproducibility",
        ("env_lock", "code_ref_policy", "data_ref_policy", "manifest_path"),
        errors,
    )
    validate_budget(payload, errors)
    validate_reviews(payload, ready, artifact_path, errors)

    gates = payload.get("unresolved_human_gates")
    if not isinstance(gates, list):
        errors.append("unresolved_human_gates: expected a list")
    elif ready and gates:
        errors.append("unresolved_human_gates: ready status requires an empty list")
    return errors, ready


# V2 action-scoped authorization implementation.

V2_STAGES = ("code_readiness", "static_acquisition", "human_oracle", "phase0_launch")
V2_ACTIONS = ("static_acquisition", "human_oracle", "phase0_launch", "scale_launch")
V2_STAGE_INDEX = {stage: index for index, stage in enumerate(V2_STAGES)} | {"scale_launch": 4}
V2_STAGE_DEPENDENCIES = {
    "code_readiness": [],
    "static_acquisition": ["code_readiness"],
    "human_oracle": ["static_acquisition"],
    "phase0_launch": ["human_oracle"],
}
V2_ACTION_PREFIX = {
    "static_acquisition": ["code_readiness"],
    "human_oracle": ["code_readiness", "static_acquisition"],
    "phase0_launch": ["code_readiness", "static_acquisition", "human_oracle"],
    "scale_launch": list(V2_STAGES),
}
V2_STAGE_EVIDENCE = {
    "code_readiness": "synthetic_test",
    "static_acquisition": "static_production",
    "human_oracle": "human_oracle",
    "phase0_launch": "phase0_production",
}
V2_KIND_STAGE = {
    "code_test": "code_readiness",
    "public_source": "static_acquisition",
    "license": "static_acquisition",
    "registry": "static_acquisition",
    "raw_input": "static_acquisition",
    "blinded_audit_bundle": "static_acquisition",
    "human_labels": "human_oracle",
    "human_derivation": "human_oracle",
    "human_decision": "human_oracle",
    "clean_reproduction": "human_oracle",
    "capability_evidence": "human_oracle",
    "phase0_raw_result": "phase0_launch",
    "phase0_result": "phase0_launch",
}
V2_KIND_ROLE = {
    "public_source": "acquisition_attestor",
    "license": "acquisition_attestor",
    "registry": "acquisition_attestor",
    "raw_input": "acquisition_attestor",
    "blinded_audit_bundle": "acquisition_attestor",
    "human_labels": "human_oracle",
    "human_derivation": "human_oracle",
    "human_decision": "human_oracle",
    "clean_reproduction": "runtime_attestor",
    "capability_evidence": "runtime_attestor",
    "phase0_raw_result": "runtime_attestor",
    "phase0_result": "runtime_attestor",
}
V2_KIND_ACTION = {
    "public_source": "human_oracle",
    "license": "human_oracle",
    "registry": "human_oracle",
    "raw_input": "human_oracle",
    "blinded_audit_bundle": "human_oracle",
    "human_labels": "phase0_launch",
    "human_derivation": "phase0_launch",
    "clean_reproduction": "phase0_launch",
    "capability_evidence": "phase0_launch",
    "phase0_raw_result": "scale_launch",
    "phase0_result": "scale_launch",
}
V2_ATTESTATION_NAMESPACE = "research-execution-grill-v3"
V3_LINEAGE_NAMESPACE = "research-execution-grill-v3-lineage"
V3_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
V2_RUNTIME_KINDS = {"clean_reproduction", "capability_evidence", "phase0_raw_result", "phase0_result"}
V2_MANIFEST_EXCLUDED_KINDS = V2_RUNTIME_KINDS
V2_CAPABILITIES = (
    "luna_available",
    "terra_available",
    "thread_capacity_available",
    "reviewer_available",
    "runtime_available",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected an object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(f"{label}: keys must be exactly {sorted(expected)}")
        return False
    return True


def v2_core_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """The one immutable projection reviewed for every requested action."""
    fields = (
        "schema_version", "protocol_version", "proposal_id", "proposal_source",
        "proposal_hash", "checkpoint", "lineage_id", "checkpoint_generation",
        "claims", "non_goals", "ambiguities", "claim_experiment_matrix",
        "baseline_fairness", "design", "oracle_attack", "reproducibility",
        "stage_dependencies", "action_contracts", "review_plan", "review_plan_hash",
        "phase0_requirements", "budget", "pilot_scale", "unresolved_human_gates",
    )
    projection = {field: copy.deepcopy(payload.get(field)) for field in fields}
    projection["stages"] = [
        {
            "id": row.get("id"),
            "required_artifacts": copy.deepcopy(row.get("required_artifacts")),
            "provided_artifacts": copy.deepcopy(row.get("provided_artifacts")),
        }
        for row in payload.get("stages", []) if isinstance(row, dict)
    ]
    projection["artifacts"] = [
        {
            key: copy.deepcopy(row.get(key))
            for key in (
                "id", "kind", "evidence_class", "producer_stage", "consumer_stage",
                "consumes", "provides", "attested_action", "signer_identity",
            )
        }
        for row in payload.get("artifacts", []) if isinstance(row, dict)
    ]
    return projection


def v2_core_hash(payload: dict[str, Any]) -> str:
    return canonical_sha256(v2_core_projection(payload))


def v2_evidence_manifest(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": row.get("id"),
            "kind": row.get("kind"),
            "source_sha256": row.get("source_sha256"),
            "semantic_sha256": row.get("semantic_sha256"),
            "consumes": copy.deepcopy(row.get("consumes")),
        }
        for row in payload.get("artifacts", [])
        if isinstance(row, dict) and row.get("kind") not in V2_MANIFEST_EXCLUDED_KINDS
    ]


def v2_evidence_manifest_hash(payload: dict[str, Any]) -> str:
    return canonical_sha256(v2_evidence_manifest(payload))


def resolve_cli_path(value: str | Path | None, base: Path) -> Path | None:
    if value is None or not str(value).strip():
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else base.parent / path


def load_trust_policy(
    path_value: Path | None,
    pinned_hash: str | None,
    artifact_path: Path,
    operational: list[str],
) -> tuple[dict[str, set[str]], dict[str, str]]:
    path = resolve_cli_path(path_value, artifact_path)
    if path is None or not nonempty_string(pinned_hash):
        operational.append("trust_policy: path and externally pinned canonical SHA-256 are required")
        return {}, {}
    policy = load_json_object(path, "trust_policy", operational) if path.is_file() else None
    if policy is None:
        if not path.is_file():
            operational.append(f"trust_policy: file does not exist: {path}")
        return {}, {}
    if canonical_sha256(policy) != pinned_hash:
        operational.append("trust_policy: external canonical SHA-256 pin mismatch")
    if policy.get("schema_version") != 1 or policy.get("protocol_version") != PROTOCOL_VERSION:
        operational.append("trust_policy: schema/protocol mismatch")
    if policy.get("namespace") != V2_ATTESTATION_NAMESPACE:
        operational.append("trust_policy: namespace mismatch")
    roles: dict[str, set[str]] = {}
    keys: dict[str, str] = {}
    identities = policy.get("identities")
    if not isinstance(identities, list) or not identities:
        operational.append("trust_policy.identities: expected a non-empty list")
        return roles, keys
    for index, row in enumerate(identities):
        label = f"trust_policy.identities[{index}]"
        if not isinstance(row, dict) or not nonempty_string(row.get("identity")):
            operational.append(f"{label}: identity is required")
            continue
        identity = row["identity"]
        role_list = row.get("roles")
        public_key = row.get("public_key")
        if identity in roles:
            operational.append(f"{label}: duplicate identity")
            continue
        if not isinstance(role_list, list) or not role_list or not all(nonempty_string(item) for item in role_list):
            operational.append(f"{label}.roles: expected non-empty roles")
            role_list = []
        if not nonempty_string(public_key) or not public_key.startswith(("ssh-ed25519 ", "ecdsa-sha2-", "ssh-rsa ")):
            operational.append(f"{label}.public_key: unsupported or missing OpenSSH public key")
            public_key = ""
        roles[identity] = set(role_list)
        keys[identity] = public_key
    return roles, keys


def verify_detached_signature(
    payload: dict[str, Any],
    signature_value: Any,
    identity: Any,
    required_role: str,
    roles: dict[str, set[str]],
    keys: dict[str, str],
    artifact_path: Path,
    label: str,
    operational: list[str],
    contract_errors: list[str] | None = None,
    namespace: str = V2_ATTESTATION_NAMESPACE,
) -> bool:
    if shutil.which("ssh-keygen") is None:
        operational.append(f"{label}: ssh-keygen is unavailable")
        return False
    if not roles and not keys:
        return False
    evidence_errors = contract_errors if contract_errors is not None else operational
    if not nonempty_string(identity) or identity not in roles:
        evidence_errors.append(f"{label}: signer identity is not trusted")
        return False
    if required_role not in roles[identity]:
        evidence_errors.append(f"{label}: signer lacks required role {required_role}")
        return False
    signature_path = resolve_reference(signature_value, artifact_path)
    if signature_path is None or not signature_path.is_file():
        evidence_errors.append(f"{label}: detached signature is missing")
        return False
    with tempfile.NamedTemporaryFile("w", encoding="utf-8") as allowed:
        allowed.write(f"{identity} {keys[identity]}\n")
        allowed.flush()
        result = subprocess.run(
            [
                "ssh-keygen", "-Y", "verify", "-f", allowed.name, "-I", identity,
                "-n", namespace, "-s", str(signature_path),
            ],
            input=canonical_json(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        evidence_errors.append(f"{label}: detached signature verification failed: {detail}")
        return False
    return True


def semantic_source(
    artifact: dict[str, Any], artifact_path: Path, label: str, errors: list[str]
) -> tuple[Path | None, dict[str, Any] | None]:
    source_path = resolve_reference(artifact.get("source_path"), artifact_path)
    if source_path is None or not source_path.is_file():
        errors.append(f"{label}.source_path: external source file is required")
        return None, None
    if sha256_file(source_path) != artifact.get("source_sha256"):
        errors.append(f"{label}.source_sha256: source content hash mismatch")
    source = load_json_object(source_path, f"{label}.source", errors)
    if source is None:
        return source_path, None
    if canonical_sha256(source) != artifact.get("semantic_sha256"):
        errors.append(f"{label}.semantic_sha256: canonical semantic hash mismatch")
    return source_path, source


def validate_v2_source_schema(
    artifact: dict[str, Any], source: dict[str, Any], payload: dict[str, Any],
    artifacts: dict[str, dict[str, Any]], evidence_hash: str, label: str, errors: list[str],
) -> None:
    kind = artifact.get("kind")
    if kind == "code_test":
        exact_keys(source, {"tests_passed", "test_manifest_hash"}, label, errors)
        if source.get("tests_passed") is not True or not nonempty_string(source.get("test_manifest_hash")):
            errors.append(f"{label}: code tests must be passed and manifest-bound")
    elif kind in {"public_source", "license", "raw_input"}:
        exact_keys(source, {"source_id", "uri", "license", "content_sha256"}, label, errors)
        for field in ("source_id", "uri", "license", "content_sha256"):
            if not nonempty_string(source.get(field)):
                errors.append(f"{label}.{field}: required")
    elif kind == "registry":
        exact_keys(source, {"proposal_id", "proposal_hash", "sources"}, label, errors)
        if source.get("proposal_id") != payload.get("proposal_id") or source.get("proposal_hash") != payload.get("proposal_hash"):
            errors.append(f"{label}: registry proposal binding mismatch")
        if not isinstance(source.get("sources"), list):
            errors.append(f"{label}.sources: expected a list")
        else:
            for index, item in enumerate(source["sources"]):
                exact_keys(item, {"source_id", "kind", "source_sha256", "license"}, f"{label}.sources[{index}]", errors)
    elif kind == "blinded_audit_bundle":
        exact_keys(source, {"proposal_id", "proposal_hash", "registry_semantic_sha256", "blinded", "items"}, label, errors)
        if source.get("proposal_id") != payload.get("proposal_id") or source.get("proposal_hash") != payload.get("proposal_hash"):
            errors.append(f"{label}: bundle proposal binding mismatch")
        registry_ids = artifact.get("consumes") or []
        registry_hashes = {artifacts[item].get("semantic_sha256") for item in registry_ids if item in artifacts and artifacts[item].get("kind") == "registry"}
        if source.get("registry_semantic_sha256") not in registry_hashes:
            errors.append(f"{label}.registry_semantic_sha256: bundle is not bound to its consumed registry")
        if source.get("blinded") is not True or not isinstance(source.get("items"), list):
            errors.append(f"{label}: bundle must be blinded with an item list")
        elif isinstance(source.get("items"), list):
            for index, item in enumerate(source["items"]):
                exact_keys(item, {"artifact_id", "semantic_sha256"}, f"{label}.items[{index}]", errors)
    elif kind in {"human_labels", "human_derivation"}:
        value_key = "labels" if kind == "human_labels" else "derivation"
        exact_keys(source, {"proposal_id", "proposal_hash", "bundle_semantic_sha256", "sealed", value_key}, label, errors)
        if source.get("proposal_id") != payload.get("proposal_id") or source.get("proposal_hash") != payload.get("proposal_hash"):
            errors.append(f"{label}: human artifact proposal binding mismatch")
        bundle_hashes = {artifacts[item].get("semantic_sha256") for item in artifact.get("consumes") or [] if item in artifacts and artifacts[item].get("kind") == "blinded_audit_bundle"}
        if source.get("bundle_semantic_sha256") not in bundle_hashes or source.get("sealed") is not True:
            errors.append(f"{label}: human artifact must be sealed and bound to the frozen bundle")
    elif kind == "human_decision":
        exact_keys(source, {"proposal_id", "proposal_hash", "ambiguity_id", "resolution", "approved_by"}, label, errors)
        if source.get("proposal_id") != payload.get("proposal_id") or source.get("proposal_hash") != payload.get("proposal_hash"):
            errors.append(f"{label}: human decision proposal binding mismatch")
        for field in ("ambiguity_id", "resolution", "approved_by"):
            if not nonempty_string(source.get(field)):
                errors.append(f"{label}.{field}: expected a non-empty string")
    elif kind == "clean_reproduction":
        exact_keys(source, {"bundle_semantic_sha256", "evidence_manifest_hash", "manifest_semantic_sha256", "clean"}, label, errors)
        bundle_hashes = {artifacts[item].get("semantic_sha256") for item in artifact.get("consumes") or [] if item in artifacts and artifacts[item].get("kind") == "blinded_audit_bundle"}
        if source.get("bundle_semantic_sha256") not in bundle_hashes:
            errors.append(f"{label}: reproduction bundle binding mismatch")
        if source.get("evidence_manifest_hash") != evidence_hash or source.get("clean") is not True:
            errors.append(f"{label}: reproduction must be clean and bind the exact evidence manifest")
    elif kind == "capability_evidence":
        if exact_keys(source, set(V2_CAPABILITIES), label, errors):
            for name in V2_CAPABILITIES:
                if not isinstance(source.get(name), bool):
                    errors.append(f"{label}.{name}: expected an exact boolean")
    elif kind == "phase0_raw_result":
        exact_keys(source, {"conditions", "bundle_semantic_sha256", "evidence_manifest_hash"}, label, errors)
        if not isinstance(source.get("conditions"), dict):
            errors.append(f"{label}.conditions: expected an object")
        bundle_hashes = {row.get("semantic_sha256") for row in artifacts.values() if row.get("kind") == "blinded_audit_bundle"}
        if source.get("bundle_semantic_sha256") not in bundle_hashes:
            errors.append(f"{label}.bundle_semantic_sha256: phase0 raw result bundle mismatch")
        if source.get("evidence_manifest_hash") != evidence_hash:
            errors.append(f"{label}.evidence_manifest_hash: phase0 raw result manifest mismatch")
    elif kind == "phase0_result":
        exact_keys(
            source,
            {
                "schema_version", "protocol_version", "proposal_id", "proposal_hash",
                "checkpoint", "requested_action", "pilot_plan_hash",
                "bundle_semantic_sha256", "evidence_manifest_hash", "condition_results",
            },
            label,
            errors,
        )


def validate_v2_artifacts(
    payload: dict[str, Any], artifact_path: Path, requested_action: str,
    roles: dict[str, set[str]], keys: dict[str, str], errors: list[str], operational: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], set[str]]:
    rows = payload.get("artifacts")
    if not isinstance(rows, list) or not rows:
        errors.append("artifacts: expected a non-empty external artifact declaration list")
        return {}, {}, set()
    artifacts: dict[str, dict[str, Any]] = {}
    sources: dict[str, dict[str, Any]] = {}
    verified_artifacts: set[str] = set()
    for index, artifact in enumerate(rows):
        label = f"artifacts[{index}]"
        required = {
            "id", "kind", "evidence_class", "producer_stage", "consumer_stage",
            "source_path", "source_sha256", "semantic_sha256", "consumes", "provides",
        }
        if not isinstance(artifact, dict) or not required <= set(artifact):
            errors.append(f"{label}: missing required declaration fields")
            continue
        artifact_id = artifact.get("id")
        if not nonempty_string(artifact_id) or artifact_id in artifacts:
            errors.append(f"{label}.id: missing or duplicate artifact ID")
            continue
        kind = artifact.get("kind")
        producer = artifact.get("producer_stage")
        consumer = artifact.get("consumer_stage")
        if kind not in V2_KIND_STAGE or producer != V2_KIND_STAGE.get(kind):
            errors.append(f"{label}: artifact kind has the wrong producer stage")
        if artifact.get("evidence_class") != V2_STAGE_EVIDENCE.get(producer):
            errors.append(f"{label}.evidence_class: wrong exact evidence class")
        if consumer not in V2_STAGE_INDEX or producer not in V2_STAGE_INDEX or V2_STAGE_INDEX.get(consumer, -1) < V2_STAGE_INDEX.get(producer, -1):
            errors.append(f"{label}.consumer_stage: consumer cannot precede producer")
        for field in ("consumes", "provides"):
            value = artifact.get(field)
            if not isinstance(value, list) or len(value) != len(set(value)) or not all(nonempty_string(item) for item in value):
                errors.append(f"{label}.{field}: expected unique artifact IDs")
        if set(artifact.get("consumes") or []) & set(artifact.get("provides") or []):
            errors.append(f"{label}: consumes/provides overlap")
        artifacts[artifact_id] = artifact
        _path, source = semantic_source(artifact, artifact_path, label, errors)
        if source is not None:
            sources[artifact_id] = source
    evidence_hash = v2_evidence_manifest_hash(payload)
    if payload.get("evidence_manifest_hash") != evidence_hash:
        errors.append("evidence_manifest_hash: canonical evidence declaration mismatch")
    for artifact_id, artifact in artifacts.items():
        label = f"artifacts[{artifact_id}]"
        for dependency_id in artifact.get("consumes") or []:
            dependency = artifacts.get(dependency_id)
            if dependency is None:
                errors.append(f"{label}.consumes: missing reference {dependency_id!r}")
                continue
            if dependency_id == artifact_id:
                errors.append(f"{label}.consumes: self edge is forbidden")
            if V2_STAGE_INDEX.get(dependency.get("producer_stage"), -1) > V2_STAGE_INDEX.get(artifact.get("producer_stage"), -1):
                errors.append(f"{label}.consumes: future-stage dependency is forbidden")
            if artifact_id not in (dependency.get("provides") or []):
                errors.append(f"{label}.consumes: inverse provides edge is missing")
        for provided_id in artifact.get("provides") or []:
            target = artifacts.get(provided_id)
            if target is None:
                errors.append(f"{label}.provides: missing reference {provided_id!r}")
            elif artifact_id not in (target.get("consumes") or []):
                errors.append(f"{label}.provides: inverse consumes edge is missing")
            elif target.get("producer_stage") != artifact.get("consumer_stage"):
                errors.append(f"{label}.consumer_stage: does not match provided artifact producer")
        if artifact_id in sources:
            validate_v2_source_schema(artifact, sources[artifact_id], payload, artifacts, evidence_hash, label, errors)
        role = V2_KIND_ROLE.get(artifact.get("kind"))
        if role is not None:
            provenance_issues = errors
            for field in ("attested_action", "attestation_path", "signature_path", "signer_identity"):
                if not nonempty_string(artifact.get(field)):
                    provenance_issues.append(f"{label}.{field}: signed provenance envelope is required")
            expected_action = V2_KIND_ACTION.get(artifact.get("kind"))
            if expected_action is not None and artifact.get("attested_action") != expected_action:
                provenance_issues.append(f"{label}.attested_action: wrong production action binding")
            if artifact.get("kind") == "human_decision" and artifact.get("attested_action") not in {"phase0_launch", "scale_launch"}:
                errors.append(f"{label}.attested_action: human decision must bind phase0_launch or scale_launch")
            attestation_path = resolve_reference(artifact.get("attestation_path"), artifact_path)
            attestation = load_json_object(attestation_path, f"{label}.attestation", provenance_issues) if attestation_path and attestation_path.is_file() else None
            consumed = [
                {"artifact_id": item, "semantic_sha256": artifacts[item].get("semantic_sha256")}
                for item in artifact.get("consumes") or [] if item in artifacts
            ]
            expected = {
                "schema_version": V3_SCHEMA_VERSION,
                "protocol_version": PROTOCOL_VERSION,
                "proposal_id": payload.get("proposal_id"),
                "proposal_hash": payload.get("proposal_hash"),
                "checkpoint_id": payload.get("checkpoint_id"),
                "lineage_id": payload.get("lineage_id"),
                "requested_action": artifact.get("attested_action"),
                "artifact_id": artifact_id,
                "artifact_kind": artifact.get("kind"),
                "evidence_class": artifact.get("evidence_class"),
                "source_sha256": artifact.get("source_sha256"),
                "semantic_sha256": artifact.get("semantic_sha256"),
                "consumed_artifacts": consumed,
            }
            if attestation != expected:
                provenance_issues.append(f"{label}.attestation: canonical binding mismatch")
            elif verify_detached_signature(
                    attestation, artifact.get("signature_path"), artifact.get("signer_identity"),
                    role, roles, keys, artifact_path, f"{label}.signature", operational,
                    errors,
                ):
                verified_artifacts.add(artifact_id)
    graph = {item: set(row.get("consumes") or []) & set(artifacts) for item, row in artifacts.items()}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"artifacts: dependency cycle includes {node!r}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)
    for artifact_id in graph:
        visit(artifact_id)
    return artifacts, sources, verified_artifacts


def validate_v2_stages(
    payload: dict[str, Any], artifacts: dict[str, dict[str, Any]], requested_action: str, errors: list[str]
) -> tuple[dict[str, dict[str, Any]], bool]:
    rows = payload.get("stages")
    if not isinstance(rows, list) or len(rows) != 4:
        errors.append("stages: expected exactly four bootstrap stages")
        return {}, False
    stages: dict[str, dict[str, Any]] = {}
    seen_nonpassed = False
    for index, row in enumerate(rows):
        label = f"stages[{index}]"
        if not isinstance(row, dict) or row.get("id") != V2_STAGES[index]:
            errors.append(f"{label}: wrong exact stage order")
            continue
        if row.get("status") not in {"pending", "passed", "blocked"}:
            errors.append(f"{label}.status: invalid exact enum")
        if row.get("status") != "passed":
            seen_nonpassed = True
        elif seen_nonpassed:
            errors.append(f"{label}.status: passed stages must form an ordered prefix")
        for field in ("required_artifacts", "provided_artifacts"):
            value = row.get(field)
            if not isinstance(value, list) or len(value) != len(set(value)) or not all(nonempty_string(item) for item in value):
                errors.append(f"{label}.{field}: expected unique artifact IDs")
        if set(row.get("required_artifacts") or []) & set(row.get("provided_artifacts") or []):
            errors.append(f"{label}: required/provided overlap")
        stages[row["id"]] = row
    if payload.get("stage_dependencies") != V2_STAGE_DEPENDENCIES:
        errors.append("stage_dependencies: exact four-stage predecessor map is required")
    expected_contracts = {
        action: {"required_passed_stages": prefix}
        for action, prefix in V2_ACTION_PREFIX.items()
    }
    if payload.get("action_contracts") != expected_contracts:
        errors.append("action_contracts: exact action boundary contracts are required")
    for stage, row in stages.items():
        provided = {item for item, artifact in artifacts.items() if artifact.get("producer_stage") == stage}
        if set(row.get("provided_artifacts") or []) != provided:
            errors.append(f"stages.{stage}.provided_artifacts: must equal producer declarations")
        required = {
            dependency
            for item in provided
            for dependency in artifacts[item].get("consumes") or []
            if artifacts.get(dependency, {}).get("producer_stage") != stage
        }
        if set(row.get("required_artifacts") or []) != required:
            errors.append(f"stages.{stage}.required_artifacts: must equal direct consumed artifacts")
    stage_ready = all(
        stages.get(stage, {}).get("status") == "passed"
        for stage in V2_ACTION_PREFIX[requested_action]
    )
    passed = {stage for stage, row in stages.items() if row.get("status") == "passed"}
    for artifact_id, artifact in artifacts.items():
        if artifact.get("producer_stage") not in passed:
            errors.append(f"artifacts[{artifact_id}]: future-stage artifact exists before producer stage passed")
    return stages, stage_ready


def validate_v2_ambiguities(
    payload: dict[str, Any], artifacts: dict[str, dict[str, Any]], sources: dict[str, dict[str, Any]],
    authorization_action: bool, errors: list[str],
) -> None:
    rows = payload.get("ambiguities")
    if not isinstance(rows, list):
        errors.append("ambiguities: expected a list")
        return
    for index, row in enumerate(rows):
        label = f"ambiguities[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: expected an object")
            continue
        severity = row.get("severity")
        status = row.get("status")
        if severity not in AMBIGUITY_SEVERITIES or status not in {"resolved", "unresolved"}:
            errors.append(f"{label}: malformed severity/status enum")
        for field in ("id", "question", "source"):
            if not nonempty_string(row.get(field)):
                errors.append(f"{label}.{field}: required")
        if status == "resolved" and not nonempty_string(row.get("resolution")):
            errors.append(f"{label}.resolution: required")
        if status == "resolved" and severity in BLOCKING_SEVERITIES:
            authority = row.get("resolution_authority")
            if authority == "proposal_source":
                if not re.match(r"^proposal:\s*\S.*$", str(row.get("source") or "")):
                    errors.append(f"{label}.source: proposal:<locator> is required")
            elif authority == "human_decision":
                artifact_id = row.get("decision_artifact_id")
                artifact = artifacts.get(artifact_id)
                decision = sources.get(artifact_id)
                if artifact is None or artifact.get("kind") != "human_decision" or decision is None:
                    errors.append(f"{label}.decision_artifact_id: signed human decision is required")
                else:
                    expected = {
                        "proposal_id": payload.get("proposal_id"),
                        "proposal_hash": payload.get("proposal_hash"),
                        "ambiguity_id": row.get("id"),
                        "resolution": row.get("resolution"),
                    }
                    for field, value in expected.items():
                        if decision.get(field) != value:
                            errors.append(f"{label}.decision_artifact_id: {field} binding mismatch")
            else:
                errors.append(f"{label}.resolution_authority: authoritative source is required")
        if authorization_action and severity in BLOCKING_SEVERITIES and status != "resolved":
            errors.append(f"{label}: unresolved blocking ambiguity")


def validate_v2_review_lifecycle(
    payload: dict[str, Any], artifact_path: Path, requested_action: str,
    roles: dict[str, set[str]], keys: dict[str, str], core_hash: str,
    evidence_hash: str, errors: list[str], operational: list[str],
) -> tuple[bool, str]:
    plan = payload.get("review_plan")
    if not isinstance(plan, list) or not plan:
        errors.append("review_plan: expected a non-empty frozen plan")
        return False, "initial"
    if payload.get("review_plan_hash") != canonical_sha256(plan):
        errors.append("review_plan_hash: canonical frozen plan mismatch")
    planned: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(plan):
        label = f"review_plan[{index}]"
        required = {"reviewer_id", "signer_identity", "reviewer_type", "reviewer_context_id", "reviewer_model"}
        if not exact_keys(row, required, label, errors):
            continue
        reviewer_id = row.get("reviewer_id")
        if not nonempty_string(reviewer_id) or reviewer_id in planned:
            errors.append(f"{label}.reviewer_id: missing or duplicate")
            continue
        if row.get("reviewer_type") != "internal_blind_gpt" or row.get("reviewer_model") not in ALLOWED_GPT_MODELS:
            errors.append(f"{label}: exact internal GPT reviewer type/model is required")
        if row.get("reviewer_context_id") == payload.get("controller_context_id"):
            errors.append(f"{label}: reviewer context must be independent")
        if row.get("signer_identity") not in roles or "reviewer" not in roles.get(row.get("signer_identity"), set()):
            operational.append(f"{label}.signer_identity: trusted reviewer signer role is required")
        planned[reviewer_id] = row
    history = payload.get("review_history")
    if not isinstance(history, list):
        errors.append("review_history: expected append-only history")
        return False, "initial"
    review_rows: list[dict[str, Any]] = []
    review_records: list[tuple[int, dict[str, Any]]] = []
    corrections: list[tuple[int, dict[str, Any]]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for index, row in enumerate(history):
        label = f"review_history[{index}]"
        if not isinstance(row, dict) or row.get("event") not in {"review", "correction"}:
            errors.append(f"{label}.event: exact review/correction enum required")
            continue
        if row["event"] == "correction":
            exact_keys(row, {"event", "before_core", "after_core", "plan_hash"}, label, errors)
            corrections.append((index, row))
            continue
        phase = row.get("phase")
        exact_keys(
            row,
            {
                "event", "review_id", "reviewer_id", "phase", "core_hash",
                "evidence_manifest_hash", "requested_action", "source_path",
                "source_sha256", "semantic_sha256", "signature_path",
            },
            label,
            errors,
        )
        if phase not in {"initial", "re_review"}:
            errors.append(f"{label}.phase: malformed review phase")
            continue
        identity = (
            str(row.get("requested_action")), str(row.get("core_hash")),
            str(row.get("reviewer_id")), str(phase),
        )
        if identity in seen:
            errors.append(f"{label}: duplicate (requested_action, core_hash, reviewer_id, phase)")
        seen.add(identity)
        review_rows.append(row)
        review_records.append((index, row))
        plan_row = planned.get(row.get("reviewer_id"))
        if plan_row is None:
            errors.append(f"{label}.reviewer_id: reviewer is not in frozen plan")
            continue
        source_path = resolve_reference(row.get("source_path"), artifact_path)
        if source_path is None or not source_path.is_file():
            operational.append(f"{label}.source_path: signed external review is missing")
            continue
        if sha256_file(source_path) != row.get("source_sha256"):
            operational.append(f"{label}.source_sha256: review source hash mismatch")
        review = load_json_object(source_path, f"{label}.source", operational)
        if review is None:
            continue
        if canonical_sha256(review) != row.get("semantic_sha256"):
            operational.append(f"{label}.semantic_sha256: review semantic hash mismatch")
        expected_fields = {
            "schema_version", "protocol_version", "proposal_id", "proposal_hash",
            "reviewer_id", "reviewer_context_id", "reviewer_model", "core_hash",
            "plan_hash", "evidence_manifest_hash", "requested_action", "phase",
            "verdict", "findings",
        }
        exact_keys(review, expected_fields, f"{label}.source", operational)
        bindings = {
            "schema_version": V3_SCHEMA_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "proposal_id": payload.get("proposal_id"),
            "proposal_hash": payload.get("proposal_hash"),
            "reviewer_id": row.get("reviewer_id"),
            "reviewer_context_id": plan_row.get("reviewer_context_id"),
            "reviewer_model": plan_row.get("reviewer_model"),
            "core_hash": row.get("core_hash"),
            "plan_hash": payload.get("review_plan_hash"),
            "evidence_manifest_hash": row.get("evidence_manifest_hash"),
            "requested_action": row.get("requested_action"),
            "phase": phase,
        }
        for field, expected in bindings.items():
            if review.get(field) != expected:
                operational.append(f"{label}.source.{field}: stale or mismatched binding")
        if review.get("verdict") not in {"pass", "blocked"}:
            errors.append(f"{label}.source.verdict: malformed exact enum")
        findings = review.get("findings")
        if not isinstance(findings, list):
            errors.append(f"{label}.source.findings: expected a list")
        else:
            for finding_index, finding in enumerate(findings):
                finding_label = f"{label}.source.findings[{finding_index}]"
                if not exact_keys(finding, {"id", "severity", "status", "summary"}, finding_label, errors):
                    continue
                if finding.get("severity") not in FINDING_SEVERITIES or finding.get("status") not in {"open", "resolved"}:
                    errors.append(f"{finding_label}: malformed exact enum")
        verify_detached_signature(
            review, row.get("signature_path"), plan_row.get("signer_identity"), "reviewer",
            roles, keys, artifact_path, f"{label}.signature", operational,
        )
    expected_reviewers = set(planned)
    grouped_reviews: dict[tuple[str, str, str], list[tuple[int, dict[str, Any]]]] = {}
    for index, row in review_records:
        group = (str(row.get("requested_action")), str(row.get("core_hash")), str(row.get("phase")))
        grouped_reviews.setdefault(group, []).append((index, row))
    for (action, grouped_core, phase), rows in grouped_reviews.items():
        if len(rows) > len(expected_reviewers):
            errors.append(
                f"review_history: at most one complete {phase} cycle is allowed "
                f"for action/core {action}/{grouped_core}"
            )

    correction_scopes: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = {}
    for correction_index, correction in corrections:
        before = correction.get("before_core")
        after = correction.get("after_core")
        if (
            not nonempty_string(before) or not nonempty_string(after)
            or before == after
        ):
            errors.append("review_history.correction: before_core must differ from after_core")
        if correction.get("plan_hash") != payload.get("review_plan_hash"):
            errors.append("review_history.correction: frozen plan hash mismatch")
        initial_actions = {
            str(row.get("requested_action"))
            for _index, row in review_records
            if row.get("phase") == "initial" and row.get("core_hash") == before
        }
        rereview_actions = {
            str(row.get("requested_action"))
            for _index, row in review_records
            if row.get("phase") == "re_review" and row.get("core_hash") == after
        }
        scoped_actions = initial_actions & rereview_actions
        if len(scoped_actions) != 1:
            errors.append("review_history.correction: cannot bind correction to exactly one action/core review cycle")
            continue
        action = next(iter(scoped_actions))
        correction_scopes.setdefault((action, str(after)), []).append((correction_index, correction))
        initial = [
            (index, row) for index, row in review_records
            if row.get("requested_action") == action
            and row.get("phase") == "initial" and row.get("core_hash") == before
        ]
        rereview = [
            (index, row) for index, row in review_records
            if row.get("requested_action") == action
            and row.get("phase") == "re_review" and row.get("core_hash") == after
        ]
        if (
            {row.get("reviewer_id") for _index, row in initial} != expected_reviewers
            or len(initial) != len(expected_reviewers)
        ):
            errors.append("review_history.correction: complete signed initial review cycle is required")
        if (
            {row.get("reviewer_id") for _index, row in rereview} != expected_reviewers
            or len(rereview) != len(expected_reviewers)
        ):
            errors.append("review_history.correction: complete signed re-review cycle is required")
        if initial and rereview and not (
            max(index for index, _row in initial) < correction_index
            < min(index for index, _row in rereview)
        ):
            errors.append("review_history.correction: must append after initial review and before re-review")
    for (action, scoped_core), scoped_corrections in correction_scopes.items():
        if len(scoped_corrections) > 1:
            errors.append(
                "review_history: at most one consolidated correction is allowed "
                f"for action/core {action}/{scoped_core}"
            )
    for action, grouped_core, phase in grouped_reviews:
        if phase == "re_review" and (action, grouped_core) not in correction_scopes:
            errors.append(
                "review_history: re-review requires the scoped consolidated correction "
                f"for action/core {action}/{grouped_core}"
            )
    current_ids = payload.get("current_review_ids")
    if not isinstance(current_ids, list) or len(current_ids) != len(set(current_ids)):
        errors.append("current_review_ids: expected unique current review IDs")
        current_ids = []
    current = [row for row in review_rows if row.get("review_id") in set(current_ids)]
    current_reviewers = [row.get("reviewer_id") for row in current]
    if set(current_reviewers) != expected_reviewers or len(current_reviewers) != len(expected_reviewers):
        errors.append("current_review_ids: must identify exactly one current signed review for every planned reviewer")
    if len(current_ids) != len(expected_reviewers) or set(current_ids) != {row.get("review_id") for row in current}:
        errors.append("current_review_ids: missing or extra current review ID")
    current_phases = {row.get("phase") for row in current}
    current_phase = next(iter(current_phases)) if len(current_phases) == 1 else "initial"
    if len(current_phases) != 1:
        errors.append("current_review_ids: current reviews must share one exact phase")
    current_corrections = correction_scopes.get((requested_action, core_hash), [])
    if current_phase == "re_review" and len(current_corrections) != 1:
        errors.append("current_review_ids: current re-review requires exactly one scoped correction")
    if current_phase == "initial" and current_corrections:
        errors.append("current_review_ids: initial cycle cannot use a correction for the same action/core")
    for row in current:
        if row.get("phase") != current_phase:
            errors.append("current_review_ids: current phase does not match correction lifecycle")
        if row.get("core_hash") != core_hash or row.get("evidence_manifest_hash") != evidence_hash or row.get("requested_action") != requested_action:
            errors.append("current_review_ids: stale core/plan/evidence-manifest/action binding")
    current_pass = True
    for row in current:
        source_path = resolve_reference(row.get("source_path"), artifact_path)
        review = load_json_object(source_path, "current_review", []) if source_path and source_path.is_file() else None
        if review is None or review.get("verdict") != "pass":
            current_pass = False
        elif any(
            isinstance(finding, dict)
            and finding.get("severity") in BLOCKING_SEVERITIES
            and finding.get("status") == "open"
            for finding in review.get("findings", [])
        ):
            current_pass = False
    return current_pass and len(current) == len(expected_reviewers), current_phase


def validate_v2_lineage(
    payload: dict[str, Any], artifact_path: Path, requested_action: str,
    ledger_value: Path | None, tail_pin: str | None, roles: dict[str, set[str]],
    keys: dict[str, str], core_hash: str, evidence_hash: str, review_cycle: str,
    blocked_rereview: bool, errors: list[str], operational: list[str],
) -> bool:
    ledger_path = resolve_cli_path(ledger_value, artifact_path)
    if ledger_path is None or not nonempty_string(tail_pin):
        operational.append("lineage: ledger path and externally pinned tail SHA-256 are required")
        return False
    ledger = load_json_object(ledger_path, "lineage", operational) if ledger_path.is_file() else None
    if ledger is None:
        if not ledger_path.is_file():
            operational.append(f"lineage: ledger does not exist: {ledger_path}")
        return False
    entries = ledger.get("entries")
    if ledger.get("schema_version") != 1 or not isinstance(entries, list) or not entries:
        operational.append("lineage: schema_version 1 and non-empty entries are required")
        return False
    previous: str | None = None
    terminal_seen = False
    latest_attestation: dict[str, Any] | None = None
    planned_reviewers = {
        row.get("reviewer_id")
        for row in payload.get("review_plan", [])
        if isinstance(row, dict) and nonempty_string(row.get("reviewer_id"))
    }
    cycle_reviewers: dict[tuple[Any, Any, Any, Any], list[Any]] = {}
    for row in payload.get("review_history", []):
        if not isinstance(row, dict) or row.get("event") != "review":
            continue
        identity = (
            row.get("core_hash"), row.get("phase"), row.get("requested_action"),
            row.get("evidence_manifest_hash"),
        )
        cycle_reviewers.setdefault(identity, []).append(row.get("reviewer_id"))
    review_cycles = {
        identity
        for identity, reviewers in cycle_reviewers.items()
        if set(reviewers) == planned_reviewers and len(reviewers) == len(planned_reviewers)
    }
    for index, entry in enumerate(entries):
        label = f"lineage.entries[{index}]"
        if not isinstance(entry, dict) or entry.get("sequence") != index or entry.get("previous_entry_hash") != previous:
            operational.append(f"{label}: sequence/hash-chain mismatch")
            continue
        attestation_path = resolve_reference(entry.get("attestation_path"), ledger_path.resolve())
        signature_path = resolve_reference(entry.get("signature_path"), ledger_path.resolve())
        attestation = load_json_object(attestation_path, f"{label}.attestation", operational) if attestation_path and attestation_path.is_file() else None
        if attestation is None:
            operational.append(f"{label}: signed attestation is missing")
            continue
        exact_keys(
            attestation,
            {
                "schema_version", "protocol_version", "proposal_id", "proposal_hash",
                "checkpoint", "lineage_id", "core_hash", "review_cycle",
                "requested_action", "evidence_manifest_hash", "state",
            },
            f"{label}.attestation",
            operational,
        )
        lineage_action = attestation.get("requested_action")
        lineage_checkpoint = "pre_scale" if lineage_action == "scale_launch" else "pre_implementation"
        for field, expected_value in {
            "schema_version": 2,
            "protocol_version": PROTOCOL_VERSION,
            "proposal_id": payload.get("proposal_id"),
            "proposal_hash": payload.get("proposal_hash"),
            "checkpoint": lineage_checkpoint,
            "lineage_id": payload.get("lineage_id"),
        }.items():
            if attestation.get(field) != expected_value:
                operational.append(f"{label}.attestation.{field}: lineage binding mismatch")
        cycle_identity = (
            attestation.get("core_hash"), attestation.get("review_cycle"),
            attestation.get("requested_action"), attestation.get("evidence_manifest_hash"),
        )
        if cycle_identity not in review_cycles:
            operational.append(f"{label}.attestation: no complete review cycle binding")
        if attestation.get("state") not in {"active", "ARCHITECTURE_RESET_REQUIRED"}:
            operational.append(f"{label}.attestation.state: malformed exact enum")
        if canonical_sha256(attestation) != entry.get("attestation_sha256"):
            operational.append(f"{label}: attestation hash mismatch")
        signature_hash = sha256_file(signature_path) if signature_path and signature_path.is_file() else None
        projection = {
            "sequence": index,
            "previous_entry_hash": previous,
            "attestation_sha256": entry.get("attestation_sha256"),
            "signature_sha256": signature_hash,
            "signer_identity": entry.get("signer_identity"),
        }
        if canonical_sha256(projection) != entry.get("entry_hash"):
            operational.append(f"{label}: entry hash mismatch")
        verify_detached_signature(
            attestation, entry.get("signature_path"), entry.get("signer_identity"),
            "lineage_authority", roles, keys, ledger_path.resolve(), f"{label}.signature", operational,
        )
        if terminal_seen:
            errors.append(f"{label}: schema/protocol v2 cannot append after terminal convergence")
        if attestation.get("state") == "ARCHITECTURE_RESET_REQUIRED":
            terminal_seen = True
        previous = entry.get("entry_hash")
        latest_attestation = attestation
    if previous != tail_pin:
        operational.append("lineage: external tail SHA-256 pin mismatch")
    if latest_attestation is None:
        return False
    expected = {
        "schema_version": V3_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "proposal_id": payload.get("proposal_id"),
        "proposal_hash": payload.get("proposal_hash"),
        "checkpoint": payload.get("checkpoint"),
        "lineage_id": payload.get("lineage_id"),
        "core_hash": core_hash,
        "review_cycle": review_cycle,
        "requested_action": requested_action,
        "evidence_manifest_hash": evidence_hash,
        "state": "ARCHITECTURE_RESET_REQUIRED" if blocked_rereview else "active",
    }
    if latest_attestation != expected:
        operational.append("lineage: latest signed entry does not bind the current artifact/action")
    return not terminal_seen and latest_attestation == expected and previous == tail_pin


def v2_pilot_plan_hash(section: dict[str, Any]) -> str:
    plan = copy.deepcopy(section)
    plan.pop("pilot_evidence_artifact_id", None)
    return canonical_sha256(plan)


def validate_v2_scale(
    payload: dict[str, Any], artifacts: dict[str, dict[str, Any]], sources: dict[str, dict[str, Any]],
    evidence_hash: str, errors: list[str],
) -> None:
    section = payload.get("pilot_scale")
    if not isinstance(section, dict):
        errors.append("pilot_scale: required for scale_launch")
        return
    for key in ("pilot_pass_conditions", "scale_conditions", "kill_conditions"):
        validate_conditions(section, key, errors)
    if section.get("scale_requires_all_conditions") is not True or section.get("stop_on_any_kill") is not True:
        errors.append("pilot_scale: all scale conditions and any-kill stop are mandatory")
    looks = section.get("max_interim_looks")
    schedule = section.get("interim_look_schedule")
    if not isinstance(looks, int) or isinstance(looks, bool) or looks < 0 or not isinstance(schedule, list) or len(schedule) != looks or not all(nonempty_string(item) for item in schedule):
        errors.append("pilot_scale: interim look schedule mismatch")
    sequential = payload.get("design", {}).get("sequential_analysis") if isinstance(payload.get("design"), dict) else None
    if not isinstance(sequential, dict) or sequential.get("registered_max_looks") != looks:
        errors.append("pilot_scale: registered looks mismatch design")
    artifact_id = section.get("pilot_evidence_artifact_id")
    artifact = artifacts.get(artifact_id)
    evidence = sources.get(artifact_id)
    if artifact is None or artifact.get("kind") != "phase0_result" or evidence is None:
        errors.append("pilot_scale.pilot_evidence_artifact_id: signed phase0_result is required")
        return
    expected = {
        "schema_version": V3_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "proposal_id": payload.get("proposal_id"),
        "proposal_hash": payload.get("proposal_hash"),
        "checkpoint": "pre_scale",
        "requested_action": "scale_launch",
        "pilot_plan_hash": v2_pilot_plan_hash(section),
        "evidence_manifest_hash": evidence_hash,
    }
    requirements = payload.get("phase0_requirements")
    bundle = artifacts.get(requirements.get("bundle_artifact_id")) if isinstance(requirements, dict) else None
    designated_bundle_hash = bundle.get("semantic_sha256") if bundle else None
    expected["bundle_semantic_sha256"] = designated_bundle_hash
    for field, value in expected.items():
        if evidence.get(field) != value:
            errors.append(f"pilot_scale.evidence.{field}: stale or mismatched")
    conditions: dict[str, tuple[str, dict[str, Any]]] = {}
    for group in ("pilot_pass_conditions", "scale_conditions", "kill_conditions"):
        for condition in section.get(group, []):
            if isinstance(condition, dict) and nonempty_string(condition.get("id")):
                if condition["id"] in conditions:
                    errors.append(f"pilot_scale.{group}: duplicate condition ID")
                conditions[condition["id"]] = (group, condition)
    results = evidence.get("condition_results")
    if not isinstance(results, list):
        errors.append("pilot_scale.evidence.condition_results: expected a list")
        return
    summarized_bundle_hash = evidence.get("bundle_semantic_sha256")
    consumed_raw_ids = {
        item for item in artifact.get("consumes") or []
        if artifacts.get(item, {}).get("kind") == "phase0_raw_result"
    }
    for raw_id in sorted(consumed_raw_ids):
        raw_source = sources.get(raw_id)
        if raw_source is None:
            continue
        if (
            raw_source.get("bundle_semantic_sha256") != designated_bundle_hash
            or raw_source.get("bundle_semantic_sha256") != summarized_bundle_hash
        ):
            errors.append(
                f"pilot_scale.raw_result.{raw_id}.bundle_semantic_sha256: "
                "must match the exact phase0_requirements bundle and summarized phase0_result"
            )
    observed: dict[str, Any] = {}
    for index, result in enumerate(results):
        label = f"pilot_scale.evidence.condition_results[{index}]"
        if not isinstance(result, dict) or not exact_keys(result, {"condition_id", "observed", "source_artifact_id", "source_json_pointer"}, label, errors):
            continue
        condition_id = result.get("condition_id")
        if condition_id in observed:
            errors.append(f"{label}.condition_id: duplicate")
            continue
        source_artifact = artifacts.get(result.get("source_artifact_id"))
        source = sources.get(result.get("source_artifact_id"))
        if source_artifact is None or source_artifact.get("kind") != "phase0_raw_result" or source is None:
            errors.append(f"{label}.source_artifact_id: signed raw result is required")
            continue
        if source_artifact.get("id") not in consumed_raw_ids:
            errors.append(f"{label}.source_artifact_id: raw result must be consumed by the summarized phase0_result")
        if (
            source.get("bundle_semantic_sha256") != designated_bundle_hash
            or source.get("bundle_semantic_sha256") != summarized_bundle_hash
        ):
            errors.append(
                f"{label}.source_artifact_id: raw result bundle must match the exact "
                "phase0_requirements bundle and summarized phase0_result"
            )
        pointed = resolve_json_pointer(source, result.get("source_json_pointer"))
        if pointed is MISSING or not strict_scalar_equal(pointed, result.get("observed")):
            errors.append(f"{label}.observed: does not match bound raw result")
        observed[condition_id] = result.get("observed")
    if set(observed) != set(conditions):
        errors.append("pilot_scale.evidence.condition_results: must cover every and only frozen condition")
    for condition_id, (group, condition) in conditions.items():
        if condition_id not in observed:
            continue
        holds = condition_holds(condition, observed[condition_id])
        if holds is None:
            errors.append(f"pilot_scale.{condition_id}: incompatible observation type")
        elif group in {"pilot_pass_conditions", "scale_conditions"} and not holds:
            errors.append(f"pilot_scale.{condition_id}: required condition failed")
        elif group == "kill_conditions" and holds:
            errors.append(f"pilot_scale.{condition_id}: kill condition triggered")


# V3 authoritative event-sourced adapter.  The pure lifecycle reducer lives in
# research_grill_state_machine.py; this section validates external evidence and
# translates signed ledger events into its immutable input objects.

V3_EVENT_BODY_FIELDS = {
    "seq", "previous_event_hash", "event_type", "checkpoint_id",
    "proposal_id", "proposal_hash", "lineage_id", "protocol_version",
    "requested_action", "signer_principal", "signer_role", "bindings",
    "expected_ledger_tail", "outcome",
}


def v3_relevant_artifacts(payload: dict[str, Any], action: str) -> list[dict[str, Any]]:
    stages = set(V2_ACTION_PREFIX[action])
    return [
        row for row in payload.get("artifacts", [])
        if isinstance(row, dict) and row.get("producer_stage") in stages
    ]


def v3_action_core_projection(payload: dict[str, Any], action: str) -> dict[str, Any]:
    fields = (
        "schema_version", "protocol_version", "proposal_id", "proposal_source",
        "proposal_hash", "checkpoint_id", "lineage_id", "claims", "non_goals",
        "ambiguities", "claim_experiment_matrix", "baseline_fairness", "design",
        "oracle_attack", "reproducibility", "stage_dependencies", "action_contracts",
        "review_plan", "review_plan_hash", "unresolved_human_gates",
    )
    projection = {field: copy.deepcopy(payload.get(field)) for field in fields}
    projection["requested_action"] = action
    relevant_ids = {row.get("id") for row in v3_relevant_artifacts(payload, action)}
    projection["artifacts"] = [
        {
            "id": row.get("id"), "kind": row.get("kind"),
            "evidence_class": row.get("evidence_class"),
            "producer_stage": row.get("producer_stage"),
            "consumer_stage": row.get("consumer_stage"),
            "consumes": [item for item in row.get("consumes", []) if item in relevant_ids],
            "provides": [item for item in row.get("provides", []) if item in relevant_ids],
            "attested_action": row.get("attested_action"),
            "signer_identity": row.get("signer_identity"),
        }
        for row in v3_relevant_artifacts(payload, action)
    ]
    projection["stages"] = [
        {
            "id": row.get("id"),
            "required_artifacts": [item for item in row.get("required_artifacts", []) if item in relevant_ids],
            "provided_artifacts": [item for item in row.get("provided_artifacts", []) if item in relevant_ids],
        }
        for row in payload.get("stages", [])
        if isinstance(row, dict) and row.get("id") in set(V2_ACTION_PREFIX[action])
    ]
    if action in {"phase0_launch", "scale_launch"}:
        projection["phase0_requirements"] = copy.deepcopy(payload.get("phase0_requirements"))
        budget = payload.get("budget") if isinstance(payload.get("budget"), dict) else {}
        limit_key = "scale_limits" if action == "scale_launch" else "phase0_limits"
        projection["budget"] = {
            limit_key: copy.deepcopy(budget.get(limit_key)),
            "stop_rule": budget.get("stop_rule"),
        }
    if action == "scale_launch":
        projection["pilot_scale"] = copy.deepcopy(payload.get("pilot_scale"))
    return projection


def v3_action_core_hash(payload: dict[str, Any], action: str) -> str:
    return canonical_sha256(v3_action_core_projection(payload, action))


def v3_action_evidence_manifest(
    payload: dict[str, Any], artifact_path: Path, action: str,
    artifacts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    relevant_ids = {row.get("id") for row in v3_relevant_artifacts(payload, action)}
    for artifact_id in sorted(relevant_ids):
        artifact = artifacts.get(artifact_id, {})
        attestation_path = resolve_reference(artifact.get("attestation_path"), artifact_path)
        attestation = None
        if attestation_path is not None and attestation_path.is_file():
            attestation = load_json_object(attestation_path, f"manifest.{artifact_id}.attestation", [])
        consumed = [
            {
                "artifact_id": dependency,
                "semantic_sha256": artifacts.get(dependency, {}).get("semantic_sha256"),
            }
            for dependency in sorted(artifact.get("consumes") or [])
        ]
        rows.append({
            "id": artifact_id,
            "kind": artifact.get("kind"),
            "evidence_class": artifact.get("evidence_class"),
            "producer_stage": artifact.get("producer_stage"),
            "source_sha256": artifact.get("source_sha256"),
            "semantic_sha256": artifact.get("semantic_sha256"),
            "attestation_payload": attestation,
            "signature_identity": artifact.get("signer_identity"),
            "consumed_artifacts": consumed,
        })
    return rows


def v3_action_evidence_manifest_hash(
    payload: dict[str, Any], artifact_path: Path, action: str,
    artifacts: dict[str, dict[str, Any]],
) -> str:
    return canonical_sha256(v3_action_evidence_manifest(payload, artifact_path, action, artifacts))


def validate_v3_review_cycles(
    payload: dict[str, Any], artifact_path: Path, roles: dict[str, set[str]],
    keys: dict[str, str], errors: list[str], operational: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    plan = payload.get("review_plan")
    if not isinstance(plan, list) or not plan:
        errors.append("review_plan: expected a non-empty frozen plan")
        return {}, {}
    if payload.get("review_plan_hash") != canonical_sha256(plan):
        errors.append("review_plan_hash: canonical frozen plan mismatch")
    planned: dict[str, dict[str, Any]] = {}
    planned_signers: set[str] = set()
    planned_contexts: set[str] = set()
    for index, row in enumerate(plan):
        label = f"review_plan[{index}]"
        if not exact_keys(row, {"reviewer_id", "signer_identity", "reviewer_type", "reviewer_context_id", "reviewer_model"}, label, errors):
            continue
        reviewer_id = row.get("reviewer_id")
        valid_reviewer_id = nonempty_string(reviewer_id) and reviewer_id not in planned
        if not valid_reviewer_id:
            errors.append(f"{label}.reviewer_id: missing or duplicate")
        signer_identity = row.get("signer_identity")
        if not nonempty_string(signer_identity) or signer_identity in planned_signers:
            errors.append(
                f"{label}.signer_identity: missing or duplicate across planned reviewer slots"
            )
        else:
            planned_signers.add(signer_identity)
        reviewer_context_id = row.get("reviewer_context_id")
        if not nonempty_string(reviewer_context_id) or reviewer_context_id in planned_contexts:
            errors.append(
                f"{label}.reviewer_context_id: missing or duplicate across planned reviewer slots"
            )
        else:
            planned_contexts.add(reviewer_context_id)
        if row.get("reviewer_type") != "internal_blind_gpt" or row.get("reviewer_model") not in ALLOWED_GPT_MODELS:
            errors.append(f"{label}: exact internal GPT reviewer type/model is required")
        if row.get("reviewer_context_id") == payload.get("controller_context_id"):
            errors.append(f"{label}: reviewer context must be independent")
        if valid_reviewer_id:
            planned[str(reviewer_id)] = row
    history = payload.get("review_history")
    if not isinstance(history, list):
        errors.append("review_history: expected append-only review artifacts")
        return {}, {}
    groups: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = {}
    review_ids: set[str] = set()
    observed_reviewer_bindings: dict[str, tuple[str, str]] = {}
    observed_signer_owners: dict[str, str] = {}
    observed_context_owners: dict[str, str] = {}
    for index, row in enumerate(history):
        label = f"review_history[{index}]"
        expected_row_fields = {
            "event", "review_id", "reviewer_id", "phase", "core_hash",
            "evidence_manifest_hash", "requested_action", "opened_event_hash",
            "source_path", "source_sha256", "semantic_sha256",
            "attestation_sha256", "signature_path",
        }
        if not isinstance(row, dict) or not exact_keys(row, expected_row_fields, label, errors):
            continue
        if row.get("event") != "review" or row.get("phase") not in {"initial", "re_review"}:
            errors.append(f"{label}: malformed review event/phase")
            continue
        review_id = row.get("review_id")
        if not nonempty_string(review_id) or review_id in review_ids:
            errors.append(f"{label}.review_id: missing or duplicate")
        review_ids.add(str(review_id))
        plan_row = planned.get(row.get("reviewer_id"))
        if plan_row is None:
            errors.append(f"{label}.reviewer_id: reviewer is not in frozen plan")
            continue
        source_path = resolve_reference(row.get("source_path"), artifact_path)
        if source_path is None or not source_path.is_file():
            errors.append(f"{label}.source_path: signed review artifact is missing")
            continue
        if sha256_file(source_path) != row.get("source_sha256"):
            errors.append(f"{label}.source_sha256: review source hash mismatch")
        review = load_json_object(source_path, f"{label}.source", errors)
        if review is None:
            continue
        semantic_hash = canonical_sha256(review)
        if semantic_hash != row.get("semantic_sha256") or semantic_hash != row.get("attestation_sha256"):
            errors.append(f"{label}: semantic/attestation hash mismatch")
        expected_source_fields = {
            "schema_version", "protocol_version", "proposal_id", "proposal_hash",
            "requested_action", "opened_event_hash", "core_hash",
            "evidence_manifest_hash", "plan_hash", "reviewer_id",
            "reviewer_context_id", "reviewer_model", "signer_principal",
            "signer_role", "phase", "verdict", "findings",
        }
        exact_keys(review, expected_source_fields, f"{label}.source", errors)
        bindings = {
            "schema_version": V3_SCHEMA_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "proposal_id": payload.get("proposal_id"),
            "proposal_hash": payload.get("proposal_hash"),
            "requested_action": row.get("requested_action"),
            "opened_event_hash": row.get("opened_event_hash"),
            "core_hash": row.get("core_hash"),
            "evidence_manifest_hash": row.get("evidence_manifest_hash"),
            "plan_hash": payload.get("review_plan_hash"),
            "reviewer_id": row.get("reviewer_id"),
            "reviewer_context_id": plan_row.get("reviewer_context_id"),
            "reviewer_model": plan_row.get("reviewer_model"),
            "signer_principal": plan_row.get("signer_identity"),
            "signer_role": "reviewer",
            "phase": row.get("phase"),
        }
        for field, expected in bindings.items():
            if review.get(field) != expected:
                errors.append(f"{label}.source.{field}: stale or mismatched binding")
        actual_reviewer = str(review.get("reviewer_id"))
        actual_signer = str(review.get("signer_principal"))
        actual_context = str(review.get("reviewer_context_id"))
        observed_binding = observed_reviewer_bindings.get(actual_reviewer)
        if observed_binding is not None and observed_binding != (actual_signer, actual_context):
            errors.append(
                f"{label}.source: reviewer_id cannot swap signer/context between review phases"
            )
        else:
            observed_reviewer_bindings[actual_reviewer] = (actual_signer, actual_context)
        signer_owner = observed_signer_owners.get(actual_signer)
        if signer_owner is not None and signer_owner != actual_reviewer:
            errors.append(
                f"{label}.source.signer_principal: signer cannot satisfy two reviewer IDs"
            )
        else:
            observed_signer_owners[actual_signer] = actual_reviewer
        context_owner = observed_context_owners.get(actual_context)
        if context_owner is not None and context_owner != actual_reviewer:
            errors.append(
                f"{label}.source.reviewer_context_id: context cannot satisfy two reviewer IDs"
            )
        else:
            observed_context_owners[actual_context] = actual_reviewer
        verdict = review.get("verdict")
        if verdict not in {"pass", "blocked"}:
            errors.append(f"{label}.source.verdict: malformed exact enum")
        findings = review.get("findings")
        if not isinstance(findings, list):
            errors.append(f"{label}.source.findings: expected a list")
            findings = []
        finding_ids: set[str] = set()
        for finding_index, finding in enumerate(findings):
            finding_label = f"{label}.source.findings[{finding_index}]"
            if not exact_keys(finding, {"id", "severity", "status", "summary"}, finding_label, errors):
                continue
            if finding.get("id") in finding_ids:
                errors.append(f"{finding_label}.id: duplicate")
            finding_ids.add(str(finding.get("id")))
            if finding.get("severity") not in FINDING_SEVERITIES or finding.get("status") not in {"open", "resolved"}:
                errors.append(f"{finding_label}: malformed exact enum")
        signer = plan_row.get("signer_identity")
        if roles and (signer not in roles or "reviewer" not in roles.get(signer, set())):
            errors.append(f"{label}.signer: trusted reviewer role is required")
        verify_detached_signature(
            review, row.get("signature_path"), signer, "reviewer", roles, keys,
            artifact_path, f"{label}.signature", operational, errors,
        )
        group = (
            str(row.get("requested_action")), str(row.get("opened_event_hash")),
            str(row.get("core_hash")), str(row.get("evidence_manifest_hash")),
            str(payload.get("review_plan_hash")), str(row.get("phase")),
        )
        groups.setdefault(group, []).append({"row": row, "review": review})
    cycle_map: dict[str, dict[str, Any]] = {}
    review_to_cycle: dict[str, dict[str, Any]] = {}
    planned_projection = [
        {
            "reviewer_id": row.get("reviewer_id"),
            "signer_principal": row.get("signer_identity"),
            "signer_role": "reviewer",
            "reviewer_context_id": row.get("reviewer_context_id"),
            "reviewer_model": row.get("reviewer_model"),
        }
        for row in sorted(plan, key=lambda item: str(item.get("reviewer_id")))
        if isinstance(row, dict)
    ]
    for group, members in groups.items():
        reviewer_ids = [member["row"].get("reviewer_id") for member in members]
        duplicate_slots = sorted({
            str(reviewer_id) for reviewer_id in reviewer_ids
            if reviewer_ids.count(reviewer_id) > 1
        })
        if duplicate_slots:
            errors.append(
                "review cycle must contain exactly one signed row per frozen reviewer slot; "
                "duplicate reviewer_id=" + ",".join(duplicate_slots)
            )
            continue
        if set(reviewer_ids) != set(planned) or len(reviewer_ids) != len(planned):
            continue
        reviews_projection = []
        blocked = False
        for member in sorted(members, key=lambda item: str(item["row"].get("reviewer_id"))):
            row = member["row"]
            review = member["review"]
            normalized_findings = sorted(review.get("findings") or [], key=lambda item: str(item.get("id")))
            blocked = blocked or review.get("verdict") == "blocked" or any(
                finding.get("severity") in BLOCKING_SEVERITIES and finding.get("status") == "open"
                for finding in normalized_findings if isinstance(finding, dict)
            )
            reviews_projection.append({
                "reviewer_id": row.get("reviewer_id"),
                "signer_principal": review.get("signer_principal"),
                "reviewer_context_id": review.get("reviewer_context_id"),
                "verdict": review.get("verdict"),
                "findings": normalized_findings,
                "source_sha256": row.get("source_sha256"),
                "semantic_sha256": row.get("semantic_sha256"),
                "attestation_sha256": row.get("attestation_sha256"),
            })
        projection = {
            "requested_action": group[0], "opened_event_hash": group[1],
            "core_hash": group[2], "evidence_manifest_hash": group[3],
            "review_plan_hash": group[4], "phase": group[5],
            "planned_reviewers": planned_projection,
            "reviews": reviews_projection,
        }
        cycle_hash = canonical_sha256(projection)
        cycle = {
            "hash": cycle_hash, "action": group[0], "opened_event_hash": group[1],
            "core_hash": group[2], "manifest_hash": group[3], "plan_hash": group[4],
            "phase": group[5], "verdict": "blocked" if blocked else "pass",
            "review_ids": tuple(member["row"].get("review_id") for member in members),
        }
        cycle_map[cycle_hash] = cycle
        for review_id in cycle["review_ids"]:
            review_to_cycle[str(review_id)] = cycle
    return cycle_map, review_to_cycle


V3_MINIMUM_EVIDENCE_KINDS = {
    "static_acquisition": ("code_test",),
    "human_oracle": ("registry", "blinded_audit_bundle"),
    "phase0_launch": (
        "human_labels", "human_derivation", "clean_reproduction", "capability_evidence",
    ),
    "scale_launch": (
        "blinded_audit_bundle", "phase0_raw_result", "phase0_result",
    ),
}


def validate_v3_minimum_evidence(
    action: str,
    artifacts: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    verified_artifacts: set[str],
    errors: list[str],
) -> None:
    """Require concrete, verified action evidence; stage status is not evidence."""

    by_kind: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts.values():
        by_kind.setdefault(str(artifact.get("kind")), []).append(artifact)
    for kind in V3_MINIMUM_EVIDENCE_KINDS[action]:
        rows = by_kind.get(kind, [])
        if not rows:
            errors.append(f"minimum_evidence.{action}: missing required artifact kind {kind}")
            continue
        if kind == "code_test":
            for row in rows:
                source = sources.get(str(row.get("id")))
                if not isinstance(source, dict) or source.get("tests_passed") is not True:
                    errors.append(
                        "minimum_evidence.static_acquisition: code_test must be a passed "
                        "content-bound nonauthorizing Code Readiness contract"
                    )
        elif not any(str(row.get("id")) in verified_artifacts for row in rows):
            errors.append(
                f"minimum_evidence.{action}: required artifact kind {kind} "
                "has no verified detached attestation"
            )


def validate_v3_scientific_context(
    payload: dict[str, Any], artifact_path: Path, action: str,
    trust_policy: Path | None, trust_policy_hash: str | None,
) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    operational: list[str] = []
    if payload.get("schema_version") != V3_SCHEMA_VERSION or payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("schema/protocol: expected research-execution-grill-v3 schema 3")
    for key in ("proposal_id", "proposal_source", "proposal_hash", "controller_context_id", "checkpoint_id", "lineage_id"):
        require_string(payload, key, errors)
    validate_hashed_file(payload, "proposal_source", "proposal_hash", artifact_path, errors)
    roles, keys = load_trust_policy(trust_policy, trust_policy_hash, artifact_path, operational)
    artifacts, sources, verified_artifacts = validate_v2_artifacts(
        payload, artifact_path, action, roles, keys, errors, operational
    )
    _stages, stage_ready = validate_v2_stages(payload, artifacts, action, errors)
    validate_v3_minimum_evidence(action, artifacts, sources, verified_artifacts, errors)
    claim_ids = validate_claims(payload, errors)
    require_string_list(payload, "non_goals", errors)
    validate_claim_matrix(payload, claim_ids, errors)
    validate_baselines(payload, errors)
    validate_design(payload, errors)
    validate_oracle_attack(payload, errors)
    validate_object_strings(payload, "reproducibility", ("env_lock", "code_ref_policy", "data_ref_policy", "manifest_path"), errors)
    validate_v2_ambiguities(payload, artifacts, sources, action in {"phase0_launch", "scale_launch"}, errors)
    gates = payload.get("unresolved_human_gates")
    if not isinstance(gates, list):
        errors.append("unresolved_human_gates: expected a list")
    elif action in {"phase0_launch", "scale_launch"} and gates:
        errors.append("unresolved_human_gates: phase0/scale authorization requires an empty list")
    if payload.get("review_plan_hash") != canonical_sha256(payload.get("review_plan")):
        errors.append("review_plan_hash: canonical frozen plan mismatch")
    requirements = payload.get("phase0_requirements")
    if action in {"phase0_launch", "scale_launch"}:
        expected_kinds = {
            "registry_artifact_id": "registry", "bundle_artifact_id": "blinded_audit_bundle",
            "labels_artifact_id": "human_labels", "derivation_artifact_id": "human_derivation",
            "reproduction_artifact_id": "clean_reproduction", "capability_artifact_id": "capability_evidence",
        }
        if not isinstance(requirements, dict):
            errors.append("phase0_requirements: typed artifact IDs are required")
        else:
            for field, kind in expected_kinds.items():
                artifact = artifacts.get(requirements.get(field))
                if artifact is None or artifact.get("kind") != kind:
                    errors.append(f"phase0_requirements.{field}: signed {kind} artifact is required")
            capability_id = requirements.get("capability_artifact_id")
            capability = sources.get(capability_id)
            if capability_id in verified_artifacts and isinstance(capability, dict):
                unavailable = [name for name in V2_CAPABILITIES if capability.get(name) is False]
                if unavailable:
                    operational.append("signed runtime capability unavailable: " + ", ".join(unavailable))
        budget = payload.get("budget")
        limit_key = "scale_limits" if action == "scale_launch" else "phase0_limits"
        limits = budget.get(limit_key) if isinstance(budget, dict) else None
        if not isinstance(limits, dict) or not limits:
            errors.append(f"budget.{limit_key}: positive finite bounds are required")
        else:
            for name, value in limits.items():
                if not nonempty_string(name) or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                    errors.append(f"budget.{limit_key}.{name}: expected a positive finite number")
        if not isinstance(budget, dict) or not nonempty_string(budget.get("stop_rule")):
            errors.append("budget.stop_rule: required")
    manifest_hash = v3_action_evidence_manifest_hash(payload, artifact_path, action, artifacts)
    if action == "scale_launch":
        validate_v2_scale(payload, artifacts, sources, v2_evidence_manifest_hash(payload), errors)
    context = {
        "roles": roles, "keys": keys, "artifacts": artifacts, "sources": sources,
        "stage_ready": stage_ready,
        "core_hash": v3_action_core_hash(payload, action),
        "manifest_hash": manifest_hash,
        "review_plan_hash": payload.get("review_plan_hash"),
    }
    return context, errors, operational


def load_v3_ledger_events(
    payload: dict[str, Any], artifact_path: Path, ledger_value: Path | None,
    roles: dict[str, set[str]], keys: dict[str, str],
    errors: list[str], operational: list[str], *, allow_missing: bool = False,
) -> tuple[list[V3ValidatedEvent], list[dict[str, Any]], Path | None]:
    ledger_path = resolve_cli_path(ledger_value, artifact_path)
    if ledger_path is None:
        if allow_missing:
            return [], [], None
        operational.append("lineage: v3 signed ledger path is required")
        return [], [], None
    if not ledger_path.is_file():
        if allow_missing:
            return [], [], ledger_path
        operational.append(f"lineage: ledger does not exist: {ledger_path}")
        return [], [], ledger_path
    ledger = load_json_object(ledger_path, "lineage", errors)
    if ledger is None:
        return [], [], ledger_path
    if not exact_keys(ledger, {"schema_version", "protocol_version", "events"}, "lineage", errors):
        return [], [], ledger_path
    if ledger.get("schema_version") != V3_SCHEMA_VERSION or ledger.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("lineage: expected schema 3 / research-execution-grill-v3")
    rows = ledger.get("events")
    if not isinstance(rows, list):
        errors.append("lineage.events: expected a list")
        return [], [], ledger_path
    events: list[V3ValidatedEvent] = []
    bodies: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        label = f"lineage.events[{index}]"
        if not exact_keys(row, {"body", "event_hash", "signature_path"}, label, errors):
            continue
        body = row.get("body")
        if not exact_keys(body, V3_EVENT_BODY_FIELDS, f"{label}.body", errors):
            continue
        event_hash = canonical_sha256(body)
        if row.get("event_hash") != event_hash:
            errors.append(f"{label}.event_hash: canonical body hash mismatch")
        envelope = {"body": body, "event_hash": row.get("event_hash")}
        signer = body.get("signer_principal")
        if body.get("signer_role") != "lineage_authority":
            errors.append(f"{label}.body.signer_role: lineage_authority is required")
        verify_detached_signature(
            envelope, row.get("signature_path"), signer, "lineage_authority",
            roles, keys, ledger_path, f"{label}.signature", operational, errors,
            namespace=V3_LINEAGE_NAMESPACE,
        )
        for field, expected in {
            "checkpoint_id": payload.get("checkpoint_id"),
            "proposal_id": payload.get("proposal_id"),
            "proposal_hash": payload.get("proposal_hash"),
            "lineage_id": payload.get("lineage_id"),
            "protocol_version": PROTOCOL_VERSION,
        }.items():
            if body.get(field) != expected:
                errors.append(f"{label}.body.{field}: checkpoint/proposal/lineage binding mismatch")
        bindings = body.get("bindings")
        if not isinstance(bindings, dict) or not all(nonempty_string(key) and nonempty_string(value) for key, value in bindings.items()):
            errors.append(f"{label}.body.bindings: expected non-empty string bindings")
            bindings = {}
        try:
            event_type = V3EventType(body.get("event_type"))
        except ValueError:
            errors.append(f"{label}.body.event_type: malformed exact enum")
            continue
        action_value = body.get("requested_action")
        try:
            action = V3Action(action_value) if action_value is not None else None
        except ValueError:
            errors.append(f"{label}.body.requested_action: malformed exact enum")
            continue
        outcome_value = body.get("outcome")
        try:
            outcome = V3Outcome(outcome_value) if outcome_value is not None else None
        except ValueError:
            errors.append(f"{label}.body.outcome: malformed exact enum")
            continue
        if not isinstance(body.get("seq"), int) or isinstance(body.get("seq"), bool):
            errors.append(f"{label}.body.seq: expected integer")
            continue
        events.append(V3ValidatedEvent(
            body["seq"], body.get("previous_event_hash"), str(row.get("event_hash")),
            event_type, action, body.get("expected_ledger_tail"),
            tuple(sorted((str(key), str(value)) for key, value in bindings.items())),
            outcome,
        ))
        bodies.append(body)
    return events, bodies, ledger_path


def validate_v3_tail_pin(
    pinned_tail: str | None,
    events: list[V3ValidatedEvent],
    errors: list[str],
) -> str:
    observed = events[-1].event_hash if events else V3_EMPTY_LEDGER_TAIL
    if not isinstance(pinned_tail, str) or not pinned_tail:
        errors.append(
            "lineage_tail_sha256: explicit external tail pin is required "
            f"(use {V3_EMPTY_LEDGER_TAIL!r} only for an empty ledger)"
        )
        return observed
    if observed == V3_EMPTY_LEDGER_TAIL:
        if pinned_tail != V3_EMPTY_LEDGER_TAIL:
            errors.append(
                f"lineage_tail_sha256: empty ledger requires exact {V3_EMPTY_LEDGER_TAIL!r} sentinel"
            )
        return observed
    if not V3_SHA256_PATTERN.fullmatch(pinned_tail):
        errors.append("lineage_tail_sha256: expected canonical lowercase sha256:<64 hex> tail")
    elif pinned_tail == "sha256:" + "0" * 64:
        errors.append("lineage_tail_sha256: zero tail is never a valid external pin")
    elif pinned_tail != observed:
        errors.append("lineage_tail_sha256: external pin does not match observed canonical ledger tail")
    return observed


def validate_v3_final_review_bindings(
    bodies: list[dict[str, Any]], cycle_map: dict[str, dict[str, Any]], errors: list[str],
) -> None:
    opened_by_hash = {
        canonical_sha256(body): body
        for body in bodies
        if body.get("event_type") == V3EventType.ACTION_OPENED.value
    }
    for index, body in enumerate(bodies):
        bindings = body.get("bindings") if isinstance(body.get("bindings"), dict) else {}
        if body.get("event_type") == V3EventType.CORRECTION_APPLIED.value:
            cycle_hash = bindings.get("initial_review_cycle_hash")
            cycle = cycle_map.get(cycle_hash)
            opened = opened_by_hash.get(bindings.get("opened_event_hash"))
            if cycle is None:
                errors.append(
                    f"lineage.events[{index}]: correction lacks its retained complete signed blocked initial review cycle"
                )
                continue
            expected = {
                "action": body.get("requested_action"),
                "opened_event_hash": bindings.get("opened_event_hash"),
                "core_hash": bindings.get("before_core_hash"),
                "manifest_hash": bindings.get("before_manifest_hash"),
                "plan_hash": (opened.get("bindings") or {}).get("review_plan_hash") if opened else None,
                "phase": "initial",
                "verdict": "blocked",
            }
            for field, value in expected.items():
                if cycle.get(field) != value:
                    errors.append(
                        f"lineage.events[{index}].bindings.initial_review_cycle_hash: "
                        f"blocked initial review cycle {field} mismatch"
                    )
            continue
        if body.get("event_type") != V3EventType.ACTION_FINALIZED.value:
            continue
        cycle_hash = bindings.get("review_cycle_hash")
        cycle = cycle_map.get(cycle_hash)
        if cycle is None:
            errors.append(f"lineage.events[{index}]: finalized event lacks a retained complete signed review cycle")
            continue
        expected = {
            "action": body.get("requested_action"),
            "opened_event_hash": bindings.get("opened_event_hash"),
            "core_hash": bindings.get("final_core_hash"),
            "manifest_hash": bindings.get("final_manifest_hash"),
            "phase": bindings.get("review_phase"),
            "verdict": bindings.get("review_verdict"),
        }
        for field, value in expected.items():
            if cycle.get(field) != value:
                errors.append(f"lineage.events[{index}].bindings.{field}: review cycle mismatch")


def current_v3_review_cycle(
    payload: dict[str, Any], review_to_cycle: dict[str, dict[str, Any]],
    action: str, opened_hash: str, core_hash: str, manifest_hash: str,
    errors: list[str],
) -> dict[str, Any] | None:
    current_ids = payload.get("current_review_ids")
    if not isinstance(current_ids, list) or not current_ids or len(current_ids) != len(set(current_ids)):
        errors.append("current_review_ids: exact current complete review set is required")
        return None
    cycles = {review_to_cycle.get(str(review_id), {}).get("hash") for review_id in current_ids}
    cycles.discard(None)
    if len(cycles) != 1:
        errors.append("current_review_ids: reviews must identify one complete cycle")
        return None
    cycle = next((value for value in review_to_cycle.values() if value.get("hash") == next(iter(cycles))), None)
    if cycle is None or set(cycle.get("review_ids", ())) != set(current_ids):
        errors.append("current_review_ids: must equal every and only review in the complete cycle")
        return None
    for field, expected in {
        "action": action, "opened_event_hash": opened_hash,
        "core_hash": core_hash, "manifest_hash": manifest_hash,
        "plan_hash": payload.get("review_plan_hash"),
    }.items():
        if cycle.get(field) != expected:
            errors.append(f"current_review_ids: stale {field} binding")
    return cycle


def infer_lineage_principal(roles: dict[str, set[str]], explicit: str | None, errors: list[str]) -> str | None:
    if explicit is not None:
        if explicit not in roles or "lineage_authority" not in roles.get(explicit, set()):
            errors.append("event signer principal lacks lineage_authority role")
            return None
        return explicit
    candidates = sorted(identity for identity, identity_roles in roles.items() if "lineage_authority" in identity_roles)
    if len(candidates) != 1:
        errors.append("event signer principal is required unless exactly one lineage_authority is trusted")
        return None
    return candidates[0]


def v3_candidate_body(
    payload: dict[str, Any], event_type: str, action: str | None,
    signer_principal: str, state: Any, next_seq: int, context: dict[str, Any],
    cycle: dict[str, Any] | None, errors: list[str],
) -> dict[str, Any] | None:
    previous = state.tail_hash
    bindings: dict[str, str] = {}
    outcome: str | None = None
    requested = action
    current_action_state = state.action_states[-1] if state.action_states and state.action_states[-1].outcome is None else None
    if event_type == V3EventType.CHECKPOINT_OPENED.value:
        if state.tail_hash != V3_EMPTY_LEDGER_TAIL:
            errors.append("prepare checkpoint_opened: checkpoint already exists")
        requested = None
        bindings = {"action_order": ",".join(item.value for item in V3_ACTION_ORDER)}
    elif event_type == V3EventType.ACTION_OPENED.value:
        if action is None:
            errors.append("prepare action_opened: --requested-action is required")
        bindings = {
            "core_hash": context.get("core_hash"),
            "evidence_manifest_hash": context.get("manifest_hash"),
            "review_plan_hash": context.get("review_plan_hash"),
        }
    elif event_type == V3EventType.CORRECTION_APPLIED.value:
        if current_action_state is None or action != current_action_state.action.value:
            errors.append("prepare correction_applied: requested action is not currently open")
        elif cycle is None or cycle.get("phase") != "initial" or cycle.get("verdict") != "blocked":
            errors.append("prepare correction_applied: one complete blocked initial review cycle is required")
        else:
            bindings = {
                "opened_event_hash": current_action_state.opened_event_hash,
                "before_core_hash": current_action_state.initial_core_hash,
                "after_core_hash": context.get("core_hash"),
                "before_manifest_hash": current_action_state.initial_manifest_hash,
                "after_manifest_hash": context.get("manifest_hash"),
                "initial_review_cycle_hash": cycle.get("hash"),
            }
    elif event_type == V3EventType.ACTION_FINALIZED.value:
        if current_action_state is None or action != current_action_state.action.value:
            errors.append("prepare action_finalized: requested action is not currently open")
        elif cycle is None:
            errors.append("prepare action_finalized: complete current signed review cycle is required")
        else:
            corrected = current_action_state.correction_event_hash is not None
            if not corrected and (cycle.get("phase") != "initial" or cycle.get("verdict") != "pass"):
                errors.append("prepare action_finalized: blocked initial review requires correction_applied")
            elif corrected and cycle.get("phase") != "re_review":
                errors.append("prepare action_finalized: correction requires complete re_review")
            else:
                outcome = (
                    V3Outcome.AUTHORIZED.value
                    if cycle.get("verdict") == "pass"
                    else V3Outcome.ARCHITECTURE_RESET_REQUIRED.value
                )
                bindings = {
                    "opened_event_hash": current_action_state.opened_event_hash,
                    "final_core_hash": context.get("core_hash"),
                    "final_manifest_hash": context.get("manifest_hash"),
                    "review_cycle_hash": cycle.get("hash"),
                    "review_phase": cycle.get("phase"),
                    "review_verdict": cycle.get("verdict"),
                }
                if corrected:
                    bindings["correction_event_hash"] = current_action_state.correction_event_hash
    else:
        errors.append("prepare event: malformed event type")
    if errors:
        return None
    return {
        "seq": next_seq,
        "previous_event_hash": previous,
        "event_type": event_type,
        "checkpoint_id": payload.get("checkpoint_id"),
        "proposal_id": payload.get("proposal_id"),
        "proposal_hash": payload.get("proposal_hash"),
        "lineage_id": payload.get("lineage_id"),
        "protocol_version": PROTOCOL_VERSION,
        "requested_action": requested,
        "signer_principal": signer_principal,
        "signer_role": "lineage_authority",
        "bindings": bindings,
        "expected_ledger_tail": previous,
        "outcome": outcome,
    }

def validate_v2_audit(payload: dict[str, Any], artifact_path: Path) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 2 or payload.get("protocol_version") != LEGACY_V2_PROTOCOL_VERSION:
        errors.append("schema/protocol: expected historical schema 2 / research-execution-grill-v2")
    for key in ("proposal_id", "proposal_source", "proposal_hash", "lineage_id"):
        require_string(payload, key, errors)
    validate_hashed_file(payload, "proposal_source", "proposal_hash", artifact_path, errors)
    rows = payload.get("artifacts")
    if not isinstance(rows, list) or not rows:
        errors.append("artifacts: historical v2 declaration list is required")
    else:
        ids = [row.get("id") for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or any(not nonempty_string(item) for item in ids) or len(ids) != len(set(ids)):
            errors.append("artifacts: historical v2 artifact IDs must be complete and unique")
    if not isinstance(payload.get("review_history"), list):
        errors.append("review_history: historical v2 append-only list is required")
    return errors


def emit_issues(title: str, issues: list[str], exit_code: int) -> int:
    print(f"{title} with {len(issues)} issue(s):", file=sys.stderr)
    for issue in issues:
        print(f"- {issue}", file=sys.stderr)
    return exit_code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--required-checkpoint", choices=sorted(CHECKPOINTS))
    parser.add_argument("--required-authorization", choices=V2_ACTIONS)
    parser.add_argument("--prepare-event", choices=[item.value for item in V3EventType])
    parser.add_argument("--prepare-authorization", choices=V2_ACTIONS)
    parser.add_argument("--requested-action", choices=V2_ACTIONS)
    parser.add_argument("--candidate-out", type=Path)
    parser.add_argument("--event-signer-principal")
    parser.add_argument("--event-signer-role", default="lineage_authority")
    parser.add_argument("--trust-policy", type=Path)
    parser.add_argument("--trust-policy-sha256")
    parser.add_argument("--lineage-ledger", type=Path)
    parser.add_argument("--lineage-tail-sha256")
    parser.add_argument(
        "--audit-v1",
        action="store_true",
        help="inspect historical schema v1 structure only; never authorizes an action",
    )
    parser.add_argument(
        "--audit-v2",
        action="store_true",
        help="inspect historical schema v2 structure only; never authorizes an action",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = json.loads(
            args.artifact.read_text(encoding="utf-8"),
            parse_constant=reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"GRILL VALIDATOR ERROR: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("GRILL VALIDATOR ERROR: top-level JSON must be an object", file=sys.stderr)
        return 2
    schema_version = payload.get("schema_version")
    if schema_version == 1:
        if not args.audit_v1 or args.audit_v2:
            print(
                "GRILL VALIDATOR ERROR: schema v1 requires explicit --audit-v1 and cannot authorize",
                file=sys.stderr,
            )
            return 1
        errors, _ = validate_v1(payload, args.artifact.resolve(), args.required_checkpoint)
        if errors:
            print(f"Research execution Grill v1 structural audit failed with {len(errors)} violation(s):", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print("Research execution Grill v1 structural audit passed; authorization is unavailable.")
        return 4
    if schema_version == 2:
        if not args.audit_v2 or args.audit_v1:
            print("GRILL VALIDATOR ERROR: schema v2 requires explicit matching --audit-v2 and cannot authorize", file=sys.stderr)
            return 1
        errors = validate_v2_audit(payload, args.artifact.resolve())
        if errors:
            return emit_issues("Research execution Grill v2 structural audit failed", errors, 1)
        print("Research execution Grill v2 structural audit passed; authorization is unavailable.")
        return 4
    if schema_version != V3_SCHEMA_VERSION:
        print(f"GRILL VALIDATOR ERROR: unsupported schema_version {schema_version!r}", file=sys.stderr)
        return 1
    if args.audit_v1 or args.audit_v2:
        print("GRILL VALIDATOR ERROR: legacy audit flags reject schema v3", file=sys.stderr)
        return 1
    if args.required_checkpoint is not None:
        print("GRILL VALIDATOR ERROR: --required-checkpoint is non-authorizing; use an exact v3 action", file=sys.stderr)
        return 1
    prepare_event = args.prepare_event
    prepare_action = args.requested_action
    if args.prepare_authorization is not None:
        if prepare_event is not None or (prepare_action is not None and prepare_action != args.prepare_authorization):
            print("GRILL VALIDATOR ERROR: conflicting prepare modes/actions", file=sys.stderr)
            return 1
        prepare_event = V3EventType.ACTION_FINALIZED.value
        prepare_action = args.prepare_authorization
    if args.required_authorization is not None and prepare_event is not None:
        print("GRILL VALIDATOR ERROR: prepare and authorization modes are mutually exclusive", file=sys.stderr)
        return 1
    if args.required_authorization is None and prepare_event is None:
        print("Research execution Grill v3 is nonauthorizing without prepare or required-authorization mode.")
        return 3
    if args.event_signer_role != "lineage_authority":
        print("GRILL VALIDATOR ERROR: v3 event signer role must be lineage_authority", file=sys.stderr)
        return 1
    requested_action = args.required_authorization or prepare_action
    context_action = requested_action or V3Action.STATIC_ACQUISITION.value
    context, errors, operational = validate_v3_scientific_context(
        payload, args.artifact.resolve(), context_action,
        args.trust_policy, args.trust_policy_sha256,
    )
    allow_missing_ledger = prepare_event == V3EventType.CHECKPOINT_OPENED.value
    events, bodies, _ledger_path = load_v3_ledger_events(
        payload, args.artifact.resolve(), args.lineage_ledger,
        context.get("roles", {}), context.get("keys", {}), errors, operational,
        allow_missing=allow_missing_ledger,
    )
    validate_v3_tail_pin(args.lineage_tail_sha256, events, errors)
    state = evaluate_v3_events(events)
    if state.decision is V3DecisionKind.VALIDATION_ERROR:
        errors.append(f"state_machine: {state.message}")
    cycle_map, review_to_cycle = validate_v3_review_cycles(
        payload, args.artifact.resolve(), context.get("roles", {}),
        context.get("keys", {}), errors, operational,
    )
    validate_v3_final_review_bindings(bodies, cycle_map, errors)
    if errors:
        return emit_issues("Research execution Grill v3 validation failed", errors, 1)
    if operational:
        return emit_issues("Research execution Grill is OPERATIONAL_BLOCKED", operational, 3)
    if prepare_event is not None:
        if prepare_event != V3EventType.CHECKPOINT_OPENED.value and not context.get("stage_ready"):
            print(f"Research execution Grill action {prepare_action} is not ready to prepare.")
            return 3
        principal = infer_lineage_principal(context.get("roles", {}), args.event_signer_principal, errors)
        cycle = None
        current_action_state = state.action_states[-1] if state.action_states and state.action_states[-1].outcome is None else None
        if prepare_event == V3EventType.CORRECTION_APPLIED.value and current_action_state is not None and prepare_action is not None:
            cycle = current_v3_review_cycle(
                payload, review_to_cycle, prepare_action, current_action_state.opened_event_hash,
                current_action_state.initial_core_hash, current_action_state.initial_manifest_hash, errors,
            )
        elif prepare_event == V3EventType.ACTION_FINALIZED.value and current_action_state is not None and prepare_action is not None:
            cycle = current_v3_review_cycle(
                payload, review_to_cycle, prepare_action, current_action_state.opened_event_hash,
                context.get("core_hash"), context.get("manifest_hash"), errors,
            )
        if principal is None:
            return emit_issues("Research execution Grill v3 candidate preparation failed", errors, 1)
        body = v3_candidate_body(
            payload, prepare_event, prepare_action, principal, state, len(events), context, cycle, errors,
        )
        if body is None:
            return emit_issues("Research execution Grill v3 candidate preparation failed", errors, 1)
        event_hash = canonical_sha256(body)
        try:
            candidate_event = V3ValidatedEvent(
                body["seq"], body.get("previous_event_hash"), event_hash,
                V3EventType(body["event_type"]),
                V3Action(body["requested_action"]) if body.get("requested_action") else None,
                body.get("expected_ledger_tail"),
                tuple(sorted((str(key), str(value)) for key, value in body["bindings"].items())),
                V3Outcome(body["outcome"]) if body.get("outcome") else None,
            )
        except ValueError as exc:
            return emit_issues("Research execution Grill v3 candidate preparation failed", [str(exc)], 1)
        candidate_state = evaluate_v3_events([*events, candidate_event])
        if candidate_state.decision is V3DecisionKind.VALIDATION_ERROR:
            return emit_issues("Research execution Grill v3 candidate preparation failed", [candidate_state.message], 1)
        envelope = {"body": body, "event_hash": event_hash}
        encoded = canonical_json(envelope)
        if args.candidate_out is not None:
            candidate_path = resolve_cli_path(args.candidate_out, args.artifact.resolve())
            try:
                assert candidate_path is not None
                with candidate_path.open("xb") as handle:
                    handle.write(encoded)
            except FileExistsError:
                print(f"GRILL VALIDATOR ERROR: candidate output already exists: {candidate_path}", file=sys.stderr)
                return 1
            except OSError as exc:
                print(f"GRILL VALIDATOR ERROR: cannot write candidate: {exc}", file=sys.stderr)
                return 2
            print(f"PREPARED_NOT_AUTHORIZED: {candidate_path}")
        else:
            print(encoded.decode("utf-8"))
        return 5
    assert args.required_authorization is not None
    action = args.required_authorization
    if not context.get("stage_ready"):
        print(f"Research execution Grill v3: {action} evidence stage is not ready.")
        return 3
    opened_body = next((body for body in bodies if body.get("event_type") == "action_opened" and body.get("requested_action") == action), None)
    finalized_body = next((body for body in bodies if body.get("event_type") == "action_finalized" and body.get("requested_action") == action), None)
    if opened_body is not None:
        opened_bindings = opened_body.get("bindings", {})
        if opened_bindings.get("review_plan_hash") != context.get("review_plan_hash"):
            return emit_issues("Research execution Grill v3 validation failed", ["action_opened review-plan binding is stale"], 1)
    if finalized_body is not None:
        final_bindings = finalized_body.get("bindings", {})
        drift = []
        if final_bindings.get("final_core_hash") != context.get("core_hash"):
            drift.append("action_finalized core binding is stale")
        if final_bindings.get("final_manifest_hash") != context.get("manifest_hash"):
            drift.append("action_finalized evidence manifest binding is stale")
        if drift:
            return emit_issues("Research execution Grill v3 validation failed", drift, 1)
    decision = v3_authorization(state, V3Action(action))
    if decision.decision is not V3DecisionKind.AUTHORIZED:
        print(f"Research execution Grill v3: {action} is not yet authorized.")
        return 3
    print(f"Research execution Grill v3 authorized: {payload['proposal_id']} -> {action}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
