"""Burning Deep props, part A: gear, pipes, cage, timbers, ore, cart, anvil."""
import math
import numpy as np
from xrc_deep_lib import (Spr, ss_mask, ell, rect, poly, capsule, union, minus, inter, nb, bevel, shrink, grow,
                          outline, rivet, chain_v, chain_line, glint, lerp_ramp,
                          ST, MG, IR, GD, CH, ASH, RU, LE, WD, HS, K, KH, T, h01)

TAU = 2 * math.pi


# =================================================================================================== 1. gear
GEAR_N = 12          # teeth; the interior is GEAR_N-fold symmetric so one tooth period loops seamlessly
GEAR_WEB = True      # True: a solid dished web with a bolt ring; False: spokes


def _labels(W, H, fn, nlab, ss=4):
    ys, xs = np.mgrid[0:H * ss, 0:W * ss]
    X = (xs + 0.5) / ss
    Y = (ys + 0.5) / ss
    lab = fn(X, Y)
    lab = lab.reshape(H, ss, W, ss).transpose(0, 2, 1, 3).reshape(H, W, ss * ss)
    occ = (lab > 0).mean(axis=2) >= 0.5
    cnts = np.stack([(lab == j).sum(axis=2) for j in range(1, nlab + 1)], axis=2)
    return np.where(occ, cnts.argmax(axis=2) + 1, 0)


def gear(f, nf=8, N=None, web=None):
    N = N or GEAR_N
    web = GEAR_WEB if web is None else web
    W = H = 48
    cx = cy = 24.0
    per = TAU / N
    rot = f / nf * per
    Ro, Rr, Ri, Rh = 23.3, 19.2, 15.0, 5.6

    def lab_fn(X, Y):
        X = X - cx
        Y = Y - cy
        r = np.hypot(X, Y)
        th = np.arctan2(Y, X)
        ph = (np.mod(th - rot, per) / per - 0.5)          # tooth centred on ph = 0
        # tooth flank: straight-ish sides in world units (tip ~ 0.36 of the period, root ~ 0.52)
        t = np.clip((r - Rr) / (Ro - Rr), 0, 1)
        hw = 0.26 - 0.09 * t
        tooth = (r >= Rr - 0.3) & (r <= Ro) & (np.abs(ph) < hw)
        rim = (r >= Ri) & (r < Rr)
        L = np.zeros(r.shape, dtype=int)
        L[tooth] = 1
        L[rim] = 2
        if web:
            L[(r < Ri)] = 3
        else:
            sp = np.abs(r * np.sin((np.abs(ph) - 0.5) * per))
            L[(r < Ri) & (sp < 1.25 + (Ri - r) * 0.05)] = 3
        L[r < Rh] = 4
        return L

    L = _labels(W, H, lab_fn, 4)
    body = L > 0
    spr = Spr(W, H)
    up = ~nb(body, 0, -1); lf = ~nb(body, -1, 0); dn = ~nb(body, 0, 1); rt = ~nb(body, 1, 0)
    for y in range(H):
        for x in range(W):
            k = L[y, x]
            if not k:
                continue
            rr = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
            s = math.sin(ang)                              # +1 = bottom of the wheel (toward the lava)
            c = IR[3] if k in (1, 2) else IR[2]
            if k == 2 and Rr - 1.4 < rr < Rr - 0.4:
                c = IR[2]                                 # root groove
            if k == 2 and Ri - 0.1 < rr < Ri + 0.9:
                c = IR[4] if s > 0.35 else IR[1] if s < -0.35 else IR[2]   # lip of the dished web
            if k == 3:
                if Ri - 1.2 < rr < Ri:
                    c = IR[1] if s > -0.2 else IR[2]      # the web falls away under the lip
                elif 7.2 < rr < 9.2:                      # raised bolt ring
                    c = IR[4] if (s < -0.3 and rr > 8.4) or (s > 0.3 and rr < 8.0) else IR[3]
                    if (s > 0.3 and rr > 8.4) or (s < -0.3 and rr < 8.0):
                        c = IR[2]
                elif rr < 7.2:
                    c = IR[2] if s < 0 else IR[3]
            if k == 1:
                ph = ((ang - rot) % per) / per - 0.5
                if 0.02 < ph < 0.2 and rr < Ro - 1.0:
                    c = RU[2] if rr < Rr + 1.8 else RU[1]  # rust bleeding down one flank of every tooth
            if up[y, x] or lf[y, x]:
                c = IR[5] if (up[y, x] and lf[y, x]) or (k == 1 and rr > Ro - 1.2 and -2.6 < ang < -0.5) else IR[4]
            elif dn[y, x] or rt[y, x]:
                c = MG[1] if (dn[y, x] and 0.45 < ang < 2.7) else IR[1]     # lava bounce on the underside
            spr.set(x, y, c)
    # rotating details: bolts on the ring, one heat crack per tooth (object space, so the loop is seamless);
    # a crack glows only while it is turned down toward the heat
    for i in range(N):
        a = rot + (i + 0.5) * per
        bx = round(cx + math.cos(a) * 8.3 - 0.5); by = round(cy + math.sin(a) * 8.3 - 0.5)
        spr.set(bx, by, IR[5] if math.sin(a + 0.7) < -0.2 else IR[4] if math.sin(a) < 0.5 else IR[1])
        a2 = rot + i * per + 0.12
        heat = math.sin(a2)
        if heat < -0.15:
            continue
        lvl = 3 if heat > 0.75 else 2 if heat > 0.35 else 1
        for j, (dr, da) in enumerate(((-2.4, -0.06), (-1.4, 0.0), (-0.4, 0.07), (0.6, 0.04), (1.6, 0.12))):
            x = round(cx + math.cos(a2 + da) * (Ri + dr) - 0.5)
            y = round(cy + math.sin(a2 + da) * (Ri + dr) - 0.5)
            if 0 <= x < W and 0 <= y < H and L[y, x] in (2, 3):
                v = lvl - (1 if j in (0, 4) else 0)
                if v > 0:
                    spr.set(x, y, MG[v] if v < 3 else MG[3])
    cap = ss_mask(W, H, ell(cx, cy, 2.6, 2.6))
    spr.shade(cap, IR, 3)
    spr.set(23, 23, IR[5])
    spr.set(24, 24, MG[3])                                # the axle glows in its socket
    outline(spr)
    return spr.img


def build_gear():
    frames = [{"ms": 90, "cels": {"Gear": gear(f)}} for f in range(8)]
    return 48, 48, ["Gear"], frames, [("spin", 0, 7)]


# =================================================================================================== shared bits
def vpipe(spr, x0, x1, y0, y1, dark=0, hot_foot=0):
    """Vertical iron pipe covering columns x0..x1, rows y0..y1: cylinder shading lit from the left."""
    w = x1 - x0 + 1
    for x in range(x0, x1 + 1):
        u = (x + 0.5 - x0) / w
        lv = 4 if u < 0.2 else (5 if w >= 7 and u < 0.36 else 4) if u < 0.36 else 3 if u < 0.62 else 2 if u < 0.84 else 1
        for y in range(y0, y1 + 1):
            v = lv - dark
            c = IR[max(0, min(6, v))]
            if hot_foot and y > y1 - hot_foot and u > 0.8:
                c = MG[1]
            spr.set(x, y, c)


def hpipe(spr, x0, x1, y0, y1, dark=0):
    h = y1 - y0 + 1
    for y in range(y0, y1 + 1):
        u = (y + 0.5 - y0) / h
        lv = 4 if u < 0.25 else 3 if u < 0.6 else 2 if u < 0.85 else 1
        if h >= 6 and 0.2 <= u < 0.4:
            lv = 5
        for x in range(x0, x1 + 1):
            spr.set(x, y, IR[max(0, min(6, lv - dark))])


def collar_v(spr, x0, x1, y, h=2, bolts=True):
    """A flange collar around a vertical pipe (one px proud each side)."""
    for yy in range(y, y + h):
        for x in range(x0 - 1, x1 + 2):
            u = (x + 0.5 - x0 + 1) / (x1 - x0 + 3)
            lv = 4 if u < 0.3 else 3 if u < 0.7 else 2
            if yy == y:
                lv += 1
            if yy == y + h - 1:
                lv -= 1
            spr.set(x, yy, IR[max(1, min(5, lv))])
    if bolts:
        for x in range(x0 + 1, x1, 3):
            spr.set(x, y + h - 1 if h > 2 else y, IR[5] if x < (x0 + x1) / 2 else IR[4])


def handwheel(spr, cx, cy, r, rim=RU, ang=0.3):
    m = ss_mask(spr.w, spr.h, minus(ell(cx, cy, r, r), ell(cx, cy, r - 1.3, r - 1.3)))
    for y, x in np.argwhere(m):
        a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
        s = -math.sin(a + 0.8)
        spr.set(x, y, rim[3] if s > 0.35 else rim[2] if s > -0.35 else rim[1])
    for k in range(4):
        a = ang + k * math.pi / 2
        for t in np.linspace(1.0, r - 1.2, 6):
            spr.set(round(cx - 0.5 + math.cos(a) * t), round(cy - 0.5 + math.sin(a) * t), rim[2])
    spr.set(round(cx - 0.5), round(cy - 0.5), IR[5])


def lumps(spr, items, sep=CH[0]):
    """items: (cx, cy, rx, ry, kind, seed) back to front. kind: ore / slag / hot / stone / coal.
    Each lump is a faceted pebble with a 1px dark seam where it overlaps what is behind it."""
    for (cx, cy, rx, ry, kind, sd) in items:
        n = 7
        pts = []
        for i in range(n):
            a = i / n * TAU + h01(sd, i, 3) * 0.5
            rr = 0.82 + 0.3 * h01(sd, i, 5)
            pts.append((cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr))
        m = ss_mask(spr.w, spr.h, poly(pts))
        if not m.any():
            continue
        edge = m & ~shrink(m)
        bv = bevel(m)
        behind = spr.occ()
        for y, x in np.argwhere(m):
            b = bv[y, x]
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if kind == "hot":
                d = math.hypot(dx * 1.1, dy * 1.2)
                c = MG[5] if d < 0.35 else MG[4] if d < 0.65 else MG[3] if d < 0.9 else MG[2]
                if b < 0:
                    c = MG[2] if d > 0.6 else c
                if h01(x, y, sd) < 0.12 and d > 0.4:
                    c = CH[2]                                   # a crust fleck
            elif kind == "ember":
                d = math.hypot(dx, dy)
                c = MG[3] if d < 0.5 else MG[2] if d < 0.85 else CH[2]
                if b > 0:
                    c = CH[3]
            elif kind == "slag":
                c = CH[2] if b == 0 else CH[4] if b > 0 else CH[1]
                if b == 2:
                    c = ASH[4]                                   # glassy glint
            elif kind == "coal":
                c = CH[1] if b <= 0 else CH[3]
            elif kind == "ore":
                c = ST[4] if b == 0 else ST[6] if b > 0 else ST[2]
                if h01(x, y, sd + 9) < 0.12 and b >= 0:
                    c = GD[3] if h01(x, y, 2) < 0.5 else GD[4]  # metal in the rock
            else:
                c = ST[3] if b == 0 else ST[5] if b > 0 else ST[1]
            if edge[y, x] and behind[y, x] and b <= 0 and kind != "hot":
                c = sep
            spr.set(x, y, c)


# =================================================================================================== 2. pipes
def pipes():
    W, H = 32, 64
    s = Spr(W, H)
    # pipe A (big): floor -> a flared vent cowl at the top
    vpipe(s, 3, 10, 6, 61, hot_foot=6)
    cowl = ss_mask(W, H, poly([(3, 6), (11, 6), (13, 1), (1, 1)]))
    for y, x in np.argwhere(cowl):
        u = (x + 0.5 - 1) / 12
        s.set(x, y, IR[4] if u < 0.25 else IR[3] if u < 0.6 else IR[2] if u < 0.85 else IR[1])
    for x in range(2, 12):
        s.set(x, 1, IR[0] if 3 <= x <= 10 else IR[3])             # sooty mouth
    s.set(4, 1, MG[1]); s.set(7, 1, MG[1])
    for x in range(1, 13):
        s.set(x, 2, IR[5] if x < 4 else IR[4] if x < 9 else IR[3])  # lip
    # pipe B: floor -> y 26, then an elbow bending left into A
    vpipe(s, 14, 18, 27, 61, hot_foot=5)
    elb = ss_mask(W, H, minus(inter(ell(13.0, 27.5, 6.0, 6.2), rect(11, 21, 18, 27)), ell(13.0, 27.5, 1.2, 1.2)))
    for y, x in np.argwhere(elb):
        d = math.hypot(x + 0.5 - 13.0, y + 0.5 - 27.5) / 6.0     # radial position across the bend
        s.set(x, y, IR[4] if d > 0.78 else IR[3] if d > 0.5 else IR[2])
    for y in range(21, 27):
        s.set(11, y, IR[3])
    # pipe C: floor -> gauge stub
    vpipe(s, 23, 28, 42, 61, hot_foot=5)
    vpipe(s, 25, 26, 37, 41)
    # crossovers
    hpipe(s, 11, 13, 50, 54)
    hpipe(s, 19, 22, 46, 49)
    # collars / flanges
    collar_v(s, 3, 10, 58, 3)
    collar_v(s, 14, 18, 58, 3)
    collar_v(s, 23, 28, 58, 3)
    collar_v(s, 3, 10, 42, 2)
    collar_v(s, 3, 10, 10, 2)
    collar_v(s, 14, 18, 38, 2)
    collar_v(s, 23, 28, 42, 2)
    for y in range(21, 28):
        s.set(10, y, IR[2]); s.set(11, y, IR[4] if y < 25 else IR[3])   # elbow flange onto A
    # the leaking seam on A: a flange cracked open, molten light seeping, a drip run below it
    collar_v(s, 3, 10, 30, 3, bolts=False)
    for x in range(3, 11):
        s.set(x, 31, MG[3] if 4 <= x <= 8 else MG[2])
    s.set(5, 31, MG[5]); s.set(6, 31, MG[4])
    for (x, y, c) in ((5, 33, MG[3]), (5, 34, MG[2]), (5, 35, MG[2]), (5, 36, MG[1]), (8, 33, MG[1])):
        s.set(x, y, c)
    s.set(3, 30, IR[5]); s.set(9, 30, IR[4])
    # handwheel valve on B
    handwheel(s, 16.5, 33.0, 4.3)
    # lever valve on the low crossover
    for i in range(6):
        s.set(12 - i // 2, 49 - i, IR[4] if i < 5 else RU[3])
    s.set(12, 50, IR[5])
    # pressure gauge on C
    gx, gy = 25.5, 32.0
    g = ss_mask(W, H, ell(gx, gy, 5.0, 5.0))
    gi = ss_mask(W, H, ell(gx, gy, 3.7, 3.7))
    for y, x in np.argwhere(g & ~gi):
        a = math.atan2(y + 0.5 - gy, x + 0.5 - gx)
        v = -math.sin(a + 0.8)
        s.set(x, y, GD[3] if v > 0.5 else GD[2] if v > -0.3 else GD[1])
    for y, x in np.argwhere(gi):
        s.set(x, y, ASH[2] if (x - gx) + (y - gy) > 1.5 else ASH[3])
    for (x, y) in ((22, 32), (23, 29), (25, 28), (28, 29), (28, 33)):
        s.set(x, y, ASH[1])                                        # ticks
    s.set(25, 31, IR[1]); s.set(26, 30, MG[3]); s.set(27, 29, MG[4])   # needle pinned in the red
    s.set(23, 30, ASH[4])
    # bolt heads
    for (x, y) in ((4, 16), (4, 24), (4, 48), (4, 54), (24, 50), (24, 55), (15, 45), (15, 52)):
        s.set(x, y, IR[5]); s.set(x, y + 1, IR[2])
    outline(s)
    return s.img


def build_pipes():
    return 32, 64, ["Pipes"], [{"ms": 100, "cels": {"Pipes": pipes()}}], [("idle", 0, 0)]


# =================================================================================================== 3. cage
def cage():
    W, H = 24, 32
    s = Spr(W, H)
    chain_v(s, 11, 0, 7)
    # ring + bail
    ring = ss_mask(W, H, minus(ell(12, 9, 2.2, 2.2), ell(12, 9, 1.0, 1.0)))
    s.fill(ring, lambda x, y: IR[4] if y < 9 else IR[2])
    bail = ss_mask(W, H, minus(ell(12, 17.5, 10.2, 7.5), ell(12, 17.5, 9.0, 6.4), rect(0, 15, 23, 31)))
    s.fill(bail, lambda x, y: IR[4] if x < 12 else IR[3])
    # ore heaped above the rim
    lumps(s, [(8, 14.5, 3.2, 2.6, "ore", 1), (15.5, 14, 3.4, 2.8, "slag", 2), (11.5, 13, 2.6, 2.2, "hot", 3),
              (5.5, 15.5, 2.2, 1.8, "stone", 4), (18.5, 15.5, 2.4, 1.8, "ore", 5)])
    # bucket body: tapered, riveted bands, slits showing the hot load inside
    body = ss_mask(W, H, poly([(2, 16), (22, 16), (20, 30), (4, 30)]))
    for y, x in np.argwhere(body):
        u = (x + 0.5 - 2) / 20
        lv = 4 if u < 0.16 else 3 if u < 0.5 else 2 if u < 0.8 else 1
        if y >= 29:
            lv = 1
        s.set(x, y, IR[lv])
    for x in range(2, 22):
        s.set(x, 16, IR[5] if x < 8 else IR[4])
        s.set(x, 17, IR[2])
    for y in (22, 27):
        for x in range(3, 22):
            if body[y, x]:
                s.set(x, y, IR[4] if x < 8 else IR[3])
                if body[y + 1, x]:
                    s.set(x, y + 1, IR[1])
        for x in (5, 11, 17):
            s.set(x, y, IR[5])
    for sx in (8, 14):
        for y in range(19, 22):
            s.set(sx, y, MG[3] if y == 20 else MG[2])
    s.set(8, 20, MG[4])
    for x in range(6, 18):
        s.set(x, 29, MG[1])                                     # heat bounce on the base
    # lugs
    for (x, y) in ((2, 17), (21, 17)):
        s.set(x, y, IR[4])
    outline(s)
    return s.img


def build_cage():
    return 24, 32, ["Cage"], [{"ms": 100, "cels": {"Cage": cage()}}], [("idle", 0, 0)]


# =================================================================================================== 4. timbers
def _charwood(s, m, seed, vertical=True, x0=0, y0=0):
    """Charred timber: dark brown heartwood with long grain streaks, patches of char-black alligator checking,
    the worn lit edge showing warmer wood, a very few embers alive in the deepest checks."""
    bv = bevel(m)
    for y, x in np.argwhere(m):
        b = bv[y, x]
        u, v = (x - x0, y - y0) if vertical else (y - y0, x - x0)
        # grain: each column carries streaks of varying length
        g = h01(u, (v + int(h01(u, 1, seed) * 40)) // (9 + int(h01(u, 2, seed) * 14)), seed)
        c = WD[2] if g < 0.55 else WD[1] if g < 0.85 else WD[3]
        # char patches: blackened wood over the grain, split by short irregular checks
        ch = h01(0, (v + int(h01(seed, 3) * 30)) // 13, seed + 5)
        if ch < 0.42 or (ch < 0.55 and h01(u, v // 3, seed + 6) < 0.5):
            c = CH[2] if g < 0.6 else CH[1] if g < 0.85 else CH[3]
            if h01(u // 2, v, seed + 8) < 0.13:
                c = CH[0]
            elif h01(u // 2, v - 1, seed + 8) < 0.13:
                c = CH[3]                                          # the scale's lit lip above a check
        if b > 0:
            c = WD[4] if ch >= 0.45 else WD[3]
        elif b < 0:
            c = CH[1] if ch < 0.45 else WD[0]
        s.set(x, y, c)
    pts = np.argwhere(m & ~grow(~m, 1))
    for (y, x) in pts:
        if h01(int(x), int(y), seed + 7) < 0.02 and s.get(x, y) == CH[0]:
            s.set(x, y, MG[2] if h01(int(x), int(y), 3) < 0.6 else MG[3])


def _strap(s, x0, x1, y, h=3):
    for yy in range(y, y + h):
        for x in range(x0, x1 + 1):
            c = IR[4] if yy == y else IR[1] if yy == y + h - 1 else IR[3]
            if x == x1:
                c = IR[1]
            s.set(x, yy, c)
    s.set(x0 + 1, y + 1, IR[5]); s.set(x1 - 2, y + 1, IR[5])


def timbers():
    W, H = 48, 160
    s = Spr(W, H)
    # stone footings
    for (fx0, fx1) in ((0, 11), (36, 47)):
        m = ss_mask(W, H, rect(fx0, 153, fx1, 159))
        s.shade(m, ST, 4)
        for x in range(fx0 + 1, fx1):
            s.set(x, 156, ST[2])
    # posts
    for (px0, px1, sd) in ((2, 8, 11), (39, 45, 12)):
        m = ss_mask(W, H, rect(px0, 8, px1, 152))
        _charwood(s, m, sd, True, px0, 8)
    # knee braces
    for (a, b, sd) in (((9, 27), (19, 12), 21), ((38, 27), (28, 12), 22)):
        m = ss_mask(W, H, capsule(a[0], a[1], b[0], b[1], 1.7))
        m &= ~ss_mask(W, H, union(rect(2, 0, 8, 159), rect(39, 0, 45, 159), rect(0, 0, 47, 11)))
        _charwood(s, m, sd, False, 0, 0)
    # crossbeam
    m = ss_mask(W, H, poly([(0, 3), (48, 3), (48, 12), (0, 12)]))
    _charwood(s, m, 31, False, 0, 3)
    for x in range(0, 48):
        s.set(x, 3, WD[3] if h01(x, 1, 5) < 0.75 else WD[2])
    # iron straps: beam-post joints (L plates), bands down the posts
    for (x0, x1) in ((1, 9), (38, 46)):
        for y in (9, 44, 96, 140):
            _strap(s, x0, x1, y)
        for y in range(4, 12):
            s.set(x0, y, IR[3]); s.set(x0 + 1, y, IR[2])
            s.set(x1, y, IR[2]); s.set(x1 - 1, y, IR[1])
        s.set(x0, 5, IR[5]); s.set(x1 - 1, 5, IR[4])
    # hook on a chain from the beam's middle
    chain_v(s, 23, 13, 36)
    hook = [(23, 36, IR[4]), (24, 36, IR[3]), (22, 37, IR[4]), (22, 38, IR[4]), (22, 39, IR[3]), (23, 40, IR[3]),
            (24, 40, IR[2]), (25, 39, IR[2]), (26, 38, IR[3]), (26, 37, IR[4])]
    for (x, y, c) in hook:
        s.set(x, y, c)
    for x in range(21, 27):
        s.set(x, 12, IR[3])
    s.set(22, 12, IR[5])
    # dead lamp on a nail on the right post
    s.set(37, 52, IR[5]); s.set(36, 52, IR[3])
    chain_v(s, 34, 52, 56)
    lamp = ["..aa..", ".abba.", "ab..ba", "acddca", "acddca", "ac..ca", ".abba.", "..aa.."]
    key = {"a": IR[2], "b": IR[4], "c": IR[3], "d": ASH[1], ".": None}
    for j, row in enumerate(lamp):
        for i, ch in enumerate(row):
            if ch == "." and 2 <= j <= 5 and 1 <= i <= 4:
                s.set(32 + i, 56 + j, CH[1])                      # dark sooted glass
            elif key.get(ch):
                s.set(32 + i, 56 + j, key[ch])
    s.set(33, 58, ASH[3])                                           # cold glint on the glass
    outline(s)
    return s.img


def build_timbers():
    return 48, 160, ["Timbers"], [{"ms": 100, "cels": {"Timbers": timbers()}}], [("idle", 0, 0)]


# =================================================================================================== 5. ore
def ore():
    W, H = 32, 16
    s = Spr(W, H)
    items = [
        (16, 12.5, 13.5, 3.8, "stone", 1),
        (7.5, 11.5, 4.6, 3.4, "ore", 2), (23.5, 11.0, 4.8, 3.6, "slag", 3),
        (15.0, 9.5, 5.0, 4.0, "ore", 4), (19.5, 6.8, 3.4, 3.0, "hot", 9),
        (11.0, 6.8, 3.2, 2.8, "slag", 5), (15.5, 4.2, 2.8, 2.5, "ore", 11),
        (3.5, 13.6, 3.0, 2.2, "slag", 6), (28.0, 13.4, 3.4, 2.4, "ore", 7),
        (12.0, 13.4, 3.4, 2.3, "hot", 8), (20.0, 13.6, 3.2, 2.2, "stone", 10),
        (25.8, 7.8, 2.2, 1.9, "ember", 12),
    ]
    lumps(s, items)
    outline(s)
    s.set(21, 1, MG[4])                                             # a spark lifting off the hottest lump
    return s.img


def build_ore():
    return 32, 16, ["Ore"], [{"ms": 100, "cels": {"Ore": ore()}}], [("idle", 0, 0)]


# =================================================================================================== 6. cart
def _wheel(s, cx, cy, r, ang):
    m = ss_mask(s.w, s.h, ell(cx, cy, r, r))
    inner = ss_mask(s.w, s.h, ell(cx, cy, r - 1.2, r - 1.2))
    for y, x in np.argwhere(m & ~inner):
        a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
        v = -math.sin(a + 0.8)
        s.set(x, y, IR[4] if v > 0.45 else IR[3] if v > -0.2 else IR[2])
    for y, x in np.argwhere(inner):
        s.set(x, y, IR[0])
    for k in range(4):
        a = ang + k * math.pi / 2
        for t in np.linspace(0.6, r - 1.0, 8):
            x, y = round(cx - 0.5 + math.cos(a) * t), round(cy - 0.5 + math.sin(a) * t)
            s.set(x, y, IR[3] if math.sin(a + 0.8) < 0 else IR[2])
    s.set(round(cx - 0.5), round(cy - 0.5), IR[5])


def cart(f):
    W, H = 40, 28
    s = Spr(W, H)
    bob = (0, 1, 0, 0)[f]
    ang = f * (math.pi / 2) / 4                                     # 4 frames = one spoke period (90 deg)
    # load: glowing ore heaped over the rim
    ld = [(12, 7.5, 5.0, 3.6, "ore", 21), (27, 7.5, 5.5, 3.6, "slag", 22), (19.5, 5.5, 5.0, 3.8, "hot", 23),
          (7, 9, 3.0, 2.4, "slag", 24), (33, 9, 3.2, 2.4, "ore", 25), (15, 6, 2.6, 2.2, "hot", 26),
          (24, 5, 2.4, 2.0, "ember", 27), (30.5, 6.8, 2.0, 1.8, "hot", 28)]
    ld = [(x, y + bob + (0.5 if (i + f) % 3 == 0 and f % 2 else 0), a, b, k, sd) for i, (x, y, a, b, k, sd) in enumerate(ld)]
    lumps(s, ld)
    # hull: tapered iron tub, riveted plates
    y0 = 9 + bob
    hull = ss_mask(W, H, poly([(2, y0), (38, y0), (35, y0 + 13), (5, y0 + 13)]))
    for y, x in np.argwhere(hull):
        u = (x + 0.5 - 2) / 36
        lv = 3 if u < 0.12 else 2 if u < 0.7 else 1
        s.set(x, y, IR[lv])
    for x in range(2, 38):
        s.set(x, y0, IR[5] if x < 10 else IR[4])
        s.set(x, y0 + 1, IR[3])
        s.set(x, y0 + 2, IR[1])
    for x in range(5, 35):
        if hull[y0 + 12, x]:
            s.set(x, y0 + 12, MG[1] if 8 < x < 32 else IR[1])       # heat under the belly
    for sx in (13, 26):
        for y in range(y0 + 3, y0 + 12):
            if hull[y, sx]:
                s.set(sx, y, IR[3]); s.set(sx + 1, y, IR[1])
        for y in (y0 + 5, y0 + 9):
            s.set(sx, y, IR[5])
    for y in (y0 + 6,):
        for x in range(4, 36):
            if hull[y, x] and x not in (13, 14, 26, 27):
                s.set(x, y, IR[3] if x < 13 else IR[2])
    for (x, y) in ((6, y0 + 4), (33, y0 + 4), (6, y0 + 9), (32, y0 + 9)):
        s.set(x, y, IR[4])
    # couplings
    for (x, y) in ((0, y0 + 5), (1, y0 + 5), (38, y0 + 5), (39, y0 + 5)):
        s.set(x, y, IR[3])
    # axle bar + wheels
    for x in range(8, 33):
        s.set(x, y0 + 13, IR[1])
    _wheel(s, 10.5, 23.0, 4.5, ang)
    _wheel(s, 29.5, 23.0, 4.5, ang)
    outline(s)
    # sparks at the wheels (rolling right: they spray back and up from each rim's contact point)
    # each spark is a short streak (head bright, tail cooler) sprayed back and up from the contact point
    SP = [[(3, 0, 5, 1), (6, -1, 3, 1)], [(4, -1, 4, 2), (7, 0, 2, 0)], [(3, 0, 6, 1), (5, -2, 2, 1)],
          [(5, -1, 3, 1), (8, 0, 2, 1)]]
    for (wx, k) in ((10, 0), (29, 1)):
        for (d, dy, ln, rise) in SP[(f + 2 * k) % 4]:
            for i in range(ln):
                x = wx - 3 - d - i
                y = 27 + dy - (i * rise) // 2
                if 0 <= x < W and 0 <= y < H and s.get(x, y)[3] == 0:
                    s.set(x, y, MG[7] if i == 0 else MG[6] if i == 1 else MG[4])
    # embers lifting off the load
    for (x, y) in (((17, 1), (25, 2)), ((18, 0), (26, 1)), ((16, 2), (24, 0)), ((19, 1), (27, 3)))[f]:
        s.set(x, y, MG[5])
    return s.img


def build_cart():
    frames = [{"ms": 80, "cels": {"Cart": cart(f)}} for f in range(4)]
    return 40, 28, ["Cart"], frames, [("roll", 0, 3)]


# =================================================================================================== 8. anvil
def anvil():
    W, H = 48, 32
    s = Spr(W, H)
    # quench trough (left): riveted iron box, black oil with the forge-glow reflected in it
    tr = ss_mask(W, H, poly([(0, 22), (15, 22), (14, 32), (1, 32)]))
    for y, x in np.argwhere(tr):
        u = (x + 0.5) / 15
        s.set(x, y, IR[3] if u < 0.15 else IR[2] if u < 0.7 else IR[1])
    for x in range(0, 15):
        s.set(x, 22, IR[5] if x < 5 else IR[4])
        s.set(x, 23, IR[0] if 1 <= x <= 13 else IR[3])
        s.set(x, 24, IR[1] if 1 <= x <= 13 else IR[3])
    for x in range(2, 12):
        s.set(x, 23, MG[1] if 4 <= x <= 9 else IR[0])
    s.set(6, 23, MG[3]); s.set(7, 23, MG[2])
    for (x, y) in ((2, 27), (12, 27), (2, 30), (12, 30)):
        s.set(x, y, IR[4])
    for x in range(1, 15):
        s.set(x, 26, IR[3] if x < 6 else IR[2])
    # anvil: stone block base, flared iron foot, waist, body, horn (left) and heel (right)
    base = ss_mask(W, H, rect(17, 27, 37, 31))
    s.shade(base, ST, 4)
    for x in range(18, 37):
        s.set(x, 29, ST[3] if x % 7 else ST[1])
    foot = ss_mask(W, H, poly([(18, 27), (36, 27), (33, 23), (21, 23)]))
    waist = ss_mask(W, H, poly([(21, 23.5), (33, 23.5), (30.5, 18), (23.5, 18)]))
    body = ss_mask(W, H, union(poly([(17, 11), (40, 11), (41.5, 12.5), (40.5, 18), (18, 18)]),
                               poly([(18, 11), (10, 11.2), (5.5, 11.8), (3.5, 12.6), (8, 13.6), (12.5, 15.4),
                                     (16, 17.4), (18, 18)])))
    for m, base_lv in ((foot, 3), (waist, 2), (body, 3)):
        bv = bevel(m)
        for y, x in np.argwhere(m):
            u = (x + 0.5 - 17) / 24
            lv = base_lv + bv[y, x] - (1 if u > 0.75 else 0)
            s.set(x, y, IR[max(1, min(5, lv))])
    for x in range(5, 42):
        if body[11, x]:
            s.set(x, 11, IR[6] if 12 < x < 30 and x % 5 else IR[5])   # polished face
            if body[12, x]:
                s.set(x, 12, IR[4])
    for x in range(12, 41):
        if body[17, x] and not body[18, x]:
            s.set(x, 17, MG[1] if 18 < x < 39 else IR[1])
    for x in range(4, 18):
        for y in range(12, 18):
            if body[y, x] and not body[y + 1, x]:
                s.set(x, y, MG[1] if x > 9 else IR[1])            # the forge-glow on the underside
    s.set(37, 12, IR[0]); s.set(38, 12, IR[0])                        # hardy hole
    # a billet cooling on the face
    for x in range(22, 28):
        s.set(x, 10, MG[5] if 23 <= x <= 26 else MG[4])
        s.set(x, 9, MG[6] if 24 <= x <= 25 else MG[5] if 23 <= x <= 26 else None)
    # the great hammer, leaning on the heel: head on the floor, haft up across the anvil's right side
    haft = ss_mask(W, H, capsule(41.5, 25.5, 33.5, 1.5, 1.15))
    for y, x in np.argwhere(haft):
        s.set(x, y, WD[4] if (x + y) % 2 == 0 and x < 38.5 - (y - 1.5) * 0.33 else WD[3])
    for (x, y) in ((35, 7), (36, 7), (37, 11), (38, 11)):
        s.set(x, y, IR[4])                                            # iron ferrules on the haft
    head = ss_mask(W, H, poly([(36, 25), (47, 23), (47.9, 31.9), (37, 31.9)]))
    bv = bevel(head)
    for y, x in np.argwhere(head):
        lv = 3 + bv[y, x] - (1 if x > 44 else 0)
        s.set(x, y, IR[max(1, min(5, lv))])
    for y in range(24, 32):
        if head[y, 40]:
            s.set(40, y, IR[1])                                       # the head's socket band
            s.set(41, y, IR[4] if y < 28 else IR[3])
    outline(s)
    return s.img


def build_anvil():
    return 48, 32, ["Anvil"], [{"ms": 100, "cels": {"Anvil": anvil()}}], [("idle", 0, 0)]
