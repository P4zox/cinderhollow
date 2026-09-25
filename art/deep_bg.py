"""Parallax backgrounds for the `deep` biome (THE BURNING DEEP).

bg_deep_far : 512x216 opaque, tileable (period 512): the vast root-forge cavern -- a ceiling of petrified heartwood roots,
              colossal furnace towers with glowing maws, lava falls, a molten sea glowing up from below.
bg_deep_mid : 512x216 transparent, tileable: nearer forge machinery -- gear wheels, riveted girders, hanging chains and
              crucibles, anvil blocks -- black silhouettes rim-lit orange from the heat below.
"""
import math, random
from envlib import C, ramp, T, K, bt, pick, h01, smooth, clamp, Canvas, fbm

W, H = 512, 216

SKY = ramp("060303", "0a0505", "0e0706", "130908", "190c0a", "200f0b", "28130d", "31170f", "3c1c10", "4a2212",
           "5a2913", "6d3114", "833a14", "9c4515", "b85418", "d6661c")
SIL = ramp("070404", "0b0605", "100807", "160a08", "1d0d0a", "26110c")          # distant silhouettes (warm black)
MG = ramp("3a0906", "661107", "9c1f09", "cf3b0c", "f26414", "ff9a2e", "ffcf66", "fff3cc")
IRN = ramp("050303", "0a0606", "100a09", "18100e", "221612", "2e1d17")
RIM = ramp("5a1a08", "8a2c0c", "c04a12", "f07a22", "ffb050")


def wrapdx(x, cx):
    d = (x - cx) % W
    return d - W if d > W / 2 else d


def far_v(x, y):
    """Brightness of the haze: dark vault, glowing floor of the cavern, hotter under the lava falls."""
    v = 0.05 + 0.62 * smooth(40, 216, y) ** 1.6
    for fx in (96, 300, 430):
        v += 0.18 * math.exp(-(wrapdx(x, fx) / 70.0) ** 2) * smooth(60, 216, y)
    return v


def build_deep_far():
    cv = Canvas(W, H, wrap=True)
    for y in range(H):
        for x in range(W):
            n = fbm(x, y, 64, 8, 5) - 0.5
            cv.set(x, y, pick(SKY, far_v(x, y) + 0.06 * n, x, y))
    rnd = random.Random(11)
    # 1) distant furnace towers (very hazy): tapering stacks with a glowing maw near the base
    for (cx, w, top) in ((40, 26, 70), (150, 34, 50), (236, 22, 88), (352, 40, 44), (470, 24, 80)):
        for y in range(top, H):
            t = (y - top) / (H - top)
            hw = w * (0.55 + 0.45 * t)
            for x in range(int(cx - hw), int(cx + hw) + 1):
                d = abs(x - cx) / hw
                v = 0.10 + 0.10 * smooth(0.4, 1.0, 1 - d) + 0.18 * t ** 2
                cv.set(x, y, pick(SKY, v, x, y))
        # rim ledges / bands
        for yb in range(top + 12, H, 26):
            hw = w * (0.55 + 0.45 * (yb - top) / (H - top)) + 2
            for x in range(int(cx - hw), int(cx + hw) + 1):
                cv.set(x, yb, SKY[4])
        # glowing maw
        my = top + int((H - top) * 0.62)
        for y in range(my - 9, my + 7):
            for x in range(int(cx - w * 0.35), int(cx + w * 0.35) + 1):
                e = ((x - cx) / (w * 0.35)) ** 2 + ((y - my) / 8.0) ** 2
                if e < 1:
                    cv.set(x, y, pick(MG, 0.35 + 0.5 * (1 - e), x, y))
        # smoke column rising off the top
        for y in range(0, top):
            for x in range(int(cx - 12), int(cx + 13)):
                wob = 6 * math.sin(y * 0.07 + cx)
                if abs(x - cx - wob) < 5 + (top - y) * 0.12 and fbm(x, y, 16, 8, 3) > 0.5:
                    cv.set(x, y, pick(SKY, 0.16 + 0.08 * fbm(x, y, 8, 4, 4), x, y))
    # 2) lava falls pouring from the vault into the molten sea
    for fx in (96, 300, 430):
        for y in range(18, H):
            wob = 1.5 * math.sin(y * 0.11 + fx)
            wid = 2.2 + 1.8 * smooth(18, 216, y)
            for x in range(int(fx - wid - 1), int(fx + wid + 2)):
                d = abs(x - fx - wob) / wid
                if d < 1:
                    cv.set(x, y, pick(MG, 0.95 - 0.55 * d - 0.15 * (h01(x, y // 3, 7) < 0.3), x, y))
        for y in range(H - 30, H):         # splash glow at the foot
            for x in range(fx - 30, fx + 31):
                d = math.hypot((x - fx) / 30.0, (y - H) / 26.0)
                if d < 1 and (1 - d) * 1.4 > bt(x, y):
                    cv.set(x, y, pick(MG, 0.25 + 0.45 * (1 - d), x, y))
    # 3) the vault: petrified heartwood roots hanging from the ceiling (charcoal, ember-veined)
    for i in range(9):
        rx = i * 57 + rnd.uniform(-10, 10)
        ln = rnd.uniform(40, 95)
        w0 = rnd.uniform(9, 16)
        lean = rnd.uniform(-0.25, 0.25)
        for y in range(0, int(ln)):
            t = y / ln
            cx = rx + lean * y + 4 * math.sin(y * 0.08 + i)
            hw = w0 * (1 - t) ** 0.8 + 0.6
            for x in range(int(cx - hw), int(cx + hw) + 1):
                d = (x - cx) / hw
                v = 0.30 - 0.2 * d
                c = pick(SIL, v + 0.2, x, y)
                if abs(d) < 0.25 and h01(x, y // 2, i) < 0.07 and t < 0.8:
                    c = MG[2]
                cv.set(x, y, c)
        # a tendril dripping a glowing bead
        tip = (rx + lean * ln, ln)
        cv.set(tip[0], tip[1] + 2, MG[4]); cv.set(tip[0], tip[1] + 3, MG[3])
    # 4) ceiling rock
    for x in range(W):
        h = 6 + 8 * fbm(x, 0, 64, 1, 21)
        for y in range(int(h)):
            cv.set(x, y, SIL[1] if y < h - 1 else SIL[3])
    # 5) the molten sea: bright band at the bottom with dark cooling crust
    for y in range(H - 14, H):
        for x in range(W):
            t = (y - (H - 14)) / 14
            n = fbm(x, y, 32, 4, 31)
            v = 0.35 + 0.35 * t + 0.25 * (n - 0.5)
            c = pick(MG, v, x, y)
            if n < 0.38 and t > 0.3:
                c = SKY[6]
            cv.set(x, y, c)
    return cv.img


def gear(cv, cx, cy, r, teeth, body, rim_c, hole=True, phase=0.0):
    for y in range(int(cy - r - 3), int(cy + r + 4)):
        for x in range(int(cx - r - 3), int(cx + r + 4)):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx) + phase
            tooth = math.cos(a * teeth) > 0.25
            R = r + (2.5 if tooth else 0)
            if d > R:
                continue
            if hole and d < r * 0.28:
                continue
            spoke = any(abs(math.sin(a - k * math.pi / 3)) * d < 1.6 for k in range(3))
            if r * 0.34 < d < r * 0.72 and not spoke:
                continue
            c = body
            if dy < -d * 0.4 and d > R - 2:
                c = rim_c
            cv.set(x, y, c)


def build_deep_mid():
    cv = Canvas(W, H, wrap=True)
    rnd = random.Random(5)
    B0, B1, B2 = IRN[1], IRN[2], IRN[3]
    # 1) riveted girders / scaffold towers
    for (x0, w, top) in ((10, 16, 60), (206, 12, 84), (330, 18, 52), (452, 14, 96)):
        for y in range(top, H):
            for x in range(x0, x0 + w):
                edge = x in (x0, x0 + w - 1)
                cv.set(x, y, B2 if edge else B1)
            if (y - top) % 18 == 0:
                for x in range(x0 - 3, x0 + w + 3):
                    cv.set(x, y, B2); cv.set(x, y + 1, B1)
        # cross bracing
        for k in range(top, H - 18, 18):
            for i in range(18):
                cv.set(x0 + int(i * (w - 1) / 17), k + i, B2)
                cv.set(x0 + w - 1 - int(i * (w - 1) / 17), k + i, B2)
    # 2) big gear wheels half-sunk behind machinery
    for (cx, cy, r, n) in ((120, 170, 38, 14), (164, 128, 18, 9), (400, 178, 44, 16), (268, 196, 22, 10)):
        gear(cv, cx, cy, r, n, B1, B2, phase=cx * 0.01)
    # 3) anvil-shaped forge blocks along the floor
    for (cx, w, h) in ((60, 70, 34), (300, 90, 40), (480, 60, 28)):
        top = H - h
        for y in range(top, H):
            t = (y - top) / h
            hw = w / 2 * (1.0 if t < 0.25 else 0.62 if t < 0.7 else 0.82)
            for x in range(int(cx - hw), int(cx + hw) + 1):
                cv.set(x, y, B1 if t > 0.25 else B2)
    # 4) hanging chains with crucibles / hooks
    for (cx, ln, kind) in ((36, 120, 'crucible'), (150, 70, 'hook'), (250, 110, 'chain'), (372, 90, 'crucible'), (440, 60, 'hook')):
        for y in range(0, ln):
            if y % 4 < 2:
                cv.set(cx, y, B2); cv.set(cx + 1, y, B1)
            else:
                cv.set(cx - 1, y, B1); cv.set(cx + 2, y, B1); cv.set(cx, y, B0); cv.set(cx + 1, y, B0)
        if kind == 'crucible':
            for y in range(ln, ln + 22):
                t = (y - ln) / 22
                hw = 13 - 5 * t ** 2
                for x in range(int(cx - hw), int(cx + hw) + 2):
                    cv.set(x, y, B1)
            for x in range(cx - 12, cx + 14):
                cv.set(x, ln, MG[3] if (x % 3) else MG[4])       # glowing lip of the molten charge
                cv.set(x, ln + 1, MG[2])
        elif kind == 'hook':
            for (dx, dy) in ((0, 0), (1, 1), (2, 2), (2, 3), (1, 4), (0, 4), (-1, 3)):
                cv.set(cx + dx, ln + dy, B2)
    # 5) pipes running along the lower third
    for (y0, x0, x1) in ((150, 0, 120), (138, 200, 330), (160, 420, 512)):
        for x in range(x0, x1):
            for y in range(y0, y0 + 6):
                cv.set(x, y, B2 if y == y0 else B1 if y < y0 + 5 else B0)
            if x % 40 == 0:
                for y in range(y0 - 1, y0 + 7):
                    cv.set(x, y, B2); cv.set(x + 1, y, B2)
    # rim light: every silhouette pixel whose neighbour below / beside is empty glows with the heat from beneath
    px = cv.img.load()
    hits = []
    for y in range(H - 1):
        for x in range(W):
            if px[x, y][3] == 0:
                continue
            below, up = px[x, y + 1], px[x, y - 1] if y else (0, 0, 0, 0)
            lf, rt = px[(x - 1) % W, y], px[(x + 1) % W, y]
            heat = smooth(40, 216, y)
            if below[3] == 0 and heat > 0.2:
                hits.append((x, y, RIM[min(4, int(1 + heat * 3))]))
            elif (lf[3] == 0 or rt[3] == 0) and h01(x, y, 3) < 0.35 * heat:
                hits.append((x, y, RIM[int(heat * 2)]))
            elif up[3] == 0 and y > 0:
                hits.append((x, y, IRN[4]))
    for (x, y, c) in hits:
        px[x, y] = c
    return cv.img


BUILDERS = {"deep": (build_deep_far, build_deep_mid)}
