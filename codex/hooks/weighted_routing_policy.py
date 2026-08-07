"""Shared classifiers for the runtime Hook and post-run auditor."""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
from typing import Any


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
SAFE_AGENT_CONTROLS = {"spawn_agent", "wait_agent", "close_agent", "resume_agent", "send_input"}
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
