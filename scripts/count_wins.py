#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The shifted-axis control, counted and tested — every statistic the README
quotes for that control, from the raw file `validate_axes.py` writes.

    python3 scripts/validate_axes.py            # writes qc/validation_raw.json
    python3 scripts/count_wins.py               # this script reads it

`validate_axes.py` measures, for every annotated slice, a banded-energy ratio
between the annotated centre and the same centre displaced by a fixed number of
voxels in four directions (`r150`, `r300` for the two displacement magnitudes it
runs). A ratio above 1 is a "win" for the annotated centre.

This script does the counting and the testing that the README reports, and it
does BOTH displacements, not only the one that came out positive:

  * pooled slice-level binomial test (one-sided) — the number the README used to
    quote on its own. It PSEUDOREPLICATES: 297 slices are not 297 independent
    trials, since within a scroll they sit ~480 voxels apart, sample continuous
    tissue and share one interpolated axis. It is printed because it is what a
    reader will otherwise recompute, and labelled for what it is.
  * scroll-level sign test over the ten scrolls — the clustered statement, with
    the scroll as the unit of replication. This is the defensible one.
  * the per-scroll table, uncorrected, with the Bonferroni threshold printed
    next to it so it is visible that no scroll survives correction.
  * the per-scroll MEDIAN ratio next to the win rate, because a win rate near
    0.5 says nothing about which side the middle of the distribution is on.
    PHerc0800's median, the one the README quotes, is printed here.

Every count, rate, p-value and median the README quotes for this control is
printed by this script. It does not print the voxels-to-millimetres conversion
of the displacement (300 vox = 2.6-2.8 mm), which comes from the per-scroll
voxel size and is done in `axis_stats.py`.
"""
import json
import os
import sys

import numpy as np
from scipy.stats import binomtest

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW = os.path.join(ROOT, "qc", "validation_raw.json")


def tally(data, key):
    """Per-scroll `(wins, n, median ratio)` for one displacement magnitude, plus
    the number of NaN values dropped. Pure — it prints nothing — so that a
    figure can be drawn from exactly the counting `block` below prints, rather
    than from a second implementation of it that could drift."""
    per = {}
    dropped = 0
    for scroll, rows in sorted(data.items()):
        raw = [r[key] for r in rows if r.get(key) is not None]
        # A NaN would fail `v > 1.0` and be silently counted as a loss, so drop
        # it explicitly and say how many were dropped. On the shipped file this
        # is 0; the guard is here so that it stays visible if it ever is not.
        vals = [v for v in raw if not np.isnan(v)]
        dropped += len(raw) - len(vals)
        if not vals:
            continue
        per[scroll] = (sum(1 for v in vals if v > 1.0), len(vals),
                       float(np.median(vals)))
    return per, dropped


def block(data, key):
    per, dropped = tally(data, key)

    wins = sum(p[0] for p in per.values())
    n = sum(p[1] for p in per.values())
    pooled = binomtest(wins, n, 0.5, alternative='greater').pvalue

    above = sum(1 for w, k, _ in per.values() if w / k > 0.5)
    signp = binomtest(above, len(per), 0.5, alternative='greater').pvalue

    alpha = 0.05 / len(per)
    print(f"\n=== {key}: annotated centre vs the same centre displaced "
          f"{key[1:]} voxels ===")
    print(f"{'scroll':10} {'wins':>7} {'rate':>6} {'median ratio':>13} "
          f"{'p (uncorrected)':>16} {'survives Bonferroni':>21}")
    for scroll, (w, k, med) in sorted(per.items(), key=lambda kv: -kv[1][0] / kv[1][1]):
        p = binomtest(w, k, 0.5, alternative='greater').pvalue
        flag = "yes" if p < alpha else "no"
        mark = "  <- below 50%" if w / k < 0.5 else ""
        print(f"{scroll:10} {w:3d}/{k:<3d} {w/k:6.3f} {med:13.3f} "
              f"{p:16.3f} {flag:>21}{mark}")
    if dropped:
        print(f"({dropped} value(s) were NaN and were dropped)")
    print(f"\npooled over slices (PSEUDOREPLICATED, do not quote alone): "
          f"{wins}/{n} = {wins/n:.3f}, one-sided binomial p = {pooled:.3g}")
    print(f"scroll-level sign test (the defensible statement): "
          f"{above}/{len(per)} scrolls above 50%, one-sided p = {signp:.3g}")
    print(f"Bonferroni threshold for the {len(per)} per-scroll tests: "
          f"alpha = 0.05/{len(per)} = {alpha:.4f}")


def main():
    if not os.path.exists(RAW):
        raise SystemExit(f"{RAW} not found — run scripts/validate_axes.py first")
    data = json.load(open(RAW))
    for key in ("r300", "r150"):
        block(data, key)


if __name__ == "__main__":
    sys.exit(main())
