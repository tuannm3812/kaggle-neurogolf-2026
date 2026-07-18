# NeuroGolf Version Track

## Run ledger

| run | manifest time | score | exported | unsolved | Δexported | recovered | dominant family | notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| manual:v9-cli-2026-06-09 | 2026-06-04 19:12:15 | ERROR | 400 | 0 | +130 | 130 | external_transform_library | manual submit rejected; 58 invalid ONNX |
| kaggle-runs:2026-06-04-0650 | 2026-06-04 16:20:59 | 2561.0800 | 270 | 130 | 0 | 0 | external_transform_library | notebook auto-submit; all unsolved external_missing |

## Key version summary

### Version checkpoints

| date | submission / run label | score | status | change vs previous | key note |
| --- | --- | ---: | --- | ---: | --- |
| 2026-06-09 03:08 | manual v9 CLI submit | — | ERROR | — | 400-file archive rejected; do not manual-submit pulled output |
| 2026-06-04 17:00:21 | kaggle-runs:2026-06-04-0650 | 2561.08 | COMPLETE | -507.89 | current active leaderboard score |
| 2026-06-04 15:28:23 | v4 ranked crop + transform lib fixes | 3068.97 | COMPLETE | +507.89 | stable plateau; recovery target |
| 2026-06-04 09:12:27 | Simple-logic solver v24 | 3068.97 | COMPLETE | 0 | same plateau |
| 2026-06-04 05:45:01 | 261 external-transform candidates | 3235.97 | COMPLETE | +2982.03 | all-time best |
| 2026-06-04 05:01:29 | merged external lib filename fix | 3133.57 | COMPLETE | +2879.63 | first large jump |
| 2026-06-04 05:49:49 | simple_logic_export_v1 baseline | 253.94 | COMPLETE | -2695.40 | format-validation baseline |

### Score bands and what they mean

| band | score | archive behavior | submission path |
| --- | ---: | --- | --- |
| Baseline | 253.94 | valid format, low coverage | notebook |
| Missing external | 2561.08 | 270 solved, 130 external_missing | notebook |
| Stable plateau | 3068.97 | validated solved-task-only | notebook |
| Peak | 3235.97 | best external-library coverage | notebook / local export |
| Rejected | ERROR | unvalidated or scorer-incompatible ONNX | manual submit (avoid) |

### Manifest-level changelog

- `manual:v9-cli-2026-06-09`: manifest `400 / 400`, submission `ERROR`; `58` tasks had dynamic shapes, ORT failures, or unsupported ops.
- `local-runs:2026-06-04-0650`: score unknown, exported `268` (`external_missing:task005` dominant reason).
- `kaggle-runs:2026-06-04-0650`: score `2561.08`, exported `270` (`+2` vs local run, same dominant reason).

## Keep this

- Keep notebook-first submission through competition-linked kernels.
- Keep solved-task-only archive policy; best scored runs never used invalid placeholders.
- Keep the `3068.97` kernel track (`neurogolf-2026-simple-logic-solver`) as the recovery baseline.

## Change this

- Change: do not manual-submit downloaded `submission.zip` files from kernel output.
- Change: v9 expansion kernel needs stricter pre-export validation before it becomes the primary submit path.
- Change: treat manifest export count as diagnostic only; win metric is `COMPLETE` submission + public score delta.

## Recommended next step

1. Re-run `tuannm3812/neurogolf-2026-simple-logic-solver` and wait for notebook auto-submit (`target >= 3068`).
2. Tighten export validation in the v9 kernel before using dual-library expansion.
3. After each kernel run: `competitions submissions` → pull manifest → `compare` → `track`.

See `docs/01_instructions.md` Section 9 for the full notebook-first submission strategy.
