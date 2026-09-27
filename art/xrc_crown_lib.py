"""Raster helpers for gen_xrc_crown.py (Pale Crown props).

Everything is analytic: shapes are sampled SSxSS per pixel and a pixel is filled on majority
coverage, then a small clean-up pass removes 1px spurs and fills 1px notches, so silhouettes are
hard, clean pixel clusters (no anti-aliasing). Shading is computed at pixel centres and quantised
to a ramp with hard thresholds (clean bands, no dithering).
"""
import math
import numpy as np
from PIL import Image

SS = 4


def hx(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def rp(*hs):
    return [hx(h) for h in hs]


# ------------------------------------------------------------------ shared Crown palette
# (sampled from gilded_sentinel / sun_seraph / root_spawn so props share the enemies' hand)
OUT = hx("0b080c")
IVORY = rp("29201a", "4a3b2c", "76624a", "a38c68", "cbb68b", "ebdfbd", "f5f0e2", "fffbe8")
GOLD = rp("382107", "65400e", "9c6915", "d09a2a", "f0ca58", "ffe890", "fff3b4", "fffbe8")
GREY = rp("27232d", "48434f", "736e79", "a39d9a", "d2cbbd", "f5f0e2")
BRONZE = rp("2a1c14", "4a3020", "6e4a28", "946a34", "b88e44", "dcb45c", "f4dc90")
PETAL = rp("8e8296", "b0a0a8", "cebeb6", "e4d6c2", "f4e8d0", "fffae8")     # lilac-shadowed blossom
SAGE = rp("2e3a34", "46584e", "6a8474", "98b29c", "cfe0c8")                # pale silver-sage
FLAME = rp("d09a2a", "f0ca58", "ffe890", "fff3b4", "fffbe8", "ffffff")
WHITE = hx("ffffff")


# ------------------------------------------------------------------ grids
def grid(w, h, ss=1):
    ys, xs = np.mgrid[0:h * ss, 0:w * ss]
    return (xs + 0.5) / ss, (ys + 0.5) / ss


def coverage(fn, w, h, ss=SS):
    """fn(X, Y) -> bool array; returns per-pixel coverage fraction."""
    X, Y = grid(w, h, ss)
    m = fn(X, Y).astype(np.float32)
    return m.reshape(h, ss, w, ss).mean(axis=(1, 3))


def clean(m, passes=1):
    m = m.copy()
    for _ in range(passes):
        p = np.pad(m, 1)
        n = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        m = np.where(m & (n <= 1), False, m)
        m = np.where(~m & (n >= 3), True, m)
    return m


def mask(fn, w, h, thr=0.5, cl=True):
    m = coverage(fn, w, h) >= thr
    return clean(m) if cl else m


def dilate(m, diag=False):
    p = np.pad(m, 1)
    o = m | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    if diag:
        o = o | p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
    return o


def erode(m):
    return ~dilate(~m)


def edge(m):
    """pixels of m with an orthogonal neighbour outside m"""
    return m & ~erode(m)


# ------------------------------------------------------------------ fields
def seg_field(X, Y, segs):
    """segs: list of (x0, y0, x1, y1, r0, r1).  Returns (d, u, s):
    d = distance - radius (negative inside), u = signed across offset / radius (-1..1, + = right of
    travel direction), s = arc length along the whole polyline at the closest point."""
    d = np.full(X.shape, 1e9, np.float32)
    u = np.zeros(X.shape, np.float32)
    s = np.zeros(X.shape, np.float32)
    acc = 0.0
    for (x0, y0, x1, y1, r0, r1) in segs:
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        L = math.sqrt(L2) if L2 else 1e-6
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / (L2 if L2 else 1e-6), 0, 1)
        px, py = x0 + t * dx, y0 + t * dy
        ex, ey = X - px, Y - py
        dist = np.sqrt(ex * ex + ey * ey)
        r = r0 + (r1 - r0) * t
        dd = dist - r
        better = dd < d
        cr = (dx * ey - dy * ex) / L                 # signed perpendicular offset
        d = np.where(better, dd, d)
        u = np.where(better, np.clip(cr / np.maximum(r, 0.3), -1, 1), u)
        s = np.where(better, acc + t * L, s)
        acc += L
    return d, u, s


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def poly_segs(pts, r0, r1, rfn=None):
    n = len(pts) - 1
    segs = []
    for i in range(n):
        ta, tb = i / n, (i + 1) / n
        ra = rfn(ta) if rfn else r0 + (r1 - r0) * ta
        rb = rfn(tb) if rfn else r0 + (r1 - r0) * tb
        segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], ra, rb))
    return segs


def in_poly(X, Y, poly):
    inside = np.zeros(X.shape, bool)
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if y0 == y1:
            continue
        cond = ((y0 > Y) != (y1 > Y))
        xi = x0 + (Y - y0) * (x1 - x0) / (y1 - y0)
        inside ^= cond & (X < xi)
    return inside


# ------------------------------------------------------------------ light / quantise
LIGHT = np.array([-0.55, -0.7, 0.45])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def tube_light(u, dirx, diry):
    """Lambert for a cylinder: u = across offset (-1..1), (dirx, diry) = travel direction."""
    nx, ny = -diry * u, dirx * u               # across direction (right of travel) scaled by u
    nz = np.sqrt(np.clip(1 - u * u, 0, 1))
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


def q(v, n):
    """quantise 0..1 -> 0..n-1 (hard thresholds)"""
    return np.clip(np.floor(np.asarray(v) * n), 0, n - 1).astype(int)


# ------------------------------------------------------------------ sprite
class Spr:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.c = np.zeros((h, w, 4), np.uint8)
        self.X, self.Y = grid(w, h)

    def opaque(self):
        return self.c[..., 3] > 0

    def paint(self, m, col):
        """col: RGBA tuple, or HxWx4 array, or (ramp, index_array)"""
        if isinstance(col, tuple) and len(col) == 2 and isinstance(col[0], list):
            r, idx = col
            arr = np.array(r, np.uint8)[np.clip(idx, 0, len(r) - 1)]
            self.c[m] = arr[m]
        elif isinstance(col, np.ndarray):
            self.c[m] = col[m]
        else:
            self.c[m] = col

    def ring(self, m, col, diag=False):
        """separation line on already-painted pixels around mask m (drawn before painting m)"""
        r = dilate(m, diag) & ~m & self.opaque()
        self.c[r] = col

    def px(self, x, y, col):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y, x] = col

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(int(v) for v in self.c[y, x])
        return (0, 0, 0, 0)

    def outline(self, col=OUT, diag=False, skip=None):
        o = self.opaque()
        r = dilate(o, diag) & ~o
        if skip is not None:
            r &= ~skip
        self.c[r] = col

    def img(self):
        return Image.fromarray(self.c.copy(), "RGBA")


def to_img(arr):
    return Image.fromarray(arr, "RGBA")


def tube(w, h, segs, thr=0.5, cl=True, pad=2):
    """Evaluate a tube (list of segments) inside its bounding box only.
    Returns (mask HxW bool, u HxW, s HxW) with u/s valid inside the bbox."""
    xs = [v for sg in segs for v in (sg[0] - sg[4], sg[2] - sg[5], sg[0] + sg[4], sg[2] + sg[5])]
    ys = [v for sg in segs for v in (sg[1] - sg[4], sg[3] - sg[5], sg[1] + sg[4], sg[3] + sg[5])]
    x0, x1 = max(0, int(min(xs)) - pad), min(w, int(max(xs)) + pad + 1)
    y0, y1 = max(0, int(min(ys)) - pad), min(h, int(max(ys)) + pad + 1)
    m = np.zeros((h, w), bool)
    U = np.zeros((h, w), np.float32)
    S = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return m, U, S
    bw, bh = x1 - x0, y1 - y0
    ys_, xs_ = np.mgrid[0:bh * SS, 0:bw * SS]
    Xs, Ys = x0 + (xs_ + 0.5) / SS, y0 + (ys_ + 0.5) / SS
    d = seg_field(Xs, Ys, segs)[0]
    cov = (d < 0).astype(np.float32).reshape(bh, SS, bw, SS).mean(axis=(1, 3))
    mm = cov >= thr
    if cl:
        mm = clean(mm)
    m[y0:y1, x0:x1] = mm
    yc, xc = np.mgrid[0:bh, 0:bw]
    _, u, s = seg_field(x0 + xc + 0.5, y0 + yc + 0.5, segs)
    U[y0:y1, x0:x1] = u
    S[y0:y1, x0:x1] = s
    return m, U, S


def bez2(p0, p1, p2, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def polylen(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
