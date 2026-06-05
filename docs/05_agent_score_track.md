# NeuroGolf Version Track

## How to update scores in this track

Use this flow after each Kaggle run:

1. (Optional quick check) inspect live leaderboard run history:

```bash
python3 scripts/agents/neurogolf_agents.py score --competition neurogolf-2026 --account tuannm3812
```

2. Refresh local run tracking with auto score matching:

```bash
python3 scripts/agents/neurogolf_agents.py track \
  --auto-score \
  --account tuannm3812 \
  --history artifacts/analysis/neurogolf_run_history.csv \
  --output docs/05_agent_score_track.md \
  artifacts/submission/kaggle-runs
```

3. If `--auto-score` misses a run score (rare in burst submissions), add an override row in `artifacts/analysis/score_by_run.csv`:

```csv
run_label,public_score
kaggle-runs:2026-06-04-0650,2561.08
```

Then rerun `track` with `--score-log artifacts/analysis/score_by_run.csv`.

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
