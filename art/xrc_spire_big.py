"""Big pieces for the Stormward Spire expansion.

xrc_sp_lantern   96x112  loop(4)   the lighthouse lantern room from outside; the lens glow pulses
xrc_sp_colossus  176x304 idle(1)   THE STORMWARDEN: drowned knight statue, waist-deep, dead lantern held high
xrc_sp_seaview   512x216 loop(1)   the open storm sea from high up (tileable, horizon y=128), moon-glade, stacks, wreck

The colossus is modelled as signed-distance parts (numpy), majority-sampled 4x4 for clean silhouettes, shaded from
per-part dome normals into the green-black DROWN ramp, then detailed by hand (seams, lames, cracks, barnacles).
"""
import math, random
import numpy as np
from PIL import Image
from xrc_spire_kit import *   # noqa: F401,F403
from xrc_spire_kit import (Spr, K, T, h01, clamp, bt, ST, SHEEN, GLINT, SALT, SEA, AMBER, RUST, VERD, IRON, WOOD,
                           WHEAT, GRASS, BONE, CLOTH, CANVAS, GLASS, FLAME, VERDR, COPPER, DROWN, SCAR, TAR, DRIFT,
                           outline, flame, thick_line)
from envlib import C, ramp, fbm, vnoise, lerpc, smooth
from spire_props import stone_level
from spire_tiles import BOLT


# =========================================================================== SDF toolkit
def sd_seg(X, Y, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = np.clip(((X - ax) * vx + (Y - ay) * vy) / (vx * vx + vy * vy + 1e-9), 0, 1)
    return np.hypot(X - ax - vx * t, Y - ay - vy * t), t


def sd_cone(X, Y, a, b, ra, rb):
    d, t = sd_seg(X, Y, a, b)
    return d - (ra + (rb - ra) * t)


def sd_ell(X, Y, c, rx, ry, rot=0.0):
    x, y = X - c[0], Y - c[1]
    if rot:
        cr, sr = math.cos(rot), math.sin(rot)
        x, y = x * cr + y * sr, -x * sr + y * cr
    k = np.hypot(x / rx, y / ry)
    return (k - 1) * min(rx, ry)


def sd_poly(X, Y, pts):
    d = np.full(X.shape, 1e9)
    inside = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dd, _ = sd_seg(X, Y, a, b)
        d = np.minimum(d, dd)
        (x0, y0), (x1, y1) = a, b
        cond = (y0 > Y) != (y1 > Y)
        xc = x0 + (Y - y0) * (x1 - x0) / ((y1 - y0) if y1 != y0 else 1e-9)
        inside ^= cond & (X < xc)
    return np.where(inside, -d, d)


# =========================================================================== THE STORMWARDEN
CW, CH = 176, 304
CX = 74                          # the body axis
COL_FIST = (153, 30)             # the raised fist
COL_LANTERN = (164, 74)          # centre of the dead lantern (frame coords)
SWORD_G = (38.0, 246.0)          # sword guard centre
SWORD_D = (-0.40, 0.917)         # blade direction (down-left)


def _col_parts(X, Y):
    """-> list of (name, sdf, R (dome radius), base tone) back to front."""
    P = []
    cx = CX
    # a narrow stone cape streaming off the right shoulder behind the body, torn into points
    cape = sd_poly(X, Y, [(96, 124), (108, 130), (118, 160), (126, 196), (130, 226), (124, 218), (121, 236),
                          (114, 222), (110, 240), (104, 214), (98, 190)])
    P.append(("cape", cape, 8, 2.2))
    P.append(("faulds", sd_poly(X, Y, [(55, 236), (93, 236), (99, 262), (104, 303), (44, 303), (49, 262)]), 16, 3.0))
    P.append(("torso", sd_poly(X, Y, [(52, 116), (62, 110), (86, 110), (96, 116), (104, 130), (104, 150), (97, 180),
                                      (90, 206), (93, 238), (55, 238), (58, 206), (51, 180), (44, 150), (44, 130)]),
              22, 3.6))
    P.append(("belt", sd_poly(X, Y, [(54, 230), (94, 230), (95, 239), (53, 239)]), 3, 2.8))
    P.append(("neck", sd_ell(X, Y, (cx, 110), 12, 8), 8, 3.0))
    helm = np.minimum(sd_ell(X, Y, (cx, 80), 13.5, 21),
                      sd_poly(X, Y, [(61, 84), (87, 84), (83, 100), (74, 110), (65, 100)]))
    helm = np.maximum(helm, -sd_poly(X, Y, [(81, 60), (90, 64), (89, 72), (84, 70), (83, 66)]))   # a shard broken off
    P.append(("helm", helm, 12, 4.2))
    # crest blade + swept temple fins
    P.append(("crest", sd_poly(X, Y, [(71, 63), (77, 61), (81, 50), (82, 40), (79, 30), (78, 42), (74, 53)]), 3, 4.2))
    # the raised arm (viewer's right)
    P.append(("rupper", sd_cone(X, Y, (100, 124), (134, 84), 9.5, 7.5), 8, 3.8))
    P.append(("rfore", sd_cone(X, Y, (134, 84), (148, 46), 7.0, 6.2), 7, 3.9))
    P.append(("rcuff", sd_cone(X, Y, (147, 49), (151, 39), 6.6, 8.0), 5, 4.1))
    P.append(("relbow", sd_ell(X, Y, (134, 85), 7.5, 6.0, 0.9), 5, 4.1))
    P.append(("rfist", sd_poly(X, Y, [(146, 34), (150, 24), (157, 22), (161, 27), (160, 36), (154, 39), (148, 39)]),
              5, 4.4))
    P.append(("rpaul", sd_poly(X, Y, [(88, 116), (98, 108), (112, 106), (122, 112), (124, 122), (116, 122),
                                      (106, 128), (96, 130)]), 7, 4.3))
    # the lowered arm (viewer's left)
    P.append(("lupper", sd_cone(X, Y, (46, 130), (32, 184), 9.0, 7.0), 7, 3.4))
    P.append(("lpaul", sd_poly(X, Y, [(60, 116), (48, 112), (36, 114), (27, 122), (25, 134), (29, 131), (31, 135),
                                      (35, 132), (39, 136), (50, 134), (58, 128)]), 7, 4.1))
    P.append(("lelbow", sd_ell(X, Y, (32, 185), 7.0, 5.8, 0.3), 5, 3.5))
    P.append(("lfore", sd_cone(X, Y, (32, 185), (37, 226), 6.6, 5.8), 7, 3.3))
    P.append(("lcuff", sd_cone(X, Y, (37, 224), (38, 232), 6.0, 7.6), 5, 3.5))
    # the sword: guard below the fist, blade snapped off two-thirds down
    bdx, bdy = SWORD_D
    g0 = SWORD_G
    tip = (g0[0] + bdx * 44, g0[1] + bdy * 44)
    blade = sd_cone(X, Y, g0, tip, 3.9, 3.3)
    u = (X - g0[0]) * bdx + (Y - g0[1]) * bdy
    v = -(X - g0[0]) * bdy + (Y - g0[1]) * bdx
    cut = u - (36 + 3.2 * np.abs(np.sin(v * 1.25)) + 0.8 * v)
    blade = np.maximum(blade, cut)
    P.append(("blade", blade, 3, 3.6))
    P.append(("guard", sd_cone(X, Y, (g0[0] - bdy * 10, g0[1] + bdx * 10), (g0[0] + bdy * 10, g0[1] - bdx * 10),
                               1.8, 1.8), 2, 3.8))
    P.append(("lfist", sd_ell(X, Y, (38, 238), 6.8, 7.2, -0.2), 6, 3.9))
    return P


def colossus():
    SS = 4
    ys, xs = np.mgrid[0:CH * SS, 0:CW * SS]
    Xs, Ys = (xs + 0.5) / SS, (ys + 0.5) / SS
    parts_ss = _col_parts(Xs, Ys)
    union_ss = np.zeros(Xs.shape, bool)
    for _, d, _, _ in parts_ss:
        union_ss |= d < 0
    cover = union_ss.reshape(CH, SS, CW, SS).mean(axis=(1, 3))
    mask = cover >= 0.5
    del parts_ss, union_ss
    ys, xs = np.mgrid[0:CH, 0:CW]
    X, Y = xs + 0.5, ys + 0.5
    parts = _col_parts(X, Y)
    idmap = np.full((CH, CW), -1)
    for i, (_, d, _, _) in enumerate(parts):
        idmap[d < 0.0] = i
    # pixels in the (majority) mask with no centre-sampled part: give them the nearest part
    miss = mask & (idmap < 0)
    if miss.any():
        best = np.full((CH, CW), 1e9)
        for i, (_, d, _, _) in enumerate(parts):
            sel = miss & (d < best)
            idmap[sel] = i
            best = np.where(sel, d, best)
    idmap[~mask] = -1
    # shading from dome normals
    L = np.array([-0.55, -0.62, 0.56])
    L /= np.linalg.norm(L)
    val = np.zeros((CH, CW))
    for i, (name, d, R, base) in enumerate(parts):
        h = np.sqrt(np.clip(-d / R, 0, 1))
        gy, gx = np.gradient(h)
        nx, ny, nz = -gx * R * 0.9, -gy * R * 0.9, np.ones_like(h)
        nn = np.sqrt(nx * nx + ny * ny + nz * nz)
        dif = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / nn, 0, 1)
        v = base - 1.8 + dif * 3.8
        if name in ("torso", "faulds", "belt", "neck", "helm"):
            v = v - (X - CX) / 30.0 * 0.9                 # the body turns away from the light on the right
        sel = idmap == i
        val[sel] = v[sel]
    # atmosphere: darker and wetter toward the sea, a touch of sky light at the top
    val += np.clip((140 - Y) / 140, -1, 1) * 0.6 - np.clip((Y - 230) / 70, 0, 1) * 1.0
    # ---- bevel seams between parts: the front part's edge is lit on its upper-left, cut dark on its lower-right
    order = idmap.copy()
    seam = np.zeros((CH, CW))
    for (dx, dy, amt) in ((1, 0, -1.6), (0, 1, -1.8), (-1, 0, 0.9), (0, -1, 1.0)):
        nb = np.full((CH, CW), -1)
        sx0, sx1 = max(0, dx), CW + min(0, dx)
        sy0, sy1 = max(0, dy), CH + min(0, dy)
        nb[sy0 - dy:sy1 - dy, sx0 - dx:sx1 - dx] = order[sy0:sy1, sx0:sx1]
        edge = (order >= 0) & (nb >= 0) & (nb < order)
        seam = np.where(edge & (seam == 0), amt, seam)
    val += seam
    names = [p[0] for p in parts]

    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    px = img.load()
    for y in range(CH):
        for x in range(CW):
            if idmap[y, x] >= 0:
                px[x, y] = DROWN[int(clamp(round(val[y, x]), 1, 9))]
    s = Spr(CW, CH)
    s.img, s.px = img, px

    def v_at(x, y):
        return idmap[int(y), int(x)] if 0 <= int(x) < CW and 0 <= int(y) < CH else -1

    def shade(x, y, dv):
        x, y = int(x), int(y)
        if 0 <= x < CW and 0 <= y < CH and idmap[y, x] >= 0:
            c = px[x, y]
            i = DROWN.index(c) if c in DROWN else 4
            px[x, y] = DROWN[int(clamp(i + dv, 0, 10))]

    def on(name, x, y):
        i = v_at(x, y)
        return i >= 0 and names[i] == name

    # ---- carved detail
    cx = CX
    # breastplate keel ridge + a pectoral line, the plackart over the belly
    for y in range(114, 230):
        if on("torso", cx, y):
            shade(cx - 1, y, +1)
            shade(cx + 1, y, -1)
    for side in (-1, 1):
        for i in range(40):
            a = i / 39
            x = cx + side * (2 + a * 25)
            y = 150 - 10 * a * a + (2 if side > 0 else 0) * a
            if on("torso", x, y):
                shade(x, y, -2)
                shade(x, y - 1, +1)
    for i in range(60):                                   # plackart: a pointed arch rising from the belt
        a = (i / 59) * 2 - 1
        x = cx + a * 17
        y = 229 - 30 * (1 - abs(a)) ** 0.8
        if on("torso", x, y):
            shade(x, y, -2)
            shade(x, y - 1, +1)
    # fauld lames (a slight sag), split at the centre
    for k in range(6):
        yl = 248 + k * 10
        for x in range(36, 112):
            y = yl + 2.0 * math.sin((x - 44) / 60 * math.pi)
            if on("faulds", x, y):
                shade(x, y, -2)
                shade(x, y + 1, +1)
    for y in range(240, 304):
        if on("faulds", cx, y):
            shade(cx, y, -2)
            shade(cx - 1, y, +1)
    # belt buckle
    for y in range(231, 238):
        shade(cx - 3, y, +2)
        shade(cx + 3, y, -1)
    for x in range(cx - 3, cx + 4):
        shade(x, 231, +2)
        shade(x, 237, -1)
    # pauldron lames: two plates stepping down under each
    for (pts, nm) in (([(28, 126), (38, 122), (50, 122), (58, 124)], "lpaul"),
                      ([(26, 131), (36, 128), (48, 129), (56, 130)], "lpaul"),
                      ([(92, 122), (102, 116), (114, 114), (122, 117)], "rpaul"),
                      ([(96, 127), (106, 121), (116, 120), (123, 121)], "rpaul")):
        for a_, b_ in zip(pts, pts[1:]):
            n = int(max(abs(b_[0] - a_[0]), abs(b_[1] - a_[1]))) + 1
            for i in range(n):
                t = i / n
                x, y = a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t
                if on(nm, x, y):
                    shade(x, y, -2)
                    shade(x, y - 1, +1)
    # vambrace cuffs + rerebrace bands
    for (a_, b_, nm, tts) in (((134, 84), (148, 46), "rfore", (0.5,)), ((32, 185), (37, 226), "lfore", (0.5,)),
                              ((100, 124), (134, 84), "rupper", (0.5,)), ((46, 130), (32, 184), "lupper", (0.5,))):
        for tt in tts:
            mx, my = a_[0] + (b_[0] - a_[0]) * tt, a_[1] + (b_[1] - a_[1]) * tt
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]
            Ln = math.hypot(dx, dy)
            px_, py_ = -dy / Ln, dx / Ln
            for j in range(-9, 10):
                if on(nm, mx + px_ * j, my + py_ * j):
                    shade(mx + px_ * j, my + py_ * j, -2)
                    shade(mx + px_ * j - dx / Ln, my + py_ * j - dy / Ln, +1)
    # the helm: visor slit, breaths, a lit centre ridge
    for x in range(58, 92):
        for y in (83, 84):
            if on("helm", x, y):
                px[x, y] = DROWN[0]
        if on("helm", x, 85):
            shade(x, 85, +1)
        if on("helm", x, 82):
            shade(x, 82, -1)
    for bx in (68, 71, 77, 80):
        for y in range(90, 97):
            if on("helm", bx, y) and y - 90 < 7 - abs(bx - 74) // 2:
                px[bx, y] = DROWN[1]
    for y in range(60, 83):
        if on("helm", cx, y):
            shade(cx - 1, y, +1)
            shade(cx + 1, y, -1)
    for i in range(9):
        x, y = 149 + i * 1.1, 26 + i * 0.1
        if on("rfist", x, y):
            shade(x, y, -2)
    # sword fuller
    g0 = SWORD_G
    for i in range(6, 32):
        x, y = g0[0] + SWORD_D[0] * i, g0[1] + SWORD_D[1] * i
        if on("blade", x, y):
            shade(x, y, -2)
            shade(x - 1, y, +1)
    # cape folds
    for (x0, y0, x1, y1) in ((104, 134, 112, 212), (110, 140, 120, 222), (100, 150, 104, 196)):
        n = int(abs(y1 - y0)) + 1
        for i in range(n):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if on("cape", x, y):
                shade(x, y, -1)
                shade(x - 1, y, +1)
    # ---- rain streaks (darker wet runs below ledges)
    for x in range(CW):
        if h01(x, 0, 91) < 0.14:
            y0 = int(h01(x, 1, 92) * 180) + 70
            for y in range(y0, min(CH, y0 + 8 + int(h01(x, 2, 93) * 30))):
                if idmap[y, x] >= 0 and px[x, y] != DROWN[0]:
                    shade(x, y, -1)
    # ---- barnacle crusts, only near the sea and on the low hand/sword
    rnd = random.Random(5)
    for i in range(34):
        y = int(CH - 8 - (rnd.random() ** 1.5) * 70)
        x = rnd.randint(34, 110)
        if v_at(x, y) < 0:
            continue
        for (dx, dy, dv) in ((0, 0, 2), (1, 0, 1), (0, 1, -2), (1, 1, -2)):
            shade(x + dx, y + dy, dv)
    for (x, y) in ((33, 236), (41, 243), (30, 262), (45, 232), (36, 214)):
        shade(x, y, 2)
        shade(x, y + 1, -2)
    # ---- lightning-scar cracks with a faint pale glow (restrained: mostly the dim tone)
    cracks = [
        [(84, 70), (80, 74), (82, 78), (78, 82)],
        [(66, 64), (70, 70), (68, 74), (72, 79)],
        [(64, 120), (69, 127), (66, 133), (72, 142), (70, 149), (76, 158), (73, 166), (78, 176)],
        [(70, 149), (64, 156), (65, 162)],
        [(124, 98), (128, 92), (127, 87), (133, 79), (138, 70), (136, 64), (142, 55)],
        [(58, 246), (63, 252), (60, 258), (65, 266)],
    ]
    for pts in cracks:
        cells = []
        for a_, b_ in zip(pts, pts[1:]):
            n = int(max(abs(b_[0] - a_[0]), abs(b_[1] - a_[1]))) + 1
            for i in range(n):
                t = i / n
                cells.append((round(a_[0] + (b_[0] - a_[0]) * t), round(a_[1] + (b_[1] - a_[1]) * t)))
        cells.append(pts[-1])
        for (x, y) in cells:
            if v_at(x, y) >= 0:
                shade(x + 1, y, -1)
        for j, (x, y) in enumerate(cells):
            if v_at(x, y) >= 0:
                px[x, y] = SCAR[1] if j % 6 == 3 else SCAR[0]
    # ---- the chain and the dead lantern (iron)
    L_ = Spr(CW, CH)
    fx, fy = COL_FIST
    lx, ly = COL_LANTERN
    top_ring = (lx, 50)
    n = 8
    for i in range(n + 1):
        t = i / n
        x = fx + 2 + (top_ring[0] - fx - 2) * t
        y = fy + 7 + (top_ring[1] - fy - 7) * t
        if i % 2 == 0:
            L_.set(x, y, IRON[3])
            L_.set(x + 1, y, IRON[2])
            L_.set(x, y + 1, IRON[2])
        else:
            L_.set(x, y, IRON[4])
    # cap (a pointed hood with a finial ring)
    for y in range(50, 62):
        hw = (y - 50) / 11 * 10.5
        for x in range(int(lx - hw), int(lx + hw) + 1):
            lit = (x - lx) / max(hw, 1)
            L_.set(x, y, IRON[int(clamp(3.0 - lit * 1.6 - (y - 50) * 0.05, 1, 4))])
    for x in range(lx - 12, lx + 13):
        L_.set(x, 62, IRON[4] if x < lx + 4 else IRON[2])
        L_.set(x, 63, IRON[1])
    L_.set(lx, 49, IRON[4])
    L_.set(lx, 48, IRON[3])
    # the cage: four bars (the middle two foreshortened), dark empty panes, broken glass shards
    for y in range(64, 87):
        for x in range(lx - 10, lx + 11):
            rel = x - lx
            if rel in (-10, -9):
                c = IRON[4] if rel == -10 else IRON[3]
            elif rel in (9, 10):
                c = IRON[2] if rel == 9 else IRON[1]
            elif rel in (-4, 4):
                c = IRON[3] if rel < 0 else IRON[2]
            else:
                c = GLASS[0] if (x + y) % 7 else ST[1]
                if rel < -4 and y < 70 and y - 64 < (-4 - rel):
                    c = GLASS[2]                          # a shard left in the frame
                if rel > 4 and y > 80:
                    c = GLASS[1]
            L_.set(x, y, c)
    for x in range(lx - 11, lx + 12):
        L_.set(x, 75, IRON[3] if x < lx else IRON[2])
    # the burner inside: a dead black cup
    for x in range(lx - 2, lx + 3):
        L_.set(x, 82, IRON[2])
        L_.set(x, 83, IRON[1])
    # base + drop finial
    for y in range(87, 93):
        hw = 11 - (y - 87) * 1.2
        for x in range(int(lx - hw), int(lx + hw) + 1):
            L_.set(x, y, IRON[int(clamp(3.8 - (x - lx) / max(hw, 1) * 1.6 - (y - 87) * 0.3, 1, 5))])
    for y in range(93, 99):
        L_.set(lx, y, IRON[3] if y < 97 else IRON[2])
    L_.set(lx - 1, 95, IRON[3])
    L_.set(lx + 1, 95, IRON[2])
    for (x, y) in ((lx - 7, 62), (lx + 6, 88), (lx - 10, 80)):
        L_.set(x, y, RUST[3])
        L_.set(x, y + 1, RUST[2])
    L_.outline()
    s.img.alpha_composite(L_.img)
    s.px = px = s.img.load()
    # ---- outline the statue (softened: the darkest sea-stone, not ink)
    s.img = outline(s.img, DROWN[0])
    s.px = px = s.img.load()
    # rim light: cold sky light on the upper-left silhouette edges
    for y in range(1, CH - 20):
        for x in range(1, CW - 1):
            if idmap[y, x] >= 0 and idmap[y - 1, x] < 0 and idmap[y, x - 1] < 0:
                shade(x, y, +2)
            elif idmap[y, x] >= 0 and (idmap[y - 1, x] < 0 or idmap[y, x - 1] < 0):
                if px[x, y] != DROWN[0]:
                    shade(x, y, +1)
    # ---- the waterline: the stone dissolves into foam and surf across the bottom rows
    rnd = random.Random(9)
    for x in range(CW):
        top = CH - 10 + 3 * math.sin(x * 0.21) + 2 * math.sin(x * 0.53 + 1)
        inside = any(idmap[y, x] >= 0 for y in range(CH - 30, CH))
        if not inside and not (24 < x < 128):
            continue
        for y in range(int(top), CH):
            d = y - top
            if inside or d > 2:
                c = SEA[9] if d < 1.5 else SEA[8] if d < 3.5 else SEA[6] if d < 6 else SEA[4]
                if (x * 3 + y) % 7 == 0 and d < 4:
                    c = SEA[10]
                s.set(x, y, c)
        # foam lace creeping up the stone
        if inside:
            for k in range(int(3 + 5 * h01(x, 0, 51))):
                y = int(top) - k
                if 0 <= y < CH and idmap[y, x] >= 0 and h01(x, y, 52) < 0.55 - k * 0.07:
                    s.set(x, y, SEA[8] if k > 1 else SEA[9])
    for i in range(26):                                        # spray thrown up against the statue
        x = rnd.randint(36, 124)
        y = CH - 12 - int(rnd.random() ** 2 * 18)
        s.set(x, y, SEA[9] if i % 3 else SEA[10])
    return CW, CH, ["Stormwarden"], [{"ms": 1000, "cels": {"Stormwarden": s.img}}], [("idle", 0, 0)]


# =========================================================================== lighthouse lantern room
LAN_LENS = (48, 60)              # lens centre (the light source), frame coords


def lantern():
    Wd, Hd = 96, 112
    cx = 48
    GX0, GX1, GY0, GY1 = 20, 75, 39, 78          # glazing
    frames = []
    for f in range(4):
        k = [0, 1, 2, 1][f]                      # glow pulse
        s = Spr(Wd, Hd)
        # ---- gallery deck, corbels and the tower top below
        for y in range(98, 112):
            for x in range(16, 80):
                sl = stone_level(x + 2, y - 98, 8, 5, 21)
                lv = 6.0 - (x - 16) / 64 * 2.4
                lv = 2 if sl is None else lv + sl * 0.7
                if y < 101:
                    lv -= 1.6                                # under the deck
                s.set(x, y, ST[int(clamp(lv, 1, 9))])
        for cxr in range(8, 92, 10):                         # corbels
            for y in range(98, 105):
                w = 3 - (y - 98) // 3
                for x in range(cxr - w, cxr + w + 1):
                    if 0 <= x < Wd:
                        s.set(x, y, ST[6 if x < cxr else 4] if y < 104 else ST[3])
        for y in range(93, 98):
            for x in range(3, 93):
                lv = [9.2, 7.5, 6, 4.6, 2.8][y - 93] - (x - 3) / 90 * 1.6
                if (x - 3) % 15 == 0 and y > 93:
                    lv = 2
                s.set(x, y, ST[int(clamp(lv, 1, 10))])
        for x in range(34, 62):                              # the lens light pooling on the wet deck
            if h01(x, 0, 12) < 0.35 + 0.1 * k:
                s.set(x, 93, AMBER[2] if abs(x - cx) < 6 + k else AMBER[1])
        # ---- the lantern room's pedestal (iron-bound stone)
        for y in range(79, 93):
            for x in range(GX0 - 1, GX1 + 2):
                lv = 6.2 - (x - GX0) / (GX1 - GX0) * 2.6
                if y == 79:
                    lv += 2
                elif y == 80:
                    lv -= 1.6
                if (x - GX0 + 1) in (0, 16, 40, 56) or x == GX1 + 1:
                    lv -= 1.5                                    # the octagon's corners
                s.set(x, y, ST[int(clamp(lv, 1, 10))])
        for (vx, vy) in ((28, 85), (44, 85), (52, 85), (66, 85)):  # vent grilles
            for i in range(4):
                s.set(vx + i, vy, IRON[1])
                s.set(vx + i, vy + 2, IRON[1])
                s.set(vx + i, vy + 1, IRON[3] if i % 2 else IRON[2])
        # ---- glazing: three faces of the octagon, dark storm glass, the great lens behind
        faces = [(GX0, 35, -1), (36, 59, 0), (60, GX1, 1)]
        for y in range(GY0, GY1 + 1):
            for x in range(GX0, GX1 + 1):
                face = 0 if x < 36 else (1 if x < 60 else 2)
                dx, dy = (x + 0.5 - LAN_LENS[0]) / 15.5, (y + 0.5 - LAN_LENS[1]) / 17.5
                rr = dx * dx + dy * dy
                # beehive lens outline (slightly narrower at the top)
                lens_hw = 15.5 * math.sqrt(max(0, 1 - ((y + 0.5 - LAN_LENS[1]) / 17.5) ** 2)) * (0.86 + 0.14 * (y > LAN_LENS[1]))
                in_lens = abs(x + 0.5 - LAN_LENS[0]) <= lens_hw and GY0 + 3 <= y <= GY1 - 1
                if in_lens:
                    ry_ = y - LAN_LENS[1]
                    ring = abs(ry_)
                    if ring <= 4:                                 # the central bull's-eye drum
                        lv = 4.2 + k * 0.4 - abs(dx) * 1.6
                        if abs(dx) < 0.18 and ring <= 2:
                            lv = 5
                    else:
                        band = (ring - 5) % 4                      # prism rings
                        lv = 3.6 + k * 0.35 - abs(dx) * 1.8 - (ring - 4) * 0.07
                        if band == 3:
                            lv -= 1.4
                        elif band == 0:
                            lv += 0.5
                    if face != 1:
                        lv -= 0.6                                  # seen through the angled panes
                    c = AMBER[int(clamp(lv, 1, 5))]
                else:
                    warm = rr < 1.28 + 0.12 * k and face == 1
                    if warm:
                        c = AMBER[1] if rr < 1.1 + 0.1 * k else AMBER[0]
                    else:
                        c = GLASS[1] if face != 2 else GLASS[0]
                        if face == 0 and (x - y) % 11 == 0:
                            c = GLASS[2]                               # a cold reflection on the lit side
                s.set(x, y, c)
        # the lens' brass frame ribs (vertical) and pedestal
        for rx in (-9, 0, 9):
            for y in range(GY0 + 4, GY1):
                if s.get(cx + rx, y) in AMBER:
                    s.set(cx + rx, y, AMBER[1] if rx else AMBER[2])
        for x in range(cx - 6, cx + 7):
            s.set(x, GY1, WOOD[2])
        # mullions + astragals (iron)
        for mx in (GX0, 35, 36, 59, 60, GX1):
            for y in range(GY0, GY1 + 1):
                s.set(mx, y, IRON[4] if mx in (GX0, 36, 60) else IRON[2])
        for mx in (28, 44, 52, 68):
            for y in range(GY0, GY1 + 1):
                s.set(mx, y, IRON[3] if s.get(mx, y) not in AMBER else IRON[2])
        for ay in (52, 65):
            for x in range(GX0, GX1 + 1):
                s.set(x, ay, IRON[4] if x < 60 else IRON[2])
        for x in range(GX0, GX1 + 1):
            s.set(x, GY0, IRON[5] if x < 60 else IRON[3])
            s.set(x, GY1, IRON[3])
        # rain on the panes: short cold streaks
        for (rx_, ry_) in ((24, 42), (31, 55), (40, 44), (57, 69), (64, 46), (71, 58), (48, 71)):
            for i in range(3):
                if s.get(rx_ + i // 2, ry_ + i) not in (IRON[2], IRON[3], IRON[4], IRON[5]):
                    s.set(rx_ + i // 2, ry_ + i, SHEEN[1] if i == 0 else SHEEN[2])
        # ---- the copper roof: a flared dome with ribs, verdigris runs, a vent ball and the lightning spike
        RY0, RY1 = 18, 36
        for y in range(RY0, RY1 + 1):
            t = (y - RY0) / (RY1 - RY0)
            hw = 3 + 31 * (1 - (1 - t) ** 2) ** 0.75
            for x in range(int(cx - hw), int(cx + hw) + 1):
                u = (x + 0.5 - cx) / hw                             # -1..1 across
                lv = 4.0 - u * 2.2 - abs(u) ** 3 * 0.6 + (1 - t) * 0.6
                ph = math.asin(clamp(u, -1, 1))
                rib = abs((ph / (math.pi / 10)) - round(ph / (math.pi / 10))) < 0.09 * (1 + 1 / (hw * 0.2))
                if rib:
                    lv += 1.1 if u < 0.2 else 0.4
                c = VERDR[int(clamp(lv - 1.0, 1, 4))]
                if not rib and h01(int(ph * 24), 0, 7) < 0.25 and t > 0.45 + 0.4 * h01(int(ph * 24), 1, 8):
                    c = COPPER[int(clamp(lv - 1.6, 0, 3))]            # bare copper where the verdigris has run
                s.set(x, y, c)
        for x in range(cx - 35, cx + 36):                          # eave band
            s.set(x, 37, VERDR[5] if x < cx + 12 else VERDR[3])
            s.set(x, 38, COPPER[1] if abs(x - cx) > 22 - 4 * k else AMBER[1])
        for (sx_, dirx) in ((cx - 35, -1), (cx + 35, 1)):          # gutter spouts
            s.set(sx_ + dirx, 37, VERDR[4])
            s.set(sx_ + 2 * dirx, 38, VERDR[3])
        for (dx, dy, c) in ((-2, 0, VERDR[5]), (-1, -1, VERDR[6]), (0, -1, VERDR[5]), (1, -1, VERDR[4]),
                            (-1, 0, VERDR[5]), (0, 0, VERDR[4]), (1, 0, VERDR[3]), (2, 0, VERDR[2]),
                            (-1, 1, VERDR[3]), (0, 1, VERDR[2]), (1, 1, VERDR[1]), (-2, -1, VERDR[4]),
                            (2, -1, VERDR[3]), (0, -2, VERDR[4]), (-1, -2, VERDR[5]), (1, -2, VERDR[3])):
            s.set(cx + dx, 16 + dy, c)                              # the vent ball
        for y in range(1, 14):
            s.set(cx, y, IRON[4] if y > 3 else IRON[5])
            if y > 6:
                s.set(cx + 1, y, IRON[2])
        s.set(cx - 1, 9, IRON[3])
        s.set(cx + 1, 5, IRON[3])                                   # the rod's barbs
        s.set(cx, 0, BOLT[1])
        # ---- the gallery railing (open ironwork in front of the pedestal)
        rail = Spr(Wd, Hd)
        for x in range(4, 92):
            rail.set(x, 81, IRON[5] if x < 70 else IRON[4])
            rail.set(x, 82, IRON[2])
            rail.set(x, 87, IRON[3])
        for i, x in enumerate(range(4, 93, 6)):
            for y in range(81, 93):
                rail.set(x, y, IRON[4] if i % 3 else IRON[5])
            if i % 3 == 0:
                rail.set(x, 80, IRON[5])
                rail.set(x - 1, 81, IRON[4])
                rail.set(x + 1, 81, IRON[3])
            if h01(i, 0, 5) < 0.3:
                rail.set(x, 90, RUST[3])
                rail.set(x, 91, RUST[2])
        s.outline()
        s.img.alpha_composite(rail.img)
        s.px = s.img.load()
        # outline only the railing's outer ends and top so it stays open
        for x in (3, 92):
            for y in range(80, 93):
                if s.get(x, y)[3] == 0:
                    s.set(x, y, K)
        s.set(cx - 1, 1, BOLT[2] if f == 2 else None)
        frames.append({"ms": [220, 180, 260, 180][f], "cels": {"Lantern": s.img}})
    return Wd, Hd, ["Lantern"], frames, [("loop", 0, 3)]


# =========================================================================== the open storm sea (vista parallax)
SV_W, SV_H, SV_HZ = 512, 216, 128
SV_MOON_X = 300                  # axis of the moon-glade (under the cloud break of the sky layer)
# horizon haze (violet, as the sky's low band) -> black water
VSEA = ramp("05070d", "080b13", "0b0f19", "0f1420", "131927", "181f30", "1e2539", "252c43", "2d334d", "363b57",
            "414561")
MOON = ramp("3a4866", "4e6080", "6a80a0", "90a8c4", "bcd0e2", "e6f2fa")
STACK = ramp("0e0f19", "151623", "1c1d2e", "24253a", "3c4260", "5a6484")
SV_FOAM = [C("4e6680"), C("7a94ae"), C("a8c0d4")]
RAIN = (150, 166, 192)


def _wdx(x, cx):
    d = (x - cx) % SV_W
    return d - SV_W if d > SV_W / 2 else d


def _tn(x, y, sx, sy, seed):
    return vnoise(x, y, sx, sy, seed, SV_W // sx)


def _tnr(x, y, sx, seed):
    """tileable 1-D-ish noise with any desired cell size (snapped so a whole number of cells spans 512)."""
    n = max(1, int(round(SV_W / sx)))
    return vnoise(x, y, SV_W / n, 1, seed, n)


def seaview():
    W, H, HZ = SV_W, SV_H, SV_HZ
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    B4 = bt
    # ------------------------------------------------------------------ the water
    def glade(x, d):
        gw = 9 + d * 0.78
        gx = _wdx(x, SV_MOON_X) / gw
        return math.exp(-gx * gx * 1.7)

    for y in range(HZ, H):
        d = y - HZ + 0.5                                   # rows below the horizon
        t = d / (H - HZ)
        wscale = 1.0 + d * 0.07                              # horizontal feature scale grows toward the viewer
        amp = smooth(2.0, 26.0, d)                           # swells resolve out of the haze
        for x in range(W):
            g = glade(x, d)
            # long swells: crest rows spread out toward the viewer, undulating left-right
            wig = (_tn(x, d * 0.3, 64, 1, 3) - 0.5) * 2.0 + (_tn(x, d * 0.15, 128, 1, 4) - 0.5) * 3.0
            ph = 1.62 * math.sqrt(d) + wig * 0.3
            fr = ph - math.floor(ph)                          # 0..1 across one swell (crest at 0)
            wave = math.cos(2 * math.pi * fr)
            shade = (_tn(x, d * 0.5, 128, 12, 9) - 0.5) * 1.6   # cloud shadow drifting over the water
            v = 7.4 - 6.0 * t ** 0.55 + shade * (1 - g) * min(1, d / 16)
            v += wave * 1.1 * amp
            v += g * (2.0 - 1.0 * t)
            vi = int(clamp(v, 0, 10))
            if v - vi > bt(x, y):
                vi += 1
            c = VSEA[min(10, vi)]
            lip = 0.06 + 0.05 * amp
            dash = _tnr(x, math.floor(ph) * 7.3, 16 * wscale, 11)
            if (fr < lip or fr > 0.985) and d > 1.5 and dash > 0.35:
                c = VSEA[min(10, vi + 2)]                     # the lit lip of the swell
                if g > 0.2:
                    c = MOON[int(clamp(g * 5.4 - 0.8 + (dash - 0.5) * 2.5, 0, 5))]
            elif lip <= fr < lip + 0.09 and amp > 0.4:
                c = VSEA[max(0, vi - 2)]                      # the shadowed back just beyond the lip
            elif g > 0.12:
                # the glade's own chop: short horizontal glints on small ripples, stretched in x
                ph2 = 5.2 * math.sqrt(d) + (_tn(x, d, 32, 2, 13) - 0.5) * 1.4
                f2 = ph2 - math.floor(ph2)
                d2 = _tnr(x, math.floor(ph2) * 3.1, 8 * wscale / 1.5, 17)
                if f2 < 0.22 and d2 > 0.62 - g * 0.3:
                    c = MOON[int(clamp(g * 4.4 + (d2 - 0.6) * 4 - 0.4, 0, 5))]
            px[x, y] = c
    # a few brightest sparkles in the heart of the glade
    rnd = random.Random(21)
    for i in range(160):
        y = HZ + 1 + int(rnd.random() ** 1.3 * (H - HZ - 1))
        d = y - HZ + 0.5
        x = int(SV_MOON_X + rnd.gauss(0, (9 + d * 0.78) * 0.4)) % W
        if px[x, y] in MOON[3:]:
            px[x, y] = MOON[5]
    # sparse whitecaps on the nearer water, away from the glade
    for i in range(46):
        y = HZ + 24 + int(rnd.random() ** 0.8 * (H - HZ - 26))
        d = y - HZ
        x = rnd.randrange(W)
        if glade(x, d) > 0.15:
            continue
        L = 2 + int(d / 26 + rnd.random() * 2)
        for j in range(L):
            px[(x + j) % W, y] = SV_FOAM[0] if j in (0, L - 1) else SV_FOAM[1]
    # the horizon: a thin haze line, silver under the break
    for x in range(W):
        g = math.exp(-(_wdx(x, SV_MOON_X) / 16) ** 2)
        px[x, HZ] = MOON[int(clamp(g * 5.5, 0, 5))] if g > 0.18 else VSEA[9]
        if g > 0.45:
            px[x, HZ + 1] = MOON[int(clamp(g * 4.2, 0, 5))]
    # ------------------------------------------------------------------ distant sea stacks (above the horizon)
    from spire_props import point_in_poly as pip
    stacks = [
        # a tall leaning pillar with a notch, and its broken twin
        [(34, 128), (35, 116), (36, 104), (38, 95), (37, 90), (40, 86), (43, 87), (44, 91), (46, 89), (48, 93),
         (48, 100), (50, 107), (51, 117), (53, 128)],
        [(56, 128), (57, 119), (59, 113), (62, 112), (63, 117), (65, 128)],
        # a squat pair
        [(117, 128), (118, 121), (120, 116), (123, 115), (124, 118), (127, 117), (129, 121), (131, 128)],
        [(137, 128), (138, 124), (141, 122), (143, 125), (144, 128)],
        # the great arch stack: two pinnacles over a sea arch
        [(370, 128), (372, 120), (375, 112), (377, 104), (379, 100), (378, 96), (381, 93), (384, 95), (386, 101),
         (389, 104), (393, 103), (395, 99), (398, 98), (400, 102), (402, 108), (407, 113), (411, 117), (415, 122),
         (418, 128)],
        [(466, 128), (468, 121), (470, 117), (473, 116), (475, 119), (477, 123), (479, 128)],
        [(207, 128), (209, 125), (212, 124), (215, 126), (216, 128)],
    ]
    arch = [(388, 129), (389, 123), (392, 119), (396, 120), (398, 124), (399, 129)]
    for poly in stacks:
        xs_ = [p_[0] for p_ in poly]
        top = min(p_[1] for p_ in poly)
        mid = sum(xs_) / len(xs_)
        toward = 1 if mid < SV_MOON_X else -1
        for y in range(top, HZ + 1):
            row = [x for x in range(min(xs_), max(xs_) + 1) if pip(x + 0.5, y + 0.5, poly) and not pip(x + 0.5, y + 0.5, arch)]
            if not row:
                continue
            l_, r_ = row[0], row[-1]
            for x in row:
                u = (x - l_) / max(1, r_ - l_)
                lit = u if toward > 0 else 1 - u
                c = STACK[2] if lit > 0.55 + 0.15 * (_tn(y * 4, top, 16, 1, 31) - 0.5) else STACK[1]
                ledge = h01(top, y, 33) < 0.16 and y > top + 3
                if ledge and lit > 0.35 + 0.4 * h01(top, y, 34):
                    c = STACK[0]                               # a bedding ledge, part-way across
                px[x % W, y] = c
            edge = r_ if toward > 0 else l_
            if y > top + 1:
                px[edge % W, y] = STACK[4] if h01(edge, y, 35) < 0.3 else STACK[3]
            if y <= top + 1:                                   # a crown catching the light
                for x in row:
                    px[x % W, y] = STACK[3]
        for j in range(min(xs_) - 2, max(xs_) + 3):         # surf at the foot
            if rnd.random() < 0.6:
                px[j % W, HZ + (1 if rnd.random() < 0.5 else 0)] = SV_FOAM[0 if rnd.random() < 0.5 else 1]
    # ------------------------------------------------------------------ the wreck, ribs black against the glade
    wx, wy = 278, HZ + 4
    for i in range(11):
        rx = wx + i * 3.3
        h = 6 + 8 * math.sin(math.pi * (i + 0.5) / 11) - (5 if i in (3, 8) else 0) - (3 if i == 10 else 0)
        for j in range(int(h) + 1):
            tt = j / max(h, 1)
            x = rx - 2.0 * tt * tt * (1 if i < 6 else -1)
            px[int(round(x)) % W, wy - j] = STACK[0] if j < h - 1 else STACK[1]
            if tt > 0.35 and i >= 6 and j % 2 == 0:
                px[(int(round(x)) + 1) % W, wy - j] = STACK[3]          # moonlit edge
    for x in range(wx - 3, wx + 36):                                    # the keel, awash
        px[x % W, wy + 1] = STACK[0]
        px[x % W, wy] = STACK[0] if 0 <= x - wx < 34 else px[x % W, wy]
        if x % 4 == 0:
            px[x % W, wy + 2] = SV_FOAM[1]
    for j in range(26):                                                 # the broken mast, leaning, a yard aslant
        px[int(round(wx + 14 - j * 0.3)) % W, wy - j] = STACK[0]
    for j in range(12):
        px[int(round(wx + 4 + j)) % W, wy - 20 + int(j * 0.4)] = STACK[1]
    for j in range(6):                                                  # a rag of sail still on it
        px[int(round(wx + 12 + j * 0.3)) % W, wy - 17 + j] = STACK[1]
    # ------------------------------------------------------------------ rain curtains over the far water
    veils = [(84, 58, 60, 1), (190, 40, 74, 2), (452, 64, 54, 3)]
    for (vx, vw, vtop, seed) in veils:
        for x0 in range(vx - vw, vx + vw):
            if _tn(x0 * 3, 0, 4, 1, seed) < 0.45 or (x0 % 2):
                continue
            edge = 1 - abs(x0 - vx) / vw
            top = vtop + int(10 * _tn(x0, 1, 16, 1, seed + 5))
            for y in range(top, HZ):
                x = x0 + (y - top) * 0.22                    # slanting downwind
                a = int(clamp(edge * 1.6, 0, 1) * clamp((y - top) / 30, 0, 1) * (26 + 22 * _tn(x0, y, 8, 4, seed + 9)))
                if a < 6:
                    continue
                X_ = int(x) % W
                if px[X_, y][3] == 255:
                    continue                                 # never over the opaque stacks
                px[X_, y] = RAIN + (a,)
            # where it falls on the water: the far water hazes a tone lighter
            xb = int(x0 + (HZ - top) * 0.22) % W
            for y in range(HZ + 1, HZ + 7):
                if edge > 0.3 and px[xb, y] in VSEA and (y + xb) % 2 == 0:
                    px[xb, y] = VSEA[min(10, VSEA.index(px[xb, y]) + 1)]
    return W, H, ["Sea"], [{"ms": 1000, "cels": {"Sea": img}}], [("loop", 0, 0)]
