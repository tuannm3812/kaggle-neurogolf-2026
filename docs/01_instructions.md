# NeuroGolf 2026 Instructions, Questions, Tasks, and Approach

This document defines the working plan for the NeuroGolf 2026 solution. It covers the competition objective, the questions we need to answer, the project tasks, and the solution approach we are building.

## 1. Competition Overview

NeuroGolf 2026 asks competitors to solve ARC-AGI style image-transformation tasks with small ONNX models. Each task provides a few input/output examples showing a transformation over colored integer grids. The submission must provide ONNX models that reproduce the transformation for each test input.

Competition constraints are fixed by Kaggle scoring and validated by notebook behavior:

- The task set is based on ARC-AGI public training tasks.
- A submission is a `submission.zip` archive.
- The archive may contain at most one ONNX file per task.
- Task files are named `task001.onnx`, `task002.onnx`, through `task400.onnx`.
- ONNX tensors and parameters must have statically defined shapes.
- Disallowed ONNX operations include `Loop`, `Scan`, `NonZero`, `Unique`, `Script`, and `Function`.
- Each ONNX file has a size limit of `1.44MB`.
- Scoring rewards correctness and compactness. The published cost formula is `max(1, 25 - ln(cost))`, where cost combines parameters, memory footprint, and multiply-accumulate operations.


## 2. Core Questions

The project is organized around the following questions.

### 2.1 Dataset Questions

- Do we have all `400` expected tasks?
- How many train/test examples does each task provide?
- Which tasks preserve shape and which tasks change shape?
- Which tasks introduce colors, remove colors, or keep the same palette?
- How often does color `0` behave like background?
- Which tasks are object-sparse versus object-dense?
- Which tasks are likely crop, extract, expand, tile, construct, count, or movement tasks?

### 2.2 Modeling Questions

- Which simple solvers explain all train pairs for a task?
- Which same-shape tasks can be solved by color maps, background fills, masks, flips, rotations, or transpose?
- Which shape-changing tasks can be solved by crop, scale, tile, extract, or construct logic?
- Which tasks require object-level reasoning?
- Which tasks require pattern, counting, grid-line, or global logic?
- Which solver families can be exported to compact ONNX graphs?
- How do we keep every ONNX file valid, small, and evaluator-compatible?

### 2.3 Submission Questions

- Does `submission.zip` contain all expected `taskXXX.onnx` files?
- Are all models valid ONNX?
- Are the model input/output names, dtypes, and shapes accepted by the evaluator?
- Are model files below the size limit?
- Can validation errors be isolated without blocking archive creation?
- Which model strategy was used for each task, including whether it exported successfully or was rejected?

## 3. Project Tasks

### 3.1 EDA Tasks

- Load and normalize all task JSON files.
- Produce task-level summary tables.
- Measure train/test counts and multi-test tasks.
- Analyze grid shape and area changes.
- Analyze color frequency and palette deltas.
- Render representative task samples.
- Export figures and markdown report assets.

Primary notebook:

- `notebooks/01_eda.ipynb`

Primary notes:

- `docs/02_eda_insights.md`

### 3.2 Solver Diagnostics Tasks

- Test strict simple same-shape solver hypotheses.
- Test strict shape-changing solver hypotheses.
- Compute connected-component complexity.
- Assign recommended solver tracks.
- Export diagnostic CSVs for downstream solver notebooks.

Primary notebook:

- `notebooks/03_solver_diagnostics.ipynb`

Next-step notebook:

- `notebooks/04_solver_development.ipynb`

### 3.3 Baseline Modeling Tasks

- Prepare task-scoped ONNX outputs aligned to the expected task roster.
- Validate ONNX graph construction.
- Validate runtime behavior where possible.
- Build a valid `submission.zip` (defaulting to validated solved-task-only exports).
- Maintain a manifest of model strategy by task with `solver_family`, `solver_kind`, `validation_scope`,
  `candidate_count`, `train_fit`, `onnx_exported`, and `reason_rejected`.
- Use fallback models only for compatibility experiments; keep real rule-based candidates separate in the manifest.

Primary notebook:

- `notebooks/02_baseline_models.ipynb`

Primary notes:

- `docs/03_baseline_models.md`

## 4. Current Approach

The current solution path is deliberately staged.

### 4.1 Stage 1: Understand the Benchmark

We first build a reliable EDA layer. This includes coverage checks, shape analysis, color analysis, palette deltas, task rendering, and solver-track prioritization.

Output:

- task summary CSVs;
- color-count CSVs;
- EDA figures;
- markdown figure report;
- documented insights.

### 4.2 Stage 2: Validate Submission Mechanics

We then build an ONNX packaging baseline. This does not aim to be competitive by itself. Its purpose is to prove that we can generate a structurally complete archive and diagnose evaluator compatibility.

Current baseline model families:

- single-test constant ONNX models;
- multi-test input-equality selector ONNX models;
- constant fallback ONNX models for unsupported tasks.

Output:

- `submission.zip`;
- model manifest (`simple_logic_manifest.csv`) with solver-family metadata and rejection reasons.
- validation table.

### 4.3 Stage 3: Implement Real Solver Families

Next, we move from public-output baselines to input-derived solvers. The solver should fit all train pairs before it is exported to ONNX. The first solver-development notebook now builds candidate tables for strict same-shape and shape-changing rules, then routes the remaining tasks into deeper object, compression, expansion, and pattern-analysis tracks.

Initial solver family order:

1. Background-to-single-color solver.
2. Global color-map solver.
3. Object extraction and object selection solvers.
4. Crop, extract, and compression solvers.
5. Expand, tile, and construction solvers.
6. Pattern, counting, grid-line, and global-logic solvers.

### 4.4 Stage 4: Export Reliable Solvers to ONNX

Only solver families with clear train-fit behavior should be exported. Each exported solver should be small, static-shape where required, and compatible with the competition's ONNX restrictions.

## 5. Current Results

Current EDA and diagnostics results:

- `400 / 400` normalized tasks are loaded.
- Median train examples per task is `3`.
- `386` tasks have one test case.
- `14` tasks have multiple test cases.
- `138 / 400` tasks change shape.
- `262 / 400` tasks are same-area.
- Strict same-shape solver diagnostics cover `62` tasks.
- Strict shape-changing heuristics cover `4` tasks.
- Strict simple solvers therefore explain only a small first slice of the benchmark; the dominant unsolved tracks remain object movement/selection and crop/extract/compress.
- Recommended largest solver tracks are object movement/selection and crop/extract/compress.

Current baseline results:

- The first scorer-compatible solved-task-only submission completed successfully.
- All-time best and current active leaderboard public score is `3590.21`, stable across notebook auto-submits from `2026-06-10` (v23) through a `2026-07-20` rerun (`399 / 400` validated, `1` unsolved).
- The `2026-06-04`-`06-09` history (`3235.97` peak, `3068.97` plateau, `2561.08` active, and the `2026-06-09` manual v9 `SubmissionStatus.ERROR`) is retired; see `docs/05_agent_score_track.md` for the full run ledger.
- The accepted interface is static one-hot `float32` with shape `[1, 10, 30, 30]`.
- The accepted archive strategy is solved-task-only: include only validated task models, never invalid placeholders.
- Transform-library candidates dominate solved coverage. The wave4 "cheaper local solver" hypothesis (`artifacts/analysis/wave4_cost_audit.md`) was tested `2026-07-20` with a live full-validation rerun and disproven: `solve_task()` already picks the lowest-cost valid solver everywhere, so this specific angle is closed. Open question: the `2026-07-20` rerun solved `2` more tasks than v33 (`task101`, `task118`) without moving the public score — cause not yet understood.
- Notebook 5 focuses on cost-aware input-derived solver export, with public-output fallback disabled by default. Note: the committed `notebooks/05_simple_solver_export.ipynb` has drifted from the working `kaggle/` kernel bundles (a solver-loop bug means it would currently export nothing) — the pushed kernels are unaffected, but the repo notebook needs a fix before further local edits.

## 6. Solution Principles

- Prefer interpretable solver families over broad learned models because the benchmark is low-shot.
- Separate same-shape and shape-changing tasks early.
- Treat background handling as a first-class primitive.
- Track exact task ids covered by every solver.
- Validate on all train pairs before ONNX export.
- Keep ONNX files structurally valid and compact.
- Keep score-oriented public-output fallbacks labeled separately from rule-derived solvers.
- Prefer valid solved-task-only archives over complete archives with weak placeholders.

## 7. Next Work

Submission strategy is notebook-first. See [Section 9](#9-kaggle-submission-flow-notebook-first) for the full flow.

Phased score targets (phases 0-1 are done, retained for history):

| Phase | Target score | Primary action | Status |
| --- | ---: | --- | --- |
| 0 — recover baseline | ≥ `3068` COMPLETE | Re-run main competition kernel (`neurogolf-2026-simple-logic-solver`) | Done (`2026-06-04`) |
| 1 — expand safely | ≥ `3235` COMPLETE | Fix export validation in v9 kernel, then push dual-library kernel | Done, surpassed (`3590.21` since `2026-06-10`) |
| 2 — wave4 solver-swap targeting | `~3648`-`3753` | Raise lowest-scoring exported tasks by swapping to a cheaper *existing* local solver | Disproven (`2026-07-20`) |
| 3 — native solvers for worst-cost tasks | TBD, see below | Hand-build small native solvers for the specific `A_critical`/`B_high` tasks currently solved only by bloated external-library graphs | Current priority (`2026-07-20`) |

### 7.1 Cost model (why phase 2 failed and phase 3 can work)

The scorer's per-task score is `max(1, 25 - ln(cost))` where
`cost = total_params + total_bytes + total_macs`, and Conv layers dominate
`total_macs` (`c_out * c_in * kernel² * 900`, fixed by the `30x30` grid).
This is a **log scale**: cutting cost by half only buys ~0.7 points, so
phase 2's "swap to an existing cheaper solver" search (already
exhaustively done inside `solve_task()`) could never move much even if it
weren't already optimal — score gains need order-of-magnitude+ cost cuts.

Inspected the actual exported graph for `task379` (cost `188,976,965`,
score `5.94`, the worst in the fleet): **1,263 nodes, 233 separate Conv
layers, 740 boolean comparison ops.** That is not inherent task
difficulty — it is the external transform-library's generic
search/DSL-compiled representation being extremely inefficient. A
hand-built native solver expressing the same transformation directly
(a handful of ops, not 233 Conv layers) could plausibly cut cost by
100-10,000x, moving that one task from score `~6` toward `~20+`.

This only pays off for the specific `9` `A_critical` + `29` `B_high`
tasks (`artifacts/analysis/wave4_cost_audit.md`, regenerate against the
latest manifest before trusting stale numbers) — it requires genuine
per-task rule discovery (inspect train pairs, find the actual
transformation, build/validate a new solver), not a mechanical fix.

Current score-improvement priorities, in order:

1. Submit only through competition-linked kernels; do not manually submit downloaded `submission.zip` files.
2. Do not re-attempt the wave4 "swap to a cheaper existing local solver" angle: proven closed, see §7.1.
3. Work the worst-cost tasks one at a time: pick from the bottom of a freshly-regenerated `wave4_cost_audit.md`, inspect that task's train pairs directly (`load_tasks`, `task_pairs`), look for a compact rule, prototype a new `try_*_solver` function, validate with full ONNX Runtime pair-checking (never the relaxed mode — see the `2026-07-20` lesson in `docs/06_coding_rules.md` §5), then add it to `solve_task()`'s solver list in both `notebooks/05_simple_solver_export.ipynb` and the `kaggle/` kernel bundle.
4. Before spending effort on any currently-*unsolved* task (right now only `task115`, deliberately blocklisted for scorer runtime-risk): confirm it's actually part of the scored subset first. `task101`/`task118` were newly solved `2026-07-20` and the public score didn't move at all, suggesting not every task_id counts toward the public score. Re-verify with a controlled single-task before/after comparison if pursuing coverage.
5. `task115` specifically: `task118` (same runtime-risk blocklist category) was successfully re-enabled `2026-07-20` — worth checking whether `task115`'s original blocking reason still applies before assuming it's permanently out of reach.
6. Track `solver_family`, `validation_scope`, `candidate_count`, `train_fit`, `onnx_exported`, and `reason_rejected`
   in every manifest row so rule-derived progress is separate from fallback coverage.
7. Fix the `notebooks/05_simple_solver_export.ipynb` drift from the working `kaggle/` kernel bundles before making further local edits to it (see `docs/06_coding_rules.md`) — lower urgency now since the deployed kernels are unaffected, but blocks safely prototyping new solvers locally in the repo notebook.

Recommended submission kernel:

- Expansion: `tuannm3812/neurogolf-2026-simple-logic-solver-export-v9` (dual transform-library datasets) — this has been the active kernel since v17 and currently scores `3590.21`.

Recommended export notebook:

- `notebooks/05_simple_solver_export.ipynb`

Expected output:

- `submission.zip` (written to `artifacts/submission/local-runs/<run_id>/submission.zip`)
- `simple_logic_manifest.csv` (written to `artifacts/submission/local-runs/<run_id>/simple_logic_manifest.csv`)
- task-level solver-family counts in the notebook output
- `solver_family`, `solver_kind`, `validation_scope`, `candidate_count`, `train_fit`, `onnx_exported`, and
  `reason_rejected` in the manifest

Score plateau triage:

- `notebooks/06_score_plateau_triage.ipynb`
- compare one or more `simple_logic_manifest.csv` files from Kaggle output datasets;
- identify whether new solver families selected any task ids;
- render newly added or dynamic-crop task panels;
- write `score_triage_artifacts.zip` for review.

Supporting diagnostics:

- `notebooks/04_solver_development.ipynb`

Supporting diagnostic artifacts:

- `neurogolf_solver_candidate_table.csv` (`artifacts/analysis/`)
- `neurogolf_same_shape_solver_fits.csv` (`artifacts/analysis/`)
- `neurogolf_shape_solver_fits.csv` (`artifacts/analysis/`)
- `neurogolf_solver_development_artifacts.zip` (`artifacts/analysis/`)

Recommended first solver targets:

- full-background-fill tasks;
- global color-map tasks;
- low-component object selection tasks;
- crop/extract/compress tasks with clear bounding-box behavior.

## 8. Next Implementation Plan

### 8.1 Build the Solver Candidate Table

Create a task-level table that joins:

- EDA structural features;
- solver diagnostics;
- connected-component features;
- current baseline model family;
- validation result;
- recommended next solver family.

Expected artifact:

- `neurogolf_solver_candidate_table.csv`

### 8.2 Implement Same-Shape Rule Solvers

Start with the highest-confidence same-shape families:

- background-to-single-color;
- global color map;
- mask-fill;
- object-preserving recolor;
- simple symmetry transforms only where diagnostics prove train-fit.

Expected result:

- exact task ids solved on all train pairs;
- failure examples for near misses;
- ONNX export feasibility per solver.

Expected artifact:

- `submission.zip`
- `simple_logic_manifest.csv`
- solver-family validation summaries from notebook output

### 8.3 Implement Object-Level Solvers

Use connected components to test object-level hypotheses:

- select largest/smallest object;
- select object by color;
- move object by inferred vector;
- remove background/noise objects;
- copy, align, or complete object patterns.

Expected result:

- object solver coverage table;
- rendered before/after examples for solved and failed tasks.

### 8.4 Implement Shape-Changing Solvers

Prioritize compression and expansion separately:

- crop to non-background bounding box;
- crop to selected object;
- fixed-template output from selected object;
- integer scale;
- tile or periodic repetition;
- object replication or construction.

Expected result:

- train-fit coverage by shape-change family;
- list of tasks needing dynamic output shape handling;
- ONNX export plan for each supported shape family.

### 8.5 Replace Packaging Baselines

Once a real solver explains all train pairs for a task, replace the public-output baseline model for that task.

Replacement criteria:

- solver matches every train pair;
- solver output is derived from input;
- exported ONNX validates locally;
- file size is below the competition limit;
- manifest records the solver family, validation scope, and rejection reason for each task.

## 9. Kaggle Submission Flow (Notebook-First)

Submissions must go through a **competition-linked kernel** (`competition_sources: ["neurogolf-2026"]`). The notebook writes `submission.zip` to `/kaggle/working`. Submit the **notebook run output**, not a locally downloaded zip file.

**Do:**

- Push and run the export kernel via CLI.
- Submit with `kaggle competitions submit -k <kernel-slug> -f submission.zip -v <version>`.
- Use CLI to orchestrate (`kernels push`, `kernels status`, `kernels output`, `competitions submit -k ...`).

**Do not:**

- Upload a local file path with `competitions submit -f /path/to/submission.zip`.
- Treat manifest `400 / 400 exported` as scorer-safe without pre-export validation.
- Fill missing tasks with invalid placeholders to make the archive look complete.

Why: the `2026-06-09` manual v9 submit failed with `SubmissionStatus.ERROR` because the pulled archive contained `400` ONNX files but `58` were scorer-incompatible (dynamic tensor shapes, ORT load failures, unsupported ops). Every best-scored run since (`3068.97`, `3235.97`, and the current `3590.21`) used **validated solved-task-only** archives submitted by the notebook.

### 9.1 Kernel tracks

| Track | Kernel slug | Datasets | Target |
| --- | --- | --- | ---: |
| Recovery | `tuannm3812/neurogolf-2026-simple-logic-solver` | `karnakbaevarthur/neurogolf-2026-task-transformation-library` | ≥ `3068` (baseline floor, superseded) |
| Expansion | `tuannm3812/neurogolf-2026-simple-logic-solver-export-v9` | above + `konbu17/neurogolf-2026-blended-401-v117` | current active score `3590.21`; no confirmed higher target yet (wave4 swap target disproven `2026-07-20`) |

The expansion track has been the active one since the v17-v33 wave-based iterations (`docs/05_agent_score_track.md`); its original `≥ 3235` target was reached and surpassed weeks ago.

Kernel bundle paths in this repo:

- `kaggle/neurogolf-2026-simple-logic-solver-export-v9/`

### 9.2 Archive policy

- **Solved-task-only:** only tasks with `train_fit=True` and scorer-compatible ONNX enter `submission.zip`.
- **`EXPORT_PUBLIC_OUTPUT_FALLBACK = False`** by default.
- **`USE_TRANSFORM_LIBRARY = True`** with auto-discovery of mounted library paths on Kaggle.
- Every rejected task must appear in the manifest with `onnx_exported=False` and a `reason_rejected` code.

Pre-export validation gate (reject before zip write):

- input/output names are `input` / `output`
- input/output dtype is `float32`
- input/output shape is exactly `[1, 10, 30, 30]` (no `0` dimensions)
- no banned ops: `Loop`, `Scan`, `NonZero`, `Unique`, `Script`, `Function`
- `ir_version <= 9` for external-library models
- ONNX Runtime CPU session loads successfully
- all available train and public test pairs pass inference
- file size `< 1.44MB`

See `docs/03_baseline_models.md` for the full contract and validation details.

### 9.3 CLI workflow

Keep Kaggle credentials available:

- `KAGGLE_CONFIG_DIR=~/Downloads` (or your folder containing `kaggle.json`).

One-command loop (push, wait, pull output, submit notebook run):

```bash
KAGGLE_CONFIG_DIR=~/Downloads ./scripts/run_kaggle_export.sh
```

Manual steps:

```bash
export KAGGLE_CONFIG_DIR=~/Downloads
export KAGGLE=/Users/tuanm.nguyen/Library/Python/3.9/bin/kaggle

# 1) Push kernel (triggers GPU run)
$KAGGLE kernels push -p kaggle/neurogolf-2026-simple-logic-solver-export-v9
# note the pushed version number, e.g. 2

# 2) Poll until complete
$KAGGLE kernels status tuannm3812/neurogolf-2026-simple-logic-solver-export-v9

# 3) Submit the notebook run output to the competition
$KAGGLE competitions submit -c neurogolf-2026 \
  -k tuannm3812/neurogolf-2026-simple-logic-solver-export-v9 \
  -f submission.zip \
  -v 2 \
  -m "Notebook export run"

# 4) Check submission status and score
$KAGGLE competitions submissions -c neurogolf-2026 | head -5

# 5) Pull output for local triage (optional; do not re-upload this file)
RUN_ID=$(date +%Y-%m-%d-%H%M)
$KAGGLE kernels output tuannm3812/neurogolf-2026-simple-logic-solver-export-v9 \
  -p artifacts/submission/kaggle-runs/$RUN_ID -o
```

Important: `-f submission.zip` refers to the **output file produced by the kernel run**, not a local path. Do not use `-f artifacts/.../submission.zip`.

Optional environment overrides for transform-library discovery:

- `TRANSFORM_LIBRARY_DIR` or `TRANSFORM_LIBRARY_PATH`
- library roots may also contain `simple_logic_onnx/task*.onnx` or nested `**/submission/task*.onnx`

Post-run verification:

- confirm `simple_logic_manifest.csv` exists in kernel output;
- confirm submission status is `COMPLETE`, not `ERROR`;
- compare manifest against prior run with `scripts/agents/neurogolf_agents.py compare`.

### 9.4 Decision rules

| Observation | Action |
| --- | --- |
| Score increases, status `COMPLETE` | Keep kernel version and archive policy |
| Status `ERROR` | Revert to solved-task-only; tighten validation; do not manual-submit pulled output |
| Exported count rises, score flat | Run plateau triage; check public-scored task overlap |
| `external_missing` dominates | Fix dataset mount in kernel metadata, not solver search |
| Dynamic shape or ORT failure in manifest | Exclude task from zip; record `reason_rejected` |

## 10. Agent-Driven Score Loop

Use `scripts/agents/neurogolf_agents.py` to enforce a predictable improvement cycle:

- `score`: pull latest Kaggle submission list and best public score.
- `report`: print or write a combined score + manifest summary.
- `compare`: show recovered task IDs between manifest versions.
- `track`: aggregate versions and emit keep/change lessons for each run.

Suggested cycle:

1. Push the competition export kernel and wait for Kaggle run completion.
2. Confirm auto-submission status is `COMPLETE` via `competitions submissions`.
3. Pull kernel output to a local directory for triage only (do not re-submit the pulled zip).
4. Run `report` with the pulled manifest.
5. Run `track` to append run summaries to history and capture keep/change notes.
6. Fix the highest-frequency rejection reason first (`external_missing` or scorer validation failures).
7. Re-run the kernel and then run `compare` against the prior manifest for a hard win metric.
