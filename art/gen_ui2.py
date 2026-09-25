#!/usr/bin/env python3
"""UI icons v2 (ART_SPEC2 section B) -> art/ui_icons2.aseprite + assets/ui_icons2.png/.json
                                      art/ui_panel.aseprite  + assets/ui_panel.png/.json

ui_icons2: 16x16 frames, ONE tag per icon, one frame each (order = ICONS below).
ui_panel : 96x64, single tag `panel`: ornate dark panel, gold corner filigree. 9-slice
           friendly: all ornament lives inside the 8px corners; every edge row/column
           between the corners is constant, and the centre is a flat fill.

Same house style as gen_ui.py (and reuses its Icon grid + palette): one strong silhouette
per icon, lit from the upper-left, auto 1px near-black outline on its own layer.
Weapons are drawn on the 45-degree diagonal (hilt bottom-left, tip top-right) with
`dband`, which rasterises a band in diagonal coordinates (d = x - y along the blade,
s = x + y across it) -> clean pixel staircases at any width.
Re-runnable: python3 art/gen_ui2.py
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
import gen_ui  # noqa: E402

S = 16
PAL = dict(gen_ui.PAL)
PAL.update({
    # rot green
    'n': (26, 46, 26), 'N': (56, 100, 40), 'o': (118, 166, 54), 'O': (194, 226, 112),
    # violet (sorcery / scholar)
    'i': (46, 22, 80), 'I': (100, 54, 158), 'j': (168, 118, 228), 'J': (226, 200, 255),
    # teal (Kalden)
    'd': (14, 52, 60), 'D': (30, 110, 116), 'q': (70, 180, 168), 'Q': (164, 238, 222),
    # ember orange
    'f': (122, 34, 16), 'F': (200, 70, 26), 'h': (244, 128, 40),
    # rusted iron
    'x': (70, 42, 34), 'X': (116, 70, 46), 'z': (160, 104, 64),
    # leather / wood
    'l': (52, 34, 26), 'L': (98, 66, 42), 'w': (140, 98, 60),
    # v6 boss remembrances: ash bone, black steel, pale root, white-gold glow
    'H': (218, 212, 198), 'M': (156, 150, 142), 'T': (96, 90, 92),
    'k': (30, 23, 31), 'C': (72, 58, 58), '6': (122, 102, 92),
    'p': (236, 228, 206), 'U': (168, 156, 130), 'E': (255, 244, 196),
})


class Icon(gen_ui.Icon):
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

    def dband(self, d0, d1, lo, hi, fn):
        """Band along the up-right diagonal. d = x - y (along), s = x + y (across, low s =
        upper-left = lit side). lo/hi: s bounds (numbers or f(d)). fn(k, n, d) -> colour,
        k = s - lo, n = hi - lo."""
        for y in range(S):
            for x in range(S):
                d, s = x - y, x + y
                if not d0 <= d <= d1:
                    continue
                l = lo(d) if callable(lo) else lo
                h = hi(d) if callable(hi) else hi
                if l <= s <= h:
                    c = fn(s - l, h - l, d) if callable(fn) else fn
                    if c:
                        self.g[y][x] = c

    def dpx(self, d, s, c):
        if (d + s) % 2 == 0:
            self.px((d + s) // 2, (s - d) // 2, c)


def ramp3(lit, mid, dark, edge=None):
    """Band colouring across its width: lit upper-left edge, mid body, dark lower-right."""
    def f(k, n, d):
        if n == 0:
            return mid
        if k == 0:
            return lit
        if k == n:
            return dark
        return edge if (edge and k == 1 and n >= 3) else mid
    return f


def taper(lo, hi, d_start, d_tip, keep_lo=False):
    """Bounds that narrow linearly to a point at d_tip."""
    def fl(d):
        if d <= d_start:
            return lo
        t = (d - d_start) / max(1, d_tip - d_start)
        mid = (lo + hi) / 2
        return lo if keep_lo else math.floor(lo + (mid - lo) * t + 0.5)

    def fh(d):
        if d <= d_start:
            return hi
        t = (d - d_start) / max(1, d_tip - d_start)
        mid = (lo + hi) / 2
        return math.floor(hi - (hi - (lo if keep_lo else mid)) * t + 0.5)
    return fl, fh


sparkle = gen_ui.sparkle


# ================================================================ weapons
def w_longsword():
    ic = Icon()
    lo, hi = taper(14, 16, 8, 13)
    ic.dband(-4, 13, lo, hi, ramp3('5', '4', '2'))
    ic.dband(-4, 9, 15, 15, '3')                     # fuller
    ic.dpx(13, 15, 'W')
    ic.dband(-6, -5, 10, 20, lambda k, n, d: 'y' if k < 3 else ('G' if k < n - 1 else 'g'))
    ic.dband(-10, -7, 15, 16, lambda k, n, d: 't' if (d + k) % 3 else 'l')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'Y' if k == 0 else ('y' if k < 2 else 'G'))
    return ic


def w_dagger():
    ic = Icon()
    # short, curved: the blade bows toward the upper-left as it nears the tip
    def lo(d):
        t = max(0.0, (d + 1) / 9)
        return 15 - round(2.4 * t * t) - (1 if d >= 7 else 0)

    def hi(d):
        t = max(0.0, (d + 1) / 9)
        return 16 - round(2.4 * t * t) - (1 if d >= 6 else 0) - (1 if d >= 8 else 0)
    ic.dband(-1, 8, lo, hi, ramp3('5', '4', '2'))
    ic.dband(-3, -2, 12, 19, lambda k, n, d: 'y' if k < 2 else ('G' if k < n else 'g'))
    ic.dband(-8, -4, 15, 16, lambda k, n, d: 'v' if k == 0 else ('u' if d % 3 else 't'))
    ic.dband(-10, -9, 14, 17, lambda k, n, d: 'v' if k < 2 else 'u')
    return ic


def w_greatsword():
    ic = Icon()
    # huge slab of pitted iron eaten by rust, blunt chamfered tip, gold runes down the fuller
    def lo(d):
        return 13 + (1 if d >= 12 else 0)

    def hi(d):
        return 17 - (1 if d >= 12 else 0) - (1 if d >= 13 else 0)

    def col(k, n, d):
        rust = (d * 7 + k * 3) % 11 < 3 and k >= 2
        if k == 0:
            return '5'
        if k == 1:
            return 'X' if (d * 5) % 9 == 0 else '4'
        if k == n:
            return 'x' if d % 3 == 0 else '2'
        return 'X' if rust else '3'
    ic.dband(-3, 13, lo, hi, col)
    ic.dband(-2, 10, 15, 15, '2')
    for d in (-1, 2, 5, 8):
        ic.dpx(d, 15, 'Y' if d < 4 else 'y')
    ic.dband(-5, -4, 9, 21, lambda k, n, d: '5' if k < 2 else ('4' if k < n - 2 else ('3' if k < n else '2')))
    ic.dband(-10, -6, 15, 16, lambda k, n, d: 'L' if k == 0 else 'l')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: '4' if k < 2 else '2')
    return ic


def w_spear():
    ic = Icon()
    # long ash-wood shaft corner to corner, leaf-shaped steel head
    ic.dband(-13, 3, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -12, 15, 16, '3')
    ic.dband(2, 3, 14, 17, lambda k, n, d: 'y' if k < 2 else 'G')
    widths = {4: (15, 16), 5: (14, 17), 6: (13, 17), 7: (13, 17), 8: (14, 17), 9: (14, 16), 10: (15, 16),
              11: (15, 16), 12: (15, 15), 13: (15, 15)}
    ic.dband(4, 13, lambda d: widths[d][0], lambda d: widths[d][1], ramp3('5', '4', '2'))
    ic.dband(5, 11, 15, 15, '3')
    ic.dpx(13, 15, 'W')
    return ic


def w_katana():
    ic = Icon()
    # slender, gently curved blade: steel spine, pale moonlight-blue cutting edge
    def lo(d):
        t = (d + 3) / 16
        return 15 - round(1.3 * math.sin(math.pi * min(1.0, t) * 0.85)) + (1 if d >= 12 else 0)

    def hi(d):
        return lo(d) + (0 if d >= 12 else 1)
    ic.dband(-3, 13, lo, hi, lambda k, n, d: 'c' if n == 0 else ('4' if k == 0 else 'c'))
    ic.dband(-3, 10, lambda d: hi(d), lambda d: hi(d), lambda k, n, d: 'A' if d < 2 else 'c')
    ic.dpx(13, lo(13), 'W')
    ic.dband(-3, -3, 14, 16, 'y')                     # habaki collar
    ic.dband(-5, -4, 12, 18, lambda k, n, d: 'y' if k == 0 else ('G' if k in (1, n) else '2'))
    ic.dband(-11, -6, 15, 16, lambda k, n, d: 'v' if (d + k) % 3 == 0 else '2')
    ic.dband(-12, -12, 15, 16, 'G')
    return ic


def w_maul():
    ic = Icon()
    # wooden haft into a heavy iron block whose seams glow ember-orange
    ic.dband(-13, 0, 15, 16, lambda k, n, d: 'w' if k == 0 else 'L')
    ic.dband(-13, -12, 15, 16, '2')
    ic.dband(-6, -5, 15, 16, 'l')
    ic.rows(7, 1, [
        ".4444443",
        "45555443",
        "4544hh32",
        "44hFYhF2",
        "3hF32h22",
        "33333222",
        ".333222.",
    ])
    ic.rows(6, 3, ["3", "3"])
    return ic


def w_oathbrand():
    ic = Icon()
    # holy straight sword: white-gold blade with a glowing core line, swept-wing gold guard
    lo, hi = taper(14, 16, 8, 13)
    ic.dband(-4, 13, lo, hi, ramp3('W', 'Y', 'y'))
    ic.dband(-4, 10, 15, 15, 'W')
    ic.dpx(13, 15, 'W')
    # winged guard: the tips sweep toward the blade
    ic.dband(-6, -5, 11, 19, lambda k, n, d: 'Y' if k < 2 else ('y' if k < n - 1 else 'G'))
    for (d, s) in ((-4, 10), (-3, 9), (-4, 20), (-3, 21)):
        ic.dpx(d, s, 'y')
    ic.dband(-10, -7, 15, 16, lambda k, n, d: 'v' if k == 0 else 'u')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'c' if k < 2 else 'A')
    ic.px(12, 6, 'Y'); ic.px(4, 4, 'Y'); ic.px(13, 9, 'y')
    return ic


def w_kalden():
    ic = Icon()
    # black greatsword, pale edge, teal fuller inlaid with gold filigree
    lo, hi = taper(13, 16, 9, 13)
    ic.dband(-4, 13, lo, hi, lambda k, n, d: '4' if k == 0 else ('2' if k < n else '1'))
    ic.dband(-3, 9, 15, 15, 'D')
    for d in (-1, 3, 7):
        ic.dpx(d, 15, 'q')
    for d in (1, 5, 9):
        ic.dpx(d, 15, 'y')
    ic.dpx(13, 15, '5')
    ic.dband(-6, -5, 10, 20, lambda k, n, d: 'q' if k < 2 else ('D' if k < n - 1 else 'd'))
    ic.dpx(-5, 15, 'y'); ic.dpx(-6, 10, 'y'); ic.dpx(-6, 20, 'G')
    ic.dband(-10, -7, 15, 16, lambda k, n, d: 'd' if (d + k) % 2 else '1')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'y' if k < 2 else 'G')
    return ic


# ---- v6: boss remembrance weapons (appended after every existing icon)
def w_gravetusk():
    ic = Icon()
    # huge curved ash-bone tusk, bound in glowing golden roots; root-knot guard, root-wrapped grip
    def lo(d):
        t = max(0.0, (d + 3) / 16)
        return 14 - round(3.2 * t * t) + (1 if d >= 11 else 0) + (1 if d >= 13 else 0)

    def hi(d):
        t = max(0.0, (d + 3) / 16)
        return 18 - round(3.2 * t * t) - (1 if d >= 9 else 0) - (1 if d >= 11 else 0) - (1 if d >= 12 else 0)

    def col(k, n, d):
        if d - k // 2 in (0, 5):
            return 'Y' if k < n - 1 else 'y'           # root bindings winding round the tusk
        if k == 0:
            return 'H'
        if k == n:
            return 'T'
        return 'H' if k == 1 else 'M'
    ic.dband(-3, 13, lo, hi, col)
    ic.dpx(13, lo(13) + (lo(13) + 13) % 2, 'W')
    ic.dband(-5, -4, 11, 19, lambda k, n, d: 'Y' if 3 <= k <= n - 3 else ('L' if k < 3 else 'l'))
    ic.dpx(-3, 10, 'y'); ic.dpx(-3, 20, 'G')          # tendrils hooked up the tusk
    ic.dband(-10, -6, 15, 16, lambda k, n, d: 'y' if (d + k) % 3 == 0 else ('L' if k == 0 else 'l'))
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'Y' if 1 <= k <= 2 else ('H' if k == 0 else 'M'))
    ic.px(13, 7, 'y')
    return ic


def w_omen():
    ic = Icon()
    # Morvain's curved black-steel sword: serrated gold edge (upper-left, convex) breathing embers
    def lo(d):
        t = (d + 3) / 16
        return 14 - round(1.8 * math.sin(math.pi * min(1.0, t) * 0.8)) + (1 if d >= 11 else 0) + (1 if d >= 12 else 0)

    def hi(d):
        return lo(d) + (3 if d < 10 else (2 if d < 12 else 0))

    def col(k, n, d):
        if k == 0:
            return 'Y' if d >= 9 else 'y'             # gold edge
        if k == 1:
            return 'h' if d % 3 == 0 and 0 <= d <= 9 else '6'
        return 'k' if (k == n and d % 2) else 'C'
    ic.dband(-3, 13, lo, hi, col)
    for d in (0, 3, 6, 9):                            # serrations: gold teeth, white-hot tips
        ic.dpx(d, lo(d) - 1 - ((lo(d) - 1 + d) % 2), 'E' if d == 6 else 'Y')
    ic.dpx(13, lo(13) + (lo(13) + 13) % 2, 'E')
    ic.dband(-5, -4, 11, 19, lambda k, n, d: 'h' if 3 <= k <= n - 3 else ('y' if k < 3 else 'G'))
    for (d, s) in ((-3, 10), (-2, 9), (-3, 20), (-2, 21)):   # swept wings
        ic.dpx(d, s, 'y' if s < 15 else 'G')
    ic.dband(-10, -6, 15, 16, lambda k, n, d: 'r' if (d + k) % 2 else 'm')
    ic.dband(-12, -11, 14, 17, lambda k, n, d: 'h' if 1 <= k <= 2 else ('y' if k == 0 else 'G'))
    return ic


def w_rotmaw():
    ic = Icon()
    # crude cleaver: femur haft, a slab of rusted iron with a bone ridge, glowing pustules, green drips
    ic.dband(-13, 1, 15, 16, lambda k, n, d: 'N' if d % 4 == 0 else ('v' if k == 0 else 'u'))
    ic.dband(-13, -12, 14, 17, lambda k, n, d: 'v' if k < 2 else 'u')
    ic.dband(2, 3, 14, 18, lambda k, n, d: 'z' if k < 2 else 'x')          # rusted collar

    def hi(d):
        return min(23, 17 + (d - 3) * 2) - (1 if d >= 12 else 0)

    def col(k, n, d):
        if k == 0:
            return 'v' if d % 3 else 'u'              # vertebra ridge along the spine
        if k == n:
            return 'o' if d % 4 == 1 else 'M'         # crude edge weeping rot
        if k == n - 1:
            return 's'
        if (d * 2 + k) % 7 == 0:
            return 'X'                                # rust bloom
        return 'S'
    ic.dband(4, 13, 13, hi, col)
    ic.rows(11, 4, [".h.", "hYh", ".hF"])            # glowing pustules
    ic.px(14, 2, 'h')
    for d in (5, 8, 11):                              # drips off the edge
        s = hi(d) + (1 if (d + hi(d)) % 2 else 0)
        x, y = (d + s) // 2, (s - d) // 2
        if ic.get(x, y + 1) is None:
            ic.px(x, y + 1, 'o')
            if d != 8:
                ic.px(x, y + 2, 'O')
    return ic


def w_scepter():
    ic = Icon()
    # pale branching root shaft, luminous gold leaf-blade, a small halo ring below the head
    ic.dband(-12, 4, 15, 16, lambda k, n, d: 'p' if k == 0 else 'U')
    for (d, s) in ((-13, 13), (-14, 12), (-13, 18), (-14, 19), (-7, 17), (-8, 18), (0, 13), (-1, 12)):
        ic.dpx(d, s, 'p' if s < 15 else 'U')          # root foot + twig nubs
    ic.dband(-4, -3, 15, 16, 'y')                     # gold binding
    # halo: an oblique ring round the shaft
    for (d, s) in ((1, 11), (1, 19), (2, 10), (2, 20), (3, 10), (3, 20), (4, 11), (4, 19),
                   (2, 12), (3, 12), (2, 18), (3, 18)):
        ic.dpx(d, s, 'E' if s < 15 else 'y')
    ic.dpx(5, 13, 'p'); ic.dpx(5, 17, 'U'); ic.dpx(6, 12, 'p'); ic.dpx(6, 18, 'U')   # prongs
    widths = {6: (14, 16), 7: (13, 17), 8: (13, 17), 9: (13, 17), 10: (14, 16), 11: (14, 16),
              12: (15, 15), 13: (15, 15)}
    ic.dband(6, 13, lambda d: widths[d][0], lambda d: widths[d][1], ramp3('E', 'Y', 'y'))
    ic.dband(7, 11, 15, 15, 'W')
    ic.dpx(13, 15, 'W')
    ic.px(14, 1, 'Y'); ic.px(10, 2, 'y')
    return ic


# ================================================================ weapon arts
def crescent_band(ic, cx, cy, r, a0, a1, thick, cols):
    """Moon-crescent arc: fattest at the middle, sharp at both ends. cols = (edge, body, inner)."""
    n = 90
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        th = thick * math.sin(math.pi * t) ** 0.8
        for k in range(int(th * 2) + 1):
            rr = r - k * 0.5
            c = cols[0] if k < 2 else (cols[1] if k < th * 2 - 1 else cols[2])
            ic.px(cx + math.cos(a) * rr, cy - math.sin(a) * rr, c)


def a_crescent():
    ic = Icon()
    # a great silver crescent cut sweeping over the top, a glint at its leading tip
    crescent_band(ic, 8, 10, 6.8, 200, -20, 3.4, ('W', '5', '4'))
    sparkle(ic, 13, 12, big=False)
    ic.px(2, 13, '4'); ic.px(1, 14, '3')
    return ic


def a_stormleap():
    ic = Icon()
    # twin chevrons of wind launching upward out of a ring of ash
    ic.rows(0, 0, [
        ".......WW.......",
        "......WccW......",
        ".....WcAAcW.....",
        "....WcA..AcW....",
        "...WcA.WW.AcW...",
        "...cA.WccW.Ac...",
        "...A.WcAAcW.A...",
        "....WcA..AcW....",
        "...WcA....AcW...",
        "...cA......Ac...",
        "...A........A...",
        "................",
        "...s55555555s...",
        ".sS4........4Ss.",
        "..s33333333333s.",
        "................",
    ])
    ic.px(1, 11, 's'); ic.px(14, 11, 's'); ic.px(0, 13, 'S'); ic.px(15, 13, 'S')
    return ic


def a_bloodstep():
    ic = Icon()
    # a crimson blood-drop hurtling right, trailing afterimage streaks
    ic.ell(10.5, 8, 4.2, 4.2, lambda nx, ny: 'P' if (nx + ny) < -0.8 else ('R' if (nx + ny) < 0.5 else 'r'))
    ic.poly([(1, 8), (9.5, 4.0), (9.5, 12.0)], lambda x, y: 'R' if y < 8 else ('r' if y < 10 else 'm'))
    ic.line(3, 7, 8, 5, 'P')
    for (y, x0, x1) in ((3, 3, 7), (13, 2, 7), (2, 0, 2), (14, 0, 2)):
        ic.line(x0, y, x1, y, 'r')
    ic.px(9, 6, 'W'); ic.px(10, 5, 'P')
    return ic


def flame_tongue(ic, bx, by, h, w, phase, ramp):
    """ramp = (hot, mid, cool, tip)."""
    for i in range(h):
        t = i / h
        hw = w * (1 - t) ** 0.8
        for x in range(int(bx - 3), int(bx + 4)):
            d = abs(x + 0.5 - bx - 0.6 * math.sin(t * 3.5 + phase))
            if d <= hw:
                c = ramp[0] if (t < 0.3 and d < hw * 0.5) else (ramp[1] if t < 0.55 else (ramp[2] if t < 0.8 else ramp[3]))
                ic.px(x, by - i, c)


def a_cinderblade():
    ic = Icon()
    # diagonal sword wreathed in licking ember fire
    for (bx, by, h, w, ph) in ((4.5, 12, 6, 1.6, 0.3), (7.5, 9, 7, 1.7, 1.2), (10.5, 6, 6, 1.6, 2.0),
                               (13, 3.5, 4, 1.2, 0.5), (2.5, 14, 4, 1.2, 1.0)):
        flame_tongue(ic, bx, by, h, w, ph, ('Y', 'h', 'F', 'f'))
    lo, hi = taper(14, 15, 9, 13)
    ic.dband(-4, 13, lo, hi, ramp3('W', 'Y', 'Y'))
    ic.dband(-6, -5, 11, 19, lambda k, n, d: 'y' if k < 2 else 'G')
    ic.dband(-10, -7, 15, 16, 'l')
    ic.dband(-12, -11, 14, 17, 'y')
    return ic


def a_warcry():
    ic = Icon()
    # a roaring great-helm, its visor blazing, golden shout rings bursting out both sides
    for (r, c) in ((6.2, 'y'), (7.8, 'G')):
        for i in range(60):
            a = math.radians(-48 + 96 * i / 59)
            ic.px(8 + math.cos(a) * r, 8 - math.sin(a) * r, c)
            ic.px(7 - math.cos(a) * r, 8 - math.sin(a) * r, c)
    ic.rows(4, 2, [
        "..5554..",
        ".554443.",
        "55444332",
        "5YYYYYY2",
        "54yWWy32",
        "4433y322",
        "443.y.22",
        "43332222",
        "GyyyGGGg",
        ".g....g.",
    ])
    ic.px(7, 9, '3'); ic.px(9, 9, '2')
    return ic


def a_moonwave():
    ic = Icon()
    # pale-blue crescent wave rushing right, motion streaks trailing behind
    crescent_band(ic, 6, 8, 7.2, 80, -80, 3.6, ('W', 'c', 'A'))
    for (y, x0, x1) in ((4, 1, 5), (8, 0, 6), (12, 1, 5)):
        ic.line(x0, y, x1, y, 'a')
        ic.px(x1, y, 'A')
    sparkle(ic, 2, 1, c='W', c2='c')
    return ic


# ================================================================ charms
def chain(ic, pts, c1='y', c2='G'):
    for i, (x, y) in enumerate(pts):
        ic.px(x, y, c1 if i % 2 == 0 else c2)


def gem(ic, cx, cy, rx, ry, ramp):
    """Faceted round gem. ramp = (glint, lit, mid, dark)."""
    ic.ell(cx, cy, rx, ry, lambda nx, ny: ramp[1] if (nx + ny) < -0.5 else (ramp[2] if (nx + ny) < 0.6 else ramp[3]))
    ic.px(cx - rx * 0.45, cy - ry * 0.45, ramp[0])


def necklace(ic, cx, y_top, y_bot, rx, c1, c2):
    """Chain loop behind the pendant: upper arc of an ellipse, alternating link colours."""
    ry = y_bot - y_top
    pts = []
    for i in range(40):
        a = math.pi * i / 39
        p = (round(cx + math.cos(a) * rx), round(y_bot - math.sin(a) * ry))
        if p not in pts:
            pts.append(p)
    for i, (x, y) in enumerate(pts):
        ic.px(x, y, c1 if (i // 1) % 2 == 0 else c2)


def c_crimson():
    ic = Icon()
    # gold chain amulet holding a teardrop ruby
    necklace(ic, 7.5, 0, 6, 5.2, 'y', 'G')
    ic.rect(7, 5, 8, 6, 'y'); ic.px(7, 5, 'Y')
    ic.poly([(7.5, 6), (11.5, 11), (11.5, 12), (9.5, 15), (5.5, 15), (3.5, 12), (3.5, 11)],
            lambda x, y: 'P' if (x < 7 and y < 11) else ('R' if x + y < 18 else ('r' if x + y < 22 else 'm')))
    ic.px(6, 10, 'W'); ic.px(5, 11, 'P')
    return ic


def c_azure():
    ic = Icon()
    # round sapphire in a pronged silver star setting, a small silver bail on top
    ic.ell(8, 1.8, 1.8, 1.6, lambda nx, ny: None if nx * nx + ny * ny < 0.25 else '5')
    for a in range(0, 360, 45):
        r = 6.8 if a % 90 == 0 else 6.2
        x, y = 8 + math.cos(math.radians(a)) * r, 9 - math.sin(math.radians(a)) * r
        ic.line(8 + math.cos(math.radians(a)) * 4, 9 - math.sin(math.radians(a)) * 4, x, y,
                '5' if a in (90, 135, 180) else ('4' if a in (45, 225) else '3'))
    ic.ell(8, 9, 4.8, 4.8, lambda nx, ny: '5' if (nx + ny) < -0.7 else ('4' if (nx + ny) < 0.6 else '3'))
    gem(ic, 8, 9, 3.6, 3.6, ('W', 'c', 'A', 'a'))
    ic.px(10, 11, 'b'); ic.px(9, 12, 'b'); ic.px(6, 7, 'c')
    return ic


def c_horn():
    ic = Icon()
    # a gold-banded war horn of dark polished horn: sharp tip bottom-left, sweeping up to a
    # gold-rimmed bell mouth at the top-right
    P0, P1, P2 = (1.5, 13.5), (11.5, 13.5), (11.5, 4.5)
    def bez(t):
        return ((1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0],
                (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1])
    n = 80
    for i in range(n):
        t = i / (n - 1)
        x, y = bez(t)
        w = 0.3 + 2.0 * t ** 1.5
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= w * w:
                    band = 0.44 < t < 0.52 or 0.76 < t < 0.83
                    lit = (dx + dy) < -0.4
                    tipc = t < 0.3
                    c = ('Y' if lit else 'y') if band else (('z' if lit else ('w' if (dx + dy) < 1.0 else 'L'))
                                                          if not tipc else ('w' if lit else 'l'))
                    ic.px(x + dx, y + dy, c)
    ic.ell(11.5, 3.4, 3.5, 2.0, lambda nx, ny: 'l' if nx * nx + ny * ny < 0.4 else ('y' if ny < 0.2 else 'G'))
    ic.px(10, 2, 'x')
    return ic


def c_fang():
    ic = Icon()
    # a great curved fang capped in gold, hung on a leather cord, blood at the tip
    ic.rows(0, 0, [
        "....l......l....",
        ".....l....l.....",
        "......l..l......",
        "......GyyG......",
        "......vvvut.....",
        "......vvvut.....",
        ".....vvvvut.....",
        ".....vvvut......",
        ".....vvvut......",
        "....vvvut.......",
        "....vvut........",
        "...vvut.........",
        "...vut..........",
        "..vut...........",
        "..Rr............",
        ".R..............",
    ])
    ic.px(6, 4, 'W'); ic.px(9, 3, 'G')
    return ic


def c_ember():
    ic = Icon()
    # gold ring crowned by a glowing ember stone
    ic.ell(8, 11, 5, 3.4, lambda nx, ny: None if nx * nx + ny * ny < 0.4 else
           ('Y' if (nx + ny) < -0.4 else ('y' if (nx + ny) < 0.6 else 'G')))
    ic.rect(5, 6, 10, 7, 'G'); ic.px(5, 6, 'y')
    ic.ell(7.5, 4.2, 3.3, 3.2, lambda nx, ny: 'Y' if (nx + ny) < -0.7 else ('h' if (nx + ny) < 0.3 else 'F'))
    ic.px(6, 3, 'W')
    ic.px(12, 1, 'h'); ic.px(3, 1, 'F'); ic.px(13, 4, 'Y')
    return ic


def c_heel():
    ic = Icon()
    # a knight's spur: steel heel band (open toward the toes) and a spiked gold rowel
    ic.ell(5.5, 8.5, 4.6, 4.4, lambda nx, ny: None if (nx * nx + ny * ny < 0.38 or nx < -0.5) else
           ('5' if ny < -0.25 else ('4' if ny < 0.45 else '3')))
    ic.rect(10, 8, 11, 9, '4'); ic.px(10, 9, '3'); ic.px(11, 9, '3')
    for a in range(0, 360, 45):
        r = 2.6 if a % 90 == 0 else 2.0
        ic.px(13 + math.cos(math.radians(a)) * r, 8.5 - math.sin(math.radians(a)) * r,
              'Y' if (a in (90, 135, 180)) else 'y')
    ic.rect(12, 8, 13, 9, 'G'); ic.px(12, 8, 'Y')
    ic.px(1, 5, '5'); ic.px(1, 12, '3')
    return ic


def c_crest():
    ic = Icon()
    # heraldic crest: gold-rimmed heater shield, deep teal field, the white-gold Pale Root
    ic.poly([(2, 1), (13, 1), (13, 8), (8, 14), (7, 14), (2, 8)], 'G')
    ic.poly([(3, 2), (12, 2), (12, 8), (8, 12), (7, 12), (3, 8)],
            lambda x, y: 'q' if (x < 5 and y < 6) else ('D' if x < 9 else 'd'))
    ic.line(2, 1, 13, 1, 'y'); ic.line(2, 1, 2, 8, 'y')
    ic.rows(4, 3, [
        "..YWY..",
        ".YWWWY.",
        "Y.YWY.y",
        "...W...",
        "..yWy..",
        ".y.y.y.",
    ])
    return ic


def c_scholar():
    ic = Icon()
    # violet eye-medallion in a bronze rim, hung from a small bail
    ic.ell(8, 1.8, 1.8, 1.6, lambda nx, ny: None if nx * nx + ny * ny < 0.25 else 'y')
    ic.ell(8, 8.5, 5.8, 5.8, lambda nx, ny: 'y' if (nx + ny) < -0.6 else ('G' if (nx + ny) < 0.7 else 'g'))
    ic.ell(8, 8.5, 4.4, 4.4, lambda nx, ny: 'j' if (nx + ny) < -0.6 else ('I' if (nx + ny) < 0.5 else 'i'))
    ic.rows(4, 7, [
        "..JJJJ..",
        ".J.iiWJ.",
        "..JJJJ..",
    ])
    ic.px(7, 8, 'i')
    ic.px(5, 5, 'J')
    return ic


def c_greed():
    ic = Icon()
    # heavy gold signet ring set with a large emerald, a coin tucked behind
    ic.ell(11.5, 4, 3.4, 3.4, lambda nx, ny: 'G' if nx * nx + ny * ny > 0.55 else ('y' if nx + ny < 0 else 'G'))
    ic.px(11, 3, 'Y')
    ic.ell(7.5, 11, 5.6, 4, lambda nx, ny: None if nx * nx + ny * ny < 0.4 else
           ('Y' if (nx + ny) < -0.5 else ('y' if (nx + ny) < 0.5 else 'G')))
    ic.rect(4, 5, 11, 7, 'G'); ic.px(4, 5, 'y')
    gem(ic, 7.5, 4.5, 3.2, 2.6, ('W', 'O', 'o', 'N'))
    return ic


def c_grace():
    ic = Icon()
    # a radiant grace pendant: white-gold flame-drop in a sunburst
    for a in range(0, 360, 45):
        r0, r1 = 5.2, (7.2 if a % 90 == 0 else 6.4)
        ic.line(8 + math.cos(math.radians(a)) * r0, 8.5 - math.sin(math.radians(a)) * r0,
                8 + math.cos(math.radians(a)) * r1, 8.5 - math.sin(math.radians(a)) * r1, 'y')
    ic.ell(8, 8.5, 4.4, 4.4, lambda nx, ny: 'G' if nx * nx + ny * ny > 0.62 else None)
    ic.poly([(8, 4), (10.8, 9), (10.8, 10), (9.5, 12), (6.5, 12), (5.2, 10), (5.2, 9)],
            lambda x, y: 'W' if (x < 8 and y < 10) else ('Y' if x + y < 19 else 'y'))
    ic.px(8, 0, 'Y')
    return ic


def c_thorn():
    ic = Icon()
    # a circlet of twisted brambles with a single crimson berry-drop
    for i in range(80):
        a = 2 * math.pi * i / 80
        r = 5.2 + 0.7 * math.sin(a * 5)
        x, y = 8 + math.cos(a) * r, 8.5 - math.sin(a) * r
        lit = math.cos(a) * -0.7 + math.sin(a) * 0.7 > 0
        ic.px(x, y, 'o' if lit else 'N')
    for a in range(15, 360, 40):
        rr = math.radians(a)
        x0, y0 = 8 + math.cos(rr) * 5.4, 8.5 - math.sin(rr) * 5.4
        ic.line(x0, y0, x0 + math.cos(rr + 0.6) * 2.4, y0 - math.sin(rr + 0.6) * 2.4, 'w')
    ic.rect(7, 13, 8, 14, 'R'); ic.px(7, 13, 'P'); ic.px(8, 15, 'r')
    return ic


def c_veil():
    ic = Icon()
    # a gossamer veil hanging from a silver ring: soft vertical folds, scalloped hem
    ic.ell(8, 1.8, 1.9, 1.9, lambda nx, ny: None if nx * nx + ny * ny < 0.3 else ('5' if ny < 0 else '4'))
    for y in range(3, 15):
        t = (y - 3) / 11
        half = 1.5 + 5.2 * t ** 0.8
        for x in range(16):
            u = (x + 0.5 - 8) / half
            if abs(u) > 1:
                continue
            hem = 13.3 + 1.1 * math.cos((x + 0.5 - 8) * 1.35)
            if y > hem:
                continue
            f = math.cos(u * 4.2)
            v = f * 0.6 - u * 0.45 + 0.1
            c = 'W' if v > 0.5 else ('c' if v > 0.05 else ('5' if v > -0.45 else '4'))
            ic.px(x, y, c)
    ic.px(8, 3, 'W')
    return ic


def s_shards():
    ic = Icon()
    # a volley of violet-gold crystal shards flying right
    def crys(x, y, L, h):
        ic.poly([(x, y), (x + L - 2, y - h), (x + L, y), (x + L - 2, y + h)],
                lambda px_, py_: 'J' if py_ < y else ('j' if py_ == y else 'I'))
        ic.line(x + 1, y, x + L - 1, y, 'j')
        ic.px(x + L, y, 'W')
        ic.px(x, y, 'y')
    crys(4, 8, 10, 2)
    crys(1, 3, 7, 1)
    crys(2, 13, 7, 1)
    ic.px(0, 8, 'G'); ic.px(1, 8, 'y'); ic.px(2, 8, 'Y')
    return ic


def s_warmth():
    ic = Icon()
    # a golden healing heart glowing with rising motes
    ic.rows(2, 5, [
        ".YYy..yyG.",
        "YWYyyyyyyG",
        "YYyyyyyyyG",
        "yyyyyyyyGG",
        ".yyyyyyGG.",
        "..yyyyGG..",
        "...yyGG...",
        "....GG....",
    ])
    ic.px(3, 6, 'W')
    ic.rows(6, 7, ["..YY", ".YWWY", ".YWWY", "..YY"][:0])
    for (x, y, c) in ((4, 2, 'Y'), (8, 1, 'W'), (12, 3, 'Y'), (7, 3, 'y'), (1, 3, 'y'), (14, 1, 'y')):
        ic.px(x, y, c)
    ic.rect(7, 7, 8, 9, 'Y'); ic.rect(6, 8, 9, 8, 'Y'); ic.px(7, 8, 'W')
    return ic


def s_lance():
    ic = Icon()
    # a frost lance: a long faceted ice spike thrusting up-right, splintered crystal at its
    # back end and a trail of frost motes
    def lo(d):
        return 14 if d < 9 else 14 + (d - 8) // 2

    def hi(d):
        if d < -8:
            return 15
        return 17 if d < 5 else 17 - (d - 4) // 2 - (1 if d >= 12 else 0)
    ic.dband(-10, 13, lo, hi, lambda k, n, d: 'W' if k == 0 else ('c' if k < n - 1 or n < 2 else 'A'))
    ic.dband(-6, 10, 15, 15, 'W')
    ic.dband(-10, -9, 13, 17, lambda k, n, d: 'A' if k in (0, n) else None)
    for (d, s) in ((-12, 12), (-13, 17), (-11, 19), (-8, 11)):
        ic.dpx(d, s, 'c')
    ic.px(2, 9, 'A'); ic.px(6, 14, 'A'); ic.px(0, 12, 'a')
    ic.dpx(13, 15, 'W')
    return ic


def s_rotmist():
    ic = Icon()
    # a low billowing rot-green cloud, a pale skull leering out of it, bubbles rising
    for (cx, cy, r) in ((4.5, 10.5, 3.4), (11.5, 10.5, 3.4), (8, 8.5, 4.2), (2.5, 12.5, 2.2), (13.5, 12.5, 2.2),
                        (8, 12, 3.4)):
        ic.ell(cx, cy, r, r * 0.85, lambda nx, ny: 'O' if (nx + ny) < -0.95 else ('o' if (nx + ny) < 0.2 else 'N'))
    ic.rows(6, 7, [
        ".vvv.",
        "vnvnu",
        "vvuuu",
        ".u.t.",
    ])
    ic.px(4, 3, 'o'); ic.px(12, 2, 'O'); ic.px(11, 4, 'o'); ic.px(3, 1, 'N')
    return ic


def i_emberstone():
    ic = Icon()
    # a charred black stone split by glowing ember cracks
    ic.poly([(4, 3), (10, 2), (14, 6), (13, 12), (8, 14), (3, 12), (2, 7)],
            lambda x, y: 'S' if (x + y) < 9 else ('s' if (x + y) < 17 else '1'))
    ic.line(4, 3, 10, 2, '4')
    for (a, b) in (((5, 5), (8, 8)), ((8, 8), (7, 12)), ((8, 8), (12, 6)), ((12, 6), (13, 9)), ((5, 5), (3, 8))):
        ic.line(*a, *b, 'F')
    ic.px(8, 8, 'Y'); ic.px(7, 9, 'h'); ic.px(9, 8, 'h'); ic.px(6, 6, 'h'); ic.px(11, 7, 'h')
    ic.px(7, 11, 'h')
    return ic


def i_tear():
    ic = Icon()
    # a crystallised tear: pale cyan glowing drop with a white heart
    ic.poly([(8, 1), (13, 9), (13, 11), (11, 14), (5, 14), (3, 11), (3, 9)],
            lambda x, y: 'W' if (x < 7 and 6 < y < 11 and x > 4) else
            ('c' if x + y < 17 else ('A' if x + y < 21 else 'a')))
    ic.line(8, 2, 8, 6, 'c')
    ic.px(5, 8, 'W'); ic.px(6, 7, 'W')
    sparkle(ic, 13, 3, c='W', c2='c')
    return ic


def i_bell():
    ic = Icon()
    # a bronze bell with a hanging clapper
    ic.rect(7, 1, 8, 2, 'G'); ic.px(7, 1, 'y')
    ic.poly([(5, 3), (10, 3), (11, 6), (12, 11), (14, 12), (14, 13), (1, 13), (1, 12), (3, 11), (4, 6)],
            lambda x, y: 'Y' if (x < 6 and y < 9) else ('y' if x < 8 else ('G' if x < 11 else 'g')))
    ic.line(5, 3, 4, 10, 'Y')
    ic.line(1, 12, 14, 12, 'y'); ic.line(1, 13, 14, 13, 'G')
    ic.px(12, 13, 'g'); ic.px(13, 13, 'g'); ic.px(14, 13, 'g')
    ic.rect(7, 14, 8, 14, '3'); ic.px(7, 14, '4')
    ic.line(5, 9, 11, 9, 'G')
    return ic


def i_letter():
    ic = Icon()
    # a folded parchment letter closed with a crimson wax seal
    ic.rect(1, 4, 14, 12, 'v')
    ic.rect(1, 12, 14, 12, 'u'); ic.rect(14, 4, 14, 12, 'u')
    ic.line(1, 4, 7, 9, 'u'); ic.line(14, 4, 8, 9, 'u')
    ic.line(1, 12, 6, 8, 't'); ic.line(14, 12, 9, 8, 't')
    ic.ell(7.5, 9, 2.4, 2.4, lambda nx, ny: 'P' if (nx + ny) < -0.6 else ('R' if (nx + ny) < 0.5 else 'r'))
    ic.px(7, 9, 'm'); ic.px(8, 9, 'r')
    ic.line(8, 11, 9, 13, 'R'); ic.px(6, 12, 'r')
    return ic


def i_crownkey():
    ic = Icon()
    # white-gold key whose bow is a three-pointed crown set with a pale gem
    ic.rows(1, 0, [
        "Y..Y..y",
        "YY.Y.yG",
        "WYYYyyG",
        "YYcAyyG",
        "yyyyGGg",
    ])
    ic.line(5, 5, 13, 13, 'Y')
    ic.line(6, 5, 13, 12, 'y')
    ic.line(5, 6, 12, 13, 'G')
    ic.rows(9, 11, ["y..", "yG.", ".G."])
    ic.rows(11, 9, ["y.", "yG"])
    ic.px(14, 14, 'G')
    return ic


def i_rotseed():
    ic = Icon()
    # a swollen rot seed: mottled green husk split by a glowing orange seam, a curling sprout
    ic.ell(8, 10, 5, 4.6, lambda nx, ny: 'o' if (nx + ny) < -0.6 else ('N' if (nx + ny) < 0.6 else 'n'))
    for (x, y) in ((5, 10), (11, 8), (10, 13), (6, 13)):
        ic.px(x, y, 'F')
    ic.rows(7, 7, [".Y", "Yh", "Yh", "hF", "hF", ".F"])
    ic.line(8, 5, 8, 3, 'o'); ic.px(9, 2, 'o'); ic.px(10, 2, 'O'); ic.px(10, 1, 'O'); ic.px(7, 3, 'O')
    ic.px(5, 7, 'O')
    return ic


def i_herb():
    ic = Icon()
    # a sprig of healing herb: three pointed leaves on a stem, tied with twine
    ic.line(7, 14, 8, 4, 'N')
    for (x0, y0, x1, y1, lit) in ((8, 3, 8, 0, True), (8, 6, 12, 3, True), (7, 8, 3, 5, True),
                                  (8, 9, 12, 8, False), (7, 11, 3, 10, False)):
        L = math.hypot(x1 - x0, y1 - y0)
        n = int(L * 3)
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            w = 1.6 * math.sin(math.pi * min(1, t * 1.1)) ** 0.7
            px_, py_ = -(y1 - y0) / L, (x1 - x0) / L
            for k in range(-2, 3):
                if abs(k) <= w:
                    ic.px(x + px_ * k * 0.7, y + py_ * k * 0.7, 'O' if k < 0 else 'o')
        ic.line(x0, y0, x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.8, 'N')
    ic.rect(6, 12, 9, 12, 'u'); ic.px(6, 12, 'v')
    ic.px(8, 14, 'N')
    return ic


ICONS = [
    ("w_longsword", w_longsword), ("w_dagger", w_dagger), ("w_greatsword", w_greatsword),
    ("w_spear", w_spear), ("w_katana", w_katana), ("w_maul", w_maul), ("w_oathbrand", w_oathbrand),
    ("w_kalden", w_kalden),
    ("a_crescent", a_crescent), ("a_stormleap", a_stormleap), ("a_bloodstep", a_bloodstep),
    ("a_cinderblade", a_cinderblade), ("a_warcry", a_warcry), ("a_moonwave", a_moonwave),
    ("c_crimson", c_crimson), ("c_azure", c_azure), ("c_horn", c_horn), ("c_fang", c_fang),
    ("c_ember", c_ember), ("c_heel", c_heel), ("c_crest", c_crest), ("c_scholar", c_scholar),
    ("c_greed", c_greed), ("c_grace", c_grace), ("c_thorn", c_thorn), ("c_veil", c_veil),
    ("s_shards", s_shards), ("s_warmth", s_warmth), ("s_lance", s_lance), ("s_rotmist", s_rotmist),
    ("i_emberstone", i_emberstone), ("i_tear", i_tear), ("i_bell", i_bell), ("i_letter", i_letter),
    ("i_crownkey", i_crownkey), ("i_rotseed", i_rotseed), ("i_herb", i_herb),
    # v6: appended so every earlier frame / tag keeps its index
    ("w_gravetusk", w_gravetusk), ("w_omen", w_omen), ("w_rotmaw", w_rotmaw), ("w_scepter", w_scepter),
]


# ================================================================ panel
def panel():
    """96x64 dark panel. Layers: Back (outline, dark band, fill), Gold (rims + corner filigree).
    9-slice friendly: ornament is confined to the 8x8 corners; every row/column of the edges
    between the corners is identical, the centre is one flat colour. Lit from the upper-left
    like the node frame: top/left rims bright, bottom/right rims shadowed."""
    W, H = 96, 64
    # top-left corner (8x8); the other three corners are its mirror images
    CORNER = [
        ".KKKKKKK",
        "KHHHgRRR",
        "KHprgBhB",
        "KHrmggBg",
        "KggggBBB",
        "KRBgBJII",
        "KRhBBISS",
        "KRBgBISF",
    ]
    PROFILE = "KRBBBISF"         # cross-section of an edge, outside -> in
    K = PAL['K'] + (255,)
    col = {
        'B': (18, 15, 22, 255), 'F': (24, 21, 30, 255), 'S': (14, 12, 18, 255),
        'r': PAL['R'] + (255,), 'p': PAL['P'] + (255,), 'm': PAL['r'] + (255,),
    }
    Gd, Gm, Gl, Gh = (PAL['g'] + (255,), PAL['G'] + (255,), PAL['y'] + (255,), PAL['Y'] + (255,))
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gold = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bp, gp = back.load(), gold.load()
    for y in range(H):
        for x in range(W):
            cx, cy = min(x, W - 1 - x), min(y, H - 1 - y)
            if cx < 8 and cy < 8:
                ch = CORNER[cy][cx]
            elif cy < 8:
                ch = PROFILE[cy]
            elif cx < 8:
                ch = PROFILE[cx]
            else:
                ch = 'F'
            top, left = y < H / 2, x < W / 2
            horiz = cy < cx if (cx < 8 and cy < 8) else cy < 8
            lit = (top if horiz else left) if cx != cy else (top or left)
            if ch == '.':
                continue
            if ch == 'K':
                bp[x, y] = K
            elif ch in col:
                bp[x, y] = col[ch]
                if ch in 'rpm':
                    # 2x2 ruby: always lit on its own upper-left pixel, whatever the corner
                    ax = 0 if (cx == 2) == left else 1
                    ay = 0 if (cy == 2) == top else 1
                    bp[x, y] = col['B']
                    gp[x, y] = col[[['p', 'r'], ['r', 'm']][ay][ax]]
            elif ch == 'R':
                bp[x, y] = col['B']
                gp[x, y] = Gm if lit else Gd
            elif ch in 'IJ':
                bp[x, y] = col['B']
                gp[x, y] = Gh if ch == 'J' and top and left else (Gl if lit else Gm)
            elif ch in 'gHh':
                bp[x, y] = col['B']
                if ch == 'H':
                    gp[x, y] = Gh if top else Gl
                elif ch == 'g':
                    gp[x, y] = Gl if top else Gm
                else:
                    gp[x, y] = Gm if top else Gd
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
    asebuild.build("ui_icons2", S, S, ["Outline", "Icon"], frames, tags)

    back, gold = panel()
    asebuild.build("ui_panel", 96, 64, ["Back", "Gold"], [{"ms": 100, "cels": {"Back": back, "Gold": gold}}],
                   [("panel", 0, 0)])
    pn = back.copy()
    pn.alpha_composite(gold)

    fr = Image.open(os.path.join(os.path.dirname(HERE), "assets", "ui_frame.png")).convert("RGBA")

    # preview: top = 1x strip on dark (true size, shown 2x) + panel at 1x/9-slice test;
    #          below = each icon in the node frame at 4x with its name
    Z = 4
    cols = 10
    rows = (len(comps) + cols - 1) // cols
    cw, ch = 28 * Z, 34 * Z
    top_h = 64 * 2 + 20
    sheet = Image.new("RGBA", (cols * cw, top_h + rows * ch), (92, 92, 100, 255))
    d = ImageDraw.Draw(sheet)
    strip = Image.new("RGBA", (19 * 18 + 2, 3 * 18 + 2), (20, 18, 26, 255))
    for i, (_, c) in enumerate(comps):
        strip.alpha_composite(c, (2 + (i % 19) * 18, 2 + (i // 19) * 18))
    sheet.paste(strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST), (0, 0))
    # panel at 2x, plus a 9-sliced 160x48 stretch test at 1x... shown 2x
    px0 = strip.width * 2 + 8
    sheet.alpha_composite(pn.resize((192, 128), Image.NEAREST), (px0, 0))
    ns = nine_slice(pn, 150, 40, 8)
    sheet.alpha_composite(ns.resize((300, 80), Image.NEAREST), (px0 + 200, 0))
    sheet.alpha_composite(ns, (px0 + 200, 90))
    sheet.alpha_composite(pn, (px0 + 360, 90 - 30))
    for i, (name, c) in enumerate(comps):
        cell = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        win = Image.new("RGBA", (16, 16), (28, 24, 34, 255))
        cell.paste(win, (4, 4))
        cell.alpha_composite(fr)
        cell.alpha_composite(c, (4, 4))
        x, y = (i % cols) * cw + 2 * Z, top_h + (i // cols) * ch + 2 * Z
        sheet.alpha_composite(cell.resize((24 * Z, 24 * Z), Image.NEAREST), (x, y))
        d.text((x, y + 24 * Z + 4), name, fill=(255, 255, 255, 255))
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "ui2.png"))
    print("ui_icons2:", len(frames), "icons; ui_panel: 1")


def nine_slice(img, w, h, c):
    W, H = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    def part(x0, y0, x1, y1, dw, dh):
        return img.crop((x0, y0, x1, y1)).resize((dw, dh), Image.NEAREST)
    out.alpha_composite(part(0, 0, c, c, c, c), (0, 0))
    out.alpha_composite(part(W - c, 0, W, c, c, c), (w - c, 0))
    out.alpha_composite(part(0, H - c, c, H, c, c), (0, h - c))
    out.alpha_composite(part(W - c, H - c, W, H, c, c), (w - c, h - c))
    out.alpha_composite(part(c, 0, W - c, c, w - 2 * c, c), (c, 0))
    out.alpha_composite(part(c, H - c, W - c, H, w - 2 * c, c), (c, h - c))
    out.alpha_composite(part(0, c, c, H - c, c, h - 2 * c), (0, c))
    out.alpha_composite(part(W - c, c, W, H - c, c, h - 2 * c), (w - c, c))
    out.alpha_composite(part(c, c, W - c, H - c, w - 2 * c, h - 2 * c), (c, c))
    return out


if __name__ == "__main__":
    main()
