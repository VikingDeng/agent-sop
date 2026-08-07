#!/usr/bin/env python3
"""Install the repository-owned Codex adapter without changing the main model."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import tempfile
import tomllib
from typing import Any


ROLES = ("explorer", "focused_worker", "luna_executor", "worker", "verifier", "reviewer", "risk_reviewer")
HOOK_FILES = ("weighted_cost_router.py", "weighted_routing_policy.py")
AGENT_SETTINGS = {
    "default_subagent_model": '"gpt-5.6-luna"',
    "default_subagent_reasoning_effort": '"medium"',
    "max_concurrent_threads_per_session": "2",
    "max_depth": "1",
}


@dataclass(frozen=True)
class Mutation:
    destination: Path
    backup: Path | None


class Installer:
    def __init__(self, repo_root: Path, home: Path, workspace: Path, dry_run: bool = False):
        self.repo_root = repo_root.resolve()
        self.home = home.resolve()
        self.workspace = workspace.resolve()
        self.dry_run = dry_run
        self.stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.actions: list[str] = []
        self.mutations: list[Mutation] = []
        self.config_path = self.home / ".codex" / "config.toml"
        self.hooks_path = self.home / ".codex" / "hooks.json"
        self.staged_config = ""
        self.staged_hooks = ""
        self.manifest_path = self.home / ".codex" / "install-rollback" / f"{self.stamp}.json"

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

    def _backup(self, destination: Path) -> Path:
        candidate = destination.with_name(f"{destination.name}.backup-{self.stamp}")
        suffix = 1
        while self._exists(candidate):
            candidate = destination.with_name(f"{destination.name}.backup-{self.stamp}-{suffix}")
            suffix += 1
        self._record(f"backup {destination} -> {candidate}")
        if self.dry_run:
            return candidate
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            candidate.symlink_to(os.readlink(destination))
        elif destination.is_dir():
            shutil.copytree(destination, candidate)
        else:
            shutil.copy2(destination, candidate)
        return candidate

    def _begin_mutation(self, destination: Path) -> None:
        backup = self._backup(destination) if self._exists(destination) else None
        self.mutations.append(Mutation(destination, backup))
        self._record(f"rollback-entry {destination} <- {backup or '[absent]'}")
        self._persist_manifest("in_progress")

    def _persist_manifest(self, status: str, errors: list[str] | None = None) -> None:
        if self.dry_run or not self.mutations:
            return
        payload = {
            "schema_version": 1,
            "status": status,
            "created_at": self.stamp,
            "mutations": [
                {"destination": str(item.destination), "backup": str(item.backup) if item.backup else None}
                for item in self.mutations
            ],
            "errors": errors or [],
        }
        self._atomic_text(self.manifest_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def _restore(self, mutation: Mutation) -> None:
        destination, backup = mutation.destination, mutation.backup
        self._remove(destination)
        if backup is None:
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        if backup.is_symlink():
            destination.symlink_to(os.readlink(backup))
        elif backup.is_dir():
            shutil.copytree(backup, destination)
        else:
            shutil.copy2(backup, destination)

    def rollback(self) -> list[str]:
        errors: list[str] = []
        if self.dry_run:
            return errors
        for mutation in reversed(self.mutations):
            try:
                self._restore(mutation)
                self._record(f"rolled-back {mutation.destination}")
            except OSError as exc:
                errors.append(f"{mutation.destination}: {exc}")
        self._persist_manifest("rollback_failed" if errors else "rolled_back", errors)
        return errors

    def link(self, source: Path, destination: Path) -> None:
        source = source.resolve()
        if not source.exists():
            raise ValueError(f"missing source: {source}")
        if destination.is_symlink() and destination.resolve() == source:
            self._record(f"unchanged {destination}")
            return
        self._begin_mutation(destination)
        self._record(f"link {destination} -> {source}")
        if self.dry_run:
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._remove(destination)
        destination.symlink_to(source, target_is_directory=source.is_dir())

    @staticmethod
    def _replace_section_values(text: str, section: str, settings: dict[str, str]) -> str:
        lines = text.splitlines()
        header = re.compile(rf"^\s*\[{re.escape(section)}\]\s*(?:#.*)?$")
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

        for key, value in settings.items():
            pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
            existing = next((index for index in range(start + 1, end) if pattern.match(lines[index])), None)
            rendered = f"{key} = {value}"
            if existing is None:
                lines.insert(end, rendered)
                end += 1
            else:
                lines[existing] = rendered
        return "\n".join(lines) + "\n"

    @staticmethod
    def _hook_command(entry: Any, home: Path) -> Any:
        if isinstance(entry, dict):
            return {key: Installer._hook_command(value, home) for key, value in entry.items()}
        if isinstance(entry, list):
            return [Installer._hook_command(value, home) for value in entry]
        if isinstance(entry, str):
            runtime_hook = shlex.quote(str(home / ".codex" / "hooks" / "weighted_cost_router.py"))
            return entry.replace('"$HOME/.codex/hooks/weighted_cost_router.py"', runtime_hook)
        return entry

    @staticmethod
    def _is_router_registration(registration: Any) -> bool:
        if not isinstance(registration, dict):
            return False
        for hook in registration.get("hooks", []):
            if not isinstance(hook, dict) or not isinstance(hook.get("command"), str):
                continue
            try:
                words = shlex.split(hook["command"])
            except ValueError:
                continue
            if (
                len(words) >= 2
                and Path(words[0]).name in {"python", "python3"}
                and Path(words[1]).name == "weighted_cost_router.py"
            ):
                return True
        return False

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

    def _render_hooks(self) -> str:
        source = json.loads((self.repo_root / "codex" / "hooks" / "hooks.json").read_text())
        source = self._hook_command(source, self.home)
        self._validate_hook_shape(source, "repository hooks.json")
        if self.hooks_path.exists():
            current = json.loads(self.hooks_path.read_text())
            self._validate_hook_shape(current, str(self.hooks_path))
        else:
            current = {"description": "Merged local Codex hooks", "hooks": {}}

        merged = json.loads(json.dumps(current))
        for event, registrations in source["hooks"].items():
            existing = merged["hooks"].setdefault(event, [])
            existing[:] = [item for item in existing if not self._is_router_registration(item)]
            existing.extend(registrations)
        self._validate_hook_shape(merged, "staged hooks.json")
        return json.dumps(merged, ensure_ascii=False, indent=2) + "\n"

    def preflight(self) -> None:
        required = [
            self.repo_root / "codex" / "AGENTS.global.md",
            self.repo_root / "codex" / "AGENTS.workspace.md",
            self.repo_root / "codex" / "skills" / "research-execution-grill" / "SKILL.md",
            self.repo_root / "codex" / "hooks" / "hooks.json",
            *(self.repo_root / "codex" / "hooks" / name for name in HOOK_FILES),
            *(self.repo_root / "codex" / "agents" / f"{role}.toml" for role in ROLES),
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise ValueError("missing installation source(s): " + ", ".join(missing))

        original_config = self.config_path.read_text() if self.config_path.exists() else ""
        try:
            tomllib.loads(original_config)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"refusing to modify malformed {self.config_path}: {exc}") from exc
        self.staged_config = self._replace_section_values(original_config, "agents", AGENT_SETTINGS)
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
            with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
                handle.write(content)
                temporary = Path(handle.name)
            os.replace(temporary, path)
            temporary = None
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def _write_staged(self, destination: Path, content: str, description: str) -> None:
        original = destination.read_text() if destination.exists() else ""
        if content == original and not destination.is_symlink():
            self._record(f"unchanged {destination}")
            return
        self._begin_mutation(destination)
        self._record(description)
        if not self.dry_run:
            self._atomic_text(destination, content)

    def configure_agents(self) -> None:
        self._write_staged(
            self.config_path,
            self.staged_config,
            f"configure [agents] in {self.config_path}; preserve top-level model",
        )

    def merge_hooks(self) -> None:
        self._write_staged(
            self.hooks_path,
            self.staged_hooks,
            f"merge weighted router registrations into {self.hooks_path}",
        )

    def install(self) -> None:
        self.preflight()
        codex_home = self.home / ".codex"
        try:
            self.link(self.repo_root / "codex" / "AGENTS.global.md", codex_home / "AGENTS.md")
            self.link(self.repo_root / "codex" / "AGENTS.workspace.md", self.workspace / "AGENTS.md")
            for role in ROLES:
                self.link(self.repo_root / "codex" / "agents" / f"{role}.toml", codex_home / "agents" / f"{role}.toml")
            self.link(
                self.repo_root / "codex" / "skills" / "research-execution-grill",
                codex_home / "skills" / "research-execution-grill",
            )
            for hook_file in HOOK_FILES:
                self.link(self.repo_root / "codex" / "hooks" / hook_file, codex_home / "hooks" / hook_file)
            self.configure_agents()
            self.merge_hooks()  # Activate the Hook only after all dependencies and config are ready.
            self._persist_manifest("completed")
        except BaseException as exc:
            rollback_errors = self.rollback()
            manifest = "; ".join(
                f"{item.destination} <- {item.backup or '[absent]'}" for item in self.mutations
            ) or "no mutations"
            detail = f"installation failed and rollback ran; manifest: {manifest}"
            if rollback_errors:
                detail += "; rollback errors: " + "; ".join(rollback_errors)
            raise RuntimeError(f"{detail}; cause: {exc}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--workspace", type=Path, default=Path("/Users/viking"))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    installer = Installer(args.repo_root, args.home, args.workspace, dry_run=args.dry_run)
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
