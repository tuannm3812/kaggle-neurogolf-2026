# NeuroGolf 2026 Instructions, Questions, Tasks, and Approach

This document defines the working plan for the NeuroGolf 2026 solution. It covers the competition objective, the questions we need to answer, the project tasks, and the solution approach we are building.

## 1. Competition Overview

NeuroGolf 2026 asks competitors to solve ARC-AGI style image-transformation tasks with small ONNX neural networks. Each task provides a few input/output examples showing a transformation over colored integer grids. The submission must provide ONNX models that reproduce the transformation for the task inputs.

Current public competition information indicates:

- The task set is based on ARC-AGI public training tasks.
- A submission is a `submission.zip` archive.
- The archive may contain at most one ONNX file per task.
- Task files are named `task001.onnx`, `task002.onnx`, through `task400.onnx`.
- ONNX tensors and parameters must have statically defined shapes.
- Disallowed ONNX operations include `Loop`, `Scan`, `NonZero`, `Unique`, `Script`, and `Function`.
- Each ONNX file has a size limit of `1.44MB`.
- Scoring rewards correctness and compactness. The published cost formula is `max(1, 25 - ln(cost))`, where cost combines parameters, memory footprint, and multiply-accumulate operations.

Source checked: CompeteHub mirror of the Kaggle competition page, crawled 4 days before this note and summarizing the official competition page.

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
- Which model strategy was used for each task?

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

- `notebooks/1_eda.ipynb`

Primary notes:

- `docs/2_eda_insights.md`

### 3.2 Solver Diagnostics Tasks

- Test strict simple same-shape solver hypotheses.
- Test strict shape-changing solver hypotheses.
- Compute connected-component complexity.
- Assign recommended solver tracks.
- Export diagnostic CSVs for downstream solver notebooks.

Primary notebook:

- `notebooks/3_solver_diagnostics.ipynb`

Next-step notebook:

- `notebooks/4_solver_development.ipynb`

### 3.3 Baseline Modeling Tasks

- Generate one ONNX file per expected task.
- Validate ONNX graph construction.
- Validate runtime behavior where possible.
- Build a complete `submission.zip`.
- Maintain a manifest of model strategy by task.
- Use fallback models only to guarantee structural completeness.

Primary notebook:

- `notebooks/2_baseline_models.ipynb`

Primary notes:

- `docs/3_baseline_models.md`

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
- model manifest;
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
- Public score is `253.94`.
- The accepted interface is static one-hot `float32` with shape `[1, 10, 30, 30]`.
- The accepted archive strategy is to include only validated task models rather than invalid placeholders.
- Notebook 5 now separates input-derived rule solvers from score-oriented public-output fallback models.

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

The next implementation step is to rerun the refined scorer-compatible export notebook and compare the score against the `253.94` baseline.

Recommended next notebook:

- `notebooks/5_simple_solver_export.ipynb`

Expected output:

- `submission.zip`
- `simple_logic_manifest.csv`
- task-level solver-family counts in the notebook output

Supporting diagnostics:

- `notebooks/4_solver_development.ipynb`

Supporting diagnostic artifacts:

- `neurogolf_solver_candidate_table.csv`
- `neurogolf_same_shape_solver_fits.csv`
- `neurogolf_shape_solver_fits.csv`
- `neurogolf_solver_development_artifacts.zip`

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
- `simple_solver_manifest.csv`
- `simple_solver_validation.csv`

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
- manifest records the solver family and validation status.
