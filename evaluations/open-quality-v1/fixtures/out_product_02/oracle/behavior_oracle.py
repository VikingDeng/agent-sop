#!/usr/bin/env python3
"""Independent API oracle for out_product_02.

The evaluator keeps this file outside the agent-visible workspace.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


EXPECTED_CONTRACT_SHA256 = "8f227eb4098571eb30ffb3de0fb6e7477a4cc33cc17f9d99c0110cefecd3d682"


def _load_app(candidate: Path):
    spec = importlib.util.spec_from_file_location("candidate_experiment_app", candidate / "app.py")
    if spec is None or spec.loader is None:
        raise AssertionError("cannot import candidate app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "create_server", None)):
        raise AssertionError("app.py must expose create_server(port=..., data_dir=...)")
    return module


def _request(base: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        base + path,
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
        method="POST" if body else "GET",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def check(candidate: Path) -> dict[str, Any]:
    import hashlib

    contract_hash = hashlib.sha256((candidate / "api-contract.json").read_bytes()).hexdigest()
    if contract_hash != EXPECTED_CONTRACT_SHA256:
        raise AssertionError("frozen api-contract.json changed")

    with tempfile.TemporaryDirectory(prefix="experiment-fixture-") as temporary:
        data_dir = Path(temporary) / "data"
        shutil.copytree(candidate / "data", data_dir)
        module = _load_app(candidate)
        server = module.create_server(port=0, data_dir=data_dir)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        base = f"http://{host}:{port}"
        checks: list[str] = []
        try:
            status, payload = _request(base, "/api/runs")
            assert status == 200 and len(payload["runs"]) == 4
            assert {run["status"] for run in payload["runs"]} == {"running", "completed", "failed"}
            checks.append("run-list")

            status, payload = _request(base, "/api/runs?scenario=empty")
            assert status == 200 and payload == {"runs": []}
            status, payload = _request(base, "/api/runs?scenario=error")
            assert status == 500 and payload["error"]["code"] == "fixture_failure"
            checks.append("empty-and-error-scenarios")

            status, payload = _request(base, "/api/runs/run-204")
            assert status == 200
            failure = payload["run"]["failure"]
            assert payload["run"]["status"] == "failed" and failure["retryable"] is False
            status, payload = _request(base, "/api/runs/run-204/logs")
            assert status == 200 and len(payload["lines"]) >= 90
            assert max(map(len, payload["lines"])) > 100
            checks.append("failed-run-and-long-logs")

            status, payload = _request(base, "/api/compare?left=run-201&right=run-202")
            assert status == 200 and payload["metric_deltas"]["accuracy"] == 0.043
            checks.append("comparison-semantics")

            status, payload = _request(base, "/api/runs", {"name": "oracle run", "dataset": "support-intents-v3"})
            assert status == 201
            created = payload["run"]
            assert created["status"] == "queued" and created["progress"] == 0
            status, payload = _request(base, f"/api/runs/{created['id']}")
            assert status == 200 and payload["run"]["name"] == "oracle run"
            checks.append("create-and-persist")

            status, payload = _request(base, "/api/runs/does-not-exist")
            assert status == 404 and payload["error"]["code"] == "run_not_found"
            status, payload = _request(base, "/api/runs", {"name": "", "dataset": "x"})
            assert status == 400 and payload["error"]["code"] == "invalid_request"
            checks.append("contract-errors")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    return {"fixture": "out_product_02", "status": "PASS", "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        report = check(args.candidate.resolve())
    except Exception as error:  # independent oracle should return one machine-readable failure
        print(json.dumps({"fixture": "out_product_02", "status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
