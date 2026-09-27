#!/usr/bin/env python3
"""SA — Crimson Manor props for the new rooms (CM9–CM17).
   xsa_cm 64x64 props; xsa_portrait (the Countess's family portrait, 80x64); xsa_chand (the fallen chandelier, 112x64).
   Run: python3 art/gen_xsa_cm.py"""
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from xsa_kit import Cv, C, lit, mix, sheet, OUT, cyl_shade

WD = [C('1a0e10'), C('2a1616'), C('3e2220'), C('56302a'), C('744634')]      # dark lacquered wood
RED = [C('3a0810'), C('5e0e1c'), C('8a1828'), C('b82a3a')]
GOLD = [C('4a3414'), C('7a5a24'), C('b08a3a'), C('e8c878')]
IR = [C('121014'), C('221e26'), C('36303c'), C('544c5c')]
STN = [C('141016'), C('241e26'), C('362c38'), C('4c404e'), C('6a5a6a')]
PAPER = C('d8ccb0')


def c64(): return Cv(64, 64)


def chimney():
    c = c64(); y = 63
    c.rect(20, y - 34, 43, y, STN[2]); c.rect(18, y - 38, 45, y - 34, STN[3])
    for row in range(0, 34, 4):
        off = 4 if (row // 4) % 2 else 0
        c.line(20, y - row, 43, y - row, STN[1])
        for x in range(20 + off, 44, 8): c.line(x, y - row, x, y - row - 3, STN[1])
    for x in (24, 32, 38): c.rect(x, y - 44, x + 3, y - 38, C('4a3a3a')); c.rect(x, y - 45, x + 3, y - 44, C('6a4a40'))
    c.poly([(18, y - 8), (45, y - 16), (45, y), (18, y)], (0, 0, 0, 0)) if False else None
    return c.bevel().outline().im


def weathervane():
    c = c64(); y = 63
    c.rect(31, y - 36, 32, y, IR[2]); c.line(24, y - 28, 39, y - 28, IR[2]); c.line(31, y - 35, 31, y - 21, IR[2])
    c.poly([(22, y - 40), (34, y - 44), (42, y - 40), (34, y - 37)], IR[3])   # a crow in iron
    c.poly([(40, y - 41), (44, y - 42), (41, y - 39)], IR[3])
    c.p(24, y - 30, C('b08a3a')); c.p(38, y - 30, C('b08a3a'))
    return c.bevel().outline().im


def crows(f):
    c = c64(); y = 63
    for i, x in enumerate((20, 34, 44)):
        up = (f + i) % 2
        c.ell(x, y - 4, 4, 3, C('14121a')); c.ell(x + 3, y - 7, 2, 2, C('14121a')); c.p(x + 5, y - 7, C('c8a040'))
        c.p(x + 3, y - 8, C('d02020'))
        if up: c.poly([(x - 2, y - 5), (x - 6, y - 12), (x + 1, y - 6)], C('1e1a26'))
        c.line(x - 1, y - 1, x - 1, y, C('3a3030'))
    return c.outline((6, 4, 8, 255)).im


def gutterspout():
    c = c64(); y = 63
    c.poly([(12, y - 20), (40, y - 26), (48, y - 22), (40, y - 16), (12, y - 14)], STN[3])
    c.ell(46, y - 24, 5, 4, STN[3]); c.p(48, y - 25, RED[3]); c.poly([(49, y - 22), (54, y - 21), (49, y - 20)], STN[2])
    c.poly([(30, y - 26), (34, y - 34), (38, y - 26)], STN[2])
    return c.bevel().outline().im


def grandclock(f):
    c = c64(); y = 63
    c.rect(24, y - 56, 39, y, WD[2]); c.rect(22, y - 60, 41, y - 56, WD[3]); c.poly([(22, y - 60), (31.5, y - 64), (41, y - 60)], WD[3])
    c.ell(31.5, y - 48, 6, 6, PAPER); c.ell(31.5, y - 48, 6, 6, (0, 0, 0, 0)) if False else None
    c.ell(31.5, y - 48, 5, 5, PAPER); c.line(31.5, y - 48, 31.5, y - 52, OUT); c.line(31.5, y - 48, 34, y - 47, OUT)
    c.rect(27, y - 38, 36, y - 8, C('100a0c'))
    sw = [-3, 3][f]; c.line(31.5, y - 38, 31.5 + sw, y - 14, GOLD[2]); c.ell(31.5 + sw, y - 13, 2.5, 2.5, GOLD[3])
    c.rect(23, y - 4, 40, y, WD[1])
    return c.bevel().outline().im


def bust():
    c = c64(); y = 63
    c.rect(26, y - 22, 37, y, STN[3]); c.rect(24, y - 24, 39, y - 22, STN[4]); c.rect(24, y - 2, 39, y, STN[2])
    c.poly([(22, y - 24), (26, y - 34), (37, y - 34), (41, y - 24)], C('8a8290'))
    c.ell(31.5, y - 40, 5, 6, C('9a929e')); c.p(30, y - 41, C('3a3440')); c.p(33, y - 41, C('3a3440'))
    c.poly([(26, y - 44), (31, y - 48), (37, y - 44), (35, y - 42), (28, y - 42)], C('7a727e'))
    return c.bevel().outline().im


def rug():
    c = c64(); y = 63
    c.rect(4, y - 3, 59, y, RED[1]); c.rect(6, y - 3, 57, y - 2, RED[2])
    for x in range(8, 56, 6): c.p(x, y - 2, GOLD[2]); c.p(x + 3, y - 1, GOLD[1])
    for x in range(4, 60, 3): c.p(x, y, GOLD[1])
    return c.outline().im


def bookcase(fallen=False):
    c = c64(); y = 63
    c.rect(16, y - 46, 47, y, WD[2]); c.rect(18, y - 44, 45, y - 2, C('0c0608'))
    c.rect(14, y - 48, 49, y - 46, WD[3])
    r = random.Random(5 + fallen)
    for sy in (y - 34, y - 22, y - 11, y - 2):
        c.rect(17, sy, 46, sy + 1, WD[3])
        x = 19
        while x < 44:
            w = r.randint(1, 3); h = r.randint(6, 10); col = r.choice([RED[1], RED[2], C('2a3a4a'), C('3a2a1a'), C('4a4028'), C('2a2a2a')])
            if fallen and r.random() < 0.4: x += w + 1; continue
            c.rect(x, sy - h, x + w, sy - 1, col); c.p(x, sy - h + 2, GOLD[2])
            x += w + 1
    c = c.bevel().outline()
    if fallen:
        c.im = c.im.rotate(-78, expand=False, center=(32, 60)); c = c.outline()
        for x in range(4, 60, 5): c.rect(x, y - 2, x + 3, y, r.choice([RED[1], C('2a3a4a'), C('4a4028')]))
    return c.im


def books():
    c = c64(); y = 63; r = random.Random(8)
    for i in range(10):
        x = 10 + r.randint(0, 40); yy = y - r.randint(0, 6)
        col = r.choice([RED[1], RED[2], C('2a3a4a'), C('3a2a1a'), C('4a4028')])
        c.rect(x, yy - 2, x + r.randint(5, 8), yy, col); c.line(x, yy - 1, x + 3, yy - 1, GOLD[2])
    for i in range(6): c.rect(12 + i * 7, y - 9 + (i % 3), 16 + i * 7, y - 8 + (i % 3), PAPER)
    return c.bevel().outline().im


def bed():
    c = c64(); y = 63
    c.rect(6, y - 14, 57, y - 6, RED[1]); c.rect(6, y - 16, 57, y - 14, C('d8ccc0'))
    c.rect(4, y - 30, 8, y, WD[3]); c.rect(55, y - 22, 59, y, WD[3]); c.rect(4, y - 32, 8, y - 30, GOLD[2])
    c.poly([(8, y - 30), (20, y - 36), (8, y - 20)], RED[2])
    c.ell(14, y - 18, 5, 3, C('e8e0d8')); c.rect(6, y - 6, 57, y - 4, WD[2])
    return c.bevel().outline().im


def wardrobe():
    c = c64(); y = 63
    c.rect(18, y - 50, 45, y, WD[2]); c.rect(16, y - 53, 47, y - 50, WD[3]); c.line(31, y - 48, 31, y - 3, WD[0])
    for x in (21, 34): c.rect(x, y - 46, x + 8, y - 6, WD[3]); c.rect(x + 1, y - 45, x + 7, y - 7, WD[2])
    c.p(29, y - 26, GOLD[3]); c.p(33, y - 26, GOLD[3])
    c.rect(19, y - 2, 21, y, WD[1]); c.rect(42, y - 2, 44, y, WD[1])
    return c.bevel().outline().im


def hearth(f):
    c = c64(); y = 63
    c.rect(10, y - 34, 53, y, STN[3]); c.rect(8, y - 38, 55, y - 34, STN[4]); c.rect(18, y - 26, 45, y, C('0a0608'))
    c.poly([(18, y - 26), (31.5, y - 32), (45, y - 26)], C('0a0608'))
    for i in range(5):
        x = 22 + i * 5; h = 8 + ((f + i) % 3) * 4
        c.poly([(x - 3, y), (x, y - h), (x + 3, y)], C('ff7a30' if i % 2 else 'ffa040')); c.p(x, y - h + 3, C('ffe080'))
    c.rect(20, y - 2, 43, y, C('3a1a10'))
    c = c.bevel(0.12, 0.25).outline()
    c.glow(31.5, y - 8, 16, (255, 140, 60), 0.3)
    return c.im


def bellboard():
    c = c64(); y = 63
    c.rect(10, y - 30, 53, y - 6, WD[2]); c.rect(12, y - 28, 51, y - 8, WD[1])
    names = ['Salon', 'Library', 'Study', 'Countess', 'Nursery', 'Ballroom']
    for i in range(6):
        x = 16 + (i % 3) * 13; yy = y - 24 + (i // 3) * 10
        c.ell(x, yy, 2.5, 2.5, GOLD[2]); c.p(x - 1, yy - 1, GOLD[3]); c.line(x + 3, yy + 3, x + 7, yy + 3, PAPER)
    c.rect(30, y - 6, 33, y, WD[2])
    return c.bevel().outline().im


def piano():
    c = c64(); y = 63
    c.poly([(4, y - 26), (40, y - 26), (58, y - 22), (60, y - 16), (4, y - 16)], C('0e0a0e'))
    c.poly([(8, y - 26), (44, y - 44), (48, y - 42), (14, y - 26)], C('1a141c'))   # the raised lid
    c.rect(4, y - 16, 36, y - 14, C('e8e0d0'))
    for x in range(5, 36, 2): c.p(x, y - 16, C('141014'))
    for x in (8, 34, 54): c.rect(x, y - 14, x + 1, y, C('141014'))
    c.p(10, y - 25, GOLD[2]); c.p(46, y - 23, GOLD[2])
    c.rect(12, y - 30, 20, y - 26, PAPER)   # sheet music
    return c.bevel(0.25, 0.3).outline().im


def roses():
    c = c64(); y = 63
    c.poly([(16, y), (18, y - 10), (46, y - 10), (48, y)], STN[3]); c.rect(16, y - 12, 48, y - 10, STN[4])
    r = random.Random(12)
    for i in range(12):
        x = 20 + i * 2.2; pts = [(x, y - 11), (x + r.randint(-4, 4), y - 20), (x + r.randint(-6, 6), y - 28 - r.randint(0, 6))]
        c.thick(pts, C('2a241a'), 1)
        c.ell(pts[-1][0], pts[-1][1], 2, 2, r.choice([C('3a0a14'), C('4a1018'), C('2a0a10')])); c.p(pts[-1][0] - 1, pts[-1][1] - 1, C('6a1a24'))
        if i % 3 == 0: c.p(pts[1][0] + 2, pts[1][1] + 3, C('4a1018'))   # fallen petals
    return c.bevel(0.1, 0.2).outline().im


def trellis():
    c = c64(); y = 63
    for x in (18, 45):
        c.rect(x, y - 52, x + 1, y, IR[2])
    for k in range(18):
        t = k / 17 * math.pi; c.p(31.5 - math.cos(t) * 13.5, y - 52 - math.sin(t) * 10, IR[2])
    for yy in range(y - 50, y, 8): c.line(18, yy, 46, yy - 6, IR[1])
    r = random.Random(13)
    for _ in range(40):
        x, yy = r.randint(16, 48), r.randint(y - 60, y)
        c.p(x, yy, r.choice([C('2a241a'), C('3a2e20'), C('4a1018')]))
    return c.outline().im


def canvasback():
    c = c64(); y = 63
    c.rect(14, y - 40, 49, y - 8, C('8a7a60')); c.rect(12, y - 42, 51, y - 40, WD[3]); c.rect(12, y - 8, 51, y - 6, WD[3])
    c.rect(12, y - 42, 14, y - 6, WD[3]); c.rect(49, y - 42, 51, y - 6, WD[3]); c.line(14, y - 40, 49, y - 8, WD[2]); c.line(49, y - 40, 14, y - 8, WD[2])
    c.ell(28, y - 26, 1, 1, OUT); c.ell(35, y - 26, 1, 1, OUT)   # the eyeholes the servants cut
    c.rect(28, y - 6, 35, y, WD[1])
    return c.bevel().outline().im


def pipes():
    c = c64(); y = 63
    for x in (20, 28): c.rect(x, 0, x + 3, y, IR[2]); c.rect(x, 0, x, y, IR[3])
    for yy in (10, 30, 50): c.rect(18, yy, 33, yy + 3, IR[1])
    c.rect(28, 38, 44, 41, IR[2]); c.rect(42, 38, 45, 50, IR[2]); c.ell(43.5, 44, 4, 4, C('6a2a20')); c.p(42, 43, C('a84a30'))
    return c.bevel().outline().im


def lamp(f):
    c = c64(); y = 63
    c.rect(31, y - 22, 32, y, IR[2]); c.rect(28, y - 2, 35, y, IR[2])
    c.poly([(26, y - 30), (37, y - 30), (35, y - 22), (28, y - 22)], IR[1]); c.rect(28, y - 29, 35, y - 23, C('3a1a10'))
    c.ell(31.5, y - 26, 2, 2.5 + (f == 1), mix(C('ff8a40'), C('ffe0a0'), f * 0.3))
    c.poly([(27, y - 30), (31.5, y - 34), (36, y - 30)], IR[2])
    c = c.bevel(0.15, 0.3).outline()
    c.glow(31.5, y - 26, 10, (255, 170, 100), 0.35)
    return c.im


def laundry():
    c = c64()
    c.line(0, 2, 63, 4, C('8a8070'))
    for i, (x, col, h) in enumerate([(6, C('d8d0c0'), 16), (20, C('8a1828'), 12), (34, C('c8c0b0'), 20), (48, C('3a3a4a'), 14)]):
        c.rect(x, 3, x + 9, 3 + h, col); c.rect(x, 3 + h, x + 9, 4 + h, lit(col, -0.3))
        c.p(x + 1, 3, C('5a4a3a')); c.p(x + 8, 3, C('5a4a3a'))
    return c.bevel(0.1, 0.25).outline().im


def spyhole():
    c = c64(); y = 63
    c.rect(24, y - 38, 39, y - 22, WD[2]); c.rect(26, y - 36, 37, y - 24, WD[1])
    c.rect(29, y - 31, 34, y - 29, C('ffd090')); c.p(31, y - 30, C('fff0c0'))
    c.rect(28, y - 22, 35, y - 20, WD[3])
    c = c.bevel().outline(); c.glow(31.5, y - 30, 8, (255, 210, 140), 0.3)
    return c.im


def cot():
    c = c64(); y = 63
    c.rect(10, y - 10, 53, y - 7, C('6a5a4a')); c.rect(10, y - 12, 53, y - 10, C('8a8070'))
    for x in (10, 51): c.rect(x, y - 7, x + 2, y, WD[2])
    c.ell(16, y - 13, 5, 2, C('c8c0b0')); c.rect(24, y - 13, 50, y - 11, C('4a3a3a'))
    return c.bevel().outline().im


def stove(f):
    c = c64(); y = 63
    c.rect(18, y - 22, 45, y, IR[1]); c.rect(16, y - 24, 47, y - 22, IR[2]); c.rect(36, y - 44, 40, y - 24, IR[1])
    c.rect(22, y - 16, 33, y - 6, C('2a0a06')); c.rect(23, y - 12, 32, y - 7, C('ff8030' if f else 'ffa040'))
    c.ell(26, y - 27, 4, 2, IR[3])
    c = c.bevel().outline(); c.glow(27.5, y - 10, 10, (255, 140, 60), 0.3)
    return c.im


def desk():
    c = c64(); y = 63
    c.rect(8, y - 20, 55, y - 17, WD[3]); c.rect(10, y - 17, 22, y, WD[2]); c.rect(42, y - 17, 53, y, WD[2])
    for yy in (y - 13, y - 7): c.p(16, yy, GOLD[3]); c.p(47, yy, GOLD[3])
    c.rect(26, y - 23, 38, y - 20, PAPER); c.line(28, y - 22, 36, y - 22, C('5a4a3a'))
    c.rect(44, y - 26, 46, y - 20, GOLD[2]); c.ell(45, y - 28, 1.5, 2, C('ffc070'))   # a candle
    c.rect(14, y - 24, 18, y - 20, C('1a1a2a')); c.line(18, y - 24, 22, y - 30, PAPER)   # ink and quill
    return c.bevel().outline().im


def globe():
    c = c64(); y = 63
    c.rect(30, y - 12, 33, y, WD[3]); c.rect(24, y - 2, 39, y, WD[2])
    c.ell(31.5, y - 22, 10, 10, C('3a4a3a')); c.ell(28, y - 25, 4, 3, C('7a6a4a')); c.ell(35, y - 18, 3, 4, C('7a6a4a'))
    for k in range(20):
        t = k / 19 * math.pi; c.p(31.5 + math.cos(t) * 12, y - 22 - math.sin(t) * 12, GOLD[2])
    return c.bevel().outline().im


def chalk():
    c = c64(); y = 63
    for row in range(5):
        yy = y - 40 + row * 7; x = 8 + (row % 2) * 4
        for i in range(12 + row):
            if (i * 7 + row) % 5: c.p(x + i * 3, yy + (i % 2), C('c8c4b8', 170))
    for i in range(4): c.line(44 + i * 2, y - 20, 44 + i * 2, y - 12, C('c8c4b8', 170))
    c.line(42, y - 16, 53, y - 17, C('c8c4b8', 170))
    return c.im


def build_cm():
    items = [('chimney', [chimney()]), ('weathervane', [weathervane()]), ('crows', [crows(0), crows(1)]), ('gutterspout', [gutterspout()]),
             ('grandclock', [grandclock(0), grandclock(1)]), ('bust', [bust()]), ('rug', [rug()]), ('bookcase', [bookcase()]),
             ('bookcase_fallen', [bookcase(True)]), ('books', [books()]), ('bed', [bed()]), ('wardrobe', [wardrobe()]),
             ('hearth', [hearth(f) for f in range(3)]), ('bellboard', [bellboard()]), ('piano', [piano()]), ('roses', [roses()]),
             ('trellis', [trellis()]), ('canvasback', [canvasback()]), ('pipes', [pipes()]), ('lamp_cm', [lamp(f) for f in (0, 1, 2, 1)]),
             ('laundry', [laundry()]), ('spyhole', [spyhole()]), ('cot', [cot()]), ('stove', [stove(0), stove(1)]), ('desk', [desk()]),
             ('globe', [globe()]), ('chalk', [chalk()])]
    sheet('xsa_cm', 64, 64, items, ms={'crows': 600, 'grandclock': 1000, 'hearth': 140, 'lamp_cm': 150, 'stove': 400})


def familyportrait():
    c = Cv(80, 64)
    c.rect(0, 0, 79, 63, GOLD[1]); c.rect(3, 3, 76, 60, GOLD[2]); c.rect(5, 5, 74, 58, C('120a0c'))
    for x in range(0, 80, 4): c.p(x, 0, GOLD[3]); c.p(x + 2, 63, GOLD[0])
    # the family: the Count (left, black), the Countess (centre, crimson, larger), the child (right, white)
    c.poly([(14, 58), (16, 30), (22, 24), (28, 30), (30, 58)], C('141018')); c.ell(22, 20, 4, 5, C('c8b8a8'))
    c.poly([(30, 58), (32, 28), (40, 20), (48, 28), (50, 58)], RED[1]); c.ell(40, 15, 5, 6, C('e0d0c8')); c.poly([(34, 12), (40, 7), (46, 12), (44, 16), (36, 16)], C('1a0a0c'))
    c.p(38, 15, OUT); c.p(42, 15, OUT)   # her eyes (53_sa.js lights them)
    c.poly([(52, 58), (54, 40), (58, 36), (62, 40), (64, 58)], C('d8d0c8')); c.ell(58, 32, 3, 4, C('e8dcd4'))
    for _ in range(200):
        r = random.random
        x, y = int(6 + r() * 68), int(6 + r() * 52)
        px = c.g(x, y)
        if px[3]: c.p(x, y, lit(px, (r() - 0.5) * 0.15))
    c.outline()
    return c.im


def fallenchandelier():
    c = Cv(112, 64); y = 63
    c.ell(56, y - 10, 50, 10, GOLD[1]); c.ell(56, y - 12, 44, 7, GOLD[2]); c.ell(56, y - 12, 36, 4, C('0c0808'))
    for i in range(9):
        x = 14 + i * 10.5; c.thick([(56, y - 26), (x, y - 12)], GOLD[1], 2)
        c.rect(x - 1, y - 18, x + 1, y - 12, PAPER)
    c.ell(56, y - 28, 6, 6, GOLD[2])
    r = random.Random(20)
    for _ in range(60): c.p(r.randint(4, 108), r.randint(y - 6, y), r.choice([C('c8e0f0'), C('8aa0b8'), C('f0f8ff')]))   # crystal drops
    for i in range(3): c.thick([(56 + i * 3, y - 34), (60 + i * 6, 0)], IR[2], 1)
    c.bevel(0.2, 0.3).outline()
    return c.im


if __name__ == '__main__':
    build_cm()
    sheet('xsa_portrait', 80, 64, [('familyportrait', [familyportrait()])])
    sheet('xsa_chand', 112, 64, [('fallenchandelier', [fallenchandelier()])])
    print('ok')
