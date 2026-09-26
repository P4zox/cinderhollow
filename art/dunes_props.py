"""Props for the `dunes` biome (built by gen_dunes_env.py).

du_props    32x32: hatch (1) the sun-bronze hatch grate shut (top 7 rows), hatch_open (1) swung against the wall (8x28 at left)
du_stele    24x32: idle (4 loop) a hieroglyph stele, a faint gold glow pulsing in its sun-disc
du_altar    32x20: idle (1) / glow (4) a gold sun-disc mirror on a bronze ceiling bracket (pivot = top centre)
du_colossus 176x128: idle (1) the buried face of a colossal sun-king (nemes headcloth, sun-disc crown), painted into DU3's back
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, h01, clamp, blank, pick
from dunes_tiles import ST, SD, GD, LP, BZ, LN, outline_k

SH = (18, 10, 6, 255)


def frame(w, h, im):
    return {"ms": 120, "cels": {"Layer": im}}


# --------------------------------------------------------------------------- hatch
def hatch(open_=False):
    img = blank(32, 32)
    px = img.load()
    if open_:
        for y in range(2, 30):
            for x in range(1, 7):
                c = BZ[4] if x in (1,) else BZ[3] if x in (2, 5) else BZ[2]
                if y % 6 == 0:
                    c = GD[3]
                px[x, y] = c
        for y in (9, 21):
            px[3, y] = GD[5]; px[4, y] = GD[4]
        return outline_k(img)
    for y in range(7):
        for x in range(32):
            c = BZ[4] if y == 0 else BZ[3] if y == 1 else BZ[2]
            if 1 < y < 6 and x % 4 in (1, 2) and 1 < x < 30:
                c = BZ[0] if y > 2 else SD[2]
            if y == 6:
                c = K
            px[x, y] = c
    # a gilt sun-disc lock plate
    for y in range(1, 6):
        for x in range(12, 20):
            d = math.hypot(x + .5 - 16, y + .5 - 3.4)
            if d < 3.4:
                px[x, y] = GD[5] if d < 1.2 else GD[4] if x < 16 else GD[3]
    return outline_k(img)


# --------------------------------------------------------------------------- stele
def stele(f):
    img = blank(24, 32)
    px = img.load()
    for y in range(3, 32):
        for x in range(3, 21):
            # round-topped tablet on a plinth
            if y < 9 and (x + .5 - 12) ** 2 / 81 + (y + .5 - 9) ** 2 / 36 > 1:
                continue
            if y >= 28:
                if not (1 <= x <= 22):
                    continue
            c = ST[7] if x < 7 else ST[6] if x < 16 else ST[5]
            if x == 3 or (y < 9 and x < 8):
                c = ST[8]
            if y >= 28:
                c = ST[6] if y == 28 else ST[4]
            px[x, y] = c
    for y in range(28, 32):
        for x in range(1, 23):
            px[x, y] = ST[7] if y == 28 else ST[5] if x < 12 else ST[4]
    # the sun-disc with wings at the top
    glow = (0, 1, 2, 1)[f]
    for y in range(4, 10):
        for x in range(5, 19):
            d = math.hypot(x + .5 - 12, y + .5 - 7)
            if d < 2.4:
                px[x, y] = (GD[4], GD[5], GD[6])[glow]
            elif 5 < abs(x + .5 - 12) < 7.5 and 5.5 < y < 8.5:
                px[x, y] = GD[3] if y == 6 else GD[2]
    # hieroglyph rows (tiny carved signs)
    rows = [(12, "o| ~ ^"), (16, "~^ |o"), (20, "|o~ ^"), (24, "^ ~|o")]
    for (yy, sig) in rows:
        for x in range(5, 19):
            px[x, yy + 3] = ST[4]                               # register line
        for i, ch in enumerate(sig):
            x0 = 5 + i * 2 + (1 if yy % 8 else 0)
            if ch == "o":
                pts = [(x0, yy), (x0 + 1, yy), (x0, yy + 1), (x0 + 1, yy + 1)]
            elif ch == "|":
                pts = [(x0, yy - 1), (x0, yy), (x0, yy + 1), (x0, yy + 2)]
            elif ch == "~":
                pts = [(x0, yy + 1), (x0 + 1, yy), (x0 + 2, yy + 1)]
            elif ch == "^":
                pts = [(x0, yy + 1), (x0 + 1, yy), (x0 + 2, yy + 1)]
            else:
                pts = []
            for (x, y) in pts:
                if 4 < x < 20:
                    px[x, y] = ST[2]
                    if x + 1 < 20:
                        px[x + 1, y] = ST[8] if px[x + 1, y] != ST[2] else ST[2]
    # sand drifted against the base
    for x in range(0, 24):
        h = int(3 + 2 * math.sin(x * 0.4) - abs(x - 12) * 0.15)
        for y in range(32 - max(0, h), 32):
            px[x, y] = SD[7] if y == 32 - h else SD[6]
    return outline_k(img)


# --------------------------------------------------------------------------- altar mirror
def altar(glow):
    img = blank(32, 20)
    px = img.load()
    # bracket arms from the ceiling
    for y in range(0, 6):
        for x in (9, 22):
            px[x, y] = BZ[3]; px[x + 1, y] = BZ[2]
    for x in range(8, 24):
        px[x, 5] = BZ[4] if x < 16 else BZ[3]
    # the disc
    cx, cy, r = 15.5, 11.5, 6.6
    for y in range(4, 20):
        for x in range(6, 26):
            d = math.hypot(x + .5 - cx - 0.5, y + .5 - cy)
            if d < r:
                if d > r - 1.2:
                    c = GD[3]
                else:
                    k = (x + .5 - cx) * -0.12 + (y + .5 - cy) * -0.1
                    v = 3 + k + glow * 0.9
                    c = GD[int(clamp(round(v), 2, 6))]
                    if glow >= 2 and d < 2.5:
                        c = GD[6]
                px[x, y] = c
    # a lapis boss in the middle when idle
    if glow == 0:
        for (x, y) in ((15, 11), (16, 11), (15, 12), (16, 12)):
            px[x, y] = LP[3]
    out = outline_k(img)
    if glow:
        op = out.load()
        for i in range(8):                                  # rays
            a = i / 8 * 2 * math.pi + glow * 0.3
            for rr in (8, 9):
                x, y = int(round(16 + math.cos(a) * rr)), int(round(11.5 + math.sin(a) * rr * 0.9))
                if 0 <= x < 32 and 0 <= y < 20 and op[x, y][3] == 0:
                    op[x, y] = GD[5] if rr == 8 else GD[4]
    return out


# --------------------------------------------------------------------------- the buried colossus
def colossus():
    """A colossal sun-king's face buried to the lips: striped nemes headcloth flaring to the shoulders, a cobra brow ornament,
    a cracked sun-disc crown, hollow eyes rimmed in kohl, the nose broken off. Sandstone, weathered, one gilt band surviving.
    Light from the upper left (the rift). Transparent background; the bottom is hidden behind the dune front layer."""
    Wd, Hd = 176, 128
    img = blank(Wd, Hd)
    px = img.load()
    cx = 88
    STONE = ramp("150d08", "1f150d", "2b1d12", "3a2718", "4a321e", "5c3f25", "70502f", "86623a", "9c7548", "b18a58")

    def setp(x, y, lv):
        if 0 <= x < Wd and 0 <= y < Hd:
            px[x, y] = STONE[int(clamp(lv, 0, 9))]

    # nemes headcloth: from a rounded crown flaring out to lappets at the sides
    for y in range(30, Hd):
        t = (y - 30) / (Hd - 30)
        half = 38 + 26 * min(1, t * 1.6)
        for x in range(int(cx - half), int(cx + half) + 1):
            dx = (x - cx) / half
            stripe = int((y - 30 + abs(x - cx) * 0.35) / 5) % 2
            lv = 5.4 - dx * 1.6 + (0.8 if stripe else -0.3) - t * 0.8
            if abs(dx) > 0.92:
                lv -= 1.5
            if h01(x, y, 5) < 0.08:
                lv -= 1
            setp(x, y, lv)
    # rounded top of the headcloth
    for y in range(14, 34):
        for x in range(cx - 40, cx + 41):
            e = ((x - cx) / 40) ** 2 + ((y - 34) / 20) ** 2
            if e < 1:
                lv = 5.8 - (x - cx) / 40 * 1.5 - (y - 34) / 20 * -0.6 + (0.6 if int((y - 14) / 5) % 2 else -0.3)
                setp(x, y, lv)
    # the face (in front of the headcloth)
    for y in range(40, Hd):
        for x in range(cx - 26, cx + 27):
            dx = (x - cx) / 26
            if y < 52 and abs(dx) > 0.9 - (52 - y) * 0.02:
                continue
            jaw = y > 108 and abs(dx) > 1 - (y - 108) * 0.03
            if jaw:
                continue
            lv = 6.6 - dx * 2.2 - (0.6 if y > 100 else 0)
            # cheek planes and brow shadow
            if 58 <= y <= 62:
                lv -= 1.5
            if abs(dx) > 0.75:
                lv -= 0.8
            if h01(x, y, 9) < 0.06:
                lv -= 1
            setp(x, y, lv)
    # eyes: kohl-rimmed hollows
    for (ex, ey) in ((cx - 11, 68), (cx + 11, 68)):
        for y in range(ey - 5, ey + 5):
            for x in range(ex - 9, ex + 10):
                e = ((x - ex) / 9) ** 2 + ((y - ey) / 4.2) ** 2
                if e < 1:
                    setp(x, y, 0.5 if e < 0.55 else 2)
        for x in range(ex + 6, ex + 14):                        # the kohl wing
            setp(x if ex < cx else 2 * ex - x, ey + 1 + (x - ex - 6) // 3, 1)
    # broken nose (a jagged scar) and the lips at the sand line
    for y in range(74, 96):
        for x in range(cx - 5, cx + 6):
            if abs(x - cx) < 5 - (96 - y) * 0.1:
                setp(x, y, 7.5 - (x - cx) * 0.3 if y < 84 else 4)
    for x in range(cx - 7, cx + 6):                             # broken edge
        setp(x, 84 + int(h01(x, 1, 3) * 3), 1)
    for y in range(102, 110):
        for x in range(cx - 12, cx + 13):
            if abs(x - cx) < 12 - abs(y - 106) * 1.5:
                setp(x, y, 4.5 - (x - cx) * 0.08 if y < 106 else 3)
    # cobra ornament at the brow + a surviving gilt band across the forehead
    for y in range(44, 52):
        for x in range(cx - 20, cx + 21):
            if y in (47, 48) and px[x, y][3]:
                px[x, y] = GD[3] if (x // 3) % 2 else GD[2]
    for y in range(32, 50):
        for x in range(cx - 4, cx + 5):
            e = ((x - cx) / 4) ** 2 + ((y - 38) / 7) ** 2
            if e < 1:
                px[x, y] = GD[4] if x < cx else GD[3]
    # cracked sun-disc crown atop, half fallen
    for y in range(0, 22):
        for x in range(cx - 20, cx + 21):
            d = math.hypot(x - cx, y - 12)
            if d < 12 and not (x > cx + 3 and y < 10 + (x - cx) * 0.4):
                px[x, y] = GD[4] if d < 5 and x < cx else GD[3] if d < 10 else GD[2]
    for i in range(20):                                         # a crack through the face
        x = cx + 14 + int(math.sin(i * 0.7) * 2) - i // 4
        setp(x, 40 + i * 3, 0.5)
    # sand drifted into the headcloth folds and piled against the cheeks
    for y in range(Hd):
        for x in range(Wd):
            if px[x, y][3] and h01(x, y, 44) < 0.35 and (y > 100 or (y > 60 and abs(x - cx) > 40)):
                if y % 3 == 0 or h01(x, y, 45) < 0.3:
                    px[x, y] = SD[5] if x < cx else SD[4]
    return outline_k(img)


PROPS = {
    "du_props": lambda: (32, 32, ["Layer"], [frame(32, 32, hatch()), frame(32, 32, hatch(True))], [("hatch", 0, 0), ("hatch_open", 1, 1)]),
    "du_stele": lambda: (24, 32, ["Layer"], [{"ms": (400, 200, 400, 200)[f], "cels": {"Layer": stele(f)}} for f in range(4)], [("idle", 0, 3)]),
    "du_altar": lambda: (32, 20, ["Layer"], [frame(32, 20, altar(0))] + [{"ms": 80, "cels": {"Layer": altar(g)}} for g in (1, 2, 3, 2)],
                         [("idle", 0, 0), ("glow", 1, 4)]),
    "du_colossus": lambda: (176, 128, ["Layer"], [frame(176, 128, colossus())], [("idle", 0, 0)]),
}
