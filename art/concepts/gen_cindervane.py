#!/usr/bin/env python3
"""CONCEPT v3 -- "Cindervane, the Stormbound Drake" (Tempest Spire main boss).  Rewritten from the user's
reference painting (ref_cindervane.png); v2 kept as gen_cindervane_v2.py / cindervane_v2.png.

    python3 art/concepts/gen_cindervane.py                    full sheet + frames + closeups
    python3 art/concepts/gen_cindervane.py quick roar,idle    1x frames only (fast iteration)

Outputs (art/concepts/):  cindervane.png (sheet, 2x, knight for scale), cindervane_<pose>.png (1x frames),
                          cindervane_closeup.png (3x head closeups)

Design: a massive, heavily ARMOURED storm dragon.  One SPINE CURVE (centripetal Catmull-Rom through keyed
joints with dorsal/ventral radii) is swept into a tube: tail + torso + thick neck share one surface with
per-pixel normal, arc length and lateral coordinate.  Armour is a SHINGLED SCUTE FIELD laid in that
(arc, lateral) space: staggered rows of jagged, back-pointing, keeled plates; head-ward / dorsal plates
overlap the ones behind, every plate is split along its keel into a lit and a shadowed facet (crisp
obsidian read, not noise), occluded edges drop a 1px contact shadow and free tips catch a highlight.
Lightning is PATH-TRACED THROUGH THE SEAMS between plates (shortest random path over seam pixels) with
a 1px soft halo, and branches across the wing membranes.  Parts hung off the curve / keyed joints:
dorsal + flank spike rows, spiked tail club, four armoured legs (2-bone IK, clawed feet), wing-arms
(tattered membranes, clawed finger bones), and an angular faceted horned head with hinged jaw.
Poses are dicts of joints (animatable).  Faces RIGHT.  Frame 288x176.
"""
import heapq, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

W, H = 288, 176
YY, XX = np.mgrid[0:H, 0:W]
PX, PY = XX + 0.5, YY + 0.5


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# =========================================================================== palette
RAMPS = {
    # armour scutes: stone-grey / charcoal obsidian, cool
    "A": ["#060609", "#0c0c11", "#14141a", "#1d1d24", "#27272f", "#33333b", "#42424a", "#55545b", "#6d6b70", "#8c898b"],
    # under-hide between plates / skin: near-black charcoal
    "H": ["#050508", "#09090d", "#0f0f14", "#16161c", "#1f1f26", "#2a2a31", "#36363d"],
    # ventral plates (throat / belly bands): ashen slate
    "P": ["#0e0e12", "#16161b", "#202026", "#2b2a30", "#38363b", "#474449", "#59555a"],
    # spikes & horns: obsidian roots -> pale stone tips
    "S": ["#07070a", "#0e0e13", "#18181e", "#24242b", "#33333a", "#46454b", "#5d5b60", "#7a7679", "#9d9899"],
    # bone: teeth, claws
    "B": ["#141215", "#262227", "#3d383b", "#5a5456", "#7f7777", "#a79e9a", "#cfc7bd", "#ece6da"],
    # wing membrane: dark umber-grey, backlit
    "M": ["#08070a", "#0e0b0f", "#151015", "#1c161b", "#241c22", "#2d232a", "#382c33", "#45373e", "#54434a"],
    # mouth interior
    "K": ["#07050a", "#120b14", "#1e1220", "#2c1a2d"],
}
STORM = ["#0b1a3a", "#12306a", "#1c4fa6", "#2f7ae0", "#5aa8ff", "#a4d6ff", "#eef9ff"]
OUT = "#040407"
RIM = ["#1a2640", "#22324f", "#2c4268", "#6a98d8"]

MATS = list(RAMPS)
MI = {m: i for i, m in enumerate(MATS)}
RAMP_RGB = {m: np.array([hexc(c) for c in r], dtype=np.uint8) for m, r in RAMPS.items()}

LIGHT = np.array([-0.55, -0.70, 0.46]); LIGHT /= np.linalg.norm(LIGHT)
RIMDIR = np.array([0.80, -0.60])  # storm light from behind / upper right (2D)


# =========================================================================== geometry
def v2(a):
    return np.asarray(a, dtype=float)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rotv(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def hash01(x, y, k=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def catmull(keys, per=24):
    """Centripetal Catmull-Rom through keys (rows: x, y, extra...).  Returns dense (N, k) array."""
    K = v2(keys)
    P = np.vstack([2 * K[0] - K[1], K, 2 * K[-1] - K[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        def tj(ti, a, b):
            return ti + max(1e-3, np.hypot(*(b[:2] - a[:2]))) ** 0.5
        t0 = 0.0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        for t in np.linspace(t1, t2, per, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(K[-1])
    return np.array(out)


def resample(D, step=0.4):
    seg = np.hypot(*np.diff(D[:, :2], axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    ss = np.arange(0, s[-1] + 1e-6, step)
    R = np.stack([np.interp(ss, s, D[:, k]) for k in range(D.shape[1])], axis=1)
    return R, ss


def qbez(p0, p1, p2, n=40):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = v2(p0), v2(p1), v2(p2)
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def pp_pixels(pts):
    """Pixel-perfect 1px stroke through dense points (no L-corners)."""
    px = []
    for x, y in pts:
        q = (int(math.floor(x)), int(math.floor(y)))
        if not px or px[-1] != q:
            if px and abs(px[-1][0] - q[0]) > 1 or px and abs(px[-1][1] - q[1]) > 1:
                a = px[-1]
                n = max(abs(q[0] - a[0]), abs(q[1] - a[1]))
                for k in range(1, n):
                    px.append((round(a[0] + (q[0] - a[0]) * k / n), round(a[1] + (q[1] - a[1]) * k / n)))
            px.append(q)
    out = []
    i = 0
    while i < len(px):
        if 0 < i < len(px) - 1 and out:
            a, b, c = out[-1], px[i], px[i + 1]
            if abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and (a[0] == b[0] or a[1] == b[1]):
                i += 1
                continue
        out.append(px[i])
        i += 1
    return out


def poly_mask(pts):
    pts = v2(pts)
    m = np.zeros((H, W), bool)
    n = len(pts)
    y0 = max(0, int(math.floor(pts[:, 1].min())) - 1); y1 = min(H - 1, int(math.ceil(pts[:, 1].max())) + 1)
    for y in range(y0, y1 + 1):
        cy = y + 0.5
        xi = []
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
            if (ya <= cy < yb) or (yb <= cy < ya):
                xi.append(xa + (cy - ya) * (xb - xa) / (yb - ya))
        xi.sort()
        for a, b in zip(xi[::2], xi[1::2]):
            xa_, xb_ = max(0, int(math.ceil(a - 0.5))), min(W - 1, int(math.floor(b - 0.5)))
            if xb_ >= xa_:
                m[y, xa_:xb_ + 1] = True
    return m


def ell_mask(c, rx, ry, ang=0.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    dx, dy = PX - c[0], PY - c[1]
    u, v = dx * ca + dy * sa, -dx * sa + dy * ca
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1.0


def shift(m, dx, dy):
    o = np.zeros_like(m)
    ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy))
    xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
    o[ys, xs] = m[yd, xd]
    return o


def dil4(m):
    return m | shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)


def n4(m):
    return (shift(m, 1, 0).astype(int) + shift(m, -1, 0) + shift(m, 0, 1) + shift(m, 0, -1))


def clean(m, it=2):
    """Remove 1px spurs and fill 1px notches so curves stay smooth."""
    for _ in range(it):
        k = n4(m)
        m = (m & (k >= 2)) | (~m & (k >= 3))
    return m


def dist_to(pts, mask=None):
    """Distance from every pixel to a set of points (N,2)."""
    pts = v2(pts)
    d = np.full((H, W), 1e9)
    for x, y in pts[:: max(1, len(pts) // 400)]:
        d = np.minimum(d, (PX - x) ** 2 + (PY - y) ** 2)
    return np.sqrt(d)


# =========================================================================== tube (the core primitive)
class Tube:
    """Swept tube along dense samples S (x, y, rd, rv).  rd = dorsal (left-of-travel) radius, rv = ventral."""

    def __init__(self, keys, per=24, step=0.4, flat=1.0, minr=0.55, clean_it=2):
        D = catmull(keys, per) if len(keys) > 2 else np.vstack([np.linspace(keys[0][k], keys[1][k], 40)
                                                                 for k in range(len(keys[0]))]).T
        S, s = resample(D, step)
        self.S, self.s = S, s
        T = np.gradient(S[:, :2], axis=0)
        T /= np.maximum(1e-6, np.hypot(T[:, 0], T[:, 1]))[:, None]
        self.T = T
        self.N = np.stack([-T[:, 1], T[:, 0]], axis=1)  # ventral side (right of travel, i.e. down when heading right)
        best = np.full((H, W), 9.0)
        OX = np.zeros((H, W)); OY = np.zeros((H, W)); RR = np.ones((H, W)); LAT = np.zeros((H, W))
        IDX = np.zeros((H, W), int)
        for i in range(len(S)):
            x, y, rd, rv = S[i, :4]
            r = max(rd, rv, minr)
            x0, x1 = max(0, int(x - r - 2)), min(W, int(x + r + 3))
            y0, y1 = max(0, int(y - r - 2)), min(H, int(y + r + 3))
            if x0 >= x1 or y0 >= y1:
                continue
            ox = PX[y0:y1, x0:x1] - x; oy = PY[y0:y1, x0:x1] - y
            l = ox * self.N[i, 0] + oy * self.N[i, 1]
            rs = np.maximum(np.where(l < 0, rd, rv), minr)
            q = np.hypot(ox, oy) / rs
            b = best[y0:y1, x0:x1]
            upd = q < b
            b[upd] = q[upd]
            OX[y0:y1, x0:x1][upd] = ox[upd]; OY[y0:y1, x0:x1][upd] = oy[upd]
            RR[y0:y1, x0:x1][upd] = rs[upd]; LAT[y0:y1, x0:x1][upd] = (l / rs)[upd]
            IDX[y0:y1, x0:x1][upd] = i
        m = best <= 1.0
        # thin ends: guarantee a connected 1px core where the tube is sub-pixel
        thin = np.maximum(S[:, 2], S[:, 3]) < 1.6
        if thin.any():
            for (px_, py_) in pp_pixels(S[thin, :2]):
                if 0 <= px_ < W and 0 <= py_ < H and m[py_, px_]:
                    best[py_, px_] = min(best[py_, px_], 0.3)
                elif 0 <= px_ < W and 0 <= py_ < H:
                    m[py_, px_] = True
                    best[py_, px_] = 0.3
                    IDX[py_, px_] = int(np.argmin(np.hypot(S[:, 0] - px_ - .5, S[:, 1] - py_ - .5)))
                    OX[py_, px_] = OY[py_, px_] = 0
        if clean_it:
            m2 = clean(m, clean_it)
            # keep 1px cores alive
            m = m2 | (m & (best < 0.35))
        self.mask = m
        nx, ny = OX / RR * flat, OY / RR * flat
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.06, 1))
        self.nrm = np.stack([nx, ny, nz], axis=-1)
        self.nrm /= np.linalg.norm(self.nrm, axis=-1, keepdims=True)
        self.lat = LAT
        self.rad = RR
        self.lpx = LAT * RR
        self.idx = IDX
        self.arc = s[IDX]

    def at(self, s_):
        """Point, tangent, ventral normal, radii at arc length s_."""
        i = int(np.clip(np.searchsorted(self.s, s_), 0, len(self.s) - 1))
        return self.S[i, :2], self.T[i], self.N[i], self.S[i, 2], self.S[i, 3]

    @property
    def length(self):
        return self.s[-1]


def cap(a, b, r0, r1, bulge=0.0, bend=0.0, bt=0.5, **kw):
    """Tapered (optionally bent / bulging) limb segment as a Tube.  bend = sideways offset of the midpoint."""
    a, b = v2(a), v2(b)
    d = b - a
    nrm = np.array([-d[1], d[0]]) / (np.hypot(*d) or 1)
    mid = (a + b) / 2 + nrm * bend
    keys = []
    for t in np.linspace(0, 1, 7):
        p = (1 - t) ** 2 * a + 2 * (1 - t) * t * mid + t * t * b
        r = r0 + (r1 - r0) * t + bulge * math.sin(math.pi * t ** (math.log(0.5) / math.log(bt)))
        keys.append((p[0], p[1], r, r))
    return Tube(keys, **kw)




def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def unit(v):
    v = v2(v)
    return v / (np.hypot(*v) or 1)


def dense_stroke(pts):
    """Clip a pixel-perfect stroke to the frame."""
    return [p for p in pp_pixels(pts) if 0 <= p[0] < W and 0 <= p[1] < H]


# =========================================================================== canvas
class Canvas:
    def __init__(self):
        self.mat = np.full((H, W), -1)
        self.nrm = np.zeros((H, W, 3)); self.nrm[..., 2] = 1
        self.bias = np.zeros((H, W))
        self.lvl = np.full((H, W), -1)       # direct level (flat materials); -1 = use lighting
        self.fixed = np.full((H, W), -1)      # index into fixed colours
        self.pid = np.zeros((H, W), int)
        self.line = np.zeros((H, W), bool)    # interior contour (sel-out dark line)
        self.rim = np.zeros((H, W), bool)
        self.seam = np.zeros((H, W), bool)    # cracks between armour plates (lightning runs here)
        self.depth = np.zeros((H, W))         # 0 near .. 1 far (for lightning strength)
        self.n = 0
        self.fixed_cols = []

    def fx(self, col):
        if col not in self.fixed_cols:
            self.fixed_cols.append(col)
        return self.fixed_cols.index(col)

    def filled(self):
        return self.mat >= 0

    def paint(self, mask, nrm, mat, bias=0.0, seam=True, rim=True, lvl=None, far=0.0):
        mask = mask.copy()
        self.n += 1
        if seam:
            s = dil4(mask) & ~mask & self.filled()
            if seam == "soft":
                s &= self.mat != MI["H"]
            self.line |= s
        self.mat[mask] = MI[mat]
        if nrm is None:
            self.nrm[mask] = (0, 0, 1)
        else:
            self.nrm[mask] = nrm[mask]
        self.bias[mask] = bias[mask] if isinstance(bias, np.ndarray) else bias
        self.lvl[mask] = lvl[mask] if isinstance(lvl, np.ndarray) else (-1 if lvl is None else lvl)
        self.fixed[mask] = -1
        self.pid[mask] = self.n
        self.line[mask] = False
        self.seam[mask] = False
        self.rim[mask] = rim
        self.depth[mask] = far
        return mask

    def put(self, pixels, col, only=None):
        k = self.fx(col)
        if isinstance(pixels, np.ndarray):
            m = pixels & self.filled()
            if only is not None:
                m &= only
            self.fixed[m] = k
            return
        for x, y in pixels:
            if 0 <= x < W and 0 <= y < H and self.mat[y, x] >= 0 and (only is None or only[y, x]):
                self.fixed[y, x] = k

    def put_any(self, pixels, col):
        k = self.fx(col)
        self.n += 1
        for x, y in pixels:
            if 0 <= x < W and 0 <= y < H:
                if self.mat[y, x] < 0:
                    self.mat[y, x] = MI["H"]
                    self.rim[y, x] = False
                self.fixed[y, x] = k
                self.line[y, x] = False

    def is_glow(self):
        g = np.zeros((H, W), bool)
        for k, c in enumerate(self.fixed_cols):
            if c in STORM:
                g |= self.fixed == k
        return g

    # ------------------------------------------------------------------ resolve
    def render(self, outline=True):
        img = np.zeros((H, W, 4), np.uint8)
        filled = self.filled()
        ndl = (self.nrm * LIGHT).sum(-1)
        level = np.zeros((H, W), int)
        for m in MATS:
            sel = self.mat == MI[m]
            if not sel.any():
                continue
            top = len(RAMPS[m]) - 1
            v = 0.08 + 0.92 * np.clip(ndl, 0, 1)
            if m in ("A", "H", "P"):
                f = v * top * 1.0 + 0.1 + (100 - PY) * 0.0045
            elif m in ("B", "S"):
                f = v * (top - 0.3) + 0.3
            else:
                f = v * top
            f = f + self.bias
            L = np.clip(np.floor(f), 0, top).astype(int)
            L = np.where(self.lvl >= 0, np.clip(self.lvl, 0, top), L)
            level[sel] = L[sel]
        for _ in range(2):   # speckle cleanup within a part
            same = [(shift(level, dx, dy), shift(self.pid, dx, dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            agree = np.ones((H, W), bool)
            ref = same[0][0]
            for lv, pd in same:
                agree &= (pd == self.pid) & (lv == ref)
            fix = agree & (ref != level) & filled & (self.lvl < 0) & ~self.seam
            level = np.where(fix, ref, level)
        level = np.where(self.line, np.minimum(level, np.where(level > 3, 1, 0)), level)
        for m in MATS:
            sel = (self.mat == MI[m])
            img[sel, :3] = RAMP_RGB[m][np.clip(level[sel], 0, len(RAMPS[m]) - 1)]
        img[filled, 3] = 255
        empty = ~filled
        edge_r = filled & (shift(empty, -1, 0) | shift(empty, 0, 1) | shift(empty, -1, 1))
        face = self.nrm[..., 0] * RIMDIR[0] + self.nrm[..., 1] * RIMDIR[1]
        rimsel = edge_r & self.rim & (face > 0.62) & (self.nrm[..., 1] < 0.2) & ~self.line
        img[rimsel, :3] = np.where((face[rimsel] > 0.75)[:, None], np.array(hexc(RIM[2])), np.array(hexc(RIM[1])))
        edge_b = filled & shift(empty, 0, -1) & (self.nrm[..., 1] > 0.45) & ~self.line & self.rim
        img[edge_b & ((self.mat == MI["A"]) | (self.mat == MI["H"])), :3] = np.array(hexc("#1a2233"))
        for k, c in enumerate(self.fixed_cols):
            img[self.fixed == k, :3] = np.array(hexc(c))
        if outline:
            ring = dil4(filled) & ~filled
            img[ring] = (*hexc(OUT), 255)
        return Image.fromarray(img)


class FX:
    """Unoutlined glow overlay (lightning, eye glow, sparks)."""

    def __init__(self):
        self.img = np.zeros((H, W, 4), np.uint8)

    def put(self, pts, col, only_empty=False, alpha=255):
        c = hexc(col)
        for x, y in pts:
            if 0 <= x < W and 0 <= y < H:
                if only_empty and self.img[y, x, 3]:
                    continue
                self.img[y, x] = (*c, alpha)

    def put_mask(self, m, col, alpha=255):
        self.img[m] = (*hexc(col), alpha)

    def image(self):
        return Image.fromarray(self.img)


# =========================================================================== armour: shingled scute field
def scutes(C, tb, mask, rows=3.0, pu_k=0.62, pu_min=3.2, pu_max=9.0, bias=0.0, seed=0, lift=0.18, far=0.0,
           facet=0.55, var=0.5, mat="A", keep_seam=True):
    """Lay staggered rows of keeled, back-pointing plates over `mask` in the tube's (arc, lateral) space.

    rows = plate rows per half-girth (so plates scale with the body's thickness); column pitch along the
    arc = clip(radius * pu_k).  Head-ward and dorsal plates overlap the ones behind/below them."""
    rng_ = np.random.RandomState(seed)
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return None
    # warped arc coordinate: plates per px follows 1/pitch(radius)
    rS = np.maximum(tb.S[:, 2], tb.S[:, 3])
    pitch = np.clip(rS * pu_k, pu_min, pu_max)
    g = np.concatenate([[0], np.cumsum(np.diff(tb.s) / pitch[1:])])
    idx = tb.idx[ys, xs]
    U = g[idx]
    V = tb.lat[ys, xs] * rows            # rows per half girth, 0 = spine line
    ri0 = np.floor(V).astype(int)
    best_p = np.full(len(ys), -1e9); best_id = np.full(len(ys), -1, np.int64)
    best_t = np.zeros(len(ys)); best_dv = np.zeros(len(ys)); best_hw = np.ones(len(ys))
    for dr in (-1, 0, 1):
        ri = ri0 + dr
        stag = (ri % 2) * 0.5
        ci0 = np.floor(U - stag).astype(int)
        for dc in (-1, 0, 1, 2):
            ci = ci0 + dc
            key = (ci + 5000) * 211 + (ri + 500) + seed * 1000003
            jx = (np.vectorize(hash01)(ci, ri, seed) - 0.5) * 0.30
            jy = (np.vectorize(hash01)(ci, ri, seed + 5) - 0.5) * 0.22
            cu = ci + stag + 0.5 + jx
            cv = ri + 0.5 + jy
            du = U - cu; dv = V - cv
            a, b = 0.98, 0.42                      # tip reaches back into the plate behind, root under the next
            t = (b - du) / (a + b)
            prof = np.where(t < 0.38, 1.0 - ((0.38 - t) / 0.38) ** 2 * 0.35, ((1 - t) / 0.62).clip(0, 1) ** 0.9)
            hw = 0.60 * prof
            dvc = dv + lift * t * t * np.sign(cv + 1e-3) * -1    # tips flare out toward the spine / belly edge
            cov = (t >= 0) & (t <= 1) & (np.abs(dvc) < hw)
            pr = cu - cv * 0.28 * np.sign(cv + 1e-3) * -1 * 0 + (-np.abs(cv)) * 0.30
            upd = cov & (pr > best_p)
            best_p[upd] = pr[upd]; best_id[upd] = key[upd]; best_t[upd] = t[upd]
            best_dv[upd] = (dvc / np.maximum(hw, 1e-3))[upd]; best_hw[upd] = hw[upd]
    # ------------------------------------------------ write into full-frame maps
    PID = np.full((H, W), -1, np.int64); PID[ys, xs] = best_id
    PRI = np.full((H, W), -1e9); PRI[ys, xs] = best_p
    TT = np.zeros((H, W)); TT[ys, xs] = best_t
    DV = np.zeros((H, W)); DV[ys, xs] = best_dv
    plate = mask & (PID >= 0)
    gap = mask & ~plate
    # facet normals: keel splits every plate into a dorsal (lit) and ventral (shadow) face; tips lift
    Tn = tb.T[tb.idx]; Nn = tb.N[tb.idx]
    sgn = np.sign(DV + 1e-4)
    k = facet * (0.55 + 0.45 * np.abs(DV))
    nx = tb.nrm[..., 0] + Nn[..., 0] * sgn * k - Tn[..., 0] * TT * 0.35
    ny = tb.nrm[..., 1] + Nn[..., 1] * sgn * k - Tn[..., 1] * TT * 0.35
    nz = tb.nrm[..., 2] + 0.15
    fn = np.stack([nx, ny, nz], -1); fn /= np.linalg.norm(fn, axis=-1, keepdims=True)
    nrm = tb.nrm
    # facet as a quantised tone step on top of the smooth form shading: crisp two-tone plates that keep
    # the big light/shadow masses of the body readable
    dl = (fn * LIGHT).sum(-1) - (nrm * LIGHT).sum(-1)
    base_l = np.clip((nrm * LIGHT).sum(-1), 0, 1)
    pb = np.where(dl > 0, 1.0, -1.0) * (0.35 + 0.75 * base_l) * facet
    pb -= TT ** 2 * 0.6
    # per-plate tone variation (whole plates, never per pixel)
    hv = (np.mod(PID * 2654435761, 1000) / 1000.0 - 0.5) * var * 2
    pb += np.where(plate, hv, 0)
    # contact shadow: pixel next to a plate that lies on top of it (or next to a gap)
    shadow_ = np.zeros((H, W), bool); free = np.zeros((H, W), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nid = shift(PID, dx, dy); npr = shift(PRI, dx, dy); nin = shift(mask, dx, dy)
        diff = plate & nin & (nid != PID)
        shadow_ |= diff & ((npr > PRI) | (nid < 0))
        free |= diff & (npr < PRI) & (nid >= 0)
    # free (overlapping) edges catch a thin highlight where they face the light
    ndl = (fn * LIGHT).sum(-1)
    hi = free & ~shadow_ & (ndl > 0.45)
    pb += np.where(hi, 1.2, 0)
    C.paint(plate, nrm, mat, bias=pb + bias, seam=False, far=far)
    C.paint(gap, tb.nrm, "H", bias=bias - 1.5, seam=False, far=far)
    sh = shadow_ & ~hi
    C.lvl[sh] = 1 if mat == "A" else 0
    C.lvl[gap] = 0
    if keep_seam:
        C.seam |= sh | gap
    return dict(pid=PID, plate=plate, gap=gap, shadow=sh)


# =========================================================================== spikes (faceted stone cones)
def spike(C, base, tip, w0, bend=0.0, bias=0.0, far=0.0, mat="S", under=False, tipw=0.0, glow_tip=None):
    """Curved, sharp, two-faceted spike from base to tip (w0 = half width at the base).
    bend bows the spike sideways (+ = to the left of base->tip).  under=True: only paint empty pixels."""
    base, tip = v2(base), v2(tip)
    d = tip - base
    L = np.hypot(*d)
    if L < 1.0:
        return None
    u = d / L; n = np.array([-u[1], u[0]])
    ctrl = (base + tip) / 2 + n * bend * L
    cen = qbez(base, ctrl, tip, 24)
    tang = np.gradient(cen, axis=0); tang /= np.hypot(tang[:, 0], tang[:, 1])[:, None]
    perp = np.stack([-tang[:, 1], tang[:, 0]], 1)
    tt = np.linspace(0, 1, len(cen))
    wd = w0 * (1 - tt) ** 0.95 + tipw
    left = cen + perp * wd[:, None]; right = cen - perp * wd[:, None]
    poly = list(left) + list(right[::-1])
    m = poly_mask(poly)
    # guarantee a 1px sharp core to the tip
    for (px_, py_) in pp_pixels(cen):
        if 0 <= px_ < W and 0 <= py_ < H:
            m[py_, px_] = True
    if under:
        m &= ~C.filled()
    if not m.any():
        return m
    ys, xs = np.nonzero(m)
    dd = (PX[ys, xs][:, None] - cen[None, :, 0]) ** 2 + (PY[ys, xs][:, None] - cen[None, :, 1]) ** 2
    j = dd.argmin(1)
    side = np.sign((PX[ys, xs] - cen[j, 0]) * perp[j, 0] + (PY[ys, xs] - cen[j, 1]) * perp[j, 1] + 1e-4)
    nrm = np.zeros((H, W, 3)); nrm[..., 2] = 1
    nx = perp[j, 0] * side * 0.78 - tang[j, 0] * 0.12
    ny = perp[j, 1] * side * 0.78 - tang[j, 1] * 0.12
    nv = np.stack([nx, ny, np.full(len(ys), 0.62)], 1); nv /= np.linalg.norm(nv, axis=1, keepdims=True)
    nrm[ys, xs] = nv
    b = np.zeros((H, W))
    b[ys, xs] = 0.7 - 1.6 * np.clip(1 - tt[j] / 0.35, 0, 1) + 0.9 * np.clip((tt[j] - 0.55) / 0.45, 0, 1)
    C.paint(m, nrm, mat, bias=b + bias, seam=True, far=far, rim=False)
    return m


def spike_row(C, tb, s0, s1, side, size, lat=-0.85, ang=38, step_k=0.9, bias=0.0, far=0.0, seed=0, lean=0.0,
              bend=0.10, wk=0.36, minh=2.5):
    """Row of spikes rooted on the tube surface at lateral `lat` (-1 dorsal .. +1 ventral), leaning back
    (toward the tail) by `ang` degrees from the surface normal.  size(t) -> height in px."""
    rng = np.random.RandomState(seed)
    s = s0
    tips = []
    while s < min(s1, tb.length - 1):
        t = (s - s0) / max(1e-3, s1 - s0)
        p, T, N, rd, rv = tb.at(s)
        r = rd if lat < 0 else rv
        h = size(t) * (0.85 + 0.3 * rng.rand())
        if h >= minh:
            base = p + N * lat * r * 0.98
            out = N * side
            dirv = np.array(rotv(out, 0)) * math.cos(math.radians(ang)) - T * math.sin(math.radians(ang))
            dirv = unit(dirv + T * lean)
            tip = base + dirv * h
            spike(C, base - dirv * 1.5, tip, max(1.2, h * wk), bend=bend * side, bias=bias, far=far)
            tips.append(tip)
        s += max(2.2, h * step_k)
    return tips


# =========================================================================== body
def body_tube(P):
    K = [list(k) for k in P["spine"]]
    # tail club: the whip swells into a knob that carries the spike fan
    K[0][2] = K[0][3] = max(K[0][2], 2.8)
    K[1][2] = K[1][3] = max(K[1][2], 2.6)
    return Tube(K, per=20, step=0.35, flat=0.95)


def arc_of(tb, x, y):
    """Arc length of the spine sample closest to (x, y)."""
    i = int(np.argmin(np.hypot(tb.S[:, 0] - x, tb.S[:, 1] - y)))
    return tb.s[i]


def paint_dorsal(C, P, tb, far=0.0):
    """Big back-swept spikes along neck, back and tail (drawn before the hide so it covers their roots)."""
    L = tb.length
    s_hip, s_head = P["s_hip"], P["s_head"]
    big = P.get("spike_k", 1.0)

    def size(t):   # t over the whole spine: small on the tail tip, huge over the shoulders, smaller up the neck
        s = t * L
        tail = 3.0 + 7.0 * smooth(s, 0, s_hip)
        back = 16.0 * math.exp(-((s - P["s_shoulder"]) / (0.28 * L)) ** 2)
        neck = -8.0 * smooth(s, P["s_shoulder"] + 8, s_head)
        return big * max(2.0, tail + back + neck)
    tips = spike_row(C, tb, 6, s_head - 4, -1, size, lat=-0.7, ang=34, step_k=0.50, far=far, seed=3, bend=0.14,
                     wk=0.40, bias=0.3)
    # secondary staggered flank row (shorter, more swept) over back + neck: the bristling porcupine read
    tips += spike_row(C, tb, s_hip - 30, s_head - 10, -1, lambda t: 0.62 * size((s_hip - 30 + t * (s_head - 10 - s_hip + 30)) / L),
                      lat=-0.35, ang=48, step_k=0.7, far=far, seed=4, bend=0.1, wk=0.34, bias=-0.3)
    return tips


def paint_tail_club(C, P, tb, far=0.0):
    """Spiked fan at the tail tip + paired barbs along the last third of the tail (both edges)."""
    L = tb.length
    tips = []
    for k, s in enumerate(np.arange(L * 0.08, L * 0.45, 6.0)):
        p, T, N, rd, rv = tb.at(s)
        h = 4.0 + 5.0 * (s / (L * 0.45))
        base = p + N * rv * 0.6
        tip = base + unit(N * 0.75 - T * 0.65) * h
        spike(C, base, tip, max(1.3, h * 0.3), bend=0.1, far=far, bias=-0.6)
        tips.append(tip)
    p, T, N, rd, rv = tb.at(2.0)
    fan = P.get("fan", [-165, -140, -115, -92, 170, 145, 120])
    for a in fan:
        dv = np.array(rotv(-T, a))
        h = 10.0 + 4.0 * abs(math.cos(math.radians(a)))
        tip = p + dv * h * P.get("fan_k", 1.0)
        spike(C, p + dv * 1.5, tip, 2.2 * P.get("fan_k", 1.0), bend=0.12 * (1 if a > 0 else -1), far=far, bias=0.2)
        tips.append(tip)
    return tips


def paint_body(C, P, tb, far=0.0):
    lat, arc = tb.lat, tb.arc
    m = tb.mask
    C.paint(m, tb.nrm, "H", far=far)
    s_hip, s_throat = P["s_hip"] - 6, P["s_head"] - 3
    span = s_throat - s_hip
    tpos = np.clip((arc - s_hip) / span, 0, 1)
    band = m & (lat > 0.56 + 0.26 * (np.abs(tpos - 0.45) / 0.55) ** 3) & (arc > s_hip) & (arc < s_throat)
    scutes(C, tb, m & ~band, rows=P.get("rows", 2.2), pu_k=0.8, pu_max=12, facet=0.8, far=far, seed=1)
    # ventral bands: broad segmented slate plates, grooves glow when the storm is up
    pb = np.full((H, W), 0.2) - np.clip(lat - 0.8, 0, 1) * 4.0
    C.paint(band, tb.nrm, "P", bias=pb, seam=True, far=far)
    sp = np.where(tpos > 0.6, 3.4, 4.6)
    groove = band & (np.mod(arc - s_hip, sp) < 1.0)
    C.lvl[groove] = 0
    tg = P.get("throat", 1)
    gi = np.floor((arc - s_hip) / sp).astype(int)
    pick = np.vectorize(hash01)(gi, 3, 9) > 0.45
    hot = groove & (tpos > 0.62) & (lat > 0.62) & (lat < 0.86) & pick
    if tg >= 1:
        C.put(hot & (tpos > 0.85), STORM[1])
    if tg >= 2:
        C.put(hot, STORM[1]); C.put(hot & (tpos > 0.85) & (lat > 0.68) & (lat < 0.8), STORM[3])
    return band


# =========================================================================== legs
def ik2(a, b, L1, L2, pref):
    a, b = v2(a), v2(b)
    d = b - a
    dist = np.hypot(*d)
    if dist >= L1 + L2 - 0.01:
        return a + d * L1 / (L1 + L2)
    x = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    hh = math.sqrt(max(0, L1 * L1 - x * x))
    u = d / dist
    mid = a + u * x
    c1 = mid + np.array([-u[1], u[0]]) * hh; c2 = mid - np.array([-u[1], u[0]]) * hh
    return c1 if (c1 - mid) @ v2(pref) >= (c2 - mid) @ v2(pref) else c2


def claws(C, root, dirs, lens, sz, bias, far, grip=1.0):
    """Toes: short armoured knuckle + long hooked bone talon curling down into the ground."""
    for k, (dv, ln) in enumerate(zip(dirs, lens)):
        dv = unit(dv)
        t1 = v2(root) + dv * ln * 0.55 * sz
        kn = cap(root, t1, 3.0 * sz, 2.4 * sz, clean_it=1)
        C.paint(kn.mask, kn.nrm, "A", bias=bias + 0.6 - 0.6 * (k % 2), far=far)
        tip = t1 + dv * ln * 0.62 * sz + np.array([0, 2.2 * grip * sz])
        spike(C, t1 - dv * 0.8, tip, 2.4 * sz, bend=-0.34 * np.sign(dv[0] + 1e-3), mat="B", bias=bias - 0.4, far=far)


def armoured(C, a, b, r0, r1, bulge=0.0, bend=0.0, bt=0.5, bias=0.0, far=0.0, rows=1.7, seed=0, seam="soft"):
    """Limb segment a->b whose plates point toward a (so pass the lower joint as `a` for down-pointing plates)."""
    t = cap(a, b, r0, r1, bulge=bulge, bend=bend, bt=bt, clean_it=1)
    C.paint(t.mask, t.nrm, "H", bias=bias, far=far, seam=seam)
    scutes(C, t, t.mask, rows=rows, pu_k=0.9, pu_min=3.0, pu_max=8.0, facet=0.75, bias=bias, seed=seed, far=far)
    # silhouette line against whatever was underneath
    return t


def hind_leg(C, L, bias=0.0, far=0.0):
    sz = L.get("sz", 1.0)
    bias = bias + (0.7 if not far else 0.2)
    hip, ankle, foot = v2(L["hip"]), v2(L["ankle"]), v2(L["foot"])
    knee = v2(L["knee_at"]) if "knee_at" in L else ik2(hip, ankle, 25 * sz, 23 * sz, L.get("knee", (1, 0)))
    # toes (behind the foot)
    fd = unit(foot - ankle)
    claws(C, foot + (0, -1), [(1, 0.12), (0.9, 0.4), (0.45, 0.8), (-0.7, 0.5)], [11, 10.5, 8, 6], sz, bias, far)
    armoured(C, foot, ankle, 5.2 * sz, 5.8 * sz, bias=bias, far=far, rows=1.4, seed=11)
    # heel spur + knee spike
    spike(C, ankle + (1, 0), ankle + (-7 * sz, 3 * sz), 2.0 * sz, bend=0.15, bias=bias, far=far, under=True)
    armoured(C, ankle, knee, 5.8 * sz, 8.0 * sz, bulge=1.2 * sz, bend=1.2, bias=bias, far=far, rows=1.6, seed=12)
    kd = unit(knee - hip) + unit(knee - ankle)
    spike(C, knee - unit(kd) * 2, knee + unit(unit(kd) + (0, -0.6)) * 9 * sz, 2.6 * sz, bend=0.1, bias=bias, far=far, under=True)
    armoured(C, knee, hip, 8.5 * sz, 13.0 * sz, bulge=2.0 * sz, bt=0.6, bend=-2.0, bias=bias + 0.5, far=far, rows=2.0,
             seed=13)
    return knee


def fore_leg(C, A, bias=0.0, far=0.0):
    sz = A.get("sz", 1.0)
    bias = bias + (0.7 if not far else 0.2)
    sh, el, wr, hd = (v2(A[k]) for k in ("shoulder", "elbow", "wrist", "hand"))
    cd = unit(A.get("claw_dir", (1, 0.3)))
    dirs = [rotv(cd, a) for a in (-20, 0, 22, 48)]
    claws(C, hd, dirs, [11, 12.5, 11, 8], sz, bias, far, grip=A.get("grip", 1.0))
    armoured(C, hd, wr, 5.4 * sz, 6.0 * sz, bias=bias, far=far, rows=1.3, seed=21)
    fa = armoured(C, wr, el, 6.4 * sz, 9.0 * sz, bulge=2.0 * sz, bt=0.35, bend=A.get("fore_bend", -1.0), bias=bias,
                  far=far, rows=1.7, seed=22)
    # jagged plate spikes on the back of the forearm + big elbow spike
    for t in (0.35, 0.62):
        p = wr + (el - wr) * t
        back = unit(np.array(rotv(unit(el - wr), -90 if A.get("flip", 0) else 90)))
        spike(C, p, p + unit(back * 0.8 + unit(el - wr) * 0.6) * 7 * sz, 2.2 * sz, bend=0.1, bias=bias, far=far, under=True)
    ev = unit(el - wr) + unit(el - sh) * 0.6
    spike(C, el - unit(ev) * 3, el + unit(ev) * 12 * sz, 3.2 * sz, bend=0.12, bias=bias + 0.3, far=far, under=True)
    armoured(C, el, sh, 8.5 * sz, 13.0 * sz, bulge=2.0 * sz, bt=0.6, bend=A.get("up_bend", 1.5), bias=bias + 0.2,
             far=far, rows=1.9, seed=23)


# =========================================================================== wings
def wing(C, W_, bias=0.0, far=False, seed=0):
    """Wing-arm: armoured humerus/forearm with leading-edge spikes, hooked thumb talon, four long finger
    bones ending in claws, and a ragged, holed, backlit membrane."""
    fd = 1.0 if far else 0.0
    sh, el, wr = v2(W_["shoulder"]), v2(W_["elbow"]), v2(W_["wrist"])
    tips = [v2(t) for t in W_["tips"]]
    root = v2(W_["root"])
    bends = W_.get("bends", [2.0, 3.0, 3.0, 2.5])
    sag = W_.get("sag", [0.28, 0.30, 0.30, 0.34])
    bs = W_.get("bend_sign", 1)
    fingers = []
    for k, tp in enumerate(tips):
        d = tp - wr
        nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
        fingers.append(qbez(wr, (wr + tp) / 2 + nrm * bends[k] * bs, tp, 60))

    def scallop(a, b, s):
        mid = (a + b) / 2
        return list(qbez(a, mid + (wr - mid) * s, b, 30))
    poly = [sh, el, wr] + list(fingers[0])
    for k in range(len(tips) - 1):
        poly += scallop(tips[k], tips[k + 1], sag[k])
    poly += scallop(tips[-1], root, sag[-1])
    poly += list(qbez(root, (root + sh) / 2, sh, 10))
    mem = clean(poly_mask(poly), 2)
    rng = np.random.RandomState(seed)
    # ragged trailing edge: many tears of varying depth, a few long rips
    for k in range(len(tips)):
        a, b = tips[k], (tips[k + 1] if k + 1 < len(tips) else root)
        mid = (a + b) / 2
        c = mid + (wr - mid) * sag[k]
        nt = W_.get("tears", 5) + 3
        for j in range(nt):
            t = (j + 0.5 + rng.uniform(-0.3, 0.3)) / nt
            p = (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t * t * b
            inward = unit(wr - p)
            side = np.array([-inward[1], inward[0]])
            depth = rng.uniform(2.5, 6.0) if rng.rand() < 0.6 else rng.uniform(8, 16)
            w = rng.uniform(0.9, 2.2)
            tri = [p - side * w - inward * 2, p + side * w - inward * 2,
                   p + inward * depth + side * rng.uniform(-1.5, 1.5)]
            mem &= ~poly_mask(tri)
    # torn holes: irregular (two overlapping ellipses), mostly toward the trailing half
    for j in range(int(W_.get("nholes", 6) * 1.5)):
        k = rng.randint(0, len(tips))
        f = fingers[k]; g = fingers[k + 1] if k + 1 < len(tips) else qbez(wr, (wr + root) / 2, root, 60)
        tt = rng.uniform(0.4, 0.88); mix = rng.uniform(0.25, 0.75)
        c = f[int(tt * 59)] * (1 - mix) + g[int(tt * 59)] * mix
        r = rng.uniform(1.4, 3.4) * W_.get("hole_k", 1.0)
        ang = math.degrees(math.atan2(*(c - wr)[::-1])) + rng.uniform(-30, 30)
        hole = ell_mask(c, r * 1.4, r * 0.7, ang) | ell_mask(c + rng.uniform(-1.5, 1.5, 2), r, r * 0.6, ang + 50)
        mem &= ~hole
    mem = clean(mem, 1)
    # shading: backlit skin glows through where thin (far from bones, near the torn edge)
    bone_pts = np.vstack(fingers + [qbez(sh, (sh + el) / 2, el, 20), qbez(el, (el + wr) / 2, wr, 20)])
    dB = dist_to(bone_pts)
    dW = np.hypot(PX - wr[0], PY - wr[1])
    reach = max(np.hypot(*(t - wr)) for t in tips)
    hem = mem & dil4(~mem) & (dB > 2.5)
    lv = 1.0 + 1.8 * smooth(dB, 1.5, 12) + 2.4 * smooth(dW / reach, 0.35, 1.0)
    lv -= C.filled() * (1.8 if not far else 0.8)
    lv += bias
    lv = np.floor(lv)
    lv[hem] += 1
    C.paint(mem, None, "M", lvl=np.clip(lv, 0, 8).astype(int), rim=False, seam=True, far=fd)
    # membrane creases alongside each finger (1px darker)
    for k, f in enumerate(fingers[1:], 1):
        d = f[-1] - f[0]
        nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
        off = f[8:50] + nrm * 1.8 * W_.get("crease_side", 1)
        C.put([p for p in dense_stroke(off) if mem[p[1], p[0]]], RAMPS["M"][max(0, int(1 + bias))])
    # striations: faint radial folds between the fingers (skin stretched from the wrist)
    rs = np.random.RandomState(seed + 99)
    for k in range(len(fingers)):
        f = fingers[k]; g = fingers[k + 1] if k + 1 < len(fingers) else qbez(wr, (wr + root) / 2, root, 60)
        for mix in (0.34, 0.67):
            mix += rs.uniform(-0.08, 0.08)
            line_ = [f[i] * (1 - mix) + g[i] * mix for i in range(14, 52)]
            px = [p for p in dense_stroke(line_) if mem[p[1], p[0]] and dB[p[1], p[0]] > 2.5]
            for (x, y) in px[::1]:
                lvv = C.lvl[y, x]
                if C.fixed[y, x] < 0 and lvv > 0:
                    C.lvl[y, x] = lvv - 1
    # finger bones (thin, tapering) + tip claws
    for k, f in enumerate(fingers):
        rr = np.linspace(W_.get("finger_r", 2.4) * (1.0 - 0.12 * k), 0.7, len(f))
        keys = [(x, y, r, r) for (x, y), r in zip(f[::6], rr[::6])] + [(f[-1][0], f[-1][1], 0.5, 0.5)]
        ft = Tube(keys, per=8, step=0.3, clean_it=1)
        C.paint(ft.mask, ft.nrm, "A", bias=bias + 0.6, rim=False, far=fd)
        dv = unit(f[-1] - f[-6])
        ck = unit(np.array(rotv(dv, 75 * (1 if (dv[0] > 0) != far else -1))))
        spike(C, f[-4], f[-1] + dv * 4.5 + ck * 2.4, 1.6, bend=0.25 * (1 if dv[0] > 0 else -1), mat="B",
              bias=bias - 0.5, far=fd)
    # forearm + humerus (armoured), leading-edge spikes
    fr = W_.get("fore_r", (4.0, 2.7))
    fa = cap(wr, el, fr[1], fr[0], bulge=0.9, bt=0.7, bend=-W_.get("fore_bend", -1.5))
    C.paint(fa.mask, fa.nrm, "H", bias=bias, far=fd)
    scutes(C, fa, fa.mask, rows=1.2, pu_k=1.1, pu_min=3.5, pu_max=6, facet=0.7, bias=bias, seed=seed + 1, far=fd)
    lead = unit(np.array(rotv(unit(wr - el), -90 if (wr - el)[0] * (1 if not far else 1) >= 0 else 90)))
    if lead[1] > 0:
        lead = -lead
    for t in np.linspace(0.2, 0.85, W_.get("lead_spikes", 4)):
        p = el + (wr - el) * t
        spike(C, p, p + unit(lead + unit(el - wr) * 0.9) * (7.0 + 3.0 * t), 2.2, bend=0.1, bias=bias - 0.2, far=fd,
              under=True)
    hr = W_.get("hum_r", (6.4, 3.6))
    hu = cap(el, sh, hr[1], hr[0], bulge=1.3, bt=0.65, bend=-W_.get("hum_bend", 1.5))
    C.paint(hu.mask, hu.nrm, "H", bias=bias, seam="soft", far=fd)
    scutes(C, hu, hu.mask, rows=1.4, pu_k=1.0, pu_min=3.5, pu_max=7, facet=0.7, bias=bias, seed=seed + 2, far=fd)
    # elbow spike + wrist knuckle + big hooked thumb talon
    ev = unit(unit(el - sh) + unit(el - wr))
    spike(C, el - ev * 1.5, el + ev * 8, 2.4, bend=0.15, bias=bias + 0.3, far=fd)
    kn = Tube([(wr[0], wr[1], 3.0, 3.0), (wr[0] + 0.8, wr[1] + 0.4, 2.8, 2.8)], clean_it=0)
    C.paint(kn.mask, kn.nrm, "A", bias=bias + 0.8, seam=False, far=fd)
    th = unit(W_.get("thumb", (3, -4)))
    hook = np.array(rotv(th, 90 if th[0] >= 0 else -90))
    spike(C, wr + th * 1.0, wr + th * 9 + hook * 3.5, 2.2, bend=0.3 * (1 if th[0] >= 0 else -1), mat="B",
          bias=bias - 0.3, far=fd)
    return dict(fingers=fingers, mem=mem, wrist=wr, tips=tips, root=root, el=el, far=far)


# =========================================================================== head
def head(C, fxl, P, far=0.0):
    """Big angular faceted skull: brow shelf, plated cheeks, crown of back-swept horns and spikes, hinged
    jaw lined with jagged teeth and chin spikes, glowing storm-blue eye and throat."""
    hp = v2(P["head"]); ang = P["head_ang"]; jaw = P.get("jaw", 0)
    sc = P.get("head_sc", 1.0)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    U = np.array([ca, sa]); V = np.array([-sa, ca])
    hinge = (2.0, 3.0)

    hy = P.get("head_hy", 1.15)

    def w(x, y):
        return hp + U * x * sc + V * y * sc * hy

    def wj(x, y):
        dx, dy = rotv((x - hinge[0], y - hinge[1]), jaw)
        return w(hinge[0] + dx, hinge[1] + dy)

    def nr(nx, ny, nz):
        v = np.array([nx * ca - ny * sa, nx * sa + ny * ca, nz])
        return v / np.linalg.norm(v)

    def facet(poly, n, bias=0.0, mat="A", fn=w, seam=True, rim=True):
        m = poly_mask([fn(*p) for p in poly])
        nm = np.zeros((H, W, 3)); nm[..., :] = n
        C.paint(m, nm, mat, bias=bias, seam=seam, rim=rim, far=far)
        return m

    def hspike(b, t, w0, bend=0.12, bias=0.0, fn=w):
        spike(C, fn(*b), fn(*t), w0 * sc, bend=bend, bias=bias, far=far)

    cr = P.get("crown", 1.0)
    # ---- far horns (behind everything, dark)
    hspike((5, -9), (-18 * cr, -27 * cr), 3.0, bend=-0.16, bias=-2.6)
    hspike((-4, -5), (-25 * cr, -15 * cr), 2.4, bend=-0.1, bias=-2.4)
    # ---- lower jaw (hinged): lit side band over a dark underside, one spike at the jaw corner
    hspike((3, 8.6), (-5, 14.5), 1.8, bend=0.14, bias=-1.4, fn=wj)
    J = [(-5, 3.0), (10, 3.0), (24, 2.9), (31, 2.8), (31.5, 4.5), (27, 6.5), (16, 8.5), (4, 9.5), (-5, 7.5)]
    jaw_m = facet(J, nr(0.0, 0.85, 0.5), bias=-0.2, fn=wj)
    facet([(-5, 3.0), (10, 3.0), (24, 2.9), (31, 2.8), (31.3, 4.2), (24, 5.0), (10, 6.0), (-5, 5.8)],
          nr(-0.1, -0.1, 1.0), bias=1.8, fn=wj, seam=False)
    # ---- mouth interior + storm throat
    if jaw > 4:
        top = [w(x, 2.4) for x in np.linspace(31, -2, 14)]
        bot = [wj(x, 3.1) for x in np.linspace(-2, 31, 14)]
        mm = poly_mask(top + bot) & ~C.filled()
        c0 = w(5.0, 2.8) + (wj(5.0, 3.2) - w(5.0, 2.8)) * 0.5
        dd = np.hypot(PX - c0[0], PY - c0[1])
        C.paint(mm, None, "K", lvl=np.clip(3 - (dd / (6 * sc)).astype(int), 0, 3), rim=False, seam=False, far=far)
        g = P.get("mouth_glow")
        if g:
            C.put(mm & (dd < 17 * sc), STORM[0])
            C.put(mm & (dd < 12.5 * sc), STORM[1])
            C.put(mm & (dd < 9 * sc), STORM[2 + min(g, 2) // 2])
            C.put(mm & (dd < 6 * sc), STORM[3 + min(g, 2)])
            C.put(mm & (dd < 3.0 * sc), STORM[6])
        for x, ln in ((12, 3.2), (17, 4.6), (22, 3.0), (26.5, 3.8), (30, 2.4)):
            spike(C, wj(x, 3.3), wj(x - 0.5, 3.1 - ln), 1.15 * sc, bend=0.0, mat="B", bias=1.0, far=far)
    # ---- skull: side facet, lit top plane, snout tip, big cheek plate
    facet([(-7, 2), (-6, -6), (0, -9), (9, -9.5), (13, -7), (16, -6), (26, -4.5), (31, -3.5), (33, -1.5), (33, 1.5),
           (31, 2.6), (4, 2.6), (-2, 4)], nr(0.05, 0.12, 1.0), bias=0.5)
    facet([(-6, -6), (0, -9), (9, -9.5), (13, -7), (16, -6), (26, -4.5), (31, -3.5), (33, -1.5), (32, -0.8),
           (26, -2.4), (16, -3.4), (12, -4.4), (6, -5.2), (-6, -3.6)], nr(-0.1, -0.85, 0.5), bias=1.4, seam=False)
    facet([(9, -9.5), (13, -7), (12, -4.4), (6, -5.2)], nr(0.35, -0.6, 0.7), bias=0.6, seam=False)
    facet([(-9, -3), (3, -2), (8, 2.5), (3, 7), (-8, 5)], nr(-0.5, 0.15, 0.85), bias=1.0)
    facet([(-9, -3), (3, -2), (4.6, -0.6), (-9, -1.4)], nr(-0.3, -0.75, 0.6), bias=1.2, seam=False)
    # plate seams on the snout side (armour read) + keel highlight
    for a, b in (((16, -3.3), (17.5, 2.4)), ((23.5, -2.6), (24.5, 2.4))):
        C.put(dense_stroke([w(*a) + (w(*b) - w(*a)) * t for t in np.linspace(0, 1, 16)]), RAMPS["A"][2],
              only=(C.mat == MI["A"]))
    kl = dense_stroke([w(x, y) for x, y in zip(np.linspace(-5, 31, 40), np.interp(np.linspace(-5, 31, 40),
                       [-5, 6, 12, 16, 26, 31], [-3.6, -5.2, -4.4, -3.4, -2.4, -1.0]))])
    C.put(kl, RAMPS["A"][9], only=(C.mat == MI["A"]))
    # upper fangs
    for x, ln in ((10, 2.6), (14.5, 5.0), (19, 3.0), (23, 3.4), (27, 4.6), (30.6, 2.4)):
        spike(C, w(x, 2.0), w(x + 0.5, 2.3 + ln), 1.15 * sc, bend=0.0, mat="B", bias=1.1, far=far)
    n0 = w(29.5, -0.8)
    C.put([(int(n0[0]), int(n0[1]))], RAMPS["A"][0])
    # skull side plates: seams with a lit lip above each (armour read) + cheekbone ridge
    for pts_ in ([(4, -2.6), (10, -1.2), (15, -1.0)], [(17, 0.4), (23, -0.2), (29, -0.4)], [(-4, -0.4), (2, 0.8)]):
        ln = dense_stroke(np.vstack([qbez(w(*pts_[0]), w(*pts_[1]), w(*pts_[-1]), 20)]))
        C.put(ln, RAMPS["A"][2], only=(C.mat == MI["A"]))
        C.put([(x, y - 1) for (x, y) in ln], RAMPS["A"][8], only=(C.mat == MI["A"]) & (C.fixed < 0))
    # ---- eye: deep socket under the brow shelf, burning storm-blue (almond, 2px tall)
    sock = poly_mask([w(6.5, -6.0), w(15.5, -4.4), w(16, -1.4), w(7.5, -2.2)])
    C.lvl[sock & (C.mat == MI["A"])] = 0
    C.put(sock & (C.mat == MI["A"]), STORM[0])
    eye = poly_mask([w(8.2, -4.0), w(11.5, -4.6), w(15.2, -3.6), w(12, -2.4), w(9, -2.8)]) & sock
    C.put(eye, STORM[4])
    ey, ex = np.nonzero(eye)
    if len(ex):
        cx_, cy_ = ex.mean(), ey.mean()
        core = eye & (np.hypot(XX - cx_, YY - cy_) < 1.3)
        C.put(core, STORM[6])
        C.put(eye & ~core & (XX > cx_ + 1), STORM[5])
    e = [(x, y) for y, x in zip(*np.nonzero(eye))]
    trail = dense_stroke([w(x, -3.9 - 0.06 * (8 - x)) for x in np.linspace(8.0, 0.0, 12)])
    fxl.put(trail[1:4], STORM[4]); fxl.put(trail[4:7], STORM[3]); fxl.put(trail[7:9], STORM[2])
    # ---- near horns + crown: everything sweeps back in one flow
    hspike((-4, 5), (-17 * cr, 14 * cr), 2.4, bend=0.1, bias=-0.4)
    hspike((-6, 1), (-24 * cr, 5 * cr), 2.6, bend=0.05, bias=-0.3)
    hspike((-6, -4), (-26 * cr, -8 * cr), 3.0, bend=-0.08, bias=0.0)
    hspike((13, -7), (5 * cr, -17 * cr), 1.8, bend=-0.14, bias=0.3)
    hspike((8, -9), (-7 * cr, -24 * cr), 2.6, bend=-0.16, bias=0.8)
    hspike((1, -8), (-29 * cr, -19 * cr), 4.0, bend=-0.2, bias=1.0)
    hspike((27, -4.4), (24.5, -9), 1.2, bend=-0.12, bias=0.5)
    P["_mouth"] = (w(31, 2.6) + (wj(31, 3.0) - w(31, 2.6)) * 0.5, ang + jaw * 0.5)
    return w, wj


# =========================================================================== lightning
def bolt(a, b, rng, amp=0.16, depth=5):
    pts = [v2(a), v2(b)]
    for _ in range(depth):
        out = [pts[0]]
        for p, q in zip(pts[:-1], pts[1:]):
            d = q - p
            L = np.hypot(*d)
            n = np.array([-d[1], d[0]]) / (L or 1)
            out += [(p + q) / 2 + n * rng.uniform(-1, 1) * L * amp, q]
        pts = out
        amp *= 0.62
    dense = []
    for p, q in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 6, endpoint=False):
            dense.append(p + (q - p) * t)
    dense.append(pts[-1])
    return pp_pixels(dense), pts


def seam_path(ok, cost, a, b):
    """Cheapest 8-connected path over pixels where ok is True (Dijkstra)."""
    a = tuple(a); b = tuple(b)
    dist = {a: 0.0}; prev = {}
    hp = [(0.0, a)]
    while hp:
        d, p = heapq.heappop(hp)
        if p == b:
            break
        if d > dist.get(p, 1e18):
            continue
        x, y = p
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not dx and not dy:
                    continue
                q = (x + dx, y + dy)
                if 0 <= q[0] < W and 0 <= q[1] < H and ok[q[1], q[0]]:
                    nd = d + cost[q[1], q[0]] * (1.41 if dx and dy else 1.0)
                    if nd < dist.get(q, 1e18):
                        dist[q] = nd; prev[q] = p
                        heapq.heappush(hp, (nd, q))
    if b not in prev and a != b:
        return []
    path = [b]
    while path[-1] != a:
        path.append(prev[path[-1]])
    return path[::-1]


def seam_lightning(C, rng, n, region=None, strength=1, reach=(10, 26), branches=1):
    """Electric veins that run THROUGH the cracks between armour plates, with a 1px soft halo."""
    inner = C.filled()
    for _ in range(2):
        inner = inner & shift(inner, 1, 0) & shift(inner, -1, 0) & shift(inner, 0, 1) & shift(inner, 0, -1)
    ok = C.seam & inner
    if region is not None:
        ok &= region
    ys, xs = np.nonzero(ok)
    if not len(ys):
        return []
    cost = 1.0 + 3.0 * np.vectorize(hash01)(XX, YY, 77)
    paths = []
    tries = 0
    while len(paths) < n and tries < n * 8:
        tries += 1
        i = rng.randint(len(ys))
        a = (xs[i], ys[i])
        d = np.hypot(xs - a[0], ys - a[1])
        cand = np.nonzero((d > reach[0]) & (d < reach[1]))[0]
        if not len(cand):
            continue
        j = cand[rng.randint(len(cand))]
        pth = seam_path(ok, cost, a, (xs[j], ys[j]))
        if len(pth) < reach[0] * 0.8:
            continue
        paths.append(pth)
        for _ in range(branches):
            k = rng.randint(len(pth) // 4, 3 * len(pth) // 4 + 1)
            b0 = pth[k]
            d = np.hypot(xs - b0[0], ys - b0[1])
            cand = np.nonzero((d > 5) & (d < reach[0]))[0]
            if len(cand):
                j = cand[rng.randint(len(cand))]
                bp = seam_path(ok, cost, b0, (xs[j], ys[j]))
                if bp:
                    paths.append(bp[1:])
    for pi, pth in enumerate(paths):
        far = C.depth[pth[0][1], pth[0][0]] if pth else 0
        lv = strength + (0 if far < 0.5 else -1)
        core = [STORM[3], STORM[4], STORM[5], STORM[6]][int(np.clip(lv + 1, 0, 3))]
        halo = [STORM[0], STORM[0], STORM[1], STORM[2]][int(np.clip(lv + 1, 0, 3))]
        pset = set(pth)
        # halo: 1px bloom on the lower/right side only, and only on plate pixels (soft, not a fat tube)
        hal = [(x + dx, y + dy) for (x, y) in pth for dx, dy in ((0, 1), (1, 0)) if (x + dx, y + dy) not in pset]
        hal = [q for q in hal if 0 <= q[0] < W and 0 <= q[1] < H and C.fixed[q[1], q[0]] < 0]
        C.put(hal[::2] if strength < 2 else hal, halo)
        C.put(pth, core)
        C.put(pth[len(pth) // 3::max(4, len(pth) // 3)], STORM[6] if lv >= 1 else STORM[5])
    return paths


def membrane_lightning(C, info, rng, n=3, strength=1):
    """Branching bolts crawling across the wing membrane from the bones toward the torn edge."""
    mem = info["mem"] & (C.mat == MI["M"])
    far = info["far"]
    wr = info["wrist"]
    out = []
    for k in range(n):
        f = info["fingers"][k % len(info["fingers"])]
        g = info["fingers"][(k % len(info["fingers"])) + 1] if (k % len(info["fingers"])) + 1 < len(info["fingers"]) else \
            qbez(wr, (wr + info["root"]) / 2, info["root"], 60)
        a = f[rng.randint(10, 30)]
        mix = rng.uniform(0.35, 0.65)
        b = f[rng.randint(40, 58)] * (1 - mix) + g[rng.randint(40, 58)] * mix
        px, pts = bolt(a, b, rng, amp=0.2, depth=5)
        px = [p for p in px if 0 <= p[0] < W and 0 <= p[1] < H]
        br = []
        for _ in range(2 + strength):
            i = rng.randint(len(pts) // 5, len(pts) - 2)
            p = pts[i]
            d = unit(v2(b) - v2(a))
            e = p + np.array(rotv(d, rng.uniform(-60, 60))) * rng.uniform(5, 12 + 4 * strength)
            bp, _ = bolt(p, e, rng, amp=0.25, depth=3)
            br += [q for q in bp if 0 <= q[0] < W and 0 <= q[1] < H]
        on = lambda L: [q for q in L if mem[q[1], q[0]]]
        core = STORM[5] if not far else STORM[4]
        if strength >= 2:
            core = STORM[6] if not far else STORM[5]
        halo = STORM[1] if not far else STORM[0]
        if strength >= 2:
            halo = STORM[2] if not far else STORM[1]
        hal = [(x + dx, y + dy) for (x, y) in px for dx, dy in ((1, 0), (0, 1)) if 0 <= x + dx < W and 0 <= y + dy < H]
        C.put(on(hal), halo)
        C.put(on(br), STORM[3] if not far else STORM[2])
        C.put(on(px), core)
        out.append(px)
    return out


def sky_bolt(fxl, a, b, rng, bright=1.0, branches=2, amp=0.16, C=None):
    """Background bolt: never drawn over the sprite (C given)."""
    free = (lambda L: [q for q in L if 0 <= q[0] < W and 0 <= q[1] < H and C.mat[q[1], q[0]] < 0]) if C is not None \
        else (lambda L: L)
    px, pts = bolt(a, b, rng, amp=amp)
    half = px[: len(px) // 2]
    fxl.put(free([(x + 1, y) for (x, y) in half]), STORM[2], only_empty=True)
    fxl.put(free(px), STORM[5] if bright < 1 else STORM[6])
    for k in range(branches):
        i = rng.randint(len(pts) // 4, 3 * len(pts) // 4)
        p = pts[i]
        d = unit(v2(b) - v2(a))
        e = p + np.array(rotv(d, rng.uniform(-55, 55))) * rng.uniform(5, 13)
        bp, _ = bolt(p, e, rng, amp=0.24, depth=3)
        fxl.put(free(bp), STORM[4] if k == 0 else STORM[3])
    return px


# =========================================================================== poses
POSES = {}

POSES["roar"] = dict(
    label="2  REARING ROAR - wings flung wide, storm in the seams (intro key art)",
    ground=168,
    spine=[(16, 98, 0.8, 0.8), (15, 117, 2.0, 2.0), (20, 134, 3.3, 3.3), (38, 146, 4.8, 4.8), (60, 150, 6.2, 6.2),
           (82, 146, 8.0, 8.0), (102, 139, 11.0, 11.5), (120, 129, 15.0, 16.0), (141, 118, 19.0, 20.5),
           (161, 107, 20.0, 21.0), (177, 96, 16.5, 17.5), (189, 84, 13.0, 13.0), (199, 72, 11.2, 11.0),
           (210, 63, 10.0, 9.8), (221, 57, 9.0, 8.8), (231, 54, 8.0, 8.0)],
    marks=dict(s_hip=(120, 130), s_shoulder=(168, 104)),
    throat=1, halo=(236, 44, 64), spike_k=1.25, fan_k=1.4,
    head=(231, 54), head_ang=-24, jaw=38, mouth_glow=2, head_sc=1.25,
    legs=[dict(hip=(110, 126), knee_at=(124, 142), ankle=(108, 156), foot=(116, 163), bias=-1.0, sz=1.0),
          dict(hip=(122, 132), knee_at=(140, 146), ankle=(124, 158), foot=(133, 164), bias=1.2, sz=1.08)],
    arms=[dict(shoulder=(180, 104), elbow=(182, 128), wrist=(202, 146), hand=(208, 156), claw_dir=(1, 0.5), bias=-1.2,
               sz=0.95),
          dict(shoulder=(170, 112), elbow=(164, 136), wrist=(184, 152), hand=(190, 162), claw_dir=(1, 0.5), bias=1.2,
               sz=1.08)],
    wings=[dict(shoulder=(170, 92), elbow=(170, 54), wrist=(180, 12), thumb=(2, -4),
                tips=[(214, 0), (230, 8), (226, 26), (206, 40)], root=(186, 86), bends=[-3, -3, -3, -2.5],
                sag=[0.3, 0.32, 0.3, 0.36], bias=-2.6, seed=4, nholes=5, tears=4, bolts=1, fore_r=(2.8, 2.0), hum_r=(4.4, 2.6)),
           dict(shoulder=(156, 94), elbow=(134, 56), wrist=(114, 20), thumb=(-3, -4),
                tips=[(22, 4), (6, 40), (22, 70), (62, 84)], root=(146, 96), bends=[3, 3, 3, 2.5],
                sag=[0.36, 0.38, 0.38, 0.4], bias=0.0, seed=7, nholes=8, tears=6)],
    seam_bolts=(22, 1), wing_bolts=4,
    sky=[((282, 70), (266, 124), 0.8)],
)


POSES["idle"] = dict(
    label="1  GROUNDED IDLE - crouched, head low, wings half-raised, storm flickering in the seams",
    ground=168,
    spine=[(12, 134, 0.8, 0.8), (11, 151, 2.0, 2.0), (22, 162, 3.3, 3.3), (44, 165, 4.8, 4.8), (66, 160, 6.2, 6.2),
           (86, 150, 8.0, 8.0), (104, 139, 11.0, 11.5), (122, 130, 15.0, 16.0), (143, 124, 19.0, 20.5),
           (163, 122, 20.0, 21.0), (179, 124, 16.5, 17.5), (192, 129, 13.0, 13.0), (204, 135, 11.2, 11.0),
           (215, 139, 10.0, 9.8), (225, 141, 9.0, 8.8), (234, 141, 8.0, 8.0)],
    marks=dict(s_hip=(122, 130), s_shoulder=(160, 122)),
    throat=0, spike_k=1.2, fan_k=1.3, fan=[-165, -135, -105, 170, 140],
    head=(234, 141), head_ang=4, jaw=0, head_sc=1.2,
    legs=[dict(hip=(106, 132), knee_at=(124, 146), ankle=(104, 158), foot=(113, 164), bias=-1.0, sz=1.0),
          dict(hip=(118, 136), knee_at=(138, 150), ankle=(120, 160), foot=(129, 165), bias=1.2, sz=1.08)],
    arms=[dict(shoulder=(178, 128), elbow=(172, 148), wrist=(192, 158), hand=(199, 163), claw_dir=(1, 0.45),
               bias=-1.0, sz=0.95),
          dict(shoulder=(166, 134), elbow=(158, 152), wrist=(178, 160), hand=(185, 165), claw_dir=(1, 0.45), bias=1.2,
               sz=1.08)],
    wings=[dict(shoulder=(166, 112), elbow=(158, 80), wrist=(176, 46), thumb=(3, -4),
                tips=[(128, 24), (110, 42), (112, 66), (134, 86)], root=(160, 106), bends=[3, 3, 3, 2.5],
                sag=[0.22, 0.24, 0.24, 0.3], bias=-2.0, seed=31, nholes=3, tears=3, bolts=1, fore_r=(2.8, 2.0),
                hum_r=(4.4, 2.6), lead_spikes=3),
           dict(shoulder=(150, 114), elbow=(130, 84), wrist=(148, 48), thumb=(3, -4),
                tips=[(96, 34), (78, 56), (82, 82), (104, 102)], root=(132, 116), bends=[3, 3, 3, 2.5],
                sag=[0.22, 0.24, 0.24, 0.3], bias=0.0, seed=33, nholes=5, tears=4, bolts=2)],
    seam_bolts=(9, 1), seed=8,
)

POSES["breath"] = dict(
    label="3  LIGHTNING BREATH - neck lunges, jaws wide, a crackling bolt sprays forward",
    ground=168,
    spine=[(14, 92, 0.8, 0.8), (10, 111, 2.0, 2.0), (10, 130, 3.3, 3.3), (24, 145, 4.8, 4.8), (44, 151, 6.2, 6.2),
           (62, 146, 8.0, 8.0), (77, 138, 11.0, 11.5), (93, 130, 15.0, 16.0), (112, 123, 19.0, 20.5),
           (131, 119, 20.0, 21.0), (146, 116, 16.5, 17.5), (159, 113, 13.0, 13.0), (171, 112, 11.2, 11.0),
           (182, 113, 10.0, 9.8), (192, 115, 9.0, 8.8), (201, 117, 8.0, 8.0)],
    marks=dict(s_hip=(93, 130), s_shoulder=(126, 120)),
    throat=2, spike_k=1.2, fan_k=1.3, halo=None, fan=[-165, -135, -105, 170, 140],
    head=(201, 117), head_ang=8, jaw=34, mouth_glow=2, head_sc=1.15,
    legs=[dict(hip=(80, 134), knee_at=(98, 146), ankle=(78, 158), foot=(87, 164), bias=-1.0, sz=1.0),
          dict(hip=(92, 138), knee_at=(112, 150), ankle=(94, 160), foot=(103, 165), bias=1.2, sz=1.08)],
    arms=[dict(shoulder=(142, 122), elbow=(140, 144), wrist=(160, 156), hand=(167, 162), claw_dir=(1, 0.45),
               bias=-1.0, sz=0.95),
          dict(shoulder=(132, 128), elbow=(126, 148), wrist=(146, 158), hand=(153, 164), claw_dir=(1, 0.45), bias=1.2,
               sz=1.08)],
    wings=[dict(shoulder=(126, 106), elbow=(136, 76), wrist=(144, 40), thumb=(3, -4),
                tips=[(172, 6), (192, 22), (190, 46), (170, 62)], root=(142, 100), bends=[-3, -3, -3, -2.5],
                sag=[0.28, 0.3, 0.3, 0.34], bias=-2.0, seed=41, nholes=4, tears=4, bolts=1, fore_r=(2.8, 2.0),
                hum_r=(4.4, 2.6)),
           dict(shoulder=(114, 110), elbow=(94, 76), wrist=(80, 40), thumb=(-3, -4),
                tips=[(22, 8), (6, 40), (14, 74), (44, 96)], root=(96, 112), bends=[3, 3, 3, 2.5],
                sag=[0.36, 0.38, 0.38, 0.4], bias=0.0, seed=43, nholes=7, tears=6)],
    seam_bolts=(18, 1), wing_bolts=3, seed=12, beam=dict(length=70, ang=10),
)

POSES["air"] = dict(
    label="4  PHASE 2 - AIRBORNE, the storm breaks loose",
    ground=None, phase=2,
    spine=[(12, 60, 0.8, 0.8), (14, 77, 2.0, 2.0), (24, 91, 3.3, 3.3), (44, 99, 4.8, 4.8), (66, 102, 6.2, 6.2),
           (88, 99, 8.0, 8.0), (108, 94, 11.0, 11.5), (127, 90, 15.0, 16.0), (148, 88, 19.0, 20.5),
           (168, 89, 20.0, 21.0), (184, 88, 16.5, 17.5), (197, 83, 13.0, 13.0), (208, 77, 11.2, 11.0),
           (219, 74, 10.0, 9.8), (229, 74, 9.0, 8.8), (238, 76, 8.0, 8.0)],
    marks=dict(s_hip=(127, 90), s_shoulder=(162, 88)),
    throat=2, spike_k=1.25, fan_k=1.4, halo=(150, 60, 90),
    head=(238, 76), head_ang=12, jaw=22, mouth_glow=2, head_sc=1.15,
    legs=[dict(hip=(112, 94), knee_at=(128, 108), ankle=(110, 118), foot=(98, 126), bias=-1.0, sz=1.0),
          dict(hip=(124, 98), knee_at=(142, 112), ankle=(124, 122), foot=(112, 130), bias=1.2, sz=1.08)],
    arms=[dict(shoulder=(176, 96), elbow=(170, 112), wrist=(186, 120), hand=(193, 126), claw_dir=(0.6, 0.8),
               bias=-1.0, sz=0.95),
          dict(shoulder=(166, 102), elbow=(158, 118), wrist=(174, 126), hand=(181, 132), claw_dir=(0.6, 0.8),
               bias=1.2, sz=1.08)],
    wings=[dict(shoulder=(168, 78), elbow=(184, 46), wrist=(196, 12), thumb=(2, -4),
                tips=[(246, 1), (272, 12), (270, 34), (244, 50)], root=(186, 84), bends=[-3, -3, -3, -2.5],
                sag=[0.3, 0.32, 0.3, 0.36], bias=-1.6, seed=51, nholes=5, tears=4, bolts=3, fore_r=(2.8, 2.0),
                hum_r=(4.4, 2.6)),
           dict(shoulder=(154, 80), elbow=(132, 46), wrist=(110, 12), thumb=(-3, -4),
                tips=[(20, 3), (4, 40), (20, 72), (62, 90)], root=(136, 94), bends=[3, 3, 3, 2.5],
                sag=[0.36, 0.38, 0.38, 0.4], bias=0.0, seed=53, nholes=8, tears=6)],
    seam_bolts=(30, 2), wing_bolts=5, seed=21,
    sky=[((270, 12), (287, 40), 1), ((60, 92), (40, 140), 1), ((190, 134), (206, 176), 0.8)],
)


def render_pose(P):
    C = Canvas()
    fxl = FX()
    rng = np.random.RandomState(P.get("seed", 5))
    phase = P.get("phase", 1)
    tb = body_tube(P)
    for k, (x, y) in P["marks"].items():
        P[k] = arc_of(tb, x, y)
    P["s_head"] = tb.length
    fw, nw = P["wings"]
    fl, nl = P["legs"]
    fa, na = P["arms"]
    # ---- far side
    fi = wing(C, fw, bias=fw.get("bias", -1.4), far=True, seed=fw.get("seed", 1))
    hind_leg(C, fl, bias=fl["bias"], far=1.0)
    fore_leg(C, fa, bias=fa["bias"], far=1.0)
    # ---- body
    dtips = paint_dorsal(C, P, tb)
    ttips = paint_tail_club(C, P, tb)
    band = paint_body(C, P, tb)
    hind_leg(C, nl, bias=nl["bias"])
    head(C, fxl, P)
    fore_leg(C, na, bias=na["bias"])
    ni = wing(C, nw, bias=nw.get("bias", 0), far=False, seed=nw.get("seed", 2))
    # ---- storm
    nb, br = P.get("seam_bolts", (8, 1))
    seam_lightning(C, rng, nb, strength=phase, branches=br)
    membrane_lightning(C, fi, rng, n=fw.get("bolts", P.get("wing_bolts", 3)), strength=phase)
    membrane_lightning(C, ni, rng, n=P.get("wing_bolts", 3), strength=phase)
    img = C.render()
    if P.get("beam"):
        m, a = P["_mouth"]
        breath_beam(fxl, C, m, P["beam"].get("ang", a), P["beam"]["length"], rng)
    if phase >= 2:
        arcs(fxl, C, dtips, rng, 9, reach=(5, 12))
        arcs(fxl, C, ttips, rng, 4, reach=(5, 10))
        wt = [t for info in (fi, ni) for t in info["tips"]] + [fi["wrist"], ni["wrist"]]
        arcs(fxl, C, wt, rng, 6, reach=(6, 14))
    for a, b, brt in P.get("sky", []):
        sky_bolt(fxl, a, b, rng, brt, C=C)
    img.alpha_composite(fxl.image())
    P["_tb"], P["_dtips"], P["_ttips"], P["_wi"] = tb, dtips, ttips, (fi, ni)
    return img


def breath_beam(fxl, C, mouth, ang, length, rng):
    """Crackling lightning breath: a jagged white-hot core inside a cold-blue cone, wrapped by forking bolts."""
    U = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); V = np.array([-U[1], U[0]])
    dx, dy = PX - mouth[0], PY - mouth[1]
    s_ = dx * U[0] + dy * U[1]
    l_ = dx * V[0] + dy * V[1]
    wob = np.sin(s_ * 0.45) * 0.8 + np.sin(s_ * 1.3 + 1) * 0.5
    wd = 1.2 + s_ * 0.06
    r = np.abs(l_ - wob * np.clip(s_ / 12, 0, 1)) / wd
    on = (s_ > 0) & (s_ < length)
    empty = (C.mat < 0) | (C.mat == MI["K"])
    img = fxl.img
    for thr, c in ((2.2, STORM[1]), (1.5, STORM[2]), (1.0, STORM[3]), (0.6, STORM[4]), (0.3, STORM[5])):
        img[on & empty & (r < thr)] = (*hexc(c), 255)
    # white-hot jagged core
    core, _ = bolt(v2(mouth) + U, v2(mouth) + U * length, rng, amp=0.035, depth=5)
    fxl.put([q for q in core if 0 <= q[0] < W and 0 <= q[1] < H and empty[q[1], q[0]]], STORM[6])
    # bolts twisting around the beam and spraying out of it
    for k in range(6):
        e = v2(mouth) + U * length * rng.uniform(0.55, 1.1) + V * rng.uniform(-16, 16)
        px, pts = bolt(v2(mouth) + U * 3, e, rng, amp=0.14, depth=5)
        px = [q for q in px if 0 <= q[0] < W and 0 <= q[1] < H and empty[q[1], q[0]]]
        fxl.put([(x, y + 1) for (x, y) in px], STORM[2], only_empty=True)
        fxl.put(px, STORM[6] if k < 2 else STORM[5])
        for _ in range(2):
            i = rng.randint(len(pts) // 3, len(pts) - 1)
            q = pts[i]
            f = q + np.array(rotv(U, rng.choice([-1, 1]) * rng.uniform(25, 70))) * rng.uniform(5, 12)
            bp, _ = bolt(q, f, rng, amp=0.25, depth=3)
            fxl.put([q for q in bp if 0 <= q[0] < W and 0 <= q[1] < H and empty[q[1], q[0]]], STORM[4])
    # muzzle flash
    fl = (np.hypot(dx, dy) < 4.5) & empty
    img[fl] = (*hexc(STORM[5]), 255)
    img[(np.hypot(dx, dy) < 2.5) & empty] = (*hexc(STORM[6]), 255)


def arcs(fxl, C, pts, rng, n, reach=(6, 14), col=STORM[5], up=True):
    """Short electric arcs jumping off spike / claw tips into the air (phase 2)."""
    pts = [v2(p) for p in pts]
    for k in range(min(n, len(pts))):
        a = pts[rng.randint(len(pts))]
        dirv = np.array(rotv((0, -1) if up else (1, 0), rng.uniform(-70, 70)))
        b = a + dirv * rng.uniform(*reach)
        px, pts_ = bolt(a, b, rng, amp=0.3, depth=4)
        px = [q for q in px if 0 <= q[0] < W and 0 <= q[1] < H and C.mat[q[1], q[0]] < 0]
        fxl.put([(x + 1, y) for (x, y) in px], STORM[2], only_empty=True)
        fxl.put(px, col)
        fxl.put(px[:1], STORM[6])


# =========================================================================== backdrop + sheet
def knight():
    p = Image.open(os.path.join(ROOT, "assets", "player.png")).crop((0, 0, 64, 40)).convert("RGBA")
    w = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).crop((0, 0, 64, 40)).convert("RGBA")
    p.alpha_composite(w)
    return p.transpose(Image.FLIP_LEFT_RIGHT)


def backdrop(w, h, seed, ground, storm=1, halo=None, root_glow=None, spires=True):
    rng = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    bg = np.zeros((h, w, 4), np.uint8); bg[..., 3] = 255
    # sky: stepped vertical gradient (no dithering noise)
    sky = ["#0b0d13", "#0d1017", "#10131b", "#12161f", "#151a24"]
    band = np.clip((yy / h * 5 + 0.25 * np.sin(xx * 0.05 + seed)).astype(int), 0, 4)
    for k, c in enumerate(sky):
        bg[band == k, :3] = hexc(c)
    # distant golden Pale Root glow, far behind (faint, stepped)
    if root_glow:
        # the Pale Root, far behind: faint golden bloom, a pale trunk and a canopy of glowing twig-tips
        gx, gy, gr = root_glow
        wob = np.sin(xx * 0.31 + yy * 0.17) * 1.6 + np.sin(xx * 0.13 - yy * 0.29) * 2.2
        d = np.hypot((xx - gx) / 1.6, (yy - gy) * 1.15) + wob
        for rr, c in ((gr, "#131418"), (gr * 0.66, "#18181a"), (gr * 0.4, "#1f1d1b"), (gr * 0.2, "#29251e")):
            bg[d < rr, :3] = hexc(c)
        rr_ = np.random.RandomState(4)
        # canopy: a ragged, stepped golden cloud (brighter toward its heart), branches silhouetted inside
        cy_ = gy - gr * 0.05
        cd = np.hypot((xx - gx) / (gr * 0.62), (yy - cy_) / (gr * 0.34)) + 0.10 * np.sin(xx * 0.9) * np.cos(yy * 0.7) \
            + 0.12 * np.sin(np.arctan2(yy - cy_, xx - gx) * 7)
        for thr, c in ((1.0, "#2c271e"), (0.78, "#3d3423"), (0.52, "#54462a"), (0.3, "#6e5b30")):
            bg[(cd < thr) & (yy < cy_ + gr * 0.2), :3] = hexc(c)
        trunk = [(gx + 0.6 * math.sin(t * 5), gy + gr * 0.7 - t * gr * 0.62) for t in np.linspace(0, 1, 30)]
        for (x, y) in pp_pixels(trunk):
            if 0 <= x < w and 0 <= y < h:
                bg[y, x, :3] = hexc("#7a6534")
        for k in range(7):
            a = math.radians(-160 + k * 23)
            end = (gx + math.cos(a) * gr * 0.5, cy_ + math.sin(a) * gr * 0.26)
            px, _ = bolt((gx, gy + gr * 0.12), end, rr_, amp=0.18, depth=3)
            for (x, y) in px:
                if 0 <= x < w and 0 <= y < h:
                    bg[y, x, :3] = hexc("#2a2419")
        for (x, y) in pp_pixels(np.linspace((gx - gr * 0.7, gy + gr * 0.7), (gx + gr * 0.7, gy + gr * 0.7), 40)):
            if 0 <= x < w and 0 <= y < h:
                bg[y, x, :3] = hexc("#201e1c")
    if halo:
        hx, hy, hr = halo
        d = np.hypot((xx - hx) / 1.2, yy - hy) + np.sin(xx * 0.21 + yy * 0.13) * 1.5
        for rr, c in ((hr, "#131823"), (hr * 0.72, "#172031"), (hr * 0.48, "#1c2940"), (hr * 0.28, "#22334f")):
            bg[d < rr, :3] = hexc(c)
    # cloud banks: layered, lit undersides
    for k in range(3 + storm):
        cx = rng.uniform(0, w); cy = rng.uniform(4, h * 0.45); rx = rng.uniform(40, 90); ry = rng.uniform(6, 12)
        d = np.hypot((xx - cx) / rx, (yy - cy) / ry) + 0.12 * np.sin(xx * 0.18 + k)
        bg[d < 1.0, :3] = hexc("#191e2a")
        bg[(d < 1.0) & (d > 0.8) & (yy > cy), :3] = hexc("#232b3c" if storm > 1 else "#1f2533")
        bg[(d < 0.55), :3] = hexc("#161a25")
    # ruined gothic spires far right (silhouette, one tone + a lit edge)
    if spires:
        base = ground if ground else h
        for (sx, sw, sh_) in ((w - 34, 7, 70), (w - 20, 5, 52), (w - 50, 4, 40), (w - 8, 6, 60), (w - 62, 9, 30)):
            for x in range(sx - sw, sx + sw + 1):
                if not 0 <= x < w:
                    continue
                top = base - sh_ + abs(x - sx) * (sh_ * 0.28 / max(1, sw)) ** 1.0 * 2.2
                bg[int(max(0, top)):base, x, :3] = hexc("#10131b")
                if x == sx - sw + 1:
                    bg[int(max(0, top)):base, x, :3] = hexc("#161b26")
    # rain: sparse long diagonal streaks
    for k in range(70 + 40 * storm):
        x0 = rng.uniform(0, w + 30); y0 = rng.uniform(-10, h); L = rng.uniform(4, 9)
        for t in np.linspace(0, 1, int(L)):
            x = int(x0 - t * L * 0.35); y = int(y0 + t * L)
            if 0 <= x < w and 0 <= y < h:
                c = bg[y, x, :3].astype(int)
                bg[y, x, :3] = np.clip(c + 10, 0, 255)
    if ground:
        g = ground
        bg[g + 1:, :, :3] = hexc("#121319")
        # broken masonry ledge: blocks with lit tops
        x = 0
        while x < w:
            bw = rng.randint(9, 20); bh = rng.randint(2, 5)
            top = g + 1 - (bh if rng.rand() < 0.35 else 0)
            bg[top:g + 1, x:x + bw - 1, :3] = hexc("#191a22")
            bg[top, x:x + bw - 1, :3] = hexc("#2a2c36")
            bg[g + 1, x:x + bw - 1, :3] = hexc("#262833")
            x += bw
        stripe = (yy > g + 3) & (((xx + yy * 3) % 13) == 0)
        bg[stripe, :3] = hexc("#16171e")
    return Image.fromarray(bg).copy()


def rubble(img, xs, ground, seed):
    """Loose masonry chunks around the feet (drawn in FRONT of the sprite's toes to sell the grip)."""
    rng = np.random.RandomState(seed)
    d = ImageDraw.Draw(img)
    for x in xs:
        for k in range(3):
            cx = x + rng.randint(-10, 10); w_ = rng.randint(3, 7); h_ = rng.randint(2, 4)
            y1 = ground + 1
            d.polygon([(cx - w_, y1), (cx - w_ + 1, y1 - h_), (cx + w_ - 2, y1 - h_ - 1), (cx + w_, y1)],
                      fill=hexc("#1b1c24"), outline=hexc(OUT))
            d.line([(cx - w_ + 2, y1 - h_), (cx + w_ - 3, y1 - h_ - 1)], fill=hexc("#34363f"))


def quick(names):
    for k in names:
        im = render_pose(POSES[k])
        bg = Image.new("RGBA", (W, H), (18, 20, 28, 255))
        bg.alpha_composite(im)
        bg.save(os.path.join(HERE, "cindervane_%s.png" % k))
        print("wrote", k)


ORDER = ["idle", "roar", "breath", "air"]
FEET = {"idle": [113, 129, 199, 185], "roar": [108, 133, 208, 190], "breath": [87, 103, 167, 153]}


def panel(k, P, im):
    extra = 48 if k == "idle" else 0
    bg = backdrop(W + extra, H, 3 + len(k), P["ground"], storm=2 if P.get("phase", 1) >= 2 else 1,
                  halo=P.get("halo"), root_glow=(50, 124, 30) if k in ("roar", "air", "idle") else None,
                  spires=k != "air")
    if P["ground"]:
        px = bg.load()
        for x in range(60, 230):
            px[x, P["ground"] + 1] = hexc("#0b0b10") + (255,)
    bg.alpha_composite(im)
    if P["ground"]:
        rubble(bg, FEET.get(k, []), P["ground"], 9)
    if k == "idle":
        bg.alpha_composite(knight(), (W + extra - 58, P["ground"] + 1 - 40))
    return bg


def main(names=ORDER):
    S = 2
    pad = 12
    lab_h = 16
    panels = {}
    for k in names:
        P = POSES[k]
        im = render_pose(P)
        im.save(os.path.join(HERE, "cindervane_%s.png" % k))
        panels[k] = panel(k, P, im)
    colw = [max(panels["idle"].width, panels["breath"].width), max(panels["roar"].width, panels["air"].width)]
    title_h = 30
    SW = pad * 3 + (colw[0] + colw[1]) * S
    SH = title_h + pad * 2 + 2 * (H * S + lab_h) + pad
    sheet = Image.new("RGBA", (SW, SH), (9, 10, 14, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f1 = ImageFont.load_default(size=16)
        f2 = ImageFont.load_default(size=11)
    except TypeError:
        f1 = f2 = ImageFont.load_default()
    d.text((pad, 8), "CINDERVANE, THE STORMBOUND DRAKE  -  concept v3  (%dx%d frames, shown 2x, from the reference painting)"
           % (W, H), fill=(205, 216, 236), font=f1)
    grid = [["idle", "roar"], ["breath", "air"]]
    y = title_h + pad
    for row in grid:
        x = pad
        for ci, k in enumerate(row):
            d.text((x, y), POSES[k]["label"] + ("    (knight for scale)" if k == "idle" else ""),
                   fill=(143, 200, 255) if k == "air" else (182, 178, 170), font=f2)
            im = panels[k].resize((panels[k].width * S, H * S), Image.NEAREST)
            sheet.alpha_composite(im, (x, y + lab_h))
            x += colw[ci] * S + pad
        y += H * S + lab_h + pad
    sheet.convert("RGB").save(os.path.join(HERE, "cindervane.png"))
    # 3x head closeups
    cs = 3
    boxes = []
    for k in names:
        hx, hy = POSES[k]["head"]
        x0 = int(np.clip(hx - 46, 0, panels[k].width - 112)); y0 = int(np.clip(hy - 42, 0, H - 80))
        boxes.append((k, (x0, y0, x0 + 112, y0 + 80)))
    cw = sum((b[2] - b[0]) * cs + pad for _, b in boxes) + pad
    close = Image.new("RGBA", (cw, 80 * cs + pad * 2 + lab_h), (9, 10, 14, 255))
    dc = ImageDraw.Draw(close)
    x = pad
    for k, b in boxes:
        c = panels[k].crop(b)
        dc.text((x, 4), k + " head (3x)", fill=(182, 178, 170), font=f2)
        close.alpha_composite(c.resize((c.width * cs, c.height * cs), Image.NEAREST), (x, pad + lab_h))
        x += c.width * cs + pad
    close.convert("RGB").save(os.path.join(HERE, "cindervane_closeup.png"))
    print("wrote", os.path.join(HERE, "cindervane.png"), sheet.size)


if __name__ == "__main__" and len(sys.argv) == 1:
    main()
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "quick":
    quick(sys.argv[2].split(","))
