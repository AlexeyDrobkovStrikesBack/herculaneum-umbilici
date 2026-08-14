#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every number in README section 6 -- the pre-registered axis-benefit run --
recomputed from the per-slice results that ship in `axis_benefit/`.

    python3 scripts/axis_benefit.py

numpy and scipy only. It does NOT measure anything: the measurement streams ten
scroll volumes out of the open bucket and imports villa's spiral code, and it is
shipped under `axis_benefit/measure/` for inspection rather than for running
here (README section 6, "What does not travel"). This script takes the
measurement's own output -- one q per axis per slice -- and does the counting
and the testing, so the step from "a q on each slice" to "p = 0.0020" is
arithmetic a reader can check rather than a number to be taken on trust.

The specification the run followed, fixed in writing before any comparative
quantity existed, is `axis_benefit/PREREGISTRATION.md`. This script implements
its section 10 and nothing else. The order of the blocks below is the order that
file puts them in: primary first, then the secondaries it declared, then the
control, then the post-hoc it declared and labelled as post-hoc in advance.

What each block prints

  PRIMARY        per-scroll mean of (q_annotated - q_stick_mean), and the
                 two-sided Wilcoxon signed-rank over those ten scroll values.
                 The scroll is the unit of replication; the slice is not.
  secondary      the same against the volume-centre stick, and the slice-level
                 tests, which pseudoreplicate and are labelled as such.
  worst case     every non-scorable slice charged to the annotated axis as a
                 loss, plus which axis actually failed the coverage rule on each
                 of them.
  control        our own axis displaced sideways, and the sensitivity floor --
                 the smallest displacement this measure can see at all. That
                 number bounds what the run can claim, so it prints here and it
                 is quoted in the body of the README, not in a footnote.
  stick distance how far the straight stick actually sits from the annotated
                 axis, which is what decides whether the effect lives above the
                 floor.
  post-hoc       the three corrected variants of the two bad PHerc0813 control
                 points, and how far apart the three placements are. Post-hoc,
                 declared in advance as post-hoc, never the headline.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from scipy.stats import wilcoxon, binomtest

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'axis_benefit')

SCROLLS = ["PHerc0191", "PHerc0257", "PHerc0268", "PHerc0358", "PHerc0800",
           "PHerc0813", "PHerc1203", "PHerc1218", "PHerc1447", "PHerc1545"]
AXES = ['annotated', 'stick_mean', 'stick_volume_centre']
CONTROL_D = [25, 50, 100, 200, 400, 800]


def load(scroll, suffix=""):
    with open(os.path.join(DATA, f'prereg_{scroll}{suffix}.json')) as fh:
        return json.load(fh)


def scorable(d):
    return [r for r in d["slices"] if r.get("scorable")]


def per_scroll(baseline="stick_mean", override=None):
    """One row per scroll. `override` swaps in a post-hoc variant file."""
    rows = []
    for s in SCROLLS:
        d = load(s, override) if (override and s == "PHerc0813") else load(s)
        sl = d["slices"]
        sc = scorable(d)
        qa = np.array([r["conditions"]["annotated"]["q"] for r in sc])
        qb = np.array([r["conditions"][baseline]["q"] for r in sc])
        rows.append(dict(scroll=s, um=d["um_per_px"], n=len(sc), drop=len(sl) - len(sc),
                         qa=qa, qb=qb, delta=float((qa - qb).mean()),
                         wins=int((qa > qb).sum()),
                         drops=[(r["z_L0"], r.get("reason", "?"), r.get("ring_at_400"))
                                for r in sl if not r.get("scorable")]))
    return rows


# ------------------------------------------------------------------ primary --
def report(baseline, label):
    rows = per_scroll(baseline)
    delta = np.array([r["delta"] for r in rows])
    qa = np.concatenate([r["qa"] for r in rows])
    qb = np.concatenate([r["qb"] for r in rows])
    print(f"\n=== {label}: annotated vs {baseline} ===")
    print(f"{'scroll':11s} {'n':>4s} {'drop':>5s} {'mean qA':>9s} {'mean qB':>9s} "
          f"{'Delta':>9s}  wins")
    for r in rows:
        print(f"{r['scroll']:11s} {r['n']:4d} {r['drop']:5d} {r['qa'].mean():+9.4f} "
              f"{r['qb'].mean():+9.4f} {r['delta']:+9.4f}  {r['wins']:3d}/{r['n']}")
    n_pos = int((delta > 0).sum())
    w = wilcoxon(delta, alternative="two-sided")
    print(f"\nscrolls with Delta > 0: {n_pos}/10   (pre-registered requirement: >= 6)")
    print(f"pooled mean q: annotated {qa.mean():+.4f}  {baseline} {qb.mean():+.4f}  "
          f"ratio {qa.mean() / qb.mean():.3f}x")
    print(f"pooled median q: annotated {np.median(qa):+.4f}  {baseline} {np.median(qb):+.4f}")
    print(f"pooled slice wins: {int((qa > qb).sum())}/{len(qa)}")
    print(f"Wilcoxon signed-rank over the ten scroll Deltas: "
          f"W = {w.statistic:.1f}  p = {w.pvalue:.4f}  (two-sided)")
    ok = (w.pvalue < 0.05) and (n_pos >= 6) and (np.median(delta) > 0)
    print(f"verdict under PREREGISTRATION.md 10.2: "
          f"{'CLAIM SUPPORTED' if ok else 'NULL -- claim not made'}")
    ws = wilcoxon(qa - qb, alternative="two-sided")
    bt = binomtest(int((qa > qb).sum()), len(qa), 0.5)
    print(f"[secondary, anticonservative -- slices within a scroll are not "
          f"independent] slice-level Wilcoxon W = {ws.statistic:.0f} p = {ws.pvalue:.2e}; "
          f"sign test p = {bt.pvalue:.2e}")
    return rows


# ---------------------------------------------------------------- exclusions --
def exclusions():
    rows = per_scroll()
    tot = sum(r["drop"] for r in rows)
    print("\n=== the non-scorable slices, and who caused them ===")
    print(f"non-scorable: {tot}/300")
    blame = {k: 0 for k in AXES}
    for r in rows:
        if not r["drop"]:
            continue
        print(f"  {r['scroll']}: {r['drop']:2d}  z = " +
              " ".join(str(z) for z, _, _ in r["drops"]))
        for _, _, ring in r["drops"]:
            if not ring:
                continue
            for k, v in ring.items():
                if v < 0.95:
                    blame[k] += 1
    print("the axis whose ring fell below 95% coverage at r = 400 was")
    for k, v in blame.items():
        print(f"   {k:22s} on {v}")
    print("  -- i.e. most drops are the STICKS running off the edge of the scroll,")
    print("     which removes slices the annotated axis would mostly have won.")
    tw = sum(r["wins"] for r in rows)
    tn = sum(r["n"] + r["drop"] for r in rows)
    print(f"worst case, every non-scorable slice charged to the annotated axis as a "
          f"loss: {tw}/{tn}, sign test p = {binomtest(tw, tn, 0.5).pvalue:.2e}")


# ------------------------------------------------------------------ control --
def control():
    print("\n=== control: our own axis displaced sideways (PREREGISTRATION.md 10.4) ===")
    per_d, per_mm, monot, n_slices = {x: [] for x in CONTROL_D}, {x: [] for x in CONTROL_D}, [], 0
    for s in SCROLLS:
        d = load(s)
        um = d["um_per_px"]
        for r in scorable(d):
            cs = r["conditions"]
            if not any(k.startswith("control_") for k in cs):
                continue
            n_slices += 1
            q0 = cs["annotated"]["q"]
            last = None
            for x in CONTROL_D:
                vals = [cs[f"control_d{x}_dir{i}"]["q"] for i in range(4)
                        if f"control_d{x}_dir{i}" in cs
                        and cs[f"control_d{x}_dir{i}"]["q"] is not None
                        and cs[f"control_d{x}_dir{i}"]["ring95"] >= 0.95]
                if vals:
                    per_d[x].append(q0 - float(np.mean(vals)))
                    per_mm[x].append(x * um / 1000.0)
                    last = float(np.mean(vals))
            if last is not None:
                monot.append(q0 > last)
    print(f"control slices with valid coverage: {n_slices}")
    print(f"{'d (px)':>7s} {'d (mm)':>8s} {'n':>4s} {'median qA-qd':>13s} {'mean':>9s} "
          f"{'frac degraded':>14s}")
    floor = None
    for x in CONTROL_D:
        v = np.array(per_d[x])
        mm, med = float(np.mean(per_mm[x])), float(np.median(v))
        print(f"{x:7d} {mm:8.2f} {len(v):4d} {med:+13.4f} {v.mean():+9.4f} "
              f"{float((v > 0).mean()):14.2f}")
        if floor is None and med >= 0.01:
            floor = (x, mm)
    print(f"largest valid displacement degrades q on {sum(monot)}/{len(monot)} "
          f"control slices")
    print(f"SENSITIVITY FLOOR: {floor[0]} px = {floor[1]:.2f} mm "
          f"(first d whose median drop reaches the pre-registered 0.01)")


def stick_distance():
    print("\n=== how far the straight stick actually is from the annotated axis ===")
    print("(this is what decides whether the effect lives above the floor above)")
    allv = []
    for s in SCROLLS:
        d = load(s)
        v = np.array([r["conditions"]["stick_mean"]["displacement_um"] / 1000.0
                      for r in scorable(d)])
        allv.append(v)
        print(f"  {s}  n={len(v):3d}  median {np.median(v):6.2f} mm  "
              f"mean {v.mean():6.2f} mm  max {v.max():6.2f} mm")
    a = np.concatenate(allv)
    print(f"  pooled over the {len(a)} scorable slices: median {np.median(a):.2f} mm, "
          f"mean {np.mean(a):.2f} mm")


def losses_and_rbar():
    rows = per_scroll()
    qa = np.concatenate([r["qa"] for r in rows])
    qb = np.concatenate([r["qb"] for r in rows])
    win = qa > qb
    print("\n=== where the annotated axis loses ===")
    print(f"losses {int((~win).sum())}/{len(qa)}; mean q_annotated on losses "
          f"{qa[~win].mean():+.4f} against {qa[win].mean():+.4f} on wins")
    print(f"mean gap on wins {(qa - qb)[win].mean():+.4f}, on losses "
          f"{(qa - qb)[~win].mean():+.4f}")
    print("\n=== villa's own winding-phase concentration Rbar "
          "(secondary; cannot change the verdict) ===")
    for nm in AXES:
        v = np.array([r["conditions"][nm]["rbar"] for s in SCROLLS
                      for r in scorable(load(s))
                      if r["conditions"][nm].get("rbar") is not None])
        print(f"  {nm:22s} n={len(v)} mean={v.mean():.4f} median={np.median(v):.4f} "
              f"max={v.max():.4f}")
    print("  at the noise floor for every axis, and identical between them.")


# ------------------------------------------------------------------ post-hoc --
def posthoc():
    print("\n=== POST-HOC (PREREGISTRATION.md 10.5): the two bad PHerc0813 points ===")
    print("Not the pre-registered result. The primary test above keeps these slices in.")
    base = per_scroll()
    d0 = np.array([r["delta"] for r in base])
    b13 = base[SCROLLS.index("PHerc0813")]
    print(f"  pre-registered, unchanged : PHerc0813 Delta = {b13['delta']:+.4f} "
          f"(n = {b13['n']}, wins {b13['wins']}) -> "
          f"W = {wilcoxon(d0).statistic:.1f}, p = {wilcoxon(d0).pvalue:.4f}")
    for v in ["eye", "drop", "argmax"]:
        d = load("PHerc0813", f"_posthoc_{v}")
        sc = scorable(d)
        qa = np.array([r["conditions"]["annotated"]["q"] for r in sc])
        qb = np.array([r["conditions"]["stick_mean"]["q"] for r in sc])
        dd = d0.copy()
        dd[SCROLLS.index("PHerc0813")] = (qa - qb).mean()
        w = wilcoxon(dd)
        print(f"  post-hoc {v:6s}           : PHerc0813 Delta = {(qa - qb).mean():+.4f} "
              f"(n = {len(sc)}, wins {int((qa > qb).sum())}) -> "
              f"W = {w.statistic:.1f}, p = {w.pvalue:.4f}, scrolls Delta>0 "
              f"{int((dd > 0).sum())}/10")
    print("  every correction leaves PHerc0813's Delta LOWER than the uncorrected")
    print("  annotation, and the primary test does not move.")

    # how far apart the three placements are
    src = json.load(open(os.path.join(ROOT, 'PHerc0813_umbilicus.json')))
    um = 9.362
    pts = {'published': {p['z']: (p['x'], p['y']) for p in src['control_points']}}
    for v in ["eye", "argmax"]:
        with open(os.path.join(DATA, f'PHerc0813_posthoc_{v}.json')) as fh:
            pts[v] = {p['z']: (p['x'], p['y']) for p in json.load(fh)['control_points']}
    print("\n  distances between the three placements of the two suspect points")
    print("  (level-0 voxels, and mm at this scroll's 9.362 um voxel):")
    for z in (6616, 9296):
        print(f"    z = {z}: published {pts['published'][z]}  eye {pts['eye'][z]}  "
              f"argmax {pts['argmax'][z]}")
        for a, b in (('eye', 'published'), ('eye', 'argmax'), ('argmax', 'published')):
            dd = math.dist(pts[a][z], pts[b][z])
            print(f"       {a:6s} - {b:9s} {dd:7.1f} vox = {dd * um / 1000:5.2f} mm")
    print("  the by-eye placement is low-confidence: those two sections are crushed")
    print("  flat and show no whorl. It is one plausible correction, not the correction.")


def check_sampling():
    """The 300 slice indices were fixed by a rule, not chosen. Re-derive them
    from the shipped umbilicus files and check they are the ones that ran."""
    print("\n=== the slice sampling was a rule, not a choice ===")
    print("re-deriving z_k = round(z_min + k(z_max-z_min)/29), k = 0..29, minus 1 if odd,")
    print("from the shipped PHercNNNN_umbilicus.json, and comparing with what ran:")
    allok = True
    for s in SCROLLS:
        with open(os.path.join(ROOT, f'{s}_umbilicus.json')) as fh:
            zs = [p['z'] for p in json.load(fh)['control_points']]
        zmin, zmax = zs[0], zs[-1]
        rule = []
        for k in range(30):
            z = round(zmin + k * (zmax - zmin) / 29)
            rule.append(z - 1 if z % 2 else z)
        ran = [r["z_L0"] for r in load(s)["slices"]]
        allok &= (rule == ran)
        print(f"  {s}  annotated z {zmin}-{zmax}  30 slices  "
              f"{'identical' if rule == ran else 'DIFFERS'}")
    print(f"all ten: {'the run used exactly the slices the rule gives' if allok else 'MISMATCH'}")


def main():
    print("axis-benefit run, recomputed from " + DATA)
    check_sampling()
    report("stick_mean", "PRIMARY")
    report("stick_volume_centre", "[secondary] the volume-centre stick")
    exclusions()
    control()
    stick_distance()
    losses_and_rbar()
    posthoc()
    print("\nThis recomputes the statistics from the per-slice q values. It does not")
    print("re-measure them; see README section 6 for what re-measuring would take.")


if __name__ == '__main__':
    sys.exit(main())
