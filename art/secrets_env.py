"""Tilesets + parallax for agent X's biomes (standard 48-tile index layout, docs/ART_SPEC.md section 6).

hermit : a mountain cave above the cliffs -- weathered warm-grey rock in rough boulder courses, moss on the lips,
         roots, a few carved prayer marks; wooden plank walkways lashed with rope; butter lamps.
ember  : the hollow beneath the Crown -- black basalt split by glowing ember veins, ash drifts on the lips,
         obsidian ledges and shard spikes; burning roots of the Pale Root hanging from above.
Seamless: the interior texture is a pure function of the pixel on a 16x16 torus (voronoi boulders), depth
darkening depends only on the distance to exposed sides, edges are layered on per exposed side.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline, pick, Canvas, smooth
from env_bg import tn, wrapdx

N, E, S, W_ = 1, 2, 4, 8
TS = 16

BIOMES = {
    "hermit": dict(
        ST=ramp("0b090b", "141114", "1d181b", "272023", "322a2b", "3e3434", "4b3f3d", "5a4c48", "6b5b54", "7f6d63", "978577"),
        LIP=[C("a89a7e"), C("7c7058"), C("4e4638"), C("1c1614")],
        MOSS=ramp("141a0e", "222c14", "34401c", "4a5626", "647032"),
        GLOW=ramp("5a3c14", "8a6224", "c09440", "ecc870"),
        BG=ramp("060506", "0a0809", "0e0b0d", "130f11", "181315", "1e181a", "251e20"),
        seeds=[(3.1, 3.4), (11.2, 2.2), (7.4, 9.6), (14.6, 11.8), (1.8, 13.4)]),
    "ember": dict(
        ST=ramp("060406", "0c080a", "120c0e", "181113", "1f1618", "271c1d", "302224", "3a2a2b", "463334", "553d3d", "684a48"),
        LIP=[C("8a7f78"), C("5e5652"), C("3a3234"), C("140c0c")],
        MOSS=ramp("2a2224", "3e3536", "554b4a", "6e6462", "8a807c"),     # ash drifts
        GLOW=ramp("5a1408", "a02a0c", "e0561a", "ff9a3a", "ffd88a"),
        BG=ramp("050304", "080506", "0c0708", "10090a", "150c0c", "1a0f0f", "201212"),
        seeds=[(2.6, 2.8), (9.8, 4.2), (6.0, 11.0), (13.4, 12.4), (15.0, 5.6)]),
}


def wrap16(d):
    d %= 16
    return d - 16 if d >= 8 else d


def voronoi(B, x, y):
    """-> (cell index, dist to nearest, dist to 2nd) on the 16x16 torus."""
    best = []
    for i, (sx, sy) in enumerate(B["seeds"]):
        dx, dy = wrap16(x + .5 - sx), wrap16(y + .5 - sy)
        best.append((math.hypot(dx * 0.9, dy * 1.25), i))
    best.sort()
    return best[0][1], best[0][0], best[1][0]


def solid_shape(mask):
    sh = [[True] * TS for _ in range(TS)]
    cut = []
    if mask & N and mask & W_:
        cut += [(0, 0), (1, 0), (0, 1)]
    if mask & N and mask & E:
        cut += [(15, 0), (14, 0), (15, 1)]
    if mask & S and mask & W_:
        cut += [(0, 15), (1, 15), (0, 14)]
    if mask & S and mask & E:
        cut += [(15, 15), (14, 15), (15, 14)]
    for x, y in cut:
        sh[y][x] = False
    if mask & S:
        for x in range(2, TS - 2):
            if h01(x, 2, 9) < 0.2:
                sh[15][x] = False
    for side, x in ((W_, 0), (E, 15)):
        if mask & side:
            for y in range(2, 14):
                if h01(y, side, 51) < 0.14:
                    sh[y][x] = False
    return sh


def solid_tile(B, mask, variant=False, biome="hermit"):
    ST = B["ST"]
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask)

    def dist(x, y):
        ds = [99]
        if mask & N: ds.append(y)
        if mask & S: ds.append(15 - y + 3)
        if mask & W_: ds.append(x + 1)
        if mask & E: ds.append(15 - x + 1)
        return min(ds)

    def out(x, y, dx, dy):
        X, Y = x + dx, y + dy
        if X < 0: return bool(mask & W_)
        if X >= TS: return bool(mask & E)
        if Y < 0: return bool(mask & N)
        if Y >= TS: return bool(mask & S)
        return not sh[Y][X]

    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            ci, d1, d2 = voronoi(B, x, y)
            edge = d2 - d1
            sx, sy = B["seeds"][ci]
            tone = (0, 1, -1, 1, 0)[ci % 5]
            lv = 6 + tone
            # boulder shading: lit upper-left of each stone
            dx, dy = wrap16(x + .5 - sx), wrap16(y + .5 - sy)
            lv += 1 if (dx + dy) < -2.2 else (-1 if (dx + dy) > 2.6 else 0)
            if edge < 0.9:
                lv = 2                                    # the crack between stones
            elif edge < 1.6:
                lv -= 1
            r = h01(x, y, 17 + ci)
            if r < 0.07: lv -= 1
            elif r > 0.95: lv += 1
            d = dist(x, y) + 2.0 * h01(int(sx * 3), int(sy * 3), 60)
            k = (d > 5) + (d > 9) + (d > 12)
            lv -= (0, 2, 3, 4)[k]
            if k >= 2:
                lv = min(lv, 3) if edge >= 0.9 else 1         # deep rock: quiet, almost flat
            if mask & S and 15 - y < 3:
                lv -= (2, 1, 1)[15 - y]
            if mask & W_ and x < 2:
                lv += 1
            px[x, y] = ST[int(clamp(lv, 0, len(ST) - 1))]
            # ember veins glowing inside the cracks (ember biome, near exposed faces)
            if biome == "ember" and edge < 0.7 and k == 0 and h01(ci, int(sx), 5) < 0.5:
                px[x, y] = B["GLOW"][1]
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, -1, 0) and not (mask & N and y < 3):
                px[x, y] = ST[8]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & N:
        LIP, MOSS = B["LIP"], B["MOSS"]
        for x in range(TS):
            for y in range(3):
                if not sh[y][x]:
                    continue
                c = LIP[y]
                if out(x, y, 1, 0):
                    c = K if y else LIP[1]
                px[x, y] = c
            # moss / ash drift lying on the lip, hanging a little over the edge
            m = 2 + int(1.6 * math.sin(x * 0.8 + 1.3) + 1.2 * h01(x, 1, 33))
            for y in range(0, max(0, m)):
                if sh[y][x] and not out(x, y, 1, 0):
                    px[x, y] = MOSS[4 if y == 0 else 3 if y == 1 else 2]
            if h01(x, 3, 34) < 0.25 and sh[3][x] and px[x, 3] != K:
                px[x, 3] = MOSS[1]
        if biome == "ember":
            for x in range(TS):
                if sh[4][x] and px[x, 4] != K and h01(x, 4, 44) < 0.35:
                    px[x, 4] = B["GLOW"][2]
    if variant and mask:
        feature(B, img, mask, biome)
    return img


def feature(B, img, mask, biome):
    px = img.load()
    lo = 5 if mask & N else 1
    k = (mask * 7 + 3) % 4

    def ok(x, y):
        return 0 <= x < TS and lo <= y < 15 and px[x, y][3] and px[x, y] != K
    if biome == "hermit":
        if k in (0, 2):                                     # a root threading through the stone
            x = 3 + (mask * 5) % 9
            for y in range(lo, 15):
                xx = x + int(1.5 * math.sin(y * 0.6 + mask))
                if ok(xx, y):
                    px[xx, y] = C("5e4428") if y % 3 else C("7c5a34")
                if ok(xx + 1, y):
                    px[xx + 1, y] = C("2e2016")
        if k in (1, 2):                                     # carved prayer mark, faint gold
            cx, cy = 4 + (mask * 3) % 7, max(lo + 2, 7)
            for (dx, dy) in ((0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-1, 0), (1, 0), (-2, 2), (2, 2)):
                if ok(cx + dx, cy + dy):
                    px[cx + dx, cy + dy] = B["GLOW"][1] if (dx + dy) % 2 else B["GLOW"][0]
        if k == 3:                                          # moss patch creeping down a crack
            for y in range(lo, 13):
                for x in range(6, 11):
                    if ok(x, y) and h01(x, y, 88) < 0.5 - (y - lo) * 0.04:
                        px[x, y] = B["MOSS"][2 if (x + y) % 2 else 1]
    else:
        # a brighter ember vein bursting through the stone
        x = 2 + (mask * 5) % 11
        for y in range(lo, min(15, lo + 7)):
            x += (1 if h01(y, mask, 7) > 0.6 else -1 if h01(y, mask, 7) < 0.3 else 0)
            if ok(x, y):
                px[x, y] = B["GLOW"][2] if y % 3 else B["GLOW"][3]
                if ok(x + 1, y):
                    px[x + 1, y] = B["GLOW"][0]


def platform(B, kind, biome):
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    if biome == "hermit":
        WOOD = ramp("1a120c", "2a1e14", "3e2c1c", "564028", "705436", "8a6c46")
        for x in range(TS):
            if (left and x == 0) or (right and x == 15):
                continue
            px[x, 0] = WOOD[5] if h01(x, 0, 3) > 0.3 else WOOD[4]
            for y in (1, 2):
                px[x, y] = WOOD[3] if x % 5 else WOOD[1]           # plank joints
            px[x, 3] = WOOD[2]
            px[x, 4] = K
        for xr in (3, 12):                                         # rope lashings
            if (xr == 3 and left) or (xr == 12 and right) or kind == "M":
                for y in range(0, 5):
                    px[xr, y] = C("b8a878") if y % 2 else C("8a7c58")
        if left:
            for y in range(5, 14):
                px[1, y], px[2, y] = WOOD[1], WOOD[3]
        if right:
            for y in range(5, 14):
                px[13, y], px[14, y] = WOOD[3], WOOD[1]
    else:
        OB = ramp("08060a", "120c10", "1c1418", "282024", "3a3034", "564a4c")
        for x in range(TS):
            if (left and x < 1) or (right and x > 14):
                continue
            px[x, 0] = OB[5] if h01(x, 0, 3) > 0.4 else OB[4]
            px[x, 1] = OB[3]
            px[x, 2] = OB[2]
            dep = 3 + int(2 * h01(x // 3, 1, 9))
            for y in range(3, dep + 1):
                px[x, y] = OB[1]
            px[x, dep + 1] = K
            if h01(x, 2, 11) < 0.25:
                px[x, dep] = B["GLOW"][2]
    return outline(img)


def spikes(B, biome, down=False):
    img = blank(TS, TS)
    px = img.load()
    if biome == "hermit":
        cols = ramp("1a1418", "2e2628", "4a3e3c", "6a5a52", "8e7a6c")
        tipc = cols[4]
    else:
        cols = ramp("08060a", "140e12", "221a1e", "3a2e32", "5a4a4c")
        tipc = B["GLOW"][4]
    for n, (cx, ty, hw0) in enumerate(((2.5, 5, 2.2), (6.5, 1, 2.6), (10.5, 4, 2.2), (13.8, 7, 1.8))):
        for y in range(ty, 15):
            t = (y - ty) / (14 - ty)
            hw = 0.3 + hw0 * t
            for x in range(TS):
                dx = x + 0.5 - cx - (1 - t) * 0.8
                if abs(dx) <= hw:
                    c = cols[3] if dx < -0.3 else cols[2] if dx < hw * 0.4 else cols[1]
                    if y <= ty + 1:
                        c = tipc
                    elif biome == "ember" and abs(dx) < 0.5 and y < ty + 4:
                        c = B["GLOW"][2]
                    px[x, y] = c
    img = outline(img)
    px = img.load()
    for x in range(TS):
        px[x, 15] = K
        px[x, 14] = cols[1]
    return img.transpose(Image.FLIP_TOP_BOTTOM) if down else img


def bg_wall(B, k, biome):
    BG = B["BG"]
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            ci, d1, d2 = voronoi(B, (x + k * 5) % 16, (y + k * 9) % 16)
            v = 3 + (1 if (d2 - d1) > 1.5 else 0) - (1 if (d2 - d1) < 0.8 else 0) + (ci % 2)
            if h01(x, y, 90 + k) < 0.1:
                v -= 1
            px[x, y] = BG[int(clamp(v, 0, len(BG) - 1))]
    if biome == "ember" and k in (1, 2):                  # faint ember vein in the back wall
        x = 5 + k * 3
        for y in range(TS):
            x += 1 if h01(y, k, 3) > 0.7 else -1 if h01(y, k, 3) < 0.2 else 0
            px[x % 16, y] = C("3a1208") if y % 3 else C("5a1a0a")
    return img


def deco_hang(B, biome):
    img = blank(TS, TS)
    px = img.load()
    if biome == "hermit":                              # a rope of prayer strips (tiles vertically)
        for y in range(TS):
            px[7, y] = C("8a7c58") if y % 2 else C("6a5e44")
        for y0, col in ((3, C("76202c")), (10, C("8a6a2c"))):
            for j in range(4):
                for i in range(3 - j // 2):
                    px[8 + i, y0 + j] = col
    else:                                             # a burning root hanging from above
        for y in range(TS):
            x = 7 + int(1.4 * math.sin(y * 0.5))
            px[x, y] = C("3a2a20")
            px[x + 1, y] = C("5a3c24") if y % 4 else B["GLOW"][2]
    return outline(img)


def deco_roots(B, biome):
    img = blank(TS, TS)
    px = img.load()
    for r in range(3):
        x = 3 + r * 5
        L = 9 + r * 2
        for y in range(L):
            xx = x + int(1.5 * math.sin(y * 0.5 + r))
            px[xx, y] = C("4a3820") if biome == "hermit" else C("3a2418")
            if biome == "ember" and y > L - 3:
                px[xx, y] = B["GLOW"][3]
    return outline(img)


def deco_candles(B, biome):
    img = blank(TS, TS)
    px = img.load()
    if biome == "hermit":                              # clay butter lamps
        for cx in (4, 10):
            for y in range(12, 15):
                for x in range(cx - 2, cx + 3):
                    px[x, y] = C("8a4c28") if y < 14 else C("6a361c")
            px[cx, 11] = C("ffc14a")
            px[cx, 10] = C("fff0b8")
            px[cx, 9] = C("f58a24")
    else:                                              # guttering black candles
        for cx, top in ((4, 8), (8, 5), (12, 9)):
            for y in range(top + 1, 15):
                px[cx, y] = C("1c1416")
                px[cx + 1, y] = C("0e0a0c")
            px[cx, top] = C("ff9a3a")
            px[cx, top - 1] = C("ffd88a")
        for x in range(2, 15):
            px[x, 15] = C("140c0e")
    return outline(img)


def deco_bones(B, biome):
    img = blank(TS, TS)
    px = img.load()
    bone = [C("75664f"), C("a39274"), C("cdbf9d")]
    for x in range(2, 14):
        px[x, 14] = bone[1] if x % 3 else bone[2]
    for (cx, cy) in ((5, 12), (10, 12)):
        for y in range(cy - 2, cy + 1):
            for x in range(cx - 2, cx + 2):
                px[x, y] = bone[2] if y == cy - 2 else bone[1]
        px[cx - 1, cy - 1] = K
    if biome == "ember":
        px[7, 13], px[8, 13] = B["GLOW"][2], B["GLOW"][3]
    return outline(img)


def breakable(B, biome):
    img = solid_tile(B, 0, biome=biome)
    px = img.load()
    for (x, y) in ((6, 2), (7, 4), (6, 6), (8, 8), (8, 10), (9, 12), (7, 5), (9, 6), (10, 6)):
        px[x, y] = B["ST"][0]
    return img


def tuft(B, biome):
    img = blank(TS, TS)
    px = img.load()
    MOSS = B["MOSS"]
    for x in range(TS):
        hgt = int(3 * max(0.0, math.sin((x + 1) * 0.55)) * (0.5 + h01(x // 3, 1, 3)))
        for j in range(hgt):
            px[x, 15 - j] = MOSS[4] if j == hgt - 1 else MOSS[3]
    if biome == "hermit":
        for x in (3, 9, 13):                           # grass blades
            for j in range(4):
                px[x + (j // 2), 15 - j] = MOSS[3] if j < 3 else MOSS[4]
    else:
        for x in (4, 11):
            px[x, 14] = B["GLOW"][3]
    return img


def build_tileset(biome):
    B = BIOMES[biome]
    t = [solid_tile(B, m, biome=biome) for m in range(16)]
    t += [solid_tile(B, m, True, biome) for m in range(16)]
    t += [platform(B, k, biome) for k in ("L", "M", "R", "single")]
    t.append(spikes(B, biome))
    t.append(spikes(B, biome, True))
    t += [bg_wall(B, k, biome) for k in range(4)]
    t += [deco_hang(B, biome), deco_roots(B, biome), deco_candles(B, biome), deco_bones(B, biome)]
    t.append(breakable(B, biome))
    t.append(tuft(B, biome))
    assert len(t) == 48
    return t


# =========================================================================== parallax
BW, BH = 512, 216
DUSK = ramp("0c0a17", "120e22", "19122b", "221733", "2c1c3a", "38213f", "462742", "552d44", "663445",
            "7a3d46", "8e4a47", "a25a4a", "b46c4e", "c48054", "d29760", "deb070", "e9ca88")
GOLDR = ramp("3a2616", "6a4630", "8e6038", "b4843e", "d4a44a", "ecc466", "f8e098", "fff6d0")
MTN = ramp("140f1c", "1a1424", "20192c", "281f34", "30263c")


def hermit_far():
    """Dusk seen from a mountain cave: layered peaks, sea of haze, and the fallen Pale Root glowing on the horizon."""
    cv = Canvas(BW, BH, wrap=True)
    for y in range(BH):
        for x in range(BW):
            v = 0.1 + 0.85 * (y / 150) ** 1.4 + 0.05 * tn(x, y, 64, 18, 3)
            cv.set(x, y, pick(DUSK, v if y < 150 else 0.9 - (y - 150) / 300, x, y))
    for k in range(70):                                   # stars
        x, y = int(h01(k, 1, 7) * BW), int(h01(k, 2, 7) * 70)
        cv.set(x, y, DUSK[14] if k % 5 else GOLDR[7])
    # the fallen Root: a colossal glowing trunk lying along the horizon (root-ball left, crown right)
    hy = 116
    x0, x1 = 60, 420
    glow = {}
    for x in range(BW):
        t = (x - x0) / (x1 - x0)
        if 0 <= t <= 1:
            thick = 5 + 9 * math.sin(math.pi * min(1, t * 1.3)) ** 0.6 * (1 - 0.5 * t)
            top = hy - thick - 2 * tn(x, 0, 32, 1, 5)
            for y in range(int(top), hy + 2):
                v = 0.95 - (y - top) / (thick + 3) * 0.7
                cv.set(x, y, pick(GOLDR, clamp(v, 0.2, 1), x, y))
            for y in range(int(top) - 26, int(top)):
                glow[(x, y)] = max(glow.get((x, y), 0), 1 - (top - y) / 26)
    rnd_b = [(x0 + 4, -2.3, 46), (x0 + 12, -1.9, 38), (x0 - 2, -2.8, 30)] + \
            [(x1 - 70 + b * 22, -math.pi / 2 + (h01(b, 2, 4) - 0.5) * 1.3, 34 + 26 * h01(b, 3, 4)) for b in range(5)]
    for bi, (bx, ang, L) in enumerate(rnd_b):
        x, y = bx, hy - 8
        for st in range(int(L)):
            ang += (h01(bi, st, 6) - 0.5) * 0.22
            x += math.cos(ang); y += math.sin(ang)
            wdt = max(1, int(4 * (1 - st / L)))
            for d in range(wdt):
                cv.set(x + d, y, GOLDR[6] if d == 0 else GOLDR[4])
                for gy in range(-6, 1):
                    glow[(int(x + d) % BW, int(y) + gy)] = max(glow.get((int(x + d) % BW, int(y) + gy), 0), 0.4 + gy * 0.05)
    for (x, y), gv in glow.items():                       # soft dithered halo
        if cv.get(x, y) in DUSK and 0 <= y < BH:
            base = DUSK.index(cv.get(x, y))
            cv.set(x, y, pick(DUSK, (base + gv * 5 * (0.6 + 0.4 * bt(x, y))) / (len(DUSK) - 1), x, y))
    # two ranges of dark peaks in front
    for layer, (base, amp, sx, col) in enumerate(((150, 32, 128, MTN[4]), (176, 42, 64, MTN[1]))):
        for x in range(BW):
            top = base - amp * (0.5 + 0.5 * tn(x, layer, sx, 1, 11 + layer)) - 8 * tn(x, 3, 16, 1, 21 + layer)
            for y in range(int(top), BH):
                c = col
                if y < top + 2 and layer == 0:
                    c = MTN[2] if x % 3 else DUSK[6]
                cv.set(x, y, c)
    return cv.img


def hermit_mid():
    cv = Canvas(BW, BH, wrap=True)
    for x in range(BW):                                   # a near ridge with wind-bent pines
        top = 178 - 18 * tn(x, 1, 128, 1, 31) - 6 * tn(x, 2, 32, 1, 32)
        for y in range(int(top), BH):
            cv.set(x, y, C("0c0a10") if y > top + 1 else C("241c2a"))
    for t_ in range(7):
        tx = int(t_ * 73 + 30 * h01(t_, 1, 3))
        base = 178 - 18 * tn(tx, 1, 128, 1, 31)
        hgt = 24 + int(20 * h01(t_, 2, 3))
        for j in range(hgt):
            y = base - j
            w = int((hgt - j) * 0.35) + 1
            lean = int(j * 0.12)
            for i in range(-w, w + 1):
                if (j % 5) < 3 or abs(i) < 2:
                    cv.set(tx + i + lean, y, C("0e0b12"))
    return cv.img


def ember_far():
    """A vast dark hollow: basalt columns, a distant lake of embers, the Root's burning taproots hanging from above."""
    R = ramp("050304", "0a0506", "100809", "170b0b", "200e0d", "2c120f", "3a1810", "4e1e10", "6a2810", "8e3812")
    cv = Canvas(BW, BH, wrap=True)
    for y in range(BH):
        for x in range(BW):
            v = 0.08 + 0.5 * smooth(60, 200, y) + 0.08 * tn(x, y, 64, 32, 5)
            cv.set(x, y, pick(R, v, x, y))
    EMB = ramp("5a1408", "a02a0c", "e0561a", "ff9a3a", "ffd88a")
    for x in range(BW):                                   # the ember lake on the far floor
        for y in range(184, 200):
            v = 0.75 - (y - 184) * 0.045 + 0.18 * tn(x, y, 32, 4, 9)
            cv.set(x, y, pick(EMB, v, x, y))
        for y in range(160, 184):                          # its glow on the haze above
            cv.set(x, y, pick(R, 0.55 + 0.4 * (y - 160) / 24, x, y))
    for c in range(14):                                   # basalt columns
        cx = int(c * 37 + 12 * h01(c, 1, 7))
        wdt = 6 + int(8 * h01(c, 2, 7))
        top = 40 + int(90 * h01(c, 3, 7))
        for y in range(top, 190):
            for i in range(wdt):
                edge = i == 0 or i == wdt - 1
                cv.set(cx + i, y, R[1] if edge else R[2] if (i + y // 7) % 4 else R[3])
            if y > 170:
                cv.set(cx + wdt // 2, y, EMB[1])
    for r in range(6):                                    # burning taproots from the ceiling
        x = r * 85 + 30 * h01(r, 1, 9)
        L = 60 + 60 * h01(r, 2, 9)
        for y in range(int(L)):
            x += math.sin(y * 0.05 + r) * 0.6
            for d in range(max(1, int(4 * (1 - y / L)))):
                cv.set(x + d, y, EMB[2] if (y + d) % 5 == 0 else R[6])
    return cv.img


def ember_mid():
    cv = Canvas(BW, BH, wrap=True)
    EMB = ramp("5a1408", "a02a0c", "e0561a", "ff9a3a")
    for x in range(BW):
        top = 184 - 22 * tn(x, 1, 64, 1, 41) - 10 * tn(x, 2, 16, 1, 42)
        for y in range(int(top), BH):
            cv.set(x, y, C("080405") if y > top + 1 else C("2a1410"))
    for c in range(6):
        cx = int(c * 90 + 20 * h01(c, 1, 5))
        top = 70 + int(60 * h01(c, 2, 5))
        for y in range(top, BH):
            for i in range(10):
                cv.set(cx + i, y, C("0a0607") if 0 < i < 9 else C("1a0e0e"))
            if (y * 7 + c) % 23 == 0:
                cv.set(cx + 4, y, EMB[2])
    for r in range(4):                                    # hanging roots, near
        x = r * 128 + 50
        for y in range(0, 60 + r * 10):
            x += math.sin(y * 0.08 + r) * 0.7
            cv.set(x, y, C("1a0e0a"))
            cv.set(x + 1, y, EMB[1] if y % 9 == 0 else C("120a08"))
    return cv.img


BUILDERS = {"hermit": (hermit_far, hermit_mid), "ember": (ember_far, ember_mid)}
