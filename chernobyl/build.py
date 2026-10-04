# -*- coding: utf-8 -*-
"""出片：配乐 → 逐场渲染 → 编码 → 混流。

    py -3 -m chernobyl.build                 全片
    py -3 -m chernobyl.build --at 13:1.2     某一拍的单帧全分辨率
    py -3 -m chernobyl.build --stills 5      一场抽 7 帧拼长图
    py -3 -m chernobyl.build --scenes 2,4    只重渲某几场

一场一小节，场与场之间没有任何共享状态，所以「并行」在这里等于把场景切片丢给
若干独立进程，每个进程自己写自己的帧文件 —— 进程之间零通信。

为什么不用 multiprocessing.Pool：Windows 沙箱不允许开**命名管道**
（\\\\.\\pipe\\...），Pool 一建队列就 PermissionError: [WinError 5]。
子进程仍然是真并行，只是不能再走 Pool 的 SimpleQueue；stdout 各自落到日志文件，
不经过任何管道。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

import numpy as np

from mg.core import Canvas

from . import chrome
from . import scenes as SC
from . import theme as T

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# 用 -m 跑的时候 __name__ 是 "__main__"，只有 __package__ 还是真包名。
PKG = __package__ or os.path.basename(HERE)
OUT = os.path.join(ROOT, "out")
FRAMES = os.path.join(OUT, "frames")


def scene_objects():
    # one instance per scene, in bar order: SCENES lives in scenes.py
    return [cls() for cls in SC.SCENES]


def render_one(i, ss=2):
    obj = scene_objects()[i]
    os.makedirs(FRAMES, exist_ok=True)
    f0 = int(round(i * T.BAR * T.FPS))
    f1 = int(round((i + 1) * T.BAR * T.FPS))
    for f in range(f0, f1):
        t = f / T.FPS
        tl = t - i * T.BAR
        c = Canvas(T.W, T.H, ss=ss, out=(T.OUT_W, T.OUT_H))
        obj.render(c, tl, t)
        p = c.pass_()
        chrome.draw(p, t, i, chrome.POST[i].get("light", False))
        c.commit()
        chrome.finish(c, t, i)
        c.image().save(os.path.join(FRAMES, f"f{f:04d}.png"))
    return f1 - f0


def render_at(i, tl, ss=2, name=None):
    obj = scene_objects()[i]
    t = i * T.BAR + tl
    c = Canvas(T.W, T.H, ss=ss, out=(T.OUT_W, T.OUT_H))
    obj.render(c, tl, t)
    p = c.pass_()
    chrome.draw(p, t, i, chrome.POST[i].get("light", False))
    c.commit()
    chrome.finish(c, t, i)
    path = os.path.join(OUT, name or f"at_s{i}_{tl:.3f}.png")
    c.image().save(path)
    return path


def render_still(i, tl_list, ss=2, tag=""):
    from PIL import Image

    os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
    rows = []
    for k, tl in enumerate(tl_list):
        t = i * T.BAR + tl
        c = Canvas(T.W, T.H, ss=ss, out=(T.OUT_W, T.OUT_H))
        scene_objects()[i].render(c, tl, t)
        p = c.pass_()
        chrome.draw(p, t, i, chrome.POST[i].get("light", False))
        c.commit()
        chrome.finish(c, t, i)
        img = c.image()
        img.save(os.path.join(OUT, f"stills/s{i}_{k}_{tl:.2f}{tag}.png"))
        rows.append(img)
    sheet = Image.new("RGB", (rows[0].width, rows[0].height * len(rows)), (0, 0, 0))
    for k, im in enumerate(rows):
        sheet.paste(im, (0, k * im.height))
    sp = os.path.join(OUT, f"sheet_s{i}{tag}.jpg")
    sheet.resize((sheet.width * 3 // 5, sheet.height * 3 // 5), Image.LANCZOS).save(
        sp, quality=88)
    return sp


def build_audio():
    from . import audio as A

    os.makedirs(OUT, exist_ok=True)
    st, sr = A.build()
    A.write_wav(os.path.join(OUT, "track.wav"), st, sr)
    wave, spec = A.analyse(st, sr, fps=T.FPS)
    np.save(os.path.join(OUT, "wave.npy"), wave)
    np.save(os.path.join(OUT, "spec.npy"), spec)
    return os.path.join(OUT, "track.wav")


# --------------------------------------------------------------------------
# 并行扇出（零 IPC）
# --------------------------------------------------------------------------
def _child_env():
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def fan_out(idx, ss, jobs):
    chunks = [c for c in (idx[i::jobs] for i in range(jobs)) if c]
    os.makedirs(FRAMES, exist_ok=True)
    procs = []
    for k, ch in enumerate(chunks):
        cmd = [sys.executable, "-m", PKG + ".build", "--only-frames",
               "--scenes", ",".join(str(i) for i in ch), "--ss", str(ss)]
        log = open(os.path.join(OUT, "worker_%d.log" % k), "w", encoding="utf-8")
        procs.append((k, ch, subprocess.Popen(
            cmd, cwd=ROOT, env=_child_env(), stdout=log, stderr=subprocess.STDOUT),
            log))
    bad = []
    for k, ch, p, log in procs:
        rc = p.wait()
        log.close()
        if rc != 0:
            bad.append((k, ch, rc, os.path.join(OUT, "worker_%d.log" % k)))
    if bad:
        for k, ch, rc, lg in bad:
            print("worker %d scenes=%s rc=%d log=%s" % (k, ch, rc, lg))
        raise SystemExit("some workers failed")


# GPU first. Measured on this engine's own 1080p frames: h264_nvenc is 3.7x
# faster than libx264 preset slow and 28% smaller, for about 0.9 dB of PSNR.
# The AQ switches are not optional — without them flat gradients and grain
# band in the shadows. libx264 stays as the fallback where NVENC is missing.
#
# 选项名在本机 ffmpeg 9.0 上是**连字符**（-spatial-aq / -temporal-aq）。
# 写成下划线（spatial_aq）时 ffmpeg 直接 "Unrecognized option" 退出，
# 而那段 stderr 正好被 libx264 的兜底日志覆盖掉 —— 症状就是「明明有卡却静默退回 x264」。
NVENC = ["-c:v", "h264_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr",
         "-cq", "19", "-b:v", "0", "-spatial-aq", "1", "-temporal-aq", "1",
         "-aq-strength", "12", "-bf", "3", "-pix_fmt", "yuv420p"]
X264 = ["-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p"]


def _has_nvenc():
    """Ask ffmpeg what it was built with — through a temp file, not a pipe.

    Handing nvenc's own options to a build without that encoder makes ffmpeg
    die on `Unrecognized option 'rc'`, which reads like the render is broken.
    The listing is written to a file rather than captured, because piped stdio
    is a sandbox boundary on this platform.
    """
    tmp = os.path.join(OUT, "_encoders.txt")
    os.makedirs(OUT, exist_ok=True)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], stdout=fh,
                           stderr=subprocess.STDOUT)
        txt = open(tmp, encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    return "h264_nvenc" in txt


def _encode_frames(dst, enc, tag="enc"):
    """每个尝试写自己的日志 —— 共用一个文件时，兜底那次会把失败原因截掉。"""
    log = open(os.path.join(OUT, "_%s.log" % tag), "w", encoding="utf-8")
    try:
        return subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-framerate", str(T.FPS),
            "-i", os.path.join(FRAMES, "f%04d.png"), *enc,
            "-movflags", "+faststart", dst,
        ], stdout=log, stderr=subprocess.STDOUT).returncode
    finally:
        log.close()


def encode(name="chernobyl-45s"):
    silent = os.path.join(OUT, f"{name}_silent.mp4")
    for e, (enc, tag) in enumerate([(NVENC, "nvenc"), (X264, "x264")]
                                   if _has_nvenc() else [(X264, "x264")]):
        if _encode_frames(silent, enc, tag) == 0:
            break
        if e == 0:
            print("  nvenc present but failed (%s.log), falling back to libx264"
                  % tag)
    else:
        raise SystemExit("neither h264_nvenc nor libx264 could encode")
    final = os.path.join(OUT, f"{name}.mp4")
    wav = os.path.join(OUT, "track.wav")
    if os.path.exists(wav):
        log = open(os.path.join(OUT, "_mux.log"), "w", encoding="utf-8")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav,
                # 384k. At 256k the native AAC encoder puts this material's
                # decoded peak above 0 dBFS — the mix is transient-heavy.
                "-c:v", "copy", "-c:a", "aac", "-b:a", "384k", "-shortest",
                "-movflags", "+faststart", final,
            ], check=True, stdout=log, stderr=subprocess.STDOUT)
        finally:
            log.close()
        os.remove(silent)
        return final
    return silent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default="all")
    ap.add_argument("--at", default=None)
    ap.add_argument("--stills", type=int, default=None)
    ap.add_argument("--ss", type=int, default=2)
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--skip-frames", action="store_true")
    ap.add_argument("--only-frames", action="store_true",
                    help="只渲帧，不配乐也不编码（并行扇出的子进程用）")
    ap.add_argument("--jobs", type=int, default=0)
    args = ap.parse_args()

    if args.at:
        i, tl = args.at.split(":")
        print(render_at(int(i), float(tl), args.ss))
        return
    if args.stills is not None:
        i = args.stills
        print(render_still(i, [T.BAR * (k / 7.0) for k in range(7)], args.ss))
        return

    idx = list(range(T.BARS)) if args.scenes == "all" else \
        [int(v) for v in args.scenes.split(",")]

    if args.only_frames:
        t0 = time.time()
        n = sum(render_one(i, args.ss) for i in idx)
        print(f"frames {n} in {time.time() - t0:.1f}s idx={idx}", flush=True)
        return

    os.makedirs(OUT, exist_ok=True)
    if not args.no_audio:
        t0 = time.time()
        build_audio()
        print(f"audio  {time.time() - t0:.1f}s")

    if not args.skip_frames:
        # Never the whole machine: a render is a long task and the box has to
        # stay usable while it runs. One worker per scene at most, and a third
        # of the logical cores by default.
        want = args.jobs or max(1, (os.cpu_count() or 4) // 3)
        jobs = max(1, min(len(idx), want))
        if args.jobs and args.jobs > jobs:
            print(f"  --jobs {args.jobs} clamped to {jobs}")
        t0 = time.time()
        fan_out(idx, args.ss, jobs)
        print(f"frames done in {time.time() - t0:.1f}s ({jobs} workers)")

    print("out:", encode())


if __name__ == "__main__":
    main()
