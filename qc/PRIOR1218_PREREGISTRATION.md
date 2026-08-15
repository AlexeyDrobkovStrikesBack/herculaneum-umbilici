# Pre-registration: comparing our PHerc1218 axis against the prior annotation

Written **before** any comparative quantity between the two files existed, on
2026-08-15. The sha256 of this file was recorded before
`scripts/prior_1218.py` was first run, so that the interpretation below cannot
have been chosen after seeing the answer. That hash is reported in the README
section this specification belongs to (§7).

## Why this comparison exists

Every other check in this package compares our axes against a control we built
ourselves (a shifted axis, a straight stick, an auto-centroid), or against
sean's three files on *other* scrolls. None of them is an independent
annotation of one of *our* ten. On PHerc1218 there is one:
`data/spiral_input_pherc1218/umbilicus.json` in
[IyanDopico/vesuvius-sheet-tools](https://github.com/IyanDopico/vesuvius-sheet-tools),
committed `6a831e0` on 2026-07-21, three weeks before ours. It is the only
place in this package where a reader can check us against someone who is not
us.

## The two quantities are not defined to be the same point

This must be stated before the numbers, because it decides what they can mean.

- **Ours** is a hand-placed winding centre: a human looked at a CT cross-section
  and put a point where the spiral turns close on themselves.
- **Theirs** is the **centroid of the papyrus mask** of each slice —
  `scripts/constraints/make_umbilicus.py` composites the nonzero-label mask of
  their own instance segmentation, takes `ys.mean(), xs.mean()` of that mask,
  smooths the z→(y,x) series with a 5-sample running median, and scales L1→L0.

For a cross-section whose papyrus is distributed symmetrically about the
winding centre these two coincide. For a cross-section that is crushed, torn,
partly outside the mask, or simply has more material on one side, they do not,
and the gap is a property of the *scroll*, not an error in either file. So this
is not a ground-truth comparison in either direction, and no result below will
be reported as one file being right and the other wrong.

## What is computed

Both files index level-0 voxels of the same volume,
`PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr`
(grid 23247 × 7593 × 7593 at 8.640 µm — to be confirmed against the bucket,
and against the `FULL_Z = 23247` / `FULL_YX = 7593` constants hard-coded in
their generator). If that turns out to be false the comparison is void and the
frame difference is reported instead of a distance.

1. The overlapping z range of the two polylines.
2. Both polylines evaluated on a common z grid inside that overlap — their own
   sampling, which is the denser of the two — with linear interpolation in z,
   the interpolation villa's own consumer `json_umbilicus_z_to_yx` performs.
3. `d(z) = hypot(Δy, Δx)` in level-0 voxels and in millimetres.
4. The **distribution** of `d`: min, quartiles, median, 90th percentile, max,
   and the z at which the max occurs — not a single number.
5. The signed `(Δy, Δx)` separately, and `d` recomputed after removing the
   best constant offset, which separates "the two axes sit in slightly
   different places" from "the two axes have different shapes".

## The yardsticks, fixed now

The package already publishes three distances, and the verdict is expressed
against them rather than against a number invented for this section:

| yardstick | value | where |
|---|---|---|
| sensitivity floor of the pre-registered §6 run | **1.81 mm** | §6.4 |
| median distance from the annotated axis to the straight stick it beats | **6.0 mm** | §6 |
| the headline "a straight line is not a substitute" deviation | **20.7 mm** | Motivation, PHerc0268 |

**Bands, fixed before the run:**

- **median d < 1.81 mm** — the two axes are closer than the resolution of this
  package's own downstream benefit test. They are interchangeable for it.
- **1.81 mm ≤ median d < 6.0 mm** — the two independent annotations differ by
  less than the effect §5/§6 claim to measure. Reported as agreement at the
  scale that matters, with the residual named.
- **6.0 mm ≤ median d < 20.7 mm** — the disagreement is the size of the effect
  this package claims. It has to be explained, not absorbed; the README says so
  in the same words wherever the §6 result is quoted.
- **median d ≥ 20.7 mm** — the two files disagree by more than the number the
  Motivation section is built on. In that case the honest action is to say the
  comparison failed and to withhold the framing that a per-slice axis is
  well-determined on this scroll until it is understood.

## What agreement would mean

That two annotations of PHerc1218 produced by different people, from different
inputs — a human reading CT cross-sections versus the centroid of an automatic
instance segmentation — land on the same line. That is evidence that both are
tracking a real feature of the scroll rather than the idiosyncrasies of one
method, and it is the only such evidence in this package.

It would **not** show that either file is correct. Both methods can share a
bias: on a scroll whose cross-sections lean consistently to one side, a human
eye and a mass centroid can be pulled the same way. Agreement would also carry
one extra statement, about the scroll and not about the annotations: that
PHerc1218's cross-sections are close enough to symmetric that the papyrus
centroid is near the winding centre.

## What disagreement would mean

By itself, **not** that either file is wrong — see the definition paragraph
above. Three shapes of disagreement are distinguished, and which one occurs is
the finding:

- **A roughly constant offset** (the bulk of `d` removed by subtracting one
  vector): a convention or frame difference — a different centre definition, a
  half-voxel or level convention, an origin offset. Reported as a convention
  finding, not as annotation error.
- **A z-dependent disagreement, largest where the scroll is most damaged or
  where their label coverage is thinnest**: the centroid-versus-centre gap
  opening exactly where a cross-section stops being symmetric. This is the
  outcome the definition paragraph predicts, and it says the centroid is not a
  drop-in for a hand-placed axis on asymmetric slices.
- **A disagreement comparable to or larger than the scroll's radius, or one
  that grows without bound in z**: this would indicate an actual error, and the
  next step would be to find which file it is in — for which the tie-breaker is
  the CT itself, not either polyline.

## What this comparison cannot do

It cannot make either file ground truth, it covers one of ten scrolls, and it
covers only the z range both files span. Nothing here licenses a claim about
the other nine.
