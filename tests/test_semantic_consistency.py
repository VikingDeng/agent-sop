from __future__ import annotations

import importlib.util
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
import shutil
import tarfile
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
        identifiers = [entry["id"] for entry in entries]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for entry in entries:
            lifecycle = entry["lifecycle"]
            for state in ("declared", "audited", "installed", "enabled", "evaluated", "promoted"):
                self.assertIsInstance(lifecycle[state], bool, (entry["id"], state))
            if lifecycle["promoted"]:
                self.assertTrue(lifecycle["audited"])
                self.assertTrue(lifecycle["installed"])
                self.assertTrue(lifecycle["evaluated"])
                self.assertTrue(lifecycle["enabled"])
                self.assertIs(entry["evaluation"]["result"]["promotion_thresholds_met"], True)
                valid_until = datetime.strptime(entry["evaluation"]["valid_until"], "%Y-%m-%d").date()
                self.assertGreaterEqual(valid_until, date.today())
        self.assertFalse(any(entry["lifecycle"]["promoted"] for entry in entries))
        shim = next(entry for entry in entries if entry["id"] == "local-research-execution-grill-shim")
        self.assertEqual(shim["lifecycle"]["current"], "retired")
        self.assertFalse(shim["lifecycle"]["installed"])
        self.assertFalse((ROOT / "codex/skills/research-execution-grill/SKILL.md").exists())
        self.assertFalse((ROOT / "codex/skills/research-execution-grill/agents/openai.yaml").exists())

    def test_frontend_design_no_go_is_reproducible_and_remains_inert(self) -> None:
        registry = json.loads((ROOT / "skill-registry.yaml").read_text(encoding="utf-8"))
        entry = next(item for item in registry["entries"] if item["id"] == "anthropic-frontend-design")
        lifecycle = entry["lifecycle"]
        self.assertTrue(lifecycle["audited"])
        self.assertTrue(lifecycle["evaluated"])
        self.assertFalse(lifecycle["installed"])
        self.assertFalse(lifecycle["enabled"])
        self.assertFalse(lifecycle["promoted"])
        self.assertEqual(lifecycle["current"], "evaluated_no_go")

        source_root = ROOT / "codex/external-skills/anthropic-frontend-design"
        digest = hashlib.sha256()
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(source_root).as_posix().encode("utf-8")
            content = source.read_bytes()
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
            self.assertEqual(
                hashlib.sha256(content).hexdigest(),
                entry["source"]["selected_file_sha256"][source.relative_to(source_root).as_posix()],
            )
        self.assertEqual(digest.hexdigest(), entry["source"]["content_sha256"])

        result = entry["evaluation"]["result"]
        scores = result["independent_quality_score_10"]
        self.assertLess(scores["full_pinned_skill"], scores["strong_no_skill"])
        self.assertLess(scores["full_pinned_skill"], scores["minimal_reminder"])
        artifact = ROOT / result["raw_artifacts"]
        self.assertTrue(artifact.is_file())
        with tarfile.open(artifact, "r:gz") as archive:
            members = set(archive.getnames())
        for required in (
            "strong_no_skill/cold-chain/index.html",
            "minimal_reminder/cinema/index.html",
            "full_skill/roastery/index.html",
            "evidence-v2/browser-results.json",
            "blind/anonymization-map.json",
        ):
            self.assertIn(required, members)


if __name__ == "__main__":
    unittest.main()
