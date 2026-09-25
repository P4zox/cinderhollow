"""Parallax backgrounds: bg_<biome>_far (512x216 opaque) and bg_<biome>_mid (512x216, transparent
except silhouettes in the lower 2/3). Everything wraps horizontally (period 512)."""
import math, random
from envlib import (C, ramp, T, K, bt, pick, pick_i, h01, vnoise, fbm, smooth, clamp, lerpc,
                    Canvas)

W, H = 512, 216


def tn(x, y, sx, sy, seed):
    """tileable single-octave noise (sx must divide 512)."""
    return vnoise(x, y, sx, sy, seed, W // sx)


def wrapdx(x, cx):
    d = (x - cx) % W
    return d - W if d > W / 2 else d


# =========================================================================== generic shapes
def limb_tree(rnd, x, y, ang, length, width, depth, curl, segs, spread=(0.35, 0.6), shrink=(0.55, 0.7),
              step=3.0, twig=True, grav=0.0):
    """Recursive branching curve; appends (x0,y0,x1,y1,w) to segs. ang: radians, 0=right, pi/2=up."""
    n = max(2, int(length / step))
    for i in range(n):
        ang += curl + rnd.uniform(-0.07, 0.07)
        x2 = x + math.cos(ang) * step
        y2 = y - math.sin(ang) * step + grav * i
        w = width * (1 - 0.4 * i / n)
        segs.append((x, y, x2, y2, w))
        x, y = x2, y2
        if twig and depth >= 1 and i > 1 and i % 4 == 2:
            side = rnd.choice((-1, 1))
            limb_tree(rnd, x, y, ang + side * rnd.uniform(0.5, 0.9), length * 0.35, max(0.8, width * 0.4),
                      0, -side * 0.03, segs, step=step, twig=False, grav=grav)
    if depth > 0:
        for side in (-1, 1):
            limb_tree(rnd, x, y, ang + side * rnd.uniform(*spread), length * rnd.uniform(*shrink),
                      width * 0.62, depth - 1, side * 0.02, segs, spread, shrink, step, twig, grav)
    return segs


def raster_segs(segs):
    """-> dict (x,y) -> (w at that point, is_core)"""
    out = {}
    for (x0, y0, x1, y1, w) in segs:
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        r = max(0.5, w / 2)
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for yy in range(int(y - r) - 1, int(y + r) + 2):
                for xx in range(int(x - r) - 1, int(x + r) + 2):
                    d2 = (xx - x) ** 2 + (yy - y) ** 2
                    if d2 <= r * r + 0.25:
                        core = d2 <= (r - 1) ** 2
                        k = (xx % W, yy)
                        pw, pc = out.get(k, (0, False))
                        out[k] = (max(pw, w), pc or core)
    return out


def haze_toward(cv, y0, y1, pairs, amt=1.0):
    """Dither colours in `pairs` (dict c -> hazier c) progressively from y0 to y1."""
    for y in range(H):
        s = smooth(y0, y1, y) * amt
        if s <= 0:
            continue
        for x in range(W):
            c = cv.px[x, y]
            if c in pairs and s > bt(x, y):
                cv.px[x, y] = pairs[c]


# =========================================================================== RAMPARTS
R_SKY = ramp("0c0a17", "120e22", "19122b", "221733", "2c1c3a", "38213f", "462742", "552d44", "663445",
             "7a3d46", "8e4a47", "a25a4a", "b46c4e", "c48054", "d29760", "deb070", "e9ca88", "f3e2ac")
R_GOLD = ramp("6a4630", "8e6038", "b4843e", "d4a44a", "ecc466", "f8e098", "fff6d0")
R_MT = ramp("1a1428", "221a32", "2c223c", "362a46", "423250", "4e3a58")
TREE_X, TREE_Y = 176, 132     # fallen tree: the upturned root-mass stands here


def r_sky_v(x, y):
    t = clamp(y / 150.0)
    v = 0.04 + 0.60 * t ** 1.9
    dx, dy = wrapdx(x, TREE_X + 40) / 190.0, (y - 96) / 110.0
    d = math.sqrt(dx * dx + dy * dy)
    v += 0.30 * max(0.0, 1 - d) ** 1.8
    return v


def r_ridge(x, base, amp, seed, sx=64):
    return base + amp * (fbm(x, 0, sx, 1, seed) - 0.5) * 2


def build_ramparts_far():
    cv = Canvas(W, H, wrap=True)
    # --- sky + crepuscular rays
    for y in range(H):
        for x in range(W):
            v = r_sky_v(x, y)
            ang = math.atan2(y - 96, wrapdx(x, TREE_X + 40))
            ray = 0.5 + 0.5 * math.sin(ang * 23 + 1.3)
            if y > 40:
                v += 0.035 * ray * smooth(40, 110, y) * max(0, 1 - abs(wrapdx(x, TREE_X + 40)) / 220)
            cv.set(x, y, pick(R_SKY, v, x, y))
    # --- stratus cloud bands, lit from below by the tree glow
    for y in range(20, 128):
        for x in range(W):
            n = fbm(x, y, 128, 7, 40) * 0.7 + tn(x, y, 32, 3, 41) * 0.3
            band = math.sin(y * 0.16 + fbm(x, 0, 256, 1, 42) * 4)
            f = n + 0.18 * band - 0.62
            if f > 0:
                v = r_sky_v(x, y) + 0.10 + 0.25 * f
                under = cv.get(x, y + 2)
                if f < 0.04:      # soft dithered fringe
                    if bt(x, y) > f / 0.04:
                        continue
                cv.set(x, y, pick(R_SKY, v, x, y))
    # stars in the dark top
    rnd = random.Random(5)
    for _ in range(70):
        x, y = rnd.randrange(W), rnd.randrange(0, 48)
        if r_sky_v(x, y) < 0.11 and cv.get(x, y) in R_SKY[:3]:
            cv.set(x, y, R_SKY[8] if rnd.random() < 0.8 else R_SKY[12])

    # --- the Pale Root: a colossal fallen golden tree. Its torn-up root plate stands on end at
    # TREE_X; the trunk lies along the horizon to the right, the broken crown slumps beyond.
    rnd = random.Random(1337)
    roots = []
    for i in range(15):
        deg = -30 + i * 15 + rnd.uniform(-5, 5)          # radiate around the upper half + sides
        ln = rnd.uniform(34, 52) * (1.0 if 20 < deg < 160 else 0.75)
        curl = rnd.uniform(-0.02, 0.02) + (0.012 if deg > 90 else -0.012)
        limb_tree(rnd, TREE_X + math.cos(math.radians(deg)) * 12, TREE_Y - 22 - math.sin(math.radians(deg)) * 12,
                  math.radians(deg), ln, rnd.uniform(3.2, 4.6), 2, curl, roots,
                  spread=(0.25, 0.5), shrink=(0.45, 0.6), step=2.5, twig=False)
    rootpx = raster_segs(roots)
    crown = []
    for (x0, y0, deg, ln, w) in ((372, 128, 85, 44, 4.6), (376, 132, 45, 48, 4.4), (380, 138, 115, 34, 3.6),
                                 (384, 140, 15, 42, 3.6), (368, 124, 135, 30, 3.0), (390, 142, 65, 36, 3.2)):
        limb_tree(rnd, x0, y0, math.radians(deg), ln, w, 2, -0.035, crown, spread=(0.4, 0.8),
                  shrink=(0.5, 0.65), grav=0.35, step=2.5, twig=False)
    crownpx = raster_segs(crown)

    def trunk_geo(x):
        t = (x - TREE_X) / (360 - TREE_X)
        return TREE_Y - 18 + 22 * t, 16 * (1 - t) + 10 * t

    # glow halo: sky brightened around every part of the tree
    halo = {}
    for (x, y) in list(rootpx) + list(crownpx):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    k = ((x + dx) % W, y + dy)
                    halo[k] = max(halo.get(k, 0), 1 - (dx * dx + dy * dy) / 20)
    for x in range(TREE_X, 372):
        cy, hw = trunk_geo(x)
        for y in range(int(cy - hw - 6), int(cy - hw)):
            k = (x % W, y)
            halo[k] = max(halo.get(k, 0), (y - (cy - hw - 6)) / 7)
    for (x, y), a in halo.items():
        if 0 <= y < H:
            cv.set(x, y, pick(R_SKY, r_sky_v(x, y) + 0.15 * a, x, y))
    # crown foliage: dim golden leaf-clouds drooping over the far end
    for y in range(80, 160):
        for x in range(340, 470):
            dx, dy = (x - 404) / 62, (y - 122) / 30
            f = 1 - (dx * dx + dy * dy)
            leaf = tn(x, y, 8, 4, 71) * 0.7 + tn(x, y, 4, 2, 72) * 0.3
            f = f * 0.9 + leaf * 0.5 - 0.55
            if f > 0.04:
                v = 0.30 + 0.4 * f + 0.25 * (leaf - 0.5) - 0.15 * smooth(130, 155, y)
                cv.set(x, y, pick(R_GOLD[:5], v, x, y))
    TG = R_GOLD
    for (x, y), (w, core) in rootpx.items():
        up = smooth(TREE_Y + 5, TREE_Y - 60, y)
        cv.set(x, y, TG[4] if core and w > 2.0 else (TG[3] if w > 1.6 or up > 0.5 else TG[2]))
    for (x, y), (w, core) in crownpx.items():
        cv.set(x, y, TG[3] if core else TG[2])
    # root plate: dense tangle of gold roots seen end-on, dark gaps between
    for y in range(TREE_Y - 46, TREE_Y + 2):
        for x in range(TREE_X - 24, TREE_X + 25):
            dx, dy = (x - TREE_X) / 23, (y - (TREE_Y - 21)) / 24
            d = dx * dx + dy * dy
            n = tn(x, y, 8, 8, 81) * 0.6 + tn(x, y, 4, 4, 83) * 0.4
            if d < 1 and (d < 0.82 or n > 0.5):
                ang = math.atan2(dy, dx)
                fib = math.sin(ang * 11 + n * 5 + math.sqrt(d) * 2)
                v = 0.62 - 0.35 * d + 0.25 * (n - 0.5) + 0.14 * smooth(0.2, -0.9, dx + dy)
                if fib > 0.45:
                    v -= 0.28
                c = pick([R_MT[3], TG[0], TG[1], TG[2], TG[3], TG[4]], v, x, y)
                cv.set(x, y, c)
    # trunk: massive glowing log lying along the horizon, bark ridges along its length
    for x in range(TREE_X + 14, 366):
        cy, hw = trunk_geo(x)
        for y in range(int(cy - hw), int(cy + hw) + 1):
            dy = (y - cy) / hw
            groove = math.sin(dy * 8.5 + math.sin(x * 0.06) * 1.2 + math.sin(x * 0.17) * 0.4)
            v = 0.78 - 0.28 * abs(dy + 0.35) - (0.26 if dy > 0.4 else 0)
            if groove > 0.6:
                v -= 0.2
            cv.set(x, y, pick(TG[:6], v, x, y))
        cv.set(x, int(cy - hw), TG[5] if x % 7 else TG[4])
    # splintered broken end
    for i, (dx, up) in enumerate(((0, 0), (1, 3), (2, 1), (3, 5), (4, 2), (5, 4), (6, 0))):
        x = 366 + dx
        cy, hw = trunk_geo(x)
        for y in range(int(cy - hw) - up, int(cy + hw) - 2 * (dx // 2) + 1):
            cv.set(x, y, TG[3] if y < cy else TG[1])
    # broken snag where the crown tore away
    for (x, y) in ((366, 136), (368, 134), (369, 133), (371, 135), (372, 137)):
        cv.set(x, y, TG[3])

    # --- distant mountains / plateaus with fortress silhouettes, hazy
    for x in range(W):
        ridge = r_ridge(x, 136, 12, 50, 128) + 8 * (tn(x, 0, 16, 1, 51) - 0.5)
        # lower in front of the tree so the trunk stays visible
        ridge += 8 * smooth(90, 0, abs(wrapdx(x, 280)))
        for y in range(int(ridge), H):
            s = smooth(ridge, ridge + 50, y)
            v = 0.62 - 0.35 * s + 0.25 * smooth(150, 216, y)
            cv.set(x, y, pick(R_MT, v, x, y))
        cv.set(x, int(ridge), R_MT[5])
    # fortress silhouettes on the ridge
    TOW = [(20, 10, 96, "spire"), (36, 14, 108, "crenel"), (14, 50, 118, "wall"), (440, 12, 92, "spire"),
           (458, 9, 104, "broken"), (420, 70, 120, "wall"), (486, 14, 110, "crenel")]
    for (x0, w, top, kind) in TOW:
        for x in range(x0, x0 + w):
            for y in range(top, 160):
                cv.set(x, y, pick(R_MT, 0.2 + 0.4 * smooth(top + 10, 160, y), x, y))
        if kind == "spire":
            for dy in range(int(w * 1.8)):
                hw = (w / 2 + 1) * (1 - dy / (w * 1.8))
                for x in range(int(x0 + w / 2 - hw), int(x0 + w / 2 + hw) + 1):
                    cv.set(x, top - dy, R_MT[0])
        elif kind in ("crenel", "wall"):
            for x in range(x0, x0 + w):
                if (x - x0) % 4 < 2:
                    cv.set(x, top - 1, R_MT[0])
                    cv.set(x, top - 2, R_MT[0])
        elif kind == "broken":
            for x in range(x0, x0 + w):
                for dy in range(int(h01(x, 0, 3) * 7)):
                    cv.set(x, top - dy, R_MT[0])
    for (x, y) in ((24, 104), (25, 104), (40, 114), (444, 100), (445, 108), (462, 110), (430, 124)):
        cv.set(x, y, R_GOLD[3])
    # --- low valley fog bands (lighter where the tree lights them)
    for y in range(150, H):
        for x in range(W):
            n = fbm(x, y, 128, 4, 60)
            f = n - 0.55 + 0.25 * math.sin(y * 0.3 + n * 6)
            if f > 0 and f * 3 > bt(x, y):
                v = 0.30 + 0.25 * max(0, 1 - abs(wrapdx(x, 250)) / 200) - 0.15 * smooth(170, 216, y)
                cv.set(x, y, pick(R_SKY[3:12], v, x, y))
    return cv.img


R_SIL = ramp("0f0d17", "15121e", "1c1826", "241f30", "2e2839", "3a3143")
R_RIM = C("6a4a4c")
R_RIM2 = C("8a5e52")
R_FOG = {R_SIL[0]: R_SIL[2], R_SIL[1]: R_SIL[3], R_SIL[2]: R_SIL[3], R_SIL[3]: R_SIL[4],
         R_RIM: R_SIL[4], R_RIM2: R_RIM}


def build_ramparts_mid():
    cv = Canvas(W, H, wrap=True)
    far_c, far_top = R_SIL[3], R_SIL[4]
    body, shade, dark = R_SIL[2], R_SIL[1], R_SIL[0]

    def rect(x0, x1, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                cv.set(x, y, c)

    def rim_pass(c_body=(body, shade), rim=R_RIM, rim2=R_RIM2):
        """1px rim light on top edges and left edges of dark silhouettes (sky behind)."""
        px = cv.img.load()
        tops, lefts = [], []
        for y in range(1, H):
            for x in range(W):
                c = px[x, y]
                if c not in c_body:
                    continue
                if px[x, y - 1][3] == 0 or px[x, y - 1] in (far_c, far_top):
                    tops.append((x, y))
                elif px[(x - 1) % W, y][3] == 0 or px[(x - 1) % W, y] in (far_c, far_top):
                    lefts.append((x, y))
        for (x, y) in tops:
            px[x, y] = rim2 if h01(x, y, 3) < 0.3 else rim
        for (x, y) in lefts:
            px[x, y] = rim if (y // 4) % 3 else R_SIL[4]

    # ---- A: distant curtain wall + small towers (hazy, low contrast)
    for x in range(W):
        top = 146 + int(3 * (tn(x, 0, 64, 1, 3) - 0.5))
        rect(x, x, top, H - 1, far_c)
        if x % 6 < 3:
            rect(x, x, top - 2, top - 1, far_c)
        cv.set(x, top - (2 if x % 6 < 3 else 0), far_top)
    for (cx, w, top) in ((20, 8, 124), (150, 10, 116), (270, 7, 128), (400, 9, 120)):
        rect(cx - w // 2, cx + w // 2, top, 150, far_c)
        for dy in range(1, w + 3):
            hw = (w / 2 + 1) * (1 - dy / (w + 3))
            rect(cx - hw, cx + hw, top - dy, top - dy, far_c)
        cv.set(cx - w // 2, top, far_top)

    # ---- B: near ramparts
    # arcade: crenellated wall-walk carried on arches
    AX0, AX1, TOP = 96, 262, 112
    rect(AX0, AX1, TOP, H - 1, body)
    for x in range(AX0, AX1 + 1):              # merlons
        if (x - AX0) % 7 < 4:
            rect(x, x, TOP - 5, TOP - 1, body)
    rect(AX0 - 2, AX1 + 2, TOP + 1, TOP + 3, shade)   # string course
    rect(AX0 - 2, AX1 + 2, TOP + 1, TOP + 1, body)
    for i in range(6):
        cx = AX0 + 16 + i * 28
        # opening: straight jambs, round head
        for y in range(TOP + 10, H):
            for x in range(cx - 10, cx + 11):
                if y >= TOP + 21 or (x - cx) ** 2 + (y - (TOP + 21)) ** 2 <= 100:
                    cv.set(x, y, T)
        # voussoir ring
        for y in range(TOP + 7, TOP + 22):
            for x in range(cx - 13, cx + 14):
                d = math.hypot(x - cx, y - (TOP + 21))
                if 10 < d <= 12.6 and cv.get(x, y)[3]:
                    ang = math.degrees(math.atan2(TOP + 21 - y, x - cx))
                    cv.set(x, y, shade if int(ang) % 20 < 3 else body)
        # pier shading
        rect(cx + 11, cx + 12, TOP + 21, H - 1, shade)
    # broken end of the arcade (right): jagged collapse
    for x in range(AX1 - 24, AX1 + 6):
        cut = TOP - 6 + int((x - (AX1 - 24)) * 1.6 + h01(x, 0, 12) * 8)
        for y in range(TOP - 6, min(H, cut)):
            cv.set(x, y, T)
    # rubble heap at the break
    for x in range(AX1 - 20, AX1 + 22):
        top = 186 - int(14 * math.sin(math.pi * (x - (AX1 - 20)) / 42) + h01(x, 4, 13) * 4)
        rect(x, x, top, H - 1, body)

    def tower(cx, w, top, roof):
        x0, x1 = cx - w // 2, cx + w // 2
        rect(x0, x1, top, H - 1, body)
        rect(x1 - 2, x1, top, H - 1, shade)
        for y in range(top + 6, H, 7):                 # coursing
            for x in range(x0 + 1, x1 - 2):
                if (x * 3 + y) % 5 == 0:
                    cv.set(x, y, shade)
        if roof == "cone":
            h = int(w * 1.5)
            for dy in range(1, h):
                hw = (w / 2 + 3) * (1 - dy / h)
                rect(cx - hw, cx + hw, top - dy, top - dy, body)
                rect(cx + hw * 0.3, cx + hw, top - dy, top - dy, shade)
            rect(x0 - 3, x1 + 3, top, top + 1, shade)
        elif roof == "crenel":
            rect(x0 - 2, x1 + 2, top - 1, top + 2, body)
            for x in range(x0 - 2, x1 + 3):
                if (x - x0) % 4 < 2:
                    rect(x, x, top - 5, top - 2, body)
        elif roof == "broken":
            for x in range(x0, x1 + 1):
                rect(x, x, top - int(h01(x, 1, cx) * 12 + (x - x0) * 0.6), top, body)
        # windows (dark slits, one faintly lit)
        for k, wy in enumerate((top + 14, top + 34)):
            if wy < 170:
                rect(cx - 1, cx, wy, wy + 6, dark)
                cv.set(cx - 1, wy - 1, dark)
                if (cx + k) % 3 == 0:
                    rect(cx - 1, cx - 1, wy + 2, wy + 5, C("8a5a2c"))

    tower(44, 24, 66, "cone")
    tower(96, 14, 98, "crenel")
    tower(300, 20, 84, "broken")
    tower(474, 18, 92, "crenel")
    rect(474, 512 + 44, 150, H - 1, body)            # low wall wrapping around to x=44
    for x in range(474, 512 + 44):
        if (x % 7) < 4:
            rect(x, x, 145, 149, body)

    # the Pale Root invades: a great gold root arcs over the wall between the towers
    GR = ramp("2a2024", "3e3028", "56422e", "6e5634", "8a6e3e")
    seg = []
    for i in range(61):
        t = i / 60
        x = 320 + 150 * t
        y = 216 - 150 * math.sin(math.pi * t) ** 0.8 + 16 * t
        seg.append((x, y))
    for i, (x, y) in enumerate(seg):
        t = i / 60
        r = 7 - 3 * t + 1.5 * math.sin(t * 9)
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                d = math.hypot(xx - x, yy - y)
                if d <= r:
                    # lit from above-left; bark ridges along the root
                    nx, ny = (xx - x) / r, (yy - y) / r
                    v = 0.55 - 0.45 * ny - 0.2 * nx
                    if math.sin(ny * 5.5 + math.sin(i * 0.25) * 1.5) > 0.75:
                        v -= 0.25
                    cv.set(xx, yy, pick(GR, v, xx, yy))
    # side rootlets dangling from the arc
    rnd = random.Random(8)
    for i in range(6, 56, 7):
        x, y = seg[i]
        L = rnd.randint(10, 30)
        for k in range(L):
            cv.set(round(x + math.sin(k * 0.3 + i) * 2), round(y + 4 + k), GR[2] if k < L - 3 else GR[1])
    # hanging banners (tattered, dark crimson)
    BAN = [C("2a1016"), C("3a141c"), C("4e1c24")]
    for (bx, by, bl) in ((38, 96, 26), (292, 110, 20), (140, 124, 16), (468, 108, 22)):
        for y in range(by, by + bl):
            for x in range(bx, bx + 7):
                if y > by + bl - 5 and (x + y) % 3 == 0:
                    continue
                cv.set(x, y, BAN[1] if x < bx + 5 else BAN[0])
            cv.set(bx, y, BAN[2])
        rect(bx - 1, bx + 7, by - 1, by - 1, dark)
        for (x, y) in ((bx + 2, by + 6), (bx + 3, by + 5), (bx + 4, by + 6), (bx + 3, by + 7)):
            cv.set(x, y, C("6a4a2a"))      # faded gold sigil
    # ground rubble line
    for x in range(W):
        top = 198 + int(6 * (tn(x, 5, 16, 1, 9) - 0.5)) + int(3 * tn(x, 6, 4, 1, 10))
        rect(x, x, top, H - 1, shade)
    rim_pass()
    haze_toward(cv, 150, 222, R_FOG, 1.0)
    return cv.img


BUILDERS = {
    "ramparts": (build_ramparts_far, build_ramparts_mid),
}


# =========================================================================== CATACOMBS
K_CAVE = ramp("070507", "0b080b", "100c0f", "161114", "1d161a", "251c20", "2e2427", "382c2e")
K_TEAL = ramp("101a1a", "152322", "1b2d2b", "223835", "2b4541", "36554f", "46685f")
K_GOLD = ramp("2e1e16", "4a301c", "684622", "8a602c", "ac7e38", "cca04c", "e8c470")


def build_catacombs_far():
    cv = Canvas(W, H, wrap=True)
    # 1) cavern air: dark at the roof and floor, hazier (lighter) in the middle distance
    for y in range(H):
        for x in range(W):
            v = 0.12 + 0.42 * smooth(10, 120, y) - 0.34 * smooth(160, 216, y)
            v += 0.12 * (fbm(x, y, 128, 32, 300) - 0.5)
            cv.set(x, y, pick(K_CAVE, v, x, y))
    # 2) back wall of the ossuary: carved cliff with tiers of niches in irregular patches
    def back_top(x):
        return 44 + 22 * fbm(x, 0, 128, 1, 305) + 6 * tn(x, 0, 16, 1, 306)
    for x in range(W):
        top = back_top(x)
        for y in range(int(top), 176):
            v = 0.50 + 0.10 * (tn(x, y, 32, 16, 307) - 0.5) - 0.18 * smooth(140, 176, y)
            cv.set(x, y, pick(K_CAVE, v, x, y))
        cv.set(x, int(top), K_CAVE[6])
    for (px0, px1, py0, tiers) in ((10, 150, 70, 3), (190, 330, 64, 4), (370, 480, 78, 3)):
        for t in range(tiers):
            ty = py0 + t * 22
            nh, nw, pitch = 12, 6, 10
            for x in range(px0 - 2, px1 + 2):          # carved ledge
                cv.set(x, ty + nh + 1, K_CAVE[6])
                cv.set(x, ty + nh + 2, K_CAVE[2])
            for nx in range(px0 + (t % 2) * 5, px1 - nw, pitch):
                if h01(nx, t, 311) < 0.12:
                    continue                         # collapsed niche
                for y in range(ty, ty + nh):
                    for x in range(nx, nx + nw):
                        cxn = nx + (nw - 1) / 2
                        if y - ty < 3 and (x - cxn) ** 2 + (y - ty - 3) ** 2 > 9.5:
                            continue
                        cv.set(x, y, K_CAVE[1])
                if h01(nx, t, 310) < 0.55:           # skull in the niche
                    cv.set(nx + 2, ty + nh - 3, K_CAVE[6])
                    cv.set(nx + 3, ty + nh - 3, K_CAVE[7])
                    cv.set(nx + 2, ty + nh - 2, K_CAVE[4])
                    cv.set(nx + 3, ty + nh - 2, K_CAVE[5])
    # 3) teal candle-light pools on the back wall
    for (cx, cy) in ((64, 128), (262, 118), (420, 132)):
        for y in range(cy - 40, cy + 40):
            for x in range(cx - 60, cx + 60):
                d = math.hypot((x - cx) / 60, (y - cy) / 40)
                a = (1 - d) * 0.9
                if a > 0 and a > bt(x, y) * 0.9 + 0.1:
                    c = cv.get(x, y)
                    i = K_CAVE.index(c) if c in K_CAVE else 3
                    cv.set(x, y, K_TEAL[min(6, max(0, i - 2 + int(a * 3)))])
        for (dx, h) in ((-3, 4), (0, 6), (2, 3), (5, 5)):
            for k in range(h):
                cv.set(cx + dx, cy - k, K_CAVE[6])
            cv.set(cx + dx, cy - h, K_TEAL[6])
            cv.set(cx + dx, cy - h - 1, C("b8fff0"))
    # 4) nearer cave columns (darker silhouettes joining roof and floor)
    for (cx, w, pinch) in ((150, 18, 0.5), (352, 24, 0.35), (500, 14, 0.6)):
        for y in range(H):
            t = abs(y - 110) / 110
            hw = w / 2 * (pinch + (1 - pinch) * t ** 1.5) + 3 * (tn(cx, y, 4, 8, 320) - 0.5)
            for x in range(int(cx - hw), int(cx + hw) + 1):
                v = 0.22 + (0.12 if x < cx - hw + 2 else 0)
                cv.set(x, y, pick(K_CAVE, v - 0.1 * smooth(150, 216, y), x, y))
    # 5) golden roots pushing down through the roof, branching; hazed with depth
    rnd = random.Random(42)
    GR = [K_CAVE[3], K_GOLD[0], K_GOLD[1], K_GOLD[2], K_GOLD[3], K_GOLD[4]]
    for (rx, wd, lean) in ((96, 6.0, 0.25), (228, 7.5, -0.3), (300, 4.0, 0.2), (446, 6.5, -0.15)):
        segs = limb_tree(rnd, rx, -4, math.radians(-90 + lean * 30), 70, wd, 2, lean * 0.02, [],
                         spread=(0.25, 0.5), shrink=(0.5, 0.7), step=3.0, twig=True)
        # faint light shaft from the crack the root entered by
        for y in range(0, 150):
            for dx in range(-10, 11):
                x = rx + dx + y * 0.25
                a = smooth(10, 3, abs(dx)) * (1 - smooth(20, 150, y)) * 0.45
                c = cv.get(x, y)
                if a > bt(x, y) and c in K_CAVE:
                    cv.set(x, y, K_CAVE[min(7, K_CAVE.index(c) + 2)])
        pix = raster_segs(segs)
        for (x, y), (w, core) in pix.items():
            if y < 0:
                continue
            fade = smooth(40, 170, y)
            v = (0.8 if core else 0.5) - 0.55 * fade + (0.1 if w > 3 else 0)
            cv.set(x, y, pick(GR, v, x, y))
        for (x0, y0, x1, y1, w) in segs[::9]:      # glowing vein nodes
            if y0 < 110 and w > 2:
                cv.set(x0, y0, K_GOLD[5])
    # 6) roof: stalactite silhouette, nearest and darkest
    for x in range(W):
        top = 4 + 7 * fbm(x, 0, 32, 1, 320, octaves=2) + 22 * h01(x // 4, 0, 321) ** 8 * (1 - (x % 4) / 6)
        for y in range(0, int(top)):
            cv.set(x, y, K_CAVE[0])
        cv.set(x, int(top), K_CAVE[2])
    # 7) floor: distant bone-strewn ground, dark
    for x in range(W):
        top = 184 + 6 * fbm(x, 3, 64, 1, 330)
        for y in range(int(top), H):
            cv.set(x, y, pick(K_CAVE, 0.18 - 0.1 * smooth(top, H, y), x, y))
        if h01(x, 1, 331) < 0.15:
            cv.set(x, int(top), K_CAVE[5])
    # 8) motes
    rnd = random.Random(12)
    for _ in range(80):
        x, y = rnd.randrange(W), rnd.randrange(30, 180)
        cv.set(x, y, K_TEAL[5] if rnd.random() < 0.6 else K_GOLD[4])
    return cv.img


K_SIL = ramp("0a0708", "0f0b0c", "151011", "1b1516", "221a1b")
K_RIM = ramp("1e3230", "2a4541", "3a5c56")
K_FOG = {K_SIL[0]: K_SIL[1], K_SIL[1]: K_SIL[2], K_SIL[2]: K_SIL[3], K_SIL[3]: K_SIL[4],
         K_RIM[0]: K_SIL[3], K_RIM[1]: K_RIM[0], K_RIM[2]: K_RIM[1]}


def build_catacombs_mid():
    cv = Canvas(W, H, wrap=True)
    body, shade, dark = K_SIL[2], K_SIL[1], K_SIL[0]

    def rect(x0, x1, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                cv.set(x, y, c)

    # crypt arcade: thick round arches on squat piers
    def arch_bay(cx, span, spring, top):
        """Wall band between `top` and the ground with a round-headed opening."""
        r = span / 2
        for y in range(top, H):
            for x in range(int(cx - r - 9), int(cx + r + 10)):
                inside = abs(x - cx) <= r and (y >= spring or (x - cx) ** 2 + (y - spring) ** 2 <= r * r)
                if not inside:
                    cv.set(x, y, body)
        # voussoirs ring
        for y in range(top, spring + 1):
            for x in range(int(cx - r - 4), int(cx + r + 5)):
                d = math.hypot(x - cx, y - spring)
                if r < d <= r + 4:
                    a = math.degrees(math.atan2(spring - y, x - cx))
                    cv.set(x, y, shade if int(a) % 18 < 3 or d > r + 3 else K_SIL[3])

    for (cx, span, spring, top) in ((60, 44, 118, 84), (164, 38, 128, 98), (268, 48, 112, 76),
                                    (372, 40, 124, 92), (466, 36, 130, 102)):
        arch_bay(cx, span, spring, top)
    # skull stacks in the piers (ossuary walls): rows of little skulls
    for (x0, x1, y0, y1) in ((88, 140, 150, 190), (292, 344, 146, 190)):
        for y in range(y0, y1, 5):
            for x in range(x0 + (y // 5) % 2 * 2, x1, 4):
                if cv.get(x, y) == body:
                    cv.set(x, y, K_SIL[4])
                    cv.set(x + 1, y, K_SIL[4])
                    cv.set(x, y + 1, dark)
                    cv.set(x + 1, y + 1, K_SIL[3])
    # broken tops of the wall
    for x in range(W):
        for y in range(60, 110):
            c = cv.get(x, y)
            if c[3] and not cv.get(x, y - 1)[3]:
                for k in range(int(h01(x // 2, 5, 400) ** 3 * 5)):
                    cv.set(x, y - k - 1, body)
                break
    # sarcophagi / coffins leaning in the arches
    for (sx, sy) in ((52, 176), (262, 172), (378, 180)):
        for y in range(sy, 200):
            for x in range(sx, sx + 14):
                if (y - sy) < 3 and (x - sx < 2 or x - sx > 11):
                    continue
                cv.set(x, y, K_SIL[3] if y == sy or x == sx else body)
        rect(sx + 5, sx + 8, sy + 5, sy + 6, shade)
        rect(sx + 6, sx + 7, sy + 3, sy + 12, shade)
    # candles on the ledges (teal)
    for (x, y) in ((24, 166), (30, 164), (216, 176), (330, 160), (420, 170), (425, 172)):
        rect(x, x, y, y + 4, K_SIL[4])
        cv.set(x, y - 1, K_RIM[2])
        cv.set(x, y - 2, C("9af0dc"))
    # gold roots strangling the arches
    GR = [K_SIL[3], K_GOLD[0], K_GOLD[1], K_GOLD[2]]
    for (x0, y0, x1, y1, amp, w) in ((0, 96, 130, 150, 14, 3.5), (230, 70, 360, 170, -18, 4.0),
                                     (400, 110, 512, 90, 10, 3.0)):
        for i in range(160):
            t = i / 159
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t - amp * math.sin(math.pi * t)
            r = w * (1 - 0.4 * t)
            for dy in range(-int(r) - 1, int(r) + 2):
                d = dy / r
                if abs(d) <= 1:
                    v = 0.6 - 0.5 * d - (0.25 if math.sin(d * 4 + x * 0.1) > 0.75 else 0)
                    cv.set(x, y + dy, pick(GR, v, x, y + dy))
        # dangling rootlets
        for k in range(6):
            t = (k + 0.5) / 6
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t - amp * math.sin(math.pi * t)
            for j in range(int(8 + 14 * h01(k, x0, 401))):
                cv.set(x + math.sin(j * 0.5 + k) * 1.2, y + w + j, GR[1])
    # ground: bone rubble
    for x in range(W):
        top = 196 + int(5 * (tn(x, 5, 16, 1, 402) - 0.5)) + int(3 * tn(x, 6, 4, 1, 403))
        rect(x, x, top, H - 1, shade)
        if h01(x, 7, 404) < 0.12:
            cv.set(x, top - 1, K_SIL[4])
    # teal rim-light on edges facing the candle-lit haze (top + left)
    px = cv.img.load()
    rim = []
    for y in range(1, H):
        for x in range(W):
            c = px[x, y]
            if c in (body, shade, K_SIL[3]):
                if px[x, y - 1][3] == 0:
                    rim.append((x, y, K_RIM[1]))
                elif px[(x - 1) % W, y][3] == 0:
                    rim.append((x, y, K_RIM[0]))
                elif px[(x + 1) % W, y][3] == 0 and h01(x, y, 5) < 0.5:
                    rim.append((x, y, K_RIM[0]))
    for (x, y, c) in rim:
        px[x, y] = c
    haze_toward(cv, 160, 226, K_FOG, 1.0)
    return cv.img


BUILDERS["catacombs"] = (build_catacombs_far, build_catacombs_mid)


# =========================================================================== CATHEDRAL
N_AIR = ramp("0a0b14", "0e1019", "12151f", "171b27", "1d222f", "232937", "2a3140", "32394a", "3b4356")
N_LIGHT = ramp("3b4356", "4c5670", "62708c", "7e8eaa", "a0b0c8", "c6d2e2", "e6eef6")
N_GOLD = ramp("3a2e1c", "5a4626", "7e6230", "a8843e", "d0aa56")
WIN_X = [48, 176, 304, 432]           # lancet windows, period 128 -> tileable


def build_cathedral_far():
    cv = Canvas(W, H, wrap=True)
    # 1) nave air: darker toward the vault, faint haze band where the light falls
    for y in range(H):
        for x in range(W):
            v = 0.15 + 0.45 * smooth(0, 150, y) - 0.2 * smooth(170, 216, y)
            v += 0.08 * (fbm(x, y, 128, 32, 500) - 0.5)
            cv.set(x, y, pick(N_AIR, v, x, y))
    # 2) far wall: clustered piers between windows, pointed vault ribs above
    for (i, wx) in enumerate(WIN_X):
        px0 = wx + 64 - 7                      # pier between windows
        for y in range(18, 176):
            for x in range(px0, px0 + 14):
                c = N_AIR[4] if (x - px0) % 5 else N_AIR[2]
                if x == px0:
                    c = N_AIR[6]
                cv.set(x, y, c)
        for x in range(px0 - 3, px0 + 17):     # capital with gold filigree
            cv.set(x, 58, N_AIR[6])
            cv.set(x, 59, N_GOLD[2] if x % 2 else N_GOLD[1])
            cv.set(x, 60, N_AIR[3])
        # pointed vault ribs springing from the capitals
        for s in (-1, 1):
            for t in range(0, 64):
                x = px0 + 7 + s * t
                y = 58 - 52 * math.sin(math.acos(1 - t / 64)) * 0.95
                for k in range(2):
                    cv.set(x, int(y) + k, N_AIR[5] if k == 0 else N_AIR[1])
    # 3) tall lancet windows with tracery, pale cold light
    for wx in WIN_X:
        x0, x1, ytop, ybot = wx - 13, wx + 13, 22, 150
        for y in range(ytop, ybot):
            for x in range(x0, x1 + 1):
                dx = abs(x - wx)
                # pointed head: two arcs
                if y < ytop + 26:
                    r = 40
                    cx = wx - 27 if x >= wx else wx + 27
                    if (x - cx) ** 2 + (y - (ytop + 26)) ** 2 > r * r:
                        continue
                v = 0.42 + 0.30 * (1 - smooth(ytop, ybot, y)) - 0.22 * (dx / 13) ** 2 + 0.1 * (tn(x, y, 4, 8, 505) - 0.5)
                c = pick(N_LIGHT[:6], v, x, y)
                if dx in (12, 13) or x == wx or (dx == 6 and y > ytop + 30) or (y - ytop) % 24 == 0:
                    c = N_AIR[3]                            # mullions + transoms
                cv.set(x, y, c)
        # rose-ish oculus in the head
        for y in range(ytop + 6, ytop + 20):
            for x in range(wx - 7, wx + 8):
                d = math.hypot(x - wx, y - (ytop + 13))
                if 5 < d < 6.5 or (d < 5 and (abs(x - wx) == 0 or y == ytop + 13)):
                    cv.set(x, y, N_AIR[3])
        # sill
        for x in range(x0 - 2, x1 + 3):
            cv.set(x, ybot, N_GOLD[1])
            cv.set(x, ybot + 1, N_AIR[2])
    # 4) light shafts falling from each window down-right onto the floor
    for wx in WIN_X:
        for y in range(40, 210):
            spread = 10 + (y - 40) * 0.12
            cx = wx + (y - 40) * 0.55
            for dx in range(-int(spread) - 2, int(spread) + 3):
                x = cx + dx
                a = smooth(spread + 2, spread - 4, abs(dx)) * 0.45 * (1 - smooth(120, 210, y)) \
                    * (0.7 + 0.3 * math.sin(dx * 0.7 + y * 0.02))
                c = cv.get(x, y)
                if a > bt(x, y) and c in N_AIR:
                    cv.set(x, y, N_AIR[min(8, N_AIR.index(c) + 3)] if a > 0.3 else N_AIR[min(8, N_AIR.index(c) + 2)])
    # 5) floor line + still water with window reflections
    WL = 176
    for x in range(W):
        cv.set(x, WL - 1, N_AIR[6])
        cv.set(x, WL - 2, N_AIR[3])
    for y in range(WL, H):
        for x in range(W):
            my = 2 * WL - y - 1                 # mirrored source row
            ripple = int(2 * math.sin(y * 0.9 + x * 0.05))
            src = cv.get(x + ripple, my) if my >= 0 else N_AIR[0]
            if src in N_LIGHT:
                i = N_LIGHT.index(src)
                c = N_LIGHT[max(0, i - 2)] if (y + x // 3) % 3 else N_AIR[4]
            elif src in N_AIR:
                c = N_AIR[max(0, N_AIR.index(src) - 2)]
            else:
                c = N_AIR[2]
            if (y - WL) % 5 == 0 and h01(x // 6, y, 510) < 0.5:
                c = N_AIR[5]                   # glints on the ripples
            cv.set(x, y, c)
    # 6) motes of pale light drifting in the shafts
    rnd = random.Random(21)
    for _ in range(60):
        x, y = rnd.randrange(W), rnd.randrange(50, 170)
        cv.set(x, y, N_LIGHT[5] if rnd.random() < 0.7 else N_GOLD[4])
    return cv.img


N_SIL = ramp("0b0c14", "10121c", "151824", "1b1f2d", "222737")
N_RIM = ramp("2e3850", "44527a", "5e6e96")
N_FOG = {N_SIL[0]: N_SIL[1], N_SIL[1]: N_SIL[2], N_SIL[2]: N_SIL[3], N_SIL[3]: N_SIL[4],
         N_RIM[0]: N_SIL[3], N_RIM[1]: N_RIM[0], N_RIM[2]: N_RIM[1]}


def build_cathedral_mid():
    cv = Canvas(W, H, wrap=True)
    body, shade, dark = N_SIL[2], N_SIL[1], N_SIL[0]
    WL = 198

    def rect(x0, x1, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                cv.set(x, y, c)

    PIERS = [(20, 22), (148, 18), (276, 22), (404, 18)]
    for (cx, w) in PIERS:
        x0, x1 = cx - w // 2, cx + w // 2
        rect(x0, x1, 52, WL, body)
        for x in range(x0, x1 + 1):              # clustered shafts
            if (x - x0) % 5 == 4:
                rect(x, x, 58, WL, shade)
        rect(x1 - 1, x1, 52, WL, shade)
        # capital: gold filigree band
        rect(x0 - 4, x1 + 4, 106, 110, N_SIL[3])
        for x in range(x0 - 4, x1 + 5):
            cv.set(x, 107, N_GOLD[2] if x % 3 else N_GOLD[3])
            cv.set(x, 109, N_GOLD[1] if x % 2 else N_SIL[3])
        rect(x0 - 3, x1 + 3, 111, 112, dark)
        # base
        rect(x0 - 3, x1 + 3, WL - 8, WL, N_SIL[3])
        for x in range(x0 - 3, x1 + 4):
            cv.set(x, WL - 8, N_GOLD[1] if x % 4 == 0 else N_SIL[4])
    # pointed arches spanning pier to pier, with a triforium band above
    SPRING = 110
    for i, (cx, w) in enumerate(PIERS):
        ncx, nw = PIERS[(i + 1) % len(PIERS)]
        if i == len(PIERS) - 1:
            ncx += W
        a0, a1 = cx + w // 2 + 4, ncx - nw // 2 - 4
        span = a1 - a0
        R = 0.56 * span
        cL, cR = a1 - R, a0 + R          # left flank arc centred right of middle, and vice versa
        apex = SPRING - math.sqrt(R * R - (span / 2 - (span - R)) ** 2)
        for x in range(a0 - 6, a1 + 7):
            for y in range(52, SPRING + 1):
                dL, dR = math.hypot(x - cL, y - SPRING), math.hypot(x - cR, y - SPRING)
                inside = dL <= R and dR <= R and a0 <= x <= a1
                ring = dL <= R + 5 and dR <= R + 5 and a0 - 5 <= x <= a1 + 5
                if inside:
                    if (abs(dL - R) < 0.9 or abs(dR - R) < 0.9) and (x + y) % 3:
                        cv.set(x, y, N_GOLD[1])      # gilded intrados
                    continue
                if ring:
                    ang = math.atan2(SPRING - y, x - (a0 + a1) / 2)
                    cv.set(x, y, shade if int(math.degrees(ang)) % 14 < 2 else N_SIL[3])
                elif y >= 58:
                    cv.set(x, y, body)
        rect(a0 - 6, a1 + 6, 52, 57, body)          # triforium band
        for x in range(a0 - 6, a1 + 7):
            if (x - a0) % 10 < 4:
                rect(x, x, 53, 56, dark)
                cv.set(x, 53, N_SIL[3])
            cv.set(x, 57, N_GOLD[1] if x % 3 == 0 else shade)
    # hanging censers on chains from the arches
    for (hx, L) in ((84, 40), (212, 28), (340, 46), (468, 34)):
        for y in range(60, 60 + L):
            cv.set(hx, y, N_SIL[3] if y % 3 else dark)
        by = 60 + L
        for (dx, dy) in ((-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-3, 1), (3, 1), (-3, 2), (-2, 2), (-1, 2),
                         (0, 2), (1, 2), (2, 2), (3, 2), (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (0, 4)):
            cv.set(hx + dx, by + dy, body)
        cv.set(hx, by + 1, N_GOLD[4])
        cv.set(hx - 1, by + 1, N_GOLD[3])
        cv.set(hx + 1, by + 1, N_GOLD[2])
    # broken rubble + fallen statue head in the water
    for x in range(W):
        top = WL - 3 + int(4 * (tn(x, 5, 16, 1, 520) - 0.5))
        rect(x, x, top, WL, shade)
    for y in range(WL - 14, WL):
        for x in range(330, 352):
            if math.hypot((x - 341) / 11, (y - WL) / 14) < 1:
                cv.set(x, y, body if x > 336 else N_SIL[3])
    # rim light (cool, from the windows) on top + left edges
    px = cv.img.load()
    rim = []
    for y in range(1, H):
        for x in range(W):
            c = px[x, y]
            if c in (body, shade, N_SIL[3]):
                if px[x, y - 1][3] == 0:
                    rim.append((x, y, N_RIM[1]))
                elif px[(x - 1) % W, y][3] == 0:
                    rim.append((x, y, N_RIM[2] if y < 120 else N_RIM[1]))
    for (x, y, c) in rim:
        px[x, y] = c
    # still-water reflection of the mid layer (darkened, rippled)
    for y in range(WL + 1, H):
        for x in range(W):
            my = 2 * WL - y
            src = px[(x + int(1.5 * math.sin(y * 1.1))) % W, my]
            if src[3] and (y + x) % 2 == 0 or (src[3] and y < WL + 6):
                px[x, y] = N_SIL[1] if src in N_SIL else N_SIL[2]
            elif not src[3]:
                px[x, y] = T
        if (y - WL) % 4 == 1:
            for x in range(W):
                if px[x, y][3] and h01(x // 5, y, 530) < 0.4:
                    px[x, y] = N_RIM[0]
    haze_toward(cv, 150, 230, N_FOG, 0.8)
    return cv.img


BUILDERS["cathedral"] = (build_cathedral_far, build_cathedral_mid)
