"""Tileset for the `deep` biome -- THE BURNING DEEP (the root-forges beneath the Mire).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8): forge masonry of heat-scorched basalt blocks,
       the joints near exposed faces glowing with magma, a riveted iron coping along every top edge
16-31  same masks, variant: petrified heartwood roots (charcoal-black, ember-cracked) and iron clamp plates
32-35  one-way platform L / M / R / single: iron grate catwalk on brackets, glowing slag caught in the grate
36/37  floor / ceiling spikes: obsidian slag shards, hot at the tips
38-41  background wall: soot-dark firebrick with iron pipes (41 = pipe column, tiles vertically)
42     hanging chain with a forge hook            43 hanging tongs + a cooling ingot
44     glowing coal heap                            45 slag clinker + a charred skull
46     breakable wall (looks like 0)                47 top tuft: ash and cinders
Plus `tiles_deep_fx` (built from here too): animated lava surface / body and conveyor belt pieces.
Seam approach as env2/archives: the interior texture is a pure function of the in-tile pixel on a 16x16 torus.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank

N, E, S, W = 1, 2, 4, 8
TS = 16

ST = ramp("0b0707", "140d0c", "1d1412", "281b17", "35241e", "442e25", "553a2e", "6b4a3a", "86604a", "a67c5e")
MG = ramp("3a0906", "661107", "9c1f09", "cf3b0c", "f26414", "ff9a2e", "ffcf66", "fff3cc")
IR = ramp("0b0809", "161112", "221a19", "342824", "4f3d32", "7a634c", "a08466")
GD = ramp("2b1a0e", "4f3314", "7d5519", "b2822a", "dfb24a", "fbe7a0")
CH = ramp("0a0808", "121010", "1c1818", "282222", "3a302c")          # charcoal (petrified root)
ASH = ramp("1d1716", "2c2422", "3e3430", "574a43", "7a6a60", "a09080")

# masonry courses on the torus: (y0, y1, joints x)
COURSES = [(0, 5, [3, 11]), (6, 10, [7]), (11, 15, [1, 13])]


def wrap16(d):
    d %= 16
    return d - 16 if d >= 8 else d


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
    if mask & S:
        for x in range(2, 14):
            if h01(x, 5, 33) < 0.14:
                sh[15][x] = False
    return sh


def depth_of(mask, x, y):
    ds = [99]
    if mask & N: ds.append(y - 3)
    if mask & S: ds.append(15 - y + 2)
    if mask & W: ds.append(x)
    if mask & E: ds.append(15 - x)
    return max(0, min(ds))


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
            tone = (0, 1, -1, 1, 0, -1)[(ci * 3 + bi * 2) % 6]
            lv = 5 + tone
            if joint:
                # joints: dark, and molten near an exposed face (the forge heat seeps through the mortar)
                near = depth_of(mask, x, y)
                if near < 5 and (mask & (N | W | E)) and h01(x, y, 41) < 0.8:
                    c = MG[3] if near < 2 else MG[2] if near < 3 else MG[1]
                    px[x, y] = c
                    continue
                px[x, y] = ST[1]
                continue
            if ly == 0: lv += 1
            elif ly == bh - 2: lv -= 1
            if lx == 1: lv += 1
            elif lx == bw - 1: lv -= 1
            r = h01(x, y, 19 + ci)
            if r < 0.09: lv -= 1
            elif r > 0.96: lv += 1
            # heat: blocks near the surface warm up from below (the whole Deep glows from underneath)
            k = (d > 4) + (d > 7) + (d > 10)
            lv -= (0, 2, 3, 4)[k]
            if k >= 2:
                lv = min(lv, 2)
            if mask & W and x < 2: lv += 1
            if mask & E and x > 13: lv -= 1
            px[x, y] = ST[int(clamp(lv, 0, 9))]
    if variant:
        variant_features(px, sh, mask)
    # faces: outline on E / S, soot-rim on W
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, -1, 0) and not (mask & N and y < 4):
                px[x, y] = ST[7] if y % 5 else ST[8]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & S:   # underside: hot bounce light from the lava below
        for x in range(TS):
            for y in range(14, 9, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = MG[1] if (x + y) % 3 else MG[2]
                    break
    if mask & N:
        coping(px, sh, mask, out)
    return img


def coping(px, sh, mask, out):
    """Riveted iron coping along the top: lit worn edge, dark band with rivets, a molten seam beneath it."""
    for x in range(TS):
        for y in range(4):
            if not sh[y][x]:
                continue
            c = (IR[5], IR[4], IR[2], IR[1])[y]
            if y == 0 and h01(x, 0, 81) < 0.2:
                c = IR[6]
            if y == 2 and x % 8 == 4:
                c = IR[5]                                 # rivet head
            if y == 3 and x % 8 == 4:
                c = IR[0]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else IR[3]
            elif out(x, y, -1, 0) or (mask & W and x == 0):
                c = IR[5] if y < 2 else IR[3]
            px[x, y] = c
        if sh[4][x] and px[x, 4] != K and not (mask & E and x >= 14) and not (mask & W and x <= 0):
            px[x, 4] = MG[2] if h01(x, 4, 12) < 0.5 else MG[1]
            if h01(x, 4, 13) < 0.2 and sh[5][x]:
                px[x, 5] = MG[1]


def variant_features(px, sh, mask):
    """Variants: a knot of petrified heartwood root (charcoal growth rings, ember-cracked) set into a block, or an
    iron clamp plate riveted across a joint. Deep interior tiles stay quiet (only a darker, cracked block)."""
    seed = mask
    if mask == 0:
        for (x, y) in ((5, 3), (6, 4), (6, 5), (7, 6), (7, 7), (8, 8)):
            if sh[y][x]:
                px[x, y] = ST[0]
        return
    if seed % 2 == 0:
        cx, cy, rx, ry = (8.5 if not mask & W else 10.5), (10.5 if mask & N else 8.5), 4.6, 3.4
        for y in range(TS):
            for x in range(TS):
                if not sh[y][x] or px[x, y] == K or (mask & N and y < 5):
                    continue
                d = math.hypot((x + .5 - cx) / rx, (y + .5 - cy) / ry)
                if d > 1:
                    continue
                ring = int(d * 3.2)
                c = CH[(3, 2, 3, 1)[ring]] if d < 0.95 else CH[0]
                if d < 0.25:
                    c = MG[3]
                elif 0.3 < d < 0.9 and h01(x, y, 91 + seed) < 0.13:
                    c = MG[4] if h01(x, y, 92) < 0.4 else MG[2]
                if (x + .5 - cx) < -1.5 and d < 0.8 and ring == 1:
                    c = CH[4]
                px[x, y] = c
    else:
        y0 = 7 if mask & N else 4
        for y in range(y0, y0 + 6):
            for x in range(9, 14):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = IR[4] if x == 9 or y == y0 else IR[1] if x == 13 or y == y0 + 5 else IR[2]
        for (x, y) in ((10, y0 + 1), (12, y0 + 4)):
            if sh[y][x]:
                px[x, y] = IR[6]


# =========================================================================== platform, spikes
def platform(kind):
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        for y in range(5):
            if y == 0:
                c = IR[5] if h01(x, 0, 3) > 0.25 else IR[6]
            elif y == 4:
                c = K
            elif (x + (0 if y % 2 else 1)) % 3 == 0:
                c = IR[1]                                  # grate holes
                if y == 2 and h01(x, y, 17) < 0.3:
                    c = MG[4] if h01(x, 9, 2) < 0.5 else MG[3]   # slag caught in the grate
            else:
                c = IR[3] if y < 3 else IR[2]
            px[x, y] = c
    def bracket(x0, sgn):
        for i in range(6):
            x = x0 + sgn * i // 2
            y = 5 + i
            if 0 <= x < TS:
                px[x, y] = IR[3] if i < 5 else K
        for y in range(5, 8):
            px[x0, y] = IR[2]
    if kind in ("L", "single"):
        px[0, 0] = K; px[0, 1] = IR[4]
        bracket(2, 1)
    if kind in ("R", "single"):
        px[15, 0] = K; px[15, 1] = IR[2]
        bracket(13, -1)
    if kind == "M":
        for y in range(5, 7):
            px[8, y] = IR[2]
        px[8, 7] = K
    # chain links hanging from the catwalk
    if kind == "M":
        for y in range(5, 12):
            px[4, y] = IR[4] if y % 2 else IR[2]
        px[4, 12] = MG[3]
    return img


def spikes(down=False):
    img = blank(TS, TS)
    px = img.load()
    base = 15
    for i, (cx, h, w) in enumerate(((2.5, 9, 2.2), (6.5, 13, 2.6), (10.5, 10, 2.3), (13.8, 7, 1.8))):
        for y in range(base - h, base + 1):
            t = (base - y) / h
            hw = w * (1 - t) + 0.3
            for x in range(int(cx - hw - 1), int(cx + hw + 2)):
                if not (0 <= x < TS):
                    continue
                dx = x + 0.5 - cx
                if abs(dx) > hw:
                    continue
                if t > 0.72:
                    c = MG[6] if t > 0.9 else MG[5] if t > 0.8 else MG[4]
                elif dx < -0.2:
                    c = CH[4] if t > 0.4 else CH[3]
                else:
                    c = CH[1] if t < 0.5 else CH[2]
                px[x, y] = c
    # clinker at the base
    for x in range(TS):
        px[x, 15] = ST[2] if h01(x, 1, 4) < 0.6 else MG[1]
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
    D = ramp("080505", "0e0909", "140c0b", "1b110f", "231613")
    for y in range(TS):
        for x in range(TS):
            row = y // 4
            off = 0 if row % 2 else 4
            joint = (y % 4 == 3) or ((x + off) % 8 == 7)
            lv = 1 if joint else 2 + (1 if (y % 4 == 0) else 0)
            r = h01(x + k * 16, y, 51)
            if r < 0.1: lv -= 1
            if k == 1 and not joint and h01((x + off) // 8, row, 77) < 0.3:
                lv = 1                                 # soot-blackened brick
            px[x, y] = D[int(clamp(lv, 0, 4))]
    if k == 2:     # a dim furnace grille glowing through the wall
        for y in range(5, 11):
            for x in range(4, 12):
                edge = x in (4, 11) or y in (5, 10)
                if edge:
                    px[x, y] = IR[2]
                elif x % 2 == 0:
                    px[x, y] = IR[0]
                else:
                    px[x, y] = MG[0] if 7 < y < 10 else IR[1]
    if k == 3:     # pipe column (tiles vertically)
        for y in range(TS):
            for x in range(6, 10):
                c = IR[2] if x == 7 else IR[1] if x < 9 else IR[0]
                if x == 6:
                    c = D[0]
                if y in (3, 4):
                    c = IR[3] if x < 9 else IR[1]      # flange
                px[x, y] = c
            if y == 4:
                px[7, y] = IR[4]
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


def deco_hang():
    img = blank(TS, TS)
    px = img.load()
    chain_col(px, 7, 0, 11)
    # forge hook
    for (x, y, c) in ((7, 11, IR[4]), (8, 11, IR[3]), (6, 12, IR[4]), (9, 12, IR[3]), (6, 13, IR[3]), (9, 13, IR[2]),
                      (7, 14, IR[2]), (8, 14, IR[2]), (10, 12, IR[2]), (10, 11, IR[4])):
        px[x, y] = c
    return outline_k(img)


def deco_tongs():
    img = blank(TS, TS)
    px = img.load()
    chain_col(px, 7, 0, 5)
    for i in range(7):
        px[6 - i // 3, 5 + i] = IR[4]
        px[9 + i // 3, 5 + i] = IR[3]
    for x in range(4, 12):                    # a cooling ingot held in the jaws
        for y in range(11, 14):
            px[x, y] = MG[3] if (y == 11 and 5 < x < 10) else MG[2] if y == 12 else IR[2]
    return outline_k(img)


def deco_coals():
    img = blank(TS, TS)
    px = img.load()
    for y in range(9, 16):
        half = (y - 8) * 1.2 + 1
        for x in range(int(8 - half), int(8 + half) + 1):
            if 0 <= x < TS:
                r = h01(x, y, 61)
                c = CH[2] if r < 0.45 else MG[3] if r < 0.62 else MG[4] if r < 0.72 else CH[3]
                if y < 11 and r < 0.3:
                    c = MG[5]
                px[x, y] = c
    for (x, y) in ((8, 6), (6, 4), (10, 3)):
        px[x, y] = MG[5]
    px[8, 7] = MG[4]
    return outline_k(img, skip={(8, 6), (6, 4), (10, 3), (8, 7)})


def deco_slag():
    img = blank(TS, TS)
    px = img.load()
    for y in range(11, 16):
        for x in range(1, 15):
            if h01(x, y, 44) < 0.7 - (15 - y) * 0.12:
                px[x, y] = ST[3] if h01(x, y, 9) < 0.5 else CH[2]
                if h01(x, y, 10) < 0.1:
                    px[x, y] = MG[2]
    # charred skull
    sk = ["  .....  ", " ....... ", "..x...x..", ".........", " ..o.o.. ", "  ....   "]
    for j, row in enumerate(sk):
        for i, ch in enumerate(row):
            if ch == ".":
                px[4 + i, 8 + j] = ASH[3] if j < 2 else ASH[2]
            elif ch in "xo":
                px[4 + i, 8 + j] = CH[0]
    px[6, 8] = ASH[4]
    return outline_k(img)


def deco_tuft():
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        h = int(h01(x, 1, 5) * 3)
        for y in range(15 - h, 16):
            px[x, y] = ASH[2] if y > 15 - h else ASH[3]
        if h01(x, 2, 6) < 0.18:
            px[x, 15 - h - 1] = MG[4]
    return img


def breakable():
    img = solid_tile(0)
    px = img.load()
    for (x, y) in ((6, 2), (7, 3), (7, 4), (6, 5), (7, 6), (8, 7), (8, 8), (9, 9), (9, 10), (8, 11), (9, 12)):
        px[x, y] = ST[0]
        if x + 1 < 16:
            px[x + 1, y] = ST[6]
    return img


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


def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [solid_tile(m, variant=True) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(spikes())
    t.append(spikes(down=True))
    t += [bg_wall(k) for k in range(4)]
    t += [deco_hang(), deco_tongs(), deco_coals(), deco_slag(), breakable(), deco_tuft()]
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t


# =========================================================================== animated fx tiles (tiles_deep_fx)
def lava_top(f, n=8):
    """Lava surface: rolling crest (tileable in x and in time), bright skin, crust flecks drifting."""
    img = blank(TS, TS)
    px = img.load()
    ph = f / n * 2 * math.pi
    for x in range(TS):
        w = 1.4 * math.sin(ph + x * 2 * math.pi / 16) + 0.8 * math.sin(2 * ph - x * 4 * math.pi / 16)
        top = int(round(3 + w))
        for y in range(top, TS):
            d = y - top
            c = MG[7] if d == 0 else MG[6] if d == 1 else MG[5] if d < 4 else MG[4] if d < 7 else MG[3] if d < 11 else MG[2]
            # crust flecks: dark cooling skin that drifts with the flow
            if 2 <= d <= 7 and h01((x + f * 2) % 16, y, 7) < 0.1:
                c = MG[2]
            if d == 1 and h01((x - f) % 16, 1, 9) < 0.15:
                c = MG[7]
            px[x, y] = c
    return img


def lava_body(f, n=4):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            v = 0.5 + 0.25 * math.sin((x + f * 4) * 2 * math.pi / 16 + y * 0.6) + 0.25 * math.sin(y * 2 * math.pi / 16 - f * math.pi / 2)
            c = MG[3] if v > 0.85 else MG[2] if v > 0.45 else MG[1]
            if h01(x, (y + f * 4) % 16, 3) < 0.05:
                c = MG[4]
            px[x, y] = c
    return img


def belt(kind, f):
    """Conveyor segment: dark iron frame, a slatted rubbery-iron belt on top that moves 4px per 4 frames,
    a big cog showing through at the ends, a molten glow leaking between the slats."""
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            if y < 5:
                sl = (x + f) % 4 == 0
                c = IR[1] if sl else (IR[4] if y == 0 else IR[3] if y == 1 else IR[2])
                if y == 4:
                    c = K
                if sl and y == 2:
                    c = MG[2]
            else:
                c = IR[2] if (x // 4 + y // 4) % 2 else IR[1]
                if y == 5:
                    c = IR[0]
                if y in (8, 12) and x % 4 == 1:
                    c = IR[4]                         # rivets
                if y == 15:
                    c = K
            px[x, y] = c
    if kind in ("L", "R"):
        cx = 7.5 if kind == "L" else 8.5
        for y in range(5, 15):
            for x in range(TS):
                d = math.hypot(x + .5 - cx, y + .5 - 10)
                if d < 4.6:
                    a = math.atan2(y + .5 - 10, x + .5 - cx) + f * math.pi / 4 * (1 if kind == "R" else -1)
                    tooth = math.cos(a * 6) > 0.3
                    if d > 3.6 and not tooth:
                        continue
                    px[x, y] = IR[5] if d < 1.2 else IR[4] if (d > 3.3) else IR[3]
                    if d < 0.8:
                        px[x, y] = GD[3]
        edge = 0 if kind == "L" else 15
        for y in range(TS):
            px[edge, y] = K
    return img


def hatch(open_=False):
    """The forge hatch grate (32x16 when shut; 8x32 hanging open against the wall)."""
    if open_:
        img = blank(8, 32)
        px = img.load()
        for y in range(32):
            for x in range(1, 7):
                c = IR[3] if x in (1, 6) or y % 5 == 0 else IR[1]
                px[x, y] = c
        for y in (6, 20):
            px[3, y] = GD[3]; px[4, y] = GD[2]
        return outline_k(img)
    img = blank(32, 16)
    px = img.load()
    for y in range(6):
        for x in range(32):
            c = IR[4] if y == 0 else IR[2]
            if y in (1, 2, 3, 4) and x % 4 in (1, 2) and 1 < x < 30:
                c = IR[0] if y > 1 else MG[1]
            if y == 5:
                c = K
            px[x, y] = c
    for x in (14, 15, 16, 17):
        for y in range(1, 5):
            px[x, y] = GD[3] if y < 3 else GD[2]          # Ashwright's gold lock plate
    px[15, 2] = MG[5]
    return outline_k(img)
