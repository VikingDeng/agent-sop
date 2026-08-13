#!/usr/bin/env python3
"""Structural and evidence-binding oracle for out_idea_01.

This intentionally does not score which scientific idea is best.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def check(candidate: Path, submission_path: Path) -> dict[str, Any]:
    literature = _load(candidate / "evidence" / "literature.json")["cards"]
    traces = _load(candidate / "evidence" / "traces.json")["traces"]
    collisions = _load(candidate / "evidence" / "collision-matrix.json")
    adapter = _load(candidate / "evidence" / "benchmark-adapter-contract.json")
    submission = _load(submission_path)

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

    status = "PASS" if not errors else "FAIL"
    return {
        "fixture": "out_idea_01",
        "status": status,
        "errors": errors,
        "checked_candidates": len(candidates),
        "note": "This oracle checks structure/evidence binding only; scientific quality remains blind-review evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("submission", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.candidate.resolve(), args.submission.resolve())
    except Exception as error:
        result = {"fixture": "out_idea_01", "status": "FAIL", "errors": [str(error)]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
