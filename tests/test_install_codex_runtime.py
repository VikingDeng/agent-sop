import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
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
    def make_environment(self, base: Path) -> tuple[Path, Path, Path]:
        home = base / "home"
        workspace = base / "workspace"
        (home / ".codex").mkdir(parents=True)
        workspace.mkdir()
        return home, workspace, home / ".codex"

    def install(self, home: Path, workspace: Path, **kwargs: object) -> INSTALL.Installer:
        installer = INSTALL.Installer(ROOT, home, workspace, **kwargs)
        installer.install()
        return installer

    def test_first_install_creates_complete_generation_and_stable_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            installer = self.install(home, workspace)

            current = home / INSTALL.RUNTIME_CURRENT
            self.assertTrue(current.is_symlink())
            self.assertEqual(current.resolve(), installer.snapshot_path.resolve())
            self.assertTrue((home / INSTALL.INSTALL_LOCK).is_file())
            stable_root = installer.runtime_current
            self.assertEqual(
                os.readlink(codex_home / "agents/luna_executor.toml"),
                str(stable_root / "codex/agents/luna_executor.toml"),
            )
            self.assertEqual(
                os.readlink(codex_home / "agents/sol_architect.toml"),
                str(stable_root / "codex/agents/sol_architect.toml"),
            )
            self.assertEqual(
                os.readlink(workspace / "AGENTS.md"),
                str(stable_root / "codex/AGENTS.workspace.md"),
            )
            generation = installer.snapshot_path
            assert generation is not None
            self.assertTrue((generation / INSTALL.SNAPSHOT_MANIFEST).is_file())
            self.assertTrue((generation / "PRINCIPLES.md").is_file())
            self.assertTrue((generation / "PROSE_STANDARD.md").is_file())
            self.assertTrue(all(not item.is_symlink() for item in generation.rglob("*")))
            self.assertTrue(all(item.stat().st_mode & 0o222 == 0 for item in [generation, *generation.rglob("*")]))

    def test_first_install_creates_missing_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            home.mkdir()
            workspace.mkdir()

            self.install(home, workspace)

            self.assertTrue((home / ".codex/config.toml").is_file())
            self.assertTrue((home / ".codex/AGENTS.md").is_file())
            self.assertTrue((home / INSTALL.RUNTIME_CURRENT).is_symlink())

    def test_migration_from_direct_snapshot_or_repository_links_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            shutil.copytree(ROOT, source)
            home, workspace, codex_home = self.make_environment(base)
            (codex_home / "agents").mkdir()
            (codex_home / "hooks").mkdir()
            (codex_home / "skills").mkdir()
            retired_source = source / "codex/skills/research-execution-grill"
            retired_source.mkdir(parents=True, exist_ok=True)
            (retired_source / "SKILL.md").write_text("retired\n", encoding="utf-8")
            (codex_home / "AGENTS.md").symlink_to(source / "codex/AGENTS.global.md")
            (codex_home / "agents/luna_executor.toml").symlink_to(source / "codex/agents/luna_executor.toml")
            (codex_home / "skills/research-execution-grill").symlink_to(
                source / "codex/skills/research-execution-grill", target_is_directory=True
            )
            (workspace / "AGENTS.md").symlink_to(source / "codex/AGENTS.workspace.md")

            installer = INSTALL.Installer(source, home, workspace)
            installer.install()
            current = installer.runtime_current
            for link in (codex_home / "AGENTS.md", codex_home / "agents/luna_executor.toml", workspace / "AGENTS.md"):
                self.assertTrue(os.readlink(link).startswith(str(current)), link)
            self.assertFalse((codex_home / "skills/research-execution-grill").exists())
            self.assertFalse((codex_home / "skills/research-execution-grill").is_symlink())
            backups = list(codex_home.glob("*.backup-*")) + list((codex_home / "agents").glob("*.backup-*")) + list((codex_home / "skills").glob("*.backup-*")) + list(workspace.glob("*.backup-*"))
            self.assertTrue(backups)

            repeated = INSTALL.Installer(source, home, workspace)
            repeated.install()
            self.assertFalse(any(action.startswith("backup") for action in repeated.actions))

    def test_retirement_preserves_unrecognized_same_named_skill_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home, workspace, codex_home = self.make_environment(base)
            external = base / "external-fork/codex/skills/research-execution-grill"
            external.mkdir(parents=True)
            destination = codex_home / "skills/research-execution-grill"
            destination.parent.mkdir()
            destination.symlink_to(external, target_is_directory=True)

            installer = self.install(home, workspace)

            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), external.resolve())
            self.assertTrue(any("preserve unrecognized retired-link" in action for action in installer.actions))

    def test_snapshot_markdown_dependencies_are_closed(self) -> None:
        snapshot_files = set(INSTALL.SNAPSHOT_FILES)
        missing: list[str] = []
        for relative in sorted(snapshot_files):
            source = ROOT / relative
            if source.suffix != ".md":
                continue
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)#?]+\.md)(?:#[^)]*)?\)", text):
                if "://" in target:
                    continue
                resolved = (source.parent / target).resolve().relative_to(ROOT).as_posix()
                if resolved not in snapshot_files:
                    missing.append(f"{relative} -> {resolved}")
            for target in re.findall(r"→\s*([A-Za-z0-9_./-]+\.md)", text):
                if target.startswith(("tier0-", "tier1-", "tier2-")):
                    resolved = f"sop/{target}"
                elif target.startswith(("../", "./")):
                    resolved = (source.parent / target).resolve().relative_to(ROOT).as_posix()
                else:
                    resolved = target
                if resolved not in snapshot_files:
                    missing.append(f"{relative} -> {resolved}")
        self.assertEqual(missing, [])

    def test_snapshot_registry_evidence_dependencies_are_closed(self) -> None:
        snapshot_files = set(INSTALL.SNAPSHOT_FILES)
        registry = json.loads((ROOT / "skill-registry.yaml").read_text(encoding="utf-8"))
        missing: list[str] = []
        for entry in registry["entries"]:
            evidence_paths = [entry["audit"].get("evidence"), entry["evaluation"].get("pilot_evidence")]
            for evidence in filter(None, evidence_paths):
                relative = evidence.split("#", 1)[0]
                if relative not in snapshot_files:
                    missing.append(f"{entry['id']} -> {relative}")
        self.assertEqual(missing, [])

    def test_update_builds_new_generation_and_switches_one_current_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            shutil.copytree(ROOT, source)
            home, workspace, codex_home = self.make_environment(base)
            first = INSTALL.Installer(source, home, workspace)
            first.install()
            current = home / INSTALL.RUNTIME_CURRENT
            old_target = os.readlink(current)
            stable_target = os.readlink(codex_home / "hooks/weighted_cost_router.py")

            readme = source / "codex/README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\nupdate marker\n", encoding="utf-8")
            second = INSTALL.Installer(source, home, workspace)
            second.install()

            self.assertNotEqual(os.readlink(current), old_target)
            self.assertNotEqual(second.snapshot_path, first.snapshot_path)
            self.assertEqual(os.readlink(codex_home / "hooks/weighted_cost_router.py"), stable_target)
            self.assertTrue(Path(old_target).is_dir())
            self.assertEqual(current.resolve(), second.snapshot_path.resolve())

    def test_source_checkout_removal_leaves_runtime_layers_and_profiles_available(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            shutil.copytree(ROOT, source)
            home, workspace, codex_home = self.make_environment(base)
            installer = INSTALL.Installer(source, home, workspace)
            installer.install()
            hooks = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
            hook_command = shlex.split(hooks["hooks"]["SessionStart"][-1]["hooks"][0]["command"])
            launcher = Path(hook_command[1])
            self.assertEqual(launcher, installer.python_launcher)
            self.assertTrue(launcher.is_file())
            self.assertTrue(os.access(launcher, os.X_OK))
            self.assertFalse(launcher.is_relative_to(source.resolve()))
            shutil.rmtree(source)

            hook_environment = dict(os.environ)
            hook_environment["HOME"] = str(home)
            installed_command = hooks["hooks"]["SessionStart"][-1]["hooks"][0][
                "command"
            ]
            session_start = subprocess.run(
                ["/bin/sh", "-c", installed_command],
                input=json.dumps(
                    {
                        "hook_event_name": "SessionStart",
                        "model": "gpt-5.6-terra",
                        "model_reasoning_effort": "high",
                        "session_id": "source-removal-test",
                    }
                ),
                capture_output=True,
                text=True,
                check=False,
                env=hook_environment,
            )
            self.assertEqual(session_start.returncode, 0, session_start.stderr)
            session_payload = json.loads(session_start.stdout)
            context = session_payload["hookSpecificOutput"]["additionalContext"]
            context_limit = hooks["hooks"]["SessionStart"][-1]["hooks"][0][
                "additionalContextLimit"
            ]
            self.assertTrue(context.startswith("SOP_RUNTIME "))
            self.assertLessEqual(len(context), context_limit)
            self.assertLessEqual(len(context.encode("utf-8")), context_limit)
            marker = json.loads(context.splitlines()[0].removeprefix("SOP_RUNTIME "))
            self.assertRegex(marker["generation"], r"^sha256-[0-9a-f]{64}$")

            self.assertIn("Weighted-cost routing", (codex_home / "hooks/weighted_cost_router.py").read_text())
            self.assertTrue((codex_home / "agents/luna_executor.toml").read_text())
            runtime = home / INSTALL.RUNTIME_CURRENT
            self.assertIn("唯一通用运行时决策源", (runtime / "sop/tier0-core/autonomous-supervisor.md").read_text())
            self.assertIn("platform adapter", (runtime / "codex/CODEX-ADAPTER.md").read_text())
            self.assertIn("0→1 development", (runtime / "sop/tier1-skeleton/run-development.md").read_text())
            self.assertIn("已批准 proposal", (runtime / "sop/tier1-skeleton/research-execution-grill.md").read_text())
            self.assertIn("有截止时间", (runtime / "sop/tier1-skeleton/run-competition.md").read_text())
            evidence_reference = runtime / "sop/tier1-skeleton/references/research-evidence-presentation.md"
            self.assertIn("authoritative final table", evidence_reference.read_text(encoding="utf-8"))
            overlay = runtime / "skeletons/contestos-adaptive-overlay-v2.md"
            self.assertIn("legacy, explicit-only", overlay.read_text(encoding="utf-8"))
            registry = json.loads((runtime / "skill-registry.yaml").read_text(encoding="utf-8"))
            self.assertTrue(registry["entries"])
            self.assertFalse(any(item["lifecycle"]["promoted"] for item in registry["entries"]))
            competition_reference = "~/.codex/runtime-current/sop/tier1-skeleton/run-competition.md"
            competition = runtime / "sop/tier1-skeleton/run-competition.md"
            self.assertIn("执行通用竞赛与黑客松", competition.read_text(encoding="utf-8"))
            global_context = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("~/.codex/runtime-current/codex/CODEX-ADAPTER.md", global_context)
            self.assertIn("~/.codex/runtime-current/sop/tier1-skeleton/run-development.md", global_context)
            self.assertIn(competition_reference, global_context)
            workspace_context = (workspace / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Codex routing comes from `codex/CODEX-ADAPTER.md`", workspace_context)
            for context_text in (global_context, workspace_context):
                self.assertNotIn("runtime-current/skeletons/contestos-adaptive-overlay", context_text)
            manifest = json.loads((runtime / INSTALL.SNAPSHOT_MANIFEST).read_text(encoding="utf-8"))
            self.assertEqual(manifest["runtime_components"]["codex_adapter"]["version"], "v2")
            self.assertEqual(manifest["runtime_components"]["development_profile"]["version"], "v1")
            self.assertRegex(manifest["runtime_components"]["kernel"]["sha256"], r"^[0-9a-f]{64}$")

    def test_failure_before_current_switch_preserves_old_active_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            shutil.copytree(ROOT, source)
            home, workspace, codex_home = self.make_environment(base)
            first = INSTALL.Installer(source, home, workspace)
            first.install()
            current = home / INSTALL.RUNTIME_CURRENT
            old_current = os.readlink(current)
            (source / "codex/README.md").write_text("new generation\n", encoding="utf-8")
            installer = INSTALL.Installer(source, home, workspace)

            def fail_before_switch(snapshot: Path) -> None:
                raise OSError("injected failure before current swap")

            installer._switch_current = fail_before_switch  # type: ignore[method-assign]
            with self.assertRaisesRegex(RuntimeError, "without rollback"):
                installer.install()
            self.assertEqual(os.readlink(current), old_current)
            self.assertEqual(os.readlink(codex_home / "AGENTS.md"), str(installer.runtime_current / "codex/AGENTS.global.md"))
            self.assertNotIn("max_depth", tomllib.loads((codex_home / "config.toml").read_text())["agents"])

    def test_migration_failure_before_current_preserves_all_legacy_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            shutil.copytree(ROOT, source)
            home, workspace, codex_home = self.make_environment(base)
            legacy = [
                (codex_home / "AGENTS.md", "codex/AGENTS.global.md"),
                (workspace / "AGENTS.md", "codex/AGENTS.workspace.md"),
                *((codex_home / "agents" / f"{role}.toml", f"codex/agents/{role}.toml") for role in INSTALL.ROLES),
                *((codex_home / "hooks" / hook, f"codex/hooks/{hook}") for hook in INSTALL.HOOK_FILES),
            ]
            (codex_home / "agents").mkdir()
            (codex_home / "skills").mkdir()
            (codex_home / "hooks").mkdir()
            for destination, relative in legacy:
                destination.symlink_to(source / relative, target_is_directory=destination.suffix == "" or destination.name == "research-execution-grill")
            original_targets = {destination: os.readlink(destination) for destination, _ in legacy}

            installer = INSTALL.Installer(source, home, workspace)

            def fail_before_pointer() -> None:
                raise OSError("injected pre-pointer failure")

            installer.configure_agents = fail_before_pointer  # type: ignore[method-assign]
            with self.assertRaisesRegex(RuntimeError, "without rollback"):
                installer.install()

            self.assertFalse((home / INSTALL.RUNTIME_CURRENT).is_symlink())
            for destination, _ in legacy:
                self.assertTrue(destination.is_symlink())
                self.assertEqual(os.readlink(destination), original_targets[destination])
                self.assertTrue(destination.resolve().exists())

    def test_per_link_replacement_failure_preserves_that_legacy_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            shutil.copytree(ROOT, source)
            home, workspace, codex_home = self.make_environment(base)
            failed_destination = workspace.resolve() / "AGENTS.md"
            failed_destination.symlink_to(source / "codex/AGENTS.workspace.md")
            original_target = os.readlink(failed_destination)
            installer = INSTALL.Installer(source, home, workspace)
            real_replace = INSTALL.os.replace

            def fail_one_link(staged: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
                if Path(destination) == failed_destination:
                    raise OSError("injected stable-link replacement failure")
                real_replace(staged, destination)

            INSTALL.os.replace = fail_one_link  # type: ignore[method-assign]
            try:
                with self.assertRaisesRegex(RuntimeError, "without rollback"):
                    installer.install()
            finally:
                INSTALL.os.replace = real_replace  # type: ignore[method-assign]

            self.assertTrue((home / INSTALL.RUNTIME_CURRENT).is_symlink())
            self.assertTrue(failed_destination.is_symlink())
            self.assertEqual(os.readlink(failed_destination), original_target)
            self.assertTrue(failed_destination.resolve().is_file())

    def test_lock_refuses_concurrent_install_and_releases_after_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home, workspace, codex_home = self.make_environment(base)
            ready = base / "ready"
            release = base / "release"
            module_path = str(SCRIPT)
            holder_code = f"""
import importlib.util
from pathlib import Path
import time
spec = importlib.util.spec_from_file_location('install_codex_runtime', {module_path!r})
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
installer = module.Installer(Path({str(ROOT)!r}), Path({str(home)!r}), Path({str(workspace)!r}))
with installer._install_lock():
    Path({str(ready)!r}).write_text('ready')
    while not Path({str(release)!r}).exists():
        time.sleep(0.02)
"""
            holder = subprocess.Popen([sys.executable, "-c", holder_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and holder.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.02)
                if not ready.exists():
                    stdout, stderr = holder.communicate(timeout=2)
                    self.fail(stderr or stdout or "lock holder did not start")
                blocked = subprocess.run(
                    [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--home", str(home), "--workspace", str(workspace)],
                    capture_output=True, text=True, check=False, timeout=5,
                )
                self.assertEqual(blocked.returncode, 2)
                self.assertIn("installer already in progress", blocked.stderr)
            finally:
                release.write_text("release")
                try:
                    holder.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    holder.kill()
                    holder.communicate(timeout=2)
            released = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--home", str(home), "--workspace", str(workspace)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(released.returncode, 0, released.stderr)

    def test_profiles_preserve_foreground_model_and_render_advisory_or_strict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            (codex_home / "config.toml").write_text(
                'model = "gpt-5.6-terra"\nmodel_reasoning_effort = "low"\nsandbox_mode = "read-only"\n\n[agents]\nenabled = false\nunrelated = "keep"\n',
                encoding="utf-8",
            )
            (codex_home / "hooks.json").write_text(json.dumps({"description": "user", "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "user-hook"}]}]}}))
            self.install(home, workspace)
            parsed = tomllib.loads((codex_home / "config.toml").read_text())
            self.assertEqual(parsed["model"], "gpt-5.6-terra")
            self.assertEqual(parsed["model_reasoning_effort"], "low")
            self.assertEqual(parsed["agents"]["unrelated"], "keep")
            self.assertEqual(parsed["agents"]["default_subagent_model"], "gpt-5.6-luna")
            self.assertEqual(parsed["agents"]["default_subagent_reasoning_effort"], "medium")
            self.assertEqual(parsed["agents"]["max_concurrent_threads_per_session"], 2)
            self.assertFalse(parsed["agents"]["enabled"])
            self.assertNotIn("max_depth", parsed["agents"])
            hooks = json.loads((codex_home / "hooks.json").read_text())
            self.assertIn("user-hook", json.dumps(hooks))
            self.assertIn("CODEX_ROUTER_ENFORCEMENT=advisory", json.dumps(hooks))
            self.assertFalse(any(INSTALL.Installer._is_router_registration(item, home) for item in hooks["hooks"]["Stop"]))
            self.assertNotEqual(hooks["hooks"]["PreToolUse"][-1]["matcher"], ".*")
            self.assertNotIn("functions\\.exec", hooks["hooks"]["PreToolUse"][-1]["matcher"])
            self.assertNotIn("functions\\.exec", hooks["hooks"]["PostToolUse"][-1]["matcher"])

            strict = INSTALL.Installer(ROOT, home, workspace, routing_profile="strict")
            strict.install()
            strict_hooks = json.loads((codex_home / "hooks.json").read_text())
            self.assertIn("CODEX_ROUTER_ENFORCEMENT=strict", json.dumps(strict_hooks))
            self.assertTrue(any(INSTALL.Installer._is_router_registration(item, home) for item in strict_hooks["hooks"]["Stop"]))
            self.assertEqual(strict_hooks["hooks"]["PreToolUse"][-1]["matcher"], ".*")
            self.assertIn("functions\\.exec", strict_hooks["hooks"]["PostToolUse"][-1]["matcher"])

    def test_named_foreground_profiles_set_only_the_requested_model_values(self) -> None:
        for profile, model in (("sol-supervisor", "gpt-5.6-sol"), ("terra-supervisor", "gpt-5.6-terra")):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                home, workspace, codex_home = self.make_environment(Path(directory))
                (codex_home / "config.toml").write_text('model = "gpt-4.1"\nsandbox_mode = "read-only"\n')
                self.install(home, workspace, profile=profile)
                parsed = tomllib.loads((codex_home / "config.toml").read_text())
                self.assertEqual(parsed["model"], model)
                self.assertEqual(parsed["model_reasoning_effort"], "high")
                self.assertEqual(parsed["sandbox_mode"], "read-only")

    def test_strict_preserve_rejects_incompatible_foreground_model_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            config = codex_home / "config.toml"
            original = 'model = "gpt-4.1-custom"\n'
            config.write_text(original)
            with self.assertRaisesRegex(ValueError, "incompatible foreground model"):
                INSTALL.Installer(ROOT, home, workspace, routing_profile="strict").install()
            self.assertEqual(config.read_text(), original)
            self.assertFalse((home / INSTALL.RUNTIME_CURRENT).exists())
            self.assertFalse((codex_home / "AGENTS.md").exists())

    def test_config_and_hooks_preserve_unrelated_data_and_managed_registration_is_unique(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            config = codex_home / "config.toml"
            config.write_text('model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n\n[telemetry]\nretained = "yes"\n\n[agents]\nmax_depth = 3\nunrelated = "preserve"\n')
            hooks = codex_home / "hooks.json"
            hooks.write_text(json.dumps({"description": "existing", "hooks": {"PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "existing-hook"}]},
                {"matcher": ".*", "hooks": [{"type": "command", "command": 'CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"'}]},
            ]}}))
            self.install(home, workspace)
            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed["telemetry"], {"retained": "yes"})
            self.assertEqual(parsed["agents"]["unrelated"], "preserve")
            self.assertNotIn("max_depth", parsed["agents"])
            merged = json.loads(hooks.read_text())
            self.assertIn("existing-hook", json.dumps(merged))
            self.assertEqual(sum(INSTALL.Installer._is_router_registration(item, home) for item in merged["hooks"]["PreToolUse"]), 1)

    def test_agents_section_migration_removes_basic_and_literal_quoted_legacy_keys(self) -> None:
        for quoted_key in ('"max_depth"', "'max_depth'"):
            with self.subTest(quoted_key=quoted_key), tempfile.TemporaryDirectory() as directory:
                home, workspace, codex_home = self.make_environment(Path(directory))
                config = codex_home / "config.toml"
                config.write_text(
                    f'# preserve this comment\n[agents]\n{quoted_key} = 3\nunrelated = "keep"\n',
                    encoding="utf-8",
                )

                self.install(home, workspace)

                rendered = config.read_text(encoding="utf-8")
                parsed = tomllib.loads(rendered)
                self.assertNotIn("max_depth", parsed["agents"])
                self.assertNotIn("enabled", parsed["agents"])
                self.assertEqual(parsed["agents"]["unrelated"], "keep")
                self.assertIn("# preserve this comment", rendered)

    def test_top_level_dotted_agents_migration_preserves_mode_unknown_keys_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            config = codex_home / "config.toml"
            config.write_text(
                '# preserve dotted mode\n'
                'agents.max_depth = 3\n'
                'agents.enabled = false\n'
                '# preserve unknown dotted key\n'
                'agents.unrelated = "keep"\n\n'
                '[telemetry]\nretained = "yes"\n',
                encoding="utf-8",
            )

            self.install(home, workspace)

            rendered = config.read_text(encoding="utf-8")
            parsed = tomllib.loads(rendered)
            self.assertEqual(parsed["telemetry"], {"retained": "yes"})
            self.assertNotIn("max_depth", parsed["agents"])
            self.assertFalse(parsed["agents"]["enabled"])
            self.assertEqual(parsed["agents"]["unrelated"], "keep")
            self.assertIn("# preserve dotted mode", rendered)
            self.assertIn("# preserve unknown dotted key", rendered)
            self.assertNotIn("[agents]", rendered)
            self.assertEqual(rendered.count("agents.enabled ="), 1)
            for key in (
                "default_subagent_model",
                "default_subagent_reasoning_effort",
                "max_concurrent_threads_per_session",
            ):
                self.assertRegex(rendered, rf"(?m)^agents\.{key} = ")

    def test_tampered_generation_is_rejected_and_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, _ = self.make_environment(Path(directory))
            installer = self.install(home, workspace)
            generation = installer.snapshot_path
            assert generation is not None
            target = generation / "codex/README.md"
            target.chmod(0o644)
            target.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "existing generation failed verification"):
                INSTALL.Installer(ROOT, home, workspace).prepare_snapshot()
            self.assertEqual(target.read_text(), "tampered\n")

    def test_dry_run_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home, workspace, _ = self.make_environment(base)
            before_home = sorted(path.relative_to(base) for path in base.rglob("*"))
            before_workspace = sorted(path.relative_to(workspace) for path in workspace.rglob("*"))
            installer = INSTALL.Installer(ROOT, home, workspace, dry_run=True)
            installer.install()
            self.assertEqual(before_home, sorted(path.relative_to(base) for path in base.rglob("*")))
            self.assertEqual(before_workspace, sorted(path.relative_to(workspace) for path in workspace.rglob("*")))
            self.assertFalse((home / INSTALL.INSTALL_LOCK).exists())
            self.assertTrue(installer.staged_config)
            self.assertTrue(installer.staged_hooks)

    def test_dry_run_rejects_regular_file_codex_home_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            workspace = base / "workspace"
            home.mkdir()
            workspace.mkdir()
            codex_home = home / ".codex"
            original = "preserve this file\n"
            codex_home.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unsafe install directory"):
                INSTALL.Installer(ROOT, home, workspace, dry_run=True).install()

            self.assertTrue(codex_home.is_file())
            self.assertEqual(codex_home.read_text(encoding="utf-8"), original)

    def test_late_atomic_write_failure_leaves_parseable_files_and_reports_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            self.install(home, workspace)
            config = codex_home / "config.toml"
            config.write_text('model = "gpt-5.6-sol"\n\n[agents]\nmax_depth = 3\n')
            hooks = codex_home / "hooks.json"
            old_hooks = hooks.read_text()
            installer = INSTALL.Installer(ROOT, home, workspace, routing_profile="strict")
            real_atomic = installer._atomic_text

            def fail_hooks(path: Path, content: str) -> None:
                if path == installer.hooks_path:
                    raise OSError("injected late atomic write failure")
                real_atomic(path, content)

            installer._atomic_text = fail_hooks  # type: ignore[method-assign]
            with self.assertRaisesRegex(RuntimeError, r"atomic write failed.*backup") as raised:
                installer.install()
            self.assertIn("hooks.json", str(raised.exception))
            self.assertNotIn("max_depth", tomllib.loads(config.read_text())["agents"])
            self.assertEqual(json.loads(hooks.read_text()), json.loads(old_hooks))
            backup_files = list(codex_home.glob("config.toml.backup-*"))
            self.assertTrue(backup_files)

            installer = INSTALL.Installer(ROOT, home, workspace, routing_profile="strict")
            installer.install()
            self.assertIn("CODEX_ROUTER_ENFORCEMENT=strict", hooks.read_text())

    def test_malformed_config_or_hooks_is_rejected_without_runtime_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home, workspace, codex_home = self.make_environment(Path(directory))
            hooks = codex_home / "hooks.json"
            hooks.write_text("not json")
            with self.assertRaises(ValueError):
                INSTALL.Installer(ROOT, home, workspace).install()
            self.assertEqual(hooks.read_text(), "not json")
            self.assertFalse((home / INSTALL.RUNTIME_CURRENT).exists())

    def test_preflight_rejects_unavailable_python_without_runtime_mutation(self) -> None:
        for case in ("missing", "not-executable", "not-python", "inside-source"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                source = base / "source"
                shutil.copytree(ROOT, source)
                home, workspace, codex_home = self.make_environment(base)
                config = codex_home / "config.toml"
                hooks = codex_home / "hooks.json"
                config.write_text('model = "gpt-5.6-terra"\n', encoding="utf-8")
                hooks.write_text(json.dumps({"description": "preserve", "hooks": {}}), encoding="utf-8")
                original_config = config.read_text(encoding="utf-8")
                original_hooks = hooks.read_text(encoding="utf-8")

                if case == "missing":
                    launcher = base / "missing-python3"
                elif case == "not-executable":
                    launcher = base / "python3"
                    launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                    launcher.chmod(0o644)
                elif case == "not-python":
                    launcher = base / "python3"
                    launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                    launcher.chmod(0o755)
                else:
                    launcher = source / "python3"
                    launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                    launcher.chmod(0o755)

                with self.assertRaisesRegex(ValueError, "Python launcher"):
                    INSTALL.Installer(source, home, workspace, python_launcher=launcher).install()

                self.assertEqual(config.read_text(encoding="utf-8"), original_config)
                self.assertEqual(hooks.read_text(encoding="utf-8"), original_hooks)
                self.assertFalse((home / INSTALL.RUNTIME_CURRENT).exists())
                self.assertFalse((codex_home / "AGENTS.md").exists())

    def test_nonstandard_python_name_is_idempotently_managed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home, workspace, codex_home = self.make_environment(base)
            launcher = base / "custom-runtime"
            launcher.write_text(
                "#!/bin/sh\nexec "
                + shlex.quote(str(Path(sys.executable).resolve()))
                + ' "$@"\n',
                encoding="utf-8",
            )
            launcher.chmod(0o755)

            for _ in range(2):
                self.install(
                    home,
                    workspace,
                    routing_profile="strict",
                    python_launcher=launcher,
                )

            hooks = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
            for event, registrations in hooks["hooks"].items():
                managed = [
                    registration
                    for registration in registrations
                    if INSTALL.Installer._is_router_registration(registration, home)
                ]
                self.assertEqual(len(managed), 1, event)
                command = managed[0]["hooks"][0]["command"]
                self.assertEqual(shlex.split(command)[1], str(launcher.resolve()))

    def test_hook_command_detection_keeps_unrelated_commands_and_quotes_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home with space"
            workspace = base / "workspace"
            (home / ".codex").mkdir(parents=True)
            workspace.mkdir()
            installer = self.install(home, workspace)
            hooks = json.loads((home / ".codex/hooks.json").read_text())
            command = hooks["hooks"]["PreToolUse"][-1]["hooks"][0]["command"]
            self.assertEqual(
                shlex.split(command),
                [
                    "CODEX_ROUTER_ENFORCEMENT=advisory",
                    str(installer.python_launcher),
                    str(home.resolve() / ".codex/hooks/weighted_cost_router.py"),
                ],
            )
            unrelated = {"hooks": [{"command": "python3 weighted_cost_router.py"}]}
            self.assertFalse(INSTALL.Installer._is_router_registration(unrelated))


if __name__ == "__main__":
    unittest.main()
