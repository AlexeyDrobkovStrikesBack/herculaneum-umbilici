#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibration of the quality gates against sean's reference annotation.

Runs THE SAME gates (imported from qc_gates, the logic is not duplicated) on
sean's annotation and on ours, collects the results into one table and writes
a summary json with every per-row verdict — the montages and the report are
built from it afterwards.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qc_gates import best_center      # noqa: E402

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETS = [
    ("sean", "PHerc0125", "ref_sean/PHerc0125_umbilicus.json", "ref_sean/PHerc0125"),
    ("sean", "PHerc0211", "ref_sean/PHerc0211_umbilicus.json", "ref_sean/PHerc0211"),
    ("sean", "PHerc0826", "ref_sean/PHerc0826_umbilicus.json", "ref_sean/PHerc0826"),
    ("ours", "PHerc0191", "results/PHerc0191_umbilicus.json", "PHerc0191"),
    ("ours", "PHerc0257", "results/PHerc0257_umbilicus.json", "PHerc0257"),
    ("ours", "PHerc0268", "results/PHerc0268_umbilicus.json", "PHerc0268"),
]

OK, WARN, S = 130.0, 250.0, 8.0


def run(jpath, sdir):
    pts = json.load(open(os.path.join(ROOT, jpath)))["control_points"]
    rows = []
    for p in pts:
        z = int(round(p["z"]))
        fp = os.path.join(ROOT, sdir, f"z{z}.png")
        if not os.path.exists(fp):
            continue                                  # slice was not downloaded — point is outside the sample
        img = np.asarray(Image.open(fp).convert("L")).astype(np.float32)
        ax, ay = p["x"] / S, p["y"] / S
        (sb, bx, by), applicable, relief = best_center(img, ax, ay)
        del img
        sh = float(np.hypot(bx - ax, by - ay) * S)
        if not applicable:
            v = "n/a"
        elif sh < OK:
            v = "OK"
        elif sh < WARN:
            v = "fair"
        else:
            v = "candidate"
        rows.append({"z": z, "x": p["x"], "y": p["y"], "shift": sh, "relief": relief,
                     "score": sb, "applicable": bool(applicable), "verdict": v,
                     "cand_x": int(bx * S), "cand_y": int(by * S)})
    return rows


def kink(rows, key):
    """Median deviation of a point from the straight line between its z-neighbours —
    the "kink" of the polyline.
    Computed for the author's annotation (key='pt') and for the set in which every
    point is replaced by the detector's candidate (key='cand'). The comparison is
    fair: the same z values, the same neighbours. The winding axis is physically
    smooth, so the set with the smaller kink is closer to the truth — this is a
    check independent of the rings.
    """
    r = sorted(rows, key=lambda q: q["z"])
    xs = np.array([q["x"] if key == "pt" else q["cand_x"] for q in r], float)
    ys = np.array([q["y"] if key == "pt" else q["cand_y"] for q in r], float)
    zs = np.array([q["z"] for q in r], float)
    d = []
    for i in range(1, len(r) - 1):
        w = (zs[i] - zs[i - 1]) / (zs[i + 1] - zs[i - 1])
        px = xs[i - 1] + w * (xs[i + 1] - xs[i - 1])
        py = ys[i - 1] + w * (ys[i + 1] - ys[i - 1])
        d.append(np.hypot(xs[i] - px, ys[i] - py))
    return float(np.median(d)) if d else float("nan")


def main():
    out = {}
    print(f"{'author':6} {'scroll':10} {'n':>3} {'OK':>3} {'fair':>4} {'cand':>4} "
          f"{'n/a':>6} | {'med.shift':>9} {'med.relief':>10} | "
          f"{'author kink':>12} {'cand. kink':>11}")
    agg = {}
    for who, name, jp, sd in SETS:
        rows = run(jp, sd)
        if not rows:
            print(f"{who:6} {name:10} — no slices")
            continue
        n = len(rows)
        c = {k: sum(1 for r in rows if r["verdict"] == k)
             for k in ("OK", "fair", "candidate", "n/a")}
        sh = np.array([r["shift"] for r in rows])
        sha = np.array([r["shift"] for r in rows if r["applicable"]])
        rel = np.array([r["relief"] for r in rows])
        st = {"who": who, "scroll": name, "n": n, **c,
              "med_shift": float(np.median(sh)),
              "med_shift_applicable": float(np.median(sha)) if len(sha) else None,
              "med_relief": float(np.median(rel)),
              "frac_ok": (c["OK"] + c["fair"]) / n,
              "frac_cand": c["candidate"] / n,
              "frac_na": c["n/a"] / n,
              "kink_author": kink(rows, "pt"),
              "kink_cand": kink(rows, "cand")}
        out[name] = {"stats": st, "rows": rows}
        agg.setdefault(who, []).extend(rows)
        print(f"{who:6} {name:10} {n:3d} {c['OK']:3d} {c['fair']:4d} {c['candidate']:4d} "
              f"{c['n/a']:6d} | {st['med_shift']:9.0f} {st['med_relief']:10.2f} | "
              f"{st['kink_author']:12.0f} {st['kink_cand']:11.0f}")

    print()
    for who, rows in agg.items():
        n = len(rows)
        c = {k: sum(1 for r in rows if r["verdict"] == k)
             for k in ("OK", "fair", "candidate", "n/a")}
        sh = np.median([r["shift"] for r in rows])
        out[f"TOTAL_{who}"] = {"stats": {"who": who, "scroll": f"TOTAL ({who})", "n": n,
                                         **c, "med_shift": float(sh),
                                         "frac_ok": (c["OK"] + c["fair"]) / n,
                                         "frac_cand": c["candidate"] / n,
                                         "frac_na": c["n/a"] / n}}
        print(f"TOTAL {who:10}: {n} points | OK/fair {(c['OK']+c['fair'])/n*100:.0f}% | "
              f"candidate better {c['candidate']/n*100:.0f}% | "
              f"not applicable {c['n/a']/n*100:.0f}% | median shift {sh:.0f} vox")

    with open(os.path.join(ROOT, "qc", "калибровка_sean.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
