#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""panels/calibration_summary.png — two panels, two different questions.

Left: what the ring-symmetry verdict is made of (share of OK/fair, "the
detector's candidate is better", "detector not applicable"). sean and we are
indistinguishable here: the gate measures how crushed the cross-section is, not
how well it was annotated.

Right: the kink of the axis polyline (median deviation of a point from the
chord between its z-neighbours) after thinning both sides towards a 480-voxel
z-step, because the sparser the points, the larger the kink by itself. The
thinning keeps the nearest existing point to each target, so it only makes a
dense polyline sparser: it brings sean's three to a realized median step of
465-474, but it cannot lift ours off the spacing they were annotated at, and
those run 336-640. The realized step is therefore printed beside every bar, and
the bars must be read as "kink at that step", not as a matched comparison. The
difference is not in our favour under any of the three columns
`axis_stats.py` prints; only its size depends on which one is used.

Reads `qc/calibration_sean.json` written by calib_sean.py, and the axis json
files themselves. Covers all ten shipped scrolls, not the three the earlier
version of this figure used.

    python3 scripts/calib_sean.py && python3 scripts/calib_figure.py
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calib_sean import ROOT, TREE, SETS            # noqa: E402
from axis_stats import kink, med_step, subsample   # noqa: E402

STEP = 480.0          # the z-step both sides are brought to

SURF = "#fcfcfb"
INK, INK2 = "#0b0b0b", "#52514e"
C_SEAN, C_OUR = "#2a78d6", "#eb6834"
V_OK, V_CAND, V_NA = "#0ca30c", "#fab219", "#b8b6ae"


def main():
    data = json.load(open(os.path.join(ROOT, "qc", "calibration_sean.json")))
    src = {name: (who, jp) for who, name, jp, _ in SETS}
    names = [n for n in src if n in data]
    who = {n: src[n][0] for n in names}
    lab = [f"{n}\n{who[n]}" for n in names]
    y = np.arange(len(names))[::-1]

    ks, st = {}, {}
    for n in names:
        base = TREE if src[n][1].startswith("ref_sean/") else ROOT
        pts = json.load(open(os.path.join(base, src[n][1])))["control_points"]
        thin = subsample(pts, STEP)
        ks[n] = kink(thin)
        st[n] = med_step(thin)      # what the thinning actually achieved

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 8.6), facecolor=SURF)
    fig.subplots_adjust(left=0.10, right=0.985, top=0.885, bottom=0.20, wspace=0.40)

    # --- panel 1: what the ring gate's verdict is made of
    ax1.set_facecolor(SURF)
    left = np.zeros(len(names))
    for key, col, nm in (("frac_ok", V_OK, "OK / fair"),
                         ("frac_cand", V_CAND, "detector's candidate is better"),
                         ("frac_na", V_NA, "detector not applicable")):
        w = np.array([data[n]["stats"][key] * 100 for n in names])
        ax1.barh(y, w, left=left, height=0.62, color=col, label=nm,
                 edgecolor=SURF, linewidth=2)
        for yy, ww, ll in zip(y, w, left):
            if ww >= 12:
                ax1.text(ll + ww / 2, yy, f"{ww:.0f}%", ha="center", va="center",
                         color="#ffffff" if col != V_NA else INK, fontsize=10)
        left += w
    ax1.set_xlim(0, 100)
    ax1.set_title("Ring gate: what the verdict is made of\n"
                  "sean and we sit in the same regime",
                  fontsize=11, color=INK, loc="left")
    ax1.set_xlabel("share of points, %", fontsize=10, color=INK2)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=1,
               frameon=False, fontsize=9.5, labelcolor=INK2)

    # --- panel 2: kink of the polyline at a common z-step
    ax2.set_facecolor(SURF)
    vals = np.array([ks[n] for n in names])
    cols = [C_SEAN if who[n] == "sean" else C_OUR for n in names]
    ax2.barh(y, vals, height=0.62, color=cols)
    band = [ks[n] for n in names if who[n] == "sean"]
    ax2.axvspan(min(band), max(band), color=C_SEAN, alpha=0.10, zorder=0)
    for yy, n in zip(y, names):
        ax2.text(ks[n] + 8, yy, f"{ks[n]:.0f}", va="center", fontsize=10, color=INK)
        ax2.text(ks[n] + 8, yy - 0.30, f"at a {st[n]:.0f}-vox step", va="center",
                 fontsize=8, color=INK2)
    ax2.set_xlim(0, max(vals) * 1.42)
    inside = sum(1 for n in names
                 if who[n] == "ours" and min(band) <= ks[n] <= max(band))
    ours_st = [st[n] for n in names if who[n] == "ours"]
    sean_st = [st[n] for n in names if who[n] == "sean"]
    ax2.set_title(f"Kink of the axis after thinning towards a {STEP:.0f}-voxel z-step\n"
                  f"lower is smoother; sean's band ({min(band):.0f}-{max(band):.0f}) is shaded — "
                  f"{inside} of our ten\nfalls inside it. The thinning only drops points, so it "
                  f"reaches\n{min(sean_st):.0f}-{max(sean_st):.0f} vox on sean's side but "
                  f"{min(ours_st):.0f}-{max(ours_st):.0f} on ours: read each bar\n"
                  f"at the step printed under it, not as a matched comparison.",
                  fontsize=10, color=INK, loc="left")
    ax2.set_xlabel("median deviation from the chord between neighbours, voxels",
                   fontsize=10, color=INK2)
    hs = [plt.Rectangle((0, 0), 1, 1, color=C_SEAN),
          plt.Rectangle((0, 0), 1, 1, color=C_OUR)]
    ax2.legend(hs, ["sean's annotation", "our annotation"], loc="upper center",
               bbox_to_anchor=(0.5, -0.10), ncol=1, frameon=False,
               fontsize=9.5, labelcolor=INK2)

    for ax in (ax1, ax2):
        ax.set_yticks(y)
        ax.set_yticklabels(lab, fontsize=9.5, color=INK)
        ax.tick_params(colors=INK2, length=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#d8d6cf")
        ax.xaxis.grid(True, color="#e8e6df", linewidth=0.8)
        ax.set_axisbelow(True)

    outdir = os.path.join(ROOT, "panels")
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, "calibration_summary.png")
    fig.savefig(p, dpi=140, facecolor=SURF)
    print("wrote", p)


if __name__ == "__main__":
    sys.exit(main())
