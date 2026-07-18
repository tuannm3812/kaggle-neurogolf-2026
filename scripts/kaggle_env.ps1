# Resolve Kaggle credentials and kernel slug for Windows PowerShell.
param(
    [string]$Account = "3812",
    [string]$KernelBasename = "neurogolf-2026-simple-logic-solver-export-v9"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RepoKaggleDir = Join-Path $Root ".kaggle"
$ParentDir = Split-Path -Parent $Root

function Resolve-KaggleConfigDir {
    if ($env:KAGGLE_CONFIG_DIR -and (Test-Path (Join-Path $env:KAGGLE_CONFIG_DIR "kaggle.json"))) {
        return $env:KAGGLE_CONFIG_DIR
    }
    if (Test-Path (Join-Path $RepoKaggleDir "kaggle.json")) {
        return $RepoKaggleDir
    }
    foreach ($dir in @($ParentDir, $Root, (Join-Path $env:USERPROFILE "Downloads"))) {
        foreach ($name in @("kaggle_tuannm3812.json", "kaggle.json")) {
            $candidate = Join-Path $dir $name
            if (Test-Path $candidate) {
                if ($name -eq "kaggle.json") {
                    return $dir
                }
                $tmp = Join-Path $env:TEMP ("neurogolf_kaggle_cfg_" + [guid]::NewGuid().ToString("N"))
                New-Item -ItemType Directory -Force -Path $tmp | Out-Null
                Copy-Item -Force $candidate (Join-Path $tmp "kaggle.json")
                return $tmp
            }
        }
    }
    throw "Kaggle credentials not found. Run scripts/setup_kaggle_credentials.ps1 first."
}

function Resolve-KaggleCmd {
    $kaggle = Get-Command kaggle -ErrorAction SilentlyContinue
    if ($kaggle) {
        return @($kaggle.Source)
    }
    return @("python", "-m", "kaggle")
}

switch ($Account.ToLower()) {
    { $_ -in @("3812", "tuannm3812") } {
        $script:KAGGLE_USER = "tuannm3812"
    }
    { $_ -in @("3823", "tuannm3823") } {
        $script:KAGGLE_USER = "tuannm3823"
    }
    default {
        throw "Unknown account '$Account'. Use 3812 or 3823."
    }
}

$script:KAGGLE_CONFIG_DIR = Resolve-KaggleConfigDir
$env:KAGGLE_CONFIG_DIR = $script:KAGGLE_CONFIG_DIR
$script:KERNEL_SLUG = "$KAGGLE_USER/$KernelBasename"
$script:KAGGLE_CMD = Resolve-KaggleCmd

Write-Host "Kaggle user: $KAGGLE_USER"
Write-Host "Config dir:  $KAGGLE_CONFIG_DIR"
Write-Host "Kernel slug: $KERNEL_SLUG"
Write-Host "Kaggle cmd:  $($KAGGLE_CMD -join ' ')"
