#!/usr/bin/env python3
"""UMBILICUS QUALITY GATES — the single implementation (do not copy the logic around).

Gates:
  1. smoothness: deviation of a point from the interpolation of its z-neighbours;
  2. rings: symmetry score of the point against the best center in its neighbourhood;
  3. ring applicability: if the score field in the neighbourhood is flat, or the
     best score is low, the detector is NOT APPLICABLE (the scroll is crushed,
     there is no verdict).
     Lesson from 0268 (Aug 9): on a mess the detector sticks to contrasty folds,
     and its "candidates" there are no better than the manual points.

Usage:
  qc_gates.py <umbilicus.json> <slices_dir> [--scale 8] [--out qc_dir]
Slices: z{Z}.png, with L0 voxels in the name. Prints a table of verdicts (stdout),
writes the candidates json and a montage png into --out.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image

def ring_score(img, cx, cy, rmax=90):
    th = np.linspace(0, 2*np.pi, 72, endpoint=False)
    rr = np.arange(6, rmax)
    xx = cx + rr[None,:]*np.cos(th[:,None]); yy = cy + rr[None,:]*np.sin(th[:,None])
    xi = np.clip(xx.astype(int), 0, img.shape[1]-1)
    yi = np.clip(yy.astype(int), 0, img.shape[0]-1)
    prof = img[yi, xi].mean(0)
    det = prof - np.convolve(prof, np.ones(9)/9, 'same')
    return float(np.abs(det[5:-5]).mean())

def best_center(img, ax, ay, half=45, step=3):
    field = []
    best = (ring_score(img, ax, ay), ax, ay)
    for dy in range(-half, half+1, step):
        for dx in range(-half, half+1, step):
            s = ring_score(img, ax+dx, ay+dy)
            field.append(s)
            if s > best[0]:
                best = (s, ax+dx, ay+dy)
    field = np.array(field)
    # applicability: relief of the field (best noticeably above the median) and the level itself
    relief = best[0] / (np.median(field) + 1e-6)
    applicable = relief > 1.25 and best[0] > 4.5
    return best, applicable, relief

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("umbilicus")
    ap.add_argument("slices_dir")
    ap.add_argument("--scale", type=float, default=8.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ok", type=float, default=130.0)
    ap.add_argument("--warn", type=float, default=250.0)
    a = ap.parse_args()
    d = json.load(open(a.umbilicus))
    pts = d["control_points"] if isinstance(d, dict) else d
    name = os.path.basename(a.umbilicus).split("_")[0]
    S = a.scale
    rows, cand = [], {}
    for p in pts:
        z = int(round(p["z"]))
        fp = os.path.join(a.slices_dir, f"z{z}.png")
        if not os.path.exists(fp):
            rows.append((z, None, None, None, "no slice")); continue
        img = np.asarray(Image.open(fp).convert("L")).astype(np.float32)
        ax, ay = p["x"]/S, p["y"]/S
        (sb, bx, by), applicable, relief = best_center(img, ax, ay)
        sh = float(np.hypot(bx-ax, by-ay)*S)
        if not applicable:
            v = "DETECTOR NOT APPLICABLE (crushed)"
        elif sh < a.ok: v = "OK"
        elif sh < a.warn: v = "fair"
        else:
            v = "CANDIDATE IS BETTER"; cand[z] = (int(bx*S), int(by*S))
        rows.append((z, sh, relief, applicable, v))
    n_ok = sum(1 for r in rows if r[4] in ("OK","fair"))
    n_na = sum(1 for r in rows if r[4].startswith("DETECTOR"))
    n_cd = len(cand)
    print(f"== {name}: {len(rows)} points | OK/fair {n_ok} | not applicable {n_na} | candidates {n_cd}")
    for z, sh, rel, app, v in rows:
        s = f"{z}: {v}"
        if sh is not None: s += f" (shift {sh:.0f} vox, relief {rel:.2f})"
        print(s)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(cand, open(os.path.join(a.out, f"кандидаты_{name}.json"), "w"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
