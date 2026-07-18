#!/usr/bin/env python3
"""Utilities for notebook output hygiene."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Optional


def _load_notebook(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_notebook(path: Path, notebook: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=1)
        f.write("\n")


def _code_cell_sources(notebook: dict) -> List[str]:
    sources: List[str] = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        sources.append(source)
    return sources


def _head_notebook_source(path: Path) -> Optional[List[str]]:
    try:
        raw = subprocess.check_output(
            ["git", "show", f"HEAD:{path.as_posix()}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None
    return _code_cell_sources(json.loads(raw))


def _clear_outputs(notebook: dict) -> bool:
    changed = False
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        cell["execution_count"] = None
    return changed


def _is_code_changed(path: Path) -> bool:
    try:
        head_sources = _head_notebook_source(path)
    except Exception:
        return True
    if head_sources is None:
        # New notebook not in HEAD: treat as changed code.
        return True
    return _code_cell_sources(_load_notebook(path)) != head_sources


def _default_notebooks() -> List[Path]:
    return sorted(Path("notebooks").glob("*.ipynb"))


def _arg_notebooks(raw: List[str]) -> List[Path]:
    notebooks = []
    for item in raw:
        notebook_path = Path(item)
        if "*" in item or "?" in item or "[" in item:
            notebooks.extend(sorted(Path(".").glob(item)))
        else:
            notebooks.append(notebook_path)
    return sorted(set(notebooks))


def _run(notebooks: List[Path], changed_only: bool) -> None:
    for path in notebooks:
        if not path.exists():
            print(f"skip: missing {path}")
            continue
        notebook = _load_notebook(path)
        if changed_only and not _is_code_changed(path):
            print(f"keep outputs: {path} (code unchanged)")
            continue
        if _clear_outputs(notebook):
            _write_notebook(path, notebook)
            print(f"cleared outputs: {path}")
        else:
            print(f"no code outputs: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Clear Jupyter outputs on notebooks where logic changed, "
            "or all notebooks when --all is set."
        )
    )
    parser.add_argument(
        "notebooks",
        nargs="*",
        help="Notebook paths or globs (default: notebooks/*.ipynb)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clear outputs for all selected notebooks.",
    )
    args = parser.parse_args()

    notebooks = _arg_notebooks(args.notebooks) if args.notebooks else _default_notebooks()
    if not notebooks:
        print("no notebooks found")
        return 1

    _run(notebooks, changed_only=not args.all)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
