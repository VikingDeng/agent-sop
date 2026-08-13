#!/usr/bin/env python3
"""Dependency-free experiment-run fixture server."""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "static"
DEFAULT_DATA_DIR = ROOT / "data"
RUN_ID_RE = re.compile(r"^/api/runs/([^/]+)(/logs)?$")


def _read_store(data_dir: Path) -> dict[str, Any]:
    with (data_dir / "runs.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_store(data_dir: Path, store: dict[str, Any]) -> None:
    target = data_dir / "runs.json"
    temporary = data_dir / "runs.json.tmp"
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(target)


def _summary(run: dict[str, Any]) -> dict[str, Any]:
    fields = ("id", "name", "dataset", "status", "created_at", "progress", "metrics")
    return {field: run[field] for field in fields}


def _detail(run: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "id",
        "name",
        "dataset",
        "status",
        "created_at",
        "progress",
        "metrics",
        "parameters",
        "failure",
    )
    return {field: run[field] for field in fields}


def _find_run(store: dict[str, Any], run_id: str) -> dict[str, Any] | None:
    return next((run for run in store["runs"] if run["id"] == run_id), None)


def _expanded_logs(run: dict[str, Any]) -> list[str]:
    lines = list(run.get("logs", []))
    repeat = run.get("log_repeat")
    if repeat:
        for index in range(int(repeat["count"])):
            lines.append(
                repeat["template"].format(
                    second=f"{index % 60:02d}",
                    item=f"{index + 1:04d}",
                )
            )
    return lines


class ExperimentHandler(BaseHTTPRequestHandler):
    server_version = "ExperimentFixture/1.0"

    @property
    def data_dir(self) -> Path:
        return self.server.data_dir  # type: ignore[attr-defined]

    @property
    def store_lock(self) -> threading.Lock:
        return self.server.store_lock  # type: ignore[attr-defined]

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, code: str, message: str) -> None:
        self._json(status, {"error": {"code": code, "message": message}})

    def _static(self, path: str) -> None:
        mapping = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
        }
        if path not in mapping:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Resource not found")
            return
        filename, content_type = mapping[path]
        body = (STATIC_ROOT / filename).read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            self._static(parsed.path)
            return

        if parsed.path == "/api/runs":
            scenario = parse_qs(parsed.query).get("scenario", ["default"])[0]
            if scenario == "slow":
                time.sleep(0.2)
            if scenario == "error":
                self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "fixture_failure", "Planted 500 scenario")
                return
            store = _read_store(self.data_dir)
            runs = [] if scenario == "empty" else [_summary(run) for run in store["runs"]]
            self._json(HTTPStatus.OK, {"runs": runs})
            return

        if parsed.path == "/api/compare":
            query = parse_qs(parsed.query)
            left_id = query.get("left", [""])[0]
            right_id = query.get("right", [""])[0]
            store = _read_store(self.data_dir)
            left = _find_run(store, left_id)
            right = _find_run(store, right_id)
            if left is None or right is None:
                self._error(HTTPStatus.NOT_FOUND, "run_not_found", "Both comparison runs must exist")
                return
            common = sorted(set(left["metrics"]) & set(right["metrics"]))
            deltas = {key: round(float(right["metrics"][key]) - float(left["metrics"][key]), 6) for key in common}
            self._json(
                HTTPStatus.OK,
                {"left": _summary(left), "right": _summary(right), "metric_deltas": deltas},
            )
            return

        match = RUN_ID_RE.match(parsed.path)
        if match:
            run_id, log_suffix = match.groups()
            store = _read_store(self.data_dir)
            run = _find_run(store, run_id)
            if run is None:
                self._error(HTTPStatus.NOT_FOUND, "run_not_found", f"Unknown run: {run_id}")
                return
            payload = {"run_id": run_id, "lines": _expanded_logs(run)} if log_suffix else {"run": _detail(run)}
            self._json(HTTPStatus.OK, payload)
            return

        self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        if parsed.path != "/api/runs":
            self._error(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_request", "Request body must be JSON")
            return
        name = payload.get("name") if isinstance(payload, dict) else None
        dataset = payload.get("dataset") if isinstance(payload, dict) else None
        if not isinstance(name, str) or not name.strip() or not isinstance(dataset, str) or not dataset.strip():
            self._error(HTTPStatus.BAD_REQUEST, "invalid_request", "name and dataset are required")
            return
        with self.store_lock:
            store = _read_store(self.data_dir)
            run_id = f"run-{store['next_id']}"
            store["next_id"] += 1
            run = {
                "id": run_id,
                "name": name.strip(),
                "dataset": dataset.strip(),
                "status": "queued",
                "created_at": "2026-07-18T13:00:00Z",
                "progress": 0,
                "metrics": {},
                "parameters": {},
                "failure": None,
                "logs": ["13:00:00 run queued"],
            }
            store["runs"].append(run)
            _write_store(self.data_dir, store)
        self._json(HTTPStatus.CREATED, {"run": _detail(run)})


def create_server(port: int = 8765, data_dir: Path | None = None) -> ThreadingHTTPServer:
    resolved_data_dir = data_dir or Path(os.environ.get("EXPERIMENT_DATA_DIR", DEFAULT_DATA_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", port), ExperimentHandler)
    server.data_dir = resolved_data_dir  # type: ignore[attr-defined]
    server.store_lock = threading.Lock()  # type: ignore[attr-defined]
    return server


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = create_server(port=args.port)
    host, port = server.server_address
    print(f"Experiment fixture listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
