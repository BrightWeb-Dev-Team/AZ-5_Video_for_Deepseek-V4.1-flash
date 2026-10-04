# -*- coding: utf-8 -*-
"""配乐 —— 128 BPM / 24 小节 / 45.000 s，四幕与画面共用同一张时间表。

风格牌要求「电气化，打点与生长同帧」：所以鼓点不铺满，而是**按场的性质**出现 ——
第一幕只有记录仪的滴答（单音脉冲 + 稀疏盖革计数），第二幕推进到四拍底鼓，
第三幕（12–18 小节）是事故本身：AZ-5 那一下是整条片子最重的瞬态，
第四幕全部撤掉，只剩铺底、钟声和盖革的余响。

所有时间点都走 at(bar, beat)，和画面一样由 240 × bars / seconds = 128 BPM 反解，
不写死样本数（gotchas 37：时间轴只能有一个来源）。
"""
from __future__ import annotations

import numpy as np

from mg.dsp import (SR, analyse, bp, env_ad, filt, hp, lp, noise, peak_norm, place,
                    reverb_tail, t_axis, write_wav)

from . import theme as T

NOTE = {"A1": 55.0, "B2": 123.47, "C2": 65.41, "D2": 73.42, "E2": 82.41,
        "F2": 87.31, "G2": 98.0, "A2": 110.0, "C3": 130.81, "D3": 146.83,
        "E3": 164.81, "F3": 174.61, "G3": 196.0, "A3": 220.0, "C4": 261.63,
        "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0,
        "C5": 523.25, "E5": 659.26}


# --------------------------------------------------------------------------
# 音色
# --------------------------------------------------------------------------
def kick(sr=SR, dur=0.72, f0=112.0, f1=38.0, pitch_t=0.085, amp_t=0.34, drive=1.9):
    """更低的底鼓：这台片子的「重量」全在这个 38 Hz 上。"""
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    f = f1 + (f0 - f1) * np.exp(-t / pitch_t)
    body = np.sin(2 * np.pi * np.cumsum(f) / sr).astype(np.float32)
    a = np.exp(-t / amp_t).astype(np.float32)
    click = filt((noise(n, 11) * np.exp(-t / 0.0035)).astype(np.float32), sr,
                 bp(1800, 7000, 2.0)).astype(np.float32) * 0.26
    return peak_norm(filt(np.tanh((body * a + click) * drive) * 0.8, sr,
                          lp(5200, 2.4)).astype(np.float32))


def tick(sr=SR, dur=0.05, seed=3, hi=5200.0):
    """记录仪笔尖的滴答：第一幕唯一的节拍来源。"""
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    x = filt(noise(n, seed), sr, bp(hi * 0.6, hi * 2.2, 2.4)).astype(np.float32)
    x *= np.exp(-t / 0.006).astype(np.float32)
    return peak_norm(x)


def geiger(sr=SR, dur=None, rate=7.0, seed=17, lo=1400.0, hi=6200.0):
    """盖革计数器的咔哒串 —— 用计数率当打击乐。"""
    dur = dur or T.BAR
    n = int(round(dur * sr))
    out = np.zeros(n, np.float32)
    rng = np.random.default_rng(seed)
    k = 0
    pos = 0.0
    while pos < dur:
        pos += rng.exponential(1.0 / max(rate, 0.05))
        i = int(pos * sr)
        if i >= n:
            break
        cl = filt(noise(int(0.012 * sr), seed + 100 + k), sr, bp(lo, hi, 2.2))
        cl = (cl * np.exp(-np.arange(len(cl)) / (0.0025 * sr))).astype(np.float32)
        j = min(n, i + len(cl))
        out[i:j] += cl[: j - i] * (0.35 + 0.65 * rng.random())
        k += 1
    return out


def hat(sr=SR, dur=0.085, seed=5, open_=False):
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    x = filt(noise(n, seed), sr, hp(8200, 2.2)).astype(np.float32)
    x *= np.exp(-t / (0.052 if open_ else 0.015)).astype(np.float32)
    return peak_norm(filt(x, sr, hp(6200, 1.6)).astype(np.float32))


def sub(freq, sr=SR, dur=0.58, amp=0.9):
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    x = np.sin(2 * np.pi * freq * t).astype(np.float32)
    x += 0.14 * np.sin(4 * np.pi * freq * t).astype(np.float32)
    x *= env_ad(n, 0.008, 0.50, sr, 2.8)
    return peak_norm(x) * amp


def pluck(freq, sr=SR, dur=0.30, bright=1.0):
    """冷的 FM 拨弦：这个音色是「仪表」而不是「乐器」。"""
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    mod = np.sin(2 * np.pi * freq * 3.51 * t).astype(np.float32) * np.exp(-t / 0.04) * 2.6
    x = np.sin(2 * np.pi * freq * t + mod).astype(np.float32)
    x += 0.26 * np.sin(2 * np.pi * freq * 7.02 * t).astype(np.float32) * np.exp(-t / 0.02)
    x *= env_ad(n, 0.0010, 0.20, sr, 5.6)
    return peak_norm(filt(x, sr, lp(8200 * bright, 2.6)).astype(np.float32))


def bell(freq, sr=SR, dur=2.4):
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    x = np.sin(2 * np.pi * freq * t).astype(np.float32)
    x += 0.32 * np.sin(2 * np.pi * freq * 2.76 * t).astype(np.float32) * np.exp(-t / 0.42)
    x += 0.14 * np.sin(2 * np.pi * freq * 5.40 * t).astype(np.float32) * np.exp(-t / 0.15)
    x *= env_ad(n, 0.005, 1.9, sr, 2.2)
    return peak_norm(filt(x, sr, lp(7200, 2.2)).astype(np.float32))


def pad_chord(freqs, sr=SR, dur=2.0, cut=1500.0, detune=0.0061):
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    x = np.zeros(n, np.float32)
    for f in freqs:
        for d, g in ((-detune, 0.8), (0.0, 0.9), (detune, 0.8), (detune * 2.3, 0.5)):
            ph = 2 * np.pi * (f * (1.0 + d)) * t
            x += (2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0).astype(np.float32) * g / len(freqs)
    x = filt(x, sr, lp(cut, 2.2)).astype(np.float32)
    x *= env_ad(n, 0.34, dur * 0.72, sr, 1.4)
    return peak_norm(x)


def alarm(sr=SR, dur=0.9, f0=690.0, f1=930.0):
    """两声报警：事故幕里唯一的「旋律」。"""
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    seg = (t // 0.22).astype(np.int32)
    f = np.where(seg % 2 == 0, f0, f1)
    ph = 2 * np.pi * np.cumsum(f) / sr
    x = (2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0).astype(np.float32)
    x = filt(x, sr, bp(400, 4200, 2.0)).astype(np.float32)
    gate = np.where((t % 0.22) < 0.15, 1.0, 0.0).astype(np.float32)
    x *= gate * np.exp(-t / 1.6)
    return peak_norm(x)


def riser(sr=SR, dur=1.875, f0=260.0, f1=8600.0, seed=21):
    n = int(round(dur * sr))
    x = noise(n, seed)

    def resp(f, tt, a=f0, b=f1, d=dur):
        pos = min(1.0, max(0.0, tt / d)) ** 1.75
        c = a * (b / a) ** pos
        return ((f / c) ** 1.7 / (1.0 + (f / c) ** 1.7)
                * (1.0 / (1.0 + (f / min(c * 5.0, 16000.0)) ** 2.0)))

    x = filt(x, sr, resp).astype(np.float32)
    t = np.arange(len(x), dtype=np.float32) / sr
    amp = (t / max(float(t[-1]), 1e-6)) ** 2.0
    x *= amp
    swp = np.sin(2 * np.pi * np.cumsum(np.linspace(180, 2100, len(x))) / sr).astype(np.float32)
    return peak_norm(x + swp * amp * 0.24)


def impact(sr=SR, dur=1.6, seed=33, hard=1.0):
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    crk = filt(noise(n, seed), sr, bp(300, 8000, 1.5)).astype(np.float32)
    crk *= np.exp(-t / (0.07 / max(hard, 1e-3)))
    f = 190.0 * np.exp(-t / 0.10) + 31.0
    boom = np.sin(2 * np.pi * np.cumsum(f) / sr).astype(np.float32) * np.exp(-t / 0.42)
    return peak_norm(crk * 0.85 * hard + boom)


def drone(freqs, sr=SR, dur=4.0, seed=9):
    """事故后的低频铺底：不是音乐，是背景。"""
    n = int(round(dur * sr))
    t = t_axis(dur, sr)
    x = np.zeros(n, np.float32)
    for i, f in enumerate(freqs):
        x += np.sin(2 * np.pi * f * t + i * 1.1).astype(np.float32)
    x = x / max(1, len(freqs))
    x += 0.18 * filt(noise(n, seed), sr, bp(60, 320, 2.0)).astype(np.float32)
    x *= env_ad(n, 0.5, dur * 0.6, sr, 1.2)
    return peak_norm(x)


# --------------------------------------------------------------------------
# 编排：i–VI–iv–V（a 小调），四幕各有各的织体
# --------------------------------------------------------------------------
PROG = [
    ("A2", ["A2", "C3", "E3", "A3"]),
    ("F2", ["F2", "A2", "C3", "F3"]),
    ("D2", ["D2", "F2", "A2", "D3"]),
    ("E2", ["E2", "G2", "B2", "E3"]),
]
ARP = ["A4", "C5", "E5", "A4", "C5", "E5", "A4", "C5"]


def build(dur=None, sr=SR):
    dur = dur or T.DUR
    n = int(round(dur * sr))
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)

    def at(bar, beat=0.0):
        return int(round((bar * T.BAR + beat * T.BEAT) * sr))

    def put(src, bar, beat, gl, gr):
        place(L, src, at(bar, beat), gl)
        place(R, src, at(bar, beat), gr)

    K = kick(sr)
    KT = kick(sr, dur=0.5, f0=132.0, amp_t=0.22)      # 紧凑版，第二幕用
    HH = hat(sr)
    HO = hat(sr, dur=0.24, open_=True)
    SUB = {nm: sub(NOTE[nm]) for nm in NOTE if nm.endswith("2")}
    PLK = {nm: pluck(NOTE[nm]) for nm in ("A4", "C5", "E5", "D4", "E4", "G4")}
    BL = {nm: bell(NOTE[nm]) for nm in ("A4", "C5", "E5", "A3", "C4")}
    DRN = drone([55.0, 82.41, 110.0], sr, 4.5)

    for bar in range(T.BARS):
        root, chord = PROG[bar % 4]
        act = bar // 6

        # --- 铺底：四幕的浓度不同
        if act == 0:
            cut, g = 1100.0, (0.16 if bar == 0 else 0.13)
        elif act == 1:
            cut, g = 1700.0, 0.19
        elif act == 2:
            cut, g = 2100.0, 0.22
        else:
            cut, g = 1300.0, (0.24 if bar in (18, 19, 23) else 0.20)
        pad = pad_chord([NOTE[x] for x in chord], sr, T.BAR * 1.06, cut=cut)
        put(pad, bar, 0.0, g * 0.95, g * 1.05)

        # --- 第一幕：记录仪的滴答 + 稀疏盖革
        if act == 0:
            for beat in range(4):
                put(tick(sr, seed=3 + beat, hi=4600.0 + beat * 320), bar, beat, 0.34, 0.30)
            if bar >= 1:
                gg = geiger(sr, T.BAR, rate=3.2 + bar * 0.5, seed=40 + bar)
                put(gg, bar, 0.0, 0.30, 0.26)
            if bar >= 2:
                put(KT, bar, 0.0, 0.62, 0.62)
                put(KT, bar, 2.0, 0.44, 0.44)
            if bar == 5:
                put(riser(sr, T.BAR * 0.95, 240.0, 7000.0, 61), bar, 0.08, 0.40, 0.40)

        # --- 第二幕：四拍底鼓、八分踩镲、十六分拨弦、低音 riff
        elif act == 1:
            for beat in range(4):
                put(KT, bar, beat, 0.80, 0.80)
                put(HO, bar, beat + 0.5, 0.13, 0.145)
                put(HH, bar, beat + 0.25, 0.085, 0.08)
                put(HH, bar, beat + 0.75, 0.075, 0.072)
            riff = [(0.0, 1.0), (0.75, 0.5), (1.5, 0.8), (2.25, 0.45), (3.0, 0.9)]
            for off, gl in riff:
                put(SUB.get(root, SUB["A2"]), bar, off, 0.30 * gl, 0.30 * gl)
            if bar >= 7:
                for i in range(16):
                    nm = ARP[i % len(ARP)]
                    f = PLK.get(nm, PLK["A4"])
                    pan = 0.5 + 0.42 * float(np.sin(i * 1.13 + bar * 0.4))
                    put(f, bar, i * 0.25, 0.115 * (1.0 - pan * 0.5), 0.115 * pan)
            if bar == 11:
                put(riser(sr, T.BAR * 0.98, 200.0, 9000.0, 71), bar, 0.04, 0.46, 0.46)

        # --- 第三幕：事故。AZ-5（12）与蒸汽爆炸（15）是整条片子的两个重量点
        elif act == 2:
            if bar == 12:
                put(impact(sr, 1.8, 33, 1.15), bar, 0.0, 0.92, 0.92)
                put(alarm(sr, 1.0), bar, 0.10, 0.30, 0.26)
                for beat in (0.0, 1.0, 2.0, 2.5, 3.0, 3.5):
                    put(K, bar, beat, 0.72, 0.72)
            elif bar == 15:
                put(impact(sr, 2.0, 51, 1.35), bar, 0.0, 1.0, 1.0)
                put(impact(sr, 1.4, 52, 1.0), bar, 0.35, 0.62, 0.62)
                put(alarm(sr, 1.2, 620.0, 880.0), bar, 0.5, 0.24, 0.22)
            else:
                for beat in (0.0, 0.75, 1.5, 2.25, 3.0, 3.5):
                    put(K, bar, beat, 0.68, 0.68)
                put(SUB.get(root, SUB["A2"]), bar, 0.0, 0.34, 0.34)
                put(SUB.get(root, SUB["A2"]), bar, 2.0, 0.26, 0.26)
            if bar in (13, 14, 16, 17):
                gg = geiger(sr, T.BAR, rate=16.0 + (bar - 13) * 3.0, seed=80 + bar)
                put(gg, bar, 0.0, 0.34, 0.30)
            if bar >= 16:
                put(DRN, bar, 0.0, 0.34, 0.34)
            if bar == 14:
                put(riser(sr, T.BAR * 0.9, 300.0, 6000.0, 91), bar, 0.1, 0.28, 0.28)

        # --- 第四幕：全部撤掉，只剩铺底、钟声、盖革的余响
        else:
            gg = geiger(sr, T.BAR, rate=max(1.0, 4.5 - (bar - 18) * 0.8), seed=120 + bar)
            put(gg, bar, 0.0, 0.16, 0.15)
            if bar in (18, 23):
                put(KT, bar, 0.0, 0.52, 0.52)
            if bar in (19, 20):
                put(SUB.get(root, SUB["A2"]), bar, 0.0, 0.24, 0.24)
            # 结论那三小节不能空成静音：一小节一个低音点，像判决书翻页
            if bar in (20, 21, 22):
                put(SUB.get(root, SUB["A2"]), bar, 0.0, 0.20, 0.20)
                put(SUB.get(root, SUB["A2"]), bar, 2.0, 0.13, 0.13)
            if bar == 22:
                put(riser(sr, T.BAR, 220.0, 3400.0, 131), bar, 0.2, 0.18, 0.18)

    # --- 钟声：结论与收尾的旋律
    for bar, beat, nm, g in ((19, 0.0, "A4", 0.22), (19, 2.0, "E5", 0.16),
                             (21, 0.0, "C5", 0.18), (22, 1.5, "A4", 0.16),
                             (23, 0.0, "A3", 0.30), (23, 2.0, "E5", 0.14)):
        b = BL.get(nm, BL["A4"])
        put(b, bar, beat, g * 0.95, g * 0.8)

    # --- 总线上处理
    L = filt(L, sr, lp(15800, 2.2)).astype(np.float32)
    R = filt(R, sr, lp(15800, 2.2)).astype(np.float32)
    L = filt(L, sr, hp(28, 2.0)).astype(np.float32)
    R = filt(R, sr, hp(28, 2.0)).astype(np.float32)
    L = reverb_tail(L, sr, taps=((0.083, 0.15), (0.147, 0.09), (0.229, 0.055)))
    R = reverb_tail(R, sr, taps=((0.097, 0.15), (0.163, 0.09), (0.251, 0.055)))

    st = np.stack([L, R], -1)
    peak = float(np.abs(st).max())
    st = np.tanh(st / max(peak, 1e-6) * 1.85) / np.tanh(1.85)
    f = int(0.014 * sr)
    st[:f] *= np.linspace(0, 1, f, dtype=np.float32)[:, None]
    g = int(0.9 * sr)
    st[-g:] *= np.linspace(1.0, 0.0, g, dtype=np.float32)[:, None]

    # 真峰在过采样之后压（gotchas 27）：只保证采样点不超，编码器照样在采样间顶上去。
    # 0.905 ⇒ 约 −0.9 dBTP，落在交付规范的 −1.0 ~ −0.5 dBTP 里。
    st = _limit_truepeak(st, ceiling=0.905)
    return st.astype(np.float32), sr


def _limit_truepeak(st, ceiling=0.905):
    """4× 过采样后按真峰归一 —— 压的是瞬态，主体响度不掉。"""
    out = np.empty_like(st)
    for ch in range(st.shape[1]):
        x = st[:, ch].astype(np.float64)
        n = len(x)
        spec = np.fft.rfft(x)
        pad = np.zeros(n * 4 // 2 + 1, dtype=np.complex128)
        pad[: len(spec)] = spec
        up = np.fft.irfft(pad, n * 4) * 4.0
        pk = float(np.abs(up).max())
        if pk > ceiling:
            x = x * (ceiling / pk)
        out[:, ch] = x.astype(np.float32)
    return out


__all__ = ["build", "write_wav", "analyse", "SR"]
