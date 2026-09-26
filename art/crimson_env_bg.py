"""Parallax + interior backdrops for THE CRIMSON MANOR.

bg_crimson_far  512x216 opaque, tileable, 4 frames (blood rain): a huge dark blood moon low in a black-violet sky,
                thin dark-red cloud strands, the manor's distant spires on a hill, faint slanted blood-rain streaks.
bg_crimson_mid  512x216 transparent, tileable: black gothic manor wings, spires, an iron fence with stone posts,
                dead trees, gargoyles on posts; a few tiny dim red-orange lit windows.
cm_interior     64x128 frames: paper / wainscot / window / pilaster (the engine composes indoor back layers from them)
"""
import math, random
from PIL import Image
from envlib import T, K, bt, h01, clamp, smooth, Canvas, fbm, vnoise, blank
from crimson_env_lib import (ST, MB, SV, BL, VV, DM, WD, IR, GL, WX, FL, Spr, lit, ellipse_fill, outline)
from envlib import ramp

W, H = 512, 216

SKY = ramp("040308", "07050b", "0a070f", "0e0913", "130b17", "180d1a", "1e0f1c", "25111e", "2d1320", "361522")
MOON = ramp("1a060b", "270910", "360c13", "461017", "58141a", "6c1a1e", "822424", "983228")
CLD = ramp("0c0710", "130a14", "1b0c17", "240e19", "30121c", "3e1620")
SIL = ramp("050407", "08060b", "0b080f", "0f0b13", "140e18", "1a121e")
WIN = ramp("2e0c0a", "4a140e", "6e2212", "924018")
RAIN = [(0x2a, 0x0c, 0x16, 255), (0x3a, 0x10, 0x18, 255), (0x52, 0x14, 0x1c, 255)]

MCX, MCY, MR = 318, 120, 74


def wrapdx(x, cx, period=W):
    d = (x - cx) % period
    return d - period if d > period / 2 else d


# =========================================================================== far
def sky_v(x, y):
    v = 0.10 + 0.30 * smooth(0, 200, y)
    d = math.hypot(wrapdx(x, MCX), y - MCY)
    v += 0.42 * math.exp(-max(0.0, d - MR) / 34.0) * (d > MR)
    return v


def moon_px(x, y):
    dx, dy = (x + .5 - MCX) / MR, (y + .5 - MCY) / MR
    d2 = dx * dx + dy * dy
    if d2 > 1:
        return None
    nz = math.sqrt(1 - d2)
    light = 0.5 + 0.5 * (-0.5 * dx - 0.45 * dy + 0.5 * nz)             # lit from the upper-left
    mar = fbm(x, y, 32, 24, 17, W=512)
    v = 0.12 + 0.62 * light
    if mar > 0.56:
        v -= 0.16                                                        # maria: flat darker seas
    if mar > 0.64:
        v -= 0.08
    v -= 0.14 * smooth(0.86, 1.0, math.sqrt(d2))                        # limb darkening
    i = int(clamp(v) * (len(MOON) - 1) + 0.5)
    if d2 > 0.9 and dx + dy < -0.5:
        i += 1                                                           # thin bright limb upper-left
    return MOON[max(0, min(len(MOON) - 1, i))]


CLOUDS = [  # (centre x, centre y, length, thickness, seed)
    (300, 94, 250, 9, 1), (372, 110, 150, 6, 2), (120, 70, 200, 8, 3), (40, 118, 150, 6, 4), (470, 82, 170, 7, 5),
    (236, 142, 130, 5, 6), (190, 50, 120, 5, 7), (420, 146, 140, 6, 8), (262, 124, 100, 4, 9),
]


def cloud_hit(x, y):
    """0 = none, 1 = cloud body, 2 = cloud lower edge (lit from the moon behind)."""
    best = 0
    for (cx, cy, L, th, sd) in CLOUDS:
        d = wrapdx(x, cx)
        u = d / (L / 2)
        if abs(u) >= 1:
            continue
        t = th * (1 - u * u) ** 0.8 * (0.55 + 0.45 * vnoise(x, sd * 10, 12, 1, sd, W // 12))
        yc = cy + 2.5 * math.sin(d * 0.03 + sd) + 1.5 * math.sin(d * 0.09 + sd * 2) + (u * 3 if sd % 2 else -u * 3)
        if abs(y + .5 - yc) <= t / 2:
            k = 2 if (y + 1.5 - yc) > t / 2 else 3 if (y - 0.5 - yc) < -t / 2 else 1
            best = max(best, k) if best != 3 else best
    return best


def hill_y(x):
    return 176 + 10 * math.sin(x * 2 * math.pi / 512 * 2 + 0.7) + 6 * fbm(x, 0, 64, 1, 9, W=512)


def far_ridge_y(x):
    return 160 + 12 * math.sin(x * 2 * math.pi / 512 * 3 + 2.1) + 8 * fbm(x, 0, 32, 1, 3, W=512)


def manor_far(cv):
    """The manor on its hill: a silhouette of towers, spires and roofs (drawn over the moon, it rises into it)."""
    col, rim = SIL[1], SIL[3]
    base = 170
    # main block + roofs
    def box(x0, x1, top):
        for x in range(x0, x1 + 1):
            for y in range(top, 200):
                cv.set(x, y, col)

    def spire(cx, top, hw, base_y):
        for y in range(top, base_y + 1):
            t = (y - top) / max(1, base_y - top)
            w = hw * t
            for x in range(int(round(cx - w)), int(round(cx + w)) + 1):
                cv.set(x, y, col)
        cv.set(cx, top - 1, col)
        cv.set(cx, top - 2, col)

    def gable(x0, x1, top, peak):
        cx = (x0 + x1) / 2
        for x in range(x0, x1 + 1):
            yy = top - (peak * (1 - abs(x - cx) / ((x1 - x0) / 2)))
            for y in range(int(yy), top + 1):
                cv.set(x, y, col)

    # east wing, central keep, west wing (spanning the moon)
    box(252, 300, 150); gable(252, 276, 150, 10); gable(277, 300, 150, 10)
    box(300, 322, 128); spire(311, 70, 11, 128)                           # the great spire
    for (tx, top, hw) in ((296, 118, 4), (326, 112, 4)):
        box(tx - 3, tx + 3, top); spire(tx, top - 18, hw, top)
    box(322, 372, 146); gable(322, 346, 146, 9); gable(347, 372, 146, 9)
    box(372, 384, 132); spire(378, 104, 7, 132)
    box(238, 252, 140); spire(245, 116, 8, 140)
    # chimneys + pinnacles
    for (x, top) in ((262, 136), (290, 132), (336, 132), (360, 134)):
        for y in range(top, 150):
            cv.set(x, y, col); cv.set(x + 1, y, col)
    for x in range(238, 385, 6):
        cv.set(x, 139 if x < 252 else 149 if x < 300 else 127 if x < 322 else 145 if x < 372 else 131, col)
    # tiny dim windows
    for (x, y) in ((260, 162), (268, 160), (284, 164), (309, 140), (313, 150), (340, 158), (356, 160), (244, 150),
                   (378, 142), (311, 108)):
        cv.set(x, y, WIN[1]); cv.set(x, y + 1, WIN[0])
    # moonlit rim on the upper-left edges of the silhouette (only against the moon)
    px = cv.img.load()
    hits = []
    for y in range(60, 200):
        for x in range(230, 392):
            if px[x, y] != col:
                continue
            up, lf = px[x, y - 1], px[x - 1, y]
            if (up != col and up not in (WIN[0], WIN[1])) or (lf != col and lf not in (WIN[0], WIN[1])):
                inside = math.hypot(x - MCX, y - MCY) < MR + 6
                hits.append((x, y, rim if inside else SIL[2]))
    for (x, y, c) in hits:
        px[x, y] = c


def rain(cv, f, n_frames=4, count=150, seed=7, dark=False):
    """Slanted blood-rain streaks: pattern in sheared space (u = x + s*y), shifted down 216/n per frame (loops)."""
    rnd = random.Random(seed)
    s = 0.34
    px = cv.img.load()
    for i in range(count):
        u0 = rnd.uniform(0, W)
        y0 = rnd.uniform(0, H)
        L = rnd.randint(4, 8)
        bright = rnd.random() < 0.25
        for t in range(L):
            y = (y0 + t + f * H / n_frames) % H
            x = int(round(u0 - s * y)) % W
            yi = int(y)
            cur = px[x, yi]
            c = RAIN[2] if (bright and t >= L - 2) else RAIN[1] if t >= L // 2 else RAIN[0]
            # only draw if it brightens (rain is lit against the dark sky, lost against the moon)
            if sum(c[:3]) > sum(cur[:3]):
                px[x, yi] = c


def build_crimson_far(frames=4):
    base = Canvas(W, H, wrap=True)
    for y in range(H):
        for x in range(W):
            n = fbm(x, y, 64, 16, 5, W=512) - 0.5
            base.set(x, y, lit(SKY, sky_v(x, y) + 0.05 * n, x, y))
    # stars? no -- a starless underground "sky": faint red motes of drifting ash instead
    rnd = random.Random(4)
    for i in range(40):
        x, y = rnd.randrange(W), rnd.randrange(8, 120)
        if math.hypot(wrapdx(x, MCX), y - MCY) > MR + 20:
            base.set(x, y, SKY[6])
    # moon
    for y in range(MCY - MR - 1, MCY + MR + 2):
        for x in range(MCX - MR - 1, MCX + MR + 2):
            c = moon_px(x, y)
            if c is not None:
                base.set(x, y, c)
    # cloud wisps: dark bands across the moon (its light catching their lower edge), faint red-violet over the sky
    for y in range(30, 170):
        for x in range(W):
            hit = cloud_hit(x, y)
            if not hit:
                continue
            inmoon = (x + .5 - MCX) ** 2 + (y + .5 - MCY) ** 2 <= MR * MR
            if inmoon:
                base.set(x, y, MOON[5] if hit == 2 else MOON[2] if hit == 3 else MOON[1])
            else:
                base.set(x, y, CLD[4] if hit == 2 else CLD[1] if hit == 3 else CLD[2])
    # distant ridge (atmospheric), then the manor hill
    for x in range(W):
        r = far_ridge_y(x)
        for y in range(int(r), H):
            base.set(x, y, SKY[4] if y == int(r) else SKY[2])
    manor_far(base)
    for x in range(W):
        hy = hill_y(x)
        for y in range(int(hy), H):
            base.set(x, y, SIL[2] if y == int(hy) else SIL[1] if y < hy + 14 else SIL[0])
        # bare trees along the hill crest
    rnd = random.Random(12)
    for i in range(14):
        tx = rnd.randrange(W)
        if 230 < tx < 392:
            continue
        ty = int(hill_y(tx))
        th = rnd.randint(8, 16)
        for y in range(ty - th, ty + 1):
            base.set(tx, y, SIL[1])
        for k in range(3):
            by = ty - th + 2 + k * 3
            ln = rnd.randint(2, 5)
            sg = 1 if (i + k) % 2 else -1
            for j in range(ln):
                base.set(tx + sg * (j + 1), by - j // 2, SIL[1])
    out = []
    for f in range(frames):
        cv = Canvas(W, H, wrap=True)
        cv.img = base.img.copy()
        cv.px = cv.img.load()
        rain(cv, f, frames)
        out.append(cv.img)
    return out


# =========================================================================== mid
class Arch:
    """Silhouette architecture on a wrapping canvas with two-tone volume (moonlight from the upper-left)."""
    def __init__(self, cv):
        self.cv = cv
        self.L, self.M, self.D, self.X = IR[2], IR[1], IR[0], IR[3]
        self.wins = []

    def box(self, x0, x1, top, bot=H - 1, c=None):
        for x in range(x0, x1 + 1):
            for y in range(top, bot + 1):
                self.cv.set(x, y, c or self.M)

    def tower(self, x0, x1, top, bot=H - 1):
        """Square tower: lit left face (a third), shaded right face."""
        split = x0 + (x1 - x0) // 3
        for x in range(x0, x1 + 1):
            for y in range(top, bot + 1):
                self.cv.set(x, y, self.L if x < split else self.M)
        for y in range(top, bot + 1, 12):                        # string courses
            for x in range(x0 - 1, x1 + 2):
                self.cv.set(x, y, self.X if x < split else self.L)

    def spire(self, cx, top, hw, base_y, crockets=True):
        for y in range(top, base_y + 1):
            t = (y - top) / max(1, base_y - top)
            w = hw * t
            for x in range(int(round(cx - w)), int(round(cx + w)) + 1):
                self.cv.set(x, y, self.L if x < cx else self.M)
            if crockets and (y - top) % 6 == 3 and t > 0.15:
                self.cv.set(int(round(cx - w)) - 1, y, self.L)
                self.cv.set(int(round(cx + w)) + 1, y, self.M)
        for y in range(top - 5, top):
            self.cv.set(cx, y, self.L)
        self.cv.set(cx - 1, top - 3, self.L); self.cv.set(cx + 1, top - 3, self.L)

    def pinnacle(self, cx, top, h=8):
        for y in range(top, top + h):
            w = (y - top) // 3
            for x in range(cx - w, cx + w + 1):
                self.cv.set(x, y, self.L if x <= cx else self.M)
        self.cv.set(cx, top - 1, self.L)

    def roof(self, x0, x1, top, pitch=1.0):
        cx = (x0 + x1) / 2
        hw = (x1 - x0) / 2
        for x in range(x0, x1 + 1):
            yy = top - pitch * (hw - abs(x - cx))
            for y in range(int(yy), top + 1):
                self.cv.set(x, y, self.M if x > cx else self.L if (top - y) > 1 else self.M)

    def lancet(self, x, y, h=9, lit=False):
        """A tall 3-px pointed window: dark opening, lit-edge frame. Recorded if lit."""
        for yy in range(y, y + h):
            for xx in range(x, x + 3):
                if yy == y and xx != x + 1:
                    continue
                self.cv.set(xx, yy, self.D)
        self.cv.set(x - 1, y + 2, self.X)
        for yy in range(y + 1, y + h):
            self.cv.set(x - 1, yy, self.L)
        for xx in range(x - 1, x + 4):
            self.cv.set(xx, y + h, self.L)
        if lit:
            self.wins.append((x, y, h))

    def wing(self, x0, x1, cornice, gables, bays, lit_bays=(), rows=2):
        """A manor wing: facade + cornice + gabled roofs + buttresses with pinnacles + lancet windows."""
        self.box(x0, x1, cornice)
        gw = (x1 - x0) / gables
        for g in range(gables):
            self.roof(int(x0 + g * gw), int(x0 + (g + 1) * gw), cornice, 0.95)
        for x in range(x0 - 1, x1 + 2):
            self.cv.set(x, cornice, self.X)
            self.cv.set(x, cornice + 1, self.D)
        bw = (x1 - x0) / bays
        for b in range(bays + 1):
            bx = int(x0 + b * bw)
            for y in range(cornice - 2, H):
                self.cv.set(bx, y, self.L)
                self.cv.set(bx + 1, y, self.M)
                self.cv.set(bx + 2, y, self.D)
            self.pinnacle(bx + 1, cornice - 10, 9)
        for b in range(bays):
            wx = int(x0 + b * bw + bw / 2) - 1
            for r in range(rows):
                self.lancet(wx, cornice + 8 + r * 20, 10, (b, r) in lit_bays)


def build_crimson_mid():
    cv = Canvas(W, H, wrap=True)
    A = Arch(cv)
    # --- west range: a long wing with a square bell tower
    A.wing(8, 128, 132, 3, 6, lit_bays={(1, 0), (4, 1)})
    A.tower(56, 80, 96)
    A.spire(68, 78, 12, 96)
    for x in (56, 80):
        A.pinnacle(x, 86, 10)
    A.lancet(66, 104, 12, lit=False)
    # --- the east house: tall hall with a rose window, flanked by twin spired towers
    A.wing(330, 470, 138, 4, 7, lit_bays={(2, 0), (5, 1)})
    A.tower(376, 424, 104)
    A.roof(376, 424, 104, 1.1)
    for x in range(376, 425):
        cv.set(x, 104, IR[3])
    cx, cy, r = 400, 120, 8                                   # rose window
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = math.hypot(x + .5 - cx - .5, y + .5 - cy - .5)
            a = math.atan2(y - cy, x - cx)
            if d <= r:
                c = IR[0]
                if abs(d - r) < 0.9:
                    c = IR[3] if (x < cx or y < cy) else IR[2]
                elif d < 2.2 or (d > 3 and abs(math.sin(a * 4)) < 0.25):
                    c = IR[2]
                cv.set(x, y, c)
    for (tx, top) in ((366, 100), (434, 100)):
        A.tower(tx - 8, tx + 8, top)
        A.spire(tx, 78, 9, top)
        A.lancet(tx - 1, top + 12, 10, lit=(tx == 434))
    # --- a ruined gothic cloister arcade joining them, dead trees in the garth
    for x in range(128, 330):
        for y in range(170, H):
            cv.set(x, y, IR[1])
        cv.set(x, 170, IR[3]); cv.set(x, 171, IR[0])
    for ax in range(134, 324, 18):
        for y in range(176, 206):
            for x in range(ax, ax + 12):
                t = y - 176
                hw = 6 if t > 5 else (0.5, 2, 3.5, 4.5, 5.2, 5.8)[t]
                if abs(x + 0.5 - (ax + 6)) <= hw:
                    cv.set(x, y, T)
        A.pinnacle(ax - 3, 162, 8)
    for b0 in (208, 262):                                    # collapsed bays: broken top edge
        for x in range(b0, b0 + 26):
            dip = int(6 * math.sin((x - b0) / 26 * math.pi) + 3 * h01(x, 0, 5))
            for y in range(162, 171 + dip):
                cv.set(x, y, T)

    def tree(x0, y0, h, seed, w0=4):
        rnd = random.Random(seed)

        def branch(x, y, ang, ln, w, depth):
            for i in range(int(ln)):
                x += math.cos(ang)
                y += math.sin(ang)
                ang += rnd.uniform(-0.14, 0.14)
                for k in range(int(w)):
                    cv.set(x + k - w // 2, y, IR[2] if k == 0 else IR[1])
            if depth > 0:
                for sg in (-1, 1):
                    if rnd.random() < 0.88:
                        branch(x, y, ang + sg * rnd.uniform(0.35, 0.8), ln * rnd.uniform(0.5, 0.72),
                               max(1, w - 1), depth - 1)
        branch(x0, y0, -math.pi / 2 + rnd.uniform(-0.1, 0.1), h, w0, 4)
        for k in range(-5, 6):                                  # root flare
            cv.set(x0 + k, y0 + (abs(k) < 3), IR[1])
    tree(176, H - 30, 34, 3)
    tree(236, H - 30, 26, 11, 3)
    tree(296, H - 30, 30, 21)
    tree(492, H - 30, 44, 8)
    # --- iron fence along the bottom, stone posts with urns and two crouching gargoyles
    fy = H - 34
    for x in range(W):
        cv.set(x, fy + 6, IR[2]); cv.set(x, fy + 7, IR[1]); cv.set(x, fy + 22, IR[2])
        if x % 5 == 0:
            for y in range(fy, H):
                cv.set(x, y, IR[2] if y < fy + 3 else IR[1])
            cv.set(x, fy - 2, IR[3]); cv.set(x, fy - 1, IR[2])
            cv.set(x - 1, fy + 1, IR[2]); cv.set(x + 1, fy + 1, IR[1])
        if x % 10 == 2:
            cv.set(x, fy + 9, IR[2]); cv.set(x + 1, fy + 10, IR[2]); cv.set(x, fy + 11, IR[2])  # scroll
    for y in range(H - 8, H):
        for x in range(W):
            cv.set(x, y, IR[0] if y > H - 8 else IR[2])
    for (px_, garg) in ((150, True), (258, False), (318, True), (500, False), (30, False)):
        A.tower(px_ - 4, px_ + 4, fy - 6)
        A.box(px_ - 5, px_ + 5, fy - 8, fy - 6, IR[3])
        if garg:
            gargoyle_sil(cv, px_, fy - 8, IR[1])
        else:
            for (dx, dy) in ((0, -1), (-1, -2), (0, -2), (1, -2), (-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3),
                             (-1, -4), (0, -4), (1, -4), (0, -5), (0, -6)):
                cv.set(px_ + dx, fy - 8 + dy, IR[2] if dx <= 0 else IR[1])
    # rim: faint moonlight on silhouette tops
    px = cv.img.load()
    hits = []
    for y in range(1, H):
        for x in range(W):
            if px[x, y][3] == 0:
                continue
            if px[x, y - 1][3] == 0:
                hits.append((x, y, IR[4] if h01(x, y, 2) < 0.4 else IR[3]))
    for (x, y, c) in hits:
        px[x, y] = c
    # a few dim, warm windows
    for (x, y, h) in A.wins:
        for yy in range(y + 1, y + h):
            for xx in range(x, x + 3):
                if yy == y + 1 and xx != x + 1:
                    continue
                c = WIN[1] if yy > y + h // 2 else WIN[2]
                if xx == x + 1 and yy == y + h // 2:
                    c = IR[0]
                cv.set(xx, yy, c)
        cv.set(x + 1, y + 2, WIN[3])
    return cv.img


def gargoyle_sil(cv, cx, by, col):
    """Crouched winged gargoyle silhouette facing left, sitting on a post top at y=by."""
    rows = [
        "......##.........",
        ".....####........",
        "....#####....#...",
        "...######...##...",
        "..#######..###...",
        ".##.####..####...",
        "....###########..",
        "...############..",
        "...###########...",
        "....#########....",
        "....##.#####.....",
        "...###..###......",
    ]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                cv.set(cx - 8 + i, by - len(rows) + j, col)


# =========================================================================== interior (cm_interior)
IW, IH = 64, 128


DAMASK_HALF = [   # left half + centre column of a 15x32 damask motif ('#' motif, '+' silk highlight)
    ".......#",
    "......#+",
    "......#+",
    ".......#",
    "..###..#",
    ".#...#.#",
    "#..#..##",
    "#.#....#",
    ".#....#.",
    "......#.",
    ".....#.#",
    "....#..#",
    "...#.+.#",
    "..#.+#.#",
    "..#+#..#",
    ".#.#..+#",
    ".#.#.+##",
    ".#.#..+#",
    "..#+#..#",
    "..#.+#.#",
    "...#.+.#",
    "....#..#",
    ".....#.#",
    "..##..##",
    ".#..#.##",
    "#....###",
    "#.##..##",
    ".#..#..#",
    "......##",
    ".....###",
    ".......#",
    "........",
]
DAMASK_MOTIF = [row + row[-2::-1] for row in DAMASK_HALF]      # 15 wide, symmetric
SPRIG = ["..#..", ".#+#.", "#+.+#", ".#+#.", "..#.."]


def paper_px(x, y):
    """Damask: the motif in a 32x32 cell with a half-drop repeat (period 64 x 32 -> tiles 64x128), a small
    diamond sprig between motifs. 0 ground, 1 motif, 2 silk highlight."""
    x %= 64
    y %= 128
    col = x // 32
    yy = (y + (16 if col else 0)) % 32
    xx = x % 32
    mx, my = xx - 8, yy
    if 0 <= mx < 15:
        ch = DAMASK_MOTIF[my][mx]
        if ch != ".":
            return 2 if ch == "+" else 1
    # sprig at the cell's side midpoints (between motifs of the neighbouring half-dropped column)
    sx, sy = (xx + 2) % 32, (yy + 16 + 2) % 32
    if sx < 5 and sy < 5 and SPRIG[sy][sx] != ".":
        return 2 if SPRIG[sy][sx] == "+" else 1
    return 0


def paper():
    s = Spr(IW, IH)
    for y in range(IH):
        for x in range(IW):
            v = paper_px(x, y)
            c = {0: DM[2], 1: DM[3], 2: DM[4]}[v]
            if v == 0 and (x * 3 + y * 5) % 19 == 0:
                c = DM[1]                                                   # faint woven grain
            s.set(x, y, c)
    return s.img


def wainscot():
    s = Spr(IW, IH)
    y0 = IH - 48
    # chair rail: tarnished silver on top, a wood moulding under it
    for x in range(IW):
        s.set(x, y0, SV[4] if h01(x, 0, 3) > 0.15 else SV[5])
        s.set(x, y0 + 1, SV[3])
        s.set(x, y0 + 2, SV[1])
        s.set(x, y0 + 3, WD[5])
        s.set(x, y0 + 4, WD[3])
        s.set(x, y0 + 5, K)
    # panels: two raised panels per 64 (stiles at x 0..3 and 32..35), rails top/bottom
    for y in range(y0 + 6, IH):
        for x in range(IW):
            lx = x % 32
            c = WD[2]
            if (y - y0 - 6) % 7 == 3 and lx > 4:
                c = WD[2] if (x + y) % 5 else WD[1]                         # faint wood grain
            s.set(x, y, c)
    for x in range(IW):
        lx = x % 32
        if lx < 4:
            for y in range(y0 + 6, IH - 7):
                s.set(x, y, WD[3] if lx == 0 else WD[2] if lx < 3 else WD[1])
    # raised panel (bevelled): x 6..29 of each half, y y0+10 .. IH-12
    for half in (0, 32):
        x0, x1, t, b = half + 6, half + 29, y0 + 10, IH - 13
        for y in range(t, b + 1):
            for x in range(x0, x1 + 1):
                if y == t or x == x0:
                    c = WD[4]
                elif y == b or x == x1:
                    c = WD[0]
                elif y == t + 1 or x == x0 + 1:
                    c = WD[3]
                elif y == b - 1 or x == x1 - 1:
                    c = WD[1]
                else:
                    c = WD[2] if (y - t) % 6 else WD[3] if x % 3 == 0 else WD[2]
                s.set(x, y, c)
        # carved gothic blind arch inside the panel: pointed head, lit left rim, shadowed right rim
        ax0, ax1, at, ab = x0 + 5, x1 - 5, t + 4, b - 3
        acx = (ax0 + ax1 + 1) / 2
        R = (ax1 - ax0 + 1) * 0.9
        yc = at + R * 0.8
        for y in range(at, ab + 1):
            for x in range(ax0, ax1 + 1):
                inside_a = y >= yc or (math.hypot(x + .5 - (ax0 + R), y + .5 - yc) <= R and
                                       math.hypot(x + .5 - (ax1 + 1 - R), y + .5 - yc) <= R)
                if not inside_a:
                    continue
                s.set(x, y, VV[0])
        for y in range(at, ab + 1):
            for x in range(ax0, ax1 + 1):
                if s.get(x, y) != VV[0]:
                    continue
                if s.get(x - 1, y) not in (VV[0], WD[0]) or s.get(x, y - 1) not in (VV[0], WD[0]):
                    s.set(x, y, WD[0])
        for y in range(at, ab + 1):
            for x in range(ax0, ax1 + 1):
                if s.get(x, y) == VV[0]:
                    s.set(x, y, WD[1])
                    if s.get(x + 1, y) not in (VV[0], WD[0], WD[2], WD[1]) or y == ab:
                        s.set(x, y, WD[4])
        for y in range(int(yc) + 1, ab):
            s.set(int(acx), y, WD[3])                                       # a thin mullion
    # skirting
    for x in range(IW):
        s.set(x, IH - 7, WD[4])
        s.set(x, IH - 6, WD[3])
        for y in range(IH - 5, IH):
            s.set(x, y, WD[1] if y < IH - 1 else WD[0])
    return s.img


def window():
    s = Spr(IW, IH)
    x0, x1 = 12, 51                  # 40 wide
    top, bot = 20, 119               # 100 tall
    cx = (x0 + x1 + 1) / 2
    hw = (x1 - x0 + 1) / 2

    def inside(x, y, inset):
        """Inside the lancet outline shrunk by `inset` px."""
        if y > bot - inset or x < x0 + inset or x > x1 - inset:
            return False
        # pointed head: two arcs of radius R centred on the opposite side at y = top + R*0.87
        R = (x1 - x0 + 1) * 0.95
        yc = top + R * 0.87
        if y >= yc:
            return y >= top + inset
        dl = math.hypot(x + .5 - (x0 + R), y + .5 - yc)
        dr = math.hypot(x + .5 - (x1 + 1 - R), y + .5 - yc)
        return dl <= R - inset and dr <= R - inset

    # stone surround (black marble, lit upper-left) and a deep reveal
    for y in range(IH):
        for x in range(IW):
            if inside(x, y, 0) and not inside(x, y, 4):
                edge_l = not inside(x - 1, y, 0) or not inside(x, y - 1, 0)
                c = MB[3]
                if not inside(x - 1, y, 1) and x < cx:
                    c = MB[5]
                if not inside(x, y - 1, 1):
                    c = MB[5] if x < cx else MB[4]
                if not inside(x + 1, y, 1) and x > cx:
                    c = MB[1]
                if inside(x, y, 3):
                    c = MB[1] if x > cx else MB[2]                          # inner reveal in shadow
                s.set(x, y, c)
    # sill
    for x in range(x0 - 2, x1 + 3):
        s.set(x, bot + 1, MB[5] if x < cx else MB[4])
        s.set(x, bot + 2, MB[3])
        s.set(x, bot + 3, MB[1])
    # iron tracery (panes stay transparent): central mullion, two transoms, a rose in the head, cusped sub-arches
    def iron(x, y):
        s.set(x, y, IR[4] if (x + y) % 5 else IR[5])
    for y in range(46, bot - 3):
        if inside(int(cx), y, 4):
            iron(int(cx) - 1, y); s.set(int(cx), y, IR[2])
    for ty in (60, 90):
        for x in range(x0 + 4, x1 - 3):
            if inside(x, ty, 4):
                iron(x, ty)
    # leaded quarries (diamond lattice) -- thin iron lines, panes between remain transparent
    for y in range(top + 4, bot - 3):
        for x in range(x0 + 4, x1 - 3):
            if not inside(x, y, 5):
                continue
            if ((x + y) % 10 == 0 or (x - y) % 10 == 0) and y > 62:
                s.set(x, y, IR[2])
    # rose window in the head
    rcx, rcy, rr = cx - 0.5, 36, 7
    for y in range(rcy - rr - 1, rcy + rr + 2):
        for x in range(int(rcx - rr - 1), int(rcx + rr + 2)):
            d = math.hypot(x + .5 - (rcx + .5), y + .5 - rcy)
            a = math.atan2(y + .5 - rcy, x + .5 - (rcx + .5))
            foil = 3.0 + 0.9 * math.cos(a * 6)
            if abs(d - rr) < 0.8 or (abs(d - foil - 1.6) < 0.6 and d < rr - 1) or d < 1.2:
                if inside(x, y, 4):
                    iron(x, y)
    # small cusped arches under the transom at y=60 (two lights)
    for sgn in (-1, 1):
        acx = cx + sgn * 9.5 - 0.5
        for x in range(int(acx - 8), int(acx + 9)):
            yy = 60 + int(6 - math.sqrt(max(0.0, 36 - (x + .5 - acx - .5) ** 2 * 0.56)))
            if inside(x, yy, 4) and abs(x + .5 - acx - .5) < 8:
                iron(x, yy)
    # curtains: crimson velvet hanging from a rod, tied back at y ~ 72 with silver cords, pooling on the floor
    for x in range(x0 - 7, x1 + 8):
        s.set(x, 13, SV[4] if x > 6 else SV[3])
        s.set(x, 14, IR[2])
    s.set(x0 - 8, 13, SV[5]); s.set(x1 + 8, 13, SV[3])
    for side in (-1, 1):
        for y in range(15, IH - 2):
            # curtain half-width profile: full at top, pinched at the tie (y=74), billowing below
            if y < 74:
                t = (y - 15) / 59
                wdt = 13 - 8 * t ** 1.4
            else:
                t = (y - 74) / (IH - 76)
                wdt = 5 + 6 * math.sin(min(1.0, t * 1.3) * math.pi / 2)
            if side < 0:
                xa, xb = x0 - 7, x0 - 7 + wdt
            else:
                xa, xb = x1 + 8 - wdt, x1 + 8
            for x in range(int(xa), int(math.ceil(xb))):
                u = (x - xa) / max(1.0, xb - xa)
                fold = math.sin((u * 3.2 + (0.2 if side > 0 else 0)) * math.pi)
                v = 0.45 + 0.35 * fold
                if side > 0:
                    v -= 0.08
                if y < 20:
                    v += 0.1
                c = VV[int(clamp(v) * (len(VV) - 1) + 0.5)]
                if x == int(xa) and side < 0:
                    c = VV[5]
                s.set(x, y, c)
        # tie-back cord + tassel
        tx0 = x0 - 7 if side < 0 else x1 + 8 - 6
        for x in range(tx0, tx0 + 7):
            s.set(x, 74, SV[4] if x % 2 else SV[3])
        tx = x0 - 1 if side < 0 else x1 + 1
        for (dx, dy, c) in ((0, 1, SV[4]), (0, 2, GL[4]), (-1, 3, GL[3]), (0, 3, GL[5]), (1, 3, GL[2]), (0, 4, GL[3])):
            s.set(tx + dx, 74 + dy, c)
    pre = s.img.copy()
    s.outline()
    # the glazing stays exactly as drawn: panes fully transparent, no outline creeping into them
    pp, op = pre.load(), s.img.load()
    for y in range(IH):
        for x in range(IW):
            if inside(x, y, 4):
                op[x, y] = pp[x, y]
    return s.img


def window_glazing():
    """L-mode mask (255 = glass pane) of the window frame: the transparent pixels inside the lancet. The engine must not
    draw `paper` there, so the sky parallax shows through the panes."""
    img = window()
    a = img.getchannel("A").load()
    m = Image.new("L", (IW, IH), 0)
    mp = m.load()
    for y in range(IH):
        xs = [x for x in range(IW) if a[x, y]]
        if not xs:
            continue
        for x in range(12, 52):
            if a[x, y] == 0 and any(a[xx, y] for xx in range(12, x)) and any(a[xx, y] for xx in range(x + 1, 52)) \
                    and 20 <= y <= 119:
                mp[x, y] = 255
    return m


def pilaster():
    s = Spr(IW, IH)
    x0, x1 = 24, 39
    for y in range(IH):
        for x in range(x0, x1 + 1):
            lx = x - x0
            c = MB[2]
            if lx == 0:
                c = MB[4]
            elif lx == 1:
                c = MB[3]
            elif lx == 15:
                c = MB[0]
            elif lx == 14:
                c = MB[1]
            elif lx in (4, 8, 12):
                c = MB[1]                                                   # fluting shadow
            elif lx in (3, 7, 11):
                c = MB[3]                                                   # fluting lit edge
            if (y * 3 + lx * 7) % 61 == 0 and 1 < lx < 14 and lx not in (3, 4, 7, 8, 11, 12):
                c = MB[4]                                                   # faint marble vein
            s.set(x, y, c)
    # capital (silver) at y 8..19
    def band(y, xa, xb, cl, cm, cd):
        for x in range(xa, xb + 1):
            s.set(x, y, cl if x < xa + 2 else cd if x > xb - 2 else cm)
    band(6, 21, 42, MB[4], MB[3], MB[1])
    band(7, 21, 42, MB[3], MB[2], MB[0])
    CAP = [
        "####################",
        "####################",
        ".##..............##.",
        "#..#....####....#..#",
        "#.##...#.##.#...##.#",
        ".##...#.####.#...##.",
        "..#..#.######.#..#..",
        "...#.##.####.##.#...",
        "....############....",
        "..################..",
        "..################..",
    ]
    for j, row in enumerate(CAP):
        for i, ch in enumerate(row):
            x, y = 22 + i, 8 + j
            if ch == "#":
                u = i / 19
                c = SV[5] if u < 0.2 else SV[4] if u < 0.55 else SV[3] if u < 0.85 else SV[2]
                if j in (1, 10):
                    c = SV[2] if u > 0.3 else SV[3]
                s.set(x, y, c)
            elif 24 <= x <= 39:
                s.set(x, y, MB[1])
            elif j > 0:
                s.set(x, y, T)
    band(19, 24, 39, K, K, K)
    # plinth y 112..127
    band(110, 23, 40, SV[4], SV[3], SV[1])
    band(111, 23, 40, SV[2], SV[2], SV[1])
    for y in range(112, IH):
        for x in range(22, 42):
            lx = x - 22
            c = MB[3] if lx < 2 else MB[0] if lx > 17 else MB[2]
            if y == 112:
                c = MB[4] if lx < 18 else MB[1]
            if y in (118, 119):
                c = MB[4] if y == 118 else MB[1]
            s.set(x, y, c)
    for y in range(IH):
        for x in (x0 - 1, x1 + 1):
            if s.get(x, y)[3] == 0:
                s.set(x, y, K)
    s.outline()
    return s.img


def build_interior():
    ims = [paper(), wainscot(), window(), pilaster()]
    frames = [{"ms": 1000, "cels": {"Interior": im}} for im in ims]
    tags = [("paper", 0, 0), ("wainscot", 1, 1), ("window", 2, 2), ("pilaster", 3, 3)]
    return IW, IH, ["Interior"], frames, tags
