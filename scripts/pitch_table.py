#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The winding-pitch numbers of the README caveats, recomputed rather than quoted.

Until now these were the last two numbers in the package with no shipped source
at all: the FFT range 247-371 um, the ridge-interval cross-check range
380-468 um, and the per-spot ratios behind "6% to 90% higher place for place".
The producer needs the L3 slices and is not in this repository, but its output
for the five measured spots is five pairs of numbers, and those now ship as
`qc/winding_map_metrics.json` -- the producer's own output file, copied verbatim
from the annotation tree, keys and all.

What this script adds on top of merely shipping it is the voxel correction, the
one piece of arithmetic a reader would otherwise have to trust:

  the demo pipeline converted pixels to micrometres with 9.362 um/voxel for
  every scroll. Four of the ten scrolls are 8.640 um/voxel, and one of the five
  measured spots (PHerc0800 z=12512) is on one of them. Its two values are
  therefore scaled by 8.640/9.362. The voxel size is not hard-coded here: it is
  parsed out of `metadata.source_volume` of that scroll's shipped umbilicus
  json, the same way `axis_stats.py` does it.

    python3 scripts/pitch_table.py

Needs numpy only for nothing at all -- this script uses the standard library.
"""
import json
import os
import re
import sys

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'qc', 'winding_map_metrics.json')
DEMO_UM = 9.362      # what the demo pipeline assumed for every scroll
L3 = 8               # L0 voxels per L3 pixel


def voxel_um(scroll):
    p = os.path.join(ROOT, f'{scroll}_umbilicus.json')
    vol = json.load(open(p))['metadata']['source_volume']
    m = re.search(r'-([0-9]+\.[0-9]+)um-', vol)
    if not m:
        raise SystemExit(f'no voxel size in {scroll} source_volume')
    return float(m.group(1))


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f'{SRC} not found')
    rows = json.load(open(SRC))
    print('=== winding pitch at the five readable spots ===')
    print(f"{'scroll':10} {'z':>7} {'vox um':>7} {'FFT (as run)':>13} "
          f"{'FFT':>8} {'check (as run)':>15} {'check':>8} {'check/FFT':>10}")
    ffts, checks = [], []
    for r in rows:
        um = voxel_um(r['scroll'])
        k = um / DEMO_UM
        fft = r['pitch_ours_um'] * k
        chk = r['spacing_check_um'] * k
        ffts.append(fft)
        checks.append(chk)
        print(f"{r['scroll']:10} {r['z']:7d} {um:7.3f} {r['pitch_ours_um']:13.1f} "
              f"{fft:8.1f} {r['spacing_check_um']:15.1f} {chk:8.1f} "
              f"{chk/fft:10.3f}")
    print(f'\nFFT range              {min(ffts):.1f} - {max(ffts):.1f} um   '
          f'(README: 247-371)')
    print(f'cross-check range      {min(checks):.1f} - {max(checks):.1f} um   '
          f'(README: 380-468)')
    print(f'cross-check / FFT      {min(c/f for c, f in zip(checks, ffts)):.2f}x'
          f' - {max(c/f for c, f in zip(checks, ffts)):.2f}x   '
          f'(README: 6% to 90% higher)')
    print(f'\nThe cross-check is quantised: 5.5 L3 pixels is '
          f'{5.5 * 9.362 * L3:.1f} um on a 9.362 um scroll and '
          f'{5.5 * 8.640 * L3:.1f} um on an 8.640 um one, and the cross-check '
          f'returns\nexactly that at three of the five spots. That is why it is '
          f'not treated as independent confirmation to micrometre precision.')
    print('\nThese are LOCAL pitches, at spots chosen because the laminae have '
          'separated far enough to be\nreadable at L3. Our own pitch work puts '
          'tightly-wound material at 180-225 um. Read the range as\n"the pitch '
          'at these five spots", not as the winding pitch of these scrolls.')


if __name__ == '__main__':
    sys.exit(main())
