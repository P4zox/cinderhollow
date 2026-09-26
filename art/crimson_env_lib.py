"""Shared palettes + drawing helpers for THE CRIMSON MANOR environment art (gen_crimson_env.py).

A vampiric noble estate hidden underground: violet-black obsidian ashlar, polished black marble, tarnished silver,
deep crimson velvet and damask, dried blood, small warm candle-gold accents. Dark, elegant, restrained.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline

# --------------------------------------------------------------------------- palettes (dark -> light)
ST = ramp("07060a", "0c0911", "110d18", "17121f", "1e1828", "261e32", "2f263d", "3a2f49", "473a55", "574864")
MB = ramp("0b0a0f", "15131b", "1f1c27", "2c2836", "3d3849", "575069", "7a7290")          # polished black marble
SV = ramp("19181c", "2a282e", "3f3c44", "58545c", "77727a", "9a9498", "bdb5b0")          # tarnished silver
BL = ramp("12040a", "22060c", "360910", "4e0c16", "6a111c", "8a1a22", "b02a2c", "d24a3e")  # blood (dried -> fresh)
VV = ramp("14050a", "22070f", "340b16", "4a101e", "641628", "802034", "9e3040")          # crimson velvet
DM = ramp("0e0609", "14080c", "1b0a10", "230d14", "2c1119", "36151e")                    # damask wallpaper (very dark)
WD = ramp("0a0707", "120c0b", "1b1210", "251915", "31211a", "3f2b21", "52392b")          # dark carved wood
IR = ramp("070609", "0e0c11", "16131a", "201c25", "2d2833", "3d3744")                    # wrought iron (violet-black)
GL = ramp("1c130b", "33230f", "4f3816", "6e5020", "8d6a2c", "b08b44", "d4b56e")          # tarnished gilt
WX = ramp("2a080d", "480d15", "6c141c", "8e2026", "b03634")                              # red candle wax
FL = ramp("6a1c08", "b0400e", "e2781c", "ffb648", "ffe7a4")                              # candle flame (warm gold)
SK = ramp("2a2230", "4a3f4a", "72646a", "9c8c8a", "c8b8ae", "e8dccc")                    # pale skin / bone / marble
GR = ramp("100e14", "1c1a22", "2a2733", "3c3946", "524e5c", "6c6878", "8c8898")          # grey stone (statues)
GS = ramp("0e0c14", "1a1726", "2a2540", "3e3860", "5a5484")                              # dark crystal drops


class Spr:
    """Tiny canvas with helpers; draws opaque pixels into an RGBA image."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = blank(w, h)
        self.px = self.img.load()

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return T

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def shaded_rect(self, x0, y0, x1, y1, r, base=3):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                i = base
                if y == y0:
                    i += 2
                elif y == y1:
                    i -= 1
                if x == x0 and y != y0:
                    i += 1
                elif x == x1:
                    i -= 1
                self.set(x, y, r[max(0, min(len(r) - 1, i))])

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.set(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def hline(self, x0, x1, y, c):
        for x in range(int(x0), int(x1) + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            self.set(x, y, c)

    def map(self, ox, oy, rows, key):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in key:
                    self.set(ox + i, oy + j, key[ch])

    def paste(self, img, ox, oy):
        self.img.alpha_composite(img, (int(ox), int(oy)))
        self.px = self.img.load()

    def outline(self, diag=False, col=K):
        self.img = outline(self.img, col, diag=diag)
        self.px = self.img.load()
        return self


def flame(s, cx, base_y, h, w, phase, pal=FL, seed=0, tongue=True):
    """Teardrop flame with a licking tip, flickering with phase (0..1, loops). Clean colour bands."""
    P = phase * 2 * math.pi
    for y in range(int(base_y - h * 1.2) - 2, int(base_y) + 1):
        t = (base_y - y) / h
        if t < 0 or t > 1.2:
            continue
        sway = (math.sin(P + t * 3.2 + seed) * 1.0 + math.sin(2 * P + t * 5 + seed * 2) * 0.45) * t
        body = math.sin(math.pi * min(1.0, 0.2 + t * 0.8)) ** 0.7
        hw = w * body * max(0.0, 1.05 - t) ** 0.6
        hw *= 1 + 0.1 * math.sin(2 * P + seed + t * 4)
        for x in range(int(cx - w - 4), int(cx + w + 5)):
            dx = abs(x + 0.5 - cx - sway)
            if dx > hw:
                continue
            k = 1 - dx / max(hw, 0.4)
            v = 0.15 + 0.55 * k * (1 - 0.6 * t) + 0.35 * (1 - t)
            i = int(clamp(v) * (len(pal) - 1) + 0.5)
            s.set(x, y, pal[min(len(pal) - 1, i)])
    if tongue and math.sin(P + seed) > 0.35:
        tx = cx + math.sin(P + seed) * 1.2
        ty = base_y - h * 1.15 - 1
        s.set(tx, ty, pal[2])


def tiny_flame(s, x, y, f, seed=0):
    """3-4px candle flame for small props: 4 hand-made frames, bottom pixel at (x, y)."""
    k = (f + seed) % 4
    shapes = [
        [(0, 0, 3), (0, -1, 3), (0, -2, 2), (0, -3, 1)],
        [(0, 0, 3), (0, -1, 4), (0, -2, 2), (-1, -1, 1), (0, -3, 1)],
        [(0, 0, 3), (0, -1, 3), (1, -2, 2), (1, -3, 1)],
        [(0, 0, 3), (0, -1, 4), (0, -2, 3), (0, -3, 2), (-1, -4, 1)],
    ]
    for (dx, dy, i) in shapes[k]:
        s.set(x + dx, y + dy, FL[i])


def ellipse_fill(s, cx, cy, rx, ry, fn):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = dx * dx + dy * dy
            if d <= 1:
                c = fn(x, y, dx, dy, d)
                if c is not None:
                    s.set(x, y, c)


def lit(r, v, x, y):
    """Ordered-dither pick in a ramp (v in 0..1)."""
    v = clamp(v)
    f = v * (len(r) - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return r[min(i, len(r) - 1)]


def pixel_clean(img):
    """Force every pixel fully opaque or fully transparent."""
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            c = px[x, y]
            if 0 < c[3] < 255:
                px[x, y] = (c[0], c[1], c[2], 255) if c[3] >= 128 else T
    return img
