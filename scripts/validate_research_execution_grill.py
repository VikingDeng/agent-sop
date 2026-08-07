#!/usr/bin/env python3
"""Fail-closed validator for a research execution Grill artifact."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


READY_STATUSES = {"implementation_ready", "scale_ready"}
CHECKPOINTS = {"pre_implementation", "pre_scale"}
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
    core.pop("reviews", None)
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


def validate(
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--required-checkpoint", choices=sorted(CHECKPOINTS))
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
    errors, ready = validate(payload, args.artifact.resolve(), args.required_checkpoint)
    if errors:
        print(f"Research execution Grill failed with {len(errors)} violation(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if not ready:
        print("Research execution Grill is structurally valid but BLOCKED.")
        return 3
    print(f"Research execution Grill passed: {payload['proposal_id']} -> {payload['status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
