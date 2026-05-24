# EDA and Solver Diagnostics Insights

This note summarizes what the current EDA and solver-diagnostics notebooks tell us about the NeuroGolf 2026 task distribution. The goal is to turn notebook output into modeling decisions: which task families matter, which simple solvers are worth implementing first, and where deeper analysis is still needed.

## 1. Executive Summary

- Data coverage is complete: `400 / 400` normalized tasks are available.
- The benchmark is low-shot: the median task has `3` training examples, with a range from `2` to `10`.
- Shape-changing behavior is too common to defer: `138 / 400` tasks change shape in train pairs.
- Same-area tasks are still the majority: `262 / 400` tasks preserve approximate area.
- Color `0` dominates input and output cells, so background handling should be a core primitive.
- Strict simple solvers explain only a limited slice of the benchmark: `62` tasks for same-shape rules and `4` tasks for simple shape-changing heuristics.
- The strict solver slice is useful for first exports, but it leaves most tasks for object-level, crop/extract, construction, and pattern logic.
- The next modeling work should focus on object extraction, object movement/selection, crop/compress logic, and construction rules rather than broad learned models.

## 2. Data Health

- Input discovery is healthy: `800` JSON files were discovered.
- The loader normalized these into `400` tasks.
- Expected task coverage is complete: `task001` through `task400` are present.
- All loaded tasks include test outputs in the current public benchmark files.

Interpretation:

- Missing data is not currently a blocker.
- Downstream errors are more likely to come from ONNX generation, submission structure, evaluator constraints, or weak solver logic than from data loading.
- Complete task coverage also makes per-task manifests valuable because every modeling decision can be audited against the full expected id set.

## 3. Dataset Structure

Training examples are sparse:

- Median train examples per task: `3`
- Minimum train examples: `2`
- Maximum train examples: `10`

Test-case structure:

- `386` tasks have exactly one test case.
- `14` tasks have multiple test cases.

Interpretation:

- This is not a setting where conventional model training per task is attractive. There are too few examples.
- Rule induction, hypothesis search, symbolic transforms, and object-centric heuristics should be prioritized.
- The `14` multi-test tasks are operationally important because they expose whether a model truly conditions on the input or merely emits a fixed output.

## 4. Shape Behavior

Task shape categories from the structural deep dive:

- `262` same-area tasks
- `97` strong compression tasks
- `26` strong expansion tasks
- `10` mild expansion tasks
- `5` mild compression tasks

Shape-changing total:

- `138 / 400` tasks change shape in train pairs.

Interpretation:

- Same-shape solvers are necessary but not sufficient.
- Strong compression tasks likely involve crop, extract, summarize, count, select, or canonicalize operations.
- Strong expansion tasks likely involve tiling, scaling, drawing, completion, or construction.
- Shape-changing tasks should be handled as a separate solver track rather than as exceptions inside same-shape logic.

High-priority shape deep dives:

- Split strong compression tasks into crop-to-bounding-box, object extraction, summarization/counting, and fixed-template output.
- Split strong expansion tasks into nearest-neighbor scale, periodic tile, object replication, grid construction, and drawing/completion.
- Track whether output shape is fixed across train examples or derived from input geometry.

## 5. Color and Palette Behavior

Color `0` dominates both train inputs and outputs.

Palette relation across tasks:

- `176` same-palette tasks
- `91` removes-color tasks
- `86` introduces-color tasks
- `47` introduces-and-removes-color tasks

Interpretation:

- Same-palette tasks are more likely driven by geometry, movement, selection, or arrangement than by inventing new colors.
- Removes-color tasks often indicate filtering, object selection, masking, background normalization, or crop/extract behavior.
- Introduces-color tasks suggest marking, filling, completion, derived labels, or conversion from object relation to output annotation.
- Introduces-and-removes-color tasks are likely more compositional and should be treated as harder solver candidates.

High-priority color deep dives:

- Identify dominant background token per task rather than assuming `0` is always background.
- Separate color-map tasks from color-creation tasks.
- Measure whether introduced colors are constant across train pairs or derived from input colors.
- Compare input/output color counts against shape-change groups.

## 6. Simple Solver Coverage

Strict same-shape solver compatibility covers `62` tasks.

Same-shape diagnostic breakdown:

- `background_to_single_color`: `50`
- `global_color_map`: `5`
- `rotate_180`: `2`
- `transpose`: `2`
- `rotate_90`: `1`
- `flip_horizontal`: `1`
- `flip_vertical`: `1`
- `identity`: `0`
- `rotate_270`: `0`

Strict shape-changing heuristics cover only `4` tasks:

- `nearest_integer_scale`: `2`
- `crop_non_background`: `1`
- `periodic_tile_from_input`: `1`

Interpretation:

- Background-to-single-color is the strongest immediate baseline family.
- Pure global color maps exist but are not a large-enough strategy by themselves.
- Simple flips/rotations/transposes are rare as complete task explanations.
- The current crop/scale/tile checks are intentionally strict; low coverage does not mean these ideas are unimportant, only that naïve versions are insufficient.

## 7. Object Complexity

Connected-component diagnostics show a wide spread in object complexity.

High-component stress tasks include:

- `task110`
- `task205`
- `task017`
- `task305`
- `task074`

Interpretation:

- Low-component tasks are good candidates for object extraction, movement, selection, and relation solvers.
- High-component tasks likely require pattern, counting, grid-line, texture, or global-logic approaches.
- Component count alone is not enough. We also need object shape, bounding-box density, color grouping, and relative-position features.

Recommended object-level additions:

- Connected components by each non-background color.
- Bounding boxes, areas, aspect ratios, and compactness.
- Object preservation checks between input and output.
- Object movement vectors and alignment.
- Symmetry and repetition features.
- Grid-line detection and region segmentation.

## 8. Modeling Priority

Recommended solver tracks from diagnostics:

- `148` tasks: deep dive object movement/selection
- `101` tasks: deep dive crop/extract/compress
- `62` tasks: implement simple same-shape solver
- `52` tasks: deep dive pattern/counting/global logic
- `33` tasks: deep dive expand/tile/construct
- `4` tasks: implement simple shape solver

Recommended implementation order:

1. Background-to-single-color and global color-map solvers.
2. Object extraction, object movement, and object selection solvers.
3. Crop, extract, and compression solvers.
4. Expand, tile, and construct solvers.
5. Pattern, counting, grid-line, and global-logic diagnostics for high-component tasks.

## 9. Do We Need More Deep-Dive Analysis?

Yes, but it should be targeted rather than broad. The current EDA is enough to reject a purely generic modeling approach and enough to define the first solver families. The next notebook should first produce a solver candidate table, then use that table to decide which deep dives are worth doing. The next deep dives should be solver-enabling:

- For the `62` simple same-shape candidates, export exact task ids and expected solver family.
- For the `101` crop/extract/compress candidates, classify whether output is object crop, bbox crop, fixed template, count summary, or selected object.
- For the `148` object movement/selection candidates, compute object correspondences between train inputs and outputs.
- For the `33` expand/tile/construct candidates, classify scaling, tiling, replication, and drawing patterns.
- For the `52` pattern/counting/global-logic candidates, add grid-line, region-count, repetition, and symmetry diagnostics.

The immediate next notebook should therefore be solver-development oriented, not more descriptive EDA.

Current next-step artifact:

- `notebooks/4_solver_development.ipynb` creates train-fit candidate tables for simple same-shape and shape-changing solvers.
- It exports `neurogolf_solver_candidate_table.csv`, `neurogolf_same_shape_solver_fits.csv`, and `neurogolf_shape_solver_fits.csv`.
- It also writes `neurogolf_solver_development_artifacts.zip` so the candidate tables can be downloaded from Kaggle as one bundle.
- The following notebook after that should export the highest-confidence simple same-shape solvers to ONNX, starting with background-to-single-color and global color-map candidates.

Latest solver-development routing:

- `158` tasks: deep dive object movement/selection
- `99` tasks: deep dive crop/extract/compress
- `62` tasks: export simple same-shape solver
- `45` tasks: deep dive pattern/counting/global logic
- `32` tasks: deep dive expand/tile/construct
- `4` tasks: export simple shape solver

## 10. Visual Evidence and Figure Insights

The EDA figures are included here as evidence for modeling decisions. The goal is not to list every generated file; it is to connect each visual to a solver implication.

### 10.1 Pair Distributions

![Pair distributions](figures/eda/1_pair_distributions.png)

Insight:

- Most tasks are low-shot, with the median task providing only `3` training examples.
- `386 / 400` tasks have one test case, but the `14` multi-test tasks are disproportionately important for submission robustness.
- Modeling implication: prioritize rule induction and train-fit checks over statistical fitting, and keep multi-test tasks in every validation pass.

### 10.2 Grid Geometry

![Grid geometry](figures/eda/2_grid_geometry.png)

Insight:

- The benchmark splits into a same-shape majority and a substantial shape-changing minority.
- `138 / 400` tasks change shape in training pairs, so dynamic output construction cannot be treated as an edge case.
- Modeling implication: maintain separate solver tracks for same-shape transformations, compression/extraction, and expansion/construction.

### 10.3 Color Frequency

![Color frequency](figures/eda/3_color_frequency.png)

Insight:

- Color `0` dominates both train inputs and outputs.
- Background logic should be explicit rather than incidental, but task-specific checks are still needed because removing or introducing color `0` can itself be part of the rule.
- Modeling implication: background detection, masking, fill operations, and object extraction should be first-class primitives in solver code.

### 10.4 Palette Relation

![Palette relation](figures/eda/5_palette_relation.png)

Insight:

- `176` tasks keep the same palette, but `224` tasks alter the palette in some way.
- Introduced and removed colors indicate that many transformations are semantic, not only geometric.
- Modeling implication: separate pure geometry solvers from recoloring, marking, filtering, and label-generation solvers.

### 10.5 Difficult Task Gallery

The difficult-task gallery selects concrete stress examples from the latest EDA run.

![Task 398 strong expansion](figures/eda/7_difficult_task398_strong_expansion.png)

Insight:

- `task398` is the strongest expansion sample and should anchor expand/tile/construct solver design.
- Modeling implication: expansion solvers need to infer output size and repeated structure, not just recolor or copy cells.

![Task 355 strong compression](figures/eda/8_difficult_task355_strong_compression.png)

Insight:

- `task355` is an extreme compression sample, with output collapsing to a tiny target grid.
- Modeling implication: compression solvers need object selection, summarization, counting, or canonicalization logic beyond simple crop-to-bounding-box.

![Task 054 largest grid](figures/eda/9_difficult_task054_largest_grid.png)

Insight:

- `task054` is a largest-grid stress case.
- Modeling implication: dense ONNX operations should be checked against this kind of task before being adopted broadly, because size and runtime can become limiting even when the rule is simple.

![Task 022 rich palette](figures/eda/10_difficult_task022_rich_palette.png)

Insight:

- `task022` stresses color handling and palette-rich visual parsing.
- Modeling implication: object grouping by color and palette-aware comparisons are needed before moving into more complex object selection.

![Task 399 multi-test](figures/eda/11_difficult_task399_multi_test.png)

Insight:

- `task399` is a multi-test stress case.
- Modeling implication: it should stay in the validation set for any ONNX solver that branches on input, because constant-output shortcuts can hide failures on single-test tasks.

![Task 003 mixed palette](figures/eda/12_difficult_task003_mixed_palette.png)

Insight:

- `task003` combines shape change with color replacement.
- Modeling implication: early solvers should not assume that shape-change and palette-change families are independent.

### 10.6 Solver Planning Buckets

![Solver planning buckets](figures/eda/13_solver_planning_buckets.png)

Insight:

- The broad EDA buckets confirm that the next phase should be solver-specific rather than more descriptive EDA.
- The largest broad bucket is shape-changing, followed by larger same-shape tasks that likely need object or pattern reasoning.
- Modeling implication: implement narrow train-fit solvers first, then use failure buckets to decide where deeper object diagnostics are necessary.

## 11. Solver Development Output Insights

The downloaded `neurogolf_solver_development_artifacts.zip` contains the three expected files:

- `neurogolf_solver_candidate_table.csv`
- `neurogolf_same_shape_solver_fits.csv`
- `neurogolf_shape_solver_fits.csv`

Candidate-table coverage is complete: `400` rows and `27` columns.

Latest candidate routing:

- `158` tasks: deep dive object movement/selection
- `99` tasks: deep dive crop/extract/compress
- `62` tasks: export simple same-shape solver
- `45` tasks: deep dive pattern/counting/global logic
- `32` tasks: deep dive expand/tile/construct
- `4` tasks: export simple shape solver

Immediate export candidates:

- `50` tasks fit `background_to_single_color`.
- `5` tasks fit `global_color_map`: `task016`, `task267`, `task276`, `task309`, `task337`.
- `4` tasks fit simple shape-changing solvers: `task031`, `task223`, `task249`, `task307`.

Deep-dive implications:

- Object movement/selection is the largest queue at `158` tasks, with median `4` max components and max `10`; this is the best next analysis target after simple solver export.
- Crop/extract/compress has `99` tasks and median area ratio `0.15`; this queue likely mixes object extraction, summary outputs, and selected-object canonicalization.
- Pattern/counting/global logic has only `45` tasks but much higher component complexity, with median `17` max components and maximum `782`; these should be deferred until simpler object and compression tracks are measured.
- Expand/tile/construct has `32` tasks with median area ratio `4.0`; this track needs output-size inference and construction rules.

Readiness assessment:

- Yes, we have enough information to move to the next step.
- The next notebook should export real ONNX solvers for the safest simple same-shape candidates first: full-background-fill and global color-map models. Geometric transforms should follow once the first solver archive is validated.
- In parallel, the next diagnostic deep dive should focus on object movement/selection because it is the largest unsolved queue and still has manageable component counts.

Next notebook:

- `notebooks/5_simple_solver_export.ipynb` exports the first input-derived ONNX solver families.
- It starts with the safer exportable subset of same-shape rules: full-background-fill and global color-map models.
- It preserves a complete `submission.zip` by keeping fallback models for tasks not yet solved by input-derived rules.
