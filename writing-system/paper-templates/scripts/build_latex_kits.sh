#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  build_latex_kits.sh — compile each official LaTeX author kit shipped in
#  latex/<venue>/, from a clean copy, and report per-kit results.
#
#  Usage:
#    ./build_latex_kits.sh                  # all kits
#    ./build_latex_kits.sh acl cvpr icml    # selected venues
#    ./build_latex_kits.sh --keep           # keep this run's scratch tree
#    ./build_latex_kits.sh --no-report      # do not append to BUILD_REPORT.md
#
#  Why "from a clean copy": these kits write .aux/.bbl/.log next to their
#  sources. Compiling in place would litter latex/<venue>/, which is supposed
#  to stay a pristine copy of what the venue published.
#
#  A kit counts as OK only when the compiler exits 0 AND the expected PDF
#  exists and is non-empty; a PDF already shipped inside the kit is removed
#  from the copy first, so it can never be mistaken for a fresh build.
#
#  Exit code 0 only if every kit compiled.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib.sh"

KEEP=0
NO_REPORT=0
WANTED=()
for a in "$@"; do
  case "$a" in
    --keep) KEEP=1 ;;
    --no-report) NO_REPORT=1 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) WANTED+=("$a") ;;
  esac
done

have latexmk || { bad "latexmk is not on PATH"; info "install LaTeX first — see ENVIRONMENT.md"; exit 1; }

# One private scratch tree per run. Earlier versions reused a fixed
# "$TMPDIR/paper-templates-latex" and wiped per-venue subdirs in it, which can
# destroy the evidence of a concurrent run; only this run's own mktemp
# directory is ever removed.
SCRATCH_ROOT="${TMPDIR:-/tmp}/paper-templates-latex"
mkdir -p "$SCRATCH_ROOT"
SCRATCH="$(mktemp -d "$SCRATCH_ROOT/run.XXXXXX")" \
  || { bad "cannot create a scratch directory under $SCRATCH_ROOT"; exit 1; }

# venue  relative-path-to-entry  engine
KITS=(
  "neurips neurips/Styles/neurips_2025.tex                                 pdflatex"
  "icml     icml/kit/example_paper.tex                                     pdflatex"
  "iclr     iclr/kit/iclr2027/iclr2027_conference.tex                      pdflatex"
  "cvpr     cvpr/kit/main.tex                                              pdflatex"
  "iccv     iccv/kit/main.tex                                              pdflatex"
  "eccv     eccv/2026/kit/main.tex                                         pdflatex"
  "acl      acl/kit/acl_latex.tex                                          pdflatex"
  "aaai     aaai/kit/AnonymousSubmission2027.tex                           pdflatex"
  "ijcai    ijcai/kit/ijcai26.tex                                          pdflatex"
  "ieee     ieee/IEEEtran/bare_conf.tex                                    pdflatex"
  "kdd      kdd/acmart-primary/samples/sigconf.tex                         pdflatex"
)

n_ok=0; n_fail=0; n_skip=0
results=""

head1 "Compiling official LaTeX author kits"

for row in "${KITS[@]}"; do
  read -r venue entry engine <<<"$row"

  if [ ${#WANTED[@]} -gt 0 ]; then
    keep=0
    for w in "${WANTED[@]}"; do [ "$w" = "$venue" ] && keep=1; done
    [ "$keep" = "0" ] && continue
  fi

  src="$LIB_ROOT/latex/$entry"
  if [ ! -f "$src" ]; then
    printf '  %-9s %sskipped (no entry: %s)%s\n' "$venue" "$C_DIM" "$entry" "$C_RESET"
    n_skip=$((n_skip + 1)); continue
  fi

  work="$SCRATCH/$venue"
  rm -rf "$work"; mkdir -p "$work"
  cp -r "$LIB_ROOT/latex/$venue/." "$work/" 2>/dev/null

  rel="${entry#*/}"                 # drop the venue prefix; paths are venue-relative
  log="$SCRATCH/$venue.build.log"

  # LaTeX searches the CURRENT DIRECTORY (plus TEXINPUTS) for .sty/.cls -- NOT
  # the directory of the document being compiled. Several kits keep their class
  # file apart from the working root, so cd to the document's own directory or
  # every \usepackage in it fails with "File ... not found".
  docdir="$(dirname "$rel")"
  docfile="$(basename "$rel")"
  base="${docfile%.tex}"

  # The output THIS build must produce. Some kits ship a PDF with exactly that
  # name (e.g. aaai ships AnonymousSubmission2027.pdf), so drop that copy from
  # the scratch tree first: from here on, the file existing means latexmk made
  # it, not that it came with the kit.
  if [ "$docdir" = "." ]; then exp_pdf="$work/$base.pdf"; else exp_pdf="$work/$docdir/$base.pdf"; fi
  if [ -e "$exp_pdf" ]; then
    info "$venue: removed the kit's shipped $base.pdf from the scratch copy"
    rm -f "$exp_pdf"
  fi

  rc=0
  ( cd "$work/$docdir" && timeout 600 latexmk -pdf -interaction=nonstopmode "$docfile" >"$log" 2>&1 ) || rc=$?

  if [ "$rc" -eq 0 ] && [ -s "$exp_pdf" ]; then
    size=$(stat -c%s "$exp_pdf")
    printf '  %-9s %sok%s  %8s bytes  (%s)\n' "$venue" "$C_GREEN" "$C_RESET" "$size" "$engine"
    results="$results$venue"$'\t'"OK"$'\t'"$size"$'\t'"$log"$'\n'
    n_ok=$((n_ok + 1))
  else
    if [ "$rc" -ne 0 ]; then
      first="$(grep -m1 '^!' "$log" 2>/dev/null | cut -c1-100 || true)"
      [ -n "$first" ] || first="no '^!' line in the log"
      err="latexmk exited $rc: $first"
    elif [ ! -e "$exp_pdf" ]; then
      err="latexmk exited 0 but $base.pdf was not produced"
    else
      err="latexmk exited 0 but $base.pdf is empty"
    fi
    printf '  %-9s %sFAIL%s  %s\n' "$venue" "$C_RED" "$C_RESET" "$err"
    results="$results$venue"$'\t'"FAIL"$'\t'"0"$'\t'"$log"$'\n'
    n_fail=$((n_fail + 1))
  fi

  [ "$KEEP" = "0" ] && rm -rf "$work"
done

printf '\n'
if [ "$n_fail" = "0" ]; then
  ok "$n_ok compiled, 0 failed, $n_skip skipped"
else
  bad "$n_ok compiled, $n_fail FAILED, $n_skip skipped"
fi
info "scratch logs: $SCRATCH"
if [ "$KEEP" = "1" ]; then
  info "scratch trees kept (--keep)"
else
  rm -rf "$SCRATCH"
  info "scratch removed; use --keep to keep the trees and logs"
fi

# Append to BUILD_REPORT.md when it already exists (unless --no-report).
REPORT="$LIB_ROOT/BUILD_REPORT.md"
if [ "$NO_REPORT" = "1" ]; then
  info "--no-report: BUILD_REPORT.md left untouched"
elif [ -f "$REPORT" ]; then
  {
    printf '\n---\n\n## LaTeX author kits\n\n'
    printf 'Compiled by `scripts/build_latex_kits.sh` on %s.\n\n' "$(date -u '+%Y-%m-%d %H:%M UTC')"
    printf 'Each kit is compiled from a throwaway copy so `latex/<venue>/` stays exactly\n'
    printf 'as the venue published it.\n\n'
    printf '| Venue | Result | PDF bytes |\n|---|---|---|\n'
    printf '%s' "$results" | while IFS=$'\t' read -r v st sz log; do
      [ -z "$v" ] && continue
      mark="✅ OK"; [ "$st" = "FAIL" ] && mark="❌ **FAIL**"
      printf '| `%s` | %s | %s |\n' "$v" "$mark" "$sz"
    done
    printf '\n**%s compiled, %s failed.**\n' "$n_ok" "$n_fail"
  } >> "$REPORT"
  ok "appended the LaTeX results to BUILD_REPORT.md"
fi

[ "$n_fail" = "0" ] || exit 1
exit 0
