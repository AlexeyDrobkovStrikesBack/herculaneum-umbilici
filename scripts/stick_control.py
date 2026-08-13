#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The control this package's own Motivation section asks for and never ran:
does the per-slice annotated axis beat a straight vertical stick?

Why it was missing
------------------
The Motivation section argues that substituting a straight vertical line for the
axis is not a small approximation, and it argues that geometrically: the
annotated centre departs from the vertical by up to 20.7 mm. That is a statement
about the annotation, not about the scroll -- it says our points move, not that
moving with them buys anything. Section 2 tests the annotated centre against a
centre displaced by a FIXED 150 or 300 voxels, which is a different question
again. Nothing in the package tested the annotated axis against the straight
stick with a measure.

This does. It reuses the banded-energy measure of `validate_axes.py` unchanged
(imported, not reimplemented) and evaluates it, on every one of the same 297
annotated slices, at three centres:

    annotated   the interpolated annotated axis at that z (identical to the
                `h` column of qc/validation_raw.json)
    mean stick  a vertical line through the mean (x, y) of that scroll's
                annotated points -- the reference the 20.7 mm figure is
                measured against
    cheby stick a vertical line placed as well as a straight line can be (the
                Chebyshev centre of the point set) -- the reference behind the
                19.0 mm figure

Unlike the +150/+300 control the displacement here is not fixed: it is whatever
the scroll's own curvature makes it, from ~0 voxels near the middle of a scroll
to thousands at the ends. So the win rate is reported against displacement as
well as pooled, which is the part that can fail: section 2 established that this
measure resolves gross displacement and not annotation-scale accuracy, so a
useful result here must show wins concentrated at large displacement and no
signal at small displacement. If it does not, the measure is picking up
something other than centring.

Reproducing
-----------
    python3 scripts/stick_control.py                 # counts the shipped raw file
    python3 scripts/stick_control.py --measure       # recomputes it (needs the
                                                     # per-scroll slice PNGs)

The shipped `qc/stick_control_raw.json` (about 100 KB) is what `--measure`
writes, so the counting path runs from a bare clone with numpy and scipy alone.

Definitions, so the counting can be checked:
  win      h(annotated) > h(stick) on that slice. Ties would count as losses;
           there are none.
  ratio    h(annotated) / h(stick).
  offset   distance in L0 voxels between the annotated centre and the stick at
           that z. This is the "dose".
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.stats import binomtest

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TREE = os.environ.get('UMBILICI_TREE', ROOT)
RAW = os.path.join(ROOT, 'qc', 'stick_control_raw.json')

SCROLLS = ["PHerc0191", "PHerc0257", "PHerc0268", "PHerc0358", "PHerc0800",
           "PHerc0813", "PHerc1203", "PHerc1218", "PHerc1447", "PHerc1545"]

STICKS = ('mean', 'cheby')
# Dose bins in L0 voxels. The edges are fixed by section 2's own finding: the
# measure was null at a 150-voxel displacement and positive at 300, so the bins
# are set to straddle that, not chosen after looking at this result.
BINS = [(0, 150), (150, 300), (300, 600), (600, 10 ** 9)]


def chebyshev_center(xy):
    """Centre of the smallest circle covering the points -- the best a straight
    vertical stick can be placed. Same coarse-then-fine search as
    `axis_stats.chebyshev_radius`, which returns only the radius."""
    lo, hi = xy.min(0), xy.max(0)
    c = xy.mean(0)
    span = float(max(hi - lo))
    for _ in range(40):
        g = np.stack(np.meshgrid(np.linspace(c[0] - span, c[0] + span, 21),
                                 np.linspace(c[1] - span, c[1] + span, 21)),
                     -1).reshape(-1, 2)
        r = np.hypot(*(xy[None, :, :] - g[:, None, :]).transpose(2, 0, 1)).max(1)
        c = g[int(np.argmin(r))]
        span /= 3.0
    return c


def measure():
    """Recompute the raw file. Needs the per-scroll slice PNGs and meta.json."""
    from PIL import Image
    import validate_axes as V

    out = {}
    for name in SCROLLS:
        meta = json.load(open(os.path.join(TREE, name, 'meta.json')))
        cp = json.load(open(os.path.join(
            ROOT, f'{name}_umbilicus.json')))['control_points']
        xy = np.array([[p['x'], p['y']] for p in cp], float)
        centres = {'mean': xy.mean(0), 'cheby': chebyshev_center(xy)}
        rows = []
        for s in V.all_slices(meta, cp):
            img = np.asarray(Image.open(os.path.join(TREE, name, s['file'])
                                        ).convert('L'), dtype=np.float32)
            ax = V.axis_at(cp, s['z'])
            cx, cy = ax[0] / V.SCALE, ax[1] / V.SCALE
            rec = {'z': s['z'], 'file': s['file'],
                   'h': V.coherence(*V.unwrap(img, cx, cy))[0]}
            for k, c in centres.items():
                sx, sy = c[0] / V.SCALE, c[1] / V.SCALE
                rec[f'h_{k}'] = V.coherence(*V.unwrap(img, sx, sy))[0]
                rec[f'off_{k}'] = float(np.hypot(ax[0] - c[0], ax[1] - c[1]))
            rows.append(rec)
            del img
        out[name] = rows
        print(f'{name}: {len(rows)} slices', flush=True)
    os.makedirs(os.path.join(ROOT, 'qc'), exist_ok=True)
    json.dump(out, open(RAW, 'w'), indent=1)
    print('written', RAW)


def usable(r, stick):
    """A slice counts only if the measure returned a value at BOTH centres."""
    for k in ('h', f'h_{stick}'):
        v = r.get(k)
        if v is None or np.isnan(v):
            return False
    return True


def block(data, stick):
    print(f'\n=== annotated axis vs the {stick} stick ===')
    print(f"{'scroll':10} {'wins':>7} {'rate':>6} {'median ratio':>13} "
          f"{'median offset':>14} {'p (uncorrected)':>16}")
    per = {}
    dropped = []
    for name in SCROLLS:
        rows = []
        for r in data.get(name, []):
            if usable(r, stick):
                rows.append(r)
            else:
                dropped.append((name, r['z']))
        if not rows:
            continue
        w = sum(1 for r in rows if r['h'] > r[f'h_{stick}'])
        rat = np.median([r['h'] / r[f'h_{stick}'] for r in rows
                         if r[f'h_{stick}'] > 0])
        off = np.median([r[f'off_{stick}'] for r in rows])
        per[name] = (w, len(rows), float(rat), float(off))
    for name, (w, k, rat, off) in sorted(per.items(), key=lambda kv: -kv[1][0] / kv[1][1]):
        p = binomtest(w, k, 0.5, alternative='greater').pvalue
        mark = '  <- below 50%' if w / k < 0.5 else ''
        print(f'{name:10} {w:3d}/{k:<3d} {w/k:6.3f} {rat:13.3f} '
              f'{off:14.0f} {p:16.3f}{mark}')
    if dropped:
        print(f'\n{len(dropped)} slice(s) dropped because the measure returns no '
              f'value at the stick centre — it lands far enough outside the '
              f'tissue that fewer than 20 radii carry data: '
              + ', '.join(f'{n} z={z}' for n, z in dropped) +
              '. Dropping them runs against this control: on those slices the '
              'stick fails outright.')
    wins = sum(v[0] for v in per.values())
    n = sum(v[1] for v in per.values())
    above = sum(1 for w, k, _, _ in per.values() if w / k > 0.5)
    print(f'\npooled over slices (PSEUDOREPLICATED, do not quote alone): '
          f'{wins}/{n} = {wins/n:.3f}, one-sided binomial p = '
          f'{binomtest(wins, n, 0.5, alternative="greater").pvalue:.3g}')
    print(f'scroll-level sign test (the defensible statement): {above}/{len(per)} '
          f'scrolls above 50%, one-sided p = '
          f'{binomtest(above, len(per), 0.5, alternative="greater").pvalue:.3g}')

    print(f'\nwin rate against displacement (L0 voxels between the annotated '
          f'centre and the {stick} stick at that slice):')
    print(f"{'offset':>14} {'slices':>7} {'wins':>7} {'rate':>6} "
          f"{'p (uncorrected)':>16}")
    for lo, hi in BINS:
        rows = [r for name in SCROLLS for r in data.get(name, [])
                if usable(r, stick) and lo <= r[f'off_{stick}'] < hi]
        if not rows:
            continue
        w = sum(1 for r in rows if r['h'] > r[f'h_{stick}'])
        label = f'{lo}-{hi}' if hi < 10 ** 9 else f'{lo}+'
        print(f'{label:>14} {len(rows):7d} {w:7d} {w/len(rows):6.3f} '
              f'{binomtest(w, len(rows), 0.5, alternative="greater").pvalue:16.3f}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--measure', action='store_true',
                    help='recompute the raw file from the slice PNGs')
    a = ap.parse_args()
    if a.measure:
        return measure()
    if not os.path.exists(RAW):
        raise SystemExit(f'{RAW} not found — run with --measure (needs the tree)')
    data = json.load(open(RAW))
    for stick in STICKS:
        block(data, stick)


if __name__ == '__main__':
    sys.exit(main())
