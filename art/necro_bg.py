"""Parallax for the `necropolis` biome.

bg_necropolis_far  512x216 opaque, tileable: a blue-black abyss; the vertical city of the dead in three depth planes --
                   needle spires of stacked bone, cathedral towers with pale ghost-lit windows, a great bell hanging in
                   the far dark, cold haze bands rising from below.
bg_necropolis_mid  512x216 transparent, tileable: an ossuary colonnade -- arches lined with skulls, hanging chains and
                   small bells, silhouettes only (dark, low contrast), lower 2/3.
"""
import math
from PIL import Image
from envlib import Canvas, ramp, h01, fbm, pick, clamp, lerpc, C

W, H = 512, 216
SKY = ramp("04050a", "070910", "0b0f1c", "111829", "18223b", "20304f", "2a3f64")
P3 = ramp("121a30", "162038", "1b2742")        # farthest city plane
P2 = ramp("0c1122", "0f152a", "141c36")
P1 = ramp("06070d", "080a12", "0c0f1c")
WIN = ramp("1e3a6a", "3a70c0", "7fb4ee", "cfe6ff")
MID = ramp("04040a", "07070e", "0b0b15", "11121e", "191a2a")


def spire(cv, x0, base, w, h, col, seed, windows=True, bells=False):
    """A bone needle-spire: tapering tower with ribs, a pointed cap, optional lit slits."""
    for y in range(int(base - h), int(base) + 1):
        t = min(1.0, max(0.0, (base - y) / h))
        half = w * (1 - t) ** 0.7 * 0.5 + 0.5
        if t > 0.86:
            half = max(0.5, half * (1 - (t - 0.86) / 0.14))
        for x in range(int(x0 - half), int(x0 + half) + 1):
            cv.set(x, y, col)
        if int((base - y)) % 11 == 0 and t < 0.8:          # ribs / balconies
            for x in range(int(x0 - half - 1), int(x0 + half) + 2):
                cv.set(x, y, col)
    if windows:
        for k in range(int(h / 14)):
            y = base - 8 - k * 14 - int(h01(seed, k, 3) * 4)
            if h01(seed, k, 5) < 0.55 and y > base - h * 0.8:
                c = WIN[1] if h01(seed, k, 7) < 0.7 else WIN[2]
                cv.set(x0, y, c); cv.set(x0, y + 1, c)
                if h01(seed, k, 9) < 0.3:
                    cv.set(x0, y - 1, WIN[0])


def cathedral(cv, x0, base, w, h, col, seed):
    """A cathedral block with two towers and a rose window of ghost-fire."""
    for y in range(int(base - h * 0.55), int(base) + 1):
        for x in range(int(x0 - w / 2), int(x0 + w / 2) + 1):
            cv.set(x, y, col)
    for sx in (-1, 1):
        spire(cv, x0 + sx * w * 0.38, base, w * 0.3, h, col, seed + sx, windows=True)
    spire(cv, x0, base - h * 0.5, w * 0.35, h * 0.35, col, seed + 5, windows=False)
    # rose window
    cy, r = base - h * 0.36, max(2.0, w * 0.12)
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(x0 - r) - 1, int(x0 + r) + 2):
            d = math.hypot(x + .5 - x0, y + .5 - cy)
            if d <= r:
                spoke = abs(math.sin(math.atan2(y + .5 - cy, x + .5 - x0) * 4)) < 0.35
                cv.set(x, y, WIN[2] if d < r * 0.35 else WIN[1] if spoke or d > r - 0.8 else WIN[0])


def far():
    cv = Canvas(W, H, wrap=True)
    for y in range(H):
        for x in range(W):
            v = 0.08 + 0.85 * (y / H) ** 1.8 + (fbm(x, y, 64, 40, 3) - 0.5) * 0.25
            cv.set(x, y, pick(SKY, v, x, y))
    # distant great bell hanging in the dark (one per tile)
    bx, by = 380, 30
    for y in range(0, by):
        cv.set(bx, y, P3[1])
    for y in range(by, by + 34):
        t = (y - by) / 34
        half = 5 + 13 * t ** 1.6
        for x in range(int(bx - half), int(bx + half) + 1):
            cv.set(x, y, P3[2] if x < bx - half * 0.3 else P3[1])
    for x in range(bx - 19, bx + 20):
        cv.set(x, by + 34, P3[2])
    # plane 3 (farthest): many thin spires
    for i in range(14):
        x0 = i * 37 + int(h01(i, 1, 11) * 20)
        spire(cv, x0, H - 30, 7 + h01(i, 2, 11) * 8, 70 + h01(i, 3, 11) * 70, P3[0], i + 100)
    for x in range(W):
        for y in range(H - 34, H):
            cv.set(x, y, P3[0])
    # haze band
    for y in range(H - 60, H - 20):
        for x in range(W):
            k = 1 - abs(y - (H - 40)) / 20
            if k > 0 and h01(x, y, 17) < 0.35 * k:
                cv.set(x, y, lerpc(cv.get(x, y), C("20305a"), 0.35 * k))
    # plane 2: cathedrals and big spires
    for i, (x0, w, h) in enumerate(((60, 46, 120), (200, 22, 150), (300, 58, 110), (450, 26, 160))):
        if i % 2 == 0:
            cathedral(cv, x0, H - 12, w, h, P2[1], i + 200)
        else:
            spire(cv, x0, H - 12, w, h, P2[1], i + 200)
    for x in range(W):
        for y in range(H - 14, H):
            cv.set(x, y, P2[0])
    # plane 1 (nearest far): stepped rooftops of the city of the dead
    x = 0
    k = 0
    while x < W:
        w = 18 + int(h01(k, 5, 21) * 30)
        h = 18 + int(h01(k, 6, 21) * 26)
        for xx in range(x, x + w):
            roof = h + (w / 2 - abs(xx - x - w / 2)) * 0.6
            for y in range(int(H - roof), H):
                cv.set(xx, y, P1[1] if xx - x > 2 else P1[2])
        if h01(k, 8, 21) < 0.6:
            wx, wy = x + w // 2, int(H - h * 0.6)
            cv.set(wx, wy, WIN[0]); cv.set(wx, wy + 1, WIN[0])
        x += w
        k += 1
    # drifting ghost motes (static, sparse)
    for i in range(18):
        mx, my = int(h01(i, 1, 31) * W), int(h01(i, 2, 31) * (H - 60))
        cv.set(mx, my, WIN[1] if i % 3 else WIN[2])
    img = cv.img
    return img


def mid():
    cv = Canvas(W, H, wrap=True)
    base = H
    # colonnade: 4 bays per tile, each an arch with a skull-lined intrados
    bay = 128
    for b in range(4):
        x0 = b * bay
        # piers
        for x in range(x0, x0 + 18):
            for y in range(70, base):
                c = MID[3] if x - x0 in (2, 3) else MID[2] if x - x0 < 15 else MID[1]
                cv.set(x, y, c)
        # capital + arch
        for x in range(x0 - 2, x0 + 20):
            cv.set(x, 70, MID[4]); cv.set(x, 71, MID[3])
        cx, top = x0 + 18 + (bay - 18) / 2, 70
        rx, ry = (bay - 18) / 2, 44
        for x in range(x0 + 18, x0 + bay):
            dx = (x + .5 - cx) / rx
            if abs(dx) > 1:
                continue
            ay = top - ry * math.sqrt(1 - dx * dx) + ry
            for y in range(0, int(ay) + 1):
                if y >= ay - 7:
                    cv.set(x, y, MID[3] if y >= ay - 2 else MID[2])
                elif y < 30:
                    cv.set(x, y, MID[1])
            # skulls along the intrados
            if int(x - x0) % 7 == 3:
                yy = int(ay) - 4
                for (dx2, dy2, c) in ((0, 0, MID[4]), (1, 0, MID[4]), (-1, 0, MID[3]), (0, -1, MID[4]), (0, 1, MID[1])):
                    cv.set(x + dx2, yy + dy2, c)
        for x in range(x0, x0 + bay):
            for y in range(0, 30):
                if cv.get(x, y)[3] == 0:
                    cv.set(x, y, MID[1])
        # hanging chain + small bell in each bay
        hx = int(cx + (h01(b, 1, 41) - 0.5) * 30)
        hl = 40 + int(h01(b, 2, 41) * 50)
        for y in range(30, 30 + hl):
            cv.set(hx, y, MID[3] if y % 3 else MID[2])
        if b % 2 == 0:
            for y in range(30 + hl, 30 + hl + 12):
                t = (y - 30 - hl) / 12
                half = 2 + 5 * t ** 1.5
                for x in range(int(hx - half), int(hx + half) + 1):
                    cv.set(x, y, MID[3] if x < hx else MID[2])
        # low balustrade of stacked bones between piers
        for x in range(x0 + 18, x0 + bay):
            for y in range(base - 26, base):
                if y == base - 26 or y == base - 25:
                    cv.set(x, y, MID[3])
                elif (x - x0) % 6 == 0:
                    cv.set(x, y, MID[2])
    return cv.img


BUILDERS = {"necropolis": (far, mid)}
