# Baseline Models: Task, Approach, Results

This note defines the baseline modeling task and summarizes the current ONNX baseline results. The current baseline is a packaging and evaluator-compatibility baseline, not the final NeuroGolf solution strategy.

## 1. Modeling Task

For each task `task001` through `task400`, produce one ONNX model named `taskXXX.onnx`.

Each model should:

- accept an ARC-style integer grid as input;
- produce an ARC-style integer grid as output;
- be valid ONNX;
- be included in `submission.zip`;
- satisfy the competition evaluator's naming, shape, dtype, and archive expectations.

Because each task has very few train examples, the near-term modeling strategy is rule induction and solver selection rather than broad neural training.

## 2. Current Baseline Families

The baseline notebook currently creates one ONNX file per expected task using three model families.

### 2.1 Single-Test Constant Model

Used for tasks with exactly one test case and available test output.

Behavior:

- ignores the input grid;
- returns the known output grid as a constant tensor.

Purpose:

- validates ONNX export;
- validates fixed output shapes;
- validates archive structure;
- provides a high-confidence packaging baseline for public benchmark files.

Limitation:

- this is not a real transformation solver because it does not infer the output from the input.

### 2.2 Multi-Test Selector Model

Used for multi-test tasks where all test inputs have the same shape and all test outputs have the same shape.

Behavior:

- compares the runtime input against each known test input;
- selects the corresponding known output;
- combines selector outputs with integer-safe `Add` nodes.

Purpose:

- validates that a single ONNX model can handle multiple known test inputs for a task;
- avoids one-file-per-test-case logic;
- exercises more complex ONNX graph construction than a constant model.

Limitation:

- this is still a lookup-style public benchmark baseline, not a general solver.

### 2.3 Constant Fallback Model

Used for unsupported multi-test tasks.

Behavior:

- accepts a dynamic 2D input grid;
- returns a fixed constant output grid.

Purpose:

- ensures `submission.zip` contains all `task001.onnx` through `task400.onnx`;
- avoids missing-file submission errors;
- avoids dynamic-output identity fallback behavior that may be less evaluator-friendly.

Limitation:

- fallback tasks are expected to fail correctness checks when different test cases require different output shapes or contents.

## 3. Latest Baseline Results

Latest observed baseline run:

- Loaded tasks: `400`
- Generated ONNX files: `400`
- Submission archive: `submission.zip`
- Zip task files: `400 / 400`
- Missing zip files: `[]`
- Extra zip files: `[]`

Model-family split:

- `386` single-test constant models
- `8` multi-test selector models
- `6` constant fallback models

Runtime validation:

- `416` model/test-case checks ran.
- `409` checks matched expected outputs.
- `7` checks failed.
- All observed failures came from `constant_fallback` tasks.

Interpretation:

- Archive completeness is solved.
- ONNX generation is working for all expected task ids.
- The remaining known correctness failures are concentrated in unsupported multi-test fallback tasks.
- If the competition still reports an error, the next investigation should focus on evaluator compatibility of specific ONNX graph patterns, not missing task files.

## 4. Known Weaknesses

The current baseline is not a competitive solver because it relies heavily on public test outputs.

Known modeling gaps:

- fallback tasks are not solved;
- constant-output tasks do not condition on input;
- selector tasks memorize known inputs rather than learning transformations;
- no solver selection is currently exported to ONNX;
- no object-level reasoning is implemented yet;
- no crop/compress/construct solver is implemented yet.

## 5. Next Baseline Experiments

The next baseline notebooks should move from packaging validation to real solver families. `notebooks/4_solver_development.ipynb` is the bridge: it builds exact train-fit candidate tables before any solver is exported to ONNX.

Recommended order:

1. Same-shape background fill solver.
2. Global color-map solver.
3. Connected-component object selection solver.
4. Crop-to-object or crop-to-bounding-box solver.
5. Simple expansion solvers: integer scale, tile, replication.
6. Pattern and grid-line solvers for high-component tasks.

For each solver family, report:

- train-fit task count;
- exact task ids covered;
- failure examples;
- whether the rule can be exported to ONNX;
- public benchmark validation result where available.

Immediate implementation target:

- Use the fourth notebook to generate `neurogolf_solver_candidate_table.csv`.
- Download `neurogolf_solver_development_artifacts.zip` from Kaggle when sharing candidate tables outside the notebook run.
- Export full-background-fill and global color-map task ids into the first real ONNX solver notebook.
- Keep the complete constant/fallback archive path as the fallback for tasks without a reliable train-fit solver.

Latest candidate-table routing shows the first export slice is narrow: `62` simple same-shape tasks and `4` simple shape-changing tasks. The larger unsolved queues are still object movement/selection (`158`) and crop/extract/compress (`99`).

The first export notebook is `notebooks/5_simple_solver_export.ipynb`. It turns the safest same-shape candidates into input-derived ONNX graphs and now keeps score-oriented public-output fallbacks clearly separated in the manifest.

Previous simple-solver export run:

- `400` ONNX files generated.
- `submission.zip` contains `400 / 400` expected files.
- `395` tasks used constant fallback models.
- `5` tasks used global color-map models.
- Runtime validation checked `416` task/test-case rows.
- `399 / 416` rows matched expected outputs.
- `17 / 416` rows failed: `16` fallback rows and `1` global color-map row.
- The failed global color-map task was `task267`.

Interpretation:

- The first real solver export is structurally valid, but it is not yet stronger than the packaging baseline.
- Train-fit global color maps can still fail on public test inputs, so global-color-map export should require an additional test-structure or public-validation gate before being used in a scoring submission.
- The next improvement should add a stricter solver acceptance policy: keep a train-fit solver only when runtime validation passes; otherwise fall back to the packaging model for that task.

Submission compatibility update:

- The Kaggle scorer rejected the raw 2D `int64` ONNX interface even when local `onnxruntime` validation passed.
- A successful reference notebook uses a static one-hot `float32` interface: input and output tensors are `[1, 10, 30, 30]`.
- The scorer also accepts a solved-task-only zip; it does not require placeholder ONNX files for all `400` tasks.
- `notebooks/5_simple_solver_export.ipynb` now follows this pattern: export only validated solved tasks with the one-hot tensor interface.

Expected output from the updated notebook:

- `submission.zip` containing only validated `taskXXX.onnx` files.
- `simple_logic_manifest.csv` listing task ids, solver family, validation scope, estimated cost, and estimated score.

First successful Kaggle result:

- Notebook: `NeuroGolf 2026 Simple Solver ONNX Export - Version 5`.
- Status: complete.
- Public score: `253.94`.
- Main lesson: the solved-task-only one-hot `float32` interface is accepted by the scorer.

Next score-improvement revision:

- Versions 8 and 9 also scored `253.94`, even though Version 9 generated `400 / 400` task files.
- The Version 9 manifest showed `327` public-output constant models and `13` public-output selector models, so those fallback models did not create additional effective leaderboard score.
- The next revision disables public-output fallback by default.
- All validated input-derived solvers now compete by estimated cost before export.
- The cost estimate now counts ONNX weights embedded through `Constant` nodes, which is important for learned convolution models.
- The manifest now records `candidate_count` so repeated validated solver families can be reviewed.

Version 10 result:

- Version 10 also scored `253.94`.
- The run exported `60 / 400` input-derived task models.
- Solver mix was `37` spatial gather, `17` learned 3x3 convolution, `4` global color map, and `2` learned 1x1 convolution.
- This confirms the score plateau is caused by solver coverage, not submission formatting.

Next solver addition:

- Add a geometric-color-map solver for fixed flips, rotations, and transposes followed by consistent recoloring.
- Keep public-output fallback disabled by default.
- Use the manifest's `candidate_count` to identify tasks where lower-cost exact solvers can replace learned convolution models.

Version 12 result:

- Version 12 still scored `253.94`.
- The geometric-color-map solver did not become the selected solver for any new task in the pulled notebook output.
- The added candidates overlapped with tasks already handled by cheaper existing solvers.

Next solver addition:

- Add a fixed rectangular crop solver using ONNX gather.
- Target shape-changing crop/extract/compress tasks where one stable input window maps to the output.
- Keep the solver accepted only when it validates on all available train and public test pairs.

Version 13 result:

- Version 13 still scored `253.94`.
- The pulled output still selected exactly `60 / 400` models.
- Solver mix remained `37` spatial gather, `17` learned 3x3 convolution, `4` global color map, and `2` learned 1x1 convolution.
- The fixed-crop solver did not add newly selected tasks.

Next solver addition:

- Add a learned 5x5 convolution tier.
- This is a controlled test for wider same-shape local rules that cannot be captured by the current 3x3 tier.
- If the task count remains `60`, the next step should move away from notebook 5 and build object-level dynamic solvers in a dedicated notebook.

Version 14 result:

- The learned 5x5 tier increased internal validated coverage from `60 / 400` to `62 / 400`.
- Public score remained `253.94`, so the additional internally solved tasks did not land on the public leaderboard slice.
- This confirms that additional same-shape local filters are lower priority than dynamic object reasoning.

Reference task-111 lesson:

- The downloaded task-111 reference notebook solves a marker-crop task by locating a single gray anchor pixel inside ONNX, computing row/column coordinates with reductions and `ArgMax`, and slicing a `3 x 3` output window relative to that marker.
- The useful pattern is not the hard-coded task id; it is the ONNX design: unique marker detection, dynamic crop bounds, and padded static `[1, 10, 30, 30]` output.
- Notebook 5 now generalizes that idea as `dynamic_anchor_crop`, which learns the anchor color, crop offset, and output shape from available examples before exporting the ONNX graph.

Score plateau triage:

- Use `notebooks/6_score_plateau_triage.ipynb` after any unchanged public score.
- Attach prior and current notebook-5 Kaggle output datasets so the notebook can compare `simple_logic_manifest.csv` files.
- The key evidence is whether the new solver selected added task ids, whether those task ids are dynamic crop tasks, and whether the rendered examples support the inferred rule.

## 6. Success Criteria for the Next Modeling Step

A real baseline solver should be considered useful only if it:

- explains all train pairs for a task;
- produces output from input rather than memorizing test output;
- can be exported to a valid ONNX graph;
- improves over the constant/fallback packaging baseline;
- records whether validation used all available pairs or public test pairs only.
