# Umbilicus annotations for the 10 remaining First Letters scrolls

Manual umbilicus (winding-axis) polylines for the ten First Letters prize
scrolls that did not have one yet: PHerc 0191, 0257, 0268, 0358, 0800, 0813,
1203, 1218, 1447, 1545. File format matches sean's published umbilicus files
(integer voxel coordinates, per-point `score`, `metadata` block). Coordinates
are level-0 voxels of each scroll's masked prize volume — 9.362 µm for six
scrolls and **8.640 µm for PHerc 0268, 0800, 1218, 1447**; the exact volume
id is recorded in each file's `metadata.source_volume`.

Note on PHerc1203: the only existing 9.362 derivation in the bucket is
`20250820131727-...-masked`; all coordinates refer to it.

## Motivation

We were working on PHerc1203 for the First Letters prize and needed a winding
axis for it: every winding-number assignment, every polar unwrap and every
spiral fit we tried takes a centre per z-slice, and we had none for that scroll.
Three scrolls have a published umbilicus (sean's PHerc0125, 0211, 0826); the ten
scrolls in the prize set did not.

What we kept running into is that substituting a straight vertical line for the
axis is not a small approximation. On the ten shipped files the annotated centre
departs from a vertical line through the scroll's own mean centre by up to
**20.7 mm** (PHerc0268; second largest PHerc0800 at 19.9 mm), and the axis
sweeps **37.9 mm** laterally over the height of that scroll. At the 247–371 µm
pitch we measure at five readable spots (see caveats — those spots are locally
separated, and tightly-wound material is finer, which would make this count
larger not smaller), 20.7 mm of lateral error crosses
roughly 56 to 84 windings — far more than enough to assign a sheet to the wrong
turn at the top or bottom of a scroll. Placing the vertical optimally
instead of through the mean centre does not rescue it: the best a straight stick
can do on PHerc0268 is still 19.0 mm (`scripts/axis_stats.py`, `cheby_mm`).

So we annotated the ten by hand, in the same format sean published. We are
contributing them because a per-slice centre is an input that several tools in
this project take and that did not exist for these ten scrolls. All numbers
below are measured on real scroll data; no part of this validation uses
synthetic data or injected defects.

Downstream consumer, run rather than assumed: villa's spiral loader
`scripts/spiral/umbilicus.py` (`json_umbilicus_z_to_yx`) was run against all ten
of these files and sean's three. All thirteen parse and return a working
z → (y, x) interpolator. See "Format compatibility" below.

## Method
Manual annotation on ~31 axial slices per scroll (small web annotator with
auto-suggested centers, triplanar side views and winding-ring overlays;
khartes `exp-2025-08-01` used to cross-check ambiguous spots). Untouched
auto-suggestions were dropped at finalization — polylines interpolate
between human-confirmed points only. **The rule that implements this is a
2-voxel threshold** (`scripts/finalize.py --tol`, default 2.0): a point counts
as human-confirmed if it sits ≥2 voxels from the auto-suggestion it started
from. Two voxels at L3 is a quarter of a pixel, so we name the three published
points that sit within 10 voxels of their auto-suggestion — PHerc1447 z=11888
(3.3 vox), PHerc0257 z=15272 (6.6 vox), PHerc0813 z=3496 (9.9 vox). These are
deliberate micro-adjustments, but they are not distinguishable from a slipped
click, so we would rather list them.

## Validation

Four independent checks, and they are not equally reproducible. To be exact:

- **Check 2 (the shifted-axis control) reproduces from a fresh clone.** Its raw
  per-slice measurements ship as `qc/validation_raw.json`, and
  `scripts/count_wins.py` recomputes every count, rate, median and p-value
  quoted in §2 from that file with nothing but python, numpy and scipy.
- **Every geometry number about our own ten axes** (deviations, sweep, kink with
  the z-spacing each value was measured at, largest gap and its endpoints)
  reproduces from a fresh clone via `scripts/axis_stats.py`. Two exceptions,
  both marked in the table below: the tissue-band coverage needs each scroll's
  `meta.json` from the annotation tree, and **sean's three rows of the
  smoothness table need his three published files**, which we do not
  redistribute here — put them in `ref_sean/` from the open bucket. Without them
  the script prints our ten rows and says the comparison rows are missing.
- **Check 3 (calibration against sean)** needs the annotation tree — the
  per-slice PNGs and sean's three files from the open bucket. Script ships.
- **Check 1 (the winding-order test)** needs the annotation tree *and* code that
  is not in this repository. Every number in it, and where it came from, is
  tabulated in `STEP2_CONSISTENCY.md` §13.
- **Check 4** has no script at all and never did. It is marked below.

The table under "What is scripted" repeats this per number. There is no blanket
claim, and the previous heading — "scripts included for every number except one,
marked" — was not true.

### 1. Winding-order test, swap-controlled (the practical one)

Arcs of papyrus are traced around a fixed neutral centre (independent of either
axis under test), matched across slices geometrically, and the pairwise winding
ORDER implied by each axis is compared between neighbouring heights. On the
shipped tracing pipeline, with neutral tracing:

| scroll | manual axis | auto-centroid | shared pairs | kept only by manual : only by auto |
|---|---|---|---|---|
| PHerc0191 | 0.919 (354/385) | 0.826 (318/385) | 385 | 43 : 7 |
| PHerc0358 | 0.900 (206/229) | 0.738 (169/229) | 229 | 42 : 5 |
| PHerc1203 | 0.850 (226/266) | 0.782 (208/266) | 266 | 21 : 3 |

The pair sample is strictly identical for the two axes — same denominator in
every row — so the last column is a paired count: pairs whose order the manual
axis preserves and the centroid does not, against pairs where it is the other
way round. So 85–92% against 74–83%, and in paired counts the centroid loses
order **6.1–8.4×** more often. (The earlier text said "3–8×". That was wrong:
43/7, 42/5 and 21/3 are 6.1, 8.4 and 7.0. The 3.8 came from a different run —
the circle-replacement control, counts 19:5 on PHerc1203 — which that sentence
did not mention.)

**Swap control.** The same test re-run with the tracing itself done around the
manual axis, and again around the auto-centroid, gives nine cells. Counted
exactly: the manual axis is ahead in **six**, exactly level in **two** — both
scrolls traced around the auto-centre, PHerc0191 at 221/238 for each axis and
PHerc1203 at 223/269 for each — and **behind in one**. The one it is behind on
is PHerc0358 traced around the auto-centre, where the auto-centre keeps 131 of
143 pairs (0.916) against the manual axis's 130 (0.909). Our working document
calls that a tie and we think that is fair, but a reviewer is entitled to call
it a loss, so we print it rather than writing "never reverses", which is what
the earlier README said.

Strict absolute winding numbering is unresolvable at L3 preview resolution for
**either** axis. Under neutral tracing only 8–20 arcs per stack are even
evaluable, and of those 0–12.5% keep the same absolute number under the manual
axis against 0–22.2% under the auto-centroid. Neither axis is consistently
ahead, the counts are too small to say anything, and the metric is simply not
usable at this resolution. Stated honestly; we make no claim there. See
`panels/step2_*`.

**Two caveats we found ourselves and would rather state than have you discover:**

(a) What is matched across heights are *traced papyrus arcs*, not verified single
sheets — beyond the core our chaining can hop between neighbouring laminae, so
read the numbers as arc order, not sheet identity. We retracted the "physical
sheets" wording ourselves on 2026-08-10 and the shipped panels now say arcs.

(b) The *size* of the gap is tracing-pipeline dependent, and under an
alternative, stricter first-order chainer the sign is not stable. Swept across
that chainer's chaining tolerance — its module default is
`tol = clip(0.30·gap, 0.6, 1.2)`, hard-coded in the module. A cell is the manual
axis's preserved-pair rate minus the auto-centroid's on an identical pair
sample; the parenthesised number is that shared pair count.

| chaining tolerance | PHerc0191 | PHerc0358 | PHerc1203 |
|---|---|---|---|
| **0.30·gap, cap 1.2 (module default)** | +0.000 (12 pairs) | **−0.024 (42)** | +0.125 (32) |
| 0.40, cap 1.5 | **−0.031 (32)** | **−0.049 (41)** | +0.054 (93) |
| 0.50, cap 1.8 | +0.000 (61) | **−0.013 (77)** | +0.017 (113) |
| 0.65, cap 2.4 | +0.042 (95) | +0.012 (169) | +0.045 (111) |
| 0.80, cap 3.0 | +0.000 (95) | +0.052 (114) | +0.054 (55) |
| 1.00, cap 4.0 | +0.000 (54) | +0.014 (69) | +0.086 (35) |
| shipped pipeline (zero order) | +0.093 (385) | +0.162 (229) | +0.068 (266) |

**On PHerc0358, at the module's own default tolerance, the manual axis loses**
(−0.024 on 42 pairs), and it loses again at the next two tolerances (−0.049 and
−0.013); it only turns positive at 0.65 and looser, and never approaches the
shipped pipeline's +0.162. On PHerc0191 it loses at 0.40/1.5 (−0.031), is
exactly zero at four of the six tolerances and reaches at most +0.042. Only on
PHerc1203 does the gap survive every tolerance we tried (+0.017…+0.125). The
earlier README said this "is not reproduced on 0191/0358 at any chaining
tolerance", which reads as *vanishes*; what it actually does on 0358 is
**reverse**, and we would rather say so.

We tested whether the PHerc0358 reversal is a small-sample artifact and it is
not. Random 42-pair subsamples of the shipped 229-pair run (4000 draws without
replacement) give an expected gap of **+0.163, 95% band +0.048…+0.286**;
**−0.024 was observed, p < 0.001.** Our own resampling test says the
disagreement is real, not noise. We do not yet understand why, and we publish it.

Because of this we do not claim "the manual axis never loses". The claim we do
make, stated mechanically rather than with the undefined word "reliable" the
earlier text used — and "reliable" was undefined, there is no minimum pair
count or threshold behind it anywhere in our own evidence:

> **On the shipped zero-order pipeline, splitting its pairs by lamella-following
> retention at k = 1, 2 and 3 (`gate_by_ridge`: a continuous run of ≥30 samples
> where the arc's tangent agrees with the structure-tensor lamella direction to
> within 22° at coherence ≥0.25, both tracks passing on ≥k common slices) and by
> radius belt from the tracing centre, the manual axis's advantage is
> non-negative in every cell.**

It is *positive* in all but one: on PHerc1203's outermost radius belt (r > 140 px
at L3, 14 pairs) it is exactly +0.000. Two further cells carry too few pairs to
report at all — PHerc0191's innermost retained subset has none, PHerc0358's
outermost belt has four — and we are not counting those in our favour. It is
largest where the arcs provably
follow a lamella — +0.154 on 39 pairs of PHerc0358 at k ≥ 3, +0.238 on 21 pairs
of PHerc1203 at k ≥ 3, and +0.294 on the 17 lamella-retained pairs inside
PHerc1203's innermost belt (r 0–60 px). **Those subset numbers belong to the
shipped pipeline**, not to the first-order chainer; the earlier text attributed
the +0.29 to the first-order chainer, which was wrong.

Full tables, the resampling test, the null control and the provenance of every
number are in **`STEP2_CONSISTENCY.md` in this repository**. (The earlier README
cited a Russian working document that did not ship. That is fixed: the evidence
is now in the repo, in English, and it contains the results that argue against
us as well as the ones that do not.)

### 2. Shifted-axis control across 297 annotated slices

A banded-energy measure is computed at each annotated centre and at the same
centre displaced by a fixed number of voxels in four directions; a ratio above 1
is a win for the annotated centre. Reproduce with
`scripts/validate_axes.py` then `scripts/count_wins.py`.

At **+300 voxels** (≈2.6–2.8 mm, depending on the scroll's voxel size) the
annotated centre wins **184/297** slices, 0.620.

- The **defensible statistic is the scroll-level sign test: 9 of 10 scrolls
  above 50%, one-sided p = 0.011.** We quote that one. The pooled slice-level
  binomial gives p = 2.3e-05, and that is what an earlier version of this README
  quoted, but it pseudoreplicates: within a scroll the slices sit ~480 voxels
  apart, share one linearly-interpolated axis and sample continuous tissue, so
  they are not 297 independent trials. The unit of replication is the scroll.
  p = 0.011 is roughly 500× weaker and it is the number that survives scrutiny.
- **The tenth scroll is on the wrong side.** PHerc0800 is 14/29 = 0.483, median
  ratio 0.970 — there the annotated axis loses to the deliberately displaced one
  more often than it wins. That is not underpower, it is the wrong sign, and we
  name it rather than folding it into "limited per-scroll power".
- Per-scroll, uncorrected: PHerc0191 22/31 p=0.015, PHerc0813 21/31 p=0.035,
  PHerc1203 21/31 p=0.035, PHerc1218 20/30 p=0.049, PHerc0358 20/31 p=0.075,
  PHerc1545 17/29, PHerc0257 18/31, PHerc1447 18/31, PHerc0268 13/23,
  PHerc0800 14/29. **These p-values are uncorrected for multiplicity. Under
  Bonferroni (α = 0.05/10 = 0.005) none of the ten survives.**
- **The tighter control failed and here it is.** The same script also runs a
  **+150-voxel** displacement (≈1.3–1.4 mm). There the test is null:
  **159/297 = 0.535, pooled p = 0.12**, scroll-level 7/10 above 50%, sign-test
  p = 0.17, and three scrolls are below 50% (PHerc0268 0.348, PHerc1447 0.419,
  PHerc1545 0.483). `count_wins.py` prints both magnitudes side by side, so
  anyone who runs it sees this. The honest reading: **this measure resolves
  gross displacement, not annotation-scale accuracy.** It is evidence that our
  axes are not ~3 mm wrong; it is not evidence about their precision.

### 3. Calibration against sean's three published umbilici (0125/0211/0826)

Same ring-symmetry gates run on both sides, `scripts/calib_sean.py` (needs the
annotation tree for the slice PNGs; `UMBILICI_TREE`).

Median ring-gate displacement: **ours 268.3 voxels over all ten shipped axes
(279 points); sean's 273.6 over his three (75 points).** The gate is the same in
both cases and it does not separate us: it measures how crushed a cross-section
is, not how well it was annotated.

> **Correction.** An earlier version of this README said "ours 265 vs sean's 274".
> That 265 was three of our ten scrolls (PHerc0191/0257/0268, 93 points), read
> from the pre-finalization annotator output — 31-point polylines that still
> contained the untouched auto-suggestions this package says it drops. It also
> does not reproduce today (268.3). `calib_sean.py` now runs all ten scrolls
> against the shipped files, and 268.3 is what it prints. Sean's 273.6 → 274 is
> unchanged and reproduces exactly.

**Smoothness, and this one is not in our favour.** Kink = median distance of a
point from the chord between its z-neighbours. **Kink grows with the length of
the chord**, so no kink value means anything without the z-spacing it was
measured at, and every value below carries one (`scripts/axis_stats.py`; the
panel is `scripts/calib_figure.py`):

| scroll | whose | as published | at its median step | after thinning towards 480 | at its realized step | matched, 480 ± 20% only | triples |
|---|---|---|---|---|---|---|---|
| PHerc0211 | sean | 32 | 188 | 98 | 474 | **87** | 16 |
| PHerc0125 | sean | 39 | 212 | 61 | 465 | **51** | 16 |
| PHerc0826 | sean | 63 | 283 | 92 | 467 | **70** | 9 |
| PHerc0358 | ours | 86 | 368 | 153 | 376 | – | 0 |
| PHerc1218 | ours | 89 | 608 | 84 | 608 | – | 0 |
| PHerc1447 | ours | 119 | 640 | 127 | 640 | – | 0 |
| PHerc1203 | ours | 123 | 520 | 123 | 520 | **123** | 29 |
| PHerc1545 | ours | 140 | 552 | 140 | 552 | **137** | 22 |
| PHerc0800 | ours | 178 | 592 | 178 | 592 | – | 0 |
| PHerc0257 | ours | 182 | 480 | 177 | 480 | **172** | 23 |
| PHerc0813 | ours | 182 | 448 | 208 | 448 | **166** | 17 |
| PHerc0268 | ours | 261 | 328 | 469 | 336 | – | 0 |
| PHerc0191 | ours | 264 | 480 | 264 | 480 | **187** | 14 |

**The middle column is not a common-step comparison, and an earlier version of
this README wrongly said it was.** The thinning keeps, for each point of a
480-voxel target grid, the nearest point that already exists. That resamples a
*dense* polyline onto ~480 — it does exactly that for sean, whose three land at
465/474/467 — but it cannot manufacture a spacing a sparse polyline does not
have. Ours end up at 336 to 640, a 1.9× spread, and only two of the ten land on
480. So "thinned to a common 480-voxel z-step" was wrong about our own side, and
the sentence that called that column the fair one named the wrong column. The
error ran against us rather than for us — it made our roughest scroll look 1.8×
rougher than it is — but a fairness argument that points at the unfair column is
worth correcting either way.

The last column is the comparison that convention was meant to be: only those
triples whose **both** chords are within ±20% of 480 voxels, and no resampling
at all. **On that column sean is 51–87 and the five of ours that can be measured
on it are 123–187** — our smoothest matched scroll is 1.4× his roughest matched
value and our roughest is 2.1×. The other five of our ten contain no pair of
adjacent chords near 480 anywhere and simply cannot be placed on that axis; for
those we quote the as-published figure with its spacing, and nothing else.

**PHerc0268's 469 was an artifact of that resampling and we withdraw it.** The
thinning takes it from 23 points to 16, with a median gap of 336 but a mean of
484 and a maximum of 664: the result alternates short and doubled gaps, and the
median kink is then dominated by the long ones. Its honest as-published figure
is **261, over 328-voxel chords**. It and PHerc0191 (264, over 480-voxel chords)
are the two roughest of our ten in both columns where both of them appear, but
they are measured over different chord lengths and neither has a matched-spacing
value, so we do not rank them against each other.

What does not change: **sean's axes are smoother than ours.** That holds in
every one of the three columns — as published (his 32–63 against our 86–264),
after thinning (his 61–98, with exactly one of our ten, PHerc1218 at 84, inside
that band) and at matched spacing (his 51–87 against our 123–187). Only the
*size* of the gap depends on which column is used, and the largest version of it
was the artifact. An earlier version of this README said "our later scrolls
match his range" — that is false on the shipped files and it is removed. The two
sides are annotated at different z-densities and we have not shown that the
difference costs anything downstream, but we are not going to claim parity we do
not have.

### 4. Independent track on PHerc0358 — **not scripted**

Its core is filled with dense sediment (bright in CT); auto-tracking that plug
confirmed 19/22 trackable points within 11–93 vox. This is a journal-documented
spot check. There is no script for it in this repository and there was none
when it was run.

## What is scripted

| number | script | runs on a fresh clone? |
|---|---|---|
| 20.7 mm / 19.9 mm deviation, 37.9 mm sweep, 19.0 mm optimal stick, largest gap 2400 vox **and its endpoints z 15480→17880** | `scripts/axis_stats.py` | **yes** |
| **our ten rows** of the §3 kink table — all three columns, the z-spacing of each, and the matched-triple counts | `scripts/axis_stats.py` | **yes** |
| **sean's three rows** of the §3 kink table, his 61–98 band and his 51–87 matched range | `scripts/axis_stats.py` | **no** — needs `ref_sean/`, which is not in this repo; fetch his three files from the open bucket. Our ten rows print without it |
| 184/297, p = 2.3e-05, the clustered p = 0.011, per-scroll table **including the median ratios** (PHerc0800's 0.970), Bonferroni, the 159/297 null at 150 vox | `scripts/count_wins.py` | **yes** — `qc/validation_raw.json` ships |
| the banded-energy measure itself | `scripts/validate_axes.py`, `scripts/validate_bands.py` | no — needs the per-scroll slice PNGs |
| bare edges, tissue-band coverage per scroll **and the 90.6% aggregate** (z-weighted; the script also prints the 89.9% unweighted mean and the 94.0% median so the definition is visible) | `scripts/axis_stats.py` | needs `PHercNNNN/meta.json` (`UMBILICI_TREE`) |
| 268.3 vs 273.6 median displacement, the kink figure | `scripts/calib_sean.py`, `scripts/calib_figure.py` | needs the slice PNGs and `ref_sean/` |
| the shipped axes themselves, from annotator output | `scripts/finalize.py` | needs `results/` |
| **winding pitch 247–371 µm and the 380–468 µm cross-check** | **not shipped here.** Produced by `qc/витковая_карта_код/` in the annotation tree; the five per-spot values are in `qc/витковая_карта_метрики.json` there. The PHerc0800 voxel correction quoted in the caveats is one multiplication by 8.640/9.362 | no |
| **85–92% vs 74–83%, 43:7 / 42:5 / 21:3, the tolerance sweep, the resampling test** | **not shipped here.** Produced by `qc/шаг2_код/stack.py` and `qc/эвиденс_кандидаты/код/развилка/развилка3.py` in the annotation tree; every number and its provenance is tabulated in `STEP2_CONSISTENCY.md` §13 | no |
| **19/22 on PHerc0358** | **no script, journal-documented** | no |

`scripts/README.md` lists the known rough edges in the scripts themselves.

## Honest caveats
- Collapse zones (chevron-folded interiors) are best-effort judgement;
  PHerc0268 is crushed almost throughout. Note that PHerc0268 is also the scroll
  carrying the headline 20.7 mm number, is one of the two roughest of the ten
  (kink 261 at its 328-voxel spacing, against PHerc0191's 264 at 480 — an
  earlier version of this README quoted 469 here, which was an artifact of
  resampling and is withdrawn in §3), and has the lowest coverage of its tissue
  band (69%). The most dramatic
  geometry claim in this package rests on its weakest annotation; the
  second-largest deviation, PHerc0800 at 19.9 mm, makes the same point without
  leaning on it.
- Bare edges: PHerc0268 bottom 2952 vox, PHerc1545 top 1624 vox,
  PHerc0800 1152/1160 and PHerc1218 1192 vox carry no axis; interior
  gaps after finalization do not exceed 2400 vox (PHerc0191, z 15480→17880).
  Coverage of the tissue band runs 69–94%, 90.6% overall.
- Three slices excluded as undeterminable (PHerc1545 z=19056; PHerc0191
  z=15960, z=16440).
- Winding pitch at five readable spots is **247–371 µm** by FFT (locally
  separated sheets); tightly wound regions sit at the L3 Nyquist limit. An
  independent ridge-interval cross-check at the same five spots gives
  **380–468 µm** — 6% to 90% higher place for place — and it is quantised: the
  cross-check returns exactly 5.5 px at L3 at three of the five spots, which is
  411.9 µm on the two 9.362 µm scrolls and 380.1 µm on PHerc0800, whose voxel is
  8.640 µm. We quote the FFT range and we are not treating the cross-check as
  independent confirmation to micrometre precision. **Correction:** an earlier
  version of this README gave that range as 393–468 µm and called 411.9 µm "the
  value returned at three of the five spots". Both statements carried PHerc0800
  at the wrong voxel size — the demo pipeline assumed 9.362 µm for every scroll.
  Converting it (× 8.640 / 9.362) moves its cross-check from 411.9 to 380.1 µm
  and its FFT value from 358 to 331 µm; the FFT range 247–371 is set by
  PHerc0191 and PHerc0358, both 9.362 µm scrolls, and is unaffected.
- These five are **local** pitches, measured exactly where the laminae have
  separated far enough to be readable at L3, which is why they are larger than
  the 180–225 µm bracket our own pitch work gives for tightly-wound material;
  a contribution from the second harmonic (stuck-together sheet pairs) is also
  possible. Read 247–371 µm as "the pitch at these five spots", not as the
  winding pitch of these scrolls. The consequence for the Motivation section is
  conservative in the direction that matters: at a finer true pitch, 20.7 mm of
  lateral error would cross *more* windings than the 56–84 quoted there, not
  fewer.
- The shifted-axis control ran on a snapshot slightly older than the final
  files: 18/297 slices carry points that were later dropped at finalization,
  and three PHerc1545 points were moved (≤260 vox) after the control run.
  Winding-map numbers were computed on the final files. The calibration in §3
  now runs on the final files too — it did not in the earlier version of this
  README, which is why that number changed.

## Format compatibility
Field-for-field against sean's three files: top-level keys identical and in the
same order; per-point keys `x, y, z, score` identical and in the same order; all
coordinates integer on both sides; `score: 100` on every point on both sides;
`z_grid_spacing: 0` is sean's own convention; `min_score_threshold` and
`high_score_threshold` both 0.75. Our `metadata` is an exact superset of his,
adding only `source_volume` and `annotator_note`.

## Files
- `PHercNNNN_umbilicus.json` × 10 — the axes.
- `panels/axis_PHercNNNN.png` — each axis drawn on its scroll.
- `panels/step2_stack_*.png`, `panels/step2_points_*.png` — the winding-order
  test on PHerc 0191, 0358 and 1203.
- `panels/calibration_summary.png` — our gates calibrated against sean's three
  published umbilici, all ten scrolls.
- `STEP2_CONSISTENCY.md` — the full evidence behind the winding-order test,
  including the results that go against us.
- `qc/validation_raw.json` — the raw per-slice measurements of the shifted-axis
  control, so §2 can be recomputed without rebuilding anything.
- `scripts/` — QC gates, finalization, and the validation scripts behind the
  numbers above (`qc_gates.py`, `finalize.py`, `validate_axes.py`,
  `validate_bands.py`, `count_wins.py`, `calib_sean.py`, `calib_figure.py`,
  `axis_stats.py`, `qc_sheet.py`).

The annotator itself is a small web page; happy to share it on request.
