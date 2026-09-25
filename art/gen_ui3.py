#!/usr/bin/env python3
"""UI icons v3 (expansion gear) -> art/ui_icons3.aseprite + assets/ui_icons3.png/.json

16x16 frames, ONE tag per icon, one frame each (order = ICONS below). Same house style as
gen_ui.py / gen_ui2.py (reuses their Icon grid, dband diagonal rasteriser and palette):
one strong silhouette per icon, lit from the upper-left, auto 1px near-black outline on its
own layer. Weapons lie on the 45-degree diagonal (hilt bottom-left, tip top-right).

Contents: 17 weapons (w_<id>), 12 weapon arts (a_<id>), 9 spells (s_<id>), 13 charms (<id>).
Re-runnable: python3 art/gen_ui3.py   (preview -> art/previews/ui3.png)
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
import gen_ui2  # noqa: E402
from gen_ui2 import Icon, ramp3, taper, crescent_band, gem, necklace, sparkle, flame_tongue  # noqa: E402

S = 16
PAL = gen_ui2.PAL
PAL.update({
    # storm cyan (lightning)
    '7': (18, 56, 88), '8': (48, 150, 210), '9': (150, 236, 255),
    # ink black-violet
    'B': (24, 14, 38),
    # wind: grey-green -> pale mint
    'V': (104, 150, 136), 'Z': (196, 236, 218),
    # deep ice
    '0': (14, 30, 66),
})


def dline(ic, d0, d1, s, c):
    for d in range(d0, d1 + 1):
        ic.dpx(d, s, c)


# ================================================================ weapons
def w_frostbrand():
    ic = Icon()
    # straight sword of blue-white ice steel, frost crystals bristling at the guard
    lo, hi = taper(14, 16, 8, 13)
    ic.dband(-4, 13, lo, hi, ramp3('W', 'c', 'A'))
    ic.dband(-4, 10, 15, 15, 'W')
    for d in (0, 4, 8):
        ic.dpx(d, 15, 'c')
    ic.dpx(13, 15, 'W')
    ic.dband(-6, -5, 10, 20, lambda k, n, d: 'c' if k < 3 else ('A' if k < n - 1 else 'a'))
    for (d, s) in ((-4, 9), (-3, 8), (-4, 21), (-3, 22), (-7, 11), (-7, 19)):   # ice spurs
        ic.dpx(d, s, 'c' if s < 15 else 'A')
    ic.dband(-10, -7, 15, 16, lambda k, n, d: 'b' if (d + k) % 2 else '2')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'W' if k == 0 else ('c' if k < 2 else 'A'))
    ic.px(3, 2, 'c'); ic.px(12, 12, 'A'); ic.px(4, 5, 'W')
    return ic


def w_pagecutter():
    ic = Icon()
    # a paper-knife of bone-white steel, its edge stained with violet ink, a quill-feather grip
    lo, hi = taper(14, 16, 5, 9)
    ic.dband(-2, 9, lo, hi, lambda k, n, d: 'v' if k == 0 else ('p' if k < n else 'I'))
    ic.dband(-1, 7, 16, 16, 'I')
    ic.dpx(9, 15, 'W')
    ic.dband(-3, -3, 12, 18, lambda k, n, d: 'j' if k < 2 else ('I' if k < n else 'i'))
    ic.dband(-8, -4, 15, 16, lambda k, n, d: 'B' if (d + k) % 2 else 'i')
    ic.dband(-11, -9, 14, 17, lambda k, n, d: 'J' if k == 0 else ('j' if k < 2 else 'I'))
    ic.dpx(-12, 13, 'j'); ic.dpx(-12, 19, 'I')
    ic.px(12, 9, 'I'); ic.px(12, 10, 'i')                     # ink drip
    ic.px(4, 6, 'y')
    return ic


def w_colossus_hammer():
    ic = Icon()
    # black iron haft into a colossal slag block (set across the haft) split by molten seams
    ic.dband(-13, 2, 15, 16, lambda k, n, d: 'C' if k == 0 else 'k')
    ic.dband(-13, -12, 14, 17, lambda k, n, d: 'h' if k == 1 else 'C')
    ic.dband(-7, -6, 15, 16, 'F')

    def col(k, n, d):
        if d == 3 or k == 0:
            return '6'
        if d == 10 or k == n:
            return 'k'
        if (d == 6 and 2 <= k <= n - 2) or (k == n // 2 and 4 <= d <= 9):
            return 'Y' if (d == 6 and k == n // 2) else 'h'
        if (d == 7 and 3 <= k <= n - 3) or (k == n // 2 + 1 and 5 <= d <= 8):
            return 'F'
        return 'C' if (d + k) % 7 else 'k'
    ic.dband(3, 10, 7, 23, col)
    ic.px(15, 0, 'h'); ic.px(13, 0, 'F')
    return ic


def w_glacier_maul():
    ic = Icon()
    # a wooden haft driven into a jagged block of glacier ice, set across the haft
    ic.dband(-13, 2, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -12, 15, 16, '3')
    ic.dband(-6, -5, 15, 16, 'l')

    def col(k, n, d):
        if (k in (0, 1) and (d + k) % 3 == 0) or (k == n and d % 2):
            return None
        if k <= 1 or d == 3:
            return 'W'
        if k >= n - 1 or d == 11:
            return 'a' if d % 3 else 'b'
        if (d * 3 + k) % 7 == 0:
            return 'W'
        return 'c' if k < n // 2 else 'A'
    ic.dband(3, 11, 7, 23, col)
    ic.px(1, 3, 'c'); ic.px(14, 13, 'A')
    return ic


def w_bell_hammer():
    ic = Icon()
    # a long haft carrying a bronze bell as its head, mouth flared, clapper hanging out
    ic.dband(-13, 0, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -12, 14, 17, lambda k, n, d: 'y' if k < 2 else 'G')
    ic.rows(4, 0, [
        "....yG.....",
        "...YyyG....",
        "..YYyyGG...",
        "..YyyyGG...",
        ".YYyyyyGg..",
        ".Yyyy6yGg..",
        "YYyyyyyyGg.",
        "yyyyyyyyGGg",
        ".GGGGGGGgg.",
        "....3......",
        "....4......",
    ])
    return ic


def w_forge_cleaver():
    ic = Icon()
    # a broad slab cleaver of black forge-iron, its cutting edge still white-hot
    ic.dband(-13, -3, 15, 16, lambda k, n, d: 'L' if k == 0 else 'l')
    ic.dband(-13, -12, 14, 17, 'C')
    ic.dband(-3, -2, 12, 18, lambda k, n, d: 'z' if k < 2 else 'x')

    def hi(d):
        return min(21, 17 + (d + 1)) - (1 if d >= 11 else 0) - (1 if d >= 12 else 0)

    def col(k, n, d):
        if k == 0:
            return '6'
        if k == n:
            return 'Y' if d % 3 else 'W'
        if k == n - 1:
            return 'h'
        if k == n - 2:
            return 'F'
        return 'C' if (d + k) % 5 else 'k'
    ic.dband(-1, 12, 13, hi, col)
    ic.px(5, 7, 'k'); ic.px(6, 6, 'k')          # rivets
    return ic


def w_stormfang():
    ic = Icon()
    # a dark drake-bone spear with a forked, crackling head of storm-blue metal
    ic.dband(-13, 3, 15, 16, lambda k, n, d: '6' if k == 0 else 'C')
    for d in (-9, -5, -1):
        ic.dband(d, d, 15, 16, '8')
    ic.dband(2, 3, 14, 17, lambda k, n, d: '9' if k < 2 else '8')
    widths = {4: (15, 16), 5: (14, 17), 6: (13, 17), 7: (13, 17), 8: (14, 17), 9: (14, 16), 10: (15, 16),
              11: (15, 16), 12: (15, 15), 13: (15, 15)}
    ic.dband(4, 13, lambda d: widths[d][0], lambda d: widths[d][1], ramp3('W', '9', '8'))
    ic.dband(5, 11, 15, 15, 'W')
    for (d, s) in ((6, 11), (7, 10), (8, 10), (6, 19), (7, 20), (8, 20)):   # fork barbs
        ic.dpx(d, s, '9' if s < 15 else '8')
    ic.dpx(13, 15, 'W')
    ic.px(15, 4, '9'); ic.px(11, 0, '9'); ic.px(14, 6, '8')
    return ic


def w_stormvein():
    ic = Icon()
    # a slender dark katana with a crackling lightning vein down the blade
    def lo(d):
        t = (d + 3) / 16
        return 15 - round(1.3 * math.sin(math.pi * min(1.0, t) * 0.85)) + (1 if d >= 12 else 0)

    def hi(d):
        return lo(d) + (0 if d >= 12 else 1)
    ic.dband(-3, 13, lo, hi, lambda k, n, d: '4' if k == 0 else '2')
    for d in range(-2, 12):
        s = lo(d) + (1 if d % 3 == 1 else 0) if d < 12 else lo(d)
        ic.dpx(d, s, '9' if d % 3 else 'W')
    ic.dpx(13, lo(13), 'W')
    ic.dband(-3, -3, 14, 16, '8')
    ic.dband(-5, -4, 12, 18, lambda k, n, d: '9' if k == 0 else ('8' if k in (1, n) else '7'))
    ic.dband(-11, -6, 15, 16, lambda k, n, d: '9' if (d + k) % 3 == 0 else '1')
    ic.dband(-12, -12, 15, 16, '8')
    ic.px(14, 3, '9'); ic.px(12, 0, '8')
    return ic


def w_quarterstaff():
    ic = Icon()
    # a plain ash quarterstaff, iron-shod at both ends, leather grip in the middle
    ic.dband(-13, 13, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -11, 15, 16, lambda k, n, d: '4' if k == 0 else '3')
    ic.dband(11, 13, 15, 16, lambda k, n, d: '4' if k == 0 else '3')
    ic.dband(-2, 2, 15, 16, lambda k, n, d: 'l' if (d + k) % 2 else 'x')
    ic.dpx(13, 15, '5'); ic.dpx(-13, 15, '5')
    return ic


def w_windstaff():
    ic = Icon()
    # a pale pilgrim's staff whose head curls into a crook, wind spiralling around it
    ic.dband(-13, 6, 15, 16, lambda k, n, d: 'p' if k == 0 else 'U')
    ic.dband(-13, -12, 14, 17, 'M')
    ic.rows(8, 0, [
        "..pppU..",
        ".pU..UU.",
        "pU....U.",
        "pU...pU.",
        "Up..pU..",
        "Upp.....",
        ".Up.....",
    ])
    for (x, y, c) in ((14, 1, 'Z'), (15, 2, 'V'), (15, 4, 'Z'), (14, 6, 'V'), (13, 7, 'Z'), (11, 8, 'V'),
                      (6, 1, 'Z'), (7, 0, 'V'), (11, 3, 'Z'), (12, 4, 'Z')):
        ic.px(x, y, c)
    ic.px(1, 10, 'Z'); ic.px(0, 9, 'V'); ic.px(4, 7, 'Z')
    return ic


def w_inkquill():
    ic = Icon()
    # a staff-length quill: black nib dripping ink bottom-left, a great violet vane up-right
    ic.dband(-13, 12, 15, 15, 'v')
    ic.dband(-13, -9, 15, 16, lambda k, n, d: 'B' if k else 'i')
    ic.dpx(-14, 15, 'B')

    def vlo(d):
        return 15 - (0 if d < -6 else min(4, (d + 7) // 3 + 1)) + (max(0, d - 10))

    def vhi(d):
        return 15 + (0 if d < -4 else min(3, (d + 5) // 3 + 1)) - (max(0, d - 10))
    ic.dband(-6, 13, vlo, lambda d: 14, lambda k, n, d: 'J' if k == 0 else ('j' if (d + k) % 3 else 'I'))
    ic.dband(-4, 13, lambda d: 16, vhi, lambda k, n, d: 'i' if k == n else ('I' if (d + k) % 3 else 'j'))
    ic.dband(-8, 13, 15, 15, 'v')
    ic.px(1, 15, 'I'); ic.px(0, 13, 'i')          # ink drop
    ic.px(13, 1, 'y')
    return ic


def w_lantern_staff():
    ic = Icon()
    # a black staff with a hooked head from which a glowing lantern hangs
    ic.dband(-13, 3, 15, 16, lambda k, n, d: 'C' if k == 0 else 'k')
    ic.dband(-13, -12, 14, 17, 'G')
    ic.rows(8, 0, [
        "..CCCC..",
        ".C....C.",
        "C.....G.",
        "C....GyG",
        "....GYWYG",
        "....yWWYg",
        "....GYYyg",
        ".....gGg.",
    ])
    ic.px(9, 3, 'k'); ic.px(8, 3, 'C')
    ic.px(15, 9, 'y'); ic.px(10, 10, 'Y')
    return ic


def w_knight_shield():
    ic = Icon()
    # a knight's sword behind a heater shield: azure field, silver rim, gold cross
    lo, hi = taper(14, 16, 9, 13)
    ic.dband(0, 13, lo, hi, ramp3('5', '4', '2'))
    ic.dpx(13, 15, 'W')
    ic.poly([(1, 5), (10, 5), (10, 10), (6, 15), (5, 15), (1, 10)], '4')
    ic.poly([(2, 6), (9, 6), (9, 10), (6, 13), (5, 13), (2, 10)],
            lambda x, y: 'A' if (x < 4 and y < 9) else ('a' if x < 7 else 'b'))
    ic.line(1, 5, 10, 5, '5'); ic.line(1, 5, 1, 10, '5')
    ic.line(5, 6, 5, 12, 'y'); ic.line(2, 8, 9, 8, 'y'); ic.px(5, 8, 'Y')
    return ic


def w_twinborne():
    ic = Icon()
    # a round shield split down the middle: ember flame on the left, frost on the right
    def f(nx, ny):
        r = nx * nx + ny * ny
        if r > 0.8:
            return 'y' if (nx + ny) < -0.2 else 'G'
        if nx < -0.08:
            return 'Y' if (nx + ny) < -0.9 else ('h' if ny < 0.3 else 'F')
        if nx > 0.08:
            return 'W' if (nx + ny) < -0.3 else ('c' if ny < 0.3 else 'A')
        return 'k'
    ic.ell(8, 8, 7.2, 7.2, f)
    ic.ell(8, 8, 1.8, 1.8, lambda nx, ny: 'Y' if nx + ny < 0 else 'G')
    ic.px(4, 5, 'W'); ic.px(12, 5, 'W')
    return ic


def w_overseer_bulwark():
    ic = Icon()
    # a towering slab of forge iron, molten rivets and a glowing viewing slit
    ic.poly([(3, 0), (12, 0), (13, 2), (13, 13), (8, 15), (7, 15), (2, 13), (2, 2)],
            lambda x, y: '6' if (x < 5 and y < 7) else ('C' if x < 9 else 'k'))
    ic.line(3, 0, 12, 0, '6'); ic.line(2, 2, 2, 13, '6')
    ic.line(4, 4, 11, 4, 'h'); ic.line(5, 5, 10, 5, 'F'); ic.px(7, 4, 'Y'); ic.px(8, 4, 'Y')
    for (x, y) in ((4, 2), (11, 2), (4, 11), (11, 11), (7, 13)):
        ic.px(x, y, 'h')
    ic.line(7, 7, 7, 11, 'k'); ic.line(8, 7, 8, 11, '6')
    return ic


def w_twinfangs():
    ic = Icon()
    # two curved fang-blades crossed in an X, grips wrapped in dark red
    for flip in (False, True):
        pts = []
        for i in range(12):
            t = i / 11
            x = 2 + 11.5 * t
            y = 13 - 11.5 * t + 2.2 * math.sin(math.pi * t)
            pts.append((15 - x if flip else x, y))
        for i, (x, y) in enumerate(pts):
            if i < 3:
                ic.px(x, y, 'r' if i % 2 else 'm')
            elif i == 3:
                ic.px(x, y, 'y'); ic.px(x + (1 if flip else -1), y - 1, 'G'); ic.px(x + (-1 if flip else 1), y + 1, 'G')
            else:
                ic.px(x, y, '5' if flip else '4')
                ic.px(x, y + 1, '3' if flip else '2')
        ic.px(*pts[-1], 'W')
    return ic


def w_first_ember():
    ic = Icon()
    # a mirror-blade: one edge white-gold, the other obsidian black; an ember heart at the guard
    lo, hi = taper(13, 17, 8, 13)

    def col(k, n, d):
        if k <= n // 2:
            return 'W' if k == 0 else 'E'
        return 'k' if k == n else 'B'
    ic.dband(-3, 13, lo, hi, col)
    ic.dpx(13, 15, 'W')
    ic.dband(-5, -4, 11, 19, lambda k, n, d: 'Y' if k < 3 else ('k' if k > n - 3 else 'h'))
    ic.dpx(-4, 15, 'W')
    ic.dband(-10, -6, 15, 16, lambda k, n, d: 'k' if (d + k) % 2 else 'C')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'h' if 1 <= k <= 2 else 'F')
    ic.px(14, 0, 'h'); ic.px(15, 1, 'Y'); ic.px(13, 0, 'F')
    return ic


# ================================================================ weapon arts
def a_whirlwind():
    ic = Icon()
    # a staff held level inside a spinning ring of wind
    for i in range(70):
        a = 2 * math.pi * i / 70
        r = 6.6 - 1.6 * (i / 70)
        x, y = 8 + math.cos(a) * r, 8 + math.sin(a) * r * 0.62
        ic.px(x, y, 'Z' if i < 30 else ('V' if i < 55 else 'S'))
    for i in range(40):
        a = 2 * math.pi * i / 40 + 1.4
        r = 3.8
        ic.px(8 + math.cos(a) * r, 8 + math.sin(a) * r * 0.62, 'W' if i < 14 else 'Z')
    ic.line(1, 11, 14, 5, 'w'); ic.line(2, 11, 14, 6, 'L')
    ic.px(1, 11, '4'); ic.px(14, 5, '4')
    ic.px(2, 3, 'Z'); ic.px(13, 13, 'V')
    return ic


def a_gale_vault():
    ic = Icon()
    # an arcing leap over a jagged foe-spike, a gust chevron at the top of the arc
    for i in range(40):
        t = i / 39
        x = 1 + 13 * t
        y = 13 - 10 * math.sin(math.pi * t)
        ic.px(x, y, 'Z' if t < 0.7 else 'V')
        if 0.2 < t < 0.8:
            ic.px(x, y + 1, 'V')
    ic.rows(5, 10, ["..S..", ".SsS.", "SsssS", "sssss"])
    ic.rows(6, 1, ["W...W", ".WZW.", "..W.."])
    ic.px(14, 13, 'W'); ic.px(15, 14, 'Z')
    return ic


def a_ink_mark():
    ic = Icon()
    # a quill drawing a glowing glyph onto the floor
    ic.ell(8, 12, 7, 3, lambda nx, ny: None if nx * nx + ny * ny < 0.55 else ('j' if ny < 0 else 'I'))
    ic.rows(5, 11, ["Y.y.Y", ".YWY.", "y.Y.y"][:2])
    ic.px(7, 13, 'y')
    ic.line(13, 0, 8, 10, 'v')
    ic.line(14, 1, 10, 7, 'j'); ic.line(15, 1, 11, 7, 'I'); ic.line(12, 0, 9, 6, 'J')
    ic.px(8, 10, 'B'); ic.px(8, 11, 'I')
    return ic


def shield_shape(ic, fill, rim_lit, rim):
    ic.poly([(3, 2), (12, 2), (12, 8), (8, 14), (7, 14), (3, 8)], rim)
    ic.poly([(4, 3), (11, 3), (11, 8), (8, 12), (7, 12), (4, 8)], fill)
    ic.line(3, 2, 12, 2, rim_lit); ic.line(3, 2, 3, 8, rim_lit)


def a_aegis():
    ic = Icon()
    # a shield blazing with a perfect-guard aura: golden rays burst from its rim
    for a in range(0, 360, 30):
        r0, r1 = 6.4, 7.8 if a % 60 == 0 else 7.0
        ic.line(8 + math.cos(math.radians(a)) * r0, 8 - math.sin(math.radians(a)) * r0,
                8 + math.cos(math.radians(a)) * r1, 8 - math.sin(math.radians(a)) * r1, 'Y')
    shield_shape(ic, lambda x, y: 'W' if (x < 6 and y < 6) else ('Y' if x + y < 16 else 'y'), 'W', 'G')
    ic.line(7, 4, 7, 10, 'G'); ic.line(5, 6, 10, 6, 'G')
    return ic


def a_frost_aegis():
    ic = Icon()
    # an ice-rimmed shield bearing a white snowflake, crystals bristling off it
    shield_shape(ic, lambda x, y: 'A' if (x < 6 and y < 6) else ('a' if x + y < 16 else 'b'), 'W', 'c')
    ic.line(7, 4, 7, 11, 'W'); ic.line(5, 6, 10, 9, 'c'); ic.line(10, 6, 5, 9, 'c')
    ic.px(7, 7, 'W')
    for (x, y) in ((1, 1), (14, 1), (1, 9), (14, 9), (7, 0), (8, 0)):
        ic.px(x, y, 'c')
    ic.px(0, 0, 'W'); ic.px(15, 0, 'W')
    return ic


def a_shield_charge():
    ic = Icon()
    # a tower shield rushing right, speed streaks behind, sparks on its face
    for (y, x0, x1) in ((3, 0, 4), (7, 0, 5), (11, 1, 4), (13, 0, 3)):
        ic.line(x0, y, x1, y, 'S'); ic.px(x1, y, '4')
    ic.poly([(7, 1), (12, 1), (13, 3), (13, 12), (10, 15), (9, 15), (6, 12), (6, 3)],
            lambda x, y: '6' if x < 9 else ('C' if x < 12 else 'k'))
    ic.line(7, 1, 12, 1, '6')
    ic.px(9, 5, 'h'); ic.px(9, 9, 'h'); ic.px(12, 7, 'F')
    ic.px(15, 4, 'Y'); ic.px(14, 6, 'W'); ic.px(15, 9, 'Y'); ic.px(14, 11, 'y')
    return ic


def a_magma_quake():
    ic = Icon()
    # the ground split open by a slam, lava erupting from three fissures
    ic.rect(0, 12, 15, 15, 's')
    ic.line(0, 12, 15, 12, 'S')
    for (x, h) in ((3, 5), (8, 9), (13, 6)):
        flame_tongue(ic, x + 0.5, 12, h, 1.5, x * 0.7, ('Y', 'h', 'F', 'f'))
        ic.line(x, 12, x - 1, 15, 'h'); ic.px(x, 13, 'Y')
    ic.line(4, 14, 7, 13, 'F'); ic.line(9, 14, 12, 13, 'F')
    ic.px(6, 1, 'h'); ic.px(11, 3, 'F'); ic.px(1, 5, 'F')
    return ic


def a_thunder_lunge():
    ic = Icon()
    # a spear-point streaking right on a jagged trail of lightning
    zig = [(0, 9), (3, 6), (5, 9), (8, 6), (10, 8)]
    for (a, b) in zip(zig, zig[1:]):
        ic.line(*a, *b, '8')
    for (a, b) in zip(zig, zig[1:]):
        ic.line(a[0], a[1] - 1, b[0], b[1] - 1, '9')
    ic.poly([(10, 5), (15, 7.5), (10, 10)], lambda x, y: 'W' if y < 7.5 else '9')
    ic.line(10, 7, 15, 7, 'W')
    ic.px(2, 2, '9'); ic.px(6, 13, '8'); ic.px(12, 12, '9'); ic.px(13, 2, '8')
    return ic


def a_tolling_blow():
    ic = Icon()
    # a bronze bell ringing: concentric sound arcs on both sides
    ic.poly([(6, 3), (9, 3), (10, 6), (11, 10), (12, 11), (12, 12), (3, 12), (3, 11), (4, 10), (5, 6)],
            lambda x, y: 'Y' if (x < 7 and y < 8) else ('y' if x < 8 else ('G' if x < 10 else 'g')))
    ic.rect(7, 1, 8, 2, 'G'); ic.line(3, 12, 12, 12, 'y')
    ic.rect(7, 13, 8, 14, '3')
    for r, c in ((1.5, 'Y'), (3.2, 'y')):
        for i in range(12):
            a = math.radians(-50 + 100 * i / 11)
            ic.px(12.5 + r + math.cos(a) * 1.2, 8 - math.sin(a) * (2.2 + r), c)
            ic.px(2.5 - r - math.cos(a) * 1.2, 8 - math.sin(a) * (2.2 + r), c)
    return ic


def a_twin_tempest():
    ic = Icon()
    # a storm of crossing blade-cuts, eight thin slashes whirling around a bright centre
    cuts = [((1, 3), (13, 12), 'W'), ((2, 13), (14, 2), '5'), ((0, 8), (15, 7), '4'), ((6, 0), (9, 15), '5'),
            ((3, 1), (11, 14), '4'), ((12, 1), (4, 15), '4')]
    for (a, b, c) in cuts:
        ic.line(*a, *b, c)
    ic.ell(8, 8, 2.2, 2.2, lambda nx, ny: 'W' if nx + ny < 0 else 'P')
    ic.px(1, 3, 'P'); ic.px(14, 2, 'R'); ic.px(15, 7, 'P')
    return ic


def a_echo():
    ic = Icon()
    # a white-gold crescent and, trailing it, its ghostly ember echo
    crescent_band(ic, 6, 9, 6.0, 110, -60, 2.6, ('U', 'T', 'C'))
    crescent_band(ic, 9.5, 8, 6.2, 110, -60, 3.2, ('W', 'E', 'Y'))
    sparkle(ic, 13, 3, c='W', c2='h')
    ic.px(2, 14, 'h'); ic.px(1, 12, 'F')
    return ic


def a_backstep_slash():
    ic = Icon()
    # a hooked arrow hopping back to the left, then a bright forward cut on the right
    ic.rows(0, 2, [
        "...ZZZZ...",
        "..Z....V..",
        ".ZZZ....V.",
        "ZZZZZ...V.",
        "..........",
    ][:4])
    ic.px(1, 4, 'Z'); ic.px(3, 4, 'Z')
    ic.line(1, 5, 5, 5, 'V')
    crescent_band(ic, 8, 9, 6.6, 70, -70, 3.0, ('W', '5', '4'))
    ic.px(14, 2, 'W'); ic.px(2, 12, 'S'); ic.px(4, 13, 'S')
    return ic


def s_ink_seal():
    ic = Icon()
    # a violet seal circle with a gold star-glyph at its heart, ink bleeding from its rim
    ic.ell(8, 8, 7.4, 7.4, lambda nx, ny: None if nx * nx + ny * ny < 0.62 else ('j' if (nx + ny) < -0.3 else ('I' if nx + ny < 0.7 else 'i')))
    ic.ell(8, 8, 5.2, 5.2, lambda nx, ny: 'B' if nx * nx + ny * ny < 1 else None)
    for k in range(5):
        a1, a2 = math.radians(90 + 144 * k), math.radians(90 + 144 * (k + 1))
        ic.line(8 + math.cos(a1) * 4.2, 8 - math.sin(a1) * 4.2, 8 + math.cos(a2) * 4.2, 8 - math.sin(a2) * 4.2, 'y')
    ic.px(8, 8, 'W'); ic.px(7, 8, 'Y')
    ic.px(13, 14, 'I'); ic.px(13, 15, 'i'); ic.px(2, 14, 'i')
    return ic


def s_glyph_swarm():
    ic = Icon()
    # five small rune-diamonds streaming right in a V, trails of violet behind them
    def rune(x, y, big=False):
        ic.rows(x - 1, y - 1, [".J.", "JYj", ".j."] if not big else [".J.", "JWj", ".j."])
        ic.line(x - 4, y, x - 2, y, 'I')
    for (x, y) in ((13, 8), (9, 4), (9, 12), (5, 1), (5, 15)):
        rune(x, y, x == 13)
    ic.px(15, 8, 'Y')
    return ic


def s_glacial_wall():
    ic = Icon()
    # a slab of jagged glacier ice rising out of the ground
    ic.poly([(2, 15), (2, 5), (4, 2), (6, 4), (8, 0), (10, 3), (12, 1), (14, 5), (14, 15)],
            lambda x, y: 'W' if (x < 5 and y < 8) else ('c' if x < 8 else ('A' if x < 12 else 'a')))
    ic.line(4, 3, 4, 13, 'W'); ic.line(8, 1, 8, 13, 'c'); ic.line(11, 3, 11, 14, 'a')
    ic.line(5, 8, 7, 10, 'A'); ic.line(9, 6, 10, 8, 'W')
    ic.line(0, 15, 15, 15, 'b')
    ic.px(1, 12, 'c'); ic.px(15, 11, 'A')
    return ic


def s_frost_nova():
    ic = Icon()
    # a white-hot frost burst: six crystal arms with barbs and a ring of ice motes
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ex, ey = 8 + math.cos(a) * 7, 8 - math.sin(a) * 7
        ic.line(8, 8, ex, ey, 'c' if k in (0, 1, 5) else 'A')
        for sgn in (-1, 1):
            b = a + sgn * 0.7
            mx, my = 8 + math.cos(a) * 4.5, 8 - math.sin(a) * 4.5
            ic.line(mx, my, mx + math.cos(b) * 2, my - math.sin(b) * 2, 'A' if k > 2 else 'c')
        ic.px(ex, ey, 'W')
    ic.ell(8, 8, 1.8, 1.8, lambda nx, ny: 'W')
    return ic


def s_magma_orb():
    ic = Icon()
    # a molten orb lobbed along an arc: black crust plates over a white-hot heart, dripping fire
    for i in range(14):
        t = i / 13
        ic.px(0 + 6 * t, 14 - 7 * math.sin(math.pi * t * 0.6), 'F' if t < 0.6 else 'h')

    def f(nx, ny):
        v = nx + ny
        crust = (nx * 3 + ny * 5) % 1.6 < 0.35 and v > -0.2
        if crust:
            return 'k' if v > 0.6 else 'C'
        return 'W' if v < -1.0 else ('Y' if v < -0.4 else ('h' if v < 0.3 else ('F' if v < 0.9 else 'f')))
    ic.ell(10, 7, 5, 5, f)
    ic.px(9, 13, 'h'); ic.px(9, 14, 'F'); ic.px(13, 13, 'F'); ic.px(15, 2, 'h')
    return ic


def s_chain_lightning():
    ic = Icon()
    # lightning leaping between three sparks
    nodes = [(1, 12), (7, 4), (14, 11)]
    segs = [[(1, 12), (3, 8), (5, 9), (7, 4)], [(7, 4), (9, 8), (11, 7), (14, 11)]]
    for seg in segs:
        for (a, b) in zip(seg, seg[1:]):
            ic.line(*a, *b, '9')
            ic.line(a[0] + 1, a[1], b[0] + 1, b[1], '8')
    for (x, y) in nodes:
        sparkle(ic, x, y, c='W', c2='9')
    ic.px(14, 1, '8'); ic.px(3, 1, '9')
    return ic


def s_stormcall():
    ic = Icon()
    # a black storm-cloud splitting to drop a white bolt
    for (cx, cy, r) in ((4.5, 4.5, 3.2), (9, 3.5, 3.8), (12.5, 5, 3.0), (7, 6, 3)):
        ic.ell(cx, cy, r, r * 0.8, lambda nx, ny: 'S' if (nx + ny) < -0.7 else ('s' if ny < 0.5 else '1'))
    ic.line(9, 7, 7, 10, 'W'); ic.line(7, 10, 10, 10, 'W'); ic.line(10, 10, 7, 15, 'W')
    ic.line(8, 7, 6, 10, '9'); ic.line(11, 10, 8, 15, '9')
    ic.px(3, 11, '8'); ic.px(13, 12, '9')
    return ic


def s_wind_ward():
    ic = Icon()
    # a spiralling wind barrier, an arrow glancing off it
    for i in range(80):
        t = i / 79
        a = t * 2 * math.pi * 1.25
        r = 7 - 3.4 * t
        ic.px(8 + math.cos(a) * r, 8 + math.sin(a) * r, 'Z' if t < 0.35 else ('V' if t < 0.75 else 'W'))
    ic.line(0, 1, 3, 4, '3'); ic.px(3, 4, '5'); ic.px(4, 5, 'W')
    ic.line(4, 5, 1, 10, '3'); ic.px(0, 11, 'S')
    return ic


def s_ember_echo():
    ic = Icon()
    # a living flame and its hollow echo standing behind it
    flame_tongue(ic, 5, 14, 11, 2.6, 0.4, ('M', 'T', 'C', 'k'))
    flame_tongue(ic, 10, 15, 13, 3.4, 1.4, ('W', 'Y', 'h', 'F'))
    ic.px(10, 12, 'E'); ic.px(9, 13, 'W')
    return ic


# ================================================================ charms
def c_bead():
    ic = Icon()
    # a loop of worn wooden prayer beads with one gold bead and a tassel
    pts = []
    for i in range(11):
        a = 2 * math.pi * i / 11 + 0.3
        pts.append((8 + math.cos(a) * 5.4, 6.8 + math.sin(a) * 5.0))
    for i, (x, y) in enumerate(pts):
        c1 = ('Y', 'y', 'G') if i == 3 else ('w', 'L', 'l')
        ic.ell(x, y, 1.5, 1.5, lambda nx, ny, c1=c1: c1[0] if nx + ny < -0.5 else (c1[1] if nx + ny < 0.6 else c1[2]))
    ic.line(8, 12, 8, 13, 'G')
    ic.rows(6, 13, [".yYy.", "y.y.y", "G.G.G"][:3])
    return ic


def c_lantern():
    ic = Icon()
    # a small iron pocket-lantern, its glass brimming with warm light
    ic.ell(8, 1.5, 1.8, 1.5, lambda nx, ny: None if nx * nx + ny * ny < 0.25 else '3')
    ic.rows(3, 3, [
        ".4444443.",
        "443333322",
        ".3YWWYy2.",
        ".3YWWYy2.",
        ".3yYYyG2.",
        ".3yyyGG2.",
        "443333322",
        "..32222..",
    ])
    ic.px(1, 7, 'y'); ic.px(14, 7, 'G'); ic.px(8, 13, 'y')
    return ic


def c_quill():
    ic = Icon()
    # a white quill standing in a squat black inkwell rimmed with gold
    ic.line(4, 0, 9, 10, 'v')
    ic.poly([(4, 0), (7, 1), (9, 6), (8, 8)], lambda x, y: 'v' if x < 7 else 'u')
    ic.poly([(3, 1), (4, 6), (7, 8)], lambda x, y: 'p')
    ic.line(4, 0, 8, 8, 'W')
    ic.rows(4, 9, [
        "..yyyy..",
        ".GiIIiG.",
        "BiIjIiiB",
        "BiIIiiiB",
        "BBiiiiBB",
        ".BBBBBB.",
    ])
    return ic


def c_frostheart():
    ic = Icon()
    # a heart of clear ice with a white core, hung from a frosted silver bail
    ic.ell(8, 1.5, 1.6, 1.4, lambda nx, ny: None if nx * nx + ny * ny < 0.25 else '5')
    ic.rows(2, 3, [
        ".WWc..ccA.",
        "WWccccccAa",
        "WccccAAAAa",
        "cccWcAAAab",
        ".ccAAAAab.",
        "..cAAAab..",
        "...Aaab...",
        "....ab....",
    ])
    ic.px(5, 6, 'W'); ic.px(6, 5, 'W')
    ic.px(1, 1, 'c'); ic.px(14, 2, 'c'); ic.px(13, 13, 'A')
    return ic


def c_aegis():
    ic = Icon()
    # a small silver kite-shield pendant set with a pale ice gem, hung on a chain
    necklace(ic, 8, 0, 4, 4.5, '4', '3')
    ic.poly([(4, 4), (11, 4), (11, 9), (8, 14), (7, 14), (4, 9)],
            lambda x, y: '5' if (x < 6 and y < 8) else ('4' if x < 9 else '3'))
    ic.line(4, 4, 11, 4, 'W')
    gem(ic, 7.5, 7.8, 2, 2.2, ('W', 'c', 'A', 'a'))
    return ic


def c_twin():
    ic = Icon()
    # two interlocking rings: one of ember flame, one of frost
    ic.ell(5.5, 8, 4.6, 4.6, lambda nx, ny: None if nx * nx + ny * ny < 0.45 else ('Y' if nx + ny < -0.4 else ('h' if nx + ny < 0.5 else 'F')))
    ic.ell(10.5, 8, 4.6, 4.6, lambda nx, ny: None if nx * nx + ny * ny < 0.45 else ('W' if nx + ny < -0.4 else ('c' if nx + ny < 0.5 else 'A')))
    ic.px(8, 5, 'h'); ic.px(8, 4, 'Y')       # flame ring passes over the frost ring at the top
    ic.px(1, 3, 'F'); ic.px(14, 13, 'c')
    return ic


def c_slag():
    ic = Icon()
    # a drop of cooling slag on a cord: black crust cracked over a molten core
    ic.line(3, 0, 8, 4, 'l'); ic.line(13, 0, 8, 4, 'l')
    ic.poly([(8, 3), (13, 9), (13, 11), (11, 14), (5, 14), (3, 11), (3, 9)],
            lambda x, y: '6' if (x < 7 and y < 9) else ('C' if x + y < 19 else 'k'))
    for (a, b) in (((6, 7), (8, 10)), ((8, 10), (11, 9)), ((8, 10), (7, 13)), ((10, 7), (11, 9))):
        ic.line(*a, *b, 'h')
    ic.px(8, 10, 'Y'); ic.px(9, 11, 'F')
    ic.px(8, 15, 'h')
    return ic


def c_brand():
    ic = Icon()
    # a branding iron, its sigil head glowing white-hot
    ic.dband(-13, -2, 15, 16, lambda k, n, d: '4' if k == 0 else '2')
    ic.dband(-13, -10, 15, 16, lambda k, n, d: 'L' if k == 0 else 'l')
    ic.rows(8, 1, [
        ".hYYh..",
        "hY..Yh.",
        "Y.WW.Y.",
        "Y.WW.Yh",
        "hY..YhF",
        ".hYYhF.",
        "..FF...",
    ])
    ic.px(7, 8, '3')
    return ic


def c_core():
    ic = Icon()
    # a molten core caged in blackened iron bands
    ic.ell(8, 8.5, 5.4, 5.4, lambda nx, ny: 'W' if (nx + ny) < -1.0 else ('Y' if (nx + ny) < -0.3 else ('h' if (nx + ny) < 0.5 else 'F')))
    ic.ell(8, 8.5, 6.4, 6.4, lambda nx, ny: 'C' if (nx * nx + ny * ny > 0.78 or abs(nx) < 0.12 or abs(ny) < 0.12) else None)
    ic.rect(7, 0, 8, 2, 'C'); ic.px(7, 0, '6')
    return ic


def c_feather():
    ic = Icon()
    # a long storm-drake feather, dark cyan vane edged with crackling white
    ic.line(3, 14, 13, 1, 'W')
    for i in range(10):
        t = i / 9
        x, y = 3 + 10 * t, 14 - 13 * t
        w = 3.2 * math.sin(math.pi * min(1, t * 1.15))
        ic.line(x, y, x - w, y - w * 0.9, '8' if i % 3 else '9')
        ic.line(x, y, x + w * 0.9, y + w, '7' if i % 2 else '8')
    ic.line(3, 14, 13, 1, 'W')
    ic.px(2, 15, 'v'); ic.px(14, 0, '9'); ic.px(9, 2, '9')
    return ic


def c_scale():
    ic = Icon()
    # a great black drake scale, gold-rimmed, a vein of storm-light down its keel
    ic.poly([(8, 0), (13, 4), (14, 9), (11, 14), (8, 15), (5, 14), (2, 9), (3, 4)],
            lambda x, y: 'y' if (x + y) < 7 else ('G' if (x + y) > 23 else ('6' if x < 8 and y < 7 else ('C' if x < 9 else 'k'))))
    ic.poly([(8, 2), (12, 5), (12, 9), (10, 13), (8, 13), (6, 13), (4, 9), (4, 5)],
            lambda x, y: '6' if (x < 7 and y < 7) else ('C' if x < 9 else 'k'))
    ic.line(8, 2, 8, 13, '8'); ic.px(8, 5, '9'); ic.px(8, 9, '9')
    return ic


def c_clapper():
    ic = Icon()
    # a bell's clapper: bronze rod and heavy teardrop weight, ringing arcs beside it
    ic.rect(7, 0, 8, 1, 'G'); ic.px(7, 0, 'Y')
    ic.line(7, 2, 7, 8, 'y'); ic.line(8, 2, 8, 8, 'G')
    ic.ell(7.5, 11.5, 3.2, 3.6, lambda nx, ny: 'Y' if (nx + ny) < -0.6 else ('y' if (nx + ny) < 0.4 else ('G' if (nx + ny) < 1.0 else 'g')))
    for i in range(8):
        a = math.radians(-45 + 90 * i / 7)
        ic.px(12 + math.cos(a) * 2, 8 - math.sin(a) * 4, 'y')
        ic.px(3 - math.cos(a) * 2, 8 - math.sin(a) * 4, 'y')
    return ic


def c_echo():
    ic = Icon()
    # a tiny ember whose light rings outward in two hollow echoes
    for (r, c) in ((7.0, 'T'), (4.8, 'U')):
        for i in range(60):
            a = 2 * math.pi * i / 60
            if (i // 5) % 3 == 2:
                continue
            ic.px(8 + math.cos(a) * r, 8 + math.sin(a) * r, c)
    ic.ell(8, 8, 2.8, 2.8, lambda nx, ny: 'W' if (nx + ny) < -0.6 else ('Y' if (nx + ny) < 0.3 else 'h'))
    ic.px(8, 4, 'h'); ic.px(8, 3, 'Y')
    return ic


ICONS = [
    # weapons (17)
    ("w_frostbrand", w_frostbrand), ("w_pagecutter", w_pagecutter), ("w_colossus_hammer", w_colossus_hammer),
    ("w_glacier_maul", w_glacier_maul), ("w_bell_hammer", w_bell_hammer), ("w_forge_cleaver", w_forge_cleaver),
    ("w_stormfang", w_stormfang), ("w_stormvein", w_stormvein), ("w_quarterstaff", w_quarterstaff),
    ("w_windstaff", w_windstaff), ("w_inkquill", w_inkquill), ("w_lantern_staff", w_lantern_staff),
    ("w_knight_shield", w_knight_shield), ("w_twinborne", w_twinborne), ("w_overseer_bulwark", w_overseer_bulwark),
    ("w_twinfangs", w_twinfangs), ("w_first_ember", w_first_ember),
    # arts (12)
    ("a_whirlwind", a_whirlwind), ("a_gale_vault", a_gale_vault), ("a_ink_mark", a_ink_mark), ("a_aegis", a_aegis),
    ("a_frost_aegis", a_frost_aegis), ("a_shield_charge", a_shield_charge), ("a_magma_quake", a_magma_quake),
    ("a_thunder_lunge", a_thunder_lunge), ("a_tolling_blow", a_tolling_blow), ("a_twin_tempest", a_twin_tempest),
    ("a_echo", a_echo), ("a_backstep_slash", a_backstep_slash),
    # spells (9)
    ("s_ink_seal", s_ink_seal), ("s_glyph_swarm", s_glyph_swarm), ("s_glacial_wall", s_glacial_wall),
    ("s_frost_nova", s_frost_nova), ("s_magma_orb", s_magma_orb), ("s_chain_lightning", s_chain_lightning),
    ("s_stormcall", s_stormcall), ("s_wind_ward", s_wind_ward), ("s_ember_echo", s_ember_echo),
    # charms (13)
    ("c_bead", c_bead), ("c_lantern", c_lantern), ("c_quill", c_quill), ("c_frostheart", c_frostheart),
    ("c_aegis", c_aegis), ("c_twin", c_twin), ("c_slag", c_slag), ("c_brand", c_brand), ("c_core", c_core),
    ("c_feather", c_feather), ("c_scale", c_scale), ("c_clapper", c_clapper), ("c_echo", c_echo),
]


def main():
    frames, tags, comps = [], [], []
    for i, (name, fn) in enumerate(ICONS):
        body, out = fn().images()
        frames.append({"ms": 100, "cels": {"Outline": out, "Icon": body}})
        tags.append((name, i, i))
        c = out.copy()
        c.alpha_composite(body)
        comps.append((name, c))
    if "--preview-only" not in sys.argv:
        asebuild.build("ui_icons3", S, S, ["Outline", "Icon"], frames, tags)

    fr = Image.open(os.path.join(os.path.dirname(HERE), "assets", "ui_frame.png")).convert("RGBA")
    Z, cols = 4, 10
    rows = (len(comps) + cols - 1) // cols
    cw, ch = 28 * Z, 32 * Z
    top_h = 3 * 18 * 3 + 12
    sheet = Image.new("RGBA", (cols * cw, top_h + rows * ch), (92, 92, 100, 255))
    d = ImageDraw.Draw(sheet)
    strip = Image.new("RGBA", (20 * 18 + 2, 3 * 18 + 2), (20, 18, 26, 255))
    for i, (_, c) in enumerate(comps):
        strip.alpha_composite(c, (2 + (i % 20) * 18, 2 + (i // 20) * 18))
    sheet.paste(strip.resize((strip.width * 3, strip.height * 3), Image.NEAREST), (0, 0))
    for i, (name, c) in enumerate(comps):
        cell = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        cell.paste(Image.new("RGBA", (16, 16), (28, 24, 34, 255)), (4, 4))
        cell.alpha_composite(fr)
        cell.alpha_composite(c, (4, 4))
        x, y = (i % cols) * cw + 2 * Z, top_h + (i // cols) * ch + 2 * Z
        sheet.alpha_composite(cell.resize((24 * Z, 24 * Z), Image.NEAREST), (x, y))
        d.text((x, y + 24 * Z + 2), name, fill=(255, 255, 255, 255))
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "ui3.png"))
    print("ui_icons3:", len(frames), "icons")


if __name__ == "__main__":
    main()
