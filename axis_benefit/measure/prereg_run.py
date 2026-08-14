"""The pre-registered run.  Specification: _axisdemo/PREREGISTRATION.md (fixed 17:35).

Nothing here decides anything the specification left open; every threshold, every
rule and every slice index comes from that file.  Slices are streamed and
discarded.  One JSON per scroll: prereg_<scroll>.json.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import axisdemo as A            # noqa: E402  scoring code, frozen at prereg time
import tiled_st                 # noqa: E402  verified bit-identical to A.structure_tensor
import zslice_http as Z         # noqa: E402  verified byte-identical to the s3fs path
from zlist import zs as prereg_zs  # noqa: E402

torch.set_num_threads(2)

VOL = {
    "PHerc0191": ("20250821151635-9.362um-1.2m-113keV-masked.zarr", 9.362),
    "PHerc0257": ("20250821151750-9.362um-1.2m-113keV-masked.zarr", 9.362),
    "PHerc0268": ("20251110183117-8.640um-1.2m-116keV-masked.zarr", 8.640),
    "PHerc0358": ("20250821151737-9.362um-1.2m-113keV-masked.zarr", 9.362),
    "PHerc0800": ("20250521135224-8.640um-1.2m-116keV-masked.zarr", 8.640),
    "PHerc0813": ("20250821151723-9.362um-1.2m-113keV-masked.zarr", 9.362),
    "PHerc1203": ("20250820131727-9.362um-1.2m-113keV-masked.zarr", 9.362),
    "PHerc1218": ("20250521120456-8.640um-1.2m-116keV-masked.zarr", 8.640),
    "PHerc1447": ("20250521151220-8.640um-1.2m-116keV-masked.zarr", 8.640),
    "PHerc1545": ("20250821151648-9.362um-1.2m-113keV-masked.zarr", 9.362),
}

LEVEL = 1
SUB = 2
R0_FRAC = 0.25
RING_FRAC = 0.95
R_MAX, R_MIN, R_STEP = 2000, 400, 25
DR_GRID = np.arange(4.0, 30.01, 0.5)
CONTROL_D = [25, 50, 100, 200, 400, 800]
CONTROL_DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
CONTROL_K = [0, 5, 10, 15, 20, 25]          # which of the 30 slices carry the control
STATUS = "/home/alexr/vesuvius/load_status.txt"


# ------------------------------------------------------------ compute gate --
def gate_wait(tag=""):
    """Pause while the station is loaded.  See PREREGISTRATION.md sec.11."""
    waited = 0
    while True:
        try:
            f = dict(kv.split("=", 1) for kv in open(STATUS).read().split() if "=" in kv)
            load = float(f.get("load", 0))
            mem = float(f.get("mem_avail", "9G").rstrip("G"))
        except Exception:
            return waited
        if load <= 1.25 * 16 and mem >= 1.2:
            return waited
        if waited == 0:
            print(f"  [gate] pausing {tag}: load={load} mem={mem}G", flush=True)
        time.sleep(30)
        waited += 30


# ---------------------------------------------------- strict annulus rule ---
def common_outer_radius_strict(inside, centres):
    """As axisdemo.common_outer_radius but with NO fall-back: None if no radius
    in [R_MIN, R_MAX] gives every candidate axis a >=95 % ring (PREREG sec.7)."""
    for r in range(R_MAX, R_MIN - 1, -R_STEP):
        if all(A.ring_inside_fraction(inside, c, r) >= RING_FRAC for c in centres):
            return float(r)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scrolls", nargs="+")
    ap.add_argument("--umb-suffix", default="_umbilicus.json")
    ap.add_argument("--umb-dir", default="/home/alexr/vesuvius/umbilici_repo")
    ap.add_argument("--out-suffix", default="")
    ap.add_argument("--no-control", action="store_true")
    args = ap.parse_args()

    for scroll in args.scrolls:
        vol, um_L0 = VOL[scroll]
        root = f"vesuvius-challenge-open-data/{scroll}/volumes/{vol}"
        umb = os.path.join(args.umb_dir, f"{scroll}{args.umb_suffix}")
        um_px = um_L0 * 2 ** LEVEL
        out_path = os.path.join(HERE, f"prereg_{scroll}{args.out_suffix}.json")

        ax_annot = A.villa_axis(umb, LEVEL)
        ax_stick = A.stick_from_mean(umb, LEVEL)
        zlist = prereg_zs(scroll)

        res = dict(scroll=scroll, volume=root, umbilicus=umb, level=LEVEL, um_per_px=um_px,
                   spec="PREREGISTRATION.md 2026-08-13 17:35",
                   params=dict(sub=SUB, r0_frac=R0_FRAC, ring_frac=RING_FRAC,
                               r_sweep=[R_MAX, R_MIN, R_STEP], n_sectors=72,
                               sigma_d=1.5, sigma_t=6.0, dr_grid=[4.0, 30.0, 0.5],
                               phase_band=100.0, seed=0, control_d=CONTROL_D,
                               control_k=CONTROL_K),
                   slices=[])

        pool = ThreadPoolExecutor(1)
        nxt = pool.submit(Z.read_zslice, root, LEVEL, zlist[0] // 2)
        t_scroll = time.time()
        for k, z0 in enumerate(zlist):
            zl = z0 // 2
            img = nxt.result()
            if k + 1 < len(zlist):
                nxt = pool.submit(Z.read_zslice, root, LEVEL, zlist[k + 1] // 2)
            gate_wait(f"{scroll} z{z0}")
            t0 = time.time()

            inside = img > 0
            n_in = int(inside.sum())
            rec = dict(k=k, z_L0=z0, z_level=zl, n_inside=n_in, conditions={})
            if n_in < 10_000:
                rec["scorable"] = False
                rec["reason"] = "empty slice"
                res["slices"].append(rec)
                print(f"  {scroll} k{k:02d} z{z0} EMPTY", flush=True)
                del img, inside
                gc.collect()
                json.dump(res, open(out_path, "w"), indent=1)
                continue

            c_annot = np.asarray(ax_annot(zl), float)
            c_stick = np.asarray(ax_stick(zl), float)
            c_vol = np.array([img.shape[0] / 2.0, img.shape[1] / 2.0])
            main_c = [("annotated", c_annot), ("stick_mean", c_stick),
                      ("stick_volume_centre", c_vol)]
            rec["centres"] = {n: [float(c[0]), float(c[1])] for n, c in main_c}

            r1 = common_outer_radius_strict(inside, [c for _, c in main_c])
            if r1 is None:
                rec["scorable"] = False
                rec["reason"] = "no common annulus at >=95% ring coverage"
                rec["ring_at_400"] = {n: A.ring_inside_fraction(inside, c, 400.0)
                                      for n, c in main_c}
                res["slices"].append(rec)
                print(f"  {scroll} k{k:02d} z{z0} NO-ANNULUS "
                      f"{rec['ring_at_400']}", flush=True)
                del img, inside
                gc.collect()
                json.dump(res, open(out_path, "w"), indent=1)
                continue
            r0 = float(round(R0_FRAC * r1))
            rec["r0"], rec["r1"] = r0, r1

            mask, _, thr = A.papyrus_mask(img)
            rec["threshold"] = thr
            J = tiled_st.structure_tensor_tiled(img, sigma_d=1.5, sigma_t=6.0, sub=SUB)
            ins = inside[::SUB, ::SUB]

            conds = list(main_c)
            if not args.no_control and k in CONTROL_K:
                for d in CONTROL_D:
                    for i, (uy, ux) in enumerate(CONTROL_DIRS):
                        conds.append((f"control_d{d}_dir{i}",
                                      c_annot + np.array([uy, ux], float) * d))

            for name, c in conds:
                q, npx, frac = A.radial_anisotropy_sectored(J, ins, c / SUB, r0 / SUB, r1 / SUB)
                d = dict(q=None if not np.isfinite(q) else float(q), n_pixels=int(npx),
                         valid_sector_frac=float(frac),
                         ring95=A.ring_inside_fraction(inside, c, r1),
                         displacement_px=float(np.hypot(*(c - c_annot))))
                d["displacement_um"] = d["displacement_px"] * um_px
                if name in ("annotated", "stick_mean", "stick_volume_centre"):
                    rb, dr, nph = A.phase_concentration(img, mask, c, r0, r1, DR_GRID,
                                                        rng=np.random.default_rng(0))
                    d["rbar"] = None if not np.isfinite(rb) else float(rb)
                    d["dr_best"] = None if not np.isfinite(dr) else float(dr)
                rec["conditions"][name] = d

            qs = {n: rec["conditions"][n]["q"] for n, _ in main_c}
            rec["scorable"] = all(v is not None for v in qs.values())
            if not rec["scorable"]:
                rec["reason"] = "invalid q for " + ",".join(n for n, v in qs.items() if v is None)
            res["slices"].append(rec)
            print(f"  {scroll} k{k:02d} z{z0} r=[{r0:.0f},{r1:.0f}] "
                  f"A={qs['annotated']} B1={qs['stick_mean']} B2={qs['stick_volume_centre']} "
                  f"{'OK' if rec['scorable'] else 'NON-SCORABLE'} [{time.time()-t0:.0f}s]",
                  flush=True)
            json.dump(res, open(out_path, "w"), indent=1)
            del img, inside, mask, J, ins
            gc.collect()
        pool.shutdown()
        json.dump(res, open(out_path, "w"), indent=1)
        print(f"wrote {out_path}  [{(time.time()-t_scroll)/60:.1f} min]", flush=True)


if __name__ == "__main__":
    main()
