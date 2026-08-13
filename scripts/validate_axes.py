#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validity check of the manual umbilicus annotation of the ten scrolls.

Method: polar unwrap around the annotated axis + a mandatory control with the
axis shifted by 150 and 300 L0 voxels in four directions.

Read-only. Writes:
  qc/валидация_PHercNNNN.png   — panels
  qc/validation_raw.json       — all the numbers
The ВАЛИДАЦИЯ_ОСЕЙ.md report is assembled separately (report_axes.py).

Data root: the repository root by default, override with the UMBILICI_ROOT
environment variable.
"""
import json, os, sys, time
import numpy as np
from PIL import Image

ROOT = os.environ.get(
    'UMBILICI_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QC = f'{ROOT}/qc'
SCROLLS = ['PHerc0191', 'PHerc0257', 'PHerc0268', 'PHerc0358', 'PHerc0800',
           'PHerc0813', 'PHerc1203', 'PHerc1218', 'PHerc1447', 'PHerc1545']

NTHETA = 512           # samples along the angle
RMIN, RMAX = 12, 340   # radii, L3 pixels
W_TREND = 61           # radial trend window, px (bandpass filter)
W_SMOOTH = 3           # smoothing window along the radius, px
MASK_THR = 10          # tissue threshold on the masked slice
SCALE = 8.0            # L0 voxels per L3 pixel
SHIFT_VOX = (150, 300)
GRID_R, GRID_STEP = 40.0, 5.0   # H map around the annotated point, L3 px


# -------------------------------------------------------------- axis
def axis_at(cp, z):
    """Axis (x, y) in L0 voxels at the given z: linear interpolation."""
    zs = [p['z'] for p in cp]
    if z < zs[0] or z > zs[-1]:
        return None
    i = int(np.searchsorted(zs, z))
    if i == 0:
        return float(cp[0]['x']), float(cp[0]['y'])
    a, b = cp[i - 1], cp[i]
    if b['z'] == a['z']:
        return float(a['x']), float(a['y'])
    t = (z - a['z']) / (b['z'] - a['z'])
    return a['x'] + t * (b['x'] - a['x']), a['y'] + t * (b['y'] - a['y'])


# ------------------------------------------------------------ unwrap
def unwrap(img, cx, cy):
    """Polar unwrap around (cx, cy), L3 pixels.

    Returns (val[NTHETA, NR], valid[NTHETA, NR]). Bilinear sampling;
    valid = all four supporting pixels are inside the frame and are tissue
    (>MASK_THR), so that the sample does not land on the mask border and
    produce a spurious "edge"."""
    H, W = img.shape
    th = np.arange(NTHETA) * (2 * np.pi / NTHETA)
    r = np.arange(RMIN, RMAX + 1, 1.0)
    X = cx + np.cos(th)[:, None] * r[None, :]
    Y = cy + np.sin(th)[:, None] * r[None, :]
    x0 = np.floor(X).astype(np.int32); y0 = np.floor(Y).astype(np.int32)
    ok = (x0 >= 0) & (x0 < W - 1) & (y0 >= 0) & (y0 < H - 1)
    xc = np.clip(x0, 0, W - 2); yc = np.clip(y0, 0, H - 2)
    fx = (X - xc).astype(np.float32); fy = (Y - yc).astype(np.float32)
    p00 = img[yc, xc]; p10 = img[yc, xc + 1]
    p01 = img[yc + 1, xc]; p11 = img[yc + 1, xc + 1]
    val = ((p00 * (1 - fx) + p10 * fx) * (1 - fy) +
           (p01 * (1 - fx) + p11 * fx) * fy)
    tis = ((p00 > MASK_THR) & (p10 > MASK_THR) &
           (p01 > MASK_THR) & (p11 > MASK_THR))
    return val.astype(np.float32), (ok & tis)


def _box(a, w):
    c = np.cumsum(np.pad(a, ((0, 0), (w // 2 + 1, w // 2))), axis=1)
    return c[:, w:] - c[:, :-w]


def bandpass(val, valid, w_tr=W_TREND, w_sm=W_SMOOTH):
    """Mask-aware bandpass filter along the radius: we remove the radial
    density trend (window w_tr) and the fine noise (window w_sm)."""
    v = valid.astype(np.float32)
    p = np.where(valid, val, 0).astype(np.float32)
    tr = _box(p, w_tr) / np.maximum(_box(v, w_tr), 1e-6)
    d = np.where(valid, p - tr, 0)
    if w_sm > 1:
        d = np.where(valid, _box(d, w_sm) / np.maximum(_box(v, w_sm), 1e-6), 0)
    return d.astype(np.float32)


def coherence(val, valid, w_tr=W_TREND, w_sm=W_SMOOTH):
    """Measure H of how straight the bands are: the fraction of the energy of
    the banded pattern that survives averaging over the angle.

    d(theta, r) is the bandpassed unwrap. For each radius we take
    m(r) = mean of d over all angles that carry tissue, and e(r) = mean square
    of d. H = sum_r m(r)^2 / sum_r e(r) over the radii covered by more than
    half of the angles. Bands strictly horizontal -> averaging over the angle
    destroys nothing, H -> 1. Bands wander along the radius -> under averaging
    they cancel each other out, H -> 0. The measure is dimensionless and does
    not depend on brightness or on the winding period."""
    d = bandpass(val, valid, w_tr, w_sm)
    v = valid.astype(np.float32)
    n = v.sum(0)
    good = n > 0.5 * val.shape[0]
    if good.sum() < 20:
        return np.nan, 0.0
    m = (d * v).sum(0) / np.maximum(n, 1e-6)
    e = (d * d * v).sum(0) / np.maximum(n, 1e-6)
    return (float((m[good] ** 2).sum() / max(float(e[good].sum()), 1e-12)),
            float(good.sum()))


# ---------------------------------------------------------------- map
def h_map(img, cx, cy, rad=GRID_R, step=GRID_STEP):
    g = np.arange(-rad, rad + 1e-6, step)
    H = np.full((len(g), len(g)), np.nan)
    for i, dy in enumerate(g):
        for j, dx in enumerate(g):
            v, m = unwrap(img, cx + dx, cy + dy)
            H[i, j] = coherence(v, m)[0]
    k = np.unravel_index(np.nanargmax(H), H.shape)
    interior = 0 < k[0] < len(g) - 1 and 0 < k[1] < len(g) - 1
    dy, dx = g[k[0]], g[k[1]]
    if interior:                      # sub-pixel refinement by parabola fit
        for ax, kk in ((1, k[1]), (0, k[0])):
            a, b, c = (H[k[0], kk - 1], H[k]. item(), H[k[0], kk + 1]) if ax == 1 \
                else (H[kk - 1, k[1]], H[k].item(), H[kk + 1, k[1]])
            den = a - 2 * b + c
            sh = 0.5 * (a - c) / den * step if abs(den) > 1e-12 else 0.0
            sh = float(np.clip(sh, -step, step))
            if ax == 1:
                dx += sh
            else:
                dy += sh
    med = float(np.nanmedian(H))
    return dict(grid=g.tolist(), H=H.tolist(), dx=float(dx), dy=float(dy),
                dist=float(np.hypot(dx, dy)), hmax=float(np.nanmax(H)),
                hmed=med, interior=bool(interior),
                sharp=bool(interior and np.nanmax(H) > 1.3 * med))


# ------------------------------------------------------------- slices
def pick_slices(meta, cp, n=6):
    zs = [p['z'] for p in cp]
    cand = [s for s in meta['slices'] if zs[0] <= s['z'] <= zs[-1]]
    if len(cand) <= n:
        return cand
    idx = np.linspace(0, len(cand) - 1, n).round().astype(int)
    return [cand[i] for i in idx]


def all_slices(meta, cp):
    zs = [p['z'] for p in cp]
    return [s for s in meta['slices'] if zs[0] <= s['z'] <= zs[-1]]


def analyse(name, want_map=True):
    meta = json.load(open(f'{ROOT}/{name}/meta.json'))
    cp = json.load(open(f'{ROOT}/submission/{name}_umbilicus.json'))['control_points']
    recs = []
    panel_z = {s['z'] for s in pick_slices(meta, cp, 6)}
    for s in all_slices(meta, cp):
        img = np.asarray(Image.open(f"{ROOT}/{name}/{s['file']}").convert('L'),
                         dtype=np.float32)
        ax = axis_at(cp, s['z'])
        cx, cy = ax[0] / SCALE, ax[1] / SCALE
        v, m = unwrap(img, cx, cy)
        h0, nr0 = coherence(v, m)
        rec = dict(z=s['z'], file=s['file'], cx=cx, cy=cy, h=h0, nrad=nr0,
                   panel=s['z'] in panel_z)
        for sv in SHIFT_VOX:
            d = sv / SCALE
            hs = []
            for a, b in ((d, 0), (-d, 0), (0, d), (0, -d)):
                v2, m2 = unwrap(img, cx + a, cy + b)
                hs.append(coherence(v2, m2)[0])
            rec[f'h{sv}'] = hs
            rec[f'h{sv}_mean'] = float(np.nanmean(hs))
        rec['r150'] = rec['h'] / rec['h150_mean'] if rec['h150_mean'] else np.nan
        rec['r300'] = rec['h'] / rec['h300_mean'] if rec['h300_mean'] else np.nan
        if want_map:
            rec['map'] = h_map(img, cx, cy)
        recs.append(rec)
        del img
    return recs


if __name__ == '__main__':
    names = sys.argv[1:] or SCROLLS
    os.makedirs(QC, exist_ok=True)
    path = f'{QC}/validation_raw.json'
    out = {}
    if os.path.exists(path):
        out = json.load(open(path))
    for n in names:
        t = time.time()
        out[n] = analyse(n)
        r3 = [r['r300'] for r in out[n]]
        r15 = [r['r150'] for r in out[n]]
        dd = [r['map']['dist'] for r in out[n] if r['map']['sharp']]
        print(f"{n}: median R300={np.nanmedian(r3):.2f} R150={np.nanmedian(r15):.2f} "
              f"| slices with R300>1: {int(np.sum(np.array(r3) > 1))}/{len(r3)} "
              f"| sharp maps {len(dd)}/{len(r3)}, median |offset| "
              f"{np.median(dd) if dd else float('nan'):.1f} px "
              f"({time.time() - t:.0f} s)", flush=True)
        json.dump(out, open(path, 'w'), ensure_ascii=False)
    print('written', path)
