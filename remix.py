# -*- coding: utf-8 -*-
"""重建配乐，并把新音轨混回已有视频（视频流 -c:v copy，不重编一帧）。"""
import os
import subprocess

import numpy as np

from chernobyl import audio as A
from chernobyl import theme as T

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

st, sr = A.build()
A.write_wav(os.path.join(OUT, "track.wav"), st, sr)
wave, spec = A.analyse(st, sr, fps=T.FPS)
np.save(os.path.join(OUT, "wave.npy"), wave)
np.save(os.path.join(OUT, "spec.npy"), spec)

mono = st.mean(1)


def db(x):
    return 20.0 * np.log10(max(float(x), 1e-9))


print("--- 四幕响度（配乐是否跟着叙事走）---")
for k in range(4):
    a, b = int(k * 6 * T.BAR * sr), int((k + 1) * 6 * T.BAR * sr)
    seg = mono[a:b]
    print("act %d   rms %6.1f dBFS   peak %6.1f dBFS   samples %d"
          % (k + 1, db(seg.std()), db(np.abs(seg).max()), len(seg)))
print("--- 每小节 rms（应为 24 个非零值）---")
bars = [db(mono[int(i * T.BAR * sr):int((i + 1) * T.BAR * sr)].std())
        for i in range(T.BARS)]
print(" ".join("%.0f" % v for v in bars))
print("silent bars:", sum(1 for v in bars if v < -60))

src = os.path.join(OUT, "chernobyl-45s.mp4")
tmp = os.path.join(OUT, "_remix.mp4")
log = open(os.path.join(OUT, "_remix.log"), "w", encoding="utf-8")
try:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src,
                    "-i", os.path.join(OUT, "track.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "384k", "-shortest",
                    "-movflags", "+faststart", tmp],
                   check=True, stdout=log, stderr=subprocess.STDOUT)
finally:
    log.close()
os.replace(tmp, src)
print("remuxed", src, os.path.getsize(src))
