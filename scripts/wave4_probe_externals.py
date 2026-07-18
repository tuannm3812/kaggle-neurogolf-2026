#!/usr/bin/env python3
"""Probe local solvers on library-exported tasks (Wave 4 prep)."""

from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "kaggle/neurogolf-2026-simple-logic-solver-export-v9/neurogolf-2026-simple-logic-solver-export-v9.ipynb"
MANIFEST = Path(
    os.environ.get(
        "WAVE4_MANIFEST",
        ROOT
        / "artifacts/submission/kaggle-runs/2026-06-10-v23-wave2-reexport/simple_logic_manifest.csv",
    )
)
TASK_DIR = Path(os.environ.get("NEUROGOLF_TASK_DIR", "/tmp/neurogolf-data/extracted"))
OUT_CSV = ROOT / "artifacts/analysis/wave4_local_probe.csv"
MAX_TASKS = int(os.environ.get("WAVE4_MAX_TASKS", "0"))  # 0 = all priority A+B

LIBRARY_KINDS = {
    "external_transform_library",
    "transform_library_onnx",
    "runtime_risk_library_onnx",
}

LOCAL_SOLVERS = [
    "constant",
    "identity",
    "background_to_single_color",
    "partial_background_fill_conv",
    "single_object_shift",
    "largest_object_crop",
    "ranked_component_crop",
    "global_color_map",
    "spatial_gather",
    "geometric_color_map",
    "fixed_crop",
    "dynamic_bbox_crop",
    "dynamic_anchor_crop",
    "nearest_integer_scale",
    "periodic_tile",
]


def load_notebook_namespace() -> dict:
    nb = json.loads(NOTEBOOK.read_text())
    chunks: list[str] = []
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        text = "".join(src) if isinstance(src, list) else src
        if not text.strip():
            continue
        if "manifest_rows: list[dict[str, Any]]" in text:
            break
        if "tasks = load_tasks(TASK_DIR)" in text:
            text = text.replace(
                "tasks = load_tasks(TASK_DIR) if TASK_DIR.exists() else {}",
                "tasks = {}",
            )
        chunks.append(text)
    os.environ.setdefault("SKIP_LEARNED_CONV", "true")
    os.environ.setdefault("USE_TRANSFORM_LIBRARY", "false")
    code = "\n\n".join(chunks)
    future_line = "from __future__ import annotations\n"
    if future_line.strip() in code:
        code = future_line + code.replace(future_line, "")
    code = code.replace(
        "VALIDATE_WITH_ONNXRUNTIME = True",
        "VALIDATE_WITH_ONNXRUNTIME = False",
    )
    ns: dict = {"__name__": "wave4_probe"}
    exec(compile(code, str(NOTEBOOK), "exec"), ns, ns)
    ns["VALIDATE_WITH_ONNXRUNTIME"] = False
    ns["ORT_AVAILABLE"] = False
    return ns


def score_of(ns: dict, model) -> float:
    return max(1.0, 25.0 - math.log(max(1, ns["estimate_model_cost"](model))))


def main() -> int:
    if not MANIFEST.exists():
        print(f"missing manifest: {MANIFEST}")
        return 1
    if not TASK_DIR.exists():
        print(f"missing task dir: {TASK_DIR}")
        return 1

    rows = list(csv.DictReader(MANIFEST.open()))
    targets = [
        r
        for r in rows
        if (str(r.get("onnx_exported", "")).lower() in {"1", "true", "yes"} or r.get("model_path"))
        and r.get("solver_kind") in LIBRARY_KINDS
    ]
    targets.sort(key=lambda r: float(r.get("score_estimate") or 0))
    if MAX_TASKS > 0:
        targets = targets[:MAX_TASKS]

    ns = load_notebook_namespace()
    tasks = ns["load_tasks"](TASK_DIR)

    solver_fns = {
        "constant": lambda p: ns["try_constant_solver"](p),
        "identity": lambda p: ns["try_identity_solver"](p),
        "background_to_single_color": lambda p: ns["try_background_to_single_color_solver"](p),
        "partial_background_fill_conv": lambda p: ns["try_partial_background_fill_conv_solver"](p),
        "single_object_shift": lambda p: ns["try_object_shift_solver"](p),
        "largest_object_crop": lambda p: ns["try_largest_object_crop_solver"](p),
        "ranked_component_crop": lambda p: ns["try_ranked_component_crop_solver"](p),
        "global_color_map": lambda p: ns["try_color_map_solver"](p),
        "spatial_gather": lambda p: ns["try_spatial_gather_solver"](p),
        "geometric_color_map": lambda p: ns["try_geometric_color_map_solver"](p),
        "fixed_crop": lambda p: ns["try_fixed_crop_solver"](p),
        "dynamic_bbox_crop": lambda p: ns["try_dynamic_bbox_crop_solver"](p),
        "dynamic_anchor_crop": lambda p: ns["try_dynamic_anchor_crop_solver"](p),
        "nearest_integer_scale": lambda p: ns["try_nearest_integer_scale_solver"](p),
        "periodic_tile": lambda p: ns["try_periodic_tile_solver"](p),
    }

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    hits = 0
    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "task_id",
                "current_kind",
                "current_score",
                "best_local",
                "best_local_score",
                "delta_score",
            ],
        )
        writer.writeheader()

        for row in targets:
            tid = row["task_id"]
            task = tasks.get(tid)
            if not task:
                continue
            pairs = ns["task_pairs"](task)
            current = float(row.get("score_estimate") or 0)
            best_name = ""
            best_score = 0.0
            normalize = ns.get("_normalize_solver_result")
            for name, fn in solver_fns.items():
                try:
                    result = fn(pairs)
                except Exception:
                    continue
                if normalize is not None:
                    model, _, _ = normalize(name, result)
                elif isinstance(result, tuple):
                    model = result[0]
                else:
                    model = result
                if model is None:
                    continue
                ok, _ = ns["is_scorer_compatible"](model, skip_ort_init=True)
                if not ok:
                    continue
                ex_ok, _ = ns["model_passes_v9_export"](
                    model, task_id=tid, solver_kind=name
                )
                if not ex_ok:
                    continue
                if not ns["model_solves_pairs"](model, pairs):
                    continue
                sc = score_of(ns, model)
                if sc > best_score:
                    best_score = sc
                    best_name = name
            if best_name and best_score > current + 0.5:
                hits += 1
                writer.writerow(
                    {
                        "task_id": tid,
                        "current_kind": row.get("solver_kind"),
                        "current_score": current,
                        "best_local": best_name,
                        "best_local_score": round(best_score, 2),
                        "delta_score": round(best_score - current, 2),
                    }
                )
                print(
                    f"{tid}: {row.get('solver_kind')} {current:.2f} -> {best_name} {best_score:.2f} (+{best_score-current:.2f})"
                )

    print(f"wrote {OUT_CSV} ({hits} improvements found / {len(targets)} probed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
