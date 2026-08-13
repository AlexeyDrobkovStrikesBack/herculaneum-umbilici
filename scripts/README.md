# Scripts

These are the working scripts behind the numbers in the top-level README. Most
are shipped as they were run rather than rewritten for publication; the three
exceptions are named below. Read this first — there are known rough edges and we
would rather state them than have you find them.

Requires `numpy`, `Pillow`, `scipy`, and `matplotlib` for `calib_figure.py`.

## Where they look for data

Every script resolves the axis files from `UMBILICI_ROOT`, defaulting to the
repository root, and the annotation tree from `UMBILICI_TREE`, defaulting to the
same place:

```bash
python3 scripts/axis_stats.py                       # works on a fresh clone
python3 scripts/count_wins.py                       # needs qc/validation_raw.json

export UMBILICI_TREE=/path/to/annotation/tree       # for the rest
python3 scripts/validate_axes.py PHerc0191
```

The annotation tree is **not** fully contained in this repository:

| path | what | in this repo? |
|---|---|---|
| `PHercNNNN_umbilicus.json` | the finalized axes | yes |
| `PHercNNNN/` | per-scroll L3 slice PNGs, `meta.json`, `auto_centers.json` | no — derived from the public volumes |
| `results/` | annotator output, `игнор.json` ignore list | no |
| `ref_sean/` | sean's three published umbilici, for calibration | no — fetch from the open bucket |
| `qc/` | gate reports and json written by these scripts | no (it is gitignored); the published panels are in `panels/` |

**Two scripts run on a fresh clone with nothing else**: `axis_stats.py`
(everything about the polylines themselves) and `count_wins.py` (everything about
the shifted-axis control, given the raw json that `validate_axes.py` writes).
The rest need the slice PNGs. The axes and the panels are self-contained; the
scripts are here so the method is inspectable and so the numbers can be
recomputed by anyone who rebuilds that tree. Ask and we will help you reproduce it.

## What each one does

- `axis_stats.py` — **new for this release.** Geometry of the ten shipped axes:
  max deviation from vertical, the deviation an optimally placed straight stick
  would still have, lateral sweep, kink (as published and at a common 480-voxel
  z-step), largest interior gap, and — with the annotation tree — bare edges and
  tissue-band coverage. Every definition is in the docstring.
- `count_wins.py` — **new for this release.** Counts and tests the shifted-axis
  control from `qc/validation_raw.json`. Prints both displacement magnitudes
  (300 and 150 voxels), the pooled slice-level binomial (labelled as
  pseudoreplicated), the scroll-level sign test, the per-scroll table and the
  Bonferroni threshold. The previous release quoted a p-value produced by a
  script that did not ship; this is that script, and it also reports the control
  that came out null.
- `qc_gates.py` — the automatic smoothness and ring-symmetry gates; emits the
  candidates json. (Its docstring claims it also writes a montage png; it does
  not.)
- `finalize.py` — drops auto-suggested points that a human never confirmed and
  stamps `metadata.source_volume`. The confirmation rule is `--tol`, default 2.0
  voxels. **Known bug:** `auto_centers.json` and `meta.json` are read from the
  data root, never from `--indir`, so pointing `--indir` somewhere else silently
  disables the dropping and leaves `source_volume` empty. Run it against the
  root. It also merges the human ignore list into the same bucket as the dropped
  auto-suggestions, so its printed "auto dropped" count for PHerc0191 includes
  two slices that a human excluded.
- `validate_axes.py` — the shifted-axis control across 297 slices; writes
  `qc/validation_raw.json`. Its docstring mentions per-scroll panels and a
  `report_axes.py`; no such file ever existed — the assembler was called
  `validate_report.py` and it does not ship. `count_wins.py` replaces the part
  of it that produced published numbers. It (and `validate_bands.py`) reads the
  axes from `{root}/submission/`, a staging directory in our tree; the same
  files are byte-identical at the top level of this repository, so on a fresh
  clone either symlink `submission/` to `.` or edit that one path.
- `validate_bands.py` — the banded-energy measure used by that control; imports
  `validate_axes` for its paths. **Known bug:** it writes
  `qc/validation_bands.json` without creating `qc/` first, so create the
  directory before running it or the run is discarded at the last line.
- `calib_sean.py` — **changed for this release, and this is the one behavioural
  change we made.** It previously covered three of our ten scrolls and read them
  from `results/`, the pre-finalization annotator output; the number it produced
  therefore described polylines this package does not ship. It now runs all ten
  against the shipped files, and it creates `qc/` before writing. Its output json
  is `qc/calibration_sean.json` (renamed from a Cyrillic filename). The
  before/after values are both stated in the top-level README.
- `calib_figure.py` — **new to this release** (it existed but had not been
  shipped); draws `panels/calibration_summary.png` from that json.
- `qc_sheet.py` — the per-scroll QC sheet. Note it defaults its output directory
  to the data root, so running it as documented drops ten `qc_PHercNNNN.png`
  next to the axes; pass an explicit output directory.

## The panel producers

`calib_figure.py` (here) draws `panels/calibration_summary.png`. The other sixteen panels
are drawn by two scripts that are **not** shipped, because both need the annotation tree
to run at all and would be dead code here: `qc/ось_панель_en.py` draws the ten axis
panels from each scroll's side projections, and `qc/шаг2_код/viz_en.py` draws the six
step2 panels from the traced stacks. Ask and we will send them.

The step2 panels were re-rendered from Russian into English for this release. That
re-render was checked rather than assumed: `viz_en.py` has a `--ru` mode that renders the
original Russian strings through the same code path, and in that mode it reproduces all
six previously published panels **byte-identically**. The English panels therefore differ
from them in text only — no number, colour, threshold or layout changed. The one
substantive wording change is deliberate and is the reason for the re-render: the figures
now say *traced arcs*, never *physical sheets*, matching the caveat in the top-level
README.

Some scripts still write files with Cyrillic names into `qc/`
(`qc_gates.py` → `кандидаты_*.json`, `validate_axes.py` → `валидация_*.png`,
`ВАЛИДАЦИЯ_ОСЕЙ.md`). Those are working-tree artifacts, not published outputs.

## Language

Comments and printed strings were translated from Russian for this release.
Beyond the `UMBILICI_ROOT` / `UMBILICI_TREE` path handling above, the only
structural changes are the ones named explicitly in the list: the `calib_sean.py`
scope and output path, and the two new scripts. Everything else is literal text,
verified by a token-level diff against the originals that produced the published
numbers. One earlier version of this section claimed the path handling was the
*only* structural change; that was not accurate even then, since `calib_sean.py`
had a code token (`"наш"` → `"ours"`) that flows into an output key.
