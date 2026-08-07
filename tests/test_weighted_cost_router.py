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


def pretool(model: str, tool_name: str, tool_input: dict | str, *, session_id: str = "test-session", turn_id: str | None = "turn-a") -> dict:
    event = {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "model": model,
        "tool_name": tool_name,
        "tool_input": tool_input,
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
        "tool_input": tool_input,
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

    def test_unknown_luna_posttool_blocks_and_preserves_wait_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            state_path = Path(directory) / "test-session.json"
            state_path.write_text(json.dumps({"waits": [{"signature": "keep", "time": 1}], "other": "keep"}))
            result = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
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
            self.assertIsNone(ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
                {"agent_id": "luna-child"},
            )))
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.verified").exists())

    def test_task_name_is_a_supported_luna_spawn_success_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            self.assertIsNone(ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
                {"task_name": "/root/bounded-luna-task"},
            )))
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.verified").exists())

    def test_capability_markers_are_monotonic_across_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            success = ROUTER.handle(posttool({"agent_type": "luna_executor"}, {"agent_id": "child"}))
            failure = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
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
            failure = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"}, "Unknown model gpt-5.6-luna"
            ))
            success = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"}, {"agent_id": "late-child"}
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
            ROUTER.handle(posttool({"agent_type": "luna_executor"}, "Unknown model gpt-5.6-luna"))
            event = pretool("gpt-5.6-sol", "wait_agent", {})
            ROUTER.handle(event)
            self.assertTrue((Path(directory) / "capability" / "test-session--turn-a.unavailable").exists())

    def test_unknown_luna_is_only_classified_for_positive_luna_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            self.assertIsNone(ROUTER.handle(posttool(
                {"agent_type": "reviewer"},
                "Unknown model gpt-5.6-luna; reviewer response mentions Luna",
            )))
            self.assertFalse((Path(directory) / "capability").exists())

    def test_outer_functions_exec_only_classifies_canonical_luna_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            blocked = ROUTER.handle(posttool(
                nested_spawn("luna_executor"),
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

    def test_task_name_luna_text_marks_success_but_error_evidence_marks_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"CODEX_ROUTER_STATE_DIR": directory}
        ):
            success = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
                {"task_name": "gpt-5.6-luna-unavailable-repro"},
                session_id="success-session",
            ))
            failure = ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
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
            ("name", "custom-worker"),
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
            ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
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
            ROUTER.handle(posttool(
                {"agent_type": "luna_executor"},
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
