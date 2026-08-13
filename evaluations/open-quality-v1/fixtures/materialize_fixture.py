#!/usr/bin/env python3
"""Build a byte-deterministic ZIP from one agent-visible workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def workspace_files(workspace: Path) -> list[Path]:
    return [
        path
        for path in sorted(workspace.rglob("*"), key=lambda value: value.relative_to(workspace).as_posix())
        if path.is_file() and path.suffix != ".pyc" and not any(part in IGNORED_PARTS for part in path.parts)
    ]


def file_hashes(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in workspace_files(workspace)
    }


def tree_hash(hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative, file_hash in sorted(hashes.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_bundle(workspace: Path, output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in workspace_files(workspace):
            relative = path.relative_to(workspace).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, path.read_bytes())
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", choices=sorted(path.name for path in ROOT.glob("out_*") if path.is_dir()))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    workspace = ROOT / args.fixture / "workspace"
    hashes = file_hashes(workspace)
    archive_hash = write_bundle(workspace, args.output.resolve())
    print(
        json.dumps(
            {
                "fixture": args.fixture,
                "files": len(hashes),
                "tree_sha256": tree_hash(hashes),
                "archive_sha256": archive_hash,
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
