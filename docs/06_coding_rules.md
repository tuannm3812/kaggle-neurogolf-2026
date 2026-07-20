# Coding Rules

This is the project-specific coding standard for NeuroGolf 2026. It follows
the shared baseline at `coding-standards/coding_standards.md` (sibling repo,
outside this checkout) and adds rules specific to ARC-style solver
development and Kaggle ONNX submission. Where this project intentionally
departs from the master standard, the deviation is called out explicitly
rather than left implicit.

**Deviations from the master standard:**

- Naming uses zero-padded numbers (`01_`, `02_`, …) instead of the master's
  unpadded scheme (`1_`, `2_`, …), so lexicographic and numeric sort order
  match once past `09`. See §2.
- This file is numbered last (`06_coding_rules.md`) instead of first
  (`0_coding_standards.md`) to preserve existing stable links across
  `README.md`, notebooks, and prior commits. New projects forked from the
  master should still start with `0_coding_standards.md`.
- A `kaggle/` root folder holds pushed kernel bundles (notebook copy +
  `kernel-metadata.json` per track). This is additive to the master's
  folder list, not a replacement.

## 1. Repository Scope

This repository is notebook-first. Kaggle notebooks are the executable
source of truth; `docs/` captures analysis, model results, and project
decisions in writing.

Keep the root small:

- `notebooks/` — Kaggle notebooks, the executable workflow.
- `kaggle/` — pushed kernel bundles (notebook + `kernel-metadata.json`) per
  submission track, mirroring what actually runs on Kaggle.
- `docs/` — standards, instructions, EDA notes, model/solver results,
  decisions.
- `README.md` — high-level overview and current best/active score.
- `scripts/` — small CLI helpers only (env setup, monitoring, notebook
  hygiene, agent functions), not core solver logic.
- `artifacts/` — generated run artifacts (manifests, submission packages,
  ONNX files, logs, analysis CSVs). Gitignored except where a lightweight
  file directly supports written analysis.
- `.gitignore` — all generated and local-only files, including `.kaggle/`
  credentials.

Keep local-only generated folders local-only. Commit only the artifacts
that directly document reasoning or reproducible benchmark decisions.

## 2. Artifact Naming

Use numbered, stable, **zero-padded** names so sort order stays correct
past nine entries:

- `docs/01_instructions.md`
- `docs/02_eda_insights.md`
- `docs/03_baseline_models.md`
- `docs/04_agent_workflow.md`
- `docs/05_agent_score_track.md`
- `docs/06_coding_rules.md`
- `notebooks/01_eda.ipynb`
- `notebooks/02_baseline_models.ipynb`
- `notebooks/03_solver_diagnostics.ipynb`
- `notebooks/04_solver_development.ipynb`
- `notebooks/05_simple_solver_export.ipynb`
- `notebooks/06_score_plateau_triage.ipynb`

Rules:

- Reserve a new number for a promoted, project-owned workflow — not every
  parameter tweak. Use a config cell or a version-track entry
  (`docs/05_agent_score_track.md`) for small variants instead of
  near-duplicate notebooks.
- Notebook names should describe the actual Kaggle workflow performed, not
  just a step number. Do not split model generation and submission
  packaging into separate notebooks when the competition flow is meant to
  run end-to-end.
- Kernel bundles under `kaggle/<kernel-slug>/` should mirror the notebook
  they were pushed from; keep the slug stable once a track is named.

## 3. Code Style

Follow PEP 8 for Python code:

- Use 4 spaces for indentation.
- Keep lines to 79 characters or fewer where practical (a little slack is
  fine for notebook display/print calls where wrapping hurts readability).
- Prefer list comprehensions, f-strings, and small named helper functions
  over long procedural cells.
- Add type hints to every reusable function; use `snake_case` for variables
  and functions, `UPPER_SNAKE_CASE` for constants and config fields.
- Group imports in this order:
  1. Standard library
  2. Third-party libraries
  3. Local or competition utility modules
- Separate import groups with a blank line.

Use Google-style docstrings for reusable functions when the function is not
self-explanatory:

```python
def func(x: int) -> int:
    """One-line summary.

    Args:
        x: Description.

    Returns:
        Description.
    """
```

Add short inline comments only when they explain why a decision was made.
Avoid comments that restate what the code already says.

## 4. Notebook Style

Each notebook should include:

- A short purpose statement and numbered Markdown sections at the top.
- A single configuration block near the top for tunable values (seed,
  paths, thresholds) — no magic numbers scattered through cells.
- Explicit mode flags when runtime behavior differs between analysis,
  validation, and submission (for example `EXPORT_PUBLIC_OUTPUT_FALLBACK`,
  `USE_TRANSFORM_LIBRARY`). Submission-mode cells should skip broad EDA and
  focus on load → solve/export → validate → write.
- Deterministic seeding wherever randomness is used, for reproducibility.
- Kaggle path auto-detection where practical; do not hardcode a personal
  username or local-only path.
- Concise Markdown insight cells after important plots or metrics — a
  notebook without interpretation is not done.
- Artifact-writing cells for reusable outputs such as `submission.zip`,
  manifests, CSVs, or plots.
- A closing findings/limitations/next-step cell summarizing what the run
  showed and what to try next.

Prefer readable, self-contained notebook code over imports from local
project modules. Kaggle should be able to run the notebook after attaching
only the required competition datasets and allowed model inputs.

Keep analysis prose out of code cells. Use markdown cells for
interpretation; use code cells for computation, plotting, validation, and
explicit report-asset generation.

Notebook output policy:

- Keep notebook outputs committed when executable logic is unchanged.
- Clear all outputs and execution counts before committing when you changed
  runnable code and retrained/reran on Kaggle.
- Add outputs back only after the run is intentionally reviewed and
  stabilized.

Use this helper to keep the rule consistent:

- `python3 scripts/clean_notebook_outputs.py` clears outputs only for
  notebooks with code changes versus `HEAD`.
- `python3 scripts/clean_notebook_outputs.py --all notebooks/04_solver_development.ipynb`
  clears one notebook only.
- `python3 scripts/clean_notebook_outputs.py notebooks/*.ipynb` clears
  changed notebooks across a set.

Competition notebooks should not depend on internet access during final
reruns. For runtime packages that differ from the Kaggle image, prefer
attached wheelhouse datasets when finalizing. Exploratory installs are
allowed only behind explicit configuration or in a clearly labeled
dependency setup cell.

Submission paths must stay focused on loading inputs, generating or
validating ONNX files, and writing `submission.zip`. Do not run broad EDA
inside scored submission paths.

## 5. Solver Validation and Leakage Prevention

ARC-style tasks replace the usual train/validation leakage risk with a
narrower but just-as-serious one: a solver that looks complete on paper but
was never honestly validated.

- Fit a solver's rule only from a task's own train examples. Never derive a
  rule by reading the public test *output* — that is target leakage in this
  benchmark's shape, not a legitimate solver.
- `EXPORT_PUBLIC_OUTPUT_FALLBACK` and similar fallback flags must default to
  `False`. A fallback that copies known public outputs inflates archive
  completeness without producing a generalizable, scorer-trustworthy model.
- Every exported task must pass the full pre-export validation gate (input
  contract, shape, dtype, banned ops, ONNX Runtime load, train + public-test
  inference) documented in `docs/03_baseline_models.md` before it enters
  `submission.zip`. Train-fit alone is not sufficient evidence.
- Prefer a solved-task-only archive over a complete archive padded with weak
  or invalid placeholders — this has been the win condition in every scored
  run so far (see `docs/05_agent_score_track.md`).
- When public score does not move as expected, compare manifests before
  trusting new "coverage": new internal coverage may not overlap the
  publicly scored slice.
- Never disable `VALIDATE_WITH_ONNXRUNTIME`/`ORT_AVAILABLE` in a probe or
  analysis script for speed without checking what else keys off those
  flags. `model_solves_pairs()` returns `True` unconditionally when
  validation is off, so a "probe" that disables it will report every
  candidate as solving the task regardless of correctness (found
  `2026-07-20` in `scripts/wave4_probe_externals.py`: it reported 12 false
  "cheaper local solver" improvements that a full-validation re-check
  showed were 0 real ones; a live re-run of `solve_task()` with real
  validation confirmed 0 tasks would have benefited).

## 6. Plot Style

Use Viridis as the default visual language across notebooks:

- Use `"viridis"` as the default colormap for charts and heatmaps.
- Use Viridis-derived colors for categorical or sequential accents.
- Change color palettes only when a specific chart needs clearer contrast,
  semantic coloring, or accessibility improvement.
- Keep ARC grid rendering on the canonical 0-9 ARC color palette because
  those colors are semantic puzzle tokens, not a stylistic choice.
- Keep chart titles short and analytical; avoid decorative styling.

## 7. Documentation Style

Documentation should be written for a competition reviewer or teammate who
wants the reasoning quickly:

- Use numbered sections; lead with findings and implications, evidence
  after.
- Include exact metrics when available — not vague claims.
- Timestamp any fact that can change (scores, deadlines, plateau status);
  use absolute dates (`2026-06-09`), not relative ones.
- Link notebooks and docs with relative paths.
- Keep model/solver result pages separate by family or workflow.
- Keep broad narrative in `README.md`; keep detailed evidence in focused
  `docs/` files.

Exception: `docs/05_agent_score_track.md` is machine-generated by
`neurogolf_agents.py track` (`build_track_report`). Its section headers are
owned by that function, not hand-edited — change the generator, not the
file, if the structure needs to change.

## 8. Git Hygiene

Do not commit:

- Raw Kaggle competition data.
- Local checkpoints or Kaggle working directories.
- Large cached arrays or feature tables.
- Python caches or notebook checkpoints.
- Ad hoc experiment dumps.
- Credentials, tokens, or `.env`/`kaggle.json` files — keep these under
  `.kaggle/`, which is gitignored.

Commit lightweight artifacts only when they directly support the written
analysis, such as figures used by EDA markdown and model/solver result
pages.

### 8.1 Agent commit protocol (for delegated function runs)

- Use conventional commit format: `<type>(agent/<function>): <summary>`.
- Keep function scope tight: commit only the files produced or edited by
  that agent function.
- If no durable artifact was produced, no commit is required.
- When documentation is generated (for example `report`, `compare`,
  `track`), prefer `docs/` and `artifacts/analysis/` references over code
  churn.
- For notebook edits, ensure outputs are cleaned or explicitly reviewed
  before commit.

Example mapping:

| Function | Commit scope | Example message |
| --- | --- | --- |
| `score` | usually none, optionally log snapshots | `docs(agent/score): add latest score snapshot note` |
| `report` | `docs/*_report*.md` | `docs(agent/report): archive latest score diagnostics` |
| `compare` | manifest deltas + notes | `docs(agent/compare): add run comparison delta` |
| `track` | history and tracked summary docs | `chore(agent/track): append run ledger entry` |

## 9. Commit Message Convention

Use Conventional Commits, scoped and imperative, for all non-kernel work:

```
<type>(<scope>): <imperative summary>
```

Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.

Examples:

- `feat(agent): auto-map kaggle scores in track command`
- `fix(agent): map auto-fetched Kaggle scores to run ledger`
- `docs: add agent function commit protocol`

Exception — kernel version syncs: when a commit mirrors a Kaggle kernel
push, use the established `Kaggle Notebook | <Kernel Title> | Version N`
subject instead of a conventional-commit type. This keeps the commit
searchable against the matching Kaggle kernel version. Use it only for
commits that are exactly a kernel content sync; ordinary code or doc
changes still follow the format above.

Rules:

- One coherent change per commit. Don't mix a notebook behavior change with
  an unrelated docs update unless they're genuinely the same closed change.
- Put material detail in the commit body, not just the subject: what
  changed, what was validated, what wasn't. Never claim a Kaggle run
  passed unless its status was actually checked (`kernels status` /
  `competitions submissions`).
- Don't amend or force-push shared history without explicit reason.

## 10. Pre-Commit / Pre-Push Workflow

Before staging anything:

1. Run `git status --short` and review every path — don't blind `git add -A`.
2. If notebook code changed, either rerun it on Kaggle or clear its outputs
   before committing (`scripts/clean_notebook_outputs.py`, see §4).
3. Run verification proportional to the change:
   - Script/function changes → `python3 -m py_compile <file>` or a smoke
     run of the affected function.
   - Notebook changes → confirm the notebook JSON is well-formed and the
     output-clearing rule was followed.
   - Docs-only changes → check relative links and any dates/scores cited
     against `docs/05_agent_score_track.md`.
4. Stage only the intended change; confirm no data files, credentials, or
   generated artifacts snuck in (`git diff --cached --stat`).
5. Write the commit message per §9.
6. Push without force; confirm the commit landed on the expected branch.

Before submitting a Kaggle run specifically, also see §11.

## 11. Kaggle Submission Method

Submit through a **competition-linked kernel** (notebook-first), not by
uploading a locally downloaded `submission.zip`.

Why: Kaggle re-executes the submitted notebook end-to-end against the
hidden test set, tying the leaderboard score to code Kaggle actually ran. A
`2026-06-09` manual CLI submit of a pulled kernel output failed with
`ERROR` — the archive reported `400 / 400` in its manifest, but `58` files
were scorer-incompatible (dynamic tensor shapes, ORT load failures,
unsupported ops) that only Kaggle's own execution path would have caught.
Every best-scoring run (`3068.97`, `3235.97`, and the current `3590.21`) was a notebook auto-submit.

Rules:

- Push and run the export kernel via CLI (`kernels push`), then submit the
  **notebook run output** (`competitions submit -k <slug> -f submission.zip
  -v <version>`) — never `competitions submit -f /local/path/submission.zip`.
- Treat manifest `N / N exported` as diagnostic only, not scorer-safe,
  until the pre-export validation gate (§5, `docs/03_baseline_models.md`)
  has passed.
- Kernel notebooks must stay offline-safe and self-contained per §4.
- Before submitting, confirm the kernel version pushed matches what's in
  `kaggle/<kernel-slug>/`, and record the result (version, score, date) in
  `docs/05_agent_score_track.md`.

Full CLI workflow and kernel-track table: `docs/01_instructions.md` §9.
