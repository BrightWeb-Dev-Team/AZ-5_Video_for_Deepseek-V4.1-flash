# -*- coding: utf-8 -*-
"""数据图版词汇表 —— 坐标轴、曲线、柱、表盘、标注、示意图零件。

风格牌（data-infographic）只给了四句招式：柱/线/表盘按拍生长、坐标轴刻度单位、
一个数据点被唯一强调色高亮、数字滚到位就停。这个模块把那四句变成可复用的零件，
24 场里的每一场都只是「同一套零件 + 不同数据」，所以全片看起来是一支片子而不是 24 张图。

三条纪律写进接口里：
  1. 曲线一律走 Plot 映射，画面上任何位置都能反查回数据值；
  2. 完成判定用 ramp()（线性时钟），缓动只作用在运动上 —— 见 gotchas 24 / 46，
     out_expo 饱和在 ~0.93，拿它当「播完了」的门会静默吃掉最后一截；
  3. 每一幅图都必须能挂出处（source_line）和示意图标记（SCHEMATIC）。
"""
from __future__ import annotations

import re

import numpy as np

from mg import anim as A
from mg import fonts as F
from mg.core import clip01, gauss, radial

from . import theme as T

W, H = T.W, T.H
CX, CY = W / 2.0, H / 2.0

# 版心：场标题带 / 绘图区 / 读数行 / 出处行。HUD 在 648（点指示器）和 700（时间码）上。
TOP = 46.0
TITLE_Y = 84.0        # 场标题 cap 中线
SUB_Y = 118.0         # 副标题基线
PLOT_Y0 = 148.0
PLOT_Y1 = 552.0
READ_Y = 584.0        # 读数行基线
SRC_Y = 622.0         # 出处行基线


# --------------------------------------------------------------------------
# 字体：中文走 Noto Sans SC，数字/读数走 JetBrains Mono
# --------------------------------------------------------------------------
_ZH = {400: "NotoSansSC-Regular.otf", 500: "NotoSansSC-Medium.otf",
       700: "NotoSansSC-Bold.otf"}
_CJK = re.compile(r"[\u2e80-\u9fff\uff00-\uffef\u3000-\u303f]")


def has_cjk(s):
    return bool(_CJK.search(s or ""))


def zh(size, weight=400):
    return F.font(_ZH[min(_ZH, key=lambda k: abs(k - weight))], size)


def zm(size, weight=500):
    return F.mono(size, weight)


def tf(s, size, weight=500):
    """按内容挑字体：含中文就必须走 Noto（内置等宽字面没有 CJK，会渲成豆腐块）。

    等宽只留给纯数字/拉丁读数 —— 那才是这张牌的「刻度与读数」语气。
    """
    return zh(size, weight) if has_cjk(s) else zm(size, weight)


# --------------------------------------------------------------------------
# 时钟与缓动
# --------------------------------------------------------------------------
def ramp(t, t0=0.0, dur=0.4):
    """线性 0→1 完成钟。凡是要问「这段画完了没有」，问它，不要问缓动函数。"""
    return float(np.clip((t - t0) / max(1e-6, dur), 0.0, 1.0))


def grow(t, t0=0.0, dur=0.34, k=5.6):
    """柱/线的生长缓动：收尾要硬，落位就停。"""
    return A.out_expo(clip01((t - t0) / dur), k)


def roll(t, t0, dur, target, nd=0):
    """数字滚动到 target 后停住（线性时钟 + 缓出），返回 float。

    刻意不复用 out_expo 当完成门：这里 dur 末端的值就是 target 本身。
    """
    u = ramp(t, t0, dur)
    v = target * (1.0 - (1.0 - u) ** 3)
    return round(v, nd) if nd else v


def settle(t, t0, dur=0.22):
    """落位带一点过冲，用于大字/大数字（压印感）。"""
    return A.out_back(clip01((t - t0) / dur), 1.7)


# --------------------------------------------------------------------------
# 底板
# --------------------------------------------------------------------------
def plate(c, cy=None, tint=(0.014, 0.020, 0.028), rx=760.0, ry=250.0):
    """暗场底板上的一条环境光带：纯黑底会做出廉价感（design-grammar 第三节）。"""
    c.add += (np.asarray(tint, np.float32).reshape(1, 1, 3)
              * gauss(W, H, CX, CY if cy is None else cy, rx, ry)[..., None])


def hair_grid(p, x0=0.0, y0=TOP, x1=W, y1=SRC_Y + 6, cols=12, rows=6,
              color=None, alpha=0.055, major=0):
    """极淡的底纹网格。major>0 时每 major 条加重一档。

    图元数量就是一帧的成本（performance.md 第三节），所以底纹只给 12×6 ——
    它在 alpha 0.05 上本来也只是一层气，加密度只是把每一帧都画贵。
    """
    col = T.RULE if color is None else color
    for i in range(1, cols):
        a = alpha * (1.9 if major and i % major == 0 else 1.0)
        x = x0 + (x1 - x0) * i / cols
        p.line([(x, y0), (x, y1)], col, 0.7, a)
    for j in range(1, rows):
        a = alpha * (1.9 if major and j % major == 0 else 1.0)
        y = y0 + (y1 - y0) * j / rows
        p.line([(x0, y), (x1, y)], col, 0.7, a)


# --------------------------------------------------------------------------
# 数据 → 画面
# --------------------------------------------------------------------------
class Plot:
    """一块绘图区。所有曲线/柱/标记都经它映射，画面坐标随时能反查数据值。"""

    def __init__(self, x0, y0, x1, y1, xlo, xhi, ylo, yhi, logy=False):
        self.x0, self.y0, self.x1, self.y1 = float(x0), float(y0), float(x1), float(y1)
        self.xlo, self.xhi, self.ylo, self.yhi = xlo, xhi, ylo, yhi
        self.logy = logy

    def sx(self, v):
        d = self.xhi - self.xlo
        u = (float(v) - self.xlo) / d if abs(d) > 1e-9 else 0.0
        return self.x0 + (self.x1 - self.x0) * u

    def sy(self, v):
        lo, hi, v = self.ylo, self.yhi, float(v)
        if self.logy:
            v = max(v, 1e-3)
            lo, hi = max(lo, 1e-3), max(hi, 1e-3)
            d = np.log10(hi) - np.log10(lo)
            u = (np.log10(v) - np.log10(lo)) / d if abs(d) > 1e-9 else 0.0
        else:
            # 轴可以反向（深度向下时 ylo > yhi），所以分母取带符号的差，
            # 不能写成 max(1e-9, hi-lo) —— 那会把 -7 变成 1e-9，坐标直接炸掉。
            d = hi - lo
            u = (v - lo) / d if abs(d) > 1e-9 else 0.0
        return self.y1 - (self.y1 - self.y0) * u

    def pt(self, xv, yv):
        return (self.sx(xv), self.sy(yv))

    def curve(self, xs, ys):
        return [(self.sx(x), self.sy(y)) for x, y in zip(xs, ys)]

    def box(self):
        return (self.x0, self.y0, self.x1, self.y1)


def frame(p, pl, xlab=None, ylab=None, xticks=None, yticks=None, grid=True,
          color=None, alpha=0.9, tick_len=4.0, lab_size=None, tick_fmt="{}",
          ylab_size=None, xtick_labels=None, ytick_labels=None):
    """坐标轴：基线 + 刻度 + 刻度值 + 单位标注。grid 画极淡的横网格。"""
    col = T.RULE_HI if color is None else color
    ls = lab_size or T.S_TAG
    if grid:
        for v in (yticks or []):
            y = pl.sy(v)
            p.line([(pl.x0, y), (pl.x1, y)], T.RULE, 0.7, 0.36 * alpha)
    p.line([(pl.x0, pl.y1), (pl.x1, pl.y1)], col, 1.1, 0.95 * alpha)
    p.line([(pl.x0, pl.y0), (pl.x0, pl.y1)], col, 1.1, 0.95 * alpha)
    for i, v in enumerate(xticks or []):
        x = pl.sx(v)
        p.line([(x, pl.y1), (x, pl.y1 + tick_len)], col, 1.0, 0.8 * alpha)
        lab = xtick_labels[i] if xtick_labels else tick_fmt.format(v)
        p.text(x, pl.y1 + tick_len + 12, lab, tf(lab, ls), T.GREY, 1.2, "ms",
               0.85 * alpha)
    for i, v in enumerate(yticks or []):
        y = pl.sy(v)
        p.line([(pl.x0 - tick_len, y), (pl.x0, y)], col, 1.0, 0.8 * alpha)
        lab = ytick_labels[i] if ytick_labels else tick_fmt.format(v)
        p.text(pl.x0 - tick_len - 6, y + 3.2, lab, tf(lab, ylab_size or ls),
               T.GREY, 0.8, "rs", 0.85 * alpha)
    if xlab:
        p.text((pl.x0 + pl.x1) / 2.0, pl.y1 + 42, xlab, zh(T.S_NOTE), T.GREY, 0.6, "ms", 0.8)
    if ylab:
        p.text(pl.x0 - 46, pl.y0 - 12, ylab, zh(T.S_NOTE), T.GREY, 0.6, "ls", 0.8)


def series(p, pl, xs, ys, color, width=1.8, alpha=1.0, upto=1.0, dash=False,
           glow=False):
    """折线。upto 是沿 x 的揭示比例（0..1），用 ramp() 驱动，不要用缓动。"""
    n = len(xs)
    k = int(round(clip01(upto) * (n - 1)))
    if k < 1:
        return
    pts = pl.curve(xs[:k + 1], ys[:k + 1])
    if dash:
        dash_line(p, pts, color, width, alpha)
        return
    if glow:
        p.path(pts, color, width * 3.4, alpha * 0.16)
    p.path(pts, color, width, alpha)


def area(p, pl, xs, ys, color, alpha=0.16, upto=1.0, base=None):
    """曲线下的填充（用多边形近似）。"""
    n = len(xs)
    k = int(round(clip01(upto) * (n - 1)))
    if k < 1:
        return
    b = pl.y1 if base is None else pl.sy(base)
    pts = pl.curve(xs[:k + 1], ys[:k + 1])
    p.poly(pts + [(pts[-1][0], b), (pts[0][0], b)], color, alpha)


def vbar(p, pl, xv, yv, color, w=26.0, alpha=1.0, base=None):
    """一根从基线长上来的柱。"""
    y = pl.sy(yv)
    b = pl.y1 if base is None else pl.sy(base)
    p.rect(pl.sx(xv) - w / 2.0, min(y, b), w, abs(b - y), color, alpha)


def hbar(p, x, y, w, h, frac, color, alpha=1.0, track=True):
    """横条：track 画底槽，frac 画已实现部分。"""
    if track:
        p.rect(x, y, w, h, T.SLATE, 0.7 * alpha)
    f = clip01(frac)
    if f > 0.002:
        p.rect(x, y, max(1.0, w * f), h, color, alpha)


def dash_line(p, pts, color, width=1.2, alpha=1.0, dash=7.0, gap=5.0):
    """虚线折线：按弧长切段。"""
    seg = []
    carry = 0.0
    on = True
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        d = float(np.hypot(x1 - x0, y1 - y0))
        if d < 1e-6:
            continue
        ux, uy = (x1 - x0) / d, (y1 - y0) / d
        s = 0.0
        while s < d:
            step = (dash if on else gap) - carry
            e = min(d, s + step)
            if on:
                seg.append(((x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)))
            carry += e - s
            if carry >= (dash if on else gap) - 1e-6:
                on = not on
                carry = 0.0
            s = e
    for a, b in seg:
        p.line([a, b], color, width, alpha)


def hline(p, pl, yv, color, label=None, alpha=0.9, width=1.0, dash=True, side="l"):
    """限值线 / 参考线。"""
    y = pl.sy(yv)
    if dash:
        dash_line(p, [(pl.x0, y), (pl.x1, y)], color, width, alpha, 8.0, 5.0)
    else:
        p.line([(pl.x0, y), (pl.x1, y)], color, width, alpha)
    if label:
        x = pl.x0 + 8 if side == "l" else pl.x1 - 8
        p.text(x, y - 8, label, zh(T.S_NOTE), color, 0.5,
               "ls" if side == "l" else "rs", alpha)


def marker(p, pl, xv, yv, color, label=None, sub=None, side="r", r=4.4,
           ring=True, alpha=1.0, up=22.0):
    """唯一被强调的那个数据点：十字准星 + 引线 + 标签。"""
    x, y = pl.pt(xv, yv)
    if ring:
        p.ellipse(x, y, r * 2.3, r * 2.3, color, 0.30 * alpha, width=1.2)
    p.dot(x, y, r, color, alpha)
    if label:
        dx = 34 if side == "r" else -34
        ex = x + dx
        ey = y - up
        p.line([(x, y - r - 3), (x, ey), (ex, ey)], color, 1.0, 0.75 * alpha)
        p.text(ex + (5 if side == "r" else -5), ey - 5, label, zh(T.S_NOTE + 1.5),
               color, 0.6, "ls" if side == "r" else "rs", alpha)
        if sub:
            p.text(ex + (5 if side == "r" else -5), ey + 15, sub, tf(sub, T.S_TAG),
                   T.GREY, 1.2, "ls" if side == "r" else "rs", 0.9 * alpha)


def bracket(p, x0, y0, x1, y1, color, alpha=0.5, ln=11.0, width=1.0):
    """四角括号：把一块图框成「仪表读数」。"""
    for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1),
                           (x1, y1, -1, -1)):
        p.line([(cx, cy), (cx + sx * ln, cy)], color, width, alpha)
        p.line([(cx, cy), (cx, cy + sy * ln)], color, width, alpha)


# --------------------------------------------------------------------------
# 版式零件
# --------------------------------------------------------------------------
def kicker(p, x, y, s, color=None, alpha=0.9, size=None):
    """等宽小标签（拉丁）—— 永远用 JBMono，别往里面塞中文。"""
    p.text(x, y, s, zm(size or T.S_TAG), T.ACCENT if color is None else color,
           T.TRACK_HUD, "ls", alpha)


def title(p, cn, num=None, sub=None, alpha=1.0):
    """场标题：左上角等宽编号 + 中文大标题 + 中文副标。"""
    x = T.M
    p.text(x, TITLE_Y, cn, zh(T.S_H1, 700), T.WHITE, T.TRACK_H1, "lm", alpha)
    if num:
        w = F.measure(zh(T.S_H1, 700), cn, T.TRACK_H1)
        p.text(x + w + 18, TITLE_Y + 10, num, zm(17), T.ACCENT, 1.6, "lm", alpha)
    if sub:
        p.text(x, SUB_Y, sub, zh(T.S_BODY), T.GREY, T.TRACK_BODY, "ls", 0.92 * alpha)


def source_line(p, s, alpha=0.85, color=None):
    p.text(T.M, SRC_Y, s, zm(9.0, 400), T.GREY_D if color is None else color, 1.1, "ls",
           alpha)


def note(p, x, y, s, color=None, alpha=0.9, anchor="ls", size=None):
    return p.text(x, y, s, zh(size or T.S_NOTE), T.GREY if color is None else color,
                  0.5, anchor, alpha)


def readout(p, x, y, label, value, unit="", color=None, anchor="ls", vsize=None,
            alpha=1.0, gap=0.0):
    """一行读数：中文小标签在上，读数在下。返回数值右边界。

    数值与单位按内容选字体（tf）：纯数字走等宽，含中文走 Noto。
    """
    col = T.ACCENT if color is None else color
    p.text(x, y, label, zh(T.S_READ), T.GREY, 0.6, "ls", 0.9 * alpha)
    fv = tf(str(value), vsize or 17)
    w = p.text(x, y + 24, str(value), fv, col, 1.0, "ls", alpha)
    if unit:
        p.text(x + w + 5, y + 24, unit, tf(unit, 9.5, 400), T.GREY, 1.0, "ls", 0.85 * alpha)
    return x + w


def big_num(p, x, y, s, unit=None, color=None, size=None, anchor="mm", alpha=1.0,
            sub=None):
    """大数字。数字是这张牌的主角，unit 用小一号等宽跟在右下。"""
    col = T.ACCENT if color is None else color
    w = p.text(x, y, s, zm(size or T.S_NUM_BIG), col, -2.0, anchor, alpha)
    if unit:
        self_w = T.ACCENT_LT
        p.text(x + (w / 2.0 if anchor[0] == "m" else 0) + 8, y + 26, unit,
               zm(15, 400), self_w, 1.4, "ls", 0.95 * alpha)
    if sub:
        p.text(x, y + 42 if anchor[1] == "m" else y + 24, sub, zh(T.S_NOTE), T.GREY,
               0.6, "ms" if anchor[0] == "m" else "ls", 0.9 * alpha)
    return w


def swatch_row(p, x, y, items, gap=0.0, size=11.0, alpha=1.0):
    """图例：色块 + 等宽文字。items = [(颜色, 文字), ...]"""
    cx = x
    for col, s in items:
        p.rect(cx, y - 8, 9, 9, col, 0.95 * alpha, radius=1.5)
        w = p.text(cx + 15, y, s, zh(size), T.GREY, 0.5, "ls", 0.9 * alpha)
        cx += 15 + w + 22 + gap
    return cx


def check_row(p, x, y, w, s, state, prog, sub=None, alpha=1.0):
    """清单行：state = 'ok' | 'bad' | 'warn'。逐行按拍揭示。"""
    a = clip01(prog) * alpha
    if a <= 0.01:
        return
    col = {"ok": T.ACCENT, "bad": T.DANGER, "warn": T.ACCENT_LT}[state]
    p.line([(x, y + 6), (x + w * a, y + 6)], T.RULE, 1.0, 0.5)
    p.text(x, y, s, zh(T.S_BODY + 1.0), T.WHITE, 0.7, "ls", 0.94 * a)
    if a > 0.55:
        b = ramp(a, 0.55, 0.45)
        if state == "ok":
            p.line([(x + w - 22, y - 1), (x + w - 15, y + 5)], col, 2.1, b)
            p.line([(x + w - 15, y + 5), (x + w - 4, y - 8)], col, 2.1, b)
        else:
            p.line([(x + w - 20, y - 7), (x + w - 5, y + 5)], col, 2.1, b)
            p.line([(x + w - 5, y - 7), (x + w - 20, y + 5)], col, 2.1, b)
        if sub:
            p.text(x + w + 14, y, sub, tf(sub, T.S_TAG), col, 1.2, "ls", 0.9 * b)


# --------------------------------------------------------------------------
# 示意图零件（画核岛剖面用；一律配 SCHEMATIC 标注）
# --------------------------------------------------------------------------
def dot_matrix(p, x0, y0, x1, y1, cols, rows, color, r=1.7, alpha=0.55,
               highlight=None, hi_color=None):
    """点阵：石墨砌体 / 压力管孔道平面图。一批点一次画完（p.dots 是单图元）。"""
    pts = []
    for j in range(rows):
        for i in range(cols):
            pts.append((x0 + (x1 - x0) * (i + 0.5) / cols,
                        y0 + (y1 - y0) * (j + 0.5) / rows))
    p.dots(pts, r, color, alpha)
    if highlight:
        for i, j in highlight:
            p.dot(x0 + (x1 - x0) * (i + 0.5) / cols,
                  y0 + (y1 - y0) * (j + 0.5) / rows, r * 2.3,
                  hi_color or T.ACCENT, 1.0)
    return pts


def tube(p, x, y0, y1, r, wall, color, alpha=1.0, inner=None, inner_alpha=0.5):
    """一根压力管的正视剖面（两条壁 + 内腔）。"""
    p.line([(x - r, y0), (x - r, y1)], color, wall, alpha)
    p.line([(x + r, y0), (x + r, y1)], color, wall, alpha)
    if inner:
        p.line([(x, y0), (x, y1)], inner, 1.2, inner_alpha)


def bubbles(p, xs, ys, rs, color, alpha=0.7):
    """蒸汽泡：一批圆点。"""
    p.dots(list(zip(xs, ys)), 0.0, color, 0.0)   # noop，保持接口一致性
    for x, y, r in zip(xs, ys, rs):
        p.ellipse(x, y, r, r, color, alpha, width=1.2)


def arrow(p, x0, y0, x1, y1, color, width=1.6, alpha=1.0, head=7.0):
    p.line([(x0, y0), (x1, y1)], color, width, alpha)
    d = np.hypot(x1 - x0, y1 - y0)
    if d < 1e-6:
        return
    ux, uy = (x1 - x0) / d, (y1 - y0) / d
    px, py = -uy, ux
    for s in (1, -1):
        p.line([(x1, y1), (x1 - ux * head + px * head * 0.5 * s,
                           y1 - uy * head + py * head * 0.5 * s)], color, width, alpha)


def arc_arrow(p, cx, cy, r, a0, a1, color, width=1.8, alpha=1.0, head=7.0):
    """反馈环用的弧形箭头。角度是度，顺时针为正。"""
    p.arc(cx, cy, r, r, a0, a1, color, width, alpha)
    a = np.radians(a1)
    ex, ey = cx + r * np.cos(a), cy + r * np.sin(a)
    ta = np.radians(a1 + 8)
    tx, ty = cx + r * np.cos(ta), cy + r * np.sin(ta)
    d = np.hypot(tx - ex, ty - ey)
    if d < 1e-6:
        return
    ux, uy = (tx - ex) / d, (ty - ey) / d
    px, py = -uy, ux
    for s in (1, -1):
        p.line([(ex, ey), (ex - ux * head + px * head * 0.5 * s,
                           ey - uy * head + py * head * 0.5 * s)], color, width, alpha)


def dim(p, x0, x1, y, color, label, alpha=0.85, tick=6.0, size=None):
    """尺寸标注线：两端带竖挡 + 居中标签（工程图语言）。"""
    p.line([(x0, y), (x1, y)], color, 1.0, alpha)
    p.line([(x0, y - tick), (x0, y + tick)], color, 1.0, alpha)
    p.line([(x1, y - tick), (x1, y + tick)], color, 1.0, alpha)
    if label:
        p.text((x0 + x1) / 2.0, y - 7, label, tf(label, size or T.S_TAG), color, 1.2,
               "ms", alpha)


# --------------------------------------------------------------------------
# 表盘
# --------------------------------------------------------------------------
def dial(p, cx, cy, r, v, color, label=None, alpha=1.0, w=5.0, unit=None,
         value=None, sweep=(200.0, 340.0)):
    """指针/弧表盘。sweep 是起止角（度，PIL 约定 0=3 点、顺时针）。"""
    p.ellipse(cx, cy, r, r, T.SLATE, 0.85 * alpha, width=w)
    a0, a1 = sweep
    p.arc(cx, cy, r, r, a0, a0 + (a1 - a0) * clip01(v), color, w, alpha)
    p.dot(cx, cy, 2.6, color, 0.9 * alpha)
    if value:
        p.text(cx, cy - 6, value, zm(19), T.WHITE, -0.6, "mm", alpha)
    if label:
        p.text(cx, cy + r + 17, label, zh(T.S_READ), T.GREY, 0.6, "ms", 0.9 * alpha)
    if unit:
        p.text(cx, cy + 12, unit, zm(8.5, 400), T.GREY, 1.0, "mm", 0.8 * alpha)
