#!/usr/bin/env python3
"""CONCEPT v2 -- "Cindervane, the Last Drake" (Tempest Spire main boss).  Written fresh; v1 was rejected.

    python3 art/concepts/gen_cindervane.py

Outputs (art/concepts/):  cindervane.png (sheet, 2x, knight for scale), cindervane_<pose>.png (1x frames),
                          cindervane_closeup.png (4x head/wing crops for review)

Design: an ancient serpentine wyvern-drake.  One continuous SPINE CURVE (centripetal Catmull-Rom through
keyed joints, each with dorsal/ventral radii) is swept into a tapered tube -> tail, torso and the long
neck share one smooth surface with a per-pixel normal, arc length s and lateral coordinate (dorsal ->
ventral).  Everything else is a PART hung off that curve or off keyed joints: dorsal ridge spines, belly
plates, whip tail + barbed spade, digitigrade hind legs (2-bone IK), wing-arms (humerus / forearm / four
finger bones + scalloped, tattered, backlit membrane), and a small wedge head with a swept crown of horns,
hinged jaw and fine teeth.  Shading = normal . key light quantised into short, hand-picked ramps (same
method as gen_hound.py / gen_boss.py), 1px dark outline with sel-out, storm-blue rim light from the back,
single-pixel speckle cleanup.  Poses are plain dicts of joints, so the rig can be animated later.
Faces RIGHT.  Frame 256x160.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

W, H = 256, 160
YY, XX = np.mgrid[0:H, 0:W]
PX, PY = XX + 0.5, YY + 0.5


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# =========================================================================== palette
RAMPS = {
    # charcoal / ash-black hide (cool violet undertone)
    "H": ["#08080c", "#0e0e14", "#16151d", "#201e28", "#2b2833", "#383441", "#48434f", "#5c5663", "#78707b"],
    # ventral plates: ash-bone, a touch warm
    "P": ["#121015", "#1c181e", "#28222a", "#352e35", "#463d43", "#5a4f53", "#716566", "#8a7d78"],
    # bone: horns, claws, teeth
    "B": ["#1c1817", "#332d2a", "#554c45", "#81766a", "#b1a795", "#d9d1bf", "#f3eee2"],
    # dark horn: ridge spines, barbs
    "D": ["#0b0a0d", "#151318", "#211e23", "#302b30", "#433c40", "#5d5455"],
    # wing membrane (plum-black, backlit)
    "M": ["#0a080d", "#110e15", "#18131d", "#201a27", "#292231", "#332b3e", "#40384e", "#534b64"],
    # mouth
    "K": ["#0c0508", "#1e0a12", "#3a1420", "#5a2030"],
}
STORM = ["#0c1a31", "#123055", "#1d4f8c", "#3478c4", "#62a8ec", "#a7d8ff", "#eaf8ff"]
EMBER = ["#240a07", "#4c150b", "#80260e", "#b8401a", "#e86a26", "#ffa347", "#ffe0a0"]
OUT = "#050509"
RIM = ["#27395a", "#314a70", "#45659a", "#6f95c8"]

MATS = list(RAMPS)
MI = {m: i for i, m in enumerate(MATS)}
RAMP_RGB = {m: np.array([hexc(c) for c in r], dtype=np.uint8) for m, r in RAMPS.items()}

LIGHT = np.array([-0.52, -0.72, 0.46]); LIGHT /= np.linalg.norm(LIGHT)
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


# =========================================================================== canvas
class Canvas:
    def __init__(self):
        self.mat = np.full((H, W), -1)
        self.nrm = np.zeros((H, W, 3)); self.nrm[..., 2] = 1
        self.bias = np.zeros((H, W))
        self.lvl = np.full((H, W), -1)       # direct level (flat materials) -1 = use lighting
        self.fixed = np.full((H, W), -1)      # index into FIXED colours
        self.pid = np.zeros((H, W), int)
        self.line = np.zeros((H, W), bool)
        self.rim = np.zeros((H, W), bool)
        self.n = 0
        self.fixed_cols = []

    def fx(self, col):
        if col not in self.fixed_cols:
            self.fixed_cols.append(col)
        return self.fixed_cols.index(col)

    def filled(self):
        return self.mat >= 0

    def paint(self, mask, nrm, mat, bias=0.0, seam=True, rim=True, lvl=None):
        mask = mask.copy()
        self.n += 1
        if seam:
            s = dil4(mask) & ~mask & self.filled()
            if seam == "soft":   # blend into hide (muscle growing out of the body), outline against anything else
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
        self.rim[mask] = rim
        return mask

    def put(self, pixels, col, only=None):
        """Fixed-colour decal on existing pixels (list of (x,y) or bool mask)."""
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
        """Fixed colour, creating pixels if needed (still part of the sprite, gets outlined)."""
        k = self.fx(col)
        self.n += 1
        for x, y in pixels:
            if 0 <= x < W and 0 <= y < H:
                if self.mat[y, x] < 0:
                    self.mat[y, x] = MI["H"]
                    self.rim[y, x] = False
                self.fixed[y, x] = k
                self.line[y, x] = False

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
            v = 0.10 + 0.90 * np.clip(ndl, 0, 1)
            if m in ("H", "P"):
                f = v * top * 0.95 + 0.15 + (95 - PY) * 0.010
            elif m in ("B", "D"):
                f = v * (top - 0.4) + 0.35
            else:
                f = v * top
            f = f + self.bias
            L = np.clip(np.floor(f), 0, top).astype(int)
            direct = self.lvl >= 0
            L = np.where(direct, np.clip(self.lvl + np.minimum(self.bias, 0) * 0, 0, top), L)
            level[sel] = L[sel]
        # speckle cleanup: a pixel whose 4 neighbours (same part) agree on another level adopts it
        for _ in range(2):
            same = [(shift(level, dx, dy), shift(self.pid, dx, dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            agree = np.ones((H, W), bool)
            ref = same[0][0]
            for lv, pd in same:
                agree &= (pd == self.pid) & (lv == ref)
            fix = agree & (ref != level) & filled & (self.lvl < 0)
            level = np.where(fix, ref, level)
        # sel-out interior contour lines
        level = np.where(self.line, np.minimum(level, np.where(level > 3, 1, 0)), level)
        for m in MATS:
            sel = (self.mat == MI[m])
            img[sel, :3] = RAMP_RGB[m][np.clip(level[sel], 0, len(RAMPS[m]) - 1)]
        img[filled, 3] = 255
        # rim light: silhouette pixels facing the storm light
        empty = ~filled
        edge_r = filled & (shift(empty, -1, 0) | shift(empty, 0, 1) | shift(empty, -1, 1))
        edge_r2 = filled & ~edge_r & (shift(empty, -2, 0) | shift(empty, 0, 2))
        face = self.nrm[..., 0] * RIMDIR[0] + self.nrm[..., 1] * RIMDIR[1]
        rimsel = edge_r & self.rim & (face > 0.5) & (self.nrm[..., 1] < 0.25) & ~self.line
        img[rimsel, :3] = np.where((face[rimsel] > 0.75)[:, None], np.array(hexc(RIM[2])), np.array(hexc(RIM[1])))
        # cool bounce light along the undersides (volume), 1px inside the lower silhouette
        edge_b = filled & shift(empty, 0, -1) & (self.nrm[..., 1] > 0.45) & ~self.line & self.rim
        img[edge_b & (self.mat == MI["H"]), :3] = np.array(hexc("#1f2536"))
        img[edge_b & (self.mat == MI["P"]), :3] = np.array(hexc("#2a2c3c"))
        # fixed colours on top
        for k, c in enumerate(self.fixed_cols):
            img[self.fixed == k, :3] = np.array(hexc(c))
        if outline:
            ring = dil4(filled) & ~filled
            img[ring] = (*hexc(OUT), 255)
        return Image.fromarray(img)


class FX:
    """Unoutlined glow overlay (lightning, fire, eye glow, sparks)."""

    def __init__(self):
        self.img = np.zeros((H, W, 4), np.uint8)

    def put(self, pts, col, under=None, only_empty=False):
        c = hexc(col)
        for x, y in pts:
            if 0 <= x < W and 0 <= y < H:
                if only_empty and self.img[y, x, 3]:
                    continue
                self.img[y, x] = (*c, 255)

    def put_mask(self, m, col):
        self.img[m] = (*hexc(col), 255)

    def image(self):
        return Image.fromarray(self.img)


# =========================================================================== parts
def body_tube(P):
    return Tube(P["spine"], per=20, step=0.35, flat=0.95)


def paint_body(C, P, tb, far_bias=0):
    """Tail + torso + neck: hide, belly plates, throat glow, chest embers."""
    lat, arc = tb.lat, tb.arc
    m = tb.mask
    s_hip, s_throat = P["plates"]
    bias = np.zeros((H, W))
    # smooth ambient occlusion toward the belly and in the neck crook
    bias -= np.clip(lat - 0.55, 0, 1) * 1.2
    C.paint(m, tb.nrm, "H", bias=bias)
    ndl = (tb.nrm * LIGHT).sum(-1)
    band = m & (lat < -0.30) & (lat > -0.97) & (arc > 30) & (arc < s_throat + 12) & (ndl > 0.30)
    rowf = (lat + 1.0) / 0.24
    row = np.floor(rowf); fr = rowf - row
    uu = arc / 3.4 + row * 0.5 + (fr - 0.5) ** 2 * 1.4
    fu = uu - np.floor(uu)
    C.bias[band & (fu < 0.28)] -= 1.0
    C.bias[band & (fu > 0.36) & (fu < 0.62) & (fr < 0.45)] += 0.6
    plate = m & (lat > 0.40) & (arc > s_hip) & (arc < s_throat)
    # plates narrow toward the ends
    span = s_throat - s_hip
    tpos = np.clip((arc - s_hip) / span, 0, 1)
    plate &= lat > 0.40 + 0.35 * (np.abs(tpos - 0.45) / 0.55) ** 3
    pb = np.full((H, W), 1.6)
    pb -= np.clip(lat - 0.82, 0, 1) * 5.0
    sp = np.where(tpos > 0.62, 3.0, 4.0)
    groove = plate & (np.mod(arc - s_hip, sp) < 1.0)
    C.paint(plate, tb.nrm, "P", bias=pb, seam=False, rim=True)
    # band edge line
    bandedge = plate & ~shift(plate, 0, -1) & ~shift(plate, 0, 1) | (plate & ~(shift(plate, 0, -1) & shift(plate, 1, 0) & shift(plate, -1, 0) & shift(plate, 0, 1)) & (lat < 0.62))
    C.bias[bandedge & (lat < 0.62)] -= 1.5
    # grooves: faint storm-blue seams in the throat, a banked ember glow deep in the chest, plain elsewhere
    throat = groove & (tpos > 0.66) & (lat > 0.55) & (lat < 0.92)
    chest = groove & (tpos > 0.30) & (tpos < 0.52) & (lat > 0.52) & (lat < 0.90)
    plain = groove & ~throat & ~chest
    C.bias[groove] -= 2.0
    tg = P.get("throat", 1)
    tplate = plate & (tpos > 0.66) & (lat > 0.56) & (lat < 0.88) & ~groove
    tcore = tplate & (lat > 0.64) & (lat < 0.78)
    if tg == 1:
        C.put(throat, STORM[1])
    elif tg == 2:
        C.put(tplate, STORM[1]); C.put(throat, STORM[0])
    elif tg >= 3:
        C.put(tplate, STORM[2]); C.put(tcore, STORM[3]); C.put(throat, STORM[1])
    # banked coals: an oval of warmth under the chest plates, brightest in the seams at its heart
    tc = 0.42
    heat = 1.0 - np.hypot((tpos - tc) / 0.13, (lat - 0.72) / 0.22)
    warm = plate & (heat > 0) & ~groove
    C.put(warm & (heat > 0.0) & (heat <= 0.45), "#3a2226")
    C.put(warm & (heat > 0.45), "#4e2a24")
    seam_hot = groove & (heat > -0.25) & (lat > 0.5)
    C.put(seam_hot & (heat <= 0.3), EMBER[1])
    C.put(seam_hot & (heat > 0.3) & (heat <= 0.65), EMBER[2])
    C.put(seam_hot & (heat > 0.65), EMBER[3])


def paint_ridge(C, P, tb, far=False):
    """Back-swept dorsal spines along the spine curve (drawn before the body so it overlaps their roots)."""
    L = tb.length
    s0, s1 = P["ridge"]
    sizef = P.get("ridge_size", lambda t: 1.0)
    s = s0
    while s < min(s1, L - 2):
        t = (s - s0) / (s1 - s0)
        p, T, N, rd, rv = tb.at(s)
        h = 1.2 + 5.2 * math.sin(math.pi * min(1, t * 1.25)) ** 1.4 * sizef(t)
        base = p - N * (rd - 0.9)
        dirv = -N * 0.62 - T * 0.78
        dirv /= np.hypot(*dirv)
        tip = base + dirv * h
        ctrl = base + dirv * h * 0.55 + (-N) * h * 0.25
        pts = qbez(base, ctrl, tip, 10)
        keys = [(x, y, r, r) for (x, y), r in zip(pts, np.linspace(max(1.0, h * 0.34), 0.35, 10))]
        sp = Tube(keys, per=6, step=0.3, clean_it=1)
        C.paint(sp.mask, sp.nrm, "D", bias=(-1 if far else 0), seam=False)
        s += 3.2 + h * 0.55


def paint_tail_barbs(C, P, tb):
    """Whip end: small back-swept barbs on both edges + a slender spade blade."""
    L = tb.length
    for k, s in enumerate(np.arange(L - 34, L - 6, 6.5)):
        p, T, N, rd, rv = tb.at(s)
        for side in (-1, 1):
            if side == 1 and k % 2 == 0:
                continue
            base = p + N * side * max(rd, 0.8) * 0.8
            tip = base + (N * side * 0.75 - T * 0.66) * (2.6 + k * 0.2)
            pts = qbez(base, (base + tip) / 2 + N * side * 0.6, tip, 8)
            keys = [(x, y, r, r) for (x, y), r in zip(pts, np.linspace(0.95, 0.35, 8))]
            bt = Tube(keys, per=6, step=0.3, clean_it=0)
            C.paint(bt.mask & ~C.filled(), bt.nrm, "D", seam=False)
    # spade: leaf blade continuing the tangent, with two recurved flukes
    p, T, N, rd, rv = tb.at(L - 1)
    tip = p + T * 11
    lw = P.get("spade_w", 3.2)
    left = [p + T * (6 * t) + N * (-lw * math.sin(math.pi * min(1, t * 1.15)) - 0.2) for t in np.linspace(0, 1, 10)]
    right = [p + T * (6 * t) + N * (lw * math.sin(math.pi * min(1, t * 1.15)) + 0.2) for t in np.linspace(0, 1, 10)]
    fl = p - T * 2.5 + N * (-lw - 1.2); fr = p - T * 2.5 + N * (lw + 1.2)
    outline = [p - T * 1.0, fl, p + T * 1.2 + N * (-lw * 0.9)] + [p + T * (1.2 + 9.8 * t) + N * (-lw * 0.9 * (1 - t) ** 1.3) for t in np.linspace(0.05, 1, 10)] \
              + [p + T * (1.2 + 9.8 * t) + N * (lw * 0.9 * (1 - t) ** 1.3) for t in np.linspace(1, 0.05, 10)] + [p + T * 1.2 + N * (lw * 0.9), fr]
    m = clean(poly_mask(outline), 1)
    # blade normal: ridge along the tangent
    d = (PX - p[0]) * N[0] + (PY - p[1]) * N[1]
    nx = -N[0] * np.sign(d) * 0.55; ny = -N[1] * np.sign(d) * 0.55
    nr = np.stack([-nx, -ny, np.full((H, W), 0.8)], -1)
    C.paint(m, nr, "D", bias=0.5)


def leg(C, hip, knee_pref, ankle, foot, sz=1.0, bias=0, toes=1.0):
    """Digitigrade hind leg: heavy thigh, lean shin, long metatarsus, three toes with bone talons."""
    L1, L2 = 22 * sz, 20 * sz
    hip, ankle, foot = v2(hip), v2(ankle), v2(foot)
    d = ankle - hip
    dist = np.hypot(*d)
    if dist >= L1 + L2 - 0.01:
        knee = hip + d * L1 / (L1 + L2)
    else:
        a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
        hh = math.sqrt(max(0, L1 * L1 - a * a))
        u = d / dist
        mid = hip + u * a
        c1 = mid + np.array([-u[1], u[0]]) * hh; c2 = mid - np.array([-u[1], u[0]]) * hh
        pref = v2(knee_pref)
        knee = c1 if (c1 - mid) @ pref >= (c2 - mid) @ pref else c2
    fwd = 1.0
    # toes first (behind the foot pad)
    for k, (ang, ln) in enumerate(((10, 7.0), (28, 6.0), (-8, 5.0))):
        if k == 2 and toes < 1:
            continue
        dv = np.array(rotv((1, 0), ang)) * fwd
        t0 = foot + np.array([0.5, -0.8])
        t1 = t0 + dv * ln * sz
        tt = cap(t0, t1, 1.9 * sz, 1.3 * sz, clean_it=1)
        C.paint(tt.mask, tt.nrm, "H", bias=bias - (1 if k == 2 else 0))
        cl = qbez(t1 + (-0.5, -0.3), t1 + dv * 2.6 + (0, 0.4), t1 + dv * 3.2 + (0.4, 2.6), 10)
        keys = [(x, y, r, r) for (x, y), r in zip(cl, np.linspace(1.25, 0.35, 10))]
        ct = Tube(keys, per=6, step=0.3, clean_it=0)
        C.paint(ct.mask, ct.nrm, "B", bias=bias - (1 if k == 2 else 0), seam=True)
    meta = cap(ankle, foot, 2.9 * sz, 2.3 * sz, clean_it=1)
    C.paint(meta.mask, meta.nrm, "H", bias=bias)
    # heel spur
    sp = qbez(ankle + (0.5, 0.5), ankle + (-3, 1), ankle + (-5.5, 3.5), 8)
    keys = [(x, y, r, r) for (x, y), r in zip(sp, np.linspace(1.2, 0.35, 8))]
    st = Tube(keys, per=6, step=0.3, clean_it=0)
    C.paint(st.mask & ~C.filled(), st.nrm, "D", bias=bias, seam=False)
    shin = cap(knee, ankle, 4.6 * sz, 2.9 * sz, bulge=0.8 * sz, bend=-1.0, clean_it=1)
    C.paint(shin.mask, shin.nrm, "H", bias=bias)
    thigh = cap(hip, knee, 9.2 * sz, 4.4 * sz, bulge=1.8 * sz, bt=0.4, bend=1.8, flat=0.9)
    C.paint(thigh.mask, thigh.nrm, "H", bias=bias + 0.3)
    return knee


def arm(C, A, bias=0):
    """Lean muscular foreleg: shoulder -> elbow -> wrist -> hand, three hooked bone talons."""
    sh, el, wr, hd = (v2(A[k]) for k in ("shoulder", "elbow", "wrist", "hand"))
    sz = A.get("sz", 1.0)
    cd = v2(A.get("claw_dir", (1, 0.35)))
    cd /= np.hypot(*cd)
    for k, (ang, ln) in enumerate(((-18, 4.5), (4, 5.0), (24, 4.2))):
        dv = np.array(rotv(cd, ang))
        f0 = hd
        f1 = hd + dv * ln * sz
        ft = cap(f0, f1, 1.7 * sz, 1.2 * sz, clean_it=1)
        C.paint(ft.mask, ft.nrm, "H", bias=bias - (1 if k == 0 else 0))
        curl = np.array(rotv(dv, 70))
        cl = qbez(f1, f1 + dv * 2.4, f1 + dv * 2.6 + curl * 2.8, 10)
        keys = [(x, y, r, r) for (x, y), r in zip(cl, np.linspace(1.15, 0.35, 10))]
        ct = Tube(keys, per=6, step=0.3, clean_it=0)
        C.paint(ct.mask, ct.nrm, "B", bias=bias - (1 if k == 0 else 0))
    hand = cap(wr, hd, 2.4 * sz, 2.2 * sz, clean_it=1)
    C.paint(hand.mask, hand.nrm, "H", bias=bias)
    fa = cap(el, wr, 3.3 * sz, 2.2 * sz, bulge=0.9 * sz, bt=0.3, bend=A.get("fore_bend", -1.0), clean_it=1)
    C.paint(fa.mask, fa.nrm, "H", bias=bias)
    # elbow spur
    ev = (el - wr) / np.hypot(*(el - wr))
    sp = qbez(el, el + ev * 2.5, el + ev * 5.0 + np.array(rotv(ev, 90)) * 1.5, 8)
    keys = [(x, y, r, r) for (x, y), r in zip(sp, np.linspace(1.3, 0.35, 8))]
    et = Tube(keys, per=6, step=0.3, clean_it=0)
    C.paint(et.mask & ~fa.mask, et.nrm, "D", bias=bias + 0.5, seam=False)
    ua = cap(sh, el, 5.4 * sz, 2.9 * sz, bulge=1.1 * sz, bt=0.3, bend=A.get("up_bend", 1.2))
    C.paint(ua.mask, ua.nrm, "H", bias=bias + 0.2, seam="soft")


def wing(C, W_, bias=0, phase=1, far=False, seed=0):
    """Wing-arm: humerus, forearm, thumb talon, four finger bones, scalloped tattered backlit membrane."""
    sh, el, wr = v2(W_["shoulder"]), v2(W_["elbow"]), v2(W_["wrist"])
    tips = [v2(t) for t in W_["tips"]]
    root = v2(W_["root"])
    bends = W_.get("bends", [2.0, 3.0, 3.0, 2.5])
    sag = W_.get("sag", [0.28, 0.30, 0.30, 0.34])
    fingers = []
    for k, tp in enumerate(tips):
        d = tp - wr
        nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
        fingers.append(qbez(wr, (wr + tp) / 2 + nrm * bends[k] * (-1 if far else 1) * W_.get("bend_sign", 1), tp, 60))
    # ---------------- membrane outline
    def scallop(a, b, s):
        mid = (a + b) / 2
        c = mid + (wr - mid) * s
        return list(qbez(a, c, b, 30))
    poly = [sh, el, wr] + list(fingers[0])
    for k in range(len(tips) - 1):
        poly += scallop(tips[k], tips[k + 1], sag[k])
    poly += scallop(tips[-1], root, sag[-1])
    poly += list(qbez(root, (root + sh) / 2 + (sh - root) * 0.0, sh, 10))
    mem = clean(poly_mask(poly), 2)
    # tatters: notches cut into trailing scallops and a few torn holes
    rng = np.random.RandomState(seed)
    for k in range(len(tips)):
        a, b = tips[k], (tips[k + 1] if k + 1 < len(tips) else root)
        for j in range(W_.get("notches", 2)):
            t = 0.25 + rng.rand() * 0.5
            mid = (a + b) / 2
            c = mid + (wr - mid) * sag[k]
            p = (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t * t * b
            inward = (wr - p) / np.hypot(*(wr - p))
            depth = 4.0 + rng.rand() * 6.0
            w = 0.9 + rng.rand() * 0.9
            side = np.array([-inward[1], inward[0]])
            tri = [p - side * w + inward * -1, p + side * w + inward * -1, p + inward * depth + side * rng.uniform(-1, 1)]
            mem &= ~poly_mask(tri)
    for (hx, hy, hr) in W_.get("holes", []):
        c = wr + (tips[int(hx)] - wr) * hy + (tips[min(int(hx) + 1, len(tips) - 1)] - tips[int(hx)]) * (hx % 1)
        mem &= ~ell_mask(c, hr * 1.5, hr * 0.42, ang=math.degrees(math.atan2(*(c - wr)[::-1])))
    mem = clean(mem, 1)
    # ---------------- membrane shading (flat, backlit): thin skin far from the bones glows through
    bone_pts = np.vstack(fingers + [qbez(sh, (sh + el) / 2, el, 20), qbez(el, (el + wr) / 2, wr, 20)])
    dB = dist_to(bone_pts)
    edge = mem & ~(shift(mem, 1, 0) & shift(mem, -1, 0) & shift(mem, 0, 1) & shift(mem, 0, -1))
    dW = np.hypot(PX - wr[0], PY - wr[1])
    reach = max(np.hypot(*(t - wr)) for t in tips)
    outside = ~mem
    hem = mem & dil4(outside) & (dB > 2.5)
    hy, hx = np.nonzero(hem)
    dT = dist_to(np.stack([hx + 0.5, hy + 0.5], 1)) if len(hx) else np.full((H, W), 99.0)
    sm = lambda x, a, b: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
    lv = 1.6 + 1.3 * sm(dB, 1.5, 10) + 1.4 * sm(dW / reach, 0.35, 0.95) + 1.1 * (1 - sm(dT, 1.0, 7.0))
    under = C.filled()
    lv -= under * (1.6 if not far else 0.8)          # body seen through the membrane
    lv += bias
    lv = np.floor(lv)
    lv[hem] += 1                                      # translucent trailing rim
    C.paint(mem, None, "M", lvl=np.clip(lv, 0, 7).astype(int), rim=False, seam=True)
    folded = W_.get("folded", False)
    if folded:
        # folded fan: the hidden fingers show only as pleats (dark crease + lit ridge)
        for k, f in enumerate(fingers[1:], 1):
            dk = [p for p in pp_pixels(f[6:58]) if 0 <= p[0] < W and 0 <= p[1] < H and mem[p[1], p[0]]]
            C.put(dk, RAMPS["M"][int(max(0, 0 + bias))])
            lt = [(x, y - 1) for (x, y) in dk if 0 <= y - 1 < H and mem[y - 1, x]]
            C.put(lt, RAMPS["M"][int(max(0, 5 + bias))])
    for k, f in enumerate(fingers[1:] if not folded else [], 1):
        d = f[-1] - f[0]
        nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
        off = f[8:48] + nrm * (1.6 if not far else -1.6) * W_.get("crease_side", 1)
        pts = [p for p in pp_pixels(off) if 0 <= p[0] < W and 0 <= p[1] < H and mem[p[1], p[0]]]
        C.put(pts, RAMPS["M"][max(0, 1 + bias)])
    # ---------------- storm veins along the bones (thin, elegant)
    vein_pts = []
    for k, f in enumerate(fingers if not folded else fingers[:1]):
        d = f[-1] - f[0]
        nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
        side = -1 if k == 0 else 1
        n_end = 52 if phase == 1 else 57
        off = f[5:n_end] + nrm * side * (2.0) * W_.get("crease_side", 1) * (-1 if far else 1)
        pts = [p for p in pp_pixels(off) if 0 <= p[0] < W and 0 <= p[1] < H and mem[p[1], p[0]]]
        vein_pts.append(pts)
        # a fork into the membrane
        if folded:
            vein_pts.append([])
            continue
        j = int(len(f) * 0.55)
        a = f[j] + nrm * side * 2.0
        tipv = f[j] + (f[-1] - f[j]) * 0.35 + nrm * side * (6 + 3 * (k % 2))
        fk = [p for p in pp_pixels(qbez(a, (a + tipv) / 2 + nrm * side, tipv, 16)) if 0 <= p[0] < W and 0 <= p[1] < H and mem[p[1], p[0]]]
        vein_pts.append(fk)
    # ---------------- arm & fingers (bones on top of the membrane)
    for k, f in enumerate(fingers if not folded else fingers[:1]):
        rr = np.linspace(W_.get("finger_r", 1.9) * (1.0 - 0.1 * k), 0.45, len(f))
        keys = [(x, y, r, r) for (x, y), r in zip(f[::6], rr[::6])] + [(f[-1][0], f[-1][1], 0.4, 0.4)]
        ft = Tube(keys, per=8, step=0.3, clean_it=1)
        C.paint(ft.mask, ft.nrm, "H", bias=bias + 0.4, rim=False)
    fr = W_.get("fore_r", (2.6, 1.7))
    fa = cap(el, wr, fr[0], fr[1], bulge=0.9, bt=0.22, bend=W_.get("fore_bend", -1.5))
    C.paint(fa.mask, fa.nrm, "H", bias=bias)
    # elbow spur (bone), pointing back along the humerus line
    ev = (el - sh) / np.hypot(*(el - sh))
    sp = qbez(el, el + ev * 3.0 + np.array([-ev[1], ev[0]]) * 1.0, el + ev * 6.0 + np.array([-ev[1], ev[0]]) * 2.5, 10)
    keys = [(x, y, r, r) for (x, y), r in zip(sp, np.linspace(1.4, 0.35, 10))]
    et = Tube(keys, per=6, step=0.3, clean_it=0)
    C.paint(et.mask & ~fa.mask, et.nrm, "D", bias=bias + 0.5, seam=False)
    hr = W_.get("hum_r", (4.8, 2.4))
    hu = cap(sh, el, hr[0], hr[1], bulge=1.3, bt=0.35, bend=W_.get("hum_bend", 1.5))
    C.paint(hu.mask, hu.nrm, "H", bias=bias, seam="soft")
    # shoulder / pectoral mass the arm grows out of (no seam: one muscle)
    d = (el - sh) / np.hypot(*(el - sh))
    sc_ = W_.get("shoulder_sz", 0.0)
    if sc_:
        dome = cap(sh - d * 3 * sc_, sh + d * 4 * sc_, 6.2 * sc_, 4.2 * sc_, clean_it=1)
        C.paint(dome.mask, dome.nrm, "H", bias=bias - 0.2, seam=False)
    # wrist knuckle + thumb talon
    kn = Tube([(wr[0], wr[1], 2.6, 2.6), (wr[0] + 1.0, wr[1] + 0.5, 2.4, 2.4)], clean_it=0)
    C.paint(kn.mask, kn.nrm, "H", bias=bias + 0.4, seam=False)
    th = v2(W_.get("thumb", (4, 5)))
    tu = th / np.hypot(*th)
    hook = np.array([-tu[1], tu[0]]) * (1 if th[0] >= 0 else -1)
    b0 = wr + tu * 1.2
    cl = qbez(b0, b0 + tu * 3.5, b0 + tu * 5.5 + hook * 2.2, 16)
    keys = [(x, y, r, r) for (x, y), r in zip(cl, np.linspace(1.35, 0.35, 16))]
    ct = Tube(keys, per=6, step=0.3, clean_it=0)
    C.paint(ct.mask, ct.nrm, "B", bias=bias - 3.0 * np.clip(1 - ct.arc / 4.0, 0, 1))
    return dict(veins=vein_pts, fingers=fingers, mem=mem, wrist=wr, tips=tips)


def paint_veins(C, fxl, info, phase, far=False):
    for i, pts in enumerate(info["veins"]):
        fork = i % 2 == 1
        n = len(pts)
        for j, (x, y) in enumerate(pts):
            t = j / max(1, n - 1)
            if phase == 1:
                c = STORM[2] if t < 0.45 else STORM[1]
                if far:
                    c = STORM[1] if t < 0.5 else STORM[0]
                if fork:
                    c = STORM[1] if not far else STORM[0]
                C.put([(x, y)], c)
            else:
                c = STORM[5] if t < 0.7 else STORM[4]
                if fork:
                    c = STORM[4] if t < 0.6 else STORM[3]
                if far:
                    c = STORM[4] if not fork else STORM[3]
                C.put([(x, y)], c)
        if phase == 2:
            # soft halo on the membrane either side
            for (x, y) in pts:
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    q = (x + dx, y + dy)
                    if 0 <= q[0] < W and 0 <= q[1] < H and info["mem"][q[1], q[0]] and C.fixed[q[1], q[0]] < 0 \
                            and C.mat[q[1], q[0]] == MI["M"]:
                        C.put([q], STORM[1] if not far else STORM[0])


# ----------------------------------------------------------------------------- head
def head(C, fxl, P):
    """Small wedge skull, swept crown of long thin horns, hinged jaw with fine teeth, cold slit eye."""
    hp = v2(P["head"]); ang = P["head_ang"]; jaw = P.get("jaw", 0)
    sc = P.get("head_sc", 1.15)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    U = np.array([ca, sa]); V = np.array([-sa, ca])

    def w(x, y):
        return hp + U * x * sc + V * y * sc

    def wj(x, y):  # lower-jaw space (rotated about the hinge)
        hx, hy = 2.0, 2.4
        dx, dy = rotv((x - hx, y - hy), jaw)
        return w(hx + dx, hy + dy)

    hdec = P.get("horn_decouple", 0.7)

    def hw(base, q):
        b = w(*base)
        d = (w(*q) - b)
        return b + np.array(rotv(d, -ang * hdec))

    def horn(base, ctrl, tip, r0, bias):
        pts = qbez(w(*base), hw(base, ctrl), hw(base, tip), 40)
        keys = [(x, y, r, r) for (x, y), r in zip(pts[::4], np.linspace(r0 * sc, 0.4, 10))] + [(*pts[-1], 0.35, 0.35)]
        t = Tube(keys, per=8, step=0.25, clean_it=1)
        b = np.zeros((H, W))
        # darker root, pale tips
        b += np.clip(1.0 - t.arc / 9.0, 0, 1) ** 1.5 * -3.2
        C.paint(t.mask, t.nrm, "B", bias=b + bias, rim=False)

    crown = P.get("crown", 1.0)
    # far-side horns (behind the skull)
    hl = P.get("horn_len", 1.0)
    horn((2.5, -3.9), (-8, -7.0 * crown), (-20 * hl, -19 * crown), 1.7, -1.8)
    # lower jaw
    jkeys = [(*wj(0.5, 2.8), 2.2 * sc, 2.7 * sc), (*wj(8, 3.5), 1.7 * sc, 2.1 * sc), (*wj(15, 3.3), 1.3 * sc, 1.6 * sc),
             (*wj(20.5, 3.0), 1.0 * sc, 1.2 * sc), (*wj(23.0, 2.7), 0.7, 0.8)]
    jt = Tube(jkeys, per=12, step=0.3, clean_it=1)
    if jaw > 3:
        # mouth interior
        top = [w(x, 2.2 + 0.05 * x) for x in np.linspace(24, 3, 12)]
        bot = [wj(x, 1.4 + 0.02 * x) for x in np.linspace(3, 23, 12)]
        mm = poly_mask(top + bot)
        dd = np.hypot(PX - w(3, 2.6)[0], PY - w(3, 2.6)[1])
        C.paint(mm, None, "K", lvl=np.clip(3 - (dd / (7 * sc)).astype(int), 0, 3), rim=False, seam=False)
        # throat glow at the back of the mouth
        g = P.get("mouth_glow", None)
        if g is not None:
            gm = mm & (dd < 5.0 * sc)
            C.put(gm, g[0])
            C.put(mm & (dd < 2.6 * sc), g[1])
    C.paint(jt.mask, jt.nrm, "H", bias=-0.4)
    # upper skull: wedge, brow shelf, slight beak hook at the tip
    keys = [(*w(-3.0, -0.3), 3.8 * sc, 3.4 * sc), (*w(1.5, -0.7), 4.7 * sc, 3.3 * sc), (*w(6.5, -0.4), 4.3 * sc, 2.8 * sc),
            (*w(12, 0.3), 3.3 * sc, 2.4 * sc), (*w(18, 0.9), 2.6 * sc, 2.0 * sc), (*w(22.5, 1.5), 1.9 * sc, 1.6 * sc),
            (*w(24.9, 2.1), 1.35, 1.25)]
    sk = Tube(keys, per=12, step=0.3, flat=0.95, clean_it=2)
    C.paint(sk.mask, sk.nrm, "H", bias=1.4)
    # jaw line of fine teeth
    mouth = [w(x, 2.1 + 0.07 * x) for x in np.linspace(9, 23.5, 40)]
    ml = pp_pixels(mouth)
    C.put(ml, RAMPS["H"][0])
    if jaw <= 3:
        teeth = []
        for x in np.arange(10, 23, 2.0):
            p = w(x, 2.1 + 0.07 * x + 1.0)
            teeth.append((int(p[0]), int(p[1])))
        C.put(teeth, RAMPS["B"][4])
    else:
        up, lo = [], []
        for x in np.arange(6.5, 23.5, 1.9):
            p = w(x, 2.2 + 0.05 * x + 0.9)
            q = w(x, 2.2 + 0.05 * x + 1.9)
            up += [(int(p[0]), int(p[1]))]
            if x < 22 and x > 8:
                up += [(int(q[0]), int(q[1]))]
        for x in np.arange(7.5, 22.5, 2.1):
            p = wj(x, 1.4 + 0.02 * x - 0.9)
            lo += [(int(p[0]), int(p[1]))]
        C.put_any(up, RAMPS["B"][4])
        C.put_any(lo, RAMPS["B"][3])
    # cheekbone: crease from under the eye back to the jaw hinge, lit ridge above it
    ck = pp_pixels([w(x, 0.9 - 0.12 * (x - 8)) for x in np.linspace(12.0, 0.5, 24)])
    C.put(ck, RAMPS["H"][1], only=(C.mat == MI["H"]))
    ckh = pp_pixels([w(x, -0.1 - 0.12 * (x - 8)) for x in np.linspace(10.5, 2.0, 18)])
    C.put(ckh, RAMPS["H"][5], only=(C.mat == MI["H"]))
    # nostril
    n0 = w(21.5, 0.4)
    C.put([(int(n0[0]), int(n0[1]))], RAMPS["H"][0])
    # brow ridge: sinister shelf angled down to the snout, eye tucked beneath
    brow = pp_pixels([w(x, -2.8 + 0.22 * (x - 3)) for x in np.linspace(3.0, 10.5, 20)])
    C.put(brow, RAMPS["H"][1])
    brow_hi = pp_pixels([w(x, -3.8 + 0.22 * (x - 3)) for x in np.linspace(3.5, 9.5, 20)])
    C.put(brow_hi, RAMPS["H"][6])
    e0, e1 = w(5.6, -1.3), w(9.8, -0.5)
    eye = pp_pixels(np.linspace(e0, e1, 12))
    C.put(eye, STORM[4])
    C.put(eye[len(eye) // 2: len(eye) // 2 + 1], STORM[6])
    C.put(eye[:1], STORM[3])
    # cold glow trailing back from the eye (FX, over the hide)
    trail = pp_pixels([w(x, -1.3 - 0.05 * (6 - x)) for x in np.linspace(5.8, 1.0, 12)])
    fxl.put(trail[1:4], STORM[3])
    fxl.put(trail[4:6], STORM[2])
    P["_eye"] = eye
    # near-side horns (in front): the long crown sweep + cheek spikes
    horn((0.0, -3.6), (-11, -4.0 * crown), (-25 * hl, -16 * crown), 2.1, 0.0)
    horn((-2.5, -0.4), (-8, 0.2), (-14 * hl, -3.0 * crown), 1.4, -0.8)
    horn((0.0, 2.8), (-4.5, 3.6), (-8.5, 5.8), 1.0, -1.0)
    # small brow spur over the eye and a nasal ridge horn: a crueller, more draconic wedge
    horn((4.5, -4.2), (2.5, -5.6), (-0.5, -6.4), 0.9, -0.6)
    return w, wj


# =========================================================================== FX
def bolt(a, b, rng, amp=0.15, depth=5):
    pts = [v2(a), v2(b)]
    for _ in range(depth):
        out = [pts[0]]
        for p, q in zip(pts[:-1], pts[1:]):
            d = q - p
            L = np.hypot(*d)
            n = np.array([-d[1], d[0]]) / (L or 1)
            m = (p + q) / 2 + n * rng.uniform(-1, 1) * L * amp
            out += [m, q]
        pts = out
        amp *= 0.62
    dense = []
    for p, q in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 6, endpoint=False):
            dense.append(p + (q - p) * t)
    dense.append(pts[-1])
    return pp_pixels(dense), pts


def lightning(fxl, a, b, rng, bright=1.0, branches=2):
    px, pts = bolt(a, b, rng)
    # soft glow only on the trunk's first half, one side (reads as bloom, not noise)
    half = px[: len(px) // 2]
    fxl.put([(x + 1, y) for (x, y) in half], STORM[2], only_empty=True)
    fxl.put(px, STORM[5] if bright < 1 else STORM[6])
    fxl.put(px[:2], STORM[6])
    for k in range(branches):
        i = rng.randint(len(pts) // 4, 3 * len(pts) // 4)
        p = pts[i]
        d = v2(b) - v2(a)
        ang = rng.uniform(-50, 50)
        e = p + np.array(rotv(d / np.hypot(*d), ang)) * rng.uniform(6, 14)
        bp, _ = bolt(p, e, rng, amp=0.22, depth=3)
        fxl.put(bp, STORM[4] if k == 0 else STORM[3])


def fire(fxl, C, mouth, ang, length, w0=1.6, spread=0.20, seed=3):
    """Start of the breath: blue-white core at the lips blooming into an orange stream."""
    U = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); V = np.array([-U[1], U[0]])
    dx, dy = PX - mouth[0], PY - mouth[1]
    s = dx * U[0] + dy * U[1]
    l = dx * V[0] + dy * V[1]
    wig = np.sin(s * 0.33 + 1.0) * 0.8 + np.sin(s * 0.71 + 2.0) * 0.5 * np.clip(s / 30, 0, 1)
    l2 = l - wig * np.clip(s / 20, 0, 1)
    wd = w0 + s * spread + np.sin(s * 0.9) * 0.4 * np.clip(s / 25, 0, 1)
    r = np.abs(l2) / np.maximum(wd, 0.5)
    inside = (s > 0) & (s < length) & (r < 1.0)
    # ragged licks at the edge
    lick = (s > 8) & (s < length * 1.05) & (r >= 1.0) & (r < 1.45) & \
           (np.sin(s * 0.55 - np.sign(l2) * 1.3) > 0.35) & (np.sin(s * 1.7 + l2) > -0.2)
    tail = (s >= length) & (s < length + 10) & (r < 1.0 - (s - length) / 10.0)
    fs = s / length
    heat = (1 - r) * 1.1 + (1 - fs) * 0.7  # 0..1.8
    cols = [(1.45, STORM[6]), (1.2, STORM[5]), (1.0, "#fff2c8"), (0.8, EMBER[6]), (0.55, EMBER[5]), (0.32, EMBER[4]),
            (0.12, EMBER[3]), (-9, EMBER[2])]
    img = fxl.img
    allowed = (C.mat < 0) | (C.mat == MI["K"])
    m_all = (inside | tail) & allowed
    lick &= allowed
    blue_zone = s < 14
    for thr, c in reversed(cols):
        sel = m_all & (heat >= thr)
        img[sel] = (*hexc(c), 255)
    # near the lips the core is storm-blue-white, edges cold blue
    img[m_all & blue_zone & (r > 0.55)] = (*hexc(STORM[4]), 255)
    img[m_all & blue_zone & (r <= 0.55)] = (*hexc(STORM[6]), 255)
    img[m_all & (s >= 14) & (s < 22) & (r > 0.72)] = (*hexc(STORM[3]), 255)
    img[lick & (s < 20)] = (*hexc(STORM[2]), 255)
    img[lick & (s >= 20)] = (*hexc(EMBER[2]), 255)
    # sparks
    rng = np.random.RandomState(seed)
    for _ in range(26):
        ss = rng.uniform(10, length + 6)
        ll = rng.uniform(-1, 1) * (w0 + ss * spread) * 1.6
        p = mouth + U * ss + V * ll
        x, y = int(p[0]), int(p[1])
        if 0 <= x < W and 0 <= y < H and not img[y, x, 3]:
            img[y, x] = (*hexc(EMBER[5] if rng.rand() < 0.5 else EMBER[4]), 255)


# =========================================================================== poses
POSES = {}

POSES["idle"] = dict(
    label="1  GROUNDED IDLE - coiled, head low, wings folded",
    ground=150,
    spine=[(5, 128, 0.5, 0.5), (12, 141, 1.0, 1.0), (26, 147, 1.7, 1.7), (46, 146, 2.7, 2.7), (64, 138, 4.3, 4.3),
           (80, 124, 7.5, 8.0), (98, 113, 10.5, 12.5), (118, 110, 11.5, 14.5), (136, 108, 10.0, 12.5),
           (150, 100, 6.6, 7.2), (160, 91, 5.1, 5.3), (171, 86, 4.4, 4.5), (182, 86, 3.9, 4.0), (192, 90, 3.7, 3.7),
           (199, 96, 3.5, 3.5)],
    plates=(95, 205), ridge=(40, 212), throat=1,
    head=(199, 96), head_ang=18, jaw=0,
    legs=[dict(hip=(90, 118), knee=(1, 0), ankle=(84, 143), foot=(92, 147), bias=-1.4, sz=0.95),
          dict(hip=(96, 120), knee=(1, 0), ankle=(92, 145), foot=(101, 148), bias=0.0, sz=1.0)],
    arms=[dict(shoulder=(141, 112), elbow=(135, 130), wrist=(152, 141), hand=(158, 146), bias=-1.4, sz=0.95),
          dict(shoulder=(134, 114), elbow=(127, 132), wrist=(143, 142), hand=(149, 147), bias=0.0)],
    wings=[dict(shoulder=(130, 97), elbow=(112, 85), wrist=(143, 63), thumb=(4, -3),
                tips=[(70, 86), (74, 89), (78, 92), (83, 95)], root=(104, 99), sag=[0.03, 0.03, 0.03, 0.08],
                bends=[7, 7, 6, 5], notches=0, holes=[], hum_r=(3.6, 2.0), fore_r=(2.2, 1.5), fore_bend=1.0,
                hum_bend=1.0, bias=-1.6, folded=True, shoulder_sz=0.7),
           dict(shoulder=(124, 99), elbow=(104, 89), wrist=(136, 67), thumb=(4, -3),
                tips=[(56, 94), (60, 97), (64, 100), (69, 103)], root=(96, 104), sag=[0.03, 0.03, 0.03, 0.08],
                bends=[7, 7, 6, 5], notches=0, holes=[], hum_r=(4.0, 2.2), fore_r=(2.4, 1.6), fore_bend=1.0,
                hum_bend=1.0, bias=0, folded=True, shoulder_sz=0.8)],
)

POSES["roar"] = dict(
    label="2  REARING ROAR - wings flung wide (intro key art)",
    ground=150,
    spine=[(6, 118, 0.5, 0.5), (12, 133, 1.0, 1.0), (24, 144, 1.7, 1.7), (44, 148, 2.6, 2.6), (66, 144, 4.2, 4.2),
           (86, 132, 7.5, 8.0), (100, 116, 10.0, 12.0), (110, 98, 11.0, 13.5), (118, 82, 10.0, 12.0),
           (124, 67, 6.6, 7.2), (127, 54, 5.1, 5.3), (133, 43, 4.4, 4.5), (143, 36, 3.9, 4.0), (153, 34, 3.7, 3.7),
           (160, 35, 3.5, 3.5)],
    plates=(95, 205), ridge=(40, 212), throat=3, halo=(150, 46, 78),
    head=(160, 35), head_ang=-30, jaw=30, mouth_glow=(STORM[3], STORM[5]),
    legs=[dict(hip=(94, 126), knee=(1, -0.3), ankle=(90, 144), foot=(98, 148), bias=-1.4, sz=0.95),
          dict(hip=(100, 128), knee=(1, -0.3), ankle=(104, 144), foot=(112, 148), bias=0.0, sz=1.0)],
    arms=[dict(shoulder=(122, 88), elbow=(134, 100), wrist=(146, 88), hand=(150, 80), claw_dir=(0.4, -0.9), bias=-1.4, sz=0.95),
          dict(shoulder=(117, 92), elbow=(126, 108), wrist=(140, 98), hand=(145, 90), claw_dir=(0.4, -0.9), bias=0.0)],
    wings=[dict(shoulder=(124, 80), elbow=(150, 66), wrist=(180, 46), thumb=(4, -3),
                tips=[(248, 30), (254, 64), (240, 94), (208, 110)], root=(126, 106), sag=[0.3, 0.32, 0.32, 0.35],
                bends=[-3, -3, -3, -2.5], notches=2, holes=[(1.5, 0.75, 2.4)], bias=-1.2, seed=4,
                hum_r=(4.0, 2.0), fore_r=(2.2, 1.4)),
           dict(shoulder=(114, 82), elbow=(88, 56), wrist=(70, 26), thumb=(-4, -4),
                tips=[(6, 4), (2, 40), (14, 76), (44, 100)], root=(104, 112), sag=[0.3, 0.32, 0.32, 0.35],
                bends=[3, 3, 3, 2.5], notches=2, holes=[(0.5, 0.72, 2.6), (2.4, 0.8, 2.0)], bias=0, seed=7,
                hum_r=(4.6, 2.2), fore_r=(2.5, 1.6))],
)

POSES["breath"] = dict(
    label="3  BREATH - neck lunges low, storm-fire ignites",
    ground=150,
    spine=[(4, 100, 0.5, 0.5), (8, 116, 1.0, 1.0), (18, 130, 1.7, 1.7), (36, 138, 2.7, 2.7), (56, 134, 4.3, 4.3),
           (72, 122, 7.5, 8.0), (90, 112, 10.5, 12.5), (110, 110, 11.5, 14.5), (128, 112, 10.0, 12.5),
           (141, 116, 6.6, 7.2), (152, 122, 5.1, 5.3), (163, 126, 4.4, 4.5), (174, 127, 3.9, 4.0), (184, 126, 3.7, 3.7),
           (190, 126, 3.5, 3.5)],
    plates=(95, 215), ridge=(40, 222), throat=3,
    head=(190, 126), head_ang=6, jaw=26, mouth_glow=(STORM[4], STORM[6]),
    legs=[dict(hip=(82, 118), knee=(1, 0.2), ankle=(74, 143), foot=(82, 147), bias=-1.4, sz=0.95),
          dict(hip=(88, 120), knee=(1, 0.2), ankle=(86, 145), foot=(95, 148), bias=0.0, sz=1.0)],
    arms=[dict(shoulder=(133, 116), elbow=(130, 132), wrist=(147, 141), hand=(154, 146), bias=-1.4, sz=0.95),
          dict(shoulder=(126, 118), elbow=(121, 134), wrist=(138, 142), hand=(145, 147), bias=0.0)],
    wings=[dict(shoulder=(124, 102), elbow=(134, 80), wrist=(148, 52), thumb=(4, -3),
                tips=[(174, 4), (200, 22), (206, 48), (186, 72)], root=(130, 108), sag=[0.3, 0.32, 0.32, 0.35],
                bends=[-3, -3, -3, -2.5], notches=2, holes=[(1.4, 0.8, 2.0)], bias=-1.2, seed=11,
                hum_r=(4.0, 2.0), fore_r=(2.2, 1.4)),
           dict(shoulder=(112, 104), elbow=(94, 84), wrist=(96, 48), thumb=(-3, -4),
                tips=[(44, 8), (26, 40), (32, 72), (56, 96)], root=(92, 114), sag=[0.3, 0.32, 0.32, 0.35],
                bends=[3, 3, 3, 2.5], notches=2, holes=[(2.3, 0.78, 2.2)], bias=0, seed=13,
                hum_r=(4.6, 2.2), fore_r=(2.5, 1.6))],
    fire=dict(ang=4, length=74),
)

POSES["air"] = dict(
    label="4  PHASE 2 - AIRBORNE, storm-lit",
    ground=None,
    spine=[(4, 70, 0.5, 0.5), (12, 86, 1.0, 1.0), (24, 100, 1.7, 1.7), (42, 108, 2.7, 2.7), (60, 106, 4.3, 4.3),
           (76, 98, 7.5, 8.0), (94, 92, 10.5, 12.5), (114, 91, 11.5, 14.0), (132, 93, 10.0, 12.0),
           (146, 90, 6.6, 7.2), (157, 82, 5.1, 5.3), (168, 76, 4.4, 4.5), (180, 75, 3.9, 4.0), (191, 79, 3.7, 3.7),
           (198, 84, 3.5, 3.5)],
    plates=(95, 205), ridge=(40, 212), throat=3,
    head=(198, 84), head_ang=16, jaw=14, mouth_glow=(STORM[3], STORM[5]),
    legs=[dict(hip=(80, 100), knee=(1, 0.6), ankle=(66, 118), foot=(56, 124), bias=-1.4, sz=0.95),
          dict(hip=(86, 102), knee=(1, 0.6), ankle=(74, 122), foot=(63, 128), bias=0.0, sz=1.0)],
    arms=[dict(shoulder=(131, 98), elbow=(128, 112), wrist=(143, 114), hand=(149, 118), claw_dir=(0.5, 0.85), bias=-1.4, sz=0.95),
          dict(shoulder=(126, 100), elbow=(120, 115), wrist=(135, 118), hand=(141, 123), claw_dir=(0.5, 0.85), bias=0.0)],
    wings=[dict(shoulder=(128, 84), elbow=(150, 54), wrist=(170, 24), thumb=(4, -3),
                tips=[(242, 2), (254, 26), (242, 50), (214, 64)], root=(132, 96), sag=[0.3, 0.32, 0.32, 0.35],
                bends=[-3, -3, -3, -2.5], notches=2, holes=[(1.5, 0.8, 2.4)], bias=-1.0, seed=21,
                hum_r=(4.0, 2.0), fore_r=(2.2, 1.4)),
           dict(shoulder=(120, 86), elbow=(98, 58), wrist=(82, 26), thumb=(-4, -4),
                tips=[(14, 2), (4, 36), (14, 70), (46, 92)], root=(98, 100), sag=[0.3, 0.32, 0.32, 0.35],
                bends=[3, 3, 3, 2.5], notches=2, holes=[(0.5, 0.75, 2.4), (2.5, 0.82, 2.0)], bias=0, seed=23,
                hum_r=(4.6, 2.2), fore_r=(2.5, 1.6))],
    phase=2, ridge_arcs=[52, 118, 176],
    bolts=[((14, 3), (2, 22), 1), ((242, 3), (254, 16), 1), ((226, 72), (238, 96), 0.8), ((58, 96), (40, 128), 1),
           ((126, 108), (116, 140), 0.8), ((176, 30), (196, 12), 0.8), ((6, 40), (1, 60), 0.8)],
)


# =========================================================================== render
def render_pose(P):
    C = Canvas()
    fxl = FX()
    phase = P.get("phase", 1)
    tb = body_tube(P)
    far_w, near_w = P["wings"][0], P["wings"][1]
    far_l, near_l = P["legs"][0], P["legs"][1]
    folded = P is POSES.get("idle")
    # ---- far side
    fi = wing(C, far_w, bias=far_w.get("bias", -1), phase=phase, far=True, seed=far_w.get("seed", 1))
    paint_veins(C, fxl, fi, phase, far=True)
    leg(C, far_l["hip"], far_l["knee"], far_l["ankle"], far_l["foot"], far_l["sz"], far_l["bias"])
    if P.get("arms"):
        arm(C, P["arms"][0], bias=P["arms"][0].get("bias", -1.4))
    # ---- body
    paint_ridge(C, P, tb)
    paint_body(C, P, tb)
    paint_tail_barbs(C, P, tb)
    leg(C, near_l["hip"], near_l["knee"], near_l["ankle"], near_l["foot"], near_l["sz"], near_l["bias"])
    if P.get("arms"):
        arm(C, P["arms"][1], bias=P["arms"][1].get("bias", 0))
    head(C, fxl, P)
    ni = wing(C, near_w, bias=near_w.get("bias", 0), phase=phase, far=False, seed=near_w.get("seed", 2))
    paint_veins(C, fxl, ni, phase)
    img = C.render()
    if P.get("fire"):
        f = P["fire"]
        hp = v2(P["head"]); a = P["head_ang"]
        U = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]); V = np.array([-U[1], U[0]])
        sc = P.get("head_sc", 1.15)
        mouth = hp + U * 16.0 * sc + V * 3.6 * sc
        fire(fxl, C, mouth, f["ang"], f["length"], w0=1.4, spread=0.27)
    if phase == 2:
        rng = np.random.RandomState(5)
        for s0 in P.get("ridge_arcs", []):
            p0, T0, N0, rd0, _ = tb.at(s0)
            p1, T1, N1, rd1, _ = tb.at(s0 + 14)
            a = p0 - N0 * (rd0 + 3.5); b = p1 - N1 * (rd1 + 3.0)
            px, _ = bolt(a, b, rng, amp=0.22, depth=4)
            fxl.put([q for q in px if not (0 <= q[0] < W and 0 <= q[1] < H and C.mat[q[1], q[0]] >= 0)], STORM[5])
        for a, b, br in P.get("bolts", []):
            lightning(fxl, a, b, rng, br)
    img.alpha_composite(fxl.image())
    return img


# =========================================================================== sheet
def knight():
    p = Image.open(os.path.join(ROOT, "assets", "player.png")).crop((0, 0, 64, 40)).convert("RGBA")
    w = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).crop((0, 0, 64, 40)).convert("RGBA")
    p.alpha_composite(w)
    return p.transpose(Image.FLIP_LEFT_RIGHT)


def backdrop(w, h, seed, ground, storm=False, halo=None):
    bg = np.zeros((h, w, 4), np.uint8)
    bg[...] = (*hexc("#0e1016"), 255)
    yy, xx = np.mgrid[0:h, 0:w]
    # layered storm banks: soft horizontal bands broken by slow waves
    for k, (col, base, amp, fq) in enumerate(((("#12151d"), 56, 9, 0.035), ("#161a24", 36, 7, 0.05), ("#1b2030", 18, 5, 0.07))):
        edge = base + amp * np.sin(xx * fq + seed * (k + 1)) + amp * 0.5 * np.sin(xx * fq * 2.7 + seed)
        sel = yy < edge
        bg[sel] = (*hexc(col), 255)
    if halo:
        # cold storm-light breaking through behind the silhouette (stepped, pixel-art bands)
        hx, hy, hr = halo
        d = np.hypot((xx - hx) / 1.25, yy - hy) + np.sin(xx * 0.21 + yy * 0.13) * 1.5
        for rr, col in ((hr, "#141925"), (hr * 0.72, "#18202e"), (hr * 0.48, "#1d2738"), (hr * 0.28, "#243048")):
            bg[d < rr] = (*hexc(col), 255)
    if storm:
        # storm-lit cloud undersides
        for k, (cx, cy, rx, ry) in enumerate(((36, 22, 46, 10), (142, 12, 60, 9), (226, 30, 40, 8))):
            d = np.hypot((xx - cx) / rx, (yy - cy) / ry)
            wob = 0.08 * np.sin(xx * 0.3 + k)
            bg[(d < 1.0 + wob)] = (*hexc("#1a2030"), 255)
            bg[(d < 1.0 + wob) & (d > 0.84 + wob) & (yy > cy)] = (*hexc("#26314a"), 255)
    if ground:
        g = ground
        bg[g + 1:, :] = (*hexc("#14151c"), 255)
        bg[g + 1, :] = (*hexc("#262833"), 255)
        stripe = (yy > g + 3) & (((xx + yy * 3) % 11) == 0)
        bg[stripe] = (*hexc("#181920"), 255)
    return Image.fromarray(bg).copy()


def shadow(img, cx, w, ground):
    px = img.load()
    for x in range(int(cx - w), int(cx + w)):
        t = abs(x - cx) / w
        if 0 <= x < img.width:
            px[x, ground + 1] = hexc("#0b0b10") + (255,)
            if t < 0.8:
                px[x, ground + 2] = hexc("#101117") + (255,)


def main():
    S = 2
    pad = 12
    lab_h = 16
    extra = 44
    panels = {}
    for k, P in POSES.items():
        im = render_pose(P)
        im.save(os.path.join(HERE, "cindervane_%s.png" % k))
        wid = W + (extra if k == "idle" else 0)
        bg = backdrop(wid, H, 3 + len(k), P["ground"], storm=(k == "air"), halo=P.get("halo"))
        if P["ground"]:
            shadow(bg, P.get("shadow_x", 110), 70, P["ground"])
        bg.alpha_composite(im)
        if k == "idle":
            kn = knight()
            bg.alpha_composite(kn, (W - 22, P["ground"] + 1 - 40))
        panels[k] = bg
    colw = [max(panels["idle"].width, panels["breath"].width), max(panels["roar"].width, panels["air"].width)]
    title_h = 30
    SW = pad * 3 + (colw[0] + colw[1]) * S
    SH = title_h + pad * 2 + 2 * (H * S + lab_h) + pad
    sheet = Image.new("RGBA", (SW, SH), (10, 11, 16, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f1 = ImageFont.load_default(size=16)
        f2 = ImageFont.load_default(size=11)
    except TypeError:
        f1 = f2 = ImageFont.load_default()
    d.text((pad, 8), "CINDERVANE, THE LAST DRAKE  -  concept v2  (256x160 frames, shown 2x)", fill=(205, 216, 236), font=f1)
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
    # review closeups (4x): idle head, roar head, breath fire, phase-2 wing
    crops = [("idle", (150, 62, 234, 118)), ("roar", (118, 8, 202, 64)), ("breath", (170, 100, 254, 156)),
             ("air", (150, 0, 234, 56))]
    cs = 4
    cw = sum((b[2] - b[0]) * cs + pad for _, b in crops) + pad
    close = Image.new("RGBA", (cw, 56 * cs + pad * 2), (10, 11, 16, 255))
    x = pad
    for k, b in crops:
        c = panels[k].crop(b)
        close.alpha_composite(c.resize((c.width * cs, c.height * cs), Image.NEAREST), (x, pad))
        x += c.width * cs + pad
    close.convert("RGB").save(os.path.join(HERE, "cindervane_closeup.png"))
    print("wrote", os.path.join(HERE, "cindervane.png"), sheet.size)


if __name__ == "__main__":
    main()
