"""Parallax for the `spire` biome — THE TEMPEST SPIRE.

bg_spire_far : 512x216 opaque, horizontally tileable, 10 frames.
               Night storm over a black sea: strata of heavy bruised storm cloud with sagging, faintly lit
               undersides, slanted rain, a low glow band on the horizon, the sea in the lower third with
               perspective swell lines and whitecaps, and far out ONE silhouette: the Stormspire, a broken
               gothic spire on a sea stack with a lightning rod at its tip, faintly rim-lit.
               loop   0-3  calm: only the rain, whitecaps and the rod's spark move
               flash  4-6  a forked bolt strikes the sea right of the spire (4 blinding, 5 afterglow, 6 ~normal)
               flash2 7-9  sheet lightning inside the clouds over the left + a thin far bolt
bg_spire_mid : 512x216 transparent, tileable, 4 frames `loop`. Silhouettes: sea cliff with a windmill hamlet,
               a broken arched causeway marching over the sea, jagged sea stacks; waves bursting on the
               bases, windmill sails turning; faint cold rim light from above.

Built like the other *_bg modules: wrapping Canvas, tileable value noise, ordered dithering onto one ramp,
1px rim light on silhouettes. Every loop frame shares the exact same composition.
"""
import math, random
from envlib import C, ramp, T, K, bt, pick_i, h01, smooth, clamp, Canvas
from env_bg import tn, wrapdx
from spire_tiles import AMBER, BOLT, SEA

W, H = 512, 216
HZ = 140                       # sea horizon

# one long ramp: blue-black -> bruised violet-grey -> cold storm blue -> white (flash only uses the top)
FAR = ramp("04050a", "07080f", "0a0c14", "0e0f1a", "121320", "161726", "1b1b2d", "212035", "28263d", "2f2c46",
           "38344f", "423c59", "4d4663", "5a526f", "68627e", "7a7890", "8e92a8", "a6b0c6", "c2d0e2", "dce8f4",
           "f0f8ff")
NF = len(FAR)
FOAM = [C("4e6680"), C("7a94ae"), C("a8c0d4"), C("d6e6f0")]

# cloud strata, back (low, lighter) to front (high, darker): base y of the underside, lobe period, depth, tone
BANKS = [
    dict(base=120, per=32, lobe=5, amp=5, tilt=6, tone=0.30, seed=1),
    dict(base=106, per=64, lobe=9, amp=7, tilt=10, tone=0.27, seed=2),
    dict(base=88, per=64, lobe=12, amp=9, tilt=14, tone=0.24, seed=3),
    dict(base=66, per=128, lobe=16, amp=10, tilt=16, tone=0.21, seed=4),
    dict(base=40, per=128, lobe=16, amp=10, tilt=12, tone=0.18, seed=5),
]

SPX = 346                      # the Stormspire's axis
BOLT_TOP, BOLT_BOT = (388, 44), (404, HZ + 1)
SHEET = (118, 56)
THIN_TOP, THIN_BOT = (156, 102), (146, HZ)


def bank_bottom(b, x):
    """Underside of a cloud bank: domain-warped rounded lobes of varying width sagging from a tilted base."""
    per = b["per"]
    sd = b["seed"]
    warp = 0.55 * per * (tn(x, 0, 64, 1, sd * 7) - 0.5) * 2 + 0.3 * per * (tn(x, 0, 32, 1, sd * 7 + 1) - 0.5)
    u = (x + warp) / per
    lob = math.sqrt(max(0.0, math.sin(math.pi * u)))
    size = 0.35 + 0.65 * tn(x, 0, 128, 1, sd + 30)
    return (b["base"] + b["tilt"] * (tn(x, 0, 256, 1, sd + 60) - 0.5) * 2
            + b["amp"] * (tn(x, 0, 16, 1, sd) - 0.5) + b["lobe"] * lob * size)


# ---------------------------------------------------------------------------- the Stormspire silhouette
def spire_mask():
    """-> set of (x, y) pixels of the spire + its sea stack, and the tower's window pixel."""
    m = set()
    rnd = random.Random(7)
    # sea stack: jagged, leaning slightly, sitting in the sea
    for y in range(106, HZ + 3):
        t = (y - 106) / (HZ + 3 - 106)
        hl = 12 + 15 * t ** 0.8 + 3 * (tn(y * 4, 0, 32, 1, 50) - 0.5) * 2
        hr = 11 + 13 * t ** 0.9 + 3 * (tn(y * 4, 0, 32, 1, 51) - 0.5) * 2
        for x in range(int(SPX - hl), int(SPX + hr) + 1):
            m.add((x, y))
    # a broken shoulder of rock on the left
    for y in range(116, 126):
        for x in range(SPX - 22 + (y - 116) // 3 * -1, SPX - 12):
            m.add((x, y))
    # tower: plinth, shaft with buttress steps
    for y in range(52, 107):
        hw = 6 if y < 94 else 8 if y < 101 else 10
        for x in range(SPX - hw, SPX + hw + 1):
            m.add((x, y))
        if y > 70 and (y - 70) % 12 < 2:            # string courses
            m.add((SPX - hw - 1, y))
            m.add((SPX + hw + 1, y))
    # buttress fins
    for y in range(78, 101):
        k = (y - 78) / 22
        for s in (-1, 1):
            m.add((SPX + s * (7 + int(k * 3)), y))
    # belfry with two open arches (see-through)
    for y in range(40, 53):
        for x in range(SPX - 8, SPX + 9):
            m.add((x, y))
    for y in range(43, 50):
        for x in (SPX - 4, SPX - 3, SPX + 3, SPX + 4):
            if not (y == 43 and x in (SPX - 4, SPX + 4)):
                m.discard((x, y))
    # corner pinnacles
    for s in (-1, 1):
        for y in range(33, 41):
            m.add((SPX + s * 8, y))
            if y > 36:
                m.add((SPX + s * 7, y))
    # the spire cone (broken on the right side: a jagged bite)
    for y in range(14, 41):
        t = (y - 14) / 26
        hw = 0.4 + 6.2 * t ** 1.1
        for x in range(int(SPX - hw), int(SPX + hw) + 1):
            if abs(x + 0.5 - SPX) <= hw + 0.5:
                m.add((x, y))
    for y in range(20, 33):
        bite = 3 + int(2 * math.sin(y * 1.3)) + (1 if y in (25, 26) else 0)
        t = (y - 14) / 26
        hw = 0.4 + 6.2 * t ** 1.1
        for x in range(int(SPX + hw - bite) + 1, int(SPX + hw) + 2):
            m.discard((x, y))
    # lightning rod + crossbar + ring
    for y in range(4, 15):
        m.add((SPX, y))
    for x in range(SPX - 2, SPX + 3):
        m.add((x, 9))
    m.add((SPX - 1, 6))
    m.add((SPX + 1, 6))
    window = (SPX - 2, 64)
    return m, window


def bolt_path(p0, p1, seed, rough=0.28, depth=6):
    """Jagged midpoint-displaced polyline from p0 to p1 (a list of integer points, 8-connected)."""
    rnd = random.Random(seed)
    pts = [p0, p1]
    for d in range(depth):
        nxt = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            mx = (a[0] + b[0]) / 2 + rnd.uniform(-1, 1) * L * rough
            my = (a[1] + b[1]) / 2 + rnd.uniform(-0.2, 0.2) * L * rough
            nxt += [(mx, my), b]
        pts = nxt
    out = []
    for a, b in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for k in range(n + 1):
            p = (round(a[0] + (b[0] - a[0]) * k / n), round(a[1] + (b[1] - a[1]) * k / n))
            if not out or out[-1] != p:
                out.append(p)
    return out


def main_bolt():
    trunk = bolt_path(BOLT_TOP, BOLT_BOT, 11, 0.22)
    rnd = random.Random(12)
    branches = []
    for (frac, dx, dy, sd) in ((0.22, -26, 30, 1), (0.45, 22, 24, 2), (0.6, -14, 30, 3), (0.12, 30, 12, 4)):
        p = trunk[int(len(trunk) * frac)]
        branches.append(bolt_path(p, (p[0] + dx, p[1] + dy), 20 + sd, 0.3, 4))
    # a secondary fork twig on the first branch
    b0 = branches[0]
    q = b0[len(b0) // 2]
    branches.append(bolt_path(q, (q[0] - 12, q[1] + 16), 31, 0.3, 3))
    return trunk, branches


# ---------------------------------------------------------------------------- FAR
class FarStatic:
    def __init__(self):
        self.val = [[0.0] * W for _ in range(H)]
        self.under = [[0.0] * W for _ in range(H)]      # 1 on lit cloud undersides
        self.bank = [[-1] * W for _ in range(H)]
        bots = [[bank_bottom(b, x) for x in range(W)] for b in BANKS]
        self.bots = bots
        for y in range(H):
            for x in range(W):
                if y >= HZ:
                    continue
                # open sky under the storm: glow band at the horizon
                v = 0.24 + 0.10 * smooth(60, HZ, y) + 0.09 * math.exp(-((y - HZ + 6) / 9.0) ** 2)
                v += 0.02 * (tn(x, y, 128, 32, 3) - 0.5)
                bi = -1
                for i in range(len(BANKS) - 1, -1, -1):
                    if y < bots[i][x]:
                        bi = i
                        break
                if bi >= 0:
                    b = BANKS[bi]
                    dy = bots[bi][x] - y                      # distance above the underside
                    v = b["tone"]
                    u = math.exp(-dy / 6.0)
                    m = 0.35 + 0.9 * tn(x + bi * 37, 0, 128, 1, 70 + bi)
                    v += 0.07 * u * m
                    # the upper, shadowed body of each bank darkens towards the next bank's underside
                    v -= 0.05 * smooth(4, 26, dy)
                    # billow texture: soft large lumps
                    v += 0.03 * (tn(x, y, 64, 16, 10 + bi) - 0.5) * 2
                    if dy < 1.2:
                        v += 0.035 * m                        # crisp lit rim of the underside
                    self.under[y][x] = u
                    self.bank[y][x] = bi
                self.val[y][x] = v
        # rain curtains (virga) hanging under the low banks: slanted, slightly darker
        for y in range(70, HZ):
            for x in range(W):
                u = x - 0.35 * y
                c = tn(u, 0, 64, 1, 77)
                if c > 0.62:
                    self.val[y][x] -= 0.03 * smooth(0.62, 0.8, c) * smooth(70, 100, y)
        # far low headlands on the left horizon (hazy)
        for x in range(W):
            hl = max(0.0, tn(x, 0, 128, 1, 90) - 0.5) * 2
            if hl <= 0:
                continue
            top = HZ - 1 - 10 * hl ** 0.7 - 2 * tn(x, 0, 16, 1, 91)
            for y in range(int(top), HZ):
                self.val[y][x] = 0.17 if y > top + 1 else 0.25
        # sea
        for y in range(HZ, H):
            d = (y - HZ) / (H - HZ)
            for x in range(W):
                v = 0.19 - 0.13 * d ** 0.6
                v += 0.02 * (tn(x, y, 64, 4, 60) - 0.5)
                self.val[y][x] = v
        self.crests = self.make_crests()
        self.spire, self.window = spire_mask()
        self.rain = self.make_rain()

    def make_crests(self):
        """Perspective swell lines: list of (y, x0, length, foam?, phase)."""
        rnd = random.Random(5)
        out = []
        y = HZ + 1.0
        k = 0
        while y < H:
            depth = (y - HZ) / (H - HZ)
            n = int(6 + 18 * depth)
            for i in range(n):
                x0 = rnd.randrange(W)
                L = int(3 + depth * 18 * rnd.random() + 2)
                foam = rnd.random() < 0.18 + 0.3 * depth
                out.append((int(y), x0, L, foam, rnd.random()))
            y += 1.2 + depth * 5.5
            k += 1
        return out

    def make_rain(self):
        rnd = random.Random(9)
        return [(rnd.randrange(W), rnd.randrange(64), rnd.randint(3, 6)) for _ in range(150)]


_FS = None


def far_static():
    global _FS
    if _FS is None:
        _FS = FarStatic()
    return _FS


def light_at(x, y, src, fs, I, reach, glob, under_boost):
    if I <= 0:
        return 0.0
    d = math.hypot(wrapdx(x, src[0]), (y - src[1]) * 1.3)
    loc = math.exp(-d / reach)
    v = I * (glob + (1 - glob) * loc)
    if y < HZ and fs.bank[y][x] >= 0:
        v *= 0.55 + under_boost * fs.under[y][x]
    return v


FLASH = {
    # frame: (source, intensity, reach, global, underside boost, bolt stage)
    4: (BOLT_TOP, 0.95, 150, 0.45, 0.9, "main_full"),
    5: (BOLT_TOP, 0.42, 120, 0.35, 0.8, "main_fade"),
    6: (BOLT_TOP, 0.10, 110, 0.30, 0.6, "main_ghost"),
    7: (SHEET, 0.80, 70, 0.12, 0.35, "thin_full"),
    8: (SHEET, 0.34, 60, 0.10, 0.3, "thin_fade"),
    9: (SHEET, 0.09, 55, 0.10, 0.3, None),
}


def build_far_frame(f):
    fs = far_static()
    cv = Canvas(W, H, wrap=True)
    idx = [[0] * W for _ in range(H)]
    src, I, reach, glob, ub, stage = FLASH.get(f, (None, 0.0, 1, 0, 0, None))
    loopf = f % 4
    for y in range(H):
        for x in range(W):
            v = fs.val[y][x]
            if I > 0:
                if y < HZ:
                    v += light_at(x, y, src, fs, I, reach, glob, ub)
                else:
                    # sea catches the flash: overall lift, strongest in a column under the source
                    d = abs(wrapdx(x, src[0]))
                    v += I * (0.22 * glob + 0.26 * math.exp(-d / 60.0)) * (1 - 0.6 * (y - HZ) / (H - HZ))
            idx[y][x] = pick_i(NF, v, x, y)
    # spire silhouette + rim light (cold, from upper-left; in the main flash lit from the right, the bolt side)
    for (x, y) in fs.spire:
        if not (0 <= y < H):
            continue
        lf = (x - 1, y) not in fs.spire
        rt = (x + 1, y) not in fs.spire
        up = (x, y - 1) not in fs.spire
        base = 1 if (I > 0.3 and stage and stage.startswith("main")) else 2
        c = base
        if f in (4, 5):
            if rt or up:
                c = 12 if f == 4 else 8
        else:
            if up:
                c = 7
            elif lf:
                c = 5
        if y >= HZ and c > base:
            c = base
        idx[y][x % W] = c
    # sea: swell crests, whitecaps (animated in the loop), a dark trough under each crest
    for (y, x0, L, foam, ph) in fs.crests:
        if y >= H:
            continue
        near = I * (math.exp(-abs(wrapdx(x0, src[0])) / 70.0) if src else 0)
        for i in range(L):
            x = (x0 + i) % W
            if (x, y) in fs.spire:
                continue
            idx[y][x] = min(NF - 1, idx[y][x] + 1 + int(near * 8))
            if y + 1 < H and i % 2 == 0:
                idx[y + 1][x] = max(0, idx[y + 1][x] - 1)
    for (x, y) in list(fs.spire):
        pass
    img = cv.img
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = FAR[idx[y][x]]
    # the tower's single warm window (dimmed by the flash's glare)
    wx, wy = fs.window
    px[wx, wy] = AMBER[3] if f not in (4,) else AMBER[1]
    px[wx, wy + 1] = AMBER[2] if f not in (4,) else AMBER[0]
    # whitecaps: foam dabs, each with its own phase; 4-frame loop
    for (y, x0, L, foam, ph) in fs.crests:
        if not foam or y >= H:
            continue
        a = math.sin(2 * math.pi * (ph + loopf / 4.0))
        if a < 0.3:
            continue
        depth = (y - HZ) / (H - HZ)
        n = max(1, int(L * 0.5 * a))
        xs = x0 + (L - n) // 2
        near = I * (math.exp(-abs(wrapdx(x0, src[0])) / 70.0) if src else 0)
        for i in range(n):
            x = (xs + i) % W
            if (x, y) in fs.spire:
                continue
            k = 0 if depth < 0.45 else 1
            if i == n // 2 and a > 0.8 and depth > 0.3:
                k += 1
            k = min(3, k + int(near * 3))
            px[x, y] = FOAM[k]
            if depth > 0.5 and a > 0.5 and i % 3 == 1 and y - 1 > HZ:
                px[x, y - 1] = FOAM[max(0, k - 1)]
    # surf ring around the sea stack
    for x in range(SPX - 30, SPX + 28):
        y = HZ + 2
        if (x, y - 1) in fs.spire or (x, y) in fs.spire or (x + 1, y - 1) in fs.spire or (x - 1, y - 1) in fs.spire:
            ok = h01(x, loopf, 44) < 0.45
            if ok and (x, y) not in fs.spire:
                px[x % W, y] = FOAM[1] if h01(x, loopf, 45) < 0.3 else FOAM[0]
    # rain: slanted streaks falling along their slant, 16px per frame (period 64 -> perfect 4-frame loop)
    slope = 0.32
    for (su, sy, L) in fs.rain:
        for rep in range(0, H + 64, 64):
            y0 = sy + rep + loopf * 16 - 64
            for j in range(L):
                y = y0 + j
                if not (0 <= y < H):
                    continue
                x = int(su + slope * y) % W
                if (x, y) in fs.spire:
                    continue
                c = px[x, y]
                try:
                    i = FAR.index(c)
                except ValueError:
                    continue
                lift = 1
                if I > 0.2:
                    lift = 1 + int(I * 4 * math.exp(-abs(wrapdx(x, src[0])) / 140.0))
                if j == 0 and L < 5:
                    continue
                px[x, y] = FAR[min(NF - 1, i + lift)]
    # rod spark: a tiny cold spark at the tip, loop frames 1 and 3 (restrained)
    if f in (1, 3, 4, 5):
        px[SPX, 3] = BOLT[1] if f != 4 else BOLT[3]
        if f in (4, 5):
            px[SPX, 2] = BOLT[2]
            px[SPX - 1, 4] = BOLT[1]
            px[SPX + 1, 4] = BOLT[1]
    # lightning bolts
    if stage in ("main_full", "main_fade", "main_ghost"):
        trunk, branches = main_bolt()
        draw_bolt(px, trunk, stage, main=True)
        if stage != "main_ghost":
            for bi, br in enumerate(branches):
                if stage == "main_fade" and bi not in (1,):
                    continue
                draw_bolt(px, br, stage, main=False)
        if stage == "main_full":
            # strike splash + reflection column on the sea
            bx, by = BOLT_BOT
            for y in range(HZ + 1, H):
                for dx in (-1, 0, 1):
                    if bt(bx + dx, y) < 0.55 - (y - HZ) / 160.0 - abs(dx) * 0.2:
                        px[(bx + dx + (y % 3 == 0)) % W, y] = BOLT[2] if dx == 0 else BOLT[1]
            for (dx, dy) in ((-2, 0), (2, 0), (-3, 1), (3, 1), (-1, -1), (1, -1), (0, -2)):
                px[(bx + dx) % W, by + dy] = BOLT[3] if abs(dx) < 2 else BOLT[2]
    if stage in ("thin_full", "thin_fade"):
        thin = bolt_path(THIN_TOP, THIN_BOT, 41, 0.25, 5)
        for (x, y) in thin:
            if 0 <= y < H:
                px[x % W, y] = BOLT[2] if stage == "thin_full" else BOLT[0]
                if stage == "thin_full" and bt(x, y) < 0.5:
                    px[(x + 1) % W, y] = BOLT[1]
        # cloud-to-cloud crawler inside the lit bank (sheet lightning veins)
        if stage == "thin_full":
            for (p0, p1, sd) in (((90, 52), (150, 62), 51), ((118, 56), (100, 80), 52)):
                for (x, y) in bolt_path(p0, p1, sd, 0.3, 4):
                    if 0 <= y < H and bt(x, y) < 0.7:
                        px[x % W, y] = BOLT[1] if bt(x, y) < 0.35 else FAR[17]
    return img


def draw_bolt(px, pts, stage, main):
    if stage == "main_full":
        core, glow, halo = BOLT[3], BOLT[2], BOLT[1]
    elif stage == "main_fade":
        core, glow, halo = BOLT[2], BOLT[1], None
    else:
        core, glow, halo = BOLT[0], None, None
    for (x, y) in pts:
        if not (0 <= y < H):
            continue
        if stage == "main_ghost" and (y % 3 == 0 or y < BOLT_TOP[1] + 20):
            continue
        if halo and main:
            for (dx, dy) in ((-2, 0), (2, 0)):
                X = (x + dx) % W
                c = px[X, y]
                if c in FAR and FAR.index(c) < 16 and bt(X, y) < 0.5:
                    px[X, y] = halo
        wide = main and stage == "main_full"
        if glow:
            for dx in ((-1, 2) if wide else (-1, 1)):
                X = (x + dx) % W
                if px[X, y] not in (core,) and (main or bt(X, y) < 0.4):
                    px[X, y] = glow
        px[x % W, y] = core
        if wide:
            px[(x + 1) % W, y] = core


def build_spire_far():
    """-> list of 10 frame images."""
    return [build_far_frame(f) for f in range(10)]


# ---------------------------------------------------------------------------- MID
MD = ramp("06070c", "090b11", "0d1017", "12151e", "171b26", "1d2230")
RIM = [C("2a3346"), C("3a4760"), C("52627e")]
MFOAM = [C("3e5068"), C("62788e"), C("8ea4b8"), C("bcd0de")]


def crag(x, peaks, cx_wrap=True):
    """Craggy top profile: the lowest of several steep 'fang' cones + small ledge steps. None if no rock."""
    best = None
    for (px_, py_, sl) in peaks:
        d = abs(wrapdx(x, px_)) if cx_wrap else abs(x - px_)
        y = py_ + sl * d
        if best is None or y < best:
            best = y
    if best is None:
        return None
    return best + 2 * math.floor(tn(x, 0, 8, 1, 17) * 2.2)


def cliff_top(x):
    """The headland: a plateau (x -8..100) falling in stepped crags to the sea on both sides."""
    xx = wrapdx(x, 50)                                   # -206..306 around the headland centre
    if xx < -60 or xx > 86:
        return None
    base = 104 + 2 * (tn(x, 0, 32, 1, 5) - 0.5) * 2
    if xx > 50:                                          # east face: steep, with two ledges
        d = xx - 50
        base += d ** 1.45 * 0.9 + (6 if d > 14 else 0) + (5 if d > 26 else 0)
    elif xx < -40:                                       # west flank, gentler
        d = -40 - xx
        base += d ** 1.3 * 1.4
    return base + 2 * math.floor(tn(x, 0, 8, 1, 17) * 2.2)
STACKS = [  # (centre x, half width of the crown, crown y, seed) — columnar stacks with broken crowns
    (388, 11, 104, 1), (430, 7, 140, 2), (466, 13, 90, 3), (503, 5, 160, 4),
]


def stack_top(x, st):
    cx, hw, top, sd = st
    d = x + 0.5 - cx
    ad = abs(d)
    rnd = random.Random(sd)
    fangs = [(rnd.uniform(-hw, hw), rnd.uniform(0, 7)) for _ in range(4)] + [(0, 0)]
    crown = min(fy + 2.6 * abs(d - fx) for fx, fy in fangs)
    crown = min(crown, 12)
    if ad <= hw:
        return top + crown
    # steep, ledged sides flaring towards the sea
    e = ad - hw
    ledge = 7 if e > 2 else 0
    return top + min(12, crown) + e * 7.5 + ledge + (4 if e > 5 else 0)


def rock_column(cv, x, top, SEA_Y, seed):
    """Fill a rock column from top to the sea; a few long, sparse vertical crevices."""
    crev = h01(x, 0, seed) < 0.06
    y0 = int(top) + 6 + int(h01(x, 1, seed) * 20)
    y1 = y0 + 10 + int(h01(x, 2, seed) * 30)
    for y in range(int(top), SEA_Y):
        c = MD[2]
        if crev and y0 <= y <= y1:
            c = MD[1]
        cv.set(x, y, c)


def build_mid_frame(f):
    cv = Canvas(W, H, wrap=True)
    SEA_Y = 200
    # -------------------------------------------- near sea strip (the water in front of the stacks)
    for y in range(SEA_Y, H):
        for x in range(W):
            cv.set(x, y, MD[1] if y > SEA_Y + 1 else MD[3])
    # -------------------------------------------- left headland: plateau, then a stepped cliff face into the sea
    for x in range(W):
        t = cliff_top(x)
        if t is None or t >= SEA_Y:
            continue
        rock_column(cv, x, t, SEA_Y, 3)
    # cottage silhouette on the plateau (sagging roof, chimney, one warm window)
    ctx, cty = 78, cliff_top(78)
    for y in range(int(cty) - 9, int(cty) + 1):
        for x in range(ctx - 9, ctx + 9):
            cv.set(x, y, MD[3])
    for y in range(int(cty) - 19, int(cty) - 9):
        hw = (y - (cty - 19)) * 1.05 + 1 + (1 if y > cty - 12 else 0)
        for x in range(int(ctx - hw), int(ctx + hw) + 1):
            cv.set(x, y + (1 if abs(x - ctx) < 3 and y > cty - 16 else 0), MD[3])     # a sag in the ridge
    for y in range(int(cty) - 22, int(cty) - 13):
        cv.set(ctx + 5, y, MD[3])
        cv.set(ctx + 6, y, MD[3])
    cv.set(ctx - 4, int(cty) - 5, AMBER[3])
    cv.set(ctx - 4, int(cty) - 4, AMBER[2])
    cv.set(ctx - 5, int(cty) - 5, AMBER[2])
    # windmill: tapered tower, cone cap, 4 sails turning (22.5 deg per frame -> seamless 4-frame loop)
    wx, wb = 36, int(cliff_top(36)) + 1
    for y in range(wb - 38, wb):
        t = (y - (wb - 38)) / 38
        hw = 4.5 + 3.5 * t
        for x in range(int(wx - hw), int(wx + hw) + 1):
            cv.set(x, y, MD[3])
    for y in range(wb - 48, wb - 37):
        hw = (y - (wb - 48)) * 0.62 + 0.5
        for x in range(int(wx - hw), int(wx + hw) + 1):
            cv.set(x, y, MD[3])
    cv.set(wx - 1, wb - 20, AMBER[3])
    cv.set(wx - 1, wb - 19, AMBER[2])
    hub = (wx + 2, wb - 38)
    ang0 = math.radians(22.5 * f + 12)
    for k in range(4):
        a = ang0 + k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        L = 26                                           # identical sails: 90 deg symmetry -> seamless 4-frame loop
        for r10 in range(10, L * 10):
            r = r10 / 10
            cv.set(hub[0] + ca * r, hub[1] + sa * r, MD[4])
            if r > 7:
                wd = 4 if r < 18 else 2                  # canvas torn from the tips
                for w10 in range(5, wd * 10, 5):
                    w = w10 / 10
                    x_ = hub[0] + ca * r - sa * w
                    y_ = hub[1] + sa * r + ca * w
                    cv.set(x_, y_, MD[3] if int(r) % 5 else MD[4])
    # -------------------------------------------- the broken arched causeway
    DECK, DECK_B = 148, 156
    PIERS = list(range(142, 350, 34))
    gap = (238, 272)
    for x in range(118, 356):
        if gap[0] <= x <= gap[1]:
            continue
        top = DECK
        if gap[0] - 7 < x < gap[0]:
            top = DECK + (x - (gap[0] - 7)) * 1.4 + (2 if x % 3 == 0 else 0)
        if gap[1] < x < gap[1] + 7:
            top = DECK + ((gap[1] + 7) - x) * 1.2 + (2 if x % 3 == 1 else 0)
        for y in range(int(top), DECK_B + 1):
            cv.set(x, y, MD[3] if y < DECK + 2 else MD[2])
        if top == DECK:
            if x % 6 == 0 and not (300 < x < 318):       # parapet posts (a stretch knocked away)
                for y in range(DECK - 4, DECK):
                    cv.set(x, y, MD[3])
            if not (300 < x < 318):
                cv.set(x, DECK - 4, MD[3])
    for i, px0 in enumerate(PIERS):
        in_gap = gap[0] - 2 < px0 + 4 < gap[1] + 2
        top = DECK_B if not in_gap else 170
        for y in range(top, SEA_Y):
            flare = 1 if y > 190 else 0
            for x in range(px0 - flare, px0 + 8 + flare):
                cv.set(x, y, MD[2])
        if in_gap:                                        # the lone surviving pier: broken, jagged crown
            for x in range(px0, px0 + 8):
                for y in range(top - (3 if x in (px0 + 1, px0 + 5) else 1 if x % 2 else 0), top):
                    cv.set(x, y, MD[2])
    for a, b in zip(PIERS, PIERS[1:]):
        x0, x1 = a + 8, b
        if gap[0] - 4 < x0 < gap[1] or gap[0] < x1 < gap[1] + 4:
            continue
        cx, r = (x0 + x1) / 2, (x1 - x0) / 2
        for x in range(x0, x1):
            dy = math.sqrt(max(0.0, r * r - (x + 0.5 - cx) ** 2))
            for y in range(DECK_B, int(DECK_B + 16 - dy * 0.9)):
                cv.set(x, y, MD[2])
    # causeway lamp post (one warm point)
    for y in range(DECK - 12, DECK - 4):
        cv.set(208, y, MD[4])
    cv.set(209, DECK - 12, MD[4])
    cv.set(210, DECK - 11, AMBER[3])
    cv.set(210, DECK - 10, AMBER[2])
    # -------------------------------------------- jagged sea stacks on the right
    for x in range(360, 512):
        for si, st in enumerate(STACKS):
            t = stack_top(x, st)
            if t is not None and t < SEA_Y:
                rock_column(cv, x, t, SEA_Y, 10 + si)
    # ruined arch fragment on the tallest stack
    ax = 460
    at = int(stack_top(ax, STACKS[2]))
    for y in range(at - 12, at + 1):
        cv.set(ax, y, MD[3])
        cv.set(ax + 1, y, MD[3])
    for i in range(12):
        a = math.pi * (1 - i / 22)
        cv.set(ax + 8 + 7 * math.cos(a), at - 10 - 6 * math.sin(a), MD[3])
    # -------------------------------------------- rim light (cold, from above; left edges fainter)
    px = cv.img.load()
    body_set = set(MD)
    hits = []
    for y in range(1, SEA_Y):
        for x in range(W):
            c = px[x, y]
            if c not in body_set:
                continue
            up, lf = px[x, y - 1], px[(x - 1) % W, y]
            if up[3] == 0:
                hits.append((x, y, RIM[2] if h01(x, y, 3) < 0.35 else RIM[1]))
            elif lf[3] == 0:
                hits.append((x, y, RIM[0]))
    for (x, y, c) in hits:
        px[x, y] = c
    # -------------------------------------------- waves bursting on the bases (4-frame cycle, staggered)
    sites = [(138, 0), (153, 2), (283, 1), (352, 3), (378, 1), (440, 2), (482, 0), (503, 3)]
    for (sx, off) in sites:
        splash(cv, sx, SEA_Y, (f + off) % 4, sx)
    # foam line along the near sea surface
    for x in range(W):
        if ((x + f * 5) % 13) < 3:
            cv.set(x, SEA_Y, MFOAM[1])
        if ((x * 3 + f * 7) % 19) < 2:
            cv.set(x, SEA_Y + 3, MFOAM[0])
    return cv.img


def splash(cv, sx, sy, ph, seed):
    """One wave bursting at a base. ph 0 foam mound, 1 rising plume, 2 peak (fingers + droplets), 3 collapse."""
    rnd = random.Random(seed * 13 + ph)
    lit, mid, dark = MFOAM[2], MFOAM[1], MFOAM[0]
    if ph == 0:
        for x in range(sx - 5, sx + 6):
            h = 2 if abs(x - sx) < 3 else 1
            for y in range(sy - h, sy + 1):
                cv.set(x, y, mid if y == sy - h else dark)
        return
    if ph == 1:
        H_ = 9
        for y in range(sy - H_, sy + 1):
            t = (sy - y) / H_
            hw = 3.2 * (1 - t) ** 0.6 + 0.6
            for x in range(int(sx - hw), int(sx + hw) + 1):
                cv.set(x, y, lit if x < sx else mid)
        for x in range(sx - 6, sx + 7):
            cv.set(x, sy, mid)
        return
    if ph == 2:
        H_ = 15
        for y in range(sy - 8, sy + 1):
            t = (sy - y) / 8
            hw = 3.5 * (1 - t) + 1
            for x in range(int(sx - hw), int(sx + hw) + 1):
                cv.set(x, y, lit if x <= sx else mid)
        for (dx, sgn) in ((-1, -1), (0, 0), (1, 1)):        # three fingers fanning out
            for i in range(8):
                x = sx + dx + sgn * (i * i) / 14.0
                y = sy - 8 - i
                cv.set(x, y, lit if sgn <= 0 else mid)
        for i in range(7):
            cv.set(sx + rnd.randint(-8, 8), sy - rnd.randint(9, H_ + 2), mid)
        for x in range(sx - 7, sx + 8):
            cv.set(x, sy, mid)
        return
    # collapse: wide low foam, falling droplets
    for x in range(sx - 8, sx + 9):
        h = 3 if abs(x - sx) < 4 else 2 if abs(x - sx) < 7 else 1
        for y in range(sy - h, sy + 1):
            cv.set(x, y, mid if y == sy - h else dark)
    for i in range(6):
        cv.set(sx + rnd.randint(-9, 9), sy - rnd.randint(4, 10), dark)


def build_spire_mid():
    """-> list of 4 frame images."""
    return [build_mid_frame(f) for f in range(4)]


BUILDERS = {"spire": (build_spire_far, build_spire_mid)}
