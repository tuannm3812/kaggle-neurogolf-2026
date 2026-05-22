# NeuroGolf 2026

This repository develops a structured solution path for the NeuroGolf 2026 competition. The current work focuses on understanding the ARC-style task distribution, measuring simple solver opportunities, and building a reliable ONNX submission pipeline before investing in higher-complexity solvers.

## 1. Current Workflow

- `notebooks/01_eda.ipynb` builds the task inventory: coverage, train/test counts, grid geometry, color usage, shape changes, visual samples, and first-pass solver buckets.
- `notebooks/02_baseline_models.ipynb` builds the ONNX packaging baseline and writes a complete `submission.zip` containing `task001.onnx` through `task400.onnx`.
- `notebooks/03_solver_diagnostics.ipynb` measures strict simple-solver compatibility, connected-component complexity, shape-change behavior, palette deltas, and recommended solver tracks.

## 2. Key Findings

- The benchmark load is complete: `400 / 400` normalized tasks are present.
- The dataset is low-shot: the median task has `3` training examples, with a range from `2` to `10`.
- Shape-changing tasks are a major segment: `138 / 400` tasks change shape in train pairs.
- Most tasks have one test case, but `14` tasks have multiple test cases, so the submission pipeline must support more than one invocation pattern.
- Color `0` dominates train inputs and outputs, making background handling a core primitive rather than a minor detail.
- Palette behavior is mixed: `176` same-palette tasks, `91` removes-color tasks, `86` introduces-color tasks, and `47` tasks that both introduce and remove colors.

## 3. Diagnostic Results

Strict simple solvers explain a useful but limited slice of the benchmark:

- `62` tasks are compatible with at least one simple same-shape solver.
- `50` tasks match a background-to-single-color pattern.
- `5` tasks match a global color-map pattern.
- Basic geometric transforms such as flips, rotations, and transpose cover only a handful of tasks.
- Strict shape-changing heuristics currently explain `4` tasks: crop, integer scale, or periodic tiling.

The broader modeling backlog is therefore object- and structure-heavy:

- `148` tasks: object movement or object selection
- `101` tasks: crop, extract, or compress
- `62` tasks: simple same-shape solver candidates
- `52` tasks: pattern, counting, or global logic
- `33` tasks: expand, tile, or construct
- `4` tasks: simple shape solver candidates

Full notes are maintained in `docs/eda-diagnostics-insights.md`.

## 4. Baseline Status

The current baseline is primarily a submission-system validation baseline. It proves that the repository can generate a complete ONNX archive with one model per expected task.

Current baseline behavior:

- Single-test tasks use constant-output ONNX models.
- Structurally compatible multi-test tasks use an input-equality selector model.
- Unsupported tasks use a dynamic-input constant fallback so the archive remains complete.
- The generated archive is `submission.zip`.
- A manifest records which model strategy was used for each task.

This baseline is not the final modeling strategy. Its purpose is to validate file naming, ONNX graph construction, runtime validation, archive completeness, and submission mechanics.

## 5. Modeling Roadmap

The next solver notebooks should prioritize train-fit coverage before ONNX optimization:

1. Implement background-to-single-color and global color-map solvers.
2. Add connected-component object extraction, movement, and selection solvers.
3. Build crop, extract, and compression solvers for shape-changing tasks.
4. Add expansion, tiling, and construction solvers.
5. Investigate high-component tasks with pattern, counting, grid-line, and global-logic diagnostics.

The intended progression is simple: measure coverage, implement narrow solvers, validate on training pairs, then export only the reliable solver families to ONNX.
