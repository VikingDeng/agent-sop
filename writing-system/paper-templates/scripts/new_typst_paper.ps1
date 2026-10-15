# ---------------------------------------------------------------------------
#  new_typst_paper.ps1 — scaffold a layered Typst project from this library.
#
#  Usage:
#    .\new_typst_paper.ps1 -Template chinese-research -Name 2026-q3-survey
#    .\new_typst_paper.ps1 -Template modern-technical -Name design-note -Dir D:\reports
#    .\new_typst_paper.ps1 -Template generic -Name draft-paper   # venue not decided
#    .\new_typst_paper.ps1 -List
#
#  Two project shapes, both layered (main = assembly only):
#
#    LAYERED DOCUMENT — the three daily entries, plus two optional layouts:
#      chinese-research       调研综述 (survey / review)
#      modern-technical       工程技术文档 (engineering / technical document)
#      generic                paper draft, submission target not decided yet
#      academic-clean, chinese-thesis-report   optional report layouts
#
#      main.typ        assembly only (imports meta.typ + content\)
#      meta.typ        metadata, single source of truth
#      content\        chapters / sections (placeholder text to replace)
#      vendor\template frozen copy of the template source (no @local needed)
#      tools\verify_template_lock.py   lock checker (Python 3 stdlib only)
#      template.lock   template id/version/source + per-file sha256
#      Makefile  .gitignore  references.bib  README.md
#      assets\         only when the starter ships assets\ (SVG figures)
#
#    VENUE PAPER (neurips, icml, ...)
#      main.typ  content\  figures\  references.bib  README.md
#
#  Layered path = REGISTERED in templates.tsv as reports\<id>, plus the
#  generic-typst draft. A layered row must ship starter\{main.typ,meta.typ,
#  content\}; that starter is pre-checked, and a missing file is a hard failure
#  - never a fallback to examples\radar-paper\. Every other row is a venue
#  paper and needs its adapted entry in examples\radar-paper\.
#  There is NO silent fallback: an unknown template, an unusable state, a
#  missing starter or a missing entry fails BEFORE anything is created.
#
#  Layered projects: `make build` needs Python 3 + Typst + GNU make (the lock
#  check runs first), and this scaffolder needs Python 3 to write
#  template.lock.  Missing or unusable Python 3 fails BEFORE anything is
#  created; a failed lock write is a failure, never a "created" success.
#  Nothing is ever installed automatically.
#
#  Windows counterpart of new_typst_paper.sh.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$Template,
    [string]$Name,
    [string]$Dir = '.',
    [switch]$Force,
    [switch]$List
)

# Copy failures etc. must stop the script, not print and continue into a
# "created" success message.
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/lib.ps1"

if ($List) { & (Join-Path $PSScriptRoot 'list_templates.ps1'); exit 0 }

if (-not $Template) { Write-Bad '-Template is required'; exit 2 }
if (-not $Name) { Write-Bad '-Name is required'; exit 2 }
if ([string]::IsNullOrWhiteSpace($Dir)) { Write-Bad '-Dir must not be empty'; exit 2 }

# Accept both the short form ("neurips") and the manifest id ("neurips-typst").
if (-not (Test-ManifestHas -Id $Template)) {
    if (Test-ManifestHas -Id "$Template-typst") { $Template = "$Template-typst" }
    else {
        Write-Bad "unknown template '$Template'"
        Write-Info 'run: .\list_templates.ps1'
        exit 2
    }
}

$manifestEntry = Get-ManifestEntry -Id $Template
$base = $Template -replace '-typst$', ''
$mPath = $manifestEntry.Path
$version = $manifestEntry.Version
$origin = $manifestEntry.Origin
$license = $manifestEntry.License

if ($manifestEntry.State -in @('no-typst-template', 'broken')) {
    Write-Bad "template '$Template' is marked '$($manifestEntry.State)' - there is no reliable Typst template for it."
    Write-Info "Use the official LaTeX kit instead: latex\$base  (see TEMPLATE_CATALOG.md)"
    if ($mPath -and (Test-Path (Join-Path $LibRoot $mPath))) {
        Write-Info "no scaffolded Typst entry; the library keeps only notes here: $mPath/"
    }
    Write-Info 'Or pick the closest working Typst template: .\list_templates.ps1 -State ok'
    exit 3
}

# ---- classify BEFORE creating anything -------------------------------------
# A LAYERED document is decided by the MANIFEST, never by what happens to exist
# on disk: every reports\<id> row (report templates) and generic-typst (the
# "no target yet" paper draft) are layered BY REGISTRATION. Their
# starter\{main.typ,meta.typ,content\} is then PRE-CHECKED.
# Deciding this on a starter\ directory would let a missing starter silently
# fall back to the venue branch below - for generic that is
# examples\radar-paper\main-generic.typ, which needs the @local package cache
# and produces the old project shape instead of failing.
# Everything else is a VENUE PAPER and needs its adapted entry in
# examples\radar-paper\. Missing starter or missing entry -> hard failure,
# never a fallback to another template.
$isLayered = $false
$entrySrc = $null
$starter = $null
$vendorSrc = $null
$dirName = $null
if ($mPath -like 'reports/*') { $isLayered = $true }
if ($Template -eq 'generic-typst') { $isLayered = $true }

if ($isLayered) {
    $vendorSrc = Join-Path $LibRoot $mPath
    $starter = Join-Path $vendorSrc 'starter'
    $dirName = Split-Path $mPath -Leaf
    foreach ($need in 'main.typ', 'meta.typ', 'content') {
        if (-not (Test-Path (Join-Path $starter $need))) {
            Write-Bad "template '$Template' is registered as a layered document, but its starter is missing: $mPath/starter/$need"
            Write-Info "restore $mPath/starter/{main.typ,meta.typ,content/} and re-run"
            Write-Info 'this script will NOT fall back to a venue entry; nothing was created'
            exit 3
        }
    }
    foreach ($need in "$dirName.typ", 'typst.toml') {
        if (-not (Test-Path (Join-Path $vendorSrc $need))) {
            Write-Bad "template '$Template' is incomplete: $mPath needs $need"
            exit 3
        }
    }
}
else {
    $entrySrc = Join-Path $LibRoot "examples/radar-paper/main-$base.typ"
    if (-not (Test-Path $entrySrc)) {
        Write-Bad "template '$Template' has no scaffolded entry: missing examples/radar-paper/main-$base.typ"
        if ($mPath -and (Test-Path (Join-Path $LibRoot $mPath))) {
            Write-Info "the original template IS in this library: $mPath/"
        }
        $adapted = @(Get-ChildItem (Join-Path $LibRoot 'examples/radar-paper') -Filter 'main-*.typ' |
            Select-Object -ExpandProperty Name)
        Write-Info "adapted entry files: $($adapted -join ' ')"
        exit 3
    }
}

# ---- required toolchain (checked BEFORE creating anything) -----------------
# A layered project is not usable without template.lock (make build verifies it
# first), so a missing/unusable Python 3 is a hard failure here: fail before
# any directory exists. Nothing is ever installed automatically.
$py = $null
if ($isLayered) {
    if (Test-Have 'python3') { $py = 'python3' } elseif (Test-Have 'python') { $py = 'python' }
    if (-not $py) {
        Write-Bad 'layered projects need Python 3 to write template.lock, but neither python3 nor python was found'
        Write-Info 'install Python 3 yourself and re-run; this script installs nothing, and no target was created'
        exit 3
    }
    & $py -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Bad "'$py' is not a usable Python 3 (version probe exit code $LASTEXITCODE)"
        Write-Info 'point PATH at a real Python 3 and re-run; no target was created'
        exit 3
    }
}

# ---- target directory ------------------------------------------------------
$target = Join-Path $Dir $Name
if (Test-Path $target) {
    if (-not (Test-Path $target -PathType Container)) {
        Write-Bad "$target exists and is not a directory"
        exit 2
    }
    $existing = @(Get-ChildItem -Force $target -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 0 -and -not $Force) {
        Write-Bad "$target exists and is not empty (use -Force to write into it)"
        exit 2
    }
}

if ($isLayered) {
    foreach ($d in 'content', 'vendor/template', 'tools') {
        New-Item -ItemType Directory -Force -Path (Join-Path $target $d) | Out-Null
    }
    Copy-Item -Path (Join-Path $starter 'main.typ') -Destination (Join-Path $target 'main.typ') -Force
    Copy-Item -Path (Join-Path $starter 'meta.typ') -Destination (Join-Path $target 'meta.typ') -Force
    Copy-Item -Path (Join-Path $starter 'content/*') -Destination (Join-Path $target 'content') -Recurse -Force

    # ---- vendor: ONLY the template source, its manifest and its licence -----
    $vendorTemplate = Join-Path $target 'vendor/template'
    Copy-Item -Path (Join-Path $vendorSrc "$dirName.typ") -Destination $vendorTemplate -Force
    Copy-Item -Path (Join-Path $vendorSrc 'typst.toml') -Destination $vendorTemplate -Force
    $licFile = $null
    foreach ($cand in 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING') {
        if (Test-Path (Join-Path $vendorSrc $cand)) {
            Copy-Item -Path (Join-Path $vendorSrc $cand) -Destination $vendorTemplate -Force
            $licFile = $cand
            break
        }
    }
    $licLine = if ($licFile) { ", ``$licFile``" } else { '' }
    $sourceMd = @'
# 模板快照来源

- 模板 id：`__TEMPLATE__`
- 版本：`__VERSION__`
- 来源：本地模板库 `__MPATH__/`（origin: __ORIGIN__，license: __LICENSE__）
- 快照文件：`__DIRNAME__.typ`, `typst.toml`__LICLINE__
- 复制时机：由 `scripts/new_typst_paper.ps1` 创建工程时一次性复制；
  每个文件的 sha256 记在工程根的 `template.lock`。

本目录是**只读快照**，不要手改；升级与校验流程见工程 `README.md` 第七节。
'@
    $sourceMd = $sourceMd.Replace('__TEMPLATE__', $Template).Replace('__VERSION__', $version).
        Replace('__MPATH__', $mPath).Replace('__ORIGIN__', $origin).
        Replace('__LICENSE__', $license).Replace('__DIRNAME__', $dirName).
        Replace('__LICLINE__', $licLine)
    Set-Content -LiteralPath (Join-Path $vendorTemplate 'SOURCE.md') -Value $sourceMd -Encoding UTF8

    # ---- shared static assets (single source: shared/report-project/) ------
    Copy-Item -Path (Join-Path $LibRoot 'shared/report-project/Makefile') -Destination $target -Force
    Copy-Item -Path (Join-Path $LibRoot 'shared/report-project/.gitignore') -Destination $target -Force
    Copy-Item -Path (Join-Path $LibRoot 'shared/report-project/tools/verify_template_lock.py') `
        -Destination (Join-Path $target 'tools') -Force
    $readmeTemplate = Get-Content -LiteralPath (Join-Path $LibRoot 'shared/report-project/README.md') -Raw
    $readme = $readmeTemplate.Replace('__PROJECT_NAME__', $Name).
        Replace('__TEMPLATE_ID__', $dirName).Replace('__TEMPLATE_PATH__', $mPath).
        Replace('__TEMPLATE_VERSION__', $version).Replace('__TEMPLATE_ORIGIN__', $origin).
        Replace('__TEMPLATE_LICENSE__', $license).
        Replace('__SCAFFOLD_SCRIPT__', 'scripts/new_typst_paper.ps1')
    Set-Content -LiteralPath (Join-Path $target 'README.md') -Value $readme -Encoding UTF8

    # ---- bibliography + starter assets ---------------------------------------
    # The three daily starters ship their own references.bib (one real entry,
    # typesetting demo only) and the assets\ their content\ imports. Older
    # starters have neither: they keep the previous behaviour (shared radar
    # bibliography) and no assets\ directory is created for them.
    $starterBib = Join-Path $starter 'references.bib'
    if (Test-Path $starterBib) {
        Copy-Item -Path $starterBib -Destination (Join-Path $target 'references.bib') -Force
    }
    else {
        Copy-Item -Path (Join-Path $LibRoot 'shared/bibliography/radar-ai4science.bib') `
            -Destination (Join-Path $target 'references.bib') -Force
    }
    $starterAssets = Join-Path $starter 'assets'
    if (Test-Path $starterAssets -PathType Container) {
        New-Item -ItemType Directory -Force -Path (Join-Path $target 'assets') | Out-Null
        Copy-Item -Path (Join-Path $starterAssets '*') -Destination (Join-Path $target 'assets') -Recurse -Force
    }

    # ---- lock: created ONCE here; later upgrades rewrite it explicitly -----
    # The native exit code is checked explicitly ($LASTEXITCODE): a project
    # without template.lock must not be reported as created.
    Push-Location $target
    try {
        & $py 'tools/verify_template_lock.py' --write --template $dirName --source $mPath
        $lockExit = $LASTEXITCODE
    }
    finally { Pop-Location }
    if ($lockExit -ne 0) {
        Write-Bad "template.lock generation failed (exit $lockExit) - $target is INCOMPLETE"
        Write-Info "retry:  cd $target; $py tools\verify_template_lock.py --write --template $dirName --source $mPath"
        Write-Info 'or delete the target and re-run this script (nothing is auto-deleted)'
        exit 4
    }

    Write-Ok "created $target  (layered project, template $dirName $version)"
    ''
    Write-Info "next:  cd $target; make build       # -> build/main.pdf"
    Write-Info 'edit:  meta.typ first, then content\*.typ (placeholder text)'
    Write-Info 'note:  vendor\template\ is a frozen snapshot; make build checks template.lock first (Python 3 + Typst + GNU make)'
    exit 0
}

# ---- venue paper -----------------------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $target 'content') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $target 'figures') | Out-Null
Copy-Item -Path (Join-Path $LibRoot 'shared/content/*') -Destination (Join-Path $target 'content') -Recurse -Force
$figSrc = Join-Path $LibRoot 'examples/radar-paper/figures'
Get-ChildItem -Path $figSrc -Filter *.svg -ErrorAction SilentlyContinue |
    Copy-Item -Destination (Join-Path $target 'figures') -Force
Copy-Item -Path (Join-Path $LibRoot 'shared/bibliography/radar-ai4science.bib') `
    -Destination (Join-Path $target 'references.bib') -Force
Copy-Item -Path $entrySrc -Destination (Join-Path $target 'main.typ') -Force

# README
$readme = @"
# $Name

Created from template ``$Template`` by ``scripts/new_typst_paper.ps1``.

## Build

``````powershell
typst compile main.typ          # -> main.pdf
typst watch   main.typ          # live rebuild
``````

## Layout

| Path | What goes here |
|---|---|
| ``main.typ`` | Entry file for the **$Template** template. Venue-specific. Switching venue means replacing this file **and re-checking the result**: page breaks, caption placement and citation syntax all change with the template, and nothing is converted automatically. |
| ``content\`` | Your prose. Venue-agnostic; never import a venue package in here. |
| ``figures\`` | Figures. Vector placeholders are included - replace them. |
| ``references.bib`` | Bibliography. |
| ``content\_adapt.typ`` | Maps the neutral author schema into each venue's author shape. |

## Changing venue

Keep ``content\`` and copy a different entry file over ``main.typ``:

``````powershell
Copy-Item "$LibRoot\examples\radar-paper\main-icml.typ" main.typ -Force
typst compile main.typ
``````

The prose is reusable; the rendering is not automatically equivalent. Compare the
new PDF against the old one (pages, per-page text, figure/table numbering) before
you rely on it. Moving between Typst and LaTeX requires rewriting the body by
hand - there is no converter.

## Rules that keep it portable

1. In ``content\``, use **only core Typst** - ``=``, ``#figure``, ``#table``, math, ``@cite``.
   Do not import a venue package there, or the body stops being portable.
2. Give every label a typed prefix (``fig:``, ``tbl:``, ``sec:``, ``eq:``) and never put a
   colon in a bibliography key. The ACL adapter relies on that convention to tell
   citations from cross-references.
3. Put author/affiliation shaping in ``content\_adapt.typ``, not in the prose.
"@
Set-Content -LiteralPath (Join-Path $target 'README.md') -Value $readme -Encoding UTF8

Write-Ok "created $target"
''
Write-Info "next:  cd $target; typst compile main.typ"
Write-Info 'edit:  content\_meta.typ  (title, authors, abstract)'
