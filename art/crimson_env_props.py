"""Props for THE CRIMSON MANOR (part 1: furnishings). Each builder returns (w, h, layers, frames, tags).

cm_candelabra 16x40 loop(4)   standing tarnished-silver candelabra, three red candles, flickering flames
cm_chandelier 64x48 loop(4)   wrought-iron ring chandelier, red candles, dark crystal drops; pivot = top-centre (32,0)
cm_sconce     16x24 loop(4)   wall sconce, red-glass chimney with a candle inside
cm_lectern    24x32 loop(4)   an open diary on a dark-wood lectern, flickering candle, a page stirring
cm_table      64x32 idle(1)   long banquet table: black cloth, silver candlestick, goblets, spilled wine
cm_barrel     32x32 idle(1)   wine cask on a cradle, stained dark
cm_winerack   48x48 idle(1)   wine rack with dusty bottles, a couple broken and dripping
cm_coffin     32x24 closed(1) open(1)
cm_carriage   96x64 idle(1)   a wrecked black lacquered carriage, one wheel broken, torn crimson curtains, silver trim

Face right, bottom-anchored, centred; 1px K outline; light from the upper-left.
"""
import math
from PIL import Image, ImageDraw
from envlib import K, T, h01, clamp, blank, ramp
from crimson_env_lib import (ST, MB, SV, BL, VV, DM, WD, IR, GL, WX, FL, SK, GR, GS, Spr, tiny_flame, flame,
                             outline)

LQ = ramp("08070b", "0f0d14", "17141e", "211c2a", "2e2738", "433a52")        # black lacquer
BTL = ramp("070a09", "0c1210", "131c18", "1d2a24", "2c3e34", "46604e")       # dark bottle glass
PA = ramp("3a3030", "5a4c46", "7c6a5e", "9c8876", "b8a48e")                   # old parchment (candle-dim)
DUST = (0x5a, 0x54, 0x58, 255)


def turned(s, cx, y0, y1, hw_fn, R, spec=True, bias=0.0):
    """Lathe-turned solid (candlestick, goblet, knop...): cylindrical shading lit from the left."""
    for y in range(int(y0), int(y1) + 1):
        hw = hw_fn(y)
        if hw <= 0:
            continue
        for x in range(int(math.floor(cx - hw - 1)), int(math.ceil(cx + hw + 1))):
            u = (x + .5 - cx) / hw
            if abs(u) > 1:
                continue
            l = 0.5 - 0.45 * u + bias
            if spec and -0.8 < u < -0.25:
                l += 0.28
            s.set(x, y, R[int(clamp(l) * (len(R) - 1) + 0.5)])


def poly(s, pts, fn):
    """Fill a polygon; fn(x, y) -> colour or None."""
    m = Image.new("L", (s.w, s.h), 0)
    ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
    mp = m.load()
    for y in range(s.h):
        for x in range(s.w):
            if mp[x, y]:
                c = fn(x, y)
                if c is not None:
                    s.set(x, y, c)


def candle(s, x0, top, bot, w=2):
    """Red wax candle, 1-2 px wide, with a lit rim and a drip."""
    for y in range(top, bot + 1):
        for dx in range(w):
            c = WX[3] if dx == 0 else WX[2]
            if y == top:
                c = WX[4] if dx == 0 else WX[3]
            s.set(x0 + dx, y, c)
    s.set(x0 + w, top + 1, WX[2])
    if bot - top > 3:
        s.set(x0 + w, top + 2, WX[1])
    s.set(x0 + (w - 1), top - 1, K)                     # wick


# =========================================================================== candelabra
def candelabra():
    Wd, Hd = 16, 40
    frames = []
    for f in range(4):
        s = Spr(Wd, Hd)
        cx = 8.0

        def prof(y):
            if y >= 37: return 5.5 - (39 - y) * 0.2 + (y - 37) * 0.6
            if y == 36: return 3.5
            if y == 35: return 2.2
            if y in (33, 34): return 1.8 if y == 34 else 1.3
            if y in (27, 28): return 2.0
            if y in (21, 22): return 1.6
            if y >= 15: return 1.0
            if y in (13, 14): return 2.2 if y == 14 else 1.5
            if y in (10, 11): return 1.6
            return 0
        turned(s, cx, 10, 39, prof, SV, bias=-0.1)
        # a curved crossbar lifting to the side cups
        for x in range(3, 13):
            y = 14 if 5 <= x <= 10 else 13
            s.set(x, y, SV[4] if x < 8 else SV[2])
            s.set(x, y + 1, SV[2] if x < 8 else SV[1])
        for (x, y) in ((3, 12), (12, 12)):
            s.set(x, y, SV[3] if x < 8 else SV[2])
        # drip pans
        for (x0, y) in ((1, 11), (11, 11)):
            s.set(x0, y, SV[4]); s.set(x0 + 1, y, SV[4]); s.set(x0 + 2, y, SV[3]); s.set(x0 + 3, y, SV[2])
        for (x, c) in ((5, 4), (6, 4), (7, 3), (8, 3), (9, 2), (10, 2)):
            s.set(x, 9, SV[c])
        candle(s, 2, 5, 10)
        candle(s, 12, 6, 10)
        candle(s, 7, 3, 8)
        # a red wax drip running down the stem
        s.set(9, 16, WX[2]); s.set(9, 17, WX[1])
        s.outline()
        tiny_flame(s, 2, 3, f, 0)
        tiny_flame(s, 12, 4, f, 2)
        tiny_flame(s, 7, 1, f, 1)
        frames.append({"ms": 130, "cels": {"Candelabra": s.img}})
    return Wd, Hd, ["Candelabra"], frames, [("loop", 0, 3)]


# =========================================================================== chandelier
def chandelier():
    Wd, Hd = 64, 48
    CX, CY, RX, RY = 32, 26, 25, 6
    frames = []
    cand = [a * math.pi / 3 + math.pi / 6 for a in range(6)]
    for f in range(4):
        s = Spr(Wd, Hd)

        def prof(y):
            if y <= 1: return 0
            if y == 2: return 1.2
            if 3 <= y <= 6: return 0.9
            if y in (7, 8): return 2.2 if y == 8 else 1.6
            if 9 <= y <= 13: return 0.9
            if 14 <= y <= 19: return 1.2 + 2.0 * math.sin((y - 13) / 7 * math.pi)
            if 20 <= y <= 30: return 1.0
            if y in (31, 32): return 2.0
            if y == 33: return 1.2
            return 0
        # chains from the crown to the ring (behind everything)
        for (ex, ey) in ((CX - RX + 1, CY - 1), (CX + RX - 1, CY - 1), (CX - 12, CY + 2), (CX + 12, CY + 2)):
            n = int(max(abs(ex - CX), abs(ey - 4)))
            for i in range(n + 1):
                t = i / n
                x, y = CX + (ex - CX) * t, 4 + (ey - 4) * t
                s.set(x, y, IR[4] if i % 2 else IR[2])
        # back half of the ring + back candles
        back = [a for a in cand if math.sin(a) < 0]
        front = [a for a in cand if math.sin(a) >= 0]

        def ring(half):
            for i in range(360):
                a = i / 360 * 2 * math.pi
                if (math.sin(a) >= 0) != (half == "front"):
                    continue
                x = CX + RX * math.cos(a)
                y = CY + RY * math.sin(a)
                if half == "front":
                    s.set(x, y, SV[4] if math.cos(a) < 0 else SV[3])       # silver trim on the rim
                    s.set(x, y + 1, IR[4] if math.cos(a) < 0 else IR[3])
                    s.set(x, y + 2, IR[2])
                else:
                    s.set(x, y, IR[3]); s.set(x, y + 1, IR[2])

        def candle_at(a, dim):
            x = int(round(CX + RX * math.cos(a)))
            y = int(round(CY + RY * math.sin(a)))
            s.set(x - 1, y - 1, SV[3] if not dim else SV[2]); s.set(x, y - 1, SV[3] if not dim else SV[1])
            s.set(x + 1, y - 1, SV[2] if not dim else SV[1])
            for yy in range(y - 6, y - 1):
                s.set(x - 1, yy, WX[3] if not dim else WX[1]); s.set(x, yy, WX[2] if not dim else WX[0])
            s.set(x - 1, y - 7, WX[4] if not dim else WX[2]); s.set(x, y - 7, WX[3] if not dim else WX[1])
            s.set(x + 1, y - 5, WX[2] if not dim else WX[1])
            return (x - 1, y - 9)
        tips = []
        for a in back:
            tips.append(candle_at(a, True))
        ring("back")
        turned(s, CX, 0, 33, prof, IR, bias=0.1)
        # crown ring at the very top (the pivot)
        s.set(CX - 1, 0, IR[4]); s.set(CX, 0, IR[3]); s.set(CX - 2, 1, IR[4]); s.set(CX + 1, 1, IR[2])
        # scroll arms from the vase out to the ring
        for sg in (-1, 1):
            for i in range(20):
                t = i / 19
                x = CX + sg * (2 + t * (RX - 4))
                y = 19 + 7 * t - 3 * math.sin(t * math.pi)
                s.set(x, y, IR[4] if sg < 0 else IR[3])
            for (dx, dy) in ((3, 20), (4, 21), (5, 21), (6, 20)):
                s.set(CX + sg * dx, dy, IR[3])
        ring("front")
        # hanging crystal drops beneath the front of the ring
        for k, a in enumerate([math.pi * (0.08 + 0.84 * i / 10) for i in range(11)]):
            x = int(round(CX + RX * math.cos(a)))
            y = int(round(CY + RY * math.sin(a))) + 3
            ln = 2 + (k % 3)
            for yy in range(y, y + ln):
                s.set(x, yy, IR[2])
            glint = (k + f) % 4 == 0
            s.set(x, y + ln, GS[4] if glint else GS[3]); s.set(x + 1, y + ln, GS[2])
            s.set(x, y + ln + 1, GS[2]); s.set(x + 1, y + ln + 1, GS[1])
            s.set(x, y + ln + 2, GS[1])
        # central pendant drop
        for (dx, dy, c) in ((0, 34, GS[3]), (-1, 35, GS[4]), (0, 35, GS[3]), (1, 35, GS[2]), (-1, 36, GS[3]),
                            (0, 36, GS[2]), (1, 36, GS[1]), (-1, 37, GS[2]), (0, 37, GS[1]), (1, 37, GS[1]),
                            (0, 38, GS[1]), (0, 39, GS[0])):
            s.set(CX + dx - 0, dy, c)
        if f % 2 == 0:
            s.set(CX - 1, 35, (0x8a, 0x84, 0xb0, 255))
        for a in front:
            tips.append(candle_at(a, False))
        s.outline()
        for i, (x, y) in enumerate(tips):
            tiny_flame(s, x, y + 1, f, i)
        frames.append({"ms": 130, "cels": {"Chandelier": s.img}})
    return Wd, Hd, ["Chandelier"], frames, [("loop", 0, 3)]


# =========================================================================== sconce
def sconce():
    Wd, Hd = 16, 24
    frames = []
    for f in range(4):
        s = Spr(Wd, Hd)
        # backplate: a pointed gothic escutcheon in tarnished silver, finial dropping to the bottom row
        for y in range(1, 21):
            if y < 4:
                hw = (0.5, 1.5, 2.5)[y - 1]
            elif y < 17:
                hw = 3.5
            else:
                hw = 3.5 - (y - 16) * 0.9
            for x in range(int(8 - hw - 0.5), int(8 + hw + 0.5)):
                u = (x + .5 - 8) / max(hw, 0.5)
                c = SV[4] if u < -0.5 else SV[3] if u < 0.3 else SV[2]
                if y == 1 or (u < -0.6 and y < 17):
                    c = SV[5]
                s.set(x, y, c)
        for y in range(21, 24):
            s.set(7, y, SV[3]); s.set(8, y, SV[2])
        s.set(7, 23, SV[4])
        # the arm + drip pan (bobeche)
        for x in range(4, 12):
            s.set(x, 15, SV[5] if x < 7 else SV[4] if x < 10 else SV[3])
            s.set(x, 16, SV[3] if x < 9 else SV[1])
        s.set(7, 17, SV[3]); s.set(8, 17, SV[2]); s.set(7, 18, SV[2]); s.set(8, 18, SV[1])
        # red glass chimney with the candle glowing inside
        for y in range(5, 15):
            for x in range(5, 11):
                edge = x in (5, 10) or y == 5
                c = BL[3] if edge else BL[5] if y > 8 else BL[4]
                if x == 6 and 6 <= y <= 12:
                    c = BL[7] if y < 9 else BL[6]
                if x == 10:
                    c = BL[2]
                s.set(x, y, c)
        # glowing core, flickering
        core = [((7, 10), (8, 10), (7, 9), (8, 11), (7, 11)), ((7, 10), (8, 10), (7, 9), (8, 9), (7, 11)),
                ((7, 10), (8, 10), (8, 9), (7, 11)), ((7, 10), (8, 10), (7, 9), (7, 8), (8, 11), (7, 11))][f]
        for (x, y) in core:
            s.set(x, y, FL[2])
        s.set(7, 10, FL[4] if f % 2 else FL[3]); s.set(8, 10, FL[3])
        for x in range(7, 9):
            s.set(x, 12, WX[3] if x == 7 else WX[2]); s.set(x, 13, WX[2] if x == 7 else WX[1])
        s.set(4, 4, SV[3]); s.set(5, 4, SV[4]); s.set(10, 4, SV[2]); s.set(11, 4, SV[2])   # glass rim crown
        s.set(6, 4, SV[5]); s.set(7, 4, SV[4]); s.set(8, 4, SV[3]); s.set(9, 4, SV[3])
        s.outline()
        frames.append({"ms": 140, "cels": {"Sconce": s.img}})
    return Wd, Hd, ["Sconce"], frames, [("loop", 0, 3)]


# =========================================================================== lectern
def lectern():
    Wd, Hd = 24, 32
    frames = []
    for f in range(4):
        s = Spr(Wd, Hd)
        # foot
        for x in range(4, 20):
            s.set(x, 31, WD[2] if x > 5 else WD[4])
            s.set(x, 30, WD[4] if x < 12 else WD[3])
        for x in range(6, 18):
            s.set(x, 29, WD[5] if x < 10 else WD[4])
        # turned column
        def prof(y):
            if y in (19, 20): return 2.5
            if y in (26, 27): return 2.5
            if y == 28: return 3.2
            if 17 <= y <= 28: return 1.6
            return 0
        turned(s, 12, 17, 28, prof, WD)
        # slanted desk, seen from the front-above
        for y in range(11, 18):
            inset = (17 - y) // 3
            for x in range(3 + inset, 21 - inset):
                c = WD[4] if y < 16 else WD[5] if y == 16 else WD[2]
                if x == 3 + inset:
                    c = WD[6]
                elif x == 20 - inset:
                    c = WD[2]
                s.set(x, y, c)
        # the diary: crimson leather cover, two page faces with faint red-ink lines
        for x in range(4, 20):
            s.set(x, 15, VV[3] if 4 < x < 19 else VV[2])
            s.set(x, 14, PA[2] if x % 2 else PA[1])
        s.set(11, 14, VV[2]); s.set(12, 14, VV[2])
        for x in range(5, 19):
            g = abs(x + 0.5 - 12)
            top = 8 + (1 if g < 1.6 else 0) + (1 if g > 6 else 0)
            lift = 0
            if x >= 16 and f in (1, 2):
                lift = (x - 15) * (1 if f == 1 else 2) // 2
            for y in range(top - lift, 14):
                c = PA[4] if x < 12 else PA[3]
                if g < 1.6:
                    c = PA[1]
                elif y == top - lift:
                    c = PA[4] if x < 12 else PA[3]
                elif (y - top) % 2 == 1 and 1.5 < g < 6 and h01(x, y, 3) < 0.75:
                    c = BL[3] if x < 12 else BL[2]                 # handwriting
                s.set(x, y, c)
        # ribbon bookmark hanging over the front edge
        s.set(13, 15, BL[4]); s.set(13, 16, BL[4]); s.set(13, 17, BL[3]); s.set(14, 18, BL[3])
        # a small candle on the desk's back-right corner
        for (x, y, c) in ((18, 10, SV[4]), (19, 10, SV[3]), (20, 10, SV[2])):
            s.set(x, y, c)
        candle(s, 19, 5, 9, 1)
        s.set(18, 9, WX[2])
        s.outline()
        tiny_flame(s, 19, 3, f, 0)
        frames.append({"ms": 140, "cels": {"Lectern": s.img}})
    return Wd, Hd, ["Lectern"], frames, [("loop", 0, 3)]


# =========================================================================== table
def table():
    Wd, Hd = 64, 32
    s = Spr(Wd, Hd)
    CL = ramp("060509", "0b0a10", "121019", "1a1724", "252032", "342d44")       # black cloth
    # carved legs under the cloth
    for x0 in (7, 54):
        for y in range(26, 32):
            w = 3 if y < 30 else 4
            for x in range(x0, x0 + w):
                s.set(x, y, WD[4] if x == x0 else WD[2] if x < x0 + w - 1 else WD[1])
        s.set(x0, 28, WD[5]); s.set(x0 + 1, 28, WD[3])
    # table top face (cloth over it)
    for x in range(2, 62):
        s.set(x, 14, CL[5] if x < 30 else CL[4])
        s.set(x, 15, CL[4] if x < 20 else CL[3])
    # the drape: folds as soft vertical bands, silver lace hem
    for x in range(2, 62):
        fold = math.sin((x - 2) / 6.5 * math.pi)
        for y in range(16, 27):
            v = 0.42 + 0.25 * fold - 0.15 * (y - 16) / 10
            if x < 4:
                v += 0.2
            if x > 59:
                v -= 0.2
            s.set(x, y, CL[int(clamp(v) * (len(CL) - 1) + 0.5)])
        hem = 27 + (1 if (x % 6) in (2, 3) else 0)
        for y in range(27, hem + 1):
            s.set(x, y, CL[2])
        s.set(x, hem, SV[3] if x % 2 else SV[2])
        if x % 6 == 3:
            s.set(x, hem + 1, SV[2])
    # centre: silver candlestick with three candles
    def prof(y):
        if y == 13: return 3.0
        if y == 12: return 1.8
        if 7 <= y <= 11: return 0.9 if y != 9 else 1.6
        if y == 6: return 2.0
        return 0
    turned(s, 32, 6, 13, prof, SV)
    for (x, y) in ((29, 6), (28, 5), (35, 6), (36, 5)):
        s.set(x, y, SV[4] if x < 32 else SV[2])
    candle(s, 27, 1, 4, 1)
    candle(s, 36, 1, 4, 1)
    candle(s, 31, 0, 5, 2)
    # goblets
    def goblet(cx, spill=False):
        def gp(y):
            if y == 13: return 2.0
            if y == 12: return 1.0
            if y == 11: return 0.7
            if 8 <= y <= 10: return 1.8 - (y - 8) * 0.35
            return 0
        turned(s, cx, 8, 13, gp, SV)
        s.set(cx - 2, 8, SV[5]); s.set(cx + 1, 8, SV[2])
        s.set(cx - 1, 8, BL[4]); s.set(cx, 8, BL[3])          # wine at the brim
    goblet(14)
    goblet(47)
    # a platter of dark grapes / figs
    for x in range(18, 27):
        s.set(x, 13, SV[3] if x < 22 else SV[2])
    for (x, y, c) in ((19, 12, VV[2]), (20, 12, VV[3]), (21, 11, VV[3]), (22, 12, VV[2]), (23, 11, VV[1]),
                      (24, 12, VV[2]), (21, 12, VV[1]), (22, 11, VV[4]), (20, 11, VV[2])):
        s.set(x, y, c)
    # the toppled goblet at the right, its wine spreading and dripping off the cloth
    for (x, y, c) in ((52, 12, SV[5]), (53, 12, SV[4]), (54, 12, SV[4]), (55, 12, SV[3]), (52, 13, SV[3]),
                      (53, 13, SV[3]), (54, 13, SV[2]), (56, 13, SV[3]), (57, 12, SV[3]), (57, 13, SV[2])):
        s.set(x, y, c)
    for x in range(46, 52):
        s.set(x, 14, BL[3] if x % 2 else BL[4])
    for x in range(47, 51):
        s.set(x, 15, BL[2])
    for (x, ln) in ((48, 6), (50, 3)):
        for y in range(16, 16 + ln):
            s.set(x, y, BL[2] if y < 15 + ln else BL[3])
    s.outline()
    tiny_flame(s, 27, -1 + 1, 0, 0)
    tiny_flame(s, 36, -1 + 1, 0, 2)
    return Wd, Hd, ["Table"], [{"ms": 1000, "cels": {"Table": s.img}}], [("idle", 0, 0)]


# =========================================================================== barrel
def barrel():
    Wd, Hd = 32, 32
    s = Spr(Wd, Hd)
    cy = 15.5
    # cradle: two X trestles and a plank (behind the cask's lower half)
    for x0 in (6, 21):
        for i in range(10):
            s.set(x0 + i // 2, 22 + i, WD[4])
            s.set(x0 + 4 - i // 2, 22 + i, WD[3])
            s.set(x0 + 5 - i // 2, 22 + i, WD[2])
    for x in range(4, 29):
        s.set(x, 26, WD[3] if x % 7 else WD[2])
    # the cask body (lying on its side): bulged profile, shaded as a cylinder along x (light from above-left)
    for x in range(3, 29):
        u = (x + .5 - 16) / 13
        hh = 7.0 + 2.0 * (1 - u * u)
        for y in range(int(cy - hh), int(cy + hh) + 1):
            v = (y + .5 - cy) / hh
            if abs(v) > 1:
                continue
            l = 0.52 - 0.45 * v - 0.12 * u
            if -0.75 < v < -0.35:
                l += 0.2
            c = WD[int(clamp(l) * (len(WD) - 1) + 0.5)]
            # stave seams run along the cask
            if abs(((v + 1) * 3.5) % 1 - 0.5) > 0.44 and abs(v) < 0.9:
                c = WD[max(0, WD.index(c) - 1)]
            s.set(x, y, c)
    # iron hoops
    for hx in (6, 7, 12, 20, 25, 26):
        u = (hx + .5 - 16) / 13
        hh = 7.0 + 2.0 * (1 - u * u)
        for y in range(int(cy - hh), int(cy + hh) + 1):
            v = (y + .5 - cy) / hh
            if abs(v) > 1:
                continue
            l = 0.55 - 0.5 * v
            c = IR[int(clamp(l) * (len(IR) - 1) + 0.5)]
            if hx in (7, 26) and v < -0.3:
                c = SV[2]
            s.set(hx, y, c)
    # the head at the right end (lighter end-grain), a spigot, dark wine stains
    for y in range(9, 23):
        s.set(28, y, WD[3] if y < 15 else WD[2])
    s.set(29, 15, GL[4]); s.set(30, 15, GL[3]); s.set(29, 16, GL[3]); s.set(30, 16, GL[2])
    s.set(31, 16, GL[2]); s.set(30, 17, GL[2])
    for y in range(18, 22):
        s.set(30, y, BL[2] if y < 21 else BL[3])
    for (x, y) in ((27, 17), (26, 18), (27, 18), (26, 19), (25, 20), (27, 19), (24, 21), (26, 21), (25, 22), (27, 20)):
        s.set(x, y, BL[1] if h01(x, y, 3) < 0.5 else BL[2])
    for (x, y) in ((10, 20), (11, 21), (10, 22), (15, 21), (16, 22), (14, 22)):
        s.set(x, y, BL[1])
    # stencilled crest: tarnished silver mark on the belly
    for (x, y, c) in ((16, 12, SV[3]), (15, 13, SV[2]), (16, 13, SV[3]), (17, 13, SV[2]), (16, 14, SV[2])):
        s.set(x, y, c)
    # puddle on the floor under the tap
    for x in range(26, 32):
        s.set(x, 31, BL[2] if x % 2 else BL[3])
    s.outline()
    return Wd, Hd, ["Barrel"], [{"ms": 1000, "cels": {"Barrel": s.img}}], [("idle", 0, 0)]


# =========================================================================== wine rack
def winerack():
    Wd, Hd = 48, 48
    s = Spr(Wd, Hd)
    # frame: uprights, top + bottom rails, a plinth
    for y in range(3, 45):
        for x in (2, 3, 4):
            s.set(x, y, WD[4] if x == 2 else WD[3] if x == 3 else WD[1])
        for x in (43, 44, 45):
            s.set(x, y, WD[3] if x == 43 else WD[2] if x == 44 else WD[1])
    for x in range(1, 47):
        s.set(x, 2, WD[5] if x < 30 else WD[4]); s.set(x, 3, WD[4]); s.set(x, 4, WD[2])
        s.set(x, 44, WD[4]); s.set(x, 45, WD[3]); s.set(x, 46, WD[2]); s.set(x, 47, WD[1])
    # 4 x 4 cubbies of 9 x 9 (x 5..42, y 5..43)
    broken = {(1, 0), (3, 2)}
    empty = {(2, 1), (0, 3)}
    for r in range(4):
        for c in range(4):
            x0, y0 = 5 + c * 9 + (1 if c > 1 else 0), 5 + r * 10 - (1 if r > 2 else 0)
            # shelf board under the cubby + divider on its right
            for x in range(x0, x0 + 9):
                s.set(x, y0 + 9, WD[4] if x < x0 + 8 else WD[2])
            for y in range(y0, y0 + 9):
                s.set(x0 + 8, y, WD[3])
            for y in range(y0, y0 + 9):
                for x in range(x0, x0 + 8):
                    s.set(x, y, WD[0] if y > y0 else WD[1])
            if (c, r) in empty:
                continue
            bx, by = x0 + 3.5, y0 + 4.8
            # bottle seen end-on (its punted base), dusty dark glass
            for y in range(y0 + 1, y0 + 9):
                for x in range(x0, x0 + 8):
                    d = math.hypot(x + .5 - bx, y + .5 - by)
                    if d <= 3.3:
                        cc = BTL[2] if d > 2.3 else BTL[1]
                        if (x + .5 - bx) + (y + .5 - by) < -2.2 and d > 2.2:
                            cc = BTL[4]                         # shoulder catching light
                        if d < 1.5:
                            cc = WX[2] if (x + .5 - bx) + (y + .5 - by) < 0 else WX[1]   # red wax seal
                        s.set(x, y, cc)
            s.set(int(bx) - 1, int(by) - 3, DUST); s.set(int(bx), int(by) - 3, DUST)
            if (c, r) in broken:
                # a smashed bottle: jagged hole, wine dripping over the shelf
                for (dx, dy) in ((0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (0, -1), (2, 1)):
                    s.set(int(bx) + dx, int(by) + dy, BL[1])
                s.set(int(bx) - 1, int(by) - 1, BTL[5]); s.set(int(bx) + 2, int(by), BTL[4])
                for y in range(int(by) + 2, y0 + 12):
                    s.set(int(bx), y, BL[3] if y < y0 + 10 else BL[4])
    # long drips from the broken bottles down the rack to a puddle at the foot
    for (x, y0, y1) in ((18, 18, 30), (38, 38, 44)):
        for y in range(y0, y1):
            s.set(x, y, BL[3] if y % 5 else BL[4])
    for x in range(14, 24):
        s.set(x, 47, BL[3] if x % 2 else BL[2])
    for x in range(35, 42):
        s.set(x, 47, BL[2])
    # cobweb in the top-left corner
    for i in range(6):
        s.set(5 + i, 5, (0x44, 0x40, 0x48, 255) if i % 2 == 0 else None)
        s.set(5, 5 + i, (0x44, 0x40, 0x48, 255) if i % 2 == 0 else None)
    for i in range(5):
        s.set(5 + i, 10 - i, (0x3a, 0x36, 0x40, 255))
    s.outline()
    return Wd, Hd, ["Rack"], [{"ms": 1000, "cels": {"Rack": s.img}}], [("idle", 0, 0)]


# =========================================================================== coffin
def coffin_depth(x):
    """Half-depth of the coffin's hexagonal plan at column x (head at the left), seen from the front-above."""
    if x < 2 or x > 29:
        return 0
    if x <= 9:
        return 3.4 + (x - 2) / 7 * 2.6
    return 6.0 - (x - 9) / 20 * 3.0


def coffin_body(s, open_, mid=9, wall=6):
    for x in range(2, 30):
        d = coffin_depth(x)
        top, front = int(round(mid - d)), int(round(mid + d))
        for y in range(front, front + wall):
            c = LQ[3] if x < 10 else LQ[2]
            if y == front:
                c = SV[4] if x < 12 else SV[3]                 # silver trim along the lid edge
            elif y == front + wall - 1:
                c = LQ[1]
            elif y == front + 1:
                c = LQ[4] if x < 18 else LQ[3]                 # lacquer gloss
            s.set(x, y, c)
        for y in range(top, front):
            if not open_:
                c = LQ[4] if y < mid - 1 else LQ[3]
                if y == top:
                    c = LQ[5] if x < 16 else LQ[4]
                if y == front - 1:
                    c = LQ[2]
                if x == 2:
                    c = LQ[4]
            else:
                if y == top or x == 2:
                    c = LQ[4]                                  # the wall's top edge
                elif y == top + 1 or x == 3:
                    c = VV[1]                                  # shadowed inner wall
                else:
                    c = VV[3] if (x + (y % 2) * 2) % 4 else VV[1]   # tufted lining with buttons
                    if (x + y) % 4 == 1:
                        c = VV[4]
                s.set(x, y, c)
                continue
            s.set(x, y, c)
    # the raised lid moulding (closed): a thin inset hexagon line
    if not open_:
        for x in range(4, 28):
            d = coffin_depth(x) - 1.6
            if d > 0:
                s.set(x, int(round(mid - d)), LQ[5] if x < 16 else LQ[4])
                s.set(x, int(round(mid + d)), LQ[1])
    # silver handles on the front wall, silver corner caps, feet
    for hx in (7, 15, 23):
        y = int(round(mid + coffin_depth(hx))) + 3
        s.set(hx, y, SV[5]); s.set(hx + 1, y, SV[4]); s.set(hx + 2, y, SV[3])
        s.set(hx, y + 1, SV[2]); s.set(hx + 2, y + 1, SV[1])
    for x in (2, 29):
        y = int(round(mid + coffin_depth(x)))
        s.set(x, y + 1, SV[4]); s.set(x, y + 2, SV[3]); s.set(x, y + wall - 2, SV[2])
    for x in (4, 5, 26, 27):
        yb = int(round(mid + coffin_depth(x))) + wall
        s.set(x, yb, LQ[2] if x in (4, 26) else LQ[1])


def coffin(open_=False):
    Wd, Hd = 32, 24
    s = Spr(Wd, Hd)
    mid = 9
    # the coffin sits lower when its lid is aside (room for the lid on top), same footprint
    coffin_body(s, open_, mid + (2 if open_ else 0), 6 if not open_ else 5)
    if not open_:
        # silver plaque + a dead rose laid on the lid
        for (x, y, c) in ((12, 8, SV[5]), (13, 8, SV[4]), (14, 8, SV[3]), (12, 9, SV[3]), (13, 9, SV[3]),
                          (14, 9, SV[2]), (13, 7, SV[4]), (13, 10, SV[2])):
            s.set(x, y, c)
        for (x, y, c) in ((19, 8, IR[3]), (20, 9, IR[3]), (21, 9, IR[3]), (22, 10, IR[2]), (18, 7, VV[4]),
                          (18, 8, VV[3]), (17, 7, VV[2]), (17, 8, VV[1]), (18, 6, VV[5])):
            s.set(x, y, c)
        s.outline()
        return s.img
    # pillow at the head end
    for (x, y, c) in ((4, 9, VV[6]), (5, 9, VV[6]), (6, 9, VV[5]), (4, 10, VV[5]), (5, 10, VV[5]), (6, 10, VV[4]),
                      (4, 11, VV[4]), (5, 11, VV[4]), (6, 11, VV[3]), (4, 12, VV[3]), (5, 12, VV[3]), (7, 10, VV[3]),
                      (7, 11, VV[2])):
        s.set(x, y, c)
    s.outline()
    # the lid, shoved aside: slid right and down across the foot end, overhanging the front wall at an angle
    lid = Spr(Wd, Hd)
    for i in range(22):
        x = 10 + i
        d = coffin_depth(i * 27 / 21 + 2) * 0.85
        cy = 8 + i * 0.35
        top, bot = int(round(cy - d)), int(round(cy + d))
        for y in range(top, bot + 1):
            c = LQ[4] if y < cy else LQ[3]
            if y == top:
                c = LQ[5] if i < 8 else LQ[4]
            lid.set(x, y, c)
        lid.set(x, bot + 1, SV[3] if i < 10 else SV[2])
        lid.set(x, bot + 2, LQ[1])
    for (x, y, c) in ((17, 9, SV[4]), (18, 9, SV[3]), (17, 10, SV[3]), (18, 10, SV[2])):
        lid.set(x, y, c)
    lid.outline()
    s.paste(lid.img, 0, 0)
    return s.img


def build_coffin():
    frames = [{"ms": 1000, "cels": {"Coffin": coffin(False)}}, {"ms": 1000, "cels": {"Coffin": coffin(True)}}]
    return 32, 24, ["Coffin"], frames, [("closed", 0, 0), ("open", 1, 1)]


# =========================================================================== carriage
def wheel(s, cx, cy, r, spokes=10, broken=False, sq=1.0, rim=IR, hub=SV):
    for y in range(int(cy - r) - 2, int(cy + r) + 3):
        for x in range(int(cx - r * sq) - 2, int(cx + r * sq) + 3):
            dx, dy = (x + .5 - cx) / sq, y + .5 - cy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            if broken and 0.3 < a < 1.6:
                continue                                     # a chunk of the rim is gone
            if r - 2 <= d <= r:
                l = 0.5 - 0.4 * (dx + dy) / (r * 1.4)
                c = rim[int(clamp(l) * (len(rim) - 1) + 0.5)]
                if d > r - 0.8 and dy < 0 and dx < 0:
                    c = SV[3]                                # silver tyre catching the light
                s.set(x, y, c)
            elif d < 2.2:
                s.set(x, y, hub[4] if dx + dy < 0 else hub[2])
            elif d < r - 2:
                for k in range(spokes):
                    sa = k * 2 * math.pi / spokes
                    if broken and k in (2, 3, 7):
                        continue
                    if abs(math.sin(a - sa)) * d < 0.7 and math.cos(a - sa) > 0:
                        s.set(x, y, rim[3] if k < spokes // 2 else rim[2])


def carriage():
    Wd, Hd = 96, 64
    body = Spr(Wd, Hd)
    b = body
    # ---- coach body (unsheared); belly curves up at the ends
    def belly(x):
        u = (x - 45) / 26
        return 44 - 12 * (max(0.0, abs(u) - 0.45) / 0.55) ** 1.6

    def topy(x):
        e = min(x - 19, 71 - x)
        return 12 + (3 - e if e < 3 else 0)

    for x in range(19, 72):
        bot = int(round(belly(x)))
        for y in range(topy(x), bot + 1):
            c = LQ[2]
            if x < 22:
                c = LQ[4]
            if y < 14:
                c = LQ[4]
            if y == bot:
                c = LQ[1]
            if 30 <= y <= 31:
                c = SV[3] if y == 30 else LQ[1]               # silver waist moulding
            if y > 31 and (x + (y - 31)) % 23 == 0:
                c = LQ[4]                                    # gloss streak on the lower panel
            b.set(x, y, c)
    # roof with a silver rail and corner finials
    for x in range(17, 74):
        b.set(x, 11, LQ[3]); b.set(x, 10, LQ[4] if x < 50 else LQ[3]); b.set(x, 9, SV[2])
        if x % 6 == 0:
            b.set(x, 8, SV[3]); b.set(x, 7, SV[4])
    for x in range(17, 74):
        b.set(x, 6, SV[3] if x < 50 else SV[2])
    for fx in (17, 73):
        b.set(fx, 5, SV[5]); b.set(fx, 4, SV[4])
    # panels with silver pin-striping
    for (x0, x1, y0, y1) in ((21, 35, 14, 29), (37, 55, 14, 43), (57, 70, 14, 29)):
        for x in range(x0, x1 + 1):
            b.set(x, y0, SV[2]); b.set(x, min(y1, int(belly(x)) - 2), SV[1])
        for y in range(y0, y1 + 1):
            if y <= int(belly(x0)) - 2:
                b.set(x0, y, SV[2])
            if y <= int(belly(x1)) - 2:
                b.set(x1, y, SV[1])
    # windows: door window (pointed) + two quarter windows, torn crimson curtains inside, dark interior
    def window(x0, x1, y0, y1, pointed):
        cxw = (x0 + x1) / 2
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if pointed and y < y0 + 3 and abs(x + .5 - cxw - .5) > (y - y0 + 1) * 2:
                    continue
                b.set(x, y, IR[0])
        # ragged curtains hanging from the top on both sides
        for x in range(x0, x1 + 1):
            side = x < x0 + (x1 - x0) * 0.4 or x > x0 + (x1 - x0) * 0.75
            if not side:
                continue
            ln = int((y1 - y0) * (0.55 + 0.45 * h01(x, y0, 4)))
            for y in range(y0 + (2 if pointed else 0), y0 + ln):
                if pointed and y < y0 + 3 and abs(x + .5 - cxw - .5) > (y - y0 + 1) * 2:
                    continue
                c = VV[4] if (x - x0) % 3 == 0 else VV[3] if (x - x0) % 3 == 1 else VV[2]
                b.set(x, y, c)
            if h01(x, 9, 3) < 0.5:
                b.set(x, y0 + ln, VV[1])
    window(40, 52, 16, 28, True)
    window(24, 33, 16, 26, False)
    window(60, 68, 16, 26, False)
    # crest on the door
    for (x, y, c) in ((45, 34, SV[5]), (46, 34, SV[4]), (47, 34, SV[3]), (45, 35, SV[4]), (46, 35, BL[4]),
                      (47, 35, SV[2]), (45, 36, SV[3]), (46, 36, SV[3]), (47, 36, SV[2]), (46, 37, SV[2])):
        b.set(x, y, c)
    b.set(53, 32, SV[4]); b.set(53, 33, SV[3])                                          # door handle
    # coachman's box at the front + footboard
    for y in range(22, 34):
        for x in range(72, 80):
            b.set(x, y, LQ[3] if x < 74 else LQ[2])
    for x in range(71, 82):
        b.set(x, 21, SV[3] if x < 76 else SV[2]); b.set(x, 22, LQ[4])
    for i in range(10):
        b.set(80 + i // 2, 33 + i // 2, LQ[3]); b.set(81 + i // 2, 33 + i // 2, LQ[2])
    # a (dead) carriage lamp on the box corner
    for y in range(14, 20):
        b.set(71, y, BL[3] if 15 <= y <= 18 else IR[3]); b.set(72, y, BL[2] if 15 <= y <= 18 else IR[2])
    b.set(71, 13, SV[3]); b.set(72, 13, SV[2]); b.set(71, 20, IR[2])
    # perch + springs
    for x in range(22, 76):
        b.set(x, 47, IR[3]); b.set(x, 48, IR[1])
    for sx in (26, 66):
        for i in range(6):
            b.set(sx + int(2 * math.sin(i / 5 * math.pi)), 42 + i, IR[4])
    # ---- tilt: the rear corner sags onto the broken wheel (vertical shear, pixel-clean)
    s = Spr(Wd, Hd)
    bp = b.img.load()
    for x in range(Wd):
        dy = int(round(max(0, 70 - x) * 0.11))
        for y in range(Hd):
            c = bp[x, y]
            if c[3]:
                s.set(x, y + dy, c)
    # front wheel (intact) and the broken shafts resting on the ground
    wheel(s, 70, 51, 12, 10)
    for i in range(26):
        x = 76 + i * 0.75
        y = 49 + i * 0.5
        s.set(x, y, WD[3]); s.set(x, y + 1, WD[1])
    for (x, y) in ((95, 62), (94, 62), (93, 61)):
        s.set(x, y, WD[2])
    s.set(90, 63, WD[3]); s.set(91, 63, WD[2])                                          # splinter
    # the rear wheel: broken, fallen against the body, a chunk of rim missing; spokes on the ground
    wheel(s, 20, 50, 13, 10, broken=True, sq=0.55)
    for (x0, y0, x1, y1) in ((30, 62, 37, 60), (6, 63, 12, 61), (40, 63, 45, 63)):
        s.line(x0, y0, x1, y1, WD[3])
    # torn curtain scrap on the ground
    for (x, y) in ((48, 62), (49, 62), (50, 63), (51, 63), (52, 63), (49, 63)):
        s.set(x, y, VV[3])
    s.outline()
    return Wd, Hd, ["Carriage"], [{"ms": 1000, "cels": {"Carriage": s.img}}], [("idle", 0, 0)]


PROPS = {
    "cm_candelabra": candelabra,
    "cm_chandelier": chandelier,
    "cm_sconce": sconce,
    "cm_lectern": lectern,
    "cm_table": table,
    "cm_barrel": barrel,
    "cm_winerack": winerack,
    "cm_coffin": build_coffin,
    "cm_carriage": carriage,
}
