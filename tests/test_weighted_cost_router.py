from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "codex/hooks/weighted_cost_router.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("weighted_cost_router", SCRIPT)
assert SPEC and SPEC.loader
ROUTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROUTER)


def pretool(model: str, tool_name: str, tool_input: dict | str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "session_id": "test-session",
        "model": model,
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


class WeightedCostRouterTests(unittest.TestCase):
    def test_session_start_injects_objective_and_luna_gate(self) -> None:
        result = ROUTER.handle({"hook_event_name": "SessionStart"})
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("25*Sol", context)
        self.assertIn("LUNA_ELIGIBLE", context)

    def test_sol_direct_mutation_is_denied(self) -> None:
        result = ROUTER.handle(pretool("gpt-5.6-sol", "apply_patch", {"patch": "x"}))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_sol_nested_mutation_is_denied(self) -> None:
        result = ROUTER.handle(pretool(
            "gpt-5.6-sol",
            "functions.exec",
            'await tools.apply_patch("*** Begin Patch")',
        ))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_sol_heavy_command_is_denied_but_targeted_read_is_allowed(self) -> None:
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "exec_command", {"cmd": "python -m pytest"}))
        nested = ROUTER.handle(pretool(
            "gpt-5.6-sol", "functions.exec", 'await tools.exec_command({"cmd":"python3 -m unittest"})'
        ))
        allowed = ROUTER.handle(pretool("gpt-5.6-sol", "exec_command", {"cmd": "rg --files src"}))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(nested["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(allowed)

    def test_every_governed_heavy_command_class_is_denied(self) -> None:
        commands = (
            "poetry install",
            "terraform plan",
            "git tag v1",
            "cargo build",
            "go test ./...",
            "pnpm run build",
            "pip install package",
            "make all",
            "docker build .",
            "kubectl apply -f deployment.yaml",
            "launchctl stop service",
            "bash scripts/deploy.sh",
        )
        for command in commands:
            with self.subTest(command=command):
                result = ROUTER.handle(pretool(
                    "gpt-5.6-sol",
                    "functions.exec",
                    f'await tools.exec_command({{"cmd":{command!r}}})',
                ))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_shell_writes_and_unknown_nested_mutators_are_denied(self) -> None:
        cases = (
            ("exec_command", {"cmd": "sed -i.bak s/a/b/ file"}),
            ("functions.exec", 'await tools.write({"path":"file"})'),
            ("functions.exec", 'await tools.exec_command({"cmd":"rg pytest tests"})'),
        )
        for tool, value in cases[:2]:
            with self.subTest(tool=tool):
                result = ROUTER.handle(pretool("gpt-5.6-sol", tool, value))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", *cases[2])))

    def test_nested_agent_policy_is_enforced(self) -> None:
        full = ROUTER.handle(pretool(
            "gpt-5.6-sol",
            "functions.exec",
            "await tools.multi_agent_v1__spawn_agent({agent_type:'worker',fork_context:true,message:'x'})",
        ))
        risk = ROUTER.handle(pretool(
            "gpt-5.6-sol",
            "functions.exec",
            "await tools.multi_agent_v1__spawn_agent({agent_type:'risk_reviewer',fork_context:false,message:'review'})",
        ))
        self.assertEqual(full["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(risk["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_pretool_schema_uncertainty_fails_closed(self) -> None:
        result = ROUTER.handle({"hook_event_name": "PreToolUse", "tool_input": {}})
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_malformed_json_exits_nonzero_and_records_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ, CODEX_ROUTER_STATE_DIR=directory)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input="not json",
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue((Path(directory) / "hook-errors.jsonl").exists())

    def test_schema_invalid_json_exits_nonzero_and_records_error(self) -> None:
        for payload in ("[]", "{}"):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                environment = dict(os.environ, CODEX_ROUTER_STATE_DIR=directory)
                completed = subprocess.run(
                    [sys.executable, str(SCRIPT)],
                    input=payload,
                    text=True,
                    capture_output=True,
                    env=environment,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertTrue((Path(directory) / "hook-errors.jsonl").exists())

    def test_computed_and_aliased_tool_access_are_denied(self) -> None:
        cases = (
            'await tools["apply_patch"]("patch")',
            "const t=tools; await t.spawn_agent({agent_type:'worker',fork_context:true})",
        )
        for source in cases:
            with self.subTest(source=source):
                result = ROUTER.handle(pretool("gpt-5.6-sol", "functions.exec", source))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_mutating_options_of_read_tools_are_denied(self) -> None:
        commands = (
            "git branch codex/probe",
            "sed -n 'w /tmp/router-probe' input.txt",
            "rg --pre 'touch /tmp/router-probe' pattern .",
            "git diff --output=/tmp/diff",
        )
        for command in commands:
            with self.subTest(command=command):
                result = ROUTER.handle(pretool("gpt-5.6-sol", "exec_command", {"cmd": command}))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_luna_can_edit_and_test(self) -> None:
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-luna", "apply_patch", {"patch": "x"})))
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-luna", "exec_command", {"cmd": "pytest"})))

    def test_risk_reviewer_requires_trigger_and_evidence_pack(self) -> None:
        missing = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "agent_type": "risk_reviewer",
            "message": "review this",
            "fork_turns": "none",
        }))
        accepted = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "agent_type": "risk_reviewer",
            "message": "HIGH_RISK_TRIGGER: concurrency\nEVIDENCE_PACK: diff and tests",
            "fork_turns": "none",
        }))
        self.assertEqual(missing["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(accepted)

    def test_full_history_fork_is_denied_for_every_role(self) -> None:
        result = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "agent_type": "luna_executor",
            "message": "bounded task",
            "fork_turns": "all",
        }))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_unspecified_child_that_may_inherit_sol_is_denied(self) -> None:
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "message": "do the implementation",
            "fork_context": False,
        }))
        allowed = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "agent_type": "luna_executor",
            "message": "bounded implementation",
            "fork_context": False,
        }))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(allowed)

    def test_third_short_wait_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            event = pretool("gpt-5.6-sol", "wait_agent", {})
            self.assertIsNone(ROUTER.handle(event))
            self.assertIsNone(ROUTER.handle(event))
            result = ROUTER.handle(event)
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
