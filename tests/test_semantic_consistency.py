from __future__ import annotations

import importlib.util
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
            (VALIDATOR.ACTIVE_OVERLAY,)
            + tuple(source for source, _ in VALIDATOR.ACTIVE_OVERLAY_REFERENCES),
        )
        return temporary

    def skill_repo(self) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        destination = Path(temporary.name)
        self.copy_files(
            destination,
            (
                "codex/skills/research-execution-grill/SKILL.md",
                "sop/tier1-skeleton/research-execution-grill.md",
                "sop/tier1-skeleton/references/research-execution-grill-artifact.md",
                "sop/tier1-skeleton/references/research-evidence-presentation.md",
                "scripts/validate_research_execution_grill.py",
            ),
        )
        return temporary

    def test_current_structural_contract_passes(self) -> None:
        self.assertEqual(VALIDATOR.validate_active_overlay_references(ROOT), [])
        self.assertEqual(VALIDATOR.validate_skill_resource_references(ROOT), [])

    def test_rejects_missing_active_overlay_file(self) -> None:
        with self.overlay_repo() as temporary:
            overlay = Path(temporary) / VALIDATOR.ACTIVE_OVERLAY
            overlay.unlink()
            errors = VALIDATOR.validate_active_overlay_references(Path(temporary))
            self.assertTrue(any("active overlay missing" in error for error in errors), errors)

    def test_rejects_unreachable_active_overlay_reference(self) -> None:
        with self.overlay_repo() as temporary:
            path = Path(temporary) / "skeletons/README.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("contestos-adaptive-overlay-v2.md", "contestos-adaptive-overlay-v2-missing.md"),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_active_overlay_references(Path(temporary))
            self.assertTrue(any("active overlay reference missing" in error for error in errors), errors)

    def test_rejects_unresolved_skill_resource_reference(self) -> None:
        with self.skill_repo() as temporary:
            path = Path(temporary) / "codex/skills/research-execution-grill/SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    "sop/tier1-skeleton/research-execution-grill.md",
                    "sop/tier1-skeleton/missing-research-execution-grill.md",
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_skill_resource_references(Path(temporary))
            self.assertTrue(any("unresolved local resource reference" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
