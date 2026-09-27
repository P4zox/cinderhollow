"""Expansion 3 · agent RA: decor for the Ashen Ramparts, Rootbound Catacombs and Sunken Cathedral.

  xra_deco   64x64 props (bottom-centre anchored unless noted), one tag per prop (animated ones loop)
  xra_tall   32x96 stained-glass lancets and skull pillars
  xra_rose   160x160 the great rose window (K11) + its unlit frame
  xra_pano   512x160 the Hallow seen from the Watcher's Perch (R11): a painted parallax band, 2 layers
  xra_icons  16x16 the trial charm icon (c_x3_chime)

Run: python3 art/gen_xra.py  (needs Aseprite via asebuild)
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline, vnoise
from env_props import STONE, WARM, GOLD, IRON, WOOD, CRIM, flame
import asebuild

# ---------------------------------------------------------------- palettes
RSTONE = ramp("1c1822", "2c2634", "3e3648", "544a5e", "6e6478", "8e8496", "b2a8b6")      # rampart stone (violet grey)
BONE = ramp("241e1a", "3c322a", "5a4c3e", "7e6c56", "a48e72", "c8b494", "e6dcc2")
CSTONE = ramp("16182a", "242840", "343a56", "4a526e", "66708c", "8c96ae", "bcc4d6")     # cathedral stone (blue grey)
DWOOD = ramp("140e0c", "261a14", "3a281c", "523826", "6e4c32", "8e6840")
HAY = ramp("3a2a14", "5e4420", "86642e", "ae8a42", "d0b060", "ecd490")
CLOTH = ramp("1e0a10", "3a1018", "5e1822", "86242e", "b0343a", "d25a52")
BLUE = ramp("0c1430", "18285a", "28448c", "3e68b8", "6c9adc", "b4d4f4")
ROOT = ramp("1a120c", "2e2014", "4a3420", "6a4c2c", "8e6a3c", "b48e54")
GREEN = ramp("0e1a12", "1a3222", "2a5034", "3e7248", "5e9a62")
WAX = ramp("6a5a44", "a89070", "d8c8a0", "f4ecd0")
FLAME = ramp("7a2a0a", "c05010", "f08a20", "ffc050", "fff0b0", "ffffff")
GLASS = {'gold': ramp("3a2408", "7a4c10", "c0801c", "f0b840", "ffe08a", "fff6d0"),
         'rose': ramp("300818", "6a1030", "a82048", "e04a6a", "ff8aa0", "ffd6de"),
         'blue': ramp("0a1238", "142a70", "2248b0", "3a74e0", "7ab0ff", "d0e6ff"),
         'green': ramp("08200e", "103e1c", "1e6a30", "38a04a", "7ad088", "d0f4d8")}


# ---------------------------------------------------------------- a tiny part-based renderer: shapes get lit from the upper left
class Fig:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.pix = {}        # (x,y) -> (ramp, base, part)
        s.over = {}       # explicit colours drawn after shading
        s.n = 0

    def _part(s):
        s.n += 1
        return s.n

    def cell(s, x, y, R, base, part):
        if 0 <= x < s.w and 0 <= y < s.h:
            s.pix[(int(x), int(y))] = (R, base, part)

    def box(s, x0, y0, x1, y1, R, base=3, part=None):
        p = part or s._part()
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                s.cell(x, y, R, base, p)
        return p

    def ell(s, cx, cy, rx, ry, R, base=3, part=None):
        p = part or s._part()
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / max(rx, 0.1)) ** 2 + ((y + 0.5 - cy) / max(ry, 0.1)) ** 2 <= 1:
                    s.cell(x, y, R, base, p)
        return p

    def poly(s, pts, R, base=3, part=None):
        p = part or s._part()
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                if _inside(x + 0.5, y + 0.5, pts):
                    s.cell(x, y, R, base, p)
        return p

    def line(s, x0, y0, x1, y1, R, base=3, part=None, th=1):
        p = part or s._part()
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for k in range(th):
                s.cell(round(x) + (k if abs(y1 - y0) > abs(x1 - x0) else 0), round(y) + (0 if abs(y1 - y0) > abs(x1 - x0) else k), R, base, p)
        return p

    def px(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h:
            s.over[(int(x), int(y))] = c

    def hline(s, x0, x1, y, c):
        for x in range(int(x0), int(x1) + 1): s.px(x, y, c)

    def vline(s, x, y0, y1, c):
        for y in range(int(y0), int(y1) + 1): s.px(x, y, c)

    def erase(s, x, y):
        s.pix.pop((int(x), int(y)), None); s.over.pop((int(x), int(y)), None)

    def render(s, ol=True, tex=0.0, seed=0, lightx=-1):
        img = blank(s.w, s.h); P = img.load()
        for (x, y), (R, base, part) in s.pix.items():
            same = lambda dx, dy: s.pix.get((x + dx, y + dy), (None, 0, -1))[2] == part
            i = base
            if not same(0, -1): i += 1
            if not same(lightx, 0): i += 1
            if not same(-lightx, 0): i -= 1
            if not same(0, 1): i -= 1
            if tex:
                v = h01(x, y, seed) - 0.5
                if abs(v) * tex > bt(x, y) * 0.5: i += 1 if v > 0 else -1
            P[x, y] = R[max(0, min(len(R) - 1, i))]
        for (x, y), c in s.over.items():
            P[x, y] = c
        return outline(img, K) if ol else img


def _inside(x, y, pts):
    c = False; n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-9) + x0:
            c = not c
    return c


def frame(w, h, img, ax='bottom'):
    """place a prop image in a w x h cel: bottom-centred (default) or top-centred ('top')."""
    out = blank(w, h)
    ox = (w - img.size[0]) // 2
    oy = h - img.size[1] if ax == 'bottom' else 0
    out.alpha_composite(img, (ox, oy))
    return out


def candle(f, x, y, ph, h=3):
    f.box(x, y - h, x, y, WAX, 2)
    fl = FLAME[4] if (ph + x) % 3 else FLAME[3]
    f.px(x, y - h - 1, fl); f.px(x, y - h - 2, FLAME[3] if (ph + x) % 2 else FLAME[2])


# ================================================================= RAMPARTS
def banner_wall(ph):
    """a tattered war banner hanging from an iron rod (top-anchored)"""
    f = Fig(22, 48)
    f.box(0, 0, 21, 1, IRON, 3)
    f.px(0, 0, IRON[4]); f.px(21, 1, IRON[1])
    sway = [0, 1, 1, 0][ph]
    for y in range(2, 44):
        t = (y - 2) / 42
        dx = round(math.sin(ph * math.pi / 2 + t * 3) * t * 1.5) + (sway if y > 30 else 0)
        x0, x1 = 3 + dx, 18 + dx
        for x in range(x0, x1 + 1):
            if y > 36 and ((x - x0) % 5 in (0, 1)) and y > 36 + ((x * 7) % 5): continue   # torn tail
            f.cell(x, y, CLOTH, 3 if (x - x0) > 3 else 4, 1)
    # the sigil: a pale ashen tree
    cx = 11
    for y in range(12, 30):
        dx = round(math.sin(ph * math.pi / 2 + (y - 2) / 42 * 3) * (y - 2) / 42 * 1.5)
        f.px(cx + dx, y, GOLD[2] if y < 26 else GOLD[1])
        if y in (15, 19, 23):
            for k in range(1, 5 - (y - 15) // 4):
                f.px(cx + dx - k, y - k, GOLD[1]); f.px(cx + dx + k, y - k, GOLD[1])
    f.hline(4, 17, 6, GOLD[1])
    return f.render()


def banner_pole(ph):
    f = Fig(28, 64)
    f.box(12, 4, 13, 63, WOOD, 2)
    f.px(12, 3, GOLD[3]); f.px(13, 3, GOLD[2]); f.px(12, 2, GOLD[3])
    for y in range(6, 34):
        t = (y - 6) / 28
        wave = math.sin(ph * math.pi / 2 + t * 4) * 1.2
        for x in range(14, 27):
            u = (x - 14) / 12
            yy = y + round(math.sin(ph * math.pi / 2 + u * 5) * 1.5 * u)
            if u > 0.75 and (yy + x) % 6 < 2 and t > 0.6: continue
            f.cell(x, yy, CLOTH, 3 if u < 0.7 else 2, 1)
    for y in range(12, 24):
        f.px(20 + round(math.sin(ph * math.pi / 2 + 0.5 * 5) * 0.7), y, GOLD[2])
    f.hline(18, 22, 16, GOLD[1])
    return f.render()


def hay():
    f = Fig(44, 26)
    for (x0, y0, x1, y1) in [(0, 12, 20, 25), (19, 12, 40, 25), (9, 1, 30, 13)]:
        p = f.box(x0, y0, x1, y1, HAY, 3)
        for x in range(x0 + 2, x1, 3):
            for y in range(y0 + 1, y1):
                if h01(x, y, 3) < 0.35: f.px(x, y, HAY[2])
        f.vline(x0 + (x1 - x0) // 3, y0, y1, HAY[1]); f.vline(x0 + 2 * (x1 - x0) // 3, y0, y1, HAY[1])
    for i in range(10):
        x = int(h01(i, 1, 9) * 44); f.px(x, 25 - int(h01(i, 2, 9) * 2), HAY[4])
    f.line(38, 25, 43, 18, HAY, 4)
    return f.render()


def rack():
    f = Fig(34, 40)
    f.box(2, 10, 3, 39, WOOD, 2); f.box(30, 10, 31, 39, WOOD, 2)
    f.box(0, 8, 33, 10, WOOD, 3); f.box(0, 30, 33, 31, WOOD, 2)
    for i, x in enumerate([7, 12, 17, 22, 27]):
        if i == 3:
            f.box(x, 12, x + 1, 38, IRON, 4); f.box(x - 2, 30, x + 3, 30, GOLD, 1)     # sword
        else:
            f.box(x, 1, x, 38, WOOD, 3)
            f.poly([(x - 1, 6), (x, 0), (x + 2, 6)], IRON, 4)                           # spear heads
    f.ell(9, 34, 5, 5, IRON, 2)
    f.px(9, 34, GOLD[2])
    return f.render()


def bunk():
    f = Fig(44, 36)
    for x in (1, 42):
        f.box(x - 1, 2, x, 35, WOOD, 2)
    for y in (14, 30):
        f.box(0, y, 43, y + 2, WOOD, 3)
        f.box(3, y - 3, 40, y - 1, CLOTH, 2)             # blanket
        f.ell(8, y - 3, 4, 2, BONE, 4)                   # straw pillow
    f.box(0, 1, 43, 2, WOOD, 3)
    f.line(30, 27, 38, 21, BONE, 3)                      # a dropped arm bone
    return f.render()


def barrels():
    f = Fig(46, 30)
    def barrel(x, y, w, h):
        p = f.box(x, y, x + w, y + h, WOOD, 3)
        for yy in (y + 2, y + h - 2):
            f.hline(x, x + w, yy, IRON[2])
        f.vline(x + w // 2, y, y + h, WOOD[2])
    barrel(1, 12, 12, 17); barrel(14, 10, 12, 19)
    p = f.box(28, 16, 44, 29, WOOD, 2)
    f.line(28, 16, 44, 29, WOOD, 1, p); f.line(44, 16, 28, 29, WOOD, 1, p)
    f.box(30, 5, 42, 15, WOOD, 3)
    f.hline(30, 42, 10, WOOD[1])
    return f.render()


def horse():
    """a horse's bones where it fell in its stall"""
    f = Fig(56, 22)
    f.ell(11, 11, 6, 4, BONE, 4)                     # skull
    f.poly([(4, 9), (0, 12), (1, 14), (8, 13)], BONE, 4)
    f.px(10, 10, K); f.px(11, 10, K)
    for i in range(12):                             # spine
        f.box(16 + i * 2, 13 - int(math.sin(i / 11 * math.pi) * 3), 17 + i * 2, 14 - int(math.sin(i / 11 * math.pi) * 3), BONE, 3)
    for i in range(7):                              # ribs
        x = 22 + i * 3
        for k in range(8):
            f.cell(x + k // 3, 12 + k, BONE, 4 - k // 4, 100 + i)
    f.ell(44, 15, 6, 4, BONE, 3)                    # pelvis
    for (a, b) in [((40, 17), (35, 21)), ((47, 17), (54, 21)), ((20, 16), (15, 21)), ((26, 18), (29, 21))]:
        f.line(a[0], a[1], b[0], b[1], BONE, 3)
    f.hline(0, 55, 21, HAY[1])
    for x in range(0, 56, 3): f.px(x, 20, HAY[2] if x % 2 else HAY[3])
    return f.render()


def cart():
    f = Fig(56, 32)
    f.poly([(4, 10), (46, 14), (46, 20), (4, 18)], WOOD, 3)
    for x in range(8, 46, 6): f.px(x, 16, WOOD[1])
    f.line(46, 17, 55, 26, WOOD, 2, th=2)
    wheel = lambda cx, cy, r: [f.ell(cx, cy, r, r, WOOD, 2)]
    f.ell(14, 23, 8, 8, DWOOD, 3)
    f.ell(14, 23, 5, 5, DWOOD, 1)
    for a in range(0, 360, 45):
        f.line(14, 23, 14 + math.cos(math.radians(a)) * 7, 23 + math.sin(math.radians(a)) * 7, DWOOD, 4)
    f.ell(38, 28, 7, 4, DWOOD, 2)                    # the broken wheel lies flat
    f.box(20, 4, 30, 10, HAY, 3)
    return f.render()


def beacon(ph):
    """the great signal beacon: an iron fire-basket on a tripod"""
    f = Fig(40, 60)
    for (a, b) in [((20, 36), (8, 59)), ((20, 36), (32, 59)), ((20, 36), (20, 59))]:
        f.line(a[0], a[1], b[0], b[1], IRON, 3, th=2)
    f.poly([(4, 24), (36, 24), (30, 36), (10, 36)], IRON, 3)
    for x in range(6, 35, 4): f.vline(x, 25, 34, IRON[1])
    f.hline(4, 36, 24, IRON[4])
    img = f.render()
    s = Fig(40, 60)
    base = FLAME
    fl = blank(40, 60)
    from env_props import Spr
    sp = Spr(40, 60)
    flame(sp, 20, 24, 20, 12, ph / 4, FLAME, 1)
    flame(sp, 13, 24, 12, 6, (ph / 4 + 0.3) % 1, FLAME, 2)
    flame(sp, 27, 24, 13, 6, (ph / 4 + 0.6) % 1, FLAME, 3)
    img.alpha_composite(sp.img)
    return img


def winch():
    f = Fig(40, 40)
    f.box(2, 8, 5, 39, WOOD, 2); f.box(34, 8, 37, 39, WOOD, 2)
    f.box(0, 36, 39, 39, RSTONE, 3)
    p = f.box(6, 14, 33, 28, DWOOD, 3)
    for y in range(15, 28, 2): f.hline(6, 33, y, IRON[2] if y % 4 == 1 else IRON[3])   # coiled chain
    f.ell(4, 21, 4, 4, IRON, 3)
    for a in range(0, 360, 60):                     # the capstan spokes
        f.line(4, 21, 4 + math.cos(math.radians(a)) * 9, 21 + math.sin(math.radians(a)) * 9, WOOD, 4)
    f.box(18, 0, 20, 14, IRON, 2)
    return f.render()


def dummy():
    f = Fig(24, 40)
    f.box(11, 14, 12, 39, WOOD, 2)
    f.box(3, 16, 20, 17, WOOD, 3)
    f.ell(11.5, 24, 6, 8, HAY, 3)
    f.ell(11.5, 10, 4.5, 5, HAY, 4)
    f.hline(6, 17, 24, CLOTH[3]); f.hline(7, 16, 25, CLOTH[2])
    for (x, y) in [(10, 22), (14, 27)]: f.px(x, y, IRON[3])
    f.line(15, 20, 21, 12, WOOD, 4)                 # an arrow stuck in it
    f.px(21, 12, IRON[4])
    return f.render()


def stall():
    """a stable stall partition (back decor)"""
    f = Fig(52, 44)
    f.box(0, 4, 3, 43, DWOOD, 2); f.box(48, 4, 51, 43, DWOOD, 2)
    for y in range(18, 44, 5): f.box(4, y, 47, y + 3, DWOOD, 2)
    f.box(0, 2, 51, 4, DWOOD, 3)
    f.box(20, 8, 31, 14, DWOOD, 1)                  # manger
    for x in range(21, 31, 2): f.px(x, 8, HAY[3])
    f.line(8, 22, 18, 12, IRON, 3)                   # a hanging bridle
    return f.render(tex=0.4)


def crenel():
    """a stretch of parapet with merlons, seen behind the walk (back decor, tiles 4 wide)"""
    f = Fig(64, 30)
    f.box(0, 14, 63, 29, RSTONE, 2)
    for x0 in (0, 16, 32, 48):
        f.box(x0 + 2, 2, x0 + 11, 13, RSTONE, 2, part=f._part())
        f.px(x0 + 6, 7, K); f.px(x0 + 6, 8, K); f.px(x0 + 6, 9, K)       # arrow slit
    for y in range(17, 29, 4):
        for x in range((y // 4 % 2) * 4, 64, 8): f.vline(x, y, y + 3, RSTONE[1])
        f.hline(0, 63, y, RSTONE[1])
    for x in (6, 30, 51): f.px(x, 12, GREEN[2]); f.px(x + 1, 13, GREEN[3])
    return f.render(ol=False, tex=0.6, seed=4)


def trebuchet():
    """a burnt siege engine left on the wall: the Long Wall's far landmark (back decor)"""
    f = Fig(64, 64)
    f.poly([(6, 63), (28, 18), (33, 18), (14, 63)], DWOOD, 2)
    f.poly([(58, 63), (36, 18), (31, 18), (50, 63)], DWOOD, 2)
    f.box(2, 58, 61, 63, DWOOD, 2)
    f.box(26, 16, 37, 20, IRON, 2)
    f.line(8, 2, 55, 38, DWOOD, 3, th=3)            # the throwing arm, snapped
    f.box(49, 36, 60, 47, IRON, 2)                  # counterweight
    f.line(8, 2, 3, 12, IRON, 2)                    # sling chain
    for y in range(40, 58, 5): f.hline(18, 46, y, DWOOD[1])
    return f.render(tex=0.3)


def rubble():
    f = Fig(34, 14)
    for (cx, cy, rx, ry) in [(8, 10, 7, 4), (19, 9, 8, 5), (28, 11, 5, 3), (14, 6, 4, 3)]:
        f.ell(cx, cy, rx, ry, RSTONE, 3)
    f.box(0, 12, 33, 13, RSTONE, 2)
    f.line(22, 5, 30, 2, WOOD, 3)
    return f.render(tex=0.5)


def flag(ph):
    f = Fig(40, 56)
    f.box(5, 2, 6, 55, IRON, 3)
    f.px(5, 1, GOLD[3])
    for y in range(4, 22):
        for x in range(7, 38):
            u = (x - 7) / 30
            yy = y + round(math.sin(ph * math.pi / 2 + u * 6) * 2.2 * u)
            if u > 0.8 and (yy + x + ph) % 5 < 2: continue
            f.cell(x, yy, CLOTH, 3 if (y - 4) < 12 else 2, 1)
    return f.render()


def torch(ph):
    """a wall sconce with a burning torch (centred in its cell, drawn on the wall)"""
    from env_props import Spr
    f = Fig(20, 36)
    f.box(8, 20, 11, 22, IRON, 3); f.box(9, 23, 10, 30, IRON, 2); f.box(7, 30, 12, 31, IRON, 3)     # bracket
    f.box(8, 13, 11, 20, WOOD, 3)
    f.hline(7, 12, 14, IRON[2]); f.hline(7, 12, 18, IRON[2])
    img = f.render()
    sp = Spr(20, 36)
    flame(sp, 9.5, 13, 10, 4, ph / 4, FLAME, 2)
    img.alpha_composite(sp.img)
    return img


def slit():
    """an arrow slit: a sliver of night sky in the wall"""
    f = Fig(14, 34)
    f.box(0, 4, 13, 33, RSTONE, 3)
    f.ell(6.5, 5, 6.5, 5, RSTONE, 3, part=1)
    img = f.render(tex=0.4, seed=12)
    P = img.load()
    for y in range(4, 30):
        for x in range(5, 9):
            if y < 7 and (x - 6.5) ** 2 + (y - 7) ** 2 > 5: continue
            v = y / 30
            P[x, y] = (int(40 + 60 * v), int(36 + 30 * v), int(70 + 40 * v), 255)
    P[6, 12] = (230, 230, 255, 255); P[7, 20] = (180, 180, 230, 255)
    for x in range(4, 10): P[x, 30] = RSTONE[5]
    return img


def shields():
    """crossed spears behind a battered kite shield, hung on the wall"""
    f = Fig(36, 36)
    f.line(3, 3, 32, 32, WOOD, 3); f.line(32, 3, 3, 32, WOOD, 3)
    for (x, y) in [(3, 3), (32, 3)]: f.poly([(x - 2, y + 3), (x, y - 2), (x + 2, y + 3)], IRON, 4)
    f.poly([(9, 8), (27, 8), (27, 20), (18, 32), (9, 20)], CLOTH, 3)
    f.poly([(12, 11), (24, 11), (24, 19), (18, 27), (12, 19)], CLOTH, 2)
    f.vline(18, 10, 28, GOLD[2]); f.hline(11, 25, 15, GOLD[2])
    f.px(22, 13, K); f.px(23, 14, K); f.px(14, 22, K)
    return f.render()


# ================================================================= CATACOMBS
def bshelf():
    """a wall of burial niches, skulls looking out (back decor)"""
    f = Fig(64, 52)
    f.box(0, 0, 63, 51, BONE, 1)
    for row, y in enumerate((3, 20, 37)):
        for i, x in enumerate(range(3 - (row % 2) * 7, 64, 14)):
            f.box(x, y, x + 10, y + 12, BONE, 0, part=f._part())
            f.ell(x + 5.5, y + 12 - 5 - (h01(i, row, 5) > 0.5), 3.4, 3.2, BONE, 4, part=f._part())
            f.px(x + 4, y + 7, K); f.px(x + 7, y + 7, K)
            if h01(i, row, 7) > 0.6: f.line(x + 1, y + 12, x + 9, y + 11, BONE, 4)
        f.hline(0, 63, y + 13, BONE[3])
    return f.render(ol=False, tex=0.5, seed=2)


def coffin():
    f = Fig(22, 44)
    f.poly([(6, 0), (15, 0), (21, 12), (17, 43), (4, 43), (0, 12)], DWOOD, 3)
    f.poly([(8, 3), (13, 3), (18, 13), (15, 40), (6, 40), (3, 13)], DWOOD, 2)
    f.box(10, 8, 11, 26, BONE, 3); f.box(6, 14, 15, 15, BONE, 3)          # the carved root-cross
    for (x, y) in [(3, 13), (18, 13), (5, 40), (15, 40)]: f.px(x, y, IRON[3])
    return f.render()


def sarc():
    f = Fig(52, 26)
    f.box(0, 14, 51, 25, BONE, 2)
    for x in range(4, 50, 8): f.box(x, 17, x + 4, 23, BONE, 1, part=f._part())
    f.box(1, 10, 50, 13, BONE, 3)
    f.ell(9, 7, 4, 3.5, BONE, 4)                        # effigy head
    f.poly([(12, 5), (44, 6), (47, 10), (12, 10)], BONE, 3)
    f.box(26, 3, 28, 7, BONE, 4); f.box(24, 4, 30, 4, BONE, 4)        # hands on a sword hilt
    f.line(29, 6, 44, 6, IRON, 4)
    return f.render(tex=0.4)


def skulls():
    f = Fig(36, 18)
    for i, (cx, cy) in enumerate([(5, 14), (12, 14), (19, 14), (26, 14), (32, 15), (9, 9), (16, 9), (23, 9), (13, 4), (29, 10)]):
        f.ell(cx, cy, 3.4, 3.1, BONE, 4 if i % 3 else 3)
        f.px(cx - 1, cy, K); f.px(cx + 1, cy, K)
        f.px(cx, cy + 2, BONE[1])
    f.line(0, 17, 35, 17, BONE, 2)
    return f.render()


def rootc(ph):
    """a curtain of roots hanging through the vault (top-anchored)"""
    f = Fig(40, 56)
    f.box(0, 0, 39, 2, ROOT, 3)
    for i in range(9):
        x0 = 2 + i * 4.3 + h01(i, 0, 1) * 2
        L = 18 + h01(i, 1, 1) * 34
        sw = math.sin(ph * math.pi / 2 + i) * 1.2
        th = 2 if h01(i, 2, 1) > 0.4 else 1
        prev = None
        for y in range(2, int(L)):
            t = y / L
            x = x0 + math.sin(y * 0.25 + i) * 1.2 + sw * t * t
            for k in range(th if t < 0.7 else 1):
                f.cell(round(x) + k, y, ROOT, 3 if k == 0 else 2, 10 + i)
            if y > 8 and h01(i, y, 3) > 0.93:
                f.line(round(x), y, round(x) + (3 if i % 2 else -3), y + 5, ROOT, 2)
    return f.render()


def tomb(n):
    """a carved tomb slab: a lantern and its roman numeral (the Crypt of Lanterns' clue)"""
    f = Fig(28, 38)
    f.poly([(2, 6), (8, 1), (19, 1), (25, 6), (25, 37), (2, 37)], BONE, 3)
    f.box(5, 8, 22, 34, BONE, 2, part=f._part())
    # the lantern carving
    f.box(11, 12, 16, 20, BONE, 1, part=f._part())
    f.hline(10, 17, 11, BONE[4]); f.hline(10, 17, 21, BONE[4]); f.vline(13, 9, 10, BONE[4])
    for y in range(14, 19): f.px(13 if y % 2 else 14, y, GOLD[3] if y < 17 else GOLD[2])
    # numeral, inlaid in gold
    glyphs = {1: ['I'], 2: ['I', 'I'], 3: ['I', 'I', 'I'], 4: ['I', 'V']}[n]
    x = 14 - (len(glyphs) * 4 - 2) // 2
    for gph in glyphs:
        if gph == 'I':
            f.vline(x, 25, 31, GOLD[3]); f.px(x + 1, 25, GOLD[2]); f.px(x - 1, 25, GOLD[2]); f.px(x + 1, 31, GOLD[2]); f.px(x - 1, 31, GOLD[2]); x += 4
        else:
            for k in range(7): f.px(x - 2 + (k * 2 // 6), 25 + k, GOLD[3]); f.px(x + 2 - (k * 2 // 6), 25 + k, GOLD[3])
            x += 6
    return f.render(tex=0.35, seed=n)


def bonechand(ph):
    """a chandelier of bones and candles (top-anchored)"""
    f = Fig(40, 34)
    f.vline(19, 0, 10, IRON[3]); f.vline(20, 0, 10, IRON[2])
    f.ell(19.5, 14, 4, 4, BONE, 4)
    f.px(18, 14, K); f.px(21, 14, K)
    f.poly([(2, 20), (38, 20), (34, 24), (6, 24)], BONE, 3)
    for x in range(4, 37, 3): f.px(x, 22, BONE[1])
    for (a, b) in [((19, 10), (4, 20)), ((20, 10), (35, 20))]:
        f.line(a[0], a[1], b[0], b[1], BONE, 4)
    for i, x in enumerate(range(6, 36, 6)):
        f.vline(x, 25, 28 + (i % 2) * 3, BONE[2])
    for x in (5, 12, 19, 27, 34):
        candle(f, x, 19, ph, 2)
    return f.render()


def digger():
    f = Fig(36, 34)
    f.line(4, 0, 12, 33, WOOD, 3, th=2)
    f.poly([(11, 26), (17, 28), (15, 33), (9, 33)], IRON, 4)                # the spade in the dirt
    f.ell(24, 26, 9, 7, HAY, 2)                      # a sack of lime
    f.hline(19, 29, 21, HAY[4])
    f.box(29, 23, 34, 32, IRON, 2)                   # his lantern, dark
    f.box(30, 25, 33, 30, IRON, 1, part=f._part())
    f.ell(18, 32, 16, 2, ROOT, 2)                    # turned earth
    return f.render()


def skullpillar():
    f = Fig(26, 90)
    f.box(2, 82, 23, 89, BONE, 3); f.box(4, 0, 21, 3, BONE, 3)
    for r, y in enumerate(range(5, 82, 7)):
        for i, x in enumerate(range(6 + (r % 2) * 3, 22, 6)):
            f.ell(x, y + 3, 3.2, 3.2, BONE, 4 if (i + r) % 3 else 3, part=f._part())
            f.px(x - 1, y + 3, K); f.px(x + 1, y + 3, K)
    for y in range(4, 82): f.px(3, y, BONE[1]); f.px(22, y, BONE[0])
    return f.render()


def rootheart():
    """the Ossuary's landmark: a root as thick as a tower, split around a heart of amber sap (top-anchored)"""
    Wd, Hd = 96, 128
    f = Fig(Wd, Hd)
    body = f._part()
    for y in range(0, 110):
        t = y / 110
        hw = 22 - 8 * math.sin(min(1, t * 1.3) * math.pi / 2) + (t - 0.8) * 60 * (t > 0.8)
        c = 48 + math.sin(y * 0.05) * 3
        for x in range(int(c - hw), int(c + hw) + 1):
            f.cell(x, y, ROOT, 3, body)
    for (a, L, y0) in [(3.4, 40, 100), (-0.25, 40, 100), (2.9, 26, 106), (0.2, 28, 106)]:   # roots splaying at the foot
        for k in range(L):
            x = 48 + math.cos(a) * k * 1.2; y = y0 + k * 0.45 + math.sin(k * 0.4)
            for d in range(3 - k * 2 // L):
                f.cell(round(x), round(y) + d, ROOT, 3, body)
    img = f.render(tex=0.4, seed=8)
    P = img.load()
    for x in range(Wd):                                  # bark grooves running down the trunk
        for y in range(Hd):
            if P[x, y][3] and P[x, y] != K and (x * 7 + int(math.sin(y * 0.09 + x) * 3)) % 9 == 0: P[x, y] = ROOT[1]
    for y in range(40, 84):                              # the split, and the heart of sap inside it
        for x in range(30, 66):
            d = ((x + 0.5 - 48.5) / 9) ** 2 + ((y + 0.5 - 62) / 21) ** 2
            if d < 1 and P[x, y][3]:
                v = 1 - d
                if v < 0.18: P[x, y] = K
                elif v < 0.35: P[x, y] = ROOT[0]
                else: P[x, y] = (255, int(140 + 100 * v), int(50 + 110 * v), 255) if bt(x, y) < v * 1.7 else (200, 100, 40, 255)
    for y in range(4, 108, 3):                           # amber veins bleeding from the split
        for side in (-1, 1):
            x = 48 + side * (6 + (abs(y - 62) * 0.25)) + math.sin(y * 0.3) * 2
            if P[int(x), y][3] and abs(y - 62) < 44 and (y // 3) % 3: P[int(x), y] = (230, 140, 60, 255)
    return img


# ================================================================= CATHEDRAL
def kneel():
    """a pilgrim statue, kneeling on one knee, hood bowed, hands pressed together (stone)"""
    f = Fig(30, 42)
    f.box(1, 36, 28, 41, CSTONE, 3)                                          # plinth
    f.hline(2, 27, 38, CSTONE[2])
    f.poly([(5, 35), (7, 20), (12, 14), (17, 15), (19, 24), (17, 35)], CSTONE, 3)     # robe over the back and the kneeling leg
    f.poly([(15, 28), (24, 28), (25, 35), (15, 35)], CSTONE, 3)             # the forward knee and shin
    f.ell(15, 11, 5, 5.5, CSTONE, 4)                                        # hood
    f.poly([(16, 8), (21, 12), (19, 17), (15, 14)], CSTONE, 4)              # hood lip, bowed forward
    f.px(18, 12, CSTONE[0]); f.px(18, 13, CSTONE[0]); f.px(17, 13, CSTONE[1])        # shadow of the face
    f.poly([(16, 18), (22, 15), (24, 17), (18, 22)], CSTONE, 4)             # forearms raised
    f.poly([(22, 11), (24, 10), (25, 16), (23, 17)], CSTONE, 5)             # hands pressed together
    for y in range(20, 35, 3): f.px(9 + (y % 2), y, CSTONE[2]); f.px(13, y + 1, CSTONE[2])   # cloth folds
    f.line(6, 34, 16, 34, CSTONE, 2)
    return f.render(tex=0.35, seed=5)


def pew():
    f = Fig(52, 22)
    f.box(0, 2, 3, 21, DWOOD, 3); f.box(48, 2, 51, 21, DWOOD, 3)
    f.box(0, 12, 51, 14, DWOOD, 3)
    f.box(3, 2, 48, 9, DWOOD, 2)
    for x in range(8, 48, 8): f.vline(x, 3, 8, DWOOD[1])
    f.ell(1.5, 1.5, 2, 2, GOLD, 2); f.ell(49.5, 1.5, 2, 2, GOLD, 2)
    return f.render()


def booth(openf):
    f = Fig(50, 60)
    f.poly([(2, 12), (25, 0), (47, 12)], DWOOD, 3)
    f.box(0, 12, 49, 59, DWOOD, 3)
    f.box(4, 16, 45, 57, DWOOD, 1, part=f._part())
    f.ell(25, 5, 2, 2, GOLD, 3)
    f.box(23, 16, 26, 57, DWOOD, 3, part=f._part())            # centre post
    for x in (12, 37):                                          # carved grilles
        for y in range(20, 30, 2): f.hline(x - 3, x + 3, y, DWOOD[4])
    for side, x0 in ((0, 5), (1, 28)):
        if openf and side == 1:
            f.poly([(x0, 32), (x0 + 5, 32), (x0 + 3, 57), (x0, 57)], CLOTH, 3)      # curtain thrown back
            for y in range(34, 57, 3): f.px(x0 + 2, y, CLOTH[1])
        else:
            f.box(x0, 32, x0 + 16, 57, CLOTH, 2, part=f._part())
            for x in range(x0 + 2, x0 + 16, 3): f.vline(x, 33, 56, CLOTH[1])
    f.box(0, 58, 49, 59, DWOOD, 2)
    return f.render()


def organ():
    """the great organ's pipes (back decor landmark)"""
    f = Fig(64, 64)
    f.box(0, 44, 63, 63, DWOOD, 3)
    for x in range(4, 60, 8): f.box(x, 48, x + 5, 60, DWOOD, 1, part=f._part())
    hs = [30, 36, 42, 38, 44, 50, 44, 38, 42, 36, 30]
    for i, h in enumerate(hs):
        x = 3 + i * 5.3
        f.box(x, 44 - h, x + 3, 44, IRON if i % 2 else GOLD, 3 if i % 2 else 2, part=f._part())
        f.box(x, 44 - h + 4, x + 3, 44 - h + 5, K, 0, part=f._part())                # the mouth
        f.px(x + 1, 44 - h, (GOLD if i % 2 == 0 else IRON)[4])
    f.box(0, 43, 63, 44, GOLD, 2)
    return f.render()


def chand(ph):
    """a cathedral chandelier: an iron hoop of candles (top-anchored)"""
    f = Fig(48, 30)
    f.vline(23, 0, 12, IRON[3]); f.vline(24, 0, 12, IRON[2])
    f.ell(23.5, 20, 22, 5, IRON, 3)
    f.ell(23.5, 19, 19, 3, IRON, 1, part=None)
    for x0, y0 in ((23, 12), (24, 12)):
        f.line(x0, y0, 3, 19, IRON, 3); f.line(x0, y0, 44, 19, IRON, 3)
    f.ell(23.5, 26, 3, 3, GOLD, 3)
    img = f.render()
    c = Fig(48, 30)
    for x in (4, 11, 18, 29, 36, 43):
        candle(c, x, 15 if x in (4, 43) else 14, ph, 3)
    img.alpha_composite(c.render(ol=False))
    return img


def altar():
    f = Fig(56, 34)
    f.box(2, 12, 53, 33, CSTONE, 3)
    f.box(0, 10, 55, 13, CSTONE, 4)
    f.box(6, 12, 49, 26, CLOTH, 2, part=f._part())                 # the altar cloth
    f.hline(6, 49, 13, GOLD[2]); f.hline(6, 49, 25, GOLD[2])
    for y in range(15, 24): f.px(27, y, GOLD[3]); f.px(28, y, GOLD[2])
    f.hline(24, 31, 18, GOLD[3])
    f.box(25, 2, 30, 9, GOLD, 2)                                    # reliquary box
    f.px(27, 1, GOLD[4]); f.px(28, 1, GOLD[4])
    for x in (8, 14, 41, 47):
        candle(f, x, 9, x, 5)
    return f.render()


def saint():
    f = Fig(28, 72)
    f.box(3, 64, 24, 71, CSTONE, 3)
    f.poly([(8, 22), (19, 22), (22, 63), (5, 63)], CSTONE, 3)       # robe
    f.ell(13.5, 16, 4.5, 5.5, CSTONE, 4)                           # head
    f.poly([(8, 26), (4, 44), (8, 45), (11, 30)], CSTONE, 4)        # arm raised holding a root-staff
    f.line(4, 8, 5, 63, WOOD, 3)
    for y in range(28, 62, 4): f.px(12 + (y % 3), y, CSTONE[2])
    img = f.render(tex=0.3, seed=9)
    # a halo: a thin gold ring behind the head
    P = img.load()
    for a in range(0, 360, 6):
        x, y = round(13.5 + math.cos(math.radians(a)) * 8), round(15 + math.sin(math.radians(a)) * 8)
        if 0 <= x < 28 and 0 <= y < 72 and P[x, y][3] == 0: P[x, y] = GOLD[3]
    return img


def votive(ph):
    f = Fig(28, 26)
    f.box(2, 12, 25, 14, IRON, 3); f.box(4, 15, 5, 25, IRON, 2); f.box(22, 15, 23, 25, IRON, 2)
    f.box(6, 20, 21, 21, IRON, 2)
    for i, x in enumerate(range(4, 25, 3)):
        candle(f, x, 11, ph + i, 2 + (i * 7) % 3)
    return f.render()


def censer(ph):
    f = Fig(16, 36)
    sw = [0, 1, 0, -1][ph]
    f.line(8, 0, 8 + sw, 24, IRON, 3)
    f.ell(8 + sw, 28, 5, 4, GOLD, 2)
    f.hline(4 + sw, 12 + sw, 27, GOLD[4])
    f.px(8 + sw, 23, GOLD[4])
    return f.render()


def emblem(k):
    """small carved plaques above the organ stops: sun, moon, root, bell"""
    f = Fig(16, 16)
    f.box(0, 0, 15, 15, DWOOD, 3)
    f.box(2, 2, 13, 13, DWOOD, 1, part=f._part())
    G = GOLD
    if k == 0:
        for a in range(0, 360, 45): f.px(round(7.5 + math.cos(math.radians(a)) * 4.5), round(7.5 + math.sin(math.radians(a)) * 4.5), G[3])
        for y in range(6, 10):
            for x in range(6, 10): f.px(x, y, G[4] if (x + y) % 3 else G[3])
    elif k == 1:
        for y in range(3, 13):
            for x in range(3, 13):
                if (x - 7.5) ** 2 + (y - 7.5) ** 2 <= 20 and (x - 9.5) ** 2 + (y - 6.5) ** 2 > 14: f.px(x, y, G[3])
    elif k == 2:
        f.vline(7, 3, 9, G[3]); f.vline(8, 3, 9, G[2])
        for i in range(4): f.px(7 - i, 9 + i, G[3]); f.px(8 + i, 9 + i, G[3]); f.px(7, 10 + i % 3, G[2])
    else:
        for y in range(4, 12):
            w = 1 + (y - 4) * 0.55
            f.hline(round(7.5 - w), round(7.5 + w), y, G[3] if y < 11 else G[4])
        f.px(7, 3, G[3]); f.px(8, 3, G[3]); f.px(7, 12, G[4])
    return f.render(ol=False)


# ================================================================= tall: stained glass + pillars
def lancet(scheme):
    """a pointed lancet of leaded glass: a jewelled border, pale diamond quarries, two roundels (a saint, the Root)"""
    W_, H_ = 32, 96
    f = Fig(W_, H_)
    top = 16
    f.box(1, top, 30, 95, CSTONE, 3)
    f.ell(15.5, top + 1, 14.5, 15, CSTONE, 3, part=1)
    f.box(0, 90, 31, 95, CSTONE, 4, part=f._part())                    # the sill
    img = f.render(tex=0.3, seed=3)
    P = img.load()
    Gl = GLASS[scheme]
    rim = GLASS['blue'] if scheme != 'blue' else GLASS['rose']
    fig = GLASS['gold'] if scheme != 'gold' else GLASS['rose']
    cx = 15.5
    def inside(x, y, pad=0):
        if y > 88 - pad: return False
        if x < 5 + pad or x > 26 - pad: return False
        if y >= top + 2: return True
        return ((x + 0.5 - cx) / (10.5 - pad)) ** 2 + ((y + 0.5 - top - 2) / (12.5 - pad)) ** 2 <= 1
    rounds = [(cx, 36, 7.5), (cx, 66, 7.5)]
    for y in range(2, 90):
        for x in range(4, 28):
            if not inside(x, y): continue
            v = 0.5 + 0.3 * vnoise(x, y, 6, 6, len(scheme) * 7) + 0.18 * (1 - y / 90)
            if not inside(x, y, 2):                                        # the jewelled border band
                R = rim; v += 0.1
                if (y % 5 == 0) and not inside(x, y, 1): P[x, y] = (255, 240, 210, 255); continue
            else:
                inr = None
                for k, (rx, ry, rr) in enumerate(rounds):
                    d = math.hypot(x + 0.5 - rx, y + 0.5 - ry)
                    if d < rr + 0.8: inr = (k, d, rx, ry, rr)
                if inr:
                    k, d, rx, ry, rr = inr
                    if d > rr - 0.6: P[x, y] = K; continue
                    R = Gl; v = 0.35 + 0.2 * vnoise(x, y, 4, 4, 5)
                    dx, dy = x + 0.5 - rx, y + 0.5 - ry
                    if k == 0:   # a saint: gold halo, pale face, robe
                        if 2.2 < math.hypot(dx, dy + 2.5) < 3.4 and dy < 0: R = GLASS['gold']; v = 0.95
                        elif math.hypot(dx, dy + 2.5) <= 2.2: R = [(0, 0, 0, 255), (200, 170, 150, 255), (236, 214, 190, 255), (255, 240, 220, 255)]; v = 0.8
                        elif dy > 0 and abs(dx) < 1 + dy * 0.7: R = fig; v = 0.7 + 0.2 * (dx < 0)
                    else:        # the Pale Root: a trunk and its crown
                        if abs(dx) < 1.2 and dy > -2: R = GLASS['gold']; v = 0.85
                        elif dy <= -1 and math.hypot(dx, dy + 2) < 4.2 and (int(dx * 2 + dy) % 3 != 0): R = GLASS['green']; v = 0.75
                else:
                    u, w = (x - y) % 6, (x + y) % 6                   # diamond quarries
                    if u == 0 or w == 0: P[x, y] = K if (x + y) % 2 else (30, 26, 34, 255); continue
                    R = Gl; v = 0.34 + 0.3 * vnoise(x, y, 8, 8, 21) + (0.12 if ((x - y) // 6 + (x + y) // 6) % 2 else 0)
            i = int(clamp(v) * (len(R) - 2) + bt(x, y) * 0.9)
            P[x, y] = R[max(1, min(len(R) - 1, i))]
    # a trefoil at the apex, and the lead divider bars
    for (tx, ty) in [(cx - 2.5, top + 1), (cx + 2.5, top + 1), (cx, top - 2.5)]:
        for y in range(int(ty) - 3, int(ty) + 4):
            for x in range(int(tx) - 3, int(tx) + 4):
                d = math.hypot(x + 0.5 - tx, y + 0.5 - ty)
                if d < 2.2 and inside(x, y): P[x, y] = GLASS['gold'][4] if d < 1.2 else GLASS['gold'][3]
    for y in (50, 51):
        for x in range(4, 28):
            if inside(x, y): P[x, y] = K
    return img


# ================================================================= the rose window (K11)
def rose(lit):
    S = 160
    img = blank(S, S); P = img.load()
    cx = cy = 79.5
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - cx - 0.5, y + 0.5 - cy - 0.5
            r = math.hypot(dx, dy); a = (math.atan2(dy, dx) + math.pi * 2) % (math.pi * 2)
            if r > 79: continue
            if r > 72:                                                  # stone ring
                i = 3 + (1 if dy < 0 else 0) - (1 if r > 77 else 0)
                P[x, y] = CSTONE[max(1, min(6, i))]; continue
            if r > 70: P[x, y] = K; continue
            petals = 12; seg = a / (2 * math.pi) * petals; fr = seg - math.floor(seg)
            # tracery: spokes, rings and petal arcs in lead
            lead = abs(fr - 0.5) * (2 * math.pi * r / petals) < 0.9 and r > 12
            lead |= abs(r - 12) < 1.1 or abs(r - 40) < 1.1 or abs(r - 70) < 1.5
            pr = 40 + 22 * math.sin(fr * math.pi)
            lead |= abs(r - pr) < 1.0 and r > 40
            lead |= abs(r - (12 + 20 * math.sin(fr * math.pi))) < 0.9 and 12 < r < 40
            if lead:
                P[x, y] = K if lit else CSTONE[0]; continue
            if not lit:
                P[x, y] = CSTONE[1] if (x + y) % 2 else CSTONE[0]; continue
            ring = 0 if r < 12 else 1 if r < 40 else 2
            k = int(seg) % 4
            R = [GLASS['gold'], GLASS['rose'], GLASS['blue'], GLASS['rose'] if k % 2 else GLASS['blue']][ring if ring < 2 else 2 + (k % 2)]
            if ring == 1 and k % 2: R = GLASS['green']
            v = 0.5 + 0.3 * vnoise(x, y, 6, 6, 11) + 0.25 * (1 - r / 70) - 0.12 * (dy > 0)
            i = int(clamp(v) * (len(R) - 2) + bt(x, y) * 0.9)
            P[x, y] = R[max(1, min(len(R) - 1, i))]
    return img


# ================================================================= the Hallow panorama (R11)
def pano(layer):
    """layer 0: far hills in the dusk, the cathedral's spires and the archive tower; layer 1: near hills, the Long Wall's towers.
    (the Pale Root itself is in the ramparts' own far sky)"""
    Wd, Hd = 512, 160
    img = blank(Wd, Hd); P = img.load()
    if layer == 0:
        HILL = ramp("3a2c44", "34283e", "2e2438", "282032")
        for x in range(Wd):
            h = 100 + 16 * vnoise(x, 0, 64, 1, 3, 8) + 7 * vnoise(x, 0, 16, 1, 5, 32)
            for y in range(int(h), Hd):
                d = y - h
                P[x, y] = (150, 96, 90, 255) if d < 1 else HILL[min(3, int(d / 12 + bt(x, y) * 0.8))]
        def spire(cx, base, w, h):
            for y in range(base - h, base + 4):
                t = (y - (base - h)) / h
                hw = w * (0.18 if t < 0.35 else 0.55 if t < 0.62 else 1)
                for x in range(int(cx - hw), int(cx + hw) + 1):
                    P[x, y] = (72, 56, 84, 255) if x < cx - hw + 1.5 else (52, 42, 64, 255)
        for cx, base, w, h in [(150, 108, 10, 62), (132, 110, 6, 36), (168, 110, 6, 40), (120, 112, 4, 20), (180, 112, 4, 22)]:
            spire(cx, base, w, h)
        for y in range(62, 82, 5): P[150, y] = (255, 200, 120, 255)
        P[132, 90] = (255, 190, 110, 255); P[168, 88] = (255, 190, 110, 255)
        spire(372, 104, 7, 46); spire(362, 106, 4, 20)
        for y in range(70, 90, 6): P[372, y] = (255, 190, 110, 255)
        for x in range(Wd):                                                        # low mist in the valleys
            for y in range(118, 132):
                if vnoise(x, y, 40, 6, 21, 13) > 0.55 and bt(x, y) < 0.5:
                    c = P[x, y]; P[x, y] = (min(255, c[0] + 26), min(255, c[1] + 18), min(255, c[2] + 30), 255)
    else:
        HILL = ramp("1a1322", "150f1c", "110c17")
        for x in range(Wd):
            h = 126 + 12 * vnoise(x, 0, 48, 1, 9, 11) + 5 * vnoise(x, 0, 12, 1, 13, 43)
            for y in range(int(h), Hd):
                d = y - h
                P[x, y] = (96, 60, 64, 255) if d < 1 else HILL[min(2, int(d / 10 + bt(x, y) * 0.8))]
        for x0 in (60, 236, 304, 468):                                               # far wall towers, crenellated
            top = 98 + (x0 % 7)
            for y in range(top, 140):
                for x in range(x0, x0 + 12):
                    if y < top + 4 and (x - x0) % 4 >= 2: continue
                    P[x, y] = (40, 30, 50, 255) if x < x0 + 2 else (30, 23, 38, 255)
            P[x0 + 5, top + 12] = (255, 170, 90, 255)
        for x0 in range(0, Wd, 3):                                                 # the wall itself, linking them
            y = 128 + int(3 * math.sin(x0 / 40))
            for yy in range(y, y + 6):
                if 0 <= yy < Hd and P[x0, yy][3] == 0: P[x0, yy] = (30, 23, 38, 255)
    return img


# ================================================================= icon
def icon_chime():
    f = Fig(16, 16)
    for y in range(3, 12):
        w = 1.2 + (y - 3) * 0.6
        f.hline(round(7.5 - w), round(7.5 + w), y, GOLD[3] if y < 10 else GOLD[4])
    f.px(7, 2, GOLD[2]); f.px(8, 2, GOLD[2]); f.px(7, 12, GOLD[4]); f.px(8, 12, GOLD[3])
    for y in range(4, 10): f.px(6, y, GOLD[4])
    for (a, b) in [((2, 5), (1, 3)), ((13, 5), (14, 3)), ((2, 9), (0, 9)), ((13, 9), (15, 9))]:
        f.px(a[0], a[1], (200, 230, 255, 255)); f.px(b[0], b[1], (150, 200, 255, 255))
    f.px(7, 14, (200, 230, 255, 255)); f.px(8, 15, (150, 200, 255, 255))
    return f.render()


# ================================================================= build
def build():
    deco = []   # (tag, [images]) in 64x64 cels; anchor 'top' props are top-aligned
    TOP = {'wbanner', 'rootc', 'bonechand', 'chand', 'censer'}
    def add(tag, imgs):
        deco.append((tag, [frame(64, 64, im, 'top' if tag in TOP else 'bottom') for im in imgs]))
    add('wbanner', [banner_wall(i) for i in range(4)])
    add('pbanner', [banner_pole(i) for i in range(4)])
    add('hay', [hay()]); add('rack', [rack()]); add('bunk', [bunk()]); add('barrels', [barrels()])
    add('horse', [horse()]); add('cart', [cart()]); add('beacon', [beacon(i) for i in range(4)])
    add('winch', [winch()]); add('dummy', [dummy()]); add('stall', [stall()]); add('crenel', [crenel()])
    add('trebuchet', [trebuchet()]); add('rubble', [rubble()]); add('flag', [flag(i) for i in range(4)])
    add('torch', [torch(i) for i in range(4)]); add('slit', [slit()]); add('shields', [shields()])
    add('bshelf', [bshelf()]); add('coffin', [coffin()]); add('sarc', [sarc()]); add('skulls', [skulls()])
    add('rootc', [rootc(i) for i in range(4)]); add('tomb', [tomb(n) for n in (1, 2, 3, 4)])
    add('bonechand', [bonechand(i) for i in range(3)]); add('digger', [digger()])
    add('kneel', [kneel()]); add('pew', [pew()]); add('booth', [booth(False), booth(True)]); add('organ', [organ()])
    add('chand', [chand(i) for i in range(3)]); add('altar', [altar()]); add('saint', [saint()])
    add('votive', [votive(i) for i in range(3)]); add('censer', [censer(i) for i in range(4)])
    add('emblem', [frame(16, 16, emblem(k)) if False else emblem(k) for k in range(4)])
    frames, tags = [], []
    for tag, imgs in deco:
        a = len(frames)
        for im in imgs:
            cel = im if im.size == (64, 64) else frame(64, 64, im)
            frames.append({"ms": 140 if len(imgs) > 1 else 100, "cels": {"art": cel}})
        tags.append((tag, a, len(frames) - 1))
    asebuild.build("xra_deco", 64, 64, ["art"], frames, tags)
    print("xra_deco:", len(frames), "frames", 64 * 64 * len(frames), "px")

    tall = [('lancet_gold', lancet('gold')), ('lancet_rose', lancet('rose')), ('lancet_blue', lancet('blue')), ('skullpillar', frame(32, 96, skullpillar()))]
    asebuild.build("xra_tall", 32, 96, ["art"], [{"ms": 100, "cels": {"art": im}} for _, im in tall], [(t, i, i) for i, (t, _) in enumerate(tall)])
    asebuild.build("xra_big", 96, 128, ["art"], [{"ms": 100, "cels": {"art": rootheart()}}], [("rootheart", 0, 0)])
    asebuild.build("xra_rose", 160, 160, ["art"], [{"ms": 100, "cels": {"art": rose(True)}}, {"ms": 100, "cels": {"art": rose(False)}}], [("lit", 0, 0), ("dark", 1, 1)])
    asebuild.build("xra_pano", 512, 160, ["art"], [{"ms": 100, "cels": {"art": pano(0)}}, {"ms": 100, "cels": {"art": pano(1)}}], [("far", 0, 0), ("near", 1, 1)])
    asebuild.build("xra_icons", 16, 16, ["art"], [{"ms": 100, "cels": {"art": icon_chime()}}], [("c_x3_chime", 0, 0)])


if __name__ == "__main__":
    build()
