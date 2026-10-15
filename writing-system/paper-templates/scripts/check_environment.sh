#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  check_environment.sh — report which writing tools are present.
#
#  Usage:  ./check_environment.sh [--md]
#          --md   emit Markdown (paste-ready) instead of the terminal table
#
#  Bash counterpart of check_environment.ps1. Exit code is always 0: this is a
#  report, not a gate.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib.sh"

MD=0
[ "${1:-}" = "--md" ] && MD=1

probe() { # <command> <label>
  if have "$1"; then
    local v
    v="$("$1" --version 2>&1 | head -1 | tr -d '\r')"
    printf '%s\t%s\t%s\n' "$1" "$(command -v "$1")" "$v"
  else
    printf '%s\t%s\t%s\n' "$1" "" "MISSING"
  fi
}

COMMANDS="typst xelatex lualatex pdflatex latexmk tlmgr biber bibtex git python3 code"
ROWS=""
missing=""
for c in $COMMANDS; do
  row="$(probe "$c")"
  ROWS="$ROWS$row"$'\n'
  [ "$(printf '%s' "$row" | cut -f3)" = "MISSING" ] && missing="$missing $c"
done

# ---- fonts -----------------------------------------------------------------
cjk_count=$(fc-list :lang=zh 2>/dev/null | wc -l | tr -d ' ')
serif_cjk=$(fc-list 2>/dev/null | grep -ci "Noto Serif CJK SC" || true)
sans_cjk=$(fc-list 2>/dev/null | grep -ci "Noto Sans CJK SC" || true)
gyre=$(fc-list 2>/dev/null | grep -c "TeX Gyre" || true)

# ---- typst packages --------------------------------------------------------
pkg_cache="$HOME/.cache/typst/packages/preview"
pkg_count=0
[ -d "$pkg_cache" ] && pkg_count=$(find "$pkg_cache" -maxdepth 2 -mindepth 2 -type d 2>/dev/null | wc -l | tr -d ' ')
local_pkgs="$HOME/.local/share/typst/packages/local"
local_count=0
[ -d "$local_pkgs" ] && local_count=$(find "$local_pkgs" -maxdepth 2 -mindepth 2 -type d 2>/dev/null | wc -l | tr -d ' ')

emit() {
  if [ "$MD" = "1" ]; then
    printf '| Tool | Version | Path |\n|---|---|---|\n'
    printf '%s' "$ROWS" | while IFS=$'\t' read -r n p v; do
      [ -z "$n" ] && continue
      [ "$v" = "MISSING" ] && v="**MISSING**"
      [ -z "$p" ] && p="—"
      printf '| `%s` | %s | `%s` |\n' "$n" "$v" "$p"
    done
  else
    head1 "Command line tools"
    printf '%-10s %-55s %s\n' "TOOL" "PATH" "VERSION"
    printf '%s' "$ROWS" | while IFS=$'\t' read -r n p v; do
      [ -z "$n" ] && continue
      if [ "$v" = "MISSING" ]; then
        printf '%-10s %-55s %s%s%s\n' "$n" "-" "$C_RED" "MISSING" "$C_RESET"
      else
        printf '%-10s %-55s %s\n' "$n" "${p:0:55}" "${v:0:60}"
      fi
    done
  fi
}

if [ "$MD" = "1" ]; then
  emit
  printf '\n### Fonts\n\n'
  printf '| Item | Count |\n|---|---|\n'
  printf '| CJK fonts installed | %s |\n' "$cjk_count"
  printf '| Noto Serif CJK SC | %s |\n' "$serif_cjk"
  printf '| Noto Sans CJK SC | %s |\n' "$sans_cjk"
  printf '| TeX Gyre faces | %s |\n' "$gyre"
  printf '\n### Typst packages\n\n'
  printf '| Item | Count |\n|---|---|\n'
  printf '| @preview packages cached | %s |\n' "$pkg_count"
  printf '| @local packages installed | %s |\n' "$local_count"
else
  emit
  head1 "Fonts"
  printf '  CJK fonts ............ %s\n' "$cjk_count"
  printf '  Noto Serif CJK SC .... %s\n' "$serif_cjk"
  printf '  Noto Sans CJK SC ..... %s\n' "$sans_cjk"
  printf '  TeX Gyre faces ....... %s\n' "$gyre"
  head1 "Typst packages"
  printf '  cached @preview ...... %s\n' "$pkg_count"
  printf '  installed @local ..... %s\n' "$local_count"
  head1 "Library"
  printf '  root ................. %s\n' "$LIB_ROOT"
  if [ -n "$missing" ]; then
    printf '\n'
    warn "not installed:$missing"
    case "$missing" in *typst*)  info "install Typst:  https://github.com/typst/typst/releases";; esac
    case "$missing" in *xelatex*) info "install LaTeX:  https://yihui.org/tinytex/ (user-level)";; esac
  else
    printf '\n'; ok "every checked tool is present"
  fi
fi
exit 0
