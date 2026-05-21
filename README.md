# NeuroGolf 2026

Kaggle notebooks for the NeuroGolf 2026 competition, focused first on a professional EDA workflow for ARC-style task data.

## 1. Notebook Index

- `notebooks/01_eda.ipynb`: Kaggle-ready EDA for ARC-style task JSON files. It discovers input JSON files, normalizes task payloads, summarizes task coverage, visualizes train/test pair distributions, inspects grid geometry, reviews color-token usage, renders ARC examples, creates first-pass solver buckets, and exports lightweight summary CSVs.
- `notebooks/02_baseline_models.ipynb`: Kaggle-ready baseline notebook that builds constant-output ONNX files for single-test-case tasks with provided test outputs. This is a submission-format sanity baseline, not a general ARC solver.
- `notebooks/03_solver_diagnostics.ipynb`: Kaggle-ready diagnostic notebook that measures simple solver compatibility, shape-change patterns, color/palette behavior, connected components, and recommended solver tracks before deeper modeling.

## 2. Kaggle Usage

Upload or copy the notebook into Kaggle, attach the NeuroGolf 2026 competition/public data, and run top-to-bottom. The notebook discovers JSON files under `/kaggle/input` and writes summary CSVs to `/kaggle/working`.

## 3. EDA Key Points

- The Kaggle run discovered 800 JSON files and loaded 400 normalized tasks, with full expected-style coverage from `task001` through `task400`.
- The dataset is mostly low-shot: median training examples per task is 3, with a range from 2 to 10.
- Most tasks have one test case, but some have multiple test cases, so submission code must not assume a single invocation forever.
- Shape-changing tasks are substantial: 138 / 400 tasks show train-time input/output shape changes, while 262 / 400 are same-shape in the training examples.
- Input grids can reach 30x30, so larger-grid tasks should be used as ONNX cost and memory stress tests.
- Color token `0` dominates both train inputs and outputs, which makes background handling a central baseline concern.
- The provisional EDA buckets are: 138 shape-changing, 108 larger same-shape, 85 small same-shape, and 69 low-color same-shape tasks.

## 4. Deep-Dive EDA Backlog

- Separate strong expansion/compression tasks from same-area tasks; these likely need different solver families.
- Compare input/output color-set deltas to identify introduced-color, removed-color, and same-palette tasks.
- Isolate multiple-test-case tasks early because they need input-conditioned models or exact transformation logic.
- Add object-level diagnostics next: connected components by color, bounding boxes, symmetry, repetition, and grid-line detection.
- Add train-pair consistency checks for simple solver hypotheses such as identity, color map, crop, tile, scale, transpose, mirror, and mask-fill.
- Use `03_solver_diagnostics.ipynb` to turn these checks into measurable coverage tables before implementing each solver family.

## 5. Baseline Direction

The first baseline is an ONNX packaging baseline. It writes the Kaggle-facing artifact to `/kaggle/working/submission.zip`, validates generated models with `onnxruntime` when available, and keeps a manifest of generated task models. Single-test tasks use constant-output models; structurally compatible multi-test tasks use an input-equality selector model. The baseline notebook includes the official starter-notebook dependency pins for Kaggle: `numpy==2.4.4`, `onnx==1.21.0`, `onnxruntime==1.24.4`, and `onnx-tool==1.0.1`. It should be followed by solver baselines that infer outputs from input grids rather than relying on public test outputs.

## 6. Project Rules

Notebook style and visualization conventions are documented in `docs/coding-rules.md`.
