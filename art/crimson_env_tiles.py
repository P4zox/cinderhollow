"""Tileset `tiles_crimson` -- THE CRIMSON MANOR (agent C).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid, index = mask of AIR neighbours (N=1 E=2 S=4 W=8): violet-black obsidian ashlar with a faint cool sheen;
       exposed tops get a polished black-marble coping with a thin tarnished-silver trim line and rare dried-blood drips
16-31  same masks, variant: carved gothic tracery blocks / blood-veined black marble slabs / iron dovetail clamps
32-35  one-way platform L / M / R / single: black wrought-iron balcony, dark wood + velvet floor board, scrollwork
       railing frieze underneath, silver drop finials at the ends
36/37  floor / ceiling spikes: iron fence spears with silver tips
38-41  background wall: dark crimson damask (38 plain, 39 peeled to dark wood, 40 faded blotch, 41 dried-blood smear)
42     hanging chain + small red-glass lantern        43 hanging tattered crimson velvet drape
44     candle cluster with red wax drips              45 spilled goblet, a skull and dead roses
46     breakable wall (looks like 0 with a subtle crack)
47     top tuft overlay: dead black roses and thorned ivy
Seams: the interior texture is a pure function of the in-tile pixel on a 16x16 torus (as deep_tiles.py).
"""
import math
from PIL import Image
from envlib import K, T, h01, clamp, blank
from crimson_env_lib import ST, MB, SV, BL, VV, DM, WD, IR, GL, WX, FL, SK, GS, Spr, tiny_flame, outline

N, E, S, W = 1, 2, 4, 8
TS = 16
SHEEN = [(0x3a, 0x36, 0x58, 255), (0x52, 0x4e, 0x78, 255)]     # cool violet-blue gloss on obsidian

# ashlar courses on the torus: (y0, y1, joint xs): a long block over two short ones
COURSES = [(0, 7, [6]), (8, 15, [1, 9])]


def block(x, y):
    for ci, (y0, y1, js) in enumerate(COURSES):
        if y0 <= y <= y1:
            ly = y - y0
            js = sorted(js)
            for bi, j in enumerate(js):
                nj = js[(bi + 1) % len(js)]
                w = (nj - j) % 16 or 16
                lx = (x - j) % 16
                if lx < w:
                    return ci, bi, lx, ly, w, y1 - y0 + 1, (lx == 0 or ly == y1 - y0)
    raise AssertionError


def solid_shape(mask):
    sh = [[True] * TS for _ in range(TS)]
    if mask & N and mask & W:
        sh[0][0] = False
    if mask & N and mask & E:
        sh[0][15] = False
    if mask & S and mask & W:
        for p in ((0, 15), (1, 15), (0, 14)):
            sh[p[1]][p[0]] = False
    if mask & S and mask & E:
        for p in ((15, 15), (14, 15), (15, 14)):
            sh[p[1]][p[0]] = False
    return sh


def depth_of(mask, x, y):
    ds = [99]
    if mask & N: ds.append(y - 5)
    if mask & S: ds.append(15 - y + 1)
    if mask & W: ds.append(x)
    if mask & E: ds.append(15 - x + 1)
    return max(0, min(ds))


def stone_px(mask, x, y):
    """Colour of the obsidian ashlar at torus pixel (x, y) for a tile with this air mask (before faces/coping)."""
    ci, bi, lx, ly, bw, bh, joint = block(x, y)
    j0 = COURSES[ci][2][bi]
    cen = ((j0 + bw / 2) % 16, COURSES[ci][0] + bh / 2)
    d = depth_of(mask, *cen) + 2.0 * h01(int(cen[0] * 3), int(cen[1] * 5), 7)
    if joint:
        return ST[0] if d > 5 else ST[1]
    tone = (0, -1, 1)[(ci * 2 + bi) % 3]
    lv = 5 + tone
    if ly == 0:
        lv += 1                                    # polished top arris catches the light
    elif ly == bh - 2:
        lv -= 1
    if lx == 1:
        lv += 1
    elif lx == bw - 1:
        lv -= 1
    r = h01(x, y, 19 + ci)
    if r < 0.06:
        lv -= 1
    k = (d > 3) + (d > 6) + (d > 9)
    lv -= (0, 1, 3, 4)[k]
    if k >= 2:
        lv = min(lv, 3)
    c = ST[int(clamp(lv, 0, 9))]
    # the obsidian sheen: a short diagonal gloss streak in the upper-left of the long blocks
    if k == 0 and ci == 0 and 2 <= lx <= 6 and 1 <= ly <= 4 and (lx - ly) == 1:
        c = SHEEN[1] if ly == 1 else SHEEN[0]
    return c


def solid_tile(mask, variant=False):
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask)

    def out(x, y, dx, dy):
        X, Y = x + dx, y + dy
        if X < 0: return bool(mask & W)
        if X >= TS: return bool(mask & E)
        if Y < 0: return bool(mask & N)
        if Y >= TS: return bool(mask & S)
        return not sh[Y][X]

    for y in range(TS):
        for x in range(TS):
            if sh[y][x]:
                px[x, y] = stone_px(mask, x, y)
    if variant:
        variant_features(px, sh, mask)
    # faces: dark outline on E / S (shadow side), a cool lit rim on W
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, -1, 0) and not (mask & N and y < 6):
                px[x, y] = ST[7] if (y % 8) else ST[8]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & E:
        for y in range(TS):
            if sh[y][14] and px[14, y] != K and not (mask & N and y < 6):
                px[14, y] = ST[2] if px[14, y][0] > ST[2][0] else px[14, y]
    if mask & S:
        for x in range(TS):
            if sh[14][x] and px[x, 14] != K:
                px[x, 14] = ST[1]
    if mask & N:
        coping(px, sh, mask, out, variant)
    return img


def coping(px, sh, mask, out, variant):
    """Polished black-marble coping: bright arris, glossy band, tarnished-silver trim, shadow line, rare blood drips."""
    for x in range(TS):
        for y in range(6):
            if not sh[y][x]:
                continue
            if y == 0:
                c = MB[5] if h01(x, 0, 81 + variant) > 0.18 else MB[6]
            elif y == 1:
                c = MB[4]
            elif y == 2:
                c = MB[3] if h01(x, 2, 44) > 0.12 else MB[4]
            elif y == 3:
                c = MB[2]
            elif y == 4:
                c = SV[4] if h01(x, 4, 12) > 0.2 else SV[3]
                if h01(x, 4, 13) > 0.86:
                    c = SV[5]
            else:
                c = K
            # a faint white vein wandering through the marble
            if y in (1, 2, 3) and ((x * 2 + y * 3 + (5 if variant else 0)) % 23) == 0:
                c = MB[5]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else MB[3]
            elif mask & E and x == 14 and 0 < y < 5:
                c = MB[2] if y < 4 else SV[2]
            elif out(x, y, -1, 0) or (mask & W and x == 0):
                c = MB[6] if y < 3 else (SV[5] if y == 4 else (K if y == 5 else MB[4]))
            px[x, y] = c
    # dried blood seeping from under the trim (rare; different spots per variant so floors do not repeat)
    drips = {False: {3: [4], 9: [12], 13: [9]},
             True: {1: [11], 7: [10], 15: [6]}}[variant]
    for dx in drips.get(mask, []):
        if not sh[6][dx]:
            continue
        ln = 2 + int(h01(dx, mask, 3) * 3)
        px[dx, 5] = BL[3]
        for yy in range(6, 6 + ln):
            if yy < 15 and px[dx, yy] != K:
                px[dx, yy] = BL[2] if yy < 5 + ln else BL[4]
        if 6 + ln < 15 and px[dx, 6 + ln] != K:
            px[dx, 6 + ln] = BL[3]


def variant_features(px, sh, mask):
    lo = 6 if mask & N else 0
    if mask == 0:
        # interior variant stays quiet: a hairline crack through a dark block
        for (x, y) in ((3, 9), (4, 10), (5, 10), (6, 11), (7, 11), (8, 12), (9, 12)):
            px[x, y] = ST[0]
        return
    kind = mask % 3
    if kind == 0:
        tracery(px, sh, mask, lo)
    elif kind == 1:
        veined(px, sh, mask, lo)
    else:
        clamp_plate(px, sh, mask, lo)


def tracery(px, sh, mask, lo):
    """A carved gothic lancet in relief: recessed dark field, pointed head with a trefoil, lit upper-left rim."""
    cx = 8 if not (mask & W) else 9
    if mask & E:
        cx -= 1
    top = max(lo + 1, 7) if mask & N else 2
    bot = min(14, top + 9) if not (mask & S) else 12
    hw = 3
    for y in range(top, bot + 1):
        for x in range(cx - hw, cx + hw + 1):
            dx = x - cx
            yy = y - top
            # pointed arch head: width grows over the first 3 rows
            lim = hw if yy >= 3 else (0, 1.5, 2.5)[yy]
            if abs(dx) > lim + 0.01:
                continue
            edge = abs(dx) >= lim - 0.5 or y == bot
            if edge:
                c = ST[7] if (dx < 0 or yy < 2) and y != bot else ST[2]
            else:
                c = ST[1]
            px[x, y] = c
    # trefoil in the head + a thin mullion
    for (dx, dy) in ((0, 3), (-1, 4), (1, 4), (0, 5)):
        px[cx + dx, top + dy] = ST[5]
    px[cx, top + 4] = ST[1]
    for y in range(top + 6, bot):
        px[cx, y] = ST[4]


def veined(px, sh, mask, lo):
    """Blood-veined black marble: one block is polished marble; a thin dried-blood vein meanders through it."""
    y0 = lo + 1 if mask & N else 1
    y1 = 14 if not (mask & S) else 13
    for y in range(y0, y1 + 1):
        for x in range(TS):
            if not sh[y][x] or px[x, y] in (K,):
                continue
            ci, bi, lx, ly, bw, bh, joint = block(x, y)
            if ci != 1 or joint:
                continue
            c = MB[3] if ly == 0 else MB[2] if lx == 1 else MB[1] if lx == bw - 1 else MB[2]
            if (lx + ly * 2) % 9 == 0 and not joint:
                c = MB[3]
            px[x, y] = c
    # the vein: a smooth wandering line across the lower course
    ph = mask * 1.7
    prev = None
    for x in range(TS):
        y = int(round(11.5 + 1.8 * math.sin(x * 0.45 + ph) + 0.8 * math.sin(x * 1.1 + ph * 2)))
        if y0 <= y <= y1 and sh[y][x] and px[x, y] != K:
            px[x, y] = BL[1] if (x + mask) % 4 else BL[2]
            if prev is not None and abs(prev - y) > 1:
                yy = (prev + y) // 2
                if px[x, yy] != K:
                    px[x, yy] = BL[0]
        prev = y


def clamp_plate(px, sh, mask, lo):
    """A riveted iron strap bolted across the long course's joint (x=6), a silver bolt head, a rust-blood streak."""
    y0 = 8 if mask & N else 3
    x0 = 3
    for yy in range(4):
        for xx in range(8):
            X, Y = x0 + xx, y0 + yy
            if not sh[Y][X] or px[X, Y] == K:
                continue
            if yy == 0:
                c = IR[5]
            elif yy == 3:
                c = K
            elif xx == 0:
                c = IR[4]
            elif xx == 7:
                c = IR[1]
            else:
                c = IR[3] if yy == 1 else IR[2]
            px[X, Y] = c
    for bx in (x0 + 1, x0 + 6):
        px[bx, y0 + 1] = SV[5]
        px[bx, y0 + 2] = SV[2]
    for yy in range(y0 + 4, min(15, y0 + 7)):
        if px[x0 + 6, yy] != K:
            px[x0 + 6, yy] = BL[1]


# =========================================================================== platform
def platform(kind):
    """Black wrought-iron balcony: polished wood board with a velvet runner and silver trim; below it a gothic
    iron arcade (tiny pointed arches between bars) with silver drops; iron corbel brackets + finials at the ends."""
    s = Spr(TS, TS)
    for x in range(TS):
        s.set(x, 0, WD[5] if h01(x, 0, 3) > 0.2 else WD[6])
        s.set(x, 1, WD[4] if x % 5 else WD[3])
        s.set(x, 2, VV[3] if (x // 2) % 2 else VV[2])
        s.set(x, 3, SV[3] if h01(x, 3, 8) > 0.15 else SV[4])
        s.set(x, 4, K)
    # arcade frieze rows 5..8: bars every 4px, pointed arches between them
    for x in range(TS):
        m = x % 4
        if m == 0:
            for y in range(5, 9):
                s.set(x, y, IR[5] if y < 8 else IR[4])
        elif m == 2:
            s.set(x, 6, IR[4])
        else:
            s.set(x, 7, IR[3])
        s.set(x, 8, IR[3] if m else IR[4])
    for x in range(0, TS, 8):
        s.set(x, 9, SV[3]); s.set(x, 10, SV[4])            # little silver drop on every other bar
    if kind in ("L", "single"):
        corbel(s, 1, 1)
    if kind in ("R", "single"):
        corbel(s, 14, -1)
    img = s.img
    # outline only where the silhouette ends (the middle joins its neighbours seamlessly)
    px = img.load()
    src = img.copy().load()
    for y in range(TS):
        for x in range(TS):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < TS and 0 <= Y < TS and src[X, Y][3] and src[X, Y] != K:
                    px[x, y] = K
                    break
    if kind in ("L", "single"):
        for y in range(0, 5):
            px[0, y] = K
    if kind in ("R", "single"):
        for y in range(0, 5):
            px[15, y] = K
    return img


def corbel(s, x, sg):
    """End support: an iron scroll bracket curling back under the board, a silver pineapple finial at its foot."""
    for y in range(5, 12):
        s.set(x, y, IR[5] if sg > 0 else IR[3])
    for i, (dx, dy) in enumerate(((1, 6), (2, 7), (3, 7), (4, 6), (4, 5))):
        s.set(x + sg * dx, dy, IR[4])
    s.set(x + sg * 2, 6, IR[2])
    s.set(x, 12, SV[5] if sg > 0 else SV[4])
    s.set(x + sg, 12, SV[3])
    s.set(x, 13, SV[4] if sg > 0 else SV[3])
    s.set(x + sg, 13, SV[2])
    s.set(x, 14, SV[3])


# =========================================================================== spikes
def spikes(down=False):
    s = Spr(TS, TS)
    # horizontal rails
    for x in range(TS):
        s.set(x, 13, IR[4]); s.set(x, 14, IR[2]); s.set(x, 15, IR[1])
    for x in range(0, TS, 2):
        s.set(x, 11, IR[3] if x % 4 == 0 else T)
    for i, cx in enumerate((1, 5, 9, 13)):
        top = (4, 2, 3, 1)[i]
        for y in range(top + 4, 13):
            s.set(cx, y, IR[5]); s.set(cx + 1, y, IR[3])
        # spear head: diamond, silver
        head = [(0, 0, 6), (1, 0, 5), (0, 1, 5), (1, 1, 4), (-1, 2, 4), (0, 2, 5), (1, 2, 4), (2, 2, 3),
                (0, 3, 4), (1, 3, 3)]
        for (dx, dy, c) in head:
            s.set(cx + dx, top + dy, SV[c])
        s.set(cx, top + 4, SV[2]); s.set(cx + 1, top + 4, SV[1])        # collar
    s.outline()
    img = s.img
    if down:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


# =========================================================================== background walls (damask)
DAMASK = [   # 16x16 damask medallion; '#' pattern, '+' pattern highlight
    "................",
    ".......#........",
    "......###.......",
    ".....#.#.#......",
    "....#..#..#.....",
    "...##.###.##....",
    "..#..#+#+#..#...",
    ".##.#+.#.+#.##..",
    "..#..#+#+#..#...",
    "...##.###.##....",
    "....#..#..#.....",
    ".....#.#.#......",
    "......###.......",
    ".......#........",
    "................",
    "#...............",
]


def damask_px(x, y):
    """Pattern value (0 ground, 1 motif, 2 motif highlight) of the tiling damask at torus pixel."""
    ch = DAMASK[y % 16][x % 16]
    return 0 if ch == "." else 2 if ch == "+" else 1


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            v = damask_px(x, y)
            c = DM[2] if v == 0 else DM[3] if v == 1 else DM[4]
            if v == 0 and (x + y * 3) % 11 == 0:
                c = DM[1]                                   # faint woven grain
            px[x, y] = c
    if k == 1:   # paper peeled away showing the dark wood beneath
        for y in range(4, 13):
            for x in range(6, 14):
                e = ((x - 9.5) / 4.2) ** 2 + ((y - 8.5) / 4.6) ** 2 + 0.25 * h01(x, y, 3)
                if e < 1:
                    c = WD[2] if (x + y // 3) % 4 else WD[1]
                    if e > 0.7:
                        c = DM[0]
                    px[x, y] = c
        for (x, y) in ((6, 5), (7, 4), (12, 12), (13, 11)):
            px[x, y] = DM[5]                                # curled paper edge catching light
    elif k == 2:  # faded, darker water blotch
        for y in range(TS):
            for x in range(TS):
                e = ((x - 5) / 6.0) ** 2 + ((y - 10) / 5.0) ** 2
                if e < 1 and px[x, y] in DM:
                    px[x, y] = DM[max(0, DM.index(px[x, y]) - 1)]
    elif k == 3:  # an old dried-blood smear dragged down the wall
        for (x0, y0, ln) in ((9, 2, 12), (10, 3, 9), (11, 2, 7), (8, 5, 5)):
            for y in range(y0, min(16, y0 + ln)):
                px[x0, y] = BL[1] if (y + x0) % 3 else BL[2]
        px[10, 12] = BL[2]; px[9, 14] = BL[1]
    return img


# =========================================================================== decorations
def chain(s, x, y0, y1):
    for y in range(y0, y1):
        if y % 3 == 0:
            s.set(x, y, IR[4]); s.set(x + 1, y, IR[2])
        elif y % 3 == 1:
            s.set(x, y, IR[3])
        else:
            s.set(x, y, IR[5]); s.set(x + 1, y, IR[3])


def deco_lantern():
    s = Spr(TS, TS)
    chain(s, 7, 0, 5)
    # cap
    s.hline(6, 9, 5, SV[4]); s.set(9, 5, SV[2])
    s.hline(5, 10, 6, IR[4]); s.set(10, 6, IR[2])
    # red glass body with iron frame
    for y in range(7, 13):
        for x in range(5, 11):
            if x in (5, 10):
                c = IR[4] if x == 5 else IR[2]
            elif x == 8 and y > 7:
                c = IR[3]
            else:
                c = BL[5] if (y < 10 and x < 8) else BL[4]
                if y == 8 and x == 6:
                    c = BL[7]
                if y >= 11:
                    c = BL[3]
            s.set(x, y, c)
    s.set(7, 10, FL[3]); s.set(7, 9, FL[4]); s.set(6, 10, FL[2])       # the candle inside
    s.hline(5, 10, 13, IR[4]); s.set(10, 13, IR[2])
    s.set(7, 14, SV[3]); s.set(8, 14, SV[2])                          # finial
    s.outline()
    return s.img


def deco_drape():
    s = Spr(TS, TS)
    # rod bracket at the top, velvet hanging in tattered folds
    s.hline(0, 15, 0, IR[3])
    for x in range(1, 15):
        fold = (x - 1) % 5
        ln = 11 + int(3 * h01(x, 1, 21))
        if x in (1, 14):
            ln -= 3
        for y in range(1, ln):
            c = VV[4] if fold == 1 else VV[3] if fold in (0, 2) else VV[2] if fold == 3 else VV[1]
            if y < 3:
                c = VV[5] if fold == 1 else c
            s.set(x, y, c)
        # ragged hem
        if h01(x, 7, 5) < 0.5:
            s.set(x, ln, VV[1])
    # a silver tie tassel
    s.set(6, 4, SV[4]); s.set(7, 4, SV[3]); s.set(6, 5, SV[3]); s.set(6, 6, GL[4]); s.set(6, 7, GL[3])
    s.outline()
    return s.img


def deco_candles():
    s = Spr(TS, TS)
    # three red candles of different heights, pooled wax at the base
    for (x0, top, w) in ((3, 8, 2), (7, 5, 2), (11, 10, 2)):
        for y in range(top, 15):
            for dx in range(w):
                c = WX[3] if dx == 0 else WX[2]
                if y == top:
                    c = WX[4] if dx == 0 else WX[3]
                s.set(x0 + dx, y, c)
        s.set(x0 + w, top + 1, WX[3]); s.set(x0 + w, top + 2, WX[2])        # drip over the rim
        s.set(x0 - 1, top + 3, WX[2])
        s.set(x0, top - 1, K)                                               # wick
    for x in range(1, 15):                                                  # wax pool
        s.set(x, 15, WX[1] if x % 3 else WX[2])
    s.set(2, 14, WX[2]); s.set(13, 14, WX[2]); s.set(10, 14, WX[1])
    s.outline()
    for (x0, top, sd) in ((3, 8, 0), (7, 5, 1), (11, 10, 2)):
        tiny_flame(s, x0, top - 2, 0, sd)
    return s.img


def deco_goblet():
    s = Spr(TS, TS)
    # skull (left, a little back)
    sk = ["..####..", ".######.", "##.##.##", "#..##..#", "########", ".#.#.#..", "..###..."]
    col = {0: SK[4], 1: SK[3], 2: SK[2], 3: SK[1]}
    for j, row in enumerate(sk):
        for i, ch in enumerate(row):
            if ch == "#":
                c = SK[4] if (j < 2 and i < 4) else SK[3] if j < 3 else SK[2]
                s.set(1 + i, 8 + j, c)
            elif j in (2, 3) and ch == ".":
                s.set(1 + i, 8 + j, SK[0])
    # spilled goblet on its side (right), silver, blood pooling out
    for (x, y, c) in ((9, 11, SV[5]), (10, 11, SV[4]), (11, 11, SV[4]), (12, 11, SV[3]),
                      (9, 12, SV[4]), (10, 12, SV[3]), (11, 12, SV[3]), (12, 12, SV[2]),
                      (13, 12, SV[3]), (14, 13, SV[3]), (14, 12, SV[4]), (14, 14, SV[2]), (13, 11, SV[2])):
        s.set(x, y, c)
    s.set(8, 11, BL[2]); s.set(8, 12, BL[3])
    for x in range(3, 10):                                                  # blood pool
        s.set(x, 15, BL[3] if x % 2 else BL[4])
    for x in range(5, 9):
        s.set(x, 14, BL[4] if x != 7 else BL[5])
    # dead roses: two black-red blooms on dry stems
    for (x, y) in ((11, 14), (12, 14), (10, 15), (11, 15), (12, 15), (13, 15)):
        s.set(x, y, IR[3] if y == 15 else VV[1])
    s.set(11, 13, VV[2]); s.set(12, 13, VV[3])
    s.outline()
    return s.img


def deco_tuft():
    """Dead black roses and thorned ivy creeping over a ledge (sits on top of a surface)."""
    s = Spr(TS, TS)
    for x in range(TS):
        h = int(h01(x, 1, 9) * 3) + (1 if x % 7 == 3 else 0)
        for y in range(15 - h, 16):
            c = IR[3] if (x + y) % 3 else IR[4]
            if y == 15 - h:
                c = IR[4]
            s.set(x, y, c)
        if h01(x, 4, 2) < 0.18 and h >= 1:
            s.set(x, 15 - h - 1, IR[2])                                      # a thorn
    # rose blooms (very dark crimson, a single lit petal)
    for (bx, by) in ((3, 12), (11, 13)):
        for (dx, dy, c) in ((0, 0, VV[2]), (1, 0, VV[3]), (0, 1, VV[1]), (1, 1, VV[2]), (-1, 1, VV[1]), (2, 1, VV[1]),
                            (0, -1, VV[4]), (1, -1, VV[2])):
            s.set(bx + dx, by + dy, c)
    s.set(8, 13, BL[2])                                                      # a fallen petal
    return s.outline().img


def breakable():
    img = solid_tile(0)
    px = img.load()
    for (x, y) in ((6, 1), (6, 2), (7, 3), (7, 4), (6, 5), (7, 6), (8, 8), (8, 9), (9, 10), (9, 11), (8, 12), (9, 13)):
        px[x, y] = K
        if x + 1 < 16:
            px[x + 1, y] = ST[4]
    return img


def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [solid_tile(m, variant=True) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(spikes())
    t.append(spikes(down=True))
    t += [bg_wall(k) for k in range(4)]
    t += [deco_lantern(), deco_drape(), deco_candles(), deco_goblet(), breakable(), deco_tuft()]
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t
