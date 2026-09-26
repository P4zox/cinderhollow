"""Props for the `barrows` biome (THE DROWNED BARROWS). Each builder returns (w, h, layers, frames, tags).

db_bell    32x48   idle(1) ring(6)   drowned bronze bell (verdigris, barnacles, a dark crack) on a short chain that
                                     reaches the TOP edge; pivot = top-centre (16, 0). `ring` swings it with a teal shimmer
db_boat    112x32  idle(1) rock(4)   the Ferryman's long black funeral boat, curled prow at the RIGHT with a teal lantern.
                                     Walkable deck top = row y=12 across x=12..99 in EVERY frame; waterline y=24
db_lamp    16x40   loop(4)           iron post holding a jar of glowing teal water, skull finial, flicker + bubbles
db_grate   32x16   idle(1)           rusted drain grate: top 4 rows are the grate bar, tines + dripping water below
db_bones   32x24   loop(4)           heap of drowned bones and skulls, teal marrow pulsing
db_window  48x64   idle(1)           broken sunken-chapel lancet window, pale teal glass shards, hanging seaweed
db_statue  32x64   idle(1)           drowned weeping saint wrapped in chains, barnacle-crusted, one hand raised

Face right, bottom-anchored & horizontally centred (bell: hung by its top-centre). 1px K outline, light from the
upper-left, pixel-clean (alpha 0/255) except the deliberate teal glow pixels of the bell shimmer / bone marrow halo.
"""
import math, random
from envlib import C, ramp, K, T, h01, clamp, smooth, blank, outline
from env_props import Spr
from barrows_env_tiles import ST, VD, BZ, BONE, GL, IR, KELP

LAC = ramp("060709", "0b0d10", "111418", "181c21", "21262c", "2c3239", "3b434b")      # black lacquered wood
RUST = ramp("100b09", "1b1310", "2a1d16", "3a291e", "4c3626")
GLASS = ramp("0f2e2e", "1a4a48", "2c6e68", "4f9a8e", "86c6b6")
SS = ramp("080d0c", "0e1513", "151e1b", "1d2824", "26332e", "31403a", "3e4f47", "4e6158", "63776c", "7d9184")
GLOWA = lambda c, a: (c[0], c[1], c[2], a)


def one(name_layer, img, ms=1000):
    return {"ms": ms, "cels": {name_layer: img}}


# =========================================================================== db_bell
BW, BH = 32, 48
PIV = (16.0, 0.0)
CROWN = 12            # local y where the crown loop starts
BODY0, BODY1 = 15, 42  # local y of the shoulder top and the lip


def bell_hw(ly):
    """Slender gothic bell: a rounded crown, a long gently concave waist, a strong flare into the lip."""
    t = (ly - BODY0) / (BODY1 - BODY0)
    if t < 0:
        return 0
    if t < 0.12:
        return 3.4 + 2.8 * math.sqrt(t / 0.12)
    return 6.2 + 0.4 * t + 3.4 * smooth(0.42, 1.0, t) ** 1.7


CRACK = [(4.5, 42), (4.5, 41), (5.5, 40), (5.5, 39), (4.5, 38), (4.5, 37), (5.5, 36), (5.5, 35), (4.5, 34), (4.5, 33)]
BARN = [(-6.5, 39.5, 1), (-4.5, 40.5, 0), (-8.0, 40.5, 0), (2.5, 18.5, 0)]


def bell_local(lx, ly, clap):
    """Colour at bell-local coords (x right of the axis, y down from the pivot), or None."""
    # chain: face-on ring / edge-on link alternating every 2px
    if 0 <= ly < CROWN:
        if int(ly) % 4 < 2:
            if -1 <= lx < 1:
                return IR[5] if lx < 0 else IR[3]
        else:
            if 1 <= abs(lx) < 2:
                return IR[4] if lx < 0 else IR[2]
        return None
    # crown loop (canon)
    if CROWN <= ly < BODY0:
        if abs(lx) < 2.6:
            if int(ly) == CROWN + 1 and abs(lx) < 0.9:
                return None
            return VD[4] if lx < -0.5 else VD[2] if lx < 1 else VD[1]
        return None
    if BODY0 <= ly <= BODY1 + 0.99:
        hw = bell_hw(ly)
        if abs(lx) > hw:
            return None
        nx = lx / hw
        lv = 2.3 - 1.6 * nx - 0.5 * nx * nx
        if -0.6 < nx < -0.4:
            lv += 1.0                                       # the bronze's specular streak
        if nx > 0.75:
            lv -= 0.8
        iy = int(ly)
        if iy in (19, 36):
            lv += 1                                         # raised mouldings
        elif iy in (20, 37):
            lv -= 1.1
        if iy >= BODY1:
            lv -= 1.4                                       # lip underside
        if iy == BODY1 - 1:
            lv += 0.6
        # dark stains weeping down from the upper moulding
        col = int(math.floor(lx + 20))
        if h01(col, 0, 55) < 0.2 and 21 <= iy < 22 + 11 * h01(col, 1, 56):
            lv -= 0.9
        patch = False
        # crack
        for (cx, cy) in CRACK:
            if abs(lx - cx) < 0.5 and int(ly) == cy:
                return ST[0]
            if abs(lx - (cx - 1)) < 0.5 and int(ly) == cy:
                lv += 1.2
        for (bx, by, big) in BARN:
            d = math.hypot(lx - bx, ly - by)
            if d < 1.0 + big * 0.6:
                if d < 0.5:
                    return ST[1]
                return BONE[4] if lx - bx < 0 else BONE[2]
        if patch:
            return BZ[int(clamp(lv * 0.8, 0, 3))]
        return VD[int(clamp(round(lv), 0, 5))]
    # clapper hanging just below the lip
    if BODY1 + 1 <= ly < BODY1 + 4:
        if abs(lx - clap) < 1.6:
            return IR[4] if lx - clap < 0 else IR[2]
    return None


def bell_frame(theta_deg, clap, glow=0.0, seed=0):
    th = math.radians(theta_deg)
    ct, st = math.cos(th), math.sin(th)
    s = Spr(BW, BH)
    for y in range(BH):
        for x in range(BW):
            dx, dy = x + 0.5 - PIV[0], y + 0.5 - PIV[1]
            lx = dx * ct + dy * st              # rotate back into the bell's frame
            ly = -dx * st + dy * ct
            c = bell_local(lx, ly, clap)
            if c is not None:
                s.set(x, y, c)
    for x in range(15, 17):                     # the chain always reaches the top edge
        if s.get(x, 0)[3] == 0 and x == 15:
            s.set(x, 0, IR[5])
    s.outline()
    img = s.img
    if glow > 0:
        # teal shimmer: a halo 1px outside the outline, fading with the swing, plus a few sparkles
        px = img.load()
        halo = []
        for y in range(14, BH):
            for x in range(BW):
                if px[x, y][3]:
                    continue
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + ddx, y + ddy
                    if 0 <= X < BW and 0 <= Y < BH and px[X, Y] == K and Y > 12:
                        halo.append((x, y))
                        break
        for (x, y) in halo:
            a = int((70 + 60 * (y > 30)) * glow)
            if a > 8:
                px[x, y] = GLOWA(GL[3], a)
        rnd = random.Random(seed)
        for _ in range(int(6 * glow) + 1):
            x = rnd.randint(3, 28)
            y = rnd.randint(30, 47)
            if px[x, y][3] == 0:
                px[x, y] = GL[4] if rnd.random() < 0.5 else GLOWA(GL[3], 200)
    return img


def bell():
    frames = [one("Bell", bell_frame(0, 0.0))]
    seq = [(4.0, -1.0, 1.0), (6.5, -1.5, 0.9), (2.5, -0.5, 0.7), (-4.0, 1.2, 0.5), (-2.5, 0.8, 0.3), (1.0, 0.0, 0.12)]
    for i, (th, cl, g) in enumerate(seq):
        frames.append(one("Bell", bell_frame(th, cl, g, seed=i), ms=[90, 110, 120, 130, 140, 160][i]))
    return BW, BH, ["Bell"], frames, [("idle", 0, 0), ("ring", 1, 6)]


# =========================================================================== db_boat
OW, OH = 112, 32
DECK_Y, DECK_X0, DECK_X1, WATER_Y = 12, 12, 99, 24


def hull_top(x):
    if x < DECK_X0:
        return DECK_Y - (DECK_X0 - x) * 0.55              # the stern sweeps up a little
    return DECK_Y


def hull_bot(x):
    b = 28.0
    if x < 26:
        b -= ((26 - x) / 21.0) ** 1.6 * 15.5
    if x > 84:
        b -= ((x - 84) / 16.0) ** 1.5 * 13.0
    return b


# the prow: a slender swan-neck rising from the bow and curling back into a scroll (x, y, radius)
PROW = [(97.0, 15.0, 2.6), (99.5, 12.0, 2.2), (101.8, 8.8, 1.8), (103.4, 5.8, 1.5), (104.2, 3.2, 1.3),
        (103.9, 1.5, 1.1), (102.8, 0.9, 1.0), (101.6, 1.4, 0.9), (101.2, 2.6, 0.8), (101.9, 3.4, 0.7)]


def spline(pts, n=60):
    out = []
    for i in range(len(pts) - 1):
        (x0, y0, r0), (x1, y1, r1) = pts[i], pts[i + 1]
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t))
    out.append(pts[-1])
    return out


def boat_hull():
    s = Spr(OW, OH)
    x_min, x_max = 4, 100
    for x in range(x_min, x_max + 1):
        top = hull_top(x)
        bot = hull_bot(x)
        if bot <= top + 1:
            continue
        for y in range(int(math.ceil(top)), int(bot) + 1):
            ry = y - DECK_Y
            if ry <= 0:
                c = LAC[5] if y == int(math.ceil(top)) else LAC[4]
            elif ry == 1:
                c = LAC[3]
            elif ry == 3:
                c = VD[3] if (x % 6) else VD[5]              # a verdigris funeral trim with studs
            elif ry == 2 or ry == 4:
                c = LAC[1]
            else:
                lv = 3.2 - 0.14 * (ry - 4)
                if (ry - 5) % 4 == 3:
                    lv = 1                                     # strake seams
                elif (ry - 5) % 4 == 0 and h01(x // 5, ry, 3) < 0.5:
                    lv += 1.2                                  # lacquer sheen along the top of a strake
                if x < x_min + 6 or x > x_max - 10:
                    lv -= 0.5
                c = LAC[int(clamp(round(lv), 0, 6))]
            s.set(x, y, c)
        # keel line
        s.set(x, int(bot), LAC[0])
    # stern post: a short upswept tail
    for i, (x, y) in enumerate(((4, 8), (3, 7), (3, 6), (4, 5))):
        s.set(x, y, LAC[4] if i < 3 else LAC[5])
        s.set(x + 1, y, LAC[2])
    # prow neck + curl
    for (px_, py_, r) in spline(PROW):
        for y in range(int(py_ - r) - 1, int(py_ + r) + 2):
            for x in range(int(px_ - r) - 1, int(px_ + r) + 2):
                d = math.hypot(x + 0.5 - px_, y + 0.5 - py_)
                if d <= r:
                    nx = (x + 0.5 - px_) / max(r, 0.5)
                    ny = (y + 0.5 - py_) / max(r, 0.5)
                    lv = 3.2 - 1.6 * nx - 1.0 * ny
                    s.set(x, y, LAC[int(clamp(round(lv), 1, 6))])
    # glossy lacquer rim: pixels of the prow / stern whose upper or left neighbour is open water catch the light
    rim = []
    for y in range(OH):
        for x in range(OW):
            if s.get(x, y)[3] and (x > 95 or x < 12) and y < DECK_Y + 4:
                if s.get(x - 1, y)[3] == 0 or s.get(x, y - 1)[3] == 0:
                    rim.append((x, y))
    for (x, y) in rim:
        s.set(x, y, LAC[6])
    # the prow's scroll eye: a small verdigris stud
    s.set(102, 2, VD[4])
    # deck gunwale highlight must stay exactly on row 12 over the walkable span
    for x in range(DECK_X0, DECK_X1 + 1):
        s.set(x, DECK_Y, LAC[5] if h01(x, 0, 5) > 0.15 else LAC[6])
    return s


def candle_cluster(s, x0, heights, f, seed):
    for i, h in enumerate(heights):
        x = x0 + i * 2
        top = DECK_Y - h
        for y in range(top, DECK_Y):
            s.set(x, y, BONE[5] if y == top else BONE[4] if i % 2 == 0 else BONE[3])
        # wax dribble down the gunwale
        s.set(x, DECK_Y + 1, BONE[3])
        if i == 0:
            s.set(x, DECK_Y + 2, BONE[2])


def candle_flames(img, x0, heights, f, seed):
    px = img.load()
    for i, h in enumerate(heights):
        x = x0 + i * 2
        top = DECK_Y - h
        flick = (f + i + seed) % 4
        fh = 2 + (flick in (1, 2))
        for k in range(fh):
            y = top - 1 - k
            c = GL[4] if k == 0 else GL[5] if k == 1 and fh == 3 else GL[3]
            if k == fh - 1:
                c = GL[3]
            if 0 <= y < OH:
                px[x, y] = c


def boat_frame(f):
    s = boat_hull()
    candle_cluster(s, 17, (3, 5, 2), f, 0)
    candle_cluster(s, 89, (4, 2), f, 2)
    # frayed rope: a slack loop draped over the gunwale and down the side
    for i in range(24):
        t = i / 23
        x = 30 + 12 * t
        y = DECK_Y + 1 + 6 * math.sin(math.pi * t) + 0.5 * math.sin(f * math.pi / 2) * math.sin(math.pi * t)
        s.set(x, y, RUST[4] if i % 3 else RUST[3])
    # a trailing rope end hanging from the stern post, swaying
    sway = (0, 1, 1, 0)[f]
    for k in range(10):
        s.set(4 + (sway if k > 5 else 0) + (1 if k > 7 else 0) * sway, 9 + k, RUST[3] if k % 2 else RUST[4])
    s.set(4 + 2 * sway, 19, RUST[2]); s.set(5 + 2 * sway, 20, RUST[2])      # frayed strands
    # lantern: an iron arm off the prow curl, a hook, the caged teal lantern swinging a pixel
    arm_y = 2
    for x in range(105, 110):
        s.set(x, arm_y + (1 if x == 105 else 0), IR[4] if x < 108 else IR[3])
    s.set(109, arm_y + 1, IR[3])
    sw = (0, 1, 0, -1)[f]
    lx = 109 + sw
    s.set(109, 4, IR[3])
    s.set(lx, 5, IR[4])
    for x in range(lx - 2, lx + 1 + 1):
        s.set(x, 6, IR[4] if x < lx else IR[2])
    for y in range(7, 11):
        for x in range(lx - 2, lx + 2):
            if x == lx - 2 or x == lx + 1:
                s.set(x, y, IR[3] if x < lx else IR[1])
            else:
                g = 3 if (f % 2 == 0) else 2
                s.set(x, y, GL[g + 1] if (y == 8 and x == lx - 1) else GL[g])
    for x in range(lx - 2, lx + 2):
        s.set(x, 11, IR[2])
    s.outline()
    img = s.img
    candle_flames(img, 17, (3, 5, 2), f, 0)
    candle_flames(img, 89, (4, 2), f, 2)
    return img


def boat():
    frames = [one("Boat", boat_frame(0))]
    for f in range(4):
        frames.append(one("Boat", boat_frame(f), ms=220))
    return OW, OH, ["Boat"], frames, [("idle", 0, 0), ("rock", 1, 4)]


# =========================================================================== db_lamp
def lamp_frame(f):
    Wd, Hd = 16, 40
    s = Spr(Wd, Hd)
    # barnacled stone footing
    for y in range(35, 40):
        hw = 4 + (y - 35) // 2
        for x in range(8 - hw, 8 + hw):
            c = ST[8] if y == 35 else ST[6] if x < 7 else ST[4]
            if y == 39:
                c = ST[3]
            s.set(x, y, c)
    for (x, y) in ((4, 37), (10, 38), (11, 37)):
        s.set(x, y, BONE[4]); s.set(x + 1, y, BONE[2])
    # iron post with verdigris collars
    for y in range(16, 35):
        s.set(7, y, IR[5] if y % 9 else VD[4])
        s.set(8, y, IR[3] if y % 9 else VD[2])
    for y in (22, 30):
        s.set(6, y, VD[3]); s.set(9, y, VD[1])
    # jar: iron cap, glass, glowing water, iron base
    for x in range(4, 12):
        s.set(x, 5, IR[5] if x < 8 else IR[3])
        s.set(x, 15, IR[4] if x < 8 else IR[2])
    for x in range(5, 11):
        s.set(x, 4, IR[4] if x < 8 else IR[2])
    pulse = (0, 1, 0, -1)[f]
    for y in range(6, 15):
        for x in range(4, 12):
            if x in (4, 11):
                c = GLASS[3] if x == 4 else GLASS[1]
            elif y < 8:
                c = GLASS[0]                                 # the air gap above the water
            else:
                d = abs(x + 0.5 - 8) / 3.5
                v = 1.8 - 1.3 * d + 0.5 * pulse + (0.5 if 10 < y < 14 else 0)
                c = GL[int(clamp(round(v), 0, 3))]
            s.set(x, y, c)
    for x in range(5, 11):
        s.set(x, 8, GL[3] if x in (6, 7) else GL[2])         # the meniscus
    # bubbles rising (period 8 over the loop)
    for (bx, ph) in ((6, 0), (9, 4)):
        by = 14 - ((f * 2 + ph) % 6)
        if 9 <= by <= 14:
            s.set(bx, by, GL[4])
    # the finial: a small skull on the cap
    sk = [".###.", "#####", "#o#o#", ".###."]
    for j, row in enumerate(sk):
        for i, ch in enumerate(row):
            if ch == "#":
                s.set(6 + i, j, BONE[5] if (j == 0 or i == 0) else BONE[4] if i < 4 else BONE[3])
            elif ch == "o":
                s.set(6 + i, j, GL[3] if f % 2 == 0 else GL[2])
    s.outline()
    img = s.img
    px = img.load()
    px[5, 9] = GLASS[4]                                      # glint on the glass
    # round the jar's shoulders
    for (x, y) in ((4, 6), (11, 6), (4, 14), (11, 14)):
        px[x, y] = K
    return img


def lamp():
    frames = [one("Lamp", lamp_frame(f), ms=[160, 140, 160, 180][f]) for f in range(4)]
    return 16, 40, ["Lamp"], frames, [("loop", 0, 3)]


# =========================================================================== db_grate
def grate():
    s = Spr(32, 16)
    for x in range(32):
        s.set(x, 0, RUST[4] if h01(x, 0, 2) > 0.3 else VD[4])
        s.set(x, 3, RUST[2] if h01(x, 3, 2) > 0.35 else VD[2])
        for y in (1, 2):
            slot = x % 4 in (1, 2) and 0 < x < 31
            if slot:
                c = ST[0]
                if y == 2 and h01(x, 7, 3) < 0.25:
                    c = GL[1]                                # dark water glinting through the slots
            else:
                c = RUST[3] if y == 1 else RUST[2]
                if h01(x, y, 5) < 0.2:
                    c = VD[3]
            s.set(x, y, c)
    # tines under the bar with water dripping off them
    for x in range(0, 32, 4):
        for y in range(4, 7):
            s.set(x, y, RUST[3] if y < 6 else RUST[1])
            s.set(x + 3, y, RUST[1] if y < 6 else ST[1])
    s.outline()
    img = s.img
    px = img.load()
    for (x, y, c) in ((4, 9, ST[8]), (12, 11, ST[7]), (20, 8, ST[8]), (28, 12, ST[6]), (11, 14, GL[1]),
                      (12, 14, ST[7]), (23, 15, GL[1]), (24, 15, ST[6]), (3, 15, ST[6])):
        px[x, y] = c
    return 32, 16, ["Grate"], [one("Grate", img)], [("idle", 0, 0)]


# =========================================================================== db_bones
def long_bone(s, x0, y0, x1, y1, lit=4):
    """A long bone: 2px shaft (lit top row), knobbed ends."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        s.set(x, y, BONE[lit])
        s.set(x, y + 1, BONE[lit - 2])
    for (x, y) in ((x0, y0), (x1, y1)):
        s.set(x, y - 1, BONE[lit + 1])
        s.set(x, y + 2, BONE[lit - 2])


def skull_big(s, x0, y0, flip=False, dim=0):
    rows = ["..####..", ".######.", "########", "#oo##oo#", "#oo##oo#", ".######.", "..#..#..", "..####.."]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            ii = 7 - i if flip else i
            if ch == "#":
                v = 5 if (j < 2 or i < 2) else 4 if j < 5 else 3
                if i > 5:
                    v -= 1
                s.set(x0 + ii, y0 + j, BONE[max(1, v - dim)])
            elif ch == "o":
                s.set(x0 + ii, y0 + j, ST[1])


BONES_MARROW = [(4, 20), (27, 16), (14, 13), (17, 21)]


def bones_frame(f):
    s = Spr(32, 24)
    # the mound: dark silt with a few dim bone fragments
    for y in range(14, 24):
        hw = 3 + (y - 14) * 1.5
        for x in range(int(16 - hw), int(16 + hw) + 1):
            if 0 <= x < 32:
                r = h01(x // 2, y, 44)
                s.set(x, y, ST[5] if r < 0.5 else ST[4] if r < 0.8 else BONE[1])
    # long bones crossing the heap, broken ends toward the viewer
    long_bone(s, 4, 20, 15, 16, 4)
    long_bone(s, 17, 21, 27, 16, 3)
    long_bone(s, 9, 13, 14, 13, 4)
    # a rib pair arcing out of the silt at the right
    for k, cx in enumerate((22, 25)):
        for i in range(7):
            a = math.pi * (0.15 + 0.7 * i / 6)
            s.set(cx - 3 * math.cos(a), 21 - 5 * math.sin(a), BONE[4 - k] if i < 4 else BONE[3 - k])
    skull_big(s, 11, 4)                     # crowning skull
    skull_big(s, 3, 12, flip=True, dim=1)   # a second skull half-sunk on the left
    s.outline()
    img = s.img
    px = img.load()
    lvl = (1, 2, 3, 2)[f]
    eyes = [(12, 7), (13, 7), (16, 7), (17, 7), (4, 15), (5, 15), (8, 15), (9, 15)]
    for (x, y) in BONES_MARROW:
        px[x, y] = GL[lvl + 1]
    for (x, y) in eyes:
        px[x, y] = GL[lvl - 1]
    for (x, y) in ((12, 8), (17, 8)):
        px[x, y] = GL[max(0, lvl - 2)] if lvl > 1 else ST[1]
    # a soft halo around the marrow at the peak of the pulse (deliberate glow)
    if lvl >= 2:
        a = 60 if lvl == 2 else 110
        for (x, y) in BONES_MARROW:
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                X, Y = x + dx, y + dy
                if 0 <= X < 32 and 0 <= Y < 24 and px[X, Y][3] == 0:
                    px[X, Y] = GLOWA(GL[3], a)
    return img


def bones():
    frames = [one("Bones", bones_frame(f), ms=[300, 240, 340, 240][f]) for f in range(4)]
    return 32, 24, ["Bones"], frames, [("loop", 0, 3)]


# =========================================================================== db_window
def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xc:
                inside = not inside
    return inside


def window():
    Wd, Hd = 48, 64
    s = Spr(Wd, Hd)
    cx = 24
    OUT, IN = 19, 13
    SPRING = 26

    def inside(x, y, hw, spring, top):
        dx = abs(x + 0.5 - cx)
        if y >= spring:
            return dx <= hw
        r = ((spring - top) ** 2 + hw * hw) / (2 * hw)
        ccx = hw - r
        return (dx - ccx) ** 2 + (y + 0.5 - spring) ** 2 <= r * r and y >= top

    for y in range(Hd):
        for x in range(Wd):
            outer = inside(x, y, OUT, SPRING, 1)
            inner = inside(x, y, IN, SPRING, 8)
            if y >= 56:
                outer = abs(x + 0.5 - cx) <= OUT + 2 - (1 if y > 60 else 0)
                inner = False
            if outer and not inner:
                if y < SPRING:
                    ang = math.atan2(y - SPRING, x + 0.5 - cx)
                    jl = int((ang + math.pi) * 9 * 3) % 3 == 0
                else:
                    jl = (y % 8 == 0)
                lv = 5.5 - (x - (cx - OUT)) / (2 * OUT) * 3
                if jl:
                    lv = 2
                if y >= 56:
                    lv = 8 if y == 56 else 6 if y < 59 else 4
                if h01(x, y, 9) < 0.06:
                    lv -= 1.5
                s.set(x, y, ST[int(clamp(round(lv), 1, 10))])
    for y in range(8, 56):
        for x in range(Wd):
            if inside(x, y, IN, SPRING, 8) and not inside(x, y, IN - 2, SPRING, 10):
                s.set(x, y, ST[8] if x < cx else ST[3])
    # tracery: mullion splitting into two sub-lancets, a trefoil in the head; the right mullion stub is snapped
    for y in range(22, 56):
        if 36 <= y < 46:
            continue
        s.set(cx - 1, y, ST[8]); s.set(cx, y, ST[5])
    for side in (-1, 1):
        scx = cx + side * 6
        for i in range(36):
            a = math.pi * i / 36
            x = scx + 6 * math.cos(a) * side * -1
            y = 30 - 8 * math.sin(a)
            s.set(x, y, ST[7] if side < 0 else ST[5])
    for i in range(48):
        a = 2 * math.pi * i / 48
        r = 3.5 + 1.2 * math.cos(3 * a)
        s.set(cx + r * math.cos(a), 15 + r * math.sin(a), ST[7] if math.cos(a) < 0.2 else ST[4])
    # pale teal glass shards still caught in the leading
    shards = [
        [(cx - IN + 2, 44), (cx - 3, 49), (cx - 3, 55), (cx - IN + 2, 55)],
        [(cx + 2, 50), (cx + 8, 53), (cx + IN - 2, 51), (cx + IN - 2, 55), (cx + 2, 55)],
        [(cx - IN + 3, 27), (cx - 7, 32), (cx - IN + 3, 37)],
        [(cx + 2, 20), (cx + 6, 24), (cx + 2, 28)],
        [(cx - 5, 12), (cx - 2, 15), (cx - 4, 18)],
    ]
    for poly in shards:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                if point_in_poly(x + 0.5, y + 0.5, poly) and s.get(x, y)[3] == 0:
                    lv = 2 + (1 if (x + y) % 5 == 0 else 0) - (1 if x > cx else 0)
                    c = GLASS[int(clamp(lv, 0, 4))]
                    if (x - y) % 6 == 0:
                        c = IR[2]
                    s.set(x, y, c)
        s.set(poly[0][0] + 1, poly[0][1] + 1, GLASS[4])
    # barnacles on the jambs and the sill
    for (x, y) in ((6, 44), (8, 47), (39, 50), (41, 38), (12, 55), (30, 55)):
        s.set(x, y, BONE[4]); s.set(x + 1, y, BONE[2]); s.set(x, y + 1, BONE[3]); s.set(x + 1, y + 1, ST[1])
    # seaweed: strands hanging from the arch head and draped over the sill
    def strand(x0, y0, L, sway, ph):
        for k in range(L):
            t = k / max(1, L - 1)
            x = x0 + round(math.sin(k * 0.45 + ph) * sway * (0.3 + t))
            s.set(x, y0 + k, KELP[5] if k % 5 == 1 else KELP[4] if t < 0.8 else KELP[3])
            if t < 0.5:
                s.set(x + 1, y0 + k, KELP[2])
    strand(cx - 8, 10, 22, 1.4, 0.3)
    strand(cx + 5, 8, 14, -1.2, 1.4)
    strand(cx + 9, 13, 26, 1.0, 2.2)
    strand(cx - 16, 56, 8, 0.8, 0.9)
    strand(cx + 14, 56, 6, -0.8, 2.9)
    s.set(cx + 5 + round(math.sin(13 * 0.45 + 1.4) * -1.2 * 1.3), 21, GL[3])      # a glowing bulb on the weed
    s.outline()
    return Wd, Hd, ["Window"], [one("Window", s.img)], [("idle", 0, 0)]


# =========================================================================== db_statue
def statue():
    """A drowned weeping saint: slender hooded figure facing right, head bowed, one hand pressed to the face, the
    other arm raised high with the sleeve fallen back and a broken shackle on the wrist; wrapped in verdigris chains,
    barnacles crusting the hem, weed trailing from the sleeve."""
    Wd, Hd = 32, 64
    s = Spr(Wd, Hd)
    # ---- plinth: two stepped blocks with a verdigris name-plaque
    cxp = 14
    for y in range(52, 64):
        hw = 9 if y < 55 else 11
        for x in range(cxp - hw, cxp + hw + 1):
            lv = 6 - (x - (cxp - hw)) / (2 * hw) * 3.5
            if y in (52, 55):
                lv += 2
            if y in (54, 63):
                lv -= 2
            if h01(x, y, 3) < 0.07:
                lv -= 1
            s.set(x, y, SS[int(clamp(round(lv), 1, 9))])
    for x in range(cxp - 3, cxp + 4):
        for y in range(57, 61):
            s.set(x, y, VD[3] if y == 57 else VD[2] if x < cxp + 3 else VD[1])
    s.set(cxp - 1, 59, VD[0]); s.set(cxp + 1, 59, VD[0])

    # ---- the raised arm: bunched sleeve at the shoulder/elbow, bare forearm, open palm at the upper right
    sleeve = [(15.0, 20.0), (18.5, 12.0), (21.5, 9.5), (23.5, 11.5), (21.5, 17.5), (18.0, 21.0)]
    for y in range(9, 23):
        for x in range(14, 25):
            if point_in_poly(x + 0.5, y + 0.5, sleeve):
                d = (x - 15) / 9.0
                lv = 6.8 - 3.4 * d + (0.8 if (x + y) % 5 == 0 and y > 14 else 0)
                s.set(x, y, SS[int(clamp(round(lv), 1, 9))])
    for i in range(8):                                   # forearm
        t = i / 7
        x, y = 21.4 + 1.6 * t, 10.5 - 6.0 * t
        s.set(x, y, SS[8]); s.set(x + 1, y, SS[5])
    for (x, y, v) in ((23, 3, 8), (24, 3, 6), (22, 2, 8), (23, 2, 7), (24, 2, 6), (22, 1, 8), (23, 1, 7), (24, 1, 5),
                      (25, 2, 5), (23, 0, 7), (24, 0, 6), (21, 3, 7)):
        s.set(x, y, SS[v])                               # open palm, fingers up, thumb out
    # broken shackle on the raised wrist, three links dangling
    for (x, y, c) in ((22, 5, VD[4]), (23, 5, VD[3]), (24, 5, VD[2]), (22, 6, VD[3]), (24, 6, VD[1]),
                      (24, 7, IR[4]), (25, 8, IR[3]), (25, 9, VD[3]), (25, 10, IR[3])):
        s.set(x, y, c)
    # ---- robe: span per row, lit from the left edge
    def L(y):
        if y < 30:
            return 9.6 + 0.07 * (y - 19)
        return 10.4 - 5.6 * ((y - 30) / 21.0) ** 1.5

    def R(y):
        if y < 30:
            return 18.6 - 0.05 * (y - 19)
        return 18.1 + 4.2 * ((y - 30) / 21.0) ** 1.3

    for y in range(18, 52):
        l, r = L(y), R(y)
        if y == 18:
            l, r = l + 1.5, r - 1.0                      # rounded shoulders
        for x in range(int(l), int(math.ceil(r))):
            if not (l <= x + 0.5 <= r):
                continue
            nx = ((x + 0.5) - l) / (r - l)               # 0 at the lit left edge .. 1 at the shadowed right
            lv = 7.2 - 4.6 * nx
            fold = math.sin(nx * 9.5 + 0.8)             # long straight folds, only below the chest
            lv += 0.9 * fold * smooth(24, 36, y)
            if y >= 50:
                lv -= 0.8
            s.set(x, y, SS[int(clamp(round(lv), 1, 9))])
    # ---- hood + bowed head: an egg tilted forward, draped down onto the shoulders
    hx, hy, rx, ry, tilt = 13.6, 13.2, 4.3, 5.6, 0.42
    face = []
    for y in range(6, 20):
        for x in range(7, 21):
            dx, dy = x + 0.5 - hx, y + 0.5 - hy
            u = dx * math.cos(tilt) + dy * math.sin(tilt)
            v = -dx * math.sin(tilt) + dy * math.cos(tilt)
            e = (u / rx) ** 2 + (v / ry) ** 2
            if e <= 1:
                lv = 7.0 - 3.0 * (u / rx + 1) / 2 * 1.6 + (0.6 if v < -2 else 0)
                s.set(x, y, SS[int(clamp(round(lv), 1, 9))])
                if u > rx * 0.45 and -ry * 0.1 < v < ry * 0.75:
                    face.append((x, y))
    for (x, y) in face:
        s.set(x, y, SS[1])                               # the face, lost in the hood's shadow
    # ---- near hand pressed to the face, forearm down across the chest
    for (x, y, v) in ((18, 14, 8), (19, 14, 7), (18, 15, 7), (19, 15, 6), (18, 16, 6), (19, 16, 5)):
        s.set(x, y, SS[v])
    for i, (x, y) in enumerate(((18, 17), (17, 18), (17, 19), (16, 20), (16, 21))):
        s.set(x, y, SS[8] if i < 2 else SS[7]); s.set(x + 1, y, SS[5])
    # ---- chains wrapped around the robe (clipped to it), a loose end dropping over the plinth
    for (y0, slope) in ((26, 0.40), (39, -0.30)):
        for i in range(24):
            x = 6 + i
            y = y0 + (i - 8) * slope
            if s.get(x, y)[3] == 0 or not (L(int(y)) <= x + 0.5 <= R(int(y))):
                continue
            if i % 3 == 0:
                s.set(x, y, VD[4]); s.set(x, y + 1, VD[2])
            elif i % 3 == 1:
                s.set(x, y, IR[4]); s.set(x, y + 1, IR[2])
            else:
                s.set(x, y, VD[3])
    for k in range(13):
        s.set(22 + (1 if k > 8 else 0), 41 + k, VD[3] if k % 2 else IR[3])
    # ---- barnacles crusting the hem and plinth; weed trailing from the sleeve and the hem
    for (x, y) in ((7, 49), (9, 50), (6, 46), (19, 50), (5, 53), (21, 56), (4, 57), (8, 44)):
        s.set(x, y, BONE[4]); s.set(x + 1, y, BONE[2]); s.set(x, y + 1, BONE[3])
    for k in range(9):
        s.set(21 + round(math.sin(k * 0.6) * 0.8), 19 + k, KELP[5] if k < 4 else KELP[4] if k < 7 else KELP[3])
    for k in range(7):
        s.set(6 + round(math.sin(k * 0.7 + 1) * 0.6), 45 + k, KELP[4])
    s.outline()
    img = s.img
    px = img.load()
    # the saint's tears: a thin teal trail from the shadowed face (after the outline, restrained)
    fx = max(face, key=lambda p: p[1] + 0.5 * p[0]) if face else (17, 15)
    for k, c in enumerate((GL[4], GL[3], GL[2])):
        if px[fx[0], fx[1] + k][3]:
            px[fx[0], fx[1] + k] = c
    return Wd, Hd, ["Statue"], [one("Statue", img)], [("idle", 0, 0)]


PROPS = {"db_bell": bell, "db_boat": boat, "db_lamp": lamp, "db_grate": grate, "db_bones": bones,
         "db_window": window, "db_statue": statue}
