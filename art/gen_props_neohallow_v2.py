#!/usr/bin/env python3
"""NEO-HALLOW props v2 (docs/v17/neohallow_upgrade.md): the street furniture of the megacity, redrawn with volume.

  python3 art/gen_props_neohallow_v2.py [--no-ase]

Rebuilt sheets (same frame sizes, tags, frame counts, durations and bottom-centre anchors, so no room data changes):
  nh_deco  64x80  sign0-2 (2), billboard0-2 (4), lamp (2), antenna, vent, canopy, pylon, rack (2), glyph (4)
  nh_term  24x32  idle (4), on (4)                 nh_train 112x48 run (4), idle (1) (roof = the top rows: it is a platform)
  xsc_m    64x64  only the NEO-HALLOW tags vending (2), watertower, maglev (devdesk is the Dev Room joke: kept as is)
  xsc_s    32x32  only dumpster
  nh_kit   16x16  new: pipe, pipe_j, rail, rail_p, stripe, stripe_e: the sprites the 55_sc.js bakes now tile
                  (they replace the flat fillRect pipes / railings / warning stripes)
Look: gunmetal with a cold rim on the lit (left) side and a falling shadow on the right, 1 px dark outline, grime and
rust streaks low down, emissive neon only where it is a light (tubes, screens, LEDs: those pixels are bright enough that
the shader shows them as painted), holograms translucent (partial alpha, scanlines).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import hexc  # noqa: E402
ROOT = os.path.dirname(HERE)

ST = ['07070d', '0c0c15', '12131f', '191b2a', '212436', '2b2f44', '373c55', '464c68', '585f7e', '6e7696', '8a92b0', 'aab2cc', 'd0d6e6']
RUST = ['1a0e0c', '2e1812', '4a2618', '6a3a20']
CY = ['06202e', '0b4d66', '13a3c9', '3fe0ff', 'b8f6ff', 'f2feff']
MG = ['2a0624', '6e0f5c', 'c21d97', 'ff3fc0', 'ff9fe2', 'fff0fb']
AM = ['3a1e06', '7a4410', 'c87a20', 'ffb050', 'ffe0a0', 'fff6e0']
GR = ['0b3a2c', '157a58', '2fd09a', '5affd2', 'c8fff0', 'f0fff8']
RD = ['3a0610', '8a0f22', 'e0223f', 'ff6a7e', 'ffd0d8']
OUT = '05050a'


def h01(*a):
    v = 0
    for x in a: v = (v * 1103515245 + int(x) * 2654435761 + 12345) & 0xffffffff
    v ^= v >> 13; v = (v * 1274126177) & 0xffffffff; v ^= v >> 16
    return (v & 0xffff) / 65535


class C:
    def __init__(self, w, h):
        self.w, self.h = w, h; self.a = np.zeros((h, w, 4), float)

    def px(self, x, y, c, al=255):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < self.w and 0 <= y < self.h) or c is None: return
        col = hexc(c)
        if al >= 255 or self.a[y, x, 3] == 0: self.a[y, x] = [*col, al]
        else:
            k = al / 255; self.a[y, x, :3] = self.a[y, x, :3] * (1 - k) + col * k; self.a[y, x, 3] = max(self.a[y, x, 3], al)

    def rect(self, x, y, w, h, c, al=255):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)): self.px(xx, yy, c, al)

    def line(self, x0, y0, x1, y1, c, al=255):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for i in range(n + 1): self.px(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, c, al)

    def box(self, x, y, w, h, r=ST, lo=3, hi=7, top=True, grime=0.0, seed=0):
        """a lit volume: left rim, body with a slight vertical gradient, shadowed right, top cap, dark bottom, grime low"""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                t = (yy - y) / max(1, h - 1)
                v = hi - (hi - lo) * (0.35 + 0.45 * t)
                if xx == x: v = hi + 1
                elif xx == x + 1 and w > 4: v = hi
                elif xx >= x + w - max(1, w // 5): v = lo
                if top and yy == y: v = hi + 2
                elif top and yy == y + 1 and h > 4: v = hi + 0.5
                if yy == y + h - 1: v = lo - 1
                if grime and t > 0.55 and h01(xx, yy, seed) < (t - 0.55) * grime * 2: v -= 1
                self.px(xx, yy, r[int(np.clip(round(v), 0, len(r) - 1))])

    def cyl(self, x, y, w, h, r=ST, lo=2, hi=8):
        """a vertical round pole / tank: highlight a third from the left"""
        for xx in range(x, x + w):
            u = (xx - x + 0.5) / w
            v = lo + (hi - lo) * max(0, 1 - abs(u - 0.32) * 2.2)
            for yy in range(y, y + h): self.px(xx, yy, r[int(np.clip(round(v), 0, len(r) - 1))])

    def tube(self, pts, ram, core=4, al=255):
        """a neon tube: 1 px bright core, its glass a step down beside it"""
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.line(x0, y0, x1, y1, ram[core], al)

    def outline(self, c=OUT, skip_alpha_below=200):
        a = self.a[..., 3] >= skip_alpha_below; m = np.zeros_like(a)
        m[1:] |= a[:-1]; m[:-1] |= a[1:]; m[:, 1:] |= a[:, :-1]; m[:, :-1] |= a[:, 1:]
        edge = m & (self.a[..., 3] == 0)
        self.a[edge] = [*hexc(c), 255]

    def grime(self, x0, y0, w, h, k=0.5, seed=1):
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                if self.a[yy, xx, 3] > 200 and h01(xx, yy, seed) < k * (yy - y0) / max(1, h):
                    self.a[yy, xx, :3] *= 0.75

    def rust(self, x, y, n, seed=3):
        for i in range(n):
            xx = x + int(h01(i, seed) * 3); L = 2 + int(h01(i, seed, 2) * 5)
            for yy in range(y, y + L):
                if 0 <= yy < self.h and 0 <= xx < self.w and self.a[yy, xx, 3] > 200: self.a[yy, xx, :3] = self.a[yy, xx, :3] * 0.6 + hexc(RUST[2]) * 0.4

    def img(self):
        return Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8))


def glyphs(c, x0, y0, n, ram, seed, step=6, size=4, horiz=True, off=(), al=255):
    """made-up neon script (no letters): each glyph a few 1 px tube strokes in a size x size cell"""
    for k in range(n):
        ox, oy = (x0 + k * step, y0) if horiz else (x0, y0 + k * step)
        on = k not in off; col = ram[4] if on else ram[1]; a_ = al if on else 200
        g = int(h01(k, seed, 9) * 4095)
        m = size // 2
        c.line(ox + m, oy, ox + m, oy + size, col, a_) if g & 1 else c.line(ox + (g >> 1) % 2 * size, oy, ox + (g >> 1) % 2 * size, oy + size, col, a_)   # a stem
        if g & 4: c.line(ox, oy + 1, ox + m, oy + 1, col, a_)                     # a short bar off it
        if g & 8: c.line(ox + m, oy + m, ox + size, oy + size, col, a_)           # a falling stroke
        if g & 16: c.line(ox, oy + size, ox + m - 1, oy + m + 1, col, a_)         # a rising tick
        if g & 32: c.px(ox + size, oy + 1, col, a_)                               # a dot
        if g & 64 and not g & 8: c.line(ox + m, oy + size - 1, ox + size, oy + size - 1, col, a_)


# =============================================================================================== nh_deco (64x80)
def sign(v, f):
    ram = [MG, CY, AM][v]; c = C(64, 80)
    c.cyl(30, 46, 3, 34, ST, 3, 8)                                     # the post
    c.box(27, 76, 9, 4, ST, 2, 6); c.rect(28, 76, 7, 1, ST[8])          # its foot plate
    c.box(29, 42, 5, 4, ST, 3, 7)                                       # the clamp
    c.box(13, 18, 38, 25, ST, 2, 6, grime=0.6, seed=v)                  # the casing
    c.rect(15, 20, 34, 21, '0a0812')                                    # dark glass
    for yy in range(21, 40):                                            # the glow inside the box (lit glass)
        for xx in range(16, 48): c.px(xx, yy, ram[1], int(70 + 40 * (1 - abs(yy - 30) / 10)))
    glyphs(c, 18, 24, 5, ram, v * 7 + 1, step=6, size=4, off=((2,) if f else ()))
    c.rect(18, 33, 28, 1, ram[3] if not f else ram[2]); c.rect(18, 34, 28, 1, ram[1])   # an underline tube
    c.rect(16, 37, 6, 2, ram[2]); c.rect(24, 37, 2, 2, ram[3])
    c.rect(13, 18, 38, 1, ST[10]); c.rect(13, 42, 38, 1, ST[1])         # rim / bottom of the casing
    c.rust(40, 43, 3, v)
    c.line(48, 43, 50, 50, ST[3]); c.line(50, 50, 49, 56, ST[3])        # a dangling cable
    c.outline()
    return c.img()


def billboard(v, f):
    ram = [MG, CY, MG][v]; c = C(64, 80)
    c.box(28, 50, 8, 30, ST, 2, 7, grime=0.7, seed=v + 5)               # the pylon
    for yy in range(54, 78, 6): c.rect(28, yy, 8, 1, ST[2])
    c.box(22, 76, 20, 4, ST, 2, 6)
    c.box(24, 45, 16, 5, ST, 3, 8)                                      # the projector head
    c.rect(26, 44, 12, 1, ram[3]); c.rect(28, 43, 8, 1, ram[4])
    c.outline()
    x0, y0, w, h = 6, 4, 52, 38                                         # the projection: translucent, scanlined
    for y in range(y0, y0 + h):
        scan = (y + f * 2) % 3 == 0
        for x in range(x0, x0 + w):
            edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
            corner = (x in (x0, x0 + 1, x0 + w - 2, x0 + w - 1)) and (y in (y0, y0 + 1, y0 + h - 2, y0 + h - 1))
            if corner: c.px(x, y, ram[4], 255)
            elif edge: c.px(x, y, ram[3], 230)
            else: c.px(x, y, ram[2] if scan else ram[1], 120 if scan else 78)
    for yy in range(y0 + h, 43):                                        # the beam from the head up into the panel
        for xx in range(28 - (43 - yy) // 2, 36 + (43 - yy) // 2): c.px(xx, yy, ram[2], 40)
    if v == 0:      # an eye in a ring (the city watching)
        for a in range(0, 360, 6):
            c.px(32 + 13 * math.cos(math.radians(a)), 22 + 7 * math.sin(math.radians(a)), ram[4], 240)
        for a in range(0, 360, 10): c.px(32 + 6 * math.cos(math.radians(a)), 22 + 6 * math.sin(math.radians(a)), ram[3], 240)
        c.rect(30, 20 + (1 if f == 2 else 0), 5, 5 - (2 if f == 2 else 0), ram[5]); c.rect(31, 21, 3, 3, '1a0818')
        glyphs(c, 11, 34, 7, ram, 31 + f, step=6, size=3, al=230)
    elif v == 1:    # a wall of scrolling glyphs
        for row in range(3):
            glyphs(c, 11 + ((f * 2 + row * 3) % 6), 10 + row * 10, 6, ram, 11 + row * 5 + f, step=7, size=4, al=235)
    else:           # the Pale Root, as a logo
        for i in range(40):
            t = i / 39; x = 22 + t * 20; y = 37 - t * 26 + math.sin(t * 6) * 2
            c.px(x, y, 'e8e3d6', 240); c.px(x + 1, y, 'b8b2a4', 230)
        for k in range(5):
            t = 0.3 + k * 0.13; x = 22 + t * 20; y = 37 - t * 26
            c.line(x, y, x + (-6 if k % 2 else 6), y - 4, 'b8b2a4', 220)
        glyphs(c, 10, 8, 3, ram, 5, step=6, size=4, al=235)
    if f == 3:      # the glitch frame: a slice slides sideways
        sl = c.a[14:20].copy(); c.a[14:20] = 0; c.a[14:20, 5:] = sl[:, :-5]
    return c.img()


def lamp(f):
    c = C(64, 80)
    c.box(28, 75, 8, 5, ST, 2, 6)
    c.cyl(30, 28, 3, 47, ST, 2, 9)
    for yy in (40, 56): c.rect(29, yy, 5, 1, ST[6])
    c.line(32, 28, 36, 24, ST[6]); c.line(33, 28, 37, 25, ST[3]); c.line(36, 24, 40, 23, ST[6])
    c.box(38, 21, 12, 4, ST, 2, 7)                                       # the head
    c.rect(39, 25, 10, 1, CY[4] if f == 0 else CY[3]); c.rect(40, 26, 8, 1, CY[2], 200)
    c.outline()
    return c.img()


def antenna():
    c = C(64, 80)
    c.box(26, 76, 12, 4, ST, 2, 6)
    for yy in range(14, 76):                                             # a lattice mast
        c.px(29, yy, ST[7]); c.px(34, yy, ST[4])
        if (yy - 14) % 6 == 0: c.line(29, yy, 34, yy + 6, ST[5]); c.line(34, yy, 29, yy + 6, ST[3])
    c.box(22, 28, 7, 7, ST, 3, 8); c.px(25, 31, ST[2])                   # dishes
    c.line(21, 27, 21, 35, ST[9]); c.box(35, 42, 6, 6, ST, 3, 7); c.line(41, 41, 41, 48, ST[5])
    c.line(31, 14, 31, 6, ST[8]); c.line(27, 10, 36, 10, ST[6])
    c.px(31, 5, RD[3]); c.px(31, 4, RD[2])
    c.outline()
    return c.img()


def vent():
    c = C(64, 80)
    c.box(18, 60, 28, 20, ST, 2, 7, grime=0.8, seed=4)
    c.rect(21, 64, 22, 12, ST[1])
    for xx in range(22, 42, 2): c.rect(xx, 65, 1, 10, ST[4])              # the grille
    c.rect(21, 64, 22, 1, ST[6])
    c.cyl(24, 50, 8, 10, ST, 2, 8); c.rect(23, 49, 10, 2, ST[9]); c.rect(24, 51, 8, 1, ST[1])   # an exhaust stack
    c.cyl(36, 54, 4, 6, ST, 2, 7)
    c.line(46, 66, 50, 66, ST[5]); c.line(50, 66, 50, 80, ST[5])          # a pipe down to the roof
    c.rust(20, 72, 4, 9)
    c.px(42, 62, RD[2])                                                   # a status LED
    c.outline()
    return c.img()


def canopy():
    c = C(64, 80)
    c.box(3, 20, 58, 5, ST, 3, 9)                                        # the roof slab
    c.rect(3, 25, 58, 1, CY[3]); c.rect(4, 26, 56, 1, CY[1], 200)        # LED strip under it
    for x0 in (9, 52):
        c.cyl(x0, 26, 3, 54, ST, 2, 8)
        c.box(x0 - 1, 77, 5, 3, ST, 2, 6)
    for yy in range(30, 70):                                             # glass side panels (translucent)
        for xx in list(range(12, 18)) + list(range(46, 52)):
            c.px(xx, yy, CY[1] if (xx + yy) % 7 else CY[2], 70)
    c.rect(12, 30, 6, 1, CY[3], 200); c.rect(46, 30, 6, 1, CY[3], 200)
    c.box(22, 28, 20, 9, ST, 1, 5); c.rect(23, 29, 18, 7, '08080e')       # a route board
    glyphs(c, 24, 30, 3, CY, 2, step=6, size=4)
    c.rect(20, 60, 24, 2, ST[6]); c.rect(21, 62, 2, 8, ST[3]); c.rect(41, 62, 2, 8, ST[3])   # a bench
    c.outline()
    return c.img()


def pylon():
    c = C(64, 80)
    c.box(26, 36, 12, 44, ST, 2, 7, grime=0.9, seed=7)
    c.box(21, 31, 22, 6, ST, 3, 9)
    for yy in range(40, 80, 5): c.px(31, yy, CY[3]); c.px(32, yy, CY[2])   # a rail light running down it
    c.rect(26, 50, 12, 1, ST[2]); c.rect(26, 64, 12, 1, ST[2])
    c.rust(34, 40, 4, 2)
    c.outline()
    return c.img()


def rack(f):
    c = C(64, 80)
    c.box(19, 30, 26, 50, ST, 1, 6, grime=0.5, seed=8)
    c.rect(21, 33, 22, 45, ST[1])
    for y in range(34, 77, 4):
        c.rect(22, y, 20, 3, ST[2]); c.rect(22, y, 20, 1, ST[4])
        for x in range(24, 40, 3):
            if h01(x, y + f * 7, 3) > 0.45: c.px(x, y + 1, [CY[3], CY[2], MG[3], AM[3], GR[3]][int(h01(x, y, 4) * 5)])
    c.rect(19, 30, 26, 1, ST[9]); c.rect(43, 33, 1, 45, ST[3])
    c.outline()
    return c.img()


def glyph(f):
    c = C(64, 80)
    c.box(22, 75, 20, 5, ST, 2, 7); c.rect(24, 74, 16, 1, CY[3]); c.rect(26, 73, 12, 1, CY[2], 200)
    c.outline()
    for yy in range(42, 73):                                             # the projection cone, faint
        hw = 3 + (73 - yy) * 0.35
        for xx in range(int(32 - hw), int(32 + hw)): c.px(xx, yy, CY[2], 26)
    for a in range(0, 360, 6):                                           # the sigil: a ring that turns, and the Root
        ang = math.radians(a + f * 22)
        x = 32 + 12 * math.cos(ang); y = 52 + 4.5 * math.sin(ang)
        if (a // 6) % 4: c.px(x, y, CY[4] if math.sin(ang) > 0 else CY[3], 240 if math.sin(ang) > 0 else 160)
    for i in range(26):
        t = i / 25; c.px(32 + math.sin(t * 6 + f * 1.5) * 3.5, 66 - t * 24, 'd8d2c4', 230)
    return c.img()


def deco_sheet():
    frames, tags = [], []

    def add(tag, ims):
        tags.append((tag, len(frames), len(frames) + len(ims) - 1)); frames.extend(ims)
    for v in range(3): add(f'sign{v}', [sign(v, f) for f in range(2)])
    for v in range(3): add(f'billboard{v}', [billboard(v, f) for f in range(4)])
    add('lamp', [lamp(f) for f in range(2)])
    add('antenna', [antenna()]); add('vent', [vent()]); add('canopy', [canopy()]); add('pylon', [pylon()])
    add('rack', [rack(f) for f in range(2)]); add('glyph', [glyph(f) for f in range(4)])
    return frames, tags


# =============================================================================================== nh_term (24x32)
def term(f, on):
    ram = GR if on else CY; c = C(24, 32)
    c.box(5, 13, 14, 19, ST, 2, 7, grime=0.7, seed=f)                    # the kiosk
    c.rect(7, 22, 10, 6, ST[2]); c.rect(7, 22, 10, 1, ST[5])               # an access panel
    for xx in range(8, 16, 2): c.px(xx, 25, ST[1])
    c.box(3, 3, 18, 11, ST, 2, 8)                                          # the screen housing, tilted
    c.rect(5, 5, 14, 7, ram[0])
    for i in range(3):                                                     # scrolling lines
        yy = 6 + (i * 2 + f) % 6
        c.rect(6, yy, 3 + int(h01(i, f, 3) * 9), 1, ram[3] if i == 0 else ram[2])
    c.rect(5, 5, 14, 1, ram[1])
    c.px(6, 27, RD[2] if not on else GR[3]); c.px(8, 27, AM[2])
    c.box(4, 14, 16, 2, ST, 3, 9)                                          # the keyboard ledge
    c.line(18, 30, 21, 31, ST[3])
    c.outline()
    return c.img()


# =============================================================================================== nh_train (112x48)
def train(f, run):
    c = C(112, 48)
    # body: a long streamlined car, roof flat (the platform), noses at both ends
    for x in range(7, 105):
        nose = min(x - 7, 104 - x)
        top = 0; bot = 34 - (0 if nose > 10 else (10 - nose) // 2)
        y0 = top + (0 if nose > 3 else 3 - nose)
        for y in range(y0, bot):
            t = (y - y0) / max(1, bot - y0)
            v = 9 - t * 6
            if y == y0: v = 11
            elif y == y0 + 1: v = 8
            if y == bot - 1: v = 1
            c.px(x, y, ST[int(np.clip(v, 0, 12))])
    c.rect(9, 6, 94, 10, '0a0a14')                                           # the window band
    for x in range(12, 100, 9):
        c.rect(x, 7, 7, 8, '182436'); c.rect(x, 7, 7, 1, '2a3a52')
        for y in range(8, 15): c.px(x + 1, y, '2a4a62')                       # the cabin's cold light through the glass
        if h01(x, 5) > 0.7: c.rect(x + 2, 11, 3, 4, '101824')                 # somebody's empty seat
    c.rect(9, 18, 94, 1, MG[3]); c.rect(9, 19, 94, 1, MG[1])                 # the magenta line
    c.rect(9, 3, 94, 1, ST[6])
    for x in range(20, 96, 24): c.rect(x, 21, 1, 9, ST[3])                   # door seams
    c.rect(100, 9, 4, 3, AM[4]); c.rect(98, 10, 2, 1, AM[2])                  # the lamp at the leading nose
    c.rect(8, 10, 2, 3, RD[2])                                                # tail light
    for x0 in (14, 82):                                                       # mag-lev pads, glowing
        c.box(x0, 34, 16, 3, ST, 2, 6)
        k = 4 if (run and f % 2 == 0) else 3
        c.rect(x0 + 1, 37, 14, 1, CY[k]); c.rect(x0 + 2, 38, 12, 1, CY[2], 200 if run else 150)
    c.outline()
    if run:   # speed streaks off the tail
        for i in range(4):
            y = 8 + i * 6 + (f % 2); L = 4 + (f + i) % 3 * 2
            for x in range(0, L): c.px(x, y, CY[2] if i % 2 else MG[2], 120)
    return c.img()


# =============================================================================================== xsc_m / xsc_s tags
def vending(f):
    c = C(64, 64)
    c.box(22, 29, 21, 35, ST, 2, 7, grime=0.8, seed=11); c.box(22, 25, 21, 4, ST, 3, 8)
    c.rect(24, 32, 12, 18, '0a0810')
    for yy in range(33, 49, 4):                                              # lit shelves of cans behind the glass
        c.rect(25, yy + 3, 10, 1, ST[4])
        for xx in range(25, 35, 2): c.px(xx, yy + 2, [MG[2], CY[2], AM[2], GR[2]][int(h01(xx, yy, 2) * 4)])
    for yy in range(32, 50):
        for xx in range(24, 36): c.px(xx, yy, CY[2] if f == 0 else MG[2], 70)
    c.rect(24, 32, 12, 1, CY[4] if f == 0 else MG[4]); c.rect(22, 26, 21, 3, '0a0810'); c.rect(23, 27, 19, 1, MG[3] if f == 0 else CY[3])   # the marquee
    c.rect(37, 33, 4, 6, ST[1]); c.px(38, 34, GR[3]); c.px(39, 36, AM[3])     # the coin panel
    c.rect(25, 53, 10, 4, ST[1]); c.rect(25, 53, 10, 1, ST[5])               # the tray
    c.rect(22, 29, 21, 1, ST[10])
    c.rust(24, 58, 5, 4)
    c.outline()
    return c.img()


def watertower():
    c = C(64, 64)
    for yy in range(4, 38):                                                 # a dark steel tank on legs, banded
        for xx in range(13, 51):
            u = (xx - 13 + 0.5) / 38; v = 2 + 6 * max(0, 1 - abs(u - 0.3) * 2.2)
            if (yy - 4) % 8 == 0: v += 1.5
            c.px(xx, yy, ST[int(np.clip(round(v), 0, 12))])
    for i in range(10):                                                     # the conical lid
        w_ = 40 - i * 4
        if w_ <= 0: break
        c.rect(32 - w_ // 2, 4 - i // 2 - 1, w_, 1, ST[7] if i % 2 else ST[6])
    c.rect(15, 18, 12, 4, '0a0810'); c.rect(16, 19, 10, 1, MG[3]); c.rect(16, 20, 10, 1, MG[1])   # a neon tag somebody hung on it
    c.grime(13, 20, 38, 18, 0.6, 3); c.rust(20, 36, 6, 5)
    for x0 in (16, 30, 46):                                                 # legs and bracing
        c.rect(x0, 38, 2, 26, ST[5]); c.rect(x0, 38, 1, 26, ST[7])
    c.line(17, 44, 31, 58, ST[3]); c.line(31, 44, 17, 58, ST[3]); c.line(31, 44, 47, 58, ST[3]); c.line(47, 44, 31, 58, ST[3])
    c.rect(14, 38, 36, 2, ST[3])
    c.outline()
    return c.img()


def maglev():
    c = C(64, 64)   # the Data Highway car: rows 45..63, roof (the platform) at the top of that
    for x in range(64):
        nose = min(x, 63 - x)
        y0 = 45 + (0 if nose > 3 else 3 - nose); bot = 63 - (0 if nose > 6 else (6 - nose) // 2)
        for y in range(y0, bot):
            t = (y - y0) / max(1, bot - y0); v = 9 - t * 6
            if y == y0: v = 11
            if y == bot - 1: v = 1
            c.px(x, y, ST[int(np.clip(v, 0, 12))])
    c.rect(3, 48, 58, 5, '0a0a14')
    for x in range(5, 60, 7): c.rect(x, 49, 5, 3, '1c2a40'); c.rect(x + 1, 49, 1, 3, '2e4a66')
    c.rect(3, 55, 58, 1, MG[3]); c.rect(60, 50, 3, 2, AM[4]); c.rect(1, 50, 2, 2, RD[2])
    c.rect(6, 61, 52, 1, CY[3]); c.rect(8, 62, 48, 1, CY[2], 180)
    return c.img()


def dumpster():
    c = C(32, 32)
    c.box(3, 17, 26, 15, ['0a100e', '0e1614', '142020', '1a2a28', '22363a', '2c4448', '38545a', '4a6a70', '62868c', '84a8ae'], 1, 5, grime=1.0, seed=6)
    c.rect(2, 15, 28, 3, ST[6]); c.rect(2, 15, 28, 1, ST[9]); c.line(3, 15, 28, 13, ST[5])   # the lid, ajar
    for xx in (8, 16, 24): c.rect(xx, 19, 1, 10, '0a100e')
    c.rect(5, 21, 6, 3, MG[2]); c.rect(5, 21, 6, 1, MG[3])                   # a sticker
    c.rust(12, 24, 5, 8)
    c.rect(4, 31, 3, 1, ST[2]); c.rect(25, 31, 3, 1, ST[2])
    c.outline()
    return c.img()


# =============================================================================================== nh_kit (16x16, new)
def kit():
    ims, tags = [], []

    def add(tag, im): tags.append((tag, len(ims), len(ims))); ims.append(im)
    c = C(16, 16)   # pipe: two parallel pipes along a tunnel roof (rows 0-3 and 6-9), tile horizontally
    for y0, r in ((0, (2, 8)), (6, (1, 6))):
        for x in range(16):
            for k, v in enumerate((r[1], r[1] - 2, r[0] + 2, r[0])): c.px(x, y0 + k, ST[v])
        for x in (5, 11): c.px(x, y0 + 2, ST[r[0]])
    add('pipe', c.img())
    c = C(16, 16)   # pipe with a flange joint and a valve
    for y0, r in ((0, (2, 8)), (6, (1, 6))):
        for x in range(16):
            for k, v in enumerate((r[1], r[1] - 2, r[0] + 2, r[0])): c.px(x, y0 + k, ST[v])
        c.rect(6, y0 - 1 if y0 else 0, 3, 6 if y0 else 5, ST[r[1] - 1]); c.rect(6, y0 - 1 if y0 else 0, 1, 6 if y0 else 5, ST[r[1] + 1])
    c.rect(12, 10, 1, 2, ST[5]); c.rect(10, 12, 5, 1, RD[1]); c.px(12, 12, RD[2])
    c.px(7, 4, CY[2])
    add('pipe_j', c.img())
    c = C(16, 16)   # railing: top rail, mid rail, a post at x 0 (rows 6..15; the bake places the floor at row 16)
    for x in range(16):
        c.px(x, 6, ST[10]); c.px(x, 7, ST[5]); c.px(x, 11, ST[7]); c.px(x, 12, ST[3])
    c.rect(0, 6, 2, 10, ST[6]); c.rect(0, 6, 1, 10, ST[9]); c.rect(1, 15, 1, 1, ST[2])
    add('rail', c.img())
    c = C(16, 16)   # railing with a lit post (an LED cap)
    for x in range(16):
        c.px(x, 6, ST[10]); c.px(x, 7, ST[5]); c.px(x, 11, ST[7]); c.px(x, 12, ST[3])
    c.rect(0, 5, 2, 11, ST[6]); c.rect(0, 5, 1, 11, ST[9]); c.px(0, 4, CY[3]); c.px(1, 4, CY[2])
    add('rail_p', c.img())
    c = C(16, 16)   # hazard stripe band (rows 0-2), worn
    for x in range(16):
        for y in range(3):
            on = ((x + y) // 3) % 2 == 0
            col = (AM[3] if y == 0 else AM[2]) if on else ST[1]
            if on and h01(x, y, 4) < 0.15: col = AM[1]
            c.px(x, y, col)
        c.px(x, 3, ST[0])
    add('stripe', c.img())
    c = C(16, 16)   # the stripe's end cap / a bolted plate edge
    for x in range(16):
        for y in range(3): c.px(x, y, (AM[2] if ((x + y) // 3) % 2 == 0 else ST[1]) if x < 13 else ST[6 if y == 0 else 4])
        c.px(x, 3, ST[0])
    c.px(14, 1, ST[9])
    add('stripe_e', c.img())
    return ims, tags


# =============================================================================================== build
def load(name):
    im = Image.open(os.path.join(ROOT, 'assets', f'{name}.png')).convert('RGBA'); j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    frs = [im.crop((f['frame']['x'], f['frame']['y'], f['frame']['x'] + f['frame']['w'], f['frame']['y'] + f['frame']['h'])) for f in j['frames']]
    return frs, [f['duration'] for f in j['frames']], [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']], j['frames'][0]['frame']


def check(name, tags, n, fw, fh):
    j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    assert [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']] == tags, name
    assert len(j['frames']) == n and (j['frames'][0]['frame']['w'], j['frames'][0]['frame']['h']) == (fw, fh), name


def sheet_preview(name, frames, fw, fh, out):
    cols = min(len(frames), 12); rows = (len(frames) + cols - 1) // cols; sc = 3 if fw <= 64 else 2
    pv = Image.new('RGBA', (cols * (fw + 2) * sc, rows * (fh + 2) * sc), (60, 56, 80, 255))
    for i, fr in enumerate(frames):
        cell = Image.new('RGBA', (fw, fh), (24, 20, 40, 255)); cell.alpha_composite(fr)
        pv.alpha_composite(cell.resize((fw * sc, fh * sc), Image.NEAREST), ((i % cols) * (fw + 2) * sc, (i // cols) * (fh + 2) * sc))
    pv.save(out)


def main(ase=True):
    import asebuild
    SRC = os.path.join(HERE, 'bg_src', 'neohallow'); os.makedirs(SRC + '/v1', exist_ok=True)
    out = {}
    fr, tg = deco_sheet(); out['nh_deco'] = (fr, tg, [140] * len(fr), 64, 80)
    fr = [term(f, False) for f in range(4)] + [term(f, True) for f in range(4)]; out['nh_term'] = (fr, [('idle', 0, 3), ('on', 4, 7)], [120] * 8, 24, 32)
    fr = [train(f, True) for f in range(4)] + [train(0, False)]; out['nh_train'] = (fr, [('run', 0, 3), ('idle', 4, 4)], [80] * 5, 112, 48)
    for nm, rep in (('xsc_m', {'vending': [vending(0), vending(1)], 'watertower': [watertower()], 'maglev': [maglev()]}), ('xsc_s', {'dumpster': [dumpster()]})):
        frs, durs, tags, f0 = load(nm)
        for t, a, b in tags:
            if t in rep:
                assert len(rep[t]) == b - a + 1, (nm, t)
                for i, im in enumerate(rep[t]): frs[a + i] = im
        out[nm] = (frs, tags, durs, f0['w'], f0['h'])
    fr, tg = kit(); out['nh_kit'] = (fr, tg, [100] * len(fr), 16, 16)
    for name, (frames, tags, durs, fw, fh) in out.items():
        sheet_preview(name, frames, fw, fh, os.path.join(SRC, f'props_{name}.png'))
        if ase:
            v1 = os.path.join(SRC, 'v1', f'{name}.png')
            if not os.path.exists(v1) and os.path.exists(os.path.join(ROOT, 'assets', f'{name}.png')):
                import shutil
                for ext in ('png', 'json'): shutil.copy(os.path.join(ROOT, 'assets', f'{name}.{ext}'), os.path.join(SRC, 'v1', f'{name}.{ext}'))
            asebuild.build(name, fw, fh, ['art'], [{'ms': d, 'cels': {'art': im}} for im, d in zip(frames, durs)], tags)
            check(name, [tuple(t) for t in tags], len(frames), fw, fh)
    print('ok', list(out))


if __name__ == '__main__':
    main('--no-ase' not in sys.argv)
