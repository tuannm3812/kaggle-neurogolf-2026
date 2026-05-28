# NeuroGolf 2026

<img src="docs/assets/neurogolf-2026-header.png" alt="NeuroGolf 2026 competition banner" width="100%">

<p>
  <img alt="Kaggle" src="https://img.shields.io/badge/Kaggle-NeuroGolf_2026-20BEFF?style=flat-square&logo=kaggle&logoColor=white">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="ONNX" src="https://img.shields.io/badge/ONNX-submission-005CED?style=flat-square">
  <img alt="Workflow" src="https://img.shields.io/badge/workflow-notebook--first-2E7D32?style=flat-square">
</p>

NeuroGolf 2026 is an ARC-style grid-reasoning competition where each task must be solved by an ONNX model. This repository documents a notebook-first solution workflow: explore the task distribution, measure solver opportunities, build a valid ONNX packaging baseline, then move toward evaluator-compatible input-derived solvers.

## 1. Project Overview

The project explores how far interpretable, compact ONNX programs can go on low-shot ARC-style tasks. Each task provides only a few input/output examples, so the core challenge is not conventional model training; it is rule discovery, solver selection, and valid ONNX export under scoring constraints.

The current solution is deliberately staged:

1. Profile the full task set with EDA and visual diagnostics.
2. Build valid Kaggle-compatible ONNX submissions.
3. Measure which symbolic solver families fit each task.
4. Export only validated input-derived solvers.
5. Use manifest-based triage when public score does not move.

## 2. Task and Goal

The competition task is to submit a `submission.zip` containing ONNX models named by task id, such as `task001.onnx`. Each model must accept a static one-hot `float32` tensor and produce the transformed output grid for that task.

Our project goals are:

- Build a reliable notebook-first workflow that runs on Kaggle.
- Understand the `400` public tasks through EDA and solver diagnostics.
- Produce scorer-compatible ONNX submissions with transparent manifests.
- Replace public-output fallbacks with input-derived rule solvers.
- Improve score through object, crop, movement, and construction logic.

## 3. Key Metrics

| Area | Current finding |
| --- | --- |
| Task coverage | `400 / 400` normalized tasks loaded |
| Training density | Median `3` train examples per task |
| Test structure | `386` single-test tasks, `14` multi-test tasks |
| Shape behavior | `262` same-area tasks, `138` shape-changing tasks |
| Palette behavior | `176` same-palette, `224` palette-changing tasks |
| Simple solver slice | `62` same-shape candidates, `4` simple shape-changing candidates |
| First valid public score | `253.94` |
| Current plateau | Additional internal coverage has not yet moved public score |

Solver-development routing:

| Solver track | Task count | Priority |
| --- | ---: | --- |
| Object movement/selection | `158` | High |
| Crop/extract/compress | `99` | High |
| Simple same-shape export | `62` | Implemented as first export track |
| Pattern/counting/global logic | `45` | Later diagnostic track |
| Expand/tile/construct | `32` | Next construction track |
| Simple shape export | `4` | Low-risk specialized track |

## 4. Progress

The project has reached a valid submission baseline and moved into solver-family development.

Completed:

- Full EDA coverage for all `400` tasks.
- Difficult-task gallery and solver-track prioritization.
- Baseline ONNX packaging workflow.
- First successful scorer-compatible submission.
- Static one-hot `float32` interface: `[1, 10, 30, 30]`.
- Input-derived solver exports for color maps, spatial gather, local convolutions, fixed crops, bounding-box crops, and anchor-relative crops.
- Manifest triage notebook for score-plateau analysis.

Current result:

- Public score: `253.94`.
- Repeated versions with fallback and additional simple solvers stayed at `253.94`.
- Learned `5x5` convolution improved internal validation from `60` to `62` tasks, but did not improve public score.
- The next score-improvement direction is object-level reasoning rather than more same-shape local filters.

## 5. Lessons Learned

- Kaggle scorer compatibility matters as much as local ONNX Runtime validation. Raw 2D `int64` grid models can run locally and still fail the scorer.
- The accepted pattern is a static one-hot `float32` interface with shape `[1, 10, 30, 30]`.
- A solved-task-only archive is safer than a complete archive filled with weak or invalid placeholders.
- Public-output fallback models can make an archive look more complete without improving effective leaderboard score.
- Train-fit is not enough. Solvers need public-test validation and manifest-level tracking to avoid false confidence.
- Simple global rules explain only a small slice of the benchmark.
- The largest remaining opportunities are object movement/selection and crop/extract/compress tasks.
- Manifest comparison is essential when score plateaus: new internal coverage may not overlap the public scored slice.

## 6. Repository Map

```text
.
├── README.md
├── docs/
│   ├── 1_instructions.md
│   ├── 2_eda_insights.md
│   ├── 3_baseline_models.md
│   ├── assets/
│   ├── coding-rules.md
│   └── figures/
└── notebooks/
    ├── 1_eda.ipynb
    ├── 2_baseline_models.ipynb
    ├── 3_solver_diagnostics.ipynb
    ├── 4_solver_development.ipynb
    ├── 5_simple_solver_export.ipynb
    └── 6_score_plateau_triage.ipynb
```

The repository is intentionally notebook-first. Kaggle notebooks are the executable source of truth; `docs/` captures interpretation, results, and project decisions.

## 7. Notebook Workflow

| Notebook | Purpose | Current role |
| --- | --- | --- |
| `1_eda.ipynb` | Dataset profiling, visual task review, difficult-task gallery | Defines the modeling problem and evidence base |
| `2_baseline_models.ipynb` | Complete ONNX packaging baseline | Validates archive structure and fallback behavior |
| `3_solver_diagnostics.ipynb` | Strict solver checks and component diagnostics | Quantifies solver-family opportunities |
| `4_solver_development.ipynb` | Candidate tables for solver routing | Produces task-level next-action artifacts |
| `5_simple_solver_export.ipynb` | Scorer-compatible ONNX export | Generates rule-derived and score-oriented task models |
| `6_score_plateau_triage.ipynb` | Score plateau diagnosis | Compares manifests, isolates new coverage, and renders review panels |

Detailed run instructions and next work live in [docs/1_instructions.md](docs/1_instructions.md).

## 8. Technical Skills

- Python notebook engineering for Kaggle execution.
- ARC-style grid analysis and symbolic rule diagnostics.
- Pandas and NumPy feature engineering for task-level metadata.
- Matplotlib visual diagnostics with ARC token palettes.
- ONNX graph construction with static tensor interfaces.
- ONNX Runtime validation and submission artifact checks.
- Rule-based solver design: color maps, constant rules, identity, spatial gather, and convolution candidates.
- Competition workflow hygiene: manifests, validation tables, lightweight docs, and reproducible notebook outputs.

## 9. Detailed Notes

- EDA evidence: `docs/2_eda_insights.md`
- Baseline and submission notes: `docs/3_baseline_models.md`
- Working plan and next steps: `docs/1_instructions.md`
- Project rules: `docs/coding-rules.md`
