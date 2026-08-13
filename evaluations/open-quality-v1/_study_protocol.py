"""Lightweight Open Quality package validator.

Hashes prove package consistency only. They do not authenticate the runner,
blind reviewer, Oracle, commit/tree, or token accounting. This module therefore
never grants pilot advancement or SOP promotion.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
import statistics
import tempfile
from typing import Any


BASELINE_COMMIT = "497b5ba436a1a0392af01db3f2fecd3aa53e95e9"
MANIFEST_VERSION = "open-quality-study-manifest-v1"
OUTCOME_VERSION = "open-quality-outcome-fixtures-v1"
ROUTING_VERSION = "open-quality-routing-v1"
ARMS = ("A", "B", "C")
TASK_CLASSES = (
    "open_product", "research_ideation", "approved_research_execution",
    "simple_bounded_change",
)
PRIMARY_MODES = (
    "fast_path", "option_search", "contract_ready_execution",
    "evidence_closure", "re_contract",
)
OVERLAYS = (
    "browser_walkthrough", "durable_goal", "high_risk_supervision",
    "independent_review", "research_collision", "research_fidelity",
    "visual_critic",
)
USER_DECISIONS = ("not_needed", "defer_until_evidence", "required_now")
HEX = set("0123456789abcdef")

COMMON_RESULT_KEYS = {
    "fixture_id", "fixture_hash", "arm", "replicate", "study_manifest_id",
    "study_manifest_sha256", "treatment_sha256", "run_id", "trace_ref",
    "trace_sha256", "reported_wcu", "reported_wcu_complete",
    "token_usage_ref", "token_usage_sha256", "reported_elapsed_seconds",
    "reported_agents_used", "reported_gpu_count", "reported_external_cost_usd",
    "reported_network_mode",
}
ROUTING_RESULT_KEYS = COMMON_RESULT_KEYS | {"routing"}
OUTCOME_RESULT_KEYS = COMMON_RESULT_KEYS | {
    "materialized_input_sha256", "artifact_ref", "artifact_sha256",
    "oracle_ref", "oracle_sha256", "reported_oracle_pass",
    "blind_assignment_id", "blind_assignment_ref", "blind_assignment_sha256",
    "reported_blind_score", "reported_reviewer_id", "reported_arm_hidden",
    "reported_user_corrections", "reported_agent_rework_cycles",
    "reported_unrequested_artifacts", "reported_unnecessary_agent_spawns",
    "acceptance_changed", "unauthorized_side_effect",
}


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def is_sha256(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64 and set(value) <= HEX
            and value != "0" * 64)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> tuple[list[Any], list[str]]:
    rows: list[Any] = []
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for number, raw in enumerate(handle, 1):
                if not raw.strip():
                    continue
                try:
                    rows.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    errors.append(f"{path}: line {number}: {exc.msg}")
    except OSError as exc:
        errors.append(f"cannot read {path}: {exc}")
    if not rows and not errors:
        errors.append(f"{path}: contains no records")
    return rows, errors


def closed(value: Any, keys: set[str], label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(value, dict):
        return None, [f"{label}: expected object"]
    if set(value) != keys:
        return value, [f"{label}: fields must be exactly {sorted(keys)}"]
    return value, []


def static_fixture_hash(fixture: dict[str, Any]) -> str:
    return canonical_sha256(fixture)


def active_fixtures(stage: str, fixtures: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if stage == "pilot":
        return {key: value for key, value in fixtures.items() if value["pilot"] is True}
    return fixtures


def validate_outcome_fixtures(payload: Any) -> tuple[list[str], dict[str, dict[str, Any]]]:
    errors: list[str] = []
    if not isinstance(payload, dict) or set(payload) != {"version", "fixtures"}:
        return ["outcome fixtures: expected closed version/fixtures object"], {}
    if payload.get("version") != OUTCOME_VERSION:
        errors.append("outcome fixtures.version: drift")
    rows = payload.get("fixtures")
    if not isinstance(rows, list) or len(rows) != 12:
        return errors + ["outcome fixtures: expected exactly 12 rows"], {}
    keys = {
        "id", "task_class", "pilot", "prompt", "prompt_sha256",
        "input_artifact", "input_artifact_sha256", "oracle_contract",
        "oracle_contract_sha256", "blind_rubric", "blind_rubric_sha256",
        "budget", "resource_ceiling",
    }
    fixtures: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    pilots: Counter[str] = Counter()
    for index, row in enumerate(rows):
        label = f"outcome fixtures[{index}]"
        obj, row_errors = closed(row, keys, label)
        errors.extend(row_errors)
        if obj is None:
            continue
        fixture_id = row.get("id")
        if not nonempty(fixture_id) or fixture_id in fixtures:
            errors.append(f"{label}.id: invalid/duplicate")
            continue
        fixtures[fixture_id] = row
        task_class = row.get("task_class")
        if task_class not in TASK_CLASSES:
            errors.append(f"{label}.task_class: invalid")
        else:
            counts[task_class] += 1
            pilots[task_class] += int(row.get("pilot") is True)
        if not isinstance(row.get("pilot"), bool):
            errors.append(f"{label}.pilot: expected boolean")
        for field in ("prompt", "input_artifact", "oracle_contract", "blind_rubric"):
            value = row.get(field)
            if not nonempty(value) or row.get(f"{field}_sha256") != text_sha256(value):
                errors.append(f"{label}.{field}: text/hash mismatch")
        budget = row.get("budget")
        if (not isinstance(budget, dict)
                or set(budget) != {"max_wcu", "max_elapsed_seconds"}
                or any(not finite(value) or value <= 0 for value in budget.values())):
            errors.append(f"{label}.budget: invalid")
        ceiling = row.get("resource_ceiling")
        if (not isinstance(ceiling, dict) or set(ceiling) != {
                "network", "max_agents", "max_gpu_count", "max_external_cost_usd"}):
            errors.append(f"{label}.resource_ceiling: invalid")
        else:
            if ceiling.get("network") not in {"disabled", "fixture_only"}:
                errors.append(f"{label}.resource_ceiling.network: invalid")
            for field in ("max_agents", "max_gpu_count"):
                minimum = 1 if field == "max_agents" else 0
                if (not isinstance(ceiling.get(field), int)
                        or isinstance(ceiling.get(field), bool)
                        or ceiling[field] < minimum):
                    errors.append(f"{label}.resource_ceiling.{field}: invalid")
            cost = ceiling.get("max_external_cost_usd")
            if not finite(cost) or cost < 0:
                errors.append(f"{label}.resource_ceiling.max_external_cost_usd: invalid")
    for task_class in TASK_CLASSES:
        if counts[task_class] != 3:
            errors.append(f"outcome fixtures: {task_class} must have 3")
        if pilots[task_class] != 1:
            errors.append(f"outcome fixtures: {task_class} must have 1 pilot row")
    return errors, fixtures


def validate_study_schema(schema: Any) -> list[str]:
    expected = {
        "manifest_version", "study_manifest_id", "study_stage",
        "candidate_frozen_before_results", "arms", "runtime", "budget",
        "resource_ceiling", "randomization", "fixtures",
    }
    if not isinstance(schema, dict):
        return ["study schema: expected object"]
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        return ["study schema: root must be closed"]
    if (set(schema.get("required", [])) != expected
            or set(schema.get("properties", {})) != expected):
        return ["study schema: root fields drift"]
    return []


def manifest_template(routing: dict[str, dict[str, Any]], outcomes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    routing_rows = [{"fixture_id": key, "fixture_hash": static_fixture_hash(value)}
                    for key, value in sorted(routing.items())]
    outcome_rows = []
    for fixture_id, fixture in sorted(outcomes.items()):
        outcome_rows.append({
            "fixture_id": fixture_id,
            "fixture_hash": static_fixture_hash(fixture),
            "prompt_sha256": fixture["prompt_sha256"],
            "oracle_contract_sha256": fixture["oracle_contract_sha256"],
            "blind_rubric_sha256": fixture["blind_rubric_sha256"],
            "materialized_input_ref": f"REPLACE/inputs/{fixture_id}.bundle",
            "materialized_input_sha256": "REPLACE_WITH_SHA256",
        })
    return {
        "manifest_version": MANIFEST_VERSION,
        "study_manifest_id": "REPLACE_WITH_STUDY_ID",
        "study_stage": "pilot",
        "candidate_frozen_before_results": True,
        "arms": {
            "A": {"treatment": "raw_platform_only", "reported_repository_commit": None, "treatment_ref": "REPLACE/A.bundle", "treatment_sha256": "REPLACE_WITH_SHA256"},
            "B": {"treatment": "main_at_497b5ba", "reported_repository_commit": BASELINE_COMMIT, "treatment_ref": "REPLACE/B.bundle", "treatment_sha256": "REPLACE_WITH_SHA256"},
            "C": {"treatment": "candidate", "reported_repository_commit": "REPLACE_WITH_40_HEX", "reported_candidate_tree_sha256": "REPLACE_WITH_SHA256", "treatment_ref": "REPLACE/C.bundle", "treatment_sha256": "REPLACE_WITH_SHA256"},
        },
        "runtime": {"reported_model": "REPLACE", "reported_build": "REPLACE", "reported_reasoning_effort": "REPLACE", "permissions_ref": "REPLACE/permissions.json", "permissions_sha256": "REPLACE_WITH_SHA256"},
        "budget": {"max_total_reported_wcu": 1, "max_total_reported_run_seconds": 1, "max_reported_external_cost_usd": 0},
        "resource_ceiling": {"network": "fixture_only", "max_agents": 1, "max_gpu_count": 0},
        "randomization": {"reported_method": "blocked_randomization", "assignment_plan_ref": "REPLACE/assignment-plan.json", "assignment_plan_sha256": "REPLACE_WITH_SHA256"},
        "fixtures": {"routing": routing_rows, "outcome": outcome_rows},
    }


def checked_file(root: Path, path: Path, label: str) -> tuple[Path | None, list[str]]:
    """Resolve one package file without accepting symlinked path components."""
    try:
        lexical_root = Path(os.path.abspath(root))
        for candidate in (lexical_root, *lexical_root.parents):
            if candidate == Path(candidate.anchor):
                break
            if stat.S_ISLNK(candidate.lstat().st_mode):
                return None, [f"{label}: symlink evidence root forbidden"]
        lexical_path = Path(os.path.abspath(path))
        relative = lexical_path.relative_to(lexical_root)
        resolved_root = lexical_root.resolve(strict=True)
        current = lexical_root
        for part in relative.parts:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                return None, [f"{label}: symlink path forbidden"]
        resolved = lexical_path.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError, RuntimeError) as exc:
        return None, [f"{label}: must be a file inside evidence root: {exc}"]
    if not resolved.is_file():
        return None, [f"{label}: expected regular file"]
    return resolved, []


def safe_file(root: Path, ref: Any, digest: Any, label: str) -> tuple[Path | None, list[str]]:
    if not nonempty(ref) or not is_sha256(digest) or "\\" in ref or ":" in ref:
        return None, [f"{label}: invalid relative ref/hash"]
    pure = PurePosixPath(ref)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        return None, [f"{label}: path escape forbidden"]
    path, errors = checked_file(root, root / Path(*pure.parts), label)
    if errors or path is None:
        return None, errors
    return path, [] if file_sha256(path) == digest else [f"{label}: hash mismatch"]


class Paths:
    def __init__(self, root: Path) -> None:
        lexical_root = Path(os.path.abspath(root))
        for candidate in (lexical_root, *lexical_root.parents):
            if candidate == Path(candidate.anchor):
                break
            if stat.S_ISLNK(candidate.lstat().st_mode):
                raise ValueError("symlink evidence root forbidden")
        self.root = root.resolve(strict=True)
        self.used: dict[str, str] = {}

    def add(self, path: Path | None, label: str) -> list[str]:
        if path is None:
            return []
        try:
            canonical = path.resolve(strict=True).relative_to(self.root).as_posix()
        except (OSError, ValueError, RuntimeError) as exc:
            return [f"{label}: cannot canonicalize inside evidence root: {exc}"]
        if canonical in self.used:
            return [f"{label}: path reused from {self.used[canonical]}"]
        self.used[canonical] = label
        return []


def validate_manifest(path: Path, root: Path, stage: str,
                      routing: dict[str, dict[str, Any]],
                      outcomes: dict[str, dict[str, Any]],
                      paths: Paths) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    try:
        resolved_root = root.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
        resolved_path.relative_to(resolved_root)
        manifest = load_json(resolved_path)
        manifest_sha = file_sha256(resolved_path)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"manifest must be valid JSON inside evidence root: {exc}"], {}
    keys = {
        "manifest_version", "study_manifest_id", "study_stage",
        "candidate_frozen_before_results", "arms", "runtime", "budget",
        "resource_ceiling", "randomization", "fixtures",
    }
    obj, row_errors = closed(manifest, keys, "manifest")
    errors.extend(row_errors)
    if obj is None:
        return errors, {}
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        errors.append("manifest.version: drift")
    if not nonempty(manifest.get("study_manifest_id")):
        errors.append("manifest.study_manifest_id: invalid")
    if manifest.get("study_stage") != stage:
        errors.append("manifest.study_stage: CLI mismatch")
    if manifest.get("candidate_frozen_before_results") is not True:
        errors.append("manifest: candidate not frozen")

    arm_context: dict[str, Any] = {}
    arms, arm_errors = closed(manifest.get("arms"), set(ARMS), "manifest.arms")
    errors.extend(arm_errors)
    if arms:
        for arm in ARMS:
            arm_keys = {"treatment", "reported_repository_commit", "treatment_ref", "treatment_sha256"}
            if arm == "C":
                arm_keys.add("reported_candidate_tree_sha256")
            row, item_errors = closed(arms.get(arm), arm_keys, f"manifest.arms.{arm}")
            errors.extend(item_errors)
            if row is None:
                continue
            if row.get("treatment") != {"A": "raw_platform_only", "B": "main_at_497b5ba", "C": "candidate"}[arm]:
                errors.append(f"manifest.arms.{arm}.treatment: drift")
            commit = row.get("reported_repository_commit")
            if arm == "A" and commit is not None:
                errors.append("manifest.arms.A.reported_repository_commit: must be null")
            if arm == "B" and commit != BASELINE_COMMIT:
                errors.append("manifest.arms.B.reported_repository_commit: baseline drift")
            if arm == "C":
                if not isinstance(commit, str) or len(commit) != 40 or not set(commit) <= HEX:
                    errors.append("manifest.arms.C.reported_repository_commit: invalid shape")
                if not is_sha256(row.get("reported_candidate_tree_sha256")):
                    errors.append("manifest.arms.C.reported_candidate_tree_sha256: invalid")
            treatment_path, file_errors = safe_file(root, row.get("treatment_ref"), row.get("treatment_sha256"), f"manifest.arms.{arm}.treatment")
            errors.extend(file_errors)
            errors.extend(paths.add(treatment_path, f"manifest.arms.{arm}.treatment_ref"))
            arm_context[arm] = row

    runtime_keys = {"reported_model", "reported_build", "reported_reasoning_effort", "permissions_ref", "permissions_sha256"}
    runtime, runtime_errors = closed(manifest.get("runtime"), runtime_keys, "manifest.runtime")
    errors.extend(runtime_errors)
    if runtime:
        for field in ("reported_model", "reported_build", "reported_reasoning_effort"):
            if not nonempty(runtime.get(field)):
                errors.append(f"manifest.runtime.{field}: invalid")
        permissions_path, file_errors = safe_file(root, runtime.get("permissions_ref"), runtime.get("permissions_sha256"), "manifest.runtime.permissions")
        errors.extend(file_errors)
        errors.extend(paths.add(permissions_path, "manifest.runtime.permissions_ref"))

    budget_keys = {"max_total_reported_wcu", "max_total_reported_run_seconds", "max_reported_external_cost_usd"}
    budget, budget_errors = closed(manifest.get("budget"), budget_keys, "manifest.budget")
    errors.extend(budget_errors)
    if budget:
        for field in budget_keys:
            value = budget.get(field)
            if not finite(value) or value < 0 or (field != "max_reported_external_cost_usd" and value == 0):
                errors.append(f"manifest.budget.{field}: invalid")

    resource_keys = {"network", "max_agents", "max_gpu_count"}
    resources, resource_errors = closed(manifest.get("resource_ceiling"), resource_keys, "manifest.resource_ceiling")
    errors.extend(resource_errors)
    if resources:
        if resources.get("network") not in {"disabled", "fixture_only"}:
            errors.append("manifest.resource_ceiling.network: invalid")
        for field in ("max_agents", "max_gpu_count"):
            minimum = 1 if field == "max_agents" else 0
            if (not isinstance(resources.get(field), int)
                    or isinstance(resources.get(field), bool)
                    or resources[field] < minimum):
                errors.append(f"manifest.resource_ceiling.{field}: invalid")

    random_keys = {"reported_method", "assignment_plan_ref", "assignment_plan_sha256"}
    randomization, random_errors = closed(manifest.get("randomization"), random_keys, "manifest.randomization")
    errors.extend(random_errors)
    assignment_plan: dict[tuple[str, int, str], str] = {}
    if randomization:
        plan_path, file_errors = safe_file(root, randomization.get("assignment_plan_ref"), randomization.get("assignment_plan_sha256"), "manifest.randomization.assignment_plan")
        errors.extend(file_errors)
        errors.extend(paths.add(plan_path, "manifest.randomization.assignment_plan_ref"))

    active_routing = active_fixtures(stage, routing)
    active_outcomes = active_fixtures(stage, outcomes)
    if randomization and plan_path is not None:
        try:
            plan = load_json(plan_path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"manifest.randomization.assignment_plan: invalid JSON: {exc}")
            plan = None
        plan_obj, plan_errors = closed(plan, {"schema_version", "stage", "outcome_slots"}, "assignment plan")
        errors.extend(plan_errors)
        if plan_obj is not None:
            if plan.get("schema_version") != "open-quality-assignment-plan-v1":
                errors.append("assignment plan.schema_version: drift")
            if plan.get("stage") != stage:
                errors.append("assignment plan.stage: manifest mismatch")
            rows = plan.get("outcome_slots")
            reps = (1,) if stage == "pilot" else (1, 2, 3)
            expected_slots = {(fixture_id, rep) for fixture_id in active_outcomes for rep in reps}
            observed_slots: set[tuple[str, int]] = set()
            assignment_ids: set[str] = set()
            if not isinstance(rows, list):
                errors.append("assignment plan.outcome_slots: expected list")
            else:
                for index, row in enumerate(rows):
                    label = f"assignment plan.outcome_slots[{index}]"
                    item, item_errors = closed(row, {"fixture_id", "replicate", "concealed_order", "assignments"}, label)
                    errors.extend(item_errors)
                    if item is None:
                        continue
                    fixture_id, replicate = row.get("fixture_id"), row.get("replicate")
                    if (not isinstance(fixture_id, str)
                            or not isinstance(replicate, int)
                            or isinstance(replicate, bool)):
                        errors.append(f"{label}: fixture_id/replicate types invalid")
                        continue
                    slot = (fixture_id, replicate)
                    if slot not in expected_slots or slot in observed_slots:
                        errors.append(f"{label}: unexpected/duplicate slot")
                        continue
                    observed_slots.add(slot)
                    order = row.get("concealed_order")
                    assignments = row.get("assignments")
                    if (not isinstance(order, list)
                            or any(not isinstance(value, str) for value in order)
                            or len(order) != 3 or len(set(order)) != 3):
                        errors.append(f"{label}.concealed_order: expected 3 unique IDs")
                        continue
                    assignment_obj, assignment_errors = closed(assignments, set(ARMS), f"{label}.assignments")
                    errors.extend(assignment_errors)
                    if (assignment_obj is None
                            or any(not isinstance(value, str) for value in assignments.values())
                            or set(order) != set(assignments.values())):
                        errors.append(f"{label}: concealed order must permute A/B/C assignment IDs")
                        continue
                    for arm, assignment_id in assignments.items():
                        if not nonempty(assignment_id) or assignment_id in assignment_ids:
                            errors.append(f"{label}.assignments.{arm}: invalid/duplicate")
                        else:
                            assignment_ids.add(assignment_id)
                            assignment_plan[(slot[0], slot[1], arm)] = assignment_id
                if observed_slots != expected_slots:
                    errors.append("assignment plan: incomplete outcome slots")
    bindings, binding_errors = closed(manifest.get("fixtures"), {"routing", "outcome"}, "manifest.fixtures")
    errors.extend(binding_errors)
    routing_bindings: dict[str, Any] = {}
    outcome_bindings: dict[str, Any] = {}
    if bindings:
        for suite, fixtures, target in (("routing", active_routing, routing_bindings),
                                        ("outcome", active_outcomes, outcome_bindings)):
            rows = bindings.get(suite)
            if not isinstance(rows, list):
                errors.append(f"manifest.fixtures.{suite}: expected list")
                continue
            item_keys = {"fixture_id", "fixture_hash"}
            if suite == "outcome":
                item_keys |= {"prompt_sha256", "oracle_contract_sha256", "blind_rubric_sha256", "materialized_input_ref", "materialized_input_sha256"}
            for index, row in enumerate(rows):
                label = f"manifest.fixtures.{suite}[{index}]"
                item, item_errors = closed(row, item_keys, label)
                errors.extend(item_errors)
                if item is None:
                    continue
                fixture_id = row.get("fixture_id")
                if fixture_id not in fixtures or fixture_id in target:
                    errors.append(f"{label}.fixture_id: unknown/duplicate for stage")
                    continue
                fixture = fixtures[fixture_id]
                if row.get("fixture_hash") != static_fixture_hash(fixture):
                    errors.append(f"{label}.fixture_hash: static drift")
                if suite == "outcome":
                    for field in ("prompt_sha256", "oracle_contract_sha256", "blind_rubric_sha256"):
                        if row.get(field) != fixture[field]:
                            errors.append(f"{label}.{field}: static drift")
                    input_path, file_errors = safe_file(root, row.get("materialized_input_ref"), row.get("materialized_input_sha256"), f"{label}.materialized_input")
                    errors.extend(file_errors)
                    errors.extend(paths.add(input_path, f"{label}.materialized_input_ref"))
                target[fixture_id] = row
            if set(target) != set(fixtures):
                errors.append(f"manifest.fixtures.{suite}: incomplete/excess stage binding")
    context = {
        "manifest": manifest, "manifest_sha256": manifest_sha, "root": resolved_root,
        "arms": arm_context, "budget": budget or {}, "resources": resources or {},
        "routing": routing_bindings, "outcome": outcome_bindings,
        "active_routing": active_routing, "active_outcomes": active_outcomes,
        "assignment_plan": assignment_plan,
        "paths": paths,
    }
    return errors, context


def validate_routing_output(value: Any, fixture_id: str, label: str) -> list[str]:
    keys = {"schema_version", "case_id", "primary_mode", "overlays", "user_decision", "decisive_facts", "next_action"}
    row, errors = closed(value, keys, label)
    if row is None:
        return errors
    if row.get("schema_version") != ROUTING_VERSION or row.get("case_id") != fixture_id:
        errors.append(f"{label}: schema/case mismatch")
    if row.get("primary_mode") not in PRIMARY_MODES:
        errors.append(f"{label}.primary_mode: invalid")
    overlays = row.get("overlays")
    if (not isinstance(overlays, list)
            or any(not isinstance(item, str) for item in overlays)
            or len(overlays) != len(set(overlays))
            or set(overlays) - set(OVERLAYS)):
        errors.append(f"{label}.overlays: invalid")
    if row.get("user_decision") not in USER_DECISIONS:
        errors.append(f"{label}.user_decision: invalid")
    if not isinstance(row.get("decisive_facts"), list) or not row["decisive_facts"]:
        errors.append(f"{label}.decisive_facts: invalid")
    if not nonempty(row.get("next_action")):
        errors.append(f"{label}.next_action: invalid")
    return errors


def validate_results(routing_rows: list[Any], outcome_rows: list[Any], stage: str,
                     context: dict[str, Any], outcomes: dict[str, dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    errors: list[str] = []
    valid_routing: list[dict[str, Any]] = []
    valid_outcomes: list[dict[str, Any]] = []
    reps = (1,) if stage == "pilot" else (1, 2, 3)
    expected = {
        "routing": {(key, arm, rep) for key in context["active_routing"] for arm in ARMS for rep in reps},
        "outcome": {(key, arm, rep) for key in context["active_outcomes"] for arm in ARMS for rep in reps},
    }
    observed = {"routing": set(), "outcome": set()}
    paths = context["paths"]
    run_ids: set[str] = set()
    assignment_ids: set[str] = set()

    def visit(row: Any, index: int, suite: str) -> None:
        label = f"{suite} results[{index}]"
        keys = ROUTING_RESULT_KEYS if suite == "routing" else OUTCOME_RESULT_KEYS
        obj, row_errors = closed(row, keys, label)
        errors.extend(row_errors)
        if obj is None:
            return
        fixture_id, arm, rep = row.get("fixture_id"), row.get("arm"), row.get("replicate")
        if (not isinstance(fixture_id, str) or not isinstance(arm, str)
                or not isinstance(rep, int) or isinstance(rep, bool)):
            errors.append(f"{label}: fixture_id/arm/replicate types invalid")
            return
        slot = (fixture_id, arm, rep)
        if slot not in expected[suite] or slot in observed[suite]:
            errors.append(f"{label}: slot outside design or duplicate {slot}")
            return
        observed[suite].add(slot)
        binding = context[suite][fixture_id]
        values = {
            "fixture_hash": binding["fixture_hash"],
            "study_manifest_id": context["manifest"]["study_manifest_id"],
            "study_manifest_sha256": context["manifest_sha256"],
            "treatment_sha256": context["arms"][arm]["treatment_sha256"],
        }
        for field, wanted in values.items():
            if row.get(field) != wanted:
                errors.append(f"{label}.{field}: manifest mismatch")
        run_id = row.get("run_id")
        if not nonempty(run_id) or run_id in run_ids:
            errors.append(f"{label}.run_id: invalid/duplicate")
        else:
            run_ids.add(run_id)
        for ref_field, hash_field in (("trace_ref", "trace_sha256"), ("token_usage_ref", "token_usage_sha256")):
            evidence_path, file_errors = safe_file(context["root"], row.get(ref_field), row.get(hash_field), f"{label}.{ref_field}")
            errors.extend(file_errors)
            errors.extend(paths.add(evidence_path, f"{label}.{ref_field}"))
        if row.get("reported_wcu_complete") is not True:
            errors.append(f"{label}.reported_wcu_complete: false")
        for field in ("reported_wcu", "reported_elapsed_seconds"):
            if not finite(row.get(field)) or row[field] <= 0:
                errors.append(f"{label}.{field}: invalid")
        for field in ("reported_agents_used", "reported_gpu_count"):
            minimum = 1 if field == "reported_agents_used" else 0
            if (not isinstance(row.get(field), int)
                    or isinstance(row.get(field), bool)
                    or row[field] < minimum):
                errors.append(f"{label}.{field}: invalid")
        if (not finite(row.get("reported_external_cost_usd"))
                or row["reported_external_cost_usd"] < 0):
            errors.append(f"{label}.reported_external_cost_usd: invalid")
        resources = context["resources"]
        if row.get("reported_network_mode") not in {"disabled", resources.get("network")}:
            errors.append(f"{label}.reported_network_mode: exceeds ceiling")
        if ((isinstance(row.get("reported_agents_used"), int)
             and not isinstance(row.get("reported_agents_used"), bool)
             and row["reported_agents_used"] > resources.get("max_agents", -1))
                or (isinstance(row.get("reported_gpu_count"), int)
                    and not isinstance(row.get("reported_gpu_count"), bool)
                    and row["reported_gpu_count"] > resources.get("max_gpu_count", -1))):
            errors.append(f"{label}: exceeds study resource ceiling")
        if suite == "routing":
            errors.extend(validate_routing_output(row.get("routing"), fixture_id, f"{label}.routing"))
            valid_routing.append(row)
            return
        fixture = outcomes[fixture_id]
        if row.get("materialized_input_sha256") != binding["materialized_input_sha256"]:
            errors.append(f"{label}.materialized_input_sha256: manifest mismatch")
        for ref_field, hash_field in (("artifact_ref", "artifact_sha256"), ("oracle_ref", "oracle_sha256"), ("blind_assignment_ref", "blind_assignment_sha256")):
            evidence_path, file_errors = safe_file(context["root"], row.get(ref_field), row.get(hash_field), f"{label}.{ref_field}")
            errors.extend(file_errors)
            errors.extend(paths.add(evidence_path, f"{label}.{ref_field}"))
        assignment = row.get("blind_assignment_id")
        if not nonempty(assignment) or assignment in assignment_ids:
            errors.append(f"{label}.blind_assignment_id: invalid/duplicate")
        else:
            assignment_ids.add(assignment)
        if assignment != context["assignment_plan"].get((fixture_id, rep, arm)):
            errors.append(f"{label}.blind_assignment_id: frozen plan mismatch")
        for field in ("reported_oracle_pass", "reported_arm_hidden", "acceptance_changed", "unauthorized_side_effect"):
            if not isinstance(row.get(field), bool):
                errors.append(f"{label}.{field}: expected boolean")
        if row.get("acceptance_changed") is not False or row.get("unauthorized_side_effect") is not False:
            errors.append(f"{label}: acceptance changed or unauthorized side effect")
        if (not finite(row.get("reported_blind_score"))
                or not 0 <= row["reported_blind_score"] <= 10):
            errors.append(f"{label}.reported_blind_score: invalid")
        if not nonempty(row.get("reported_reviewer_id")):
            errors.append(f"{label}.reported_reviewer_id: invalid")
        for field in ("reported_user_corrections", "reported_agent_rework_cycles",
                      "reported_unrequested_artifacts", "reported_unnecessary_agent_spawns"):
            if (not isinstance(row.get(field), int)
                    or isinstance(row.get(field), bool)
                    or row[field] < 0):
                errors.append(f"{label}.{field}: invalid")
        budget = fixture["budget"]
        if ((finite(row.get("reported_wcu"))
             and row["reported_wcu"] > budget["max_wcu"])
                or (finite(row.get("reported_elapsed_seconds"))
                    and row["reported_elapsed_seconds"] > budget["max_elapsed_seconds"])):
            errors.append(f"{label}: fixture budget exceeded")
        ceiling = fixture["resource_ceiling"]
        if row.get("reported_network_mode") not in {"disabled", ceiling["network"]}:
            errors.append(f"{label}.reported_network_mode: exceeds fixture resource ceiling")
        if ((isinstance(row.get("reported_agents_used"), int)
             and not isinstance(row.get("reported_agents_used"), bool)
             and row["reported_agents_used"] > ceiling["max_agents"])
                or (isinstance(row.get("reported_gpu_count"), int)
                    and not isinstance(row.get("reported_gpu_count"), bool)
                    and row["reported_gpu_count"] > ceiling["max_gpu_count"])
                or (finite(row.get("reported_external_cost_usd"))
                    and row["reported_external_cost_usd"] > ceiling["max_external_cost_usd"])):
            errors.append(f"{label}: fixture resource ceiling exceeded")
        valid_outcomes.append(row)

    for index, row in enumerate(routing_rows):
        visit(row, index, "routing")
    for index, row in enumerate(outcome_rows):
        visit(row, index, "outcome")
    for suite in ("routing", "outcome"):
        if observed[suite] != expected[suite]:
            errors.append(f"{suite} results: missing {len(expected[suite] - observed[suite])} slots")
    all_rows = [*valid_routing, *valid_outcomes]
    totals = {
        "reported_wcu": sum(float(row.get("reported_wcu", 0)) for row in all_rows if finite(row.get("reported_wcu"))),
        "reported_run_seconds": sum(float(row.get("reported_elapsed_seconds", 0)) for row in all_rows if finite(row.get("reported_elapsed_seconds"))),
        "reported_external_cost_usd": sum(float(row.get("reported_external_cost_usd", 0)) for row in all_rows if finite(row.get("reported_external_cost_usd"))),
    }
    for metric, limit in (("reported_wcu", "max_total_reported_wcu"), ("reported_run_seconds", "max_total_reported_run_seconds"), ("reported_external_cost_usd", "max_reported_external_cost_usd")):
        if totals[metric] > context["budget"].get(limit, -1):
            errors.append(f"study {metric}: budget exceeded")
    integrity = {
        "expected_routing_records": len(expected["routing"]),
        "observed_routing_records": len(routing_rows),
        "expected_outcome_records": len(expected["outcome"]),
        "observed_outcome_records": len(outcome_rows),
        "unique_bound_paths": len(paths.used),
        "reported_totals": totals,
    }
    return errors, valid_routing, valid_outcomes, integrity


def reported_metrics(routing_rows: list[dict[str, Any]], outcome_rows: list[dict[str, Any]],
                     routing_cases: dict[str, dict[str, Any]], outcomes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for arm in ARMS:
        routes = [row for row in routing_rows if row["arm"] == arm]
        delivered = [row for row in outcome_rows if row["arm"] == arm]
        exact = sum(
            row["routing"]["primary_mode"] == routing_cases[row["fixture_id"]]["expected"]["primary_mode"]
            and set(row["routing"]["overlays"]) == set(routing_cases[row["fixture_id"]]["expected"]["overlays"])
            and row["routing"]["user_decision"] == routing_cases[row["fixture_id"]]["expected"]["user_decision"]
            for row in routes
        )
        by_fixture: defaultdict[str, list[float]] = defaultdict(list)
        for row in delivered:
            by_fixture[row["fixture_id"]].append(float(row["reported_blind_score"]))
        dispersions = [statistics.pstdev(values) for values in by_fixture.values() if len(values) > 1]
        report[arm] = {
            "reported_routing_exact_accuracy": exact / len(routes) if routes else None,
            "reported_oracle_pass_rate": sum(bool(row["reported_oracle_pass"]) for row in delivered) / len(delivered) if delivered else None,
            "reported_blind_quality_mean": statistics.fmean(float(row["reported_blind_score"]) for row in delivered) if delivered else None,
            "reported_within_fixture_quality_sd": statistics.fmean(dispersions) if dispersions else None,
            "reported_total_wcu": sum(float(row["reported_wcu"]) for row in routes + delivered),
            "reported_total_rework": sum(row["reported_user_corrections"] + row["reported_agent_rework_cycles"] for row in delivered),
            "reported_simple_unrequested_artifacts": sum(row["reported_unrequested_artifacts"] for row in delivered if outcomes[row["fixture_id"]]["task_class"] == "simple_bounded_change"),
        }
    return report


def run_package(stage: str, manifest_path: Path, root: Path,
                routing_results_path: Path, outcome_results_path: Path,
                routing: dict[str, dict[str, Any]], outcomes: dict[str, dict[str, Any]]) -> tuple[int, dict[str, Any]]:
    try:
        paths = Paths(root)
    except (OSError, RuntimeError, ValueError) as exc:
        return 1, {
            "decision": "PACKAGE_INVALID", "promotion_eligible": False,
            "errors": [f"evidence root: cannot resolve: {exc}"],
        }
    path_errors: list[str] = []
    controls: dict[str, Path] = {}
    for package_path, label in (
        (manifest_path, "study manifest"),
        (routing_results_path, "routing results"),
        (outcome_results_path, "outcome results"),
    ):
        resolved, file_errors = checked_file(root, package_path, label)
        path_errors.extend(file_errors)
        path_errors.extend(paths.add(resolved, label))
        if resolved is not None:
            controls[label] = resolved
    if path_errors:
        return 1, {
            "decision": "PACKAGE_INVALID", "promotion_eligible": False,
            "errors": path_errors,
        }
    manifest_errors, context = validate_manifest(
        controls["study manifest"], root, stage, routing, outcomes, paths,
    )
    routing_rows, route_load_errors = load_jsonl(controls["routing results"])
    outcome_rows, outcome_load_errors = load_jsonl(controls["outcome results"])
    errors = [*manifest_errors, *path_errors, *route_load_errors, *outcome_load_errors]
    if errors:
        return 1, {"decision": "PACKAGE_INVALID", "promotion_eligible": False, "errors": errors}
    row_errors, valid_routes, valid_outcomes, integrity = validate_results(routing_rows, outcome_rows, stage, context, outcomes)
    if row_errors:
        return 1, {"decision": "PACKAGE_INVALID", "promotion_eligible": False, "integrity": integrity, "errors": row_errors}
    return 0, {
        "decision": "PACKAGE_COMPLETE_UNVERIFIED",
        "promotion_eligible": False,
        "integrity": {**integrity, "package_consistent": True},
        "metrics_status": "DERIVED_FROM_UNVERIFIED_REPORTED_RECEIPTS",
        "reported_metrics": reported_metrics(valid_routes, valid_outcomes, context["active_routing"], outcomes),
        "unverified_claims": [
            "treatment commit/tree identity", "runner and arm isolation",
            "token/WCU agreement with raw trace", "Oracle independence/execution",
            "blindness, reviewer identity, and assignment randomness",
        ],
        "promotion_authority": "INDEPENDENT_SIGNED_EVALUATOR_OR_HUMAN_REQUIRED",
    }


def run_self_test(routing: dict[str, dict[str, Any]], outcomes: dict[str, dict[str, Any]]) -> dict[str, bool]:
    """A fully synthetic consistent package must remain unverified."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        def write(ref: str, content: bytes) -> str:
            path = root / ref
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return file_sha256(path)

        treatment = {}
        for arm in ARMS:
            ref = f"treatment/{arm}.bundle"
            treatment[arm] = (ref, write(ref, f"treatment {arm}".encode()))
        permissions_ref, assignment_ref = "study/permissions.json", "study/assignments.json"
        permissions_sha = write(permissions_ref, b"{}")
        assignment_payload = {
            "schema_version": "open-quality-assignment-plan-v1",
            "stage": "promotion",
            "outcome_slots": [
                {
                    "fixture_id": fixture_id,
                    "replicate": rep,
                    "concealed_order": [
                        f"assignment-{fixture_id}-{arm}-{rep}" for arm in ARMS
                    ],
                    "assignments": {
                        arm: f"assignment-{fixture_id}-{arm}-{rep}" for arm in ARMS
                    },
                }
                for rep in (1, 2, 3)
                for fixture_id in outcomes
            ],
        }
        assignment_sha = write(
            assignment_ref,
            json.dumps(assignment_payload, sort_keys=True).encode("utf-8"),
        )
        manifest = manifest_template(routing, outcomes)
        manifest.update({
            "study_manifest_id": "package-self-check", "study_stage": "promotion",
            "arms": {
                "A": {"treatment": "raw_platform_only", "reported_repository_commit": None, "treatment_ref": treatment["A"][0], "treatment_sha256": treatment["A"][1]},
                "B": {"treatment": "main_at_497b5ba", "reported_repository_commit": BASELINE_COMMIT, "treatment_ref": treatment["B"][0], "treatment_sha256": treatment["B"][1]},
                "C": {"treatment": "candidate", "reported_repository_commit": "c" * 40, "reported_candidate_tree_sha256": "d" * 64, "treatment_ref": treatment["C"][0], "treatment_sha256": treatment["C"][1]},
            },
            "runtime": {"reported_model": "model", "reported_build": "build", "reported_reasoning_effort": "high", "permissions_ref": permissions_ref, "permissions_sha256": permissions_sha},
            "budget": {"max_total_reported_wcu": 1_000_000, "max_total_reported_run_seconds": 1_000_000, "max_reported_external_cost_usd": 0},
            "resource_ceiling": {"network": "fixture_only", "max_agents": 4, "max_gpu_count": 1},
            "randomization": {"reported_method": "blocked_randomization", "assignment_plan_ref": assignment_ref, "assignment_plan_sha256": assignment_sha},
        })
        for binding in manifest["fixtures"]["outcome"]:
            ref = f"inputs/{binding['fixture_id']}.bundle"
            binding["materialized_input_ref"] = ref
            binding["materialized_input_sha256"] = write(ref, binding["fixture_id"].encode())
        manifest_path = root / "study/manifest.json"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        manifest_sha = file_sha256(manifest_path)
        route_rows: list[dict[str, Any]] = []
        outcome_rows: list[dict[str, Any]] = []

        def common(fixture_id: str, fixture_hash: str, arm: str, rep: int, suite: str) -> dict[str, Any]:
            run_id = f"run-{suite}-{fixture_id}-{arm}-{rep}"
            trace_ref, token_ref = f"runs/{run_id}/trace.raw", f"runs/{run_id}/tokens.json"
            return {
                "fixture_id": fixture_id, "fixture_hash": fixture_hash, "arm": arm,
                "replicate": rep, "study_manifest_id": manifest["study_manifest_id"],
                "study_manifest_sha256": manifest_sha, "treatment_sha256": treatment[arm][1],
                "run_id": run_id, "trace_ref": trace_ref, "trace_sha256": write(trace_ref, run_id.encode()),
                "reported_wcu": 1000, "reported_wcu_complete": True,
                "token_usage_ref": token_ref, "token_usage_sha256": write(token_ref, b"{}"),
                "reported_elapsed_seconds": 10, "reported_agents_used": 1,
                "reported_gpu_count": 0, "reported_external_cost_usd": 0,
                "reported_network_mode": "disabled",
            }

        for rep in (1, 2, 3):
            for fixture_id, fixture in routing.items():
                for arm in ARMS:
                    row = common(fixture_id, static_fixture_hash(fixture), arm, rep, "routing")
                    gold = fixture["expected"]
                    row["routing"] = {"schema_version": ROUTING_VERSION, "case_id": fixture_id, "primary_mode": gold["primary_mode"], "overlays": gold["overlays"], "user_decision": gold["user_decision"], "decisive_facts": ["reported"], "next_action": "reported"}
                    route_rows.append(row)
            for fixture_id, fixture in outcomes.items():
                for arm in ARMS:
                    row = common(fixture_id, static_fixture_hash(fixture), arm, rep, "outcome")
                    run_id = row["run_id"]
                    artifact_ref, oracle_ref, blind_ref = f"runs/{run_id}/artifact.bin", f"runs/{run_id}/oracle.json", f"runs/{run_id}/blind.json"
                    row.update({
                        "materialized_input_sha256": next(x for x in manifest["fixtures"]["outcome"] if x["fixture_id"] == fixture_id)["materialized_input_sha256"],
                        "artifact_ref": artifact_ref,
                        "artifact_sha256": write(artifact_ref, f"same-{fixture_id}-{rep}".encode()),
                        "oracle_ref": oracle_ref, "oracle_sha256": write(oracle_ref, b"{}"),
                        "reported_oracle_pass": True,
                        "blind_assignment_id": f"assignment-{fixture_id}-{arm}-{rep}",
                        "blind_assignment_ref": blind_ref, "blind_assignment_sha256": write(blind_ref, b"{}"),
                        "reported_blind_score": 9 if arm == "C" else 8,
                        "reported_reviewer_id": "reviewer", "reported_arm_hidden": True,
                        "reported_user_corrections": 0, "reported_agent_rework_cycles": 0,
                        "reported_unrequested_artifacts": 0, "reported_unnecessary_agent_spawns": 0,
                        "acceptance_changed": False, "unauthorized_side_effect": False,
                    })
                    outcome_rows.append(row)
        route_path, outcome_path = root / "study/routing.jsonl", root / "study/outcome.jsonl"

        def dump(path: Path, rows: list[dict[str, Any]]) -> None:
            path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

        dump(route_path, route_rows)
        dump(outcome_path, outcome_rows)
        code, complete = run_package("promotion", manifest_path, root, route_path, outcome_path, routing, outcomes)
        missing_path = root / "study/missing.jsonl"
        dump(missing_path, route_rows[:-1])
        missing_code, _ = run_package("promotion", manifest_path, root, missing_path, outcome_path, routing, outcomes)
        mismatch = [dict(row) for row in route_rows]
        mismatch[0]["study_manifest_sha256"] = "e" * 64
        mismatch_path = root / "study/mismatch.jsonl"
        dump(mismatch_path, mismatch)
        mismatch_code, _ = run_package("promotion", manifest_path, root, mismatch_path, outcome_path, routing, outcomes)
        duplicate = [dict(row) for row in outcome_rows]
        duplicate[1]["artifact_ref"] = duplicate[0]["artifact_ref"]
        duplicate[1]["artifact_sha256"] = duplicate[0]["artifact_sha256"]
        duplicate[1]["blind_assignment_id"] = duplicate[0]["blind_assignment_id"]
        duplicate_path = root / "study/duplicate.jsonl"
        dump(duplicate_path, duplicate)
        duplicate_code, _ = run_package("promotion", manifest_path, root, route_path, duplicate_path, routing, outcomes)
        changed = [dict(row) for row in outcome_rows]
        changed[0]["acceptance_changed"] = True
        changed_path = root / "study/changed.jsonl"
        dump(changed_path, changed)
        changed_code, _ = run_package("promotion", manifest_path, root, route_path, changed_path, routing, outcomes)
        assignment_mismatch = [dict(row) for row in outcome_rows]
        assignment_mismatch[0]["blind_assignment_id"] = "assignment-not-in-plan"
        assignment_mismatch_path = root / "study/assignment-mismatch.jsonl"
        dump(assignment_mismatch_path, assignment_mismatch)
        assignment_mismatch_code, _ = run_package(
            "promotion", manifest_path, root, route_path,
            assignment_mismatch_path, routing, outcomes,
        )
        network_mismatch = [dict(row) for row in outcome_rows]
        disabled_fixture = next(
            fixture_id for fixture_id, fixture in outcomes.items()
            if fixture["resource_ceiling"]["network"] == "disabled"
        )
        next(
            row for row in network_mismatch if row["fixture_id"] == disabled_fixture
        )["reported_network_mode"] = "fixture_only"
        network_mismatch_path = root / "study/network-mismatch.jsonl"
        dump(network_mismatch_path, network_mismatch)
        network_mismatch_code, network_mismatch_report = run_package(
            "promotion", manifest_path, root, route_path,
            network_mismatch_path, routing, outcomes,
        )
        symlink_path = root / "study/routing-symlink.jsonl"
        symlink_path.symlink_to(route_path.name)
        symlink_code, symlink_report = run_package(
            "promotion", manifest_path, root, symlink_path,
            outcome_path, routing, outcomes,
        )
        control_reuse_code, control_reuse_report = run_package(
            "promotion", manifest_path, root, route_path,
            manifest_path, routing, outcomes,
        )
        evidence_root_link = root.parent / f"{root.name}-link"
        evidence_root_link.symlink_to(root, target_is_directory=True)
        root_symlink_code, root_symlink_report = run_package(
            "promotion",
            evidence_root_link / manifest_path.relative_to(root),
            evidence_root_link,
            evidence_root_link / route_path.relative_to(root),
            evidence_root_link / outcome_path.relative_to(root),
            routing,
            outcomes,
        )
        evidence_root_link.unlink()
        parent_real = root.parent / f"{root.name}-parent-real"
        parent_real.mkdir()
        nested_root = parent_real / "root"
        nested_root.symlink_to(root, target_is_directory=True)
        parent_link = root.parent / f"{root.name}-parent-link"
        parent_link.symlink_to(parent_real, target_is_directory=True)
        ancestor_path = parent_link / "root"
        ancestor_symlink_code, ancestor_symlink_report = run_package(
            "promotion",
            ancestor_path / manifest_path.relative_to(root),
            ancestor_path,
            ancestor_path / route_path.relative_to(root),
            ancestor_path / outcome_path.relative_to(root),
            routing,
            outcomes,
        )
        parent_link.unlink()
        nested_root.unlink()
        parent_real.rmdir()
        return {
            "complete_synthetic_is_unverified": code == 0 and complete.get("decision") == "PACKAGE_COMPLETE_UNVERIFIED" and complete.get("promotion_eligible") is False,
            "missing_slot_rejected": missing_code == 1,
            "manifest_mismatch_rejected": mismatch_code == 1,
            "duplicate_path_and_assignment_rejected": duplicate_code == 1,
            "changed_acceptance_rejected": changed_code == 1,
            "assignment_plan_mismatch_rejected": assignment_mismatch_code == 1,
            "fixture_network_ceiling_rejected": (
                network_mismatch_code == 1
                and any(
                    "reported_network_mode: exceeds fixture resource ceiling" in error
                    for error in network_mismatch_report.get("errors", [])
                )
            ),
            "symlink_path_rejected": (
                symlink_code == 1
                and any(
                    "symlink path forbidden" in error
                    for error in symlink_report.get("errors", [])
                )
            ),
            "manifest_and_results_paths_reserved": (
                control_reuse_code == 1
                and any(
                    "path reused from study manifest" in error
                    for error in control_reuse_report.get("errors", [])
                )
            ),
            "symlink_evidence_root_rejected": (
                root_symlink_code == 1
                and any(
                    "symlink evidence root forbidden" in error
                    for error in root_symlink_report.get("errors", [])
                )
            ),
            "symlink_evidence_root_ancestor_rejected": (
                ancestor_symlink_code == 1
                and any(
                    "symlink evidence root forbidden" in error
                    for error in ancestor_symlink_report.get("errors", [])
                )
            ),
            "identical_final_bytes_across_arms_valid": code == 0,
        }
