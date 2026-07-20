# NeuroGolf Agent Workflow

This document defines the lightweight agent stack used to run, monitor, and improve
the Kaggle score quickly.

## 1. Why This Exists

- Score plateaus can be misleading without manifest context.
- Public score improvements only come from tasks solved by actual train-fit rules, not placeholders.
- External-transform candidates are currently the largest coverage slice; we need fast checks to detect exactly where they fail and what to build next.
- Submission status (`COMPLETE` vs `ERROR`) matters as much as exported task count.

## 2. Submission Rule: Notebook-First

- **Submit the notebook run**, not a locally downloaded zip.
- After `kernels push` completes, run:
  ```bash
  kaggle competitions submit -c neurogolf-2026 \
    -k tuannm3812/neurogolf-2026-simple-logic-solver \
    -f submission.zip \
    -v <kernel-version> \
    -m "Notebook export run"
  ```
- `-f submission.zip` is the **kernel output filename**, not a local path.
- **Do not** run `competitions submit -f /path/to/submission.zip`.

Why: local zip uploads caused a `2026-06-09` `ERROR` when v9 exported scorer-incompatible models. Notebook output submit via `-k ... -f submission.zip` is the supported code-competition path.

Orchestration script:

```bash
KAGGLE_CONFIG_DIR=~/Downloads ./scripts/run_kaggle_export.sh
```

Strategy details: `docs/01_instructions.md` Section 9.

## 3. Agents Implemented in `scripts/agents/neurogolf_agents.py`

- `score`  
  fetches recent submission records for an account and competition.
- `report`  
  combines latest score + manifest diagnostics and emits a short strategy note.
- `compare`  
  diffs two manifest files to show recovered task IDs and family-level deltas.
- `track`  
  tracks multiple manifest versions into a versioned ledger and summarizes keep/change lessons.

## 4. Commit Protocol for Agent Functions

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

## 5. Current Priority From This Report

- Active leaderboard and all-time best score: `3590.21`, stable since `2026-06-10` (v23) through the latest confirmed run (`2026-06-20`, v33: `397 / 400` exported, `3` unsolved).
- The `2026-06-09` manual v9 `SubmissionStatus.ERROR` is resolved; the earlier `2561.08`/`3068.97` plateau is retired history, not the current state.
- Immediate action: pursue the wave4 cost-audit targets (`artifacts/analysis/wave4_cost_audit.md`) — raising the lowest-scoring `external_transform_library`/`transform_library_onnx` tasks is the identified next upside (`+58` to `+163` estimated public score).
- Before using v9 expansion: enforce pre-export validation gate documented in `docs/03_baseline_models.md`.

## 6. Command Examples

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

## 7. Nightly Score-Improvement Schedule

1. Push the competition export kernel (or run `./scripts/run_kaggle_export.sh`).
2. Confirm auto-submission status is `COMPLETE` via `competitions submissions`.
3. Pull kernel output for triage only; keep `simple_logic_manifest.csv` (do not re-submit the pulled zip).
4. Run `report` and archive the report.
5. If status is `ERROR`, revert archive policy and tighten pre-export validation.
6. If unresolved reasons are mostly `external_missing`, fix transform-library discovery/path mounting first.
7. Otherwise, promote one solver family into the export notebook, rerun the kernel, and compare manifests.

## 8. Lessons Rulebook (Keep vs Change)

- Keep:
  - any run with positive `Δexported` and no new top rejection failure introduced.
  - stable improvements in the same family when they continue recovering tasks already in the target slice.
- Change:
  - zero or negative coverage delta with unchanged top rejection reasons.
  - top rejection reasons stay on the same brittle class after attempted fixes.
  - no positive family delta for newly introduced families after at least two reruns.

## 9. Exit Criteria for Each Iteration

- Submission status is `COMPLETE`, not `ERROR`.
- Manifest shows non-zero task recovery when targeting expansion.
- New kernel run writes the manifest with explicit solver-source tags and rejection reasons.
- Public score improves versus previous successful submission.
