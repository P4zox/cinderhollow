#!/usr/bin/env python3
"""The Veiled Pharaoh (agent DU main boss) -- the last sun-king, who would not be buried.

    python3 art/gen_dunes_pharaoh.py [--preview] [--only idle,combo]

Frame 160x128, faces RIGHT, feet on the bottom row, anchor x = 72. ~100px to the top of the sun-disc crown.
Tall and emaciated: limbs wrapped in ancient gold-tinted linen with dark tar showing through, a striped gold-and-lapis nemes
headcloth, a gold death mask (in profile) with one amber eye slit burning in it, a sun-disc crown between slender horns, a broad
usekh collar and a hieroglyph apron, a long pleated kilt; a cloak of streaming sand pours off his shoulders and breaks into
grains behind him. A gold khopesh in the near hand, a tall sun sceptre in the far hand.
Skeleton lengths (thigh 20.5, shin 21.5, upper arm 15, forearm 15, spine and neck) are fixed; every pose only moves joints.
Sheets (all share assets/pharaoh_meta.json; `sheets` maps tag -> sheet):
  pharaoh_a idle(8) walk(8) rise(10)     pharaoh_b combo(16) stagger(4)     pharaoh_c beam(14) coffin(12)
  pharaoh_d summon(12) disc(12)          pharaoh_e vanish(8) emerge(10)     pharaoh_f death(16)
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
from dunes_kit import tube, bands, glint, sun_disc, AMBER  # noqa: E402

W, H = 160, 128
K.setup(W, H)
FL = 127
AX = 72
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None

LAYERS = ["FXBack", "Cloak", "FarArm", "Sceptre", "FarLeg", "Skirt", "NearLeg", "Body", "Collar", "Head", "Crown", "Khopesh",
          "NearArm", "FX"]
NOOUT = {"FX", "FXBack"}
THIGH, SHIN, UARM, FARM = 20.5, 21.5, 15.0, 15.0
NEU = dict(P=(70.0, 84.0), C=(72.0, 55.0), Hd=(75.4, 42.0), hup=(0.18, -1.0),
           fb=(62.0, FL), ff=(80.0, FL), kb=None, kf=None,
           hf=(84.0, 84.0), kang=62, hb=(60.0, 80.0), sang=-92, su0=-44, su1=40,
           eb=None, ef=None,                           # optional elbow overrides
           glow=0, eye=1, cloak=1.0, smear=None, sink=0.0, spray=0, dust=0, glint=None, rot=0.0, piv=(70, 100), wind=0.0,
           crossed=False, mask_off=0.0, crack=0.0)
PS = mk(NEU)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


# --------------------------------------------------------------------------- weapons
def khopesh(L, grip, ang, info):
    """Gold sickle-sword: a straight bronze-bound neck, then the deep forward hook; the outer curve is the edge."""
    ca, sa = dirv(ang)
    nx, ny = -sa, ca
    outer, inner = [], []
    for k in range(17):
        t = k / 16
        u = 3.0 + t * 21.0
        curl = max(0.0, t - 0.38) ** 1.6 * 11.0
        w = 1.2 if t < 0.38 else 1.2 + (t - 0.38) * 5.0 * (1 - max(0, t - 0.85) * 4)
        c = (grip[0] + ca * u - nx * curl, grip[1] + sa * u - ny * curl)
        outer.append((c[0] + nx * w, c[1] + ny * w))
        inner.append((c[0] - nx * 0.8, c[1] - ny * 0.8))
    m = poly_mask(outer + inner[::-1])
    L.paint(n_plate(m, 1.3, (-0.25, -0.3), 1.3), "g", 0, ao=0)
    L.decal([q for q in {ip(q) for q in outer} if q in m], ("g", 5))
    L.decal([q for q in m if hash01(q[0], q[1], 13) < 0.06], ("g", 2))                          # hieroglyphs engraved
    hilt = L.paint(n_capsule(grip, (grip[0] - ca * 4.0, grip[1] - sa * 4.0), 1.1, 1.0, 1.0), "u", 0, ao=0)
    L.paint(n_dome((grip[0] + ca * 2.4, grip[1] + sa * 2.4), 1.6, 1.6), "g", 0, ao=0)
    info["hit"] |= m
    info["ktip"] = outer[-1]
    info["kmid"] = outer[10]
    return m


def sceptre(L, FX, grip, ang, u0, u1, glow, fi, info):
    """Tall sun sceptre: a gold-banded shaft, a crescent cradling a sun-disc at the top, a forked foot."""
    ca, sa = dirv(ang)
    a = (grip[0] + ca * u0, grip[1] + sa * u0)
    b = (grip[0] + ca * u1, grip[1] + sa * u1)
    shaft = L.paint(n_capsule(a, b, 1.0, 1.0, 1.0), "b", 0, ao=0)
    for k in range(4):                                                                  # gold bands
        u = u0 + (u1 - u0) * (0.2 + 0.2 * k)
        c = (grip[0] + ca * u, grip[1] + sa * u)
        L.paint(n_dome(c, 1.4, 1.4), "g", 0, ao=0)
    nx, ny = -sa, ca
    cres = [(b[0] + nx * k + ca * (1.8 - abs(k) * 0.4), b[1] + ny * k + sa * (1.8 - abs(k) * 0.4)) for k in (-3.8, -2.4, -1.0, 1.0, 2.4, 3.8)]
    L.paint(n_tube(cres, [0.9, 1.0, 1.0, 1.0, 1.0, 0.9]), "g", 0, ao=0)
    dc = (b[0] + ca * 4.8, b[1] + sa * 4.8)
    sun_disc(L, dc, 3.4, fi, glow=glow, FX=FX)
    for sgn in (-1, 1):                                                                 # forked foot
        for q in polyline([ip(a), ip((a[0] - ca * 3.0 + nx * sgn * 1.6, a[1] - sa * 3.0 + ny * sgn * 1.6))]):
            L.fixed({q: "b4"})
    info["tip"] = dc
    info["foot"] = a
    return shaft


# --------------------------------------------------------------------------- the sand cloak
def cloak(Lc, FXB, FX, sh_back, sh_front, P, fi, strength, sw, wind, info):
    """A mantle of pouring sand hung from the shoulders; it falls behind him, then streams back and breaks into grains."""
    k = strength
    flow = -sw * 0.6 - wind * 0.8
    top0, top1 = sh_back, sh_front
    hem_y = FL - 6
    back_edge = []
    for i in range(9):
        t = i / 8
        y = top0[1] + (hem_y - top0[1]) * t
        wave = math.sin(fi * 0.9 + t * 5.2) * (1.0 + 3.0 * t) * k
        x = top0[0] - 3.0 - t * (10.0 + 12.0 * k) + wave + flow * t * 2.0
        back_edge.append((x, y))
    front_edge = [(top1[0] - 2.0, top1[1] + 1.0), (P[0] - 6.0, P[1] - 4.0), (P[0] - 8.0 + flow * 0.5, hem_y - 12.0), (P[0] - 12.0 + flow, hem_y)]
    pts = [top1] + [top0] + back_edge + front_edge[::-1]
    m = poly_mask(pts)
    Lc.paint(n_plate(m, 3.0, (-0.15, -0.1), 1.2, fold=lambda x, y: (0.5 * math.sin(y * 0.35 + fi * 0.9 + x * 0.1), 0)), "z", -1, ao=0)
    # flowing streaks
    Lc.decal([q for q in m if int(q[1] * 0.4 + q[0] * 0.12 + fi * 1.3 + 4 * hash01(q[0] // 3, q[1] // 7, 5)) % 6 == 0], ("z", 2))
    Lc.decal([q for q in m if int(q[1] * 0.4 + q[0] * 0.12 + fi * 1.3 + 4 * hash01(q[0] // 4, q[1] // 5, 6)) % 9 == 4], ("z", 6))
    # grains streaming off the trailing edge (the cloak is always coming apart)
    n = int(40 * k)
    for j in range(n):
        t = hash01(j, 1, 31)
        base = back_edge[min(8, int(t * 8))]
        age = (fi * 0.37 + hash01(j, 2, 31)) % 1.0
        q = ip((base[0] - age * (14 + 10 * k) + math.sin(j + fi) * 1.5, base[1] + age * 6 * (t - 0.3)))
        if K.inb(*q) and q[1] < FL:
            (FXB if j % 3 else FX).put([q], ("z7", "z6", "z5", "z4")[int(age * 4)])
    info["cloak"] = m


# --------------------------------------------------------------------------- the figure
def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n not in NOOUT}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    Pp, Cc, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(Cc, Pp)
    ln = math.hypot(*upv)
    F = basis(Pp, upv)
    shN, shF = F(3.6, -ln + 2.6), F(-3.8, -ln + 3.0)
    hipN, hipF = F(2.4, 0.8), F(-2.4, 0.8)

    # ---- sand cloak
    cloak(Ls["Cloak"], FXB, FX, T(F(-4.2, -ln + 1.0)), T(F(2.0, -ln + 0.4)), T(Pp), fi, p["cloak"], sw, p["wind"], info)

    # ---- legs: long, thin, wrapped; gold anklets
    kf = leg(R, Ls["NearLeg"], hipN, p["ff"], THIGH, SHIN, 2.4, 1.8, "s", bias=-1, knee=p["kf"], flen=4.6, heel=2.0, boot_h=2.2, pref=(1, -0.15))
    kb = leg(R, Ls["FarLeg"], hipF, p["fb"], THIGH, SHIN, 2.4, 1.8, "s", bias=-3, knee=p["kb"], flen=4.6, heel=2.0, boot_h=2.2, pref=(1, -0.15))
    for nm, hip, kn, ft, b in (("NearLeg", hipN, kf, p["ff"], 1), ("FarLeg", hipF, kb, p["fb"], 0)):
        m = set(Ls[nm].px)
        bands(Ls[nm], m, T(hip), T(ft), 2.6, ("s", 1 + b), phase=0.3)
        Ls[nm].decal([q for q in m if hash01(q[0], q[1], 17) < 0.08], ("n", 2))
        ank = T((ft[0], ft[1] - 4.0))
        Ls[nm].decal([q for q in m if abs(q[1] - ank[1]) < 1.0 and abs(q[0] - ank[0]) < 3], ("g", 3 + b))

    # ---- kilt: a long pleated linen skirt, a gold belt, a hieroglyph apron hanging to the knees
    sway = sw * 0.5 - p["wind"] * 0.4
    sk = [F(-4.4, -2.4), F(5.0, -2.4), add(F(6.8, THIGH + 5.0), (sway * 0.4, 0)), add(F(-6.2, THIGH + 4.2), (sway, 0))]
    skm = R.plate(Ls["Skirt"], sk, "s", bevel=2.0, tilt=(-0.15, 0), strength=1.1, fold=lambda x, y: (0.7 * math.sin(x * 1.0), 0), bias=-1)
    Ls["Skirt"].decal([q for q in skm if (q[0] + (q[1] // 3)) % 3 == 0], ("s", 3))
    apron = poly_mask([T(F(0.8, -1.2)), T(F(5.0, -1.2)), T(F(5.8, THIGH + 2.4)), T(F(1.6, THIGH + 2.4))])
    Ls["Skirt"].paint(n_plate(apron, 1.0, (-0.1, 0)), "g", 0, ao=0, clip=apron)
    for k in range(5):                                                                # glyph registers on the apron
        y0 = T(F(3.2, 2.0 + k * 4.0))[1]
        Ls["Skirt"].decal([q for q in apron if abs(q[1] - y0) < 0.6], ("u", 2))
        Ls["Skirt"].decal([q for q in apron if abs(q[1] - (y0 + 2)) < 0.6 and hash01(q[0], k, 5) < 0.5], ("g", 1))
    belt = poly_mask([T(F(-5.4, -3.8)), T(F(5.8, -3.8)), T(F(5.8, -1.6)), T(F(-5.4, -1.6))])
    Ls["Skirt"].paint(n_plate(belt, 0.8, (0, -0.3)), "g", 0, ao=0)
    Ls["Skirt"].decal([q for q in belt if q[0] % 3 == 0], ("u", 3))
    info["skirt"] = skm

    # ---- torso: gaunt, wrapped, ribs of tar showing
    Bd = Ls["Body"]
    torso = [F(-3.0, -0.6), F(-4.4, -ln + 5.0), F(-4.0, -ln + 0.4), F(-1.2, -ln - 1.4), F(3.4, -ln - 1.4), F(5.2, -ln + 1.0),
             F(4.0, -ln + 7.0), F(2.4, -ln * 0.4), F(2.8, -0.6)]
    tm = R.plate(Bd, torso, "s", bevel=2.6, tilt=(-0.2, -0.05), strength=1.3, bias=-1)
    bands(Bd, tm, T(Pp), T(Cc), 2.8, ("s", 2), phase=0.8)
    for k in range(4):                                                                # ribs of tar between the wrappings
        yy = -ln + 11.0 + k * 3.0
        Bd.decal([q for q in polyline([ip(T(F(-1.0, yy))), ip(T(F(3.4, yy - 1.0)))]) if q in tm], ("n", 1))
    info["torso"] = tm

    # ---- far arm + the sun sceptre
    arm(R, Ls["FarArm"], shF, p["hb"], UARM, FARM, 2.0, 1.6, "s", bias=-2, fist="n", fist_r=1.6, pref=(-1, 0.6), elbow=p["eb"])
    bands(Ls["FarArm"], set(Ls["FarArm"].px), T(shF), T(p["hb"]), 2.4, ("s", 1), phase=0.1)
    if p["sang"] is not None:
        sceptre(Ls["Sceptre"], FX, T(p["hb"]), R.A(p["sang"]), p["su0"], p["su1"], p["glow"], fi, info)

    # ---- collar: a broad usekh of gold, lapis and carnelian rows, a falcon-winged pectoral
    Cl = Ls["Collar"]
    cc = F(0.6, -ln + 1.0)
    for rr, mat in ((8.0, "g"), (6.6, "u"), (5.4, "g"), (4.2, "r"), (3.0, "g")):
        m = {q for q in mask_disc(T(cc), rr, rr * 0.62) if (q[1] - T(cc)[1]) >= -0.5}
        if mat == "g":
            Cl.paint(n_dome(T(cc), rr, rr * 0.62, flat=0.7, tilt=(-0.2, -0.3)), "g", 0, ao=0, clip=m)
        else:
            Cl.paint({q: (0, 0, 1) for q in m}, mat, 0, ao=0)
            Cl.decal([q for q in m if q[0] % 2 == 0], (mat, 4 if mat == "u" else 3))
    pec = T(F(0.8, -ln + 9.0))
    Cl.paint(n_dome(pec, 2.4, 2.0, tilt=(-0.2, -0.3)), "g", 0, ao=0)
    FX.put([ip(pec)], "u3" if p["eye"] < 2 else "a3")

    # ---- head: nemes headcloth (gold and lapis stripes), the gold death mask, one amber eye slit
    G0 = basis(Hd, p["hup"])
    G = lambda a, b: G0(a * 1.22, b * 1.22)
    Hl = Ls["Head"]
    Hl.paint(n_tube([T(F(0.8, -ln - 1.0)), T(G(-0.8, 5.0))], [2.4, 2.1]), "s", -1)
    nemes = [G(-6.2, 2.4), G(-6.6, -2.6), G(-4.6, -6.6), G(0.0, -7.8), G(3.6, -6.2), G(4.4, -3.4), G(2.2, -3.2), G(-0.8, 1.6),
             G(-1.6, 9.0), G(-5.4, 12.6), G(-9.4, 10.8)]
    nm = R.plate(Hl, nemes, "g", bevel=2.0, tilt=(-0.25, -0.3), strength=1.3)
    # stripes: lapis bands across the headcloth
    Hl.decal([q for q in nm if int(((q[1] - T(G(0, -8))[1]) * 0.9 + (q[0] - T(G(0, 0))[0]) * 0.25)) % 3 == 0], ("u", 2))
    mask_pts = [G(-0.6, -3.6), G(2.8, -4.4), G(4.8, -2.6), G(6.0, -0.2), G(5.8, 2.2), G(4.2, 4.4), G(1.4, 5.2), G(-0.6, 3.6)]
    mm = R.plate(Hl, mask_pts, "g", bevel=1.6, tilt=(-0.25, -0.15), strength=1.3, bias=-1)
    Hl.decal([q for q in mm if any((q[0] + a, q[1] + b) in nm and (q[0] + a, q[1] + b) not in mm for a, b in ((-1, 0), (0, -1), (0, 1)))], ("g", 0))
    Hl.decal(polyline([ip(T(G(5.0, -0.6))), ip(T(G(6.4, 1.6))), ip(T(G(5.6, 2.2)))]), ("g", 4))       # the nose ridge
    Hl.decal(polyline([ip(T(G(4.2, 3.4))), ip(T(G(5.4, 3.2)))]), ("g", 1))                         # the lips
    beard = [G(2.4, 4.8), G(4.0, 4.8), G(3.8, 10.0), G(2.6, 10.4)]                                  # the false beard
    bm = R.plate(Hl, beard, "g", bevel=0.8, tilt=(-0.2, 0))
    Hl.decal([q for q in bm if q[1] % 2 == 0], ("u", 2))
    sock = poly_mask([T(G(1.6, -2.0)), T(G(5.4, -2.2)), T(G(5.6, -0.2)), T(G(1.8, 0.0))])
    Hl.decal([q for q in sock if q in mm], ("g", 0))
    slit = polyline([ip(T(G(2.0, -1.0))), ip(T(G(5.4, -1.2)))])
    Hl.decal(slit, ("n", 0))
    if p["eye"]:
        e0, e1 = ip(T(G(2.4, -1.0))), ip(T(G(4.8, -1.2)))
        FX.put(polyline([e0, e1]), "a4" if p["eye"] >= 2 else "a3")
        FX.put([e1], "a5" if p["eye"] >= 2 else "a4")
        FX.put([(e1[0] + 1, e1[1])], "a2")
        if p["eye"] >= 2:
            FX.put([(e1[0] + 2, e1[1]), (e1[0] + 3, e1[1]), (e1[0] + 1, e1[1] - 1)], "a2")
    info["eye"] = T(G(4.0, -1.1))
    if p["crack"] > 0:
        Hl.decal([q for q in polyline([ip(T(G(3.0, -4.4))), ip(T(G(4.2, -0.6))), ip(T(G(2.4, 2.4))), ip(T(G(3.8, 5.0)))]) if q in mm], ("g", 0))
    info["head"] = nm | mm
    # ---- crown: the sun-disc between two slender horns, a cobra rearing at the brow
    Cr = Ls["Crown"]
    top = G(-0.8, -7.2)
    dc = T(add(top, (0.0, -10.4)))
    for s_ in (-1, 1):
        hp = curve([T(add(top, (s_ * 1.2, 0.8))), T(add(top, (s_ * 5.6, -3.4))), T(add(top, (s_ * 7.2, -10.0))), T(add(top, (s_ * 5.4, -15.4))),
                    T(add(top, (s_ * 2.6, -17.4)))], 5)
        Cr.paint(n_tube(hp, [1.4 - 1.0 * i / (len(hp) - 1) for i in range(len(hp))]), "b" if s_ < 0 else "g", 0 if s_ > 0 else -1, ao=0)
    Cr.paint(n_tube([T(add(top, (0.0, 0.6))), T(add(top, (0.0, -6.8)))], [1.0, 0.8]), "g", -1, ao=0)          # the disc's stem
    sun_disc(Cr, dc, 3.9, fi, glow=max(p["glow"] - 1, 0) if p["glow"] >= 2 else 0, FX=FX)
    Cr.decal([q for q in mask_disc(dc, 4.2) if abs(math.hypot(q[0] + .5 - dc[0], q[1] + .5 - dc[1]) - 3.4) < 0.5], ("g", 2))
    ur = curve([T(G(3.0, -4.0)), T(G(4.4, -6.6)), T(G(5.8, -7.0))], 3)
    Cr.paint(n_tube(ur, [0.9, 0.9, 0.7]), "g", 0, ao=0)
    FX.put([ip(T(G(5.6, -7.0)))], "a3")
    info["crown"] = dc

    # ---- near arm + the khopesh
    if p["kang"] is not None:
        khopesh(Ls["Khopesh"], T(p["hf"]), R.A(p["kang"]), info)
    el = arm(R, Ls["NearArm"], shN, p["hf"], UARM, FARM, 2.2, 1.8, "s", bias=0, fist="n", fist_r=1.8, pref=(-1, 0.7), elbow=p["ef"])
    bands(Ls["NearArm"], set(Ls["NearArm"].px), T(shN), T(p["hf"]), 2.4, ("s", 2), phase=0.4)
    for c_ in (lerp(T(shN), T(el), 0.45), lerp(T(el), T(p["hf"]), 0.75)):                      # gold armband + bracer
        Ls["NearArm"].decal([q for q in Ls["NearArm"].px if math.hypot(q[0] - c_[0], q[1] - c_[1]) < 2.4 and abs((q[1] - c_[1])) < 1.2], ("g", 4))
    Ls["NearArm"].paint(n_dome(T(add(shN, (0.4, -0.6))), 2.2, 1.8, tilt=(-0.3, -0.4)), "g", 0, ao=0)   # shoulder disc
    info["hand"] = T(p["hf"])
    info["handb"] = T(p["hb"])

    # ---- FX: smears, glints, sand
    if p["smear"]:
        for (g0, a0, g1, a1) in p["smear"]:
            info["hit"] |= swept(FX, T(g0), R.A(a0), T(g1), R.A(a1), 14, 25, hw=1.3, pal="khopesh", taper=0.6)
    if p["glint"]:
        glint(FX, p["glint"], big=True)
    if p["sink"] > 0:
        dy = int(round(p["sink"] * 118))
        for L in Ls.values():
            if isinstance(L, Layer):
                L.px = {(q[0], q[1] + dy): e_ for q, e_ in L.px.items() if q[1] + dy < FL - 1}
        for F_ in (FX, FXB):
            F_.px = {(q[0], q[1] + dy): c for q, c in F_.px.items() if q[1] + dy < FL - 1}
        info["hit"] = {(q[0], q[1] + dy) for q in info["hit"] if q[1] + dy < FL - 1}
        info["eye"] = (info["eye"][0], info["eye"][1] + dy)
        info["tip"] = (info["tip"][0], info["tip"][1] + dy) if "tip" in info else None
    if p["spray"]:
        for k in range(40):
            a = -math.pi * (0.06 + 0.88 * hash01(k, fi, 7))
            rr = 4 + 30 * hash01(k, fi + 1, 7) * p["spray"]
            FX.put([ip((Pp[0] + 6 + math.cos(a) * rr * 1.2, FL - 1 + math.sin(a) * rr))], ("z7", "z6", "z5", "z4")[k % 4])
        for x in range(int(Pp[0] - 24), int(Pp[0] + 34)):
            h = int(2 + 4 * max(0.0, 1 - abs(x - Pp[0] - 5) / 29))
            for y in range(FL - h, FL + 1):
                FX.put([(x, y)], "z6" if y == FL - h else "z5")
    if p["dust"]:
        for k in range(16):
            FX.put([(int(Pp[0] + (hash01(k, fi, 3) - 0.5) * 50), FL - int(hash01(k, fi, 4) * 5))], ("z6", "z5", "z4")[k % 3])
    return Ls, info


# =========================================================================== animations
ST = dict(P=(70.0, 84.0), C=(72.0, 55.0), Hd=(75.4, 42.0), hup=(0.18, -1.0), fb=(62.0, FL), ff=(80.0, FL))


def a_idle():
    fr = []
    for i in range(8):
        b = 0.5 - 0.5 * math.cos(i / 8 * 2 * math.pi)
        fr.append((170, PS(C=(72.0, 55.0 + b * 0.8), Hd=(75.4, 42.0 + b * 1.0), hf=(84.0, 84.0 + b * 0.5), hb=(60.0, 80.0 + b * 0.6),
                           glow=1 if i in (3, 4) else 0)))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        bob = 1.0 * abs(s)
        fr.append((140, PS(P=(70.0, 84.0 + bob), C=(72.6, 55.2 + bob), Hd=(76.2, 42.4 + bob), hup=(0.24, -1.0),
                           ff=(71.0 + 10.0 * c, FL - max(0, s) * 3.0), fb=(69.0 - 10.0 * c, FL - max(0, -s) * 3.0),
                           hf=(84.0 + 1.2 * c, 84.0 + bob), kang=62 + 4 * c, hb=(60.0 - 1.4 * c, 80.0 + bob), wind=-1.0)))
    return fr


CROSS = dict(P=(70.0, 84.0), C=(71.0, 55.2), Hd=(72.6, 43.6), hup=(0.05, -1.0), fb=(66.0, FL), ff=(76.0, FL),
             hf=(66.0, 64.0), kang=-120, hb=(78.0, 64.0), sang=-58, su0=-26, su1=30, ef=(80.0, 70.0), eb=(62.0, 70.0))


def a_rise():
    """Intro: a standing sarcophagus pose (arms crossed, weapons on the chest), then the eye kindles and he unfolds."""
    fr = [(700, PS(**dict(CROSS, Hd=(72.0, 45.0), hup=(-0.1, -1.0)), eye=0, cloak=0.3)),
          (500, PS(**dict(CROSS, Hd=(72.0, 45.0), hup=(-0.1, -1.0)), eye=1, cloak=0.3)),
          (240, PS(**CROSS, eye=2, cloak=0.5)),
          (200, PS(**dict(CROSS, hf=(70.0, 66.0), hb=(74.0, 66.0), ef=None, eb=None), eye=2, cloak=0.7)),
          (180, PS(**dict(CROSS, hf=(78.0, 72.0), kang=-40, hb=(66.0, 70.0), sang=-80, ef=None, eb=None), eye=2, cloak=0.9)),
          (160, PS(hf=(82.0, 78.0), kang=20, hb=(62.0, 76.0), eye=2, cloak=1.0)),
          (200, PS(hf=(84.0, 82.0), kang=50, eye=2, glow=1, dust=1)),
          (240, PS(eye=2, glow=2)),
          (200, PS(eye=2, glow=1)),
          (200, PS())]
    return fr


def a_combo():
    wind1 = dict(P=(68.0, 85.0), C=(67.0, 56.4), Hd=(69.6, 43.8), hup=(-0.05, -1.0), fb=(58.0, FL), ff=(78.0, FL))
    cut1 = dict(P=(74.0, 85.4), C=(80.0, 57.6), Hd=(85.0, 45.4), hup=(0.55, -1.0), fb=(60.0, FL), ff=(90.0, FL))
    wind2 = dict(P=(73.0, 85.4), C=(76.0, 57.0), Hd=(80.4, 44.6), hup=(0.4, -1.0), fb=(60.0, FL), ff=(88.0, FL))
    over = dict(P=(72.0, 84.0), C=(72.4, 55.0), Hd=(75.0, 42.2), hup=(0.05, -1.0), fb=(60.0, FL), ff=(86.0, FL))
    slam = dict(P=(78.0, 88.0), C=(86.0, 62.0), Hd=(92.0, 51.0), hup=(0.9, -1.0), fb=(62.0, FL), ff=(96.0, FL))
    return [
        (110, PS(**wind1, hf=(78.0, 70.0), kang=-100, hb=(58.0, 78.0))),
        (160, PS(**wind1, hf=(70.0, 60.0), kang=-150, hb=(56.0, 76.0), eye=2)),
        (170, PS(**wind1, hf=(66.0, 56.0), kang=-165, hb=(55.0, 76.0), eye=2, glint=(58.0, 38.0))),
        (60, PS(**cut1, hf=(102.0, 74.0), kang=-10, hb=(64.0, 80.0), eye=2, smear=[((66.0, 56.0), -165, (102.0, 74.0), -10)], dust=1)),
        (70, PS(**cut1, hf=(100.0, 86.0), kang=40, hb=(64.0, 82.0), eye=2, smear=[((102.0, 74.0), -10, (100.0, 86.0), 40)])),
        (110, PS(**cut1, hf=(96.0, 90.0), kang=70, hb=(64.0, 82.0))),
        (140, PS(**wind2, hf=(92.0, 92.0), kang=130, hb=(64.0, 82.0), eye=2)),
        (150, PS(**wind2, hf=(88.0, 94.0), kang=150, hb=(64.0, 82.0), eye=2, glint=(80.0, 112.0))),
        (60, PS(**cut1, hf=(104.0, 64.0), kang=-60, hb=(66.0, 80.0), eye=2, smear=[((88.0, 94.0), 150, (104.0, 64.0), -60)])),
        (70, PS(**cut1, hf=(96.0, 52.0), kang=-110, hb=(66.0, 78.0), eye=2, smear=[((104.0, 64.0), -60, (96.0, 52.0), -110)])),
        (150, PS(**over, hf=(80.0, 38.0), kang=-160, hb=(62.0, 76.0), eye=2)),
        (190, PS(**over, hf=(76.0, 32.0), kang=-175, hb=(62.0, 76.0), eye=2, glint=(70.0, 18.0), glow=1)),
        (60, PS(**slam, hf=(108.0, 86.0), kang=30, hb=(70.0, 84.0), eye=2, smear=[((76.0, 32.0), -175, (108.0, 86.0), 30)], dust=1)),
        (80, PS(**slam, hf=(110.0, 96.0), kang=62, hb=(70.0, 86.0), eye=2, smear=[((108.0, 86.0), 30, (110.0, 96.0), 62)], dust=1)),
        (190, PS(**slam, hf=(106.0, 100.0), kang=70, hb=(70.0, 86.0))),
        (200, PS(P=(72.0, 85.0), C=(76.0, 56.4), Hd=(80.0, 43.8), hup=(0.4, -1.0), ff=(88.0, FL), hf=(90.0, 86.0), kang=66)),
    ]


def a_beam():
    """Sceptre raised forward-high, the disc gathers light (0-5); the beam fires (6-10) as the sceptre sweeps down; recover."""
    brace = dict(P=(67.0, 85.0), C=(66.0, 56.4), Hd=(68.6, 43.6), hup=(-0.05, -1.0), fb=(54.0, FL), ff=(80.0, FL))
    fire = dict(P=(70.0, 85.0), C=(72.0, 56.0), Hd=(76.0, 43.2), hup=(0.3, -1.0), fb=(56.0, FL), ff=(84.0, FL))
    fr = [(120, PS(**brace, hb=(70.0, 62.0), sang=-70, su0=-30, su1=40, hf=(72.0, 84.0), kang=70, glow=1)),
          (140, PS(**brace, hb=(76.0, 50.0), sang=-52, su0=-30, su1=40, hf=(70.0, 82.0), kang=70, glow=1)),
          (150, PS(**brace, hb=(80.0, 44.0), sang=-45, su0=-30, su1=40, hf=(68.0, 82.0), kang=70, glow=2, eye=2)),
          (150, PS(**brace, hb=(80.0, 44.0), sang=-45, su0=-30, su1=40, hf=(68.0, 82.0), kang=70, glow=2, eye=2)),
          (150, PS(**brace, hb=(80.0, 44.0), sang=-45, su0=-30, su1=40, hf=(68.0, 82.0), kang=70, glow=3, eye=2)),
          (130, PS(**brace, hb=(81.0, 44.0), sang=-44, su0=-30, su1=40, hf=(68.0, 82.0), kang=70, glow=3, eye=2))]
    for k in range(5):
        t = k / 4
        fr.append((110, PS(**fire, hb=(86.0 + t * 2, 48.0 + t * 10), sang=-40 + t * 58, su0=-30, su1=40, hf=(70.0, 82.0), kang=70, glow=3, eye=2,
                           wind=3.0, dust=1 if k > 2 else 0)))
    fr += [(150, PS(**fire, hb=(84.0, 64.0), sang=30, su0=-30, su1=40, hf=(72.0, 82.0), kang=68, glow=1)),
           (150, PS(hb=(66.0, 72.0), sang=-60, su0=-36, su1=40, glow=0)),
           (160, PS())]
    return fr


def a_coffin():
    """Both hands lift the sceptre overhead (0-5), drive its forked foot into the sand (6: the engine raises the coffins)."""
    up = dict(P=(69.0, 84.0), C=(69.6, 55.0), Hd=(72.4, 42.4), hup=(0.05, -1.0), fb=(58.0, FL), ff=(80.0, FL))
    down = dict(P=(72.0, 88.0), C=(78.0, 61.0), Hd=(83.0, 50.0), hup=(0.8, -1.0), fb=(58.0, FL), ff=(86.0, FL))
    return [
        (120, PS(**up, hb=(74.0, 58.0), sang=-95, su0=-36, su1=34, hf=(76.0, 64.0), kang=-40)),
        (140, PS(**up, hb=(76.0, 44.0), sang=-92, su0=-30, su1=40, hf=(80.0, 50.0), kang=-100, eye=2)),
        (150, PS(**up, hb=(78.0, 34.0), sang=-90, su0=-26, su1=44, hf=(82.0, 40.0), kang=-120, eye=2, glow=1)),
        (170, PS(**up, hb=(78.0, 32.0), sang=-90, su0=-26, su1=44, hf=(82.0, 38.0), kang=-120, eye=2, glow=2, glint=(78.0, 110.0))),
        (150, PS(**up, hb=(78.0, 32.0), sang=-90, su0=-26, su1=44, hf=(82.0, 38.0), kang=-120, eye=2, glow=2)),
        (60, PS(**down, hb=(92.0, 74.0), sang=-92, su0=-44, su1=24, hf=(96.0, 78.0), kang=-40, eye=2, glow=2)),
        (90, PS(**down, hb=(92.0, 82.0), sang=-92, su0=-44, su1=24, hf=(96.0, 84.0), kang=-30, eye=2, glow=3, spray=0.8, dust=1)),
        (200, PS(**down, hb=(92.0, 82.0), sang=-92, su0=-44, su1=24, hf=(96.0, 84.0), kang=-30, eye=2, glow=2, spray=0.5, dust=1)),
        (170, PS(**down, hb=(90.0, 82.0), sang=-92, su0=-44, su1=24, hf=(94.0, 86.0), kang=10, glow=1)),
        (160, PS(P=(71.0, 85.0), C=(74.0, 56.4), Hd=(78.0, 43.8), hup=(0.4, -1.0), hb=(80.0, 78.0), sang=-92, su0=-44, su1=30, hf=(86.0, 84.0), kang=50)),
        (160, PS(hb=(66.0, 80.0), sang=-92, su0=-42, su1=38)),
        (160, PS()),
    ]


def a_summon():
    """Arms spread and lifted, the cloak billows; the sand answers (spawn at 7)."""
    spread = dict(P=(70.0, 84.0), C=(70.4, 54.6), Hd=(72.6, 41.6), hup=(-0.1, -1.0), fb=(58.0, FL), ff=(82.0, FL))
    return [
        (120, PS(**spread, hf=(86.0, 70.0), kang=-40, hb=(56.0, 70.0), sang=-92, su0=-30, su1=40)),
        (140, PS(**spread, hf=(92.0, 56.0), kang=-80, hb=(52.0, 58.0), sang=-100, su0=-30, su1=40, eye=2, cloak=1.3, wind=-2.0)),
        (150, PS(**spread, hf=(94.0, 44.0), kang=-100, hb=(50.0, 46.0), sang=-104, su0=-30, su1=40, eye=2, cloak=1.5, wind=-3.0, glow=1)),
        (150, PS(**spread, hf=(95.0, 40.0), kang=-104, hb=(50.0, 42.0), sang=-104, su0=-30, su1=40, eye=2, cloak=1.6, wind=-3.0, glow=2)),
        (150, PS(**spread, hf=(95.0, 40.0), kang=-104, hb=(50.0, 42.0), sang=-104, su0=-30, su1=40, eye=2, cloak=1.7, wind=-4.0, glow=2)),
        (140, PS(**spread, hf=(95.0, 40.0), kang=-104, hb=(50.0, 42.0), sang=-104, su0=-30, su1=40, eye=2, cloak=1.7, wind=-4.0, glow=3)),
        (100, PS(**spread, hf=(96.0, 46.0), kang=-90, hb=(50.0, 48.0), sang=-100, su0=-30, su1=40, eye=2, cloak=1.8, wind=-4.0, glow=3)),
        (160, PS(**spread, hf=(98.0, 70.0), kang=-20, hb=(48.0, 70.0), sang=-92, su0=-40, su1=34, eye=2, cloak=1.4, spray=0.7, dust=1, glow=2)),
        (180, PS(**spread, hf=(94.0, 76.0), kang=10, hb=(52.0, 74.0), sang=-92, su0=-40, su1=34, cloak=1.2, spray=0.4, dust=1, glow=1)),
        (160, PS(hf=(88.0, 80.0), kang=40, hb=(56.0, 78.0), cloak=1.1)),
        (150, PS(hf=(85.0, 83.0), kang=58)),
        (150, PS()),
    ]


def a_disc():
    """The sceptre raised high, the disc swells with light (0-6); he flings it (7: the engine releases the tracking sun-disc)."""
    lift = dict(P=(69.0, 84.0), C=(69.0, 55.0), Hd=(71.6, 42.2), hup=(-0.05, -1.0), fb=(58.0, FL), ff=(80.0, FL))
    fling = dict(P=(73.0, 85.0), C=(78.0, 57.0), Hd=(83.0, 45.0), hup=(0.6, -1.0), fb=(60.0, FL), ff=(88.0, FL))
    return [
        (120, PS(**lift, hb=(66.0, 60.0), sang=-100, su0=-30, su1=40, glow=1)),
        (140, PS(**lift, hb=(64.0, 44.0), sang=-104, su0=-30, su1=44, glow=1, eye=2)),
        (150, PS(**lift, hb=(62.0, 36.0), sang=-108, su0=-30, su1=44, glow=2, eye=2)),
        (150, PS(**lift, hb=(62.0, 36.0), sang=-108, su0=-30, su1=44, glow=3, eye=2)),
        (150, PS(**lift, hb=(62.0, 36.0), sang=-108, su0=-30, su1=44, glow=3, eye=2, glint=(58.0, 4.0))),
        (120, PS(**lift, hb=(60.0, 38.0), sang=-120, su0=-30, su1=44, glow=3, eye=2)),
        (100, PS(**lift, hb=(58.0, 40.0), sang=-130, su0=-30, su1=44, glow=3, eye=2)),
        (60, PS(**fling, hb=(90.0, 46.0), sang=-40, su0=-30, su1=44, glow=1, eye=2, wind=3.0)),
        (140, PS(**fling, hb=(96.0, 60.0), sang=-10, su0=-30, su1=44, glow=0, eye=2)),
        (160, PS(**fling, hb=(90.0, 70.0), sang=-60, su0=-30, su1=44)),
        (150, PS(hb=(66.0, 76.0), sang=-88, su0=-42, su1=40)),
        (150, PS()),
    ]


def a_vanish():
    fr = []
    for k in range(8):
        s = max(0.0, (k - 1) / 6.0)
        fr.append((90 if k else 140, PS(sink=s * 1.02, spray=1.0 if k > 0 else 0.4, cloak=1.4, wind=-3.0, eye=2,
                                        hf=(84.0, 80.0), kang=40, hb=(62.0, 74.0))))
    return fr


def a_emerge():
    up = dict(P=(72.0, 84.0), C=(75.0, 55.0), Hd=(79.0, 42.6), hup=(0.3, -1.0), fb=(62.0, FL), ff=(86.0, FL))
    return [
        (80, PS(**up, sink=0.8, spray=1.0, hf=(84.0, 86.0), kang=150, eye=2)),
        (70, PS(**up, sink=0.55, spray=1.0, hf=(86.0, 84.0), kang=150, eye=2)),
        (70, PS(**up, sink=0.3, spray=1.0, hf=(88.0, 84.0), kang=150, eye=2, glint=(96.0, 110.0))),
        (80, PS(**up, sink=0.1, spray=0.8, hf=(90.0, 88.0), kang=160, eye=2)),
        (60, PS(**up, spray=0.6, hf=(104.0, 58.0), kang=-70, eye=2, smear=[((90.0, 88.0), 160, (104.0, 58.0), -70)], dust=1)),
        (70, PS(**up, spray=0.4, hf=(96.0, 38.0), kang=-120, eye=2, smear=[((104.0, 58.0), -70, (96.0, 38.0), -120)])),
        (90, PS(**up, hf=(90.0, 34.0), kang=-140, eye=2)),
        (150, PS(**up, hf=(88.0, 50.0), kang=-60)),
        (160, PS(hf=(86.0, 76.0), kang=30)),
        (160, PS()),
    ]


def a_stagger():
    rock = dict(P=(66.0, 85.0), C=(62.0, 58.0), Hd=(62.0, 46.0), hup=(-0.5, -1.0), fb=(58.0, FL), ff=(78.0, FL))
    slump = dict(P=(68.0, 90.0), C=(74.0, 64.0), Hd=(80.0, 54.0), hup=(0.9, -0.9), fb=(56.0, FL), ff=(80.0, FL))
    return [(90, PS(**rock, hf=(76.0, 60.0), kang=-120, hb=(52.0, 64.0), sang=-120, eye=1)),
            (140, PS(**slump, hf=(86.0, 100.0), kang=70, hb=(62.0, 96.0), sang=-80, su0=-30, su1=40, eye=1)),
            (300, PS(**slump, hf=(86.0, 102.0), kang=72, hb=(62.0, 98.0), sang=-80, su0=-30, su1=40, eye=1)),
            (300, PS(**dict(slump, C=(74.4, 64.6), Hd=(80.6, 54.8)), hf=(86.0, 103.0), kang=74, hb=(62.0, 99.0), sang=-80, su0=-30, su1=40, eye=1))]


def a_death():
    kneel = dict(P=(68.0, 99.0), C=(74.0, 72.0), Hd=(80.0, 61.0), hup=(0.8, -1.0), kf=(84.0, 104.0), ff=(82.0, FL), kb=(62.0, 121.0),
                 fb=(44.0, FL), hf=(92.0, 114.0), kang=90, hb=(58.0, 106.0), sang=-86, su0=-18, su1=50)
    names = [n for n in LAYERS if n not in NOOUT]
    pal = ("a3", "g4", "z6", "z5", "z4")
    fr = [(110, PS(P=(66.0, 85.0), C=(61.0, 58.0), Hd=(60.0, 46.0), hup=(-0.6, -1.0), fb=(58.0, FL), ff=(78.0, FL), hf=(78.0, 60.0), kang=-120,
                   hb=(50.0, 62.0), sang=-120, eye=2)),
          (200, PS(P=(67.0, 92.0), C=(70.0, 64.0), Hd=(74.0, 52.0), hup=(0.4, -1.0), kf=(80.0, 98.0), kb=(60.0, 110.0), fb=(52.0, FL), ff=(84.0, FL),
                   hf=(88.0, 100.0), kang=80, hb=(58.0, 96.0), sang=-86, su0=-30, su1=44, eye=2)),
          (260, PS(**kneel, eye=1, cloak=0.6)),
          (400, PS(**dict(kneel, Hd=(80.4, 62.0), hup=(0.95, -1.0)), eye=2, crack=1, cloak=0.5)),
          (300, PS(**dict(kneel, Hd=(80.4, 62.0), hup=(0.95, -1.0)), eye=1, crack=1, cloak=0.3)),
          (300, PS(**dict(kneel, Hd=(80.8, 63.0), hup=(1.0, -0.9)), eye=0, crack=1, cloak=0.1))]
    for k, (sq, burn) in enumerate(((0.85, 0.1), (0.7, 0.2), (0.55, 0.28), (0.42, 0.34), (0.3, 0.4), (0.2, 0.45), (0.12, 0.5), (0.07, 0.54),
                                    (0.04, 0.58), (0.02, 0.62))):
        fr.append((140 if k < 9 else 800, PS(**dict(kneel, Hd=(80.8, 63.0), hup=(1.0, -0.9)), eye=0, crack=1, cloak=0.0, dust=1,
                                                post=collapse(names, sq, burn, seed=11, pal=pal, spread=0.2 + k * 0.1))))
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("rise", a_rise), ("combo", a_combo), ("stagger", a_stagger), ("beam", a_beam), ("coffin", a_coffin),
           ("summon", a_summon), ("disc", a_disc), ("vanish", a_vanish), ("emerge", a_emerge), ("death", a_death)]
SHEETS = {"pharaoh_a": ("idle", "walk", "rise"), "pharaoh_b": ("combo", "stagger"), "pharaoh_c": ("beam", "coffin"),
          "pharaoh_d": ("summon", "disc"), "pharaoh_e": ("vanish", "emerge"), "pharaoh_f": ("death",)}
LOOPS = ("idle", "walk")


def render(only=None):
    out, infos, tags = [], {}, []
    n = 0
    for tag, fn in TAGDEFS:
        if only and tag not in only:
            continue
        fr = fn()
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
        print("rendered", tag, len(fr), flush=True)
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


def pt(q):
    return [int(round(q[0])), int(round(q[1]))] if q else [AX, 30]


def main():
    out, infos, tags = render(ONLY)
    flats = [K.flatten(imgs, LAYERS) for _, imgs in out]
    K.preview_rows("pharaoh" + ("_wip" if ONLY else ""), tags, flats, scale=3)
    if ONLY:
        return
    idle = infos["idle"][0]
    tb = bbox(idle["torso"] | idle["head"] | idle["skirt"])
    meta = {
        "native": 1, "frame": [W, H], "anchor": [AX, H],
        "hurtbox": [tb[0] + 2, tb[1] + 2, tb[2] - 4, H - tb[1] - 2],
        "sheets": {t: s for s, ts in SHEETS.items() for t in ts},
        "attacks": {
            "combo": {"windows": [{"active": [3, 4], "hit": hit(infos, "combo", [3, 4], AX)},
                                  {"active": [8, 9], "hit": hit(infos, "combo", [8, 9], AX)},
                                  {"active": [12, 13], "hit": hit(infos, "combo", [12, 13], AX)}]},
            "emerge": {"active": [4, 5], "hit": hit(infos, "emerge", [4, 5], AX - 10)},
        },
        "telegraph": {"combo": {"frame": 1, "at": [58, 38]}, "emerge": {"frame": 2, "at": [96, 110]}},
        "events": {"beam_on": 6, "beam_off": 10, "coffin": 6, "summon": 7, "disc": 7},
        "spawn": {"tip": {"frames": {t: [pt(i.get("tip")) for i in infos[t]] for t in infos}}},
        "eye": {t: [pt(i.get("eye")) for i in infos[t]] for t in infos},
        "notes": "faces right, anchor = feet. combo = three khopesh cuts (3-4 rising diagonal, 8-9 upswing, 12-13 overhead slam). "
                 "beam: sceptre raised (0-5, disc gathers light), beam fires 6-10 while the sceptre sweeps down (engine draws the ray "
                 "from spawn.tip). coffin: sceptre driven into the sand at 6. summon: arms spread, spawn at 7. disc: the sun-disc "
                 "is flung at 7. vanish/emerge: into and out of the storm-sand (emerge cut 4-5). rise = intro (frame 0 = the dormant "
                 "sarcophagus pose). eye = per-frame eye-slit point for the storm glow.",
    }
    E3.hitbox_preview3("pharaoh", tags, flats, {k: v for k, v in meta.items() if k != "spawn"})
    with open(os.path.join(asebuild.ASSETS, "pharaoh_meta.json"), "w") as fh:
        json.dump(meta, fh)
    for t, d in meta["attacks"].items():
        print("attack", t, d.get("windows") or (d["active"], d["hit"]))
    print("hurtbox", meta["hurtbox"])
    if BUILD:
        for sname, keep in SHEETS.items():
            frames, st = [], []
            for (t, a, b) in tags:
                if t not in keep:
                    continue
                s0 = len(frames)
                for k in range(a, b + 1):
                    frames.append({"ms": out[k][0], "cels": {n_: out[k][1][n_] for n_ in LAYERS if n_ in out[k][1]}})
                st.append((t, s0, len(frames) - 1))
            asebuild.build(sname, W, H, LAYERS, frames, st)
            print("built", sname, len(frames))


if __name__ == "__main__":
    main()
