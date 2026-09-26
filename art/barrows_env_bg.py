"""Parallax for the `barrows` biome -- THE DROWNED BARROWS.

bg_barrows_far : 512x216 opaque, tileable (period 512), 4 frames `loop`.
                 A vast drowned crypt vault seen through dark water: a far arcade dissolving into the murk, a distant
                 flooded chapel nave (one lancet window holding a faint teal glow), great piers carrying pointed vault
                 arches, three cold shafts of light falling from openings far above, drowned bells hanging on long
                 chains, toppled tombs half-sunk in silt. Animation: caustic ripples crawl down the light shafts and
                 silt motes twinkle (every frame has the same composition).
bg_barrows_mid : 512x216 transparent, tileable, 1 frame `loop`. Near-black silhouettes in the lower two thirds: a
                 broken arcade, snapped pillars, a wall of burial niches, kelp rising from the silt, chains hanging from
                 above (one holding a sunken bell); faint teal rim light from above.

Built like the other *_bg modules: wrapping Canvas, tileable value noise, ordered dithering onto one ramp.
"""
import math, random
from envlib import C, ramp, T, bt, pick, h01, smooth, clamp, Canvas, fbm

W, H = 512, 216
NFR = 4
GAIN = 2.3                     # all far-layer values below are authored dark; this maps them onto the ramp

FAR = ramp("020405", "030607", "04080a", "050a0c", "070c0f", "080f12", "0a1215", "0c1518", "0e181b", "111c20",
           "142024", "172529", "1b2a2e", "203135", "26393c", "2e4446", "385052", "455f5f", "577370", "6f8c86")
NF = len(FAR)
GL = ramp("0d3431", "145a54", "1f8f85", "2fbfb0", "8ff0e0")
SIL = ramp("010304", "020506", "03070a", "050a0c", "070d10")
RIM = ramp("0f2426", "143231", "1b4441", "245a55")

SHAFTS = [(118, 34, 0.18), (268, 44, 0.24), (410, 28, 0.16)]      # (x at top, width at top, strength)
SLANT = 0.22                                                         # shafts lean down-right


def wrapdx(x, cx):
    d = (x - cx) % W
    return d - W if d > W / 2 else d


def haze_v(x, y):
    """Water haze: vault dark above, a lighter band of suspended silt in the middle distance, dark floor."""
    v = 0.12 + 0.13 * math.exp(-((y - 128) / 46.0) ** 2) - 0.07 * smooth(150, 216, y)
    v += 0.05 * (fbm(x, y, 64, 12, 5) - 0.5)
    return v


def shaft_v(x, y, f):
    """Additive brightness of the three cold light shafts; caustic ripples slide down them (period 8px, 2px/frame)."""
    v = 0.0
    for (sx, sw, k) in SHAFTS:
        cx = sx + SLANT * y
        wid = sw * (1 + 0.5 * y / H)
        d = abs(wrapdx(x, cx)) / (wid / 2)
        if d >= 1:
            continue
        edge = smooth(1.0, 0.45, d)
        fall = 1 - 0.75 * smooth(0, 216, y)
        rip = 0.5 + 0.5 * math.sin(2 * math.pi * (y - 2 * f) / 8.0)
        streak = 0.72 + 0.28 * math.sin(wrapdx(x, cx) * 0.4 + sx)         # a few broad brighter rays in the shaft
        v += k * edge * fall * (0.85 + 0.15 * rip) * streak
    return v


def pointed(dx, y, hw, spring, apex):
    """Inside a two-centred pointed arch opening of half-width hw, springing at y=spring, apex at y=apex."""
    if abs(dx) > hw:
        return False
    if y >= spring:
        return True
    if y < apex:
        return False
    r = ((spring - apex) ** 2 + hw * hw) / (2 * hw)
    ccx = hw - r
    return (abs(dx) - ccx) ** 2 + (y - spring) ** 2 <= r * r


def bell_shape(cx, top, h):
    """-> dict (x, y) -> shade (0..1, lit from the upper-left) for a hanging bell silhouette."""
    out = {}
    for y in range(int(top), int(top + h) + 1):
        t = (y - top) / h
        hw = h * (0.20 + 0.12 * t + 0.20 * smooth(0.6, 1.0, t))
        if t < 0.12:
            hw = h * 0.22 * math.sqrt(max(0.0, t / 0.12))
        for x in range(int(cx - hw) - 1, int(cx + hw) + 2):
            dx = x + 0.5 - cx
            if abs(dx) <= hw:
                out[(x, y)] = 0.5 - 0.5 * dx / max(hw, 1)
    return out


def build_far():
    frames = []
    base = Canvas(W, H, wrap=True)
    val = [[0.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            val[y][x] = haze_v(x, y)

    def setv(x, y, v):
        x %= W
        if 0 <= y < H:
            val[y][x] = v

    # 1) far arcade: slender piers and pointed arches dissolving into the murk (period 64)
    for y in range(58, 190):
        for x in range(W):
            lx = (x % 64) - 32
            opening = pointed(lx + 0.5, y, 23, 104, 70)
            if not opening:
                setv(x, y, val[y][x] - 0.035 - 0.02 * smooth(120, 190, y))
            elif y > 150:
                setv(x, y, val[y][x] - 0.01)
    # 2) the flooded chapel nave, centred at x=256 behind the main arch: gabled front, belfry, a glowing lancet
    CX = 256
    for y in range(52, 200):
        for x in range(CX - 44, CX + 45):
            dx = x + 0.5 - CX
            gable = 86 + abs(dx) * 0.62
            if y < gable:
                continue
            v = 0.075 - 0.02 * (dx / 44)
            if abs(dx) > 38:
                v -= 0.01
            setv(x, y, v)
    for y in range(40, 90):                                    # belfry + spire
        for x in range(CX - 8, CX + 9):
            dx = x + 0.5 - CX
            if y < 58 and abs(dx) > (y - 40) * 0.42 + 0.5:
                continue
            setv(x, y, 0.07 - 0.02 * dx / 8)
    for y in range(60, 70):                                    # belfry openings
        for x in (CX - 4, CX - 3, CX + 3, CX + 4):
            setv(x, y, val[y][x] + 0.05)
    # the lancet window with a faint teal glow + rose above it
    glow = {}
    for y in range(106, 162):
        for x in range(CX - 11, CX + 12):
            dx = x + 0.5 - CX
            if pointed(dx, y, 7, 120, 106):
                inner = pointed(dx, y, 5, 122, 109)
                mull = abs(dx) < 1 or y == 134
                if inner and not mull:
                    glow[(x, y)] = 0.3 + 0.35 * smooth(112, 160, y) - 0.2 * (h01(x, y // 3, 4) < 0.3)
                else:
                    setv(x, y, 0.05)
    for y in range(172, 200):                                  # the nave door, drowned in silt
        for x in range(CX - 8, CX + 9):
            if pointed(x + 0.5 - CX, y, 8, 182, 172):
                setv(x, y, 0.035)
    # 3) cold shafts of light (added to the haze later per frame)
    # 4) great piers and vault arches (period 128, piers at 64 + 128k), nearer and darker
    piers = [64 + 128 * k for k in range(4)]
    for y in range(0, H):
        for x in range(W):
            lx = (x % 128) - 64                                 # 0 at a pier axis (x = 64 + 128k)
            ax = ((x - 64) % 128) - 64                          # 0 at an arch crown (x = 128k)
            in_pier = abs(lx) <= 11
            in_open = pointed(ax + 0.5, y, 53, 96, 30)
            if y < 30 or (not in_open and y < 100) or in_pier:
                shade = 0.05
                if in_pier:
                    nx = (lx + 0.5) / 11
                    shade = 0.06 - 0.025 * nx
                    if abs(lx) == 11 and lx < 0:
                        shade = 0.085
                    if (y - 96) % 22 == 0 and y > 96:
                        shade = 0.08                              # pier drum joints catch a little light
                if not in_pier:
                    # arch soffit ring: a lit band hugging the opening
                    if pointed(ax + 0.5, y, 57, 96, 25) and not in_open:
                        shade = 0.08 if ax < 0 else 0.055
                    elif y < 18:
                        shade = 0.035
                setv(x, y, shade)
    # capitals on the piers
    for p in piers:
        for y in range(92, 98):
            for x in range(p - 14 + (97 - y) // 2, p + 15 - (97 - y) // 2):
                setv(x, y, 0.09 if x < p else 0.06)
    # 5) drowned bells hanging on long chains from the vault
    bells = [(12, 72, 20), (424, 100, 26), (498, 58, 14), (150, 64, 12)]
    for (bx, by, bh) in bells:
        for y in range(18, by):
            if (y // 2) % 2 == 0:
                setv(bx, y, 0.06)
            else:
                setv(bx - 1, y, 0.05); setv(bx + 1, y, 0.05)
        for (x, y), sh in bell_shape(bx, by, bh).items():
            lit = shaft_v(x, y, 0) > 0.05
            setv(x, y, 0.035 + 0.05 * sh + (0.05 * sh if lit else 0))
        # the lip catching the cold light
        lip_y = by + bh
        for x in range(int(bx - bh * 0.52), int(bx + bh * 0.52) + 1):
            setv(x, lip_y, 0.07 if x < bx else 0.05)
    # 6) the silt floor with toppled tombs half-sunk
    rnd = random.Random(4)
    for x in range(W):
        top = 196 + 7 * fbm(x, 0, 64, 1, 21) - 3
        for y in range(int(top), H):
            setv(x, y, 0.03 + 0.03 * smooth(top + 4, top, y))
    for (tx, tw, th, tilt) in ((40, 34, 10, 0.08), (178, 28, 8, -0.1), (372, 40, 12, 0.05), (452, 22, 7, 0.0)):
        for x in range(tx, tx + tw):
            top = 200 - th + int((x - tx) * tilt)
            for y in range(top, 204):
                v = 0.045 if y > top else 0.075
                if x == tx:
                    v = 0.07
                setv(x, y, v)
    # render the static base values; per frame add shafts, glow shimmer and motes
    motes = [(rnd.randrange(W), rnd.randrange(20, 200), rnd.random()) for _ in range(150)]
    for f in range(NFR):
        cv = Canvas(W, H, wrap=True)
        for y in range(H):
            for x in range(W):
                v = val[y][x]
                s = shaft_v(x, y, f)
                # shafts are dimmed where they pass behind the near piers (the piers occlude them)
                lx = (x % 128) - 64
                if abs(lx) <= 11:
                    s *= 0.25
                s *= smooth(6, 34, y)                            # shafts fade in below the vault openings
                cv.set(x, y, pick(FAR, GAIN * (v + s), x, y))
        for (x, y), g in glow.items():
            gg = g + 0.08 * math.sin(2 * math.pi * f / NFR + y * 0.2)
            cv.set(x, y, GL[1] if gg > 0.66 else GL[0] if gg > 0.42 else FAR[11])
        for i, (x, y, ph) in enumerate(motes):
            a = (ph + f / NFR) % 1.0
            v = val[y][x] + shaft_v(x, y, f)
            if a < 0.5:
                c = FAR[min(NF - 1, int(GAIN * (v + 0.07) * (NF - 1)))]
                if shaft_v(x, y, f) > 0.06 and a < 0.25:
                    c = FAR[min(NF - 1, int(GAIN * (v + 0.12) * (NF - 1)))]
                cv.set(x, y, c)
        # a few bioluminescent specks drifting on the floor silt (teal, very sparse)
        for (x, y) in ((96, 201), (212, 205), (300, 199), (401, 206), (488, 202)):
            if (x // 7 + f) % 4 != 0:
                cv.set(x, y, GL[1])
        frames.append(cv.img)
    return frames


# =========================================================================== mid layer
def build_mid():
    cv = Canvas(W, H, wrap=True)
    B0, B1, B2, B3 = SIL[1], SIL[2], SIL[3], SIL[4]

    def fill(x, y, c):
        cv.set(x, y, c)

    # 1) the silt floor band
    for x in range(W):
        top = 200 + 6 * fbm(x, 0, 32, 1, 8)
        for y in range(int(top), H):
            fill(x, y, B1)
    # 2) broken arcade (two bays, the second arch snapped off) at x=0..150
    AX = 12
    for y in range(90, H):
        for x in range(AX, AX + 150):
            lx = x - AX
            in_p = lx < 14 or 66 <= lx < 80 or 132 <= lx < 146
            if not in_p:
                # arch spandrels above the openings
                bay = 0 if lx < 66 else 1
                ox = (AX + 40) if bay == 0 else (AX + 106)
                if y < 150 and not pointed(x + 0.5 - ox, y, 26, 130, 100):
                    if bay == 1 and x > AX + 104 - (y - 90) * 0.5 and y < 118:
                        continue                              # the broken arch: a ragged bite
                    if y >= 96:
                        fill(x, y, B2)
                continue
            if lx >= 132 and y < 118 + 10 * h01(x, 0, 3):
                continue                                       # snapped third pier
            fill(x, y, B2 if (lx % 66) < 3 else B1)
    for y in range(90, 96):                                   # cornice
        for x in range(AX - 3, AX + 96):
            fill(x, y, B3 if y == 90 else B2)
    # 3) snapped pillars
    for (px0, w, top) in ((200, 16, 104), (474, 14, 150), (254, 10, 170)):
        for y in range(top - 6, H):
            for x in range(px0, px0 + w):
                jag = top + 5 * math.sin(x * 1.7 + px0) + 3 * h01(x, 1, 9)
                if y < jag:
                    continue
                fill(x, y, B2 if x == px0 else B1)
            if (y - top) % 20 == 10:
                for x in range(px0 - 1, px0 + w + 1):
                    fill(x, y, B2)
        for y in range(H - 12, H):                             # base plinth
            for x in range(px0 - 3, px0 + w + 3):
                fill(x, y, B1)
    # 4) wall of burial niches (x 296..386)
    NX0, NX1, NTOP = 296, 386, 122
    for y in range(NTOP, H):
        for x in range(NX0, NX1):
            top = NTOP + (8 if x > NX1 - 20 else 0) + int(4 * h01(x // 3, 0, 5))
            if y < top:
                continue
            fill(x, y, B1)
    for row, ny in enumerate((136, 166)):
        for col, nx in enumerate(range(NX0 + 8, NX1 - 12, 24)):
            for y in range(ny, ny + 20):
                for x in range(nx, nx + 14):
                    if pointed(x + 0.5 - (nx + 7), y, 7, ny + 6, ny):
                        fill(x, y, B0)
            if (row + col) % 3 == 1:
                # a skull in the niche, lit faintly teal from above
                for (dx, dy) in ((5, 16), (6, 15), (7, 15), (8, 16), (6, 17), (7, 17)):
                    fill(nx + dx, ny + dy, RIM[1])
    # 5) chains from above, one holding a sunken bell
    for (cx, ln) in ((160, 70), (238, 118), (430, 92), (444, 40)):
        for y in range(0, ln):
            if y % 4 < 2:
                fill(cx, y, B3); fill(cx + 1, y, B2)
            else:
                fill(cx - 1, y, B2); fill(cx + 2, y, B2); fill(cx, y, B0); fill(cx + 1, y, B0)
    for (x, y), sh in bell_shape(430.5, 92, 30).items():
        fill(x, y, B2 if sh > 0.7 else B1)
    for x in range(430 - 16, 430 + 18):
        fill(x, 122, B2)
    # 6) kelp rising from the silt, swaying
    rnd = random.Random(8)
    for i in range(16):
        kx = rnd.randrange(W)
        ln = rnd.randint(40, 110)
        ph = rnd.random() * 6
        for y in range(H - 8, H - 8 - ln, -1):
            t = (H - 8 - y) / ln
            x = kx + 5 * math.sin(t * 3.2 + ph) * t
            fill(x, y, B2)
            if t < 0.7:
                fill(x + 1, y, B1)
            if int(y + ph * 3) % 9 == 0:
                fill(x + (2 if i % 2 else -1), y, B1)
                fill(x + (3 if i % 2 else -2), y - 1, B1)
    # rim light: silhouette pixels with open water above catch the cold light; a few left edges too
    px = cv.img.load()
    hits = []
    for y in range(1, H):
        for x in range(W):
            if px[x, y][3] == 0:
                continue
            up = px[x, y - 1]
            lf = px[(x - 1) % W, y]
            if up[3] == 0 and y > 60:
                hits.append((x, y, RIM[2] if h01(x, y, 3) < 0.35 else RIM[1]))
            elif lf[3] == 0 and h01(x, y // 2, 4) < 0.35 and y > 80:
                hits.append((x, y, RIM[0]))
    for (x, y, c) in hits:
        px[x, y] = c
    # a couple of bioluminescent specks on the rubble and the bell's lip
    for (x, y) in ((58, 203), (322, 213), (431, 121), (205, 212)):
        px[x % W, y] = GL[2]
    return cv.img
