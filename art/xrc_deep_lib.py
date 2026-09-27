"""Drawing helpers for gen_xrc_deep.py (Burning Deep props, xrc_dp_*).

Pixel-clean RGBA drawing: supersampled shape masks with a majority vote (smooth silhouettes, no AA mush),
a top-left bevel lighter, a 1px outliner that keeps glow edges warm, chains, rivets, and a few extra ramps
built to sit next to deep_tiles' ST / MG / IR / GD / CH / ASH.
"""
import math
import numpy as np
from PIL import Image
import deep_tiles as DT
from envlib import K, h01, ramp

ST, MG, IR, GD, CH, ASH = DT.ST, DT.MG, DT.IR, DT.GD, DT.CH, DT.ASH
T = (0, 0, 0, 0)
RU = ramp("24100b", "3b190e", "562612", "743618")                     # rust on the black iron
LE = ramp("120a09", "1e120e", "2d1a13", "40261a", "573524")           # smoke-cured leather
WD = ramp("0c0807", "171009", "22170f", "302015", "422c1c", "5a3c25")  # charred timber (under the char)
HS = ramp("1c1219", "2a1822", "3b202a")                               # heat-tempered iron (bruised violet)
KH = MG[0]                                                             # outline next to molten pixels

HOT = set(MG[2:])


def ss_mask(w, h, fn, ss=4, thr=0.5):
    """Evaluate fn(X, Y) -> bool on an ss x ss subsample grid per pixel; a pixel is in when >= thr are in."""
    ys, xs = np.mgrid[0:h * ss, 0:w * ss]
    X = (xs + 0.5) / ss
    Y = (ys + 0.5) / ss
    m = np.asarray(fn(X, Y), dtype=float)
    return m.reshape(h, ss, w, ss).mean(axis=(1, 3)) >= thr


# ---------------------------------------------------------------- shape functions (X, Y float arrays -> bool)
def ell(cx, cy, rx, ry):
    return lambda X, Y: ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0


def rect(x0, y0, x1, y1):
    """Covers pixels x0..x1, y0..y1 inclusive."""
    return lambda X, Y: (X >= x0) & (X <= x1 + 1) & (Y >= y0) & (Y <= y1 + 1)


def poly(pts):
    P = [(float(a), float(b)) for a, b in pts]

    def fn(X, Y):
        inside = np.zeros(X.shape, dtype=bool)
        n = len(P)
        for i in range(n):
            x1, y1 = P[i]
            x2, y2 = P[(i + 1) % n]
            if y1 == y2:
                continue
            cond = (Y >= min(y1, y2)) & (Y < max(y1, y2))
            xi = x1 + (Y - y1) * (x2 - x1) / (y2 - y1)
            inside ^= cond & (X < xi)
        return inside
    return fn


def capsule(ax, ay, bx, by, r):
    def fn(X, Y):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy or 1e-9
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L, 0, 1)
        return (X - ax - t * dx) ** 2 + (Y - ay - t * dy) ** 2 <= r * r
    return fn


def union(*fs):
    return lambda X, Y: np.logical_or.reduce([f(X, Y) for f in fs])


def minus(a, *bs):
    return lambda X, Y: a(X, Y) & ~np.logical_or.reduce([b(X, Y) for b in bs])


def inter(*fs):
    return lambda X, Y: np.logical_and.reduce([f(X, Y) for f in fs])


# ---------------------------------------------------------------- mask utilities
def nb(m, dx, dy):
    """m sampled at (x+dx, y+dy); False outside."""
    h, w = m.shape
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def bevel(m):
    """Per-pixel light offset for a raised face lit from the upper left: +1 top/left rim, -1 bottom/right rim,
    +2 on the upper-left 'corner' pixels (both up and left open)."""
    up = ~nb(m, 0, -1)
    lf = ~nb(m, -1, 0)
    dn = ~nb(m, 0, 1)
    rt = ~nb(m, 1, 0)
    o = np.zeros(m.shape, dtype=int)
    o[up | lf] += 1
    o[up & lf] += 1
    o[(dn | rt) & ~(up | lf)] -= 1
    o[~m] = 0
    return o


def shrink(m, n=1):
    for _ in range(n):
        m = m & nb(m, 1, 0) & nb(m, -1, 0) & nb(m, 0, 1) & nb(m, 0, -1)
    return m


def grow(m, n=1):
    for _ in range(n):
        m = m | nb(m, 1, 0) | nb(m, -1, 0) | nb(m, 0, 1) | nb(m, 0, -1)
    return m


# ---------------------------------------------------------------- sprite canvas
class Spr:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), T)
        self.px = self.img.load()

    def set(self, x, y, c):
        if c is None:
            return
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return T

    def mask(self, fn, ss=4, thr=0.5):
        return ss_mask(self.w, self.h, fn, ss, thr)

    def fill(self, m, c):
        for y, x in np.argwhere(m):
            self.set(x, y, c(int(x), int(y)) if callable(c) else c)

    def shade(self, m, ramp_, base, extra=None, lo=0, hi=None):
        """Fill mask with ramp_[base + bevel (+ extra(x, y))], clamped."""
        hi = len(ramp_) - 1 if hi is None else hi
        bv = bevel(m)
        for y, x in np.argwhere(m):
            v = base + bv[y, x] + (extra(int(x), int(y)) if extra else 0)
            self.set(x, y, ramp_[int(max(lo, min(hi, v)))])

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1):
            t = i / n
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def paste(self, other, ox=0, oy=0):
        self.img.alpha_composite(other.img if isinstance(other, Spr) else other, (int(ox), int(oy)))

    def occ(self):
        return np.array(self.img)[:, :, 3] > 0

    def copy(self):
        s = Spr(self.w, self.h)
        s.img = self.img.copy()
        s.px = s.img.load()
        return s


def outline(spr, col=K, hot_col=KH, skip=None):
    """1px 4-neighbour outline into transparent pixels. Next to a molten pixel the outline goes dark red so
    glow never sits in a pitch-black ring."""
    a = np.array(spr.img)
    occ = a[:, :, 3] > 0
    src = spr.img.copy().load()
    h, w = occ.shape
    for y in range(h):
        for x in range(w):
            if occ[y, x]:
                continue
            hit = None
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and occ[Y, X]:
                    if skip and (X, Y) in skip:
                        continue
                    c = src[X, Y]
                    if c == col:
                        continue
                    hit = hot_col if (c in HOT and hot_col) else (hit or col)
                    if hit == hot_col:
                        break
            if hit:
                spr.px[x, y] = hit
    return spr


def rivet(spr, x, y, lit=IR[5], dark=IR[0]):
    spr.set(x, y, lit)
    spr.set(x + 1, y + 1, dark)


def chain_v(spr, x, y0, y1, phase=0):
    """2px vertical chain (same pattern as deep_tiles.chain_col)."""
    for y in range(y0, y1):
        k = (y + phase) % 3
        if k == 0:
            spr.set(x, y, IR[4]); spr.set(x + 1, y, IR[2])
        elif k == 1:
            spr.set(x, y, IR[3])
        else:
            spr.set(x, y, IR[5]); spr.set(x + 1, y, IR[3])


def chain_line(spr, x0, y0, x1, y1, phase=0):
    """Chain along an arbitrary line: alternating face-on (2px) and edge-on (1px) links."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    L = math.hypot(x1 - x0, y1 - y0) or 1
    px_, py_ = -(y1 - y0) / L, (x1 - x0) / L         # perpendicular
    ox, oy = (1, 0) if abs(px_) >= abs(py_) else (0, 1)
    for i in range(n + 1):
        t = i / n
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        k = (i + phase) % 3
        if k == 0:
            spr.set(x, y, IR[4]); spr.set(x + ox, y + oy, IR[2])
        elif k == 1:
            spr.set(x, y, IR[3])
        else:
            spr.set(x, y, IR[5]); spr.set(x + ox, y + oy, IR[3])


def glint(spr, x, y, big=False):
    spr.set(x, y, GD[5])
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            spr.set(x + dx, y + dy, GD[4])


def lerp_ramp(r, v):
    return r[int(max(0, min(len(r) - 1, round(v))))]
