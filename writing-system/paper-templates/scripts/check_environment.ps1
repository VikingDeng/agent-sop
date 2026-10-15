# ---------------------------------------------------------------------------
#  check_environment.ps1 — report which writing tools are present.
#
#  Usage:
#    .\check_environment.ps1            # terminal report
#    .\check_environment.ps1 -Markdown  # paste-ready Markdown
#
#  Windows counterpart of check_environment.sh. Always exits 0: it reports,
#  it does not gate.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [switch]$Markdown
)

. "$PSScriptRoot/lib.ps1"

# <command> <--version flag> <human label>
$tools = @(
    @('typst', '--version', 'Typst CLI'),
    @('xelatex', '--version', 'XeLaTeX (TeX Live / MiKTeX)'),
    @('lualatex', '--version', 'LuaLaTeX'),
    @('pdflatex', '--version', 'pdfLaTeX'),
    @('latexmk', '--version', 'latexmk'),
    @('tlmgr', '--version', 'tlmgr (TeX Live manager)'),
    @('biber', '--version', 'biber (biblatex backend)'),
    @('bibtex', '--version', 'BibTeX'),
    @('git', '--version', 'Git'),
    @('python', '--version', 'Python'),
    @('code', '--version', 'VS Code CLI')
)

$results = @()
$missing = @()
foreach ($t in $tools) {
    $name = $t[0]; $flag = $t[1]; $label = $t[2]
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        $ver = ''
        try {
            # Several of these print their banner to stderr, and `--version` is
            # not universally supported (tlmgr wants `--version`, biber too),
            # so treat any output as a version string.
            $raw = & $name $flag 2>&1 | Select-Object -First 1
            $ver = ($raw | Out-String).Trim()
        }
        catch { $ver = '(version probe failed)' }
        $results += [pscustomobject]@{
            Tool = $name; Label = $label; Version = $ver
            Path = $cmd.Source; Present = $true
        }
    }
    else {
        $missing += $name
        $results += [pscustomobject]@{
            Tool = $name; Label = $label; Version = 'MISSING'
            Path = '-'; Present = $false
        }
    }
}

# ---- VS Code extensions ----------------------------------------------------
$extensions = @()
if (Get-Command code -ErrorAction SilentlyContinue) {
    try {
        $list = (& code --list-extensions 2>$null) | Where-Object {
            $_ -match 'tinymist|typst|latex-workshop'
        }
        $extensions = @($list)
    }
    catch { }
}

# ---- fonts -----------------------------------------------------------------
$cjkCount = 0; $serifCjk = 0; $sansCjk = 0; $gyre = 0
$fcList = Get-Command fc-list -ErrorAction SilentlyContinue
if ($fcList) {
    try {
        $cjkCount = @(& fc-list ':lang=zh' 2>$null).Count
        $serifCjk = @(& fc-list 2>$null | Select-String -SimpleMatch 'Noto Serif CJK SC').Count
        $sansCjk = @(& fc-list 2>$null | Select-String -SimpleMatch 'Noto Sans CJK SC').Count
        $gyre = @(& fc-list 2>$null | Select-String -SimpleMatch 'TeX Gyre').Count
    }
    catch { }
}
else {
    Write-Info 'fc-list not available (normal on Windows) - font inventory skipped.'
}

# ---- typst packages --------------------------------------------------------
$pkgRoot = Get-TypstPackageRoot
$cacheRoot = Get-TypstCacheRoot
$previewCount = 0; $localCount = 0
$previewDir = Join-Path $cacheRoot 'preview'
$localDir = Join-Path $pkgRoot 'local'
if (Test-Path $previewDir) {
    $previewCount = @(Get-ChildItem $previewDir -Directory -ErrorAction SilentlyContinue).Count
}
if (Test-Path $localDir) {
    $localCount = @(Get-ChildItem $localDir -Directory -ErrorAction SilentlyContinue).Count
}

# ---- emit ------------------------------------------------------------------
if ($Markdown) {
    '| Tool | Version | Path |'
    '|---|---|---|'
    foreach ($r in $results) {
        $v = if ($r.Present) { $r.Version } else { '**MISSING**' }
        "| ``$($r.Tool)`` | $v | ``$($r.Path)`` |"
    }
    ''
    '| Item | Value |'
    '|---|---|'
    "| Typst data dir (@local) | ``$pkgRoot`` |"
    "| Typst cache dir (@preview) | ``$cacheRoot`` |"
    "| @preview packages | $previewCount |"
    "| @local packages | $localCount |"
    "| CJK fonts | $cjkCount |"
    "| Noto Serif CJK SC | $serifCjk |"
    "| Noto Sans CJK SC | $sansCjk |"
    ''
    '| VS Code extension |  |'
    '|---|---|'
    foreach ($e in $extensions) { "| ``$e`` | installed |" }
}
else {
    Write-Head 'Command line tools'
    '{0,-10} {1,-52} {2}' -f 'TOOL', 'PATH', 'VERSION'
    '-' * 110
    foreach ($r in $results) {
        if ($r.Present) {
            '{0,-10} {1,-52} {2}' -f $r.Tool, $r.Path.Substring(0, [Math]::Min(52, $r.Path.Length)), $r.Version
        }
        else {
            Write-Host ('{0,-10} {1,-52} {2}' -f $r.Tool, '-', 'MISSING') -ForegroundColor Red
        }
    }

    Write-Head 'VS Code extensions'
    if ($extensions.Count -eq 0) {
        Write-Warn2 'no Typst/LaTeX extension detected (or `code` CLI unavailable)'
    }
    else {
        foreach ($e in $extensions) { "  $e" }
    }

    Write-Head 'Fonts'
    "  CJK fonts ............ $cjkCount"
    "  Noto Serif CJK SC .... $serifCjk"
    "  Noto Sans CJK SC ..... $sansCjk"
    "  TeX Gyre faces ....... $gyre"

    Write-Head 'Typst packages'
    "  data dir (@local) .... $pkgRoot"
    "  cache dir (@preview) . $cacheRoot"
    "  cached @preview ...... $previewCount"
    "  installed @local ..... $localCount"

    Write-Head 'Library'
    "  root ................. $LibRoot"

    if ($missing.Count -gt 0) {
        ''
        Write-Warn2 "not installed: $($missing -join ', ')"
        if ($missing -contains 'typst') { Write-Info 'install Typst:  winget install --id Typst.Typst  (or https://github.com/typst/typst/releases)' }
        if ($missing -contains 'xelatex') { Write-Info 'install LaTeX:  winget install --id MiKTeX.MiKTeX  (or https://yihui.org/tinytex/)' }
    }
    else {
        ''
        Write-Ok 'every checked tool is present'
    }
}
exit 0
