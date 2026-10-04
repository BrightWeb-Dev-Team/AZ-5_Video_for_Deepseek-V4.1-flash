# -*- coding: utf-8 -*-
"""Contact sheets: 24 smoke frames -> one overview sheet + detail sheets."""
import os
import sys

from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def sheet(names, cols, cell, dst, label=True):
    rows = (len(names) + cols - 1) // cols
    cw, ch = cell
    im = Image.new("RGB", (cw * cols, ch * rows), (0, 0, 0))
    for k, n in enumerate(names):
        try:
            f = Image.open(os.path.join(OUT, n)).convert("RGB")
        except OSError:
            continue
        f = f.resize((cw, ch), Image.LANCZOS)
        im.paste(f, ((k % cols) * cw, (k // cols) * ch))
    im.save(dst, quality=90)
    print("wrote", dst, im.size)


if __name__ == "__main__":
    allf = ["smoke_%02d.png" % (i + 1) for i in range(24)]
    sheet(allf, 4, (480, 270), os.path.join(OUT, "sheet_all.jpg"))
    for g in range(4):
        part = allf[g * 6:(g + 1) * 6]
        sheet(part, 2, (960, 540), os.path.join(OUT, "sheet_act%d.jpg" % (g + 1)))
