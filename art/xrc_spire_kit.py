"""Shared palette + drawing helpers for the xrc_sp_* props (Stormward Spire expansion), built on the Spire ramps.

Same hand as spire_props.py: 1px K outline, light from the upper-left, 3-5 tone ramps, pixel-clean (alpha 0/255).
"""
import math
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline
from env_props import Spr, flame
from spire_tiles import (ST, SHEEN, GLINT, SALT, SEA, BOLT, AMBER, RUST, VERD, IRON, WOOD, WHEAT, GRASS, BONE, CLOTH,
                         LICHEN, THRIFT)
from spire_props import SLATE, CANVAS, FLAME, GLASS, stone_level, point_in_poly

# tarred planking: near-black with a warm-grey lift, wet sheen comes from SHEEN
TAR = ramp("0b0a0b", "131113", "1b1819", "241f1f", "2e2826", "3a322e", "473d36")
# glass net floats: muted sea-green
GFLOAT = ramp("10201f", "1b3533", "2a4f4a", "3f6d63", "5f8f80")
# kite sailcloth
OCHRE = ramp("211810", "362818", "4e3c20", "68502a", "826636", "9c7c44")
FRED = ramp("1e0e0f", "331617", "4a201f", "632b28", "7a3833", "8e4840")
GBLUE = ramp("11161f", "1b2330", "283347", "37455c", "485872", "5e708a")
# silver driftwood / bleached bone-grey wood
DRIFT = ramp("171717", "252422", "34322e", "46433d", "5a564e", "706a60", "878073")
# weathered copper roof
VERDR = ramp("0d1a1a", "142a28", "1d3c37", "284f47", "366457", "4a7a69", "63927e")
COPPER = ramp("24130e", "3a2016", "532f1f", "6c3f29")
# the drowned colossus: green-black sea stone
DROWN = ramp("040707", "070c0c", "0b1212", "0f1818", "141f1f", "1a2727", "213030", "293a39", "324543", "3d514e",
             "4a5f5a")
SCAR = ramp("23403f", "3e6966", "6a9c96", "a6d0c8", "d8f0ea")


def spr(w, h):
    return Spr(w, h)


def thick_line(s, x0, y0, x1, y1, cols, width=2, normal_light=True):
    """A 1-2px beam from (x0,y0) to (x1,y1); cols = [lit, dark] (first px row/col towards the upper-left is lit)."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    # perpendicular pointing down-right (shadow side)
    px_, py_ = -dy / L, dx / L
    if px_ + py_ < 0:
        px_, py_ = -px_, -py_
    for i in range(n + 1):
        t = i / n
        x, y = x0 + dx * t, y0 + dy * t
        for k in range(width):
            c = cols[min(k, len(cols) - 1)]
            s.set(x + px_ * k, y + py_ * k, c)


def fill_poly(s, pts, colfn):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            if point_in_poly(x + 0.5, y + 0.5, pts):
                c = colfn(x, y)
                if c is not None:
                    s.set(x, y, c)


def rope(s, pts, cols=(WHEAT[2], WHEAT[1]), twist=2):
    """Polyline rope; alternates two tones every `twist` px to suggest the lay."""
    k = 0
    for a, b in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(n):
            t = i / n
            s.set(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, cols[(k // twist) % len(cols)])
            k += 1
    s.set(pts[-1][0], pts[-1][1], cols[(k // twist) % len(cols)])


def sag_pts(x0, y0, x1, y1, sag, n=None):
    n = n or int(abs(x1 - x0)) + 1
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n + sag * math.sin(math.pi * i / n)) for i in range(n + 1)]


def glass_float(s, x, y, glint=True):
    """3x3 glass net-float with a rope cross and a cold glint (x, y = top-left)."""
    for (dx, dy, c) in ((1, 0, GFLOAT[3]), (0, 1, GFLOAT[3]), (1, 1, GFLOAT[2]), (2, 1, GFLOAT[1]),
                        (1, 2, GFLOAT[1]), (0, 0, None), (2, 0, None), (0, 2, None), (2, 2, None)):
        if c:
            s.set(x + dx, y + dy, c)
    if glint:
        s.set(x + 1, y, GFLOAT[4])


def cork_float(s, x, y):
    """2x3 cork float."""
    s.set(x, y, WHEAT[3])
    s.set(x + 1, y, WHEAT[2])
    s.set(x, y + 1, WHEAT[3])
    s.set(x + 1, y + 1, WHEAT[1])
    s.set(x, y + 2, WHEAT[2])
    s.set(x + 1, y + 2, WHEAT[1])


def pixel_clean(img):
    return all(a in (0, 255) for a in set(img.getdata(3)))
