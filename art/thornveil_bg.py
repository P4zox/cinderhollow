"""Thornveil Wood parallax: bg_thornveil_far (512x216 opaque) and bg_thornveil_mid (512x216 transparent), tileable in x."""
import math
from PIL import Image
from thornveil_kit import C, h01, bt, clamp, K
from envlib import fbm, lerpc

W, H = 512, 216


def dith(c0, c1, t, x, y):
    return c1 if t > bt(x, y) else c0


def far():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    px = img.load()
    top, mid, low = C("#040908"), C("#1a2d29"), C("#0a1311")
    # --- canopy-dark sky to a fog-lit band, then ground fog
    for y in range(H):
        for x in range(W):
            t = y / H
            n = fbm(x, y, 64, 32, 3, W, 3)
            if t < 0.62:
                k = (t / 0.62) ** 1.6 + (n - 0.5) * 0.08
                c = lerpc(top, mid, clamp(k))
            else:
                k = (t - 0.62) / 0.38 + (n - 0.5) * 0.2
                c = lerpc(mid, low, clamp(k))
            px[x, y] = c
    # --- far trunks, three depth layers (each nearer layer darker and wider, hazed by fog)
    layers = [(9, 5, 9, C("#243833"), 0.0), (7, 8, 14, C("#172622"), 1.0), (5, 12, 20, C("#0d1714"), 2.0)]
    for li, (n, w0, w1, col, seed) in enumerate(layers):
        for i in range(n):
            cx = (i + 0.35 * h01(i, li, 3)) * W / n + li * 23
            w = w0 + (w1 - w0) * h01(i, li, 4)
            lean = (h01(i, li, 5) - 0.5) * 0.08
            for y in range(H):
                sway = math.sin(y * 0.02 + i) * 2 + lean * (H - y)
                ww = w * (1 + 0.5 * max(0, (y - H * 0.78) / (H * 0.22)) ** 2)   # root flare at the base
                for dx in range(-int(ww) - 1, int(ww) + 2):
                    if abs(dx) <= ww / 2:
                        x = int(cx + sway + dx) % W
                        c = col
                        # a faint lit left edge
                        if dx < -ww / 2 + 1.5 and li < 2:
                            c = lerpc(col, C("#3a524a"), 0.35)
                        px[x, y] = dith(px[x, y], c, 0.35 + 0.3 * li + 0.25 * (1 - y / H), x, y) if li == 0 else c
            # hanging moss beards from branch stubs
            for b in range(2):
                by = int(30 + h01(i, b, li + 7) * 90)
                bx = int(cx + (1 if b else -1) * (w / 2 + 2))
                L = int(10 + h01(i, b, 9) * 22)
                for yy in range(L):
                    for xx in range(-1, 2 + (L - yy) // 8):
                        if h01(bx + xx, by + yy, 3) < 0.55 - yy / L * 0.4:
                            px[(bx + xx) % W, min(H - 1, by + yy)] = col
    # --- god rays from the upper left, pale spirit-green (dithered)
    for r in range(4):
        x0 = 40 + r * 131
        wd = 16 + r * 5
        for y in range(H):
            for dx in range(wd):
                x = int(x0 + dx + y * 0.55) % W
                a = 0.10 * (1 - y / H) * math.sin(dx / wd * math.pi)
                if a > 0.05 + bt(x, y) * 0.12:
                    px[x, y] = lerpc(px[x, y], C("#6f9a88"), 0.22)
    # --- low fog drifting over the ground
    for y in range(int(H * 0.72), H):
        for x in range(W):
            n = fbm(x, y, 32, 8, 11, W, 3)
            a = clamp((n - 0.35) * 1.6) * (0.55 - abs(y - H * 0.86) / H)
            if a > bt(x, y):
                px[x, y] = lerpc(px[x, y], C("#324a44"), 0.5)
    return img


def mid():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    BK = [C(h) for h in ("#070b0a", "#0c1311", "#121c18", "#19261f", "#223328")]
    MS = [C(h) for h in ("#10231a", "#183423", "#22462c")]
    RB = [C(h) for h in ("#6c6960", "#8f8a7c", "#b3ad9c")]

    def put(x, y, c):
        if 0 <= y < H:
            px[int(x) % W, int(y)] = c
    trunks = [(70, 38), (262, 50), (430, 30)]
    for ti, (cx, w) in enumerate(trunks):
        for y in range(H):
            flare = max(0, (y - H * 0.7) / (H * 0.3))
            ww = w * (1 + 0.9 * flare ** 2)
            sway = math.sin(y * 0.018 + ti * 2) * 3
            for dx in range(-int(ww), int(ww) + 1):
                if abs(dx) > ww / 2:
                    continue
                x = cx + sway + dx
                u = (dx + ww / 2) / ww            # 0 = left (lit) .. 1 = right
                grain = 0.5 + 0.5 * math.sin((dx * 0.9 + fbm(x, y, 32, 16, ti, W, 2) * 12))
                v = 0.62 - 0.55 * u + 0.18 * (grain - 0.5)
                c = BK[max(0, min(4, int(v * 5)))]
                put(x, y, c)
            # moss on the lit side
            if y < H * 0.8 and fbm(cx, y, 16, 8, 30 + ti, W, 2) > 0.45:
                for k in range(3):
                    put(cx + sway - ww / 2 + k, y, MS[2 - k] if k < 3 else MS[0])
        # roots at the base spreading out
        for r in range(5):
            side = -1 if r % 2 else 1
            L = 20 + h01(ti, r, 3) * 30
            for i in range(int(L)):
                t = i / L
                x = cx + side * (w * 0.4 + i)
                y = H - 26 + t * t * 26 - (r // 2) * 3 + math.sin(i * 0.3) * 1.5
                th = max(1, int(4 * (1 - t)))
                for k in range(th):
                    put(x, y + k, BK[2] if k == 0 else BK[1])
        # branches with moss beards and pale ribbons
        for b in range(3):
            side = -1 if (b + ti) % 2 else 1
            by = 20 + b * 38 + h01(ti, b, 7) * 12
            L = 30 + h01(ti, b, 8) * 40
            for i in range(int(L)):
                t = i / L
                x = cx + side * (w / 2 + i)
                y = by - t * 14 + math.sin(t * 5) * 3
                th = max(1, int(4 * (1 - t)))
                for k in range(th):
                    put(x, y + k, BK[3] if k == 0 else BK[1])
                if t > 0.15 and h01(ti * 97 + b, i, 21) < 0.16:          # moss beard clumps
                    ml = int(5 + h01(ti, b * 50 + i, 2) ** 2 * 26)
                    for yy in range(ml):
                        wdt = max(1, int(3 * (1 - yy / ml)))
                        for xx in range(wdt):
                            if h01(int(x) + xx, int(y) + yy, 5) < 0.85 - yy / ml * 0.4:
                                put(x + xx + int(math.sin(yy * 0.3) ), y + th + yy, MS[1] if yy < ml * 0.5 else MS[0])
            if b == 1:                                # a pale ribbon tied to the branch, hanging and curling
                rx = cx + side * (w / 2 + L * 0.55)
                ry = by - 8
                for yy in range(34):
                    x = rx + math.sin(yy * 0.25 + ti) * 3
                    c = RB[2] if yy < 8 else RB[1] if yy < 22 else RB[0]
                    put(x, ry + yy, c); put(x + 1, ry + yy, RB[0] if yy % 5 else c)
    return img
