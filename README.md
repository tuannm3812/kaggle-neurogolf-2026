# NeuroGolf 2026

Kaggle notebooks for the NeuroGolf 2026 competition, focused first on a professional EDA workflow for ARC-style task data.

## 1. Notebook Index

- `notebooks/01_eda.ipynb`: Kaggle-ready EDA for ARC-style task JSON files. It discovers input JSON files, normalizes task payloads, summarizes task coverage, visualizes train/test pair distributions, inspects grid geometry, reviews color-token usage, renders ARC examples, creates first-pass solver buckets, and exports lightweight summary CSVs.

## 2. Kaggle Usage

Upload or copy the notebook into Kaggle, attach the NeuroGolf 2026 competition/public data, and run top-to-bottom. The notebook discovers JSON files under `/kaggle/input` and writes summary CSVs to `/kaggle/working`.

## 3. EDA Key Points

- Confirm data attachment first: the notebook reports discovered JSON files and loaded normalized tasks before any analysis.
- Check expected task coverage against `task001` through `task400` before building per-task ONNX artifacts.
- Treat same-shape and shape-changing tasks as separate solver-planning tracks.
- Use color-token frequency and unique-color distributions to identify likely recoloring, masking, background, and object-based transformations.
- Review diverse visual samples, not only the first task ids, before committing to solver families.

## 4. Project Rules

Notebook style and visualization conventions are documented in `docs/coding-rules.md`.
