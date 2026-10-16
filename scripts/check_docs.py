#!/usr/bin/env python3
"""Check that local Markdown links resolve and core docs stay within size caps.

Size is counted as CJK characters plus Latin word tokens. writing-system/ is a
read-only snapshot and is excluded.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPS = {
    "README.md": 450,
    "AGENTS.md": 300,
    "KERNEL.md": 1000,
    "playbooks/oss-pr.md": 600,
    "playbooks/research.md": 800,
    "retro/TEMPLATE.md": 300,
}
TOTAL_CAP = 3500  # all Markdown outside writing-system/ and retro entries
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CJK = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.'/-]*")


def size(text: str) -> int:
    return len(CJK.findall(text)) + len(LATIN.findall(CJK.sub(" ", text)))


def markdown_files() -> list[Path]:
    return [
        p for p in sorted(ROOT.rglob("*.md"))
        if ".git" not in p.parts and "writing-system" not in p.relative_to(ROOT).parts
    ]


def main() -> int:
    errors: list[str] = []
    total = 0
    for path in markdown_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if not (rel.startswith("retro/") and rel != "retro/TEMPLATE.md"):
            total += size(text)
        for target in LINK.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            if not (path.parent / target.split("#", 1)[0]).exists():
                errors.append(f"{rel}: broken link {target}")
    for rel, cap in CAPS.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: missing")
            continue
        n = size(path.read_text(encoding="utf-8"))
        print(f"{rel}: {n}/{cap}")
        if n > cap:
            errors.append(f"{rel}: size {n} exceeds cap {cap}; delete something before adding")
    print(f"total: {total}/{TOTAL_CAP}")
    if total > TOTAL_CAP:
        errors.append(f"total size {total} exceeds cap {TOTAL_CAP}")
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
