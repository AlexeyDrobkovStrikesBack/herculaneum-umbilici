#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibration of the quality gates against sean's reference annotation.

Runs THE SAME gates (imported from qc_gates, the logic is not duplicated) on
sean's annotation and on ours, collects the results into one table and writes
a summary json with every per-row verdict — the montages and the report are
built from it afterwards.

CHANGED FOR THIS RELEASE, and this is the one script that is not shipped exactly
as it was first run. Two things were wrong with the original and both inflated
its authority:
  * it covered only three of our ten scrolls (PHerc0191/0257/0268), and
  * it read them from `results/`, the pre-finalization annotator output, which
    still contained the untouched auto-suggestions that finalization drops.
So the published "ours" figure described a polyline that the package does not
ship. It now runs all ten scrolls against the SHIPPED json files. The old
three-scroll, pre-finalization number and the new one are both stated in the
README so the change is visible rather than silent.

Paths: the axis json files are read from UMBILICI_ROOT (this repository); the
per-slice PNGs and `ref_sean/` are read from UMBILICI_TREE, which defaults to
the same place. Point UMBILICI_TREE at the annotation tree to run it.
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
TREE = os.environ.get('UMBILICI_TREE', ROOT)

SETS = (
    [("sean", n, f"ref_sean/{n}_umbilicus.json", f"ref_sean/{n}")
     for n in ("PHerc0125", "PHerc0211", "PHerc0826")]
    + [("ours", n, f"{n}_umbilicus.json", n)
       for n in ("PHerc0191", "PHerc0257", "PHerc0268", "PHerc0358", "PHerc0800",
                 "PHerc0813", "PHerc1203", "PHerc1218", "PHerc1447", "PHerc1545")]
)

OK, WARN, S = 130.0, 250.0, 8.0


def run(jpath, sdir):
    # ours ship in this repository; sean's reference lives in the annotation tree
    jbase = TREE if jpath.startswith("ref_sean/") else ROOT
    pts = json.load(open(os.path.join(jbase, jpath)))["control_points"]
    rows = []
    for p in pts:
        z = int(round(p["z"]))
        fp = os.path.join(TREE, sdir, f"z{z}.png")
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

    outdir = os.path.join(ROOT, "qc")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "calibration_sean.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"\nwrote {os.path.join(outdir, 'calibration_sean.json')}")


if __name__ == "__main__":
    main()
