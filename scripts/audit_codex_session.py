#!/usr/bin/env python3
"""Audit a complete Codex task tree for weighted token cost and routing behavior."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any


HOOKS_DIR = Path(__file__).resolve().parents[1] / "codex" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
from weighted_routing_policy import is_sol_execution, normalize_tool_name  # noqa: E402


MODEL_WEIGHTS = {"sol": 25, "terra": 10, "luna": 1}
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


@dataclass(frozen=True)
class SessionMeta:
    path: Path
    thread_id: str
    session_id: str
    parent_thread_id: str | None
    agent_role: str | None


def model_family(model: str) -> str:
    lowered = model.lower()
    for family in MODEL_WEIGHTS:
        if family in lowered:
            return family
    return "unknown"


def _read_meta(path: Path) -> SessionMeta | None:
    try:
        with path.open() as handle:
            for _ in range(20):
                line = handle.readline()
                if not line:
                    break
                record = json.loads(line)
                if record.get("type") != "session_meta":
                    continue
                payload = record.get("payload", {})
                if not isinstance(payload, dict):
                    return None
                thread_id = str(payload.get("id") or payload.get("session_id") or "")
                if not thread_id:
                    return None
                return SessionMeta(
                    path=path.resolve(),
                    thread_id=thread_id,
                    session_id=str(payload.get("session_id") or thread_id),
                    parent_thread_id=(str(payload["parent_thread_id"]) if payload.get("parent_thread_id") else None),
                    agent_role=(str(payload["agent_role"]) if payload.get("agent_role") else None),
                )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return None


def discover_session_tree(target: str, sessions_root: Path) -> list[SessionMeta]:
    target_path = Path(target).expanduser()
    search_roots = {sessions_root.resolve(), (sessions_root.parent / "archived_sessions").resolve()}
    root_meta: SessionMeta | None = None
    if target_path.is_file():
        target_path = target_path.resolve()
        root_meta = _read_meta(target_path)
        if root_meta is None:
            raise ValueError(f"not a readable Codex session log: {target_path}")
        root_id = root_meta.thread_id
        search_roots.add(target_path.parent)
    else:
        root_id = target

    candidate_paths = {
        path.resolve()
        for root in search_roots
        if root.exists()
        for path in root.rglob("*.jsonl")
    }
    if root_meta is not None:
        candidate_paths.add(root_meta.path)

    by_id: dict[str, SessionMeta] = {}
    for path in candidate_paths:
        meta = _read_meta(path)
        if meta is None:
            continue
        previous = by_id.get(meta.thread_id)
        if previous is not None and previous.path != meta.path:
            raise ValueError(
                f"duplicate thread id {meta.thread_id!r}: {previous.path} and {meta.path}; WCU would be ambiguous"
            )
        by_id[meta.thread_id] = meta

    if root_id not in by_id:
        raise ValueError(f"session {root_id!r} not found below active or archived session roots")

    selected_ids = {root_id}
    changed = True
    while changed:
        changed = False
        for meta in by_id.values():
            if meta.parent_thread_id in selected_ids and meta.thread_id not in selected_ids:
                selected_ids.add(meta.thread_id)
                changed = True
    return sorted((by_id[thread_id] for thread_id in selected_ids), key=lambda item: item.thread_id)


def _normalize_usage(current: Any, line_number: int) -> tuple[dict[str, int] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(current, dict):
        return None, [f"line {line_number}: total_token_usage is not an object"]
    normalized: dict[str, int] = {}
    for field in TOKEN_FIELDS:
        if field == "total_tokens" and field not in current:
            continue
        value = current.get(field, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"line {line_number}: {field} is missing or not a non-negative integer")
            value = 0
        normalized[field] = value
    if "total_tokens" not in normalized:
        normalized["total_tokens"] = normalized.get("input_tokens", 0) + normalized.get("output_tokens", 0)
        errors.append(f"line {line_number}: total_tokens missing; derived partial total")
    minimum_total = normalized.get("input_tokens", 0) + normalized.get("output_tokens", 0)
    if normalized["total_tokens"] < minimum_total:
        errors.append(f"line {line_number}: total_tokens is below input_tokens + output_tokens")
        normalized["total_tokens"] = minimum_total
    return normalized, errors


def _usage_delta(current: dict[str, int], previous: dict[str, int]) -> dict[str, int]:
    reset = current["total_tokens"] < previous.get("total_tokens", 0)
    return {
        field: max(0, current.get(field, 0) - (0 if reset else previous.get(field, 0)))
        for field in TOKEN_FIELDS
    }


def _arguments(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("arguments") if payload.get("type") == "function_call" else payload.get("input")
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"raw": raw}
    except json.JSONDecodeError:
        return {"raw": raw}


def _output_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_output_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(_output_text(item) for item in value.values())
    return "" if value is None else str(value)


def _output_size(payload: dict[str, Any]) -> int:
    return len(_output_text(payload.get("output")))


def _spawn_role(name: str, arguments: dict[str, Any]) -> str | None:
    leaf = normalize_tool_name(name)
    raw = str(arguments.get("raw", ""))
    if leaf not in {"spawn_agent", "agent", "create_agent"} and not (
        leaf == "exec" and re.search(r"tools\.[A-Za-z0-9_]*(?:spawn_agent|create_agent)\s*\(", raw)
    ):
        return None
    direct = arguments.get("agent_type") or arguments.get("role")
    if isinstance(direct, str):
        return direct
    match = re.search(r"(?:agent_type|role)\s*:\s*['\"]([^'\"]+)['\"]", raw)
    return match.group(1) if match else "unspecified"


def _spawn_output_succeeded(output: Any) -> bool:
    text = _output_text(output).strip()
    lowered = text.lower()
    if not text or any(marker in lowered for marker in ("full-history forked", "not found", "permission denied")):
        return False
    if any(marker in text for marker in ('"agent_id"', '"task_name"', '"nickname"', "agent_id")):
        return True
    try:
        parsed = json.loads(text)
        return isinstance(parsed, dict) and not parsed.get("error")
    except json.JSONDecodeError:
        return False


def audit_log(meta: SessionMeta, large_output_chars: int = 20_000) -> dict[str, Any]:
    active_model = "unknown"
    previous_usage = {field: 0 for field in TOKEN_FIELDS}
    usage_by_model: dict[str, Counter[str]] = defaultdict(Counter)
    calls_by_model: dict[str, Counter[str]] = defaultdict(Counter)
    call_index: dict[str, tuple[str, str]] = {}
    pending_spawns: dict[str, str] = {}
    successful_spawns: Counter[str] = Counter()
    failed_spawns: Counter[str] = Counter()
    large_outputs: list[dict[str, Any]] = []
    sol_execution_calls: list[dict[str, str]] = []
    parse_errors = 0
    usage_schema_errors: list[str] = []
    token_snapshot_count = 0
    task_complete = False
    last_token_line = 0
    last_substantive_line = 0

    try:
        handle = meta.path.open()
    except OSError as exc:
        return {
            "thread_id": meta.thread_id,
            "session_id": meta.session_id,
            "parent_thread_id": meta.parent_thread_id,
            "agent_role": meta.agent_role,
            "path": str(meta.path),
            "usage_by_model": {},
            "calls_by_model": {},
            "successful_spawns": {},
            "failed_spawns": {},
            "unresolved_spawn_calls": 0,
            "large_outputs": [],
            "sol_execution_calls": [],
            "parse_errors": 1,
            "usage_schema_errors": [f"cannot open log: {exc}"],
            "token_snapshot_count": 0,
            "task_complete": False,
        }

    with handle:
        for line_number, line in enumerate(handle, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if not isinstance(record, dict) or not isinstance(record.get("payload", {}), dict):
                parse_errors += 1
                continue
            payload = record.get("payload", {})
            is_task_complete = record.get("type") == "event_msg" and payload.get("type") == "task_complete"
            substantive_after_completion = (
                record.get("type") in {"turn_context", "response_item"}
                or (record.get("type") == "event_msg" and payload.get("type") in {"task_started", "token_count", "user_message"})
            )
            if task_complete and substantive_after_completion:
                task_complete = False
            if substantive_after_completion:
                last_substantive_line = line_number
            if record.get("type") == "turn_context":
                if isinstance(payload.get("model"), str):
                    active_model = payload["model"]
                else:
                    usage_schema_errors.append(f"line {line_number}: turn_context model missing")
                continue
            if is_task_complete:
                task_complete = True
            if record.get("type") == "event_msg" and payload.get("type") == "token_count":
                current, errors = _normalize_usage(payload.get("info", {}).get("total_token_usage"), line_number)
                usage_schema_errors.extend(errors)
                if current is not None:
                    token_snapshot_count += 1
                    last_token_line = line_number
                    usage_by_model[active_model].update(_usage_delta(current, previous_usage))
                    previous_usage = current
                continue
            if record.get("type") != "response_item":
                continue

            item_type = str(payload.get("type", ""))
            if item_type in {"function_call", "custom_tool_call"}:
                name = str(payload.get("name", "unknown"))
                arguments = _arguments(payload)
                calls_by_model[active_model][name] += 1
                call_id = str(payload.get("call_id") or payload.get("id") or "")
                if call_id:
                    call_index[call_id] = (active_model, name)
                role = _spawn_role(name, arguments)
                if role is not None:
                    if call_id:
                        pending_spawns[call_id] = role
                    else:
                        failed_spawns[role] += 1
                if model_family(active_model) == "sol" and is_sol_execution(name, arguments):
                    sol_execution_calls.append({"tool": name, "line": str(line_number)})
                continue

            if item_type in {"function_call_output", "custom_tool_call_output"}:
                call_id = str(payload.get("call_id") or "")
                model, name = call_index.get(call_id, (active_model, "unknown"))
                size = _output_size(payload)
                if size >= large_output_chars:
                    large_outputs.append({"model": model, "tool": name, "chars": size, "line": line_number})
                role = pending_spawns.pop(call_id, None)
                if role is not None:
                    if _spawn_output_succeeded(payload.get("output")):
                        successful_spawns[role] += 1
                    else:
                        failed_spawns[role] += 1

    return {
        "thread_id": meta.thread_id,
        "session_id": meta.session_id,
        "parent_thread_id": meta.parent_thread_id,
        "agent_role": meta.agent_role,
        "path": str(meta.path),
        "usage_by_model": {model: dict(counter) for model, counter in usage_by_model.items()},
        "calls_by_model": {model: dict(counter) for model, counter in calls_by_model.items()},
        "successful_spawns": dict(successful_spawns),
        "failed_spawns": dict(failed_spawns),
        "unresolved_spawn_calls": len(pending_spawns),
        "large_outputs": large_outputs,
        "sol_execution_calls": sol_execution_calls,
        "parse_errors": parse_errors,
        "usage_schema_errors": usage_schema_errors,
        "token_snapshot_count": token_snapshot_count,
        "task_complete": task_complete,
        "last_token_line": last_token_line,
        "last_substantive_line": last_substantive_line,
    }


def audit_session_tree(target: str, sessions_root: Path, large_output_chars: int = 20_000) -> dict[str, Any]:
    metas = discover_session_tree(target, sessions_root)
    sessions = [audit_log(meta, large_output_chars=large_output_chars) for meta in metas]
    model_totals: dict[str, Counter[str]] = defaultdict(Counter)
    family_totals: dict[str, Counter[str]] = defaultdict(Counter)
    roles: Counter[str] = Counter()
    children_by_parent: Counter[str] = Counter(meta.parent_thread_id for meta in metas if meta.parent_thread_id)
    large_outputs: list[dict[str, Any]] = []
    sol_execution_calls: list[dict[str, Any]] = []
    completeness_violations: list[str] = []

    for session in sessions:
        thread_id = str(session["thread_id"])
        if session["agent_role"]:
            roles[str(session["agent_role"])] += 1
        for model, usage in session["usage_by_model"].items():
            model_totals[model].update(usage)
            family_totals[model_family(model)].update(usage)
        for output in session["large_outputs"]:
            large_outputs.append({"thread_id": thread_id, **output})
        for call in session["sol_execution_calls"]:
            sol_execution_calls.append({"thread_id": thread_id, **call})

        expected_children = sum(session["successful_spawns"].values())
        discovered_children = children_by_parent[thread_id]
        if expected_children > discovered_children:
            completeness_violations.append(
                f"thread {thread_id}: {expected_children} successful spawn(s) but only {discovered_children} child log(s)"
            )
        if session["unresolved_spawn_calls"]:
            completeness_violations.append(
                f"thread {thread_id}: {session['unresolved_spawn_calls']} spawn call(s) have no output"
            )
        if session["parse_errors"]:
            completeness_violations.append(f"thread {thread_id}: {session['parse_errors']} corrupt JSON line(s)")
        if session["usage_schema_errors"]:
            completeness_violations.append(
                f"thread {thread_id}: {len(session['usage_schema_errors'])} token/schema error(s)"
            )
        if not session["token_snapshot_count"]:
            completeness_violations.append(f"thread {thread_id}: no valid token snapshot")
        if not session["task_complete"]:
            completeness_violations.append(f"thread {thread_id}: task_complete event missing")
        elif session["last_token_line"] < session["last_substantive_line"]:
            completeness_violations.append(f"thread {thread_id}: final token snapshot precedes later activity")

    unknown_models = sorted(
        model for model in model_totals
        if model_family(model) == "unknown" and model_totals[model]["total_tokens"]
    )
    weighted_cost = sum(
        counter["total_tokens"] * MODEL_WEIGHTS.get(model_family(model), 0)
        for model, counter in model_totals.items()
    )
    total_tokens = sum(counter["total_tokens"] for counter in model_totals.values())
    lower_cost_tokens = sum(family_totals[family]["total_tokens"] for family in ("terra", "luna"))

    violations = list(completeness_violations)
    if sol_execution_calls:
        violations.append(f"{len(sol_execution_calls)} non-read-only tool call(s) were made by Sol")
    if unknown_models:
        violations.append("unknown model family: " + ", ".join(unknown_models))
    observations = []
    if total_tokens and not lower_cost_tokens:
        observations.append("no Terra or Luna tokens were observed; confirm that all work was judgment-only")

    return {
        "root": target,
        "session_count": len(sessions),
        "cost_status": "partial_uncertain" if completeness_violations or unknown_models else "complete",
        "weighted_cost_units": weighted_cost,
        "total_tokens": total_tokens,
        "model_totals": {model: dict(counter) for model, counter in sorted(model_totals.items())},
        "family_totals": {family: dict(family_totals[family]) for family in ("sol", "terra", "luna", "unknown")},
        "subagent_roles": dict(roles),
        "large_outputs": sorted(large_outputs, key=lambda item: item["chars"], reverse=True),
        "sol_execution_calls": sol_execution_calls,
        "completeness_violations": completeness_violations,
        "routing_violations": violations,
        "routing_observations": observations,
        "sessions": sessions,
    }


def render_report(report: dict[str, Any]) -> str:
    uncertainty = " [UNCERTAIN/PARTIAL]" if report["cost_status"] != "complete" else ""
    lines = [
        f"Sessions: {report['session_count']}",
        f"Raw tokens: {report['total_tokens']:,}{uncertainty}",
        f"Weighted cost: {report['weighted_cost_units']:,} WCU{uncertainty} (25*Sol + 10*Terra + 1*Luna)",
        "",
        "Family  Tokens       Weight  WCU",
    ]
    for family in ("sol", "terra", "luna", "unknown"):
        tokens = report["family_totals"][family].get("total_tokens", 0)
        weight = MODEL_WEIGHTS.get(family, 0)
        lines.append(f"{family:<7} {tokens:>12,} {weight:>7} {tokens * weight:>12,}")
    if report["subagent_roles"]:
        lines.extend(("", "Subagent roles: " + ", ".join(f"{key}={value}" for key, value in sorted(report["subagent_roles"].items()))))
    lines.extend(("", f"Large tool outputs (>= threshold): {len(report['large_outputs'])}"))
    if report["routing_violations"]:
        lines.append("Routing/completeness violations:")
        lines.extend(f"- {item}" for item in report["routing_violations"])
    else:
        lines.append("Routing/completeness violations: none detected")
    if report["routing_observations"]:
        lines.append("Observations:")
        lines.extend(f"- {item}" for item in report["routing_observations"])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="root thread id or path to its rollout JSONL")
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--large-output-chars", type=int, default=20_000)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = audit_session_tree(args.target, args.sessions_root, args.large_output_chars)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_report(report))
    return 1 if report["routing_violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
