#!/usr/bin/env python3
"""The Drowned Choir (agent B) -- a colossal serpentine leviathan of fused drowned corpses (user reference:
art/concepts/ref_drowned_choir.png): eel body, narrow skeletal fish head with needle teeth, a crest of screaming choir
faces along its back, teal glow in the eye and gills, dripping black water.

    python3 art/gen_barrows_choir.py            build every sheet (Aseprite) + previews
    python3 art/gen_barrows_choir.py --preview  previews only

Like the Pale Root's beast (art/gen_sovbeast.py) the body is assembled in the engine along a swimming spine. Every piece is
drawn once in its own local frame at 4x, then resampled at each heading with a majority vote (pixel-clean, no rotation
at runtime):

    choir_head        88x88, 17 headings (-90..90 deg, the engine mirrors leftward headings); tags closed / open
    choir_seg_RR      body capsule of radius RR (4..15), 17 headings; tags fill0 fill1 fill2 (fused-corpse variants), line
                      (1px dark silhouette drawn first for all pieces so the body shares one outline)
    choir_tail        56x56 ragged tail fin, 17 headings x 2 sway frames; tags t0 / t1
    choir_face        20x22 upright choir face that rides the crest; tags calm(2) hum(2) scream(3)
    choir_wraith      24x24 a face torn loose as a homing wraith (phase 2), tag fly(4)
    fx_db_bile        12x12 teal bile glob (tag fx_db_bile, 4 loop), fx_db_bileburst 32x24 splat (6, pivot bottom)
"""
import math, os, sys, random
from collections import Counter
import numpy as np
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

PV = os.path.join(ART, "previews")
os.makedirs(PV, exist_ok=True)

HEX = {
    "OUT": "#08070c",
    # drowned flesh (grey-green, cold)
    "F0": "#161e1c", "F1": "#28332f", "F2": "#44524b", "F3": "#687870", "F4": "#909f95", "F5": "#b9c4b8",
    # bone
    "B1": "#3c3b33", "B2": "#6d6a5b", "B3": "#a19b86", "B4": "#d6d0bb",
    # bruise / old blood
    "R1": "#2b1417", "R2": "#4e2427", "R3": "#6f3532",
    # teal glow
    "T1": "#0e3f3d", "T2": "#1d8279", "T3": "#39cfc0", "T4": "#98f2e3", "T5": "#e8fffa",
    # black water
    "K0": "#050708", "K1": "#0d1315",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
S = 4                      # local drawing scale
SEG_L = 9                  # spine spacing (px): the engine uses the same value
RADII = list(range(4, 16))
ANGS = [-90 + i * 11.25 for i in range(17)]


def blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


# ------------------------------------------------------------------ local canvases (drawn at 4x in u/v space, u forward, v down)
class Local:
    """a label canvas in local coordinates: u in [-R, R], v in [-R, R] at scale S"""
    def __init__(self, R):
        self.R = R
        self.n = 2 * R * S
        self.a = np.zeros((self.n, self.n), dtype=np.int16)   # 0 = empty, else palette index + 1
        uu = (np.arange(self.n) + 0.5) / S - R
        self.U, self.V = np.meshgrid(uu, uu)                   # U[row, col] = u of col, V = v of row

    def put(self, mask, col):
        self.a[mask] = KEYS.index(col) + 1

    def poly(self, pts):
        from matplotlib.path import Path
        p = Path(pts)
        return p.contains_points(np.stack([self.U.ravel(), self.V.ravel()], 1)).reshape(self.U.shape)

    def disc(self, cu, cv, r, ry=None):
        ry = ry or r
        return ((self.U - cu) / r) ** 2 + ((self.V - cv) / ry) ** 2 <= 1

    def seg(self, p0, p1, w):
        (u0, v0), (u1, v1) = p0, p1
        du, dv = u1 - u0, v1 - v0
        L2 = du * du + dv * dv or 1e-9
        t = np.clip(((self.U - u0) * du + (self.V - v0) * dv) / L2, 0, 1)
        return (self.U - (u0 + t * du)) ** 2 + (self.V - (v0 + t * dv)) ** 2 <= (w / 2) ** 2

    def polyline(self, pts, w):
        m = np.zeros_like(self.a, dtype=bool)
        for a, b in zip(pts, pts[1:]):
            m |= self.seg(a, b, w)
        return m


KEYS = list(HEX.keys())


def resample(loc, theta, F, cx=None, cy=None, flipv=False):
    """render a Local canvas rotated by theta (deg, screen heading) into an FxF RGBA image; majority vote of 4x4 samples"""
    cx = F / 2 if cx is None else cx
    cy = F / 2 if cy is None else cy
    ct, st = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    k = 4
    offs = (np.arange(k) + 0.5) / k
    xs = (np.arange(F)[:, None] + offs[None, :]).ravel()      # F*k
    X, Y = np.meshgrid(xs, xs)                                 # (F*k, F*k)
    dx, dy = X - cx, Y - cy
    u = dx * ct + dy * st
    v = -dx * st + dy * ct
    if flipv:
        v = -v
    ci = np.floor((u + loc.R) * S).astype(int)
    ri = np.floor((v + loc.R) * S).astype(int)
    ok = (ci >= 0) & (ri >= 0) & (ci < loc.n) & (ri < loc.n)
    lab = np.zeros(X.shape, dtype=np.int16)
    lab[ok] = loc.a[ri[ok], ci[ok]]
    lab = lab.reshape(F, k, F, k).transpose(0, 2, 1, 3).reshape(F, F, k * k)
    img = blank(F, F)
    px = img.load()
    for y in range(F):
        for x in range(F):
            s = lab[y, x]
            nz = s[s > 0]
            if len(nz) * 2 < len(s):
                continue
            c = Counter(nz.tolist()).most_common(1)[0][0]
            px[x, y] = RGBA[KEYS[c - 1]]
    return img


def outline(img, col="OUT", skip=None):
    w, h = img.size
    src = img.load()
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            if skip and skip(x, y):
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + a, y + b
                if 0 <= xx < w and 0 <= yy < h and src[xx, yy][3]:
                    op[x, y] = RGBA[col]
                    break
    return out


def hsh(x, y, k=0):
    n = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


# ================================================================== head
HEAD_F = 88
UPPER = [(-16, -9.5), (-10, -12.0), (-3, -14.0), (4, -14.2), (10, -12.6), (17, -10.4), (24, -8.2), (31, -6.0), (37, -3.8),
         (42, -1.8), (45, -0.2), (44, 0.9), (38, 1.0), (28, 1.2), (18, 1.6), (9, 2.2), (2, 3.2), (-6, 5.5), (-12, 8.0), (-16, 9.5)]
JAW = [(-5, 3.6), (6, 3.0), (16, 2.6), (27, 2.2), (37, 1.7), (43, 1.4), (41, 3.8), (33, 5.6), (22, 7.8), (10, 9.8), (0, 10.8), (-7, 10.2)]
HINGE = (-3.0, 3.5)


def rot_pts(pts, piv, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(piv[0] + (u - piv[0]) * c - (v - piv[1]) * s, piv[1] + (u - piv[0]) * s + (v - piv[1]) * c) for u, v in pts]


def head_local(open_):
    L = Local(44)
    U, V = L.U, L.V
    jaw_ang = 27 if open_ else 0
    jaw = rot_pts(JAW, HINGE, jaw_ang)
    up = L.poly(UPPER)
    jm = L.poly(jaw)
    # mouth cavity when open: between the upper jaw line and the rotated jaw
    if open_:
        cav = L.poly([(-4, 3.2), (43, 0.8)] + [jaw[4], jaw[3], jaw[2], jaw[1], jaw[0]]) & ~up
        L.put(cav, "K0")
        L.put(cav & ~L.poly([(-4, 4.6), (43, 2.2)] + [(q[0], q[1] - 1.4) for q in (jaw[4], jaw[3], jaw[2], jaw[1], jaw[0])]), "R1")
        L.put(cav & L.disc(0, 6, 8, 5), "T1")
        L.put(cav & L.disc(-2, 5.5, 4.5, 3), "T2")
    # lower jaw
    L.put(jm, "F3")
    jaw_lo = jm & ~L.poly(rot_pts([(-8, 2), (44, 1), (44, 3.6), (30, 5.2), (16, 6.8), (2, 8.6), (-8, 8.8)], HINGE, jaw_ang))
    L.put(jaw_lo, "F2")
    L.put(jm & L.polyline(rot_pts([(-5, 10.4), (10, 9.6), (22, 7.6), (33, 5.4), (41, 3.6)], HINGE, jaw_ang), 0.9), "F1")
    L.put(jm & L.disc(*rot_pts([(8, 7)], HINGE, jaw_ang)[0], 5, 2.2), "R2")
    # skull
    L.put(up, "F3")
    L.put(up & (V < -7.5 + (U + 16) * 0.12), "F4")
    L.put(up & (V > -2.5 + (U + 16) * 0.05), "F2")
    L.put(up & (V > 3.0) & (U < -4), "F1")
    top_edge = up & ~L.poly([(u, v + 1.3) for u, v in UPPER[:11]] + [(45, 3), (-16, 11)])
    L.put(top_edge & (U < 30), "F5")
    L.put(up & L.disc(4, -10.5, 7, 2.2), "B3")                                  # brow plate
    L.put(up & L.polyline([(-10, -9.5), (2, -11.5), (14, -9.8), (30, -6.0)], 0.7), "F2")   # skull ridge
    L.put(up & L.poly([(14, -1.2), (22, -3.4), (32, -3.2), (36, -1.6), (30, 0.2), (18, 0.6)]), "F1")   # cheek hollow
    L.put(up & L.poly([(20, -3.2), (31, -3.6), (29, -2.4), (21, -2.0)]), "F0")
    L.put(up & L.disc(38.5, -2.6, 1.6, 0.8), "F0")                              # nostril
    L.put(up & L.disc(-10, 2, 6, 5) & (V > 0), "R2")                           # bruised throat
    L.put(up & L.disc(-9, 3, 3, 2), "R3")
    # gills: glowing slats behind the eye
    for k, gu in enumerate((-10.5, -7.0, -3.5, 0.0)):
        pts = [(gu - 1.4, -5.0 + k * 0.4), (gu, -1.0), (gu + 0.6, 3.5), (gu - 0.6, 7.2 - k * 0.6)]
        L.put(up & L.polyline(pts, 1.9), "F0")
        L.put(up & L.polyline(pts[:3], 0.9), "T3" if k else "T2")
        L.put(up & L.polyline(pts[1:3], 0.5), "T4")
    # eye: socket, lens, core
    L.put(up & L.disc(10.5, -6.2, 4.6, 3.8), "F0")
    L.put(L.disc(10.5, -6.2, 3.3, 2.8), "T2")
    L.put(L.disc(10.8, -6.3, 2.4, 2.0), "T3")
    L.put(L.disc(11.2, -6.5, 1.3, 1.1), "T4")
    L.put(L.disc(11.5, -6.7, 0.6, 0.6), "T5")
    # backward spines on the crown
    for (u0, v0, du, dv) in ((4, -13.6, -9, -7), (-3, -13.4, -10, -6), (-10, -11.4, -9, -4.5)):
        tri = L.poly([(u0 + 2.2, v0 + 0.8), (u0 - 2.2, v0 + 1.2), (u0 + du, v0 + dv)])
        L.put(tri, "F1")
        L.put(tri & L.seg((u0 + 1.2, v0 + 0.4), (u0 + du * 0.7, v0 + dv * 0.7), 0.7), "F3")
    # needle teeth
    rnd = random.Random(7)
    for u in np.arange(5.0, 43.0, 2.3):
        base_v = 1.0 + (43 - u) * 0.012
        ln = 2.2 + rnd.random() * 1.2 + (3.4 if u > 34 else 0) + (1.6 if 20 < u < 24 else 0)
        L.put(L.poly([(u - 0.55, base_v - 0.3), (u + 0.55, base_v - 0.3), (u + 0.25, base_v + ln)]), "B4")
    for u in np.arange(6.2, 42.0, 2.3):
        ln = 2.0 + rnd.random() * 1.2 + (3.0 if u > 35 else 0)
        base = (u, 2.2 + (u / 43) * -0.6)
        tri = rot_pts([(u - 0.55, base[1] + 0.5), (u + 0.55, base[1] + 0.5), (u - 0.2, base[1] - ln)], HINGE, jaw_ang)
        L.put(L.poly(tri), "B3")
    # tattered skin hanging from the jaw (black water strands)
    for k, u in enumerate((2, 9, 17, 26)):
        p = rot_pts([(u, 9.6 - u * 0.12)], HINGE, jaw_ang)[0]
        L.put(L.seg(p, (p[0] - 1.5, p[1] + 3 + (k % 2) * 3), 0.8), "K1")
    return L


# ================================================================== body segments
NVAR = 5
VSEQ = [0, 3, 1, 4, 2, 3, 0, 1, 4, 2, 1, 3]   # the engine uses the same variant sequence along the spine


def seg_local(r, var):
    """one body capsule. Consecutive capsules overlap, so only a crescent band (s in -4.5..4.5, where
    s = u + r*sqrt(1-w^2)) of each shows: texture is authored in (s, w) so the bands read as a collage of fused bodies."""
    R = r + SEG_L // 2 + 4
    L = Local(R)
    U, V = L.U, L.V
    half = SEG_L / 2
    tt = np.clip(np.abs(U) - half, 0, None)
    d = np.sqrt(tt ** 2 + V ** 2)
    cap = d <= r
    w = np.clip(V / r, -1, 1)                       # -1 top (back) .. +1 belly
    sq = np.sqrt(np.clip(1 - w * w, 0, 1))
    s_ = U + r * sq                                 # crescent coordinate: the visible band is |s_| < 4.5
    rng = random.Random(r * 31 + var * 7)
    # base ramp: pale lit back, cold grey-green flank, dark belly
    L.put(cap, "F1")
    L.put(cap & (w < 0.42), "F2")
    L.put(cap & (w < -0.3), "F3")
    L.put(cap & (w < -0.72), "F4")
    L.put(cap & (w < -0.9), "F5" if r >= 6 else "F4")
    L.put(cap & (w > 0.78), "F0")
    # mottling: large soft blotches (a darker step), a few pale ones on the back
    cell = 3.2
    gi = np.floor((s_ + 40) / cell).astype(int)
    gj = np.floor((w * r + 40) / cell).astype(int)
    hv = np.vectorize(lambda a, b: hsh(a, b, var * 13 + r))(gi, gj)
    L.put(cap & (hv > 0.86) & (w > -0.3) & (w < 0.42), "F1")
    L.put(cap & (hv > 0.86) & (w >= 0.42), "F0")
    L.put(cap & (hv < 0.07) & (w < -0.3) & (w > -0.72), "F4")
    band = np.abs(U) < 4.8
    if r >= 7:
        if var == 0:      # a pale arm lying across the flank, the hand splayed toward the belly
            arm = [(-3.5, -0.62), (-1.0, -0.1), (1.6, 0.42), (2.4, 0.7)]
            pts = [(q[0], q[1] * r) for q in arm]
            m = np.zeros_like(cap)
            for (a0, a1) in zip(pts, pts[1:]):
                m |= L.seg(a0, a1, max(1.8, r * 0.22))
            m &= cap
            # map onto the crescent: shift by the band offset
            L.put(np.roll(m, 0) & band, "F4")
            L.put(L.polyline([(q[0] + 0.7, q[1] + 1.0) for q in pts], 0.7) & band & cap, "F1")
            for k in range(3):
                L.put(L.seg((pts[-1][0], pts[-1][1]), (pts[-1][0] - 1.2 + k * 1.2, pts[-1][1] + 2.2), 0.6) & cap, "F4")
        elif var == 1:    # ribs pressing through
            for k in range(3):
                u0 = -3 + k * 2.6
                L.put(cap & band & L.polyline([(u0, -0.15 * r), (u0 + 1.0, 0.2 * r), (u0 + 0.3, 0.5 * r)], 0.8), "F1")
                L.put(cap & band & L.polyline([(u0 - 0.7, -0.15 * r), (u0 + 0.3, 0.2 * r)], 0.5), "F4")
        elif var == 2:    # a drowned face sunk into the flank
            fu, fv = -0.5, -0.05 * r
            L.put(cap & L.disc(fu, fv, 2.9, 3.4), "F4")
            L.put(cap & L.disc(fu + 0.5, fv + 0.5, 2.9, 3.4) & ~L.disc(fu, fv, 2.9, 3.4), "F1")
            for sx in (-1, 1):
                L.put(cap & L.disc(fu + sx * 1.2, fv - 0.8, 0.65, 0.6), "F0")
            L.put(cap & L.disc(fu, fv + 1.6, 0.8, 1.0), "F0")
        elif var == 3:    # barnacle crust on the back, an old dark wound low on the flank
            for k in range(4):
                bu, bv = rng.uniform(-3.5, 3.5), -r * rng.uniform(0.5, 0.82)
                L.put(cap & L.disc(bu, bv, 1.05, 0.85), "B3")
                L.put(cap & L.disc(bu + 0.2, bv + 0.2, 0.45, 0.4), "B1")
            L.put(cap & L.disc(0.5, 0.45 * r, 2.8, 1.4), "R2")
            L.put(cap & L.disc(0.7, 0.5 * r, 1.4, 0.6), "R1")
        else:             # a shoulder/knee lump and a streak of black water down the belly
            L.put(cap & L.disc(-0.5, -0.3 * r, 3.4, 0.28 * r), "F4")
            L.put(cap & L.disc(0.3, -0.12 * r, 3.4, 0.22 * r) & ~L.disc(-0.5, -0.3 * r, 3.4, 0.28 * r), "F1")
            L.put(cap & L.seg((1.5, 0.35 * r), (2.0, r), 1.1), "K1")
        # dark bruising low on the flank (the reference's red patches), sparse
        if hsh(r, var, 5) < 0.45:
            L.put(cap & L.disc(rng.uniform(-3, 3), 0.62 * r, 1.8, 0.9), "R2")
        # dorsal spine: black, raked back
    elif r >= 5:
        L.put(cap & band & L.disc(0, -0.25 * r, 3.0, 0.3 * r), "F4")
        L.put(cap & band & L.disc(0.5, 0.2 * r, 3.2, 0.15 * r), "F1")
    # oily black water clinging to the belly
    L.put(cap & L.seg((-1 + var * 0.6, 0.8 * r), (-0.6 + var * 0.6, r), 0.9), "K1")
    # remap: features were authored around u = 0; slide them onto the visible crescent (u = s - r*sqrt(1-w^2))
    L2 = Local(R)
    src = L.a
    shift = np.round((r * sq) * S).astype(int)       # per-pixel column shift (depends on row only)
    rows, cols = np.indices(src.shape)
    sc = cols + shift
    ok = (sc >= 0) & (sc < src.shape[1])
    feat = np.zeros_like(src)
    feat[ok] = src[rows[ok], sc[ok]]
    base = L.a.copy()
    L2.a = np.where(cap, feat, 0).astype(np.int16)
    # anything the shift left empty inside the capsule gets the plain ramp
    L2.a = np.where(cap & (L2.a == 0), base, L2.a)
    line = Local(R)
    line.put(d <= r + 1.15, "OUT")
    return L2, line, 2 * R


def seg_frames(r):
    fills = {k: [] for k in range(NVAR)}
    lines = []
    F = None
    for var in range(NVAR):
        L, line, F = seg_local(r, var)
        for th in ANGS:
            fills[var].append(resample(L, th, F))
    _, line, F = seg_local(r, 0)
    for th in ANGS:
        lines.append(resample(line, th, F))
    return F, fills, lines


# ================================================================== tail fin
TAIL_F = 72


def tail_local(sway):
    L = Local(36)
    # ragged fin running back from the attach point, bone rays through a dark membrane
    top = [(0, -3), (8, -7 - sway), (17, -10 - sway * 1.5), (25, -9.5 - sway * 2), (31, -6 - sway * 2.4), (35, -1.5 - sway * 2.8)]
    bot = [(34, 2 - sway * 2.4), (29, 6 - sway * 1.9), (21, 9 - sway * 1.3), (12, 8 - sway * 0.6), (5, 4.5), (0, 2.5)]
    fin = L.poly(top + bot)
    L.put(fin, "F1")
    L.put(fin & (L.V < -2 - L.U * 0.1), "F2")
    for k, (eu, ev) in enumerate(((31, -7 - sway * 2.3), (34, -1 - sway * 2.6), (28, 5.5 - sway * 1.9), (18, 8 - sway))):
        L.put(fin & L.seg((0, 0), (eu, ev), 0.9), "B2")
        L.put(fin & L.seg((0, 0), (eu * 0.6, ev * 0.6), 0.5), "B3")
    # tears in the membrane
    for (cu, cv) in ((26, -5 - sway * 2), (17, 5.5 - sway), (32, 2 - sway * 2.5)):
        L.put(fin & L.disc(cu, cv, 2.2, 1.0), "K0")
    L.put(L.disc(0, 0, 3.4, 3.0), "F2")
    L.put(L.disc(0, -1, 2.0, 1.2), "F3")
    return L


# ================================================================== crest faces + wraiths (upright, drawn at 1x)
def face_img(expr, fr):
    """20x22 drowned choir face, front view, neck at the bottom blending into the body"""
    W_, H_ = 20, 22
    L = Local(11)            # 22x22 local
    U, V = L.U, L.V
    lean = (-0.5, 0.0, 0.5)[fr % 3] if expr != "calm" else (0.0, 0.3)[fr % 2]
    # neck + shoulders dissolving into the crest
    L.put(L.poly([(-5, 3), (5, 3), (7, 11), (-7, 11)]), "F2")
    L.put(L.poly([(-3, 3), (3, 3), (4, 11), (-4, 11)]) & (U < 0.5), "F3")
    # wet hair hanging at the sides
    L.put(L.disc(lean, -2.2, 6.8, 7.4) & ~L.disc(lean, 0.2, 5.3, 6.8), "K1")
    L.put(L.poly([(-6.8 + lean, -2), (-5 + lean, -2), (-4.2, 7), (-6.4, 6)]), "K1")
    L.put(L.poly([(6.8 + lean, -2), (5 + lean, -2), (4.2, 7), (6.4, 6)]), "K1")
    # skull-like face
    face = L.disc(lean, -0.8, 5.0, 6.3)
    L.put(face, "F4")
    L.put(face & (U > lean + 1.8), "F3")
    L.put(face & ~L.disc(lean - 0.6, -1.4, 4.4, 5.7), "F2")
    L.put(face & L.disc(lean - 1.4, -4.5, 2.4, 1.3), "F5")          # brow highlight
    for s in (-1, 1):                                                 # hollow cheeks
        L.put(face & L.disc(lean + s * 3.0, 1.8, 1.3, 2.2), "F2")
    # eye sockets
    glow = expr in ("scream", "hum")
    for s in (-1, 1):
        L.put(L.disc(lean + s * 2.1, -2.0, 1.45, 1.15), "F0")
    img = resample(L, 0, 22)
    img = img.crop((1, 0, 21, 22))
    px = img.load()
    cx = 10 + int(round(lean))

    def put(x, y, c):
        if 0 <= x < W_ and 0 <= y < H_:
            px[x, y] = RGBA[c]
    # eyes: dim teal points, bright when singing
    for s in (-1, 1):
        ex = cx + (s * 2 if s > 0 else -3)
        put(ex, 9, "T3" if glow else "T2")
        if expr == "scream":
            put(ex, 8, "T4")
    # mouth
    if expr == "calm":
        for x in range(cx - 1, cx + 1):
            put(x, 14, "F0")
        put(cx - 1, 15, "F1")
    elif expr == "hum":
        for y in range(13, 16):
            for x in range(cx - 1, cx + 1):
                put(x, y, "F0")
        put(cx - 1, 14, "T2")
        put(cx, 14, "T3" if fr % 2 else "T2")
    else:
        h = (3, 4, 5)[fr % 3]
        for y in range(12, 12 + h):
            wdt = 2 if y in (12, 11 + h) else 3
            for x in range(cx - wdt // 2 - 1, cx - wdt // 2 - 1 + wdt + 1):
                put(x, y, "F0")
        for y in range(13, 12 + h - 1):
            put(cx - 1, y, "T2")
            put(cx, y, "T3")
        put(cx, 13, "T4")
    img = outline(img)
    # soften the bottom: the neck sinks into the body (no outline along the bottom 3 rows)
    for y in range(H_ - 3, H_):
        for x in range(W_):
            if px[x, y][:3] == RGBA["OUT"][:3]:
                px[x, y] = (0, 0, 0, 0)
    return outline_fix(img)


def outline_fix(img):
    return img


def wraith_img(fr):
    W_ = 24
    img = blank(W_, W_)
    px = img.load()
    # teal wisp tail streaming left (FX: a few alpha steps allowed)
    for i in range(16):
        x = 12 - i
        yc = 12 + math.sin((i + fr * 2) * 0.55) * (i * 0.18)
        wdt = max(0.5, 4.2 - i * 0.25)
        for y in range(W_):
            d = abs(y + 0.5 - yc)
            if d <= wdt and 0 <= x < W_:
                a = int(200 * (1 - i / 17) * (1 if d < wdt * 0.5 else 0.6))
                c = RGBA["T3"] if d < wdt * 0.35 else RGBA["T2"]
                if a > 30:
                    px[x, y] = c[:3] + (a,)
    face = face_img("scream", fr % 3).resize((20, 22))
    face = face.crop((2, 1, 18, 17))            # just the head
    img.alpha_composite(face, (8, 4))
    px = img.load()
    for y in range(W_):
        for x in range(W_):
            p = px[x, y]
            if p[3] and p[:3] == RGBA["K1"][:3]:
                px[x, y] = RGBA["T1"]
    return img


# ================================================================== FX
def bile_img(fr):
    img = blank(12, 12)
    px = img.load()
    for y in range(12):
        for x in range(12):
            dx, dy = x + 0.5 - 6.5 + (fr % 2) * 0.3, y + 0.5 - 6
            r = math.hypot(dx * (1.0 if fr % 2 else 1.15), dy)
            if r <= 3.6:
                c = "T4" if r < 1.3 else "T3" if r < 2.4 else "T2"
                if dx > 1.4 and dy < -1:
                    c = "T5"
                px[x, y] = RGBA[c]
            elif r <= 4.6 and dx < 0 and hsh(x, y, fr) < 0.6:
                px[x, y] = RGBA["T2"][:3] + (170,)
    # trailing droplets (travelling right: they fall behind, to the left)
    for k in range(2):
        x, y = 1 + k * 2, 5 + ((fr + k) % 3)
        px[x, y] = RGBA["T3"][:3] + (200,)
    return img


def burst_img(fr):
    W_, H_ = 32, 24
    img = blank(W_, H_)
    px = img.load()
    rnd = random.Random(11)
    k = fr / 5
    for n in range(18):
        a = math.radians(rnd.uniform(200, 340))
        sp = rnd.uniform(6, 14)
        x = 16 + math.cos(a) * sp * k * 1.6
        y = H_ - 2 + math.sin(a) * sp * k * 1.9 + 9 * k * k
        if 0 <= x < W_ and 0 <= y < H_ and fr < 5:
            c = "T4" if n % 4 == 0 else "T3"
            px[int(x), int(y)] = RGBA[c]
            if fr < 3 and int(x) + 1 < W_:
                px[int(x) + 1, int(y)] = RGBA["T2"]
    # the splat on the surface
    wdt = int(4 + fr * 2.4)
    for x in range(16 - wdt, 16 + wdt):
        if 0 <= x < W_:
            for y in (H_ - 1, H_ - 2):
                if fr < 5 or hsh(x, y, fr) < 0.5:
                    px[x, H_ - 1] = RGBA["T2" if fr > 2 else "T3"]
    if fr < 3:
        for y in range(H_ - 6 - fr * 2, H_ - 1):
            for x in range(14 - fr, 18 + fr):
                if hsh(x, y, fr) < 0.5:
                    px[x, y] = RGBA["T3"][:3] + (180,)
    return img


# ================================================================== build
def mirror_ok():
    pass


def build(preview_only):
    heads = {}
    frames, tags = [], []
    for nm, op in (("closed", False), ("open", True)):
        L = head_local(op)
        a = len(frames)
        ims = []
        for th in ANGS:
            ct, st = math.cos(math.radians(th)), math.sin(math.radians(th))
            im = outline(resample(L, th, HEAD_F), skip=lambda x, y, ct=ct, st=st: (x + 0.5 - HEAD_F / 2) * ct + (y + 0.5 - HEAD_F / 2) * st < -13)
            ims.append(im)
            frames.append({"ms": 100, "cels": {"Head": im}})
        heads[nm] = ims
        tags.append((nm, a, len(frames) - 1))
    if not preview_only:
        asebuild.build("choir_head", HEAD_F, HEAD_F, ["Head"], frames, tags)
    segs = {}
    for r in RADII:
        F, fills, lines = seg_frames(r)
        segs[r] = (F, fills, lines)
        if not preview_only:
            fr, tg = [], []
            for nm, lst in [(f"fill{k}", fills[k]) for k in range(NVAR)] + [("line", lines)]:
                tg.append((nm, len(fr), len(fr) + len(lst) - 1))
                fr += [{"ms": 100, "cels": {"Body": im}} for im in lst]
            asebuild.build(f"choir_seg_{r:02d}", F, F, ["Body"], fr, tg)
    tails = {}
    frames, tags = [], []
    for k, sway in enumerate((0.0, 1.0)):
        L = tail_local(sway)
        a = len(frames)
        ims = [outline(resample(L, th, TAIL_F)) for th in ANGS]
        tails[k] = ims
        frames += [{"ms": 100, "cels": {"Tail": im}} for im in ims]
        tags.append((f"t{k}", a, len(frames) - 1))
    if not preview_only:
        asebuild.build("choir_tail", TAIL_F, TAIL_F, ["Tail"], frames, tags)
    faces = []
    frames, tags = [], []
    for nm, n, ms in (("calm", 2, 400), ("hum", 2, 220), ("scream", 3, 90)):
        a = len(frames)
        for i in range(n):
            im = face_img(nm, i)
            faces.append(im)
            frames.append({"ms": ms, "cels": {"Face": im}})
        tags.append((nm, a, len(frames) - 1))
    if not preview_only:
        asebuild.build("choir_face", 20, 22, ["Face"], frames, tags)
    wr = [wraith_img(i) for i in range(4)]
    if not preview_only:
        asebuild.build("choir_wraith", 24, 24, ["Wraith"], [{"ms": 90, "cels": {"Wraith": im}} for im in wr], [("fly", 0, 3)])
        asebuild.build("fx_db_bile", 12, 12, ["FX"], [{"ms": 80, "cels": {"FX": bile_img(i)}} for i in range(4)], [("fx_db_bile", 0, 3)])
        asebuild.build("fx_db_bileburst", 32, 24, ["FX"], [{"ms": 70, "cels": {"FX": burst_img(i)}} for i in range(6)], [("fx_db_bileburst", 0, 5)])
    preview(heads, segs, tails, faces, wr)


# ------------------------------------------------------------------ previews: every sheet + an assembled pose in the engine's manner
def sb_mirror(a):
    d = math.degrees(a)
    flip = math.cos(a) < 0
    if flip:
        d = 180 - d
    d = ((d + 180) % 360 + 360) % 360 - 180
    return min(range(17), key=lambda i: abs(ANGS[i] - d)), flip


def radius_profile(n=40):
    out = []
    for i in range(n):
        u = i / (n - 1)
        r = 8.5 + 6.5 * min(1, u / 0.28) ** 0.8
        if u > 0.42:
            r = 4 + (r - 4) * max(0.0, 1 - (u - 0.42) / 0.58) ** 0.9
        out.append(int(round(max(4, min(15, r)))))
    return out


def assemble(heads, segs, tails, faces, spine, mouth_open=False, face_expr=0):
    Wc, Hc = 520, 260
    img = Image.new("RGBA", (Wc, Hc), (26, 38, 40, 255))
    N = len(spine)
    rad = radius_profile(N)

    def paste(im, x, y, flip=False):
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        img.alpha_composite(im, (int(round(x - im.width / 2)), int(round(y - im.height / 2))))
    # faces behind body
    for pas in ("line", "fill"):
        for i in range(N - 2, -1, -1):
            p0, p1 = spine[i], spine[i + 1]
            a = math.atan2(p0[1] - p1[1], p0[0] - p1[0])
            fi, flip = sb_mirror(a)
            F, fills, lines = segs[rad[i]]
            im = lines[fi] if pas == "line" else fills[VSEQ[i % len(VSEQ)]][fi]
            paste(im, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, flip)
        if pas == "line":
            for i in range(3, 24, 2):
                p0, p1 = spine[i], spine[i + 1]
                a = math.atan2(p0[1] - p1[1], p0[0] - p1[0])
                nx, ny = math.sin(a), -math.cos(a)
                if math.cos(a) < 0:
                    nx, ny = -nx, -ny
                off = rad[i] * 0.85 + 5
                fim = faces[4 + (i % 3)] if face_expr else faces[i % 2]
                if i > 15:
                    fim = fim.resize((16, 18), Image.NEAREST)
                paste(fim, p0[0] + nx * off, p0[1] + ny * off - 2)
    a = math.atan2(spine[-1][1] - spine[-2][1], spine[-1][0] - spine[-2][0])
    fi, flip = sb_mirror(a)
    paste(tails[0][fi], spine[-1][0] + math.cos(a) * 0, spine[-1][1], flip)
    a = math.atan2(spine[0][1] - spine[1][1], spine[0][0] - spine[1][0])
    fi, flip = sb_mirror(a)
    paste(heads["open" if mouth_open else "closed"][fi], spine[0][0], spine[0][1], flip)
    return img


def preview(heads, segs, tails, faces, wr):
    rows = []
    for nm in ("closed", "open"):
        strip = Image.new("RGBA", (HEAD_F * 17, HEAD_F), (110, 110, 118, 255))
        for i, im in enumerate(heads[nm]):
            strip.alpha_composite(im, (i * HEAD_F, 0))
        rows.append(strip)
    for r in (6, 10, 15):
        F, fills, lines = segs[r]
        strip = Image.new("RGBA", (F * 17, F * 3), (110, 110, 118, 255))
        for v in range(3):
            for i in range(17):
                strip.alpha_composite(lines[i], (i * F, v * F))
                strip.alpha_composite(fills[v][i], (i * F, v * F))
        rows.append(strip)
    strip = Image.new("RGBA", (TAIL_F * 17, TAIL_F), (110, 110, 118, 255))
    for i, im in enumerate(tails[0]):
        strip.alpha_composite(im, (i * TAIL_F, 0))
    rows.append(strip)
    strip = Image.new("RGBA", (24 * 12, 24), (110, 110, 118, 255))
    for i, im in enumerate(faces):
        strip.alpha_composite(im, (i * 24, 1))
    for i, im in enumerate(wr):
        strip.alpha_composite(im, (7 * 24 + i * 24, 0))
    rows.append(strip)
    Wp = max(r.width for r in rows)
    Hp = sum(r.height + 4 for r in rows)
    sheet = Image.new("RGBA", (Wp, Hp), (70, 70, 78, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height + 4
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(os.path.join(PV, "choir_parts.png"))
    # assembled poses (the engine's spine solver, roughly): an S-curve like the reference, and a rearing wail pose
    def spine_curve(fn, n=40):
        pts = [fn(0)]
        t = 0.0
        while len(pts) < n:
            t += 0.002
            p = fn(t)
            if math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) >= SEG_L:
                pts.append(p)
        return pts
    s1 = spine_curve(lambda t: (430 - t * 330, 90 + math.sin(t * 7.5) * 40 + t * 30))
    s2 = spine_curve(lambda t: (300 - t * 60 + math.sin(t * 4) * 70, 60 + t * 190))
    a1 = assemble(heads, segs, tails, faces, s1, mouth_open=True, face_expr=1)
    a2 = assemble(heads, segs, tails, faces, s2, mouth_open=False, face_expr=0)
    both = Image.new("RGBA", (a1.width, a1.height * 2 + 4), (70, 70, 78, 255))
    both.alpha_composite(a1, (0, 0))
    both.alpha_composite(a2, (0, a1.height + 4))
    both.resize((both.width * 3, both.height * 3), Image.NEAREST).save(os.path.join(PV, "choir.png"))
    a1.crop((260, 20, 520, 170)).resize((260 * 4, 150 * 4), Image.NEAREST).save(os.path.join(PV, "choir_closeup.png"))


if __name__ == "__main__":
    build("--preview" in sys.argv)
