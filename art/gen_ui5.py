#!/usr/bin/env python3
"""UI icons v5 (Expansion 2 gear, agent G) -> art/ui_icons5.aseprite + assets/ui_icons5.png/.json

16x16 frames, ONE tag per icon (order = ICONS below). Same house style as gen_ui.py / gen_ui2.py /
gen_ui3.py (reuses their Icon grid, dband diagonal rasteriser and palette): one strong silhouette,
lit from the upper-left, auto 1px near-black outline on its own layer. Weapons on the 45-degree
diagonal (hilt bottom-left, tip top-right); scythes carry their blade across the top, whips coil.

Contents: 21 weapons (w_<id>), 10 arts (a_<id>), 10 spells (s_<id>), 15 charms (<id>),
2 traversal items (i_tidebreath, i_moonstep).
Re-runnable: python3 art/gen_ui5.py [--preview-only]   (preview -> art/previews/ui5.png)
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
import gen_ui2  # noqa: E402
import gen_ui3  # noqa: E402  (registers the storm/ink/wind palette keys)
from gen_ui2 import Icon, ramp3, taper, crescent_band, gem, necklace, sparkle, flame_tongue  # noqa: E402

S = 16
PAL = gen_ui2.PAL
PAL.update({
    # blood
    '%': (92, 8, 22), '&': (178, 18, 38), '*': (236, 70, 80),
    # moss / thorn green
    '(': (28, 52, 30), ')': (62, 110, 52), '+': (150, 200, 96),
    # teal sea glow
    ',': (12, 58, 64), '-': (30, 132, 130), '~': (120, 230, 214),
    # neon magenta
    '/': (110, 20, 110), ':': (230, 60, 210), ';': (255, 170, 250),
    # sand / sun
    '<': (120, 88, 44), '=': (200, 160, 88), '>': (246, 222, 150),
    # ghost blue (Vael)
    '?': (40, 60, 120), '@': (120, 170, 255), '[': (210, 236, 255),
    # star violet-white
    ']': (60, 40, 110), '^': (150, 120, 230), '_': (236, 228, 255),
    # pale flame (Venn)
    '{': (150, 140, 120), '|': (230, 222, 196), '}': (255, 252, 236),
})


def scythe(ic, shaft, blade, d_top=11, reach=12.0, thick=2.8, bow=0.0):
    """Shaft on the diagonal up to d_top; a long blade sweeps from the shaft head to the left,
    curving down to a point. shaft = (lit, dark, butt); blade = (edge, body, back)."""
    ic.dband(-13, d_top, 15, 16, lambda k, n, d: shaft[0] if k == 0 else shaft[1])
    ic.dband(-13, -12, 14, 17, shaft[2])
    hx, hy = (d_top + 15) / 2, (15 - d_top) / 2          # shaft head in pixels
    n = 80
    for i in range(n + 1):
        t = i / n
        x = hx + 0.5 - reach * t
        y = hy - 0.5 - 1.6 * math.sin(math.pi * t * 0.7) + (3.2 + bow) * t ** 2.2
        th = thick * (1 - t) ** 0.55 + 0.3
        for k in range(int(th * 2) + 1):
            c = blade[0] if k < 2 else (blade[1] if k < th * 2 - 1 else blade[2])
            ic.px(x, y + k * 0.5, c)
    ic.px(hx, hy, shaft[0])


def whip(ic, handle, links, tip, turns=1.1, r0=6.2):
    """Handle on the lower-left diagonal, then a coiling lash spiralling up to the right."""
    ic.dband(-13, -7, 15, 16, lambda k, n, d: handle[0] if k == 0 else handle[1])
    ic.dband(-8, -7, 14, 17, handle[2])
    pts = []
    for i in range(120):
        t = i / 119
        a = math.pi * 1.25 - t * turns * 2 * math.pi
        r = r0 * (1 - 0.55 * t)
        pts.append((8.5 + math.cos(a) * r + t * 2.5, 8.5 - math.sin(a) * r - t * 2.5))
    last = None
    for i, (x, y) in enumerate(pts):
        p = (round(x), round(y))
        if p == last:
            continue
        last = p
        ic.px(x, y, links[(i // 6) % len(links)])
    ic.px(*pts[-1], tip)
    return pts


# ================================================================ weapons
def w_antler_scythe():
    ic = Icon()
    # dark living-wood haft, a pale bone blade grown from branching antlers, moss at the joint
    scythe(ic, ('C', 'k', ')'), ('|', 'M', 'T'), thick=2.6)
    for (x, y, c) in ((14, 1, 'u'), (15, 0, 'v'), (12, 0, 'u'), (13, 3, ')'), (12, 4, '+'), (11, 5, ')')):
        ic.px(x, y, c)
    ic.px(2, 8, '+'); ic.px(4, 12, ')')
    return ic


def w_briar_scythe():
    ic = Icon()
    # a bramble-wrapped haft, green-black blade edged with thorns
    scythe(ic, (')', '(', 'l'), ('+', ')', '('), reach=11, thick=2.3)
    for d in (-10, -6, -2, 2, 6):
        ic.dpx(d, 14, '+'); ic.dpx(d + 1, 17, ')')
    for x in (4, 7, 10):
        ic.px(x, 3, '+')
    return ic


def w_thornwood_staff():
    ic = Icon()
    # a gnarled thornwood staff crowned with a knot of green thorns and a bud of light
    ic.dband(-13, 8, 15, 16, lambda k, n, d: 'w' if k == 0 else ('L' if d % 4 else 'l'))
    for d in (-9, -4, 1, 5):
        ic.dpx(d, 13, ')'); ic.dpx(d + 1, 18, ')')
    ic.rows(10, 0, [
        ".)+).",
        ")(+()",
        "+(Y(+",
        ")(()).",
        ".)..)",
    ])
    ic.px(12, 2, 'W')
    return ic


def w_choir_harpoon():
    ic = Icon()
    # a black harpoon shaft wound with drowned rope, barbed teal-glowing head
    ic.dband(-13, 3, 15, 16, lambda k, n, d: 'C' if k == 0 else 'k')
    for d in (-10, -7, -4):
        ic.dband(d, d, 15, 16, '-')
    widths = {4: (15, 16), 5: (14, 17), 6: (13, 17), 7: (14, 16), 8: (14, 16), 9: (15, 16), 10: (15, 16), 11: (15, 15), 12: (15, 15), 13: (15, 15)}
    ic.dband(4, 13, lambda d: widths[d][0], lambda d: widths[d][1], ramp3('~', '-', ','))
    for (d, s) in ((6, 11), (7, 11), (6, 20), (7, 19)):        # barbs
        ic.dpx(d, s, '~' if s < 15 else '-')
    ic.dpx(13, 15, 'W')
    ic.px(1, 12, '-'); ic.px(3, 15, ',')
    return ic


def w_tidecleaver():
    ic = Icon()
    # a massive sea-worn cleaver: barnacled iron, a wave-curled teal edge
    ic.dband(-13, -3, 15, 16, lambda k, n, d: 'L' if k == 0 else 'l')
    ic.dband(-3, -2, 12, 18, lambda k, n, d: '-' if k < 2 else ',')

    def hi(d):
        return min(21, 17 + (d + 1)) - (1 if d >= 11 else 0) - (1 if d >= 12 else 0)

    def col(k, n, d):
        if k == 0:
            return '4'
        if k == n:
            return '~'
        if k == n - 1:
            return '-'
        return 'u' if (d * 3 + k) % 7 == 0 else ('3' if (d + k) % 5 else '2')
    ic.dband(-1, 12, 13, hi, col)
    return ic


def w_barnacle_fang():
    ic = Icon()
    # a curved fang-dagger crusted with barnacles, a pearl in its pommel
    lo, hi = taper(14, 16, 5, 9)
    ic.dband(-2, 9, lo, hi, lambda k, n, d: 'v' if k == 0 else ('u' if k < n else 't'))
    for d in (0, 3, 6):
        ic.dpx(d, 16, 'S')
    ic.dpx(9, 15, 'W')
    ic.dband(-3, -3, 12, 18, lambda k, n, d: '-' if k < 2 else ',')
    ic.dband(-8, -4, 15, 16, lambda k, n, d: ',' if (d + k) % 2 else '-')
    ic.ell(2.5, 13.5, 1.6, 1.6, lambda nx, ny: 'W' if nx + ny < -0.5 else ('v' if nx + ny < 0.5 else 'u'))
    return ic


def w_sanguine_rapier():
    ic = Icon()
    # a needle rapier of blood-red steel with a swept gold cup-hilt
    lo, hi = taper(15, 16, 6, 13)
    ic.dband(-3, 13, lo, hi, lambda k, n, d: '*' if k == 0 else '&')
    ic.dpx(13, 15, 'P')
    for (d, s) in ((-5, 11), (-6, 12), (-6, 18), (-5, 19), (-4, 12), (-4, 18)):
        ic.dpx(d, s, 'y')
    ic.dband(-4, -4, 13, 17, lambda k, n, d: 'Y' if k < 2 else 'G')
    ic.dband(-10, -5, 15, 16, lambda k, n, d: '%' if (d + k) % 2 else 'k')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'Y' if k < 2 else 'G')
    ic.px(12, 5, '*'); ic.px(13, 8, '%')
    return ic


def w_carving_knife():
    ic = Icon()
    # a butler's broad carving knife, polished steel, black bone handle, a drop of red
    ic.dband(-1, 10, 13, lambda d: 16 if d < 8 else 15, lambda k, n, d: '5' if k == 0 else ('4' if k < n - 1 else '3'))
    ic.dband(-1, 7, 16, 16, '2')
    ic.dpx(10, 13, 'W')
    ic.dband(-3, -2, 13, 17, '4')
    ic.dband(-9, -4, 15, 16, lambda k, n, d: 'k' if (d + k) % 3 else 'C')
    ic.px(11, 7, '&'); ic.px(11, 8, '%')
    return ic


def w_crimson_scythe():
    ic = Icon()
    # a black scythe whose long blade drips blood
    scythe(ic, ('C', 'k', '&'), ('*', '&', '%'), thick=2.8, bow=1.0)
    ic.px(3, 7, '&'); ic.px(3, 8, '%'); ic.px(6, 8, '&')
    return ic


def w_vael_greatsword():
    ic = Icon()
    # a massive bone greatsword bound in corroded gold, ghost-fire running down the fuller
    lo, hi = taper(13, 17, 9, 13)
    ic.dband(-4, 13, lo, hi, lambda k, n, d: 'H' if k == 0 else ('M' if k < n else 'T'))
    ic.dband(-3, 10, 15, 15, '@')
    for d in (-1, 3, 7):
        ic.dpx(d, 15, '[')
    ic.dpx(13, 15, 'W')
    ic.dband(-6, -5, 10, 20, lambda k, n, d: 'y' if k < 2 else ('G' if k < n - 1 else 'g'))
    ic.dpx(-6, 10, 'H'); ic.dpx(-6, 20, 'T')                # horned guard tips
    ic.dband(-10, -7, 15, 16, lambda k, n, d: ']' if (d + k) % 2 else 'k')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: '@' if k < 2 else '?')
    return ic


def w_headsman_chain():
    ic = Icon()
    # an iron chain whip ending in a heavy hooked blade
    pts = whip(ic, ('6', 'C', '3'), ['4', '3', '4', '2'], '5', turns=1.0)
    x, y = pts[-1]
    ic.rows(int(x) - 2, int(y) - 2, ["55.", "543", ".32"])
    return ic


def w_gravechain():
    ic = Icon()
    # a rusted grave chain with a small skull-weight at its end, pale ghost-light in the links
    pts = whip(ic, ('z', 'x', '3'), ['X', 'z', '@', 'X'], 'v', turns=1.15)
    x, y = pts[-1]
    ic.ell(x, y, 1.6, 1.5, lambda nx, ny: 'v' if nx + ny < 0 else 'u')
    ic.px(x, y, 'k')
    return ic


def w_pharaoh_khopesh():
    ic = Icon()
    # a gold khopesh: straight grip, blade hooking forward in a sickle, lapis inlay
    ic.dband(-13, -5, 15, 16, lambda k, n, d: 'b' if (d + k) % 2 else 'a')
    ic.dband(-4, -4, 13, 17, 'y')
    ic.dband(-3, 4, 14, 17, lambda k, n, d: 'Y' if k == 0 else ('y' if k < n else 'G'))
    ic.rows(8, 0, [
        "..YYY.",
        ".YyyyG",
        "Yy..yG",
        "Yy..G.",
        "yG....",
    ])
    ic.px(9, 1, 'W'); ic.px(7, 6, 'A')
    return ic


def w_sun_sceptre():
    ic = Icon()
    # a gold sceptre topped by a sun disc with rays
    ic.dband(-13, 5, 15, 16, lambda k, n, d: 'y' if k == 0 else 'G')
    for d in (-9, -3):
        ic.dband(d, d, 14, 17, 'a')
    for a in range(0, 360, 45):
        r0, r1 = 3.6, 5.6 if a % 90 == 0 else 5.0
        ic.line(11.5 + math.cos(math.radians(a)) * r0, 4 - math.sin(math.radians(a)) * r0,
                11.5 + math.cos(math.radians(a)) * r1, 4 - math.sin(math.radians(a)) * r1, 'Y')
    ic.ell(11.5, 4, 2.8, 2.8, lambda nx, ny: 'W' if nx + ny < -0.6 else ('Y' if nx + ny < 0.5 else 'y'))
    return ic


def w_scarab_spear():
    ic = Icon()
    # a bronze spear whose head is a stylised scarab with folded wings
    ic.dband(-13, 3, 15, 16, lambda k, n, d: '=' if k == 0 else '<')
    ic.dband(2, 3, 14, 17, lambda k, n, d: 'y' if k < 2 else 'G')
    widths = {4: (14, 17), 5: (13, 18), 6: (13, 18), 7: (13, 17), 8: (14, 17), 9: (14, 16), 10: (15, 16), 11: (15, 16), 12: (15, 15), 13: (15, 15)}
    ic.dband(4, 13, lambda d: widths[d][0], lambda d: widths[d][1], lambda k, n, d: 'Y' if k == 0 else ('-' if k == n // 2 and d < 9 else ('y' if k < n else 'G')))
    ic.dpx(13, 15, 'W')
    return ic


def w_starblade():
    ic = Icon()
    # an obsidian katana cracked with starlight, a star at the tip
    def lo(d):
        t = (d + 3) / 16
        return 15 - round(1.3 * math.sin(math.pi * min(1.0, t) * 0.85)) + (1 if d >= 12 else 0)

    def hi(d):
        return lo(d) + (0 if d >= 12 else 1)
    ic.dband(-3, 13, lo, hi, lambda k, n, d: ']' if k == 0 else 'k')
    for d in (-1, 2, 5, 8, 10):
        ic.dpx(d, lo(d) + (1 if d % 2 else 0), '_' if d % 3 else '^')
    ic.dband(-5, -4, 12, 18, lambda k, n, d: '^' if k == 0 else (']' if k in (1, n) else 'k'))
    ic.dband(-11, -6, 15, 16, lambda k, n, d: '^' if (d + k) % 3 == 0 else '1')
    sparkle(ic, 14, 1, c='W', c2='_')
    return ic


def w_meteor_maul():
    ic = Icon()
    # a haft driven into a smouldering meteorite: black rock, violet-white glowing cracks
    ic.dband(-13, 1, 15, 16, lambda k, n, d: 'L' if k == 0 else 'l')
    ic.dband(-13, -12, 14, 17, '3')
    ic.ell(10.5, 5, 5.2, 4.8, lambda nx, ny: '6' if nx + ny < -0.6 else ('C' if nx + ny < 0.5 else 'k'))
    for (a, b) in (((8, 3), (11, 6)), ((11, 6), (14, 5)), ((11, 6), (10, 9))):
        ic.line(*a, *b, '^')
    ic.px(11, 6, '_'); ic.px(8, 3, '_')
    ic.px(15, 1, '^'); ic.px(14, 0, ']')
    return ic


def w_orrery_whip():
    ic = Icon()
    # a brass whip of linked orrery rings, a small glowing planet at the end
    pts = whip(ic, ('y', 'G', 'g'), ['y', 'G', '^', 'y'], '_', turns=1.2)
    x, y = pts[-1]
    ic.ell(x, y, 1.8, 1.8, lambda nx, ny: '_' if nx + ny < -0.4 else '^')
    return ic


def w_saint_lance():
    ic = Icon()
    # a white chrome energy lance, cyan light core, magenta circuit lines
    ic.dband(-13, 2, 15, 16, lambda k, n, d: '5' if k == 0 else '4')
    for d in (-10, -6, -2):
        ic.dpx(d, 15, ':')
    ic.dband(3, 13, lambda d: 15 - (1 if d < 9 else 0), lambda d: 16 + (1 if d < 7 else 0) - (1 if d > 11 else 0),
             lambda k, n, d: 'W' if k == 0 else ('9' if k < n else '8'))
    ic.dband(4, 11, 15, 15, 'W')
    ic.dpx(13, 15, 'W'); ic.px(15, 0, '9'); ic.px(13, 4, ';')
    return ic


def w_plasma_katana():
    ic = Icon()
    # a katana whose blade is pure magenta plasma around a white core, chrome guard
    def lo(d):
        t = (d + 3) / 16
        return 15 - round(1.2 * math.sin(math.pi * min(1.0, t) * 0.85)) + (1 if d >= 12 else 0)

    def hi(d):
        return lo(d) + (0 if d >= 12 else 1)
    ic.dband(-3, 13, lambda d: lo(d) - 1, lambda d: hi(d) + 1, lambda k, n, d: ':' if k in (0, n) else ('W' if k == 1 else ';'))
    ic.dband(-5, -4, 12, 18, lambda k, n, d: '5' if k == 0 else '3')
    ic.dband(-11, -6, 15, 16, lambda k, n, d: '8' if (d + k) % 3 == 0 else '1')
    ic.px(1, 14, '9')
    return ic


def w_last_kindling():
    ic = Icon()
    # a root-and-flame scythe: pale root haft, a blade of white fire
    scythe(ic, ('p', 'U', '{'), ('}', '|', '{'), thick=3.0)
    for (x, y) in ((4, 2), (7, 1), (10, 1)):
        ic.px(x, y, '}')
    ic.px(5, 1, '|'); ic.px(1, 5, '|')
    ic.px(13, 5, 'h')
    return ic


# ================================================================ arts
def a_reap():
    ic = Icon()
    # a full circle of reaping: a scythe blade sweeping round with green motion
    for i in range(80):
        a = 2 * math.pi * i / 80
        ic.px(8 + math.cos(a) * 6.5, 8 + math.sin(a) * 6.5, '+' if i < 25 else (')' if i < 55 else '('))
    crescent_band(ic, 8, 8, 6.2, 150, 20, 2.6, ('W', '5', '4'))
    ic.line(8, 8, 12, 12, 'L'); ic.px(8, 8, 'w')
    return ic


def a_harvest_moon():
    ic = Icon()
    # a great pale-gold crescent moon spinning, trailing its own echoes
    crescent_band(ic, 9, 8, 6.5, 250, 70, 3.4, ('W', 'Y', 'y'))
    for (y, x0, x1) in ((3, 1, 4), (8, 0, 3), (13, 1, 4)):
        ic.line(x0, y, x1, y, 'G')
    ic.px(12, 2, 'W')
    return ic


def a_lash():
    ic = Icon()
    # a whip cracking: an S-curve lash ending in a spark
    pts = [(1, 14), (4, 10), (6, 11), (9, 7), (11, 8), (13, 4)]
    for (a, b) in zip(pts, pts[1:]):
        ic.line(*a, *b, 'z')
    for (a, b) in zip(pts, pts[1:]):
        ic.line(a[0], a[1] - 1, b[0], b[1] - 1, 'X')
    sparkle(ic, 14, 2, big=True, c='W', c2='Y')
    return ic


def a_chain_drag():
    ic = Icon()
    # a chain hooked into a foe's skull, pulled taut toward you
    for x in range(1, 11):
        ic.px(x, 8, '4' if x % 2 else '3')
        if x % 2:
            ic.px(x, 7, '5')
    ic.rows(10, 5, ["5.", "53", "43", "3."])
    ic.ell(13, 8, 2.6, 3, lambda nx, ny: 'v' if nx + ny < 0 else 'u')
    ic.px(12, 8, 'k'); ic.px(14, 8, 'k')
    for (x, y) in ((2, 5), (2, 11), (4, 4), (4, 12)):
        ic.px(x, y, 'S')
    return ic


def a_blood_frenzy():
    ic = Icon()
    # three blood-red thrust streaks and a falling drop
    for (y, x0) in ((4, 2), (8, 0), (12, 3)):
        ic.line(x0, y, 12, y, '&'); ic.line(x0 + 3, y, 13, y, '*'); ic.px(14, y, 'P')
    ic.poly([(10, 9), (12, 12), (12, 13), (11, 15), (9, 15), (8, 13), (8, 12)], lambda x, y: '*' if x < 10 else '&')
    return ic


def a_tidal_surge():
    ic = Icon()
    # a curling wave crest breaking forward
    for y in range(16):
        for x in range(16):
            cx, cy = 9, 9
            d = math.hypot(x - cx, (y - cy) * 1.1)
            if 3.5 < d < 7 and not (x < 9 and y < 8):
                ic.px(x, y, '~' if d > 6 else ('-' if d > 4.7 else ','))
    ic.rect(0, 13, 15, 15, ','); ic.line(0, 13, 15, 13, '-')
    ic.px(4, 4, '~'); ic.px(3, 6, '-'); ic.px(6, 3, '~')
    ic.px(15, 7, 'W'); ic.px(14, 5, '~')
    return ic


def a_solar_flare():
    ic = Icon()
    # a raised khopesh with a blazing sun above it
    for a in range(0, 360, 30):
        r1 = 7.4 if a % 60 == 0 else 6.2
        ic.line(8 + math.cos(math.radians(a)) * 4.2, 6 - math.sin(math.radians(a)) * 4.2,
                8 + math.cos(math.radians(a)) * r1, 6 - math.sin(math.radians(a)) * r1, 'Y' if a % 60 == 0 else 'y')
    ic.ell(8, 6, 3.4, 3.4, lambda nx, ny: 'W' if nx + ny < -0.5 else ('Y' if nx + ny < 0.5 else 'h'))
    ic.line(8, 11, 8, 15, 'G'); ic.px(7, 11, 'y'); ic.px(9, 11, 'y')
    return ic


def a_starfall():
    ic = Icon()
    # stars streaking down diagonally onto the ground
    for (x, y, L) in ((12, 2, 5), (7, 4, 6), (13, 8, 4)):
        for i in range(L):
            ic.px(x - i, y - i, ']' if i > L - 2 else '^')
        sparkle(ic, x + 1, y + 1, c='W', c2='_')
    ic.line(0, 15, 15, 15, 'S')
    return ic


def a_overclock():
    ic = Icon()
    # a neon clock face with its hand spun past the limit, glitch bars
    ic.ell(8, 8, 6.6, 6.6, lambda nx, ny: None if nx * nx + ny * ny < 0.68 else ('9' if nx + ny < 0 else '8'))
    ic.line(8, 8, 8, 3, 'W'); ic.line(8, 8, 12, 10, ';')
    ic.px(8, 8, ':')
    for (y, x0, x1, c) in ((2, 11, 15, ':'), (13, 0, 4, '9'), (14, 10, 13, ';')):
        ic.line(x0, y, x1, y, c)
    return ic


def a_pale_pyre():
    ic = Icon()
    # a ring of pale white flames rising around a root
    for (bx, h, w) in ((3, 9, 2.0), (8, 13, 2.6), (13, 9, 2.0)):
        flame_tongue(ic, bx + 0.5, 14, h, w, bx * 0.5, ('}', '|', '{', 'T'))
    ic.line(1, 15, 14, 15, 'U')
    return ic


# ================================================================ spells
def s_bramble_snare():
    ic = Icon()
    # a coil of thorned brambles snapping shut on the ground
    for i in range(70):
        t = i / 69
        a = t * 2 * math.pi * 1.4
        r = 6.5 - 3.5 * t
        x, y = 8 + math.cos(a) * r, 10 + math.sin(a) * r * 0.55
        ic.px(x, y, '+' if math.sin(a) < 0 else ')')
    for (x, y) in ((2, 8), (13, 8), (5, 12), (11, 13), (8, 6)):
        ic.px(x, y - 1, 'v')
    ic.line(5, 6, 3, 1, ')'); ic.line(11, 6, 13, 1, ')'); ic.px(3, 1, '+'); ic.px(13, 1, '+')
    return ic


def s_drowning_hymn():
    ic = Icon()
    # a wave of pale drowned faces singing, open-mouthed
    for y in range(16):
        for x in range(16):
            v = 9 + 3 * math.sin(x * 0.55)
            if y >= v:
                ic.px(x, y, '-' if y < v + 2 else ',')
    for cx in (3, 8, 13):
        cy = 9 + 3 * math.sin(cx * 0.55) - 2
        ic.ell(cx, cy, 2, 2.4, lambda nx, ny: 'v' if nx + ny < 0.4 else 'u')
        ic.px(cx - 1, cy - 0.5, 'k'); ic.px(cx + 1, cy - 0.5, 'k'); ic.px(cx, cy + 1, 'k')
    ic.px(5, 1, '~'); ic.px(10, 2, '~'); ic.px(12, 0, '-')
    return ic


def s_blood_lance():
    ic = Icon()
    # a crimson lance thrusting up-right, a drop of blood returning
    ic.dband(-12, 13, 15, lambda d: 17 if d < 6 else (16 if d < 11 else 15), lambda k, n, d: '*' if k == 0 else ('&' if k < n else '%'))
    ic.dband(-8, 9, 15, 15, 'P')
    ic.dpx(13, 15, 'W')
    ic.poly([(3, 3), (5, 6), (5, 7), (4, 8), (2, 8), (1, 7), (1, 6)], lambda x, y: '*' if x < 3 else '&')
    return ic


def s_crimson_rite():
    ic = Icon()
    # a bleeding heart inside a crimson sigil circle
    ic.ell(8, 8, 7.2, 7.2, lambda nx, ny: None if nx * nx + ny * ny < 0.72 else ('&' if nx + ny < 0.3 else '%'))
    ic.rows(4, 4, [
        ".**.**.",
        "*P**&&&",
        "*****&%",
        ".***&%.",
        "..*&%..",
        "...%...",
    ])
    ic.px(8, 11, '&'); ic.px(8, 13, '*')
    return ic


def s_soul_chains():
    ic = Icon()
    # ghostly blue chains crossing in an X around a small soul flame
    for (a, b) in (((1, 1), (14, 14)), ((1, 14), (14, 1))):
        n = 14
        for i in range(n + 1):
            x = a[0] + (b[0] - a[0]) * i / n
            y = a[1] + (b[1] - a[1]) * i / n
            ic.px(x, y, '[' if i % 3 == 0 else ('@' if i % 3 == 1 else None) or '?')
    flame_tongue(ic, 8, 11, 6, 2.0, 0.5, ('[', '@', '?', '?'))
    return ic


def s_sunbeam():
    ic = Icon()
    # a column of sunlight falling onto the ground from a small sun
    for y in range(3, 15):
        for x in range(5, 11):
            e = min(x - 5, 10 - x)
            ic.px(x, y, 'W' if e >= 2 else ('Y' if e == 1 else 'y'))
    ic.ell(8, 2, 3.2, 2.2, lambda nx, ny: 'W' if ny < 0 else 'Y')
    ic.line(1, 15, 14, 15, 'y'); ic.px(3, 14, 'Y'); ic.px(12, 14, 'Y')
    return ic


def s_sandstorm():
    ic = Icon()
    # a funnel of whirling sand
    for i in range(110):
        t = i / 109
        y = 1 + 13 * t
        r = 7 * (1 - t) ** 0.8 + 0.8
        a = t * 18
        ic.px(8 + math.cos(a) * r + (1 - t) * 0.5, y, '>' if math.sin(a) < -0.2 else ('=' if math.sin(a) < 0.5 else '<'))
    ic.px(2, 3, '='); ic.px(14, 6, '<'); ic.px(12, 11, '=')
    return ic


def s_comet():
    ic = Icon()
    # a white-violet comet streaking down-right with a long tail
    for i in range(12):
        x, y = 2 + i * 0.85, 1 + i * 0.85
        w = 2.4 * i / 11
        ic.ell(x, y, max(0.6, w * 0.6), max(0.6, w * 0.6), lambda nx, ny, i=i: ']' if i < 4 else ('^' if i < 9 else '_'))
    ic.ell(12, 11, 2.8, 2.8, lambda nx, ny: 'W' if nx + ny < 0 else '_')
    ic.px(14, 14, '^'); ic.px(10, 14, ']')
    return ic


def s_pulse_shot():
    ic = Icon()
    # three neon bolts in a line, magenta cores with cyan trails
    for (x, y) in ((11, 4), (8, 8), (5, 12)):
        ic.line(x - 5, y + 1, x - 1, y, '8')
        ic.rows(x - 1, y - 1, [".;.", ";W:", ".:."])
    return ic


def s_null_field():
    ic = Icon()
    # a hex-grid dome with a crossed-out bolt inside
    ic.ell(8, 11, 7, 7, lambda nx, ny: None if ny > 0.55 or nx * nx + ny * ny < 0.7 else ('9' if nx + ny < 0 else '8'))
    for (x, y) in ((4, 8), (8, 6), (12, 8), (6, 10), (10, 10)):
        ic.px(x, y, '7')
    ic.line(1, 15, 14, 15, '8')
    ic.line(6, 8, 10, 12, ':'); ic.line(10, 8, 6, 12, ':')
    return ic


# ================================================================ charms
def c_antler():
    ic = Icon()
    # a small branching antler bound with a pale ribbon and moss
    ic.line(8, 15, 8, 5, 'u'); ic.line(9, 15, 9, 6, 't')
    for (a, b) in (((8, 10), (4, 6)), ((4, 6), (3, 2)), ((4, 6), (1, 5)), ((8, 7), (12, 3)), ((12, 3), (13, 0)), ((12, 3), (15, 3)), ((8, 5), (7, 1))):
        ic.line(*a, *b, 'v')
    ic.line(7, 12, 10, 12, 'W'); ic.px(10, 13, 'p'); ic.px(11, 14, 'p')
    ic.px(9, 9, '+'); ic.px(7, 9, ')')
    return ic


def c_moss():
    ic = Icon()
    # a round stone overgrown with luminous moss, a tiny sprout on top
    ic.ell(8, 10, 6, 5, lambda nx, ny: 'S' if nx + ny < -0.3 else ('s' if nx + ny < 0.6 else '1'))
    ic.ell(8, 8, 6, 3.4, lambda nx, ny: ('+' if nx + ny < -0.2 else ')') if ny < 0.4 else None)
    ic.line(8, 5, 8, 2, ')'); ic.px(9, 2, '+'); ic.px(7, 1, '+')
    ic.px(4, 11, ')'); ic.px(11, 12, ')')
    return ic


def c_gill():
    ic = Icon()
    # a teal fish-gill charm on a cord, bubbles rising from it
    necklace(ic, 8, 0, 4, 4.4, 'l', 'L')
    ic.ell(8, 9, 5, 4.5, lambda nx, ny: '~' if nx + ny < -0.6 else ('-' if nx + ny < 0.5 else ','))
    for x in (6, 8, 10):
        ic.line(x, 7, x - 1, 11, ',')
    ic.px(13, 3, '~'); ic.px(14, 1, '~'); ic.px(12, 5, '-')
    return ic


def c_pearl():
    ic = Icon()
    # a black pearl in an open shell glowing teal
    ic.poly([(1, 10), (15, 10), (13, 14), (3, 14)], lambda x, y: 'u' if y < 12 else 't')
    ic.poly([(2, 9), (14, 9), (12, 3), (4, 3)], lambda x, y: 'v' if y < 5 else 'u')
    for x in (4, 7, 10, 13):
        ic.px(x, 12, 't')
    ic.ell(8, 9, 2.8, 2.6, lambda nx, ny: '~' if nx + ny < -0.6 else ('-' if nx + ny < 0.4 else 'k'))
    return ic


def c_bloodvial():
    ic = Icon()
    # a slender glass vial of blood sealed with gold
    ic.rect(7, 0, 8, 2, 'y'); ic.px(7, 0, 'Y')
    ic.poly([(6, 3), (9, 3), (11, 7), (11, 13), (9, 15), (6, 15), (4, 13), (4, 7)], lambda x, y: 'e' if y < 7 else ('*' if x < 6 else ('&' if x < 9 else '%')))
    ic.px(5, 8, 'W'); ic.px(5, 9, 'P')
    return ic


def c_countess():
    ic = Icon()
    # a gold brooch set with a bleeding ruby, bat-wing filigree
    for (a, b) in (((1, 6), (5, 9)), ((14, 6), (10, 9)), ((1, 6), (3, 10)), ((14, 6), (12, 10))):
        ic.line(*a, *b, 'y')
    ic.ell(7.5, 8.5, 4, 4, lambda nx, ny: 'Y' if nx + ny < -0.5 else ('y' if nx + ny < 0.6 else 'G'))
    gem(ic, 7.5, 8.5, 2.6, 2.6, ('W', '*', '&', '%'))
    ic.px(7, 13, '&'); ic.px(7, 14, '%')
    return ic


def c_crown():
    ic = Icon()
    # a small corroded gold crown with bone spikes and a ghost-blue gem
    ic.poly([(1, 13), (1, 6), (4, 9), (6, 3), (8, 8), (10, 3), (12, 9), (15, 6), (15, 13)],
            lambda x, y: 'y' if x < 6 else ('G' if x < 11 else 'g'))
    for (x, y) in ((1, 5), (6, 2), (10, 2), (15, 5)):
        ic.px(x, y, 'H')
    ic.line(1, 12, 15, 12, 'x')
    gem(ic, 8, 10, 1.8, 1.8, ('[', '@', '@', '?'))
    return ic


def c_court():
    ic = Icon()
    # a purple signet ring bearing a skull seal
    ic.ell(8, 10, 5.6, 4.6, lambda nx, ny: None if nx * nx + ny * ny < 0.4 else ('j' if nx + ny < -0.4 else ('I' if nx + ny < 0.5 else 'i')))
    ic.ell(8, 4.5, 3.6, 3.2, lambda nx, ny: 'v' if nx + ny < 0 else 'u')
    ic.px(7, 4, 'k'); ic.px(9, 4, 'k'); ic.px(8, 6, 't')
    return ic


def c_scarab():
    ic = Icon()
    # a gold-and-lapis scarab with spread wings
    ic.poly([(1, 6), (6, 5), (6, 11), (2, 10)], lambda x, y: 'A' if y < 8 else 'a')
    ic.poly([(15, 6), (10, 5), (10, 11), (14, 10)], lambda x, y: 'A' if y < 8 else 'a')
    ic.ell(8, 8.5, 2.8, 4.6, lambda nx, ny: 'Y' if nx + ny < -0.4 else ('y' if nx + ny < 0.5 else 'G'))
    ic.ell(8, 3, 1.8, 1.6, lambda nx, ny: 'y')
    ic.line(8, 6, 8, 12, 'G')
    ic.px(1, 5, 'y'); ic.px(15, 5, 'y')
    return ic


def c_sun():
    ic = Icon()
    # a gold sun disc pendant held by two cobra wings
    ic.ell(8, 7, 4.4, 4.4, lambda nx, ny: 'W' if nx + ny < -0.8 else ('Y' if nx + ny < 0.2 else ('y' if nx + ny < 0.8 else 'h')))
    ic.line(0, 12, 5, 10, 'a'); ic.line(15, 12, 10, 10, 'a'); ic.line(1, 13, 6, 11, 'A'); ic.line(14, 13, 9, 11, 'A')
    ic.line(8, 12, 8, 14, 'G')
    return ic


def c_star():
    ic = Icon()
    # a shard of fallen star: violet-white glass, radiant
    ic.poly([(8, 0), (10, 6), (15, 8), (10, 10), (8, 15), (6, 10), (1, 8), (6, 6)],
            lambda x, y: '_' if (x <= 8 and y <= 8) else ('^' if x + y < 18 else ']'))
    ic.px(8, 8, 'W'); ic.px(7, 7, 'W')
    return ic


def c_orrery():
    ic = Icon()
    # a brass cog with a tiny planet orbiting on a ring
    for a in range(0, 360, 45):
        ic.rect(int(7.5 + math.cos(math.radians(a)) * 6), int(8 + math.sin(math.radians(a)) * 6),
                int(7.5 + math.cos(math.radians(a)) * 6) + 1, int(8 + math.sin(math.radians(a)) * 6) + 1, 'G')
    ic.ell(8, 8.5, 5.2, 5.2, lambda nx, ny: None if nx * nx + ny * ny < 0.25 else ('Y' if nx + ny < -0.4 else ('y' if nx + ny < 0.5 else 'G')))
    ic.ell(8, 8.5, 1.4, 1.4, lambda nx, ny: '^')
    ic.px(12, 3, '_'); ic.px(13, 3, '^')
    return ic


def c_hack():
    ic = Icon()
    # a chip with a glowing eye, circuit traces running out
    ic.rect(4, 4, 11, 11, '2'); ic.rect(5, 5, 10, 10, '1')
    for i in (5, 8, 10):
        ic.line(i, 0, i, 3, '8'); ic.line(i, 12, i, 15, '8'); ic.line(0, i, 3, i, ':'); ic.line(12, i, 15, i, ':')
    ic.ell(7.5, 7.5, 2.4, 1.6, lambda nx, ny: '9')
    ic.px(7, 7, 'W')
    return ic


def c_neon():
    ic = Icon()
    # a neon halo ring, cyan and magenta segments
    for i in range(64):
        a = 2 * math.pi * i / 64
        c = '9' if (i // 8) % 2 == 0 else ':'
        ic.px(8 + math.cos(a) * 6, 8 + math.sin(a) * 3.2, c)
        ic.px(8 + math.cos(a) * 5.2, 8 + math.sin(a) * 2.5, '8' if c == '9' else '/')
    ic.px(8, 4, 'W'); ic.px(8, 12, 'W')
    return ic


def c_lastflame():
    ic = Icon()
    # a single pale flame cupped in a root cradle
    flame_tongue(ic, 8, 12, 11, 3.2, 0.7, ('}', '|', '{', 'T'))
    ic.line(3, 11, 6, 14, 'U'); ic.line(13, 11, 10, 14, 'U'); ic.line(6, 14, 10, 14, 'p')
    return ic


def i_tidebreath():
    ic = Icon()
    # a great teal bubble of held breath with a small pale conch inside, smaller bubbles rising
    ic.ell(7, 9, 6.4, 6.4, lambda nx, ny: None if nx * nx + ny * ny < 0.72 else ('~' if nx + ny < -0.2 else ('-' if nx + ny < 0.7 else ',')))
    ic.px(4, 5, 'W'); ic.px(5, 4, '~')
    ic.poly([(4, 12), (6, 8), (9, 7), (11, 9), (9, 12)], lambda x, y: 'v' if x + y < 16 else 'u')
    ic.line(6, 11, 9, 8, 't')
    for (x, y, r) in ((13, 3, 1.3), (14.5, 0.8, 0.8)):
        ic.ell(x, y, r, r, lambda nx, ny: '~' if nx + ny < 0 else '-')
    return ic


def i_moonstep():
    ic = Icon()
    # three crescent moons rising like steps, a star at the top
    def moon(cx, cy, r):
        ic.ell(cx, cy, r, r, lambda nx, ny: None if (nx + 0.75) ** 2 + (ny + 0.35) ** 2 < 0.45 else
               ('W' if nx + ny < 0.2 else ('_' if nx + ny < 0.9 else '^')))
    moon(3, 12.5, 2.5); moon(8, 8.5, 2.6); moon(13, 4.5, 2.7)
    sparkle(ic, 14, 1, c='W', c2='_')
    return ic


ICONS = [
    ("w_antler_scythe", w_antler_scythe), ("w_briar_scythe", w_briar_scythe), ("w_thornwood_staff", w_thornwood_staff),
    ("w_choir_harpoon", w_choir_harpoon), ("w_tidecleaver", w_tidecleaver), ("w_barnacle_fang", w_barnacle_fang),
    ("w_sanguine_rapier", w_sanguine_rapier), ("w_carving_knife", w_carving_knife), ("w_crimson_scythe", w_crimson_scythe),
    ("w_vael_greatsword", w_vael_greatsword), ("w_headsman_chain", w_headsman_chain), ("w_gravechain", w_gravechain),
    ("w_pharaoh_khopesh", w_pharaoh_khopesh), ("w_sun_sceptre", w_sun_sceptre), ("w_scarab_spear", w_scarab_spear),
    ("w_starblade", w_starblade), ("w_meteor_maul", w_meteor_maul), ("w_orrery_whip", w_orrery_whip),
    ("w_saint_lance", w_saint_lance), ("w_plasma_katana", w_plasma_katana), ("w_last_kindling", w_last_kindling),
    ("a_reap", a_reap), ("a_harvest_moon", a_harvest_moon), ("a_lash", a_lash), ("a_chain_drag", a_chain_drag),
    ("a_blood_frenzy", a_blood_frenzy), ("a_tidal_surge", a_tidal_surge), ("a_solar_flare", a_solar_flare),
    ("a_starfall", a_starfall), ("a_overclock", a_overclock), ("a_pale_pyre", a_pale_pyre),
    ("s_bramble_snare", s_bramble_snare), ("s_drowning_hymn", s_drowning_hymn), ("s_blood_lance", s_blood_lance),
    ("s_crimson_rite", s_crimson_rite), ("s_soul_chains", s_soul_chains), ("s_sunbeam", s_sunbeam),
    ("s_sandstorm", s_sandstorm), ("s_comet", s_comet), ("s_pulse_shot", s_pulse_shot), ("s_null_field", s_null_field),
    ("c_antler", c_antler), ("c_moss", c_moss), ("c_gill", c_gill), ("c_pearl", c_pearl), ("c_bloodvial", c_bloodvial),
    ("c_countess", c_countess), ("c_crown", c_crown), ("c_court", c_court), ("c_scarab", c_scarab), ("c_sun", c_sun),
    ("c_star", c_star), ("c_orrery", c_orrery), ("c_hack", c_hack), ("c_neon", c_neon), ("c_lastflame", c_lastflame),
    ("i_tidebreath", i_tidebreath), ("i_moonstep", i_moonstep),
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
        asebuild.build("ui_icons5", S, S, ["Outline", "Icon"], frames, tags)
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
    sheet.save(os.path.join(pdir, "ui5.png"))
    print("ui_icons5:", len(frames), "icons")


if __name__ == "__main__":
    main()
