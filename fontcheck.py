# -*- coding: utf-8 -*-
"""Smoke test: can we set Chinese type with the copied Noto Sans SC faces?"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "assets", "fonts")
W, H = 1280, 720

faces = [
    ("NotoSansSC-Bold.otf", "切尔诺贝利 4 号机组 石墨慢化沸水堆"),
    ("NotoSansSC-Medium.otf", "正空泡系数 控制棒石墨端头 紧急停堆 AZ-5"),
    ("NotoSansSC-Regular.otf", "功率 200 MWt · 氧当量 8 根 · 01:23:40"),
    ("JBMono500.woff", "RBMK-1000  +4.5 beta  01:23:40.00"),
    ("JBMono500.woff", "中文 in mono -> expect tofu"),
]

im = Image.new("RGB", (W, H), (8, 12, 17))
d = ImageDraw.Draw(im)
y = 40
for name, s in faces:
    f = ImageFont.truetype(os.path.join(FD, name), 44)
    d.text((40, y), name, font=ImageFont.truetype(os.path.join(FD, "JBMono500.woff"), 16),
           fill=(255, 176, 32))
    d.text((40, y + 22), s, font=f, fill=(232, 240, 246))
    print("%-24s w=%7.1f  %s" % (name, f.getlength(s), s))
    y += 108

im.save(os.path.join(HERE, "out", "fontcheck.png"))
print("wrote out/fontcheck.png")
