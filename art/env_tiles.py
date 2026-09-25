"""Tilesets for the three biomes: tiles_<biome>, 48 frames of 16x16 (see docs/ART_SPEC.md s6).

 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8)
16-31  same masks, variant (cracks / moss / roots / inlays)
32-35  one-way platform L / M / R / single      36/37 floor / ceiling spikes
38-41  background wall tiles                    42-45 chain / roots / candles / bones overlays
46     breakable wall (looks like 0)            47 rubble / grass tuft overlay

The masonry pattern is a function of the in-tile pixel only (period 16 in x and y), so the
interior texture continues seamlessly across any combination of tiles; edge treatment
(lip, rim light, outline, underside shadow, chips) is layered on per exposed side.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, pick_i, clamp, smooth, blank, outline

N, E, S, W = 1, 2, 4, 8
TS = 16

# --------------------------------------------------------------------------- biome configs
BIOMES = {
    "ramparts": dict(
        stone=ramp("15131b", "201d27", "2b2833", "383440", "47424e", "59535e", "6f6870", "8a8185", "a89c96"),
        base=4.6, deep=1.0,
        mortar_drop=2.2,
        courses=[(6, [4, 13]), (5, [9]), (5, [1, 12])],
        round_corners=False,
        lip=[C("c9b596"), C("9a8c84"), C("6f6870"), C("2b2833")],
        lip_joints=[10],
        rim=C("7f777a"), rim2=C("5f5862"),
        under=C("201d27"),
        tuft=ramp("3f3d2a", "5c5a36", "7f7a46", "a39a5c"),
        ash=C("b3a58c"),
        accent=ramp("3f3d2a", "556038", "72804a"),    # moss
        wood=ramp("1e1512", "3a2a20", "58402c", "7a5a3c", "9c7a52"),
        iron=ramp("15131b", "2e2a33", "4a4550", "736c74", "a39aa0"),
        flame=ramp("8a2e12", "d86a22", "ffb040", "fff0b0"),
        bg=ramp("121118", "181720", "1f1d28", "262431", "2e2b39", "363242"),
        bgbase=3.0,
    ),
    "catacombs": dict(
        stone=ramp("120d0e", "1d1616", "292020", "362a27", "453630", "57443a", "6d5646", "886c54", "a48768"),
        base=5.0, deep=1.2,
        mortar_drop=2.4,
        courses=[(5, [2, 9]), (6, [5, 13]), (5, [0, 10])],
        round_corners=True,
        lip=[C("a08466"), C("7c6450"), C("574438"), C("1d1616")],
        lip_joints=[],
        rim=C("7a6250"), rim2=C("5a4638"),
        under=C("1d1616"),
        tuft=ramp("2c2420", "4a3c32", "6e5a48", "94806a"),
        ash=C("8f7a62"),
        accent=ramp("4a2e12", "7a5220", "b07c30", "e0b050", "ffe08a"),   # gold roots
        bone=ramp("4e4638", "7e7460", "aea388", "d6ceb2"),
        wood=ramp("1a1210", "33241c", "4e3828", "6c4e36", "8c6a4a"),
        iron=ramp("120d0e", "2a2424", "463e3c", "6a605a", "948878"),
        flame=ramp("1c5a5a", "2e9a94", "6ee0cc", "d8fff4"),
        bg=ramp("0e0b0b", "151011", "1c1516", "231b1b", "2b2120", "342826"),
        bgbase=3.0,
    ),
    "cathedral": dict(
        stone=ramp("171824", "232534", "313445", "434758", "585d6f", "727788", "8f94a2", "b0b3bb", "d4d3d0"),
        base=5.3, deep=1.4, pits=0.025,
        mortar_drop=2.0,
        courses=[(8, [3]), (8, [11])],
        round_corners=False,
        lip=[C("eee8d8"), C("c4c4c4"), C("a8823c"), C("313445")],
        lip_joints=[],
        rim=C("a0a4b0"), rim2=C("7c8190"),
        under=C("232534"),
        tuft=ramp("2c3440", "4a5462", "6e7a86", "98a4ac"),
        ash=C("c9c6be"),
        accent=ramp("5a3c14", "8a6224", "c09440", "ecc870", "fff0b8"),   # gold filigree
        wood=ramp("1e1a1c", "3a3030", "564640", "76604e", "9a8062"),
        iron=ramp("171824", "2c2e3c", "484c5c", "727788", "a4a8b4"),
        flame=ramp("8a4a12", "d8922a", "ffd060", "fff6c8"),
        bg=ramp("0f1019", "151722", "1b1e2b", "222634", "2a2e3f", "32374a"),
        bgbase=3.0,
    ),
}


# --------------------------------------------------------------------------- masonry
def masonry(cfg, x, y):
    """-> (level_offset, is_mortar, block_id, local coords) for in-tile pixel (x, y)."""
    y0 = 0
    for ci, (h, joints) in enumerate(cfg["courses"]):
        if y0 <= y < y0 + h:
            ly = y - y0
            if ly == h - 1:
                return None, True, (ci, -1), (0, ly, h)
            if x in joints:
                return None, True, (ci, -1), (0, ly, h)
            # block index: which joint precedes x (wrapping)
            prev = max([j for j in joints if j < x], default=max(joints) - TS)
            nxt = min([j for j in joints if j > x], default=min(joints) + TS)
            bi = joints.index(prev % TS) if (prev % TS) in joints else 0
            lx, bw = x - prev - 1, nxt - prev - 1
            return (lx, ly, bw, h - 1), False, (ci, bi), (lx, ly, h)
        y0 += h
    raise ValueError


def block_level(cfg, x, y, seed=0):
    """Fractional ramp level for the lit, textured masonry at in-tile (x, y)."""
    geo, mortar, bid, _ = masonry(cfg, x, y)
    b = cfg["base"]
    if mortar:
        return b - cfg["mortar_drop"], True
    lx, ly, bw, bh = geo
    tone = h01(bid[0] * 7 + bid[1], 3, 91 + seed)
    lv = b + (-0.9 if tone < 0.28 else (0.55 if tone > 0.8 else 0.0))
    if cfg["round_corners"] and (lx in (0, bw - 1)) and (ly in (0, bh - 1)):
        return b - cfg["mortar_drop"] + 0.6, True
    if ly == 0:
        lv += 1.0            # top face catches the light
    elif ly == bh - 1:
        lv -= 0.9
    if lx == 0 and ly > 0:
        lv += 0.45
    elif lx == bw - 1:
        lv -= 0.8
    r = h01(x, y, 7 + seed)
    if r < cfg.get("pits", 0.07):
        lv -= 1.0            # pits
    elif r > 0.965 and ly > 0:
        lv += 0.8            # glints
    return lv, False


def lit_level(cfg, x, y, seed=0):
    lv, mortar = block_level(cfg, x, y, seed)
    return lv, mortar


def deep_level(cfg, x, y, seed=0):
    """Deep interior: flat, dark, only faint joints (low detail)."""
    _, mortar, _, _ = masonry(cfg, x, y)
    lv, _ = block_level(cfg, x, y, seed)
    D = cfg["deep"]
    if mortar:
        return D - 1
    return D + (0.6 if lv - cfg["base"] > 0.8 else 0)


def level_at(cfg, x, y, dfun, seed=0, shift=0.0):
    """dfun(x, y) -> distance to the nearest exposed edge (unclamped coords ok)."""
    geo, mortar, bid, _ = masonry(cfg, x, y)
    if mortar:
        t = dfun(x, y) + 1.5
    else:
        lx, ly, bw, bh = geo
        a, b = max(0, x - lx), min(TS - 1, x - lx + bw - 1)     # block piece clipped to tile
        cx, cy = (a + b) / 2, y - ly + (bh - 1) / 2
        t = min(dfun(a, cy), dfun(b, cy), dfun(cx, cy)) + 4.0 * h01(bid[0] * 7 + bid[1], 5, 77 + seed)
    top = len(cfg["stone"]) - 1
    if t < 7.0:
        lv = lit_level(cfg, x, y, seed)[0] + shift
    elif t < 11.0:
        lv = lit_level(cfg, x, y, seed)[0] - 1.2 + shift * 0.7
    else:
        lv = deep_level(cfg, x, y, seed) + shift * 0.4
    return int(round(clamp(lv, 0, top)))


def interior_color(cfg, x, y, dfun, seed=0, shift=0.0):
    return cfg["stone"][level_at(cfg, x, y, dfun, seed, shift)]


# --------------------------------------------------------------------------- solid tile
def solid_shape(mask, cfg):
    """Opaque-pixel mask for a solid tile: rounded exposed corners + chips at joints."""
    sh = [[True] * TS for _ in range(TS)]
    cut = []
    if mask & N and mask & W:
        cut += [(0, 0), (1, 0), (0, 1)]
    if mask & N and mask & E:
        cut += [(15, 0), (14, 0), (15, 1)]
    if mask & S and mask & W:
        cut += [(0, 15), (1, 15), (0, 14)]
    if mask & S and mask & E:
        cut += [(15, 15), (14, 15), (15, 14)]
    for x, y in cut:
        sh[y][x] = False
    # chips where mortar lines meet an exposed side face
    for y in range(4 if mask & N else 0, TS - (3 if mask & S else 0)):
        _, mort, _, (_, ly, h) = masonry(cfg, 0, y)
        if ly == h - 1 or (cfg["round_corners"] and ly == 0):
            if mask & W:
                sh[y][0] = False
            if mask & E:
                sh[y][15] = False
    if mask & S:
        for x in range(1, TS - 1):
            _, mort, _, _ = masonry(cfg, x, 15)
            if masonry(cfg, x, 14)[1] and h01(x, 1, 5) < 0.6:
                sh[15][x] = False
        for x in range(TS):
            if h01(x, 2, 9) < 0.18:
                sh[15][x] = False
    return sh


def solid_tile(cfg, mask, seed=0):
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask, cfg)
    st = cfg["stone"]

    def dfun(x, y):
        ds = [99]
        if mask & N:
            ds.append(y)
        if mask & S:
            ds.append(15 - y + 3)
        if mask & W:
            ds.append(x)
        if mask & E:
            ds.append(15 - x + 1)
        return max(0, min(ds))

    def out(x, y, dx, dy):
        X, Y = x + dx, y + dy
        if X < 0:
            return bool(mask & W)
        if X >= TS:
            return bool(mask & E)
        if Y < 0:
            return bool(mask & N)
        if Y >= TS:
            return bool(mask & S)
        return not sh[Y][X]

    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            ds = [99]
            if mask & N:
                ds.append(y)
            if mask & S:
                ds.append(15 - y)
            if mask & W:
                ds.append(x)
            if mask & E:
                ds.append(15 - x)
            d = min(ds)
            lvshift = 0.0
            if mask & W and x < 3:
                lvshift += (1.0, 0.6, 0.3)[x]
            if mask & E and 15 - x < 3:
                lvshift -= (1.0, 0.6, 0.3)[15 - x]
            if mask & S and 15 - y < 4:
                lvshift -= (1.6, 1.2, 0.8, 0.4)[15 - y]
            c = interior_color(cfg, x, y, dfun, seed, lvshift)
            px[x, y] = c
    # ---- side faces: rim light (W), outline (E, S)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            o_w, o_e, o_s, o_n = out(x, y, -1, 0), out(x, y, 1, 0), out(x, y, 0, 1), out(x, y, 0, -1)
            if o_e or o_s:
                px[x, y] = K
            elif o_w and not (mask & N and y < 4):
                px[x, y] = cfg["rim"] if (y + x) % 5 else cfg["rim2"]
            elif o_n and not (mask & N):     # notch interiors
                px[x, y] = K
    # ---- top lip
    if mask & N:
        lip = cfg["lip"]
        for y in range(4):
            for x in range(TS):
                if not sh[y][x]:
                    continue
                c = lip[y]
                if x in cfg["lip_joints"] and 1 <= y <= 2:
                    c = lip[3]
                if y == 0 and h01(x, 0, 21) < 0.22:
                    c = lip[1]
                if y == 1 and h01(x, 1, 22) < 0.15:
                    c = lip[0]
                if out(x, y, 1, 0) or (mask & E and x == 15):
                    c = K if y else lip[2]
                elif mask & W and x == 0 or out(x, y, -1, 0):
                    c = lip[0] if y < 2 else lip[1]
                px[x, y] = c
        # rounded corner shoulder
        if mask & E:
            px[14, 1] = lip[1]
            px[13, 0] = lip[1]
    return img


# --------------------------------------------------------------------------- variants
def crack(img, pts, dark, lite=None):
    px = img.load()
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            x = round(x0 + (x1 - x0) * k / max(n, 1))
            y = round(y0 + (y1 - y0) * k / max(n, 1))
            if 0 <= x < TS and 0 <= y < TS and px[x, y][3]:
                px[x, y] = dark
                if lite and 0 <= x + 1 < TS and px[x + 1, y][3] and px[x + 1, y] != dark:
                    px[x + 1, y] = lite


CRACKS = [
    [(4, 5), (6, 7), (6, 9), (8, 11), (9, 13)],
    [(11, 4), (10, 6), (11, 8), (9, 10)],
    [(3, 9), (5, 10), (7, 10), (8, 12)],
    [(7, 5), (8, 7), (7, 9), (8, 10), (10, 11)],
]


def lvl_of(cfg, c):
    st = cfg["stone"]
    return st.index(c) if c in st else -1


def draw_path(img, pts, colfn, lo=0, hi=15):
    """Walk a polyline; colfn(x, y, i, level) -> colour or None. Skips K/transparent pixels."""
    px = img.load()
    done = set()
    i = 0
    for a in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[a], pts[a + 1]
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            x, y = round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n)
            if (x, y) in done or not (0 <= x < TS and lo <= y <= hi):
                continue
            done.add((x, y))
            c0 = px[x, y]
            if c0[3] == 0 or c0 == K:
                continue
            c = colfn(x, y, i, c0)
            if c:
                px[x, y] = c
            i += 1


def f_crack(cfg, img, mask, k, lo):
    st = cfg["stone"]
    pts = [(x, max(lo + 1, min(13, y))) for x, y in CRACKS[k % 4]]
    px = img.load()

    def col(x, y, i, c0):
        L = lvl_of(cfg, c0)
        if L < 0:
            return None
        # lit lip on the upper-left side of the crack when the stone is in the lit crust
        if L >= 3 and x > 0 and px[x - 1, y] not in (K,) and px[x - 1, y][3] and lvl_of(cfg, px[x - 1, y]) >= 3:
            px[x - 1, y] = st[min(len(st) - 1, L + 1)]
        return st[max(0, L - 3)]
    draw_path(img, pts, col, lo, 14)


def f_mortar_roots(cfg, img, mask, k, lo):
    """Gold roots creeping along the mortar joints (catacombs)."""
    r = cfg["accent"]
    px = img.load()
    yrow = [4, 10, 15][k % 3]
    if yrow < lo + 1 or (mask & S and yrow > 12):
        yrow = 10
    xs = range(1, 15) if k % 2 else range(2, 12)
    for x in xs:
        wob = 0 if h01(x, k, 61) < 0.7 else (-1 if h01(x, k, 62) < 0.5 else 1)
        y = yrow + wob
        if not (lo <= y <= 14):
            continue
        c0 = px[x, y]
        if c0[3] == 0 or c0 == K:
            continue
        L = lvl_of(cfg, c0)
        bright = L >= 3 or L < 0
        if not bright:           # deep interior: barely-there dark root
            if h01(x, y, 64) < 0.75:
                px[x, y] = r[0]
            continue
        px[x, y] = r[2]
        if y - 1 >= lo and px[x, y - 1] not in (K,) and px[x, y - 1][3] and h01(x, y, 63) < 0.5:
            px[x, y - 1] = r[3]
        if y + 1 <= 14 and px[x, y + 1] not in (K,) and px[x, y + 1][3]:
            px[x, y + 1] = r[0]
    # a glowing node and a descending feeler
    nx = 5 + k % 6
    if lo <= yrow <= 14 and lvl_of(cfg, px[nx, yrow]) != 0 and mask:
        px[nx, yrow] = r[4]
        for dy in range(1, 3 + k % 3):
            if yrow + dy <= 14 and px[nx + 1, yrow + dy] != K and px[nx + 1, yrow + dy][3]:
                px[nx + 1, yrow + dy] = r[1] if dy > 1 else r[2]


def f_skull(cfg, img, mask, k, lo):
    px = img.load()
    bone = cfg["bone"]
    st = cfg["stone"]
    sx, sy = 4 + (k * 3) % 6, max(lo + 2, 6 + k % 3)
    SK = [".111.", "12221", "20302", ".121."]
    for j, row in enumerate(SK):
        for i, ch in enumerate(row):
            X, Y = sx + i, sy + j
            if ch != "." and 0 <= X < 16 and Y < 15 and px[X, Y] != K and px[X, Y][3]:
                px[X, Y] = {"0": st[0], "1": bone[0], "2": bone[1], "3": bone[2]}[ch]
    if lo <= sy - 1:
        px[sx + 1, sy - 1] = bone[2]
        px[sx + 2, sy - 1] = bone[3]


def f_bones(cfg, img, mask, k, lo):
    px = img.load()
    bone = cfg["bone"]
    for (x0, y0, L, d) in ((3, 7 + k % 3, 5, 0), (9, 12, 4, -1)):
        y = max(lo + 1, y0)
        for i in range(L):
            X, Y = x0 + i, y + (i * d) // 3
            if 0 <= X < 16 and Y < 15 and px[X, Y] != K:
                px[X, Y] = bone[2] if i in (0, L - 1) else bone[1]
        if px[x0, y - 1] != K and y - 1 >= lo:
            px[x0, y - 1] = bone[1]


def f_vein(cfg, img, mask, k, lo):
    st = cfg["stone"]
    pts = [[(1, 6), (4, 7), (6, 9), (9, 10), (13, 13)], [(14, 5), (11, 7), (9, 7), (7, 9), (5, 13)],
           [(2, 12), (5, 11), (8, 12), (11, 10), (14, 11)], [(6, 5), (7, 8), (10, 9), (12, 13)]][k % 4]
    pts = [(x, max(lo + 1, y)) for x, y in pts]

    def col(x, y, i, c0):
        L = lvl_of(cfg, c0)
        if L < 0 or (L < 3 and i % 2):
            return None
        return st[min(len(st) - 1, L + 1 + (1 if i % 3 == 0 and L >= 4 else 0))]
    draw_path(img, pts, col, lo, 14)


def f_inlay(cfg, img, mask, k, lo):
    px = img.load()
    g = cfg["accent"]
    cx, cy = (7, 12) if (k % 2 or lo > 4) else (8, 4)
    if cy - 2 < lo:
        cy = 12
    pat = {(0, -2): 2, (-1, -1): 1, (1, -1): 3, (-2, 0): 1, (0, 0): 4, (2, 0): 2, (-1, 1): 1, (1, 1): 2,
           (0, 2): 1, (-3, 0): 0, (3, 0): 0}
    for (dx, dy), c in pat.items():
        X, Y = cx + dx, cy + dy
        if 0 <= X < 16 and lo <= Y < 15 and px[X, Y] != K and px[X, Y][3]:
            px[X, Y] = g[c]


def f_moss(cfg, img, mask, k, lo):
    px = img.load()
    mos = cfg["accent"]
    if not mask & N:
        return
    for x in range(1, 15):
        v = h01(x, mask, 33)
        if v < 0.55:
            L = 1 + int(h01(x, mask, 34) * 3) if v < 0.3 else 0
            px[x, 3] = mos[1]
            px[x, 2] = mos[2] if h01(x, 9, 35) < 0.5 else mos[1]
            for yy in range(4, 4 + L):
                if px[x, yy][3] and px[x, yy] != K:
                    px[x, yy] = mos[0] if yy == 3 + L else mos[1]


FEATURES = {
    "ramparts": [[f_crack, f_moss], [f_crack], [f_moss], [f_crack, f_moss]],
    "catacombs": [[f_mortar_roots], [f_skull], [f_mortar_roots, f_crack], [f_bones]],
    "cathedral": [[f_vein], [f_inlay], [f_crack], [f_vein, f_inlay]],
}


def variant_tile(biome, cfg, mask):
    img = solid_tile(cfg, mask, seed=5)
    k = (mask * 7 + 1) % 4
    lo = 4 if mask & N else 1
    feats = FEATURES[biome][k]
    if mask == 0:       # deep interior variant stays subtle
        feats = {"ramparts": [f_crack], "catacombs": [f_mortar_roots], "cathedral": [f_vein]}[biome]
    for f in feats:
        f(cfg, img, mask, mask // 2 + k, lo)
    return img


# --------------------------------------------------------------------------- one-way platforms
def platform(biome, cfg, kind):
    """kind: 'L', 'M', 'R', 'single'."""
    img = blank(TS, TS)
    px = img.load()
    left = kind in ("L", "single")
    right = kind in ("R", "single")
    if biome == "cathedral":
        st, gold = cfg["stone"], cfg["accent"]
        for x in range(TS):
            if (left and x == 0) or (right and x == 15):
                continue
            px[x, 0] = st[8]
            px[x, 1] = st[7]
            px[x, 2] = gold[2] if x % 4 else gold[3]
            px[x, 3] = st[5]
            px[x, 4] = K
        for (a, b) in ((0, 4),):
            pass
        # corbels
        xs = []
        if left:
            xs.append(2)
        if right:
            xs.append(10)
        if kind == "M":
            xs.append(6)
        for cx in xs:
            for i, row in enumerate(["K6655K", ".K54K.", ".K43K.", "..KK.."]):
                for j, ch in enumerate(row):
                    if ch != ".":
                        px[cx + j, 5 + i] = K if ch == "K" else st[int(ch)]
        if left:
            px[0, 1], px[0, 2], px[0, 3] = K, K, K
            px[1, 0] = st[8]
        if right:
            px[15, 1], px[15, 2], px[15, 3] = K, K, K
    else:
        wd, ir = cfg["wood"], cfg["iron"]
        for x in range(TS):
            if (left and x == 0) or (right and x == 15):
                continue
            seam = (x == 7 and kind != "single")
            px[x, 0] = wd[4] if not seam else wd[2]
            px[x, 1] = wd[3] if not seam else wd[1]
            px[x, 2] = wd[2] if h01(x, 2, 40) > 0.25 else wd[3]
            px[x, 3] = wd[1]
            px[x, 4] = K
        if left:
            for y in range(1, 4):
                px[0, y] = K
        if right:
            for y in range(1, 4):
                px[15, y] = K
        # iron strap / rope binding
        for sx in ([3] if left else []) + ([12] if right else []) + ([10] if kind == "M" else []):
            if biome == "catacombs":
                bone = cfg["bone"]
                for y in range(0, 4):
                    px[sx, y] = bone[2] if y % 2 == 0 else bone[1]
                px[sx, 4] = K
            else:
                for y in range(0, 4):
                    px[sx, y] = ir[3] if y == 0 else ir[2]
                    px[sx + 1, y] = ir[1]
        # bracket under the ends
        if left or right:
            for bx in ([1] if left else []) + ([9] if right else []):
                for i, row in enumerate(["K2222K", ".K21K.", "..KK.."]):
                    for j, ch in enumerate(row):
                        if ch != ".":
                            px[bx + j, 5 + i] = K if ch == "K" else ir[int(ch)]
    return img


# --------------------------------------------------------------------------- spikes
def spikes(biome, cfg, down=False):
    """Row of sharp spikes on a rubble base (bottom rows); flipped for the ceiling version."""
    img = blank(TS, TS)
    px = img.load()
    if biome == "catacombs":        # sharpened bone stakes
        a = cfg["bone"]
        dark, mid, lit, tip = a[0], a[1], a[2], a[3]
        base = cfg["stone"]
    elif biome == "cathedral":      # gilded iron spikes
        a = cfg["accent"]
        dark, mid, lit, tip = cfg["iron"][1], cfg["iron"][2], a[2], a[4]
        base = cfg["stone"]
    else:                           # rusted iron stakes
        ir = cfg["iron"]
        dark, mid, lit, tip = ir[1], ir[2], ir[3], ir[4]
        base = cfg["stone"]
    # spikes: (center x, tip y, half base width)
    SP = [(2, 4, 1.6), (6, 1, 2.0), (10, 5, 1.6), (13.5, 2, 1.8)]
    for (cx, ty, hw0) in SP:
        for y in range(ty, 14):
            t = (y - ty) / (13 - ty)
            hw = 0.25 + hw0 * t
            for x in range(TS):
                dx = x + 0.5 - cx
                if abs(dx) <= hw:
                    c = mid
                    if dx < 0 and dx > -hw + 0.0 and abs(dx) < hw * 0.55 + 0.3:
                        c = lit
                    if dx >= hw * 0.35:
                        c = dark
                    if y <= ty + 1:
                        c = tip
                    px[x, y] = c
    img = outline(img)
    px = img.load()
    # rubble base strip the spikes are driven into
    for x in range(TS):
        px[x, 15] = K
        px[x, 14] = base[3] if h01(x, 14, 4) < 0.6 else base[2]
        if h01(x, 13, 4) < 0.35 and px[x, 13] == T:
            px[x, 13] = base[4]
            if px[x, 12] == T:
                px[x, 12] = K
    if down:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


# --------------------------------------------------------------------------- background walls
def bg_wall(biome, cfg, k):
    bg = cfg["bg"]
    img = blank(TS, TS)
    px = img.load()
    c2 = dict(cfg)
    c2["base"], c2["mortar_drop"] = cfg["bgbase"], 1.6
    for y in range(TS):
        for x in range(TS):
            lv, mort = block_level(c2, x, y, seed=11)
            lv = cfg["bgbase"] + (lv - cfg["bgbase"]) * 0.7
            px[x, y] = bg[pick_i(len(bg), lv / (len(bg) - 1), x, y)]
    if k == 1:
        # weathered: cracks + stain
        crack(img, [(3, 2), (5, 5), (4, 8), (6, 11), (6, 13)], bg[0])
        crack(img, [(11, 6), (12, 9), (10, 12)], bg[0])
    elif k == 2:
        # feature: ramparts arrow slit / catacombs bone niche / cathedral filigree panel
        if biome == "ramparts":
            for y in range(2, 14):
                for x in range(7, 9):
                    px[x, y] = bg[0]
            for y in range(6, 9):
                for x in range(5, 11):
                    px[x, y] = bg[0]
            for y in range(2, 14):
                px[9, y] = bg[4]
        elif biome == "catacombs":
            bone = cfg["bone"]
            for y in range(3, 13):
                for x in range(2, 14):
                    r = ((x - 7.5) / 6) ** 2 + (max(0, 6 - y) / 4) ** 2
                    if r <= 1:
                        px[x, y] = bg[0]
            # skulls stacked in the niche, dimmed
            dim = [C("2c2822"), C("3e382e"), C("524a3c")]
            for sx in (3, 8):
                for j, row in enumerate([".111.", "12221", "20202", ".222."]):
                    for i, ch in enumerate(row):
                        if ch != ".":
                            px[sx + i, 8 + j] = bg[0] if ch == "0" else dim[int(ch)]
            for x in range(2, 14):
                px[x, 12] = bg[4]
        else:
            # blind lancet niche with a thin gilded outline
            gold = [C("3a3020"), C("54442a"), C("6e5a34")]
            for y in range(1, 16):
                for x in range(3, 13):
                    dx = abs(x - 7.5)
                    inside = y >= 7 or (dx - 0.5) ** 2 + 0 <= (y - 1) * 3.2 - 1
                    edge = inside and (x in (3, 12) or (y < 7 and not ((dx + 0.5) ** 2 <= (y - 1) * 3.2 - 1)))
                    if inside:
                        px[x, y] = gold[1] if edge else bg[0]
            px[7, 1], px[8, 1] = gold[2], gold[2]
            for x in range(4, 12):
                px[x, 15] = bg[3]
    elif k == 3:
        # vertical pilaster (tiles vertically) centred in the tile
        for y in range(TS):
            for x in range(4, 12):
                c = bg[3]
                if x == 4:
                    c = bg[4]
                elif x == 11:
                    c = bg[1]
                elif x in (6, 9):
                    c = bg[2]
                px[x, y] = c
            px[3, y] = bg[0]
            px[12, y] = bg[0]
    return img


# --------------------------------------------------------------------------- overlays
def deco_chain(cfg):
    img = blank(TS, TS)
    px = img.load()
    ir = cfg["iron"]
    # links alternate: ring (4 tall) / edge-on (4 tall), period 8 -> tiles vertically
    for y0 in (0, 8):
        for (x, y, c) in ((7, 0, 3), (8, 0, 3), (6, 1, 3), (9, 1, 2), (6, 2, 2), (9, 2, 1), (7, 3, 2), (8, 3, 1)):
            px[x, y0 + y] = ir[c]
        for y in range(4, 8):
            px[7, y0 + y] = ir[3] if y < 6 else ir[2]
            px[8, y0 + y] = ir[1]
    return outline(img)


def deco_roots(biome, cfg):
    img = blank(TS, TS)
    px = img.load()
    if biome == "catacombs":
        r = cfg["accent"]
        cols = (r[1], r[2], r[3])
    elif biome == "cathedral":
        r = cfg["accent"]
        cols = (r[0], r[1], r[2])
    else:
        r = ramp("2e2a1e", "4a4630", "6a6440")
        cols = (r[0], r[1], r[2])
    strands = [(3, 0, 11, 0.4), (7, 0, 15, -0.3), (8, 0, 9, 0.6), (12, 0, 13, -0.5), (1, 0, 6, 0.2)]
    for (x0, y0, L, sway) in strands:
        for y in range(L):
            x = round(x0 + math.sin(y * 0.5 + x0) * sway * 2)
            w = 2 if y < L * 0.45 and x0 in (7, 12) else 1
            for i in range(w):
                if 0 <= x + i < 16:
                    px[x + i, y] = cols[2] if i == 0 and y % 3 != 2 else cols[1]
        tipx = round(x0 + math.sin((L - 1) * 0.5 + x0) * sway * 2)
        if 0 <= tipx < 16:
            px[tipx, L - 1] = cols[0]
    # glowing nodes on catacomb roots
    if biome == "catacombs":
        px[7, 4] = cfg["accent"][4]
        px[12, 6] = cfg["accent"][4]
    return outline(img)


def deco_candles(biome, cfg):
    img = blank(TS, TS)
    px = img.load()
    wax = ramp("5e5448", "8e8270", "bcae94", "dcd0b4") if biome != "cathedral" else ramp("6c6a6e", "a4a2a4", "cfccc8", "ece8e0")
    fl = cfg["flame"]
    for (cx, top) in ((3, 9), (6, 6), (9, 10), (12, 8)):
        for y in range(top, 15):
            px[cx, y] = wax[2] if y > top else wax[3]
            px[cx + 1, y] = wax[1]
        # drips + puddle
        px[cx - 1, 14] = wax[1]
        px[cx + 2, 14] = wax[0]
        # flame
        px[cx, top - 1] = fl[3]
        px[cx, top - 2] = fl[2]
        px[cx + 1, top - 1] = fl[1]
        px[cx, top - 3] = fl[1]
    img = outline(img)
    px = img.load()
    for (cx, top) in ((3, 9), (6, 6), (9, 10), (12, 8)):   # flames without outline tops
        px[cx, top - 4] = T
        px[cx - 1, top - 3] = T
        px[cx + 1, top - 3] = T
        px[cx + 1, top - 2] = T
        px[cx - 1, top - 2] = T
    return img


def deco_bones(cfg):
    img = blank(TS, TS)
    px = img.load()
    bone = cfg.get("bone", ramp("4e4638", "7e7460", "aea388", "d6ceb2"))
    # skull
    SK = ["..2222..", ".233332.", "23333332", "31033013", "23333332", ".33.33.."]
    for j, row in enumerate(SK):
        for i, ch in enumerate(row):
            if ch != ".":
                px[4 + i, 9 + j] = K if ch == "0" else bone[int(ch)]
    # long bones
    for x in range(0, 6):
        px[x, 14] = bone[2]
        px[x, 13] = bone[3] if x in (0, 5) else bone[1]
    for x in range(10, 16):
        px[x, 14 - (x - 10) // 3] = bone[2]
    px[10, 13], px[15, 11] = bone[3], bone[3]
    px[12, 15] = bone[1]
    for x in range(1, 15):
        px[x, 15] = bone[1] if h01(x, 15, 3) < 0.5 else bone[0]
    return outline(img)


def deco_tuft(biome, cfg):
    img = blank(TS, TS)
    px = img.load()
    tf = cfg["tuft"]
    # rubble pebbles on the bottom rows
    for (x, w, h) in ((1, 3, 2), (6, 2, 1), (11, 4, 2)):
        for yy in range(h):
            for xx in range(w):
                px[x + xx, 15 - yy] = tf[2] if yy == h - 1 else tf[1]
        px[x, 15 - h + 1] = tf[3]
    if biome == "ramparts":
        blades = [(2, 5), (4, 3), (5, 6), (8, 4), (9, 7), (10, 3), (13, 5), (14, 3)]
        g = ramp("3f3d2a", "5c5a36", "7f7a46", "a39a5c")
    elif biome == "catacombs":
        blades = [(3, 3), (9, 4), (13, 2)]
        g = ramp("2c2420", "4a3c32", "6e5a48", "94806a")
        # pale cave mushrooms
        m = cfg["flame"]
        for (x, y) in ((8, 11), (9, 11), (10, 11), (9, 12), (9, 13), (9, 14)):
            px[x, y] = ramp("3c6a64", "8ad2c0", "cffff0")[1 if y == 11 else 0]
        px[9, 11] = C("cffff0")
    else:
        blades = [(5, 3), (13, 2)]
        g = ramp("2c3a3a", "3e5452", "5a726c", "7e968c")      # pale moss sprigs
        st = cfg["stone"]
        for (x, y, c) in ((8, 14, 7), (9, 14, 6), (10, 14, 5), (8, 15, 6), (9, 15, 5), (10, 15, 4), (9, 13, 8),
                          (3, 15, 6), (4, 15, 5)):
            px[x, y] = st[c]                               # broken marble chunk
        # little white flowers
        for (x, y) in ((5, 9), (12, 10)):
            px[x, y] = C("f0ece0")
            px[x, y + 1] = g[2]
    for (bx, h) in blades:
        for i in range(h):
            x = bx + (1 if i > h * 0.6 and bx % 2 else 0)
            px[x, 15 - i] = g[3] if i == h - 1 else g[2 if i > 1 else 1]
    return outline(img)


def breakable(cfg):
    img = solid_tile(cfg, 0)
    st = cfg["stone"]
    crack(img, [(6, 2), (7, 5), (6, 8), (8, 10), (9, 13)], st[0], st[cfg["deep"].__int__() + 1])
    crack(img, [(7, 5), (10, 6)], st[0])
    return img


# --------------------------------------------------------------------------- tileset
def build_tileset(biome):
    cfg = BIOMES[biome]
    t = []
    for m in range(16):
        t.append(solid_tile(cfg, m))
    for m in range(16):
        t.append(variant_tile(biome, cfg, m))
    t += [platform(biome, cfg, k) for k in ("L", "M", "R", "single")]
    t.append(spikes(biome, cfg))
    t.append(spikes(biome, cfg, down=True))
    t += [bg_wall(biome, cfg, k) for k in range(4)]
    t.append(deco_chain(cfg))
    t.append(deco_roots(biome, cfg))
    t.append(deco_candles(biome, cfg))
    t.append(deco_bones(cfg))
    t.append(breakable(cfg))
    t.append(deco_tuft(biome, cfg))
    assert len(t) == 48
    return t
