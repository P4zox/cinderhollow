"""Tileset for the `barrows` biome -- THE DROWNED BARROWS (tombs beneath the Sunken Cathedral, flooded by a black tide).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8): slick blue-green tomb masonry, a slate
       coping slab with a wet top-lit lip on every N edge, water beading off the underside of overhangs
16-31  same masks, variant: barnacle clusters with a speck of glowing algae / a verdigris bronze burial plaque
       weeping a green stain down the stone
32-35  one-way platform L / M / R / single: a slab of burial stone with a verdigris iron rim, black weed hanging
36/37  floor / ceiling spikes: barnacle-crusted iron spikes with pale bone-shard tips
38-41  background wall: drowned crypt masonry (38/39 plain, 40 burial niche with a faint skull, 41 niche with bones)
42     hanging verdigris chain (tiles vertically)   43 hanging black kelp / weed
44     teal-flame candles set in skulls              45 glowing bone pile
46     breakable wall (looks like 0, subtle crack)   47 top tuft: barnacles and black weed
Seam approach (as deep/archives): interior texture is a pure function of the in-tile pixel on a 16x16 torus.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, h01, clamp, blank

N, E, S, W = 1, 2, 4, 8
TS = 16

# wet stone: near-black blue-green .. top-lit lip
ST = ramp("05090b", "070d10", "0a1215", "0e181b", "132024", "18282c", "1e2f33", "26393c", "2f4345", "3a5052",
          "4b6464", "63807c")
VD = ramp("0c1a18", "15292a", "1f3d39", "2f5f55", "447c6d", "5f9a86", "86bca6")     # verdigris bronze / iron
BZ = ramp("16120d", "261d14", "3a2c1c", "54402a")                                 # bare dark bronze
BONE = ramp("26261f", "3f3d33", "5c594b", "848070", "a8a290", "bdb8a2", "dcd8c4")
GL = ramp("0d3431", "145a54", "1f8f85", "2fbfb0", "8ff0e0", "e2fff9")              # bioluminescence
IR = ramp("07090c", "0e1216", "161c21", "20282d", "2c363a", "3b4648")              # black iron
KELP = ramp("050b09", "08130f", "0d1c16", "13271e", "1b3428", "264634")
BG = ramp("020506", "04090b", "060c0e", "081113", "0b1518", "0f1a1d", "142024")    # background masonry
BGB = ramp("121614", "1b201c", "262c26")                                           # very dim bone (bg)

# masonry courses on the torus: (y0, y1, joints x) -- large calm blocks
COURSES = [(0, 5, [3, 12]), (6, 10, [8]), (11, 15, [1, 11])]


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
    if mask & S: ds.append(15 - y + 4)          # undersides stay shadowed (light from above)
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
            d = depth_of(mask, *cen) + 2.0 * h01(int(cen[0] * 3), int(cen[1] * 5), 7)
            if joint:
                px[x, y] = ST[1] if d > 5 else ST[2]
                continue
            tone = (0, 1, 0, -1, 1, 0)[(ci * 3 + bi * 2) % 6]
            lv = 5 + tone
            if ly == 0:
                lv += 1                                  # wet top bevel of each block
            elif ly == bh - 2:
                lv -= 1
            if lx == 1 and ly > 0:
                lv += 0.6
            elif lx == bw - 1:
                lv -= 1
            r = h01(x, y, 19 + ci)
            if r < 0.07:
                lv -= 1
            # a slick diagonal sheen across one block in three
            if h01(ci, bi, 5) < 0.4 and (lx - ly) in (2, 3) and ly > 0:
                lv += 1
            k = (d > 4) + (d > 7) + (d > 10)
            lv -= (0, 1, 2, 2.5)[k]
            if k >= 2:
                lv = min(lv, 4)
            if mask & W and x < 2:
                lv += 1
            if mask & E and x > 13:
                lv -= 1
            px[x, y] = ST[int(clamp(round(lv), 1, 8))]
    if variant:
        variant_features(px, sh, mask)
    # faces: K outline on E / S, lit rim on W (light from upper-left)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            if out(x, y, 1, 0) or out(x, y, 0, 1):
                px[x, y] = K
            elif out(x, y, 2, 0) and not (mask & N and y < 4) and not out(x, y, 0, 1):
                px[x, y] = ST[6] if (y % 5) else ST[5]     # wet sheen just inside the shadowed E face
            elif out(x, y, -1, 0) and not (mask & N and y < 4):
                px[x, y] = ST[7] if (y % 6) else ST[8]
            elif out(x, y, 0, -1) and not (mask & N):
                px[x, y] = K
    if mask & S:
        # underside: dark wet band with water beading, a few drops hanging
        for x in range(TS):
            for y in range(14, 10, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = ST[2]
                    if h01(x, 3, 71) < 0.1:
                        px[x, y] = GL[0]                 # faint wet glint catching the teal light
                    break
    if mask & N:
        coping(px, sh, mask, out)
    return img


def coping(px, sh, mask, out):
    """Slate coping slab along the top: wet top-lit lip, a lit bevel, a shadowed underside, water drips beneath."""
    for x in range(TS):
        for y in range(4):
            if not sh[y][x]:
                continue
            c = (ST[11], ST[9], ST[7], ST[2])[y]
            if y == 0 and h01(x, 0, 81) < 0.22:
                c = ST[10]
            if y == 1 and h01(x, 1, 82) < 0.12:
                c = ST[10]
            if y == 2 and h01(x, 2, 83) < 0.15:
                c = ST[6]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else ST[8]
            elif out(x, y, -1, 0) or (mask & W and x == 0):
                c = ST[10] if y < 2 else ST[8] if y == 2 else ST[3]
            px[x, y] = c
        # a slab joint every 16 px (at x=10) so long floors read as laid stone
        if x == 10 and not (mask & E and x >= 14):
            for y in (1, 2):
                if sh[y][x]:
                    px[x, y] = ST[4]
        # drips of water running off the lip
        if sh[4][x] and px[x, 4] != K and h01(x, 4, 12) < 0.18 and not (mask & W and x == 0) and not (mask & E and x == 15):
            px[x, 4] = ST[8]
            if sh[5][x] and h01(x, 5, 13) < 0.5:
                px[x, 5] = ST[7]
    # a rare algae speck on the lip (bioluminescent), kept very sparse
    for x in range(1, 15):
        if sh[0][x] and h01(x, 0, 90 + mask) < 0.018:
            px[x, 0] = GL[3] if h01(x, 1, 91) < 0.5 else GL[2]


def barnacle(px, sh, cx, cy, big=False):
    pts = [(0, 0, 3), (1, 0, 2), (0, 1, 1), (1, 1, 0)]
    if big:
        pts = [(0, -1, 4), (1, -1, 3), (-1, 0, 4), (0, 0, 2), (1, 0, 1), (2, 0, 2), (-1, 1, 3), (0, 1, 0), (1, 1, 0),
               (2, 1, 1)]
    for dx, dy, v in pts:
        x, y = cx + dx, cy + dy
        if 0 <= x < TS and 0 <= y < TS and sh[y][x]:
            px[x, y] = BONE[v] if v else ST[1]


def variant_features(px, sh, mask):
    """Variants: barnacle clusters + a speck of glowing algae, or a verdigris burial plaque weeping a green stain.
    Deep interior (mask 0) stays quiet: a single dark crack."""
    if mask == 0:
        for (x, y) in ((4, 7), (5, 8), (5, 9), (6, 10), (7, 10), (8, 11)):
            if sh[y][x]:
                px[x, y] = ST[1]
        return
    y_top = 6 if mask & N else 3
    if mask % 2 == 0:
        # barnacles clustering toward an exposed face
        bx = 3 if mask & W else 11 if mask & E else 6
        by = 12 if mask & S else y_top + 3
        barnacle(px, sh, bx, by, big=True)
        barnacle(px, sh, bx + 4, by + 1)
        barnacle(px, sh, bx - 2, by + 3)
        for (x, y) in ((bx + 3, by - 1), (bx - 1, by + 2)):
            if 0 <= x < TS and 0 <= y < TS and sh[y][x]:
                px[x, y] = GL[3]
        if 0 <= bx + 3 < TS and sh[by][bx + 3]:
            px[bx + 3, by] = GL[1]
    else:
        # a verdigris bronze burial plaque set into the stone, weeping a green stain down the joints below it
        x0, y0 = 5, y_top + 2
        pw, ph = 6, 4
        for y in range(y0, y0 + ph):
            for x in range(x0, x0 + pw):
                if not sh[y][x]:
                    continue
                if y == y0:
                    c = VD[4] if x < x0 + pw - 1 else VD[2]
                elif x == x0:
                    c = VD[3]
                elif y == y0 + ph - 1 or x == x0 + pw - 1:
                    c = VD[0]
                else:
                    c = VD[2] if (x * 3 + y) % 7 else BZ[2]
                px[x, y] = c
        for x in range(x0 + 1, x0 + pw - 1):          # a worn line of inscription
            if (x - x0) % 2:
                px[x, y0 + 2] = VD[1]
        for (x, y0s, ln) in ((x0 + 1, y0 + ph, 3), (x0 + 3, y0 + ph, 5)):
            for y in range(y0s, min(TS, y0s + ln)):
                if sh[y][x]:
                    px[x, y] = VD[1] if (y - y0s) < ln - 1 else VD[0]


# =========================================================================== platform, spikes
def platform(kind):
    """Burial stone slab with a verdigris iron rim along its top, iron corbels at the ends, weed hanging below."""
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        for y in range(5):
            if y == 0:
                c = VD[5] if h01(x, 0, 3) > 0.2 else VD[6]
            elif y == 1:
                c = VD[3] if x % 8 != 3 else VD[5]         # rim band with rivets
            elif y == 2:
                c = ST[8] if h01(x, 2, 4) > 0.15 else ST[9]
            elif y == 3:
                c = ST[6] if x % 16 != 12 else ST[3]
            else:
                c = K
            px[x, y] = c
    def corbel(x0, sgn):
        # a small iron bracket: vertical strap under the slab, diagonal strut back to it
        for y in range(5, 9):
            px[x0, y] = IR[4] if sgn > 0 else IR[3]
        for i in range(1, 4):
            px[x0 + sgn * i, 5 + (3 - i)] = IR[3] if sgn > 0 else IR[2]
        px[x0, 9] = IR[2]
    if kind in ("L", "single"):
        px[0, 0] = K
        px[0, 1] = VD[4]; px[0, 2] = ST[9]; px[0, 3] = ST[7]
        corbel(2, 1)
    if kind in ("R", "single"):
        px[15, 0] = K
        px[15, 1] = VD[1]; px[15, 2] = ST[5]; px[15, 3] = ST[3]
        corbel(13, -1)
    if kind == "M":
        # a couple of black weed strands trailing from the slab
        for (x, ln) in ((5, 5), (6, 3), (11, 4)):
            for y in range(5, 5 + ln):
                px[x, y] = KELP[4] if y < 5 + ln - 1 else KELP[2]
        px[6, 7] = GL[2]
    if kind == "single":
        px[8, 5] = KELP[4]; px[8, 6] = KELP[3]; px[8, 7] = KELP[2]
    return outline_k(img)


def spikes(down=False):
    img = blank(TS, TS)
    px = img.load()
    base = 15
    for i, (cx, h, w) in enumerate(((2.5, 8, 2.0), (6.5, 13, 2.4), (10.5, 10, 2.2), (13.8, 6, 1.6))):
        for y in range(base - h, base + 1):
            t = (base - y) / h
            hw = w * (1 - t) + 0.35
            for x in range(int(cx - hw - 1), int(cx + hw + 2)):
                if not (0 <= x < TS):
                    continue
                dx = x + 0.5 - cx
                if abs(dx) > hw:
                    continue
                if t > 0.8:
                    c = BONE[4] if t > 0.9 else BONE[3]                          # pale bone-shard tips
                elif dx < -0.2:
                    c = IR[5] if t > 0.35 else IR[4]
                else:
                    c = IR[2] if t < 0.5 else IR[3]
                # verdigris crust creeping up the lower shaft
                if t < 0.35 and h01(x, y, 17 + i) < 0.45:
                    c = VD[3] if dx < 0 else VD[2]
                px[x, y] = c
    # a low crust of barnacles along the base
    for x in range(TS):
        px[x, 15] = ST[4] if h01(x, 1, 4) < 0.7 else VD[2]
    for x0 in (0, 4, 8, 12):
        px[x0, 14] = BONE[3]; px[x0 + 1, 14] = BONE[2]
        px[x0 + 1, 15] = ST[1]
    out = outline_k(img)
    if down:
        out = out.transpose(Image.FLIP_TOP_BOTTOM)
    return out


# =========================================================================== background wall
def bg_mason(px, k):
    for y in range(TS):
        for x in range(TS):
            row = y // 8
            off = 0 if row % 2 else 8
            joint = (y % 8 == 7) or ((x + off) % 16 == 0) or (y % 8 == 3 and (x + off) % 16 == 8 and False)
            lv = 1 if joint else 2 + (1 if (y % 8 == 0) else 0)
            if not joint and (x + off) % 16 == 1 and y % 8 < 6:
                lv += 1
            r = h01(x + k * 16, y, 51)
            if r < 0.08:
                lv -= 1
            if k == 1 and not joint and (x + y) % 7 == 0 and h01(x, y, 3) < 0.4:
                lv -= 1                               # wet streaking on the second plain tile
            px[x, y] = BG[int(clamp(lv, 0, 6))]
    if k == 1:
        px[5, 10] = GL[0]


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    bg_mason(px, k)
    if k == 3:
        # plain masonry with a faint verdigris stain weeping down from a joint
        for (x, y0, ln) in ((6, 8, 6), (7, 8, 3)):
            for y in range(y0, y0 + ln):
                px[x, y] = VD[0] if y < y0 + ln - 1 else BG[2]
    if k == 2:
        # a burial niche: pointed-arched recess, sill lip below
        x0, x1, top, bot = 3, 12, 3, 13
        for y in range(top, bot + 1):
            for x in range(x0, x1 + 1):
                cx = (x0 + x1) / 2 + 0.5
                hw = (x1 - x0 + 1) / 2
                if y < top + 4:
                    # pointed arch head
                    t = (top + 4 - y) / 4
                    if abs(x + 0.5 - cx) > hw * (1 - t * t) + 0.2:
                        continue
                edge_l = x == x0 or (y < top + 4 and abs(x + 0.5 - cx) > hw * (1 - ((top + 4 - y) / 4) ** 2) - 1.2 and x < cx)
                px[x, y] = BG[2] if edge_l else BG[0]
        for x in range(x0 - 1, x1 + 2):
            px[x, bot + 1] = BG[4]
            px[x, bot + 2] = BG[1]
        # a faint skull resting on a long bone in the niche
        sk = ["..###..", ".#####.", "#o#.#o#", ".#####.", "..#.#.."]
        for j, row in enumerate(sk):
            for i, ch in enumerate(row):
                X, Y = 4 + i, 7 + j
                if ch == "#":
                    px[X, Y] = BGB[1] if (j < 2 and i < 4) else BGB[0]
                elif ch == "o":
                    px[X, Y] = BG[0]
        for x in range(4, 12):
            px[x, 12] = BGB[0]
        px[4, 11] = BGB[0]; px[11, 13] = BGB[0]
    return img


# =========================================================================== decorations
def chain_col(px, x0, y0, y1):
    """Verdigris chain, period 8 (tiles vertically): face-on ring then edge-on link."""
    for yb in range(y0, y1, 8):
        for (x, y, c) in ((0, 0, 4), (1, 0, 3), (-1, 1, 4), (2, 1, 2), (-1, 2, 3), (2, 2, 1), (0, 3, 2), (1, 3, 1)):
            if yb + y < y1:
                px[x0 + x, yb + y] = VD[c]
        for y in range(4, 8):
            if yb + y < y1:
                px[x0, yb + y] = VD[4] if y < 6 else VD[3]
                px[x0 + 1, yb + y] = VD[1]


def deco_chain():
    img = blank(TS, TS)
    px = img.load()
    chain_col(px, 7, 0, 16)
    return outline_k(img, vertical_open=True)


def deco_kelp():
    """Three strands of black weed hanging from above, tapering, swaying; one carries a glowing bulb."""
    img = blank(TS, TS)
    px = img.load()
    strands = [(4, 15, 0.9, 0.0), (8, 11, -0.8, 1.9), (11, 14, 0.7, 3.1)]
    for (x0, L, sway, ph) in strands:
        for y in range(L):
            t = y / max(1, L - 1)
            x = x0 + round(math.sin(y * 0.42 + ph) * sway * (0.3 + t))
            wide = t < 0.55
            c = KELP[5] if y % 5 == 1 else KELP[4]
            if t > 0.8:
                c = KELP[3]
            px[x, y] = c
            if wide and 0 <= x + 1 < TS:
                px[x + 1, y] = KELP[2]
        # frond leaf midway
        ly = int(L * 0.5)
        lx = x0 + round(math.sin(ly * 0.42 + ph) * sway * (0.3 + ly / max(1, L - 1)))
        if 0 <= lx - 1 < TS:
            px[lx - 1, ly] = KELP[4]
            px[lx - 1, ly + 1] = KELP[3]
    tip_x = 8 + round(math.sin(10 * 0.42 + 1.9) * -0.8 * 1.3)
    px[tip_x, 11] = GL[3]
    px[tip_x, 12] = GL[1]
    return outline_k(img, skip_top=True)


def skull(px, x0, y0, lit=False):
    """5x5 skull, lit from upper-left; teal light from above if lit."""
    sk = [".###.", "#####", "#o#o#", ".###.", ".#.#."]
    for j, row in enumerate(sk):
        for i, ch in enumerate(row):
            X, Y = x0 + i, y0 + j
            if ch == "#":
                v = 5 if (j == 0 or i == 0) else 4 if j < 3 else 3
                if i == 4:
                    v -= 1
                px[X, Y] = BONE[v]
            elif ch == "o":
                px[X, Y] = GL[1] if lit else ST[1]


def teal_flame(px, cx, top, h):
    for y in range(top, top + h):
        t = (y - top) / max(1, h - 1)
        if t < 0.34:
            px[cx, y] = GL[5] if t < 0.2 else GL[4]
        elif t < 0.7:
            px[cx, y] = GL[4]
            if h > 3:
                px[cx - 1, y] = GL[3]
        else:
            px[cx, y] = GL[3]


def deco_candles():
    img = blank(TS, TS)
    px = img.load()
    # two skulls on the ground, candles melted onto their crowns, a lone stub between them
    skull(px, 1, 11, lit=True)
    skull(px, 9, 11, lit=True)
    candles = [(3, 7, 4), (11, 5, 6), (7, 11, 4), (13, 8, 3)]      # (x, top of wax, height)
    for (x, top, h) in candles:
        for y in range(top, top + h):
            px[x, y] = BONE[5] if y == top else BONE[4] if x != 13 else BONE[3]
        if x == 7:
            for y in range(top, 16):
                px[x, y] = BONE[4] if y == top else BONE[3]
            px[6, 15] = BONE[3]; px[8, 15] = BONE[2]
    # wax dribbles down the skulls
    px[4, 11] = BONE[5]; px[12, 11] = BONE[5]; px[12, 12] = BONE[4]
    out = outline_k(img)
    op = out.load()
    # flames after the outline (unoutlined glow)
    for (x, top, h) in candles:
        fh = 3 if h >= 4 else 2
        teal_flame(op, x, top - fh, fh)
    return out


def bone_shape(px, x0, y0, x1, y1, v=4):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / n
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        if 0 <= x < TS and 0 <= y < TS:
            px[x, y] = BONE[v if i < n * 0.6 else v - 1]
    for (x, y) in ((x0, y0), (x1, y1)):
        for dx, dy in ((0, -1), (0, 1)):
            if 0 <= x + dx < TS and 0 <= y + dy < TS:
                px[x + dx, y + dy] = BONE[v]


def deco_bones():
    img = blank(TS, TS)
    px = img.load()
    for y in range(13, 16):
        for x in range(1, 15):
            if abs(x - 7.5) < 7 - (15 - y) * 1.5:
                px[x, y] = BONE[2] if h01(x, y, 44) < 0.6 else BONE[1]
    bone_shape(px, 2, 12, 9, 14, 4)
    bone_shape(px, 8, 11, 14, 13, 3)
    bone_shape(px, 4, 14, 12, 15, 3)
    skull(px, 5, 8, lit=True)
    out = outline_k(img)
    op = out.load()
    # glowing marrow at the broken bone ends
    for (x, y, c) in ((9, 13, GL[4]), (10, 14, GL[3]), (13, 12, GL[3]), (2, 14, GL[2])):
        op[x, y] = c
    return out


def deco_tuft():
    img = blank(TS, TS)
    px = img.load()
    # barnacle bumps along the surface
    for (x, h) in ((1, 2), (4, 1), (9, 2), (13, 1)):
        for dx in range(3):
            X = x + dx
            if X < TS:
                top = 15 - h + (1 if dx != 1 else 0)
                for y in range(top, 16):
                    px[X, y] = BONE[4] if (y == top and dx == 0) else BONE[3] if y == top else BONE[2]
        px[x + 1, 15 - h] = ST[1]                          # the barnacle's dark mouth
    # black weed blades
    for (x, h, lean) in ((3, 5, 1), (7, 7, -1), (8, 4, 1), (12, 6, 1), (15, 3, -1)):
        for i in range(h):
            X = x + (lean if i > h * 0.6 else 0)
            if 0 <= X < TS:
                px[X, 15 - i] = KELP[5] if i > h - 2 else KELP[4] if i > 1 else KELP[3]
    px[7, 8] = GL[3]
    return img


def breakable():
    img = solid_tile(0)
    px = img.load()
    for (x, y) in ((6, 2), (7, 3), (7, 4), (6, 5), (7, 6), (8, 7), (8, 8), (9, 9), (9, 10), (8, 11), (9, 12)):
        px[x, y] = ST[0]
        if x + 1 < 16:
            px[x + 1, y] = ST[6]
    return img


def outline_k(img, skip=(), vertical_open=False, skip_top=False):
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
                if vertical_open and dy:
                    continue
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
    t += [deco_chain(), deco_kelp(), deco_candles(), deco_bones(), breakable(), deco_tuft()]
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t
