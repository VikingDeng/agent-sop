#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  install-local-typst-packages.sh
#
#  Registers the non-@preview templates in this library as Typst LOCAL
#  packages, so that a bare
#
#      typst compile main-icml.typ
#
#  works from anywhere — no `--root` flag, no network access — exactly like a
#  published `@preview` package would.
#
#  Why this is needed
#  ------------------
#  Typst resolves `--root` to the directory of the INPUT FILE. A
#  parent-relative import (`../../typst/icml/icml.typ`) is therefore illegal,
#  and a root-absolute import (`/typst/icml/icml.typ`) requires `--root`.
#  A local package sidesteps both, because a package carries its own root.
#
#  Layout Typst expects (Linux):
#      ${XDG_DATA_HOME:-~/.local/share}/typst/packages/<namespace>/<name>/<version>/
#
#  RE-RUN THIS SCRIPT after editing anything under:
#      typst/icml/  typst/iclr/  typst/generic/
#      reports/modern-technical/  reports/academic-clean/  reports/chinese-research/
# ---------------------------------------------------------------------------
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/typst/packages/local"

# <source dir relative to library root> <package name> <version>
ENTRIES=(
  "typst/icml               lucky-icml           0.7.1"
  "typst/iclr               clear-iclr           0.7.1"
  "typst/generic            generic-paper        0.1.0"
  "reports/modern-technical modern-technical     0.1.0"
  "reports/academic-clean   academic-clean       0.1.0"
  "reports/chinese-research chinese-research     0.1.0"
  "reports/chinese-plain    chinese-plain        0.1.0"
  "vendor/elegant-mono      elegant-mono         0.1.0"
)

echo "Installing local Typst packages into: $DEST_ROOT"

for entry in "${ENTRIES[@]}"; do
  read -r rel name version <<<"$entry"
  src="$HERE/$rel"
  if [ ! -f "$src/typst.toml" ]; then
    echo "  SKIP  $name (no typst.toml in $rel)"
    continue
  fi
  dest="$DEST_ROOT/$name/$version"
  rm -rf "$dest"
  mkdir -p "$dest"
  ( cd "$src" && tar -cf - \
      --exclude='out.pdf' --exclude='*.log' --exclude='thumbnail.png' . ) \
    | ( cd "$dest" && tar -xf - )

  # Typst validates that the manifest version MATCHES the directory version.
  # The vendored sources still carry their upstream version, so rewrite it.
  python3 - "$dest/typst.toml" "$version" <<'PYFIX'
import re, sys
path, version = sys.argv[1], sys.argv[2]
s = open(path).read()
s = re.sub(r'(?m)^version\s*=\s*"[^"]*"', f'version = "{version}"', s, count=1)
# `typst init` support is not shipped in these library copies; drop the
# section so the manifest does not point at files that are not there.
s = re.sub(r'(?ms)^\[template\].*?(?=^\[|\Z)', '', s).rstrip() + "\n"
open(path, 'w').write(s)
PYFIX

  echo "  ok    @local/$name:$version  <-  $rel"
done

echo
echo "Done. Import style:  #import \"@local/generic-paper:0.1.0\": generic-paper"
