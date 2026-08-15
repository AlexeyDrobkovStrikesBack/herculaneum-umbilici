# `qc/prior_umbilicus_PHerc1218_IyanDopico.json` — where this file comes from

This is **not our file.** It is redistributed here, byte for byte, so that the
comparison in README §7 runs from a bare clone instead of asking the reader to
take our word for the other side of it.

| | |
|---|---|
| author | Iyán Dopico ([@IyanDopico](https://github.com/IyanDopico)) |
| repository | <https://github.com/IyanDopico/vesuvius-sheet-tools> |
| path in that repository | `data/spiral_input_pherc1218/umbilicus.json` |
| commit that added it | [`6a831e0`](https://github.com/IyanDopico/vesuvius-sheet-tools/commit/6a831e0a9a) — *"data: publish spiral_input_pherc1218 — first spiral-fit input pack for PHerc1218"*, 2026-07-21T23:05:46Z |
| bytes | 33,718 |
| sha256 | `a153ad7a768866cb2800baed4190505dadccfb98aec2635fd8dd0510dec29560` |
| git blob sha1 | `52348c6e182f093406cea4ca17fde7c7160b3de2` |
| generator | `scripts/constraints/make_umbilicus.py` in the same repository |
| licence | MIT |

Verify it yourself without trusting this copy:

```
curl -sL https://raw.githubusercontent.com/IyanDopico/vesuvius-sheet-tools/6a831e0a9a/data/spiral_input_pherc1218/umbilicus.json | sha256sum
```

`scripts/prior_1218.py --fetch` does exactly that and refuses to proceed if the
hash differs from the one above.

## Licence notice, reproduced as MIT requires

```
MIT License

Copyright (c) 2026 Iyan Dopico

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## What it contains, as its own generator defines it

`{"control_points": [{"z", "y", "x"}, ...]}` — 365 points, float, level-0
voxels, no `metadata` block and no per-point `score`. Its z runs 32 → 23216 on
a 64-voxel grid.

Each point is the **centroid of the papyrus mask of that slice**: their
generator composites the nonzero-label mask of their own instance segmentation
at eight sampled slices per 256-slice slab, takes `ys.mean(), xs.mean()`,
smooths the series with a 5-sample running median, and multiplies by 2 to go
from their L1 working grid to level 0. Slices with fewer than 10,000 nonzero
mask pixels are skipped.

That is a different quantity from the hand-placed winding centre this package
ships, and README §7 is written around the difference rather than through it.

## The frame both files index

Their generator hard-codes `FULL_Z = 23247`, `FULL_YX = 7593` and their pack's
own `README.txt` names the volume
`20250521120456-8.640um-1.2m-116keV-masked` — the same volume id our
`PHerc1218_umbilicus.json` records in `metadata.source_volume`, and the same
level-0 grid the bucket reports (`.../0/.zarray` → `shape [23247, 7593, 7593]`).
Both files therefore index the same voxels, which is what makes §7 a distance
rather than a registration problem. `scripts/prior_1218.py` re-checks this
against the bucket with `--check-bucket` rather than assuming it.
