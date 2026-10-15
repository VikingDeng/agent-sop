# ---------------------------------------------------------------------------
#  list_templates.ps1 — print the template inventory from templates.tsv.
#
#  Usage:
#    .\list_templates.ps1
#    .\list_templates.ps1 -Format typst
#    .\list_templates.ps1 -State ok
#    .\list_templates.ps1 -Origin community
#    .\list_templates.ps1 -Markdown
#    .\list_templates.ps1 -Paths
#
#  Windows counterpart of list_templates.sh.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$Format,
    [string]$State,
    [string]$Origin,
    [switch]$Markdown,
    [switch]$Paths
)

. "$PSScriptRoot/lib.ps1"

$rows = @(Get-ManifestRows)
if ($Format) { $rows = $rows | Where-Object { $_.Format -eq $Format } }
if ($State) { $rows = $rows | Where-Object { $_.State -eq $State } }
if ($Origin) { $rows = $rows | Where-Object { $_.Origin -eq $Origin } }

if (-not $rows) { Write-Warn2 'no templates matched'; exit 0 }

if ($Paths) {
    foreach ($r in $rows) { '{0,-24} {1}' -f $r.Id, (Join-Path $LibRoot $r.Path) }
    exit 0
}

if ($Markdown) {
    '| ID | Format | Venue | Template | Version | Year | Origin | License | Path | State |'
    '|---|---|---|---|---|---|---|---|---|---|'
    foreach ($r in $rows) {
        '| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | `{8}` | {9} |' -f `
            $r.Id, $r.Format, $r.Venue, $r.Template, $r.Version, $r.Year, $r.Origin, $r.License, $r.Path, $r.State
    }
    exit 0
}

Write-Head "Template inventory  ($Manifest)"
'{0,-22} {1,-6} {2,-24} {3,-19} {4,-8} {5,-8} {6,-15} {7,-11} {8}' -f `
    'ID', 'FORMAT', 'VENUE', 'TEMPLATE', 'VERSION', 'YEAR', 'ORIGIN', 'LICENSE', 'STATE'
'-' * 140

foreach ($r in $rows) {
    $color = switch ($r.State) {
        'ok' { 'Green' }
        'patched' { 'Yellow' }
        'no-typst-template' { 'DarkGray' }
        'broken' { 'Red' }
        default { 'Gray' }
    }
    $venue = if ($r.Venue.Length -gt 24) { $r.Venue.Substring(0, 24) } else { $r.Venue }
    $tmpl = if ($r.Template.Length -gt 19) { $r.Template.Substring(0, 19) } else { $r.Template }
    Write-Host ('{0,-22} {1,-6} {2,-24} {3,-19} {4,-8} {5,-8} {6,-15} {7,-11} {8}' -f `
            $r.Id, $r.Format, $venue, $tmpl, $r.Version, $r.Year, $r.Origin, $r.License, $r.State) -ForegroundColor $color
}

''
Write-Info 'origin: official = venue/publisher | typst-official = Typst project | community = third-party reimplementation | own = this library'
Write-Info 'state:  ok | patched (locally fixed to compile) | no-typst-template | broken'
exit 0
