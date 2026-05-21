# EDA and Solver Diagnostics Insights

## 1. Data Health

- Kaggle input discovery is healthy: `800` JSON files discovered and `400` normalized tasks loaded.
- Expected task coverage is complete: `task001` through `task400` are present.
- All loaded tasks include test outputs in the current public benchmark files.

## 2. Dataset Shape

- The dataset is low-shot: median train examples per task is `3`, with a range from `2` to `10`.
- `386` tasks have one test case, while `14` tasks have multiple test cases.
- Shape-changing tasks are large enough to deserve a first-class solver track: `138 / 400` tasks change shape in train pairs.
- Shape categories:
  - `262` same-area tasks
  - `97` strong compression tasks
  - `26` strong expansion tasks
  - `10` mild expansion tasks
  - `5` mild compression tasks

## 3. Color Behavior

- Color `0` dominates train inputs and outputs, so background handling should be treated as a core primitive.
- Palette relation across tasks:
  - `176` same-palette tasks
  - `91` removes-color tasks
  - `86` introduces-color tasks
  - `47` introduces-and-removes-color tasks
- Same-palette tasks are likely driven more by geometry, object movement, or selection than by color invention.
- Introduces-color tasks are good candidates for marking, completion, fill, or derived-label logic.
- Removes-color tasks often indicate filtering, extraction, masking, or background normalization.

## 4. Solver Diagnostics

- Strict same-shape solver compatibility covers `62` tasks.
- The strongest simple same-shape signal is `background_to_single_color`, covering `50` tasks.
- Other strict same-shape signals are smaller:
  - `global_color_map`: `5`
  - `rotate_180`: `2`
  - `transpose`: `2`
  - `rotate_90`: `1`
  - `flip_horizontal`: `1`
  - `flip_vertical`: `1`
  - `identity`: `0`
- Strict shape-changing heuristics currently cover only `4` tasks:
  - `nearest_integer_scale`: `2`
  - `crop_non_background`: `1`
  - `periodic_tile_from_input`: `1`

## 5. Object Complexity

- Connected-component diagnostics show a wide spread in object complexity.
- Some tasks have hundreds of tiny components, which likely need pattern, counting, grid-line, or global-logic approaches rather than simple object movement.
- High-component stress tasks include `task110`, `task205`, `task017`, `task305`, and `task074`.

## 6. Recommended Modeling Priority

Recommended next solver tracks from diagnostics:

- `148` tasks: deep dive object movement/selection
- `101` tasks: deep dive crop/extract/compress
- `62` tasks: implement simple same-shape solver
- `52` tasks: deep dive pattern/counting/global logic
- `33` tasks: deep dive expand/tile/construct
- `4` tasks: implement simple shape solver

## 7. Practical Next Step

The next modeling notebook should not start with broad neural approaches. It should implement train-fit solvers in this order:

1. Background-to-single-color and global color-map solvers.
2. Object connected-component extraction, movement, and selection.
3. Crop/extract/compress solvers.
4. Expand/tile/construct solvers.
5. Pattern/counting/global-logic diagnostics for high-component tasks.
