[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GameBinaries,

    [string]$Destination
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if (-not $Destination) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Destination = Join-Path $repoRoot "lab\dumps\ue4ss\$stamp"
}

$source = (Resolve-Path $GameBinaries).Path
$Destination = [System.IO.Path]::GetFullPath($Destination)
New-Item -ItemType Directory -Force -Path $Destination | Out-Null

# New experimental layout keeps UE4SS files in <Win64>\ue4ss.
# Old stable layout keeps them directly in <Win64>.
$roots = @($source)
$nestedRoot = Join-Path $source "ue4ss"
if (Test-Path $nestedRoot) {
    $roots += $nestedRoot
}

$files = @(
    "UE4SS_ObjectDump.txt",
    "UE4SS.log",
    "UE4SS-settings.ini",
    "Mods\mods.txt"
)
$directories = @(
    "CXXHeaderDump",
    "UE4SS_SDK",
    "Mappings"
)

$copied = @()
$resolvedRoot = $null

foreach ($name in $files) {
    foreach ($root in $roots) {
        $path = Join-Path $root $name
        if (-not (Test-Path $path)) {
            continue
        }
        $parent = Split-Path $name
        if ($parent) {
            New-Item -ItemType Directory -Force -Path (
                Join-Path $Destination $parent
            ) | Out-Null
        }
        Copy-Item $path -Destination (Join-Path $Destination $name) -Force
        $copied += $name
        if (-not $resolvedRoot) {
            $resolvedRoot = $root
        }
        break
    }
}

foreach ($name in $directories) {
    foreach ($root in $roots) {
        $path = Join-Path $root $name
        if (-not (Test-Path $path)) {
            continue
        }
        Copy-Item $path -Destination $Destination -Recurse -Force
        $copied += "$name/"
        if (-not $resolvedRoot) {
            $resolvedRoot = $root
        }
        break
    }
}

$manifest = @{
    collected_at   = (Get-Date).ToString("o")
    game_binaries  = $source
    ue4ss_root     = $resolvedRoot
    items          = $copied
}
$manifest | ConvertTo-Json -Depth 4 |
    Set-Content -Path (Join-Path $Destination "manifest.json") -Encoding utf8

Write-Host "Collected $($copied.Count) item(s) into $Destination"
foreach ($item in $copied) {
    Write-Host "  $item"
}

if ($copied.Count -eq 0) {
    Write-Warning "Nothing was collected. Check -GameBinaries and whether UE4SS wrote its dumps there."
}
