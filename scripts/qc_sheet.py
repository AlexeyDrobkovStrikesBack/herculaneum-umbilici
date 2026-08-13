#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contact sheet: one row per scroll, the auto-center marked with a cross.
By eye you can see whether the guess landed inside the body of the scroll and
whether the holder crept into the frame.
   python qc_sheet.py [output_dir]
"""
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.environ.get('UMBILICI_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT
T = 260          # tile size
PER = 8          # slices per row


def main():
    rows = []
    for name in sorted(os.listdir(ROOT)):
        mp = os.path.join(ROOT, name, "meta.json")
        if not os.path.exists(mp):
            continue
        m = json.load(open(mp))
        auto = json.load(open(os.path.join(ROOT, name, "auto_centers.json")))
        sc = m["scale"]
        step = max(1, len(m["slices"]) // PER)
        picks = list(zip(m["slices"], auto))[::step][:PER]
        tiles = []
        for sl, a in picks:
            im = Image.open(os.path.join(ROOT, name, sl["file"])).convert("RGB")
            d = ImageDraw.Draw(im)
            x, y = a["x"] / sc, a["y"] / sc
            r = im.width // 22
            d.line([(x - r, y), (x + r, y)], fill=(255, 90, 0), width=4)
            d.line([(x, y - r), (x, y + r)], fill=(255, 90, 0), width=4)
            d.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], outline=(255, 90, 0), width=4)
            d.text((10, 10), f"z{sl['z']}", fill=(255, 235, 0))
            tiles.append(im.resize((T, T)))
            del im
        sheet = Image.new("RGB", (T * PER, T), (0, 0, 0))
        for i, t in enumerate(tiles):
            sheet.paste(t, (i * T, 0))
        d = ImageDraw.Draw(sheet)
        d.text((6, T - 16), name, fill=(255, 235, 0))
        p = os.path.join(OUT, f"qc_{name}.png")
        sheet.save(p)
        rows.append((name, len(m["slices"]), p))
        print(f"{name}: {len(m['slices'])} slices → {p}", flush=True)
    print(f"scrolls: {len(rows)}")


if __name__ == "__main__":
    main()
