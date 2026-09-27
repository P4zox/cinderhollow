"""THE HEARTBLOOM (xrc_cr_heartbloom) for gen_xrc_crown.py.

176x176, bottom-anchored (stem base at (88, 175)). A vast pale lantern-flower crowning the Pale
Root: three tall back petals (inner faces, lit gold by the core), two side petals and two outer
petals curling open, two front petals half-closed over a breathing core of soft light, a cup of
carved-bark sepals with worn gilt edges on a gilded calyx, a thick gnarled stem with two spiral sap
veins (light climbs them into the flower) and a root flare into the bough, two pale leaves.

loop(6): the core breathes (band radii + halo), sap pulses climb the stem, the outer/side petals
open and close by 1-2 px, motes of light rise through the halo.
"""
import math
import numpy as np
from xrc_crown_lib import (Spr, OUT, IVORY, GOLD, SAGE, hx, rp, tube, bez, bez2, poly_segs, dilate, erode,
                           mask, q, tube_light, grid, WHITE)

W, H = 176, 176
CORE = (88.0, 66.0)
NF = 6

# luminous petal ramp: cool lilac shadow -> warm white
LUM = rp("5e5268", "85788e", "a898a8", "c8bcbc", "e2d6cc", "f4ecdc", "fdf8ec", "ffffff")
GLW = rp("b07a26", "d09a2a", "f0ca58", "ffe890", "fff3b4", "fffbe8", "ffffff")
LEAF = rp("48504a", "68766a", "8e9e8c", "b4c2ac", "d8e2cc", "f0f4e4")
BARK = IVORY
HALO = [(255, 246, 214, 64), (255, 244, 206, 34), (255, 240, 200, 16)]


def glow_at(X, Y, rg=46.0):
    d = np.hypot(X - CORE[0], (Y - CORE[1]) * 1.1)
    return np.clip(1 - d / rg, 0, 1) ** 1.3


def petal_prof(w):
    return lambda t: w * max(0.0, math.sin(math.pi * (0.12 + 0.88 * t) ** 1.3)) ** 0.7


def draw_petal(s, base, ctrl, tip, w, kind, solid, sep=True):
    pts = bez2(base, ctrl, tip, 30)
    segs = poly_segs(pts, 0, 0, petal_prof(w))
    m, u, sl = tube(W, H, segs)
    if not m.any():
        return m
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    t = np.clip(sl / L, 0, 1)
    X, Y = s.X, s.Y
    au = np.abs(u)
    g = glow_at(X, Y)
    # smooth axis direction from the curve itself (index by t)
    n = len(pts) - 1
    D = np.array([(pts[min(i + 1, n)][0] - pts[max(i - 1, 0)][0], pts[min(i + 1, n)][1] - pts[max(i - 1, 0)][1])
                  for i in range(n + 1)], np.float32)
    D /= np.linalg.norm(D, axis=1, keepdims=True) + 1e-6
    ti = np.clip((t * n).round().astype(int), 0, n)
    lam = tube_light(u, D[ti, 0], D[ti, 1])          # + = faces the light (convex reading)
    li = np.full(u.shape, 6)
    if kind == "in":        # concave inner face: the light-facing half is in shade, far half lit
        li = np.where(lam > 0.28, 5, li)
        li = np.where((lam < -0.2) & (t > 0.35), 7, li)
        li = np.where((au < 0.07) & (t > 0.1) & (t < 0.8), 5, li)          # crease
        li = np.where((au > 0.84) & (lam > 0.2), 4, li)                     # shaded rim
        li = np.where((t > 0.84) & (lam < 0.3), 7, li)                      # luminous tip
        li = np.where(t < 0.16, 5, li)
    else:                   # convex outer face: lit half, shade half, midrib ridge
        li = np.where(lam > 0.3, 7, li)
        li = np.where(lam < -0.15, 5, li)
        li = np.where((lam < -0.45) & (au > 0.8), 4, li)
        li = np.where((au < 0.09) & (t > 0.2) & (t < 0.78) & (lam > -0.15), 7, li)
        li = np.where(t < 0.14, 4, li)
        li = np.where((t < 0.3) & (li > 5), 5, li)
    v = li / 7.0
    col = np.array(LUM, np.uint8)[li]
    if kind == "in":        # warm the inner faces toward the cup, gilt thread along the crease
        warm = (t < 0.5) & (li >= 6)
        col = np.where(warm[..., None], np.array(GLW[5], np.uint8), col)
        thread = (au < 0.07) & (t > 0.1) & (t < 0.62)
        col = np.where(thread[..., None], np.array(GLW[2], np.uint8), col)
    else:                   # backlit rims of the outer faces near the core
        rim = (au > 0.72) & (glow_at(X, Y, 60.0) > 0.2)
        col = np.where(rim[..., None], np.array(GLW[4], np.uint8), col)
    # glow from the core (petal bases inside the cup, backlit front petal rims)
    gw = g * (1.2 if kind == "in" else 0.8) + 0.18 * (1 - t) * (kind == "in")
    gi = np.where(gw > 0.8, 3, np.where(gw > 0.62, 4, 5)) - (v < 0.45)
    col = np.where((gw > 0.46)[..., None], np.array(GLW, np.uint8)[gi], col)
    if sep:
        r = dilate(m) & ~m & solid
        sc = np.where((g > 0.38)[..., None], np.array(GLW[1], np.uint8), np.array(LUM[1], np.uint8))
        s.c[r] = sc[r]
    s.c[m] = col[m]
    solid |= m
    return m


def draw_sepal(s, base, ctrl, tip, w, solid, worn_seed=0.0):
    pts = bez2(base, ctrl, tip, 24)
    prof = lambda t: w * max(0.0, math.sin(math.pi * (0.2 + 0.8 * t) ** 1.15)) ** 0.8
    segs = poly_segs(pts, 0, 0, prof)
    m, u, sl = tube(W, H, segs)
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    t = np.clip(sl / L, 0, 1)
    gy, gx = np.gradient(sl)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    lam = tube_light(u * 0.95, gx / nrm, gy / nrm)
    v = 0.08 + 0.72 * np.clip(0.45 + 0.65 * lam, 0, 1)
    au = np.abs(u)
    groove = (np.abs(au - 0.42) < 0.09) & (t < 0.85)          # carved channels
    ridge = (au < 0.1) & (t < 0.9)
    v = v - 0.28 * groove + 0.12 * ridge
    idx = q(np.clip(v, 0, 0.999), 7) + 1
    r = dilate(m) & ~m & solid
    s.c[r] = BARK[1]
    s.paint(m, (BARK, idx))
    # worn gilt along the lit edge + gilt tip
    e = m & ~erode(m)
    lit_side = lam > 0.05
    worn = np.sin(sl * 0.45 + worn_seed) > -0.3
    s.paint(e & lit_side & worn & (t > 0.08), (GOLD, np.where(t > 0.6, 5, 4) + 0 * idx))
    s.paint(m & (t > 0.9), GOLD[5])
    solid |= m
    return m


def draw_bark_tube(s, pts, r0, r1, solid, rfn=None, lo=0.0, hi=0.9, fur=True, sep=BARK[1]):
    segs = poly_segs(pts, r0, r1, rfn)
    m, u, sl = tube(W, H, segs)
    gy, gx = np.gradient(sl)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    lam = tube_light(u, gx / nrm, gy / nrm)
    v = lo + (hi - lo) * np.clip(0.45 + 0.65 * lam, 0, 1)
    if fur:
        v = v - 0.16 * (np.sin(u * 2.4 + sl * 0.32) > 0.86)
    if sep is not None:
        r = dilate(m) & ~m & solid
        s.c[r] = sep
    s.paint(m, (BARK, q(np.clip(v, 0, 0.999), 8)))
    solid |= m
    return m, u, sl


def heartbloom():
    frames = []
    for f in range(NF):
        b = 0.5 - 0.5 * math.cos(2 * math.pi * f / NF)          # breath 0..1..0
        s = Spr(W, H)
        X, Y = s.X, s.Y
        solid = np.zeros((H, W), bool)
        # ---------------- root flare into the bough
        for (p0, p1, p2, p3, r0, r1) in (
                ((84, 158), (78, 168), (62, 172), (34, 175.6), 5.5, 1.3),
                ((92, 158), (98, 168), (116, 171), (144, 175.6), 5.5, 1.3),
                ((86, 164), (80, 172), (70, 174.5), (56, 175.8), 4.0, 1.4),
                ((91, 164), (96, 172), (108, 174.6), (122, 175.8), 4.0, 1.4)):
            draw_bark_tube(s, bez(p0, p1, p2, p3, 16), r0, r1, solid, lo=0.0, hi=0.82)
        # ---------------- stem
        stem = bez((88, 175), (84, 150), (93, 136), (88, 112), 26)
        sm, su, ssl = draw_bark_tube(s, stem, 0, 0, solid, rfn=lambda t: 10.5 - 4.2 * t, lo=0.02, hi=0.9,
                                     sep=None)
        # spiral sap veins with pulses climbing into the flower
        Ls = ssl.max() if sm.any() else 1
        for k in range(2):
            ph = ssl * 0.21 + k * math.pi
            on = sm & (np.abs(su - np.sin(ph) * 0.8) < 0.13) & (np.cos(ph) > -0.1)
            climb = (Ls - ssl - f / NF * 32) % 32
            hot = climb < 5
            s.paint(on, (GOLD, np.where(hot, 6, np.where(np.cos(ph) > 0.5, 4, 3))))
        # ---------------- leaves
        for (p0, p1, p2, w) in (((84, 142), (58, 124), (36, 146), 8.0), ((93, 128), (118, 114), (136, 132), 7.0)):
            pts = bez2(p0, p1, p2, 24)
            segs = poly_segs(pts, 0, 0, lambda t, w=w: w * max(0.0, math.sin(math.pi * (0.1 + 0.9 * t) ** 1.2)) ** 0.8)
            m, u, sl = tube(W, H, segs)
            L = sl.max() if m.any() else 1
            t = sl / L
            v = 0.45 + 0.3 * (u < 0) * (p0[0] < 88) + 0.3 * (u > 0) * (p0[0] > 88) - 0.1 * np.abs(u) + 0.12 * t
            v = v - 0.18 * ((np.abs(u) < 0.08) & (t < 0.9)) + 0.0
            v = v - 0.12 * (np.abs(np.abs(u) - 0.55 + 0.25 * t) < 0.06)
            r = dilate(m) & ~m & solid
            s.c[r] = LEAF[0]
            s.paint(m, (LEAF, q(np.clip(v, 0, 0.999), 6)))
            solid |= m
        # ---------------- petals, back to front
        open_ = b
        draw_petal(s, (88, 102), (87, 56), (88, 9 - 0.5 * b), 17.5, "in", solid)
        draw_petal(s, (83, 102), (68, 52), (55 - b, 20), 15.0, "in", solid)
        draw_petal(s, (93, 102), (108, 52), (121 + b, 20), 15.0, "in", solid)
        draw_petal(s, (82, 104), (52, 72), (30 - 1.5 * open_, 44 + 0.8 * open_), 14.5, "in", solid)
        draw_petal(s, (94, 104), (124, 72), (146 + 1.5 * open_, 44 + 0.8 * open_), 14.5, "in", solid)
        # core of soft light (between the back and front petals)
        R = 14.5 + 1.6 * b
        dx, dy = X - CORE[0], Y - CORE[1]
        th = np.arctan2(dy, dx)
        rr = np.hypot(dx, dy) / (R * (1 + 0.035 * np.sin(5 * th + f * 1.05)))
        cm = rr <= 1.0
        ci = np.where(rr < 0.34 + 0.08 * b, 6, np.where(rr < 0.58 + 0.06 * b, 5, np.where(rr < 0.8, 4, 3)))
        s.paint(cm, (GLW, ci))
        s.paint(cm & (rr > 0.93) & (dy > 0), GLW[2])
        solid |= cm
        # outer petals curling out and down (outer faces)
        draw_petal(s, (80, 108), (44, 92), (18 - 1.5 * open_, 88 + 1.5 * open_), 12.5, "out", solid)
        draw_petal(s, (96, 108), (132, 92), (158 + 1.5 * open_, 88 + 1.5 * open_), 12.5, "out", solid)
        # front petals, half-closed over the core
        draw_petal(s, (86, 112), (70, 92), (64 - 0.8 * b, 70), 12.5, "out", solid)
        draw_petal(s, (90, 112), (106, 92), (112 + 0.8 * b, 70), 12.5, "out", solid)
        draw_petal(s, (88, 113), (88, 100), (88, 87 + b), 8.0, "out", solid)
        # ---------------- calyx + carved sepals
        cal = mask(lambda X_, Y_: ((X_ - 88) / 12.5) ** 2 + ((Y_ - 117) / 6.5) ** 2 <= 1, W, H)
        r = dilate(cal) & ~cal & solid
        s.c[r] = BARK[1]
        nx, ny = (X - 88) / 12.5, (Y - 117) / 6.5
        cv = 0.62 - 0.45 * (nx * 0.75 + ny * 0.6)
        cv = cv - 0.22 * (np.abs(np.sin((X - 88) * 0.55)) < 0.3) * (ny > -0.3)      # carved flutes
        s.paint(cal, (BARK, q(np.clip(cv, 0, 0.999), 7)))

        solid |= cal
        for (p0, p1, p2, w, sd) in (((80, 112), (58, 114), (40, 100), 8.5, 0.0),
                                    ((96, 112), (118, 114), (136, 100), 8.5, 1.0),
                                    ((82, 117), (68, 118), (58, 108), 8.0, 2.0),
                                    ((94, 117), (108, 118), (118, 108), 8.0, 3.0)):
            draw_sepal(s, p0, p1, p2, w, solid, sd)
        # ---------------- outline, then halo + motes on the transparent pixels
        s.outline(OUT)
        op = s.opaque()
        d = np.hypot(X - CORE[0], (Y - CORE[1]) * 1.02)
        for k in range(7):
            ph = (f / NF + k / 7.0) % 1.0
            ang = k * 2.4 + ph * 1.2
            rad = 30 + 34 * ph
            x = CORE[0] + math.cos(ang) * rad * 0.9
            y = CORE[1] - 8 - ph * 40 + math.sin(ang) * 8
            if s.c[int(y) % H, int(x) % W, 3] < 255:
                s.px(x, y, GLW[6] if ph < 0.6 else GLW[4])
                if ph < 0.35 and s.c[int(y) + 1, int(x), 3] < 255:
                    s.px(x, y + 1, GLW[3])
        frames.append(s.img())
    return W, H, ["Heartbloom"], [{"ms": 140, "cels": {"Heartbloom": im}} for im in frames], [("loop", 0, NF - 1)]
