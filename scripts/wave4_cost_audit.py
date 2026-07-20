#!/usr/bin/env python3
"""Rank exported tasks by score and flag cost-optimization targets (Wave 4)."""

from __future__ import annotations

import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(
    os.environ.get(
        "WAVE4_MANIFEST",
        ROOT
        / "artifacts/submission/kaggle-runs/2026-06-10-v23-wave2-reexport/simple_logic_manifest.csv",
    )
)
PUBLIC_SCORE = float(os.environ.get("WAVE4_PUBLIC_SCORE", "3590.21"))
OUT_CSV = ROOT / "artifacts/analysis/wave4_cost_audit.csv"
OUT_MD = ROOT / "artifacts/analysis/wave4_cost_audit.md"

LIBRARY_KINDS = {
    "external_transform_library",
    "transform_library_onnx",
    "runtime_risk_library_onnx",
}


def exported_rows(path: Path) -> list[dict]:
    """Return only the manifest rows that were actually exported."""
    rows = list(csv.DictReader(path.open()))
    return [
        r
        for r in rows
        if str(r.get("onnx_exported", "")).lower() in {"1", "true", "yes"}
        or r.get("model_path")
    ]


def main() -> int:
    if not MANIFEST.exists():
        print(f"missing manifest: {MANIFEST}")
        return 1

    rows = exported_rows(MANIFEST)
    est_sum = sum(float(r.get("score_estimate") or 0) for r in rows)
    ratio = PUBLIC_SCORE / est_sum if est_sum else 0.567

    ranked = sorted(
        rows,
        key=lambda r: float(r.get("score_estimate") or 0),
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "rank",
                "task_id",
                "solver_kind",
                "score_estimate",
                "public_est",
                "cost_estimate",
                "wave4_priority",
            ],
        )
        writer.writeheader()
        for i, row in enumerate(ranked, start=1):
            est = float(row.get("score_estimate") or 0)
            kind = row.get("solver_kind", "")
            if est < 10 and kind in LIBRARY_KINDS:
                priority = "A_critical"
            elif est < 12 and kind in LIBRARY_KINDS:
                priority = "B_high"
            elif kind in LIBRARY_KINDS:
                priority = "C_library"
            else:
                priority = "D_local_ok"
            writer.writerow(
                {
                    "rank": i,
                    "task_id": row["task_id"],
                    "solver_kind": kind,
                    "score_estimate": est,
                    "public_est": round(est * ratio, 2),
                    "cost_estimate": row.get("cost_estimate", ""),
                    "wave4_priority": priority,
                }
            )

    buckets = {"A_critical": 0, "B_high": 0, "C_library": 0, "D_local_ok": 0}
    for row in ranked:
        est = float(row.get("score_estimate") or 0)
        kind = row.get("solver_kind", "")
        if est < 10 and kind in LIBRARY_KINDS:
            buckets["A_critical"] += 1
        elif est < 12 and kind in LIBRARY_KINDS:
            buckets["B_high"] += 1
        elif kind in LIBRARY_KINDS:
            buckets["C_library"] += 1
        else:
            buckets["D_local_ok"] += 1

    gain_if_a_to_20 = sum(
        max(0.0, 20.0 - float(r.get("score_estimate") or 0)) * ratio
        for r in ranked
        if float(r.get("score_estimate") or 0) < 10
        and r.get("solver_kind") in LIBRARY_KINDS
    )
    gain_if_ab_to_18 = sum(
        max(0.0, 18.0 - float(r.get("score_estimate") or 0)) * ratio
        for r in ranked
        if float(r.get("score_estimate") or 0) < 12
        and r.get("solver_kind") in LIBRARY_KINDS
    )

    lines = [
        "# Wave 4 Cost Audit",
        "",
        f"Manifest: `{MANIFEST}`",
        f"Exported: **{len(rows)}** | Public score: **{PUBLIC_SCORE}** | Est sum: **{est_sum:.1f}**",
        f"Public/est ratio: **{ratio:.4f}**",
        "",
        "## Priority buckets",
        "",
        f"- **A_critical** (library, est < 10): {buckets['A_critical']}",
        f"- **B_high** (library, est < 12): {buckets['B_high']}",
        f"- **C_library** (other library): {buckets['C_library']}",
        f"- **D_local_ok** (local solvers): {buckets['D_local_ok']}",
        "",
        "## Upside estimates",
        "",
        f"- Raise all **A** tasks to est 20: **+{gain_if_a_to_20:.0f}** public (~{PUBLIC_SCORE + gain_if_a_to_20:.0f})",
        f"- Raise all **A+B** tasks to est 18: **+{gain_if_ab_to_18:.0f}** public (~{PUBLIC_SCORE + gain_if_ab_to_18:.0f})",
        "",
        "## Bottom 25 (fix first)",
        "",
        "| task | kind | est | ~public | cost |",
        "|---|---|---:|---:|---:|",
    ]
    for row in ranked[:25]:
        est = float(row.get("score_estimate") or 0)
        lines.append(
            f"| {row['task_id']} | {row.get('solver_kind','')} | {est:.2f} | {est * ratio:.2f} | {row.get('cost_estimate','')} |"
        )
    lines.extend(["", f"Full CSV: `{OUT_CSV}`", ""])

    OUT_MD.write_text("\n".join(lines))
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    print(
        f"buckets A/B/C/D = {buckets['A_critical']}/{buckets['B_high']}/{buckets['C_library']}/{buckets['D_local_ok']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
