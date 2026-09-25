"""Environment props (biome-neutral). Each returns (w, h, layers, frames, tags) for asebuild.

Face right, bottom-anchored, horizontally centred. 1px K outline, light from upper-left.
"""
import math, random
from PIL import Image
from envlib import C, ramp, K, T, bt, h01, pick, smooth, clamp, blank, outline

STONE = ramp("1e1c24", "2e2b35", "423e4a", "5a5562", "76707c", "9a929c", "b8b0b4")
WARM = ramp("2a2024", "403028", "5e4634", "806040", "a88450", "d0aa66", "ecd08a")   # stone lit by fire
GOLD = ramp("5a3c14", "8a6224", "c09440", "ecc870", "fff0b8", "ffffff")
IRON = ramp("15131b", "2e2a33", "4a4550", "736c74", "a39aa0")
CRIM = ramp("3a0a14", "6a1420", "a0202e", "e04050", "ff8a8a", "ffd8d0")
WOOD = ramp("1e1512", "3a2a20", "58402c", "7a5a3c", "9c7a52")
CLAY = ramp("2a1c1c", "4a3028", "6e4a38", "94684c", "b88c68")


class Spr:
    """Tiny canvas with helpers; draws opaque pixels into an RGBA image."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = blank(w, h)
        self.px = self.img.load()

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return T

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def shaded_rect(self, x0, y0, x1, y1, r, base=3):
        """Box lit from upper-left: top row +2, left col +1, right col -1, bottom -1."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                i = base
                if y == y0:
                    i += 2
                elif y == y1:
                    i -= 1
                if x == x0 and y != y0:
                    i += 1
                elif x == x1:
                    i -= 1
                self.set(x, y, r[max(0, min(len(r) - 1, i))])

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.set(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def outline(self, diag=False):
        self.img = outline(self.img, K, diag=diag)
        self.px = self.img.load()
        return self


def flame(s, cx, base_y, h, w, phase, pal=GOLD, seed=0):
    """Teardrop flame with a licking tip, flickering with phase (0..1, loops). Clean colour bands."""
    P = phase * 2 * math.pi
    for y in range(int(base_y - h * 1.2) - 2, int(base_y) + 1):
        t = (base_y - y) / h                       # 0 at base, 1 at tip
        if t < 0 or t > 1.2:
            continue
        sway = (math.sin(P + t * 3.2 + seed) * 1.2 + math.sin(2 * P + t * 5 + seed * 2) * 0.5) * t
        body = math.sin(math.pi * min(1.0, 0.2 + t * 0.8)) ** 0.7
        hw = w * body * max(0.0, 1.05 - t) ** 0.6
        hw *= 1 + 0.1 * math.sin(2 * P + seed + t * 4)
        for x in range(int(cx - w - 4), int(cx + w + 5)):
            dx = abs(x + 0.5 - cx - sway)
            if dx > hw:
                continue
            k = 1 - dx / max(hw, 0.4)             # 1 at centre
            v = 0.15 + 0.55 * k * (1 - 0.6 * t) + 0.35 * (1 - t)
            i = int(clamp(v) * (len(pal) - 1) + 0.5)
            s.set(x, y, pal[min(len(pal) - 1, i)])
    # a detached tongue above the tip on some frames
    if math.sin(P + seed) > 0.2:
        tx = cx + math.sin(P * 1.0 + seed) * 1.5
        ty = base_y - h * 1.15 - 1
        s.set(tx, ty, pal[2])
        s.set(tx, ty + 1, pal[1])


# =========================================================================== shrine
def shrine():
    Wd, Hd = 48, 64
    layers = ["Stone", "Statue", "Brazier", "Flame"]

    def stone(lit):
        s = Spr(Wd, Hd)
        R = WARM if lit else STONE
        # stepped plinth
        s.shaded_rect(2, 56, 45, 63, STONE, 2)
        s.shaded_rect(5, 50, 42, 56, STONE, 3)
        for x in range(6, 42, 6):           # joints
            s.set(x, 53, STONE[1])
            s.set(x + 3, 59, STONE[0])
        # carved gold filigree band on the upper step
        for x in range(8, 40):
            if x % 4 == 0:
                s.set(x, 52, GOLD[1])
            elif x % 4 == 2:
                s.set(x, 53, GOLD[0])
        if lit:                               # firelight on the plinth top near the brazier
            for x in range(18, 44):
                a = 1 - abs(x - 34) / 14
                if a > bt(x, 50) * 0.8:
                    s.set(x, 50, WARM[5])
                if a > bt(x, 51) + 0.2:
                    s.set(x, 51, WARM[4])
        return s.outline().img

    def statue(lit):
        """Small hooded figure kneeling on one knee, both hands on a sword planted before it."""
        s = Spr(Wd, Hd)
        pts = {}
        # cloak mass: from the shoulders flaring to the ground behind
        for y in range(31, 50):
            t = (y - 31) / 18
            xl = 11 - 6 * t ** 1.3
            xr = 17 + 2 * t
            for x in range(int(xl), int(xr) + 1):
                pts[(x, y)] = "cloak"
        # hood (head bowed forward)
        for y in range(23, 33):
            for x in range(9, 20):
                if ((x - 14.2) / 4.6) ** 2 + ((y - 28) / 5) ** 2 <= 1:
                    pts[(x, y)] = "hood"
        # front leg: thigh forward to the knee, shin down to the foot
        for y in range(40, 44):
            for x in range(15, 23):
                pts[(x, y)] = "leg"
        for y in range(43, 50):
            for x in range(20, 24):
                pts[(x, y)] = "leg"
        pts[(24, 49)] = "leg"
        # arms reaching to the hilt
        for i in range(8):
            pts[(16 + i, 34 + i // 3)] = "arm"
            pts[(16 + i, 35 + i // 3)] = "arm"
        for (x, y) in list(pts):
            if not (0 <= x < Wd):
                del pts[(x, y)]
        R = STONE
        for (x, y), part in pts.items():
            # light from upper-left: value from position inside the silhouette
            left = (x, y) not in pts or (x - 1, y) not in pts
            top = (x, y - 1) not in pts
            right = (x + 1, y) not in pts
            i = 3
            if part == "hood":
                i = 4 if x < 14 else 3
                if 15 <= x <= 18 and 27 <= y <= 31 and ((x - 18.5) ** 2 + (y - 29.5) ** 2) < 7:
                    i = 1                             # shadowed face in the hood opening
            elif part == "cloak":
                i = 4 if x < 9 else (3 if x < 14 else 2)
                if x in (10, 13) and y > 36 + (x - 10):
                    i -= 1                            # long cloth folds
            elif part == "leg":
                i = 3 if y < 42 else 2
            elif part == "arm":
                i = 4
            if top:
                i += 1
            if left:
                i += 1
            if right and part != "hood":
                i -= 1
            c = R[max(1, min(6, i))]
            if lit and (right or (x > 18 and part in ("leg", "arm")) or (part == "hood" and x > 16)):
                c = WARM[max(2, min(6, i + 1))]    # firelight on the side facing the brazier
            s.set(x, y, c)
        # the planted sword
        for y in range(33, 50):
            s.set(25, y, STONE[5] if y > 37 else STONE[4])
            s.set(26, y, STONE[3])
        s.rect(23, 37, 28, 37, GOLD[1])
        s.set(23, 37, GOLD[2])
        s.rect(25, 34, 26, 36, WOOD[2])
        s.set(25, 33, GOLD[2])
        s.set(26, 33, GOLD[1])
        return s.outline().img

    def brazier(lit):
        s = Spr(Wd, Hd)
        R = STONE
        # slender pedestal with a gold collar
        for y in range(30, 50):
            hw = 2.5 + (1.5 if y > 45 else 0) + (1 if y < 33 else 0)
            for x in range(int(36 - hw), int(36 + hw) + 1):
                i = 5 if x == int(36 - hw) else (2 if x >= 36 + hw - 1 else 3)
                c = R[i]
                if lit and y < 34:
                    c = WARM[min(6, i + 1)]          # flame-lit under the bowl
                elif lit and x == int(36 - hw) and y < 44:
                    c = WARM[5]
                s.set(x, y, c)
        for x in range(33, 40):
            s.set(x, 38, GOLD[2] if x < 37 else GOLD[1])
        s.shaded_rect(31, 47, 41, 49, STONE, 2)
        # bowl (iron, gold rim)
        for y in range(24, 30):
            t = (y - 24) / 5
            hw = 8 - 5 * t ** 1.4
            for x in range(int(36 - hw), int(36 + hw) + 1):
                i = 3 if x < 36 else 2
                if x == int(36 - hw):
                    i = 4
                s.set(x, y, IRON[i])
        for x in range(27, 46):
            s.set(x, 23, GOLD[3] if x < 32 else (GOLD[2] if x < 40 else GOLD[1]))
        for x in range(29, 44):
            s.set(x, 22, (GOLD[1] if lit and x % 3 else STONE[3]) if x % 2 else STONE[2])
        return s.outline().img

    def flame_cel(phase, size):
        s = Spr(Wd, Hd)
        if size > 0:
            FP = [GOLD[0], GOLD[1], GOLD[2], GOLD[3], GOLD[4], GOLD[5]]
            flame(s, 32.5, 22, 9 * size, 3 * size, phase + 0.37, FP, seed=2)
            flame(s, 39.5, 22, 10 * size, 3 * size, phase + 0.71, FP, seed=3)
            flame(s, 36, 22, 19 * size, 5.5 * size, phase, FP, seed=1)
            # sparks rising and drifting (loop over the phase)
            for k in range(int(5 * size)):
                u = (phase + k / 5) % 1.0
                x = 36 + math.sin(k * 2.3 + u * 6) * 5
                y = 22 - 18 * size - u * 14
                s.set(x, y, GOLD[4] if k % 2 else GOLD[3])
        else:
            s.set(36, 21, GOLD[0])
        return s.img

    frames, tags = [], []
    base = lambda lit: {"Stone": stone(lit), "Statue": statue(lit), "Brazier": brazier(lit)}
    unlit, lit = base(False), base(True)
    frames.append({"ms": 200, "cels": dict(unlit, Flame=flame_cel(0, 0))})
    tags.append(("unlit", 0, 0))
    for i in range(6):                      # kindle: sparks -> roaring
        size = [0.15, 0.3, 0.55, 0.85, 1.15, 1.0][i]
        cels = dict(lit if i >= 2 else unlit, Flame=flame_cel(i / 6, size))
        frames.append({"ms": [90, 90, 90, 100, 110, 120][i], "cels": cels})
    tags.append(("kindle", 1, 6))
    for i in range(6):
        frames.append({"ms": 110, "cels": dict(lit, Flame=flame_cel(i / 6, 1.0))})
    tags.append(("lit", 7, 12))
    return Wd, Hd, layers, frames, tags


# =========================================================================== fog wall
def fog():
    Wd, Hd = 32, 80
    FOGC = [C("a07028"), C("d0a040"), C("f0d070"), C("fff4c8")]
    frames = []
    for f in range(6):
        ph = f / 6 * 2 * math.pi
        img = blank(Wd, Hd)
        px = img.load()
        for y in range(Hd):
            yy = y / Hd * 2 * math.pi
            for x in range(Wd):
                # vertical curtains drifting upward: phase advances one full y-period over 6 frames
                v = (0.45 + 0.22 * math.sin(x * 0.42 + 0.9 * math.sin(yy + ph))
                     + 0.16 * math.sin(x * 0.9 + yy * 2 + ph * 2 + 1.3)
                     + 0.10 * math.sin(yy * 3 + ph * 3 + x * 0.2))
                edge = min(x + 1, Wd - x) / 6.0
                v *= min(1.0, edge) * (0.55 + 0.45 * smooth(0, 16, y)) * (0.8 + 0.2 * smooth(Hd, Hd - 10, y))
                if v < 0.28:
                    continue
                lvl = min(3, int((v - 0.28) / 0.13))
                if lvl < 3 and (v - 0.28) / 0.13 - lvl > 0.5 + 0.5 * bt(x, y):
                    lvl += 1                      # dithered steps between bands
                a = (60, 95, 130, 170)[lvl]
                c = FOGC[lvl]
                px[x, y] = (c[0], c[1], c[2], a)
        rnd = random.Random(5)
        for k in range(12):                        # rising glyph motes
            x0 = rnd.randrange(3, Wd - 3)
            y0 = int(rnd.randrange(Hd) - f * Hd / 6 * (1 + k % 2)) % Hd
            px[x0, y0] = (255, 244, 200, 230)
        frames.append({"ms": 110, "cels": {"Fog": img}})
    return Wd, Hd, ["Fog"], frames, [("loop", 0, 5)]


# =========================================================================== portcullis
def gate():
    Wd, Hd = 16, 64

    def portcullis(lift):
        s = Spr(Wd, Hd)
        top = -lift
        for bx in (1, 5, 9, 13):
            for y in range(top, top + 58):
                s.set(bx, y, IRON[3])
                s.set(bx + 1, y, IRON[1])
            # spike
            for (dx, dy, c) in ((0, 58, 3), (1, 58, 1), (0, 59, 3), (1, 59, 2), (0, 60, 4), (1, 61, 3)):
                s.set(bx + dx, top + dy, IRON[c])
        for cy in range(4, 58, 11):
            for x in range(0, 16):
                s.set(x, top + cy, IRON[2] if x % 4 else IRON[4])
                s.set(x, top + cy + 1, IRON[1])
        s.outline()
        return s.img

    def frame_cel():
        s = Spr(Wd, Hd)       # stone lintel housing at the top
        s.shaded_rect(0, 0, 15, 3, STONE, 3)
        s.set(7, 2, GOLD[1])
        s.set(8, 2, GOLD[2])
        return s.img

    frames = [{"ms": 200, "cels": {"Gate": portcullis(0), "Frame": frame_cel()}}]
    for i, lift in enumerate((4, 12, 22, 34, 46, 54)):
        frames.append({"ms": 80 if i else 140, "cels": {"Gate": portcullis(lift), "Frame": frame_cel()}})
    frames.append({"ms": 200, "cels": {"Gate": portcullis(54), "Frame": frame_cel()}})
    return Wd, Hd, ["Gate", "Frame"], frames, [("closed", 0, 0), ("opening", 1, 6), ("open", 7, 7)]


# =========================================================================== lever
def lever():
    Wd, Hd = 16, 24

    def base():
        s = Spr(Wd, Hd)
        s.shaded_rect(2, 19, 13, 23, STONE, 3)
        s.shaded_rect(4, 16, 11, 19, IRON, 2)
        s.set(7, 17, GOLD[2])
        s.set(8, 17, GOLD[1])
        return s.outline().img

    def handle(deg):
        s = Spr(Wd, Hd)
        a = math.radians(deg)
        px_, py_ = 7.5, 17
        L = 10
        ex, ey = px_ + math.sin(a) * L, py_ - math.cos(a) * L
        s.line(px_, py_, ex, ey, IRON[3])
        s.line(px_ + 1, py_, ex + 1, ey, IRON[1])
        # grip knob
        for (dx, dy) in ((0, 0), (1, 0), (0, -1), (1, -1)):
            s.set(ex + dx, ey + dy, CRIM[2])
        s.set(ex, ey - 1, CRIM[4])
        return s.outline().img

    frames = [{"ms": 200, "cels": {"Base": base(), "Handle": handle(-40)}}]
    for i, d in enumerate((-30, -5, 22, 40)):
        frames.append({"ms": 70, "cels": {"Base": base(), "Handle": handle(d)}})
    frames.append({"ms": 200, "cels": {"Base": base(), "Handle": handle(40)}})
    return Wd, Hd, ["Handle", "Base"], frames, [("off", 0, 0), ("pull", 1, 4), ("on", 5, 5)]


# =========================================================================== urn
def urn():
    Wd, Hd = 16, 24
    # half-widths per row: lip, neck, shoulder, belly, taper, foot
    prof = {5: 3, 6: 2, 7: 2, 8: 2.5, 9: 4, 10: 5, 11: 5.5, 12: 6, 13: 6, 14: 6, 15: 6, 16: 5.5, 17: 5,
            18: 4.5, 19: 3.5, 20: 2.5, 21: 2.5, 22: 3.5, 23: 3.5}

    def body(cracked=False):
        s = Spr(Wd, Hd)
        for y, hw in prof.items():
            x0, x1 = int(round(8 - hw)), int(round(8 + hw)) - 1
            for x in range(x0, x1 + 1):
                k = (x - x0) / max(1, x1 - x0)
                i = 4 if k < 0.2 else (3 if k < 0.55 else (2 if k < 0.85 else 1))
                if y in (5, 22):
                    i = min(4, i + 1)
                c = CLAY[i]
                if y == 10 or y == 18:
                    c = GOLD[2] if k < 0.4 else (GOLD[1] if k < 0.8 else GOLD[0])
                if y in (13, 14) and 0.25 < k < 0.75 and (x + y) % 3 == 0:
                    c = CLAY[1]                     # painted band
                s.set(x, y, c)
        s.set(7, 4, GOLD[2])
        s.set(8, 4, GOLD[1])
        if cracked:
            for (x, y) in ((6, 11), (7, 12), (7, 13), (8, 14), (8, 15), (9, 16), (5, 15), (6, 16), (10, 12)):
                s.set(x, y, CLAY[0])
        return s.outline().img

    def shards(t):
        s = Spr(Wd, Hd)
        rnd = random.Random(3)
        for k in range(9):
            ang = rnd.uniform(-2.6, -0.5)
            sp = rnd.uniform(3, 8)
            x = 8 + math.cos(ang) * sp * t
            y = 14 + math.sin(ang) * sp * t + 14 * t * t
            y = min(y, 22 - (k % 2))
            for (dx, dy) in ((0, 0), (1, 0), (0, 1)):
                s.set(x + dx, y + dy, CLAY[3] if (k + dx) % 2 else CLAY[2])
        # dust / ash puff + a gold spill
        if t < 0.8:
            for k in range(8):
                a = k / 8 * 6.28
                r = 3 + 6 * t
                s.set(8 + math.cos(a) * r, 15 + math.sin(a) * r * 0.6, STONE[4] if k % 2 else STONE[5])
        for x in range(4, 12):
            if t > 0.3:
                s.set(x, 23, CLAY[1] if x % 2 else CLAY[2])
        if t > 0.5:
            s.set(9, 22, GOLD[3])
            s.set(6, 22, GOLD[2])
        return s.outline().img

    frames = [{"ms": 200, "cels": {"Urn": body()}}]
    frames.append({"ms": 70, "cels": {"Urn": body(True)}})
    for t in (0.25, 0.5, 0.8, 1.0):
        frames.append({"ms": 80 if t < 1 else 200, "cels": {"Urn": shards(t)}})
    return Wd, Hd, ["Urn"], frames, [("idle", 0, 0), ("break", 1, 5)]


# =========================================================================== lantern
def lantern():
    Wd, Hd = 16, 32
    frames = []
    for f in range(4):
        s = Spr(Wd, Hd)
        # chain
        for y in range(0, 12):
            s.set(7 + (y // 2) % 2, y, IRON[3] if y % 2 == 0 else IRON[2])
        # cap
        s.rect(5, 12, 10, 12, IRON[3])
        s.rect(4, 13, 11, 14, IRON[2])
        s.set(4, 13, IRON[4])
        # glass box with cage bars
        for y in range(15, 26):
            for x in range(4, 12):
                c = GOLD[1] if x > 9 else GOLD[2]
                s.set(x, y, c)
        flame(s, 7.5, 24, 7 + (f % 2), 2.2, f / 4, pal=[GOLD[1], GOLD[2], GOLD[3], GOLD[4], GOLD[5]], seed=f)
        for y in range(15, 26):
            s.set(4, y, IRON[3])
            s.set(11, y, IRON[1])
            s.set(8, y, IRON[2] if y % 3 else IRON[1])
        s.rect(4, 26, 11, 27, IRON[2])
        s.rect(6, 28, 9, 28, IRON[1])
        s.set(7, 29, IRON[3])
        s.outline()
        frames.append({"ms": 120, "cels": {"Lantern": s.img}})
    return Wd, Hd, ["Lantern"], frames, [("loop", 0, 3)]


# =========================================================================== remnant (dropped cinders)
def remnant():
    Wd, Hd = 24, 32
    frames = []
    for f in range(6):
        ph = f / 6
        P = ph * 2 * math.pi
        s = Spr(Wd, Hd)
        pulse = 1 + 0.12 * math.sin(P)
        # scorched ash patch
        for x in range(4, 20):
            s.set(x, 31, STONE[1] if (x % 3) else STONE[2])
        for x in range(7, 17):
            s.set(x, 30, STONE[2] if x % 2 else STONE[3])
        # outer crimson wisp, inner gold flame, bright core orb
        flame(s, 12, 29, 20 * pulse, 6.5 * pulse, ph, pal=[CRIM[0], CRIM[1], CRIM[2], CRIM[3], CRIM[4]], seed=4)
        flame(s, 12, 29, 12 * pulse, 3.5 * pulse, ph + 0.5, pal=[CRIM[3], GOLD[2], GOLD[3], GOLD[4]], seed=7)
        for y in range(21, 29):
            for x in range(8, 17):
                d = math.hypot(x + 0.5 - 12, y + 0.5 - 25)
                if d < 2.6 * pulse:
                    s.set(x, y, GOLD[5] if d < 1.3 else GOLD[4])
        # orbiting motes (two rings)
        for k in range(4):
            a = P + k * math.pi / 2
            r = 8 if k % 2 else 6
            s.set(12 + math.cos(a) * r, 22 - k * 3 + math.sin(a) * 2, GOLD[4] if k % 2 else CRIM[4])
        frames.append({"ms": 110, "cels": {"Wisp": s.img}})
    return Wd, Hd, ["Wisp"], frames, [("loop", 0, 5)]


# =========================================================================== item orb
def item():
    Wd, Hd = 16, 16
    frames = []
    for f in range(6):
        ph = f / 6 * 2 * math.pi
        s = Spr(Wd, Hd)
        r = 3.0 + 0.5 * math.sin(ph)
        cy = 9 + round(math.sin(ph))
        # rays (cross, pulsing)
        L = 5 + round(1.5 * math.sin(ph))
        for d in range(int(r) + 1, L + 1):
            c = GOLD[2] if d > L - 2 else GOLD[3]
            for (dx, dy) in ((d, 0), (-d, 0), (0, -d), (0, d)):
                s.set(7.5 + dx, cy + dy, c)
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - cy)
                if d <= r:
                    v = 1 - d / r * 0.7 + 0.25 * ((7.5 - x) + (cy - y)) / r
                    s.set(x, y, pick(GOLD[1:], v, x, y))
        s.set(6, cy - 1, GOLD[5])
        frames.append({"ms": 100, "cels": {"Orb": s.img}})
    return Wd, Hd, ["Orb"], frames, [("loop", 0, 5)]


# =========================================================================== chest
def chest():
    Wd, Hd = 32, 24

    def body_cel():
        s = Spr(Wd, Hd)
        for y in range(13, 24):
            for x in range(4, 28):
                i = 3 if y < 15 else 2
                if x == 4:
                    i += 1
                if x == 27 or y == 23:
                    i = 1
                if (x - 4) % 6 == 5 and y > 14:
                    i = 1                  # plank seams
                s.set(x, y, WOOD[i])
        for bx in (6, 25):                 # iron bands
            for y in range(13, 24):
                s.set(bx, y, IRON[3])
                s.set(bx + 1, y, IRON[1])
        for x in range(4, 28):
            s.set(x, 22, IRON[2])
        return s.img

    def lid_cel(open_t):
        """open_t 0..1: the lid swings back; seen from the front it shrinks and rises."""
        s = Spr(Wd, Hd)
        h = round(7 * (1 - open_t) + 3 * open_t)
        top = 13 - h
        lift = round(-3 * open_t)
        for y in range(top + lift, 13 + lift):
            for x in range(4, 28):
                i = 4 if y == top + lift else 3
                if open_t > 0.5:
                    i = 1 if y > top + lift else 2      # we now see the lid's dark underside
                if x == 27:
                    i = 1
                s.set(x, y, WOOD[i])
        for bx in (6, 25):
            for y in range(top + lift, 13 + lift):
                s.set(bx, y, IRON[3] if open_t < 0.5 else IRON[1])
        return s.img

    def lock_cel(open_t):
        s = Spr(Wd, Hd)
        if open_t < 0.3:
            s.rect(15, 11, 16, 14, GOLD[2])
            s.set(15, 11, GOLD[3])
            s.set(16, 13, GOLD[0])
        return s.img

    def glow_cel(t):
        s = Spr(Wd, Hd)
        if t <= 0:
            return s.img
        # light spilling up out of the chest
        for y in range(0, 13):
            for x in range(5, 27):
                ray = 0.6 + 0.4 * math.cos((x - 16) * 1.1)
                a = t * (0.35 + 0.65 * y / 12) * (1 - abs(x - 16) / 12) * ray * 1.4
                if a > bt(x, y) * 0.7 + 0.1:
                    s.set(x, y, GOLD[4] if a > 0.8 else (GOLD[3] if a > 0.45 else GOLD[2]))
        for x in range(6, 26):
            s.set(x, 12, GOLD[4])
        return s.img

    def compose(t, glow):
        b = body_cel()
        l = lid_cel(t)
        merged = b.copy()
        merged.alpha_composite(l)
        merged.alpha_composite(lock_cel(t))
        m = outline(merged)
        return {"Chest": m, "Glow": glow_cel(glow)}

    frames = [{"ms": 200, "cels": compose(0, 0)}]
    for (t, g, ms) in ((0.15, 0, 90), (0.45, 0.4, 80), (0.8, 0.8, 80), (1.0, 1.0, 120), (1.0, 0.6, 250)):
        frames.append({"ms": ms, "cels": compose(t, g)})
    return Wd, Hd, ["Glow", "Chest"], frames, [("closed", 0, 0), ("open", 1, 5)]


# =========================================================================== elevator
def elevator():
    Wd, Hd = 48, 16
    s = Spr(Wd, Hd)
    # chains up out of frame at both ends
    for cx in (4, 43):
        for y in range(0, 7):
            s.set(cx + (y // 2) % 2, y, IRON[3] if y % 2 == 0 else IRON[2])
    # iron yoke
    s.rect(2, 6, 45, 7, IRON[2])
    s.rect(2, 6, 45, 6, IRON[3])
    # stone slab
    for y in range(8, 15):
        for x in range(1, 47):
            i = 4 if y == 8 else (3 if y < 11 else 2)
            if x == 1:
                i += 1
            if x == 46 or y == 14:
                i = 1
            if x in (12, 24, 36) and 9 <= y <= 13:
                i = 1
            s.set(x, y, STONE[min(6, i)])
    # gold rune ring in the centre block
    for (x, y) in ((22, 10), (23, 9), (25, 9), (26, 10), (26, 12), (25, 13), (23, 13), (22, 12), (24, 11)):
        s.set(x, y, GOLD[2])
    s.set(24, 11, GOLD[4])
    s.outline()
    return Wd, Hd, ["Lift"], [{"ms": 200, "cels": {"Lift": s.img}}], [("idle", 0, 0)]


PROPS = {
    "prop_shrine": shrine, "prop_fog": fog, "prop_gate": gate, "prop_lever": lever, "prop_urn": urn,
    "prop_lantern": lantern, "prop_remnant": remnant, "prop_item": item, "prop_chest": chest,
    "prop_elevator": elevator,
}
