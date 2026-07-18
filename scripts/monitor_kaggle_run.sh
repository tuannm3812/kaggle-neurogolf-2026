#!/usr/bin/env bash
# Poll a Kaggle kernel run; when complete, download output and print next-step hints.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KAGGLE="${KAGGLE_BIN:-/Users/tuanm.nguyen/Library/Python/3.9/bin/kaggle}"
KAGGLE_ACCOUNT="${KAGGLE_ACCOUNT:-3812}"
KERNEL_DIR="${KERNEL_DIR:-$ROOT/kaggle/neurogolf-2026-simple-logic-solver-export-v9}"
# shellcheck source=scripts/kaggle_env.sh
source "$ROOT/scripts/kaggle_env.sh"
RUN_ID="${RUN_ID:-2026-06-10-v24-wave3-runtime-risk}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/artifacts/submission/kaggle-runs/$RUN_ID}"
POLL_SECONDS="${POLL_SECONDS:-30}"
MAX_WAIT_MINUTES="${MAX_WAIT_MINUTES:-120}"
AUTO_AUDIT="${AUTO_AUDIT:-1}"

PYTHON="${PYTHON:-/Library/Developer/CommandLineTools/usr/bin/python3}"

echo "==> Monitoring $KERNEL_SLUG on $KAGGLE_USER (RUN_ID=$RUN_ID)"
deadline=$((SECONDS + MAX_WAIT_MINUTES * 60))
while true; do
  kstatus="$("$PYTHON" "$KAGGLE" kernels status "$KERNEL_SLUG" 2>&1 | awk -F'"' '{print $2}' | tail -1)"
  echo "$(date +%H:%M:%S) status: $kstatus"
  case "$kstatus" in
    *COMPLETE*) break ;;
    *ERROR*|*FAILED*)
      echo "Kernel failed: $kstatus" >&2
      exit 1
      ;;
  esac
  if (( SECONDS > deadline )); then
    echo "Timed out after ${MAX_WAIT_MINUTES} minutes" >&2
    exit 1
  fi
  sleep "$POLL_SECONDS"
done

mkdir -p "$OUTPUT_DIR"
echo "==> Downloading output to $OUTPUT_DIR"
"$PYTHON" "$KAGGLE" kernels output "$KERNEL_SLUG" -p "$OUTPUT_DIR" -o

if [[ -f "$OUTPUT_DIR/simple_logic_manifest.csv" ]]; then
  echo "==> Manifest summary"
  "$PYTHON" - <<PY
import csv
from collections import Counter
from pathlib import Path
p = Path("$OUTPUT_DIR/simple_logic_manifest.csv")
rows = list(csv.DictReader(p.open()))
exp = [r for r in rows if str(r.get("onnx_exported","")).lower() in {"1","true","yes"} or r.get("model_path")]
uns = [r for r in rows if r not in exp]
score = sum(float(r.get("score_estimate") or 0) for r in exp)
print(f"exported: {len(exp)}/400  est_sum: {score:.1f}  unsolved: {len(uns)}")
print("kinds:", dict(Counter(r.get("solver_kind","?") for r in exp)))
for r in uns:
    print(" unsolved", r["task_id"], (r.get("reason_rejected") or "")[:80])
PY
fi

echo "==> Latest submissions"
"$PYTHON" "$KAGGLE" competitions submissions -c neurogolf-2026 2>&1 | head -6

if [[ "$AUTO_AUDIT" == "1" && -f "$OUTPUT_DIR/simple_logic_manifest.csv" ]]; then
  echo "==> Wave 4 cost audit on new manifest"
  WAVE4_MANIFEST="$OUTPUT_DIR/simple_logic_manifest.csv" \
    "$PYTHON" "$ROOT/scripts/wave4_cost_audit.py"
fi

echo "Done. Output: $OUTPUT_DIR"
