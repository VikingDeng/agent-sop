from __future__ import annotations

import importlib.util
from concurrent.futures import ThreadPoolExecutor
import hashlib
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
from weighted_routing_policy import close_result_succeeded


def _marked_tool_input(tool_name: str, tool_input: dict | str) -> dict | str:
    if not isinstance(tool_input, dict) or tool_name not in {"Agent", "spawn_agent", "create_agent"}:
        return tool_input
    request = ROUTER.classify_spawn_request(tool_name, tool_input)
    if request is None or request.role is None:
        return tool_input
    marked = dict(tool_input)
    message = str(marked.get("message") or marked.get("prompt") or marked.get("task") or "")
    if "PACKAGE_ID:" in message or "PACKAGE_PHASE:" in message:
        return marked
    phase = {
        "explorer": "map",
        "luna_executor": "initial",
        "focused_worker": "initial",
        "reviewer": "review",
        "risk_reviewer": "review",
        "worker": "correction",
        "terra_debugger": "correction",
        "verifier": "verify",
    }.get(request.role)
    if phase is None:
        return tool_input
    digest = hashlib.sha256(
        json.dumps(tool_input, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:12]
    marked["message"] = f"{message}\nPACKAGE_ID: test-{digest}\nPACKAGE_PHASE: {phase}".strip()
    return marked


def pretool(model: str, tool_name: str, tool_input: dict | str, *, session_id: str = "test-session", turn_id: str | None = "turn-a") -> dict:
    event = {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "model": model,
        "tool_name": tool_name,
        "tool_input": _marked_tool_input(tool_name, tool_input),
    }
    if turn_id is not None:
        event["turn_id"] = turn_id
    return event


def posttool(
    tool_input: dict | str,
    response: object,
    *,
    tool_name: str = "spawn_agent",
    session_id: str = "test-session",
    turn_id: str | None = "turn-a",
) -> dict:
    event = {
        "hook_event_name": "PostToolUse",
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": _marked_tool_input(tool_name, tool_input),
        "tool_response": response,
    }
    if turn_id is not None:
        event["turn_id"] = turn_id
    return event


def nested_spawn(
    role: str,
    *,
    model: str | None = None,
    message: str = "bounded canonical task",
    factory: str = "multi_agent_v1__spawn_agent",
) -> str:
    phase = {
        "explorer": "map",
        "luna_executor": "initial",
        "focused_worker": "initial",
        "reviewer": "review",
        "risk_reviewer": "review",
        "worker": "correction",
        "terra_debugger": "correction",
        "verifier": "verify",
    }.get(role, "initial")
    marked = f"{message}\nPACKAGE_ID: nested-{role}\nPACKAGE_PHASE: {phase}"
    payload = {"agent_type": role, "fork_context": False, "message": marked}
    if model is not None:
        payload["model"] = model
    return f"await tools.{factory}({json.dumps(payload, separators=(',', ':'))});"


class WeightedCostRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state = tempfile.TemporaryDirectory()
        self._environment = patch.dict(
            os.environ, {
                "CODEX_ROUTER_STATE_DIR": self._state.name,
                "CODEX_ROUTER_ENFORCEMENT": "strict",
            }
        )
        self._environment.start()

    def tearDown(self) -> None:
        self._environment.stop()
        self._state.cleanup()

    def test_session_start_injects_objective_and_adaptive_routing(self) -> None:
        result = ROUTER.handle({"hook_event_name": "SessionStart"})
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("25*Sol", context)
        self.assertIn("adaptive advisory", context)

    def test_default_advisory_mode_does_not_block_sol_or_luna_fallback(self) -> None:
        with patch.dict(os.environ, {"CODEX_ROUTER_ENFORCEMENT": "advisory"}):
            sol = ROUTER.handle(pretool("gpt-5.6-sol", "apply_patch", {"patch": "x"}))
            self.assertNotEqual(sol["hookSpecificOutput"].get("permissionDecision"), "deny")

            request = {"agent_type": "luna_executor"}
            unavailable = ROUTER.handle(posttool(
                request,
                "Unknown model `gpt-5.6-luna`; available: gpt-5.6-sol, gpt-5.6-terra",
            ))
            self.assertNotEqual(unavailable.get("decision"), "block")
            self.assertIn("reroute", unavailable["hookSpecificOutput"]["additionalContext"])

            terra = ROUTER.handle(pretool(
                "gpt-5.6-sol",
                "spawn_agent",
                {"agent_type": "worker", "message": "continue the same bounded outcome", "fork_context": False},
            ))
            self.assertNotEqual((terra or {}).get("hookSpecificOutput", {}).get("permissionDecision"), "deny")

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

    def test_unknown_luna_posttool_blocks_and_preserves_wait_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            state_path = Path(directory) / "test-session.json"
            state_path.write_text(json.dumps({"waits": [{"signature": "keep", "time": 1}], "other": "keep"}))
            request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            result = ROUTER.handle(posttool(
                request,
                "Unknown model `gpt-5.6-luna` for spawn_agent. Available models: gpt-5.6-sol, gpt-5.6-terra",
            ))
            self.assertEqual(result["decision"], "block")
            self.assertFalse(result["continue"])
            self.assertIn("Refresh/start", result["reason"])
            state = json.loads(state_path.read_text())
            self.assertEqual(state["waits"][0]["signature"], "keep")
            self.assertEqual(state["other"], "keep")
            marker = Path(directory) / "capability" / "test-session--turn-a.unavailable"
            self.assertTrue(marker.exists())
            self.assertNotIn("luna_capability", state)

    def test_successful_luna_posttool_records_verified_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            self.assertIsNone(ROUTER.handle(posttool(
                request,
                {"agent_id": "luna-child"},
            )))
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.verified").exists())

    def test_task_name_is_a_supported_luna_spawn_success_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            self.assertIsNone(ROUTER.handle(posttool(
                request,
                {"task_name": "/root/bounded-luna-task"},
            )))
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.verified").exists())

    def test_capability_markers_are_monotonic_across_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            success_request = {"agent_type": "luna_executor", "message": "PACKAGE_ID: success\nPACKAGE_PHASE: initial"}
            failure_request = {"agent_type": "luna_executor", "message": "PACKAGE_ID: failure\nPACKAGE_PHASE: initial"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", success_request)))
            success = ROUTER.handle(posttool(success_request, {"agent_id": "child"}))
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", failure_request)))
            failure = ROUTER.handle(posttool(
                failure_request,
                "Unknown model gpt-5.6-luna",
            ))
            self.assertIsNone(success)
            self.assertEqual(failure["decision"], "block")
            capability = Path(directory) / "capability"
            self.assertTrue((capability / "test-session--turn-a.verified").exists())
            self.assertTrue((capability / "test-session--turn-a.unavailable").exists())
            blocked = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "worker", "message": "retry", "fork_context": False,
                },
            ))
            self.assertEqual(blocked["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_unavailable_marker_wins_when_success_arrives_later(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            failure_request = {"agent_type": "luna_executor", "message": "PACKAGE_ID: failure\nPACKAGE_PHASE: initial"}
            late_request = {"agent_type": "luna_executor", "message": "PACKAGE_ID: late\nPACKAGE_PHASE: initial"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", failure_request)))
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", late_request)))
            failure = ROUTER.handle(posttool(
                failure_request, "Unknown model gpt-5.6-luna"
            ))
            success = ROUTER.handle(posttool(
                late_request, {"agent_id": "late-child"}
            ))
            self.assertEqual(failure["decision"], "block")
            self.assertIsNone(success)
            capability = Path(directory) / "capability"
            self.assertTrue((capability / "test-session--turn-a.unavailable").exists())
            self.assertTrue((capability / "test-session--turn-a.verified").exists())
            blocked = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "worker", "message": "retry", "fork_context": False,
                },
            ))
            self.assertEqual(blocked["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_failure_marker_survives_wait_state_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            ROUTER.handle(posttool(request, "Unknown model gpt-5.6-luna"))
            event = pretool("gpt-5.6-sol", "wait_agent", {})
            ROUTER.handle(event)
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.unavailable").exists())

    def test_unknown_luna_is_only_classified_for_positive_luna_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            request = {"agent_type": "reviewer"}
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            self.assertIsNone(ROUTER.handle(posttool(
                request,
                "Unknown model gpt-5.6-luna; reviewer response mentions Luna",
            )))
            self.assertFalse((Path(directory) / "capability").exists())

    def test_outer_functions_exec_only_classifies_canonical_luna_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            source = nested_spawn("luna_executor")
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "functions.exec", source)))
            blocked = ROUTER.handle(posttool(
                source,
                "Unknown model gpt-5.6-luna",
                tool_name="functions.exec",
            ))
            self.assertEqual(blocked["decision"], "block")
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.unavailable").exists())
            self.assertIsNone(ROUTER.handle(posttool(
                'await tools.exec_command({"cmd":"echo Unknown model gpt-5.6-luna"})',
                "Unknown model gpt-5.6-luna",
                tool_name="functions.exec",
                session_id="other-session",
            )))
            self.assertFalse((Path(directory) / "capability" / "other-session--turn-a.unavailable").exists())

    def test_missing_top_level_turn_id_fails_closed_without_poison(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            post = posttool(
                {"agent_type": "luna_executor"},
                {
                    "status": "failed",
                    "message": "Unknown model gpt-5.6-luna",
                    "turn_id": "nested-do-not-use",
                },
                turn_id=None,
            )
            result = ROUTER.handle(post)
            self.assertEqual(result["decision"], "block")
            self.assertFalse((Path(directory) / "capability").exists())
            later = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "worker", "message": "later turn", "fork_context": False,
                }, turn_id="turn-b",
            ))
            self.assertIsNone(later)

    def test_missing_turn_id_blocks_agent_and_canonical_outer_exec_only_for_that_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            agent = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "luna_executor", "message": "bounded", "fork_context": False,
                }, turn_id=None,
            ))
            outer = ROUTER.handle(pretool(
                "gpt-5.6-sol", "functions.exec", nested_spawn("luna_executor"), turn_id=None,
            ))
            self.assertEqual(agent["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(outer["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertFalse((Path(directory) / "capability").exists())
            later = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "reviewer", "message": "review", "fork_context": False,
                }, turn_id="turn-b",
            ))
            self.assertIsNone(later)

    def test_posttool_matcher_covers_outer_functions_exec(self) -> None:
        hooks = json.loads((ROOT / "codex/hooks/hooks.json").read_text())
        matcher = hooks["hooks"]["PostToolUse"][0]["matcher"]
        self.assertIn("functions\\.exec", matcher)
        self.assertIn("close_agent", matcher)

    def test_strict_spawn_result_matrix_is_fail_closed_and_serializable(self) -> None:
        cases = (
            ({"agent_id": "child"}, True),
            ('{"thread_id":"thread-1"}', True),
            ({"task_name": "/root/bounded-task"}, True),
            ({"agent_id": ""}, False),
            ({"nickname": None}, False),
            ({"nickname": "not-a-documented-standalone-id"}, False),
            ({"isError": True, "agent_id": "child"}, False),
            ({"error": "failed", "agent_id": "child"}, False),
            ({"status": "failed", "agent_id": "child"}, False),
            ("{malformed", False),
            ("", False),
        )
        for response, expected in cases:
            with self.subTest(response=response):
                self.assertEqual(
                    ROUTER.classify_spawn_result(response, luna_role="luna_executor").succeeded,
                    expected,
                )

    def test_unknown_luna_result_matrix_inspects_only_error_evidence(self) -> None:
        cases = (
            ({"task_name": "gpt-5.6-luna-unavailable-repro"}, True, False),
            ({
                "message": "Unknown model gpt-5.6-luna",
                "task_name": "gpt-5.6-luna-unavailable-repro",
            }, True, False),
            ({
                "error": "Unknown model gpt-5.6-luna",
                "task_name": "gpt-5.6-luna-unavailable-repro",
            }, False, True),
            ({
                "error": "spawn failed",
                "message": "Unknown model gpt-5.6-luna",
                "task_name": "bounded",
            }, False, False),
            ({
                "status": "failed",
                "message": "gpt-5.6-luna is unavailable",
                "task_name": "bounded",
            }, False, True),
            ({
                "isError": True,
                "content": [{"type": "text", "text": "Unknown model gpt-5.6-luna"}],
                "task_name": "bounded",
            }, False, True),
            ({
                "content": [{"type": "error", "text": "gpt-5.6-luna not found"}],
                "task_name": "bounded",
            }, False, True),
            ("Unknown model gpt-5.6-luna", False, True),
        )
        for response, succeeded, unknown_luna in cases:
            with self.subTest(response=response):
                result = ROUTER.classify_spawn_result(response, luna_role="luna_executor")
                self.assertEqual(result.succeeded, succeeded)
                self.assertEqual(result.unknown_luna, unknown_luna)

    def test_thread_limit_is_distinct_and_allows_only_one_same_spawn_retry(self) -> None:
        request = {
            "agent_type": "luna_executor",
            "message": "bounded implementation",
            "fork_context": False,
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            result = ROUTER.classify_spawn_result(
                "agent-thread-limit: maximum concurrent threads reached",
                luna_role="luna_executor",
            )
            self.assertTrue(result.thread_limit)
            self.assertFalse(result.unknown_luna)
            self.assertTrue(ROUTER.classify_spawn_result(
                {"status": "agent-thread-limit"}, luna_role="luna_executor"
            ).thread_limit)
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            first = ROUTER.handle(posttool(request, "agent-thread-limit: maximum concurrent threads reached"))
            self.assertNotIn("decision", first)
            self.assertNotIn("continue", first)
            self.assertIn("not Luna model unavailability", first["hookSpecificOutput"]["additionalContext"])
            self.assertFalse((Path(directory) / "capability" / "test-session--turn-a.unavailable").exists())
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            second = ROUTER.handle(posttool(request, "agent-thread-limit: maximum concurrent threads reached"))
            self.assertNotIn("decision", second)
            self.assertIn("agent-thread-limit", second["hookSpecificOutput"]["additionalContext"])
            denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request))
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("locked after thread-limit recovery", denied["hookSpecificOutput"]["permissionDecisionReason"])
            state = json.loads((Path(directory) / "test-session.json").read_text())
            self.assertEqual(len(state["thread_limit_packages"]), 1)
            package_state = next(iter(state["thread_limit_packages"].values()))
            self.assertEqual(package_state["status"], "locked")
            self.assertEqual(package_state["retry_count"], 1)
            self.assertRegex(package_state["signature"], r"^[0-9a-f]{64}$")
            self.assertNotIn("bounded implementation", json.dumps(state))

    def test_thread_limit_recovery_denies_changed_signature_dimensions(self) -> None:
        original = {
            "agent_type": "luna_executor",
            "model": "gpt-5.6-luna",
            "fork_context": False,
            "message": "bounded\nPACKAGE_ID: recovery-package\nPACKAGE_PHASE: initial",
        }
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        first = ROUTER.handle(posttool(original, "agent-thread-limit"))
        self.assertIn("now in recovery", first["hookSpecificOutput"]["additionalContext"])

        changed_requests = (
            {**original, "message": original["message"].replace("bounded", "changed message")},
            {**original, "model": "gpt-luna-alternate"},
            {
                **original,
                "agent_type": "worker",
                "model": "gpt-5.6-terra",
                "message": (
                    "bounded\nPACKAGE_ID: recovery-package\nPACKAGE_PHASE: initial\n"
                    "LUNA_ELIGIBLE=no(semantic pressure)"
                ),
            },
            {**original, "message": original["message"].replace("initial", "correction")},
        )
        for index, changed in enumerate(changed_requests):
            with self.subTest(index=index):
                denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", changed))
                self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("exact same-signature retry", denied["hookSpecificOutput"]["permissionDecisionReason"])

        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        retry_failure = ROUTER.handle(posttool(original, {"status": "failed"}))
        self.assertIn("locked against further spawns", retry_failure["hookSpecificOutput"]["additionalContext"])
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_denied_altered_input_does_not_consume_valid_identical_retry(self) -> None:
        original = {
            "agent_type": "luna_executor",
            "model": "gpt-5.6-luna",
            "fork_context": False,
            "message": "bounded\nPACKAGE_ID: retry-ordering\nPACKAGE_PHASE: initial",
        }
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        ROUTER.handle(posttool(original, "agent-thread-limit"))

        altered = {**original, "fork_context": True}
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", altered))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("do not fork the full parent history", denied["hookSpecificOutput"]["permissionDecisionReason"])

        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        retry_marker = ROUTER._thread_limit_retry_marker("test-session", "retry-ordering")
        self.assertTrue(retry_marker.exists())

    def test_final_recovery_commit_failure_rolls_back_package_reservation(self) -> None:
        original = {
            "agent_type": "luna_executor",
            "fork_context": False,
            "message": "bounded\nPACKAGE_ID: retry-rollback\nPACKAGE_PHASE: initial",
        }
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        ROUTER.handle(posttool(original, "agent-thread-limit"))

        with patch.object(ROUTER, "_commit_thread_limit_preflight", return_value="forced commit denial"):
            denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))

    def test_new_package_after_recovery_requires_explicit_recontract_evidence(self) -> None:
        original = {
            "agent_type": "verifier",
            "fork_context": False,
            "message": "verify\nPACKAGE_ID: old-package\nPACKAGE_PHASE: verify",
        }
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        ROUTER.handle(posttool(original, "agent-thread-limit"))

        relabeled = {
            "agent_type": "verifier",
            "fork_context": False,
            "message": "verify\nPACKAGE_ID: new-package\nPACKAGE_PHASE: verify",
        }
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", relabeled))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("explicit re-contract evidence", denied["hookSpecificOutput"]["permissionDecisionReason"])

        relabeled["message"] += (
            "\nRECONTRACT_OLD_PACKAGE_ID: old-package"
            "\nRECONTRACT_NEW_PACKAGE_ID: new-package"
            f"\nRECONTRACT_OLD_CONTRACT_SHA256: {'a' * 64}"
            f"\nRECONTRACT_NEW_CONTRACT_SHA256: {'b' * 64}"
            "\nRECONTRACT_REASON: acceptance contract materially changed"
            "\nRECONTRACT_SCOPE_ACCEPTANCE_DELTA: added one bounded file and one new assertion"
        )
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", relabeled)))

    def test_downstream_denied_recontract_does_not_mutate_lineage(self) -> None:
        original = {
            "agent_type": "verifier",
            "fork_context": False,
            "message": "verify\nPACKAGE_ID: lineage-old\nPACKAGE_PHASE: verify",
        }
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", original)))
        ROUTER.handle(posttool(original, "agent-thread-limit"))

        evidence = (
            "verify\nPACKAGE_ID: lineage-new\nPACKAGE_PHASE: verify"
            "\nRECONTRACT_OLD_PACKAGE_ID: lineage-old"
            "\nRECONTRACT_NEW_PACKAGE_ID: lineage-new"
            f"\nRECONTRACT_OLD_CONTRACT_SHA256: {'a' * 64}"
            f"\nRECONTRACT_NEW_CONTRACT_SHA256: {'b' * 64}"
            "\nRECONTRACT_REASON: acceptance contract materially changed"
            "\nRECONTRACT_SCOPE_ACCEPTANCE_DELTA: added one bounded assertion"
        )
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "agent_type": "verifier",
            "fork_context": True,
            "message": evidence,
        }))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        state = json.loads((Path(self._state.name) / "test-session.json").read_text())
        self.assertEqual(state["thread_limit_packages"]["lineage-old"]["status"], "recovery")

        marker_free = {
            "agent_type": "verifier",
            "fork_context": False,
            "message": "verify\nPACKAGE_ID: lineage-new\nPACKAGE_PHASE: verify",
        }
        denied_retry = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", marker_free))
        self.assertEqual(denied_retry["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("explicit re-contract evidence", denied_retry["hookSpecificOutput"]["permissionDecisionReason"])

    def test_one_successful_risk_reviewer_is_the_session_maximum(self) -> None:
        request = {
            "agent_type": "risk_reviewer",
            "message": "HIGH_RISK_TRIGGER: concurrency\nEVIDENCE_PACK: focused diff",
            "fork_context": False,
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            self.assertIsNone(ROUTER.handle(posttool(request, {"agent_id": "risk-child"})))
            denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request))
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertRegex(
                denied["hookSpecificOutput"]["permissionDecisionReason"],
                r"one allowed Sol risk_reviewer|review budget is already committed",
            )

    def test_close_result_uses_documented_previous_status_schema(self) -> None:
        successful = (
            {"previous_status": "pending_init"},
            {"previous_status": "running"},
            {"previous_status": "interrupted"},
            {"previous_status": "shutdown"},
            {"previous_status": {"completed": "done"}},
            {"previous_status": {"errored": "task failed"}},
        )
        failed = (
            {"previous_status": "not_found"},
            {"previous_status": "closed"},
            {"previous_status": {}},
            {"previous_status": {"unexpected": "value"}},
            {"previous_status": "running", "error": "tool failure"},
            {"isError": True, "previous_status": "shutdown"},
            None,
        )
        for result in successful:
            with self.subTest(success=result):
                self.assertTrue(close_result_succeeded(result))
                self.assertTrue(close_result_succeeded(json.dumps(result)))
        for result in failed:
            with self.subTest(failure=result):
                self.assertFalse(close_result_succeeded(result))

    def test_risk_reviewer_reservation_is_atomic_and_failed_spawn_releases_it(self) -> None:
        request = {
            "agent_type": "risk_reviewer",
            "message": (
                "HIGH_RISK_TRIGGER: concurrency\nEVIDENCE_PACK: focused diff\n"
                "PACKAGE_ID: concurrent-risk\nPACKAGE_PHASE: review"
            ),
            "fork_context": False,
        }
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda _: ROUTER.handle(pretool(
                    "gpt-5.6-sol", "spawn_agent", request, session_id="risk-race"
                )),
                range(2),
            ))
        self.assertEqual(sum(result is None for result in results), 1)
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertIsNone(ROUTER.handle(posttool(
            request, {"status": "failed"}, session_id="risk-race"
        )))
        self.assertIsNone(ROUTER.handle(pretool(
            "gpt-5.6-sol", "spawn_agent", request, session_id="risk-race"
        )))
        self.assertIsNone(ROUTER.handle(posttool(
            request, {"agent_id": "risk-child"}, session_id="risk-race"
        )))
        denied = ROUTER.handle(pretool(
            "gpt-5.6-sol",
            "spawn_agent",
            {**request, "message": request["message"].replace("concurrent-risk", "second-risk")},
            session_id="risk-race",
        ))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_package_phase_budget_is_global_across_roles_and_packages_are_independent(self) -> None:
        def request(role: str, package: str, phase: str) -> dict:
            return {
                "agent_type": role,
                "fork_context": False,
                "message": f"bounded\nPACKAGE_ID: {package}\nPACKAGE_PHASE: {phase}",
            }

        initial = request("luna_executor", "package-a", "initial")
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", initial)))
        self.assertIsNone(ROUTER.handle(posttool(initial, {"agent_id": "initial"})))

        terra_initial = request("worker", "package-a", "initial")
        terra_initial["message"] += "\nLUNA_ELIGIBLE=no(semantic cross-file pressure)"
        denied_initial = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", terra_initial))
        self.assertEqual(denied_initial["hookSpecificOutput"]["permissionDecision"], "deny")

        correction = request("worker", "package-a", "correction")
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", correction)))
        self.assertIsNone(ROUTER.handle(posttool(correction, {"agent_id": "correction"})))
        second_correction = request("luna_executor", "package-a", "correction")
        denied_correction = ROUTER.handle(pretool(
            "gpt-5.6-sol", "spawn_agent", second_correction
        ))
        self.assertEqual(denied_correction["hookSpecificOutput"]["permissionDecision"], "deny")

        review = request("reviewer", "package-a", "review")
        re_review = request("reviewer", "package-a", "re_review")
        for spawn in (review, re_review):
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", spawn)))
            self.assertIsNone(ROUTER.handle(posttool(spawn, {"agent_id": spawn["message"]})))
        denied_re_review = ROUTER.handle(pretool(
            "gpt-5.6-sol", "spawn_agent", re_review
        ))
        self.assertEqual(denied_re_review["hookSpecificOutput"]["permissionDecision"], "deny")

        independent = request("luna_executor", "package-b", "initial")
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", independent)))

    def test_terra_can_be_the_single_initial_only_with_luna_ineligible_reason(self) -> None:
        def terra_request(role: str, package: str, reason: str | None) -> dict:
            message = f"bounded\nPACKAGE_ID: {package}\nPACKAGE_PHASE: initial"
            if reason is not None:
                message += f"\nLUNA_ELIGIBLE=no({reason})"
            return {"agent_type": role, "fork_context": False, "message": message}

        for role in ("worker", "terra_debugger"):
            with self.subTest(role=role):
                request = terra_request(role, f"terra-{role}", "semantic pressure")
                self.assertIsNone(ROUTER.handle(pretool(
                    "gpt-5.6-sol", "spawn_agent", request, session_id=f"session-{role}"
                )))

        for index, reason in enumerate((None, "", "   ")):
            with self.subTest(reason=reason):
                request = terra_request("worker", f"missing-{index}", reason)
                denied = ROUTER.handle(pretool(
                    "gpt-5.6-sol", "spawn_agent", request, session_id=f"missing-{index}"
                ))
                self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("LUNA_ELIGIBLE=no(reason)", denied["hookSpecificOutput"]["permissionDecisionReason"])

    def test_successful_initial_blocks_every_later_initial_role(self) -> None:
        first = {
            "agent_type": "worker",
            "fork_context": False,
            "message": (
                "bounded\nPACKAGE_ID: single-initial\nPACKAGE_PHASE: initial\n"
                "LUNA_ELIGIBLE=no(semantic pressure)"
            ),
        }
        self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", first)))
        self.assertIsNone(ROUTER.handle(posttool(first, {"agent_id": "terra-initial"})))
        for role in ("focused_worker", "luna_executor", "worker", "terra_debugger"):
            message = "bounded\nPACKAGE_ID: single-initial\nPACKAGE_PHASE: initial"
            if role in {"worker", "terra_debugger"}:
                message += "\nLUNA_ELIGIBLE=no(still semantic)"
            with self.subTest(role=role):
                denied = ROUTER.handle(pretool(
                    "gpt-5.6-sol", "spawn_agent",
                    {"agent_type": role, "fork_context": False, "message": message},
                ))
                self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("initial budget is already committed", denied["hookSpecificOutput"]["permissionDecisionReason"])

    def test_missing_package_markers_fail_closed(self) -> None:
        result = ROUTER.handle({
            "hook_event_name": "PreToolUse",
            "session_id": "missing-package",
            "turn_id": "turn-a",
            "model": "gpt-5.6-sol",
            "tool_name": "spawn_agent",
            "tool_input": {
                "agent_type": "luna_executor",
                "message": "bounded",
                "fork_context": False,
            },
        })
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("PACKAGE_ID", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_ordinary_reviewer_is_terra_and_sol_is_not_a_default_child(self) -> None:
        self.assertEqual(ROUTER.ROLE_MODEL_FAMILIES["reviewer"], "terra")
        self.assertEqual(ROUTER.ROLE_MODEL_FAMILIES["risk_reviewer"], "sol")
        denied = ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", {
            "message": "ordinary review",
            "fork_context": False,
        }))
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_task_name_luna_text_marks_success_but_error_evidence_marks_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            success_request = {"agent_type": "luna_executor"}
            failure_request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", success_request, session_id="success-session"
            )))
            success = ROUTER.handle(posttool(
                success_request,
                {"task_name": "gpt-5.6-luna-unavailable-repro"},
                session_id="success-session",
            ))
            self.assertIsNone(ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", failure_request, session_id="failure-session"
            )))
            failure = ROUTER.handle(posttool(
                failure_request,
                {
                    "error": "Unknown model gpt-5.6-luna",
                    "task_name": "gpt-5.6-luna-unavailable-repro",
                },
                session_id="failure-session",
            ))
            capability = Path(directory) / "capability"
            self.assertIsNone(success)
            self.assertEqual(failure["decision"], "block")
            self.assertTrue((capability / "success-session--turn-a.verified").exists())
            self.assertFalse((capability / "success-session--turn-a.unavailable").exists())
            self.assertTrue((capability / "failure-session--turn-a.unavailable").exists())

    def test_request_aliases_and_unknown_luna_model_share_lifecycle_classification(self) -> None:
        cases = (
            ("agent_type", "luna_executor"),
            ("subagent_type", "luna_executor"),
            ("role", "luna_executor"),
            ("name", "luna_executor"),
        )
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            for index, (field, value) in enumerate(cases):
                with self.subTest(field=field, value=value):
                    request = {field: value, "model": "gpt-5.6-luna", "fork_context": False}
                    pre = ROUTER.handle(pretool(
                        "gpt-5.6-sol", "spawn_agent", request,
                        session_id=f"alias-{index}",
                    ))
                    self.assertIsNone(pre)
                    post = ROUTER.handle(posttool(
                        request,
                        "Unknown model gpt-5.6-luna",
                        session_id=f"alias-{index}",
                    ))
                    self.assertEqual(post["decision"], "block")
                    self.assertTrue((
                        Path(directory) / "capability" / f"alias-{index}--turn-a.unavailable"
                    ).exists())

    def test_conflicting_request_aliases_fail_closed_without_markers(self) -> None:
        cases = (
            ({
                "agent_type": "reviewer",
                "role": "luna_executor",
                "model": "gpt-5.6-luna",
                "fork_context": False,
            }, "identity aliases disagree"),
            ({
                "agent_type": "luna_executor",
                "model": "gpt-5.6-luna",
                "model_name": "gpt-5.6-sol",
                "fork_context": False,
            }, "model aliases disagree"),
        )
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            for index, (request, reason) in enumerate(cases):
                with self.subTest(request=request):
                    session_id = f"conflict-{index}"
                    pre = ROUTER.handle(pretool(
                        "gpt-5.6-sol", "spawn_agent", request, session_id=session_id,
                    ))
                    post = ROUTER.handle(posttool(
                        request,
                        {"task_name": "/root/ambiguous-task"},
                        session_id=session_id,
                    ))
                    self.assertIn(reason, pre["hookSpecificOutput"]["permissionDecisionReason"])
                    self.assertEqual(post["decision"], "block")
                    self.assertIn(reason, post["reason"])
                    self.assertFalse((Path(directory) / "capability").exists())

    def test_identical_request_aliases_remain_valid_across_pre_and_posttool(self) -> None:
        request = {
            "agent_type": " luna_executor ",
            "subagent_type": "LUNA_EXECUTOR",
            "role": "luna_executor",
            "name": "luna_executor",
            "model": "gpt-5.6-luna",
            "model_name": " GPT-5.6-LUNA ",
            "fork_context": False,
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            self.assertIsNone(ROUTER.handle(pretool("gpt-5.6-sol", "spawn_agent", request)))
            self.assertIsNone(ROUTER.handle(posttool(
                request, {"task_name": "/root/duplicate-alias-task"},
            )))
            self.assertTrue((
                Path(directory) / "capability" / "test-session--turn-a.verified"
            ).exists())

    def test_same_turn_execution_escalation_is_blocked_but_review_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            failed_request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", failed_request
            )))
            ROUTER.handle(posttool(
                failed_request,
                "Unknown model gpt-5.6-luna; available models are gpt-5.6-sol and gpt-5.6-terra",
            ))
            blocked = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "worker", "message": "escalate", "fork_context": False,
                }, turn_id="turn-a",
            ))
            reviewer = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "reviewer", "message": "review", "fork_context": False,
                }, turn_id="turn-a",
            ))
            direct_sol = ROUTER.handle(pretool(
                "gpt-5.6-sol", "apply_patch", {"patch": "x"}, turn_id="turn-a",
            ))
            self.assertEqual(blocked["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("do not escalate to Terra", blocked["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertIsNone(reviewer)
            self.assertEqual(direct_sol["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_luna_unavailable_state_does_not_block_a_later_turn(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            failed_request = {"agent_type": "luna_executor"}
            self.assertIsNone(ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", failed_request
            )))
            ROUTER.handle(posttool(
                failed_request,
                "Unknown model gpt-5.6-luna",
            ))
            later = ROUTER.handle(pretool(
                "gpt-5.6-sol", "spawn_agent", {
                    "agent_type": "worker", "message": "new task", "fork_context": False,
                }, turn_id="turn-b",
            ))
            self.assertIsNone(later)

    def test_malformed_posttool_response_fails_closed_without_poisoning_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            missing = ROUTER.handle({
                "hook_event_name": "PostToolUse",
                "session_id": "test-session",
                "turn_id": "turn-a",
                "tool_name": "spawn_agent",
                "tool_input": {"agent_type": "luna_executor"},
            })
            irrelevant = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"}, {"unexpected": [object(), None]},
            ))
            self.assertEqual(missing["decision"], "block")
            self.assertIsNone(irrelevant)
            self.assertFalse((Path(directory) / "test-session.json").exists())
            self.assertFalse((Path(directory) / "capability").exists())

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

    def test_terra_debugger_subagent_context_is_hypothesis_first_and_adaptive(self) -> None:
        result = ROUTER.handle({
            "hook_event_name": "SubagentStart",
            "agent_type": "terra_debugger",
        })
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("hypothesis-first", context)
        self.assertIn("Adapt tools or implementation paths explicitly", context)
        self.assertIn("outcome contract", context)
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
        for index, source in enumerate(cases):
            with self.subTest(source=source):
                self.assertIsNone(ROUTER.handle(pretool(
                    "gpt-5.6-sol", "functions.exec", source, session_id=f"nested-{index}"
                )))

    def test_canonical_nested_agent_payload_rejects_policy_errors(self) -> None:
        cases = (
            nested_spawn("luna_executor", model="gpt-5.6-terra"),
            nested_spawn("missing_role"),
            nested_spawn("luna_executor").replace('"agent_type":"luna_executor",', ""),
            nested_spawn("luna_executor").replace('"fork_context":false', '"fork_context":true'),
            nested_spawn("luna_executor").replace('"fork_context":false,', ""),
            nested_spawn("luna_executor").replace(
                '"message":"bounded canonical task\\nPACKAGE_ID: nested-luna_executor\\nPACKAGE_PHASE: initial"',
                '"message":""',
            ),
            nested_spawn("luna_executor").replace(
                '"message":"bounded canonical task\\nPACKAGE_ID: nested-luna_executor\\nPACKAGE_PHASE: initial"',
                '"message":selectedMessage',
            ),
            nested_spawn("luna_executor").replace(
                '"message":"bounded canonical task\\nPACKAGE_ID: nested-luna_executor\\nPACKAGE_PHASE: initial"',
                '"unknown":"x","message":"bounded canonical task\\nPACKAGE_ID: nested-luna_executor\\nPACKAGE_PHASE: initial"',
            ),
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
