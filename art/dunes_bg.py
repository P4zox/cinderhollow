"""Parallax backgrounds for the `dunes` biome (THE SUNSCORCHED DUNES).

bg_dunes_far : 512x216 opaque, tileable (period 512): a buried desert under a cavern roof. Through a long rift in the rock the
               sky burns white-hot around the sun-disc; below, gold dunes roll away in the haze, with the half-buried head of a
               colossal sun-king, a toppled obelisk and far pyramids.
bg_dunes_mid : 512x216 transparent, tileable: nearer dune crests and ruins -- broken colonnades, a jackal-headed colossus seated
               to the waist in sand, obelisks -- dark umber silhouettes rim-lit gold from the rift.
"""
import math, random
from envlib import C, ramp, T, K, bt, pick, h01, smooth, clamp, Canvas, fbm

W, H = 512, 216

ROCK = ramp("0c0705", "120a07", "190e09", "20130b", "2a180e", "341e11")           # cavern roof
SKY = ramp("5a3410", "7a4814", "9c6018", "c07c20", "e0a032", "f4c65a", "fde392", "fff4cc", "fffcf0")
HAZE = ramp("3a220e", "4e2e12", "643c16", "7c4c1c", "956022", "ac742a", "c28a36", "d6a046", "e6b85a")
DUNE = ramp("24150a", "321d0d", "422711", "553216", "6a3f1b", "7f4e22", "96602a", "ad7434")
SIL = ramp("140b06", "1b0f08", "24140a", "2e1a0d", "382010")
RIM = ramp("7a5018", "a8742a", "d6a044", "f4ca6c", "fff0b0")


def poly_fill(cv, pts, colf):
    """Scanline-fill a polygon; colf(x, y) -> colour or None."""
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        cy = y + 0.5
        xs = []
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            if (y1 <= cy < y2) or (y2 <= cy < y1):
                xs.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                c = colf(x, y)
                if c is not None:
                    cv.set(x, y, c)


def wrapdx(x, cx):
    d = (x - cx) % W
    return d - W if d > W / 2 else d


def rift_y(x):
    """Lower edge of the cavern roof (the rift opening): high in the middle of the loop, jagged."""
    v = 34 + 16 * math.cos(2 * math.pi * x / W) + 6 * math.sin(2 * math.pi * x * 3 / W + 1.2) + 3 * math.sin(2 * math.pi * x * 11 / W)
    return v + 4 * (fbm(x, 0, 32, 1, 3) - 0.5)


def dune_line(x, base, amp, per, ph, seed):
    return base - amp * (0.55 + 0.45 * math.sin(2 * math.pi * x * per / W + ph)) - 6 * (fbm(x, seed, 64, 1, seed) - 0.5)


SUN_X, SUN_Y = 300, 30


def build_dunes_far():
    cv = Canvas(W, H, wrap=True)
    # sky through the rift: white-hot around the sun, deepening to gold/amber at the edges and toward the horizon
    for y in range(H):
        for x in range(W):
            dsun = math.hypot(wrapdx(x, SUN_X) * 0.8, (y - SUN_Y) * 1.2)
            v = 0.45 + 0.5 * math.exp(-(dsun / 90.0) ** 2) - 0.25 * smooth(40, 150, y) + 0.05 * (fbm(x, y, 64, 12, 3) - 0.5)
            cv.set(x, y, pick(SKY, v, x, y))
    # the sun-disc and its halo rings
    for y in range(0, 70):
        for x in range(SUN_X - 40, SUN_X + 41):
            d = math.hypot(x - SUN_X, y - SUN_Y)
            if d < 11:
                cv.set(x, y, SKY[8])
            elif d < 12.5:
                cv.set(x, y, SKY[7])
            elif 17 < d < 18.2 and h01(x, y, 4) < 0.7:
                cv.set(x, y, SKY[7])
    # far haze band + pyramids
    for x in range(W):
        hz = 112 + 3 * math.sin(2 * math.pi * x * 2 / W)
        for y in range(int(hz), H):
            v = 0.35 + 0.5 * smooth(hz, H, y) * 0 + 0.3 * (1 - smooth(hz, hz + 40, y))
            cv.set(x, y, pick(HAZE, 0.62 - 0.25 * smooth(hz, H, y) + 0.04 * (fbm(x, y, 32, 8, 7) - 0.5), x, y))
    for (cx, w, h) in ((70, 46, 36), (118, 28, 22), (410, 60, 44), (470, 30, 22)):
        base = 116
        for y in range(base - h, base + 1):
            t = (y - (base - h)) / h
            hw = w * t
            for x in range(int(cx - hw), int(cx + hw) + 1):
                lit = x < cx
                cv.set(x, y, pick(HAZE, (0.62 if lit else 0.4) - 0.15 * t, x, y))
    # three dune ranges, far to near
    for (base, amp, per, ph, seed, lo, hi) in ((130, 12, 3, 0.5, 11, 0.42, 0.72), (152, 16, 2, 2.1, 12, 0.3, 0.62), (178, 20, 1, 4.0, 13, 0.18, 0.5)):
        for x in range(W):
            top = dune_line(x, base, amp, per, ph, seed)
            slope = dune_line(x + 1, base, amp, per, ph, seed) - top
            for y in range(int(top), H):
                t = smooth(top, top + 50, y)
                v = hi - (hi - lo) * t
                if slope > 0.12:
                    v -= 0.12                                   # lee side in shade
                if y == int(top):
                    v += 0.12
                cv.set(x, y, pick(DUNE if base > 140 else HAZE, v + 0.03 * (fbm(x, y, 32, 6, seed) - 0.5), x, y))
    # the colossal sun-king's head, buried to the chin in the middle dunes: nemes headcloth with lappets, a cracked sun-disc
    hx, hy = 150, 152
    def hz(v):
        return lambda x, y: pick(HAZE, v(x, y), x, y)
    nemes = [(hx - 22, hy - 58), (hx - 14, hy - 66), (hx, hy - 69), (hx + 14, hy - 66), (hx + 22, hy - 58), (hx + 23, hy - 44),
             (hx + 36, hy - 14), (hx + 38, hy + 4), (hx - 38, hy + 4), (hx - 36, hy - 14), (hx - 23, hy - 44)]
    poly_fill(cv, nemes, hz(lambda x, y: 0.5 - 0.006 * (x - hx) + (0.05 if int((y - hy) / 3) % 2 else -0.02)))
    face = [(hx - 13, hy - 52), (hx + 13, hy - 52), (hx + 14, hy - 30), (hx + 10, hy - 12), (hx + 4, hy - 4), (hx - 4, hy - 4),
            (hx - 10, hy - 12), (hx - 14, hy - 30)]
    poly_fill(cv, face, hz(lambda x, y: 0.6 - 0.012 * (x - hx) - (0.18 if abs(y - (hy - 38)) < 3 and 3 < abs(x - hx) < 10 else 0)
                          - (0.08 if (x - hx) > 8 else 0)))
    poly_fill(cv, [(hx - 13, hy - 55), (hx + 13, hy - 55), (hx + 13, hy - 52), (hx - 13, hy - 52)], hz(lambda x, y: 0.72))   # brow band
    poly_fill(cv, [(hx - 2, hy - 62), (hx + 2, hy - 62), (hx + 2, hy - 53), (hx - 2, hy - 53)], hz(lambda x, y: 0.76))       # uraeus
    for y in range(hy - 96, hy - 66):                                                           # sun-disc crown, a wedge broken away
        for x in range(hx - 16, hx + 17):
            d = math.hypot(x - hx, y - (hy - 82))
            if d < 14 and not (x - hx > 2 and y - (hy - 82) < -2 - (x - hx) * 0.3):
                cv.set(x, y, pick(HAZE, 0.8 - d * 0.02 if x < hx + 4 else 0.52, x, y))
    # toppled obelisk in the near-far dunes
    for i in range(80):
        x0, y0 = 360 + i, 166 - i * 0.28
        for k in range(-4, 5):
            cv.set(int(x0), int(y0 + k), pick(HAZE, 0.46 if k < 0 else 0.3, int(x0), int(y0 + k)))
    # the cavern roof (dark rock) above the rift, with hanging sand trickles catching the light
    for x in range(W):
        ry = rift_y(x)
        for y in range(0, int(ry) + 1):
            v = 0.2 + 0.5 * (1 - smooth(0, ry, y)) * 0 + 0.3 * smooth(ry - 10, ry, y) + 0.12 * (fbm(x, y, 16, 8, 21) - 0.5)
            cv.set(x, y, pick(ROCK, v, x, y))
        cv.set(x, int(ry), RIM[1])
        if h01(x, 1, 31) < 0.07:
            L = int(10 + 30 * h01(x, 2, 31))
            for y in range(int(ry), int(ry) + L):
                cv.set(x, y, SKY[5] if (y + x) % 3 else SKY[6])
    # rock also frames the bottom corners of the view? no -- keep the floor open: dunes run to the bottom
    return cv.img


def build_dunes_mid():
    cv = Canvas(W, H, wrap=True)
    # 1) near dune crests along the bottom
    for x in range(W):
        top = dune_line(x, 196, 22, 2, 1.1, 41)
        for y in range(int(top), H):
            v = 0.55 - 0.4 * smooth(top, top + 20, y)
            c = SIL[int(clamp(v * 5, 0, 4))]
            if y == int(top):
                c = RIM[2] if dune_line(x + 1, 196, 22, 2, 1.1, 41) < top else RIM[1]
            cv.set(x, y, c)
    rnd = random.Random(5)
    # 2) broken colonnade
    for i, cx in enumerate((40, 64, 88, 112)):
        h = (96, 70, 104, 44)[i]
        base = 200
        for y in range(base - h, base):
            for x in range(cx - 7, cx + 8):
                if y < base - h + 4 and abs(x - cx) < 7 - (base - h + 4 - y):
                    continue
                edge = x == cx - 7
                c = RIM[1] if edge and y % 7 else SIL[3] if x < cx - 3 else SIL[2]
                if (y - (base - h)) % 16 == 15:
                    c = SIL[1]                                  # drum joints
                cv.set(x, y, c)
        if i in (0, 2):                                         # capital (papyrus bundle)
            for y in range(base - h - 8, base - h):
                for x in range(cx - 10, cx + 11):
                    if abs(x - cx) < 10 - (base - h - y) * 0.3:
                        cv.set(x, y, SIL[3] if x > cx - 8 else RIM[1])
    for x in range(34, 96):                                     # a lintel resting on two columns
        for y in range(88, 96):
            if x < 96:
                cv.set(x, y, SIL[3] if y > 89 else RIM[2])
    # 3) the seated jackal colossus, buried to the waist: broad shoulders, a collar, arms at its sides, the jackal head in profile
    jx, jy = 300, 206
    def jc(x, y):
        lit = x < jx - 14 or (y < jy - 100 and x < jx - 2)
        return (RIM[1] if (x + y) % 2 else SIL[3]) if lit and x < jx - 20 else RIM[1] if lit and x == jx - 20 else SIL[3] if x < jx else SIL[2]
    torso = [(jx - 20, jy), (jx - 23, jy - 44), (jx - 26, jy - 60), (jx - 12, jy - 70), (jx + 12, jy - 70), (jx + 26, jy - 60),
             (jx + 23, jy - 44), (jx + 20, jy)]
    poly_fill(cv, torso, jc)
    for side in (-1, 1):                                                                    # upper arms at the sides
        arm_ = [(jx + side * 24, jy - 62), (jx + side * 31, jy - 54), (jx + side * 30, jy - 10), (jx + side * 23, jy - 10)]
        poly_fill(cv, arm_, lambda x, y, sd=side: (RIM[2] if x < jx - 29 else SIL[3]) if sd < 0 else SIL[2])
    poly_fill(cv, [(jx - 16, jy - 70), (jx + 16, jy - 70), (jx + 13, jy - 60), (jx - 13, jy - 60)],
              lambda x, y: RIM[3] if (y - (jy - 70)) % 3 == 0 else RIM[1] if x < jx else SIL[3])            # the broad collar
    jy += 22
    neck = [(jx - 8, jy - 92), (jx + 8, jy - 92), (jx + 7, jy - 112), (jx - 7, jy - 112)]
    poly_fill(cv, neck, jc)
    head = [(jx - 12, jy - 110), (jx - 10, jy - 124), (jx - 2, jy - 130), (jx + 8, jy - 128), (jx + 30, jy - 118), (jx + 34, jy - 114),
            (jx + 30, jy - 111), (jx + 10, jy - 108), (jx - 2, jy - 104)]
    poly_fill(cv, head, jc)
    for (ex, ey) in ((jx - 6, jy - 128), (jx + 3, jy - 129)):                              # tall ears
        poly_fill(cv, [(ex - 4, ey + 2), (ex + 1, ey - 22), (ex + 5, ey + 2)], jc)
    for (x, y) in ((jx + 10, jy - 121), (jx + 11, jy - 121)):
        cv.set(x, y, RIM[4])                                                                # a gold eye
    # 4) obelisks
    for (cx, h, w) in ((420, 130, 9), (470, 90, 7)):
        base = 205
        for y in range(base - h, base):
            hw = w * (0.7 + 0.3 * (y - (base - h)) / h)
            for x in range(int(cx - hw), int(cx + hw) + 1):
                c = RIM[1] if x < cx - hw + 2 else SIL[3] if x < cx else SIL[2]
                cv.set(x, y, c)
        for y in range(base - h - 10, base - h):
            hw = (y - (base - h - 10)) * w * 0.07
            for x in range(int(cx - hw), int(cx + hw) + 1):
                cv.set(x, y, RIM[3] if x < cx else RIM[1])       # gilded pyramidion
    # 5) sand pouring from above in a couple of places (thin streams)
    for sx in (190, 372):
        for y in range(0, 190):
            for k in range(2):
                if h01(sx + k, y // 3, 17) < 0.8:
                    cv.set(sx + k, y, RIM[2] if (y + k) % 4 else RIM[3])
    return cv.img


BUILDERS = {"dunes": (build_dunes_far, build_dunes_mid)}
