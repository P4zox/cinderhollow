"""Starfall Crater environment: tileset (standard 48-tile layout), star-glass tiles, parallax (agent SF).

Black volcanic glass (obsidian) in conchoidal facets with a glossy blue-white lip, veins of starlight in the variants,
shard platforms, glass-tooth spikes. Star-glass ('?' tiles) is translucent deep blue with specular streaks.
Seamless: the interior is a pure function of the pixel on a 16x16 torus; edges are layered per exposed side.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline, pick, Canvas, smooth, fbm, lerpc

N, E, S, W_ = 1, 2, 4, 8
TS = 16

OB = ramp("040409", "07080f", "0b0c18", "101224", "151930", "1c213e", "252c50", "313b66", "3f4c80")
LIP = [C("cbd8ff"), C("7d91d2"), C("3b4886"), C("1a1f3c")]
GLOW = ramp("18244e", "2e4796", "5a7ee0", "a6c0ff", "eef4ff")
BGW = ramp("030308", "05050c", "080812", "0b0b18", "0e0f1e", "121326", "17182f")
GL = ramp("080c22", "0e1538", "15204e", "1d2c68", "283c86", "3652a6", "4c6ec6", "7494e4", "a8c2ff", "e6eeff")
SEEDS = [(2.6, 2.4), (9.6, 3.6), (5.8, 10.4), (13.2, 11.6), (14.8, 5.0), (1.4, 14.2)]


def wrap16(d):
    d %= 16
    return d - 16 if d >= 8 else d


def voronoi(x, y, seeds=SEEDS, sx=0.95, sy=1.2):
    best = []
    for i, (px_, py_) in enumerate(seeds):
        dx, dy = wrap16(x + .5 - px_), wrap16(y + .5 - py_)
        best.append((math.hypot(dx * sx, dy * sy), i, dx, dy))
    best.sort()
    return best[0], best[1]


# facet normals: each voronoi cell is a flat chip of glass tilted its own way
FACET = [(-0.5, -0.6), (0.3, -0.4), (-0.2, 0.3), (0.5, 0.2), (-0.6, 0.1), (0.1, -0.7)]


def facet_level(x, y):
    (d1, ci, dx, dy), (d2, cj, _, _) = voronoi(x, y)
    nx, ny = FACET[ci % len(FACET)]
    lit = -(nx * 0.6 + ny * 0.8)                    # light from the upper-left
    # conchoidal ripple: rings around the facet seed
    rip = 0.25 * math.sin(d1 * 2.2 + ci)
    lv = 3.4 + 1.6 * lit + rip
    edge = d2 - d1
    return lv, edge, ci, dx, dy


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
    if mask & S:                                     # jagged underside: glass teeth
        for x in range(TS):
            k = int(2.4 * max(0, math.sin(x * 1.3 + 0.7)) * h01(x // 2, 5, 12))
            for j in range(k):
                sh[15 - j][x] = False if (x % 4) in (0, 3) else sh[15 - j][x]
    return sh


def solid_tile(mask, variant=False):
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask)

    def dist(x, y):
        ds = [99]
        if mask & N: ds.append(y)
        if mask & S: ds.append(15 - y + 2)
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
            lv, edge, ci, dx, dy = facet_level(x, y)
            if edge < 0.55:
                lv = 1.2                                 # the fracture line between chips
            elif edge < 1.1 and (dx + dy) < 0:
                lv += 1.3                                # a lit ridge on the upper-left side of each chip
            d = dist(x, y)
            k = (d > 4) + (d > 8) + (d > 11)
            lv -= (0, 1.2, 2.0, 2.6)[k]
            if k >= 2:
                lv = min(lv, 2.6)
            if mask & S and 15 - y < 3:
                lv -= (1.6, 1.0, 0.5)[15 - y]
            if mask & W_ and x < 2:
                lv += 0.8
            v = clamp(lv / (len(OB) - 1), 0, 1)
            px[x, y] = pick(OB, v, x, y)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, -1, 0) and not (mask & N and y < 3):
                px[x, y] = OB[6]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & N:
        for x in range(TS):
            for y in range(3):
                if not sh[y][x]:
                    continue
                c = LIP[y]
                if y == 0 and h01(x, 0, 21) < 0.22:
                    c = LIP[1]                           # broken gloss
                if out(x, y, 1, 0):
                    c = K if y else LIP[1]
                px[x, y] = c
            if sh[3][x] and px[x, 3] != K and h01(x, 3, 34) < 0.3:
                px[x, 3] = LIP[3]
        for x in (3, 11):                                # a star glint on the lip
            if sh[0][x] and h01(x, mask, 7) < 0.5:
                px[x, 0] = GLOW[4]
    if variant and mask != 15 and (mask * 7) % 3 != 1:
        vein(img, mask)
    elif variant:
        for i in range(5):
            x, y = 4 + i + mask % 5, 6 + i
            if px[x, y][3] and px[x, y] != K:
                px[x, y] = OB[7]
    return img


def vein(img, mask):
    """a thin crack of starlight running through the glass"""
    px = img.load()
    lo = 5 if mask & N else 1
    x = 3 + (mask * 5) % 10
    ln = 6 + mask % 5
    for i, y in enumerate(range(lo, min(15, lo + ln))):
        x += 1 if h01(y, mask, 7) > 0.62 else -1 if h01(y, mask, 7) < 0.3 else 0
        x = max(1, min(14, x))
        if px[x, y][3] and px[x, y] != K:
            px[x, y] = GLOW[3] if i % 4 == 1 else GLOW[2]
            if px[x + 1, y][3] and px[x + 1, y] != K:
                px[x + 1, y] = GLOW[0]
    if mask % 3 == 0:                                    # a single embedded star
        sx, sy = 4 + (mask * 7) % 8, max(lo + 3, 8)
        if px[sx, sy][3] and px[sx, sy] != K:
            px[sx, sy] = GLOW[4]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if px[sx + dx, sy + dy][3] and px[sx + dx, sy + dy] != K:
                    px[sx + dx, sy + dy] = GLOW[1]


def platform(kind):
    """a floating slab of black glass with a glossy top edge and a jagged keel"""
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    for x in range(TS):
        if (left and x < 1) or (right and x > 14):
            continue
        px[x, 0] = LIP[0] if h01(x, 0, 3) > 0.25 else LIP[1]
        px[x, 1] = LIP[2]
        px[x, 2] = OB[5] if (x // 3) % 2 else OB[4]
        keel = 3 + int(2.5 * (0.5 + 0.5 * math.sin(x * 0.9 + (1 if kind == "M" else 0))) * h01(x // 2, 2, 5))
        if left and x < 4:
            keel = min(keel, 3 + x // 2)
        if right and x > 11:
            keel = min(keel, 3 + (15 - x) // 2)
        for y in range(3, keel + 1):
            px[x, y] = OB[3] if y < keel else OB[2]
        px[x, keel + 1] = K
        if h01(x, 4, 17) < 0.12:
            px[x, 3] = GLOW[2]
    return outline(img)


def spikes(down=False):
    img = blank(TS, TS)
    px = img.load()
    for n, (cx, ty, hw0) in enumerate(((2.6, 4, 2.0), (6.6, 0, 2.4), (10.4, 3, 2.1), (13.8, 6, 1.7))):
        for y in range(ty, 15):
            t = (y - ty) / (14 - ty)
            hw = 0.3 + hw0 * t
            for x in range(TS):
                dx = x + 0.5 - cx - (1 - t) * 0.6
                if abs(dx) <= hw:
                    c = GL[7] if dx < -hw * 0.3 else GL[4] if dx < hw * 0.4 else GL[2]
                    if y <= ty + 1:
                        c = GLOW[4]
                    px[x, y] = c
    img = outline(img)
    px = img.load()
    for x in range(TS):
        px[x, 15] = K
        px[x, 14] = OB[2]
    return img.transpose(Image.FLIP_TOP_BOTTOM) if down else img


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            (d1, ci, dx, dy), (d2, _, _, _) = voronoi((x + k * 5) % 16, (y + k * 9) % 16)
            v = 3 + (1 if (d2 - d1) > 1.5 else 0) - (1 if (d2 - d1) < 0.7 else 0) + (ci % 2)
            if h01(x, y, 90 + k) < 0.08:
                v -= 1
            px[x, y] = BGW[int(clamp(v, 0, len(BGW) - 1))]
    if k in (1, 3):                                        # a far, faint star seen through the wall's glass
        sx, sy = 4 + k * 2, 5 + k
        px[sx, sy] = GLOW[1]
    return img


def deco_chain():
    """a hanging strand of star-glass beads (tiles vertically)"""
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        px[7, y] = C("2a3050") if y % 4 else C("4a5890")
    for y0 in (4, 12):
        for dx, dy, c in ((0, 0, GLOW[3]), (1, 0, GLOW[2]), (-1, 0, GLOW[2]), (0, 1, GLOW[1]), (0, -1, GLOW[2])):
            px[7 + dx, y0 + dy] = c
    return outline(img)


def deco_icicles():
    img = blank(TS, TS)
    px = img.load()
    for r, (x, L) in enumerate(((3, 9), (7, 13), (11, 7), (13, 10))):
        for y in range(L):
            w = 1 if y > L * 0.45 else 2
            for i in range(w):
                px[x + i, y] = GL[7] if i == 0 and y < L - 2 else GL[4]
            if y == L - 1:
                px[x, y] = GLOW[3]
    return outline(img)


def deco_crystals():
    img = blank(TS, TS)
    px = img.load()
    for cx, top, w in ((4, 7, 2), (8, 3, 3), (12, 8, 2)):
        for y in range(top, 15):
            t = (y - top) / max(1, 14 - top)
            hw = max(0.6, w * min(1.0, t * 2.2))
            for x in range(TS):
                dx = x + 0.5 - cx
                if abs(dx) <= hw:
                    px[x, y] = GL[8] if dx < -0.2 else GL[5] if dx < hw * 0.5 else GL[3]
        px[cx, top] = GLOW[4]
        px[cx, top + 2] = GLOW[3]
    for x in range(2, 15):
        px[x, 15] = OB[3]
    return outline(img)


def deco_shards():
    img = blank(TS, TS)
    px = img.load()
    for cx, cy, s in ((4, 13, 2), (8, 12, 3), (12, 13, 2), (6, 14, 1), (10, 14, 1)):
        for y in range(cy - s, cy + 2):
            for x in range(cx - s, cx + s + 1):
                if abs(x - cx) + abs(y - cy) <= s + 0.5:
                    px[x, y] = GL[7] if x < cx else OB[5] if y < cy else OB[3]
    px[8, 9] = GLOW[3]
    return outline(img)


def breakable():
    img = solid_tile(0)
    px = img.load()
    for (x, y) in ((6, 2), (7, 4), (6, 6), (8, 8), (8, 10), (9, 12), (7, 5), (9, 6), (10, 6)):
        px[x, y] = GLOW[1]
    return img


def tuft():
    img = blank(TS, TS)
    px = img.load()
    for x0, hgt in ((2, 2), (5, 4), (6, 2), (10, 3), (13, 2)):
        for j in range(hgt):
            px[x0, 15 - j] = GL[8] if j == hgt - 1 else GL[5]
            if j == 0:
                px[x0 + 1, 15] = GL[3]
    px[5, 11] = GLOW[4]
    return outline(img)


def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [solid_tile(m, True) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(spikes())
    t.append(spikes(True))
    t += [bg_wall(k) for k in range(4)]
    t += [deco_chain(), deco_icicles(), deco_crystals(), deco_shards()]
    t.append(breakable())
    t.append(tuft())
    assert len(t) == 48
    return t


# =========================================================================== star-glass ('?')
def glass_tile(mask, variant=False):
    img = blank(TS, TS)
    px = img.load()

    def out(x, y, dx, dy):
        X, Y = x + dx, y + dy
        if X < 0: return bool(mask & W_)
        if X >= TS: return bool(mask & E)
        if Y < 0: return bool(mask & N)
        if Y >= TS: return bool(mask & S)
        return False
    for y in range(TS):
        for x in range(TS):
            # deep translucent body: brighter towards the lit upper-left, specular bands on the diagonal
            d = min([99] + ([y] if mask & N else []) + ([x] if mask & W_ else []) + ([15 - y] if mask & S else []) + ([15 - x] if mask & E else []))
            band = 0.5 + 0.5 * math.sin(((x + 16 - y) % 16) * (2 * math.pi / 16) * 2 + 0.6)
            v = 0.32 + 0.22 * band - 0.03 * min(d, 6)
            if (x - y) % 16 in (3, 4) or (x - y) % 16 == 11:
                v += 0.22                                   # the streak
            px[x, y] = pick(GL, clamp(v, 0, 1), x, y)
    # inner stars
    for (sx, sy, k) in ((4, 9, 0), (11, 4, 1), (13, 13, 2)):
        if variant or k == 1:
            px[sx, sy] = GLOW[4]
            if k == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    px[sx + dx, sy + dy] = GL[7]
    for y in range(TS):
        for x in range(TS):
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, 0, -1):
                px[x, y] = GL[9] if not out(x, y, 1, 0) else GL[8]
            elif out(x, y, -1, 0):
                px[x, y] = GL[8]
            elif (mask & N and y == 1) or (mask & W_ and x == 1):
                px[x, y] = GL[6]
    return img


def build_glass():
    return [glass_tile(m) for m in range(16)] + [glass_tile(m, True) for m in range(16)]


# =========================================================================== parallax
BW, BH = 512, 216
SKY = ramp("020309", "03040c", "04060f", "060813", "080a18", "0a0d1d", "0c1022", "0e1328", "11162e", "141a34")
NEB = [C("140a26"), C("1e0f3a"), C("2a1650"), C("361c66"), C("1a2656"), C("22306e"), C("2e3e86")]
RIM = ramp("05060d", "080a14", "0b0e1c", "0f1326", "141a32")


def far():
    cv = Canvas(BW, BH, wrap=True)
    for y in range(BH):
        for x in range(BW):
            t = y / BH
            cv.set(x, y, pick(SKY, t * 0.95, x, y))
    # nebula band, diagonal, tileable
    for y in range(BH):
        for x in range(BW):
            n = fbm(x, y, 64, 40, 7, BW, 4)
            band = math.exp(-((y - 70 - 40 * math.sin(x / BW * 2 * math.pi)) / 38.0) ** 2)
            v = (n - 0.42) * 2.4 * band
            if v > 0.05:
                n2 = fbm(x + 17, y, 32, 24, 19, BW, 3)
                pal = NEB[:4] if n2 < 0.5 else [NEB[0], NEB[4], NEB[5], NEB[6]]
                i = int(clamp(v, 0, 0.999) * len(pal))
                if v * len(pal) - i > bt(x, y) * 0.9 or i > 0:
                    cv.set(x, y, pal[min(i, len(pal) - 1)])
    # stars
    for i in range(520):
        x, y = int(h01(i, 1, 3) * BW), int(h01(i, 2, 3) * 170)
        b = h01(i, 3, 3)
        c = C("e8f0ff") if b > 0.93 else C("9fb2e6") if b > 0.7 else C("56638e") if b > 0.35 else C("343c5c")
        cv.set(x, y, c)
        if b > 0.975:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.set(x + dx, y + dy, C("6d80c0"))
    # the scar the star left across the sky
    for i in range(420):
        t = i / 420
        x, y = 40 + t * 300, 8 + t * t * 120
        w = 2.4 * (1 - t) + 0.6
        for dy in range(-3, 4):
            if abs(dy) <= w:
                c = C("cfe0ff") if abs(dy) < w * 0.3 and t > 0.3 else C("6f86c8") if abs(dy) < w * 0.7 else C("27305a")
                if h01(i, dy, 9) < 0.85:
                    cv.set(x, y + dy, c)
    # distant crater rim with the old gods' corpses slumped over it
    for x in range(BW):
        hgt = 26 + 10 * math.sin(x / BW * 2 * math.pi * 3 + 1) + 6 * fbm(x, 0, 32, 1, 5, BW, 3) * 2
        top = int(BH - hgt)
        for y in range(top, BH):
            cv.set(x, y, RIM[1] if y > top + 2 else RIM[3])
        if h01(x, 1, 44) < 0.08:
            cv.set(x, top, C("4a5a9a"))
    god(cv, 150, BH - 22, 1.0)
    god(cv, 420, BH - 20, 0.75, flip=True)
    return cv.img


def god(cv, cx, base, s, flip=False):
    """a colossal fallen god slumped over the crater rim: thick ribs, spine, a great antlered skull resting on the ground"""
    sil, lit, lit2 = C("05060d"), C("1e2850"), C("34447e")
    f = -1 if flip else 1
    pts = set()

    def blob(x, y, r):
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                if (xx + .5 - x) ** 2 + (yy + .5 - y) ** 2 <= r * r:
                    pts.add((xx, yy))
    for i in range(int(110 * s)):                          # spine, arching over the rim
        t = i / (110 * s)
        blob(cx + f * i, base - 10 * s - math.sin(t * math.pi) * 14 * s, 3.2 * s)
    for r in range(6):                                     # ribs curling up from the spine and back down
        rx = cx + f * (18 + r * 15) * s
        rh = (58 - r * 7) * s
        for i in range(48):
            t = i / 47
            x = rx + f * (math.sin(t * math.pi) * 16 * s - t * 10 * s)
            y = base - 12 * s - math.sin(t * math.pi * 0.92) * rh
            blob(x, y, (2.6 - 1.4 * t) * s)
    hx, hy = cx - f * 10 * s, base - 16 * s                # the skull, resting on its jaw
    for yy in range(int(-18 * s), int(14 * s)):
        for xx in range(int(-15 * s), int(15 * s)):
            e = (xx / (13 * s)) ** 2 + ((yy + 2 * s) / (15 * s)) ** 2
            if e <= 1 or (yy > 4 * s and abs(xx + f * 8 * s) < 9 * s and yy < 13 * s):
                pts.add((int(hx + xx), int(hy + yy)))
    for side in (-1, 1):                                   # antlers, thick at the root
        x, y = hx + side * 7 * s, hy - 14 * s
        for i in range(int(46 * s)):
            t = i / (46 * s)
            x += side * (0.9 - 0.3 * t)
            y -= 1.0 - 0.5 * t
            blob(x, y, (2.4 - 1.6 * t) * s)
            if i in (int(16 * s), int(30 * s)):
                bx, by = x, y
                for j in range(int(12 * s)):
                    bx += side * 0.2; by -= 1
                    blob(bx, by, 1.2 * s)
    for (x, y) in pts:
        cv.set(x, y, sil)
    for (x, y) in pts:
        if (x, y - 1) not in pts:
            cv.set(x, y, lit2 if (x - 1, y) not in pts else lit)
        elif (x - 1, y) not in pts:
            cv.set(x, y, lit)
    for dx in (-5, 5):                                     # hollow eyes, a last glimmer
        for yy in range(3):
            cv.set(int(hx + dx * s), int(hy - 2 * s + yy), C("04050a"))
        cv.set(int(hx + dx * s), int(hy - 1 * s), C("6a88e0"))


def mid():
    cv = Canvas(BW, BH, wrap=True)
    body, rim, rim2 = C("090a16"), C("2f3b72"), C("5a70c0")
    # floating islands
    for (ix, iy, w, h) in ((60, 70, 70, 22), (250, 40, 46, 16), (380, 88, 90, 26), (470, 30, 30, 12)):
        for x in range(-w // 2, w // 2):
            t = abs(x) / (w / 2)
            top = int(iy - (1 - t * t) * 3 - h01(x // 3, 1, ix) * 2)
            bot = int(iy + (1 - t) ** 1.3 * h * (0.7 + 0.3 * h01(x // 2, 3, ix)))
            for y in range(top, bot):
                cv.set(ix + x, y, body)
            cv.set(ix + x, top, rim if h01(x, 2, ix) > 0.2 else rim2)
        for k in range(3):                                   # shard spires on the islands
            sx = ix - w // 3 + k * w // 3
            for y in range(int(12 * h01(k, ix, 4)) + 4):
                for x in range(-2 + y // 5, 3 - y // 5):
                    cv.set(sx + x, iy - 2 - y, body)
            cv.set(sx, iy - 4, rim2)
    # ground spires and a broken observatory dome
    for i in range(22):
        sx = int(h01(i, 7, 2) * BW)
        hgt = 20 + int(h01(i, 8, 2) * 50)
        lean = (h01(i, 9, 2) - 0.5) * 0.6
        for y in range(hgt):
            hw = 1 + (hgt - y) * 0.09
            for x in range(int(-hw), int(hw) + 1):
                cv.set(sx + x + int(lean * y), BH - 1 - y, body)
            cv.set(sx + int(-hw) + int(lean * y), BH - 1 - y, rim if y > hgt * 0.3 else rim2)
    dx, dy, R = 300, BH - 44, 38
    for y in range(-R, 1):
        for x in range(-R, R + 1):
            d = math.hypot(x, y * 1.1)
            if R - 4 <= d <= R and not (x > 6 and y < -R * 0.4):     # the dome shell, broken open
                cv.set(dx + x, dy + y, body)
    for y in range(0, 44):
        for x in range(-R - 2, R + 3):
            if abs(x) > R - 6 or y > 30:
                cv.set(dx + x, dy + y, body)
    for x in range(-R, R + 1, 7):
        cv.set(dx + x, dy + 30, rim)
    for y in range(BH - 12, BH):
        for x in range(BW):
            cv.set(x, y, body)
    return cv.img


# =========================================================================== phase-2 void (Astrel): the crater opens to deep space
VOID = ramp("020106", "05030d", "080516", "0c0720", "110a2c", "170d38")
GAL = [C("1a0f3a"), C("2c1a5e"), C("41308a"), C("5a52b8"), C("8a8ee0"), C("c8d4ff"), C("ffffff")]


def void_far():
    cv = Canvas(BW, BH, wrap=True)
    for y in range(BH):
        for x in range(BW):
            v = 0.35 + 0.35 * fbm(x, y, 64, 54, 31, BW, 3) - 0.15 * abs(y - 108) / 108
            cv.set(x, y, pick(VOID, clamp(v, 0, 1), x, y))
    # a spiral galaxy wheeling in the dark
    gx, gy = 330, 96
    for i in range(9000):
        arm = i % 2
        t = h01(i, 1, 77)
        a = arm * math.pi + t * 7.5 + (h01(i, 2, 77) - 0.5) * 0.9 * (1 - t)
        r = 6 + t * 96
        x, y = gx + math.cos(a) * r, gy + math.sin(a) * r * 0.42
        br = (1 - t) * 0.9 + 0.1 * h01(i, 3, 77)
        cv.set(x, y, GAL[min(6, int(br * 6.5))])
    for y in range(-10, 11):
        for x in range(-22, 23):
            d = math.hypot(x / 22, y / 10)
            if d < 1:
                cv.set(gx + x, gy + y, GAL[6] if d < 0.25 else GAL[5] if d < 0.5 else GAL[4] if d < 0.75 else cv.get(gx + x, gy + y) if h01(x, y, 4) < 0.5 else GAL[3])
    # a dying star, vast and cold, its corona torn into rays
    sx, sy, sr = 96, 44, 17
    for y in range(-80, 81):
        for x in range(-80, 81):
            d = math.hypot(x, y)
            if d < sr:
                l = 1 - d / sr
                cv.set(sx + x, sy + y, pick([C("4a5a9c"), C("6e80c0"), C("9aaae0"), C("c8d4f4")], 0.2 + 0.7 * l + 0.1 * (-(x + y) / sr), x, y))
            elif d < sr + 3:
                cv.set(sx + x, sy + y, C("4a64c8") if h01(x, y, 5) < 0.7 else C("8aa4f0"))
            elif d < 58:
                ang = math.atan2(y, x)
                ray = max(0.0, math.cos(ang * 7 + 0.4)) ** 6 + max(0.0, math.cos(ang * 11 - 1.2)) ** 10
                v = ray * (1 - (d - sr) / (58 - sr)) ** 1.8 * 0.8
                if v > 0.12 and bt(x, y) < v * 1.6:
                    cv.set(sx + x, sy + y, C("222c66") if v < 0.35 else C("3e50a0") if v < 0.6 else C("6e84cc"))
    # stars: dense, and some big
    for i in range(1400):
        x, y = int(h01(i, 5, 9) * BW), int(h01(i, 6, 9) * BH)
        b = h01(i, 7, 9)
        cv.set(x, y, C("ffffff") if b > 0.95 else C("a8b8ec") if b > 0.75 else C("5a64a0") if b > 0.4 else C("2e3160"))
        if b > 0.985:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.set(x + dx, y + dy, C("7a8ce0"))
    return cv.img


def void_mid():
    cv = Canvas(BW, BH, wrap=True)
    body, rim, rim2, glow = C("07070f"), C("34447e"), C("7e92d6"), C("c6d8ff")
    for k, (ix, iy, w, h) in enumerate(((40, 150, 80, 30), (180, 176, 60, 22), (300, 136, 110, 34), (452, 170, 70, 26), (250, 60, 34, 14), (420, 48, 26, 10))):
        for x in range(-w // 2, w // 2):
            t = abs(x) / (w / 2)
            top = int(iy - (1 - t * t) * 4 - h01(x // 3, 1, ix) * 3)
            bot = int(iy + (1 - t) ** 1.2 * h * (0.7 + 0.3 * h01(x // 2, 3, ix)))
            for y in range(top, bot):
                cv.set(ix + x, y, body)
            cv.set(ix + x, top, rim if h01(x, 2, ix) > 0.25 else rim2)
            if h01(x, 5, ix) < 0.06:
                for y in range(top + 2, min(bot, top + 8)):
                    cv.set(ix + x, y, glow if y == top + 2 else rim)
        for j in range(int(w / 12)):                     # shards drifting off the chunk
            sx, sy = ix + (h01(j, k, 3) - 0.5) * w * 1.3, iy - 10 - h01(j, k, 4) * 24
            for dy in range(4):
                for dx in range(-1 + dy // 2, 2 - dy // 2):
                    cv.set(sx + dx, sy + dy, body)
            cv.set(sx, sy, rim2)
    return cv.img
