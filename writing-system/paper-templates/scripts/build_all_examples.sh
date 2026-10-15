#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  build_all_examples.sh — compile every example and every vendored template,
#  then write BUILD_REPORT.md.
#
#  Usage:
#    ./build_all_examples.sh                      # compile everything, write the report
#    ./build_all_examples.sh --quick              # skip the library template demos
#    ./build_all_examples.sh --reports-only       # only the report templates
#    ./build_all_examples.sh --no-report          # do not write BUILD_REPORT.md
#    ./build_all_examples.sh --reports-only --no-report   # precise local checks
#
#  The report targets are read from templates.tsv (every row whose path is
#  reports/*), NOT from a hard-coded list — a newly registered report is picked
#  up automatically.
#
#  Exit code: 0 only if every target's compiler returned 0 AND the PDF exists.
#  A stale or partial PDF is a FAILURE, never a success. See BUILD_REPORT.md.
#
#  Bash counterpart of build_all_examples.ps1.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib.sh"

QUICK=0
REPORT=1
REPORTS_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) QUICK=1; shift ;;
    --no-report) REPORT=0; shift ;;
    --reports-only) REPORTS_ONLY=1; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) bad "unknown option: $1"; exit 2 ;;
  esac
done

have typst || { bad "typst is not on PATH"; info "install: https://github.com/typst/typst/releases"; exit 1; }

OUT="$LIB_ROOT/build"
LOGS="$OUT/logs"
mkdir -p "$LOGS"

results=""
n_ok=0
n_fail=0

# compile_one <label> <source-file> <output-pdf> <workdir>
# Success requires BOTH: the compiler exited 0 AND the output PDF exists.
compile_one() {
  local label="$1" src="$2" out="$3" wd="$4"
  local log="$LOGS/$(printf '%s' "$label" | tr ' /' '__').log"
  local rc=0
  rm -f "$out"
  ( cd "$wd" && timeout 300 typst compile "$src" "$out" >"$log" 2>&1 ) || rc=$?
  if [ "$rc" = "0" ] && [ -f "$out" ]; then
    local size bytes warns
    bytes=$(stat -c%s "$out")
    warns=$(grep -c '^warning' "$log" 2>/dev/null || true)
    printf '  %s%-34s%s %sok%s  %8s bytes  warnings=%s\n' "$C_BOLD" "$label" "$C_RESET" "$C_GREEN" "$C_RESET" "$bytes" "${warns:-0}"
    results="$results$label"$'\t'"OK"$'\t'"$bytes"$'\t'"${warns:-0}"$'\t'"$log"$'\n'
    n_ok=$((n_ok + 1))
  else
    local err firsterr=""
    # `|| true` matters: under `set -e` a grep with no match would abort the
    # whole script silently instead of reporting this target as failed.
    firsterr=$(grep -m1 '^error' "$log" 2>/dev/null | cut -c1-160 || true)
    if [ "$rc" != "0" ]; then
      err="typst exit=$rc: ${firsterr:-no 'error:' line in the log}"
    else
      err="typst exit=0 but no PDF was written"
    fi
    printf '  %s%-34s%s %sFAIL%s  %s\n' "$C_BOLD" "$label" "$C_RESET" "$C_RED" "$C_RESET" "$err"
    results="$results$label"$'\t'"FAIL"$'\t'"0"$'\t'"0"$'\t'"$log"$'\n'
    n_fail=$((n_fail + 1))
  fi
}

if [ "$REPORTS_ONLY" = "0" ]; then
  head1 "1/3  Example project — one body, many templates"
  EX="$LIB_ROOT/examples/radar-paper"
  for f in main-generic main-report main-neurips main-icml main-iclr main-cvpr main-ieee main-acl; do
    [ -f "$EX/$f.typ" ] || continue
    compile_one "examples/radar-paper/$f" "$f.typ" "$OUT/examples-$f.pdf" "$EX"
  done

  head1 "2/3  Report templates — targets read from templates.tsv"
else
  head1 "Reports only — targets read from templates.tsv"
fi

# One data source: every manifest row whose path is under reports/.
while IFS=$'\t' read -r id format venue template version year origin license path source state; do
  [ -z "$id" ] && continue
  case "$path" in reports/*) ;; *) continue ;; esac
  d="$LIB_ROOT/$path"
  if [ ! -f "$d/example.typ" ]; then
    warn "reports/$id: $path/example.typ not found — skipped"
    continue
  fi
  compile_one "reports/$id/example" "example.typ" "$OUT/report-$id.pdf" "$d"
done < <(manifest_rows)

if [ "$REPORTS_ONLY" = "0" ]; then
  if [ "$QUICK" = "0" ]; then
    head1 "3/3  Vendored library templates (their own demo documents)"
    # <label> <dir> <entry>
    while read -r label dir entry; do
      [ -z "$label" ] && continue
      d="$LIB_ROOT/$dir"
      [ -f "$d/$entry" ] || { warn "$label: $dir/$entry not found"; continue; }
      compile_one "$label" "$entry" "$OUT/lib-$(printf '%s' "$label" | tr '/' '-').pdf" "$d"
    done <<'TARGETS'
typst/neurips          typst/neurips             main.typ
typst/icml             typst/icml                main.typ
typst/iclr             typst/iclr                main.typ
typst/cvpr             typst/cvpr                main.typ
typst/acl              typst/acl                 main.typ
typst/ieee/charged-ieee typst/ieee/charged-ieee  main.typ
typst/ieee/ieeeconf    typst/ieee/bamdone-ieeeconf main.typ
typst/ieee/vgtc        typst/ieee/ieee-vgtc      journal.typ
typst/radar/isprs      typst/radar/isprs         main.typ
typst/generic/jmlr     typst/generic/jmlr        main.typ
typst/generic/tmlr     typst/generic/tmlr        main.typ
TARGETS
  else
    head1 "3/3  Vendored library templates — SKIPPED (--quick)"
  fi
fi

printf '\n'
if [ "$n_fail" = "0" ]; then
  ok "$n_ok compiled, 0 failed"
else
  bad "$n_ok compiled, $n_fail FAILED"
fi

if [ "$REPORT" = "1" ]; then
  REP="$LIB_ROOT/BUILD_REPORT.md"
  {
    printf '# Build Report\n\n'
    printf 'Generated by `scripts/build_all_examples.sh` on %s.\n\n' "$(date -u '+%Y-%m-%d %H:%M UTC')"
    printf 'Typst: `%s`\n\n' "$(typst --version 2>&1 | head -1)"
    printf '## Summary\n\n'
    printf '| Target | Result | Bytes | Warnings |\n|---|---|---|---|\n'
    printf '%s' "$results" | while IFS=$'\t' read -r label status bytes warns log; do
      [ -z "$label" ] && continue
      mark="$status"
      [ "$status" = "OK" ] && mark="✅ OK"
      [ "$status" = "FAIL" ] && mark="❌ **FAIL**"
      printf '| `%s` | %s | %s | %s |\n' "$label" "$mark" "$bytes" "$warns"
    done
    printf '\n**%s compiled, %s failed.**\n\n' "$n_ok" "$n_fail"
    printf '## Per-target detail\n\n'
    printf 'Warnings are listed because they are informative, not because they are\n'
    printf 'failures. The recurring "unknown font family" warning means a template\n'
    printf 'names a commercial font that this machine does not own; Typst then uses\n'
    printf 'the next font in that template'"'"'s fallback chain. The embedded font in the\n'
    printf 'produced PDF is the thing that matters.\n\n'
    printf '%s' "$results" | while IFS=$'\t' read -r label status bytes warns log; do
      [ -z "$label" ] && continue
      printf '### `%s` — %s\n\n' "$label" "$status"
      if [ -f "$log" ]; then
        printf '```\n'
        if [ "$(grep -c . "$log" 2>/dev/null || echo 0)" = "0" ]; then
          printf '(no output — clean compile, zero warnings)\n'
        else
          head -40 "$log"
          [ "$(wc -l < "$log")" -gt 40 ] && printf '\n... (%s more lines in %s)\n' "$(( $(wc -l < "$log") - 40 ))" "${log#$LIB_ROOT/}"
        fi
        printf '```\n\n'
      fi
    done
    printf '## Reproduce\n\n```bash\n./scripts/build_all_examples.sh\n```\n'
  } > "$REP"
  printf '\n'
  ok "wrote ${REP#$LIB_ROOT/}"
fi

[ "$n_fail" = "0" ] || exit 1
exit 0
