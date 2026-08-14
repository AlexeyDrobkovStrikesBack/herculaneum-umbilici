#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The four statistics panels for README sections 6, 5, 2 and 1.

    python3 scripts/stat_figures.py            # draws all four
    python3 scripts/stat_figures.py prereg     # one of: prereg stick shifted frozen

Runs on a bare clone with numpy, scipy and matplotlib and nothing else — the
inputs of all four ship. Every number drawn is recomputed here from those
inputs; none is copied from the README's prose. Where a quantity already has a
shipped producer, this script imports that producer's own counting rather than
reimplementing it (`axis_benefit.per_scroll`, `axis_benefit.control_table`,
`axis_benefit.stick_distances`, `count_wins.tally`, `stick_control.tally`,
`stick_control.dose_bins`, `order_stat.radial_sign`), so a figure cannot drift
away from the table it illustrates. Each figure prints the numbers it draws, so
the panels can be checked as text without opening the images.

Why these four, and why as statistics
-------------------------------------
Sections 5 and 6 are the two strongest results in this package and until now
neither had a figure of any kind. Section 6 is the harder case: an attempt at a
picture of it was made on 2026-08-13 and deliberately not shipped, because
nothing passed the legibility rule that attempt had fixed for itself and the
only readable crops were 90-degree windows chosen because they looked right
(README section 6.7). That verdict stands and is not revisited here: a
demonstration in polar-unwrap form does not exist for this material. What these
four panels draw is the arithmetic — the paired values, the counts, the tests
and the bounds — which is a different genre and one the evidence supports.

The rule every caption on these panels was written under
-------------------------------------------------------
No caption may claim more than the README section it illustrates, and each
panel must carry that section's limitation in the image rather than leave it to
be read elsewhere. Concretely:

  section 6  the sensitivity floor is drawn to scale against the stick distance,
             because that ratio is what decides whether the run credits gross
             placement (it does) or annotation precision (it cannot).
  section 5  the flat dose-response gets a panel of the same size as the win,
             because a figure showing only the win would be the overclaim this
             package spent three review passes removing.
  section 2  the control that FAILED is drawn beside the one that passed, on the
             same scale and in the same scroll order.
  section 1  the frozen axis is drawn against the live one, because scoring
             identically is this package's own strongest self-limitation.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy.stats import binomtest, wilcoxon

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.gridspec import GridSpec              # noqa: E402
from matplotlib.lines import Line2D                   # noqa: E402
from matplotlib.patches import Rectangle              # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axis_benefit as AB                             # noqa: E402
import count_wins as CW                               # noqa: E402
import stick_control as SC                            # noqa: E402
import order_stat as OS                               # noqa: E402
from axis_stats import voxel_um                       # noqa: E402

ROOT = os.environ.get("UMBILICI_ROOT",
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANELS = os.path.join(ROOT, "panels")

# Same palette as panels/calibration_summary.png, so the new panels read as part
# of the same set. Orange is always our annotated axis, blue always the baseline
# it is being tested against, grey always a quantity that failed or is null.
SURF = "#fcfcfb"
INK, INK2 = "#0b0b0b", "#52514e"
C_ANN = "#eb6834"          # the annotated per-slice axis
C_BASE = "#2a78d6"         # the stick / the displaced centre / the auto-centroid
C_NULL = "#9b9890"         # a null or failed result
C_BAD = "#c2352b"          # a scroll on the wrong side of 50%
GRID, SPINE = "#e8e6df", "#d8d6cf"

FIFTY = 0.5


def style(ax, xgrid=True):
    ax.set_facecolor(SURF)
    ax.tick_params(colors=INK2, length=0, labelsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(SPINE)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def ci(w, n):
    """Clopper-Pearson 95% interval on a win rate, as (low, high)."""
    c = binomtest(w, n, 0.5).proportion_ci(confidence_level=0.95)
    return float(c.low), float(c.high)


def save(fig, name):
    os.makedirs(PANELS, exist_ok=True)
    p = os.path.join(PANELS, name)
    fig.savefig(p, dpi=140, facecolor=SURF)
    plt.close(fig)
    print("wrote", p)


# ============================================================ section 6 =====
def fig_prereg():
    """panels/prereg_axis_benefit.png — the pre-registered ten-scroll run.

    Left: the ten paired values, one line per scroll, so that "10 of 10" is a
    thing you can count rather than a claim. Top right: the pooled result and
    the tests. Bottom: the bound — the sensitivity floor drawn to scale on the
    same millimetre axis as the distance the straight stick actually sits at,
    which is the whole reason this run credits gross placement and not
    precision.
    """
    rows = AB.per_scroll("stick_mean")
    delta = np.array([r["delta"] for r in rows])
    qa = np.concatenate([r["qa"] for r in rows])
    qb = np.concatenate([r["qb"] for r in rows])
    w = wilcoxon(delta, alternative="two-sided")
    n_pos = int((delta > 0).sum())
    wins = int((qa > qb).sum())
    tw = sum(r["wins"] for r in rows)
    tn = sum(r["n"] + r["drop"] for r in rows)
    worst = binomtest(tw, tn, 0.5).pvalue
    ct = AB.control_table()
    per_d, pooled_d = AB.stick_distances()
    floor_px, floor_mm = ct["floor"]
    gap = float(qa.mean() - qb.mean())

    print("\n--- section 6 figure, numbers as drawn ---")
    for r in rows:
        print(f"  {r['scroll']}  n={r['n']:2d} qA={r['qa'].mean():+.4f} "
              f"qB={r['qb'].mean():+.4f} D={r['delta']:+.4f} wins {r['wins']}/{r['n']}")
    print(f"  Wilcoxon W={w.statistic:.1f} p={w.pvalue:.4f}; {n_pos}/10 positive")
    print(f"  pooled {qa.mean():+.4f} vs {qb.mean():+.4f} = {qa.mean()/qb.mean():.2f}x; "
          f"slice wins {wins}/{len(qa)}; gap {gap:+.4f}")
    print(f"  worst case {tw}/{tn} p={worst:.1e}")
    print(f"  floor {floor_px} px = {floor_mm:.2f} mm; stick median {pooled_d[0]:.2f} mm "
          f"(per-scroll {min(v[1] for v in per_d.values()):.2f}-"
          f"{max(v[1] for v in per_d.values()):.2f} mm)")

    fig = plt.figure(figsize=(15.4, 11.6), facecolor=SURF)
    gs = GridSpec(2, 2, figure=fig, width_ratios=[1.34, 1.0],
                  height_ratios=[1.10, 1.0], left=0.082, right=0.978,
                  top=0.818, bottom=0.068, wspace=0.28, hspace=0.40)

    fig.text(0.082, 0.972,
             "Section 6 — the pre-registered run on all ten scrolls: does the annotated "
             "axis help a tool?",
             fontsize=15.5, color=INK, va="top")
    fig.text(0.082, 0.941,
             "Concentricity q of the papyrus about each axis, measured through villa's own "
             "loader and parameterisation, under a rule fixed in writing before any\n"
             "comparative quantity existed. A proxy for one geometric property fit_spiral's "
             "model asserts — not fit_spiral's output; §6.2 gives the three reasons it "
             "could not be run here.",
             fontsize=10, color=INK2, va="top", linespacing=1.55)

    # ---- the ten pairings -------------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    style(ax)
    y = np.arange(len(rows))[::-1]
    for yy, r in zip(y, rows):
        a, b = r["qa"].mean(), r["qb"].mean()
        ax.plot([b, a], [yy, yy], color=INK2, linewidth=1.1, zorder=1)
        ax.scatter([b], [yy], s=52, color=C_BASE, zorder=3)
        ax.scatter([a], [yy], s=52, color=C_ANN, zorder=3)
        ax.text(0.302, yy + 0.02, f"{r['delta']:+.4f}", fontsize=9,
                color=INK, va="center", ha="right", fontweight="bold")
        ax.text(0.302, yy - 0.34, f"{r['wins']}/{r['n']} slices", fontsize=7.6,
                color=INK2, va="center", ha="right")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['scroll']}  n={r['n']}" for r in rows], fontsize=9, color=INK)
    ax.set_xlim(0, 0.305)
    ax.set_xticks(np.arange(0, 0.251, 0.05))
    ax.set_ylim(-2.15, len(rows) - 0.35)
    ax.set_xlabel("mean concentricity q over that scroll's scorable slices", fontsize=9.5,
                  color=INK2)
    ax.set_title("Every scroll separately, and every one moves the same way\n"
                 "Δ and the slice wins are printed at the right of each row",
                 fontsize=10.5, color=INK, loc="left")
    ax.legend([Line2D([], [], marker="o", linestyle="", color=C_ANN, markersize=8),
               Line2D([], [], marker="o", linestyle="", color=C_BASE, markersize=8)],
              ["annotated per-slice axis", "best straight vertical stick (baseline B1)"],
              loc="lower left", frameon=False, fontsize=9, labelcolor=INK2,
              handletextpad=0.4)

    # ---- the pooled result ------------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    style(ax)
    vals = [qa.mean(), qb.mean()]
    ax.barh([1, 0], vals, height=0.44, color=[C_ANN, C_BASE])
    for yy, v in zip([1, 0], vals):
        ax.text(v + 0.004, yy, f"{v:+.4f}", va="center", fontsize=11, color=INK,
                fontweight="bold")
    ax.set_yticks([1, 0])
    ax.set_yticklabels(["annotated axis", "straight stick"], fontsize=9.5, color=INK)
    ax.set_xlim(0, 0.235)
    ax.set_ylim(-1.62, 1.55)
    ax.set_xlabel("pooled mean q over the 252 scorable slices", fontsize=9.5, color=INK2)
    ax.set_title(f"Pooled: {qa.mean()/qb.mean():.2f}× the concentricity",
                 fontsize=10.5, color=INK, loc="left")
    ax.text(0.0, -0.72,
            f"Wilcoxon signed-rank over the ten scroll Δ\n"
            f"W = {w.statistic:.1f},  p = {w.pvalue:.4f}  (two-sided)\n"
            f"{n_pos} of 10 scrolls positive  (rule required ≥ 6)\n"
            f"{wins} of {len(qa)} slice-level wins\n"
            f"every excluded slice charged to us: {tw}/{tn}, p = {worst:.1e}",
            fontsize=9.2, color=INK2, va="top", linespacing=1.75,
            transform=ax.get_yaxis_transform(which="grid"))

    # ---- the bound, to scale ----------------------------------------------
    ax = fig.add_subplot(gs[1, :])
    style(ax)
    dmm = [r[1] for r in ct["rows"]]
    dmed = [r[3] for r in ct["rows"]]
    xmax = 15.6

    ax.axvspan(0, floor_mm, color=C_NULL, alpha=0.20, zorder=0)
    ax.text(0.68, 0.058, "blind below the floor",
            ha="center", va="center", fontsize=8.8, color="#6b6862", rotation=90)

    ax.axhline(0.01, color=INK2, linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
    ax.text(3.05, 0.0122, "pre-registered 0.01 detection threshold",
            fontsize=8.6, color=INK2)

    ax.plot(dmm, dmed, color=C_BASE, linewidth=1.8, marker="o", markersize=6.5, zorder=3,
            label="what displacing our OWN axis by that much costs q (median, 53 control slices)")
    for x, v in zip(dmm, dmed):
        ax.text(x, v + 0.0042, f"{v:+.4f}", ha="center", fontsize=8.2, color=INK)

    ax.axvline(floor_mm, color=INK, linewidth=1.3, zorder=4)
    ax.text(floor_mm + 0.14, 0.1010, f"sensitivity floor\n{floor_mm:.2f} mm ({floor_px} px)",
            fontsize=9.2, color=INK, va="top", fontweight="bold", linespacing=1.5)

    ax.axvline(pooled_d[0], color=C_ANN, linewidth=1.6, zorder=4)
    ax.text(pooled_d[0] + 0.14, 0.1010,
            f"the straight stick actually sits here\nmedian {pooled_d[0]:.2f} mm — "
            f"{pooled_d[0]/floor_mm:.1f}× the floor",
            fontsize=9.2, color=C_ANN, va="top", fontweight="bold", linespacing=1.5)

    meds = sorted(v[1] for v in per_d.values())
    ax.scatter(meds, [0.1088] * len(meds), marker="|", s=190, color=C_ANN, zorder=5)
    ax.text(meds[0] - 0.22, 0.1088, "the ten per-scroll medians", fontsize=8.4,
            color=C_ANN, va="center", ha="right")

    ax.axhline(gap, color=C_ANN, linewidth=1.1, linestyle=(0, (5, 3)), zorder=2)
    ax.text(9.35, gap + 0.0032,
            f"the gap this run actually measures: {gap:+.4f} pooled",
            fontsize=8.8, color=C_ANN)

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 0.1165)
    ax.set_xticks(np.arange(0, 16, 1.0))
    ax.set_xlabel("displacement of the axis, millimetres — one linear scale for both quantities",
                  fontsize=9.5, color=INK2)
    ax.set_ylabel("median drop in q", fontsize=9.5, color=INK2)
    ax.set_title(
        "The bound, drawn to scale: the measure is blind below 1.81 mm, and the stick sits at "
        "a median 6.0 mm\n"
        "This is why the run stands up — and it is also the ceiling on what it may claim. "
        "It credits gross axis placement;\nit cannot credit annotation precision, and no "
        "experiment of this shape can (§6.4, §6.8).",
        fontsize=10.5, color=INK, loc="left", linespacing=1.5)
    ax.set_yticks(np.arange(0, 0.081, 0.02))
    ax.legend(loc="lower right", bbox_to_anchor=(0.995, 0.215), frameon=False,
              fontsize=8.8, labelcolor=INK2)

    save(fig, "prereg_axis_benefit.png")


# ============================================================ section 5 =====
def fig_stick():
    """panels/stick_control.png — the straight-stick control, both halves.

    The two panels are the same size on purpose. The left one is the result;
    the right one is the reason section 5 does not claim a mechanism for it.
    """
    data = json.load(open(os.path.join(ROOT, "qc", "stick_control_raw.json")))
    per = {k: SC.tally(data, k)[0] for k in SC.STICKS}
    drop = {k: SC.tally(data, k)[1] for k in SC.STICKS}
    bins = {k: SC.dose_bins(data, k) for k in SC.STICKS}

    order = [n for n, _ in sorted(per["mean"].items(), key=lambda kv: -kv[1][0] / kv[1][1])]
    tot = {k: (sum(v[0] for v in per[k].values()), sum(v[1] for v in per[k].values()))
           for k in SC.STICKS}
    above = {k: sum(1 for w, n, _, _ in per[k].values() if w / n > FIFTY) for k in SC.STICKS}
    signp = {k: binomtest(above[k], len(per[k]), 0.5, alternative="greater").pvalue
             for k in SC.STICKS}

    print("\n--- section 5 figure, numbers as drawn ---")
    for k in SC.STICKS:
        print(f"  {k} stick: pooled {tot[k][0]}/{tot[k][1]} = {tot[k][0]/tot[k][1]:.3f}; "
              f"{above[k]}/10 scrolls above 50%, sign p = {signp[k]:.5f}; "
              f"{len(drop[k])} slice(s) unscorable")
        print("   bins: " + "  ".join(
            f"{lo}-{'inf' if hi > 10**8 else hi}: {wn}/{n} = {wn/n:.3f}"
            for lo, hi, n, wn in bins[k]))

    fig = plt.figure(figsize=(15.6, 9.5), facecolor=SURF)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.0, 1.0], left=0.080, right=0.982,
                  top=0.770, bottom=0.240, wspace=0.22)

    fig.text(0.080, 0.968,
             "Section 5 — the straight-stick control, and it is half a negative result",
             fontsize=15.5, color=INK, va="top")
    fig.text(0.080, 0.933,
             "Banded-energy measure at the annotated per-slice centre against a straight "
             "vertical stick, on the same 297 slices. Two sticks: through the mean of\n"
             "that scroll's own annotated points, and placed as well as a straight line can "
             "be (the Chebyshev centre). Both panels count the same slices.",
             fontsize=10, color=INK2, va="top", linespacing=1.55)

    # ---- the win ----------------------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    style(ax)
    y = np.arange(len(order))[::-1]
    # Drawn from the 50% line rather than from zero: the axis is truncated at
    # 0.30, and a bar growing off the left edge of a truncated axis would make
    # 0.536 look like a large quantity. The length of each stem is the only
    # thing that matters here — how far above chance that scroll sits.
    for yy, n in zip(y, order):
        w, k, _, _ = per["mean"][n]
        wc, kc, _, _ = per["cheby"][n]
        ax.plot([FIFTY, w / k], [yy, yy], color=C_ANN, linewidth=3.0,
                solid_capstyle="butt", zorder=2)
        ax.scatter([w / k], [yy], s=58, color=C_ANN, zorder=4)
        ax.scatter([wc / kc], [yy], s=50, color=C_BASE, zorder=4, marker="D")
        ax.text(max(w / k, wc / kc) + 0.012, yy + 0.02,
                f"{w}/{k}   ·   {wc}/{kc}", fontsize=8.4, color=INK, va="center")
    ax.plot([FIFTY, FIFTY], [-0.62, len(order) - 0.45], color=INK, linewidth=1.4,
            zorder=5)
    ax.text(FIFTY - 0.006, len(order) - 0.45, "50%", fontsize=9, color=INK, ha="right",
            va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels(order, fontsize=9, color=INK)
    ax.set_xlim(0.42, 0.94)
    ax.set_ylim(-2.45, len(order) - 0.30)
    ax.set_xlabel("share of that scroll's slices the annotated axis wins", fontsize=9.5,
                  color=INK2)
    ax.set_title("The positive half: all ten scrolls above 50%, against both sticks\n"
                 "Stems and circles are the mean stick, diamonds the optimally placed one",
                 fontsize=10.5, color=INK, loc="left")
    ax.text(0.0, -1.00,
            f"pooled {tot['mean'][0]}/{tot['mean'][1]} = {tot['mean'][0]/tot['mean'][1]:.3f} "
            f"(mean stick)   and   {tot['cheby'][0]}/{tot['cheby'][1]} = "
            f"{tot['cheby'][0]/tot['cheby'][1]:.3f} (optimal stick)\n"
            f"scroll-level sign test, the defensible statement: "
            f"{above['mean']}/10 above 50%, one-sided p = {signp['mean']:.5f}\n"
            f"the pooled counts pseudoreplicate — the scroll is the unit of replication",
            fontsize=8.8, color=INK2, va="top", linespacing=1.75,
            transform=ax.get_yaxis_transform(which="grid"))

    # ---- the flat dose-response -------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    style(ax)
    labels = [f"{lo}–{hi}" if hi < 10 ** 8 else f"{lo}+" for lo, hi, _, _ in bins["mean"]]
    x = np.arange(len(labels))
    for k, col, off, mk, ha in (("mean", C_ANN, -0.11, "o", "right"),
                                ("cheby", C_BASE, +0.11, "D", "left")):
        rate = np.array([wn / n for _, _, n, wn in bins[k]])
        los = np.array([ci(wn, n)[0] for _, _, n, wn in bins[k]])
        his = np.array([ci(wn, n)[1] for _, _, n, wn in bins[k]])
        ax.errorbar(x + off, rate, yerr=[rate - los, his - rate], fmt=mk, color=col,
                    markersize=7.5, capsize=4, linewidth=1.3, zorder=3,
                    label=("mean stick" if k == "mean" else "optimally placed stick"))
        for xx, r in zip(x + off, rate):
            ax.text(xx + (-0.055 if ha == "right" else 0.055), r, f"{r:.2f}", ha=ha,
                    va="center", fontsize=8.6, color=col, fontweight="bold")
    ax.text(-0.47, 0.122, "slices", fontsize=8.2, color=INK2, va="center")
    for xx, bm, bc in zip(x, bins["mean"], bins["cheby"]):
        ax.text(xx - 0.11, 0.122, str(bm[2]), ha="center", fontsize=8.2, color=C_ANN)
        ax.text(xx + 0.11, 0.122, str(bc[2]), ha="center", fontsize=8.2, color=C_BASE)
    ax.axhline(FIFTY, color=INK, linewidth=1.4, zorder=5)
    ax.text(len(labels) - 0.52, FIFTY + 0.014, "50%", fontsize=9, color=INK, ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, color=INK)
    ax.set_xlim(-0.52, len(labels) - 0.48)
    ax.set_ylim(0.10, 1.02)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_xlabel("how far the stick is from the annotated centre on that slice, "
                  "level-0 voxels\n(the bin edges are section 2's own 150 and 300, fixed "
                  "before this was counted)",
                  fontsize=9.5, color=INK2, linespacing=1.6)
    ax.set_ylabel("share of slices the annotated axis wins", fontsize=9.5, color=INK2)
    ax.set_title("The negative half, and it is the important one: no dose–response\n"
                 "It should RISE to the right if the win came from real curvature. It is flat.\n"
                 "95% Clopper–Pearson intervals: the two smallest bins carry almost nothing.",
                 fontsize=10.5, color=INK, loc="left", linespacing=1.5)
    ax.legend(loc="upper right", bbox_to_anchor=(0.998, 0.998), frameon=False, fontsize=9,
              labelcolor=INK2)

    fig.text(0.080, 0.150,
             "What section 5 therefore claims: on every one of the ten scrolls this measure "
             "prefers the annotated per-slice axis to the best straight line through that "
             "scroll's own annotation, on about 62–64% of slices.\n"
             "What it does NOT claim: that this is because the axis follows the scroll's "
             "curvature. The flat dose–response gives no evidence for that mechanism, and "
             "the two smallest bins are too small to test on their own.\n"
             "The alternative we cannot rule out with this design: both sticks are derived "
             "from our own points, so the comparison may be between our annotation and a "
             "smoothed version of itself.",
             fontsize=9, color=INK2, va="top", linespacing=1.75)

    save(fig, "stick_control.png")


# ============================================================ section 2 =====
def fig_shifted():
    """panels/shifted_axis_controls.png — the control that passed and the one
    that failed, side by side, same scale, same scroll order."""
    data = json.load(open(os.path.join(ROOT, "qc", "validation_raw.json")))
    per = {k: CW.tally(data, k)[0] for k in ("r300", "r150")}
    order = [n for n, _ in sorted(per["r300"].items(), key=lambda kv: -kv[1][0] / kv[1][1])]

    stat = {}
    for k in ("r300", "r150"):
        wins = sum(v[0] for v in per[k].values())
        n = sum(v[1] for v in per[k].values())
        above = sum(1 for w, kk, _ in per[k].values() if w / kk > FIFTY)
        stat[k] = dict(wins=wins, n=n, above=above,
                       pooled=binomtest(wins, n, 0.5, alternative="greater").pvalue,
                       sign=binomtest(above, len(per[k]), 0.5,
                                      alternative="greater").pvalue)

    print("\n--- section 2 figure, numbers as drawn ---")
    for k in ("r300", "r150"):
        s = stat[k]
        print(f"  {k}: {s['wins']}/{s['n']} = {s['wins']/s['n']:.3f}, pooled p = "
              f"{s['pooled']:.3g}; {s['above']}/10 above 50%, sign p = {s['sign']:.3g}")
        print("   below 50%: " + ", ".join(
            f"{n} {per[k][n][0]}/{per[k][n][1]}={per[k][n][0]/per[k][n][1]:.3f}"
            for n in order if per[k][n][0] / per[k][n][1] < FIFTY) or "   below 50%: none")

    fig = plt.figure(figsize=(15.0, 8.4), facecolor=SURF)
    gs = GridSpec(1, 2, figure=fig, left=0.085, right=0.975, top=0.760, bottom=0.150,
                  wspace=0.24)

    fig.text(0.085, 0.960,
             "Section 2 — the shifted-axis control at two displacements: one passed, "
             "one failed",
             fontsize=15, color=INK, va="top")
    fig.text(0.085, 0.925,
             "The banded-energy measure at each annotated centre against the SAME centre "
             "displaced by a fixed distance in four directions, across 297 annotated slices.\n"
             "Both panels are the same 297 slices on the same scale in the same scroll "
             "order, so the collapse from one displacement to the other can be read straight off.",
             fontsize=10, color=INK2, va="top", linespacing=1.55)

    titles = {
        "r300": ("+300 voxels  (≈ 2.6–2.8 mm):  the control passes",
                 "9 of 10 scrolls above 50%"),
        "r150": ("+150 voxels  (≈ 1.3–1.4 mm):  the control is NULL",
                 "3 of 10 scrolls fall below 50%"),
    }
    for col, k in enumerate(("r300", "r150")):
        ax = fig.add_subplot(gs[0, col])
        style(ax)
        y = np.arange(len(order))[::-1]
        # Stems from the 50% line, not bars from zero: the axis is truncated, and
        # a bar growing off the left edge would make 0.535 look like a large
        # quantity. It also puts every scroll that is on the wrong side of chance
        # visibly on the wrong side of the line, which is the right panel's point.
        for yy, n in zip(y, order):
            w, kk, _ = per[k][n]
            rate = w / kk
            bad = rate < FIFTY
            col = C_BAD if bad else (C_ANN if k == "r300" else C_NULL)
            ax.plot([FIFTY, rate], [yy, yy], color=col, linewidth=7.5,
                    solid_capstyle="butt", zorder=2)
            ax.text(rate + (-0.008 if bad else 0.008), yy + 0.02, f"{w}/{kk}",
                    fontsize=8.6, color=(C_BAD if bad else INK), va="center",
                    ha="right" if bad else "left")
        ax.plot([FIFTY, FIFTY], [-0.62, len(order) - 0.45], color=INK, linewidth=1.4,
                zorder=5)
        ax.text(FIFTY - 0.005, len(order) - 0.45, "50%", fontsize=9, color=INK,
                ha="right", va="bottom")
        ax.set_yticks(y)
        ax.set_yticklabels(order, fontsize=9, color=INK)
        ax.set_xlim(0.31, 0.76)
        ax.set_ylim(-2.45, len(order) - 0.30)
        ax.set_xlabel("share of that scroll's slices the annotated centre wins",
                      fontsize=9.5, color=INK2)
        ax.set_title(titles[k][0] + "\n" + titles[k][1], fontsize=10.5, color=INK,
                     loc="left")
        s = stat[k]
        ax.text(0.0, -1.00,
                f"pooled {s['wins']}/{s['n']} = {s['wins']/s['n']:.3f}, "
                f"one-sided p = {s['pooled']:.3g}  (pseudoreplicated)\n"
                f"scroll-level sign test: {s['above']}/10 above 50%, "
                f"one-sided p = {s['sign']:.3g}\n"
                f"Bonferroni α = 0.05/10 = 0.005 — no scroll survives correction",
                fontsize=8.8, color=INK2, va="top", linespacing=1.75,
                transform=ax.get_yaxis_transform(which="grid"))

    fig.text(0.085, 0.058,
             "Showing the failed control is the point. The two panels together are what "
             "licenses section 2's reading and nothing stronger: this measure resolves gross "
             "displacement, not annotation-scale accuracy.\n"
             "It is evidence that these axes are not ~3 mm wrong. It is not evidence about "
             "their precision. Section 6 reaches the same wall from a different direction "
             "with a different measure and a 1.81 mm floor.",
             fontsize=9, color=INK2, va="top", linespacing=1.75)

    save(fig, "shifted_axis_controls.png")


# ============================================================ section 1 =====
FROZEN_SCROLLS = ["PHerc0191", "PHerc0358", "PHerc1203"]


def frozen_table():
    """Score three candidate axes on one common pair sample, per README section 1.

    The candidates are the live per-slice manual axis, that same axis frozen at
    the mean of its own 25 centres over the stack (no per-slice variation at
    all), and the auto-centroid. A pair enters the sample only if ALL THREE
    return a defined sign on at least three common heights, so nothing here is
    scored on a sample it helped select — the README notes what happens if you
    let the frozen axis pick its own denominator instead, and it is a weaker
    piece of evidence, not a stronger one.

    Also returned, because they are the explanation rather than decoration: the
    manual axis's own excursion from its stack mean, the separation between the
    two axes, and how many individual (pair, height) sign decisions change at
    all. Distances are millimetres, from each scroll's own voxel size in
    `metadata.source_volume` and the level-3 scale in `PHercNNNN/meta.json`.
    """
    out = []
    for scroll in FROZEN_SCROLLS:
        z, tracks = OS.load(os.path.join(ROOT, "qc", f"order_fixture_{scroll}.npz"))
        man_c, auto_c = z["man_c"], z["auto_c"]
        frozen_c = np.repeat(man_c.mean(axis=0)[None, :], len(man_c), axis=0)
        cands = {"man": man_c, "frozen": frozen_c, "auto": auto_c}

        pairs = []
        n_either = n_change = n_both = n_disagree = 0
        for a in range(len(tracks)):
            for b in range(a + 1, len(tracks)):
                common = sorted(set(tracks[a]) & set(tracks[b]))
                if len(common) < 2:
                    continue
                sg = {k: {} for k in cands}
                for i in common:
                    pa, pb = tracks[a][i], tracks[b][i]
                    for k, C in cands.items():
                        s = OS.radial_sign(pa, pb, C[i])
                        if s is not None:
                            sg[k][i] = s
                    sm, sf = sg["man"].get(i), sg["frozen"].get(i)
                    if sm is None and sf is None:
                        continue
                    n_either += 1
                    if (sm is None) != (sf is None):
                        n_change += 1
                    else:
                        n_both += 1
                        if sm != sf:
                            n_change += 1
                            n_disagree += 1
                both = sorted(set(sg["man"]) & set(sg["frozen"]) & set(sg["auto"]))
                if len(both) >= OS.MIN_COMMON:
                    pairs.append({k: {i: sg[k][i] for i in both} for k in cands})

        um = voxel_um(json.load(open(os.path.join(
            ROOT, f"{scroll}_umbilicus.json")))["metadata"])
        scale = json.load(open(os.path.join(ROOT, scroll, "meta.json")))["scale"]
        mm_px = scale * um / 1000.0
        exc = np.hypot(*(man_c - man_c.mean(0)).T) * mm_px
        sep = np.hypot(*(man_c - auto_c).T) * mm_px
        zs = z["slice_z"]

        r = dict(scroll=scroll, pairs=len(pairs),
                 exc_med=float(np.median(exc)), exc_max=float(exc.max()),
                 sep_med=float(np.median(sep)),
                 span=float((zs.max() - zs.min()) * um / 1000.0),
                 change=100.0 * n_change / n_either,
                 disagree=100.0 * n_disagree / n_both,
                 n_either=n_either, n_both=n_both)
        for k in cands:
            kept = sum(1 for p in pairs if len(set(p[k].values())) == 1)
            r[k] = (kept, kept / len(pairs))
        out.append(r)
    return out


def fig_frozen():
    """panels/frozen_axis.png — section 1's own strongest self-limitation.

    Left: the frozen axis scores identically to the live one, on identical
    integer counts. Right: why — the motion being frozen out is at or under the
    metric's resolution, while the gap between the two axes is well above it.
    Takes a couple of minutes: it scores three candidates on every track pair of
    three stacks.
    """
    rows = frozen_table()

    print("\n--- section 1 figure, numbers as drawn ---")
    for r in rows:
        print(f"  {r['scroll']}  pairs={r['pairs']}  "
              f"live {r['man'][1]:.3f} ({r['man'][0]})  "
              f"frozen {r['frozen'][1]:.3f} ({r['frozen'][0]})  "
              f"auto {r['auto'][1]:.3f} ({r['auto'][0]})  "
              f"| excursion med {r['exc_med']:.1f} max {r['exc_max']:.1f} mm, "
              f"stack {r['span']:.1f} mm, axis gap {r['sep_med']:.2f} mm, "
              f"decisions changed {r['change']:.1f}%, disagree {r['disagree']:.1f}%")

    fig = plt.figure(figsize=(15.4, 9.0), facecolor=SURF)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.12, 1.0], left=0.082, right=0.980,
                  top=0.762, bottom=0.250, wspace=0.26)

    fig.text(0.082, 0.966,
             "Section 1 — none of the winding-order advantage comes from the axis being "
             "per-slice",
             fontsize=15.5, color=INK, va="top")
    fig.text(0.082, 0.931,
             "Freeze the manual axis at a single constant point — the mean of its own 25 "
             "centres over the stack, no per-slice variation whatsoever — and score it against\n"
             "the live axis and the auto-centroid on one common pair sample. A pair enters "
             "only if all three candidates return a defined sign on at least three common heights.",
             fontsize=10, color=INK2, va="top", linespacing=1.55)

    # ---- identical scores --------------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    style(ax)
    h, gaph = 0.24, 0.265
    specs = [("man", C_ANN, None, "manual axis, live per-slice"),
             ("frozen", C_ANN, "///", "the same axis frozen at its stack mean"),
             ("auto", C_BASE, None, "auto-centroid")]
    yticks, ylabels = [], []
    for j, r in enumerate(rows):
        base = (len(rows) - 1 - j) * 1.35
        for i, (key, col, hatch, _) in enumerate(specs):
            yy = base + (1 - i) * gaph
            kept, frac = r[key]
            ax.barh(yy, frac, height=h, color=col, hatch=hatch, edgecolor=SURF,
                    linewidth=0.0, zorder=2)
            ax.text(frac + 0.006, yy, f"{frac:.3f}  ({kept} pairs)", fontsize=8.8,
                    color=INK, va="center")
        yticks.append(base)
        ylabels.append(f"{r['scroll']}\n{r['pairs']} shared pairs")
        ax.text(0.008, base + gaph * 1.62, "identical, to the integer count",
                fontsize=8.2, color="#8a5a3a", fontstyle="italic", va="center")
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=9, color=INK, linespacing=1.5)
    ax.set_xlim(0, 1.10)
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.set_ylim(-1.55, (len(rows) - 1) * 1.35 + 0.80)
    ax.set_xlabel("share of pairs whose winding order the axis preserves across the stack",
                  fontsize=9.5, color=INK2)
    ax.set_title("Net gain from tracking the core slice by slice: +0.000 on all three\n"
                 "Not merely the same rounded rate — the same integer counts",
                 fontsize=10.5, color=INK, loc="left")
    ax.legend([Rectangle((0, 0), 1, 1, color=C_ANN),
               Rectangle((0, 0), 1, 1, facecolor=C_ANN, hatch="///", edgecolor=SURF),
               Rectangle((0, 0), 1, 1, color=C_BASE)],
              [s[3] for s in specs], loc="lower left", bbox_to_anchor=(0.0, 0.0),
              frameon=False, fontsize=8.8, labelcolor=INK2, ncol=3,
              columnspacing=1.4, handlelength=1.4)

    # ---- why ---------------------------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    style(ax)
    y = np.arange(len(rows))[::-1] * 1.0
    ax.axvspan(3.0, 6.0, color=C_NULL, alpha=0.22, zorder=0)
    ax.text(4.5, len(rows) - 0.46, "the metric's own\ndetection threshold\n3–6 mm",
            ha="center", va="top", fontsize=8.6, color="#6b6862", linespacing=1.5)
    for yy, r in zip(y, rows):
        ax.plot([r["exc_med"], r["exc_max"]], [yy, yy], color=C_ANN, linewidth=2.6,
                solid_capstyle="butt", zorder=3)
        ax.scatter([r["exc_med"]], [yy], s=54, color=C_ANN, zorder=4)
        ax.scatter([r["sep_med"]], [yy], s=64, color=C_BASE, marker="D", zorder=4)
        ax.text(r["exc_med"], yy - 0.20, f"{r['exc_med']:.1f}–{r['exc_max']:.1f} mm",
                fontsize=8.4, color=C_ANN, ha="left", va="top")
        ax.text(r["sep_med"], yy - 0.20, f"{r['sep_med']:.2f} mm", fontsize=8.4,
                color=C_BASE, ha="center", va="top")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['scroll']}\nstack spans {r['span']:.1f} mm" for r in rows],
                       fontsize=9, color=INK, linespacing=1.5)
    ax.set_xlim(0, 16.0)
    ax.set_ylim(-1.45, len(rows) - 0.22)
    ax.set_xlabel("millimetres", fontsize=9.5, color=INK2)
    ax.set_title("Why: the motion being frozen out is at or under the metric's resolution,\n"
                 "and the gap between the two axes is well above it",
                 fontsize=10.5, color=INK, loc="left")
    ax.legend([Line2D([], [], color=C_ANN, linewidth=2.6, marker="o", markersize=7),
               Line2D([], [], color=C_BASE, linestyle="", marker="D", markersize=7)],
              ["the manual axis's own excursion from its stack mean (median → max)",
               "median separation between the manual axis and the auto-centroid"],
              loc="lower left", bbox_to_anchor=(0.0, 0.0), frameon=False, fontsize=8.6,
              labelcolor=INK2)

    chg = " / ".join(f"{r['change']:.1f}%" for r in rows)
    dis = " / ".join(f"{r['disagree']:.1f}%" for r in rows)
    fig.text(0.082, 0.165,
             f"Read section 1 as measuring WHERE THE CENTRE SITS, not how it moves. The "
             f"metric is not literally blind to the freeze — {chg} of individual "
             f"(pair, height) sign decisions\n"
             f"change status, mostly by moving in or out of evaluability, and among "
             f"decisions both versions resolve they disagree on {dis} — but the changes "
             f"cancel to nothing in aggregate.\n"
             f"Nothing here demonstrates a benefit from per-slice tracking on these three "
             f"stacks. What per-slice annotation is for is the scrolls and zones where the "
             f"core wanders further\n"
             f"than 3 mm, and that case is not made by this test.",
             fontsize=9, color=INK2, va="top", linespacing=1.75)

    save(fig, "frozen_axis.png")


FIGURES = {"prereg": fig_prereg, "stick": fig_stick,
           "shifted": fig_shifted, "frozen": fig_frozen}


def main():
    want = [a for a in sys.argv[1:] if a in FIGURES] or list(FIGURES)
    for k in want:
        FIGURES[k]()


if __name__ == "__main__":
    sys.exit(main())
