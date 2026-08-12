from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_sop_repo.py"
SPEC = importlib.util.spec_from_file_location("validate_sop_repo", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class StructuralConsistencyTests(unittest.TestCase):
    def copy_files(self, destination: Path, relative_paths: tuple[str, ...]) -> None:
        for relative_path in relative_paths:
            source = ROOT / relative_path
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def overlay_repo(self) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        destination = Path(temporary.name)
        self.copy_files(
            destination,
            (VALIDATOR.LEGACY_OVERLAY,)
            + tuple(source for source, _ in VALIDATOR.LEGACY_OVERLAY_REFERENCES),
        )
        return temporary

    def test_current_structural_contract_passes(self) -> None:
        self.assertEqual(VALIDATOR.validate_legacy_overlay_references(ROOT), [])
        self.assertEqual(VALIDATOR.validate_skill_resource_references(ROOT), [])
        files = VALIDATOR.formal_sops(ROOT)
        direct, reverse = VALIDATOR.collect_dependency_graph(ROOT, files)
        self.assertEqual(VALIDATOR.validate_index(ROOT, files, direct, reverse), [])

    def test_index_rejects_discipline_metadata_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            shutil.copytree(ROOT / "sop", fixture / "sop")
            index = fixture / "sop/README.md"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "statistics-oracle.md | research | U1 | P1 P2 P3 P4 |",
                    "statistics-oracle.md | research | U1 | P2 P3 P4 |",
                ),
                encoding="utf-8",
            )
            files = VALIDATOR.formal_sops(fixture)
            direct, reverse = VALIDATOR.collect_dependency_graph(fixture, files)
            errors = VALIDATOR.validate_index(fixture, files, direct, reverse)
            self.assertTrue(any("discipline drift for tier1-skeleton/statistics-oracle.md" in item for item in errors))

    def test_workspace_compute_profile_discovers_resources_locally(self) -> None:
        workspace = (ROOT / "codex/AGENTS.workspace.md").read_text(encoding="utf-8")
        compute_profile = workspace.split("## Local resources", maxsplit=1)[1]
        self.assertIn("~/.ssh/config", compute_profile)
        self.assertIn("closest project instructions", compute_profile)
        self.assertIn("read-only probes", compute_profile)
        self.assertNotIn("/Users/viking", workspace)
        self.assertNotRegex(compute_profile, r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")

    def test_runtime_bootstrap_does_not_default_load_legacy_overlay(self) -> None:
        installed_reference = "~/.codex/runtime-current/skeletons/contestos-adaptive-overlay-v2.md"
        self.assertNotIn(installed_reference, (ROOT / "codex/AGENTS.global.md").read_text(encoding="utf-8"))
        self.assertNotIn(installed_reference, (ROOT / "codex/AGENTS.workspace.md").read_text(encoding="utf-8"))
        self.assertIn(
            "Do not load provenance-locked ContestOS v1 skeletons",
            (ROOT / "codex/AGENTS.global.md").read_text(encoding="utf-8"),
        )

    def test_rejects_missing_legacy_overlay_file(self) -> None:
        with self.overlay_repo() as temporary:
            overlay = Path(temporary) / VALIDATOR.LEGACY_OVERLAY
            overlay.unlink()
            errors = VALIDATOR.validate_legacy_overlay_references(Path(temporary))
            self.assertTrue(any("legacy overlay missing" in error for error in errors), errors)

    def test_rejects_unreachable_legacy_overlay_reference(self) -> None:
        with self.overlay_repo() as temporary:
            path = Path(temporary) / "skeletons/README.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("contestos-adaptive-overlay-v2.md", "contestos-adaptive-overlay-v2-missing.md"),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_legacy_overlay_references(Path(temporary))
            self.assertTrue(any("legacy overlay reference missing" in error for error in errors), errors)

    def test_skill_registry_is_machine_readable_and_has_no_promoted_shortcuts(self) -> None:
        registry = json.loads((ROOT / "skill-registry.yaml").read_text(encoding="utf-8"))
        self.assertEqual(registry["schema_version"], 1)
        self.assertEqual(registry["format"], "strict-json-compatible-yaml-1.2")
        entries = registry["entries"]
        evaluation_report = (ROOT / "skill-evaluations/round1-2026-08-12.md").read_text(encoding="utf-8")
        identifiers = [entry["id"] for entry in entries]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for entry in entries:
            lifecycle = entry["lifecycle"]
            license_spdx = entry["source"].get("license_spdx")
            if license_spdx is not None:
                self.assertRegex(license_spdx, r"^[A-Za-z0-9][A-Za-z0-9.+-]*$", entry["id"])
            selected_paths = entry["source"].get("selected_paths")
            if selected_paths is not None:
                self.assertEqual(selected_paths, sorted(set(selected_paths)), entry["id"])
            for state in ("declared", "audited", "installed", "enabled", "evaluated", "promoted"):
                self.assertIsInstance(lifecycle[state], bool, (entry["id"], state))
            self.assertTrue(lifecycle["declared"], entry["id"])
            if lifecycle["audited"]:
                source = entry["source"]
                self.assertTrue(source["repository"], entry["id"])
                self.assertRegex(source["commit"], r"^[0-9a-f]{40}$", entry["id"])
                self.assertTrue(source["subpath"], entry["id"])
                self.assertRegex(source["content_sha256"], r"^[0-9a-f]{64}$", entry["id"])
                self.assertTrue(source["content_hash_scheme"], entry["id"])
                self.assertTrue(source["selected_file_sha256"], entry["id"])
                for label, digest in source["selected_file_sha256"].items():
                    self.assertRegex(digest, r"^[0-9a-f]{64}$", (entry["id"], label))
                self.assertTrue(source["license_spdx"], entry["id"])
                self.assertTrue(source["license_evidence"], entry["id"])
                evidence = entry["audit"].get("evidence")
                if isinstance(evidence, str) and evidence.startswith("skill-evaluations/round1-2026-08-12.md#"):
                    self.assertIn(source["content_sha256"], evaluation_report, entry["id"])
            if lifecycle["installed"]:
                self.assertTrue(lifecycle["audited"], entry["id"])
            if lifecycle["enabled"]:
                self.assertTrue(lifecycle["installed"], entry["id"])
            if lifecycle["evaluated"]:
                self.assertTrue(lifecycle["audited"], entry["id"])
                self.assertTrue(entry["evaluation"]["fixtures"], entry["id"])
                self.assertIsNotNone(entry["evaluation"]["thresholds"], entry["id"])
                self.assertIsNotNone(entry["evaluation"]["result"], entry["id"])
            if lifecycle["promoted"]:
                self.assertTrue(lifecycle["audited"])
                self.assertTrue(lifecycle["evaluated"])
                self.assertTrue(lifecycle["enabled"])
        self.assertFalse(any(entry["lifecycle"]["promoted"] for entry in entries))
        power = next(entry for entry in entries if entry["id"] == "kdense-statistical-power")
        self.assertTrue(power["lifecycle"]["audited"])
        self.assertFalse(power["lifecycle"]["installed"])
        self.assertFalse(power["lifecycle"]["enabled"])
        self.assertFalse(power["lifecycle"]["promoted"])
        self.assertEqual(power["activation"]["mode"], "explicit_experiment_only")
        self.assertEqual(power["source"]["license_spdx"], "MIT")
        self.assertRegex(power["source"]["content_sha256"], r"^[0-9a-f]{64}$")
        selected_hashes = power["source"]["selected_file_sha256"]
        self.assertEqual(len(selected_hashes), 6)
        canonical_digest_input = b"".join(
            digest.encode("ascii") + b"  " + relative_path.encode("utf-8") + b"\n"
            for relative_path, digest in sorted(selected_hashes.items())
        )
        self.assertEqual(
            hashlib.sha256(canonical_digest_input).hexdigest(),
            power["source"]["content_sha256"],
        )
        self.assertFalse(power["audit"]["blockers"])
        shim = next(entry for entry in entries if entry["id"] == "local-research-execution-grill-shim")
        self.assertEqual(shim["lifecycle"]["current"], "retired")
        self.assertFalse(shim["lifecycle"]["installed"])
        self.assertFalse((ROOT / "codex/skills/research-execution-grill/SKILL.md").exists())
        self.assertFalse((ROOT / "codex/skills/research-execution-grill/agents/openai.yaml").exists())


if __name__ == "__main__":
    unittest.main()
