# Scripts

These are the working scripts behind the numbers in the top-level README. Most
are shipped as they were run rather than rewritten for publication; the three
exceptions are named below. Read this first — there are known rough edges and we
would rather state them than have you find them.

Requires `numpy`, `Pillow`, `scipy`, and `matplotlib` for the three figure
scripts (`calib_figure.py`, `stat_figures.py`, `prior_1218.py --figure`);
`requirements.txt` pins the
versions every number here was produced or re-verified with. The **seven** that run
on a fresh clone need **only `numpy` and `scipy`** — `axis_stats.py`,
`count_wins.py`, `order_stat.py`, `stick_control.py`, `snapshot_recheck.py`,
`axis_benefit.py` and `prior_1218.py` (which needs `numpy` alone unless you pass
`--figure`) — checked by running them
against a clone with nothing but those two importable, most recently on
2026-08-15. `stat_figures.py` is an
eighth that runs on a fresh clone and needs **`matplotlib` as well**, and
nothing beyond it. `pitch_table.py` and `fetch_sean.py` run on a fresh clone
needing neither.

## Where they look for data

Every script resolves its data from `UMBILICI_ROOT`, defaulting to the
repository root. **`UMBILICI_TREE` is read by six of the eighteen** —
`axis_stats.py` (for `PHercNNNN/meta.json` and `ref_sean/`), `calib_sean.py`
(for the slice PNGs and `ref_sean/`), `calib_figure.py`, which imports both
variables from `calib_sean.py` and uses `UMBILICI_TREE` for `ref_sean/` only,
`fetch_sean.py` (it installs into `{UMBILICI_TREE}/ref_sean/`), and the
`--measure` modes of `stick_control.py` and `snapshot_recheck.py` (for the slice
PNGs). The other twelve — `validate_axes.py`, `validate_bands.py`, `qc_gates.py`,
`qc_sheet.py`, `finalize.py`, `count_wins.py`, `order_stat.py`,
`pitch_table.py`, `axis_benefit.py`, `prior_1218.py`, `stamp_frame.py` and
`stat_figures.py` — take **everything** from
`UMBILICI_ROOT`, tree data included: `validate_axes.py` reads
`{UMBILICI_ROOT}/PHercNNNN/meta.json` and `{UMBILICI_ROOT}/submission/`
(`validate_axes.py:164-165`), `finalize.py` reads `auto_centers.json` and
`meta.json` from the same root (`finalize.py:39,75`), `qc_sheet.py` likewise
(`qc_sheet.py:24,28`). Setting `UMBILICI_TREE` has no effect on any of those
ten (an earlier version of this paragraph said six, and listed seven). A previous version of this paragraph said every script honoured it, and
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
python3 scripts/pitch_table.py        # the five-spot winding pitch, voxel-corrected
python3 scripts/axis_benefit.py      # the pre-registered axis-benefit run of README section 6
# the same fresh clone, plus matplotlib:
python3 scripts/stat_figures.py      # the four statistics panels of README 6, 5, 2, 1
python3 scripts/prior_1218.py --figure  # README section 7 and its panel

# these reach the public bucket every time and do not run offline:
python3 scripts/stamp_frame.py --check   # the five frame keys of README section 8
python3 scripts/prior_1218.py --check-bucket --measure-centroid

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

**Seven scripts run on a fresh clone with nothing else**: `axis_stats.py`
(everything about the ten polylines, the coverage columns, and all thirteen
smoothness rows — sean's three from the shipped digest, marked as such),
`count_wins.py` (the shifted-axis control from the raw json that
`validate_axes.py` writes, which ships), `order_stat.py` (the winding-order
statistic from the shipped fixtures), `stick_control.py` (the straight-stick
control), `snapshot_recheck.py` (the shifted-axis control on both the
snapshot and the final files), `axis_benefit.py` (the pre-registered
axis-benefit run, from the per-slice results in `axis_benefit/`) and
`prior_1218.py` (README section 7, on numpy alone unless `--figure` is passed).
An **eighth**,
`stat_figures.py`, also runs on a fresh clone and needs `matplotlib` on top of
those two — verified on 2026-08-14 by cloning this repository to an empty
directory and regenerating all four of its panels there, byte-identically, with
only numpy, scipy and matplotlib installed, and re-verified on 2026-08-15
together with `prior_1218.py --figure`, whose panel came back byte-identical on
the same clone.
`fetch_sean.py` and `pitch_table.py` need no third-party package at all. The rest need the slice PNGs. The axes and the panels are self-contained; the
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
- `prior_1218.py` — **new on 2026-08-15.** README section 7: our PHerc1218 axis
  against Iyán Dopico's prior annotation, the only external check in this
  package. Prints the shared frame, the overlap, the distance distribution in
  voxels and millimetres, the same distance at our own hand-placed nodes only,
  the mean offset and the residual after removing it, and the verdict against
  the bands fixed in `qc/PRIOR1218_PREREGISTRATION.md` before it first ran.
  `--figure` draws `panels/prior_1218_agreement.png` and prints every number on
  it. Four optional legs leave the clone: `--fetch` re-downloads the prior file
  and refuses to install a hash mismatch; `--check-bucket` re-reads the level-0
  shape and `samplePixelSize`; `--villa DIR` redoes the interpolation through
  villa's own `json_umbilicus_z_to_yx` instead of `np.interp` (it agrees to
  0.0000 voxels); `--measure-centroid` re-streams 48 MB of level 5 to rebuild
  `qc/prior_1218_centroid_raw.json`. Rough edge: the centroid reader handles
  only raw uint8 C-order zarr and says so by refusing anything else — it is a
  minimal reader for one known store, not a zarr library.
- `stamp_frame.py` — **new on 2026-08-15.** Stamps and verifies the five frame
  keys of PR villa#1454 (README section 8). `--check` writes nothing and prints,
  per scroll, the voxel size from the volume id beside the one from the bucket's
  `metadata.json`, the level-0 shape, whether the control points are inside it,
  whether it matches that scroll's own `meta.json` `shape_L0`, and whether the
  file is already stamped and agrees. `--write` restamps and prints the md5
  before and after each file. It always goes to the network: no value is ever
  taken from the file being checked. Rough edge: it does not create a backup —
  the guarantee that it only appends the five keys rests on `json.dump(indent=1)`
  round-tripping these files byte-for-byte, which `--check` on an unstamped file
  demonstrates and `git diff` confirms.
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
  20 seconds. Since 2026-08-15 it also prints, from the same fixtures, how far
  apart the two axes are on each stack — the median §1 quotes (13.30 / 13.44 /
  6.75 mm) and the value at the stack's middle height (16.71 / 16.09 / 9.16 mm),
  which is the height the `centre_in_core_*.png` panels are drawn at. That is
  the only change to the file; the order statistic itself is untouched and was
  re-run to confirm it.
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
- `pitch_table.py` — **new.** Prints the five-spot winding-pitch table of the
  README caveats from `qc/winding_map_metrics.json`, applying the per-scroll
  voxel correction the demo pipeline missed. Standard library only.
- `axis_benefit.py` — **new.** Every statistic in README section 6, recomputed
  from the ten `axis_benefit/prereg_PHercNNNN.json`: the per-scroll table, the
  primary Wilcoxon over the ten scroll means, both stick baselines, the
  worst-case exclusion check, the displaced-axis control and the 3.63 mm
  sensitivity floor (1.81 mm before the 2026-08-19 re-measurement; see README
  section 6.4), how far the stick actually sits from the annotated axis,
  villa's R̄, and the three post-hoc PHerc0813 variants with the distances
  between the three placements. It also re-derives the 300 slice indices from
  the shipped umbilicus files and checks the run used exactly those, so the
  sampling rule is verifiable rather than asserted. It does **not** measure
  anything — the measurement is `axis_benefit/measure/`, which needs the public
  volumes and villa's spiral code; see README section 6.9. About 5 seconds.
- `stat_figures.py` — **new on 2026-08-14.** The four statistics panels of
  README sections 6, 5, 2 and 1: `panels/prereg_axis_benefit.png`,
  `stick_control.png`, `shifted_axis_controls.png` and `frozen_axis.png`.
  Sections 5 and 6 had no figure of any kind before this; sections 2 and 1 had
  none for the control that failed or for the frozen-axis comparison. It measures
  nothing and reads only files that ship. Where a quantity already has a
  producer it **imports that producer's counting** rather than writing a second
  copy — `axis_benefit.per_scroll` / `control_table` / `stick_distances`,
  `count_wins.tally`, `stick_control.tally` / `dose_bins`,
  `order_stat.radial_sign` — so a panel cannot drift away from the table it
  illustrates, and it **prints every number it draws** so the panels are
  checkable as text. The one quantity with no prior producer is section 1's
  frozen-axis scoring, which is implemented here as `frozen_table()` following
  the recipe README section 1 gives, and it reproduces that section's table
  exactly, including the 20.1% / 15.3% / 24.3% of sign decisions that change
  status and the 0.3% / 0.2% / 0.7% that disagree. Takes a little over 20 seconds,
  nearly all of it section 1. Two rates in it are drawn as stems from the 50% line
  rather than as bars from zero, because both of those axes are truncated and a
  bar growing off the left edge of a truncated axis overstates the quantity;
  every other panel starts its axis at zero.
- `fetch_sean.py` — **new.** Installs and verifies sean's three reference
  umbilici against the sha256 in `qc/sean_reference.json`, and states where they
  actually came from. It refuses to install a file whose hash does not match.

## The panel producers

`stat_figures.py` draws the four statistics panels and `prior_1218.py --figure` draws
`panels/prior_1218_agreement.png`; those five are the ones that regenerate from a bare
clone, and all five were re-checked byte-identical on a fresh clone on 2026-08-15.
**On 2026-08-20 all shipped panels except the twelve §1 order panels were
re-rendered on the densified curves** (the top-level README's Panels box lists what
changed on each): the five above regenerate from a clone and now reproduce the
shipped bytes again; `calibration_summary.png` was re-drawn from a fresh
`calib_sean.py` run on the densified curves; and the eighteen tree-drawn panels
below were re-run against the shipped axes. Three scripts changed for that
re-render, each named in the Language section at the bottom: `stat_figures.py`
(the §6 panel's bottom title is now computed instead of hardcoded — the old
string still said 1.81 mm/6.0 mm — and a `finegrid_floor()` helper recomputes
the 20 August finer-ladder floor from `axis_benefit/finegrid_2026-08-20/` so
both floors are drawn), `prior_1218.py` (the drawn yardsticks are now
recomputed at draw time via `current_yardsticks()`; the sealed verdict bands
are untouched and the panel footer names them), and, in the annotation tree,
`evidence_panels_en.py` (the atlas strings carry the current 19.8 mm and the
§3 re-run, and the stage-3 at-height separation is computed from the drawn
centres rather than read from the fixture).
`calib_figure.py` also ships and draws `panels/calibration_summary.png`, but that panel
does **not** regenerate on a clone: it reads `qc/calibration_sean.json`, which holds sean's
verbatim coordinates and is deliberately withheld by `.gitignore`, so on a clone the
script stops at its first read. The
other thirty panels are drawn by three scripts that are **not** shipped, because all
three need the annotation tree to run at all and would be dead code here: `qc/ось_панель_en.py` draws the
ten axis panels from each scroll's side projections, `qc/шаг2_код/viz_en.py` draws the six
step2 panels from the traced stacks, and `qc/эвиденс_кандидаты/код/evidence_panels_en.py`
draws the eleven added on 2026-08-14 — the ten-scroll axis atlas, the four annotation-site
panels and the six order-map / bump panels — and the three `centre_in_core_*.png` added on
2026-08-15. Ask and we will send them.

All fourteen of the last group need the tree twice over: the four annotation-site panels
read the per-scroll L3 slice PNGs and the ring detector's `кандидаты_*.json`, the atlas
reads the pre-rendered side projections, and the six order panels re-run the tracer that
`order_stat.py`'s row in the top-level README explains is not in this repository. The
`.npz` fixtures that ship are the tracer's *output*, which is enough to recompute §1's
statistic but not enough to redraw the arcs on a slice. The three `centre_in_core_*.png`
need both halves: the slice PNG for the image and the repaired tracer for the lines. What
they do **not** need the tree for is their two numbers, which they read out of the shipped
`qc/order_fixture_*.npz` and which `order_stat.py` prints.

Every one of these panels was re-rendered from Russian into English rather than edited as
pixels, and that re-render was checked rather than assumed. (The byte-equivalence
checks below were made on 2026-08-14/15 against the then-current data and
describe those renders; the 2026-08-20 re-render changed the English strings
and the stage-3 separation computation, so the `--ru` byte checks are a
property of the 15 August files, not of today's.) `viz_en.py` and
`evidence_panels_en.py` both have a `--ru` mode that renders the original Russian strings
through the same code path. In that mode `viz_en.py` reproduces all six previously
published step2 panels **byte-identically**, and `evidence_panels_en.py` reproduces all
eleven staged Russian candidates **byte-identically** (verified 2026-08-14 and again on
2026-08-15 after the stage-3 rebuild below, matplotlib 3.11.1). The English panels
therefore differ from them in text only — no number, colour, threshold or layout changed
by accident.

The three `centre_in_core_*.png` are the exception to that check and get a stricter one
instead, because they are a rebuild rather than a re-render and no Russian original of
them exists. `evidence_panels_en.py` grew two QC switches for them. `--dump` writes the
geometry it actually draws — both centres and every arc polyline — to `.npz`; the English
and Russian runs produce **md5-identical dumps** on all three scrolls. `--notext`
suppresses the only three strings drawn inside the image (the two cross labels and the
scale bar's label); with it, the 1228×1228 image area of the English and Russian renders
is **pixel-identical**, md5 for md5, on all three. Together those say what the byte check
says for the other eleven: the two languages differ in text and in nothing else.

Three differences are deliberate, and they are the reason for the re-render:

1. The figures say *traced arcs*, never *physical sheets*, matching caveat 1(a) in the
   top-level README.
2. The atlas footer carries the ring-gate calibration §3 now states (268.3 over 279
   points) instead of the withdrawn 265, and the order panels carry the sentence §1
   states about what the winding-order test does *not* show. Both are in the `EN` string
   table only, so `--ru` still reproduces the original bytes and the check stays runnable.
3. `annotation_site_PHerc0191.png` shows z = 10208 where the Russian candidate showed
   z = 8768. z = 8768 is in the annotation catalogue but is **not** a control point of the
   shipped `PHerc0191_umbilicus.json` — it is one of the nine points finalization dropped
   as an unconfirmed auto-suggestion — so the cross drawn there was the interpolated
   polyline while the panel title said "where the axis was annotated". z = 10208 is the
   nearest kept control point to mid-height. This is the one change that is not text, and
   it is a correction; `--ru` keeps the original z so the byte check still covers the
   Russian file.

**The stage-3 rebuild, 2026-08-15.** The staged Russian candidates for "the axis as the
centre of the unwrap" were rejected rather than translated, and the three
`centre_in_core_*.png` were built in their place. What was wrong with them: the two
centres were drawn in two *different* crops, so nothing in either frame marked where the
core was; and their headline, "12 segments traced around the cross against 9", was a count
produced by no shipped script and dependent on both the crop radius and the gate
thresholds — the panel was its own source. The rebuild puts both crosses on one frame at
full brightness with the arcs from each centre in two colours, and prints no count at all;
its only numbers are the axis separations, which come from the shipped fixtures. Its
slice, crop and tracing radius are module constants stated on the panel, so none of them
can be tuned per scroll. The tracer is the same repaired one the annotation-site panels
use, with the same discipline: where it does not hold a lamella the line stops and no
circle is completed.

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
previously printed value moved. A fourth pass (2026-08-20, the panel
re-render) changed two shipped scripts: `stat_figures.py` gained
`finegrid_floor()` and a computed §6-panel title (the hardcoded one had gone
stale — it still said 1.81 mm and 6.0 mm over current lines), and
`prior_1218.py` gained `current_yardsticks()` so the figure's dashed yardstick
lines are recomputed instead of typed; its sealed verdict bands (`FLOOR_MM`,
`STICK_MM`, `HEADLINE_MM`) and every printed verdict are untouched, re-run
before and after with identical output. A third pass added four scripts and changed one:
`axis_stats.py` gained the `qc/sean_reference.json` fallback and verification for
sean's three rows, which was run before and after against the same data with
every measured value identical and only a provenance note added to those three
lines. Everything else is literal text,
verified by a token-level diff against the originals that produced the published
numbers. One earlier version of this section claimed the path handling was the
*only* structural change; that was not accurate even then, since `calib_sean.py`
had a code token (`"наш"` → `"ours"`) that flows into an output key.
