# NeuroGolf Version Track

## Run ledger

| run | manifest time | score | exported | unsolved | Δexported | recovered | dominant family | notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| kaggle-runs:2026-06-04-0650 | 2026-06-04 16:20:59 | 2561.0800 | 270 | 130 | 0 | 0 | external_transform_library | no net coverage change |

## Key version summary

### Version checkpoints

| date (UTC+?) | submission / run label | score | change vs previous | key note |
| --- | --- | ---: | ---: | --- |
| 2026-06-04 17:00:21 | kaggle-runs:2026-06-04-0650 | 2561.08 | -507.89 | latest run, no net manifest recovery |
| 2026-06-04 15:28:23 | v4 ranked crop + transform lib fixes | 3068.97 | +507.89 | best plateau regained before fallback regression |
| 2026-06-04 05:45:01 | local run: 261 external-transform candidates | 3235.97 | +2982.03 | best public score in current history |
| 2026-06-04 05:01:29 | merged external lib filename fix | 3133.57 | +2879.63 | first large jump from baseline |
| 2026-06-04 05:49:49 | simple_logic_export_v1 baseline | 253.94 | -2695.40 | reset from baseline format |

### Manifest-level changelog

- `local-runs:2026-06-04-0650`: score unknown, exported `268` (`external_missing:task005` dominant reason).
- `kaggle-runs:2026-06-04-0650`: score `2561.08`, exported `270` (`+2` vs local run, same dominant reason).
- `kaggle-runs:2026-06-04-0650` (tracked artifact row): score `2561.08`, exported `270`, no additional recovered tasks beyond local baseline.

## Change this
- Change: `kaggle-runs:2026-06-04-0650` did not improve solved coverage; validate new solver families before widening search.

## Recommended next step
- Promote the highest-yield family from the positive delta row, then rerun only that notebook change.
- If `dominant_reason` remains `external_missing`, prioritize transform-library mount and candidate discovery checks.
