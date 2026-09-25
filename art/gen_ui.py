#!/usr/bin/env python3
"""UI icons (ART_SPEC section 3) -> art/ui_icons.aseprite + assets/ui_icons.png/.json
                                  art/ui_frame.aseprite + assets/ui_frame.png/.json

ui_icons: 16x16 frames, ONE tag per icon, one frame each (order = ICONS below).
ui_frame: 24x24, single tag `frame`: ornate gold-on-black node frame, transparent 16x16 centre.

Icons are drawn with small vector-ish primitives on a 16x16 grid, then get the house 1px
near-black outline automatically. Readable at 1x: one strong silhouette per icon, lit from
the upper-left, metal/bone bodies with gold / crimson / azure accents.
Layers: Icon (the drawn shape) + Outline (auto 1px outline), so the outline can be recoloured.
Re-runnable: python3 art/gen_ui.py
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402

S = 16
PAL = {
    'K': (8, 7, 12),
    # steel
    '1': (33, 32, 48), '2': (52, 53, 74), '3': (84, 90, 118), '4': (150, 162, 196), '5': (205, 214, 236),
    'W': (255, 248, 230),
    # gold
    'g': (96, 54, 18), 'G': (170, 110, 40), 'y': (240, 170, 60), 'Y': (255, 210, 120),
    # crimson
    'm': (62, 6, 18), 'r': (150, 20, 40), 'R': (240, 36, 50), 'P': (255, 128, 118),
    # azure
    'b': (22, 36, 84), 'a': (40, 82, 168), 'A': (82, 152, 232), 'c': (170, 222, 255),
    # bone / parchment
    't': (112, 92, 72), 'u': (186, 164, 126), 'v': (232, 216, 180),
    # stone
    's': (62, 58, 72), 'S': (104, 98, 112),
    # glass
    'e': (70, 76, 100),
}


class Icon:
    def __init__(self):
        self.g = [[None] * S for _ in range(S)]

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < S and 0 <= y < S:
            self.g[y][x] = c

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < S and 0 <= y < S else None

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for i in range(n + 1):
            t = i / max(1, n)
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def ell(self, cx, cy, rx, ry, fn):
        """fn(nx, ny) -> colour or None, nx/ny in -1..1 (for shading from the upper-left)."""
        for y in range(S):
            for x in range(S):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if nx * nx + ny * ny <= 1.0:
                    c = fn(nx, ny)
                    if c:
                        self.g[y][x] = c

    def poly(self, pts, fn):
        """Fill polygon; fn(x, y) -> colour."""
        img = Image.new("L", (S, S), 0)
        ImageDraw.Draw(img).polygon(pts, fill=255)
        for y in range(S):
            for x in range(S):
                if img.getpixel((x, y)):
                    c = fn(x, y) if callable(fn) else fn
                    if c:
                        self.g[y][x] = c

    def rows(self, x0, y0, rows):
        """Stamp ASCII rows ('.' = skip)."""
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch != '.':
                    self.px(x0 + i, y0 + j, ch)

    def images(self):
        body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        for y in range(S):
            for x in range(S):
                c = self.g[y][x]
                if c:
                    body.putpixel((x, y), PAL[c] + (255,))
        for y in range(S):
            for x in range(S):
                if self.g[y][x] is None and any(self.get(x + a, y + b) not in (None, 'K')
                                                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out.putpixel((x, y), PAL['K'] + (255,))
        return body, out


def shade(lit, mid, dark, bias=0.0):
    """Sphere-ish shading from the upper-left for ell()."""
    def f(nx, ny):
        v = -0.7 * nx - 0.7 * ny + bias
        return lit if v > 0.45 else (mid if v > -0.35 else dark)
    return f


# ---------------------------------------------------------------- shared drawings
def sword(ic, tip, base, guard_w=2, blade=('5', '3'), hilt='G', pommel='y'):
    """Diagonal/straight sword: blade from base -> tip, 2px wide (lit edge + flat)."""
    (tx, ty), (bx, by) = tip, base
    L = math.hypot(tx - bx, ty - by)
    dx, dy = (tx - bx) / L, (ty - by) / L
    px_, py_ = -dy, dx
    lit_side = 1 if (px_ + py_) < 0 else -1          # side facing the upper-left gets the lit edge
    n = int(L * 2)
    for i in range(n + 1):
        t = i / n
        x, y = bx + (tx - bx) * t, by + (ty - by) * t
        ic.px(x, y, blade[1])
        if t < 0.92:
            ic.px(x + px_ * lit_side * 0.9, y + py_ * lit_side * 0.9, blade[0])
    ic.px(tx, ty, 'W')
    for s in range(-guard_w, guard_w + 1):
        ic.px(bx + px_ * s, by + py_ * s, hilt if abs(s) < guard_w else 'g')
    ic.px(bx - dx * 1.2, by - dy * 1.2, 't')
    ic.px(bx - dx * 2.2, by - dy * 2.2, 't')
    ic.px(bx - dx * 3.3, by - dy * 3.3, pommel)


def sparkle(ic, x, y, big=False, c='W', c2='Y'):
    ic.px(x, y, c)
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ic.px(x + a, y + b, c2)
        if big:
            ic.px(x + 2 * a, y + 2 * b, c2)


def flask(ic, liquid):
    """Round-bottomed flask. liquid = (lit, mid, dark, deep)."""
    L1, L2, L3, L4 = liquid
    # bulb
    ic.ell(8, 10, 5.4, 4.8, lambda nx, ny: (L1 if (-0.8 * nx - 0.6 * ny) > 0.45 else
                                          (L2 if (-0.8 * nx - 0.6 * ny) > -0.25 else (L3 if ny < 0.55 else L4)))
           if ny > -0.35 else 'e')
    # neck + rim + cork
    ic.rect(6, 3, 9, 5, 'e')
    ic.px(6, 4, '3'); ic.px(6, 5, '3')
    ic.rect(5, 3, 10, 3, '3')
    ic.px(5, 3, '4')
    ic.rect(6, 1, 9, 2, 'G')
    ic.px(6, 1, 'y'); ic.px(7, 1, 'y')
    # glass highlight
    ic.px(5, 8, 'W'); ic.px(4, 9, 'c' if L2 == 'A' else 'P'); ic.px(5, 9, L1)
    # surface line of the liquid
    for x in range(4, 13):
        if ic.get(x, 7) and ic.get(x, 7) != 'e':
            ic.px(x, 7, L1)


# ================================================================ skill nodes
def keen_edge():
    ic = Icon()
    # long blade with a honed white edge and a gleam travelling along it
    sword(ic, (14, 1), (5, 10), guard_w=2)
    ic.line(13, 2, 7, 8, 'W')
    sparkle(ic, 10, 3, big=True)
    return ic


def fourth_strike():
    ic = Icon()
    # three quick silver cuts, then the big golden fourth crescent
    for i in range(3):
        y = 2 + i * 3
        ic.line(1, y + 1, 4, y, '4')
        ic.px(4, y, '5')
    for i in range(60):
        t = i / 59
        a = math.radians(110 - 150 * t)
        th = 2.4 * math.sin(math.pi * min(1, t ** 0.8))
        for k in range(int(th) + 1):
            r = 7.2 - k
            c = 'W' if k == 0 and 0.3 < t < 0.8 else ('Y' if k == 0 else ('y' if k == 1 else 'G'))
            ic.px(6 + math.cos(a) * r, 8 - math.sin(a) * r, c)
    return ic


def charged_arts():
    ic = Icon()
    # radiating gold charge behind an upright blade
    for (x0, y0, x1, y1) in ((2, 4, 5, 7), (13, 4, 10, 7), (1, 9, 4, 9), (14, 9, 11, 9), (3, 13, 5, 11), (12, 13, 10, 11)):
        ic.line(x0, y0, x1, y1, 'y')
    ic.px(2, 4, 'Y'); ic.px(13, 4, 'Y'); ic.px(1, 9, 'Y'); ic.px(14, 9, 'Y')
    ic.rect(7, 2, 8, 11, '3')
    ic.line(7, 2, 7, 10, '5')
    ic.px(7, 1, 'W'); ic.px(8, 1, '4')
    ic.rect(5, 11, 10, 11, 'G'); ic.px(5, 11, 'g'); ic.px(10, 11, 'g')
    ic.rect(7, 12, 8, 13, 't')
    ic.rect(7, 14, 8, 14, 'y')
    return ic


def riposte_mastery():
    ic = Icon()
    # crimson critical burst at the tip of a horizontal thrust
    ic.ell(11, 7.5, 3.6, 3.6, lambda nx, ny: 'R' if nx * nx + ny * ny > 0.3 else 'P')
    for (x, y) in ((11, 2), (11, 13), (15, 7), (14, 4), (14, 11), (8, 3), (8, 12)):
        ic.line(11, 7, x, y, 'R')
    ic.px(11, 7, 'W'); ic.px(12, 7, 'W')
    ic.rect(1, 7, 12, 8, '3')
    ic.line(1, 7, 11, 7, '5')
    ic.px(13, 7, 'W')
    ic.rect(3, 5, 3, 10, 'G'); ic.px(3, 5, 'y')
    ic.rect(1, 7, 2, 8, 't')
    ic.px(0, 7, 'y')
    return ic


def bloodthirst():
    ic = Icon()
    # blood drop with two fangs biting into it
    ic.poly([(8, 1), (13, 9), (13, 11), (11, 14), (5, 14), (3, 11), (3, 9)],
            lambda x, y: 'P' if (x < 7 and 6 < y < 11 and x > 4) else
            ('R' if x + y < 17 else ('r' if x + y < 22 else 'm')))
    ic.px(5, 8, 'W'); ic.px(5, 9, 'P')
    # fangs
    for fx in (6, 10):
        ic.rows(fx - 1, 1, ["vv", "vv", "v.", ".."])
    ic.px(5, 1, 'W'); ic.px(9, 1, 'W')
    return ic


def ash_bolt():
    ic = Icon()
    # sorcery bolt: blazing head top-right, tapering ember tail to the bottom-left
    for i in range(10):
        t = i / 9
        x, y = 9 - 7 * t, 7 + 6 * t
        hw = 2.2 * (1 - t) + 0.4
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if abs(dx + dy) <= hw * 1.4 and abs(dx - dy) <= 1.4:
                    ic.px(x + dx, y + dy, 'Y' if t < 0.3 and abs(dx + dy) < 1 else ('y' if t < 0.65 else 'G'))
    ic.ell(10.5, 5.5, 3.6, 3.6, lambda nx, ny: 'W' if nx * nx + ny * ny < 0.3 else ('Y' if nx * nx + ny * ny < 0.66 else 'y'))
    for (x, y) in ((4, 8), (6, 13), (1, 11), (12, 11), (14, 8)):
        ic.px(x, y, 'y')
    ic.px(14, 2, 'W')
    return ic


def sunspear():
    ic = Icon()
    # golden spear of light pointing up-right, its head wrapped in a sun-burst
    for a in range(0, 360, 45):
        r0, r1 = 2.8, (5.8 if a % 90 == 0 else 4.6)
        ic.line(10 + math.cos(math.radians(a)) * r0, 6 - math.sin(math.radians(a)) * r0,
                10 + math.cos(math.radians(a)) * r1, 6 - math.sin(math.radians(a)) * r1, 'y')
    ic.ell(10, 6, 2.6, 2.6, lambda nx, ny: 'Y')
    ic.line(1, 15, 9, 7, 'G')
    ic.line(2, 15, 10, 7, 'y')
    ic.line(1, 14, 8, 7, 'y')
    # spearhead (diamond) in white-gold, pointing up-right
    ic.poly([(14, 2), (12, 7), (10, 7), (9, 6), (9, 4)], lambda x, y: 'W' if x + y < 16 else 'Y')
    ic.px(14, 1, 'W')
    return ic


def azure_thrift():
    ic = Icon()
    # azure crystal with a gold coin (thrift) behind it
    ic.ell(10.5, 10.5, 4.3, 4.3, lambda nx, ny: 'G' if nx * nx + ny * ny > 0.6 else ('Y' if (-nx - ny) > 0.5 else 'y'))
    ic.ell(10.5, 10.5, 1.2, 1.2, lambda nx, ny: "G")
    ic.px(8, 8, 'W')
    ic.poly([(6, 1), (10, 6), (6, 14), (2, 6)],
            lambda x, y: 'c' if (x < 6 and y < 7) else ('A' if x < 6 or y < 5 else ('a' if y < 11 else 'b')))
    ic.line(6, 2, 6, 12, 'A')
    ic.px(4, 5, 'W')
    return ic


def emberburst():
    ic = Icon()
    # tongues of fire erupting from a ground ring
    ic.ell(8, 12.5, 6.5, 2.2, lambda nx, ny: 'y' if nx * nx + ny * ny > 0.45 else None)
    ic.ell(8, 12.5, 6.5, 2.2, lambda nx, ny: None if nx * nx + ny * ny > 0.45 else 'g')
    for (bx, h, w) in ((3, 6, 1.6), (8, 10, 2.4), (13, 6, 1.6), (5.5, 8, 1.6), (10.5, 8, 1.6)):
        for i in range(h):
            t = i / h
            hw = w * (1 - t) ** 0.8
            for x in range(int(bx - 3), int(bx + 4)):
                d = abs(x + 0.5 - bx - 0.5 * math.sin(t * 3))
                if d <= hw:
                    c = 'W' if t < 0.25 and d < hw * 0.5 else ('Y' if t < 0.45 else ('y' if t < 0.7 else 'R'))
                    ic.px(x, 12 - i, c)
    return ic


def soul_siphon():
    ic = Icon()
    # azure spiral drawing in toward a crimson soul core
    for i in range(70):
        t = i / 70
        a = t * 3.2 * math.pi
        r = 6.6 * (1 - t) + 1.2
        x, y = 8 + math.cos(a) * r, 8 - math.sin(a) * r
        ic.px(x, y, 'c' if t < 0.25 else ('A' if t < 0.6 else 'a'))
    ic.ell(8, 8, 2.4, 2.4, lambda nx, ny: 'P' if (nx + ny) < -0.4 else 'R')
    ic.px(7, 7, 'W')
    ic.px(14, 8, 'W')
    return ic


def quickstep():
    ic = Icon()
    # armoured sabaton kicking off, azure speed lines trailing behind
    for y, (x0, x1) in ((4, (1, 5)), (8, (0, 4)), (12, (2, 5))):
        ic.line(x0, y, x1, y, 'A')
        ic.px(x1, y, 'c')
    # greave (shin) + ankle + pointed toe, sole
    ic.poly([(7, 1), (11, 1), (11, 8), (14, 10), (15, 12), (15, 13), (7, 13), (7, 9)],
            lambda x, y: '4' if (x < 9 and y < 10) else ('3' if (x < 11 or y < 11) else '2'))
    ic.line(7, 1, 7, 12, '5')
    ic.rect(7, 4, 11, 4, 'G'); ic.px(7, 4, 'y')
    ic.rect(7, 8, 11, 8, '2')
    ic.rect(7, 14, 15, 14, '1')
    ic.px(12, 11, '4'); ic.px(13, 11, '4')
    return ic


def iron_flask():
    ic = Icon()
    flask(ic, ('P', 'R', 'r', 'm'))
    # iron bands riveted round the bulb
    for x in range(3, 14):
        if ic.get(x, 10):
            ic.px(x, 10, '4' if x < 7 else ('3' if x < 11 else '2'))
    for x in (5, 8, 11):
        ic.px(x, 10, '5')
    ic.rect(5, 3, 10, 3, '4')
    return ic


def steadfast():
    ic = Icon()
    # kite shield, gold rim, steel field with a gold boss
    ic.poly([(2, 2), (13, 2), (13, 8), (8, 14), (7, 14), (2, 8)], 'G')
    ic.poly([(3, 3), (12, 3), (12, 8), (8, 12), (7, 12), (3, 8)],
            lambda x, y: '4' if (x < 6 and y < 7) else ('3' if x < 8 else '2'))
    ic.line(2, 2, 13, 2, 'y')
    ic.line(2, 2, 2, 8, 'y')
    ic.line(7, 3, 7, 12, 'G'); ic.line(3, 6, 12, 6, 'G')
    ic.rect(7, 5, 8, 7, 'y'); ic.px(7, 5, 'Y')
    return ic


def last_stand():
    ic = Icon()
    # sword driven into the ground, wreathed in crimson flame tongues
    for (bx, h, w) in ((3.5, 7, 1.5), (12.5, 7, 1.5), (5.5, 11, 1.7), (10.5, 11, 1.7)):
        for i in range(h):
            t = i / h
            hw = w * (1 - t) ** 0.8
            for x in range(int(bx - 3), int(bx + 4)):
                d = abs(x + 0.5 - bx - 0.6 * math.sin(t * 3.5 + bx))
                if d <= hw:
                    ic.px(x, 13 - i, 'P' if t < 0.25 and d < 0.8 else ('R' if t < 0.6 else 'r'))
    ic.rect(7, 4, 8, 13, '3')
    ic.line(7, 4, 7, 12, '5')
    ic.rect(4, 3, 11, 3, 'G'); ic.px(4, 3, 'g'); ic.px(11, 3, 'g'); ic.px(5, 3, 'y'); ic.px(6, 3, 'y')
    ic.rect(7, 1, 8, 2, 't')
    ic.px(7, 0, 'y'); ic.px(8, 0, 'G')
    ic.rect(1, 14, 14, 14, 's'); ic.line(1, 14, 6, 14, 'S')
    return ic


def second_wind():
    ic = Icon()
    # two curling gusts of azure wind with a gold spark of renewed breath
    def curl(cx, cy, r, turns, cols, start):
        n = 60
        for i in range(n):
            t = i / n
            a = start + t * turns * 2 * math.pi
            rr = r * (1 - 0.6 * t)
            ic.px(cx + math.cos(a) * rr, cy - math.sin(a) * rr, cols[0] if t < 0.5 else cols[1])
    ic.line(1, 5, 9, 5, 'A'); ic.line(1, 10, 7, 10, 'A')
    curl(10, 7.5, 3.4, 0.8, ('c', 'A'), -math.pi / 2)
    curl(8.5, 11.5, 2.6, 0.8, ('A', 'a'), -math.pi / 2)
    ic.line(1, 5, 4, 5, 'c')
    sparkle(ic, 13, 3)
    return ic


# ================================================================ items / HUD
def flask_red():
    ic = Icon()
    flask(ic, ('P', 'R', 'r', 'm'))
    return ic


def flask_blue():
    ic = Icon()
    flask(ic, ('c', 'A', 'a', 'b'))
    return ic


def cinder():
    ic = Icon()
    # glowing gold cinder: faceted ember with a flicker of flame
    ic.poly([(8, 2), (13, 8), (8, 14), (3, 8)],
            lambda x, y: 'Y' if (x < 8 and y < 8) else ('y' if (x >= 8 and y < 8) or (x < 8) else 'G'))
    ic.poly([(8, 5), (10.5, 8), (8, 11), (5.5, 8)], lambda x, y: 'W' if (x < 8 and y < 8) else 'Y')
    ic.line(8, 2, 8, 13, 'y')
    ic.px(8, 5, 'W'); ic.px(7, 7, 'W')
    ic.px(13, 3, 'Y'); ic.px(2, 12, 'y')
    return ic


def shard():
    ic = Icon()
    # skill point: tall golden crystal prism with a white-hot facet
    ic.poly([(8, 1), (12, 5), (11, 12), (8, 15), (5, 12), (4, 5)],
            lambda x, y: 'Y' if x < 7 else ('y' if x < 9 else 'G'))
    ic.line(8, 2, 8, 14, 'y')
    ic.line(6, 4, 6, 11, 'W')
    ic.line(5, 5, 5, 10, 'Y')
    ic.px(10, 12, 'g'); ic.px(9, 13, 'g')
    sparkle(ic, 13, 2)
    return ic


def key():
    ic = Icon()
    # ornate key, bow top-left, bit bottom-right
    ic.ell(4.5, 4.5, 3.6, 3.6, lambda nx, ny: None if nx * nx + ny * ny < 0.22 else
           ('Y' if (-nx - ny) > 0.3 else ('y' if (-nx - ny) > -0.5 else 'G')))
    ic.line(6, 6, 13, 13, 'y')
    ic.line(7, 6, 13, 12, 'G')
    ic.rows(9, 11, ["y..", "yy.", ".G."])
    ic.rows(11, 9, ["G.", "yG"])
    ic.px(3, 3, 'W')
    return ic


def talon():
    ic = Icon()
    # wall-jump relic: a great hooked claw (bone) set in a gold cuff
    for i in range(30):
        t = i / 29
        a = math.radians(195 - 175 * t)              # sweeps up and over, tip hooks down-right
        r = 7.0 - 1.6 * t
        x, y = 7.5 + math.cos(a) * r, 11.5 - math.sin(a) * r * 1.2
        w = 2.0 * (1 - t) ** 0.8 + 0.6
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= w * w:
                    ic.px(x + dx, y + dy, 'v' if (dx + dy) < 0 else ('u' if (dx + dy) < 2 else 't'))
    ic.rect(1, 11, 4, 14, 'G'); ic.line(1, 11, 1, 14, 'y'); ic.line(1, 11, 4, 11, 'y')
    ic.px(2, 13, 'R')
    return ic


WING = ["....vv",
        "...vvv",
        ".vvvvu",
        "vvvvuu",
        "vvvuuu",
        "vvuuut",
        "vuuutt",
        "uuut.t",
        "uut.t.",
        "ut.t..",
        "t....."]


def wings():
    ic = Icon()
    # double-jump relic: two pale wings swept up from a gold clasp, notched feather tips
    ic.rows(9, 2, WING)
    ic.rows(1, 2, [r[::-1] for r in WING])
    # left wing is lit on its outer (left) edge too: brighten its leading edge
    for j, r in enumerate(WING):
        k = len(r) - 1 - r.index(next(ch for ch in r if ch != '.'))
        ic.px(1 + k, 2 + j, 'v') if j < 7 else None
    ic.rect(7, 4, 8, 10, 'y')
    ic.px(7, 4, 'Y'); ic.px(7, 5, 'W'); ic.px(8, 10, 'G'); ic.px(7, 10, 'G')
    ic.px(7, 11, 'g'); ic.px(8, 11, 'g')
    return ic


def map_():
    ic = Icon()
    # rolled parchment map with a crimson route mark
    ic.rect(2, 3, 13, 12, 'v')
    for y in range(3, 13):
        ic.px(2, y, 'u'); ic.px(13, y, 'u')
    ic.rect(1, 2, 2, 13, 't'); ic.rect(13, 2, 14, 13, 't')
    ic.px(1, 2, 'u'); ic.px(13, 2, 'u')
    ic.line(4, 10, 6, 7, 'u'); ic.line(6, 7, 9, 8, 'u'); ic.line(9, 8, 10, 5, 'u')
    ic.rows(9, 4, ["R.R", ".R.", "R.R"])
    ic.line(4, 5, 5, 5, 't'); ic.line(8, 11, 11, 11, 't')
    return ic


def shrine():
    ic = Icon()
    # grace shrine: gold flame over a stone brazier
    for i in range(7):
        t = i / 7
        hw = 2.6 * (1 - t) ** 0.8
        for x in range(4, 12):
            d = abs(x + 0.5 - 8 - 0.6 * math.sin(t * 4))
            if d <= hw:
                ic.px(x, 7 - i, 'W' if t < 0.35 and d < 1 else ('Y' if t < 0.6 else 'y'))
    ic.rect(4, 8, 11, 9, 'S'); ic.px(4, 8, '4'); ic.line(5, 8, 10, 8, 'S')
    ic.rect(3, 8, 12, 8, 'S'); ic.px(3, 8, '4')
    ic.rect(6, 10, 9, 12, 's'); ic.px(6, 10, 'S')
    ic.rect(4, 13, 11, 14, 's'); ic.line(4, 13, 10, 13, 'S')
    ic.px(5, 9, 'G'); ic.px(10, 9, 'G')
    return ic


def skull():
    ic = Icon()
    ic.ell(8, 6.5, 5.6, 5.2, shade('v', 'u', 't'))
    ic.rect(5, 10, 10, 13, 'u')
    ic.rect(5, 10, 6, 12, 'v')
    # eye sockets with a faint crimson ember, nose, teeth
    ic.rect(4, 6, 6, 8, '1'); ic.rect(9, 6, 11, 8, '1')
    ic.px(5, 7, 'R'); ic.px(10, 7, 'r')
    ic.px(7, 9, '1'); ic.px(8, 9, '1')
    for x in (6, 8, 10):
        ic.px(x, 12, 't')
    ic.px(5, 13, 't'); ic.px(10, 13, 't')
    ic.px(5, 3, 'W')
    return ic


def lock():
    ic = Icon()
    # iron padlock with a gold keyhole
    ic.ell(8, 5.5, 4.2, 4.6, lambda nx, ny: None if nx * nx + ny * ny < 0.36 else ('4' if nx < -0.2 else '3'))
    ic.rect(2, 7, 13, 14, '3')
    ic.rect(2, 7, 4, 13, '4')
    ic.rect(11, 8, 13, 14, '2')
    ic.line(2, 7, 13, 7, '5')
    ic.rect(7, 9, 8, 10, 'y'); ic.px(7, 9, 'Y')
    ic.rect(7, 11, 8, 12, 'G')
    ic.line(2, 14, 13, 14, '1')
    return ic


ICONS = [("keen_edge", keen_edge), ("fourth_strike", fourth_strike), ("charged_arts", charged_arts),
         ("riposte_mastery", riposte_mastery), ("bloodthirst", bloodthirst), ("ash_bolt", ash_bolt),
         ("sunspear", sunspear), ("azure_thrift", azure_thrift), ("emberburst", emberburst),
         ("soul_siphon", soul_siphon), ("quickstep", quickstep), ("iron_flask", iron_flask),
         ("steadfast", steadfast), ("last_stand", last_stand), ("second_wind", second_wind),
         ("flask_red", flask_red), ("flask_blue", flask_blue), ("cinder", cinder), ("shard", shard),
         ("key", key), ("talon", talon), ("wings", wings), ("map", map_), ("shrine", shrine),
         ("skull", skull), ("lock", lock)]


# ================================================================ node frame
def node_frame():
    """24x24 ornate gold-on-black frame; transparent 16x16 centre at (4..19, 4..19)."""
    F = 24
    back = Image.new("RGBA", (F, F), (0, 0, 0, 0))
    gold = Image.new("RGBA", (F, F), (0, 0, 0, 0))
    K = PAL['K'] + (255,)
    BLK = (16, 13, 20, 255)
    Gd, Gm, Gl, Gh = (PAL['g'] + (255,), PAL['G'] + (255,), PAL['y'] + (255,), PAL['Y'] + (255,))

    def inner(x, y):
        return 4 <= x <= 19 and 4 <= y <= 19

    # black band with chamfered outer corners
    for y in range(F):
        for x in range(F):
            if inner(x, y):
                continue
            cx, cy = min(x, F - 1 - x), min(y, F - 1 - y)
            if cx + cy < 2:
                continue                      # chamfer
            back.putpixel((x, y), K if (cx == 0 or cy == 0 or cx + cy == 2) else BLK)
    # gold inner rim (1px, lit top/left) hugging the transparent window
    for i in range(3, 21):
        for (x, y) in ((i, 3), (3, i)):
            gold.putpixel((x, y), Gl)
        for (x, y) in ((i, 20), (20, i)):
            gold.putpixel((x, y), Gm)
    # gold outer rim, inset by 1 from the outline
    for i in range(3, 21):
        gold.putpixel((i, 1), Gm)
        gold.putpixel((1, i), Gm)
        gold.putpixel((i, 22), Gd)
        gold.putpixel((22, i), Gd)
    for (x, y) in ((2, 2), (21, 2), (2, 21), (21, 21)):
        gold.putpixel((x, y), Gm)
    # corner ornaments: little diamonds with a bright facet
    for (cx, cy) in ((2, 2), (21, 2), (2, 21), (21, 21)):
        for (dx, dy, c) in ((0, 0, Gh), (1, 0, Gl), (-1, 0, Gl), (0, 1, Gl), (0, -1, Gl)):
            x, y = cx + dx, cy + dy
            if 0 < x < F - 1 and 0 < y < F - 1:
                gold.putpixel((x, y), c)
    # mid-edge studs (top one is a crimson gem)
    for (x, y) in ((11, 1), (12, 1), (11, 22), (12, 22), (1, 11), (1, 12), (22, 11), (22, 12)):
        gold.putpixel((x, y), Gh)
    for (x, y) in ((11, 2), (12, 2)):
        gold.putpixel((x, y), PAL['R'] + (255,))
    gold.putpixel((11, 2), PAL['P'] + (255,))
    # bright L-brackets on the inner rim corners
    for (cx, cy, sx, sy) in ((3, 3, 1, 1), (20, 3, -1, 1), (3, 20, 1, -1), (20, 20, -1, -1)):
        for i in range(3):
            gold.putpixel((cx + sx * i, cy), Gh)
            gold.putpixel((cx, cy + sy * i), Gh)
    # filigree ticks between the rims
    for i in (6, 17):
        for (x, y) in ((i, 2), (2, i), (i, 21), (21, i)):
            gold.putpixel((x, y), Gd)
    return back, gold


# ================================================================ build + preview
def main():
    frames, tags, comps = [], [], []
    for i, (name, fn) in enumerate(ICONS):
        body, out = fn().images()
        frames.append({"ms": 100, "cels": {"Outline": out, "Icon": body}})
        tags.append((name, i, i))
        c = out.copy()
        c.alpha_composite(body)
        comps.append((name, c))
    asebuild.build("ui_icons", S, S, ["Outline", "Icon"], frames, tags)

    back, gold = node_frame()
    asebuild.build("ui_frame", 24, 24, ["Back", "Gold"], [{"ms": 100, "cels": {"Back": back, "Gold": gold}}],
                   [("frame", 0, 0)])
    fr = back.copy()
    fr.alpha_composite(gold)

    # preview: row 1 = 1x on dark (true size), rows below = icons inside the frame at 4x on mid-grey
    Z = 4
    cols = 9
    rows = (len(comps) + cols - 1) // cols
    cw, ch = 28 * Z, 36 * Z
    sheet = Image.new("RGBA", (cols * cw, 40 + rows * ch), (92, 92, 100, 255))
    d = ImageDraw.Draw(sheet)
    strip = Image.new("RGBA", (len(comps) * 18 + 2, 20), (20, 18, 26, 255))
    for i, (_, c) in enumerate(comps):
        strip.alpha_composite(c, (2 + i * 18, 2))
    sheet.paste(strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST), (0, 0))
    for i, (name, c) in enumerate(comps):
        cell = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        win = Image.new("RGBA", (16, 16), (28, 24, 34, 255))
        cell.paste(win, (4, 4))
        cell.alpha_composite(fr)
        cell.alpha_composite(c, (4, 4))
        x, y = (i % cols) * cw + 2 * Z, 40 + (i // cols) * ch + 2 * Z
        sheet.alpha_composite(cell.resize((24 * Z, 24 * Z), Image.NEAREST), (x, y))
        d.text((x, y + 24 * Z + 4), name, fill=(255, 255, 255, 255))
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "ui.png"))
    print("ui_icons:", len(frames), "icons; ui_frame: 1")


if __name__ == "__main__":
    main()
