#!/usr/bin/env python3
"""Agent X props + FX.

    python3 art/gen_secrets_fx.py [--preview]

Props (bottom-anchored, centred):
    sc_seal      32x48  idle(6 loop) flare(4) shatter(8)   faint golden seal carved into R1's cliff wall
    sc_campfire  32x32  loop(6)                            the hermit's fire: stone ring, charred wood, flames
    sc_mat       32x16  idle(1)                            woven meditation mat, clay bowl, incense
    sc_cairn     16x24  idle(1)                            stacked prayer stones with a scrap of cloth
    sc_banner    32x64  idle(6 loop) ring(6) spent(1)      the challenger's banner on a pike, with a small iron bell
    sc_ashes     48x16  loop(6)                            mound of grey ash with ember glints (Ember's Hollow)
FX (centred):
    fx_sc_whirl  32x40  6 loop   Oswin's ash-wind whirlwind (travels along the ground)
    fx_sc_gust   64x32  5        dash-start burst of ash-wind
    fx_sc_cslash 48x32  4 loop   the Champion's burning crescent (travels right)
    fx_sc_ecres  48x32  4 loop   the First Ember's black-and-ember crescent (travels right)
    fx_sc_ebolt  32x16  4 loop   the First Ember's ember bolt (travels right)
    fx_sc_eburst 64x64  8        dark ember burst ring
Preview: art/previews/secrets_fx.png
"""
import math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
from envlib import C, K, T, h01, outline, blank, scale  # noqa: E402

BUILD = "--preview" not in sys.argv
GOLD = [C("3a2616"), C("6a4630"), C("8e6038"), C("b4843e"), C("d4a44a"), C("ecc466"), C("f8e098"), C("fff6d0")]
STONE = [C("15121a"), C("221d26"), C("302a33"), C("403842"), C("524852"), C("665a62"), C("7e7078"), C("988a8e")]
ASH = [C("1c191c"), C("2c282c"), C("3e393c"), C("544e50"), C("6e6766"), C("8c8480"), C("aca39c"), C("ccc3b8")]
EMB = [C("3a0c06"), C("6a1a0a"), C("a02a0c"), C("e0561a"), C("ff9a3a"), C("ffd88a"), C("fff4d8")]
WOOD = [C("140d0a"), C("22160f"), C("342216"), C("4a3220"), C("64462c"), C("7e5c3a")]
CRIM = [C("1a0708"), C("34101a"), C("521824"), C("76202c"), C("98303a"), C("b84a48")]
IRON = [C("0e0c12"), C("1c1920"), C("2e2a32"), C("444048"), C("5e5a62"), C("807a84")]
REED = [C("2a2214"), C("3e321c"), C("564628"), C("6e5a34"), C("8a7444"), C("a89058")]
CLAY = [C("2a140c"), C("4a2414"), C("6a361c"), C("8a4c28"), C("a8663a")]
WIND = [C("3a3a46"), C("6a6a7a"), C("a4a4b2"), C("d8d8e2"), C("f6f6fa")]
BLACK = [C("060306"), C("0e0708"), C("1a0c0c")]


def put(px, w, h, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < w and 0 <= y < h and c is not None:
        px[x, y] = c


# =========================================================================== props
def seal():
    """A gold sigil etched into the rock (transparent elsewhere): circle, inner star-knot, four rune ticks."""
    w, h = 32, 48
    frames = []
    cx, cy = 16.0, 24.0

    def glyph(img, bright, crack=0.0, drop=0.0):
        px = img.load()
        cols = GOLD[2:6] if bright == 0 else GOLD[3:8] if bright == 1 else GOLD[4:8]
        for y in range(h):
            for x in range(w):
                dx, dy = x + .5 - cx, y + .5 - cy
                r = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                on = False
                if 10.2 <= r <= 11.4:
                    on = True
                if 7.4 <= r <= 8.0 and int((a + 3.2) * 4) % 3 != 0:
                    on = True
                # a four-lobed knot
                k = abs(math.cos(2 * a)) * 6.2
                if abs(r - k) < 0.6 and r > 1.5:
                    on = True
                if r < 1.2:
                    on = True
                for t in range(4):                          # rune ticks on the circle
                    ta = t * math.pi / 2 + math.pi / 4
                    if abs(a - ta) < 0.08 and 11.4 < r < 14.2:
                        on = True
                if not on:
                    continue
                if crack and h01(int(x / 3), int(y / 3), 71) < crack:
                    continue
                yy = y + int(drop * (1 + h01(int(x / 3), int(y / 3), 72) * 6)) if drop else y
                if 0 <= yy < h:
                    c = cols[min(len(cols) - 1, int((1 - r / 15) * len(cols)) + (1 if (x + y) % 5 == 0 else 0))]
                    px[x, yy] = c
        return img
    for i in range(6):
        img = blank(w, h)
        glyph(img, 0)
        px = img.load()
        for k in range(3):                                # faint motes
            t = (i / 6 + k / 3) % 1
            put(px, w, h, cx - 6 + k * 6, cy + 10 - t * 20, GOLD[4])
        frames.append({"ms": 160, "cels": {"Seal": img}})
    for i in range(4):
        img = blank(w, h)
        glyph(img, 2 if i < 2 else 1)
        px = img.load()
        for a in range(0, 360, 30):
            rr = 13 + i * 2
            put(px, w, h, cx + math.cos(math.radians(a)) * rr, cy + math.sin(math.radians(a)) * rr, GOLD[6 - i])
        frames.append({"ms": (40, 60, 80, 100)[i], "cels": {"Seal": img}})
    for i in range(8):
        img = blank(w, h)
        if i < 5:
            glyph(img, 2 if i < 2 else 1, crack=0.12 + i * 0.16, drop=i * 0.6)
        px = img.load()
        for k in range(24):                                 # gold shards flung out of the wall
            a = h01(k, 1, 90) * 6.28
            rr = 4 + i * (2.5 + h01(k, 2, 90) * 3)
            x = cx + math.cos(a) * rr + i * 1.2
            y = cy + math.sin(a) * rr + i * i * 0.35
            if i < 7 or k % 2:
                put(px, w, h, x, y, GOLD[max(2, 7 - i)])
        frames.append({"ms": (50, 60, 70, 80, 90, 100, 120, 160)[i], "cels": {"Seal": img}})
    return (w, h, ["Seal"], frames, [("idle", 0, 5), ("flare", 6, 9), ("shatter", 10, 17)])


def campfire():
    w, h = 32, 32
    frames = []
    for i in range(6):
        base = blank(w, h)
        px = base.load()
        # ring of stones
        for k, sx in enumerate((4, 8, 12, 18, 22, 26)):
            r = 2.2 + (k % 2) * 0.6
            for y in range(28, 32):
                for x in range(sx - 3, sx + 4):
                    if ((x - sx) / (r + 0.6)) ** 2 + ((y - 30) / 2.0) ** 2 <= 1:
                        px[x, y] = STONE[5 if y < 29 else 3 if x < sx + 1 else 2]
        # charred logs crossed
        for (x0, y0, x1, y1) in ((8, 29, 23, 25), (24, 29, 10, 25)):
            n = 20
            for k in range(n + 1):
                t = k / n
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                for d in (-1, 0, 1):
                    put(px, w, h, x, y + d, WOOD[1] if d < 0 else WOOD[2] if d == 0 else WOOD[0])
                if k % 5 == 2:
                    put(px, w, h, x, y, EMB[3])
        base = outline(base)
        fl = blank(w, h)
        fp = fl.load()
        # flames: 3 tongues flickering
        for t_i, (fx0, hh) in enumerate(((16, 15), (12, 10), (20, 11))):
            hh = hh + int(3 * math.sin(i * 1.3 + t_i * 2.1))
            for y in range(27 - hh, 28):
                tt = (27 - y) / max(1, hh)
                half = (1 - tt) ** 0.8 * (3.2 if t_i == 0 else 2.2) + 0.3
                wob = math.sin(i * 1.7 + tt * 5 + t_i) * 1.2 * tt
                for x in range(int(fx0 - half - 2), int(fx0 + half + 3)):
                    dx = abs(x + .5 - (fx0 + wob))
                    if dx <= half:
                        rr = dx / max(half, 0.5) * 0.5 + tt * 0.8
                        c = EMB[6] if rr < 0.3 else EMB[5] if rr < 0.55 else EMB[4] if rr < 0.8 else EMB[3] if rr < 1.05 else EMB[2]
                        put(fp, w, h, x, y, c)
        for k in range(3):
            t = (i / 6 + k * 0.33) % 1
            put(fp, w, h, 14 + k * 3 + math.sin(t * 6) * 2, 12 - t * 12, EMB[4] if t < 0.5 else EMB[3])
        frames.append({"ms": 100, "cels": {"Base": base, "Flame": fl}})
    return (w, h, ["Base", "Flame"], frames, [("loop", 0, 5)])


def mat():
    w, h = 32, 16
    img = blank(w, h)
    px = img.load()
    for y in range(12, 15):
        for x in range(2, 30):
            c = REED[3] if (x + (y % 2)) % 3 else REED[2]
            if y == 12:
                c = REED[4] if x % 4 else REED[3]
            if x in (2, 29):
                c = REED[1]
            px[x, y] = c
    for x in range(3, 29, 6):
        px[x, 12] = CRIM[3]
    # clay bowl
    for y in range(8, 12):
        for x in range(21, 28):
            if ((x - 24) / 3.4) ** 2 + ((y - 8) / 3.4) ** 2 <= 1:
                px[x, y] = CLAY[3] if x < 24 else CLAY[2]
    for x in range(21, 28):
        px[x, 8] = CLAY[4] if x < 26 else CLAY[3]
    px[23, 8], px[24, 8] = CLAY[1], CLAY[1]
    # incense stick in a little stand
    for y in range(3, 12):
        px[8, y] = WOOD[3] if y > 4 else EMB[4]
    px[7, 11], px[9, 11] = STONE[4], STONE[3]
    img = outline(img)
    return (w, h, ["Mat"], [{"ms": 1000, "cels": {"Mat": img}}], [("idle", 0, 0)])


def cairn():
    w, h = 16, 24
    img = blank(w, h)
    px = img.load()
    y = 23
    for k, (rw, rh) in enumerate(((6.2, 2.6), (5.0, 2.2), (4.2, 2.0), (3.2, 1.8), (2.2, 1.4))):
        cx = 8 + (0.6 if k % 2 else -0.4)
        cy = y - rh
        for yy in range(int(cy - rh - 1), int(cy + rh + 1)):
            for xx in range(int(cx - rw - 1), int(cx + rw + 2)):
                if ((xx + .5 - cx) / rw) ** 2 + ((yy + .5 - cy) / rh) ** 2 <= 1:
                    lit = (xx + .5 - cx) < -rw * 0.2 and (yy + .5 - cy) < 0
                    px[xx, yy] = STONE[6 if lit else 4 if (yy + .5 - cy) < rh * 0.4 else 2]
        y = int(cy - rh + 1)
    img = outline(img)
    px = img.load()
    for yy in range(2, 8):                               # a stick with a scrap of cloth
        px[10, yy] = WOOD[3]
    for yy in range(2, 5):
        for xx in range(11, 14 - (yy - 2)):
            px[xx, yy] = CRIM[4] if yy == 2 else CRIM[3]
    return (w, h, ["Cairn"], [{"ms": 1000, "cels": {"Cairn": img}}], [("idle", 0, 0)])


def banner():
    """A tall pike with a tattered crimson war banner (faded gold sigil) and a small iron bell."""
    w, h = 32, 64
    frames = []

    def draw(i, mode):
        img = blank(w, h)
        px = img.load()
        # pike
        for y in range(4, 64):
            px[10, y] = IRON[3]
            px[11, y] = IRON[1]
        for y in range(0, 5):                              # spearhead
            for x in range(9, 13):
                if abs(x + .5 - 11) <= (y + 1) * 0.45:
                    px[x, y] = IRON[5] if x < 11 else IRON[3]
        for x in range(7, 15):                             # crossbar
            px[x, 8] = WOOD[3]
            px[x, 9] = WOOD[1]
        # banner cloth
        droop = mode == "spent"
        for y in range(9, 48 if not droop else 40):
            t = (y - 9) / 38
            wave = math.sin(t * 5 + i * 1.1) * (1.5 + t * 2) if not droop else math.sin(t * 3) * 0.6
            x0 = 12
            x1 = 12 + (14 if not droop else 7) - int(t * 2) + wave
            for x in range(x0, int(x1) + 1):
                if y > 36 and h01(x, y // 2, 5) < (y - 36) / 12 + (0.35 if droop else 0):
                    continue                              # tattered hem
                c = CRIM[3] if (x + int(wave)) % 5 else CRIM[2]
                if x == x0:
                    c = CRIM[1]
                if y == 9:
                    c = CRIM[4]
                px[x, y] = c
        # faded gold sigil: crossed blades inside a ring
        if not droop:
            scx, scy = 18.0 + math.sin(i * 1.1 + 2) * 1.2, 22.0
            for a in range(0, 360, 20):
                put(px, w, h, scx + math.cos(math.radians(a)) * 4.2, scy + math.sin(math.radians(a)) * 4.2, GOLD[3])
            for k in range(-3, 4):
                put(px, w, h, scx + k, scy + k, GOLD[4])
                put(px, w, h, scx + k, scy - k, GOLD[4])
        # bell on a short chain from the crossbar
        bx = 8
        sw = {"ring": (0, 3, -3, 2, -1, 0)[i % 6], "idle": 0, "spent": 0}[mode]
        for y in range(10, 13):
            px[bx, y] = IRON[3]
        for y in range(13, 19):
            half = 1 + (y - 13) * 0.45
            for x in range(int(bx - half - 1), int(bx + half + 2)):
                if abs(x + .5 - (bx + .5 + sw * (y - 12) / 6)) <= half:
                    put(px, w, h, x, y, IRON[4] if x < bx + sw * 0.5 else IRON[2])
        put(px, w, h, bx + sw, 19, GOLD[4])
        img = outline(img)
        if mode == "ring" and i in (1, 2, 3):
            p2 = img.load()
            for a in range(0, 360, 40):
                rr = 6 + i * 2
                put(p2, w, h, bx + math.cos(math.radians(a)) * rr, 16 + math.sin(math.radians(a)) * rr, GOLD[6])
        return img
    for i in range(6):
        frames.append({"ms": 140, "cels": {"Banner": draw(i, "idle")}})
    for i in range(6):
        frames.append({"ms": 80, "cels": {"Banner": draw(i, "ring")}})
    frames.append({"ms": 1000, "cels": {"Banner": draw(0, "spent")}})
    return (w, h, ["Banner"], frames, [("idle", 0, 5), ("ring", 6, 11), ("spent", 12, 12)])


def ashes():
    w, h = 48, 16
    frames = []
    for i in range(6):
        img = blank(w, h)
        px = img.load()
        for x in range(2, 46):
            t = (x - 24) / 22
            top = 15 - int(7 * (1 - t * t) ** 1.2 + 1.2 * math.sin(x * 0.7))
            for y in range(max(0, top), 16):
                d = y - top
                c = ASH[6] if d == 0 else ASH[5] if d < 2 else ASH[4] if d < 4 else ASH[3]
                if h01(x, y, 3) < 0.12:
                    c = ASH[2]
                px[x, y] = c
        img = outline(img)
        px = img.load()
        for k in range(9):                                  # ember glints breathing in the ash
            x = 6 + int(h01(k, 1, 7) * 36)
            y = 10 + int(h01(k, 2, 7) * 5)
            on = (math.sin(i * 1.05 + k * 1.7) + 1) / 2
            if on > 0.35 and px[x, y][3]:
                px[x, y] = EMB[3 if on < 0.7 else 4]
        frames.append({"ms": 150, "cels": {"Ash": img}})
    return (w, h, ["Ash"], frames, [("loop", 0, 5)])


# =========================================================================== fx
def whirl():
    w, h = 32, 40
    frames = []
    for i in range(6):
        img = blank(w, h)
        px = img.load()
        for s in range(3):
            prev = None
            for yy in range(64, 3, -1):
                y = yy / 2
                t = (32 - y) / 30                                  # 0 bottom .. 1 top
                rx = 2.0 + t * 10.5
                ph = y * 0.32 + s * 2.09 + i * 1.05
                x = 16 + math.sin(ph) * rx + math.sin(y * 0.2 + i * 0.7) * 1.2
                depth = math.cos(ph)
                if depth < -0.55:
                    continue
                c = WIND[4] if depth > 0.75 else WIND[3] if depth > 0.3 else WIND[2] if depth > -0.1 else WIND[1]
                put(px, w, h, x, y, c)
                if depth > 0.4 and t > 0.3:
                    put(px, w, h, x + 1, y, WIND[2])
        for k in range(10):                                     # dust kicked at the base
            a = h01(k, i, 3) * 6.28
            put(px, w, h, 16 + math.cos(a) * (5 + k * 0.8), 32 - abs(math.sin(a)) * 3, ASH[4] if k % 2 else ASH[5])
        frames.append({"ms": 70, "cels": {"FX": img}})
    return (w, h, ["FX"], frames, [("sc_whirl", 0, 5)])


def gust():
    w, h = 64, 32
    frames = []
    for i in range(5):
        img = blank(w, h)
        px = img.load()
        for k in range(14):
            y = 6 + int(h01(k, 1, 5) * 20)
            L = 10 + int(h01(k, 2, 5) * 24) - i * 3
            x0 = 40 - i * 7 - int(h01(k, 3, 5) * 10)
            for x in range(x0, x0 + max(2, L)):
                t = (x - x0) / max(1, L)
                if i > 2 and h01(x, y, i) < 0.4:
                    continue
                put(px, w, h, x, y + math.sin(x * 0.3 + k) * 0.8, WIND[3] if t > 0.7 else WIND[2] if t > 0.35 else WIND[1])
        frames.append({"ms": (50, 60, 70, 80, 90)[i], "cels": {"FX": img}})
    return (w, h, ["FX"], frames, [("sc_gust", 0, 4)])


def crescent(pal, core_black=False, name="x"):
    w, h = 48, 32
    frames = []
    for i in range(4):
        img = blank(w, h)
        px = img.load()
        ox = 24 + i * 2
        rx, ry, th = 14 + i, 14.0, 7.0 - i * 0.6
        for y in range(h):
            for x in range(w):
                ux, uy = (x + .5 - ox) / rx, (y + .5 - 16) / ry
                d = math.hypot(ux, uy)
                if d > 1:
                    continue
                ix = (x + .5 - (ox - th)) / rx
                if math.hypot(ix, uy) <= 1:
                    continue
                edge = (1 - d) * rx
                if edge < 1.0:
                    c = pal[-1]
                elif edge < 2.2:
                    c = pal[-2]
                elif edge < 4.0:
                    c = pal[-3] if not core_black else BLACK[2]
                else:
                    c = pal[-4] if not core_black else BLACK[1 if (x + y) % 2 else 0]
                if i == 3 and h01(x, y, 5) < 0.3:
                    continue
                px[x, y] = c
        for k in range(8):
            put(px, w, h, ox - th - 2 - h01(k, i, 3) * 8, 16 + (h01(k, i, 4) - 0.5) * 22, pal[-2] if k % 2 else pal[-3])
        frames.append({"ms": 60, "cels": {"FX": img}})
    return (w, h, ["FX"], frames, [(name, 0, 3)])


def ebolt():
    w, h = 32, 16
    frames = []
    for i in range(4):
        img = blank(w, h)
        px = img.load()
        for x in range(4, 28):
            t = (27 - x) / 23                                   # 0 head .. 1 tail
            half = (1 - t) * 3.4 + 0.4
            for y in range(h):
                dy = abs(y + .5 - 8 - math.sin(x * 0.6 + i * 1.6) * t * 1.8)
                if dy <= half and h01(x, y, i) > t * 0.55:
                    r = dy / max(half, 0.5)
                    c = BLACK[1] if r < 0.35 and t < 0.5 else EMB[5] if r < 0.55 else EMB[4] if r < 0.8 else EMB[3] if t < 0.6 else EMB[2]
                    px[x, y] = c
        put(px, w, h, 27, 8, EMB[6])
        frames.append({"ms": 60, "cels": {"FX": img}})
    return (w, h, ["FX"], frames, [("sc_ebolt", 0, 3)])


def eburst():
    w, h = 64, 64
    frames = []
    for i in range(8):
        img = blank(w, h)
        px = img.load()
        R = 6 + i * 3.6
        th = max(1.5, 7 - i * 0.7)
        for y in range(h):
            for x in range(w):
                d = math.hypot(x + .5 - 32, y + .5 - 32)
                if R - th <= d <= R:
                    t = (d - (R - th)) / th
                    if i > 4 and h01(x, y, i) < (i - 4) * 0.22:
                        continue
                    c = EMB[5] if t > 0.75 else EMB[4] if t > 0.5 else EMB[3] if t > 0.25 else BLACK[2]
                    px[x, y] = c
                elif d < R - th and i < 3:
                    if h01(x, y, 9) < 0.25:
                        px[x, y] = BLACK[1]
        for k in range(16):
            a = k / 16 * 6.28 + i * 0.1
            rr = R + 2 + h01(k, i, 3) * 6
            put(px, w, h, 32 + math.cos(a) * rr, 32 + math.sin(a) * rr, EMB[4] if k % 2 else EMB[3])
        frames.append({"ms": (40, 50, 60, 70, 80, 90, 100, 120)[i], "cels": {"FX": img}})
    return (w, h, ["FX"], frames, [("sc_eburst", 0, 7)])


PROPS = {"sc_seal": seal, "sc_campfire": campfire, "sc_mat": mat, "sc_cairn": cairn, "sc_banner": banner, "sc_ashes": ashes}
FXS = {"fx_sc_whirl": whirl, "fx_sc_gust": gust,
       "fx_sc_cslash": lambda: crescent([EMB[1], EMB[2], EMB[3], EMB[4], EMB[5], EMB[6]], name="sc_cslash"),
       "fx_sc_ecres": lambda: crescent([EMB[1], EMB[2], EMB[3], EMB[4], EMB[5]], core_black=True, name="sc_ecres"),
       "fx_sc_ebolt": ebolt, "fx_sc_eburst": eburst}


def flatten(w, h, layers, fr):
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for n in layers:
        if n in fr["cels"]:
            out.alpha_composite(fr["cels"][n])
    return out


def main():
    rows = []
    built = {}
    for name, fn in list(PROPS.items()) + list(FXS.items()):
        w, h, layers, frames, tags = fn()
        built[name] = (w, h, layers, frames, tags)
        for (t, a, b) in tags:
            rows.append((name + ":" + t, w, h, [flatten(w, h, layers, frames[i]) for i in range(a, b + 1)]))
    k = 4
    rw = max(len(r[3]) * (r[1] * k + 6) for r in rows) + 200
    rh = sum(r[2] * k + 10 for r in rows) + 10
    sheet = Image.new("RGBA", (rw, rh), (86, 86, 94, 255))
    d = ImageDraw.Draw(sheet)
    y = 8
    for (lab, w, h, ims) in rows:
        d.text((6, y + 2), lab, fill=(235, 235, 235, 255))
        x = 200
        for im in ims:
            bg = Image.new("RGBA", (w, h), (60, 58, 66, 255))
            bg.alpha_composite(im)
            sheet.alpha_composite(scale(bg, k), (x, y))
            x += w * k + 6
        y += h * k + 10
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    sheet.save(os.path.join(ART, "previews", "secrets_fx.png"))
    if BUILD:
        for name, (w, h, layers, frames, tags) in built.items():
            asebuild.build(name, w, h, layers, frames, tags)
    print("built", len(built))


if __name__ == "__main__":
    main()
