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
"""
import json
import os
import sys

from scipy.stats import binomtest

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW = os.path.join(ROOT, "qc", "validation_raw.json")


def block(data, key):
    per = {}
    for scroll, rows in sorted(data.items()):
        vals = [r[key] for r in rows if r.get(key) is not None]
        if not vals:
            continue
        per[scroll] = (sum(1 for v in vals if v > 1.0), len(vals))

    wins = sum(w for w, _ in per.values())
    n = sum(k for _, k in per.values())
    pooled = binomtest(wins, n, 0.5, alternative='greater').pvalue

    above = sum(1 for w, k in per.values() if w / k > 0.5)
    signp = binomtest(above, len(per), 0.5, alternative='greater').pvalue

    alpha = 0.05 / len(per)
    print(f"\n=== {key}: annotated centre vs the same centre displaced "
          f"{key[1:]} voxels ===")
    print(f"{'scroll':10} {'wins':>7} {'rate':>6} {'p (uncorrected)':>16} {'survives Bonferroni':>21}")
    for scroll, (w, k) in sorted(per.items(), key=lambda kv: -kv[1][0] / kv[1][1]):
        p = binomtest(w, k, 0.5, alternative='greater').pvalue
        flag = "yes" if p < alpha else "no"
        mark = "  <- below 50%" if w / k < 0.5 else ""
        print(f"{scroll:10} {w:3d}/{k:<3d} {w/k:6.3f} {p:16.3f} {flag:>21}{mark}")
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
