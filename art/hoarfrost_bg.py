"""Parallax for the `hoarfrost` biome — THE HOARFROST AQUEDUCT.

bg_hoarfrost_far : 512x216 opaque, horizontally tileable. Night in the high passes past the Rampart
                   Summit: deep blue-black sky, sparse stars, a pale cold moon with a faint halo, a
                   restrained teal aurora curtain; two ranges of snow-capped peaks (lit on their
                   left flanks), faint frozen falls hanging on the cliffs, gorge mist, and the great
                   two-tier aqueduct striding across the gorge. The aqueduct's scale follows a cosine
                   of period 512 (near at one side, receding at the other) and its arches are
                   placed by integrating 1/scale, normalised to a whole number of arches, so the
                   layer still tiles.
bg_hoarfrost_mid : 512x216 transparent, tileable. Silhouettes in the lower 2/3: near aqueduct piers
                   and arches with a broken channel span (icicle fringes on the broken ends), a
                   frozen waterfall column poured from the break, snow-laden pines and rock spurs.

Built like archives_bg / env_bg: wrapping Canvas, tileable value noise, ordered dithering onto short
ramps, snow/rime on the top edges of silhouettes.
"""
import math, random
from envlib import C, ramp, T, K, bt, pick, h01, smooth, clamp, Canvas, fbm
from env_bg import tn, wrapdx
from hoarfrost_tiles import GOLD, ICE

W, H = 512, 216

# =========================================================================== FAR
FAR = ramp("03050a", "05070d", "070a11", "090d15", "0c1019", "0f141e", "121824", "161d2a", "1a2231",
           "1f2838", "252f41", "2c374a", "344055", "3e4a60", "4a576d", "58667d", "6a788f", "8190a6",
           "9dabbf")
AUR = ramp("0a1a1f", "0e2429", "123036", "173d42")                 # faint teal aurora
HZ = 118                                                           # horizon / eye level
MOON = (150, 36, 10)


def ridge(x, sx, seed, amp, base, octaves=4):
    """Tileable mountain profile: ridged fbm -> sharp peaks."""
    n = fbm(x, 0, sx, 1, seed, W, octaves)
    r = 1 - abs(2 * n - 1)
    return base - amp * r ** 1.6


def aqueduct_geom():
    """Per-column scale s(x) (0.42..1) and the arch coordinate u(x) (whole number per period)."""
    s = [0.71 + 0.29 * math.cos(2 * math.pi * (x - 96) / W) for x in range(W)]
    acc, u = 0.0, []
    for x in range(W):
        u.append(acc)
        acc += 1.0 / (30.0 * s[x])
    n = round(acc)
    u = [v * n / acc for v in u]
    return s, u, n


def build_hoarfrost_far():
    cv = Canvas(W, H, wrap=True)
    val = [[0.0] * W for _ in range(H)]
    kind = [[0] * W for _ in range(H)]                              # 0 sky, 1 far range, 2 near range
    # ---------------------------------------------------------------- sky
    mx, my, mr = MOON
    for y in range(H):
        for x in range(W):
            v = 0.04 + 0.17 * smooth(0, HZ + 20, y)
            dm = math.hypot(wrapdx(x, mx), y - my)
            v += 0.13 * math.exp(-dm / 24.0) + 0.05 * math.exp(-dm / 80.0)
            v += 0.02 * (tn(x, y, 64, 24, 3) - 0.5)
            val[y][x] = v
    # ---------------------------------------------------------------- ranges
    P1 = [ridge(x, 128, 11, 70, 112) for x in range(W)]            # far range (hazy, higher peaks)
    P2 = [ridge(x + 40, 64, 23, 44, 132) for x in range(W)]        # nearer range
    for (P, kd, rock, snow_hi, sd, haze) in ((P1, 1, 0.17, 0.46, 40, 0.10), (P2, 2, 0.09, 0.38, 30, 0.05)):
        for x in range(W):
            top = P[x]
            sl = (P[(x + 3) % W] - P[(x - 3) % W]) / 6.0           # >0: ground falls to the right
            for y in range(int(top), H):
                dy = y - top
                g0 = tn(x + 0.45 * dy, dy, 16, 36, 30 + kd)
                g1 = tn(x + 1 + 0.45 * dy, dy, 16, 36, 30 + kd)
                gm = tn(x - 1 + 0.45 * dy, dy, 16, 36, 30 + kd)
                ridge_ = 1 - abs(2 * g0 - 1)
                face = (gm - g1) * 5 + clamp(sl, -1, 1) * 0.9 * (1 - smooth(0, 30, dy))
                face *= 1 - smooth(HZ - 6, HZ + 14, y)
                snowy = 0.55 * ridge_ + 0.75 * (1 - smooth(0, sd, dy)) + 0.1 * tn(x, y, 8, 8, 40 + kd)
                if snowy > 0.78 and y < HZ + 8:
                    v = snow_hi + (0.05 if face > 0.05 else -0.13 if face < -0.05 else -0.05)
                else:
                    v = rock + (0.04 if face > 0.05 else -0.02) - 0.05 * smooth(0, 70, dy)
                v += haze * smooth(HZ - 30, HZ + 30, y)
                val[y][x] = v
                kind[y][x] = kd
    # frozen falls hanging on the near range's cliffs
    for fx in (58, 204, 330, 452):
        base = int(P2[fx]) + 10
        L = 22 + (fx % 17)
        for y in range(base, base + L):
            t = (y - base) / L
            for dx in range(-1, 1):
                x = (fx + dx + int(1.5 * math.sin(y * 0.2))) % W
                if kind[y][x] == 2:
                    val[y][x] = 0.30 - 0.14 * t + (0.05 if dx < 0 else 0)
    # ---------------------------------------------------------------- gorge: moonlit mist, dark floor
    for y in range(HZ - 10, H):
        for x in range(W):
            m = 0.16 * math.exp(-((y - (HZ + 30)) / 22.0) ** 2) * (0.75 + 0.5 * tn(x, y, 64, 12, 44))
            dark = smooth(HZ + 40, H, y)
            val[y][x] = val[y][x] * (1 - 0.55 * dark) + m
    # ---------------------------------------------------------------- quantise
    for y in range(H):
        for x in range(W):
            cv.set(x, y, pick(FAR, val[y][x], x, y))
    # aurora: a faint, thin curtain of vertical streaks along a slow wave (sky only)
    for x in range(W):
        yc = 40 + 10 * math.sin(2 * math.pi * x / W * 2 + 0.7) + 5 * math.sin(2 * math.pi * x / W * 5)
        amp = max(0.0, math.sin(2 * math.pi * x / W * 3 + 1.9)) ** 1.5
        streak = tn(x, 0, 4, 1, 51)
        for y in range(int(yc - 16), int(yc + 6)):
            if y < 0 or kind[y][x]:
                continue
            t = (y - (yc - 16)) / 22.0
            a = amp * streak * math.sin(math.pi * t) ** 2 * t
            if a > 0.30 and bt(x, y) < (a - 0.3) * 2.4:
                cv.set(x, y, AUR[1] if a > 0.6 else AUR[0])
    # stars (sky only, sparse, a few brighter)
    rnd = random.Random(7)
    for i in range(130):
        x, y = rnd.randrange(W), rnd.randrange(0, 100)
        if kind[y][x] or math.hypot(wrapdx(x, mx), y - my) < mr + 8:
            continue
        r = rnd.random()
        cv.set(x, y, FAR[13] if r < 0.1 else FAR[10] if r < 0.45 else FAR[8])
        if r < 0.025:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.set(x + dx, y + dy, FAR[9])
    # moon: pale disc lit from the upper left, faint maria
    for y in range(my - mr - 1, my + mr + 2):
        for x in range(mx - mr - 1, mx + mr + 2):
            d = math.hypot(x + 0.5 - mx, y + 0.5 - my)
            if d > mr:
                continue
            lx, ly = (x + 0.5 - mx) / mr, (y + 0.5 - my) / mr
            v = 0.84 - 0.18 * (lx + ly) * 0.5 - 0.10 * (d / mr) ** 3
            if tn(x * 4, y * 4, 32, 24, 61) > 0.62:
                v -= 0.10
            if d > mr - 1:
                v -= 0.06
            cv.set(x, y, pick(FAR, v, x, y))
    # ---------------------------------------------------------------- the aqueduct across the gorge
    s, u, n = aqueduct_geom()
    for x in range(W):
        sc = s[x]
        deck = HZ - 2 - 16 * sc                                    # top of the channel
        base = HZ + 30 + 40 * sc                                   # foot, lost in the gorge dark
        tier = deck + 6 * sc                                       # channel -> upper arcade
        mid_ = deck + 20 * sc                                      # upper arcade -> lower arcade
        f = u[x] % 1.0
        f3 = (u[x] * 3) % 1.0
        cell = 30.0 * sc
        tone = 0.07 + 0.03 * sc
        for y in range(int(deck), min(H, int(base))):
            if y < tier:
                v = tone + 0.05
                if y < deck + 1:
                    v = 0.40 + 0.10 * sc                           # snow on the channel
                elif y >= tier - 1:
                    v = tone + 0.02
            elif y < mid_:
                lx = (f3 - 0.5) * cell / 3
                hw = cell / 3 * 0.30
                spring = tier + 2 * sc + hw
                if abs(lx) < hw and y > spring - math.sqrt(max(0, hw * hw - lx * lx)) and y < mid_ - 1.5 * sc:
                    continue
                v = tone + (0.04 if f3 < 0.1 else 0)
                if y >= mid_ - 1.5 * sc:
                    v = tone + 0.07                                # string course, rimed
            else:
                lx = (f - 0.56) * cell
                hw = cell * 0.34
                spring = mid_ + 2 * sc + hw
                if abs(lx) < hw and y > spring - math.sqrt(max(0, hw * hw - lx * lx)):
                    continue
                v = tone + (0.05 if f < 0.08 else 0)
            v += 0.05 * smooth(HZ + 20, base, y)                   # mist around the piers' feet
            cv.set(x, y, pick(FAR, v, x, y))
    # a breach in the channel: frozen spill pouring from it down into the gorge
    bx = 300
    sc = s[bx]
    deck = HZ - 2 - 16 * sc
    for y in range(int(deck), int(HZ + 44)):
        t = (y - deck) / (HZ + 44 - deck)
        for dx in range(-1, 1 + int(3 * t)):
            x = bx + dx + int(1.5 * math.sin(y * 0.3) * t)
            v = 0.33 - 0.15 * t + (0.07 if dx < 0 else 0)
            cv.set(x, y, pick(FAR, v, x, y))
    # two warm window-lights of a shrine far up the pass (the only warm accent)
    wy = int(P2[412]) + 6
    for (x, y) in ((412, wy), (415, wy)):
        cv.set(x, y, GOLD[1])
    return cv.img


# =========================================================================== MID
MD = ramp("05070b", "07090f", "0a0d14", "0d111a", "111621", "161c29")
RIM = C("2c3848")
RIM2 = C("55667d")
SNOWM = C("6d7f96")
FICE = ramp("0d1822", "111f2c", "172a3a", "1f3548", "2a4459")     # dim ice for the frozen falls


def rect(cv, x0, x1, y0, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            cv.set(x, y, c)


def pine(cv, cx, base, h, seed):
    """Snow-laden fir: a few broad drooping tiers (the rim pass puts snow on each tier's lit top)."""
    top = base - h
    ntier = max(3, int(h / 10))
    for i in range(ntier):
        ty = top + h * 0.78 * i / ntier - (2 if i else 0)
        th = h * 0.78 / ntier + 5
        wmax = 3 + h * 0.22 * (0.4 + 0.6 * (i + 1) / ntier)
        for y in range(int(ty), int(ty + th) + 1):
            tt = max(0.0, (y - ty) / th)
            hw = wmax * tt ** 0.75
            for x in range(int(cx - hw), int(cx + hw) + 1):
                cv.set(x, y, MD[3] if x <= cx else MD[2])
        # drooping bough tips
        yb = int(ty + th)
        cv.set(cx - wmax - 1, yb + 1, MD[3])
        cv.set(cx + wmax + 1, yb + 1, MD[2])
    cv.set(cx, top - 1, MD[3])
    cv.set(cx, top - 2, MD[3])
    rect(cv, cx - 1, cx, base - h * 0.18, base + 8, MD[1])


def crag(cv, x0, x1, top, seed):
    """Jagged rock spur rising from the bottom edge (faceted, darker right faces)."""
    rnd = random.Random(seed)
    pts = [(x0, H + 2)]
    n = 5
    for i in range(1, n):
        t = i / n
        pts.append((x0 + (x1 - x0) * t + rnd.uniform(-4, 4), top + (1 - math.sin(math.pi * t)) * (H - top) * 0.7
                    + rnd.uniform(-8, 6)))
    pts.append((x1, H + 2))
    for x in range(int(x0), int(x1) + 1):
        for k in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[k], pts[k + 1]
            if ax <= x <= bx:
                yy = ay + (by - ay) * (x - ax) / max(1e-6, bx - ax)
                c = MD[2] if by < ay else MD[1]                    # rising facets face the light
                for y in range(int(yy), H):
                    cv.set(x, y, c)
                break


def build_hoarfrost_mid():
    cv = Canvas(W, H, wrap=True)
    CH0, CH1 = 84, 98                                              # channel slab top / bottom
    PW = 22
    PIERS = [20, 148, 276, 404]                                    # bay = 128
    R = (128 - PW) / 2
    SPRING = CH1 + 4 + R
    GAP = (200, 234)                                               # breach in bay B
    RUIN = 3                                                       # bay D (404 -> 20) has fallen
    fringe = []                                                    # (x, y) where icicles hang
    # ---------------------------------------------------------------- piers
    for i, px0 in enumerate(PIERS):
        rect(cv, px0, px0 + PW - 1, CH1, H - 1, MD[2])
        rect(cv, px0, px0 + 2, CH1, H - 1, MD[3])                  # lit left face
        rect(cv, px0 + PW - 3, px0 + PW - 1, CH1, H - 1, MD[1])
        for yy in range(CH1 + 16, H, 14):                          # coursing
            rect(cv, px0 + 3, px0 + PW - 4, yy, yy, MD[1])
        rect(cv, px0 - 2, px0 + PW + 1, SPRING - 3, SPRING, MD[3])  # impost
        rect(cv, px0 - 2, px0 + PW + 1, SPRING + 1, SPRING + 1, MD[1])
    # ---------------------------------------------------------------- arches / spandrels
    for i, px0 in enumerate(PIERS):
        a0 = px0 + PW
        a1 = PIERS[(i + 1) % 4] + (W if i == 3 else 0)
        cx = (a0 + a1) / 2
        for x in range(int(a0) - 1, int(a1) + 1):
            dx = x + 0.5 - cx
            yin = SPRING - math.sqrt(max(0.0, R * R - dx * dx))
            if i == RUIN:
                # only the springers survive: stubs of voussoirs climbing off each pier, broken
                lim = 18 + 6 * h01(x // 3, 1, 7)
                if abs(dx) < R - lim:
                    continue
                yt = yin - 7 - 5 * h01(x // 2, 2, 8)
                for y in range(int(yt), int(yin)):
                    cv.set(x, y, MD[3] if (y - int(yt)) < 2 else MD[2])
                continue
            for y in range(CH1, int(yin)):
                if i == 1 and GAP[0] <= x <= GAP[1] and y < CH1 + 10 + 3 * h01(x // 2, 5, 3):
                    continue
                cv.set(x, y, MD[2])
            ang = math.degrees(math.atan2(SPRING - yin, dx))
            for y in range(int(yin) - 5, int(yin)):
                if not (i == 1 and GAP[0] <= x <= GAP[1] and y < CH1 + 10):
                    cv.set(x, y, MD[3] if (int(ang) // 10) % 2 else MD[2])
            if abs(dx) < R * 0.55 and h01(x, 3, 88) < 0.4:
                fringe.append((x, int(yin)))
    # ---------------------------------------------------------------- channel slab + cornice
    snow_top = []
    for x in range(W):
        bay = next(i for i in range(4) if (x - PIERS[i]) % W < 128)
        if bay == RUIN and not (PIERS[3] <= x < PIERS[3] + PW or PIERS[0] <= x < PIERS[0] + PW):
            continue
        if GAP[0] <= x <= GAP[1]:
            continue
        rect(cv, x, x, CH0, CH1, MD[3] if x % 32 else MD[2])
        cv.set(x, CH0 + 4, MD[4])                                  # cornice
        cv.set(x, CH0 + 5, MD[1])
        snow_top.append(x)
        if h01(x, 9, 88) < 0.35:
            fringe.append((x, CH0 + 6))
    # ragged pier tops over the fallen bay
    for px0 in (PIERS[3], PIERS[0]):
        for x in range(px0 - 2, px0 + PW + 2):
            d = int(4 + 10 * h01(x // 2, px0, 21))
            for y in range(CH0 - 2, CH0 + d):
                cv.set(x, y, T)
    # breach edges: jagged broken ends of the channel
    for (bx, sg) in ((GAP[0], -1), (GAP[1], 1)):
        for y in range(CH0 - 1, CH1 + 12):
            L = int(1 + 5 * h01(y // 2, bx, 5))
            for k in range(L):
                cv.set(bx + sg * k, y, T)
    # ---------------------------------------------------------------- the frozen fall out of the breach
    fx0, fx1 = GAP[0] + 3, GAP[1] - 3
    for y in range(CH0 + 3, H):
        t = (y - CH0) / (H - CH0)
        wob = 1.5 * math.sin(y * 0.07) + 1.0 * math.sin(y * 0.19 + 1)
        xl = fx0 + 5 * t ** 2 - 2 * t + wob - 8 * smooth(0.8, 1, t)
        xr = fx1 - 3 * t + wob * 0.6 + 9 * smooth(0.8, 1, t)
        for x in range(int(xl), int(xr) + 1):
            u_ = (x - xl) / max(1, xr - xl)
            flow = tn(x * 4, y, 8, 72, 71)
            i = 1 + (u_ < 0.3) + (flow > 0.64) - (u_ > 0.8)
            cv.set(x, y, FICE[max(0, min(4, i))])
        if int(xl) - 1 >= 0 or True:
            cv.set(int(xl) - 1, y, MD[1])
            cv.set(int(xr) + 1, y, MD[1])
    # icicle fringes (channel cornice, arch crowns, breach lips)
    for (x, y) in fringe:
        if not cv.opaque(x, y - 1) or cv.opaque(x, y):
            continue
        L = 2 + int(8 * h01(x, y, 89) ** 2)
        for j in range(L):
            cv.set(x, y + j, FICE[2] if j < L - 1 else FICE[1])
    for (bx, sg) in ((GAP[0] - 3, -1), (GAP[1] + 3, 1)):
        for k in range(0, 12, 2):
            x = bx + sg * k
            y = CH1 + 1
            while y < H and not cv.opaque(x, y - 1):
                y += 1
            L = 4 + int(9 * h01(k, bx, 9))
            for j in range(L):
                if not cv.opaque(x, y + j):
                    cv.set(x, y + j, FICE[3] if j < L - 2 else FICE[2])
    # ---------------------------------------------------------------- foreground crags + pines
    crag(cv, 52, 138, 150, 3)
    crag(cv, 300, 372, 164, 5)
    crag(cv, 444, 504, 172, 8)
    for (cx, base, h, sd) in ((70, 196, 48, 1), (92, 204, 34, 2), (122, 192, 40, 3), (318, 204, 42, 4),
                              (352, 198, 30, 5), (462, 208, 36, 6), (488, 204, 26, 7), (160, 212, 24, 8)):
        pine(cv, cx, base, h, sd)
    # snowy ground drift along the bottom
    for x in range(W):
        top = 209 - 3 * tn(x, 0, 32, 1, 70) - 2 * tn(x, 0, 8, 1, 71)
        for y in range(int(top), H):
            cv.set(x, y, MD[1] if y - int(top) > 1 else MD[3])
    # ---------------------------------------------------------------- snow / rime on top edges
    px = cv.img.load()
    body = set(MD)
    hits = []
    for y in range(1, H):
        for x in range(W):
            c = px[x, y]
            if c not in body:
                continue
            up, lf, ul = px[x, y - 1], px[(x - 1) % W, y], px[(x - 1) % W, y - 1]
            if up[3] == 0 and (ul[3] == 0 or lf[3] == 0):
                hits.append((x, y, RIM2))
                if y + 1 < H and px[x, y + 1] in body and h01(x, y, 3) < 0.55:
                    hits.append((x, y + 1, RIM))
            elif lf[3] == 0 and ul[3] == 0 and up[3]:
                hits.append((x, y, RIM))                           # vertical lit edges only
    for (x, y, c) in hits:
        px[x, y] = c
    # a snow crust piled along the channel top (drawn after the rim pass so it sits on top)
    for x in snow_top:
        if px[x, CH0][3] and px[x, CH0 - 1][3] == 0:
            d = 1 + (h01(x // 3, 0, 61) < 0.5)
            for j in range(d):
                px[x, CH0 - 1 - j] = SNOWM if j == d - 1 else RIM2
    # a brazier left burning on a pier impost (the only warm accent in the layer)
    bx, by = PIERS[2] + PW - 4, int(SPRING) - 4
    for (dx, dy, c) in ((0, 0, MD[4]), (1, 0, MD[4]), (-1, 0, MD[4]), (0, -1, GOLD[1]), (0, -2, GOLD[2]),
                        (1, -1, GOLD[0]), (-1, -1, GOLD[0])):
        px[(bx + dx) % W, by + dy] = c
    return cv.img


BUILDERS = {"hoarfrost": (build_hoarfrost_far, build_hoarfrost_mid)}
