#!/usr/bin/env python3
"""Validate Open Quality contracts, diagnostics, or an unverified package."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

import _study_protocol as study


ROOT = Path(__file__).resolve().parent
ROUTING_CASES_PATH = ROOT / "routing-cases.json"
ROUTING_SCHEMA_PATH = ROOT / "routing-output.schema.json"
OUTCOME_FIXTURES_PATH = ROOT / "outcome-fixtures.json"
STUDY_SCHEMA_PATH = ROOT / "study-manifest.schema.json"
CASE_VERSION = "open-quality-routing-cases-v1"
ROUTING_KEYS = {
    "schema_version", "case_id", "primary_mode", "overlays", "user_decision",
    "decisive_facts", "next_action",
}
DIAGNOSTIC_KEYS = {
    "case_id", "arm", "replicate", "routing", "run_id", "reported_wcu",
    "reported_wcu_complete",
}


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def validate_routing_schema(schema: Any) -> list[str]:
    if not isinstance(schema, dict):
        return ["routing schema: expected object"]
    errors: list[str] = []
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        errors.append("routing schema: root must be closed")
    if set(schema.get("required", [])) != ROUTING_KEYS or set(schema.get("properties", {})) != ROUTING_KEYS:
        errors.append("routing schema: fields drift")
    return errors


def validate_routing_cases(payload: Any) -> tuple[list[str], dict[str, dict[str, Any]]]:
    errors: list[str] = []
    keys = {"version", "task_classes", "primary_modes", "overlays", "cases"}
    if not isinstance(payload, dict) or set(payload) != keys:
        return ["routing cases: expected closed manifest"], {}
    if payload.get("version") != CASE_VERSION:
        errors.append("routing cases.version: drift")
    rows = payload.get("cases")
    if not isinstance(rows, list) or len(rows) != 24:
        return errors + ["routing cases: expected 24 rows"], {}
    row_keys = {"id", "task_class", "pilot", "boundary_pair", "prompt", "expected", "why"}
    expected_keys = {"primary_mode", "overlays", "user_decision"}
    cases: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    pilots: Counter[str] = Counter()
    pairs: Counter[str] = Counter()
    for index, row in enumerate(rows):
        label = f"routing cases[{index}]"
        if not isinstance(row, dict) or set(row) != row_keys:
            errors.append(f"{label}: fields drift")
            continue
        case_id = row.get("id")
        if not study.nonempty(case_id) or case_id in cases:
            errors.append(f"{label}.id: invalid/duplicate")
            continue
        cases[case_id] = row
        task_class = row.get("task_class")
        if task_class not in study.TASK_CLASSES:
            errors.append(f"{label}.task_class: invalid")
        else:
            counts[task_class] += 1
            pilots[task_class] += int(row.get("pilot") is True)
        pairs[row.get("boundary_pair")] += 1
        expected = row.get("expected")
        if not isinstance(expected, dict) or set(expected) != expected_keys:
            errors.append(f"{label}.expected: fields drift")
            continue
        if expected.get("primary_mode") not in study.PRIMARY_MODES:
            errors.append(f"{label}.expected.primary_mode: invalid")
        overlays = expected.get("overlays")
        if not isinstance(overlays, list) or set(overlays) - set(study.OVERLAYS):
            errors.append(f"{label}.expected.overlays: invalid")
        if expected.get("user_decision") not in study.USER_DECISIONS:
            errors.append(f"{label}.expected.user_decision: invalid")
    for task_class in study.TASK_CLASSES:
        if counts[task_class] != 6 or pilots[task_class] != 3:
            errors.append(f"routing cases: {task_class} must have 6/3 pilot")
    if len(pairs) != 12 or any(value != 2 for value in pairs.values()):
        errors.append("routing cases: expected 12 paired boundaries")
    pilot = study.active_fixtures("pilot", cases)
    if pilot.get("research_04", {}).get("expected") != {
        "primary_mode": "re_contract",
        "overlays": ["durable_goal", "research_fidelity"],
        "user_decision": "required_now",
    }:
        errors.append("routing pilot: must include research_04 re_contract/HUMAN boundary")
    return errors, cases


def load_static() -> tuple[list[str], dict[str, Any]]:
    try:
        routing_schema = study.load_json(ROUTING_SCHEMA_PATH)
        routing_payload = study.load_json(ROUTING_CASES_PATH)
        outcome_payload = study.load_json(OUTCOME_FIXTURES_PATH)
        study_schema = study.load_json(STUDY_SCHEMA_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [str(exc)], {}
    errors = validate_routing_schema(routing_schema)
    route_errors, routes = validate_routing_cases(routing_payload)
    outcome_errors, outcomes = study.validate_outcome_fixtures(outcome_payload)
    errors.extend(route_errors)
    errors.extend(outcome_errors)
    errors.extend(study.validate_study_schema(study_schema))
    return errors, {"routing": routes, "outcomes": outcomes}


def diagnostic(path: Path, routes: dict[str, dict[str, Any]]) -> tuple[int, dict[str, Any]]:
    rows, errors = study.load_jsonl(path)
    expected = {(case_id, arm, 1) for case_id in routes for arm in study.ARMS}
    observed: set[tuple[str, str, int]] = set()
    exact: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    for index, row in enumerate(rows):
        label = f"routing diagnostic[{index}]"
        if not isinstance(row, dict) or set(row) != DIAGNOSTIC_KEYS:
            errors.append(f"{label}: fields drift")
            continue
        slot = (row.get("case_id"), row.get("arm"), row.get("replicate"))
        if slot not in expected or slot in observed:
            errors.append(f"{label}: unexpected/duplicate slot")
            continue
        observed.add(slot)
        errors.extend(study.validate_routing_output(row.get("routing"), row["case_id"], f"{label}.routing"))
        gold = routes[row["case_id"]]["expected"]
        if (row["routing"].get("primary_mode") == gold["primary_mode"]
                and set(row["routing"].get("overlays", [])) == set(gold["overlays"])
                and row["routing"].get("user_decision") == gold["user_decision"]):
            exact[row["arm"]] += 1
        totals[row["arm"]] += 1
    if observed != expected:
        errors.append(f"routing diagnostic: missing {len(expected - observed)} slots")
    if errors:
        return 1, {"decision": "PACKAGE_INVALID", "promotion_eligible": False, "errors": errors}
    return 0, {
        "decision": "ROUTING_DIAGNOSTIC_ONLY_UNVERIFIED",
        "promotion_eligible": False,
        "reported_exact_accuracy": {arm: exact[arm] / totals[arm] for arm in study.ARMS},
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--manifest-template", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--stage", choices=("routing", "pilot", "promotion"))
    parser.add_argument("--routing-results", type=Path)
    parser.add_argument("--outcome-results", type=Path)
    parser.add_argument("--study-manifest", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    args = parser.parse_args(argv)
    standalone = sum(int(value) for value in (args.validate_only, args.manifest_template, args.self_test))
    if standalone:
        if standalone != 1 or any(value is not None for value in (args.stage, args.routing_results, args.outcome_results, args.study_manifest, args.evidence_root)):
            parser.error("choose one standalone action")
        return args
    if args.stage == "routing":
        if args.routing_results is None or any(value is not None for value in (args.outcome_results, args.study_manifest, args.evidence_root)):
            parser.error("routing requires only --routing-results")
        return args
    if args.stage in {"pilot", "promotion"}:
        if any(value is None for value in (args.routing_results, args.outcome_results, args.study_manifest, args.evidence_root)):
            parser.error("pilot/promotion require all four package arguments")
        return args
    parser.error("choose an action")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    errors, static = load_static()
    if errors:
        emit({"decision": "PACKAGE_INVALID", "promotion_eligible": False, "errors": errors})
        return 1
    routes, outcomes = static["routing"], static["outcomes"]
    if args.validate_only:
        emit({
            "decision": "STATIC_CONTRACT_VALID",
            "promotion_eligible": False,
            "routing_cases": len(routes),
            "pilot_routing_cases": len(study.active_fixtures("pilot", routes)),
            "outcome_fixture_contracts": len(outcomes),
            "pilot_outcome_fixture_contracts": len(study.active_fixtures("pilot", outcomes)),
            "all_outcome_inputs_materialized": False,
            "pilot_bundle_verification": "RUN_FIXTURES_VERIFY_COMMAND",
        })
        return 0
    if args.manifest_template:
        emit(study.manifest_template(study.active_fixtures("pilot", routes), study.active_fixtures("pilot", outcomes)))
        return 0
    if args.self_test:
        report = study.run_self_test(routes, outcomes)
        report["evidence_status"] = "SYNTHETIC_PACKAGE_SELF_TEST_NOT_EVALUATION_EVIDENCE"
        emit(report)
        return 0 if all(value is True for key, value in report.items() if key != "evidence_status") else 1
    if args.stage == "routing":
        code, report = diagnostic(args.routing_results, routes)
    else:
        code, report = study.run_package(args.stage, args.study_manifest, args.evidence_root, args.routing_results, args.outcome_results, routes, outcomes)
    emit(report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
