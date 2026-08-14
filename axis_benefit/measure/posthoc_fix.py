"""Post-hoc only (PREREGISTRATION.md sec.10.5).  Builds corrected copies of the
PHerc0813 umbilicus for the two suspect control points, z = 6616 and z = 9296.
`umbilici_repo` is never written to.

Variants
  eye   -- both points re-placed by eye on the rendered cross-section, without
           reference to q (figs/zoom_z6616_b.png, figs/zoom_z9296_b.png).
  drop  -- both points deleted, so villa's loader interpolates across them.
           Completely independent of q and of my eye.
  argmax-- both points placed at the q-argmax on their own slice.  Circular by
           construction: the measure that scores the axis chooses the axis.
           An upper bound, never an estimate.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import axisdemo as A          # noqa: E402
import tiled_st               # noqa: E402
import zslice_http as Z       # noqa: E402
from prereg_run import VOL, LEVEL, common_outer_radius_strict, R0_FRAC  # noqa: E402

SRC = "<repo>/PHerc0813_umbilicus.json"
SUSPECT_Z = [6616, 9296]
# by-eye placements, level-0 (x, y).  Read off the zoomed cross-sections from the
# curvature of the sheets; the sections are badly crushed and these carry an
# uncertainty of roughly +-300 px (2.8 mm), which is stated in the report.
EYE = {6616: (4600, 4400), 9296: (4300, 4200)}


def write_variant(name, transform):
    d = json.load(open(SRC))
    d["control_points"] = transform([dict(p) for p in d["control_points"]])
    d.setdefault("metadata", {})["annotator_note"] = f"POST-HOC variant '{name}' - not the published annotation"
    out = os.path.join(HERE, f"PHerc0813_posthoc_{name}.json")
    json.dump(d, open(out, "w"), indent=1)
    print("wrote", out, len(d["control_points"]), "points")
    return out


def find_argmax():
    vol, um = VOL["PHerc0813"]
    root = f"vesuvius-challenge-open-data/PHerc0813/volumes/{vol}"
    res = {}
    for z0 in SUSPECT_Z:
        img = Z.read_zslice(root, LEVEL, z0 // 2)
        inside = img > 0
        ca = np.asarray(A.villa_axis(SRC, LEVEL)(z0 // 2), float)
        cb = np.asarray(A.stick_from_mean(SRC, LEVEL)(z0 // 2), float)
        r1 = common_outer_radius_strict(inside, [ca, cb])
        if r1 is None:
            r1 = 500.0
        r0 = float(round(R0_FRAC * r1))
        J = tiled_st.structure_tensor_tiled(img, sub=4)
        ins = inside[::4, ::4]
        offs = np.arange(-1400, 1401, 100)
        best = (-9, None)
        for dy in offs:
            for dx in offs:
                c = np.array([ca[0] + dy, ca[1] + dx])
                if A.ring_inside_fraction(inside, c, r1) < 0.95:
                    continue
                q = A.radial_anisotropy_sectored(J, ins, c / 4, r0 / 4, r1 / 4)[0]
                if np.isfinite(q) and q > best[0]:
                    best = (float(q), (float(c[0]), float(c[1])))
        print(f"  z{z0}: annulus {r0:.0f}-{r1:.0f}, argmax q={best[0]:+.4f} at yx={best[1]} "
              f"(annotated yx={ca.tolist()})")
        res[z0] = best
        del img, inside, J, ins
    return res


if __name__ == "__main__":
    def eye(pts):
        for p in pts:
            if p["z"] in EYE:
                p["x"], p["y"] = EYE[p["z"]]
        return pts

    def drop(pts):
        return [p for p in pts if p["z"] not in SUSPECT_Z]

    write_variant("eye", eye)
    write_variant("drop", drop)

    print("q-argmax search (circular upper bound):")
    res = find_argmax()
    json.dump({str(k): v for k, v in res.items()},
              open(os.path.join(HERE, "posthoc_argmax.json"), "w"), indent=1)

    def argm(pts):
        for p in pts:
            if p["z"] in res and res[p["z"]][1]:
                y, x = res[p["z"]][1]
                p["x"], p["y"] = int(round(x * 2)), int(round(y * 2))
        return pts

    write_variant("argmax", argm)
