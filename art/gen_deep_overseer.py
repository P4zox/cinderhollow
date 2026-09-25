#!/usr/bin/env python3
"""The Forge Overseer (agent D) -- mini-boss of the Foundry Halls: the elite of Ashwright's forge-guard.

    python3 art/gen_deep_overseer.py [--preview]

overseer  96x80, faces right, feet on the bottom row, ~66 px tall.  A tall blackened-iron warden with an Ashwright-gold
crest; in its near hand a tower FORGE SHIELD (a slab of anvil iron with a glowing furnace grille, gilt rim, spiked
brow); in its far hand a long FLAME-LANCE fed from a furnace tank on its back (two vent stacks).
Tags: idle(6) walk(8) flame(18: raise lance 0-2, kindle 3-4, flame 5-14 sweeping high->low, recover 15-17)
      bash(11: crouch 0-2, charge active 4-7) slam(13: shield hauled overhead 0-6 = front OPEN, crash 7-8)
      vent(10: hunch 0-3, back vents blast 4-6 behind it) stagger(4: shield dropped, kneeling) death(12)
Meta: hurtbox, attacks (bash, slam, vent windows), flame nozzle point + angle per flame frame, telegraphs, shield rect.
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import gen_deep_enemies as DE  # noqa: E402  (ramps S/U/F + helpers)
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, swept  # noqa: E402
import gen_enemies3 as E3  # noqa: E402
from gen_enemies3 import n_tube, curve, mk, spawn_pt, rot, madd, disc_glow, halo_dots, collapse  # noqa: E402

BUILD = "--preview" not in sys.argv
DE.BUILD = BUILD
E3.BUILD = BUILD
E3.SPEC_FRAMES["overseer"] = dict(idle=6, walk=8, flame=18, bash=11, slam=13, vent=10, stagger=4, death=12)
GLOW = DE.GLOW
LAYERS = ["Tank", "FarArm", "FarLeg", "Body", "Head", "NearLeg", "Shield", "FX"]
FL = 79.0
NEU = dict(P=(38.0, 50.0), C=(40.0, 31.0), Hd=(42.0, 19.5), ha=0.0,
           nk=(43.4, 64.0), nf=(45.0, FL), fk=(34.6, 64.4), ff=(31.6, FL),
           S=(57.0, 47.0), sa=0.0, sup=False, lh=(47.0, 33.0), la=-4.0, noz=0.3, vent=0.3, visor=1.0, core=1.0,
           rot=0.0, piv=(0, 0), smoke=0, bash=0.0, sparks=0, wind=0.0, dropped=False, crack=0.0)
OP = mk(NEU)


def shield(L, FX, c, ang, fi, glow, hot=0.0):
    """Tower forge-shield: a tall slab with an anvil-horn brow, gilt rim, furnace grille; returns its mask."""
    R_ = lambda x, y: add(c, rot((x, y), ang))
    outline = [R_(-5.0, -20.0), R_(1.0, -22.5), R_(7.5, -21.0), R_(9.5, -17.0), R_(6.8, -15.4), R_(6.6, 16.0), R_(3.5, 21.0),
               R_(-3.0, 21.0), R_(-6.0, 16.5), R_(-6.4, -15.0)]
    m = poly_mask(outline)
    L.paint(n_plate(m, 2.4, (-0.35, -0.15), 1.25, fold=lambda x, y: (0.25, 0)), "F", 0)
    # gilt rim
    edge = {q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    inner = {q for q in m if q not in edge and any((q[0] + a, q[1] + b) in edge for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    L.decal(list(inner), "G2")
    L.decal([q for q in inner if q[1] < c[1] - 10 or q[0] < c[0] - 3], "G3")
    # spiked brow
    for x in (-3.0, 1.0, 5.0):
        tip = R_(x, -26.0 + abs(x - 1) * 0.5)
        L.paint(n_plate(poly_mask([R_(x - 1.6, -20.6), R_(x + 1.6, -21.2), tip]), 0.6, (-0.2, -0.5)), "F", 1, ao=0)
    # furnace grille: horizontal slots glowing with the fire inside
    for k, yy in enumerate((-8.0, -4.0, 0.0, 4.0)):
        for q in polyline([ip(R_(-2.4, yy)), ip(R_(3.6, yy))]):
            if q in m:
                g_ = glow + hot + 0.3 * math.sin(fi * 1.7 + k)
                L.fixed({q: "O4" if g_ > 1.6 else "O3" if g_ > 0.9 else "O2", (q[0], q[1] + 1): "F1"})
    # Ashwright's seal below the grille
    sc = ip(R_(0.6, 10.0))
    L.fixed({sc: "Y1", (sc[0] - 1, sc[1]): "G3", (sc[0] + 1, sc[1]): "G4", (sc[0], sc[1] - 1): "G4", (sc[0], sc[1] + 1): "G2"})
    if hot > 0.5:   # red-hot in phase 2 overheating
        L.decal([q for q in edge if hash01(*q, 3) < 0.5], "U4")
    DE.glow_under(L, ("U2", "U1"), depth=1)
    return m


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    P, C, Hd = T(p["P"]), T(p["C"]), T(p["Hd"])
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    # ---- furnace tank on the back + two vent stacks
    Tk = Ls["Tank"]
    tc = F(-9.0, -ln + 6.0)
    Tk.paint(n_capsule(F(-9.0, -ln - 2.0), F(-9.5, -ln + 13.0), 5.2, 4.6), "F", -1)
    Tk.decal([q for q in line(F(-13.6, -ln + 5.0), F(-4.6, -ln + 5.0)) if q in Tk.px], "G2")
    for k in range(2):
        b, t = F(-12.5, -ln + 2.5 + k * 6.0), F(-17.5, -ln + 1.0 + k * 6.0)
        Tk.paint(n_capsule(b, t, 1.8, 1.5), "F", 0)
        Tk.paint(n_capsule(t, madd(t, (sub(t, b), 0.08)), 2.2, 2.2), "F", 1, ao=0)
        mouth = ip(madd(t, (sub(t, b), 0.14)))
        v = p["vent"]
        FX.put([mouth], "O4" if v > 1.2 else "O2")
        if v > 1.0:
            d = sub(t, b); l = math.hypot(*d); d = (d[0] / l, d[1] / l)
            for j in range(int(v * 4)):
                q = madd(mouth, (d, 1.5 + j * 1.6), ((-d[1], d[0]), math.sin(j * 1.3 + fi) * 0.8))
                disc_glow(FX, q, 1.0 + j * 0.35 * (v / 2), GLOW[:5] if v > 1.8 else GLOW[1:5])
        for j in range(2 + p["smoke"] * 2):
            tt = (j / 4 + fi * 0.17) % 1.0
            FX.put([ip((mouth[0] - tt * 6 + math.sin(j * 2 + tt * 5), mouth[1] - 1 - tt * 10))], "S3" if tt < 0.5 else "S2")
        info.setdefault("vents", []).append(mouth)
    # ---- far arm + flame-lance
    Fa = Ls["FarArm"]
    shF = F(-3.0, -ln + 3.0)
    lh = T(p["lh"])
    el = ik(shF, lh, 9.0, 8.4, (-0.3, 1))
    Fa.paint(n_tube([shF, el, lh], [3.4, 2.8, 2.6]), "F", -1)
    Fa.paint(n_dome(lh, 2.6, 2.6), "F", -1, ao=0)
    la = p["la"] + p["rot"]
    d = (math.cos(math.radians(la)), math.sin(math.radians(la)))
    back_ = madd(lh, (d, -7.0))
    tip = madd(lh, (d, 22.0))
    Fa.paint(n_capsule(back_, tip, 1.5, 1.3), "F", 0)
    Fa.paint(n_capsule(madd(tip, (d, -3.5)), madd(tip, (d, 1.0)), 2.3, 2.0), "F", 1, ao=0)
    Fa.decal([q for q in line(madd(lh, (d, 4)), madd(lh, (d, 16))) if q in Fa.px][::3], "G3")
    muzzle = madd(tip, (d, 2.0))
    Fa.fixed({ip(muzzle): "O5" if p["noz"] > 1.4 else "O3"})
    if p["noz"] > 0.5:
        disc_glow(FX, madd(muzzle, (d, 1.4)), 0.8 + p["noz"] * 1.1, GLOW[:4])
    if p["noz"] > 1.2:
        halo_dots(FX, madd(muzzle, (d, 1.4)), 3.5 + p["noz"], 12, fi, ("O3", "O2"))
    # hose from tank to lance
    hose = curve([F(-6.0, -ln + 10.0), lerp(F(-6.0, -ln + 10.0), back_, 0.5), back_], 6)
    for q in dict.fromkeys(polyline([ip(v) for v in hose])):
        if q not in Fa.px:
            Fa.fixed({q: "F3"})
    info["muzzle"] = muzzle
    info["lang"] = la
    # ---- far leg
    Fl = Ls["FarLeg"]
    Fl.paint(n_tube([F(-3.0, 1.0), T(p["fk"]), T(p["ff"])], [4.4, 3.6, 3.0]), "F", -2)
    ft = T(p["ff"])
    Fl.paint(n_plate(poly_mask([add(ft, (-4.4, 1)), add(ft, (-4.0, -3.8)), add(ft, (4.8, -2.4)), add(ft, (6.0, 1))]), 1.2, (0, -0.4)), "F", -2)
    # ---- body: tall cuirass, gilt edges, furnace core; faulds
    Bd = Ls["Body"]
    torso = [F(-8.4, -ln - 1.4), F(7.4, -ln - 1.0), F(8.6, -ln + 5.4), F(4.6, -ln + 13.0), F(3.4, -1.6), F(-3.8, -1.6), F(-6.4, -ln + 12.4),
             F(-9.2, -ln + 4.4)]
    tm = poly_mask(torso)
    Bd.paint(n_plate(tm, 3.0, (-0.25, -0.2), 1.25), "F", 0)
    Bd.decal([q for q in polyline([ip(F(-8.4, -ln - 1.4)), ip(F(7.4, -ln - 1.0))]) if q in tm], "G3")
    Bd.decal([q for q in polyline([ip(F(-0.6, -ln + 1.0)), ip(F(0.4, -ln + 11.0))]) if q in tm], ("F", 5))
    fau = [F(-6.4, -2.6), F(5.4, -2.6), F(7.0, 7.0), F(-8.0, 7.0)]
    fm = poly_mask(fau)
    Bd.paint(n_plate(fm, 1.6, (-0.2, 0.1)), "F", -1)
    for k in range(4):
        Bd.decal([q for q in line(F(-7.2, 0.0 + k * 1.8), F(6.2, 0.0 + k * 1.8)) if q in fm], ("F", 1))
    Bd.decal([q for q in line(F(-6.4, -2.6), F(5.4, -2.6)) if q in Bd.px], "G3")
    cc = ip(F(0.6, -ln + 7.0))
    gr = {}
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dx) + abs(dy) <= 4:
                gr[(cc[0] + dx, cc[1] + dy)] = ("F1" if dx % 2 else ("O4" if p["core"] > 1.3 else "O3") if abs(dy) < 3 else "O2") if p["core"] > 0 else "F1"
    Bd.fixed(gr)
    info["hit"] |= set(tm)
    # ---- head: tall helm, back-swept gold-edged crest horns, a visor slit of fire
    Hl = Ls["Head"]
    G = lambda x, y: add(Hd, rot((x, y), p["ha"]))
    Hl.paint(n_tube([F(0.4, -ln - 0.6), G(-0.4, 3.4)], [3.4, 3.0]), "F", -1)
    helm = [G(-3.6, 3.6), G(-4.0, -1.8), G(-2.8, -5.4), G(0.6, -6.8), G(3.8, -5.2), G(4.8, -1.2), G(4.2, 2.8), G(2.0, 4.2)]
    hm = poly_mask(helm)
    Hl.paint(n_plate(hm, 1.8, (-0.3, -0.35), 1.3), "F", 0)
    for (a0, a1, a2, b) in (((-2.0, -5.0), (-7.4, -6.2), (-13.4, -6.0), 0), ((0.4, -6.4), (-5.0, -8.8), (-11.6, -9.6), 1)):
        hp_ = curve([G(*a0), G(*a1), G(*a2)], 5)
        Hl.paint(n_tube(hp_, [1.9 - 1.5 * i / (len(hp_) - 1) for i in range(len(hp_))]), "F", b, ao=0)
        Hl.fixed({ip(G(*a2)): "G4"})
    Hl.decal([q for q in line(G(-3.8, 3.4), G(2.2, 4.2)) if q in hm], "G2")
    vis = [ip(G(x, 0.2)) for x in (0.4, 1.4, 2.4, 3.4)]
    Hl.fixed({q: ("O4" if i >= 2 and p["visor"] > 1.2 else "O3" if p["visor"] > 0.5 else "F1") for i, q in enumerate(vis)})
    info["visor"] = G(2.4, 0.2)
    info["hit"] |= set(Hl.px)
    # ---- near leg
    Nl = Ls["NearLeg"]
    Nl.paint(n_tube([F(2.4, 0.6), T(p["nk"]), T(p["nf"])], [4.6, 3.8, 3.2]), "F", 0)
    Nl.paint(n_dome(T(p["nk"]), 3.5, 3.2, tilt=(-0.2, -0.2)), "F", 1, ao=0)
    Nl.decal([ip(T(p["nk"])), ip(add(T(p["nk"]), (1, 0)))], "G3")
    ft = T(p["nf"])
    Nl.paint(n_plate(poly_mask([add(ft, (-4.6, 1)), add(ft, (-4.2, -4.0)), add(ft, (5.0, -2.6)), add(ft, (6.6, 1))]), 1.2, (0, -0.4)), "F", 0)
    # ---- near arm + shield (the shield covers the front of the body)
    Sh = Ls["Shield"]
    shN = F(5.0, -ln + 3.0)
    Sh.paint(n_dome(madd(shN, ((0, -1), 1.0)), 5.4, 4.4, tilt=(-0.2, -0.4)), "F", 1)
    Sh.decal([q for q in polyline([ip(madd(shN, ((-1, 0), 5.0))), ip(madd(shN, ((1, 0.2), 5.0)))]) if q in Sh.px], "G3")
    S = T(p["S"])
    grip = madd(S, ((-1, 0), 4.0))
    el2 = ik(shN, grip, 8.0, 8.0, (-0.2, 1))
    Sh.paint(n_tube([shN, el2, grip], [3.2, 2.8, 2.6]), "F", 0)
    sm = shield(Sh, FX, S, p["sa"] + p["rot"], fi, 1.0 + p["core"] * 0.4, hot=p["crack"])
    info["shield"] = sm
    info["hit"] |= sm
    for L_ in (Bd, Hl, Nl, Fl, Fa):
        DE.glow_under(L_, ("U2", "U1"), depth=1)
    for L_ in (Bd, Hl, Nl, Sh, Tk):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "F" and not isinstance(e_[3], str)], ("F", 5))
    if p["bash"] > 0:
        bb = K.bbox(sm)
        for k, y in enumerate(range(bb[1] + 4, bb[1] + bb[3] - 2, 5)):
            x1 = bb[0] - 2
            for x in range(x1 - 14 + k % 3 * 2, x1):
                FX.put([(x, y)], "O3" if x > x1 - 6 else "O1")
    if p["sparks"]:
        cx = S[0] + 6
        for k in range(16):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 3, 17))
            rr = 3 + 14 * hash01(k, 4, 17)
            FX.put([ip((cx + math.cos(a) * rr, FL + math.sin(a) * rr * 0.5))], ("O5", "O4", "O3", "Y2")[k % 4])
    return Ls, info


# ---------------------------------------------------------------- keyframes
def a_idle():
    fr = []
    for i in range(6):
        b = 0.5 - 0.5 * math.cos(i * math.pi / 3)
        fr.append((180, OP(C=(40.0, 31.0 + b * 0.6), Hd=(42.0, 19.5 + b * 0.8), S=(57.0, 47.0 + b * 0.5), lh=(47.0, 33.0 + b * 0.6),
                           core=1.0 + 0.3 * b, noz=0.3 + 0.2 * (i % 2), vent=0.3)))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        b = abs(s) * 1.0
        fr.append((130, OP(P=(38.0, 50.0 + b * 0.4), C=(40.4, 31.2 + b), Hd=(42.4, 19.8 + b), S=(57.4, 47.2 + b),
                           nk=(43.4 + 3.4 * c, 64.2), nf=(44.0 + 5.4 * c, FL - max(0, s) * 2.4),
                           fk=(34.6 - 3.4 * c, 64.4), ff=(33.0 - 5.4 * c, FL - max(0, -s) * 2.4), lh=(47.0, 33.0 + b),
                           smoke=1 if i % 4 == 0 else 0)))
    return fr


def a_flame():
    brace = dict(P=(37.0, 51.0), C=(39.0, 32.0), Hd=(41.4, 20.6), nk=(45.4, 64.0), nf=(48.0, FL), fk=(32.6, 64.6), ff=(28.0, FL),
                 S=(58.0, 48.0))
    frs = [
        (130, OP(**brace, lh=(46.0, 30.0), la=-12, noz=0.6)),
        (130, OP(**brace, lh=(47.0, 27.0), la=-16, noz=0.9, visor=1.4)),
        (140, OP(**brace, lh=(48.0, 25.4), la=-14, noz=1.2, visor=1.6, core=1.4)),
        (200, OP(**brace, lh=(48.0, 25.0), la=-12, noz=1.8, visor=2.0, core=1.8, vent=1.0)),
        (140, OP(**brace, lh=(48.4, 25.0), la=-10, noz=2.4, visor=2.0, core=2.0, vent=1.2)),
    ]
    for k in range(10):      # flame frames: sweep from -8 deg (high) to +22 deg (low), recoil shudder
        a = -8 + 30 * k / 9
        frs.append((110, OP(**dict(brace, P=(36.6 - 0.3 * (k % 2), 51.0)), lh=(48.0 - 0.4 * (k % 2), 25.4 + k * 0.5), la=a, noz=2.6,
                             visor=2.0, core=2.0, vent=1.2, smoke=1)))
    frs += [
        (140, OP(**brace, lh=(47.0, 29.0), la=10, noz=1.0, visor=1.4, core=1.4, vent=1.8, smoke=2)),
        (150, OP(lh=(47.0, 31.0), la=0, noz=0.6, vent=1.2, smoke=2)),
        (160, OP(noz=0.3, vent=0.6, smoke=1)),
    ]
    return frs


def a_bash():
    crouch = dict(P=(36.0, 52.0), C=(37.0, 33.6), Hd=(39.6, 23.0), nk=(42.4, 65.0), nf=(45.0, FL), fk=(31.4, 65.4), ff=(26.4, FL),
                  S=(54.0, 50.0), lh=(44.0, 36.0), la=6)
    lunge = dict(P=(46.0, 51.0), C=(51.0, 33.0), Hd=(54.4, 22.6), ha=10, nk=(52.4, 64.0), nf=(56.0, FL), fk=(38.0, 65.0), ff=(31.0, FL),
                 S=(66.0, 48.4), sa=6, lh=(55.0, 36.0), la=10)
    return [
        (120, OP(**crouch)),
        (200, OP(**crouch, visor=1.6, core=1.6)),
        (150, OP(**dict(crouch, P=(35.0, 52.4), C=(35.4, 34.0), S=(52.4, 50.4)), visor=2.0, core=2.0, vent=1.4)),
        (70, OP(**dict(lunge, P=(42.0, 51.0), C=(46.0, 33.0), Hd=(49.4, 22.4), S=(61.0, 48.4)), bash=1)),
        (80, OP(**lunge, bash=1)),
        (80, OP(**lunge, bash=1)),
        (90, OP(**lunge, sparks=1)),
        (110, OP(**dict(lunge, S=(65.0, 49.0), sa=2), sparks=1)),
        (150, OP(**dict(lunge, P=(44.0, 50.4), C=(47.0, 31.6), Hd=(49.6, 20.6), S=(62.4, 47.6), sa=0))),
        (160, OP(P=(41.0, 50.0), C=(43.0, 31.2), Hd=(45.0, 19.8), S=(59.0, 47.0))),
        (160, OP()),
    ]


def a_slam():
    up1 = dict(P=(37.0, 50.4), C=(38.4, 31.0), Hd=(40.0, 20.6), ha=-12, S=(48.0, 26.0), sa=-55, lh=(43.0, 26.0), la=-60)
    up2 = dict(P=(36.4, 50.0), C=(37.0, 30.0), Hd=(38.6, 19.6), ha=-18, S=(40.0, 14.0), sa=-95, lh=(40.0, 20.0), la=-80,
               nk=(42.4, 63.6), fk=(33.6, 64.0))
    down = dict(P=(40.0, 52.0), C=(46.0, 35.0), Hd=(50.0, 25.0), ha=16, S=(66.0, 55.0), sa=-8, lh=(52.0, 38.0), la=20,
                nk=(47.0, 65.0), nf=(50.0, FL), fk=(35.0, 65.0), ff=(30.0, FL))
    return [
        (120, OP(S=(55.0, 44.0), sa=-20)),
        (120, OP(**up1)),
        (140, OP(**dict(up1, S=(44.0, 18.0), sa=-80), visor=1.4)),
        (160, OP(**up2, visor=1.6, core=1.4)),
        (200, OP(**up2, visor=2.0, core=1.8, crack=0.0)),
        (220, OP(**dict(up2, S=(39.0, 13.0), sa=-100), visor=2.0, core=2.0)),
        (120, OP(**dict(up2, S=(38.0, 12.0), sa=-104), visor=2.0, core=2.0, vent=1.2)),
        (70, OP(**dict(down, S=(62.0, 30.0), sa=-40))),
        (80, OP(**down, sparks=1)),
        (120, OP(**down, sparks=1)),
        (200, OP(**down)),
        (160, OP(**dict(down, P=(39.0, 51.0), C=(43.0, 33.0), Hd=(46.0, 22.0), S=(62.0, 51.0), sa=-4))),
        (160, OP()),
    ]


def a_vent():
    hunch = dict(P=(38.0, 51.0), C=(41.4, 33.0), Hd=(45.0, 23.4), ha=14, S=(58.0, 49.0), lh=(48.0, 36.0), la=10)
    return [
        (120, OP(**hunch, vent=0.8)),
        (140, OP(**hunch, vent=1.2, core=1.4)),
        (220, OP(**hunch, vent=1.6, core=1.8, visor=1.6)),
        (140, OP(**hunch, vent=2.0, core=2.0, visor=2.0)),
        (90, OP(**hunch, vent=3.0, core=2.0, smoke=2)),
        (100, OP(**hunch, vent=3.0, core=2.0, smoke=2)),
        (110, OP(**hunch, vent=2.6, core=1.6, smoke=2)),
        (140, OP(**hunch, vent=1.2, smoke=2)),
        (150, OP(vent=0.8, smoke=1)),
        (150, OP(vent=0.4)),
    ]


def a_stagger():
    kneel = dict(P=(37.0, 58.0), C=(41.0, 40.0), Hd=(45.4, 30.0), ha=22, nk=(46.0, 68.0), nf=(47.0, FL), fk=(31.0, 72.0), ff=(24.0, FL),
                 S=(60.0, 60.0), sa=30, lh=(47.0, 50.0), la=40, visor=0.6, core=0.6, noz=0.0, vent=0.2)
    return [(90, OP(P=(35.0, 51.0), C=(34.0, 32.0), Hd=(34.6, 21.0), ha=-20, S=(54.0, 48.0), sa=16, visor=0.4)),
            (130, OP(**dict(kneel, C=(39.0, 38.0), Hd=(42.4, 27.0)))),
            (200, OP(**kneel)),
            (200, OP(**dict(kneel, visor=1.0)))]


def a_death():
    kneel = dict(P=(37.0, 58.0), C=(41.0, 40.0), Hd=(45.4, 30.0), ha=22, nk=(46.0, 68.0), nf=(47.0, FL), fk=(31.0, 72.0), ff=(24.0, FL),
                 S=(62.0, 66.0), sa=70, lh=(47.0, 50.0), la=40, visor=0.3, core=2.4, noz=0.0, vent=2.0)
    sn = ["Tank", "FarArm", "FarLeg", "Body", "Head", "NearLeg", "Shield"]
    iron = ("O4", "O3", "F3", "F2", "F1")
    return [
        (100, OP(P=(35.0, 51.0), C=(33.4, 32.0), Hd=(33.6, 21.0), ha=-26, S=(54.0, 48.0), sa=16, visor=0.2, core=2.4, sparks=1)),
        (130, OP(**dict(kneel, C=(39.0, 36.0), Hd=(42.0, 25.0), S=(58.0, 55.0), sa=20), smoke=1)),
        (160, OP(**dict(kneel, S=(60.0, 60.0), sa=40))),
        (160, OP(**kneel, smoke=2)),
        (120, OP(**kneel, smoke=2, sparks=1)),
        (160, OP(**dict(kneel, core=2.8, vent=3.0), smoke=2)),
        (140, OP(**dict(kneel, core=1.2), smoke=2)),
        (140, OP(**kneel, smoke=2, post=collapse(sn, 0.8, 0.08, pal=iron, spread=0.2))),
        (140, OP(**kneel, smoke=1, post=collapse(sn, 0.6, 0.16, pal=iron, spread=0.25))),
        (160, OP(**kneel, smoke=1, post=collapse(sn, 0.42, 0.22, pal=iron, spread=0.3))),
        (180, OP(**kneel, post=collapse(sn, 0.3, 0.26, pal=iron, spread=0.35))),
        (700, OP(**kneel, post=collapse(sn, 0.22, 0.3, pal=iron, spread=0.4))),
    ]


def main():
    K.setup(96, 80)
    anims, infos = E3.render_anims("overseer", LAYERS, draw,
                                   [("idle", a_idle), ("walk", a_walk), ("flame", a_flame), ("bash", a_bash), ("slam", a_slam),
                                    ("vent", a_vent), ("stagger", a_stagger), ("death", a_death)], sway_key="C", loops=("idle", "walk"))
    hb = E3.hurtbox(anims, ["Body", "Head", "Tank"], inset=(2, 2, 2))

    def rect_of(pts, floor=False):
        r = K.bbox(pts)
        if floor:
            r[3] = K.H - r[1]
        return r
    bash_hit = rect_of(infos["bash"][4]["shield"] | infos["bash"][5]["shield"], True)
    slam_hit = rect_of(infos["slam"][8]["shield"], True)
    slam_hit = [slam_hit[0] - 4, slam_hit[1], slam_hit[2] + 12, slam_hit[3]]
    vent_hit = [0, 4, 30, 52]
    meta = {"native": 1, "frame": [96, 80], "anchor": [38, 80], "hurtbox": hb,
            "attacks": {"bash": {"active": [4, 7], "hit": bash_hit}, "slam": {"active": [7, 8], "hit": slam_hit},
                        "vent": {"active": [4, 6], "hit": vent_hit}},
            "flame_frames": [5, 14],
            "nozzle": [spawn_pt(i["muzzle"]) for i in infos["flame"]],
            "flame_ang": [round(i["lang"], 1) for i in infos["flame"]],
            "shield": rect_of(infos["idle"][0]["shield"]),
            "telegraph": {"flame": {"frame": 3, "at": spawn_pt(infos["flame"][3]["muzzle"])},
                          "bash": {"frame": 1, "at": spawn_pt(infos["bash"][1]["visor"])},
                          "slam": {"frame": 4, "at": spawn_pt(infos["slam"][4]["visor"])},
                          "vent": {"frame": 2, "at": spawn_pt(infos["vent"][2]["vents"][0])}},
            "notes": "faces right. Shield covers the front in idle/walk/flame/bash/vent; during slam 1-6 it is hauled overhead "
                     "(front open). flame: engine emits the flame from nozzle[i] at flame_ang[i] (deg) on flame_frames."}
    DE.export("overseer", LAYERS, anims, meta)
    print(json.dumps({k: v for k, v in meta.items() if k not in ("notes", "nozzle", "flame_ang")}))
    if BUILD:
        print(E3.verify("overseer"))


if __name__ == "__main__":
    main()
