"""Parallax for the `archives` biome — THE ASHEN ARCHIVES.

bg_archives_far : 512x216 opaque, horizontally tileable. The inside of the colossal library-tower:
                  the curved far wall is tier upon tier of shelf-galleries (the rings bow with the
                  cylinder's perspective around the horizon line, via a cosine of period 512 so the
                  layer tiles), pale shafts of light fall from the bell-chamber far above onto a
                  huge central spiral of shelves (a book-tower wound by a helical gallery), the
                  great bell hangs as a silhouette in the light; candle dots and faint violet glyphs.
bg_archives_mid : 512x216 transparent, tileable. Silhouettes: shelf towers with gothic crowns,
                  rolling ladders, an iron bridge, chains dropping from above with cages of books,
                  a giant tome bound in chains, drifts of fallen books on the floor.

Built like env_bg / env2_bg: wrapping Canvas, tileable value noise, ordered dithering onto short
ramps, 1px rim light on the lit edges of silhouettes.
"""
import math, random
from envlib import C, ramp, T, K, bt, pick, h01, smooth, clamp, Canvas
from env_bg import tn, wrapdx
from archives_tiles import GOLD, VIO, PARCH

W, H = 512, 216

# =========================================================================== FAR
FAR = ramp("040308", "07060c", "0a0810", "0d0b15", "110e1b", "151121", "1a1528", "201a30", "261f38",
           "2d2541", "352c4b", "3f3456", "4a3e62", "574970", "66577e", "7a6b90", "9486a8", "b4a8c4")
H0 = 118          # eye level: rings above it bow upward at the sides, below it downward
CX = 256          # the central spiral
BEAMS = [(146, 36, 0.30, 0.34), (206, 12, 0.30, 0.20), (236, 6, 0.30, 0.16), (430, 20, 0.30, 0.13)]


def ring_r(x, y):
    """Map screen y to the cylinder's ring coordinate (undo the perspective bow)."""
    c = math.cos(2 * math.pi * (x - CX) / W)
    return H0 + (y - H0) / (1 + 0.42 * (1 - c) / 2)


def beam(x, y):
    """Light-shaft intensity 0..1 at (x, y)."""
    v = 0.0
    for (bx, bw, sl, amp) in BEAMS:
        cx = bx + sl * y
        d = abs(wrapdx(x, cx))
        if d < bw:
            e = smooth(0, 1, 1 - d / bw)
            fall = 1 - smooth(0, 215, y) * 0.75
            flick = 0.85 + 0.15 * tn(x + y * 2, y, 8, 16, 9)
            v += amp * e * fall * flick
    return v


def wall_tex(x, y):
    """Value offset of the curved far wall of shelf-galleries at (x, y); + list of specials."""
    r = ring_r(x, y)
    t = (r - 6) % 24
    tier = int((r - 6) // 24)
    xx = x % 64
    if xx < 5:                                              # pilaster between shelf bays
        return (0.05 if xx == 0 else 0.02 if xx < 3 else -0.03), None
    if t < 1.2:
        return 0.12, ("candle" if (x + tier * 29) % 53 == 0 and 30 < y < 200 else None)
    if t < 2.4:
        return 0.05, None                                   # balustrade rail
    if t < 4.5:
        return (-0.07 if (x + tier) % 4 else 0.02), None     # balusters over deep shadow
    if t < 6:
        return -0.08, None
    if t < 19:
        # two shelf rows of book spines
        s = (t - 6) % 6.5
        if s < 1:
            return 0.03, None                               # plank
        col = (x + tier * 7) // 2
        top = 1 + h01(col, tier, 3) * 3.4
        if s < top:
            return -0.06, None                              # gap above the books
        return -0.01 + 0.06 * (h01(col, tier * 3 + int(t // 6.5), 4) - 0.5), None
    return -0.10, None                                      # the void under the next gallery


def build_archives_far():
    cv = Canvas(W, H, wrap=True)
    val = [[0.0] * W for _ in range(H)]
    spec = {}
    for y in range(H):
        for x in range(W):
            gx = math.cos(2 * math.pi * (x - CX) / W)
            amb = 0.09 + 0.15 * math.exp(-((y - 105) / 80.0) ** 2) + 0.13 * max(0.0, gx) ** 2
            amb += 0.30 * math.exp(-math.hypot(wrapdx(x, CX) * 0.8, y + 20) / 70.0)      # oculus glow above
            tv, sp = wall_tex(x, y)
            # contrast of the wall fades into gloom far above and in the abyss below
            f = 0.35 + 0.65 * math.exp(-((y - 110) / 85.0) ** 2)
            v = amb + tv * f * 1.5 + beam(x, y)
            v += 0.03 * (tn(x, y, 32, 24, 5) - 0.5)
            val[y][x] = v
            if sp:
                spec[(x, y)] = sp
    # ---------------------------------------------------------------- central spiral of shelves
    CT = 50                                                  # top of the shelf column (a cone roof above)

    def colw(y):
        return 22 + 18 * smooth(CT, 216, y)

    for y in range(CT - 18, H):
        rc = colw(y) if y >= CT else colw(CT) * (y - (CT - 18)) / 18.0
        if rc < 0.6:
            continue
        for x in range(int(CX - rc - 3), int(CX + rc + 4)):
            nx = (x + 0.5 - CX) / rc
            if abs(nx) > 1:
                if abs(nx) < 1 + 3 / max(rc, 3):
                    val[y][x % W] -= 0.06
                continue
            nz = math.sqrt(1 - nx * nx)
            lit = 0.5 + 0.5 * (-0.8 * nx + 0.4 * nz)
            if y < CT:                                       # slate cone roof, lit on the left
                val[y][x % W] = 0.14 + 0.30 * lit + (0.06 if (y % 3 == 0) else 0)
                continue
            u = math.asin(nx) * rc                           # arc length around the column
            s = (y - CT) % 9
            fade = 0.55 + 0.45 * smooth(CT, 140, y)
            v = 0.14 + 0.34 * lit * fade
            if s == 0:
                v += 0.07 * fade
            elif s < 3:
                v -= 0.05
            else:
                col = int((u + 200) // 2)
                v += 0.08 * (h01(col, y // 9, 11) - 0.5) * fade
            v += beam(x, y) * 0.8 * (0.4 + 0.6 * lit)
            val[y][x % W] = v
            if s == 0 and int(u + 400) % 13 == 0 and ((y - CT) // 9) % 3 == 1 and 40 < y < 200 and nx < 0.6:
                spec[(x % W, y - 1)] = "candle"
    # the helical gallery wound around it: back half, then (after quantising) front half
    ribbon = []
    P = 46.0
    th = 0.0
    while True:
        yc = 236 - P * th / (2 * math.pi)
        if yc < CT + 2:
            break
        rh = colw(yc) + 12
        ribbon.append((CX + rh * math.sin(th), yc, math.cos(th), th))
        th += 0.008
    for (x, yc, z, th) in ribbon:
        if z < 0:
            for dy in range(0, 3):
                yy = int(yc) + dy
                if 0 <= yy < H:
                    val[yy][int(x) % W] = (0.24 if dy == 0 else 0.13) + beam(x, yy) * 0.5
    for y in range(H):
        for x in range(W):
            cv.set(x, y, pick(FAR, val[y][x], x, y))
    # front half of the gallery: lit tread, slab face, dark underside, balustrade posts, lamps
    for (x, yc, z, th) in ribbon:
        if z >= 0:
            lit = 0.55 + 0.45 * math.sin(th + 1.2)
            xi = int(x)
            for dy, dv in ((-3, None), (-2, None), (-1, None), (0, 0.62), (1, 0.44), (2, 0.34), (3, 0.24), (4, 0.10)):
                yy = int(yc) + dy
                if not (0 <= yy < H):
                    continue
                if dv is None:
                    if xi % 4 == 0 or dy == -3:
                        cv.set(xi, yy, pick(FAR, 0.18 + 0.3 * lit + beam(x, yy) * 0.5, xi, yy))
                    continue
                cv.set(xi, yy, pick(FAR, 0.06 + dv * lit + beam(x, yy) * 0.6, xi, yy))
            if int(th * 125) % 211 == 0 and 30 < yc < 205:
                spec[(xi, int(yc) - 4)] = "candle"
    # ---------------------------------------------------------------- the great bell in the light
    bx, by = CX, 8
    for y in range(by, by + 22):
        t = (y - by) / 22
        hw = 4 + 7 * t ** 1.8 + (2 if y > by + 19 else 0)
        for x in range(int(bx - hw), int(bx + hw) + 1):
            e = (x - bx) / max(hw, 1)
            v = 0.05 + 0.10 * max(0, -e) + (0.12 if (y == by + 19) else 0)
            cv.set(x, y, pick(FAR, v, x, y))
    for x in range(bx - 1, bx + 2):
        cv.set(x, by + 23, FAR[3])                           # clapper
    for y in range(0, by):
        cv.set(bx, y, FAR[3])
        cv.set(bx + 1, y, FAR[2])
    for x in range(bx - 46, bx + 47):                        # the yoke beam
        cv.set(x, 3, FAR[5] if (x % 9) else FAR[8])
        cv.set(x, 4, FAR[2])
    # ---------------------------------------------------------------- specials: candles, glyphs, motes
    for (x, y), sp in spec.items():
        if sp == "candle":
            a = smooth(20, 90, y) * (1 - smooth(170, 215, y))
            cv.set(x, y, GOLD[3] if a > 0.6 else GOLD[2] if a > 0.3 else GOLD[1])
            if a > 0.5:
                cv.set(x, y + 1, GOLD[1])
    rnd = random.Random(21)
    for i in range(46):                                      # faint violet glyph-motes, gold sparks
        x, y = rnd.randrange(W), rnd.randrange(20, 200)
        near = abs(wrapdx(x, CX)) < 90
        if not near and rnd.random() < 0.5:
            continue
        c = [VIO[1], VIO[2], VIO[3], GOLD[1]][rnd.randrange(4) if near else rnd.randrange(2)]
        cv.set(x, y, c)
        if rnd.random() < 0.3:
            cv.set(x + 1, y, VIO[1])
    for (bx0, bw, sl, amp) in BEAMS[:2]:                      # dust / page specks drifting in the beams
        for i in range(18):
            y = rnd.randrange(10, 190)
            x = bx0 + sl * y + rnd.uniform(-bw * 0.6, bw * 0.6)
            cv.set(x, y, FAR[15] if rnd.random() < 0.4 else FAR[13])
    return cv.img


# =========================================================================== MID
MD = ramp("08070d", "0c0a12", "110e18", "16121f", "1c1727", "231d30")
RIM_V = C("3c3058")
RIM_V2 = C("54447a")
RIM_G = C("6e5636")
BOOKM = [C("24121a"), C("122024"), C("241c12"), C("1c142a"), C("1e1a18")]


def rect(cv, x0, x1, y0, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            cv.set(x, y, c)


def chain(cv, x, y0, y1, dx=0.0):
    """Vertical-ish chain of 2px links from (x, y0) to y1, drifting by dx per px."""
    for y in range(int(y0), int(y1)):
        xx = x + dx * (y - y0)
        k = (y - int(y0)) % 6
        if k in (0, 5):
            cv.set(xx, y, MD[4])
            cv.set(xx + 1, y, MD[4])
        elif k in (1, 2, 3, 4):
            if k in (1, 4):
                cv.set(xx - (0 if (y // 6) % 2 else 0), y, MD[3])
                cv.set(xx + 1, y, MD[3])
            else:
                cv.set(xx, y, MD[3] if (y // 6) % 2 else MD[2])
                cv.set(xx + 1, y, MD[2] if (y // 6) % 2 else MD[3])


def shelf_tower(cv, x0, w, top, seed):
    """Tall freestanding bookcase with a pointed gothic crown, running off the bottom of the layer."""
    rnd = random.Random(seed)
    x1 = x0 + w - 1
    # crown: pointed gable with finial
    cxm = x0 + w / 2
    gh = w * 0.45
    for y in range(int(top - gh - 8), int(top) + 1):
        for x in range(x0 - 2, x1 + 3):
            dxn = abs(x + 0.5 - cxm) / (w / 2 + 2)
            yl = top - gh * (1 - dxn)
            if y >= yl:
                cv.set(x, y, MD[2])
    for y in range(int(top - gh - 8), int(top - gh) + 1):      # finial spike
        cv.set(cxm, y, MD[3])
    cv.set(cxm - 1, int(top - gh - 3), MD[3])
    cv.set(cxm + 1, int(top - gh - 3), MD[3])
    # rose window in the gable (faint violet)
    ry = top - gh * 0.45
    for y in range(int(ry - 4), int(ry + 5)):
        for x in range(int(cxm - 4), int(cxm + 5)):
            d = math.hypot(x + 0.5 - cxm, y + 0.5 - ry)
            if d < 3.6:
                cv.set(x, y, VIO[0] if d > 2.2 or (x + y) % 2 else VIO[1])
    # frame + cornice
    rect(cv, x0 - 2, x1 + 2, top, top + 3, MD[3])
    rect(cv, x0, x1, top + 4, H - 1, MD[1])
    rect(cv, x0, x0 + 2, top + 4, H - 1, MD[3])
    rect(cv, x1 - 2, x1, top + 4, H - 1, MD[2])
    # shelves of books
    y = top + 6
    while y < H:
        sh = 15
        rect(cv, x0 + 3, x1 - 3, y, y + sh - 1, MD[0])
        x = x0 + 3
        while x <= x1 - 3:
            bw = rnd.choice((1, 2, 2, 3))
            bh = rnd.randint(8, 13)
            c = rnd.choice(BOOKM)
            if rnd.random() < 0.1:
                x += 2
                continue
            for dx in range(bw):
                if x + dx > x1 - 3:
                    break
                for yy in range(y + sh - 1 - bh, y + sh - 1):
                    cv.set(x + dx, yy, c if dx else MD[3] if yy == y + sh - 1 - bh else MD[2])
            x += bw
        rect(cv, x0 + 3, x1 - 3, y + sh - 1, y + sh, MD[3])      # plank
        y += sh + 1


def ladder(cv, xb, yb, xt, yt, wd=7):
    n = int(abs(yb - yt))
    for i in range(n + 1):
        t = i / n
        x = xb + (xt - xb) * t
        y = yb + (yt - yb) * t
        cv.set(x, y, MD[4])
        cv.set(x + wd, y, MD[3])
        if int(y) % 7 == 0:
            for k in range(1, wd):
                cv.set(x + k, y, MD[3])
    # hook over the rail at the top
    cv.set(xt + 1, yt - 1, MD[4])
    cv.set(xt + wd + 1, yt - 1, MD[4])


def cage(cv, cx, top, w, h, seed):
    """Hanging bell-shaped iron cage stuffed with books."""
    rnd = random.Random(seed)
    for y in range(top, top + h):
        t = (y - top) / h
        hw = w / 2 * (0.35 + 0.65 * min(1.0, t * 3.2) ** 0.5)
        # books inside (lower 2/3)
        if t > 0.35:
            for x in range(int(cx - hw + 1), int(cx + hw)):
                c = BOOKM[(x // 2 + int(t * 5)) % len(BOOKM)] if rnd.random() < 0.9 else MD[0]
                cv.set(x, y, c)
        # bars
        for k in range(-3, 4):
            x = cx + hw * k / 3.3
            cv.set(x, y, MD[4] if k < 0 else MD[3])
    rect(cv, cx - w / 2, cx + w / 2, top + h, top + h + 2, MD[3])    # base ring
    rect(cv, cx - 3, cx + 3, top - 2, top, MD[4])                    # crown ring
    for y in range(top + h + 3, top + h + 7):                        # a dangling bookmark ribbon
        cv.set(cx + 4 + (y % 3 == 0), y, C("3a1420"))
    # a single candle glowing inside
    cv.set(cx - 1, top + int(h * 0.45), GOLD[2])
    cv.set(cx - 1, top + int(h * 0.45) - 1, GOLD[3])


def giant_tome(cv, cx, cy, w, h):
    """A colossal closed grimoire seen from the front: ridged spine on the left, cover with gilt
    corner guards and a violet sigil boss, page block on the right/bottom, bound by two chains."""
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    x1, y1 = x0 + w, y0 + h
    PG = [C("1e1a24"), C("2c2632"), C("3a3240")]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x < x0 + 6:                                   # rounded spine with raised bands
                k = x - x0
                c = [MD[3], MD[5], MD[5], MD[4], MD[3], MD[1]][k]
                if (y - y0) % 9 in (3, 4):
                    c = RIM_V if k in (1, 2) else MD[5]
            elif y >= y1 - 3 and x > x0 + 7:                 # page block (bottom)
                c = PG[(x + y) % 2] if y < y1 else MD[1]
            elif x >= x1 - 3 and y > y0 + 2:                 # page block (fore-edge)
                c = PG[1 + (y % 2)] if x < x1 else MD[1]
            else:
                c = MD[4] if y > y0 + 1 else MD[5]
                if x == x0 + 6:
                    c = MD[1]                                # hinge groove
            cv.set(x, y, c)
    # gilt corner guards
    for (qx, qy, sx, sy) in ((x0 + 7, y0, 1, 1), (x1 - 4, y0, -1, 1), (x0 + 7, y1 - 4, 1, -1), (x1 - 4, y1 - 4, -1, -1)):
        for i in range(5):
            cv.set(qx + sx * i, qy, RIM_G)
            cv.set(qx, qy + sy * i, RIM_G)
        cv.set(qx + sx, qy + sy, RIM_G)
    # sigil boss: ring + eye, glowing faint violet
    mx, my = (x0 + 6 + x1 - 3) / 2, (y0 + y1 - 3) / 2
    for a in range(0, 360, 6):
        cv.set(mx + 8 * math.cos(math.radians(a)), my + 7 * math.sin(math.radians(a)), VIO[1])
    for a in range(0, 360, 12):
        cv.set(mx + 4 * math.cos(math.radians(a)), my + 2 * math.sin(math.radians(a)), VIO[2])
    cv.set(mx, my, VIO[4])
    cv.set(mx - 1, my, VIO[3])
    cv.set(mx + 1, my, VIO[3])
    for dy in (-6, 6):
        cv.set(mx, my + dy, VIO[3])
    # two binding chains wrapped vertically around the book, padlocked at the fore-edge
    for bx in (x0 + 14, x1 - 12):
        for y in range(y0 - 1, y1 + 2):
            k = y % 4
            cv.set(bx, y, MD[5] if k < 2 else C("2a2436"))
            cv.set(bx + 1, y, MD[2] if k < 2 else MD[4])
    for y in range(int(my) - 1, int(my) + 5):
        for x in range(x1 - 1, x1 + 4):
            cv.set(x, y, RIM_G if (x, y) != (x1 + 1, int(my) + 2) else MD[0])
    return (x0, y0, x1, y1)


def build_archives_mid():
    cv = Canvas(W, H, wrap=True)
    # drifts of fallen books along the floor
    for x in range(W):
        top = 204 - 6 * tn(x, 0, 32, 1, 70) - 4 * tn(x, 0, 8, 1, 71)
        for y in range(int(top), H):
            cv.set(x, y, MD[1] if (y - int(top)) > 1 else MD[3])
        if h01(x // 3, 0, 72) < 0.18:                            # a few spines sticking up
            for y in range(int(top) - 3, int(top)):
                cv.set(x, y, MD[2])
    # iron bridge (behind the towers) with lamps hanging under it
    for x in range(60, 350):
        cv.set(x, 168, MD[3])
        cv.set(x, 169, MD[4])
        cv.set(x, 170, MD[2])
        cv.set(x, 160, MD[3])
        if x % 12 == 0:
            for y in range(161, 168):
                cv.set(x, y, MD[3])
        if x % 48 == 20:
            for y in range(171, 176):
                cv.set(x, y, MD[3])
            cv.set(x, 176, GOLD[2])
            cv.set(x, 177, GOLD[1])
    # shelf towers
    shelf_tower(cv, 16, 56, 46, 1)
    shelf_tower(cv, 336, 44, 76, 2)
    shelf_tower(cv, 482, 34, 100, 3)
    # rolling ladders
    ladder(cv, 90, 206, 74, 128)
    ladder(cv, 392, 206, 382, 124, 6)
    # chains & cages
    chain(cv, 122, 0, 52)
    cage(cv, 123, 54, 22, 30, 5)
    chain(cv, 176, 0, 92)
    cage(cv, 177, 94, 16, 22, 6)
    chain(cv, 98, 0, 40)
    # the giant chained tome, hung by chains from the dark between the towers
    x0, y0, x1, y1 = giant_tome(cv, 437, 138, 56, 44)
    chain(cv, 400, 0, y0 + 4, (x0 + 2 - 400) / (y0 + 4))
    chain(cv, 474, 0, y0 + 4, (x1 - 2 - 474) / (y0 + 4))
    chain(cv, 423, 0, y0, 0)
    chain(cv, 450, 0, y0, 0)
    # rim light: violet on top/left edges of silhouettes, candle-gold on a few right edges
    px = cv.img.load()
    body = set(MD)
    hits = []
    for y in range(1, H):
        for x in range(W):
            c = px[x, y]
            if c not in body:
                continue
            up, lf, rt = px[x, y - 1], px[(x - 1) % W, y], px[(x + 1) % W, y]
            if up[3] == 0:
                hits.append((x, y, RIM_V2 if h01(x, y, 3) < 0.5 else RIM_V))
            elif lf[3] == 0:
                hits.append((x, y, RIM_V))
            elif rt[3] == 0 and h01(x // 2, y // 3, 5) < 0.3 and y > 60:
                hits.append((x, y, RIM_G))
    for (x, y, c) in hits:
        px[x, y] = c
    return cv.img


BUILDERS = {"archives": (build_archives_far, build_archives_mid)}
