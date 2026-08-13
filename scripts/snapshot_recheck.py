#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure the one staleness this package discloses, instead of only disclosing it.

The caveat being closed
-----------------------
README, "Honest caveats":

    The shifted-axis control ran on a snapshot slightly older than the final
    files: 18/297 slices carry points that were later dropped at finalization,
    and three PHerc1545 points were moved (<=260 vox) after the control run.

That tells a reader the input drifted. It does not tell them whether the result
moved with it. This script re-runs the whole of section 2 on the FINAL shipped
files -- same measure, same slices, same displacements, same counting code --
and prints the published numbers next to the re-run ones so the size of the
staleness is a measured quantity rather than a caveat.

Nothing here replaces a published number. `qc/validation_raw.json` and the
section-2 figures stay exactly as they are; this is a second, later measurement
of the same thing on the newer input, and both are shipped.

Reproducing
-----------
    python3 scripts/snapshot_recheck.py               # compares the two shipped
                                                      # raw files
    python3 scripts/snapshot_recheck.py --measure     # recomputes the final-file
                                                      # side (needs the slice PNGs)

The counting is not reimplemented: it calls `count_wins.block`, the same
function that prints the published section-2 table.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('UMBILICI_ROOT', os.path.dirname(HERE))
TREE = os.environ.get('UMBILICI_TREE', ROOT)

OLD = os.path.join(ROOT, 'qc', 'validation_raw.json')
NEW = os.path.join(ROOT, 'qc', 'validation_final_raw.json')

SCROLLS = ["PHerc0191", "PHerc0257", "PHerc0268", "PHerc0358", "PHerc0800",
           "PHerc0813", "PHerc1203", "PHerc1218", "PHerc1447", "PHerc1545"]


def measure():
    """Re-run the section-2 measurement on the shipped (final) json files.

    Identical to `validate_axes.analyse` except that the axis is read from the
    shipped file at the repository root rather than from `submission/`, and the
    17x17 H map is not computed — no published number uses it and it is 289
    unwraps per slice.
    """
    from PIL import Image
    import validate_axes as V

    out = {}
    for name in SCROLLS:
        meta = json.load(open(os.path.join(TREE, name, 'meta.json')))
        cp = json.load(open(os.path.join(
            ROOT, f'{name}_umbilicus.json')))['control_points']
        rows = []
        for s in V.all_slices(meta, cp):
            img = np.asarray(Image.open(os.path.join(TREE, name, s['file'])
                                        ).convert('L'), dtype=np.float32)
            ax = V.axis_at(cp, s['z'])
            cx, cy = ax[0] / V.SCALE, ax[1] / V.SCALE
            rec = {'z': s['z'], 'file': s['file'], 'cx': cx, 'cy': cy}
            rec['h'] = V.coherence(*V.unwrap(img, cx, cy))[0]
            for sv in V.SHIFT_VOX:
                d = sv / V.SCALE
                hs = [V.coherence(*V.unwrap(img, cx + a, cy + b))[0]
                      for a, b in ((d, 0), (-d, 0), (0, d), (0, -d))]
                rec[f'h{sv}'] = hs
                rec[f'h{sv}_mean'] = float(np.nanmean(hs))
            for sv in V.SHIFT_VOX:
                m = rec[f'h{sv}_mean']
                rec[f'r{sv}'] = rec['h'] / m if m else float('nan')
            rows.append(rec)
            del img
        out[name] = rows
        print(f'{name}: {len(rows)} slices', flush=True)
    os.makedirs(os.path.join(ROOT, 'qc'), exist_ok=True)
    json.dump(out, open(NEW, 'w'), indent=1)
    print('written', NEW)


def drift(old, new):
    same = moved = 0
    where = []
    for name in SCROLLS:
        o = {r['z']: r for r in old.get(name, [])}
        for r in new.get(name, []):
            if r['z'] not in o:
                where.append((name, r['z'], 'slice not in the snapshot run'))
                continue
            if o[r['z']]['h'] == r['h']:
                same += 1
            else:
                moved += 1
                where.append((name, r['z'],
                              f"h {o[r['z']]['h']:.4f} -> {r['h']:.4f}"))
    print(f'\n=== how far the input actually drifted ===')
    print(f'slices whose measured value at the annotated centre is bit-identical '
          f'between the two runs: {same}')
    print(f'slices where it changed: {moved}')
    for n, z, what in where:
        print(f'  {n} z={z}: {what}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--measure', action='store_true')
    a = ap.parse_args()
    if a.measure:
        return measure()
    for p in (OLD, NEW):
        if not os.path.exists(p):
            raise SystemExit(f'{p} not found')
    old = json.load(open(OLD))
    new = json.load(open(NEW))

    sys.path.insert(0, HERE)
    import count_wins

    print('################ PUBLISHED — the snapshot run, qc/validation_raw.json')
    for key in ('r300', 'r150'):
        count_wins.block(old, key)
    print('\n\n################ RE-RUN ON THE FINAL SHIPPED FILES — '
          'qc/validation_final_raw.json')
    for key in ('r300', 'r150'):
        count_wins.block(new, key)
    drift(old, new)


if __name__ == '__main__':
    sys.exit(main())
