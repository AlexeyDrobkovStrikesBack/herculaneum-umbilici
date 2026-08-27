#!/usr/bin/env python3
"""Рисунки оси для заявки — в правильных пропорциях и читаемой линией.

ЗАЧЕМ ОТДЕЛЬНО ОТ СТРАНИЦЫ. Боковой вид в аннотаторе сжат по высоте: он всегда
720 строк, какой бы ни была высота свитка, и у 0268 это сжатие примерно в 1.7
раза. Плюс ось там нарисована линией в 1.2 пикселя с прозрачностью — для работы
удобно, для картинки в заявку нечитаемо. Здесь пропорции восстанавливаются по
настоящим микронам, линия рисуется толщиной, ветви — разными цветами, и внизу
ставится масштабная линейка, чтобы читатель мерил, а не верил.

  fig_axis.py PHerc0268 [xz|yz|оба] [--out ПАПКА]
"""
import argparse
import glob
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
# Работает поверх рабочего дерева разметки: там лежат срезы-картинки,
# которые в репозиторий не кладутся из-за размера. Путь задаётся UMB_ROOT.
ROOT = os.environ.get("UMB_ROOT", "/home/alexr/vesuvius/umbilici")
COL_MAIN = (255, 220, 60)          # обычная ось — жёлтая, чтобы не спорить с ветвями
COL_BR = [(255, 90, 90), (110, 190, 255), (120, 255, 150)]   # ветви
COL_BAR = (255, 255, 255)


def voxel_um(scroll):
    m = json.load(open(f"{ROOT}/{scroll}/meta.json"))
    v = m.get("volume", "")
    for part in v.split("-"):
        if part.endswith("um"):
            try:
                return float(part[:-2])
            except ValueError:
                pass
    raise SystemExit(f"{scroll}: не могу прочитать размер вокселя из имени тома")


def axes_for(scroll):
    """Основная ось и ветви, если они есть."""
    out = []
    main = f"{ROOT}/results/{scroll}_umbilicus.json"
    if os.path.exists(main):
        out.append(("scroll axis (single-valued file)", COL_MAIN,
                    sorted(json.load(open(main))["control_points"], key=lambda c: c["z"])))
    for i, f in enumerate(sorted(glob.glob(f"{ROOT}/results/{scroll}_branch_*_umbilicus.json"))):
        if ".bak" in f or ".prev" in f:
            continue
        name = os.path.basename(f).split("_branch_")[1].split("_umbilicus")[0]
        cp = json.load(open(f)).get("control_points") or []
        if cp:
            out.append((f"branch \"{name}\"", COL_BR[i % len(COL_BR)],
                        sorted(cp, key=lambda c: c["z"])))
    return out


def draw(scroll, axis, outdir, width=1400, zrange=None, curves=True):
    sd = json.load(open(f"{ROOT}/{scroll}/side.json"))
    zr = sd["z_rows_L0"]
    sc = sd["scale"]
    um = voxel_um(scroll)
    key = "x" if axis == "xz" else "y"
    im = Image.open(f"{ROOT}/{scroll}/{sd[axis]['file']}").convert("RGB")
    w0, h0 = im.size

    # ПРОПОРЦИИ. По ширине пиксель = sc вокселей; по высоте строка = свой шаг из
    # z_rows_L0. Растягиваем по высоте так, чтобы миллиметр был миллиметром.
    # ПОЛОСА ВЫСОТ. На весь свиток интересное место занимает пару процентов
    # картинки и не читается вовсе: у 0800 полоса с тремя центрами это 2.6 мм
    # против 179 мм всей высоты. Поэтому можно вырезать полосу по z.
    r0, r1 = 0, len(zr) - 1
    if zrange:
        r0 = min(range(len(zr)), key=lambda i: abs(zr[i] - zrange[0]))
        r1 = min(range(len(zr)), key=lambda i: abs(zr[i] - zrange[1]))
        r0, r1 = min(r0, r1), max(r0, r1)
        im = im.crop((0, r0, w0, r1 + 1))
    zr_use = zr[r0:r1 + 1]

    z_span = (zr_use[-1] - zr_use[0]) * um / 1000.0          # мм
    x_span = w0 * sc * um / 1000.0                           # мм
    k = width / w0
    height = max(60, int(round(width * z_span / x_span)))
    im = im.resize((width, height), Image.LANCZOS)
    d = ImageDraw.Draw(im)

    def row_y(z):
        j = min(range(len(zr_use)), key=lambda i: abs(zr_use[i] - z))
        return (j / max(1, len(zr_use) - 1)) * (height - 1)

    legend = []
    lw = max(3, int(width / 350))
    # ЦВЕТ ОСНОВНОЙ ОСИ ЗАВИСИТ ОТ ТОГО, ЕСТЬ ЛИ ВЕТВИ. Пунктирная жёлтая
    # нужна там, где под ней идут ветви и она обязана их не закрывать (0268).
    # Там, где ветвей нет (0800), она — главный предмет картинки, и тускнеть
    # ей незачем: рисуем сплошной и цветом, который виден на папирусе.
    has_branches = any(n.startswith("branch") for n, _, _ in axes_for(scroll))
    # ЛИНИИ, ПРОВЕДЁННЫЕ НА ЭТОМ ЖЕ РАЗРЕЗЕ. Ход оси, который человек проследил
    # рукой, живёт отдельным файлом-зеркалом и на прежней картинке отсутствовал
    # вовсе — а именно он показывает возврат по высоте.
    if curves:
        pax = "y" if axis == "xz" else "x"
        cut = sd.get("y0_L0") if axis == "xz" else sd.get("x0_L0")
        hidx = 0 if axis == "xz" else 1
        for f in sorted(glob.glob(f"{ROOT}/results/{scroll}_*_{pax}{int(cut)}_*_umbilicus.json")):
            if ".bak" in f or ".prev" in f:
                continue
            cp = json.load(open(f)).get("control_points") or []
            if len(cp) < 2:
                continue
            kind = os.path.basename(f).split("_")[1]
            pts = [((c["x"] if hidx == 0 else c["y"]) / sc * k, row_y(c["z"])) for c in cp]
            d.line(pts, fill=(0, 220, 255), width=lw)
            for x, y in pts:
                r = max(3, int(width / 380))
                d.ellipse([x - r, y - r, x + r, y + r], outline=(0, 220, 255), width=2)
            legend.append((f"traced path ({kind}), in drawing order", (0, 220, 255), len(cp)))
    for name, col, cp in axes_for(scroll):
        pts = [((c[key] / sc) * k, row_y(c["z"])) for c in cp]
        main = name.startswith("scroll axis")
        if main and not has_branches:
            col = (255, 70, 70)
        if len(pts) > 1:
            if main and has_branches:
                # ОСНОВНАЯ — ПУНКТИРОМ И ТОНЬШЕ. Она проходит там же, где ветви,
                # и сплошной линией того же веса просто закрывает их собой.
                for a, b in zip(pts, pts[1:]):
                    n = max(2, int(((b[0]-a[0])**2 + (b[1]-a[1])**2) ** 0.5 / 9))
                    for t in range(0, n, 2):
                        p0 = (a[0] + (b[0]-a[0])*t/n, a[1] + (b[1]-a[1])*t/n)
                        p1 = (a[0] + (b[0]-a[0])*(t+1)/n, a[1] + (b[1]-a[1])*(t+1)/n)
                        d.line([p0, p1], fill=col, width=max(2, lw - 2))
            else:
                d.line(pts, fill=col, width=lw + (1 if main else 0))
        for x, y in pts:
            r = max(3, int(width / 400)) - (1 if (main and has_branches) else 0)
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        legend.append((name, col, len(cp)))

    # МАСШТАБНАЯ ЛИНЕЙКА — 10 мм, чтобы читатель мерил сам
    px_per_mm = width / x_span
    bar = 10 * px_per_mm
    x0, y0 = int(0.04 * width), int(height - 0.05 * height)
    d.line([(x0, y0), (x0 + bar, y0)], fill=COL_BAR, width=max(3, int(width / 400)))
    for xx in (x0, x0 + bar):
        d.line([(xx, y0 - 8), (xx, y0 + 8)], fill=COL_BAR, width=2)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                  max(13, width // 70))
    except Exception:
        font = ImageFont.load_default()
    d.text((x0, y0 - max(26, width // 55)), "10 mm", fill=COL_BAR, font=font)

    # ПОДПИСИ НА ПОДЛОЖКЕ. На светлом папирусе белый текст не читается вовсе,
    # а прозрачная подложка не мешает смотреть на вещество под ней.
    lines = [f"{scroll} · {axis.upper()} section · {um} um/voxel · true aspect"]
    lines += [f"— {name}: {n} points" for name, _, n in legend]
    step = max(20, width // 55)
    pad = int(step * 0.5)
    box_w = int(max(font.getlength(t) for t in lines) + 2 * pad)
    box_h = step * len(lines) + 2 * pad
    x0b, y0b = int(0.03 * width), int(0.02 * height)
    panel = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 170))
    im.paste(Image.alpha_composite(im.crop((x0b, y0b, x0b + box_w, y0b + box_h)).convert("RGBA"),
                                   panel).convert("RGB"), (x0b, y0b))
    d = ImageDraw.Draw(im)
    ty = y0b + pad
    d.text((x0b + pad, ty), lines[0], fill=(255, 255, 255), font=font)
    for (name, col, n), text in zip(legend, lines[1:]):
        ty += step
        d.text((x0b + pad, ty), text, fill=col, font=font)

    os.makedirs(outdir, exist_ok=True)
    tag = f"_z{zrange[0]}-{zrange[1]}" if zrange else ""
    p = os.path.join(outdir, f"{scroll}_{axis}{tag}_axis.png")
    im.save(p)
    print(f"{p}  {width}x{height}  поле {x_span:.0f} x {z_span:.0f} мм")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scroll")
    ap.add_argument("axis", nargs="?", default="both")
    ap.add_argument("--out", default=os.environ.get("UMB_FIG", f"{ROOT}/fig"))
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--zrange", type=int, nargs=2, default=None,
                    help="полоса высот в вокселях L0, например --zrange 16800 19800")
    ap.add_argument("--no-curves", action="store_true")
    a = ap.parse_args()
    axes = ["xz", "yz"] if a.axis == "both" else [a.axis]
    for ax in axes:
        draw(a.scroll, ax, a.out, a.width, a.zrange, not a.no_curves)


if __name__ == "__main__":
    main()
