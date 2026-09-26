#!/usr/bin/env python3
"""Necropolis FX (agent N): fx_nv_pillar 24x104, 8 frames (tag nv_pillar, pivot bottom): a column of pale ghost-fire
erupting from a floor sigil -- 0-1 erupt, 2-5 full (flickering), 6-7 gutter out."""
import math, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from envlib import h01, ramp  # noqa: E402

GH = ramp("0b1732", "142c58", "22498a", "3a70c0", "63a0e6", "a2cdf8", "e4f3ff")
W, H = 24, 104


def frame(f):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = im.load()
    grow = (0.35, 0.8, 1, 1, 1, 1, 0.7, 0.35)[f]
    thin = (0.6, 0.9, 1, 1.05, 0.95, 1, 0.7, 0.4)[f]
    top = H - H * grow
    for y in range(H):
        if y < top:
            continue
        t = (H - y) / H
        wob = math.sin(y * 0.22 + f * 1.7) * 1.6 + math.sin(y * 0.07 - f) * 1.2
        half = (4.5 + 3.5 * (1 - t) ** 2) * thin
        if y - top < 10:
            half *= (y - top) / 10
        for x in range(W):
            dx = abs(x + 0.5 - (W / 2 + wob * t))
            if dx > half:
                continue
            r = dx / max(half, 0.5)
            if f >= 6 and h01(x, y, f) < 0.35:
                continue
            if h01(x, y // 2, f) < 0.08 * t and r > 0.4:
                continue
            i = 6 if r < 0.25 else 5 if r < 0.5 else 4 if r < 0.75 else 3 if r < 0.92 else 2
            px[x, y] = GH[i]
    # sigil ring at the base
    for x in range(W):
        if h01(x, 1, f) < 0.7:
            px[x, H - 1] = GH[3 if x % 3 else 5]
    # sparks
    for k in range(6):
        sx = int(W / 2 + (h01(k, f, 3) - 0.5) * 18)
        sy = int(top + h01(k, f, 4) * (H - top) * 0.8)
        if 0 <= sx < W and 0 <= sy < H:
            px[sx, sy] = GH[6]
    return im


frames = [{"ms": (60, 60, 80, 80, 80, 80, 90, 90)[f], "cels": {"FX": frame(f)}} for f in range(8)]
asebuild.build("fx_nv_pillar", W, H, ["FX"], frames, [("nv_pillar", 0, 7)])
print("fx_nv_pillar ok")
