# Coding Rules

## 1. Notebook Style

- Use a plain title as the first notebook heading.
- Use simple numeric prefixes for ordered project artifacts, such as `1_eda.ipynb` and `2_eda_insights.md`; do not use zero-padded prefixes such as `01_`.
- Group notebooks into a small number of numbered top-level chapters, such as `# 1. Setup and Data Loading`.
- Use numbered subheadings inside each chapter, such as `## 1.1 Setup` and `## 1.2 Data Discovery`.
- Avoid standalone heading-only Markdown cells. Each heading cell should include a short explanation of why the section exists.
- Add concise Markdown or generated Markdown insight blocks after analytical code cells.
- Clear notebook outputs and execution counts only when notebook code changes. Do not clear outputs for documentation-only, review-only, or insight-summary changes.

## 2. Visualization Style

- Use `viridis` for charts and continuous visual summaries.
- Keep ARC grid rendering on the canonical 0-9 ARC color palette because those colors are semantic puzzle tokens.
- Prefer clear axis labels and professional chart titles over decorative styling.

## 3. Kaggle Runtime Assumptions

- Notebooks are expected to run on Kaggle.
- Do not add local dependency installation cells unless a notebook explicitly needs a non-standard package.
- For ONNX baseline notebooks, use the official starter-notebook Kaggle pins: `numpy==2.4.4`, `onnx==1.21.0`, `onnxruntime==1.24.4`, and `onnx-tool==1.0.1`.
- Discover competition inputs from `/kaggle/input` rather than hard-coding a single dataset folder name.
