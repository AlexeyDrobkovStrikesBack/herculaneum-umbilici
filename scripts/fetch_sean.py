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
bucket". We checked, on 2026-08-13:

    $ curl -s "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/\\
        ?list-type=2&prefix=PHerc0125/&max-keys=1000"

  lists three non-volume keys for PHerc0125 — the mask photo, the photo, and a
  lasagna prediction json — and the same for PHerc0211 and PHerc0826. There is
  no umbilicus file under any of the three prefixes. There is none under
  `dl.ash2txt.org/community-uploads/bruniss/` either. As far as we can establish
  the files exist only as those Discord attachments, so the honest instruction is
  "ask sean, or take them from that message", not "download them from X".

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

`qc/sean_reference.json` also records, for each of the three, the point count,
the z range and the six smoothness numbers we measured. If your copy hashes the
same, `axis_stats.py` will recompute those six and tell you they agree.
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
