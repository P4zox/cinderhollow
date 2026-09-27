#!/usr/bin/env python3
"""Agent SC props + charm icons (Expansion 3) -> assets xsc_s (32x32), xsc_m (64x64), xsc_l (128x128), xsc_icons (16x16).
Every sprite is anchored bottom-centre (drawSprite {bottom:true}) unless noted in 55_sc.js.
Re-runnable: python3 art/gen_xsc.py [--preview-only]   (preview -> art/previews/xsc_props.png)"""
import math, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from envlib import C, K, T, h01, clamp, blank, outline, pick, bt, vnoise, lerpc, scale  # noqa: E402
from xsc_lib import *  # noqa: E402,F401


# ============================================================================ small props (32x32)
def glassgrass(seed):
    img = blank(32, 32)
    blades = [(-6, 7, -0.3), (-3, 11, -0.1), (0, 14, 0.05), (3, 9, 0.25), (6, 6, 0.4), (-8, 4, -0.5)] if seed == 0 else \
             [(-5, 9, -0.2), (-1, 6, -0.4), (2, 12, 0.1), (5, 8, 0.3), (8, 5, 0.5)]
    for dx, h, lean in blades:
        for i in range(h):
            x = 16 + dx + lean * i
            v = 0.3 + 0.6 * i / h
            put(img, x, 31 - i, pick(GL, v, x, i))
            if i < h * 0.6: put(img, x + 1, 31 - i, pick(GL, v - 0.3, x, i))
        put(img, 16 + dx + lean * h, 31 - h, GL[7])
    return outline(img)


def hgrass(seed):
    img = blank(32, 32)
    G = ramp("1e2414", "34402a", "4e5c36", "6e7a44", "96985a", "bcb070")
    for i in range(11):
        dx = -9 + i * 1.8 + (h01(i, seed) - 0.5) * 2
        h = 3 + int(h01(i, seed + 3) * (7 if seed == 0 else 5))
        lean = (h01(i, seed + 7) - 0.5) * 0.9
        for k in range(h):
            put(img, 16 + dx + lean * k, 31 - k, pick(G, 0.25 + 0.7 * k / h, i, k))
    return img


def meteor(stage):
    """a cooled meteor lying flat, 32 wide; its walkable top at row 20. stage 0 fresh, 1 cracking, 2 breaking"""
    img = blank(32, 32)
    top = 20
    pts = [(1, top + 3), (4, top), (11, top - 1), (21, top - 1), (28, top), (31, top + 3), (30, top + 8), (24, top + 11), (8, top + 11), (2, top + 8)]
    for (x, y) in poly_pts(pts):
        v = 0.55 - 0.45 * (y - top) / 11 + 0.08 * (vnoise(x, y, 3, 3, 5) - 0.5)
        put(img, x, y, pick(OB, v, x, y))
    for x in range(4, 28):   # the flat glassy top, lit
        put(img, x, top - 1 if 11 <= x <= 21 else top, GL[5] if (x + stage) % 5 else GL[6])
    veins = [[(6, top + 3), (10, top + 6), (15, top + 5), (19, top + 8)], [(22, top + 2), (24, top + 6), (27, top + 7)], [(12, top + 1), (13, top + 4)]]
    if stage >= 1: veins += [[(15, top + 5), (16, top + 9), (14, top + 11)], [(24, top + 6), (21, top + 10)], [(4, top + 5), (7, top + 8)]]
    for v in veins:
        for a, b in zip(v, v[1:]):
            line(img, a, b, STAR[3] if stage < 2 else STAR[4])
        put(img, v[0][0], v[0][1], VIOLET[4])
    img = outline(img)
    if stage == 2:   # split in two: a dark seam through the middle, chips falling away
        for y in range(top - 1, top + 12):
            put(img, 16 + (y % 2), y, T)
        for (x, y) in ((3, top + 11), (29, top + 10), (10, top + 12)):
            put(img, x, y + 1, OB[4])
    return img


def emberrock():
    img = blank(32, 32)
    ell(img, 16, 28, 9, 6, lambda nx, ny, x, y: pick(OB, 0.6 - 0.4 * ny - 0.3 * nx, x, y) if ny < 0.6 else None)
    for a, b in (((11, 27), (15, 29)), ((15, 29), (19, 26)), ((19, 26), (22, 28))):
        line(img, a, b, VIOLET[3])
    put(img, 15, 29, STAR[4]); put(img, 12, 25, GL[6])
    return outline(img)


def wayshrine():
    img = blank(32, 32)
    shade_box(img, 13, 12, 18, 31, PALESTONE, 0.45, 0.2, seed=2)     # the post
    shade_box(img, 10, 29, 21, 31, PALESTONE, 0.35, 0.1, seed=3)     # its foot
    rect(img, 11, 10, 20, 11, lambda x, y: pick(PALESTONE, 0.65 - 0.03 * (x - 11), x, y))   # cap
    for x in (12, 19):                                                 # the lamp cage
        line(img, (x, 3), (x, 9), BRASS[3])
    line(img, (12, 3), (19, 3), BRASS[4]); line(img, (13, 2), (18, 2), BRASS[5])
    ell(img, 15.5, 6.5, 2.6, 2.8, lambda nx, ny, x, y: STAR[4] if nx * nx + ny * ny < 0.3 else STAR[3])
    for (x, y) in ((14, 20), (15, 23), (16, 19), (14, 26)):          # etched star-marks, pilgrims' tallies
        put(img, x, y, GL[4])
    return outline(img)


def wellshard(f):
    img = blank(32, 32)
    cx, cy = 16, 20
    pts = [(cx, cy - 11), (cx + 4, cy - 2), (cx + 1, cy + 10), (cx - 4, cy + 1)]
    facet(img, [pts[0], pts[1], (cx, cy)], GL, 0.75, 1)
    facet(img, [pts[1], pts[2], (cx, cy)], GL, 0.35, 2)
    facet(img, [pts[2], pts[3], (cx, cy)], GL, 0.2, 3)
    facet(img, [pts[3], pts[0], (cx, cy)], GL, 0.9, 4)
    core = 0.5 + 0.5 * math.sin(f / 4 * math.tau)
    for i in range(-5, 6):
        put(img, cx - 0.3 * i * 0.2, cy + i, STAR[2 + int(core * 2)] if abs(i) < 4 else STAR[2])
    img = outline(img)
    for k in range(3):                                   # motes spiralling in
        a = f / 4 * math.tau + k * math.tau / 3
        put(img, cx + math.cos(a) * 12, cy + math.sin(a) * 6, STAR[3] if k == 0 else STAR[2])
    return img


def ashpile(seed):
    img = blank(32, 32)
    w = 12 if seed == 0 else 9
    for x in range(16 - w, 16 + w + 1):
        t = (x - 16) / w
        h = int((1 - t * t) * (7 if seed == 0 else 5) + h01(x, seed) * 1.5)
        for k in range(h):
            v = 0.35 + 0.4 * k / max(1, h) - 0.15 * t
            put(img, x, 31 - k, pick(ASH, v, x, k))
    for (x, y) in ((12, 29), (19, 30), (16, 27)) if seed == 0 else ((14, 30), (18, 29)):
        put(img, x, y, FIRE[4])
    return outline(img)


def dumpster():
    img = blank(32, 32)
    D = ramp("0a100c", "12201a", "1c3026", "284434", "386044")
    shade_box(img, 4, 18, 27, 31, D, 0.5, 0.3, seed=4)
    rect(img, 3, 16, 28, 17, lambda x, y: pick(D, 0.8 if y == 16 else 0.45, x, y))   # lid
    for x in range(6, 26, 5): line(img, (x, 19), (x, 30), D[1])
    rect(img, 9, 22, 14, 25, MG[3]); rect(img, 10, 23, 13, 24, MG[5])                   # a sticker, neon
    rect(img, 18, 26, 22, 28, CY[2])
    return outline(img)


def lantern():
    img = blank(32, 32)
    line(img, (16, 12), (16, 31), WOOD[3]); line(img, (17, 13), (17, 31), WOOD[1])       # the stake
    line(img, (16, 12), (21, 10), WOOD[3])
    ell(img, 21, 17, 3.5, 5, lambda nx, ny, x, y: pick(PAPER, 0.9 - 0.4 * (nx + 1) / 2 - 0.2 * abs(ny), x, y))
    for y in (13, 17, 21): line(img, (18, y), (24, y), PAPER[1])
    rect(img, 19, 11, 23, 11, WOOD[2]); rect(img, 19, 22, 23, 22, WOOD[2])
    return outline(img)


def jars():
    img = blank(32, 32)
    for cx, h, w in ((8, 12, 5), (16, 16, 6), (24, 10, 4)):
        ell(img, cx, 31 - h / 2, w, h / 2, lambda nx, ny, x, y: pick(CLAY, 0.7 - 0.45 * (nx + 1) / 2 - 0.15 * ny, x, y))
        rect(img, cx - 2, 31 - h - 1, cx + 2, 31 - h, CLAY[5])
        line(img, (cx - w + 1, 31 - h * 0.6), (cx + w - 1, 31 - h * 0.6), CLAY[1])
    return outline(img)


def rug():
    img = blank(32, 32)
    R = ramp("3a1210", "6e2a24", "9a3c2c", "c86a3a", "e8b070")
    for x in range(1, 31):
        for y in (29, 30, 31):
            k = (x // 3 + y) % 4
            put(img, x, y, R[[1, 2, 1, 3][k]] if 3 < x < 28 else R[4] if (x + y) % 2 else R[0])
    return img


def embershelf():
    img = blank(32, 32)
    shade_box(img, 6, 20, 25, 31, STONE, 0.4, 0.2, seed=6)
    rect(img, 4, 18, 27, 19, lambda x, y: pick(STONE, 0.7 if y == 18 else 0.45, x, y))
    ell(img, 16, 16, 5, 2.5, lambda nx, ny, x, y: pick(CLAY, 0.6 - 0.3 * nx, x, y))
    for (x, y) in ((14, 15), (16, 14), (18, 15), (15, 15), (17, 15)):
        put(img, x, y, FIRE[5] if (x + y) % 2 else FIRE[3])
    return outline(img)


def hangingpots():
    """hangs from the top of the frame (the cell top is frame row 2)"""
    img = blank(32, 32)
    rect(img, 1, 2, 30, 3, lambda x, y: pick(WOOD, 0.6 if y == 2 else 0.35, x, y))
    for cx, L, r in ((8, 8, 3.5), (17, 13, 4.5), (25, 6, 3)):
        line(img, (cx, 4), (cx, 4 + L), STEEL[3])
        ell(img, cx, 5 + L + r, r, r, lambda nx, ny, x, y: pick(STEEL if cx == 17 else CLAY, 0.65 - 0.4 * (nx + 1) / 2 - 0.2 * ny, x, y) if ny > -0.7 else None)
    return outline(img)


def firewood():
    img = blank(32, 32)
    for i, (cx, cy) in enumerate(((10, 28), (17, 28), (24, 28), (13, 24), (20, 24), (16, 20))):
        ell(img, cx, cy, 3.5, 3.5, lambda nx, ny, x, y: pick(WOOD, 0.75 - 0.35 * (nx * nx + ny * ny), x, y))
        put(img, cx, cy, WOOD[1]); put(img, cx - 1, cy - 1, WOOD[6])
    return outline(img)


def stonelantern():
    img = blank(32, 32)
    shade_box(img, 13, 22, 18, 31, STONE, 0.45, 0.2, seed=7)
    rect(img, 10, 20, 21, 21, lambda x, y: pick(STONE, 0.7 if y == 20 else 0.45, x, y))
    shade_box(img, 11, 12, 20, 19, STONE, 0.5, 0.2, seed=8)
    rect(img, 13, 14, 18, 17, lambda x, y: AMB[4] if (x + y) % 3 else AMB[3])                 # the light window
    poly(img, [(8, 12), (15.5, 6), (23, 12)], lambda x, y: pick(STONE, 0.65 - 0.25 * (x - 8) / 15, x, y))
    put(img, 15, 5, STONE[5]); put(img, 16, 5, STONE[4])
    return outline(img)


def herbs():
    img = blank(32, 32)
    rect(img, 1, 29, 30, 31, lambda x, y: pick(WOOD, 0.45 if y == 29 else 0.25, x, y))           # the bed's timber edge
    rect(img, 2, 28, 29, 28, CLAY[2])
    H = [ramp("1e2c16", "2e4a22", "4a6e30", "6e9a42", "a6c86a"), ramp("26241a", "444230", "6a6a44", "9a9a5e", "c8c486"),
         ramp("2a1a26", "4a2e44", "6e4a6a", "9e70a0", "d0a8d8")]
    for i in range(9):
        cx = 3 + i * 3.2 + h01(i, 3); P = H[i % 3]; h = 5 + int(h01(i, 5) * 6)
        for k in range(h):
            for d in (-1, 0, 1):
                if abs(d) < 1 + (h - k) / h * 1.5 and h01(i * 7 + d, k) > 0.25:
                    put(img, cx + d + (k % 3 == 0) * (1 if i % 2 else -1), 27 - k, pick(P, 0.3 + 0.6 * k / h, i, k))
        if i % 3 == 2: put(img, cx, 27 - h, H[2][4])
    return outline(img)


# ============================================================================ medium props (64x64)
def vending(f):
    img = blank(64, 64)
    x0, x1, y0 = 23, 41, 30
    shade_box(img, x0, y0, x1, 63, NV, 0.45, 0.2, seed=9)
    rect(img, x0 + 2, y0 + 3, x1 - 2, y0 + 18, CY[1])               # the lit front
    for r in range(4):
        for c in range(4):
            col = [MG[3], CY[3], AMB[3], MG[4]][(r + c) % 4]
            rect(img, x0 + 3 + c * 4, y0 + 4 + r * 4, x0 + 5 + c * 4, y0 + 6 + r * 4, col)
    if f == 1: rect(img, x0 + 3, y0 + 8, x1 - 3, y0 + 9, CY[0])      # a flickering row
    rect(img, x0 + 2, y0 + 21, x1 - 7, y0 + 25, NV[0]); rect(img, x1 - 5, y0 + 21, x1 - 3, y0 + 26, NV[5])
    rect(img, x0 + 2, y0 + 1, x1 - 2, y0 + 1, MG[3] if f == 0 else MG[4])
    img = outline(img)
    return img


def watertower():
    img = blank(64, 64)
    for lx in (18, 44):
        line(img, (lx, 40), (lx - 2, 63), STEEL[3]); line(img, (lx + 1, 40), (lx - 1, 63), STEEL[1])
    line(img, (18, 50), (44, 58), STEEL[2]); line(img, (44, 50), (18, 58), STEEL[2])
    for y in range(14, 41):
        for x in range(14, 50):
            v = 0.62 - 0.4 * (x - 14) / 36 + (0.1 if (x - 14) % 6 == 0 else 0)
            put(img, x, y, pick(RUST, v, x, y))
    for y in (18, 28, 38): line(img, (14, y), (49, y), RUST[1])
    poly(img, [(11, 14), (32, 3), (53, 14)], lambda x, y: pick(RUST, 0.5 - 0.3 * (x - 11) / 42, x, y))
    rect(img, 20, 22, 36, 26, NV[1]); rect(img, 21, 23, 35, 25, MG[3])            # a neon tag across the tank
    return outline(img)


def deadshrine(n):
    img = blank(64, 64)
    cx = 32
    shade_box(img, cx - 13, 58, cx + 13, 63, STONE, 0.35, 0.1, seed=10)          # plinth
    shade_box(img, cx - 9, 36, cx + 9, 57, STONE, 0.4, 0.2, seed=11)             # the shrine body
    rect(img, cx - 5, 42, cx + 5, 52, CHAR[1])                                     # the fire niche
    for x in range(cx - 5, cx + 6):
        put(img, x, 52, ASH[4] if x % 2 else ASH[5])
    if n == 0:
        for (x, y) in ((cx - 2, 51), (cx, 50), (cx + 2, 51), (cx - 1, 51), (cx + 1, 51), (cx, 49)):
            put(img, x, y, FIRE[5] if y < 51 else FIRE[3])
    elif n == 1:
        for (x, y) in ((cx - 1, 51), (cx + 2, 51)): put(img, x, y, FIRE[2])
    if n < 3:
        poly(img, [(cx - 14, 36), (cx, 26), (cx + 14, 36)], lambda x, y: pick(STONE, 0.6 - 0.35 * (x - cx + 14) / 28, x, y))
        rect(img, cx - 14, 36, cx + 14, 37, STONE[1])
    else:   # the roof has fallen beside it
        poly(img, [(cx + 10, 63), (cx + 14, 52), (cx + 28, 57), (cx + 25, 63)], lambda x, y: pick(STONE, 0.5 - 0.3 * (x - cx - 10) / 18, x, y))
        for x in range(cx - 9, cx + 10): put(img, x, 36, STONE[2] if x % 3 else T)
    for y in range(38, 58, 3):                                                     # soot streaks
        put(img, cx - 6 + (y % 5), y, CHAR[3]); put(img, cx + 4 - (y % 4), y + 1, CHAR[3])
    return outline(img)


def deadtree(v):
    img = blank(64, 64)
    def branch(x, y, a, L, w, d):
        if d > 5 or L < 3: return
        ex, ey = x + math.cos(a) * L, y - math.sin(a) * L
        for i in range(int(L) + 1):
            t = i / max(1, L); px, py = x + (ex - x) * t, y + (ey - y) * t
            for k in range(max(1, int(w * (1 - t * 0.5)))):
                put(img, px + k - w // 2, py, pick(CHAR, 0.35 + 0.3 * (k == 0), px, py))
        s = h01(int(x), int(y), v)
        branch(ex, ey, a + 0.45 + s * 0.3, L * 0.62, max(1, w - 1), d + 1)
        branch(ex, ey, a - 0.5 - s * 0.2, L * 0.55, max(1, w - 1), d + 1)
    branch(32, 63, math.pi / 2 + (0.08 if v else -0.06), 22, 4, 0)
    for (x, y) in ((31, 50), (33, 44), (30, 38)):
        put(img, x, y, FIRE[2] if v == 0 else CHAR[4])
    return outline(img)


def devdesk(f):
    img = blank(64, 64)
    D = ramp("1a120c", "2e2014", "46301e", "5e4228", "7a5634")
    rect(img, 12, 44, 51, 46, lambda x, y: pick(D, 0.7 if y == 44 else 0.4, x, y))
    for lx in (14, 49): rect(img, lx, 47, lx + 1, 63, D[1])
    shade_box(img, 24, 24, 45, 43, ramp("1a1a18", "2c2c28", "44443e", "5e5e56", "7a7a70"), 0.55, 0.2, seed=12)   # the CRT
    rect(img, 27, 27, 42, 39, C("041008"))
    for i in range(5):
        w = 3 + int(h01(i, f) * 10)
        rect(img, 28, 28 + i * 2, 28 + w, 28 + i * 2, C("5aff8a") if i != 4 or f else C("b8ffcc"))
    rect(img, 30, 43, 38, 43, C("2c2c28"))
    rect(img, 16, 41, 22, 43, C("222222")); rect(img, 17, 41, 21, 41, C("444444"))          # keyboard
    rect(img, 47, 38, 50, 43, C("e8e0d0")); rect(img, 48, 39, 49, 40, C("6a3a1a"))          # mug
    rect(img, 43, 25, 47, 29, C("f0e060")); rect(img, 20, 30, 23, 34, C("ff9fe2"))          # sticky notes
    return outline(img)


def hearth(f):
    img = blank(64, 64)
    shade_box(img, 10, 22, 53, 63, STONE, 0.45, 0.25, seed=13)
    for y in range(24, 62, 5):                                        # coursed stone
        for x in range(10 + (y // 5 % 2) * 4, 54, 8): put(img, x, y, STONE[1])
        line(img, (10, y), (53, y), STONE[2])
    rect(img, 6, 20, 57, 22, lambda x, y: pick(WOOD, 0.75 if y == 20 else 0.45, x, y))   # the mantel
    rect(img, 18, 36, 45, 63, CHAR[0])                                                    # the firebox
    rect(img, 16, 34, 47, 35, STONE[4])
    for i in range(6):                                                                    # logs
        line(img, (20 + i * 4, 60), (26 + i * 3, 56), WOOD[2 + i % 2])
    for i in range(9):                                                                    # flames
        x = 21 + i * 3
        h = 8 + int(10 * abs(math.sin(f * 1.3 + i * 1.7))) + (4 if 3 <= i <= 5 else 0)
        for k in range(h):
            t = k / h
            put(img, x + round(math.sin(k * 0.5 + f + i) * t * 1.5), 58 - k, FIRE[7 - int(t * 5)] if t < 0.9 else FIRE[2])
            if t < 0.5: put(img, x + 1, 58 - k, FIRE[6 - int(t * 6)])
    for (x, y) in ((24, 18), (38, 17)): rect(img, x, y, x + 3, y + 1, CLAY[3])            # bowls on the mantel
    return outline(img)


def chimes(f):
    """hangs from frame row 24 (the eave), rods sway"""
    img = blank(64, 64)
    rect(img, 22, 23, 41, 24, lambda x, y: pick(WOOD, 0.7 if y == 23 else 0.4, x, y))
    line(img, (31, 18), (31, 22), WOOD[2]); line(img, (32, 18), (32, 22), WOOD[1])
    sway = math.sin(f / 4 * math.tau) * 2.2
    for i, L in enumerate((14, 20, 26, 18, 12)):
        x0 = 24 + i * 4; o = sway * (0.6 + 0.15 * i)
        line(img, (x0, 25), (x0 + o * 0.4, 28), PALESTONE[3])
        for k in range(L):
            t = k / L
            put(img, x0 + o * (0.4 + 0.6 * t), 28 + k, STEEL[5] if k % 5 else STEEL[6])
            put(img, x0 + 1 + o * (0.4 + 0.6 * t), 28 + k, STEEL[3])
    line(img, (32, 25), (32 + sway, 45), PAPER[1]); rect(img, 30 + round(sway), 45, 33 + round(sway), 50, PAPER[3])   # the paper tail
    return outline(img)


def shelves():
    img = blank(64, 64)
    shade_box(img, 18, 24, 45, 63, WOOD, 0.35, 0.15, seed=14)
    for y in (24, 36, 48, 62): rect(img, 18, y, 45, y + 1, WOOD[5] if y < 62 else WOOD[2])
    for i, (x, y, w, h, P) in enumerate(((20, 30, 3, 6, CLAY), (25, 32, 4, 4, CLAY), (31, 29, 2, 7, PAPER), (34, 29, 2, 7, WOOD), (38, 31, 4, 5, CLAY),
                                         (20, 44, 5, 4, STEEL), (27, 41, 2, 7, PAPER), (30, 42, 2, 6, MOSS), (34, 43, 6, 5, CLAY), (21, 56, 6, 6, WOOD), (30, 55, 5, 7, CLAY), (38, 57, 5, 5, PAPER))):
        rect(img, x, y, x + w, y + h - 1, lambda xx, yy: pick(P, 0.7 - 0.35 * (xx - x) / max(1, w), xx, yy))
    return outline(img)


def pine():
    img = blank(64, 64)
    P = ramp("0c140e", "162418", "20361f", "2c4a28", "3e6034")
    rect(img, 31, 50, 33, 63, WOOD[2])
    for i in range(6):
        y = 50 - i * 7; w = 14 - i * 2
        poly(img, [(32 - w, y + 2), (32, y - 9), (32 + w, y + 2), (32 + w - 3, y + 4), (32 - w + 3, y + 4)],
             lambda x, yy: pick(P, 0.6 - 0.45 * (x - 32 + w) / (2 * w) + 0.15 * (h01(x, yy) - 0.5), x, yy))
    return outline(img)


def maglev():
    """a maglev car; its roof (the ridable top) at row 46, body to row 63"""
    img = blank(64, 64)
    body = [(1, 50), (5, 46), (58, 46), (63, 50), (62, 60), (2, 60)]
    for (x, y) in poly_pts(body):
        v = 0.7 - 0.5 * (y - 46) / 14 + (0.12 if y == 47 else 0)
        put(img, x, y, pick(NV, v, x, y))
    rect(img, 6, 49, 57, 53, CY[1])
    for x in range(8, 56, 6): rect(img, x, 50, x + 3, 52, CY[3])
    rect(img, 4, 46, 59, 46, NV[6])
    rect(img, 3, 60, 60, 61, NV[2]); rect(img, 6, 62, 57, 62, MG[2])   # the mag skid
    rect(img, 57, 51, 61, 53, AMB[4])                                    # headlight (faces right)
    return outline(img)


# ============================================================================ large props (128x128)
def dome():
    img = blank(128, 128)
    cx, base = 64, 127
    shade_box(img, 16, 104, 111, 127, PALESTONE, 0.4, 0.2, seed=15)          # the drum
    for x in range(20, 110, 14):                                              # pilasters
        shade_box(img, x, 100, x + 5, 127, PALESTONE, 0.55, 0.2, seed=x)
    rect(img, 14, 100, 113, 103, lambda x, y: pick(PALESTONE, 0.7 if y == 100 else 0.5, x, y))
    for i in range(40):                                                       # the broken dome: ribs over a star-dark shell
        a = math.pi + i / 39 * math.pi
        for r in range(0, 46):
            x, y = cx + math.cos(a) * r, 100 + math.sin(a) * r * 0.9
            if a > math.pi * 1.74 and r > 26 + 10 * math.sin(i * 1.7): continue   # a bite knocked out of the east side
            if r > 43: put(img, x, y, pick(PALESTONE, 0.62, x, y))
            elif i % 6 == 0: put(img, x, y, pick(PALESTONE, 0.5, x, y))
            else: put(img, x, y, pick(OB, 0.25 + 0.2 * (1 - r / 46), x, y))
    for (x, y) in ((50, 72), (58, 64), (44, 84), (70, 80), (54, 88)): star(img, x, y, big=(x == 58))
    # the great telescope poking out of the slit
    for u in range(0, 42):
        for v in range(-3, 4):
            x, y = 70 + u * 0.8 - v * 0.5, 86 - u * 0.6 + v * 0.8
            put(img, x, y, pick(BRASS, 0.75 - 0.5 * (v + 3) / 6 + (0.15 if u % 10 == 0 else 0), x, y))
    for v in range(-4, 5): put(img, 104 - v * 0.5, 61 + v * 0.8, GL[6] if v < 0 else GL[4])
    rect(img, 56, 110, 70, 127, OB[1]); rect(img, 57, 110, 69, 110, PALESTONE[6])   # the doorway
    return outline(img)


def fallenstar(f, glow_only=False):
    img = blank(128, 128)
    def crystal(cx, base, w, h, lean, lit, seed):
        tip = (cx + lean * h, base - h)
        L, R = (cx - w, base), (cx + w, base)
        mid = (cx + lean * h * 0.5 + w * 0.15, base - h * 0.45)
        facet(img, [L, tip, mid], GL, 0.55 + lit * 0.3, seed)
        facet(img, [mid, tip, R], GL, 0.25 + lit * 0.15, seed + 1)
        facet(img, [L, mid, R], GL, 0.35 + lit * 0.2, seed + 2)
        line(img, L, tip, GL[6]); line(img, tip, mid, GL[7])
    crystal(46, 127, 11, 70, -0.18, 0.5, 1)
    crystal(84, 127, 10, 58, 0.25, 0.4, 4)
    crystal(64, 127, 18, 112, 0.06, 1.0, 7)          # the heart-spire
    crystal(30, 127, 6, 34, -0.4, 0.3, 10)
    crystal(98, 127, 6, 30, 0.45, 0.3, 13)
    pulse = 0.5 + 0.5 * math.sin(f / 4 * math.tau)
    for i in range(12, 100):                          # the burning core inside the spire
        x = 64 + 0.06 * (127 - (127 - i)) * 0.0 + math.sin(i * 0.3 + f) * 1.5
        c = STAR[4] if i % 7 < 2 + int(pulse * 3) else STAR[3]
        put(img, 64 + (127 - i) * 0.06 - 1 + math.sin(i * 0.35 + f) * 1.2, i + 15, c)
    for (x, y) in ((58, 40), (70, 62), (48, 92), (86, 96), (62, 20)): star(img, x, y, big=(y == 40))
    img = outline(img)
    rect(img, 18, 124, 110, 127, lambda x, y: pick(OB, 0.35 + 0.1 * (y - 124), x, y) if h01(x, y) > 0.2 else None)   # half-buried
    if glow_only: return glow_copy(img, C("9ab8ff"), grow=2)
    return img


def embertree(f, glow_only=False):
    img = blank(128, 128)
    def seg(a, b, w0, w1, dark=0.3):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(n + 1):
            t = i / n; x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t; w = w0 + (w1 - w0) * t
            for k in range(-int(w), int(w) + 1):
                put(img, x + k, y, pick(CHAR, dark + 0.35 * (1 - (k + w) / (2 * w + 1)), x + k, y))
    seg((64, 127), (62, 70), 11, 6)
    seg((50, 127), (58, 108), 6, 3); seg((80, 127), (70, 108), 6, 3)     # roots
    seg((62, 72), (36, 34), 5, 2); seg((63, 70), (92, 30), 5, 2); seg((62, 74), (66, 14), 4, 1.5)
    seg((40, 40), (22, 30), 2, 1); seg((38, 38), (40, 16), 2, 1); seg((88, 34), (106, 22), 2, 1); seg((90, 32), (86, 12), 2, 1)
    seg((64, 30), (52, 10), 1.5, 1); seg((64, 26), (78, 8), 1.5, 1)
    # the fire inside, showing through the cracks of the bark
    cracks = [[(63, 124), (61, 110), (65, 96), (62, 84), (63, 72)], [(62, 76), (50, 56), (40, 40)], [(64, 74), (78, 52), (90, 34)], [(63, 70), (65, 44), (66, 18)],
              [(56, 118), (58, 108)], [(70, 118), (68, 106)]]
    for k, cr in enumerate(cracks):
        for a, b in zip(cr, cr[1:]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
            for i in range(n + 1):
                t = i / n; x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                hot = 0.5 + 0.5 * math.sin(y * 0.2 + f * 1.6 + k)
                put(img, x, y, FIRE[4 + int(hot * 2.9)])
                if k == 0 and i % 3 == 0: put(img, x + 1, y, FIRE[3])
    img = outline(img)
    if glow_only: return glow_copy(img, C("ff9a40"), grow=2)
    return img


def hut():
    img = blank(128, 128)
    x0, x1, y0 = 26, 102, 82
    for y in range(y0, 128):                                                  # plank walls
        for x in range(x0, x1 + 1):
            plank = (x - x0) // 7
            v = 0.45 + 0.12 * (h01(plank, 3) - 0.5) - 0.18 * (x - x0) / (x1 - x0) + (0.12 if (x - x0) % 7 == 0 else 0)
            put(img, x, y, pick(WOOD, v, x, y))
    for x in (x0, x1): shade_box(img, x - 2, y0 - 2, x + 2, 127, WOOD, 0.3, 0.2, seed=x)   # corner posts
    rect(img, x0 - 4, 124, x1 + 4, 127, lambda x, y: pick(STONE, 0.4, x, y))  # a stone footing
    rect(img, 48, 98, 66, 127, WOOD[0]); rect(img, 49, 99, 65, 127, CHAR[2])  # the doorway (the hatch is inside)
    for (x, y) in ((50, 100), (64, 100)): rect(img, x, y, x, 127, WOOD[4])
    ell(img, 86, 100, 7, 7, lambda nx, ny, x, y: AMB[4] if nx * nx + ny * ny < 0.45 else AMB[2] if nx * nx + ny * ny < 0.75 else WOOD[1])   # round window, lit
    line(img, (79, 100), (93, 100), WOOD[1]); line(img, (86, 93), (86, 107), WOOD[1])
    # the thatched roof
    for (x, y) in poly_pts([(12, 86), (64, 44), (116, 86), (110, 90), (18, 90)]):
        v = 0.55 - 0.4 * (x - 12) / 104 + 0.1 * (((x + y * 2) % 5) == 0) - 0.12 * (vnoise(x, y, 2, 6, 3) - 0.5)
        put(img, x, y, pick(THATCH, v, x, y))
    for i in range(0, 104, 3): put(img, 12 + i, 88 + (i % 2), THATCH[1])
    shade_box(img, 88, 48, 96, 68, STONE, 0.45, 0.2, seed=16)                 # chimney
    rect(img, 86, 46, 98, 48, STONE[5])
    for (x, y) in ((40, 70), (58, 60), (80, 66)): put(img, x, y, MOSS[4])   # moss on the thatch
    line(img, (30, 94), (44, 94), WOOD[5])                                     # a shelf of herbs drying under the eave
    for x in range(31, 44, 3): line(img, (x, 95), (x, 99), MOSS[3])
    return outline(img)


def comet(f):
    img = blank(128, 128)
    cx, cy = 64, 64
    for r in range(22, 0, -1):
        t = r / 22
        ell(img, cx, cy, r, r * 0.92, lambda nx, ny, x, y, t=t: (STAR[4] if t < 0.3 else STAR[3] if t < 0.55 else STAR[2] if t < 0.8 else GL[3]) if h01(x, y, f) > t * 0.35 else None)
    for k in range(7):                                   # ice shards orbiting the heart
        a = f / 4 * math.tau * 0.25 + k * math.tau / 7
        sx, sy = cx + math.cos(a) * 40, cy + math.sin(a) * 26
        facet(img, [(sx, sy - 5), (sx + 3, sy), (sx, sy + 5), (sx - 3, sy)], GL, 0.6, k)
    for k in range(40):                                  # the tail, streaming up-left
        t = k / 40
        put(img, cx - 20 - k * 1.3, cy - 14 - k * 0.9 + math.sin(k * 0.6 + f) * 2, STAR[3] if t < 0.4 else STAR[2] if t < 0.7 else STAR[1])
    return img


# ============================================================================ charm icons (16x16, own outline layer)
def icon_moon():
    img = blank(16, 16)
    ell(img, 7.5, 7.5, 6, 6, lambda nx, ny, x, y: None if (nx - 0.55) ** 2 + (ny + 0.2) ** 2 < 0.55 else (GL[7] if nx + ny < -0.6 else GL[6] if nx + ny < 0.2 else GL[4]))
    for (x, y, c) in ((12, 3, STAR[4]), (13, 6, STAR[3]), (11, 9, STAR[2]), (14, 11, STAR[3]), (12, 13, STAR[2])):
        put(img, x, y, c)
    line(img, (3, 13), (6, 12), VIOLET[3]); put(img, 2, 14, VIOLET[4])
    return img


def icon_glitch():
    img = blank(16, 16)
    def diamond(ox, col, col2):
        poly(img, [(8 + ox, 1), (14 + ox, 8), (8 + ox, 15), (2 + ox, 8)], lambda x, y: col if (x - ox + y) < 16 else col2)
    diamond(-1, MG[2], MG[1]); diamond(1, CY[2], CY[1])
    poly(img, [(8, 3), (12, 8), (8, 13), (4, 8)], lambda x, y: NV[1])
    for y in (5, 8, 11): line(img, (5, y), (11, y), CY[4] if y != 8 else MG[4])
    put(img, 8, 8, C("ffffff"))
    return img


def icon_flame():
    img = blank(16, 16)
    # a heart of dark stone cupping a white-hot flame
    ell(img, 5, 6, 3.6, 3.6, lambda nx, ny, x, y: pick(CHAR, 0.8 - 0.4 * (nx + ny), x, y))
    ell(img, 11, 6, 3.6, 3.6, lambda nx, ny, x, y: pick(CHAR, 0.7 - 0.4 * (nx + ny), x, y))
    poly(img, [(1.5, 7), (8, 15), (14.5, 7)], lambda x, y: pick(CHAR, 0.5 - 0.03 * (x - 2), x, y))
    for (x, y, c) in ((8, 3, FIRE[7]), (8, 4, FIRE[6]), (7, 5, FIRE[5]), (8, 5, FIRE[7]), (9, 5, FIRE[5]), (7, 6, FIRE[6]), (8, 6, FIRE[7]), (9, 6, FIRE[6]),
                      (6, 7, FIRE[4]), (7, 7, FIRE[6]), (8, 7, FIRE[7]), (9, 7, FIRE[6]), (10, 7, FIRE[4]), (6, 8, FIRE[3]), (7, 8, FIRE[5]), (8, 8, FIRE[6]),
                      (9, 8, FIRE[5]), (10, 8, FIRE[3]), (7, 9, FIRE[4]), (8, 9, FIRE[5]), (9, 9, FIRE[4]), (8, 10, FIRE[3])):
        put(img, x, y, c)
    return img


def icon_frames(fn):
    body = fn()
    out = outline(body, K)
    ol = blank(16, 16)
    for y in range(16):
        for x in range(16):
            if out.getpixel((x, y))[3] and not body.getpixel((x, y))[3]: ol.putpixel((x, y), out.getpixel((x, y)))
    return ol, body


# ============================================================================ sheets
SMALL = [("glassgrass", [glassgrass(0), glassgrass(1)]), ("grass", [hgrass(0), hgrass(1)]), ("meteor", [meteor(0), meteor(1), meteor(2)]),
         ("emberrock", [emberrock()]), ("wayshrine", [wayshrine()]), ("wellshard", [wellshard(f) for f in range(4)]),
         ("ashpile", [ashpile(0), ashpile(1)]), ("dumpster", [dumpster()]), ("lantern", [lantern()]), ("jars", [jars()]), ("rug", [rug()]),
         ("embershelf", [embershelf()]), ("hangingpots", [hangingpots()]), ("firewood", [firewood()]), ("stonelantern", [stonelantern()]), ("herbs", [herbs()])]
MEDIUM = [("vending", [vending(0), vending(1)]), ("watertower", [watertower()]), ("deadshrine", [deadshrine(n) for n in range(4)]),
          ("deadtree", [deadtree(0), deadtree(1)]), ("devdesk", [devdesk(0), devdesk(1)]), ("hearth", [hearth(f) for f in range(6)]),
          ("chimes", [chimes(f) for f in range(4)]), ("shelves", [shelves()]), ("pine", [pine()]), ("maglev", [maglev()])]
LARGE = [("dome", [dome()]), ("fallenstar", [fallenstar(f) for f in range(4)]), ("fallenstar_glow", [fallenstar(0, True)]),
         ("embertree", [embertree(f) for f in range(4)]), ("embertree_glow", [embertree(0, True)]), ("hut", [hut()]), ("comet", [comet(f) for f in range(4)])]


def build(name, size, groups, ase):
    frames, tags = [], []
    for tag, imgs in groups:
        a = len(frames)
        for im in imgs:
            assert im.size == (size, size), (name, tag, im.size)
            frames.append({"ms": 120, "cels": {"Layer": im}})
        tags.append((tag, a, len(frames) - 1))
    if ase: asebuild.build(name, size, size, ["Layer"], frames, tags)
    return [f["cels"]["Layer"] for f in frames]


def main():
    ase = "--preview-only" not in sys.argv
    rows = []
    for name, size, groups in (("xsc_s", 32, SMALL), ("xsc_m", 64, MEDIUM), ("xsc_l", 128, LARGE)):
        imgs = build(name, size, groups, ase)
        row = Image.new("RGBA", (len(imgs) * (size + 2), size + 2), (70, 70, 84, 255))
        for i, im in enumerate(imgs): row.alpha_composite(im, (i * (size + 2) + 1, 1))
        rows.append(row)
    icons = [icon_frames(f) for f in (icon_moon, icon_glitch, icon_flame)]
    if ase:
        asebuild.build("xsc_icons", 16, 16, ["Outline", "Icon"], [{"ms": 100, "cels": {"Outline": o, "Icon": b}} for o, b in icons],
                       [(n, i, i) for i, n in enumerate(("c_x3_moon", "c_x3_glitch", "c_x3_flame"))])
    ir = Image.new("RGBA", (3 * 18, 18), (40, 36, 48, 255))
    for i, (o, b) in enumerate(icons): ir.alpha_composite(o, (i * 18 + 1, 1)); ir.alpha_composite(b, (i * 18 + 1, 1))
    rows.append(scale(ir, 2))
    W = max(r.size[0] for r in rows); H = sum(r.size[1] for r in rows)
    pv = Image.new("RGBA", (min(W, 2400), H), (50, 50, 58, 255)); y = 0
    for r in rows: pv.paste(r, (0, y)); y += r.size[1]
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    scale(pv, 2).save(os.path.join(HERE, "previews", "xsc_props.png"))
    print("xsc props", "(preview only)" if not ase else "built")


if __name__ == "__main__":
    main()
