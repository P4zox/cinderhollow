"""CROWN OVERLOOK panorama (xrc_cr_panorama) for gen_xrc_crown.py.

512x216, one frame, horizontally tileable (period 512: every shape wraps). Transparent sky above
the horizon (~y 100) except for the Hallow's landmarks breaking through the cloud sea. Depth is
built from six rows of billowing cloud (far -> near: cooler, flatter, bluer -> warmer, brighter,
higher contrast), with the landmarks slotted between rows so each sinks into the right depth:

  x  18-122  the ruined Ashen Ramparts on their cliff (nearest landmark, between rows 1 and 2)
  x 142-206  the Sunken Cathedral's spires, drowned to the shoulders
  x 230-296  the storm-wrapped Tempest Spire with a fork of lightning
  x 318-382  the Burning Deep: a forge-red rift glowing up through the cloud, a rose smoke plume
  x 390-446  the Mire: a bank of dark green-grey mist with drowned dead trees
  x 452-506  the broken towers of the Archives

Sun shafts from the upper left lift the clouds in diagonal bands and gild their tops.
Clean hard bands; no noise textures.
"""
import math, random
import numpy as np
from xrc_crown_lib import hx, rp, in_poly

W, H = 512, 216
L3 = np.array([-0.55, -0.62, 0.56])
L3 = L3 / np.linalg.norm(L3)

CL = rp("727498", "84869e", "9698b8", "aaaac6", "bebcd0", "d0ccd8", "e0dbe0", "ede7e4", "f8f2ea", "fffcf4")
GLD = rp("e6cfa4", "f2dfb8", "fcecca", "fff8e2")
FAR = rp("8e92b4", "9ea0be", "aeaec8", "bebcd0", "cecad6", "dcd6dc")        # hazy landmark bodies
FRIM = rp("e8dccc", "f4e8d6", "fff6e6")                                     # sun rim on far shapes
STORM = rp("5a5e86", "686c92", "787ca0", "888cae", "9a9cbc", "b0b0cc")
BOLT = rp("fffef8", "f0ecff", "c8c0f4", "9890d8")
FORGE = rp("4a1414", "7a2218", "b03a1c", "e0642a", "ff9a40", "ffcc70", "fff0b0")
EMBERC = rp("c87a5c", "e0986c", "f0b684", "fad2a2")                         # red-lit cloud
MIRE = rp("3e4a46", "4c5a54", "5c6a62", "6e7c72", "84907e", "9aa494")


# per-row tone sets (lo, hi) -> the few CL indices actually used: flat shapes, no onion rings
TONES = {(5, 7): [5, 6, 7], (4, 8): [4, 6, 7, 8], (3, 8): [3, 5, 7, 8], (3, 9): [3, 5, 7, 9],
         (2, 9): [3, 5, 7, 8, 9]}


class Pano:
    def __init__(self):
        self.c = np.zeros((H, W, 4), np.uint8)
        ys, xs = np.mgrid[0:H, 0:W]
        self.X, self.Y = xs + 0.5, ys + 0.5

    def put(self, m, col):
        if isinstance(col, tuple) and len(col) == 2 and isinstance(col[0], list):
            r, idx = col
            arr = np.array(r, np.uint8)[np.clip(idx, 0, len(r) - 1)]
            self.c[m] = arr[m]
        else:
            self.c[m] = col

    def px(self, x, y, col):
        x, y = int(x) % W, int(y)
        if 0 <= y < H:
            self.c[y, x] = col


def wdx(X, cx):
    return (X - cx + W / 2) % W - W / 2


# ------------------------------------------------------------------ clouds
def cloud_row(p, base, rmin, rmax, seed, lo, hi, gold=0.0, tint=None, asp=0.6, und=(0.0, 1, 0.0),
              towers=(), step=(0.5, 0.85), fill=True):
    """A layer of billows. Each billow is a flattened ellipsoid lit from the upper left whose lower
    half sinks into shadow, so the crest of the next (nearer) layer always reads against shade.
    und = (amplitude, integer waves per 512, phase): large-scale undulation of the layer (tileable).
    towers = [(x, r_scale, lift)]: extra big billows that heap up out of the layer.
    lo/hi: CL index range. gold: how strongly sunlit crests gild."""
    rnd = random.Random(seed)
    A, K, PH = und

    def bl(x):
        return base + A * math.sin(2 * math.pi * K * x / W + PH)

    domes = []
    x = rnd.uniform(0, 6)
    while x < W - 2:
        r = rnd.uniform(rmin, rmax)
        domes.append((x, bl(x) - rnd.uniform(0.0, 0.35) * r * asp, r, asp * rnd.uniform(0.85, 1.15)))
        x += r * rnd.uniform(*step)
    for (tx, rs, lift) in towers:
        r = rmax * rs
        domes.append((tx, bl(tx) - lift, r, asp * 0.95))
        domes.append((tx - r * 0.55, bl(tx) - lift * 0.55, r * 0.7, asp))
        domes.append((tx + r * 0.6, bl(tx) - lift * 0.45, r * 0.65, asp))
    nubs = []
    for (cx, cy, r, a_) in domes:
        if r >= 11:
            for ang in (-150, -115, -80, -45):
                if rnd.random() < 0.7:
                    th = math.radians(ang + rnd.uniform(-12, 12))
                    rr = r * rnd.uniform(0.3, 0.42)
                    nubs.append((cx + math.cos(th) * r * 0.78, cy + math.sin(th) * r * a_ * 0.82, rr,
                                 a_ * 1.1))
    domes = domes + nubs
    X, Y = p.X, p.Y
    if fill:
        bm = Y >= np.array([[bl(x + 0.5) for x in range(W)]]) + rmin * asp * 0.4
        p.c[bm] = CL[lo]
    for (cx, cy, r, a_) in sorted(domes, key=lambda d: d[1]):
        ry = r * a_
        dx = wdx(X, cx)
        dy = Y - cy
        nx, ny = dx / r, dy / ry
        m = nx * nx + ny * ny <= 1
        if not m.any():
            continue
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        lam = nx * L3[0] + ny * 0.8 * L3[1] + nz * L3[2]
        v = np.clip(0.45 + 0.6 * lam - 0.55 * np.clip(ny + 0.1, 0, 1), 0, 0.999)
        tones = TONES.get((lo, hi))
        if tones is None:
            idx = lo + np.floor(v * (hi - lo + 1)).astype(int)
        else:
            idx = np.array(tones)[np.clip(np.floor(v * len(tones)).astype(int), 0, len(tones) - 1)]
        col = np.array(CL, np.uint8)[np.clip(idx, 0, len(CL) - 1)]
        if gold > 0:
            rim = (nx * nx + ny * ny > (1 - 1.4 / ry) ** 2) & (ny < -0.25) & (lam > 0.3)
            gi = np.clip((lam * gold * 4).astype(int), 0, 3)
            col = np.where(rim[..., None], np.array(GLD, np.uint8)[gi], col)
        if tint is not None:
            col = tint(X, Y, idx, col)
        p.c[m] = col[m]
    return domes


# ------------------------------------------------------------------ landmarks
def rim_light(p, m, body_col, rim_col, left_col=None):
    """1px rim on the sky-facing (top / left) edges of mask m."""
    up = np.roll(m, 1, axis=0)
    up[0] = False
    lf = np.roll(m, 1, axis=1)
    top = m & ~up
    left = m & ~lf & ~top
    p.put(top, rim_col)
    p.put(left, left_col if left_col is not None else rim_col)


def poly(p, pts):
    return in_poly(p.X, p.Y, pts)


ROCK = rp("5e6288", "6c7096", "7c80a4", "8e90b2", "a2a2c0", "b6b4ce")


def ramparts(p):
    """the Ashen Ramparts: a sheer faceted crag heaved out of the cloud sea, crowned with ruined
    crenellated curtain walls, a broken gatehouse keep and a turret; sun on the left faces"""
    X, Y = p.X, p.Y
    crag = [(14, 150), (20, 130), (23, 118), (28, 110), (30, 102), (35, 97), (37, 90), (42, 88), (48, 89),
            (53, 86), (60, 88), (66, 85), (73, 87), (80, 84), (88, 86), (95, 85), (100, 90), (104, 99),
            (108, 104), (111, 114), (116, 126), (122, 150)]
    cm = poly(p, crag)
    edges = [(27, 0.12), (36, -0.08), (49, 0.1), (63, -0.06), (78, 0.08), (92, -0.05), (104, 0.15)]
    fi = np.zeros(X.shape, int)
    for (e, sl) in edges:
        fi += (X + sl * (Y - 100) > e)
    lit = np.isin(fi, (0, 2, 5))
    ci = np.where(lit, 4, np.where(np.isin(fi, (1, 4)), 3, 2)) - (X > 100)
    ci = np.where(Y > 118, ci - 1, ci)
    p.put(cm, (ROCK, np.clip(ci, 0, 5)))
    for (y0, x0, x1) in ((100, 32, 58), (110, 60, 94), (118, 24, 44)):          # ledges
        p.put(cm & (np.abs(Y - y0 - 0.1 * (X - x0)) < 0.55) & (X > x0) & (X < x1), ROCK[4])
    rim_light(p, cm, None, FRIM[1], FRIM[0])
    # curtain walls with crenellations, a breach, a fallen section
    wall = (X >= 38) & (X <= 98) & (Y >= 79) & (Y <= 90) & ~poly(p, [(0, 150), (0, 0), (38, 0), (38, 150)])
    wall &= ~((X > 58) & (X < 67) & (Y < 85 + 0.5 * np.abs(X - 62.5)))
    wall &= ~((Y < 80) & (np.floor(X / 2.0).astype(int) % 2 == 1))
    keep = poly(p, [(38, 88), (38, 62), (40, 60), (41, 56), (43, 60), (45, 57), (47, 61), (50, 58), (52, 62),
                    (52, 88)])
    tur = poly(p, [(92, 88), (92, 70), (93.5, 66), (96, 60), (98.5, 66), (100, 70), (100, 88)])
    bm = wall | keep | tur
    shade = (keep & (X > 47)) | (tur & (X > 97)) | (wall & (X > 100))
    p.put(bm, (FAR, np.where(shade, 1, 3)))
    for (x, y) in ((42, 68), (46, 68), (42, 76), (95, 74), (96, 80), (75, 82), (84, 82)):
        p.px(x, y, ROCK[0])
        p.px(x, y + 1, ROCK[0])
    rim_light(p, bm, None, FRIM[2], FRIM[1])
    for k in range(5):                                         # tattered banner
        p.px(45 + k, 52 + (k % 2) + k // 3, ROCK[1])
    for y in range(52, 57):
        p.px(45, y, ROCK[0])


def cathedral(p):
    X, Y = p.X, p.Y
    body = poly(p, [(144, 112), (144, 98), (150, 94), (196, 94), (204, 98), (204, 112)])
    spires = [
        [(166, 112), (166, 76), (170, 70), (172, 56), (173.5, 44), (175, 56), (177, 70), (181, 76), (181, 112)],
        [(150, 112), (150, 86), (153, 80), (155, 68), (157, 80), (160, 86), (160, 112)],
        [(188, 112), (188, 86), (191, 80), (193, 70), (195, 80), (198, 86), (198, 112)],
    ]
    m = body.copy()
    for sp in spires:
        m |= poly(p, sp)
    # pinnacles
    for x in (147, 163, 184, 201):
        m |= poly(p, [(x - 1.2, 96), (x, 88), (x + 1.2, 96)])
    shade = (X > 176) & (X < 182) | (X > 157) & (X < 161) | (X > 195) & (X < 199)
    p.put(m, (FAR, np.where(shade, 2, 3)))
    # lancet windows, rose window catching the light
    for (x, y0, y1) in ((170, 80, 88), (175, 80, 88), (154, 90, 96), (193, 90, 96)):
        for y in range(y0, y1):
            p.px(x, y, FAR[1])
    for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        p.px(173 + dx, 96 + dy, FRIM[1] if dx or dy else FRIM[2])
    rim_light(p, m, None, FRIM[1], FRIM[0])


def tempest(p):
    """the Tempest Spire: a needle tower wound with rings of storm cloud (passing behind and in
    front of it) under a torn cap it pierces, a forked bolt dropping into the cloud sea"""
    X, Y = p.X, p.Y
    TX = 262
    dx = wdx(X, TX)
    tw = poly(p, [(TX - 3.5, 118), (TX - 3, 62), (TX - 4.5, 58), (TX - 2.5, 52), (TX - 1, 40), (TX, 26),
                  (TX + 1, 40), (TX + 2.5, 52), (TX + 4.5, 58), (TX + 3, 62), (TX + 3.5, 118)])
    # the storm: a thunderhead heaped behind the spire, rain curtains under its flat belly, one
    # churning ring of cloud wound round the spire's crown (back half behind, front half over it)
    def paint_domes(ds, shift=0, lo=0):
        for (cx, cy, r, asp) in sorted(ds, key=lambda d: d[1]):
            nx, ny = wdx(X, cx) / r, (Y - cy) / (r * asp)
            m = (nx * nx + ny * ny <= 1) & (Y <= 76)
            nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
            lam = nx * L3[0] + ny * 0.8 * L3[1] + nz * L3[2]
            v = np.clip(0.42 + 0.6 * lam - 0.5 * np.clip(ny + 0.1, 0, 1), 0, 0.999)
            p.put(m, (STORM, np.clip(lo + (v * (6 - lo)).astype(int) + shift, 0, 5)))

    rnd = random.Random(9)
    head = [(262, 62, 30, 0.5), (240, 66, 16, 0.55), (284, 65, 18, 0.5), (250, 52, 15, 0.6),
            (272, 50, 16, 0.6), (262, 42, 13, 0.6), (228, 70, 9, 0.6), (297, 70, 10, 0.55)]
    paint_domes(head, -1)
    hm = np.zeros(X.shape, bool)
    for (cx, cy, r, asp) in head:
        hm |= ((wdx(X, cx) / r) ** 2 + ((Y - cy) / (r * asp)) ** 2 <= 1) & (Y <= 76)
    p.put(hm & ~np.roll(hm, 1, axis=0) & (dx < 10), FRIM[0])
    belly = (np.abs(dx) < 34) & (Y >= 70) & (Y <= 76) & (p.c[..., 3] > 0)
    p.put(belly, STORM[0])
    # rain curtains
    for k in range(-30, 32, 3):
        x0 = TX + k
        L = int(22 + 10 * math.sin(k * 0.7))
        if abs(k) > 26 and k % 2:
            continue
        for j in range(L):
            if (j + k) % 7 < 5:
                p.px(x0 - j * 0.35, 77 + j, STORM[3] if j < L * 0.6 else STORM[4])
    p.put(tw, (FAR, np.where(dx > 1, 1, 3)))
    rim_light(p, tw, None, FRIM[1], FAR[4])
    ring = []
    n = 11
    for i in range(n):
        th = 2 * math.pi * i / n + 0.4
        rr = 6.5 + 2.5 * math.sin(th * 2 + 1)
        ring.append((TX + 24 * math.cos(th), 58 + 5 * math.sin(th) - rr * 0.2, rr, 0.55, math.sin(th) > 0))
    paint_domes([d[:4] for d in ring if not d[4]], -1)
    p.put(tw & (Y < 60), (FAR, np.where(dx > 1, 1, 3)))
    rim_light(p, tw & (Y < 60), None, FRIM[1], FAR[4])
    paint_domes([d[:4] for d in ring if d[4]], 0)
    p.px(TX, 26, BOLT[1])
    p.px(TX, 25, BOLT[2])
    for y in (84, 92, 100):                                     # slit windows below the storm
        p.px(TX - 1, y, FAR[0])
        p.px(TX - 1, y + 1, FAR[0])
    for y in range(106, 118):                                   # buttressed foot
        w_ = 3.5 + (y - 106) * 0.35
        for x in range(int(TX - w_), int(TX + w_) + 1):
            if not (TX - 3.5 <= x <= TX + 3.5):
                p.px(x, y, FAR[3] if x < TX else FAR[1])
    # lightning
    bolt = [(283, 74), (280, 81), (284, 86), (279, 94), (282, 99), (277, 110)]
    fork = [(280, 81), (274, 86), (271, 93)]
    fork2 = [(279, 94), (286, 100), (285, 106)]
    for path, core in ((bolt, BOLT[0]), (fork, BOLT[1]), (fork2, BOLT[1])):
        for i in range(len(path) - 1):
            (x0, y0), (x1, y1) = path[i], path[i + 1]
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                p.px(round(x) + 1, round(y), BOLT[2] if core == BOLT[0] else BOLT[3])
    for path, core in ((bolt, BOLT[0]), (fork, BOLT[1]), (fork2, BOLT[1])):
        for i in range(len(path) - 1):
            (x0, y0), (x1, y1) = path[i], path[i + 1]
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                p.px(round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), core)


def archives(p):
    X, Y = p.X, p.Y
    m = np.zeros((H, W), bool)
    towers = [(458, 6, 86, 0.0), (472, 9, 66, 0.0), (488, 7, 76, 0.08), (500, 5, 92, 0.0)]
    for (cx, hw, top, lean) in towers:
        xx = X - (cx + lean * (112 - Y))
        jag = top + 3 * np.abs(np.sin(xx * 1.3 + cx))           # broken, jagged top
        tm = (np.abs(xx) <= hw) & (Y >= jag) & (Y <= 116)
        m |= tm
    # broken bridge between towers 2 and 3
    br = (X >= 478) & (X <= 486) & (np.abs(Y - 84) <= 1) & ~((X > 482) & (X < 485))
    m |= br
    xx = X - 472
    shade = np.zeros((H, W), bool)
    for (cx, hw, top, lean) in towers:
        shade |= ((X - (cx + lean * (112 - Y))) > hw * 0.35) & ((X - (cx + lean * (112 - Y))) <= hw)
    p.put(m, (FAR, np.where(shade, 2, 3)))
    for (x, y) in ((470, 74), (474, 74), (470, 82), (474, 82), (486, 86), (458, 94), (500, 100)):
        p.px(x, y, FAR[1])
        p.px(x, y + 1, FAR[1])
    rim_light(p, m, None, FRIM[1], FRIM[0])


MISTC = rp("5a6862", "687670", "78867e", "8a968c", "9ea89c")


def mire(p):
    """the Mire: a long low bank of dark green-grey mist lying on the sea, drowned dead trees"""
    X, Y = p.X, p.Y
    dx = wdx(X, 416)
    rnd = random.Random(12)
    for (x0, hgt) in ((392, 14), (399, 20), (407, 26), (419, 17), (428, 23), (436, 15), (444, 11)):
        x, y = float(x0), 116.0
        for k in range(hgt):
            p.px(x, y - k, MISTC[0])
            if k < hgt * 0.4:
                p.px(x + 1, y - k, MISTC[1])
            x += rnd.uniform(-0.3, 0.3)
            if k in (int(hgt * 0.55), hgt - 3) and hgt > 12:
                sd = rnd.choice((-1, 1))
                for j in range(3 + (k < hgt - 3)):
                    p.px(x + sd * (j + 1), y - k - j * 0.8, MISTC[0])
    env = np.clip(1 - (dx / 40.0) ** 2, 0, 1)
    top = 113 - 6 * env ** 0.7 - 1.5 * np.abs(np.sin(X * 0.28)) * (env > 0.1)
    mm = (env > 0) & (Y >= top) & (Y < 128)
    mi = np.clip((1.2 + 0.28 * (Y - top) + 1.6 * (1 - env)).astype(int), 0, 4)
    p.put(mm, (MISTC, mi))
    p.put(mm & ~np.roll(mm, 1, axis=0), MISTC[4])
    for (x0, y0, L) in ((370, 113, 16), (452, 115, 14), (378, 119, 10), (446, 108, 9)):
        for k in range(L):
            p.px(x0 + k, y0 + (1 if k > L // 2 else 0), MISTC[3])


SMOKE = rp("a88c9c", "baa0ac", "ccb4ba", "dcc8c8", "eadad6")


def forge_rift(p, cy=150):
    """rose-grey smoke rising from the Burning Deep, leaning and thinning into a flat haze"""
    X, Y = p.X, p.Y
    FX = 350
    rnd = random.Random(7)
    puffs = [(0.0, 0, 3.2, 2.6), (0.14, 2, 4.0, 3.2), (0.27, -2, 4.6, 3.6), (0.4, 3, 5.6, 3.8),
             (0.53, 1, 7.0, 4.0), (0.66, 6, 8.0, 3.8), (0.8, 4, 10.0, 3.6), (0.93, 10, 12.0, 3.2)]
    for (t, ox, rx, ry) in puffs:
        cx = FX + 3 + 18 * t ** 1.6 + ox
        cyk = 132 - 46 * t
        m = (wdx(X, cx) / rx) ** 2 + ((Y - cyk) / ry) ** 2 <= 1
        nx, ny = wdx(X, cx) / rx, (Y - cyk) / ry
        v = np.clip(0.35 - 0.3 * nx - 0.35 * ny + 0.55 * t, 0, 0.999)
        si = (v * 5).astype(int)
        col = np.array(SMOKE, np.uint8)[np.clip(si, 0, 4)]
        belly = (ny > 0.3) & (t < 0.5)
        col = np.where(belly[..., None], np.array(EMBERC[1], np.uint8), col)
        p.c[m] = col[m]
    return None


def forge_tint_fn(FX=350, cy=150, rad=46.0):
    def tint(X, Y, idx, col):
        d = np.hypot(wdx(X, FX) / rad, (Y - cy) / (rad * 0.5))
        k = np.clip(1 - d, 0, 1)
        # undersides (low idx) near the rift glow red; tops pick up rose
        e = ((k > 0.2) & (idx <= 6)) | ((k > 0.55) & (idx <= 7))
        ei = np.clip((k * 4).astype(int), 0, 3)
        col = np.where(e[..., None], np.array(EMBERC, np.uint8)[ei], col)
        e2 = (k > 0.6) & (idx <= 3)
        col = np.where(e2[..., None], np.array(FORGE, np.uint8)[np.clip((k * 7).astype(int) - 1, 3, 5)], col)
        return col
    return tint


def rift_glow(p, FX=350, cy=147):
    X, Y = p.X, p.Y
    dx = wdx(X, FX)
    # the rift: a lens-shaped gap between billows, glowing from deep below
    hw = 30 * np.clip(1 - ((Y - cy) / 6.0) ** 2, 0, 1) ** 0.6 * (1 + 0.12 * np.sin(X * 0.5))
    m = (np.abs(dx) < hw) & (np.abs(Y - cy) < 6)
    k = 1 - np.abs(dx) / np.maximum(hw, 0.5)
    fi = np.clip((k * 5.5 + (Y - cy + 7) * 0.12).astype(int), 0, 6)
    p.put(m, (FORGE, fi))
    # embers drifting up out of it
    rnd = random.Random(4)
    for _ in range(14):
        x = FX + rnd.uniform(-16, 16)
        y = cy - rnd.uniform(3, 30)
        p.px(x, y, FORGE[rnd.choice((4, 5, 5, 6))])


# ------------------------------------------------------------------ sun shafts
def shafts(p, y0=104):
    X, Y = p.X, p.Y
    ph = (X + (Y - y0) * 0.6) % 256
    beam = (((ph > 20) & (ph < 46)) | ((ph > 150) & (ph < 162))) & (Y > y0)
    return beam


def build_panorama():
    p = Pano()
    X, Y = p.X, p.Y
    # far haze streaks just above the horizon (thin, broken)
    for (y, seed) in ((97, 1), (100, 2), (103, 3)):
        rnd = random.Random(seed)
        x = 0.0
        while x < W:
            L = rnd.uniform(10, 40)
            if rnd.random() < 0.55:
                for k in range(int(L)):
                    p.px(x + k, y, CL[7] if y < 100 else CL[6])
            x += L + rnd.uniform(6, 30)
    # row 0: the horizon, flat, cool, low contrast; a few far cumulus heads
    cloud_row(p, 111, 7, 13, 10, 5, 7, asp=0.32, towers=((120, 1.2, 5), (330, 1.4, 6), (480, 1.0, 4)))
    archives(p)
    cathedral(p)
    tempest(p)
    # row 1
    cloud_row(p, 118, 9, 16, 11, 4, 8, gold=0.3, asp=0.42, und=(2.0, 3, 0.5), towers=((212, 1.3, 7),))
    mire(p)
    # row 2 (the crag rises out of it; the rift sits in it)
    cloud_row(p, 129, 12, 22, 12, 3, 8, gold=0.5, tint=forge_tint_fn(cy=140, rad=52), asp=0.5,
              und=(3.0, 2, 1.7), towers=((440, 1.2, 8),))
    ramparts(p)
    cloud_row(p, 140, 12, 24, 16, 3, 9, gold=0.6, tint=forge_tint_fn(cy=142, rad=46), asp=0.5,
              und=(3.0, 3, 0.2), towers=((180, 1.3, 9),))
    forge_rift(p)
    rift_glow(p, cy=137)
    # row 3
    cloud_row(p, 156, 18, 30, 13, 2, 9, gold=0.7, tint=forge_tint_fn(cy=146, rad=30), asp=0.52,
              und=(4.0, 2, 3.1), towers=((64, 1.3, 12), (300, 1.1, 8)))
    # row 4
    cloud_row(p, 180, 24, 40, 14, 2, 9, gold=0.9, asp=0.52, und=(5.0, 1, 0.9), towers=((410, 1.2, 14),))
    # row 5: foreground billows, brightest
    cloud_row(p, 210, 32, 52, 15, 2, 9, gold=1.0, asp=0.5, und=(4.0, 2, 2.2), towers=((150, 1.1, 10),))
    # sun shafts: lift clouds inside diagonal beams by one step
    beam = shafts(p) & (p.c[..., 3] > 0)
    cl = np.array(CL, np.uint8)
    for i in range(len(CL) - 2, 4, -1):
        mm = beam & np.all(p.c == cl[i], axis=-1)
        p.c[mm] = cl[i + 1]
    top_lit = beam & (np.all(p.c == cl[9], axis=-1) | np.all(p.c == cl[8], axis=-1))
    p.c[top_lit & np.all(p.c == cl[9], axis=-1)] = GLD[3]
    # motes of light above the sea
    rnd = random.Random(21)
    for _ in range(36):
        x, y = rnd.randrange(W), rnd.randrange(112, 210)
        if p.c[y, x, 3]:
            p.px(x, y, GLD[3])
    return p.c


def panorama():
    from PIL import Image
    img = Image.fromarray(build_panorama(), "RGBA")
    return W, H, ["Vista"], [{"ms": 1000, "cels": {"Vista": img}}], [("idle", 0, 0)]
