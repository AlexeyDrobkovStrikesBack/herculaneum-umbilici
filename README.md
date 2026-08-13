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

## Method
Manual annotation on ~31 axial slices per scroll (small web annotator with
auto-suggested centers, triplanar side views and winding-ring overlays;
khartes `exp-2025-08-01` used to cross-check ambiguous spots). Untouched
auto-suggestions were dropped at finalization — polylines interpolate
between human-confirmed points only. The axes are far from vertical: the
deviation from a vertical line through each scroll's mean center reaches
20.7 mm (PHerc0268; full lateral sweep of that axis is 37.9 mm) — a straight
"stick" axis misses the true core by up to two centimeters.

## Validation (scripts included for every number except one, marked)
- **Winding-order test, swap-controlled** (the practical one): sheets are
  traced around a fixed neutral center (independent of either axis), matched
  across slices geometrically, and the pairwise winding ORDER from each axis
  is compared between neighboring heights. Our axes preserve sheet order
  across height on 85–92% of pairs vs 74–83% for the auto-centroid; in
  paired counts the centroid loses order 3–8× more often (43:7, 42:5, 21:3
  on PHerc 0191/0358/1203). The full swap control (re-tracing around either
  axis) never reverses the result. Strict absolute winding numbering is
  unresolvable at L3 preview resolution for either axis — stated honestly.
  See `panels/step2_*`. Two caveats we found ourselves and would rather state than
  have you discover: (a) what is matched across heights are *traced papyrus
  arcs*, not verified single sheets — beyond the core our chaining can hop
  between neighbouring laminae, so read the numbers as arc order, not sheet
  identity; (b) the *size* of the gap is tracing-pipeline dependent — with
  a stricter first-order chainer the same gap holds on PHerc1203 (+0.13,
  and it concentrates on arcs that provably follow a lamella, up to +0.29
  in the core) but is not reproduced on 0191/0358 at any chaining
  tolerance. What is robust across every reliable subset of the shipped
  pipeline, including provably lamella-following arcs, is the direction:
  the manual axis never loses. Sensitivity, null-control and subset tables
  are in `ШАГ2_СОГЛАСОВАННОСТЬ.md`.
- **Shifted-axis control** across 297 annotated slices: a banded-energy
  measure favors our axes over deliberately shifted ones (+300 vox) on
  184/297 slices, p=2.3e-05 collectively; individually significant on
  PHerc0191, 0813, 1203, 1218. L3 preview resolution (winding pitch ~3 px)
  limits per-scroll power.
- **Calibration against sean's three published umbilici** (0125/0211/0826):
  same ring-symmetry gates — median displacement ours 265 vox vs sean's 274.
  On polyline smoothness sean's axes are 2–6× smoother than our two earliest
  scrolls (0191, 0268); our later scrolls match his range.
- **Independent track on PHerc0358**: its core is filled with dense sediment
  (bright in CT); auto-tracking that plug confirmed 19/22 trackable points
  within 11–93 vox (journal-documented spot check, not scripted).

## Honest caveats
- Collapse zones (chevron-folded interiors) are best-effort judgement;
  PHerc0268 is crushed almost throughout.
- Bare edges: PHerc0268 bottom ~2950 vox, PHerc1545 top ~1620 vox,
  PHerc0800 and PHerc1218 edge stretches >1000 vox carry no axis; interior
  gaps after finalization do not exceed ~2400 vox.
- Three slices excluded as undeterminable (PHerc1545 z=19056; PHerc0191
  z=15960, z=16440).
- Winding pitch measured at readable spots is 250–370 µm (locally separated
  sheets); tightly wound regions sit at the L3 Nyquist limit.
- The shifted-axis control ran on a snapshot slightly older than the final
  files: 18/297 slices carry points that were later dropped at finalization,
  and three PHerc1545 points were moved (≤260 vox) after the control run.
  Winding-map numbers were computed on the final files.

## Files
- `PHercNNNN_umbilicus.json` × 10 — the axes.
- `panels/axis_PHercNNNN.png` — each axis drawn on its scroll.
- `panels/step2_stack_*.png`, `panels/step2_points_*.png` — the winding-order
  test on PHerc 0191, 0358 and 1203.
- `panels/calibration_summary.png` — our gates calibrated against sean's three
  published umbilici.
- `scripts/` — QC gates, finalization, and the validation scripts behind the
  numbers above (`qc_gates.py`, `finalize.py`, `validate_axes.py`,
  `validate_bands.py`, `calib_sean.py`, `qc_sheet.py`).

The annotator itself is a small web page; happy to share it on request.
