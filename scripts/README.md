# Scripts

These are the working scripts behind the numbers in the top-level README, shipped
as they were run rather than rewritten for publication. Read this first — there
are known rough edges and we would rather state them than have you find them.

## Where they look for data

Every script resolves its data root from `UMBILICI_ROOT`, defaulting to the
repository root:

```bash
export UMBILICI_ROOT=/path/to/this/repo
python3 scripts/validate_axes.py PHerc0191
```

They expect the working-tree layout we annotated in, which is **not** fully
contained in this repository:

| path | what | in this repo? |
|---|---|---|
| `PHercNNNN_umbilicus.json` | the finalized axes | yes |
| `PHercNNNN/` | per-scroll L3 slice PNGs used for annotation | no — derived from the public volumes |
| `submission/` | the finalized files as a staging directory | no |
| `results/` | annotator output, `игнор.json` ignore list | no |
| `ref_sean/` | sean's three published umbilici, for calibration | no — fetch from the open bucket |
| `qc/` | gate reports and QC panels written by these scripts | partly (panels are in `panels/`) |

So the scripts run end-to-end only against the annotation tree, not against a
fresh clone. The axes themselves and the panels are self-contained; the scripts
are here so the method is inspectable and so the numbers can be recomputed by
anyone who rebuilds that tree. Ask and we will help you reproduce it.

## What each one does

- `qc_gates.py` — the automatic smoothness and ring-symmetry gates; emits the
  candidates json. (Its docstring claims it also writes a montage png; it does
  not.)
- `finalize.py` — drops auto-suggested points that a human never confirmed and
  stamps `metadata.source_volume`. **Known bug:** `auto_centers.json` and
  `meta.json` are read from the data root, never from `--indir`, so pointing
  `--indir` somewhere else silently disables the dropping and leaves
  `source_volume` empty. Run it against the root.
- `validate_axes.py` — the shifted-axis control across 297 slices; writes
  `qc/validation_raw.json`. Its docstring also mentions per-scroll panels and a
  `report_axes.py`; neither ships here.
- `validate_bands.py` — the banded-energy measure used by that control; imports
  `validate_axes` for its paths.
- `calib_sean.py` — calibration of our gates against sean's three published
  umbilici. **Note:** it writes its summary json into `qc/` without creating the
  directory first, so create `qc/` before running. Verdict labels are dict keys
  in that json and are English here (`OK`, `fair`, `candidate`, `n/a`,
  `TOTAL_ours`).
- `qc_sheet.py` — the per-scroll QC sheet.

## Language

Comments and printed strings were translated from Russian for this release. The
only structural change made during translation was the `UMBILICI_ROOT` path
handling above; everything else is literal text, verified by a token-level diff
against the originals that produced the published numbers.
