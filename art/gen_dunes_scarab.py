#!/usr/bin/env python3
"""The Scarab Knight (agent DU mini-boss) -- a knight of the sun-kings grown a beetle's carapace in the long dark.

    python3 art/gen_dunes_scarab.py [--preview] [--only thrust,sweep]

Frame 112x80, faces RIGHT, feet on the bottom row, anchor x = 50. ~64px tall to the horn tip.
Sleek, upright insect-knight: a small helmed head with a rhinoceros-beetle horn sweeping up and forward, an amber visor
slit; black chitin plates with gold trim; a golden carapace (the folded elytra) worn like a shell-cape from the shoulders
to the knees; slender digitigrade legs with spurred feet; a long leaf-bladed spear.
Sheets: scarab   idle(6) walk(8) thrust(10) sweep(12)
        scarab_b rear(6) charge(4) burrow(8) emerge(10) stagger(4) death(10)
Meta assets/scarab_meta.json (shared by both sheets; `sheets` maps tag -> sheet).
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, hash01, mask_disc, poly_mask, n_plate,  # noqa: E402
                       n_dome, n_capsule, swept, dirv, bbox, basis, leg, arm)
import gen_enemies3 as E3  # noqa: E402
from gen_enemies3 import n_tube, curve, mk, spawn_pt, collapse  # noqa: E402
import dunes_kit as DK  # noqa: E402
from dunes_kit import tube, glint  # noqa: E402

W, H = 112, 80
K.setup(W, H)
FL = 79
AX = 50
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None

LAYERS = ["FXBack", "FarArm", "FarLeg", "Elytra", "Body", "NearLeg", "Head", "Spear", "NearArm", "FX"]
NEU = dict(P=(47.0, 54.0), C=(49.0, 37.0), Hd=(53.0, 27.0), hup=(0.3, -1.0),
           fb=(41.0, FL), ff=(55.0, FL), kb=None, kf=None,
           hf=(62.0, 50.0), hb=(44.0, 48.0), sang=-8, su0=-26, su1=24,
           ely=0.0, eye=1, smear=None, thrust=None, rot=0.0, piv=(48, 60), dust=0, sink=0.0, spray=0, glint=None, cracks=0.0, horn=0.0,
           wind=0.0)
PS = mk(NEU)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def spear(L, FX, grip, ang, u0, u1, info):
    ca, sa = dirv(ang)
    a = (grip[0] + ca * u0, grip[1] + sa * u0)
    b = (grip[0] + ca * u1, grip[1] + sa * u1)
    shaft = L.paint(n_capsule(a, b, 0.85, 0.85, 1.0), "b", 0, ao=0)
    nx, ny = -sa, ca
    blade = []
    for k in range(9):
        t = k / 8
        w = math.sin(min(1.0, t * 1.25) * math.pi) * 2.4 * (1 - t * 0.35)
        blade.append((b[0] + ca * t * 12 + nx * w, b[1] + sa * t * 12 + ny * w))
    for k in range(8, -1, -1):
        t = k / 8
        w = math.sin(min(1.0, t * 1.25) * math.pi) * 2.4 * (1 - t * 0.35)
        blade.append((b[0] + ca * t * 12 - nx * w, b[1] + sa * t * 12 - ny * w))
    bm = poly_mask(blade)
    L.paint(n_plate(bm, 1.2, (-0.25, -0.3), 1.3), "e", 0, ao=0)
    L.decal(polyline([ip(b), ip((b[0] + ca * 11, b[1] + sa * 11))]), ("e", 2))            # the midrib
    # a gold collar where blade meets shaft, a tassel of red linen
    L.paint(n_dome((b[0] - ca * 0.6, b[1] - sa * 0.6), 1.5, 1.5), "e", 0, ao=0)
    info["hit"] |= bm | {q for q in shaft if (q[0] - grip[0]) * ca + (q[1] - grip[1]) * sa > u1 * 0.5}
    info["tip"] = (b[0] + ca * 12, b[1] + sa * 12)
    info["blade"] = (b[0] + ca * 6, b[1] + sa * 6)
    return bm


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n not in ("FX", "FXBack")}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    Pp, Cc, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(Cc, Pp)
    ln = math.hypot(*upv)
    F = basis(Pp, upv)
    shN, shF = F(3.4, -ln + 2.0), F(-3.6, -ln + 2.6)
    hipN, hipF = F(2.2, 0.6), F(-2.2, 0.6)
    # legs: slender, black chitin, gold knee-caps, spurred feet
    kf = leg(R, Ls["NearLeg"], hipN, p["ff"], 12.4, 12.8, 2.6, 1.9, "c", bias=0, knee=p["kf"], flen=4.0, heel=2.0, boot_h=2.0, pref=(1, -0.15))
    kb = leg(R, Ls["FarLeg"], hipF, p["fb"], 12.4, 12.8, 2.6, 1.9, "c", bias=-2, knee=p["kb"], flen=4.0, heel=2.0, boot_h=2.0, pref=(1, -0.15))
    for nm, kn, ft, b in (("NearLeg", kf, p["ff"], 0), ("FarLeg", kb, p["fb"], -2)):
        Ls[nm].paint(n_dome(T(kn), 2.2, 2.0, tilt=(-0.2, -0.3)), "e", b, ao=0)
        sp_ = T((ft[0] - 2.6, ft[1] - 2.8))
        for q in polyline([ip(sp_), ip((sp_[0] - 2.4, sp_[1] + 1.2))]):
            Ls[nm].fixed({q: "e3" if b == 0 else "e2"})
    # the carapace: golden elytra from the shoulders down the back to the knees, lifting when it rears / charges
    E = Ls["Elytra"]
    lift = p["ely"]
    top = F(-2.0, -ln + 0.6)
    ep = [F(1.0, -ln - 0.8), F(-3.4, -ln - 1.8 - lift * 2), F(-8.4 - lift * 4.0, -ln + 4.0 - lift * 3), F(-10.0 - lift * 5.0, -ln * 0.4 - lift * 2),
          F(-9.4 - lift * 4.4, 3.0 - lift), F(-6.0 - lift * 2, 10.0 - lift * 1.5), F(-2.4, 7.0), F(0.4, -2.0)]
    em = R.plate(E, [add(q, (-sw * 0.25, 0)) if i >= 3 else q for i, q in enumerate(ep)], "e", bevel=3.6, tilt=(-0.2, -0.15), strength=1.3, bias=0)
    for gk in (0.35, 0.62):                                                                   # longitudinal grooves
        gp = [ip(T(F(-3.0 - lift - 5.0 * gk, -ln + 1.4))), ip(T(F(-3.6 - lift * 3.6 - 6.0 * gk, -ln * 0.4))), ip(T(F(-2.6 - lift * 2 - 3.6 * gk, 6.0 - lift)))]
        E.decal([q for q in polyline(gp) if q in em], ("e", 2))
    seam = [ip(T(F(-3.0 - lift, -ln + 1.0))), ip(T(F(-7.4 - lift * 3.6, -ln * 0.3))), ip(T(F(-5.6 - lift * 2, 7.0 - lift)))]
    E.decal([q for q in polyline(seam) if q in em], ("e", 1))
    E.decal([q for q in em if (q[0], q[1] - 1) not in em], ("e", 6))
    # fine punched dots along the rim (gold-smith work)
    rim = [q for q in em if any((q[0] + a, q[1] + b) not in em for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    E.decal([q for i, q in enumerate(sorted(rim)) if i % 5 == 0], ("e", 2))
    info["ely"] = em
    # torso: segmented black chitin plates with gold trim lines, a narrow waist
    Bd = Ls["Body"]
    torso = [F(-3.0, 0.0), F(-4.0, -ln + 5.0), F(-4.6, -ln + 0.6), F(-2.0, -ln - 1.6), F(3.4, -ln - 1.6), F(5.4, -ln + 1.4),
             F(4.8, -ln + 6.0), F(2.6, -ln * 0.45), F(3.0, 0.0)]
    tm = R.plate(Bd, torso, "c", bevel=2.6, tilt=(-0.25, -0.15), strength=1.4)
    for k in range(4):
        y = -ln + 5.5 + k * (ln - 6) / 3.6
        Bd.decal([q for q in polyline([ip(T(F(-3.6, y))), ip(T(F(4.4, y - 0.8)))]) if q in tm], ("e", 3) if k == 0 else ("c", 1))
    # a pair of small folded forelimbs across the chest (the insect it became)
    for k in range(2):
        a0 = F(2.4, -ln + 4.0 + k * 2.4)
        Bd.paint(n_tube([T(a0), T(F(5.0, -ln + 6.0 + k * 2.4)), T(F(3.6, -ln + 8.8 + k * 2.0))], [0.9, 0.8, 0.7]), "c", 1, ao=0)
    info["torso"] = tm
    # head: a small helm, the horn sweeping up and forward, an amber visor slit
    G = basis(Hd, p["hup"])
    Hl = Ls["Head"]
    Hl.paint(n_tube([T(F(0.8, -ln - 1.0)), T(G(-0.6, 3.0))], [2.2, 1.9]), "c", -1)
    helm = [G(-3.6, 2.8), G(-4.0, -1.0), G(-2.2, -3.6), G(1.6, -3.8), G(4.2, -1.6), G(4.8, 1.6), G(3.2, 3.6), G(-0.6, 4.0)]
    hm = R.plate(Hl, helm, "c", bevel=1.8, tilt=(-0.3, -0.3), strength=1.4)
    Hl.decal([q for q in polyline([ip(T(G(-3.4, -0.6))), ip(T(G(1.8, -3.4)))]) if q in hm], ("e", 4))      # gold crest line
    hr = p["horn"]
    horn = curve([T(G(1.6, -2.6)), T(G(4.0, -7.0 - hr)), T(G(4.4 + hr * 0.4, -12.6 - hr * 1.2)), T(G(2.6, -16.4 - hr))], 5)
    Hl.paint(n_tube(horn, [1.9 - 1.5 * i / (len(horn) - 1) for i in range(len(horn))]), "e", 0, ao=0)
    info["horn"] = horn[-1]
    visor = polyline([ip(T(G(1.8, 0.2))), ip(T(G(4.4, 0.6)))])
    Hl.decal(visor, ("c", 0))
    e = ip(T(G(3.4, 0.4)))
    if p["eye"]:
        FX.put([e, (e[0] - 1, e[1])], "a4" if p["eye"] == 2 else "a3")
    info["head"] = hm
    info["eye"] = T(G(3.4, 0.4))
    # far arm (steadies the spear)
    arm(R, Ls["FarArm"], shF, p["hb"], 9.6, 9.4, 2.0, 1.6, "c", bias=-2, fist="c", fist_r=1.6, pref=(-1, 0.6))
    spear(Ls["Spear"], FX, T(p["hf"]), R.A(p["sang"]), p["su0"], p["su1"], info)
    el = arm(R, Ls["NearArm"], shN, p["hf"], 9.6, 9.4, 2.3, 1.8, "c", bias=0, fist="c", fist_r=1.8, pref=(-1, 0.7))
    Ls["NearArm"].paint(n_dome(T(shN), 3.0, 2.6, tilt=(-0.3, -0.4)), "e", 0, ao=0)                     # gold pauldron
    Ls["NearArm"].paint(n_dome(T(el), 1.7, 1.6, tilt=(-0.3, -0.3)), "e", 0, ao=0)
    info["hand"] = T(p["hf"])
    # FX: smears, thrust streaks, glints
    if p["smear"]:
        for (g0, a0, g1, a1) in p["smear"]:
            L_ = p["su1"] + 12
            info["hit"] |= swept(FX, T(g0), R.A(a0), T(g1), R.A(a1), L_ - 10, L_ + 1, hw=1.3, pal="khopesh", taper=0.6)
    if p["thrust"]:
        info["hit"] |= K.thrust_lines(FX, T(p["hf"]), R.A(p["sang"]), -8, p["su1"] + 12, (-4, -2, 2, 4), pal="khopesh", flash=p["su1"] + 10)
    if p["glint"]:
        glint(FX, p["glint"], big=True)
    if p["cracks"] > 0:
        for k in range(int(10 * p["cracks"])):
            q0 = list(em)[int(hash01(k, 3, 9) * len(em))] if em else None
            if q0:
                for q in polyline([q0, (q0[0] + int((hash01(k, 4, 9) - 0.5) * 8), q0[1] + int(hash01(k, 5, 9) * 6))]):
                    if q in E.px:
                        E.decal([q], ("e", 0))
                        FX.put([q], "a2") if hash01(q[0], q[1], 2) < 0.2 else None
    # burrowing: sink into the floor, sand spraying up around
    if p["sink"] > 0:
        dy = int(round(p["sink"] * 64))
        for L in Ls.values():
            if isinstance(L, Layer):
                L.px = {(q[0], q[1] + dy): e_ for q, e_ in L.px.items() if q[1] + dy < FL - 1}
        FX.px = {(q[0], q[1] + dy): c for q, c in FX.px.items() if q[1] + dy < FL - 1}
        info["hit"] = {(q[0], q[1] + dy) for q in info["hit"] if q[1] + dy < FL - 1}
    if p["spray"]:
        for k in range(26):
            a = -math.pi * (0.08 + 0.84 * hash01(k, fi, 7))
            rr = 3 + 22 * hash01(k, fi + 1, 7) * p["spray"]
            FX.put([ip((Pp[0] + 4 + math.cos(a) * rr * 1.2, FL - 1 + math.sin(a) * rr))], ("z7", "z6", "z5", "z4")[k % 4])
        for x in range(int(Pp[0] - 16), int(Pp[0] + 22)):
            h = int(2 + 3 * (1 - abs(x - Pp[0] - 3) / 19))
            for y in range(FL - h, FL + 1):
                FX.put([(x, y)], "z6" if y == FL - h else "z5")
    if p["dust"]:
        for k in range(14):
            FX.put([(int(Pp[0] + (hash01(k, fi, 3) - 0.5) * 36), FL - int(hash01(k, fi, 4) * 4))], ("z6", "z5", "z4")[k % 3])
    return Ls, info


# =========================================================================== animations
STANCE = dict(P=(46.0, 55.0), C=(47.6, 38.4), Hd=(51.4, 28.4), hup=(0.26, -1.0), fb=(38.0, FL), ff=(57.0, FL))


def a_idle():
    fr = []
    for i in range(6):
        b = (0.0, 0.4, 0.8, 1.0, 0.8, 0.4)[i]
        fr.append((170, PS(C=(49.0, 37.0 + b * 0.6), Hd=(53.0, 27.0 + b * 0.8), hf=(62.0, 50.0 + b * 0.3), hb=(44.0, 48.0 + b * 0.5),
                           ely=0.05 * b)))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        bob = 1.2 * abs(s)
        fr.append((105, PS(P=(47.0, 54.0 + bob), C=(49.6, 37.2 + bob), Hd=(53.6, 27.4 + bob), hup=(0.34, -1.0),
                           ff=(49.0 + 8.0 * c, FL - max(0, s) * 3.0), fb=(46.0 - 8.0 * c, FL - max(0, -s) * 3.0),
                           hf=(62.4 + c, 50.0 + bob), sang=-8 + 2 * s, hb=(44.0 - 1.6 * c, 48.0 + bob))))
    return fr


def a_thrust():
    back = dict(P=(44.0, 56.0), C=(43.6, 39.4), Hd=(46.6, 29.6), hup=(0.1, -1.0), fb=(33.0, FL), ff=(55.0, FL))
    lunge = dict(P=(52.0, 56.0), C=(58.0, 40.4), Hd=(63.4, 31.6), hup=(0.7, -1.0), fb=(38.0, FL), ff=(68.0, FL))
    return [
        (110, PS(**back, hf=(52.0, 49.0), hb=(38.0, 48.0), sang=-4)),
        (150, PS(**back, hf=(46.0, 48.0), hb=(33.0, 47.0), sang=-3, eye=2)),
        (160, PS(**back, hf=(44.0, 48.0), hb=(31.0, 47.0), sang=2, eye=2, glint=(80.0, 50.0))),
        (60, PS(**lunge, hf=(74.0, 54.0), hb=(62.0, 53.0), sang=7, su0=-30, su1=18, eye=2, thrust=True, dust=1)),
        (70, PS(**lunge, hf=(76.0, 55.0), hb=(64.0, 54.0), sang=8, su0=-30, su1=18, eye=2, thrust=True, dust=1)),
        (90, PS(**lunge, hf=(74.0, 55.0), hb=(62.0, 54.0), sang=8, su0=-30, su1=18)),
        (110, PS(P=(50.0, 55.0), C=(54.0, 38.6), Hd=(58.4, 29.0), hup=(0.5, -1.0), fb=(38.0, FL), ff=(64.0, FL), hf=(68.0, 48.0), hb=(56.0, 48.0),
                 sang=-10)),
        (120, PS(P=(48.0, 54.6), C=(51.0, 37.6), Hd=(55.0, 27.8), hup=(0.4, -1.0), ff=(59.0, FL), hf=(65.0, 49.0), hb=(49.0, 48.0))),
        (140, PS(hf=(63.0, 50.0))),
        (140, PS()),
    ]


def a_sweep():
    wind = dict(P=(45.0, 56.0), C=(44.0, 39.4), Hd=(46.6, 29.2), hup=(-0.05, -1.0), fb=(35.0, FL), ff=(56.0, FL))
    cut = dict(P=(50.0, 56.0), C=(54.4, 39.6), Hd=(58.8, 30.4), hup=(0.55, -1.0), fb=(38.0, FL), ff=(64.0, FL))
    return [
        (110, PS(**wind, hf=(50.0, 42.0), hb=(40.0, 44.0), sang=-150, su0=-16, su1=24)),
        (170, PS(**wind, hf=(44.0, 38.0), hb=(38.0, 42.0), sang=-165, su0=-16, su1=24, eye=2)),
        (160, PS(**wind, hf=(42.0, 37.0), hb=(37.0, 42.0), sang=-170, su0=-16, su1=24, eye=2, glint=(20.0, 30.0))),
        (60, PS(**cut, hf=(66.0, 44.0), hb=(56.0, 46.0), sang=-20, su0=-16, su1=24, eye=2, smear=[((42.0, 37.0), -170, (66.0, 44.0), -20)])),
        (70, PS(**cut, hf=(66.0, 50.0), hb=(56.0, 50.0), sang=20, su0=-16, su1=24, eye=2, smear=[((66.0, 44.0), -20, (66.0, 50.0), 20)])),
        (120, PS(**cut, hf=(63.0, 54.0), hb=(54.0, 52.0), sang=40, su0=-16, su1=24)),
        (160, PS(**cut, hf=(62.0, 56.0), hb=(53.0, 53.0), sang=30, su0=-16, su1=24, eye=2)),
        (60, PS(**wind, hf=(46.0, 52.0), hb=(38.0, 50.0), sang=175, su0=-16, su1=24, eye=2, smear=[((62.0, 56.0), 30, (46.0, 52.0), 175)])),
        (70, PS(**wind, hf=(44.0, 44.0), hb=(38.0, 46.0), sang=205, su0=-16, su1=24, eye=2, smear=[((46.0, 52.0), 175, (44.0, 44.0), 205)])),
        (130, PS(**wind, hf=(48.0, 44.0), hb=(40.0, 46.0), sang=-160, su0=-16, su1=24)),
        (140, PS(hf=(58.0, 48.0), sang=-40)),
        (150, PS()),
    ]


def a_rear():
    up = dict(P=(44.0, 54.0), C=(42.4, 37.0), Hd=(44.0, 26.4), hup=(-0.3, -1.0), fb=(34.0, FL), ff=(54.0, FL))
    return [
        (110, PS(**up, hf=(54.0, 44.0), hb=(40.0, 44.0), sang=-30, ely=0.3)),
        (140, PS(**up, hf=(48.0, 40.0), hb=(36.0, 40.0), sang=-150, su0=-20, su1=20, ely=0.6, eye=2, horn=1.0)),
        (180, PS(**up, hf=(46.0, 38.0), hb=(35.0, 40.0), sang=-160, su0=-20, su1=20, ely=0.8, eye=2, horn=1.5, glint=(58.0, 10.0))),
        (180, PS(**up, hf=(46.0, 38.0), hb=(35.0, 40.0), sang=-160, su0=-20, su1=20, ely=0.9, eye=2, horn=1.5)),
        (90, PS(P=(46.0, 57.0), C=(52.0, 44.0), Hd=(58.4, 38.0), hup=(1.0, -0.6), fb=(34.0, FL), ff=(58.0, FL), hf=(44.0, 48.0), hb=(40.0, 50.0),
                sang=-175, su0=-20, su1=20, ely=0.7, eye=2, dust=1)),
        (90, PS(P=(47.0, 58.0), C=(54.0, 46.0), Hd=(61.0, 41.0), hup=(1.0, -0.4), fb=(34.0, FL), ff=(60.0, FL), hf=(44.0, 50.0), hb=(40.0, 52.0),
                sang=-178, su0=-20, su1=20, ely=0.6, eye=2, dust=1)),
    ]


def a_charge():
    fr = []
    for i in range(4):
        ph = 2 * math.pi * i / 4
        c, s = math.cos(ph), math.sin(ph)
        fr.append((70, PS(P=(47.0, 58.0 - abs(s)), C=(55.0, 46.0 - abs(s)), Hd=(62.0, 41.6 - abs(s)), hup=(1.0, -0.4),
                          ff=(52.0 + 10 * c, FL - max(0, s) * 4), fb=(46.0 - 10 * c, FL - max(0, -s) * 4),
                          hf=(44.0, 50.0), hb=(40.0, 52.0), sang=-178, su0=-20, su1=20, ely=0.55 + 0.1 * s, eye=2, dust=1)))
    return fr


def a_burrow():
    crouch = dict(P=(47.0, 60.0), C=(53.0, 48.0), Hd=(59.0, 42.0), hup=(1.0, -0.2), fb=(38.0, FL), ff=(58.0, FL), hf=(58.0, 58.0), hb=(52.0, 56.0),
                  sang=60, ely=0.2)
    fr = [(120, PS(**crouch)), (110, PS(**crouch, spray=0.3))]
    for k, s_ in enumerate((0.2, 0.4, 0.6, 0.8, 0.95, 1.1)):
        fr.append((80, PS(**crouch, sink=min(1.0, s_), spray=0.6 + 0.4 * (k < 4))))
    return fr


def a_emerge():
    up = dict(P=(48.0, 53.0), C=(50.0, 36.0), Hd=(53.0, 26.0), hup=(0.2, -1.0), fb=(42.0, FL), ff=(56.0, FL), hf=(56.0, 30.0), hb=(50.0, 34.0),
              sang=-82, su0=-18, su1=22, ely=0.5, eye=2)
    return [
        (70, PS(**up, sink=0.7, spray=1.0)),
        (60, PS(**up, sink=0.4, spray=1.0, thrust=True)),
        (60, PS(**up, sink=0.12, spray=0.9, thrust=True)),
        (80, PS(**up, sink=0.0, spray=0.6, thrust=True)),
        (100, PS(**dict(up, hf=(57.0, 32.0)), spray=0.3)),
        (120, PS(P=(47.0, 55.0), C=(49.0, 38.0), Hd=(52.4, 28.0), hup=(0.26, -1.0), hf=(60.0, 40.0), hb=(48.0, 42.0), sang=-50, ely=0.3)),
        (120, PS(hf=(62.0, 46.0), hb=(45.0, 46.0), sang=-20, ely=0.15)),
        (120, PS(ely=0.05)),
        (120, PS()),
        (120, PS()),
    ]


def a_stagger():
    rock = dict(P=(44.0, 56.0), C=(41.0, 40.0), Hd=(40.4, 30.6), hup=(-0.5, -1.0), fb=(36.0, FL), ff=(54.0, FL))
    slump = dict(P=(45.0, 59.0), C=(49.0, 44.0), Hd=(54.0, 37.0), hup=(0.9, -0.8), fb=(36.0, FL), ff=(56.0, FL))
    return [
        (90, PS(**rock, hf=(52.0, 40.0), hb=(36.0, 42.0), sang=-120, eye=0, ely=0.4)),
        (130, PS(**slump, hf=(58.0, 58.0), hb=(46.0, 58.0), sang=70, eye=0, ely=0.2)),
        (300, PS(**slump, hf=(58.0, 60.0), hb=(46.0, 59.0), sang=74, eye=0, ely=0.2)),
        (300, PS(**dict(slump, C=(49.4, 44.6), Hd=(54.6, 37.8)), hf=(58.0, 60.0), hb=(46.0, 59.4), sang=75, eye=0, ely=0.2)),
    ]


def a_death():
    kneel = dict(P=(45.0, 63.0), C=(50.0, 48.0), Hd=(56.0, 41.0), hup=(1.0, -0.7), kf=(56.0, 68.0), ff=(54.0, FL), kb=(40.0, 76.0),
                 fb=(30.0, FL), hf=(62.0, 70.0), hb=(52.0, 66.0), sang=12, su0=-30, su1=18, eye=0, ely=0.3)
    names = [n for n in LAYERS if n not in ("FX", "FXBack")]
    pal = ("a3", "e5", "e4", "z5", "z4")
    fr = [
        (100, PS(P=(44.0, 56.0), C=(40.0, 40.0), Hd=(39.0, 31.0), hup=(-0.6, -1.0), fb=(36.0, FL), ff=(54.0, FL), hf=(50.0, 40.0), hb=(36.0, 42.0),
                 sang=-130, eye=2, ely=0.5)),
        (180, PS(**kneel, cracks=0.3)),
        (300, PS(**kneel, cracks=0.6)),
        (260, PS(**kneel, cracks=1.0)),
    ]
    for k, (sq, burn) in enumerate(((0.75, 0.15), (0.5, 0.3), (0.3, 0.4), (0.16, 0.48), (0.08, 0.55), (0.04, 0.6))):
        fr.append((150 if k < 5 else 700, PS(**kneel, cracks=1.0, dust=1, post=collapse(names, sq, burn, seed=9, pal=pal, spread=0.3 + k * 0.15))))
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("thrust", a_thrust), ("sweep", a_sweep), ("rear", a_rear), ("charge", a_charge),
           ("burrow", a_burrow), ("emerge", a_emerge), ("stagger", a_stagger), ("death", a_death)]
SHEET_A = ("idle", "walk", "thrust", "sweep")
LOOPS = ("idle", "walk", "charge")


def render(only=None):
    out, infos, tags = [], {}, []
    n = 0
    for tag, fn in TAGDEFS:
        fr = fn()
        if only and tag not in only:
            continue
        drv = [p["C"][0] for _, p in fr]
        sway = K.spring(drv, loop=tag in LOOPS, extra=[p.get("wind", 0.0) for _, p in fr])
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            Ls, info = draw(p, a + k, sway[k])
            imgs = {nm: (K.render_layer(v) if isinstance(v, Layer) else v.image()) for nm, v in Ls.items()}
            if p.get("post"):
                imgs = p["post"](imgs)
            out.append((ms, imgs))
            infos[tag].append(info)
            n += 1
        tags.append((tag, a, n - 1))
        print("rendered", tag, len(fr))
    return out, infos, tags


def hit(infos, tag, ks, x_min, floor=True):
    pts = set()
    for k in ks:
        pts |= infos[tag][k]["hit"]
    r = bbox(pts, 1)
    if r[0] < x_min:
        r[2] -= x_min - r[0]
        r[0] = x_min
    if floor:
        r[3] = H - r[1]
    return r


def main():
    out, infos, tags = render(ONLY)
    flats = [K.flatten(imgs, LAYERS) for _, imgs in out]
    K.preview_rows("scarab" + ("_wip" if ONLY else ""), tags, flats)
    if ONLY:
        return
    idle = infos["idle"][0]
    tb = bbox(idle["torso"] | idle["head"] | idle["ely"])
    meta = {
        "native": 1, "frame": [W, H], "anchor": [AX, H],
        "hurtbox": [tb[0] + 3, tb[1] + 2, tb[2] - 6, H - tb[1] - 2],
        "sheets": {t: ("scarab" if t in SHEET_A else "scarab_b") for t, _ in TAGDEFS},
        "attacks": {
            "thrust": {"active": [3, 4], "hit": hit(infos, "thrust", [3, 4], AX + 4)},
            "sweep": {"windows": [{"active": [3, 4], "hit": hit(infos, "sweep", [3, 4], AX)}, {"active": [7, 8], "hit": hit(infos, "sweep", [7, 8], 0)}]},
            "emerge": {"active": [1, 3], "hit": hit(infos, "emerge", [1, 3], AX - 16)},
        },
        "telegraph": {"thrust": {"frame": 2, "at": [80, 50]}, "sweep": {"frame": 2, "at": [20, 30]}, "rear": {"frame": 2, "at": [58, 10]}},
        "notes": "faces right, anchor = feet. thrust = spear lunge (3-4); sweep = a forward overhead sweep (3-4) then a backhand "
                 "sweep behind him (7-8). rear = wind-up of the horn charge (charge loops while the engine drives him). burrow sinks "
                 "into the sand (the engine moves the mound), emerge erupts upward with the spear (1-3). scarab_b shares this meta.",
    }
    E3.hitbox_preview3("scarab", tags, flats, meta)
    with open(os.path.join(asebuild.ASSETS, "scarab_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        print("attack", t, d.get("windows") or (d["active"], d["hit"]))
    print("hurtbox", meta["hurtbox"])
    if BUILD:
        for sheet_name, keep in (("scarab", SHEET_A), ("scarab_b", tuple(t for t, _ in TAGDEFS if t not in SHEET_A))):
            frames, st, i = [], [], 0
            for (t, a, b) in tags:
                if t not in keep:
                    continue
                s0 = len(frames)
                for k in range(a, b + 1):
                    frames.append({"ms": out[k][0], "cels": {n_: out[k][1][n_] for n_ in LAYERS if n_ in out[k][1]}})
                st.append((t, s0, len(frames) - 1))
            asebuild.build(sheet_name, W, H, LAYERS, frames, st)


if __name__ == "__main__":
    main()
