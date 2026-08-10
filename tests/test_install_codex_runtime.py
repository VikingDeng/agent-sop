from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/install_codex_runtime.py"
SPEC = importlib.util.spec_from_file_location("install_codex_runtime", SCRIPT)
assert SPEC and SPEC.loader
INSTALL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INSTALL
SPEC.loader.exec_module(INSTALL)


class InstallCodexRuntimeTests(unittest.TestCase):
    def test_install_preserves_main_model_and_merges_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            (codex_home / "config.toml").write_text(
                '\n'.join((
                    'model = "gpt-5.6-sol"',
                    'model_reasoning_effort = "high"',
                    'sandbox_mode = "read-only"',
                    'approval_policy = "never"',
                    '',
                    '[telemetry]',
                    'retained = "yes"',
                    '',
                    '[agents]',
                    'max_depth = 3',
                    'unrelated_agent_setting = "preserve"',
                    '',
                )),
                encoding="utf-8",
            )
            (codex_home / "hooks.json").write_text(json.dumps({
                "description": "existing",
                "hooks": {"PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "existing-hook"}]},
                    {"matcher": ".*", "hooks": [{"type": "command", "command": "/usr/bin/python3 \\\"$HOME/.codex/hooks/weighted_cost_router.py\\\""}]},
                    {"matcher": ".*", "hooks": [{"type": "command", "command": "CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3 \\\"$HOME/.codex/hooks/weighted_cost_router.py\\\""}]},
                ]},
            }), encoding="utf-8")

            installer = INSTALL.Installer(ROOT, home, workspace)
            installer.install()

            config = (codex_home / "config.toml").read_text()
            parsed = tomllib.loads(config)
            self.assertEqual(parsed["model"], "gpt-5.6-sol")
            self.assertEqual(parsed["model_reasoning_effort"], "high")
            self.assertEqual(parsed["sandbox_mode"], "read-only")
            self.assertEqual(parsed["approval_policy"], "never")
            self.assertEqual(parsed["telemetry"], {"retained": "yes"})
            self.assertEqual(parsed["agents"]["unrelated_agent_setting"], "preserve")
            self.assertEqual(parsed["agents"]["default_subagent_model"], "gpt-5.6-luna")
            self.assertEqual(parsed["agents"]["max_depth"], 1)
            hooks = json.loads((codex_home / "hooks.json").read_text())
            rendered = json.dumps(hooks)
            self.assertIn("existing-hook", rendered)
            self.assertIn(str(codex_home / "hooks" / "weighted_cost_router.py"), rendered)
            self.assertEqual(
                sum(INSTALL.Installer._is_router_registration(registration, home) for registration in hooks["hooks"]["PreToolUse"]),
                1,
            )
            self.assertTrue((codex_home / "agents" / "luna_executor.toml").is_symlink())
            terra_debugger = codex_home / "agents" / "terra_debugger.toml"
            self.assertTrue(terra_debugger.is_symlink())
            self.assertEqual(terra_debugger.resolve(), (ROOT / "codex" / "agents" / "terra_debugger.toml").resolve())

            second = INSTALL.Installer(ROOT, home, workspace)
            second.install()
            self.assertFalse(any(action.startswith("backup") for action in second.actions))

    def test_sol_supervisor_profile_sets_foreground_model_and_preserves_unrelated_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            config = codex_home / "config.toml"
            config.write_text(
                'model = "gpt-5.6-luna"\nmodel_reasoning_effort = "low"\nsandbox_mode = "read-only"\n\n[telemetry]\nretained = "yes"\n',
                encoding="utf-8",
            )
            INSTALL.Installer(ROOT, home, workspace, profile="sol-supervisor").install()
            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed["model"], "gpt-5.6-sol")
            self.assertEqual(parsed["model_reasoning_effort"], "high")
            self.assertEqual(parsed["sandbox_mode"], "read-only")
            self.assertEqual(parsed["telemetry"], {"retained": "yes"})

    def test_preserve_profile_is_the_default_and_cli_accepts_sol_supervisor(self) -> None:
        args = INSTALL.parse_args([])
        self.assertEqual(args.profile, "preserve")
        self.assertEqual(INSTALL.parse_args(["--profile", "sol-supervisor"]).profile, "sol-supervisor")
        self.assertEqual(INSTALL.parse_args(["--profile", "terra-supervisor"]).profile, "terra-supervisor")

    def test_terra_supervisor_profile_sets_foreground_model_and_preserves_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            config = codex_home / "config.toml"
            config.write_text(
                'model = "gpt-5.6-sol"\n'
                'model_reasoning_effort = "low"\n'
                'sandbox_mode = "read-only"\n'
                '\n'
                '[telemetry]\n'
                'retained = "yes"\n'
                '\n'
                '[agents]\n'
                'unrelated_agent_setting = "preserve"\n',
                encoding="utf-8",
            )
            hooks = codex_home / "hooks.json"
            hooks.write_text(json.dumps({
                "description": "existing",
                "hooks": {"PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "existing-hook"}]},
                ]},
            }), encoding="utf-8")

            INSTALL.Installer(ROOT, home, workspace, profile="terra-supervisor").install()

            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed["model"], "gpt-5.6-terra")
            self.assertEqual(parsed["model_reasoning_effort"], "high")
            self.assertEqual(parsed["sandbox_mode"], "read-only")
            self.assertEqual(parsed["telemetry"], {"retained": "yes"})
            self.assertEqual(parsed["agents"]["unrelated_agent_setting"], "preserve")
            self.assertEqual(parsed["agents"]["default_subagent_model"], "gpt-5.6-luna")
            self.assertEqual(parsed["agents"]["default_subagent_reasoning_effort"], "medium")
            self.assertEqual(parsed["agents"]["max_concurrent_threads_per_session"], 2)
            self.assertEqual(parsed["agents"]["max_depth"], 1)

            rendered_hooks = json.loads(hooks.read_text())
            rendered = json.dumps(rendered_hooks)
            self.assertIn("existing-hook", rendered)
            self.assertIn("CODEX_ROUTER_ENFORCEMENT=strict", rendered)
            self.assertEqual(
                sum(INSTALL.Installer._is_router_registration(registration, home)
                    for registration in rendered_hooks["hooks"]["PreToolUse"]),
                1,
            )

    def test_terra_debugger_role_declares_fixed_debugging_contract(self) -> None:
        role = tomllib.loads((ROOT / "codex" / "agents" / "terra_debugger.toml").read_text())
        self.assertEqual(role["name"], "terra_debugger")
        self.assertEqual(role["model"], "gpt-5.6-terra")
        self.assertEqual(role["model_reasoning_effort"], "high")
        self.assertEqual(role["sandbox_mode"], "workspace-write")
        for requirement in (
            "P1 contract",
            "P2",
            "falsifiable hypotheses",
            "independent oracle",
            "P3",
            "fallback behavior",
            "P4",
            "Luna",
            "STATUS: PASS | REVISE | BLOCKED",
            "ROOT_CAUSE:",
            "ALTERNATIVES_REJECTED:",
        ):
            self.assertIn(requirement, role["developer_instructions"])

    def test_preflight_requires_the_terra_debugger_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo_root = base / "repo"
            shutil.copytree(ROOT / "codex", repo_root / "codex")
            (repo_root / "codex" / "agents" / "terra_debugger.toml").unlink()
            home = base / "home"
            workspace = base / "workspace"
            (home / ".codex").mkdir(parents=True)
            workspace.mkdir()

            installer = INSTALL.Installer(repo_root, home, workspace)
            with self.assertRaisesRegex(ValueError, "terra_debugger.toml"):
                installer.preflight()
            self.assertFalse((home / ".codex" / "agents").exists())

    def test_malformed_existing_hooks_are_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            hooks = codex_home / "hooks.json"
            hooks.write_text("not json")
            installer = INSTALL.Installer(ROOT, home, workspace)
            with self.assertRaises(ValueError):
                installer.install()
            self.assertEqual(hooks.read_text(), "not json")

    def test_wrong_event_registration_shape_fails_before_linking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            hooks = codex_home / "hooks.json"
            hooks.write_text(json.dumps({"hooks": {"PreToolUse": {"matcher": ".*"}}}))
            installer = INSTALL.Installer(ROOT, home, workspace)
            with self.assertRaises(ValueError):
                installer.install()
            self.assertFalse((codex_home / "AGENTS.md").exists())
            self.assertEqual(json.loads(hooks.read_text())["hooks"]["PreToolUse"]["matcher"], ".*")

    def test_space_in_home_path_is_shell_quoted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home with space"
            workspace = base / "workspace"
            (home / ".codex").mkdir(parents=True)
            workspace.mkdir()
            installer = INSTALL.Installer(ROOT, home, workspace)
            installer.install()
            hooks = json.loads((home / ".codex" / "hooks.json").read_text())
            command = hooks["hooks"]["PreToolUse"][-1]["hooks"][0]["command"]
            self.assertEqual(
                shlex.split(command),
                [
                    "CODEX_ROUTER_ENFORCEMENT=strict",
                    "/usr/bin/python3",
                    str(home.resolve() / ".codex" / "hooks" / "weighted_cost_router.py"),
                ],
            )

    def test_agents_header_with_comment_remains_valid_toml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            config = codex_home / "config.toml"
            config.write_text('[agents] # keep this note\nmax_depth = 3\n')
            INSTALL.Installer(ROOT, home, workspace).install()
            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed["agents"]["max_depth"], 1)
            self.assertEqual(config.read_text().count("[agents]"), 1)

    def test_late_failure_rolls_back_files_and_original_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            original_source = base / "original-agents.md"
            original_source.write_text("original")
            runtime_agents = codex_home / "AGENTS.md"
            runtime_agents.symlink_to(original_source)
            config = codex_home / "config.toml"
            original_config = 'model = "gpt-5.6-sol"\n'
            config.write_text(original_config)

            installer = INSTALL.Installer(ROOT, home, workspace)

            def fail_late() -> None:
                raise OSError("injected hook activation failure")

            installer.merge_hooks = fail_late
            with self.assertRaises(RuntimeError):
                installer.install()
            self.assertTrue(runtime_agents.is_symlink())
            self.assertEqual(runtime_agents.resolve(), original_source.resolve())
            self.assertEqual(config.read_text(), original_config)
            self.assertFalse((codex_home / "agents" / "luna_executor.toml").exists())
            self.assertFalse((codex_home / "agents" / "terra_debugger.toml").exists())

    def test_description_mention_does_not_remove_unrelated_hook(self) -> None:
        registration = {
            "matcher": ".*",
            "description": "mentions weighted_cost_router.py but invokes something else",
            "hooks": [{"type": "command", "command": "python3 other.py"}],
        }
        self.assertFalse(INSTALL.Installer._is_router_registration(registration))

    def test_router_registration_detector_accepts_unprefixed_and_env_prefixed_commands(self) -> None:
        for command in (
            '/usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"',
            'CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"',
        ):
            with self.subTest(command=command):
                self.assertTrue(INSTALL.Installer._is_router_registration({"hooks": [{"command": command}]}))

    def test_custom_weighted_router_path_survives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            hooks_path = codex_home / "hooks.json"
            hooks_path.write_text(json.dumps({
                "description": "existing",
                "hooks": {"PreToolUse": [{
                    "matcher": ".*",
                    "hooks": [{"type": "command", "command": "/usr/bin/python3 /custom/weighted_cost_router.py"}],
                }]},
            }), encoding="utf-8")

            installer = INSTALL.Installer(ROOT, home, workspace)
            installer.install()
            merged = json.loads(hooks_path.read_text())
            commands = [
                hook.get("command")
                for registration in merged["hooks"]["PreToolUse"]
                for hook in registration["hooks"]
            ]
            self.assertIn("/usr/bin/python3 /custom/weighted_cost_router.py", commands)
            self.assertEqual(sum("weighted_cost_router.py" in command for command in commands), 2)

    def test_router_registration_detector_rejects_non_exact_launcher_or_env(self) -> None:
        for command in (
            'python3 "$HOME/.codex/hooks/weighted_cost_router.py"',
            'CODEX_ROUTER_ENFORCEMENT=advisory /usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"',
            'OTHER_SETTING=yes /usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"',
        ):
            with self.subTest(command=command):
                self.assertFalse(INSTALL.Installer._is_router_registration({"hooks": [{"command": command}]}))

    def test_mixed_registration_preserves_sibling_metadata_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            original = {
                "description": "existing",
                "hooks": {"PreToolUse": [
                    {"matcher": "first", "hooks": [{"type": "command", "command": "first-hook"}]},
                    {
                        "matcher": "mixed",
                        "metadata": {"owner": "user"},
                        "hooks": [
                            {"type": "command", "command": 'CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"'},
                            {"type": "command", "command": "user-notify", "timeout": 17},
                        ],
                    },
                    {"matcher": "last", "hooks": [{"type": "command", "command": "last-hook"}]},
                ]},
            }
            hooks_path = codex_home / "hooks.json"
            hooks_path.write_text(json.dumps(original), encoding="utf-8")

            installer = INSTALL.Installer(ROOT, home, workspace)
            installer.install()
            merged = json.loads(hooks_path.read_text())
            pretool = merged["hooks"]["PreToolUse"]
            self.assertEqual([item["matcher"] for item in pretool[:3]], ["first", "mixed", "last"])
            mixed = pretool[1]
            self.assertEqual(mixed["metadata"], {"owner": "user"})
            self.assertEqual(mixed["hooks"], [{"type": "command", "command": "user-notify", "timeout": 17}])
            self.assertEqual(pretool[-1]["hooks"][0]["command"].split()[0], "CODEX_ROUTER_ENFORCEMENT=strict")

            dry_run = INSTALL.Installer(ROOT, home, workspace, dry_run=True)
            dry_run.install()
            staged = json.loads(dry_run.staged_hooks)
            self.assertEqual(staged["hooks"]["PreToolUse"][1], mixed)
            self.assertIn("user-notify", json.dumps(staged))

    def test_repeated_install_and_dry_run_are_idempotent_for_each_profile(self) -> None:
        for profile in ("preserve", "sol-supervisor", "terra-supervisor"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                home = base / "home"
                workspace = base / "workspace"
                (home / ".codex").mkdir(parents=True)
                workspace.mkdir()
                installer = INSTALL.Installer(ROOT, home, workspace, profile=profile)
                installer.install()
                config_path = home / ".codex" / "config.toml"
                hooks_path = home / ".codex" / "hooks.json"
                installed_config = config_path.read_bytes()
                installed_hooks = hooks_path.read_bytes()

                repeated = INSTALL.Installer(ROOT, home, workspace, profile=profile)
                repeated.install()
                self.assertEqual(config_path.read_bytes(), installed_config)
                self.assertEqual(hooks_path.read_bytes(), installed_hooks)

                dry_run = INSTALL.Installer(ROOT, home, workspace, dry_run=True, profile=profile)
                dry_run.install()
                self.assertEqual(config_path.read_bytes(), installed_config)
                self.assertEqual(hooks_path.read_bytes(), installed_hooks)

                self.assertFalse(any(action.startswith("backup") for action in repeated.actions))
                self.assertFalse(any(action.startswith("backup") for action in dry_run.actions))
                staged = json.loads(dry_run.staged_hooks)
                pretool = staged["hooks"]["PreToolUse"]
                self.assertEqual(
                    sum("weighted_cost_router.py" in hook.get("command", "") for item in pretool for hook in item["hooks"]),
                    1,
                )

    def test_router_filename_as_non_script_argument_is_not_managed(self) -> None:
        registration = {
            "matcher": ".*",
            "hooks": [{"type": "command", "command": "rg weighted_cost_router.py"}],
        }
        self.assertFalse(INSTALL.Installer._is_router_registration(registration))

    def test_keyboard_interrupt_after_hook_activation_rolls_back_and_persists_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            workspace.mkdir()
            config = codex_home / "config.toml"
            original_config = 'model = "gpt-5.6-sol"\n'
            config.write_text(original_config)
            installer = INSTALL.Installer(ROOT, home, workspace)
            real_merge = installer.merge_hooks

            def interrupt_after_activation() -> None:
                real_merge()
                raise KeyboardInterrupt()

            installer.merge_hooks = interrupt_after_activation
            with self.assertRaises(RuntimeError):
                installer.install()
            self.assertEqual(config.read_text(), original_config)
            self.assertFalse((codex_home / "hooks.json").exists())
            manifest = json.loads(installer.manifest_path.read_text())
            self.assertEqual(manifest["status"], "rolled_back")
            self.assertGreater(len(manifest["mutations"]), 1)


if __name__ == "__main__":
    unittest.main()
