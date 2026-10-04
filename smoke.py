# -*- coding: utf-8 -*-
"""Smoke test: render one frame from each of the 24 scenes and report failures."""
import sys
import time
import traceback

from chernobyl import build, theme as T

fail = []
t0 = time.time()
for i in range(T.BARS):
    t1 = time.time()
    try:
        p = build.render_at(i, 1.40, ss=2, name="smoke_%02d.png" % (i + 1))
        print("ok   %02d  %5.2fs  %s" % (i + 1, time.time() - t1, p), flush=True)
    except Exception:
        fail.append(i)
        print("FAIL %02d" % (i + 1), flush=True)
        traceback.print_exc()
print("total %.1fs  failures=%s" % (time.time() - t0, [f + 1 for f in fail]))
sys.exit(1 if fail else 0)
