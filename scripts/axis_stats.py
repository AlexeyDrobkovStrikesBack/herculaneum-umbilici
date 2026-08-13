#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geometry of the shipped axes — every number the README states about the
polylines themselves, recomputed from the ten published json files.

Runs on a fresh clone with no extra data: the voxel size is parsed out of each
file's `metadata.source_volume`. Two columns (tissue band, bare edges, coverage)
additionally need `PHercNNNN/meta.json` from the annotation tree; where that is
absent the columns print as `-`.

    python3 scripts/axis_stats.py

Definitions, stated so they can be checked:

  max deviation   max over annotated points of the distance from the vertical
                  line through the scroll's MEAN (x, y). This is the reference
                  the README quotes. A vertical line placed optimally (the
                  Chebyshev centre of the point set) is a smaller number, also
                  printed, so the choice of reference is visible.
  lateral sweep   diameter of the point set in the xy plane, i.e. the largest
                  distance between any two annotated centres.
  kink            median distance of a point from the straight chord between
                  its two z-neighbours. Reported twice: on the polyline as
                  published, and after thinning to a common 480-voxel z-step
                  (the fairness convention of calib_figure.py, so that a denser
                  annotation is not credited for being denser).
  largest gap     largest interior z gap between consecutive annotated points.
"""
import json
import os
import re
import sys

import numpy as np

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# The annotation tree (per-scroll meta.json, ref_sean/) if it is somewhere else.
TREE = os.environ.get('UMBILICI_TREE', ROOT)

SCROLLS = ["PHerc0191", "PHerc0257", "PHerc0268", "PHerc0358", "PHerc0800",
           "PHerc0813", "PHerc1203", "PHerc1218", "PHerc1447", "PHerc1545"]

STEP = 480.0          # common z-step for the fair kink comparison


def voxel_um(meta):
    """Voxel size in micrometres, parsed from the recorded volume id."""
    m = re.search(r'-([0-9]+\.[0-9]+)um-', meta.get("source_volume", ""))
    if not m:
        raise SystemExit("no voxel size in source_volume")
    return float(m.group(1))


def subsample(pts, step):
    pts = sorted(pts, key=lambda p: p["z"])
    zs = np.array([p["z"] for p in pts], float)
    tgt = np.arange(zs[0], zs[-1] + 1, step)
    idx = sorted({int(np.argmin(np.abs(zs - t))) for t in tgt})
    return [pts[i] for i in idx]


def kink(pts):
    r = sorted(pts, key=lambda q: q["z"])
    xs = np.array([q["x"] for q in r], float)
    ys = np.array([q["y"] for q in r], float)
    zs = np.array([q["z"] for q in r], float)
    d = []
    for i in range(1, len(r) - 1):
        w = (zs[i] - zs[i - 1]) / (zs[i + 1] - zs[i - 1])
        px = xs[i - 1] + w * (xs[i + 1] - xs[i - 1])
        py = ys[i - 1] + w * (ys[i + 1] - ys[i - 1])
        d.append(np.hypot(xs[i] - px, ys[i] - py))
    return float(np.median(d)) if d else float("nan")


def chebyshev_radius(xy):
    """Radius of the smallest circle covering the points, found by a coarse
    then fine grid search — the deviation a vertical stick would have if it
    were placed as well as possible."""
    lo, hi = xy.min(0), xy.max(0)
    c = xy.mean(0)
    span = float(max(hi - lo))
    for _ in range(40):
        g = np.stack(np.meshgrid(np.linspace(c[0] - span, c[0] + span, 21),
                                 np.linspace(c[1] - span, c[1] + span, 21)), -1).reshape(-1, 2)
        r = np.hypot(*(xy[None, :, :] - g[:, None, :]).transpose(2, 0, 1)).max(1)
        c = g[int(np.argmin(r))]
        span /= 3.0
    return float(np.hypot(*(xy - c).T).max())


def main():
    print(f"{'scroll':10} {'vox_um':>6} {'n':>3} {'maxdev_mm':>9} {'cheby_mm':>8} "
          f"{'sweep_mm':>8} {'kink':>6} {'kink480':>7} {'maxgap':>6} "
          f"{'band':>13} {'bare_lo':>7} {'bare_hi':>7} {'cover':>6}")
    for s in SCROLLS:
        d = json.load(open(os.path.join(ROOT, f"{s}_umbilicus.json")))
        pts = sorted(d["control_points"], key=lambda p: p["z"])
        um = voxel_um(d["metadata"])
        xy = np.array([[p["x"], p["y"]] for p in pts], float)
        zs = np.array([p["z"] for p in pts], float)

        dev = float(np.hypot(*(xy - xy.mean(0)).T).max()) * um / 1000.0
        cheby = chebyshev_radius(xy) * um / 1000.0
        sweep = float(np.hypot(*(xy[None] - xy[:, None]).transpose(2, 0, 1)).max()) * um / 1000.0
        gap = int(np.diff(zs).max())

        mp = os.path.join(TREE, s, "meta.json")
        if os.path.exists(mp):
            zr = json.load(open(mp))["z_range_L0"]
            band = f"{int(zr[0])}-{int(zr[1])}"
            lo, hi = int(zs[0] - zr[0]), int(zr[1] - zs[-1])
            cover = f"{(zs[-1] - zs[0]) / (zr[1] - zr[0]) * 100:.0f}%"
        else:
            band, lo, hi, cover = "-", "-", "-", "-"

        print(f"{s:10} {um:6.3f} {len(pts):3d} {dev:9.2f} {cheby:8.2f} {sweep:8.2f} "
              f"{kink(pts):6.0f} {kink(subsample(pts, STEP)):7.0f} {gap:6d} "
              f"{band:>13} {str(lo):>7} {str(hi):>7} {cover:>6}")

    ref = os.path.join(TREE, "ref_sean")
    if os.path.isdir(ref):
        print("\nsean's published axes, same kink definition:")
        for s in ("PHerc0125", "PHerc0211", "PHerc0826"):
            p = os.path.join(ref, f"{s}_umbilicus.json")
            if not os.path.exists(p):
                continue
            pts = json.load(open(p))["control_points"]
            print(f"{s:10} {'':6} {len(pts):3d} {'':9} {'':8} {'':8} "
                  f"{kink(pts):6.0f} {kink(subsample(pts, STEP)):7.0f}")
    else:
        print("\n(ref_sean/ not present — fetch sean's three axes from the open "
              "bucket to reproduce the smoothness comparison)")


if __name__ == "__main__":
    sys.exit(main())
