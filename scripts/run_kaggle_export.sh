#!/usr/bin/env bash
# Push, run, and pull the NeuroGolf export kernel via Kaggle CLI.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KAGGLE_BIN="${KAGGLE_BIN:-$(command -v kaggle || true)}"
if [[ -z "${KAGGLE_BIN}" && -x "/Users/tuanm.nguyen/Library/Python/3.9/bin/kaggle" ]]; then
  KAGGLE_BIN="/Users/tuanm.nguyen/Library/Python/3.9/bin/kaggle"
fi
KAGGLE_CONFIG_DIR="${KAGGLE_CONFIG_DIR:-$HOME/Downloads}"
KAGGLE_ACCOUNT="${KAGGLE_ACCOUNT:-3812}"
KERNEL_DIR="${KERNEL_DIR:-$ROOT/kaggle/neurogolf-2026-simple-logic-solver-export-v9}"
SUBMIT_MESSAGE="${SUBMIT_MESSAGE:-NeuroGolf notebook export run}"
SUBMIT_OUTPUT_FILE="${SUBMIT_OUTPUT_FILE:-submission.zip}"
SKIP_COMPETITION_SUBMIT="${SKIP_COMPETITION_SUBMIT:-0}"
RUN_ID="${RUN_ID:-$(date +%Y-%m-%d-%H%M)}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/artifacts/submission/kaggle-runs/$RUN_ID}"
POLL_SECONDS="${POLL_SECONDS:-30}"
MAX_WAIT_MINUTES="${MAX_WAIT_MINUTES:-90}"

if [[ ! -x "$KAGGLE_BIN" ]]; then
  echo "kaggle CLI not found. Install with: pip install kaggle" >&2
  exit 1
fi
if [[ ! -f "$KERNEL_DIR/kernel-metadata.json" ]]; then
  echo "Missing kernel bundle at $KERNEL_DIR" >&2
  exit 1
fi

# shellcheck source=scripts/kaggle_env.sh
source "$ROOT/scripts/kaggle_env.sh"
KERNEL_DIR="$KERNEL_DIR" kaggle_prepare_kernel_metadata

echo "==> Kaggle account: $KAGGLE_USER (slug: $KERNEL_SLUG)"
export KAGGLE_CONFIG_DIR

echo "==> Pushing kernel: $KERNEL_SLUG"
push_output="$("$KAGGLE_BIN" kernels push -p "$KERNEL_DIR" 2>&1)"
echo "$push_output"
kernel_version="$(echo "$push_output" | sed -n 's/.*Kernel version \([0-9][0-9]*\) successfully pushed.*/\1/p' | tail -1)"
if [[ -z "$kernel_version" ]]; then
  echo "warning: could not parse kernel version from push output" >&2
fi

echo "==> Waiting for kernel completion (poll every ${POLL_SECONDS}s)"
deadline=$((SECONDS + MAX_WAIT_MINUTES * 60))
while true; do
  kstatus="$("$KAGGLE_BIN" kernels status "$KERNEL_SLUG" 2>&1 | awk -F'"' '{print $2}' | tail -1)"
  echo "    status: $kstatus"
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
"$KAGGLE_BIN" kernels output "$KERNEL_SLUG" -p "$OUTPUT_DIR" -o

if [[ -f "$OUTPUT_DIR/simple_logic_manifest.csv" ]]; then
  echo "==> Manifest summary"
  python3 - <<PY
import csv
from collections import Counter
from pathlib import Path

path = Path("$OUTPUT_DIR/simple_logic_manifest.csv")
rows = list(csv.DictReader(path.open()))
if not rows:
    print("manifest empty")
    raise SystemExit(0)

def exported(row):
    val = str(row.get("onnx_exported", "")).lower()
    if val in {"1", "true", "yes"}:
        return True
    if val in {"0", "false", "no", ""}:
        return bool(row.get("model_path"))
    return bool(val)

exp = [r for r in rows if exported(r)]
uns = [r for r in rows if not exported(r)]
print(f"exported: {len(exp)} / {len(rows)}")
print(f"unsolved: {len(uns)}")
if exp and "solver_family" in exp[0]:
    fam = Counter(r.get("solver_family", "?") for r in exp)
    print("families:", dict(fam))
if uns:
    reasons = Counter((r.get("reason_rejected") or "unknown").split(":")[0] for r in uns)
    print("rejections:", dict(reasons))
PY
fi

if [[ "$SKIP_COMPETITION_SUBMIT" != "1" ]]; then
  echo "==> Submitting notebook output to competition"
  submit_cmd=(
    "$KAGGLE_BIN" competitions submit -c neurogolf-2026
    -k "$KERNEL_SLUG"
    -f "$SUBMIT_OUTPUT_FILE"
    -m "$SUBMIT_MESSAGE"
  )
  if [[ -n "$kernel_version" ]]; then
    submit_cmd+=(-v "$kernel_version")
  fi
  "${submit_cmd[@]}"
else
  echo "==> Skipping competition submit (SKIP_COMPETITION_SUBMIT=1)"
fi

echo "==> Latest competition submissions"
"$KAGGLE_BIN" competitions submissions -c neurogolf-2026 | head -5

echo "Done. Output: $OUTPUT_DIR"
kaggle_restore_kernel_metadata
