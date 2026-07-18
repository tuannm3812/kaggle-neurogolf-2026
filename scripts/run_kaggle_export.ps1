# Push, run, and submit the NeuroGolf v9 export kernel from Windows PowerShell.
param(
    [string]$RunId = (Get-Date -Format "yyyy-MM-dd-HHmm"),
    [string]$SubmitMessage = "v29: original-library-first + library-only export audit (GPU)",
    [switch]$SkipSubmit
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$KernelDir = Join-Path $Root "kaggle/neurogolf-2026-simple-logic-solver-export-v9"
$OutputDir = Join-Path $Root "artifacts/submission/kaggle-runs/$RunId"
$PollSeconds = 30
$MaxWaitMinutes = 360

. (Join-Path $Root "scripts/kaggle_env.ps1") -Account 3812

Write-Host "==> Pushing kernel $KERNEL_SLUG"
$pushOutput = & $KAGGLE_CMD[0] @($KAGGLE_CMD[1..($KAGGLE_CMD.Length-1)] + @("kernels", "push", "-p", $KernelDir)) 2>&1 | Out-String
Write-Host $pushOutput
$kernelVersion = [regex]::Match($pushOutput, "Kernel version (\d+) successfully pushed").Groups[1].Value

Write-Host "==> Waiting for kernel completion"
$deadline = (Get-Date).AddMinutes($MaxWaitMinutes)
while ($true) {
    $statusRaw = & $KAGGLE_CMD[0] @($KAGGLE_CMD[1..($KAGGLE_CMD.Length-1)] + @("kernels", "status", $KERNEL_SLUG)) 2>&1 | Out-String
    $status = [regex]::Match($statusRaw, '"(KernelWorkerStatus\.[^"]+)"').Groups[1].Value
    if (-not $status) { $status = ($statusRaw -split "`n" | Select-Object -Last 3) -join " " }
    Write-Host ("    status: " + $status)
    if ($status -like "*COMPLETE*") { break }
    if ($status -like "*ERROR*" -or $status -like "*FAILED*") {
        throw "Kernel failed: $status"
    }
    if ((Get-Date) -gt $deadline) {
        throw "Timed out after $MaxWaitMinutes minutes"
    }
    Start-Sleep -Seconds $PollSeconds
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Write-Host "==> Downloading output to $OutputDir"
& $KAGGLE_CMD[0] @($KAGGLE_CMD[1..($KAGGLE_CMD.Length-1)] + @("kernels", "output", $KERNEL_SLUG, "-p", $OutputDir, "-o"))

$manifest = Join-Path $OutputDir "simple_logic_manifest.csv"
if (Test-Path $manifest) {
    python -c "import csv,os; from collections import Counter; from pathlib import Path; rows=list(csv.DictReader(Path(r'$manifest').open())); exp=[r for r in rows if str(r.get('onnx_exported','')).lower() in {'1','true','yes'} or r.get('model_path')]; uns=[r for r in rows if r not in exp]; print(f'exported: {len(exp)} / {len(rows)}'); print(f'unsolved: {len(uns)}'); print('rejections:', dict(Counter((r.get('reason_rejected') or 'unknown').split(':')[0] for r in uns)) if uns else {})"
}

if (-not $SkipSubmit) {
    Write-Host "==> Submitting notebook output"
    $submitArgs = @("competitions", "submit", "-c", "neurogolf-2026", "-k", $KERNEL_SLUG, "-f", "submission.zip", "-m", $SubmitMessage)
    if ($kernelVersion) { $submitArgs += @("-v", $kernelVersion) }
    & $KAGGLE_CMD[0] @($KAGGLE_CMD[1..($KAGGLE_CMD.Length-1)] + $submitArgs)
}

Write-Host "==> Latest submissions"
& $KAGGLE_CMD[0] @($KAGGLE_CMD[1..($KAGGLE_CMD.Length-1)] + @("competitions", "submissions", "-c", "neurogolf-2026")) | Select-Object -First 6

Write-Host "Done. Output: $OutputDir"
