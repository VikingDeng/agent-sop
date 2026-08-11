#!/usr/bin/env python3
"""Install the repository-owned Codex adapter with an explicit model profile."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import stat
import sys
import tempfile
import tomllib
from typing import Any


ROLES = (
    "explorer",
    "focused_worker",
    "luna_executor",
    "sol_architect",
    "terra_debugger",
    "worker",
    "verifier",
    "reviewer",
    "risk_reviewer",
)
HOOK_FILES = ("weighted_cost_router.py", "weighted_routing_policy.py")
ROUTING_PROFILES = ("advisory", "strict")
DEFAULT_ROUTING_PROFILE = "advisory"
AGENT_SETTINGS = {
    "default_subagent_model": '"gpt-5.6-luna"',
    "default_subagent_reasoning_effort": '"medium"',
    "max_concurrent_threads_per_session": "2",
}
PROFILE_SETTINGS = {
    "preserve": {},
    "sol-supervisor": {"model": '"gpt-5.6-sol"', "model_reasoning_effort": '"high"'},
    "terra-supervisor": {"model": '"gpt-5.6-terra"', "model_reasoning_effort": '"high"'},
}
MANAGED_PYTHON_LAUNCHER = "/usr/bin/python3"
MANAGED_ROUTER_RELATIVE_PATH = Path(".codex/hooks/weighted_cost_router.py")
SNAPSHOT_ROOT = Path(".codex/runtime-snapshots")
RUNTIME_CURRENT = Path(".codex/runtime-current")
SNAPSHOT_MANIFEST = "snapshot-manifest.json"
INSTALL_LOCK = Path(".codex/install.lock")

SNAPSHOT_FILES = (
    "PRINCIPLES.md",
    "PROSE_STANDARD.md",
    "SKILL-ADAPTERS.md",
    "skill-registry.yaml",
    "codex/AGENTS.global.md",
    "codex/AGENTS.workspace.md",
    "codex/CODEX-ADAPTER.md",
    "codex/README.md",
    "codex/ROUTING_ACCEPTANCE.md",
    "codex/hooks/hooks.json",
    "codex/hooks/weighted_cost_router.py",
    "codex/hooks/weighted_routing_policy.py",
    *(f"codex/agents/{role}.toml" for role in ROLES),
    "sop/tier0-core/autonomous-supervisor.md",
    "sop/tier0-core/add-dependency.md",
    "sop/tier0-core/build-oracle.md",
    "sop/tier0-core/commit-and-pr.md",
    "sop/tier0-core/lock-env.md",
    "sop/tier0-core/no-fallback-review.md",
    "sop/tier0-core/profile-code.md",
    "sop/tier0-core/reproduce-result.md",
    "sop/tier1-skeleton/build-local-proxy.md",
    "sop/tier1-skeleton/drift-check.md",
    "sop/tier1-skeleton/maintain-patch-series.md",
    "sop/tier1-skeleton/package-submission.md",
    "sop/tier1-skeleton/research-execution-grill.md",
    "sop/tier1-skeleton/references/research-execution-grill-artifact.md",
    "sop/tier1-skeleton/references/research-evidence-presentation.md",
    "sop/tier1-skeleton/references/statistics-redlines.md",
    "sop/tier1-skeleton/run-competition.md",
    "sop/tier1-skeleton/run-development.md",
    "sop/tier1-skeleton/run-experiment.md",
    "sop/tier1-skeleton/statistics-oracle.md",
    "sop/tier1-skeleton/write-contract.md",
    "sop/tier2-activity/ops-remote-compute.md",
    "scripts/validate_research_execution_grill.py",
    "scripts/research_grill_state_machine.py",
    "skeletons/contestos-adaptive-overlay-v2.md",
)
RETIRED_MANAGED_LINKS = (Path(".codex/skills/research-execution-grill"),)
SUPPORTED_MODEL_FAMILIES = ("sol", "terra", "luna")


class Installer:
    def __init__(
        self,
        repo_root: Path,
        home: Path,
        workspace: Path,
        dry_run: bool = False,
        profile: str = "preserve",
        routing_profile: str = DEFAULT_ROUTING_PROFILE,
    ):
        self.repo_root = repo_root.resolve()
        self.home = home.resolve()
        self.workspace = workspace.resolve()
        if profile not in PROFILE_SETTINGS:
            raise ValueError(f"unknown installer profile: {profile}")
        if routing_profile not in ROUTING_PROFILES:
            raise ValueError(f"unknown routing profile: {routing_profile}")
        self.dry_run = dry_run
        self.profile = profile
        self.routing_profile = routing_profile
        self.stamp = (
            f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}-"
            f"{os.getpid()}-{secrets.token_hex(8)}"
        )
        self.actions: list[str] = []
        self.backups: list[Path] = []
        self.staged_config = ""
        self.staged_hooks = ""
        self.snapshot_path: Path | None = None
        self.snapshot_files: tuple[Path, ...] = ()
        self.current_swapped = False

        codex_home = self.home / ".codex"
        self.config_path = codex_home / "config.toml"
        self.hooks_path = codex_home / "hooks.json"
        self.runtime_current = self.home / RUNTIME_CURRENT

    def _record(self, message: str) -> None:
        self.actions.append(message)

    @staticmethod
    def _exists(path: Path) -> bool:
        return path.exists() or path.is_symlink()

    @staticmethod
    def _remove(path: Path) -> None:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)

    def _reject_symlink_parents(self, path: Path) -> None:
        roots = (self.home, self.workspace)
        current = path.parent
        while True:
            if current.is_symlink():
                raise ValueError(f"unsafe install path through symlink: {path}")
            if current in roots:
                return
            if current == current.parent:
                raise ValueError(f"unsafe install path: {path}")
            current = current.parent

    def _ensure_codex_home(self) -> None:
        codex_home = self.home / ".codex"
        if self.dry_run and not self._exists(codex_home):
            return
        try:
            if not self.dry_run:
                codex_home.mkdir()
        except FileExistsError:
            pass
        try:
            mode = codex_home.lstat().st_mode
        except FileNotFoundError as exc:
            raise ValueError(f"unable to create install directory: {codex_home}") from exc
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ValueError(f"unsafe install directory: {codex_home}")

    def _backup(self, destination: Path) -> Path:
        candidate = destination.with_name(f"{destination.name}.backup-{self.stamp}")
        suffix = 1
        while self._exists(candidate):
            candidate = destination.with_name(f"{destination.name}.backup-{self.stamp}-{suffix}")
            suffix += 1
        self._record(f"backup {destination} -> {candidate}")
        if self.dry_run:
            return candidate
        self._reject_symlink_parents(candidate)
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            candidate.symlink_to(os.readlink(destination), target_is_directory=destination.resolve().is_dir())
        elif destination.is_dir():
            shutil.copytree(destination, candidate, symlinks=True)
        else:
            shutil.copy2(destination, candidate)
        self.backups.append(candidate)
        return candidate

    @contextmanager
    def _install_lock(self):
        """Hold one non-blocking per-home lock across every real install write."""
        if self.dry_run:
            yield
            return

        codex_home = self.home / ".codex"
        try:
            mode = codex_home.lstat().st_mode
        except FileNotFoundError as exc:
            raise ValueError(f"unsafe install lock parent: {codex_home}") from exc
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ValueError(f"unsafe install lock parent: {codex_home}")

        lock_path = self.home / INSTALL_LOCK
        try:
            mode = lock_path.lstat().st_mode
        except FileNotFoundError:
            mode = None
        if mode is not None and (stat.S_ISLNK(mode) or not stat.S_ISREG(mode)):
            raise ValueError(f"unsafe install lock path: {lock_path}")

        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(lock_path, flags, 0o600)
        except OSError as exc:
            raise ValueError(f"unable to open install lock: {lock_path}: {exc}") from exc
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError(f"unsafe install lock path: {lock_path}")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError(f"installer already in progress: {lock_path}") from exc
            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    @staticmethod
    def _model_family(model: str) -> str | None:
        lowered = model.strip().lower()
        for family in SUPPORTED_MODEL_FAMILIES:
            if re.search(rf"(?:^|[-_.:/]){re.escape(family)}(?:$|[-_.:/])", lowered):
                return family
        return None

    def _snapshot_source_paths(self) -> tuple[Path, ...]:
        return tuple(self.repo_root / relative for relative in SNAPSHOT_FILES)

    @staticmethod
    def _snapshot_digest(sources: tuple[Path, ...]) -> tuple[str, dict[str, str]]:
        file_hashes: dict[str, str] = {}
        digest = hashlib.sha256()
        for relative, source in zip(SNAPSHOT_FILES, sources):
            content = source.read_bytes()
            file_hashes[relative] = hashlib.sha256(content).hexdigest()
            path_bytes = relative.encode("utf-8")
            digest.update(len(path_bytes).to_bytes(4, "big"))
            digest.update(path_bytes)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        return digest.hexdigest(), file_hashes

    @classmethod
    def _snapshot_is_verified(
        cls,
        path: Path,
        file_hashes: dict[str, str],
        *,
        content_address: str | None = None,
    ) -> bool:
        manifest_path = path / SNAPSHOT_MANIFEST
        if not path.is_dir() or path.is_symlink() or not manifest_path.is_file() or manifest_path.is_symlink():
            return False
        expected_address = content_address or path.name
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema_version") != 1
            or manifest.get("content_address") != expected_address
            or manifest.get("files") != file_hashes
        ):
            return False

        expected_files = {Path(SNAPSHOT_MANIFEST), *(Path(relative) for relative in file_hashes)}
        expected_entries = set(expected_files)
        for entry in expected_files:
            expected_entries.update(entry.parents)
        expected_entries.discard(Path("."))
        for candidate in path.rglob("*"):
            relative = candidate.relative_to(path)
            if relative not in expected_entries or candidate.is_symlink():
                return False
            mode = candidate.stat().st_mode
            if mode & 0o222 or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                return False
        if path.stat().st_mode & 0o222:
            return False
        for relative, expected_hash in file_hashes.items():
            candidate = path / relative
            if not candidate.is_file() or candidate.is_symlink():
                return False
            try:
                actual_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
            except OSError:
                return False
            if actual_hash != expected_hash:
                return False
        return True

    @staticmethod
    def _lock_snapshot(path: Path, sources: tuple[Path, ...]) -> None:
        for relative, source in zip(SNAPSHOT_FILES, sources):
            destination = path / relative
            os.chmod(destination, 0o444 | (source.stat().st_mode & 0o111))
        for directory in sorted((candidate for candidate in path.rglob("*") if candidate.is_dir()), reverse=True):
            os.chmod(directory, 0o555)
        os.chmod(path, 0o555)
        os.chmod(path / SNAPSHOT_MANIFEST, 0o444)

    def _runtime_components(self, file_hashes: dict[str, str]) -> dict[str, Any]:
        component_paths = {
            "kernel": "sop/tier0-core/autonomous-supervisor.md",
            "codex_adapter": "codex/CODEX-ADAPTER.md",
            "development_profile": "sop/tier1-skeleton/run-development.md",
            "research_profile": "sop/tier1-skeleton/research-execution-grill.md",
            "competition_profile": "sop/tier1-skeleton/run-competition.md",
            "statistics_oracle": "sop/tier1-skeleton/statistics-oracle.md",
        }
        components: dict[str, Any] = {}
        for name, relative in component_paths.items():
            text = (self.repo_root / relative).read_text(encoding="utf-8")
            match = re.search(r"^- \*\*版本\*\*:\s*([^\n]+)$", text, re.MULTILINE)
            components[name] = {
                "path": relative,
                "version": match.group(1).strip() if match else "UNKNOWN",
                "sha256": file_hashes[relative],
            }
        registry = json.loads((self.repo_root / "skill-registry.yaml").read_text(encoding="utf-8"))
        components["skill_registry"] = {
            "path": "skill-registry.yaml",
            "schema_version": registry.get("schema_version", "UNKNOWN"),
            "sha256": file_hashes["skill-registry.yaml"],
        }
        return components

    def prepare_snapshot(self) -> Path:
        sources = self._snapshot_source_paths()
        missing = [str(path) for path in sources if not path.is_file() or path.is_symlink()]
        if missing:
            raise ValueError("missing snapshot source(s): " + ", ".join(missing))
        digest, file_hashes = self._snapshot_digest(sources)
        snapshot_root = self.home / SNAPSHOT_ROOT
        if snapshot_root.is_symlink() or (snapshot_root.exists() and not snapshot_root.is_dir()):
            raise ValueError(f"unsafe snapshot root: {snapshot_root}")
        target = snapshot_root / f"sha256-{digest}"
        self.snapshot_files = sources
        self.snapshot_path = target
        if self._snapshot_is_verified(target, file_hashes):
            self._record(f"reuse verified immutable generation {target}")
            return target
        if self._exists(target):
            raise ValueError(f"existing generation failed verification: {target}")
        self._record(f"create immutable generation {target}")
        if self.dry_run:
            return target

        snapshot_root.mkdir(parents=True, exist_ok=True)
        staging: Path | None = Path(tempfile.mkdtemp(prefix=".staging-", dir=snapshot_root))
        try:
            for relative, source in zip(SNAPSHOT_FILES, sources):
                destination = staging / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            manifest = {
                "schema_version": 1,
                "content_address": f"sha256-{digest}",
                "files": file_hashes,
                "runtime_components": self._runtime_components(file_hashes),
            }
            self._atomic_text(staging / SNAPSHOT_MANIFEST, json.dumps(manifest, sort_keys=True, indent=2) + "\n")
            self._lock_snapshot(staging, sources)
            if not self._snapshot_is_verified(staging, file_hashes, content_address=f"sha256-{digest}"):
                raise ValueError("staged immutable generation failed verification")
            if self._exists(target):
                raise ValueError(f"generation appeared during install: {target}")
            os.replace(staging, target)
            staging = None
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging)
        return target

    @staticmethod
    def _replace_section_values(
        text: str,
        section: str,
        settings: dict[str, str],
        remove_keys: tuple[str, ...] = (),
    ) -> str:
        lines = text.splitlines()
        header = re.compile(rf"^\s*\[{re.escape(section)}\]\s*(?:#.*)?$")
        def key_pattern(key: str) -> str:
            escaped = re.escape(key)
            return rf"(?:{escaped}|\"{escaped}\"|'{escaped}')"

        top_level_end = next(
            (index for index, line in enumerate(lines) if re.match(r"^\s*\[", line)),
            len(lines),
        )
        dotted_key = re.compile(
            rf"^\s*{re.escape(section)}\.(?:[A-Za-z0-9_-]+|\"[^\"]+\"|'[^']+')\s*="
        )
        if any(dotted_key.match(line) for line in lines[:top_level_end]):
            for key in remove_keys:
                pattern = re.compile(rf"^\s*{re.escape(section)}\.{key_pattern(key)}\s*=")
                lines = [
                    line
                    for index, line in enumerate(lines)
                    if not (index < top_level_end and pattern.match(line))
                ]
                top_level_end = next(
                    (index for index, line in enumerate(lines) if re.match(r"^\s*\[", line)),
                    len(lines),
                )

            for key, value in settings.items():
                pattern = re.compile(rf"^\s*{re.escape(section)}\.{key_pattern(key)}\s*=")
                existing = next(
                    (index for index in range(top_level_end) if pattern.match(lines[index])),
                    None,
                )
                rendered = f"{section}.{key} = {value}"
                if existing is None:
                    lines.insert(top_level_end, rendered)
                    top_level_end += 1
                else:
                    lines[existing] = rendered
            return "\n".join(lines) + "\n"

        try:
            start = next(index for index, line in enumerate(lines) if header.match(line))
            end = next(
                (index for index in range(start + 1, len(lines)) if re.match(r"^\s*\[", lines[index])),
                len(lines),
            )
        except StopIteration:
            if lines and lines[-1].strip():
                lines.append("")
            start = len(lines)
            lines.append(f"[{section}]")
            end = len(lines)

        for key in remove_keys:
            pattern = re.compile(rf"^\s*{key_pattern(key)}\s*=")
            lines = [
                line
                for index, line in enumerate(lines)
                if not (start < index < end and pattern.match(line))
            ]
            end = next(
                (index for index in range(start + 1, len(lines)) if re.match(r"^\s*\[", lines[index])),
                len(lines),
            )

        for key, value in settings.items():
            pattern = re.compile(rf"^\s*{key_pattern(key)}\s*=")
            existing = next((index for index in range(start + 1, end) if pattern.match(lines[index])), None)
            rendered = f"{key} = {value}"
            if existing is None:
                lines.insert(end, rendered)
                end += 1
            else:
                lines[existing] = rendered
        return "\n".join(lines) + "\n"

    @staticmethod
    def _replace_top_level_values(text: str, settings: dict[str, str]) -> str:
        if not settings:
            return text
        lines = text.splitlines()
        end = next((index for index, line in enumerate(lines) if re.match(r"^\s*\[", line)), len(lines))
        for key, value in settings.items():
            pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
            existing = next((index for index in range(end) if pattern.match(lines[index])), None)
            rendered = f"{key} = {value}"
            if existing is None:
                lines.insert(end, rendered)
                end += 1
            else:
                lines[existing] = rendered
        return "\n".join(lines) + "\n"

    @staticmethod
    def _hook_command(entry: Any, home: Path, routing_profile: str = DEFAULT_ROUTING_PROFILE) -> Any:
        if isinstance(entry, dict):
            return {key: Installer._hook_command(value, home, routing_profile) for key, value in entry.items()}
        if isinstance(entry, list):
            return [Installer._hook_command(value, home, routing_profile) for value in entry]
        if isinstance(entry, str):
            try:
                words = shlex.split(entry)
            except ValueError:
                return entry
            if len(words) not in {2, 3}:
                return entry
            if len(words) == 3 and words[1] == MANAGED_PYTHON_LAUNCHER and words[0].startswith("CODEX_ROUTER_ENFORCEMENT="):
                if words[0].split("=", 1)[1].lower() not in ROUTING_PROFILES:
                    return entry
                words.pop(0)
            if len(words) != 2 or words[0] != MANAGED_PYTHON_LAUNCHER:
                return entry
            if words[1] not in {"$HOME/.codex/hooks/weighted_cost_router.py", str(home / MANAGED_ROUTER_RELATIVE_PATH)}:
                return entry
            runtime_hook = shlex.quote(str(home / MANAGED_ROUTER_RELATIVE_PATH))
            return f"CODEX_ROUTER_ENFORCEMENT={routing_profile} {MANAGED_PYTHON_LAUNCHER} {runtime_hook}"
        return entry

    @staticmethod
    def _is_managed_router_command(command: str, home: Path | None = None) -> bool:
        try:
            words = shlex.split(command)
        except ValueError:
            return False
        if words and words[0].startswith("CODEX_ROUTER_ENFORCEMENT="):
            if words[0].split("=", 1)[1].lower() not in ROUTING_PROFILES:
                return False
            words.pop(0)
        if len(words) != 2 or words[0] != MANAGED_PYTHON_LAUNCHER:
            return False
        managed_paths = {"$HOME/.codex/hooks/weighted_cost_router.py"}
        if home is not None:
            managed_paths.add(str(home.resolve() / MANAGED_ROUTER_RELATIVE_PATH))
        return words[1] in managed_paths

    @staticmethod
    def _is_router_registration(registration: Any, home: Path | None = None) -> bool:
        if not isinstance(registration, dict):
            return False
        return any(
            isinstance(hook, dict)
            and isinstance(hook.get("command"), str)
            and Installer._is_managed_router_command(hook["command"], home)
            for hook in registration.get("hooks", [])
        )

    @staticmethod
    def _without_managed_router_commands(registration: Any, home: Path) -> Any:
        if not isinstance(registration, dict):
            return registration
        retained = dict(registration)
        retained["hooks"] = [
            hook for hook in registration.get("hooks", [])
            if not (
                isinstance(hook, dict)
                and isinstance(hook.get("command"), str)
                and Installer._is_managed_router_command(hook["command"], home)
            )
        ]
        return retained

    @staticmethod
    def _validate_hook_shape(payload: Any, label: str) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("hooks"), dict):
            raise ValueError(f"{label} has an unexpected hooks shape")
        for event, registrations in payload["hooks"].items():
            if not isinstance(event, str) or not isinstance(registrations, list):
                raise ValueError(f"{label} event registrations must be lists")
            for registration in registrations:
                if not isinstance(registration, dict) or not isinstance(registration.get("hooks"), list):
                    raise ValueError(f"{label} contains a malformed {event} registration")

    def _profile_hook_source(self, source: dict[str, Any]) -> dict[str, Any]:
        """Reduce advisory instrumentation to lifecycle-relevant events.

        Strict mode retains the repository policy verbatim because it is an
        explicitly selected enforcement profile.  Advisory mode records
        provenance and observes sub-agent lifecycle/routing calls without
        paying a Python process launch on every unrelated tool and Stop.
        """
        if self.routing_profile == "strict":
            return source
        profiled = json.loads(json.dumps(source))
        profiled["hooks"]["Stop"] = []
        for registration in profiled["hooks"].get("PreToolUse", []):
            registration["matcher"] = (
                "Agent|spawn_agent|create_agent|resume_agent|close_agent|"
                "multi_agent_v1__spawn_agent|multi_agent_v1__create_agent|"
                "multi_agent_v1__close_agent"
            )
        for registration in profiled["hooks"].get("PostToolUse", []):
            registration["matcher"] = (
                "Agent|spawn_agent|create_agent|close_agent|"
                "multi_agent_v1__spawn_agent|multi_agent_v1__create_agent|"
                "multi_agent_v1__close_agent"
            )
        return profiled

    def _render_hooks(self) -> str:
        source = json.loads((self.repo_root / "codex/hooks/hooks.json").read_text(encoding="utf-8"))
        source = self._hook_command(source, self.home, self.routing_profile)
        source = self._profile_hook_source(source)
        self._validate_hook_shape(source, "repository hooks.json")
        if self.hooks_path.is_symlink():
            raise ValueError(f"refusing to modify symlink {self.hooks_path}")
        if self.hooks_path.exists():
            try:
                current = json.loads(self.hooks_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"refusing to modify malformed {self.hooks_path}: {exc}") from exc
            self._validate_hook_shape(current, str(self.hooks_path))
        else:
            current = {"description": "Merged local Codex hooks", "hooks": {}}

        merged = json.loads(json.dumps(current))
        for event, registrations in source["hooks"].items():
            existing = merged["hooks"].setdefault(event, [])
            retained = []
            for item in existing:
                filtered = self._without_managed_router_commands(item, self.home)
                if not isinstance(filtered, dict) or filtered.get("hooks"):
                    retained.append(filtered)
            existing[:] = retained
            existing.extend(registrations)
        self._validate_hook_shape(merged, "staged hooks.json")
        return json.dumps(merged, ensure_ascii=False, indent=2) + "\n"

    def preflight(self) -> None:
        sources = self._snapshot_source_paths()
        missing = [str(path) for path in sources if not path.is_file() or path.is_symlink()]
        if missing:
            raise ValueError("missing installation source(s): " + ", ".join(missing))
        if self.config_path.is_symlink():
            raise ValueError(f"refusing to modify symlink {self.config_path}")
        original_config = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else ""
        try:
            parsed_config = tomllib.loads(original_config)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"refusing to modify malformed {self.config_path}: {exc}") from exc
        preserved_model = parsed_config.get("model")
        if self.routing_profile == "strict" and self.profile == "preserve" and preserved_model is not None:
            if not isinstance(preserved_model, str) or self._model_family(preserved_model) is None:
                raise ValueError(
                    "strict routing profile cannot preserve an incompatible foreground model; "
                    "select --profile sol-supervisor or terra-supervisor, or install with --routing-profile advisory"
                )
        staged = self._replace_top_level_values(original_config, PROFILE_SETTINGS[self.profile])
        self.staged_config = self._replace_section_values(
            staged,
            "agents",
            AGENT_SETTINGS,
            remove_keys=("max_depth",),
        )
        try:
            tomllib.loads(self.staged_config)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"staged config.toml is invalid: {exc}") from exc
        self.staged_hooks = self._render_hooks()
        json.loads(self.staged_hooks)

    @staticmethod
    def _atomic_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
                handle.write(content)
                temporary = Path(handle.name)
            os.replace(temporary, path)
            temporary = None
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def _write_staged(self, destination: Path, content: str, description: str) -> None:
        original = destination.read_text(encoding="utf-8") if destination.exists() else ""
        if content == original and not destination.is_symlink():
            self._record(f"unchanged {destination}")
            return
        backup = self._backup(destination) if self._exists(destination) else None
        self._record(description)
        if self.dry_run:
            return
        try:
            self._atomic_text(destination, content)
        except BaseException as exc:
            backup_text = str(backup) if backup is not None else "no prior file"
            raise RuntimeError(f"atomic write failed for {destination}; backup: {backup_text}") from exc

    def configure_agents(self) -> None:
        self._write_staged(
            self.config_path,
            self.staged_config,
            f"configure profile={self.profile} and [agents] in {self.config_path}",
        )

    def merge_hooks(self) -> None:
        self._write_staged(
            self.hooks_path,
            self.staged_hooks,
            f"merge weighted router registrations into {self.hooks_path}",
        )

    def _stable_links(self, snapshot: Path) -> tuple[tuple[Path, Path], ...]:
        current = self.runtime_current
        codex_home = self.home / ".codex"
        links = [
            (codex_home / "AGENTS.md", current / "codex/AGENTS.global.md"),
            (self.workspace / "AGENTS.md", current / "codex/AGENTS.workspace.md"),
            *(
                (codex_home / "agents" / f"{role}.toml", current / "codex/agents" / f"{role}.toml")
                for role in ROLES
            ),
            *(
                (codex_home / "hooks" / hook_file, current / "codex/hooks" / hook_file)
                for hook_file in HOOK_FILES
            ),
        ]
        # The argument keeps the call site explicit: every target must be in the
        # verified generation before its stable link is prepared.
        if not self.dry_run and not self._snapshot_is_verified(snapshot, self._snapshot_hashes(snapshot)):
            raise ValueError(f"generation failed verification before linking: {snapshot}")
        return tuple(links)

    def _retire_obsolete_links(self) -> None:
        """Remove only legacy symlinks that this adapter can identify as its own."""
        for relative in RETIRED_MANAGED_LINKS:
            destination = self.home / relative
            if not destination.is_symlink():
                continue
            raw_target = os.readlink(destination)
            target = (destination.parent / raw_target).resolve() if not Path(raw_target).is_absolute() else Path(raw_target).resolve()
            recognized_targets = {
                (self.runtime_current / "codex/skills/research-execution-grill").resolve(strict=False),
                (self.repo_root / "codex/skills/research-execution-grill").resolve(strict=False),
            }
            # A stable link through runtime-current resolves into the active
            # generation, so compare its literal form as well as resolved paths.
            stable_literal = str(self.runtime_current / "codex/skills/research-execution-grill")
            if target not in recognized_targets and raw_target != stable_literal:
                self._record(f"preserve unrecognized retired-link target {destination} -> {raw_target}")
                continue
            self._backup(destination)
            self._record(f"retire obsolete managed link {destination}")
            if not self.dry_run:
                destination.unlink()

    def _current_generation_is_valid(self) -> bool:
        if not self.runtime_current.is_symlink():
            return False
        try:
            current = self.runtime_current.resolve(strict=True)
            file_hashes = self._snapshot_hashes(current)
            return self._snapshot_is_verified(current, file_hashes)
        except (OSError, RuntimeError, KeyError, TypeError, json.JSONDecodeError):
            return False

    @staticmethod
    def _snapshot_hashes(path: Path) -> dict[str, str]:
        manifest = json.loads((path / SNAPSHOT_MANIFEST).read_text(encoding="utf-8"))
        return manifest["files"]

    def _prepare_stable_links(self, snapshot: Path) -> None:
        for destination, target in self._stable_links(snapshot):
            if destination.is_symlink() and os.readlink(destination) == str(target):
                self._record(f"unchanged {destination}")
                continue
            if self._exists(destination):
                self._backup(destination)
            self._reject_symlink_parents(destination)
            self._record(f"prepare stable link {destination} -> {target}")
            if self.dry_run:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(f".{destination.name}.link-{self.stamp}")
            try:
                temporary.symlink_to(
                    target,
                    target_is_directory=target.suffix == "" or target.name == "research-execution-grill",
                )
                os.replace(temporary, destination)
            finally:
                if temporary.is_symlink():
                    temporary.unlink()

    def _switch_current(self, snapshot: Path) -> None:
        if self.runtime_current.is_symlink() and self.runtime_current.resolve() == snapshot.resolve():
            self._record(f"current generation unchanged {self.runtime_current}")
            self.current_swapped = True
            return
        if self._exists(self.runtime_current) and not self.runtime_current.is_symlink():
            raise ValueError(f"unsafe runtime-current path: {self.runtime_current}")
        self._record(f"switch {self.runtime_current} -> {snapshot}")
        if self.dry_run:
            return
        self.runtime_current.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.runtime_current.with_name(f".runtime-current-{self.stamp}")
        try:
            temporary.symlink_to(snapshot)
            os.replace(temporary, self.runtime_current)
            self.current_swapped = True
        finally:
            if temporary.is_symlink():
                temporary.unlink()

    def install(self) -> None:
        self._ensure_codex_home()
        with self._install_lock():
            self.preflight()
            snapshot = self.prepare_snapshot()
            current_is_valid = self._current_generation_is_valid()
            try:
                if current_is_valid:
                    self._prepare_stable_links(snapshot)
                self.configure_agents()
                self.merge_hooks()
                self._switch_current(snapshot)
                if not current_is_valid:
                    self._prepare_stable_links(snapshot)
                self._retire_obsolete_links()
            except BaseException as exc:
                backups = ", ".join(str(path) for path in self.backups) or "none"
                raise RuntimeError(
                    "installation stopped without rollback; valid atomic writes were retained; "
                    f"backups: {backups}; rerun to converge; cause: {exc}"
                ) from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.home(),
        help="workspace root that receives the lightweight AGENTS.md overlay (default: current home)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--profile",
        choices=tuple(PROFILE_SETTINGS),
        default="preserve",
        help="configuration profile; preserve leaves the foreground model unchanged",
    )
    parser.add_argument(
        "--routing-profile",
        choices=ROUTING_PROFILES,
        default=DEFAULT_ROUTING_PROFILE,
        help="Hook enforcement profile; advisory is the adaptive default",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    installer = Installer(
        args.repo_root,
        args.home,
        args.workspace,
        dry_run=args.dry_run,
        profile=args.profile,
        routing_profile=args.routing_profile,
    )
    try:
        installer.install()
    except BaseException as exc:
        if installer.actions:
            print("\n".join(installer.actions), file=sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print("\n".join(installer.actions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
