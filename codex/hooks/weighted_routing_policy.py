"""Shared classifiers for the runtime Hook and post-run auditor."""

from __future__ import annotations

import ast
from dataclasses import dataclass
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


def _model_matches_family(model: str, family: str) -> bool:
    return re.search(rf"(?:^|[-_.:/]){re.escape(family)}(?:$|[-_.:/])", model) is not None


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
