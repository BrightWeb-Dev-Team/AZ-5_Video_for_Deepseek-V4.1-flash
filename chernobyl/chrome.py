# -*- coding: utf-8 -*-
"""HUD 与收尾。

一支片子的家具：左上角机组标、右上角片名、左下角时间码、右下角场名、
中下 24 点场序指示器（按四幕分组）、最底一条进度条。
场景画内容，这里画框。

`POST` 是逐场后期参数，`finish()` 走一条链：
bloom → 色差 → 调色 → 暗角 → 切点爆闪 → 扫描线 → 颗粒 → 色调映射。
爆闪压在暗角之后 —— 顺序反了四角会发灰、爆闪变成灰雾（gotchas 18）。
"""
from __future__ import annotations

import numpy as np

from mg import fonts as F
from mg.core import corner_brackets

from . import scenes as SC
from . import theme as T

W, H = T.W, T.H
DOT_Y = 648.0
BAR_Y = H - 4.0
ACT = 6                      # 24 场 / 四幕，每幕 6 场


def _tc(t):
    fr = int(round(t * T.FPS))
    return "TC %02d:%02d:%02d" % (fr // (T.FPS * 3600) % 100, fr // T.FPS % 60, fr % T.FPS)


def draw(p, t, scene_i, light=False):
    ink = T.INK if light else T.GREY
    dim = T.SLATE if light else T.GREY_D
    acc = T.ACCENT_DK if light else T.ACCENT

    # --- 左上：机组标（等宽，只放拉丁；中文一律走场景自己的标题）
    p.rect(T.HUD_M, T.HUD_TOP - 5.5, 9, 9, acc, 0.95)
    p.rect(T.HUD_M + 3.0, T.HUD_TOP - 2.5, 3, 3, T.PAPER if light else T.INK, 0.95)
    p.text(T.HUD_M + 17, T.HUD_TOP, f"{T.BRAND} — {T.PRODUCT}", F.mono(T.S_HUD), ink,
           T.TRACK_HUD)

    # --- 右上：片名
    p.text(W - T.HUD_M, T.HUD_TOP, T.REEL_TAG, F.mono(T.S_HUD), ink, T.TRACK_HUD,
           anchor="rs")

    # --- 左下：时间码
    p.text(T.HUD_M, T.HUD_BOT, _tc(t), F.mono(T.S_HUD), ink, T.TRACK_HUD)

    # --- 右下：场名（等宽 → 只能是英文）
    sid, sname, _ = T.SCENES[scene_i]
    wlab = p.text(W - T.HUD_M, T.HUD_BOT, f"SCENE {sid} / {sname}", F.mono(T.S_HUD),
                  ink, T.TRACK_HUD, anchor="rs")
    p.rect(W - T.HUD_M - wlab - 11, T.HUD_BOT - 3.0, 5, 5, acc, 0.9)

    # --- 中下：24 点场序，按四幕分组（1 幕 6 场，组间留空）
    gap, act_gap = 12.0, 9.0
    span = gap * (T.BARS - 1) + act_gap * 3
    x0 = W / 2.0 - span / 2.0
    for i in range(T.BARS):
        cx = x0 + i * gap + (i // ACT) * act_gap
        if i == scene_i:
            p.rect(cx - 5.0, DOT_Y - 1.5, 10.0, 3.0, acc, 1.0, radius=1.5)
        elif i < scene_i:
            p.dot(cx, DOT_Y, 1.9, ink, 0.60)
        else:
            p.dot(cx, DOT_Y, 1.9, dim, 0.50)

    # --- 底行左侧：档案标签（与中下的场序点不冲突）
    p.dot(T.HUD_M + 3.0, DOT_Y, 3.0, acc, 0.85)
    p.text(T.HUD_M + 13, DOT_Y + 3.2, "ARCHIVE 1986-04-26 01:23:40", F.mono(8.5), ink,
           T.TRACK_HUD, alpha=0.85)

    corner_brackets(p, W, H, acc, 26, 15, 0.30 if not light else 0.26)

    # --- 进度条
    p.rect(0, BAR_Y, W, 3.0, dim, 0.30)
    prog = t / T.DUR
    p.rect(0, BAR_Y, W * prog, 3.0, acc, 0.95)
    p.rect(W * prog - 1.5, BAR_Y - 1.0, 3.0, 5.0, T.INK if light else T.WHITE, 0.85)


# --------------------------------------------------------------------------
# 逐场后期
# --------------------------------------------------------------------------
def _post(i):
    """默认：深板记录仪。爆闪中性偏冷，无扫描线（这不是霓虹片）。"""
    q = dict(bloom=(0.66, 0.26), chroma=1.1, vig=0.46, grain=0.0105, scan=0.0,
             flash=0.44, tint=(0.95, 0.99, 1.0), light=False)
    if i == 0:                      # 片头：多留一点辉光
        q.update(bloom=(0.66, 0.28), vig=0.42, flash=0.85, grain=0.0115)
    if i in (2, 3, 5, 6, 7, 8, 9, 10):   # 第一二幕的图表场：安静、干净
        q.update(bloom=(0.70, 0.24), vig=0.42, flash=0.34, grain=0.0095)
    if i == 12:                     # AZ-5：观众要感到那一下
        q.update(bloom=(0.62, 0.28), vig=0.50, flash=0.95, tint=(1.0, 0.86, 0.72))
    if i == 13:                     # 功率尖峰：事故的红，镜头烧起来
        q.update(bloom=(0.58, 0.30), vig=0.54, flash=1.15, chroma=1.6,
                 tint=(1.0, 0.52, 0.34), grain=0.0135)
    if i == 14:                     # 压力管破裂仍然是一张机制图，不要烧成一片砖红
        q.update(bloom=(0.72, 0.24), vig=0.44, flash=0.34, grain=0.0095)
    if i == 15:                     # 蒸汽爆炸
        q.update(bloom=(0.52, 0.32), vig=0.52, flash=1.30, chroma=2.0,
                 tint=(1.0, 0.72, 0.56), grain=0.0150)
    if i == 16:                     # 没有安全壳：回到冷静的比较图
        q.update(bloom=(0.72, 0.24), vig=0.44, flash=0.30, grain=0.0095)
    if i == 17:                     # 石墨火：十天，一直是红的
        q.update(bloom=(0.60, 0.30), vig=0.56, flash=0.55, chroma=1.5,
                 tint=(1.0, 0.66, 0.44), grain=0.0130)
    if i == 18:                     # 闭环：把三条线收成一条
        q.update(bloom=(0.64, 0.28), vig=0.50, flash=0.40)
    if i == 19:                     # 报告纸：整片唯一一次反白
        q.update(bloom=(0.97, 0.20), chroma=0.5, vig=0.14, grain=0.0050,
                 flash=0.10, tint=(1.0, 1.0, 1.0), light=True)
    if i in (20, 21, 22):           # 结论与改造
        q.update(bloom=(0.70, 0.24), vig=0.44, flash=0.34, grain=0.0095)
    if i == 23:                     # 收尾
        q.update(bloom=(0.66, 0.28), vig=0.50, flash=0.42, grain=0.0115)
    return q


POST = {i: _post(i) for i in range(T.BARS)}


def finish(c, t, scene_i):
    q = dict(POST[scene_i])
    q.update(getattr(c, "post_override", None) or {})

    c.bloom(thr=q["bloom"][0], knee=q["bloom"][1])
    c.chroma(q["chroma"])

    if q.get("light"):
        c.rgb = np.clip(c.rgb, 0.0, 1.0)
        c.vignette(q["vig"], 2.0)
    else:
        # 阴影压向冷灰，暖色只留给琥珀 —— 这样「红色」全片只有事故一个有话语权
        c.rgb = c.rgb * np.asarray((1.0, 1.005, 1.02), np.float32).reshape(1, 1, 3)
        c.rgb = c.rgb + np.asarray((0.003, 0.005, 0.010), np.float32).reshape(1, 1, 3)
        l = c.rgb.mean(axis=2, keepdims=True)
        c.rgb = np.clip(l + (c.rgb - l) * 1.05, 0.0, 1.0)
        c.vignette(q["vig"], 1.7)

    # 切点即重音：第 1 拍落在强拍上，爆闪衰减 0.055 s
    fl = q["flash"]
    if fl > 0.004:
        flash = fl * float(np.exp(-max(0.0, t % T.BAR) / 0.055))
        c.add += flash * np.asarray(q["tint"], np.float32).reshape(1, 1, 3)

    if q["scan"]:
        c.scanlines(q["scan"], 3)
    c.grain(q["grain"])
    c.tonemap(0.86 if q.get("light") else 0.80)
    _ = SC  # 场景层拥有 mark 之类的图像零件，chrome 只管矢量家具
    return c
