# NeuroGolf Version Track

## Run ledger

| run | manifest time | score | exported | unsolved | Δexported | recovered | dominant family | notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| local-runs:2026-06-04-0650 | 2026-06-04 15:51:59 | unknown | 268 | 132 | 0 | 0 | external_transform_library | no net coverage change |
| kaggle-runs:2026-06-04-0650 | 2026-06-04 16:20:59 | unknown | 270 | 130 | 2 | 2 | external_transform_library | +2 solved |

## Keep this
- Keep: `kaggle-runs:2026-06-04-0650` improved solved coverage by 2 tasks.

## Change this
- Change: `local-runs:2026-06-04-0650` did not improve solved coverage; validate new solver families before widening search.

## Recommended next step
- Promote the highest-yield family from the positive delta row, then rerun only that notebook change.
- If `dominant_reason` remains `external_missing`, prioritize transform-library mount and candidate discovery checks.
