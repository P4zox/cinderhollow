"""Tilesets for the v2 biomes `mire` and `crown` (docs/ART_SPEC2.md section F).

Same 48-frame index layout as the v1 tilesets (see env_tiles.py):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8)
16-31  same masks, variant
32-35  one-way platform L / M / R / single      36/37 floor / ceiling spikes
38-41  background wall tiles                    42-45 hanging / roots / light cluster / floor clutter
46     breakable wall (looks like 0)            47 top tuft overlay

Same seamless approach as v1: the interior texture is a pure function of the in-tile pixel on a
16x16 torus (stones / bark plates wrap across the tile edges), so any arrangement of tiles joins
without seams; depth darkening is driven by the distance to the exposed sides only, and all edge
treatment (lip, rim light, outline, chips) is layered on per exposed side.

  mire  : waterlogged dark peat with embedded moss-capped fieldstones, thick sickly-green moss lip
  crown : pale white-gold bark of the fallen Pale Root, wavy fissured plates, gold sap
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline

N, E, S, W = 1, 2, 4, 8
TS = 16


def wrap16(d):
    d %= 16
    return d - 16 if d >= 8 else d


# =========================================================================== MIRE material
M_PEAT = ramp("0b0a08", "13110d", "1b1813", "25211a", "302a20", "3c3427", "4a402f")
M_STONE = ramp("0f1311", "171c19", "202722", "2a322b", "353f35", "434d40", "545e4c", "6b735b", "878c6d")
M_MOSS = ramp("141c10", "1f2a14", "2e3c18", "40521e", "566c26", "70882e", "8ea43a", "b2c458")
M_ROT = ramp("3a1608", "6a2a0c", "a84814", "e07a24", "ffac48", "ffe0a0")
M_BONE = ramp("3a3a2c", "5c5c46", "85826a", "aca88c")
M_WOOD = ramp("15110c", "231c14", "32291c", "443826", "584a32", "6e5e40", "86764e")
M_ROPE = ramp("3a3222", "5a4e34", "7e704c")
M_WATER = ramp("0c1a18", "12272a", "1a3a3a", "2a5652", "4a8076")

# rounded fieldstones on the 16x16 torus: (cx, cy, rx, ry, tone, mossy)
M_STONES = [
    (3.5, 2.5, 3.7, 2.5, 0, 1), (11.8, 4.2, 4.3, 2.7, 1, 1), (6.3, 9.6, 4.4, 2.8, 0, 1),
    (14.8, 11.4, 2.9, 2.5, -1, 0), (1.2, 14.6, 2.9, 1.9, 0, 1), (10.4, 14.9, 3.1, 1.7, -1, 0),
]


def mire_sample(x, y):
    """-> (ramp, level, element_centre or None)"""
    for i, (cx, cy, rx, ry, tone, mossy) in enumerate(M_STONES):
        dx, dy = wrap16(x + 0.5 - cx), wrap16(y + 0.5 - cy)
        nx, ny = dx / rx, dy / ry
        r2 = nx * nx + ny * ny
        if r2 <= 1.0:
            r = math.sqrt(r2)
            lv = 4 + tone + round(-1.5 * (nx * 0.5 + ny * 0.85))
            if r > 0.72 and nx * 0.5 + ny * 0.85 > 0.35:
                lv = 1 + (tone > 0)                                # shadowed lower-right rim
            elif r > 0.7 and nx * 0.5 + ny * 0.85 < -0.45:
                lv += 1                                           # lit upper-left rim
            if h01(x, y, 17) < 0.07:
                lv -= 1                                           # pits
            cen = (x - dx + 0.5, y - dy + 0.5)
            if mossy and ny < -0.2 - 0.25 * h01(x, 3, 20 + i) and r < 0.98:
                ml = 4 + round(-1.2 * ny) - (1 if h01(x, y, 21) < 0.25 else 0)
                return M_MOSS, ml, cen
            return M_STONE, lv, cen
    # peat between the stones: fibrous, contact shadow under-right of stones
    lv = 3
    for (cx, cy, rx, ry, _, _) in M_STONES:
        dx, dy = wrap16(x + 0.5 - cx), wrap16(y + 0.5 - cy)
        nx, ny = dx / (rx + 1.3), dy / (ry + 1.3)
        if nx * nx + ny * ny <= 1.0 and ny > -0.1:
            lv = 1
            break
    if lv == 3:
        f = h01(x // 3 + (y % 3) * 5, y, 31)
        if f > 0.78:
            lv = 4
        elif f < 0.12:
            lv = 2
        if h01(x, y, 32) < 0.05:
            lv = 5
    return M_PEAT, lv, None


# =========================================================================== CROWN material
C_BARK = ramp("17111a", "241a22", "35262c", "4a3732", "62493a", "7e6248", "9c805e", "b99c74",
              "d2b88c", "e4cea4", "f2e2bc", "fcf6e0")
C_SAP = ramp("4a2c10", "7a4c18", "b07a26", "e0ac3c", "fad66a", "fff2b0", "fffff4")
C_LEAF = ramp("5e5a3a", "8a8250", "b8ac6c", "e0d496", "fbf4d0")
C_GRASS = ramp("46584e", "6a8474", "98b29c", "cfe0c8")         # pale silver-sage grass


# bark of a tree lying on its side: long horizontal ridges (4 per tile) split by staggered
# lens-shaped fissures -> interlaced "furrowed bark" read. Everything has period 16 in x and y.
C_LENS = [   # per ridge boundary i (below ridge i): list of (start x, length)
    [(1, 9), (12, 3)], [(6, 8)], [(0, 4), (10, 7)], [(4, 9)],
]


def crown_wave(x, i):
    return round(0.7 * math.sin(2 * math.pi * (x + 5 * i) / 16))


def crown_fissure_at(x, i):
    """-> fissure depth (0 none, 1 thin, 2 deep centre) under ridge i at column x."""
    for (s0, L) in C_LENS[i]:
        t = (x - s0) % 16
        if t < L:
            m = min(t, L - 1 - t)
            return 2 if m >= 2 else 1
    return 0


def crown_fissures(x):
    """y of the fissure rows (used by the sap feature): one per ridge boundary."""
    return [(4 * i + 3 + crown_wave(x, i)) % 16 for i in range(4)]


def crown_sample(x, y):
    bs = crown_fissures(x)
    for i in range(4):
        p = bs[i - 1]
        r = (y - p) % 16
        if 1 <= r <= (bs[i] - p) % 16:
            break
    ly = r - 1                                   # 0 = ridge top row
    f = crown_fissure_at(x, i)
    # element = a 5px chunk of this ridge (staggered per ridge) -> depth follows the bark
    off = (i * 3) % 5
    cx = ((x - off) // 5) * 5 + off + 2.5
    cen = (cx, y - ly + 1.5)
    if y == bs[i]:                               # boundary row under ridge i
        if f == 2:
            return C_BARK, 1, cen
        if f == 1:
            return C_BARK, 3, cen
        return C_BARK, 6 + (1 if h01(x, i, 44) < 0.3 else 0), cen
    if f == 2 and (y + 1) % 16 == bs[i]:
        return C_BARK, 3, cen                    # lens widens upward in the middle
    lv = 8
    if ly == 0:
        lv = 9 if crown_fissure_at(x, (i - 1) % 4) else 10
    elif ly == 1:
        lv = 9
    elif ly >= 3:
        lv = 7
    if h01(x // 2, y, 41) < 0.12:
        lv -= 1                                  # grain streaks
    if h01(x, y, 43) < 0.03:
        lv -= 2
    return C_BARK, lv, cen


# =========================================================================== biome configs
BIOMES = {
    "mire": dict(
        sample=mire_sample,
        steps={id(M_PEAT): (2, 1, 1), id(M_STONE): (2, 2, 1), id(M_MOSS): (3, 2, 1)},
        deep_ramp=M_PEAT,
        lip=[C("a4b44a"), C("6e8430"), C("46581f"), C("222a14")],
        rim=M_STONE[6], rim2=M_MOSS[5],
        bottom_ragged=0.3,
    ),
    "crown": dict(
        sample=crown_sample,
        steps={id(C_BARK): (1, 2, 2)},
        deep_ramp=C_BARK,
        lip=[C("fff8e4"), C("e8dab4"), C("c9a458"), C("5e4632")],
        rim=C_BARK[9], rim2=C_BARK[10],
        bottom_ragged=0.15,
    ),
}


def depth_steps(d, biome="mire"):
    """How many darkening steps at distance d from an exposed side (0..3)."""
    if biome == "crown":            # thicker sunlit crust of pale bark before the heartwood darkens
        return (d > 7) + (d > 11) + (d > 14)
    return (d > 5) + (d > 9) + (d > 12)


# =========================================================================== solid tile
def solid_shape(mask, cfg):
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
    # chips on the side faces where the texture has a dark joint (fissure / peat gap)
    for y in range(4 if mask & N else 1, TS - (3 if mask & S else 1)):
        for side, x in ((W, 0), (E, 15)):
            if mask & side and h01(y, side, 51) < 0.22:
                sh[y][x] = False
    if mask & S:
        for x in range(1, TS - 1):
            if h01(x, 2, 9) < cfg["bottom_ragged"]:
                sh[15][x] = False
    return sh


def solid_tile(biome, mask, seed=0):
    cfg = BIOMES[biome]
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask, cfg)

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
            r, lv, cen = cfg["sample"](x, y)
            if cen is not None:
                d = dfun(*cen) + 3.0 * h01(int(cen[0] * 3), int(cen[1] * 3), 60 + seed)
            else:
                d = dfun(x, y) + 2.5 * (bt(x, y) - 0.5)
            k = depth_steps(d, biome)
            st = cfg["steps"][id(r)]
            if k >= 3 and r is not cfg["deep_ramp"] and biome == "mire":
                # deep interior: stones sink into flat dark peat; keep a faint outline of them
                r, lv = M_PEAT, (1 if lv <= 2 else 2)
            else:
                lv -= sum(st[:k])
                if k >= 2:
                    lv = min(lv, {"mire": 4, "crown": 5}[biome])   # low detail when deep
            # light from upper-left on exposed sides
            if mask & W and x < 3:
                lv += (1, 1, 0)[x]
            if mask & E and 15 - x < 2:
                lv -= 1
            if mask & S and 15 - y < 3:
                lv -= (2, 1, 1)[15 - y]
            px[x, y] = r[int(clamp(lv, 0, len(r) - 1))]
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
            elif o_n and not (mask & N):
                px[x, y] = K
    if mask & N:
        LIP[biome](cfg, img, sh, mask, out)
    return img


def lip_mire(cfg, img, sh, mask, out):
    """Thick moss mat with a ragged hanging fringe."""
    px = img.load()
    lip = cfg["lip"]
    for x in range(TS):
        # fringe length below the 4 lip rows (period 16 -> continuous across tiles)
        L = int(h01(x, 0, 71) * 3.2) + (2 if h01(x // 2, 1, 72) < 0.3 else 0)
        if mask & E and x >= 14 or mask & W and x <= 1:
            L = min(L, 1)
        for y in range(0, 4 + L):
            if y >= TS or not sh[y][x]:
                continue
            if y < 4:
                c = lip[y]
                if y == 0 and h01(x, 0, 73) < 0.25:
                    c = M_MOSS[6]
                if y == 1 and h01(x, 1, 74) < 0.2:
                    c = lip[0]
                if y == 2 and h01(x, 2, 75) < 0.18:
                    c = M_MOSS[5]
            else:
                c = M_MOSS[2] if y < 3 + L else M_MOSS[1]
                if y == 4 and h01(x, 4, 76) < 0.3:
                    c = M_MOSS[3]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else lip[2]
            elif (mask & W and x == 0) or out(x, y, -1, 0):
                c = lip[0] if y < 2 else lip[1]
            px[x, y] = c
    if mask & E:
        px[14, 1] = lip[1]
        px[13, 0] = lip[1]
    # a few bright moss tips / spore dots on the top
    for x in range(TS):
        if sh[0][x] and h01(x, 9, 77) < 0.12 and px[x, 0] != K:
            px[x, 0] = M_MOSS[7]


def lip_crown(cfg, img, sh, mask, out):
    """Sun-bleached bark crest: cream highlight, golden lichen band, shaded underside."""
    px = img.load()
    lip = cfg["lip"]
    for y in range(4):
        for x in range(TS):
            if not sh[y][x]:
                continue
            c = lip[y]
            if y == 0 and h01(x, 0, 81) < 0.2:
                c = lip[1]
            if y == 2 and h01(x, 2, 82) < 0.3:
                c = C_SAP[4] if h01(x, 3, 83) < 0.4 else C_SAP[2]
            if y == 3 and h01(x, 3, 84) < 0.3:
                c = C_BARK[5]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else lip[2]
            elif (mask & W and x == 0) or out(x, y, -1, 0):
                c = lip[0] if y < 2 else lip[1]
            px[x, y] = c
    if mask & E:
        px[14, 1] = lip[1]
        px[13, 0] = lip[1]


LIP = {"mire": lip_mire, "crown": lip_crown}


# =========================================================================== variant features
def _ok(px, x, y, lo):
    return 0 <= x < TS and lo <= y < 15 and px[x, y][3] and px[x, y] != K


def is_deep(c, r):
    return c in r[:3]


def polyline(pts):
    out = []
    for a in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[a], pts[a + 1]
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            p = (round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n))
            if not out or out[-1] != p:
                out.append(p)
    return out


def f_fungus(img, mask, k, lo):
    """Rot-orange bracket fungi: little glowing half-moon shelves stacked on the face."""
    px = img.load()
    bx, by = (2 + (k * 5) % 8), max(lo + 2, 7 + k % 3)
    SHELF = {5: [".454.", "43332", ".1110"], 4: [".45.", "4332", ".110"], 3: ["45.", "332", "10."]}
    for j, (dx, dy, w) in enumerate(((0, 0, 5), (4, 3, 4), (1, 5, 3))[: 2 + k % 2]):
        for r, row in enumerate(SHELF[w]):
            for i, ch in enumerate(row):
                X, Y = bx + dx + i, by + dy + r
                if ch != "." and _ok(px, X, Y, lo):
                    px[X, Y] = M_PEAT[0] if ch == "0" else M_ROT[int(ch)] if ch != "5" else M_ROT[5]


def f_roots(img, mask, k, lo):
    """Dark wet roots snaking through the peat, glossy highlight on top."""
    px = img.load()
    paths = [[(0, 7), (4, 8), (7, 7), (10, 9), (15, 10)], [(2, 15), (4, 12), (8, 11), (12, 12), (15, 11)],
             [(0, 11), (3, 10), (6, 12), (9, 12), (13, 9), (15, 9)]]
    pts = [(x, max(lo + 1, y)) for x, y in paths[k % 3]]
    for (x, y) in polyline(pts):
        if _ok(px, x, y, lo):
            deep = px[x, y] in M_PEAT[:2] or px[x, y] in M_STONE[:2]
            px[x, y] = M_WOOD[1] if deep else M_WOOD[3]
            if _ok(px, x, y - 1, lo) and not deep:
                px[x, y - 1] = M_WOOD[5] if (x % 3) else M_WOOD[4]
            if _ok(px, x, y + 1, lo):
                px[x, y + 1] = M_WOOD[0]


def f_skull(img, mask, k, lo):
    """Half-sunken, moss-stained skull."""
    px = img.load()
    sx, sy = 4 + (k * 3) % 7, max(lo + 3, 8 + k % 3)
    SK = [".122.", "12332", "30303", ".232."]
    for j, row in enumerate(SK):
        for i, ch in enumerate(row):
            X, Y = sx + i, sy + j
            if ch != "." and _ok(px, X, Y, lo):
                px[X, Y] = {"0": M_PEAT[0], "1": M_MOSS[4], "2": M_BONE[1], "3": M_BONE[2]}[ch]
    for i in range(-1, 6):
        if _ok(px, sx + i, sy + 4, lo):
            px[sx + i, sy + 4] = M_PEAT[1]


def f_seep(img, mask, k, lo):
    """Water seeping out of a crack: dark wet streak with a teal glint."""
    px = img.load()
    x0 = 3 + (k * 7) % 10
    y0 = max(lo + 1, 5)
    for y in range(y0, 15):
        x = x0 + (1 if (y - y0) > 5 else 0)
        if _ok(px, x, y, lo):
            px[x, y] = M_WATER[1] if y % 4 else M_WATER[3]
        if _ok(px, x + 1, y, lo) and y > y0 + 2:
            px[x + 1, y] = M_PEAT[1]
    if _ok(px, x0, y0, lo):
        px[x0, y0] = M_WATER[4]


def f_moss_patch(img, mask, k, lo):
    px = img.load()
    cx, cy = 4 + (k * 5) % 9, max(lo + 3, 9 + k % 4)
    for y in range(cy - 2, cy + 3):
        for x in range(cx - 4, cx + 5):
            d = ((x - cx) / 4.2) ** 2 + ((y - cy) / 2.3) ** 2
            if d < 1 and h01(x, y, 90 + k) < 0.85 and _ok(px, x, y, lo):
                px[x, y] = M_MOSS[4 if y < cy else 3] if d < 0.6 else M_MOSS[2]


def f_sapvein(img, mask, k, lo):
    """Fissures brimming with glowing gold sap (the Root's grace) + a welling bead."""
    px = img.load()
    rows = [(k + 1) % 4, (k + 3) % 4] if k % 3 == 0 else [(k + 1) % 4]
    for i in rows:
        for x in range(TS):
            f = crown_fissure_at(x, i)
            if not f:
                continue
            y = crown_fissures(x)[i]
            for yy in ([y, y - 1] if f == 2 else [y]):
                if not _ok(px, x, yy, lo):
                    continue
                dim = px[x, yy] in C_BARK[:3] and px[x, yy] != C_BARK[1] and px[x, yy] != C_BARK[3]
                deep = px[x, yy] in (C_BARK[0],)
                if deep:
                    px[x, yy] = C_SAP[1]
                else:
                    px[x, yy] = C_SAP[4] if (f == 2 and yy == y) else C_SAP[3] if f == 2 else C_SAP[2]
    # glowing node on the first lens
    i = rows[0]
    s0, L = C_LENS[i][0]
    nx = (s0 + L // 2) % 16
    y = crown_fissures(nx)[i]
    if mask and lo <= y < 14:
        for (dx, dy, c) in ((0, 0, C_SAP[4]), (0, 1, C_SAP[6]), (0, 2, C_SAP[4]), (1, 0, C_SAP[3]), (0, 3, C_SAP[2])):
            if _ok(px, nx + dx, y + dy, lo):
                px[nx + dx, y + dy] = c


def f_knot(img, mask, k, lo):
    """Eye-shaped bark knot with concentric rings."""
    px = img.load()
    cx, cy = 5 + (k * 3) % 7, max(lo + 3, 10 - k % 2)
    for y in range(cy - 3, cy + 4):
        for x in range(cx - 4, cx + 5):
            nx, ny = (x - cx) / 4.2, (y - cy) / 2.6
            d = math.sqrt(nx * nx + ny * ny)
            if d < 1 and _ok(px, x, y, lo):
                if d < 0.3:
                    c = C_BARK[2]
                elif d < 0.55:
                    c = C_BARK[5] if ny < 0 else C_BARK[4]
                elif d < 0.8:
                    c = C_BARK[3]
                else:
                    c = C_BARK[8] if ny < 0 else C_BARK[5]
                px[x, y] = c
    if _ok(px, cx, cy, lo):
        px[cx, cy] = C_SAP[3]


def f_lichen(img, mask, k, lo):
    px = img.load()
    L = ramp("7e8a6a", "a6b08a", "d0d6b0")
    for (x0, y0) in ((2 + k % 4, max(lo + 2, 6)), (9 + k % 3, max(lo + 3, 11))):
        for y in range(y0 - 1, y0 + 2):
            for x in range(x0 - 2, x0 + 3):
                if h01(x, y, 97 + k) < 0.6 and abs(x - x0) + abs(y - y0) < 3 and _ok(px, x, y, lo):
                    if px[x, y] in C_BARK[:3]:
                        continue
                    px[x, y] = L[2] if (y < y0) else L[1] if h01(x, y, 98) < 0.6 else L[0]


def f_crack_crown(img, mask, k, lo):
    px = img.load()
    pts = [[(4, 5), (6, 7), (6, 9), (8, 11), (9, 13)], [(11, 4), (10, 6), (11, 8), (9, 10)],
           [(3, 9), (5, 10), (7, 10), (8, 12)]][k % 3]
    for (x, y) in polyline([(x, max(lo + 1, y)) for x, y in pts]):
        if _ok(px, x, y, lo):
            px[x, y] = C_BARK[1]
            if _ok(px, x - 1, y, lo) and px[x - 1, y] not in C_BARK[:3]:
                px[x - 1, y] = C_BARK[9]


FEATURES = {
    "mire": [[f_fungus], [f_roots, f_moss_patch], [f_skull], [f_seep, f_roots], [f_moss_patch, f_fungus]],
    "crown": [[f_sapvein], [f_knot], [f_lichen, f_crack_crown], [f_sapvein, f_lichen], [f_knot, f_sapvein]],
}


def variant_tile(biome, mask):
    img = solid_tile(biome, mask, seed=5)
    k = (mask * 7 + 1) % 5
    lo = 5 if mask & N else 1
    if biome == "mire" and mask & N:
        lo = 8
    feats = FEATURES[biome][k]
    if mask == 0:
        feats = {"mire": [f_roots], "crown": [f_sapvein]}[biome]
    for f in feats:
        f(img, mask, mask // 2 + k, lo)
    return img


# =========================================================================== platforms
def platform_mire(kind):
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    wd = M_WOOD
    for x in range(TS):
        if (left and x == 0) or (right and x == 15):
            continue
        seam = x in (5, 11)
        px[x, 0] = (M_MOSS[5] if h01(x, 0, 101) < 0.45 else wd[6]) if not seam else wd[3]
        px[x, 1] = wd[5] if not seam else wd[2]
        px[x, 2] = wd[4] if h01(x, 2, 102) > 0.3 else wd[3]
        px[x, 3] = wd[2] if h01(x, 3, 103) > 0.2 else wd[1]
        px[x, 4] = K
    for y in range(1, 4):
        if left:
            px[0, y] = K
        if right:
            px[15, y] = K
    # moss mats dripping from the planks
    for x in range(1, 15):
        L = int(h01(x, 5, 104) ** 2 * 5)
        if (left and x < 3) or (right and x > 12):
            L = 0
        for y in range(5, 5 + L):
            px[x, y] = M_MOSS[3] if y < 4 + L else M_MOSS[2]
    # rope lashings (+ frayed hanging end) near the ends
    for sx in ([2] if left else []) + ([13] if right else []) + ([8] if kind == "M" else []):
        for y in range(0, 4):
            px[sx, y] = M_ROPE[2] if y % 2 == 0 else M_ROPE[1]
        for y in range(5, 9):
            px[sx, y] = M_ROPE[1] if y < 8 else M_ROPE[0]
    return outline(img)


def platform_crown(kind):
    """A horizontal limb of pale bark; cut ends show golden growth rings."""
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    b = C_BARK
    for x in range(TS):
        if (left and x == 0) or (right and x == 15):
            continue
        px[x, 0] = b[11] if h01(x, 0, 111) > 0.2 else b[10]
        px[x, 1] = b[9]
        px[x, 2] = C_SAP[3] if h01(x, 2, 112) < 0.35 else b[7]
        px[x, 3] = b[5] if h01(x, 3, 113) > 0.3 else b[4]
        px[x, 4] = K
        if (x + 2) % 7 == 0:
            px[x, 2] = b[4]           # bark fissure
    for (edge, x0) in ((left, 1), (right, 14)):
        if edge:                        # cut end: growth rings
            for y in range(0, 4):
                px[x0, y] = C_SAP[4] if y in (1, 2) else C_SAP[2]
            px[x0 - 1 if x0 == 1 else x0 + 1, 1] = K
    # small hanging white-gold leaves
    for (lx, L) in (((4, 3), (10, 2)) if kind == "M" else ((6, 3),) if kind == "single" else
                    ((9, 2),) if kind == "L" else ((5, 3),)):
        for y in range(5, 5 + L):
            px[lx, y] = C_LEAF[2] if y < 4 + L else C_LEAF[4]
        px[lx + 1, 4 + L] = C_LEAF[3]
    return outline(img)


# =========================================================================== spikes
def spikes(biome, down=False):
    img = blank(TS, TS)
    px = img.load()
    if biome == "mire":     # sharpened bleached-deadwood stakes, rot-stained at the base
        dark, mid, lit, tip, tip2 = C("4e4a3c"), C("8a8470"), C("bdb69a"), C("dcd6bc"), C("f4f0dc")
        SP = [(2, 5, 1.5, -0.10), (5.5, 2, 1.9, 0.08), (9.5, 4, 1.7, -0.06), (13.2, 1, 1.9, 0.1)]
    else:                   # crystallised sap thorns
        dark, mid, lit, tip, tip2 = C_SAP[1], C_SAP[3], C_SAP[5], C_SAP[6], C_SAP[6]
        SP = [(2, 4, 1.5, 0), (6, 1, 2.0, 0), (10, 5, 1.6, 0), (13.5, 2, 1.8, 0)]
    for (cx, ty, hw0, lean) in SP:
        for y in range(ty, 14):
            t = (y - ty) / (13 - ty)
            hw = 0.25 + hw0 * t
            ccx = cx + lean * (13 - y)
            for x in range(TS):
                dx = x + 0.5 - ccx
                if abs(dx) <= hw:
                    c = mid
                    if dx < 0 and abs(dx) < hw * 0.55 + 0.3:
                        c = lit
                    if dx >= hw * 0.35:
                        c = dark
                    if y <= ty + 1:
                        c = tip2 if y == ty else tip
                    elif biome == "mire" and y >= 10 and c != dark:
                        c = M_WOOD[4] if c == mid else mid          # wet rot stain near the mud
                    px[x, y] = c
        if biome == "mire":            # side barbs
            by = ty + 5
            if by < 12:
                bx = int(ccx + (1.5 if int(cx) % 2 else -2))
                if 0 <= bx < TS and px[bx, by][3] == 0:
                    px[bx, by] = lit
    img = outline(img)
    px = img.load()
    base = (M_PEAT, M_MOSS) if biome == "mire" else (C_BARK, C_SAP)
    for x in range(TS):
        px[x, 15] = K
        if biome == "mire":
            px[x, 14] = M_MOSS[3] if h01(x, 14, 4) < 0.5 else M_PEAT[4]
            if h01(x, 13, 4) < 0.35 and px[x, 13] == T:
                px[x, 13] = M_MOSS[4]
                if px[x, 12] == T:
                    px[x, 12] = K
        else:
            px[x, 14] = C_BARK[8] if h01(x, 14, 4) < 0.6 else C_BARK[6]
            if h01(x, 13, 4) < 0.3 and px[x, 13] == T:
                px[x, 13] = C_BARK[9]
                if px[x, 12] == T:
                    px[x, 12] = K
    if down:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


# =========================================================================== background walls
M_BG = ramp("0b0e0d", "0f1412", "141a17", "19201c", "1e2621", "242d27")
C_BG = ramp("1a151c", "221b24", "2b222c", "352a34", "40333c", "4c3d44")


def bg_wall(biome, k):
    img = blank(TS, TS)
    px = img.load()
    bg = M_BG if biome == "mire" else C_BG
    samp = mire_sample if biome == "mire" else crown_sample
    for y in range(TS):
        for x in range(TS):
            r, lv, _ = samp(x, y)
            # compress the material to the dim bg ramp (low contrast)
            n = lv / (len(r) - 1)
            v = 1.2 + n * 3.2
            if biome == "crown":
                v = 1.0 + n * 3.6
            i = int(v + bt(x, y) * 0.0 + 0.5)
            px[x, y] = bg[max(0, min(len(bg) - 1, i))]
    if k == 1:
        for pts in ([(3, 2), (5, 5), (4, 8), (6, 11), (6, 13)], [(11, 6), (12, 9), (10, 12)]):
            for (x, y) in polyline(pts):
                px[x, y] = bg[0]
        if biome == "mire":            # dark wet stain running down
            for y in range(4, 16):
                for x in (8, 9):
                    if h01(x, y, 121) < 0.7:
                        px[x, y] = bg[1]
    elif k == 2:
        if biome == "mire":
            # rotted round hollow with a curtain of hanging moss
            for y in range(2, 15):
                for x in range(2, 14):
                    if ((x - 7.5) / 5.5) ** 2 + ((y - 8.5) / 6.2) ** 2 <= 1:
                        px[x, y] = bg[0]
            mz = [C("1a2414"), C("22301a"), C("2c3c1e")]
            for x in range(3, 13):
                L = 3 + int(h01(x, 0, 122) * 7)
                for y in range(3, 3 + L):
                    if ((x - 7.5) / 5.5) ** 2 + ((y - 8.5) / 6.2) ** 2 <= 1 and (x % 2 == 0 or y < 5):
                        px[x, y] = mz[2] if y < 4 else mz[1] if y < 2 + L else mz[0]
        else:
            # sap-lit hollow: a lens of glowing heartwood
            for y in range(1, 15):
                for x in range(3, 13):
                    d = ((x - 7.5) / 4.8) ** 2 + ((y - 8) / 6.6) ** 2
                    if d <= 1:
                        px[x, y] = bg[0] if d > 0.55 else C("3a2616") if d > 0.25 else C("5c3a18")
            px[7, 8], px[8, 7] = C("8a5a1e"), C("8a5a1e")
    elif k == 3:
        # vertical pile / root column centred in the tile (tiles vertically)
        col = [bg[0], bg[4], bg[3], bg[3], bg[2], bg[3], bg[2], bg[1], bg[0]]
        for y in range(TS):
            for i, c in enumerate(col):
                x = 4 + i
                cc = c
                if 1 <= i <= 7 and h01(x, y // 3, 123) < 0.15:
                    cc = bg[1]
                px[x, y] = cc
            if biome == "mire" and y % 8 == 3:
                for x in range(5, 12):
                    px[x, y] = C("2a2618") if x % 2 else C("3a3422")   # rope binding
    return img


# =========================================================================== overlays
def deco_hang(biome):
    """42: hanging strand that tiles vertically (mire: moss-hung rusty chain, crown: gilded chain)."""
    img = blank(TS, TS)
    px = img.load()
    if biome == "mire":
        ir = ramp("1a1612", "3a2e22", "5a4632", "7a6044")    # rusted iron
    else:
        ir = [C_SAP[1], C_SAP[2], C_SAP[3], C_SAP[5]]
    for y0 in (0, 8):
        for (x, y, c) in ((7, 0, 3), (8, 0, 3), (6, 1, 3), (9, 1, 2), (6, 2, 2), (9, 2, 1), (7, 3, 2), (8, 3, 1)):
            px[x, y0 + y] = ir[c]
        for y in range(4, 8):
            px[7, y0 + y] = ir[3] if y < 6 else ir[2]
            px[8, y0 + y] = ir[1]
    if biome == "mire":             # moss tatters hanging off the links
        for (x, y, L) in ((9, 2, 4), (5, 9, 5), (10, 11, 3)):
            for i in range(L):
                px[x + (i // 3) * (1 if x > 7 else -1), y + i] = M_MOSS[3] if i < L - 1 else M_MOSS[2]
    else:                           # a petal caught on a link
        px[10, 5], px[11, 5], px[10, 6] = C_LEAF[4], C_LEAF[3], C_LEAF[2]
    return outline(img)


def deco_roots(biome):
    img = blank(TS, TS)
    px = img.load()
    if biome == "mire":
        cols = (M_WOOD[1], M_WOOD[3], M_WOOD[4])
    else:
        cols = (C_BARK[6], C_BARK[8], C_BARK[10])
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
            if biome == "crown":        # glowing sap droplet at the tip
                px[tipx, min(15, L)] = C_SAP[5]
            elif (x0 % 2):
                px[tipx, min(15, L)] = M_WATER[4]      # water drip
    if biome == "mire":
        for (x, y) in ((7, 3), (12, 5), (3, 2)):
            px[x, y] = M_MOSS[4]
    return outline(img)


def deco_light(biome):
    """44: light-source cluster (mire: glowing rot-orange mushrooms, crown: sap-bulb blossoms)."""
    img = blank(TS, TS)
    px = img.load()
    if biome == "mire":
        stem = ramp("4a4236", "7a6e58", "a89a7c")
        for (cx, top, capw) in ((4, 8, 2), (8, 5, 3), (12, 9, 2), (10, 11, 1)):
            for y in range(top + 1, 15):
                px[cx, y] = stem[1] if y > top + 1 else stem[2]
            for dx in range(-capw, capw + 1):
                px[cx + dx, top] = M_ROT[3] if dx < capw else M_ROT[2]
                if abs(dx) < capw:
                    px[cx + dx, top - 1] = M_ROT[4] if dx <= 0 else M_ROT[3]
            px[cx - capw + 1 if capw > 1 else cx, top - 1] = M_ROT[5]
            px[cx, top + 1] = M_ROT[1]
        for x in range(2, 14):
            px[x, 15] = M_MOSS[3] if x % 3 else M_MOSS[2]
        img = outline(img)
        px = img.load()
        for (x, y) in ((6, 3), (11, 6), (3, 5)):   # floating spores (no outline)
            px[x, y] = M_ROT[4]
    else:
        stem = [C_LEAF[0], C_LEAF[1], C_LEAF[2]]
        for (cx, top) in ((4, 7), (8, 4), (12, 8)):
            for y in range(top + 2, 15):
                px[cx, y] = stem[1] if y % 3 else stem[2]
            # bulb of glowing sap: 3x3 with bright core
            for dy in range(3):
                for dx in range(-1, 2):
                    px[cx + dx, top + dy] = C_SAP[4] if (dx, dy) != (1, 2) else C_SAP[2]
            px[cx, top + 1] = C_SAP[6]
            px[cx - 1, top] = C_SAP[5]
            px[cx + 1, top + 3] = C_LEAF[2]
            px[cx - 1, top + 4] = C_LEAF[3]
        for x in range(2, 14):
            px[x, 15] = C_BARK[8] if x % 3 else C_BARK[6]
        img = outline(img)
        px = img.load()
        for (x, y) in ((6, 2), (11, 4), (2, 5)):
            px[x, y] = C_SAP[5]
    return img


def deco_clutter(biome):
    """45: floor clutter (mire: bones sunk in moss with a lily, crown: a fallen knight's gilded helm)."""
    img = blank(TS, TS)
    px = img.load()
    if biome == "mire":
        bone = M_BONE
        SK = ["..2222..", ".233332.", "23333332", "31033013", "23333332", ".33.33.."]
        for j, row in enumerate(SK):
            for i, ch in enumerate(row):
                if ch != ".":
                    px[4 + i, 9 + j] = K if ch == "0" else bone[int(ch)]
        for (x, y) in ((5, 9), (6, 9), (4, 10), (5, 10)):
            px[x, y] = M_MOSS[4]                              # moss cap on the skull
        for x in range(10, 16):
            px[x, 14 - (x - 10) // 3] = bone[2]
        px[10, 13], px[15, 11] = bone[3], bone[3]
        for x in range(0, 16):
            px[x, 15] = M_MOSS[3] if h01(x, 15, 3) < 0.5 else M_MOSS[2]
        for x in range(0, 4):
            px[x, 14] = M_MOSS[4] if x % 2 else M_MOSS[3]
        # a pale bog-lily
        px[2, 12], px[1, 13], px[3, 13], px[2, 13] = C("e6e2c8"), C("c8c4a8"), C("c8c4a8"), M_ROT[4]
    else:
        g = C_SAP
        st = ramp("3c3a44", "5e5c68", "8a8894", "b8b6c0")
        # helm lying on its side, visor slit dark, gilded crest
        HM = ["...3333..", "..322223.", ".32211112", "3211K1112", "3211K1111", ".2111111.", "..11111.."]
        for j, row in enumerate(HM):
            for i, ch in enumerate(row):
                if ch != ".":
                    px[3 + i, 8 + j] = K if ch == "K" else st[int(ch)]
        for i in range(5):
            px[4 + i, 7 - (1 if i in (1, 2) else 0)] = g[3] if i % 2 else g[4]
        for x in range(0, 16):
            px[x, 15] = C_BARK[8] if h01(x, 15, 3) < 0.5 else C_BARK[6]
        # scattered petals
        for (x, y) in ((1, 14), (12, 14), (14, 13), (13, 11)):
            px[x, y] = C_LEAF[4]
            px[x + 1, y] = C_LEAF[3]
    return outline(img)


def deco_tuft(biome):
    img = blank(TS, TS)
    px = img.load()
    if biome == "mire":
        # reeds + cattails + moss clump
        for (bx, h, lean) in ((2, 7, 0), (4, 11, 1), (6, 6, -1), (9, 12, 0), (11, 8, 1), (13, 5, 0)):
            for i in range(h):
                x = bx + (lean if i > h * 0.6 else 0)
                px[x, 15 - i] = M_MOSS[5] if i > h - 3 else M_MOSS[3] if i > 1 else M_MOSS[2]
        for (bx, h) in ((4, 11), (9, 12)):              # cattail heads
            x = bx + (1 if bx == 4 else 0)
            for dy in range(3):
                px[x, 15 - h - dy] = M_WOOD[4] if dy else M_WOOD[5]
            px[x, 15 - h - 3] = M_MOSS[3]
        for x in range(0, 16):
            if h01(x, 15, 131) < 0.7:
                px[x, 15] = M_MOSS[4] if x % 3 else M_MOSS[3]
    else:
        G = C_GRASS
        blades = [(2, 4), (3, 6), (5, 3), (8, 5), (10, 7), (11, 4), (14, 5)]
        for (bx, h) in blades:
            for i in range(h):
                x = bx + (1 if i > h * 0.6 and bx % 2 else 0)
                px[x, 15 - i] = G[3] if i == h - 1 else G[2 if i > 1 else 1]
        for (x, y) in ((4, 9), (12, 8)):                # white flowers with gold hearts
            px[x, y] = C_LEAF[4]
            px[x - 1, y + 1], px[x + 1, y + 1], px[x, y + 2] = C_LEAF[4], C_LEAF[4], C_LEAF[4]
            px[x, y + 1] = C_SAP[4]
            px[x, y + 3] = G[1]
        for (x, y) in ((7, 15), (8, 15), (13, 15)):
            px[x, y] = C_LEAF[4]
    return outline(img)


def breakable(biome):
    img = solid_tile(biome, 0)
    px = img.load()
    r = M_PEAT if biome == "mire" else C_BARK
    for pts in ([(6, 2), (7, 5), (6, 8), (8, 10), (9, 13)], [(7, 5), (10, 6)]):
        for (x, y) in polyline(pts):
            px[x, y] = r[0]
            if (x + 1, y) not in pts and x + 1 < 16 and y % 2 == 0:
                px[x + 1, y] = r[3] if biome == "mire" else r[4]
    return img


# =========================================================================== tileset
def build_tileset(biome):
    t = [solid_tile(biome, m) for m in range(16)]
    t += [variant_tile(biome, m) for m in range(16)]
    plat = platform_mire if biome == "mire" else platform_crown
    t += [plat(k) for k in ("L", "M", "R", "single")]
    t.append(spikes(biome))
    t.append(spikes(biome, down=True))
    t += [bg_wall(biome, k) for k in range(4)]
    t.append(deco_hang(biome))
    t.append(deco_roots(biome))
    t.append(deco_light(biome))
    t.append(deco_clutter(biome))
    t.append(breakable(biome))
    t.append(deco_tuft(biome))
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t
