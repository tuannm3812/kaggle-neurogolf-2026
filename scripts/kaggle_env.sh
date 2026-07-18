#!/usr/bin/env bash
# Resolve Kaggle CLI credentials and kernel slug for tuannm3812 / tuannm3823.
# Source from run_kaggle_export.sh and monitor_kaggle_run.sh:
#   KAGGLE_ACCOUNT=3823 source scripts/kaggle_env.sh

set -euo pipefail

KAGGLE_ACCOUNT="${KAGGLE_ACCOUNT:-3812}"
KAGGLE_CREDENTIALS_BASE="${KAGGLE_CREDENTIALS_BASE:-$HOME/Downloads}"
KAGGLE_KERNEL_BASENAME="${KAGGLE_KERNEL_BASENAME:-neurogolf-2026-simple-logic-solver-export-v9}"

_kaggle_env_cleanup() {
  if [[ -n "${KAGGLE_CONFIG_TMP:-}" && -d "$KAGGLE_CONFIG_TMP" ]]; then
    rm -rf "$KAGGLE_CONFIG_TMP"
    unset KAGGLE_CONFIG_TMP
  fi
  if [[ -n "${KAGGLE_METADATA_BACKUP:-}" && -f "$KAGGLE_METADATA_BACKUP" ]]; then
    cp "$KAGGLE_METADATA_BACKUP" "$KERNEL_DIR/kernel-metadata.json"
    rm -f "$KAGGLE_METADATA_BACKUP"
    unset KAGGLE_METADATA_BACKUP
  fi
}

trap _kaggle_env_cleanup EXIT

_kaggle_account_key="$(printf '%s' "$KAGGLE_ACCOUNT" | tr '[:upper:]' '[:lower:]')"
case "$_kaggle_account_key" in
  3812|tuannm3812)
    KAGGLE_USER="tuannm3812"
    export KAGGLE_CONFIG_DIR="${KAGGLE_CONFIG_DIR:-$KAGGLE_CREDENTIALS_BASE}"
    if [[ -f "$KAGGLE_CONFIG_DIR/kaggle.json" ]]; then
      :
    elif [[ -f "$KAGGLE_CREDENTIALS_BASE/kaggle_tuannm3812.json" ]]; then
      KAGGLE_CONFIG_TMP="$(mktemp -d "${TMPDIR:-/tmp}/neurogolf_kaggle_cfg_XXXXXX")"
      cp "$KAGGLE_CREDENTIALS_BASE/kaggle_tuannm3812.json" "$KAGGLE_CONFIG_TMP/kaggle.json"
      chmod 600 "$KAGGLE_CONFIG_TMP/kaggle.json"
      export KAGGLE_CONFIG_DIR="$KAGGLE_CONFIG_TMP"
    elif [[ -f "$KAGGLE_CONFIG_DIR/kaggle_tuannm3812.json" ]]; then
      KAGGLE_CONFIG_TMP="$(mktemp -d "${TMPDIR:-/tmp}/neurogolf_kaggle_cfg_XXXXXX")"
      cp "$KAGGLE_CONFIG_DIR/kaggle_tuannm3812.json" "$KAGGLE_CONFIG_TMP/kaggle.json"
      chmod 600 "$KAGGLE_CONFIG_TMP/kaggle.json"
      export KAGGLE_CONFIG_DIR="$KAGGLE_CONFIG_TMP"
    elif [[ ! -f "$KAGGLE_CONFIG_DIR/kaggle.json" ]]; then
      echo "Missing kaggle.json or kaggle_tuannm3812.json for account $KAGGLE_USER under $KAGGLE_CREDENTIALS_BASE" >&2
      exit 1
    fi
    ;;
  3823|tuannm3823)
    KAGGLE_USER="tuannm3823"
    KAGGLE_CONFIG_TMP="$(mktemp -d "${TMPDIR:-/tmp}/neurogolf_kaggle_cfg_XXXXXX")"
    if [[ ! -f "$KAGGLE_CREDENTIALS_BASE/kaggle_tuannm3823.json" ]]; then
      echo "Missing $KAGGLE_CREDENTIALS_BASE/kaggle_tuannm3823.json" >&2
      exit 1
    fi
    cp "$KAGGLE_CREDENTIALS_BASE/kaggle_tuannm3823.json" "$KAGGLE_CONFIG_TMP/kaggle.json"
    chmod 600 "$KAGGLE_CONFIG_TMP/kaggle.json"
    export KAGGLE_CONFIG_DIR="$KAGGLE_CONFIG_TMP"
    ;;
  *)
    echo "Unknown KAGGLE_ACCOUNT='$KAGGLE_ACCOUNT' (use 3812 or 3823)" >&2
    exit 1
    ;;
esac

export KAGGLE_USER
KERNEL_SLUG="${KERNEL_SLUG:-$KAGGLE_USER/$KAGGLE_KERNEL_BASENAME}"
export KERNEL_SLUG

kaggle_prepare_kernel_metadata() {
  local meta="$KERNEL_DIR/kernel-metadata.json"
  local want_id="$KERNEL_SLUG"
  local current_id
  current_id="$(python3 - <<PY
import json
print(json.load(open("$meta"))["id"])
PY
)"
  if [[ "$current_id" == "$want_id" ]]; then
    return 0
  fi
  KAGGLE_METADATA_BACKUP="$(mktemp)"
  cp "$meta" "$KAGGLE_METADATA_BACKUP"
  python3 - <<PY
import json
from pathlib import Path
path = Path("$meta")
data = json.loads(path.read_text())
data["id"] = "$want_id"
path.write_text(json.dumps(data, indent=2) + "\n")
PY
  echo "==> Patched kernel-metadata id: $current_id -> $want_id"
}

kaggle_restore_kernel_metadata() {
  if [[ -n "${KAGGLE_METADATA_BACKUP:-}" && -f "$KAGGLE_METADATA_BACKUP" ]]; then
    cp "$KAGGLE_METADATA_BACKUP" "$KERNEL_DIR/kernel-metadata.json"
    rm -f "$KAGGLE_METADATA_BACKUP"
    unset KAGGLE_METADATA_BACKUP
  fi
}
