# Copy kaggle_tuannm3812.json into repo-local .kaggle/kaggle.json for CLI use.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Candidates = @(
    (Join-Path (Split-Path -Parent $Root) "kaggle_tuannm3812.json"),
    (Join-Path $Root "kaggle_tuannm3812.json"),
    (Join-Path $env:USERPROFILE "Downloads\kaggle_tuannm3812.json"),
    (Join-Path $env:USERPROFILE "Downloads\kaggle.json")
)

$Source = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Source) {
    Write-Error "Could not find kaggle_tuannm3812.json or kaggle.json. Checked:`n$($Candidates -join "`n")"
}

$TargetDir = Join-Path $Root ".kaggle"
$Target = Join-Path $TargetDir "kaggle.json"
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
Copy-Item -Force $Source $Target

$env:KAGGLE_CONFIG_DIR = $TargetDir
Write-Host "Configured Kaggle credentials:"
Write-Host "  source: $Source"
Write-Host "  active: $Target"
Write-Host ""
Write-Host "Test with:"
Write-Host "  `$env:KAGGLE_CONFIG_DIR = '$TargetDir'"
Write-Host "  python -m kaggle competitions list -s neurogolf"
