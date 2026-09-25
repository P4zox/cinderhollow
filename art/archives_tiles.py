"""Tileset for the `archives` biome — THE ASHEN ARCHIVES (library-tower grown into the bell tower).

Same 48-frame index layout as every other tileset (docs/ART_SPEC.md section 6):
 0-15  solid terrain, index = mask of AIR neighbours (N=1 E=2 S=4 W=8)
16-31  same masks, variant (book niches carved into the rock, violet glyphs, ink seeps, pinned pages)
32-35  one-way platform L / M / R / single: riveted iron walkway with grating + truss brackets
36/37  floor / ceiling spikes: iron quill-nibs rising out of an ink pool
38-41  background wall: dark bookshelf wall (41 = shelf upright, tiles vertically)
42     hanging chain with a locked grimoire     43 candle cluster
44     stacked tomes                             45 scattered pages
46     breakable wall (looks like 0)             47 top tuft: loose pages + ash dust

Seamless approach copied from env2_tiles: the interior texture is a pure function of the in-tile
pixel on a 16x16 torus (ashlar courses wrap across tile edges), depth darkening depends only on the
distance to the exposed sides (evaluated at each block's centre so blocks darken as units), and all
edge treatment (cornice lip, rim light, outline) is layered on per exposed side.
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
# ink-stained basalt: indigo-tinted near-black -> ash grey
ST = ramp("07060b", "0e0c14", "16131d", "1f1b28", "2a2433", "352e40", "41394d", "50465c", "615670",
          "776b84", "948aa0")
INK = ramp("05040a", "0b0914", "141024", "241a3c", "3c2c5c")          # glossy blue-black ink
PARCH = ramp("3e3428", "6a5c44", "9a8a68", "c4b48c", "e2d6b0", "f6eed6")
GOLD = ramp("5a3c14", "8a6224", "c09440", "ecc870", "fff0b8", "ffffff")
VIO = ramp("22163a", "3a2658", "5a3c86", "8660b8", "b494e4", "e2d0ff")
IRON = ramp("100e16", "221e2a", "383240", "524a5a", "70687a", "978ea0", "c2b8c4")
OAK = ramp("0c0909", "150f0e", "1f1714", "2b201a", "3a2b21", "4c3829", "604733", "785a40")
CRIM = ramp("3a0a14", "6a1420", "a0202e", "e04050")
WAX = ramp("6a5a48", "a8987c", "d8ccb0", "f4ecd8")
# leather book bindings (dark, mid, lit)
BOOKS = [ramp("2e1014", "4e1c20", "74302c"), ramp("0e2024", "183638", "2a5250"), ramp("2e2412", "4e3c1c", "74582a"),
         ramp("22142e", "382448", "553a66"), ramp("241a14", "3c2c20", "5a4430"), ramp("1a1a22", "2c2c38", "44444f")]

# ashlar courses on the torus: (y0, y1 inclusive incl. joint row, list of vertical joint xs)
COURSES = [(0, 7, [7]), (8, 15, [2, 12])]


def ashlar_block(x, y):
    """-> (course index, block index, lx, ly, bw, bh, joint?) for pixel x, y of the torus."""
    for ci, (y0, y1, js) in enumerate(COURSES):
        if y0 <= y <= y1:
            ly = y - y0
            js = sorted(js)
            # which block along x (wrapping)
            for bi, j in enumerate(js):
                nj = js[(bi + 1) % len(js)]
                w = (nj - j) % 16 or 16
                lx = (x - j) % 16
                if lx < w:
                    return ci, bi, lx, ly, w, y1 - y0 + 1, (lx == 0 or ly == y1 - y0)
    raise AssertionError


def arch_sample(x, y):
    """-> (ramp, level, element_centre)"""
    ci, bi, lx, ly, bw, bh, joint = ashlar_block(x, y)
    j = COURSES[ci][2][bi]
    cen = ((j + bw / 2) % 16, COURSES[ci][0] + bh / 2 - 0.5)
    seed = ci * 7 + bi
    tone = (0, 1, -1, 0, 1)[(seed * 3) % 5]
    if joint:
        return ST, 2, cen
    lv = 6 + tone
    if ly == 0:
        lv += 1                                   # lit top bevel
    elif ly == bh - 2:
        lv -= 1                                   # shaded lower bevel
    if lx == 1:
        lv += 1 if ly < bh - 2 else 0
    elif lx == bw - 1:
        lv -= 1
    # chisel speckle / pits
    r = h01(x, y, 17 + seed)
    if r < 0.08:
        lv -= 1
    elif r > 0.95:
        lv += 1
    return ST, lv, cen


def blot(x, y):
    """Old ink soaked into one block of the torus: 0 none, 1 rim, 2 core (applied only near the surface)."""
    bx, by = 5.0, 11.5
    dd = (wrap16(x + 0.5 - bx) / 3.4) ** 2 + ((y + 0.5 - by) / 2.2) ** 2
    if dd < 0.35:
        return 2
    if dd < 1 and bt(x, y) > 0.45:
        return 1
    return 0


def depth_steps(d):
    return (d > 5) + (d > 9) + (d > 12)


LIP = [C("cabba0"), C("9a8a80"), C("62566a"), C("1a1522")]


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
            for y in (7, 15):
                if not (mask & S and y == 15) and h01(y, side, 51) < 0.6:
                    sh[y][x] = False
    if mask & S:
        for x in range(2, TS - 2):
            if h01(x, 2, 9) < 0.12:
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
            r, lv, cen = arch_sample(x, y)
            d = dfun(*cen) + 3.0 * h01(int(cen[0] * 3), int(cen[1] * 3), 60 + seed)
            k = depth_steps(d)
            if r is ST:
                if k == 0:
                    lv -= blot(x, y)
                lv -= (0, 2, 3, 4)[k]
                if k >= 2:
                    lv = min(lv, 3)
            else:
                lv = max(0, lv - (k > 1))
            if mask & W and x < 3 and r is ST:
                lv += (1, 1, 0)[x]
            if mask & E and 15 - x < 2 and r is ST:
                lv -= 1
            if mask & S and 15 - y < 3 and r is ST:
                lv -= (2, 1, 1)[15 - y]
            px[x, y] = r[int(clamp(lv, 0, len(r) - 1))]
    # side faces: rim light (W), outline (E, S)
    for y in range(TS):
        for x in range(TS):
            if not sh[y][x]:
                continue
            o_w, o_e, o_s, o_n = out(x, y, -1, 0), out(x, y, 1, 0), out(x, y, 0, 1), out(x, y, 0, -1)
            if o_e or o_s:
                px[x, y] = K
            elif o_w and not (mask & N and y < 4):
                px[x, y] = ST[8] if (y % 8) not in (0, 7) else ST[9]
            elif o_n and not (mask & N):
                px[x, y] = K
    # faint violet bounce light just above the outline on undersides (glyph-lit from below)
    if mask & S:
        for x in range(TS):
            for y in range(14, 8, -1):
                if sh[y][x] and px[x, y] != K:
                    px[x, y] = VIO[1] if (x % 4) else VIO[0]
                    break
    if mask & N:
        lip(img, sh, mask, out)
    return img


def lip(img, sh, mask, out):
    """Carved cornice: candle-lit worn top edge, moulding, deep shadow line, ink drips below."""
    px = img.load()
    for x in range(TS):
        for y in range(4):
            if not sh[y][x]:
                continue
            c = LIP[y]
            if y == 0 and h01(x, 0, 81) < 0.18:
                c = PARCH[4]                       # candle-warm glints on the worn edge
            if y == 1 and h01(x, 1, 82) < 0.15:
                c = LIP[0]
            if y == 2 and (x % 8 == 3):
                c = GOLD[1]                        # gilt stud in the moulding
            if out(x, y, 1, 0) or (mask & E and x == 15):
                c = K if y else LIP[1]
            elif (mask & W and x == 0) or out(x, y, -1, 0):
                c = LIP[0] if y < 2 else LIP[1]
            px[x, y] = c
        # ink drips running off the cornice
        L = int(h01(x, 0, 71) ** 3 * 5)
        if (mask & E and x >= 14) or (mask & W and x <= 1):
            L = 0
        for y in range(4, 4 + L):
            if sh[y][x] and px[x, y] != K:
                px[x, y] = INK[1] if y < 3 + L else INK[3]
    if mask & E:
        px[14, 0] = LIP[1]


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


def f_niche(img, mask, k, lo):
    """A book niche carved into the rock: dark recess, stone sill, a row of leather spines."""
    px = img.load()
    w = 8 + k % 3
    x0 = 2 + (k * 3) % max(1, 13 - w)
    y0 = max(lo + 1, 5 + k % 2)
    y1 = min(14, y0 + 7)
    if y1 - y0 < 5:
        return
    for y in range(y0, y1 + 1):
        for x in range(x0 - 1, x0 + w + 1):
            if not _ok(px, x, y, lo - 1):
                continue
            if x in (x0 - 1, x0 + w) or y == y0:
                px[x, y] = K if (y == y0 or x == x0 + w) else ST[4]
            elif y == y1:
                px[x, y] = ST[7] if x < x0 + w - 1 else ST[5]       # lit sill
            else:
                px[x, y] = INK[1]
    # books standing on the sill
    x = x0
    i = k
    while x < x0 + w:
        bw = 1 + (h01(i, 3, 5) < 0.45)
        bh = 3 + int(h01(i, 4, 6) * (y1 - y0 - 3))
        br = BOOKS[(i * 5 + k) % len(BOOKS)]
        lean = h01(i, 7, 8) < 0.12 and bw == 1
        for dx in range(bw):
            if x + dx >= x0 + w:
                break
            for y in range(y1 - bh, y1):
                if _ok(px, x + dx, y, lo):
                    c = br[2] if dx == 0 else br[1]
                    if y == y1 - bh:
                        c = br[2]
                    if y == y1 - bh + 2 and bh > 3:
                        c = GOLD[1] if (i % 3 == 0) else br[0]       # spine band
                    px[x + dx, y] = c
        x += bw + (1 if lean else 0)
        i += 1


def f_glyph(img, mask, k, lo):
    """A carved sigil glowing faint violet-gold (the Scribe's warding marks)."""
    px = img.load()
    G = [["..X..", ".X.X.", "X.O.X", ".X.X.", "..X.."],
         ["XXXXX", "X...X", "X.O.X", "..X..", ".XXX."],
         [".XXX.", "X...X", "XO.OX", "X...X", ".X.X."]][k % 3]
    cx, cy = 3 + (k * 5) % 8, max(lo + 1, 6 + k % 3)
    for j, row in enumerate(G):
        for i, ch in enumerate(row):
            X, Y = cx + i, cy + j
            if ch != "." and _ok(px, X, Y, lo):
                px[X, Y] = VIO[3] if ch == "X" else GOLD[3]
                if _ok(px, X + 1, Y + 1, lo) and G[j + 1 if j < 4 else j][min(4, i + 1)] == ".":
                    px[X + 1, Y + 1] = VIO[0]                         # carved shadow


def f_seep(img, mask, k, lo):
    """Ink seeping from a crack: glossy blue-black run with a violet sheen."""
    px = img.load()
    x0 = 3 + (k * 7) % 10
    y0 = max(lo + 1, 4)
    for (x, y) in polyline([(x0 - 2, y0), (x0, y0 + 1), (x0 + 1, y0 + 1)]):
        if _ok(px, x, y, lo):
            px[x, y] = INK[0]
    for y in range(y0 + 1, 15):
        x = x0 + (1 if (y - y0) > 6 else 0)
        if _ok(px, x, y, lo):
            px[x, y] = INK[2] if y % 4 else INK[4]
        if _ok(px, x + 1, y, lo) and y > y0 + 2:
            px[x + 1, y] = INK[1]
    if _ok(px, x0, 14, lo):
        px[x0 + 1, 14] = INK[4]


def f_page(img, mask, k, lo):
    """A parchment page nailed to the stone, lines of script, curled corner."""
    px = img.load()
    x0, y0 = 4 + (k * 3) % 7, max(lo + 1, 5 + k % 3)
    for y in range(y0, min(15, y0 + 7)):
        for x in range(x0, x0 + 5):
            if not _ok(px, x, y, lo):
                continue
            c = PARCH[2] if x < x0 + 4 else PARCH[1]
            if y > y0 + 1 and (y - y0) % 2 == 0 and x0 < x < x0 + 4:
                c = PARCH[0]                                         # script line
            if y == y0 + 6 and x == x0 + 4:
                c = PARCH[1]                                         # curled corner
            px[x, y] = c
    if _ok(px, x0 + 2, y0, lo):
        px[x0 + 2, y0] = IRON[5]                                    # nail
    for x in range(x0 + 1, x0 + 6):
        if _ok(px, x, min(14, y0 + 7), lo):
            px[x, min(14, y0 + 7)] = ST[1]                           # drop shadow


def f_crack(img, mask, k, lo):
    px = img.load()
    pts = [[(4, 5), (6, 7), (6, 9), (8, 11), (9, 13)], [(11, 4), (10, 6), (11, 8), (9, 10)],
           [(3, 9), (5, 10), (7, 10), (8, 12)]][k % 3]
    for (x, y) in polyline([(x, max(lo + 1, y)) for x, y in pts]):
        if _ok(px, x, y, lo):
            px[x, y] = ST[1]
            if _ok(px, x - 1, y, lo) and px[x - 1, y] in ST[3:]:
                px[x - 1, y] = ST[8]


FEATURES = [[f_niche], [f_glyph, f_crack], [f_seep], [f_page, f_crack], [f_niche, f_seep]]


def variant_tile(mask):
    img = solid_tile(mask, seed=5)
    k = (mask * 7 + 1) % 5
    lo = 6 if mask & N else 1
    feats = FEATURES[k]
    if mask & N and f_page in feats:
        feats = [f_glyph if f is f_page else f for f in feats]
    if mask == 0:
        feats = [f_seep]
    for f in feats:
        f(img, mask, mask // 2 + k, lo)
    return img


# =========================================================================== platforms
def platform(kind):
    """Riveted iron walkway: lit tread plate, open lattice under it, truss brackets at the ends."""
    img = blank(TS, TS)
    px = img.load()
    left, right = kind in ("L", "single"), kind in ("R", "single")
    ir = IRON
    for x in range(TS):
        if (left and x == 0) or (right and x == 15):
            continue
        px[x, 0] = ir[6] if h01(x, 0, 101) > 0.25 else PARCH[3]       # candle-lit worn tread
        px[x, 1] = ir[4] if x % 4 else GOLD[2]                          # rivets
        # open lattice (holes are transparent -> background shows through)
        for y in (2, 3):
            hole = (x + y) % 3 == 0
            px[x, y] = T if hole else (ir[3] if y == 2 else ir[2])
        px[x, 4] = ir[2]
        px[x, 5] = K
    for y in range(1, 5):
        if left:
            px[0, y] = K
            px[1, y] = ir[4]
        if right:
            px[15, y] = K
            px[14, y] = ir[2]
    # truss brackets under the ends (diagonal strut back to the wall / pillar)
    def strut(xa, sgn):
        for i in range(7):
            x, y = xa + sgn * i, 6 + i
            if 0 <= x < 16:
                px[x, y] = ir[4] if i % 3 else GOLD[1]
                if 0 <= x + sgn < 16:
                    px[x + sgn, y] = ir[2]
    if left:
        for y in range(6, 14):
            px[2, y] = ir[4] if y % 4 else ir[5]
            px[3, y] = ir[2]
        strut(4, 1)
    if right:
        for y in range(6, 14):
            px[13, y] = ir[3]
            px[12, y] = ir[4] if y % 4 else ir[5]
        strut(11, -1)
    if kind == "M":          # a short hanging chain with a dangling tag of parchment
        for y in range(6, 11):
            px[8, y] = ir[4] if y % 2 else ir[2]
        for y in range(11, 14):
            for x in (7, 8, 9):
                px[x, y] = PARCH[3] if x < 9 else PARCH[2]
        px[8, 12] = PARCH[1]
    return outline(img)


# =========================================================================== spikes
def spikes(down=False):
    """Iron quill-nibs: split, pierced pen nibs standing up out of a black ink pool."""
    img = blank(TS, TS)
    px = img.load()
    dark, mid, lit, tip = IRON[2], IRON[4], IRON[6], GOLD[4]
    NIBS = [(2.5, 4, 1.9), (6.5, 1, 2.3), (10.5, 5, 1.9), (13.5, 2, 2.0)]
    for n, (cx, ty, hw0) in enumerate(NIBS):
        for y in range(ty, 14):
            t = (y - ty) / (13 - ty)
            hw = 0.3 + hw0 * min(1.0, (t / 0.7) ** 0.8)
            if t > 0.85:
                hw = hw0 * 0.75                                 # the nib's neck into the holder
            for x in range(TS):
                dx = x + 0.5 - cx
                if abs(dx) <= hw:
                    c = mid
                    if dx < -0.2:
                        c = lit if dx > -hw + 0.8 or hw < 1 else mid
                    if dx >= hw * 0.4:
                        c = dark
                    if y <= ty + 1:
                        c = tip
                    px[x, y] = c
        # slit + breather hole
        sx = int(cx)
        for y in range(ty + 2, ty + 2 + max(2, (13 - ty) // 2)):
            if px[sx, y][3]:
                px[sx, y] = K
        hy = ty + 2 + max(2, (13 - ty) // 2)
        if hy < 13:
            px[sx, hy] = K
            if px[sx - 1, hy][3]:
                px[sx - 1, hy] = INK[2]
        # ink bead on the tip (one blood-red)
        if n == 1:
            px[sx, ty] = CRIM[3]
            px[sx, ty + 1] = CRIM[2]
    img = outline(img)
    px = img.load()
    for x in range(TS):
        px[x, 15] = K
        px[x, 14] = INK[1] if h01(x, 14, 4) < 0.7 else INK[3]
        if h01(x, 13, 4) < 0.3 and px[x, 13] == T:
            px[x, 13] = INK[2]
            if px[x, 12] == T:
                px[x, 12] = K
    if down:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


# =========================================================================== background walls
BG = ramp("07060b", "0b0a11", "100e17", "15121e", "1a1625", "201b2d", "282136")
BGB = [ramp("140a10", "1e0f16", "2a1620"), ramp("0a1216", "0f1a20", "16242a"), ramp("15110c", "1f1912", "2a2218"),
       ramp("120c1a", "1a1226", "241a32"), ramp("110e0d", "1a1513", "241d1a")]


def shelf_books(px, x0, x1, seed, gap_at=None, lean_at=None):
    """Row of books standing on the plank at y=12, between columns x0..x1."""
    x, i = x0, 0
    while x <= x1:
        bw = 1 + (h01(i, seed, 5) < 0.55)
        bh = 6 + int(h01(i, seed, 6) * 6)
        br = BGB[int(h01(i, seed, 7) * len(BGB)) % len(BGB)]
        if gap_at is not None and gap_at <= x < gap_at + 3:
            x += 1
            i += 1
            continue
        for dx in range(bw):
            if x + dx > x1:
                break
            for y in range(12 - bh, 12):
                c = br[2] if dx == 0 else br[1]
                if y == 12 - bh:
                    c = br[1]
                if y == 12 - bh + 2:
                    c = br[0] if (i % 3) else C("3a2c18")          # tarnished gilt band
                px[x + dx, y] = c
        x += bw
        if h01(i, seed, 9) < 0.25:
            x += 1                                                  # 1px dark gap
        i += 1
    if lean_at is not None:                                          # a book leaning into a gap
        for j in range(8):
            X = lean_at + j // 3
            px[X, 11 - j] = BGB[0][2]
            px[X + 1, 11 - j] = BGB[0][1]


def bg_wall(k):
    img = blank(TS, TS)
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            px[x, y] = BG[1] if y < 2 else BG[0] if (x + y) % 7 else BG[1]      # deep shelf back
    if k == 3:
        # vertical shelf upright (tiles vertically), with plank stubs at both sides
        for y in range(TS):
            for x in range(4, 12):
                c = [BG[0], BG[5], BG[4], BG[4], BG[3], BG[3], BG[2], BG[0]][x - 4]
                if 5 <= x <= 10 and h01(x, y // 4, 123) < 0.12:
                    c = BG[2]
                px[x, y] = c
            if y in (12, 13):
                for x in list(range(0, 4)) + list(range(12, 16)):
                    px[x, y] = BG[5] if y == 12 else BG[3]
        for y in (3, 11):                                                       # carved rosettes
            px[7, y], px[8, y] = BG[6], BG[3]
        return img
    seed = 10 + k
    shelf_books(px, 0, 15, seed, gap_at=(9 if k == 1 else None), lean_at=(9 if k == 1 else None))
    # plank + its shadow
    for x in range(TS):
        px[x, 12] = BG[6] if x % 5 else BG[5]
        px[x, 13] = BG[4]
        px[x, 14] = BG[2]
        px[x, 15] = BG[1]
    if k == 2:
        # a stack of books lying flat in a gap on the shelf + a faint violet glyph plate above
        for x in range(8, 15):
            for y in range(4, 12):
                px[x, y] = BG[0]
        for j, (x0, x1, br) in enumerate(((8, 14, BGB[4]), (9, 14, BGB[0]), (8, 13, BGB[3]), (9, 13, BGB[1]))):
            yb = 11 - j * 2
            for x in range(x0, x1 + 1):
                px[x, yb] = br[1]
                px[x, yb - 1] = br[2] if x > x0 else br[1]
            px[x1, yb - 1] = C("2a2432")
        px[3, 3], px[4, 4], px[2, 4], px[3, 5] = C("2e2044"), C("2e2044"), C("2e2044"), C("2e2044")
        px[3, 4] = C("4a3470")
    return img


# =========================================================================== overlays
def chain_links(px, x0=7):
    ir = IRON
    for y0 in (0, 8):
        for (x, y, c) in ((0, 0, 4), (1, 0, 4), (-1, 1, 4), (2, 1, 3), (-1, 2, 3), (2, 2, 2), (0, 3, 3), (1, 3, 2)):
            px[x0 + x, y0 + y] = ir[c]
        for y in range(4, 8):
            px[x0, y0 + y] = ir[5] if y < 6 else ir[4]
            px[x0 + 1, y0 + y] = ir[2]


def deco_hang():
    """42: chain (tiles vertically) with a grimoire strapped shut by an iron band + gold padlock."""
    img = blank(TS, TS)
    px = img.load()
    chain_links(px)
    b = BOOKS[0]
    x0, y0, w, h = 3, 5, 10, 9
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            c = b[1]
            if x <= x0 + 1:
                c = b[2] if x == x0 else b[1]                              # rounded spine, lit
                if (y - y0) in (2, 6):
                    c = GOLD[1]                                             # raised bands
            elif y == y0:
                c = b[2]
            elif y >= y0 + h - 2 and x > x0 + 1:
                c = PARCH[3] if y == y0 + h - 2 else PARCH[1]              # page block below
            elif x >= x0 + w - 2:
                c = PARCH[2] if x == x0 + w - 2 else PARCH[1]              # fore-edge
            px[x, y] = c
    for (x, y) in ((x0 + 5, y0 + 2), (x0 + 4, y0 + 3), (x0 + 6, y0 + 3), (x0 + 5, y0 + 4)):
        px[x, y] = GOLD[2]                                                  # cover emblem
    px[x0 + 5, y0 + 3] = VIO[3]
    for y in range(y0, y0 + h):
        px[x0 + 7, y] = IRON[4] if y % 2 else IRON[3]                      # iron strap
    px[x0 + 8, y0 + 4], px[x0 + 9, y0 + 4] = GOLD[3], GOLD[2]              # padlock
    px[x0 + 8, y0 + 5], px[x0 + 9, y0 + 5] = GOLD[2], GOLD[1]
    return outline(img)


def deco_candles():
    """43: cluster of tallow candles on a wax puddle (static flames; the engine may glow them)."""
    img = blank(TS, TS)
    px = img.load()
    for (cx, top) in ((4, 8), (7, 4), (10, 9), (12, 11)):
        for y in range(top + 1, 15):
            px[cx, y] = WAX[2] if y > top + 1 else WAX[3]
            px[cx + 1, y] = WAX[1]
        px[cx + 1, top + 2] = WAX[3]                                      # drip
        # flame
        px[cx, top - 2] = GOLD[3]
        px[cx, top - 1] = GOLD[4]
        px[cx, top] = GOLD[5]
        px[cx + 1, top] = GOLD[2]
        px[cx, top + 1] = OAK[1]                                          # wick
    for x in range(2, 15):
        px[x, 15] = WAX[1] if x % 3 else WAX[0]
        if 3 <= x <= 13:
            px[x, 14] = WAX[2] if px[x, 14][3] == 0 else px[x, 14]
    img = outline(img)
    px = img.load()
    for (x, y) in ((6, 1), (11, 5), (2, 5)):                              # rising sparks (no outline)
        px[x, y] = GOLD[3]
    return img


def book_flat(px, x0, y0, w, h, br, pages=True):
    """A book lying flat, spine facing the viewer: cover top/bottom rows, page block between."""
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + h):
            if y == y0:
                c = br[2]
            elif y == y0 + h - 1:
                c = br[0]
            elif pages and x > x0 and x < x0 + w - 1 and y0 < y < y0 + h - 1 and x > x0 + w - 3:
                c = PARCH[3] if y % 2 else PARCH[2]                      # page edges on the right
            else:
                c = br[1]
            px[x, y] = c
    if h >= 3:
        px[x0 + 1, y0 + 1] = GOLD[2]
        if w > 7:
            px[x0 + 3, y0 + 1] = GOLD[1]


def deco_tomes():
    """44: a leaning stack of heavy tomes with a stub of candle on top."""
    img = blank(TS, TS)
    px = img.load()
    book_flat(px, 1, 12, 13, 4, BOOKS[4])
    book_flat(px, 2, 9, 11, 3, BOOKS[0])
    book_flat(px, 3, 6, 10, 3, BOOKS[3])
    book_flat(px, 2, 4, 9, 2, BOOKS[1])
    # candle stub + melted wax running over the covers
    for y in range(1, 4):
        px[6, y] = WAX[2]
        px[7, y] = WAX[1]
    px[6, 0] = GOLD[4]
    px[5, 4] = WAX[3]
    px[5, 5] = WAX[2]
    # a book standing upright, leaning against the stack
    for j in range(9):
        px[14, 15 - j] = BOOKS[2][2] if j < 8 else BOOKS[2][1]
        px[15, 15 - j] = BOOKS[2][1]
    img = outline(img)
    px = img.load()
    px[6, 0] = GOLD[4]
    return img


def deco_pages():
    """45: loose pages strewn on the floor (flat sheets + one open leaf with script), a quill, two
    pages drifting down."""
    img = blank(TS, TS)
    px = img.load()
    # an open leaf lying at a slight skew, script lines
    for j in range(3):
        for i in range(7):
            x, y = 2 + i, 12 + j - (1 if i > 4 and j == 0 else 0)
            px[x, y] = PARCH[4] if j == 0 else PARCH[3]
            if j >= 1 and i % 2 == 1 and 0 < i < 6:
                px[x, y] = INK[3]
    for i in range(7):
        px[2 + i, 15] = PARCH[1]
    # flat sheets
    for (x0, y0, w) in ((9, 14, 6), (0, 15, 3)):
        for i in range(w):
            px[x0 + i, y0] = PARCH[4] if i % 2 else PARCH[3]
            if y0 + 1 < 16:
                px[x0 + i, y0 + 1] = PARCH[1]
    # quill lying across the sheets
    for i in range(6):
        px[8 + i, 13 - i // 3] = PARCH[5] if i > 1 else PARCH[1]
    px[7, 14] = K
    img = outline(img)
    px = img.load()
    # drifting pages (unoutlined, tilted -> read as mid-air)
    for (x, y, w) in ((3, 3, 3), (11, 6, 3)):
        for i in range(w):
            px[x + i, y + (i // 2)] = PARCH[4]
            px[x + i, y + 1 + (i // 2)] = PARCH[2]
    return img


def deco_tuft():
    """47: ash dust drifted along the ledge with loose pages lying flat / curling (sits on the surface)."""
    img = blank(TS, TS)
    px = img.load()
    for x in range(TS):                                             # low dust drift
        hgt = int(2.4 * max(0.0, math.sin((x + 2) * 0.45)) * (0.5 + h01(x // 4, 1, 3)))
        for j in range(hgt):
            px[x, 15 - j] = ST[8] if j == hgt - 1 else ST[6]
    # flat pages: thin cream slivers (lit top edge, shaded underside), one curling up at the end
    for (x0, y0, w, curl) in ((1, 14, 5, 1), (8, 15, 6, 0), (10, 13, 4, 0)):
        for i in range(w):
            px[x0 + i, y0] = PARCH[4] if i % 3 else PARCH[3]
            if y0 + 1 < 16:
                px[x0 + i, y0 + 1] = PARCH[1]
        if curl:
            px[x0 + w, y0 - 1] = PARCH[4]
            px[x0 + w, y0] = PARCH[2]
            px[x0 + w + 1, y0 - 2] = PARCH[3]
    px[12, 12], px[13, 12] = INK[2], INK[3]                         # ink blot on a page
    return outline(img)


def breakable():
    img = solid_tile(0)
    px = img.load()
    for pts in ([(6, 2), (7, 5), (6, 8), (8, 10), (9, 13)], [(7, 5), (10, 6)]):
        for (x, y) in polyline(pts):
            px[x, y] = ST[0]
            if (x + 1, y) not in pts and x + 1 < 16 and y % 2 == 0:
                px[x + 1, y] = ST[4]
    return img


# =========================================================================== tileset
def build_tileset():
    t = [solid_tile(m) for m in range(16)]
    t += [variant_tile(m) for m in range(16)]
    t += [platform(k) for k in ("L", "M", "R", "single")]
    t.append(spikes())
    t.append(spikes(down=True))
    t += [bg_wall(k) for k in range(4)]
    t.append(deco_hang())
    t.append(deco_candles())
    t.append(deco_tomes())
    t.append(deco_pages())
    t.append(breakable())
    t.append(deco_tuft())
    assert len(t) == 48 and all(i.size == (16, 16) for i in t)
    return t
