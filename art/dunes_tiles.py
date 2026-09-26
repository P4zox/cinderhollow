"""Tileset for the `dunes` biome -- THE SUNSCORCHED DUNES (the buried desert of the sun-kings).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8): big dressed sandstone blocks, the joints choked
       with drifted sand; every exposed top carries a thick cap of wind-rippled gold sand (its crest catches the sun)
16-31  same masks, variant: hieroglyph-carved blocks (a sun-disc, an eye, a scarab), one with a lapis-and-gold inlay band
32-35  one-way platform L / M / R / single: a broken sandstone lintel with a gilt cavetto band, sand spilling off the ends
36/37  floor / ceiling spikes: gilded bronze spear-heads set in sand
38-41  background wall: shadowed sandstone courses with faint relief; 41 = a papyrus-bundle column (tiles vertically)
42     hanging chain with a gold scarab amulet        43 hanging linen shrouds (tattered, pale)
44     oil lamp on a tripod (flame)                     45 broken canopic jar + sand + a skull
46     breakable wall (looks like 0)                    47 top tuft: a drift of loose sand
Plus `tiles_dunes_fx`: qs_top (6, quicksand surface slowly churning), qs_body (4), slope (1: the sand lip + body for the
sand-surf slopes, one column per depth pixel), sand (1: deep dune sand, tileable).
Seam approach as deep/env2: every interior texture is a pure function of the in-tile pixel on a 16x16 torus.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, pick

N, E, S, W = 1, 2, 4, 8
TS = 16

# sandstone (warm ochre stone) and dune sand (gold), gilt, lapis, shadow
ST = ramp("140c08", "1e140d", "2a1c12", "382617", "47301c", "583c22", "6c4b2b", "835c35", "9c7042", "b58752", "cda066")
SD = ramp("2a1809", "3f250e", "573413", "704518", "8a581f", "a56d28", "bf8534", "d6a048", "e8bd66", "f6d994", "fff0c4")
GD = ramp("2b1a0e", "4f3314", "7d5519", "b2822a", "dfb24a", "fbe7a0", "fffbe8")
LP = ramp("0c1224", "16244a", "22407a", "3a64a8", "6a94cc")
BZ = ramp("1a0e08", "33200f", "553616", "7e5220", "a8742e", "d6a04a")      # bronze
LN = ramp("3a3026", "5e5040", "84735c", "a8977a", "cbbc9c", "e9dfc4")      # linen
SH = (18, 10, 6, 255)

COURSES = [(0, 6, [2, 10]), (7, 11, [6, 14]), (12, 15, [1, 9])]     # masonry courses on the torus: (y0, y1, joints)


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
    if mask & E: ds.append(15 - x)
    return max(0, min(ds))


def sand_cap_h(x):
    """Height of the sand cap on exposed tops: wind ripples (tileable in x)."""
    return 5 + int(round(1.2 * math.sin(x * 2 * math.pi / 16 * 2 + 0.6) + 0.6 * math.sin(x * 2 * math.pi / 16 * 3)))


def sand_px(x, y, d):
    """Dune sand at depth d below its surface (the ripple lines run diagonally)."""
    rip = (x * 2 + y * 5) % 11
    v = 8.2 - d * 0.9
    if rip == 0:
        v -= 1.3
    elif rip == 1:
        v += 0.6
    if h01(x, y, 71) < 0.08:
        v -= 1.0
    if h01(x, y, 72) > 0.96:
        v += 1.0
    return SD[int(clamp(round(v), 1, 9))]


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
            d = depth_of(mask, x, y)
            if joint:
                # joints full of drifted sand, darker deep inside
                px[x, y] = SD[3] if d < 4 else SD[2] if d < 8 else ST[1]
                if h01(x, y, 5) < 0.25 and d < 6:
                    px[x, y] = SD[4]
                continue
            tone = (0, 1, -1, 1, 0, -1)[(ci * 3 + bi * 2) % 6]
            lv = 7 + tone
            if ly == 0: lv += 1
            elif ly == bh - 2: lv -= 1
            if lx == 1: lv += 1
            elif lx == bw - 1: lv -= 1
            r = h01(x, y, 19 + ci)
            if r < 0.1: lv -= 1
            elif r > 0.95: lv += 1
            if (x + y * 3) % 7 == 0 and h01(x, y, 23) < 0.4:
                lv -= 1                                       # sandstone strata pits
            k = (d > 3) + (d > 6) + (d > 9)
            lv -= (0, 2, 4, 5)[k]
            if mask & W and x < 2: lv += 1
            if mask & E and x > 13: lv -= 1
            px[x, y] = ST[int(clamp(lv, 0, 10))]
    if variant:
        variant_features(px, sh, mask)
    # faces: dark outline on E / S / W; the W face gets a thin sunlit rim
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, -1, 0) and not (mask & N and y < 6):
                px[x, y] = ST[8] if y % 5 else ST[9]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & S:   # underside: warm bounce light off the sand below
        for x in range(TS):
            for y in range(14, 10, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = ST[5] if (x + y) % 3 else ST[6]
                    break
    if mask & N:
        sand_cap(px, sh, mask, out)
    return img


def sand_cap(px, sh, mask, out):
    """A thick cap of wind-rippled sand on every exposed top; bright crest line, it spills a little over the side faces."""
    for x in range(TS):
        hgt = sand_cap_h(x)
        if mask & W and x < 3:
            hgt += 1                                          # sand spills over the rim
        if mask & E and x > 12:
            hgt += 1
        for y in range(hgt + 1):
            if not sh[y][x]:
                continue
            if y == 0:
                c = SD[10] if h01(x, 0, 81) < 0.35 else SD[9]
            elif y == 1:
                c = SD[8]
            elif y == hgt:
                c = SD[3] if h01(x, y, 3) < 0.6 else ST[3]    # the sand meets the stone: shadow line
            else:
                c = sand_px(x, y, y)
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y > 0 else SD[6]
            elif out(x, y, -1, 0) or (mask & W and x == 0):
                c = SD[9] if y < 2 else SD[7]
            px[x, y] = c


def variant_features(px, sh, mask):
    """Carved hieroglyphs on some blocks (sun-disc, eye, scarab); gold / lapis inlay on others. Deep tiles stay quiet."""
    if mask == 0:
        for (x, y) in ((4, 3), (5, 4), (5, 5), (6, 6), (6, 7)):
            if sh[y][x]:
                px[x, y] = ST[1]
        return
    kind = mask % 3
    oy = 7 if mask & N else 3
    if mask & S:
        oy = min(oy, 5)

    def carve(pts, c=None):
        for (x, y) in pts:
            X, Y = x, y + oy
            if 0 <= X < TS and 0 <= Y < TS and sh[Y][X] and px[X, Y] != K:
                px[X, Y] = c or ST[2]
                if X + 1 < TS and Y + 1 < TS and sh[Y + 1][X + 1] and px[X + 1, Y + 1] not in (K,):
                    px[X + 1, Y + 1] = ST[8] if c is None else px[X + 1, Y + 1]
    if kind == 0:   # sun-disc with rays
        ring = [(x, y) for y in range(0, 7) for x in range(4, 12) if 2.0 < math.hypot(x + .5 - 8, y + .5 - 3.2) < 3.1]
        carve(ring)
        carve([(8, 3)], GD[4])
        carve([(3, 3), (13, 3), (8, -1)])
    elif kind == 1:  # the eye
        eye = [(4, 3), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 3), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (6, 6), (5, 7), (9, 5), (10, 6)]
        carve(eye)
        carve([(7, 3)], LP[3])
    else:           # inlay band: lapis and gold squares across the block
        for x in range(2, 14):
            for yy in (2, 3):
                X, Y = x, oy + yy
                if sh[Y][X] and px[X, Y] != K:
                    px[X, Y] = (GD[4] if yy == 2 else GD[3]) if (x // 2) % 2 else (LP[3] if yy == 2 else LP[2])
        for x in range(2, 14):
            if sh[oy + 4][x] and px[x, oy + 4] != K:
                px[x, oy + 4] = ST[2]


# =========================================================================== platform, spikes
def platform(kind):
    """Broken sandstone lintel: sand on top, a gilt cavetto band, blocky ends (sand spilling off)."""
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        for y in range(6):
            if y == 0:
                c = SD[9] if h01(x, 0, 3) > 0.3 else SD[10]
            elif y == 1:
                c = SD[7]
            elif y == 2:
                c = GD[4] if (x % 4) else GD[3]
            elif y == 3:
                c = ST[7] if (x + 1) % 8 else ST[5]
            elif y == 4:
                c = ST[5]
            else:
                c = K
            px[x, y] = c
    if kind in ("L", "single"):
        for y in range(6):
            px[0, y] = K if y else SD[7]
        for y in range(6, 9):
            px[1, y] = SD[6] if y < 8 else SD[4]               # sand trickle
    if kind in ("R", "single"):
        for y in range(6):
            px[15, y] = K if y else SD[7]
        for y in range(6, 10):
            px[14, y] = SD[6] if y < 9 else SD[4]
    if kind == "M":
        px[8, 3] = ST[4]
    return img


def spikes(down=False):
    img = blank(TS, TS)
    px = img.load()
    base = 15
    for (cx, h, w) in ((2.5, 9, 1.9), (6.5, 13, 2.3), (10.5, 11, 2.1), (13.8, 7, 1.6)):
        for y in range(base - h, base + 1):
            t = (base - y) / h
            hw = w * (1 - t) + 0.25
            for x in range(int(cx - hw - 1), int(cx + hw + 2)):
                if not (0 <= x < TS):
                    continue
                dx = x + 0.5 - cx
                if abs(dx) > hw:
                    continue
                if t > 0.78:
                    c = GD[6] if t > 0.92 else GD[5]
                elif dx < -0.2:
                    c = GD[4] if t > 0.4 else BZ[4]
                else:
                    c = BZ[2] if t < 0.5 else BZ[3]
                px[x, y] = c
    for x in range(TS):                                      # sand at the base
        for y in (14, 15):
            if not px[x, y][3] or y == 15:
                px[x, y] = SD[6] if (y == 14) else SD[4]
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
def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    D = ramp("0e0805", "150c07", "1d110a", "26170d", "301d10")
    for y in range(TS):
        for x in range(TS):
            row = y // 5
            off = 0 if row % 2 else 5
            joint = (y % 5 == 4) or ((x + off) % 10 == 9)
            lv = 1 if joint else 2 + (1 if (y % 5 == 0) else 0)
            if h01(x + k * 16, y, 51) < 0.1:
                lv -= 1
            px[x, y] = D[int(clamp(lv, 0, 4))]
    if k == 1:     # faint relief: a walking figure in profile
        for (x, y) in ((7, 2), (7, 3), (6, 4), (7, 4), (8, 4), (7, 5), (7, 6), (6, 7), (8, 7), (6, 8), (9, 8), (5, 9), (9, 9)):
            px[x, y] = D[4]
    if k == 2:     # a sun-disc niche
        for y in range(3, 11):
            for x in range(4, 12):
                d = math.hypot(x + .5 - 8, y + .5 - 7)
                if d < 3.8:
                    px[x, y] = D[0] if d > 2.6 else (GD[1] if d < 1.4 else D[1])
    if k == 3:     # papyrus-bundle column (tiles vertically)
        for y in range(TS):
            for x in range(4, 12):
                c = D[3] if x in (5, 8) else D[2] if x < 10 else D[1]
                if x == 4:
                    c = D[0]
                if y in (6, 7):
                    c = D[4] if x < 10 else D[2]           # binding band
                px[x, y] = c
    return img


# =========================================================================== decorations
def chain_col(px, x, y0, y1):
    for y in range(y0, y1):
        if y % 3 == 0:
            px[x, y] = BZ[4]; px[x + 1, y] = BZ[2]
        elif y % 3 == 1:
            px[x, y] = BZ[3]
        else:
            px[x, y] = BZ[5]; px[x + 1, y] = BZ[3]


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


def deco_hang():
    """Chain with a gold scarab amulet."""
    img = blank(TS, TS)
    px = img.load()
    chain_col(px, 7, 0, 9)
    sc = ["  .##.  ", " ###### ", "##o##o##", " ###### ", " ##..## ", "  ####  ", "   ##   "]
    for j, row in enumerate(sc):
        for i, ch in enumerate(row):
            X, Y = 4 + i, 9 + j - 1
            if Y >= TS:
                continue
            if ch == "#":
                px[X, Y] = GD[4] if (i < 4 and j < 3) else GD[3]
            elif ch == "o":
                px[X, Y] = LP[3]
            elif ch == ".":
                px[X, Y] = GD[5]
    return outline_k(img)


def deco_shroud():
    """Tattered linen strips hanging from above."""
    img = blank(TS, TS)
    px = img.load()
    for (x0, L, sw) in ((3, 12, 0.6), (7, 15, -0.5), (11, 10, 0.4)):
        for y in range(L):
            x = int(round(x0 + math.sin(y * 0.5 + x0) * 0.8 + sw * y * 0.1))
            for dx in (0, 1):
                X = x + dx
                if 0 <= X < TS:
                    c = LN[3] if dx == 0 else LN[2]
                    if y % 5 == 4:
                        c = LN[1]
                    px[X, y] = c
        tip = L
        if tip < TS:
            px[int(round(x0 + sw * tip * 0.1)), tip - 1] = LN[1]
    return outline_k(img)


def deco_lamp():
    """Bronze tripod oil lamp with a small flame."""
    img = blank(TS, TS)
    px = img.load()
    for (a, b) in (((5, 15), (7, 9)), ((11, 15), (9, 9)), ((8, 15), (8, 9))):
        n = 7
        for i in range(n):
            t = i / (n - 1)
            px[int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t))] = BZ[3] if i % 2 else BZ[4]
    for x in range(5, 12):
        px[x, 8] = BZ[4] if x < 9 else BZ[3]
        px[x, 7] = BZ[5] if x in (5, 11) else BZ[2]
    for (x, y, c) in ((8, 6, GD[5]), (8, 5, GD[6]), (7, 6, GD[4]), (9, 6, GD[4]), (8, 4, GD[5]), (8, 3, GD[4])):
        px[x, y] = c
    return outline_k(img, skip={(8, 3), (8, 4)})


def deco_jar():
    """A broken canopic jar lying in the sand, a skull beside it."""
    img = blank(TS, TS)
    px = img.load()
    for y in range(12, 16):
        for x in range(0, 16):
            if h01(x, y, 44) < 0.85 - (15 - y) * 0.25:
                px[x, y] = SD[5] if h01(x, y, 9) < 0.6 else SD[4]
    for y in range(7, 14):
        for x in range(2, 9):
            e = ((x + .5 - 5.5) / 3.4) ** 2 + ((y + .5 - 10.5) / 3.6) ** 2
            if e < 1 and not (x > 6 and y < 10):              # broken shoulder
                px[x, y] = LN[4] if x < 5 else LN[3] if x < 7 else LN[2]
                if y == 10:
                    px[x, y] = LP[2] if x % 2 else GD[3]
    sk = [" ... ", ".x.x.", ".....", " o.o "]
    for j, row in enumerate(sk):
        for i, ch in enumerate(row):
            if ch == ".":
                px[10 + i, 10 + j] = LN[4] if j < 2 else LN[3]
            elif ch in "xo":
                px[10 + i, 10 + j] = SH
    return outline_k(img)


def deco_tuft():
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        h = int(1 + 2.4 * (0.5 + 0.5 * math.sin(x * 0.55 + 1.3)) * (0.6 + 0.4 * h01(x, 1, 5)))
        for y in range(15 - h, 16):
            px[x, y] = SD[9] if y == 15 - h else SD[8]
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
    t += [deco_hang(), deco_shroud(), deco_lamp(), deco_jar(), breakable(), deco_tuft()]
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t


# =========================================================================== animated / special tiles (tiles_dunes_fx)
QS = ramp("2a1809", "3f250e", "573413", "6f4518", "87561f", "a06a28", "b88034", "cf9a48")


def qs_top(f, n=6):
    """Quicksand surface: a slow churn -- dimples drift inward, a dark swirl line, damp sheen. Tileable in x and time."""
    img = blank(TS, TS)
    px = img.load()
    ph = f / n * 2 * math.pi
    for x in range(TS):
        w = 0.8 * math.sin(ph + x * 2 * math.pi / 16) + 0.5 * math.sin(-ph * 2 + x * 4 * math.pi / 16)
        top = int(round(2 + w))
        for y in range(top, TS):
            d = y - top
            v = 6.3 - d * 0.42
            sw = math.sin((x + f * 2.67) * 2 * math.pi / 16 * 2 + y * 0.9)
            if sw > 0.86:
                v -= 1.6                                      # swirl furrow
            elif sw < -0.9:
                v += 0.8
            if h01((x + f * 3) % 16, y, 7) < 0.07:
                v -= 1.2
            c = QS[int(clamp(round(v), 0, 7))]
            if d == 0:
                c = QS[7] if h01((x - f) % 16, 1, 9) < 0.5 else QS[6]
            px[x, y] = c
    return img


def qs_body(f, n=4):
    """Deep quicksand: a slow, lumpy churn (tileable value noise drifting down), darker with no hard pattern."""
    from envlib import vnoise
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            tau = 2 * math.pi / 16
            yy = y + f * 4
            v = 0.5 + 0.2 * math.sin(tau * (x + 2 * yy) + 1.1) + 0.17 * math.sin(tau * (3 * x - yy) + 2.3) + 0.13 * math.sin(tau * (2 * x + 3 * yy) + 0.4)
            lv = 1.2 + v * 2.6
            if h01(x, (y + f * 4) % 16, 3) < 0.04:
                lv += 1.5
            px[x, y] = QS[int(clamp(round(lv), 0, 5))]
    return img


def slope_tile():
    """Column k of row d = the look of dune sand d px below a slope's surface (bright crest, rippled, darkening)."""
    img = blank(TS, TS)
    px = img.load()
    for d in range(TS):
        for x in range(TS):
            if d == 0:
                c = SD[10] if h01(x, 0, 11) < 0.4 else SD[9]
            elif d == 1:
                c = SD[9] if h01(x, 1, 12) < 0.3 else SD[8]
            elif d == 2:
                c = SD[7]
            else:
                c = sand_px(x, d + 2, d * 0.55)
            px[x, d] = c
    return img


def deep_sand():
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            rip = (x * 2 + y * 5) % 11
            v = 4.6
            if rip == 0:
                v -= 1.0
            elif rip == 1:
                v += 0.5
            if h01(x, y, 91) < 0.07:
                v -= 1
            if h01(x, y, 92) > 0.97:
                v += 1
            px[x, y] = SD[int(clamp(round(v), 1, 9))]
    return img


def build_fx():
    """-> (w, h, layers, frames, tags) for tiles_dunes_fx."""
    frames, tags = [], []
    def add(tag, ims):
        a = len(frames)
        for im in ims:
            frames.append({"ms": 140, "cels": {"Tiles": im}})
        tags.append((tag, a, len(frames) - 1))
    add("qs_top", [qs_top(f) for f in range(6)])
    add("qs_body", [qs_body(f) for f in range(4)])
    add("slope", [slope_tile()])
    add("sand", [deep_sand()])
    return (16, 16, ["Tiles"], frames, tags)
