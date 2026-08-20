# Result: the finer displacement ladder — the floor is 2.72 mm

20 August 2026. Run under `FLOOR_FINEGRID_PREREG_2026-08-20.md`, which was
written and committed before any of these numbers existed. The published
repository was not written to.

## Validation first: the original rule reproduces

Before reading the new ladder, the pre-registered rule was recomputed twice — on
the shipped files and on the new control-only run — and it returns its published
answer both times.

| rule | files | floor |
|---|---|---|
| pre-registered ladder | shipped `umbilici_repo/axis_benefit/prereg_*.json` | **200 px = 3.63 mm** |
| pre-registered ladder | new fine-ladder files | **200 px = 3.63 mm** |

Every one of the original rungs' control values is **bit-identical** between the
two runs — checked on PHerc1203, 121 of 121 values identical to within 1e-9, 0
different. The finer run computes the same thing; it only adds rungs.

## The result

| px | mm | n | median drop | mean | frac degraded |
|---|---|---|---|---|---|
| 25 | 0.45 | 52 | +0.0003 | +0.0001 | 0.60 |
| 50 | 0.91 | 52 | +0.0018 | +0.0018 | 0.65 |
| **75** | **1.36** | 52 | +0.0042 | +0.0045 | 0.69 |
| 100 | 1.82 | 51 | +0.0076 | +0.0082 | 0.73 |
| **125** | **2.27** | 51 | **+0.0098** | +0.0128 | 0.75 |
| **150** | **2.72** | 51 | **+0.0159** | +0.0181 | 0.80 ← **floor** |
| **175** | **3.18** | 51 | +0.0192 | +0.0246 | 0.76 |
| 200 | 3.63 | 50 | +0.0255 | +0.0321 | 0.80 |
| **300** | **5.44** | 47 | +0.0509 | +0.0555 | 0.79 |
| 400 | 7.24 | 44 | +0.0713 | +0.0818 | 0.84 |
| 800 | 14.32 | 14 | +0.1119 | +0.1363 | 1.00 |

**Floor on the finer ladder: 150 px = 2.72 mm.** Threshold 0.01, unchanged.
Monotonicity holds across all eleven rungs, so the pre-committed condition in
§"What is committed in advance" item 3 is met and a floor may be quoted.

## What this does and does not say

**It is a resolution result, not an improvement.** The measured quantity did not
change — every original rung is identical. The floor moved from 3.63 mm to
2.72 mm because the ladder now has rungs where the threshold is actually crossed,
not because the instrument got better.

**The knife edge is not gone, it moved one rung down.** At 125 px the median drop
is **+0.0098**, two thousandths below the threshold. So the same step-function
fragility that made 1.81 become 3.63 now sits between 125 and 150 px. The
defensible statement is that **the blind zone ends somewhere between 2.27 mm and
2.72 mm**, and we quote 2.72 mm because that is what the pre-registered rule
returns on this ladder.

**The old numbers are not vindicated.** Per the pre-registration, item 5: 2.72 mm
is a new measurement on a new ladder. It does not license re-quoting 1.81 mm,
which was returned by a ladder too coarse to locate the crossing. Both the
3.63 mm and 2.72 mm figures must be quoted together wherever one is quoted, and
3.63 mm remains the headline until the finer ladder has been reproduced by
someone else.

## What actually changes downstream

1. **The PHerc1203 margin widens.** §6.4 of the README notes that the straight
   stick sits a median 4.09 mm from the annotated axis on PHerc1203, clearing the
   3.63 mm floor "by a factor of 1.1 … and that narrowing is part of the cost of
   this update". Against 2.72 mm the factor is **1.5**. Pooled, the stick sits at
   a median 6.24 mm, a factor of **2.3** rather than 1.7.
2. **§7.5 does not come back.** The agreement with Iyan Dopico's independent
   PHerc1218 axis has a median of 2.00 mm. That is still **below** 2.72 mm, so it
   still sits inside the blind zone and still cannot be read as evidence about
   millimetre accuracy. This was the outcome that would have been most convenient
   to reverse, and it does not reverse.
3. **The densification is still invisible to this instrument.** Nothing here
   touches that: the added points move the axis by less than 2.27 mm on almost
   every slice, and 112 of 198 paired slices did not move at all.
4. **The main claim is untouched.** 10 of 10 scrolls, W = 0.0, p = 0.0020. The
   floor bounds interpretation, not the test.

## The weakness this run deliberately did not address

The control still rests on **six slices per scroll, 52 valid pooled**. That is
why the 15 → 19 August change in the 100 px drop carried Wilcoxon p = 0.43: there
is no power, and the floor's own stability is unmeasured. Widening the control
set is a separate change with a separate cost, named in the pre-registration and
deliberately not mixed into this run.

## Reproduction

    cd <worktree>/_axisdemo   # the runner lives outside this repository; see the note in README §6.4
    .venv-torch/bin/python floor_finegrid.py PHerc0191 PHerc0257 PHerc0268 \
        PHerc0358 PHerc0800 PHerc0813 PHerc1203 PHerc1218 PHerc1447 PHerc1545
    .venv-torch/bin/python floor_table.py

`floor_finegrid.py` is the pre-registered runner with two changes and no others:
the ladder gains five rungs, and only the six control slices per scroll are
processed. Output `prereg_*_finegrid.json` beside the originals, summary
`floor_finegrid_result.json`.
