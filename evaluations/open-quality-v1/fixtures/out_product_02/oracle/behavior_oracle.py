#!/usr/bin/env python3
"""Independent API oracle for out_product_02.

The evaluator keeps this file outside the agent-visible workspace.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


EXPECTED_CONTRACT_SHA256 = "8f227eb4098571eb30ffb3de0fb6e7477a4cc33cc17f9d99c0110cefecd3d682"
SERVER_START_TIMEOUT_SECONDS = 3.0
SERVER_STOP_TIMEOUT_SECONDS = 3.0
SERVER_HARNESS = r"""
import importlib.util
import json
import sys
from pathlib import Path

candidate = Path(sys.argv[1])
data_dir = Path(sys.argv[2])
ready = Path(sys.argv[3])
sys.path.insert(0, str(candidate))
spec = importlib.util.spec_from_file_location("candidate_experiment_app", candidate / "app.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import candidate app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
create_server = getattr(module, "create_server", None)
if not callable(create_server):
    raise RuntimeError("app.py must expose create_server(port=..., data_dir=...)")
server = create_server(port=0, data_dir=data_dir)
host, port = server.server_address
temporary = ready.with_suffix(".tmp")
temporary.write_text(json.dumps({"host": host, "port": port}), encoding="utf-8")
temporary.replace(ready)
try:
    server.serve_forever()
finally:
    server.server_close()
"""


class OracleFailure(RuntimeError):
    """A candidate violated one observable product contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OracleFailure(message)


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


@contextmanager
def _running_server(candidate: Path, data_dir: Path):
    ready = data_dir.parent / f"server-{time.monotonic_ns()}.ready.json"
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process_log = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-c", SERVER_HARNESS, str(candidate), str(data_dir), str(ready)],
        cwd=candidate,
        env=environment,
        text=True,
        stdout=process_log,
        stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
        endpoint: str | None = None
        while time.monotonic() < deadline:
            if ready.is_file():
                try:
                    address = json.loads(ready.read_text(encoding="utf-8"))
                    endpoint = f"http://{address['host']}:{address['port']}"
                except (json.JSONDecodeError, KeyError, OSError, TypeError):
                    endpoint = None
                if endpoint is not None:
                    break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        if endpoint is None:
            process_log.seek(0)
            detail = process_log.read()[-1000:].strip()
            raise OracleFailure(f"candidate server did not start: {detail or 'no process output'}")
        _require(process.poll() is None, "candidate server exited during startup")
        yield endpoint
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=SERVER_STOP_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=SERVER_STOP_TIMEOUT_SECONDS)
        ready.unlink(missing_ok=True)
        process_log.close()


def check(candidate: Path) -> dict[str, Any]:
    import hashlib

    contract_hash = hashlib.sha256((candidate / "api-contract.json").read_bytes()).hexdigest()
    if contract_hash != EXPECTED_CONTRACT_SHA256:
        raise OracleFailure("frozen api-contract.json changed")

    with tempfile.TemporaryDirectory(prefix="experiment-fixture-") as temporary:
        data_dir = Path(temporary) / "data"
        shutil.copytree(candidate / "data", data_dir)
        checks: list[str] = []
        created_id = ""
        with _running_server(candidate, data_dir) as base:
            status, payload = _request(base, "/api/runs")
            runs = payload.get("runs")
            _require(status == 200, f"run list returned HTTP {status}, expected 200")
            _require(isinstance(runs, list) and len(runs) == 4, "run list must contain the four frozen runs")
            _require(
                {run.get("status") for run in runs if isinstance(run, dict)} == {"running", "completed", "failed"},
                "run list must expose running, completed, and failed states",
            )
            checks.append("run-list")

            status, payload = _request(base, "/api/runs?scenario=empty")
            _require(status == 200 and payload == {"runs": []}, "empty scenario must return HTTP 200 and no runs")
            status, payload = _request(base, "/api/runs?scenario=error")
            _require(
                status == 500 and payload.get("error", {}).get("code") == "fixture_failure",
                "error scenario must return the frozen fixture_failure response",
            )
            checks.append("empty-and-error-scenarios")

            status, payload = _request(base, "/api/runs/run-204")
            _require(status == 200 and isinstance(payload.get("run"), dict), "failed-run detail must return HTTP 200")
            run = payload["run"]
            failure = run.get("failure")
            _require(
                run.get("status") == "failed" and isinstance(failure, dict) and failure.get("retryable") is False,
                "run-204 must remain a non-retryable failed run",
            )
            status, payload = _request(base, "/api/runs/run-204/logs")
            lines = payload.get("lines")
            _require(status == 200 and isinstance(lines, list) and len(lines) >= 90, "run-204 must expose at least 90 log lines")
            _require(all(isinstance(line, str) for line in lines) and max(map(len, lines)) > 100, "run-204 must include a log line longer than 100 characters")
            checks.append("failed-run-and-long-logs")

            status, payload = _request(base, "/api/compare?left=run-201&right=run-202")
            _require(
                status == 200 and payload.get("metric_deltas", {}).get("accuracy") == 0.043,
                "run comparison must preserve the frozen accuracy delta of 0.043",
            )
            checks.append("comparison-semantics")

            status, payload = _request(base, "/api/runs", {"name": "oracle run", "dataset": "support-intents-v3"})
            created = payload.get("run")
            _require(status == 201 and isinstance(created, dict), "valid run creation must return HTTP 201 and a run")
            _require(created.get("status") == "queued" and created.get("progress") == 0, "new run must begin queued at zero progress")
            created_id = str(created.get("id", ""))
            _require(bool(created_id), "created run must have a non-empty id")
            status, payload = _request(base, f"/api/runs/{created_id}")
            _require(
                status == 200 and payload.get("run", {}).get("name") == "oracle run",
                "created run must be readable before restart",
            )
            checks.append("create-and-persist")

        # A fresh server object must reconstruct state from the same data directory.
        # Passing only before this boundary is compatible with in-memory fake persistence.
        with _running_server(candidate, data_dir) as base:
            status, payload = _request(base, f"/api/runs/{created_id}")
            persisted = payload.get("run")
            _require(status == 200 and isinstance(persisted, dict), "created run was lost after server restart")
            _require(
                persisted.get("id") == created_id
                and persisted.get("name") == "oracle run"
                and persisted.get("dataset") == "support-intents-v3"
                and persisted.get("status") == "queued"
                and persisted.get("progress") == 0,
                "created run changed after server restart",
            )
            checks.append("server-restart-persistence")

            status, payload = _request(base, "/api/runs/does-not-exist")
            _require(
                status == 404 and payload.get("error", {}).get("code") == "run_not_found",
                "missing run must return the frozen run_not_found response",
            )
            status, payload = _request(base, "/api/runs", {"name": "", "dataset": "x"})
            _require(
                status == 400 and payload.get("error", {}).get("code") == "invalid_request",
                "invalid create request must return the frozen invalid_request response",
            )
            checks.append("contract-errors")

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
