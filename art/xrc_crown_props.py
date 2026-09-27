"""Small Pale Crown props for gen_xrc_crown.py. Each builder returns (w, h, layers, frames, tags)."""
import math
import numpy as np
from xrc_crown_lib import (Spr, OUT, IVORY, GOLD, GREY, BRONZE, PETAL, SAGE, FLAME, WHITE, hx, rp,
                           mask, clean, dilate, erode, edge, seg_field, bez, poly_segs, in_poly,
                           tube_light, q, grid, coverage, SS)


def frames_of(layer, imgs, ms):
    if isinstance(ms, int):
        ms = [ms] * len(imgs)
    return [{"ms": m, "cels": {layer: im}} for im, m in zip(imgs, ms)]


def tube_paint(s, segs, ramp, lo=0.0, hi=1.0, ring=None, furrow=None, bias=0.0, thr=0.5, m_extra=None):
    """Rasterise a shaded tube (union of segments) into s. Returns the mask."""
    w, h = s.w, s.h
    m = mask(lambda X, Y: seg_field(X, Y, segs)[0] < 0, w, h, thr)
    if m_extra is not None:
        m &= m_extra
    d, u, sl = seg_field(s.X, s.Y, segs)
    # travel direction per pixel ~ from the nearest segment: approximate with overall gradient of s
    gy, gx = np.gradient(sl)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    lam = tube_light(u, gx / nrm, gy / nrm)
    v = lo + (hi - lo) * np.clip(0.45 + 0.65 * lam, 0, 1) + bias
    if furrow is not None:
        v = v - furrow(u, sl, s.X, s.Y)
    idx = q(np.clip(v, 0, 0.999), len(ramp))
    if ring is not None:
        s.ring(m, ring)
    s.paint(m, (ramp, idx))
    return m


# =========================================================================== 1. sap vein
def sapvein():
    """A vein of glowing sap sunk in a fissure of living pale bark: two bark lips (left lit on its
    outer face, right lit on its inner face), a warm dark seam either side of the sap, short
    horizontal bark cracks, two capillaries, a bead that swells and drips. Two light pulses per
    loop travel down the vein (one every 32 px)."""
    W, H = 16, 64
    NF = 6
    END = 53

    def cx(y):
        return 7.7 + 1.4 * math.sin(y * 0.1 + 0.6) + 0.6 * math.sin(y * 0.26 + 1.9)

    def rv(y):
        return 1.2 + 0.3 * math.sin(y * 0.21) - 0.65 * max(0.0, (y - 42) / 11)

    def rb(y, sd):
        b = 5.3 + 0.8 * math.sin(y * 0.17 + 1.1 + sd * 1.7) + 0.45 * math.sin(y * 0.47 + sd)
        return rv(y) + (b - rv(y)) * (1 - max(0.0, (y - 36) / 17) ** 1.2)

    cracks = {3: -1, 9: 1, 14: -1, 22: 1, 27: -1, 33: 1, 40: -1, 46: 1}
    caps = [(18, -1), (35, 1)]

    frames = []
    for f in range(NF):
        s = Spr(W, H)
        ph = f / NF * 32

        def pulse(y):
            return max(math.exp(-(((y - ph - k * 32 + 3) / 3.0) ** 2)) for k in range(-1, 3))

        vein_px = {}
        for y in range(0, END + 1):
            c = cx(y + 0.5)
            r = rv(y + 0.5)
            pl = pulse(y)
            for x in range(W):
                dx = x + 0.5 - c
                sd = -1 if dx < 0 else 1
                ad = abs(dx)
                if ad <= r + 0.15:
                    core = ad <= r * 0.45 + 0.1
                    lv = (5 if core else 3) + (pl > 0.3) + (pl > 0.7) + (core and pl > 0.85)
                    s.px(x, y, GOLD[min(7, lv)])
                    vein_px[(x, y)] = 1
                    continue
                if y > END - 3:
                    continue
                R = rb(y + 0.5, sd)
                if ad > R:
                    continue
                t = (ad - r) / max(R - r, 0.6)           # 0 at the vein, 1 at the bark edge
                k = int(ad - r - 0.15)                   # pixel index from the vein edge
                if k == 0:
                    col = GOLD[2] if pl > 0.5 else GOLD[1]    # warm dark seam
                elif sd < 0:                             # left lip: outer face lit
                    col = IVORY[3] if t < 0.45 else (IVORY[7] if t < 0.8 else IVORY[6])
                    if k == 1 and pl > 0.5:
                        col = GOLD[3]
                else:                                    # right lip: inner face lit, outer in shade
                    col = IVORY[6] if t < 0.5 else (IVORY[5] if t < 0.8 else IVORY[4])
                    if k == 1 and pl > 0.5:
                        col = GOLD[5]
                if cracks.get(y) == sd and k >= 2 and t < 0.95:
                    col = IVORY[2] if sd < 0 else IVORY[3]
                if cracks.get(y - 1) == sd and k >= 2 and t < 0.9:
                    col = IVORY[7] if sd < 0 else IVORY[6]       # lit lip under the crack
                s.px(x, y, col)
        # capillaries: 1px sap threads running down-and-out into the lips
        for (y0, sd) in caps:
            c = cx(y0)
            pl = pulse(y0 + 2)
            for k in range(4):
                x = c + sd * (rv(y0) + 1.2 + k * 0.8)
                s.px(x, y0 + k, GOLD[5] if pl > 0.5 else GOLD[4])
        # drip strand + bead: swells over the loop, drips on the last frame
        g = f / (NF - 1)
        bx = cx(END)
        by = END + 2.6 + 0.8 * g
        brr = 1.05 + 0.75 * g
        for y in range(END - 2, H):
            for x in range(W):
                ddx, ddy = x + 0.5 - bx, y + 0.5 - by
                d = math.hypot(ddx, ddy)
                if d <= brr or (y + 0.5 < by and abs(ddx) < 0.9 and y > END - 3):
                    lv = 4
                    if ddx < 0 and ddy < -0.2 and d > 0.4:
                        lv = 6
                    elif ddx > 0.2 and ddy > 0:
                        lv = 3
                    s.px(x, y, GOLD[lv])
        s.outline(OUT)
        s.c[0][(s.c[0][:, 3] > 0) & (s.c[0][:, 0] == OUT[0]) & (s.c[0][:, 1] == OUT[1])] = 0
        if f == NF - 1:
            s.px(bx, by + 5, GOLD[6])
            s.px(bx, by + 6, GOLD[3])
        # white spark on the head of each pulse
        for k in range(-1, 3):
            yy = int(ph + k * 32 - 1)
            if 1 <= yy < END - 3:
                s.px(cx(yy + 0.5) - 0.2, yy, WHITE)
        frames.append(s.img())
    return W, H, ["Vein"], frames_of("Vein", frames, 110), [("loop", 0, NF - 1)]


# =========================================================================== 4. brazier
def thorn(s, x0, y0, x1, y1, w, ramp):
    """tapering thorn from base (x0, y0) to tip (x1, y1), base half-width w; lit on its upper-left."""
    segs = poly_segs([(x0, y0), ((x0 * 2 + x1) / 3, (y0 * 2 + y1) / 3 + 0.3), (x1, y1)], w, 0.15)
    m = mask(lambda X, Y: seg_field(X, Y, segs)[0] < 0, s.w, s.h, 0.45, cl=False)
    d, u, sl = seg_field(s.X, s.Y, segs)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    lam = tube_light(u, dx / L, dy / L)
    s.paint(m, (ramp, q(np.clip(0.35 + 0.6 * lam, 0, 0.999), len(ramp) - 1) + 1))
    return m

def brazier():
    W, H = 16, 40
    NF = 6
    CX = 8.0

    def base():
        s = Spr(W, H)
        # three thorned legs splaying to claw feet
        legs = [bez((CX, 32), (CX - 1.5, 35), (CX - 4, 37), (CX - 6.2, 39.2), 10),
                bez((CX, 32), (CX + 1.5, 35), (CX + 4, 37), (CX + 6.2, 39.2), 10),
                bez((CX, 32), (CX, 35), (CX, 37), (CX, 39.3), 6)]
        for i, L in enumerate(legs):
            tube_paint(s, poly_segs(L, 1.25, 0.8), BRONZE, 0.18, 0.95, ring=BRONZE[0] if i == 2 else None)
        # stem with a knop
        stem = [(CX, 33), (CX, 22)]
        tube_paint(s, poly_segs(stem, 1.05, 0.95), BRONZE, 0.15, 1.0)
        for (ky, kr) in ((29.5, 1.9), (23.5, 1.5)):
            tube_paint(s, [(CX, ky - 0.6, CX, ky + 0.6, kr, kr)], BRONZE, 0.2, 1.0)
        # thorns on the stem: small hooked spikes angled up and out
        for (x0, y0, sd) in ((CX - 0.8, 31.6, -1), (CX + 0.8, 27.6, 1), (CX - 0.8, 25.6, -1)):
            thorn(s, x0, y0, x0 + sd * 3.0, y0 - 2.4, 1.0, BRONZE)
        # bowl: shallow crowned cup
        bowl = lambda X, Y: (Y >= 17) & (Y <= 22.2) & (np.abs(X - CX) <= 6.4 - np.clip(Y - 17, 0, None) ** 1.35 * 0.72)
        bm = mask(bowl, W, H)
        X, Y = s.X, s.Y
        nxx = (X - CX) / 6.4
        lam = -nxx * 0.7 + 0.3 - (Y - 17) * 0.09
        bi = q(np.clip(0.45 + 0.45 * lam, 0, 0.999), 7)
        s.paint(bm, (BRONZE, bi))
        # rim band + inner glow bed
        for x in range(2, 14):
            if bm[17, x]:
                s.px(x, 17, BRONZE[6] if x < 9 else BRONZE[5])
            if bm[18, x]:
                s.px(x, 18, BRONZE[2] if x in (2, 13) else (BRONZE[4] if x < 6 else BRONZE[3]))
        for x in range(4, 12):
            s.px(x, 20, BRONZE[1] if (x % 3 == 0) else s.get(x, 20))       # ribbing
        # crown thorns rising from the rim
        for (x0, y0, x1, y1) in ((2.4, 17.6, 0.6, 13.2), (13.6, 17.6, 15.4, 13.2)):
            thorn(s, x0, y0, x1, y1, 1.3, BRONZE)
        return s

    frames = []
    for f in range(NF):
        s = base()
        P = f / NF * 2 * math.pi
        # flame: clean bands, pale white-gold, licking tip
        fh = 12.5 + 1.2 * math.sin(P) + 0.6 * math.sin(2 * P + 1)
        for y in range(1, 18):
            t = (17.2 - y) / fh
            if t < 0 or t > 1.05:
                continue
            sway = (math.sin(P + t * 3.0) * 0.9 + math.sin(2 * P + t * 5.0 + 1.3) * 0.4) * t
            body = math.sin(math.pi * min(1.0, 0.22 + t * 0.78)) ** 0.65
            hw = 3.4 * body * max(0.0, 1.03 - t) ** 0.55 * (1 + 0.08 * math.sin(2 * P + t * 4))
            for x in range(W):
                dx = abs(x + 0.5 - CX - sway)
                if dx > hw:
                    continue
                k = 1 - dx / max(hw, 0.45)
                v = 0.10 + 0.62 * k * (1 - 0.45 * t) + 0.33 * (1 - t)
                i = int(min(0.999, max(0, v)) * len(FLAME))
                s.px(x, y, FLAME[i])
        # a detached tongue / rising sparks
        for k in range(2):
            ph = (f / NF + k * 0.5) % 1.0
            yy = 4 - ph * 6
            xx = CX + math.sin(ph * 6.3 + k * 2) * 2.2
            if yy >= 0:
                s.px(xx, yy, FLAME[2] if ph < 0.5 else FLAME[1])
        # glow bed in the bowl
        for x in range(4, 12):
            s.px(x, 17, FLAME[3] if (x + f) % 3 else FLAME[4])
        flame_m = np.zeros((H, W), bool)
        c = s.c
        for y in range(0, 17):
            for x in range(W):
                if c[y, x, 3] and tuple(c[y, x]) in [tuple(v) for v in FLAME]:
                    flame_m[y, x] = True
        s.outline(OUT, skip=dilate(flame_m) & (s.Y < 16.5))
        frames.append(s.img())
    return W, H, ["Brazier"], frames_of("Brazier", frames, 100), [("loop", 0, NF - 1)]


# =========================================================================== 5. blossom
def flower(s, cx, cy, r=1.0, rot=0.0, pal=PETAL, sep=None, lobes=5):
    """Lobed 5-petal pale blossom (clean supersampled silhouette), lit from the upper left,
    lilac shade lower right, darker throat ring and a gold heart. `sep` = separation-line colour
    drawn on anything already painted underneath."""
    R = 2.6 * r

    def fn(X, Y):
        dx, dy = X - cx, Y - cy
        th = np.arctan2(dy, dx) - rot
        rr = R * (0.72 + 0.28 * np.abs(np.cos(th * lobes / 2)))
        return dx * dx + dy * dy <= rr * rr

    m = mask(fn, s.w, s.h, 0.5, cl=False)
    if not m.any():
        return m
    dx, dy = s.X - cx, s.Y - cy
    d = np.sqrt(dx * dx + dy * dy) / R
    v = 0.78 - 0.3 * (dx + dy) / R - 0.22 * (d < 0.45)
    idx = q(np.clip(v, 0, 0.999), len(pal) - 1) + 1
    if sep is not None:
        s.ring(m, sep)
    s.paint(m, (pal, idx))
    s.px(cx - 0.5, cy - 0.5, GOLD[4])
    if r >= 1.1:
        s.px(cx + 0.5, cy - 0.5, GOLD[3])
        s.px(cx - 0.5, cy - 1.5, GOLD[5])
    return m


def blossom():
    """A low twig of pale Root bark arching out of a root nub, bearing five-petalled ivory blossoms
    with gold hearts and two buds; sways 1px at the tips, three petals drift down on a loop."""
    W, H = 32, 24
    NF = 4

    def draw(f):
        s = Spr(W, H)
        sw = [0.0, 1.0, 0.0, -1.0][f]
        BX, BY = 9.0, 23.4

        def bend(p):
            h = max(0.0, (BY - p[1]) / 14.0) + max(0.0, (p[0] - BX) / 22.0)
            return (p[0] + sw * 0.9 * h, p[1] - sw * 0.25 * max(0.0, (p[0] - BX) / 20.0))

        main = [bend(p) for p in bez((BX, BY), (BX + 1, 17), (BX + 6, 11.5), (BX + 15, 11.5), 18)]
        droop = [bend(p) for p in bez(main[-1], (BX + 18, 11.5), (BX + 19.5, 13), (BX + 20, 15.5), 8)]
        left = [bend(p) for p in bez(main[5], (BX - 1, 14.5), (BX - 3, 12), (BX - 4, 9.5), 10)]
        tube_paint(s, [(BX - 3.0, 23.3, BX + 3.0, 23.4, 1.2, 1.0)], IVORY, 0.1, 0.8)
        tube_paint(s, poly_segs(main, 1.15, 0.6), IVORY, 0.1, 0.78)
        tube_paint(s, poly_segs(droop, 0.6, 0.45), IVORY, 0.1, 0.72)
        tube_paint(s, poly_segs(left, 0.7, 0.45), IVORY, 0.1, 0.72)
        # sage leaves (2-3 px slivers)
        for (p, a, L) in ((main[4], 0.2, 3.0), (main[13], 2.3, 2.6), (left[4], 3.6, 2.4), (droop[4], 0.9, 2.2)):
            x0, y0 = p
            for k in range(int(L * 2) + 1):
                t = k / (L * 2)
                xx, yy = x0 + math.cos(a) * L * t, y0 + math.sin(a) * L * t
                s.px(xx, yy, SAGE[3] if t < 0.55 else SAGE[4])
        # buds
        for (p, oy) in ((main[11], -1.6), (droop[5], 1.2)):
            s.px(p[0], p[1] + oy, PETAL[4])
            s.px(p[0], p[1] + oy + (1 if oy < 0 else -1), SAGE[2])
        # blossoms, back to front
        fl = [(left[-1], 1.2, 0.5, -1.2), (main[16], 1.3, 0.2, -1.8), (main[9], 1.35, 0.9, -2.0),
              (droop[-1], 1.05, 0.1, 1.0), (main[3], 0.85, 2.1, -1.0)]
        for (p, r, rot, oy) in fl:
            flower(s, p[0], p[1] + oy, r, rot + sw * 0.1, sep=PETAL[0])
        s.outline(OUT)
        # falling petals
        for k, (x0, y0, drift) in enumerate(((20.0, 11.0, 1), (5.0, 12.0, -1), (27.0, 17.0, 1))):
            ph = ((f + k * 4 / 3) / NF) % 1.0
            yy = y0 + ph * 9
            xx = x0 + drift * math.sin(ph * 2 * math.pi) * 1.5 + ph * 2
            if yy < H - 1:
                s.px(xx, yy, PETAL[5])
                s.px(xx + (1 if (f + k) % 2 else 0), yy + 1, PETAL[2])
        return s.img()

    frames = [draw(f) for f in range(NF)]
    return W, H, ["Blossom"], frames_of("Blossom", frames, 180), [("loop", 0, NF - 1)]


# =========================================================================== 2. root knot
def gnarl(u, sl, X, Y, k=0.9, thr=0.72, amt=0.22):
    """twisting bark grooves along a tube (spiral furrows), crisp"""
    return amt * (np.sin(u * 2.6 + sl * k) > thr)


def rootknot():
    """A gnarled knot of pale roots rising from the floor: a great back arch with a burl and
    knot-eye, a second root twisting up through it and curling back into an open loop, a low
    front root, a gilded ring grown into the right leg (the bark swells either side of the band),
    small white flowers in the crevices and silver-sage grass at the feet. Openwork: the
    background shows through the loops."""
    W, H = 48, 32
    s = Spr(W, H)
    fur = lambda k=1.0, a=0.3: (lambda u, sl, X, Y: gnarl(u, sl, X, Y, k, amt=a))
    # --- A: great back arch, floor-left -> crown -> right leg
    A = bez((3.5, 32.5), (4.0, 17), (15, 7.5), (24, 9.0), 20)[:-1] + \
        bez((24, 9.0), (33, 10.5), (38.5, 15), (38.5, 22), 12)[:-1] + \
        bez((38.5, 22), (38.5, 27), (40.5, 30.5), (45.5, 32.5), 8)
    wA = lambda t: 3.7 - 1.4 * math.sin(min(1, t * 1.1) * math.pi) ** 0.7
    tube_paint(s, poly_segs(A, 0, 0, wA), IVORY, 0.0, 0.84, furrow=fur(0.9))
    # burl with a knot-eye on the arch's left shoulder
    tube_paint(s, [(10.8, 13.8, 11.4, 14.2, 3.9, 3.9)], IVORY, 0.0, 0.86)
    for (x, y, c) in ((10, 13, IVORY[1]), (11, 13, IVORY[1]), (9, 14, IVORY[1]), (12, 14, IVORY[2]),
                      (10, 14, IVORY[0]), (11, 14, IVORY[0]), (10, 15, IVORY[3]), (11, 15, IVORY[5]),
                      (9, 12, IVORY[6]), (10, 12, IVORY[6])):
        s.px(x, y, c)
    # --- ring band on the right leg, bark swelling either side
    ringc = (38.6, 21.0)
    tube_paint(s, [(ringc[0] - 0.1, ringc[1] - 2.2, ringc[0] + 0.2, ringc[1] + 2.6, 3.1, 3.3)], IVORY, 0.0, 0.88,
               furrow=fur(1.0))
    rm = mask(lambda X, Y: (np.abs(X - ringc[0]) <= 3.5) &
              (np.abs(Y - (ringc[1] + 0.8 * (1 - ((X - ringc[0]) / 3.5) ** 2))) <= 1.0), W, H, 0.5, cl=False)
    s.ring(rm, GOLD[0])
    rx = (s.X - ringc[0]) / 3.5
    gi = np.where(rx < -0.55, 5, np.where(rx < 0.0, 6, np.where(rx < 0.5, 4, 3)))
    gi = gi - ((s.Y - ringc[1] - 0.8 * (1 - rx ** 2)) > 0.1)
    s.paint(rm, (GOLD, gi))
    s.px(ringc[0] - 1.4, ringc[1] - 0.2, GOLD[7])
    # --- B: twisting root rising through the arch and curling back into an open loop
    B = bez((13.5, 32.5), (15, 24), (24, 21), (29, 15.5), 14)[:-1] + \
        bez((29, 15.5), (33, 11), (29, 4.5), (23.5, 7.5), 10)[:-1] + \
        bez((23.5, 7.5), (19.5, 10), (20.5, 15.5), (25.5, 16.5), 10)
    wB = lambda t: 3.0 - 1.9 * t
    tube_paint(s, poly_segs(B, 0, 0, wB), IVORY, 0.1, 1.0, ring=IVORY[0], furrow=fur(1.1))
    # --- C: low front root humping over the floor
    Cc = bez((21.5, 32.5), (24, 25.5), (30.5, 25), (35.5, 32.5), 14)
    tube_paint(s, poly_segs(Cc, 0, 0, lambda t: 2.5 - 0.8 * math.sin(t * math.pi)), IVORY, 0.12, 1.0,
               ring=IVORY[0], furrow=fur(1.3, 0.3))
    # little feeder roots along the floor
    for pts, r0, r1 in ((bez((0.3, 31.8), (2, 29.8), (5, 29.8), (7.5, 31.8), 8), 0.9, 1.3),
                        (bez((43.5, 31.8), (45, 30.2), (46.5, 30.4), (47.8, 31.8), 6), 1.2, 0.8),
                        (bez((16.5, 31.8), (18.5, 30.4), (20, 30.6), (21.5, 31.8), 6), 0.9, 0.9)):
        tube_paint(s, poly_segs(pts, r0, r1), IVORY, 0.05, 0.85, ring=IVORY[1])
    # --- small white flowers in the crevices + sage grass
    for (x, y, r, rot) in ((16.0, 10.6, 0.95, 0.3), (33.4, 15.5, 0.85, 1.2), (27.8, 24.6, 0.8, 0.7),
                           (6.8, 22.0, 0.75, 2.0), (19.5, 26.2, 0.72, 0.4)):
        flower(s, x, y, r, rot, sep=IVORY[1])
    for (x0, n) in ((1, 3), (10, 2), (34, 3), (42, 2)):
        for k in range(n):
            x = x0 + k * 1.6
            hgt = 2 + (k % 2) + (1 if k == 1 else 0)
            for yy in range(hgt):
                s.px(x + (0.5 * yy if k == n - 1 else -0.4 * yy * (k == 0)), 31 - yy,
                     SAGE[4] if yy == hgt - 1 else SAGE[3])
    s.outline(OUT)
    s.c[H - 1:, :][s.c[H - 1:, :, 3] == 0] = 0
    return W, H, ["Knot"], [{"ms": 200, "cels": {"Knot": s.img()}}], [("idle", 0, 0)]


# =========================================================================== 3. portrait
VARN = rp("141012", "1e1719", "2a2123", "382c2c", "483a36", "5a4a40")      # darkened varnish ground
MANT = rp("2c1a1e", "422428", "5a3034", "74443e")                           # dusty faded mantle


def portrait():
    """A portrait in a gothic pointed-arch frame grown from pale bark: the molding is a gnarled
    root with faded gilt on its inner bevel, gilt rosettes at the springline, a curled finial at
    the apex and rootlets curling from the lower corners. The painting: a pale knight of the
    Sovereign's court in 3/4 view - crowned helm with a T-visor, ivory pauldrons with gold trim,
    dusty mantle, a faded gilt halo - on a darkened varnish ground."""
    W, H = 32, 40
    s = Spr(W, H)
    X, Y = s.X, s.Y
    CXp = 16.0
    # opening (canvas): pointed arch
    x0, x1, yb, ys, ya = 7.0, 25.0, 34.0, 16.0, 4.6

    HW = (x1 - x0) / 2
    RA = ((ys - ya) ** 2 + HW * HW) / (2 * HW)          # arc radius giving the apex height

    def arch(X, Y, grow=0.0):
        """gothic pointed arch; offsetting = same arc centres with a bigger radius"""
        dx = np.abs(X - CXp)
        dc = dx + (RA - HW)                            # distance from the opposite arc centre
        topy = ys - np.sqrt(np.clip((RA + grow) ** 2 - dc * dc, 0, None))
        inside_top = (Y >= ys) | ((Y >= topy) & (dc <= RA + grow))
        return (dx <= HW + grow) & inside_top & (Y <= yb + grow)

    open_m = mask(lambda X_, Y_: arch(X_, Y_), W, H, 0.5)
    # ---- painting
    # ground: varnish, a soft halo of lighter bands behind the head
    hd = np.hypot(X - 15.6, (Y - 16.6) * 0.95)
    gv = np.where(hd < 7.8, 4, np.where(hd < 10.0, 3, np.where(Y < 11, 1, 2)))
    gv = gv - (Y > 28)
    s.paint(open_m, (VARN, gv))
    # faded gilt halo ring
    halo = open_m & (np.abs(hd - 6.4) < 0.55)
    s.paint(halo, (GOLD, np.where(X < 16, 3, 2)))
    # mantle / shoulders silhouette behind the pauldrons
    mant = open_m & (Y >= 25.5) & (np.abs(X - 16) <= 7.5 + (Y - 25.5) * 0.9)
    s.paint(mant, (MANT, np.where(X < 13, 2, 1) + 0 * X.astype(int)))
    # torso / breastplate
    tor = open_m & (Y >= 24.5) & (np.abs(X - 15.8) <= 3.8 + (Y - 24.5) * 0.25)
    tv = np.where(X < 14.5, 5, np.where(X < 17.5, 4, 3))
    s.paint(tor, (IVORY, tv))
    for y in range(27, 34):                                   # gold medallion line down the chest
        s.px(15, y, GOLD[3] if y % 3 else GOLD[4])
    s.px(15, 28, GOLD[4]); s.px(14, 28, GOLD[2]); s.px(16, 28, GOLD[2]); s.px(15, 29, GOLD[2])
    # pauldrons (layered plates)
    for (pcx, lit) in ((10.2, True), (21.8, False)):
        pm = open_m & (((X - pcx) / 4.6) ** 2 + ((Y - 28.6) / 3.4) ** 2 <= 1) & (Y <= 31.2)
        nx, ny = (X - pcx) / 4.6, (Y - 28.6) / 3.4
        pv = 0.6 - 0.35 * (nx * 0.7 + ny * 0.7) - (0 if lit else 0.18)
        s.ring(pm, IVORY[0])
        s.paint(pm, (IVORY, q(np.clip(pv, 0, 0.999), 5) + 2))
        trim = pm & ~erode(pm) & (Y > 28.4)
        s.paint(trim, (GOLD, np.where(X < 16, 3, 2)))
        pm2 = open_m & (((X - pcx) / 4.0) ** 2 + ((Y - 31.9) / 2.2) ** 2 <= 1) & (Y > 31.2)
        s.paint(pm2, (IVORY, q(np.clip(pv - 0.1, 0, 0.999), 5) + 1))
    # gorget
    gor = open_m & (Y >= 22.5) & (Y <= 25.2) & (np.abs(X - 15.6) <= 2.9)
    s.paint(gor, (IVORY, np.where(X < 15, 4, 3)))
    s.paint(gor & (np.abs(Y - 24.5) < 0.5), GOLD[2])
    # helm: tall smooth great-helm (3/4 view, facing left)
    HX, HY, HRX, HRY = 15.5, 18.3, 3.7, 5.9
    hm = open_m & (((X - HX) / HRX) ** 2 + ((Y - HY) / HRY) ** 2 <= 1) & (Y <= 23.2)
    nx, ny = (X - HX) / HRX, (Y - HY) / HRY
    hv = 0.62 - 0.45 * (nx * 0.8 + ny * 0.45)
    s.ring(hm, VARN[0])
    s.paint(hm, (IVORY, q(np.clip(hv, 0, 0.999), 6) + 2))
    # crown of five spikes on the helm (faded gold)
    for (bx, tx, ty, w) in ((12.7, 11.0, 10.2, 0.85), (14.1, 13.4, 8.0, 0.95), (15.6, 15.6, 6.4, 1.05),
                            (17.1, 17.8, 8.0, 0.95), (18.4, 19.8, 10.4, 0.8)):
        thorn(s, bx, 13.6, tx, ty, w, GOLD[1:6])
    for x in range(12, 20):                                  # circlet band
        if hm[13, x] or hm[14, x]:
            s.px(x, 13, GOLD[4] if x < 15 else GOLD[3])
    # eye slit + a raised ridge down the faceplate; the far cheek in shade
    for x in range(12, 18):
        if hm[18, x]:
            s.px(x, 18, VARN[0] if x != 14 else IVORY[2])
    for y in range(15, 23):
        s.px(14, y, IVORY[7] if y != 18 else IVORY[3])
        s.px(15, y, IVORY[4] if y != 18 else VARN[0])
    for y in range(19, 23):
        s.px(12 + (y > 21), y, IVORY[6])
    for y in range(15, 23):
        for x in (18, 19):
            if hm[y, x]:
                s.px(x, y, IVORY[3] if x == 18 else IVORY[2])
    # ---- frame: pale bark molding along the arch, a gnarled root
    ring_in = mask(lambda X_, Y_: arch(X_, Y_, 0.0), W, H, 0.5)
    ring_out = mask(lambda X_, Y_: arch(X_, Y_, 3.6), W, H, 0.5)
    fr = ring_out & ~open_m
    # across-molding coordinate by distance rings (0 = inner edge, 1 = outer edge)
    k1 = dilate(open_m, True)
    k2 = dilate(k1, True)
    k3 = dilate(k2, True)
    lvl = np.where(k1, 0, np.where(k2, 1, np.where(k3, 2, 3)))
    left = X < CXp
    top = Y < 16
    # rounded molding: inner bevel shaded, crest lit, outer edge mid; light from the upper left
    fv = np.select([lvl == 0, lvl == 1, lvl == 2], [3, 6, 5], 4)
    fv = fv + np.where(left | top & (X < CXp + 3), 1, -1)
    fv = np.where((Y > yb) & (lvl >= 1), fv - 1, fv)
    s.paint(fr, (IVORY, np.clip(fv, 1, 7)))
    # gnarl grooves twisting round the molding
    ang = np.arctan2(Y - 22.0, X - CXp)
    per = np.where(Y > yb, X / 5.0, ang * 5.2)
    frac = per - np.floor(per)
    g = fr & (lvl == 2) & (np.abs(frac - 0.5) < 0.07) & (Y < yb)
    s.paint(g, (IVORY, np.clip(fv - 2, 1, 7)))
    # faded gilt on the inner bevel (broken)
    gil = fr & (lvl == 0) & (np.sin((X * 0.7 + Y * 0.9)) > -0.35)
    s.paint(gil, (GOLD, np.where(left | top, 3, 2) + 0 * X.astype(int)))
    # gilt rosettes at the springline + base
    for (rx, ry) in ((5.2, 15.0), (26.8, 15.0), (16.0, 36.3)):
        for (dx, dy, c) in ((0, 0, 5), (-1, 0, 3), (1, 0, 3), (0, -1, 4), (0, 1, 2)):
            s.px(rx + dx, ry + dy, GOLD[c])
    # apex finial: a small curled root tip with a gilded bud
    fin = [(16.0, 2.8), (16.3, 1.6), (17.4, 0.9), (18.4, 1.4), (18.3, 2.4)]
    tube_paint(s, poly_segs(fin, 1.1, 0.5), IVORY, 0.2, 1.0)
    s.px(15, 1, GOLD[4]); s.px(15, 2, GOLD[3])
    # thin roots twining up over the molding
    vineL = bez((5.0, 37.0), (1.5, 31), (7.5, 27), (4.0, 21.5), 12)[:-1] + \
        bez((4.0, 21.5), (1.8, 17), (6.8, 13.5), (6.5, 8.5), 10)
    tube_paint(s, poly_segs(vineL, 1.05, 0.55), IVORY, 0.05, 0.95, ring=IVORY[1])
    vineR = bez((27.2, 37.0), (30.6, 32), (25.0, 29), (28.2, 24.5), 12)
    tube_paint(s, poly_segs(vineR, 1.0, 0.55), IVORY, 0.05, 0.9, ring=IVORY[1])
    for (x, y) in ((7, 8), (28, 24)):
        s.px(x, y - 1, PETAL[5]); s.px(x, y - 2, PETAL[4])
    # rootlets trailing down from the bottom rail
    for (rx, L, bend_) in ((8.5, 3.2, -0.8), (12.5, 2.0, 0.6), (21.0, 3.4, 0.9), (24.5, 1.6, -0.4)):
        pts = bez((rx, 37.2), (rx, 37.2 + L * 0.5), (rx + bend_, 37.2 + L * 0.8), (rx + bend_ * 1.6, 37.2 + L), 6)
        tube_paint(s, poly_segs(pts, 0.85, 0.45), IVORY, 0.1, 0.8)
    s.outline(OUT)
    return W, H, ["Portrait"], [{"ms": 200, "cels": {"Portrait": s.img()}}], [("idle", 0, 0)]
