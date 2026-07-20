# Baseline Models: Task, Approach, Results

This note records the current stable baseline and the notebook workflow we use for NeuroGolf 2026 submissions.

## 1. Task Contract

For each task ID `task001` through `task400`, the submission should contain one ONNX file named `taskXXX.onnx` in `submission.zip`.

Required interface (scorer compatible):

- ONNX input tensor: `float32`, shape `[1, 10, 30, 30]`
- ONNX output tensor: `float32`, shape `[1, 10, 30, 30]`
- Solver execution is done in static one-hot space
- ARC output is decoded from the first `h x w` region of the output canvas

## 2. Current Baseline Implementation

`notebooks/05_simple_solver_export.ipynb` is now the main export notebook and is organized into:

1. Input/paths/dependency setup
2. ARC grid↔one-hot tensor utilities
3. Uniform ONNX builders with static interface
4. Solver families and cost-based selection
5. Export packaging and manifest writing

## 3. Latest Run Summary

### 2026-07-20 (kaggle-runs:2026-07-20-1610) — current

From `artifacts/submission/kaggle-runs/2026-07-20-1610/simple_logic_manifest.csv`:

- Loaded tasks: `400`
- Exported (`onnx_exported=True`): `399`
- Unsolved (`onnx_exported=False`): `1` (`task115`, deliberately blocklisted for scorer runtime-risk)
- Public score: `3590.21` (`SubmissionStatus.COMPLETE`)
- This is the reverted state after the `barrier_crossing` solver regression (added, caused `3590.21 → 3579.96`, reverted same day) — see `docs/06_coding_rules.md` §5 for the full lesson before attempting a similar solver again.
- The wave4 "swap to a cheaper local solver" hypothesis is disproven (`0` of `397` tasks would benefit from swapping families); `2` newly-solved tasks (`task101`, `task118`, since reverted) did not move the public score, cause unknown.

### History

- `2026-06-04` (`2561.08`, `270/400`): first scorer-compatible solved-task-only submission.
- `2026-06-09` manual v9 CLI submit: `SubmissionStatus.ERROR` despite a `400/400` manifest — `58` tasks were scorer-incompatible (dynamic shapes, ORT load failures, unsupported ops). Lesson: manifest export count ≠ scorer-safe archive; never manual-submit unfiltered kernel output.
- `2026-06-10` to `2026-06-20` (v23-v33): score climbed to and stabilized at `3590.21` via wave-based reexports (`397/400`, solver mix dominated by `external_transform_library`/`transform_library_onnx`).
- Full run-by-run ledger: `docs/05_agent_score_track.md`.

### Score reference bands

| Score | Meaning | Archive behavior |
| ---: | --- | --- |
| `253.94` | Valid format, minimal coverage | Early baselines |
| `2561.08` | `270` validated tasks, 130 missing external | Solved-only, safe (history) |
| `2949–3068` | Transform library mounted, validated subset | Solved-only, early plateau (history) |
| `3133–3235` | Better external-library coverage | Solved-only (history) |
| `3590.21` | `399` validated tasks, `1` unsolved (wave2-4 reexports; task coverage grew, score did not) | Solved-only, current plateau |
| `ERROR` | Scorer rejected archive | Complete or unvalidated archive |

## 4. Archive Policy

Default export policy is **solved-task-only**:

- include a task in `submission.zip` only when it passes the pre-export validation gate;
- keep unsolved tasks in the manifest with `onnx_exported=False` and `reason_rejected`;
- never add invalid placeholders to reach `400 / 400` file count;
- keep `EXPORT_PUBLIC_OUTPUT_FALLBACK = False` unless running an explicit fallback experiment.

Competition-linked kernels auto-submit `/kaggle/working/submission.zip`. Pulled output is for triage and manifest comparison only.

## 5. Pre-Export Validation Gate

Reject a candidate model before writing it to the submission archive when any check fails:

| Check | Requirement |
| --- | --- |
| Input name / output name | `input` / `output` |
| Dtype | `float32` |
| Shape | exactly `[1, 10, 30, 30]` (no `0` dimensions) |
| Banned ops | none of `Loop`, `Scan`, `NonZero`, `Unique`, `Script`, `Function` |
| IR version | `<= 9` for external-library imports |
| ORT load | CPU `InferenceSession` initializes |
| Pair fit | all available train and public test pairs pass inference |
| Size | `< 1.44MB` per task file |

Record rejection in `reason_rejected` rather than silently dropping the row from the manifest.

## 6. What This Means

- The external transform library dominates solved coverage when mounted correctly.
- More exported tasks only help when every added task passes the scorer validation gate.
- Public-output fallback remains disabled by default.
- Score-relevant progress comes from validated coverage and local solver families, not archive completeness alone.

## 7. Current Solver Families in `solve_task()`

In try order (lowest-cost valid candidate wins, not first match):

- `constant`, `identity`
- `background_to_single_color`, `partial_background_fill_conv`
- `single_object_shift`, `largest_object_crop`, `ranked_component_crop`
- `global_color_map`, `geometric_color_map`, `unique_color_order`
- `spatial_gather`, `fixed_crop`, `dynamic_bbox_crop`, `dynamic_anchor_crop`
- `nearest_integer_scale`, `periodic_tile`
- `learned_conv_{1x1,3x3,5x5}` (feature-flagged via `SKIP_LEARNED_CONV`)
- `external_transform_library`, `runtime_risk_library_onnx` (mounted-dataset candidates)

## 8. Manifest and Debugging

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

## 9. Current Working Assumption

Same-shape-only improvements have plateaued; the current priority is new native solvers for the specific worst-cost tasks (not broader family sweeps). See `docs/01_instructions.md` §7 for the full, current prioritized list.

## 10. Historical Notes

- Early versions (5–10) validated core scoring compatibility of the fixed one-hot interface and complete submission packaging.
- Mid revisions with geometric/crop/learned additions moved local candidate diversity but did not show public-score lift relative to earlier baselines.
- Solver quality tracking was improved by adding cost ranking, `reason_rejected`, and source attribution in the manifest.
- The `2026-06-09` v9 manual submit confirmed that unfiltered `400 / 400` exports can fail scorer validation even when the manifest looks complete.

