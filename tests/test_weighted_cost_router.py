from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
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


def nested_spawn(
    role: str,
    *,
    model: str | None = None,
    message: str = "bounded canonical task",
    factory: str = "multi_agent_v1__spawn_agent",
) -> str:
    payload = {"agent_type": role, "fork_context": False, "message": message}
    if model is not None:
        payload["model"] = model
    return f"await tools.{factory}({json.dumps(payload, separators=(',', ':'))});"


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

    def test_sol_parent_may_spawn_explicit_terra_debugger_without_full_fork(self) -> None:
        result = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "agent_type": "terra_debugger",
            "message": "unknown root cause; test ranked hypotheses",
            "fork_context": False,
        }))
        self.assertIsNone(result)

    def test_terra_debugger_subagent_context_is_hypothesis_first_and_no_fallback(self) -> None:
        result = ROUTER.handle({
            "hook_event_name": "SubagentStart",
            "agent_type": "terra_debugger",
        })
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("hypothesis-first", context)
        self.assertIn("no-fallback", context)
        self.assertIn("compact evidence packet", context)

    def test_known_role_model_mismatches_are_denied(self) -> None:
        cases = (
            ("terra_debugger", "gpt-5.6-sol"),
            ("luna_executor", "gpt-5.6-terra"),
        )
        for role, model in cases:
            with self.subTest(role=role, model=model):
                result = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
                    "agent_type": role,
                    "model": model,
                    "message": "bounded task",
                    "fork_context": False,
                }))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_known_role_correct_or_omitted_model_overrides_are_allowed(self) -> None:
        cases = (
            {
                "agent_type": "terra_debugger",
                "model": "gpt-5.6-terra",
                "message": "diagnose an unknown root cause",
                "fork_context": False,
            },
            {
                "agent_type": "luna_executor",
                "model": "gpt-5.6-luna",
                "message": "bounded implementation",
                "fork_context": False,
            },
            {
                "agent_type": "reviewer",
                "message": "review the bounded diff",
                "fork_context": False,
            },
        )
        for tool_input in cases:
            with self.subTest(tool_input=tool_input):
                self.assertIsNone(ROUTER.handle(pretool(
                    "gpt-5.6-sol", "spawn_agent", tool_input
                )))

    def test_canonical_nested_agent_calls_allow_matching_or_omitted_models(self) -> None:
        cases = (
            nested_spawn("luna_executor"),
            nested_spawn("luna_executor", model="gpt-5.6-luna"),
            nested_spawn("terra_debugger", model="gpt-5.6-terra", factory="multi_agent_v1__create_agent"),
        )
        for source in cases:
            with self.subTest(source=source):
                self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "functions.exec", source)))

    def test_canonical_nested_agent_payload_rejects_policy_errors(self) -> None:
        cases = (
            nested_spawn("luna_executor", model="gpt-5.6-terra"),
            nested_spawn("missing_role"),
            nested_spawn("luna_executor").replace('"agent_type":"luna_executor",', ""),
            nested_spawn("luna_executor").replace('"fork_context":false', '"fork_context":true'),
            nested_spawn("luna_executor").replace('"fork_context":false,', ""),
            nested_spawn("luna_executor").replace('"message":"bounded canonical task"', '"message":""'),
            nested_spawn("luna_executor").replace('"message":"bounded canonical task"', '"message":selectedMessage'),
            nested_spawn("luna_executor").replace('"message":"bounded canonical task"', '"unknown":"x","message":"bounded canonical task"'),
            'await tools.multi_agent_v1__spawn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x","agent_type":"terra_debugger"});',
        )
        for source in cases:
            with self.subTest(source=source):
                result = ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", source))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_nested_risk_reviewer_requires_markers(self) -> None:
        allowed = nested_spawn(
            "risk_reviewer",
            model="gpt-5.6-sol",
            message="HIGH_RISK_TRIGGER: parser boundary\nEVIDENCE_PACK: focused diff",
        )
        missing = nested_spawn("risk_reviewer", model="gpt-5.6-sol", message="ordinary review")
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", allowed)))
        denied = ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", missing))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_nested_agent_statement_must_be_the_only_statement(self) -> None:
        canonical = nested_spawn("luna_executor")
        cases = (
            "const result = " + canonical,
            canonical + " " + canonical,
            canonical + " await tools.exec_command({\"cmd\":\"pwd\"});",
            "/* comment */ " + canonical,
            canonical.replace("await tools.", "await tools /* comment */."),
        )
        for source in cases:
            with self.subTest(source=source):
                result = ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", source))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_nested_agent_factory_static_bypasses_are_denied(self) -> None:
        cases = (
            'const { multi_agent_v1__spawn_agent: spawn } = tools; await spawn({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
            'await tools[ /* comment */ "multi_agent_v1__spawn_agent"]({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
            'await tools["multi_agent_v1__\\u0073pawn_agent"]({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
            'await tools["multi_agent_v1__\\x73pawn_agent"]({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
            'await tools.multi_agent_v1__sp\\u0061wn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
            'await tools.multi_agent_v1__sp\\u{61}wn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
            'await tools.multi_agent_v1__sp\\u00zzwn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
        )
        for source in cases:
            with self.subTest(source=source):
                result = ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", source))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        source = 'await tools.multi_agent_v1__spawn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x","agent_type":"terra_debugger"});'
        result = ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", source))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_respawn_and_unrelated_nested_calls_remain_unchanged(self) -> None:
        cases = (
            'await tools.respawn_agent({"agent_type":"luna_executor"})',
            'await tools.exec_command({"cmd":"rg router tests"})',
        )
        for source in cases:
            with self.subTest(source=source):
                self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", source)))

    def test_dynamic_nested_tool_access_is_terra_allowed_but_sol_denied(self) -> None:
        source = 'const method = "apply_patch"; await tools[method]({"patch":"x"})'
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", source)))
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "functions.exec", source))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_nested_source_limit_is_deterministic_and_fail_closed(self) -> None:
        canonical = nested_spawn("luna_executor")
        near_limit = canonical + (" " * (ROUTER.MAX_FUNCTIONS_EXEC_SOURCE - len(canonical)))
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", near_limit)))
        self.assertEqual(
            ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", near_limit)),
            ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", near_limit)),
        )
        over_limit = near_limit + " "
        result = ROUTER.handle(pretool("gpt-5.6-terra", "functions.exec", over_limit))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_near_cap_unmatched_braces_scan_within_conservative_cpu_budget(self) -> None:
        # The old per-opening forward search is quadratic on this input. CPU time
        # avoids scheduler noise while leaving a deliberately generous bound.
        source = "{ " * (ROUTER.MAX_FUNCTIONS_EXEC_SOURCE // 2)
        started = time.process_time()
        analysis = ROUTER.analyze_functions_exec(source)
        elapsed = time.process_time() - started
        self.assertFalse(analysis.dynamic_tool_access)
        self.assertLess(elapsed, 1.0)

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
