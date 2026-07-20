# NeuroGolf 2026

<img src="docs/assets/neurogolf-2026-header.png" alt="NeuroGolf 2026 competition banner" width="100%">

<p>
  <img alt="Kaggle" src="https://img.shields.io/badge/Kaggle-NeuroGolf_2026-20BEFF?style=flat-square&logo=kaggle&logoColor=white">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="ONNX" src="https://img.shields.io/badge/ONNX-submission-005CED?style=flat-square">
  <img alt="Score" src="https://img.shields.io/badge/public_score-3590.21-2E7D32?style=flat-square">
  <img alt="Coverage" src="https://img.shields.io/badge/tasks_solved-399%2F400-2E7D32?style=flat-square">
</p>

**A symbolic, cost-aware solver system for ARC-AGI-style grid reasoning — every answer is a compact, interpretable ONNX program, not a trained black box.**

NeuroGolf 2026 scores each submission with `max(1, 25 - ln(cost))` per task, where `cost` is derived from the ONNX graph's own parameters, memory footprint, and compute — correctness alone isn't enough, the *program itself* has to be small and simple. This repo builds 18 interpretable, rule-based solver families (color maps, object/crop logic, spatial gather, small learned convolutions, external transform-library integration) for the 400 grid-transformation tasks, validates each candidate against every training example before accepting it, and automatically keeps whichever valid solver is cheapest for each task.

## Results

| | |
|---|---|
| **Public score** | `3590.21` |
| **Tasks solved** | `399 / 400` — the 1 remaining is a deliberate exclusion (scorer runtime-risk), not a gap |
| **Solver families** | 18 interpretable rule families, tried cheapest-first, ranked by ONNX graph cost |
| **Validation** | Every exported model passes ONNX Runtime inference, a scorer-compatibility gate, and a `1.44MB` size cap before submission |

## How It Works

1. **EDA** — profile all 400 tasks (shape, palette, and object-complexity distributions) to route each toward the right solver family.
2. **Rule discovery** — for every task, try each solver family in order of cost (constant → color map → crop/object logic → small learned convolutions → external transform library), accepting a candidate only once it exactly reproduces every training example.
3. **Cost-aware export** — among all solvers that correctly solve a task, keep the cheapest one. The scorer rewards small, structurally simple graphs, not just correctness — a 233-layer convolution stack and a single gather op can both be "correct," but only one scores well.
4. **Notebook-first submission** — Kaggle re-executes the submitted notebook end-to-end against the hidden test set, so the leaderboard score is tied to code Kaggle actually ran, never a locally-assembled artifact.

## Engineering Practices

- **Live-validated, not just locally validated.** A hand-derived solver for one of the highest-cost tasks passed every local check — rule validated against training data, real ONNX Runtime inference, the full scorer-compatibility gate — and still regressed the live score (`3590.21 → 3579.96`) once submitted. Caught via a follow-up scored run and reverted the same day; the root cause (local test data not matching Kaggle's actual grading input) is now a standing rule: no new solver family is trusted until confirmed by a live run.
- **Manifest-driven debugging.** Every task's solver family, validation scope, and rejection reason is tracked in a structured manifest, so "why wasn't this task solved" is a data query, not a guess.
- **Automated score tracking.** A CLI agent (`scripts/agents/neurogolf_agents.py`) pulls Kaggle submission history, diffs manifests between runs, and maintains a running ledger of what improved the score and what didn't.

## Tech Stack

`Python` · `ONNX` / `ONNX Runtime` · `NumPy` / `Pandas` · `Matplotlib` · `Kaggle Notebooks & CLI` · rule-based / symbolic solver design

## Repository Structure

```text
notebooks/     Kaggle notebooks: EDA -> baseline -> diagnostics -> solver dev -> export -> triage
kaggle/        Pushed kernel bundles that mirror what actually runs on Kaggle
scripts/       CLI helpers: notebook hygiene, Kaggle orchestration, score-tracking agent
docs/          Standards, EDA findings, solver contract, full run history
```

Notebooks run end-to-end on Kaggle after attaching the competition dataset; no local setup required to review the logic.

## Further Reading

| Doc | Contents |
|---|---|
| [docs/01_instructions.md](docs/01_instructions.md) | Working plan, current priorities, Kaggle submission flow |
| [docs/02_eda_insights.md](docs/02_eda_insights.md) | Full EDA evidence and difficult-task gallery |
| [docs/03_baseline_models.md](docs/03_baseline_models.md) | ONNX interface contract, solver families, validation gate |
| [docs/04_agent_workflow.md](docs/04_agent_workflow.md) | Score-tracking agent usage and commit protocol |
| [docs/05_agent_score_track.md](docs/05_agent_score_track.md) | Full run-by-run score ledger |
| [docs/06_coding_rules.md](docs/06_coding_rules.md) | Coding standard and documented engineering lessons |
