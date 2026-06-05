# Baseline Models: Task, Approach, Results

This note records the current stable baseline and the notebook workflow we use for NeuroGolf 2026 submissions.

## 1) Task Contract

For each task ID `task001` through `task400`, the submission should contain one ONNX file named `taskXXX.onnx` in `submission.zip`.

Required interface (scorer compatible):

- ONNX input tensor: `float32`, shape `[1, 10, 30, 30]`
- ONNX output tensor: `float32`, shape `[1, 10, 30, 30]`
- Solver execution is done in static one-hot space
- ARC output is decoded from the first `h x w` region of the output canvas

## 2) Current Baseline Implementation

`notebooks/05_simple_solver_export.ipynb` is now the main export notebook and is organized into:

1. Input/paths/dependency setup
2. ARC grid↔one-hot tensor utilities
3. Uniform ONNX builders with static interface
4. Solver families and cost-based selection
5. Export packaging and manifest writing

No code changes in this pass changed solver behavior; this refinement pass focused on notebook clarity and output documentation.

## 3) Latest Run Summary (2026-06-04)

From the latest downloaded notebook output (`/tmp/neurogolf14-output/simple_logic_manifest.csv`):

- Loaded tasks: `400`
- Exported (`onnx_exported=True`): `289`
- Unsolved (`onnx_exported=False`): `111`
- Local solver coverage:
  - `50` `background_to_single_color`
  - `37` `spatial_gather`
  - `4` `global_color_map`
  - `1` `object_crop` (`dynamic_anchor_crop`)
- External transform-library coverage:
  - `197` `external_transform_library`

Total exported models: `50 + 37 + 4 + 1 + 197 = 289`

## 4) What This Means

- The external transform library has become a practical fallback and currently dominates solved coverage.
- There is no longer an all-task completed baseline; `111` tasks remain unsolved by this notebook revision.
- Public-output fallback is still available but remains disabled by default in this workflow.
- Score-relevant progress will now come from improving dynamic/object-centric families, not from formatting cleanup.

## 5) Current Solver Families in the Notebook

- `background_to_single_color`
- `global_color_map` (1x1 mapping)
- `geometric_color_map` (fixed geometry + color map)
- `spatial_gather`
- `fixed_crop`
- `nearest_integer_scale`
- `periodic_tile`
- `single_object_shift`
- `largest_object_crop`
- `dynamic_bbox_crop`
- `dynamic_anchor_crop`
- `learned_conv_{1x1,3x3,5x5}` (feature-flagged)
- `external_transform_library` (runtime-selected, validated candidate models)

## 6) Manifest and Debugging

`simple_logic_manifest.csv` is the control surface for validation and debugging.

Tracked fields:

- `task_id`
- `solver_family`
- `solver_kind`
- `validation_scope`
- `candidate_count`
- `train_fit`
- `onnx_exported`
- `reason_rejected`
- `cost_estimate`
- `submission_source`
- `submission_model_size`

Use this manifest to answer:

- Why was a task not exported?
- Which family was accepted and why?
- Which family was cheapest for a given task?
- Are rejected candidates failing local validation, ONNX validation, or size constraints?

## 7) Current Working Assumption

The score plateaus previously seen with same-shape-only improvements indicate the next gains are likely in:

1. Object movement/selection solvers
2. Better shape-change models (`dynamic_bbox_crop` / object-aware transforms)
3. Marker-driven or relation-aware crop families

The priority is to convert the largest unresolved slices first, then re-run scoreplateau triage in `notebooks/06_score_plateau_triage.ipynb`.

## 8) Historical Notes

- Early versions (5–10) validated core scoring compatibility of the fixed one-hot interface and complete submission packaging.
- Mid revisions with geometric/crop/learned additions moved local candidate diversity but did not show public-score lift relative to earlier baselines.
- Solver quality tracking was improved by adding cost ranking, `reason_rejected`, and source attribution in the manifest.

