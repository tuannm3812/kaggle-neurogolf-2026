# Wait for kernel v24, download output, submit, print status.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:KAGGLE_CONFIG_DIR = Join-Path $Root ".kaggle"
$KernelSlug = "tuannm3812/neurogolf-2026-simple-logic-solver-export-v9"
$KernelVersion = "24"
$RunId = "2026-06-13-v28"
$OutputDir = Join-Path $Root "artifacts/submission/kaggle-runs/$RunId"
$PollSeconds = 45
$MaxWaitMinutes = 120
$SubmitMessage = "v28: original-library-first + full export audit (GPU)"

$deadline = (Get-Date).AddMinutes($MaxWaitMinutes)
while ($true) {
    $statusRaw = python -m kaggle kernels status $KernelSlug 2>&1 | Out-String
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
python -m kaggle kernels output $KernelSlug -p $OutputDir -o 2>&1 | Out-Null

$manifest = Join-Path $OutputDir "simple_logic_manifest.csv"
if (Test-Path $manifest) {
    python -c "import csv; from collections import Counter; from pathlib import Path; rows=list(csv.DictReader(Path(r'$manifest').open())); exp=[r for r in rows if str(r.get('onnx_exported','')).lower() in {'1','true','yes'} or r.get('model_path')]; uns=[r for r in rows if r not in exp]; print(f'exported: {len(exp)} / {len(rows)}'); print(f'unsolved: {len(uns)}'); print('rejections:', dict(Counter((r.get('reason_rejected') or 'unknown').split(':')[0] for r in uns)) if uns else {})"
}

Write-Host "Submitting notebook output (version $KernelVersion)"
python -m kaggle competitions submit -c neurogolf-2026 -k $KernelSlug -f submission.zip -v $KernelVersion -m $SubmitMessage
Write-Host "Latest submissions:"
python -m kaggle competitions submissions -c neurogolf-2026 2>&1 | Select-Object -First 6
