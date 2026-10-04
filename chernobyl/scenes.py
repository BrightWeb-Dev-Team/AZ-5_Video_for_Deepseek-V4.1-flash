# -*- coding: utf-8 -*-
"""24 场，一场一小节。叙事骨架（设计缺陷 + 物理原理为主干）：

  Ⅰ 堆型（01–06）    RBMK 是什么 / 正空泡系数 / 为什么是正的 / 控制棒端头 / ORM 裕度
  Ⅱ 当晚（07–12）    试验目的 / 氙毒 / 拔棒 / 非正常状态 / 01:23:04 / AZ-5
  Ⅲ 爆炸（13–18）    正反应性注入 / 功率尖峰 / 压力管破裂 / 蒸汽爆炸 / 无安全壳 / 石墨火
  Ⅳ 结论（19–24）    闭环 / INSAG-7 / 三条缺陷 / 事故后改造 / 安全文化 / 收尾

每一场都遵守同一套版式：左上中文标题 → 绘图区 → 读数行 → 左下出处。
颜色语义全片不串：琥珀=实测值，红=越限与事故进程，蓝=负反应性/吸收体，灰=参照。
"""
from __future__ import annotations

import numpy as np

from mg import anim as A
from mg import fonts as F

from . import charts as C
from . import theme as T

W, H = T.W, T.H
CX, CY = W / 2.0, H / 2.0
BEAT = T.BEAT
D = T.D

PLOT_X0, PLOT_X1 = 122.0, 1158.0
PLOT_Y0, PLOT_Y1 = 172.0, 522.0


def plate(c, cy=330, tint=(0.013, 0.019, 0.027), rx=780, ry=250):
    C.plate(c, cy, tint, rx, ry)


def plot(x0=PLOT_X0, x1=PLOT_X1, y0=PLOT_Y0, y1=PLOT_Y1, xlo=0.0, xhi=1.0,
         ylo=0.0, yhi=1.0, logy=False):
    return C.Plot(x0, y0, x1, y1, xlo, xhi, ylo, yhi, logy)


def beats(tl, n):
    """把一小节切成 n 拍，返回第 i 拍的起点秒数。"""
    return [i * (T.BAR / n) for i in range(n)]


# ==========================================================================
# 01 / SLATE —— 片头
# ==========================================================================
class Slate:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 300, (0.020, 0.028, 0.038), 820, 300)

        p = c.pass_()
        C.hair_grid(p, y0=40, y1=C.SRC_Y + 8, cols=16, rows=9, alpha=0.05, major=4)

        e = C.grow(tl, 0.02, 0.5)
        C.kicker(p, T.M, 92, "RBMK-1000  ·  REACTOR 4  ·  PRIPYAT", T.ACCENT, e)

        a1 = C.ramp(tl, 0.10, 0.42)
        p.text(T.M, 156, "切尔诺贝利 4 号机组", C.zh(68, 700), T.WHITE, 1.2, "ls", a1)
        a2 = C.ramp(tl, 0.24, 0.42)
        p.text(T.M, 200, "事故原因技术复盘", C.zh(26, 500), T.ACCENT_LT, 3.0, "ls", a2)

        # 片名的下划线按拍擦出
        w = C.ramp(tl, 0.34, 0.45)
        if w > 0.004:
            p.line([(T.M, 226), (T.M + 520 * w, 226)], T.ACCENT, 2.2, 0.9)

        # --- 右侧：整晚的功率形状，一个字形讲完这支片子
        pl = plot(716, 1160, 250, 520, 0.0, 6.0, 0.0, 1.08)
        xs = np.linspace(0, 6, 240)
        ys = np.where(xs < 4.30, 0.055, 0.055 + 1.0 * np.clip((xs - 4.30) / 0.28, 0, 1) ** 0.8)
        ys = np.where(xs > 4.62, 1.02 + 0.05 * np.sin(xs * 40), ys)
        C.frame(p, pl, yticks=[], xticks=[], grid=False)
        C.series(p, pl, xs, ys, T.TRACE, 1.6, 0.55 * e, upto=C.ramp(tl, 0.30, 0.85))
        C.series(p, pl, xs, ys, T.DANGER, 2.2, 0.95 * e, upto=C.ramp(tl, 0.30, 0.85))
        C.note(p, 716, 240, "中子功率 · 04-25 01:06 → 04-26 01:24", T.GREY, 0.85 * e)
        if C.ramp(tl, 0.86, 0.3) > 0.5:
            p.text(1160, 246, "×100", C.zm(15), T.DANGER, 1.4, "rs", 0.95)

        # --- 大时间码
        b = C.settle(tl, 0.62, 0.30)
        if b > 0.01:
            p.text(T.M, 396, "01:23:40", C.zm(104), T.ACCENT, -3.5, "ls", b)
            p.text(T.M, 436, "AZ-5 按下", C.zh(20, 500), T.WHITE, 1.0, "ls",
                   0.95 * C.ramp(tl, 0.78, 0.3))
            p.text(T.M + 210, 434, "→  7 秒后第一次爆炸", C.zh(15), T.DANGER_BR, 0.8,
                   "ls", C.ramp(tl, 0.96, 0.35))

        # --- 四幕索引
        c.commit()
        p = c.pass_()
        acts = [("Ⅰ", "堆型", 0), ("Ⅱ", "当晚", 6), ("Ⅲ", "爆炸", 12), ("Ⅳ", "结论", 18)]
        x = T.M
        for k, (num, name, i0) in enumerate(acts):
            ea = C.ramp(tl, 1.02 + k * 0.10, 0.32)
            if ea <= 0.01:
                x += 208
                continue
            p.text(x, C.READ_Y, num, C.zm(15), T.ACCENT, 1.0, "ls", ea)
            p.text(x + 20, C.READ_Y, name, C.zh(16, 500), T.WHITE, 1.4, "ls", ea)
            for j in range(6):
                p.rect(x + 68 + j * 20, C.READ_Y - 11, 17, 3.0, T.RULE_HI, 0.55 * ea)
            x += 208
        C.source_line(p, T.SRC_INSAG7 + "   ·   " + T.SRC_RULES)
        c.commit()


# ==========================================================================
# 02 / THE CORE —— RBMK-1000 是什么
# ==========================================================================
class Core:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 340)
        p = c.pass_()
        C.hair_grid(p, alpha=0.045)
        C.title(p, "RBMK-1000 是什么", "02", "石墨慢化 · 轻水冷却兼吸收 · 压力管式沸水堆")

        # --- 左：石墨砌体平面图（1661 根压力管孔道，点阵）
        e = C.grow(tl, 0.10, 0.55)
        bx0, by0, bx1, by1 = 118.0, 210.0, 606.0, 470.0
        C.bracket(p, bx0 - 12, by0 - 12, bx1 + 12, by1 + 12, T.RULE_HI, 0.5 * e)
        cols, rows = 30, 15
        C.dot_matrix(p, bx0, by0, bx1, by1, cols, rows, T.GREY_D, 1.5,
                     0.75 * e, highlight=[(22, 7)], hi_color=T.ACCENT)
        C.note(p, bx0, by1 + 30, "石墨砌体平面：%d 根压力管孔道（点阵示意，非等比例）"
               % D["channels"], T.GREY, 0.95 * e)
        p.text(bx0, by0 - 22, "GRAPHITE STACK · PLAN", C.zm(T.S_TAG), T.GREY_D, 1.3,
               "ls", 0.9 * e)

        # --- 右：单根压力管剖面（放大）
        ex = 716.0
        f = C.grow(tl, 0.30, 0.5)
        if f > 0.01:
            p.line([(ex - 12, by0 - 22), (ex - 12, by1 + 22)], T.RULE_HI, 1.0, 0.5 * f)
            p.line([(ex + 372, by0 - 22), (ex + 372, by1 + 22)], T.RULE_HI, 1.0, 0.5 * f)
            p.text(ex, by0 - 22, "ONE CHANNEL · SECTION", C.zm(T.S_TAG), T.GREY_D, 1.3,
                   "ls", 0.9 * f)
            xc = ex + 62.0
            # 石墨砌体
            p.rect(ex + 22, by0, 100, by1 - by0 - 6, T.SLATE, 0.55 * f)
            C.dot_matrix(p, ex + 26, by0 + 6, ex + 118, by1 - 16, 7, 11, T.GREY_D, 1.3,
                         0.55 * f)
            p.text(ex + 30, by0 + 20, "石墨", C.zh(13), T.GREY, 0.6, "ls", 0.9 * f)
            # 压力管 + 燃料棒束
            C.tube(p, xc, by0 + 8, by1 - 14, 26.0, 2.6, T.ACCENT, 0.95 * f)
            for i in range(6):
                yy = by0 + 26 + i * 34
                p.line([(xc - 15, yy), (xc + 15, yy)], T.INFO_LT, 1.4, 0.55 * f)
            p.text(xc + 42, by0 + 40, "压力管 φ88 mm", C.zh(12.5), T.ACCENT_LT, 0.6,
                   "ls", 0.92 * f)
            p.text(xc + 42, by0 + 62, "燃料束 · 富集度 %.1f%%" % D["enrich_pct"],
                   C.zh(12.5), T.GREY, 0.6, "ls", 0.9 * f)
            p.text(xc + 42, by0 + 96, "轻水：冷却剂 + 吸收剂", C.zh(12.5), T.INFO_LT,
                   0.6, "ls", 0.9 * f)
            # 控制棒孔道
            xr = ex + 356.0
            p.rect(xr - 24, by0, 48, by1 - by0 - 6, T.SLATE, 0.5 * f)
            p.line([(xr - 24, by0 + 150), (xr + 24, by0 + 150)], T.RULE_HI, 1.0, 0.7 * f)
            p.rect(xr - 17, by0 + 8, 34, 96, T.INFO, 0.42 * f)
            p.rect(xr - 17, by0 + 104, 34, 46, T.ACCENT_DK, 0.55 * f)
            p.text(xr, by0 - 8, "控制棒孔道", C.zh(12.5), T.GREY, 0.6, "ms", 0.9 * f)
            p.text(xr, by1 + 14, "碳化硼 + 石墨端头", C.zh(11.5), T.GREY_D, 0.5, "ms",
                   0.85 * f)

        # --- 读数行
        r = C.ramp(tl, 0.72, 0.35)
        C.readout(p, 118, C.READ_Y, "热功率", "3200", "MWt", T.ACCENT, alpha=r)
        C.readout(p, 388, C.READ_Y, "电功率", "1000", "MWe", T.WHITE, alpha=r)
        C.readout(p, 628, C.READ_Y, "压力管", "1661", "根", T.WHITE, alpha=r)
        C.readout(p, 868, C.READ_Y, "石墨砌体", "1700", "t", T.WHITE, alpha=r)
        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 03 / VOID COEFF —— 正空泡系数
# ==========================================================================
class VoidCoeff:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "正空泡系数", "03", "冷却剂汽化，反应性反而上升 —— 整起事故的物理核心")

        pl = plot(150, 1130, 196, 512, 0.0, 100.0, -1.2, 5.2)
        C.frame(p, pl, xlab="蒸汽空泡份额  %", ylab="反应性  β",
                xticks=[0, 25, 50, 75, 100], yticks=[-1, 0, 1, 2, 3, 4, 5])
        C.hline(p, pl, 0.0, T.RULE_HI, None, 0.9, 1.1, False)

        # 参照：压水堆（示意）。采样点多一点，否则 upto 只会在 0/1 之间跳变。
        e_ref = C.ramp(tl, 0.30, 0.55)
        rxs = np.linspace(0.0, 100.0, 24)
        rys = D["void_beta_pwr"] * rxs / 100.0
        C.series(p, pl, rxs, rys, T.TRACE, 1.5, 0.85, upto=e_ref, dash=True)
        p.text(pl.sx(100) - 6, pl.sy(D["void_beta_pwr"]) + 16, "压水堆 PWR ≈ 负（示意）",
               C.zh(12), T.GREY, 0.5, "rs", 0.85 * e_ref)

        # 主体：RBMK 空泡系数
        e = C.ramp(tl, 0.14, 0.70)
        xs = np.linspace(0.0, 100.0, 60)
        ys = D["void_beta"] * xs / 100.0
        C.area(p, pl, xs, ys, T.ACCENT, 0.10, upto=e)
        C.series(p, pl, xs, ys, T.ACCENT, 2.4, 1.0, upto=e)

        m = C.ramp(tl, 0.72, 0.28)
        if m > 0.02:
            C.marker(p, pl, 100.0, D["void_beta"], T.ACCENT, "+4.5 β", "INSAG-7 · 1992",
                     "l", 5.0, True, m)
        C.note(p, 1130, 176, "空泡份额 0 = 全水；100 = 全蒸汽", T.GREY_D, 0.85,
               anchor="rs")

        r = C.ramp(tl, 0.84, 0.3)
        C.readout(p, 118, C.READ_Y, "空泡系数", "+4.5", "β", T.ACCENT, alpha=r)
        C.readout(p, 348, C.READ_Y, "压水堆参照", "≈ 负", "", T.GREY, alpha=r)
        C.readout(p, 588, C.READ_Y, "β 的含义", "缓发中子份额", "", T.WHITE, alpha=r)
        p.text(118, C.READ_Y + 62, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls", 0.8 * r)
        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 04 / WHY POSITIVE —— 为什么是正的
# ==========================================================================
class WhyPositive:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "为什么是正的", "04", "水在 RBMK 里干两件事：带走热量，吸收中子")

        # --- 左：一根通道，水位随空泡下降
        e = C.grow(tl, 0.08, 0.5)
        x0, y0, x1, y1 = 118.0, 210.0, 470.0, 500.0
        C.bracket(p, x0 - 12, y0 - 12, x1 + 12, y1 + 12, T.RULE_HI, 0.5 * e)
        p.text(x0, y0 - 22, "PRESSURE CHANNEL", C.zm(T.S_TAG), T.GREY_D, 1.3, "ls", 0.9 * e)
        xc = (x0 + x1) / 2.0
        C.tube(p, xc, y0, y1, 40.0, 3.0, T.GREY, 0.95 * e)
        # 水柱随空泡份额下降（本体是「空泡把水挤走」）
        void = 0.62 * C.ramp(tl, 0.24, 0.95)
        wy = y1 - (y1 - y0) * (1.0 - void)
        p.rect(xc - 36, wy, 72, y1 - wy, T.INFO, 0.34 * e)
        p.line([(xc - 36, wy), (xc + 36, wy)], T.INFO_LT, 1.8, 0.85 * e)
        p.text(xc, y0 - 6, "蒸汽" if void > 0.1 else "", C.zh(12), T.ACCENT_LT, 0.6,
               "ms", 0.9 * e)
        for i in range(7):
            u = (i * 0.137 + tl * 0.7) % 1.0
            if u < void:
                yy = y1 - (y1 - y0) * u
                rr = 3.2 + 3.4 * ((i * 37) % 7) / 7.0
                p.ellipse(xc + (i % 3 - 1) * 14, yy, rr, rr, T.ACCENT, 0.55 * e,
                          width=1.3)
        p.text(xc, y1 + 26, "空泡份额 %2d%%" % int(round(void * 100)), C.zh(13),
               T.ACCENT, 0.7, "ms", 0.9 * e)
        C.note(p, x0, y0 - 40, "水被挤走 → 吸收中子的东西少了", T.INFO_LT, 0.9 * e)

        # --- 右：中子收支表。水被挤走 → 「吸收」那一格变小 → 净额变大
        pl = plot(716, 1120, 250, 470, 0.0, 2.0, 0.0, 1.0)
        C.frame(p, pl, yticks=[], xticks=[], grid=False)
        parts = [("水吸收", T.INFO, 0.40), ("其他吸收", T.GREY_D, 0.42),
                 ("链式反应净额", T.ACCENT, 0.80)]
        cols = [("有水", [0.55, 0.25, 0.20]), ("全是蒸汽", [0.20, 0.25, 0.55])]
        for k, (lab, seg) in enumerate(cols):
            g = C.grow(tl, 0.34 + k * 0.32, 0.34, 6.0)
            if g <= 0.01:
                continue
            xc = pl.sx(k + 0.5)
            hw = 82.0
            y = pl.y1
            for si, (sname, col, al) in enumerate(parts):
                hh = (pl.y1 - pl.y0) * seg[si] * g
                p.rect(xc - hw, y - hh, hw * 2, hh, col, al * g)
                if si == 2 and g > 0.5:
                    p.text(xc, y - hh - 18, "%d" % int(round(seg[si] * 100)), C.zm(30),
                           col, -1.2, "ms", g)
                y -= hh
            p.text(xc, pl.y1 + 32, lab, C.zh(14, 500), T.WHITE, 0.7, "ms", g)
        C.swatch_row(p, 716, 532, [(T.INFO, "水吸收"), (T.GREY_D, "其他吸收"),
                                   (T.ACCENT, "链式反应净额")], 0, 11.0)
        p.text(716, 232, "中子收支 · 纵向合计为 100（示意）", C.zh(11), T.GREY_D, 0.5,
               "ls", 0.85)
        p.text(716, 566, "水少一点，蓝色那一格就小一点，琥珀那一格就大一点",
               C.zh(12.5), T.GREY, 0.5, "ls", 0.9 * C.ramp(tl, 0.80, 0.3))

        r = C.ramp(tl, 0.86, 0.28)
        p.text(118, C.READ_Y, "水的双重角色 —— 正空泡系数的来源", C.zh(15, 500),
               T.WHITE, 0.8, "ls", 0.95 * r)
        p.text(118, C.READ_Y + 62, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls", 0.8 * r)
        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 05 / ROD DESIGN —— 控制棒的两个缺陷
# ==========================================================================
class RodDesign:
    KEY = "rod"

    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "控制棒的两个缺陷", "05",
                "吸收体下面挂着石墨端头：插棒的头两秒是「把水顶出去」")

        # --- 左：插入前 / 插入后两根通道
        e = C.grow(tl, 0.08, 0.5)
        for k, (lab, depth) in enumerate((("插入前", 0.0), ("插入 1.5 s", 0.34))):
            xc = 210.0 + k * 200.0
            y0, y1 = 254.0, 500.0
            p.text(xc, y0 - 26, lab, C.zh(13), T.GREY, 0.6, "ms", 0.95 * e)
            C.tube(p, xc, y0, y1, 34.0, 2.4, T.GREY_D, 0.95 * e)
            # 通道里的水（吸收体）
            p.rect(xc - 30, y0, 60, y1 - y0, T.INFO, 0.22 * e)
            # 控制棒：吸收体 + 石墨端头，按 depth 下移
            travel = (y1 - y0 - 20) * depth
            ry = y0 - 118 + travel
            p.rect(xc - 22, ry, 44, 70, T.GREY_D, 0.92 * e)          # 碳化硼吸收体
            p.rect(xc - 22, ry + 70, 44, 42, T.ACCENT_DK, 0.88 * e)  # 石墨端头
            p.text(xc + 46, ry + 38, "吸收体", C.zh(11.5), T.GREY, 0.5, "ls", 0.9 * e)
            p.text(xc + 46, ry + 92, "石墨端头", C.zh(11.5), T.ACCENT, 0.5, "ls", 0.9 * e)
        C.arrow(p, 462, 350, 560, 350, T.ACCENT, 1.6, 0.85 * e)
        p.text(511, 340, "%.0f m" % D["rod_travel_m"], C.zm(11), T.ACCENT, 1.0, "ms",
               0.9 * e)
        C.note(p, 118, 528, "全行程 %.0f s：头 %.0f s 走的是石墨，不是吸收体"
               % (D["rod_travel_s"], D["tip_effect_s"]), T.ACCENT_LT, 0.9 * e)

        # --- 右：反应性 vs 插入时间
        pl = plot(660, 1156, 236, 470, 0.0, 6.0, -1.9, 0.85)
        C.frame(p, pl, xlab="AZ-5 后时间  s", ylab="反应性  β",
                xticks=[0, 1, 2, 3, 4, 5, 6], yticks=[-1.5, -1.0, -0.5, 0, 0.5])
        C.hline(p, pl, 0.0, T.RULE_HI, None, 0.9, 1.0, False)
        xs = np.linspace(0, 6, 120)
        lowp = 0.44 * np.exp(-((xs - 1.2) / 0.85) ** 2) - 1.45 / (1.0 + np.exp(-(xs - 2.2) * 3.0))
        highp = 0.05 * np.exp(-((xs - 1.2) / 0.85) ** 2) - 1.65 / (1.0 + np.exp(-(xs - 1.9) * 3.0))
        e1 = C.ramp(tl, 0.42, 0.72)
        C.series(p, pl, xs, highp, T.TRACE, 1.5, 0.8, upto=e1, dash=True)
        C.series(p, pl, xs, lowp, T.ACCENT, 2.4, 1.0, upto=e1)
        p.text(pl.sx(5.6), pl.sy(highp[-1]) - 12, "名义功率下（示意）", C.zh(11.5), T.GREY,
               0.5, "rs", 0.85)
        p.text(pl.sx(3.4), pl.sy(0.44) - 14, "低功率 + 裕度不足：净注入", C.zh(11.5),
               T.ACCENT_LT, 0.5, "rs", 0.9)
        m = C.ramp(tl, 0.80, 0.26)
        if m > 0.02:
            C.marker(p, pl, 1.2, 0.44, T.ACCENT, "+0.4 β", "端头效应的峰值（示意）", "r",
                     4.4, True, m)

        r = C.ramp(tl, 0.88, 0.24)
        C.source_line(p, T.SRC_INSAG7)
        p.text(118, C.SRC_Y - 30, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls", 0.85 * r)
        c.commit()


# ==========================================================================
# 06 / ROD MARGIN —— 运行反应性裕度 ORM
# ==========================================================================
class RodMargin:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "运行反应性裕度 ORM", "06",
                "当晚规程的下限、当晚的实测值、事故后提高到的下限 —— 三个数")

        pl = plot(200, 880, 190, 486, 0.0, 3.0, 0.0, 34.0)
        C.frame(p, pl, xticks=[], ylab="当量根数", yticks=[0, 10, 20, 30])
        bars = [("当晚规程下限", D["orm_limit_night"], T.GREY),
                ("当晚实测", D["orm_actual"], T.ACCENT),
                ("事故后提高到", D["orm_after"], T.INFO)]
        for i, (lab, v, col) in enumerate(bars):
            g = C.grow(tl, 0.16 + i * 0.26, 0.32, 6.4)
            if g <= 0.01:
                continue
            xc = pl.sx(i + 0.5)
            top = pl.sy(v * g)
            # 柱是「读数」不是色块：细柱 + 亮顶 + 描边
            p.rect(xc - 26, top, 52, pl.y1 - top, col, 0.26 * g)
            p.line([(xc - 26, top), (xc - 26, pl.y1)], col, 1.0, 0.55 * g)
            p.line([(xc + 26, top), (xc + 26, pl.y1)], col, 1.0, 0.55 * g)
            p.rect(xc - 26, top - 3.2, 52, 3.2, col, 0.95 * g)
            p.text(xc, top - 18, "%d" % v, C.zm(32), col, -1.2, "ms", 0.95 * g)
            p.text(xc, pl.y1 + 30, lab, C.zh(13), T.GREY, 0.6, "ms", 0.92)
            p.text(xc, pl.y1 + 50, "根当量", C.zh(11), T.GREY_D, 0.5, "ms", 0.85)

        # 越限线：当晚适用的下限
        lx = C.ramp(tl, 0.84, 0.3)
        if lx > 0.02:
            y15 = pl.sy(D["orm_limit_night"])
            C.dash_line(p, [(pl.x0, y15), (pl.x1, y15)], T.DANGER, 1.6, 0.85 * lx, 8, 5)
            p.text(pl.x1 - 8, y15 - 9, "当晚下限 %d" % D["orm_limit_night"], C.zh(12),
                   T.DANGER_BR, 0.5, "rs", 0.9 * lx)

        # --- 右上：211 根棒位条带（4×22 采样，图元数才是成本）
        e = C.grow(tl, 0.44, 0.5)
        if e > 0.01:
            sx, sy = 968.0, 216.0
            p.text(sx, sy - 20, "211 根控制棒插深分布（示意）", C.zh(12), T.GREY, 0.6,
                   "ls", 0.9 * e)
            rng = np.random.default_rng(4)
            nrow, ncol = 4, 22
            for k in range(nrow):
                p.rect(sx, sy + k * 46, ncol * 8.4, 34, T.SLATE, 0.35 * e)
                for j in range(ncol):
                    idx = k * ncol + j
                    deep = 0.86 + 0.14 * rng.random() if idx < 20 else \
                        0.18 + 0.50 * rng.random()
                    g = C.grow(tl, 0.5 + k * 0.06, 0.3)
                    p.rect(sx + j * 8.4 + 1.0, sy + k * 46, 6.4, 34 * deep * g,
                           T.INFO if idx < 20 else T.GREY_D, 0.42 * e)
            p.text(sx, sy + nrow * 46 + 16, "深插 20 根（示意）", C.zh(11), T.INFO_LT,
                   0.5, "ls", 0.85 * e)
            p.text(sx + ncol * 8.4, sy + nrow * 46 + 16, "抽出越多，裕度越小",
                   C.zh(11), T.GREY_D, 0.5, "rs", 0.85 * e)

        r = C.ramp(tl, 0.86, 0.26)
        C.readout(p, 118, C.READ_Y - 58, "ORM 实测", "%d" % D["orm_actual"], "根当量",
                  T.ACCENT, alpha=r)
        C.readout(p, 388, C.READ_Y - 58, "当晚下限", "%d" % D["orm_limit_night"],
                  "根当量", T.DANGER_BR, alpha=r)
        p.text(118, C.READ_Y + 6, "ORM 低于下限时，堆芯对「插棒」的反应会反转", C.zh(14),
               T.WHITE, 0.6, "ls", 0.95 * r)
        C.source_line(p, T.SRC_INSAG7 + "   ·   " + T.SRC_RULES)
        c.commit()


# ==========================================================================
# 07 / THE TEST —— 试验目的
# ==========================================================================
class TheTest:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "试验目的", "07", "降功率到 700 MWt：验证汽轮发电机惰转能否撑住 40 秒厂用电")

        # --- 左：厂用电链路
        e = C.grow(tl, 0.08, 0.5)
        bx, by, bw, bh = 118.0, 300.0, 104.0, 72.0
        nodes = [("反应堆", "3200 MWt"), ("汽轮机", "惰转"), ("发电机", "→"), ("厂用电", "40 s")]
        for i, (a, b) in enumerate(nodes):
            g = C.ramp(tl, 0.10 + i * 0.10, 0.32) * e
            if g <= 0.01:
                continue
            x = bx + i * 128.0
            col = T.ACCENT if i == 3 else T.RULE_HI
            p.rect(x, by, bw, bh, T.SLATE, 0.55 * g)
            p.rect(x, by, bw, 2.2, col, 0.95 * g)
            p.text(x + bw / 2.0, by + 32, a, C.zh(15, 500), T.WHITE, 0.6, "ms", g)
            p.text(x + bw / 2.0, by + 55, b, C.zm(9.5), T.GREY, 1.2, "ms", 0.9 * g)
            if i < 3:
                C.arrow(p, x + bw + 4, by + bh / 2.0, x + 122, by + bh / 2.0,
                        T.RULE_HI, 1.4, 0.85 * g, 6.0)

        # --- 右侧：功率台阶
        pl = plot(700, 1156, 214, 470, 0.0, 17.0, 0.0, 3500.0)
        C.frame(p, pl, xlab="4 月 25 日 01:06 → 4 月 26 日 01:23   小时", ylab="热功率 MWt",
                xticks=[0, 4, 8, 12, 17], yticks=[0, 1000, 2000, 3000])
        xs = np.linspace(0, 17, 200)
        ys = 3200.0 - (3200.0 - 700.0) * np.clip(xs / 1.6, 0, 1)
        C.area(p, pl, xs, ys, T.TRACE, 0.10, upto=C.ramp(tl, 0.30, 0.75))
        C.series(p, pl, xs, ys, T.TRACE, 2.0, 0.9, upto=C.ramp(tl, 0.30, 0.75))
        C.hline(p, pl, 700.0, T.ACCENT, "目标 700 MWt", 0.9 * C.ramp(tl, 0.76, 0.3),
                1.3, True, "l")
        C.marker(p, pl, 17.0, 700.0, T.ACCENT, "700", "试验工况", "l", 4.2, True,
                 C.ramp(tl, 0.80, 0.25))
        C.note(p, 700, 196, "STEP DOWN · 3200 → 700 MWt", T.GREY_D, 0.85)

        r = C.ramp(tl, 0.86, 0.26)
        C.readout(p, 118, C.READ_Y, "起始功率", "3200", "MWt", T.WHITE, alpha=r)
        C.readout(p, 368, C.READ_Y, "试验目标", "700", "MWt", T.ACCENT, alpha=r)
        C.readout(p, 618, C.READ_Y, "需要维持", "40", "s", T.WHITE, alpha=r)
        C.source_line(p, T.SRC_RULES)
        c.commit()


# ==========================================================================
# 08 / XENON —— 氙-135 毒化
# ==========================================================================
class Xenon:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "氙-135 毒化", "08", "功率掉下去之后，碘还在变成氙，氙却烧不掉了")

        pl = plot(150, 1130, 200, 486, 0.0, 16.0, 0.0, 1.06)
        C.frame(p, pl, xlab="降功率后 小时", ylab="相对浓度",
                xticks=[0, 4, 8, 12, 16], yticks=[0, 0.5, 1.0])
        lam_i = np.log(2) / D["i135_h"]
        lam_x = np.log(2) / D["xe135_h"]
        xs = np.linspace(0, 16, 240)
        iod = np.exp(-lam_i * xs)
        xe = lam_i / (lam_i - lam_x) * (np.exp(-lam_x * xs) - np.exp(-lam_i * xs))
        xe = xe / xe.max()
        e1 = C.ramp(tl, 0.16, 0.7)
        C.series(p, pl, xs, iod, T.INFO, 1.8, 0.8, upto=e1)
        C.area(p, pl, xs, xe, T.ACCENT, 0.07, upto=C.ramp(tl, 0.26, 0.72))
        C.series(p, pl, xs, xe, T.ACCENT, 2.8, 1.0, upto=C.ramp(tl, 0.26, 0.72))
        p.text(pl.sx(15.6), pl.sy(iod[-1]) - 10, "碘-135  半衰期 %.1f h" % D["i135_h"],
               C.zh(11.5), T.INFO_LT, 0.5, "rs", 0.9 * e1)
        p.text(pl.sx(11.4), pl.sy(1.0) - 14, "氙-135  半衰期 %.1f h" % D["xe135_h"],
               C.zh(11.5), T.ACCENT_LT, 0.5, "rs", 0.95)

        # 峰值位置（二室模型的 11.3 h）
        pk = float(xs[int(np.argmax(xe))])
        m = C.ramp(tl, 0.74, 0.26)
        C.marker(p, pl, pk, 1.0, T.ACCENT, "毒化峰值", "降功率后约 %.0f 小时" % pk, "l",
                 4.2, True, m)
        # 当晚位置
        if C.ramp(tl, 0.80, 0.25) > 0.4:
            p.line([(pl.sx(0.6), pl.y0), (pl.sx(0.6), pl.y1)], T.DANGER, 1.2, 0.7)
            p.text(pl.sx(0.6) + 8, pl.y0 + 18, "当晚 01:23", C.zh(11.5), T.DANGER_BR,
                   0.5, "ls", 0.9)

        r = C.ramp(tl, 0.86, 0.26)
        big = C.roll(tl, 0.86, 0.34, D["p_dropped"])
        C.readout(p, 118, C.READ_Y, "功率掉到", "%d" % int(big), "MWt", T.DANGER_BR,
                  alpha=r)
        C.readout(p, 388, C.READ_Y, "占目标", "4", "%", T.WHITE, alpha=r)
        C.readout(p, 628, C.READ_Y, "中毒机制", "中子毒物", "", T.INFO_LT, alpha=r)
        p.text(118, C.SRC_Y - 30, "二室模型（停堆后理想情况，未计入剩余通量燃耗）· 半衰期取实测值",
               C.zh(10.5), T.GREY_D, 0.4, "ls", 0.85 * r)
        C.source_line(p, T.SRC_NNDC + "   ·   " + T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 09 / ROD WITHDRAWAL —— 拔棒回功率
# ==========================================================================
class Withdrawal:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "把功率拉回来", "09", "唯一的办法是拔出控制棒 —— 裕度就是在这一步被吃掉的")

        # --- 上：功率回升（两个量拆成两块图，叠在同一块里会变成一个看不懂的叉）
        pl = plot(150, 1130, 180, 356, 0.0, 10.0, 0.0, 420.0)
        C.frame(p, pl, ylab="热功率 MWt", xticks=[], yticks=[0, 200, 400])
        xs = np.linspace(0, 10, 160)
        ys = 30.0 + (200.0 - 30.0) * np.clip((xs - 1.2) / 5.0, 0, 1)
        e = C.ramp(tl, 0.16, 0.68)
        C.area(p, pl, xs, ys, T.ACCENT, 0.09, upto=e)
        C.series(p, pl, xs, ys, T.ACCENT, 2.6, 1.0, upto=e)
        C.hline(p, pl, 200.0, T.WHITE, "恢复到 200 MWt", 0.7 * C.ramp(tl, 0.66, 0.3),
                1.0, True, "l")
        p.text(1130, 168, "① 把功率从 30 MWt 拉回 200 MWt", C.zh(12), T.ACCENT_LT, 0.6,
               "rs", 0.9)

        # --- 下：同一时间轴上的 ORM
        plo = plot(150, 1130, 404, 496, 0.0, 10.0, 0.0, 32.0)
        C.frame(p, plo, xlab="4 月 26 日 00:30 → 01:23   分钟", ylab="ORM 当量根数",
                xticks=[0, 2, 4, 6, 8, 10], yticks=[0, 10, 20, 30])
        e2 = C.ramp(tl, 0.44, 0.5)
        oxs = np.linspace(0, 10, 80)
        oys = D["orm_before"] - (D["orm_before"] - D["orm_actual"]) * np.clip(
            (oxs - 1.6) / 5.4, 0, 1)
        C.series(p, plo, oxs, oys, T.TRACE, 1.6, 0.9, upto=e2, dash=True)
        C.hline(p, plo, D["orm_limit_night"], T.DANGER, "下限 %d" % D["orm_limit_night"],
                0.85 * C.ramp(tl, 0.72, 0.28), 1.2, True, "l")
        C.marker(p, plo, 10.0, D["orm_actual"], T.DANGER,
                 "ORM ≈ %d 根当量" % D["orm_actual"], None, "l", 4.4, True,
                 C.ramp(tl, 0.80, 0.24), up=24)
        p.text(1130, 392, "② 同一时间轴上，裕度被吃掉", C.zh(12), T.DANGER_BR, 0.6,
               "rs", 0.9)

        r = C.ramp(tl, 0.86, 0.26)
        C.readout(p, 118, C.READ_Y, "恢复到", "200", "MWt", T.ACCENT, alpha=r)
        C.readout(p, 368, C.READ_Y, "ORM", "26 → 8", "根当量", T.DANGER_BR, alpha=r)
        C.readout(p, 648, C.READ_Y, "抽取的控制棒", "远低于下限", "", T.WHITE, alpha=r)
        C.source_line(p, T.SRC_INSAG7 + "   ·   " + T.SRC_RULES)
        c.commit()


# ==========================================================================
# 10 / ABNORMAL —— 当晚的非正常状态
# ==========================================================================
class Abnormal:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "当晚的非正常状态", "10", "一半是试验方案要求的，一半是运行中的偏离 —— 两者要分开看")

        # --- 左栏：方案主动要求撤掉的保护
        a = C.ramp(tl, 0.10, 0.5)
        x = 118.0
        w = 470.0
        p.text(x, 226, "A · 试验方案主动要求（已批准）", C.zh(14, 500), T.ACCENT_LT, 0.8,
               "ls", a)
        p.line([(x, 236), (x + w, 236)], T.RULE_HI, 1.0, 0.7 * a)
        rowsA = ["应急堆芯冷却系统 ECCS 隔离", "局部自动调节器 LAR 停用", "汽水失衡保护信号封锁"]
        for i, s in enumerate(rowsA):
            C.check_row(p, x, 282 + i * 62, w, s, "warn",
                        C.ramp(tl, 0.20 + i * 0.12, 0.34) * a, "方案要求")
        p.text(x, 486, "→ 这些保护不是被误操作关掉的，", C.zh(13), T.GREY, 0.5, "ls",
               0.9 * a)
        p.text(x, 508, "   是运行规程允许在试验中撤掉的。", C.zh(13), T.GREY, 0.5, "ls",
               0.9 * a)

        # --- 右栏：真正偏离规程的
        b = C.ramp(tl, 0.42, 0.5)
        x2 = 668.0
        w2 = 490.0
        p.text(x2, 226, "B · 运行中偏离规程", C.zh(14, 500), T.DANGER_BR, 0.8, "ls", b)
        p.line([(x2, 236), (x2 + w2, 236)], T.RULE_HI, 1.0, 0.7 * b)
        rowsB = [("ORM ≈ %d 根当量，低于当晚下限 %d" % (D["orm_actual"],
                                                        D["orm_limit_night"]), "超限"),
                 ("主泵 %d 台运行，规程上限 %d 台" % (D["pumps_running"], D["pumps_limit"]),
                  "超限")]
        for i, (s, sub) in enumerate(rowsB):
            C.check_row(p, x2, 282 + i * 62, w2, s, "bad",
                        C.ramp(tl, 0.52 + i * 0.14, 0.34) * b, sub)
        p.text(x2, 486, "→ 保护被撤掉之后，堆芯只剩", C.zh(13), T.GREY, 0.5, "ls",
               0.9 * b)
        p.text(x2, 508, "   「插棒」这一道屏障，而它当时也是反的。", C.zh(13),
               T.DANGER_BR, 0.5, "ls", 0.9 * b)

        C.source_line(p, T.SRC_INSAG7 + "   ·   " + T.SRC_RULES)
        c.commit()


# ==========================================================================
# 11 / 01:23:04 —— 试验开始
# ==========================================================================
class TestStart:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 300)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "01:23:04  试验开始", "11", "8 台主泵运行，蒸汽压力稳定 —— 仪表盘上一切正常")

        # --- 8 个主泵表盘
        for i in range(8):
            g = C.grow(tl, 0.10 + i * 0.045, 0.30, 6.0)
            if g <= 0.01:
                continue
            cx = 128.0 + i * 146.0
            v = 0.72 + 0.18 * np.sin(t * 1.3 + i * 0.9)
            col = T.ACCENT if i < 2 else T.RULE_HI
            C.dial(p, cx, 268, 46.0, v * g, col, "MCP-%d" % (i + 1), g, 4.4, None,
                   "%d%%" % int(round(v * 100)))
        p.text(128.0, 358, "主循环泵 · 8 台同时运行（规程上限 6 台）", C.zh(12.5),
               T.DANGER_BR, 0.6, "ls", C.ramp(tl, 0.46, 0.3))

        # --- 大时间码
        b = C.settle(tl, 0.48, 0.28)
        if b > 0.01:
            p.text(CX, 438, "01:23:04", C.zm(84), T.ACCENT, -2.6, "mm", b)
            p.text(CX, 470, "试验开始 · 惰转试验窗口 40 s", C.zh(17, 500), T.WHITE, 1.2,
                   "ms", 0.95 * C.ramp(tl, 0.62, 0.3))

        # --- 底部：稳定的中子功率
        pl = plot(300, 1000, 500, 556, 0.0, 10.0, 0.0, 1.0)
        C.frame(p, pl, xticks=[], yticks=[], grid=False)
        xs = np.linspace(0, 10, 200)
        ys = 0.42 + 0.012 * np.sin(xs * 3.1) + 0.006 * np.sin(xs * 9.0)
        C.series(p, pl, xs, ys, T.ACCENT_BR, 1.8, 0.9, upto=C.ramp(tl, 0.70, 0.5))
        p.text(300, 492, "中子功率 · 200 MWt · 平", C.zh(11.5), T.GREY, 0.5, "ls",
               0.9 * C.ramp(tl, 0.70, 0.4))

        r = C.ramp(tl, 0.84, 0.26)
        C.readout(p, 118, C.READ_Y, "主泵", "8", "台运行", T.DANGER_BR, alpha=r)
        C.readout(p, 358, C.READ_Y, "中子功率", "200", "MWt", T.ACCENT, alpha=r)
        C.readout(p, 618, C.READ_Y, "蒸汽压力", "≈ 70", "bar 名义", T.WHITE, alpha=r)
        C.source_line(p, T.SRC_RULES)
        c.commit()


# ==========================================================================
# 12 / AZ-5 —— 紧急停堆
# ==========================================================================
class Az5:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 330, (0.030, 0.020, 0.014), 820, 300)
        p = c.pass_()
        C.hair_grid(p, alpha=0.045)
        C.kicker(p, T.M, 96, "SCRAM  ·  ALL 211 RODS INSERT", T.DANGER, 0.9)

        b = C.settle(tl, 0.06, 0.26)
        if b > 0.01:
            p.text(CX, 178, "01:23:40", C.zm(120), T.DANGER, -4.0, "mm", b)
        p.text(CX, 246, "AZ-5 紧急停堆", C.zh(34, 700), T.WHITE, 2.0, "ms",
               0.95 * C.ramp(tl, 0.22, 0.32))

        # --- 控制棒阵下插
        top, bot = 300.0, 536.0
        e = C.ramp(tl, 0.34, 1.45)
        p.rect(230.0, top, 820.0, bot - top, T.SLATE, 0.45)
        dots = [(230.0 + 820.0 * (i + 0.5) / 44.0, top + (bot - top) * (j + 0.5) / 12.0)
                for j in range(12) for i in range(44)]
        p.dots(dots, 1.4, T.GREY_D, 0.5)
        # 棒束：一整条带子按 e 下移
        band = 78.0
        y = top - band + (bot - top + band) * e
        p.rect(236.0, y, 808.0, band, T.ACCENT_DK, 0.55)
        for i in range(20):
            p.line([(236.0 + 808.0 * (i + 0.5) / 20.0, max(y, top)),
                    (236.0 + 808.0 * (i + 0.5) / 20.0, min(y + band, bot))],
                   T.DANGER, 1.4, 0.75)
        C.dim(p, 236.0, 1044.0, bot + 26, T.RULE_HI, "全行程 7.0 m · 18 s", 0.7, 5.0)

        # --- 底部：功率刚刚开始抬头
        pl = plot(300, 1000, 560, 610, 0.0, 4.0, 0.0, 1.0)
        xs = np.linspace(0, 4, 120)
        ys = 0.30 + 0.05 * np.clip((xs - 3.0) / 1.0, 0, 1) ** 0.6
        C.series(p, pl, xs, ys, T.DANGER, 2.4, 0.95, upto=C.ramp(tl, 0.60, 0.9))
        p.text(300, 552, "中子功率", C.zh(11.5), T.GREY, 0.5, "ls", 0.9)

        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 13 / POSITIVE SCRAM —— 石墨端头注入正反应性
# ==========================================================================
class PositiveScram:
    G_LEN = 1.2      # 石墨端头长度 m（示意比例）
    TRAVEL = 7.0     # 通道高度 m

    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "石墨端头注入正反应性", "13",
                "插棒的头两秒，进入堆芯的是石墨 —— 它把水顶了出去")

        # --- 左：时空图（通道深度 × 时间，谁占着这根通道）
        pl = plot(150, 660, 196, 486, 0.0, 6.0, self.TRAVEL, 0.0)
        C.frame(p, pl, xlab="AZ-5 后 秒", ylab="通道深度 m",
                xticks=[0, 1, 2, 3, 4, 5, 6], yticks=[0, 1, 2, 3, 4, 5, 6, 7])
        v = self.TRAVEL / 18.0
        t_abs = (self.TRAVEL - self.G_LEN) / v      # 吸收体开始进入的时刻 3.09 s
        e = C.ramp(tl, 0.16, 0.85)
        x_end = 6.0 * e
        # 水（吸收体）
        wat = [(0.0, 0.0), (x_end, v * x_end), (x_end, self.TRAVEL), (0.0, self.TRAVEL)]
        p.poly(pl.curve([q[0] for q in wat], [q[1] for q in wat]), T.INFO, 0.20)
        # 石墨端头：带子 = {(x,z): max(0, L-1.2) <= z <= L}，L = v·x
        if x_end > t_abs:
            gt = [(0.0, 0.0), (t_abs, 0.0), (x_end, v * x_end - self.G_LEN),
                  (x_end, v * x_end)]
        else:
            gt = [(0.0, 0.0), (x_end, 0.0), (x_end, v * x_end)]
        p.poly(pl.curve([q[0] for q in gt], [q[1] for q in gt]), T.ACCENT, 0.80)
        # 吸收体
        if x_end > t_abs:
            ab = [(t_abs, 0.0), (x_end, 0.0), (x_end, max(0.0, v * x_end - self.G_LEN))]
            p.poly(pl.curve([q[0] for q in ab], [q[1] for q in ab]), T.GREY_D, 0.85)
        C.swatch_row(p, 150, 512, [(T.ACCENT, "石墨端头"), (T.GREY_D, "碳化硼吸收体"),
                                   (T.INFO, "水（中子吸收剂）")], 0, 11.0)
        p.text(660, 180, "通道里「谁占位」随时间变化", C.zh(11.5), T.GREY_D, 0.5, "rs",
               0.9)

        # --- 右：反应性
        pr = plot(730, 1156, 196, 470, 0.0, 6.0, -1.9, 0.75)
        C.frame(p, pr, xlab="AZ-5 后 秒", ylab="反应性 β",
                xticks=[0, 1, 2, 3, 4, 5, 6], yticks=[-1.5, -1.0, -0.5, 0, 0.5])
        C.hline(p, pr, 0.0, T.RULE_HI, None, 0.9, 1.0, False)
        xs = np.linspace(0, 6, 140)
        lowp = 0.44 * np.exp(-((xs - 1.2) / 0.85) ** 2) - 1.45 / (1 + np.exp(-(xs - 2.2) * 3))
        highp = 0.05 * np.exp(-((xs - 1.2) / 0.85) ** 2) - 1.65 / (1 + np.exp(-(xs - 1.9) * 3))
        er = C.ramp(tl, 0.30, 0.62)
        C.series(p, pr, xs, highp, T.TRACE, 1.5, 0.8, upto=er, dash=True)
        C.series(p, pr, xs, lowp, T.ACCENT, 2.4, 1.0, upto=er)
        p.text(pr.sx(5.9), pr.sy(highp[-1]) - 10, "名义功率（示意）", C.zh(11), T.GREY,
               0.5, "rs", 0.85)
        m = C.ramp(tl, 0.76, 0.24)
        C.marker(p, pr, 1.2, 0.44, T.ACCENT, "+0.4 β", "头 2 秒净注入（示意）", "r", 4.2,
                 True, m)

        C.source_line(p, T.SRC_INSAG7)
        p.text(730, C.SRC_Y - 30, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls",
               0.85 * C.ramp(tl, 0.88, 0.2))
        c.commit()


# ==========================================================================
# 14 / POWER EXCURSION —— 功率尖峰
# ==========================================================================
class Excursion:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 330, (0.026, 0.014, 0.010), 780, 260)
        p = c.pass_()
        C.hair_grid(p, alpha=0.05)
        C.title(p, "功率尖峰", "14", "4 秒之内，功率升到额定值的百倍量级")

        pl = plot(170, 1156, 200, 500, 0.0, 6.0, 1e2, 1e6, logy=True)
        C.frame(p, pl, xlab="AZ-5 后 秒", ylab="热功率 MWt",
                xticks=[0, 1, 2, 3, 4, 5, 6],
                yticks=[1e2, 1e3, 1e4, 1e5, 1e6],
                ytick_labels=["100", "1k", "10k", "100k", "1M"],
                ylab_size=T.S_TAG - 0.5)
        C.hline(p, pl, 3200.0, T.RULE_HI, "额定 3200 MWt", 0.85, 1.2, True, "r")
        xs = np.linspace(0, 6, 260)
        ys = 200.0 * 10.0 ** np.clip((xs - 1.0) / 1.15, 0, 4.2)
        # 曲线冲到量程顶端就截断 —— 不是把超出的部分压成一条平线
        ok = np.nonzero(ys <= 1e6)[0]
        top = int(ok[-1]) if len(ok) else len(xs) - 1
        xs, ys = xs[:top + 1], ys[:top + 1]
        e = C.ramp(tl, 0.20, 0.80)
        C.series(p, pl, xs, ys, T.DANGER, 2.8, 1.0, upto=e, glow=True)
        if e > 0.6:
            p.text(pl.sx(xs[-1]) + 9, pl.y0 + 16, "↑ 超出量程", C.zh(12), T.DANGER_BR,
                   0.5, "ls", 0.9 * C.ramp(tl, 0.70, 0.3))
        m = C.ramp(tl, 0.80, 0.24)
        C.marker(p, pl, 3.6, 1.4e5, T.DANGER, "×100 额定", "INSAG-7：约 4 s 内", "l",
                 4.6, True, m, up=26)
        C.note(p, 170, 186, "对数坐标 · 每格一档", T.GREY_D, 0.85)

        b = C.settle(tl, 0.84, 0.24)
        if b > 0.01:
            p.text(170, 556, "×100", C.zm(74), T.DANGER, -2.4, "ls", b)
            p.text(300, 560, "额定功率", C.zh(19, 500), T.DANGER_BR, 1.0, "ls",
                   0.95 * C.ramp(tl, 0.88, 0.24))
            p.text(300, 588, "同一秒里，蒸汽压力已经超出压力管的承受范围", C.zh(13),
                   T.GREY, 0.5, "ls", 0.9 * C.ramp(tl, 0.90, 0.24))
        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 15 / CHANNEL RUPTURE —— 压力管破裂
# ==========================================================================
class Rupture:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "压力管破裂", "15", "燃料碎裂，冷却剂瞬间汽化 —— 空泡把反应性再往上推")

        pl = plot(160, 1156, 210, 486, 0.0, 7.0, 0.0, 104.0)
        C.frame(p, pl, xlab="通道高度（自下而上）m", ylab="空泡份额 %",
                xticks=[0, 1, 2, 3, 4, 5, 6, 7], yticks=[0, 25, 50, 75, 100])
        zs = np.linspace(0, 7, 90)
        stages = [
            ("正常",       2.0 + 5.0 * (zs / 7.0), T.INFO, 1.6),
            ("+1 s",       2.0 + 45.0 * (zs / 7.0) ** 1.5, T.ACCENT_LT, 1.8),
            ("+2 s",       5.0 + 80.0 * (zs / 7.0) ** 0.9, T.ACCENT, 2.2),
            ("+4 s 干涸",  30.0 + 72.0 * (zs / 7.0) ** 0.45, T.DANGER, 2.6),
        ]
        for i, (lab, ys, col, wd) in enumerate(stages):
            e = C.ramp(tl, 0.14 + i * 0.15, 0.40)
            if e <= 0.02:
                continue
            yv = np.clip(ys, 0, 100)
            C.series(p, pl, zs, yv, col, wd, 0.95, upto=e)
            p.text(pl.sx(7.0) + 10, pl.sy(float(yv[-1])), lab, C.zh(11.5), col, 0.5,
                   "ls", 0.92 * e)
        C.hline(p, pl, 100.0, T.DANGER, "全蒸汽：慢化只剩石墨", 0.7, 1.1, True, "l")

        r = C.ramp(tl, 0.80, 0.28)
        C.readout(p, 160, C.READ_Y, "空泡份额", "0 → 100", "%", T.DANGER, alpha=r)
        C.readout(p, 430, C.READ_Y, "后果", "反应性继续上升", "", T.WHITE, alpha=r)
        C.readout(p, 700, C.READ_Y, "此时", "停堆棒仍在插入", "", T.GREY, alpha=r)
        C.source_line(p, T.SRC_INSAG7)
        p.text(160, C.SRC_Y - 30, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls",
               0.85 * r)
        c.commit()


# ==========================================================================
# 16 / STEAM BLAST —— 蒸汽爆炸
# ==========================================================================
class Blast:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 320, (0.030, 0.014, 0.010), 800, 300)
        p = c.pass_()
        C.hair_grid(p, alpha=0.05)
        C.title(p, "蒸汽爆炸", "16", "01:23:47 与 01:23:49 —— 两次爆炸，上部生物屏蔽被掀开")

        # --- 左：厂房剖面
        e = C.grow(tl, 0.10, 0.5)
        x0, y0, x1, y1 = 150.0, 268.0, 560.0, 512.0
        p.rect(x0, y0, x1 - x0, y1 - y0, T.SLATE, 0.42 * e)
        p.path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], T.RULE_HI, 1.2, 0.7 * e,
               closed=True)
        # 堆芯
        p.rect(x0 + 54, y0 + 74, x1 - x0 - 108, y1 - y0 - 118, T.ACCENT_DK, 0.20 * e)
        C.dot_matrix(p, x0 + 62, y0 + 82, x1 - 62, y1 - 52, 12, 8, T.DANGER, 1.3,
                     0.34 * e)
        p.text((x0 + x1) / 2, y0 + 40, "堆芯", C.zh(13), T.GREY, 0.6, "ms", 0.9 * e)
        # 上部生物屏蔽被掀开
        lift = 54.0 * C.ramp(tl, 0.40, 0.85)
        p.rect(x0 + 20, y0 - 20 - lift, x1 - x0 - 40, 15, T.GREY, 0.92 * e)
        p.text((x0 + x1) / 2, y0 - 32 - lift, "上部生物屏蔽 · 2000 t", C.zh(12),
               T.WHITE, 0.6, "ms", 0.95 * e)
        if lift > 6:
            for k in range(4):
                C.arrow(p, x0 + 90 + k * 88, y0 - 4, x0 + 90 + k * 88, y0 - 24 - lift,
                        T.DANGER, 1.6, 0.7, 8.0)
        p.text((x0 + x1) / 2, y1 + 26, "反应堆厂房（剖面示意）", C.zh(11.5), T.GREY_D,
               0.5, "ms", 0.85 * e)

        # --- 右：地震式波形，两次爆炸
        pl = plot(672, 1156, 258, 470, 0.0, 6.0, -1.0, 1.6)
        C.frame(p, pl, xlab="01:23:40 之后 秒", ylab="事件强度（示意）",
                xticks=[0, 1, 2, 3, 4, 5, 6], yticks=[])
        xs = np.linspace(0, 6, 300)
        ys = (2.0 * np.exp(-((xs - 0.4) / 0.10) ** 2) * 0.06
              + 1.35 * np.exp(-((xs - 1.55) / 0.13) ** 2)
              + 1.05 * np.exp(-((xs - 1.95) / 0.16) ** 2)
              - 0.28 * np.exp(-((xs - 1.75) / 0.30) ** 2)
              + 0.22 * np.exp(-np.clip(xs - 1.6, 0, None) / 0.9) * np.sin(xs * 34))
        C.series(p, pl, xs, ys, T.DANGER, 1.9, 0.95, upto=C.ramp(tl, 0.22, 0.8))
        for s, lab in ((1.55, "第一次爆炸"), (1.95, "第二次爆炸")):
            if C.ramp(tl, 0.55 + (s - 1.55) * 0.6, 0.3) > 0.4:
                p.line([(pl.sx(s), pl.sy(1.35)), (pl.sx(s), pl.y0)], T.DANGER_BR, 1.0,
                       0.6)
                p.text(pl.sx(s) + 6, pl.y0 + 16, lab, C.zh(11.5), T.DANGER_BR, 0.5,
                       "ls", 0.9)

        b = C.settle(tl, 0.82, 0.24)
        if b > 0.01:
            p.text(672, 508, "01:23:47", C.zm(26), T.DANGER, -1.2, "ls", b)
            p.text(854, 508, "01:23:49", C.zm(26), T.DANGER, -1.2, "ls",
                   0.95 * C.ramp(tl, 0.86, 0.2))
        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 17 / NO CONTAINMENT —— 为什么没有安全壳
# ==========================================================================
class NoContainment:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "为什么没有安全壳", "17", "RBMK 只有通风厂房与上部生物屏蔽；压水堆有一层全压安全壳")

        # --- 两座剖面对照
        for k, (name, sub, has) in enumerate((("RBMK-1000", "通风厂房 · 上部生物屏蔽", False),
                                               ("压水堆 PWR", "预应力混凝土安全壳 · 钢衬里", True))):
            e = C.grow(tl, 0.10 + k * 0.22, 0.45)
            x0 = 132.0 + k * 340.0
            y0, y1 = 196.0, 340.0
            p.rect(x0, y0, 264, y1 - y0, T.SLATE, 0.42 * e)
            p.path([(x0, y0), (x0 + 264, y0), (x0 + 264, y1), (x0, y1)], T.RULE_HI,
                   1.2, 0.7 * e, closed=True)
            if has:
                p.ellipse(x0 + 132, y1 - 62, 104, 58, T.INFO, 0.85 * e, width=3.0)
                p.text(x0 + 132, y1 - 62, "安全壳", C.zh(13), T.INFO_LT, 0.6, "ms",
                       0.95 * e)
            else:
                p.rect(x0 + 30, y0 + 28, 204, 62, T.ACCENT_DK, 0.26 * e)
                C.dot_matrix(p, x0 + 36, y0 + 34, x0 + 228, y0 + 84, 12, 4, T.RULE_HI,
                             1.2, 0.5 * e)
                for i in range(6):
                    C.arrow(p, x0 + 52 + i * 34, y0 + 18, x0 + 52 + i * 34, y0 - 14,
                            T.DANGER, 1.4, 0.6 * e, 6.0)
            p.text(x0 + 132, 366, name, C.zh(17, 700), T.WHITE, 0.8, "ms", 0.95 * e)
            p.text(x0 + 132, 388, sub, C.zh(11.5), T.GREY, 0.5, "ms", 0.9 * e)

        # --- 三行对照表
        rows = [("事故时的屏障", "通风厂房", "全压安全壳"),
                ("放射性去向", "直接进入大气", "被约束在安全壳内"),
                ("结论", "没有第二道边界", "第二道边界成立")]
        for i, (a, b, cc) in enumerate(rows):
            e = C.ramp(tl, 0.50 + i * 0.12, 0.34)
            if e <= 0.01:
                continue
            y = 470 + i * 40
            p.line([(132, y - 12), (1156, y - 12)], T.RULE, 1.0, 0.55 * e)
            p.text(132, y + 8, a, C.zh(13), T.GREY, 0.5, "ls", 0.95 * e)
            p.text(430, y + 8, b, C.zh(13.5), T.DANGER_BR if i < 2 else T.WHITE, 0.5,
                   "ls", 0.95 * e)
            p.text(790, y + 8, cc, C.zh(13.5), T.INFO_LT if i < 2 else T.WHITE, 0.5,
                   "ls", 0.95 * e)
        p.line([(132, 452), (1156, 452)], T.RULE_HI, 1.0, 0.7)
        p.text(132, 444, "对照项", C.zh(11), T.GREY_D, 0.5, "ls")
        p.text(430, 444, "RBMK-1000", C.zh(11), T.GREY_D, 0.5, "ls")
        p.text(790, 444, "压水堆 PWR", C.zh(11), T.GREY_D, 0.5, "ls")

        C.source_line(p, T.SRC_INSAG7)
        p.text(132, C.SRC_Y - 30, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls", 0.85)
        c.commit()


# ==========================================================================
# 18 / GRAPHITE FIRE —— 石墨火 · 十天
# ==========================================================================
class Fire:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 330, (0.026, 0.013, 0.009), 800, 280)
        p = c.pass_()
        C.hair_grid(p, alpha=0.05)
        C.title(p, "石墨火 · 十天", "18", "4 月 26 日到 5 月 6 日，堆芯石墨持续燃烧，把放射性带进大气")

        pl = plot(170, 1156, 210, 476, 0.0, 12.0, 0.0, 1.10)
        C.frame(p, pl, xlab="事故后 天", ylab="相对释放率（示意）",
                xticks=[0, 2, 4, 6, 8, 10, 12], yticks=[0, 0.5, 1.0])
        xs = np.linspace(0, 12, 240)
        ys = np.clip(1.0 * np.exp(-((xs - 0.35) / 0.55) ** 2)
                     + 0.72 * np.exp(-((xs - 1.8) / 1.5) ** 2)
                     + 0.30 * np.exp(-np.clip(xs - 1.2, 0, None) / 4.2), 0, 1.05)
        e = C.ramp(tl, 0.18, 0.75)
        C.area(p, pl, xs, ys, T.DANGER, 0.12, upto=e)
        C.series(p, pl, xs, ys, T.DANGER, 2.6, 1.0, upto=e, glow=True)
        # 十天窗口
        w = C.ramp(tl, 0.62, 0.35)
        if w > 0.02:
            p.rect(pl.sx(0), pl.y0, (pl.sx(10) - pl.sx(0)) * w, 18, T.DANGER, 0.14)
            p.line([(pl.sx(10), pl.y0), (pl.sx(10), pl.y1)], T.DANGER, 1.4, 0.85 * w)
            C.dim(p, pl.sx(0), pl.sx(10), pl.y1 + 40, T.DANGER,
                  "封顶作业完成前共 10 天", 0.85 * w, 6.0)
        p.text(pl.sx(5), pl.y0 + 14, "石墨火窗口", C.zh(11.5), T.DANGER_BR, 0.5, "ms",
               0.9 * w)

        r = C.ramp(tl, 0.80, 0.26)
        C.readout(p, 170, C.READ_Y, "持续", "10", "天", T.DANGER, alpha=r)
        C.readout(p, 420, C.READ_Y, "释放总活度", D["release_bq"], "Bq (IAEA)", T.WHITE,
                  alpha=r)
        C.readout(p, 760, C.READ_Y, "疏散", "30 km · 13.5 万人", "", T.ACCENT_LT,
                  alpha=r)
        C.source_line(p, T.SRC_INSAG7 + "   ·   " + T.SRC_IAEA)
        p.text(170, C.SRC_Y - 30, T.SCHEMATIC, C.zh(10.5), T.GREY_D, 0.4, "ls", 0.85)
        c.commit()


# ==========================================================================
# 19 / FEEDBACK LOOP —— 闭环
# ==========================================================================
class Loop:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 340, (0.030, 0.016, 0.010), 760, 280)
        p = c.pass_()
        C.hair_grid(p, alpha=0.045)
        C.title(p, "闭环", "19", "空泡 → 反应性 → 功率 → 更多空泡：这条正反馈没有任何一道闸门能切断")

        r = 104.0
        cy = 316.0
        nodes = [(CX, cy - r, "功率 ↑"), (CX + r * 1.72, cy, "冷却剂汽化"),
                 (CX, cy + r, "空泡份额 ↑"), (CX - r * 1.72, cy, "反应性 ↑")]
        for k in range(4):
            a0 = -100.0 + k * 90.0
            arc = C.ramp(tl, 0.16 + k * 0.13, 0.34)
            if arc > 0.02:
                C.arc_arrow(p, CX, cy, r * 0.66, a0, a0 + 74 * arc, T.ACCENT, 2.2, 0.9)
        for i, (x, y, lab) in enumerate(nodes):
            a = C.ramp(tl, 0.14 + i * 0.13, 0.34)
            if a <= 0.01:
                continue
            p.rect(x - 96, y - 24, 192, 48, T.SLATE, 0.72 * a, radius=3)
            p.rect(x - 96, y - 24, 192, 2.4, T.ACCENT, 0.95 * a)
            p.text(x, y + 6, lab, C.zh(19, 700), T.WHITE, 1.0, "ms", a)
        p.text(CX, cy - 8, "正空泡系数", C.zh(16, 700), T.ACCENT, 1.4, "ms",
               0.95 * C.ramp(tl, 0.46, 0.3))
        p.text(CX, cy + 16, "+4.5 β", C.zm(19), T.ACCENT_LT, -1.0, "ms",
               0.95 * C.ramp(tl, 0.56, 0.3))

        # --- 三道本该切断闭环的闸门
        gates = [("安全壳", "不存在"), ("有效停堆", "头 2 秒是反的"),
                 ("保护信号", "被方案封锁")]
        for i, (a, b) in enumerate(gates):
            ea = C.ramp(tl, 0.62 + i * 0.11, 0.30)
            if ea <= 0.01:
                continue
            x = 196.0 + i * 320.0
            p.line([(x, 500), (x + 282, 500)], T.RULE_HI, 1.0, 0.6 * ea)
            p.text(x, 528, a, C.zh(16, 500), T.WHITE, 0.8, "ls", 0.95 * ea)
            p.text(x + 96, 528, b, C.zh(14), T.DANGER, 0.6, "ls", 0.95 * ea)
            p.line([(x + 250, 512), (x + 272, 536)], T.DANGER, 2.2, 0.9 * ea)
            p.line([(x + 272, 512), (x + 250, 536)], T.DANGER, 2.2, 0.9 * ea)
        p.text(196.0, 572, "三道闸门在同一时刻全部失效 —— 这是「同时」，不是「先后」",
               C.zh(13.5), T.GREY, 0.5, "ls", 0.9 * C.ramp(tl, 0.94, 0.24))
        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 20 / INSAG-7 —— 结论（整片唯一一次反白）
# ==========================================================================
class Insag7:
    def render(self, c, tl, t):
        c.clear(T.PAPER)
        p = c.pass_()
        # 纸面：极淡的横格 + 一点不均匀
        for j in range(1, 15):
            y = 60 + j * 46
            p.line([(0, y), (W, y)], T.SLATE, 0.7, 0.10)
        p.rect(0, 0, W, 3.0, T.ACCENT_DK, 0.90)

        C.kicker(p, T.M, 92, "IAEA SAFETY SERIES No. 75-INSAG-7   ·   1992", T.ACCENT_DK,
                 0.95)
        a1 = C.ramp(tl, 0.08, 0.42)
        p.text(T.M, 158, "根因在堆型设计", C.zh(64, 700), T.INK, 1.2, "ls", a1)
        w = C.ramp(tl, 0.30, 0.42)
        if w > 0.004:
            p.line([(T.M, 184), (T.M + 620 * w, 184)], T.ACCENT_DK, 2.4, 0.9)

        # --- 两个年份的口径变化
        box = [(T.M, 236.0, 560.0, 400.0, "1986 · INSAG-1",
                "把事故主要归因于运行人员违反规程", T.GREY_D),
               (668.0, 236.0, 1156.0, 400.0, "1992 · INSAG-7",
                "修正：根因是堆型设计缺陷，运行违规是促成条件", T.ACCENT_DK)]
        for i, (x0, y0, x1, y1, head, body, col) in enumerate(box):
            a = C.ramp(tl, 0.34 + i * 0.16, 0.40)
            if a <= 0.01:
                continue
            p.rect(x0, y0, x1 - x0, y1 - y0, T.CARD, 0.72 * a)
            p.rect(x0, y0, 4.0, y1 - y0, col, 0.95 * a)
            p.text(x0 + 22, y0 + 40, head, C.zm(13), col, 1.4, "ls", a)
            p.text(x0 + 22, y0 + 86, body, C.zh(17, 500), T.INK if i else T.GREY_D,
                   0.7, "ls", a)

        # --- 结论行
        a = C.ramp(tl, 0.66, 0.40)
        p.text(T.M, 470, "「事故的根本原因是反应堆的物理特性与设计，", C.zh(21, 500),
               T.INK, 0.9, "ls", a)
        p.text(T.M, 506, "  使运行人员在一个没有容错余地的系统里做出了致命判断。」",
               C.zh(21, 500), T.INK, 0.9, "ls", a)
        p.text(1156, 470, "释义", C.zh(11), T.GREY_D, 0.5, "rs", 0.9 * a)

        # --- 印章
        b = C.settle(tl, 0.86, 0.26)
        if b > 0.01:
            p.rect(960, 528, 196, 62, T.DANGER, 0.10 * b)
            p.path([(960, 528), (1156, 528), (1156, 590), (960, 590)], T.DANGER, 2.0,
                   0.85 * b, closed=True)
            p.text(1058, 552, "根因", C.zh(19, 700), T.DANGER, 1.2, "ms", b)
            p.text(1058, 578, "DESIGN", C.zm(10), T.DANGER, 1.6, "ms", 0.9 * b)
        C.source_line(p, T.SRC_INSAG7 + "   ·   " + T.SRC_INSAG1, 0.9, T.GREY_D)
        c.commit()


# ==========================================================================
# 21 / DEFECTS —— 三条设计缺陷
# ==========================================================================
class Defects:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "三条设计缺陷", "21", "三条同时成立，事故才成立 —— 任何一条被修掉，形状都不同")

        cols = [
            ("01", "正空泡系数", "+4.5 β", T.ACCENT,
             "功率升高 → 冷却剂汽化 →\n反应性继续升高，没有自限"),
            ("02", "控制棒石墨端头", "头 2 s 正注入", T.DANGER,
             "紧急停堆的第一步是\n把一个强吸收体（水）顶出去"),
            ("03", "无安全壳 · 保护可封锁", "两道边界同时缺位", T.INFO,
             "能量与放射性都没有\n第二道边界可以依靠"),
        ]
        for i, (num, name, tag, col, body) in enumerate(cols):
            e = C.ramp(tl, 0.12 + i * 0.20, 0.42)
            if e <= 0.01:
                continue
            x0 = 118.0 + i * 352.0
            w = 320.0
            p.rect(x0, 208, w, 328, T.SLATE, 0.34 * e)
            p.rect(x0, 208, w, 3.0, col, 0.95 * e)
            p.text(x0 + 24, 254, num, C.zm(24), col, -1.0, "ls", e)
            p.text(x0 + 24, 296, name, C.zh(21, 700), T.WHITE, 0.8, "ls", e)
            p.text(x0 + 24, 326, tag, C.tf(tag, 11), col, 1.3, "ls", 0.95 * e)
            for k, line in enumerate(body.split("\n")):
                p.text(x0 + 24, 372 + k * 26, line, C.zh(13.5), T.GREY, 0.5, "ls",
                       0.95 * e)
            # 每栏一个迷你图，画出这条缺陷的形状
            mp = C.Plot(x0 + 24, 444, x0 + w - 24, 512, 0.0, 1.0, -1.2, 1.2)
            p.line([(mp.x0, mp.y0 + (mp.y1 - mp.y0) / 2), (mp.x1, mp.y0 + (mp.y1 - mp.y0) / 2)],
                   T.RULE, 1.0, 0.5 * e)
            xs = np.linspace(0, 1, 60)
            if i == 0:
                ys = -0.9 + 2.4 * xs
            elif i == 1:
                ys = 0.95 * np.exp(-((xs - 0.28) / 0.22) ** 2) - 1.05 * np.clip(
                    (xs - 0.5) / 0.5, 0, 1)
            else:
                ys = np.zeros_like(xs)
            if i == 2:
                C.dash_line(p, [(mp.x0, mp.y0 + 8), (mp.x1, mp.y0 + 8)], T.DANGER,
                            1.6, 0.85 * e, 7, 5)
                p.text((mp.x0 + mp.x1) / 2, mp.y1 - 8, "第二道边界：缺位", C.zh(11),
                       T.DANGER_BR, 0.5, "ms", 0.9 * e)
            else:
                C.series(p, mp, xs, ys, col, 2.0, 0.95, upto=C.ramp(tl, 0.40 + i * 0.18,
                                                                    0.5) * e)

        C.source_line(p, T.SRC_INSAG7)
        c.commit()


# ==========================================================================
# 22 / FIXES —— 事故后的改造
# ==========================================================================
class Fixes:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "事故后的改造", "22", "同一个堆型在 1986 年之后被改成了另一个安全性态")

        rows = [
            ("燃料富集度 2.0% → 2.4%", "降低正空泡系数的量级"),
            ("ORM 下限提高到 30 根当量并强制执行", "保证插棒时反应性必然下降"),
            ("改进控制棒：取消石墨端头的正注入", "让「停堆」这个动作方向唯一"),
            ("快速停堆全行程缩短（原 18 s）", "缩短正注入的持续时间"),
            ("增设第二套独立停堆系统", "同一功能不再共用一条路径"),
            ("反应堆信息系统 SKALA 改进", "把堆芯状态变成可判读的读数"),
        ]
        for i, (s, sub) in enumerate(rows):
            C.check_row(p, 150, 226 + i * 56, 620, s, "ok",
                        C.ramp(tl, 0.14 + i * 0.115, 0.32), sub)

        # 右侧：停机后的状态条
        p.text(1000, 246, "改造后 RBMK 的关键差异", C.zh(13), T.GREY, 0.6, "ls",
               0.9 * C.ramp(tl, 0.4, 0.3))
        bars = [("空泡系数", 0.30, T.ACCENT, "仍为正，但量级下降"),
                ("停堆方向", 0.95, T.ACCENT, "插入即下降"),
                ("第二道边界", 0.60, T.INFO, "保护系统不可封锁")]
        for i, (lab, v, col, note) in enumerate(bars):
            e = C.grow(tl, 0.58 + i * 0.14, 0.32, 6.0)
            if e <= 0.01:
                continue
            y = 286.0 + i * 74.0
            p.text(1000, y, lab, C.zh(12), T.GREY, 0.5, "ls", 0.9 * e)
            C.hbar(p, 1000, y + 10, 156, 10, v * e, col, 0.9 * e)
            p.text(1000, y + 40, note, C.zh(11), T.GREY_D, 0.5, "ls", 0.85 * e)

        C.source_line(p, T.SRC_IAEA)
        p.text(150, C.SRC_Y - 30, "改造后的 RBMK 与 1986 年的 4 号机组不是同一个安全性态",
               C.zh(11.5), T.ACCENT_LT, 0.5, "ls", 0.9 * C.ramp(tl, 0.92, 0.24))
        c.commit()


# ==========================================================================
# 23 / SAFETY CULTURE —— 遗留
# ==========================================================================
class Culture:
    def render(self, c, tl, t):
        c.clear(T.BG0)
        plate(c, 330)
        p = c.pass_()
        C.hair_grid(p, alpha=0.04)
        C.title(p, "遗留", "23", "1986 年之后，核安全多了一个以前不在清单上的东西")

        a = C.ramp(tl, 0.10, 0.42)
        p.text(CX, 262, "安全文化", C.zh(74, 700), T.WHITE, 2.0, "mm", a)
        b = C.ramp(tl, 0.26, 0.42)
        p.text(CX, 322, "SAFETY CULTURE  ·  INSAG-4 (1991)", C.zm(14), T.ACCENT, 2.6,
               "ms", b)
        p.line([(CX - 250 * C.ramp(tl, 0.36, 0.4), 348),
                (CX + 250 * C.ramp(tl, 0.36, 0.4), 348)], T.ACCENT, 2.0, 0.85)

        # --- 时间轴（三个节点等距摆开；按年份线性排会挤成一团）
        ax0, ax1, axy = 180.0, 1100.0, 470.0
        p.line([(ax0, axy), (ax1, axy)], T.RULE_HI, 1.2, 0.85)
        marks = [(258.0, "1986", "4 号机组事故", T.DANGER),
                 (600.0, "1991", "INSAG-4 提出安全文化", T.ACCENT),
                 (1010.0, "今天", "RBMK 仍在运行（已改造）", T.INFO)]
        for i, (x, lab, sub, col) in enumerate(marks):
            e = C.ramp(tl, 0.46 + i * 0.14, 0.34)
            if e <= 0.01:
                continue
            p.line([(x, axy), (x, axy - 40 * e)], col, 1.6, 0.9)
            p.dot(x, axy, 4.6, col, 0.95)
            p.text(x, axy - 82, lab, C.tf(lab, 15), col, 1.2, "ms", e)
            p.text(x, axy - 60, sub, C.zh(12.5), T.WHITE, 0.5, "ms", 0.92 * e)

        c2 = C.ramp(tl, 0.90, 0.26)
        p.text(CX, 540, "「安全文化」：组织自身的态度与习惯，而不是某一台设备的参数", C.zh(15),
               T.GREY, 0.6, "ms", 0.95 * c2)
        C.source_line(p, T.SRC_IAEA + "   ·   INSAG-4 (1991)")
        c.commit()


# ==========================================================================
# 24 / SIGN OFF —— 收尾
# ==========================================================================
class SignOff:
    def render(self, c, tl, t):
        c.clear(T.INK)
        plate(c, 320, (0.020, 0.026, 0.036), 820, 300)
        p = c.pass_()
        C.hair_grid(p, y0=40, y1=C.SRC_Y + 8, cols=16, rows=9, alpha=0.05, major=4)
        C.kicker(p, T.M, 92, "RBMK-1000  ·  REACTOR 4  ·  CHERNOBYL", T.ACCENT,
                 C.ramp(tl, 0.04, 0.4))

        # --- 收束图：与片头同形，但这一次标上了三个时间点
        pl = plot(180, 1156, 180, 396, 0.0, 6.0, 0.0, 1.06)
        C.frame(p, pl, xticks=[0, 1, 2, 3, 4, 5, 6], yticks=[], grid=False)
        C.hline(p, pl, 1.0, T.TRACE, "额定 3200 MWt", 0.50, 1.0, True, "l")
        xs = np.linspace(0, 6, 400)
        ys = np.where(xs < 2.60, 0.072 + 0.004 * xs,
                      0.072 + 1.05 * np.clip((xs - 2.60) / 1.15, 0, 1) ** 0.75)
        ok = np.nonzero(ys <= 1.06)[0]
        top = int(ok[-1]) if len(ok) else len(xs) - 1
        low = xs < 2.60
        C.series(p, pl, xs[low], ys[low], T.ACCENT, 2.4, 0.95,
                 upto=C.ramp(tl, 0.12, 0.55))
        C.series(p, pl, xs[~low][:top - int(low.sum()) + 1],
                 ys[~low][:top - int(low.sum()) + 1], T.DANGER, 2.8, 1.0,
                 upto=C.ramp(tl, 0.30, 0.55), glow=True)
        for xv, lab, col in ((0.0, "01:23:04", T.GREY), (2.6, "01:23:40", T.GREY),
                             (float(xs[top]), "×100", T.DANGER)):
            if C.ramp(tl, 0.44, 0.3) > 0.4:
                p.text(pl.sx(xv), pl.y1 + 26, lab, C.zm(11), col, 1.2, "ms", 0.9)
        p.text(180, 166, "AZ-5 之后 6 秒 · 中子功率（刻度示意）", C.zh(11.5), T.GREY_D,
               0.5, "ls", 0.9)

        a = C.ramp(tl, 0.46, 0.42)
        p.text(T.M, 476, "一次把设计缺陷、规程漏洞与人的判断", C.zh(25, 700), T.WHITE,
               1.2, "ls", a)
        p.text(T.M, 512, "同时暴露出来的临界事故", C.zh(25, 700), T.ACCENT, 1.2, "ls", a)

        b = C.ramp(tl, 0.66, 0.40)
        rows = [("急性放射病患者", "%d 例" % D["ars_cases"]),
                ("其中 1986 年死亡", "%d 人" % D["ars_deaths_1986"]),
                ("事故时间", "1986-04-26  01:23:40")]
        for i, (k, v) in enumerate(rows):
            y = 476 + i * 30
            p.text(764, y, k, C.zh(12.5), T.GREY, 0.5, "ls", 0.9 * b)
            p.text(1004, y, v, C.tf(v, 13), T.WHITE, 1.2, "ls", 0.95 * b)
        p.text(764, 440, "UNSCEAR 2008", C.zm(9), T.GREY_D, 1.2, "ls", 0.85 * b)

        C.source_line(p, T.SRC_INSAG7)
        p.text(T.M, C.SRC_Y - 30, T.SRC_UNSCEAR + "   ·   " + T.SRC_NNDC, C.zm(9.0, 400),
               T.GREY_D, 1.1, "ls", 0.9 * b)
        c.commit()


# --------------------------------------------------------------------------
SCENES = [Slate, Core, VoidCoeff, WhyPositive, RodDesign, RodMargin,
          TheTest, Xenon, Withdrawal, Abnormal, TestStart, Az5,
          PositiveScram, Excursion, Rupture, Blast, NoContainment, Fire,
          Loop, Insag7, Defects, Fixes, Culture, SignOff]

assert len(SCENES) == T.BARS, "SCENES 必须正好 %d 场" % T.BARS
