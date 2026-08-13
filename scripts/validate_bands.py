#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The same check, but per radial band: how far out from the axis the winding
is still concentric. Writes qc/validation_bands.json."""
import json, sys, time
import numpy as np
from PIL import Image
import validate_axes as V

BANDS = [(12, 60), (12, 120), (12, 200), (12, 340)]


def unwrap_band(img, cx, cy, rmin, rmax):
    H, W = img.shape
    th = np.arange(V.NTHETA) * (2 * np.pi / V.NTHETA)
    r = np.arange(rmin, rmax + 1, 1.0)
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
    tis = ((p00 > V.MASK_THR) & (p10 > V.MASK_THR) &
           (p01 > V.MASK_THR) & (p11 > V.MASK_THR))
    return val.astype(np.float32), (ok & tis)


def run(name):
    meta = json.load(open(f'{V.ROOT}/{name}/meta.json'))
    cp = json.load(open(f'{V.ROOT}/submission/{name}_umbilicus.json'))['control_points']
    out = []
    for s in V.all_slices(meta, cp):
        img = np.asarray(Image.open(f"{V.ROOT}/{name}/{s['file']}").convert('L'),
                         dtype=np.float32)
        ax = V.axis_at(cp, s['z']); cx, cy = ax[0] / V.SCALE, ax[1] / V.SCALE
        rec = dict(z=s['z'])
        for rmin, rmax in BANDS:
            # trend window — a quarter of the band, but not less than 15 px
            wtr = max(15, int(0.25 * (rmax - rmin)) | 1)
            v, m = unwrap_band(img, cx, cy, rmin, rmax)
            h0 = V.coherence(v, m, wtr, V.W_SMOOTH)[0]
            hs = []
            for a, b in ((37.5, 0), (-37.5, 0), (0, 37.5), (0, -37.5)):
                v2, m2 = unwrap_band(img, cx + a, cy + b, rmin, rmax)
                hs.append(V.coherence(v2, m2, wtr, V.W_SMOOTH)[0])
            hm = float(np.nanmean(hs))
            rec[f'{rmax}'] = dict(h=h0, hs=hm,
                                  r=h0 / hm if hm else float('nan'))
        out.append(rec)
        del img
    return out


if __name__ == '__main__':
    path = f'{V.QC}/validation_bands.json'
    data = {}
    for n in sys.argv[1:] or V.SCROLLS:
        t = time.time()
        data[n] = run(n)
        msg = ' '.join(
            f"r{b[1]}:{np.nanmedian([x[str(b[1])]['r'] for x in data[n]]):.2f}"
            for b in BANDS)
        print(f'{n} {msg} ({time.time() - t:.0f} s)', flush=True)
        json.dump(data, open(path, 'w'), ensure_ascii=False)
    print('written', path)
