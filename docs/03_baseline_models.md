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

No code changes in this pass changed solver behavior; this refinement pass focused on notebook clarity and output documentation.

## 3. Latest Run Summary

### 2026-07-20 (kaggle-runs:2026-07-20-1157) — current

From `artifacts/submission/kaggle-runs/2026-07-20-1157/simple_logic_manifest.csv`:

- Loaded tasks: `400`
- Exported (`onnx_exported=True`): `399`
- Unsolved (`onnx_exported=False`): `1`
- Public score: `3590.21` (`SubmissionStatus.COMPLETE`) — unchanged from v33, despite `2` more tasks solved (`task101` via `partial_background_fill_conv`, `task118` via `runtime_risk_library_onnx`); cause not yet understood
- `solver_kind` comparison against v33: `0` tasks changed family among the `397` tasks already solved in both runs — confirms `solve_task()` already selects the lowest-cost valid solver everywhere
- Wave4 "swap to a cheaper local solver" hypothesis: tested and disproven (see §10 History and `docs/06_coding_rules.md` §5). Do not re-run `wave4_probe_externals.py`'s old relaxed-validation mode; it had a bug producing false-positive "improvements" (fixed `2026-07-20`).

### 2026-06-20 (kaggle-runs:2026-06-19-v33) — history

From `artifacts/submission/kaggle-runs/2026-06-19-v33/simple_logic_manifest.csv`:

- Loaded tasks: `400`
- Exported (`onnx_exported=True`): `397`
- Unsolved (`onnx_exported=False`): `3`
- Public score: `3590.21` (`SubmissionStatus.COMPLETE`), stable across v23-v25 and v32-v33
- Solver mix: `340` external_transform_library, `35` transform_library_onnx, `19` spatial_gather, `2` learned_conv_5x5, `1` dynamic_anchor_crop

### History

### 2026-06-04 (kaggle-runs:2026-06-04-0650)

From `artifacts/submission/kaggle-runs/2026-06-04-0650/simple_logic_manifest.csv`:

- Loaded tasks: `400`
- Exported (`onnx_exported=True`): `270`
- Unsolved (`onnx_exported=False`): `130` (all `external_missing`)
- Public score: `2561.08` (`SubmissionStatus.COMPLETE`)
- Solver mix: `228` external, `37` spatial_gather, `4` global_color_map, `1` object_crop

### 2026-06-09 (manual v9 submit — failed)

From pulled v9 kernel output (`tuannm3812/neurogolf-2026-simple-logic-solver-export-v9`):

- Manifest rows: `400 / 400 exported`
- ONNX files in archive: `400`
- Public score: none (`SubmissionStatus.ERROR`)
- Root cause: `58` tasks had scorer-incompatible ONNX (dynamic shapes, ORT load failures, unsupported ops)
- Lesson: manifest export count ≠ scorer-safe archive; never manual-submit unfiltered kernel output

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

## 7. Current Solver Families in the Notebook

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

The score plateaus previously seen with same-shape-only improvements indicate the next gains are likely in:

1. Object movement/selection solvers
2. Better shape-change models (`dynamic_bbox_crop` / object-aware transforms)
3. Marker-driven or relation-aware crop families

The priority is to convert the largest unresolved slices first, then re-run scoreplateau triage in `notebooks/06_score_plateau_triage.ipynb`.

## 10. Historical Notes

- Early versions (5–10) validated core scoring compatibility of the fixed one-hot interface and complete submission packaging.
- Mid revisions with geometric/crop/learned additions moved local candidate diversity but did not show public-score lift relative to earlier baselines.
- Solver quality tracking was improved by adding cost ranking, `reason_rejected`, and source attribution in the manifest.
- The `2026-06-09` v9 manual submit confirmed that unfiltered `400 / 400` exports can fail scorer validation even when the manifest looks complete.

