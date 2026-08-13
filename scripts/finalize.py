#!/usr/bin/env python3
"""FINALIZER for the umbilicus submission.

Lesson from the calibration against sean (Aug 9): the kink of our axes comes
almost entirely from the points that were left at the RAW auto-guess (the
center of mass of a crumpled pancake jumps around). Alex's manual points are
as smooth as the reference. So when the submission file is assembled, untouched
auto points are DROPPED: the polyline runs through the manual ones
(interpolation between them is linear, as in khartes). sean's format does not
require even spacing.

Recognizing an "untouched" point: it matches the scroll's auto_centers.json to
within 2 vox.

Usage: finalize.py [--indir results] [--outdir submission]
Writes: submission/PHercNNNN_umbilicus.json + a summary for each scroll.
"""
import argparse, glob, json, os
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    base = os.environ.get('UMBILICI_ROOT',
                          os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--indir", default=os.path.join(base, "results"))
    ap.add_argument("--outdir", default=os.path.join(base, "submission"))
    ap.add_argument("--tol", type=float, default=2.0)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    # ignore list: slices Alex told us to drop (for example "19056 ignore")
    ign_path = os.path.join(a.indir, "игнор.json")
    ignore = {}
    if os.path.exists(ign_path):
        ignore = {k: set(v) for k, v in json.load(open(ign_path)).items()}
    for fp in sorted(glob.glob(os.path.join(a.indir, "PHerc*_umbilicus.json"))):
        name = os.path.basename(fp).split("_")[0]
        d = json.load(open(fp))
        pts = d["control_points"]
        acp = os.path.join(base, name, "auto_centers.json")
        auto = []
        if os.path.exists(acp):
            auto = json.load(open(acp))
        amap = {}
        for q in auto:
            amap[int(round(q["z"]))] = (q["x"], q["y"])
        keep, dropped = [], []
        ign = ignore.get(name, set())
        for p in pts:
            z = int(round(p["z"]))
            if z in ign:
                dropped.append(z); continue
            au = amap.get(z)
            if au is not None and np.hypot(p["x"]-au[0], p["y"]-au[1]) < a.tol:
                dropped.append(z)
            else:
                keep.append({"x": float(p["x"]), "y": float(p["y"]), "z": float(p["z"])})
        keep.sort(key=lambda q: q["z"])
        # kink before/after (at the native step; only fair within a single scroll)
        def kink(ps):
            if len(ps) < 3: return 0.0
            xs = np.array([q["x"] for q in ps]); ys = np.array([q["y"] for q in ps])
            zs = np.array([q["z"] for q in ps])
            dev = []
            for i in range(1, len(ps)-1):
                xi = np.interp(zs[i], [zs[i-1], zs[i+1]], [xs[i-1], xs[i+1]])
                yi = np.interp(zs[i], [zs[i-1], zs[i+1]], [ys[i-1], ys[i+1]])
                dev.append(np.hypot(xs[i]-xi, ys[i]-yi))
            return float(np.median(dev))
        out = os.path.join(a.outdir, f"{name}_umbilicus.json")
        # schema as in sean's files: integer coordinates, per-point score (100 =
        # manual), a metadata block with his fields; our extra fields
        # (source_volume, annotator_note) do not bother a strict reader of his schema
        import time
        vol = ""
        mp = os.path.join(base, name, "meta.json")
        if os.path.exists(mp):
            try:
                vol = json.load(open(mp)).get("volume", "")
            except Exception:
                pass
        keep_i = [{"x": int(round(q["x"])), "y": int(round(q["y"])),
                   "z": int(round(q["z"])), "score": 100} for q in keep]
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = {
            "control_points": keep_i,
            "metadata": {
                "z_grid_spacing": 0,
                "min_score_threshold": 0.75,
                "high_score_threshold": 0.75,
                "total_points": len(keep_i),
                "timestamp": now, "created": now, "modified": now,
                "source_volume": vol,
                "annotator_note": "manual points only; untouched auto-suggestions dropped at finalization",
            },
        }
        json.dump(payload, open(out, "w"), indent=1)
        print(f"{name}: {len(pts)} -> {len(keep)} points (auto dropped: {len(dropped)}"
              f"{' at z ' + ','.join(map(str, dropped)) if dropped else ''}); "
              f"median kink {kink(pts):.0f} -> {kink(keep):.0f} vox")

if __name__ == "__main__":
    main()
