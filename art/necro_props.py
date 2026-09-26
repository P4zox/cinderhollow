"""Props for the `necropolis` biome. Each builder returns (w, h, layers, frames, tags) for asebuild.build().

nv_props     48x64, one tag per decor kind: candles(4 loop) skulls(1) brazier(4 loop) statue(1) coffin(1) banner(4 loop)
             block(1) gallows(1) throne(1). Bottom-anchored, except `banner` which hangs from its top edge.
nv_bell      32x40  idle(1) toll(6)   a bronze bell gone green-black, bone yoke; drawn hanging from its top centre
nv_bell_big  48x56  idle(1) toll(6)   the great bell of the Bone Spire
nv_walk      16x16  l m r s           bell walkway pieces: bone slats lashed on chains
nv_plat      48x12  idle(1)           a bell-hung bone platform (engine draws the chains)
"""
import math
from PIL import Image
from envlib import ramp, K, h01, clamp, blank
from necro_tiles import BN, GH, ST, IR, outline_k, SKULL

BR = ramp("0e0f0c", "1b1f18", "2b3326", "3d4a33", "566443", "7a845a")          # verdigris-black bronze
GD = ramp("24170c", "4a3113", "7a5419", "a87c2c", "d0a64a", "f0d68a")
PU = ramp("0e0714", "1c0d27", "2d1640", "43225c", "5e347a")                  # royal purple cloth
WD = ramp("100c0a", "1d1612", "2d231b", "3f3226", "564433")


def img(w, h):
    return blank(w, h)


def setp(px, w, h, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < w and 0 <= y < h:
        px[x, y] = c


def rect(px, w, h, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            setp(px, w, h, x, y, c)


def skull(px, w, h, ox, oy, lit=1.0):
    for j, row in enumerate(SKULL):
        for i, ch in enumerate(row):
            if ch == ".":
                lv = 5 if j < 2 else 4 if j < 5 else 3
                if i <= 1: lv += 1
                if i >= 6: lv -= 1
                setp(px, w, h, ox + i, oy + j, BN[int(clamp(lv * lit, 1, 7))])
            elif ch in "xo":
                setp(px, w, h, ox + i, oy + j, BN[0])
            elif ch == "t":
                setp(px, w, h, ox + i, oy + j, BN[2])


def flame(px, w, h, cx, base, size, f, seed=0):
    """Pale-blue ghost flame (FX colours, no outline)."""
    hh = size * 1.9
    for y in range(int(base - hh) - 1, int(base) + 1):
        t = (base - (y + .5)) / hh
        if t < 0 or t > 1:
            continue
        wob = math.sin(f * 1.7 + t * 5 + seed) * 0.8 * t
        half = size * 0.55 * (1 - t) ** 0.7 + 0.3
        for x in range(int(cx - half - 2), int(cx + half + 2)):
            dx = x + .5 - (cx + wob)
            if abs(dx) <= half:
                r = abs(dx) / max(half, 0.5) * 0.6 + t * 0.7
                if h01(x, y, int(f * 7 + seed)) < 0.12 * t:
                    continue
                c = GH[6] if r < 0.35 else GH[5] if r < 0.6 else GH[4] if r < 0.85 else GH[3] if r < 1.05 else GH[2]
                setp(px, w, h, x, y, c)


# ------------------------------------------------------------------------------------------------ nv_props (48x64)
PW, PH = 48, 64


def p_candles(f):
    im = img(PW, PH); px = im.load()
    for (x0, hgt) in ((14, 9), (19, 15), (24, 7), (28, 12), (33, 5)):
        rect(px, PW, PH, x0, PH - 2 - hgt, x0 + 1, PH - 2, BN[5])
        rect(px, PW, PH, x0 + 2, PH - 2 - hgt + 1, x0 + 2, PH - 2, BN[3])
        setp(px, PW, PH, x0, PH - 2 - hgt, BN[7])
    for x in range(11, 38):
        setp(px, PW, PH, x, PH - 1, BN[3] if h01(x, 1, 3) < 0.6 else BN[2])
        if h01(x, 2, 3) < 0.4:
            setp(px, PW, PH, x, PH - 2, BN[4])
    skull(px, PW, PH, 6, PH - 9, 0.9)
    im = outline_k(im)
    px = im.load()
    for i, (x0, hgt) in enumerate(((14, 9), (19, 15), (24, 7), (28, 12), (33, 5))):
        flame(px, PW, PH, x0 + 1.5, PH - 2 - hgt, 2.0, f + i * 1.3, i)
    return im


def p_skulls(f):
    im = img(PW, PH); px = im.load()
    for y in range(PH - 8, PH):
        for x in range(6, 42):
            e = ((x - 24) / 18) ** 2 + ((y - PH) / 8) ** 2
            if e < 1 and h01(x, y, 44) < 0.9:
                setp(px, PW, PH, x, y, BN[3] if h01(x, y, 9) < 0.5 else BN[2])
    for (x, y, l) in ((8, PH - 12, 0.9), (16, PH - 10, 0.8), (24, PH - 13, 1.0), (32, PH - 11, 0.85), (13, PH - 18, 1.0),
                      (21, PH - 20, 1.05), (28, PH - 18, 0.9), (18, PH - 26, 1.1)):
        skull(px, PW, PH, x, y, l)
    return outline_k(im)


def p_brazier(f):
    im = img(PW, PH); px = im.load()
    cx = 24
    # tripod of long bones
    for sgn in (-1, 0, 1):
        for i in range(22):
            x = cx + sgn * (i * 0.45)
            y = PH - 1 - i
            setp(px, PW, PH, x, y, BN[5] if sgn <= 0 else BN[3])
            if sgn:
                setp(px, PW, PH, x + sgn, y, BN[2])
        setp(px, PW, PH, cx + sgn * 10, PH - 1, BN[6])
    # bowl: a great skull-cap, iron-banded
    for y in range(PH - 30, PH - 22):
        t = (y - (PH - 30)) / 8
        half = 10 - t * 4
        for x in range(int(cx - half), int(cx + half) + 1):
            c = BN[5] if x < cx - half * 0.3 else BN[4] if x < cx + half * 0.4 else BN[2]
            if y == PH - 27:
                c = IR[4] if x < cx else IR[2]
            setp(px, PW, PH, x, y, c)
    im = outline_k(im)
    px = im.load()
    flame(px, PW, PH, cx, PH - 29, 5.5, f, 3)
    flame(px, PW, PH, cx - 4, PH - 29, 3.0, f + 2, 5)
    flame(px, PW, PH, cx + 4, PH - 29, 3.2, f + 4, 7)
    return im


def p_statue(f):
    """A weeping mourner: hooded stone figure, hands over a skull, a ghost tear."""
    im = img(PW, PH); px = im.load()
    cx = 24
    rect(px, PW, PH, cx - 10, PH - 6, cx + 10, PH - 1, ST[5])
    rect(px, PW, PH, cx - 10, PH - 6, cx + 10, PH - 6, ST[7])
    rect(px, PW, PH, cx + 7, PH - 5, cx + 10, PH - 1, ST[3])
    for y in range(PH - 48, PH - 6):
        t = (y - (PH - 48)) / 42
        half = 4 + 6 * t ** 0.8
        if y < PH - 40:
            half = 3.5 + (y - (PH - 48)) * 0.35
        for x in range(int(cx - half), int(cx + half) + 1):
            dx = (x - cx) / max(half, 1)
            lv = 7 if dx < -0.5 else 6 if dx < 0 else 5 if dx < 0.5 else 3
            if (x + y) % 9 == 0 and y > PH - 36:
                lv -= 1                       # robe folds
            setp(px, PW, PH, x, y, ST[lv])
    # hood opening (dark)
    rect(px, PW, PH, cx - 1, PH - 44, cx + 2, PH - 40, ST[1])
    setp(px, PW, PH, cx, PH - 41, GH[3])
    setp(px, PW, PH, cx, PH - 39, GH[4]); setp(px, PW, PH, cx, PH - 37, GH[3])
    skull(px, PW, PH, cx - 4, PH - 32, 0.85)
    rect(px, PW, PH, cx - 6, PH - 30, cx - 4, PH - 27, ST[7])
    rect(px, PW, PH, cx + 3, PH - 30, cx + 5, PH - 27, ST[5])
    return outline_k(im)


def p_coffin(f):
    im = img(PW, PH); px = im.load()
    # standing coffin leaning slightly, lid ajar
    pts = [(14, PH - 1), (34, PH - 1), (37, PH - 30), (31, PH - 40), (18, PH - 40), (11, PH - 30)]
    from enemy_kit import poly_mask
    m = poly_mask(pts)
    for (x, y) in m:
        dx = (x - 24) / 13
        c = WD[4] if dx < -0.5 else WD[3] if dx < 0.2 else WD[2]
        if (x - 12) % 7 == 0:
            c = WD[1]
        setp(px, PW, PH, x, y, c)
    for y in range(PH - 36, PH - 4):
        setp(px, PW, PH, 24, y, GD[2] if y % 4 else GD[3])
    for x in range(19, 30):
        setp(px, PW, PH, x, PH - 30, GD[2] if x % 3 else GD[3])
    skull(px, PW, PH, 20, PH - 27, 0.9)
    return outline_k(im)


def p_banner(f):
    """A royal banner of the Hollow Crown: tattered purple, a gold crown-and-skull device (hangs from the top)."""
    im = img(PW, PH); px = im.load()
    rect(px, PW, PH, 8, 0, 40, 2, BN[4])
    rect(px, PW, PH, 8, 2, 40, 2, BN[2])
    for x in range(12, 37):
        sway = math.sin(f * 1.5 + x * 0.12) * 1.2
        L = 44 + int(h01(x // 3, 1, f % 2 + 3) * 10) if (x // 3) % 2 else 40 + int(h01(x, 2, 5) * 6)
        for y in range(3, L):
            t = y / L
            xx = x + sway * t
            dx = (x - 24) / 12
            c = PU[3] if dx < -0.4 else PU[2] if dx < 0.5 else PU[1]
            if (x + int(y * 0.2)) % 6 == 0:
                c = PU[1]
            if x in (13, 35) or y == 5:
                c = GD[2]
            setp(px, PW, PH, xx, y, c)
    # crown over a skull
    for (x, y) in ((19, 14), (22, 12), (25, 11), (28, 12), (31, 14)):
        rect(px, PW, PH, x, y, x, 17, GD[4])
    rect(px, PW, PH, 19, 17, 31, 18, GD[3])
    skull(px, PW, PH, 21, 20, 1.0)
    return outline_k(im)


def p_block(f):
    """The headsman's block: a scarred stump with a notch, a basket of bone beside it."""
    im = img(PW, PH); px = im.load()
    for y in range(PH - 16, PH):
        for x in range(10, 32):
            dx = (x - 21) / 11
            c = WD[4] if dx < -0.4 else WD[3] if dx < 0.4 else WD[2]
            if y == PH - 16:
                c = WD[4]
            if (x * 3 + y) % 11 == 0:
                c = WD[1]
            setp(px, PW, PH, x, y, c)
    rect(px, PW, PH, 18, PH - 16, 24, PH - 14, (0, 0, 0, 0))
    rect(px, PW, PH, 18, PH - 13, 24, PH - 13, WD[1])
    for y in range(PH - 10, PH):
        for x in range(33, 44):
            c = WD[3] if (x + y) % 3 else WD[1]
            setp(px, PW, PH, x, y, c)
    skull(px, PW, PH, 34, PH - 15, 0.85)
    return outline_k(im)


def p_gallows(f):
    im = img(PW, PH); px = im.load()
    rect(px, PW, PH, 8, 2, 11, PH - 1, WD[3]); rect(px, PW, PH, 11, 2, 11, PH - 1, WD[1])
    rect(px, PW, PH, 8, 2, 42, 5, WD[3]); rect(px, PW, PH, 8, 5, 42, 5, WD[1])
    for i in range(10):
        rect(px, PW, PH, 12 + i, 6 + i, 13 + i, 6 + i, WD[2])
    # chain + shackle cage
    for y in range(6, 34):
        setp(px, PW, PH, 36, y, IR[4] if y % 3 else IR[2])
    for y in range(34, 50):
        t = (y - 34) / 16
        hw = 1 + 5 * math.sin(t * math.pi)
        setp(px, PW, PH, 36 - hw, y, IR[4]); setp(px, PW, PH, 36 + hw, y, IR[2])
        if y in (38, 44):
            rect(px, PW, PH, 36 - hw, y, 36 + hw, y, IR[3])
    skull(px, PW, PH, 32, 40, 0.8)
    rect(px, PW, PH, 4, PH - 3, 16, PH - 1, ST[5])
    return outline_k(im)


def p_throne(f):
    """The Hollow Throne: a tall seat of fused bone and corroded gold, a crown of spines."""
    im = img(PW, PH); px = im.load()
    cx = 24
    # back: tall with spines
    for y in range(6, PH - 8):
        t = (y - 6) / (PH - 14)
        half = 11 - 3 * (1 - t)
        for x in range(int(cx - half), int(cx + half) + 1):
            dx = (x - cx) / half
            c = BN[5] if dx < -0.5 else BN[4] if dx < 0.3 else BN[3]
            if abs(x - cx) in (4, 8) and y > 10:
                c = BN[2]
            setp(px, PW, PH, x, y, c)
    for i, x in enumerate((cx - 10, cx - 6, cx - 2, cx + 2, cx + 6, cx + 10)):
        hh = (8, 12, 16, 16, 12, 8)[i]
        for y in range(6 - hh, 7):
            setp(px, PW, PH, x, y, BN[6] if x < cx else BN[4])
    # seat + arms of gold
    rect(px, PW, PH, cx - 14, PH - 26, cx + 14, PH - 22, GD[3])
    rect(px, PW, PH, cx - 14, PH - 22, cx + 14, PH - 22, GD[1])
    rect(px, PW, PH, cx - 16, PH - 34, cx - 13, PH - 22, GD[4])
    rect(px, PW, PH, cx + 13, PH - 34, cx + 16, PH - 22, GD[2])
    for y in range(PH - 22, PH - 1):
        for x in (cx - 13, cx - 12, cx + 12, cx + 13):
            setp(px, PW, PH, x, y, BN[4] if x < cx else BN[2])
    rect(px, PW, PH, cx - 18, PH - 3, cx + 18, PH - 1, ST[6])
    rect(px, PW, PH, cx - 18, PH - 3, cx + 18, PH - 3, ST[8])
    skull(px, PW, PH, cx - 4, 16, 1.0)
    setp(px, PW, PH, cx - 2, 19, GH[4]); setp(px, PW, PH, cx + 2, 19, GH[4])
    return outline_k(im)


def nv_props():
    kinds = [("candles", p_candles, 4, 140), ("skulls", p_skulls, 1, 400), ("brazier", p_brazier, 4, 120),
             ("statue", p_statue, 1, 400), ("coffin", p_coffin, 1, 400), ("banner", p_banner, 4, 220),
             ("block", p_block, 1, 400), ("gallows", p_gallows, 1, 400), ("throne", p_throne, 1, 400)]
    frames, tags = [], []
    for name, fn, n, ms in kinds:
        a = len(frames)
        for f in range(n):
            frames.append({"ms": ms, "cels": {"Prop": fn(f)}})
        tags.append((name, a, len(frames) - 1))
    return PW, PH, ["Prop"], frames, tags


# ------------------------------------------------------------------------------------------------ bells
def bell_img(w, h, swing_k, f, big=False):
    im = img(w, h); px = im.load()
    cx = w / 2
    # yoke of bone at the top
    rect(px, w, h, cx - (8 if big else 6), 0, cx + (8 if big else 6), 2, BN[5])
    rect(px, w, h, cx - (8 if big else 6), 2, cx + (8 if big else 6), 2, BN[2])
    rect(px, w, h, cx - 1, 3, cx + 1, 5, IR[3])
    top, bot = 5, h - 5
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        half = (w * 0.18) + (w * 0.3) * t ** 1.8
        if y > bot - 2:
            half += 1.5
        for x in range(int(cx - half), int(cx + half) + 1):
            dx = (x + .5 - cx) / max(half, 1)
            lv = 4 if dx < -0.55 else 3 if dx < -0.1 else 2 if dx < 0.45 else 1
            if y in (top + 3, int(top + (bot - top) * 0.62), bot - 2):
                lv += 1                        # raised bands
            c = BR[int(clamp(lv, 0, 5))]
            if (y + x * 2) % 13 == 0 and dx > -0.5:
                c = BR[1]
            if abs(dx) < 0.12 and top + 6 < y < bot - 6 and (y // 2) % 3 == 0:
                c = GD[2]                        # a worn gold inscription
            setp(px, w, h, x, y, c)
    # mouth
    rect(px, w, h, cx - (w * 0.48) + 2, bot + 1, cx + (w * 0.48) - 2, bot + 1, BR[0])
    im = outline_k(im)
    px = im.load()
    # clapper (a skull on a chain) swinging inside the mouth
    clx = cx + math.sin(swing_k) * (w * 0.2)
    for y in range(bot - 6, bot + 2):
        setp(px, w, h, clx, y, IR[4])
    skull(px, w, h, int(clx - 3), bot, 1.0) if big else None
    if not big:
        rect(px, w, h, clx - 1, bot + 1, clx + 1, bot + 3, BN[5])
    # ghost glow on strike frames
    if f in (1, 2):
        for k in range(3):
            y = bot + 2 - k
            for x in range(int(cx - w * 0.45), int(cx + w * 0.45)):
                if h01(x, y, f + k) < 0.4 - k * 0.1:
                    setp(px, w, h, x, y, GH[5 - k])
    return im


def bell(big=False):
    w, h = (48, 56) if big else (32, 40)
    frames = [{"ms": 400, "cels": {"Bell": bell_img(w, h, 0, 0, big)}}]
    for f, sk in enumerate((0.9, -0.7, 0.5, -0.3, 0.15, 0)):
        frames.append({"ms": 90 if f < 2 else 130, "cels": {"Bell": bell_img(w, h, sk * 1.6, f + 1 if f < 2 else 0, big)}})
    return w, h, ["Bell"], frames, [("idle", 0, 0), ("toll", 1, 6)]


# ------------------------------------------------------------------------------------------------ walkway + platform
def walk_piece(kind):
    """A bone walkway plank-run occupying the top of its tile (the player stands on the tile top)."""
    im = img(16, 16); px = im.load()
    for x in range(16):
        slat = x % 4 == 3
        for y in range(0, 7):
            if y == 0:
                c = BN[6] if not slat else BN[3]
            elif y < 3:
                c = BN[4] if not slat else BN[2]
            elif y < 5:
                c = BN[3] if not slat else BN[1]
            elif y == 5:
                c = BN[2]
            else:
                c = K
            px[x, y] = c
    for x in range(16):                       # binding chain along the side
        if x % 3 == 0:
            px[x, 3] = IR[4]
        elif x % 3 == 1:
            px[x, 3] = IR[2]
    for x in (5, 11):                         # little bone pendants underneath
        for y in range(7, 7 + (3 if x == 5 else 2)):
            px[x, y] = BN[4]
    if kind in ("l", "s"):
        for y in range(0, 11):
            px[0, y] = BN[6] if y < 3 else BN[4]
            px[1, y] = BN[4] if y > 5 else px[1, y]
    if kind in ("r", "s"):
        for y in range(0, 11):
            px[15, y] = BN[3]
            px[14, y] = BN[2] if y > 5 else px[14, y]
    return outline_k(im)


def walk():
    frames = [{"ms": 100, "cels": {"Walk": walk_piece(k)}} for k in ("l", "m", "r", "s")]
    return 16, 16, ["Walk"], frames, [("l", 0, 0), ("m", 1, 1), ("r", 2, 2), ("s", 3, 3)]


def plat():
    w, h = 48, 12
    im = img(w, h); px = im.load()
    for x in range(1, w - 1):
        for y in range(0, 7):
            slat = x % 6 == 5
            c = (BN[6], BN[5], BN[4], BN[4], BN[3], BN[2], K)[y]
            if slat and 0 < y < 6:
                c = BN[1]
            px[x, y] = c
    for x in (4, 43):
        for y in range(0, 3):
            px[x, y] = IR[4]
    # a hanging skull beneath each end, and a small ghost lamp in the middle
    for x0 in (3, 38):
        for j, row in enumerate(SKULL[:6]):
            for i, ch in enumerate(row):
                if ch == "." and 7 + j < h:
                    px[x0 + i, 7 + j - 1] = BN[4] if j < 3 else BN[3]
                elif ch in "xo" and 7 + j < h:
                    px[x0 + i, 7 + j - 1] = BN[0]
    im = outline_k(im)
    px = im.load()
    px[24, 8] = GH[5]; px[23, 8] = GH[4]; px[24, 9] = GH[4]
    return w, h, ["Plat"], [{"ms": 400, "cels": {"Plat": im}}], [("idle", 0, 0)]


PROPS = {
    "nv_props": nv_props,
    "nv_bell": lambda: bell(False),
    "nv_bell_big": lambda: bell(True),
    "nv_walk": walk,
    "nv_plat": plat,
}
