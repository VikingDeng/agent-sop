#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  list_templates.sh — print the template inventory from templates.tsv.
#
#  Usage:
#    ./list_templates.sh              # all rows, aligned columns
#    ./list_templates.sh --format typst
#    ./list_templates.sh --state ok
#    ./list_templates.sh --md         # markdown table
#    ./list_templates.sh --paths      # just the ids and paths, for scripting
#
#  Bash counterpart of list_templates.ps1.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib.sh"

FILTER_FIELD=""
FILTER_VALUE=""
MODE="table"
while [ $# -gt 0 ]; do
  case "$1" in
    --format) FILTER_FIELD=2; FILTER_VALUE="$2"; shift 2 ;;
    --state)  FILTER_FIELD=11; FILTER_VALUE="$2"; shift 2 ;;
    --origin) FILTER_FIELD=7; FILTER_VALUE="${2:-}"; shift 2 ;;
    --md)     MODE="md"; shift ;;
    --paths)  MODE="paths"; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) bad "unknown option: $1"; exit 2 ;;
  esac
done

rows=""
while IFS=$'\t' read -r id format venue template version year origin license path source state; do
  [ -z "$id" ] && continue
  if [ -n "$FILTER_FIELD" ]; then
    actual="$(printf '%s\n' "$id" "$format" "$venue" "$template" "$version" "$year" "$origin" "$license" "$path" "$source" "$state" | sed -n "${FILTER_FIELD}p")"
    [ "$actual" != "$FILTER_VALUE" ] && continue
  fi
  rows="$rows$(printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$id" "$format" "$venue" "$template" "$version" "$year" "$origin" "$license" "$path" "$state")"$'\n'
done < <(manifest_rows)

if [ -z "$rows" ]; then
  warn "no templates matched"
  exit 0
fi

case "$MODE" in
  paths)
    printf '%s' "$rows" | while IFS=$'\t' read -r id format venue template version year origin license path state; do
      [ -z "$id" ] && continue
      printf '%-24s %s\n' "$id" "$LIB_ROOT/$path"
    done
    ;;
  md)
    printf '| ID | Format | Venue | Template | Version | Year | Origin | License | Path | State |\n'
    printf '|---|---|---|---|---|---|---|---|---|---|\n'
    printf '%s' "$rows" | while IFS=$'\t' read -r id format venue template version year origin license path state; do
      [ -z "$id" ] && continue
      printf '| %s | %s | %s | %s | %s | %s | %s | %s | `%s` | %s |\n' \
        "$id" "$format" "$venue" "$template" "$version" "$year" "$origin" "$license" "$path" "$state"
    done
    ;;
  *)
    head1 "Template inventory  ($MANIFEST)"
    printf '%-22s %-6s %-24s %-19s %-8s %-8s %-15s %-11s %s\n' \
      "ID" "FORMAT" "VENUE" "TEMPLATE" "VERSION" "YEAR" "ORIGIN" "LICENSE" "STATE"
    printf '%.0s-' {1..140}; printf '\n'
    printf '%s' "$rows" | while IFS=$'\t' read -r id format venue template version year origin license path state; do
      [ -z "$id" ] && continue
      color="$C_RESET"
      case "$state" in ok) color="$C_GREEN" ;; patched) color="$C_YELLOW" ;; no-typst-template) color="$C_DIM" ;; broken) color="$C_RED" ;; esac
      printf '%-22s %-6s %-24s %-19s %-8s %-8s %-15s %-11s %s%s%s\n' \
        "$id" "$format" "${venue:0:24}" "${template:0:19}" "$version" "$year" "$origin" "$license" "$color" "$state" "$C_RESET"
    done
    printf '\n'
    info "origin: official = venue/publisher | typst-official = Typst project | community = third-party reimplementation | own = this library"
    info "state:  ok | patched (locally fixed to compile) | no-typst-template | broken"
    ;;
esac
exit 0
