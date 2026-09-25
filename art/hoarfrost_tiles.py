"""Tileset for the `hoarfrost` biome — THE HOARFROST AQUEDUCT (frozen Roman aqueduct + cisterns).

66 frames of 16x16. 0..47 follow the standard layout (docs/ART_SPEC.md section 6), 48..65 are extra:
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8); snow/rime crust on N edges
16-31  same masks, variant (frost cracks, ice-filled fissures with icicles, frozen seeps, a carved
       tabula-ansata inscription, riveted iron sluice plates)
32-35  one-way platform L / M / R / single: iced stone lintel with icicles hanging under it
36/37  floor spikes = jagged ice shards / ceiling spikes = hanging icicle fangs
38-41  background wall: dark cistern masonry (41 = fluted pilaster, tiles vertically)
42     hanging chain with icicles            43 icicle curtain / frozen drips (hangs from the top edge)
44     frosted candle cluster (the only warm accent)
45     frozen rubble + bones locked in ice   46 breakable wall (looks like 0)
47     top tuft overlay: snowdrift + rime crystals (sits on a surface)
48-63  ICE-FLOOR terrain, same 16 masks: identical stone mass, but the exposed N surface is a thick
       glassy sheet of blue-white ice (specular streaks, icicles on exposed corners), sides glazed
64     freezing water SURFACE (opaque; engine draws it at ~70% alpha)
65     freezing water BODY (tiles in both directions)

Seamless approach copied from archives_tiles/env2_tiles: the interior texture is a pure function of
the in-tile pixel on a 16x16 torus (ashlar courses wrap across tile edges), depth darkening depends
only on the distance to the exposed sides (evaluated at each block's centre so blocks darken as
units), and all edge treatment (snow cap / ice sheet, rim light, outline) is layered per exposed side.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline

N, E, S, W = 1, 2, 4, 8
TS = 16

# =========================================================================== palette
# cold slate / basalt: blue-black -> pale blue-grey
ST = ramp("06080d", "0a0d14", "0f131b", "141923", "1a202c", "212836", "293142", "323b4e", "3c465a",
          "485368", "566278", "67748b", "7d8ba2", "9aa9be")
SNOW = ramp("4e6072", "7b90a4", "aabdcc", "d5e2eb", "f2f8fb")          # matte rime / snow (neutral)
ICE = ramp("0e2236", "15344c", "1d4a66", "286684", "3886a6", "55a6c4", "82c6dc", "b6e4f2", "e6fbff")
RIMEJ = C("3a4b60")                                                    # hoarfrost in joints
WAT = ramp("040a0e", "071318", "0a1b21", "0e252c", "133139", "1a414b", "26596a", "3a7686")
IRON = ramp("0b0e13", "161b23", "232a34", "333c48", "47515f", "5f6a79", "808b99", "a8b2be")
GOLD = ramp("5a3c14", "8a6224", "c09440", "ecc870", "fff0b8", "ffffff")
WAX = ramp("4c4c50", "7c7d80", "aeb0b2", "d8dbdc", "f0f3f4")          # cold grey tallow
BONE = ramp("3e464f", "66707a", "939ca4", "bcc4c9", "dfe5e8")         # bone, seen through ice

# ashlar courses on the torus: (y0, y1 inclusive incl. joint row, list of vertical joint xs)
# big dressed Roman blocks: one 16x8 block per course, joints staggered half a block
COURSES = [(0, 7, [4]), (8, 15, [12])]


def wrap16(d):
    d %= 16
    return d - 16 if d >= 8 else d


def ashlar_block(x, y):
    """-> (course index, block index, lx, ly, bw, bh, joint kind or None)."""
    for ci, (y0, y1, js) in enumerate(COURSES):
        if y0 <= y <= y1:
            ly = y - y0
            js = sorted(js)
            for bi, j in enumerate(js):
                nj = js[(bi + 1) % len(js)]
                w = (nj - j) % 16 or 16
                lx = (x - j) % 16
                if lx < w:
                    jk = "h" if ly == y1 - y0 else ("v" if lx == 0 else None)
                    return ci, bi, lx, ly, w, y1 - y0 + 1, jk
    raise AssertionError


def arch_sample(x, y):
    """-> (level, element_centre, joint kind)"""
    ci, bi, lx, ly, bw, bh, jk = ashlar_block(x, y)
    j = COURSES[ci][2][bi]
    cen = ((j + bw / 2) % 16, COURSES[ci][0] + bh / 2 - 0.5)
    tone = (0, 1)[ci]
    if jk:
        return 2, cen, jk
    lv = 8 + tone
    # drafted margin (rusticated Roman ashlar): lit top + left bevel, shaded bottom + right
    if ly == 0:
        lv += 1
    elif ly == bh - 2:
        lv -= 1
    if lx == 1 and ly < bh - 2:
        lv += 1
    elif lx == bw - 1:
        lv -= 1
    # inner draft line: the raised boss of the block is framed by a faint chiselled groove
    if (lx == 3 or lx == bw - 3) and 1 < ly < bh - 3:
        lv -= 1 if lx == bw - 3 else 0
    r = h01(x, y, 17 + ci)
    if r < 0.05:
        lv -= 1
    elif r > 0.975:
        lv += 1
    return lv, cen, None


def depth_steps(d):
    return (d > 5) + (d > 9) + (d > 12)


# =========================================================================== solid tile
def solid_shape(mask):
    sh = [[True] * TS for _ in range(TS)]
    cut = []
    if mask & N and mask & W:
        cut += [(0, 0)]
    if mask & N and mask & E:
        cut += [(15, 0)]
    if mask & S and mask & W:
        cut += [(0, 15), (1, 15), (0, 14)]
    if mask & S and mask & E:
        cut += [(15, 15), (14, 15), (15, 14)]
    for x, y in cut:
        sh[y][x] = False
    for side, x in ((W, 0), (E, 15)):
        if mask & side:
            for y in (7, 15):
                if not (mask & S and y == 15) and not (mask & N and y < 6) and h01(y, side, 51) < 0.6:
                    sh[y][x] = False
    if mask & S:
        for x in range(2, TS - 2):
            if h01(x, 2, 9) < 0.12:
                sh[15][x] = False
    return sh


def make_out(mask, sh):
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
    return out


def solid_tile(mask, seed=0, top="snow"):
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask)
    out = make_out(mask, sh)

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

    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            lv, cen, jk = arch_sample(x, y)
            d = dfun(*cen) + 3.0 * h01(int(cen[0] * 3), int(cen[1] * 3), 60 + seed)
            k = depth_steps(d)
            if k == 0 and jk == "h" and h01(x, y, 33) < 0.45 and mask & (N | W):
                px[x, y] = RIMEJ                                  # hoarfrost packed in the joint
                continue
            lv -= (0, 2, 3, 4)[k]
            if k >= 2:
                lv = min(lv, 3)
            if mask & W and x < 3:
                lv += (1, 1, 0)[x]
            if mask & E and 15 - x < 2:
                lv -= 1
            if mask & S and 15 - y < 3:
                lv -= (2, 1, 1)[15 - y]
            px[x, y] = ST[int(clamp(lv, 0, len(ST) - 1))]
    # side faces: cold rim light (W), outline (E, S)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            o_w, o_e, o_s, o_n = out(x, y, -1, 0), out(x, y, 1, 0), out(x, y, 0, 1), out(x, y, 0, -1)
            if o_e or o_s:
                px[x, y] = K
            elif o_w and not (mask & N and y < 5):
                px[x, y] = ST[10] if (y % 8) not in (0, 7) else ST[11]
            elif o_n and not (mask & N):
                px[x, y] = K
    # faint teal bounce light off the cistern water on undersides
    if mask & S:
        for x in range(TS):
            for y in range(14, 8, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = WAT[5] if (x % 4) else WAT[4]
                    break
    if mask & N:
        if top == "snow":
            snow_lip(img, sh, mask, out)
        else:
            ice_lip(img, sh, mask, out)
    elif top == "ice":
        glaze_sides(img, sh, mask, 0)
    return img


def cap_depth(x):
    """rows of snow on top of a block at column x (the shadow line sits right below)."""
    return 2 + (h01(x, 0, 81) < 0.45) + (h01(x // 3, 0, 83) < 0.3)


def snow_lip(img, sh, mask, out):
    """Wind-packed snow crusting the top edge: bright matte cap, blue shadow line, rime drips."""
    px = img.load()
    for x in range(TS):
        d = cap_depth(x)
        if mask & W and x == 0 or mask & E and x == 15:
            d = min(d, 3)
        for y in range(d + 1):
            if not sh[y][x]:
                continue
            if y == d:
                c = ST[1]                                          # shadow under the crust
            elif y == 0:
                c = SNOW[4] if h01(x, 0, 84) > 0.2 else SNOW[3]
            elif y == d - 1 and d > 2:
                c = SNOW[1]
            else:
                c = SNOW[3] if y == 1 else SNOW[2]
            if mask & E and x == 15:
                c = SNOW[2] if y == 0 else K
            elif mask & W and x == 0 and y < d:
                c = SNOW[4] if y < 2 else SNOW[2]
            px[x, y] = c
        # rime icicles hanging off the crust
        L = int(h01(x, 0, 71) ** 2.2 * 5)
        if (mask & E and x >= 14) or (mask & W and x <= 1):
            L = 0
        for i in range(L):
            y = d + 1 + i
            if sh[y][x] and px[x, y] != K:
                px[x, y] = ICE[7] if i == 0 else ICE[6] if i < L - 1 else ICE[5]
    if mask & W:                                                  # snow spilling down the lit side
        for y in range(3, 6):
            if sh[y][0]:
                px[0, y] = SNOW[2] if y < 5 else SNOW[1]


def glaze_sides(img, sh, mask, y0):
    """Clear ice glazing the exposed side faces (ice-floor tiles)."""
    px = img.load()
    if mask & W:
        for y in range(y0, TS):
            n0 = 9 + int(h01(y // 4, 3, 95) * 4) if y0 else 99
            if y - y0 > n0 or (mask & S and y > 13):
                break
            if sh[y][0] and px[0, y] != K:
                px[0, y] = ICE[6] if (y % 8) not in (0, 7) else ICE[7]
            if sh[y][1] and px[1, y] != K and y - y0 < 6 and y0:
                px[1, y] = ICE[3]
    if mask & E:
        for y in range(y0, TS):
            if y - y0 > (7 if y0 else 99) or (mask & S and y > 13):
                break
            if sh[y][14] and px[14, y] != K:
                px[14, y] = ICE[2] if y % 3 else ICE[3]


def ice_lip(img, sh, mask, out):
    """Thick glassy ice sheet on the top face: bright specular top, translucent cyan body the stone
    joints ghost through, diagonal glints, dark underline, icicles on exposed corners."""
    px = img.load()
    base = img.copy().load()
    TH = 5
    for x in range(TS):
        for y in range(TH + 1):
            if not sh[y][x]:
                continue
            if y == TH:
                c = ICE[1]
            elif y == 0:
                c = ICE[8] if (x + 1) % 5 else ICE[7]
            elif y == 1:
                c = ICE[7]
            else:
                lv = (6, 5, 4)[y - 2]
                s = base[x, y]
                if s[3] and sum(s[:3]) < 90:
                    lv -= 1                                        # stone joints ghost through
                g = (x + y) % 16
                if g in (9, 10):
                    lv += 2                                        # diagonal glints ("/" streaks)
                elif g in (3,):
                    lv += 1
                c = ICE[lv]
            if y in (1, 2) and (x + y) % 16 in (9, 10):
                c = ICE[8]
            if mask & E and x == 15:
                c = ICE[5] if y == 0 else K
            elif mask & E and x == 14 and 0 < y < TH:
                c = ICE[3]
            elif mask & W and x == 0:
                c = ICE[8] if y < 3 else ICE[7]
            px[x, y] = c
        # little frozen drips under the sheet
        L = int(h01(x, 5, 97) ** 3 * 4)
        if (mask & E and x >= 13) or (mask & W and x <= 2):
            L = 0
        for i in range(L):
            y = TH + 1 + i
            if sh[y][x] and px[x, y] != K:
                px[x, y] = ICE[6] if i < L - 1 else ICE[4]
    glaze_sides(img, sh, mask, TH + 1)
    # the sheet overhangs the exposed corners: icicles hanging down the side faces
    if mask & W:
        for i, c in enumerate((ICE[7], ICE[7], ICE[6], ICE[5], ICE[4])):
            if sh[TH + 1 + i][0]:
                px[0, TH + 1 + i] = c
        for i, c in enumerate((ICE[6], ICE[5], ICE[4])):
            px[1, TH + 1 + i] = c
        px[2, TH + 1] = ICE[4]
    if mask & E:
        for i, c in enumerate((ICE[6], ICE[5], ICE[5], ICE[4])):
            px[14, TH + 1 + i] = c
        px[13, TH + 1] = ICE[5]
        px[13, TH + 2] = ICE[3]


# =========================================================================== variant features
def _ok(px, x, y, lo):
    return 0 <= x < TS and lo <= y < 15 and px[x, y][3] and px[x, y] != K


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


def f_frostcrack(img, mask, k, lo):
    """A frost-split block: dark crack whose lit lip is furred with hoarfrost."""
    px = img.load()
    pts = [[(3, 6), (5, 8), (5, 10), (7, 12), (8, 14)], [(12, 5), (11, 7), (12, 9), (10, 11), (10, 13)],
           [(2, 10), (4, 11), (7, 11), (8, 13)]][k % 3]
    for (x, y) in polyline([(x, max(lo + 1, y)) for x, y in pts]):
        if _ok(px, x, y, lo):
            px[x, y] = ST[1]
            if _ok(px, x - 1, y, lo) and px[x - 1, y] != ST[1]:
                px[x - 1, y] = SNOW[1] if h01(x, y, 5) < 0.6 else RIMEJ
            if _ok(px, x + 1, y, lo) and px[x + 1, y] != ST[1] and y % 2:
                px[x + 1, y] = ST[4]


def f_embedded(img, mask, k, lo):
    """Old ice packed into the course joint, a few small icicles grown out of it."""
    px = img.load()
    y0 = 7 if lo <= 6 else 15
    if y0 == 15:
        return
    x0 = 3 + (k * 3) % 5
    x1 = x0 + 6
    for x in range(x0, x1 + 1):
        if _ok(px, x, y0, lo) or (0 <= x < TS and px[x, y0] == RIMEJ):
            px[x, y0] = ICE[3] if (x + k) % 3 else ICE[4]
    for x in (x0 + 1, x0 + 4):
        L = 2 + int(h01(x, k, 9) * 3)
        for j in range(L):
            if _ok(px, x, y0 + 1 + j, lo):
                px[x, y0 + 1 + j] = ICE[6] if j == 0 else ICE[4] if j < L - 1 else ICE[3]


def f_seep(img, mask, k, lo):
    """Water that seeped out of a joint and froze down the face: a glassy ribbon that thickens in
    drip-rings and ends in a pointed drip."""
    px = img.load()
    x0 = 3 + (k * 5) % 9
    y0 = max(lo + 1, 7 if lo < 6 else lo + 1)
    y1 = 14 if not mask & S else 12
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        if t > 0.8:
            w = 1
        else:
            w = 2 + (1 if abs(t - 0.45) < 0.1 else 0)
        for i in range(w):
            x = x0 + i
            if _ok(px, x, y, lo):
                c = ICE[6] if i == 0 else ICE[4] if i < w - 1 or w == 1 else ICE[2]
                if y == y0:
                    c = ICE[1]
                if y == y1:
                    c = ICE[7]
                px[x, y] = c
        if _ok(px, x0 + w, y, lo) and y % 3 and t < 0.8:
            px[x0 + w, y] = ST[3]                                  # wet dark stain beside it
    if _ok(px, x0, y0 + 2, lo):
        px[x0, y0 + 2] = ICE[8]


def f_tablet(img, mask, k, lo):
    """A carved Roman tabula ansata (dovetailed inscription panel) with two lines of worn letters."""
    px = img.load()
    x0, x1 = 4, 11
    y0 = max(lo + 1, 5 if lo < 6 else lo + 2)
    y1 = y0 + 5
    if y1 > 14:
        return
    ym = (y0 + y1) / 2
    for y in range(y0 - 1, y1 + 2):
        for x in range(x0 - 3, x1 + 4):
            if not _ok(px, x, y, lo):
                continue
            ear = (x < x0 and abs(y + 0.5 - ym) < (x - (x0 - 3)) * 1.2 + 0.4) or \
                  (x > x1 and abs(y + 0.5 - ym) < ((x1 + 3) - x) * 1.2 + 0.4)
            inside = x0 <= x <= x1 and y0 <= y <= y1
            if inside:
                if y == y0 or x == x0:
                    c = ST[4]                                      # shadowed inner edge of the recess
                elif y == y1 or x == x1:
                    c = ST[9]                                      # lit inner edge
                else:
                    c = ST[6]
                    if y in (y0 + 2, y0 + 4) and x0 + 1 < x < x1 - 0 and h01(x, y + k, 41) < 0.7:
                        c = ST[4]                                  # carved letters
                px[x, y] = c
            elif ear:
                px[x, y] = ST[6] if y < ym else ST[8]
    for x in range(x0, x1 + 1):                                    # frost on the upper moulding
        if _ok(px, x, y0 - 1, lo) and h01(x, 1, 44) < 0.7:
            px[x, y0 - 1] = SNOW[1]


def f_rivets(img, mask, k, lo):
    """A riveted iron sluice plate bolted to the block: frost on its top edge, a frozen weep below."""
    px = img.load()
    x0 = 4 + k % 3
    x1 = x0 + 7
    y0 = max(lo + 2, 6)
    y1 = min(13, y0 + 4)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if not _ok(px, x, y, lo):
                continue
            c = IRON[3]
            if y == y0:
                c = SNOW[2] if 0 < (x - x0) < 7 and h01(x, y, 3) < 0.8 else IRON[5]
            elif x == x0:
                c = IRON[5]
            elif y == y1 or x == x1:
                c = IRON[1]
            elif y == y0 + 1:
                c = IRON[4]
            px[x, y] = c
    for (x, y) in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
        if _ok(px, x, y, lo):
            px[x, y] = IRON[7]
    for x in range(x0 + 1, x1 + 2):                                # drop shadow on the stone
        if _ok(px, x, y1 + 1, lo):
            px[x, y1 + 1] = ST[2]
    for y in range(y0 + 1, y1 + 2):
        if _ok(px, x1 + 1, y, lo):
            px[x1 + 1, y] = ST[2]
    xs = x0 + 3
    for y in range(y1 + 1, min(15, y1 + 4)):
        if _ok(px, xs, y, lo):
            px[xs, y] = ICE[6] if y < y1 + 3 else ICE[4]


def f_deepcrack(img, mask, k, lo):
    """Deep interior: only a dark hairline frost crack (low contrast, no bright ice)."""
    px = img.load()
    for (x, y) in polyline([(5, 9), (6, 11), (6, 13)]):
        if _ok(px, x, y, lo):
            px[x, y] = ST[1]


FEATURES = [[f_seep], [f_frostcrack], [f_tablet], [f_rivets], [f_embedded, f_frostcrack], [f_embedded, f_seep]]


def variant_tile(mask, top="snow"):
    img = solid_tile(mask, seed=5, top=top)
    k = (mask * 7 + 1) % len(FEATURES)
    lo = 6 if mask & N else 1
    if top == "ice" and mask & N:
        lo = 7
    feats = FEATURES[k]
    if mask == 0:
        feats = [f_deepcrack]
    for f in feats:
        f(img, mask, mask // 2 + k, lo)
    return img


# =========================================================================== icicle helper
def icicle(px, cx, top, length, width, bright=True, lim=16):
    """Hanging icicle with its root at (cx, top): lit left column, pale core, darker right edge."""
    for j in range(length):
        t = j / max(1, length)
        hw = width / 2 * (1 - t) ** 0.85
        y = top + j
        if y >= lim:
            break
        for x in range(int(cx - width), int(cx + width) + 1):
            dx = x + 0.5 - cx
            if abs(dx) <= max(hw, 0.5 if j < length else 0):
                if dx < -hw + 0.9:
                    c = ICE[7] if bright else ICE[6]
                elif dx > hw - 0.9 and hw > 0.9:
                    c = ICE[3]
                else:
                    c = ICE[5] if bright else ICE[4]
                if j == length - 1:
                    c = ICE[6]
                if 0 <= x < 16 and 0 <= y < lim:
                    px[x, y] = c


# =========================================================================== platforms
def platform(kind):
    """Iced stone lintel: snow on the tread, dressed slab with joints, corbels at the ends and a
    fringe of icicles hanging underneath."""
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    x0 = 1 if left else 0
    x1 = 14 if right else 15
    for x in range(x0, x1 + 1):
        d = 1 + (h01(x, 0, 113) < 0.35)
        for y in range(0, 6):
            if y < d:
                c = SNOW[4] if y == 0 else SNOW[2]
            elif y == d:
                c = ST[2]
            elif y == 5:
                c = K
            else:
                c = ST[9] if y == d + 1 else ST[7] if y < 4 else ST[5]
                if x % 8 == (3 if kind != "M" else 7):
                    c = ST[2]                                      # slab joint
                elif x % 8 == (4 if kind != "M" else 0) and y > d:
                    c = ST[10]
            px[x, y] = c
    for y in range(1, 5):
        if left:
            px[x0, y] = ST[11] if y > 2 else SNOW[3]
        if right:
            px[x1, y] = ST[3] if y > 2 else SNOW[1]
    if left:
        px[x0, 0] = SNOW[3]
    if right:
        px[x1, 0] = SNOW[2]

    def corbel(xa, sgn):                                           # stepped stone bracket
        for i, w in enumerate((5, 4, 3, 2)):
            y = 6 + i
            for j in range(w):
                x = xa + sgn * j
                c = ST[8] if j == 0 else ST[6] if j < w - 1 else ST[4]
                if sgn < 0:
                    c = ST[5] if j == 0 else ST[4] if j < w - 1 else ST[3]
                px[x, y] = c
    if left:
        corbel(x0 + 1, 1)
    if right:
        corbel(x1 - 1, -1)
    # icicles hanging from the underside
    spots = {"L": [(8, 6, 3), (11, 4, 2), (14, 7, 3)], "M": [(2, 5, 2), (5, 8, 3), (9, 4, 2), (12, 9, 3), (15, 3, 2)],
             "R": [(1, 6, 3), (4, 4, 2), (7, 8, 3)], "single": [(7, 5, 3), (9, 3, 2)]}[kind]
    for (cx, L, w) in spots:
        icicle(px, cx + 0.5, 6, L, w, bright=True)
    return outline(img)


# =========================================================================== spikes
def ice_shards():
    """36: jagged ice shards thrusting up out of a frozen rime mound (faceted: lit left facet,
    bright ridge, dark right facet)."""
    img = blank(TS, TS)
    px = img.load()
    SH = [(3.0, 2, 1.7, 1.4), (8.2, 0, 2.0, -0.4), (13.0, 3, 1.7, -1.6), (5.8, 7, 1.3, 0.9), (10.6, 6, 1.3, 0.8),
          (1.0, 9, 1.1, 0.6), (15.2, 9, 1.1, -0.8)]
    for (bx, tip, hw0, lean) in SH:
        for y in range(tip, 14):
            t = (y - tip) / (13 - tip)
            hw = 0.35 + hw0 * t
            cx = bx + lean * (1 - t)
            rx = cx - hw * 0.15                                    # facet ridge
            for x in range(TS):
                dx = x + 0.5 - cx
                if abs(dx) > hw:
                    continue
                if x + 0.5 < rx - 0.5:
                    c = ICE[6] if x + 0.5 > cx - hw + 0.8 else ICE[5]
                elif x + 0.5 <= rx + 0.5:
                    c = ICE[8] if t < 0.5 else ICE[7]
                else:
                    c = ICE[3] if dx < hw - 0.8 else ICE[2]
                if y == tip:
                    c = ICE[8]
                px[x, y] = c
    img = outline(img)
    px = img.load()
    for x in range(TS):
        top = 13 - (1 if h01(x // 2, 0, 4) < 0.5 else 0)
        for y in range(top, 16):
            if y == 15:
                c = K
            elif y == top:
                c = SNOW[3] if px[x, y] in (T, K) else px[x, y]
            else:
                c = SNOW[1] if h01(x, y, 6) < 0.7 else ICE[3]
            if px[x, y][3] == 0 or px[x, y] == K or y >= 14:
                px[x, y] = c
        if px[x, top - 1] == T:
            px[x, top - 1] = K
    return img


def icicle_fangs():
    """37: a row of icicle fangs hanging from a rime crust along the top edge."""
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        px[x, 0] = ICE[3] if x % 5 else ICE[2]
        px[x, 1] = ICE[5] if h01(x, 1, 3) < 0.6 else ICE[4]
    for (cx, L, w) in ((2.5, 11, 3.4), (6.5, 14, 4.0), (10.0, 9, 3.0), (13.5, 13, 3.6), (4.5, 6, 2.0),
                       (8.5, 5, 2.0), (15.2, 6, 2.0), (11.8, 4, 1.6)):
        icicle(px, cx, 1, L, w)
    img = outline(img)
    px = img.load()
    for x in range(TS):
        px[x, 0] = ICE[2] if x % 5 else ICE[1]
    return img


# =========================================================================== background walls
BG = ramp("05070b", "080b10", "0b0f16", "0f141c", "131923", "181f2b", "1e2634", "253040")
DICE = ramp("0e1e2b", "15293a", "1d3649", "284658")          # dim ice, for the back wall


def bg_block(x, y, off=0):
    """Low-contrast cistern masonry (offset course joints from the terrain's)."""
    y = y % 16
    if y in (7, 15):
        return BG[1]
    j = (3 + off) if y < 7 else (11 + off)
    lx = (x - j) % 16
    if lx == 0:
        return BG[1]
    ly = y % 8
    c = BG[3]
    if ly == 0:
        c = BG[4]
    elif ly == 6:
        c = BG[2]
    if lx == 1 and ly < 6:
        c = BG[4]
    if h01(x, y, 131) < 0.05:
        c = BG[2]
    return c


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            px[x, y] = bg_block(x, y)
    if k == 3:
        # fluted Roman pilaster (tiles vertically)
        for y in range(TS):
            for x in range(2, 14):
                if x == 2:
                    c = BG[1]
                elif x == 3:
                    c = BG[7]
                elif x == 13:
                    c = BG[0]
                elif x == 12:
                    c = BG[3]
                else:
                    c = (BG[6] if x < 8 else BG[5]) if (x % 2 == 0) else BG[3]
                px[x, y] = c
            for x in (1, 14):
                px[x, y] = BG[1]
        for x in range(4, 12, 2):                                  # a frosted fleck on a flute
            px[x, 5] = DICE[3]
        return img
    if k == 0:
        for (x, y) in ((5, 7), (6, 7), (7, 7), (13, 15), (14, 15)):
            px[x, y] = DICE[1]                                     # hoarfrost in the joints
    if k == 1:
        # round culvert outlet with a frozen beard of ice under it
        cx, cy = 8, 4
        for y in range(0, 9):
            for x in range(3, 14):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d < 2.4:
                    px[x, y] = BG[0]
                elif d < 3.5:
                    px[x, y] = BG[5] if (y < cy and x < cx + 1) else BG[2]
        for x in range(7, 10):
            L = [5, 8, 4][x - 7]
            for y in range(cy + 2, cy + 2 + L):
                if y < 16:
                    px[x, y] = DICE[2] if x == 7 else DICE[1]
    if k == 2:
        # a long frozen trickle down the wall + a dark wet stain
        for y in range(TS):
            x = 10 + (1 if 6 < y < 11 else 0)
            px[x, y] = DICE[2] if y % 5 else DICE[3]
            px[x + 1, y] = DICE[1]
            if y % 2:
                px[x + 2, y] = BG[2]
    return img


# =========================================================================== overlays
def chain_links(px, x0=7):
    for y0 in (0, 8):
        for (x, y, c) in ((0, 0, 4), (1, 0, 4), (-1, 1, 4), (2, 1, 3), (-1, 2, 3), (2, 2, 2), (0, 3, 3), (1, 3, 2)):
            px[x0 + x, y0 + y] = IRON[c]
        for y in range(4, 8):
            px[x0, y0 + y] = IRON[5] if y < 6 else IRON[4]
            px[x0 + 1, y0 + y] = IRON[2]


def deco_chain():
    """42: hanging chain (tiles vertically), rimed, with icicles hanging off its links."""
    img = blank(TS, TS)
    px = img.load()
    chain_links(px)
    for (x, y) in ((6, 1), (7, 0), (7, 8), (6, 9)):
        px[x, y] = SNOW[2]                                         # rime on the link tops
    for (x, y, L) in ((9, 3, 4), (5, 11, 3), (9, 12, 2)):
        for j in range(L):
            px[x, y + j] = ICE[7] if j == 0 else ICE[5] if j < L - 1 else ICE[4]
    return outline(img)


def deco_curtain():
    """43: icicle curtain / frozen drips hanging from the top edge (place under a ceiling)."""
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):
        px[x, 0] = ICE[4] if x % 3 else ICE[5]
        if h01(x, 2, 7) < 0.7:
            px[x, 1] = ICE[3]
    for (cx, L, w, b) in ((1.5, 7, 2.0, 1), (3.5, 13, 2.6, 1), (6.0, 5, 1.6, 0), (7.5, 10, 2.4, 1), (10.0, 15, 3.0, 1),
                          (12.2, 6, 1.8, 0), (14.3, 11, 2.4, 1)):
        icicle(px, cx, 1, L, w, bright=bool(b))
    img = outline(img)
    px = img.load()
    for x in range(TS):
        px[x, 0] = ICE[3] if x % 3 else ICE[4]
    for (x, y) in ((5, 9), (12, 12), (8, 14)):                     # falling drops (no outline)
        if px[x, y][3] == 0:
            px[x, y] = ICE[6]
    return img


def deco_candles():
    """44: frost-rimed tallow candles on a crust of snow, small gold flames (only warm accent)."""
    img = blank(TS, TS)
    px = img.load()
    for (cx, top) in ((4, 8), (7, 5), (10, 9), (12, 11)):
        for y in range(top + 1, 15):
            px[cx, y] = WAX[2] if y > top + 1 else WAX[3]
            px[cx + 1, y] = WAX[1]
        px[cx + 1, top + 2] = WAX[3]
        px[cx, top + 3] = SNOW[3]                                  # frost on the wax
        px[cx, top - 1] = GOLD[3]
        px[cx, top] = GOLD[4]
        px[cx + 1, top] = GOLD[2]
        px[cx, top + 1] = C("201a18")
    for x in range(2, 15):
        px[x, 15] = SNOW[1] if x % 3 else SNOW[0]
        if 3 <= x <= 13 and px[x, 14][3] == 0:
            px[x, 14] = SNOW[3] if x % 4 else SNOW[2]
    img = outline(img)
    px = img.load()
    for (cx, top) in ((4, 8), (7, 5), (10, 9), (12, 11)):
        px[cx, top - 2] = GOLD[2] if cx != 7 else GOLD[3]         # flame tips (no outline)
    px[7, 2] = GOLD[1]
    return img


def deco_rubble():
    """45: a lump of old ice with a skull and bones locked inside, frost-rimed rubble beside it."""
    img = blank(TS, TS)
    px = img.load()
    # ice lump
    for y in range(5, 16):
        for x in range(1, 12):
            e = ((x + 0.5 - 6.5) / 5.6) ** 2 + ((y + 0.5 - 15.5) / 10.2) ** 2
            if e < 1:
                c = ICE[2]
                if e > 0.72 and (x < 6 or y < 9):
                    c = ICE[4]
                if x + y < 16 and e > 0.55:
                    c = ICE[5]
                px[x, y] = c
    # skull + femur inside (cold-tinted bone)
    SK = ["..333..", ".34443.", "3400403", "3444443", ".34143.", "..2.2.."]
    for j, row in enumerate(SK):
        for i, ch in enumerate(row):
            if ch != ".":
                px[3 + i, 8 + j] = BONE[int(ch)] if ch != "0" else ICE[0]
    for i in range(7):
        px[2 + i, 14 - (i // 4)] = BONE[3] if i not in (0, 6) else BONE[4]
    px[1, 13], px[9, 12] = BONE[2], BONE[2]
    # streaks of glint
    px[3, 8], px[4, 7], px[2, 11] = ICE[8], ICE[7], ICE[7]
    # rubble blocks beside it
    for (x0, y0, w, h) in ((11, 11, 4, 5), (13, 9, 3, 2)):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                c = ST[8] if y == y0 else ST[6] if x == x0 else ST[5]
                if x == x0 + w - 1:
                    c = ST[4]
                px[x, y] = c
        for x in range(x0, x0 + w - 1):
            px[x, y0] = SNOW[3]
    return outline(img)


def deco_tuft():
    """47: a wind-packed snowdrift with two rime spikes (sits on the surface below: bottom row = surface)."""
    img = blank(TS, TS)
    px = img.load()
    hs = []
    for x in range(TS):
        h = 4.2 * math.exp(-((x - 5.0) / 3.6) ** 2) + 2.4 * math.exp(-((x - 12.0) / 2.2) ** 2)
        hs.append(int(round(h)))
    for x in range(TS):
        h = hs[x]
        sl = hs[min(15, x + 1)] - hs[max(0, x - 1)]              # >0 rising: faces the light
        for j in range(h):
            y = 15 - j
            if j == h - 1:
                c = SNOW[4] if sl >= 0 else SNOW[3]
            elif j == h - 2:
                c = SNOW[3] if sl >= 0 else SNOW[2]
            else:
                c = SNOW[2] if sl >= 0 else SNOW[1]
            px[x, y] = c
    for (x, L) in ((4, 2), (12, 2)):
        for j in range(L):
            px[x, 15 - hs[x] - j] = ICE[7] if j == L - 1 else ICE[5]
    img = outline(img)
    px = img.load()
    for x in range(TS):
        if px[x, 15] == K:
            px[x, 15] = T
    return img


def breakable():
    img = solid_tile(0)
    px = img.load()
    for pts in ([(6, 2), (7, 5), (6, 8), (8, 10), (9, 13)], [(7, 5), (10, 6)]):
        for (x, y) in polyline(pts):
            px[x, y] = ST[0]
            if (x + 1, y) not in pts and x + 1 < 16 and y % 2 == 0:
                px[x + 1, y] = ST[5]
    px[7, 9] = RIMEJ
    return img


# =========================================================================== water
def water_body():
    """Dark cistern water with two faint wavy lines of cold light (period 16 both ways -> tiles)."""
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            px[x, y] = WAT[2] if y % 16 < 12 else WAT[2]
    for b in range(2):
        for x in range(TS):
            ph = 2 * math.pi * (x + 6 * b) / 16
            y = (5 + 8 * b + round(1.2 * math.sin(ph))) % 16
            if (x + 6 * b) % 16 < 10:
                px[x, y] = WAT[4] if abs(math.sin(ph) + 1) < 0.25 else WAT[3]
    return img


def water_surface():
    img = water_body()
    px = img.load()
    for x in range(TS):
        px[x, 0] = ICE[7]
        px[x, 1] = ICE[4] if (x // 3) % 3 else ICE[5]
        px[x, 2] = WAT[6]
        px[x, 3] = WAT[5] if x % 4 else WAT[4]
        px[x, 4] = WAT[3]
    # thin floating ice plates (lit top, shaded edge, dark gap in the water under them)
    for (x0, w) in ((2, 5), (11, 3)):
        for i in range(w):
            x = x0 + i
            px[x, 0] = ICE[8]
            px[x, 1] = SNOW[4] if i < w - 1 else ICE[6]
            px[x, 2] = ICE[3]
            px[x, 3] = WAT[1]
        px[x0 - 1, 1] = WAT[1]
        px[x0 + w, 1] = WAT[1]
    return img


# =========================================================================== tileset
def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [variant_tile(m) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(ice_shards())
    t.append(icicle_fangs())
    t += [bg_wall(k) for k in range(4)]
    t.append(deco_chain())
    t.append(deco_curtain())
    t.append(deco_candles())
    t.append(deco_rubble())
    t.append(breakable())
    t.append(deco_tuft())
    t += [solid_tile(m, top="ice") for m in range(16)]
    t.append(water_surface())
    t.append(water_body())
    assert len(t) == 66 and all(i.size == (16, 16) for i in t)
    return t
