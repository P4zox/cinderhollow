#!/usr/bin/env python3
"""Skill tree art (agent ST, docs/SKILLTREE_CONTRACT.md):
  sk_icons      16x16, one tag per node icon `sk_<id>` (78: five branches x 12, 10 Arsenal masteries, 8 Wayfarer)
  sk_icons_dim  the same icons desaturated and sunk into shadow, tags `skd_<id>` (locked / sealed nodes)
  sk_frames     32x32 node frames: n/f/k/m (+0 locked, 1 available, 2 learned) for trunk, fork, keystone, mastery,
                and `core`, the ember sigil at the heart of the constellation.

Same house style as gen_ui.py / gen_ui2.py / gen_ui5.py (their Icon grid, dband diagonal rasteriser and palette):
one strong silhouette, lit from the upper-left, auto 1px near-black outline on its own layer. Branch colour keys:
Blade steel+gold, Ash azure+violet, Veil violet+ghost blue, Blood crimson, Flame ember, Arsenal weapons, Wayfarer
moss/teal/gold. Keystones are the brightest and busiest of their branch.
The twelve surviving node ids reuse their gen_ui.py drawings, so a returning player recognises them.
Re-runnable: python3 art/gen_skills.py [--preview-only]   (preview -> art/previews/skills.png)
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
import gen_ui  # noqa: E402
import gen_ui2  # noqa: E402
import gen_ui3  # noqa: E402  (palette keys)
import gen_ui5  # noqa: E402  (palette keys + scythe/whip)
from gen_ui2 import Icon, ramp3, taper, crescent_band, gem, sparkle, flame_tongue  # noqa: E402

S = 16
PAL = gen_ui2.PAL
FIRE = ('Y', 'h', 'F', 'f')          # hot -> cool flame ramp
AZ = ('c', 'A', 'a', 'b')


def arc(ic, cx, cy, r, a0, a1, c, step=2.0):
    """Thin arc (degrees, counter-clockwise, y up)."""
    n = int(abs(a1 - a0) / step) + 1
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        ic.px(cx + math.cos(a) * r, cy - math.sin(a) * r, c(i / n) if callable(c) else c)


def ring(ic, cx, cy, r0, r1, fn):
    for y in range(S):
        for x in range(S):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r0 <= d <= r1:
                c = fn(x + 0.5 - cx, y + 0.5 - cy) if callable(fn) else fn
                if c:
                    ic.g[y][x] = c


def drop(ic, cx, top, bot, rw, cols):
    """Teardrop: point at top, round at the bottom. cols = (glint, lit, mid, dark)."""
    for y in range(S):
        for x in range(S):
            t = (y + 0.5 - top) / max(1, bot - top)
            if not 0 <= t <= 1:
                continue
            w = rw * (math.sin(math.pi * min(1, t * 1.25) / 2) if t < 0.8 else math.sqrt(max(0, 1 - ((t - 0.8) / 0.2) ** 2 * 0.9)))
            dx = x + 0.5 - cx
            if abs(dx) <= w:
                v = -dx / max(w, 0.1) - (t - 0.55) * 1.6
                ic.px(x, y, cols[1] if v > 0.6 else (cols[2] if v > -0.5 else cols[3]))
    ic.px(cx - rw * 0.45, top + (bot - top) * 0.62, cols[0])


def bolt(ic, pts, c1, c2=None):
    for i in range(len(pts) - 1):
        ic.line(*pts[i], *pts[i + 1], c1)
        if c2:
            ic.line(pts[i][0] + 1, pts[i][1], pts[i + 1][0] + 1, pts[i + 1][1], c2)


def slash(ic, cx, cy, r, a0, a1, thick, cols=('W', '5', '4')):
    crescent_band(ic, cx, cy, r, a0, a1, thick, cols)


def reuse(fn):
    """A gen_ui.py skill drawing (gen_ui.Icon) -> this module's Icon so images() uses the shared palette."""
    src = fn()
    ic = Icon()
    ic.g = [row[:] for row in src.g]
    return ic


# ================================================================ BLADE (steel + gold)
def heavy_hand():
    ic = Icon()
    # a greatsword driven point-first into the ground with all its weight, stone cracking round the tip
    ic.rect(6, 0, 9, 1, 'y'); ic.px(6, 0, 'Y')
    ic.rect(7, 2, 8, 3, 'l'); ic.px(7, 2, 'L')
    ic.rect(3, 4, 12, 4, 'G'); ic.px(3, 4, 'y'); ic.px(4, 4, 'Y'); ic.px(12, 4, 'g')
    ic.poly([(5, 5), (10, 5), (10, 10), (8, 12), (7, 12), (5, 10)], lambda x, y: '5' if x < 7 else ('4' if x < 9 else '3'))
    ic.line(7, 5, 7, 11, 'W')
    ic.rect(0, 13, 15, 15, 's'); ic.line(0, 13, 15, 13, 'S')
    for (x0, y0, x1, y1) in ((7, 12, 3, 15), (8, 12, 12, 15), (6, 13, 1, 13), (9, 13, 14, 13)):
        ic.line(x0, y0, x1, y1, 'y')
    ic.px(7, 12, 'W'); ic.px(8, 12, 'Y')
    for (x, y) in ((2, 10), (13, 10), (1, 7), (14, 7)):
        ic.px(x, y, 'u')
    return ic


def measured_cut():
    ic = Icon()
    # one clean, deliberate cut: a long white slash across a dark moon, a gold bead where it began
    ic.ell(8.5, 7.5, 5.5, 5.5, lambda nx, ny: 'k' if nx + ny > -0.9 else 'C')
    ic.line(1, 14, 14, 1, '5'); ic.line(2, 14, 14, 2, '4'); ic.line(1, 13, 13, 1, 'W')
    ic.px(14, 1, 'W'); ic.px(15, 0, '5')
    ic.ell(2, 13.5, 1.6, 1.6, lambda nx, ny: 'Y' if nx + ny < 0 else 'y')
    ic.px(1, 12, 'W')
    return ic


def flowing_form():
    ic = Icon()
    # two clean ribbons of steel flowing one into the next, a gold bead where they meet
    for (cy, c1, c2, ph) in ((5.5, 'W', '5', 0.0), (10.5, '5', '4', 2.2)):
        for x in range(0, 16):
            y = cy + 2.2 * math.sin(x * 0.42 + ph)
            ic.px(x, y, c1); ic.px(x, y + 1, c2)
    ic.ell(8, 8, 1.6, 1.6, lambda nx, ny: 'Y' if nx + ny < 0 else 'y')
    ic.px(15, 4, 'W')
    return ic


def sunder():
    ic = Icon()
    # a round gold-rimmed shield split clean in two, the halves prised apart, shards flying
    for dx, side in ((-1.6, -1), (1.6, 1)):
        ic.ell(7.5 + dx, 8.5, 6.2, 6.4, lambda nx, ny, side=side: None if nx * side < 0.12 else
               ('y' if nx * nx + ny * ny > 0.74 else ('4' if (side < 0 and ny < 0) else ('3' if ny < 0.35 else '2'))))
    ic.line(7, 0, 8, 3, 'W'); ic.line(8, 3, 7, 6, 'W'); ic.line(7, 6, 8, 9, '5')
    ic.ell(4, 8.5, 1.2, 1.2, lambda nx, ny: 'Y'); ic.ell(11, 8.5, 1.2, 1.2, lambda nx, ny: 'y')
    for (x, y, c) in ((1, 1, '4'), (14, 2, '5'), (15, 6, '4'), (0, 5, '5')):
        ic.px(x, y, c)
    return ic


def executioner():
    ic = Icon()
    # a headsman's broad crescent axe, a crimson bead running off the edge
    ic.dband(-13, 6, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -12, 14, 17, 'G')
    ic.poly([(8, 1), (14, 2), (15, 7), (13, 10), (9, 7)], lambda x, y: '5' if x + y < 12 else ('4' if x + y < 18 else '3'))
    ic.line(14, 2, 15, 7, 'W'); ic.line(15, 7, 13, 10, '5')
    ic.px(9, 4, '2'); ic.px(10, 6, '2')
    ic.px(14, 10, 'R'); ic.px(14, 11, 'r'); ic.px(13, 12, 'R'); ic.px(13, 13, 'm')
    return ic


def blade_dancer():
    ic = Icon()
    # two slim blades crossed mid-spin, a whirl of silver around them
    arc(ic, 8, 8, 7, 20, 160, lambda t: '5' if t < 0.5 else '4')
    arc(ic, 8, 8, 7, 200, 340, lambda t: '4' if t < 0.5 else '3')
    gen_ui.sword(ic, (13, 2), (4, 11), guard_w=1)
    gen_ui.sword(ic, (3, 2), (12, 11), guard_w=1, blade=('4', '3'))
    ic.px(8, 7, 'W')
    return ic


def crushing_weight():
    ic = Icon()
    # a great maul head driving down onto the ground, the floor buckling
    ic.rect(7, 0, 8, 4, 'L'); ic.px(7, 0, 'w')
    ic.poly([(2, 4), (13, 4), (13, 10), (2, 10)], lambda x, y: '4' if (x < 5 and y < 7) else ('3' if x < 10 else '2'))
    ic.line(2, 4, 13, 4, '5'); ic.line(2, 4, 2, 10, '5')
    ic.rect(2, 6, 13, 6, 'G'); ic.px(2, 6, 'y'); ic.px(3, 6, 'y')
    ic.rect(0, 13, 15, 13, 's'); ic.line(0, 13, 4, 13, 'S')
    for (x0, x1) in ((1, 5), (10, 14)):
        ic.line(x0, 12, x0 + 1, 11, 'y')
    ic.line(7, 11, 5, 14, 'y'); ic.line(8, 11, 10, 14, 'y'); ic.px(7, 11, 'W'); ic.px(8, 11, 'Y')
    ic.rect(0, 14, 15, 15, 'T')
    return ic


def tireless():
    ic = Icon()
    # an unbroken gold loop, the sign of the endless: strength that does not flag
    for i in range(160):
        t = i / 160 * 2 * math.pi
        x, y = 8 + 6.6 * math.sin(t), 8 + 3.4 * math.sin(2 * t)
        c = 'Y' if (x < 8 and y < 8) or (x >= 8 and y < 6.5) else ('y' if y < 9.5 else 'G')
        ic.px(x, y, c); ic.px(x, y + 1, 'G' if c != 'G' else 'g')
    ic.px(3, 5, 'W'); ic.px(12, 9, 'W')
    for (x, y) in ((1, 13), (14, 2)):
        sparkle(ic, x, y, c='Y', c2='y')
    return ic


def relentless():
    ic = Icon()
    # KEYSTONE: a raised blade beside a climbing stack of chevrons, each brighter than the last: the combo that grows
    gen_ui.sword(ic, (4, 0), (4, 11), guard_w=2)
    for i, (c1, c2) in enumerate((('G', 'g'), ('y', 'G'), ('Y', 'y'), ('W', 'Y'))):
        y = 13 - i * 3.3
        for k in range(4):
            ic.px(11 - k, y + k * 0.8, c1); ic.px(11 + k, y + k * 0.8, c2 if k else c1)
    ic.px(11, 0, 'W'); ic.px(10, 1, 'Y'); ic.px(12, 1, 'Y')
    return ic


# ================================================================ ASH (azure / violet sorcery, gold settings)
def kindled_mind():
    ic = Icon()
    # an azure flame kindled in a small gold brazier
    flame_tongue(ic, 8, 9, 9, 3.2, 0.4, ('W', 'c', 'A', 'a'))
    ic.poly([(2, 9), (13, 9), (11, 12), (4, 12)], lambda x, y: 'Y' if x < 5 else ('y' if x < 10 else 'G'))
    ic.line(2, 9, 13, 9, 'Y')
    ic.line(5, 13, 3, 15, 'G'); ic.line(10, 13, 12, 15, 'g'); ic.rect(7, 13, 8, 14, 'G')
    ic.px(7, 10, 'A'); ic.px(9, 11, 'a')
    for (x, y) in ((3, 3), (13, 4), (11, 1)):
        ic.px(x, y, 'c')
    return ic


def deep_well():
    ic = Icon()
    # a stone well brimming with azure light that rises from its depths
    ic.rect(2, 8, 13, 14, 's')
    for y in (10, 12):
        ic.line(2, y, 13, y, 'T')
    for (y, xs) in ((9, (5, 10)), (11, (3, 8, 12)), (13, (5, 10))):
        for x in xs:
            ic.px(x, y, 'T')
    ic.line(2, 8, 2, 14, 'S')
    ic.ell(7.5, 8, 6.4, 2.2, lambda nx, ny: 'S' if nx * nx + ny * ny > 0.55 else ('c' if nx < -0.2 else ('A' if nx < 0.4 else 'a')))
    for (x, y, c) in ((6, 5, 'A'), (8, 3, 'c'), (10, 5, 'A'), (7, 1, 'c'), (9, 0, 'W'), (5, 2, 'a'), (11, 2, 'a')):
        ic.px(x, y, c)
    ic.line(7, 4, 7, 6, 'c'); ic.line(8, 5, 8, 7, 'W')
    return ic


def quick_recall():
    ic = Icon()
    # a gold hourglass, azure sand streaming fast, a circling arrow of recall
    ic.poly([(4, 2), (11, 2), (8, 7), (7, 7)], lambda x, y: 'e' if y < 4 else 'A')
    ic.poly([(7, 8), (8, 8), (11, 13), (4, 13)], lambda x, y: 'e' if y < 11 else ('c' if x < 7 else 'A'))
    ic.line(7, 7, 7, 12, 'c')
    ic.rect(3, 1, 12, 1, 'y'); ic.rect(3, 14, 12, 14, 'G'); ic.px(3, 1, 'Y')
    ic.line(3, 2, 3, 13, 'G'); ic.line(12, 2, 12, 13, 'g')
    arc(ic, 8, 7.5, 7.3, 110, 250, 'c')
    ic.px(1, 11, 'W'); ic.px(0, 10, 'c'); ic.px(2, 11, 'c')
    return ic


def overcharge():
    ic = Icon()
    # an azure crystal cracking open, violet power spilling out of the fracture
    ic.poly([(8, 0), (12, 5), (8, 15), (4, 5)], lambda x, y: 'c' if (x < 8 and y < 6) else ('A' if x < 8 else ('a' if y < 10 else 'b')))
    ic.line(8, 1, 8, 13, 'A')
    bolt(ic, [(8, 3), (6, 6), (9, 8), (7, 11)], 'J')
    for (x0, y0, x1, y1) in ((4, 6, 1, 4), (12, 6, 15, 3), (5, 10, 2, 12), (11, 10, 14, 12)):
        ic.line(x0, y0, x1, y1, 'j')
    ic.px(1, 4, 'J'); ic.px(15, 3, 'J'); ic.px(6, 3, 'W')
    return ic


def mana_font():
    ic = Icon()
    # a small stone fountain, azure droplets springing up and falling back
    ic.poly([(2, 11), (13, 11), (11, 14), (4, 14)], lambda x, y: 'S' if y < 12 else ('s' if x < 10 else 'T'))
    ic.ell(7.5, 11, 5.6, 1.4, lambda nx, ny: 'A' if nx < 0.2 else 'a')
    ic.rect(7, 6, 8, 10, 'S'); ic.px(7, 6, 'u')
    for (x, y, c) in ((7, 4, 'c'), (8, 3, 'W'), (5, 2, 'A'), (10, 2, 'A'), (4, 4, 'c'), (11, 4, 'c'), (3, 6, 'A'), (12, 6, 'A'), (7, 1, 'c'), (8, 5, 'c')):
        ic.px(x, y, c)
    return ic


def memory_palace():
    ic = Icon()
    # three stacked tomes with azure and violet bindings, a glowing bookmark: room for one more spell
    for (y, c1, c2, x0, x1) in ((11, 'a', 'b', 2, 14), (7, 'I', 'i', 3, 13), (3, 'A', 'a', 2, 12)):
        ic.rect(x0, y, x1, y + 3, c2); ic.line(x0, y, x1, y, c1); ic.line(x0, y, x0, y + 3, c1)
        ic.line(x0 + 1, y + 1, x1 - 1, y + 1, 'v'); ic.px(x1, y + 1, 'u')
        ic.px(x0 + 2, y + 2, 'y'); ic.px(x0 + 3, y + 2, 'y')
    ic.line(10, 0, 10, 3, 'c'); ic.px(10, 0, 'W')
    return ic


def steady_cast():
    ic = Icon()
    # a warding circle of azure runes held steady around a gold spark
    ring(ic, 8, 8, 5.6, 7.2, lambda dx, dy: 'c' if dx + dy < -4 else ('A' if dx + dy < 3 else 'a'))
    for a in range(0, 360, 45):
        ic.px(8 + math.cos(math.radians(a)) * 6.4 - 0.5, 8 + math.sin(math.radians(a)) * 6.4 - 0.5, 'W' if a == 225 else 'b')
    ring(ic, 8, 8, 2.8, 3.6, 'a')
    sparkle(ic, 7.5, 7.5, c='W', c2='Y')
    return ic


def swift_incant():
    ic = Icon()
    # a winged azure bolt streaking right, speed lines in its wake
    for y, (x0, x1) in ((5, (0, 4)), (8, (0, 6)), (11, (1, 4))):
        ic.line(x0, y, x1, y, 'a'); ic.px(x1, y, 'A')
    ic.ell(11, 8, 3.8, 2.6, lambda nx, ny: 'W' if nx * nx + ny * ny < 0.25 else ('c' if nx * nx + ny * ny < 0.6 else 'A'))
    ic.poly([(8, 7), (5, 2), (11, 6)], lambda x, y: 'v' if y < 5 else 'u')
    ic.poly([(8, 9), (5, 14), (11, 10)], lambda x, y: 'u' if y > 11 else 'v')
    ic.px(15, 8, 'c')
    return ic


def resonance():
    ic = Icon()
    # a sword raised, its tip ringing with struck magic: clean azure arcs pulse outward
    gen_ui.sword(ic, (10, 5), (2, 13), guard_w=2)
    for (r, c) in ((2.5, 'W'), (4.3, 'c'), (6.2, 'A')):
        arc(ic, 10.5, 4.5, r, -40, 130, c, step=2.5)
    return ic


def spellblade():
    ic = Icon()
    # KEYSTONE: a sword whose blade is a shard of azure crystal wreathed in arcane fire, gold hilt
    for (bx, by, h, w, ph) in ((5, 11, 5, 1.4, 0.2), (8, 8, 6, 1.6, 1.1), (11, 5, 5, 1.4, 2.0), (13.5, 2.5, 3, 1.0, 0.4)):
        flame_tongue(ic, bx, by, h, w, ph, ('W', 'c', 'j', 'I'))
    lo, hi = taper(14, 16, 8, 13)
    ic.dband(-4, 13, lo, hi, ramp3('W', 'c', 'A'))
    ic.dband(-4, 9, 15, 15, 'A')
    ic.dband(-6, -5, 10, 20, lambda k, n, d: 'Y' if k < 3 else ('y' if k < n - 1 else 'G'))
    ic.dband(-10, -7, 15, 16, lambda k, n, d: 'I' if (d + k) % 3 else 'i')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'Y' if k == 0 else 'y')
    ic.dpx(13, 15, 'W')
    return ic


# ================================================================ VEIL (violet shadow, ghost blue, steel)
def deflect():
    ic = Icon()
    # a small buckler turning a blade aside in a shower of sparks
    ic.ell(6, 9, 5.2, 5.2, lambda nx, ny: 'y' if nx * nx + ny * ny > 0.7 else ('4' if nx + ny < -0.4 else ('3' if nx + ny < 0.5 else '2')))
    ic.ell(6, 9, 1.4, 1.4, lambda nx, ny: 'Y')
    gen_ui.sword(ic, (15, 0), (11, 4), guard_w=0, blade=('5', '4'))
    for (x, y, c) in ((10, 5, 'W'), (12, 6, 'Y'), (13, 8, 'y'), (9, 2, 'Y'), (14, 4, 'y'), (11, 8, 'Y')):
        ic.px(x, y, c)
    return ic


def evasive_strike():
    ic = Icon()
    # a violet roll-arc curling low and ending in a straight thrust of steel
    for i in range(60):
        t = i / 60
        a = math.pi * (0.5 + 1.3 * t)
        r = 5.2
        ic.px(6 + math.cos(a) * r, 8 - math.sin(a) * r, 'J' if t < 0.3 else ('j' if t < 0.7 else 'I'))
        ic.px(6 + math.cos(a) * (r - 1), 8 - math.sin(a) * (r - 1), 'I' if t < 0.6 else 'i')
    gen_ui.sword(ic, (15, 5), (8, 12), guard_w=1)
    return ic


def enduring():
    ic = Icon()
    # a green laurel wreath around a gold round: stamina that lasts
    for side in (-1, 1):
        for i in range(7):
            a = math.radians(250 - i * 22) if side < 0 else math.radians(-70 + i * 22)
            x, y = 8 + math.cos(a) * 6.2 * (1 if side > 0 else 1), 8 - math.sin(a) * 6.2
            ic.px(x, y, ')'); ic.px(x + side * 0.9, y - 0.9, '+' if i % 2 else 'o')
    ic.ell(8, 8, 3.4, 3.4, lambda nx, ny: 'Y' if nx + ny < -0.4 else ('y' if nx + ny < 0.5 else 'G'))
    ic.line(7, 6, 7, 10, 'N'); ic.line(8, 6, 8, 10, 'o'); ic.px(7, 6, 'O')
    return ic


def ironskin():
    ic = Icon()
    # an iron cuirass, riveted, a hard glint on the breast
    ic.poly([(3, 2), (6, 1), (9, 1), (12, 2), (13, 6), (12, 13), (8, 15), (7, 15), (3, 13), (2, 6)],
            lambda x, y: '4' if (x < 6 and y < 8) else ('3' if x < 10 else '2'))
    ic.line(6, 1, 9, 1, '5'); ic.line(3, 2, 2, 6, '5')
    ic.line(7, 3, 7, 14, '2'); ic.line(8, 3, 8, 14, '4')
    ic.line(3, 9, 12, 9, '2')
    for (x, y) in ((4, 4), (11, 4), (4, 11), (11, 11)):
        ic.px(x, y, 'y')
    sparkle(ic, 5, 5, c='W', c2='5')
    return ic


def featherfoot():
    ic = Icon()
    # a pale violet feather drifting, quill up-right, a trail of motion under it
    for i in range(13):
        t = i / 12
        x, y = 2 + 11 * t, 14 - 12 * t
        ic.px(x, y, 'u' if t < 0.25 else 'J')
        if 0.2 < t < 0.95:
            w = 3.2 * math.sin(math.pi * (t - 0.2) / 0.75)
            for k in range(1, int(w) + 1):
                ic.px(x - k * 0.7, y - k * 0.7 + 0.5, 'j' if k < w - 0.5 else 'I')
                ic.px(x + k * 0.7, y + k * 0.7 - 0.2, 'I' if k < w - 0.5 else 'i')
    ic.px(13, 2, 'W')
    for (x, y) in ((1, 10), (3, 12), (0, 13)):
        ic.px(x, y, '[')
    return ic


def light_feet():
    ic = Icon()
    # a light boot with a small pale wing at the ankle
    ic.poly([(6, 4), (9, 4), (9, 10), (13, 11), (14, 13), (6, 13)], lambda x, y: '4' if (x < 8 and y < 10) else ('3' if x < 11 else '2'))
    ic.line(6, 4, 6, 12, '5'); ic.rect(6, 14, 14, 14, '1')
    ic.poly([(6, 6), (0, 2), (2, 6), (0, 8), (5, 9)], lambda x, y: '[' if y < 5 else ('@' if y < 8 else '?'))
    ic.line(1, 3, 5, 6, '['); ic.px(0, 2, 'W')
    ic.rect(6, 8, 9, 8, 'G'); ic.px(6, 8, 'y')
    return ic


def shadowstep():
    ic = Icon()
    # KEYSTONE: a hooded figure stepping out of its own pale-violet afterimage
    def fig(dx, fill):
        ic.poly([(6 + dx, 1), (9 + dx, 1), (11 + dx, 4), (11 + dx, 8), (13 + dx, 15), (3 + dx, 15), (5 + dx, 8), (4 + dx, 4)], fill)
    fig(-3, lambda x, y: 'j' if x < 4 else 'I')
    fig(2, lambda x, y: 'k' if x > 9 else ('B' if y > 4 else 'i'))
    ic.line(8, 1, 6, 4, 'I'); ic.line(8, 1, 11, 1, 'I')
    ic.line(7, 6, 11, 6, 'k')
    ic.px(8, 6, 'J'); ic.px(10, 6, 'J')
    ic.line(1, 3, 3, 1, 'J'); ic.px(0, 9, 'j'); ic.px(1, 12, 'j')
    return ic


# ================================================================ BLOOD (crimson)
BLOOD = ('P', 'R', 'r', 'm')


def open_wounds():
    ic = Icon()
    # three raking claw gashes, blood welling and dripping from them
    for i, x0 in enumerate((2, 6, 10)):
        ic.line(x0, 1 + i, x0 + 4, 9 + i, 'R'); ic.line(x0 + 1, 1 + i, x0 + 5, 9 + i, 'r')
        ic.px(x0, 1 + i, 'P')
        ic.px(x0 + 4, 11 + i, 'R'); ic.px(x0 + 4, 12 + i, 'r')
    ic.px(2, 2, 'W')
    return ic


def hemorrhage():
    ic = Icon()
    # a violent burst of blood: a starburst splash around a dark core
    for a in range(0, 360, 30):
        r = 7 if a % 60 == 0 else 5
        ic.line(8, 8, 8 + math.cos(math.radians(a)) * r, 8 - math.sin(math.radians(a)) * r, 'R' if a % 60 else 'r')
    ic.ell(8, 8, 3.6, 3.6, lambda nx, ny: 'P' if nx + ny < -0.6 else ('R' if nx + ny < 0.4 else 'r'))
    for (x, y) in ((15, 8), (1, 8), (8, 1), (8, 15), (13, 3), (3, 13)):
        ic.px(x, y, 'm')
    ic.px(7, 6, 'W')
    return ic


def vein_burst():
    ic = Icon()
    # crimson veins branching out from a bursting heart-knot
    for (pts) in ([(8, 8), (5, 5), (3, 2), (1, 1)], [(8, 8), (11, 5), (14, 4)], [(8, 8), (5, 11), (2, 14)], [(8, 8), (11, 12), (13, 15)],
                  [(5, 5), (6, 1)], [(11, 5), (12, 1)], [(5, 11), (1, 10)], [(11, 12), (15, 10)]):
        for i in range(len(pts) - 1):
            ic.line(*pts[i], *pts[i + 1], 'r')
    ic.ell(8, 8, 3, 3, lambda nx, ny: 'P' if nx + ny < -0.5 else 'R')
    for (x, y) in ((1, 1), (14, 4), (2, 14), (13, 15), (6, 1), (12, 1), (1, 10), (15, 10)):
        ic.px(x, y, 'R')
    ic.px(7, 7, 'W')
    return ic


def blood_drinker():
    ic = Icon()
    # a gold chalice brimming with blood
    ic.poly([(2, 2), (13, 2), (12, 6), (9, 8), (6, 8), (3, 6)], lambda x, y: 'Y' if x < 5 else ('y' if x < 10 else 'G'))
    ic.ell(7.5, 2.8, 5, 1.3, lambda nx, ny: 'P' if nx < -0.4 else ('R' if nx < 0.4 else 'r'))
    ic.rect(7, 8, 8, 12, 'G'); ic.px(7, 9, 'y')
    ic.rect(4, 13, 11, 14, 'G'); ic.line(4, 13, 8, 13, 'y')
    ic.px(12, 4, 'R'); ic.px(12, 5, 'r'); ic.px(4, 3, 'W')
    return ic


def wrath():
    ic = Icon()
    # a horned war-helm, eyes burning red with fury
    ic.poly([(4, 4), (11, 4), (12, 8), (11, 14), (8, 15), (7, 15), (4, 14), (3, 8)], lambda x, y: '6' if (x < 6 and y < 9) else ('C' if x < 10 else 'k'))
    ic.line(4, 4, 11, 4, '6')
    ic.line(3, 5, 0, 1, 'u'); ic.line(2, 5, 0, 2, 't'); ic.px(0, 0, 'v')
    ic.line(12, 5, 15, 1, 't'); ic.line(13, 5, 15, 2, 'T'); ic.px(15, 0, 'u')
    ic.line(4, 8, 6, 9, 'R'); ic.line(11, 8, 9, 9, 'R'); ic.px(5, 8, 'P'); ic.px(10, 8, 'P')
    ic.line(7, 10, 7, 14, 'k'); ic.line(8, 10, 8, 14, 'k')
    return ic


def frenzy():
    ic = Icon()
    # three crimson crescents whirling round a red eye
    for k in range(3):
        crescent_band(ic, 8, 8, 6.6, 90 + k * 120, 20 + k * 120, 1.8, ('P', 'R', 'r'))
    ic.ell(8, 8, 2, 2, lambda nx, ny: 'R' if nx + ny < 0 else 'r')
    ic.px(8, 8, 'W')
    return ic


def blood_price():
    ic = Icon()
    # a gold cinder-coin with a single drop of blood running down its face
    ic.ell(7, 9, 6, 6, lambda nx, ny: 'G' if nx * nx + ny * ny > 0.72 else ('Y' if nx + ny < -0.5 else ('y' if nx + ny < 0.5 else 'G')))
    ic.ell(7, 9, 3.6, 3.6, lambda nx, ny: None if nx * nx + ny * ny < 0.8 else 'g')
    drop(ic, 11, 0, 8, 2.4, BLOOD)
    ic.px(10, 9, 'R'); ic.px(10, 10, 'r'); ic.px(4, 6, 'W')
    return ic


def crimson_veil():
    ic = Icon()
    # a hooded crimson veil, the dark face within hidden but for a glint
    ic.poly([(7, 0), (12, 3), (14, 9), (15, 15), (0, 15), (1, 9), (3, 3)], lambda x, y: 'R' if x < 5 else ('r' if x < 11 else 'm'))
    ic.ell(7.5, 7.5, 3.4, 4.2, lambda nx, ny: 'k' if ny < 0.8 else 'm')
    ic.line(7, 0, 3, 3, 'P'); ic.line(3, 3, 1, 9, 'R')
    ic.line(4, 11, 3, 15, 'm'); ic.line(11, 11, 12, 15, 'm')
    ic.px(6, 7, 'P'); ic.px(9, 7, 'P')
    return ic


def leech():
    ic = Icon()
    # a coiled leech, dark and glistening, its round mouth full of teeth
    for i in range(34):
        t = i / 34
        a = math.pi * (1.1 + 1.6 * t)
        r = 5.6 - 1.6 * t
        x, y = 8 + math.cos(a) * r, 8 - math.sin(a) * r
        w = 1.8 - 0.6 * t
        ic.ell(x, y, w, w, lambda nx, ny: 'r' if nx + ny < -0.3 else ('m' if nx + ny < 0.6 else '%'))
    ic.ell(3, 9.5, 2.6, 2.6, lambda nx, ny: 'm' if nx * nx + ny * ny > 0.5 else 'k')
    for (x, y) in ((2, 8), (4, 8), (2, 10), (4, 10)):
        ic.px(x, y, 'v')
    ic.px(10, 3, 'P'); ic.px(12, 6, 'P')
    return ic


def crimson_pact():
    ic = Icon()
    # KEYSTONE: a crimson heart bound in a ring of gold thorns, a drop falling from it
    ic.ell(5.5, 6, 3.4, 3.4, lambda nx, ny: 'P' if nx + ny < -0.6 else ('R' if nx + ny < 0.5 else 'r'))
    ic.ell(10.5, 6, 3.4, 3.4, lambda nx, ny: 'R' if nx + ny < -0.2 else ('r' if nx + ny < 0.8 else 'm'))
    ic.poly([(2, 7), (14, 7), (8, 13)], lambda x, y: 'R' if x < 7 else ('r' if x < 11 else 'm'))
    ic.px(4, 4, 'W')
    ring(ic, 8, 7.8, 6.8, 7.8, lambda dx, dy: 'y' if (int((math.atan2(dy, dx) + 3.2) * 3.2)) % 2 else 'G')
    for a in range(20, 360, 45):
        ic.px(8 + math.cos(math.radians(a)) * 8.2 - 0.5, 7.8 + math.sin(math.radians(a)) * 8.2 - 0.5, 'Y')
    ic.px(8, 14, 'R'); ic.px(8, 15, 'r')
    return ic


# ================================================================ FLAME (ember)
def ember_focus():
    ic = Icon()
    # a single ember held in the crosshairs of a gold focusing ring
    ring(ic, 8, 8, 5.8, 7.0, lambda dx, dy: 'y' if dx + dy < -2 else 'G')
    for (x0, y0, x1, y1) in ((8, 0, 8, 2), (8, 13, 8, 15), (0, 8, 2, 8), (13, 8, 15, 8)):
        ic.line(x0, y0, x1, y1, 'Y')
    flame_tongue(ic, 8, 11, 7, 2.2, 0.3, FIRE)
    return ic


def afterglow():
    ic = Icon()
    # a sun sinking below the horizon, its long warm rays still spreading
    ic.ell(8, 11, 5.2, 5.2, lambda nx, ny: None if ny > 0 else ('Y' if nx + ny < -0.7 else ('h' if nx + ny < -0.1 else 'F')))
    for a in (20, 50, 90, 130, 160):
        ic.line(8 + math.cos(math.radians(a)) * 6.5, 11 - math.sin(math.radians(a)) * 6.5, 8 + math.cos(math.radians(a)) * 8.5, 11 - math.sin(math.radians(a)) * 8.5, 'h')
    ic.rect(0, 11, 15, 11, 'f'); ic.rect(0, 12, 15, 12, 'g')
    ic.line(2, 14, 13, 14, 'F'); ic.line(5, 15, 10, 15, 'f')
    return ic


def kindling():
    ic = Icon()
    # a bundle of sticks, bound in twine, just catching flame
    for (x0, x1) in ((1, 13), (2, 14), (1, 14)):
        pass
    ic.line(1, 13, 13, 9, 'w'); ic.line(1, 14, 13, 10, 'L')
    ic.line(2, 9, 14, 13, 'L'); ic.line(2, 10, 14, 14, 'l')
    ic.line(3, 11, 13, 11, 'w'); ic.line(3, 12, 13, 12, 'L')
    ic.line(7, 9, 7, 14, 'u'); ic.line(8, 9, 8, 14, 't')
    flame_tongue(ic, 7.5, 9, 8, 2.6, 0.8, FIRE)
    flame_tongue(ic, 11, 9, 4, 1.3, 2.2, FIRE)
    return ic


def quick_charge():
    ic = Icon()
    # a flame inside a charge ring that is filling fast, three quarters lit
    ring(ic, 8, 8, 6, 7.4, lambda dx, dy: ('Y' if dx + dy < -3 else 'h') if (math.degrees(math.atan2(dy, dx)) + 360 + 90) % 360 < 270 else 'f')
    flame_tongue(ic, 8, 12, 9, 2.6, 1.6, FIRE)
    ic.px(1, 8, 'W')
    return ic


def wildfire():
    ic = Icon()
    # fire running wild across the ground, tongues of many heights
    for (bx, h, w, ph) in ((2, 6, 1.4, 0.5), (5, 10, 1.8, 1.3), (8.5, 13, 2.2, 0.2), (12, 9, 1.8, 2.1), (14.5, 5, 1.2, 1.0)):
        flame_tongue(ic, bx, 14, h, w, ph, FIRE)
    ic.rect(0, 15, 15, 15, 'f')
    return ic


def lingering_flame():
    ic = Icon()
    # a tall candle whose flame lingers long, a curl of smoke above
    ic.rect(6, 8, 9, 14, 'v'); ic.line(6, 8, 6, 14, 'W'); ic.line(9, 8, 9, 14, 'u')
    ic.rect(4, 15, 11, 15, 'G'); ic.px(4, 15, 'y')
    ic.px(7, 7, 'k')
    flame_tongue(ic, 7.5, 6, 6, 1.7, 0.5, ('W', 'Y', 'h', 'F'))
    for (x, y) in ((8, 0), (9, 1), (10, 0)):
        ic.px(x, y, 'T')
    ic.px(7, 9, 'u'); ic.px(8, 10, 'u')
    return ic


def pyre_heart():
    ic = Icon()
    # a heart of living fire, burning from within
    ic.ell(5.5, 6.5, 3.4, 3.4, lambda nx, ny: 'Y' if nx + ny < -0.6 else ('h' if nx + ny < 0.5 else 'F'))
    ic.ell(10.5, 6.5, 3.4, 3.4, lambda nx, ny: 'h' if nx + ny < -0.2 else ('F' if nx + ny < 0.8 else 'f'))
    ic.poly([(2, 8), (14, 8), (8, 14)], lambda x, y: 'h' if x < 7 else ('F' if x < 11 else 'f'))
    flame_tongue(ic, 8, 10, 7, 1.8, 0.4, ('W', 'Y', 'Y', 'h'))
    ic.px(4, 5, 'W')
    for (bx, ph) in ((5, 0.4), (11, 1.8)):
        flame_tongue(ic, bx, 3, 3, 1.2, ph, FIRE)
    return ic


def swift_arts():
    ic = Icon()
    # a blade trailing fire, speed streaks behind it
    for y, (x0, x1) in ((9, (0, 4)), (12, (0, 6)), (15, (2, 7))):
        ic.line(x0, y, x1, y, 'F'); ic.px(x1, y, 'h')
    for (bx, by, h, w, ph) in ((6, 12, 4, 1.2, 0.2), (9, 9, 4, 1.3, 1.1), (12, 6, 4, 1.2, 2.0)):
        flame_tongue(ic, bx, by, h, w, ph, FIRE)
    lo, hi = taper(14, 15, 9, 13)
    ic.dband(-2, 13, lo, hi, ramp3('W', '5', '4'))
    ic.dband(-4, -3, 12, 18, 'y')
    ic.dband(-7, -5, 15, 16, 'l')
    return ic


def war_drums():
    ic = Icon()
    # a war drum, hide head struck by two sticks, the beat rippling out
    ic.ell(8, 6, 6, 2.2, lambda nx, ny: 'v' if nx + ny < -0.3 else 'u')
    ic.rect(2, 6, 13, 13, 'r'); ic.line(2, 6, 2, 13, 'R')
    ic.ell(8, 13, 6, 1.8, lambda nx, ny: 'r' if ny < 0 else 'm')
    for x in (4, 7, 10, 13):
        ic.line(x - 2, 7, x, 12, 'y')
    ic.line(0, 0, 5, 5, 'w'); ic.line(15, 0, 10, 5, 'L'); ic.px(0, 0, 'u'); ic.px(15, 0, 'u')
    arc(ic, 8, 5, 7.5, 60, 120, 'h')
    return ic


def ember_blood():
    ic = Icon()
    # a drop of blood made of fire, embers glowing at its core
    drop(ic, 8, 0, 15, 5.2, ('W', 'Y', 'h', 'F'))
    ic.ell(8, 10.5, 2, 2.2, lambda nx, ny: 'Y' if nx + ny < 0 else 'h')
    ic.px(7, 10, 'W')
    for (x, y) in ((3, 12), (12, 13), (5, 6)):
        ic.px(x, y, 'f')
    return ic


def searing_arts():
    ic = Icon()
    # a branding iron, its sigil white-hot, smoke curling
    ic.dband(-13, 2, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -9, 15, 16, 'l')
    ring(ic, 11, 5, 2.2, 3.6, lambda dx, dy: 'W' if dx + dy < -1 else ('Y' if dx + dy < 1.5 else 'h'))
    ic.px(11, 5, 'h'); ic.px(10, 4, 'Y')
    for (x, y) in ((13, 0), (14, 1), (15, 0), (7, 1), (8, 0)):
        ic.px(x, y, 'T')
    return ic


def kindled():
    ic = Icon()
    # KEYSTONE: a great flame spiralling up out of a trail of fire, a white-gold heart
    for (bx, by, h, w, ph) in ((1.5, 15, 4, 1.1, 0.4), (4, 15, 6, 1.4, 1.5), (8, 15, 15, 3.4, 0.9), (12, 15, 8, 1.8, 2.3), (14.5, 15, 4, 1.1, 0.2)):
        flame_tongue(ic, bx, by, h, w, ph, FIRE)
    flame_tongue(ic, 8, 12, 8, 1.8, 0.5, ('W', 'W', 'Y', 'h'))
    ic.px(3, 2, 'Y'); ic.px(13, 4, 'Y'); ic.px(12, 1, 'h')
    return ic


# ================================================================ ARSENAL masteries: the weapon + its trick, gold laurel
def laurel(ic):
    """A small gold laurel sprig at the bottom-right: the mark of mastery."""
    for (x, y, c) in ((15, 15, 'Y'), (14, 15, 'y'), (15, 14, 'y'), (13, 15, 'G'), (15, 13, 'G'), (14, 14, 'Y')):
        ic.px(x, y, c)


def m_sword():
    ic = gen_ui2.w_longsword()
    # the finisher's arc of ash sweeping off the blade
    arc(ic, 7, 9, 7.2, 35, 150, lambda t: 'Y' if t < 0.35 else ('y' if t < 0.7 else 'G'), step=2)
    ic.px(12, 4, 'W')
    laurel(ic)
    return ic


def m_dagger():
    ic = gen_ui2.w_dagger()
    ic.ell(12, 3.5, 2.6, 2.6, lambda nx, ny: 'R' if nx * nx + ny * ny > 0.4 else 'P')
    for (x, y) in ((12, 0), (15, 3), (9, 3), (12, 7), (14, 1), (14, 6)):
        ic.px(x, y, 'R')
    ic.px(12, 3, 'W')
    laurel(ic)
    return ic


def m_great():
    ic = gen_ui2.w_greatsword()
    for (r, c) in ((4.5, 'y'), (6.5, 'G')):
        arc(ic, 3, 15.5, r, 10, 80, c, step=3)
    ic.rect(0, 15, 9, 15, 's')
    laurel(ic)
    return ic


def m_spear():
    ic = gen_ui2.w_spear()
    for (x0, y0, x1, y1) in ((0, 9, 3, 6), (1, 12, 5, 8), (4, 14, 7, 11)):
        ic.line(x0, y0, x1, y1, 'y')
    sparkle(ic, 14, 1)
    laurel(ic)
    return ic


def m_katana():
    ic = gen_ui2.w_katana()
    ic.line(0, 6, 9, 0, 'W'); ic.line(1, 7, 10, 1, 'c')
    laurel(ic)
    return ic


def m_staff():
    ic = gen_ui3.w_quarterstaff()
    # the staff whirling: bright arcs at both ends
    arc(ic, 8, 8, 7.2, 95, 175, lambda t: 'Y' if t < 0.5 else 'y', step=2)
    arc(ic, 8, 8, 7.2, 275, 355, lambda t: 'Y' if t < 0.5 else 'y', step=2)
    ic.px(1, 5, 'W'); ic.px(14, 10, 'W')
    laurel(ic)
    return ic


def m_shield():
    ic = Icon()
    gen_ui3.shield_shape(ic, lambda x, y: 'r' if x < 6 else ('m' if x < 10 else '%'), 'y', 'G')
    for (x, y) in ((0, 3), (15, 3), (0, 8), (15, 8), (4, 14), (11, 14), (7, 0)):
        ic.px(x, y, 'u')
    ic.line(7, 4, 7, 10, 'y'); ic.line(4, 7, 10, 7, 'y'); ic.px(7, 7, 'Y')
    laurel(ic)
    return ic


def m_twin():
    ic = Icon()
    # a twinblade: one grip, a blade out of each end, spinning
    lo, hi = taper(14, 16, 5, 13)
    ic.dband(3, 13, lo, hi, ramp3('5', '4', '2'))
    ic.dband(-13, -3, lambda d: 14 if d > -6 else 14 + (-6 - d) * 0.3, lambda d: 16 if d > -6 else 16 - (-6 - d) * 0.3, ramp3('5', '4', '2'))
    ic.dband(-2, 2, 15, 16, lambda k, n, d: 'l' if (d + k) % 2 else 'L')
    ic.dband(-3, -3, 13, 18, 'y'); ic.dband(3, 3, 13, 18, 'y')
    ic.dpx(13, 15, 'W'); ic.dpx(-13, 15, 'W')
    arc(ic, 8, 8, 7, 110, 160, 'Y', step=4); arc(ic, 8, 8, 7, 290, 340, 'Y', step=4)
    laurel(ic)
    return ic


def m_scythe():
    ic = Icon()
    gen_ui5.scythe(ic, ('w', 'L', 'l'), ('W', '5', '3'))
    for (x, y) in ((2, 11), (3, 12), (1, 13)):
        ic.px(x, y, 'R')
    ic.px(2, 12, 'P')
    laurel(ic)
    return ic


def m_whip():
    ic = Icon()
    gen_ui5.whip(ic, ('w', 'L', 'l'), ('v', 'u', 't'), 'W')
    sparkle(ic, 12, 3, big=True, c='W', c2='Y')
    ic.px(15, 0, 'y'); ic.px(9, 1, 'y')
    laurel(ic)
    return ic


# ================================================================ WAYFARER (the road: moss, teal, gold)
def way_prosper():
    ic = Icon()
    # a heap of glowing gold cinders, one more tumbling onto the pile
    for (cx, cy, r) in ((4, 12, 2.6), (8, 12.5, 2.8), (12, 12, 2.6), (6, 9.5, 2.4), (10, 9.5, 2.4), (8, 7, 2.3)):
        ic.ell(cx, cy, r, r * 0.8, lambda nx, ny: 'Y' if nx + ny < -0.5 else ('y' if nx + ny < 0.5 else 'G'))
    ic.ell(12.5, 3, 1.8, 1.8, lambda nx, ny: 'Y' if nx + ny < 0 else 'y')
    ic.px(12, 2, 'W'); ic.px(7, 6, 'W'); ic.px(3, 11, 'W')
    ic.px(10, 5, 'y'); ic.px(14, 6, 'G')
    return ic


def way_glint():
    ic = Icon()
    # a keen eye, and in front of it a cracked stone that glints
    ic.ell(8, 6, 7, 3.4, lambda nx, ny: 'v' if nx * nx + ny * ny > 0.35 else None)
    ic.ell(8, 6, 2.6, 2.6, lambda nx, ny: 'q' if nx + ny < 0 else 'D')
    ic.ell(8, 6, 1.1, 1.1, lambda nx, ny: 'k')
    ic.px(7, 5, 'W')
    ic.rect(2, 11, 13, 15, 's'); ic.line(2, 11, 13, 11, 'S'); ic.line(8, 11, 8, 15, 'T'); ic.line(2, 13, 13, 13, 'T')
    ic.line(5, 11, 7, 14, 'Y'); sparkle(ic, 11, 13, c='W', c2='Y')
    return ic


def way_remnant():
    ic = Icon()
    # a tied leather purse, a few cinders kept safe inside
    ic.ell(8, 10, 5.6, 4.8, lambda nx, ny: 'w' if nx + ny < -0.5 else ('L' if nx + ny < 0.5 else 'l'))
    ic.poly([(5, 5), (11, 5), (9, 7), (7, 7)], 'L')
    ic.line(5, 6, 11, 6, 'y'); ic.px(5, 6, 'Y')
    ic.line(4, 4, 6, 5, 'w'); ic.line(12, 4, 10, 5, 'L')
    ic.ell(8, 11, 1.8, 1.8, lambda nx, ny: 'Y' if nx + ny < 0 else 'y')
    ic.px(5, 9, 'u')
    return ic


def way_hook():
    ic = Icon()
    # the Root Hook flung far: a living root line reaching to a gold hook
    for i in range(14):
        ic.px(1 + i * 0.75, 14 - i * 0.75, ')' if i % 3 else '(')
    ic.px(3, 13, '+'); ic.px(6, 9, '+')
    arc(ic, 12, 5, 3, 200, 450, lambda t: 'Y' if t < 0.4 else ('y' if t < 0.8 else 'G'))
    ic.px(9, 3, 'W')
    for (x, y) in ((14, 12), (12, 14)):
        ic.px(x, y, 'y')
    ic.line(11, 10, 15, 14, 'G')
    return ic


def way_glide():
    ic = Icon()
    # a billowing cloak riding a tailwind
    ic.poly([(3, 2), (9, 1), (14, 4), (12, 9), (15, 14), (7, 12), (2, 14), (4, 8)], lambda x, y: 'Z' if x + y < 9 else ('V' if x + y < 17 else 'd'))
    ic.line(3, 2, 9, 1, 'W')
    for (x0, y0, x1) in ((0, 5, 2), (0, 9, 3), (0, 12, 1)):
        ic.line(x0, y0, x1, y0, 'Z')
    ic.px(8, 4, 'y'); ic.px(9, 4, 'Y')
    return ic


def way_dash():
    ic = Icon()
    # two ember dash flames in a row: the second charge
    for (ox_, c) in ((0, ('h', 'F', 'f')), (7, ('Y', 'h', 'F'))):
        for y in range(4, 13):
            for x in range(0, 9):
                dx, dy = x + 0.5 - 5, y + 0.5 - 8.5
                if (dx / 3.4) ** 2 + (dy / 3.6) ** 2 <= 1 and not (dx < -1 and abs(dy) > 2):
                    r = math.hypot(dx - 0.8, dy)
                    ic.px(x + ox_, y, c[0] if r < 1.4 else (c[1] if r < 2.6 else c[2]))
    ic.px(12, 8, 'W')
    for (x, y) in ((0, 3), (0, 13)):
        ic.px(x, y, 'f')
    return ic


def way_slam():
    ic = Icon()
    # a fist of stone hammering down, a shockwave rolling out both ways
    ic.poly([(5, 0), (10, 0), (11, 3), (11, 7), (4, 7), (4, 3)], lambda x, y: 'S' if x < 7 else 's')
    ic.line(5, 0, 10, 0, 'u'); ic.line(5, 2, 10, 2, 's'); ic.line(5, 4, 10, 4, 's')
    ic.line(4, 8, 11, 8, 'h'); ic.px(7, 8, 'Y'); ic.px(8, 8, 'Y')
    for side in (-1, 1):
        for i, c in enumerate(('Y', 'h', 'F')):
            x = 7.5 + side * (3 + i * 2.5)
            ic.line(x, 12 - i, x + side * 1.5, 13, c)
    ic.rect(0, 14, 15, 15, 's'); ic.line(0, 14, 15, 14, 'S')
    return ic


def way_wall():
    ic = Icon()
    # a talon hooked into a stone wall, claws biting the mortar
    for y in range(0, 16, 4):
        for x in range(0 if (y // 4) % 2 else 3, 16, 7):
            ic.rect(x, y, min(15, x + 5), y + 2, 's'); ic.line(x, y, min(15, x + 5), y, 'S')
    for (x0, y0, x1, y1) in ((4, 12, 7, 4), (7, 13, 10, 5), (10, 14, 13, 7)):
        ic.line(x0, y0, x1, y1, 'u'); ic.line(x0 + 1, y0, x1 + 1, y1, 't'); ic.px(x1, y1, 'v'); ic.px(x1, y1 - 1, 'W')
    return ic


# ================================================================ registry
KEEP = ['keen_edge', 'fourth_strike', 'charged_arts', 'riposte_mastery', 'bloodthirst', 'azure_thrift', 'soul_siphon', 'quickstep',
        'iron_flask', 'steadfast', 'last_stand', 'second_wind']
ORDER = [
    # blade
    'keen_edge', 'heavy_hand', 'fourth_strike', 'measured_cut', 'flowing_form', 'charged_arts', 'sunder', 'executioner', 'blade_dancer',
    'crushing_weight', 'tireless', 'relentless',
    # ash
    'kindled_mind', 'deep_well', 'azure_thrift', 'quick_recall', 'overcharge', 'soul_siphon', 'mana_font', 'memory_palace', 'steady_cast',
    'swift_incant', 'resonance', 'spellblade',
    # veil
    'quickstep', 'iron_flask', 'riposte_mastery', 'deflect', 'evasive_strike', 'steadfast', 'enduring', 'second_wind', 'ironskin',
    'featherfoot', 'light_feet', 'shadowstep',
    # blood
    'bloodthirst', 'open_wounds', 'hemorrhage', 'vein_burst', 'blood_drinker', 'last_stand', 'wrath', 'frenzy', 'blood_price',
    'crimson_veil', 'leech', 'crimson_pact',
    # flame
    'ember_focus', 'afterglow', 'kindling', 'quick_charge', 'wildfire', 'lingering_flame', 'pyre_heart', 'swift_arts', 'war_drums',
    'ember_blood', 'searing_arts', 'kindled',
    # arsenal
    'm_sword', 'm_dagger', 'm_great', 'm_spear', 'm_katana', 'm_staff', 'm_shield', 'm_twin', 'm_scythe', 'm_whip',
    # wayfarer
    'way_prosper', 'way_glint', 'way_remnant', 'way_hook', 'way_glide', 'way_dash', 'way_slam', 'way_wall',
]


def draw(nid):
    if nid in KEEP:
        return reuse(getattr(gen_ui, nid))
    return globals()[nid]()


# ================================================================ node frames (32x32)
FR = 32
FRAME_COLS = {   # (outline, shadow, body, lit, highlight, inner)
    0: ((8, 7, 12), (30, 26, 34), (48, 42, 54), (70, 62, 76), (92, 84, 96), (13, 11, 15)),
    1: ((8, 7, 12), (70, 48, 22), (116, 84, 40), (168, 128, 56), (206, 168, 92), (17, 13, 14)),
    2: ((8, 7, 12), (132, 88, 30), (196, 146, 58), (240, 196, 98), (255, 238, 176), (34, 24, 16)),
}


def frame_img(kind, lvl):
    im = Image.new("RGBA", (FR, FR), (0, 0, 0, 0))
    OUT, SH, BODY, LIT, HI, INNER = FRAME_COLS[lvl]
    c = FR / 2
    px = im.load()

    def put(x, y, col, a=255):
        if 0 <= x < FR and 0 <= y < FR:
            px[x, y] = col + (a,)
    shape = {}   # (x, y) -> colour, painted in order

    def shade(dx, dy, r):
        v = (-dx - dy) / max(1e-6, r * 1.414)   # +1 upper-left .. -1 lower-right
        return HI if v > 0.62 else (LIT if v > 0.15 else (BODY if v > -0.45 else SH))
    if kind in 'nfk':
        r_in, r_out = (10.2, 12.2) if kind != 'k' else (12.0, 14.6)
        for y in range(FR):
            for x in range(FR):
                dx, dy = x + 0.5 - c, y + 0.5 - c
                d = math.hypot(dx, dy)
                if d < r_in:
                    shape[(x, y)] = INNER
                elif d <= r_out:
                    shape[(x, y)] = shade(dx, dy, d)
        if kind == 'k':   # eight star points + an inner hairline ring
            for i in range(8):
                a = i * math.pi / 4 + math.pi / 8
                for t in range(0, 30):
                    rr = r_out + t * 0.06
                    w = 1.6 * (1 - t / 30)
                    for k in range(-2, 3):
                        ox_, oy_ = -math.sin(a) * k * 0.5, math.cos(a) * k * 0.5
                        if abs(k * 0.5) <= w:
                            x, y = int(c + math.cos(a) * rr + ox_), int(c + math.sin(a) * rr + oy_)
                            shape[(x, y)] = shade(math.cos(a), math.sin(a), 1) if lvl else BODY
            for y in range(FR):
                for x in range(FR):
                    d = math.hypot(x + 0.5 - c, y + 0.5 - c)
                    if 10.9 <= d <= 11.5:
                        shape[(x, y)] = BODY if lvl < 2 else LIT
        if kind == 'f':   # a fork: an inner hairline ring (the UI adds a crimson link-stud facing the partner)
            for y in range(FR):
                for x in range(FR):
                    d = math.hypot(x + 0.5 - c, y + 0.5 - c)
                    if 9.0 <= d <= 9.6:
                        shape[(x, y)] = (LIT if lvl == 2 else BODY) if lvl else SH
        if kind == 'n' and lvl:   # four tiny rivets on the ring
            for a in (45, 135, 225, 315):
                x, y = int(c + math.cos(math.radians(a)) * 11.2), int(c + math.sin(math.radians(a)) * 11.2)
                shape[(x, y)] = HI
    elif kind == 'm':   # square mastery frame with bevelled corners
        lo, hi = 4, FR - 5
        for y in range(lo, hi + 1):
            for x in range(lo, hi + 1):
                edge = min(x - lo, hi - x, y - lo, hi - y)
                cut = (min(x - lo, hi - x) + min(y - lo, hi - y)) < 2
                if cut:
                    continue
                if edge >= 2:
                    shape[(x, y)] = INNER
                else:
                    v = (1 if (x - lo < 2 or y - lo < 2) else -1)
                    shape[(x, y)] = (HI if edge == 0 else LIT) if v > 0 else (BODY if edge == 0 else SH)
        for (x, y) in ((lo + 1, lo + 1), (hi - 1, lo + 1), (lo + 1, hi - 1), (hi - 1, hi - 1)):
            shape[(x, y)] = HI if lvl else LIT
    for (x, y), col in shape.items():
        put(x, y, col)
    # 1px outline around everything
    a = im.getchannel('A')
    out = []
    for y in range(FR):
        for x in range(FR):
            if a.getpixel((x, y)):
                continue
            if any(0 <= x + dx < FR and 0 <= y + dy < FR and a.getpixel((x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.append((x, y))
    for (x, y) in out:
        put(x, y, OUT)
    return im


def core_img():
    """The ember at the heart of the constellation: a gold ring around a burning seed, root-spokes out."""
    im = Image.new("RGBA", (FR, FR), (0, 0, 0, 0))
    px = im.load()
    c = FR / 2
    GOLD = [(96, 54, 18), (170, 110, 40), (240, 170, 60), (255, 210, 120), (255, 248, 230)]
    EMB = [(122, 34, 16), (200, 70, 26), (244, 128, 40), (255, 210, 120), (255, 248, 230)]
    for y in range(FR):
        for x in range(FR):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            d = math.hypot(dx, dy)
            v = (-dx - dy) / max(1e-6, d * 1.414)
            if 9.2 <= d <= 11.2:
                px[x, y] = (GOLD[3] if v > 0.5 else GOLD[2] if v > -0.1 else GOLD[1]) + (255,)
            elif d < 9.2:
                px[x, y] = (26, 14, 10, 255)
            ang = math.atan2(dy, dx)
            if 11.2 < d <= 14.5 and abs(((ang + math.pi / 5) % (2 * math.pi / 5)) - math.pi / 5) < 0.09 * (15 - d) / 3:
                px[x, y] = GOLD[1] + (255,)
    # a burning seed: flame body
    for y in range(FR):
        for x in range(FR):
            dx, dy = x + 0.5 - c, y + 0.5 - (c + 2)
            t = -dy / 8 + 0.5
            if -7.5 <= dy <= 3.5:
                w = 4.2 * (1 - max(0, -dy) / 8) ** 0.8 if dy < 0 else math.sqrt(max(0, 12.25 - dy * dy)) * 1.2
                if abs(dx + 0.6 * math.sin(dy * 0.5)) <= w:
                    k = abs(dx) / max(w, 0.1)
                    col = EMB[4] if (k < 0.35 and -3 < dy < 2) else EMB[3] if k < 0.6 and dy > -5 else EMB[2] if k < 0.85 else EMB[1]
                    px[x, y] = col + (255,)
    a = im.getchannel('A')
    for y in range(FR):
        for x in range(FR):
            if not a.getpixel((x, y)) and any(0 <= x + dx < FR and 0 <= y + dy < FR and a.getpixel((x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (8, 7, 12, 255)
    return im


def dim(body):
    """Locked twin: desaturated, sunk toward a cold dark stone."""
    out = Image.new("RGBA", body.size, (0, 0, 0, 0))
    for y in range(body.height):
        for x in range(body.width):
            r, g, b, a = body.getpixel((x, y))
            if not a:
                continue
            L = 0.3 * r + 0.59 * g + 0.11 * b
            out.putpixel((x, y), (int(16 + L * 0.36), int(14 + L * 0.34), int(18 + L * 0.36), a))
    return out


def main():
    frames, dframes, tags, dtags, comps = [], [], [], [], []
    for i, nid in enumerate(ORDER):
        body, out = draw(nid).images()
        frames.append({"ms": 100, "cels": {"Outline": out, "Icon": body}})
        dframes.append({"ms": 100, "cels": {"Outline": out, "Icon": dim(body)}})
        tags.append(("sk_" + nid, i, i)); dtags.append(("skd_" + nid, i, i))
        c = out.copy(); c.alpha_composite(body); comps.append((nid, c))
    kinds = [(k, l) for k in 'nfkm' for l in (0, 1, 2)]
    fimgs = [frame_img(k, l) for k, l in kinds] + [core_img()]
    ftags = [f"{k}{l}" for k, l in kinds] + ["core"]
    if "--preview-only" not in sys.argv:
        asebuild.build("sk_icons", S, S, ["Outline", "Icon"], frames, tags)
        asebuild.build("sk_icons_dim", S, S, ["Outline", "Icon"], dframes, dtags)
        asebuild.build("sk_frames", FR, FR, ["Frame"], [{"ms": 100, "cels": {"Frame": im}} for im in fimgs], [(t, i, i) for i, t in enumerate(ftags)])
    # preview: every icon at 4x inside its learned frame, plus the locked twin, plus the frame set
    Z, cols = 4, 12
    rows = (len(comps) + cols - 1) // cols
    cw, ch = 34 * Z, 40 * Z
    sheet = Image.new("RGBA", (cols * cw, rows * ch + FR * Z + 20), (40, 34, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, (nid, c) in enumerate(comps):
        k = 'k' if nid in ('relentless', 'spellblade', 'shadowstep', 'crimson_pact', 'kindled') else ('m' if nid.startswith('m_') else 'n')
        cell = Image.new("RGBA", (34, 32), (0, 0, 0, 0))
        cell.alpha_composite(frame_img(k, 2), (0, 0)); cell.alpha_composite(c, (8, 8))
        small = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); small.alpha_composite(dim(c))
        x, y = (i % cols) * cw, (i // cols) * ch
        sheet.alpha_composite(cell.resize((34 * Z, 32 * Z), Image.NEAREST), (x, y))
        sheet.alpha_composite(small.resize((16 * 2, 16 * 2), Image.NEAREST), (x + 30 * Z - 8, y + 2))
        d.text((x + 4, y + 32 * Z + 2), nid, fill=(255, 255, 255, 255))
    for i, im in enumerate(fimgs):
        sheet.alpha_composite(im.resize((FR * Z, FR * Z), Image.NEAREST), (i * (FR * Z + 4), rows * ch + 10))
    pdir = os.path.join(HERE, "previews"); os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "skills.png"))
    # a 1x strip too, to judge readability at game size
    strip = Image.new("RGBA", (len(comps) * 18 + 2, 20), (20, 18, 26, 255))
    for i, (_, c) in enumerate(comps):
        strip.alpha_composite(c, (2 + i * 18, 2))
    strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST).save(os.path.join(pdir, "skills_1x.png"))
    print("sk_icons:", len(frames), "icons;", len(fimgs), "frames")


if __name__ == "__main__":
    main()
