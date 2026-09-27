#!/usr/bin/env python3
"""Expansion 3, agent RB: decor for the new Weeping Mire / Ashen Archives / Hoarfrost Aqueduct rooms + two charm icons.

Sheets (assets/xrb_*.png/json, built through art/asebuild.py):
  xrb_mtree   128x160  t0 t1 t2          dead mire trees hung with moss (back layer)
  xrb_mbig    192x272  idle              the Weeping Tree (the Drowned Grove's landmark)
  xrb_mhut    112x96   idle(2)           the fisherman's hut on stilts (window flicker)
  xrb_mprop   48x48    reeds0/1(3) lily mush(2) lantpost(3) stilt boat net stakes sign0..2 table posts valve gauge
                       moss0 moss1 pump
  xrb_ashelf  16x16    tl t tr l m0..m3 r bl b br bk   bookcase pieces (tiled over stacks and back walls)
  xrb_aprop   48x48    note books0 books1 candles(3) desk card falseshelf
  xrb_acodex  160x176  idle(4)           the hanging codex (the Grand Stacks' landmark)
  xrb_awin    96x128   idle              the Reading Nook's window (panes left clear: the rain is drawn live behind it)
  xrb_amural  128x64   idle              the scribe's fresco (Cipher Wall)
  xrb_fprop   48x48    valve crystal0 crystal1 drift gauge sign0 sign1 pump1 lamp(3)
  xrb_fbig    160x128  arch pump statue arch2    big Hoarfrost pieces
  xrb_icons   16x16    c_x3_ink c_x3_rime

Light from the upper left, 1px near-black outlines, ordered-dither ramps (house style: art/envlib.py).
Usage: python3 art/gen_xrb.py [--no-ase]   (previews -> art/previews/xrb_*.png)
"""
import math, os, random, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from envlib import C, ramp, K, T, pick, h01, vnoise, clamp, blank, outline, scale   # noqa: E402

ASE = '--no-ase' not in sys.argv
PREV = os.path.join(HERE, 'previews')
os.makedirs(PREV, exist_ok=True)

# ---------------------------------------------------------------- palettes (copied from the regions' own generators)
M_PEAT = ramp("0b0a08", "13110d", "1b1813", "25211a", "302a20", "3c3427", "4a402f")
M_MOSS = ramp("141c10", "1f2a14", "2e3c18", "40521e", "566c26", "70882e", "8ea43a", "b2c458")
M_HANG = ramp("10160f", "1a2418", "263322", "34442c", "46583a", "5d6f4a")        # grey-green hanging moss
M_WOOD = ramp("15110c", "231c14", "32291c", "443826", "584a32", "6e5e40", "86764e")
M_DEAD = ramp("0e0d0c", "181614", "24211d", "312d27", "403a32", "524a3f", "665c4e", "7c705e")   # bleached deadwood
M_ROPE = ramp("3a3222", "5a4e34", "7e704c")
M_BONE = ramp("3a3a2c", "5c5c46", "85826a", "aca88c")
M_GLOW = ramp("2a4a18", "4a7a22", "7ab236", "b4e05a", "e4ffa0")                   # spore glow
FIRE = ramp("5a1c08", "a8420e", "e07a24", "ffac48", "ffe0a0", "fffbe8")
IRONM = ramp("0e0e0c", "1c1b18", "2c2a24", "3e3a30", "524c3e", "6a624e")           # rusted iron (mire)
RUST = ramp("3a1a0c", "5c2c12", "7e4418")
OAK = ramp("0c0909", "150f0e", "1f1714", "2b201a", "3a2b21", "4c3829", "604733", "785a40")
PARCH = ramp("3e3428", "6a5c44", "9a8a68", "c4b48c", "e2d6b0", "f6eed6")
GOLD = ramp("5a3c14", "8a6224", "c09440", "ecc870", "fff0b8", "ffffff")
VIO = ramp("22163a", "3a2658", "5a3c86", "8660b8", "b494e4", "e2d0ff")
INK = ramp("05040a", "0b0914", "141024", "241a3c", "3c2c5c")
IRONA = ramp("100e16", "221e2a", "383240", "524a5a", "70687a", "978ea0", "c2b8c4")
WAX = ramp("6a5a48", "a8987c", "d8ccb0", "f4ecd8")
STONEA = ramp("0e0c12", "18151e", "231f2a", "2f2a37", "3d3746", "4d4657", "605869")
BOOKS = [ramp("2e1014", "4e1c20", "74302c"), ramp("0e2024", "183638", "2a5250"), ramp("2e2412", "4e3c1c", "74582a"),
         ramp("22142e", "382448", "553a66"), ramp("241a14", "3c2c20", "5a4430"), ramp("1a1a22", "2c2c38", "44444f")]
ST = ramp("06080d", "0a0d14", "0f131b", "141923", "1a202c", "212836", "293142", "323b4e", "3c465a", "4a556a")
SNOW = ramp("4e6072", "7b90a4", "aabdcc", "d5e2eb", "f2f8fb")
ICE = ramp("0e2236", "15344c", "1d4a66", "286684", "3886a6", "55a6c4", "82c6dc", "b6e4f2", "e6fbff")
IRONF = ramp("0b0e13", "161b23", "232a34", "333c48", "47515f", "5f6a79", "808b99", "a8b2be")
BRASS = ramp("2a200e", "4a3a18", "6e5624", "967634", "bc9a4a")
EMBER = ramp("5a1004", "a8300a", "f06a1a", "ffb040", "fff0c0")


class S:
    """a sprite canvas: pixels + helpers (all coords in px)."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = blank(w, h)
        self.px = self.img.load()

    def set(self, x, y, c):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else T

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def shade_rect(self, x0, y0, x1, y1, r, base=None, grain=0.0, seed=0):
        n = len(r)
        base = (n - 1) * 0.5 if base is None else base
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                v = base / (n - 1)
                if x == x0: v += 0.18
                if x == x1: v -= 0.2
                if y == y0: v += 0.25
                if y == y1: v -= 0.2
                if grain: v += (vnoise(x, y, 3, 2, seed) - 0.5) * grain
                self.set(x, y, pick(r, v, x, y))

    def line(self, x0, y0, x1, y1, c, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if w <= 1: self.set(x, y, c)
            else:
                for dy in range(-(w // 2), w - w // 2):
                    for dx in range(-(w // 2), w - w // 2):
                        self.set(x + dx, y + dy, c)

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def ball(self, cx, cy, r, rp, lo=0.1, hi=0.9, lx=-0.6, ly=-0.7):
        """shaded sphere / blob lit from the upper left"""
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
                d = dx * dx + dy * dy
                if d > 1: continue
                z = math.sqrt(1 - d)
                v = lo + (hi - lo) * clamp(0.55 + 0.5 * (dx * lx + dy * ly) + 0.3 * (z - 0.5))
                self.set(x, y, pick(rp, v, x, y))

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 <= y + 0.5 < y1) or (y1 <= y + 0.5 < y0):
                    xs.append(x0 + (y + 0.5 - y0) / (y1 - y0) * (x1 - x0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    self.set(x, y, c)

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[x, y]
                if c[3]: self.set(ox + x, oy + y, c)

    def out(self, col=K, diag=False):
        self.img = outline(self.img, col, diag=diag)
        self.px = self.img.load()
        return self

    def flip(self):
        o = S(self.w, self.h)
        o.img = self.img.transpose(Image.FLIP_LEFT_RIGHT); o.px = o.img.load()
        return o


def taper(s, x0, y0, x1, y1, w0, w1, rp, seed=0, bark=True):
    """a tapered limb from (x0,y0) (width w0) to (x1,y1) (width w1), lit from the upper left"""
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    steps = int(L * 2) + 2
    for i in range(steps + 1):
        t = i / steps
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        w = w0 + (w1 - w0) * t
        for k in range(-int(w) - 1, int(w) + 2):
            if abs(k) > w: continue
            x, y = cx + nx * k, cy + ny * k
            side = k / max(w, 0.5)                                  # -1 .. 1 across the limb
            lit = -side * (1 if nx < 0 else -1)
            v = 0.42 + 0.35 * lit
            if bark: v += (vnoise(x, y * 0.5, 2, 5, seed) - 0.5) * 0.35
            if abs(side) > 0.8: v -= 0.18
            s.set(x, y, pick(rp, v, x, y))


def moss_strand(s, x, y, length, rp, seed, sway=0.0):
    for i in range(int(length)):
        xx = x + math.sin(i * 0.35 + seed) * 0.8 + sway * (i / max(1, length)) ** 2
        v = 0.65 - 0.5 * i / length + (h01(int(x), i, seed) - 0.5) * 0.3
        s.set(xx, y + i, pick(rp, v, xx, y + i))
        if i % 5 == 2 and h01(int(x), i, seed + 3) > 0.5:
            s.set(xx + 1, y + i, pick(rp, v - 0.1, xx, y + i))


# ======================================================================================================== MIRE
def dead_tree(W, H, seed, big=False):
    """a drowned dead tree: flared roots, a leaning trunk, crooked limbs, grey-green moss hanging in curtains"""
    rnd = random.Random(seed)
    s = S(W, H)
    base = H - 2
    cx = W / 2 + rnd.uniform(-6, 6)
    trunk_w = (15 if big else 7) + rnd.uniform(-1, 1)
    top_y = H * (0.18 if big else 0.32)
    lean = rnd.uniform(-10, 10) if not big else rnd.uniform(-4, 4)
    limbs = []
    # roots
    for k in range(5 if big else 4):
        a = (k / (4 if big else 3) - 0.5) * 2.6
        rx = cx + math.sin(a) * (trunk_w * 2.4 + rnd.uniform(0, 8))
        taper(s, cx + math.sin(a) * trunk_w * 0.6, base - 10, rx, base + 1, trunk_w * 0.55, 1.2, M_DEAD, seed + k)
    # trunk in 3 bends
    pts = [(cx, base - 4)]
    for i in range(1, 4):
        t = i / 3
        pts.append((cx + lean * t + rnd.uniform(-4, 4), base - 4 - (base - top_y) * t))
    for i in range(3):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        taper(s, xa, ya, xb, yb, trunk_w * (1 - i * 0.22), trunk_w * (1 - (i + 1) * 0.22), M_DEAD, seed + 10 + i)
    # limbs (recursive)
    def limb(x, y, ang, L, w, depth):
        x1, y1 = x + math.cos(ang) * L, y - math.sin(ang) * L
        taper(s, x, y, x1, y1, w, max(0.6, w * 0.55), M_DEAD, seed + depth * 7 + int(L))
        limbs.append((x, y, x1, y1))
        if depth <= 0 or L < 7: return
        for d in (-1, 1):
            if rnd.random() < 0.85:
                limb(x1, y1, ang + d * rnd.uniform(0.35, 0.8) - 0.12, L * rnd.uniform(0.55, 0.75), w * 0.6, depth - 1)
    for i, (px_, py_) in enumerate(pts[1:]):
        for d in (-1, 1):
            if rnd.random() < (0.9 if i > 0 else 0.6):
                limb(px_, py_, math.pi / 2 + d * rnd.uniform(0.5, 1.1), (H * (0.2 if big else 0.22)) * rnd.uniform(0.7, 1.05),
                     trunk_w * 0.45, 3 if big else 2)
    limb(pts[-1][0], pts[-1][1], math.pi / 2 + rnd.uniform(-0.25, 0.25), H * 0.15, trunk_w * 0.4, 2)
    s.out()
    # moss curtains from the limbs
    for (x0, y0, x1, y1) in limbs:
        n = int(abs(x1 - x0) / (1.4 if big else 2.5))
        for i in range(n):
            t = rnd.random()
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if rnd.random() < (0.85 if big else 0.6):
                moss_strand(s, x, y + 1, rnd.uniform(8, 54 if big else 18), M_HANG, seed + i, sway=rnd.uniform(-2, 2))
    s.limbs = limbs
    # moss on the trunk base and the waterline stain
    for y in range(int(base - 26), base):
        for x in range(W):
            c = s.get(x, y)
            if c[3] and c != K and h01(x, y, seed + 99) < 0.25 + (y - (base - 26)) / 40:
                s.set(x, y, pick(M_MOSS, 0.35 + h01(x, y, 5) * 0.3, x, y))
    return s


def weeping_tree():
    s = dead_tree(240, 272, 71, big=True)
    # spore pods hang from the limb tips: the Grove's landmark (their light is added live in 51_rb.js)
    rnd = random.Random(5)
    ends = [(x1, y1) for (x0, y0, x1, y1) in s.limbs if 30 < x1 < 210 and 20 < y1 < 190]
    rnd.shuffle(ends)
    for (x, y) in ends[:18]:
        L = rnd.randint(4, 14)
        for k in range(L): s.set(x, y + k, M_HANG[2 + (k % 2)])
        s.ball(x, y + L + 2, 2.4, M_GLOW, 0.35, 1.0)
    return s


def reeds(v, f):
    s = S(48, 48)
    rnd = random.Random(40 + v)
    for i in range(14 if v == 0 else 18):
        bx = 8 + rnd.uniform(0, 32)
        h = rnd.uniform(22, 44)
        lean = rnd.uniform(-5, 5) + math.sin(f * 2.1 + i) * 1.6 * (h / 44)
        col = M_MOSS if rnd.random() < 0.7 else M_WOOD
        for y in range(int(h)):
            t = y / h
            x = bx + lean * t * t
            v2 = 0.25 + 0.45 * t + (0.1 if i % 2 else 0)
            s.set(x, 47 - y, pick(col, v2, x, y))
            if t < 0.35: s.set(x + 1, 47 - y, pick(col, v2 - 0.1, x, y))
        if rnd.random() < 0.55:                                       # cattail head
            x = bx + lean
            for y in range(int(h) - 7, int(h) - 1):
                s.set(x, 47 - y, M_WOOD[2]); s.set(x + 1, 47 - y, M_WOOD[1] if y % 2 else M_WOOD[3])
    return s.out()


def lily():
    s = S(48, 48)
    for (cx, cy, r) in [(14, 44, 7), (27, 45, 5), (37, 44, 6)]:
        for y in range(int(cy - r / 2.6), int(cy + r / 2.6) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = (x - cx) / r, (y - cy) / (r / 2.6)
                if dx * dx + dy * dy <= 1 and not (dx > 0.1 and abs(dy) < 0.25):     # the notch
                    s.set(x, y, pick(M_MOSS, 0.45 + 0.3 * (-dy) - 0.15 * dx, x, y))
    s.ball(28, 41, 2, ramp("5a3a48", "a86a88", "e0a8c0", "fbe0ec"), 0.3, 1)            # a pale flower
    return s.out()


def mush(f):
    s = S(48, 48)
    for (x, h, r) in [(18, 8, 5), (25, 12, 6), (31, 6, 4), (14, 4, 3)]:
        s.rect(x, 47 - h, x + 1, 47, M_BONE[1]); s.set(x, 47 - h, M_BONE[2])
        for y in range(-r // 2, 1):
            for dx in range(-r, r + 1):
                if dx * dx / (r * r) + (y * y) / ((r / 2) ** 2) <= 1:
                    k = 0.55 + 0.35 * (-y / (r / 2)) - 0.12 * (dx / r) + 0.12 * math.sin(f * math.pi + x)
                    s.set(x + dx, 47 - h + y, pick(M_GLOW, k, x + dx, y))
    return s.out()


def lantpost(f):
    s = S(48, 48)
    s.shade_rect(22, 6, 24, 47, M_WOOD, 3, grain=0.3, seed=3)
    s.rect(22, 6, 31, 7, M_WOOD[2]); s.rect(22, 6, 31, 6, M_WOOD[4])     # the arm
    s.line(30, 8, 30, 12, IRONM[3])
    # the lantern
    s.shade_rect(27, 13, 33, 22, IRONM, 2)
    s.rect(28, 14, 32, 21, FIRE[2 + (f % 2)])
    s.rect(29, 16, 31, 20, FIRE[4 - (f == 2)])
    s.set(30, 17, FIRE[5])
    s.rect(26, 12, 34, 12, IRONM[4]); s.rect(27, 23, 33, 23, IRONM[2])
    for y in range(28, 47, 3): s.set(21, y, M_MOSS[3])                  # moss creeping up the post
    return s.out()


def stilt():
    s = S(48, 48)
    s.shade_rect(21, 0, 26, 47, M_WOOD, 2.5, grain=0.35, seed=8)
    for y in (6, 26): s.rect(20, y, 27, y + 1, M_ROPE[1])               # lashings
    for y in range(30, 48):
        for x in range(21, 27):
            if h01(x, y, 3) < (y - 30) / 20: s.set(x, y, pick(M_MOSS, 0.3 + h01(x, y, 1) * 0.3, x, y))
    return s.out()


def boat():
    s = S(48, 48)
    pts = [(4, 34), (44, 30), (40, 44), (10, 46)]
    s.poly(pts, M_WOOD[3])
    for y in range(30, 47):
        for x in range(0, 48):
            if s.get(x, y)[3]:
                v = 0.25 + 0.4 * (1 - (y - 30) / 16) + (0.1 if (x // 5) % 2 else 0)
                s.set(x, y, pick(M_WOOD, v, x, y))
    s.line(5, 34, 43, 30, M_WOOD[5]); s.line(8, 36, 42, 33, M_WOOD[1])
    for x in range(12, 40, 9): s.line(x, 33, x - 1, 44, M_WOOD[1])       # ribs
    for x in range(10, 40):
        if h01(x, 1, 2) < 0.5: s.set(x, 44 + (x % 2), M_MOSS[3])
    return s.out()


def net():
    s = S(48, 48)
    s.shade_rect(8, 4, 10, 47, M_WOOD, 3, grain=0.3, seed=2); s.shade_rect(38, 4, 40, 47, M_WOOD, 3, grain=0.3, seed=4)
    s.rect(8, 4, 40, 5, M_WOOD[3])
    for i in range(12):
        x = 11 + i * 2.4
        sag = 10 + math.sin(i / 11 * math.pi) * 14
        for y in range(6, int(6 + sag)):
            if (y + i) % 3 == 0: s.set(x, y, M_ROPE[1])
        for y in range(6, int(6 + sag), 4): s.line(x, y, x + 2.4, y + 1, M_ROPE[0])
    s.out()
    for x in range(11, 38, 3): moss_strand(s, x, 20 + (x % 5), 5, M_HANG, x)
    return s


def stakes():
    s = S(48, 48)
    for i, (x, h, a) in enumerate([(12, 20, -0.2), (19, 26, 0.05), (26, 18, 0.2), (33, 23, -0.1), (39, 14, 0.3)]):
        tx, ty = x + math.sin(a) * h, 47 - h
        taper(s, x, 47, tx, ty, 2.2, 0.4, M_DEAD, i)
        s.set(tx, ty + 1, M_BONE[3])
    s.out()
    s.ball(19, 30, 3, M_BONE, 0.2, 0.95)                                  # a skull spiked on a stake
    s.set(18, 30, K); s.set(20, 30, K)
    return s


def sign(v):
    s = S(48, 48)
    s.shade_rect(23, 22, 25, 47, M_WOOD, 3, grain=0.3, seed=1)
    s.shade_rect(15, 12, 33, 23, M_WOOD, 3.5, grain=0.25, seed=7)
    c = FIRE[4]
    if v == 1:     # a carved arrow pointing down (drop through the boards)
        s.line(24, 14, 24, 20, K); s.line(21, 17, 24, 21, K); s.line(27, 17, 24, 21, K)
    elif v == 2:   # a valve wheel mark
        s.disc(24, 17, 3.5, K); s.disc(24, 17, 2, M_WOOD[4]); s.set(24, 17, K)
    else:          # an arrow pointing down into the dark (the hatch)
        s.line(24, 14, 24, 20, K); s.line(21, 17, 24, 20, K); s.line(27, 17, 24, 20, K); s.rect(19, 21, 29, 21, K)
    s.out()
    s.rect(30, 8, 31, 12, M_ROPE[1])
    return s


def table():
    s = S(48, 48)
    s.shade_rect(10, 32, 38, 34, M_WOOD, 4, grain=0.2, seed=5)
    for x in (12, 35): s.shade_rect(x, 35, x + 1, 47, M_WOOD, 2.5)
    s.rect(14, 30, 26, 31, PARCH[4]); s.rect(15, 30, 25, 30, PARCH[5])    # Kalden's letter
    for x in range(16, 25, 2): s.set(x, 31, PARCH[1])
    s.set(22, 29, RUST[2]); s.rect(21, 28, 23, 29, C("7a1818"))            # the wax seal
    s.shade_rect(30, 24, 32, 31, WAX, 2)                                 # a candle stub
    s.set(31, 22, FIRE[4]); s.set(31, 23, FIRE[3]); s.set(31, 21, FIRE[2])
    s.shade_rect(33, 28, 36, 31, M_BONE, 1.5)                            # a clay cup
    return s.out()


def posts():
    s = S(48, 48)
    s.shade_rect(21, 14, 26, 47, M_WOOD, 3, grain=0.35, seed=6)
    s.rect(20, 14, 27, 16, M_WOOD[4])
    s.rect(19, 18, 28, 19, M_ROPE[2]); s.rect(19, 24, 28, 25, M_ROPE[1])
    return s.out()


def valve_m():
    s = S(48, 48)
    s.shade_rect(14, 40, 34, 47, IRONM, 3)                               # the pipe stub
    s.shade_rect(22, 30, 26, 40, IRONM, 3)
    for a in range(0, 360, 8):
        r = math.radians(a)
        s.set(24 + math.cos(r) * 9, 28 + math.sin(r) * 9, RUST[2] if a % 40 else IRONM[5])
        s.set(24 + math.cos(r) * 8, 28 + math.sin(r) * 8, IRONM[3])
    for a in range(0, 360, 60):
        r = math.radians(a)
        s.line(24, 28, 24 + math.cos(r) * 8, 28 + math.sin(r) * 8, IRONM[4])
    s.disc(24, 28, 2, IRONM[5])
    return s.out()


def gauge_m():
    s = S(48, 48)
    s.disc(24, 38, 7, IRONM[4]); s.disc(24, 38, 5.5, M_BONE[3])
    for a in range(200, 341, 35):
        r = math.radians(a)
        s.set(24 + math.cos(r) * 4.5, 38 + math.sin(r) * 4.5, K)
    s.line(24, 38, 21, 35, C("8a1a14"))
    s.rect(23, 45, 25, 47, IRONM[2])
    return s.out()


def moss(v):
    s = S(48, 48)
    rnd = random.Random(90 + v)
    for i in range(7 + v * 3):
        moss_strand(s, 14 + rnd.uniform(0, 20), 0, rnd.uniform(14, 44), M_HANG, 50 + i + v * 9, sway=rnd.uniform(-2, 2))
    return s


def pump_m():
    s = S(48, 48)
    s.shade_rect(10, 20, 30, 47, M_WOOD, 3, grain=0.3, seed=11)         # the wooden pump housing
    s.rect(9, 20, 31, 22, M_WOOD[5]); s.rect(9, 44, 31, 45, IRONM[3])
    for y in (28, 36): s.rect(10, y, 30, y, IRONM[2])
    s.shade_rect(30, 30, 44, 33, IRONM, 3)                               # spout
    s.shade_rect(18, 8, 21, 20, IRONM, 3)                                # the handle post
    s.line(20, 8, 40, 2, IRONM[4], 2)                                    # the lever
    for x in range(12, 30, 3): moss_strand(s, x, 23, 6 + x % 5, M_HANG, x)
    return s.out()


def hut(f):
    s = S(112, 96)
    # stilts under the floor (the floor itself is terrain; the hut stands on it)
    # walls: vertical planks
    for x in range(14, 98):
        for y in range(34, 94):
            v = 0.35 + (0.12 if (x // 6) % 2 else 0) + (vnoise(x, y, 2, 9, 3) - 0.5) * 0.35 - (0.2 if x % 6 == 0 else 0)
            s.set(x, y, pick(M_WOOD, v, x, y))
    # roof: sagging mossy thatch with an overhang
    for y in range(8, 38):
        t = (y - 8) / 30
        x0, x1 = 56 - 14 - t * 44, 56 + 14 + t * 44
        sag = math.sin((y - 8) * 0.4) * 0.5
        for x in range(int(x0), int(x1)):
            v = 0.3 + 0.35 * (1 - t) + (h01(x // 2, y, 4) - 0.5) * 0.35 + sag * 0.1
            s.set(x, y, pick(M_MOSS if h01(x // 3, y // 2, 8) < 0.55 else M_PEAT, v, x, y))
    for x in range(12, 100, 2): s.set(x, 38 + (x % 4 == 0), M_HANG[2])
    # door and window
    s.shade_rect(24, 58, 38, 93, M_WOOD, 1.2, grain=0.25, seed=9)
    s.rect(24, 58, 38, 58, M_WOOD[4]); s.set(35, 76, IRONM[4])
    lit = FIRE[3] if f == 0 else FIRE[2]
    s.rect(62, 52, 84, 68, IRONM[1])
    s.rect(64, 54, 82, 66, lit); s.rect(66, 56, 80, 64, FIRE[4] if f == 0 else FIRE[3])
    s.rect(73, 54, 73, 66, M_WOOD[1]); s.rect(64, 60, 82, 60, M_WOOD[1])
    s.rect(60, 69, 86, 70, M_WOOD[5])                                    # sill
    # a chimney pipe and a hanging string of dried fish
    s.shade_rect(84, 2, 88, 22, IRONM, 2.5)
    for i in range(4):
        x = 44 + i * 5
        s.line(x, 40, x, 44, M_ROPE[1]); s.rect(x - 1, 45, x + 1, 50, M_BONE[2]); s.set(x, 51, M_BONE[1])
    for y in range(78, 94):                                              # waterline rot
        for x in range(14, 98):
            if h01(x, y, 17) < (y - 78) / 18: s.set(x, y, pick(M_MOSS, 0.25 + h01(x, y, 2) * 0.25, x, y))
    return s.out()


# ======================================================================================================== ARCHIVES
def shelf_piece(kind, seed):
    """16x16 bookcase pieces: frame + rows of book spines"""
    s = S(16, 16)
    rnd = random.Random(seed)
    s.rect(0, 0, 15, 15, OAK[1])
    edge_l = kind in ('tl', 'l', 'bl')
    edge_r = kind in ('tr', 'r', 'br')
    if kind in ('tl', 't', 'tr'):
        s.rect(0, 0, 15, 4, OAK[4]); s.rect(0, 0, 15, 0, OAK[6]); s.rect(0, 4, 15, 4, OAK[2])
        for x in range(0, 16, 4): s.set(x + 1, 2, OAK[6])
        rows = [(6, 15)]
    elif kind in ('bl', 'b', 'br'):
        s.rect(0, 10, 15, 15, OAK[3]); s.rect(0, 10, 15, 10, OAK[5]); s.rect(0, 15, 15, 15, OAK[1])
        rows = [(1, 8)]
    elif kind == 'bk':            # a broken top: splintered boards
        for x in range(16):
            top = int(3 + 5 * h01(x, 1, seed))
            s.rect(x, top, x, 15, OAK[2 if x % 3 else 3])
            s.set(x, top, OAK[5])
        rows = [(9, 15)]
    else:
        rows = [(1, 7), (9, 15)]
        s.rect(0, 8, 15, 8, OAK[5]); s.rect(0, 0, 15, 0, OAK[3])
    for (y0, y1) in rows:
        x = 1 if edge_l else 0
        while x < (14 if edge_r else 16):
            bw = rnd.choice((1, 2, 2, 2, 3))
            bh = rnd.randint(max(2, y1 - y0 - 3), y1 - y0)
            B = rnd.choice(BOOKS)
            if rnd.random() < 0.08:          # a gap, or a book lying flat
                x += bw; continue
            for xx in range(x, min(x + bw, 16)):
                for yy in range(y1 - bh + 1, y1 + 1):
                    s.set(xx, yy, B[2] if xx == x else B[1] if xx < x + bw - 1 else B[0])
                if bh > 3 and rnd.random() < 0.5: s.set(xx, y1 - bh + 2, GOLD[2])      # gilt band
            x += bw
    if edge_l: s.rect(0, 0, 1, 15, OAK[5]); s.rect(0, 0, 0, 15, OAK[6])
    if edge_r: s.rect(14, 0, 15, 15, OAK[2]); s.rect(15, 0, 15, 15, OAK[1])
    return s


def note():
    s = S(48, 48)
    for y in range(18, 44):
        for x in range(14, 34):
            v = 0.6 + (vnoise(x, y, 3, 3, 21) - 0.5) * 0.35 - (0.2 if (x - 14) + (43 - y) < 4 else 0)
            s.set(x, y, pick(PARCH, v, x, y))
    for x in range(14, 34):                                              # ragged bottom edge
        if h01(x, 5, 2) < 0.4: s.set(x, 43, T)
    s.rect(23, 17, 25, 19, IRONA[4]); s.set(24, 18, IRONA[6])            # the nail
    return s.out()


def books(v):
    s = S(48, 48)
    rnd = random.Random(60 + v)
    y = 47
    for i in range(4 + v):
        bw, bh = rnd.randint(14, 20), rnd.randint(3, 4)
        x0 = 24 - bw // 2 + rnd.randint(-3, 3)
        B = rnd.choice(BOOKS)
        s.rect(x0, y - bh + 1, x0 + bw, y, B[1]); s.rect(x0, y - bh + 1, x0 + bw, y - bh + 1, B[2])
        s.rect(x0 + bw - 1, y - bh + 1, x0 + bw, y, PARCH[3])
        y -= bh
    if v == 1:
        s.shade_rect(30, 36, 32, 47, WAX, 2); s.set(31, 34, FIRE[4]); s.set(31, 35, FIRE[3])
    return s.out()


def candles(f):
    s = S(48, 48)
    for i, (x, h) in enumerate([(18, 10), (22, 14), (26, 8), (29, 11)]):
        s.shade_rect(x, 47 - h, x + 1, 47, WAX, 2)
        fl = (f + i) % 3
        s.set(x, 46 - h, FIRE[3 + (fl == 0)]); s.set(x + (fl == 1), 45 - h, FIRE[2])
        if fl == 2: s.set(x, 44 - h, FIRE[1])
    for x in range(16, 33):
        if h01(x, 3, 1) < 0.6: s.set(x, 47, WAX[1])                      # melted wax
    return s.out()


def desk():
    s = S(48, 48)
    s.shade_rect(3, 28, 44, 31, OAK, 5, grain=0.2, seed=2)               # slanted copy desk
    for x in (5, 41): s.shade_rect(x, 32, x + 2, 47, OAK, 3)
    s.rect(5, 40, 43, 41, OAK[3])
    s.rect(9, 25, 29, 27, PARCH[4])                                       # the page being copied
    for x in range(11, 28, 2): s.set(x, 26, INK[3])
    s.rect(31, 24, 34, 27, INK[1]); s.rect(31, 24, 34, 24, IRONA[4])      # inkpot
    s.line(33, 24, 37, 14, PARCH[5]); s.line(34, 24, 38, 15, PARCH[3])    # quill
    s.shade_rect(38, 19, 40, 27, WAX, 2); s.set(39, 17, FIRE[4]); s.set(39, 18, FIRE[3])
    return s.out()


def card():
    s = S(48, 48)
    s.shade_rect(21, 30, 26, 47, OAK, 4)                                  # stand
    s.shade_rect(15, 44, 32, 47, OAK, 3)
    s.poly([(12, 22), (36, 22), (38, 30), (10, 30)], OAK[4])
    s.rect(14, 20, 33, 27, PARCH[5]); s.rect(14, 20, 33, 20, PARCH[3])     # the index card
    for y in (22, 24, 26):
        for x in range(16, 31, 3): s.set(x, y, INK[2]); s.set(x + 1, y, INK[3])
    return s.out()


def codex(f):
    """a chained book the size of a house, open, its pages bleeding violet script"""
    s = S(160, 176)
    cx, top = 80, 30
    # chains up to the ceiling
    for x0 in (22, 138):
        for y in range(0, top + 20, 4):
            s.rect(x0 - 1, y, x0 + 1, y + 2, IRONA[3]); s.set(x0, y + 1, IRONA[1])
    # covers (a shallow V), page blocks, pages
    for side in (-1, 1):
        for y in range(top, top + 120):
            t = (y - top) / 120
            for k in range(0, 72):
                x = cx + side * (4 + k)
                lift = (k / 72) ** 2 * 18
                yy = y - lift
                v = 0.25 + 0.3 * (1 - k / 72) + (0.2 if side < 0 else 0)
                s.set(x, yy + 6, pick(BOOKS[0], v, x, yy))
        for y in range(top, top + 116):
            for k in range(2, 66):
                x = cx + side * (4 + k)
                lift = (k / 72) ** 2 * 18
                yy = y - lift
                v = 0.3 + 0.2 * (1 - k / 66) * (1 if side < 0 else 0.6) - (0.2 if k > 62 else 0) + (vnoise(x, y, 5, 7, 12) - 0.5) * 0.3
                s.set(x, yy, pick(PARCH, v, x, yy))
    # script: glowing violet lines that crawl (frame f)
    rnd = random.Random(8)
    for side in (-1, 1):
        for li in range(18):
            y = top + 8 + li * 6
            n = rnd.randint(30, 56)
            for k in range(8, 8 + n):
                if rnd.random() < 0.28: continue
                x = cx + side * k
                lift = (k / 72) ** 2 * 18
                glow = ((k + li * 3 + f * 5) % 20) < 4
                s.set(x, y - lift, VIO[5] if glow else INK[3] if (k + li) % 3 else VIO[2])
    s.rect(cx - 2, top - 2, cx + 1, top + 124, OAK[2])                   # the spine / gutter shadow
    # clasps and a dripping of ink
    for side in (-1, 1):
        s.shade_rect(cx + side * 70 - 3, top + 40, cx + side * 70 + 3, top + 52, GOLD, 3)
    for i, x in enumerate((60, 74, 97, 112)):
        L = 18 + (i * 7 + f * 3) % 14
        for y in range(top + 122, top + 122 + L): s.set(x, y, INK[2] if y % 5 else VIO[2])
        s.set(x, top + 122 + L, VIO[4])
    return s.out()


def window():
    s = S(96, 128)
    # stone frame with a pointed arch; panes left transparent
    def inside(x, y, m):          # a pointed (gothic) arch springing at y 56, over a rectangle, inset by m
        r = 48 - m
        if y >= 56: return m <= x <= 95 - m and y <= 127 - m
        R, xx = r * 1.1, x + 0.5
        return math.hypot(xx - (48 - r + R), y - 56) <= R and math.hypot(xx - (48 + r - R), y - 56) <= R
    for y in range(128):
        for x in range(96):
            if inside(x, y, 0) and not inside(x, y, 7):
                v = 0.45 + (0.15 if x < 48 else -0.1) + (vnoise(x, y, 4, 4, 3) - 0.5) * 0.3
                s.set(x, y, pick(STONEA, v, x, y))
    # mullions and tracery
    for x in (31, 32, 63, 64):
        for y in range(20, 121): s.set(x, y, STONEA[4 if x % 2 else 2])
    for y in (70, 71):
        for x in range(8, 88): s.set(x, y, STONEA[4 if y == 70 else 2])
    s.disc(48, 30, 9, STONEA[3]); s.disc(48, 30, 6, T)
    for a in range(0, 360, 45):
        r = math.radians(a)
        s.set(48 + math.cos(r) * 7.5, 30 + math.sin(r) * 7.5, STONEA[5])
    # the sill
    s.shade_rect(0, 118, 95, 127, STONEA, 4)
    return s.out()


def mural():
    s = S(128, 64)
    for y in range(64):
        for x in range(128):
            v = 0.45 + (vnoise(x, y, 6, 6, 44) - 0.5) * 0.5
            s.set(x, y, pick(ramp("2a2218", "3c3222", "54462e", "6e5c3c", "8a7650"), v, x, y))
    # a hooded scribe (silhouette) holding four leaves out, numbered I..IV
    s.poly([(16, 62), (22, 20), (30, 12), (38, 20), (44, 62)], ramp("141018", "1e1822")[1])
    s.disc(30, 16, 5, ramp("141018")[0])
    for i in range(4):
        x0 = 52 + i * 18
        s.rect(x0, 16, x0 + 12, 34, PARCH[3]); s.rect(x0, 16, x0 + 12, 16, PARCH[4])
        for k in range(i + 1):                                           # tally marks = the leaf's number
            s.rect(x0 + 3 + k * 2, 38, x0 + 3 + k * 2, 44, GOLD[2])
        s.line(44, 34, x0 + 6, 34, ramp("241c14")[0])
    # a crack through the plaster
    x, y = 100, 0
    for i in range(40):
        s.set(x, y, K); x += random.Random(i).choice((-1, 0, 1)); y += 1
    return s.out()


def falseshelf():
    s = S(48, 48)
    for y in range(0, 48, 16):
        for x in range(8, 40, 16):
            p = shelf_piece('tl' if (y == 0 and x == 8) else 'tr' if y == 0 else 'l' if x == 8 else 'r', 300 + x + y)
            s.paste(p, x, y)
    s.rect(24, 30, 25, 33, GOLD[3])                                      # a brass pull where no pull should be
    return s.out()


# ======================================================================================================== HOARFROST
def valve_f():
    s = S(48, 48)
    s.shade_rect(10, 40, 38, 47, IRONF, 3); s.shade_rect(22, 30, 26, 40, IRONF, 3)
    for a in range(0, 360, 6):
        r = math.radians(a)
        s.set(24 + math.cos(r) * 10, 26 + math.sin(r) * 10, IRONF[5] if a % 30 else IRONF[7])
        s.set(24 + math.cos(r) * 9, 26 + math.sin(r) * 9, IRONF[3])
    for a in range(0, 360, 72):
        r = math.radians(a + 20)
        s.line(24, 26, 24 + math.cos(r) * 9, 26 + math.sin(r) * 9, IRONF[5])
    s.disc(24, 26, 2.5, BRASS[3])
    for x in range(12, 38):                                              # rime on the top edges
        if h01(x, 2, 3) < 0.7: s.set(x, 40, SNOW[3])
    for a in range(180, 360, 12):
        r = math.radians(a)
        s.set(24 + math.cos(r) * 10, 25 + math.sin(r) * 10, SNOW[4])
    return s.out()


def crystal(v):
    s = S(48, 48)
    rnd = random.Random(70 + v)
    for i in range(5 + v * 2):
        bx = 24 + rnd.uniform(-9, 9)
        h = rnd.uniform(10, 30 if v == 0 else 22)
        a = rnd.uniform(-0.5, 0.5)
        w = rnd.uniform(2.5, 4.5)
        tx, ty = bx + math.sin(a) * h, 47 - math.cos(a) * h
        for k in range(int(h)):
            t = k / h
            cx, cy = bx + (tx - bx) * t, 47 + (ty - 47) * t
            ww = w * (1 - t) + 0.6
            for d in range(-int(ww) - 1, int(ww) + 2):
                if abs(d) > ww: continue
                side = d / max(ww, 0.5)
                vv = 0.5 - 0.35 * side + 0.35 * t
                s.set(cx + d, cy, pick(ICE, vv, cx + d, cy))
        s.set(tx, ty, ICE[8])
    return s.out(C('060a12'))


def drift():
    s = S(48, 48)
    for x in range(4, 44):
        h = 3 + 6 * math.sin((x - 4) / 40 * math.pi) ** 0.8 + math.sin(x * 0.7) * 0.8
        for y in range(int(48 - h), 48):
            t = (y - (48 - h)) / max(h, 1)
            s.set(x, y, pick(SNOW, 0.95 - t * 0.6 - (0.1 if x > 30 else 0), x, y))
    return s


def gauge_f():
    s = S(48, 48)
    s.disc(24, 38, 7, BRASS[2]); s.disc(24, 38, 5.5, SNOW[3])
    s.line(24, 38, 27, 34, C("8a1a14"))
    for a in range(200, 341, 35):
        r = math.radians(a)
        s.set(24 + math.cos(r) * 4.5, 38 + math.sin(r) * 4.5, K)
    s.rect(23, 45, 25, 47, IRONF[3])
    for x in range(18, 31):
        if h01(x, 9, 1) < 0.6: s.set(x, 31, SNOW[4])
    return s.out()


def sign_f(v):
    s = S(48, 48)
    s.shade_rect(23, 22, 25, 47, IRONF, 3)
    s.shade_rect(15, 12, 33, 23, ST, 6, grain=0.2, seed=2)
    if v == 1: s.line(24, 14, 24, 20, ICE[7]); s.line(21, 17, 24, 21, ICE[7]); s.line(27, 17, 24, 21, ICE[7])
    else: s.line(24, 21, 24, 14, ICE[7]); s.line(21, 17, 24, 13, ICE[7]); s.line(27, 17, 24, 13, ICE[7])
    for x in range(15, 34): s.set(x, 11, SNOW[4]); s.set(x, 12, SNOW[3] if x % 3 else SNOW[4])
    return s.out()


def lamp_f(f):
    s = S(48, 48)
    s.shade_rect(22, 10, 26, 47, IRONF, 3)
    s.shade_rect(18, 4, 30, 13, IRONF, 2)
    s.rect(20, 6, 28, 11, ICE[6 + (f % 2)]); s.rect(22, 7, 26, 10, ICE[8])
    for x in range(18, 31): s.set(x, 3, SNOW[4])
    return s.out()


def pump_f(W, H, seed):
    s = S(W, H)
    # a frozen pump engine: a riveted cylinder, a beam, a flywheel, icicles hanging off it all
    cx = W // 2 - 8
    s.shade_rect(cx - 16, H - 50, cx + 16, H - 1, IRONF, 3.5, grain=0.2, seed=seed)
    for y in range(H - 48, H - 2, 8):
        for x in range(cx - 14, cx + 15, 5): s.set(x, y, IRONF[6])
    s.shade_rect(cx - 20, H - 54, cx + 20, H - 49, IRONF, 5)
    s.shade_rect(cx - 3, H - 76, cx + 3, H - 54, IRONF, 4)
    s.line(cx - 28, H - 70, cx + 34, H - 80, IRONF[5], 3)                # the beam
    fx, fy, R = cx + 26, H - 26, 20
    for a in range(0, 360, 3):
        r = math.radians(a)
        for rr in (R, R - 1, R - 2):
            s.set(fx + math.cos(r) * rr, fy + math.sin(r) * rr, IRONF[5 if rr == R else 3])
    for a in range(0, 360, 45):
        r = math.radians(a)
        s.line(fx, fy, fx + math.cos(r) * (R - 2), fy + math.sin(r) * (R - 2), IRONF[4], 2)
    s.disc(fx, fy, 4, BRASS[3])
    s.out()
    # rime: snow on top surfaces, icicles under edges
    for x in range(W):
        for y in range(1, H):
            if s.get(x, y)[3] and not s.get(x, y - 1)[3] and h01(x, y, seed) < 0.85:
                s.set(x, y, SNOW[4]); s.set(x, y + 1, SNOW[2])
    rnd = random.Random(seed)
    for i in range(12):
        x = rnd.randint(4, W - 5)
        for y in range(H - 1, 0, -1):
            if s.get(x, y)[3] and not s.get(x, y + 1)[3] and y < H - 4:
                L = rnd.randint(3, 9)
                for k in range(L): s.set(x, y + 1 + k, ICE[7 - k * 6 // L])
                break
    return s


def arch():
    s = S(160, 128)
    # one bay of the old aqueduct: piers, a round arch, a frozen channel along its top
    for y in range(128):
        for x in range(160):
            inner = (x - 80) ** 2 / 50 ** 2 + (y - 96) ** 2 / 70 ** 2 < 1 and y > 34
            if inner: continue
            if y < 22: continue
            v = 0.45 + (vnoise(x, y, 8, 5, 5) - 0.5) * 0.35 + (0.12 if x < 80 else -0.08)
            if (y - 22) % 12 == 0: v -= 0.25
            if ((x + (8 if ((y - 22) // 12) % 2 else 0)) % 16) == 0: v -= 0.2
            s.set(x, y, pick(ST, v, x, y))
    for x in range(160):                                                 # the frozen channel
        for y in range(10, 22):
            s.set(x, y, pick(ICE, 0.35 + 0.35 * (1 - (y - 10) / 12) + math.sin(x * 0.3) * 0.05, x, y))
        s.set(x, 9, SNOW[4]); s.set(x, 10, SNOW[3])
    rnd = random.Random(3)
    for i in range(22):                                                  # icicles off the arch soffit
        x = rnd.randint(34, 126)
        for y in range(40, 128):
            if not s.get(x, y)[3] and s.get(x, y - 1)[3] and s.get(x, y - 1) != ICE[3]:
                L = rnd.randint(4, 14)
                for k in range(L): s.set(x, y + k, ICE[7 - min(6, k * 7 // L)])
                break
    for x in range(0, 160, 3):                                           # water frozen mid-spill over the edge
        L = int(4 + 20 * h01(x, 0, 9) ** 3)
        for k in range(L): s.set(x, 22 + k, ICE[6 - min(5, k // 3)])
    return s.out()


def arch2():
    s = S(160, 128)
    for y in range(24, 128):
        for x in range(40, 120):
            inner = (x - 80) ** 2 / 26 ** 2 + (y - 100) ** 2 / 50 ** 2 < 1 and y > 56
            if inner: continue
            v = 0.4 + (vnoise(x, y, 6, 4, 8) - 0.5) * 0.3 + (0.1 if x < 80 else -0.08)
            if (y - 24) % 10 == 0: v -= 0.25
            s.set(x, y, pick(ST, v, x, y))
    for x in range(40, 120): s.set(x, 24, SNOW[4]); s.set(x, 25, SNOW[3])
    return s.out()


def statue():
    s = S(160, 128)
    # a frozen knight on a plinth, sword planted, cloak stiff with ice: the aqueduct's warden, long dead
    cx = 80
    s.shade_rect(cx - 18, 112, cx + 18, 127, ST, 6, grain=0.2, seed=1)
    body = [(cx - 12, 112), (cx - 9, 60), (cx - 6, 40), (cx + 6, 40), (cx + 9, 60), (cx + 14, 112)]
    s.poly(body, ST[5])
    for y in range(40, 112):
        for x in range(cx - 14, cx + 15):
            if s.get(x, y) == ST[5]:
                s.set(x, y, pick(ST, 0.55 + (cx - x) / 40 + (vnoise(x, y, 3, 6, 2) - 0.5) * 0.25, x, y))
    s.ball(cx, 32, 7, ST, 0.3, 0.95)                                     # helm
    s.rect(cx - 5, 31, cx + 4, 32, K)
    s.shade_rect(cx - 17, 40, cx - 10, 46, ST, 6); s.shade_rect(cx + 10, 40, cx + 17, 46, ST, 6)   # pauldrons
    s.shade_rect(cx - 1, 50, cx + 1, 112, IRONF, 5)                      # the sword, point down
    s.shade_rect(cx - 7, 56, cx + 7, 58, IRONF, 5)
    s.out()
    for x in range(160):
        for y in range(1, 128):
            if s.get(x, y)[3] and s.get(x, y) != K and not s.get(x, y - 1)[3] and h01(x, y, 4) < 0.9:
                s.set(x, y, SNOW[4])
    for x in range(cx - 14, cx + 15, 3):
        L = int(3 + 8 * h01(x, 5, 3))
        for k in range(L): s.set(x, 47 + k, ICE[7 - min(6, k)])
    return s


def pump_big():
    s = S(160, 128)
    p = pump_f(96, 96, 21)
    s.paste(p, 32, 32)
    return s


# ======================================================================================================== ICONS
def icon_ink():
    s = S(16, 16)
    # a coil of golden root around a drop of ink
    for a in range(0, 330, 12):
        r = math.radians(a)
        rr = 5.5 - a / 330 * 2.5
        s.set(8 + math.cos(r) * rr, 8 + math.sin(r) * rr, GOLD[3] if a % 24 else GOLD[4])
    s.poly([(8, 3), (11, 9), (8, 12), (5, 9)], INK[3])
    s.set(7, 7, VIO[4]); s.set(7, 8, VIO[3]); s.set(9, 13, GOLD[4]); s.set(13, 4, GOLD[5])
    return s.out()


def icon_rime():
    s = S(16, 16)
    s.poly([(8, 14), (2, 7), (4, 3), (8, 5), (12, 3), (14, 7)], ICE[5])
    for y in range(16):
        for x in range(16):
            if s.get(x, y) == ICE[5]:
                s.set(x, y, pick(ICE, 0.35 + (8 - x) / 16 + (8 - y) / 20, x, y))
    s.disc(8, 8, 1.6, EMBER[3]); s.set(8, 8, EMBER[4])
    s.set(4, 5, ICE[8]); s.set(5, 4, ICE[8])
    return s.out(C('060a12'))


# ======================================================================================================== build
def sheet(name, w, h, frames, tags):
    """frames: list of (S | Image, ms); tags: [(name, a, b)]"""
    fr = []
    for img, ms in frames:
        im = img.img if isinstance(img, S) else img
        if im.size != (w, h):
            c = blank(w, h); c.alpha_composite(im, ((w - im.size[0]) // 2, h - im.size[1])); im = c
        fr.append({'ms': ms, 'cels': {'Art': im}})
    # preview strip (2x)
    strip = blank(w * len(fr), h)
    for i, f in enumerate(fr): strip.alpha_composite(f['cels']['Art'], (i * w, 0))
    bg = Image.new('RGBA', strip.size, (40, 40, 52, 255)); bg.alpha_composite(strip)
    scale(bg, 2).save(os.path.join(PREV, name + '.png'))
    if ASE:
        import asebuild
        asebuild.build(name, w, h, ['Art'], fr, tags)
    print(name, w, h, len(fr))


def build_all():
    sheet('xrb_mtree', 128, 160, [(dead_tree(128, 160, s), 1000) for s in (11, 23, 37)], [('t0', 0, 0), ('t1', 1, 1), ('t2', 2, 2)])
    sheet('xrb_mbig', 240, 272, [(weeping_tree(), 1000)], [('idle', 0, 0)])
    sheet('xrb_mhut', 112, 96, [(hut(0), 900), (hut(1), 140)], [('idle', 0, 1)])
    F, tags = [], []
    def add(tag, sprites, ms=160):
        tags.append((tag, len(F), len(F) + len(sprites) - 1)); F.extend((sp, ms) for sp in sprites)
    add('reeds0', [reeds(0, f) for f in range(3)], 260); add('reeds1', [reeds(1, f) for f in range(3)], 260)
    add('lily', [lily()]); add('mush', [mush(0), mush(1)], 700); add('lantpost', [lantpost(f) for f in range(3)], 150)
    add('stilt', [stilt()]); add('boat', [boat()]); add('net', [net()]); add('stakes', [stakes()])
    add('sign0', [sign(0)]); add('sign1', [sign(1)]); add('sign2', [sign(2)]); add('table', [table()]); add('posts', [posts()])
    add('valve', [valve_m()]); add('gauge', [gauge_m()]); add('moss0', [moss(0)]); add('moss1', [moss(1)]); add('pump', [pump_m()])
    sheet('xrb_mprop', 48, 48, F, tags)
    kinds = ['tl', 't', 'tr', 'l', 'm0', 'm1', 'm2', 'm3', 'r', 'bl', 'b', 'br', 'bk']
    sheet('xrb_ashelf', 16, 16, [(shelf_piece(k, 100 + i), 1000) for i, k in enumerate(kinds)], [(k, i, i) for i, k in enumerate(kinds)])
    F, tags = [], []
    add('note', [note()]); add('books0', [books(0)]); add('books1', [books(1)]); add('candles', [candles(f) for f in range(3)], 140)
    add('desk', [desk()]); add('card', [card()]); add('falseshelf', [falseshelf()])
    sheet('xrb_aprop', 48, 48, F, tags)
    sheet('xrb_acodex', 160, 176, [(codex(f), 220) for f in range(4)], [('idle', 0, 3)])
    sheet('xrb_awin', 96, 128, [(window(), 1000)], [('idle', 0, 0)])
    sheet('xrb_amural', 128, 64, [(mural(), 1000)], [('idle', 0, 0)])
    F, tags = [], []
    add('valve', [valve_f()]); add('crystal0', [crystal(0)]); add('crystal1', [crystal(1)]); add('drift', [drift()])
    add('gauge', [gauge_f()]); add('sign0', [sign_f(0)]); add('sign1', [sign_f(1)]); add('lamp', [lamp_f(f) for f in range(2)], 500)
    sheet('xrb_fprop', 48, 48, F, tags)
    sheet('xrb_fbig', 160, 128, [(arch(), 1000), (pump_big(), 1000), (statue(), 1000), (arch2(), 1000)],
          [('arch', 0, 0), ('pump', 1, 1), ('statue', 2, 2), ('arch2', 3, 3)])
    sheet('xrb_icons', 16, 16, [(icon_ink(), 1000), (icon_rime(), 1000)], [('c_x3_ink', 0, 0), ('c_x3_rime', 1, 1)])


if __name__ == '__main__':
    build_all()
