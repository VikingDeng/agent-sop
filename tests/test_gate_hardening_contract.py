from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "codex/hooks/weighted_routing_policy.py"
SPEC = importlib.util.spec_from_file_location("weighted_routing_policy_contract", POLICY_PATH)
assert SPEC and SPEC.loader
POLICY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = POLICY
SPEC.loader.exec_module(POLICY)


class AdaptiveSopContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_installed_overlay_references_are_runtime_stable(self) -> None:
        expected = "~/.codex/runtime-current/skeletons/contestos-adaptive-overlay-v2.md"
        self.assertIn(expected, self.read("codex/AGENTS.global.md"))
        self.assertIn(expected, self.read("codex/AGENTS.workspace.md"))

    def test_router_source_and_strict_opt_in_are_structural(self) -> None:
        readme = self.read("codex/README.md")
        self.assertIn("--routing-profile strict", readme)
        self.assertIn("advisory", readme)
        hooks = json.loads(self.read("codex/hooks/hooks.json"))
        managed_commands = [
            hook["command"]
            for registrations in hooks["hooks"].values()
            for registration in registrations
            for hook in registration["hooks"]
            if hook.get("type") == "command"
        ]
        self.assertEqual(len(managed_commands), 5)
        self.assertTrue(all(command.startswith("/usr/bin/python3 ") for command in managed_commands))
        self.assertIn('"Stop"', self.read("codex/hooks/hooks.json"))

    def test_supervisor_document_has_a_formal_version_marker(self) -> None:
        supervisor = self.read("sop/tier0-core/autonomous-supervisor.md")
        self.assertRegex(supervisor, r"(?:^|\n)- \*\*版本\*\*:\s*v\d+", msg="missing formal version marker")

    def test_strict_router_profile_remains_available(self) -> None:
        self.assertEqual(POLICY.MAX_CONCURRENT_OPEN_THREADS, 2)
        self.assertEqual(POLICY.MAX_RISK_REVIEWERS_PER_SESSION, 1)
        self.assertEqual(
            POLICY.GLOBAL_LOOP_BUDGET,
            {"initial": 1, "review": 1, "correction": 1, "re_review": 1},
        )


if __name__ == "__main__":
    unittest.main()
