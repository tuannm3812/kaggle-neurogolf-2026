# NeuroGolf Agent Workflow

This document defines the lightweight agent stack used to run, monitor, and improve
the Kaggle score quickly.

## Why this exists

- Score plateaus can be misleading without manifest context.
- Public score improvements only come from tasks solved by actual train-fit rules, not placeholders.
- External-transform candidates are currently the largest coverage slice; we need fast checks to detect exactly where they fail and what to build next.

## Agents implemented in `scripts/agents/neurogolf_agents.py`

- `score`  
  fetches recent submission records for an account and competition.
- `report`  
  combines latest score + manifest diagnostics and emits a short strategy note.
- `compare`  
  diffs two manifest files to show recovered task IDs and family-level deltas.
- `track`  
  tracks multiple manifest versions into a versioned ledger and summarizes keep/change lessons.

## Commit protocol for agent functions

Use one commit per completed function run when outputs changed:

- Commit message format: `<type>(agent/<function>): <summary>`
  - `type` follows conventional commit (`chore`, `feat`, `fix`, `docs`, `refactor`, etc.).
  - `summary` is one concise imperative phrase describing the user-visible change.
- Update any generated evidence files for that function and include the exact file list in the commit body if multiple files are changed.
- Never commit raw Kaggle artifacts, local caches, or unreviewed notebook outputs.

Function-specific reminders:

- `score`
  - No code changes expected.
  - Usually no commit unless a new automation artifact is added intentionally.
- `report`
  - Commit only report outputs (`docs/*_report*.md`, evidence notes) and minimal metadata updates.
  - Use `chore(agent/report): add latest score report`.
- `compare`
  - Commit manifest delta artifacts and rationale notes when the diff is used for planning.
  - Use `docs(agent/compare):` prefix when only docs change.
- `track`
  - Commit versioned history outputs when new run evidence is accepted.
  - Use `chore(agent/track): update run ledger`.

Notebook / experiment hygiene around any agent cycle:

1. Clean notebook outputs for changed run files using
   `python3 scripts/clean_notebook_outputs.py` unless the run is intentionally committed with reviewed outputs.
2. Stage only files changed by the agent function.
3. Review diff for scope and relevance.
4. Commit and push with a message that includes the active function name.

## Current priority from this report

As of the latest pulled run (`/private/tmp/neurogolf-kaggle-3812-latest`):

- Total tasks in manifest: `400`
- Exported: `289`
- Unsolved: `111`
- Dominant resolved family: `external_transform_library`
- Current unresolved reason pattern: `external_missing:*`

That means the immediate priority is to stabilize external model discovery and
coverage before large new solver families can move the public score.

## Command examples

- Check latest score for account `tuannm3812`:

```bash
python3 scripts/agents/neurogolf_agents.py score \
  --competition neurogolf-2026 \
  --account tuannm3812
```

- Build a combined report and write Markdown:

```bash
python3 scripts/agents/neurogolf_agents.py report \
  --competition neurogolf-2026 \
  --account tuannm3812 \
  --manifest /private/tmp/neurogolf-kaggle-3812-latest/simple_logic_manifest.csv \
  --output docs/agent_report_latest.md
```

- Track local version history and append it to `artifacts/analysis/neurogolf_run_history.csv`:

```bash
python3 scripts/agents/neurogolf_agents.py track \
  --history artifacts/analysis/neurogolf_run_history.csv \
  --output docs/05_agent_score_track.md
```

- Track selected run versions with mapped Kaggle scores:

```bash
python3 scripts/agents/neurogolf_agents.py track \
  /path/to/run-14/simple_logic_manifest.csv \
  /path/to/run-15/simple_logic_manifest.csv \
  --score-log artifacts/analysis/score_by_run.csv \
  --history artifacts/analysis/neurogolf_run_history.csv \
  --output docs/05_agent_score_track.md
```

- Track selected run versions and auto-fetch recent Kaggle scores:

```bash
python3 scripts/agents/neurogolf_agents.py track \
  /path/to/run-14/simple_logic_manifest.csv \
  /path/to/run-15/simple_logic_manifest.csv \
  --auto-score \
  --account tuannm3812 \
  --history artifacts/analysis/neurogolf_run_history.csv \
  --output docs/05_agent_score_track.md
```

When `--auto-score` is enabled, the script aligns Kaggle submission times to kaggle run timestamps and fills unknown scores automatically. Review output for any mismatch if runs were submitted in burst mode.

- Compare two manifest runs:

```bash
python3 scripts/agents/neurogolf_agents.py compare \
  --base /path/to/prev/simple_logic_manifest.csv \
  --head /path/to/new/simple_logic_manifest.csv \
  --output docs/agent_manifest_delta.md
```

## Nightly score-improvement schedule

1. Push notebook (or run automatically on Kaggle).
2. Pull kernel output and keep `simple_logic_manifest.csv`.
3. Run `report` and archive the report.
4. If unresolved reasons are mostly `external_missing`, fix transform-library
   discovery/path mounting first.
5. Otherwise, promote one solver family into notebook 5, rerun, and compare manifests.

## Lessons rulebook (keep vs change)

- Keep:
  - any run with positive `Δexported` and no new top rejection failure introduced.
  - stable improvements in the same family when they continue recovering tasks already in the target slice.
- Change:
  - zero or negative coverage delta with unchanged top rejection reasons.
  - top rejection reasons stay on the same brittle class after attempted fixes.
  - no positive family delta for newly introduced families after at least two reruns.

## Exit criteria for each iteration

- Manifest shows non-zero task recovery.
- New run writes the manifest and `submission.zip` with explicit solver-source tags.
- Public score improves versus previous successful submission.
