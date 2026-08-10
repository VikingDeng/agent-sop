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
from weighted_routing_policy import (  # noqa: E402
    GLOBAL_LOOP_BUDGET,
    MAX_CONCURRENT_OPEN_THREADS,
    ROLE_MODEL_FAMILIES,
    SPAWN_IDENTIFIERS,
    analyze_functions_exec,
    classify_spawn_request,
    classify_spawn_result,
    close_result_succeeded,
    command_text,
    is_sol_execution,
    normalize_tool_name,
    parse_package_markers,
    package_contract_error,
    parse_recontract_evidence,
    post_failure_role_allowed,
    spawn_request_signature,
)


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


def _delivery_report_findings(message: str, *, repo_relevant: bool) -> list[str]:
    lowered = message.lower()
    findings: list[str] = []
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
    for category, (english, chinese) in patterns.items():
        if category == "Git/delivery state" and not repo_relevant:
            continue
        if re.search(english, lowered) or re.search(chinese, lowered):
            continue
        if category == "review disposition" and re.search(
            r"\b(?:review|reviewer|audit)\b.{0,24}\b(?:none|not run|unavailable)\b", lowered
        ):
            continue
        if category == "remaining risks/blockers" and re.search(
            r"\b(?:risk|risks|blocker|blockers|limitation|limitations)\b.{0,24}\bnone\b", lowered
        ):
            continue
        findings.append(category)
    return findings


def _identifier_values(value: Any) -> dict[str, str]:
    payload = value if isinstance(value, dict) else _spawn_result_object(value)
    if not isinstance(payload, dict):
        return {}
    return {
        key: str(payload[key]).strip()
        for key in SPAWN_IDENTIFIERS
        if isinstance(payload.get(key), str) and payload[key].strip()
    }


def _close_target(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    target = value.get("target")
    return target.strip() if isinstance(target, str) else ""


# Codex App collaboration payloads keep task messages encrypted in the rollout
# (currently Fernet tokens begin with ``gAAAA``).  An encrypted message is not
# evidence that markers are absent; it is evidence that this auditor cannot
# inspect them.  Keep that distinction separate from legacy plain-text logs.
def _is_opaque_app_message(arguments: dict[str, Any]) -> bool:
    for key in ("message", "prompt", "task"):
        value = arguments.get(key)
        if isinstance(value, str) and value.startswith("gAAAA"):
            return True
    return False


def _lifecycle_target(arguments: dict[str, Any]) -> str:
    for key in ("target", "agent", "agent_name", "task_name"):
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _lifecycle_result_succeeded(value: Any) -> bool:
    payload = _spawn_result_object(value)
    if payload is None:
        if value in (None, ""):
            return True
        return not bool(re.search(r"\b(?:failed|failure|error|timed out|interrupted)\b", str(value), re.I))
    if payload.get("isError") or payload.get("is_error") or payload.get("failed"):
        return False
    if payload.get("error") not in (None, False, ""):
        return False
    status = payload.get("status")
    return not (isinstance(status, str) and status.lower() in {"failed", "failure", "error"})


def _is_agent_inspection(tool_name: str, arguments: dict[str, Any]) -> bool:
    leaf = normalize_tool_name(tool_name)
    if leaf in {"list_agents", "get_agents", "agent_status", "read_thread_terminal"}:
        return True
    action = arguments.get("action") or arguments.get("operation") or arguments.get("mode")
    return leaf == "agent" and isinstance(action, str) and action.lower() in {"list", "inspect", "status"}


def _spawn_result_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _turn_id(payload: dict[str, Any]) -> str:
    value = payload.get("turn_id")
    if isinstance(value, str) and value:
        return value
    # Historical session JSONL stores the turn ID here; the live Hook reads
    # only its documented top-level field and does not use this parser.
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    if not isinstance(metadata, dict):
        return ""
    value = metadata.get("turn_id")
    return value if isinstance(value, str) and value else ""


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


def audit_log(meta: SessionMeta, large_output_chars: int = 20_000) -> dict[str, Any]:
    active_model = "unknown"
    previous_usage = {field: 0 for field in TOKEN_FIELDS}
    usage_by_model: dict[str, Counter[str]] = defaultdict(Counter)
    calls_by_model: dict[str, Counter[str]] = defaultdict(Counter)
    call_index: dict[str, tuple[str, str]] = {}
    pending_spawns: dict[str, tuple[Any, str, str]] = {}
    pending_closes: dict[str, tuple[str, int]] = {}
    pending_lifecycle_controls: dict[str, dict[str, Any]] = {}
    activity_by_path: dict[str, dict[str, Any]] = {}
    lifecycle_events: list[dict[str, Any]] = []
    thread_limit_failures: list[dict[str, str]] = []
    successful_spawns: Counter[str] = Counter()
    successful_spawn_roles: list[str] = []
    failed_spawns: Counter[str] = Counter()
    large_outputs: list[dict[str, Any]] = []
    sol_execution_calls: list[dict[str, str]] = []
    sol_lifecycle_calls: list[dict[str, str]] = []
    parse_errors = 0
    usage_schema_errors: list[str] = []
    token_snapshot_count = 0
    task_complete = False
    task_complete_count = 0
    task_epoch = 0
    final_epoch_task_complete_count = 0
    interrupted = False
    last_token_line = 0
    last_substantive_line = 0
    nested_policy_violations: list[str] = []
    nested_policy_uncertainties: list[str] = []
    package_contract_uncertainties: list[str] = []
    luna_routing_violations: list[str] = []
    luna_unavailable_turns: set[str] = set()
    last_agent_message = ""
    cwd = ""

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
            "successful_spawn_roles": [],
            "failed_spawns": {},
            "unresolved_spawn_calls": 0,
            "unresolved_close_calls": [],
            "lifecycle_events": [],
            "thread_limit_failures": [],
            "large_outputs": [],
            "sol_execution_calls": [],
            "sol_lifecycle_calls": [],
            "interrupted": False,
            "task_complete_count": 0,
            "task_epoch": 0,
            "final_epoch_task_complete_count": 0,
            "completion_status": "missing_completion",
            "parse_errors": 1,
            "usage_schema_errors": [f"cannot open log: {exc}"],
            "token_snapshot_count": 0,
            "task_complete": False,
            "last_agent_message": "",
            "cwd": "",
            "nested_policy_violations": [],
            "nested_policy_uncertainties": [],
            "package_contract_uncertainties": [],
            "luna_routing_violations": [],
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
            metadata_record = (
                record.get("type") in {"session_meta", "turn_context"}
                or payload.get("type") in {"task_started", "task_complete"}
            )
            if metadata_record and isinstance(payload.get("cwd"), str):
                cwd = payload["cwd"]
            observed_turn_id = _turn_id(payload)
            is_task_started = record.get("type") == "event_msg" and payload.get("type") == "task_started"
            is_task_complete = record.get("type") == "event_msg" and payload.get("type") == "task_complete"
            substantive_after_completion = (
                record.get("type") in {"turn_context", "response_item"}
                or (record.get("type") == "event_msg" and payload.get("type") in {"task_started", "token_count", "user_message"})
            )
            if is_task_started:
                task_epoch += 1
                task_complete = False
                final_epoch_task_complete_count = 0
                interrupted = False
                last_agent_message = ""
                lifecycle_events.append({"kind": "task_started", "line": line_number, "epoch": task_epoch})
            elif task_complete and substantive_after_completion:
                task_complete = False
                final_epoch_task_complete_count = 0
                last_agent_message = ""
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
                task_complete_count += 1
                final_epoch_task_complete_count += 1
                if isinstance(payload.get("last_agent_message"), str):
                    last_agent_message = payload["last_agent_message"]
                lifecycle_events.append({"kind": "task_complete", "line": line_number})
            if record.get("type") == "event_msg" and payload.get("type") == "turn_aborted":
                interrupted = True
                task_complete = False
                final_epoch_task_complete_count = 0
                last_agent_message = ""
                lifecycle_events.append({"kind": "turn_aborted", "line": line_number})
            if record.get("type") == "event_msg" and payload.get("type") == "sub_agent_activity":
                activity_kind = str(payload.get("kind") or "unknown")
                activity = {
                    "kind": "child_activity",
                    "status": activity_kind,
                    "agent_thread_id": str(payload.get("agent_thread_id") or ""),
                    "agent_path": str(payload.get("agent_path") or ""),
                    "line": line_number,
                }
                lifecycle_events.append(activity)
                if activity["agent_path"]:
                    activity_by_path[activity["agent_path"]] = activity
                    for event in lifecycle_events:
                        if event.get("kind") != "spawn_result":
                            continue
                        identifiers = event.get("identifiers", {})
                        if identifiers.get("task_name") == activity["agent_path"]:
                            if activity["agent_thread_id"]:
                                identifiers.setdefault("thread_id", activity["agent_thread_id"])
                            identifiers.setdefault("agent_path", activity["agent_path"])
                continue
            if record.get("type") == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info")
                usage_payload = info.get("total_token_usage") if isinstance(info, dict) else None
                current, errors = _normalize_usage(usage_payload, line_number)
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
                leaf = normalize_tool_name(name)
                lifecycle_control = leaf in {
                    "agent", "spawn_agent", "create_agent", "send_message", "send_input",
                    "followup_task", "wait_agent", "close_agent", "resume_agent", "interrupt_agent",
                }
                if _is_agent_inspection(name, arguments):
                    lifecycle_events.append({"kind": "agent_inspection", "line": line_number})
                if lifecycle_control and leaf not in {"spawn_agent", "create_agent", "close_agent"}:
                    control_event = {
                        "kind": "lifecycle_request",
                        "tool": name,
                        "leaf": leaf,
                        "target": _lifecycle_target(arguments),
                        "call_id": call_id,
                        "line": line_number,
                    }
                    if leaf == "followup_task":
                        message = arguments.get("message") or arguments.get("prompt") or arguments.get("task")
                        package_id, package_phase, package_error = parse_package_markers(message)
                        control_event.update({
                            "kind": "followup_request",
                            "package_id": package_id,
                            "package_phase": package_phase,
                            "package_error": package_error,
                            "package_markers_opaque": _is_opaque_app_message(arguments),
                        })
                    lifecycle_events.append(control_event)
                    if call_id:
                        pending_lifecycle_controls[call_id] = control_event
                try:
                    request = classify_spawn_request(name, arguments)
                except ValueError:
                    request = None
                lifecycle_call = leaf in {"agent", "spawn_agent", "create_agent"} or request is not None
                if lifecycle_call and not observed_turn_id:
                    luna_routing_violations.append(
                        f"line {line_number}: lifecycle call {name!r} lacks the documented top-level turn_id; enforcement is fail-closed"
                    )
                if request is not None:
                    role = request.requested_role
                    signature = spawn_request_signature(name, arguments)
                    recontract, recontract_error = parse_recontract_evidence(
                        request.message,
                        new_package_id=request.package_id,
                    )
                    lifecycle_events.append({
                        "kind": "spawn_request",
                        "role": role,
                        "call_id": call_id,
                        "line": line_number,
                        "package_id": request.package_id,
                        "package_phase": request.package_phase,
                        "package_markers_opaque": bool(
                            request.package_error and _is_opaque_app_message(arguments)
                        ),
                        "signature": signature,
                        "recontract": (
                            {
                                "old_package_id": recontract.old_package_id,
                                "new_package_id": recontract.new_package_id,
                                "old_contract_sha256": recontract.old_contract_sha256,
                                "new_contract_sha256": recontract.new_contract_sha256,
                                "reason": recontract.reason,
                                "scope_acceptance_delta": recontract.scope_acceptance_delta,
                            }
                            if recontract is not None
                            else None
                        ),
                        "recontract_error": recontract_error,
                    })
                    if recontract_error:
                        luna_routing_violations.append(
                            f"line {line_number}: invalid re-contract evidence: {recontract_error}"
                        )
                    contract_error = package_contract_error(request)
                    package_markers_opaque = bool(
                        request.package_error and _is_opaque_app_message(arguments)
                    )
                    if package_markers_opaque:
                        package_contract_uncertainties.append(
                            f"line {line_number}: opaque/encrypted App spawn message leaves PACKAGE_ID/PACKAGE_PHASE contract uncertain"
                        )
                    elif contract_error is not None:
                        luna_routing_violations.append(
                            f"line {line_number}: invalid package contract: {contract_error}"
                        )
                    if request.identity_alias_conflict:
                        luna_routing_violations.append(
                            f"line {line_number}: spawn identity aliases disagree {request.identity_values!r}; routing is uncertain"
                        )
                    elif request.model_alias_conflict:
                        luna_routing_violations.append(
                            f"line {line_number}: spawn model aliases disagree {request.model_values!r}; routing is uncertain"
                        )
                    elif request.role_model_conflict:
                        luna_routing_violations.append(
                            f"line {line_number}: known role {role!r} conflicts with explicit model {request.model!r}; routing is uncertain"
                        )
                    if request.has_conflict:
                        failed_spawns[role] += 1
                    elif call_id and observed_turn_id:
                        pending_spawns[call_id] = (request, observed_turn_id, signature)
                    elif not observed_turn_id:
                        failed_spawns[role] += 1
                    else:
                        failed_spawns[role] += 1
                    if observed_turn_id in luna_unavailable_turns and not post_failure_role_allowed(request):
                        luna_routing_violations.append(
                            f"line {line_number}: {role!r} retry/escalation followed an unavailable gpt-5.6-luna result in turn {observed_turn_id}"
                        )
                if normalize_tool_name(name) == "exec":
                    raw = command_text(arguments)
                    try:
                        analysis = analyze_functions_exec(raw)
                    except ValueError as exc:
                        nested_policy_violations.append(f"line {line_number}: {exc}")
                    else:
                        if analysis.dynamic_tool_access:
                            nested_policy_uncertainties.append(
                                f"line {line_number}: dynamic tools access has no authoritative captured inner evidence"
                            )
                if leaf == "close_agent":
                    target = _close_target(arguments)
                    lifecycle_events.append({
                        "kind": "close_request",
                        "target": target,
                        "call_id": call_id,
                        "line": line_number,
                    })
                    if call_id:
                        pending_closes[call_id] = (target, line_number)
                if model_family(active_model) == "sol" and lifecycle_control:
                    sol_lifecycle_calls.append({"tool": name, "line": str(line_number)})
                if model_family(active_model) == "sol" and not lifecycle_control and is_sol_execution(name, arguments):
                    sol_execution_calls.append({"tool": name, "line": str(line_number)})
                    if observed_turn_id in luna_unavailable_turns:
                        luna_routing_violations.append(
                            f"line {line_number}: direct Sol execution followed an unavailable gpt-5.6-luna result in turn {observed_turn_id}"
                        )
                continue

            if item_type in {"function_call_output", "custom_tool_call_output"}:
                call_id = str(payload.get("call_id") or "")
                model, name = call_index.get(call_id, (active_model, "unknown"))
                size = _output_size(payload)
                if size >= large_output_chars:
                    large_outputs.append({"model": model, "tool": name, "chars": size, "line": line_number})
                spawn = pending_spawns.pop(call_id, None)
                close = pending_closes.pop(call_id, None)
                if close is not None:
                    target, request_line = close
                    lifecycle_events.append({
                        "kind": "close_result",
                        "target": target,
                        "request_line": request_line,
                        "line": line_number,
                        "succeeded": close_result_succeeded(payload.get("output")),
                    })
                control = pending_lifecycle_controls.pop(call_id, None)
                if control is not None:
                    control["succeeded"] = _lifecycle_result_succeeded(payload.get("output"))
                    control["result_line"] = line_number
                    if control.get("leaf") == "interrupt_agent":
                        lifecycle_events.append({
                            "kind": "interrupt_result",
                            "target": control.get("target", ""),
                            "line": line_number,
                            "succeeded": control["succeeded"],
                        })
                if spawn is not None:
                    request, spawn_turn_id, signature = spawn
                    role = request.requested_role
                    classification = classify_spawn_result(
                        payload.get("output"),
                        luna_role=request.luna_role,
                    )
                    if classification.succeeded:
                        identifiers = _identifier_values(payload.get("output"))
                        result_object = _spawn_result_object(payload.get("output")) or {}
                        reported_roles = [
                            result_object.get(key)
                            for key in ("agent_type", "subagent_type", "role")
                            if isinstance(result_object.get(key), str) and result_object[key].strip()
                        ]
                        reported_models = [
                            result_object.get(key)
                            for key in ("model", "model_name")
                            if isinstance(result_object.get(key), str) and result_object[key].strip()
                        ]
                        task_name = identifiers.get("task_name")
                        activity = activity_by_path.get(task_name or "")
                        if activity is not None:
                            if activity.get("agent_thread_id"):
                                identifiers.setdefault("thread_id", activity["agent_thread_id"])
                            if activity.get("agent_path"):
                                identifiers.setdefault("agent_path", activity["agent_path"])
                        successful_spawns[role] += 1
                        successful_spawn_roles.append(role)
                        lifecycle_events.append({
                            "kind": "spawn_result",
                            "role": role,
                            "call_id": call_id,
                            "identifiers": identifiers,
                            "requested_model": request.model,
                            "reported_role": reported_roles[0] if reported_roles else None,
                            "reported_model": reported_models[0] if reported_models else None,
                            "line": line_number,
                            "package_id": request.package_id,
                            "package_phase": request.package_phase,
                            "signature": signature,
                        })
                    else:
                        failed_spawns[role] += 1
                        lifecycle_events.append({
                            "kind": "spawn_failure",
                            "role": role,
                            "line": line_number,
                            "package_id": request.package_id,
                            "package_phase": request.package_phase,
                            "signature": signature,
                        })
                        if classification.thread_limit:
                            failure = {
                                "role": role,
                                "line": str(line_number),
                                "signature": signature,
                                "package_id": str(request.package_id),
                            }
                            thread_limit_failures.append(failure)
                            lifecycle_events.append({
                                "kind": "thread_limit",
                                "role": role,
                                "line": line_number,
                                "signature": signature,
                                "package_id": request.package_id,
                                "package_phase": request.package_phase,
                            })
                        if classification.unknown_luna:
                            if spawn_turn_id:
                                luna_unavailable_turns.add(spawn_turn_id)
                            else:
                                luna_routing_violations.append(
                                    f"line {line_number}: unavailable gpt-5.6-luna result lacks turn_id; routing is uncertain"
                                )
    return {
        "thread_id": meta.thread_id,
        "session_id": meta.session_id,
        "parent_thread_id": meta.parent_thread_id,
        "agent_role": meta.agent_role,
        "path": str(meta.path),
        "usage_by_model": {model: dict(counter) for model, counter in usage_by_model.items()},
        "calls_by_model": {model: dict(counter) for model, counter in calls_by_model.items()},
        "successful_spawns": dict(successful_spawns),
        "successful_spawn_roles": successful_spawn_roles,
        "failed_spawns": dict(failed_spawns),
        "unresolved_spawn_calls": len(pending_spawns),
        "unresolved_close_calls": [
            {"call_id": call_id, "target": target, "line": line}
            for call_id, (target, line) in pending_closes.items()
        ],
        "lifecycle_events": lifecycle_events,
        "thread_limit_failures": thread_limit_failures,
        "large_outputs": large_outputs,
        "sol_execution_calls": sol_execution_calls,
        "sol_lifecycle_calls": sol_lifecycle_calls,
        "parse_errors": parse_errors,
        "usage_schema_errors": usage_schema_errors,
        "token_snapshot_count": token_snapshot_count,
        "task_complete": task_complete,
        "task_complete_count": task_complete_count,
        "task_epoch": task_epoch,
        "final_epoch_task_complete_count": final_epoch_task_complete_count,
        "interrupted": interrupted,
        "completion_status": (
            "interrupted" if interrupted else ("confirmed" if task_complete else "missing_completion")
        ),
        "last_agent_message": last_agent_message,
        "cwd": cwd,
        "last_token_line": last_token_line,
        "last_substantive_line": last_substantive_line,
        "nested_policy_violations": nested_policy_violations,
        "nested_policy_uncertainties": nested_policy_uncertainties,
        "package_contract_uncertainties": package_contract_uncertainties,
        "luna_routing_violations": luna_routing_violations,
    }


def audit_session_tree(
    target: str,
    sessions_root: Path,
    large_output_chars: int = 20_000,
    *,
    enforcement_mode: str = "strict",
) -> dict[str, Any]:
    if enforcement_mode not in {"advisory", "strict"}:
        raise ValueError("enforcement_mode must be advisory or strict")
    metas = discover_session_tree(target, sessions_root)
    sessions = [audit_log(meta, large_output_chars=large_output_chars) for meta in metas]
    model_totals: dict[str, Counter[str]] = defaultdict(Counter)
    family_totals: dict[str, Counter[str]] = defaultdict(Counter)
    roles: Counter[str] = Counter()
    children_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for session in sessions:
        parent = session["parent_thread_id"]
        if parent:
            children_by_parent[str(parent)].append(session)
    large_outputs: list[dict[str, Any]] = []
    sol_execution_calls: list[dict[str, Any]] = []
    sol_lifecycle_calls: list[dict[str, Any]] = []
    completeness_violations: list[str] = []
    routing_policy_findings: list[str] = []
    delivery_report_findings: list[str] = []
    child_lifecycle_statuses: list[dict[str, Any]] = []

    def lifecycle_violations(session: dict[str, Any], children: list[dict[str, Any]]) -> list[str]:
        events = session.get("lifecycle_events", [])
        successful_closes = [
            event for event in events
            if event.get("kind") == "close_result" and event.get("succeeded") and event.get("target")
        ]
        close_ids = {str(event["target"]) for event in successful_closes}
        violations: list[str] = []
        open_ids: set[str] = set()
        peak_open = 0
        for event in events:
            if event.get("kind") == "spawn_result":
                identifiers = event.get("identifiers", {})
                child_id = identifiers.get("thread_id") or identifiers.get("agent_id")
                if child_id:
                    open_ids.add(child_id)
                    peak_open = max(peak_open, len(open_ids))
                else:
                    violations.append(
                        f"thread {session['thread_id']}: successful spawn at line {event.get('line')} lacks a recognized child identifier; lifecycle closure is [UNCERTAIN/PARTIAL]"
                    )
            elif event.get("kind") == "close_result" and event.get("succeeded"):
                open_ids.discard(str(event.get("target", "")))
        if peak_open > MAX_CONCURRENT_OPEN_THREADS:
            violations.append(
                f"thread {session['thread_id']}: peak concurrently open spawned threads was {peak_open}, above max_concurrent_threads_per_session={MAX_CONCURRENT_OPEN_THREADS}"
            )
        child_by_id = {str(child["thread_id"]): child for child in children}
        for event in events:
            if event.get("kind") != "spawn_result":
                continue
            identifiers = event.get("identifiers", {})
            child_id = identifiers.get("thread_id") or identifiers.get("agent_id")
            child = child_by_id.get(str(child_id)) if child_id else None
            if child is None:
                continue
            event["child_thread_id"] = str(child["thread_id"])
            event["child_role"] = child.get("agent_role")
            event["child_models"] = sorted(
                model for model, usage in child.get("usage_by_model", {}).items()
                if usage.get("total_tokens", 0)
            )
        for child in children:
            child_id = str(child["thread_id"])
            interrupted_child = bool(child.get("interrupted"))
            if interrupted_child:
                status = "interrupted"
            elif child.get("task_complete"):
                status = "completed"
            else:
                status = "missing_completion"
            confirmed_close = child_id in close_ids
            child_lifecycle_statuses.append({
                "parent_thread_id": session["thread_id"],
                "child_thread_id": child_id,
                "role": child.get("agent_role"),
                "models": sorted(child.get("usage_by_model", {})),
                "status": status,
                "close_status": "confirmed" if confirmed_close else "unclosed",
            })
            if not confirmed_close:
                state = "interrupted" if interrupted_child else ("completed" if child.get("task_complete") else "missing completion")
                violations.append(
                    f"thread {session['thread_id']}: {state} child {child_id} has no confirmed successful close_agent result; close requests alone are not proof"
                )

        package_recovery: dict[str, dict[str, Any]] = {}
        for event in events:
            kind = event.get("kind")
            package_id = event.get("package_id")
            if not package_id:
                continue
            package_id = str(package_id)
            signature = event.get("signature")
            package_state = package_recovery.get(package_id)
            if kind == "spawn_request":
                active_others = {
                    old_package: state
                    for old_package, state in package_recovery.items()
                    if old_package != package_id and state.get("status") in {"recovery", "locked"}
                }
                if package_state is None and active_others:
                    recontract = event.get("recontract")
                    old_package = recontract.get("old_package_id") if isinstance(recontract, dict) else None
                    if event.get("recontract_error") or old_package not in active_others:
                        violations.append(
                            f"thread {session['thread_id']}: line {event.get('line')} silently relabeled work to package {package_id!r} after thread-limit without valid re-contract evidence"
                        )
                    else:
                        active_others[str(old_package)]["status"] = "recontracted"
                        active_others[str(old_package)]["recontracted_to"] = package_id
                package_state = package_recovery.get(package_id)
                if package_state is None:
                    continue
                if package_state.get("status") == "recovery":
                    package_state["retry_requests"] = int(package_state.get("retry_requests", 0)) + 1
                    if signature != package_state.get("signature"):
                        violations.append(
                            f"thread {session['thread_id']}: package {package_id!r} changed normalized spawn signature during thread-limit recovery at line {event.get('line')}"
                        )
                        package_state["status"] = "locked"
                    elif int(package_state["retry_requests"]) > 1:
                        violations.append(
                            f"thread {session['thread_id']}: package {package_id!r} exceeded one same-signature retry after thread-limit"
                        )
                        package_state["status"] = "locked"
                elif package_state.get("status") in {"locked", "recontracted"}:
                    violations.append(
                        f"thread {session['thread_id']}: package {package_id!r} spawned at line {event.get('line')} after recovery was locked"
                    )
            elif kind == "spawn_result" and package_state is not None:
                if (
                    package_state.get("status") == "recovery"
                    and signature == package_state.get("signature")
                    and int(package_state.get("retry_requests", 0)) == 1
                ):
                    package_state["status"] = "recovered"
            elif kind == "spawn_failure" and package_state is not None:
                if (
                    package_state.get("status") == "recovery"
                    and signature == package_state.get("signature")
                    and int(package_state.get("retry_requests", 0)) == 1
                ):
                    package_state["status"] = "locked"
            elif kind == "thread_limit":
                if package_state is None:
                    package_recovery[package_id] = {
                        "status": "recovery",
                        "signature": signature,
                        "retry_requests": 0,
                    }
                elif package_state.get("status") == "recovered":
                    package_state["status"] = "locked"

        completed_ids = {str(child["thread_id"]) for child in children if child.get("task_complete")}
        for failure in (event for event in events if event.get("kind") == "thread_limit"):
            failure_line = int(failure["line"])
            package_id = failure.get("package_id")
            later = [event for event in events if int(event.get("line", 0)) > failure_line]
            inspections = [event for event in later if event.get("kind") == "agent_inspection"]
            package_attempts = [
                event for event in later
                if event.get("kind") == "spawn_request" and event.get("package_id") == package_id
            ]
            first_retry_line = min((int(event["line"]) for event in package_attempts), default=sys.maxsize)
            if not inspections or int(inspections[0]["line"]) >= first_retry_line:
                violations.append(
                    f"thread {session['thread_id']}: agent-thread-limit at line {failure_line} lacks agent listing/inspection before retry or stop"
                )
                continue
            inspection_line = int(inspections[0]["line"])
            open_at_failure: set[str] = set()
            for event in events:
                if int(event.get("line", 0)) >= failure_line:
                    break
                if event.get("kind") == "spawn_result":
                    identifiers = event.get("identifiers", {})
                    child_id = identifiers.get("thread_id") or identifiers.get("agent_id")
                    if child_id:
                        open_at_failure.add(str(child_id))
                elif event.get("kind") == "close_result" and event.get("succeeded"):
                    open_at_failure.discard(str(event.get("target", "")))
            completed_open = completed_ids & open_at_failure
            if completed_open:
                recovery_closes = [
                    event for event in successful_closes
                    if inspection_line < int(event["line"]) < first_retry_line
                    and str(event["target"]) in completed_open
                ]
                if not recovery_closes:
                    violations.append(
                        f"thread {session['thread_id']}: agent-thread-limit at line {failure_line} had completed open children but no confirmed successful close after inspection and before retry/stop"
                    )
        followups_by_target: Counter[str] = Counter(
            str(event.get("target"))
            for event in events
            if event.get("kind") == "followup_request"
            and event.get("succeeded", True)
            and event.get("target")
        )
        for target, count in sorted(followups_by_target.items()):
            if count > GLOBAL_LOOP_BUDGET["correction"]:
                violations.append(
                    f"thread {session['thread_id']}: target {target!r} has {count} correction/followup_task attempts; maximum is {GLOBAL_LOOP_BUDGET['correction']}"
                )
        return violations

    successful_phase_counts: Counter[tuple[str, str, str]] = Counter()
    successful_risk_counts: Counter[str] = Counter()
    for session in sessions:
        root_session = str(session["session_id"])
        for event in session.get("lifecycle_events", []):
            if event.get("kind") not in {"spawn_result", "followup_request"}:
                continue
            package_id = event.get("package_id")
            phase = event.get("package_phase")
            if package_id and phase in GLOBAL_LOOP_BUDGET and event.get("kind") == "spawn_result":
                successful_phase_counts[(root_session, str(package_id), str(phase))] += 1
            if package_id and phase in GLOBAL_LOOP_BUDGET and event.get("kind") == "followup_request" and event.get("succeeded", True):
                successful_phase_counts[(root_session, str(package_id), str(phase))] += 1
            if event.get("role") == "risk_reviewer":
                successful_risk_counts[root_session] += 1
    for (root_session, package_id, phase), count in sorted(successful_phase_counts.items()):
        if count > GLOBAL_LOOP_BUDGET[phase]:
            routing_policy_findings.append(
                f"session {root_session}: package {package_id!r} has {count} successful {phase} spawns; maximum is {GLOBAL_LOOP_BUDGET[phase]}"
            )
    for root_session, count in sorted(successful_risk_counts.items()):
        if count > 1:
            routing_policy_findings.append(
                f"session {root_session}: {count} successful risk_reviewer spawns; maximum is one"
            )

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
        for call in session["sol_lifecycle_calls"]:
            sol_lifecycle_calls.append({"thread_id": thread_id, **call})

        requested_roles = Counter(session["successful_spawn_roles"])
        expected_children = sum(requested_roles.values())
        children = children_by_parent[thread_id]
        routing_policy_findings.extend(lifecycle_violations(session, children))
        discovered_children = len(children)
        if expected_children > discovered_children:
            completeness_violations.append(
                f"thread {thread_id}: {expected_children} successful spawn(s) but only {discovered_children} child log(s)"
            )
        elif discovered_children > expected_children:
            completeness_violations.append(
                f"thread {thread_id}: {discovered_children - expected_children} extra child log(s) without a successful parent spawn"
            )
        for role, count in sorted(requested_roles.items()):
            if role not in ROLE_MODEL_FAMILIES:
                completeness_violations.append(
                    f"thread {thread_id}: {count} successful spawn(s) requested noncanonical role {role!r}"
                )
        discovered_roles = Counter(
            str(child["agent_role"]) for child in children if child["agent_role"]
        )
        missing_roles = requested_roles - discovered_roles
        extra_roles = discovered_roles - requested_roles
        if missing_roles:
            detail = ", ".join(f"{role}={count}" for role, count in sorted(missing_roles.items()))
            completeness_violations.append(f"thread {thread_id}: missing requested child role(s): {detail}")
        if extra_roles:
            detail = ", ".join(f"{role}={count}" for role, count in sorted(extra_roles.items()))
            completeness_violations.append(f"thread {thread_id}: extra discovered child role(s): {detail}")
        if requested_roles != discovered_roles:
            requested = ", ".join(f"{role}={count}" for role, count in sorted(requested_roles.items())) or "none"
            discovered = ", ".join(f"{role}={count}" for role, count in sorted(discovered_roles.items())) or "none"
            completeness_violations.append(
                f"thread {thread_id}: role mismatch: requested {requested}; discovered {discovered}"
            )
        if session["unresolved_spawn_calls"]:
            completeness_violations.append(
                f"thread {thread_id}: {session['unresolved_spawn_calls']} spawn call(s) have no output"
            )
        if session["unresolved_close_calls"]:
            completeness_violations.append(
                f"thread {thread_id}: {len(session['unresolved_close_calls'])} close_agent call(s) have no output and are not closure proof"
            )
        if session["parse_errors"]:
            completeness_violations.append(f"thread {thread_id}: {session['parse_errors']} corrupt JSON line(s)")
        if session["usage_schema_errors"]:
            completeness_violations.append(
                f"thread {thread_id}: {len(session['usage_schema_errors'])} token/schema error(s)"
            )
        for item in session["nested_policy_violations"]:
            routing_policy_findings.append(f"thread {thread_id}: {item}")
        for item in session["nested_policy_uncertainties"]:
            completeness_violations.append(f"thread {thread_id}: {item}")
        for item in session["package_contract_uncertainties"]:
            completeness_violations.append(f"thread {thread_id}: {item}")
        for item in session["luna_routing_violations"]:
            routing_policy_findings.append(f"thread {thread_id}: {item}")
        if not session["token_snapshot_count"]:
            completeness_violations.append(f"thread {thread_id}: no valid token snapshot")
        if not session["task_complete"] and session.get("interrupted"):
            completeness_violations.append(
                f"thread {thread_id}: final task epoch interrupted before task_complete"
            )
        elif not session["task_complete"]:
            completeness_violations.append(f"thread {thread_id}: task_complete event missing")
        elif session["last_token_line"] < session["last_substantive_line"] and not session.get("interrupted"):
            completeness_violations.append(f"thread {thread_id}: final token snapshot precedes later activity")

        if session["task_complete"] and not session["parent_thread_id"]:
            repo_relevant = _is_git_checkout(session.get("cwd"))
            missing = _delivery_report_findings(
                session["last_agent_message"],
                repo_relevant=repo_relevant,
            )
            if missing:
                finding = f"thread {thread_id}: completed root final report missing " + ", ".join(missing)
                delivery_report_findings.append(finding)

        for child in children:
            child_id = str(child["thread_id"])
            role = child["agent_role"]
            if not role:
                completeness_violations.append(f"thread {thread_id}: child {child_id} has no declared agent_role")
                continue
            expected_family = ROLE_MODEL_FAMILIES.get(str(role))
            if expected_family is None:
                completeness_violations.append(
                    f"thread {thread_id}: child {child_id} has unknown agent_role {role!r}"
                )
                continue
            for model, usage in child["usage_by_model"].items():
                if not usage.get("total_tokens", 0):
                    continue
                actual_family = model_family(model)
                if actual_family != expected_family:
                    completeness_violations.append(
                        f"thread {thread_id}: child {child_id} role {role!r} used {actual_family!r} model family "
                        f"({model}); expected {expected_family!r}"
                    )

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

    integrity_failures = list(completeness_violations)
    if sol_execution_calls:
        routing_policy_findings.append(f"{len(sol_execution_calls)} non-read-only tool call(s) were made by Sol")
    if unknown_models:
        integrity_failures.append("unknown model family: " + ", ".join(unknown_models))
    observations = []
    if total_tokens and not lower_cost_tokens:
        observations.append("no Terra or Luna tokens were observed; confirm that all work was judgment-only")

    root_sessions = [session for session in sessions if not session["parent_thread_id"]]
    for session in root_sessions:
        root_models = [model for model, usage in session["usage_by_model"].items() if usage.get("total_tokens", 0)]
        if (
            session["task_complete"]
            and session["last_token_line"]
            and sum(usage.get("total_tokens", 0) for usage in session["usage_by_model"].values()) >= 1_000_000
            and len(root_models) == 1
            and not children_by_parent.get(str(session["thread_id"]))
            and not any(role in {"reviewer", "risk_reviewer"} for role in roles)
        ):
            observations.append(
                f"advisory: long all-single-model task on {root_models[0]} had no subagent or reviewer; assess whether a second perspective was useful"
            )

    if enforcement_mode == "strict":
        violations = [*integrity_failures, *routing_policy_findings]
    else:
        violations = list(integrity_failures)
        observations.extend(f"advisory only: {item}" for item in routing_policy_findings)

    report = {
        "root": target,
        "enforcement_mode": enforcement_mode,
        "session_count": len(sessions),
        "cost_status": "partial_uncertain" if (
            integrity_failures or (enforcement_mode == "strict" and routing_policy_findings)
        ) else "complete",
        "weighted_cost_units": weighted_cost,
        "total_tokens": total_tokens,
        "model_totals": {model: dict(counter) for model, counter in sorted(model_totals.items())},
        "family_totals": {family: dict(family_totals[family]) for family in ("sol", "terra", "luna", "unknown")},
        "subagent_roles": dict(roles),
        "large_outputs": sorted(large_outputs, key=lambda item: item["chars"], reverse=True),
        "sol_execution_calls": sol_execution_calls,
        "sol_lifecycle_calls": sol_lifecycle_calls,
        "child_lifecycle_statuses": child_lifecycle_statuses,
        "completeness_violations": integrity_failures,
        "routing_policy_findings": routing_policy_findings,
        "routing_violations": violations,
        "routing_observations": observations,
        "delivery_report_findings": delivery_report_findings,
        "sessions": sessions,
    }
    return report


def render_report(report: dict[str, Any]) -> str:
    uncertainty = " [UNCERTAIN/PARTIAL]" if report["cost_status"] != "complete" else ""
    lines = [
        f"Routing mode: {report.get('enforcement_mode', 'strict')}",
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
    lines.append(f"Sol lifecycle coordination calls: {len(report.get('sol_lifecycle_calls', []))}")
    lines.append(f"Sol heavy-execution violations: {len(report.get('sol_execution_calls', []))}")
    lines.extend(("", f"Large tool outputs (>= threshold): {len(report['large_outputs'])}"))
    if report["routing_violations"]:
        lines.append("Routing/completeness violations:")
        lines.extend(f"- {item}" for item in report["routing_violations"])
    else:
        lines.append("Routing/completeness violations: none detected")
    if report["routing_observations"]:
        lines.append("Observations:")
        lines.extend(f"- {item}" for item in report["routing_observations"])
    if report.get("delivery_report_findings"):
        lines.append("Delivery report findings (advisory):")
        lines.extend(f"- {item}" for item in report["delivery_report_findings"])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="root thread id or path to its rollout JSONL")
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--large-output-chars", type=int, default=20_000)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat historical routing/process anomalies as exit-1 violations instead of advisory observations",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = audit_session_tree(
            args.target,
            args.sessions_root,
            args.large_output_chars,
            enforcement_mode="strict" if args.strict else "advisory",
        )
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
