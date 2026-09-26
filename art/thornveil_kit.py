"""Thornveil Wood (agent T) -- shared palette + small pixel helpers for the environment/prop/fx generators.

Palette idea: a cold, fog-drowned primeval forest. Near-black loam, dark bark, deep blue-green moss (cooler and
darker than the Mire's yellow-olive), pale bone-white ribbons and skulls, and one accent: green spirit-light.
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
from envlib import C, h01, bt, vnoise, clamp, blank, scale, outline  # noqa: E402,F401

K = C("#08070c")
SOIL = [C(h) for h in ("#0a0a0a", "#121110", "#1a1815", "#23201b", "#2e2922", "#3b342a")]
BARK = [C(h) for h in ("#110d0b", "#1d1611", "#2a2018", "#3a2c21", "#4e3c2c", "#665039", "#80674a")]
MOSS = [C(h) for h in ("#0b1612", "#112219", "#183121", "#20432b", "#2c5a35", "#3e7440", "#5c9150", "#86b068")]
STONE = [C(h) for h in ("#15181a", "#1f2426", "#2b3133", "#3a4142", "#4d5553", "#66706a")]
SPIRIT = [C(h) for h in ("#123c2c", "#1d6644", "#2f9a5e", "#5fe08e", "#b4ffd0", "#f0fff6")]
RIBBON = [C(h) for h in ("#3f3c37", "#5d5a52", "#8f8a7c", "#bcb6a4", "#e2dccb")]
BONE = [C(h) for h in ("#2a2620", "#4a4336", "#7a705c", "#a89d84", "#cfc5aa", "#ece5cf")]
THORN = [C(h) for h in ("#100a09", "#211512", "#36221c", "#4f3228", "#6e4a38", "#a3806a")]
DEEP = [C(h) for h in ("#070c0b", "#0a1110", "#0e1714", "#121e1a", "#172520", "#1d2d27")]   # bg walls
FOG = [C(h) for h in ("#1b2a28", "#2a3c38", "#3d524c", "#5a706a", "#7d918a")]


def ramp_pick(r, v, x, y):
    """Ordered-dither pick from a ramp, v in 0..1."""
    v = clamp(v)
    f = v * (len(r) - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return r[min(i, len(r) - 1)]


def pnoise(x, y, s, seed, per=16):
    """Value noise periodic in both axes with period `per` (s must divide per)."""
    fx, fy = x / s, y / s
    ix, iy = math.floor(fx), math.floor(fy)
    tx, ty = fx - ix, fy - iy
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    n = per // s

    def g(a, b):
        return h01(a % n, b % n, seed)
    a = g(ix, iy) + (g(ix + 1, iy) - g(ix, iy)) * tx
    b = g(ix, iy + 1) + (g(ix + 1, iy + 1) - g(ix, iy + 1)) * tx
    return a + (b - a) * ty


class Pix:
    """A tiny RGBA canvas with bounds-checked set/get."""
    def __init__(self, w, h, img=None):
        self.w, self.h = w, h
        self.img = img or Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return (0, 0, 0, 0)

    def on(self, x, y):
        return self.get(x, y)[3] > 0

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r:
                    self.set(x, y, c)


def curve_pts(pts, n=10):
    """Catmull-Rom through pts -> dense list."""
    if len(pts) < 3:
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        m = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 2
        return [(x0 + (x1 - x0) * i / m, y0 + (y1 - y0) * i / m) for i in range(m + 1)]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        m = max(n, int(seg * 2))
        for k in range(m):
            t = k / m
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def stroke(pix, pts, r0, r1, colfn, n=10):
    """Thick shaded stroke along a curve: colfn(t, side) -> colour; side in -1..1 across the stroke."""
    cp = curve_pts(pts, n)
    L = len(cp)
    for i, (x, y) in enumerate(cp):
        t = i / max(1, L - 1)
        r = r0 + (r1 - r0) * t
        # tangent
        a = cp[max(0, i - 1)]
        b = cp[min(L - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        nx, ny = -ty / l, tx / l
        steps = max(1, int(r * 2 + 1))
        for k in range(steps + 1):
            s = -1 + 2 * k / steps if steps else 0
            px, py = x + nx * s * r, y + ny * s * r
            # light from the upper-left: the side whose normal points up-left is lit
            lit = -(nx * s * 0.6 + ny * s * 0.8)
            pix.set(math.floor(px), math.floor(py), colfn(t, lit))


def save_prev(img, name, k=4, bg=(70, 70, 76, 255)):
    out = Image.new("RGBA", img.size, bg)
    out.alpha_composite(img)
    scale(out, k).save(os.path.join(ART, "previews", name))


def strip(frames, gap=2, bg=(70, 70, 76, 255)):
    w = sum(f.size[0] + gap for f in frames)
    h = max(f.size[1] for f in frames)
    out = Image.new("RGBA", (w, h), bg)
    x = 0
    for f in frames:
        out.alpha_composite(f, (x, 0))
        x += f.size[0] + gap
    return out
