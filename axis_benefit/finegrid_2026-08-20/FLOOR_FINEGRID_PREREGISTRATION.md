# Pre-registration: a finer displacement ladder for the sensitivity floor

Written 20 August 2026, **before the finer ladder is run and before any of its
numbers exist**. Nothing below was chosen with a result in view, and the reason
for writing it separately rather than editing the original pre-registration is
that the original's rule must stay readable exactly as it was committed.

## Why this is being changed at all, stated honestly

The original pre-registration (`umbilici_repo/axis_benefit/PREREGISTRATION.md`,
13 August 17:35) fixed a displacement ladder of **25, 50, 100, 200, 400, 800 px**
and a rule: the sensitivity floor is the first rung whose median drop in q
reaches 0.01.

On the 15 August curves that rule returned **100 px = 1.81 mm**, because the
median drop at 100 px was **+0.0105**. On the 19 August densified curves it
returns **200 px = 3.63 mm**, because the median drop at 100 px is **+0.0076**.

The measured quantity moved by 0.0029. The reported floor doubled. Paired on the
40 control slices the two runs share, the change is **not significant**:
median +0.0134 → +0.0097, Wilcoxon **p = 0.43**.

So the doubling is an artifact of a step function evaluated on a quantity sitting
on its threshold, on a ladder that has **nothing between 100 and 200 px**. The
floor is not located by this ladder; it is only bracketed, and the bracket is a
factor of two wide.

**This is a change to a pre-registered instrument made after seeing a result it
produced, and that is exactly the thing pre-registration exists to prevent.** The
mitigation is that the change is committed here in advance of the run, the
original rule is not touched, both numbers will be reported side by side, and the
change is to *resolution only* — the threshold, the measure, the control slices,
the directions and the acceptance rule are all unchanged. If the finer ladder
happened to return a floor above 3.63 mm we would report that too; the commitment
below says so explicitly.

## What changes

**One thing: the ladder.** From

    25, 50, 100, 200, 400, 800

to

    25, 50, 75, 100, 125, 150, 175, 200, 300, 400, 800

Every original rung is kept, so the original rule can be recomputed from the same
files and must reproduce its own answer exactly. Four rungs are added between 100
and 200 where the bracket lies, one at 75 below it, and one at 300.

## What does not change

- The measure: `radial_anisotropy_sectored`, identical code, imported unmodified.
- The threshold: median drop ≥ **0.01**, unchanged.
- The rule: the floor is the **first** rung whose median drop reaches the
  threshold.
- The control slices: `CONTROL_K = [0, 5, 10, 15, 20, 25]`, six per scroll,
  the same six.
- The four displacement directions, and the `ring95 ≥ 0.95` validity condition.
- The curves: the shipped 19 August densified umbilici, unmodified.

## What is committed in advance

1. **The finer ladder's floor will be reported whatever it is**, including if it
   lands at or above 200 px, and including if it lands *below* 100 px, which
   would say the original ladder was too coarse in the other direction.
2. **Both floors will be quoted together** wherever the README quotes one:
   "3.63 mm on the pre-registered ladder, X mm on the finer ladder". Neither
   replaces the other. The pre-registered number remains the headline until the
   finer ladder has been externally reproduced.
3. **The monotonicity check must still hold.** If the median drop is not
   monotone in displacement across the finer ladder, that is a failure of the
   control itself and will be reported as one, and no floor will be quoted from a
   non-monotone ladder.
4. **This does not re-open the main claim.** The axis-benefit result (10 of 10
   scrolls, W = 0.0, p = 0.0020) is untouched by anything here; the floor bounds
   what that result may be *interpreted* to mean, and a finer floor changes the
   interpretation, not the test.
5. **A moved floor does not license re-quoting 1.81 mm.** If the finer ladder
   returns something near 1.8 mm, that is a new measurement on a new ladder, not
   a vindication of the old number, and it will be labelled that way.

## The second known weakness, recorded but not fixed here

The control rests on **six slices per scroll, 52 valid pooled, 40 shared between
the two runs**. That is why the Wilcoxon returns p = 0.43: there is almost no
power, and the floor's own stability is therefore unmeasured. Widening
`CONTROL_K` is a separate change with a separate cost and is **not** part of this
run — mixing a resolution change and a sample-size change in one step would make
neither attributable. It is named here so it is not forgotten.

## How it will be run

`_axisdemo/floor_finegrid.py`, a copy of the pre-registered runner restricted to
the six control slices per scroll and carrying the finer ladder, writing
`prereg_{scroll}_finegrid.json` beside the originals. The published repository is
not written to. Output goes to `FLOOR_FINEGRID_RESULT_2026-08-20.md`.

Status at the time of writing: **not run, no numbers exist.**
