#!/usr/bin/env python3
"""Осевой срез с размеченными центрами — вид сверху для заявки.

ЗАЧЕМ. Боковой вид показывает, что ось возвращается по высоте, но НЕ показывает
главного: что на одной высоте центров несколько. Это видно только сверху, на
самом срезе, где каждый центр сидит в своём схождении ламин.

  fig_slice.py PHerc0800 18408 [--pad 700] [--width 1500]
"""
import argparse
import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
# Работает поверх рабочего дерева разметки: там лежат срезы-картинки,
# которые в репозиторий не кладутся из-за размера. Путь задаётся UMB_ROOT.
ROOT = os.environ.get("UMB_ROOT", "/home/alexr/vesuvius/umbilici")
COLS = [(120, 255, 140), (110, 180, 255), (255, 220, 60), (255, 130, 230)]


def voxel_um(scroll):
    v = json.load(open(f"{ROOT}/{scroll}/meta.json")).get("volume", "")
    for p in v.split("-"):
        if p.endswith("um"):
            return float(p[:-2])
    raise SystemExit("не читается размер вокселя")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scroll")
    ap.add_argument("z", type=int)
    ap.add_argument("--pad", type=int, default=700, help="поля вокруг точек, воксели L0")
    ap.add_argument("--width", type=int, default=1500)
    ap.add_argument("--full", action="store_true",
                    help="весь срез целиком, без вырезки — чтобы было видно, "
                         "где это место на свитке")
    ap.add_argument("--out", default=os.environ.get("UMB_FIG", f"{ROOT}/fig"))
    a = ap.parse_args()

    meta = json.load(open(f"{ROOT}/{a.scroll}/meta.json"))
    sl = [s for s in meta["slices"] if int(s["z"]) == a.z]
    if not sl:
        raise SystemExit(f"среза z={a.z} нет; есть: "
                         f"{sorted(int(s['z']) for s in meta['slices'])[:40]}")
    sl = sl[0]
    sc = float(sl.get("scale", meta["scale"]))
    um = voxel_um(a.scroll)
    im = Image.open(f"{ROOT}/{a.scroll}/{sl['file']}").convert("RGB")

    # ЦЕНТРЫ ЭТОЙ ВЫСОТЫ: узлы, поставленные рукой, плюс точка обычной оси
    # ПОСТАВЛЕННАЯ РУКОЙ ТОЧКА И НЕТРОНУТОЕ ВХОЖДЕНИЕ — РАЗНЫЕ ВЕЩИ.
    # Узел, взятый из вхождения боковой линии, рождается СТРОГО в плоскости того
    # разреза: у него y (или x) равен плоскости с точностью до вокселя. Человек,
    # ставя его в центр витка, обязательно уводит его с этой плоскости. Значит
    # признак «подвинут» читается прямо из координаты, и спрашивать никого не
    # надо. На z=18408 из четырёх узлов подвинут ровно один — рисунок, где все
    # четыре названы размеченными, был неправдой.
    sd = json.load(open(f"{ROOT}/{a.scroll}/side.json"))
    cuts = [("y", sd.get("y0_L0")), ("x", sd.get("x0_L0"))]
    nodes, raw = [], []
    for f in sorted(glob.glob(f"{ROOT}/results/{a.scroll}_axis_z{a.z}_*_umbilicus.json")):
        if ".bak" in f or ".prev" in f:
            continue
        for c in json.load(open(f)).get("control_points") or []:
            on_cut = any(v is not None and abs(c[k] - v) <= 2 for k, v in cuts)
            (raw if on_cut else nodes).append((c["x"], c["y"]))
    axis_pt = None
    mainf = f"{ROOT}/results/{a.scroll}_umbilicus.json"
    if os.path.exists(mainf):
        for c in json.load(open(mainf))["control_points"]:
            if abs(c["z"] - a.z) < 1:
                axis_pt = (c["x"], c["y"])
    # ВЕТВИ ТОЖЕ ЖИВУТ НА ЭТОЙ ВЫСОТЕ. У 0268 центры размечены не поузловыми
    # кривыми, а двумя файлами ветвей, и без них картинка сверху была бы пустой.
    # Берём ТОЛЬКО точные попадания по z: ветвь, у которой на этой высоте точки
    # нет, ничего здесь не утверждает, и выдумывать за неё нельзя.
    branches = []
    for f in sorted(glob.glob(f"{ROOT}/results/{a.scroll}_branch_*_umbilicus.json")):
        if ".bak" in f or ".prev" in f:
            continue
        nm = os.path.basename(f).split("_branch_")[1].split("_umbilicus")[0]
        for c in json.load(open(f)).get("control_points") or []:
            if abs(c["z"] - a.z) < 1:
                branches.append((nm, (c["x"], c["y"])))
    if not nodes and not raw and not axis_pt and not branches:
        raise SystemExit("на этой высоте нет ни узлов, ни точки оси")

    pts = nodes + raw + [p for _, p in branches] + ([axis_pt] if axis_pt else [])
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    if a.full:
        box = (0, 0, im.size[0], im.size[1])
    else:
        box = (max(0, int((min(xs) - a.pad) / sc)), max(0, int((min(ys) - a.pad) / sc)),
               min(im.size[0], int((max(xs) + a.pad) / sc)),
               min(im.size[1], int((max(ys) + a.pad) / sc)))
    im = im.crop(box)
    k = a.width / im.size[0]
    im = im.resize((a.width, int(im.size[1] * k)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                  max(14, a.width // 60))
    except Exception:
        font = ImageFont.load_default()

    def to_px(p):
        return ((p[0] / sc - box[0]) * k, (p[1] / sc - box[1]) * k)

    r = max(10, a.width // 70)
    for i, p in enumerate(sorted(nodes)):
        x, y = to_px(p)
        col = COLS[i % len(COLS)]
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=max(3, a.width // 400))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            d.line([(x + dx * r * 1.7, y + dy * r * 1.7), (x + dx * r * 2.6, y + dy * r * 2.6)],
                   fill=col, width=max(2, a.width // 600))
        d.text((x + r * 1.6, y - r * 2.4), f"centre {i+1}", fill=col, font=font)
    BRCOL = [(110, 190, 255), (120, 255, 150), (255, 220, 60)]   # красный занят осью
    for i, (nm, p) in enumerate(branches):
        x, y = to_px(p)
        col = BRCOL[i % len(BRCOL)]
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=max(3, a.width // 380))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            d.line([(x + dx * r * 1.6, y + dy * r * 1.6), (x + dx * r * 2.5, y + dy * r * 2.5)],
                   fill=col, width=max(2, a.width // 600))
        d.text((x + r * 1.6, y - r * 2.3), f'branch "{nm}"', fill=col, font=font)
    # нетронутые вхождения — блёкло и с честной подписью
    for p in sorted(raw):
        x, y = to_px(p)
        rr = int(r * 0.7)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(150, 150, 150),
                  width=max(2, a.width // 700))
        d.text((x + rr * 1.4, y - rr * 1.8), "crossing, not placed",
               fill=(150, 150, 150), font=font)
    if axis_pt:
        x, y = to_px(axis_pt)
        # КРАСНЫЙ — ТОТ ЖЕ, ЧТО У ОСИ НА БОКОВОМ ВИДЕ. Один и тот же предмет
        # обязан быть одного цвета на всех картинках заявки, иначе читатель
        # тратит внимание на сопоставление вместо содержания.
        d.ellipse([x - r * 0.85, y - r * 0.85, x + r * 0.85, y + r * 0.85],
                  outline=(255, 70, 70), width=max(3, a.width // 380))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            d.line([(x + dx * r * 1.3, y + dy * r * 1.3), (x + dx * r * 2.1, y + dy * r * 2.1)],
                   fill=(255, 70, 70), width=max(2, a.width // 600))
        d.text((x + r * 1.3, y + r * 1.3), "single-valued axis", fill=(255, 70, 70), font=font)

    # линейка 5 мм
    px_per_mm = k / sc / um * 1000
    bar = 5 * px_per_mm
    x0, y0 = int(0.05 * a.width), int(im.size[1] * 0.94)
    d.line([(x0, y0), (x0 + bar, y0)], fill=(255, 255, 255), width=max(3, a.width // 400))
    for xx in (x0, x0 + bar):
        d.line([(xx, y0 - 9), (xx, y0 + 9)], fill=(255, 255, 255), width=2)
    d.text((x0, y0 - max(30, a.width // 45)), "5 mm", fill=(255, 255, 255), font=font)
    d.text((int(0.05 * a.width), int(0.03 * im.size[1])),
           f"{a.scroll} · axial slice z={a.z} · {um} um/voxel · "
           + (f"{len(branches)} branch points · " if branches else "")
           + f"{len(nodes)} hand-placed centres"
           + (f" · {len(raw)} crossings not yet placed" if raw else ""),
           fill=(255, 255, 255), font=font)

    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, f"{a.scroll}_z{a.z}_centres{'_full' if a.full else ''}.png")
    im.save(p)
    print(f"{p}  {im.size[0]}x{im.size[1]}  поставлено рукой {len(nodes)}, нетронутых вхождений {len(raw)}")


if __name__ == "__main__":
    main()
