#!/usr/bin/env python3
"""Recompute the winding-order statistic of README section 1 from a shipped fixture.

What this closes, and what it does not
--------------------------------------
The numbers in README section 1 -- 0.919/0.900/0.850 for the manual axis against
0.826/0.738/0.782 for the auto-centroid, and the paired counts 43:7 / 42:5 / 21:3
-- were produced by a tracing pipeline that is not in this repository (it needs
the L3 slice stacks; see README "What is scripted"). This script does not run
that tracer. It takes the tracer's output -- the traced arcs, already matched
across heights into tracks -- and recomputes the statistic itself, so the step
from "arcs on slices" to "85-92% vs 74-83%" is arithmetic a reader can check
rather than a number to be taken on trust.

The fixture (qc/order_fixture_PHercNNNN.npz, ~600 KB each) holds, for one
scroll's neutral-tracing stack:

  slice_z, slice_coarse   the 25 heights of the stack (5 catalogue + 20 thin)
  man_c, auto_c           the two axes' centres on each of those heights,
                          interpolated from the shipped umbilicus json and from
                          auto_centers.json exactly as any consumer would
  track_id, slice_idx,    the traced arcs: for every (track, height) pair, the
  ptr, pts                arc's points in L3 pixel coordinates (float32)

Everything below -- who is closer to the axis, whether that order is preserved
across the stack, the paired cross-tabulation -- is computed here from those
points. The two axes are scored on an identical pair sample by construction: a
pair enters only if BOTH axes yield a defined sign on at least three common
heights.

Usage:  python3 scripts/order_stat.py [PHerc0191 ...]
Needs:  numpy.
"""
import json
import os
import sys

import numpy as np

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCROLLS = ['PHerc0191', 'PHerc0358', 'PHerc1203']

# Parameters of the sign test, identical to the producer's radial_sign().
BIN_DEG = 2.0
MIN_BINS = 5
DOMINANCE = 0.8
MIN_COMMON = 3      # heights on which BOTH axes must give a sign


def radial_sign(pa, pb, centre):
    """+1 if arc A is closer to `centre` than arc B, -1 if further, None if the
    two arcs cross as seen from that centre.

    Radii are compared ray by ray: both arcs' points are binned by polar angle
    around the centre in 2-degree bins, and only bins occupied by both arcs are
    used. A verdict needs at least five shared bins and 80% agreement among
    them; anything less ambiguous than that returns None and the pair is not
    counted for that height, for either axis.
    """
    cx, cy = centre
    tha = np.degrees(np.arctan2(pa[:, 1] - cy, pa[:, 0] - cx)) % 360
    thb = np.degrees(np.arctan2(pb[:, 1] - cy, pb[:, 0] - cx)) % 360
    ra = np.hypot(pa[:, 0] - cx, pa[:, 1] - cy)
    rb = np.hypot(pb[:, 0] - cx, pb[:, 1] - cy)
    ba = (tha // BIN_DEG).astype(int)
    bb = (thb // BIN_DEG).astype(int)
    ma, mb = {}, {}
    for b, r in zip(ba, ra):
        ma.setdefault(b, []).append(r)
    for b, r in zip(bb, rb):
        mb.setdefault(b, []).append(r)
    common = set(ma) & set(mb)
    if len(common) < MIN_BINS:
        return None
    s = np.array([1 if np.mean(ma[b]) < np.mean(mb[b]) else -1 for b in common])
    frac_pos = (s > 0).mean()
    if frac_pos >= DOMINANCE:
        return 1
    if frac_pos <= 1 - DOMINANCE:
        return -1
    return None


def load(path):
    z = np.load(path, allow_pickle=False)
    tracks = {}
    tid, sidx, ptr, pts = z['track_id'], z['slice_idx'], z['ptr'], z['pts']
    for k in range(len(tid)):
        tracks.setdefault(int(tid[k]), {})[int(sidx[k])] = \
            pts[ptr[k]:ptr[k + 1]].astype(np.float64)
    return z, [tracks[k] for k in sorted(tracks)]


def run(scroll):
    path = f'{ROOT}/qc/order_fixture_{scroll}.npz'
    if not os.path.exists(path):
        print(f'{scroll}: {path} not found')
        return None
    z, tracks = load(path)
    man_c, auto_c = z['man_c'], z['auto_c']

    pair_signs = []
    for a in range(len(tracks)):
        for b in range(a + 1, len(tracks)):
            common = sorted(set(tracks[a]) & set(tracks[b]))
            if len(common) < 2:
                continue
            sm, sa = {}, {}
            for i in common:
                pa, pb = tracks[a][i], tracks[b][i]
                s1 = radial_sign(pa, pb, man_c[i])
                s2 = radial_sign(pa, pb, auto_c[i])
                if s1 is not None:
                    sm[i] = s1
                if s2 is not None:
                    sa[i] = s2
            both = sorted(set(sm) & set(sa))
            if len(both) >= MIN_COMMON:
                pair_signs.append(({i: sm[i] for i in both},
                                   {i: sa[i] for i in both}))

    out = {'scroll': scroll, 'n_tracks': len(tracks), 'n_pairs': len(pair_signs)}
    for key, idx in (('man', 0), ('auto', 1)):
        kept = sum(1 for ps in pair_signs if len(set(ps[idx].values())) == 1)
        out[key] = {'kept': kept, 'total': len(pair_signs),
                    'frac': round(kept / len(pair_signs), 3) if pair_signs else None}
    mo = ao = both_ = neither = 0
    for sm, sa in pair_signs:
        km = len(set(sm.values())) == 1
        ka = len(set(sa.values())) == 1
        if km and ka:
            both_ += 1
        elif km:
            mo += 1
        elif ka:
            ao += 1
        else:
            neither += 1
    out['cross'] = {'both': both_, 'man_only': mo, 'auto_only': ao,
                    'neither': neither}
    return out


def main():
    want = [s for s in sys.argv[1:] if s in SCROLLS] or SCROLLS
    print('=== winding-order statistic, neutral tracing, recomputed from the '
          'shipped fixtures ===')
    print(f'{"scroll":<11}{"manual axis":>16}{"auto-centroid":>17}'
          f'{"shared pairs":>14}{"kept only man : only auto":>28}')
    rows = []
    for s in want:
        r = run(s)
        if r is None:
            continue
        rows.append(r)
        c = r['cross']
        print(f'{s:<11}{r["man"]["frac"]:>9.3f} ({r["man"]["kept"]:>3}) '
              f'{r["auto"]["frac"]:>9.3f} ({r["auto"]["kept"]:>3})'
              f'{r["man"]["total"]:>14}'
              f'{c["man_only"]:>21} : {c["auto_only"]}')
    if rows:
        mans = [r['man']['frac'] for r in rows]
        autos = [r['auto']['frac'] for r in rows]
        print(f'\nmanual axis {min(mans):.3f}-{max(mans):.3f}, '
              f'auto-centroid {min(autos):.3f}-{max(autos):.3f}')
        print('full cross-tabulation (both / manual only / auto only / neither):')
        for r in rows:
            c = r['cross']
            print(f'  {r["scroll"]}  {c["both"]} / {c["man_only"]} / '
                  f'{c["auto_only"]} / {c["neither"]}   tracks={r["n_tracks"]}')
    print('\nThis recomputes the statistic from the traced arcs. It does not '
          'run the tracer;\nsee README "What is scripted" for what that would '
          'take.')
    if os.environ.get('ORDER_STAT_JSON'):
        json.dump(rows, open(os.environ['ORDER_STAT_JSON'], 'w'), indent=1)


if __name__ == '__main__':
    main()
