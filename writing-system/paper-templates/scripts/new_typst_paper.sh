#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  new_typst_paper.sh — scaffold a layered Typst project from this library.
#
#  Usage:
#    ./new_typst_paper.sh -t chinese-research -n 2026-q3-survey
#    ./new_typst_paper.sh -t modern-technical -n design-note -d ~/reports
#    ./new_typst_paper.sh -t generic -n draft-paper      # target venue not decided
#    ./new_typst_paper.sh --list
#
#  Options:
#    -t, --template <id>   template id (see --list, or TEMPLATE_CATALOG.md)
#    -n, --name <name>     project directory name
#    -d, --dir <parent>    where to create it (default: current directory)
#    --force               allow writing into a non-empty target directory
#
#  Two project shapes, both layered (main = assembly only):
#
#    LAYERED DOCUMENT — the three daily entries, plus two optional layouts:
#      chinese-research       调研综述 (survey / review)
#      modern-technical       工程技术文档 (engineering / technical document)
#      generic                paper draft, submission target not decided yet
#      academic-clean, chinese-thesis-report   optional report layouts
#
#      main.typ        assembly only (imports meta.typ + content/)
#      meta.typ        metadata, single source of truth
#      content/        chapters / sections (placeholder text to replace)
#      vendor/template frozen copy of the template source (no @local needed)
#      tools/verify_template_lock.py   lock checker (Python 3 stdlib only)
#      template.lock   template id/version/source + per-file sha256
#      Makefile  .gitignore  references.bib  README.md
#      assets/         only when the starter ships assets/ (SVG figures)
#
#    VENUE PAPER (neurips, icml, ...)
#      main.typ        entry for the chosen venue, imports a @local/@preview package
#      content/        YOUR PROSE (content/_meta.typ first)
#      figures/  references.bib  README.md
#
#  Layered path = REGISTERED in templates.tsv as reports/<id>, plus the
#  generic-typst draft. A layered row must ship starter/{main.typ,meta.typ,
#  content/}; that starter is pre-checked, and a missing file is a hard failure
#  — never a fallback to examples/radar-paper/. Every other row is a venue
#  paper and needs its adapted entry in examples/radar-paper/.
#  There is NO silent fallback: an unknown template, an unusable state, a
#  missing starter or a missing entry fails BEFORE anything is created.
#
#  Layered projects: `make build` needs Python 3 + Typst + GNU make (the lock
#  check runs first), and this scaffolder needs Python 3 to write
#  template.lock.  Missing or unusable Python 3 fails BEFORE anything is
#  created; a failed lock write is a failure, never a "created" success.
#  Nothing is ever installed automatically.
#
#  Bash counterpart of new_typst_paper.ps1.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib.sh"

TEMPLATE=""
NAME=""
PARENT="."
FORCE=0

usage() { sed -n '2,53p' "$0"; }

while [ $# -gt 0 ]; do
  case "$1" in
    -t|--template) TEMPLATE="${2:-}"; shift 2 ;;
    -n|--name)     NAME="${2:-}"; shift 2 ;;
    -d|--dir)      PARENT="${2:-}"; shift 2 ;;
    --force)       FORCE=1; shift ;;
    --list)        exec "$SCRIPT_DIR/list_templates.sh" ;;
    -h|--help)     usage; exit 0 ;;
    *) bad "unknown option: $1"; usage; exit 2 ;;
  esac
done

[ -z "$TEMPLATE" ] && { bad "-t/--template is required"; usage; exit 2; }
[ -z "$NAME" ]     && { bad "-n/--name is required"; usage; exit 2; }
[ -z "$PARENT" ]   && { bad "-d/--dir must not be empty"; exit 2; }

# Accept both the short form ("neurips") and the manifest id ("neurips-typst").
if ! manifest_has "$TEMPLATE"; then
  if manifest_has "${TEMPLATE}-typst"; then
    TEMPLATE="${TEMPLATE}-typst"
  else
    bad "unknown template '$TEMPLATE'"
    info "run: $SCRIPT_DIR/list_templates.sh"
    exit 2
  fi
fi

BASE="${TEMPLATE%%-typst}"
MPATH="$(manifest_field "$TEMPLATE" 9)"
VERSION="$(manifest_field "$TEMPLATE" 5)"
ORIGIN="$(manifest_field "$TEMPLATE" 7)"
LICENSE="$(manifest_field "$TEMPLATE" 8)"
STATE="$(manifest_field "$TEMPLATE" 11)"

if [ "$STATE" = "no-typst-template" ] || [ "$STATE" = "broken" ]; then
  bad "template '$TEMPLATE' is marked '$STATE' — there is no reliable Typst template for it."
  info "Use the official LaTeX kit instead: latex/${BASE}  (see TEMPLATE_CATALOG.md)"
  if [ -n "$MPATH" ] && [ -e "$LIB_ROOT/$MPATH" ]; then
    info "no scaffolded Typst entry; the library keeps only notes here: $MPATH/"
  fi
  info "Or pick the closest working Typst template: ./list_templates.sh --state ok"
  exit 3
fi

# ---- classify BEFORE creating anything -------------------------------------
# A LAYERED document is decided by the MANIFEST, never by what happens to exist
# on disk: every reports/<id> row (report templates) and generic-typst (the
# "no target yet" paper draft) are layered BY REGISTRATION. Their
# starter/{main.typ,meta.typ,content/} is then PRE-CHECKED.
# Deciding this on `-d starter/` would let a missing starter silently fall back
# to the venue branch below — for generic that is
# examples/radar-paper/main-generic.typ, which needs the @local package cache
# and produces the old project shape instead of failing.
# Everything else is a VENUE PAPER and needs its adapted entry in
# examples/radar-paper/. Missing starter or missing entry -> hard failure,
# never a fallback to another template.
IS_LAYERED=0
STARTER=""
VENDOR_SRC=""
ENTRY_SRC=""
DIR_NAME=""
case "$MPATH" in
  reports/*) IS_LAYERED=1 ;;
esac
if [ "$TEMPLATE" = "generic-typst" ]; then
  IS_LAYERED=1
fi

if [ "$IS_LAYERED" = "1" ]; then
  VENDOR_SRC="$LIB_ROOT/$MPATH"
  STARTER="$VENDOR_SRC/starter"
  DIR_NAME="${MPATH##*/}"
  for need in main.typ meta.typ content; do
    if [ ! -e "$STARTER/$need" ]; then
      bad "template '$TEMPLATE' is registered as a layered document, but its starter is missing: $MPATH/starter/$need"
      info "restore $MPATH/starter/{main.typ,meta.typ,content/} and re-run"
      info "this script will NOT fall back to a venue entry; nothing was created"
      exit 3
    fi
  done
  if [ ! -f "$VENDOR_SRC/$DIR_NAME.typ" ] || [ ! -f "$VENDOR_SRC/typst.toml" ]; then
    bad "template '$TEMPLATE' is incomplete: $MPATH needs $DIR_NAME.typ and typst.toml"
    exit 3
  fi
else
  ENTRY_SRC="$LIB_ROOT/examples/radar-paper/main-$BASE.typ"
  if [ ! -f "$ENTRY_SRC" ]; then
    bad "template '$TEMPLATE' has no scaffolded entry: missing examples/radar-paper/main-$BASE.typ"
    if [ -n "$MPATH" ] && [ -e "$LIB_ROOT/$MPATH" ]; then
      info "the original template IS in this library: $MPATH/"
    fi
    info "adapted entry files: $(cd "$LIB_ROOT/examples/radar-paper" && ls main-*.typ 2>/dev/null | tr '\n' ' ')"
    exit 3
  fi
fi

# ---- required toolchain (checked BEFORE creating anything) -----------------
# A layered project is not usable without template.lock (make build verifies it
# first), so a missing/unusable Python 3 is a hard failure here: fail before
# any directory exists. Nothing is ever installed automatically.
PY=""
if [ "$IS_LAYERED" = "1" ]; then
  if have python3; then PY=python3; elif have python; then PY=python; fi
  if [ -z "$PY" ]; then
    bad "layered projects need Python 3 to write template.lock, but neither python3 nor python was found"
    info "install Python 3 yourself and re-run; this script installs nothing, and no target was created"
    exit 3
  fi
  if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
    bad "'$PY' is not a usable Python 3 (version probe failed)"
    info "point PATH at a real Python 3 and re-run; no target was created"
    exit 3
  fi
fi

# ---- target directory ------------------------------------------------------
TARGET="$PARENT/$NAME"
if [ -e "$TARGET" ]; then
  if [ ! -d "$TARGET" ]; then
    bad "$TARGET exists and is not a directory"
    exit 2
  fi
  if [ "$FORCE" != "1" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
    bad "$TARGET exists and is not empty (use --force to write into it)"
    exit 2
  fi
fi

if [ "$IS_LAYERED" = "1" ]; then
  mkdir -p "$TARGET/content" "$TARGET/vendor/template" "$TARGET/tools"
  cp "$STARTER/main.typ" "$TARGET/main.typ"
  cp "$STARTER/meta.typ" "$TARGET/meta.typ"
  cp -R "$STARTER/content/." "$TARGET/content/"

  # ---- vendor: ONLY the template source, its manifest and its licence ------
  cp "$VENDOR_SRC/$DIR_NAME.typ" "$TARGET/vendor/template/$DIR_NAME.typ"
  cp "$VENDOR_SRC/typst.toml"    "$TARGET/vendor/template/typst.toml"
  LIC_FILE=""
  for cand in LICENSE LICENSE.md LICENSE.txt COPYING; do
    if [ -f "$VENDOR_SRC/$cand" ]; then
      cp "$VENDOR_SRC/$cand" "$TARGET/vendor/template/$cand"
      LIC_FILE="$cand"
      break
    fi
  done
  LIC_LINE=""
  [ -n "$LIC_FILE" ] && LIC_LINE=", \`$LIC_FILE\`"
  cat > "$TARGET/vendor/template/SOURCE.md" <<EOF
# 模板快照来源

- 模板 id：\`$TEMPLATE\`
- 版本：\`$VERSION\`
- 来源：本地模板库 \`$MPATH/\`（origin: $ORIGIN，license: $LICENSE）
- 快照文件：\`$DIR_NAME.typ\`, \`typst.toml\`$LIC_LINE
- 复制时机：由 \`scripts/new_typst_paper.sh\` 创建工程时一次性复制；
  每个文件的 sha256 记在工程根的 \`template.lock\`。

本目录是**只读快照**，不要手改；升级与校验流程见工程 \`README.md\` 第七节。
EOF

  # ---- shared static assets (single source: shared/report-project/) --------
  cp "$LIB_ROOT/shared/report-project/Makefile" "$TARGET/Makefile"
  cp "$LIB_ROOT/shared/report-project/.gitignore" "$TARGET/.gitignore"
  cp "$LIB_ROOT/shared/report-project/tools/verify_template_lock.py" \
     "$TARGET/tools/verify_template_lock.py"
  # ---- README: literal substitution, values passed via argv ---------------
  # Project names may contain spaces, &, |, ... — sed (and any shell splicing)
  # would corrupt or break on them, so the values are handed to Python as argv
  # and applied with str.replace; nothing is spliced into code or eval'd.
  if ! "$PY" -c '
import sys
(src, dst, name, tid, tpath, tver, torigin, tlic) = sys.argv[1:9]
text = open(src, encoding="utf-8").read()
for key, val in (
    ("__PROJECT_NAME__", name),
    ("__TEMPLATE_ID__", tid),
    ("__TEMPLATE_PATH__", tpath),
    ("__TEMPLATE_VERSION__", tver),
    ("__TEMPLATE_ORIGIN__", torigin),
    ("__TEMPLATE_LICENSE__", tlic),
    ("__SCAFFOLD_SCRIPT__", "scripts/new_typst_paper.sh"),
):
    text = text.replace(key, val)
with open(dst, "w", encoding="utf-8") as fh:
    fh.write(text)
' "$LIB_ROOT/shared/report-project/README.md" "$TARGET/README.md" \
       "$NAME" "$DIR_NAME" "$MPATH" "$VERSION" "$ORIGIN" "$LICENSE"; then
    bad "rendering $TARGET/README.md failed — the project is INCOMPLETE"
    info "fix the Python error above, delete $TARGET, and re-run (nothing is auto-deleted)"
    exit 4
  fi

  # ---- bibliography + starter assets ---------------------------------------
  # The three daily starters ship their own references.bib (one real entry,
  # typesetting demo only) and the assets/ their content/ imports. Older
  # starters have neither: they keep the previous behaviour (shared radar
  # bibliography) and no assets/ directory is created for them.
  if [ -f "$STARTER/references.bib" ]; then
    cp "$STARTER/references.bib" "$TARGET/references.bib"
  else
    cp "$LIB_ROOT/shared/bibliography/radar-ai4science.bib" "$TARGET/references.bib"
  fi
  if [ -d "$STARTER/assets" ]; then
    mkdir -p "$TARGET/assets"
    cp -R "$STARTER/assets/." "$TARGET/assets/"
  fi

  # ---- lock: created ONCE here; later upgrades rewrite it explicitly -------
  # Return code is checked: a project without template.lock must not be
  # reported as created.
  if ! ( cd "$TARGET" && "$PY" tools/verify_template_lock.py --write \
        --template "$DIR_NAME" --source "$MPATH" ); then
    bad "template.lock generation failed — $TARGET is INCOMPLETE (no template.lock)"
    info "retry:  cd $TARGET && $PY tools/verify_template_lock.py --write --template $DIR_NAME --source $MPATH"
    info "or delete $TARGET and re-run this script (nothing is auto-deleted)"
    exit 4
  fi

  ok "created $TARGET  (layered project, template $DIR_NAME $VERSION)"
  printf '\n'
  info "next:  cd $TARGET && make build       # -> build/main.pdf"
  info "edit:  meta.typ first, then content/*.typ (placeholder text)"
  info "note:  vendor/template/ is a frozen snapshot; make build checks template.lock first (Python 3 + Typst + GNU make)"
  exit 0
fi

# ---- venue paper -----------------------------------------------------------
mkdir -p "$TARGET/content" "$TARGET/figures"
cp "$LIB_ROOT/shared/content/." "$TARGET/content/" -r
cp "$LIB_ROOT/examples/radar-paper/figures/"*.svg "$TARGET/figures/" 2>/dev/null || true
cp "$LIB_ROOT/shared/bibliography/radar-ai4science.bib" "$TARGET/references.bib"
cp "$ENTRY_SRC" "$TARGET/main.typ"
# The example entries say `main-<venue>.typ` in their header comment; fix that
# so the new project does not claim to be something it is not.
sed -i "s|^//  main-.*\.typ —|//  main.typ —|" "$TARGET/main.typ" 2>/dev/null || true

cat > "$TARGET/README.md" <<EOF
# $NAME

Created from template \`$TEMPLATE\` by \`scripts/new_typst_paper.sh\`.

## Build

\`\`\`bash
typst compile main.typ          # -> main.pdf
typst watch   main.typ          # live rebuild
\`\`\`

## Layout

| Path | What goes here |
|---|---|
| \`main.typ\` | Entry file for the **$TEMPLATE** template. Venue-specific. Switching venue means replacing this file **and re-checking the result**: page breaks, caption placement and citation syntax all change with the template, and nothing is converted automatically. |
| \`content/\` | Your prose. Venue-agnostic; never import a venue package in here. |
| \`figures/\` | Figures. Two vector placeholders are included — replace them. |
| \`references.bib\` | Bibliography. |
| \`content/_adapt.typ\` | Maps the neutral author schema into each venue's author shape. |

## Changing venue

Keep \`content/\` and copy a different entry file over \`main.typ\`, e.g.

\`\`\`bash
cp $LIB_ROOT/examples/radar-paper/main-icml.typ main.typ
typst compile main.typ
\`\`\`

The prose is reusable; the rendering is not automatically equivalent. Compare the
new PDF against the old one (pages, per-page text, figure/table numbering) before
you rely on it. Moving between Typst and LaTeX requires rewriting the body by
hand — there is no converter.

## Rules that keep it portable

1. In \`content/\`, use **only core Typst** — \`=\`, \`#figure\`, \`#table\`, math, \`@cite\`.
   Do not import a venue package there, or the body stops being portable.
2. Give every label a typed prefix (\`fig:\`, \`tbl:\`, \`sec:\`, \`eq:\`) and never put a
   colon in a bibliography key. The ACL adapter relies on that convention to tell
   citations from cross-references.
3. Put author/affiliation shaping in \`content/_adapt.typ\`, not in the prose.
EOF

ok "created $TARGET"
printf '\n'
info "next:  cd $TARGET && typst compile main.typ"
info "edit:  content/_meta.typ  (title, authors, abstract)"
