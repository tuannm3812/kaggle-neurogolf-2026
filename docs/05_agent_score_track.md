# NeuroGolf Version Track

## Run ledger

| run | manifest time | score | exported | unsolved | Δexported | recovered | dominant family | notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| local-runs:2026-06-04-0650 | 2026-06-04 12:51:59 | unknown | 268 | 132 | 0 | 0 | external_transform_library | no net coverage change |
| kaggle-runs:2026-06-04-0650 | 2026-06-04 13:20:59 | unknown | 270 | 130 | 2 | 2 | external_transform_library | +2 solved |
| kaggle-runs:2026-06-09-v9-output | 2026-06-09 10:08:22 | 0.0000 | 400 | 0 | 130 | 130 | onnx | +130 solved |
| kaggle-runs:2026-06-09-1334 | 2026-06-09 10:36:02 | unknown | 270 | 130 | -130 | 0 | onnx | -130 solved |
| kaggle-runs:2026-06-09-1340-v26 | 2026-06-09 10:40:30 | unknown | 270 | 130 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-09-v9-run | 2026-06-09 10:56:11 | unknown | 400 | 0 | 130 | 130 | onnx | +130 solved |
| kaggle-runs:2026-06-09-v10-scorer-gate | 2026-06-09 12:31:00 | unknown | 370 | 30 | -30 | 0 | onnx | -30 solved |
| kaggle-runs:2026-06-09-v10-check | 2026-06-09 15:44:12 | unknown | 370 | 30 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-09-v12-scorer-venv | 2026-06-09 16:00:49 | unknown | 0 | 400 | -370 | 0 | none | -370 solved |
| kaggle-runs:2026-06-09-v13-runtime-risk | 2026-06-09 16:04:51 | unknown | 371 | 29 | 371 | 371 | onnx | +371 solved |
| kaggle-runs:2026-06-09-v14-v9-export-filter | 2026-06-10 06:41:45 | 3317.3900 | 0 | 400 | -371 | 0 | none | -371 solved |
| kaggle-runs:2026-06-09-v16-v9-allowlist | 2026-06-10 07:54:10 | 3317.3900 | 371 | 29 | 371 | 371 | onnx | +371 solved |
| kaggle-runs:2026-06-09-v15-v9-allowlist | 2026-06-10 07:54:20 | 3317.3900 | 371 | 29 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-10-v17-allowlist-fix | 2026-06-10 08:00:58 | 3329.1800 | 21 | 379 | -350 | 0 | onnx | -350 solved |
| kaggle-runs:2026-06-10-v18-embedded-allowlist | 2026-06-10 08:03:56 | 3329.1800 | 363 | 37 | 342 | 342 | onnx | +342 solved |
| kaggle-runs:2026-06-10-v19-export-fallback | 2026-06-10 12:22:51 | 3590.2100 | 365 | 35 | 2 | 2 | onnx | +2 solved |
| kaggle-runs:2026-06-10-v20-partial-bg-conv | 2026-06-10 13:57:41 | 3590.2100 | 368 | 32 | 3 | 3 | onnx | +3 solved |
| kaggle-runs:2026-06-10-v21-score-opt-partial-bg | 2026-06-10 15:57:24 | 3590.2100 | 367 | 33 | -1 | 0 | onnx | -1 solved |
| kaggle-runs:2026-06-10-v22-check | 2026-06-10 18:57:57 | unknown | 367 | 33 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-10-v23-wave2-reexport | 2026-06-10 20:07:34 | unknown | 397 | 3 | 30 | 30 | onnx | +30 solved |
| kaggle-runs:2026-06-10-v24-wave3-runtime-risk | 2026-06-10 22:03:34 | 3590.2100 | 397 | 3 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-10-v25-wave4-expensive-learned-conv | 2026-06-11 04:46:36 | unknown | 397 | 3 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-11-v26-blended-precedence-task101 | 2026-06-11 06:54:22 | unknown | 376 | 24 | -21 | 2 | onnx | -21 solved |
| kaggle-runs:2026-06-11-v27-library-fallback | 2026-06-11 08:08:16 | unknown | 399 | 1 | 23 | 23 | onnx | +23 solved |
| kaggle-runs:2026-06-18-v30 | 2026-06-19 07:42:50 | 3590.2100 | 399 | 1 | 0 | 0 | onnx | no net coverage change |
| kaggle-runs:2026-06-19-v31 | 2026-06-19 11:14:03 | unknown | 367 | 33 | -32 | 0 | onnx | -32 solved |
| kaggle-runs:2026-06-19-v32 | 2026-06-19 13:17:53 | unknown | 397 | 3 | 30 | 30 | onnx | +30 solved |
| kaggle-runs:2026-06-19-v33 | 2026-06-20 07:06:11 | unknown | 397 | 3 | 0 | 0 | onnx | no net coverage change |

## Keep this
- Keep: `kaggle-runs:2026-06-04-0650` improved solved coverage by 2 tasks.
- Keep: `kaggle-runs:2026-06-09-v9-output` improved solved coverage by 130 tasks.
- Keep: `kaggle-runs:2026-06-09-v9-run` improved solved coverage by 130 tasks.
- Keep: `kaggle-runs:2026-06-09-v13-runtime-risk` improved solved coverage by 371 tasks.
- Keep: `kaggle-runs:2026-06-09-v16-v9-allowlist` improved solved coverage by 371 tasks.
- Keep: `kaggle-runs:2026-06-10-v18-embedded-allowlist` improved solved coverage by 342 tasks.
- Keep: `kaggle-runs:2026-06-10-v19-export-fallback` improved solved coverage by 2 tasks.
- Keep: `kaggle-runs:2026-06-10-v20-partial-bg-conv` improved solved coverage by 3 tasks.
- Keep: `kaggle-runs:2026-06-10-v23-wave2-reexport` improved solved coverage by 30 tasks.
- Keep: `kaggle-runs:2026-06-11-v27-library-fallback` improved solved coverage by 23 tasks.
- Keep: `kaggle-runs:2026-06-19-v32` improved solved coverage by 30 tasks.

## Change this
- Change: `local-runs:2026-06-04-0650` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-09-1340-v26` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-09-v10-check` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-09-v15-v9-allowlist` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-10-v22-check` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-10-v24-wave3-runtime-risk` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-10-v25-wave4-expensive-learned-conv` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-18-v30` did not improve solved coverage; validate new solver families before widening search.
- Change: `kaggle-runs:2026-06-19-v33` did not improve solved coverage; validate new solver families before widening search.

## Recommended next step
- Promote the highest-yield family from the positive delta row, then rerun only that notebook change.
- If `dominant_reason` remains `external_missing`, prioritize transform-library mount and candidate discovery checks.
