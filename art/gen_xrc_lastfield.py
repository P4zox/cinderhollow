#!/usr/bin/env python3
"""THE LAST FIELD (agent RC, Expansion 3): a golden wheat field at sunset behind the Stormspire, Cindervane's nest.

Builds (all through asebuild -> Aseprite):
  xrc_lf_sky    512x216 opaque   : dusk gradient (indigo -> rose -> gold), the low sun with its halo, first stars
  xrc_lf_clouds 512x216 alpha    : long bands of cloud, violet tops, undersides burning gold/rose (engine drifts it)
  xrc_lf_far    512x216 alpha    : far blue-violet hills in haze, a thin line of the storm far off on one edge
  xrc_lf_mid    512x216 alpha    : nearer rolling fields, hedgerows, lone trees, a ruined watch-tower
  xrc_lf_near   512x216 alpha    : the near wheat and hedge in shadow with gold rim light (the lowest band)
  tiles_lastfield 48 x 16x16     : dark loam, golden stubble tops, roots and field-stones (standard 48-index layout)
  xrc_lf_nest (80x32) xrc_lf_egg (16x20: glow 6, gone 1) xrc_lf_stone (32x48) xrc_lf_tree (112x176)
  xrc_lf_stones (48x32) xrc_lf_fence (48x24) xrc_lf_plough (40x24)
Preview -> art/previews/xrc_lf_preview.png (a mock of the room at 3x) and xrc_lf_parts.png.
Usage: python3 art/gen_xrc_lastfield.py [--no-ase]
"""
import math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from envlib import C, ramp, T, K, bt, pick, pick_i, h01, vnoise, fbm, smooth, clamp, lerpc, Canvas, outline, blank, scale  # noqa: E402

W, H = 512, 216
HZ = 124                                   # horizon line in the sky layer
SUNX, SUNY, SUNR = 356, 100, 16            # the low sun (sky layer coords)

SKY = ramp("140f2a", "1b1433", "241a42", "30204f", "3e265a", "4f2b62", "633068", "7a376a", "92406a", "aa4b68",
           "c05864", "d2685e", "e07a58", "ea8e56", "f2a257", "f8b85e", "fcca6a", "ffda7e", "ffe79a", "fff2c0")
NS = len(SKY)
CLOUD = ramp("2a1d44", "3a2552", "4c2d5c", "5f3462", "733c66", "8a4666", "a25264", "b86060", "cc725a", "de8856",
             "eca058", "f6ba62", "fcd27a", "ffe6a4")
FAR = ramp("2f2248", "3a2a55", "46315f", "533868", "613f6e", "704673", "7e4d74", "8d5572", "9c5d70", "ab676c")
MID = ramp("1c1224", "24172c", "2d1c33", "37213a", "422740", "4f2e45", "5d3548", "6b3d48", "7a4646", "8a5044")
GOLD = ramp("3a2418", "5a3620", "7c4c26", "9e642c", "bf7e34", "d99a40", "ecb652", "f7d06c", "ffe490")
NEAR = ramp("140a12", "1c1018", "25151c", "2f1b20", "3a2224", "472a26")
LOAM = ramp("120a0c", "1a0f10", "241512", "2e1b15", "3a2218", "48291c", "573220", "683c26")
STONE = ramp("1a1418", "2a2026", "3b2e32", "4e3e40", "65524f", "7e6a62", "9a8474")
EMBER = ramp("3a0a06", "6e1a0a", "a8340e", "dc5a16", "f88a2a", "ffc05a", "fff0b0")
SLATE = ramp("0c0b10", "15141c", "1f1d28", "2b2936", "3a3746", "4b4858", "5e5b6c")


def tn(x, y, sx, sy, seed):
    """tileable (x wraps at W) smooth value noise"""
    return vnoise(x % W, y, sx, sy, seed, W // sx if W % sx == 0 else None)


# ============================================================================ sky
def build_sky():
    c = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            # the gradient bows up around the sun: warm light pools there
            dx = ((x - SUNX + W / 2) % W) - W / 2
            d = math.hypot(dx * 0.55, (y - SUNY) * 1.0)
            v = y / HZ
            v = v ** 1.18
            warm = math.exp(-d / 95.0) * 0.30 + math.exp(-d / 38.0) * 0.18
            v = clamp(v * 0.92 + warm)
            if y > HZ: v = clamp(0.93 + (y - HZ) / 400)
            c.set(x, y, pick(SKY, v, x, y))
    # first stars, only high up where it's already night
    for i in range(70):
        x, y = int(h01(i, 1, 51) * W), int(h01(i, 2, 51) * 70)
        if y < 62 * (0.4 + h01(i, 3, 51)):
            c.set(x, y, C("d8d0f0") if h01(i, 4, 51) < 0.3 else C("8c80b8"))
    # the sun: a pale disc with a soft two-step halo and horizontal heat-shimmer bands
    for y in range(SUNY - SUNR - 14, SUNY + SUNR + 14):
        for x in range(SUNX - SUNR - 22, SUNX + SUNR + 22):
            d = math.hypot((x - SUNX) * 0.95, y - SUNY)
            if d <= SUNR:
                band = (y - SUNY) > 7 and ((y - SUNY) % 4 == 0)          # the lower disc melts into horizontal slivers
                if band: continue
                t = d / SUNR
                c.set(x, y, C("fff8e2") if t < 0.72 else C("ffeebc") if t < 0.9 else C("ffe09a"))
            elif d <= SUNR + 3 and bt(x, y) < 0.65:
                c.set(x, y, C("ffe8a8"))
            elif d <= SUNR + 8 and bt(x, y) < 0.3:
                c.set(x, y, C("ffd88a"))
    return c.img


# ============================================================================ clouds (long lenses, lit from below by the low sun)
def lens_list():
    L, i = [], 0
    rows = [(22, 2, 0.10), (40, 2, 0.22), (57, 3, 0.36), (72, 3, 0.52), (86, 2, 0.68), (109, 2, 0.84)]
    for y0, n, tone in rows:
        for k in range(n):
            i += 1
            L.append(dict(cx=(k + h01(i, 1, 71) * 0.8) * W / n, cy=y0 + (h01(i, 2, 71) - 0.5) * 8,
                          hl=40 + h01(i, 3, 71) * (60 + y0 * 0.5), th=2.5 + h01(i, 4, 71) * (2.5 + y0 / 26), tone=tone, s=i))
    return L


def build_clouds():
    c = Canvas(W, H, wrap=True)
    for q in lens_list():
        x0, x1 = int(q['cx'] - q['hl'] - 2), int(q['cx'] + q['hl'] + 2)
        for x in range(x0, x1):
            dx = (x - q['cx']) / q['hl']
            if abs(dx) >= 1: continue
            prof = math.sqrt(1 - dx * dx) * (0.75 + 0.5 * tn(x, q['s'], 32, 1, 72 + q['s']))
            top = q['cy'] - q['th'] * 1.7 * prof            # rolling top, flat lit underside
            bot = q['cy'] + q['th'] * 0.45 * prof
            if bot - top < 0.8: continue
            for y in range(int(top), int(bot) + 1):
                u = (y - top) / max(1.0, bot - top)
                edge = min(abs(dx) * 1.0, 1.0)
                if edge > 0.9 and bt(x, y) < (edge - 0.9) / 0.1: continue          # dithered tips
                sdx = ((x - SUNX + W / 2) % W) - W / 2
                if math.hypot(sdx, y - SUNY) < SUNR + 4: continue                       # the sun burns a clear hole
                sunk = math.exp(-abs(sdx) / 170.0) * (0.5 + 0.5 * q['tone'])
                v = q['tone'] * 0.5 + u * (0.22 + 0.5 * sunk) + 0.06 * tn(x, y, 16, 4, 73)
                if y >= int(bot) - 0: v += 0.10 + 0.12 * sunk                        # burning rim underneath
                c.set(x, y, pick(CLOUD, clamp(v), x, y))
    return c.img


# ============================================================================ far hills (blue-violet, hazed toward the horizon glow)
def ridge(x, base, amp, per, seed):
    return base - amp * (0.55 * tn(x, 0, per, 1, seed) + 0.3 * tn(x, 0, per // 2, 1, seed + 1) + 0.15 * tn(x, 0, per // 4, 1, seed + 2))


def build_far():
    c = Canvas(W, H, wrap=True)
    layers = [dict(base=124, amp=30, per=256, seed=31, tone=0.64), dict(base=132, amp=22, per=128, seed=37, tone=0.46),
              dict(base=142, amp=16, per=128, seed=41, tone=0.30)]
    for L in layers:
        for x in range(W):
            top = ridge(x, L["base"], L["amp"], L["per"], L["seed"])
            sdx = ((x - SUNX + W / 2) % W) - W / 2
            top += 12 * math.exp(-(sdx / 60.0) ** 2)                   # the land dips where the sun is going down
            for y in range(int(top), H):
                depth = (y - top) / 50.0
                v = L["tone"] - 0.10 * clamp(depth)
                dx = ((x - SUNX + W / 2) % W) - W / 2
                if y - top < 2: v += 0.18 * math.exp(-abs(dx) / 130.0) + 0.05     # rim of sunset on each crest
                c.set(x, y, pick(FAR, clamp(v), x, y))
    # the storm, very far: a bruise of cloud over the west, and the thin needle of the Stormspire under it
    sx = 70
    for y in range(96, 122):
        w = 0 if y < 104 else 1
        for x in range(sx - w, sx + w + 1): c.set(x, y, FAR[1])
    c.set(sx, 95, C("b8c8f8"))
    return c.img


# ============================================================================ mid: rolling fields, hedgerows, lone trees, a ruined tower
def tree(c, x0, base, h, seed, col):
    """a lone field tree, windswept, in silhouette: a short bent trunk and a leaning, lobed crown"""
    for y in range(base - int(h * 0.55), base + 1):
        w = 0 if y < base - h * 0.3 else 1
        lean = (base - y) * 0.12
        for x in range(int(x0 - w + lean), int(x0 + w + lean) + 1): c.set(x, y, col)
    cx, cy = x0 + h * 0.22, base - h * 0.7
    for k in range(5):
        lx = cx + (k - 2) * h * 0.16 + (h01(k, seed, 5) - 0.5) * 3
        ly = cy + abs(k - 2) * h * 0.08 + (h01(k, seed, 6) - 0.5) * 2
        rx, ry = h * (0.2 + 0.08 * h01(k, seed, 7)), h * (0.16 + 0.05 * h01(k, seed, 8))
        for y in range(int(ly - ry) - 1, int(ly + ry) + 2):
            for x in range(int(lx - rx) - 1, int(lx + rx) + 2):
                if ((x - lx) / rx) ** 2 + ((y - ly) / ry) ** 2 <= 1: c.set(x, y, col)


def build_mid():
    c = Canvas(W, H, wrap=True)
    tops = [0] * W
    for x in range(W):
        tops[x] = ridge(x, 142, 20, 256, 61)
        for y in range(int(tops[x]), H):
            d = y - tops[x]
            v = 0.62 - 0.35 * clamp(d / 40)
            # strip fields: bands of gold stubble on the sunlit slopes
            f = tn(x, y, 32, 8, 63)
            if 3 < d < 30 and f > 0.58:
                g = pick_i(len(GOLD), 0.25 + 0.3 * (f - 0.58) / 0.42 - d / 120, x, y)
                c.set(x, y, GOLD[max(0, min(3, g))])
                continue
            dx = ((x - SUNX + W / 2) % W) - W / 2
            if d < 2: v += 0.25 + 0.1 * math.exp(-abs(dx) / 120.0)
            c.set(x, y, pick(MID, clamp(v), x, y))
    # hedgerows following the slope
    for x in range(W):
        if tn(x, 3, 16, 1, 67) > 0.62:
            for y in range(int(tops[x]) - 2, int(tops[x]) + 1): c.set(x, y, MID[2])
    for i, (tx, h) in enumerate([(30, 22), (118, 16), (206, 26), (292, 14), (420, 20), (466, 12)]):
        tree(c, tx, int(tops[tx % W]) + 1, h, i + 1, MID[1])
        for k in range(-1, 2): c.set(tx + k + int(h * 0.18), int(tops[tx % W]) - h - 1, MID[5])   # a sunlit edge on the crown
    # a ruined watch-tower on a far rise (someone kept this field, once)
    tx = 250; tb = int(tops[tx])
    for y in range(tb - 34, tb + 1):
        w = 4 if y > tb - 26 else 3
        for x in range(tx - w, tx + w + 1):
            broken = y < tb - 30 and (x - tx) > (tb - 30 - y) * 1.2 - 1
            if not broken: c.set(x, y, MID[1] if x < tx + 2 else MID[3])
    for y in range(tb - 22, tb - 18): c.set(tx, y, C("f6c070"))    # a slit window catching the sun
    return c.img


# ============================================================================ near: wheat and hedge in shadow, gold rim light
def build_near():
    c = Canvas(W, H, wrap=True)
    for x in range(W):
        top = 146 - 8 * tn(x, 0, 64, 1, 81) - 4 * tn(x, 0, 16, 1, 82)
        for y in range(int(top), H):
            c.set(x, y, pick(NEAR, 0.55 - clamp((y - top) / 30) * 0.4, x, y))
        # wheat heads along the crest, bending east
        if h01(x, 1, 83) < 0.55:
            h = 3 + int(h01(x, 2, 83) * 6)
            for k in range(h):
                c.set(x + (k // 3), int(top) - k, NEAR[3])
            c.set(x + h // 3, int(top) - h, GOLD[3] if h01(x, 3, 83) < 0.5 else NEAR[5])
            c.set(x + h // 3 + 1, int(top) - h + 1, GOLD[2])
        if h01(x, 4, 83) < 0.35: c.set(x, int(top), GOLD[2])      # rim light on the crest
    return c.img


# ============================================================================ tiles (48 layout)
N_, E_, S_, W_ = 1, 2, 4, 8


def loam_px(x, y, seed=0):
    n = tn(x * 7 + seed * 13, y * 7, 8, 8, 91)
    return pick(LOAM, 0.35 + 0.35 * n, x, y)


def solid_tile(mask, var=False):
    img = blank(16, 16); p = img.load()
    for y in range(16):
        for x in range(16):
            d = 99
            if mask & N_: d = min(d, y)
            if mask & S_: d = min(d, 15 - y)
            if mask & W_: d = min(d, x)
            if mask & E_: d = min(d, 15 - x)
            v = 0.25 + 0.3 * tn(x * 5 + (13 if var else 0), y * 5, 16, 16, 92) + (0.18 if d < 2 else 0.08 if d < 4 else 0)
            p[x, y] = pick(LOAM, clamp(v), x, y)
    # field stones and roots in the soil
    for i in range(1 if var else 0):
        sx, sy = int(3 + h01(mask, i, 93 + var) * 10), int(5 + h01(mask, i + 5, 93 + var) * 8)
        for yy in range(sy, sy + 2 + (i % 2)):
            for xx in range(sx, sx + 3):
                if 0 <= xx < 16 and 0 <= yy < 16: p[xx, yy] = STONE[2 + ((xx + yy) % 2)]
        if 0 <= sx < 16 and 0 <= sy < 16: p[sx, sy] = STONE[4]
    if var:
        for k in range(10):
            x, y = int(2 + k * 1.3), int(9 + math.sin(k * 0.9) * 2)
            if 0 <= x < 16: p[x, y] = C("3a2418")
    if mask & N_:     # the top: a crust of golden stubble and earth
        for x in range(16):
            h = 2 + int(h01(x, mask, 94) * 2)
            for y in range(0, h): p[x, y] = GOLD[3 + (1 if y == 0 and h01(x, 7, 95) < 0.5 else 0)] if y < h - 1 else GOLD[1]
            if h01(x, 2, 96) < 0.4: p[x, h] = LOAM[5]
    if mask & W_:
        for y in range(16): p[0, y] = LOAM[1]
    if mask & E_:
        for y in range(16): p[15, y] = K
    if mask & S_:
        for x in range(16): p[x, 15] = K
    if mask & N_ and mask & W_: p[0, 0] = T
    if mask & N_ and mask & E_: p[15, 0] = T
    return img


def plat_tile(kind):
    img = blank(16, 16); p = img.load()
    for x in range(16):
        for y in range(1, 5): p[x, y] = GOLD[1] if y > 2 else GOLD[2]
        p[x, 0] = K; p[x, 5] = K
    if kind in (0, 3):
        for y in range(0, 12): p[2, y] = LOAM[5]
    if kind in (2, 3):
        for y in range(0, 12): p[13, y] = LOAM[5]
    return img


def deco_tile(i):
    img = blank(16, 16); p = img.load()
    if i == 0:     # a field-stone
        for y in range(10, 16):
            for x in range(4, 12):
                if (x - 8) ** 2 / 16 + (y - 14) ** 2 / 12 < 1: p[x, y] = STONE[2 + (x < 7)]
    elif i == 1:   # poppies
        for k, x in enumerate((3, 8, 12)):
            for y in range(9 + k, 16): p[x, y] = C("3a4a22")
            p[x, 8 + k] = C("d8402a"); p[x + 1, 8 + k] = C("a82a1e")
    elif i == 2:   # a scatter of shed scales
        for k in range(4):
            x, y = 2 + k * 3, 13 + (k % 2)
            p[x, y] = SLATE[3]; p[x + 1, y] = SLATE[4]; p[x, y - 1] = EMBER[3] if k % 2 else SLATE[2]
    else:          # stubble tuft
        for k in range(6):
            x = 2 + k * 2
            for y in range(11 + k % 2, 16): p[x, y] = GOLD[4 - (y > 13)]
    return img


def build_tiles():
    tiles = []
    for m in range(16): tiles.append(solid_tile(m))
    for m in range(16): tiles.append(solid_tile(m, True))
    for k in range(4): tiles.append(plat_tile(k))
    sp = blank(16, 16); tiles.append(sp); tiles.append(sp.copy())          # 36/37 spikes (unused here)
    for i in range(4):                                                      # 38-41 back wall (unused: outdoor)
        b = blank(16, 16); tiles.append(b)
    for i in range(4): tiles.append(deco_tile(i))                           # 42-45 decor
    tiles.append(solid_tile(0))                                             # 46 breakable
    tuft = blank(16, 16); pt = tuft.load()                                  # 47 top tuft: stalks of wheat over the lip
    for k in range(7):
        x = 1 + k * 2
        h = 5 + int(h01(k, 1, 97) * 5)
        for y in range(16 - h, 16): pt[x, y] = GOLD[3] if y > 16 - h + 1 else GOLD[6]
    tiles.append(tuft)
    return tiles


# ============================================================================ props
def build_nest():
    c = Canvas(80, 32)
    # a hollow pressed into the wheat: flattened straw in a ring, woven twigs, and her shed scales standing in the rim
    for y in range(14, 32):
        for x in range(80):
            u, v = (x - 40) / 38.0, (y - 30) / 14.0
            r = u * u + v * v
            if r < 1:
                inner = (x - 40) ** 2 / (26 * 26) + (y - 27) ** 2 / 36.0 < 1
                col = pick(GOLD, 0.25 + 0.35 * tn(x * 3, y * 3, 8, 4, 101), x, y) if not inner else pick(LOAM, 0.55 + 0.2 * tn(x * 5, y * 5, 8, 8, 102), x, y)
                c.set(x, y, col)
    for i in range(40):   # woven straw strokes
        a = h01(i, 1, 103) * math.pi
        x0 = 40 + math.cos(a) * (28 + h01(i, 2, 103) * 8) * (1 if i % 2 else -1)
        y0 = 26 + h01(i, 3, 103) * 5
        for k in range(6): c.set(x0 + k * (1 if i % 3 else -1), y0 - k * 0.35, GOLD[5 if k < 2 else 3])
    # shed scales: dark slate teardrops standing around the rim, some with an ember sheen
    for i, x in enumerate(range(10, 72, 7)):
        base = 24 + int(3 * math.sin(i * 1.3)) + (2 if 20 < x < 60 else 0)
        h = 7 + int(h01(i, 4, 104) * 4)
        lean = (x - 40) / 30.0
        for k in range(h):
            w = 2 if k < h - 3 else 1 if k < h - 1 else 0
            cx = x + lean * k * 0.6
            for dx in range(-w, w + 1):
                col = SLATE[3 + (dx < 0)] if k > 1 else SLATE[1]
                if dx == w and k > 2: col = EMBER[2] if i % 3 == 0 else SLATE[5]
                c.set(cx + dx, base - k, col)
        c.set(x + lean * h * 0.6, base - h, SLATE[6])
    img = outline(c.img, K)
    return img


def build_egg():
    frames = []
    for f in range(6):
        c = Canvas(16, 20)
        pulse = 0.5 + 0.5 * math.sin(f / 6 * math.tau)
        for y in range(3, 20):
            for x in range(16):
                u, v = (x - 7.5) / 5.6, (y - 12.5) / (8.0 if y < 12.5 else 6.6)
                if u * u + v * v <= 1:
                    shade = clamp(0.5 - u * 0.35 - v * 0.2)
                    c.set(x, y, pick(SLATE, 0.25 + shade * 0.7, x, y))
        # ember cracks, breathing
        cracks = [(7, 6), (8, 7), (8, 8), (7, 9), (6, 10), (6, 11), (7, 12), (9, 9), (10, 10), (10, 11), (11, 12), (5, 14), (6, 15), (8, 15), (9, 16)]
        for i, (x, y) in enumerate(cracks):
            k = clamp(0.45 + 0.4 * pulse + 0.15 * math.sin(i + f))
            c.set(x, y, pick(EMBER, k, x, y))
        c.set(6, 8, SLATE[6]); c.set(5, 9, SLATE[5])      # a glint
        frames.append(outline(c.img, K))
    gone = Canvas(16, 20)
    for x, y in [(4, 18), (5, 17), (6, 18), (10, 18), (11, 17), (12, 18), (8, 19)]:
        gone.set(x, y, SLATE[3])
    gone.set(5, 16, EMBER[2]); gone.set(11, 16, SLATE[4])
    frames.append(gone.img)
    return frames


def build_stone():
    """the lore stone: a leaning standing stone carved with a drake curled around a sun"""
    c = Canvas(32, 48)
    for y in range(4, 48):
        for x in range(32):
            u = (x - 16 - (48 - y) * 0.06) / (9.5 - max(0, (12 - y)) * 0.55)
            if abs(u) <= 1 and y > 4 + abs(u) * 3:
                c.set(x, y, pick(STONE, 0.28 + 0.35 * (1 - (u + 1) / 2) + 0.12 * tn(x * 3, y * 3, 8, 8, 111), x, y))
    # the carving: a sun disc with a drake coiled about it, catching the low light
    for a in range(0, 360, 12):
        r = 5
        c.set(16 + math.cos(math.radians(a)) * r, 22 + math.sin(math.radians(a)) * r, STONE[1])
    pts = [(10, 16), (11, 15), (13, 14), (16, 13), (19, 14), (21, 16), (22, 19), (22, 23), (21, 26), (19, 28), (16, 29), (13, 28), (11, 26)]
    for (x, y) in pts: c.set(x, y, STONE[1]); c.set(x + 1, y - 1, GOLD[4])
    c.set(9, 15, STONE[1]); c.set(8, 14, STONE[1]); c.set(9, 13, GOLD[5])      # the head
    c.set(23, 17, STONE[1]); c.set(25, 15, STONE[1]); c.set(24, 16, STONE[1])  # a wing
    for x in range(12, 21): c.set(x, 36, STONE[1])                              # runes
    for x in range(13, 20, 2): c.set(x, 38, STONE[1])
    for y in range(40, 48):                                                      # wheat grown around its foot
        for x in (5, 8, 24, 27): c.set(x + (y % 3 == 0), y, GOLD[3 + (y < 42)])
    return outline(c.img, K)


def build_tree():
    """the old ash at the field's end: a leaning, split trunk, bare limbs, a few gold leaves, roots over the rock"""
    c = Canvas(112, 176)
    segs = []
    def limb(x, y, ang, ln, w, depth, seed):
        pts = []
        for i in range(int(ln)):
            ang += (h01(i, seed, 122) - 0.5) * 0.16 + 0.01 * math.sin(i * 0.3 + seed)
            x += math.cos(ang); y -= math.sin(ang)
            pts.append((x, y, max(0.4, w * (1 - 0.72 * i / ln))))
        segs.append(pts)
        if depth > 0:
            n = 2 if depth > 1 else 3
            for k in range(n):
                a2 = ang + (-0.55 + 1.1 * k / max(1, n - 1)) + (h01(depth, k, seed) - 0.5) * 0.3
                j = int(len(pts) * (0.55 + 0.4 * h01(k, depth, seed + 1)))
                px, py, pw = pts[min(j, len(pts) - 1)]
                limb(px, py, a2, ln * (0.55 + 0.15 * h01(k, 3, seed)), pw * 0.75, depth - 1, seed * 5 + k + 1)
    limb(58, 175, math.radians(96), 70, 9, 3, 7)             # the trunk, leaning a little west
    limb(62, 120, math.radians(40), 38, 4.5, 2, 19)          # a great limb reaching over the nest
    limb(52, 132, math.radians(150), 30, 4, 2, 23)
    for pts in segs:
        for (x, y, w) in pts:
            for dx in range(-int(w), int(w) + 1):
                u = dx / (w + 0.01)
                c.set(x + dx, y, pick(MID, 0.2 + 0.45 * (u + 1) / 2 + 0.08 * tn(int(x + dx) * 3, int(y), 8, 16, 121), x + dx, y))
        x, y, w = pts[-1]
        if h01(int(x), int(y), 124) < 0.5: c.set(x, y - 1, GOLD[6]); c.set(x + 1, y - 2, GOLD[5])
    # root flare over the rock
    for k, (dx, ln) in enumerate([(-1, 20), (1, 16), (-1, 11), (1, 24)]):
        for i in range(ln):
            x, y = 58 + dx * (4 + i), 172 + i * 0.18 - (k % 2)
            for yy in range(int(y), 176): c.set(x, yy, MID[2 + (i % 2)])
    img = c.img; p = img.load()
    for y in range(176):
        for x in range(1, 112):
            if p[x, y][3] and not p[x - 1, y][3] and h01(x, y, 123) < 0.65: p[x, y] = GOLD[4]
    return outline(img, K)


def build_small(kind):
    if kind == 'stones':    # a toppled ring of field-stones, a cairn
        c = Canvas(48, 32)
        for i, (x, w, h) in enumerate([(8, 5, 10), (18, 6, 18), (28, 5, 13), (38, 5, 8)]):
            for y in range(32 - h, 32):
                for xx in range(x - w, x + w):
                    u = (xx - x) / w
                    if abs(u) < 1 - max(0, (32 - h + 3 - y)) * 0.2:
                        c.set(xx, y, pick(STONE, 0.3 + 0.35 * (1 - u) / 2 + 0.1 * tn(xx * 4, y * 4, 8, 8, 131 + i), xx, y))
            c.set(x - 1, 32 - h, GOLD[5])
        return outline(c.img, K)
    if kind == 'fence':     # an old split-rail fence, one rail down
        c = Canvas(48, 24)
        for x in (4, 22, 42):
            for y in range(6, 24): c.set(x, y, MID[3]); c.set(x + 1, y, MID[5])
            c.set(x + 1, 6, GOLD[5])
        for x in range(4, 23): c.set(x, 10 + (x % 7 == 0), MID[4]); c.set(x, 11, MID[2])
        for x in range(22, 43): c.set(x, 17 - (x - 22) * 0.35, MID[4]); c.set(x, 18 - (x - 22) * 0.35, MID[2])
        for x in range(4, 42): c.set(x, 15, MID[3]) if x < 20 else None
        return outline(c.img, K)
    if kind == 'plough':    # an abandoned plough, rust and grey wood, wheat grown through it
        c = Canvas(40, 24)
        for x in range(4, 30): c.set(x, 12 + (x - 4) * 0.25, MID[4]); c.set(x, 13 + (x - 4) * 0.25, MID[2])
        for y in range(4, 14): c.set(6 - (y - 4) * 0.2, y, MID[4])
        for y in range(6, 14): c.set(3 - (y - 6) * 0.2, y, MID[4])
        for y in range(17, 24):
            for x in range(26, 34):
                if (x - 26) > (y - 17) * 1.1 - 1: c.set(x, y, pick(STONE, 0.35 + 0.1 * (x % 2), x, y))
        for x in range(26, 36): c.set(x, 17, C("7a3a1c"))
        for k in range(8):
            x = 2 + k * 5
            for y in range(24 - 5 - k % 3, 24): c.set(x, y, GOLD[3 + (y < 20)])
        return outline(c.img, K)


# ============================================================================ build
def main(ase=True):
    import asebuild
    sky, clouds, far, mid, near = build_sky(), build_clouds(), build_far(), build_mid(), build_near()
    tiles = build_tiles()
    nest, egg, stone, treeimg = build_nest(), build_egg(), build_stone(), build_tree()
    smalls = {k: build_small(k) for k in ('stones', 'fence', 'plough')}
    prev = os.path.join(HERE, 'previews'); os.makedirs(prev, exist_ok=True)
    # ---- a mock of the room at 1x: layers + a ground strip + wheat stand-ins + props
    GY = 138
    mock = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for L in (sky, clouds, far, mid, near): mock.alpha_composite(L)
    for x in range(0, W, 16):
        for y in range(GY, H, 16):
            m = 1 if y == GY else 0
            mock.alpha_composite(tiles[m], (x, y))
    mock.alpha_composite(treeimg, (400, GY - 176 + 4))
    mock.alpha_composite(nest, (300, GY - 32 + 6)); mock.alpha_composite(egg[0], (332, GY - 20 + 2))
    mock.alpha_composite(stone, (160, GY - 48 + 2)); mock.alpha_composite(smalls['stones'], (60, GY - 32 + 2))
    mock.alpha_composite(smalls['fence'], (220, GY - 24 + 2)); mock.alpha_composite(smalls['plough'], (110, GY - 24 + 2))
    scale(mock, 3).save(os.path.join(prev, 'xrc_lf_preview.png'))
    parts = Image.new('RGBA', (512, 200), (40, 30, 40, 255))
    for i, im in enumerate(tiles[:32]): parts.alpha_composite(im, (4 + (i % 16) * 18, 4 + (i // 16) * 18))
    for i, im in enumerate(tiles[32:]): parts.alpha_composite(im, (4 + i * 18, 44))
    x = 4
    for im in [nest, stone, smalls['stones'], smalls['fence'], smalls['plough']] + egg:
        parts.alpha_composite(im, (x, 70)); x += im.size[0] + 4
    parts.alpha_composite(treeimg.crop((0, 0, 112, 120)), (380, 70))
    scale(parts, 2).save(os.path.join(prev, 'xrc_lf_parts.png'))
    if not ase: return
    one = lambda name, im, tag='loop': asebuild.build(name, im.size[0], im.size[1], ['art'], [{'ms': 100, 'cels': {'art': im}}], [(tag, 0, 0)])
    for name, im in [('xrc_lf_sky', sky), ('xrc_lf_clouds', clouds), ('xrc_lf_far', far), ('xrc_lf_mid', mid), ('xrc_lf_near', near)]:
        one(name, im)
    asebuild.build('tiles_lastfield', 16, 16, ['art'], [{'ms': 100, 'cels': {'art': t}} for t in tiles], [('all', 0, len(tiles) - 1)])
    one('xrc_lf_nest', nest, 'idle'); one('xrc_lf_stone', stone, 'idle'); one('xrc_lf_tree', treeimg, 'idle')
    for k, im in smalls.items(): one('xrc_lf_' + k, im, 'idle')
    asebuild.build('xrc_lf_egg', 16, 20, ['art'], [{'ms': 140, 'cels': {'art': im}} for im in egg], [('glow', 0, 5), ('gone', 6, 6)])


if __name__ == '__main__':
    main('--no-ase' not in sys.argv)
