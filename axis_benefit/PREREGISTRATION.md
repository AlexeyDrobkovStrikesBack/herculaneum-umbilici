# Pre-registration — does an annotated umbilicus axis beat a straight vertical axis?

**Written 13 August 2026, 17:35 local, before any comparative quantity was computed.**
This file is the specification. It is fixed at the moment of writing. Everything reported in
`AXIS_BENEFIT_PREREG_2026-08-13.md` follows from it, including a null result.

## 0. Why this exists

The run of earlier today (`AXIS_BENEFIT_DEMO_2026-08-13.md`) found the annotated axis ahead of
the straight stick on 7 of 10 slices of two scrolls, mean 0.138 vs 0.084 (1.65x), Wilcoxon
p = 0.037 — **but the annulus rule that produced it was adopted after a first rule returned a
null** (5 of 8, p = 0.25). That is a forking path, and the author declined to quote the number.
This document fixes the rule, the sampling, the statistic and the failure criterion in advance,
so that whatever comes out is quotable.

## 1. What was already known when this was written (and therefore is not being decided by it)

- Both annulus rules and both of their outcomes (§4, §5.1, §5.2 of the earlier document).
- The displaced-axis control degraded the score on 8 of 8 slices out to ~7 mm, and was flat
  below ~100 px (~1.7-1.9 mm).
- Two PHerc0813 annotations, near z = 6500 and z = 9000, look wrong and score near zero.
- The measure locates the true umbilicus on intact Scroll 1 (validation figure).

The rule adopted below (§5) is the *second* of the two earlier rules, the equal-evidence
annulus. It is chosen here on its stated merits — an axis near the scroll's edge is otherwise
scored on a truncated crescent while a central one is scored on a whole ring, which penalises
position rather than correctness — and it is now being applied to **new slices** (30 per scroll
across all ten scrolls; only 4 of the 300 slices below were scored by the earlier run). The
earlier two-scroll, ten-slice result does not enter the analysis in any way.

## 2. Tooling — frozen, not to be changed mid-experiment

- **Axis placement**: `umbilicus.json_umbilicus_z_to_yx`, villa's own loader, imported
  unmodified from `<villa-checkout>/volume-cartographer/scripts/spiral/`, called
  with `downsample_factor=2` (pyramid level 1). This is the loader `fit_spiral.py:137` calls.
- **Winding parameterisation**: `sample_spiral.get_theta_and_radii`, villa's own, unmodified,
  used for the secondary phase-concentration check (§9).
- **Scoring code**: `_axisdemo/axisdemo.py` as it stands at the time of writing
  (`radial_anisotropy_sectored`, `common_outer_radius`, `ring_inside_fraction`,
  `papyrus_mask`, `phase_concentration`). No edits to the scoring functions are permitted
  after this file is written.
- **Two implementation-only changes**, both verified equal to what they replace before this
  file was written, neither touching the definition of any measured quantity:
  1. `zslice_http.py` streams the z-plane over anonymous HTTPS range GETs instead of via
     `s3fs`, so the whole experiment runs in the one interpreter that also has torch (and so
     can import `sample_spiral`). **Verified byte-identical** to the `s3fs` path on
     PHerc0813 L1 z = 2000.
  2. `tiled_st.structure_tensor_tiled` computes the structure tensor tile-wise with a 64 px
     halo and returns it already subsampled, because this machine has 12 GB of RAM with ~1.5 GB
     free and the whole-frame float32 tensor of a 6073^2 slice does not fit. **Verified
     bit-identical** (max abs difference 0.0 in all three components) to
     `axisdemo.structure_tensor` on a 2000^2 real-slice region.
- `fit_spiral.py` itself cannot run on this machine (no CUDA, Python 3.12 vs required 3.14, no
  prepared spiral dataset). This experiment is therefore a proxy for what the fitter sees, and
  says so wherever it is reported. Nothing about that changes here.
- `<work>/umbilici_repo` is read-only for this work.

## 3. Data

Level 1 of each scroll's masked OME-Zarr in the open bucket, one volume per scroll (for
PHerc1203, the 9.362 um volume — the 2.403 um volume covers a different, small z range and the
annotation is not on it). Level 1 is 2x the native voxel: 17.28 um/px for the 8.640 um scrolls,
18.72 um/px for the 9.362 um scrolls. Slices are streamed and discarded; nothing is cached to
disk (the disk is at 86 %).

| scroll | volume | um/voxel (L0) | L1 shape | annotated z-range (L0) |
|---|---|---|---|---|
| PHerc0191 | 20250821151635-9.362um-1.2m-113keV-masked.zarr | 9.362 | 9489x4194x4194 | 3496-17880 |
| PHerc0257 | 20250821151750-9.362um-1.2m-113keV-masked.zarr | 9.362 | 9436x4194x4194 | 2888-17176 |
| PHerc0268 | 20251110183117-8.640um-1.2m-116keV-masked.zarr | 8.640 | 7417x6073x6073 | 5320-12584 |
| PHerc0358 | 20250821151737-9.362um-1.2m-113keV-masked.zarr | 9.362 | 7372x3892x3892 | 1768-12920 |
| PHerc0800 | 20250521135224-8.640um-1.2m-116keV-masked.zarr | 8.640 | 12149x4934x4934 | 4256-20760 |
| PHerc0813 | 20250821151723-9.362um-1.2m-113keV-masked.zarr | 9.362 | 8497x3974x3974 | 2600-15992 |
| PHerc1203 | 20250820131727-9.362um-1.2m-113keV-masked.zarr | 9.362 | 9489x3422x3422 | 2320-17840 |
| PHerc1218 | 20250521120456-8.640um-1.2m-116keV-masked.zarr | 8.640 | 11624x3797x3797 | 3432-21144 |
| PHerc1447 | 20250521151220-8.640um-1.2m-116keV-masked.zarr | 8.640 | 12149x4172x4172 | 2944-22112 |
| PHerc1545 | 20250821151648-9.362um-1.2m-113keV-masked.zarr | 9.362 | 10481x3753x3753 | 2544-17960 |

**All ten scrolls are in. No scroll may be dropped for any reason discovered after this file
was written.**

## 4. Slice sampling — a fixed rule, nothing hand-picked

Per scroll, **30 slices**, evenly spaced over that scroll's annotated z-range with both
endpoints included:

> `z_k = round(z_min + k * (z_max - z_min) / 29)` for `k = 0..29`, then decremented by 1 if odd
> (so that the level-1 index `z_k / 2` is exact). `z_min`, `z_max` = the z of the first and
> last annotated control point.

300 slices total. The full list is produced by `_axisdemo/zlist.py` and is frozen here:

```
PHerc0191 3496 3992 4488 4984 5480 5976 6472 6968 7464 7960 8456 8952 9448 9944 10440 10936 11432 11928 12424 12920 13416 13912 14408 14904 15400 15896 16392 16888 17384 17880
PHerc0257 2888 3380 3872 4366 4858 5350 5844 6336 6830 7322 7814 8308 8800 9292 9786 10278 10770 11264 11756 12248 12742 13234 13726 14220 14712 15204 15698 16190 16682 17176
PHerc0268 5320 5570 5820 6070 6322 6572 6822 7072 7324 7574 7824 8074 8326 8576 8826 9076 9328 9578 9828 10078 10330 10580 10830 11080 11332 11582 11832 12082 12334 12584
PHerc0358 1768 2152 2536 2922 3306 3690 4074 4460 4844 5228 5614 5998 6382 6766 7152 7536 7920 8304 8690 9074 9458 9844 10228 10612 10996 11382 11766 12150 12534 12920
PHerc0800 4256 4824 5394 5962 6532 7102 7670 8240 8808 9378 9946 10516 11084 11654 12222 12792 13362 13930 14500 15068 15638 16206 16776 17344 17914 18484 19052 19622 20190 20760
PHerc0813 2600 3062 3524 3984 4446 4908 5370 5832 6294 6756 7218 7680 8142 8602 9064 9526 9988 10450 10912 11374 11836 12298 12758 13220 13682 14144 14606 15068 15530 15992
PHerc1203 2320 2854 3390 3926 4460 4996 5530 6066 6600 7136 7672 8206 8742 9276 9812 10348 10882 11418 11952 12488 13022 13558 14094 14628 15164 15698 16234 16770 17304 17840
PHerc1218 3432 4042 4654 5264 5874 6486 7096 7706 8318 8928 9540 10150 10760 11372 11982 12592 13204 13814 14426 15036 15646 16258 16868 17478 18090 18700 19312 19922 20532 21144
PHerc1447 2944 3604 4266 4926 5588 6248 6910 7570 8232 8892 9554 10214 10876 11536 12198 12858 13518 14180 14840 15502 16162 16824 17484 18146 18806 19468 20128 20790 21450 22112
PHerc1545 2544 3076 3606 4138 4670 5202 5734 6264 6796 7328 7860 8390 8922 9454 9986 10518 11048 11580 12112 12644 13176 13706 14238 14770 15302 15834 16364 16896 17428 17960
```

## 5. The conditions

Every condition sees the **same slice, the same annulus, the same structure tensor, the same
smoothing scales, the same sector binning and the same seed**. Only the axis differs.

- **A — annotated.** Our per-slice axis, placed by villa's loader.
- **B1 — straight stick at the annotation mean.** The mean of the annotated control points in
  (y, x), held constant in z. This is the strongest possible straight baseline and is the
  **primary** comparator.
- **B2 — straight stick at the volume centre.** `(H/2, W/2)`, what you get with no umbilicus at
  all. Secondary comparator, reported but not the headline.
- **C — control.** A displaced by `d` in {25, 50, 100, 200, 400, 800} level-1 px in each of the
  four axis-aligned directions (§8).

## 6. The annulus rule — fixed here, applied everywhere

**Equal-evidence annulus.** Per slice, `r1` is the largest radius in the descending sweep
`2000, 1975, ..., 400` at which **each of A, B1 and B2** sees a circle that is at least 95 % on
the scroll (`ring_inside_fraction >= 0.95` sampled at 360 points, "on the scroll" = the masked
volume's non-air mask, `img > 0`). Then `r0 = round(0.25 * r1)`. All conditions on that slice
are scored on exactly that annulus. This is `axisdemo.common_outer_radius` with its published
defaults, with the one change stated in §7.

## 7. Scorable slices, and what happens when coverage is inadequate — decided now

A slice is **scorable** iff both:

1. a common annulus exists — i.e. some `r` in [400, 2000] satisfies the 95 % rule for **all
   three** of A, B1, B2; and
2. all three of A, B1, B2 return a finite `q` on it (that is, at least 90 % of the 72 sectors
   carry papyrus over at least a quarter of the annulus, and at least 1000 pixels are in it).

Otherwise the slice is **non-scorable** and is excluded from the primary analysis. The exclusion
rule is symmetric across conditions by construction: it is a joint requirement on all three
axes, never a per-axis one, and a slice cannot be dropped for the annotated axis alone while a
stick keeps it. `common_outer_radius`'s silent fall-back to `r_min = 400` is replaced by
returning "no valid annulus" — a fall-back annulus that satisfies nobody's coverage would be
exactly the confound this rule exists to remove.

**Every non-scorable slice is counted and reported**, with which of the three axes failed. To
bound any residual bias from exclusion, a pre-registered worst-case check (§10.3) recounts the
scroll-level sign test with every non-scorable slice charged to the annotated axis as a loss.

**A slice with a visibly bad annotation is NOT excluded.** In particular the PHerc0813 slices
near z = 6500 and z = 9000, already known to score near zero, stay in the primary analysis.
Nothing may be excluded on the basis of how it looks or how it scores.

## 8. The measure

`axisdemo.radial_anisotropy_sectored` with its published defaults, unchanged:
`n_sectors = 72` (5 degrees), `min_sector_frac = 0.25`, `min_valid_sectors = 0.90`,
structure tensor `sigma_d = 1.5`, `sigma_t = 6.0`, subsampling `SUB = 2` (as in the earlier
primary run; the subsampling effect was measured there at |dq| < 3e-4 and is re-verified once
here on one slice and reported).

> **q = sum (u'Ju - t'Jt) / sum trace(J)**, averaged with equal weight per 5-degree sector,
> over the non-air pixels of the annulus, where u is the unit radial and t the unit tangential
> direction about the candidate axis.

q = +1 means every sheet crosses every ray at right angles — the sheets are the circles villa's
spiral model assumes; q = 0 no preference; q < 0 sheets running radially. The structure tensor
does not depend on the axis and is computed once per slice, so every condition is scored on
identical image evidence.

## 9. Secondary measure, reported but not part of the verdict

`phase_concentration` (villa's `get_theta_and_radii`, dr swept over 4.0..30.0 step 0.5
independently per axis, 100 px bands, at most 400 000 pixels, seed 0) for A, B1, B2 on every
slice. The earlier run found it at the noise floor for every axis; this re-checks that on ten
scrolls. **It cannot change the verdict** either way.

## 10. The analysis — statistic, test, and what counts as failure

### 10.1 Primary

- Per scroll `s`: **Delta_s = mean over that scroll's scorable slices of (q_A - q_B1)**.
- **Primary test: two-sided Wilcoxon signed-rank over the ten scroll-level Delta_s, n = 10,
  alpha = 0.05.** The scroll is the unit of analysis, because slices within a scroll are not
  independent.
- Reported alongside, descriptively: the pooled means of q_A and q_B1 over all scorable slices,
  their ratio, the per-scroll means, and the number of scrolls with Delta_s > 0.

### 10.2 The pre-registered verdict rule

> **The claim "our annotated axes measurably beat the straight vertical axis" is made only if
> BOTH: (a) the primary Wilcoxon p < 0.05 two-sided, AND (b) Delta_s > 0 on at least 6 of the
> 10 scrolls.**
>
> **If either fails, the result is null, the claim is not made, and it is not submitted.**
> A significant p with the effect in the *negative* direction is reported as evidence that the
> annotated axis is *worse*, not as a null.

No third variant will be run in search of significance. If, after seeing the result, a
different rule looks better, it will be stated as a hypothesis for a fresh pre-registration and
**not** reported alongside as a result.

### 10.3 Secondary analyses — declared now, labelled as secondary wherever they appear

1. The same test against B2 (volume-centre stick).
2. Slice-level two-sided Wilcoxon over all pooled scorable slices, and the slice-level sign
   test. Both are anticonservative because of clustering within scrolls; that is why they are
   not primary.
3. **Worst-case exclusion check**: scroll-level sign test in which every non-scorable slice is
   charged to the annotated axis as a loss.
4. Per-scroll win counts at slice level.

### 10.4 Control and sensitivity floor (carried forward from the earlier run)

On slices `k` in {0, 5, 10, 15, 20, 25} of the 30 — 6 per scroll, 60 in all — condition C is
scored at each displacement `d` and direction, keeping only displaced centres whose ring at r1
still has >= 95 % coverage and whose q is finite, and averaging over the surviving directions.

> **Sensitivity floor := the smallest d for which the median over control slices of
> (q_A - q_d) is at least 0.01**, reported in mm using each scroll's own level-1 voxel size.

The floor is reported in the body of the report next to the primary result, not in a footnote,
because it bounds what any demonstration of this shape can ever claim.

### 10.5 Post-hoc, declared in advance, and never the headline

The two PHerc0813 annotations near z = 6500 and z = 9000. The primary result keeps them as they
are. Separately, and labelled post-hoc:

- the offending control points are re-placed **by eye on the rendered slice, without reference
  to q**, in a *copy* of the umbilicus JSON inside `_axisdemo/` (`umbilici_repo` is not
  touched); PHerc0813's 30 slices are re-run with the corrected copy; the changed Delta_0813
  and the changed primary test are reported as **post-hoc**;
- and, as a strict and explicitly circular upper bound, the same with those points placed at
  the q-argmax.

Neither number may be presented as the pre-registered result.

## 11. Compute discipline

`load_status.txt` is read before every slice. The runner pauses while `load` exceeds 1.25x cores
(the gate's own THROTTLE threshold) or `MemAvailable` is below 1.2 GB. The gate's memory limb
also reports THROTTLE whenever available memory is under 2.0 GB, which on this machine is a
standing condition caused by another application holding ~8 GB, not by this job; the runner
therefore self-limits on the 1.2 GB floor and on the load threshold, and its own peak RSS is
held under ~450 MB per process by the tiled structure tensor. At most two scroll processes run
at once, 2 torch threads each. No slice is written to disk. The GUI is not touched;
`monitor_server.py` is not edited; nothing is published.

---

*Fixed 13 August 2026, 17:35. Any deviation from this document that proves unavoidable will be
recorded, with its reason, in the report — and the pre-registered number will be reported
regardless.*
