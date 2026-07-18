# Wait for a Kaggle kernel run, download output, optionally submit, print status.
param(
    [string]$KernelSlug = "tuannm3812/neurogolf-2026-simple-logic-solver-export-v9",
    [string]$KernelVersion = "",
    [string]$RunId = (Get-Date -Format "yyyy-MM-dd-HHmm"),
    [string]$SubmitMessage = "",
    [switch]$SkipSubmit,
    [int]$PollSeconds = 45,
    [int]$MaxWaitMinutes = 360
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:KAGGLE_CONFIG_DIR = Join-Path $Root ".kaggle"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$OutputDir = Join-Path $Root "artifacts/submission/kaggle-runs/$RunId"
$PythonExe = (Get-Command python -ErrorAction Stop).Source

function Invoke-Kaggle {
    param([string[]]$KaggleArgs)
    $attempts = 0
    while ($attempts -lt 3) {
        $attempts++
        try {
            Set-Location $Root
            $tmpOut = Join-Path $env:TEMP ("kaggle-cli-$PID-$($attempts)-stdout.log")
            $tmpErr = Join-Path $env:TEMP ("kaggle-cli-$PID-$($attempts)-stderr.log")
            $env:PYTHONIOENCODING = "utf-8"
            $proc = Start-Process -FilePath $PythonExe -ArgumentList (@("-m", "kaggle") + $KaggleArgs) -WorkingDirectory $Root -Wait -PassThru -NoNewWindow -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr
            $output = @()
            if (Test-Path $tmpOut) { $output += Get-Content -Path $tmpOut -Raw -Encoding utf8 }
            if (Test-Path $tmpErr) { $output += Get-Content -Path $tmpErr -Raw -Encoding utf8 }
            $output = ($output -join "").Trim()
            Remove-Item -Path $tmpOut,$tmpErr -Force -ErrorAction SilentlyContinue
            if ($proc.ExitCode -ne 0 -and -not $output) {
                throw "kaggle exited with code $($proc.ExitCode)"
            }
            if ($proc.ExitCode -ne 0 -and $output -match "Output file downloaded") {
                Write-Warning "kaggle exited $($proc.ExitCode) after download (encoding noise); continuing"
            }
            return $output
        } catch {
            Write-Host "Kaggle call failed (attempt $attempts/3): $_"
            if ($attempts -ge 3) { throw }
            Start-Sleep -Seconds 10
        }
    }
}

$deadline = (Get-Date).AddMinutes($MaxWaitMinutes)
while ($true) {
    $statusRaw = Invoke-Kaggle -KaggleArgs @("kernels", "status", $KernelSlug)
    $status = [regex]::Match($statusRaw, '"(KernelWorkerStatus\.[^"]+)"').Groups[1].Value
    if (-not $status) { $status = ($statusRaw.Trim() -split "`n" | Select-Object -Last 1) }
    Write-Host "$(Get-Date -Format 'HH:mm:ss') status: $status"
    if ($status -like "*COMPLETE*") { break }
    if ($status -like "*ERROR*" -or $status -like "*FAILED*") { throw "Kernel failed: $status" }
    if ((Get-Date) -gt $deadline) { throw "Timed out after $MaxWaitMinutes minutes" }
    Start-Sleep -Seconds $PollSeconds
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Write-Host "Downloading output to $OutputDir"
if ($KernelVersion) {
    $outputSlug = "$KernelSlug/$KernelVersion"
} else {
    $outputSlug = $KernelSlug
}
Invoke-Kaggle -KaggleArgs @("kernels", "output", $outputSlug, "-p", $OutputDir, "-o") | Out-Null

$manifest = Join-Path $OutputDir "simple_logic_manifest.csv"
if (Test-Path $manifest) {
    python -c "import csv; from collections import Counter; from pathlib import Path; rows=list(csv.DictReader(Path(r'$manifest').open())); exp=[r for r in rows if str(r.get('onnx_exported','')).lower() in {'1','true','yes'} or r.get('model_path')]; uns=[r for r in rows if r not in exp]; print(f'exported: {len(exp)} / {len(rows)}'); print(f'unsolved: {len(uns)}'); print('rejections:', dict(Counter((r.get('reason_rejected') or 'unknown').split(':')[0] for r in uns)) if uns else {})"
}

if (-not $SkipSubmit -and $SubmitMessage) {
    Write-Host "Submitting notebook output"
    if ($KernelVersion) {
        Invoke-Kaggle -KaggleArgs @(
            "competitions", "submit", "-c", "neurogolf-2026",
            "-k", $KernelSlug, "-f", "submission.zip", "-m", $SubmitMessage,
            "-v", $KernelVersion
        ) | Out-Null
    } else {
        Invoke-Kaggle -KaggleArgs @(
            "competitions", "submit", "-c", "neurogolf-2026",
            "-k", $KernelSlug, "-f", "submission.zip", "-m", $SubmitMessage
        ) | Out-Null
    }
}

Write-Host "Latest submissions:"
Invoke-Kaggle -KaggleArgs @("competitions", "submissions", "-c", "neurogolf-2026") | Select-Object -First 6
