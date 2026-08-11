from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_codex_session.py"
SPEC = importlib.util.spec_from_file_location("audit_codex_session", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def record(record_type: str, payload: dict, *, add_package_markers: bool = True) -> str:
    if (
        add_package_markers
        and record_type == "response_item"
        and payload.get("type") == "function_call"
        and payload.get("name") in {"Agent", "spawn_agent", "create_agent"}
    ):
        payload = dict(payload)
        try:
            arguments = json.loads(payload.get("arguments", "{}"))
        except (TypeError, json.JSONDecodeError):
            arguments = None
        if isinstance(arguments, dict):
            role = next(
                (arguments.get(key) for key in ("agent_type", "subagent_type", "role", "name") if arguments.get(key)),
                None,
            )
            phases = {
                "explorer": "map",
                "luna_executor": "initial",
                "focused_worker": "initial",
                "reviewer": "review",
                "risk_reviewer": "review",
                "sol_architect": "initial",
                "worker": "correction",
                "terra_debugger": "correction",
                "verifier": "verify",
            }
            if role in phases:
                message = str(arguments.get("message") or arguments.get("prompt") or arguments.get("task") or "")
                if "PACKAGE_ID:" not in message and "PACKAGE_PHASE:" not in message:
                    package = str(payload.get("call_id") or "fixture").replace("_", "-")
                    arguments["message"] = (
                        f"{message}\nPACKAGE_ID: test-{package}\nPACKAGE_PHASE: {phases[role]}"
                    ).strip()
                    payload["arguments"] = json.dumps(arguments)
    return json.dumps({"type": record_type, "payload": payload}) + "\n"


def usage(total: int, cached: int = 0) -> dict:
    return {
        "type": "token_count",
        "info": {"total_token_usage": {
            "input_tokens": total - 10,
            "cached_input_tokens": cached,
            "cache_write_input_tokens": 0,
            "output_tokens": 10,
            "reasoning_output_tokens": 2,
            "total_tokens": total,
        }},
    }


def successful_spawn(role: str, call_id: str = "spawn") -> str:
    return "".join([
        record("response_item", {
            "type": "function_call",
            "name": "spawn_agent",
            "call_id": call_id,
            "arguments": json.dumps({"agent_type": role}),
            "turn_id": "turn-a",
        }),
        record("response_item", {
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps({"agent_id": "child"}),
            "turn_id": "turn-a",
        }),
        record("response_item", {
            "type": "function_call",
            "name": "multi_agent_v1__close_agent",
            "call_id": f"close-{call_id}",
            "arguments": json.dumps({"target": "child"}),
            "turn_id": "turn-a",
        }),
        record("response_item", {
            "type": "function_call_output",
            "call_id": f"close-{call_id}",
            "output": json.dumps({"previous_status": {"completed": "done"}}),
            "turn_id": "turn-a",
        }),
    ])


def spawn_and_close(
    role: str,
    *,
    call_id: str = "spawn",
    child_id: str = "child",
    close_output: object | None = None,
    include_close_output: bool = True,
) -> str:
    output = {"previous_status": {"completed": "done"}} if close_output is None else close_output
    lines = [
        record("response_item", {
            "type": "function_call",
            "name": "spawn_agent",
            "call_id": call_id,
            "arguments": json.dumps({"agent_type": role}),
            "turn_id": "turn-a",
        }),
        record("response_item", {
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps({"agent_id": child_id}),
            "turn_id": "turn-a",
        }),
        record("response_item", {
            "type": "function_call",
            "name": "multi_agent_v1__close_agent",
            "call_id": f"close-{call_id}",
            "arguments": json.dumps({"target": child_id}),
            "turn_id": "turn-a",
        }),
    ]
    if include_close_output:
        lines.append(record("response_item", {
            "type": "function_call_output",
            "call_id": f"close-{call_id}",
            "output": json.dumps(output),
            "turn_id": "turn-a",
        }))
    return "".join(lines)


class AuditCodexSessionTests(unittest.TestCase):
    def write_log(
        self,
        root: Path,
        name: str,
        thread_id: str,
        model: str,
        totals: list[int],
        parent: str | None = None,
        role: str | None = None,
        extra: str = "",
        last_message: str = "",
        cwd: str = "",
    ) -> Path:
        payload = {"id": thread_id, "session_id": "root" if parent else thread_id}
        if parent:
            payload["parent_thread_id"] = parent
        if role:
            payload["agent_role"] = role
        lines = [
            record("session_meta", payload),
            record("turn_context", {"model": model, **({"cwd": cwd} if cwd else {})}),
            *(record("event_msg", usage(total)) for total in totals),
            extra,
            record("event_msg", usage(totals[-1])),
            record("event_msg", {"type": "task_complete", "last_agent_message": last_message}),
        ]
        path = root / f"{name}.jsonl"
        path.write_text("".join(lines))
        return path

    def test_tree_cost_uses_sol_terra_luna_weights(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100, 250])
            self.write_log(root, "luna", "child-luna", "gpt-5.6-luna", [500], "root", "luna_executor")
            self.write_log(root, "terra", "child-terra", "gpt-5.6-terra", [200], "root", "worker")

            report = AUDIT.audit_session_tree(str(parent), root)

            self.assertEqual(report["total_tokens"], 950)
            self.assertEqual(report["weighted_cost_units"], 8_750)
            self.assertEqual(report["subagent_roles"], {"luna_executor": 1, "worker": 1})
            self.assertNotIn("no Terra or Luna tokens were observed", report["routing_violations"])

    def test_sol_architect_is_canonical_sol_role_in_session_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(
                root,
                "parent",
                "root",
                "gpt-5.6-terra",
                [100],
                extra=successful_spawn("sol_architect"),
            )
            self.write_log(
                root,
                "architect",
                "child-architect",
                "gpt-5.6-sol",
                [50],
                "root",
                "sol_architect",
            )

            report = AUDIT.audit_session_tree(str(parent), root)

            self.assertEqual(AUDIT.ROLE_MODEL_FAMILIES["sol_architect"], "sol")
            self.assertEqual(report["subagent_roles"], {"sol_architect": 1})
            self.assertEqual(report["family_totals"]["sol"]["total_tokens"], 50)
            findings = "\n".join(report["completeness_violations"])
            self.assertNotIn("unknown agent_role", findings)
            self.assertNotIn("noncanonical role", findings)

    def test_completed_single_model_root_reports_delivery_and_routing_advisories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(
                root,
                "parent",
                "root",
                "gpt-5.6-luna",
                [1_000_000],
                last_message="Implemented the repository change.",
                cwd=str(ROOT),
            )
            report = AUDIT.audit_session_tree(str(path), root, enforcement_mode="advisory")
            self.assertTrue(report["delivery_report_findings"])
            self.assertTrue(any("evidence/commands" in item for item in report["delivery_report_findings"]))
            self.assertTrue(any("single-model" in item for item in report["routing_observations"]))
            self.assertEqual(report["cost_status"], "complete")

    def test_completed_chinese_root_report_is_semantically_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(
                root,
                "parent",
                "root",
                "gpt-5.6-luna",
                [100],
                last_message="结果：已完成。证据：测试和命令均通过，退出码为 0。复核：未运行。路由/WCU：Luna，成本可追溯。风险：无。交付：Git 状态不适用。",
            )
            report = AUDIT.audit_session_tree(str(path), root, enforcement_mode="advisory")
            self.assertEqual(report["delivery_report_findings"], [])

    def test_completed_non_git_english_root_report_with_code_words_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(
                root,
                "parent",
                "root",
                "gpt-5.6-luna",
                [100],
                last_message=(
                    "Outcome: completed code change. Evidence: tests and commands passed. "
                    "Review: not run. Routing/WCU: Luna. Risks: none."
                ),
                cwd=directory,
            )
            report = AUDIT.audit_session_tree(str(path), root, enforcement_mode="advisory")
            self.assertEqual(report["delivery_report_findings"], [])

    def test_advisory_accepts_concise_outcome_and_evidence_but_strict_requires_detail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(
                root,
                "parent",
                "root",
                "gpt-5.6-luna",
                [100],
                last_message="Completed the requested change. Tests passed.",
                cwd=str(ROOT),
            )
            advisory = AUDIT.audit_session_tree(str(path), root, enforcement_mode="advisory")
            strict = AUDIT.audit_session_tree(str(path), root, enforcement_mode="strict")
            self.assertEqual(advisory["delivery_report_findings"], [])
            self.assertTrue(any(
                "review disposition" in finding and "routing/WCU" in finding
                for finding in strict["delivery_report_findings"]
            ))

    def test_single_model_observation_stays_quiet_below_one_million_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(
                root,
                "parent",
                "root",
                "gpt-5.6-luna",
                [999_999],
                last_message="Implemented the repository change.",
            )
            report = AUDIT.audit_session_tree(str(path), root, enforcement_mode="advisory")
            self.assertFalse(any("single-model" in item for item in report["routing_observations"]))

    def test_model_switch_assigns_only_increment_to_new_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "switch.jsonl"
            path.write_text("".join([
                record("session_meta", {"id": "switch", "session_id": "switch"}),
                record("turn_context", {"model": "gpt-5.6-sol"}),
                record("event_msg", usage(100)),
                record("turn_context", {"model": "gpt-5.6-terra"}),
                record("event_msg", usage(150)),
                record("event_msg", {"type": "task_complete"}),
            ]))
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["model_totals"]["gpt-5.6-sol"]["total_tokens"], 100)
            self.assertEqual(report["model_totals"]["gpt-5.6-terra"]["total_tokens"], 50)
            self.assertEqual(report["weighted_cost_units"], 3_000)

    def test_detects_large_outputs_and_all_sol_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "call-1",
                    "input": "{}",
                }),
                record("response_item", {
                    "type": "custom_tool_call_output",
                    "call_id": "call-1",
                    "output": "x" * 101,
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root, large_output_chars=100)
            self.assertEqual(len(report["large_outputs"]), 1)
            self.assertTrue(any("no Terra or Luna" in item for item in report["routing_observations"]))

    def test_unknown_model_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(root, "parent", "root", "future-model", [100])
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertTrue(any("unknown model family" in item for item in report["routing_violations"]))

    def test_relative_rollout_path_is_not_counted_twice(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            path = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100])
            report = AUDIT.audit_session_tree(os.path.relpath(path), root.resolve())
            self.assertEqual(report["session_count"], 1)
            self.assertEqual(report["total_tokens"], 100)

    def test_archived_root_discovers_archived_and_active_children(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            sessions = base / "sessions"
            archived = base / "archived_sessions"
            sessions.mkdir()
            archived.mkdir()
            parent = self.write_log(archived, "parent", "root", "gpt-5.6-sol", [100])
            self.write_log(archived, "archived-child", "child-a", "gpt-5.6-luna", [200], "root", "verifier")
            self.write_log(sessions, "active-child", "child-b", "gpt-5.6-terra", [300], "root", "reviewer")
            report = AUDIT.audit_session_tree(str(parent), sessions)
            self.assertEqual(report["session_count"], 3)
            self.assertEqual(report["total_tokens"], 600)

    def test_namespaced_nested_sol_execution_uses_shared_classifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "custom_tool_call",
                    "name": "functions.exec",
                    "call_id": "mutation",
                    "input": 'await tools.apply_patch("patch")',
                }),
                record("response_item", {
                    "type": "custom_tool_call",
                    "name": "functions.exec",
                    "call_id": "terraform",
                    "input": 'await tools.exec_command({"cmd":"terraform plan"})',
                }),
                record("response_item", {
                    "type": "custom_tool_call",
                    "name": "functions.exec",
                    "call_id": "tag",
                    "input": 'await tools.exec_command({"cmd":"git tag v1"})',
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(len(report["sol_execution_calls"]), 3)

    def test_successful_spawn_without_child_is_uncertain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "spawn",
                    "arguments": json.dumps({"agent_type": "worker"}),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "spawn",
                    "output": json.dumps({"agent_id": "missing-child"}),
                    "turn_id": "turn-a",
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("successful spawn" in item for item in report["routing_violations"]))

    def test_unavailable_luna_followed_by_terra_or_sol_is_a_routing_violation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            turn = "turn-a"
            metadata = {"turn_id": turn}
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "luna-failed",
                    "arguments": json.dumps({"agent_type": "luna_executor"}),
                    **metadata,
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "luna-failed",
                    "output": "Unknown model `gpt-5.6-luna` for spawn_agent. Available models: gpt-5.6-sol, gpt-5.6-terra",
                    **metadata,
                }),
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "terra-escalation",
                    "arguments": json.dumps({"agent_type": "worker"}),
                    **metadata,
                }),
                record("response_item", {
                    "type": "function_call",
                    "name": "apply_patch",
                    "call_id": "sol-direct",
                    "arguments": "{\"patch\":\"x\"}",
                    **metadata,
                }),
                record("turn_context", {"model": "gpt-5.6-sol", "turn_id": "turn-b"}),
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "later-worker",
                    "arguments": json.dumps({"agent_type": "worker"}),
                    "turn_id": "turn-b",
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            violations = "\n".join(report["routing_violations"])
            self.assertIn("retry/escalation followed an unavailable gpt-5.6-luna", violations)
            self.assertIn("direct Sol execution followed an unavailable gpt-5.6-luna", violations)
            self.assertNotIn("later-worker", violations)

    def test_shared_spawn_result_matrix_is_strict_and_non_luna_mentions_do_not_poison(self) -> None:
        cases = (
            ({"agent_id": "child"}, True),
            ('{"thread_id":"thread-1"}', True),
            ({"task_name": "/root/bounded-task"}, True),
            ({"isError": True, "agent_id": "child"}, False),
            ({"status": "failed", "agent_id": "child"}, False),
            ({"agent_id": ""}, False),
            ({"nickname": None}, False),
            ({"nickname": "not-a-documented-standalone-id"}, False),
            ("{malformed", False),
            ("", False),
        )
        for output, expected in cases:
            with self.subTest(output=output):
                self.assertEqual(
                    AUDIT.classify_spawn_result(output, luna_role="luna_executor").succeeded,
                    expected,
                )
        self.assertFalse(AUDIT.classify_spawn_result(
            "Unknown model gpt-5.6-luna; this is only a Terra reviewer mention",
            luna_role="worker",
        ).unknown_luna)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "terra-mention",
                    "arguments": json.dumps({"agent_type": "worker"}),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "terra-mention",
                    "output": "Unknown model gpt-5.6-luna; reviewer mention only",
                    "turn_id": "turn-a",
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertFalse(any("unavailable gpt-5.6-luna" in item for item in report["routing_violations"]))

    def test_unknown_luna_result_matrix_matches_runtime_error_evidence_rules(self) -> None:
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
        for output, succeeded, unknown_luna in cases:
            with self.subTest(output=output):
                result = AUDIT.classify_spawn_result(output, luna_role="luna_executor")
                self.assertEqual(result.succeeded, succeeded)
                self.assertEqual(result.unknown_luna, unknown_luna)

    def test_request_aliases_and_unknown_role_luna_model_are_audited_like_runtime(self) -> None:
        cases = (
            ("agent_type", "luna_executor", None),
            ("subagent_type", "luna_executor", None),
            ("role", "luna_executor", None),
            ("name", "luna_executor", None),
            ("name", "custom-worker", "gpt-5.6-luna"),
        )
        for field, value, model in cases:
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request = {field: value}
                if model:
                    request["model"] = model
                extra = "".join([
                    record("response_item", {
                        "type": "function_call",
                        "name": "spawn_agent",
                        "call_id": "luna-failed",
                        "arguments": json.dumps(request),
                        "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call_output",
                        "call_id": "luna-failed",
                        "output": "Unknown model gpt-5.6-luna",
                        "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call",
                        "name": "spawn_agent",
                        "call_id": "retry",
                        "arguments": json.dumps({"name": "worker"}),
                        "turn_id": "turn-a",
                    }),
                ])
                path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
                report = AUDIT.audit_session_tree(str(path), root)
                self.assertTrue(any("retry/escalation followed" in item for item in report["routing_violations"]))

    def test_known_role_model_conflict_is_uncertain_in_the_auditor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "conflict",
                    "arguments": json.dumps({
                        "subagent_type": "luna_executor",
                        "model": "gpt-5.6-terra",
                    }),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "conflict",
                    "output": json.dumps({"task_name": "/root/conflicted-task"}),
                    "turn_id": "turn-a",
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertTrue(any("conflicts with explicit model" in item for item in report["routing_violations"]))

    def test_alias_conflicts_are_uncertain_but_identical_duplicates_remain_valid(self) -> None:
        cases = (
            ({
                "agent_type": "reviewer",
                "role": "luna_executor",
                "model": "gpt-5.6-luna",
            }, "spawn identity aliases disagree"),
            ({
                "agent_type": "luna_executor",
                "model": "gpt-5.6-luna",
                "model_name": "gpt-5.6-sol",
            }, "spawn model aliases disagree"),
        )
        for index, (request, expected) in enumerate(cases):
            with self.subTest(request=request), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                extra = record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": f"conflict-{index}",
                    "arguments": json.dumps(request),
                    "turn_id": "turn-a",
                })
                path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
                report = AUDIT.audit_session_tree(str(path), root)
                self.assertTrue(any(expected in item for item in report["routing_violations"]))
                self.assertEqual(report["sessions"][0]["successful_spawns"], {})

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = {
                "agent_type": " luna_executor ",
                "subagent_type": "LUNA_EXECUTOR",
                "role": "luna_executor",
                "name": "luna_executor",
                "model": "gpt-5.6-luna",
                "model_name": " GPT-5.6-LUNA ",
            }
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "duplicates",
                    "arguments": json.dumps(request),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "duplicates",
                    "output": json.dumps({"task_name": "/root/duplicate-alias-task"}),
                    "turn_id": "turn-a",
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["sessions"][0]["successful_spawns"], {"luna_executor": 1})
            self.assertFalse(any("aliases disagree" in item for item in report["routing_violations"]))

    def test_task_name_success_is_counted_but_nickname_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "task-name",
                    "arguments": json.dumps({"agent_type": "worker"}),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "task-name",
                    "output": json.dumps({"task_name": "gpt-5.6-luna-unavailable-repro"}),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "nickname",
                    "arguments": json.dumps({"agent_type": "worker"}),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "nickname",
                    "output": json.dumps({"nickname": "not-a-documented-standalone-id"}),
                    "turn_id": "turn-a",
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["sessions"][0]["successful_spawns"], {"worker": 1})

    def test_outer_functions_exec_requires_canonical_luna_spawn_for_failure_state(self) -> None:
        canonical = 'await tools.multi_agent_v1__spawn_agent({"agent_type":"luna_executor","fork_context":false,"message":"bounded\\nPACKAGE_ID: outer\\nPACKAGE_PHASE: initial"});'
        extra = "".join([
            record("response_item", {
                "type": "custom_tool_call",
                "name": "functions.exec",
                "call_id": "outer-luna",
                "input": canonical,
                "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "custom_tool_call_output",
                "call_id": "outer-luna",
                "output": "Unknown model gpt-5.6-luna",
                "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "outer-retry",
                "arguments": json.dumps({"agent_type": "worker"}),
                "turn_id": "turn-a",
            }),
        ])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertTrue(any("retry/escalation followed" in item for item in report["routing_violations"]))

    def test_historical_metadata_turn_id_tracks_unavailable_luna_without_overriding_top_level(self) -> None:
        metadata = {"internal_chat_message_metadata_passthrough": {"turn_id": "historical-turn"}}
        extra = "".join([
            record("response_item", {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "missing-turn",
                "arguments": json.dumps({"agent_type": "luna_executor"}),
                **metadata,
            }),
            record("response_item", {
                "type": "function_call_output",
                "call_id": "missing-turn",
                "output": "Unknown model gpt-5.6-luna",
                **metadata,
            }),
            record("response_item", {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "later-worker",
                "arguments": json.dumps({"agent_type": "worker"}),
                **metadata,
            }),
        ])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertTrue(any("retry/escalation followed" in item for item in report["routing_violations"]))
            self.assertFalse(any("lacks the documented top-level turn_id" in item for item in report["routing_violations"]))
        self.assertEqual(AUDIT._turn_id({
            "turn_id": "live-turn",
            "internal_chat_message_metadata_passthrough": {"turn_id": "historical-turn"},
        }), "live-turn")

    def test_requested_role_must_match_child_role_and_actual_model_family(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=successful_spawn("luna_executor"))
            self.write_log(root, "child", "child", "gpt-5.6-terra", [200], "root", "reviewer")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertEqual(report["family_totals"]["terra"]["total_tokens"], 200)
            self.assertTrue(any("role mismatch" in item for item in report["routing_violations"]))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(AUDIT.main([str(parent), "--sessions-root", str(root), "--json", "--strict"]), 1)

    def test_child_role_with_sol_usage_is_partial_even_when_role_label_is_luna(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=successful_spawn("luna_executor"))
            self.write_log(root, "child", "child", "gpt-5.6-sol", [200], "root", "luna_executor")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("used 'sol' model family" in item for item in report["routing_violations"]))

    def test_missing_extra_and_unknown_child_roles_are_partial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_parent = self.write_log(root, "missing", "missing", "gpt-5.6-luna", [100], extra=successful_spawn("luna_executor"))
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "missing")
            missing = AUDIT.audit_session_tree(str(missing_parent), root)
            self.assertEqual(missing["cost_status"], "partial_uncertain")
            self.assertTrue(any("has no declared agent_role" in item for item in missing["routing_violations"]))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra_parent = self.write_log(root, "extra", "extra", "gpt-5.6-luna", [100])
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "extra", "luna_executor")
            extra = AUDIT.audit_session_tree(str(extra_parent), root)
            self.assertEqual(extra["cost_status"], "partial_uncertain")
            self.assertTrue(any("extra child log" in item for item in extra["routing_violations"]))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unknown_parent = self.write_log(root, "unknown", "unknown", "gpt-5.6-luna", [100], extra=successful_spawn("luna_executor"))
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "unknown", "not_a_role")
            unknown = AUDIT.audit_session_tree(str(unknown_parent), root)
            self.assertEqual(unknown["cost_status"], "partial_uncertain")
            self.assertTrue(any("unknown agent_role" in item for item in unknown["routing_violations"]))

    def test_fully_matched_requested_role_child_role_and_family_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=successful_spawn("luna_executor"))
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "root", "luna_executor")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertEqual(report["cost_status"], "complete")
            self.assertFalse(report["routing_violations"])

    def test_completed_child_without_explicit_close_is_a_lifecycle_violation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "spawn",
                    "arguments": json.dumps({"agent_type": "luna_executor"}),
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "spawn",
                    "output": json.dumps({"agent_id": "child"}),
                    "turn_id": "turn-a",
                }),
            ])
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "root", "luna_executor")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any("no confirmed successful close_agent result" in item for item in report["routing_violations"]))

    def test_close_agent_requires_target_and_confirmed_success_output(self) -> None:
        cases = (
            ("completed", {"previous_status": {"completed": "done"}}, True, False),
            ("running", {"previous_status": "running"}, True, False),
            ("shutdown", {"previous_status": "shutdown"}, True, False),
            ("errored", {"previous_status": {"errored": "failed task"}}, True, False),
            ("not-found", {"previous_status": "not_found"}, True, True),
            ("malformed", {"previous_status": "unknown"}, True, True),
            ("tool-error", {"error": "close failed"}, True, True),
            ("missing-output", None, False, True),
        )
        for name, close_output, include_output, should_violate in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                extra = spawn_and_close(
                    "luna_executor",
                    close_output=close_output,
                    include_close_output=include_output,
                )
                parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
                self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "root", "luna_executor")
                report = AUDIT.audit_session_tree(str(parent), root)
                closure_violations = [
                    item for item in report["routing_violations"]
                    if "close_agent" in item
                ]
                self.assertEqual(bool(closure_violations), should_violate)

    def test_legacy_close_agent_id_field_is_not_closure_proof(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call", "name": "spawn_agent", "call_id": "spawn",
                    "arguments": json.dumps({"agent_type": "luna_executor"}), "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output", "call_id": "spawn",
                    "output": json.dumps({"agent_id": "child"}), "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call", "name": "close_agent", "call_id": "legacy-close",
                    "arguments": json.dumps({"agent_id": "child"}), "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output", "call_id": "legacy-close",
                    "output": json.dumps({"previous_status": "running"}), "turn_id": "turn-a",
                }),
            ])
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "root", "luna_executor")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any(
                "no confirmed successful close_agent result" in item
                for item in report["routing_violations"]
            ))

    def test_outer_functions_exec_close_is_not_inferred_as_closure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "function_call", "name": "spawn_agent", "call_id": "spawn",
                    "arguments": json.dumps({"agent_type": "luna_executor"}), "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "function_call_output", "call_id": "spawn",
                    "output": json.dumps({"agent_id": "child"}), "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "custom_tool_call", "name": "exec", "call_id": "outer-close",
                    "input": 'await tools.multi_agent_v1__close_agent({target:"child"});',
                    "turn_id": "turn-a",
                }),
                record("response_item", {
                    "type": "custom_tool_call_output", "call_id": "outer-close",
                    "output": json.dumps({"previous_status": "running"}), "turn_id": "turn-a",
                }),
            ])
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "root", "luna_executor")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any(
                "no confirmed successful close_agent result" in item
                for item in report["routing_violations"]
            ))

    def test_thread_limit_recovery_accepts_inspect_confirmed_close_and_one_retry(self) -> None:
        request = {
            "agent_type": "verifier",
            "message": "verify\nPACKAGE_ID: recovery\nPACKAGE_PHASE: verify",
            "fork_context": False,
        }
        extra = "".join([
            spawn_and_close("luna_executor", include_close_output=False),
            record("response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "limited",
                "arguments": json.dumps(request), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call_output", "call_id": "limited",
                "output": "agent-thread-limit", "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call", "name": "Agent", "call_id": "inspect",
                "arguments": json.dumps({"action": "list"}), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call", "name": "close_agent", "call_id": "close-child",
                "arguments": json.dumps({"target": "child"}), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call_output", "call_id": "close-child",
                "output": json.dumps({"previous_status": {"completed": "done"}}), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "retry",
                "arguments": json.dumps(request), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call_output", "call_id": "retry",
                "output": json.dumps({"agent_id": "retry-child"}), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call", "name": "close_agent", "call_id": "close-retry",
                "arguments": json.dumps({"target": "retry-child"}), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call_output", "call_id": "close-retry",
                "output": json.dumps({"previous_status": "shutdown"}), "turn_id": "turn-a",
            }),
        ])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            self.write_log(root, "child", "child", "gpt-5.6-luna", [200], "root", "luna_executor")
            self.write_log(root, "retry", "retry-child", "gpt-5.6-luna", [200], "root", "verifier")
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertFalse(any(
                "agent-thread-limit" in item for item in report["routing_violations"]
            ))

    def test_thread_limit_recovery_fails_without_inspection(self) -> None:
        request = {
            "agent_type": "verifier",
            "message": "verify\nPACKAGE_ID: no-inspect\nPACKAGE_PHASE: verify",
            "fork_context": False,
        }
        extra = "".join([
            record("response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "limited",
                "arguments": json.dumps(request), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call_output", "call_id": "limited",
                "output": "agent-thread-limit", "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "retry",
                "arguments": json.dumps(request), "turn_id": "turn-a",
            }),
        ])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any(
                "agent-thread-limit" in item and "inspection" in item
                for item in report["routing_violations"]
            ))

    def test_thread_limit_recovery_rejects_more_than_one_matching_retry(self) -> None:
        request = {
            "agent_type": "verifier",
            "message": "verify\nPACKAGE_ID: repeated\nPACKAGE_PHASE: verify",
            "fork_context": False,
        }
        entries = [
            record("response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": "limited",
                "arguments": json.dumps(request), "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call_output", "call_id": "limited",
                "output": "agent-thread-limit", "turn_id": "turn-a",
            }),
            record("response_item", {
                "type": "function_call", "name": "Agent", "call_id": "inspect",
                "arguments": json.dumps({"action": "list"}), "turn_id": "turn-a",
            }),
        ]
        for index in (1, 2):
            entries.append(record("response_item", {
                "type": "function_call", "name": "spawn_agent", "call_id": f"retry-{index}",
                "arguments": json.dumps(request), "turn_id": "turn-a",
            }))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(
                root, "parent", "root", "gpt-5.6-luna", [100], extra="".join(entries)
            )
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any(
                "exceeded one same-signature retry" in item
                for item in report["routing_violations"]
            ))

    def test_thread_limit_recovery_audits_changed_role_message_and_model(self) -> None:
        original = {
            "agent_type": "luna_executor",
            "fork_context": False,
            "message": "bounded\nPACKAGE_ID: adversarial\nPACKAGE_PHASE: initial",
        }
        changed_requests = (
            {
                **original,
                "agent_type": "focused_worker",
            },
            {
                **original,
                "message": "changed\nPACKAGE_ID: adversarial\nPACKAGE_PHASE: initial",
            },
            {
                **original,
                "model": "gpt-luna-alternate",
            },
            {
                **original,
                "fork_context": True,
            },
        )
        for index, changed in enumerate(changed_requests):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                extra = "".join([
                    record("response_item", {
                        "type": "function_call", "name": "spawn_agent", "call_id": "limited",
                        "arguments": json.dumps(original), "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call_output", "call_id": "limited",
                        "output": "agent-thread-limit", "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call", "name": "Agent", "call_id": "inspect",
                        "arguments": json.dumps({"action": "list"}), "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call", "name": "spawn_agent", "call_id": "changed",
                        "arguments": json.dumps(changed), "turn_id": "turn-a",
                    }),
                ])
                parent = self.write_log(
                    root, "parent", "root", "gpt-5.6-luna", [100], extra=extra
                )
                report = AUDIT.audit_session_tree(str(parent), root)
                self.assertTrue(any(
                    "changed normalized spawn signature" in item
                    for item in report["routing_violations"]
                ))

    def test_auditor_requires_recontract_evidence_for_new_package_after_limit(self) -> None:
        original = {
            "agent_type": "verifier",
            "fork_context": False,
            "message": "verify\nPACKAGE_ID: old-package\nPACKAGE_PHASE: verify",
        }
        for include_evidence in (False, True):
            with self.subTest(include_evidence=include_evidence), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                message = "verify\nPACKAGE_ID: new-package\nPACKAGE_PHASE: verify"
                if include_evidence:
                    message += (
                        "\nRECONTRACT_OLD_PACKAGE_ID: old-package"
                        "\nRECONTRACT_NEW_PACKAGE_ID: new-package"
                        f"\nRECONTRACT_OLD_CONTRACT_SHA256: {'a' * 64}"
                        f"\nRECONTRACT_NEW_CONTRACT_SHA256: {'b' * 64}"
                        "\nRECONTRACT_REASON: contract changed"
                        "\nRECONTRACT_SCOPE_ACCEPTANCE_DELTA: changed one assertion"
                    )
                extra = "".join([
                    record("response_item", {
                        "type": "function_call", "name": "spawn_agent", "call_id": "limited",
                        "arguments": json.dumps(original), "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call_output", "call_id": "limited",
                        "output": "agent-thread-limit", "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call", "name": "Agent", "call_id": "inspect",
                        "arguments": json.dumps({"action": "list"}), "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call", "name": "spawn_agent", "call_id": "new-package",
                        "arguments": json.dumps({
                            "agent_type": "verifier", "fork_context": False, "message": message,
                        }),
                        "turn_id": "turn-a",
                    }),
                ])
                parent = self.write_log(
                    root, "parent", "root", "gpt-5.6-luna", [100], extra=extra
                )
                report = AUDIT.audit_session_tree(str(parent), root)
                relabel_violations = [
                    item for item in report["routing_violations"]
                    if "silently relabeled work" in item
                ]
                self.assertEqual(bool(relabel_violations), not include_evidence)

    def test_auditor_rejects_second_successful_risk_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extras = []
            for index in (1, 2):
                child = f"risk-{index}"
                message = (
                    "HIGH_RISK_TRIGGER: concurrency\nEVIDENCE_PACK: diff\n"
                    f"PACKAGE_ID: risk-{index}\nPACKAGE_PHASE: review"
                )
                extras.extend([
                    record("response_item", {
                        "type": "function_call", "name": "spawn_agent", "call_id": f"risk-call-{index}",
                        "arguments": json.dumps({"agent_type": "risk_reviewer", "message": message}),
                        "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call_output", "call_id": f"risk-call-{index}",
                        "output": json.dumps({"agent_id": child}), "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call", "name": "close_agent", "call_id": f"close-risk-{index}",
                        "arguments": json.dumps({"target": child}), "turn_id": "turn-a",
                    }),
                    record("response_item", {
                        "type": "function_call_output", "call_id": f"close-risk-{index}",
                        "output": json.dumps({"previous_status": "interrupted"}), "turn_id": "turn-a",
                    }),
                ])
                self.write_log(root, child, child, "gpt-5.6-sol", [200], "root", "risk_reviewer")
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra="".join(extras))
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any(
                "successful risk_reviewer" in item for item in report["routing_violations"]
            ))

    def test_auditor_fails_closed_on_missing_package_markers(self) -> None:
        extra = record("response_item", {
            "type": "function_call",
            "name": "spawn_agent",
            "call_id": "unmarked",
            "arguments": json.dumps({"agent_type": "luna_executor", "message": "bounded"}),
            "turn_id": "turn-a",
        }, add_package_markers=False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(parent), root)
            self.assertTrue(any(
                "invalid package contract" in item for item in report["routing_violations"]
            ))

    def test_auditor_flags_duplicate_plain_text_and_opaque_app_package_uncertainty(self) -> None:
        duplicate = record("response_item", {
            "type": "function_call",
            "name": "spawn_agent",
            "call_id": "duplicate-markers",
            "arguments": json.dumps({
                "agent_type": "luna_executor",
                "message": "bounded\nPACKAGE_ID: one\nPACKAGE_ID: two\nPACKAGE_PHASE: initial",
            }),
            "turn_id": "turn-a",
        }, add_package_markers=False)
        opaque = record("response_item", {
            "type": "function_call",
            "name": "spawn_agent",
            "call_id": "opaque-message",
            "arguments": json.dumps({
                "agent_type": "luna_executor",
                "message": "gAAAAopaque-app-message",
            }),
            "turn_id": "turn-a",
        }, add_package_markers=False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=duplicate + opaque)
            report = AUDIT.audit_session_tree(str(path), root)
            invalid = [item for item in report["routing_violations"] if "invalid package contract" in item]
            self.assertEqual(len(invalid), 1)
            self.assertEqual(
                len([
                    item for item in report["completeness_violations"]
                    if "opaque/encrypted App spawn message" in item
                ]),
                1,
            )

    def test_opaque_app_initial_spawns_with_children_and_close_stay_uncertain(self) -> None:
        def app_call(name: str, call_id: str, arguments: dict) -> str:
            return record("response_item", {
                "type": "function_call",
                "name": name,
                "namespace": "collaboration",
                "call_id": call_id,
                "arguments": json.dumps(arguments),
                "internal_chat_message_metadata_passthrough": {"turn_id": "app-turn"},
            }, add_package_markers=False)

        def app_output(call_id: str, output: object) -> str:
            return record("response_item", {
                "type": "function_call_output",
                "call_id": call_id,
                "output": output if isinstance(output, str) else json.dumps(output),
                "internal_chat_message_metadata_passthrough": {"turn_id": "app-turn"},
            })

        for count in (1, 2):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                extra_parts: list[str] = []
                child_ids: list[str] = []
                for index in range(count):
                    task_name = f"luna_initial_{index}"
                    child_id = f"app-child-{index}"
                    child_ids.append(child_id)
                    extra_parts.extend([
                        app_call("spawn_agent", f"spawn-{index}", {
                            "task_name": task_name,
                            "agent_type": "luna_executor",
                            "fork_turns": "none",
                            "message": f"gAAAAopaque-initial-{index}",
                        }),
                        record("event_msg", {
                            "type": "sub_agent_activity",
                            "kind": "started",
                            "agent_thread_id": child_id,
                            "agent_path": f"/root/{task_name}",
                        }),
                        app_output(f"spawn-{index}", {"task_name": f"/root/{task_name}"}),
                        app_call("multi_agent_v1__close_agent", f"close-{index}", {"target": child_id}),
                        app_output(f"close-{index}", {"previous_status": {"completed": "done"}}),
                    ])
                    self.write_log(
                        root,
                        f"child-{index}",
                        child_id,
                        "gpt-5.6-luna",
                        [200 + index],
                        "root",
                        "luna_executor",
                    )
                parent = self.write_log(
                    root,
                    "parent",
                    "root",
                    "gpt-5.6-luna",
                    [100],
                    extra="".join(extra_parts),
                )

                report = AUDIT.audit_session_tree(str(parent), root)
                root_session = next(item for item in report["sessions"] if item["thread_id"] == "root")
                results = [
                    event for event in root_session["lifecycle_events"]
                    if event.get("kind") == "spawn_result"
                ]
                self.assertEqual(report["cost_status"], "partial_uncertain")
                self.assertEqual(root_session["successful_spawns"], {"luna_executor": count})
                self.assertEqual(
                    [event["identifiers"].get("thread_id") for event in results],
                    child_ids,
                )
                self.assertTrue(all(event["child_role"] == "luna_executor" for event in results))
                self.assertTrue(all(event["child_models"] == ["gpt-5.6-luna"] for event in results))
                self.assertTrue(all(
                    item["status"] == "completed" and item["close_status"] == "confirmed"
                    for item in report["child_lifecycle_statuses"]
                ))
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(
                        AUDIT.main([
                            str(parent), "--sessions-root", str(root), "--json", "--strict",
                        ]),
                        1,
                    )

    def test_escaped_dotted_nested_factory_is_an_audit_violation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join(
                record("response_item", {
                    "type": "custom_tool_call",
                    "name": "functions.exec",
                    "call_id": f"escaped-{index}",
                    "input": source,
                })
                for index, source in enumerate((
                    'await tools.multi_agent_v1__sp\\u0061wn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
                    'await tools.multi_agent_v1__sp\\u{61}wn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
                    'await tools.multi_agent_v1__sp\\u00zzwn_agent({"agent_type":"luna_executor","fork_context":false,"message":"x"});',
                ))
            )
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("exact agent factory reference" in item for item in report["routing_violations"]))
            self.assertTrue(any("invalid JavaScript identifier escape" in item for item in report["routing_violations"]))

    def test_missing_total_tokens_is_derived_but_marked_uncertain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "partial.jsonl"
            partial_usage = usage(110)
            del partial_usage["info"]["total_token_usage"]["total_tokens"]
            path.write_text("".join([
                record("session_meta", {"id": "root", "session_id": "root"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", partial_usage),
                record("event_msg", {"type": "task_complete"}),
            ]))
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["total_tokens"], 110)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("token/schema" in item for item in report["routing_violations"]))

    def test_null_token_info_is_reported_as_uncertain_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "null-info.jsonl"
            path.write_text("".join([
                record("session_meta", {"id": "root", "session_id": "root"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", {"type": "token_count", "info": None}),
                record("event_msg", {"type": "task_complete"}),
            ]))
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("token/schema" in item for item in report["routing_violations"]))

    def test_corrupt_selected_line_is_not_silently_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100])
            with path.open("a") as handle:
                handle.write("{corrupt\n")
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertTrue(any("corrupt JSON" in item for item in report["routing_violations"]))

    def test_cli_returns_nonzero_for_sol_execution_violation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = record("response_item", {
                "type": "custom_tool_call",
                "name": "functions.exec",
                "call_id": "mutation",
                "input": 'await tools.apply_patch("patch")',
            })
            path = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(AUDIT.main([str(path), "--sessions-root", str(root), "--json", "--strict"]), 1)

    def test_historical_audit_cli_reports_violations_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = record("response_item", {
                "type": "custom_tool_call",
                "name": "functions.exec",
                "call_id": "mutation",
                "input": 'await tools.apply_patch("patch")',
                "turn_id": "turn-a",
            })
            path = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            advisory = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--sessions-root", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(advisory.returncode, 0)
            self.assertIn("Routing mode: advisory", advisory.stdout)
            with path.open("a", encoding="utf-8") as handle:
                handle.write("{corrupt-json\n")
            integrity = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--sessions-root", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(integrity.returncode, 0)
            self.assertIn("corrupt JSON", integrity.stdout)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--sessions-root", str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertNotIn("Traceback", completed.stderr)

    def test_computed_sol_mutation_is_detected_by_auditor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = record("response_item", {
                "type": "custom_tool_call",
                "name": "functions.exec",
                "call_id": "mutation",
                "input": 'await tools["apply_patch"]("patch")',
            })
            path = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(len(report["sol_execution_calls"]), 1)
            self.assertTrue(report["routing_violations"])

    def test_dynamic_nested_tool_access_is_partial_and_strict_fails_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = "".join([
                record("response_item", {
                    "type": "custom_tool_call",
                    "name": "functions.exec",
                    "call_id": "dynamic",
                    "input": 'const method = "exec_command"; await tools[method]({"cmd":"rg router tests"})',
                }),
                record("response_item", {
                    "type": "custom_tool_call_output",
                    "call_id": "dynamic",
                    "output": '{"captured_inner_evidence":true,"inner_tool_call":"apply_patch"}',
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-terra", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("dynamic tools access" in item for item in report["routing_violations"]))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(AUDIT.main([str(path), "--sessions-root", str(root), "--json", "--strict"]), 1)

    def test_task_complete_must_be_terminal_for_final_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "continued.jsonl"
            path.write_text("".join([
                record("session_meta", {"id": "root", "session_id": "root"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(100)),
                record("event_msg", {"type": "task_complete"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("response_item", {"type": "message", "role": "user", "content": []}),
            ]))
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("task_complete" in item for item in report["routing_violations"]))

    def test_task_started_resets_completion_and_final_report_for_the_final_epoch(self) -> None:
        old_report = (
            "Outcome: completed. Evidence: tests passed. Review: not run. "
            "Routing/WCU: Luna. Risks: none. Delivery: Git status not applicable."
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            aborted = root / "aborted.jsonl"
            aborted.write_text("".join([
                record("session_meta", {"id": "aborted", "session_id": "aborted"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(100)),
                record("event_msg", {"type": "task_complete", "last_agent_message": old_report}),
                record("event_msg", {"type": "task_started"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(150)),
                record("event_msg", {"type": "turn_aborted"}),
            ]))
            report = AUDIT.audit_session_tree(str(aborted), root)
            session = report["sessions"][0]
            self.assertFalse(session["task_complete"])
            self.assertTrue(session["interrupted"])
            self.assertEqual(session["last_agent_message"], "")
            self.assertEqual(session["completion_status"], "interrupted")
            self.assertTrue(any("final task epoch interrupted" in item for item in report["routing_violations"]))
            self.assertFalse(any(old_report in item for item in report["delivery_report_findings"]))

            completed = root / "completed.jsonl"
            completed.write_text("".join([
                record("session_meta", {"id": "completed", "session_id": "completed"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(100)),
                record("event_msg", {"type": "task_complete", "last_agent_message": old_report}),
                record("event_msg", {"type": "task_started"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(150)),
                record("event_msg", {"type": "task_complete"}),
            ]))
            report = AUDIT.audit_session_tree(str(completed), root)
            session = next(item for item in report["sessions"] if item["thread_id"] == "completed")
            self.assertTrue(session["task_complete"])
            self.assertEqual(session["task_complete_count"], 2)
            self.assertEqual(session["last_agent_message"], "")
            self.assertTrue(report["delivery_report_findings"])
            self.assertFalse(any(old_report in item for item in report["delivery_report_findings"]))

    def test_production_shaped_app_lifecycle_trace_preserves_lineage_and_budget_findings(self) -> None:
        def app_call(name: str, call_id: str, arguments: dict) -> str:
            return record("response_item", {
                "type": "function_call",
                "name": name,
                "namespace": "collaboration",
                "call_id": call_id,
                "arguments": json.dumps(arguments),
                "internal_chat_message_metadata_passthrough": {"turn_id": "app-turn"},
            }, add_package_markers=False)

        def app_output(call_id: str, output: object) -> str:
            return record("response_item", {
                "type": "function_call_output",
                "call_id": call_id,
                "output": output if isinstance(output, str) else json.dumps(output),
                "internal_chat_message_metadata_passthrough": {"turn_id": "app-turn"},
            })

        def activity(kind: str, thread_id: str, path: str) -> str:
            return record("event_msg", {
                "type": "sub_agent_activity",
                "kind": kind,
                "agent_thread_id": thread_id,
                "agent_path": path,
            })

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            luna_id = "app-luna-thread"
            terra_id = "app-terra-thread"
            luna_path = "/root/luna_competition_executor"
            terra_path = "/root/terra_acceptance_reviewer"
            extra = "".join([
                app_call("spawn_agent", "full-history", {
                    "task_name": "luna_competition_executor",
                    "agent_type": "luna_executor",
                    "fork_turns": "all",
                    "message": "gAAAAopaque-full-history-message",
                }),
                app_output("full-history", "Full-history forked agents inherit the parent agent type; omit agent_type, or spawn without a full-history fork."),
                app_call("spawn_agent", "luna-spawn", {
                    "task_name": "luna_competition_executor",
                    "agent_type": "luna_executor",
                    "fork_turns": "none",
                    "message": "gAAAAopaque-luna-message",
                }),
                activity("started", luna_id, luna_path),
                app_output("luna-spawn", {"task_name": luna_path}),
                app_call("wait_agent", "wait-luna", {"timeout_ms": 60_000}),
                app_output("wait-luna", {"message": "Wait completed.", "timed_out": False}),
                app_call("spawn_agent", "terra-spawn", {
                    "task_name": "terra_acceptance_reviewer",
                    "agent_type": "reviewer",
                    "fork_turns": "none",
                    "message": "gAAAAopaque-reviewer-message",
                }),
                activity("started", terra_id, terra_path),
                app_output("terra-spawn", {"task_name": terra_path}),
                app_call("multi_agent_v1__close_agent", "close-terra", {"target": terra_id}),
                app_output("close-terra", {"previous_status": {"completed": "done"}}),
                app_call("followup_task", "correction-one", {
                    "target": "luna_competition_executor",
                    "message": "gAAAAopaque-correction-one",
                }),
                app_output("correction-one", ""),
                app_call("followup_task", "correction-two", {
                    "target": "luna_competition_executor",
                    "message": "gAAAAopaque-correction-two",
                }),
                app_output("correction-two", ""),
                app_call("interrupt_agent", "interrupt-luna", {"target": "luna_competition_executor"}),
                app_output("interrupt-luna", {"previous_status": "running"}),
            ])
            parent = self.write_log(root, "parent", "root", "gpt-5.6-sol", [100], extra=extra)
            luna = root / "luna.jsonl"
            luna.write_text("".join([
                record("session_meta", {
                    "id": luna_id, "session_id": "root", "parent_thread_id": "root",
                    "agent_role": "luna_executor",
                }),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(200)),
                record("event_msg", {"type": "task_complete"}),
                record("event_msg", {"type": "task_started"}),
                record("turn_context", {"model": "gpt-5.6-luna"}),
                record("event_msg", usage(250)),
                record("event_msg", {"type": "turn_aborted"}),
            ]))
            self.write_log(root, "terra", terra_id, "gpt-5.6-terra", [300], "root", "reviewer")

            report = AUDIT.audit_session_tree(str(parent), root)
            root_session = next(item for item in report["sessions"] if item["thread_id"] == "root")
            results = [event for event in root_session["lifecycle_events"] if event.get("kind") == "spawn_result"]
            self.assertEqual(root_session["failed_spawns"], {"luna_executor": 1})
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["child_thread_id"], luna_id)
            self.assertEqual(results[0]["child_role"], "luna_executor")
            self.assertEqual(results[0]["child_models"], ["gpt-5.6-luna"])
            self.assertEqual(results[1]["child_thread_id"], terra_id)
            self.assertFalse(any("invalid package contract" in item for item in report["routing_violations"]))
            self.assertTrue(any("correction/followup_task attempts" in item for item in report["routing_violations"]))
            self.assertTrue(any(item["child_thread_id"] == luna_id and item["status"] == "interrupted" for item in report["child_lifecycle_statuses"]))
            self.assertTrue(any(item["child_thread_id"] == terra_id and item["close_status"] == "confirmed" for item in report["child_lifecycle_statuses"]))
            self.assertEqual(report["sol_execution_calls"], [])
            self.assertGreaterEqual(len(report["sol_lifecycle_calls"]), 6)


if __name__ == "__main__":
    unittest.main()
