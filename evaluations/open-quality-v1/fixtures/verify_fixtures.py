#!/usr/bin/env python3
"""Offline self-check for all materialized open-quality pilot fixtures."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

import materialize_fixture


ROOT = Path(__file__).resolve().parent
FIXTURES = ("out_product_02", "out_idea_01", "out_research_02", "out_simple_02")


class FixtureVerificationError(RuntimeError):
    """A committed fixture or control violated its evaluator contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureVerificationError(message)


def _json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=cwd, env=environment, text=True, capture_output=True, timeout=45, check=False)


def _last_json(stdout: str) -> dict[str, Any]:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise FixtureVerificationError("oracle emitted no JSON")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise FixtureVerificationError("oracle output must be a JSON object")
    return value


def verify_locks(temporary: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for fixture_id in FIXTURES:
        fixture_root = ROOT / fixture_id
        metadata = _json(fixture_root / "fixture.json")
        lock = _json(fixture_root / "immutable-sha256.json")
        _require(metadata["outcome_id"] == fixture_id, f"{fixture_id}: outcome id mismatch")
        workspace = fixture_root / metadata["agent_input_root"]
        hashes = materialize_fixture.file_hashes(workspace)
        _require(hashes == lock["files"], f"{fixture_id}: workspace file hash mismatch")
        _require(
            materialize_fixture.tree_hash(hashes) == lock["tree_sha256"],
            f"{fixture_id}: tree hash mismatch",
        )
        archive = temporary / f"{fixture_id}.zip"
        archive_hash = materialize_fixture.write_bundle(workspace, archive)
        _require(
            archive_hash == lock["deterministic_zip_sha256"],
            f"{fixture_id}: archive hash mismatch",
        )
        reports.append({"fixture": fixture_id, "files": len(hashes), "tree_sha256": lock["tree_sha256"]})
    return reports


def verify_product() -> dict[str, Any]:
    fixture = ROOT / "out_product_02"
    result = _run([sys.executable, "oracle/behavior_oracle.py", "workspace"], fixture)
    report = _last_json(result.stdout)
    _require(
        result.returncode == 0 and report["status"] == "PASS",
        f"out_product_02: starting oracle failed: {report}",
    )
    styles = (fixture / "workspace/static/styles.css").read_text(encoding="utf-8")
    script = (fixture / "workspace/static/app.js").read_text(encoding="utf-8")
    markup = (fixture / "workspace/static/index.html").read_text(encoding="utf-8")
    _require(
        "min-width: 980px" in styles and "linear-gradient" in styles,
        "out_product_02: expected weak template styling is absent",
    )
    _require(
        "hero" in markup and "card-grid" in markup,
        "out_product_02: expected weak template markup is absent",
    )
    _require(
        "scenario=empty" not in script
        and "catch" not in script
        and "Launch a magical run" in markup,
        "out_product_02: starting UI no longer matches the frozen incomplete state",
    )
    report["starting_ui"] = "known-incomplete-template-state-confirmed"
    return report


def verify_idea() -> dict[str, Any]:
    fixture = ROOT / "out_idea_01"
    workspace = fixture / "workspace"
    cards = _json(workspace / "evidence/literature.json")["cards"]
    traces = _json(workspace / "evidence/traces.json")["traces"]
    _require(
        len(cards) == 24 and len({card["id"] for card in cards}) == 24,
        "out_idea_01: expected 24 uniquely identified literature cards",
    )
    _require(
        all(card["source"].startswith("https://arxiv.org/abs/") for card in cards),
        "out_idea_01: literature provenance must use arXiv abstract URLs",
    )
    _require(
        len(traces) == 12 and len({trace["id"] for trace in traces}) == 12,
        "out_idea_01: expected 12 uniquely identified replay traces",
    )
    _require(
        {trace["benchmark"] for trace in traces}
        == {"AppWorld-compatible", "SWE-bench-compatible"},
        "out_idea_01: replay traces must cover both frozen compatible splits",
    )

    controls = fixture / "oracle/controls"
    valid = _json(controls / "valid-submission.json")
    field_negative = _json(controls / "field-negative.json")
    _require(
        field_negative.get("base") == "valid-submission.json"
        and field_negative.get("operation") == "delete"
        and field_negative.get("path") == ["candidates", 1, "signal"],
        "out_idea_01: unsupported field-negative control definition",
    )
    invalid = copy.deepcopy(valid)
    removed = invalid["candidates"][1].pop("signal", None)
    _require(removed is not None, "out_idea_01: field-negative control removed no field")

    with tempfile.TemporaryDirectory(prefix="idea-negative-") as temporary:
        temporary_root = Path(temporary)
        valid_path = temporary_root / "valid-submission.json"
        invalid_path = temporary_root / "field-negative-submission.json"
        valid_path.write_text(json.dumps(valid, sort_keys=True) + "\n", encoding="utf-8")
        invalid_path.write_text(json.dumps(invalid, sort_keys=True) + "\n", encoding="utf-8")
        valid_result = _run(
            [sys.executable, "oracle/check_submission.py", "workspace", str(valid_path)],
            fixture,
        )
        invalid_result = _run(
            [sys.executable, "oracle/check_submission.py", "workspace", str(invalid_path)],
            fixture,
        )
    valid_report = _last_json(valid_result.stdout)
    invalid_report = _last_json(invalid_result.stdout)
    _require(
        valid_result.returncode == 0
        and valid_report["status"] == "PASS"
        and valid_report["errors"] == [],
        f"out_idea_01: known-valid submission rejected: {valid_report}",
    )
    expected_path = field_negative["expected_error_path"]
    expected_fragment = field_negative["expected_error_fragment"]
    _require(
        invalid_result.returncode != 0 and invalid_report["status"] == "FAIL",
        f"out_idea_01: field-negative submission was accepted: {invalid_report}",
    )
    _require(
        any(
            expected_path in error and expected_fragment in error
            for error in invalid_report["errors"]
        ),
        f"out_idea_01: field-negative failure was not localized: {invalid_report}",
    )
    return {
        "fixture": "out_idea_01",
        "status": "PASS",
        "literature_cards": len(cards),
        "replay_traces": len(traces),
        "known_valid_submission_accepted": True,
        "field_negative_submission_rejected": True,
    }


def verify_research() -> dict[str, Any]:
    fixture = ROOT / "out_research_02"
    result = _run([sys.executable, "oracle/check_phase0.py", "workspace"], fixture)
    report = _last_json(result.stdout)
    blocker_codes = {blocker["code"] for blocker in report["blockers"]}
    _require(
        result.returncode == 0 and report["status"] == "PASS",
        f"out_research_02: phase-0 oracle failed: {report}",
    )
    _require(report["verdict"] == "NO-GO", "out_research_02: expected planted NO-GO")
    _require(
        blocker_codes == {"ORDER_CONTAMINATION", "PROVENANCE_GAP"},
        f"out_research_02: unexpected blocker set: {sorted(blocker_codes)}",
    )
    _require(
        report["smoke_is_paper_evidence"] is False,
        "out_research_02: smoke result was incorrectly admitted as paper evidence",
    )
    return report


def verify_simple() -> dict[str, Any]:
    fixture = ROOT / "out_simple_02"
    workspace = fixture / "workspace"
    tests = _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], workspace)
    _require(tests.returncode == 0, f"out_simple_02: starting tests failed: {tests.stderr}")
    result = _run([sys.executable, "oracle/check_change.py", "workspace"], fixture)
    report = _last_json(result.stdout)
    _require(
        result.returncode != 0 and report["status"] == "FAIL",
        f"out_simple_02: unimplemented change was accepted: {report}",
    )
    _require(
        any("nickname compatibility probe failed" in error for error in report["errors"]),
        f"out_simple_02: expected compatibility failure is absent: {report}",
    )
    return {
        "fixture": "out_simple_02",
        "status": "PASS",
        "starting_tests": "PASS",
        "unimplemented_change_rejected": True,
        "external_checks_required": report["external_checks_required"],
    }


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="materialized-fixtures-") as temporary:
            locks = verify_locks(Path(temporary))
        reports = [verify_product(), verify_idea(), verify_research(), verify_simple()]
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps({"status": "PASS", "locks": locks, "starting_states": reports}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
