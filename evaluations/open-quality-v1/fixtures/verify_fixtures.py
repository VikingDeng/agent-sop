#!/usr/bin/env python3
"""Offline self-check for all materialized open-quality pilot fixtures."""

from __future__ import annotations

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
        raise AssertionError("oracle emitted no JSON")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise AssertionError("oracle output must be a JSON object")
    return value


def verify_locks(temporary: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for fixture_id in FIXTURES:
        fixture_root = ROOT / fixture_id
        metadata = _json(fixture_root / "fixture.json")
        lock = _json(fixture_root / "immutable-sha256.json")
        assert metadata["outcome_id"] == fixture_id
        workspace = fixture_root / metadata["agent_input_root"]
        hashes = materialize_fixture.file_hashes(workspace)
        assert hashes == lock["files"], f"{fixture_id}: workspace file hash mismatch"
        assert materialize_fixture.tree_hash(hashes) == lock["tree_sha256"], f"{fixture_id}: tree hash mismatch"
        archive = temporary / f"{fixture_id}.zip"
        archive_hash = materialize_fixture.write_bundle(workspace, archive)
        assert archive_hash == lock["deterministic_zip_sha256"], f"{fixture_id}: archive hash mismatch"
        reports.append({"fixture": fixture_id, "files": len(hashes), "tree_sha256": lock["tree_sha256"]})
    return reports


def verify_product() -> dict[str, Any]:
    fixture = ROOT / "out_product_02"
    result = _run([sys.executable, "oracle/behavior_oracle.py", "workspace"], fixture)
    report = _last_json(result.stdout)
    assert result.returncode == 0 and report["status"] == "PASS", report
    styles = (fixture / "workspace/static/styles.css").read_text(encoding="utf-8")
    script = (fixture / "workspace/static/app.js").read_text(encoding="utf-8")
    markup = (fixture / "workspace/static/index.html").read_text(encoding="utf-8")
    assert "min-width: 980px" in styles and "linear-gradient" in styles
    assert "hero" in markup and "card-grid" in markup
    assert "scenario=empty" not in script and "catch" not in script and "Launch a magical run" in markup
    report["starting_ui"] = "known-incomplete-template-state-confirmed"
    return report


def verify_idea() -> dict[str, Any]:
    fixture = ROOT / "out_idea_01"
    workspace = fixture / "workspace"
    cards = _json(workspace / "evidence/literature.json")["cards"]
    traces = _json(workspace / "evidence/traces.json")["traces"]
    assert len(cards) == 24 and len({card["id"] for card in cards}) == 24
    assert all(card["source"].startswith("https://arxiv.org/abs/") for card in cards)
    assert len(traces) == 12 and len({trace["id"] for trace in traces}) == 12
    assert {trace["benchmark"] for trace in traces} == {"AppWorld-compatible", "SWE-bench-compatible"}
    with tempfile.TemporaryDirectory(prefix="idea-negative-") as temporary:
        invalid = Path(temporary) / "submission.json"
        invalid.write_text("{}\n", encoding="utf-8")
        result = _run([sys.executable, "oracle/check_submission.py", "workspace", str(invalid)], fixture)
    report = _last_json(result.stdout)
    assert result.returncode != 0 and report["status"] == "FAIL"
    return {
        "fixture": "out_idea_01",
        "status": "PASS",
        "literature_cards": len(cards),
        "replay_traces": len(traces),
        "negative_submission_rejected": True,
    }


def verify_research() -> dict[str, Any]:
    fixture = ROOT / "out_research_02"
    result = _run([sys.executable, "oracle/check_phase0.py", "workspace"], fixture)
    report = _last_json(result.stdout)
    blocker_codes = {blocker["code"] for blocker in report["blockers"]}
    assert result.returncode == 0 and report["status"] == "PASS"
    assert report["verdict"] == "NO-GO"
    assert blocker_codes == {"ORDER_CONTAMINATION", "PROVENANCE_GAP"}
    assert report["smoke_is_paper_evidence"] is False
    return report


def verify_simple() -> dict[str, Any]:
    fixture = ROOT / "out_simple_02"
    workspace = fixture / "workspace"
    tests = _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], workspace)
    assert tests.returncode == 0, tests.stderr
    result = _run([sys.executable, "oracle/check_change.py", "workspace"], fixture)
    report = _last_json(result.stdout)
    assert result.returncode != 0 and report["status"] == "FAIL"
    assert any("nickname compatibility probe failed" in error for error in report["errors"])
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
