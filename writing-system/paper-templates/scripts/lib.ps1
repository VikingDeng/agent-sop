# ---------------------------------------------------------------------------
#  lib.ps1 — shared helpers for the paper-templates PowerShell scripts.
#  Dot-source it:   . "$PSScriptRoot/lib.ps1"
# ---------------------------------------------------------------------------
Set-StrictMode -Version Latest

$script:LibRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script:Manifest = Join-Path $LibRoot 'templates.tsv'

# Make user-level installs visible even when the shell profile was not loaded.
#   Windows: Typst from winget/scoop lands on PATH already; TinyTeX does not
#            usually exist, and MiKTeX installs system-wide.
#   Linux  : both are user-level by default in this library's setup.
function Add-ToolPaths {
    $candidates = @()
    if ($IsWindows) {
        $candidates += Join-Path $env:LOCALAPPDATA 'Programs\TinyTeX\bin\windows'
        $candidates += Join-Path $env:APPDATA 'TinyTeX\bin\windows'
        $candidates += Join-Path $env:USERPROFILE '.local\bin'
        $candidates += Join-Path $env:USERPROFILE '.TinyTeX\bin\windows'
    }
    else {
        $candidates += (Join-Path $HOME '.TinyTeX/bin/x86_64-linux')
        $candidates += (Join-Path $HOME '.TinyTeX/bin/universal-darwin')
        $candidates += (Join-Path $HOME '.TinyTeX/bin/aarch64-darwin')
        $candidates += (Join-Path $HOME '.local/bin')
    }
    foreach ($c in $candidates) {
        if ((Test-Path $c) -and ($env:PATH -notlike "*$c*")) {
            $env:PATH = "$c$([IO.Path]::PathSeparator)$env:PATH"
        }
    }
}
Add-ToolPaths

# Typst keeps two DIFFERENT directories:
#   data dir  <- packages YOU install by hand, e.g. @local/...  (writable truth)
#   cache dir <- packages downloaded from packages.typst.org, i.e. @preview/...
# Counting @preview out of the data dir always yields 0.
function Get-TypstCacheRoot {
    if ($IsWindows) {
        return (Join-Path $env:LOCALAPPDATA 'typst\packages')
    }
    elseif ($IsMacOS) {
        return (Join-Path $HOME 'Library/Caches/typst/packages')
    }
    else {
        $xdg = if ($env:XDG_CACHE_HOME) { $env:XDG_CACHE_HOME } else { Join-Path $HOME '.cache' }
        return (Join-Path $xdg 'typst/packages')
    }
}

function Get-TypstPackageRoot {
    if ($IsWindows) {
        return (Join-Path $env:APPDATA 'typst\packages')
    }
    elseif ($IsMacOS) {
        return (Join-Path $HOME 'Library/Application Support/typst/packages')
    }
    else {
        $xdg = if ($env:XDG_DATA_HOME) { $env:XDG_DATA_HOME } else { Join-Path $HOME '.local/share' }
        return (Join-Path $xdg 'typst/packages')
    }
}

# ---- output helpers --------------------------------------------------------
function Write-Ok    { param([string]$m) Write-Host "OK   $m"   -ForegroundColor Green }
function Write-Bad   { param([string]$m) Write-Host "FAIL $m"   -ForegroundColor Red }
function Write-Warn2 { param([string]$m) Write-Host "WARN $m"   -ForegroundColor Yellow }
function Write-Info  { param([string]$m) Write-Host "     $m"   -ForegroundColor DarkGray }
function Write-Head  { param([string]$m) Write-Host "`n$m" -ForegroundColor Cyan }

# ---- manifest access -------------------------------------------------------
function Get-ManifestRows {
    param([string]$Id)
    $rows = @()
    foreach ($line in Get-Content -LiteralPath $Manifest -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.StartsWith('#')) { continue }
        $f = $line -split "`t"
        if ($f.Count -lt 11) { continue }
        if ($Id -and $f[0] -ne $Id) { continue }
        $rows += , ([pscustomobject]@{
                Id       = $f[0]; Format = $f[1]; Venue = $f[2]; Template = $f[3]
                Version  = $f[4]; Year = $f[5]; Origin = $f[6]; License = $f[7]
                Path     = $f[8]; Source = $f[9]; State = $f[10]
            })
    }
    # NOTE: PowerShell unrolls the return value, so a 1-element result arrives
    # as a bare object and a 0-element result as $null. Callers therefore MUST
    # wrap this in @() before using .Count or [0]. Do not "fix" it here with a
    # leading comma -- that double-wraps and the caller then sees Count = 1
    # holding the whole array.
    return $rows
}

function Get-ManifestEntry {
    param([Parameter(Mandatory)][string]$Id)
    $r = @(Get-ManifestRows -Id $Id)   # @() is belt-and-braces at the call site
    if ($r.Count -eq 0) { return $null }
    return $r[0]
}

function Test-ManifestHas {
    param([Parameter(Mandatory)][string]$Id)
    return ($null -ne (Get-ManifestEntry -Id $Id))
}

function Test-Have {
    param([Parameter(Mandatory)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}
