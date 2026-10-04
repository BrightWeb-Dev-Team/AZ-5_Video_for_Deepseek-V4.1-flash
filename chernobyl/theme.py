# -*- coding: utf-8 -*-
"""CHERNOBYL — 45 秒技术复盘。数据图版（data-infographic 牌）。

风格牌要求：图表就是主角，柱/线/表盘按拍生长；坐标轴、刻度、单位标注；
一个数据点被唯一强调色高亮；数字滚动到位后停住。
牌面的「注意」：屏幕上的每个数字都要有出处，示意图必须标明是示意图。
所以本文件里出现的每一个量都带 SRC_* 出处，绘制时由 charts.source_line() 落到画面角上，
示意曲线一律加 SCHEMATIC 标注。

时间网格：45.000 s = 24 小节 × 1.875 s，128 BPM，每场正好一小节（每场 56 或 57 帧）。
"""

# --- identity ---------------------------------------------------------------
BRAND = "CHNPP"
DOMAIN = "CHNPP"            # 切尔诺贝利核电厂（Chernobyl Nuclear Power Plant）
PRODUCT = "UNIT 4"
STUDIO = "UNIT 4"
PLATFORMS = "RBMK-1000 · 事故原因技术复盘"
TAGLINE = "01:23:40"
REEL_TAG = "TECHNICAL BRIEF // 45 SEC"

# --- timeline ---------------------------------------------------------------
# 45.000 s exactly = 24 bars x 1.875 s @ 128 BPM. 30 fps -> 1350 frames.
#   seconds = bars * 4 * 60 / BPM      BPM = 240 * bars / seconds
FPS = 30
BPM = 128
BEAT = 60.0 / BPM          # 0.46875 s
BAR = BEAT * 4             # 1.875 s
BARS = 24
DUR = BAR * BARS           # 45.000 s
NFRAMES = int(round(DUR * FPS))   # 1350

# Layout space 720p, delivery 1080p (vector/type pass renders at delivery size).
OUT_W, OUT_H = 1920, 1080
W, H = 1280, 720

# --- palette ----------------------------------------------------------------
# 仪表盘/记录仪的量色。深板 + 极淡网格线；三个语义色各有唯一含义，全片不许串用：
#   琥珀 ACCENT  = 实测值 / 被高亮的那个数据点
#   红   DANGER  = 越限 / 事故进程
#   蓝   INFO    = 负反应性 / 中子吸收体（水、氙、碳化硼）
# 中性曲线 TRACE 只画参照，不许当强调色用。
INK = (5, 7, 10)             # deepest plate
BG0 = (9, 12, 16)
BG1 = (14, 18, 24)
BG2 = (21, 27, 35)

RULE = (30, 40, 52)          # 极淡网格线
RULE_HI = (50, 65, 82)       # 坐标轴 / 主刻度

ACCENT = (255, 176, 32)      # 琥珀：实测值
ACCENT_BR = (255, 208, 104)
ACCENT_LT = (255, 229, 174)
ACCENT_DK = (168, 104, 10)

DANGER = (255, 64, 40)       # 红：越限 / 事故
DANGER_BR = (255, 134, 94)

INFO = (74, 158, 232)        # 蓝：负反应性 / 吸收体
INFO_LT = (150, 200, 245)

TRACE = (126, 150, 168)      # 中性参照线
WHITE = (233, 240, 245)
PAPER = (236, 239, 236)      # 亮场（20 场：报告纸）
CARD = (255, 255, 255)
GREY = (118, 134, 150)
GREY_D = (62, 76, 92)
SLATE = (26, 34, 44)

# --- type -------------------------------------------------------------------
# 中文走 Noto Sans SC（内置 woff 无 CJK 字面），数字/读数走 JetBrains Mono。
# CJK 表意字约 0.88 em，拉丁大写约 0.72 em，所以字号不能互抄。
S_H1 = 58.0        # 场标题（中文）
S_H2 = 28.0        # 副标题（中文）
S_BODY = 16.0      # 正文（中文）
S_NOTE = 12.5      # 图注（中文）
S_READ = 10.5      # 读数标签
S_TAG = 10.0       # HUD / 轴标签（等宽）
S_HUD = 9.5
S_NUM = 58.0       # 大数字（等宽）
S_NUM_BIG = 112.0

TRACK_H1 = 1.4
TRACK_BODY = 0.8
TRACK_HUD = 1.5

# --- HUD chrome -------------------------------------------------------------
M = 56.0           # live-area margin
HUD_M = 27.0
HUD_TOP = 24.0
HUD_BOT = 700.0
HUD_SEC = 662.0    # HUD 上沿：场标题最多顶到这里

# --- scenes -----------------------------------------------------------------
# (编号, HUD 英文名（等宽字体上屏，必须是拉丁）, 中文名 —— 第三个字段不上屏，仅供检索)
SCENES = [
    ("01", "SLATE",           "片头 · 01:23:40"),
    ("02", "THE CORE",        "RBMK-1000 是什么"),
    ("03", "VOID COEFF",      "正空泡系数"),
    ("04", "WHY POSITIVE",    "为什么是正的"),
    ("05", "ROD DESIGN",      "控制棒的两个缺陷"),
    ("06", "ROD MARGIN",      "运行反应性裕度 ORM"),
    ("07", "THE TEST",        "试验目的"),
    ("08", "XENON",           "氙-135 毒化"),
    ("09", "ROD WITHDRAWAL",  "拔棒回功率"),
    ("10", "ABNORMAL STATE",  "当晚的非正常状态"),
    ("11", "01:23:04",        "试验开始"),
    ("12", "AZ-5",            "紧急停堆"),
    ("13", "POSITIVE SCRAM",  "石墨端头注入正反应性"),
    ("14", "POWER EXCURSION", "功率尖峰"),
    ("15", "CHANNEL RUPTURE", "压力管破裂"),
    ("16", "STEAM BLAST",     "蒸汽爆炸"),
    ("17", "NO CONTAINMENT",  "为什么没有安全壳"),
    ("18", "GRAPHITE FIRE",   "石墨火 · 十天"),
    ("19", "FEEDBACK LOOP",   "闭环"),
    ("20", "INSAG-7",         "结论：根因在堆型"),
    ("21", "DEFECTS",         "三条设计缺陷"),
    ("22", "FIXES",           "事故后的改造"),
    ("23", "SAFETY CULTURE",  "遗留：安全文化"),
    ("24", "SIGN OFF",        "收尾"),
]

# --- 出处标记 ---------------------------------------------------------------
SRC_INSAG7 = "SOURCE  INSAG-7 · IAEA SAFETY SERIES No. 75-INSAG-7 (1992)"
SRC_INSAG1 = "SOURCE  INSAG-1 · IAEA (1986)"
SRC_IAEA = "SOURCE  IAEA · 事故后公开资料"
SRC_UNSCEAR = "SOURCE  UNSCEAR 2008 REPORT · ANNEX D"
SRC_NNDC = "SOURCE  NNDC/BNL 核素衰变数据"
SRC_RULES = "SOURCE  运行规程与试验方案（事故调查报告转录）"
SCHEMATIC = "示意图 · SCHEMATIC — 形状示意，刻度为真实值"

# --- 数据（屏幕上的每个数字都从这里取，改数据只改这一处）--------------------
# 见 references/gotchas.md 第 29 条：屏幕上的数字必须能对上代码。
D = {
    # 02 堆本体
    "t_thermal_mw": 3200,        # 热功率 MWt
    "t_electric_mw": 1000,       # 电功率 MWe (2 x 500)
    "channels": 1661,            # 燃料压力管数
    "graphite_t": 1700,          # 石墨砌体质量 t
    "rods_total": 211,           # 控制棒总数
    "enrich_pct": 2.0,           # 燃料富集度 %
    "pressure_bar": 70,          # 名义蒸汽压力 bar
    # 03 空泡系数
    "void_beta": 4.5,            # 空泡系数 +4.5 beta（INSAG-7）
    "void_beta_pwr": -0.5,       # 压水堆参照值，示意
    # 05 控制棒
    "rod_travel_m": 7.0,         # 棒行程 m
    "rod_travel_s": 18.0,        # 全行程插入时间 s（原始设计）
    "tip_effect_s": 2.0,         # 端头效应持续 s
    # 06 ORM。当晚运行的规程下限是 15 根当量，实测约 8；事故后下限提高到 30。
    "orm_limit_night": 15,       # 当晚适用的规程下限（当量根数）
    "orm_actual": 8,             # 当晚实测
    "orm_after": 30,             # 事故后提高到当量根数
    # 07 试验
    "p_before": 3200,
    "p_target": 700,
    "p_turbine_s": 40,           # 汽轮机惰转需要维持厂用电的秒数
    # 08 氙毒
    "p_dropped": 30,             # 实际掉到的功率 MWt
    "i135_h": 6.7,               # I-135 半衰期 h
    "xe135_h": 9.2,              # Xe-135 半衰期 h
    # 09 拔棒
    "p_recovered": 200,
    "orm_before": 26,
    # 11 试验开始
    "t_test": "01:23:04",
    "pumps_running": 8,          # 当晚运行主泵台数
    "pumps_limit": 6,            # 规程上限
    # 12 AZ-5
    "t_az5": "01:23:40",
    # 14 功率尖峰
    "excursion_x": 100,          # 4 s 内达到额定功率的百倍量级
    "excursion_s": 4.0,
    # 16 爆炸
    "blast1": "01:23:47",
    "blast2": "01:23:49",
    "shield_t": 2000,            # 上部生物屏蔽质量 t
    # 18 石墨火
    "fire_days": 10,
    "release_bq": "5.2 × 10^18", # 释放总活度 Bq（IAEA）
    "evac_km": 30,
    "evac_people": 135000,
    # 22 改造
    "fix_enrich": "2.0% → 2.4%",
    # 24 收尾
    "ars_cases": 134,
    "ars_deaths_1986": 28,
}
