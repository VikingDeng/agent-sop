# ---------------------------------------------------------------------------
#  build_all_examples.ps1 — compile every example and every vendored template,
#  then write BUILD_REPORT.md.
#
#  Usage:
#    .\build_all_examples.ps1
#    .\build_all_examples.ps1 -Quick
#    .\build_all_examples.ps1 -ReportsOnly
#    .\build_all_examples.ps1 -NoReport
#    .\build_all_examples.ps1 -ReportsOnly -NoReport
#
#  The report targets are read from templates.tsv (every row whose path is
#  reports/*), NOT from a hard-coded list - a newly registered report is picked
#  up automatically.
#
#  Exit code: 0 only if every target's compiler returned 0 AND the PDF exists.
#  A stale or partial PDF is a FAILURE, never a success.
#
#  Windows counterpart of build_all_examples.sh.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [switch]$Quick,
    [switch]$NoReport,
    [switch]$ReportsOnly
)

. "$PSScriptRoot/lib.ps1"

if (-not (Test-Have 'typst')) {
    Write-Bad 'typst is not on PATH'
    Write-Info 'install: winget install --id Typst.Typst   (or https://github.com/typst/typst/releases)'
    exit 1
}

$outDir = Join-Path $LibRoot 'build'
$logDir = Join-Path $outDir 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$results = New-Object System.Collections.Generic.List[object]

function Invoke-Compile {
    param([string]$Label, [string]$Source, [string]$OutPdf, [string]$WorkDir)

    $safe = ($Label -replace '[ /]', '_')
    $log = Join-Path $logDir "$safe.log"
    if (Test-Path $OutPdf) { Remove-Item $OutPdf -Force }

    # Success requires BOTH: the compiler exited 0 AND the output PDF exists.
    $rc = 1
    Push-Location $WorkDir
    try {
        & typst compile $Source $OutPdf *> $log
        $rc = $LASTEXITCODE
    }
    catch {
        $rc = 1
        $_ | Out-String | Add-Content -LiteralPath $log
    }
    finally { Pop-Location }

    # Get-Content -Raw returns $null for an EMPTY file, so the else-branch does
    # not cover that case; force a string before it reaches [regex]::Matches.
    $logText = ''
    if (Test-Path $log) {
        $raw = Get-Content -LiteralPath $log -Raw
        if ($null -ne $raw) { $logText = $raw }
    }

    if ($rc -eq 0 -and (Test-Path $OutPdf)) {
        $bytes = (Get-Item $OutPdf).Length
        $warns = ([regex]::Matches($logText, '(?m)^warning')).Count
        Write-Host ('  {0,-34} ' -f $Label) -NoNewline
        Write-Host 'ok  ' -ForegroundColor Green -NoNewline
        Write-Host ("{0,8} bytes  warnings={1}" -f $bytes, $warns)
        $results.Add([pscustomobject]@{ Label = $Label; Status = 'OK'; Bytes = $bytes; Warnings = $warns; Log = $log })
        return $true
    }
    else {
        if ($rc -ne 0) {
            $err = ($logText -split "`n" | Where-Object { $_ -match '^error' } | Select-Object -First 1)
            if (-not $err) { $err = 'unknown error' }
            $err = "typst exit=${rc}: $($err.Trim())"
        }
        else {
            $err = 'typst exit=0 but no PDF was written'
        }
        Write-Host ('  {0,-34} ' -f $Label) -NoNewline
        Write-Host 'FAIL' -ForegroundColor Red -NoNewline
        Write-Host ("  {0}" -f $err)
        $results.Add([pscustomobject]@{ Label = $Label; Status = 'FAIL'; Bytes = 0; Warnings = 0; Log = $log })
        return $false
    }
}

$nOk = 0; $nFail = 0

if (-not $ReportsOnly) {
    Write-Head '1/3  Example project - one body, many templates'
    $ex = Join-Path $LibRoot 'examples/radar-paper'
    foreach ($f in 'main-generic', 'main-report', 'main-neurips', 'main-icml', 'main-iclr', 'main-cvpr', 'main-ieee', 'main-acl') {
        $src = Join-Path $ex "$f.typ"
        if (-not (Test-Path $src)) { continue }
        if (Invoke-Compile -Label "examples/radar-paper/$f" -Source "$f.typ" -OutPdf (Join-Path $outDir "examples-$f.pdf") -WorkDir $ex) { $nOk++ } else { $nFail++ }
    }
    Write-Head '2/3  Report templates - targets read from templates.tsv'
}
else {
    Write-Head 'Reports only - targets read from templates.tsv'
}

# One data source: every manifest row whose path is under reports/.
$reportRows = @(Get-ManifestRows) | Where-Object { $_.Path -like 'reports/*' }
foreach ($row in $reportRows) {
    $d = Join-Path $LibRoot $row.Path
    if (-not (Test-Path (Join-Path $d 'example.typ'))) {
        Write-Warn2 "reports/$($row.Id): $($row.Path)/example.typ not found - skipped"
        continue
    }
    if (Invoke-Compile -Label "reports/$($row.Id)/example" -Source 'example.typ' -OutPdf (Join-Path $outDir "report-$($row.Id).pdf") -WorkDir $d) { $nOk++ } else { $nFail++ }
}

if (-not $ReportsOnly) {
    if (-not $Quick) {
        Write-Head '3/3  Vendored library templates (their own demo documents)'
        $targets = @(
            @('typst/neurips', 'typst/neurips', 'main.typ'),
            @('typst/icml', 'typst/icml', 'main.typ'),
            @('typst/iclr', 'typst/iclr', 'main.typ'),
            @('typst/cvpr', 'typst/cvpr', 'main.typ'),
            @('typst/acl', 'typst/acl', 'main.typ'),
            @('typst/ieee/charged-ieee', 'typst/ieee/charged-ieee', 'main.typ'),
            @('typst/ieee/ieeeconf', 'typst/ieee/bamdone-ieeeconf', 'main.typ'),
            @('typst/ieee/vgtc', 'typst/ieee/ieee-vgtc', 'journal.typ'),
            @('typst/radar/isprs', 'typst/radar/isprs', 'main.typ'),
            @('typst/generic/jmlr', 'typst/generic/jmlr', 'main.typ'),
            @('typst/generic/tmlr', 'typst/generic/tmlr', 'main.typ')
        )
        foreach ($t in $targets) {
            $label = $t[0]; $dir = Join-Path $LibRoot $t[1]; $entry = $t[2]
            if (-not (Test-Path (Join-Path $dir $entry))) { Write-Warn2 "$label - $entry not found"; continue }
            $safe = ($label -replace '[ /]', '-')
            if (Invoke-Compile -Label $label -Source $entry -OutPdf (Join-Path $outDir "lib-$safe.pdf") -WorkDir $dir) { $nOk++ } else { $nFail++ }
        }
    }
    else {
        Write-Head '3/3  Vendored library templates - SKIPPED (-Quick)'
    }
}

''
if ($nFail -eq 0) { Write-Ok "$nOk compiled, 0 failed" } else { Write-Bad "$nOk compiled, $nFail FAILED" }

if (-not $NoReport) {
    $rep = Join-Path $LibRoot 'BUILD_REPORT.md'
    $typstVer = (& typst --version 2>&1 | Select-Object -First 1)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('# Build Report')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Generated by ``scripts/build_all_examples.ps1`` on $(Get-Date -Format 'yyyy-MM-dd HH:mm') local.")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Typst: ``$typstVer``")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('## Summary')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('| Target | Result | Bytes | Warnings |')
    [void]$sb.AppendLine('|---|---|---|---|')
    foreach ($r in $results) {
        $mark = if ($r.Status -eq 'OK') { 'OK' } else { '**FAIL**' }
        [void]$sb.AppendLine("| ``$($r.Label)`` | $mark | $($r.Bytes) | $($r.Warnings) |")
    }
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("**$nOk compiled, $nFail failed.**")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('## Per-target detail')
    [void]$sb.AppendLine()
    foreach ($r in $results) {
        [void]$sb.AppendLine("### ``$($r.Label)`` - $($r.Status)")
        [void]$sb.AppendLine()
        [void]$sb.AppendLine('```')
        if (Test-Path $r.Log) {
            # @() : Get-Content returns a bare string for a 1-line file.
            $lines = @(Get-Content -LiteralPath $r.Log)
            if ($lines.Count -eq 0) { [void]$sb.AppendLine('(no output - clean compile, zero warnings)') }
            else {
                $head = $lines | Select-Object -First 40
                foreach ($l in $head) { [void]$sb.AppendLine($l) }
                if ($lines.Count -gt 40) { [void]$sb.AppendLine("... ($($lines.Count - 40) more lines)") }
            }
        }
        [void]$sb.AppendLine('```')
        [void]$sb.AppendLine()
    }
    [void]$sb.AppendLine('## Reproduce')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('```powershell')
    [void]$sb.AppendLine('.\scripts\build_all_examples.ps1')
    [void]$sb.AppendLine('```')
    Set-Content -LiteralPath $rep -Value $sb.ToString() -Encoding UTF8
    ''
    Write-Ok 'wrote BUILD_REPORT.md'
}

if ($nFail -eq 0) { exit 0 } else { exit 1 }
