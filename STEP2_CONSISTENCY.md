# Step 2 — Winding-order consistency between heights: full evidence

English translation and consolidation of `ШАГ2_СОГЛАСОВАННОСТЬ.md` (Russian working
document, 2026-08-09 through 2026-08-10). This file exists so that a reviewer can check
the winding-order claim in the package README without reading Russian and without
trusting our summary of our own numbers.

Every number below is copied character-for-character from the working document or from
the script logs it cites. Where the working document contradicts itself, the
contradiction is printed rather than resolved. Where a number is not produced by a
shipped script, it is marked.

**Terminology.** What is traced and matched across heights are **traced arcs** of
papyrus, not verified single sheets. This is a retraction we made ourselves on
2026-08-10 and it applies to every number in this file; see §7.

---

## 1. Read this first: what does not hold

The README sentence *"the manual axis never loses"* is not supported by this document.
The following are the negative results, stated before the positive ones.

1. **On PHerc0358 the sign reverses under the stricter first-order chainer at the
   module's own default chaining tolerance**: manual 0.857, auto 0.881, gap
   **−0.024** on 42 pairs. The auto-centroid wins that run.
   (`ШАГ2_СОГЛАСОВАННОСТЬ.md:554`; log `развилка3.log`.)

2. **That reversal is not a small-sample artifact.** A 4000-draw resampling test says
   the observed −0.024 is far outside what random 42-pair subsamples of the shipped
   pipeline would give (expected +0.163, 95% band +0.048…+0.286, p < 0.001). See §8.3.
   We ran this test ourselves and it argues against us.

3. **On PHerc0191 and PHerc0358 the first-order chainer never reproduces the shipped
   pipeline's gap at any chaining tolerance** — six tolerances tried. On 0191 it runs
   between −0.031 and +0.042; on 0358 between −0.049 and +0.052, i.e. it is negative at
   the three tightest tolerances. The shipped pipeline's values there are +0.093 and
   +0.162. See §8.1.

4. **In the swap control, the worst case for the manual axis on PHerc0358 is a tie in
   the auto-centroid's favour**: 0.909 manual vs 0.916 auto, a difference of one pair
   out of 143. The working document calls this a tie ("ничья"); on the face of the
   numbers the auto-centroid is one pair ahead. See §6.

5. **The strict metric — same absolute winding number at every height — is dead at L3
   for both axes.** 0–22% of arcs keep their number, and only single-digit counts of
   arcs are even evaluable. See §5.

6. **The size of the gap is tracing-pipeline dependent** and therefore cannot be
   claimed as a property of the axes alone. The working document states this in as many
   words (`:665-666`).

What survives all of the above is narrower than the README says. The defensible
statement is: *on the shipped (zero-order) tracing pipeline, the manual axis preserves
pairwise winding order better than the auto-centroid on all three stacks under neutral
tracing; under the swap control it is ahead in six of the nine cells, exactly level in
two and behind in one (PHerc0358 traced around the auto-centre, by a single pair — see
bullet 4 above and §6); and its advantage is non-negative in every subset of that
pipeline we split out, positive in all of them but one, which is exactly zero — but
under an alternative first-order chainer the effect survives only on PHerc1203, and on
PHerc0358 it reverses.* Earlier drafts of this sentence said "in all three swap
directions" and "on every subset", which bullet 4 four lines above already contradicts;
the counts are the statement.

---

## 2. Data

| scroll | stack (level-0 z) | window | voxel |
|---|---|---|---|
| PHerc0191 | 14520…16440, 5 catalogue slices | step-1 window at z=15480 | 9.362 µm |
| PHerc0358 | 10688…12176, 5 catalogue slices | step-1 window at z=11432 | 9.362 µm |
| PHerc1203 | 5 catalogue slices, step-1 neutral zone (coordinates not printed) | step-1 window | 9.362 µm |

All three volumes are 9.362 µm/voxel (checked against the volume ids in
`volumes.json`); all millimetre figures in this file use that voxel. (PHerc0268, 0800,
1218 and 1447 are 8.640 µm/voxel and do not take part in step 2.)

Between catalogue slices (spacing 370–520 vox) five intermediate thin slices were
fetched per gap (spacing ~60–90 vox; window chunks only, via HTTP Range requests, from
an uncompressed volume, brightness normalised the same way as the catalogue PNGs — 1/99
percentiles). 25 slices per stack. Stack height 14–19 mm. Working resolution is L3
preview, 74.9 µm/px.

---

## 3. Method

**Tracing is independent of both axes under test.** Brightness ridges along rays are
chained (step-1 code) around a **neutral centre**: the fixed geometric centre of the
window, identical for every slice of the stack and for both axes being compared.
Neither the manual axis nor the auto-centroid enters the tracing. A full swap control
that re-traces around each axis in turn is run separately (§6).

**Matching arcs between heights uses no winding numbers** — otherwise the argument
would be circular:

1. Global window drift between adjacent thin slices is measured by phase correlation of
   the window images (median drift 5–10 px L3 per thin step). Direct matching across a
   full catalogue step does not work: the scroll's tilt shifts arcs by more than half a
   winding pitch, which is why the thin slices are needed at all.
2. Arc A on slice *i* and arc B on slice *i+1* (or *i+2* — one skipped slice allowed)
   are candidates for "the same physical object" if, after drift removal, the median
   XY distance between their points is below **0.45 of the measured inter-arc gap**.
   The gap is measured from the tracing itself: median distance from a point of one arc
   to the nearest point of a different arc, 4.6–5.1 px L3 ≈ 345–385 µm on these windows.
   The threshold is below half the gap, so confusing an arc with its neighbour in the
   next winding is excluded by construction.
3. A track is a connected component of that correspondence graph. Merging adjacent
   windings is additionally forbidden: two members of a component on the same slice must
   lie on the same curve and close together (median mutual distance ≤ threshold),
   otherwise the merge is blocked; components that still violate this are dropped from
   the evaluation entirely.

**The metric (pairwise order preservation from an axis).** For a pair of tracks A and B
and a candidate axis C on a given slice, take the rays from C that cross both arcs
(2° angular bins) and compare radii directly. The sign ("which one is closer to the
axis") is defined if there are ≥5 common bins and ≥80% of them agree; otherwise the
pair's order is *undefined* on that slice.

A pair enters the evaluation only if **both** axes give a defined sign on ≥3 common
slices — the two axes are therefore scored on exactly the same set of pairs. A pair is
"preserved" if the sign is the same on all of those slices.

Within a single slice the order from any centre is self-consistent (this is what
sank the first version of the demo in step 1), but *between* heights a correct axis has
to preserve the order of a physical pair — windings are nested — whereas an axis that
wanders relative to the scroll flips pairs. Fragmented tracing barely affects a radial
comparison because no counting through the core is involved.

---

## 4. Headline result (neutral tracing, shipped pipeline)

| scroll | pairs | auto-centroid: order preserved | manual axis: order preserved | centre spread over the stack |
|---|---|---|---|---|
| PHerc0191 | 385 | 318 (82.6%) | **354 (91.9%)** | auto 13.6 mm, manual 7.0 mm |
| PHerc0358 | 229 | 169 (73.8%) | **206 (90.0%)** | auto 14.1 mm, manual 5.4 mm |
| PHerc1203 | 266 | 208 (78.2%) | **226 (85.0%)** | auto 7.4 mm, manual 9.0 mm |

Paired cross-tables (the same pairs for both axes):

| scroll | both preserved | manual only | auto only | both lost |
|---|---|---|---|---|
| PHerc0191 | 311 | **43** | 7 | 24 |
| PHerc0358 | 164 | **42** | 5 | 18 |
| PHerc1203 | 205 | **21** | 3 | 37 |

Source: `qc/шаг2_метрики.json`, records with `trace_mode: "neutral"`, field
`radial_order.cross` — these three cross-tables exist in the JSON verbatim.

Ratios of the paired counts: 43/7 = 6.1, 42/5 = 8.4, 21/3 = 7.0, i.e. **6–8×**, not
3–8×; see §10 for where a "3" can come from.

Honest notes carried over from the working document:

- On PHerc1203 the auto-centroid's spread over the stack (7.4 mm) is **smaller** than
  the manual axis's (9.0 mm). The manual axis does not win by moving less; it wins by
  moving *with* the scroll — the core is genuinely tilted there.
- The margin is smaller than in the demolished step-1 demo, where the metric rewarded
  the tracing axis. 8–16 percentage points over hundreds of pairs per scroll is what
  survives an honest construction.

---

## 5. The strict metric (same absolute winding number) is dead at L3

Winding number = the ordinal of a ray's crossing of an arc, counted from the axis
itself (not from the window edge: the window is fixed and the axis drifts relative to
it, so counting from the edge would break even for a perfect axis). Result: the mode of
the number along one arc has stability ~0.3 (the number wanders by ±3–6 along a single
arc), and the fraction of arcs with the same number on ≥2 catalogue slices is 0–22%
for **both** axes, with only single-digit numbers of arcs evaluable at all:

| scroll | arcs evaluated | manual: number holds | auto: number holds |
|---|---|---|---|
| PHerc0191 | 20 | 0 | 2 |
| PHerc0358 | 8 | 1 | 0 |
| PHerc1203 | 9 | 0 | 2 |

Cause: at L3 only a fraction of the sheets are traced, in fragments; every internal
fragment that appears or disappears shifts the count of everything outside it by ±1.
That noise is identical for a correct and a displaced axis and drowns the signal.
**Absolute winding number between heights is unmeasurable at L3 through this pipeline**,
for either axis. The step-2 claim is about *order* and only about order.

---

## 6. Swap control (re-tracing around either axis)

The whole metric was run three times: with tracing around the neutral centre, around
the manual axis, and around the auto-centroid.

| scroll | tracing | pairs | manual | auto |
|---|---|---|---|---|
| PHerc0191 | neutral | 385 | **0.919** | 0.826 |
| PHerc0191 | around manual | 406 | **0.919** | 0.855 |
| PHerc0191 | around auto-centre | 238 | 0.929 | 0.929 |
| PHerc0358 | neutral | 229 | **0.900** | 0.738 |
| PHerc0358 | around manual | 193 | **0.953** | 0.881 |
| PHerc0358 | around auto-centre | 143 | 0.909 | 0.916 |
| PHerc1203 | neutral | 266 | **0.850** | 0.782 |
| PHerc1203 | around manual | 378 | **0.833** | 0.767 |
| PHerc1203 | around auto-centre | 269 | 0.829 | 0.829 |

All nine rows are present in `qc/шаг2_метрики.json` (`trace_mode` ∈ {neutral, man,
auto}, field `radial_order`).

What this shows, in the working document's own words:

1. *"There is no reversal anywhere"* — unlike step 1, where the swap flipped the
   result. *"The worst case for the manual axis is a tie (0358: 0.909 against 0.916, a
   difference of one pair out of 143)."* (`ШАГ2_СОГЛАСОВАННОСТЬ.md:148-150`.)
   For the record: 0.909 × 143 = 130 pairs, 0.916 × 143 = 131 pairs. The auto-centroid
   is ahead by one pair. Calling that a tie is our reading, not a fact; a reviewer is
   entitled to call it a loss.
2. Tracing around a centre does favour that centre (the effect caught in the step-1
   review reappears here): around the auto-centroid only arcs that are star-shaped with
   respect to it are selected — and on that subset, favourable to the auto-centroid, it
   only *catches up* with the manual axis rather than overtaking it.
3. The manual axis's score is stable against the tracing mode (0.83–0.95 across all nine
   cells); the auto-centroid's score rises only when the arcs were selected around
   itself.

---

## 7. Retraction: these are traced arcs, not sheets

On 2026-08-10 the ridge chainer was audited after Alex rejected the illustration panels
by eye. The chaining in `winding_map.build_chains` is zero-order: a candidate is scored
by `d = abs(r - lr)`, i.e. by closeness to the **last** radius of the chain, with no
prediction of the slope dr/dθ. Near the core, where the arcs are few and nearly
concentric, this works. Further out the radial gap between ridges falls to 2.4–3.5 px
L3 and "nearest ridge in radius" is almost always the **neighbouring** sheet at the same
radius. The greedy minimum-|Δr| choice keeps the radius constant, i.e. it draws a
**circle**, hopping from sheet to sheet.

Measured against a structure-tensor reference direction for the lamella (45° = random;
points with above-median coherence):

| scroll, slice | radius belt, px L3 | trace↔lamella | circle↔lamella | trace↔circle |
|---|---|---|---|---|
| PHerc1203 z=11632 | 12–40 | 10.0° | 20.5° | 15.9° |
| | 70–100 | 16.5° | 25.0° | 7.5° |
| | 140–200 | 21.2° | 22.2° | **2.8°** |
| | 260–340 | 26.9° | 26.1° | **2.0°** |
| PHerc0358 z=11432 | 12–40 | 10.4° | 18.9° | 12.3° |
| | 140–200 | 35.1° | 36.3° | **2.7°** |
| | 200–260 | 44.4° | 44.1° | **2.5°** |
| PHerc0191 z=8768 | 12–40 | 27.6° | 40.0° | 20.6° |
| | 140–200 | 25.2° | 26.3° | **2.8°** |

Beyond r ≈ 100–140 px L3 (7.5–10.5 mm) the trace differs from a bare circle by 2–3° and
agrees with the lamella exactly as well as a circle does — i.e. it carries no
information about the sheet. Inside the core the trace is real (10–16° against 17–25°
for a circle). On PHerc0191 it is weak everywhere.

**The consequence for wording** (`ШАГ2_СОГЛАСОВАННОСТЬ.md:461-464`, rendered):

> But the numbers can no longer be claimed as a "fraction of pairs of PHYSICAL SHEETS":
> beyond the core the shipped trace is not a sheet but an arc of constant radius hopping
> between sheets. The correct wording is "fraction of pairs of traced papyrus arcs
> matched between slices". This weakens the wording, but not the number.

**Why the numbers are nevertheless not affected by the drawing defect.** The defect is
in the connectivity of the polyline, and the metric does not use connectivity:

- `radial_sign` (`stack.py:446-471`) receives `pa`, `pb` as **unordered** point clouds
  plus an axis `C`. Lines 453–457 compute each point's angle and radius, 458–460 bin
  them by angle, 464 compares mean radii in the common bins. Neither the order of points
  along the polyline, nor arc length, nor winding number, nor a crossing count enters
  anywhere.
- `radial_order_metric` (`stack.py:495-496`) calls `radial_sign(good[a][i], good[b][i],
  C_m)` and `radial_sign(good[a][i], good[b][i], C_a)` — **the same two arrays**, only
  the axis changes. Any tracing defect enters both branches identically.
- A chain hopping to a neighbouring sheet shifts the track's radius by at most one
  inter-arc gap: 4.6–5.1 px L3 = 0.35–0.38 mm. The null control (§9) shows the metric
  does not react to an axis shift even of 1.5 mm. A 0.36 mm perturbation is an order of
  magnitude below the metric's resolving power.

Direct control — take the **same** tracks from the shipped run and replace every arc by
a circular arc of the same mean radius and the same angular span, erasing all radial
shape:

| stack | as is (manual/auto) | after replacement by circles |
|---|---|---|
| PHerc0191 | 0.919 / 0.826, cross 43:7 | 0.897 / 0.795, cross 47:7 |
| PHerc0358 | 0.900 / 0.738, cross 42:5 | 0.899 / 0.739, cross 38:5 |
| PHerc1203 | 0.850 / 0.782, cross 21:3 | 0.846 / 0.791, cross 19:5 |

The numbers reproduce to within ±0.02: the metric does not use the radial shape of the
traces at all, and corrupting the shape cannot corrupt it. *Unscripted in the shipped
tree*: this control was run from a session scratch directory
(`scratchpad/контроль_окружности.py`); only the document records it.

Gap decomposition by radius from the tracing centre (shipped pipeline) — the gap lives
where the tracing provably holds a sheet, not in the degenerate belt:

| stack | r 0–60 | of those, lamella-held | r 60–100 | r 100–140 | r 140+ |
|---|---|---|---|---|---|
| PHerc0191 | +0.091 (55) | 0 pairs | +0.094 (203) | +0.094 (117) | +0.100 (10) |
| PHerc0358 | +0.106 (113) | **+0.207 (29)** | +0.190 (100) | +0.500 (12) | 4 pairs |
| PHerc1203 | +0.135 (89) | **+0.294 (17)** | +0.054 (93) | +0.014 (70) | +0.000 (14) |

The degenerate belt (r > 140) holds 10, 4 and 14 pairs out of 385, 229 and 266 — it
cannot move the totals. Note that **+0.294 is a subset of the shipped zero-order run**,
not a first-order-chainer number. The README before 2026-08-13 attributed it to the
first-order chainer; that is corrected (see §11).

---

## 8. The first-order chainer: where the claim breaks

A fixed, provably sheet-following chainer exists
(`qc/эвиденс_кандидаты/код/трасса.py`, `trace_sheets_fixed` — first-order chaining with
slope prediction, plus `gate_by_ridge`, an honest break when the arc stops agreeing with
the lamella). On PHerc1203 in the 140–200 belt it gives trace↔lamella 6.1° against
trace↔circle 12.3° — the line finally follows the sheet instead of a circle.

Rerunning the whole metric with it, against the shipped pipeline:

| stack | shipped (zero-order) chainer | fixed (first-order) chainer, flag configuration |
|---|---|---|
| PHerc0191 | 385 pairs, 0.919 / 0.826 (**+0.094**) | 61 pairs, 0.967 / 0.967 (**+0.000**) |
| PHerc0358 | 229 pairs, 0.900 / 0.738 (**+0.162**) | 77 pairs, 0.870 / 0.883 (**−0.013**) |
| PHerc1203 | 266 pairs, 0.850 / 0.782 (**+0.068**) | 113 pairs, 0.805 / 0.788 (**+0.018**) |

The obvious explanation "the sample became small and easy" was checked and did **not**
hold for track length: the median number of slices per pair is 3 in both runs, and in
the dominant "3–5 slices" bin the picture is the same (shipped +0.086/+0.153/+0.067,
fixed +0.000/−0.027/+0.018). With a base rate of 43:7 out of 385 on PHerc0191 one would
expect roughly 6:1 disagreements on 61 pairs; 0:0 was observed.

### 8.1 Chaining-tolerance sweep

The flag numbers above were computed at a chaining tolerance that **does not exist in
the module**. `трасса.trace_sheets_fixed` chains with
`tol = clip(0.30 · gap, 0.6, 1.2)` (`трасса.py:94-100`, `tol_frac=0.30`, cap 1.2
hard-coded) — that is the module default. The flag's 61/77/113 pairs reproduce only at
`clip(0.50 · gap, 0.6, 1.8)`, a variant from a one-off session script.

Full sweep, minimum chain length held at l_min = 45 (`stack.py:69`, `L_MIN_TRACE = 45`,
which overrides the module's own signature default of 30). Each cell is
**manual preserved-rate minus auto preserved-rate**, with the **number of evaluated
pairs** in parentheses — pairs where *both* axes gave a defined sign on ≥3 common
slices, i.e. the same denominator for both axes:

| chaining tolerance | PHerc0191 | PHerc0358 | PHerc1203 |
|---|---|---|---|
| 0.30 · gap, cap 1.2 (**module default**) | +0.000 (12) | **−0.024** (42) | **+0.125** (32) |
| 0.40, cap 1.5 | −0.031 (32) | −0.049 (41) | +0.054 (93) |
| 0.50, cap 1.8 (the flag's numbers) | +0.000 (61) | −0.013 (77) | +0.017 (113) |
| 0.65, cap 2.4 | +0.042 (95) | +0.012 (169) | +0.045 (111) |
| 0.80, cap 3.0 | +0.000 (95) | +0.052 (114) | +0.054 (55) |
| 1.00, cap 4.0 | +0.000 (54) | +0.014 (69) | +0.086 (35) |
| shipped (zero-order) chainer | **+0.093** (385) | **+0.162** (229) | **+0.068** (266) |

Underlying rates and paired counts for the module-default row (`развилка3.log`):

| stack | pairs | manual | auto | gap | cross (both / manual only / auto only / neither) |
|---|---|---|---|---|---|
| PHerc0191 | 12 | 0.833 | 0.833 | +0.000 | 10 / 0 / 0 / 2 |
| PHerc0358 | 42 | 0.857 | 0.881 | **−0.024** | 36 / 0 / 1 / 5 |
| PHerc1203 | 32 | 0.875 | 0.750 | **+0.125** | 23 / 5 / 1 / 3 |

Read honestly: on PHerc1203 the first-order gap is present at **every** tolerance
(+0.017…+0.125) and the shipped value +0.068 lies inside that spread. On PHerc0191 and
PHerc0358 the first-order chainer comes nowhere near the shipped +0.093 and +0.162 at
any tolerance — the discrepancy there is real and is not explained by tolerance. It is
also not merely "zero": at the three tightest tolerances on PHerc0358 it is negative
(−0.024, −0.049, −0.013), and on PHerc0191 it is −0.031 at 0.40/1.5.

So the correct statement about the module-default first-order chainer is:
**+0.125 on PHerc1203 (28/32 against 24/32), exactly 0.000 on PHerc0191 on 12 pairs,
and −0.024 against us on PHerc0358 on 42 pairs.**

Script-backed: `qc/эвиденс_кандидаты/код/развилка/развилка3.py`, output
`развилка3.json`, log `развилка3.log`. Each run of that script re-asserts the shipped
numbers (354/385 and 318/385, 206/229 and 169/229, 226/266 and 208/266).

### 8.2 Is the fixed run just an "easy" inner subset? No.

Pairs of the **shipped** run were split by the fixed chainer's retention criterion
(`трасса.gate_by_ridge`: a continuous run of ≥30 samples where the arc's tangent agrees
with the lamella direction to within 22° at coherence ≥0.25; a pair is retained if
**both** tracks pass on ≥k common slices):

| stack | all pairs | retained k≥1 | dropped | retained k≥2 | dropped | retained k≥3 | dropped |
|---|---|---|---|---|---|---|---|
| PHerc0191 | +0.094 (385) | +0.036 (83) | +0.109 (302) | +0.037 (27) | +0.098 (358) | +0.111 (9) | +0.093 (376) |
| PHerc0358 | +0.162 (229) | +0.159 (157) | +0.167 (72) | +0.128 (78) | +0.179 (151) | +0.154 (39) | +0.163 (190) |
| PHerc1203 | +0.068 (266) | +0.102 (128) | +0.036 (138) | +0.185 (65) | +0.030 (201) | +0.238 (21) | +0.053 (245) |

On no stack does the margin sit entirely "in the dropped half". On 0358 it is the same
on both subsets; on 1203 it is concentrated on the arcs that provably follow a lamella
(+0.238 on 21 pairs against +0.053 on 245); only on 0191 is there a weak hint in favour
of the "easy subset" hypothesis, and it disappears at k≥3.

The fixed run's pairs do sit at smaller radii (median r from the tracing centre 72.7 vs
87.7 px L3 on 0191, 52.3 vs 60.2 on 0358, 45.6 vs 76.1 on 1203). But restricting the
shipped run to the same radius range (10–90 percentiles of the new set) keeps the gap:
**+0.113 on 204 pairs (0191), +0.120 on 142 (0358), +0.143 on 77 (1203)**.

### 8.3 The 4000-draw resampling test (PHerc0358) — the test that goes against us

Null hypothesis: the fixed chainer's 42 pairs behave like a random 42-pair subsample of
the shipped run's 229 pairs, i.e. the difference between the two runs is a sample-size
artifact. Implementation: draw 42 of the shipped run's 229 per-pair outcomes without
replacement, average the per-pair (manual − auto) difference, repeat 4000 times
(`развилка.py:238-245`, seed 0).

Rendering of `ШАГ2_СОГЛАСОВАННОСТЬ.md:540-544`:

> Small samples do not explain it either: random subsamples of the shipped run at the
> size of the fixed run (4000 draws without replacement) give, on 0358, an expected gap
> of **+0.163** with a 95% band **+0.048…+0.286**, whereas **−0.024** was observed
> (**p < 0.001**) — the difference is real, not noise. On 0191, with 12 pairs, the band
> is −0.083…+0.333, i.e. indistinguishable from noise; on 1203 the observed +0.125 lies
> **above** the expected value (p = 0.92).

All three lines from `развилка.log`:

| stack | subsample size | expected gap | 95% band | observed (fixed chainer) | p(≤ observed) |
|---|---|---|---|---|---|
| PHerc0191 | 12 | +0.093 | −0.083…+0.333 | +0.000 | 0.3167 |
| PHerc0358 | 42 | +0.163 | +0.048…+0.286 | −0.024 | 0.0000 |
| PHerc1203 | 32 | +0.068 | −0.031…+0.156 | +0.125 | 0.9227 |

The subsample sizes (12 / 42 / 32) are the **module-default** first-order pair counts,
not the flag configuration's 61 / 77 / 113.

Interpretation, stated against ourselves: on PHerc0358 the two pipelines disagree by
more than sampling can explain. On PHerc0191 the fixed result is statistically
consistent with the shipped one (it is simply uninformative at 12 pairs). On PHerc1203
the fixed result is, if anything, stronger than the shipped one.

### 8.4 The cause: arc geometry, not pair selection

Decisive control: take the pairs of the **fixed** run (in the flag configuration, to
compare exactly against the flag) and, on the same slices, substitute the nearest
**shipped** arcs of the same physical objects. The pair set and slice set are unchanged
— only the shape of the arcs changes. A substitute is not found for every pair
(12 / 21 / 47 out of 61 / 77 / 113 — itself a fact: the two chainers mostly see
different objects), so the comparison is shown on the same subset:

| stack | subset | fixed arcs | same pairs, shipped arcs |
|---|---|---|---|
| PHerc0191 | 12 pairs | +0.000 (1.000/1.000) | **+0.083** (1.000/0.917) |
| PHerc0358 | 21 pairs | +0.095 (0.952/0.857) | +0.095 (0.762/0.667) |
| PHerc1203 | 47 pairs | +0.000 (0.787/0.787) | **+0.170** (0.660/0.489) |

On 0191 and 1203, with the pair set completely fixed, the gap appears as soon as the
arcs are replaced by shipped ones. So what separates the two runs is not selection of
"easy" pairs but the geometry of the arcs: a shipped arc is a constant-radius fragment
glued from pieces of several sheets, and its mean radius wanders between slices; a
displaced axis flips that wandering more often than a correct one. A first-order arc
follows a single sheet, spans a larger angle (median 318° against 213° on 0191) and
gives a sign so stable that **both** axes preserve it — the metric simply loses its
resolving power on such arcs (0.967/0.967 on 0191).

**On PHerc0358 the substitution does not increase the gap (+0.095 under both
geometries).** That is the residual we cannot explain away, and the working document
says so: the size of the gap depends on what drew the arcs, and it cannot be claimed as
a property of the axes alone.

### 8.5 A repair of the metric that was tried and rejected

The metric drops a pair when an axis cannot determine a sign (`radial_sign` → None with
<5 common angular bins or no dominant sign), and that is the main way the auto-centroid
fails: it stands 13.9 / 14.5 / 8.0 mm from the neutral tracing centre (0191 / 0358 /
1203), i.e. **outside** the 280 px window (half-window 10.5 mm) on 0191 and 0358, while
the manual axis is 2.4 / 1.2 / 3.2 mm from it. Fraction of slices with a defined sign in
the shipped run: manual 0.306 / 0.336 / 0.274 against auto 0.234 / 0.187 / 0.187.

An **unpaired** variant of the metric (candidate = any pair with ≥3 common slices; an
axis succeeds if it determines a sign on ≥3 slices AND the sign is the same) gives the
manual axis the advantage in all nine cells:

| stack | shipped | first-order 0.30/1.2 | first-order 0.50/1.8 (flag) |
|---|---|---|---|
| PHerc0191 | +0.100 (1.54×) | +0.174 (1.67×) | +0.052 (1.20×) |
| PHerc0358 | +0.153 (2.01×) | +0.220 (2.55×) | +0.200 (2.35×) |
| PHerc1203 | +0.101 (1.69×) | +0.116 (1.71×) | +0.112 (1.52×) |

**But this metric fails the swap control, and is therefore unusable.** Re-traced around
each axis:

| stack / chainer | around neutral | around manual | around auto-centre |
|---|---|---|---|
| 0191, shipped | +0.100 | +0.062 | **−0.379** |
| 0191, first-order | +0.052 | +0.068 | **−0.407** |
| 0358, shipped | +0.153 | +0.160 | **−0.431** |
| 0358, first-order | +0.200 | +0.207 | **−0.186** |
| 1203, shipped | +0.101 | +0.118 | **−0.103** |
| 1203, first-order | +0.112 | +0.004 | **−0.016** |

Whichever axis the tracing was done around wins automatically: the arcs are selected to
be star-shaped with respect to it, and a sign from it is determined two to three times
more often. (On 1203 with the first-order chainer there is no reversal, but the manual
axis's advantage there also drops to zero as soon as tracing stops being done around the
neutral centre — i.e. it rested on the manual axis being close to the tracing centre.)
The paired filter "both axes must give a sign", which we wanted to remove, is exactly
what makes the main metric swap-stable. It stays. Recorded as a tried and rejected move.

---

## 9. Null control: does the metric have the resolving power to see this at all?

Prompted by a flag from a separate document: in the PHerc1203 sheet zone the same
pipeline could not see an axis displacement smaller than ~6 mm while the two axes there
differ by only 4.2 mm — that zone's null result was a property of the metric, not of the
axes. So the same control was run on these three stacks.

Method: the pair set is fixed by the manual axis; the known-good manual axis is shifted
by 10/20/40/80/160/320 px L3 (0.75/1.5/3.0/6.0/12.0/24.0 mm) in four directions, and
each candidate is scored on the same slices where the manual axis has a sign (≥3). The
detection threshold is the first shift at which the **median** score over the four
directions moves from the baseline by ≥0.02; in parentheses, the first shift at which
the **worst** direction fails.

| stack | detection threshold | manual↔auto separation in this zone (median / max) | margin | verdict |
|---|---|---|---|---|
| PHerc0191 (z 14520…16440) | **6.0 mm** (worst direction 6.0 mm) | 12.81 / 16.71 mm at anchor points; 13.30 / 16.71 mm over the 25 stack slices | ×2.1 | numbers stand |
| PHerc0358 (z 10688…12176) | **6.0 mm** (worst direction 3.0 mm) | 15.19 / 16.09 mm at anchors; 13.44 / 16.09 mm over slices | ×2.5 | numbers stand |
| PHerc1203 | **3.0 mm** (worst direction 3.0 mm) | 6.59 / 9.16 mm at anchors; 6.75 / 9.16 mm over slices | ×2.2 | numbers stand |

Shift curves — median over the four directions, min–max in parentheses:

| shift of the manual axis | PHerc0191 | PHerc0358 | PHerc1203 |
|---|---|---|---|
| none (baseline) | **0.9195** | **0.8996** | **0.8496** |
| 10 px = 0.75 mm | 0.9229 (0.9184–0.9252) | 0.8980 (0.8969–0.9000) | 0.8504 (0.8488–0.8517) |
| 20 px = 1.50 mm | 0.9198 (0.9171–0.9248) | 0.9014 (0.8972–0.9058) | 0.8500 (0.8361–0.8555) |
| 40 px = 3.00 mm | 0.9144 (0.9066–0.9199) | 0.9032 (0.8571–0.9172) | 0.8286 (0.8200–0.8376) |
| 80 px = 5.99 mm | 0.8805 (0.8705–0.8956) | 0.8402 (0.8280–0.8728) | 0.7993 (0.7358–0.8052) |
| 160 px = 11.98 mm | 0.7616 (0.6810–0.8387) | 0.7154 (0.4359–0.8075) | 0.6915 (0.6813–0.7299) |
| 320 px = 23.97 mm | 0.7875 (0.7333–0.8400) | 0.8061 (0.7500–0.8529) | 0.6341 (0.6136–0.7188) |
| axis frozen at the central slice | 0.9114 | 0.8982 | 0.8471 |
| **auto-centroid (actual)** | **0.8260** | **0.7380** | **0.7820** |

The auto-centroid's score on all three stacks lies between the 6 mm and 12 mm marks of
artificial displacement — where it belongs given an axis separation of 6.6–15.2 mm. The
metric sees the auto-centroid as a displaced axis, not as noise.

The frozen axis is again almost indistinguishable from the live one (−0.008 / −0.001 /
−0.003): the metric does not notice core-tilt tracking. That is a limitation of the
metric and it holds here too.

**Uniform shift versus the centroid's jumps.** A candidate "manual axis plus a rigid
vector equal to the median man→auto separation over the stack" has the same error
magnitude as the centroid but zero non-uniformity:

| stack | rigid equal-size shift | auto-centroid | cost of the jumps |
|---|---|---|---|
| PHerc0191 | 0.8374 (13.17 mm) | 0.8260 | −0.011 |
| PHerc0358 | 0.7630 (12.94 mm) | 0.7380 | −0.025 |
| PHerc1203 | 0.7833 (6.77 mm) | 0.7820 | −0.001 |

Most of the auto-centroid's deficit is explained by the sheer size of its departure from
the core, not by its jumps. The jumps add 0 to 2.5 percentage points on top. The
hypothesis "the numbers rest on local jumps" was not confirmed.

Consequence for the limitations section: the metric's detection threshold is 3–6 mm
depending on the window, so **this metric can say nothing about zones where the axes
differ by less than 3 mm**, and a threshold measured in one window does not transfer to
another window of the same scroll (6 mm in the PHerc1203 sheet zone, 3 mm in the
PHerc1203 packaged stack).

Script-backed: `qc/шаг2_код/нульконтроль/pack_sens.py` (asserts agreement of the pair
selection with `stack.radial_order_metric`), numbers in
`нульконтроль/пакет_чувствительность.json`.

---

## 10. Limitations

- L3 (74.9 µm/px), tracing is fragmentary; absolute winding number is unmeasurable at
  this resolution (§5) — the step-2 claim is about order and only about order.
- The neutral tracing centre is the centre of the window, and the step-1 window was
  built around the manual axis on the central slice of the stack; over the stack the
  manual axis moves 5–9 mm away from that fixed centre, so there is no identity, but
  full independence exists only in combination with the swap control, which is why the
  swap control was run in full.
- Thin slices are normalised by percentiles over the window, catalogue slices over the
  whole frame; the effect on ridge-detection thresholds is small, but must be mentioned.
- Auto-centres are defined on catalogue slices and linearly interpolated between them —
  the way any consumer of the axes uses them; the interpolation smooths the centroid's
  jumps, i.e. it plays **for** the auto-centroid.
- The 0.45-gap matching threshold and the ban on parallel merges make confusing
  neighbouring windings inside a track impossible by construction, but they reduce
  coverage.
- The metric cannot distinguish the axes if both lie inside the innermost winding of the
  window — it catches exactly the case of an axis leaving the windings, which is what
  the auto-centroids do.
- The detection threshold of the metric is 3–6 mm depending on the window (§9).
- **The gap was measured on the shipped (zero-order) tracing. On first-order tracing
  both axes hold pairwise order almost equally well, and the metric is uninformative
  there** (§8) — with the exception of PHerc1203, and with a reversal on PHerc0358 at
  the module-default tolerance.

---

## 11. Corrections applied to the package README

These were errors in the README as it stood before 2026-08-13, found by re-reading this
evidence against the published text. **All five are corrected in the README that ships
with this repository.** They are listed here, with the wrong wording quoted, so that a
reviewer can check the correction instead of taking it on trust.

1. **"the manual axis never loses"** — false as stated. It loses on PHerc0358 under the
   first-order chainer at the module default (−0.024, 42 pairs) and at 0.40/1.5 (−0.049,
   41 pairs), and on PHerc0191 at 0.40/1.5 (−0.031, 32 pairs). In the swap control it is
   one pair behind on PHerc0358 traced around the auto-centre (130 vs 131 of 143).
   The README now prints the full tolerance sweep, the resampling test and the losing
   swap cell instead of that sentence, and makes only this claim: *on the shipped
   zero-order pipeline, split by lamella-following retention and by radius belt, the
   manual axis's advantage is non-negative in every cell; in the nine swap cells it is
   ahead in six, level in two and behind in one; and under an alternative first-order
   chainer the advantage survives only on PHerc1203.*

2. **"loses order 3–8× more often (43:7, 42:5, 21:3)"** — those three ratios are 6.1,
   8.4 and 7.0, i.e. **6–8×**. The only place in the evidence where a ratio below 6
   appears is the circle-replacement control of §7, whose counts are 47:7, 38:5 and
   19:5, and 19/5 = 3.8. That control is a different run and the README sentence does
   not mention it. The README now writes 6.1–8.4× for the cited counts and attributes the
   3.8 to the circle control.

3. **"+0.13, and it concentrates on arcs that provably follow a lamella, up to +0.29 in
   the core"** — the +0.13 is a rounding of the module-default first-order result on
   PHerc1203, **+0.125** on 32 pairs (§8.1); that is correct. But **+0.29 is not a
   first-order-chainer number**: +0.294 (17 pairs) is the r 0–60 lamella-held subset of
   the **shipped zero-order** run (§7), and the neighbouring +0.238 (21 pairs) is the
   k≥3 retained subset of the shipped run too. The old sentence attributed
   shipped-pipeline subset numbers to the first-order chainer; the README now attributes
   them correctly.

4. **"is not reproduced on 0191/0358 at any chaining tolerance"** — true as far as it
   goes, but it reads as "the effect vanishes". What the sweep actually shows is that on
   0358 the sign **reverses** at the three tightest tolerances (−0.024, −0.049, −0.013)
   and on 0191 at one (−0.031). The README now says reversed, not absent.

5. **"robust across every reliable subset"** — the phrase "reliable subset" is **not
   defined anywhere** in the evidence, mechanically or otherwise. The README no longer
   uses it and states the mechanical split instead. See §12.

---

## 12. What "reliable subset" does and does not mean

The working document uses the phrase "on no RELIABLE subset of the shipped run does the
manual axis's advantage disappear — including pairs that provably follow a lamella
(+0.154 on 39 pairs of 0358, +0.238 on 21 pairs of 1203)"
(`ШАГ2_СОГЛАСОВАННОСТЬ.md:666-669`).

**There is no mechanical definition of "reliable subset" in the document.** No minimum
pair count, no threshold, no rule for which subsets count. This is a finding, not an
omission we are patching over: the README's former "every reliable subset" inherited an
undefined term, which is why the phrase was removed rather than defended.

What *is* defined mechanically, and can be used instead:

- **Pair admission to the metric** (`stack.py`): ≥5 common angular bins per slice, ≥80%
  of bins agreeing on the sign, and both axes with a defined sign on ≥3 common slices.
  This is the only filter that all the headline numbers pass through.
- **Lamella-following retention** (`трасса.gate_by_ridge`): a continuous run of ≥30
  samples where the arc's tangent agrees with the structure-tensor lamella direction to
  within 22° at coherence ≥0.25; a pair is retained if both tracks pass on ≥k common
  slices, with k ∈ {1, 2, 3} tabulated in §8.2.
- **Radius belts** from the tracing centre (§7), and the degenerate belt r > 140 px L3
  identified by the circle-agreement measurement.

If the README needs the sentence, the honest form is: *"across the shipped pipeline's
pairs, split by lamella-following retention at k = 1, 2, 3 and by radius belt, the
manual axis's advantage is **non-negative** in every cell that carries enough pairs to
report — positive in all of them but one, PHerc1203's degenerate belt (r > 140 px L3,
14 pairs), where it is exactly +0.000; PHerc0191's innermost lamella-held subset has no
pairs at all and PHerc0358's degenerate belt has four, and neither is counted in our
favour"* — which is what §7 and §8.2 show, and which says nothing about the first-order
chainer, where it is not true. An earlier draft of this paragraph said "positive in
every cell", which the +0.000 in the §7 table above contradicts; this is the wording the
README carries.

---

## 13. Provenance — what is scripted and what is not

| number set | source | ships in the package? |
|---|---|---|
| Headline rates, cross-tables, all 9 swap rows (§4, §6) | `qc/шаг2_метрики.json`, produced by `qc/шаг2_код/stack.py` | **no** — of the step-2 material the package ships this document and the six panels, not the metrics json or its producer. (An earlier version of this cell said the package ships "only the umbilicus JSONs, the README and PNG panels"; it also ships this file, `qc/validation_raw.json` and nine scripts.) |
| Null control, shift curves, rigid-shift comparison (§9) | `qc/шаг2_код/нульконтроль/pack_sens.py`, `пакет_чувствительность.json`, log | no |
| Tolerance sweep, module-default first-order numbers (§8.1) | `qc/эвиденс_кандидаты/код/развилка/развилка3.py`, `развилка3.json`, `развилка3.log` | no |
| Retention split, radius belts, resampling test (§8.2, §8.3) | `развилка.py` + `развилка.log` (the run's `развилка.json` is **not present** in the tree) | no |
| Unpaired metric and its swap control (§8.5) | `развилка5.py`, `развилка6.py` and their logs | no |
| Arc substitution on a fixed pair set (§8.4) | `развилка4.py`, `развилка4b.log` | no |
| Structure-tensor chainer diagnostic (§7 angle table) | **unscripted in the tree** — run from a session scratch directory; only the document and `qc/эвиденс_кандидаты/ПОЧИНКА.md` record it | no |
| Circle-replacement control (§7) | **unscripted in the tree** — `scratchpad/контроль_окружности.py`, session scratch directory | no |
| Flag configuration 0.50/1.8 (61/77/113 pairs) | **not in the module** — a one-off session script; reproducible only by overriding `trace_sheets_fixed`'s hard-coded cap | no |

Any reviewer wanting to re-run the shipped-pipeline numbers needs `qc/шаг2_код/stack.py`
plus the thin-slice cache; the shipped-number asserts inside `pack_sens.py` and
`развилка3.py` (354/385 and 318/385, 206/229 and 169/229, 226/266 and 208/266) fire on
every run of those scripts and have never failed.

---

## 14. Internal inconsistencies in the source document

Listed so that a reviewer who finds them knows we found them too.

- The shipped-pipeline gap on PHerc0191 is written **+0.094** in three places
  (`:437`, `:486`, `:512`) and **+0.093** in the sweep table (`:574`) and the log. The
  underlying rates are 0.9195 and 0.8260, difference 0.0935; both roundings appear.
  Same for PHerc0358: **+0.162** (rates 0.900 − 0.738 = 0.162) is used consistently.
- The flag's PHerc1203 number is written **+0.018** in the prose (`:439`, `:557`) and
  **+0.017** in the sweep table (`:570`). The log gives 0.805 − 0.788 = +0.017.
- The document's opening summary (`:11-16`) says the manual axis "preserves the order of
  pairs of physical sheets" — superseded by the retraction at `:461-464` (§7). The
  opening line was never rewritten. Throughout this file the wording is "traced arcs".
- The PHerc1203 z-range is deliberately withheld in the data table (`:24`) and printed
  in the null-control table (`:233`). This file follows the withholding; whether to
  publish the range is a separate decision.

---

## 15. Bottom line

On the shipped tracing pipeline, with tracing independent of both axes under test, the
manually annotated umbilicus preserves the pairwise winding order of traced arcs between
heights better than the auto-centroid on all three scrolls (0.919/0.900/0.850 against
0.826/0.738/0.782), with paired counts of 43:7, 42:5 and 21:3; it sits a factor of
2.1–2.5 above the metric's measured detection threshold. Under the three-way swap
control it does not reverse on eight of the nine cells — ahead in six, exactly level in
two — and on the ninth, PHerc0358 traced around the auto-centre, it is one pair of 143
behind (0.909 against 0.916). Split by lamella-following retention and by radius belt it
is non-negative in every cell that carries enough pairs to report, positive in all but
one (+0.000 on PHerc1203's degenerate r > 140 belt, 14 pairs), with two cells too sparse
to report at all. Earlier drafts of this paragraph said "survives the full three-way
swap control" and "present in every subset"; §1 bullet 4 and the §7 table contradict
both, and the counts above replace them.

Under an alternative, provably sheet-following first-order chainer the effect is
reproduced only on PHerc1203 (+0.125 at the module's default tolerance, 28/32 against
24/32); on PHerc0191 it is exactly zero on 12 pairs, and on PHerc0358 it reverses to
−0.024 on 42 pairs, a reversal that a 4000-draw resampling test says is not explained by
sample size (p < 0.001). The demonstrated reason is that first-order arcs give a sign so
stable that both axes preserve it, i.e. the metric loses resolving power — shown by
substituting arc geometries on a fixed pair set (+0.000 → +0.083 on 0191, +0.000 →
+0.170 on 1203) — but that explanation does not cover PHerc0358, where substituting the
geometry does not change the gap (+0.095 either way).

Therefore: the **direction** of the result is robust on the shipped pipeline and on
PHerc1203 under both pipelines; the **size** of the gap is pipeline dependent; and the
claim "the manual axis never loses" is not one this evidence supports without the
qualifier "on the shipped pipeline".
