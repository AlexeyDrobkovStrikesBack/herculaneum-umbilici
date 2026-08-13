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
                  its two z-neighbours. Kink grows with chord length, so the
                  z-spacing it was measured at is printed next to every value
                  and three variants are reported:

                    kink     / step      on the polyline as published
                    kink480  / step480   after thinning to a 480-voxel target
                                         grid (the convention of
                                         calib_figure.py). NOTE: the thinning
                                         keeps the nearest existing point to
                                         each target, so it can only make a
                                         DENSE polyline sparser. On a polyline
                                         that is already sparser than 480 it
                                         changes little or nothing, and on an
                                         irregular one it can leave alternating
                                         short and doubled gaps. `step480` is
                                         the realized median step afterwards and
                                         shows how far from 480 each side ended
                                         up; read `kink480` only together with
                                         it.
                    kinkM    / nM        the genuinely spacing-matched figure:
                                         median over only those triples of the
                                         thinned polyline whose BOTH chords are
                                         within +-20% of 480 voxels, with nM the
                                         number of such triples. Blank when
                                         there are none, which is the honest
                                         answer for a polyline that has no
                                         480-voxel spacing anywhere in it.
  largest gap     largest interior z gap between consecutive annotated points,
                  with the two z values it runs between.
"""
import hashlib
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

STEP = 480.0          # target z-step for the thinning
MATCH = 0.20          # a chord counts as matched if it is within +-20% of STEP


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


def kink_terms(pts):
    """Per-triple chord distance, with the two chord lengths it was measured
    over, so a spacing-matched subset can be selected from it."""
    r = sorted(pts, key=lambda q: q["z"])
    xs = np.array([q["x"] for q in r], float)
    ys = np.array([q["y"] for q in r], float)
    zs = np.array([q["z"] for q in r], float)
    d, lo, hi = [], [], []
    for i in range(1, len(r) - 1):
        w = (zs[i] - zs[i - 1]) / (zs[i + 1] - zs[i - 1])
        px = xs[i - 1] + w * (xs[i + 1] - xs[i - 1])
        py = ys[i - 1] + w * (ys[i + 1] - ys[i - 1])
        d.append(np.hypot(xs[i] - px, ys[i] - py))
        lo.append(zs[i] - zs[i - 1])
        hi.append(zs[i + 1] - zs[i])
    return np.array(d), np.array(lo), np.array(hi)


def kink(pts):
    d, _, _ = kink_terms(pts)
    return float(np.median(d)) if len(d) else float("nan")


def med_step(pts):
    zs = np.array(sorted(p["z"] for p in pts), float)
    return float(np.median(np.diff(zs))) if len(zs) > 1 else float("nan")


def kink_matched(pts):
    """Kink over only the triples whose both chords are within +-MATCH of STEP,
    i.e. the comparison the '480-voxel step' was meant to be."""
    d, lo, hi = kink_terms(pts)
    if not len(d):
        return float("nan"), 0
    m = (np.abs(lo - STEP) <= MATCH * STEP) & (np.abs(hi - STEP) <= MATCH * STEP)
    if not m.any():
        return float("nan"), 0
    return float(np.median(d[m])), int(m.sum())


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


def smooth_terms(pts):
    """The six numbers of one smoothness row."""
    th = subsample(pts, STEP)
    km, nm = kink_matched(th)
    return dict(n_points=len(pts), step=med_step(pts), kink=kink(pts),
                n480=len(th), step480=med_step(th), kink480=kink(th),
                kinkM=(km if nm else None), nM=nm)


def print_row(name, whose, t, note=""):
    km = f"{t['kinkM']:.0f}" if t['nM'] else "-"
    print(f"{name:10} {whose:5} {t['n_points']:3d} {t['step']:8.0f} "
          f"{t['kink']:6.0f} {t['n480']:5d} {t['step480']:8.0f} "
          f"{t['kink480']:7.0f} {km:>5} {t['nM']:3d}{note}")


def smooth_row(name, whose, pts, note=""):
    print_row(name, whose, smooth_terms(pts), note)


def main():
    print("== geometry ==")
    print(f"{'scroll':10} {'vox_um':>6} {'n':>3} {'maxdev_mm':>9} {'cheby_mm':>8} "
          f"{'sweep_mm':>8} {'maxgap':>6} {'gap_z':>15} "
          f"{'band':>13} {'bare_lo':>7} {'bare_hi':>7} {'cover':>6}")
    cov_num = cov_den = 0.0
    covers = []
    for s in SCROLLS:
        d = json.load(open(os.path.join(ROOT, f"{s}_umbilicus.json")))
        pts = sorted(d["control_points"], key=lambda p: p["z"])
        um = voxel_um(d["metadata"])
        xy = np.array([[p["x"], p["y"]] for p in pts], float)
        zs = np.array([p["z"] for p in pts], float)

        dev = float(np.hypot(*(xy - xy.mean(0)).T).max()) * um / 1000.0
        cheby = chebyshev_radius(xy) * um / 1000.0
        sweep = float(np.hypot(*(xy[None] - xy[:, None]).transpose(2, 0, 1)).max()) * um / 1000.0
        dz = np.diff(zs)
        gi = int(np.argmax(dz))
        gap = int(dz[gi])
        gapz = f"{int(zs[gi])}->{int(zs[gi + 1])}"

        mp = os.path.join(TREE, s, "meta.json")
        if os.path.exists(mp):
            zr = json.load(open(mp))["z_range_L0"]
            band = f"{int(zr[0])}-{int(zr[1])}"
            lo, hi = int(zs[0] - zr[0]), int(zr[1] - zs[-1])
            cover = f"{(zs[-1] - zs[0]) / (zr[1] - zr[0]) * 100:.0f}%"
            cov_num += zs[-1] - zs[0]
            cov_den += zr[1] - zr[0]
            covers.append((zs[-1] - zs[0]) / (zr[1] - zr[0]) * 100)
        else:
            band, lo, hi, cover = "-", "-", "-", "-"

        print(f"{s:10} {um:6.3f} {len(pts):3d} {dev:9.2f} {cheby:8.2f} {sweep:8.2f} "
              f"{gap:6d} {gapz:>15} "
              f"{band:>13} {str(lo):>7} {str(hi):>7} {cover:>6}")

    if cov_den:
        print(f"\ncoverage of the tissue band, aggregated over the ten: "
              f"{cov_num / cov_den * 100:.1f}% z-weighted (this is the figure the "
              f"README quotes), {np.mean(covers):.1f}% unweighted mean, "
              f"{np.median(covers):.1f}% median, range "
              f"{min(covers):.0f}-{max(covers):.0f}%")
    else:
        print("\n(no PHercNNNN/meta.json — set UMBILICI_TREE to the annotation "
              "tree for the tissue band, bare edges and coverage)")

    print(f"\n== smoothness ==  (kink at the spacing it was measured at; see the "
          f"docstring)\n{'scroll':10} {'whose':5} {'n':>3} {'step':>8} {'kink':>6} "
          f"{'n480':>5} {'step480':>8} {'kink480':>7} {'kinkM':>5} {'nM':>3}")
    for s in SCROLLS:
        pts = json.load(open(os.path.join(ROOT, f"{s}_umbilicus.json")))["control_points"]
        smooth_row(s, "ours", pts)

    sean_rows()


# Every derived scalar `smooth_terms()` produces. The digest check below compares
# all of them, not a subset: an earlier version omitted `kinkM`, which is the one
# column README section 3 argues is the fair comparison, so a digest whose headline
# fair-comparison value was arbitrarily wrong still certified as matching.
DIGEST_KEYS = ("n_points", "step", "kink", "n480", "step480", "kink480",
               "kinkM", "nM")


def sean_rows():
    """The three reference rows.

    Sean's annotation files are not ours to redistribute, so `ref_sean/` is not
    in this repository. What IS in the repository is `qc/sean_reference.json`:
    the derived numbers of these three rows together with the sha256 of the file
    each was computed from. So the rows print on a bare clone, marked as read
    from that digest rather than recomputed.

    When the files are supplied (`scripts/fetch_sean.py`), two INDEPENDENT checks
    run on every row and both are reported:

      bytes    sha256 of your copy against the sha256 recorded in the digest;
      numbers  all eight derived scalars recomputed from your copy against the
               eight recorded in the digest, every one of them, `kinkM` included.

    They are independent on purpose. An earlier version put the numeric
    comparison in an `elif` after the sha256 test, so it only ever ran on files
    already proven byte-identical — where deterministic code cannot make it fire.
    It was therefore structurally incapable of reporting what the numbers do on a
    copy that differs. Now a file whose bytes differ still gets its eight numbers
    compared and named, and a digest that has been edited away from the script
    that produced it is caught even though every sha256 in it is untouched.

    What the pair of checks establishes is bounded: the bytes leg says your copy
    is the copy we measured; the numbers leg says this version of the script,
    run on your copy, still produces the values recorded in the digest. Neither
    says anything about sean's annotation being right.
    """
    ref = os.path.join(TREE, "ref_sean")
    dig_path = os.path.join(ROOT, "qc", "sean_reference.json")
    dig = json.load(open(dig_path))["scrolls"] if os.path.exists(dig_path) else {}
    have = 0
    for s in ("PHerc0125", "PHerc0211", "PHerc0826"):
        p = os.path.join(ref, f"{s}_umbilicus.json")
        if os.path.exists(p):
            raw = open(p, "rb").read()
            t = smooth_terms(json.loads(raw)["control_points"])
            note = ""
            d = dig.get(s)
            if d:
                # Both legs always run; neither guards the other.
                sha_ok = hashlib.sha256(raw).hexdigest() == d.get("sha256")
                bad = [k for k in DIGEST_KEYS
                       if abs((t.get(k) or 0) - (d.get(k) or 0)) > 1e-6]
                parts = []
                parts.append("bytes match" if sha_ok
                             else "!! sha256 DIFFERS from qc/sean_reference.json")
                parts.append(f"all {len(DIGEST_KEYS)} derived values match" if not bad
                             else f"!! recomputed {bad} DIFFER from the digest")
                note = "   (" + "; ".join(parts) + ")"
            print_row(s, "sean", t, note)
            have += 1
        elif s in dig:
            print_row(s, "sean", dig[s], "   (from qc/sean_reference.json)")
    if have < 3:
        print("(sean's rows above marked '(from qc/sean_reference.json)' are read "
              "from the shipped digest, not recomputed here. His three files are "
              "not redistributed in this repository — see scripts/fetch_sean.py "
              "for what they are, where they came from and how to check that you "
              "have the same bytes we measured.)")


if __name__ == "__main__":
    sys.exit(main())
