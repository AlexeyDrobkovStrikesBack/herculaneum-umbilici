#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""README section 7 — our PHerc1218 axis against the prior annotation.

    python3 scripts/prior_1218.py                 # the numbers
    python3 scripts/prior_1218.py --figure        # + panels/prior_1218_agreement.png
    python3 scripts/prior_1218.py --fetch         # re-download the prior file
    python3 scripts/prior_1218.py --check-bucket  # re-verify the shared frame
    python3 scripts/prior_1218.py --villa DIR     # cross-check against villa's loader
    python3 scripts/prior_1218.py --measure-centroid   # re-measure the CT centroid

Runs on a bare clone with numpy alone (matplotlib only for `--figure`): both
files ship, and so does `qc/prior_1218_centroid_raw.json`. `--fetch`,
`--check-bucket`, `--villa` and `--measure-centroid` are the four legs that
reach outside the clone, and each is optional and prints what it did.

What this compares, and what it does not
----------------------------------------
PHerc1218 is the one scroll of our ten that already had an umbilicus when we
started: Iyán Dopico published one on 2026-07-21, three weeks before ours
(`qc/prior_umbilicus_PHerc1218_SOURCE.md`). It is the only external check in
this package — everywhere else the control is something we built ourselves.

The two files are **not defined to be the same point**. Ours is a hand-placed
winding centre. Theirs is the centroid of the papyrus mask of each slice, from
their own instance segmentation, running-median smoothed. On a symmetric
cross-section those coincide; on a crushed or one-sided one they do not, and
that gap is a fact about the scroll rather than an error in either file.
`qc/PRIOR1218_PREREGISTRATION.md` fixes what agreement and what disagreement
would each mean, and it was written and hashed before this script first ran.

Definitions, so they can be checked
-----------------------------------
  overlap        [max of the two z minima, min of the two z maxima]. Neither
                 polyline is extrapolated: villa's own loader would happily
                 extrapolate (`fill_value='extrapolate'`), and a comparison in
                 the region where one side is invented is not a comparison.
  common grid    their z sampling restricted to the overlap - the denser of the
                 two. Ours is evaluated on it by linear interpolation in z,
                 which is exactly what a consumer reading our file does.
  d(z)           hypot(dy, dx) at each grid z, in level-0 voxels and in mm at
                 the voxel size parsed from our metadata.source_volume.
  residual       d recomputed after subtracting the mean (dy, dx). This is the
                 part that a constant offset cannot explain, and the split
                 between the two is what says whether a disagreement is about
                 convention or about shape.
  node distances the same distance evaluated only at OUR 28 hand-placed control
                 points, so no number here rests on our own interpolation.

Post-hoc, and labelled as such (`--measure-centroid`)
-----------------------------------------------------
The paragraph above says the two files are different quantities. That is an
assertion about their generator's source code, and it can be measured instead:
the CT itself has a mass centroid per cross-section, and if their file is one
then the CT centroid should lie on their line and not on ours. This was **not**
in the pre-registration - it was added after seeing that the disagreement was
z-dependent rather than a constant offset, which is exactly the outcome the
pre-registration named as "the centroid-versus-centre gap opening where a
cross-section stops being symmetric". It is a diagnostic of the mechanism, not
a test of either file, and it is reported separately from the pre-registered
result for that reason.

`--measure-centroid` streams level 5 of the same masked volume (scale 32, so
276.5 um per voxel and a 238-voxel-wide cross-section; 24 chunks, about 48 MB)
and computes three centroids per slice: of the nonzero mask, intensity-weighted,
and intensity-weighted over the top 40% of nonzero intensities. The first is the
closest analogue of their definition, which is the centroid of a nonzero label
mask. Its output ships as `qc/prior_1218_centroid_raw.json`, so the comparison
runs from a bare clone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

import numpy as np

ROOT = os.environ.get("UMBILICI_ROOT",
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OURS = os.path.join(ROOT, "PHerc1218_umbilicus.json")
PRIOR = os.path.join(ROOT, "qc", "prior_umbilicus_PHerc1218_IyanDopico.json")
RAW = os.path.join(ROOT, "qc", "prior_1218_raw.json")
CENTROID = os.path.join(ROOT, "qc", "prior_1218_centroid_raw.json")
PANELS = os.path.join(ROOT, "panels")

CENT_LEVEL = 5            # pyramid level the centroid diagnostic reads
CENT_MIN_PX = 2000        # a slice needs this many nonzero pixels to count
CENT_TOP_PCT = 60         # "papyrus only" = intensities above this percentile

PRIOR_SHA256 = "a153ad7a768866cb2800baed4190505dadccfb98aec2635fd8dd0510dec29560"
PRIOR_URL = ("https://raw.githubusercontent.com/IyanDopico/vesuvius-sheet-tools/"
             "6a831e0a9a/data/spiral_input_pherc1218/umbilicus.json")

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"

# The three distances this package already publishes, used as the yardsticks
# for the verdict. Fixed in qc/PRIOR1218_PREREGISTRATION.md before the run.
FLOOR_MM = 1.81       # README section 6.4 - sensitivity floor of the prereg run
STICK_MM = 6.0        # README section 6   - median axis-to-stick distance
HEADLINE_MM = 20.7    # README Motivation  - PHerc0268 deviation from a vertical

# Constants hard-coded in their generator (make_umbilicus.py), against which the
# shared frame is checked.
THEIR_FULL_Z, THEIR_FULL_YX = 23247, 7593


# ---------------------------------------------------------------- loading --
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_points(path):
    """z, y, x arrays sorted by z - the same read villa's loader performs."""
    with open(path, "rt") as fh:
        doc = json.load(fh)
    pts = sorted(doc["control_points"], key=lambda p: p["z"])
    z = np.asarray([p["z"] for p in pts], dtype=float)
    y = np.asarray([p["y"] for p in pts], dtype=float)
    x = np.asarray([p["x"] for p in pts], dtype=float)
    return z, y, x, doc.get("metadata", {})


def voxel_um(meta):
    m = re.search(r"-([0-9]+\.[0-9]+)um-", meta.get("source_volume", ""))
    if not m:
        raise SystemExit("no voxel size in metadata.source_volume")
    return float(m.group(1))


def fetch_prior():
    import urllib.request
    print("fetching", PRIOR_URL)
    with urllib.request.urlopen(PRIOR_URL, timeout=120) as r:
        blob = r.read()
    got = hashlib.sha256(blob).hexdigest()
    if got != PRIOR_SHA256:
        raise SystemExit(f"!! sha256 {got} != expected {PRIOR_SHA256}; refusing to install")
    with open(PRIOR, "wb") as fh:
        fh.write(blob)
    print(f"installed {PRIOR} ({len(blob)} bytes, sha256 matches)")


def check_bucket(volume):
    """Level-0 shape of the volume both files claim, read from the bucket."""
    import urllib.request
    url = f"{BUCKET}/{volume}/0/.zarray"
    with urllib.request.urlopen(url, timeout=120) as r:
        arr = json.load(r)
    shape = arr["shape"]                       # (z, y, x)
    print(f"bucket  {url}")
    print(f"        shape (z,y,x) = {shape}, dtype {arr['dtype']}")
    ok_z = shape[0] == THEIR_FULL_Z
    ok_yx = shape[1] == THEIR_FULL_YX and shape[2] == THEIR_FULL_YX
    print(f"        their generator's FULL_Z={THEIR_FULL_Z}, FULL_YX={THEIR_FULL_YX}: "
          f"{'MATCH' if (ok_z and ok_yx) else '!! DIFFER'}")
    url = f"{BUCKET}/{volume}/metadata.json"
    with urllib.request.urlopen(url, timeout=120) as r:
        md = json.load(r)
    px_mm = md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]
    print(f"        samplePixelSize = {px_mm} mm = {px_mm * 1000:.4f} um "
          f"(the volume id says {voxel_um({'source_volume': volume}):.3f} um)")
    return shape, px_mm * 1000.0


# ------------------------------------------------------------ the compare --
def compare():
    zo, yo, xo, mo = load_points(OURS)
    zp, yp, xp, mp = load_points(PRIOR)
    um = voxel_um(mo)
    mm = um / 1000.0

    lo, hi = max(zo.min(), zp.min()), min(zo.max(), zp.max())
    keep = (zp >= lo) & (zp <= hi)
    zg = zp[keep]
    # ours interpolated onto their grid; np.interp is linear, the same rule
    # scipy's interp1d(kind='linear') applies inside the data range.
    yo_i = np.interp(zg, zo, yo)
    xo_i = np.interp(zg, zo, xo)
    dy, dx = yo_i - yp[keep], xo_i - xp[keep]
    d = np.hypot(dy, dx)

    off_y, off_x = float(dy.mean()), float(dx.mean())
    resid = np.hypot(dy - off_y, dx - off_x)

    # the same distance at our own nodes, no interpolation of our file at all
    innode = (zo >= lo) & (zo <= hi)
    yp_at = np.interp(zo[innode], zp, yp)
    xp_at = np.interp(zo[innode], zp, xp)
    dnode = np.hypot(yo[innode] - yp_at, xo[innode] - xp_at)

    return dict(
        ours=dict(path=os.path.basename(OURS), n=int(zo.size),
                  z=[float(zo.min()), float(zo.max())],
                  volume=mo.get("source_volume"), voxel_um=um),
        prior=dict(path=os.path.basename(PRIOR), n=int(zp.size),
                   z=[float(zp.min()), float(zp.max())],
                   sha256=sha256(PRIOR)),
        overlap=[float(lo), float(hi)], n_grid=int(zg.size),
        z=zg.tolist(), d_vox=d.tolist(), dy_vox=dy.tolist(), dx_vox=dx.tolist(),
        resid_vox=resid.tolist(),
        offset_vox=dict(dy=off_y, dx=off_x, norm=float(np.hypot(off_y, off_x))),
        node_z=zo[innode].tolist(), node_d_vox=dnode.tolist(),
        mm_per_vox=mm,
    )


def q(a, p):
    return float(np.percentile(a, p))


def summarise(r, out=sys.stdout):
    p = lambda *a: print(*a, file=out)
    mm = r["mm_per_vox"]
    d = np.asarray(r["d_vox"])
    res = np.asarray(r["resid_vox"])
    dn = np.asarray(r["node_d_vox"])
    zg = np.asarray(r["z"])

    p("== inputs " + "=" * 60)
    p(f"ours   {r['ours']['path']}: {r['ours']['n']} control points, "
      f"z {r['ours']['z'][0]:.0f}..{r['ours']['z'][1]:.0f}")
    p(f"       volume {r['ours']['volume']}  ->  {r['ours']['voxel_um']:.3f} um/voxel")
    p(f"prior  {r['prior']['path']}: {r['prior']['n']} control points, "
      f"z {r['prior']['z'][0]:.0f}..{r['prior']['z'][1]:.0f}")
    p(f"       sha256 {r['prior']['sha256']}")
    p(f"       {'MATCHES' if r['prior']['sha256'] == PRIOR_SHA256 else '!! DIFFERS FROM'} "
      f"the hash recorded in qc/prior_umbilicus_PHerc1218_SOURCE.md")
    p("")
    p("== overlap " + "=" * 59)
    p(f"z {r['overlap'][0]:.0f}..{r['overlap'][1]:.0f} "
      f"= {(r['overlap'][1] - r['overlap'][0]) * mm:.1f} mm of scroll, "
      f"{r['n_grid']} common-grid samples (their 64-voxel sampling), "
      f"{len(dn)} of our own nodes")
    covered = (r["overlap"][1] - r["overlap"][0]) / (r["prior"]["z"][1] - r["prior"]["z"][0])
    p(f"that is {100 * covered:.0f}% of the z their file spans; the rest is z "
      f"where only their file has points")
    p("")
    p("== distance between the two axes " + "=" * 37)
    p(f"{'':10} {'vox':>9} {'mm':>9}")
    for name, val in (("min", d.min()), ("p25", q(d, 25)), ("median", q(d, 50)),
                      ("p75", q(d, 75)), ("p90", q(d, 90)), ("max", d.max())):
        p(f"{name:10} {val:9.1f} {val * mm:9.2f}")
    p(f"max at z = {zg[int(np.argmax(d))]:.0f}")
    p(f"mean       {d.mean():9.1f} {d.mean() * mm:9.2f}")
    p("")
    p(f"at our {len(dn)} hand-placed nodes only (our file not interpolated at all):")
    p(f"{'median':10} {np.median(dn):9.1f} {np.median(dn) * mm:9.2f}")
    p(f"{'max':10} {dn.max():9.1f} {dn.max() * mm:9.2f}")
    p("")
    p("== is it concentrated in z? " + "=" * 42)
    p("(eight equal z bands over the overlap)")
    edges = np.linspace(zg.min(), zg.max(), 9)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (zg >= a) & (zg < b) if b < edges[-1] else (zg >= a) & (zg <= b)
        if m.sum():
            p(f"  z {a:7.0f} - {b:7.0f}  n={int(m.sum()):3d}  "
              f"median {np.median(d[m]) * mm:5.2f} mm  max {d[m].max() * mm:5.2f} mm")
    p("")
    p("== is it just our coarser sampling? " + "=" * 34)
    zo, yo, xo, _ = load_points(OURS)
    zp, yp, xp, _ = load_points(PRIOR)
    p(f"our node z step: median {np.median(np.diff(zo)):.0f} vox, "
      f"min {np.diff(zo).min():.0f}, max {np.diff(zo).max():.0f}; "
      f"theirs: median {np.median(np.diff(zp)):.0f} vox")
    keep = (zp >= r["overlap"][0]) & (zp <= r["overlap"][1])
    # their line pushed through our node grid and interpolated back: the most a
    # polyline sampled like ours could carry of a line sampled like theirs.
    lost = np.hypot(
        np.interp(zg, zo, np.interp(zo, zp, yp)) - yp[keep],
        np.interp(zg, zo, np.interp(zo, zp, xp)) - xp[keep]) * mm
    p(f"resampling THEIR line onto our node grid and back loses "
      f"median {np.median(lost):.2f} mm, p90 {np.percentile(lost, 90):.2f} mm, "
      f"max {lost.max():.2f} mm")
    p(f"-> the {q(d, 50) * mm:.2f} mm is "
      f"{'NOT explained' if np.median(lost) < 0.5 * q(d, 50) * mm else 'partly explained'}"
      f" by our sampling being coarser")
    p("")
    p("== is it a constant offset? " + "=" * 42)
    o = r["offset_vox"]
    p(f"mean (dy, dx) = ({o['dy']:+.1f}, {o['dx']:+.1f}) vox "
      f"= ({o['dy'] * mm:+.2f}, {o['dx'] * mm:+.2f}) mm, norm {o['norm']:.1f} vox "
      f"= {o['norm'] * mm:.2f} mm")
    p(f"residual after removing it: median {np.median(res):.1f} vox "
      f"= {np.median(res) * mm:.2f} mm, max {res.max():.1f} vox "
      f"= {res.max() * mm:.2f} mm")
    share = 1.0 - np.median(res) / np.median(d) if np.median(d) else float("nan")
    p(f"a single constant vector explains {100 * share:.0f}% of the median distance")
    p("")
    p("== verdict against the pre-registered bands " + "=" * 26)
    med_mm = q(d, 50) * mm
    p(f"median distance {med_mm:.2f} mm against the bands fixed beforehand:")
    p(f"  < {FLOOR_MM} mm   interchangeable for this package's own benefit test  "
      f"{'<-- HERE' if med_mm < FLOOR_MM else ''}")
    p(f"  < {STICK_MM} mm    smaller than the effect sections 5/6 measure           "
      f"{'<-- HERE' if FLOOR_MM <= med_mm < STICK_MM else ''}")
    p(f"  < {HEADLINE_MM} mm   the size of the effect this package claims            "
      f"{'<-- HERE' if STICK_MM <= med_mm < HEADLINE_MM else ''}")
    p(f"  >= {HEADLINE_MM} mm  larger than the Motivation number; comparison failed  "
      f"{'<-- HERE' if med_mm >= HEADLINE_MM else ''}")


# ------------------------------------------- post-hoc: where the mass is ----
def measure_centroid(volume, cache=None):
    """Per-slice centroids of the CT itself, at level CENT_LEVEL. Network."""
    import urllib.request
    base = f"{BUCKET}/{volume}/{CENT_LEVEL}"
    za = json.loads(urllib.request.urlopen(f"{base}/.zarray", timeout=180).read())
    shape, chunks = za["shape"], za["chunks"]
    if za["compressor"] is not None or za["dtype"] != "|u1" or za["order"] != "C":
        raise SystemExit(f"unexpected encoding {za}; this reader handles raw uint8 C-order only")
    scale = 2 ** CENT_LEVEL
    nz = -(-shape[0] // chunks[0])
    ny = -(-shape[1] // chunks[1])
    nx = -(-shape[2] // chunks[2])
    print(f"level {CENT_LEVEL}: shape {shape}, chunks {chunks}, "
          f"{nz * ny * nx} chunks, scale {scale} -> "
          f"{voxel_um({'source_volume': volume}) * scale:.1f} um per voxel")

    def get(cz, cy, cx):
        key = f"{cz}/{cy}/{cx}"
        if cache:
            p = os.path.join(cache, key.replace("/", "_") + ".raw")
            if os.path.exists(p):
                return open(p, "rb").read()
        try:
            blob = urllib.request.urlopen(f"{base}/{key}", timeout=300).read()
        except Exception:
            blob = b""                       # a missing chunk is all fill_value
        if cache:
            os.makedirs(cache, exist_ok=True)
            open(p, "wb").write(blob)
        return blob

    slices = {}
    for cz in range(nz):
        plane = np.zeros((chunks[0], ny * chunks[1], nx * chunks[2]), dtype=np.uint8)
        for cy in range(ny):
            for cx in range(nx):
                blob = get(cz, cy, cx)
                if not blob:
                    continue
                plane[:, cy * chunks[1]:(cy + 1) * chunks[1],
                      cx * chunks[2]:(cx + 1) * chunks[2]] = \
                    np.frombuffer(blob, dtype=np.uint8).reshape(chunks)
        plane = plane[:, :shape[1], :shape[2]]
        print(f"  chunk row z{cz}", flush=True)
        for k in range(chunks[0]):
            zl = cz * chunks[0] + k
            if zl >= shape[0]:
                break
            sl = plane[k]
            ys, xs = np.nonzero(sl)
            if ys.size < CENT_MIN_PX:
                continue
            w = sl[ys, xs].astype(np.float64)
            thr = np.percentile(w, CENT_TOP_PCT)
            m = w >= thr
            slices[str(zl)] = dict(
                nonzero=int(ys.size),
                mask_cy=float(ys.mean()), mask_cx=float(xs.mean()),
                int_cy=float((ys * w).sum() / w.sum()),
                int_cx=float((xs * w).sum() / w.sum()),
                pap_cy=float((ys[m] * w[m]).sum() / w[m].sum()),
                pap_cx=float((xs[m] * w[m]).sum() / w[m].sum()))
        del plane
    out = dict(volume=volume, level=CENT_LEVEL, scale=scale, shape=shape,
               min_nonzero_px=CENT_MIN_PX, top_percentile=CENT_TOP_PCT,
               slices=slices)
    with open(CENTROID, "wt") as fh:
        json.dump(out, fh)
    print(f"wrote {CENTROID} ({len(slices)} slices)")
    return out


def centroid_section(r, out=sys.stdout):
    """Which of the two lines does the CT's own mass centroid follow?"""
    p = lambda *a: print(*a, file=out)
    if not os.path.exists(CENTROID):
        p("(qc/prior_1218_centroid_raw.json absent; run --measure-centroid)")
        return None
    with open(CENTROID, "rt") as fh:
        c = json.load(fh)
    mm, sc = r["mm_per_vox"], c["scale"]
    zo, yo, xo, _ = load_points(OURS)
    zp, yp, xp, _ = load_points(PRIOR)
    lo, hi = r["overlap"]
    zl = np.array(sorted(int(k) for k in c["slices"]))
    z0 = zl * sc
    sel = (z0 >= lo) & (z0 <= hi)
    zs = z0[sel]
    oy, ox = np.interp(zs, zo, yo), np.interp(zs, zo, xo)
    py, px = np.interp(zs, zp, yp), np.interp(zs, zp, xp)

    p("")
    p("== post-hoc: where the CT's own mass centroid sits " + "=" * 19)
    p(f"level {c['level']} of the same volume, {mm * sc * 1000:.1f} um per voxel, "
      f"{len(zs)} slices in the overlap. NOT pre-registered - see the module "
      f"docstring.")
    p(f"{'centroid of':32} {'to OURS':>10} {'to PRIOR':>10}   prior closer on")
    res = {}
    for tag, label in (("mask", "the nonzero mask"),
                       ("int", "intensity, all nonzero"),
                       ("pap", f"intensity, top {100 - c['top_percentile']}% only")):
        cy = np.array([c["slices"][str(i)][tag + "_cy"] for i in zl[sel]]) * sc
        cx = np.array([c["slices"][str(i)][tag + "_cx"] for i in zl[sel]]) * sc
        d_o = np.hypot(cy - oy, cx - ox) * mm
        d_p = np.hypot(cy - py, cx - px) * mm
        wins = int((d_p < d_o).sum())
        p(f"{label:32} {np.median(d_o):8.2f}mm {np.median(d_p):8.2f}mm   "
          f"{wins}/{len(d_o)} slices")
        res[tag] = dict(z=zs, d_ours=d_o, d_prior=d_p, wins=wins, n=len(d_o))
    p("")
    p("Their generator says its points are the centroid of the papyrus mask. "
      "The CT agrees:")
    p("the mass centroid of these cross-sections lies on their line, not on "
      "ours. So the")
    p("distance measured above is the gap between a mass centroid and a "
      "hand-placed winding")
    p("centre - a property of the scroll - and not annotation error on either "
      "side.")
    return res


def cross_check_villa(villa_dir, r):
    """Re-evaluate ours through villa's own loader instead of np.interp."""
    sys.path.insert(0, os.path.join(villa_dir, "volume-cartographer", "scripts", "spiral"))
    from umbilicus import json_umbilicus_z_to_yx      # noqa: E402
    f = json_umbilicus_z_to_yx(OURS)
    zg = np.asarray(r["z"])
    yx = np.asarray(f(zg), dtype=float)
    zp, yp, xp, _ = load_points(PRIOR)
    keep = (zp >= r["overlap"][0]) & (zp <= r["overlap"][1])
    d = np.hypot(yx[:, 0] - yp[keep], yx[:, 1] - xp[keep])
    ours = np.asarray(r["d_vox"])
    print(f"villa loader cross-check: max |d_villa - d_here| = "
          f"{np.abs(d - ours).max():.4f} vox over {len(d)} samples "
          f"(float32 in the loader; anything under a voxel means the same line)")


# --------------------------------------------------------------- the figure --
def current_yardsticks():
    """The three yardstick distances as the shipped files give them TODAY,
    recomputed rather than copied from prose: the §6.4 sensitivity floor
    (with the 2026-08-20 finer-ladder floor beside it where those files are
    present), the §6 median stick distance, and the Motivation's largest
    deviation with the scroll that carries it.  The pre-registered verdict
    bands stay at their sealed 15 August values (FLOOR_MM, STICK_MM,
    HEADLINE_MM above) — these are for drawing only, so the panel shows the
    numbers the README currently states while the sealed verdict is printed
    unchanged."""
    import axis_benefit as AB
    from axis_stats import voxel_um, SCROLLS as ALL_SCROLLS
    floor = AB.control_table()["floor"][1]
    stick = AB.stick_distances()[1][0]
    dev, dev_scroll = 0.0, ""
    for s in ALL_SCROLLS:
        with open(os.path.join(ROOT, f"{s}_umbilicus.json")) as fh:
            d = json.load(fh)
        pts = sorted(d["control_points"], key=lambda p: p["z"])
        um = voxel_um(d["metadata"])
        xy = np.array([[p["x"], p["y"]] for p in pts], float)
        v = float(np.hypot(*(xy - xy.mean(0)).T).max()) * um / 1000.0
        if v > dev:
            dev, dev_scroll = v, s
    fine = None
    try:
        import stat_figures
        f = stat_figures.finegrid_floor()
        fine = f[1] if f else None
    except Exception:
        pass
    return floor, fine, stick, dev, dev_scroll


def figure(r):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    SURF, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
    C_ANN, C_BASE, C_NULL = "#eb6834", "#2a78d6", "#9b9890"
    GRID, SPINE = "#e8e6df", "#d8d6cf"

    def style(ax):
        ax.set_facecolor(SURF)
        ax.tick_params(colors=INK2, length=0, labelsize=8.5)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("bottom", "left"):
            ax.spines[s].set_color(SPINE)
        ax.grid(True, color=GRID, linewidth=0.7)
        ax.set_axisbelow(True)

    C_CT = "#2f8f5b"           # the CT's own mass centroid, the post-hoc line

    mm = r["mm_per_vox"]
    zo, yo, xo, _ = load_points(OURS)
    zp, yp, xp, _ = load_points(PRIOR)
    zg = np.asarray(r["z"])

    ct = None
    if os.path.exists(CENTROID):
        with open(CENTROID, "rt") as fh:
            c = json.load(fh)
        sc = c["scale"]
        zl = np.array(sorted(int(k) for k in c["slices"]))
        sel = (zl * sc >= r["overlap"][0]) & (zl * sc <= r["overlap"][1])
        ct = dict(
            z=zl[sel] * sc,
            y=np.array([c["slices"][str(i)]["mask_cy"] for i in zl[sel]]) * sc,
            x=np.array([c["slices"][str(i)]["mask_cx"] for i in zl[sel]]) * sc)
        ct["d_ours"] = np.hypot(ct["y"] - np.interp(ct["z"], zo, yo),
                                ct["x"] - np.interp(ct["z"], zo, xo)) * mm
        ct["d_prior"] = np.hypot(ct["y"] - np.interp(ct["z"], zp, yp),
                                 ct["x"] - np.interp(ct["z"], zp, xp)) * mm
    d = np.asarray(r["d_vox"]) * mm
    res = np.asarray(r["resid_vox"]) * mm
    lo, hi = r["overlap"]

    fig = plt.figure(figsize=(13.6, 9.4), facecolor=SURF)
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1.0, 1.0, 1.25],
                  hspace=0.46, wspace=0.20, left=0.062, right=0.985,
                  top=0.842, bottom=0.175)

    fig.text(0.062, 0.966,
             "PHerc1218: our hand-placed axis against the prior annotation",
             fontsize=15.5, color=INK, weight="bold")
    fig.text(0.062, 0.936,
             "the only scroll of our ten with an independent umbilicus  -  "
             "Iyan Dopico, vesuvius-sheet-tools, 6a831e0, 2026-07-21  -  "
             "both in level-0 voxels of 20250521120456-8.640um",
             fontsize=9.4, color=INK2)
    fig.text(0.062, 0.910,
             "his points are the CENTROID OF THE PAPYRUS MASK per slice; ours is a "
             "hand-placed winding centre. They are not defined to be the same point "
             "(README section 7).",
             fontsize=9.4, color=INK2, style="italic")

    for row, (ours_v, theirs_v, lab) in enumerate(
            ((xo, xp, "x"), (yo, yp, "y"))):
        ax = fig.add_subplot(gs[row, 0])
        style(ax)
        ax.axvspan(zp.min() * mm, lo * mm, color=GRID, zorder=0)
        ax.axvspan(hi * mm, zp.max() * mm, color=GRID, zorder=0)
        if ct is not None:
            ax.plot(ct["z"] * mm, ct[lab] * mm, color=C_CT, lw=2.6, alpha=0.32,
                    label="CT mass centroid (post-hoc)")
        ax.plot(zp * mm, theirs_v * mm, color=C_BASE, lw=1.3,
                label="prior (mask centroid)")
        ax.plot(zo * mm, ours_v * mm, color=C_ANN, lw=1.6, marker="o", ms=3.0,
                label="ours (hand-placed)")
        ax.set_ylabel(f"{lab}  (mm)", fontsize=9, color=INK2)
        if row == 0:
            ax.legend(fontsize=8.3, frameon=False, ncol=3, loc="lower center",
                      bbox_to_anchor=(0.5, 1.02), borderaxespad=0.0)
            ax.set_title("the two axes, component by component  "
                         "(grey = z only one file covers)",
                         fontsize=10, color=INK, loc="left", pad=24)
        else:
            ax.set_xlabel("z  (mm)", fontsize=9, color=INK2)

    ax = fig.add_subplot(gs[0:2, 1])
    style(ax)
    inp = (zp >= lo) & (zp <= hi)
    ino = (zo >= lo) & (zo <= hi)
    if ct is not None:
        ax.plot(ct["x"] * mm, ct["y"] * mm, color=C_CT, lw=3.2, alpha=0.30,
                label="CT mass centroid (post-hoc)")
    ax.plot(xp[inp] * mm, yp[inp] * mm, color=C_BASE, lw=1.2, alpha=0.9,
            label="prior (mask centroid)")
    ax.plot(xo[ino] * mm, yo[ino] * mm, color=C_ANN, lw=1.5, marker="o", ms=3.4,
            label="ours (hand-placed)")
    ax.set_xlabel("x  (mm)", fontsize=9, color=INK2)
    ax.set_ylabel("y  (mm)", fontsize=9, color=INK2)
    ax.set_aspect("equal", adjustable="datalim")
    ax.invert_yaxis()
    ax.legend(fontsize=8.5, frameon=False, loc="best")
    ax.set_title("looking down the scroll, over the overlapping z only",
                 fontsize=10, color=INK, loc="left")

    ax = fig.add_subplot(gs[2, 0])
    style(ax)
    xr = zg.max() * mm * 1.45
    floor_now, fine_now, stick_now, dev_now, dev_scroll = current_yardsticks()
    marks = [(dev_now, f"{dev_now:.1f} mm   the Motivation deviation ({dev_scroll})"),
             (stick_now, f"{stick_now:.2f} mm   median distance to the stick (section 6)"),
             (floor_now, f"{floor_now:.2f} mm   sensitivity floor (section 6.4)")]
    if fine_now is not None:
        marks.append((fine_now,
                      f"{fine_now:.2f} mm   finer-ladder floor, 20 Aug (section 6.4)"))
    for v, t in marks:
        ax.axhline(v, color=C_NULL, lw=1.0, ls="--")
        # the two floors sit ~0.9 mm apart: label one above, one below its line
        va = ("bottom" if v == floor_now else
              "top" if fine_now is not None and v == fine_now else "center")
        ax.text(xr, v, t + "  ", fontsize=7.8, color=INK2, va=va, ha="right")
    ax.plot(zg * mm, d, color=C_ANN, lw=1.4, label="distance between the two axes")
    ax.plot(zg * mm, res, color=C_BASE, lw=1.1, ls=":",
            label="after removing the mean offset")
    if ct is not None:
        ax.plot(ct["z"] * mm, ct["d_prior"], color=C_CT, lw=1.2,
                label=f"CT mass centroid to theirs  (median "
                      f"{np.median(ct['d_prior']):.2f} mm)")
        ax.plot(ct["z"] * mm, ct["d_ours"], color=C_CT, lw=1.0, ls="--", alpha=0.6,
                label=f"CT mass centroid to ours    (median "
                      f"{np.median(ct['d_ours']):.2f} mm)")
    ax.axhline(float(np.median(d)), color=C_ANN, lw=0.9, ls="-", alpha=0.45)
    ax.set_xlabel("z  (mm)", fontsize=9, color=INK2)
    ax.set_ylabel("distance  (mm)", fontsize=9, color=INK2)
    ax.set_ylim(0, max(dev_now * 1.08, d.max() * 1.15))
    ax.set_xlim(zg.min() * mm, xr)
    ax.legend(fontsize=8.0, frameon=False, loc="upper left",
              bbox_to_anchor=(0.005, 0.86))
    ax.set_title(f"disagreement along z  -  median {np.median(d):.2f} mm, "
                 f"max {d.max():.2f} mm at z = {zg[int(np.argmax(d))]:.0f}",
                 fontsize=10, color=INK, loc="left")

    ax = fig.add_subplot(gs[2, 1])
    style(ax)
    s = np.sort(d)
    ax.step(s, np.arange(1, s.size + 1) / s.size * 100, color=C_ANN, lw=1.6,
            where="post", label="distance")
    sr = np.sort(res)
    ax.step(sr, np.arange(1, sr.size + 1) / sr.size * 100, color=C_BASE, lw=1.2,
            ls=":", where="post", label="after removing the mean offset")
    xmax = max(stick_now * 1.12, s.max() * 1.15)
    vlines = [(floor_now, f"{floor_now:.2f}"), (stick_now, f"{stick_now:.2f}")]
    if fine_now is not None:
        vlines.insert(0, (fine_now, f"{fine_now:.2f}"))
    for v, t in vlines:
        ax.axvline(v, color=C_NULL, lw=1.0, ls="--")
        ax.text(v, 4, " " + t + " mm", fontsize=7.8, color=INK2, rotation=90,
                va="bottom", ha="left")
    ax.set_xlabel("distance  (mm)", fontsize=9, color=INK2)
    ax.set_ylabel("% of samples below", fontsize=9, color=INK2)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 101)
    ax.legend(fontsize=8.3, frameon=False, loc="lower right")
    ax.set_title(f"the whole distribution, not one number  "
                 f"({dev_now:.1f} mm is off this scale)",
                 fontsize=10, color=INK, loc="left")

    lines = ["Every number drawn is recomputed by scripts/prior_1218.py from the "
             "shipped json files and printed to stdout, so this panel can be checked "
             "as text.",
             f"The dashed yardsticks are the CURRENT values of those quantities; the "
             f"verdict bands sealed in qc/PRIOR1218_PREREGISTRATION.md stay at "
             f"{FLOOR_MM} / {STICK_MM} / {HEADLINE_MM} mm and the verdict is printed "
             f"against those."]
    if ct is not None:
        lines += [
            f"The green line is the CT's own mass centroid at level 5 of the same "
            f"volume. It sits on THEIR line ({np.median(ct['d_prior']):.2f} mm, closer "
            f"on {int((ct['d_prior'] < ct['d_ours']).sum())} of {len(ct['d_ours'])} "
            f"slices) - which is what their generator says it is.",
            f"So the {np.median(d):.2f} mm between the two files is the gap between a "
            f"mass centroid and a hand-placed winding centre: a difference of "
            f"definition, and a property of this scroll.",
            f"That diagnostic is post-hoc; the {np.median(d):.2f} mm is not. Agreement "
            f"does not make either file ground truth - two methods can share a bias."]
    for i, t in enumerate(lines):
        fig.text(0.062, 0.108 - 0.023 * i, t, fontsize=8.0, color=INK2)

    os.makedirs(PANELS, exist_ok=True)
    out = os.path.join(PANELS, "prior_1218_agreement.png")
    fig.savefig(out, dpi=140, facecolor=SURF)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true",
                    help="re-download the prior file and verify its sha256")
    ap.add_argument("--check-bucket", action="store_true",
                    help="re-read the level-0 shape and voxel size from the bucket")
    ap.add_argument("--villa", metavar="DIR",
                    help="a villa checkout, to re-run the interpolation through "
                         "scripts/spiral/umbilicus.py")
    ap.add_argument("--measure-centroid", action="store_true",
                    help="re-measure the CT centroid from the bucket (~48 MB) "
                         "and rewrite qc/prior_1218_centroid_raw.json")
    ap.add_argument("--cache", metavar="DIR",
                    help="cache directory for the raw chunks of --measure-centroid")
    ap.add_argument("--figure", action="store_true",
                    help="draw panels/prior_1218_agreement.png")
    ap.add_argument("--write-raw", action="store_true",
                    help="rewrite qc/prior_1218_raw.json")
    a = ap.parse_args()

    if a.fetch:
        fetch_prior()
    r = compare()
    if a.check_bucket:
        check_bucket(r["ours"]["volume"])
        print("")
    if a.measure_centroid:
        measure_centroid(r["ours"]["volume"], a.cache)
        print("")
    summarise(r)
    centroid_section(r)
    if a.villa:
        print("")
        cross_check_villa(a.villa, r)
    if a.write_raw:
        with open(RAW, "wt") as fh:
            json.dump(r, fh, indent=1)
        print("\nwrote", RAW)
    if a.figure:
        print("")
        figure(r)


if __name__ == "__main__":
    main()
