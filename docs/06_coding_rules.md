# Coding Rules

## 1. Repository Scope

This repository is intentionally notebook-first. Kaggle notebooks are the executable source of truth, while `docs/` captures analysis, model results, and project decisions.

Keep the root small:

- `notebooks/` for Kaggle notebooks.
- `docs/` for reports, results, and supporting EDA artifacts.
- `README.md` for the high-level project overview.
- `artifacts/` for generated run artifacts (manifests, submission packages, ONNX files, logs), kept in `.gitignore`.
- `.gitignore` for all generated and local-only files.
- `scripts/` for repo maintenance helpers.

Keep local-only generated folders local-only. Commit only the artifacts that directly document reasoning or reproducible benchmark decisions.

## 2. Artifact Naming

Use numbered, stable names without zero padding:

- `docs/01_instructions.md`
- `docs/02_eda_insights.md`
- `docs/03_baseline_models.md`
- `notebooks/01_eda.ipynb`
- `notebooks/02_baseline_models.ipynb`
- `notebooks/03_solver_diagnostics.ipynb`
- `notebooks/04_solver_development.ipynb`
- `notebooks/05_simple_solver_export.ipynb`
- `notebooks/06_score_plateau_triage.ipynb`

Notebook names should describe the actual Kaggle workflow. Do not split model generation and submission packaging into separate notebooks when the competition flow is meant to run end-to-end.

## 3. Code Style

Follow PEP 8 for Python code:

- Use 4 spaces for indentation.
- Keep lines to 79 characters or fewer where practical.
- Prefer list comprehensions, f-strings, and small utility functions when they improve readability.
- Add type hints for functions when the type is clear.
- Group imports in this order:
  1. Standard library
  2. Third-party libraries
  3. Local or competition utility modules
- Separate import groups with a blank line.

Use Google-style docstrings for reusable functions when the function is not self-explanatory:

```python
def func(x: int) -> int:
    """One-line summary.

    Args:
        x: Description.

    Returns:
        Description.
    """
```

Add short inline comments only when they explain why a decision was made. Avoid comments that restate what the code already says.

## 4. Notebook Style

Each notebook should include:

- a short purpose statement at the top;
- a clear configuration section near the top for tunable values;
- explicit mode flags when runtime behavior differs between analysis, validation, and submission;
- Kaggle path auto-detection where practical;
- concise Markdown insight cells after important plots or metrics;
- artifact-writing cells for reusable outputs such as `submission.zip`, manifests, CSVs, or plots.

Prefer readable, self-contained notebook code over imports from local project modules. Kaggle should be able to run the notebook after attaching only the required competition datasets and allowed model inputs.

Keep analysis prose out of code cells. Use markdown cells for interpretation; use code cells for computation, plotting, validation, and explicit report-asset generation.

Notebook output policy:

- Keep notebook outputs committed when executable logic is unchanged.
- Clear all outputs and execution counts before committing when you changed runnable code and retrained/reran on Kaggle.
- Add outputs back only after the run is intentionally reviewed and stabilized.

Use this helper to keep the rule consistent:

- `python3 scripts/clean_notebook_outputs.py` clears outputs only for notebooks with code changes versus `HEAD`.
- `python3 scripts/clean_notebook_outputs.py --all notebooks/04_solver_development.ipynb` clears one notebook only.
- `python3 scripts/clean_notebook_outputs.py notebooks/*.ipynb` clears changed notebooks across a set.

Competition notebooks should not depend on internet access during final reruns. For runtime packages that differ from the Kaggle image, prefer attached wheelhouse datasets when finalizing. Exploratory installs are allowed only behind explicit configuration or in a clearly labeled dependency setup cell.

Submission paths must stay focused on loading inputs, generating or validating ONNX files, and writing `submission.zip`. Do not run broad EDA inside scored submission paths.

## 5. Plot Style

Use Viridis as the default visual language across notebooks:

- Use `"viridis"` as the default colormap for charts and heatmaps.
- Use Viridis-derived colors for categorical or sequential accents.
- Change color palettes only when a specific chart needs clearer contrast, semantic coloring, or accessibility improvement.
- Keep ARC grid rendering on the canonical 0-9 ARC color palette because those colors are semantic puzzle tokens.
- Keep chart titles short and analytical; avoid decorative styling.

## 6. Documentation Style

Documentation should be written for a competition reviewer or teammate who wants the reasoning quickly:

- Use numbered sections.
- Lead with findings and implications.
- Include exact metrics when available.
- Link notebooks and docs with relative paths.
- Keep model result pages separate by model family or workflow.
- Keep broad narrative in `README.md`; keep detailed evidence in focused docs.

## 7. Git Hygiene

Do not commit:

- raw Kaggle competition data;
- local checkpoints;
- Kaggle working directories;
- large cached arrays or feature tables;
- Python caches or notebook checkpoints;
- ad hoc experiment dumps.

Commit lightweight artifacts only when they directly support the written analysis, such as figures used by EDA markdown and model result pages.
