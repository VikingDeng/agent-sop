"""Shared classifiers for the runtime Hook and post-run auditor."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
import os
import re
import shlex
from typing import Any


ROLE_MODEL_FAMILIES = {
    "explorer": "luna",
    "focused_worker": "luna",
    "luna_executor": "luna",
    "verifier": "luna",
    "worker": "terra",
    "terra_debugger": "terra",
    "reviewer": "terra",
    "risk_reviewer": "sol",
}

MAX_CONCURRENT_OPEN_THREADS = 2
MAX_RISK_REVIEWERS_PER_SESSION = 1
GLOBAL_LOOP_BUDGET = {
    "initial": 1,
    "review": 1,
    "correction": 1,
    "re_review": 1,
}
PACKAGE_PHASES = frozenset({"map", "initial", "review", "correction", "re_review", "verify"})
PACKAGE_ID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}"
PACKAGE_PHASE_ROLES = {
    "map": frozenset({"explorer"}),
    "initial": frozenset({"focused_worker", "luna_executor", "worker", "terra_debugger"}),
    "review": frozenset({"reviewer", "risk_reviewer"}),
    "correction": frozenset({"focused_worker", "luna_executor", "worker", "terra_debugger"}),
    "re_review": frozenset({"reviewer", "risk_reviewer"}),
    "verify": frozenset({"verifier"}),
}

NESTED_AGENT_FACTORIES = frozenset({
    "multi_agent_v1__spawn_agent",
    "multi_agent_v1__create_agent",
})
NESTED_AGENT_FIELDS = frozenset({"agent_type", "role", "model", "fork_context", "message"})
MAX_FUNCTIONS_EXEC_SOURCE = 16_384


@dataclass(frozen=True)
class NestedAgentCall:
    factory: str
    payload: dict[str, Any]
    role: str


@dataclass(frozen=True)
class FunctionsExecAnalysis:
    canonical_call: NestedAgentCall | None = None
    dynamic_tool_access: bool = False


@dataclass(frozen=True)
class SpawnResult:
    succeeded: bool = False
    unknown_luna: bool = False
    thread_limit: bool = False


@dataclass(frozen=True)
class SpawnRequest:
    """Normalized identity and model evidence for one spawn request."""

    role: str | None
    model: str | None
    identity_values: tuple[str, ...]
    model_values: tuple[str, ...]
    role_family: str | None
    model_family: str | None
    identity_alias_conflict: bool
    model_alias_conflict: bool
    role_model_conflict: bool
    message: str | None
    package_id: str | None
    package_phase: str | None
    package_error: str | None

    @property
    def requested_role(self) -> str:
        if self.identity_alias_conflict:
            return "ambiguous"
        return self.role or self.model_family or "unspecified"

    @property
    def luna_role(self) -> str | None:
        if self.has_conflict:
            return None
        if self.role_family == "luna":
            return self.role
        if self.role_family is None and self.model_family == "luna":
            return "luna"
        return None

    @property
    def has_conflict(self) -> bool:
        return self.identity_alias_conflict or self.model_alias_conflict or self.role_model_conflict


@dataclass(frozen=True)
class RecontractEvidence:
    old_package_id: str
    new_package_id: str
    old_contract_sha256: str
    new_contract_sha256: str
    reason: str
    scope_acceptance_delta: str


POST_FAILURE_ALLOWED_ROLES = frozenset({"reviewer", "risk_reviewer"})
SPAWN_IDENTITY_FIELDS = ("agent_type", "subagent_type", "role", "name")
SPAWN_MODEL_FIELDS = ("model", "model_name")
SPAWN_IDENTIFIERS = ("agent_id", "thread_id", "task_name")
FAILED_STATUSES = frozenset({"failed", "failure", "error", "errored", "unsuccessful"})


def _model_matches_family(model: str, family: str) -> bool:
    return re.search(rf"(?:^|[-_.:/]){re.escape(family)}(?:$|[-_.:/])", model) is not None


def _normalized_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    return normalized or None


def _model_family(model: str | None) -> str | None:
    if model is None:
        return None
    for family in ("sol", "terra", "luna"):
        if _model_matches_family(model, family):
            return family
    return None


def _alias_values(payload: dict[str, Any], fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        normalized
        for key in fields
        if (normalized := _normalized_string(payload.get(key))) is not None
    ))


def parse_package_markers(message: Any) -> tuple[str | None, str | None, str | None]:
    if not isinstance(message, str) or not message.strip():
        return None, None, "spawn message requires PACKAGE_ID and PACKAGE_PHASE markers"
    package_ids = re.findall(r"(?m)^PACKAGE_ID:\s*([^\s]+)\s*$", message)
    phases = re.findall(r"(?m)^PACKAGE_PHASE:\s*([^\s]+)\s*$", message)
    if len(package_ids) != 1 or len(phases) != 1:
        return None, None, "spawn message requires exactly one PACKAGE_ID and one PACKAGE_PHASE marker"
    package_id = package_ids[0]
    phase = phases[0]
    if not re.fullmatch(PACKAGE_ID_PATTERN, package_id):
        return None, None, "PACKAGE_ID must be a stable nonempty identifier of at most 128 characters"
    if phase not in PACKAGE_PHASES:
        return None, None, "PACKAGE_PHASE must be one of map|initial|review|correction|re_review|verify"
    return package_id, phase, None


def parse_recontract_evidence(
    message: Any,
    *,
    new_package_id: str | None,
) -> tuple[RecontractEvidence | None, str | None]:
    """Parse explicit supervisor-declared re-contract evidence without inferring semantics."""
    if not isinstance(message, str):
        return None, None
    fields = {
        "old_package_id": "RECONTRACT_OLD_PACKAGE_ID",
        "new_package_id": "RECONTRACT_NEW_PACKAGE_ID",
        "old_contract_sha256": "RECONTRACT_OLD_CONTRACT_SHA256",
        "new_contract_sha256": "RECONTRACT_NEW_CONTRACT_SHA256",
        "reason": "RECONTRACT_REASON",
        "scope_acceptance_delta": "RECONTRACT_SCOPE_ACCEPTANCE_DELTA",
    }
    found: dict[str, str] = {}
    any_marker = False
    for field, marker in fields.items():
        any_marker |= re.search(rf"(?m)^{marker}:", message) is not None
        values = re.findall(rf"(?m)^{marker}:\s*(\S(?:.*\S)?)\s*$", message)
        if len(values) > 1:
            return None, f"re-contract evidence requires exactly one {marker} marker"
        if values:
            found[field] = values[0]
    if not any_marker:
        return None, None
    missing = [marker for field, marker in fields.items() if field not in found]
    if missing:
        return None, "re-contract evidence is missing " + ", ".join(missing)
    if not re.fullmatch(PACKAGE_ID_PATTERN, found["old_package_id"]):
        return None, "RECONTRACT_OLD_PACKAGE_ID is invalid"
    if not re.fullmatch(PACKAGE_ID_PATTERN, found["new_package_id"]):
        return None, "RECONTRACT_NEW_PACKAGE_ID is invalid"
    if found["new_package_id"] != new_package_id:
        return None, "RECONTRACT_NEW_PACKAGE_ID must equal PACKAGE_ID"
    if found["old_package_id"] == found["new_package_id"]:
        return None, "re-contract evidence requires different old and new PACKAGE_ID values"
    for field, marker in (
        ("old_contract_sha256", "RECONTRACT_OLD_CONTRACT_SHA256"),
        ("new_contract_sha256", "RECONTRACT_NEW_CONTRACT_SHA256"),
    ):
        if not re.fullmatch(r"[0-9A-Fa-f]{64}", found[field]):
            return None, f"{marker} must be a 64-hex SHA-256"
    if found["old_contract_sha256"].lower() == found["new_contract_sha256"].lower():
        return None, "re-contract evidence requires different old and new contract SHA-256 values"
    return RecontractEvidence(
        old_package_id=found["old_package_id"],
        new_package_id=found["new_package_id"],
        old_contract_sha256=found["old_contract_sha256"].lower(),
        new_contract_sha256=found["new_contract_sha256"].lower(),
        reason=found["reason"],
        scope_acceptance_delta=found["scope_acceptance_delta"],
    ), None


def package_contract_error(request: SpawnRequest) -> str | None:
    if request.package_error:
        return request.package_error
    if request.role not in ROLE_MODEL_FAMILIES:
        return "package-marked custom spawn requires a configured role"
    allowed = PACKAGE_PHASE_ROLES.get(request.package_phase or "", frozenset())
    if request.role not in allowed:
        return f"role {request.role!r} is not permitted for PACKAGE_PHASE {request.package_phase!r}"
    if (
        request.package_phase == "initial"
        and request.role_family == "terra"
        and not re.search(r"LUNA_ELIGIBLE=no\([^\r\n)]*\S[^\r\n)]*\)", request.message or "")
    ):
        return "Terra initial requires LUNA_ELIGIBLE=no(reason) with a nonempty reason"
    return None


def _classify_spawn_payload(payload: dict[str, Any]) -> SpawnRequest:
    identity_values = _alias_values(payload, SPAWN_IDENTITY_FIELDS)
    model_values = _alias_values(payload, SPAWN_MODEL_FIELDS)
    identity_alias_conflict = len(identity_values) > 1
    model_alias_conflict = len(model_values) > 1
    role = identity_values[0] if len(identity_values) == 1 else None
    model = model_values[0] if len(model_values) == 1 else None
    role_family = ROLE_MODEL_FAMILIES.get(role or "")
    model_family = _model_family(model)
    message = payload.get("message") if isinstance(payload.get("message"), str) else None
    package_id, package_phase, package_error = parse_package_markers(message)
    return SpawnRequest(
        role=role,
        model=model,
        identity_values=identity_values,
        model_values=model_values,
        role_family=role_family,
        model_family=model_family,
        identity_alias_conflict=identity_alias_conflict,
        model_alias_conflict=model_alias_conflict,
        role_model_conflict=bool(
            not identity_alias_conflict
            and not model_alias_conflict
            and role_family is not None
            and model is not None
            and not _model_matches_family(model, role_family)
        ),
        message=message,
        package_id=package_id,
        package_phase=package_phase,
        package_error=package_error,
    )


def classify_spawn_request(tool_name: str, payload: dict[str, Any]) -> SpawnRequest | None:
    """Classify direct and canonical nested spawn inputs identically for all consumers."""
    leaf = normalize_tool_name(tool_name)
    if leaf in {"agent", "spawn_agent", "create_agent"}:
        action = _normalized_string(payload.get("action") or payload.get("operation") or payload.get("mode"))
        if leaf == "agent" and action in {"list", "inspect", "status"}:
            return None
        return _classify_spawn_payload(payload)
    if leaf != "exec":
        return None
    analysis = analyze_functions_exec(command_text(payload))
    if analysis.canonical_call is None:
        return None
    return _classify_spawn_payload(analysis.canonical_call.payload)


def spawn_request_signature(tool_name: str, payload: dict[str, Any]) -> str:
    """Hash the complete canonical accepted spawn payload without persisting its prompt."""
    request = classify_spawn_request(tool_name, payload)
    if request is None:
        raise ValueError("tool input is not a recognized spawn request")
    leaf = normalize_tool_name(tool_name)
    if leaf == "exec":
        analysis = analyze_functions_exec(command_text(payload))
        if analysis.canonical_call is None:
            raise ValueError("tool input is not a canonical nested spawn request")
        factory = analysis.canonical_call.factory
        accepted_payload = dict(analysis.canonical_call.payload)
    else:
        factory = leaf
        accepted_payload = dict(payload)

    # Alias spelling is transport noise after classification. Preserve every other
    # accepted input, including fork and reasoning controls, in the signed payload.
    for field in (*SPAWN_IDENTITY_FIELDS, *SPAWN_MODEL_FIELDS):
        accepted_payload.pop(field, None)
    accepted_payload["role"] = request.role
    accepted_payload["model"] = request.model
    signature_payload = {
        "factory": factory,
        "payload": accepted_payload,
    }
    serialized = json.dumps(signature_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def post_failure_role_allowed(request: SpawnRequest | None) -> bool:
    return bool(
        request is not None
        and not request.has_conflict
        and request.role in POST_FAILURE_ALLOWED_ROLES
    )


def _contains_unknown_luna(value: Any) -> bool:
    if isinstance(value, str):
        text = value.lower()
    else:
        try:
            text = json.dumps(value, ensure_ascii=False).lower()
        except (TypeError, ValueError):
            return False
    return bool(
        re.search(r"unknown\s+model[^\n]*gpt-5\.6-luna", text)
        or re.search(r"gpt-5\.6-luna[^\n]*(?:unknown|unavailable|not available|not found)", text)
    )


def _contains_thread_limit(value: Any) -> bool:
    if isinstance(value, str):
        text = value.lower()
    else:
        try:
            text = json.dumps(value, ensure_ascii=False).lower()
        except (TypeError, ValueError):
            return False
    return bool(
        re.search(r"agent[-_ ]thread[-_ ]limit", text)
        or re.search(r"(?:maximum|max)[-_ ]?(?:number of )?(?:open )?threads", text)
        or re.search(r"too many (?:open )?(?:agent )?threads", text)
    )


def _failure_context_payload(payload: dict[str, Any]) -> bool:
    status = payload.get("status")
    return bool(
        payload.get("isError")
        or payload.get("is_error")
        or payload.get("failed")
        or (isinstance(status, str) and status.strip().lower() in FAILED_STATUSES)
    )


def _error_content_values(content: Any, *, enclosing_failure: bool = False) -> list[Any]:
    blocks = content if isinstance(content, list) else [content]
    values: list[Any] = []
    for block in blocks:
        if isinstance(block, str):
            if enclosing_failure:
                values.append(block)
            continue
        if not isinstance(block, dict):
            continue
        block_type = _normalized_string(block.get("type"))
        block_is_error = enclosing_failure or bool(
            block.get("isError")
            or block.get("is_error")
            or block.get("failed")
            or block.get("error") not in (None, False, "")
            or block_type in {"error", "error_text", "tool_error"}
        )
        if not block_is_error:
            continue
        for key in ("error", "message", "text"):
            if block.get(key) not in (None, False, ""):
                values.append(block[key])
        if "content" in block:
            values.extend(_error_content_values(block["content"], enclosing_failure=True))
    return values


def _structured_error_values(payload: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    failed = _failure_context_payload(payload)
    if payload.get("error") not in (None, False, ""):
        values.append(payload["error"])
    if failed and payload.get("message") not in (None, False, ""):
        values.append(payload["message"])
    if "content" in payload:
        values.extend(_error_content_values(payload["content"], enclosing_failure=failed))
    return values


def unknown_luna_failure(value: Any, *, luna_role: str | None) -> bool:
    """Recognize Luna unavailability only from plain errors or structured error evidence."""
    if luna_role is None or (luna_role != "luna" and ROLE_MODEL_FAMILIES.get(luna_role) != "luna"):
        return False
    payload = _spawn_result_object(value)
    if payload is not None:
        return any(_contains_unknown_luna(item) for item in _structured_error_values(payload))
    return isinstance(value, str) and _contains_unknown_luna(value)


def thread_limit_failure(value: Any) -> bool:
    """Recognize the thread-limit resource error without treating it as Luna failure."""
    payload = _spawn_result_object(value)
    if payload is not None:
        if any(_contains_thread_limit(payload.get(key)) for key in ("status", "code", "error", "message")):
            return True
        return any(_contains_thread_limit(item) for item in _structured_error_values(payload))
    return isinstance(value, str) and _contains_thread_limit(value)


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


def classify_spawn_result(value: Any, *, luna_role: str | None = None) -> SpawnResult:
    """Classify only explicit supported spawn results; unknown Luna wins over success."""
    if thread_limit_failure(value):
        return SpawnResult(thread_limit=True)
    if unknown_luna_failure(value, luna_role=luna_role):
        return SpawnResult(unknown_luna=True)
    payload = _spawn_result_object(value)
    if payload is None:
        return SpawnResult()
    if payload.get("isError") or payload.get("is_error"):
        return SpawnResult()
    if payload.get("error") not in (None, False, ""):
        return SpawnResult()
    status = payload.get("status")
    if isinstance(status, str) and status.lower() in FAILED_STATUSES:
        return SpawnResult()
    if payload.get("failed"):
        return SpawnResult()
    for key in SPAWN_IDENTIFIERS:
        identifier = payload.get(key)
        if isinstance(identifier, str) and identifier.strip():
            return SpawnResult(succeeded=True)
    return SpawnResult()


def close_result_succeeded(value: Any) -> bool:
    """Accept documented close output unless the prior agent status was not_found."""
    payload = _spawn_result_object(value)
    if payload is None:
        return False
    if (
        payload.get("isError")
        or payload.get("is_error")
        or payload.get("failed")
        or payload.get("error") not in (None, False, "")
    ):
        return False
    previous_status = payload.get("previous_status")
    if isinstance(previous_status, str):
        return previous_status in {"pending_init", "running", "interrupted", "shutdown"}
    if not isinstance(previous_status, dict) or not previous_status:
        return False
    return bool(set(previous_status) & {"completed", "errored"})


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"JSON constant {value!r} is not permitted")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_strict_json_object(source: str) -> dict[str, Any]:
    try:
        value = json.loads(
            source,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"spawn payload is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("spawn payload must be a JSON object")
    return value


def _validate_canonical_payload(factory: str, payload: dict[str, Any]) -> NestedAgentCall:
    unknown = sorted(set(payload) - NESTED_AGENT_FIELDS)
    if unknown:
        raise ValueError("spawn payload has unknown field(s): " + ", ".join(unknown))
    identity_fields = [key for key in ("agent_type", "role") if key in payload]
    if len(identity_fields) != 1:
        raise ValueError("spawn payload requires exactly one known agent_type or role")
    role = payload[identity_fields[0]]
    if not isinstance(role, str) or role not in ROLE_MODEL_FAMILIES:
        raise ValueError("spawn payload agent_type/role is not a configured role")
    if payload.get("fork_context") is not False:
        raise ValueError("spawn payload requires fork_context exactly false")
    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("spawn payload requires a nonempty static message string")
    model = payload.get("model")
    if model is not None:
        if not isinstance(model, str) or not model:
            raise ValueError("spawn payload model must be a nonempty string when present")
        if not _model_matches_family(model, ROLE_MODEL_FAMILIES[role]):
            raise ValueError(
                f"spawn payload model does not match the {ROLE_MODEL_FAMILIES[role]} family for {role}"
            )
    if role == "risk_reviewer" and any(
        marker not in message for marker in ("HIGH_RISK_TRIGGER:", "EVIDENCE_PACK:")
    ):
        raise ValueError("risk_reviewer message requires HIGH_RISK_TRIGGER and EVIDENCE_PACK")
    request = _classify_spawn_payload(payload)
    if (contract_error := package_contract_error(request)) is not None:
        raise ValueError(contract_error)
    return NestedAgentCall(factory=factory, payload=payload, role=role)


def _read_js_string_token(source: str, position: int) -> tuple[str | None, int]:
    quote = source[position]
    position += 1
    content: list[str] = []
    while position < len(source):
        character = source[position]
        if character == quote:
            return "".join(content), position + 1
        if character != "\\":
            content.append(character)
            position += 1
            continue
        position += 1
        if position >= len(source):
            return None, position
        escaped = source[position]
        simple = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
        if escaped in simple:
            content.append(simple[escaped])
            position += 1
            continue
        if escaped == "x" and position + 2 < len(source):
            digits = source[position + 1:position + 3]
            if re.fullmatch(r"[0-9A-Fa-f]{2}", digits):
                content.append(chr(int(digits, 16)))
                position += 3
                continue
        if escaped == "u":
            if position + 1 < len(source) and source[position + 1] == "{":
                end = source.find("}", position + 2)
                digits = source[position + 2:end] if end != -1 else ""
                if digits and re.fullmatch(r"[0-9A-Fa-f]+", digits):
                    codepoint = int(digits, 16)
                    if codepoint <= 0x10FFFF:
                        content.append(chr(codepoint))
                        position = end + 1
                        continue
            digits = source[position + 1:position + 5]
            if len(digits) == 4 and re.fullmatch(r"[0-9A-Fa-f]{4}", digits):
                content.append(chr(int(digits, 16)))
                position += 5
                continue
        if escaped in "\\'\"`$":
            content.append(escaped)
            position += 1
            continue
        return None, position + 1
    return None, position


def _is_js_identifier_start(character: str) -> bool:
    return character in "_$" or character.isalpha() or (
        ord(character) > 127 and ("a" + character).isidentifier()
    )


def _is_js_identifier_part(character: str) -> bool:
    return (
        _is_js_identifier_start(character)
        or character.isdigit()
        or character in "\u200c\u200d"
        or (ord(character) > 127 and ("a" + character).isidentifier())
    )


def _read_js_identifier_escape(source: str, position: int) -> tuple[str, int]:
    """Decode one JavaScript ``\\u`` identifier escape or fail closed."""
    if not source.startswith("\\u", position):
        raise ValueError("invalid JavaScript identifier escape")
    cursor = position + 2
    if cursor < len(source) and source[cursor] == "{":
        end = source.find("}", cursor + 1)
        digits = source[cursor + 1:end] if end != -1 else ""
        if not digits or len(digits) > 6 or not re.fullmatch(r"[0-9A-Fa-f]+", digits):
            raise ValueError("invalid JavaScript identifier escape")
        codepoint = int(digits, 16)
        if codepoint > 0x10FFFF:
            raise ValueError("invalid JavaScript identifier escape")
        return chr(codepoint), end + 1
    digits = source[cursor:cursor + 4]
    if len(digits) != 4 or not re.fullmatch(r"[0-9A-Fa-f]{4}", digits):
        raise ValueError("invalid JavaScript identifier escape")
    return chr(int(digits, 16)), cursor + 4


def _read_js_identifier(source: str, position: int) -> tuple[str, bool, int]:
    content: list[str] = []
    escaped = False
    while position < len(source):
        if source.startswith("\\u", position):
            character, position = _read_js_identifier_escape(source, position)
            escaped = True
        else:
            character = source[position]
            if not (_is_js_identifier_start(character) if not content else _is_js_identifier_part(character)):
                break
            position += 1
        valid = _is_js_identifier_start(character) if not content else _is_js_identifier_part(character)
        if not valid:
            raise ValueError("invalid JavaScript identifier escape")
        content.append(character)
    if not content:
        raise ValueError("invalid JavaScript identifier")
    return "".join(content), escaped, position


def _js_tokens(source: str) -> list[tuple[str, str | None, bool]]:
    tokens: list[tuple[str, str | None, bool]] = []
    position = 0
    while position < len(source):
        if source[position].isspace():
            position += 1
            continue
        if source.startswith("//", position):
            newline = source.find("\n", position + 2)
            position = len(source) if newline == -1 else newline + 1
            continue
        if source.startswith("/*", position):
            end = source.find("*/", position + 2)
            if end == -1:
                raise ValueError("unterminated JavaScript comment")
            position = end + 2
            continue
        character = source[position]
        if character in "'\"":
            value, position = _read_js_string_token(source, position)
            tokens.append(("string", value, False))
            continue
        if character == "`":
            end = position + 1
            while end < len(source):
                if source[end] == "\\":
                    end += 2
                    continue
                if source[end] == "`":
                    break
                end += 1
            if end >= len(source):
                raise ValueError("unterminated JavaScript template")
            template = source[position + 1:end]
            expression_position = 0
            while expression_position < len(template):
                expression_start = template.find("${", expression_position)
                if expression_start == -1:
                    break
                cursor = expression_start + 2
                depth = 1
                while cursor < len(template) and depth:
                    if template[cursor] in "'\"`":
                        _, cursor = _read_js_string_token(template, cursor)
                        continue
                    if template[cursor] == "{":
                        depth += 1
                    elif template[cursor] == "}":
                        depth -= 1
                    cursor += 1
                if depth:
                    raise ValueError("unterminated JavaScript template expression")
                tokens.extend(_js_tokens(template[expression_start + 2:cursor - 1]))
                expression_position = cursor
            position = end + 1
            continue
        if _is_js_identifier_start(character) or source.startswith("\\u", position):
            identifier, escaped, position = _read_js_identifier(source, position)
            tokens.append(("identifier", identifier, escaped))
            continue
        tokens.append(("punctuation", character, False))
        position += 1
    return tokens


def executable_static_tool_calls(source: str) -> frozenset[str]:
    """Return normalized static ``tools`` call targets, excluding literals/comments."""
    if not isinstance(source, str):
        raise ValueError("functions.exec source must be a string")
    if len(source.encode("utf-8")) > MAX_FUNCTIONS_EXEC_SOURCE:
        raise ValueError(
            f"functions.exec source exceeds the {MAX_FUNCTIONS_EXEC_SOURCE}-byte policy limit"
        )
    tokens = _js_tokens(source)
    calls: set[str] = set()
    for index, (kind, value, _) in enumerate(tokens):
        if kind != "identifier" or value != "tools":
            continue
        target: str | None = None
        call_index = index + 3
        if (
            index + 3 < len(tokens)
            and tokens[index + 1][:2] == ("punctuation", ".")
            and tokens[index + 2][0] == "identifier"
        ):
            target = tokens[index + 2][1]
        elif (
            index + 4 < len(tokens)
            and tokens[index + 1][:2] == ("punctuation", "[")
            and tokens[index + 2][0] == "string"
            and tokens[index + 3][:2] == ("punctuation", "]")
        ):
            target = tokens[index + 2][1]
            call_index = index + 4
        if target is None or tokens[call_index][:2] != ("punctuation", "("):
            continue
        calls.add(str(target).lower().rsplit(".", 1)[-1].rsplit("__", 1)[-1])
    return frozenset(calls)


def _static_or_dynamic_tool_access(source: str) -> tuple[bool, bool]:
    tokens = _js_tokens(source)
    static_reference = False
    dynamic_access = False
    brace_stack: list[bool] = []
    for index, (kind, value, _) in enumerate(tokens):
        if kind == "punctuation" and value == "{":
            brace_stack.append(False)
            continue
        if kind == "punctuation" and value == "}" and brace_stack:
            has_factory = brace_stack.pop()
            if (
                has_factory
                and index + 2 < len(tokens)
                and tokens[index + 1][:2] == ("punctuation", "=")
                and tokens[index + 2][:2] == ("identifier", "tools")
            ):
                static_reference = True
            continue
        if kind == "identifier" and value in NESTED_AGENT_FACTORIES and brace_stack:
            brace_stack[-1] = True

    for index, (kind, value, _) in enumerate(tokens):
        if kind != "identifier":
            continue
        if value in NESTED_AGENT_FACTORIES:
            static_reference = True
        if value in {"eval", "Function"}:
            dynamic_access |= index + 1 < len(tokens) and tokens[index + 1][:2] == ("punctuation", "(")
        if value == "Reflect":
            dynamic_access = True
        if value in {"globalThis", "window", "self", "global", "Proxy"}:
            dynamic_access |= index + 1 < len(tokens) and tokens[index + 1][:2] in {
                ("punctuation", "["),
                ("punctuation", "("),
            }
        if value == "tools":
            if index + 1 < len(tokens) and tokens[index + 1][:2] == ("punctuation", "["):
                if (
                    index + 3 < len(tokens)
                    and tokens[index + 2][0] == "string"
                    and tokens[index + 3][:2] == ("punctuation", "]")
                ):
                    static_reference |= tokens[index + 2][1] in NESTED_AGENT_FACTORIES
                else:
                    dynamic_access = True
    return static_reference, dynamic_access


def analyze_functions_exec(source: str) -> FunctionsExecAnalysis:
    if not isinstance(source, str):
        raise ValueError("functions.exec source must be a string")
    if len(source.encode("utf-8")) > MAX_FUNCTIONS_EXEC_SOURCE:
        raise ValueError(
            f"functions.exec source exceeds the {MAX_FUNCTIONS_EXEC_SOURCE}-byte policy limit"
        )
    stripped = source.strip()
    canonical_call: NestedAgentCall | None = None
    prefix = re.match(
        r"await tools\.(multi_agent_v1__spawn_agent|multi_agent_v1__create_agent)\(",
        stripped,
    )
    if prefix:
        decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicate_json_keys, parse_constant=_reject_json_constant)
        try:
            payload, end = decoder.raw_decode(stripped, prefix.end())
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"canonical spawn statement has invalid JSON: {exc}") from exc
        while end < len(stripped) and stripped[end].isspace():
            end += 1
        if end >= len(stripped) or stripped[end] != ")":
            raise ValueError("canonical spawn statement must end after one JSON object")
        end += 1
        if end < len(stripped) and stripped[end] == ";":
            end += 1
        if stripped[end:].strip():
            raise ValueError("canonical functions.exec may contain only one spawn statement")
        if not isinstance(payload, dict):
            raise ValueError("canonical spawn argument must be a JSON object")
        canonical_call = _validate_canonical_payload(prefix.group(1), payload)
        return FunctionsExecAnalysis(canonical_call=canonical_call)

    static_reference, dynamic_access = _static_or_dynamic_tool_access(source)
    if static_reference:
        raise ValueError("exact agent factory reference is not in canonical form")
    return FunctionsExecAnalysis(dynamic_tool_access=dynamic_access)


MUTATING_TOOLS = {
    "apply_patch",
    "edit",
    "multiedit",
    "write",
    "write_file",
    "create_file",
    "delete_file",
}

READ_ONLY_COMMANDS = {"cat", "file", "head", "ls", "pwd", "rg", "stat", "tail", "type", "wc", "which"}
READ_ONLY_GIT = {"diff", "log", "rev-parse", "show", "status"}
SAFE_AGENT_CONTROLS = {"spawn_agent", "create_agent", "wait_agent", "close_agent", "resume_agent", "send_input"}
SAFE_LOCAL_STATE = {"get_goal", "update_plan", "view_image", "read_thread_terminal"}
MUTATING_NAME = re.compile(r"(?:^|_)(?:apply|create|delete|deploy|edit|install|merge|patch|push|remove|send|update|write)(?:_|$)")


def normalize_tool_name(tool_name: str) -> str:
    return tool_name.lower().rsplit(".", 1)[-1].rsplit("__", 1)[-1]


def command_text(tool_input: dict[str, Any]) -> str:
    for key in ("cmd", "command", "script", "raw"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def is_read_only_shell(command: str) -> bool:
    stripped = command.strip()
    if not stripped or re.search(r"[;&|><`\n]|\$\(", stripped):
        return False
    try:
        words = shlex.split(stripped)
    except ValueError:
        return False
    if not words:
        return False
    executable = os.path.basename(words[0])
    if executable == "git":
        return (
            len(words) >= 2
            and words[1] in READ_ONLY_GIT
            and not any(
                word.startswith(("--output", "--ext-diff", "--textconv", "--config-env", "--exec-path"))
                for word in words[2:]
            )
        )
    if executable not in READ_ONLY_COMMANDS:
        return False
    if executable == "rg" and any(
        word in {"--pre", "--hostname-bin"} or word.startswith(("--pre=", "--hostname-bin="))
        for word in words[1:]
    ):
        return False
    return True


def _nested_commands(raw: str) -> list[str]:
    commands: list[str] = []
    pattern = re.compile(r"(?:\"cmd\"|'cmd'|\bcmd)\s*:\s*(?P<literal>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')", re.DOTALL)
    for match in pattern.finditer(raw):
        literal = match.group("literal")
        try:
            value = json.loads(literal) if literal.startswith('"') else ast.literal_eval(literal)
        except (ValueError, SyntaxError, json.JSONDecodeError):
            continue
        if isinstance(value, str):
            commands.append(value)
    return commands


def _outer_exec_is_read_only(raw: str) -> bool:
    calls = re.findall(r"tools\.([A-Za-z0-9_]+)\s*\(", raw)
    canonicalized = re.sub(r"tools\.[A-Za-z0-9_]+\s*\(", "CANONICAL_TOOL(", raw)
    if re.search(r"\btools\b", canonicalized):
        return False
    if not calls:
        return True
    nested_commands = _nested_commands(raw)
    command_index = 0
    for call in calls:
        leaf = normalize_tool_name(call)
        if leaf == "exec_command":
            if command_index >= len(nested_commands) or not is_read_only_shell(nested_commands[command_index]):
                return False
            command_index += 1
            continue
        if leaf in SAFE_AGENT_CONTROLS or leaf in SAFE_LOCAL_STATE:
            continue
        if leaf in {"run", "read_mcp_resource"} or leaf.startswith(("get_", "list_", "read_", "search_", "find_", "open_")):
            continue
        return False
    return command_index == len(nested_commands)


def is_sol_execution(tool_name: str, tool_input: dict[str, Any]) -> bool:
    leaf = normalize_tool_name(tool_name)
    command = command_text(tool_input)
    if leaf == "exec":
        return not _outer_exec_is_read_only(command)
    if leaf in {"bash", "exec_command", "shell", "terminal"}:
        return not is_read_only_shell(command)
    if leaf in SAFE_AGENT_CONTROLS or leaf in SAFE_LOCAL_STATE:
        return False
    if leaf in MUTATING_TOOLS or MUTATING_NAME.search(leaf):
        return True
    if leaf in {"run", "read_mcp_resource"} or leaf.startswith(("get_", "list_", "read_", "search_", "find_", "open_", "view_")):
        return False
    return True
