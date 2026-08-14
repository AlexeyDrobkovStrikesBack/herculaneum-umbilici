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

We are working on the First Letters prize scrolls, and kept running into the
same missing input: every winding-number assignment, every polar unwrap and
every spiral fit we tried takes a centre per z-slice, and none of these ten had
one. Three scrolls have a published umbilicus (sean's PHerc0125, 0211, 0826);
the ten in the prize set did not.

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

Parsing is not benefit, so that loader was then used to ask whether the axis buys
the tool anything: on a rule fixed in writing beforehand, over 300 cross-sections
of all ten scrolls, the annotated axis beats the best straight vertical stick on
10 of 10 scrolls, p = 0.0020, 2.03× — and the measure that says so is blind below
1.81 mm, so it credits gross placement and not annotation precision. That is
validation check 6, and its figure failed.

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

Six checks, and they are not equally reproducible. To be exact:

- **Check 6 (does the axis help a tool?) reproduces from a fresh clone**, from
  the ten `axis_benefit/prereg_PHercNNNN.json` via `scripts/axis_benefit.py`. It
  is the only check here that asks whether these files benefit anything rather
  than what they look like, and it is the only one that was pre-registered — the
  specification ships as `axis_benefit/PREREGISTRATION.md`. The measurement that
  produced those per-slice files does not run from a clone: it streams 5.7 GB out
  of the public volumes and imports villa's spiral code. §6.9 says so exactly.
- **Check 2 (the shifted-axis control) reproduces from a fresh clone.** Its raw
  per-slice measurements ship as `qc/validation_raw.json`, and
  `scripts/count_wins.py` recomputes every count, rate, median and p-value
  quoted in §2 from that file with nothing but python, numpy and scipy. So does
  `scripts/snapshot_recheck.py`, which sizes the one snapshot caveat this
  package carries by re-measuring the same control on the final files.
- **Check 5 (the straight-stick control) reproduces from a fresh clone**, from
  `qc/stick_control_raw.json` via `scripts/stick_control.py`.
- **Every geometry number about our own ten axes** (deviations, sweep, kink with
  the z-spacing each value was measured at, largest gap and its endpoints, and
  now also the tissue-band coverage and the bare edges, since the ten
  `PHercNNNN/meta.json` ship) reproduces from a fresh clone via
  `scripts/axis_stats.py`. One exception, marked in the table below: **sean's
  three rows of the smoothness table** come from his three published files,
  which are not ours to redistribute. Their values, and the sha256 of the file
  each was computed from, ship in `qc/sean_reference.json`, so the rows print
  and are tied to specific bytes; supply the files and the script recomputes
  them and reports whether the two agree.
- **Check 1 (the winding-order test): the statistic now reproduces from a fresh
  clone**, from the shipped `qc/order_fixture_PHercNNNN.npz` via
  `scripts/order_stat.py`. The tracing that produced those fixtures does not —
  that code is not in this repository, and the table below says exactly what
  shipping it would take and what it would weigh. Every number in this check,
  and where it came from, is tabulated in `STEP2_CONSISTENCY.md` §13.
- **Check 3 (calibration against sean)** needs the annotation tree — the
  per-slice PNGs — and sean's three files. Script ships.
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

**What this does not show, and it belongs here rather than in a caveats
section: none of that advantage comes from the axis being per-slice.** Freeze
the manual axis at a single constant point — the mean of its own 25 centres
over the stack, no per-slice variation whatsoever — and score it against the
live per-slice axis and the auto-centroid on one common pair sample (a pair
enters only if all three candidates return a defined sign on at least three
common heights, which trims 385/229/266 to 358/223/260):

| scroll | per-slice manual axis | manual axis **frozen at its stack mean** | auto-centroid | pairs |
|---|---|---|---|---|
| PHerc0191 | 0.919 (329) | **0.919 (329)** | 0.821 (294) | 358 |
| PHerc0358 | 0.897 (200) | **0.897 (200)** | 0.744 (166) | 223 |
| PHerc1203 | 0.850 (221) | **0.850 (221)** | 0.788 (205) | 260 |

**Net gain from tracking the core slice by slice: +0.000 on all three — the same
integer counts, not merely the same rounded rate.** Reproduce it from the
shipped fixture in about twenty lines: load `qc/order_fixture_PHercNNNN.npz`,
replace `man_c` with `man_c.mean(axis=0)` broadcast over the 25 heights, and
score all three candidates with `order_stat.radial_sign` unchanged, keeping
only pairs on which all three return a sign on ≥3 common heights. Take the
common sample seriously: if instead you just substitute the frozen axis into
`order_stat.py` and let it pick its own denominator as usual, you get
0.921 (361/392) / 0.900 (208/231) / 0.866 (251/290) — the frozen axis scoring
*above* the live one, on a sample it partly selected. Same conclusion, weaker
evidence; the identical-counts version above is the one to quote.

This is what §9 of `STEP2_CONSISTENCY.md` predicts, and we should have said so
here. §9 measures the metric's detection threshold at 3–6 mm depending on the
window; the manual axis's excursion from its own stack mean is median
1.8 / 1.5 / 3.1 mm with a maximum of 4.1 / 3.3 / 5.1 mm, over stacks spanning
18.0 / 13.9 / 19.3 mm. The whole motion we are asking the metric to see sits at
or under its resolution. The metric is not literally blind to the freeze —
20.1% / 15.3% / 24.3% of individual (pair, height) sign decisions change status
when the axis is frozen, mostly by moving in or out of evaluability, and among
decisions both versions do resolve they disagree on 0.3% / 0.2% / 0.7% — but
the changes cancel to nothing in aggregate.

So read this section as measuring **where the centre sits, not how it moves**.
The two distances make the point on their own, both computed from the same
fixture: the median separation between the manual axis and the auto-centroid is
13.30 / 13.44 / 6.75 mm, comfortably above the 3–6 mm the metric can resolve,
while the manual axis's own per-slice excursion is 1.8 / 1.5 / 3.1 mm, at or
below it. The metric sees the gap between the two axes and cannot see the
motion of either. (Jitter is not the explanation either. The auto-centroid does
move more between adjacent heights on two of the three — median step 18.1 and
11.3 L3 px against the manual axis's 5.8 and 4.7 on PHerc0191 and PHerc0358 —
but on PHerc1203 it moves *less*, 5.3 against 7.1, and still loses by 0.062.
§9 of `STEP2_CONSISTENCY.md` reaches the same conclusion by a different route,
comparing the centroid against a rigid shift of equal size.) This section
therefore lands on the same limit section 5 reaches from the other direction,
and section 5 already states it plainly: *"We do **not** claim that this is
because the axis follows the scroll's curvature."* Nothing here demonstrates a
benefit from
per-slice tracking on these three stacks, and the panels' title — *"does the
axis keep the order of the turns BETWEEN slices"* — should not be read as
saying otherwise. What per-slice annotation is for is the scrolls and zones
where the core wanders further than 3 mm; that case is not made by this test.

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
`panels/step2_*`, and `panels/order_map_*` / `panels/order_bump_*` for the same
three stacks drawn two other ways.

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

**The statistic itself is now recomputable — the tracer still is not.** This
used to be the one headline number a reader could not check at all. What ships
now is `qc/order_fixture_PHercNNNN.npz` (about 600 KB each): the tracer's
output for the three neutral-tracing stacks — the traced arcs, already matched
across heights into tracks, in L3 pixel coordinates, together with the two axes'
centres on each of the 25 heights of each stack. `scripts/order_stat.py` reads
those and recomputes, with numpy alone and no other input, every number in the
table above: 0.919 / 0.900 / 0.850 against 0.826 / 0.738 / 0.782, the shared
pair counts 385 / 229 / 266, and the paired cross-tabulation whose off-diagonal
is 43:7, 42:5 and 21:3.

Be clear about what that does and does not close. It closes the step from
"traced arcs on slices" to "85–92% against 74–83%" — the sign convention, the
pair selection, the requirement that both axes be scored on an identical sample,
the counting. It does **not** close the step from CT to traced arcs: the tracer
is still not in this repository, so a reader has to take the fixture as given.
What that would cost is stated in "What is scripted" below.

The fixtures were made by re-running the neutral stacks from scratch on
2026-08-13, and that re-run reproduced all nine published figures exactly, which
is itself the first independent re-execution of this pipeline since the numbers
were first written down.

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
- **The snapshot behind this control is now measured, not just disclosed.** The
  caveat at the bottom of this README says the control ran on a slightly older
  snapshot of the files. `scripts/snapshot_recheck.py` re-runs the whole of this
  section on the **final shipped files** and prints both results side by side;
  its raw output ships as `qc/validation_final_raw.json`, so the comparison
  reproduces from a bare clone. The drift is exactly three slices: 294 of the
  297 give a bit-identical measured value at the annotated centre, and the three
  that move are PHerc1545 z = 2544, 3088 and 3640 — precisely the three points
  the caveat names. The effect on the numbers: **+300 goes from 184/297 = 0.620
  to 182/297 = 0.613** (PHerc1545 alone, 17/29 → 15/29; every other scroll
  identical), pooled p from 2.3e-05 to 6.0e-05; **+150 goes from 159/297 to
  158/297**. **Both sign tests are unchanged — 9/10 with p = 0.011 at +300 and
  7/10 with p = 0.17 at +150** — so the statistic this README actually quotes
  does not depend on which snapshot is used. The published 184/297 is left as it
  is, because it is what the shipped `validate_axes.py` produced on the input it
  had; the newer number is shipped next to it rather than in place of it.

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

> **Correction, and it is about reproducibility rather than about a number.**
> An earlier version of this README told you to fetch sean's three files "from
> the open bucket". They are not there. As far as we can establish they exist
> only as the three attachments sean posted in the Vesuvius Challenge Discord
> `#general` on 2026-08-08, so there is no URL we can honestly give.
>
> **A second correction, to how we described the check that established that.**
> An earlier version of this paragraph — and of `scripts/fetch_sean.py` — said
> each of the three prefixes in `vesuvius-challenge-open-data` "holds exactly
> three non-volume keys: a mask photo, a photo and a lasagna prediction". That
> was an incomplete enumeration written as an exhaustive one, and in the
> paragraph whose whole purpose is to show that we looked properly. Those three
> are simply the first three keys S3 hands back in key order. Each prefix
> actually holds tens of thousands of non-volume keys. Re-walked recursively on
> 2026-08-13, `volumes/` and zarr chunk interiors excluded:
>
> | prefix | non-volume keys | of which under `representations/predictions/surfaces/` |
> |---|---|---|
> | `PHerc0125/` | 37,813 | 37,802 |
> | `PHerc0211/` | 35,508 | 35,497 |
> | `PHerc0826/` | 33,481 | 33,470 |
>
> The bulk of each prefix is a `…-surface-m7-L0-th0.2.normal-grids/` tree we
> never mentioned: per-axis normal grids as `xy/`, `xz/` and `yz/` `.grid` files
> (20,840 / 8,387 / 8,387 for PHerc0125, and similarly for the other two;
> 37,614 / 35,312 / 33,258 `.grid` files per scroll in total), a few hundred
> preview jpgs under `xy_img/`, `xz_img/`, `yz_img/`, a `metadata.json`, and
> beside it a `…-surface-m7-L0-th0.2.zarr` root. **This is not staleness on our
> part.** Those keys carry `LastModified` between 2026-05-13 and 2026-07-07, so
> the tree was already there, a month old, on the day we said we had checked.
> We had listed one page and described it as the whole prefix.
>
> **What the check does establish is unchanged, and we re-ran it rather than
> restate it.** A full recursive walk of all three prefixes — 106,802 keys,
> descending everything except `volumes/` and zarr chunk interiors — returns
> **zero** matches for `umbilic|axis|centre|center|spiral|winding`,
> case-insensitively, and no loose key sits directly under any of the three
> prefixes. A crawl of `dl.ash2txt.org/community-uploads/bruniss/` to depth 3 —
> 345 directory pages, 137,026 files — likewise returns zero matches for
> `umbilic`. There is no umbilicus file under any of the three prefixes and none
> in his community-uploads area. That conclusion never depended on the miscount;
> the description of the evidence did.
>
> The listing command, corrected. What the earlier text described is what you
> get **only with `&delimiter=/`**, which collapses each prefix to its immediate
> children:
>
> ```
> $ curl -s "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/\
>     ?list-type=2&prefix=PHerc0125/&delimiter=/&max-keys=1000"
> ```
>
> returns 504 bytes: `<KeyCount>3</KeyCount>`, `<IsTruncated>false</IsTruncated>`,
> the three sub-prefixes `PHerc0125/photos/`, `PHerc0125/representations/`,
> `PHerc0125/volumes/`, and no `<Key>` elements at all — identical in shape for
> `PHerc0211/` and `PHerc0826/`. Without the delimiter the same command returns
> 412 KB, `<KeyCount>1000</KeyCount>`, `<IsTruncated>true</IsTruncated>`, and
> after those first three keys nothing but `…_cos.ome.zarr/…` chunk paths. That
> truncated page is what the earlier claim was read off, and running the command
> as it was previously documented shows a reader 1000 zarr chunks rather than the
> tidy three the sentence promised.
>

> What ships instead is `qc/sean_reference.json`: for each of his three files,
> its sha256 and byte length, its z range, and the eight derived scalars of its
> row. `scripts/axis_stats.py` prints all thirteen rows on a bare clone, marking
> sean's three as read from that digest. If you supply the files —
> `scripts/fetch_sean.py --from <dir>` verifies them against those hashes and
> refuses to install a file that does not match — the script runs **two
> independent checks per row and prints both**: whether your copy's sha256
> matches the digest, and whether all eight recomputed values match it. Be
> precise about what that buys. The bytes leg says your copy is the copy we
> measured. The numbers leg says *this version of the script, run on your copy,
> still produces the values recorded in the digest* — it catches a digest edited
> away from the code as well as a file edited away from the digest, and nothing
> about either check speaks to whether sean's annotation is right.
>
> That is a correction, not just a description. Until 2026-08-13 the numeric
> comparison sat in an `elif` behind the sha256 test, so it ran only on bytes
> already proven identical — where deterministic code cannot make it fire — and
> the set of columns it compared omitted `kinkM`, the one column the argument
> above rests on. Doctoring the shipped digest's `kinkM` from 50.79 to 999,
> leaving every sha256 untouched, still printed *"matches
> qc/sean_reference.json"*. It now prints
> `(bytes match; !! recomputed ['kinkM'] DIFFER from the digest)`.
>
> Before any of this, three of the thirteen rows were simply absent from a clean
> clone and there was no way to tell whether your copy of his files was the one
> we measured.

### 4. Independent track on PHerc0358 — **not scripted**

Its core is filled with dense sediment (bright in CT); auto-tracking that plug
confirmed 19/22 trackable points within 11–93 vox. This is a journal-documented
spot check. There is no script for it in this repository and there was none
when it was run.

### 5. The straight-stick control — new, and it is half a negative result

The Motivation section argues that a straight vertical line is not a substitute
for a per-slice axis, and until now it argued that **geometrically**: our points
move by up to 20.7 mm. That says our annotation moves. It does not say that
moving with it buys anything. Section 2 is a different question again — it
displaces the centre by a fixed 150 or 300 voxels in four directions. Nothing in
this package had ever put the annotated axis against the straight stick and
measured which one the data prefers. `scripts/stick_control.py` does, on the
same 297 slices, with the banded-energy measure of section 2 imported unchanged,
against two sticks: the vertical through the mean of each scroll's annotated
points (the reference the 20.7 mm is measured from) and the optimally placed
vertical (the Chebyshev centre, the reference behind the 19.0 mm). Its raw
output ships as `qc/stick_control_raw.json`, so it recomputes from a bare clone.

**The positive half.** Against the mean stick the annotated axis wins 188/296
slices; against the optimally placed stick, 184/295. Per scroll it is ahead in
**all ten** in both cases — sign test p = 0.00098, which is the strongest
clustered statistic in this package, stronger than section 2's 9/10 at p = 0.011
— with per-scroll median ratios of 1.07–1.54 against the mean stick and
1.01–1.69 against the optimally placed one. The denominators are 296 and 295
rather than 297 because the measure returns nothing at all at the stick centre
on a slice or two — PHerc1545 z = 17960 for both sticks, and PHerc0268
z = 12584 for the optimally placed one: the stick lands far enough off the
tissue that fewer than 20 radii carry data. Dropping those runs against this
control, since they are slices where the stick fails outright.

**The negative half, and it is the important one.** The effect does not scale
with displacement, and it was supposed to. Section 2 established that this
measure is null at a 150-voxel displacement and positive at 300, so if what the
control sees is the axis tracking real curvature, the win rate should rise with
the stick's distance from the annotated centre. Binned by that distance
(mean stick): 10/14 = 0.71 below 150 voxels, 17/27 = 0.63 at 150–300,
64/92 = 0.70 at 300–600, 97/163 = 0.60 above 600. That is flat, and if anything
faintly decreasing. Against the optimally placed stick it is 0.60, 0.72, 0.64,
0.61 — flat again. The two small-displacement bins are far too small to test on
their own (14 and 27 slices, p = 0.09 and 0.12), so this is not a
contradiction of section 2; it is a failure to demonstrate the dose–response
that would have made the result mean what we wanted it to mean.

**What we therefore claim, and what we do not.** We claim: on every one of the
ten scrolls, the banded-energy measure prefers the annotated per-slice axis to
the best straight line through that scroll's own annotation, and it prefers it
on about 62–64% of slices. We do **not** claim that this is because the axis
follows the scroll's curvature, because the flat dose–response gives us no
evidence for that mechanism. The most likely alternative — that both sticks are
derived from our own points, so the comparison is between our annotation and a
smoothed version of itself — we cannot rule out with this design.

Unlike section 2 this control was measured on the final shipped files, so it
carries no snapshot caveat.

### 6. Does the axis help a tool? A pre-registered run on all ten scrolls

Sections 1–5 are statistics about the axes. None of them is a test of whether
the axes help anyone, and that is the thing reviewers of contributions like this
one ask for: a true test that it benefits current tooling — `fit_spiral.py` is
the tool usually named — or images and demonstrations of accuracy. This package
did not have one. This section is that test. Its figure failed; §6.7 says so
before anyone has to ask.

**The result.** Under a rule fixed in writing before any comparative quantity
existed, the annotated axis makes the papyrus more concentric about it than the
best straight vertical stick does about itself, on **10 of 10 scrolls** —
Wilcoxon signed-rank over the ten per-scroll means, **W = 0.0, p = 0.0020**
two-sided, pooled **+0.1611 against +0.0795, 2.03×**, 209 of 252 slices.

**The bound, in the body and not in a footnote.** The measure is **blind below
1.81 mm**. It resolves gross displacement, not annotation-scale accuracy — the
same wall section 2 hits, reached again from a different direction with a
different measure. **This section therefore credits gross axis placement and can
never credit annotation precision.** It stands up because the straight stick is a
median **6.0 mm** off, three times that floor, not because our clicking is good.

`scripts/axis_benefit.py` recomputes every number below from `axis_benefit/` on a
fresh clone with numpy and scipy. The measurement itself does not run here; §6.9
says exactly what it needs.

**There was an earlier attempt, and it is not hidden.** A first, exploratory run
on ten cross-sections of two scrolls gave 7/10 slices, 0.138 against 0.084
(1.65×), Wilcoxon p = 0.037 — **but its annulus rule was adopted after a first
rule had returned a null** (5 of 8, p = 0.25). That is a forking path, so that
number was never quoted and is not quoted here; it is why the run below was
pre-registered instead. The two z-samplings do not intersect at all: **none of
the 300 slices below was scored by the earlier run** (`scripts/axis_benefit.py`
prints the 300 indices it re-derives; the earlier run used z = 6000, 7500, 9000,
10500, 12000 on PHerc0268 and 4000, 6500, 9000, 11500, 14000 on PHerc0813, and
not one of those ten is in the 300).

#### 6.1 What was fixed in advance, and when

The specification ships verbatim as `axis_benefit/PREREGISTRATION.md`, written
before any comparison existed. In summary:

| decision | fixed value |
|---|---|
| scrolls | all ten, none droppable afterwards |
| slices | 30 per scroll, `z_k = round(z_min + k(z_max−z_min)/29)`, k = 0..29, decremented if odd; `z_min`, `z_max` = the first and last annotated control point |
| axis A | villa's `json_umbilicus_z_to_yx` at `downsample_factor = 2` |
| baseline B1 (primary) | straight vertical stick at the mean of that scroll's annotated control points — the strongest straight baseline |
| baseline B2 (secondary) | straight vertical stick at the volume centre, i.e. no umbilicus at all |
| annulus | equal-evidence: largest `r1` in [400, 2000] at which A, B1 **and** B2 each see a ring ≥ 95% on the scroll; `r0 = 0.25 r1` |
| coverage inadequate | slice is non-scorable, counted and reported (§6.5) |
| visibly bad annotation | **not excluded** — in particular the two PHerc0813 points §6.6 is about |
| measure | radial gradient anisotropy `q`, 72 sectors, σ_d 1.5, σ_t 6.0, subsampling 2 |
| primary statistic | per-scroll mean of (q_A − q_B1) |
| primary test | two-sided Wilcoxon signed-rank over the ten scroll values, α = 0.05 |
| failure | p ≥ 0.05, **or** fewer than 6 of 10 scrolls positive → claim not made |
| third variant | forbidden |

The slice indices were a rule, not a choice, and that is checkable rather than
asserted: `scripts/axis_benefit.py` re-derives all 300 from the ten shipped
`PHercNNNN_umbilicus.json` and reports that the run used exactly those.

`q` = +1 means every sheet crosses every ray at right angles, i.e. the sheets are
the circles villa's spiral model assumes; 0 means no preference; negative means
sheets running radially. The structure tensor is computed once per slice and does
not depend on the axis, so **all three conditions are scored on identical image
evidence** — only the axis differs.

#### 6.2 The tool, and what could not be run

Villa's own `scripts/spiral/umbilicus.py` — the loader `fit_spiral.py:137` calls
on `<dataset>/umbilicus.json`, which is what our ten files are — and villa's own
`scripts/spiral/sample_spiral.py`, both imported **unmodified**. Nothing was
reimplemented, so what is compared is the tool's model rather than a paraphrase
of it.

**`fit_spiral.py` itself could not be run here, and this is not its output.**
Three separate reasons, each sufficient: it requires a CUDA-capable PyTorch and
this machine has no NVIDIA device (`torch 2.13.0+cpu`, `torch.cuda.is_available()`
false); its `scripts/spiral/.python-version` pins **3.14** and this machine has
3.12.3; and it consumes a prepared dataset root containing `verified_patches/`,
which does not exist for any of these ten scrolls and which we cannot produce
here. So this is a proxy for one geometric property the fitter's model asserts,
measured through the fitter's own loader and parameterisation. It is not the
fitter's loss and does not stand in for it. See §6.8.

#### 6.3 The pre-registered result

| scroll | scorable | dropped | mean q annotated | mean q stick | **Δ** | slice wins |
|---|---|---|---|---|---|---|
| PHerc0191 | 30 | 0 | +0.1250 | +0.0783 | **+0.0467** | 20/30 |
| PHerc0257 | 29 | 1 | +0.1292 | +0.0655 | **+0.0637** | 23/29 |
| PHerc0268 | 28 | 2 | +0.1277 | +0.0867 | **+0.0410** | 23/28 |
| PHerc0358 | 26 | 4 | +0.1787 | +0.0824 | **+0.0962** | 26/26 |
| PHerc0800 | 26 | 4 | +0.2213 | +0.0646 | **+0.1566** | 26/26 |
| PHerc0813 | 29 | 1 | +0.1701 | +0.0795 | **+0.0906** | 23/29 |
| PHerc1203 | 29 | 1 | +0.2201 | +0.1374 | **+0.0828** | 24/29 |
| PHerc1218 | 17 | 13 | +0.1154 | +0.0553 | **+0.0602** | 12/17 |
| PHerc1447 | 25 | 5 | +0.1490 | +0.0603 | **+0.0887** | 20/25 |
| PHerc1545 | 13 | 17 | +0.1636 | +0.0612 | **+0.1024** | 12/13 |

- **Primary: Wilcoxon signed-rank on the ten Δ values, W = 0.0, p = 0.0020,
  two-sided.** That is the smallest p this test can return at n = 10 — every
  scroll moved the same way.
- **10 of 10 scrolls positive**, against a pre-registered requirement of ≥ 6.
- Pooled over the 252 scorable slices: **+0.1611 against +0.0795, 2.03×**;
  medians +0.1482 against +0.0817; **209 of 252** slice-level wins.
- Secondary, against the volume-centre stick: +0.1611 against +0.0766, **2.10×**,
  W = 0.0, p = 0.0020, 10/10, 206/252 slices.
- Secondary and **anticonservative, so not the headline**: slices within a scroll
  are not independent, and the slice-level tests pseudoreplicate exactly the way
  section 2's pooled binomial does. For completeness they are Wilcoxon
  p = 1.3e-28 and sign test p = 2.3e-27. The scroll is the unit of replication.
- The wins are large and the losses are small: mean gap +0.1050 on the 209 wins,
  −0.0322 on the 43 losses. The annotated axis loses where it is already weak —
  mean q +0.0927 on its losses against +0.1752 on its wins. **The 43 losses are
  real and they are in the table above.**

**Villa's own winding-phase concentration does not discriminate, and we report
that too.** Computed with villa's `get_theta_and_radii` on all 252 slices, `dr`
swept 4.0–30.0 independently per axis: mean R̄ 0.0145 (annotated), 0.0147 (mean
stick), 0.0146 (volume-centre stick). At the noise floor for every axis on every
slice and identical between them. A single global Archimedean spiral does not
describe these crushed cross-sections regardless of the axis — which is why
`fit_spiral` carries a deformation field — and this quantity cannot tell axes
apart. It is reported because it is villa's own, not because it helps.

#### 6.4 The sensitivity floor, which bounds what this can claim

Our own axis displaced sideways by d in four directions, on the six
pre-registered control slices per scroll (60; 53 had valid coverage). Displaced
centres are kept only where the ring at r1 is still ≥ 95% on the scroll.

| displacement | mm | slices | median q(annotated) − q(displaced) | mean | fraction degraded |
|---|---|---|---|---|---|
| 25 px | 0.45 | 53 | +0.0007 | +0.0006 | 0.70 |
| 50 px | 0.91 | 53 | +0.0030 | +0.0027 | 0.70 |
| **100 px** | **1.81** | 52 | **+0.0105** | +0.0104 | 0.77 |
| 200 px | 3.63 | 51 | +0.0321 | +0.0342 | 0.80 |
| 400 px | 7.23 | 45 | +0.0594 | +0.0823 | 0.87 |
| 800 px | 14.27 | 18 | +0.0750 | +0.1001 | 0.94 |

**The measure is not insensitive to the axis**: at the largest valid displacement
the score is lower than at the annotated axis on **43 of 53** control slices, and
it falls monotonically. **The floor is 100 px = 1.81 mm**, the first displacement
whose median drop reaches the pre-registered 0.01 threshold. Below it, moving the
axis half a millimetre changes q in the fourth decimal, which is noise.

**Why the result is nevertheless not an artifact of a blind instrument.** The
straight stick sits a median **6.0 mm** from the annotated axis over the 252
slices (mean 7.4 mm; per-scroll medians 3.9 mm on PHerc1203 to 15.9 mm on
PHerc0268). That is three times the floor. The gap we measure is +0.0816 pooled;
the control says a displacement of this order should cost between **+0.0321**
(its median at 3.63 mm) and **+0.0594** (its median at 7.23 mm, where its mean is
+0.0823). So the effect is the right size for an axis error of several
millimetres — at the top of that bracket rather than in the middle of it, and we
are not claiming a match to a decimal place.

**What that leaves.** This section establishes that **a straight vertical axis is
wrong by several millimetres on these scrolls and that this costs a downstream
geometric measure about half of what it can score.** It establishes nothing about
millimetre-scale annotation quality, and no experiment of this shape can. Section
2 says the same thing in its own words — *"this measure resolves gross
displacement, not annotation-scale accuracy"* — about a different measure on
different slices.

Note also what this does **not** repair: section 5's dose–response is still flat.
That is a different measure (banded energy) binned by stick distance, and the
monotone control above does not stand in for it.

#### 6.5 The 48 non-scorable slices, charged against us

The exclusion rule is a joint requirement on all three axes, so no slice can be
dropped for the annotation alone. Of the 48 dropped, the axis whose ring failed
the 95% coverage test at r = 400 was **the annotated axis on 8**, the
annotation-mean stick on **37**, and the volume-centre stick on **41** (they
overlap; a slice can fail for more than one). Most drops are the *sticks* running
off the edge of the scroll — that is, the exclusion removes slices the annotated
axis would mostly have won, so it works against this claim rather than for it.
Two scrolls carry most of them (PHerc1545 17, PHerc1218 13), both because
annotation and stick diverge so far that no common ring survives.

**The adversarial version, pre-registered before the drops were known: charge
every one of the 48 to the annotated axis as a loss.** Slice-level wins become
**209/300, sign test p = 7.7e-12**. The result does not depend on the exclusions.

#### 6.6 Post-hoc, and labelled post-hoc: the two bad PHerc0813 points

Not part of the pre-registered result — the primary number above keeps these
slices in, exactly as the specification required. Two PHerc0813 control points,
z = 6616 at (x 4748, y 5784) and z = 9296 at (x 5710, y 3978), sit visibly off
the coil centre on the rendered cross-sections. Three corrections were tried,
each in a *copy* of the JSON; the shipped file was not touched.

| variant | how the two points were re-placed | PHerc0813 Δ | primary test with it substituted |
|---|---|---|---|
| **pre-registered, unchanged** | not touched | **+0.0906** | W = 0.0, p = 0.0020 |
| post-hoc "eye" | placed by eye from the sheet curvature, without reference to q | +0.0788 | W = 0.0, p = 0.0020 |
| post-hoc "drop" | deleted, letting villa's loader interpolate across | +0.0721 | W = 0.0, p = 0.0020 |
| post-hoc "argmax" | placed at the q-argmax on their own slice — **circular by construction, an upper bound** | +0.0829 | W = 0.0, p = 0.0020 |

**All three corrections leave PHerc0813's Δ *lower* than the uncorrected
annotation** — including the circular upper bound that was allowed to choose the
axis the score likes best — and the primary test is unchanged at p = 0.0020 in
every variant. Those two points are worth fixing for the package's own sake; they
do not move this number.

**The by-eye replacement is low-confidence and should be read that way.** Those
two cross-sections are crushed flat and show no identifiable whorl, so the
placement carries an uncertainty of roughly ±300 level-0 voxels (2.8 mm). It sits
13.0 mm and 13.4 mm from the published points, and **13.7 mm and 16.3 mm from the
q-argmax** — that disagreement is evidence the eye was not following q, which is
what it was for, but it also means "eye" is one plausible correction, not the
correction. `scripts/axis_benefit.py` prints all three placements and every
pairwise distance.

#### 6.7 The figure failed, and it is not shipped

A reviewer asking for "accompanying images or demonstrations of accuracy"
deserves to be told this before they go looking. **We tried to build the picture,
under its own stated rule, and nothing passed.**

The rule, fixed before rendering and never applied to any number in §6.3–§6.6:
candidates are the 300 pre-registered slices ranked by q on the **annotated axis
only** (ranking on one panel cannot manufacture a gap in the other), capped at 3
per scroll; a narrow near-core annulus, `r_in` the smallest radius ≥ 40 px where
both axes see a ≥ 95% ring and `r_out = r_in + 12 × pitch` from villa's own best
`dr`; angular sampling at Nyquist along the arc; legibility = the fraction of the
unwrap's spectral energy in the winding band sitting at angular frequency |m| ≤ 2,
i.e. "how much of the layered signal runs horizontally"; ship only if the
annotated panel shows readable horizontal bands and the stick panel their break.

**Nothing passed.** The best full-turn legibility across all ten scrolls was
PHerc0191 z = 3496 at **0.184 annotated against 0.049 for the stick** — a real
and large ratio, and the panel still reads as chaos. PHerc0257 z = 3872 gave
0.122 against 0.079; PHerc1203 z = 13558 gave 0.130 against 0.082, and there the
two axes are only ~4 mm apart so the panels look alike anyway.

**Checked on known-good data before blaming the material.** PHercParis4
(Scroll 1) at 45.532 µm, an intact scroll, at its visible core, with the centre
additionally optimised by search *for legibility*, reaches only **0.094** — no
better than our crushed scrolls, and its unwrap shows a clean two-lobed sweep,
which is ovality of the coil rather than a wrong centre. So the failure is not
our axes and not our scrolls: sheets in a Herculaneum cross-section do not lie on
circles about *any* point well enough to read as horizontal bands over a full
turn at these resolutions.

**The only crops that do read as bands are 90° windows chosen because they look
right.** PHerc0191 z = 3496, sector 270–360°, reaches 0.642 against the stick's
0.328 and is genuinely legible. That is a flattering crop; the honest answer to
"why only a quarter turn?" is "because the other three quarters do not work", so
**it is not shipped**.

**The finding, plainly: a demonstration of this kind in unwrap form does not
exist for this material.** The statistic is real at 2× and p = 0.0020 and it is
not visible to the eye in a polar unwrap, because what q measures — a
several-millimetre bias in a gradient-direction average over 72 sectors — is not
what an eye picks out of a crushed cross-section. We stopped building this figure
rather than ship a caption describing something the image does not contain.

#### 6.8 What this establishes, and what it does not

**Established.** Under a rule fixed in writing before the data were touched, the
annotated axes make the papyrus more concentric than the best straight vertical
stick on all ten scrolls, 2.03×, p = 0.0020, and the result survives charging
every excluded slice against us. Villa's spiral geometry is demonstrably
sensitive to the axis (43/53 control slices degrade monotonically). The
sensitivity floor is 1.81 mm and the effect lives at a median 6.0 mm.

**Not established, and not claimed.**

- **This is not `fit_spiral`'s output** (§6.2). The real fitter also carries a
  deformation field, surface tracks, patches and winding-consistency losses, any
  of which could recover from a wrong axis or profit from a right one in ways
  nothing here measures. The unambiguous version of this experiment is a GPU host
  with a prepared spiral dataset and `fit_spiral` run twice on one scroll; that
  is still the thing to do and this is not a substitute for it.
- **Nothing here credits annotation precision** (§6.4), and no experiment of this
  shape can.
- Nothing here confirms or overturns sections 1–5, which use different measures
  on different slices.
- One thing this run suggested and did **not** test, left for a fresh
  pre-registration rather than reported alongside as a result: the effect looks
  largest where the annotation departs furthest from vertical. That is a new
  claim and it needs its own specification, written first.

#### 6.9 What ships, and what does not travel

Shipped: `axis_benefit/PREREGISTRATION.md` (the specification, verbatim), the ten
`axis_benefit/prereg_PHercNNNN.json` (every slice, every axis, every control
displacement, with the q, the pixel count, the ring coverage, the displacement in
µm and villa's R̄), the three post-hoc variants and the corrected copies they were
run from, and `axis_benefit/measure/` (the measurement code as it ran). 760 KB in
total. `scripts/axis_benefit.py` turns the per-slice values into every statistic
above on a fresh clone.

**What does not travel is the measurement itself.**
`axis_benefit/measure/prereg_run.py` streams one z-plane at a time out of ten
masked OME-Zarr volumes in `vesuvius-challenge-open-data` — level 1 of each
scroll's prize volume, uint8, 3422² to 6073² per slice, so **12 to 38 MB of range
reads per slice and about 5.7 GB across the 300** — and nothing is cached, so
re-measuring means re-streaming. It also imports villa's `umbilicus.py` and
`sample_spiral.py` from a `volume-cartographer` checkout: those are not ours to
redistribute and are referenced by path rather than copied. It needs torch (CPU
is enough). Every volume id is in `PREREGISTRATION.md` §3 and in each scroll's
own `metadata.source_volume`, so the inputs are named exactly and are public.
The run took 39 minutes of wall time in two processes of two torch threads each.

## Panels

Twenty-eight figures ship in `panels/`. None of them is the source of a number:
every quantity printed on a panel is one this README states and one of the
scripts recomputes. Where a panel and this README disagreed, the panel was
re-rendered — the ten-scroll atlas below is that case, and it is named rather
than quietly fixed.

**The axes themselves.**

- `axis_PHercNNNN.png` × 10 — each axis drawn on its scroll.
- `axis_polylines_all_ten.png` — **new.** All ten axes on the XZ side
  projection: the hand-placed nodes and the linear interpolation between them,
  which is exactly what a consumer of these files reads. The per-scroll node
  counts are the `control_points` counts of the shipped json, 22 to 31. Its two
  quantities are the 20.7 mm of the Motivation section (`scripts/axis_stats.py`,
  PHerc0268) and the ring-gate calibration of §3 — ours 268.3 voxels over 279
  points against sean's 273.6 over 75. **The earlier draft of this panel printed
  "265 against 274".** That is the withdrawn three-scroll, pre-finalization
  figure §3 corrects; the shipped panel carries the current one and cites §3.
- `annotation_site_PHercNNNN.png` × 3 (PHerc 0191, 0358, 1203) and
  `annotation_site_closeup_PHerc1203.png` — **new.** What the annotator was
  looking at: a crop around an annotated node — ~26 mm, ~38 mm for the close-up
  — with the ring detector's suggestion beside it and the turns traced around
  the point. These carry no statistic. Read the broken lines literally: a
  segment is drawn only where its tangent agrees with the structure-tensor
  lamella direction, and nothing is interpolated across a gap, so the empty
  regions are where the tracer does not hold a sheet, not where there is no
  papyrus. Every column is a height that was actually annotated: all ten of the
  crosses on these four panels are hand-placed control points of the shipped
  json, not interpolated values. That was checked rather than assumed, and one
  column had to move — see `scripts/README.md`.
- `calibration_summary.png` — our gates against sean's three, all ten scrolls (§3).

**The winding-order test (§1).**

- `step2_points_PHercNNNN.png`, `step2_stack_PHercNNNN.png` × 3 each — as before.
- `order_map_PHercNNNN.png` × 3 — **new.** The same three neutral-tracing stacks
  with the slice image removed altogether: only the matched arcs, ranked by
  distance from each axis, the auto-centroid row above the manual-axis row.
- `order_bump_PHercNNNN.png` × 3 — **new.** The same arcs as a bump chart, one
  line per arc, a crossing being an order reversal.

Both kinds print the whole-stack figures of §1 — 0.919 / 0.900 / 0.850 against
0.826 / 0.738 / 0.782 and the paired 43:7, 42:5, 21:3 — which
`scripts/order_stat.py` recomputes from the shipped fixtures with numpy alone.
The reversal counts in their subtitles ("3 of 3 pairs", "5 of 10 pairs") are for
the five slices displayed, not for the stack, and the panels say which is which.
**Both kinds also carry the limit §1 states**, in the figure and not in a
caption elsewhere: none of the advantage comes from the axis being per-slice,
and the manual axis frozen at its own stack mean scores identically. A figure
whose title asks whether the axis keeps the order *between* slices must not be
left to imply that per-slice tracking is what does the work, because on these
three stacks it demonstrably is not.

**Sections 5 and 6 have no figure at all.** §6.7 says why the one attempted for
§6 was not shipped.

`panels/calibration_summary.png` regenerates here, from `scripts/calib_figure.py`.
The other twenty-seven do not: they come from three producers that need the
annotation tree — the per-scroll L3 slice PNGs, the side projections and the
tracer — and would be dead code in a bare clone. `scripts/README.md` names all
three, says what each draws, and reports the byte-identity check each was
verified with.

## What is scripted

| number | script | runs on a fresh clone? |
|---|---|---|
| **every number in §6** — the per-scroll table, W = 0.0 / p = 0.0020, the pooled 2.03× and 2.10×, 209/252, the worst-case 209/300 at p = 7.7e-12, the drop attribution 8 / 37 / 41, the control table and the 1.81 mm floor, the 6.0 mm median stick distance, R̄, the three post-hoc variants and the distances between the three placements — and the check that the 300 slice indices are the ones the pre-registered rule gives | `scripts/axis_benefit.py` | **yes** — the ten `axis_benefit/prereg_PHercNNNN.json` ship (760 KB with the post-hoc files and the measurement code) |
| **the per-slice q values themselves** | `axis_benefit/measure/prereg_run.py`, shipped verbatim as it ran | **no.** It streams 12–38 MB per slice, about 5.7 GB over the 300, out of the ten masked OME-Zarr volumes named in `axis_benefit/PREREGISTRATION.md` §3, and it imports villa's `umbilicus.py` and `sample_spiral.py` from a `volume-cartographer` checkout, which are referenced by path rather than redistributed. Needs torch; CPU is enough |
| **the figure of §6.7** | **there is none, and that is the finding.** §6.7 gives the selection rule it was built under, the four best candidates and their scores, the Scroll 1 control at 0.094, and why the one legible crop was not shipped | — |
| 20.7 mm / 19.9 mm deviation, 37.9 mm sweep, 19.0 mm optimal stick, largest gap 2400 vox **and its endpoints z 15480→17880** | `scripts/axis_stats.py` | **yes** |
| **our ten rows** of the §3 kink table — all three columns, the z-spacing of each, and the matched-triple counts | `scripts/axis_stats.py` | **yes** |
| **sean's three rows** of the §3 kink table, his 61–98 band and his 51–87 matched range | `scripts/axis_stats.py`, `scripts/fetch_sean.py` | **the values yes, the recomputation no.** His files are not ours to redistribute and are not on any public URL we could find (see the correction in §3), so the six numbers of each row ship in `qc/sean_reference.json` with the sha256 of the file they came from, and print marked as such. Supply his files and the script recomputes them and reports whether they agree |
| 184/297, p = 2.3e-05, the clustered p = 0.011, per-scroll table **including the median ratios** (PHerc0800's 0.970), Bonferroni, the 159/297 null at 150 vox | `scripts/count_wins.py` | **yes** — `qc/validation_raw.json` ships |
| **the same control re-measured on the final files** (182/297, 158/297, both sign tests unchanged) and the three-slice drift itself | `scripts/snapshot_recheck.py` | **yes** — `qc/validation_final_raw.json` ships. `--measure` needs the slice PNGs |
| **the straight-stick control of §5** — 188/296 and 184/295, all ten scrolls above 50%, sign test p = 0.00098, the per-scroll medians and the displacement bins | `scripts/stick_control.py` | **yes** — `qc/stick_control_raw.json` ships. `--measure` needs the slice PNGs |
| the banded-energy measure itself | `scripts/validate_axes.py`, `scripts/validate_bands.py` | no — needs the per-scroll slice PNGs |
| bare edges, tissue-band coverage per scroll **and the 90.6% aggregate** (z-weighted; the script also prints the 89.9% unweighted mean and the 94.0% median so the definition is visible) | `scripts/axis_stats.py` | **yes** — the ten `PHercNNNN/meta.json` now ship (25 KB in total; they carry the tissue band, the slice list and the volume id) |
| 268.3 vs 273.6 median displacement, the kink figure | `scripts/calib_sean.py`, `scripts/calib_figure.py` | needs the slice PNGs and `ref_sean/` |
| the shipped axes themselves, from annotator output | `scripts/finalize.py` | needs `results/` |
| **winding pitch 247–371 µm, the 380–468 µm cross-check, the per-spot 6%–90% ratios and the PHerc0800 voxel correction** | `scripts/pitch_table.py` | **yes** — the producer's own five-spot output ships verbatim as `qc/winding_map_metrics.json` and the script applies the voxel correction, taking each spot's voxel size from that scroll's shipped `metadata.source_volume`. The measurement that produced those five pairs (`qc/витковая_карта_код/` in the annotation tree) does not ship |
| **85–92% vs 74–83%, 43:7 / 42:5 / 21:3** | `scripts/order_stat.py` | **yes** — recomputed from `qc/order_fixture_PHercNNNN.npz`, which ships. The *tracer* that produced those fixtures still does not: see the row below |
| **the tracing that produces the fixtures** | **not shipped here.** `qc/шаг2_код/stack.py` (31 KB) plus `winding_map.py` (12 KB) and `numbering.py` (6 KB) from the same tree | no. Stated exactly, because "too big to ship" would not be true: the missing *data* is **14.6 MB** — 25 L3 slices for each of PHerc0191/0358/1203, each one plane `round(z/8)` of level 3 of that scroll's `…-masked.zarr` in `vesuvius-challenge-open-data`, normalised to the 1st/99th percentile of its non-zero pixels, exactly as `build.py` writes the catalogue slices. What blocks it is the ~49 KB of tracer code: it is Russian-commented, hard-wired to the annotation tree, and shipping it means proving it still regenerates the published numbers rather than merely running. We re-ran it on 2026-08-13 and it does (all nine figures exact), but translating and de-hardcoding it is a separate pass |
| **the tolerance sweep and the resampling test** | **not shipped here.** Produced by `qc/эвиденс_кандидаты/код/развилка/развилка3.py` in the annotation tree; every number and its provenance is tabulated in `STEP2_CONSISTENCY.md` §13 | no |
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
  README, which is why that number changed. **The cost of that staleness is now
  measured rather than left open**: re-running the control on the final files
  changes the measured value on 3 of 297 slices, moves 184/297 to 182/297 and
  159/297 to 158/297, and leaves both scroll-level sign tests identical. See §2
  and `scripts/snapshot_recheck.py`. The straight-stick control of §5 was
  measured on the final files from the start.

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
- `panels/axis_polylines_all_ten.png` — all ten axes as node polylines on the
  XZ side projection, with the §3 calibration numbers.
- `panels/annotation_site_PHerc{0191,0358,1203}.png` and
  `panels/annotation_site_closeup_PHerc1203.png` — the annotation site itself:
  crop, detector suggestion, and the turns traced around an annotated node.
- `panels/step2_stack_*.png`, `panels/step2_points_*.png` — the winding-order
  test on PHerc 0191, 0358 and 1203.
- `panels/order_map_*.png`, `panels/order_bump_*.png` — the same three stacks
  drawn without the slice image, and as a bump chart of arc rank.
- `panels/calibration_summary.png` — our gates calibrated against sean's three
  published umbilici, all ten scrolls.
- See the "Panels" section above for what each one shows and what regenerates it.
- `STEP2_CONSISTENCY.md` — the full evidence behind the winding-order test,
  including the results that go against us.
- `qc/validation_raw.json` — the raw per-slice measurements of the shifted-axis
  control, so §2 can be recomputed without rebuilding anything.
- `qc/validation_final_raw.json` — the same control re-measured on the final
  shipped files, so the disclosed snapshot drift can be sized (§2).
- `qc/stick_control_raw.json` — the raw per-slice measurements of the
  straight-stick control (§5).
- `qc/order_fixture_PHercNNNN.npz` × 3 — the traced arcs and the two axes'
  centres for the three winding-order stacks, so §1's headline statistic can be
  recomputed without the tracer.
- `qc/sean_reference.json` — sha256 and derived smoothness numbers for sean's
  three reference umbilici, which are not redistributed here (§3).
- `axis_benefit/PREREGISTRATION.md` — the specification of §6, fixed in writing
  before any comparative quantity existed, shipped verbatim.
- `axis_benefit/prereg_PHercNNNN.json` × 10 — the per-slice results of §6: for
  every one of the 300 slices, the q of each axis and of every control
  displacement, with the pixel counts, ring coverage, the stick's displacement in
  µm and villa's R̄. `scripts/axis_benefit.py` recomputes §6 from these.
- `axis_benefit/prereg_PHerc0813_posthoc_{eye,drop,argmax}.json` and the three
  corrected `PHerc0813_posthoc_*.json` they were run from — the post-hoc variants
  of §6.6. These are **not** the published annotation; the shipped
  `PHerc0813_umbilicus.json` is untouched.
- `axis_benefit/measure/` — the measurement code of §6 as it ran. It does not run
  from a bare clone (§6.9); it is here so the method is inspectable.
- `qc/winding_map_metrics.json` — the winding-map measurement's own output for
  the five readable spots, copied verbatim from the annotation tree, so the
  pitch numbers in the caveats have a source (`scripts/pitch_table.py`).
- `PHercNNNN/meta.json` × 10 — the annotation catalogue's own metadata for each
  scroll: source volume, level-3 frame, tissue band, and the list of annotated
  slices. 25 KB in total, shipped verbatim from the annotation tree so that the
  coverage and bare-edge numbers recompute from a bare clone. (These are the
  only shipped files that still carry a Russian sentence, in their `note`
  field; they are shipped byte-for-byte as the scripts read them rather than
  retyped.)
- `requirements.txt` — the versions every number here was produced or
  re-verified with.
- `scripts/` — QC gates, finalization, and the validation scripts behind the
  numbers above (`qc_gates.py`, `finalize.py`, `validate_axes.py`,
  `validate_bands.py`, `count_wins.py`, `calib_sean.py`, `calib_figure.py`,
  `axis_stats.py`, `qc_sheet.py`, `order_stat.py`, `stick_control.py`,
  `snapshot_recheck.py`, `fetch_sean.py`, `pitch_table.py`,
  `axis_benefit.py`).

The annotator itself is a small web page; happy to share it on request.
