#!/usr/bin/env python3
"""Fail-loud Codex guardrails for weighted-cost subagent routing."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from typing import Any

from weighted_routing_policy import (
    GLOBAL_LOOP_BUDGET,
    MAX_FUNCTIONS_EXEC_SOURCE,
    ROLE_MODEL_FAMILIES,
    analyze_functions_exec,
    classify_spawn_request,
    classify_spawn_result,
    command_text,
    is_sol_execution,
    normalize_tool_name,
    package_contract_error,
    parse_recontract_evidence,
    post_failure_role_allowed,
    spawn_request_signature,
)


SESSION_CONTEXT = """Weighted-cost routing is active in adaptive advisory mode unless CODEX_ROUTER_ENFORCEMENT=strict.
Objective: minimize WCU = 25*Sol tokens + 10*Terra tokens + 1*Luna tokens without weakening the requested outcome or its acceptance evidence.
Prefer Luna for bounded labor-heavy execution, Terra for semantic/debugging pressure and ordinary review, and Sol for architecture, research design, ambiguity, and final judgment. These are preferences, not permission gates. If Luna is unavailable, transparently use the lowest-cost available capable role, normally Terra.
Let the agent choose exploration order, work decomposition, repair count, and review depth from current evidence. Package IDs, phase markers, and strict loop budgets are optional coordination aids in advisory mode. Avoid full-history forks, tiny one-command delegations, repeated polling, and large raw returns.
Keep tool returns compact (target <=20k chars when practical); preserve full logs as artifacts and return summaries with decisive evidence and exit codes.
Continue while new work reduces uncertainty. Re-plan when the same failure repeats without progress, the outcome contract changes, or expected cost becomes disproportionate. Preserve real evidence and never lower acceptance criteria silently.
"""

STRICT_SESSION_CONTEXT = """Weighted-cost routing is active in strict enforcement mode.
Objective: minimize WCU = 25*Sol tokens + 10*Terra tokens + 1*Luna tokens without weakening the requested outcome or its acceptance evidence.
Strict enforcement: Sol non-read-only direct execution is denied. Fixed Luna-eligible packages must start with Luna. Luna unavailable/unknown fails closed for that package; no Terra/Sol substitution. Read-only planning/judgment remains allowed. Lifecycle/spawn coverage may still require supervisor compliance.
Use Luna for fixed Luna-eligible implementation packages, Terra only for explicitly permitted semantic/debugging work or ordinary review, and Sol for read-only architecture, research design, ambiguity, and final judgment.
Keep tool returns compact (target <=20k chars when practical); preserve full logs as artifacts and return summaries with decisive evidence and exit codes.
Preserve real evidence and never lower acceptance criteria silently. If a strict invariant or required runtime capability is uncertain, stop the affected package and report the uncertainty.
"""

ROLE_CONTEXT = {
    "explorer": "Stay targeted and read-only. Return a compact file/symbol map; do not dump large files.",
    "focused_worker": "Perform only the assigned mechanical edit and declared checks. Escalate semantic ambiguity.",
    "luna_executor": "Own the bounded labor-heavy implementation. Follow the frozen architecture and binary acceptance criteria; escalate judgment-heavy ambiguity.",
    "verifier": "Run the declared oracle and return concise raw evidence plus exit codes; do not edit source.",
    "worker": "Resolve only the documented semantic/cross-file issue. A Terra initial requires a nonempty objective LUNA_ELIGIBLE=no(reason); otherwise this is the single consolidated correction.",
    "terra_debugger": "Diagnose an unknown root cause hypothesis-first: rank competing hypotheses and run discriminating checks. Adapt tools or implementation paths explicitly while preserving the outcome contract; return a compact evidence packet.",
    "reviewer": "Review independently and read-only; findings need severity, location, failure path, and minimal repair.",
    "risk_reviewer": "Review only the explicit HIGH_RISK_TRIGGER against the compact EVIDENCE_PACK. Stay read-only and avoid broad rediscovery.",
}

STOP_TOKEN_THRESHOLD = 100_000
STOP_TOOL_TYPES = {
    "function_call",
    "custom_tool_call",
    "function_call_output",
    "custom_tool_call_output",
}

LOWER_COST_ROLES = set(ROLE_MODEL_FAMILIES) - {"risk_reviewer"}


def _strict_enforcement() -> bool:
    return os.environ.get("CODEX_ROUTER_ENFORCEMENT", "advisory").strip().lower() == "strict"


def _session_context() -> str:
    return STRICT_SESSION_CONTEXT if _strict_enforcement() else SESSION_CONTEXT

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


def _posttool_context(reason: str) -> dict[str, Any]:
    return {
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


def _spawn_signature(tool_name: str, tool_input: dict[str, Any]) -> str:
    return spawn_request_signature(tool_name, tool_input)


def _reservation_paths(session_id: str, namespace: str, key: str) -> tuple[Path, Path]:
    base = _state_path("reservations").parent / "reservations"
    digest = hashlib.sha256(f"{session_id}\0{namespace}\0{key}".encode("utf-8")).hexdigest()
    return base / f"{digest}.reserved", base / f"{digest}.committed"


def _reservation_specs(request: Any) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    if request.package_phase in GLOBAL_LOOP_BUDGET:
        specs.append(("package-phase", f"{request.package_id}\0{request.package_phase}"))
    if request.role == "risk_reviewer":
        specs.append(("session-risk-reviewer", "max-one"))
    return specs


def _release_reservations(session_id: str, specs: list[tuple[str, str]]) -> None:
    for namespace, key in specs:
        reserved, _ = _reservation_paths(session_id, namespace, key)
        try:
            reserved.unlink()
        except FileNotFoundError:
            pass


def _reserve_spawn_budget(data: dict[str, Any], request: Any) -> str | None:
    if (contract_error := package_contract_error(request)) is not None:
        return f"Weighted router: invalid package contract: {contract_error}."
    session_id = str(data.get("session_id", ""))
    if not session_id:
        return "Weighted router: package budget is unscoped without session_id; spawn is blocked."
    acquired: list[tuple[str, str]] = []
    try:
        for namespace, key in _reservation_specs(request):
            reserved, committed = _reservation_paths(session_id, namespace, key)
            reserved.parent.mkdir(parents=True, exist_ok=True)
            if committed.exists():
                _release_reservations(session_id, acquired)
                label = "Sol risk_reviewer" if namespace == "session-risk-reviewer" else request.package_phase
                return f"Weighted router: {label} budget is already committed for this session/package."
            try:
                with reserved.open("x") as handle:
                    handle.write(f"session_id={session_id}\nnamespace={namespace}\n")
            except FileExistsError:
                _release_reservations(session_id, acquired)
                label = "Sol risk_reviewer" if namespace == "session-risk-reviewer" else request.package_phase
                return f"Weighted router: {label} budget already has an in-flight reservation."
            acquired.append((namespace, key))
        return None
    except OSError as exc:
        _release_reservations(session_id, acquired)
        _record_error(f"reservation state failure: {type(exc).__name__}: {exc}")
        return "Weighted router: package/risk reservation state is uncertain; spawn is blocked."


def _settle_spawn_budget(data: dict[str, Any], request: Any, *, succeeded: bool) -> bool:
    session_id = str(data.get("session_id", ""))
    if not session_id:
        return False
    try:
        for namespace, key in _reservation_specs(request):
            reserved, committed = _reservation_paths(session_id, namespace, key)
            if succeeded:
                if committed.exists():
                    continue
                if not reserved.exists():
                    raise FileNotFoundError(f"missing reservation for {namespace}")
                os.replace(reserved, committed)
            else:
                try:
                    reserved.unlink()
                except FileNotFoundError:
                    pass
        return True
    except OSError as exc:
        _record_error(f"reservation settlement failure: {type(exc).__name__}: {exc}")
        return False


def _thread_limit_retry_marker(session_id: str, package_id: str) -> Path:
    reserved, _ = _reservation_paths(session_id, "thread-limit-package-retry", package_id)
    return reserved


def _thread_limit_retry_gate(
    data: dict[str, Any],
    tool_name: str,
    tool_input: dict[str, Any],
    request: Any,
) -> str | None:
    session_id = str(data.get("session_id", ""))
    if not session_id:
        return "Weighted router: thread-limit recovery is unscoped without session_id; list/close agents manually and stop this package."
    path = _state_path(session_id)
    try:
        state = _load_state(path)
        packages = state.get("thread_limit_packages", {})
        if not isinstance(packages, dict):
            raise ValueError("thread_limit_packages is not an object")
        evidence, evidence_error = parse_recontract_evidence(
            request.message,
            new_package_id=request.package_id,
        )
        if evidence_error:
            return f"Weighted router: invalid re-contract evidence: {evidence_error}."
        active_packages = {
            package_id: value
            for package_id, value in packages.items()
            if isinstance(value, dict) and value.get("status") in {"recovery", "locked"}
        }
        package_state = packages.get(request.package_id)
        signature = _spawn_signature(tool_name, tool_input)
        if isinstance(package_state, dict) and package_state.get("status") in {"locked", "recontracted"}:
            return (
                f"Weighted router: package {request.package_id!r} is locked after thread-limit recovery or explicit re-contracting. "
                "Do not spawn again; reuse an already-open matching Luna/Terra thread or stop. "
                "Thread-limit is not Luna model unavailability."
            )
        if isinstance(package_state, dict) and package_state.get("status") == "recovery":
            expected = package_state.get("signature")
            if signature != expected:
                return (
                    f"Weighted router: package {request.package_id!r} is in thread-limit recovery and permits only "
                    "one exact same-signature retry; changed role/model/message/phase/tool input is blocked."
                )
            if _thread_limit_retry_marker(session_id, str(request.package_id)).exists():
                return (
                    f"Weighted router: package {request.package_id!r} already has its single thread-limit retry in flight; "
                    "another retry is blocked."
                )
            return None
        active_other_packages = set(active_packages) - {request.package_id}
        if active_other_packages:
            if evidence is None:
                return (
                    "Weighted router: a new PACKAGE_ID after thread-limit recovery requires explicit re-contract evidence "
                    "linking the old/new package IDs and contract hashes, reason, and scope/acceptance delta."
                )
            if evidence.old_package_id not in active_other_packages:
                return (
                    "Weighted router: RECONTRACT_OLD_PACKAGE_ID does not identify an observed package in recovery/locked state."
                )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        _record_error(f"thread-limit retry state failure: {type(exc).__name__}: {exc}")
        return "Weighted router: thread-limit retry state is uncertain; list/close agents and stop this package."
    return None


def _commit_thread_limit_preflight(
    data: dict[str, Any],
    tool_name: str,
    tool_input: dict[str, Any],
    request: Any,
) -> str | None:
    """Atomically acquire retry/lineage state after every other PreTool gate passes."""
    session_id = str(data.get("session_id", ""))
    if not session_id:
        return "Weighted router: thread-limit recovery is unscoped without session_id; list/close agents manually and stop this package."
    path = _state_path(session_id)
    try:
        state = _load_state(path)
        packages = state.get("thread_limit_packages", {})
        if not isinstance(packages, dict):
            raise ValueError("thread_limit_packages is not an object")
        evidence, evidence_error = parse_recontract_evidence(
            request.message,
            new_package_id=request.package_id,
        )
        if evidence_error:
            return f"Weighted router: invalid re-contract evidence: {evidence_error}."
        package_state = packages.get(request.package_id)
        signature = _spawn_signature(tool_name, tool_input)
        if isinstance(package_state, dict) and package_state.get("status") in {"locked", "recontracted"}:
            return (
                f"Weighted router: package {request.package_id!r} is locked after thread-limit recovery or explicit re-contracting. "
                "Do not spawn again; reuse an already-open matching Luna/Terra thread or stop. "
                "Thread-limit is not Luna model unavailability."
            )
        if isinstance(package_state, dict) and package_state.get("status") == "recovery":
            if signature != package_state.get("signature"):
                return (
                    f"Weighted router: package {request.package_id!r} is in thread-limit recovery and permits only "
                    "one exact same-signature retry; changed role/model/message/phase/tool input is blocked."
                )
            marker = _thread_limit_retry_marker(session_id, str(request.package_id))
            marker.parent.mkdir(parents=True, exist_ok=True)
            try:
                with marker.open("x") as handle:
                    handle.write(f"session_id={session_id}\npackage_id={request.package_id}\nsignature={signature}\n")
            except FileExistsError:
                return (
                    f"Weighted router: package {request.package_id!r} already has its single thread-limit retry in flight; "
                    "another retry is blocked."
                )
            return None

        active_packages = {
            package_id: value
            for package_id, value in packages.items()
            if isinstance(value, dict) and value.get("status") in {"recovery", "locked"}
        }
        active_other_packages = set(active_packages) - {request.package_id}
        if active_other_packages:
            if evidence is None:
                return (
                    "Weighted router: a new PACKAGE_ID after thread-limit recovery requires explicit re-contract evidence "
                    "linking the old/new package IDs and contract hashes, reason, and scope/acceptance delta."
                )
            if evidence.old_package_id not in active_other_packages:
                return (
                    "Weighted router: RECONTRACT_OLD_PACKAGE_ID does not identify an observed package in recovery/locked state."
                )
            old_state = dict(packages[evidence.old_package_id])
            old_state["status"] = "recontracted"
            old_state["recontracted_to"] = evidence.new_package_id
            packages[evidence.old_package_id] = old_state
            state["thread_limit_packages"] = packages
            _write_state(path, state)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        _record_error(f"thread-limit preflight commit failure: {type(exc).__name__}: {exc}")
        return "Weighted router: thread-limit retry state is uncertain; list/close agents and stop this package."
    return None


def _settle_thread_limit_recovery(
    data: dict[str, Any],
    tool_name: str,
    tool_input: dict[str, Any],
    request: Any,
    result: Any,
) -> str:
    session_id = str(data.get("session_id", ""))
    if not session_id:
        return "error"
    path = _state_path(session_id)
    try:
        state = _load_state(path)
        packages = state.get("thread_limit_packages", {})
        if not isinstance(packages, dict):
            raise ValueError("thread_limit_packages is not an object")
        package_id = str(request.package_id)
        signature = _spawn_signature(tool_name, tool_input)
        package_state = packages.get(package_id)
        if isinstance(package_state, dict) and package_state.get("status") == "recovered":
            if not result.thread_limit:
                return "none"
            package_state["status"] = "locked"
            package_state["lock_reason"] = "later_thread_limit_after_retry"
            packages[package_id] = package_state
            state["thread_limit_packages"] = packages
            _write_state(path, state)
            return "retry_failed"
        if not isinstance(package_state, dict):
            if not result.thread_limit:
                return "none"
            packages[package_id] = {
                "status": "recovery",
                "signature": signature,
                "retry_count": 0,
            }
            state["thread_limit_packages"] = packages
            _write_state(path, state)
            return "entered_recovery"
        if package_state.get("status") == "locked":
            return "error"
        marker = _thread_limit_retry_marker(session_id, package_id)
        if package_state.get("signature") != signature or not marker.exists():
            package_state["status"] = "locked"
            package_state["lock_reason"] = "unreserved_or_changed_signature_retry_result"
            packages[package_id] = package_state
            state["thread_limit_packages"] = packages
            _write_state(path, state)
            return "error"
        marker.unlink()
        package_state["retry_count"] = 1
        if result.succeeded:
            package_state["status"] = "recovered"
            outcome = "retry_succeeded"
        else:
            package_state["status"] = "locked"
            package_state["lock_reason"] = "retry_failed"
            outcome = "retry_failed"
        packages[package_id] = package_state
        state["thread_limit_packages"] = packages
        _write_state(path, state)
        return outcome
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        _record_error(f"thread-limit recovery settlement failure: {type(exc).__name__}: {exc}")
        return "error"


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


def _transcript_turn_id(payload: dict[str, Any]) -> str:
    value = payload.get("turn_id")
    if isinstance(value, str) and value:
        return value
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    if isinstance(metadata, dict) and isinstance(metadata.get("turn_id"), str):
        return metadata["turn_id"]
    return ""


def _event_token_total(record: dict[str, Any], payload: dict[str, Any]) -> int | None:
    candidates: list[Any] = [
        payload.get("last_token_usage"),
        record.get("last_token_usage"),
    ]
    info = payload.get("info")
    if isinstance(info, dict):
        candidates.append(info.get("last_token_usage"))
    for usage in candidates:
        if (
            isinstance(usage, dict)
            and isinstance(usage.get("total_tokens"), int)
            and not isinstance(usage.get("total_tokens"), bool)
            and usage["total_tokens"] >= 0
        ):
            return usage["total_tokens"]
    return None


def _is_git_checkout(cwd: Any) -> bool:
    if not isinstance(cwd, str) or not cwd:
        return False
    try:
        path = Path(cwd).expanduser().resolve()
    except (OSError, RuntimeError):
        return False
    if not path.is_dir():
        return False
    return any((candidate / ".git").exists() for candidate in (path, *path.parents))


def _stop_evidence(data: dict[str, Any]) -> tuple[bool, str, list[str]]:
    """Return (substantial, uncertainty, command snippets) from the current turn only."""
    transcript = data.get("transcript_path")
    turn_id = data.get("turn_id")
    if not isinstance(transcript, str) or not transcript or not isinstance(turn_id, str) or not turn_id:
        return False, "Stop transcript path or turn_id is missing", []
    calls = 0
    outputs = 0
    tagged_max_tokens = 0
    task_max_tokens = 0
    saw_unattributed_token = False
    commands: list[str] = []
    active_task_turn = ""
    task_boundary_ambiguous = False
    try:
        with Path(transcript).open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except (TypeError, ValueError, json.JSONDecodeError):
                    return False, "Stop transcript contains malformed JSON", []
                if not isinstance(record, dict) or not isinstance(record.get("payload"), dict):
                    continue
                payload = record["payload"]
                item_type = str(payload.get("type", ""))
                payload_turn_id = _transcript_turn_id(payload)
                if item_type == "task_started":
                    if active_task_turn:
                        task_boundary_ambiguous = True
                    active_task_turn = payload_turn_id
                elif item_type == "task_complete":
                    if not payload_turn_id or active_task_turn != payload_turn_id:
                        task_boundary_ambiguous = True
                    active_task_turn = ""

                is_current_turn = payload_turn_id == turn_id
                untagged_current_task = (
                    not payload_turn_id
                    and active_task_turn == turn_id
                    and not task_boundary_ambiguous
                )
                if record.get("type") == "response_item" and item_type in STOP_TOOL_TYPES:
                    if not is_current_turn:
                        continue
                    if item_type.endswith("_output"):
                        outputs += 1
                    else:
                        calls += 1
                    arguments = payload.get("arguments", payload.get("input", {}))
                    if isinstance(arguments, dict):
                        for key in ("cmd", "command"):
                            if isinstance(arguments.get(key), str):
                                commands.append(arguments[key][:120])
                    elif isinstance(arguments, str) and arguments:
                        commands.append(arguments[:120])
                if record.get("type") == "event_msg" and item_type == "token_count":
                    if not (is_current_turn or untagged_current_task):
                        if not payload_turn_id:
                            saw_unattributed_token = True
                        continue
                    token_total = _event_token_total(record, payload)
                    if token_total is not None:
                        if is_current_turn:
                            tagged_max_tokens = max(tagged_max_tokens, token_total)
                        else:
                            task_max_tokens = max(task_max_tokens, token_total)
    except OSError as exc:
        return False, f"Stop transcript is unreadable: {type(exc).__name__}", []
    if active_task_turn:
        task_boundary_ambiguous = True
    max_tokens = tagged_max_tokens if task_boundary_ambiguous else max(tagged_max_tokens, task_max_tokens)
    if calls >= 3 or max_tokens >= STOP_TOKEN_THRESHOLD:
        return True, "", commands
    if not calls and not outputs:
        return False, "Stop transcript has no current-turn tool activity", commands
    if max_tokens == 0:
        if saw_unattributed_token:
            return False, "Stop transcript has an untagged token_count without unambiguous current-task boundaries", commands
        return False, "Stop transcript has no per-turn token usage; call-count evidence is below threshold", commands
    return False, "Stop transcript has fewer than three current-turn tool calls and token usage is below threshold", commands


def _stop_marker(data: dict[str, Any]) -> Path | None:
    session_id = data.get("session_id")
    turn_id = data.get("turn_id")
    if not isinstance(session_id, str) or not isinstance(turn_id, str) or not session_id or not turn_id:
        return None
    digest = hashlib.sha256(f"{session_id}\0{turn_id}".encode("utf-8")).hexdigest()
    return _state_path("stop-guard").parent / "stop-guard" / f"{digest}.done"


def _report_has(message: str, category: str) -> bool:
    lowered = message.lower()
    patterns = {
        "outcome": (
            r"\b(?:outcome|result|implemented|completed|done|success(?:fully)?|passed|failed|blocked)\b",
            r"结果|完成|实现|成功|失败|阻断|无变化|无需修改",
        ),
        "evidence/commands": (
            r"\b(?:evidence|validation|validated|tests?|tested|commands?|commanded|exit codes?|checks?)\b",
            r"证据|验证|已验证|测试|命令|退出码|检查|检验",
        ),
        "review disposition": (
            r"\b(?:review|reviewer|audit|audited)\b",
            r"审查|评审|复核|审核|未运行|不可用",
        ),
        "routing/WCU": (
            r"\b(?:routing|model|wcu|weighted cost|costs?|uncertain)\b",
            r"路由|模型|加权成本|成本|不确定",
        ),
        "remaining risks/blockers": (
            r"\b(?:risks?|blockers?|limitations?|known issues?)\b",
            r"风险|阻塞|阻碍|限制|已知问题",
        ),
        "Git/delivery state": (
            r"\b(?:git|commit|branch|delivery|deploy|external|not applicable|n/a)\b",
            r"提交|分支|交付|部署|外部|不适用|不相关",
        ),
    }
    english, chinese = patterns[category]
    if re.search(english, lowered) or re.search(chinese, lowered):
        return True
    if category == "review disposition":
        return bool(re.search(r"\b(?:review|reviewer|audit)\b.{0,24}\b(?:none|not run|unavailable)\b", lowered))
    if category == "remaining risks/blockers":
        return bool(re.search(r"\b(?:risk|risks|blocker|blockers|limitation|limitations)\b.{0,24}\bnone\b", lowered))
    return False


def _stop_missing_categories(data: dict[str, Any]) -> list[str]:
    final = data.get("last_assistant_message")
    if not isinstance(final, str) or not final.strip():
        final = ""
    missing: list[str] = []
    for category in (
        "outcome",
        "evidence/commands",
        "review disposition",
        "routing/WCU",
        "remaining risks/blockers",
    ):
        if not _report_has(final, category):
            missing.append(category)
    repo_relevant = _is_git_checkout(data.get("cwd"))
    if repo_relevant and not _report_has(final, "Git/delivery state"):
        missing.append("Git/delivery state")
    return missing


def _stop_guard(data: dict[str, Any]) -> dict[str, Any] | None:
    if data.get("stop_hook_active") is True:
        return None
    marker = _stop_marker(data)
    if marker is None:
        _record_error("Stop guard fail-open uncertainty: session_id or turn_id is missing")
        return None
    substantial, uncertainty, _commands = _stop_evidence(data)
    if uncertainty:
        _record_error(f"Stop guard fail-open uncertainty: {uncertainty}")
    if not substantial:
        return None
    missing = _stop_missing_categories(data)
    if not missing:
        return None
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        try:
            with marker.open("x", encoding="utf-8") as handle:
                handle.write("continued\n")
        except FileExistsError:
            return None
    except OSError as exc:
        _record_error(f"Stop guard marker failure: {type(exc).__name__}: {exc}")
        return None
    return {
        "decision": "block",
        "reason": "Complete final report; missing: " + ", ".join(missing) + ".",
        "continue": True,
    }


def handle(data: dict[str, Any]) -> dict[str, Any] | None:
    event_value = data.get("hook_event_name")
    if not isinstance(event_value, str) or not event_value:
        raise ValueError("hook_event_name is missing or not a string")
    event = event_value
    strict = _strict_enforcement()
    if event not in {"SessionStart", "SubagentStart", "PreToolUse", "PostToolUse", "Stop"}:
        raise ValueError(f"unsupported hook event: {event}")
    if event == "SessionStart":
        return _context(event, _session_context())

    if event == "SubagentStart":
        role = str(data.get("agent_type", "")).lower()
        message = ROLE_CONTEXT.get(role)
        return _context(event, message) if message else None

    if event == "Stop":
        return _stop_guard(data)

    if event == "PostToolUse":
        if not isinstance(data.get("tool_name"), str):
            _record_error("PostToolUse missing string tool_name")
            if not strict:
                return _posttool_context("Weighted router advisory: PostToolUse schema was incomplete; routing evidence is uncertain, but task execution is not blocked.")
            return _posttool_block("Weighted router: PostToolUse schema is uncertain; stop this package and refresh/start a new task/turn.")
        if not isinstance(data.get("tool_input"), (dict, str)) or "tool_response" not in data:
            _record_error("PostToolUse missing or malformed tool_input/tool_response")
            if not strict:
                return _posttool_context("Weighted router advisory: tool result schema was incomplete; record routing usage as uncertain and continue using task-level evidence.")
            return _posttool_block("Weighted router: PostToolUse result schema is uncertain; stop this package and refresh/start a new task/turn.")
        tool_name = data["tool_name"]
        tool_input = _tool_input(data)
        try:
            request = classify_spawn_request(tool_name, tool_input)
        except ValueError:
            request = None
        response = data["tool_response"]
        result = classify_spawn_result(response, luna_role=request.luna_role if request else None)
        if not strict:
            if request is not None and request.luna_role is not None and (result.unknown_luna or result.succeeded):
                session_id = str(data.get("session_id", ""))
                turn_id = _turn_id(data)
                if session_id and turn_id:
                    _record_luna_capability(
                        session_id,
                        turn_id,
                        unavailable=result.unknown_luna,
                        verified=result.succeeded,
                    )
            if result.unknown_luna:
                return _posttool_context(
                    "Weighted router advisory: Luna is unavailable for this call. Preserve the same outcome and acceptance evidence, then reroute to the lowest-cost available capable role, normally Terra; do not treat this as a scientific or project gate."
                )
            if result.thread_limit:
                return _posttool_context(
                    "Weighted router advisory: the child-thread limit was reached. Close completed children, reuse a matching open child, reduce decomposition, or continue in the parent when proportionate."
                )
            if request is not None and request.has_conflict:
                return _posttool_context("Weighted router advisory: " + _request_conflict_reason(request))
            if request is not None and (contract_error := package_contract_error(request)) is not None:
                return _posttool_context(
                    "Weighted router advisory: optional package metadata is inconsistent ("
                    + contract_error
                    + "). Do not use it as audit proof; task execution may continue against the outcome contract."
                )
            return None
        if request is not None and request.has_conflict:
            reason = _request_conflict_reason(request)
            _record_error(reason)
            return _posttool_block(reason)
        if request is not None and (contract_error := package_contract_error(request)) is not None:
            reason = f"Weighted router: invalid package contract in PostToolUse: {contract_error}."
            _record_error(reason)
            return _posttool_block(reason)
        if request is not None and not _settle_spawn_budget(data, request, succeeded=result.succeeded):
            return _posttool_block("Weighted router: package/risk reservation could not be settled; stop this package.")
        recovery_outcome = (
            _settle_thread_limit_recovery(data, tool_name, tool_input, request, result)
            if request is not None
            else "none"
        )
        if recovery_outcome == "error":
            return _posttool_block(
                "Weighted router: package thread-limit recovery state could not be reconciled; lock this package and stop spawning."
            )
        if request is not None and result.thread_limit:
            if recovery_outcome == "retry_failed":
                return _posttool_context(
                    f"Weighted router: package {request.package_id!r} used its one exact-signature retry and hit "
                    "agent-thread-limit again. The package is locked against further spawns; inspect/list and close agents, "
                    "then reuse an already-open matching Luna/Terra thread or stop. This is not Luna model unavailability."
                )
            return _posttool_context(
                "Weighted router: agent-thread-limit is a thread lifecycle/resource limit, not Luna model unavailability. "
                f"Package {request.package_id!r} is now in recovery. List agents; close completed/unneeded agents; retry "
                "the exact same normalized spawn signature at most once; changed role/model/message/phase is blocked. "
                "If still blocked, reuse an already-open matching Luna/Terra thread or stop."
            )
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
        if recovery_outcome == "retry_failed":
            return _posttool_context(
                f"Weighted router: package {request.package_id!r} used its one exact-signature retry and the spawn failed. "
                "The package is locked against further spawns; inspection, close, and matching open-thread reuse remain allowed."
            )
        return None

    if event != "PreToolUse":
        return None

    if not isinstance(data.get("model"), str) or not isinstance(data.get("tool_name"), str):
        _record_error("PreToolUse missing string model or tool_name")
        if not strict:
            return _context("PreToolUse", "Weighted router advisory: model/tool schema is incomplete; routing cost is uncertain, but the tool is not blocked.")
        return _deny("Weighted router: Hook input schema is uncertain (missing model/tool_name); tool use is blocked. Disable the router registration manually only for emergency recovery.")
    if not isinstance(data.get("tool_input"), (dict, str)):
        _record_error("PreToolUse has unsupported tool_input type")
        if not strict:
            return _context("PreToolUse", "Weighted router advisory: tool input schema is unknown; do not rely on the routing audit for this call.")
        return _deny("Weighted router: Hook input schema is uncertain (unsupported tool_input); tool use is blocked.")

    tool_name = data["tool_name"].lower()
    tool_leaf = normalize_tool_name(tool_name)
    tool_input = _tool_input(data)

    active_model = _active_model(data)
    if not any(family in active_model for family in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")):
        _record_error(f"PreToolUse has unsupported model: {active_model}")
        if not strict:
            return _context("PreToolUse", "Weighted router advisory: active model is outside the configured Sol/Terra/Luna families; cost attribution is uncertain.")
        return _deny("Weighted router: active model is outside the configured Sol/Terra/Luna families; routing cost and permissions are uncertain.")

    if not strict:
        advisories: list[str] = []
        request = None
        if tool_leaf in {"agent", "spawn_agent", "create_agent", "exec"}:
            try:
                request = classify_spawn_request(tool_name, tool_input)
            except ValueError as exc:
                advisories.append(f"nested agent syntax is not auditable ({exc})")
        if request is not None:
            if request.has_conflict:
                advisories.append(_request_conflict_reason(request))
            elif (contract_error := package_contract_error(request)) is not None:
                advisories.append(f"optional package metadata is inconsistent ({contract_error})")
            if _has_full_fork(tool_input):
                advisories.append("avoid a full parent-history fork; send the minimum task-local evidence")
            if request.role == "risk_reviewer":
                prompt = _prompt(tool_input)
                if "HIGH_RISK_TRIGGER:" not in prompt or "EVIDENCE_PACK:" not in prompt:
                    advisories.append("an expensive Sol risk review lacks a concrete trigger/evidence pack")
        if "gpt-5.6-sol" in active_model and is_sol_execution(tool_name, tool_input):
            advisories.append("this is direct Sol execution; prefer Luna/Terra for long mechanical work when delegation is available")
        if advisories:
            return _context("PreToolUse", "Weighted router advisory: " + "; ".join(advisories) + ". Preserve the outcome contract and record material WCU tradeoffs.")
        return None

    if tool_leaf in {"agent", "spawn_agent", "create_agent"}:
        request = classify_spawn_request(tool_name, tool_input)
        if request is None:
            return None
        role = request.role or ""
        model_override = request.model
        if request.has_conflict:
            return _deny(_request_conflict_reason(request))
        if (contract_error := package_contract_error(request)) is not None:
            return _deny(f"Weighted router: invalid package contract: {contract_error}.")
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
        retry_denial = _thread_limit_retry_gate(data, tool_name, tool_input, request)
        if retry_denial:
            return _deny(retry_denial)
        reservation_denial = _reserve_spawn_budget(data, request)
        if reservation_denial:
            return _deny(reservation_denial)
        commit_denial = _commit_thread_limit_preflight(data, tool_name, tool_input, request)
        if commit_denial:
            _release_reservations(str(data.get("session_id", "")), _reservation_specs(request))
            return _deny(commit_denial)
        return None

    if tool_leaf == "exec":
        raw = command_text(tool_input)
        try:
            analysis = analyze_functions_exec(raw)
        except ValueError as exc:
            return _deny(f"Weighted router: nested agent factory syntax is not policy-verifiable: {exc}.")
        request = classify_spawn_request(tool_name, tool_input)
        if request is not None and request.has_conflict:
            return _deny(_request_conflict_reason(request))
        if request is not None and (contract_error := package_contract_error(request)) is not None:
            return _deny(f"Weighted router: invalid package contract: {contract_error}.")
        capability_denial = _luna_gate(data, request)
        if capability_denial:
            return _deny(capability_denial)
        if request is not None:
            retry_denial = _thread_limit_retry_gate(data, tool_name, tool_input, request)
            if retry_denial:
                return _deny(retry_denial)
            reservation_denial = _reserve_spawn_budget(data, request)
            if reservation_denial:
                return _deny(reservation_denial)
            commit_denial = _commit_thread_limit_preflight(data, tool_name, tool_input, request)
            if commit_denial:
                _release_reservations(str(data.get("session_id", "")), _reservation_specs(request))
                return _deny(commit_denial)
            return None
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
