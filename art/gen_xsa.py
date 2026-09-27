#!/usr/bin/env python3
"""SA (Expansion 3: Thornveil, Barrows, Crimson new rooms) — shared sheets + Thornveil props.
   xsa_skin   16x16 texture tiles that repaint solid cells (bark, elder, leaves, slate, brick, glass, tomb)
   xsa_icons  16x16 icons: c_x3_thorn, c_x3_lung, xsa_key1..3
   xsa_tv     48x48 Thornveil props;  xsa_tvbig 96x128 (root arches);  xsa_elder, xsa_oak (painted back trees)
   xsa_thornveil 32x64 the burning thorn curtain (the Ember Dash veil in Thornveil)
Run: python3 art/gen_xsa.py   (then gen_xsa_db.py, gen_xsa_cm.py)"""
import math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from xsa_kit import Cv, C, lit, mix, sheet, OUT, cyl_shade, bark_lines, leaf_clump

R = random.Random(7)
BARK = [C('1a130e'), C('2a1f16'), C('3b2b1d'), C('503b27'), C('6b5038')]
MOSS = [C('14281a'), C('1e3a22'), C('2f5a32'), C('4f8a4a'), C('7aa05a')]
GLOW = C('78ffbe'); BONE = [C('6e6656'), C('a89f86'), C('d8cfb4'), C('f0e8d4')]
RUST = [C('3a1c10'), C('5a2e18'), C('7a3e22'), C('a85a2e')]
IRON = [C('141218'), C('26232c'), C('3a3642'), C('5a5462')]


# ============================================================ skins
def tex(base, dark, light, seed, kind):
    c = Cv(16, 16); r = random.Random(seed)
    c.rect(0, 0, 15, 15, base)
    if kind in ('bark', 'elder'):
        for x in range(0, 16, 4):   # vertical fissures
            xx = x + r.randint(0, 2)
            for y in range(16):
                if r.random() < 0.85: c.p(xx + (1 if (y // 5) % 2 else 0), y, dark)
            for y in range(r.randint(0, 6), r.randint(8, 16)): c.p(xx + 2, y, light)
        if r.random() < 0.35:   # a knot
            kx, ky = r.randint(4, 11), r.randint(4, 11); c.ell(kx, ky, 2, 2, dark); c.p(kx - 1, ky - 1, light)
    elif kind == 'leaves':
        for _ in range(26):
            x, y = r.randint(-1, 15), r.randint(-1, 15); col = r.choice([dark, light, base, lit(light, 0.15)])
            c.ell(x, y, r.randint(1, 2), 1, col)
    elif kind == 'slate':
        for row in range(4):
            y = row * 4; off = 4 if row % 2 else 0
            c.line(0, y, 15, y, dark)
            for x in range(off, 16, 8): c.line(x, y, x, y + 3, dark)
            c.line(0, y + 1, 15, y + 1, light)
    elif kind == 'brick':
        for row in range(4):
            y = row * 4; off = 4 if row % 2 else 0
            c.line(0, y + 3, 15, y + 3, dark)
            for x in range(off, 16, 8): c.line(x, y, x, y + 3, dark)
            c.line(0, y, 15, y, light)
    elif kind == 'glass':
        c.rect(0, 0, 15, 15, (40, 52, 76, 150)); c.rect(0, 0, 15, 1, dark); c.rect(0, 0, 1, 15, dark); c.rect(8, 0, 8, 15, dark)
        for i in range(5): c.p(3 + i, 10 - i, (200, 220, 245, 170))
        c.p(12, 4, (220, 235, 255, 200))
    elif kind == 'tomb':
        c.line(0, 0, 15, 0, light); c.line(0, 15, 15, 15, dark); c.line(15, 0, 15, 15, dark)
        for _ in range(8): c.p(r.randint(1, 14), r.randint(1, 14), dark)
    c.speckle([dark, light], 6, seed=seed)
    return c.im


def build_skins():
    items = []
    sets = {'bark': BARK, 'elder': [C('140e0a'), C('221810'), C('33251a'), C('4a3624'), C('6a4e32')],
            'leaves': [C('07120b'), C('10231a'), C('1b3a25'), C('2c5a35'), C('4f8a4a')],
            'slate': [C('0c0a10'), C('1b1822'), C('2a2533'), C('3d3649'), C('4e4660')],
            'brick': [C('140b0c'), C('241315'), C('361c1e'), C('4a2628'), C('6a3a36')],
            'glass': [C('0a0c14'), C('141a26'), C('2c3a52'), C('6a86a8'), C('c8dcf0')],
            'tomb': [C('081012'), C('10201f'), C('1a302e'), C('284644'), C('4a7a70')]}
    for name, P in sets.items():
        base, dark, light = P[2], P[1], P[3]
        items.append((name, [tex(base, dark, light, 11 * i + len(name), name) for i in range(4)]))
        if name in ('bark', 'elder'):
            L, Rr = [], []
            for i in range(2):
                a = tex(base, dark, light, 97 + i, name)
                cv = Cv(16, 16); cv.im = a.copy(); cv.d = __import__('PIL.ImageDraw', fromlist=['x']).Draw(cv.im)
                cv.rect(0, 0, 1, 15, P[0]); cv.rect(2, 0, 2, 15, P[4] if name == 'bark' else P[3]); L.append(cv.im)
                b = tex(base, dark, light, 131 + i, name)
                cv = Cv(16, 16); cv.im = b.copy(); cv.d = __import__('PIL.ImageDraw', fromlist=['x']).Draw(cv.im)
                cv.rect(14, 0, 15, 15, P[0]); cv.rect(13, 0, 13, 15, P[1]); Rr.append(cv.im)
            items += [(name + '_l', L), (name + '_r', Rr)]
    sheet('xsa_skin', 16, 16, items)


# ============================================================ icons
def build_icons():
    ic = []
    # Thornstep Ring: a braided bramble ring with one green-gold thorn
    c = Cv(16, 16)
    for a in range(0, 360, 12):
        t = math.radians(a); x, y = 8 + math.cos(t) * 5, 9 + math.sin(t) * 4
        c.ell(x, y, 1.2, 1.2, BARK[3] if (a // 24) % 2 else BARK[4])
    for a in (40, 130, 220, 310):
        t = math.radians(a); c.p(8 + math.cos(t) * 7, 9 + math.sin(t) * 6, MOSS[4])
    c.poly([(8, 1), (10, 5), (6, 5)], C('d8c070')); c.p(8, 2, C('fff0b0'))
    c.bevel().outline(); ic.append(('c_x3_thorn', [c.im]))
    # Drowned Lung: a pale pearl-lung, teal veins
    c = Cv(16, 16)
    c.ell(5.5, 9, 3.5, 5, C('c8e4dc')); c.ell(10.5, 9, 3.5, 5, C('b0d4cc')); c.rect(7, 2, 8, 6, C('9ac0b8'))
    for p in [(4, 8), (5, 10), (6, 12), (11, 8), (10, 10), (9, 12)]: c.p(*p, C('3aa8a0'))
    c.p(4, 6, C('ffffff'))
    c.bevel(0.1, 0.25).outline(); ic.append(('c_x3_lung', [c.im]))
    # keys: silver (V bow), portrait (gilt, frame bow), rook (black iron, feathered)
    for tag, cols in [('xsa_key1', [C('6a7280'), C('b8c0cc'), C('eef2f8')]), ('xsa_key2', [C('7a5a20'), C('c8a050'), C('ffe8a0')]),
                      ('xsa_key3', [C('1a1820'), C('3a3648'), C('7a7690')])]:
        c = Cv(16, 16)
        c.ell(4, 5, 3, 3, cols[1]); c.ell(4, 5, 1, 1, (0, 0, 0, 0))
        c.line(6, 7, 13, 14, cols[1], 2); c.rect(10, 13, 11, 15, cols[1]); c.rect(12, 11, 13, 12, cols[1])
        c.p(3, 3, cols[2]); c.p(8, 9, cols[2])
        if tag == 'xsa_key1': c.p(3, 5, cols[0]); c.p(5, 5, cols[0]); c.p(4, 6, cols[0])
        if tag == 'xsa_key3': c.p(1, 2, C('302838')); c.p(2, 1, C('302838'))
        c.outline(); ic.append((tag, [c.im]))
    sheet('xsa_icons', 16, 16, ic)


# ============================================================ Thornveil props (48x48, standing on the bottom row)
def base48():
    return Cv(48, 48)


def snare(shut):
    c = base48(); y = 47
    c.ell(24, y - 1, 9, 2, IRON[1]); c.rect(15, y - 1, 33, y, IRON[1])
    if not shut:
        for x in range(13, 36, 2): c.p(x, y - 3, IRON[3]); c.p(x, y - 2, IRON[2])
        c.rect(12, y - 2, 13, y, RUST[2]); c.rect(35, y - 2, 36, y, RUST[2])
        c.p(24, y - 3, RUST[3])
    else:
        c.poly([(15, y - 1), (24, y - 11), (33, y - 1)], IRON[2])
        for i in range(5): c.p(19 + i * 2, y - 5 - (i % 2), IRON[3])
        c.line(24, y - 11, 24, y - 1, IRON[0])
        c.p(22, y - 7, RUST[3]); c.p(27, y - 4, RUST[2])
    c.line(33, y, 44, y - 1, IRON[2])   # the chain to its stake
    c.rect(44, y - 5, 45, y, BARK[3])
    return c.bevel().outline().im


def skullpost():
    c = base48(); y = 47
    c.rect(22, y - 28, 25, y, BARK[2]); c.rect(22, y - 28, 22, y, BARK[3])
    for yy in range(y - 28, y, 5): c.p(24, yy, BARK[1])
    c.ell(23.5, y - 31, 4, 3, BONE[2]); c.poly([(20, y - 31), (27, y - 31), (24, y - 25)], BONE[2])
    c.p(22, y - 31, OUT); c.p(25, y - 31, OUT); c.p(22, y - 30, GLOW); c.p(25, y - 30, GLOW)
    for side in (-1, 1):
        pts = [(24 + side * 3, y - 33), (24 + side * 8, y - 38), (24 + side * 10, y - 44), (24 + side * 14, y - 45)]
        c.thick(pts, BONE[1], 2)
        c.line(24 + side * 8, y - 38, 24 + side * 12, y - 39, BONE[1]); c.line(24 + side * 10, y - 43, 24 + side * 8, y - 47, BONE[1])
    for i, col in enumerate([C('c8c0a0'), C('8a2830'), C('d8d0b8')]):
        x = 20 + i * 3; c.line(x, y - 26, x + (1 if i % 2 else -1), y - 16 - i * 2, col)
    c.rect(18, y - 1, 29, y, MOSS[2])
    return c.bevel().outline().im


def antlers():
    c = base48(); y = 47
    c.ell(24, y - 1, 12, 2, MOSS[1])
    for i, (x0, d) in enumerate([(14, 1), (30, -1), (22, 1)]):
        pts = [(x0, y - 1), (x0 + d * 5, y - 5), (x0 + d * 9, y - 7), (x0 + d * 12, y - 12)]
        c.thick(pts, BONE[1 + (i % 2)], 2); c.line(x0 + d * 5, y - 5, x0 + d * 3, y - 10, BONE[2]); c.line(x0 + d * 9, y - 7, x0 + d * 10, y - 12, BONE[2])
    c.ell(26, y - 3, 3, 2, BONE[2]); c.p(25, y - 3, OUT); c.p(28, y - 3, OUT)
    return c.bevel().outline().im


def hide():
    c = base48(); y = 47
    for x0, x1 in [(6, 30), (14, 40), (22, 44)]:
        c.thick([(x0, y), (x1, y - 26)], BARK[2 + (x0 % 2)], 2)
    c.poly([(8, y - 2), (26, y - 24), (40, y - 20), (42, y - 2)], C('5a4430'))
    for i in range(6): c.line(12 + i * 5, y - 3, 22 + i * 3, y - 18, C('4a3624'))
    c.speckle([C('6a5238'), C('3a2a1c'), MOSS[2]], 40, (8, y - 24, 42, y - 2), 3)
    c.thick([(4, y - 4), (44, y - 4)], BARK[3], 2)
    for x in (18, 30): c.line(x, y - 22, x - 2, y - 14, C('c8c0a0'))
    return c.bevel().outline().im


def fungus(k):
    c = base48(); y = 47
    caps = [(18, 10, 5, 2), (26, 14, 7, 3), (33, 8, 4, 2), (22, 6, 3, 1), (12, 5, 3, 1)]
    for x, h, rx, ry in caps:
        c.rect(x - 1, y - h, x, y, C('c8dcd0')); c.ell(x - 0.5, y - h, rx, ry + 1, C('1f6a5a'))
        c.ell(x - 0.5, y - h - 1, rx - 1, ry, mix(C('2fa88a'), C('b0ffe0'), 0.3 * k))
        for dx in (-rx + 2, 0, rx - 2): c.p(x + dx - 0.5, y - h - 1, mix(C('9affd8'), C('ffffff'), 0.3 * k))
    c.rect(8, y - 1, 38, y, MOSS[1])
    c = c.bevel(0.12, 0.25).outline()
    for x, h, rx, ry in caps: c.glow(x, y - h - 2, rx + 4, (120, 255, 190), 0.18 + 0.12 * k)
    return c.im


def rootcurtain():
    c = base48()
    r = random.Random(4)
    for i in range(9):
        x = 6 + i * 4 + r.randint(-1, 1); L = r.randint(18, 40)
        pts = [(x, 0)] + [(x + math.sin(t / 4 + i) * 2, t) for t in range(4, L, 4)]
        c.thick(pts, BARK[2 + (i % 3 == 0)], 2 if i % 2 else 1.5)
        c.p(pts[-1][0], L, BARK[4])
        if i % 3 == 1: c.p(x + 1, L // 2, MOSS[3])
    return c.bevel().outline().im


def nest():
    c = base48(); y = 47
    c.ell(24, y - 3, 11, 4, BARK[2]); c.ell(24, y - 5, 8, 2, BARK[0])
    for i in range(18): c.line(13 + i, y - 1 - (i % 3), 15 + i, y - 6 + (i % 2), BARK[3 + (i % 2)])
    for x in (21, 25, 28): c.ell(x, y - 6, 1.6, 1.3, C('b8c8b0'))
    c.p(21, y - 7, C('eef4e8'))
    return c.bevel().outline().im


def mossrock():
    c = base48(); y = 47
    c.poly([(10, y), (12, y - 10), (20, y - 16), (32, y - 14), (38, y - 6), (40, y)], C('3a3a40'))
    c.speckle([C('2a2a30'), C('4a4a52')], 60, seed=5)
    c.poly([(12, y - 10), (20, y - 16), (32, y - 14), (36, y - 10), (24, y - 11)], MOSS[2])
    c.speckle([MOSS[3], MOSS[4]], 25, (12, y - 16, 36, y - 10), 6)
    return c.bevel().outline().im


def thornbed():
    c = base48(); y = 47; r = random.Random(9)
    for i in range(14):
        x0 = 4 + i * 3; h = r.randint(8, 22)
        pts = [(x0, y), (x0 + r.randint(-4, 4), y - h // 2), (x0 + r.randint(-6, 6), y - h)]
        c.thick(pts, [C('3a2418'), C('4a2e1c'), C('2a1810')][i % 3], 1.5)
        for k in range(3): c.p(pts[1][0] + (k - 1) * 2, y - h // 2 - k * 2, C('8a6a4a'))
    return c.bevel().outline().im


def standing(big):
    c = base48(); y = 47
    if big: c.poly([(16, y), (15, y - 30), (19, y - 40), (27, y - 41), (31, y - 32), (32, y)], C('4a4a50'))
    else: c.poly([(18, y), (18, y - 18), (22, y - 24), (28, y - 22), (30, y)], C('4a4a50'))
    c.speckle([C('3a3a40'), C('5a5a62'), MOSS[2]], 70, seed=8 + big)
    top = y - (38 if big else 20)
    c.poly([(17, top + 4), (22, top - 1), (28, top), (30, top + 6), (24, top + 3)], MOSS[3])
    for i in range(4 if big else 2): c.p(23, y - 12 - i * 5, C('58c890')); c.p(24, y - 14 - i * 5, C('58c890'))
    return c.bevel().outline().im


def cauldron(k):
    c = base48(); y = 47
    for x in (15, 33): c.line(x, y, x + (3 if x < 24 else -3), y - 6, IRON[2])
    c.ell(24, y - 11, 11, 8, IRON[1]); c.rect(12, y - 18, 36, y - 16, IRON[2])
    c.ell(24, y - 17, 10, 2, mix(C('2a8a3a'), C('a0ff80'), 0.25 * k))
    for i in range(3): c.ell(18 + i * 6 + k, y - 18 - (i + k) % 2, 1.5, 1, C('b8ff90'))
    for x in range(16, 34, 5): c.rect(x, y - 3, x + 2, y, C('ff8a30' if k % 2 else 'ffb050')); c.p(x + 1, y - 4, C('ffe080'))
    c = c.bevel(0.15, 0.3).outline()
    c.glow(24, y - 20, 12, (140, 255, 120), 0.25)
    return c.im


def shelves():
    c = base48(); y = 47
    c.rect(8, y - 36, 40, y, BARK[1]); c.rect(10, y - 34, 38, y - 2, C('140e0a'))
    r = random.Random(12)
    for sy in (y - 25, y - 13, y - 2):
        c.rect(9, sy, 39, sy + 1, BARK[3])
        x = 11
        while x < 36:
            w = r.randint(2, 4); h = r.randint(4, 8); col = r.choice([C('3a6a4a'), C('6a3a2a'), C('5a5a7a'), C('8a7a3a'), C('4a2a4a')])
            c.rect(x, sy - h, x + w, sy - 1, col); c.rect(x + w // 2, sy - h - 1, x + w // 2, sy - h, C('a89078')); c.p(x, sy - h + 1, lit(col, 0.4))
            x += w + r.randint(1, 3)
    return c.bevel().outline().im


def herbs():
    c = base48()
    c.line(2, 1, 46, 1, C('6a5a40'))
    r = random.Random(3)
    for i in range(6):
        x = 6 + i * 7; L = r.randint(10, 18); col = r.choice([MOSS[2], MOSS[3], C('6a7a3a'), C('7a4a5a')])
        c.line(x, 1, x, 4, C('6a5a40'))
        c.poly([(x - 3, 4 + L), (x, 4), (x + 3, 4 + L)], col); c.speckle([lit(col, 0.3), lit(col, -0.3)], 8, (x - 3, 4, x + 3, 4 + L), i)
        c.rect(x - 1, 4, x + 1, 6, C('a88a5a'))
    return c.bevel().outline().im


def mossbank():
    c = base48(); y = 47
    c.ell(24, y - 3, 22, 7, MOSS[1]); c.rect(2, y - 3, 46, y, MOSS[1])
    c.ell(24, y - 5, 19, 5, MOSS[2]); c.speckle([MOSS[3], MOSS[4]], 60, (4, y - 10, 44, y), 2)
    for x in range(6, 44, 5): c.p(x, y - 7 - (x % 3), C('f0f0e0')); c.p(x + 1, y - 6 - (x % 3), C('f8e880'))
    return c.bevel(0.1, 0.2).outline().im


def cairn():
    c = base48(); y = 47
    for i, (w, h) in enumerate([(10, 4), (8, 3), (7, 3), (5, 3), (3, 2)]):
        yy = y - 2 - sum(q[1] for q in [(10, 4), (8, 3), (7, 3), (5, 3), (3, 2)][:i]) - h / 2
        c.ell(24 + (i % 2) - 0.5, yy, w, h / 2 + 0.6, [C('4a4a50'), C('5a5a60'), C('3e3e46')][i % 3])
    c.p(24, y - 17, MOSS[3])
    return c.bevel().outline().im


def build_tv():
    items = [('snare', [snare(False), snare(True)]), ('skullpost', [skullpost()]), ('antlers', [antlers()]), ('hide', [hide()]),
             ('fungus', [fungus(k) for k in (0, 1, 2, 1)]), ('rootcurtain', [rootcurtain()]), ('nest', [nest()]), ('mossrock', [mossrock()]),
             ('thornbed', [thornbed()]), ('stone_l', [standing(True)]), ('stone_s', [standing(False)]), ('cauldron', [cauldron(k) for k in range(3)]),
             ('shelves', [shelves()]), ('herbs', [herbs()]), ('mossbank', [mossbank()]), ('stones', [cairn()])]
    sheet('xsa_tv', 48, 48, items, ms={'fungus': 300, 'cauldron': 160})


# ============================================================ big Thornveil pieces
def bark_fill(c, poly, seed, pal=BARK):
    c.poly(poly, pal[2])
    r = random.Random(seed)
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    for _ in range(int((max(xs) - min(xs)) * (max(ys) - min(ys)) / 18)):
        x, y = r.randint(int(min(xs)), int(max(xs))), r.randint(int(min(ys)), int(max(ys)))
        if c.g(x, y)[3]:
            L = r.randint(3, 9)
            for k in range(L):
                if c.g(x, y + k)[3]: c.p(x, y + k, r.choice([pal[1], pal[1], pal[3]]))


TRUNK = [C('100b08'), C('1c140e'), C('2a1f16'), C('3b2b1d'), C('503b27'), C('6b5038')]
ELD = [C('0c0806'), C('17100b'), C('231911'), C('33251a'), C('46331f'), C('5e452c')]
LEAF = [C('07120b'), C('10231a'), C('1b3a25'), C('2c5a35'), C('4f8a4a'), C('7ab060')]


def trunk(c, poly, ramp, seed, spacing=6, moss=0):
    c.poly(poly, ramp[2]); xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    box = (max(0, int(min(xs))), max(0, int(min(ys))), min(c.w - 1, int(max(xs))), min(c.h - 1, int(max(ys))))
    cyl_shade(c, ramp, box); bark_lines(c, box, ramp, seed, spacing)
    if moss:
        r = random.Random(seed + 1)
        for _ in range(moss):
            x, y = r.randint(box[0], box[2]), r.randint(box[1], box[3])
            if c.g(x, y)[3] and c.g(x - 3, y)[3] == 0 or (c.g(x, y)[3] and r.random() < 0.15):
                for k in range(r.randint(1, 4)): c.p(x + k % 2, y + k, r.choice([LEAF[3], LEAF[4], LEAF[2]]))


def rootarch():
    c = Cv(96, 128)
    # the trunk's foot (the solid trunk above is repainted by the bark skin) flaring into roots that arch over the path
    L = [(24, 0), (40, 0), (40, 46), (30, 62), (22, 90), (16, 128), (0, 128), (8, 96), (14, 60), (22, 34)]
    Rt = [(56, 0), (72, 0), (74, 34), (82, 60), (88, 96), (96, 128), (80, 128), (74, 90), (66, 62), (56, 46)]
    top = [(24, 0), (72, 0), (72, 36), (60, 50), (48, 46), (36, 50), (24, 36)]
    for poly, sd in ((L, 1), (Rt, 2), (top, 3)): trunk(c, poly, TRUNK, 20 + sd, 5, 40)
    c.outline()
    return c.im


def elder():
    W, H = 240, 440; c = Cv(W, H)
    body = [(66, 0), (174, 0), (178, 190), (190, 300), (214, 380), (240, H), (0, H), (26, 380), (50, 300), (62, 190)]
    trunk(c, body, ELD, 31, 9, 500)
    for side in (-1, 1):   # great buttress roots
        pts = [(120 + side * 40, H - 150), (120 + side * 80, H - 60), (120 + side * 118, H - 4)]
        c.thick(pts, ELD[1], 9); c.thick([(x - side, y - 3) for x, y in pts], ELD[3], 3)
    # the hollow at its heart (player's hollow: cols 53..58, rows 23..27) and the fork the high walk passes through
    c.poly([(82, H), (86, H - 74), (100, H - 92), (140, H - 92), (154, H - 74), (158, H)], C('080504'))
    c.poly([(90, H), (94, H - 70), (104, H - 84), (136, H - 84), (146, H - 70), (150, H)], C('030201'))
    c.poly([(58, 170), (62, 138), (80, 122), (120, 116), (160, 122), (178, 138), (182, 170)], C('060403'))   # the fork (rows 8..10)
    r = random.Random(33)
    for i in range(14):   # runes cut by the first wardens, still faintly lit
        x, y = r.randint(72, 168), r.randint(40, 300)
        for k in range(3): c.p(x, y + k * 2, C('78ffbe')); c.p(x + (k % 2), y + k * 2 + 1, C('3a9a70'))
    for i in range(9):    # grey ribbons over the hollow
        x, y = r.randint(90, 150), H - 98 + r.randint(-6, 6)
        c.line(x, y, x + r.randint(-3, 3), y + r.randint(8, 18), r.choice([C('a8a088'), C('7a2028'), C('6a6a8a')]))
    c.outline()
    return c.im


def motheroak():
    W, H = 256, 224; c = Cv(W, H)
    r = random.Random(41)
    # limbs first (behind the crown), then the crown in three depth layers, then the trunk and roots over them
    for pts in [[(128, 128), (84, 80), (40, 62)], [(128, 128), (176, 78), (222, 60)], [(128, 124), (134, 70), (122, 26)],
                [(122, 132), (72, 110), (28, 104)], [(134, 132), (186, 112), (230, 108)]]:
        c.thick(pts, TRUNK[1], 8); c.thick([(x - 1, y - 2) for x, y in pts], TRUNK[3], 3)
    for layer, (n, dark) in enumerate([(26, 0.5), (22, 0.25), (16, 0)]):
        ramp = [lit(q, -dark) for q in LEAF]
        for i in range(n):
            a = r.random() * 4.0 + 2.7; d = r.random() ** 0.6
            x = 128 + math.cos(a) * 118 * d; y = 78 + math.sin(a) * 66 * d + layer * 6
            rr = r.randint(14, 26) - layer * 3
            leaf_clump(c, x, y, rr, rr * 0.62, ramp, 100 * layer + i)
    body = [(106, 118), (150, 118), (156, 160), (178, 196), (212, H), (44, H), (78, 196), (100, 160)]
    trunk(c, body, TRUNK, 43, 5, 220)
    for side in (-1, 1):
        c.thick([(128 + side * 20, 186), (128 + side * 60, 212), (128 + side * 100, H - 2)], TRUNK[2], 6)
        c.thick([(128 + side * 20, 184), (128 + side * 60, 210), (128 + side * 100, H - 4)], TRUNK[4], 1.5)
    for i in range(46):   # hanging moss from the lower boughs
        x = r.randint(36, 220); y = r.randint(104, 134); Lm = r.randint(5, 18)
        for k in range(Lm): c.p(x + math.sin(k / 3) * 0.8, y + k, LEAF[3] if k % 3 else LEAF[4])
    c.outline()
    for i in range(22): c.glow(r.randint(40, 216), r.randint(20, 130), 3, (200, 255, 150), 0.55)
    return c.im


def thornveil_frames():
    out = []
    for f in range(6):
        c = Cv(32, 64); r = random.Random(50 + f % 3)
        for i in range(7):
            x = 4 + i * 4
            pts = [(x + math.sin((y + f * 3) / 7 + i) * 2, y) for y in range(0, 65, 4)]
            c.thick(pts, [C('3a2418'), C('4a2e1c'), C('2a1810')][i % 3], 2)
            for y in range(4, 64, 6): c.p(x + (2 if (y // 6 + i) % 2 else -2), y, C('8a6a4a'))
        for _ in range(12):   # embers caught in it
            x, y = r.randint(4, 28), r.randint(2, 62); k = (f + x + y) % 3
            c.p(x, y, [C('ff6a20'), C('ffa040'), C('ffd070')][k])
        c.outline((20, 10, 8, 255))
        out.append(c.im)
    return out


if __name__ == '__main__':
    build_skins(); build_icons(); build_tv()
    sheet('xsa_tvbig', 96, 128, [('rootarch', [rootarch()])])
    sheet('xsa_elder', 240, 440, [('elder', [elder()])])
    sheet('xsa_oak', 256, 224, [('motheroak', [motheroak()])])
    sheet('xsa_thornveil', 32, 64, [('loop', thornveil_frames())], ms={'loop': 110})
    print('ok')
