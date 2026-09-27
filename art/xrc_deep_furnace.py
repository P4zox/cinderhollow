"""THE HEART-FURNACE (xrc_dp_furnace, 176x192, idle 4 loop, bottom-anchored).

Two layers: `Fire` (the churning molten light inside the great arched mouth -- the only part that animates) under
`Furnace` (everything else, static, with a hole where the mouth is and the coal bed silhouetted in front of the fire).
"""
import math
import numpy as np
from xrc_deep_lib import (Spr, ss_mask, ell, rect, poly, capsule, union, minus, inter, nb, bevel, shrink, grow,
                          outline, chain_v, chain_line, ST, MG, IR, GD, CH, ASH, RU, LE, WD, HS, K, KH, T, h01)

W, H = 176, 192
MX, MY, MR = 88.0, 130.0, 29.0        # mouth arch centre + radius (opening x 59..116, arch top y 101)
MBOT = 163                            # mouth floor (the hearth lip)
TAU = 2 * math.pi

# exported for the engine
MOUTH_CENTER = (88, 134)
MOUTH_SIZE = (58, 62)


def mouth_mask():
    return ss_mask(W, H, union(ell(MX, MY, MR, MR), rect(MX - MR, MY, MX + MR - 1, MBOT)))


def heat_at(x, y):
    d = math.hypot((x - MX) / 1.15, y - (MY + 12))
    return max(0.0, 1.0 - d / 58.0)


def masonry(s, m, course_h, widths, seed, y_origin=0, base=4):
    """Heat-scorched basalt blocks inside m. Faces warm up and joints glow near the mouth."""
    bv = bevel(m)
    for y, x in np.argwhere(m):
        ci = (y - y_origin) // course_h
        ly = (y - y_origin) % course_h
        bw = widths[ci % len(widths)]
        off = int(h01(ci, 0, seed) * bw)
        lx = (x + off) % bw
        bi = (x + off) // bw
        hh = heat_at(x, y)
        if ly == course_h - 1 or lx == 0:
            if hh > 0.55 and h01(x, y, seed + 3) < 0.85:
                c = MG[2] if hh > 0.75 else MG[1]
            else:
                c = ST[1]
            s.set(x, y, c)
            continue
        tone = (0, 1, -1, 0, 1, -1)[int(h01(bi, ci, seed) * 6)]
        lv = base + tone
        if ly == 0:
            lv += 1
        elif ly == course_h - 2:
            lv -= 1
        if lx == 1:
            lv += 1
        elif lx == bw - 1:
            lv -= 1
        lv += int(round(hh * 2.4))
        lv += bv[y, x]
        r = h01(x, y, seed + 9)
        if r < 0.05:
            lv -= 1                                        # chips
        s.set(x, y, ST[int(max(1, min(8, lv)))])


def band_h(s, x0, x1, y0, y1, step=7, off=3, clip=None):
    """Horizontal riveted iron band."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if clip is not None and not clip[y, x]:
                continue
            c = IR[4] if y == y0 else IR[1] if y == y1 else IR[3] if y == y0 + 1 else IR[2]
            hh = heat_at(x, y)
            if y == y1 and hh > 0.4:
                c = MG[1]
            s.set(x, y, c)
        pass
    ry = (y0 + y1) // 2
    for x in range(x0 + off, x1, step):
        if clip is None or clip[ry, x]:
            s.set(x, ry, IR[5]); s.set(x, ry + 1, IR[1])


def strap_v(s, x0, x1, y0, y1, step=7):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = IR[4] if x == x0 else IR[1] if x == x1 else IR[2]
            s.set(x, y, c)
    for y in range(y0 + 3, y1, step):
        s.set(x0 + 1, y, IR[5]); s.set(x0 + 2 if x1 - x0 > 2 else x0 + 1, y + 1, IR[1])


def stack(s, x0, x1_base, x1_top, y_top, y_base, seed):
    """An iron chimney stack: riveted cylinder shading, bands, soot at the top edge of the frame."""
    for y in range(y_top, y_base + 1):
        t = (y - y_top) / max(1, y_base - y_top)
        xa = x0 - int(round(t * 1.5))
        xb = x1_top + int(round(t * (x1_base - x1_top)))
        w = xb - xa + 1
        for x in range(xa, xb + 1):
            u = (x + 0.5 - xa) / w
            lv = 3 if u < 0.14 else 4 if u < 0.28 else 3 if u < 0.5 else 2 if u < 0.78 else 1
            c = IR[lv]
            if (y - y_top) % 22 in (0, 1, 2):
                c = IR[min(5, lv + 1)] if (y - y_top) % 22 == 0 else IR[max(0, lv - 1)] if (y - y_top) % 22 == 2 else IR[lv]
                if (y - y_top) % 22 == 1 and x % 5 == 2:
                    c = IR[5] if u < 0.5 else IR[4]
            elif (y - y_top) % 11 == 6 and int(u * 5) in (1, 3):
                c = IR[max(0, lv - 1)]                     # plate seams
            if u > 0.86 and h01(x, y // 3, seed) < 0.25:
                c = MG[1]                                  # heat licking the shadow edge
            s.set(x, y, c)


def fire(f):
    """The mouth's churning light (layer `Fire`): posterised flowing turbulence, brightest low in the centre,
    flame tongues rising, the vault above the fire lost in deep red."""
    s = Spr(W, H)
    m = mouth_mask()
    t = f / 4 * TAU
    for y, x in np.argwhere(m):
        u = (x + 0.5 - MX) / MR
        v = min(1.0, max(0.0, (y + 0.5 - (MY - MR)) / (MBOT - (MY - MR))))   # 0 arch crown .. 1 hearth
        base = 1.05 - 0.55 * abs(u) ** 1.6 - 0.75 * (1 - v) ** 1.4
        n = (math.sin(0.33 * x + 1.8 * math.sin(0.11 * y + t) + 0.9 * math.sin(0.05 * x - t))
             + 0.8 * math.sin(0.19 * x - 0.21 * y + t) + 0.6 * math.sin(0.42 * y + 2 * t + 0.3 * x)) / 2.4
        val = base + 0.3 * n * (0.4 + 0.6 * v)
        lv = 7 if val > 0.94 else 6 if val > 0.78 else 5 if val > 0.6 else 4 if val > 0.43 else 3 if val > 0.27 else 2 if val > 0.12 else 1
        s.set(x, y, MG[lv])
    # clean single-pixel specks so the bands stay smooth
    a = np.array(s.img)
    px = s.img.load()
    for y, x in np.argwhere(m):
        c = px[x, y]
        nbs = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if m[y + dy, x + dx]]
        if nbs and all(n_ != c for n_ in nbs):
            best = max(set(nbs), key=nbs.count)
            px[x, y] = best
    return s.img


def furnace_static():
    s = Spr(W, H)
    mouth = mouth_mask()
    # ---------------------------------------------------------------- chimney stacks (behind the dome)
    stack(s, 50, 66, 64, 0, 52, 3)
    stack(s, 112, 127, 125, 0, 52, 4)
    # ---------------------------------------------------------------- body: a battered base + a great dome
    body = ss_mask(W, H, union(poly([(21, 170), (27, 74), (149, 74), (155, 170)]), ell(88, 75, 62, 42)))
    dome = body & ss_mask(W, H, rect(0, 0, W - 1, 73))
    masonry(s, body & ~dome, 9, (16, 13, 18), 11, y_origin=74, base=3)
    masonry(s, dome, 7, (12, 10, 14), 12, y_origin=33, base=3)
    # the dome's upper courses darken into soot
    for y, x in np.argwhere(dome):
        if y < 50 and s.get(x, y) not in (ST[1],) and h01(x // 3, y // 2, 5) < 0.5 + (50 - y) / 30:
            c = s.get(x, y)
            idx = ST.index(c) if c in ST else 3
            s.set(x, y, ST[max(1, idx - 1)])
    for y, x in np.argwhere(mouth):
        s.set(x, y, T)                                           # the mouth is a hole: the Fire layer shows through
    # ---------------------------------------------------------------- iron: dome ribs, bands, straps, heat plates
    for (rx, sgn) in ((70, -1), (106, 1)):
        for y in range(34, 72):
            dx = int(round(sgn * (72 - y) * 0.0))
            for x in range(rx - 2, rx + 2):
                if dome[y, x]:
                    s.set(x, y, IR[4] if x == rx - 2 else IR[1] if x == rx + 1 else IR[2])
            if y % 6 == 2 and dome[y, rx - 1]:
                s.set(rx - 1, y, IR[5])
    band_h(s, 21, 155, 66, 72, clip=body)
    band_h(s, 21, 58, 110, 115, clip=body & ~grow(mouth, 11))
    band_h(s, 118, 155, 110, 115, clip=body & ~grow(mouth, 11))
    for (x0, x1) in ((33, 36), (140, 143)):
        strap_v(s, x0, x1, 73, 165)
    # heat-stained plates flanking the jambs (bruised violet temper, rust at the rivets)
    for (x0, x1) in ((38, 46), (130, 138)):
        pm = ss_mask(W, H, rect(x0, 118, x1, 162))
        bv = bevel(pm)
        for y, x in np.argwhere(pm):
            hh = heat_at(x, y)
            c = HS[2] if hh > 0.45 else HS[1] if hh > 0.3 else IR[2]
            if bv[y, x] > 0:
                c = IR[4]
            elif bv[y, x] < 0:
                c = IR[1]
            if (y - 118) % 15 == 14:
                c = IR[1]
            s.set(x, y, c)
        for y in range(121, 162, 7):
            s.set(x0 + 2, y, IR[5]); s.set(x1 - 2, y, IR[5])
            s.set(x0 + 2, y + 1, RU[2]); s.set(x1 - 2, y + 1, RU[2])
    # ---------------------------------------------------------------- the arch: voussoirs, jambs, hearth lip
    ring = ss_mask(W, H, minus(ell(MX, MY, MR + 10, MR + 10), ell(MX, MY, MR, MR), rect(0, MY, W - 1, H - 1)))
    for y, x in np.argwhere(ring):
        a = math.atan2(y + 0.5 - MY, x + 0.5 - MX)             # -pi .. 0 over the arch
        k = (a + math.pi) / math.pi * 11                          # 11 voussoirs
        rr = math.hypot(x + 0.5 - MX, y + 0.5 - MY)
        joint = abs(k - round(k)) * (rr * math.pi / 11) < 0.55 and 0 < round(k) < 11
        inner = rr < MR + 1.6
        outer = rr > MR + 8.8
        if joint:
            c = MG[2] if rr < MR + 5 else ST[1]
        elif inner:
            c = MG[3] if rr < MR + 0.8 else MG[2]                 # intrados lit by the fire
        elif outer:
            c = ST[6] if a < -1.7 else ST[4]
        else:
            lv = 5 + (1 if a < -1.9 else 0) + (1 if rr < MR + 4 else 0) - (1 if a > -1.1 else 0)
            c = ST[lv]
            if rr < MR + 3.5 and h01(x, y, 17) < 0.35:
                c = ST[lv + 1]
        s.set(x, y, c)
    for (x0, x1, lit) in ((48, 58, True), (117, 127, False)):
        jm = ss_mask(W, H, rect(x0, int(MY), x1, MBOT + 1))
        for y, x in np.argwhere(jm):
            ly = (y - int(MY)) % 9
            inside = (x == x1) if lit else (x == x0)
            if ly == 8:
                c = MG[2] if inside or abs(x - (x1 if lit else x0)) < 4 else ST[1]
            elif inside:
                c = MG[3]
            else:
                d = abs(x - (x1 if lit else x0))
                c = ST[7] if d < 3 else ST[6] if d < 6 else ST[5]
                if ly == 0:
                    c = ST[min(8, ST.index(c) + 1)]
                if not lit and d > 6:
                    c = ST[4]
            s.set(x, y, c)
    # hearth lip: iron sill with molten metal spilling over it and down the plinth face
    for x in range(52, 125):
        s.set(x, MBOT + 1, IR[4] if x < 88 else IR[3])
        s.set(x, MBOT + 2, IR[2])
        s.set(x, MBOT + 3, IR[1])
    # ---------------------------------------------------------------- coal bed silhouetted against the fire
    coal = ss_mask(W, H, union(ell(66, 164, 9, 5), ell(80, 163, 8, 6.5), ell(95, 164, 9, 5.5), ell(109, 164, 8, 4.5),
                               ell(73, 159.5, 4.5, 3.5), ell(101, 160, 5, 3.5)) )
    coal &= mouth | ss_mask(W, H, rect(0, MBOT - 1, W - 1, MBOT))
    for y, x in np.argwhere(coal):
        top = not coal[y - 1, x]
        c = MG[4] if top else CH[1] if (x + y) % 5 else CH[2]
        if not top and coal[y - 1, x] and not coal[y - 2, x]:
            c = MG[2]
        s.set(x, y, c)
    # ---------------------------------------------------------------- the ox-skull boss over the keystone
    for sgn in (-1, 1):
        # horns: sweep out over the voussoirs, then up, tapering to hooked points
        pts = []
        for i in range(29):
            t = i / 28
            ang = math.pi * (0.05 + 0.62 * t)
            px_ = 88 + sgn * (8 + 17 * math.sin(ang) + 2 * t)
            py_ = 88 - 2 - 14 * (1 - math.cos(ang)) * 0.85 + 3 * math.sin(t * math.pi)
            pts.append((px_, py_, 2.6 * (1 - t) ** 0.8 + 0.55))
        hm = np.zeros((H, W), dtype=bool)
        for (px_, py_, r) in pts:
            hm |= ss_mask(W, H, ell(px_, py_, r, r))
        bv = bevel(hm)
        for y, x in np.argwhere(hm):
            c = IR[5] if bv[y, x] > 0 else IR[1] if bv[y, x] < 0 else IR[3]
            if bv[y, x] == 0 and ((x - 88) * sgn) > 20 and y < 84:
                c = IR[2]
            s.set(x, y, c)
    sk = ss_mask(W, H, poly([(79, 83), (97, 83), (99.5, 88), (96, 95), (93, 104), (83, 104), (80, 95), (76.5, 88)]))
    bv = bevel(sk)
    for y, x in np.argwhere(sk):
        lv = 3 + bv[y, x] - (1 if x > 90 else 0) - (1 if y > 97 else 0)
        s.set(x, y, IR[max(1, min(5, lv))])
    for x in range(82, 95):
        s.set(x, 86, IR[4] if x < 88 else IR[3])                  # brow ridge
    for ex in (83, 91):
        s.set(ex, 88, MG[4]); s.set(ex + 1, 88, MG[4]); s.set(ex, 89, MG[5]); s.set(ex + 1, 89, MG[6])
        s.set(ex - 1, 88, IR[0]); s.set(ex + 2, 89, IR[1])
    s.set(86, 101, IR[0]); s.set(89, 101, IR[0]); s.set(87, 100, IR[1]); s.set(88, 100, IR[1])
    for y in range(92, 99):
        s.set(88, y, IR[2])                                       # the nasal ridge
    s.set(84, 103, MG[3]); s.set(91, 103, MG[3])                   # fire under the muzzle
    # ---------------------------------------------------------------- crown: Ashwright's seal on the dome, vents
    seal = ["...GGGGG...", "..GkkkkkH..", ".GkkmmmkkH.", "GkkkkmkkkkH", "GkkkkmkkkkH", "GkkkkmkkkkH",
            ".gkkkmkkkH.", "..gkkkkkH..", "...ggggg..."]
    kk = {"G": GD[3], "H": GD[4], "g": GD[2], "k": IR[0], "m": GD[5]}
    for j, row in enumerate(seal):
        for i, ch in enumerate(row):
            if ch in kk:
                s.set(83 + i, 45 + j, kk[ch])
    s.set(86, 48, MG[5])
    for cxp in (60, 116):                                     # glowing spy-ports on the dome's flanks
        pm = ss_mask(W, H, ell(cxp, 62, 3.2, 3.2))
        pr = ss_mask(W, H, ell(cxp, 62, 4.6, 4.6))
        for y, x in np.argwhere(pr & ~pm):
            s.set(x, y, IR[4] if y < 62 else IR[2])
        for y, x in np.argwhere(pm):
            s.set(x, y, MG[5] if math.hypot(x + 0.5 - cxp, y + 0.5 - 62) < 1.6 else MG[3])
        s.set(cxp - 1, 61, MG[6])
    for i, x in enumerate(range(73, 104, 6)):                  # grille slots in the band above the arch
        for y in (68, 69, 70):
            s.set(x, y, MG[3] if y == 69 else MG[2])
            s.set(x + 1, y, MG[2] if y == 69 else MG[1])
    # heat cracks in the masonry beside the arch
    for (pts) in (((45, 96), (47, 99), (46, 102), (48, 105)), ((131, 94), (129, 97), (130, 100)),
                  ((40, 140), (42, 143), (41, 146)), ((136, 150), (134, 152))):
        for i in range(len(pts) - 1):
            s.line(*pts[i], *pts[i + 1], MG[2] if i % 2 else MG[3])
    # ---------------------------------------------------------------- plinth (stands on the dais)
    pl = ss_mask(W, H, union(rect(14, 170, 161, 183), rect(8, 184, 167, 191)))
    masonry(s, pl, 7, (20, 16), 21, y_origin=170, base=3)
    for x in range(12, 164):
        s.set(x, 169, IR[4] if x < 60 else IR[3])
        s.set(x, 170, IR[2])
        s.set(x, 171, IR[1] if not 60 < x < 116 else MG[1])
    for x in range(14, 162, 8):
        s.set(x, 170, IR[5])
    for x in range(6, 170):
        s.set(x, 183, ST[6] if x < 40 else ST[5])
    # molten drool from the hearth down the plinth face
    for (dx, ln) in ((70, 7), (77, 12), (84, 4), (97, 9), (104, 5)):
        for j in range(ln):
            y = MBOT + 2 + j
            s.set(dx, y, MG[5] if j < 2 else MG[4] if j < ln - 2 else MG[3])
            if j < ln - 3:
                s.set(dx + 1, y, MG[3])
        s.set(dx, MBOT + 2 + ln, MG[2])
    for x in range(56, 121):
        if s.get(x, MBOT + 1) in (IR[4], IR[3]) and h01(x, 3, 9) < 0.6:
            s.set(x, MBOT + 1, MG[4] if 64 < x < 112 else MG[3])
    # ---------------------------------------------------------------- bellows (left)
    HX, HY = 36.0, 148.0                                          # the hinge at the nozzle end
    lea = ss_mask(W, H, poly([(3, 133), (HX, HY - 3), (HX, HY + 3), (3, 161)]))
    for y, x in np.argwhere(lea):
        ang = math.atan2(y + 0.5 - HY, HX - (x + 0.5))            # fans out from the hinge
        k = (ang + 0.75) / 1.5 * 5                                # 5 pleats
        ph = k - math.floor(k)
        c = LE[3] if ph < 0.25 else LE[2] if ph < 0.6 else LE[1] if ph < 0.85 else LE[0]
        if x > HX - 6:
            c = LE[1] if ph < 0.5 else LE[0]
        if x < 6 and ph > 0.6 and x < 3 + (ph - 0.6) * 10:
            c = None                                              # zigzag of the folds at the back edge
        s.set(x, y, c)
    top_b = ss_mask(W, H, poly([(0, 131), (4, 128), (HX + 1, HY - 5), (HX + 1, HY - 2), (1, 135)]))
    bot_b = ss_mask(W, H, poly([(0, 160), (HX + 1, HY + 2), (HX + 1, HY + 5), (3, 164), (0, 164)]))
    for (bm, lit) in ((top_b, True), (bot_b, False)):
        bv = bevel(bm)
        for y, x in np.argwhere(bm):
            lv = 3 + bv[y, x] + (0 if lit else -1)
            s.set(x, y, WD[max(1, min(5, lv))])
    for (x0, y0, y1) in ((12, 128, 136), (24, 133, 140), (12, 155, 162), (24, 152, 158)):
        for y in range(y0, y1 + 1):
            if (top_b | bot_b)[y, x0]:
                s.set(x0, y, IR[4]); s.set(x0 + 1, y, IR[2])     # iron straps round the boards
    s.set(12, 130, IR[5]); s.set(24, 135, IR[5])
    wt = ss_mask(W, H, poly([(5, 128), (7, 123), (16, 123), (18, 127), (17, 131), (6, 129)]))
    s.shade(wt, ST, 4)                                            # a stone weight riding the top board
    for x in range(36, 45):                                       # the nozzle into a tuyere
        for y in (145, 146, 147, 148):
            s.set(x, y, IR[4] if y == 145 else IR[3] if y == 146 else IR[2] if y == 147 else IR[1])
    s.set(44, 146, MG[4]); s.set(44, 147, MG[3]); s.set(45, 146, MG[3])
    for x in (5, 27):                                             # trestle legs
        for y in range(160 if x == 5 else 157, 170):
            s.set(x, y, WD[3]); s.set(x + 1, y, WD[1])
    chain_v(s, 11, 92, 125)                                       # a chain from the vault works the bellows
    s.set(11, 125, IR[4]); s.set(12, 126, IR[4])
    for (x, y) in ((5, 164), (6, 164), (27, 164), (28, 164)):
        pass
    # ---------------------------------------------------------------- gantry arm (right) with crucible + tongs
    for x in range(148, 176):
        s.set(x, 84, IR[4]); s.set(x, 85, IR[3]); s.set(x, 86, IR[2]); s.set(x, 87, IR[1])
    for x in range(150, 176, 6):
        s.set(x, 85, IR[5])
    chain_line(s, 151, 108, 169, 88)
    for y in range(80, 92):
        s.set(148, y, IR[4]); s.set(149, y, IR[2])
    # small crucible on a chain
    chain_v(s, 159, 88, 101)
    cm = ss_mask(W, H, poly([(152, 103), (168, 103), (166, 112), (163, 115), (157, 115), (154, 112)]))
    for y, x in np.argwhere(cm):
        u = (x + 0.5 - 152) / 16
        s.set(x, y, IR[4] if u < 0.2 else IR[3] if u < 0.5 else IR[2] if u < 0.85 else MG[1])
    for x in range(152, 169):
        s.set(x, 103, IR[5] if x < 157 else IR[4])
        s.set(x, 102, MG[6] if 154 < x < 166 else None)
    for x in range(155, 166):
        s.set(x, 101, MG[7] if 157 < x < 164 else MG[5])
    for (x, y) in ((151, 103), (169, 103)):
        s.set(x, y, IR[4])
    chain_line(s, 152, 102, 158, 97)
    chain_line(s, 166, 102, 160, 97)
    # tongs hanging from a hook at the arm's end
    chain_v(s, 171, 88, 96)
    for y in range(96, 128):
        t = (y - 96) / 32
        spread = 0 if y < 104 else int((y - 104) * 0.18)
        s.set(170 - spread, y, IR[4]); s.set(172 + spread, y, IR[2])
    for y in range(126, 130):
        s.set(169 - 4, y, IR[3]); s.set(173 + 4, y, IR[2]) if 173 + 4 < W else None
    s.set(171, 104, IR[5])
    return s, mouth


def build_furnace():
    static, mouth = furnace_static()
    # outline the whole silhouette (fire included so the mouth never leaks outside the stone)
    base = static.copy()
    base.img.alpha_composite(fire(0))
    base.px = base.img.load()
    occ_before = base.occ()
    outline(base)
    ring = base.occ() & ~occ_before
    for y, x in np.argwhere(ring):
        static.set(x, y, base.px[x, y])
    frames = []
    for f in range(4):
        frames.append({"ms": 130, "cels": {"Fire": fire(f), "Furnace": static.img.copy()}})
    return W, H, ["Fire", "Furnace"], frames, [("idle", 0, 3)]
