# -*- coding: utf-8 -*-
"""交付自检：规格、帧数、响度、真峰，以及从成片里抽帧核对。"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
NAME = "chernobyl-45s"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,nb_frames,r_frame_rate,codec_name",
             "-show_entries", "format=duration,size", "-of", "default=noprint_wrappers=1",
             path])
    print("--- ffprobe ---")
    print(r.stdout.strip() or r.stderr.strip())


def loud(path):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-af",
             "loudnorm=print_format=summary", "-f", "null", "-"])
    txt = r.stderr
    print("--- loudness ---")
    for pat in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold"):
        for line in txt.splitlines():
            if pat in line:
                print(line.strip())


def frames():
    d = os.path.join(OUT, "frames")
    if not os.path.isdir(d):
        print("--- frames --- no frames dir (already cleaned?)")
        return
    fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    print("--- frames --- %d png, first=%s last=%s" % (len(fs), fs[0] if fs else "-",
                                                       fs[-1] if fs else "-"))


def stills(path):
    """从成片里抽 8 帧拼一张，核对编码后的实际画面。"""
    from PIL import Image
    times = [0.4, 5.2, 11.0, 17.3, 23.0, 28.4, 36.0, 43.5]
    tiles = []
    for k, t in enumerate(times):
        p = os.path.join(OUT, "chk_%d.png" % k)
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1",
             p])
        if os.path.exists(p):
            tiles.append(Image.open(p).convert("RGB").resize((640, 360),
                                                              Image.LANCZOS))
    if not tiles:
        return
    cols, rows = 2, (len(tiles) + 1) // 2
    sh = Image.new("RGB", (640 * cols, 360 * rows), (0, 0, 0))
    for i, im in enumerate(tiles):
        sh.paste(im, ((i % cols) * 640, (i // cols) * 360))
    dst = os.path.join(OUT, "check_film.jpg")
    sh.save(dst, quality=88)
    print("wrote", dst)


def cjk_audit():
    """扫描源码：任何可能落进等宽槽位的中文字符串都要人工确认。"""
    pat = re.compile(r"[\u4e00-\u9fff]")
    bad = []
    for root, _dirs, files in os.walk(os.path.join(HERE, "chernobyl")):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            for i, line in enumerate(open(p, encoding="utf-8"), 1):
                if "zm(" in line and pat.search(line):
                    bad.append("%s:%d  %s" % (f, i, line.strip()))
    print("--- zm() 调用里的中文（应为空）---")
    print("\n".join(bad) if bad else "无")


if __name__ == "__main__":
    path = os.path.join(OUT, NAME + ".mp4")
    if not os.path.exists(path):
        sys.exit("missing %s" % path)
    probe(path)
    frames()
    loud(path)
    stills(path)
    cjk_audit()
