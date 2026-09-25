"""Props for the `archives` biome. Each returns (w, h, layers, frames, tags).

prop_lectern     32x32  loop(4)   carved black-oak reading stand, a chained grimoire lying open on it,
                                  its pages glowing; violet-gold glyphs lift off the page and fade
prop_shelfcage   32x48  idle(1)   hanging iron cage crammed with books (chain runs to the top edge)
prop_candelabra  16x32  loop(4)   standing iron candelabra, three tallow candles, flickering flames

Face right, bottom-anchored, horizontally centred. 1px K outline, light from upper-left.
"""
import math
from envlib import C, ramp, K, T, h01, clamp, blank
from env_props import Spr, flame
from archives_tiles import OAK, IRON, PARCH, GOLD, VIO, WAX, BOOKS, INK, CRIM

FLAME = [GOLD[1], GOLD[2], GOLD[3], GOLD[4], GOLD[5]]


# =========================================================================== lectern
def lectern():
    Wd, Hd = 32, 32
    frames = []
    for f in range(4):
        ph = f / 4
        s = Spr(Wd, Hd)
        # plinth
        s.rect(8, 29, 23, 31, OAK[2])
        s.rect(8, 29, 23, 29, OAK[5])
        s.rect(9, 30, 9, 30, OAK[4])
        s.rect(10, 27, 21, 28, OAK[3])
        s.rect(10, 27, 21, 27, OAK[5])
        # carved pedestal column with rings
        for y in range(17, 27):
            for x in range(13, 19):
                c = OAK[5] if x == 13 else OAK[4] if x < 16 else OAK[3] if x < 18 else OAK[2]
                if y in (19, 24):
                    c = OAK[6] if x < 16 else OAK[4]
                if y in (20, 25):
                    c = OAK[1]
                s.set(x, y, c)
        # slanted desk seen from the front-above: its top face is a trapezoid, front edge thick
        for y in range(12, 19):
            inset = (18 - y) // 3
            for x in range(4 + inset, 28 - inset):
                c = OAK[4] if y < 17 else OAK[5] if y == 17 else OAK[2]
                if x == 4 + inset:
                    c = OAK[6]
                elif x == 27 - inset:
                    c = OAK[2]
                s.set(x, y, c)
        # the open grimoire lying on it: cover rim, page-block edges, then the two page faces
        for x in range(6, 26):
            s.set(x, 16, BOOKS[0][1] if 6 < x < 25 else BOOKS[0][0])      # cover visible under the pages
            s.set(x, 15, PARCH[2] if x % 2 else PARCH[1])                  # stacked page edges
        s.set(15, 15, BOOKS[0][0])
        s.set(16, 15, BOOKS[0][0])
        for x in range(7, 25):
            g = abs(x + 0.5 - 16)                                          # distance from the gutter
            top = 9 + (1 if g < 2 else 0) + (1 if g > 7.5 else 0)
            lift = 0
            if x >= 21 and f in (1, 2):                                     # right leaf lifting in the draught
                lift = (x - 20) // 2 + (f == 2)
            for y in range(top - lift, 15):
                c = PARCH[4] if x < 16 else PARCH[3]
                if y == top - lift:
                    c = PARCH[5] if x < 16 else PARCH[4]
                if g < 1:
                    c = PARCH[0]                                           # the gutter
                elif g < 2:
                    c = PARCH[2]
                elif (y - top) % 2 == 1 and y < 15 and 2 < g < 8 and h01(x, y, 3) < 0.72 and lift == 0:
                    c = PARCH[1] if h01(x, y, 7) < 0.8 else PARCH[0]      # script (some glyphs glowing)
                s.set(x, y, c)
            if lift:
                s.set(x, 15 - 1, PARCH[2])                                 # the page below shows through
        # chain from the book's clasp down to a ring on the column
        for i, (x, y) in enumerate(((26, 14), (26, 15), (25, 17), (24, 19), (22, 21), (20, 22), (19, 23))):
            s.set(x, y, IRON[5] if i % 2 == 0 else IRON[3])
        s.outline()
        # glow on the page (no outline): gold core + violet haze above, pulsing
        pul = 0.5 + 0.5 * math.sin(ph * 2 * math.pi)
        for (x, y) in ((11, 11), (12, 11), (19, 11), (20, 12)):
            s.set(x, y, GOLD[4] if pul > 0.5 else GOLD[3])
        # glyphs rising from the page, drifting and fading over the loop
        for g in range(3):
            t = (ph + g / 3) % 1.0
            gx = 12 + g * 5 + math.sin((t + g) * 2 * math.pi) * 1.5
            gy = 8 - t * 8
            col = VIO[5] if t < 0.35 else VIO[4] if t < 0.7 else VIO[2]
            if g == 1:
                col = GOLD[4] if t < 0.5 else GOLD[2]
            s.set(gx, gy, col)
            if t < 0.6:                               # a two-pixel rune stroke
                s.set(gx + 1, gy + 1, VIO[3] if g != 1 else GOLD[3])
        frames.append({"ms": 140, "cels": {"Lectern": s.img}})
    return Wd, Hd, ["Lectern"], frames, [("loop", 0, 3)]


# =========================================================================== hanging shelf-cage
def shelfcage():
    Wd, Hd = 32, 48
    s = Spr(Wd, Hd)
    cx = 16
    # chain to the top edge
    for y in range(0, 9):
        k = y % 4
        if k in (0, 3):
            s.set(cx - 1, y, IRON[5] if k == 0 else IRON[3])
            s.set(cx, y, IRON[4] if k == 0 else IRON[2])
        else:
            s.set(cx - 1 + (y // 4) % 2, y, IRON[4])
    # hook ring + dome cap
    for (x, y, c) in ((cx - 2, 9, 5), (cx + 1, 9, 3), (cx - 2, 10, 4), (cx + 1, 10, 2), (cx - 1, 11, 3), (cx, 11, 2)):
        s.set(x, y, IRON[c])
    top, bot = 12, 43

    def hw(y):
        t = (y - top) / (bot - top)
        return 3 + 9.5 * min(1.0, t * 3.0) ** 0.55

    # books inside the cage (drawn first; bars go over them)
    books_y = [(41, 3, 0), (38, 3, 4), (35, 3, 3), (32, 3, 1)]
    for (yb, bh, bi) in books_y:
        w0 = int(hw(yb) - 2)
        off = (-1, 1, 0, -2)[bi % 4]
        for y in range(yb - bh + 1, yb + 1):
            for x in range(cx - w0 + off, cx + w0 + off):
                br = BOOKS[bi]
                c = br[2] if y == yb - bh + 1 else br[0] if y == yb else br[1]
                if x > cx + w0 + off - 3 and yb - bh + 1 < y < yb:
                    c = PARCH[3] if y % 2 else PARCH[2]               # page edges
                s.set(x, y, c)
        s.set(cx - w0 + off + 1, yb - bh + 2, GOLD[2])
    # upright books leaning on the top of the stack
    xs = cx - 8
    for i, (bw, bh, bi) in enumerate(((2, 9, 1), (2, 11, 0), (1, 8, 5), (2, 10, 2), (3, 7, 3), (2, 10, 4), (1, 9, 0))):
        br = BOOKS[bi]
        for dx in range(bw):
            for y in range(29 - bh, 29):
                s.set(xs + dx, y, br[2] if dx == 0 else br[1])
            s.set(xs + dx, 29 - bh + 2, GOLD[1] if i % 2 else br[0])
        xs += bw
    # a scroll poking out through the bars
    for x in range(cx + 9, cx + 15):
        s.set(x, 25, PARCH[4])
        s.set(x, 26, PARCH[2])
    s.set(cx + 15, 25, PARCH[3])
    s.set(cx + 15, 26, CRIM[1])                                       # red wax seal
    # bars (curved dome -> straight), lit on the left
    for k in range(-4, 5):
        for y in range(top, bot + 1):
            x = cx - 0.5 + hw(y) * k / 4.0
            c = IRON[5] if k < 0 else IRON[4] if k == 0 else IRON[3]
            if k == -4:
                c = IRON[6]
            s.set(x, y, c)
    # horizontal bands
    for yb in (18, 30):
        for x in range(int(cx - hw(yb)), int(cx + hw(yb)) + 1):
            s.set(x, yb, IRON[4] if x < cx else IRON[3])
    for x in range(int(cx - hw(bot)) - 1, int(cx + hw(bot)) + 2):
        s.set(x, bot + 1, IRON[4] if x < cx else IRON[2])
        s.set(x, bot + 2, IRON[2])
    s.set(cx - 1, bot + 3, IRON[3])
    s.set(cx, bot + 3, IRON[2])
    s.set(cx - 1, bot + 4, GOLD[2])                                   # little finial
    s.outline()
    return Wd, Hd, ["Cage"], [{"ms": 200, "cels": {"Cage": s.img}}], [("idle", 0, 0)]


# =========================================================================== candelabra
def candelabra():
    Wd, Hd = 16, 32
    frames = []
    for f in range(4):
        s = Spr(Wd, Hd)
        # tripod feet
        for (x, y, c) in ((3, 31, 4), (4, 30, 4), (5, 30, 3), (12, 31, 3), (11, 30, 3), (10, 30, 2),
                          (6, 29, 4), (7, 29, 4), (8, 29, 3), (9, 29, 2)):
            s.set(x, y, IRON[c])
        # stem with knops
        for y in range(14, 29):
            s.set(7, y, IRON[5] if y % 5 else IRON[6])
            s.set(8, y, IRON[3])
            if y in (18, 24):
                s.set(6, y, IRON[5])
                s.set(9, y, IRON[2])
        # arms curving up to the outer cups
        for (x, y) in ((6, 15), (5, 15), (4, 14), (3, 13), (3, 12)):
            s.set(x, y, IRON[5])
        for (x, y) in ((9, 15), (10, 15), (11, 14), (12, 13), (12, 12)):
            s.set(x, y, IRON[3])
        # drip cups
        for (cx, cy) in ((3, 11), (12, 11), (7, 9)):
            s.set(cx - 1, cy, IRON[5])
            s.set(cx, cy, IRON[4])
            s.set(cx + 1, cy, IRON[3])
            if cx == 7:
                s.set(cx + 2, cy, IRON[3])
                s.rect(7, 10, 8, 13, IRON[4])
        # candles
        for (cx, top, bot) in ((3, 6, 10), (12, 7, 10), (7, 3, 8)):
            w2 = 2 if cx == 7 else 1
            for y in range(top, bot + 1):
                for dx in range(w2):
                    s.set(cx + dx, y, WAX[3] if dx == 0 and y == top else WAX[2] if dx == 0 else WAX[1])
            s.set(cx + w2, top + 2, WAX[2])                           # wax drip over the rim
            s.set(cx + w2, top + 3, WAX[1])
        s.outline()
        for (cx, top, sd) in ((3.5, 6, 1), (12.5, 7, 2), (8.0, 3, 0)):
            flame(s, cx, top - 1, 4 + (1 if (f + sd) % 2 else 0), 1.3, f / 4 + sd * 0.3, pal=FLAME, seed=sd)
        frames.append({"ms": 120, "cels": {"Candelabra": s.img}})
    return Wd, Hd, ["Candelabra"], frames, [("loop", 0, 3)]


PROPS = {"prop_lectern": lectern, "prop_shelfcage": shelfcage, "prop_candelabra": candelabra}
