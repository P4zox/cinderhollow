"""Tileset for the `spire` biome — THE TEMPEST SPIRE (storm-lashed sea-wall ruins under a lightning spire).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8): storm-battered basalt sea-wall
       ashlar, rain-wet top lip with a cold specular sheen and salt crust, sea-light bounce on undersides
16-31  same masks, variant (cracks, barnacles + mussels, rusted iron cramps, lichen, drain holes)
32-35  one-way platform L / M / R / single: wet timber plank walkway on rusted iron brackets
36/37  floor spikes: broken spear-headed iron railings  /  ceiling spikes: dripping basalt fangs
38-41  background wall: dark interior masonry (39 arrow slit, 40 mooring ring, 41 pilaster tiles vertically)
42     hanging rusted chain + hook               43 torn storm banner (tattered, Spire sigil)
44     storm lantern + candle stubs              45 bones + gull feathers
46     breakable wall (looks like 0)             47 top tuft: wet grass + sea-thrift

Seamless approach (as archives_tiles / env2_tiles): interior texture is a pure function of the in-tile pixel
on a 16x16 torus (ashlar courses wrap across tile edges); depth darkening depends only on the distance to the
exposed sides, evaluated at each block's centre so blocks darken as units; edge treatment is layered per side.
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline

N, E, S, W = 1, 2, 4, 8
TS = 16


def wrap16(d):
    d %= 16
    return d - 16 if d >= 8 else d


# =========================================================================== palette
# storm basalt: blue-black -> slate
ST = ramp("06070b", "0a0c12", "0f121a", "151923", "1b202c", "222836", "2a3141", "343c4e", "40495c",
          "505a6e", "667186", "8490a4")
SHEEN = [C("9aaebf"), C("5f6f84"), C("3a4557"), C("141821")]      # wet lip rows 0..3
GLINT = C("d6e6f0")
SALT = ramp("6c7682", "8e98a2", "b4bec4")
SEA = ramp("030509", "060a11", "0a1019", "0e1724", "132033", "1a2b43", "243a57", "32506f", "4a6d8c",
           "7494b0", "a8c4d8", "dceef6")
BOLT = ramp("2a4a8a", "5aa8ff", "a4d6ff", "eef9ff")
AMBER = ramp("3a200c", "6a3a14", "a8621e", "e09a3a", "ffd27a", "fff4d0")
RUST = ramp("1e100c", "3a1c12", "5a2c1a", "7c4226", "9e5c34")
VERD = ramp("1a302e", "2a4c46", "3e6a5e", "5e8c7a")
IRON = ramp("0c0d12", "181a22", "262a34", "363b47", "4a505e", "646b7a", "8a92a0")
WOOD = ramp("100d0c", "1c1816", "28221e", "352d27", "433930", "53473c", "655749", "7a6c5c")
WHEAT = ramp("2e2618", "4a3e26", "6a5a34", "8a7644", "a89258", "c4b078")
GRASS = ramp("121c1a", "1c2a26", "283a32", "36503f", "4a6a50", "64845e")
THRIFT = ramp("40202e", "6a3448", "965068", "c07a90", "e0a8b8")
LICHEN = ramp("2a2a1e", "423e28", "5c5634", "766c40")
BONE = ramp("4a4640", "7a746a", "aca498", "d8d2c6", "f2eee4")
CLOTH = ramp("0e1220", "18203a", "243258", "34467a")                 # storm-blue banner
BLOOD = ramp("3a1016", "5e1a22")

# ashlar courses on the torus: (y0, y1 inclusive incl. joint row, list of vertical joint xs)
COURSES = [(0, 6, [4, 12]), (7, 15, [9])]


def ashlar_block(x, y):
    """-> (course index, block index, lx, ly, bw, bh, joint?) for pixel x, y of the torus."""
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


def arch_sample(x, y):
    """-> (level, element_centre, joint?)"""
    ci, bi, lx, ly, bw, bh, joint = ashlar_block(x, y)
    j = COURSES[ci][2][bi]
    cen = ((j + bw / 2) % 16, COURSES[ci][0] + bh / 2 - 0.5)
    seed = ci * 7 + bi
    tone = (0, 1, -1, 0, 1)[(seed * 3) % 5]
    if joint:
        # rounded (weathered) block corners: the joint eats one pixel into the corners
        return 2, cen, True
    lv = 7 + tone
    # weather-rounded corners
    corner = (lx in (1, bw - 1)) and (ly in (0, bh - 2))
    if corner:
        return 3 + tone, cen, True
    if ly == 0:
        lv += 1                                   # lit top bevel (rain-wet)
    elif ly == bh - 2:
        lv -= 1                                   # shaded lower bevel
    if lx == 1:
        lv += 1 if ly < bh - 2 else 0
    elif lx == bw - 1:
        lv -= 1
    # sparse pitting (sea-worn)
    r = h01(x, y, 23 + seed)
    if r < 0.07:
        lv -= 2
    elif r > 0.96:
        lv += 1
    return lv, cen, False


def wet(x, y):
    """Rain sheen: a single cold highlight pixel on some block top-bevels."""
    ci, bi, lx, ly, bw, bh, joint = ashlar_block(x, y)
    return (not joint) and ly == 0 and 2 <= lx <= bw - 3 and h01(x, y, 91) < 0.22


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
    # chipped block corners on exposed side faces at the course joints
    for side, x in ((W, 0), (E, 15)):
        if mask & side:
            for y in (6, 15):
                if not (mask & S and y == 15) and h01(y, side, 57) < 0.6:
                    sh[y][x] = False
    if mask & S:                                   # worn, sea-eaten underside
        for x in range(2, TS - 2):
            if h01(x, 2, 13) < 0.14:
                sh[15][x] = False
    return sh


def solid_tile(mask, seed=0):
    img = blank(TS, TS)
    px = img.load()
    sh = solid_shape(mask)

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
            lv, cen, joint = arch_sample(x, y)
            d = dfun(*cen) + 3.0 * h01(int(cen[0] * 3), int(cen[1] * 3), 64 + seed)
            k = depth_steps(d)
            lv -= (0, 2, 3, 4)[k]
            if k >= 2:
                lv = min(lv, 3)
            if mask & W and x < 3:
                lv += (1, 1, 0)[x]
            if mask & E and 15 - x < 2:
                lv -= 1
            if mask & S and 15 - y < 3:
                lv -= (2, 1, 1)[15 - y]
            c = ST[int(clamp(lv, 0, len(ST) - 1))]
            if k == 0 and not joint and wet(x, y) and y > 3:
                c = ST[10]
            px[x, y] = c
    # side faces: cold rim light (W), outline (E, S)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            o_w, o_e, o_s, o_n = out(x, y, -1, 0), out(x, y, 1, 0), out(x, y, 0, 1), out(x, y, 0, -1)
            if o_e or o_s:
                px[x, y] = K
            elif o_w and not (mask & N and y < 4):
                px[x, y] = ST[9] if (y % 7) not in (0, 6) else ST[10]
            elif o_n and not (mask & N):
                px[x, y] = K
    # cold sea-light bouncing up onto undersides
    if mask & S:
        for x in range(TS):
            for y in range(14, 8, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = SEA[6] if (x % 5) else SEA[5]
                    if sh[y - 1][x] and px[x, y - 1] != K and x % 3 == 1:
                        px[x, y - 1] = SEA[4]
                    break
    if mask & N:
        lip(img, sh, mask, out)
    return img


def lip(img, sh, mask, out):
    """Rain-wet worn top edge: cold specular sheen, salt crust, dark shadow line, water drips below."""
    px = img.load()
    for x in range(TS):
        for y in range(4):
            if not sh[y][x]:
                continue
            c = SHEEN[y]
            if y == 0:
                r = h01(x, 0, 83)
                if r < 0.14:
                    c = GLINT                      # cold specular glint on the wet edge
                elif r > 0.8:
                    c = SALT[1]                    # salt crust
                elif r > 0.62:
                    c = SHEEN[1]
            if y == 1:
                r = h01(x, 1, 84)
                if r < 0.12:
                    c = SHEEN[0]
                elif r > 0.78:
                    c = ST[7]
            if y == 2 and h01(x, 2, 85) < 0.25:
                c = ST[5]
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else SHEEN[2]
            elif (mask & W and x == 0) or out(x, y, -1, 0):
                c = SHEEN[0] if y < 2 else SHEEN[2]
            px[x, y] = c
        # rain water dripping off the lip
        L = int(h01(x, 0, 77) ** 4 * 5)
        if (mask & E and x >= 14) or (mask & W and x <= 1):
            L = 0
        for y in range(4, 4 + L):
            if sh[y][x] and px[x, y] != K:
                px[x, y] = ST[1] if y < 3 + L else SEA[6]
    if mask & E:
        px[14, 0] = SHEEN[1]


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


def f_crack(img, mask, k, lo):
    px = img.load()
    pts = [[(4, 5), (6, 7), (6, 9), (8, 11), (9, 13)], [(11, 4), (10, 6), (11, 8), (9, 10), (10, 12)],
           [(3, 9), (5, 10), (7, 10), (8, 12)]][k % 3]
    for (x, y) in polyline([(x, max(lo + 1, y)) for x, y in pts]):
        if _ok(px, x, y, lo):
            px[x, y] = ST[1]
            if _ok(px, x - 1, y, lo) and px[x - 1, y] in ST[4:]:
                px[x - 1, y] = ST[9]


def f_barnacles(img, mask, k, lo):
    """Tide-line crust: a band of grey barnacle cones (lit top, dark mouth) with blue-black mussels."""
    px = img.load()
    base = 12 if not (mask & S) else 10
    if base - 2 < lo + 1:
        return
    x0 = 2 + (k * 3) % 5
    # mussels: small dark wedges hanging below the band
    for i, mx in enumerate((x0 + 1, x0 + 5, x0 + 8)):
        for (ax, ay, c) in ((0, 0, SEA[5]), (1, 0, SEA[4]), (0, 1, SEA[3]), (1, 1, SEA[2]), (1, 2, SEA[1])):
            if _ok(px, mx + ax, base + 1 + ay, lo):
                px[mx + ax, base + 1 + ay] = c
        if _ok(px, mx, base + 1, lo):
            px[mx, base + 1] = SEA[7]
    # barnacles: 3px cones, tight cluster
    for i, (bx, by) in enumerate(((x0, 0), (x0 + 3, -1), (x0 + 6, 0), (x0 + 9, -1), (x0 + 2, -3))):
        if h01(i, k, 5) < 0.2:
            continue
        y = base + by
        for (ax, ay, c) in ((0, 0, SALT[0]), (1, 0, SALT[2]), (2, 0, SALT[0]), (0, 1, ST[6]), (1, 1, ST[1]),
                            (2, 1, ST[4])):
            if _ok(px, bx + ax, y + ay - 1, lo):
                px[bx + ax, y + ay - 1] = c


def f_cramp(img, mask, k, lo):
    """A rusted iron cramp stapling two blocks across a joint, rust bleeding down the stone."""
    px = img.load()
    # pick the joint of the lower course (x = 9) or upper (x = 4 / 12)
    jx, y = ((9, 10), (12, 3), (4, 3))[k % 3]
    if y < lo + 1:
        jx, y = 9, 10
    for x in range(jx - 2, jx + 3):
        if _ok(px, x, y, lo):
            px[x, y] = IRON[4] if x < jx else IRON[3]
        if _ok(px, x, y + 1, lo):
            px[x, y + 1] = ST[1]
    for x in (jx - 2, jx + 2):
        if _ok(px, x, y - 1, lo):
            px[x, y - 1] = IRON[5]
    # a faint rust weep below the cramp
    for i in range(2, 5):
        if _ok(px, jx + 1, y + i, lo) and bt(jx + 1, y + i) < 0.7 - i * 0.12:
            px[jx + 1, y + i] = RUST[1]


def f_lichen(img, mask, k, lo):
    """Sea lichen: soft round muted-mustard rosettes with a paler rim, one grey-green."""
    px = img.load()
    for n, (cx, cy, r, pal) in enumerate(((4.5 + k % 5, 10.5, 2.3, LICHEN), (11.5 - k % 3, 12.5, 1.6, GRASS))):
        cy = max(lo + 2.5, cy)
        for y in range(int(cy - 3), int(cy + 4)):
            for x in range(int(cx - 4), int(cx + 5)):
                d = math.hypot((x + 0.5 - cx) * 0.75, y + 0.5 - cy) + 0.8 * h01(x, y, 47 + n)
                if d < r and _ok(px, x, y, lo):
                    i = 1 if d < r - 0.9 else 2
                    if d < r * 0.35:
                        i = 0
                    if pal is GRASS:
                        i += 2
                    px[x, y] = pal[i]


def f_drain(img, mask, k, lo):
    """Round weep-hole in the wall with rain water trickling out and down the stone."""
    px = img.load()
    cx, cy = (5, 7, 10)[k % 3] + 0.5, max(lo + 3, 8)
    for y in range(cy - 2, cy + 3):
        for x in range(int(cx) - 2, int(cx) + 3):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy - 0.2)
            if d < 2.3 and _ok(px, x, y, lo):
                px[x, y] = ST[0] if d < 1.5 else (ST[9] if y > cy else ST[2])
    # the trickle
    x = int(cx)
    for y in range(cy + 2, 15):
        if _ok(px, x, y, lo):
            px[x, y] = SEA[8] if (y - cy) % 3 else SEA[10]
        if _ok(px, x + 1, y, lo) and y > cy + 3:
            px[x + 1, y] = SEA[4]


FEATURES = [[f_crack], [f_barnacles, f_crack], [f_cramp], [f_lichen, f_crack], [f_drain], [f_barnacles, f_cramp],
            [f_lichen]]


def variant_tile(mask):
    img = solid_tile(mask, seed=5)
    k = (mask * 5 + 2) % len(FEATURES)
    lo = 6 if mask & N else 1
    feats = FEATURES[k]
    if mask == 0:
        feats = [f_crack, f_cramp]
    for f in feats:
        f(img, mask, mask // 2 + k, lo)
    return img


# =========================================================================== platforms
def platform(kind):
    """Wet timber walkway: plank ends seen edge-on (1px gaps), a stringer beam, rusted iron brackets."""
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    x0 = 1 if left else 0
    x1 = 14 if right else 15
    # plank ends: widths chosen so the pattern tiles across neighbouring M tiles (period 16)
    gaps = {3, 7, 12}
    for x in range(x0, x1 + 1):
        g = x in gaps
        # row 0: wet top, cold glints
        r = h01(x, 0, 111)
        px[x, 0] = SHEEN[2] if g else (SHEEN[0] if r < 0.2 else SHEEN[1] if r < 0.55 else WOOD[7])
        # rows 1-2: plank ends
        for y in (1, 2):
            if g:
                px[x, y] = T if y == 2 else WOOD[1]
            else:
                c = WOOD[5] if y == 1 else WOOD[4]
                nx = x + 1 in gaps or x == x1
                if nx:
                    c = WOOD[3]
                if (x - 1) in gaps or x == x0:
                    c = WOOD[6] if y == 1 else WOOD[5]
                if h01(x, y, 112) < 0.12:
                    c = WOOD[2]                    # knot / rot
                px[x, y] = c
        # row 3-4: stringer beam, grain + iron nails
        px[x, 3] = WOOD[4] if x % 6 else IRON[5]
        px[x, 4] = WOOD[2] if h01(x, 4, 113) > 0.2 else WOOD[1]
        px[x, 5] = K
    for y in range(0, 5):
        if left:
            px[0, y] = K
        if right:
            px[15, y] = K

    def bracket(xa, sgn):
        # vertical iron post + diagonal strut, rusted, with a verdigris bolt
        for y in range(6, 15):
            px[xa, y] = IRON[4] if y % 4 else RUST[3]
            px[xa + sgn, y] = IRON[2]
        for i in range(6):
            x, y = xa + sgn * (i + 1), 6 + i
            if 0 <= x < 16:
                px[x, y] = IRON[4] if i % 2 else RUST[2]
                if 0 <= x < 16 and y + 1 < 16:
                    px[x, y + 1] = IRON[2]
        px[xa, 6] = VERD[3]
        for x in range(min(xa, xa + sgn * 7), max(xa, xa + sgn * 7) + 1):     # top flange under the beam
            if 0 <= x < 16 and px[x, 6][3] == 0:
                px[x, 6] = IRON[3]
        # rust weeping down the post
        px[xa, 12] = RUST[2]
    if left:
        bracket(2, 1)
    if right:
        bracket(13, -1)
    if kind == "M":
        # rope lashing: a frayed loop under the beam + a hanging drip
        for (x, y, c) in ((6, 6, WHEAT[2]), (7, 7, WHEAT[3]), (8, 7, WHEAT[2]), (9, 6, WHEAT[1]),
                          (7, 8, WHEAT[1]), (7, 9, WHEAT[2])):
            px[x, y] = c
        px[11, 7] = SEA[9]
    return outline(img)


# =========================================================================== spikes
def spikes_floor():
    """Broken iron railings: spear-headed bars (one snapped, one bent) set in a cracked stone kerb."""
    img = blank(TS, TS)
    px = img.load()
    # (x, top, lean) — lean shifts the top by px
    BARS = [(2, 3, 0), (6, 1, 0), (10, 5, 1), (13, 2, -1)]
    for n, (bx, top, lean) in enumerate(BARS):
        for y in range(top + 3, 14):
            t = (y - top) / (14 - top)
            x = bx + round(lean * (1 - t) * 2)
            px[x, y] = IRON[5] if y % 5 else RUST[3]
            px[x + 1, y] = IRON[3] if (y + n) % 4 else RUST[2]
        # spear head (not on the snapped bar n == 2: a jagged broken end instead)
        x = bx + round(lean * 2)
        if n != 2:
            for (dx, dy, c) in ((0, 0, SHEEN[0]), (1, 0, IRON[6]), (0, 1, IRON[6]), (1, 1, IRON[4]),
                                (-1, 2, IRON[5]), (0, 2, IRON[6]), (1, 2, IRON[4]), (2, 2, IRON[3])):
                px[x + dx, top + dy] = c
            px[x, top - 1] = SHEEN[1] if n == 1 else T
        else:
            px[x, top + 2] = SHEEN[1]
            px[x + 1, top + 3] = IRON[5]
    # lower rail tying the bars together (broken between 6 and 10)
    for x in range(1, 9):
        px[x, 10] = IRON[4]
        px[x, 11] = RUST[1] if x % 3 else IRON[2]
    for x in range(12, 16):
        px[x, 9] = IRON[4]
        px[x, 10] = IRON[2]
    img = outline(img)
    px = img.load()
    # cracked stone kerb the railing is set in
    for x in range(TS):
        px[x, 15] = K
        px[x, 14] = ST[8] if h01(x, 14, 3) < 0.6 else ST[6]
        if x in (5, 11):
            px[x, 14] = ST[2]
        if px[x, 13] == T and h01(x, 13, 4) < 0.35:
            px[x, 13] = ST[7]
            if px[x, 12] == T:
                px[x, 12] = K
    return img


def spikes_ceiling():
    """Dripping basalt fangs hanging from the ceiling, wet highlights, water beads at the tips."""
    img = blank(TS, TS)
    px = img.load()
    FANGS = [(2.5, 9, 2.0), (6.0, 14, 2.4), (9.5, 8, 1.8), (13.0, 12, 2.2)]
    for n, (cx, ln, hw0) in enumerate(FANGS):
        for y in range(1, ln + 1):
            t = (y - 1) / ln
            hw = hw0 * (1 - t) ** 0.9 + 0.35
            wob = 0.5 * math.sin(y * 0.9 + n)
            for x in range(TS):
                dx = x + 0.5 - cx - wob * t
                if abs(dx) <= hw:
                    c = ST[6]
                    if dx < -hw + 1.0:
                        c = ST[9] if y % 3 else SHEEN[1]      # wet lit left flank
                    elif dx > hw - 1.0:
                        c = ST[3]
                    elif (y + n) % 4 == 0:
                        c = ST[5]
                    px[x, y] = c
        tip = (int(cx + 0.5 * math.sin(ln * 0.9 + n)), ln + 1)
        if n in (1, 3) and tip[1] + 1 < 16:
            px[tip[0], min(15, tip[1] + 1)] = SEA[10]        # hanging drop
    img = outline(img)
    px = img.load()
    for x in range(TS):
        px[x, 0] = ST[3] if h01(x, 0, 7) < 0.6 else ST[2]
    for (x, y) in ((6, 15), (13, 14)):
        if y < 16:
            px[x, y] = SEA[10]
    return img


# =========================================================================== background walls
BG = ramp("06070b", "0a0c12", "0e1119", "121621", "171c28", "1c2230", "232a3a", "2c3446")


def bg_course(x, y):
    """Low-contrast interior masonry on the torus (courses of 8, joints offset)."""
    yy = y % 8
    off = 0 if (y // 8) % 2 == 0 else 6
    xx = (x + off) % 16
    if yy == 7 or xx in (0, 11):
        return BG[1]
    v = 3 + (1 if yy == 0 else 0) - (1 if yy == 6 else 0)
    if h01((x + off) // 11, y // 8, 131) < 0.4:
        v -= 1
    if h01(x, y, 132) < 0.06:
        v -= 1
    return BG[max(0, v)]


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            px[x, y] = bg_course(x, y)
    if k == 1:
        # arrow slit: deep dark embrasure, a thin sliver of cold storm light, splayed sill
        for y in range(2, 14):
            for x in range(6, 10):
                px[x, y] = BG[0]
            px[7, y] = SEA[4] if 3 < y < 12 else BG[0]
            px[8, y] = SEA[3] if 3 < y < 12 else BG[0]
            px[5, y] = BG[5]
            px[10, y] = BG[2]
        px[7, 5] = SEA[6]
        px[8, 9] = SEA[5]
        for x in range(4, 12):
            px[x, 14] = BG[6] if x < 11 else BG[4]
            px[x, 15] = BG[2]
        for x in range(6, 10):
            px[x, 1] = BG[4]
    elif k == 2:
        # iron mooring ring on a staple + a rust stain and a salt tide-mark
        cx, cy = 8, 6
        for a in range(0, 360, 20):
            x = cx + round(3 * math.cos(math.radians(a)))
            y = cy + 4 + round(3 * math.sin(math.radians(a)))
            px[x, y] = IRON[3] if a < 180 else IRON[2]
        px[cx - 1, cy], px[cx, cy], px[cx + 1, cy] = IRON[3], IRON[4], IRON[2]
        px[cx, cy + 1] = IRON[3]
        for y in range(cy + 8, 16):
            if bt(cx, y) < 0.6:
                px[cx, y] = RUST[1]
        for x in range(TS):
            if h01(x, 0, 133) < 0.5:
                px[x, 12] = BG[5]                          # salt tide-mark
    elif k == 3:
        # pilaster: engaged column with a lit left edge and fluting, tiles vertically
        for y in range(TS):
            for x in range(3, 13):
                c = [BG[0], BG[7], BG[6], BG[5], BG[5], BG[4], BG[4], BG[3], BG[2], BG[0]][x - 3]
                if x in (6, 9) and y % 8 != 3:
                    c = BG[2]                               # fluting grooves
                px[x, y] = c
            if y % 16 == 3:
                for x in range(3, 13):
                    px[x, y] = BG[6] if x < 9 else BG[3]   # banding ring
    return img


# =========================================================================== overlays
def chain_links(px, x0=7, y0s=(0, 8)):
    ir = IRON
    for y0 in y0s:
        for (x, y, c) in ((0, 0, 4), (1, 0, 4), (-1, 1, 4), (2, 1, 3), (-1, 2, 3), (2, 2, 2), (0, 3, 3), (1, 3, 2)):
            px[x0 + x, y0 + y] = ir[c]
        for y in range(4, 8):
            px[x0, y0 + y] = ir[5] if y < 6 else ir[4]
            px[x0 + 1, y0 + y] = RUST[2] if y == 6 else ir[2]


def deco_chain():
    """42: rusted chain (tiles vertically: links at y=0 and y=8)."""
    img = blank(TS, TS)
    px = img.load()
    chain_links(px)
    return outline(img)


def deco_banner():
    """43: a torn storm banner on a short iron rod: storm-blue cloth, pale bolt sigil, ragged tail."""
    img = blank(TS, TS)
    px = img.load()
    for x in range(1, 15):
        px[x, 1] = IRON[5] if x > 1 else IRON[6]
        px[x, 2] = IRON[2]
    px[0, 1] = IRON[4]
    px[15, 1] = IRON[4]
    # ragged bottom edge per column (wind-torn), cloth leaning slightly to the right (wind)
    bottom = [13, 14, 12, 15, 11, 10, 13, 15, 14, 9, 12, 13, 11]
    for i, x in enumerate(range(2, 14)):
        yb = bottom[i]
        for y in range(3, yb + 1):
            xx = x + (1 if y > 10 and i > 2 else 0)
            c = CLOTH[2] if x < 5 else CLOTH[1]
            if x == 2:
                c = CLOTH[3]
            if y == 3:
                c = CLOTH[3] if x < 8 else CLOTH[2]
            if (x in (6, 10)) and y > 4:
                c = CLOTH[0]                         # fold shadows
            px[xx, y] = c
    # tear hole
    px[9, 8], px[9, 9], px[10, 9] = T, T, T
    # the Spire sigil: a jagged bolt through a ring, bleached pale
    for (x, y) in ((8, 4), (7, 5), (7, 6), (8, 6), (8, 7), (7, 8)):
        px[x, y] = BOLT[2] if y < 7 else BOLT[1]
    for (x, y) in ((5, 5), (5, 6), (6, 4), (10, 5), (9, 4)):
        px[x, y] = CLOTH[3]
    return outline(img)


def deco_lantern():
    """44: a squat storm lantern (hooded, caged glass) sitting on the floor, two candle stubs beside it."""
    img = blank(TS, TS)
    px = img.load()
    cx = 6
    # hood + ring
    px[cx, 2], px[cx + 1, 2] = IRON[4], IRON[3]
    for x in range(cx - 2, cx + 4):
        px[x, 3] = IRON[5] if x < cx + 1 else IRON[3]
    for x in range(cx - 3, cx + 5):
        px[x, 4] = IRON[4] if x < cx + 2 else IRON[2]
    # glass with flame
    for y in range(5, 12):
        for x in range(cx - 2, cx + 4):
            c = AMBER[3] if x < cx + 2 else AMBER[2]
            if y > 9:
                c = AMBER[2] if x < cx + 2 else AMBER[1]
            px[x, y] = c
    for (x, y, c) in ((cx, 6, AMBER[4]), (cx + 1, 6, AMBER[4]), (cx, 7, AMBER[5]), (cx + 1, 7, AMBER[4]),
                      (cx, 8, AMBER[5]), (cx + 1, 8, AMBER[5]), (cx, 5, AMBER[4])):
        px[x, y] = c
    for y in range(5, 12):
        px[cx - 3, y] = IRON[4]
        px[cx + 4, y] = IRON[2]
        if y in (7, 10):
            for x in range(cx - 2, cx + 4):
                px[x, y] = IRON[3] if x != cx else IRON[4]
    for x in range(cx - 3, cx + 5):
        px[x, 12] = IRON[4] if x < cx + 2 else IRON[2]
        px[x, 13] = IRON[2]
    for x in range(cx - 2, cx + 4):
        px[x, 14] = IRON[3]
    # candle stubs with tiny flames
    for (x0, top) in ((12, 10), (14, 12)):
        for y in range(top, 15):
            px[x0, y] = BONE[3] if y > top else BONE[4]
        px[x0, top - 1] = AMBER[4]
        px[x0, top - 2] = AMBER[3]
    for x in range(1, 16):
        px[x, 15] = BONE[1] if x > 10 else IRON[1]
    img = outline(img)
    px = img.load()
    px[12, 8] = AMBER[2]
    return img


def deco_bones():
    """45: a pile of bones (skull, ribs, long bone) with grey-white gull feathers."""
    img = blank(TS, TS)
    px = img.load()
    # long bone lying diagonally
    for i in range(9):
        x, y = 1 + i, 14 - i // 4
        px[x, y] = BONE[3] if i % 8 else BONE[4]
        px[x, y + 1] = BONE[1]
    px[1, 13], px[9, 11] = BONE[4], BONE[4]
    # skull
    for (x, y, c) in ((8, 10, 3), (9, 10, 4), (10, 10, 4), (11, 10, 3), (7, 11, 3), (8, 11, 4), (9, 11, 4),
                      (10, 11, 3), (11, 11, 3), (12, 11, 2), (7, 12, 3), (8, 12, 0), (9, 12, 3), (10, 12, 0),
                      (11, 12, 2), (12, 12, 1), (8, 13, 2), (9, 13, 3), (10, 13, 2), (11, 13, 1),
                      (8, 14, 1), (9, 14, 2), (10, 14, 1)):
        px[x, y] = BONE[c]
    px[8, 12], px[10, 12] = ST[0], ST[0]
    # rib curves
    for (x, y) in ((12, 14), (13, 13), (14, 13), (15, 14), (13, 15), (14, 15)):
        px[x, y] = BONE[2]
    img = outline(img)
    px = img.load()
    # gull feathers (grey vane, white edge, dark tip) lying/drifting — unoutlined for softness
    for i in range(6):
        px[2 + i, 8 - i // 3] = BONE[4] if i < 4 else ST[2]
        px[2 + i, 9 - i // 3] = SALT[0]
    px[1, 9] = BONE[3]
    for i in range(4):
        px[12 + i, 5 + (i // 2)] = BONE[4] if i < 3 else ST[1]
        px[12 + i, 6 + (i // 2)] = SALT[0]
    return img


def deco_tuft():
    """47: wet storm grass bent by the wind + a couple of sea-thrift pom-poms (sits on a surface)."""
    img = blank(TS, TS)
    px = img.load()
    # blades: (root x, height, lean) — all lean right with the gale
    blades = [(0, 5, 2), (2, 7, 3), (3, 4, 1), (5, 8, 3), (7, 6, 2), (8, 4, 1), (10, 7, 3), (12, 4, 1),
              (13, 6, 2)]
    for n, (bx, hgt, lean) in enumerate(blades):
        for j in range(hgt):
            t = j / max(1, hgt - 1)
            x = bx + round(lean * t * t)
            y = 15 - j
            if 0 <= x < 16:
                c = GRASS[4] if j == hgt - 1 else (GRASS[3] if j > hgt // 2 else GRASS[2])
                if n % 3 == 0 and j == hgt - 1:
                    c = GRASS[5]
                px[x, y] = c
    # sea-thrift: two small round pink heads on stiff stems
    for (sx, top) in ((6, 9), (11, 11)):
        for y in range(top + 2, 16):
            px[sx, y] = GRASS[3]
        for (dx, dy, c) in ((-1, 0, 2), (0, 0, 3), (1, 0, 2), (-1, 1, 1), (0, 1, 2), (1, 1, 1), (0, -1, 4)):
            px[sx + dx, top + dy] = THRIFT[c]
    img = outline(img)
    # the outline under ground level is dropped (sits on a surface) — keep bottom row honest
    return img


def breakable():
    img = solid_tile(0)
    px = img.load()
    for pts in ([(6, 2), (7, 5), (6, 8), (8, 10), (9, 13)], [(7, 5), (10, 6)]):
        for (x, y) in polyline(pts):
            px[x, y] = ST[0]
            if (x + 1, y) not in pts and x + 1 < 16 and y % 2 == 0:
                px[x + 1, y] = ST[5]
    return img


# =========================================================================== tileset
def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [variant_tile(m) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(spikes_floor())
    t.append(spikes_ceiling())
    t += [bg_wall(k) for k in range(4)]
    t.append(deco_chain())
    t.append(deco_banner())
    t.append(deco_lantern())
    t.append(deco_bones())
    t.append(breakable())
    t.append(deco_tuft())
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t
