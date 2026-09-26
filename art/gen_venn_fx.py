#!/usr/bin/env python3
"""Sister Venn's effect sheets (agent V).  python3 art/gen_venn_fx.py [--preview]

    fx_vn_pillar     24x104, 8 frames, pivot bottom   shrine-light pillar of pale fire (active 3-5)
    fx_vn_crescent   40x30,  4 frames loop, bottom    crescent of flame that races along the floor (travels right)
    fx_vn_spike      22x72,  8 frames, pivot bottom   a burning root lance bursting from the floor (active 3-5)
    fx_vn_burst      64x64,  8 frames, centred        a bloom of white fire (blink, heal, phase change)
    fx_vn_mark       16x6,   4 frames loop, bottom    floor warning glyph
    fx_vn_wave       28x26,  4 frames loop, bottom    low wall of white-gold fire (slam; travels right)
Palette = art/venn_rig.py HEX (the flame ramp F0-F4/L, embers E, char C).
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
from venn_rig import RGBA, hash01  # noqa: E402

BUILD = "--preview" not in sys.argv
STEPS = (70, 130, 190, 255)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def put(self, x, y, c, a=255):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if a < 255:
                a = min(STEPS, key=lambda s: abs(s - a))
            self.px[(x, y)] = RGBA[c][:3] + (a,)

    def under(self, x, y, c, a=255):
        x, y = int(math.floor(x)), int(math.floor(y))
        if (x, y) not in self.px:
            self.put(x, y, c, a)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        p = im.load()
        for q, c in self.px.items():
            p[q] = c
        return im


def flame_col(v):
    """0 (cool edge) .. 1 (white core)."""
    return "L" if v > 0.9 else "F4" if v > 0.72 else "F3" if v > 0.5 else "F2" if v > 0.3 else "F1" if v > 0.15 else "F0"


def pillar(i):
    w, h = 24, 104
    C = Canvas(w, h)
    grow = [0.08, 0.2, 0.55, 1.0, 1.0, 0.9, 0.55, 0.2][i]
    width = [2, 3, 5, 9, 10, 8, 5, 2][i]
    top = h - grow * h
    cx = w / 2
    for y in range(int(top), h):
        t = (h - y) / h
        wob = math.sin(y * 0.25 + i * 1.7) * 1.2
        ww = width * (0.55 + 0.45 * (1 - t) ** 0.4)
        for x in range(w):
            d = abs(x + .5 - cx - wob * t) / max(0.6, ww)
            if d > 1.0:
                if d < 1.5 and hash01(x, y + i * 7, 3) > 0.7:
                    C.put(x, y, "F2", 130)
                continue
            v = (1 - d) * (0.8 + 0.2 * hash01(x, y // 2 + i, 4)) + (0.25 if i in (3, 4) else 0)
            C.put(x, y, flame_col(min(1, v)), 255 if d < 0.8 else 190)
    # base flare + rising motes
    for k in range(12):
        x = cx + (hash01(k, i, 5) - 0.5) * (8 + width * 1.5)
        y = h - 1 - hash01(k, i, 6) * 4
        C.put(x, y, "F3")
    for k in range(10 if i >= 3 else 3):
        x = cx + (hash01(k, i, 7) - 0.5) * width * 2.2
        y = top + hash01(k, i, 8) * (h - top)
        C.put(x, y - 2, "F4")
    return C


def crescent(i):
    w, h = 40, 30
    C = Canvas(w, h)
    cx, cy = 14, 30
    for y in range(h):
        for x in range(w):
            dx, dy = x + .5 - cx, (y + .5 - cy) * 1.1
            r = math.hypot(dx, dy)
            a = math.atan2(-dy, dx)
            if a < 0.05 or a > 1.75:
                continue
            R = 22 + math.sin(a * 3 + i * 1.6) * 1.0
            th = 5.5 * math.sin(min(math.pi, a / 1.75 * math.pi)) + 0.8
            e = R - r
            if -1 < e < th:
                v = 1 - max(0, e) / th
                v = v * 0.85 + 0.15 * hash01(x, y + i, 9)
                C.put(x, y, flame_col(v), 255 if e < th * 0.7 else 190)
    for k in range(10):
        x = cx - 4 - hash01(k, i, 10) * 14
        y = h - 2 - hash01(k, i, 11) * 14
        C.put(x, y, "F2" if k % 2 else "F3", 190)
    return C


def spike(i):
    w, h = 22, 72
    C = Canvas(w, h)
    grow = [0.0, 0.12, 0.4, 1.0, 1.0, 0.95, 0.7, 0.35][i]
    burn = [0, 0, 0.2, 1, 1, 0.8, 0.4, 0.1][i]
    cx = w / 2
    L = grow * (h - 4)
    # ground glow + cracks
    for x in range(w):
        if hash01(x, i, 12) > 0.3:
            C.put(x, h - 1, "F2" if abs(x - cx) < 6 else "F1", 255 if i < 6 else 190)
    if L < 1:
        for x in range(int(cx - 4), int(cx + 5)):
            C.put(x, h - 2, "F3")
        return C
    for y in range(int(h - L), h):
        t = min(1.0, (h - y) / max(1, L))   # 0 at base .. 1 at the tip
        r = 3.6 * (1 - t) ** 0.8 + 0.4
        bend = math.sin(t * 2.2) * 1.4
        for x in range(w):
            d = (x + .5 - cx - bend) / r
            if abs(d) > 1:
                continue
            shade = 0.5 - d * 0.5
            c = "C4" if shade > 0.8 else "C3" if shade > 0.55 else "C2" if shade > 0.3 else "C1"
            if hash01(x, y // 2, 13) > 0.86:
                c = "E2" if burn > 0.5 else "E1"
            C.put(x, y, c)
        # outline
        for x in (int(cx + bend - r - 1), int(cx + bend + r + 0.5)):
            C.under(x, y, "OUT")
    tip = h - L
    for k in range(int(6 * burn) + 1):
        C.put(cx + (hash01(k, i, 14) - 0.5) * 4, tip - 1 - k * 1.3, "F4" if k < 2 else "F3" if k < 4 else "F2")
    for k in range(int(14 * burn)):
        y = h - hash01(k, i, 15) * L
        C.put(cx + (hash01(k, i, 16) - 0.5) * 8, y, "F2", 190)
    return C


def burst(i):
    w = h = 64
    C = Canvas(w, h)
    k = (i + 1) / 8
    R = 6 + 24 * k ** 0.7
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + .5 - 32, y + .5 - 32)
            if i < 3 and d < 10 * (1 - i / 4):
                C.put(x, y, "L" if d < 5 * (1 - i / 4) else "F4")
            e = abs(d - R)
            if e < 1.5 * (1 - k * 0.5):
                C.put(x, y, "F4" if k < 0.6 else "F3", 255 if k < 0.7 else 190)
            elif e < 3 and hash01(x, y, 17 + i) > 0.6:
                C.under(x, y, "F2", 130 if k < 0.7 else 70)
    for n in range(18):
        a = n / 18 * 6.283 + hash01(n, 1, 18)
        rr = R * (0.6 + 0.6 * hash01(n, i, 19))
        C.put(32 + math.cos(a) * rr, 32 + math.sin(a) * rr - k * 6, "F3" if n % 2 else "F4")
    return C


def mark(i):
    C = Canvas(16, 6)
    for x in range(16):
        v = 0.5 + 0.5 * math.sin(x * 0.9 + i * 1.6)
        C.put(x, 5, "F3" if v > 0.5 else "F2")
        if v > 0.7:
            C.put(x, 4, "F2", 190)
        if v > 0.92:
            C.put(x, 3 - (i % 2), "F3", 130)
    return C


def wave(i):
    w, h = 28, 26
    C = Canvas(w, h)
    for x in range(w):
        t = x / w                       # tail (left) .. front (right)
        hh = (4 + 18 * math.sin(min(math.pi, t * math.pi * 1.1)) ** 0.8) * (0.85 + 0.15 * math.sin(x * 0.8 + i * 2))
        for y in range(int(h - hh), h):
            u = (h - y) / max(1, hh)
            v = (1 - u) * 0.8 + 0.2 * hash01(x, y + i * 5, 20) + (0.2 if t > 0.6 else 0)
            C.put(x, y, flame_col(min(1, v)), 255 if u < 0.8 else 190)
    return C


SHEETS = [("fx_vn_pillar", 24, 104, pillar, 8, "vn_pillar"), ("fx_vn_crescent", 40, 30, crescent, 4, "vn_crescent"),
          ("fx_vn_spike", 22, 72, spike, 8, "vn_spike"), ("fx_vn_burst", 64, 64, burst, 8, "vn_burst"),
          ("fx_vn_mark", 16, 6, mark, 4, "vn_mark"), ("fx_vn_wave", 28, 26, wave, 4, "vn_wave")]
MS = {"fx_vn_pillar": 70, "fx_vn_crescent": 70, "fx_vn_spike": 60, "fx_vn_burst": 55, "fx_vn_mark": 80, "fx_vn_wave": 70}


def main():
    rows = []
    for name, w, h, fn, n, tag in SHEETS:
        frames = [fn(i).image() for i in range(n)]
        rows.append((w, h, frames))
        if BUILD:
            asebuild.build(name, w, h, ["FX"], [{"ms": MS[name], "cels": {"FX": f}} for f in frames], [(tag, 0, n - 1)])
        print("fx", name, n)
    s = 3
    W_ = max(sum(w + 2 for _ in fr) for w, h, fr in rows) * s
    H_ = sum(h + 2 for w, h, fr in rows) * s
    sh = Image.new("RGBA", (W_, H_), (40, 40, 46, 255))
    y = 0
    for w, h, fr in rows:
        for k, f in enumerate(fr):
            bg = Image.new("RGBA", (w, h), (70, 66, 74, 255)); bg.alpha_composite(f)
            sh.alpha_composite(bg.resize((w * s, h * s), Image.NEAREST), (k * (w + 2) * s, y))
        y += (h + 2) * s
    sh.save(os.path.join(ART, "previews", "venn_fx.png"))


if __name__ == "__main__":
    main()
