#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install and verify the three reference umbilici this package compares itself to.

What these files are
--------------------
PHerc0125, PHerc0211 and PHerc0826 were annotated and published by sean
(`bruniss`) on 2026-08-08, posted in the Vesuvius Challenge Discord `#general`
as three file attachments while he was measuring how long an umbilicus takes to
annotate. They are the only published umbilicus files for these scans that we
know of, and README section 3 uses them as the reference for the smoothness
comparison and for the ring-gate calibration.

Why they are not in this repository
-----------------------------------
They are not our work and we do not redistribute them. More to the point, we
could not point you at a stable public URL to fetch them from, and the earlier
version of the README was wrong to say you could get them "from the open
bucket". We checked, on 2026-08-13, and re-checked the same day after finding
that this docstring described the check badly. Both corrections are below.

  1. The command, with the flag it was missing. Note `&delimiter=/`:

    $ curl -s "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/\\
        ?list-type=2&prefix=PHerc0125/&delimiter=/&max-keys=1000"

  returns 504 bytes -- `<KeyCount>3</KeyCount>`, `<IsTruncated>false</IsTruncated>`,
  the three sub-prefixes `PHerc0125/photos/`, `PHerc0125/representations/` and
  `PHerc0125/volumes/`, and no `<Key>` elements at all. Same shape for PHerc0211
  and PHerc0826. WITHOUT the delimiter -- which is how this docstring used to
  document it -- the same URL returns 412 KB, `<KeyCount>1000</KeyCount>`,
  `<IsTruncated>true</IsTruncated>`, and after the first three keys nothing but
  `..._cos.ome.zarr/...` chunk paths. Running the old command showed you a
  thousand zarr chunks, not the three keys the text claimed.

  2. What is actually under those prefixes. This docstring used to say each
  prefix "lists three non-volume keys -- the mask photo, the photo, and a
  lasagna prediction json". Those are only the first three keys in key order.
  A full recursive walk, excluding `volumes/` and zarr chunk interiors, finds
  37,813 / 35,508 / 33,481 non-volume keys for PHerc0125 / PHerc0211 /
  PHerc0826. Nearly all of them -- 37,802 / 35,497 / 33,470 -- are an unmentioned
  `representations/predictions/surfaces/` tree: `...-surface-m7-L0-th0.2.normal-grids/`
  holding tens of thousands of `xy/`, `xz/`, `yz/` `.grid` files plus preview
  jpgs, and a `...-surface-m7-L0-th0.2.zarr` root. Its keys are dated
  2026-05-13 to 2026-07-07, so it predates the check; the enumeration was
  incomplete, not stale.

  What that walk does establish, and this is the part the conclusion rests on:
  across all 106,802 non-volume keys of the three prefixes there are ZERO
  matches for `umbilic|axis|centre|center|spiral|winding`, case-insensitive,
  and no loose key sits directly under any of the three prefixes. A depth-3
  crawl of `dl.ash2txt.org/community-uploads/bruniss/` -- 345 directory pages,
  137,026 files -- likewise returns zero matches for `umbilic`. There is no
  umbilicus file for these scans in the open bucket or in his uploads area. As
  far as we can establish the files exist only as those Discord attachments, so
  the honest instruction is "ask sean, or take them from that message", not
  "download them from X".

What this script does instead
-----------------------------
It makes the three files *checkable* once you have them, so that a number
computed on your copy and a number computed on ours are known to come from the
same bytes:

    python3 scripts/fetch_sean.py                     # check what is in ref_sean/
    python3 scripts/fetch_sean.py --from ~/Downloads  # copy them in, then check
    python3 scripts/fetch_sean.py --url PHerc0125=https://...   # or fetch by URL

Every copy is verified against the sha256 recorded in `qc/sean_reference.json`,
which is the digest `scripts/axis_stats.py` prints sean's three rows from when
the files are absent. A file whose hash does not match is written to
`<name>.mismatch` and NOT installed, because a silently different reference file
is worse than a missing one.

`qc/sean_reference.json` also records, for each of the three, the z range and
the eight derived scalars we measured. Once the files are in `ref_sean/`,
`axis_stats.py` runs two INDEPENDENT checks per row and prints both: whether
your copy's sha256 matches the digest, and whether all eight recomputed values
match it -- `kinkM` included, which is the column README section 3 argues is
the fair comparison. Neither check gates the other, so a file whose bytes
differ still gets its numbers compared and named, and a digest edited away from
the script that produced it is caught even with every sha256 intact. (An
earlier version nested the numeric comparison inside the sha256 test, where it
could only ever run on bytes already proven identical -- i.e. never usefully.)
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TREE = os.environ.get('UMBILICI_TREE', ROOT)
REF = os.path.join(TREE, 'ref_sean')
DIGEST = os.path.join(ROOT, 'qc', 'sean_reference.json')
NAMES = ('PHerc0125', 'PHerc0211', 'PHerc0826')


def digest():
    if not os.path.exists(DIGEST):
        raise SystemExit(f'{DIGEST} not found — it ships with this repository')
    return json.load(open(DIGEST))


def install(name, raw, want):
    got = hashlib.sha256(raw).hexdigest()
    os.makedirs(REF, exist_ok=True)
    dst = os.path.join(REF, f'{name}_umbilicus.json')
    if got != want['sha256']:
        bad = dst + '.mismatch'
        open(bad, 'wb').write(raw)
        print(f'{name}: sha256 MISMATCH — not installed\n'
              f'    expected {want["sha256"]}\n'
              f'    got      {got}\n'
              f'    written to {bad} so you can look at it')
        return False
    open(dst, 'wb').write(raw)
    print(f'{name}: sha256 ok ({len(raw)} bytes, {want["n_points"]} points, '
          f'z {want["z_first"]}-{want["z_last"]}) -> {dst}')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='src', metavar='DIR',
                    help='directory holding PHercNNNN_umbilicus.json')
    ap.add_argument('--url', action='append', default=[], metavar='NAME=URL',
                    help='fetch one file by URL; repeatable')
    a = ap.parse_args()
    d = digest()['scrolls']

    ok = fail = missing = 0
    urls = dict(u.split('=', 1) for u in a.url)
    for name in NAMES:
        want = d[name]
        raw = None
        if name in urls:
            print(f'{name}: fetching {urls[name]}')
            with urllib.request.urlopen(urls[name], timeout=60) as r:
                raw = r.read()
        elif a.src:
            p = os.path.join(os.path.expanduser(a.src), f'{name}_umbilicus.json')
            if os.path.exists(p):
                raw = open(p, 'rb').read()
        else:
            p = os.path.join(REF, f'{name}_umbilicus.json')
            if os.path.exists(p):
                raw = open(p, 'rb').read()
        if raw is None:
            print(f'{name}: not found (expected {want["bytes"]} bytes, '
                  f'sha256 {want["sha256"][:16]}...)')
            missing += 1
            continue
        if install(name, raw, want):
            ok += 1
        else:
            fail += 1

    print(f'\n{ok} verified, {fail} mismatched, {missing} missing.')
    if ok == len(NAMES):
        print('Run scripts/axis_stats.py — sean\'s three rows will now be '
              'recomputed from the files instead of read from the digest, and '
              'the script will say whether the two agree.')
    else:
        print('Without them scripts/axis_stats.py still prints all thirteen '
              'smoothness rows; sean\'s three come from qc/sean_reference.json '
              'and are marked as such.')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
