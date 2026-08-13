#!/usr/bin/env python3
"""Structural and evidence-binding oracle for out_idea_01.

This intentionally does not score which scientific idea is best.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
FIXTURE_ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _json_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def _schema_errors(schema: Any, submission: Any) -> list[str]:
    """Validate the whole public contract with its declared JSON Schema draft."""

    if not isinstance(schema, dict) or schema.get("$schema") != DRAFT_2020_12:
        raise RuntimeError(
            "submission.schema.json must declare JSON Schema Draft 2020-12"
        )
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as error:
        raise RuntimeError(
            "Draft 2020-12 validation unavailable: install the pinned jsonschema dependency"
        ) from error

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise RuntimeError(f"invalid submission.schema.json: {error.message}") from error

    validator = Draft202012Validator(schema)
    return [
        f"schema {_json_path(error.absolute_path)}: {error.message}"
        for error in sorted(
            validator.iter_errors(submission),
            key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message),
        )
    ]


def _verify_immutable_inputs(candidate: Path) -> None:
    """Bind schema and evidence reads to the evaluator-held fixture lock."""

    lock = _load(FIXTURE_ROOT / "immutable-sha256.json")
    locked_files = lock.get("files")
    if not isinstance(locked_files, dict):
        raise RuntimeError("invalid evaluator-held immutable input lock")
    changed: list[str] = []
    for relative, expected_hash in locked_files.items():
        path = candidate / relative
        if not path.is_file():
            changed.append(relative)
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            changed.append(relative)
    if changed:
        raise RuntimeError(f"immutable idea inputs changed: {sorted(changed)}")


def _result(errors: list[str], checked_candidates: int) -> dict[str, Any]:
    return {
        "fixture": "out_idea_01",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "checked_candidates": checked_candidates,
        "note": "This oracle checks the complete public schema and closed-world evidence binding only; scientific quality remains blind-review evidence.",
    }


def check(candidate: Path, submission_path: Path) -> dict[str, Any]:
    _verify_immutable_inputs(candidate)
    literature = _load(candidate / "evidence" / "literature.json")["cards"]
    traces = _load(candidate / "evidence" / "traces.json")["traces"]
    collisions = _load(candidate / "evidence" / "collision-matrix.json")
    adapter = _load(candidate / "evidence" / "benchmark-adapter-contract.json")
    schema = _load(candidate / "submission.schema.json")
    submission = _load(submission_path)

    schema_errors = _schema_errors(schema, submission)
    if schema_errors:
        candidates = submission.get("candidates", []) if isinstance(submission, dict) else []
        checked_candidates = len(candidates) if isinstance(candidates, list) else 0
        return _result(schema_errors, checked_candidates)

    literature_ids = {card["id"] for card in literature}
    trace_ids = {trace["id"] for trace in traces}
    collision_ids = {item["id"] for item in collisions["cross_domain_collisions"]}
    known_refs = literature_ids | trace_ids | collision_ids
    errors: list[str] = []

    if set(submission) != {"problem", "candidates", "selection"}:
        errors.append("submission must contain exactly problem, candidates, selection")
    candidates = submission.get("candidates", [])
    if not isinstance(candidates, list) or not 3 <= len(candidates) <= 5:
        errors.append("three to five candidates required")
        candidates = []

    seen_ids: set[str] = set()
    operation_wordsets: list[set[str]] = []
    for index, item in enumerate(candidates):
        prefix = f"candidate[{index}]"
        identifier = item.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"candidate-[1-5]", identifier):
            errors.append(f"{prefix}: invalid id")
        elif identifier in seen_ids:
            errors.append(f"{prefix}: duplicate id")
        else:
            seen_ids.add(identifier)

        operation = item.get("core_operation", {})
        if set(operation) != {"input", "state_transition", "output"}:
            errors.append(f"{prefix}: core_operation must name input/state_transition/output")
        transition = operation.get("state_transition", "")
        if not isinstance(transition, str) or len(transition.strip()) < 35:
            errors.append(f"{prefix}: state_transition is not operationally specific")
        else:
            operation_wordsets.append(_words(transition))

        refs = item.get("evidence_refs", [])
        if not isinstance(refs, list) or len(set(refs)) < 3:
            errors.append(f"{prefix}: at least three distinct evidence refs required")
        elif unknown := sorted(set(refs) - known_refs):
            errors.append(f"{prefix}: unknown evidence refs {unknown}")
        elif not (set(refs) & trace_ids) or not (set(refs) & literature_ids):
            errors.append(f"{prefix}: evidence must include a trace and literature")

        neighbor = item.get("nearest_neighbor", {})
        if neighbor.get("literature_ref") not in literature_ids:
            errors.append(f"{prefix}: nearest neighbor must bind a literature card")
        if len(str(neighbor.get("different", "")).strip()) < 25:
            errors.append(f"{prefix}: nearest-neighbor delta is too vague")

        experiment = item.get("decisive_experiment", {})
        if experiment.get("benchmark_split") not in set(adapter["available_splits"]) | {"both"}:
            errors.append(f"{prefix}: unsupported benchmark split")
        if experiment.get("primary_metric") not in adapter["primary_metrics"]:
            errors.append(f"{prefix}: unsupported primary metric")
        if not 2 <= len(experiment.get("arms", [])) <= adapter["allowed_probe_budget"]["max_arms"]:
            errors.append(f"{prefix}: decisive experiment needs two or three arms")
        if len(experiment.get("competing_explanations", [])) < 2:
            errors.append(f"{prefix}: experiment must distinguish competing explanations")
        if len(str(experiment.get("decision_rule", "")).strip()) < 25:
            errors.append(f"{prefix}: decision rule is not explicit")
        if len(str(item.get("kill_condition", "")).strip()) < 25:
            errors.append(f"{prefix}: kill condition is not falsifiable")

    for left in range(len(operation_wordsets)):
        for right in range(left + 1, len(operation_wordsets)):
            union = operation_wordsets[left] | operation_wordsets[right]
            similarity = len(operation_wordsets[left] & operation_wordsets[right]) / max(1, len(union))
            if similarity > 0.82:
                errors.append(f"candidate[{left}] and candidate[{right}] core operations are near-duplicates")

    problem_refs = set(submission.get("problem", {}).get("trace_refs", []))
    if len(problem_refs & trace_ids) < 2 or problem_refs - trace_ids:
        errors.append("problem must cite at least two known traces")
    selection = submission.get("selection", {})
    selected = selection.get("candidate_id")
    if selected is not None and selected not in seen_ids:
        errors.append("selection.candidate_id must name a candidate or be null")
    selection_refs = set(selection.get("evidence_refs", []))
    if len(selection_refs) < 2 or selection_refs - known_refs:
        errors.append("selection must bind at least two known evidence refs")

    return _result(errors, len(candidates))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("submission", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.candidate.resolve(), args.submission.resolve())
    except Exception as error:
        result = _result([f"oracle failure: {error}"], 0)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
