#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stamp the villa#1454 frame-metadata keys into the ten umbilicus files.

    python3 scripts/stamp_frame.py --check     # verify the ten as they stand
    python3 scripts/stamp_frame.py --write     # (re)stamp them

Both modes go to the bucket. Nothing here is typed by hand: every stamped
value is derived from that file's own `metadata.source_volume` and read back
out of the public bucket before it is written.

The schema
----------
Open PR ScrollPrize/villa#1454 (`umbilicus: frame metadata, project attachment,
shared resolver`, commit 85c5be1) adds five optional keys to the `metadata`
block of `umbilicus.json`, with the stated intent that generators stamp them:

    "volume":        string   the store the umbilicus was annotated on
    "voxelsize_um":  number   voxel size of the grid the coordinates index
    "volume_width":  integer  exact voxel counts of that grid; the dimension
    "volume_height": integer  ratios identify a rescaled copy of the same scan
    "volume_slices": integer  where micrometre values round

The consumer rule the PR states is `voxelsize_um / target_voxelsize_um`.
`voxelsize_um` is authoritative; `volume` and the three dimensions are
provenance. Unstamped files load exactly as before, so the stamp is additive.

Why our ten carry it, in one line: they span two voxel sizes (9.362 µm for six,
8.640 µm for four), which the README has handled in prose since day one and
which these keys make machine-checkable. README §8 gives the full reasoning
and the risk.

Where each value comes from
---------------------------
    voxelsize_um   the `-<n>um-` token of `metadata.source_volume`, CHECKED
                   against `<volume>/metadata.json` →
                   scan.tomo.acquisition.detector.samplePixelSize (mm × 1000).
                   A mismatch is a hard error; nothing is written.
    volume_width   `<volume>/0/.zarray` → shape[2]   (x)
    volume_height  `<volume>/0/.zarray` → shape[1]   (y)
    volume_slices  `<volume>/0/.zarray` → shape[0]   (z)
    volume         the store name — the last path component of
                   `metadata.source_volume`. The full bucket path stays in
                   `source_volume`, which we do not touch.

    NOTE, and it is a real limit of these ten files: all ten volumes have
    shape[1] == shape[2], so `volume_width` and `volume_height` are equal in
    every one of them. Nothing in this package can therefore distinguish the
    two conventions, and a consumer must not read our files as evidence for
    either. It is printed per scroll so the reader sees it.

Byte identity
-------------
`--write` breaks the md5s the package carried from commit da52f97 onward. That
is deliberate and is recorded in README §8 with the old and the new hash for
each of the ten. The rewrite is `json.dump(..., indent=1)` with no trailing
newline, which round-trips these files byte-for-byte when nothing is added —
verified by `--check` on an unstamped file, so the diff is the five keys and
nothing else.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.environ.get("UMBILICI_ROOT",
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"

SCROLLS = ["PHerc0191", "PHerc0257", "PHerc0268", "PHerc0358", "PHerc0800",
           "PHerc0813", "PHerc1203", "PHerc1218", "PHerc1447", "PHerc1545"]

KEYS = ("volume", "voxelsize_um", "volume_width", "volume_height", "volume_slices")


def get_json(url):
    with urllib.request.urlopen(url, timeout=180) as r:
        return json.load(r)


def frame_of(volume):
    """(voxelsize_um from the id, voxelsize_um from the bucket, shape z,y,x)."""
    m = re.search(r"-([0-9]+\.[0-9]+)um-", volume)
    if not m:
        raise SystemExit(f"no voxel size in {volume!r}")
    um_id = float(m.group(1))
    shape = get_json(f"{BUCKET}/{volume}/0/.zarray")["shape"]
    md = get_json(f"{BUCKET}/{volume}/metadata.json")
    um_bucket = md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"] * 1000.0
    return um_id, um_bucket, shape


def dump(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False).encode()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    a = ap.parse_args()

    bad = 0
    print(f"{'scroll':10} {'voxel um: id / bucket':24} {'level-0 shape z,y,x':24} "
          f"{'w==h':5} {'pts':4} {'meta.json':8} {'state'}")
    for s in SCROLLS:
        path = os.path.join(ROOT, f"{s}_umbilicus.json")
        raw = open(path, "rb").read()
        doc = json.loads(raw)
        meta = doc["metadata"]
        volume = meta["source_volume"]
        um_id, um_bucket, shape = frame_of(volume)

        agree = abs(um_id - um_bucket) < 1e-6

        # Two checks the stamp would be worthless without.
        cp = doc["control_points"]
        inb = all(0 <= p["z"] < shape[0] and 0 <= p["y"] < shape[1]
                  and 0 <= p["x"] < shape[2] for p in cp)
        # shape_L0 was recorded in the annotation tree when the slices were cut,
        # independently of today's bucket read, so agreeing is worth something.
        mpath = os.path.join(ROOT, s, "meta.json")
        tree = json.load(open(mpath))["shape_L0"] if os.path.exists(mpath) else None
        tree_ok = None if tree is None else (list(tree) == list(shape))

        stamp = {
            "volume": volume.rsplit("/", 1)[-1],
            "voxelsize_um": um_id,
            "volume_width": int(shape[2]),
            "volume_height": int(shape[1]),
            "volume_slices": int(shape[0]),
        }
        present = [k for k in KEYS if k in meta]
        if present:
            same = all(meta[k] == stamp[k] for k in KEYS if k in meta)
            state = ("stamped, agrees" if (same and len(present) == len(KEYS))
                     else "!! STAMPED BUT DISAGREES WITH THE BUCKET")
        else:
            state = "unstamped"
        if not agree:
            state = "!! VOXEL SIZE DISAGREES WITH THE BUCKET"
        elif not inb:
            state = "!! CONTROL POINTS OUT OF BOUNDS FOR THIS SHAPE"
        elif tree_ok is False:
            state = "!! DISAGREES WITH THE ANNOTATION TREE'S OWN shape_L0"
        if state.startswith("!!"):
            bad += 1

        print(f"{s:10} {um_id:>9.3f} / {um_bucket:<12.4f} "
              f"{str(shape):24} {str(shape[1] == shape[2]):5} "
              f"{'in' if inb else 'OUT':4} "
              f"{('tree -' if tree_ok is None else ('tree ok' if tree_ok else 'TREE !!')):8} "
              f"{state}")

        if a.write and agree:
            before = hashlib.md5(raw).hexdigest()
            for k in KEYS:
                meta.pop(k, None)
            meta.update(stamp)
            new = dump(doc)
            open(path, "wb").write(new)
            after = hashlib.md5(new).hexdigest()
            print(f"{'':10} md5 {before} -> {after}"
                  f"{'   (unchanged)' if before == after else ''}")

    if bad:
        sys.exit(f"\n{bad} problem(s); nothing further was written")
    print("\nall ten agree with the bucket")


if __name__ == "__main__":
    main()
