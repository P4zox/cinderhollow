"""Shared helpers for the environment generators (gen_env.py, env_*.py).

Pixel-clean drawing on RGBA PIL images: ordered-dither ramp picking, tileable value noise,
a wrapping canvas, shape rasterisers and a 1px outliner.
"""
import math, random
from PIL import Image

T = (0, 0, 0, 0)
K = (8, 7, 12, 255)


def C(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def ramp(*hexes):
    return [C(h) for h in hexes]


B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bt(x, y):
    return (B4[int(y) & 3][int(x) & 3] + 0.5) / 16.0


def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def pick(r, v, x, y):
    """Ordered-dither pick from a ramp, v in 0..1."""
    v = clamp(v)
    f = v * (len(r) - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return r[min(i, len(r) - 1)]


def pick_i(n, v, x, y):
    v = clamp(v)
    f = v * (n - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return min(i, n - 1)


def h01(ix, iy, seed=0):
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65535.0


def vnoise(x, y, sx, sy, seed, period=None):
    """Value noise. period = number of cells before wrapping in x (for tileable layers)."""
    fx, fy = x / sx, y / sy
    ix, iy = math.floor(fx), math.floor(fy)
    tx, ty = fx - ix, fy - iy
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)

    def g(a, b):
        if period:
            a %= period
        return h01(a, b, seed)
    a = g(ix, iy) + (g(ix + 1, iy) - g(ix, iy)) * tx
    b = g(ix, iy + 1) + (g(ix + 1, iy + 1) - g(ix, iy + 1)) * tx
    return a + (b - a) * ty


def fbm(x, y, sx, sy, seed, W=512, octaves=3):
    """Tileable (in x, width W) fractal noise; sx must divide W for every octave."""
    v, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        p = W // sx
        v += vnoise(x, y, sx, sy, seed + o * 17, p) * amp
        tot += amp
        amp *= 0.5
        sx = max(1, sx // 2)
        sy = max(1, sy / 2)
    return v / tot


def smooth(e0, e1, v):
    t = clamp((v - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def lerpc(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


class Canvas:
    def __init__(self, w, h, fill=T, wrap=False):
        self.w, self.h, self.wrap = w, h, wrap
        self.img = Image.new("RGBA", (w, h), fill)
        self.px = self.img.load()

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if self.wrap:
            x %= self.w
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        if self.wrap:
            x %= self.w
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return T

    def opaque(self, x, y):
        return self.get(x, y)[3] > 0

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def paste(self, img, ox, oy):
        p = img.load()
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                c = p[x, y]
                if c[3]:
                    self.set(ox + x, oy + y, c)


def outline(img, col=K, wrap=False, diag=False):
    """Add a 1px outline around opaque pixels (into transparent pixels)."""
    w, h = img.size
    src = img.load()
    out = img.copy()
    op = out.load()
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in nb:
                X, Y = x + dx, y + dy
                if wrap:
                    X %= w
                if 0 <= X < w and 0 <= Y < h and src[X, Y][3] and src[X, Y] != col:
                    op[x, y] = col
                    break
    return out


def blank(w, h):
    return Image.new("RGBA", (w, h), T)


def comp(dst, src, ox=0, oy=0):
    """Alpha-composite src onto dst (both RGBA) in place at offset."""
    dst.alpha_composite(src, (int(ox), int(oy)))
    return dst


def scale(img, k):
    return img.resize((img.size[0] * k, img.size[1] * k), Image.NEAREST)
