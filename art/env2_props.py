"""v2 environment props (docs/ART_SPEC2.md section F). Each returns (w, h, layers, frames, tags).

prop_anvil  48x32  loop(6)            Ashwright's anvil: glowing blade on the face, sparks, quench bucket
prop_bell   32x48  idle(1) ring(6)    the great bell rung to open the Crown (swings, sound rings)
prop_throne 64x80  idle(1)            root throne at the Crown summit, halo of roots, gold sap veins
prop_grave  24x24  idle(1)            knight's grave marker: sword planted in a mossy cairn, crimson rag

Face right, bottom-anchored, horizontally centred. 1px K outline, light from upper-left.
"""
import math, random
from envlib import C, ramp, K, T, bt, h01, pick, smooth, clamp, blank, outline
from env_props import Spr, flame, STONE, GOLD, IRON, CRIM, WOOD
from env2_tiles import C_BARK, C_SAP, C_LEAF, M_MOSS

HOT = ramp("5a1a08", "a8380c", "e06a18", "ffa030", "ffd870", "fff6d0")
BRONZE = ramp("2a1c14", "4a3020", "6e4a28", "946a34", "b88e44", "dcb45c", "f4dc90")
WATER = ramp("16242a", "24404a", "3a6070")


# =========================================================================== anvil
def anvil():
    Wd, Hd = 48, 32

    def base_cel():
        s = Spr(Wd, Hd)
        # wooden stump block with iron hoops
        for y in range(21, 32):
            for x in range(13, 35):
                i = 3 if x < 17 else (2 if x < 30 else 1)
                if y == 21:
                    i = 4
                if (x - 13) % 5 == 3 and y > 22:
                    i = max(1, i - 1)                     # wood grain
                s.set(x, y, WOOD[i])
        for y in (24, 29):
            for x in range(13, 35):
                s.set(x, y, IRON[3] if x < 20 else IRON[2])
        # quench bucket (right)
        for y in range(23, 32):
            for x in range(37, 47):
                i = 3 if x == 37 else (1 if x == 46 else 2)
                s.set(x, y, WOOD[i])
        for x in range(37, 47):
            s.set(x, 25, IRON[2])
            s.set(x, 30, IRON[2])
        for x in range(38, 46):
            s.set(x, 23, WATER[1] if x > 39 else WATER[2])
        # anvil: horn (left) -> face -> heel; waist; feet
        for y in range(11, 15):
            x0 = {11: 8, 12: 5, 13: 7, 14: 10}[y]
            for x in range(x0, 40):
                i = 3
                if y == 11:
                    i = 4
                elif y == 14:
                    i = 1
                if x == 39:
                    i = 1
                s.set(x, y, IRON[i])
        for y in range(15, 19):
            hw = 6 - (y - 15) + (1 if y == 18 else 0)
            for x in range(24 - hw - 2, 24 + hw + 3):
                s.set(x, y, IRON[2] if x < 24 else IRON[1])
        for y in range(19, 21):
            for x in range(15, 34):
                s.set(x, y, IRON[3] if y == 19 else IRON[2])
        s.set(36, 11, IRON[1])              # hardy hole
        s.set(33, 11, IRON[2])
        # tongs leaning on the stump
        s.line(5, 31, 10, 17, IRON[3])
        s.line(6, 31, 11, 17, IRON[1])
        s.set(9, 16, IRON[3])
        s.set(12, 16, IRON[2])
        return s.outline().img

    def hot_cel(ph):
        """Glowing blade on the face + fire-lit anvil face (pulses)."""
        s = Spr(Wd, Hd)
        P = ph * 2 * math.pi
        pulse = 0.5 + 0.5 * math.sin(P)
        # lit face near the blade
        for x in range(12, 38):
            a = 1 - abs(x - 25) / 14
            if a > 0.2 + 0.3 * bt(x, 11):
                s.set(x, 11, HOT[3] if a > 0.7 else HOT[2])
        # blade: tapering, hottest at the middle
        for x in range(15, 34):
            t = (x - 15) / 18
            c = HOT[4] if 0.3 < t < 0.75 else HOT[3]
            if 0.45 < t < 0.6 and pulse > 0.4:
                c = HOT[5]
            s.set(x, 10, c)
            if x < 31:
                s.set(x, 9, HOT[3] if t > 0.2 else HOT[2])
        s.set(34, 10, HOT[2])
        s.set(14, 10, IRON[3])               # tang (cooler)
        s.set(13, 10, IRON[2])
        # steam curling from the bucket
        for k in range(3):
            u = (ph + k / 3) % 1
            s.set(41 + math.sin(u * 6 + k) * 1.5, 21 - u * 10, STONE[5] if u < 0.5 else STONE[4])
        return s.img

    def sparks_cel(ph):
        s = Spr(Wd, Hd)
        rnd = random.Random(7)
        for k in range(12):
            ang = rnd.uniform(-2.8, -0.35)
            sp = rnd.uniform(9, 20)
            off = rnd.random()
            u = (ph + off) % 1.0
            x0, y0 = 24 + rnd.uniform(-5, 5), 9
            x = x0 + math.cos(ang) * sp * u
            y = y0 + math.sin(ang) * sp * u + 22 * u * u
            if y > 30 or u > 0.85:
                continue
            c = HOT[5] if u < 0.25 else HOT[4] if u < 0.5 else HOT[3]
            s.set(x, y, c)
            if u < 0.4:                                  # short streak behind a fast spark
                s.set(x - math.cos(ang), y - math.sin(ang), HOT[3])
        return s.img

    frames = []
    base = base_cel()
    for i in range(6):
        ph = i / 6
        frames.append({"ms": 100, "cels": {"Anvil": base, "Hot": hot_cel(ph), "Sparks": sparks_cel(ph)}})
    return Wd, Hd, ["Anvil", "Hot", "Sparks"], frames, [("loop", 0, 5)]


# =========================================================================== bell
def bell():
    Wd, Hd = 32, 48
    PIV = (15.5, 9.0)                       # bell hangs from here (on the beam)

    def frame_cel():
        s = Spr(Wd, Hd)
        # pale-bark posts rooted in a stone footing, gilded beam with a little gable
        for y in range(6, 44):
            for x in (1, 2, 3):
                s.set(x, y, C_BARK[9] if x == 1 else C_BARK[7] if x == 2 else C_BARK[5])
            for x in (28, 29, 30):
                s.set(x, y, C_BARK[8] if x == 28 else C_BARK[6] if x == 29 else C_BARK[4])
        for y in range(5, 9):
            for x in range(0, 32):
                i = 10 if y == 5 else (8 if y == 6 else 6 if y == 7 else 4)
                s.set(x, y, C_BARK[i])
        for x in range(0, 32):
            s.set(x, 7, C_SAP[3] if x % 4 else C_SAP[4])       # gold inlay line
        for y in range(0, 5):                                   # gable
            hw = 3 + y * 3
            for x in range(16 - hw, 16 + hw):
                if 0 <= x < 32:
                    s.set(x, y, C_BARK[9] if x < 16 else C_BARK[7])
        s.set(15, 1, C_SAP[5])
        s.set(16, 1, C_SAP[4])
        # braces
        for i in range(5):
            s.set(4 + i, 13 - i, C_BARK[7])
            s.set(27 - i, 13 - i, C_BARK[5])
        # stone footing
        s.shaded_rect(0, 43, 31, 47, STONE, 3)
        for x in (8, 16, 24):
            s.set(x, 45, STONE[1])
        return s.outline().img

    def bell_profile(t):
        """half-width at t (0 = crown, 1 = lip)."""
        return 4.5 + 2.5 * t + 5.5 * t ** 5

    def bell_cel(deg, wave):
        s = Spr(Wd, Hd)
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        L = 25.0                                          # crown at local y=2, lip at 2+L
        for y in range(Hd):
            for x in range(Wd):
                # inverse-rotate the pixel into bell space (pivot PIV)
                dx, dy = x + 0.5 - PIV[0], y + 0.5 - PIV[1]
                lx = dx * ca + dy * sa
                ly = -dx * sa + dy * ca
                if 0 <= ly < 2:                            # hanger loop
                    if abs(lx) < 1.6:
                        s.set(x, y, BRONZE[3] if lx < 0 else BRONZE[2])
                    continue
                t = (ly - 2) / L
                if not 0 <= t <= 1:
                    continue
                hw = bell_profile(t)
                if t < 0.12:                               # domed shoulder
                    hw *= math.sqrt(max(0.0, t / 0.12)) * 0.5 + 0.5
                if abs(lx) > hw:
                    continue
                u = lx / hw                                # -1 left .. 1 right
                v = 0.62 - 0.45 * u - 0.12 * t
                if -0.62 < u < -0.38 and t > 0.12:
                    v += 0.28                              # vertical specular streak
                c = BRONZE[int(round(clamp(v) * (len(BRONZE) - 1)))]
                if abs(t - 0.22) < 0.03 or abs(t - 0.84) < 0.03 or t > 0.96:
                    c = BRONZE[6] if u < -0.2 else BRONZE[5] if u < 0.4 else BRONZE[3]
                # emblem: the Root sigil in the middle
                if 0.45 < t < 0.7 and abs(u) < 0.28:
                    ey = (t - 0.45) / 0.25
                    if abs(u) < 0.07 or (abs(abs(u) - ey * 0.25) < 0.07 and ey > 0.3):
                        c = C_SAP[4] if u < 0.05 else C_SAP[3]
                s.set(x, y, c)
        # clapper just under the lip
        cx = PIV[0] + (-sa) * (L + 3.5) + math.sin(a * 1.6) * 1.5
        cy = PIV[1] + ca * (L + 3.5)
        for (ddx, ddy, c) in ((0, 0, IRON[2]), (1, 0, IRON[1]), (0, 1, IRON[2]), (1, 1, IRON[1]), (0, -1, IRON[3])):
            s.set(cx + ddx, cy + ddy, c)
        s.outline()
        # the toll: gold ripples spreading out under the lip + motes shaken loose
        if wave > 0:
            for k, r in enumerate((wave * 3 + 2, wave * 3 + 6)):
                y = 40 + k
                for side in (-1, 1):
                    for d in range(3):
                        X = 15.5 + side * (r + d)
                        if 4 <= X < 28 and s.get(int(X), y)[3] == 0:
                            s.set(X, y, C_SAP[5] if d == 0 else C_SAP[3])
            rnd = random.Random(wave)
            for m in range(4):
                s.set(6 + rnd.randrange(20), 10 + rnd.randrange(6) + wave * 2, C_SAP[4])
        return s.img

    fr = frame_cel()
    frames = [{"ms": 200, "cels": {"Frame": fr, "Bell": bell_cel(0, 0)}}]
    for (deg, wave, ms) in ((9, 0, 90), (-10, 1, 90), (7, 2, 100), (-5, 3, 110), (3, 4, 120), (-1, 0, 150)):
        frames.append({"ms": ms, "cels": {"Frame": fr, "Bell": bell_cel(deg, wave)}})
    return Wd, Hd, ["Frame", "Bell"], frames, [("idle", 0, 0), ("ring", 1, 6)]


# =========================================================================== throne
def _bez(p0, p1, p2, p3, w0, w1, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    segs = [(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], w0 + (w1 - w0) * i / n) for i in range(n)]
    return segs, pts


def throne():
    """A high-backed seat grown from braided roots: a dark heartwood back panel with a hollow that
    cradles a glowing seed, twisting outer roots that end in a crown of curled points, scrolled
    armrests, roots spilling over the seat front onto a two-step bark dais."""
    Wd, Hd = 64, 80
    from env2_bg import shade_limbs
    s = Spr(Wd, Hd)
    BK = C_BARK
    # --- dais: two stepped bark tiers with a gold inlay
    for y in range(71, 80):
        for x in range(1, 63):
            i = 9 if y == 71 else (7 if y < 75 else 5)
            if x < 3:
                i += 1
            if x > 60:
                i -= 2
            if y == 75:
                i = 4
            s.set(x, y, BK[i])
    for y in range(65, 71):
        for x in range(7, 57):
            i = 10 if y == 65 else (8 if y < 68 else 6)
            if x > 54:
                i -= 2
            s.set(x, y, BK[i])
    for x in range(8, 56):
        if x % 3 != 0:
            s.set(x, 67, C_SAP[3] if x % 6 < 3 else C_SAP[2])
    # --- back panel: pointed-arch slab of dark heartwood with vertical grain
    for y in range(12, 56):
        for x in range(20, 45):
            dx = abs(x + 0.5 - 32.5)
            top = 12 + (dx / 12.5) ** 1.6 * 12          # pointed arch
            if y < top:
                continue
            i = 5 - (1 if x > 34 else 0) - (1 if x > 40 else 0) + (1 if x < 24 else 0)
            if (x * 7 + y // 6) % 5 == 0:
                i -= 1                                  # grain
            s.set(x, y, BK[max(2, i)])
    # hollow in the panel with the glowing seed
    for y in range(24, 46):
        for x in range(25, 41):
            d = ((x + 0.5 - 32.5) / 6.5) ** 2 + ((y + 0.5 - 35) / 10.5) ** 2
            if d <= 1:
                s.set(x, y, BK[1] if d > 0.55 else BK[2])
    for y in range(24, 46):                             # sap-glow on the hollow's lower rim
        for x in range(25, 41):
            d = ((x + 0.5 - 32.5) / 6.5) ** 2 + ((y + 0.5 - 35) / 10.5) ** 2
            if 0.75 < d <= 1 and y > 36:
                s.set(x, y, C_SAP[1] if y < 42 else C_SAP[2])
    # --- roots (shaded tubes)
    segs = []
    veins = []
    R = [  # outer twisting roots rising from the dais to curled crown points
        ((14, 70), (10, 50), (24, 30), (14, 8), 8, 3.0),
        ((50, 70), (54, 50), (40, 30), (50, 8), 8, 3.0),
        # inner roots hugging the panel edges
        ((21, 60), (19, 48), (23, 36), (22, 24), 4, 2.2),
        ((44, 60), (46, 48), (42, 36), (43, 24), 4, 2.2),
        # crown points: short tapering spikes on the arch
        ((32.5, 14), (32.5, 10), (32.5, 6), (32.5, 2), 3.6, 1.0),
        ((29, 15), (28, 12), (27, 9), (25.5, 6), 3.0, 1.0),
        ((36, 15), (37, 12), (38, 9), (39.5, 6), 3.0, 1.0),
        # armrests: scrolls curling forward over the seat
        ((18, 62), (6, 60), (4, 46), (12, 46), 6, 2.6),
        ((47, 62), (58, 60), (60, 46), (52, 46), 6, 2.6),
        # roots spilling over the seat front onto the dais
        ((22, 56), (20, 62), (14, 66), (6, 70), 4, 2),
        ((42, 56), (45, 62), (51, 66), (58, 70), 4, 2),
        ((31, 57), (30, 62), (27, 66), (24, 70), 3.2, 1.6),
    ]
    for (p0, p1, p2, p3, w0, w1) in R:
        sg, pts = _bez(p0, p1, p2, p3, w0, w1)
        segs += sg
        veins.append(pts)
    # curled tips of the outer roots
    for (cx, cy, sgn) in ((14, 8, -1), (50, 8, 1)):
        pts = [(cx + sgn * (2.5 - 2.5 * math.cos(t)), cy - 2.5 * math.sin(t)) for t in [i / 10 * 4.2 for i in range(11)]]
        for i in range(10):
            segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 2.6 - i * 0.14))
    # gilded halo ring behind the crown points
    for y in range(0, 26):
        for x in range(18, 48):
            d = math.hypot(x + 0.5 - 32.5, (y + 0.5 - 12) * 1.05)
            if 9.0 <= d <= 11.9:
                ang = math.atan2(y + 0.5 - 12, x + 0.5 - 32.5)
                v = 0.5 - 0.5 * math.cos(ang + 2.2)
                s.set(x, y, pick(C_SAP[1:6], 0.2 + 0.8 * v, x, y))
    for (x, y), (w, v) in shade_limbs(segs).items():
        if 0 <= x < Wd and 0 <= y < Hd:
            vv = 0.02 + 0.9 * v
            if w > 2.8 and math.sin(v * 20 + (x + y) * 0.35) > 0.72:
                vv -= 0.28                               # twisting bark furrows
            s.set(x, y, pick(BK[3:12], vv, x, y))
    # --- seat slab
    for y in range(52, 58):
        for x in range(16, 49):
            i = 10 if y == 52 else (8 if y < 55 else 5)
            if x == 16:
                i += 1
            if x > 46:
                i -= 2
            s.set(x, y, BK[min(11, i)])
    for x in range(18, 47):
        s.set(x, 53, C_SAP[3] if x % 4 else C_SAP[4])
    for y in range(58, 65):                             # shadow under the seat
        for x in range(19, 46):
            if s.get(x, y)[3] == 0 or s.get(x, y) in BK[3:6]:
                s.set(x, y, BK[2] if (x + y) % 4 else BK[3])
    # --- glowing sap veins in the big roots
    for pts in veins[:2] + veins[7:9]:
        for i, (x, y) in enumerate(pts):
            if 4 < i < 36 and i % 3 != 0:
                if s.get(int(x), int(y))[3]:
                    s.set(x - 0.5, y - 0.5, C_SAP[4] if i % 7 else C_SAP[5])
    # the seed of the Root
    for (dx, dy, c) in ((0, 0, 6), (1, 0, 6), (0, 1, 5), (1, 1, 5), (-1, 0, 4), (2, 0, 4), (0, -1, 5), (1, -1, 5),
                        (-1, 1, 3), (2, 1, 3), (0, 2, 4), (1, 2, 3), (0, -2, 3), (1, -2, 2)):
        s.set(32 + dx, 34 + dy, C_SAP[c])
    for (x, y) in ((29, 30), (36, 31), (28, 38), (37, 37)):  # motes around it
        s.set(x, y, C_SAP[3])
    s.set(32, 1, C_SAP[6])
    s.set(32, 2, C_SAP[5])
    s.outline()
    for (x, y) in ((11, 70), (12, 70), (47, 64), (49, 70), (24, 64)):
        s.set(x, y, C_LEAF[4])
    return Wd, Hd, ["Throne"], [{"ms": 200, "cels": {"Throne": s.img}}], [("idle", 0, 0)]


# =========================================================================== grave
def grave():
    Wd, Hd = 24, 24
    s = Spr(Wd, Hd)
    # cairn of rounded stones
    stones = [(6, 21, 3.4, 2.4), (12, 21.5, 3.6, 2.4), (18, 21, 3.2, 2.4), (9, 18, 3.0, 2.2), (15, 18, 3.2, 2.2),
              (12, 15.5, 2.6, 1.8)]
    for (cx, cy, rx, ry) in stones:
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if nx * nx + ny * ny <= 1:
                    v = 0.5 - 0.35 * (nx * 0.6 + ny * 0.8)
                    c = pick(STONE[1:6], v, x, y)
                    if nx * nx + ny * ny > 0.7 and nx + ny > 0.5:
                        c = STONE[1]
                    if ny < -0.45 and h01(x, y, 3) < 0.7:
                        c = M_MOSS[5] if ny < -0.7 else M_MOSS[4]
                    s.set(x, y, c)
    for x in range(1, 23):
        s.set(x, 23, STONE[1] if x % 3 else M_MOSS[3])
    # the planted sword (leaning slightly), crossguard, grip, pommel
    for y in range(4, 17):
        x = 12 + (1 if y < 8 else 0)
        s.set(x, y, STONE[6] if y > 7 else STONE[5])
        s.set(x + 1, y, STONE[3])
    for x in range(9, 18):
        s.set(x, 6, GOLD[1] if x > 13 else GOLD[2])
    s.set(9, 5, GOLD[1])
    s.set(17, 7, GOLD[0])
    for y in range(2, 6):
        s.set(13, y, WOOD[2] if y % 2 else WOOD[3])
    s.set(13, 1, GOLD[2])
    s.set(14, 1, GOLD[1])
    s.outline()
    # crimson rag tied to the guard, trailing left in the wind
    for (x, y, c) in ((10, 7, 2), (9, 7, 2), (8, 8, 1), (7, 8, 2), (6, 9, 1), (5, 9, 1), (8, 7, 3), (7, 9, 0),
                      (4, 10, 0), (6, 8, 3)):
        s.set(x, y, CRIM[c])
    return Wd, Hd, ["Grave"], [{"ms": 200, "cels": {"Grave": s.img}}], [("idle", 0, 0)]


PROPS = {"prop_anvil": anvil, "prop_bell": bell, "prop_throne": throne, "prop_grave": grave}
