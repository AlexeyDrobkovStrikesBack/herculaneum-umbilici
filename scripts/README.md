# Scripts

These are the working scripts behind the numbers in the top-level README. Most
are shipped as they were run rather than rewritten for publication; the three
exceptions are named below. Read this first — there are known rough edges and we
would rather state them than have you find them.

Requires `numpy`, `Pillow`, `scipy`, and `matplotlib` for `calib_figure.py`;
`requirements.txt` pins the versions every number here was produced or
re-verified with. The **five** that run on a fresh clone need **only `numpy` and
`scipy`** — checked by running them against a clone with nothing but those two
importable.

## Where they look for data

Every script resolves its data from `UMBILICI_ROOT`, defaulting to the
repository root. **`UMBILICI_TREE` is read by six of the thirteen** —
`axis_stats.py` (for `PHercNNNN/meta.json` and `ref_sean/`), `calib_sean.py`
(for the slice PNGs and `ref_sean/`), `calib_figure.py`, which imports both
variables from `calib_sean.py` and uses `UMBILICI_TREE` for `ref_sean/` only,
`fetch_sean.py` (it installs into `{UMBILICI_TREE}/ref_sean/`), and the
`--measure` modes of `stick_control.py` and `snapshot_recheck.py` (for the slice
PNGs). The other seven — `validate_axes.py`, `validate_bands.py`, `qc_gates.py`,
`qc_sheet.py`, `finalize.py`, `count_wins.py` and `order_stat.py` — take
**everything** from
`UMBILICI_ROOT`, tree data included: `validate_axes.py` reads
`{UMBILICI_ROOT}/PHercNNNN/meta.json` and `{UMBILICI_ROOT}/submission/`
(`validate_axes.py:164-165`), `finalize.py` reads `auto_centers.json` and
`meta.json` from the same root (`finalize.py:39,75`), `qc_sheet.py` likewise
(`qc_sheet.py:24,28`). Setting `UMBILICI_TREE` has no effect on any of those
six. A previous version of this paragraph said every script honoured it, and
the worked example it gave — `export UMBILICI_TREE=…` followed by
`validate_axes.py` — did nothing for exactly that reason. The variable was
introduced in this release; this is what it actually reaches.

```bash
# a fresh clone, nothing else (numpy + scipy):
python3 scripts/axis_stats.py        # geometry, coverage, all thirteen kink rows
python3 scripts/count_wins.py        # the shifted-axis control, qc/validation_raw.json
python3 scripts/order_stat.py        # the winding-order statistic, from the fixtures
python3 scripts/stick_control.py     # the straight-stick control
python3 scripts/snapshot_recheck.py  # the same control on the snapshot and on the final files

# with the annotation tree — the three scripts that read UMBILICI_TREE:
export UMBILICI_TREE=/path/to/annotation/tree
python3 scripts/axis_stats.py                       # adds coverage, bare edges, sean's rows
python3 scripts/calib_sean.py && python3 scripts/calib_figure.py

# everything else wants one root that holds both the axes and the tree:
export UMBILICI_ROOT=/path/to/annotation/tree
python3 scripts/validate_axes.py PHerc0191
```

The annotation tree is **not** fully contained in this repository:

| path | what | in this repo? |
|---|---|---|
| `PHercNNNN_umbilicus.json` | the finalized axes | yes |
| `PHercNNNN/meta.json` | source volume, level-3 frame, tissue band, slice list | **yes** — 25 KB in total, shipped verbatim so the coverage and bare-edge numbers recompute here |
| `PHercNNNN/z*.png`, `auto_centers.json` | per-scroll L3 slice PNGs and the detector's suggestions | no — derived from the public volumes |
| `results/` | annotator output, `игнор.json` ignore list | no |
| `ref_sean/` | sean's three published umbilici, for calibration | no — and **not on any public URL we could find**; see `fetch_sean.py`. Their sha256 and derived values ship in `qc/sean_reference.json` |
| `qc/` | gate reports and json written by these scripts | no (it is gitignored); the published panels are in `panels/` |

**Five scripts run on a fresh clone with nothing else**: `axis_stats.py`
(everything about the ten polylines, the coverage columns, and all thirteen
smoothness rows — sean's three from the shipped digest, marked as such),
`count_wins.py` (the shifted-axis control from the raw json that
`validate_axes.py` writes, which ships), `order_stat.py` (the winding-order
statistic from the shipped fixtures), `stick_control.py` (the straight-stick
control) and `snapshot_recheck.py` (the shifted-axis control on both the
snapshot and the final files). `fetch_sean.py` needs no third-party package at
all. The rest need the slice PNGs. The axes and the panels are self-contained; the
scripts are here so the method is inspectable and so the numbers can be
recomputed by anyone who rebuilds that tree. Ask and we will help you reproduce it.

## What each one does

- `axis_stats.py` — **new for this release.** Geometry of the ten shipped axes:
  max deviation from vertical, the deviation an optimally placed straight stick
  would still have, lateral sweep, largest interior gap with its two z values,
  and — with the annotation tree — bare edges, per-scroll tissue-band coverage
  and the aggregate coverage in all three definitions (z-weighted, unweighted
  mean, median). Then a smoothness table: kink as published, kink after thinning
  towards a 480-voxel step, and kink over only those triples whose two chords
  are both within ±20% of 480 — with the realized median z-spacing printed next
  to each, because kink grows with chord length and is meaningless without it.
  The thinning only drops points, so it normalises a dense polyline and leaves a
  sparse one where it was; the third column is the genuinely spacing-matched one
  and it is blank where a polyline has no 480-voxel spacing anywhere in it.
  Every definition is in the docstring.
- `count_wins.py` — **new for this release.** Counts and tests the shifted-axis
  control from `qc/validation_raw.json`. Prints both displacement magnitudes
  (300 and 150 voxels), the pooled slice-level binomial (labelled as
  pseudoreplicated), the scroll-level sign test, the per-scroll table with its
  median ratios and the Bonferroni threshold. The previous release quoted a
  p-value produced by a script that did not ship; this is that script, and it
  also reports the control that came out null. It drops NaN ratios explicitly
  and says how many (zero on the shipped file), because a NaN would otherwise
  fail the `> 1.0` test and be counted as a loss.
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
  shipped); draws `panels/calibration_summary.png` from that json. Its right
  panel now prints the realized median z-step under every bar and no longer
  calls the thinned values "a common z-step", because the thinning reaches 480
  on sean's three axes and not on ours; the bars themselves are unchanged.
- `qc_sheet.py` — the per-scroll QC sheet. Note it defaults its output directory
  to the data root, so running it as documented drops ten `qc_PHercNNNN.png`
  next to the axes; pass an explicit output directory.
- `order_stat.py` — **new.** Recomputes the winding-order statistic of README §1
  — 0.919/0.900/0.850 against 0.826/0.738/0.782, the shared pair counts and the
  43:7 / 42:5 / 21:3 cross-tabulation — from `qc/order_fixture_PHercNNNN.npz`,
  which holds the traced arcs and the two axes' centres for the three neutral
  stacks. It does **not** run the tracer; the sign rule and the pair selection
  are reimplemented here from the producer and reproduce it exactly. Takes about
  20 seconds.
- `stick_control.py` — **new.** The control §5 reports: the annotated per-slice
  axis against a straight vertical stick, on the same 297 slices, with the
  banded-energy measure imported unchanged from `validate_axes.py`. Counts from
  the shipped `qc/stick_control_raw.json`; `--measure` regenerates that file and
  needs the slice PNGs. It prints the displacement bins, which is where the
  result is weak, and names the two slices where the stick is unmeasurable.
- `snapshot_recheck.py` — **new.** Re-runs the whole shifted-axis control on the
  final shipped files and prints it beside the published snapshot run, so the
  one staleness this package discloses is a measured quantity. The counting is
  `count_wins.block`, imported rather than reimplemented. Ships its raw output
  as `qc/validation_final_raw.json`; `--measure` regenerates it from the slice
  PNGs.
- `fetch_sean.py` — **new.** Installs and verifies sean's three reference
  umbilici against the sha256 in `qc/sean_reference.json`, and states where they
  actually came from. It refuses to install a file whose hash does not match.

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

`calibration_summary.png` was re-rendered once more after that, to relabel its
right-hand panel (see `calib_figure.py` above). Same check: the shipped script
first reproduced the previously published panel byte-identically, so the only
difference in the current file is the label text and the per-bar step
annotation. The bar values did not move.

Some scripts still write files with Cyrillic names into `qc/`
(`qc_gates.py` → `кандидаты_*.json`, `validate_axes.py` → `валидация_*.png`,
`ВАЛИДАЦИЯ_ОСЕЙ.md`). Those are working-tree artifacts, not published outputs.

## Language

Comments and printed strings were translated from Russian for this release.
Beyond the `UMBILICI_ROOT` / `UMBILICI_TREE` path handling above, the only
structural changes are the ones named explicitly in the list: the `calib_sean.py`
scope and output path, the two new scripts, and — added after the second review —
the extra columns in `axis_stats.py`, the median-ratio column and NaN guard in
`count_wins.py`, and the relabelled right-hand panel in `calib_figure.py`. Those
three were each run before and after the change against the same data: no
previously printed value moved. A third pass added four scripts and changed one:
`axis_stats.py` gained the `qc/sean_reference.json` fallback and verification for
sean's three rows, which was run before and after against the same data with
every measured value identical and only a provenance note added to those three
lines. Everything else is literal text,
verified by a token-level diff against the originals that produced the published
numbers. One earlier version of this section claimed the path handling was the
*only* structural change; that was not accurate even then, since `calib_sean.py`
had a code token (`"наш"` → `"ours"`) that flows into an output key.
