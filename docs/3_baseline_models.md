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

The next baseline notebooks should move from packaging validation to real solver families.

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

## 6. Success Criteria for the Next Modeling Step

A real baseline solver should be considered useful only if it:

- explains all train pairs for a task;
- produces output from input rather than memorizing test output;
- can be exported to a valid ONNX graph;
- improves over the constant/fallback packaging baseline;
- produces a complete `submission.zip` with all 400 task files.
