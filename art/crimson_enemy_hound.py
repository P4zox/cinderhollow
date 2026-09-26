"""cm_hound -- a lean skeletal blood hound of the Crimson Manor (64x40, anchor [30, 40]).

Hairless black-crimson hide stretched over ribs, a long narrow skull with needle teeth, glowing red eyes, blood
dripping from the jaws, an iron collar with a broken chain.  Low, fast, sleek.  Faces RIGHT, feet on the bottom row.
Built by gen_crimson_enemies.py.   Tags: idle(4 loop) run(6 loop) bite(8: rear back, lunging snap, active [4,5])
hurt(2) death(6).

Poses are keyed in "sighthound units" (a 56x32 reference space, floor 31, anchor x 26) and mapped to the sheet by
T() -- uniform scale 1.06 -- so every joint, limb length and radius scales together (no proportion drift).
"""
import math

import crimson_kit as CK
import enemy_kit as K
from enemy_kit import (Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, poly_mask, n_plate, n_dome,
                       mask_disc)
from gen_enemies3 import n_tube, curve, rot, madd

W, H = 64, 40
FLOOR = H - 1
AX = 30
SC = 1.06
RX = 28.0                      # reference x that lands on the anchor
FL = 31.0                      # floor in reference units
LAYERS = ["FXBack", "FarLegs", "Tail", "Body", "NearHind", "NearFront", "Head", "Chain", "FX"]
FXL = {"FXBack", "FX"}
BODY = [n for n in LAYERS if n not in FXL]


def T(p):
    return (AX + (p[0] - RX) * SC, FLOOR - (FL - p[1]) * SC)


def V(v):
    return (v[0] * SC, v[1] * SC)


NEU = dict(P=(17.0, 15.0), S=(35.0, 15.5), arch=0.0, Hh=(44.5, 10.0), ha=12.0, jaw=0.0, ta=0.0, wave=0.0,
           hn=(15.0, FL, -2.4, -5.2), hf=(18.5, FL, -2.4, -5.2), fn=(36.0, FL, -0.3, -3.0), ff=(33.0, FL, -0.3, -3.0),
           eye=1, drip=True, lines=None, splash=None, wind=0.0, gore=0, chain=0.0)
PTS = ("P", "S", "Hh")


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def shift(p, dx):
    """Move a whole pose along x (reference units): body keys and paws."""
    q = dict(p)
    for k in ("P", "S", "Hh"):
        q[k] = (p[k][0] + dx, p[k][1])
    for k in ("hn", "hf", "fn", "ff"):
        q[k] = (p[k][0] + dx,) + tuple(p[k][1:])
    if p.get("lines"):
        x0, x1, ys = p["lines"]
        q["lines"] = (x0 + dx * SC, x1 + dx * SC, ys)
    if p.get("splash"):
        q["splash"] = (p["splash"][0] + dx * SC, p["splash"][1])
    return q


def hound_leg(L, hip, paw, front, bias):
    """hip in sheet coords; paw = (x, y, ox, oy) in reference units."""
    foot = T((paw[0], paw[1]))
    foot = (foot[0], foot[1] - 0.9)
    mid = add(foot, V((paw[2], paw[3])))
    if front:
        l1, l2 = 5.6 * SC, 5.4 * SC
        mid = CK.clamp_reach(hip, mid, l1 + l2 - 0.05)
        kn = ik(hip, mid, l1, l2, (-1, 0.15))
        radii = [1.9 * SC, 1.0 * SC, 0.8 * SC, 0.7 * SC]
    else:
        l1, l2 = 6.2 * SC, 6.0 * SC
        mid = CK.clamp_reach(hip, mid, l1 + l2 - 0.05)
        kn = ik(hip, mid, l1, l2, (1, 0.25))
        radii = [2.2 * SC, 1.1 * SC, 0.8 * SC, 0.7 * SC]
    L.paint(n_tube([hip, kn, mid, foot], radii), "h", bias)
    L.paint(n_dome((foot[0] + 1.1, foot[1] + 0.35), 2.0, 0.95, tilt=(0, -0.2)), "h", bias, ao=0)
    t = ip((foot[0] + 2.8, foot[1] + 0.6))
    L.fixed({t: "w3" if bias >= 0 else "w1", (t[0] - 1, t[1] + 1): "w2" if bias >= 0 else "w1"})
    return kn, mid


def draw(p, fi, sw, phase=1):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    info = {"hit": set()}
    P, S, Hh = T(p["P"]), T(p["S"]), T(p["Hh"])
    ha = p["ha"]
    ax_ = sub(S, P)
    ln = math.hypot(*ax_)
    fwd = (ax_[0] / ln, ax_[1] / ln)
    up = (fwd[1], -fwd[0])
    dn = (-up[0], -up[1])
    s_ = SC

    # ---- far legs
    Fl = Ls["FarLegs"]
    hound_leg(Fl, madd(P, (fwd, 1.4 * s_), (dn, 1.2 * s_)), p["hf"], False, -2)
    hound_leg(Fl, madd(S, (fwd, -0.8 * s_), (dn, 2.6 * s_)), p["ff"], True, -2)

    # ---- tail: long bare whip of vertebrae, ending in a point
    Tl = Ls["Tail"]
    ta, wv = p["ta"], p["wave"]
    t0 = madd(P, (fwd, -2.8 * s_), (up, 1.4 * s_))
    t1 = add(t0, V(rot((-3.6, 2.0 + 0.3 * sw), ta)))
    t2 = add(t1, V(rot((-3.4, 2.2 + wv), ta)))
    t3 = add(t2, V(rot((-3.0, 1.2 + wv * 1.6), ta)))
    tp = curve([t0, t1, t2, t3], 5)
    Tl.paint(n_tube(tp, [(1.45 - 1.05 * i / (len(tp) - 1)) * s_ for i in range(len(tp))]), "h", -1)
    for i, q in enumerate(polyline([ip(x) for x in tp])):
        if i % 3 == 0 and q in Tl.px:
            Tl.decal([q], ("h", 4))                                     # knuckled vertebrae

    # ---- body: haunch, deeply tucked loin, skeletal ribcage, deep brisket
    Bd = Ls["Body"]
    c0 = madd(P, (fwd, -1.6 * s_), (up, 0.2 * s_))
    c1 = madd(lerp(P, S, 0.3), (up, (0.9 + p["arch"]) * s_))
    c2 = madd(lerp(P, S, 0.66), (dn, 1.0 * s_), (up, p["arch"] * 0.4 * s_))
    c3 = madd(S, (dn, 1.7 * s_))
    c4 = madd(S, (fwd, 2.4 * s_), (dn, 0.7 * s_))
    cp = curve([c0, c1, c2, c3, c4], 6)
    keys = [(0, 2.8), (0.25, 1.65), (0.52, 3.3), (0.76, 3.85), (1.0, 2.5)]
    rr = []
    for i in range(len(cp)):
        t = i / (len(cp) - 1)
        for (ta_, ra), (tb, rb) in zip(keys, keys[1:]):
            if ta_ <= t <= tb:
                u = (t - ta_) / (tb - ta_)
                u = u * u * (3 - 2 * u)
                rr.append((ra + (rb - ra) * u) * s_)
                break
    bm = Bd.paint(n_tube(cp, rr), "h", 0)
    info["body"] = bm
    # ribs: five curved grooves with a lit ridge -- hide stretched over bone
    for i in range(5):
        rx = lerp(P, S, 0.46 + 0.1 * i)
        a_ = madd(rx, (up, (2.0 + p["arch"] * 0.3) * s_))
        m_ = madd(rx, (dn, 1.4 * s_), (fwd, -0.9 * s_))
        b_ = madd(rx, (dn, 3.9 * s_), (fwd, -1.2 * s_))
        pts = [q for q in polyline([ip(a_), ip(m_), ip(b_)]) if q in bm]
        Bd.decal(pts, ("h", 1))
        Bd.decal([(q[0] + 1, q[1]) for q in pts if (q[0] + 1, q[1]) in bm and (q[0] + 1, q[1]) not in pts], ("h", 4))
    # vertebral spurs along the spine
    for i in range(8):
        t = 0.08 + i * 0.11
        c = lerp(P, S, t)
        topc = madd(c, (up, (3.0 + p["arch"] * (1 - abs(t - 0.4)) + (0.3 if 0.35 < t < 0.8 else -0.3)) * s_))
        q = ip(topc)
        guard = 0
        while q in bm and guard < 8:
            q = (q[0], q[1] - 1)
            guard += 1
        if i % 2 == 0:
            Bd.fixed({q: "h4"})
    # hip bone and scapula points
    Bd.decal([ip(madd(P, (up, 2.0 * s_), (fwd, 0.3 * s_)))], ("h", 5))

    # ---- near hind leg with lean haunch
    Nh = Ls["NearHind"]
    hip = madd(P, (fwd, 0.4 * s_), (dn, 1.0 * s_))
    Nh.paint(n_dome(madd(hip, (fwd, -0.3 * s_), (up, 0.8 * s_)), 2.7 * s_, 3.3 * s_, tilt=(-0.1, -0.1)), "h", 0)
    hound_leg(Nh, hip, p["hn"], False, 0)
    # ---- near front leg with shoulder blade
    Nf = Ls["NearFront"]
    sho = madd(S, (fwd, -0.4 * s_), (dn, 2.4 * s_))
    Nf.paint(n_dome(madd(sho, (up, 1.8 * s_), (fwd, -0.4 * s_)), 2.0 * s_, 3.0 * s_, tilt=(-0.1, -0.2)), "h", 0)
    hound_leg(Nf, sho, p["fn"], True, 0)
    info["hit"] |= set(Nf.px)

    # ---- neck + head: long narrow skull, laid-back ear, needle teeth, red eye
    Hd = Ls["Head"]
    G = lambda x, y: add(Hh, V(rot((x, y), ha)))          # noqa: E731
    hb = G(-3.2, 0.6)
    n0 = madd(S, (fwd, 1.2 * s_), (up, 1.2 * s_))
    n1 = madd(lerp(n0, hb, 0.5), (up, 1.0 * s_))
    nk = curve([n0, n1, hb], 4)
    Hd.paint(n_tube(nk, [r * s_ for r in (2.6, 2.3, 2.0, 1.8, 1.6, 1.5, 1.5, 1.5, 1.5)][:len(nk)]
                    + [1.5 * s_] * max(0, len(nk) - 9)), "h", 0)
    ear = [G(-2.4, -1.3), G(-0.4, -2.0), G(-7.4, -5.0 + 0.4 * sw)]
    Hd.paint(n_plate(poly_mask(ear), 0.8, (-0.1, -0.3)), "h", -1, ao=0)
    hinge = (-0.6, 1.4)
    ja = p["jaw"] * 42.0
    J = lambda x, y: G(*add(hinge, rot(sub((x, y), hinge), ja)))   # noqa: E731
    jaw = [J(-1.2, 1.1), J(10.0, 1.3), J(9.6, 2.0), J(2.0, 2.8), J(-1.6, 2.5)]
    if p["jaw"] > 0.15:                                                  # blood-dark gullet
        Hd.fixed({q: ("b1" if hash01(*q, 3) < 0.6 else "b0") for q in poly_mask([G(-1.0, 1.2), G(10.6, 1.2),
                                                                                    J(10.0, 1.3)])})
    jm = poly_mask(jaw)
    Hd.paint(n_plate(jm, 0.8, (0.0, 0.3)), "h", -1)
    skull = [G(-3.6, -1.1), G(-1.2, -2.2), G(1.8, -2.0), G(3.4, -1.1), G(10.6, 0.1), G(11.8, 0.6), G(11.2, 1.3),
             G(2.4, 1.3), G(-1.4, 2.2), G(-3.7, 1.0)]
    sm = poly_mask(skull)
    Hd.paint(n_plate(sm, 1.3, (-0.15, -0.3), 1.1), "h", 0)
    Hd.decal([ip(G(11.2, 0.4))], ("h", 5))                                   # wet nose
    Hd.decal([q for q in line(G(-1.0, 1.8), G(2.4, 1.1)) if q in sm], ("h", 1))   # cheekbone
    Hd.decal([q for q in line(G(1.6, -1.6), G(9.0, -0.1)) if q in sm], ("h", 4))  # bony muzzle ridge
    # needle teeth: rows along both jaws
    teeth = {}
    if p["jaw"] > 0.15:
        for x in (3.0, 4.6, 6.2, 7.8, 9.4):
            teeth[ip(G(x, 1.7))] = "w4"
            teeth[ip(G(x + 0.4, 2.4))] = "w3"
        for x in (3.8, 5.4, 7.0, 8.6):
            teeth[ip(J(x, 0.9))] = "w3"
    else:
        for x in (4.0, 6.0, 8.2):
            teeth[ip(G(x, 1.8))] = "w4"                                      # needles over the lip
    Hd.fixed(teeth)
    e = ip(G(1.8, -0.6))
    info["eye"] = e
    CK.eye_glow(FX, e, p["eye"], 1, trail=2 if p["eye"] >= 3 else 0)
    info["hit"] |= set(Hd.px)
    info["jaw"] = G(11.0, 1.6)

    # ---- iron collar with a broken chain
    Ch = Ls["Chain"]
    cc = lerp(n0, hb, 0.25)
    nd = sub(hb, n0)
    nl = math.hypot(*nd) or 1
    nd = (nd[0] / nl, nd[1] / nl)
    perp = (-nd[1], nd[0])
    band = poly_mask([add(cc, (perp[0] * 3.1 - nd[0] * 1.3, perp[1] * 3.1 - nd[1] * 1.3)),
                      add(cc, (perp[0] * 3.1 + nd[0] * 1.3, perp[1] * 3.1 + nd[1] * 1.3)),
                      add(cc, (-perp[0] * 3.1 + nd[0] * 1.3, -perp[1] * 3.1 + nd[1] * 1.3)),
                      add(cc, (-perp[0] * 3.1 - nd[0] * 1.3, -perp[1] * 3.1 - nd[1] * 1.3))])
    Ch.paint(n_plate(band, 0.9, (-0.2, -0.3), 1.2), "I", 0)
    lowest = max(band, key=lambda q: q[1])
    Ch.fixed({(lowest[0], lowest[1]): "I4"})
    top_ = min(band, key=lambda q: q[1])
    Ch.fixed({top_: "I5", (top_[0] + 1, top_[1] + 1): "I4"})                      # studs catching the light
    for q in list(band)[::5]:
        if hash01(*q, 12) < 0.5:
            Ch.decal([q], ("R", 2))                                          # rust
    # three swinging links and a broken, open one at the end
    ang = 90 + p["chain"] * 40 + sw * 10
    o = (lowest[0] + 0.5, lowest[1] + 1.2)
    pix = {}
    for k in range(4):
        d = dirv(ang + k * p["chain"] * 6)
        c = add(o, (d[0] * (1.6 + k * 2.2), d[1] * (1.6 + k * 2.2)))
        if k % 2 == 0:
            ring = [(0, -1), (1, 0), (0, 1), (-1, 0)] if k < 3 else [(0, -1), (1, 0), (-1, 0)]
        else:
            ring = [(0, -1), (0, 0), (0, 1)]
        for dx, dy in ring:
            q = (int(round(c[0])) + dx, int(round(c[1])) + dy)
            pix[q] = "I3" if dy <= 0 else "I2"
    Ch.fixed({q: c for q, c in pix.items() if q[1] <= FLOOR})

    # ---- rim light along the top line so the dark hide separates from dark rooms
    for L_ in (Bd, Hd, Nh, Nf, Tl):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "h"
                  and not isinstance(e_[3], str)], ("h", 4))
    # ---- blood: drips from the jaws (and chest when bloodied)
    if p["drip"]:
        CK.blood_drip(FX, G(7.5, 2.8 + p["jaw"] * 2.5), fi, 3.0, seed=1)
        CK.blood_drip(FX, G(4.2, 2.9 + p["jaw"] * 1.5), fi + 2, 2.2, seed=2)
        if p["jaw"] > 0.5:
            CK.blood_drip(FX, J(9.0, 2.6), fi + 1, 2.0, seed=3)
    if p["lines"]:
        x0, x1, ys = p["lines"]
        for i, y in enumerate(ys):
            a = x0 + (i * 3) % 4
            b = x1 - (i * 5) % 6
            for x in range(int(a), int(b)):
                FX.put([(x, int(y))], "b2" if x > (a + b) / 2 else "h3")
    if p["splash"]:
        cx, stg = p["splash"]
        for k in range(10):
            a = -math.pi * (0.08 + 0.84 * hash01(k, 1, 31))
            r = (2 + 6 * hash01(k, 2, 31)) * (0.7 if stg == 1 else 1.1)
            q = ip((cx + math.cos(a) * r * 1.3, FLOOR - 0.5 + math.sin(a) * r * (0.8 if stg == 1 else 0.4)
                    + (0 if stg == 1 else 1.5)))
            FX.put([q], ("a2" if k % 3 else "a3") if stg == 1 else "a1")
    return Ls, info


def dirv(a):
    return (math.cos(math.radians(a)), math.sin(math.radians(a)))


# =========================================================================== animations (reference units)
def a_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.4, 0.7, 0.3)[i]
        fr.append((180, P_(S=(35.0, 15.5 + b * 0.5), P=(17.0, 15.0 + b * 0.2), Hh=(44.5 + b * 0.2, 10.0 + b * 0.8),
                           ha=12 + b * 3, ta=-4 + 8 * math.sin(i * math.pi / 2), wave=math.sin(i * math.pi / 2 + 1),
                           chain=0.1 * math.sin(i * math.pi / 2))))
    return fr


def a_run():
    L = [  # P, S, arch, Hh, ha, hind near, hind far, front near, front far
        ((15.0, 13.5), (37.0, 14.0), -0.8, (47.5, 9.8), 6, (4.5, 25.0, 4.5, -1.8), (6.5, 26.5, 4.2, -2.2),
         (50.0, 24.5, -3.6, 0.2), (47.5, 26.5, -3.4, -0.6)),
        ((16.0, 14.5), (37.0, 15.5), 0.0, (46.5, 10.8), 10, (10.0, 24.0, 3.6, -3.0), (12.0, 25.5, 3.2, -3.2),
         (43.5, FL, -1.5, -3.0), (47.0, 27.0, -3.0, -1.5)),
        ((18.0, 15.0), (36.0, 16.0), 1.2, (45.0, 11.8), 14, (20.0, 25.0, -1.0, -4.2), (22.0, 26.5, -1.2, -4.0),
         (35.0, FL, 1.2, -3.0), (39.5, FL, -0.5, -3.0)),
        ((19.0, 13.5), (35.0, 14.5), 2.6, (44.5, 10.8), 12, (29.0, 26.0, -3.0, -3.5), (31.0, 27.0, -3.0, -3.2),
         (27.0, 25.5, 3.0, -2.2), (29.0, 26.5, 2.8, -2.0)),
        ((19.0, 15.0), (36.0, 15.0), 1.5, (46.0, 10.8), 8, (26.0, FL, -2.6, -4.6), (29.0, FL, -2.6, -4.6),
         (41.0, 26.0, -2.2, -2.6), (38.0, 27.0, -1.5, -3.0)),
        ((17.0, 14.5), (37.0, 14.5), 0.0, (47.0, 10.3), 6, (11.0, FL, -1.0, -5.0), (15.0, FL, -1.8, -5.0),
         (47.0, 25.5, -3.4, -0.8), (44.0, 27.0, -3.0, -1.6)),
    ]
    fr = []
    for i, (P, S, ar, Hh, ha, hn, hf, fn, ff) in enumerate(L):
        fr.append((70, shift(P_(P=P, S=S, arch=ar, Hh=Hh, ha=ha, hn=hn, hf=hf, fn=fn, ff=ff, ta=-14 + 10 * math.sin(i * 1.05),
                          wave=1.2 * math.sin(i * 1.05 + 1.5), wind=-2.0, chain=-0.8 + 0.3 * math.sin(i * 1.05)), -1.5)))
    return fr


def a_bite():
    """Rear back (head high, jaws parting), hold, then a long lunging snap: jaws open wide f4, shut far forward f5."""
    stand = dict(hn=(15.0, FL, -2.4, -5.2), hf=(18.5, FL, -2.4, -5.2), fn=(36.0, FL, -0.3, -3.0), ff=(33.0, FL, -0.3, -3.0))
    return [
        (120, P_(**stand, P=(16.5, 15.4), S=(34.5, 16.2), Hh=(43.6, 11.6), ha=18, jaw=0.1, ta=-6, chain=0.1)),
        (140, P_(P=(15.2, 16.4), S=(32.6, 14.6), arch=1.0, Hh=(39.8, 6.8), ha=-18, jaw=0.35, eye=2, ta=-20, wave=1.0,
                 hn=(14.0, FL, -2.0, -4.8), hf=(17.0, FL, -2.0, -4.8), fn=(35.0, FL, 0.8, -2.8),
                 ff=(32.5, FL, 0.8, -2.8), chain=0.5)),
        (260, P_(P=(14.8, 16.8), S=(32.0, 14.8), arch=1.3, Hh=(39.0, 6.4), ha=-22, jaw=0.45, eye=3, ta=-26, wave=1.4,
                 hn=(13.6, FL, -1.8, -4.6), hf=(16.6, FL, -1.8, -4.6), fn=(35.0, FL, 1.2, -2.6),
                 ff=(32.5, FL, 1.2, -2.6), chain=0.7)),
        (60, P_(P=(18.5, 15.6), S=(37.0, 15.0), arch=-0.4, Hh=(46.5, 10.8), ha=4, jaw=0.8, eye=3, ta=-4,
                hn=(13.0, FL, 1.0, -4.8), hf=(15.5, FL, 1.0, -4.8), fn=(40.0, FL, -1.6, -3.0), ff=(37.5, 28.5, -2.0, -2.0),
                chain=-0.3, wind=3, lines=(4, 20, (13, 16, 19)))),
        (70, P_(P=(21.0, 15.8), S=(40.0, 15.6), arch=-0.8, Hh=(50.5, 12.6), ha=10, jaw=1.0, eye=3, ta=6, wave=0.6,
                hn=(15.0, FL, 3.2, -4.2), hf=(17.0, FL, 3.0, -4.4), fn=(46.0, FL, -2.4, -2.6), ff=(43.0, 28.0, -2.6, -1.6),
                chain=-0.8, wind=4, lines=(6, 24, (12, 15, 18, 21)))),
        (90, P_(P=(21.0, 16.2), S=(40.2, 16.6), arch=-0.4, Hh=(51.0, 14.0), ha=16, jaw=0.0, eye=3, ta=10, wave=-0.4,
                hn=(16.0, FL, 2.4, -4.6), hf=(18.0, FL, 2.2, -4.6), fn=(46.0, FL, -1.2, -3.0), ff=(43.0, FL, -1.0, -3.0),
                chain=-1.0, wind=2, splash=(46, 1))),
        (140, P_(P=(19.5, 15.6), S=(37.8, 15.8), Hh=(47.4, 11.6), ha=16, jaw=0.2, eye=2, ta=2,
                 hn=(16.0, FL, -1.6, -5.0), hf=(18.0, FL, -1.6, -5.0), fn=(41.5, FL, -0.6, -3.0),
                 ff=(38.5, FL, -0.6, -3.0), chain=-0.3, splash=(46, 2))),
        (170, P_(P=(17.5, 15.2), S=(35.3, 15.6), Hh=(44.7, 10.4), ha=13,
                 hn=(15.5, FL, -2.4, -5.2), hf=(18.5, FL, -2.4, -5.2), fn=(36.2, FL, -0.3, -3.0),
                 ff=(33.2, FL, -0.3, -3.0))),
    ]


def a_hurt():
    return [
        (90, P_(P=(15.0, 15.0), S=(32.0, 14.0), arch=1.0, Hh=(40.0, 7.0), ha=-26, jaw=0.6, eye=3,
                hn=(13.0, FL, -2.2, -5.2), hf=(16.5, FL, -2.2, -5.2), fn=(34.0, 28.5, -1.0, -2.8), ff=(31.0, FL, -0.3, -3.0),
                ta=-20, chain=0.9)),
        (140, P_(P=(16.0, 15.0), S=(33.8, 15.0), arch=0.5, Hh=(42.5, 8.8), ha=2, jaw=0.2, eye=2,
                 hn=(14.0, FL, -2.4, -5.2), hf=(17.5, FL, -2.4, -5.2), fn=(35.0, FL, -0.3, -3.0), ff=(32.0, FL, -0.3, -3.0),
                 ta=-8, chain=0.3)),
    ]


def a_death():
    def ash(frac, pool):
        def f(imgs, ph):
            out = CK.crumble(imgs, frac, BODY, (30.0, 34.0), seed=9, radius=24.0) if frac > 0 else dict(imgs)
            fx = out["FX"].copy()
            px = fx.load()
            for x in range(int(31 - pool), int(31 + pool) + 1):
                t = abs(x + .5 - 31) / max(1.0, pool)
                if t < 1 and 0 <= x < W and px[x, FLOOR][3] == 0:
                    px[x, FLOOR] = K.RGBA["b2" if t < 0.6 else "b1"]
            out["FX"] = fx
            return out
        return f
    lie = dict(P=(17.0, 24.0), S=(34.0, 25.0), arch=0.5, Hh=(43.0, 26.5), ha=12, eye=0, drip=False,
               hn=(22.0, FL, -3.5, -1.5), hf=(24.5, FL, -3.5, -1.5), fn=(40.5, FL, -3.2, -0.5), ff=(38.0, FL, -3.0, -0.8),
               ta=20, wave=0.0, chain=1.6)
    return [
        (100, P_(P=(15.0, 16.0), S=(31.0, 12.0), arch=0.5, Hh=(38.0, 5.5), ha=-36, jaw=0.8, eye=3,
                 hn=(13.0, FL, -2.2, -5.2), hf=(16.0, FL, -2.2, -5.2), fn=(35.0, 24.0, -1.5, -2.5), ff=(33.0, 26.0, -1.5, -2.5),
                 ta=-30, chain=0.8)),
        (130, P_(P=(16.0, 20.0), S=(33.0, 21.5), arch=1.0, Hh=(41.5, 22.0), ha=30, jaw=0.4, eye=1,
                 hn=(12.0, FL, -3.0, -3.5), hf=(19.0, FL, -3.0, -3.5), fn=(38.0, FL, -1.5, -2.5), ff=(34.5, FL, -1.0, -2.5),
                 ta=0, chain=1.2)),
        (160, P_(**dict(lie, eye=1, jaw=0.3), post=ash(0.0, 3))),
        (140, P_(**lie, post=ash(0.35, 6))),
        (150, P_(**lie, post=ash(0.7, 10))),
        (500, P_(**lie, post=ash(1.01, 12))),
    ]


def a_bite_fit():
    """The snap lunges forward ~5 units; keep the jaws inside the frame (the engine carries the hound forward)."""
    fr = a_bite()
    out = []
    for k, (ms, p) in enumerate(fr):
        dx = (0, -0.5, -0.5, -2.5, -4.5, -4.5, -3.0, -1.0)[k]
        out.append((ms, shift(p, dx)))
    return out


TAGDEFS = [("idle", a_idle), ("run", a_run), ("bite", a_bite_fit), ("hurt", a_hurt), ("death", a_death)]
COUNTS = dict(idle=4, run=6, bite=8, hurt=2, death=6)
LOOPS = ("idle", "run")
RUN_KW = dict(sway_key="S")


def setup():
    K.setup(W, H)


draw_fn = draw


def meta(infos, tags, frames):
    idle = infos["idle"][0]
    bb = CK.bbox(idle["body"] | idle["hit"])
    hurt = [bb[0] + 2, bb[1] + 1, bb[2] - 6, H - (bb[1] + 1)]
    bite = CK.attack_rect(infos, "bite", 4, 5, x_min=AX + 14)
    return {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "attacks": {"bite": bite},
        "telegraph": {"bite": {"frame": 2, "at": CK.pt(infos["bite"][2]["eye"])}},
        "notes": "Faces right, anchor = feet (x 30). bite: rears back f1-2 (telegraph f2: eye flare, jaws parting), "
                 "lunging snap f3-5 drawn in place (the engine may carry it forward ~16-24px over f3-f5), jaws wide "
                 "f4, snapped shut f5 (active 4-5), recover f6-7. run: gallop, 70ms frames, loop.",
    }
