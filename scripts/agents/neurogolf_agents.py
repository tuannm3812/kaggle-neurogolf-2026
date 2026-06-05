#!/usr/bin/env python3
"""Automated workflow helpers for NeuroGolf score loops.

The script is intentionally small and defensive: it can run without pandas and
degrades gracefully when Kaggle connectivity is unavailable.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


DEFAULT_KAGGLE_BIN = shutil.which("kaggle") or "/Users/tuanm.nguyen/Library/Python/3.9/bin/kaggle"
DEFAULT_COMPETITION = "neurogolf-2026"


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(int(value))
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class SubmissionRecord:
    file_name: str
    date: str
    description: str
    status: str
    public_score: Optional[float]
    private_score: str


def _run_command(cmd: List[str], env: Dict[str, str]) -> str:
    result = subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=True,
        env=env,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def _resolve_kaggle_config_dir(
    base_dir: Path,
    account: Optional[str] = None,
) -> tuple[Path, bool]:
    if account is None:
        return base_dir, False

    key_lookup = {
        "tuannm3812": "kaggle.json",
        "3812": "kaggle.json",
        "tuannm3823": "kaggle_tuannm3823.json",
        "3823": "kaggle_tuannm3823.json",
    }
    filename = key_lookup.get(account.lower())
    if not filename:
        raise ValueError(
            f"Unknown account '{account}'. Use 'tuannm3812'/'3812' or 'tuannm3823'/'3823'."
        )

    source = base_dir / filename
    if not source.exists():
        raise FileNotFoundError(f"Kaggle credentials not found: {source}")

    if filename == "kaggle.json":
        return base_dir, False

    # Kaggle CLI expects exactly kaggle.json.
    tmp = Path(tempfile.mkdtemp(prefix="neurogolf_kaggle_cfg_"))
    shutil.copy2(source, tmp / "kaggle.json")
    return tmp, True


def fetch_kaggle_submissions(
    competition: str,
    account: Optional[str],
    config_dir: Path,
    kaggle_bin: str = DEFAULT_KAGGLE_BIN,
    limit: int = 20,
) -> List[SubmissionRecord]:
    active_dir, cleanup_dir = _resolve_kaggle_config_dir(config_dir, account)
    env = os.environ.copy()
    env["KAGGLE_CONFIG_DIR"] = str(active_dir)
    try:
        raw = _run_command([kaggle_bin, "competitions", "submissions", "-c", competition], env=env)
    finally:
        if cleanup_dir and active_dir.exists():
            shutil.rmtree(active_dir)

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.startswith("----") and not ln.startswith("fileName")]
    if lines and lines[0].startswith("usage:"):
        raise RuntimeError(f"Kaggle CLI error: {lines[0]}")

    submissions: List[SubmissionRecord] = []
    for line in lines:
        parts = re.split(r"\s{2,}", line)
        if not parts:
            continue
        status_pos = -1
        for i, part in enumerate(parts):
            if part.startswith("SubmissionStatus."):
                status_pos = i
                break
        if status_pos < 0:
            continue
        if status_pos < 2:
            continue

        file_name = parts[0]
        date = parts[1]
        description = " ".join(parts[2:status_pos]).strip()
        status = parts[status_pos]
        public_raw = parts[status_pos + 1] if status_pos + 1 < len(parts) else ""
        private_raw = parts[status_pos + 2] if status_pos + 2 < len(parts) else ""
        submissions.append(
            SubmissionRecord(
                file_name=file_name,
                date=date,
                description=description,
                status=status,
                public_score=float(public_raw) if public_raw else None,
                private_score=private_raw.strip() or "",
            )
        )

    return submissions[:limit]


def load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def manifest_summary(manifest_path: Path) -> Dict[str, Any]:
    rows = load_csv_rows(manifest_path)
    total = len(rows)
    exported = [r for r in rows if parse_bool(r.get("onnx_exported"))]
    unsolved = [r for r in rows if not parse_bool(r.get("onnx_exported"))]
    solved = [r for r in rows if parse_bool(r.get("onnx_exported"))]

    by_source: Dict[str, int] = {}
    for row in exported:
        key = str(row.get("submission_source", "unknown") or "unknown")
        by_source[key] = by_source.get(key, 0) + 1

    by_family: Dict[str, int] = {}
    for row in exported:
        family = str(row.get("solver_family", "unknown") or "unknown")
        by_family[family] = by_family.get(family, 0) + 1

    reasons = Counter()
    for row in unsolved:
        reason = str(row.get("reason_rejected", "")).strip() or "unresolved"
        reasons[reason] += 1

    unresolved_ids = [str(r.get("task_id", "")).strip() for r in unsolved if r.get("task_id")]
    solved_ids = [str(r.get("task_id", "")).strip() for r in solved if r.get("task_id")]

    return {
        "total": total,
        "exported": len(exported),
        "unsolved": len(unsolved),
        "by_source": by_source,
        "by_family": by_family,
        "reason_counts": dict(reasons.most_common()),
        "unresolved_ids": unresolved_ids,
        "solved_ids": solved_ids,
        "rows": rows,
    }


def infer_run_label(manifest_path: Path) -> str:
    """Infer a stable run label from folder structure."""
    parts = list(manifest_path.resolve().parts)
    for i in range(len(parts) - 2, 0, -1):
        if parts[i] == "local-runs" and i + 1 < len(parts):
            return f"{parts[i]}:{parts[i + 1]}"
        if parts[i] == "kaggle-runs" and i + 1 < len(parts):
            return f"{parts[i]}:{parts[i + 1]}"
    for i in range(len(parts) - 2, 0, -1):
        if parts[i] == "submission" and i + 1 < len(parts):
            return parts[i + 1]
    return f"{manifest_path.parent.name}:{manifest_path.name}" or manifest_path.stem


def discover_manifests(paths: Sequence[str] | None = None) -> list[Path]:
    """Find simple_logic_manifest.csv files from explicit paths or default folders."""
    discovered: set[Path] = set()
    explicit = list(paths or [])
    if explicit:
        for raw in explicit:
            candidate = Path(raw)
            if not candidate.exists():
                print(f"missing path: {candidate}")
                continue
            if candidate.is_file() and candidate.name == "simple_logic_manifest.csv":
                discovered.add(candidate)
                continue
            if candidate.is_dir():
                discovered.update(candidate.rglob("simple_logic_manifest.csv"))
                continue
            print(f"ignored non-manifest path: {candidate}")
    else:
        defaults = [
            Path("artifacts/submission/local-runs"),
            Path("artifacts/submission/kaggle-runs"),
        ]
        for base in defaults:
            if base.exists():
                discovered.update(base.rglob("simple_logic_manifest.csv"))

    return sorted(discovered)


def parse_score_log(score_log_path: Path) -> Dict[str, float]:
    """Read a manual run_label->public score map from CSV."""
    if not score_log_path.exists():
        return {}
    rows = load_csv_rows(score_log_path)
    scores: Dict[str, float] = {}
    for row in rows:
        run_label = str(row.get("run_label", "")).strip()
        if not run_label:
            run_label = str(row.get("run_id", "")).strip()
        if not run_label:
            continue
        raw = str(row.get("public_score", "")).strip()
        if raw in {"", "pending", "nan"}:
            continue
        try:
            scores[run_label] = float(raw)
        except ValueError:
            continue
    return scores


def read_history(path: Path) -> list[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_history(path: Path, rows: list[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_label",
        "manifest_path",
        "manifest_mtime",
        "public_score",
        "total",
        "exported",
        "unsolved",
        "dominant_family",
        "dominant_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: r.get("manifest_mtime", "")):
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def build_track_report(
    runs: list[Path],
    score_overrides: Dict[str, float] | None = None,
) -> tuple[str, list[Dict[str, str]]]:
    rows = []
    snapshots = []

    for manifest_path in runs:
        summary = manifest_summary(manifest_path)
        by_family = summary["by_family"]
        reasons = summary["reason_counts"]
        dominant_family = max(by_family.items(), key=lambda item: item[1])[0] if by_family else "none"
        dominant_reason = max(reasons.items(), key=lambda item: item[1])[0] if reasons else "none"
        run_label = infer_run_label(manifest_path)

        snapshot: Dict[str, Any] = {
            "run_label": run_label,
            "manifest_path": str(manifest_path),
            "manifest_mtime": time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(manifest_path.stat().st_mtime),
            ),
            "mtime_epoch": manifest_path.stat().st_mtime,
            "total": summary["total"],
            "exported": summary["exported"],
            "unsolved": summary["unsolved"],
            "by_family": by_family,
            "reason_counts": reasons,
            "unresolved_ids": set(summary["unresolved_ids"]),
            "solved_ids": set(summary["solved_ids"]),
            "dominant_family": dominant_family,
            "dominant_reason": dominant_reason,
            "public_score": score_overrides.get(run_label) if score_overrides else None,
        }
        snapshots.append(snapshot)

    snapshots.sort(key=lambda row: row["mtime_epoch"])
    previous_snapshot: Optional[Dict[str, Any]] = None

    lines: list[str] = []
    lines.append("# NeuroGolf Version Track")
    lines.append("")
    if not snapshots:
        lines.append("- no manifests found to track.")
        return "\n".join(lines) + "\n", []

    lines.append("## Run ledger")
    lines.append("")
    lines.append(
        "| run | manifest time | score | exported | unsolved | Δexported | recovered | dominant family | notes |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |")

    lesson_keep: list[str] = []
    lesson_change: list[str] = []

    for snapshot in snapshots:
        if previous_snapshot is None:
            delta_exported = 0
            recovered = []
            delta_score = None
        else:
            delta_exported = snapshot["exported"] - previous_snapshot["exported"]
            recovered = sorted(previous_snapshot["unresolved_ids"] - snapshot["unresolved_ids"])
            prev_score = previous_snapshot.get("public_score")
            score_val = snapshot.get("public_score")
            delta_score = score_val - prev_score if (score_val is not None and prev_score is not None) else None

        score_text = (
            f"{snapshot['public_score']:.4f}" if snapshot["public_score"] is not None else "unknown"
        )
        notes = []
        if delta_exported > 0:
            notes.append(f"+{delta_exported} solved")
            lesson_keep.append(
                f"Keep: `{snapshot['run_label']}` improved solved coverage by {delta_exported} tasks."
            )
        elif delta_exported == 0:
            notes.append("no net coverage change")
            lesson_change.append(
                f"Change: `{snapshot['run_label']}` did not improve solved coverage; validate new solver families before widening search."
            )
        else:
            notes.append(f"{delta_exported} solved")

        if delta_score is not None and delta_score < 0:
            lesson_change.append(
                f"Change: `{snapshot['run_label']}` score dropped by {-delta_score:.4f} vs previous."
            )

        lines.append(
            "| "
            + " | ".join(
                [
                    snapshot["run_label"],
                    snapshot["manifest_mtime"],
                    score_text,
                    str(snapshot["exported"]),
                    str(snapshot["unsolved"]),
                    str(delta_exported),
                    str(len(recovered)),
                    snapshot["dominant_family"],
                    ", ".join(notes[:2]),
                ]
            )
            + " |"
        )

        rows.append(
            {
                "run_label": snapshot["run_label"],
                "manifest_path": snapshot["manifest_path"],
                "manifest_mtime": snapshot["manifest_mtime"],
                "public_score": str(snapshot["public_score"]) if snapshot["public_score"] is not None else "",
                "total": str(snapshot["total"]),
                "exported": str(snapshot["exported"]),
                "unsolved": str(snapshot["unsolved"]),
                "dominant_family": snapshot["dominant_family"],
                "dominant_reason": snapshot["dominant_reason"],
            }
        )

        previous_snapshot = snapshot

    if lesson_keep:
        lines.append("")
        lines.append("## Keep this")
        for note in lesson_keep:
            lines.append(f"- {note}")
    if lesson_change:
        lines.append("")
        lines.append("## Change this")
        for note in lesson_change:
            lines.append(f"- {note}")

    if not lesson_keep and not lesson_change:
        lines.append("")
        lines.append("## Lesson")
        lines.append("- baseline run only: add at least one new manifest to generate a lesson delta.")
    else:
        lines.append("")
        lines.append("## Recommended next step")
        lines.append("- Promote the highest-yield family from the positive delta row, then rerun only that notebook change.")
        lines.append("- If `dominant_reason` remains `external_missing`, prioritize transform-library mount and candidate discovery checks.")

    return "\n".join(lines) + "\n", rows


def run_track(
    run_inputs: Sequence[str],
    output_path: str = "",
    history_path: str = "",
    score_log: str = "",
) -> str:
    manifests = discover_manifests(run_inputs)
    score_overrides = parse_score_log(Path(score_log)) if score_log else {}
    report, history_rows = build_track_report(manifests, score_overrides)

    if history_path:
        previous = read_history(Path(history_path))
        if previous:
            by_label = {row.get("run_label", ""): row for row in previous}
            for row in history_rows:
                by_label[row["run_label"]] = row
            history_rows = list(by_label.values())
        write_history(Path(history_path), history_rows)
        print(f"wrote {history_path}")

    if output_path:
        Path(output_path).write_text(report, encoding="utf-8")
        print(f"wrote {output_path}")
    return report


def build_strategy_report(
    submission_records: List[SubmissionRecord],
    manifest_path: Optional[Path],
) -> str:
    lines: List[str] = []
    lines.append("# NeuroGolf Agent Report")
    lines.append("")
    if submission_records:
        best = submission_records[0]
        lines.append("## 1. Latest Kaggle Score")
        lines.append(f"- best listed public score: {best.public_score if best.public_score is not None else 'pending'}")
        lines.append(f"- last run description: {best.description}")
        lines.append(f"- last run date: {best.date}")
        lines.append(f"- last status: {best.status}")
        lines.append("")
        lines.append("## 2. Recent public runs")
        for record in submission_records[:5]:
            score = str(record.public_score) if record.public_score is not None else "pending"
            lines.append(
                f"- {record.date} | {record.description} | score={score} | {record.status}"
            )
        lines.append("")

    if manifest_path is not None:
        summary = manifest_summary(manifest_path)
        lines.append("## 3. Latest manifest status")
        lines.append(f"- rows: {summary['total']}")
        lines.append(f"- exported: {summary['exported']} / {summary['total']}")
        lines.append(f"- unsolved: {summary['unsolved']}")
        lines.append("")
        lines.append("### Export by solver family")
        for family, count in sorted(summary["by_family"].items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- {family}: {count}")
        lines.append("")
        lines.append("### Top rejection reasons")
        for reason, count in list(summary["reason_counts"].items())[:10]:
            lines.append(f"- {reason}: {count}")
        lines.append("")

        top_unsolved = summary["unresolved_ids"][:120]
        if top_unsolved:
            lines.append("### Recommended immediate targets")
            if top_unsolved:
                lines.append("- Most unresolved tasks are currently `external_missing`.")
                lines.append("- Next action: verify transform-library mount and path candidates.")
                lines.append(f"- Sample unresolved task ids: {', '.join(top_unsolved[:50])}")
            else:
                lines.append("- No unresolved tasks found in latest manifest.")
        lines.append("")
    else:
        lines.append("## 3. Manifest")
        lines.append("- No manifest file provided. No coverage diagnostics were generated.")

    lines.append("## 4. Recommended 2x day schedule")
    lines.append("- Night loop: run export notebook once, then pull kernel output and run manifest diff.")
    lines.append("- Morning loop: inspect top unresolved tasks and promote one solver family to validation.")
    lines.append("- Gate every candidate behind full train-pair fit + ONNX validity + manifest entry.")
    lines.append("- Use notebook 5 for final export changes; avoid touching 2/6 unless workflow changes.")
    return "\n".join(lines) + "\n"


def run_compare(
    base_manifest: Path,
    head_manifest: Path,
) -> str:
    base = manifest_summary(base_manifest)
    head = manifest_summary(head_manifest)

    base_set = set(base["unresolved_ids"])
    head_set = set(head["unresolved_ids"])

    recovered = sorted(base_set - head_set)
    still_unresolved = sorted(base_set & head_set)

    lines: List[str] = []
    lines.append("# Manifest Diff Report")
    lines.append("")
    lines.append("## Coverage change")
    lines.append(f"- unresolved (base): {len(base_set)}")
    lines.append(f"- unresolved (head): {len(head_set)}")
    lines.append(f"- tasks recovered: {len(recovered)}")
    if recovered:
        lines.append(f"- sample recovered ids: {', '.join(recovered[:40])}")
    else:
        lines.append("- sample recovered ids: none")
    lines.append("")
    lines.append("## Still unresolved (sample)")
    lines.append(", ".join(still_unresolved[:80]) if still_unresolved else "- none")
    lines.append("")
    lines.append("## Export delta (by family)")
    for family in sorted(set(base["by_family"]).union(head["by_family"])):
        b = base["by_family"].get(family, 0)
        h = head["by_family"].get(family, 0)
        if b != h:
            lines.append(f"- {family}: {b} -> {h} ({h-b:+})")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NeuroGolf improvement agents for score loops.")
    sub = parser.add_subparsers(dest="command", required=True)

    score_parser = sub.add_parser("score", help="Check Kaggle submission history")
    score_parser.add_argument("--competition", default=DEFAULT_COMPETITION)
    score_parser.add_argument("--account", default=None)
    score_parser.add_argument("--config-dir", default="/Users/tuanm.nguyen/Downloads")
    score_parser.add_argument("--limit", type=int, default=20)
    score_parser.add_argument("--output", default="")
    score_parser.add_argument("--kaggle-bin", default=DEFAULT_KAGGLE_BIN)

    report_parser = sub.add_parser("report", help="Build score + manifest run report")
    report_parser.add_argument("--competition", default=DEFAULT_COMPETITION)
    report_parser.add_argument("--account", default=None)
    report_parser.add_argument("--config-dir", default="/Users/tuanm.nguyen/Downloads")
    report_parser.add_argument("--manifest", default="")
    report_parser.add_argument("--output", default="")
    report_parser.add_argument("--limit", type=int, default=20)
    report_parser.add_argument("--kaggle-bin", default=DEFAULT_KAGGLE_BIN)

    compare_parser = sub.add_parser("compare", help="Compare two manifests")
    compare_parser.add_argument("--base", required=True)
    compare_parser.add_argument("--head", required=True)
    compare_parser.add_argument("--output", default="")

    track_parser = sub.add_parser("track", help="Track run history from one or more manifest runs")
    track_parser.add_argument(
        "runs",
        nargs="*",
        help="Manifest paths or directories. If omitted, scans artifacts/submission/local-runs and kaggle-runs.",
    )
    track_parser.add_argument("--output", default="")
    track_parser.add_argument("--history", default="")
    track_parser.add_argument("--score-log", default="")

    args = parser.parse_args()
    return args


def main() -> int:
    args = parse_args()
    command = args.command

    if command == "compare":
        output = run_compare(Path(args.base), Path(args.head))
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"wrote {args.output}")
        else:
            print(output)
        return 0

    if command == "track":
        output = run_track(
            run_inputs=getattr(args, "runs", []),
            output_path=getattr(args, "output", ""),
            history_path=getattr(args, "history", ""),
            score_log=getattr(args, "score_log", ""),
        )
        print(output)
        return 0

    submissions = []
    manifest_path = Path(args.manifest) if getattr(args, "manifest", "") else None
    try:
        submissions = fetch_kaggle_submissions(
            competition=args.competition,
            account=args.account,
            config_dir=Path(args.config_dir),
            kaggle_bin=args.kaggle_bin,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"score fetch failed: {exc}")

    if command == "score":
        if not submissions:
            print("no submission rows")
            return 1
        for submission in submissions:
            score = submission.public_score if submission.public_score is not None else "pending"
            print(f"{submission.date} | {submission.status} | {score} | {submission.description}")
        return 0

    if command == "report":
        report_text = build_strategy_report(submissions, manifest_path)
        if args.output:
            Path(args.output).write_text(report_text, encoding="utf-8")
            print(f"wrote {args.output}")
        else:
            print(report_text)
        return 0

    print("unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
