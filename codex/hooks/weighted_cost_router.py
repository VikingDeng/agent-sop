#!/usr/bin/env python3
"""Fail-loud Codex guardrails for weighted-cost subagent routing."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from typing import Any

from weighted_routing_policy import (
    MAX_FUNCTIONS_EXEC_SOURCE,
    ROLE_MODEL_FAMILIES,
    analyze_functions_exec,
    classify_spawn_request,
    classify_spawn_result,
    command_text,
    is_sol_execution,
    normalize_tool_name,
    post_failure_role_allowed,
)


SESSION_CONTEXT = """Weighted-cost routing is active.
Objective: minimize WCU = 25*Sol tokens + 10*Terra tokens + 1*Luna tokens subject to unchanged acceptance criteria and review gates.
Before execution, record LUNA_ELIGIBLE=yes/no. Use Luna first for bounded labor-heavy implementation, tests, fixtures, commands, logs, and data plumbing; use Terra for semantic cross-file work or evidence-backed Luna escalation; reserve Sol for architecture, research design, ambiguity resolution, final judgment, and explicitly triggered high-risk review.
Do not use Sol for source edits, builds, tests, installs, repetitive inspection, or bulk output. If runtime evidence says gpt-5.6-luna is unavailable, stop the package and refresh/start a new task/turn; do not silently escalate to Terra or direct Sol. Escalation must name prior role, failure evidence, scope delta, and unchanged/changed acceptance criteria. risk_reviewer requires HIGH_RISK_TRIGGER and a compact EVIDENCE_PACK. Return summaries instead of large raw tool output.
"""

ROLE_CONTEXT = {
    "explorer": "Stay targeted and read-only. Return a compact file/symbol map; do not dump large files.",
    "focused_worker": "Perform only the assigned mechanical edit and declared checks. Escalate semantic ambiguity.",
    "luna_executor": "Own the bounded labor-heavy implementation. Follow the frozen architecture and binary acceptance criteria; escalate judgment-heavy ambiguity.",
    "verifier": "Run the declared oracle and return concise raw evidence plus exit codes; do not edit source.",
    "worker": "This is a Terra escalation. Resolve the documented semantic/cross-file issue without redesigning the task.",
    "terra_debugger": "Diagnose an unknown root cause hypothesis-first: state competing hypotheses, rank them by evidence, and run discriminating checks. Use no-fallback behavior; return a compact evidence packet and escalate when evidence or the contract is insufficient.",
    "reviewer": "Review independently and read-only; findings need severity, location, failure path, and minimal repair.",
    "risk_reviewer": "Review only the explicit HIGH_RISK_TRIGGER against the compact EVIDENCE_PACK. Stay read-only and avoid broad rediscovery.",
}

LOWER_COST_ROLES = set(ROLE_MODEL_FAMILIES) - {"risk_reviewer"}

def _emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")


def _context(event: str, message: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": message,
        }
    }


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _posttool_block(reason: str) -> dict[str, Any]:
    return {
        "decision": "block",
        "reason": reason,
        "continue": False,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": reason,
        }
    }


def _tool_input(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get("tool_input")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return {"raw": value}
    return {}


def _active_model(data: dict[str, Any]) -> str:
    for key in ("model", "model_name"):
        value = data.get(key)
        if isinstance(value, str):
            return value.lower()
    return ""


def _model_matches_family(model: str, family: str) -> bool:
    return re.search(rf"(?:^|[-_.:/]){re.escape(family)}(?:$|[-_.:/])", model) is not None


def _prompt(tool_input: dict[str, Any]) -> str:
    values = []
    for key in ("message", "prompt", "task", "instructions"):
        value = tool_input.get(key)
        if isinstance(value, str):
            values.append(value)
    return "\n".join(values)


def _has_full_fork(tool_input: dict[str, Any]) -> bool:
    if tool_input.get("fork_context") is True:
        return True
    return str(tool_input.get("fork_turns", "")).lower() in {"all", "full"}


def _request_conflict_reason(request: Any) -> str:
    if request.identity_alias_conflict:
        return "Weighted router: spawn identity aliases disagree; this lifecycle call is ambiguous and blocked."
    if request.model_alias_conflict:
        return "Weighted router: spawn model aliases disagree; this lifecycle call is ambiguous and blocked."
    expected_family = ROLE_MODEL_FAMILIES[request.role].title()
    return (
        f"Weighted router: {request.role} is configured for the {expected_family} family; "
        "omit the model override or select a matching family."
    )


def _state_path(session_id: str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    base = Path(os.environ.get("CODEX_ROUTER_STATE_DIR", Path.home() / ".codex" / "router-state"))
    return base / f"{safe_id}.json"


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("router state is not an object")
    return payload


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, separators=(",", ":"))
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _turn_id(data: dict[str, Any]) -> str:
    candidate = data.get("turn_id")
    return candidate if isinstance(candidate, str) and candidate else ""


def _record_luna_capability(session_id: str, turn_id: str, *, unavailable: bool, verified: bool) -> bool:
    safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    safe_turn = re.sub(r"[^A-Za-z0-9_.-]", "_", turn_id or "unknown")
    capability_dir = _state_path("capability").parent / "capability"
    try:
        capability_dir.mkdir(parents=True, exist_ok=True)
        markers = []
        if unavailable:
            markers.append(capability_dir / f"{safe_session}--{safe_turn}.unavailable")
        if verified:
            markers.append(capability_dir / f"{safe_session}--{safe_turn}.verified")
        for marker in markers:
            try:
                with marker.open("x") as handle:
                    handle.write(f"session_id={session_id}\nturn_id={turn_id}\n")
            except FileExistsError:
                pass
        return True
    except OSError as exc:
        _record_error(f"Luna capability state failure: {type(exc).__name__}: {exc}")
        return False


def _luna_gate(data: dict[str, Any], request: Any) -> str | None:
    session_id = str(data.get("session_id", ""))
    turn_id = _turn_id(data)
    if not turn_id:
        return "Weighted router: lifecycle call is missing the documented top-level turn_id; this call is blocked without persisting capability state."
    if not session_id:
        return None
    try:
        safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
        safe_turn = re.sub(r"[^A-Za-z0-9_.-]", "_", turn_id)
        capability_dir = _state_path("capability").parent / "capability"
        unavailable_marker = capability_dir / f"{safe_session}--{safe_turn}.unavailable"
        unavailable = unavailable_marker.exists()
    except OSError as exc:
        _record_error(f"Luna capability read failure: {type(exc).__name__}: {exc}")
        return "Weighted router: Luna capability state is uncertain; stop this package and refresh/start a new task/turn."
    if not unavailable:
        return None
    if post_failure_role_allowed(request):
        return None
    return "Weighted router: runtime evidence rejected gpt-5.6-luna in this turn. Stop the package; do not escalate to Terra or execute directly on Sol. Refresh/start a new task/turn."


def _record_error(message: str) -> None:
    try:
        path = _state_path("hook-errors").with_suffix(".jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as handle:
            handle.write(json.dumps({"time": time.time(), "error": message}, separators=(",", ":")) + "\n")
    except OSError:
        print(f"weighted router error (logging failed): {message}", file=sys.stderr)


def _too_many_waits(session_id: str, signature: str, now: float) -> bool:
    """Deny the third wait/poll of the same target inside 90 seconds."""
    path = _state_path(session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = _load_state(path)
        waits = [
            value for value in previous.get("waits", [])
            if isinstance(value, dict) and now - float(value.get("time", 0)) < 90
        ]
        matching = [value for value in waits if value.get("signature") == signature]
        deny = len(matching) >= 2
        waits.append({"time": now, "signature": signature})
        previous["waits"] = waits[-4:]
        _write_state(path, previous)
        return deny
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        _record_error(f"wait-state failure: {type(exc).__name__}: {exc}")
        return True


def handle(data: dict[str, Any]) -> dict[str, Any] | None:
    event_value = data.get("hook_event_name")
    if not isinstance(event_value, str) or not event_value:
        raise ValueError("hook_event_name is missing or not a string")
    event = event_value
    if event not in {"SessionStart", "SubagentStart", "PreToolUse", "PostToolUse"}:
        raise ValueError(f"unsupported hook event: {event}")
    if event == "SessionStart":
        return _context(event, SESSION_CONTEXT)

    if event == "SubagentStart":
        role = str(data.get("agent_type", "")).lower()
        message = ROLE_CONTEXT.get(role)
        return _context(event, message) if message else None

    if event == "PostToolUse":
        if not isinstance(data.get("tool_name"), str):
            _record_error("PostToolUse missing string tool_name")
            return _posttool_block("Weighted router: PostToolUse schema is uncertain; stop this package and refresh/start a new task/turn.")
        if not isinstance(data.get("tool_input"), (dict, str)) or "tool_response" not in data:
            _record_error("PostToolUse missing or malformed tool_input/tool_response")
            return _posttool_block("Weighted router: PostToolUse result schema is uncertain; stop this package and refresh/start a new task/turn.")
        tool_name = data["tool_name"]
        tool_input = _tool_input(data)
        try:
            request = classify_spawn_request(tool_name, tool_input)
        except ValueError:
            request = None
        if request is not None and request.has_conflict:
            reason = _request_conflict_reason(request)
            _record_error(reason)
            return _posttool_block(reason)
        response = data["tool_response"]
        result = classify_spawn_result(response, luna_role=request.luna_role if request else None)
        if request is not None and request.luna_role is not None and (result.unknown_luna or result.succeeded):
            turn_id = _turn_id(data)
            session_id = str(data.get("session_id", ""))
            if not session_id or not turn_id:
                _record_error("PostToolUse Luna evidence missing session_id or turn_id")
                return _posttool_block("Weighted router: Luna runtime evidence is unscoped; stop this package and refresh/start a new task/turn.")
            if not _record_luna_capability(
                session_id,
                turn_id,
                unavailable=result.unknown_luna,
                verified=result.succeeded,
            ):
                return _posttool_block("Weighted router: Luna capability state could not be persisted; stop this package and refresh/start a new task/turn.")
            if result.unknown_luna:
                return _posttool_block("Weighted router: gpt-5.6-luna was rejected as unavailable. Stop this package; do not escalate to Terra or execute directly on Sol. Refresh/start a new task/turn.")
        return None

    if event != "PreToolUse":
        return None

    if not isinstance(data.get("model"), str) or not isinstance(data.get("tool_name"), str):
        _record_error("PreToolUse missing string model or tool_name")
        return _deny("Weighted router: Hook input schema is uncertain (missing model/tool_name); tool use is blocked. Disable the router registration manually only for emergency recovery.")
    if not isinstance(data.get("tool_input"), (dict, str)):
        _record_error("PreToolUse has unsupported tool_input type")
        return _deny("Weighted router: Hook input schema is uncertain (unsupported tool_input); tool use is blocked.")

    tool_name = data["tool_name"].lower()
    tool_leaf = normalize_tool_name(tool_name)
    tool_input = _tool_input(data)

    active_model = _active_model(data)
    if not any(family in active_model for family in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")):
        _record_error(f"PreToolUse has unsupported model: {active_model}")
        return _deny("Weighted router: active model is outside the configured Sol/Terra/Luna families; routing cost and permissions are uncertain.")

    if tool_leaf in {"agent", "spawn_agent", "create_agent"}:
        request = classify_spawn_request(tool_name, tool_input)
        role = request.role or ""
        model_override = request.model
        if request.has_conflict:
            return _deny(_request_conflict_reason(request))
        capability_denial = _luna_gate(data, request)
        if capability_denial:
            return _deny(capability_denial)
        if _has_full_fork(tool_input):
            return _deny(
                "Weighted router: do not fork the full parent history. Send a compact work package and use fork_turns=none/fork_context=false."
            )
        if role == "risk_reviewer":
            prompt = _prompt(tool_input)
            missing = [marker for marker in ("HIGH_RISK_TRIGGER:", "EVIDENCE_PACK:") if marker not in prompt]
            if missing:
                return _deny(
                    "Weighted router: risk_reviewer is Sol Max and requires explicit "
                    + " and ".join(missing)
                    + ". Use Luna/Terra reviewer for ordinary review."
                )
        elif role not in LOWER_COST_ROLES and not any(
            _model_matches_family(model_override or "", family) for family in ("luna", "terra")
        ):
            return _deny(
                "Weighted router: an unspecified/default child may inherit Sol. Select an explicit Luna/Terra role or model; use risk_reviewer only with its trigger and evidence pack."
            )

    if tool_leaf == "exec":
        raw = command_text(tool_input)
        try:
            analysis = analyze_functions_exec(raw)
        except ValueError as exc:
            return _deny(f"Weighted router: nested agent factory syntax is not policy-verifiable: {exc}.")
        request = classify_spawn_request(tool_name, tool_input)
        if request is not None and request.has_conflict:
            return _deny(_request_conflict_reason(request))
        capability_denial = _luna_gate(data, request)
        if capability_denial:
            return _deny(capability_denial)
        if re.search(r"tools\.[A-Za-z0-9_]*(?:wait_agent|wait_for_agent|wait_for_subagent)\s*\(", raw):
            session_id = str(data.get("session_id", "unknown"))
            if _too_many_waits(session_id, raw, time.time()):
                return _deny("Weighted router: repeated nested polling of the same target is blocked.")

    if tool_leaf in {"wait_agent", "wait", "wait_for_agent", "wait_for_subagent"}:
        session_id = str(data.get("session_id", "unknown"))
        signature = json.dumps(tool_input, sort_keys=True, separators=(",", ":"))
        if _too_many_waits(session_id, signature, time.time()):
            return _deny(
                "Weighted router: repeated short polling is blocked. Continue independent work or issue one bounded long wait after progress."
            )

    if "gpt-5.6-sol" in active_model:
        capability_denial = _luna_gate(data, None)
        if capability_denial and is_sol_execution(tool_name, tool_input):
            return _deny(capability_denial)
        if is_sol_execution(tool_name, tool_input):
            command = command_text(tool_input)
            if tool_leaf in {"bash", "exec", "exec_command", "shell", "terminal"} and command:
                reason = (
                    "Weighted router: Sol may inspect targeted evidence but may not run labor-heavy builds, tests, installs, lifecycle commands, Git delivery, or nested mutations. Delegate the command to Luna verifier/executor."
                )
            else:
                reason = (
                    "Weighted router: Sol is the planner/judge, not the source writer. Delegate this bounded edit to luna_executor/focused_worker; escalate to Terra only with failure evidence."
                )
            return _deny(
                reason
            )

    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("top-level hook input must be an object")
        result = handle(data)
        if result is not None:
            _emit(result)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        message = f"invalid hook input: {type(exc).__name__}: {exc}"
        _record_error(message)
        print(f"weighted router error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
