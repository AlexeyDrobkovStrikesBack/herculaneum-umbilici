#!/usr/bin/env python3
"""Midpoint density audit for the umbilicus polylines.

Answers the question Paul (pmh47) raised on 2026-08-16: 30 hand-marked slices
per axis is fine in the straight parts, but in sharply curved parts the
umbilicus xy moves rapidly with z, so linear interpolation between control
points may sit in the wrong place. He asked us to look at slices halfway
between control points and add a point where the interpolation misses.

This script measures the curvature that is already visible in the annotation
itself, with no CT access and no model, so it can rank which intervals are
worth re-inspecting before anyone opens a viewer.

Two measures, both in micrometres:

  loo_miss  Leave-one-out miss. Drop an interior control point j, interpolate
            linearly between its neighbours at z_j, and measure the distance to
            where the annotator actually put it. This is a direct, empirical
            statement about how wrong linear interpolation is over a span of
            two intervals — no spline model is assumed anywhere.

  mid_est   Estimated miss at the midpoint of a single interval. For a locally
            circular arc the sagitta scales with the square of the span, so the
            miss over one interval is about a quarter of the leave-one-out miss
            measured over the two intervals that share that node. Reported per
            interval as the mean of the estimates from its two endpoints (the
            outermost intervals inherit their single interior neighbour).

mid_est is an estimate and is labelled as one. loo_miss is a measurement.

Reference scales for reading the numbers:
  - sean puts the wiggle room in the centre position itself at 20-30 voxels,
    i.e. 190-280 um at 9.362 um. Below that, precision is not meaningful.
  - our own pre-registered axis-benefit test is blind below 1.81 mm.

Usage:  python3 scripts/midpoint_audit.py [--csv out.csv]
Run from the repository root.
"""

import argparse
import csv
import glob
import json
import math
import os
import re
import sys

# Voxel size is not stored as a number in the annotation metadata; it is in the
# source volume name, e.g. "...-9.362um-1.2m-113keV-masked.zarr".
VOXEL_RE = re.compile(r"-(\d+\.\d+)um-")


def voxel_size_um(meta):
    src = meta.get("source_volume", "")
    m = VOXEL_RE.search(src)
    if not m:
        raise ValueError("no voxel size in source_volume: %r" % src)
    return float(m.group(1))


def load_axis(path):
    with open(path) as fh:
        doc = json.load(fh)
    pts = sorted(doc["control_points"], key=lambda p: p["z"])
    vox = voxel_size_um(doc["metadata"])
    return pts, vox


def loo_miss_um(pts, vox):
    """Distance from each interior point to the chord of its two neighbours."""
    out = [None] * len(pts)
    for j in range(1, len(pts) - 1):
        a, b, c = pts[j - 1], pts[j], pts[j + 1]
        span = c["z"] - a["z"]
        if span == 0:
            continue
        t = (b["z"] - a["z"]) / span
        px = a["x"] + t * (c["x"] - a["x"])
        py = a["y"] + t * (c["y"] - a["y"])
        d = math.hypot(b["x"] - px, b["y"] - py)
        out[j] = d * vox
    return out


def audit(path):
    pts, vox = load_axis(path)
    loo = loo_miss_um(pts, vox)
    scroll = os.path.basename(path).split("_")[0]

    rows = []
    for i in range(len(pts) - 1):
        # midpoint estimate for interval i -> i+1, from whichever endpoints are
        # interior points and therefore carry a leave-one-out measurement
        ests = [loo[k] / 4.0 for k in (i, i + 1) if 0 <= k < len(loo) and loo[k] is not None]
        mid_est = sum(ests) / len(ests) if ests else float("nan")
        a, b = pts[i], pts[i + 1]
        rows.append({
            "scroll": scroll,
            "voxel_um": vox,
            "interval": i,
            "z_lo": a["z"],
            "z_hi": b["z"],
            "z_mid": (a["z"] + b["z"]) // 2,
            "dz_vox": b["z"] - a["z"],
            "xy_step_um": math.hypot(b["x"] - a["x"], b["y"] - a["y"]) * vox,
            "mid_est_um": mid_est,
        })
    node_rows = [{
        "scroll": scroll,
        "voxel_um": vox,
        "node": j,
        "z": pts[j]["z"],
        "loo_miss_um": loo[j],
    } for j in range(len(pts)) if loo[j] is not None]
    return rows, node_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="write the per-interval table here")
    ap.add_argument("--top", type=int, default=15, help="how many worst intervals to print")
    ap.add_argument("--threshold", type=float, default=280.0,
                    help="um; intervals whose estimated midpoint miss exceeds this "
                         "are listed as candidates (default 280 = sean's upper "
                         "wiggle-room figure at 9.362 um)")
    args = ap.parse_args()

    paths = sorted(glob.glob("PHerc*_umbilicus.json"))
    if not paths:
        sys.exit("run from the repository root: no PHerc*_umbilicus.json here")

    all_iv, all_nodes = [], []
    print("%-10s %5s %6s  %-28s %-28s" % ("scroll", "pts", "vox", "leave-one-out miss (um)", "estimated midpoint miss (um)"))
    print("%-10s %5s %6s  %-28s %-28s" % ("", "", "", "median   p90     max", "median   p90     max"))
    for p in paths:
        iv, nodes = audit(p)
        all_iv.extend(iv)
        all_nodes.extend(nodes)
        loo = sorted(n["loo_miss_um"] for n in nodes)
        mid = sorted(r["mid_est_um"] for r in iv if not math.isnan(r["mid_est_um"]))

        def q(v, f):
            if not v:
                return float("nan")
            return v[min(len(v) - 1, int(round(f * (len(v) - 1))))]

        print("%-10s %5d %6.3f  %7.0f %7.0f %7.0f      %7.0f %7.0f %7.0f" % (
            iv[0]["scroll"], len(nodes) + 2, iv[0]["voxel_um"],
            q(loo, 0.5), q(loo, 0.9), loo[-1] if loo else float("nan"),
            q(mid, 0.5), q(mid, 0.9), mid[-1] if mid else float("nan")))

    over = [r for r in all_iv if r["mid_est_um"] > args.threshold]
    print("\n%d of %d intervals estimate a midpoint miss above %.0f um" % (
        len(over), len(all_iv), args.threshold))
    print("\nworst %d intervals (these are the slices to open first):" % args.top)
    print("%-10s %6s %8s %8s %8s %10s" % ("scroll", "iv", "z_lo", "z_mid", "z_hi", "est_um"))
    for r in sorted(all_iv, key=lambda r: -r["mid_est_um"])[:args.top]:
        print("%-10s %6d %8d %8d %8d %10.0f" % (
            r["scroll"], r["interval"], r["z_lo"], r["z_mid"], r["z_hi"], r["mid_est_um"]))

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(all_iv[0].keys()))
            w.writeheader()
            w.writerows(all_iv)
        print("\nwrote %s (%d intervals)" % (args.csv, len(all_iv)))


if __name__ == "__main__":
    main()
