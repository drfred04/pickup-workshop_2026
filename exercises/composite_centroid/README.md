# Composite Centroid Examples

These are 2-D parts for the composite-areas centroid activity. Each one has 2–4 rectangles, 1 triangle and 1–2 circular holes. Units are mm. The origin is the bottom-left corner of the part's bounding box. Dimensions and hole centers are whole millimetres, so they can be read off the grid.

| #  | Part                     | Rect. | Triangle                | Holes | A (mm²) | X̄ (mm) | Ȳ (mm) | Teaching note |
|----|--------------------------|:-----:|-------------------------|:-----:|--------:|-------:|-------:|---------------|
| 01 | Gusseted mounting bracket | 3 | right (gusset)           | 2 |  8484.8 | 54.82 | 36.38 | baseline |
| 02 | Lifting eye plate         | 2 | isosceles (eye head)     | 1 |  5886.9 | 60.00 | 41.08 | symmetric, so X̄ comes free; hole sits at the triangle's centroid |
| 03 | Index pointer plate       | 2 | isosceles, pointing right | 2 |  5146.5 | 56.61 | 24.75 | centroid falls *inside a hole* |
| 04 | Braced I-bracket          | 4 | right (brace)            | 1 |  6136.9 | 60.52 | 56.68 | most parts; near-symmetric, so X̄ ≈ 60 is a trap |
| 05 | Latch dog plate           | 3 | scalene (claw)           | 2 |  5034.8 | 35.87 | 42.37 | centroid falls *outside the material* |
| 06 | Shed end-wall panel (scale model) | 3 | scalene, off-center apex (gable) | 2 | 12046.5 | 81.46 | 41.49 | largest; triangle centroid not on a grid line |

## Files (NN = 01…06)

- `geometry_NN.json`: the part definitions. Each file is the single source of truth for its example. Each hole can take an optional `callout_deg` to set where its diameter label sits. An optional `centroid_label_offset` places the "C" label on the solution figure.
- `composite_object_NN.png`: the student figure, with no centroid shown.
- `composite_object_NN_solution.png`: the same figure with the centroid marked.
- `composite_centroid.py`: runs every `geometry_*.json`. For each one it:
  - checks the geometry (no overlapping solids, one connected piece, holes fully inside the material)
  - prints the composite table
  - cross-checks the result by rasterizing the shape
  - draws both figures

Run from the repo root: `venv/bin/python exercises/composite_centroid/composite_centroid.py`
