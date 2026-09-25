"""FX + props for The Unwritten's arena (built by art/gen_unwritten.py).

fx_ink_bolt     14x14  v(4 loop) r(4 loop)        glossy ink droplet with a bright rim (violet / phase-2 crimson)
fx_ink_quill    20x8   v(2 loop) r(2 loop)        homing quill, flying RIGHT (engine rotates it), bright nib
fx_ink_splash   24x24  v(6) r(6)                  bolt impact: blot + flung droplets
fx_ink_tendril  24x80  v(11) r(11)  pivot bottom  0-3 telegraph (ink pool + rising sparks), 4 erupt, 5-7 full
                                                  (hazard active 4-7), 8-10 retract
fx_ink_burst    64x40  v(8) r(8)    pivot bottom  ink crown splash (the boss sinking / rising)
fx_ink_page     12x12  v(6 loop) r(6 loop)        tumbling torn page (orbit, drifting pages, page storm)
fx_ink_pool     16x12  tele(4) loop(4) r_tele(4) r_loop(4)  tileable floor-flood strip, pivot bottom
ar2_inkplat     48x10  write(6) loop(4) fade(5)   a written ink platform (a thick calligraphic stroke)
ar2_book        40x48  idle(4 loop) bleed(8) empty(1)  the Scribe's unfinished book on a lectern
ar2_bookshelf   32x64  idle(1) creak(4 loop)      a tall, top-heavy bookcase; creak = books rattling (the engine rocks + topples it)
All pixel-clean; FX use only the stepped alphas 70/130/190/255.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import unwritten_rig as R  # noqa: E402

C = R.C
RGBA = C.RGBA
PV = os.path.join(ART, "previews")
STEPS = (70, 130, 190, 255)


def col(k, a=255):
    a = min(STEPS, key=lambda s: abs(s - a))
    return RGBA[k][:3] + (a,)


class Can:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def set(self, x, y, k, a=255, under=False):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if under and self.px[x, y][3]:
                return
            self.px[x, y] = col(k, a)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return (0, 0, 0, 0)

    def outline(self, k="OUT"):
        pts = [(x, y) for y in range(self.h) for x in range(self.w) if self.px[x, y][3] == 255]
        solid = set(pts)
        for (x, y) in pts:
            for a, b in C.N4:
                q = (x + a, y + b)
                if q not in solid and 0 <= q[0] < self.w and 0 <= q[1] < self.h and self.px[q][3] < 255:
                    self.px[q] = col(k)


def pal(ph):
    """(glow0, glow1, glow2, hot, white) for the phase"""
    return ("V0", "V1", "V2", "V3", "V4") if ph == "v" else ("R0", "R1", "R2", "R4", "R5")


# =========================================================================== bolt
def bolt(ph):
    out = []
    g0, g1, g2, g3, g4 = pal(ph)
    for f in range(4):
        c = Can(14, 14)
        cx = cy = 6.5
        rr = 3.6 + 0.35 * math.sin(f * math.pi / 2)
        for y in range(14):
            for x in range(14):
                d = math.hypot(x + .5 - 7, y + .5 - 7)
                ang = math.atan2(y + .5 - 7, x + .5 - 7)
                if d < rr - 1.1:
                    lit = (x + y) < 12
                    c.set(x, y, "K2" if lit else "K1")
                elif d < rr:
                    c.set(x, y, g4 if -2.7 < ang < -1.2 else g3 if -3.2 < ang < 0.2 else g2)
                elif d < rr + 1.0:
                    c.set(x, y, g1, 190)
                elif d < rr + 2.3 and (f + int((ang + 3.2) * 2)) % 2 == 0:
                    c.set(x, y, g0, 130)
        c.set(5, 5, g4); c.set(6, 5, g3)
        out.append((90, c.img))
    return out


def quill(ph):
    out = []
    g0, g1, g2, g3, g4 = pal(ph)
    for f in range(2):
        c = Can(20, 8)
        # vane: two tapered sides of a dark feather along y = 3.5, from x=1 to x=13
        for x in range(1, 14):
            t = (x - 1) / 12
            w = 0.6 + 2.6 * math.sin(t * math.pi) ** 0.8
            up = w + (0.4 if f else 0) * math.sin(x)
            for y in range(8):
                dy = y + .5 - 3.5
                if -up <= dy <= w * 0.8:
                    edge = dy <= -up + 1 or dy >= w * 0.8 - 1
                    k = g1 if (edge and dy < 0) else "K3" if dy < 0 else "K1"
                    if not edge and (x + y) % 3 == 0:
                        k = "K2"
                    c.set(x, y, k)
        for x in range(0, 15):
            c.set(x, 3, "K4" if x < 13 else "D4")          # shaft
        # nib
        for x, y, k in ((14, 3, "S3"), (15, 3, "S4"), (16, 3, g3), (17, 3, g4), (18, 3, g4), (15, 2, "S2"), (15, 4, "S1"),
                        (16, 4, g2), (16, 2, g2)):
            c.set(x, y, k)
        c.outline()
        c.set(19, 3, g2, 190)
        c.set(0, 2, g0, 130); c.set(0, 4, g0, 130)
        out.append((80, c.img))
    return out


def splash(ph):
    out = []
    g0, g1, g2, g3, g4 = pal(ph)
    for f in range(6):
        c = Can(24, 24)
        k = f / 5
        rb = 4.5 * (1 - k) + 0.5
        for y in range(24):
            for x in range(24):
                d = math.hypot(x + .5 - 12, y + .5 - 12)
                if d < rb:
                    c.set(x, y, "K2" if d < rb - 1 else g2 if f < 3 else g1)
        for i in range(10):
            a = 2 * math.pi * i / 10 + 0.3
            d = 3 + 9 * k * (0.7 + 0.5 * C.hash01(i, 1, 3))
            x, y = 12 + math.cos(a) * d, 12 + math.sin(a) * d + 3 * k * k
            if f < 5:
                c.set(x, y, g3 if f < 2 else g2)
                c.set(x - math.cos(a), y - math.sin(a), "K3", 190)
        if f < 2:
            for i in range(8):
                a = 2 * math.pi * i / 8
                c.set(12 + math.cos(a) * (6 + 2 * f), 12 + math.sin(a) * (6 + 2 * f), g4 if f == 0 else g3, 190)
        out.append((50 if f < 2 else 70, c.img))
    return out


# =========================================================================== tendril
def draw_tendril(c, h, sway, ph, seed=0):
    g0, g1, g2, g3, g4 = pal(ph)
    base = 78
    pts = []
    for yy in range(int(h) + 1):
        t = yy / max(1, h)
        cx = 11.5 + sway * math.sin(t * math.pi * 1.1 + seed) * 2.2
        if t > 0.72:
            cx += (t - 0.72) ** 2 * 60            # the tip hooks forward like a nib
        w = 1.0 + 4.6 * (1 - t) ** 0.85
        pts.append((base - yy, cx, w, t))
    for (y, cx, w, t) in pts:
        for x in range(24):
            dx = x + .5 - cx
            if abs(dx) > w:
                continue
            f = dx / w
            k = "K5" if f < -0.62 else "K4" if f < -0.25 else "K3" if f < 0.15 else "K2" if f < 0.6 else g1
            if t > 0.9:
                k = g3 if f < 0.2 else g2
            c.set(x, y, k)
    for (y, cx, w, t) in pts[4:-6:7]:                     # a column of little glyphs down its spine
        c.set(cx, y, g1)
        c.set(cx + 0.8, y - 1, g1)
    c.outline()
    if pts:
        y, cx, w, t = pts[-1]
        c.set(cx, y - 1, g4)
        c.set(cx + 1, y, g3)


def pool(c, rx, ph, glow, ry=2.4, y0=78):
    g0, g1, g2, g3, g4 = pal(ph)
    for y in range(c.h):
        for x in range(c.w):
            e = ((x + .5 - 12) / rx) ** 2 + ((y + .5 - y0) / ry) ** 2
            if e <= 1.0:
                if e > 0.62:
                    c.set(x, y, g3 if (glow and y < y0) else g2 if y < y0 else g1)
                else:
                    c.set(x, y, "K1")


def tendril(ph):
    out = []
    g0, g1, g2, g3, g4 = pal(ph)
    tele = [(3, 0.3), (5.5, 0.6), (8, 0.8), (10, 1.0)]
    for f, (rx, gl) in enumerate(tele):
        c = Can(24, 80)
        pool(c, rx, ph, f % 2 == 1)
        for i in range(2 + f):                              # glyph sparks lifting off the pool: the warning
            yy = 74 - ((f * 7 + i * 11) % 22)
            xx = 12 + (C.hash01(i, f, 5) - 0.5) * rx * 1.6
            c.set(xx, yy, g3 if i % 2 else g2, 255 if yy > 60 else 190)
            c.set(xx, yy + 1, g1, 130)
        for k in range(3):                                  # a faint column of light above: where it will rise
            c.set(12, 70 - k * 9 - f * 2, g1, 70 + 60 * (f >= 2))
        out.append((180, c.img))
    for f, (h, sw) in enumerate(((30, 0.4), (66, 0.9), (64, -0.6), (60, 0.3), (40, -0.2), (18, 0.1), (5, 0))):
        c = Can(24, 80)
        pool(c, 10 - max(0, f - 4) * 2, ph, f < 2)
        if h > 6:
            draw_tendril(c, h, sw, ph, seed=f * 0.3)
        if f == 0:
            for i in range(8):
                a = math.pi * (0.1 + 0.8 * i / 7)
                c.set(12 + math.cos(a) * 11, 76 - math.sin(a) * 8, "K3")
                c.set(12 + math.cos(a) * 12, 75 - math.sin(a) * 10, g2, 190)
        if f >= 4:
            for i in range(3):
                c.set(9 + i * 3, 78 - h - 3 + i * 5 + f, "K3")
        out.append(((50, 80, 100, 100, 70, 70, 90)[f], c.img))
    return out


def burst(ph):
    out = []
    g0, g1, g2, g3, g4 = pal(ph)
    drops = [(math.cos(a) * s, -abs(math.sin(a)) * s * 1.4) for a, s in
             ((math.pi * (0.08 + 0.84 * C.hash01(i, 2, 7)), 30 + 50 * C.hash01(i, 3, 7)) for i in range(28))]
    for f in range(8):
        c = Can(64, 40)
        t = (f + 0.6) / 7 * 0.9
        # the ink column (first frames)
        colh = (10, 22, 26, 18, 8, 0, 0, 0)[f]
        for yy in range(colh):
            w = 4.5 * (1 - yy / max(1, colh)) + 1.5
            for x in range(64):
                dx = x + .5 - 32
                if abs(dx) < w:
                    c.set(x, 38 - yy, "K4" if dx < -w * 0.4 else "K2" if dx < w * 0.5 else g1)
        for i, (vx, vy) in enumerate(drops):
            x = 32 + vx * t
            y = 38 + vy * t + 90 * t * t
            if y < 39 and f < 7:
                c.set(x, y, "K3")
                c.set(x, y - 1, g2 if i % 3 else g3, 190)
                if f < 3:
                    c.set(x - vx * 0.02, y + 1, "K2", 190)
        rx = (8, 14, 18, 20, 20, 18, 14, 9)[f]
        for x in range(64):
            for y in range(34, 40):
                e = ((x + .5 - 32) / rx) ** 2 + ((y + .5 - 38) / 2.2) ** 2
                if e <= 1:
                    c.set(x, y, g2 if e > 0.6 and y < 38 else "K1", 255 if f < 6 else 190)
        out.append(((50, 60, 70, 80, 90, 90, 100, 110)[f], c.img))
    return out


def page(ph):
    out = []
    for f in range(6):
        c = Can(12, 12)
        a = f / 6 * 2 * math.pi
        sq = math.cos(a)
        tilt = math.radians(20 * math.sin(a * 0.5) + 15)
        ca, sa = math.cos(tilt), math.sin(tilt)
        poly = []
        for (u, v) in ((-3, -4), (2, -4), (3, -3), (3, 4), (0.5, 3.6), (-1, 4.3), (-3, 4)):
            u2 = u * max(0.25, abs(sq))
            poly.append((6 + u2 * ca - v * sa, 6 + u2 * sa + v * ca))
        m = C.poly_mask(poly)
        front = sq > 0
        for (x, y) in m:
            k = ("P4" if front else "P3") if (x + y) % 5 else ("P3" if front else "P2")
            if ph == "r" and C.hash01(x, y, f) > 0.7:
                k = "R3"
            c.set(x, y, k)
        for (x, y) in m:
            if (x + 1, y) not in m or (x, y + 1) not in m:
                c.set(x, y, "P2" if ph == "v" else "R2")
        if abs(sq) > 0.5:
            for r in (-1.5, 1):
                for u in range(-1, 2):
                    q = (6 + u * abs(sq) * ca - r * sa, 6 + u * abs(sq) * sa + r * ca)
                    if (int(q[0]), int(q[1])) in m:
                        c.set(q[0], q[1], "P1")
        c.outline()
        if ph == "r":
            c.set(2, 1, "R4", 190); c.set(9, 2, "R3", 130)
        out.append((90, c.img))
    return out


def pool_strip(kind, ph):
    out = []
    g0, g1, g2, g3, g4 = pal(ph)
    for f in range(4):
        c = Can(16, 12)
        a = f / 4 * 2 * math.pi
        if kind == "tele":
            for x in range(16):
                c.set(x, 11, g1, 190)
                if (x + f * 3) % 8 in (0, 1, 3):
                    c.set(x, 10, g2 if (x + f) % 4 else g3, 190)
                if (x * 7 + f * 5) % 16 == 3:
                    c.set(x, 8 - f % 2, g3, 130)
        else:
            for x in range(16):
                top = 4 + 1.2 * math.sin(2 * math.pi * x / 16 + a) + 0.6 * math.sin(2 * math.pi * x / 8 - a)
                for y in range(int(top), 12):
                    k = "K1" if y > top + 2 else "K2"
                    if y == int(top):
                        k = g2 if math.sin(2 * math.pi * x / 16 + a) > 0.3 else "K4"
                    c.set(x, y, k)
            for x in range(16):
                if (x + f * 4) % 16 in (2, 3, 4):
                    c.set(x, 7, "K3")
        out.append((120, c.img))
    return out


# =========================================================================== platform
def plat_base(ph="v"):
    """a thick stroke of ink, calligraphic: fat middle, tapering ends; drips below; glyphs on its face"""
    g0, g1, g2, g3, g4 = pal(ph)
    c = Can(48, 10)
    for x in range(48):
        t = x / 47
        th = 2.5 + 3.2 * math.sin(math.pi * min(1, max(0, (t - 0.02) / 0.96))) ** 0.6
        y0 = 0 + (1 if x < 3 or x > 44 else 0)
        for y in range(y0, int(y0 + th) + 1):
            k = "K4" if y == y0 else "K3" if y == y0 + 1 else "K2" if y < y0 + th - 1 else "K1"
            c.set(x, y, k)
        c.set(x, y0, g2 if 3 < x < 44 else "K5")
    for x in (8, 19, 30, 39):
        c.set(x, 7, "K2"); c.set(x, 8, "K1")
    c.outline()
    for x in range(6, 42, 5):
        c.set(x, 3, g1); c.set(x + 1, 3, g1); c.set(x + 1, 4, g1)
    return c


def inkplat():
    frames = []
    base = plat_base()
    for f in range(6):
        c = Can(48, 10)
        lim = int(48 * (f + 1) / 6)
        for y in range(10):
            for x in range(min(48, lim)):
                c.px[x, y] = base.px[x, y]
        if f < 5:
            for y in range(0, 6):
                c.set(lim, y, "V4" if y < 3 else "V3")
            c.set(lim + 1, 1, "V2", 190)
        frames.append((45, c.img))
    loop = []
    for f in range(4):
        c = Can(48, 10)
        c.img.alpha_composite(base.img)
        c.px = c.img.load()
        for i, x in enumerate((8, 19, 30, 39)):
            L = (f + i) % 4
            if L >= 2:
                c.set(x, 9, "K2")
        for x in range(6, 42, 5):
            if (x // 5 + f) % 4 == 0:
                c.set(x, 3, "V2"); c.set(x + 1, 4, "V2")
        loop.append((140, c.img))
    fade = []
    for f in range(5):
        c = Can(48, 10)
        k = (f + 1) / 6
        for y in range(10):
            for x in range(48):
                p = base.px[x, y]
                if not p[3]:
                    continue
                h = C.vnoise(x / 2.5, 13) * 0.7 + C.hash01(x, y, 9) * 0.3
                if h < k:
                    continue
                if h < k + 0.12:
                    c.set(x, y, "V2", 190)
                else:
                    c.px[x, y] = p
        fade.append((90, c.img))
    return frames + loop + fade, [("write", 0, 5), ("loop", 6, 9), ("fade", 10, 14)]


# =========================================================================== the Scribe's book
def book():
    import archives_props as AP
    _, _, _, lfr, _ = AP.lectern()
    base = [f["cels"]["Lectern"] for f in lfr]
    out = []

    def frame(i):
        c = Can(40, 48)
        c.img.alpha_composite(base[i % 4], (4, 16))
        c.px = c.img.load()
        return c

    def wet_page(c, f):
        # the right-hand page is wet with fresh ink: a glossy black field, one violet glint
        for x in range(20 + 4, 29):
            for y in range(26, 31):
                if C.hash01(x, y, 2) > 0.25 or x < 27:
                    c.set(x, y, "K1" if (x + y + f) % 7 else "K3")
        c.set(24 + f % 3, 27, "V2")

    for f in range(4):                                  # idle: the last page is still wet; a single drip
        c = frame(f)
        wet_page(c, f)
        for yy in range(31, 31 + (f % 4) * 2 + 1):
            c.set(28, yy, "K2")
        c.set(28, 31 + (f % 4) * 2 + 1, "V1", 190)
        out.append((160, c.img))
    for f in range(8):                                  # bleed: ink wells up, spills, runs to the floor
        c = frame(f)
        wet_page(c, f)
        mound = (3, 6, 9, 11, 10, 8, 6, 5)[f]
        for y in range(mound):
            w = 7 * (1 - y / max(1, mound)) ** 0.7 + 1
            for x in range(40):
                dx = x + .5 - 24
                if abs(dx) < w:
                    c.set(x, 28 - y, "K3" if dx < -w * 0.3 else "K1" if dx < w * 0.6 else "V1")
        c.set(22, 28 - mound, "V3"); c.set(23, 28 - mound + 1, "V2")
        run = max(0, f - 2)
        for i, x in enumerate((9, 30, 17)):
            ln = min(20, run * (6 + 2 * i))
            for yy in range(30, 30 + ln):
                if yy < 48:
                    c.set(x + (yy - 30) // 9, yy, "K2" if yy % 3 else "K1")
            if ln:
                c.set(x + (29 + ln) // 9 - 3, 30 + ln, "V2", 190)
        if f >= 5:
            rx = (f - 4) * 6
            for x in range(40):
                for y in range(45, 48):
                    e = ((x + .5 - 20) / rx) ** 2 + ((y + .5 - 47) / 1.8) ** 2
                    if e <= 1:
                        c.set(x, y, "V2" if e > 0.55 and y < 47 else "K1")
        for i in range(2 + f):
            a = C.hash01(i, f, 4) * math.pi
            d = 4 + f * 2 * C.hash01(i, f, 5)
            c.set(24 + math.cos(a) * d, 26 - math.sin(a) * d - f, "V3" if i % 2 else "V2", 190)
        out.append(((140, 140, 130, 120, 110, 110, 120, 200)[f], c.img))
    c = frame(0)                                        # empty: the pages are blank, only stains remain
    for x in range(11, 29):
        for y in range(25, 31):
            p = c.get(x, y)
            if p[3] and (p[0] + p[1] + p[2]) > 200:
                c.set(x, y, "P3" if C.hash01(x, y, 6) > 0.12 else "K2")
    for x, y in ((12, 5), (16, 3), (21, 2), (26, 6)):   # the rising glyphs of the base lectern are gone
        for yy in range(0, 26):
            p = c.get(x + 4, yy)
    for yy in range(0, 26):
        for x in range(40):
            if c.get(x, yy)[3] and yy < 24:
                c.px[x, yy] = (0, 0, 0, 0)
    out.append((1000, c.img))
    return out, [("idle", 0, 3), ("bleed", 4, 11), ("empty", 12, 12)]



# =========================================================================== a top-heavy bookcase (falling-shelf hazard)
def bookshelf():
    from envlib import h01
    from archives_tiles import OAK, BOOKS, PARCH, GOLD, IRON
    from env_props import Spr

    def draw(f):
        s = Spr(32, 64)
        lean = 0   # the engine rocks and topples the case; frames only rattle the books
        for y in range(4, 64):
            dx = round(lean * (64 - y) / 60)                 # the creak: the case rocks on its feet
            for x in range(6, 26):
                xx = x + dx
                if x in (6, 7) or x in (24, 25):            # side posts
                    s.set(xx, y, OAK[5] if x == 6 else OAK[4] if x == 7 else OAK[3] if x == 24 else OAK[2])
                elif y in (4, 5, 6):                         # carved crown, overhanging
                    s.set(xx, y, OAK[6] if y == 4 else OAK[4])
                elif (y - 7) % 11 == 10 or y >= 61:          # shelf boards
                    s.set(xx, y, OAK[5] if (y - 7) % 11 == 10 else OAK[3])
                else:
                    s.set(xx, y, OAK[1])
            for x in (5, 26):
                for y in range(2, 7):
                    s.set(x + dx, y, OAK[4])
            s.set(15 + dx, 2, GOLD[3]); s.set(16 + dx, 2, GOLD[2]); s.set(16 + dx, 3, OAK[5])
            # books: spines of uneven height and colour, one shelf half empty, a fallen tome leaning
            for sh in range(5):
                base = 7 + sh * 11 + 9
                x = 8
                i = 0
                while x < 24:
                    w = 1 + int(h01(sh, i, 11) * 2.2)
                    hgt = 6 + int(h01(sh, i, 12) * 3) + (1 if f and h01(sh, i, 20 + f) > 0.6 else 0)
                    if sh == 2 and x > 17:
                        break
                    b = BOOKS[int(h01(sh, i, 13) * len(BOOKS)) % len(BOOKS)]
                    for bx in range(x, min(24, x + w)):
                        for by in range(base - hgt, base + 1):
                            dxx = round(lean * (64 - by) / 60)
                            c = b[2] if bx == x else b[1] if bx < x + w - 1 else b[0]
                            if by == base - hgt + 2 and w > 1:
                                c = GOLD[2]
                            s.set(bx + dxx, by, c)
                    x += w
                    i += 1
            # iron brackets
            for y in (20, 42):
                s.set(6 + round(lean * (64 - y) / 60), y, IRON[5]); s.set(25 + round(lean * (64 - y) / 60), y, IRON[3])
        s.outline()
        return s.img
    frames = [(1000, draw(0))] + [(90, draw(f)) for f in (1, 2, 3, 4)]
    return frames, [("idle", 0, 0), ("creak", 1, 4)]

# =========================================================================== build
def sheets():
    S = {}
    S["fx_ink_bolt"] = (14, 14, bolt("v") + bolt("r"), [("v", 0, 3), ("r", 4, 7)])
    S["fx_ink_quill"] = (20, 8, quill("v") + quill("r"), [("v", 0, 1), ("r", 2, 3)])
    S["fx_ink_splash"] = (24, 24, splash("v") + splash("r"), [("v", 0, 5), ("r", 6, 11)])
    S["fx_ink_tendril"] = (24, 80, tendril("v") + tendril("r"), [("v", 0, 10), ("r", 11, 21)])
    S["fx_ink_burst"] = (64, 40, burst("v") + burst("r"), [("v", 0, 7), ("r", 8, 15)])
    S["fx_ink_page"] = (12, 12, page("v") + page("r"), [("v", 0, 5), ("r", 6, 11)])
    S["fx_ink_pool"] = (16, 12, pool_strip("tele", "v") + pool_strip("loop", "v") + pool_strip("tele", "r") + pool_strip("loop", "r"),
                        [("tele", 0, 3), ("loop", 4, 7), ("r_tele", 8, 11), ("r_loop", 12, 15)])
    fr, tg = inkplat()
    S["ar2_inkplat"] = (48, 10, fr, tg)
    fr, tg = book()
    S["ar2_book"] = (40, 48, fr, tg)
    fr, tg = bookshelf()
    S["ar2_bookshelf"] = (32, 64, fr, tg)
    return S


def preview(S, path, scale=4):
    rows = []
    for name, (w, h, frs, tags) in S.items():
        rows.append((name, w, h, frs))
    Wd = max(len(f) * (w * scale + 3) for _, w, h, f in rows) + 110
    Hd = sum(h * scale + 8 for _, w, h, f in rows)
    sh = Image.new("RGBA", (Wd, Hd), (40, 40, 46, 255))
    dr = ImageDraw.Draw(sh)
    y = 0
    for name, w, h, frs in rows:
        dr.text((4, y + 4), name, fill=(220, 210, 230))
        for i, (ms, im) in enumerate(frs):
            bg = Image.new("RGBA", (w, h), (92, 92, 98, 255) if i % 2 == 0 else (22, 20, 28, 255))
            bg.alpha_composite(im)
            sh.alpha_composite(bg.resize((w * scale, h * scale), Image.NEAREST), (110 + i * (w * scale + 3), y))
        y += h * scale + 8
    sh.save(path)


def build_all(build=True):
    S = sheets()
    os.makedirs(PV, exist_ok=True)
    preview(S, os.path.join(PV, "unwritten_fx.png"))
    if not build:
        return
    import asebuild
    for name, (w, h, frs, tags) in S.items():
        asebuild.build(name, w, h, ["FX"], [{"ms": ms, "cels": {"FX": im}} for ms, im in frs], tags)
        print("built", name)


if __name__ == "__main__":
    build_all("--preview" not in sys.argv)
