#!/usr/bin/env python3
"""CONCEPT v3 -- "The Molten Colossus": a fallen forge-god of obsidian and magma (Ashwright's titan).

    python3 art/concepts/gen_colossus.py        -> art/concepts/colossus.png (sheet @2x), colossus_1x.png

Method (same family as gen_boss / gen_vessel, pushed to a sculpted 2.5D height field):
every body part is a GROUP of primitives (ellipsoid muscles, tapered capsules, bevelled plates) that
are blended with a smooth-max into ONE height field -> the normals give soft sculpted forms with crisp
creases where muscles meet.  Creases are where the molten veins run (so the glow follows the anatomy).
Obsidian gets a Voronoi facet perturbation (conchoidal chips) + sparse glassy glints; key light is a dim
cool top-right, the rim / bounce light is the forge heat (veins, heart, eyes, magma).  Groups are drawn
back-to-front with contact lines, then a 1px outline and the hot rim.  Damage states: every group has a
`shell` value (1 = intact obsidian, 0 = molten body showing) and extra break masks (see crack_shell).
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

W, H = 224, 176
GROUND = 175
YY, XX = np.mgrid[0:H, 0:W]
XC, YC = XX + 0.5, YY + 0.5
NEG = -1e6

# =========================================================================== palette
HEX = {
    "OUT": "#060304",
    # obsidian / basalt: violet-black -> cool ash grey, glassy glint
    "O0": "#0a070a", "O1": "#130e13", "O2": "#1d161c", "O3": "#2a2127", "O4": "#3b2f33", "O5": "#554747",
    "O6": "#7a6a66", "OS": "#b7b3c2",
    # heat-lit obsidian (bounce from magma)
    "H0": "#1c0909", "H1": "#300f0b", "H2": "#4b170d", "H3": "#70220e", "H4": "#9c3410",
    # molten: blood red -> orange -> white-hot
    "M0": "#3a0906", "M1": "#661107", "M2": "#9c1f09", "M3": "#cf3b0c", "M4": "#f26414", "M5": "#ff9a2e",
    "M6": "#ffcf66", "M7": "#fff3cc",
    # blackened iron
    "I0": "#0b0809", "I1": "#161112", "I2": "#221a19", "I3": "#342824", "I4": "#4f3d32", "I5": "#7a634c",
    # Ashwright gold
    "G0": "#2b1a0e", "G1": "#4f3314", "G2": "#7d5519", "G3": "#b2822a", "G4": "#dfb24a", "G5": "#fbe7a0",
    # scorched cloth (deep red)
    "C0": "#16060a", "C1": "#2a0a10", "C2": "#431016", "C3": "#62181a", "C4": "#86261f",
    # ash / smoke
    "A0": "#1d1716", "A1": "#2c2422", "A2": "#3e3430", "A3": "#574a43", "A4": "#7a6a60",
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in HEX.items()}
RAMPS = {
    "O": ["O0", "O1", "O2", "O3", "O4", "O5", "O6"],
    "H": ["H0", "H1", "H2", "H3", "H4"],
    "M": ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"],
    "I": ["I0", "I1", "I2", "I3", "I4", "I5"],
    "G": ["G0", "G1", "G2", "G3", "G4", "G5"],
    "C": ["C0", "C1", "C2", "C3", "C4"],
}
MATS = ["", "O", "I", "G", "M", "C"]
MI = {m: i for i, m in enumerate(MATS)}
LIGHT = np.array([0.42, -0.72, 0.55]); LIGHT = LIGHT / np.linalg.norm(LIGHT)


def hsh(x, y, k=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def hash_arr(ix, iy, k=0):
    h = (np.asarray(ix).astype(np.int64) * 374761393 + np.asarray(iy).astype(np.int64) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(sc, seed):
    """Smooth value noise over the frame, 0..1."""
    gx, gy = XC / sc, YC / sc
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - ix, gy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = hash_arr(ix, iy, seed); b = hash_arr(ix + 1, iy, seed)
    c = hash_arr(ix, iy + 1, seed); d = hash_arr(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def voronoi(cell, seed):
    """-> (cell id hash, edge closeness d2-d1, cell tilt x, cell tilt y)."""
    gx, gy = XC / cell, YC / cell
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    d1 = np.full(gx.shape, 9.0); d2 = np.full(gx.shape, 9.0)
    cid = np.zeros(gx.shape)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = ix + ox, iy + oy
            sx = cx + 0.15 + 0.7 * hash_arr(cx, cy, seed)
            sy = cy + 0.15 + 0.7 * hash_arr(cx, cy, seed + 7)
            d = np.hypot(gx - sx, gy - sy)
            nid = hash_arr(cx, cy, seed + 13)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            cid = np.where(closer, nid, cid)
            d1 = np.where(closer, d, d1)
    tx = (hash_arr((cid * 9973).astype(int), 1, seed) - 0.5)
    ty = (hash_arr((cid * 9973).astype(int), 2, seed) - 0.5)
    return cid, (d2 - d1) * cell, tx, ty


VOR = voronoi(6.5, 11)
VOR_FINE = voronoi(3.6, 23)
VOR_SHELL = voronoi(8.5, 41)
VOR_PLATE = voronoi(12.0, 57)
NOISE_A = vnoise(5.0, 3)
NOISE_B = vnoise(9.0, 5)
NOISE_C = vnoise(2.5, 9)


# =========================================================================== geometry
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def mul(a, k): return (a[0] * k, a[1] * k)


def rot(p, c, ang):
    s, co = math.sin(ang), math.cos(ang)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * co - dy * s, c[1] + dx * s + dy * co)


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def ik(s, h, l1, l2, pref):
    dx, dy = h[0] - s[0], h[1] - s[1]
    d = math.hypot(dx, dy) or 1e-6
    if d >= l1 + l2 - 0.01:
        return lerp(s, h, l1 / (l1 + l2))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    mx, my = s[0] + ux * a, s[1] + uy * a
    c1 = (mx - uy * hh, my + ux * hh); c2 = (mx + uy * hh, my - ux * hh)
    sc = lambda c: (c[0] - mx) * pref[0] + (c[1] - my) * pref[1]
    return c1 if sc(c1) >= sc(c2) else c2


def line_px(a, b):
    x0, y0 = int(round(a[0])), int(round(a[1])); x1, y1 = int(round(b[0])), int(round(b[1]))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts


def poly_px(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        seg = line_px(a, b)
        out += seg if not out else seg[1:]
    return out


def mask_poly(pts):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon([(x, y) for x, y in pts], fill=1)
    return np.array(im, dtype=bool)


def shift(a, dx, dy, fill):
    """out[y,x] = a[y-dy, x-dx]"""
    out = np.full_like(a, fill)
    ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
    xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def dist_in(mask, maxd=12):
    """approx distance (px) from each inside pixel to the outside."""
    d = np.where(mask, maxd, 0).astype(float)
    for _ in range(maxd):
        m = d.copy()
        for dx, dy, w in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.4), (-1, 1, 1.4), (1, -1, 1.4), (-1, -1, 1.4)):
            m = np.minimum(m, shift(d, dx, dy, 0) + w)
        d = np.where(mask, np.minimum(d, m), 0)
    return d


def dilate(mask, r=1):
    out = mask.copy()
    for _ in range(r):
        o = out.copy()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            o |= shift(out, dx, dy, False)
        out = o
    return out


# =========================================================================== primitives -> height fields
def P_ell(c, rx, ry, ang=0.0, z=0.0, hs=1.0):
    dx, dy = XC - c[0], YC - c[1]
    s, co = math.sin(ang), math.cos(ang)
    u = dx * co + dy * s; v = -dx * s + dy * co
    e = (u / rx) ** 2 + (v / ry) ** 2
    return np.where(e <= 1, z + hs * min(rx, ry) * np.sqrt(np.clip(1 - e, 0, 1)), NEG)


def P_cap(a, b, r0, r1=None, z=0.0, hs=1.0):
    r1 = r0 if r1 is None else r1
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy or 1e-6
    t = np.clip(((XC - a[0]) * dx + (YC - a[1]) * dy) / L2, 0, 1)
    qx, qy = a[0] + dx * t, a[1] + dy * t
    r = r0 + (r1 - r0) * t
    d2 = (XC - qx) ** 2 + (YC - qy) ** 2
    return np.where(d2 <= r * r, z + hs * np.sqrt(np.clip(r * r - d2, 0, None)), NEG)


def P_tube(pts, r0, r1, z=0.0, hs=1.0):
    """tapered tube along a polyline (union of capsules)."""
    out = np.full((H, W), NEG)
    n = len(pts) - 1
    for i in range(n):
        ra = r0 + (r1 - r0) * i / n; rb = r0 + (r1 - r0) * (i + 1) / n
        out = np.maximum(out, P_cap(pts[i], pts[i + 1], ra, rb, z, hs))
    return out


def P_poly(pts, z=0.0, bevel=4.0, hs=1.0, tilt=(0.0, 0.0), mask=None):
    m = mask_poly(pts) if mask is None else mask
    d = dist_in(m, int(bevel) + 2)
    t = np.clip(d / bevel, 0, 1)
    h = z + hs * bevel * np.sqrt(1 - (1 - t) ** 2) + tilt[0] * (XC - XC[m].mean() if m.any() else 0) \
        + tilt[1] * (YC - YC[m].mean() if m.any() else 0)
    return np.where(m, h, NEG)


class Prim:
    def __init__(self, h, mat="O", tag="", vein=0.0, facet=1.0, bias=0):
        self.h, self.mat, self.tag, self.vein, self.facet, self.bias = h, mat, tag, vein, facet, bias


class Group:
    """A body part: primitives blended into one sculpted height field."""
    def __init__(self, name, k=1.6, shell=1.0):
        self.name, self.k, self.shell = name, k, shell
        self.prims = []
        self.decals = []     # callables(fb, vis) run after the group is composited
        self.clip = None

    def add(self, h, mat="O", tag="", vein=0.0, facet=1.0, bias=0):
        self.prims.append(Prim(h, mat, tag, vein, facet, bias))
        return self

    def decal(self, fn):
        self.decals.append(fn)

    def resolve(self):
        hs = np.stack([p.h for p in self.prims])
        own = np.argmax(hs, axis=0)
        hmax = np.max(hs, axis=0)
        mask = hmax > NEG / 2
        if self.clip is not None:
            mask &= self.clip
        # smooth max (polynomial), accumulated
        acc = hs[0].copy()
        k = self.k
        for h in hs[1:]:
            both = (acc > NEG / 2) & (h > NEG / 2)
            d = np.abs(acc - h)
            sm = np.maximum(acc, h) + np.where(both & (d < k), (k - d) ** 2 / (4 * k), 0)
            acc = np.where(both, sm, np.maximum(acc, h))
        acc = np.where(mask, acc, NEG)
        # v3: bevelled obsidian plates -- big conchoidal slabs with a soft sunken seam (read as clusters)
        fac = np.array([p.facet for p in self.prims])[own]
        _, pe, _, _ = VOR_PLATE
        patch = np.clip((NOISE_B - 0.42) * 4.0, 0, 1)       # plates cluster in patches, smooth muscle between
        bump = (np.clip(pe / 2.2, 0, 1) - 1) * 0.75 * np.clip(fac, 0, 1) * patch
        acc = np.where(mask, acc + bump, NEG)
        # normals: central differences, steep drop outside
        drop = 2.2
        def nb(dx, dy):
            s = shift(acc, dx, dy, NEG)
            return np.where(s > NEG / 2, s, acc - drop)
        gx = (nb(-1, 0) - nb(1, 0)) * 0.5
        gy = (nb(0, -1) - nb(0, 1)) * 0.5
        nx, ny, nz = -gx, -gy, np.ones_like(gx)
        l = np.sqrt(nx * nx + ny * ny + nz * nz)
        self.mask, self.hf, self.own = mask, acc, own
        self.nx, self.ny, self.nz = nx / l, ny / l, nz / l
        return self


# =========================================================================== frame buffer
class FB:
    def __init__(self):
        self.gid = np.full((H, W), -1)
        self.mat = np.zeros((H, W), int)
        self.nx = np.zeros((H, W)); self.ny = np.zeros((H, W)); self.nz = np.ones((H, W))
        self.bias = np.zeros((H, W))
        self.heat = np.zeros((H, W))          # emissive level 0..1 for mat M
        self.fix = np.full((H, W), "", dtype=object)
        self.facet = np.zeros((H, W))
        self.crease = np.zeros((H, W), bool)
        self.groups = []
        self.contact = np.zeros((H, W), bool)
        self.bnx = np.zeros((H, W)); self.bny = np.zeros((H, W)); self.bnz = np.ones((H, W))

    def put(self, g):
        g.resolve()
        gi = len(self.groups)
        self.groups.append(g)
        m = g.mask
        # contact line + AO on what is behind
        behind = self.gid >= 0
        ring = dilate(m, 1) & ~m & behind
        self.contact |= ring
        ao = dilate(m, 3) & ~dilate(m, 1) & behind
        self.bias[ao] -= 0.6
        self.contact[m] = False
        self.gid[m] = gi
        mats = np.array([MI[p.mat] for p in g.prims])
        self.mat[m] = mats[g.own[m]]
        fac = np.array([p.facet for p in g.prims])
        self.facet[m] = fac[g.own[m]]
        pb = np.array([p.bias for p in g.prims])
        self.bias[m] = pb[g.own[m]]
        self.nx[m], self.ny[m], self.nz[m] = g.nx[m], g.ny[m], g.nz[m]
        # v3: big-form normal of the whole part (its silhouette as one pillowed volume) -> clear planes
        d = dist_in(g.mask, 10)
        hb = 10 * np.sqrt(np.clip(1 - (1 - d / 10) ** 2, 0, 1))
        hb = np.where(g.mask, hb, 0)
        bx = (shift(hb, 1, 0, 0) - shift(hb, -1, 0, 0)) * 0.5
        by = (shift(hb, 0, 1, 0) - shift(hb, 0, -1, 0)) * 0.5
        bl_ = np.sqrt(bx * bx + by * by + 1)
        self.bnx[m], self.bny[m], self.bnz[m] = (bx / bl_)[m], (by / bl_)[m], (1 / bl_)[m]
        self.heat[m] = 0
        self.fix[m] = ""
        self.crease[m] = False
        # creases between primitives (anatomy lines) + veins along chosen ones
        own = np.where(m, g.own, -1)
        cr = np.zeros((H, W), bool)
        vh = np.zeros((H, W))
        veins = np.array([p.vein for p in g.prims])
        for dx, dy in ((1, 0), (0, 1)):
            o2 = shift(own, -dx, -dy, -1)
            edge = m & (o2 >= 0) & (o2 != own)
            cr |= edge
            v = np.minimum(veins[np.clip(own, 0, None)], veins[np.clip(o2, 0, None)])
            vh = np.maximum(vh, np.where(edge, v, 0))
        self.crease |= cr
        gvis = m.copy()
        if g.shell < 1.0:
            self.crack_shell(g, m)
        # veins: broken by noise so they read as cracks in cooling rock, hotter where the rock is thin
        nz_ = 0.7 * NOISE_B + 0.3 * NOISE_A          # v3: low-frequency gate -> long continuous runs
        heat = vh * np.clip((nz_ - 0.44) * 3.2, 0, 1)
        vm = cr & (heat > 0.24)
        self.mat[vm] = MI["M"]
        self.heat[vm] = np.clip(0.25 + heat[vm] * 0.75, 0, 1)
        for fn in g.decals:
            fn(self, gvis)
        return gvis

    def crack_shell(self, g, m):
        """Damage state (v3): the obsidian shell bursts off the BELLIES of the muscles, so the breaks follow
        the anatomy -- each exposed muscle keeps a rim of shell (a lip lit hot from inside), the molten flesh
        grades from a dark cooling edge to a white-hot centre with floating crust islands, and every
        anatomical crease between the plates becomes a glowing seam."""
        amt = 1.0 - g.shell
        BURST = {"pecN": 1.0, "pecF": 0.9, "abs": 0.55, "obl": 0.7, "lat": 0.8, "trap": 0.5, "bic": 1.0,
                 "brach": 1.0, "delt": 0.75, "quad": 1.0, "calf": 0.9, "tri": 0.5, "flex": 0.6, "knee": 0.4}
        gone = np.zeros((H, W), bool)
        heat = np.zeros((H, W))
        lipsrc = np.zeros((H, W), bool)
        for i, pr in enumerate(g.prims):
            w = BURST.get(pr.tag, 0.0)
            if w <= 0 or hsh(i, len(g.name), 17) > w * (0.12 + amt * 0.85):
                continue
            pm = m & (g.own == i) & (self.mat == MI["O"])
            if pm.sum() < 20:
                continue
            d = dist_in(pm, 7)
            rag = (NOISE_C - 0.5) * 2.2 + (NOISE_A - 0.5) * 1.2
            inner = pm & (d > 2.4 + rag)
            if getattr(g, "keep", None) is not None:
                inner &= ~g.keep
            gone |= inner
            heat = np.maximum(heat, np.where(inner, d, 0))
            lipsrc |= pm
        di = dist_in(gone, 6)
        crust = (VOR_FINE[1] > 0.8) & (hash_arr((VOR_FINE[0] * 7919).astype(int), 3, 2) > 0.5) & (di > 1.6)
        hv = np.clip(0.28 + di * 0.1 + (NOISE_A - 0.5) * 0.16, 0.28, 0.8)
        hv = np.where(di > 3.2, np.maximum(hv, 0.78), hv)
        self.mat[gone] = MI["M"]
        self.heat[gone] = hv[gone]
        ci = gone & crust
        self.heat[ci] = 0.2                        # cooling crust floating on the magma
        cr_rim = gone & ~crust & dilate(ci, 1)
        self.heat[cr_rim] = np.maximum(self.heat[cr_rim], 0.62)
        # anatomical creases crack open as glowing seams (the breaks follow the body)
        own = np.where(m, g.own, -1)
        seam = np.zeros((H, W), bool)
        for dx, dy in ((1, 0), (0, 1)):
            o2 = shift(own, -dx, -dy, -1)
            seam |= m & (o2 >= 0) & (o2 != own)
        HANDS = ("knk", "fing", "thumb", "fist", "wrist", "claw", "cuff", "foot", "toe", "face", "cran")
        hand_i = [i for i, pr in enumerate(g.prims) if pr.tag.startswith(HANDS)]
        seam &= ~np.isin(own, hand_i) & ~np.isin(shift(own, -1, 0, -1), hand_i) & ~np.isin(shift(own, 0, -1, -1), hand_i)
        seam &= ~gone & ~dilate(gone, 2) & (self.mat == MI["O"]) & (NOISE_B > 0.42)
        self.mat[seam] = MI["M"]
        self.heat[seam] = np.clip(0.42 + amt * 0.2 + (NOISE_C[seam] - 0.5) * 0.3, 0, 1)
        # raised lip of the broken shell, lit hot from the magma inside
        lip = dilate(gone, 1) & ~gone & m & (self.mat == MI["O"])
        self.fix[lip] = np.where(NOISE_C[lip] > 0.55, "H4", "H3")

    # --- decal helpers (restricted to a visibility mask) ---
    def molten(self, pts, heat, vis, width=1):
        for (x, y) in pts:
            if 0 <= x < W and 0 <= y < H and vis[y, x]:
                self.mat[y, x] = MI["M"]
                self.heat[y, x] = max(self.heat[y, x] if self.mat[y, x] == MI["M"] else 0, heat)

    def paint(self, pts, key, vis=None):
        for (x, y) in pts:
            if 0 <= x < W and 0 <= y < H and (vis is None or vis[y, x]):
                self.fix[y, x] = key

    def lvl(self, pts, d, vis=None):
        for (x, y) in pts:
            if 0 <= x < W and 0 <= y < H and (vis is None or vis[y, x]):
                self.bias[y, x] += d


def smooth(pts, n=6, wob=0.0, seed=0):
    """Catmull-Rom through pts, with an organic sideways wobble."""
    if len(pts) < 3:
        pts = [pts[0], lerp(pts[0], pts[-1], 0.5), pts[-1]]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    if wob:
        res = []
        for i, q in enumerate(out):
            a_ = out[max(0, i - 1)]; b_ = out[min(len(out) - 1, i + 1)]
            u = unit(a_, b_) if a_ != b_ else (1, 0)
            w = wob * math.sin(i * 0.55 + seed * 1.7) * math.sin(math.pi * i / max(1, len(out) - 1))
            res.append((q[0] - u[1] * w, q[1] + u[0] * w))
        out = res
    return out


def vein_path(fb, vis, pts, h0, h1, branch=0, seed=1, width=1, wob=1.8):
    """hand-drawn molten vein along a smooth curve; heat h0->h1; optional side branches."""
    pts = smooth(pts, 6, wob, seed)
    px = poly_px(pts)
    n = max(1, len(px) - 1)
    rnd = random.Random(seed)
    for i, (x, y) in enumerate(px):
        t = i / n
        h = h0 + (h1 - h0) * t
        h *= 0.75 + 0.25 * math.sin(i * 0.9 + seed)
        if not (0 <= x < W and 0 <= y < H) or not vis[y, x]:
            continue
        fb.mat[y, x] = MI["M"]; fb.heat[y, x] = max(fb.heat[y, x], h)
        if width > 1 and h > 0.55:
            for (a, b) in ((1, 0), (0, 1)):
                q = (x + a, y + b)
                if 0 <= q[0] < W and 0 <= q[1] < H and vis[q[1], q[0]] and fb.mat[q[1], q[0]] != MI["M"]:
                    fb.mat[q[1], q[0]] = MI["M"]; fb.heat[q[1], q[0]] = h * 0.55
    # v3: forked tributaries -- curved, tapering, leaving the trunk in the flow direction
    for bi in range(branch):
        i = int(len(pts) * (0.25 + 0.55 * (bi + rnd.random() * 0.6) / max(1, branch)))
        i = max(1, min(len(pts) - 2, i))
        q0 = pts[i]
        u = unit(pts[i - 1], pts[i + 1])
        sd = 1 if (bi + seed) % 2 == 0 else -1
        ang = math.atan2(u[1], u[0]) + sd * rnd.uniform(0.45, 0.85)
        ln = rnd.uniform(5, 10)
        c1 = (q0[0] + math.cos(ang) * ln * 0.5, q0[1] + math.sin(ang) * ln * 0.5)
        ang2 = ang - sd * 0.35
        q1 = (c1[0] + math.cos(ang2) * ln * 0.5, c1[1] + math.sin(ang2) * ln * 0.5)
        bp = poly_px(smooth([q0, c1, q1], 4))
        hb = (h0 + (h1 - h0) * i / max(1, len(pts) - 1)) * 0.75
        nb = max(1, len(bp) - 1)
        for j, (a_, c_) in enumerate(bp):
            hv = hb * (1 - 0.7 * j / nb)
            if 0 <= a_ < W and 0 <= c_ < H and vis[c_, a_] and hv > 0.12:
                if fb.mat[c_, a_] != MI["M"]:
                    fb.mat[c_, a_] = MI["M"]; fb.heat[c_, a_] = hv
                else:
                    fb.heat[c_, a_] = max(fb.heat[c_, a_], hv)


# =========================================================================== shading
def shade(fb, glow=1.0, under=0.35):
    fig = fb.gid >= 0
    out = np.full((H, W), "", dtype=object)
    mat = fb.mat
    # v3: gentle per-plate tilt only (the plates themselves live in the height field) -> clean clusters
    _, _, tx, ty = VOR_PLATE
    k = fb.facet
    nx = fb.nx + k * tx * 0.16
    ny = fb.ny + k * ty * 0.16
    nz = fb.nz
    l = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / l, ny / l, nz / l
    ndl = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    bdl = fb.bnx * LIGHT[0] + fb.bny * LIGHT[1] + fb.bnz * LIGHT[2]
    v = np.clip(ndl * 0.62 + bdl * 0.5 - 0.06, 0, 1)
    rz = 2 * ndl * nz - LIGHT[2]
    # emissive heat field (bounce light from veins / magma), spread with falloff
    em = np.where(mat == MI["M"], fb.heat, 0.0) * glow
    field = em.copy()
    for r, fo in ((1, 0.8), (2, 0.55), (3, 0.36), (4, 0.22), (5, 0.12)):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                field = np.maximum(field, shift(em, dx, dy, 0) * fo)
    warm = field + under * np.clip(fb.ny, 0, 1) ** 1.5
    bias = fb.bias - np.where(fb.crease, 1.0, 0)
    for y in range(H):
        for x in range(W):
            if not fig[y, x]:
                continue
            if fb.fix[y, x]:
                out[y, x] = fb.fix[y, x]
                continue
            m = MATS[mat[y, x]]
            b = bias[y, x]
            if m == "M":
                i = int(round(fb.heat[y, x] * 7))
                out[y, x] = "M%d" % max(0, min(7, i))
                continue
            vv = v[y, x]
            if m == "O":
                f = 0.2 + vv ** 1.9 * 7.0 + b
                i = int(max(0, min(6, f)))
                if rz[y, x] > 0.93 and b > -0.5 and fb.facet[y, x] > 0.5 and warm[y, x] < 0.3:
                    out[y, x] = "OS" if rz[y, x] > 0.975 else "O6"      # glassy sheen on the crowns of forms
                    continue
                w = warm[y, x]
                if w > 0.26:
                    hi = int(max(0, min(4, w * 3.6 + (i - 2) * 0.45 - 0.5)))
                    out[y, x] = "H%d" % hi
                else:
                    out[y, x] = "O%d" % i
            elif m == "I":
                f = 0.3 + vv * 4.5 + b
                i = int(max(0, min(5, f)))
                if rz[y, x] > 0.95 and b >= 0:
                    i = 5
                w = warm[y, x]
                if w > 0.35 and i < 3:
                    out[y, x] = "H%d" % int(max(0, min(3, w * 3.2 - 0.4)))
                else:
                    out[y, x] = "I%d" % i
            elif m == "G":
                f = 0.9 + vv * 4.4 + b
                out[y, x] = "G%d" % int(max(0, min(5, f)))
            elif m == "C":
                f = 0.2 + vv * 3.4 + b
                i = int(max(0, min(4, f)))
                out[y, x] = "C%d" % i
    # contact lines between overlapping parts
    cl = fb.contact & fig & (mat != MI["M"]) & (fb.fix == "")
    out[cl] = "O0"
    # hot rim light: silhouette pixels facing back / down (the forge behind and the magma below)
    ext = np.zeros((H, W), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ext |= ~shift(fig, dx, dy, False)
    ext &= fig
    rim = ext & (mat == MI["O"]) & (((fb.nx < -0.55) & (fb.ny < 0.15) & (YY < 118)) | ((fb.ny > 0.6) & (YY > 160)))
    rim &= (fb.fix == "")
    rn = 0.6 * NOISE_A + 0.4 * NOISE_B
    for y, x in zip(*np.nonzero(rim)):
        w = warm[y, x] + (rn[y, x] - 0.5) * 0.6
        if rn[y, x] < 0.33 and w < 0.4:
            continue
        out[y, x] = "M3" if w > 0.6 else "M2" if w > 0.3 else "H4" if w > 0.05 else "H3"
    return out, fig, warm


def to_image(out, fig):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pix = img.load()
    # outline
    ol = np.zeros((H, W), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ol |= shift(fig, dx, dy, False)
    ol &= ~fig
    for y, x in zip(*np.nonzero(ol)):
        pix[x, y] = RGB["OUT"] + (255,)
    for y, x in zip(*np.nonzero(fig)):
        pix[x, y] = RGB[out[y, x]] + (255,)
    return img


# =========================================================================== anatomy
# Torso is sculpted in TORSO SPACE (designed around pelvis PV) and posed by a lean about the pelvis.
PV = (104.0, 112.0)


def unit(a, b):
    d = (b[0] - a[0], b[1] - a[1]); l = math.hypot(*d) or 1
    return (d[0] / l, d[1] / l)


def perp(u):
    return (-u[1], u[0])


def torso_group(p):
    """V-shaped titan torso: trapezius hump, pecs, abs, lats.  Returns group + key points."""
    T = p["T"]                                   # torso-space -> frame
    g = Group("torso", k=1.4)
    g.add(P_poly([T(q) for q in [(84, 114), (79, 101), (68, 88), (55, 74), (54, 60), (66, 48), (86, 38), (104, 34),
                                 (122, 37), (142, 45), (157, 54), (161, 66), (152, 82), (137, 98), (127, 114)]],
                 z=0, bevel=13, hs=0.85), tag="core")
    g.add(P_ell(T((100, 45)), 32, 13, -0.12 + p["lean"], z=7, hs=0.8), tag="trap", vein=0.4)
    g.add(P_ell(T((80, 56)), 22, 16, 0.5 + p["lean"], z=5, hs=0.8), tag="backhump", vein=0.2)
    g.add(P_ell(T((95, 69)), 19, 11.5, 0.2 + p["lean"], z=10), tag="pecN", vein=0.85)
    g.add(P_ell(T((128, 71)), 14, 10.5, -0.28 + p["lean"], z=9), tag="pecF", vein=0.85)
    for j, yy in enumerate((85, 94, 103)):      # v3: flat bevelled blocks (a carved six-pack, not grapes)
        wN, wF = 6.2 - j * 0.3, 5.0 - j * 0.3
        g.add(P_poly([T(q) for q in [(109.5 - wN * 2, yy - 4), (109.5, yy - 4.2), (109.5, yy + 3.8), (109.5 - wN * 2 + 0.8, yy + 3.8)]],
                     z=9.5 - j * 0.5, bevel=2.6, hs=1.2), tag="abs", vein=0.45)
        g.add(P_poly([T(q) for q in [(110.5, yy - 4.2), (110.5 + wF * 2, yy - 4.4), (110.5 + wF * 2 - 0.8, yy + 3.6), (110.5, yy + 3.8)]],
                     z=9 - j * 0.5, bevel=2.6, hs=1.2), tag="abs", vein=0.45)
    g.add(P_ell(T((87, 98)), 7, 12.5, 0.3 + p["lean"], z=6.5), tag="obl", vein=0.2)
    g.add(P_ell(T((129, 94)), 5.5, 11, -0.3 + p["lean"], z=5.5), tag="obl", vein=0.2)
    for q in ((77, 81), (79, 87), (82, 93)):
        g.add(P_ell(T(q), 4.2, 2.4, 0.5 + p["lean"], z=8), tag="serr", vein=0.15)
    g.add(P_ell(T((68, 80)), 10, 17, 0.35 + p["lean"], z=5), tag="lat", vein=0.25)
    # belt of blackened iron with the maker's mark
    g.add(P_cap(T((84, 110)), T((126, 108)), 3.2, 3.2, z=11, hs=0.7), mat="I", tag="belt", facet=0)
    heart = T((113.5, 72))
    def dec(fb, vis):
        # chest fissure: the molten heart seen through a ragged split of the sternum
        op = p.get("fissure", 0.0)
        pts = [T(q) for q in [(114, 58), (113, 63), (115, 67), (112.5, 72), (115, 77), (112, 82), (113, 87)]]
        vein_path(fb, vis, pts, 0.75, 0.55, branch=4, seed=3, width=2)
        if op > 0:
            _open_heart(fb, vis, heart, op, T)
        else:
            core = [(int(heart[0]) + a, int(heart[1]) + b) for a, b in ((0, 0), (0, -1), (-1, 0), (0, 1), (1, 1))]
            for (x, y) in core:
                if vis[y, x]:
                    fb.mat[y, x] = MI["M"]; fb.heat[y, x] = 1.0
            for (x, y) in [(int(heart[0]) + a, int(heart[1]) + b) for a in (-2, -1, 1, 2) for b in (-2, -1, 0, 1, 2)]:
                if vis[y, x] and fb.mat[y, x] != MI["M"] and abs(x - heart[0]) + abs(y - heart[1]) < 3.2:
                    fb.mat[y, x] = MI["M"]; fb.heat[y, x] = 0.6
        # veins that radiate from the heart over the pecs (follow the fibre direction)
        vein_path(fb, vis, [heart, T((104, 66)), T((92, 63)), T((84, 64))], 0.7, 0.2, branch=2, seed=5)
        vein_path(fb, vis, [heart, T((122, 69)), T((131, 67))], 0.6, 0.25, branch=1, seed=6)
        vein_path(fb, vis, [T((110, 90)), T((109, 99)), T((110, 108))], 0.45, 0.2, seed=7)
    g.decal(dec)
    return g, heart


def _open_heart(fb, vis, c, op, T):
    """Torn-open chest (v3): a ragged wound held by snapped obsidian ribs; the forge-heart inside is banded
    white-hot -> orange -> blood red with dark vessels across it, the torn shell lit hot around the rim."""
    rx, ry = 3 + 6.5 * op, 7 + 8 * op
    ribs = [c[1] - ry * 0.52, c[1] + ry * 0.02, c[1] + ry * 0.5] if op > 0.6 else []
    for y in range(int(c[1] - ry - 3), int(c[1] + ry + 4)):
        for x in range(int(c[0] - rx - 4), int(c[0] + rx + 5)):
            if not (0 <= x < W and 0 <= y < H and vis[y, x]):
                continue
            ey = (y + .5 - c[1]) / ry
            wx = rx * (1 - ey * ey * 0.3)
            ex = (x + .5 - c[0]) / (wx + 0.01)
            jag = 0.16 * math.sin((y + .5) * 1.3 + (1 if ex > 0 else 2.5)) + 0.08 * math.sin((y + .5) * 2.7)
            e = (abs(ex) * (1 + jag)) ** 2 + ey ** 2
            if e < 1.0:
                d = math.sqrt(e)
                k = 1.0 if d < 0.3 else 0.86 if d < 0.5 else 0.72 if d < 0.68 else 0.57 if d < 0.84 else 0.42
                # dark vessels arcing over the heart
                v1 = abs((x + .5 - c[0]) - 2.2 * math.sin((y + .5 - c[1]) * 0.35) - rx * 0.28)
                v2 = abs((y + .5 - c[1]) + 0.35 * (x + .5 - c[0]) - ry * 0.18)
                if 0.3 < d < 0.8 and (v1 < 0.55 or v2 < 0.5):
                    k = max(0.42, k - 0.3)
                rib = None
                for i, ry_ in enumerate(ribs):
                    gap = 0.22 + 0.12 * (i == 1)
                    if abs(y + .5 - ry_) < 1.25 * op and abs(ex) > gap:
                        rib = y + .5 < ry_
                if rib is not None:
                    fb.mat[y, x] = MI["O"]; fb.heat[y, x] = 0
                    fb.fix[y, x] = "H4" if rib else "H1"
                    continue
                fb.mat[y, x] = MI["M"]
                fb.heat[y, x] = k
            elif e < 1.55:          # broken rim of the shell: lit hot from inside
                fb.fix[y, x] = "H4" if e < 1.22 else "H2"


def paint_claws(fb, vis, claws, hot=0.45, s=1.0):
    """obsidian talons: lit / shadow facets, the tips forge-hot like the horns."""
    for (j, t) in claws:
        u = unit(j, t); v = perp(u)
        L = math.hypot(t[0] - j[0], t[1] - j[1]) + 1
        for q in np.arange(-1.0, L, 0.35):
            w_ = 1.8 * s * (1 - max(0, q) / L)
            for r in np.arange(-w_, w_ + 0.01, 0.35):
                x, y = int(j[0] + u[0] * q + v[0] * r), int(j[1] + u[1] * q + v[1] * r)
                if 0 <= x < W and 0 <= y < H and vis[y, x]:
                    lit = (v[0] * r * LIGHT[0] + v[1] * r * LIGHT[1]) > 0
                    tq = q / L
                    if tq > hot:
                        k = "M5" if tq > hot + (1 - hot) * 0.65 else "M4" if tq > hot + (1 - hot) * 0.3 else "M2"
                        fb.fix[y, x] = ""; fb.mat[y, x] = MI["M"]; fb.heat[y, x] = int(k[1]) / 7
                    else:
                        fb.fix[y, x] = ("O5" if lit else "O2") if tq > 0.15 else ("O4" if lit else "O1")


def arm_group(name, S, E, Wr, side, p, fist_dir=None, open_hand=False, rs=1.0, shell=1.0):
    """Massive arm: deltoid, biceps / triceps, forearm, clenched fist, iron shackle at the wrist."""
    g = Group(name, k=1.3)
    ua = unit(S, E); fa = unit(E, Wr)
    pu = perp(ua); pf = perp(fa)
    fwd = 1 if side == "far" else -1          # 'front' of the arm (toward facing = +x)
    if pu[0] * 1 < 0: pu = (-pu[0], -pu[1])
    if pf[0] * 1 < 0: pf = (-pf[0], -pf[1])
    s = rs
    # v3: sculpted titan arm -- round deltoid cap, bulging biceps / triceps over a slimmer bone core,
    # a forearm that swells below the elbow and tapers hard into the wrist
    g.add(P_ell(add(S, mul(ua, 5)), 19 * s, 14.5 * s, math.atan2(ua[1], ua[0]), z=14, hs=0.85), tag="delt", vein=0.5)
    g.add(P_ell(add(S, add(mul(ua, -2), mul(pu, -3 * fwd))), 12 * s, 10 * s, math.atan2(ua[1], ua[0]), z=12, hs=0.7), tag="deltB", vein=0.2)
    g.add(P_cap(S, E, 10.5 * s, 8.5 * s, z=8), tag="uarm", vein=0.12)
    mid = lerp(S, E, 0.56)
    g.add(P_ell(add(mid, mul(pu, 4.8 * s)), 12 * s, 7.8 * s, math.atan2(ua[1], ua[0]), z=14, hs=0.95), tag="bic", vein=0.5)
    g.add(P_ell(add(lerp(S, E, 0.45), mul(pu, -5 * s)), 12 * s, 7.0 * s, math.atan2(ua[1], ua[0]), z=12.5, hs=0.9), tag="tri", vein=0.2)
    g.add(P_ell(E, 8.5 * s, 8 * s, z=10), tag="elbow", vein=0.1)
    g.add(P_cap(E, Wr, 9.5 * s, 6.2 * s, z=9), tag="farm", vein=0.1)
    g.add(P_ell(add(lerp(E, Wr, 0.28), mul(pf, 3.2 * s)), 11 * s, 7.4 * s, math.atan2(fa[1], fa[0]), z=13.5, hs=0.95), tag="brach", vein=0.45)
    g.add(P_ell(add(lerp(E, Wr, 0.32), mul(pf, -3.5 * s)), 9.5 * s, 5.4 * s, math.atan2(fa[1], fa[0]), z=12, hs=0.9), tag="flex", vein=0.25)
    fd = fist_dir or fa
    fd = (fd[0] / math.hypot(*fd), fd[1] / math.hypot(*fd))
    fp = perp(fd)
    sg = 1 if fp[0] >= 0 else -1                  # +b = toward facing (thumb side)
    F = lambda a_, b_: add(Wr, add(mul(fd, a_ * s), mul(fp, b_ * s * sg)))
    fc = F(8, 0)
    g.add(P_cap(Wr, F(2, 0), 6.5 * s, 7.5 * s, z=7), tag="wrist", vein=0.2)
    ang_f = math.atan2(fd[1], fd[0])
    g.claws = []
    if open_hand:
        # v3 open talon hand: broad palm, four long jointed fingers splayed + curling, obsidian claws
        g.add(P_poly([F(-1, -8), F(-1, 8), F(10, 9.5), F(10.5, -9.5)], z=13, bevel=4, hs=1.0), tag="fist", vein=0.0, facet=0.2)
        for i, (bb, sp, ln) in enumerate(((-7.0, -0.30, 12), (-2.4, -0.10, 14), (2.3, 0.08, 13.5), (6.6, 0.26, 11))):
            k0 = F(10, bb)
            d0 = (math.cos(ang_f + sp * sg), math.sin(ang_f + sp * sg))
            j1 = add(k0, mul(d0, ln * 0.5 * s))
            ca = ang_f + (sp + 0.55) * sg
            d1 = (math.cos(ca), math.sin(ca))
            j2 = add(j1, mul(d1, ln * 0.33 * s))
            ca2 = ang_f + (sp + 1.1) * sg
            tip = add(j2, mul((math.cos(ca2), math.sin(ca2)), ln * 0.28 * s))
            g.add(P_ell(k0, 3.4 * s, 2.8 * s, ang_f + math.pi / 2, z=15.5, hs=0.9), tag="knk%d" % i, vein=0.0, facet=0.1)
            g.add(P_cap(k0, j1, 2.7 * s, 2.3 * s, z=14), tag="fing%d" % i, vein=0.0, facet=0.1)
            g.add(P_cap(j1, j2, 2.3 * s, 1.9 * s, z=14.5), tag="fingb%d" % i, vein=0.0, facet=0.1)
            g.claws.append((j2, tip))
        th0 = F(4, 8.5)
        tdir = (math.cos(ang_f + 0.9 * sg), math.sin(ang_f + 0.9 * sg))
        th1 = add(th0, mul(tdir, 7 * s))
        tdir2 = (math.cos(ang_f + 0.3 * sg), math.sin(ang_f + 0.3 * sg))
        th2 = add(th1, mul(tdir2, 6 * s))
        g.add(P_cap(th0, th1, 3.6 * s, 2.8 * s, z=16), tag="thumb", vein=0.0, facet=0.1)
        g.add(P_cap(th1, th2, 2.8 * s, 2.2 * s, z=16.5), tag="thumbb", vein=0.0, facet=0.1)
        g.claws.append((th2, add(th2, mul(tdir2, 4 * s))))
        for (j, t) in g.claws:
            u = unit(j, t); v = perp(u)
            jb = add(j, mul(u, -1.5))
            g.add(P_poly([add(jb, mul(v, 1.9 * s)), add(t, mul(u, 1.0)), add(jb, mul(v, -1.9 * s))], z=17, bevel=1.0, hs=0.6),
                  tag="claw", vein=0.0, facet=0.0)
        fc = F(14, 0)
    else:
        # v3 fist: back of the hand, a row of four big knuckles, the curled finger segments below them,
        # and a heavy thumb clamped across -- separated by crisp creases so every finger reads
        g.add(P_poly([F(-1, -8.5), F(-1, 8.5), F(11, 10.2), F(11.5, -10.2)], z=13, bevel=4, hs=1.0), tag="fist", vein=0.0, facet=0.3)
        for i, bb in enumerate((-7.1, -2.4, 2.4, 7.1)):
            g.add(P_ell(F(11.2, bb), 3.6 * s, 2.8 * s, ang_f + math.pi / 2, z=15.5 - abs(bb) * 0.12, hs=0.9),
                  tag="knk%d" % i, vein=0.0, facet=0.2)
            g.add(P_ell(F(15.8, bb * 0.97), 3.0 * s, 2.4 * s, ang_f, z=14.2 - abs(bb) * 0.1, hs=0.9),
                  tag="fing%d" % i, vein=0.0, facet=0.2)
        g.add(P_ell(F(9.0, 10.0), 6.4 * s, 3.2 * s, ang_f + 0.55 * sg, z=17.5), tag="thumb", vein=0.0, facet=0.2)
        g.add(P_ell(F(14.6, 7.6), 2.8 * s, 2.5 * s, z=18), tag="thumbtip", vein=0.0, facet=0.2)
    for (bo, to, w) in (p.get("delt_shards_" + side) or []):
        add_shard(g, add(S, bo), add(S, to), w, z=24)
    # shackle (blackened iron cuff)
    cu = add(Wr, mul(fa, -3 * s))
    g.add(P_band(add(cu, mul(fa, -3.5 * s)), add(cu, mul(fa, 3.5 * s)), 9.6 * s, z=11, hs=0.6), mat="I", tag="cuff", facet=0)
    g.add(P_band(add(cu, mul(fa, -4.5 * s)), add(cu, mul(fa, -2.5 * s)), 10.4 * s, z=12, hs=0.6), mat="I", tag="cuffR", facet=0)
    g.add(P_band(add(cu, mul(fa, 2.5 * s)), add(cu, mul(fa, 4.5 * s)), 10.4 * s, z=12, hs=0.6), mat="I", tag="cuffR", facet=0)

    def dec(fb, vis):
        # veins down the arm following biceps / forearm lines
        vein_path(fb, vis, [add(S, mul(pu, 2)), add(lerp(S, E, 0.5), mul(pu, 1)), add(E, mul(pu, -1))], 0.55, 0.3,
                  branch=2, seed=(sum(map(ord, name)) * 1) % 97)
        vein_path(fb, vis, [add(E, mul(pf, 2)), add(lerp(E, Wr, 0.6), mul(pf, -2)), add(Wr, mul(pf, -1))], 0.5, 0.8,
                  branch=2, seed=(sum(map(ord, name)) * 2) % 97, width=2)
        # cuff: rivets + hot inner edge where it bites the wrist
        for t in (-6, 0, 6):
            q = add(add(cu, mul(pf, t * s)), mul(fa, 1))
            fb.paint([(int(q[0]), int(q[1]))], "I5", vis)
            fb.paint([(int(q[0]) + 1, int(q[1]) + 1)], "I0", vis)
        # glowing seam where the shackle bites into the wrist
        for t in np.arange(-9, 9.5, 0.8):
            q = add(add(cu, mul(pf, t * s)), mul(fa, 4.6 * s))
            fb.paint([(int(q[0]), int(q[1]))], "M3" if abs(t) < 6 else "M1", vis)
        paint_claws(fb, vis, getattr(g, "claws", []))
        # v3 fingers: dark cuts between the digits, a glassy catch-light on each knuckle
        tags = [pr.tag for pr in g.prims]
        dig = [i for i, t in enumerate(tags) if t.startswith(("knk", "fing", "thumb"))]
        hand = np.isin(g.own, dig) & vis & (fb.mat != MI["M"])
        own = np.where(hand, g.own, -1)
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            o2 = shift(own, -dx, -dy, -1)
            cut = hand & (o2 >= 0) & (o2 != own) & (g.hf < shift(g.hf, -dx, -dy, NEG))
            fb.fix[cut & (fb.fix == "")] = "O0"
        for i in dig:
            if not tags[i].startswith("knk"):
                continue
            mm = hand & (g.own == i)
            if mm.any():
                sc = np.where(mm, g.nx * LIGHT[0] + g.ny * LIGHT[1] + g.nz * LIGHT[2], -9)
                y, x = np.unravel_index(np.argmax(sc), sc.shape)
                fb.fix[y, x] = "O6"
    g.decal(dec)
    g.cuff = (cu, pf)
    g.fist = fc
    return g


def leg_group(name, Hp, K, A, side, p, rs=1.0):
    g = Group(name, k=1.3)
    th = unit(Hp, K); sh = unit(K, A)
    pt = perp(th)
    if pt[0] < 0: pt = (-pt[0], -pt[1])
    ps = perp(sh)
    if ps[0] < 0: ps = (-ps[0], -ps[1])
    g.add(P_cap(Hp, K, 15, 11.5, z=6), tag="thigh", vein=0.1)
    g.add(P_ell(add(lerp(Hp, K, 0.5), mul(pt, 4)), 14, 8.5, math.atan2(th[1], th[0]), z=10), tag="quad", vein=0.35)
    g.add(P_ell(add(lerp(Hp, K, 0.62), mul(pt, -5)), 11, 6, math.atan2(th[1], th[0]), z=8), tag="ham", vein=0.1)
    g.add(P_ell(K, 9, 8.5, z=11), tag="knee", vein=0.2)
    g.add(P_cap(K, A, 11, 7.5, z=7), tag="shin", vein=0.1)
    g.add(P_ell(add(lerp(K, A, 0.33), mul(ps, -4.5)), 10, 6.5, math.atan2(sh[1], sh[0]), z=10), tag="calf", vein=0.3)
    fx, fy = A[0], GROUND
    # v3 foot: heavy heel, high arch, three splayed clawed toes
    g.add(P_ell((fx - 1, A[1] + 1), 8.5, 7.5, z=8), tag="ankle", vein=0.1)
    foot = [(fx - 10, fy + 1), (fx - 11, fy - 5), (fx - 6, A[1] - 2), (fx + 4, A[1] - 1), (fx + 11, fy - 9),
            (fx + 16, fy - 6), (fx + 17, fy + 1)]
    g.add(P_poly(foot, z=6, bevel=4, hs=1.0), tag="foot", vein=0.1, facet=0.3)
    g.add(P_ell((fx - 8, fy - 3), 5, 4, z=9), tag="heel", vein=0.0)
    g.claws = []
    for i, (tx, ty, r) in enumerate(((8.5, -3.2, 3.6), (13.5, -3.4, 3.8), (18.0, -2.8, 3.3))):
        g.add(P_ell((fx + tx, fy + ty), r * 1.15, r * 0.95, z=10 + i * 0.4), tag="toe%d" % i, vein=0.0, facet=0.1)
        j = (fx + tx + r * 0.8, fy + ty - 0.6)
        g.claws.append((j, (j[0] + 4.2, j[1] + 3.2)))
    for (j, t) in g.claws:
        u = unit(j, t); v = perp(u)
        jb = add(j, mul(u, -1.5))
        g.add(P_poly([add(jb, mul(v, 1.8)), add(t, mul(u, 0.8)), add(jb, mul(v, -1.8))], z=13, bevel=1.0, hs=0.6),
              tag="claw", vein=0.0, facet=0.0)
    def dec(fb, vis):
        paint_claws(fb, vis, g.claws, hot=0.55)
        vein_path(fb, vis, [add(Hp, mul(pt, 3)), add(lerp(Hp, K, 0.5), mul(pt, 1)), add(K, mul(pt, -2))], 0.45, 0.65,
                  branch=2, seed=(sum(map(ord, name)) * 3) % 97, width=2)
        vein_path(fb, vis, [add(K, mul(ps, 1)), add(lerp(K, A, 0.6), mul(ps, 2)), (fx + 4, fy - 3)], 0.5, 0.7,
                  branch=1, seed=(sum(map(ord, name)) * 4) % 97)
    g.decal(dec)
    return g


# =========================================================================== hand-pixelled face (3/4, facing right)
# legend: K O0 | 1-6 obsidian | S glint | j/h/H heat-lit | r o O y Y W molten M2..M7 | t tusk | g gold
FACE_KEYS = {"K": "O0", "1": "O1", "2": "O2", "3": "O3", "4": "O4", "5": "O5", "6": "O6", "S": "OS",
             "j": "H1", "h": "H2", "H": "H3", "r": "M2", "o": "M3", "O": "M4", "y": "M5", "Y": "M6", "W": "M7",
             "t": "O6", "g": "G3", "G": "G4", "q": "M1", "b": "O6", "B": "OS"}
FACE = [
"      1112223333333221      ",
"    11222333444444444321    ",
"   1122333444455555555432   ",
"  112233444555566666665543  ",
"  11223344555666666666666S3 ",
"  112KKKKK3444KKKKK4KKKKKKK1",
"  11KrooKKKK33KKo3KKKKKOoK21",
"  11KKOyYOKKK2KKo2KKYWyOKK21",
"  112KKKOyWWOK2Ko2KOWWYKKK21",
"  1122hKKKKKKK23o34KKKKK3321",
"  11222hh22233o44455S554431 ",
"   12222h2223o34444555543 1 ",
"   1222222K3KK344444444321  ",
"   12hhhhHHHoHHhh33344432   ",
]
MT = [
"   1KKKKKKKKKKKKKKKKKKKKK21 ",
"   1KK5KrrooOOyyOOoorr5KK21 ",
]
MIF = "   1KKrKOKyKWKWKWKyKOKrKK21 "
MI_ = "   1KroOyYWWWWWWWYyOorKKK21 "
MIB = "   1KKrKOKyKWKWKWKyKOrKKK21 "
MB = [
"   1K6KroOOyyyyOOor6K6KK21  ",
"   11KKKKKKKKKKKKKKKKKKK21  ",
]
JAW = [
"   11hHh2233o333hhH3334321  ",
"   11122h2233o33344445431   ",
"    11112222o233344444321   ",
"      111122o22333333321    ",
"         1111K11222211      ",
]
TUSK = {0: ((5, "B"), (6, "b"), (22, "B"), (23, "b")), -1: ((5, "B"), (6, "b"), (22, "B"), (23, "b")),
        -2: ((5, "B"), (6, "6"), (22, "B"), (23, "6")), -3: ((5, "B"), (23, "B")), -4: ((4, "b"), (24, "b"))}
def face_rows(roar):
    n = int(round(roar * 7))
    mi = [MI_] if n == 0 else [MIF] + [MI_] * max(0, n - 1) + [MIB]
    R = [list(r.ljust(30)) for r in FACE + MT + mi + MB + JAW]
    j0 = len(FACE) + len(MT) + len(mi)
    for dy, px in TUSK.items():
        for (i, ch) in px:
            R[j0 + dy][i] = ch
    return ["".join(r) for r in R]


def face_sample(p):
    """-> dict frame pixel -> palette key (inverse-mapped so tilting the head keeps it hole-free)."""
    c = p["Hd"]; a = p.get("head_ang", 0.0)
    rows = face_rows(p.get("roar", 0.0))
    ox, oy = c[0] - 14, c[1] - 7          # frame position of the map's top-left (unrotated)
    hgt = len(rows)
    out = {}
    cs, sn = math.cos(-a), math.sin(-a)
    for y in range(int(c[1] - 40), int(c[1] + 45)):
        for x in range(int(c[0] - 40), int(c[0] + 40)):
            dx, dy = x + 0.5 - c[0], y + 0.5 - c[1]
            sx = c[0] + dx * cs - dy * sn; sy = c[1] + dx * sn + dy * cs
            i, j = int(math.floor(sx - ox)), int(math.floor(sy - oy))
            if 0 <= j < hgt and 0 <= i < 30:
                ch = rows[j][i]
                if ch != " ":
                    out[(x, y)] = FACE_KEYS[ch]
    return out


def head_group(p):
    """Horned crown of blackened iron fused to an obsidian skull; a hand-pixelled cracked mask face
    (scowling brow, molten slit eyes, fissure, tusked glowing maw).  v3: crescent bull horns framing a
    tall faceted iron crown with an Ashwright-gold rim + seal."""
    c = p["Hd"]; a = p.get("head_ang", 0.0); s = p.get("head_s", 1.1)
    R = lambda q: rot(add(c, (q[0] * s, q[1] * s)), c, a)
    Ri = lambda q: (int(round(R(q)[0])), int(round(R(q)[1])))
    g = Group("head", k=0.9)
    # far horn: out to the right, then up and curling back in (crescent)
    hF = bez(R((8, -9)), R((22, -14)), R((25, -30)), R((15, -45)), 26)
    g.add(P_tube(hF, 4.6 * s, 0.7, z=2, hs=0.9), mat="I", tag="hornF", facet=0)
    g.add(P_ell(R((-6, -2)), 13 * s, 12 * s, a, z=6), tag="cran", facet=0.6)
    face = face_sample(p)
    fm = np.zeros((H, W), bool)
    for (x, y) in face:
        if 0 <= x < W and 0 <= y < H:
            fm[y, x] = True
    g.add(P_poly(None, z=9, bevel=3, hs=0.8, mask=fm), tag="face", facet=0)
    # crown: a slanted iron band + five faceted spikes, the centre one tallest
    band = [(-16, -12.5), (15, -15.5), (16, -8.5), (-15, -5.5)]
    g.add(P_poly([R(q) for q in band], z=17, bevel=2.0, hs=0.9), mat="I", tag="crown", facet=0)
    SP = ((-12.5, 7, -0.30, 2.6), (-6, 11, -0.14, 2.9), (0.8, 16, 0.0, 3.2), (7.5, 11, 0.14, 2.9), (13, 7, 0.30, 2.6))
    spikes = []
    for (sx, hgt, lean, w) in SP:
        y0 = -12.2 - (sx + 16) * 0.097
        b0, b1 = (sx - w, y0 + 1.2), (sx + w, y0 + 1.2)
        tip = (sx + lean * hgt, y0 - hgt)
        g.add(P_poly([R(b0), R(b1), R(tip)], z=18, bevel=1.0, hs=0.6), mat="I", tag="spike", facet=0)
        spikes.append((R(b0), R(b1), R(tip), R(((b0[0] + b1[0]) / 2, y0 - 0.4))))
    # near horn (behind the crown): out to the left, sweeping up
    hN = bez(R((-12, -8)), R((-29, -12)), R((-37, -28)), R((-29, -46)), 26)
    g.add(P_tube(hN, 6.0 * s, 0.8, z=22, hs=0.9), mat="I", tag="hornN", facet=0)
    g.horns = (hN, hF)
    g.clip = None

    def dec(fb, vis):
        for (x, y), k in face.items():
            if 0 <= x < W and 0 <= y < H and vis[y, x]:
                fb.fix[y, x] = k
                if k.startswith("M"):
                    fb.mat[y, x] = MI["M"]; fb.heat[y, x] = int(k[1]) / 7
        P = lambda pts, k: fb.paint([Ri(q) for q in pts], k, vis)
        if p.get("p2"):          # the mask is splitting apart: molten cracks spread from the eyes and maw
            for path, k0 in (([(-6, 0), (-9, 3), (-10, 8), (-12, 10)], 5), ([(8, 1), (10, 5), (9, 9)], 4),
                             ([(-3, -4), (-7, -6), (-11, -5)], 4), ([(0, 15), (-2, 19), (1, 23)], 5),
                             ([(10, -3), (13, -5)], 3)):
                pts = smooth([(c[0] + q[0], c[1] + q[1]) for q in path], 5, 0.6, 3)
                for i, q in enumerate(pts):
                    q = rot(q, c, a)
                    x, y = int(round(q[0])), int(round(q[1]))
                    if 0 <= x < W and 0 <= y < H and vis[y, x]:
                        fb.fix[y, x] = "M%d" % max(2, k0 - i // 6)
        # --- crown spikes: two crisp facets (lit right / shadow left), bright ridge, gold-capped tips
        for (b0, b1, tip, bm) in spikes:
            xs = [b0[0], b1[0], tip[0]]; ys = [b0[1], b1[1], tip[1]]
            for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
                for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
                    if not (0 <= x < W and 0 <= y < H and vis[y, x] and fb.mat[y, x] == MI["I"]):
                        continue
                    # which side of the ridge (bm -> tip)
                    rx, ry = tip[0] - bm[0], tip[1] - bm[1]
                    side = (x + 0.5 - bm[0]) * ry - (y + 0.5 - bm[1]) * rx
                    t = (bm[1] - (y + 0.5)) / max(1e-3, bm[1] - tip[1])
                    if fb.gid[y, x] != len(fb.groups) - 1:
                        continue
                    if t < 0.0:
                        continue
                    if abs(side) / math.hypot(rx, ry) < 0.55:
                        k = "I5" if t > 0.15 else "I4"
                    elif side < 0:
                        k = "I4" if t > 0.4 else "I3"
                    else:
                        k = "I2" if t > 0.5 else "I1"
                    if t > 0.84:
                        k = "G4" if side < 0 or abs(side) < 1 else "G2"
                    fb.fix[y, x] = k
        # --- band: gold rims, dark iron face with studs, the Ashwright seal at the centre
        def bandpt(t, v):       # t 0..1 along the band (left->right), v 0 top .. 1 bottom
            top = lerp(band[0], band[1], t); bot = lerp(band[3], band[2], t)
            return lerp(top, bot, v)
        tl, tr, br_, bl = [R(q) for q in band]
        gi = len(fb.groups) - 1
        cm = np.zeros((H, W), bool)
        cm[:] = False
        bm_ = mask_poly([tl, tr, br_, bl])
        cm = bm_ & vis & (fb.gid == gi) & (fb.mat == MI["I"]) & (fb.fix == "")
        for x in range(W):
            ys = np.nonzero(cm[:, x])[0]
            if len(ys) == 0:
                continue
            y0_, y1_ = ys.min(), ys.max()
            t = np.clip((x + 0.5 - tl[0]) / max(1e-3, tr[0] - tl[0]), 0, 1)
            for y in ys:
                j = y - y0_; jb = y1_ - y
                if j == 0:
                    k = "G4" if t > 0.3 else "G3"
                elif j == 1:
                    k = "G2"
                elif jb == 0:
                    k = "G3" if t > 0.45 else "G2"
                elif jb == 1:
                    k = "I0"
                else:
                    k = "I3" if t > 0.6 else "I2"
                fb.fix[y, x] = k
        for t in (0.13, 0.31, 0.75, 0.9):
            P([bandpt(t, 0.55)], "G3")
        sg = bandpt(0.53, 0.52)
        P([(sg[0], sg[1] - 1), (sg[0] - 1, sg[1]), (sg[0] + 1, sg[1]), (sg[0], sg[1] + 1)], "G3")
        P([sg], "M6")
        P([(sg[0], sg[1] - 1)], "G5")
        # --- horns: ridged iron (growth rings), gold bands near the root, forge-hot tips
        for hp, r0 in ((hN, 6.0 * s), (hF, 4.6 * s)):
            n = len(hp) - 1
            for i in range(3, int(n * 0.62), 3):
                q = hp[i]; q2 = hp[i + 1]
                u = unit(q, q2); v = perp(u)
                r = r0 + (0.8 - r0) * i / n
                for tt in np.arange(-r + 0.5, r - 0.4, 0.5):
                    x, y = int(q[0] + v[0] * tt), int(q[1] + v[1] * tt)
                    if 0 <= x < W and 0 <= y < H and vis[y, x] and fb.mat[y, x] == MI["I"]:
                        fb.bias[y, x] -= 1.2
            for t in (4, 5):
                q = hp[t]; fb.paint([(int(q[0]), int(q[1])), (int(q[0]) + 1, int(q[1]))], "G3", vis)
            q = hp[6]; fb.paint([(int(q[0]), int(q[1]))], "G4", vis)
        ht = p.get("horn_heat", 0.8)
        for hp, r0 in ((hN, 6.0 * s), (hF, 4.6 * s)):
            n = len(hp) - 1
            for i in range(int(n * 0.6), n + 1):
                t = max(0.0, (i - n * 0.6) / (n * 0.4))
                r = r0 + (0.8 - r0) * i / n
                for dy in np.arange(-r, r + 0.1, 0.5):
                    for dx in np.arange(-r, r + 0.1, 0.5):
                        if dx * dx + dy * dy > r * r:
                            continue
                        x, y = int(hp[i][0] + dx), int(hp[i][1] + dy)
                        if 0 <= x < W and 0 <= y < H and vis[y, x] and fb.mat[y, x] == MI["I"] and not fb.fix[y, x]:
                            hv = ht * t ** 1.6
                            if hv > 0.16:
                                fb.mat[y, x] = MI["M"]; fb.heat[y, x] = min(1.0, hv * 1.05)
    g.decal(dec)
    return g


MARK = ["..GGG..",
        ".GkkkH.",
        "GkmmmkH",
        "GkkmkkH",
        "GkkmkkH",
        ".gkkkH.",
        "..ggg.."]


def hammer_group(p):
    """Colossal anvil-headed hammer (v3): a stepped anvil of black iron -- table, waist, flared base --
    with a long tapering horn, gold-trimmed base, Ashwright's gold maker's seal on the flank, forge
    runes, and a banded haft.  The anvil's face is the striking face, still glowing from the forge."""
    g = Group("hammer", k=0.8)
    ang = p["ham_ang"]                         # direction face -> haft
    k = p.get("ham_s", 1.25)
    u = (math.cos(ang), math.sin(ang)); v = perp(u)
    if p.get("ham_flip"):
        v = (-v[0], -v[1])
    hc = p.get("ham_c")
    if p.get("ham_grip"):
        hc = sub(p["ham_grip"], mul(u, 26 * k + p.get("ham_grip_d", 40)))
    L = p.get("ham_len", 70)
    T0 = lambda c, a, b: add(c, add(mul(u, a * k), mul(v, b * k)))
    OUTL = [(0, -19), (0, 13), (1.2, 19), (2.6, 24), (4.5, 29), (6.5, 25), (9.5, 19), (12, 13), (13, 9), (15.5, 7.5),
            (18, 10.5), (19, 13.5), (26, 13.5), (26, -17.5), (19, -17.5), (18, -14.5), (15.5, -11.5), (13, -13),
            (12, -19), (10, -21.5), (3, -21.5)]
    if p.get("ham_ground"):
        ys = [T0(hc, a_, b_)[1] for a_, b_ in OUTL]
        hc = (hc[0], hc[1] + GROUND - max(ys))
    T = lambda a, b: T0(hc, a, b)
    sock = T(26, -2)
    top = add(sock, mul(u, L))
    g.add(P_cap(sock, top, 4.0, 3.5, z=4, hs=0.8), mat="I", tag="haft", facet=0)
    g.add(P_ell(add(top, mul(u, 2.5)), 4.8, 4.8, z=6), mat="G", tag="pommel", facet=0)
    g.add(P_poly([T(a_, b_) for a_, b_ in OUTL], z=8, bevel=3, hs=0.9), mat="I", tag="anvil", facet=0)
    g.add(P_cap(add(sock, add(mul(u, 1.5), mul(v, -5.2))), add(sock, add(mul(u, 1.5), mul(v, 5.2))), 2.4, 2.4, z=10),
          mat="G", tag="collar", facet=0)
    g.face = (T(0, -21), T(0, 14))

    def ab(x, y):
        d = (x + 0.5 - hc[0], y + 0.5 - hc[1])
        return (d[0] * u[0] + d[1] * u[1]) / k, (d[0] * v[0] + d[1] * v[1]) / k

    def dec(fb, vis):
        gi = len(fb.groups) - 1
        tags = [pr.tag for pr in g.prims]
        ia = tags.index("anvil"); ih = tags.index("haft")
        L2 = np.array([LIGHT[0], LIGHT[1]]); L2 = L2 / np.linalg.norm(L2)
        lu = u[0] * L2[0] + u[1] * L2[1]            # how lit a ledge facing +u is
        lv = v[0] * L2[0] + v[1] * L2[1]
        anv = vis & (fb.gid == gi) & (g.own == ia)
        edge_d = dist_in(g.mask & (g.own == ia), 3)
        heat = p.get("face_heat", 0.8)
        for y, x in zip(*np.nonzero(anv)):
            a_, b_ = ab(x, y)
            en = g.nx[y, x] * L2[0] + g.ny[y, x] * L2[1]
            horn = b_ > 13
            # base tone per tier; slight gradient toward the lit side
            if a_ < 12.3 or horn:
                tone = 2.4 + 0.9 * np.clip(b_ * lv / 22, -1, 1)
            elif a_ < 18.3:
                tone = 1.2 + 0.5 * np.clip(b_ * lv / 12, -1, 1)
            else:
                tone = 2.1 + 0.8 * np.clip(b_ * lv / 16, -1, 1)
            # ledges (the step faces between the tiers)
            for la, sgn in ((12.3, 1), (18.3, 1), (18.3 - 1.4, -1)):
                pass
            if 12.3 <= a_ < 13.4 and not horn:
                tone = 4.2 if lu > 0 else 0.2
            elif 11.2 <= a_ < 12.3 and not horn:
                tone = 0.4 if lu > 0 else 3.8
            elif 18.3 <= a_ < 19.4:
                tone = 4.0 if lu > 0 else 0.3
            elif 17.2 <= a_ < 18.3:
                tone = 0.6 if lu > 0 else 3.6
            # silhouette bevel: lit edges catch a bright line, the rest drop into shadow
            if edge_d[y, x] <= 1.2:
                tone = 4.6 if en > 0.25 else (0.3 if en < -0.2 else tone)
            if horn:
                t_h = (b_ - 13) / 16
                tone += 0.6 * (1 - t_h)
            fb.fix[y, x] = "I%d" % int(np.clip(round(tone), 0, 5))
            # gold trim band around the base
            if 23.6 <= a_ < 25.2 and edge_d[y, x] > 1.2:
                fb.fix[y, x] = "G4" if b_ * lv > 6 else "G3" if b_ * lv > -6 else "G2"
            elif 25.2 <= a_ and edge_d[y, x] > 0.9:
                fb.fix[y, x] = "G2"
            # the striking face: forge-hot, fading up into the iron
            if a_ < 4.2 and not (horn and a_ > 3.0):
                hv = heat * (1 - a_ / 4.2) ** 1.1
                if hv > 0.14:
                    fb.fix[y, x] = ""; fb.mat[y, x] = MI["M"]; fb.heat[y, x] = hv
        # gold studs on the base corners
        for bb in (-14.5, 10.5):
            q = T(21.5, bb)
            fb.paint([(int(q[0]), int(q[1]))], "G4", vis)
            fb.paint([(int(q[0]) + 1, int(q[1]) + 1)], "G1", vis)
        # Ashwright's seal: a gold ring holding a hammer-cross, a molten gem at its heart
        mc = T(8.4, -3.5)
        MK = {"G": "G3", "H": "G4", "g": "G2", "k": "I0", "m": "G5"}
        for j, row in enumerate(MARK):
            for i, ch in enumerate(row):
                if ch != ".":
                    x, y = int(mc[0]) - 3 + i, int(mc[1]) - 3 + j
                    if 0 <= x < W and 0 <= y < H and vis[y, x]:
                        fb.fix[y, x] = MK[ch]
        # forge runes flanking the seal (small glowing glyphs, upright in frame space)
        RUNES = (["x.x", "xx.", "x.x", "x.."], ["x..", "xx.", "x.x", "xx."])
        for bb, rn in zip((-14.5, 7.0), RUNES):
            rc = T(8.4, bb)
            for j, row in enumerate(rn):
                for i, ch in enumerate(row):
                    if ch == "x":
                        x, y = int(rc[0]) - 1 + i, int(rc[1]) - 2 + j
                        if 0 <= x < W and 0 <= y < H and vis[y, x]:
                            fb.fix[y, x] = ""; fb.mat[y, x] = MI["M"]; fb.heat[y, x] = p.get("rune_heat", 0.6)
        # haft: banded iron -- dark wraps with lit ridges, gold rings under the grip
        hm = vis & (fb.gid == gi) & (g.own == ih)
        for y, x in zip(*np.nonzero(hm)):
            d = (x + 0.5 - sock[0], y + 0.5 - sock[1])
            t = d[0] * u[0] + d[1] * u[1]
            s_ = d[0] * v[0] + d[1] * v[1]
            side = s_ * lv
            base = 3 if side > 1.2 else 2 if side > -1.2 else 1
            ph = (t % 5.0)
            if ph < 1.0:
                base = 0 if side < 1 else 2
            elif ph < 2.0:
                base = min(5, base + 1)
            fb.fix[y, x] = "I%d" % base
            if L - 12 < t < L - 10 or 5 < t < 7:
                fb.fix[y, x] = "G4" if side > 0.5 else "G2"
    g.decal(dec)
    g.grip = top
    return g


def P_band(a, b, r, z=0.0, hs=1.0):
    """Cylinder segment WITHOUT round caps (a cuff / band)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy or 1e-6
    t = ((XC - a[0]) * dx + (YC - a[1]) * dy) / L2
    qx, qy = a[0] + dx * t, a[1] + dy * t
    d2 = (XC - qx) ** 2 + (YC - qy) ** 2
    ok = (t >= 0) & (t <= 1) & (d2 <= r * r)
    return np.where(ok, z + hs * np.sqrt(np.clip(r * r - d2, 0, None)), NEG)


def add_shard(g, b, t, w, z=6.0):
    """two-faceted obsidian spire from base b to tip t."""
    u = unit(b, t); v = perp(u)
    l = math.hypot(t[0] - b[0], t[1] - b[1])
    mid = add(b, mul(u, l * 0.35))
    g.add(P_poly([add(b, mul(v, -w)), add(mid, mul(v, -w * 0.7)), t, b], z=z, bevel=1.2, hs=0.5,
                 tilt=(v[0] * -0.5, v[1] * -0.5)), tag="shard", facet=0.2)
    g.add(P_poly([b, t, add(mid, mul(v, w * 0.7)), add(b, mul(v, w))], z=z, bevel=1.2, hs=0.5,
                 tilt=(v[0] * 0.5, v[1] * 0.5)), tag="shard", facet=0.2)


def shards_group(p):
    """Obsidian spires erupting from the back and shoulders (jagged mythic silhouette)."""
    T = p["T"]
    g = Group("shards", k=0.5)
    for (bx, by), (tx, ty), w in p.get("shards", SHARDS):
        b = T((bx, by)); t = T((tx, ty))
        u = unit(b, t); v = perp(u)
        l = math.hypot(t[0] - b[0], t[1] - b[1])
        left = [add(b, mul(v, -w)), t, b]
        right = [b, t, add(b, mul(v, w))]
        mid = add(b, mul(u, l * 0.35))
        # two facets meeting along a ridge: lit side / shadow side
        g.add(P_poly([add(b, mul(v, -w)), add(mid, mul(v, -w * 0.7)), t, b], z=6, bevel=1.2, hs=0.5,
                     tilt=(v[0] * -0.5, v[1] * -0.5)), tag="shard", facet=0.2)
        g.add(P_poly([b, t, add(mid, mul(v, w * 0.7)), add(b, mul(v, w))], z=6, bevel=1.2, hs=0.5,
                     tilt=(v[0] * 0.5, v[1] * 0.5)), tag="shard", facet=0.2)
    return g


SHARDS = [  # torso-space base, tip, half-width
    ((78, 44), (64, 22), 6.0), ((90, 40), (84, 18), 5.0), ((70, 52), (52, 38), 5.0), ((101, 38), (103, 24), 3.6),
]


def cloth_group(p):
    """Scorched war-loincloth (v3): one heavy deep-red panel with soft vertical folds, a gold-embroidered
    border, torn tatters either side, the hem burnt ragged with a glowing ember edge."""
    T = p["T"]
    g = Group("cloth", k=0.6)
    sw = p.get("cloth_sw", 0)
    tl, tr = T((97, 112)), T((122, 111))
    ln = 36
    bl = (tl[0] + sw * 0.5 - 1, tl[1] + ln - 3); br_ = (tr[0] + sw + 2, tr[1] + ln - 5)
    # ragged hem (fixed zig-zag, not noise): points between bl and br
    hem = []
    for i in range(9):
        t = i / 8
        q = lerp(bl, br_, t)
        hem.append((q[0], q[1] + (4.5 if i % 2 else 0) + (2 if i in (3, 6) else 0)))
    panel = [tl, tr] + hem[::-1]
    g.add(P_poly(panel, z=14, bevel=2.5, hs=0.8), mat="C", tag="panel", facet=0)
    tat = []
    for (a0, a1, dx, l2) in ((T((90, 111)), T((97, 112)), -3, 26), (T((122, 111)), T((129, 109)), 3, 22)):
        b0 = (a0[0] + dx + sw * 0.3, a0[1] + l2); b1 = (a1[0] + dx * 0.5 + sw * 0.3, a1[1] + l2 - 4)
        pts = [a0, a1, b1, lerp(b0, b1, 0.5), b0]
        g.add(P_poly(pts, z=12, bevel=2, hs=0.8), mat="C", tag="tatter", facet=0, bias=-1)
        tat.append(pts)
    L2 = np.array([LIGHT[0], LIGHT[1]]) / np.linalg.norm([LIGHT[0], LIGHT[1]])

    def dec(fb, vis):
        gi = len(fb.groups) - 1
        cm = vis & (fb.gid == gi)
        pw = tr[0] - tl[0]
        for y, x in zip(*np.nonzero(cm)):
            tag = g.prims[g.own[y, x]].tag
            t = (x + 0.5 - tl[0]) / pw
            tv = (y + 0.5 - tl[1]) / ln
            if tag == "panel":
                fold = math.cos(2 * math.pi * (t * 3.0 + tv * 0.25))
                tone = 2.0 + 1.15 * fold + 0.6 * (t - 0.5) - 0.9 * tv
                if abs(t - 0.07) < 0.028 or abs(t - 0.93) < 0.028:        # gold embroidered border
                    fb.fix[y, x] = "G3" if (y % 3 == 0) else "G2"
                    continue
                if tv < 0.07:
                    tone = 0.4
            else:
                tone = 1.3 + 0.7 * math.cos(x * 0.9) - 0.7 * tv
            fb.fix[y, x] = "C%d" % int(np.clip(round(tone), 0, 4))
        # burnt hem: charred edge + glowing embers along the bottom of every piece
        for x in range(W):
            ys = np.nonzero(cm[:, x])[0]
            if len(ys) == 0:
                continue
            yb = ys.max()
            if yb < tl[1] + 12:
                continue
            fb.fix[yb, x] = "M3" if hsh(x, 3) > 0.45 else "M1"
            if yb - 1 >= 0 and cm[yb - 1, x]:
                fb.fix[yb - 1, x] = "C0"
            if hsh(x, 7) > 0.7 and yb - 2 >= 0 and cm[yb - 2, x]:
                fb.fix[yb - 2, x] = "M2"
        # small gold seal of Ashwright stitched on the panel (ring + hammer)
        c = lerp(tl, tr, 0.5)
        cx, cy = int(c[0]), int(c[1] + 8)
        for (dx, dy) in ((0, -2), (-1, -1), (1, -1), (-2, 0), (2, 0), (-1, 1), (1, 1), (0, 2)):
            fb.paint([(cx + dx, cy + dy)], "G2" if dy > 0 else "G3", cm)
        fb.paint([(cx, cy)], "G4", cm)
        fb.paint([(cx, cy + 3), (cx, cy + 4)], "G2", cm)
    g.decal(dec)
    return g



# =========================================================================== overlay FX (chains, embers, drips, fire)
class Overlay:
    def __init__(self):
        self.px = {}          # (x,y) -> key
        self.outline = set()  # pixels that get the dark outline treatment

    def put(self, x, y, key, ol=True):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.px[(x, y)] = key
            if ol:
                self.outline.add((x, y))


def chain(ov, a, b, sag=6, seed=0, broken=True, hot_end=True, sc=1.0):
    """Hanging chain of heavy links from a to b (b = free end), alternating flat / edge-on."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (4.2 * sc)))
    mid = add(lerp(a, b, 0.5), (0, sag))
    pts = [lerp(lerp(a, mid, t), lerp(mid, b, t), t) for t in [i / n for i in range(n + 1)]]
    for i in range(n):
        p0, p1 = pts[i], pts[i + 1]
        u = unit(p0, p1); v = perp(u)
        c = lerp(p0, p1, 0.5)
        if i % 2 == 0:    # flat ring
            for k in range(12):
                ang = k * math.pi / 6
                x = c[0] + u[0] * math.cos(ang) * 2.6 * sc + v[0] * math.sin(ang) * 1.6 * sc
                y = c[1] + u[1] * math.cos(ang) * 2.6 * sc + v[1] * math.sin(ang) * 1.6 * sc
                lit = (math.cos(ang) * u[0] + math.sin(ang) * v[0]) > 0.2 or (math.cos(ang) * u[1] + math.sin(ang) * v[1]) < -0.4
                ov.put(x, y, "I4" if lit else "I2")
        else:             # edge-on link
            for t in [q * sc for q in (-2.2, -1.1, 0, 1.1, 2.2)]:
                ov.put(c[0] + u[0] * t, c[1] + u[1] * t, "I3" if t < 1 else "I2")
            ov.put(c[0] + u[0] * -1.1 + 0.5, c[1] + u[1] * -1.1, "I5")
    if broken and hot_end:     # snapped last link, still glowing where it tore
        e = pts[-1]
        ov.put(e[0], e[1], "M5"); ov.put(e[0] + 1, e[1] + 1, "M3"); ov.put(e[0] - 1, e[1] + 1, "M4")


def lock_plate(ov, c):
    """Ashwright's gold lock: the maker's seal that binds the god."""
    x0, y0 = int(c[0]) - 3, int(c[1]) - 3
    PAT = ["  GGG  ", " G333G ", "G34443G", "G34m43G", "G34m43G", "G23332G", " G222G ", "  GGG  "]
    K = {"G": "G1", "2": "G2", "3": "G3", "4": "G4", "m": "M5"}
    for j, row in enumerate(PAT):
        for i, ch in enumerate(row):
            if ch != " ":
                ov.put(x0 + i, y0 + j - 1, K[ch])
    ov.put(x0 + 2, y0, "G5", ol=False)


def embers(ov, box, n, seed, hot=1.0):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x = rnd.uniform(x0, x1); y = rnd.uniform(y0, y1)
        r = rnd.random()
        k = "M7" if r < 0.15 * hot else "M6" if r < 0.4 else "M5" if r < 0.7 else "M3"
        ov.put(x, y, k, ol=False)
        if rnd.random() < 0.35:      # short rising streak
            ov.put(x - rnd.choice((0, 1)), y + 1, "M3" if k != "M3" else "M1", ol=False)


def ash(ov, box, n, seed):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        ov.put(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.choice(("A2", "A3", "A1", "A4")), ol=False)


def drip(ov, x, y, ln, seed=0, pool=False):
    """Hanging magma drip: hot stream, heavy bulb, a falling droplet below."""
    x, y = int(x), int(y)
    for k in range(ln):
        ov.put(x, y + k, "M5" if k < ln - 2 else "M6")
        if k < ln // 2:
            ov.put(x + 1, y + k, "M3")
    ov.put(x, y + ln, "M7"); ov.put(x + 1, y + ln, "M5"); ov.put(x - 1, y + ln, "M4"); ov.put(x, y + ln + 1, "M5")
    rnd = random.Random(seed)
    dy = y + ln + 4 + rnd.randint(0, 5)
    if dy < GROUND - 2:
        ov.put(x, dy, "M6"); ov.put(x, dy + 1, "M4")
    if pool:
        for dx in range(-4, 5):
            ov.put(x + dx, GROUND, "M4" if abs(dx) < 2 else "M2")
        ov.put(x, GROUND - 1, "M6"); ov.put(x - 1, GROUND - 1, "M4"); ov.put(x + 1, GROUND - 1, "M4")


class Fire:
    """Accumulates flame intensity, then colours it in clean bands (white core -> orange -> blood red).
    v3: low-frequency turbulence only, so the flame reads as big licking shapes instead of speckle."""
    def __init__(self):
        self.a = np.zeros((H, W))

    def cone(self, o, ang, length, spread, seed=0, power=1.0):
        d = (math.cos(ang), math.sin(ang))
        dx, dy = XC - o[0], YC - o[1]
        al = dx * d[0] + dy * d[1]
        pe = -dx * d[1] + dy * d[0]
        turb = vnoise(9.0, seed + 31) * 0.6 + vnoise(5.0, seed + 37) * 0.4
        t = np.clip(al / length, 0, 1)
        wob = 3.2 * np.sin(al * 0.11 + seed) * t + 1.6 * np.sin(al * 0.27 + seed * 2) * t
        bil = 7.0 * np.clip((t - 0.55) / 0.45, 0, 1) ** 1.5          # billows out at the end
        hw = 1.4 + al * math.tan(spread) * (0.85 + 0.3 * turb) + bil
        inside = (al > 0) & (al < length * (0.88 + 0.22 * turb))
        core = np.clip(1 - np.abs(pe - wob) / np.maximum(hw, 0.1), 0, 1) ** 0.8
        v = core * (1.22 - t * 0.8) + (turb - 0.5) * 0.4 * (0.3 + t)
        tail = np.clip((t - 0.7) / 0.3, 0, 1)
        v -= tail * np.clip(0.5 - turb, 0, 1) * 0.9 * (0.4 + 0.6 * (1 - core))                     # the end breaks into puffs
        v = np.where(inside, v, 0) * power
        self.a = np.maximum(self.a, np.clip(v, 0, 1.2))

    def tongue(self, base, hgt, w, seed=0, lean=0.0, power=1.0):
        bx, by = base
        for yy in range(int(hgt) + 1):
            t = yy / max(1, hgt)
            cx = bx + lean * yy + 2.0 * math.sin(yy * 0.3 + seed) * t ** 1.2 + 0.8 * math.sin(yy * 0.7 + seed * 2) * t
            ww = w * (1 - t) ** 0.85 * min(1.0, 0.55 + t * 3.0) + 0.35
            for x in range(int(cx - ww - 1), int(cx + ww + 2)):
                y = int(by - yy)
                if 0 <= x < W and 0 <= y < H:
                    v = max(0.0, 1 - abs(x + 0.5 - cx) / ww) ** 0.6 * (1.12 - t * 0.85) * power
                    self.a[y, x] = max(self.a[y, x], v)

    def to(self, ov):
        m = self.a > 0.12
        cl = ~dilate(~dilate(m, 3), 3)              # close pinholes inside the flame body
        self.a[cl & ~m] = 0.24
        for y, x in zip(*np.nonzero(self.a > 0.12)):
            v = self.a[y, x]
            k = "M7" if v > 0.9 else "M6" if v > 0.74 else "M5" if v > 0.58 else "M4" if v > 0.44 else \
                "M3" if v > 0.31 else "M2" if v > 0.2 else "M1"
            ov.put(x, y, k, ol=False)


def stream(ov, x, y0, y1, w=1.5, seed=0):
    """Magma pouring from a wound: thick at the lip, necking into drops, pooling on the ground."""
    rnd = random.Random(seed)
    L = y1 - y0
    brk = y0 + L * rnd.uniform(0.55, 0.75)        # the stream breaks into falling gobs here
    for y in range(int(y0), int(y1) + 1):
        t = (y - y0) / max(1, L)
        if y > brk and (y - int(brk)) % 7 not in (0, 1, 2):
            continue
        cx = x + math.sin(y * 0.25 + seed) * 0.9 * t
        ww = w * (1.2 - 0.6 * t)
        for xx in range(int(math.floor(cx - ww)), int(math.ceil(cx + ww)) + 1):
            d = abs(xx + 0.5 - cx) / max(ww, 0.5)
            if d > 1.15:
                continue
            ov.put(xx, y, "M7" if d < 0.3 and t < 0.4 else "M6" if d < 0.45 else "M5" if d < 0.8 else "M3", ol=False)
    if y1 >= GROUND - 2:
        for dx in range(-8, 9):
            k = "M5" if abs(dx) < 3 else "M4" if abs(dx) < 5 else "M2" if abs(dx) < 7 else "M1"
            ov.put(x + dx, GROUND, k, ol=False)
        for dx in range(-4, 5):
            ov.put(x + dx, GROUND - 1, "M6" if abs(dx) < 2 else "M3", ol=False)
        ov.put(x, GROUND - 2, "M7", ol=False); ov.put(x - 3, GROUND - 3, "M5", ol=False); ov.put(x + 4, GROUND - 4, "M4", ol=False)


def trickles(ov, fb, fig, n, seed, minheat=0.55, ymin=0, ymax=H):
    """Magma running down the body from wounds / veins, ending in a hanging drop."""
    rnd = random.Random(seed)
    hid = [i for i, g in enumerate(fb.groups) if g.name in ("head", "hammer", "cloth")]
    src = (fb.mat == MI["M"]) & (fb.heat > minheat)
    for i in hid:
        src &= fb.gid != i
    hot = [(x, y) for y, x in zip(*np.nonzero(src)) if ymin <= y < ymax]
    rnd.shuffle(hot)
    used = []
    for (x, y) in hot:
        if len(used) >= n:
            break
        if any(abs(x - a) < 7 and abs(y - b) < 10 for a, b in used):
            continue
        if not (y + 1 < H and fig[y + 1, x] and fb.mat[y + 1, x] != MI["M"]):
            continue
        used.append((x, y))
        ln = rnd.randint(5, 13)
        cx = x
        for k in range(1, ln + 1):
            yy = y + k
            if yy >= H or not fig[yy, cx]:
                ov.put(cx, yy, "M5", ol=False); ov.put(cx, yy + 1, "M6", ol=False)
                break
            ov.put(cx, yy, "M5" if k < ln - 1 else "M6", ol=False)
            if k < 3:
                ov.put(cx + 1, yy, "M3", ol=False)
            if rnd.random() < 0.15:
                cx += rnd.choice((-1, 1))
        else:
            ov.put(cx, y + ln + 1, "M7", ol=False); ov.put(cx - 1, y + ln, "M3", ol=False); ov.put(cx + 1, y + ln, "M3", ol=False)


def compose(img, ov, fig):
    pix = img.load()
    occ = {(x, y) for (x, y) in ov.outline}
    for (x, y) in ov.outline:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if q in ov.px or not (0 <= q[0] < W and 0 <= q[1] < H):
                continue
            k = ov.px[(x, y)]
            if k.startswith("I"):
                pix[q] = RGB["OUT"] + (255,)
    for (x, y), k in ov.px.items():
        pix[x, y] = RGB[k] + (255,)
    return img


# =========================================================================== poses
def make_T(lean, off=(0, 0)):
    return lambda q: add(rot(q, PV, lean), off)


def pose_windup():
    """Coiled: a deep sumo squat, the anvil-hammer hauled straight up over the crown with both hands."""
    p = dict(name="SLAM WINDUP", lean=-0.05, glow=1.2)
    T = make_T(p["lean"], (0, 15)); p["T"] = T
    p["Hd"] = T((137, 57)); p["head_ang"] = 0.14
    Sn, Sf = T((64, 60)), T((151, 61))
    u = (0.16, 0.99)
    Wn, Wf = (100, 51), (108, 42)
    p["arms"] = dict(near=(Sn, ik(Sn, Wn, 33, 30, (-1, -0.2)), Wn), far=(Sf, ik(Sf, Wf, 33, 30, (1, -0.6)), Wf))
    p["fist_near"] = (0.99, -0.16); p["fist_far"] = (0.99, -0.16)
    hn, hf = T((90, 112)), T((120, 110))
    an, af = (52, 163), (162, 163)
    p["legs"] = dict(near=(hn, ik(hn, an, 32, 25, (-1, -0.8)), an), far=(hf, ik(hf, af, 32, 25, (1, -0.8)), af))
    p["ham_grip"] = (106, 46); p["ham_ang"] = math.atan2(u[1], u[0]); p["ham_grip_d"] = 7; p["ham_len"] = 44
    p["ham_back"] = True; p["face_heat"] = 0.95; p["rune_heat"] = 0.85
    p["delt_shards_near"] = [((-3, -7), (-15, -24), 4.2), ((3, -10), (0, -25), 3.4), ((-10, -1), (-25, -9), 3.4)]
    p["delt_shards_far"] = [((2, -9), (8, -22), 3.2)]
    return p


def pose_roar():
    p = dict(name="HEART TORN OPEN - FIRE ROAR", lean=-0.15, glow=1.3, fissure=1.0, under=0.5)
    T = make_T(p["lean"]); p["T"] = T
    p["Hd"] = T((134, 55)); p["head_ang"] = -0.18; p["roar"] = 0.8
    Sn, Sf = T((64, 60)), T((151, 61))
    Wn, Wf = (24, 104), (184, 104)
    p["arms"] = dict(near=(Sn, ik(Sn, Wn, 33, 30, (-1, -0.6)), Wn), far=(Sf, ik(Sf, Wf, 33, 30, (1, -0.5)), Wf))
    p["fist_near"] = (-0.6, 0.8); p["fist_far"] = (0.5, 0.86)
    p["legs"] = dict(near=(T((90, 112)), (66, 140), (58, 163)), far=(T((120, 110)), (146, 138), (156, 163)))
    p["ham_c"] = (178, 175); p["ham_ang"] = math.atan2(-1, 0.14); p["ham_len"] = 60; p["ham_ground"] = True
    p["ham_before_torso"] = False
    p["delt_shards_near"] = [((-3, -7), (-15, -24), 4.2), ((3, -10), (0, -25), 3.4), ((-10, -1), (-25, -9), 3.4)]
    p["delt_shards_far"] = [((2, -9), (8, -22), 3.2)]
    return p


def pose_p2():
    p = pose_idle()
    p.update(name="PHASE 2 - THE SHELL BREAKS", lean=0.12, glow=1.0, under=0.45, shell=0.35, face_heat=1.0,
             rune_heat=0.95, fissure=0.35, p2=True)
    T = make_T(p["lean"]); p["T"] = T
    p["Hd"] = T((136, 55))
    p["arms"] = dict(near=(T((64, 60)), (44, 96), (38, 126)), far=(T((151, 61)), (174, 88), (188, 104)))
    p["legs"] = dict(near=(T((90, 112)), (66, 141), (56, 163)), far=(T((120, 110)), (146, 139), (156, 163)))
    p["ham_c"] = (180, 175)
    p["arms"]["far"] = (T((151, 61)), (172, 88), (182, 104))
    return p


def pose_idle():
    p = dict(name="IDLE", lean=0.13)
    T = make_T(p["lean"], (-3, 2))
    p["T"] = T
    p["Hd"] = T((137, 57))
    p["arms"] = dict(near=(T((64, 60)), (46, 94), (42, 122)), far=(T((151, 61)), (170, 86), (180, 102)))
    p["legs"] = dict(near=(T((90, 112)), (70, 140), (62, 163)), far=(T((120, 110)), (144, 138), (152, 163)))
    p["open_near"] = True; p["fist_near"] = (-0.12, 1.0)
    p["ham_c"] = (182, 175); p["ham_ang"] = math.atan2(-1, -0.06); p["ham_len"] = 66; p["ham_ground"] = True
    p["fist_far"] = (0.05, 1.0)
    p["delt_shards_near"] = [((-3, -7), (-15, -24), 4.2), ((3, -10), (0, -25), 3.4), ((-10, -1), (-25, -9), 3.4)]
    p["delt_shards_far"] = [((2, -9), (8, -22), 3.2)]
    return p


def build(p):
    fb = FB()
    sh = p.get("shell", 1.0)
    _put = fb.put
    def put(g):
        if g.name in ("torso", "armN", "armF", "legN", "legF"):
            g.shell = sh
        elif g.name == "head":
            g.shell = 1 - (1 - sh) * 0.3
        return _put(g)
    fb.put = put
    ln, lf = p["legs"]["near"], p["legs"]["far"]
    fb.put(leg_group("legF", *lf, "far", p))
    fb.put(leg_group("legN", *ln, "near", p))
    ham = None
    if p.get("ham_c") or p.get("ham_grip"):
        ham = hammer_group(p)
        if p.get("ham_back"):
            fb.put(ham)
    fb.put(shards_group(p))
    tg, heart = torso_group(p)
    if ham is not None and not p.get("ham_back") and p.get("ham_before_torso"):
        fb.put(ham)
    fb.put(tg)
    an, af = p["arms"]["near"], p["arms"]["far"]
    if ham is not None and not p.get("ham_back") and not p.get("ham_before_torso"):
        fb.put(ham)
    ga = arm_group("armF", *af, "far", p, fist_dir=p.get("fist_far"))
    fb.put(ga)
    fb.put(cloth_group(p))
    hg = head_group(p)
    fb.put(hg)
    gn = arm_group("armN", *an, "near", p, fist_dir=p.get("fist_near"), open_hand=p.get("open_near", False))
    fb.put(gn)
    if ham is not None and p.get("ham_front"):
        fb.put(ham)
    return fb, dict(heart=heart, armN=gn, armF=ga, head=hg)


def frame(p):
    fb, info = build(p)
    out, fig, warm = shade(fb, glow=p.get("glow", 1.0), under=p.get("under", 0.35))
    img = to_image(out, fig)
    ov = Overlay()
    trickles(ov, fb, fig, 7 if p.get("p2") else 3, 11, minheat=0.6 if p.get("p2") else 0.6, ymin=50)
    fire = Fire()
    for key, sag, ln in (("armN", 4, 34), ("armF", 3, 22)):
        g = info[key]
        cu, pf = g.cuff
        a = add(cu, mul(pf, -6 if key == "armN" else 7))
        dn = (0, ln)
        if p.get("open_near") and key == "armN":
            dn = (-7, ln * 0.75)            # swings clear of the talon hand
        if p["name"].startswith("SLAM"):
            dn = (-10 if key == "armN" else 6, ln * 0.8)
        if p["name"].startswith("HEART"):
            dn = (4 if key == "armN" else -3, ln)
        chain(ov, a, add(a, dn), sag=sag, seed=1)
    T = p["T"]
    chain(ov, T((84, 108.5)), T((126, 107)), sag=3.5, seed=2, broken=False, hot_end=False, sc=1.25)
    lock_plate(ov, T((106, 110.5)))
    hot = 1.0 + (0.6 if p.get("p2") else 0)
    embers(ov, (56, 14, 170, 50), int(26 * hot), 4)
    ash(ov, (46, 6, 184, 50), 18, 5)
    fn = info["armN"].fist
    drip(ov, fn[0] + 2, fn[1] + 7, 4, seed=1)
    if p["name"].startswith("HEART"):
        hd = p["Hd"]; a = p["head_ang"]
        mo = rot(add(hd, (9, 12)), hd, a)
        fire.cone(mo, -0.28, 110, 0.27, seed=3, power=1.15)
        hc = info["heart"]
        embers(ov, (hc[0] - 14, hc[1] - 22, hc[0] + 30, hc[1] + 10), 22, 21, hot=1.6)
        embers(ov, (120, 0, 224, 70), 40, 9, hot=1.5)
    if p.get("p2"):
        hd = p["Hd"]
        rnd = random.Random(7)
        for i in range(5):                          # the crown blazes: one merged, back-swept fire
            dx = -13 + i * 6.8 + rnd.uniform(-0.8, 0.8)
            hh = 12 + 16 * math.sin(math.pi * (i + 0.5) / 5) + rnd.uniform(-2, 2)
            fire.tongue(add(hd, (dx, -14 - (dx + 14) * 0.1)), hh, 6.6 + rnd.uniform(0, 1.0), seed=i * 5 + 1,
                        lean=-0.32, power=1.0)
        for i in range(4):                          # the tongues fuse into one blaze at the base
            dx = -9.6 + i * 6.8
            fire.tongue(add(hd, (dx, -13 - (dx + 14) * 0.1)), 7, 5.5, seed=90 + i, lean=-0.2, power=1.05)
        for i in range(3):                          # detached licks of flame
            q = add(hd, (-16 + i * 9 + rnd.uniform(-2, 2), rnd.uniform(-48, -40)))
            fire.tongue(q, rnd.uniform(4, 6), 1.4, seed=40 + i, lean=-0.3, power=0.75)
        fb2 = info
        fn, ff = info["armN"].fist, info["armF"].fist
        stream(ov, fn[0] - 2, fn[1] + 9, GROUND, 1.3, 1)
        drip(ov, 112, 84, 6, seed=3); drip(ov, 170, 118, 5, seed=4); drip(ov, 58, 110, 5, seed=5)
        embers(ov, (40, 30, 200, 120), 30, 13, hot=1.5)
    if p["name"].startswith("SLAM"):
        embers(ov, (20, 10, 80, 70), 18, 17, hot=1.2)
    fire.to(ov)
    img = compose(img, ov, fig)
    return img


# =========================================================================== sheet
BGC = (18, 12, 10, 255)


def player_img():
    pl = Image.open(os.path.join(ROOT, "assets", "player.png")).crop((0, 0, 64, 40))
    wp = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).crop((0, 0, 64, 40))
    c = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
    c.alpha_composite(pl); c.alpha_composite(wp)
    return c.transpose(Image.FLIP_LEFT_RIGHT)          # faces the boss


POSES = [pose_idle, pose_windup, pose_roar, pose_p2]


def main():
    from PIL import ImageDraw
    frames = [(f()["name"], frame(f())) for f in POSES]
    S, PAD, PL = 2, 14, 52
    cellw = [W + PL, W, W, W]
    rows = [[0, 1], [2, 3]]
    SW = PAD + sum(cellw[i] * S + PAD for i in rows[0])
    RH = H * S + 30
    sheet = Image.new("RGBA", (SW, 30 + RH * 2), BGC)
    dr = ImageDraw.Draw(sheet)
    dr.text((PAD, 9), "THE MOLTEN COLOSSUS  -  fallen forge-god of Ashwright   (concept v3, 224x176 frames @2x)",
            fill=(232, 190, 140, 255))
    raw = Image.new("RGBA", (W * len(frames), H), (0, 0, 0, 0))
    for ri, r in enumerate(rows):
        x = PAD
        y = 30 + ri * RH
        for i in r:
            name, im = frames[i]
            raw.alpha_composite(im, (i * W, 0))
            panel = Image.new("RGBA", (cellw[i], H), (0, 0, 0, 0))
            panel.alpha_composite(im, (0, 0))
            if i == 0:
                panel.alpha_composite(player_img(), (W + PL - 64 + 4, H - 40))
            fl = Image.new("RGBA", (cellw[i] * S, 2 * S), (40, 27, 22, 255))
            sheet.alpha_composite(fl, (x, y + 14 + H * S))
            sheet.alpha_composite(panel.resize((cellw[i] * S, H * S), Image.NEAREST), (x, y + 14))
            dr.text((x + 2, y), "%d  %s" % (i + 1, name), fill=(200, 160, 120, 255))
            x += cellw[i] * S + PAD
    sheet.save(os.path.join(HERE, "colossus.png"))
    raw.save(os.path.join(HERE, "colossus_1x.png"))
    print("wrote colossus.png", sheet.size)
    # closeup: crown + mask, roaring heart, talon hand, anvil-hammer, phase-2 torso  (@4x)
    Z = 4
    crops = [("CROWN + MASK", 0, (108, 16, 176, 80)), ("FIRE ROAR + TORN HEART", 2, (86, 22, 170, 86)),
             ("TALON HAND", 0, (20, 104, 76, 164)), ("ANVIL-HAMMER  (Ashwright's seal)", 0, (146, 116, 224, 176)),
             ("PHASE 2 - SHELL BURSTS", 3, (62, 30, 170, 96))]
    cw = sum((c[2][2] - c[2][0]) * Z + PAD for c in crops) + PAD
    ch = max((c[2][3] - c[2][1]) for c in crops) * Z + 30 + PAD
    cs = Image.new("RGBA", (cw, ch), BGC)
    dc = ImageDraw.Draw(cs)
    x = PAD
    for label, fi, (x0, y0, x1, y1) in crops:
        im = frames[fi][1].crop((x0, y0, x1, y1))
        bg = Image.new("RGBA", im.size, BGC); bg.alpha_composite(im)
        cs.alpha_composite(bg.resize(((x1 - x0) * Z, (y1 - y0) * Z), Image.NEAREST), (x, 24))
        dc.text((x + 2, 7), label, fill=(200, 160, 120, 255))
        x += (x1 - x0) * Z + PAD
    cs.save(os.path.join(HERE, "colossus_closeup.png"))
    print("wrote colossus_closeup.png", cs.size)


if __name__ == "__main__":
    main()
