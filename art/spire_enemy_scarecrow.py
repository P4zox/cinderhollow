"""sp_scarecrow (56x56, anchor [28,56]) + sp_post (56x56, same anchor). See gen_spire_enemies.py.

The engine draws sp_post BEHIND the scarecrow at the same anchor; the `hidden` frames (and rise 0-3) hang the
scarecrow on it: arms along the crossbeam (rope-bound at the wrists over the post's frayed rope ends), feet
dangling ~6px above the floor. His rusted scythe is left stuck in the field soil beside the post.
"""
import math, os
import enemy_kit as K
from enemy_kit import Layer, FXLayer, Rig, ip, line, lerp, add, sub, ik, hash01, n_dome, n_plate, n_capsule, \
    poly_mask, dirv, mask_disc
import spire_enemy_kit as S
from spire_enemy_kit import n_tube, curve, madd, mk
from PIL import Image

SPEC = dict(hidden=2, rise=8, idle=4, walk=6, reap=10, lunge=8, hurt=2, death=6)
LAYERS = ["ScytheB", "BackArm", "Legs", "Coat", "Head", "Hat", "Scythe", "FrontArm", "Rope", "FX"]
FLOOR = 55
# ---- the post (shared geometry: hidden frames line up on it)
POLE_X = 28.0          # pole centre (pixels 26..29)
POLE_TOP = 8
BEAM_Y0, BEAM_Y1 = 17, 19      # crossbeam rows (inclusive)
BEAM_X0, BEAM_X1 = 11, 45
ROPE_X = (16, 40)      # wrist bindings / frayed rope ends

NEU = dict(mode="side", P=(26.5, 35.5), C=(27.6, 23.6), Hd=(30.4, 18.4), hup=(0.3, -1.0),
           hipn=(27.4, 36.0), hipf=(25.6, 35.6), fn=(29.8, FLOOR), ff=(23.4, FLOOR), kpref=(1.0, -0.1),
           hf=(36.2, 36.3), hb=(24.0, 37.0), eyes=2, hat=None, hem=0,
           sc=None, sback=False, buried=False, smear=None, glint=False, straw=0.0, dust=None, clods=None,
           ropes=None, fibers=0.0, sparks=None, wind=0.0, flash=False)
SP = mk(NEU)


# =========================================================================== scythe
def scythe_geom(hand, a, uh, ub):
    d = dirv(a)
    return madd(hand, (d, -ub)), madd(hand, (d, uh))


def draw_scythe(L, FX, butt, heel, bang, bend, blen=15.0, buried=False, glint=False):
    """Long weathered snath butt -> heel, rusted crescent blade from the heel (edge on the concave side)."""
    out = set()
    L.paint(n_capsule(butt, heel, 0.75, 0.7), "g", 0)
    # hand-peg (nib) a third of the way up the snath
    d = sub(heel, butt)
    ln = math.hypot(*d) or 1
    d = (d[0] / ln, d[1] / ln)
    nb = madd(butt, (d, ln * 0.38))
    L.fixed({ip(madd(nb, ((-d[1], d[0]), 1.3))): "g4", ip(madd(nb, ((-d[1], d[0]), 2.2))): "g3"})
    # blade centreline
    n = 24
    pts, p = [], heel
    for i in range(n + 1):
        t = i / n
        a = bang + bend * t
        pts.append((p, dirv(a), t))
        p = madd(p, (dirv(a), blen / n))
    sgn = 1 if bend >= 0 else -1
    m = {}
    xs = [q[0][0] for q in pts]
    ys = [q[0][1] for q in pts]
    for y in range(int(min(ys)) - 3, int(max(ys)) + 4):
        for x in range(int(min(xs)) - 3, int(max(xs)) + 4):
            c = (x + .5, y + .5)
            best = None
            for (q, dd, t) in pts:
                dx, dy = c[0] - q[0], c[1] - q[1]
                dist = dx * dx + dy * dy
                if best is None or dist < best[0]:
                    best = (dist, dx, dy, dd, t)
            _, dx, dy, dd, t = best
            u = dx * dd[0] + dy * dd[1]
            v = (-dd[1] * dx + dd[0] * dy) * sgn           # + = edge (concave) side
            w = 2.5 * (1 - t) ** 0.75 + 0.35
            if abs(u) <= 0.55 and -w * 0.62 <= v <= w * 0.38 and not (t == 0 and u < 0):
                m[(x, y)] = (v, t, w)
    if buried:
        m = {q: e for q, e in m.items() if q[1] <= FLOOR - 1}
    L.paint(n_plate(set(m), 0.9, (-0.1, -0.2), 1.0), "r", 0, ao=0)
    edge = [q for q, (v, t, w) in m.items() if v > w * 0.38 - 0.95]
    L.decal(edge, ("I", 4))
    L.decal([q for q in edge if hash01(*q, 5) < 0.35], ("I", 5))
    L.decal([q for q, (v, t, w) in m.items() if v < -w * 0.62 + 0.9 and hash01(*q, 7) < 0.5], ("r", 1))
    tip = pts[-1][0]
    tq = ip(tip)
    if not buried:
        L.fixed({tq: "I5"})
    out |= set(m)
    if glint:
        gp = pts[int(n * 0.6)][0]
        S.star(FX, gp, 3, cols=("U4", "U3", "U1"))
    return out, tip, pts[int(n * 0.6)][0]


# =========================================================================== straw / small parts
def straw(FX_or_L, base, ang, n, ln, seed, fi=0, spread=70, fixed_layer=True):
    """Tuft of dry straw strands bursting from `base` roughly along `ang`."""
    pix = {}
    for k in range(n):
        a = ang + (hash01(k, seed, 3) - 0.5) * spread + math.sin(fi * 1.3 + k) * 6
        L_ = ln * (0.6 + 0.6 * hash01(k, seed, 4))
        seg = line(base, madd(base, (dirv(a), L_)))
        for j, q in enumerate(seg[1:]):
            pix[q] = "H4" if j == len(seg) - 2 else ("H3" if (j + k) % 2 else "H2")
    if fixed_layer:
        FX_or_L.fixed(pix)
    else:
        for q, c in pix.items():
            FX_or_L.put([q], c)
    return pix


def boot(L, ank, toe_dir, bias=0):
    """Small ragged boot/foot: capsule from ankle along toe_dir."""
    L.paint(n_capsule(ank, madd(ank, (toe_dir, 2.4)), 1.25, 1.0), "Z", bias - 1)


def eye_hole(L, c, glow, big=True):
    x, y = ip(c)
    pts = [(x, y), (x, y + 1)] + ([(x + 1, y), (x + 1, y + 1)] if big else [])
    cols = {0: ("OUT", "X0"), 1: ("U0", "OUT"), 2: ("U2", "U0"), 3: ("U4", "U2")}[glow]
    pix = {}
    for i, q in enumerate(pts):
        pix[q] = cols[0] if (i == 0 or (big and i == 2 and glow >= 2)) else cols[1]
    pix[(x - 1, y + (1 if big else 0))] = "X1"         # torn edge
    L.fixed(pix)


def draw_head(Ls, FX, Hd, hup, eyes, fi, info, hat=None):
    Hl = Ls["Head"]
    G = K.basis(Hd, hup)
    # bunched sack neck with a twine tie
    Hl.paint(n_tube([G(-0.8, 2.2), G(-0.4, 4.4), G(-0.6, 5.6)], [2.0, 1.4, 1.6]), "X", -1)
    Hl.decal(line(G(-2.0, 4.0), G(1.2, 4.0)), ("H", 1))
    # sack head: slightly narrow at the top, lumpy lower cheek
    Hl.paint(n_dome(G(0.4, -0.2), 3.1, 3.5, tilt=(-0.1, -0.1)), "X", 0)
    Hl.paint(n_dome(G(1.2, 1.4), 2.4, 1.9), "X", 0, ao=0)
    Hl.decal([q for q in Hl.px if hash01(*q, 11) < 0.12], ("X", 2))
    eye_hole(Hl, G(1.7, -0.9), eyes, True)
    eye_hole(Hl, G(3.4, -1.0), eyes, False)
    # stitched mouth: dark seam, pale thread crossings
    seam = line(G(1.0, 1.7), G(3.9, 1.4))
    Hl.fixed({q: "X0" for q in seam})
    for i, q in enumerate(seam):
        if i % 2 == 1:
            Hl.fixed({(q[0], q[1] - 1): "X5", (q[0], q[1] + 1): "X4"})
    info["eye"] = G(1.9, -0.6)
    info["head"] = G(0.4, -0.2)
    # ---- hat: battered wide-brim straw hat (can be knocked off: hat = (centre, up))
    Ht = Ls["Hat"]
    hc, hu = hat if hat else (G(0.4, -3.2), hup)
    Hh = K.basis(hc, hu)
    brim = [Hh(-5.6, 0.6), Hh(-4.0, -0.4), Hh(-1.0, -0.8), Hh(3.0, -0.6), Hh(5.6, 0.2), Hh(6.6, 1.2),
            Hh(5.4, 1.4), Hh(2.6, 0.6), Hh(-1.0, 0.7), Hh(-3.6, 0.9), Hh(-5.4, 1.5)]
    bm = poly_mask(brim)
    Ht.paint(n_plate(bm, 0.8, (-0.1, -0.5), 0.9), "H", -1)
    crown = [Hh(-2.7, 0.0), Hh(-2.6, -2.2), Hh(-1.4, -3.2), Hh(0.2, -2.8), Hh(1.1, -3.4), Hh(2.4, -2.4),
             Hh(2.7, 0.0)]
    cm = poly_mask(crown)
    Ht.paint(n_plate(cm, 1.2, (-0.2, -0.3), 1.0), "H", -1)
    Ht.decal(line(Hh(-2.9, -0.6), Hh(2.9, -0.6)), ("X", 1), )
    Ht.decal([q for q in line(Hh(-0.6, -3.4), Hh(0.4, -1.4))], ("H", 1))           # dent crease
    # frayed brim edge + a torn gap
    Ht.erase([ip(Hh(4.2, 0.9))])
    fr = {}
    for k, u in enumerate((-4.8, -1.8, 1.6, 4.6)):
        q = ip(Hh(u, 1.9 + (k % 2) * 0.6))
        fr[q] = "H2"
    Ht.fixed(fr)
    Ht.decal([q for q in bm | cm if hash01(*q, 13) < 0.18], ("H", 1))


def arm_side(L, sh, hand, l1, l2, pref, bias, fi, seed, grip=True, straw_on=True):
    el = ik(sh, hand, l1, l2, pref)
    cuff = lerp(el, hand, 0.78)
    L.paint(n_tube([sh, el, cuff], [1.55, 1.3, 1.55]), "Z", bias)
    d = sub(hand, el)
    ln = math.hypot(*d) or 1
    d = (d[0] / ln, d[1] / ln)
    # dried, bony hand + long fingers
    L.paint(n_dome(hand, 1.1, 1.1), "A", bias, ao=0)
    f1 = ip(madd(hand, (d, 1.6), ((-d[1], d[0]), 0.6)))
    f2 = ip(madd(hand, (d, 1.8), ((-d[1], d[0]), -0.7)))
    L.fixed({f1: "A2" if bias < 0 else "A3", f2: "A2"})
    if straw_on:
        a = math.degrees(math.atan2(d[1], d[0]))
        straw(L, cuff, a + 180 + 40, 2, 2.2, seed, fi, 50)
        straw(L, cuff, a + 180 - 40, 2, 2.0, seed + 1, fi, 50)
    return el


# =========================================================================== body poses
def coat_mask_side(F, P, ln, hem, fi, sw, heap=0.0):
    pts = [F(-2.2, -ln - 1.0), F(2.4, -ln - 0.8), F(3.6, -ln + 4.0), F(3.2, -3.0)]
    fr = P[0] + 4.6 - sw * 0.2
    bk = P[0] - 5.4 - sw * 0.7
    n = 8
    for i in range(n + 1):
        t = i / n
        x = fr - (fr - bk) * t
        long_ = (i + fi) % 3 == 0
        pts.append((x, hem + (2.4 + 1.2 * hash01(i, fi, 5) if long_ else -0.4 + 0.8 * hash01(i, 2, 7))))
    pts += [(bk - 1.6 - sw * 0.6, hem - 1.0), (bk + 0.6, hem - 4.0), F(-4.2, -3.0), F(-4.0, -ln + 2.4)]
    return pts


def draw_side(p, fi, sw, Ls, FX, info):
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    shF, shB = F(1.0, -ln + 1.2), F(-2.2, -ln + 1.6)
    hem = P[1] + 10.5
    # ---- legs: thin patched trousers, rag-wrapped feet, straw at the ankles
    Lg = Ls["Legs"]
    for k, (hip, foot) in enumerate(((p["hipf"], p["ff"]), (p["hipn"], p["fn"]))):
        bias = -2 if k == 0 else 0
        ank = (foot[0], foot[1] - 1.6)
        l1 = l2 = 10.2
        kn = ik(hip, ank, l1, l2, p["kpref"])
        Lg.paint(n_tube([hip, kn, ank], [1.5, 1.2, 1.0]), "X", bias - 1)
        boot(Lg, ank, dirv(-8 if foot[1] >= FLOOR - 0.5 else 30), bias)
        if k:
            Lg.fixed({ip((ank[0] - 1.6, ank[1] - 1.8)): "H2", ip((ank[0] - 2.4, ank[1] - 2.2)): "H1"})
    # ---- far arm
    Ba = Ls["BackArm"]
    arm_side(Ba, shB, p["hb"], 6.6, 6.6, (-1, 0.5), -2, fi, 30)
    # ---- coat
    Ct = Ls["Coat"]
    m = poly_mask(coat_mask_side(F, P, ln, hem, p["hem"], sw))
    Ct.paint(n_plate(m, 2.0, (-0.05, 0.0), 1.0,
                     fold=lambda x, y: (0.55 * math.sin((x - P[0] - sw * 0.3) * 1.2) *
                                        min(1.0, max(0.0, (y - P[1] + 6) / 10)), 0)), "Z", 0)
    ys = [q[1] for q in m]
    yb = max(ys)
    Ct.decal([q for q in m if q[1] >= yb - 1], ("Z", 1))
    # front opening seam, rope belt with a knot, one sackcloth patch
    Ct.decal([q for q in line(F(2.6, -ln + 1.0), F(3.2, 2.0)) if q in m], ("Z", 1))
    belt = line(F(-4.0, -2.4), F(3.4, -2.6))
    Ct.decal([q for q in belt if q in m], ("H", 1))
    kq = ip(F(3.0, -2.2))
    Ct.fixed({kq: "H2", (kq[0], kq[1] + 1): "H1", (kq[0] + 1, kq[1] + 2): "H2"})
    pc = F(-1.8, -ln + 6.0)
    Ct.decal([q for q in mask_disc(pc, 1.4, 1.2) if q in m], ("X", 2))
    # straw bursting from the collar and under the belt
    straw(Ct, F(0.2, -ln - 0.6), -80, 4, 3.2, 40, fi, 90)
    straw(Ct, F(3.2, -1.6), 20, 2, 2.4, 41, fi, 50)
    # ---- head + hat
    draw_head(Ls, FX, Hd, p["hup"], p["eyes"], fi, info, p["hat"])
    # ---- near arm
    Fa = Ls["FrontArm"]
    arm_side(Fa, shF, p["hf"], 6.8, 6.8, (-1, 0.6), 0, fi, 31)
    info["hit"] |= set(m)
    return m


def draw_cruc(p, fi, sw, Ls, FX, info):
    """Strung up on the post, seen from the front: arms along the crossbeam, legs dangling, head hanging."""
    dy = p.get("drop", 0.0)
    cx = POLE_X
    by = BEAM_Y0 + 1.5
    lift = p.get("lift", 0.0)          # 0..1 arms straining upward/forward (rope about to snap)
    Ba = Ls["BackArm"]
    wx = {0: ROPE_X[0], 1: ROPE_X[1]}
    for side, sgn in ((0, -1), (1, 1)):
        sh = (cx + sgn * 4.6, by + 1.8 + dy)
        wr = (wx[side] + 0.5, by - lift * 1.2)
        el = (lerp(sh, wr, 0.5)[0], by + 0.8 - lift * 1.6 + dy * 0.5)
        Ba.paint(n_tube([sh, el, wr], [1.7, 1.35, 1.45]), "Z", -1 if side == 0 else 0)
        hand = (wr[0] + sgn * 2.2, wr[1] + 1.4 - lift * 1.4)
        Ba.paint(n_dome(hand, 1.1, 1.2), "A", 0, ao=0)
        Ba.fixed({(int(hand[0]) + sgn, int(hand[1]) + 2 - int(lift)): "A2",
                  (int(hand[0]), int(hand[1]) + 2 - int(lift * 1.5)): "A3"})
        straw(Ba, (wr[0] + sgn * 1.0, wr[1]), 90 + sgn * 50, 3, 2.6, 60 + side, fi, 60)
        if p["ropes"] is None or p["ropes"][side]:
            r = {}
            for dx_ in (-1, 0, 1):
                for yy in (int(by - 1 - lift), int(by + 1 - lift)):
                    r[(int(wr[0]) + dx_, yy)] = "H2" if (dx_ + yy) % 2 else "H1"
            Ls["Rope"].fixed(r)
    # legs dangling, toes down
    Lg = Ls["Legs"]
    for k, (hx, fx_) in enumerate(((cx - 2.0, cx - 2.6 + sw * 0.1), (cx + 2.0, cx + 2.4 + sw * 0.1))):
        hip = (hx, 36.0 + dy)
        ank = (fx_, 46.6 + dy - k * 0.4)
        Lg.paint(n_tube([hip, lerp(hip, ank, 0.5), ank], [1.5, 1.25, 1.0]), "X", -1 - k)
        boot(Lg, ank, dirv(80 - k * 20), -k)
        Lg.fixed({ip((ank[0] + (-1.6 if k == 0 else 1.6), ank[1] - 1.2)): "H2"})
    # coat, frontal
    Ct = Ls["Coat"]
    hem = 40.5 + dy
    pts = [(cx - 2.2, by + 0.2 + dy), (cx - 5.6, by + 1.6 + dy), (cx - 5.4, by + 6 + dy), (cx - 4.4, 31 + dy),
           (cx - 5.8, hem - 1)]
    n = 8
    for i in range(n + 1):
        t = i / n
        x = cx - 6.0 + 12.0 * t
        long_ = (i + p["hem"]) % 3 == 0
        pts.append((x, hem + (2.0 + 1.2 * hash01(i, 3, 5) if long_ else -0.3 + 0.8 * hash01(i, 2, 7))))
    pts += [(cx + 5.8, hem - 1), (cx + 4.4, 31 + dy), (cx + 5.4, by + 6 + dy), (cx + 5.6, by + 1.6 + dy),
            (cx + 2.2, by + 0.2 + dy)]
    m = poly_mask(pts)
    Ct.paint(n_plate(m, 2.2, (0.0, 0.0), 1.0, fold=lambda x, y: (0.5 * math.sin((x - cx) * 1.3), 0)), "Z", 0)
    Ct.decal([q for q in m if q[1] >= max(q2[1] for q2 in m) - 1], ("Z", 1))
    Ct.decal([q for q in line((cx + 0.5, by + 2 + dy), (cx + 0.8, hem - 0.5)) if q in m], ("Z", 1))
    Ct.decal([q for q in line((cx - 4.6, 30.6 + dy), (cx + 4.6, 30.2 + dy)) if q in m], ("H", 1))
    kq = (int(cx + 1.6), int(30.8 + dy))
    Ct.fixed({kq: "H2", (kq[0], kq[1] + 1): "H1", (kq[0] + 1, kq[1] + 2): "H2"})
    Ct.decal([q for q in mask_disc((cx - 2.8, 25.5 + dy), 1.4, 1.2) if q in m], ("X", 2))
    straw(Ct, (cx, by + dy), -90, 5, 3.0, 80, fi, 110)
    straw(Ct, (cx + 2.4, 31.6 + dy), 70, 2, 2.4, 81, fi, 50)
    straw(Ct, (cx - 3.4, hem + 0.5), 100, 2, 2.4, 82, fi, 40)
    # head hanging forward over the chest
    draw_head(Ls, FX, p["Hd"], p["hup"], p["eyes"], fi, info, p["hat"])
    info["hit"] |= set(m)
    return m


def draw_scare(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    body = draw_cruc(p, fi, sw, Ls, FX, info) if p["mode"] == "cruc" else draw_side(p, fi, sw, Ls, FX, info)
    # ---- scythe
    if p["sc"]:
        s = p["sc"]
        L = Ls["ScytheB"] if p["sback"] else Ls["Scythe"]
        if "hand" in s:
            butt, heel = scythe_geom(s["hand"], s["a"], s["uh"], s["ub"])
        else:
            butt, heel = s["butt"], s["heel"]
        bl, tip, mid = draw_scythe(L, FX, butt, heel, s["bang"], s["bend"], s.get("blen", 15.0), p["buried"],
                                   p["glint"])
        info["blade"] = bl
        info["tip"] = tip
        info["bmid"] = mid
        info["hit"] |= bl
        if p["buried"]:
            for k in range(5):
                q = (int(heel[0]) - 2 + k, FLOOR)
                FX.put([q], "X1" if k % 2 else "X2")
            FX.put([(int(heel[0]) - 1, FLOOR - 1), (int(heel[0]) + 2, FLOOR - 1)], "X2")
    # ---- eyes: under-light when bright
    # ---- fx
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1, pal) in p["smear"]:
            info["hit"] |= K.swept(FX, g0, a0, g1, a1, u0, u1, hw=1.4, pal=pal, taper=0.45, start=p.get("sstart", 0.0),
                                   exclude=info.get("blade", set()), clip_y=FLOOR)
    if p["straw"]:
        f = p["straw"]
        c = info["head"] if p.get("straw_at") is None else p["straw_at"]
        for k in range(12):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 1, 91)) if k < 8 else math.pi * hash01(k, 2, 91)
            r = 2 + 11 * f * (0.4 + 0.6 * hash01(k, 3, 91))
            q0 = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.8 + f * f * 8)
            fa = 360 * hash01(k, 4, 91) + f * 150
            seg = line(q0, madd(q0, (dirv(fa), 2.2)))
            for j, q in enumerate(seg):
                if q[1] <= FLOOR:
                    FX.put([q], "H4" if j == 0 else "H3" if k % 2 else "H2")
    if p["dust"]:
        x0, n = p["dust"]
        for k in range(n):
            dx = (k - n / 2) * 2.2 + hash01(k, 5, 17) * 1.5
            h_ = 1 + int(hash01(k, 6, 17) * 3)
            for j in range(h_):
                FX.put([(int(x0 + dx + j * (0.6 if dx > 0 else -0.6)), FLOOR - j - (k % 2))], "X3" if j else "X2")
    if p["clods"]:
        c, f = p["clods"]
        for k in range(7):
            a = -math.pi * (0.2 + 0.6 * hash01(k, 1, 23))
            r = 2 + 8 * f * (0.5 + 0.5 * hash01(k, 2, 23))
            q = ip((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r + f * f * 4))
            FX.put([q], "X2" if k % 2 else "X1")
            if k % 3 == 0:
                FX.put([(q[0] + 1, q[1])], "X1")
    if p["fibers"]:
        f = p["fibers"]
        for side in (0, 1):
            wx = ROPE_X[side] + 0.5
            for k in range(5):
                a = -math.pi * (0.1 + 0.8 * hash01(k, side, 29))
                r = 1.5 + 6 * f * hash01(k, 7, 29)
                q = ip((wx + math.cos(a) * r, BEAM_Y0 + 1 + math.sin(a) * r + f * 4))
                FX.put([q], "H3" if k % 2 else "H2")
    if p["sparks"]:
        c = p["sparks"]
        for k in range(4):
            a = -math.pi * (0.55 + 0.35 * hash01(k, 1, 37))
            q = ip((c[0] + math.cos(a) * (1.5 + k), c[1] + math.sin(a) * (1 + k * 0.6)))
            FX.put([q], "I5" if k < 2 else "I4")
    if p["flash"]:
        S.star(FX, info["eye"], 2, cols=("U4", "U3", "U2"), diag=False)
    return Ls, info


# =========================================================================== poses / animation
HID_HD = (29.2, 20.4)
HID_UP = (0.55, -0.83)
HID = dict(mode="cruc", Hd=HID_HD, hup=HID_UP, eyes=0, P=(28.0, 36.0), C=(28.0, 20.0),
           sc=dict(butt=(47.0, 31.0), heel=(38.4, 51.4), bang=78, bend=50), buried=True)
IDLE_SC = dict(hand=(36.2, 36.3), a=-93, uh=15.5, ub=18.5, bang=-6, bend=58)


def a_hidden():
    return [(600, SP(**HID, hem=0)),
            (600, SP(**dict(HID, Hd=(HID_HD[0] + 0.3, HID_HD[1]), hup=(0.6, -0.8)), hem=1, wind=0.5))]


def a_rise():
    stuck = dict(butt=(47.0, 31.0), heel=(38.4, 51.4), bang=78, bend=50)
    return [
        (300, SP(**dict(HID, Hd=(29.4, 19.4), hup=(0.42, -0.9), eyes=1))),
        (220, SP(**dict(HID, Hd=(29.2, 17.8), hup=(0.12, -1.0), eyes=2), hem=1)),
        (200, SP(**dict(HID, Hd=(29.4, 17.4), hup=(0.08, -1.0), eyes=3), lift=0.6, hem=2, flash=True)),
        (110, SP(**dict(HID, Hd=(29.6, 18.0), hup=(0.2, -1.0), eyes=3), lift=1.0, drop=1.0, ropes=(False, False),
                 fibers=0.4, hem=0)),
        (90, SP(P=(27.2, 39.0), C=(27.6, 27.0), Hd=(30.0, 21.6), hup=(0.2, -1.0), eyes=3,
                hipn=(28.0, 39.4), hipf=(26.2, 39.0), fn=(29.0, FLOOR - 2.5), ff=(24.6, FLOOR - 1.5),
                hf=(35.0, 21.0), hb=(21.0, 22.0), sc=stuck, buried=True, fibers=1.0, wind=-2)),
        (160, SP(P=(26.4, 42.0), C=(28.8, 31.0), Hd=(32.6, 26.2), hup=(0.55, -0.9), eyes=3,
                 hipn=(27.4, 42.4), hipf=(25.4, 42.0), fn=(31.0, FLOOR), ff=(22.4, FLOOR), kpref=(1, -0.6),
                 hf=(35.0, 44.0), hb=(26.0, 45.0), sc=stuck, buried=True, dust=(26, 6), hem=1)),
        (140, SP(P=(27.0, 38.6), C=(29.8, 27.4), Hd=(34.0, 22.8), hup=(0.6, -0.85), eyes=3,
                 hipn=(28.0, 39.0), hipf=(26.0, 38.6), fn=(31.0, FLOOR), ff=(23.0, FLOOR),
                 hf=(44.0, 37.4), hb=(27.0, 42.0), sc=stuck, buried=True, hem=2)),
        (180, SP(P=(26.6, 36.4), C=(27.8, 24.6), Hd=(30.8, 19.4), hup=(0.3, -1.0), eyes=3,
                 hipn=(27.5, 36.8), hipf=(25.7, 36.4), fn=(29.8, FLOOR), ff=(23.4, FLOOR),
                 hf=(37.0, 33.0), hb=(30.0, 39.0), sc=dict(hand=(37.0, 33.0), a=-72, uh=15.0, ub=19.0, bang=12,
                                                           bend=52),
                 clods=((43.0, 49.0), 0.7), hem=0)),
    ]


def a_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        sc = dict(IDLE_SC, hand=(36.2, 36.3 + b * 0.3))
        fr.append((200, SP(C=(27.6 - b * 0.2, 23.6 + b * 0.5), Hd=(30.4 - b * 0.3, 18.4 + b * 0.7),
                           hup=(0.3 - b * 0.08, -1.0), hf=(36.2, 36.3 + b * 0.3), hb=(24.0 - b * 0.2, 37.0 + b * 0.5),
                           sc=sc, eyes=2 if i != 2 else 3, hem=i, wind=0.6 * math.sin(i * math.pi / 2))))
    return fr


def a_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.9 * abs(s_)
        lurch = 0.6 * c
        fn = (27.0 + 5.0 * c, FLOOR - (1.4 if s_ > 0.3 else 0.0))
        ff = (26.0 - 5.0 * c, FLOOR - (1.4 if s_ < -0.3 else 0.0))
        hand = (32.6 + lurch * 0.5, 37.6 + b * 0.6)
        sc = dict(hand=hand, a=150 + 2 * s_, uh=24.0, ub=6.0, bang=176, bend=-70, blen=14.5)
        fr.append((150, SP(P=(26.0 + lurch * 0.3, 36.2 + b), C=(28.0 + lurch, 24.8 + b), Hd=(31.4 + lurch, 19.8 + b * 1.2),
                           hup=(0.45, -1.0), hipn=(27.0, 36.6 + b), hipf=(25.2, 36.2 + b), fn=fn, ff=ff,
                           hf=hand, hb=(23.0 - c * 1.5, 37.6 + b), sc=sc, sback=False, eyes=2, hem=i, wind=-1.5,
                           sparks=(3.0 + (i % 2), FLOOR - 1) if i in (0, 3) else None)))
    return fr


LEAN_B = dict(P=(25.6, 36.0), C=(24.8, 24.2), Hd=(27.0, 18.6), hup=(0.05, -1.0), hipn=(26.6, 36.4),
              hipf=(24.8, 36.0), fn=(31.0, FLOOR), ff=(21.0, FLOOR))
SWING = dict(P=(27.4, 36.4), C=(30.4, 25.2), Hd=(34.6, 20.4), hup=(0.6, -1.0), hipn=(28.4, 36.8),
             hipf=(26.6, 36.4), fn=(33.0, FLOOR), ff=(21.4, FLOOR))
LOW = dict(P=(27.6, 38.0), C=(31.4, 27.6), Hd=(36.0, 23.4), hup=(0.8, -0.9), hipn=(28.6, 38.4),
           hipf=(26.8, 38.0), fn=(33.4, FLOOR), ff=(21.0, FLOOR), kpref=(1, -0.5))


def sc_at(hand, a, uh=22.0, ub=10.0, bang=None, bend=40, blen=15.0):
    return dict(hand=hand, a=a, uh=uh, ub=ub, bang=a + 90 if bang is None else bang, bend=bend, blen=blen)


def a_reap():
    s0 = sc_at((33.0, 32.0), -104, 18.0, 14.0, bend=45)
    s1 = sc_at((30.0, 28.0), -128, 19.0, 13.0, bend=45)
    s2 = sc_at((27.0, 25.6), -146, 20.0, 12.0, bend=45)
    s3 = sc_at((25.6, 25.0), -158, 20.0, 12.0, bend=45)
    s5 = sc_at((34.0, 32.0), -14, 21.0, 11.0, bend=40)
    s6 = sc_at((34.6, 40.0), 24, 21.0, 11.0, bang=160, bend=22)
    s7 = sc_at((31.0, 41.0), 40, 19.0, 13.0, bang=196, bend=10)
    s8 = sc_at((34.0, 37.0), -40, 18.0, 14.0, bend=50)

    def sm(sa, sb, pal="cold"):
        return (sa["hand"], sa["a"], sb["hand"], sb["a"], 12.0, sa["uh"] + 1.0, pal)
    return [
        (140, SP(P=(26.2, 35.8), C=(26.6, 23.8), Hd=(29.2, 18.4), hup=(0.2, -1.0), hf=s0["hand"],
                 hb=(31.0, 36.0), sc=s0, eyes=2)),
        (130, SP(**LEAN_B, hf=s1["hand"], hb=(28.0, 33.0), sc=s1, eyes=2, hem=1)),
        (130, SP(**LEAN_B, hf=s2["hand"], hb=(24.0, 30.0), sc=s2, eyes=3, hem=2, sback=True)),
        (120, SP(**dict(LEAN_B, C=(24.2, 24.4), Hd=(26.2, 18.8)), hf=s3["hand"], hb=(22.0, 29.0), sc=s3, eyes=3,
                 hem=0, sback=True)),
        (380, SP(**dict(LEAN_B, C=(24.0, 24.6), Hd=(26.0, 19.0)), hf=s3["hand"], hb=(22.0, 29.0), sc=s3, eyes=3,
                 hem=1, sback=True, glint=True)),
        (70, SP(**SWING, hf=s5["hand"], hb=(28.0, 33.0), sc=s5, eyes=3, hem=2, wind=3,
                smear=[(s3["hand"], s3["a"], s5["hand"], s5["a"], 13.0, 22.0, "cold")], sstart=0.4)),
        (90, SP(**LOW, hf=s6["hand"], hb=(30.0, 38.0), sc=s6, eyes=3, hem=0, wind=3,
                smear=[(s5["hand"], s5["a"], s6["hand"], s6["a"], 13.0, 22.5, "cold")], dust=(46, 5))),
        (140, SP(**dict(LOW, C=(31.0, 28.2), Hd=(35.4, 24.4)), hf=s7["hand"], hb=(28.0, 39.0), sc=s7, eyes=2,
                 hem=1, dust=(40, 6))),
        (160, SP(P=(26.8, 36.0), C=(28.6, 24.6), Hd=(32.0, 19.6), hup=(0.45, -1.0), hf=s8["hand"], hb=(26.0, 37.0),
                 sc=s8, eyes=2, hem=2)),
        (180, SP(hf=IDLE_SC["hand"], sc=IDLE_SC, eyes=2, hem=0)),
    ]


def a_lunge():
    c0 = sc_at((27.0, 23.0), -128, 17.0, 15.0, bend=45)
    c1 = sc_at((29.0, 18.0), -96, 15.0, 17.0, bend=45)
    c2 = sc_at((31.0, 16.0), -62, 14.0, 18.0, bend=48)
    c3 = sc_at((35.0, 24.0), -12, 14.0, 18.0, bend=40)
    c4 = sc_at((36.0, 35.0), 26, 15.0, 17.0, bang=112, bend=30)
    c6 = sc_at((33.0, 33.0), -24, 15.0, 17.0, bend=45)
    CR = dict(P=(25.4, 40.4), C=(26.8, 29.2), Hd=(30.4, 24.0), hup=(0.5, -0.9), hipn=(26.4, 40.8),
              hipf=(24.6, 40.4), fn=(30.6, FLOOR), ff=(20.8, FLOOR), kpref=(1, -0.8))
    AIR = dict(P=(27.0, 31.0), C=(28.4, 19.6), Hd=(31.4, 14.4), hup=(0.35, -1.0), hipn=(28.0, 31.4),
               hipf=(26.2, 31.0), fn=(31.0, 46.0), ff=(22.0, 48.0), kpref=(1, 0.2))
    return [
        (200, SP(**CR, hf=c0["hand"], hb=(24.0, 26.0), sc=c0, eyes=3, sback=True, flash=True)),
        (90, SP(**AIR, hf=c1["hand"], hb=(27.0, 22.0), sc=c1, eyes=3, hem=1, wind=-2, dust=(25, 5))),
        (100, SP(**dict(AIR, P=(27.6, 30.0), C=(29.4, 18.8), Hd=(32.6, 13.8), fn=(32.0, 44.0), ff=(23.0, 46.0)),
                 hf=c2["hand"], hb=(29.0, 21.0), sc=c2, eyes=3, hem=2)),
        (70, SP(P=(28.4, 34.0), C=(31.0, 23.0), Hd=(35.4, 18.6), hup=(0.6, -1.0), hipn=(29.4, 34.4),
                hipf=(27.6, 34.0), fn=(33.0, 52.0), ff=(23.4, 53.0), hf=c3["hand"], hb=(31.0, 27.0), sc=c3, eyes=3,
                hem=0, wind=3, smear=[(c2["hand"], c2["a"], c3["hand"], c3["a"], 10.0, 15.0, "cold")])),
        (70, SP(**LOW, hf=c4["hand"], hb=(31.0, 33.0), sc=c4, eyes=3, hem=1, wind=3,
                smear=[(c3["hand"], c3["a"], c4["hand"], c4["a"], 10.0, 16.0, "cold")], dust=(47, 7))),
        (120, SP(**LOW, hf=c4["hand"], hb=(31.0, 33.0), sc=c4, eyes=3, hem=2, dust=(48, 9),
                 clods=((48.0, 52.0), 0.5))),
        (170, SP(**dict(LOW, C=(30.0, 27.0), Hd=(34.0, 22.4)), hf=c6["hand"], hb=(28.0, 35.0), sc=c6, eyes=2,
                 hem=0, clods=((47.0, 50.0), 1.0))),
        (180, SP(hf=IDLE_SC["hand"], sc=IDLE_SC, eyes=2, hem=1)),
    ]


def a_hurt():
    return [(90, SP(P=(25.8, 35.8), C=(24.6, 24.0), Hd=(26.0, 18.8), hup=(-0.25, -1.0), hipn=(26.8, 36.2),
                    hipf=(25.0, 35.8), hf=(34.6, 35.6), hb=(21.0, 34.0),
                    sc=dict(IDLE_SC, hand=(34.6, 35.6), a=-100), eyes=3, straw=0.35, flash=True)),
            (150, SP(P=(26.2, 35.6), C=(26.4, 23.8), Hd=(29.0, 18.6), hup=(0.15, -1.0),
                     hf=(35.6, 36.0), sc=dict(IDLE_SC, hand=(35.6, 36.0), a=-96), eyes=2, straw=0.6, hem=1))]


def a_death():
    body = ["BackArm", "Legs", "Coat", "Head", "FrontArm"]
    rag = ("H4", "H3", "H2", "X3", "X2")
    ground_sc = dict(butt=(12.0, 54.4), heel=(40.0, 53.4), bang=-20, bend=40, blen=14.0)
    KNEEL = dict(P=(26.4, 44.0), C=(29.0, 33.4), Hd=(33.0, 29.4), hup=(0.75, -0.8), hipn=(27.4, 44.4),
                 hipf=(25.4, 44.0), fn=(31.0, FLOOR), ff=(21.0, FLOOR), kpref=(1, -0.9), hf=(33.0, 46.0),
                 hb=(26.0, 47.0))

    def col(sq, burn, spread):
        return S.collapse(body, sq, burn, seed=3, spread=spread, pal=rag, cx=28.0, rise=12)
    return [
        (110, SP(P=(25.6, 35.8), C=(24.2, 24.2), Hd=(25.4, 19.0), hup=(-0.35, -1.0), hipn=(26.6, 36.2),
                 hipf=(24.8, 35.8), hf=(33.6, 34.0), hb=(21.0, 33.0),
                 sc=dict(IDLE_SC, hand=(33.6, 34.0), a=-108), eyes=3, straw=0.3, flash=True)),
        (140, SP(P=(25.8, 38.0), C=(25.6, 26.4), Hd=(28.0, 21.6), hup=(0.2, -1.0), hipn=(26.8, 38.4),
                 hipf=(25.0, 38.0), kpref=(1, -0.5), hf=(32.0, 40.0), hb=(22.0, 40.0),
                 sc=dict(butt=(38.0, 54.4), heel=(46.0, 26.0), bang=60, bend=45, blen=14.0), eyes=2, straw=0.6)),
        (150, SP(**KNEEL, sc=ground_sc, eyes=1, straw=0.9, hem=1)),
        (150, SP(**KNEEL, sc=ground_sc, eyes=0, hat=((36.0, 36.0), (0.8, -0.6)), post=col(0.6, 0.08, 0.3),
                 straw=0.5, straw_at=(28.0, 44.0))),
        (180, SP(**KNEEL, sc=ground_sc, eyes=0, hat=((31.0, 47.5), (0.35, -1.0)), post=col(0.32, 0.14, 0.55),
                 straw=0.8, straw_at=(28.0, 48.0))),
        (800, SP(**KNEEL, sc=ground_sc, eyes=0, hat=((30.0, 50.6), (0.25, -1.0)), post=col(0.2, 0.16, 0.7))),
    ]


def build(build_ase):
    K.setup(56, 56)
    anims, infos = S.render_anims(SPEC, LAYERS, draw_scare,
                                  [("hidden", a_hidden), ("rise", a_rise), ("idle", a_idle), ("walk", a_walk),
                                   ("reap", a_reap), ("lunge", a_lunge), ("hurt", a_hurt), ("death", a_death)],
                                  sway_key="C", loops=("hidden", "idle", "walk"))
    idle_i = 2
    hb = S.hurtbox(anims, ["Coat", "Head"], inset=(1, 1, 1, 0), tag=idle_i)
    for k in (5, 6):          # the low sweep: only the part of the arc in front of / below chest height
        infos["reap"][k]["hit"] = {q for q in infos["reap"][k]["hit"] if q[1] >= 22}
    reap = S.hit_rect(infos, "reap", [5, 6], x_min=30)
    lunge = S.hit_rect(infos, "lunge", [4, 5], x_min=31)
    meta = {"native": 1, "frame": [56, 56], "anchor": [28, 56],
            "hurtbox": hb,
            "attacks": {"reap": {"active": [5, 6], "hit": reap},
                        "lunge": {"active": [4, 5], "hit": lunge}},
            "telegraph": {"reap": {"frame": 4, "at": S.spawn_pt(infos["reap"][4]["bmid"])},
                          "lunge": {"frame": 0, "at": S.spawn_pt(infos["lunge"][0]["eye"])}},
            "post": "sp_post",
            "notes": "faces right, feet on the bottom row. Draw sp_post (same anchor) BEHIND him while `hidden`/"
                     "`rise` play (keep the post standing afterwards). hidden: strung on the post, eye-holes dark, "
                     "barely sways (use as the dormant state, not hittable until woken is fine). rise: 0 head lifts, "
                     "1-2 eyes kindle blue, 3 ropes snap, 4 drops, 5 lands (feet on floor), 6 grabs the scythe stuck in "
                     "the soil, 7 yanks it free -> idle. walk drags the scythe. reap: 0-3 draw back, 4 = held windup "
                     "(blade glint = telegraph), 5-6 active low sweep to the floor, 7-9 recover. lunge: 0 crouch "
                     "(eye flash = telegraph), 1-2 hop (drawn in place; engine moves him forward on 1-3), 3 chop "
                     "descends, 4-5 active (blade hooks into the floor), 6-7 wrench free. death ends as a heap of "
                     "straw and rags with the hat on top (hold last frame)."}
    S.export("sp_scarecrow", LAYERS, anims, meta, build_ase)
    return meta


# =========================================================================== the post
def draw_post():
    L = Layer("Post")
    R_ = Layer("Rope")
    # pole: rounded, split and chipped at the top, sunk in a little mound
    L.paint(n_capsule((POLE_X, POLE_TOP + 1.5), (POLE_X, FLOOR + 2), 2.0, 2.2, flat=0.9), "g", 0)
    L.erase([(27, POLE_TOP), (28, POLE_TOP), (29, POLE_TOP + 1), (26, POLE_TOP)])
    L.fixed({(27, POLE_TOP): "g3", (26, POLE_TOP + 1): "g4"})
    # crossbeam: squared, weathered plank
    bm = {(x, y) for x in range(BEAM_X0, BEAM_X1 + 1) for y in range(BEAM_Y0, BEAM_Y1 + 1)}
    bm -= {(BEAM_X0, BEAM_Y1), (BEAM_X1, BEAM_Y0)}
    L.paint(n_plate(bm, 1.0, (0.0, -0.1), 1.0), "g", 0)
    # grain / cracks / an iron spike where the beam meets the pole
    L.decal([(x, BEAM_Y0 + 1) for x in range(BEAM_X0 + 2, BEAM_X1 - 1) if hash01(x, 1, 3) < 0.45], ("g", 2))
    L.decal([(POLE_X - 1 + (y % 2), y) for y in range(24, FLOOR, 3)], ("g", 2))
    L.decal([(POLE_X, y) for y in range(28, 48) if hash01(y, 2, 5) < 0.3], ("g", 1))
    L.fixed({(27, BEAM_Y0 + 1): "I4", (28, BEAM_Y0 + 1): "I2"})
    # lashing where the beam crosses the pole
    for y in (BEAM_Y0 - 1, BEAM_Y1 + 1):
        for x in (26, 27, 28, 29):
            R_.fixed({(x, y): "H2" if (x + y) % 2 else "H1"})
    # frayed rope ends left at the wrists
    for k, rx in enumerate(ROPE_X):
        R_.fixed({(rx - 1, BEAM_Y0): "H2", (rx, BEAM_Y0): "H1", (rx + 1, BEAM_Y0): "H2"})
        for j in range(4 + k):
            x = rx + (1 if j > 1 and k == 0 else 0) - (1 if j > 2 and k == 1 else 0)
            R_.fixed({(x, BEAM_Y1 + 1 + j): "H2" if j < 3 else "H3"})
        R_.fixed({(rx - 1, BEAM_Y1 + 2): "H1"})
    # dirt mound + two stones
    G_ = FXLayer("Ground")
    for x in range(21, 36):
        h = 1 + (1 if 24 <= x <= 32 else 0) + (1 if 26 <= x <= 30 else 0)
        for j in range(h):
            G_.put([(x, FLOOR - j)], "X1" if j == h - 1 else "X0")
    for (sx, sy) in ((22, FLOOR - 1), (33, FLOOR - 1)):
        G_.put([(sx, sy), (sx + 1, sy)], "g3")
        G_.put([(sx, sy + 1), (sx + 1, sy + 1)], "g2")
    return {"Post": K.render_layer(L), "Rope": K.render_layer(R_), "Ground": G_.image()}


def build_post(build_ase):
    K.setup(56, 56)
    imgs = draw_post()
    K.export("sp_post", ["Ground", "Post", "Rope"], [("idle", [(1000, imgs)])], None, build=build_ase)
    return None


def post_preview():
    """Scarecrow hidden/rise frames composited over the post (alignment check) -> previews/sp_scarecrow_onpost.png"""
    K.setup(56, 56)
    post = K.flatten(draw_post(), ["Ground", "Post", "Rope"])
    # rebuild from the frames just rendered (works in --preview mode too)
    anims, _ = S.render_anims({"hidden": 2, "rise": 8}, LAYERS, draw_scare,
                              [("hidden", a_hidden), ("rise", a_rise)], sway_key="C", loops=("hidden",))
    frames = [K.flatten(imgs, LAYERS) for _, lst in anims for _, imgs in lst]
    sc, per = 6, 6
    cells = [post] + frames
    rows = (len(cells) + per - 1) // per
    out = Image.new("RGBA", (per * 58 * sc, rows * 58 * sc), K.BG)
    for i, f in enumerate(cells):
        cell = Image.new("RGBA", (56, 56), (38, 40, 52, 255))
        cell.alpha_composite(post)
        if i:
            cell.alpha_composite(f)
        out.alpha_composite(cell.resize((56 * sc, 56 * sc), Image.NEAREST), ((i % per) * 58 * sc, (i // per) * 58 * sc))
    out.save(os.path.join(K.ART, "previews", "sp_scarecrow_onpost.png"))
