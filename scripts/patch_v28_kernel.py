#!/usr/bin/env python3
"""Patch v9 export kernel notebook for v28 stability fixes."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "kaggle/neurogolf-2026-simple-logic-solver-export-v9/neurogolf-2026-simple-logic-solver-export-v9.ipynb"
ALLOWLIST_PY = ROOT / "kaggle/neurogolf-2026-simple-logic-solver-export-v9/v9_allowlist.py"


def patch_source(src: str) -> tuple[str, list[str]]:
    notes: list[str] = []

    old_roots = """TRANSFORM_LIBRARY_ROOT_CANDIDATES = (
    \"/tmp/neurogolf_blended\",
    \"/private/tmp/neurogolf_blended\",
    \"/kaggle/input/datasets/konbu17/neurogolf-2026-blended-401-v117\",
    \"/kaggle/input/neurogolf-2026-blended-401-v117\",
    \"/kaggle/input/datasets/karnakbaevarthur/neurogolf-2026-task-transformation-library\",
    \"/kaggle/input/neurogolf-2026-task-transformation-library\","""
    new_roots = """TRANSFORM_LIBRARY_ROOT_CANDIDATES = (
    \"/kaggle/input/datasets/karnakbaevarthur/neurogolf-2026-task-transformation-library\",
    \"/kaggle/input/neurogolf-2026-task-transformation-library\",
    \"/tmp/neurogolf_blended\",
    \"/private/tmp/neurogolf_blended\",
    \"/kaggle/input/datasets/konbu17/neurogolf-2026-blended-401-v117\",
    \"/kaggle/input/neurogolf-2026-blended-401-v117\","""
    if old_roots in src:
        src = src.replace(old_roots, new_roots)
        notes.append("library_roots: original-first (revert v27 blended-first)")

    if "'task100', 'task101', 'task102'" in src:
        src = src.replace("'task100', 'task101', 'task102'", "'task100', 'task102'")
        notes.append("allowlist: removed task101 from fallback")

    old_filter = """def passes_v9_export_filter(
    payload: bytes, *, task_id: str, solver_kind: str | None
) -> tuple[bool, str]:
    \"\"\"Apply the v9 export policy before writing submission artifacts.\"\"\"
    if not ONNX_AVAILABLE:
        return False, \"onnx_unavailable\"
    try:
        model = onnx.ModelProto()
        model.ParseFromString(payload)
        in_shape = [
            dim.dim_value
            for dim in model.graph.input[0].type.tensor_type.shape.dim
        ]
        if in_shape != [1, 10, 30, 30]:
            return False, f\"export_shape:{in_shape}\"
    except Exception as exc:
        return False, f\"export_load:{type(exc).__name__}\"

    if solver_kind == \"external_transform_library\":
        allowlist = load_v9_export_allowlist()
        if not allowlist:
            return False, \"export_allowlist_missing\"
        if task_id not in allowlist:
            return False, \"export_not_in_v9_allowlist\"

    export_ort_kinds = LIBRARY_EXPORT_KINDS | {\"unique_color_order\"}
    export_ort_tasks = frozenset({\"task101\", \"task115\", \"task118\"})
    if (
        VALIDATE_WITH_ONNXRUNTIME
        and ORT_AVAILABLE
        and (
            solver_kind in export_ort_kinds
            or task_id in export_ort_tasks
        )
    ):
        try:
            ort.InferenceSession(payload, providers=[\"CPUExecutionProvider\"])
        except Exception as exc:
            message = str(exc)
            if \"NOT_IMPLEMENTED\" in message:
                return False, \"export_ort_not_implemented\"
            return False, f\"export_ort_init:{type(exc).__name__}\"

    return True, \"\""""
    new_filter = """def passes_v9_export_filter(
    payload: bytes, *, task_id: str, solver_kind: str | None
) -> tuple[bool, str]:
    \"\"\"Apply the v9 export policy before writing submission artifacts.\"\"\"
    if not ONNX_AVAILABLE:
        return False, \"onnx_unavailable\"
    try:
        model = onnx.ModelProto()
        model.ParseFromString(payload)
        model = normalize_external_model_shapes(model)
    except Exception as exc:
        return False, f\"export_load:{type(exc).__name__}\"

    skip_runtime = solver_kind == \"runtime_risk_library_onnx\"
    scorer_ok, scorer_reason = is_scorer_compatible(
        model,
        serialized_bytes=payload,
        skip_runtime_risk=skip_runtime,
    )
    if not scorer_ok:
        return False, scorer_reason

    if solver_kind == \"external_transform_library\":
        allowlist = load_v9_export_allowlist()
        if not allowlist:
            return False, \"export_allowlist_missing\"
        if task_id not in allowlist:
            return False, \"export_not_in_v9_allowlist\"

    return True, \"\""""
    if old_filter in src:
        src = src.replace(old_filter, new_filter)
        notes.append("export_filter: full scorer compatibility gate")

    audit_fn = """

def audit_manifest_exports(manifest_df) -> tuple[Any, list[tuple[str, str]]]:
    \"\"\"Re-validate exported rows and drop scorer-incompatible artifacts.\"\"\"
    if manifest_df.empty or \"onnx_exported\" not in manifest_df.columns:
        return manifest_df, []
    rejected: list[tuple[str, str]] = []
    rows = manifest_df.to_dict(orient=\"records\")
    for row in rows:
        if not row.get(\"onnx_exported\") or not row.get(\"model_path\"):
            continue
        path = Path(row[\"model_path\"])
        if not path.exists():
            row[\"onnx_exported\"] = False
            row[\"train_fit\"] = False
            row[\"reason_rejected\"] = \"export_missing_file\"
            rejected.append((row[\"task_id\"], \"export_missing_file\"))
            continue
        payload = path.read_bytes()
        try:
            model = onnx.ModelProto()
            model.ParseFromString(payload)
            model = normalize_external_model_shapes(model)
        except Exception as exc:
            row[\"onnx_exported\"] = False
            row[\"train_fit\"] = False
            row[\"reason_rejected\"] = f\"export_audit_load:{type(exc).__name__}\"
            rejected.append((row[\"task_id\"], row[\"reason_rejected\"]))
            continue
        skip_runtime = row.get(\"solver_kind\") == \"runtime_risk_library_onnx\"
        ok, reason = is_scorer_compatible(
            model,
            serialized_bytes=payload,
            skip_runtime_risk=skip_runtime,
        )
        if not ok:
            row[\"onnx_exported\"] = False
            row[\"train_fit\"] = False
            row[\"reason_rejected\"] = reason
            rejected.append((row[\"task_id\"], reason))
            continue
        export_ok, export_reason = passes_v9_export_filter(
            payload,
            task_id=row[\"task_id\"],
            solver_kind=row.get(\"solver_kind\"),
        )
        if not export_ok:
            row[\"onnx_exported\"] = False
            row[\"train_fit\"] = False
            row[\"reason_rejected\"] = export_reason
            rejected.append((row[\"task_id\"], export_reason))
    return pd.DataFrame(rows), rejected
"""
    if "def audit_manifest_exports" not in src and "manifest_df = pd.DataFrame(manifest_rows)" in src:
        src = src.replace(
            "manifest_df = pd.DataFrame(manifest_rows)",
            audit_fn + "\nmanifest_df = pd.DataFrame(manifest_rows)",
        )
        src = src.replace(
            "else:\n    solved_count = 0\n    display(manifest_df)\n\nwith zipfile.ZipFile(",
            "else:\n    solved_count = 0\n    display(manifest_df)\n\nmanifest_df, audit_rejected = audit_manifest_exports(manifest_df)\nif audit_rejected:\n    print(f\"Final audit rejected {len(audit_rejected)} exports (sample: {audit_rejected[:5]})\")\nsolved_count = int(manifest_df[\"onnx_exported\"].sum()) if not manifest_df.empty else 0\n\nwith zipfile.ZipFile(",
        )
        notes.append("export_audit: final manifest re-validation before zip")

    if "LEARNED_CONV_EXPENSIVE_LIBRARY = os.environ.get(" in src and "'false'" in src.split("LEARNED_CONV_EXPENSIVE_LIBRARY")[1][:120]:
        src = src.replace(
            "LEARNED_CONV_EXPENSIVE_LIBRARY = os.environ.get(\n    'LEARNED_CONV_EXPENSIVE_LIBRARY', 'false'\n).lower() not in {'0', 'false', 'no'}",
            "LEARNED_CONV_EXPENSIVE_LIBRARY = os.environ.get(\n    'LEARNED_CONV_EXPENSIVE_LIBRARY', 'true' if IN_KAGGLE else 'false'\n).lower() not in {'0', 'false', 'no'}",
        )
        notes.append("learned_conv: enabled on Kaggle (GPU kernel)")

    return src, notes


def sync_allowlist_py(text: str) -> str:
    if "'task100', 'task101', 'task102'" in text:
        text = text.replace("'task100', 'task101', 'task102'", "'task100', 'task102'")
    return text


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    all_notes: list[str] = []
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        patched, notes = patch_source(src)
        if notes:
            all_notes.extend(notes)
            cell["source"] = patched.splitlines(keepends=True)
    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    if ALLOWLIST_PY.exists():
        ALLOWLIST_PY.write_text(sync_allowlist_py(ALLOWLIST_PY.read_text(encoding="utf-8")), encoding="utf-8")
    print("Patched notebook:")
    for note in all_notes:
        print(f"  - {note}")


if __name__ == "__main__":
    main()
