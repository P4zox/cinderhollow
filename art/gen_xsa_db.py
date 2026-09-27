#!/usr/bin/env python3
"""SA — Drowned Barrows props for the new rooms (DB10–DB17).
   xsa_db 48x48 props; xsa_saint (the Drowned Saint, 176x416); xsa_rosewin (160x160); xsa_bell (the Drowned Bell, 64x80);
   xsa_lagoon (the Pearl Lagoon's painted depths, 640x352).  Run: python3 art/gen_xsa_db.py"""
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from xsa_kit import Cv, C, lit, mix, sheet, OUT, cyl_shade, BAYER

ST = [C('0a1214'), C('142224'), C('1f3334'), C('2e4a48'), C('46665f'), C('6a8a80')]   # drowned stone
ALG = [C('10281e'), C('1a3e2c'), C('2a5a3c'), C('4a7a4a')]
TEAL = C('78e6d2'); BONE = [C('5e5a4c'), C('8e8870'), C('c8c0a4'), C('ece4cc')]
BRZ = [C('1c2420'), C('2e4038'), C('3e6a58'), C('5a9a80'), C('a0d8c0')]   # verdigris bronze


def c48(): return Cv(48, 48)


def gravecross():
    c = c48(); y = 47
    c.rect(22, y - 30, 25, y, ST[3]); c.rect(15, y - 24, 32, y - 21, ST[3]); c.ell(23.5, y - 22.5, 5, 5, ST[2]); c.ell(23.5, y - 22.5, 3, 3, (0, 0, 0, 0))
    c.rect(22, y - 30, 25, y, ST[3]); c.rect(15, y - 24, 32, y - 21, ST[3])
    c.rect(19, y - 3, 28, y, ST[2])
    c.speckle([ALG[1], ALG[2], ST[1]], 30, seed=3)
    return c.bevel().outline().im


def gravestone():
    c = c48(); y = 47
    c.poly([(16, y), (16, y - 16), (19, y - 21), (28, y - 21), (31, y - 16), (31, y)], ST[3])
    c.line(20, y - 15, 27, y - 15, ST[1]); c.line(21, y - 12, 26, y - 12, ST[1]); c.line(20, y - 9, 26, y - 9, ST[1])
    c.poly([(16, y - 8), (22, y - 5), (31, y - 10), (31, y), (16, y)], ALG[1])
    c.speckle([ALG[2], ST[2]], 24, seed=4)
    return c.bevel().outline().im


def cairn():
    c = c48(); y = 47
    for i, (w, h) in enumerate([(11, 4), (9, 4), (7, 3), (5, 3)]):
        yy = y - 2 - [0, 4, 8, 11][i]
        c.ell(24 + (i % 2), yy, w, h / 2 + 0.8, [ST[3], ST[2], ST[4], ST[3]][i])
    c.rect(23, y - 20, 24, y - 13, BONE[1]); c.rect(21, y - 18, 26, y - 17, BONE[1])
    c.speckle([ALG[2]], 12, seed=5)
    return c.bevel().outline().im


def weeds(f):
    c = c48(); y = 47; r = random.Random(6)
    for i in range(7):
        x = 12 + i * 4; h = r.randint(12, 30); sw = math.sin(f * 1.1 + i) * 2.5
        pts = [(x + sw * (k / h) ** 1.5 * (1 if i % 2 else -1), y - k) for k in range(0, h, 2)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]): c.line(x0, y0, x1, y1, ALG[1 + (i % 3)])
        if i % 3 == 0: c.p(pts[-1][0], pts[-1][1], ALG[3])
    return c.outline((6, 14, 12, 255)).im


def chainlamp(f):
    c = c48()
    for y in range(0, 22, 3): c.rect(23, y, 24, y + 1, C('3a3a42'))
    c.poly([(19, 22), (28, 22), (30, 26), (27, 34), (20, 34), (17, 26)], C('2a3432'))
    c.rect(20, 25, 27, 32, C('0e2a28'))
    k = [0, 0.3, 0.1][f]
    c.ell(23.5, 29, 2.5, 3, mix(C('4ac8b8'), C('d8fff4'), k)); c.p(23, 28, C('eafff8'))
    c.rect(21, 34, 26, 35, C('2a3432'))
    c = c.bevel(0.15, 0.3).outline()
    c.glow(23.5, 29, 10, (120, 235, 215), 0.3)
    return c.im


def tomb(leak):
    c = c48(); y = 47
    c.rect(6, y - 30, 41, y, ST[2]); c.rect(8, y - 28, 39, y - 2, ST[1])
    c.rect(10, y - 26, 37, y - 4, ST[3])   # the sealing slab
    c.line(10, y - 15, 37, y - 15, ST[2])
    for x in (14, 23, 32): c.rect(x, y - 23, x + 2, y - 19, ST[2])
    c.poly([(6, y - 30), (23.5, y - 36), (41, y - 30)], ST[3])
    if leak:
        c.poly([(20, y - 26), (24, y - 20), (22, y - 12), (26, y - 4)], (0, 0, 0, 0))
        for yy in range(y - 24, y): c.p(23 + (1 if yy % 5 == 0 else 0), yy, C('7ad8cc'))
        c.rect(21, y - 3, 27, y - 1, C('2a5a58'))
    c.speckle([ALG[1], ALG[2], ST[4]], 50, seed=7 + leak)
    return c.bevel().outline().im


def pew():
    c = c48(); y = 47
    c.rect(6, y - 18, 41, y - 15, C('2a2420')); c.rect(6, y - 9, 41, y - 7, C('3a302a'))
    for x in (7, 23, 39): c.rect(x, y - 18, x + 1, y, C('2a2420'))
    c.rect(6, y - 20, 41, y - 19, C('3e342c'))
    c.speckle([ALG[1], ALG[2], C('1a1614')], 40, seed=8)
    return c.bevel().outline().im


def candles(f):
    c = c48(); y = 47
    c.poly([(12, y), (14, y - 4), (34, y - 4), (36, y)], ST[3])
    r = random.Random(9)
    for i, (x, h) in enumerate([(16, 8), (20, 12), (24, 6), (28, 10), (32, 7)]):
        c.rect(x, y - 4 - h, x + 1, y - 4, BONE[2])
        fl = (f + i) % 3
        c.ell(x + 0.5, y - 6 - h, 1, 2 + (fl == 1), mix(C('4ae0cc'), C('e0fff8'), fl * 0.3))
    c = c.bevel(0.1, 0.25).outline()
    for x in (16, 20, 24, 28, 32): c.glow(x, y - 12, 6, (120, 240, 220), 0.25)
    return c.im


def clam(f):
    c = c48(); y = 47
    c.ell(24, y - 3, 12, 3, C('3a3a48'))
    if f:
        c.poly([(12, y - 3), (15, y - 14), (24, y - 17), (33, y - 14), (36, y - 3)], C('4a4a5a'))
        for i in range(5): c.line(14 + i * 5, y - 4, 16 + i * 4, y - 14, C('5a5a6e'))
        c.ell(24, y - 4, 3, 2.5, C('eef6ff')); c.p(23, y - 5, C('ffffff'))
    else:
        c.poly([(12, y - 3), (16, y - 7), (32, y - 7), (36, y - 3)], C('4a4a5a'))
        c.rect(16, y - 5, 32, y - 4, C('e0f0ff'))
    c = c.bevel(0.2, 0.3).outline()
    c.glow(24, y - 5, 9, (200, 240, 255), 0.35 if f else 0.2)
    return c.im


def tidemark():
    c = c48(); y = 47
    c.rect(22, y - 26, 25, y, ST[3])
    for i, yy in enumerate(range(y - 24, y, 5)): c.rect(21, yy, 26, yy, [C('c8b070'), ST[1]][i % 2]); c.p(27, yy, C('c8b070') if i % 2 == 0 else ST[1])
    c.poly([(21, y - 12), (26, y - 10), (26, y), (21, y)], ALG[1])
    return c.bevel().outline().im


def wellcover():
    c = c48(); y = 47
    c.rect(12, y - 5, 35, y, ST[2]); c.rect(12, y - 7, 35, y - 6, ST[4])
    for x in range(14, 34, 4): c.rect(x, y - 5, x + 1, y, C('1c2a2a'))
    c.rect(22, y - 11, 25, y - 7, C('3a3a42')); c.p(23, y - 10, C('8a8a90'))
    return c.bevel().outline().im


def sluice():
    c = c48(); y = 47
    c.rect(10, y - 14, 37, y, ST[2]); c.ell(23.5, y - 22, 9, 9, C('3a3a40')); c.ell(23.5, y - 22, 6, 6, (0, 0, 0, 0))
    for a in range(0, 360, 45):
        t = math.radians(a); c.line(23.5, y - 22, 23.5 + math.cos(t) * 8, y - 22 + math.sin(t) * 8, C('4a4a52'))
    c.ell(23.5, y - 22, 2, 2, BRZ[3]); c.rect(13, y - 8, 34, y - 4, C('0e2a28'))
    for x in range(14, 34, 3): c.p(x, y - 6, C('4ac8b8'))
    return c.bevel().outline().im


def coral():
    c = c48(); y = 47; r = random.Random(11)
    for i in range(5):
        x = 14 + i * 5
        pts = [(x, y), (x + r.randint(-3, 3), y - 8), (x + r.randint(-5, 5), y - 14 - r.randint(0, 8))]
        col = [C('7a3a4a'), C('a85a5a'), C('5a4a6a'), C('3a6a6a')][i % 4]
        c.thick(pts, col, 2); c.p(pts[-1][0], pts[-1][1] - 1, lit(col, 0.4))
        c.line(pts[1][0], pts[1][1], pts[1][0] + 4, pts[1][1] - 5, col)
    return c.bevel().outline().im


def build_db():
    items = [('gravecross', [gravecross()]), ('gravestone', [gravestone()]), ('cairn', [cairn()]), ('weeds', [weeds(f) for f in range(6)]),
             ('chainlamp', [chainlamp(f) for f in (0, 1, 2, 1)]), ('tomb', [tomb(False)]), ('tomb_leak', [tomb(True)]), ('pew', [pew()]),
             ('candles_db', [candles(f) for f in range(3)]), ('pearlclam', [clam(0), clam(1), clam(1), clam(1)]), ('tidemark', [tidemark()]),
             ('wellcover', [wellcover()]), ('sluice', [sluice()]), ('coral', [coral()])]
    sheet('xsa_db', 48, 48, items, ms={'weeds': 220, 'chainlamp': 140, 'candles_db': 130, 'pearlclam': 1400})


# ============================================================ the Drowned Saint (landmark of the Sunken Nave)
def saint():
    W, H = 176, 416; c = Cv(W, H); cx = W // 2
    MARB = [C('0e1a1c'), C('1a2c2e'), C('2a4442'), C('3e5e5a'), C('5a7e78'), C('86a8a0')]
    # plinth: three tiers (cols 46..56 rows 32..37 = the bottom 96 px)
    for i, (w, h) in enumerate([(88, 32), (80, 32), (72, 32)]):
        y1 = H - i * 32; c.rect(cx - w, y1 - h, cx + w - 1, y1 - 1, MARB[2 + (i % 2)])
        c.rect(cx - w, y1 - h, cx + w - 1, y1 - h + 2, MARB[4])
    # robe from the plinth up (the body is solid rows 18..31: 112 px wide, 224 tall)
    robe = [(cx - 56, H - 96), (cx - 50, H - 200), (cx - 40, H - 280), (cx - 30, H - 318), (cx + 30, H - 318), (cx + 40, H - 280), (cx + 50, H - 200), (cx + 56, H - 96)]
    c.poly(robe, MARB[3]); cyl_shade(c, MARB, (cx - 56, H - 318, cx + 56, H - 97), key=MARB[3])
    for k in range(-4, 5):   # folds
        x0 = cx + k * 11
        for y in range(H - 300, H - 97, 1):
            x = x0 + math.sin(y / 23 + k) * 2 + k * (y - (H - 300)) / 60
            if c.g(int(x), y)[3]: c.p(x, y, MARB[1] if k % 2 else MARB[2])
    # hood, face, arms raised to the halo
    c.ell(cx, H - 334, 22, 26, MARB[3]); cyl_shade(c, MARB, (cx - 22, H - 360, cx + 22, H - 318), key=MARB[3])
    c.ell(cx + 2, H - 330, 11, 14, MARB[5]); c.line(cx - 3, H - 333, cx + 1, H - 333, MARB[2]); c.line(cx + 5, H - 333, cx + 9, H - 333, MARB[2])
    for side in (-1, 1):
        c.thick([(cx + side * 30, H - 300), (cx + side * 42, H - 340), (cx + side * 38, H - 384)], MARB[3], 10)
        c.thick([(cx + side * 29, H - 302), (cx + side * 41, H - 342), (cx + side * 37, H - 386)], MARB[4], 3)
    # the halo ring the perch sits on (top of the ring = 16 px from the sprite top)
    c.ell(cx, H - 390, 42, 10, BRZ[3]); c.ell(cx, H - 390, 36, 6, (0, 0, 0, 0))
    c.rect(cx - 40, 16, cx + 40, 18, BRZ[4])
    # the drowned part: algae, barnacles and tide-lines below the waterline (row 18 = 320 px up from the base)
    r = random.Random(12)
    for _ in range(900):
        x, y = r.randint(0, W - 1), r.randint(H - 316, H - 1)
        if c.g(x, y)[3] and r.random() < 0.6: c.p(x, y, r.choice([ALG[0], ALG[1], ALG[2], MARB[1]]))
    for _ in range(60):
        x, y = r.randint(10, W - 10), r.randint(H - 300, H - 20)
        if c.g(x, y)[3]: c.ell(x, y, 1.5, 1.2, C('8a8a80')); c.p(x, y, C('2a2a28'))
    c.outline()
    c.glow(cx, H - 390, 44, (120, 230, 215), 0.18)
    return c.im


def rosewin():
    c = Cv(160, 160); cx = cy = 80
    c.ell(cx, cy, 76, 76, ST[1]); c.ell(cx, cy, 70, 70, C('0e3a3a'))
    for i in range(12):
        t = i / 12 * 6.283
        c.ell(cx + math.cos(t) * 48, cy + math.sin(t) * 48, 16, 16, C('1a5a58') if i % 2 else C('14484a'))
        c.thick([(cx, cy), (cx + math.cos(t) * 70, cy + math.sin(t) * 70)], ST[2], 3)
    c.ell(cx, cy, 20, 20, C('2a7a74')); c.ell(cx, cy, 8, 8, ST[3])
    for i in range(12):
        t = (i + 0.5) / 12 * 6.283; c.ell(cx + math.cos(t) * 30, cy + math.sin(t) * 30, 5, 5, C('3a8a80'))
    r = random.Random(13)
    for _ in range(300):
        x, y = r.randint(0, 159), r.randint(0, 159)
        if c.g(x, y)[3]: c.p(x, y, lit(c.g(x, y), (BAYER[y % 4][x % 4] - 8) / 60))
    c.outline()
    return c.im


def bigbell():
    c = Cv(64, 80); cx = 32
    for y in range(0, 16, 3): c.rect(cx - 1, y, cx, y + 1, C('3a3a42'))
    c.rect(cx - 5, 16, cx + 4, 20, BRZ[1])
    c.poly([(cx - 10, 20), (cx + 10, 20), (cx + 14, 34), (cx + 16, 58), (cx + 26, 70), (cx - 26, 70), (cx - 16, 58), (cx - 14, 34)], BRZ[2])
    cyl_shade(c, BRZ, (cx - 26, 20, cx + 26, 70), key=BRZ[2])
    c.rect(cx - 27, 68, cx + 26, 71, BRZ[1]); c.ell(cx, 71, 22, 3, C('0a1210'))
    for x in range(cx - 12, cx + 12, 5): c.p(x, 40, BRZ[4]); c.p(x + 1, 44, BRZ[4])
    r = random.Random(14)
    for _ in range(90):
        x, y = r.randint(cx - 24, cx + 24), r.randint(22, 70)
        if c.g(x, y)[3]: c.p(x, y, r.choice([BRZ[3], BRZ[4], C('6ab89a')]))
    c.outline()
    return c.im


def lagoon():
    W, H = 640, 352; c = Cv(W, H)
    for y in range(H):   # the water column: dark above, a luminous band where the light pools, dark at the bed
        t = y / H; k = math.exp(-((t - 0.55) / 0.28) ** 2)
        col = mix(C('071a1e'), C('1e6664'), k * 0.85)
        for x in range(W):
            d = (BAYER[y % 4][x % 4] - 7.5) / 200
            c.im.putpixel((x, y), mix(col, C('1a5a58'), max(0, min(1, d * 6 + 0.05))) if d > 0.02 else col)
    r = random.Random(15)
    for depth in range(2):   # a drowned arcade, two ranks deep, broken
        span = [150, 190][depth]; col = [C('123c3c'), C('1e5654')][depth]; hi = [C('1e5654'), C('3a8a84')][depth]
        base = H - 10 + depth * 10; pw = [16, 22][depth]; ah = [150, 120][depth]
        for n, x0 in enumerate(range(-40 + depth * 70, W + span, span)):
            broken = r.random() < 0.3
            top = base - ah - (40 if not broken else -r.randint(10, 60))
            c.rect(x0, top, x0 + pw, base, col); c.rect(x0, top, x0 + 2, base, hi)
            c.rect(x0 - 4, top - 6, x0 + pw + 4, top, hi)
            if broken or n % 3 == 2: continue
            for k in range(span - pw):   # the arch: a thick band
                t = k / (span - pw); yy = top - 4 - math.sin(t * math.pi) * 46
                c.rect(x0 + pw + k, int(yy) - 12, x0 + pw + k, int(yy), col); c.p(x0 + pw + k, int(yy) - 12, hi)
    # a fallen saint's head on the bed
    c.ell(420, H - 28, 46, 30, C('123a3a')); c.ell(410, H - 36, 30, 20, C('184846')); c.rect(380, H - 34, 404, H - 32, C('0a2426')); c.rect(420, H - 34, 440, H - 32, C('0a2426'))
    for _ in range(26):   # slanting rays
        x = r.randint(-100, W); w = r.randint(3, 10)
        for y in range(0, int(H * 0.8)):
            xx = x + int(y * 0.35)
            a = 0.06 * (1 - y / (H * 0.8))
            for q in range(w):
                if 0 <= xx + q < W: c.im.putpixel((xx + q, y), mix(c.im.getpixel((xx + q, y)), C('9ae8e0'), a))
    for _ in range(50): c.glow(r.randint(0, W), r.randint(H // 2, H - 10), r.randint(2, 3), (200, 240, 255), 0.6)
    return c.im


if __name__ == '__main__':
    build_db()
    sheet('xsa_saint', 176, 416, [('saint', [saint()])])
    sheet('xsa_rosewin', 160, 160, [('rosewin', [rosewin()])])
    sheet('xsa_bell', 64, 80, [('bigbell', [bigbell()])])
    sheet('xsa_lagoon', 640, 352, [('lagoonback', [lagoon()])])
    print('ok')
