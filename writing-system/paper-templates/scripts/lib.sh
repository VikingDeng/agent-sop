#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  lib.sh — shared helpers for the paper-templates scripts.
#  Source it, do not execute it:   . "$(dirname "$0")/lib.sh"
# ---------------------------------------------------------------------------

set -euo pipefail

LIB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LIB_ROOT
MANIFEST="$LIB_ROOT/templates.tsv"

# Make user-level installs visible even when the shell profile was not loaded.
export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$HOME/.local/bin:$PATH"

# ---- output helpers --------------------------------------------------------
if [ -t 1 ]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'; C_DIM=$'\033[2m'
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_BLUE=$'\033[34m'
else
  C_RESET=; C_BOLD=; C_DIM=; C_RED=; C_GREEN=; C_YELLOW=; C_BLUE=
fi
ok()    { printf '%s✔%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
bad()   { printf '%s✘%s %s\n' "$C_RED"   "$C_RESET" "$*"; }
warn()  { printf '%s!%s %s\n' "$C_YELLOW" "$C_RESET" "$*"; }
info()  { printf '%s·%s %s\n' "$C_BLUE"  "$C_RESET" "$*"; }
head1() { printf '\n%s%s%s\n' "$C_BOLD" "$*" "$C_RESET"; }

# ---- manifest access -------------------------------------------------------
# manifest_rows <id|"">  -> TSV rows, comments and blank lines stripped
manifest_rows() {
  local want="${1:-}"
  while IFS=$'\t' read -r id format venue template version year origin license path source state; do
    [[ "$id" =~ ^#.*$ || -z "$id" ]] && continue
    if [ -z "$want" ] || [ "$id" = "$want" ]; then
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$id" "$format" "$venue" "$template" "$version" "$year" "$origin" \
        "$license" "$path" "$source" "$state"
    fi
  done < "$MANIFEST"
}

# manifest_field <id> <field-number 1..11>
manifest_field() {
  manifest_rows "$1" | head -1 | cut -f"$2"
}

# does a template id exist in the manifest?
manifest_has() {
  [ -n "$(manifest_rows "$1")" ]
}

# ---- tool detection --------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }
