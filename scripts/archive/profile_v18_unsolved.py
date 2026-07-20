#!/usr/bin/env python3
"""Profile v18 unsolved tasks and probe local solver families."""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "kaggle" / "neurogolf-2026-simple-logic-solver-export-v9"
NOTEBOOK = KERNEL_DIR / "neurogolf-2026-simple-logic-solver-export-v9.ipynb"
MANIFEST = (
    ROOT
    / "artifacts/submission/kaggle-runs/2026-06-10-v21-score-opt-partial-bg"
    / "simple_logic_manifest.csv"
)
TASK_DIR = Path(os.environ.get("NEUROGOLF_TASK_DIR", "/tmp/neurogolf-data/extracted"))
OUT_CSV = ROOT / "artifacts/analysis/v21_unsolved_profile.csv"
OUT_MD = ROOT / "artifacts/analysis/v21_unsolved_profile.md"

LOCAL_SOLVERS = [
    "constant",
    "identity",
    "background_to_single_color",
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
    "partial_background_fill_conv",
]


def load_notebook_namespace() -> dict:
    """Execute the v9 kernel's solver-definition cells and return its namespace.

    Skips the manifest-building cells (stops at the first cell defining
    `manifest_rows`) so only solver functions and helpers get exec'd.
    """
    nb = json.loads(NOTEBOOK.read_text())
    chunks: list[str] = []
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            text = "".join(src)
        else:
            text = src
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
    ns: dict = {"__name__": "solver_probe"}
    code = "\n\n".join(chunks)
    future_line = "from __future__ import annotations\n"
    if future_line.strip() in code:
        code = future_line + code.replace(future_line, "")
    exec(compile(code, str(NOTEBOOK), "exec"), ns, ns)
    return ns


def exported_manifest(path: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """Split a manifest CSV into (exported, unsolved) rows keyed by task id."""
    rows = list(csv.DictReader(path.open()))
    exported, unsolved = {}, {}
    for row in rows:
        ok = str(row.get("onnx_exported", "")).lower() in {"1", "true", "yes"} or bool(
            row.get("model_path")
        )
        (exported if ok else unsolved)[row["task_id"]] = row
    return exported, unsolved


def block_bucket(reason: str) -> str:
    """Group a manifest `reason_rejected` code into a coarse blocker bucket."""
    if "export_not_in_v9_allowlist" in reason:
        return "allowlist_blocked"
    if "runtime_risk" in reason:
        return "runtime_risk"
    if "input_shape" in reason:
        return "bad_external_shape"
    return "other"


def probe_local_solvers(ns: dict, task_id: str, task: dict) -> list[str]:
    """Try every local solver family against a task and return the ones that fit."""
    pairs = ns["task_pairs"](task)
    if not pairs:
        return []

    solver_map = {
        "constant": lambda: ns["try_constant_solver"](pairs),
        "identity": lambda: ns["try_identity_solver"](pairs),
        "background_to_single_color": lambda: ns["try_background_to_single_color_solver"](pairs),
        "single_object_shift": lambda: ns["try_object_shift_solver"](pairs),
        "largest_object_crop": lambda: ns["try_largest_object_crop_solver"](pairs),
        "ranked_component_crop": lambda: ns["try_ranked_component_crop_solver"](pairs),
        "global_color_map": lambda: ns["try_color_map_solver"](pairs),
        "spatial_gather": lambda: ns["try_spatial_gather_solver"](pairs),
        "geometric_color_map": lambda: ns["try_geometric_color_map_solver"](pairs),
        "fixed_crop": lambda: ns["try_fixed_crop_solver"](pairs),
        "dynamic_bbox_crop": lambda: ns["try_dynamic_bbox_crop_solver"](pairs),
        "dynamic_anchor_crop": lambda: ns["try_dynamic_anchor_crop_solver"](pairs),
        "nearest_integer_scale": lambda: ns["try_nearest_integer_scale_solver"](pairs),
        "periodic_tile": lambda: ns["try_periodic_tile_solver"](pairs),
        "partial_background_fill_conv": lambda: ns["try_partial_background_fill_conv_solver"](pairs),
    }

    hits: list[str] = []
    normalize = ns.get("_normalize_solver_result")
    validates = ns.get("model_solves_pairs")
    for name, fn in solver_map.items():
        try:
            result = fn()
        except Exception:
            continue
        if normalize is not None:
            model, specific_name, _reason = normalize(name, result)
        elif isinstance(result, tuple):
            model = result[0]
            specific_name = result[1] if len(result) > 1 else name
        else:
            model, specific_name = result, name
        if model is None:
            continue
        if validates is not None and not validates(model, pairs):
            continue
        hits.append(specific_name or name)
    return hits


PRIORITY_ACTION = {
    "export simple same-shape solver": 95,
    "export simple shape-changing solver": 90,
    "deep dive crop/extract/compress": 75,
    "deep dive object movement/selection": 70,
    "deep dive pattern/counting/global logic": 55,
    "deep dive expand/tile/construct": 50,
}

SOLVER_HINTS = [
    ("background_to_single_color", "background_to_single_color"),
    ("global_color_map", "global_color_map"),
    ("flip_horizontal", "flip_horizontal"),
    ("flip_vertical", "flip_vertical"),
    ("rotate_90", "rotate_90"),
    ("rotate_180", "rotate_180"),
    ("rotate_270", "rotate_270"),
    ("transpose", "transpose"),
    ("crop_non_background", "crop_non_background"),
    ("nearest_integer_scale", "nearest_integer_scale"),
    ("periodic_tile_from_input", "periodic_tile_from_input"),
]


def truthy(value: str) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


def eda_solver_hints(c: dict, same: dict, shape: dict, ed: dict) -> list[str]:
    """Derive candidate solver-family hints from precomputed EDA/candidate rows."""
    hints: list[str] = []
    for label, col in SOLVER_HINTS:
        for src in (c, same, shape):
            if src and truthy(src.get(col, "")):
                hints.append(label)
                break
    if truthy(c.get("object_movement_candidate", "")):
        hints.append("single_object_shift/largest_object_crop")
    if truthy(c.get("fixed_template_candidate", "")):
        hints.append("fixed_crop")
    if truthy(c.get("count_summary_candidate", "")):
        hints.append("constant/global logic")
    crop = c.get("crop_subtype", "")
    if crop and crop != "crop_unknown":
        hints.append(f"crop:{crop}")
    if ed and "same-shape" in ed.get("eda_bucket", "") and not truthy(c.get("any_same_shape_solver", "")):
        hints.append("learned_conv/geometric")
    if ed and ed.get("eda_bucket") == "shape-changing" and truthy(shape.get("any_shape_solver", "")):
        hints.append("shape_solver_bundle")
    return hints


def eda_feasibility(row: dict) -> int:
    """Score a row's near-term solvability to rank the recommended waves."""
    score = 0
    if row["block_bucket"] == "allowlist_blocked":
        score += 25
    elif row["block_bucket"] == "bad_external_shape":
        score += 15
    elif row["block_bucket"] == "runtime_risk":
        score += 10
    score += PRIORITY_ACTION.get(row["next_action"], 40)
    if row["v26_solved"] == "True" and row["v26_solver_kind"] != "external_transform_library":
        score += 30
    if truthy(row.get("any_same_shape_solver", "")):
        score += 25
    if truthy(row.get("any_shape_solver", "")):
        score += 20
    if truthy(row.get("object_movement_candidate", "")):
        score += 15
    score += min(int(row.get("hint_count", 0)), 3) * 5
    if row.get("local_solver_hits"):
        score += 40
    return score


def eda_tier(row: dict) -> str:
    """Assign a row to a recommended-wave priority tier."""
    if row.get("local_solver_hits"):
        return "A_probe_pass"
    if row["next_action"].startswith("export simple") and int(row.get("hint_count", 0)) >= 1:
        return "B_eda_simple"
    if row["block_bucket"] == "allowlist_blocked":
        return "C_allowlist_repair"
    if row["block_bucket"] == "runtime_risk":
        return "D_runtime_rewrite"
    if row["next_action"] in {"deep dive crop/extract/compress", "deep dive object movement/selection"}:
        return "C_shape_logic"
    return "D_research"


def main() -> int:
    if not TASK_DIR.exists():
        print(f"Missing task dir: {TASK_DIR}", file=sys.stderr)
        return 1

    _, unsolved = exported_manifest(MANIFEST)
    cand = {r["task_id"]: r for r in csv.DictReader((ROOT / "artifacts/analysis/neurogolf_solver_candidate_table.csv").open())}
    eda = {r["task_id"]: r for r in csv.DictReader((ROOT / "artifacts/eda/tables/neurogolf_eda_task_summary.csv").open())}
    same = {r["task_id"]: r for r in csv.DictReader((ROOT / "artifacts/analysis/neurogolf_same_shape_solver_fits.csv").open())}
    shape = {r["task_id"]: r for r in csv.DictReader((ROOT / "artifacts/analysis/neurogolf_shape_solver_fits.csv").open())}
    v26_exp, _ = exported_manifest(ROOT / "artifacts/submission/kaggle-runs/2026-06-09-1340-v26/simple_logic_manifest.csv")

    probe_enabled = False
    ns: dict = {}
    tasks: dict = {}
    if TASK_DIR.exists():
        try:
            ns = load_notebook_namespace()
            tasks = ns["load_tasks"](TASK_DIR)
            probe_enabled = bool(ns.get("ORT_AVAILABLE")) and bool(ns.get("model_solves_pairs"))
        except Exception as exc:
            print(f"warning: solver probe disabled ({exc})", file=sys.stderr)

    rows: list[dict] = []
    for task_id in sorted(unsolved):
        manifest_row = unsolved[task_id]
        reason = manifest_row.get("reason_rejected", "")
        c = cand.get(task_id, {})
        ed = eda.get(task_id, {})
        s = same.get(task_id, {})
        sh = shape.get(task_id, {})
        hints = eda_solver_hints(c, s, sh, ed)
        hits: list[str] = []
        if probe_enabled and task_id in tasks:
            hits = probe_local_solvers(ns, task_id, tasks[task_id])
        row = {
            "task_id": task_id,
            "block_bucket": block_bucket(reason),
            "reason_rejected": reason,
            "next_action": c.get("next_action", ""),
            "eda_bucket": ed.get("eda_bucket", ""),
            "shape_changes_in_train": c.get("shape_changes_in_train", ed.get("shape_changes_in_train", "")),
            "any_same_shape_solver": c.get("any_same_shape_solver", ""),
            "any_shape_solver": c.get("any_shape_solver", ""),
            "object_movement_candidate": c.get("object_movement_candidate", ""),
            "eda_solver_hints": "|".join(hints),
            "hint_count": len(hints),
            "local_solver_hits": "|".join(hits),
            "hit_count": len(hits),
            "best_local_solver": hits[0] if hits else (hints[0] if hints else ""),
            "v26_solved": str(task_id in v26_exp),
            "v26_solver_kind": v26_exp.get(task_id, {}).get("solver_kind", ""),
            "probe_enabled": str(probe_enabled),
        }
        row["priority_tier"] = eda_tier(row)
        row["feasibility_score"] = eda_feasibility(row)
        rows.append(row)

    tier_order = {
        "A_probe_pass": 0,
        "B_eda_simple": 1,
        "C_allowlist_repair": 2,
        "C_shape_logic": 3,
        "D_runtime_rewrite": 4,
        "D_research": 5,
    }
    rows.sort(key=lambda r: (tier_order[r["priority_tier"]], -r["feasibility_score"], r["task_id"]))

    fields = list(rows[0].keys())
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# v18 Unsolved Task Profile (37 tasks)\n\n",
        "Baseline: v18 scored **3315.43** with **363/400** exported.\n\n",
        "This report combines EDA/candidate-table hints"
        + (" with live local-solver probes." if probe_enabled else " (live probes skipped: ORT unavailable locally).")
        + "\n\n",
        "## Blocker summary\n\n",
    ]
    for key, count in Counter(r["block_bucket"] for r in rows).most_common():
        lines.append(f"- **{key}**: {count}\n")
    lines.append("\n## Priority tiers\n\n")
    for key in [
        "A_probe_pass",
        "B_eda_simple",
        "C_allowlist_repair",
        "C_shape_logic",
        "D_runtime_rewrite",
        "D_research",
    ]:
        lines.append(f"- **{key}**: {Counter(r['priority_tier'] for r in rows).get(key, 0)}\n")

    lines.append("\n## Ranked tasks\n\n")
    lines.append("| rank | task | tier | score | blocker | EDA hints | probe hits | next_action | v26 |\n")
    lines.append("|---:|---|---|---:|---|---|---|---|---|\n")
    for i, row in enumerate(rows, 1):
        v26 = row["v26_solver_kind"] if row["v26_solved"] == "True" else "—"
        hints = row["eda_solver_hints"] or "—"
        hits = row["local_solver_hits"] or "—"
        lines.append(
            f"| {i} | {row['task_id']} | {row['priority_tier']} | {row['feasibility_score']} | "
            f"{row['block_bucket']} | {hints} | {hits} | {row['next_action']} | {v26} |\n"
        )

    lines.append("\n## Recommended waves\n\n")
    wave_specs = [
        ("Wave 1 — EDA says simple same-shape solver", "B_eda_simple"),
        ("Wave 2 — allowlist ONNX repair or local replacement", "C_allowlist_repair"),
        ("Wave 3 — crop/extract/object movement logic", "C_shape_logic"),
        ("Wave 4 — runtime rewrite (115/118)", "D_runtime_rewrite"),
        ("Wave 5 — research backlog", "D_research"),
    ]
    if probe_enabled:
        wave_specs.insert(0, ("Wave 0 — probe-confirmed local solver", "A_probe_pass"))

    for title, tier in wave_specs:
        lines.append(f"### {title}\n\n")
        tier_rows = [r for r in rows if r["priority_tier"] == tier]
        if not tier_rows:
            lines.append("- none\n\n")
            continue
        for row in tier_rows:
            detail = row["local_solver_hits"] or row["eda_solver_hints"] or row["next_action"]
            lines.append(f"- `{row['task_id']}` ({row['block_bucket']}): {detail}\n")
        lines.append("\n")

    lines.append("## Notes\n\n")
    lines.append("- On v18, every unsolved task failed because the external library candidate was rejected; no export fallback was attempted.\n")
    lines.append("- Fixing export-aware candidate selection is likely the fastest path from 363 → 370+ before building brand-new solvers.\n")

    OUT_MD.write_text("".join(lines))

    ready = [r for r in rows if r["priority_tier"] == "A_probe_pass"]
    simple = [r for r in rows if r["priority_tier"] == "B_eda_simple"]
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    print(f"probe_enabled={probe_enabled} probe_pass={len(ready)} eda_simple={len(simple)}")
    if simple:
        print("top eda simple:", ", ".join(r["task_id"] for r in simple))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
