#!/usr/bin/env python3
"""Validate structural invariants of the agent-sop repository."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


REQUIRED_SECTIONS = (
    "触发条件",
    "前置条件",
    "依赖 SOP",
    "步骤",
    "门禁",
    "完成判定",
    "失败处理",
    "产物",
)
REQUIRED_METADATA = ("层级", "落实纪律", "绑定骨架", "通用性档位", "版本")
FORMAL_DIRS = (
    "sop/tier0-core",
    "sop/tier1-skeleton",
    "sop/tier2-activity",
)
PLACEHOLDER_LINE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:TODO|TBD|FIXME|待定|待补)(?:\b|[:：])"
)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SOP_INDEX_PATH = re.compile(
    r"^\|\s*(tier(?:0-core|1-skeleton|2-activity)/[A-Za-z0-9_.-]+\.md)\s*\|",
    re.MULTILINE,
)
DEPENDENCY_REF = re.compile(r"→\s*([^\s(]+\.md)")


class ValidationFailure(Exception):
    """Raised when the validator itself cannot complete its scan."""


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def formal_sops(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in FORMAL_DIRS:
        base = root / directory
        if not base.is_dir():
            raise ValidationFailure(f"missing formal SOP directory: {directory}")
        files.extend(path for path in base.glob("*.md") if path.is_file())
    return sorted(files)


def metadata_value(text: str, field: str) -> str | None:
    match = re.search(rf"^- \*\*{re.escape(field)}\*\*:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def section_body(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else None


def validate_sops(root: Path, files: list[Path]) -> tuple[list[str], dict[str, Path]]:
    errors: list[str] = []
    ids: dict[str, Path] = {}

    for path in files:
        rel = relative(path, root)
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^# SOP-([^:]+):\s*.+$", text, re.MULTILINE)
        if not title:
            errors.append(f"{rel}: missing '# SOP-<ID>: <name>' title")
        else:
            sop_id = title.group(1).strip()
            if sop_id != path.stem:
                errors.append(
                    f"{rel}: SOP ID '{sop_id}' does not match filename '{path.stem}'"
                )
            if sop_id in ids:
                errors.append(
                    f"{rel}: duplicate SOP ID '{sop_id}' (also {relative(ids[sop_id], root)})"
                )
            else:
                ids[sop_id] = path

        for field in REQUIRED_METADATA:
            value = metadata_value(text, field)
            if value is None or not value.strip():
                errors.append(f"{rel}: missing metadata '{field}'")

        expected_layer = path.parent.name
        layer = metadata_value(text, "层级")
        if layer and not layer.startswith(expected_layer):
            errors.append(
                f"{rel}: layer metadata '{layer}' does not match directory '{expected_layer}'"
            )

        discipline = metadata_value(text, "落实纪律")
        if discipline:
            cited = set(re.findall(r"P\d+", discipline))
            if not cited:
                errors.append(f"{rel}: discipline metadata cites no P1-P4 value")
            invalid = sorted(cited - {"P1", "P2", "P3", "P4"})
            if invalid:
                errors.append(f"{rel}: invalid discipline reference(s): {', '.join(invalid)}")

        universality = metadata_value(text, "通用性档位")
        if universality and not re.match(r"^U[012](?:\b|\()", universality):
            errors.append(f"{rel}: invalid universality tier '{universality}'")

        version = metadata_value(text, "版本")
        if version and not re.match(r"^v\d+(?:\b|\.)", version):
            errors.append(f"{rel}: invalid version '{version}'")

        for heading in REQUIRED_SECTIONS:
            count = len(re.findall(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE))
            if count != 1:
                errors.append(f"{rel}: required section '{heading}' appears {count} times")
                continue
            body = section_body(text, heading)
            if body is None or not body.strip():
                errors.append(f"{rel}: required section '{heading}' is empty")
            elif PLACEHOLDER_LINE.search(body):
                errors.append(f"{rel}: required section '{heading}' contains a placeholder")

        for dependency in DEPENDENCY_REF.findall(section_body(text, "依赖 SOP") or ""):
            candidates = (
                root / "sop" / dependency,
                root / dependency,
                path.parent / dependency,
            )
            if not any(candidate.is_file() for candidate in candidates):
                errors.append(f"{rel}: dependency reference does not exist: {dependency}")

    return errors, ids


def collect_dependency_graph(
    root: Path, files: list[Path]
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    formal_by_path = {path.resolve(): relative(path, root / "sop") for path in files}
    direct = {relative(path, root / "sop"): set() for path in files}
    reverse = {relative(path, root / "sop"): set() for path in files}

    for path in files:
        source = relative(path, root / "sop")
        text = path.read_text(encoding="utf-8")
        for dependency in DEPENDENCY_REF.findall(section_body(text, "依赖 SOP") or ""):
            direct[source].add(Path(dependency).stem)
            candidates = (
                root / "sop" / dependency,
                root / dependency,
                path.parent / dependency,
            )
            resolved = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
            if resolved in formal_by_path:
                reverse[formal_by_path[resolved]].add(path.stem)
    return direct, reverse


def dependency_names(cell: str) -> set[str]:
    if not cell or cell == "—":
        return set()
    return {item.strip().strip("`") for item in cell.split(",") if item.strip()}


def validate_index(
    root: Path,
    files: list[Path],
    direct: dict[str, set[str]],
    reverse: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    index = root / "sop/README.md"
    if not index.is_file():
        raise ValidationFailure("missing sop/README.md")
    text = index.read_text(encoding="utf-8")
    indexed = SOP_INDEX_PATH.findall(text)
    counts = Counter(indexed)

    for path, count in sorted(counts.items()):
        if count != 1:
            errors.append(f"sop/README.md: index path appears {count} times: {path}")
        if not (root / "sop" / path).is_file():
            errors.append(f"sop/README.md: indexed path does not exist: {path}")

    formal = {relative(path, root / "sop") for path in files}
    indexed_set = set(indexed)
    for missing in sorted(formal - indexed_set):
        errors.append(f"sop/README.md: formal SOP is not indexed: {missing}")
    for extra in sorted(indexed_set - formal):
        errors.append(f"sop/README.md: index entry is not a formal SOP: {extra}")

    section = ""
    for line in text.splitlines():
        if line.startswith("## Tier 0"):
            section = "tier0"
        elif line.startswith("## Tier 1"):
            section = "tier1"
        elif line.startswith("## Tier 2"):
            section = "tier2"
        if not re.match(r"^\|\s*tier(?:0-core|1-skeleton|2-activity)/", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        path = cells[0]
        if section == "tier0" and len(cells) == 4:
            actual = dependency_names(cells[3])
            expected = reverse[path]
            label = "reverse dependencies"
        elif section in {"tier1", "tier2"} and len(cells) == 5:
            actual = dependency_names(cells[4])
            expected = direct[path]
            label = "dependencies"
        else:
            errors.append(f"sop/README.md: malformed index row: {line}")
            continue
        if actual != expected:
            errors.append(
                f"sop/README.md: {label} drift for {path}; "
                f"expected {sorted(expected)}, found {sorted(actual)}"
            )
    return errors


def normalize_link_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target or target.startswith(("http://", "https://", "mailto:", "#", "/")):
        return None
    if not target.lower().endswith(".md"):
        return None
    return target


def validate_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts:
            continue
        rel = relative(path, root)
        text = path.read_text(encoding="utf-8")
        for raw in MARKDOWN_LINK.findall(text):
            target = normalize_link_target(raw)
            if target is None:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{rel}: relative Markdown link escapes repository: {target}")
                continue
            if not resolved.is_file():
                errors.append(f"{rel}: broken relative Markdown link: {target}")
    return errors


def validate_readme_counts(root: Path, files: list[Path]) -> list[str]:
    errors: list[str] = []
    readme = root / "README.md"
    if not readme.is_file():
        raise ValidationFailure("missing README.md")
    text = readme.read_text(encoding="utf-8")
    expected = Counter(path.parent.name for path in files)
    for layer, count in sorted(expected.items()):
        match = re.search(rf"{re.escape(layer)}/.*?(\d+)\s*条", text)
        if match and int(match.group(1)) != count:
            errors.append(
                f"README.md: hard-coded {layer} count is {match.group(1)}, expected {count}"
            )
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root (defaults to the parent of scripts/)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    try:
        if not root.is_dir():
            raise ValidationFailure(f"repository root does not exist: {root}")
        files = formal_sops(root)
        if not files:
            raise ValidationFailure("no formal SOP files found")
        errors, ids = validate_sops(root, files)
        direct, reverse = collect_dependency_graph(root, files)
        errors.extend(validate_index(root, files, direct, reverse))
        errors.extend(validate_markdown_links(root))
        errors.extend(validate_readme_counts(root, files))
    except (OSError, UnicodeError, ValidationFailure) as exc:
        print(f"VALIDATOR ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(f"SOP repository validation failed with {len(errors)} violation(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"SOP repository validation passed: {len(files)} formal SOPs, "
        f"{len(ids)} unique SOP IDs, synchronized dependency index and counts, "
        "no broken relative Markdown links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
