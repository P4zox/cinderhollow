"""Thornveil Wood tileset (48 x 16x16, standard index layout -- see docs/ART_SPEC.md section 6).

Terrain: near-black forest loam threaded with roots, capped by a thick blue-green moss carpet; bark rims on the
walls, root tendrils under overhangs. Variants add embedded stones, root knots and glowing spirit-fungus.
"""
import math
from thornveil_kit import (SOIL, BARK, MOSS, STONE, SPIRIT, RIBBON, BONE, THORN, DEEP, K, Pix, ramp_pick, pnoise,
                           h01, blank, curve_pts, C)

N_, E_, S_, W_ = 1, 2, 4, 8
T0 = (0, 0, 0, 0)


def _soil_level(x, y, seed):
    v = 0.26 + 0.38 * pnoise(x, y, 8, seed) + 0.12 * pnoise(x, y, 4, seed + 3)
    return v


def solid(mask, variant=0):
    P = Pix(16, 16)
    seed = 11 + variant * 7
    dN = lambda y: y if mask & N_ else 99
    dE = lambda x: 15 - x if mask & E_ else 99
    dS = lambda y: 15 - y if mask & S_ else 99
    dW = lambda x: x if mask & W_ else 99
    # ---- loam body with depth shading (darker away from exposed faces; light from the upper-left)
    for y in range(16):
        for x in range(16):
            v = _soil_level(x, y, seed)
            d = min(dN(y), dE(x), dS(y), dW(x))
            if mask == 0:
                v *= 0.72
            else:
                v *= 0.78 + 0.22 * max(0, 1 - d / 6)
            if mask & W_ and x <= 2:
                v += 0.12 * (3 - x) / 3
            if mask & E_ and x >= 13:
                v -= 0.10 * (x - 12) / 3
            if mask & S_ and y >= 13:
                v -= 0.12 * (y - 12) / 3
            P.set(x, y, ramp_pick(SOIL, v, x, y))
    # ---- one faint periodic root threaded through the loam (enters/exits each edge at the same height)
    if variant in (0, 3):
        a = 5 + int(h01(variant, mask, 5) * 7)
        ph = h01(variant, 1, 8) * 6.28
        for x in range(16):
            y = int(round(a + 1.4 * math.sin(x / 16 * 6.283 + ph))) % 16
            P.set(x, y, BARK[1])
            if h01(x, variant, 3) < 0.45:
                P.set(x, (y - 1) % 16, BARK[2])
    if variant == 3:     # a knotted root boss
        cx, cy = 8, 9
        for y in range(16):
            for x in range(16):
                dx, dy = (x + .5 - cx) / 3.0, (y + .5 - cy) / 2.4
                q = dx * dx + dy * dy
                if q <= 1:
                    P.set(x, y, ramp_pick(BARK[1:5], 0.6 - 0.4 * dx - 0.4 * dy, x, y))
                elif q <= 1.4:
                    P.set(x, y, SOIL[0])
        P.set(8, 9, BARK[1]); P.set(7, 9, BARK[1])
    if variant == 1:     # an embedded stone
        cx, cy = 5 + h01(1, 2, 3) * 6, 6 + h01(2, 3, 4) * 5
        for y in range(16):
            for x in range(16):
                dx, dy = (x + .5 - cx) / 2.9, (y + .5 - cy) / 2.2
                q = dx * dx + dy * dy
                if q <= 1:
                    lv = 0.5 - 0.35 * dx - 0.35 * dy
                    P.set(x, y, ramp_pick(STONE[:4], lv, x, y))
                elif q <= 1.35:
                    P.set(x, y, K)
    if variant == 2:     # spirit fungus: a few glowing beads in the loam
        for (x, y) in ((4, 11), (10, 7), (12, 12)):
            P.set(x, y, SPIRIT[4]); P.set(x + 1, y, SPIRIT[2]); P.set(x, y + 1, SPIRIT[1]); P.set(x - 1, y, SPIRIT[1])
    # ---- faces
    if mask & W_:
        for y in range(16):
            P.set(0, y, BARK[3] if h01(0, y, 2) < 0.6 else BARK[4]); P.set(1, y, BARK[2])
    if mask & E_:
        for y in range(16):
            P.set(15, y, BARK[1]); P.set(14, y, BARK[2] if h01(15, y, 2) < 0.5 else SOIL[2])
    if mask & S_:
        for x in range(16):
            P.set(x, 15, SOIL[0]); P.set(x, 14, SOIL[1] if P.get(x, 14) != BARK[2] else BARK[1])
        # root tendrils hanging from the underside
        for k in range(2):
            x = int(2 + h01(k, variant, 13) * 12)
            L = 3 + int(h01(k, variant, 14) * 3)
            for i in range(L):
                P.set(x + (1 if i > L // 2 and k else 0), 15 - L + 1 + i, BARK[2] if i < L - 1 else BARK[1])
    # ---- moss carpet on top
    if mask & N_:
        for x in range(16):
            th = 3 + int(pnoise(x, 0, 4, 21 + variant) * 3)
            for y in range(th):
                v = 1 - y / th
                c = MOSS[5] if y == 0 else MOSS[4] if y == 1 else MOSS[3] if y < th - 1 else MOSS[2]
                if y == 0 and h01(x, variant, 31) < 0.35:
                    c = MOSS[6]
                if y == 0 and h01(x, variant, 37) < 0.08:
                    c = MOSS[7]
                P.set(x, y, c)
            P.set(x, th, SOIL[1])
            # moss drips down the loam
            if h01(x, variant, 41) < 0.22:
                dl = 1 + int(h01(x, variant, 42) * 3)
                for i in range(dl):
                    P.set(x, th + i, MOSS[2] if i < dl - 1 else MOSS[1])
                P.set(x, th + dl, SOIL[1])
        # moss curls over exposed side faces
        if mask & W_:
            for y in range(6):
                P.set(0, y, MOSS[4] if y < 3 else MOSS[3]); P.set(1, y, MOSS[3] if y < 4 else P.get(1, y))
        if mask & E_:
            for y in range(5):
                P.set(15, y, MOSS[3] if y < 3 else MOSS[2])
    elif mask & W_ and h01(variant, 3, 5) < 0.6:   # moss patch on a bare wall
        y0 = 3 + int(h01(variant, 4, 6) * 8)
        for y in range(y0, y0 + 4):
            P.set(0, y, MOSS[4]); P.set(1, y, MOSS[3] if y < y0 + 3 else MOSS[2])
    # ---- rounded outer corners
    for (a, b, cx, cy) in ((N_, W_, 0, 0), (N_, E_, 15, 0), (S_, W_, 0, 15), (S_, E_, 15, 15)):
        if mask & a and mask & b:
            P.set(cx, cy, T0)
            if a == N_:
                P.set(cx + (1 if cx == 0 else -1), cy, MOSS[4])
    return P.img


def platform(kind):
    """Mossy branch: 32 left end / 33 middle / 34 right end / 35 single."""
    P = Pix(16, 16)
    left = kind in (32, 35)
    right = kind in (34, 35)
    for x in range(16):
        top = 1
        bot = 6
        if left and x < 3:
            top, bot = 1 + (3 - x) // 2 + (1 if x == 0 else 0), 6 - (3 - x) // 2
        if right and x > 12:
            top, bot = 1 + (x - 12) // 2 + (1 if x == 15 else 0), 6 - (x - 12) // 2
        for y in range(top, bot + 1):
            t = (y - top) / max(1, bot - top)
            v = 0.75 - 0.6 * t + 0.1 * math.sin(x * 1.3 + y)
            c = ramp_pick(BARK[1:6], v, x, y)
            if y == bot:
                c = BARK[1]
            P.set(x, y, c)
        # bark grain
        if h01(x, kind, 3) < 0.25:
            P.set(x, (top + bot) // 2 + 1, BARK[1])
        # moss on top
        P.set(x, top - 1 if top > 0 else top, MOSS[5] if h01(x, kind, 7) < 0.6 else MOSS[6])
        P.set(x, top, MOSS[4] if h01(x, kind, 8) < 0.7 else MOSS[3])
        P.set(x, top - 2 if top > 1 else top, None)
        # outline
        P.set(x, bot + 1, K)
        if top - 2 >= 0:
            P.set(x, top - 2, K)
    if left:
        for y in range(1, 7):
            if P.on(0, y) is False and P.on(1, y):
                P.set(0, y, K)
    # hanging moss strands under the branch
    for k in range(2 if kind == 33 else 1):
        x = int(3 + h01(k, kind, 21) * 10)
        L = 3 + int(h01(k, kind, 22) * 4)
        for i in range(L):
            P.set(x, 8 + i, MOSS[3] if i < L - 2 else MOSS[2])
        P.set(x + 1, 8, MOSS[2])
    return P.img


def thorns(down=False):
    """36: bramble thorns rising from the tile bottom; 37: thorny vines hanging from the top."""
    P = Pix(16, 16)
    stems = [(2.5, 10, 0.18), (7.5, 13, -0.08), (12.5, 9, -0.2)]
    for i, (x0, hgt, lean) in enumerate(stems):
        pts = [(x0, 15), (x0 + lean * hgt * 0.5 + (1 if i == 1 else -0.5), 15 - hgt * 0.55), (x0 + lean * hgt, 15 - hgt)]
        cp = curve_pts(pts, 8)
        for k, (x, y) in enumerate(cp):
            t = k / max(1, len(cp) - 1)
            xi, yi = math.floor(x), math.floor(y)
            P.set(xi, yi, THORN[3] if t < 0.8 else THORN[4])
            if t < 0.55:
                P.set(xi + 1, yi, THORN[2])
        tx, ty = cp[-1]
        P.set(math.floor(tx), math.floor(ty) - 1, THORN[5])
        # side thorns: short hooked spurs with pale tips
        for j, t in enumerate((0.35, 0.62)):
            x, y = cp[int(t * (len(cp) - 1))]
            s_ = -1 if (i + j) % 2 else 1
            P.set(math.floor(x) + s_ * (2 if s_ > 0 else 1), math.floor(y) - 1, THORN[4])
            P.set(math.floor(x) + s_ * (3 if s_ > 0 else 2), math.floor(y) - 2, THORN[5])
    for x in range(16):
        P.set(x, 15, THORN[1] if h01(x, 1, 2) < 0.6 else THORN[2])
        if h01(x, 2, 2) < 0.4:
            P.set(x, 14, THORN[1])
    img = outline_img(P.img)
    if down:
        img = img.transpose(1)
    return img


def outline_img(img):
    from envlib import outline
    return outline(img, K)


def bg_wall(k):
    """38..41: the forest depth behind the play space (trunks, hanging moss, dark foliage); low contrast."""
    P = Pix(16, 16)
    seed = 50 + k * 13
    for y in range(16):
        for x in range(16):
            v = 0.25 + 0.35 * pnoise(x, y, 8, seed) + 0.2 * pnoise(x, y, 4, seed + 1)
            # vertical bark grain (trunks behind)
            g = 0.5 + 0.5 * math.sin((x + 3 * pnoise(x, y, 8, seed + 4)) / 16 * 6.283 * 2)
            v = v * 0.7 + g * 0.22
            P.set(x, y, ramp_pick(DEEP, v, x, y))
    # a faint mossy strand or leaf cluster
    if k in (1, 3):
        x = 4 + k * 2
        for y in range(16):
            P.set((x + (y // 5)) % 16, y, DEEP[4] if y % 4 else DEEP[5])
    if k == 2:
        for i in range(5):
            x, y = int(h01(i, k, 1) * 16), int(h01(i, k, 2) * 16)
            P.set(x, y, C("#1f3a2c")); P.set((x + 1) % 16, y, C("#183024"))
    return P.img


def deco_moss():
    P = Pix(16, 16)
    for k, (x0, L) in enumerate(((3, 13), (8, 9), (12, 15))):
        for y in range(L):
            x = x0 + int(round(0.8 * math.sin(y * 0.45 + k)))
            w = 2 if y < L * 0.55 else 1
            c = MOSS[4] if y < 2 else MOSS[3] if y < L * 0.6 else MOSS[2]
            for i in range(w):
                P.set(x + i, y, c)
            if y % 3 == 2:
                P.set(x - 1, y, MOSS[2])
    return outline_img(P.img)


def deco_roots():
    P = Pix(16, 16)
    for k, (x0, L, bend) in enumerate(((2, 12, 1), (7, 15, -1), (12, 10, 1))):
        pts = [(x0, 0), (x0 + bend, L * 0.5), (x0 + bend * 0.2, L)]
        for i, (x, y) in enumerate(curve_pts(pts, 6)):
            P.set(math.floor(x), math.floor(y), BARK[2] if y < L * 0.7 else BARK[1])
            if y < L * 0.4:
                P.set(math.floor(x) + 1, math.floor(y), BARK[3])
    return outline_img(P.img)


def deco_shrooms():
    P = Pix(16, 16)
    for (x, h, r) in ((4, 5, 2), (9, 7, 3), (12, 4, 1.6)):
        for y in range(15 - h, 16):
            P.set(x, y, BONE[4]); P.set(x + 1, y, BONE[3])
        cy = 15 - h
        for yy in range(-2, 1):
            for xx in range(-int(r) - 1, int(r) + 2):
                if (xx / (r + 0.5)) ** 2 + (yy / 2.2) ** 2 <= 1:
                    c = SPIRIT[4] if yy == -2 or (yy == -1 and xx < 0) else SPIRIT[3] if yy == -1 else SPIRIT[2]
                    P.set(x + xx, cy + yy, c)
    return outline_img(P.img)


def deco_skulls():
    P = Pix(16, 16)
    # a small deer skull lying on its side + a shed antler
    for y in range(11, 16):
        for x in range(2, 9):
            dx, dy = (x + .5 - 5.5) / 3.6, (y + .5 - 13.2) / 2.4
            if dx * dx + dy * dy <= 1:
                P.set(x, y, BONE[4] if dy < 0 else BONE[3])
    for x in range(8, 12):
        P.set(x, 14, BONE[3]); P.set(x, 15, BONE[2])
    P.set(4, 13, K); P.set(5, 13, BONE[1])
    for (a, b) in (((10, 15), (14, 12)), ((14, 12), (14, 8)), ((12, 13), (11, 10)), ((14, 10), (15, 9))):
        n = 6
        for i in range(n + 1):
            P.set(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n), BONE[4] if i < n else BONE[5])
    return outline_img(P.img)


def breakable():
    img = solid(0, 0).copy()
    P = Pix(16, 16, img)
    for (a, b) in (((3, 2), (7, 7)), ((7, 7), (6, 12)), ((7, 7), (12, 9)), ((12, 9), (14, 14))):
        n = 8
        for i in range(n + 1):
            P.set(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n), K)
    P.set(8, 7, BARK[3]); P.set(11, 9, BARK[3])
    return img


def tuft():
    P = Pix(16, 16)
    for k in range(9):
        x = int(1 + h01(k, 3, 1) * 14)
        L = 2 + int(h01(k, 3, 2) * 5)
        lean = 1 if h01(k, 3, 3) < 0.5 else -1
        for i in range(L):
            P.set(x + (lean if i > L // 2 else 0), 15 - i, MOSS[5] if i < L - 1 else MOSS[6])
    # a fern frond
    for i in range(6):
        P.set(6 + i, 15 - i // 2, MOSS[5]); P.set(6 + i, 14 - i // 2, MOSS[4] if i % 2 else None)
    # two tiny pale flowers
    P.set(3, 12, RIBBON[4]); P.set(12, 11, RIBBON[3])
    return P.img


def build():
    tiles = []
    for m in range(16):
        tiles.append(solid(m, 0))
    for m in range(16):
        tiles.append(solid(m, {0: 4, 1: 4, 2: 2, 8: 2, 3: 1, 9: 1, 4: 3, 5: 3}.get(m, 1 if m % 2 else 3)))
    for k in (32, 33, 34, 35):
        tiles.append(platform(k))
    tiles.append(thorns(False))
    tiles.append(thorns(True))
    for k in range(4):
        tiles.append(bg_wall(k))
    tiles += [deco_moss(), deco_roots(), deco_shrooms(), deco_skulls(), breakable(), tuft()]
    assert len(tiles) == 48
    return tiles
