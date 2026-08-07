from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_codex_session.py"
SPEC = importlib.util.spec_from_file_location("audit_codex_session", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def record(record_type: str, payload: dict) -> str:
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
        }),
        record("response_item", {
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps({"agent_id": f"{role}-child"}),
        }),
    ])


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
    ) -> Path:
        payload = {"id": thread_id, "session_id": "root" if parent else thread_id}
        if parent:
            payload["parent_thread_id"] = parent
        if role:
            payload["agent_role"] = role
        lines = [
            record("session_meta", payload),
            record("turn_context", {"model": model}),
            *(record("event_msg", usage(total)) for total in totals),
            extra,
            record("event_msg", usage(totals[-1])),
            record("event_msg", {"type": "task_complete"}),
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
                }),
                record("response_item", {
                    "type": "function_call_output",
                    "call_id": "spawn",
                    "output": json.dumps({"agent_id": "missing-child"}),
                }),
            ])
            path = self.write_log(root, "parent", "root", "gpt-5.6-luna", [100], extra=extra)
            report = AUDIT.audit_session_tree(str(path), root)
            self.assertEqual(report["cost_status"], "partial_uncertain")
            self.assertTrue(any("successful spawn" in item for item in report["routing_violations"]))

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
                self.assertEqual(AUDIT.main([str(parent), "--sessions-root", str(root), "--json"]), 1)

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
                self.assertEqual(AUDIT.main([str(path), "--sessions-root", str(root), "--json"]), 1)

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
                self.assertEqual(AUDIT.main([str(path), "--sessions-root", str(root), "--json"]), 1)

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


if __name__ == "__main__":
    unittest.main()
