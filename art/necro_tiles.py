"""Tileset for the `necropolis` biome -- THE NECROPOLIS OF VAEL (a vertical city of the dead beneath the Catacombs).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8): cold violet-grey ashlar, bone-white capstones along
       every top edge, a thin seam of pale ghost-fire under the capstones where the dead light leaks through
16-31  same masks, variant: ossuary courses -- a row of set-in skulls, or a stacked long-bone course
32-35  one-way platform L / M / R / single: a bone lintel (a long femur-beam on carved brackets)
36/37  floor / ceiling spikes: sharpened bone stakes with pale tips
38-41  background wall: dark ossuary masonry (39 = skull niche, 40 = charnel lattice of skulls, 41 = column, tiles vertically)
42     hanging chain with a small bone chime           43 hanging cage of ribs
44     ghost-fire candles (pale blue)                  45 skull pile
46     breakable wall (looks like 0)                   47 top tuft: bone dust + a stray finger bone
Seam approach as deep/archives: interior texture is a pure function of the in-tile pixel on a 16x16 torus.
"""
import math
from PIL import Image
from envlib import ramp, K, h01, clamp, blank

N, E, S, W = 1, 2, 4, 8
TS = 16

ST = ramp("07070b", "0d0d14", "13131d", "1a1a27", "222232", "2b2b3e", "36354b", "44425c", "56536f", "6e6a86")
BN = ramp("1c1915", "2e2922", "4a4236", "6f6550", "978a6c", "bcae8c", "ddd2b2", "f1ead4")
GH = ramp("0b1732", "142c58", "22498a", "3a70c0", "63a0e6", "a2cdf8", "e4f3ff")
IR = ramp("0a0a0e", "15151c", "22222c", "33333f", "4b4b58", "6c6c7a", "9898a4")

COURSES = [(0, 5, [2, 10]), (6, 10, [6, 14]), (11, 15, [2, 11])]


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
    if mask & N: ds.append(y - 3)
    if mask & S: ds.append(15 - y + 2)
    if mask & W: ds.append(x)
    if mask & E: ds.append(15 - x)
    return max(0, min(ds))


SKULL = ["  ....  ",
         " ...... ",
         "........",
         ".xx..xx.",
         ".xx..xx.",
         "...o....",
         " .t.t.t ",
         "  ....  "]


def put_skull(px, sh, ox, oy, lit=1.0, ghost=False):
    for j, row in enumerate(SKULL):
        for i, ch in enumerate(row):
            x, y = ox + i, oy + j
            if not (0 <= x < TS and 0 <= y < TS) or not sh[y][x] or px[x, y] == K:
                continue
            if ch == ".":
                lv = 5 if j < 2 else 4 if j < 5 else 3
                if i <= 1: lv += 1
                if i >= 6: lv -= 1
                px[x, y] = BN[int(clamp(lv * lit, 1, 7))]
            elif ch == "x":
                px[x, y] = GH[3] if ghost and (i in (1, 5) and j == 3) else BN[0]
            elif ch == "o":
                px[x, y] = BN[1]
            elif ch == "t":
                px[x, y] = BN[2]


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
            if not sh[y][x]:
                continue
            ci, bi, lx, ly, bw, bh, joint = block(x, y)
            cen = ((COURSES[ci][2][bi] + bw / 2) % 16, COURSES[ci][0] + bh / 2)
            d = depth_of(mask, *cen) + 2.5 * h01(int(cen[0] * 3), int(cen[1] * 5), 7)
            tone = (0, 1, -1, 0, 1, -1)[(ci * 3 + bi * 2) % 6]
            lv = 6 + tone
            if joint:
                px[x, y] = ST[1]
                continue
            if ly == 0: lv += 1
            elif ly == bh - 2: lv -= 1
            if lx == 1: lv += 1
            elif lx == bw - 1: lv -= 1
            r = h01(x, y, 19 + ci)
            if r < 0.08: lv -= 1
            elif r > 0.965: lv += 1
            k = (d > 4) + (d > 7) + (d > 10)
            lv -= (0, 2, 3, 4)[k]
            if k >= 2:
                lv = min(lv, 2)
            if mask & W and x < 2: lv += 1
            if mask & E and x > 13: lv -= 1
            px[x, y] = ST[int(clamp(lv, 0, 9))]
    if variant:
        variant_features(px, sh, mask)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, -1, 0) and not (mask & N and y < 4):
                px[x, y] = ST[8] if y % 5 else ST[9]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & S:   # underside: faint cold bounce
        for x in range(TS):
            for y in range(14, 10, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = GH[0] if (x + y) % 3 else ST[3]
                    break
    if mask & N:
        capstone(px, sh, mask, out)
    return img


def capstone(px, sh, mask, out):
    """Bone-white capstones along the top edge; a thin ghost-fire seam leaks under them."""
    for x in range(TS):
        for y in range(4):
            if not sh[y][x]:
                continue
            seg = (x + 3) % 8 == 0
            c = (BN[6], BN[5], BN[4], BN[2])[y]
            if y == 0 and h01(x, 0, 81) < 0.18:
                c = BN[7]
            if y == 1 and h01(x, 1, 82) < 0.15:
                c = BN[4]
            if seg and y > 0:
                c = BN[1]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else BN[3]
            elif out(x, y, -1, 0) or (mask & W and x == 0):
                c = BN[7] if y < 2 else BN[4]
            px[x, y] = c
        if sh[4][x] and px[x, 4] != K and not (mask & E and x >= 14) and not (mask & W and x <= 0):
            px[x, 4] = GH[2] if h01(x, 4, 12) < 0.45 else ST[1]
            if h01(x, 4, 13) < 0.15 and sh[5][x]:
                px[x, 5] = GH[1]


def variant_features(px, sh, mask):
    """Variants: a set-in skull (ossuary course) or a course of stacked long bones. Deep interior stays quiet."""
    if mask == 0:
        for (x, y) in ((4, 4), (5, 5), (5, 6), (6, 7), (6, 8), (7, 9)):
            if sh[y][x]:
                px[x, y] = ST[0]
        return
    top = 6 if mask & N else 3
    if mask in (1, 3, 9, 4, 6, 12):
        ox = 4 if not mask & W else 6
        # dark niche behind the skull
        for y in range(top - 1, top + 9):
            for x in range(ox - 1, ox + 9):
                if 0 <= x < TS and 0 <= y < TS and sh[y][x] and px[x, y] != K:
                    px[x, y] = ST[1] if (x in (ox - 1, ox + 8) or y in (top - 1, top + 8)) else ST[0]
        put_skull(px, sh, ox, top, lit=0.75, ghost=(mask & N) and h01(mask, 3, 5) < 0.5)
    else:
        for yy in (top + 1, top + 5):
            for x in range(1, 15):
                for dy in range(3):
                    y = yy + dy
                    if y >= TS or not sh[y][x] or px[x, y] == K:
                        continue
                    knob = x in (1, 2, 13, 14)
                    c = BN[5 if dy == 0 else 4 if dy == 1 else 2]
                    if knob and dy == 1:
                        c = BN[6] if x < 8 else BN[3]
                    if not knob and dy == 1:
                        c = BN[3]
                    px[x, y] = c


# =========================================================================== platform, spikes
def platform(kind):
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        for y in range(5):
            if y == 0:
                c = BN[6] if h01(x, 0, 3) > 0.2 else BN[7]
            elif y == 1:
                c = BN[5]
            elif y == 2:
                c = BN[4] if (x + 2) % 7 else BN[2]
            elif y == 3:
                c = BN[2]
            else:
                c = K
            px[x, y] = c

    def bracket(x0, sgn):
        for i in range(7):
            x = x0 + sgn * (i // 2)
            y = 5 + i
            if 0 <= x < TS:
                px[x, y] = BN[3] if i < 6 else K
                if 0 <= x + sgn < TS and i < 5:
                    px[x + sgn, y] = BN[1]
        for y in range(5, 8):
            px[x0, y] = BN[4]
    if kind in ("L", "single"):
        px[0, 0] = K; px[0, 1] = BN[7]; px[0, 2] = BN[6]; px[0, 3] = BN[3]
        px[1, 0] = BN[7]
        bracket(3, 1)
    if kind in ("R", "single"):
        px[15, 0] = K; px[15, 1] = BN[3]; px[15, 2] = BN[2]; px[15, 3] = K
        bracket(12, -1)
    if kind == "M":
        for y in range(5, 12):
            px[6, y] = IR[4] if y % 2 else IR[2]
        px[6, 12] = GH[3]
    return img


def spikes(down=False):
    img = blank(TS, TS)
    px = img.load()
    base = 15
    for (cx, h, w) in ((2.5, 10, 1.7), (6.5, 14, 2.0), (10.5, 11, 1.8), (13.8, 8, 1.5)):
        for y in range(base - h, base + 1):
            t = (base - y) / h
            hw = w * (1 - t) + 0.3
            for x in range(int(cx - hw - 1), int(cx + hw + 2)):
                if not (0 <= x < TS):
                    continue
                dx = x + 0.5 - cx
                if abs(dx) > hw:
                    continue
                if t > 0.8:
                    c = GH[5] if t > 0.92 else BN[7]
                elif dx < -0.2:
                    c = BN[6] if t > 0.4 else BN[5]
                else:
                    c = BN[3] if t < 0.5 else BN[4]
                px[x, y] = c
    for x in range(TS):
        px[x, 15] = ST[3] if h01(x, 1, 4) < 0.6 else BN[2]
    out = blank(TS, TS)
    op = out.load()
    for y in range(TS):
        for x in range(TS):
            c = px[x, y]
            if c[3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < TS and 0 <= Y < TS and px[X, Y][3]:
                        op[x, y] = K
                        break
            else:
                op[x, y] = c
    if down:
        out = out.transpose(Image.FLIP_TOP_BOTTOM)
    return out


# =========================================================================== background wall
D = ramp("06060a", "0a0a10", "0f0f17", "14141e", "1a1a26")


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            row = y // 4
            off = 0 if row % 2 else 4
            joint = (y % 4 == 3) or ((x + off) % 8 == 7)
            lv = 1 if joint else 2 + (1 if (y % 4 == 0) else 0)
            if h01(x + k * 16, y, 51) < 0.1:
                lv -= 1
            px[x, y] = D[int(clamp(lv, 0, 4))]
    if k == 1:     # plain, a different bond + a hairline crack
        for (x, y) in ((11, 1), (11, 2), (10, 3), (10, 4), (9, 5), (9, 6), (10, 7)):
            px[x, y] = D[0]
    if k == 2:     # a skull resting in an arched niche (dim)
        for y in range(3, 14):
            for x in range(3, 13):
                arch = y > 5 or (x - 7.5) ** 2 + (y - 6) ** 2 <= 20
                if arch:
                    px[x, y] = D[0]
        for j, row in enumerate(SKULL):
            for i, ch in enumerate(row):
                x, y = 4 + i, 6 + j
                if ch == ".":
                    px[x, y] = BN[2] if j < 3 else BN[1]
                elif ch in "xo":
                    px[x, y] = D[0]
                elif ch == "t":
                    px[x, y] = BN[0]
    if k == 99:    # charnel lattice (unused: too busy as a random fill)
        for y0 in (1, 9):
            for x0 in (0, 8):
                for j in range(6):
                    for i in range(7):
                        e = ((i - 3) / 3.4) ** 2 + ((j - 2.2) / 2.8) ** 2
                        if e <= 1:
                            x, y = x0 + i, y0 + j
                            c = BN[2] if j < 3 else BN[1]
                            if j == 2 and i in (1, 2, 4, 5):
                                c = D[0]
                            if j == 4 and i == 3:
                                c = D[0]
                            px[x, y] = c
    if k == 3:     # a thin rib of bone mortared into the wall
        for x in range(2, 14):
            px[x, 9] = BN[1] if x % 3 else D[0]
    if k == 98:    # a fluted column (tiles vertically)
        for y in range(TS):
            for x in range(5, 11):
                c = ST[3] if x in (6, 8) else ST[2] if x < 10 else ST[1]
                if x == 5:
                    c = D[0]
                if y in (0, 8):
                    c = ST[4] if x < 10 else ST[2]
                px[x, y] = c
    return img


# =========================================================================== decorations
def chain_col(px, x, y0, y1):
    for y in range(y0, y1):
        if y % 3 == 0:
            px[x, y] = IR[4]; px[x + 1, y] = IR[2]
        elif y % 3 == 1:
            px[x, y] = IR[3]
        else:
            px[x, y] = IR[5]
            px[x + 1, y] = IR[3]


def outline_k(img, skip=()):
    w, h = img.size
    src = img.load()
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and src[X, Y][3] and (X, Y) not in skip:
                    op[x, y] = K
                    break
    return out


def deco_chime():
    img = blank(TS, TS)
    px = img.load()
    chain_col(px, 7, 0, 9)
    for x in range(4, 12):
        px[x, 9] = BN[3]
    for (x, l) in ((4, 4), (7, 5), (10, 3)):
        for y in range(10, 10 + l):
            px[x, y] = BN[5] if y < 10 + l - 1 else BN[6]
    return outline_k(img)


def deco_cage():
    img = blank(TS, TS)
    px = img.load()
    chain_col(px, 7, 0, 4)
    for y in range(4, 15):
        t = (y - 4) / 10
        hw = 1 + 4.5 * math.sin(t * math.pi)
        for sgn in (-1, 1):
            x = int(round(7.5 + sgn * hw))
            if 0 <= x < TS:
                px[x, y] = BN[5] if sgn < 0 else BN[3]
        if y in (7, 10, 13):
            for x in range(int(8 - hw) + 1, int(7.5 + hw)):
                px[x, y] = BN[2]
    px[7, 15] = BN[4]
    return outline_k(img)


def deco_candles():
    img = blank(TS, TS)
    px = img.load()
    for (x0, h) in ((3, 5), (7, 8), (11, 4)):
        for y in range(15 - h, 16):
            px[x0, y] = BN[6] if y < 15 - h + 2 else BN[5]
            px[x0 + 1, y] = BN[4]
        # pale-blue flame
        top = 15 - h
        px[x0, top - 1] = GH[6]; px[x0 + 1, top - 1] = GH[5]
        px[x0, top - 2] = GH[5]; px[x0 + 1, top - 2] = GH[4]
        px[x0, top - 3] = GH[4]
    for x in range(2, 14):
        px[x, 15] = BN[3] if h01(x, 15, 3) < 0.6 else BN[2]    # wax pool
    skip = {(x, y) for x in range(TS) for y in range(TS) if px[x, y] in (GH[4], GH[5], GH[6])}
    return outline_k(img, skip=skip)


def deco_skulls():
    img = blank(TS, TS)
    px = img.load()
    sh = [[True] * TS for _ in range(TS)]
    for y in range(12, 16):
        for x in range(1, 15):
            if h01(x, y, 44) < 0.8 - (15 - y) * 0.15:
                px[x, y] = BN[3] if h01(x, y, 9) < 0.5 else BN[2]
    put_skull(px, sh, 1, 8, 0.9)
    put_skull(px, sh, 7, 9, 0.8)
    put_skull(px, sh, 4, 4, 1.0)
    return outline_k(img)


def deco_tuft():
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        h = int(h01(x, 1, 5) * 2.4)
        for y in range(15 - h, 16):
            px[x, y] = BN[3] if y > 15 - h else BN[4]
    for x0 in (3, 11):
        if h01(x0, 3, 8) < 0.7:
            px[x0, 14] = BN[6]; px[x0 + 1, 14] = BN[5]; px[x0 + 2, 13] = BN[5]
    return img


def breakable():
    img = solid_tile(0)
    px = img.load()
    for (x, y) in ((6, 2), (7, 3), (7, 4), (6, 5), (7, 6), (8, 7), (8, 8), (9, 9), (9, 10), (8, 11), (9, 12)):
        px[x, y] = ST[0]
        if x + 1 < 16:
            px[x + 1, y] = ST[6]
    return img


def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [solid_tile(m, variant=True) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(spikes())
    t.append(spikes(down=True))
    t += [bg_wall(k) for k in range(4)]
    t += [deco_chime(), deco_cage(), deco_candles(), deco_skulls(), breakable(), deco_tuft()]
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t
