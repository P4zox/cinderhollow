"""Burning Deep props, part B: seat, hoard, vent, crucible, reliquary, glyphs (+ the Heart-Furnace in xrc_deep_furnace)."""
import math
import numpy as np
from xrc_deep_lib import (Spr, ss_mask, ell, rect, poly, capsule, union, minus, inter, nb, bevel, shrink, grow,
                          outline, rivet, chain_v, chain_line, glint, lerp_ramp,
                          ST, MG, IR, GD, CH, ASH, RU, LE, WD, HS, K, KH, T, h01)
from xrc_deep_a import lumps, vpipe, hpipe, collar_v
from xrc_deep_furnace import build_furnace   # noqa: F401  (re-exported for gen_xrc_deep)

TAU = 2 * math.pi


def put_map(s, ox, oy, rows, key):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            c = key.get(ch)
            if c is not None:
                s.set(ox + i, oy + j, c)


def stone_blocks(s, m, courses, seed=0, lit=5):
    """Basalt masonry inside mask m: courses = list of (y0, y1, joint_offset, block_w)."""
    bv = bevel(m)
    for y, x in np.argwhere(m):
        c = None
        for (y0, y1, off, bw) in courses:
            if y0 <= y <= y1:
                lx = (x + off) % bw
                if y == y1 or lx == 0:
                    c = ST[1]
                else:
                    t = (0, 1, -1, 0)[int(h01((x + off) // bw, y0, seed) * 4)]
                    lv = lit - 1 + t + (1 if y == y0 else 0) + (1 if lx == 1 else 0) - (1 if lx == bw - 1 else 0)
                    c = ST[max(1, min(8, lv + bv[y, x]))]
                break
        if c is None:
            c = ST[lit - 1 + bv[y, x]]
        s.set(x, y, c)


# =================================================================================================== 9. seat
def seat():
    W, H = 48, 48
    s = Spr(W, H)
    # plinth: basalt steps banded with riveted iron
    low = ss_mask(W, H, rect(1, 41, 34, 47))
    stone_blocks(s, low, [(41, 44, 2, 8), (45, 47, 6, 8)], seed=3, lit=4)
    top = ss_mask(W, H, rect(4, 34, 31, 40))
    bv = bevel(top)
    for y, x in np.argwhere(top):
        lv = 3 + bv[y, x] - (1 if x > 26 else 0)
        s.set(x, y, IR[max(1, min(5, lv))])
    for x in range(5, 31, 4):
        s.set(x, 36, IR[5]); s.set(x, 39, IR[4])
    for x in range(4, 32):
        s.set(x, 34, IR[5] if x < 12 else IR[4])
    for x in range(1, 35):
        s.set(x, 41, IR[4] if x < 10 else IR[3])                   # iron coping on the lower step
    for x in range(6, 30):
        s.set(x, 40, MG[2] if 12 <= x <= 22 else MG[1])            # a molten seam under the top plate
    # the seat: a tall-backed iron chair, pointed gothic back with side finials
    back = ss_mask(W, H, poly([(9, 30), (9, 11), (12, 7), (17.5, 2), (23, 7), (26, 11), (26, 30)]))
    bv = bevel(back)
    for y, x in np.argwhere(back):
        u = (x + 0.5 - 9) / 17
        lv = 3 if u < 0.3 else 2 if u < 0.75 else 1
        s.set(x, y, IR[max(0, min(5, lv + bv[y, x]))])
    # the back's inset panel with Ashwright's seal
    pan = ss_mask(W, H, poly([(12, 27), (12, 12), (14, 9.5), (17.5, 6), (21, 9.5), (23, 12), (23, 27)]))
    for y, x in np.argwhere(pan & ~shrink(pan)):
        s.set(x, y, IR[1] if (x < 17 and y > 9) or y > 26 else IR[3])
    for y, x in np.argwhere(shrink(pan)):
        s.set(x, y, HS[1] if y < 18 else IR[1])
    seal = ["..GGG..", ".GkkkH.", "GkmmmkH", "GkkmkkH", "GkkmkkH", ".gkkkH.", "..ggg.."]
    put_map(s, 14, 13, seal, {"G": GD[3], "H": GD[4], "g": GD[2], "k": IR[0], "m": GD[5]})
    for (x, y) in ((13, 24), (21, 24), (17, 25)):
        s.set(x, y, IR[4])
    # finials on the back's shoulders and at the peak
    for (fx, fy) in ((9, 11), (25, 11)):
        for j in range(4):
            s.set(fx, fy - j, IR[4] if j < 3 else IR[5])
            if j < 2:
                s.set(fx + 1, fy - j, IR[2])
    s.set(17, 1, IR[5]); s.set(17, 0, IR[4])
    # arms + seat pan
    for (x0, x1) in ((5, 10), (25, 30)):
        for x in range(x0, x1 + 1):
            s.set(x, 21, IR[5] if x < x0 + 2 else IR[4])
            s.set(x, 22, IR[3])
            s.set(x, 23, IR[1])
        for y in range(24, 33):
            s.set(x0, y, IR[3]); s.set(x0 + 1, y, IR[2])
    for x in range(8, 28):
        s.set(x, 29, IR[4] if x < 20 else IR[3])
        s.set(x, 30, IR[3] if x < 20 else IR[2])
        s.set(x, 31, IR[2])
        s.set(x, 32, IR[1])
        s.set(x, 33, K)
    for x in range(10, 26, 5):
        s.set(x, 30, IR[5])
    # the brass foundry horn on its tripod stand
    for y in range(22, 46):
        s.set(40, y, IR[4]); s.set(41, y, IR[2])
    for i in range(6):
        s.set(40 - i, 42 + i, IR[3])
        s.set(41 + i, 42 + i, IR[2])
    s.set(40, 42, IR[4])
    for y in range(24, 27):
        s.set(39, y, IR[4]); s.set(42, y, IR[2])                  # clamp collar
    # horn: a brass cone curving up from the mouthpiece to a great bell facing up and right
    path = [(36.0, 30.0), (38.2, 27.4), (39.8, 24.6), (41.0, 21.2), (41.8, 17.6), (42.4, 14.0)]
    samples = []
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        for t in np.linspace(0, 1, 8, endpoint=False):
            samples.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, (i + t) / (len(path) - 1)))
    tube = np.zeros((H, W), dtype=bool)
    for (px_, py_, t) in samples:
        tube |= ss_mask(W, H, ell(px_, py_, 0.75 + 1.9 * t ** 1.6, 0.75 + 1.9 * t ** 1.6))
    tb = bevel(tube)
    for y, x in np.argwhere(tube):
        s.set(x, y, GD[4] if tb[y, x] > 0 else GD[1] if tb[y, x] < 0 else GD[2] if x > 41 else GD[3])
    bell = ss_mask(W, H, ell(42.6, 11.4, 4.6, 3.0))
    bell_in = ss_mask(W, H, ell(42.9, 11.0, 3.0, 1.6))
    for y, x in np.argwhere(bell & ~bell_in):
        a = math.atan2(y + 0.5 - 11.0, x + 0.5 - 42.6)
        s.set(x, y, GD[5] if -2.6 < a < -1.6 else GD[4] if math.sin(a) < 0.1 else GD[2])
    for y, x in np.argwhere(bell_in):
        s.set(x, y, GD[0] if y < 11 else IR[0])
    for (x, y) in ((39, 26), (41, 20)):
        s.set(x, y, GD[4])                                         # brass bands on the horn
    s.set(36, 30, GD[3]); s.set(35, 30, GD[2])                    # mouthpiece
    outline(s)
    return s.img


def build_seat():
    return 48, 48, ["Seat"], [{"ms": 100, "cels": {"Seat": seat()}}], [("idle", 0, 0)]


# =================================================================================================== 10. hoard
def hoard():
    W, H = 32, 20
    s = Spr(W, H)
    # the pile: a dark bed of coin-shadow, then individual coins laid back to front so each one reads
    mound = ss_mask(W, H, union(ell(17, 21.0, 14.5, 8.6), ell(8, 20.5, 7.5, 6.0)))
    s.fill(mound, GD[0])
    coins = []
    for i in range(160):
        x = 1 + h01(i, 1, 3) * 30
        y = 11 + h01(i, 2, 3) * 9
        yi, xi = min(19, int(y)), min(31, int(x))
        if mound[yi, xi] and mound[max(0, yi - 1), xi]:
            coins.append((y, x, i))
    for (y, x, i) in sorted(coins):
        xi, yi = int(x), int(y)
        s.set(xi, yi, GD[4]); s.set(xi + 1, yi, GD[3]); s.set(xi + 2, yi, GD[2])
        s.set(xi, yi + 1, GD[2]); s.set(xi + 1, yi + 1, GD[1]); s.set(xi + 2, yi + 1, GD[1])
        if h01(i, 4, 3) < 0.15:
            s.set(xi, yi, GD[5])
    # ingots stacked on the left
    for (x0, y0) in ((2, 12), (8, 12), (5, 8)):
        ing = ss_mask(W, H, poly([(x0, y0 + 3.9), (x0 + 1, y0), (x0 + 6, y0), (x0 + 7, y0 + 3.9)]))
        for yy, xx in np.argwhere(ing):
            c = GD[4] if yy == y0 else GD[3] if xx < x0 + 5 else GD[2]
            if yy >= y0 + 3:
                c = GD[1]
            s.set(xx, yy, c)
        s.set(x0 + 2, y0, GD[5])
        for xx in range(x0 + 1, x0 + 6):
            s.set(xx, y0 + 2, GD[2] if xx < x0 + 5 else GD[1])        # stamped mark / shadow line
    # a goblet on the right
    gob = ["ghhhg", ".gHg.", "..g..", "..h..", ".ghg."]
    put_map(s, 24, 6, gob, {"g": GD[2], "h": GD[3], "H": GD[4]})
    s.set(25, 6, GD[5])
    # a sword hilt jutting from the pile
    for i in range(5):
        s.set(29 - i // 2, 15 - i, IR[4] if i < 4 else IR[5])
    for x in (26, 27, 28, 29):
        s.set(x, 12, GD[3] if x < 28 else GD[2])
    s.set(27, 10, MG[3])                                             # a ruby pommel
    # the crown, perched on the crest
    crown = ["h.H.h.h", "hgHghgh", "GGGGGGG", "grgGgbg", "ggggggg"]
    put_map(s, 13, 4, crown, {"h": GD[4], "H": GD[5], "g": GD[2], "G": GD[3], "r": MG[3], "b": ASH[4]})
    outline(s)
    for (x, y, big) in ((15, 3, False), (6, 8, False), (20, 12, True), (10, 15, False)):
        s.set(x, y, GD[5])
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s.set(x + dx, y + dy, GD[4])
    return s.img


def build_hoard():
    return 32, 20, ["Hoard"], [{"ms": 100, "cels": {"Hoard": hoard()}}], [("idle", 0, 0)]


# =================================================================================================== 11. vent
VENT_MOUTH = (16, 6)          # centre of the vent's mouth (frame coords, the lava column starts here)


def vent(mode, f):
    W, H = 32, 16
    s = Spr(W, H)
    mx, my = VENT_MOUTH
    heat = {"idle": 0, "warn": 1 + f, "erupt": 4}[mode]
    # slag pool: flat crust with hot cracks, brighter as the vent builds
    pool = ss_mask(W, H, ell(16, 14.0, 15.8, 2.6))
    for y, x in np.argwhere(pool):
        c = CH[2] if (x + y) % 7 else CH[1]
        if y == 12 or not pool[max(0, y - 1), x]:
            c = CH[3]
        s.set(x, y, c)
    cracks = [(3, 14), (4, 14), (5, 15), (8, 13), (9, 14), (10, 14), (22, 14), (23, 13), (24, 14), (26, 15), (27, 14),
              (28, 14), (6, 13), (20, 15)]
    lv = (1, 2, 2, 3, 4)[min(4, heat)]
    for i, (x, y) in enumerate(cracks):
        s.set(x, y, MG[lv if i % 3 else max(1, lv - 1)])
    # basalt cone around the mouth
    cone = ss_mask(W, H, poly([(6, 14), (11, 7.5), (13.5, 5.2), (18.5, 5.2), (21, 7.5), (26, 14)]))
    bv = bevel(cone)
    for y, x in np.argwhere(cone):
        u = (x + 0.5 - 6) / 20
        l = 4 if u < 0.3 else 3 if u < 0.6 else 2
        l += bv[y, x]
        if h01(x // 2, y // 2, 7) < 0.25:
            l -= 1                                                   # rough rock facets
        c = ST[max(1, min(6, l))]
        if y >= 12 and u > 0.25:
            c = MG[1] if (x + heat) % 3 == 0 and heat else ST[2]      # heat creeping up the foot
        s.set(x, y, c)
    for (x, y) in ((9, 11), (10, 10), (22, 11), (21, 10), (12, 9)):
        s.set(x, y, ST[1])                                           # fissures
    # mouth
    for x in range(13, 19):
        s.set(x, 6, MG[1] if heat == 0 else MG[3])
        s.set(x, 5, ST[2])
    for x in range(14, 18):
        s.set(x, 6, MG[2] if heat == 0 else MG[4] if heat < 3 else MG[5])
    s.set(13, 5, ST[4]); s.set(18, 5, ST[2])
    if mode == "warn":
        # the lava dome bulges up out of the throat and spits sparks
        b = f + 1
        dome = ss_mask(W, H, ell(mx, 6.2, 2.2 + 0.5 * f, b * 0.9 + 0.2))
        for y, x in np.argwhere(dome):
            if y <= 6:
                d = (6.2 - (y + 0.5)) / (b * 0.9 + 0.2)
                s.set(x, y, MG[6] if d > 0.6 else MG[5] if d > 0.25 else MG[4])
        SP = [[(15, 2), (18, 3)], [(13, 1), (19, 2), (16, 0)], [(12, 2), (20, 1), (15, 0), (18, 0), (11, 4)]][f]
        for (x, y) in SP:
            s.set(x, y, MG[6] if (x + y) % 2 else MG[5])
    if mode == "erupt":
        # the base of the lava column bursting out of the mouth, with splash thrown over the rim
        wob = (0, 1, 0, -1)[f]
        for y in range(0, 7):
            t = y / 6.0
            hw = 2.2 + t * 1.6 + (0.6 if (y + f) % 3 == 0 else 0)
            for x in range(W):
                d = abs(x + 0.5 - mx - wob * (1 - t))
                if d <= hw:
                    e = d / hw
                    s.set(x, y, MG[7] if e < 0.35 else MG[6] if e < 0.7 else MG[5])
        DROPS = [
            [(10, 3, 5), (22, 2, 5), (9, 6, 4), (23, 5, 4), (12, 0, 6)],
            [(9, 2, 5), (23, 1, 5), (8, 5, 4), (24, 4, 4), (20, 0, 6)],
            [(8, 3, 5), (24, 3, 5), (7, 7, 4), (25, 6, 4), (11, 1, 6)],
            [(10, 1, 5), (22, 4, 5), (7, 9, 3), (25, 9, 3), (21, 1, 6)],
        ][f]
        for (x, y, l) in DROPS:
            s.set(x, y, MG[l])
            if l >= 5:
                s.set(x, y + 1, MG[l - 1])
        for x in range(8, 24):
            if s.get(x, 12) == CH[3]:
                s.set(x, 12, MG[3] if (x + f) % 2 else MG[2])     # the pool lit by the burst
    outline(s, skip=None)
    return s.img


def build_vent():
    frames, tags = [], []
    for mode, n in (("idle", 1), ("warn", 3), ("erupt", 4)):
        a = len(frames)
        for f in range(n):
            frames.append({"ms": 110 if mode != "erupt" else 80, "cels": {"Vent": vent(mode, f)}})
        tags.append((mode, a, len(frames) - 1))
    return 32, 16, ["Vent"], frames, tags


# =================================================================================================== 12. crucible
CRU_SPOUT = (61, 19)          # the spout tip (frame coords): the pour stream leaves here


def crucible(pour, f):
    W, H = 64, 56
    s = Spr(W, H)
    cx = 31.5
    # chains: one from the ceiling to a ring, a V down to the two lugs
    chain_v(s, 31, 0, 6, phase=f if False else 0)
    ring = ss_mask(W, H, minus(ell(32, 8, 2.3, 2.1), ell(32, 8, 1.0, 0.9)))
    s.fill(ring, lambda x, y: IR[4] if y < 8 else IR[2])
    chain_line(s, 30, 9, 11, 21)
    chain_line(s, 33, 9, 52, 21)
    # body: deep bowl lit from the upper left, the charge's heat glowing through its base
    top, bot = 22, 51
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        hw = 22.5 - 5.5 * t ** 1.7
        if y >= bot - 3:
            hw -= (y - (bot - 4)) * 2.4
        for x in range(int(cx - hw), int(cx + hw) + 1):
            d = (x + 0.5 - cx) / hw
            if abs(d) > 1:
                continue
            nz = math.sqrt(max(0.0, 1 - d * d))
            lv = 0.6 + 2.6 * max(0.0, -0.55 * d + 0.45 * nz) - 1.1 * t
            band = abs(((x - cx + 3) % 11) - 5.5) < 0.6
            if band:
                lv += 0.9
                if y % 6 == 3:
                    lv = 4
            c = IR[int(max(0, min(5, round(lv))))]
            if d > 0.84 and not band:
                c = MG[1] if d > 0.94 and t < 0.8 else IR[1]
            if t > 0.84 and abs(d) < 0.7:
                c = MG[1] if (x + y) % 2 else IR[1]
            s.set(x, y, c)
    # crusted slag run down the flank (glassy black, a hot thread inside)
    for (x0, y0, ln) in ((19, 25, 9), (40, 25, 13), (27, 25, 5)):
        for j in range(ln):
            x = x0 + (1 if j > ln * 0.6 else 0)
            s.set(x, y0 + j, CH[1] if j < ln - 1 else CH[2])
            s.set(x + 1, y0 + j, CH[2] if j % 4 else CH[3])
            if j == ln // 2:
                s.set(x, y0 + j, MG[2])
    # rim
    for y in range(19, 23):
        for x in range(int(cx - 24), int(cx + 25)):
            c = IR[4] if y == 19 else IR[3] if y == 20 else IR[2] if y == 21 else IR[1]
            if y == 19 and x < cx - 12:
                c = IR[5]
            s.set(x, y, c)
    for x in range(int(cx - 22), int(cx + 23), 5):
        s.set(x, 21, IR[5])
    # the spout on the right: a lipped channel rising to the tip
    sp = ss_mask(W, H, poly([(52, 19), (58, 17.3), (62, 17.6), (62.6, 19.2), (58, 21.5), (54, 23)]))
    for y, x in np.argwhere(sp):
        s.set(x, y, IR[4] if y < 19 else IR[2] if y < 21 else IR[1])
    # lugs
    for sgn, lx in ((-1, 11), (1, 52)):
        m = ss_mask(W, H, minus(ell(lx + 0.5, 21.5, 2.6, 2.6), ell(lx + 0.5, 21.5, 1.1, 1.1)))
        s.fill(m, lambda x, y: IR[4] if y < 21 else IR[2])
    # molten charge heaving above the rim; when pouring it runs to the spout
    for x in range(int(cx - 22), int(cx + 23)):
        w = 1.0 * math.sin(f * math.pi / 2 + x * 0.3) + 0.6 * math.sin(-f * math.pi / 2 + x * 0.13)
        lift = 0.0
        if pour:
            lift = max(0.0, (x - cx) / 22.0) * 1.5
        topy = int(round(17.2 + w - lift))
        for y in range(topy, 19):
            dd = y - topy
            s.set(x, y, MG[7] if dd == 0 else MG[6] if dd == 1 else MG[5])
    if pour:
        for x in range(53, 62):
            s.set(x, 17 if x < 58 else 16 if x < 61 else 17, MG[6])
            s.set(x, 18 if x < 58 else 17, MG[5])
    else:
        s.set(60, 17, MG[3])                                          # a skin of slag in the dry spout
    outline(s)
    if pour:
        # the stream: arcs off the tip, then falls straight; blobs travel down 4 px per frame (16 px loop)
        sx, sy = CRU_SPOUT
        for y in range(sy - 1, H):
            t = y - sy
            xc = sx + 0.8 * math.sqrt(max(0, t)) * 0.9 if t < 6 else sx + 2.0
            wob = 0.5 * math.sin((y - f * 4) * TAU / 16)
            hw = 1.1 + 0.35 * math.sin((y - f * 4) * TAU / 8 + 1.0)
            for x in range(int(xc - 3), int(xc + 4)):
                d = x + 0.5 - (xc + wob)
                if abs(d) <= hw:
                    e = abs(d) / hw
                    s.set(x, y, MG[7] if e < 0.4 else MG[6] if e < 0.8 else MG[5])
                elif abs(d) <= hw + 0.8:
                    if s.get(x, y)[3] == 0:
                        s.set(x, y, MG[3])
        for (dx, dy) in ((-2, 30), (3, 38), (-2, 47)):
            yy = (dy + f * 4) % (H - 22) + 22
            s.set(sx + 2 + dx, yy, MG[5])
    return s.img


def build_crucible():
    frames = [{"ms": 140, "cels": {"Crucible": crucible(False, 0)}}]
    for f in range(4):
        frames.append({"ms": 80, "cels": {"Crucible": crucible(True, f)}})
    return 64, 56, ["Crucible"], frames, [("idle", 0, 0), ("pour", 1, 4)]


# =================================================================================================== 13. reliquary
def reliquary(state, f=0):
    """state: closed | open with f = 0 (lid cracks), 1 (lid swinging back), 2 (open, shard revealed)."""
    W, H = 24, 32
    s = Spr(W, H)
    # plinth
    pl = ss_mask(W, H, rect(3, 26, 20, 31))
    stone_blocks(s, pl, [(26, 28, 1, 6), (29, 31, 4, 6)], seed=5, lit=4)
    for x in range(2, 22):
        s.set(x, 25, ST[6] if x < 8 else ST[5])
        s.set(x, 26, ST[3])
    opened = state == "open"
    k = f if opened else -1
    # lid behind the box once it swings open (its inner face, lit by the shard)
    if k == 2:
        lid = ss_mask(W, H, poly([(4, 15), (4, 7), (12, 2.5), (20, 7), (20, 15)]))
        for y, x in np.argwhere(lid):
            c = IR[1]
            if y > 11:
                c = MG[1] if (x + y) % 2 else IR[1]
            s.set(x, y, c)
        for y, x in np.argwhere(lid & ~shrink(lid)):
            s.set(x, y, IR[3] if x < 12 else IR[2])
    # casket box
    box = ss_mask(W, H, rect(5, 15, 18, 24))
    for y, x in np.argwhere(box):
        u = (x + 0.5 - 5) / 14
        s.set(x, y, IR[3] if u < 0.2 else IR[2] if u < 0.7 else IR[1])
    for y in (15, 23):
        for x in range(5, 19):
            s.set(x, y, IR[4] if x < 11 else IR[3])
    for x in (5, 18):
        for y in range(15, 25):
            s.set(x, y, IR[4] if x == 5 else IR[1])
    for (x, y) in ((6, 16), (17, 16), (6, 22), (17, 22)):
        s.set(x, y, IR[5])
    lock = ["GHG", "GkG", "gGg"]
    put_map(s, 10, 18, lock, {"G": GD[3], "H": GD[5], "g": GD[2], "k": IR[0]})
    if k in (-1, 0):
        dy = -1 if k == 0 else 0
        lid = ss_mask(W, H, poly([(4, 15.5 + dy), (4, 12 + dy), (8, 9 + dy), (16, 9 + dy), (20, 12 + dy), (20, 15.5 + dy)]))
        bv = bevel(lid)
        for y, x in np.argwhere(lid):
            u = (x + 0.5 - 4) / 16
            lv = (3 if u < 0.35 else 2 if u < 0.75 else 1) + bv[y, x]
            s.set(x, y, IR[max(1, min(5, lv))])
        for x in range(8, 16):
            s.set(x, 9 + dy, IR[5] if x < 12 else IR[4])
        s.set(12, 8 + dy, IR[4]); s.set(12, 7 + dy, IR[5]); s.set(11, 8 + dy, IR[3])      # finial
        for x in range(5, 19):
            s.set(x, 13 + dy, IR[1])
        s.set(7, 12 + dy, IR[5]); s.set(16, 12 + dy, IR[4])
        if k == 0:
            for x in range(5, 19):
                s.set(x, 15, MG[5] if 8 <= x <= 15 else MG[4])         # light spilling from the gap
            s.set(12, 15, MG[7]); s.set(11, 15, MG[6])
        else:
            for x in range(7, 17, 3):
                s.set(x, 15, IR[1])
    elif k == 1:
        # lid half-way: seen edge-on, tilted back, the glow now pouring out over the box
        lid = ss_mask(W, H, poly([(4, 13), (5, 9), (19, 9), (20, 13)]))
        for y, x in np.argwhere(lid):
            s.set(x, y, IR[3] if y < 11 else IR[1])
        for x in range(5, 19):
            s.set(x, 9, IR[4] if x < 12 else IR[3])
            s.set(x, 13, MG[2])
        for x in range(6, 18):
            s.set(x, 14, MG[5] if 8 <= x <= 15 else MG[4])
            s.set(x, 15, MG[4] if 7 <= x <= 16 else MG[3])
        s.set(12, 14, MG[7]); s.set(11, 14, MG[6]); s.set(12, 15, MG[6])
    if k == 2:
        # open: the interior glows, the shard rises out of it
        for x in range(6, 18):
            s.set(x, 15, MG[4] if 8 <= x <= 15 else MG[3])
            s.set(x, 16, MG[2])
        shard = ["..w..", ".wYo.", ".wYo.", "wYYoo", ".YYo.", ".oYo.", "..o..", "..o.."]
        put_map(s, 10, 6, shard, {"w": MG[7], "Y": MG[6], "o": MG[5]})
        for (x, y) in ((8, 8), (16, 7), (9, 4), (15, 3), (12, 2)):
            s.set(x, y, MG[5] if (x + y) % 2 else MG[6])                 # motes of light around it
    outline(s)
    return s.img


def build_reliquary():
    frames = [{"ms": 120, "cels": {"Reliquary": reliquary("closed")}}]
    for f in range(3):
        frames.append({"ms": 120, "cels": {"Reliquary": reliquary("open", f)}})
    return 24, 32, ["Reliquary"], frames, [("closed", 0, 0), ("open", 1, 3)]


# =================================================================================================== 14. glyphs
GLYPHS = {
    "g0": [  # ox head: spread horns, broad brow, eyes, narrowing muzzle
        "XX......XX",
        "X........X",
        "X.XXXXXX.X",
        ".XXXXXXXX.",
        "..X.XX.X..",
        "..XXXXXX..",
        "...XXXX...",
        "...X..X...",
        "....XX....",
    ],
    "g1": [  # hammer
        ".XXXXXXX..",
        ".XXXXXXX..",
        ".XX...XX..",
        "....X.....",
        "....X.....",
        "....X.....",
        "....X.....",
        "...XXX....",
        "....X.....",
    ],
    "g2": [  # flame
        "....X.....",
        "....XX....",
        "...XXX..X.",
        "..XXXXX.X.",
        "..XXX.XXX.",
        ".XXX..XXX.",
        ".XX....XX.",
        ".XXX..XXX.",
        "..XXXXXX..",
    ],
    "g3": [  # skull
        "...XXXX...",
        "..XXXXXX..",
        ".XXXXXXXX.",
        ".X..XX..X.",
        ".X..XX..X.",
        ".XXXX.XXX.",
        "..XXXXXX..",
        "..X.X.X...",
        "...XXXX...",
    ],
}


def glyph(key):
    W = H = 16
    s = Spr(W, H)
    plate = ss_mask(W, H, poly([(3, 1), (13, 1), (15, 3), (15, 13), (13, 15), (3, 15), (1, 13), (1, 3)]))
    bv = bevel(plate)
    for y, x in np.argwhere(plate):
        lv = 2 + bv[y, x]
        if bv[y, x] == 0 and (x + y) > 22:
            lv = 2
        s.set(x, y, IR[max(1, min(5, lv))])
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        s.set(x, y, IR[5]); s.set(x + 1, y + 1, IR[1])
    g = GLYPHS[key]
    gm = np.zeros((H, W), dtype=bool)
    ox, oy = 3, 4 if key != "g1" else 4
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch == "X":
                gm[oy + j, ox + i] = True
    # stamped recess: the die edge (dark) above-left of each stroke
    for y, x in np.argwhere(gm):
        for dx, dy in ((-1, 0), (0, -1)):
            if not gm[y + dy, x + dx]:
                s.set(x + dx, y + dy, IR[0])
    inner = shrink(gm)
    for y, x in np.argwhere(gm):
        c = MG[6] if inner[y, x] else MG[5]
        if not nb(gm, 0, 1)[y, x] and not inner[y, x]:
            c = MG[4]
        s.set(x, y, c)
    outline(s)
    return s.img


def build_glyphs():
    frames, tags = [], []
    for i, k in enumerate(("g0", "g1", "g2", "g3")):
        frames.append({"ms": 100, "cels": {"Glyph": glyph(k)}})
        tags.append((k, i, i))
    return 16, 16, ["Glyph"], frames, tags
