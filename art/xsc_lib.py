"""Shared pixel helpers for agent SC's art (Expansion 3: Starfall, NEO-HALLOW, The Ember, The Hermit's Hollow).
Built on envlib (ordered-dither ramps, value noise, outliner). Everything draws into RGBA PIL images, pixel-clean."""
import math
from PIL import Image
from envlib import C, ramp, K, T, h01, clamp, blank, outline, pick, bt, vnoise, lerpc

# ---------------------------------------------------------------- palettes
OB = ramp("05050b", "0a0b16", "11132a", "191d3c", "232a52", "303a6a", "44518a", "6476b4", "9aaee4")   # obsidian / star-glass
GL = ramp("0a1030", "142050", "1f3274", "2e4a9c", "4a6cc4", "7a9ae6", "b8ccff", "eef4ff")                # lit glass
STONE = ramp("16171f", "23242f", "33353f", "484a55", "60636e", "7c808a", "9ca0a8", "c2c4c8")
PALESTONE = ramp("1c1c24", "2c2c36", "40404c", "585866", "727282", "9090a0", "b2b2c0", "d6d6e0")
BRASS = ramp("1e140c", "3a2614", "5e3e1a", "8a6024", "b48434", "d8aa4c", "f4d27e")
STAR = [C("1c2c66"), C("3e5cc0"), C("7c9cf0"), C("c4d6ff"), C("ffffff")]
VIOLET = ramp("1a0e30", "34205e", "5a3a9a", "8a66d0", "c0a4f4", "ece0ff")
# neon city
NV = ramp("03040a", "070913", "0d1120", "161c33", "222b4a", "34416a", "4c5c8a")
CY = ramp("06202e", "0b4d66", "13a3c9", "3fe0ff", "b8f6ff", "f2feff")
MG = ramp("2a0624", "6e0f5c", "c21d97", "ff3fc0", "ff9fe2", "fff0fb")
AMB = ramp("3a1e06", "7a4410", "c87a20", "ffb050", "ffe0a0", "fffaf0")
RUST = ramp("1a0e0a", "2e1a12", "4a2a1a", "6e3e22", "8e5a32", "b07a48")
STEEL = ramp("0c0e14", "181c26", "262c3a", "384052", "505a70", "727e96", "a0aabc")
# ember
ASH = ramp("0c0908", "171210", "221b18", "2e2622", "3c332e", "4c423c", "625650", "7e726a", "a09488")
CHAR = ramp("060403", "0e0907", "171009", "22170f", "2e2016", "3c2a1c")
FIRE = ramp("3a0a04", "7a1a06", "c03a0e", "ee6a1a", "ff9a36", "ffc46a", "ffe6a8", "fffbe8")
# hermit
WOOD = ramp("140c08", "24160e", "382216", "4e3220", "684430", "86583c", "a8744e")
THATCH = ramp("1c160c", "2e2414", "443620", "5e4a2c", "7a6238", "9a7e4a", "bca064")
MOSS = ramp("121a0e", "1e2c16", "2c4020", "3e562a", "566e36", "728a46")
PAPER = ramp("5a4a36", "8a7456", "b89e76", "dcc6a0", "f4e6c8")
CLAY = ramp("241410", "3e2218", "5a3222", "7a4630", "9c6040", "be8058")


def put(img, x, y, c):
    x, y = int(x), int(y)
    if c is not None and 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((x, y), c)


def get(img, x, y):
    x, y = int(x), int(y)
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        return img.getpixel((x, y))
    return T


def poly_pts(pts):
    ys = [p[1] for p in pts]
    res = set()
    n = len(pts)
    for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 1):
        cy = y + 0.5
        xi = []
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            if (y1 <= cy < y2) or (y2 <= cy < y1):
                xi.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
        xi.sort()
        for a, b in zip(xi[::2], xi[1::2]):
            for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                res.add((x, y))
    return res


def poly(img, pts, fn):
    """fill a polygon; fn(x, y) -> colour (or a constant colour)"""
    for (x, y) in poly_pts(pts):
        put(img, x, y, fn(x, y) if callable(fn) else fn)


def facet(img, pts, rp, lit, seed=0, jitter=0.06):
    for (x, y) in poly_pts(pts):
        put(img, x, y, pick(rp, clamp(lit + jitter * (h01(x, y, seed) - 0.5)), x, y))


def line(img, a, b, c, w=1):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for dx in range(w):
            put(img, round(x) + dx - w // 2, round(y), c)


def rect(img, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            put(img, x, y, c(x, y) if callable(c) else c)


def ell(img, cx, cy, rx, ry, fn):
    """filled ellipse; fn(nx, ny, x, y) -> colour or None (nx, ny in -1..1)"""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1:
                c = fn(nx, ny, x, y) if callable(fn) else fn
                if c is not None:
                    put(img, x, y, c)


def star(img, x, y, big=False):
    put(img, x, y, STAR[4])
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(img, x + dx, y + dy, STAR[3] if big else STAR[2])
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            put(img, x + dx, y + dy, STAR[1])


def shade_box(img, x0, y0, x1, y1, rp, base=0.5, grad=0.25, seed=0, rim=True):
    """a block lit from the upper-left: vertical gradient, bright top rim, dark bottom/right"""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = base + grad * (0.5 - (y - y0) / max(1, y1 - y0)) - 0.12 * (x - x0) / max(1, x1 - x0)
            v += 0.05 * (h01(x, y, seed) - 0.5)
            if rim and y == y0: v += 0.22
            if rim and (x == x1 or y == y1): v -= 0.15
            if rim and x == x0: v += 0.08
            put(img, x, y, pick(rp, v, x, y))


def glow_copy(img, col, grow=1):
    """a flat silhouette of img's bright pixels (luma > .55), grown by `grow` px: the additive glow layer"""
    w, h = img.size
    out = blank(w, h)
    src = img.load()
    hot = [(x, y) for y in range(h) for x in range(w) if src[x, y][3] and (src[x, y][0] * 0.3 + src[x, y][1] * 0.5 + src[x, y][2] * 0.2) > 150]
    for (x, y) in hot:
        for dy in range(-grow, grow + 1):
            for dx in range(-grow, grow + 1):
                if abs(dx) + abs(dy) <= grow:
                    put(out, x + dx, y + dy, col)
    return out


def dither_alpha(img, a, seed=0):
    """ordered-dither an image to ~a opacity (pixel-clean translucency)"""
    w, h = img.size
    out = blank(w, h)
    for y in range(h):
        for x in range(w):
            c = img.getpixel((x, y))
            if c[3] and a > bt(x + seed, y):
                out.putpixel((x, y), c)
    return out
