#!/usr/bin/env python3
"""The Veiled Pharaoh (agent DU main boss), v2 -- a massive mummified god-king.

    python3 art/gen_dunes_pharaoh.py [--preview] [--only idle,combo]

Frame 192x160, faces RIGHT, feet on the bottom row, anchor x = 88. ~136px to the top of the crown horns.
Heroic and heavy: a broad bandaged torso under a segmented gold cuirass, a huge usekh collar, great layered gold pauldrons,
thick wrapped arms with gold bracers, heavy legs with gold greaves, a lamellar gold-and-linen war kilt. The head: a striped
gold-and-lapis nemes, the gold death mask in profile with one amber eye slit, a towering crown -- a blazing sun-disc cradled by
long curved horns, a rearing uraeus. A mantle of pouring sand streams off his shoulders. A great gold khopesh in the near hand;
in the far hand a was-sceptre crowned with a jackal's head, a sun-disc hovering over it (the beams, disc and blasts come from
there).
Skeleton: every pose is authored in the v1 coordinate space and mapped (x1.3 about the feet) onto this frame; the bone lengths
(thigh, shin, upper arm, forearm) are fixed constants, so proportions stay identical in every frame.
Sheets (share assets/pharaoh_meta.json; `sheets` maps tag -> sheet):
  pharaoh_a idle(8) walk(8)      pharaoh_b rise(10) stagger(4)   pharaoh_c combo(20)     pharaoh_d lunge(12)
  pharaoh_e slam(14)             pharaoh_f beam(14)              pharaoh_g coffin(12)    pharaoh_h summon(12)
  pharaoh_i disc(12) command(10) pharaoh_j vanish(8) emerge(10)  pharaoh_k death(16)
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

W, H = 192, 160
K.setup(W, H)
FL = 159
AX = 88
OFL = 127           # the v1 floor: poses below are authored in v1 space and mapped by M()
SC = 1.3
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None

LAYERS = ["FXBack", "Cloak", "FarArm", "Sceptre", "FarLeg", "Skirt", "NearLeg", "Body", "Armour", "Collar", "Head", "Crown", "Khopesh",
          "NearArm", "Pauldron", "FX"]
NOOUT = {"FX", "FXBack"}
THIGH, SHIN, UARM, FARM = 26.0, 27.5, 19.5, 19.5
HS = 2.15           # head scale (v1 head polygons)
NEU = dict(P=(70.0, 84.0), C=(72.0, 55.0), Hd=(75.4, 42.0), hup=(0.18, -1.0),
           fb=(62.0, OFL), ff=(80.0, OFL), kb=None, kf=None,
           hf=(84.0, 84.0), kang=62, hb=(60.0, 80.0), sang=-92, su0=-44, su1=40,
           eb=None, ef=None, glow=0, eye=1, cloak=1.0, smear=None, sink=0.0, spray=0, dust=0, glint=None, rot=0.0, piv=(70, 100), wind=0.0,
           mask_off=0.0, crack=0.0, shock=0)
PS = mk(NEU)
PTS = ("P", "C", "Hd", "fb", "ff", "kb", "kf", "hf", "hb", "eb", "ef", "glint", "piv")


def M(q):
    return (AX + (q[0] - 72.0) * SC, FL - (OFL - q[1]) * SC)


def conv(p):
    q = dict(p)
    for k in PTS:
        if q.get(k) is not None:
            q[k] = M(q[k])
    q["su0"], q["su1"] = p["su0"] * SC, p["su1"] * SC
    if q.get("smear"):
        q["smear"] = [(M(g0), a0, M(g1), a1) for (g0, a0, g1, a1) in q["smear"]]
    return q


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


# --------------------------------------------------------------------------- dark-mythology palette (v3)
# tarnished, aged dark gold (the armour), blackened grave-linen, deep lapis, dark sand: gold only as the lit accent
for _r, _cols in {
    "t": ["#100a05", "#1d1409", "#2c1f0d", "#3e2c12", "#533b16", "#6d4f1c", "#8c6824", "#b08a32", "#d8b454"],
    "w": ["#0a0807", "#13100e", "#1d1916", "#29231e", "#372e27", "#473c32", "#5a4c3e"],
    "q": ["#05070f", "#0a1024", "#111c3e", "#1a2c5c", "#2a4580"],
    "k": ["#140c05", "#22150a", "#33200e", "#472d13", "#5e3d19", "#7a5222", "#98692c", "#b8843a"],
}.items():
    _keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[j:j + 2], 16) for j in (1, 3, 5)) + (255,)
        _keys.append(_k)
    K.RAMP[_r] = _keys
K.SHINY.update({"t": 0.93})
K.SMEAR["khopesh_d"] = ["a5", "a4", "t8", "t6"]
GOLD, LIN, LAP, SAND = "t", "w", "q", "k"


# --------------------------------------------------------------------------- weapons
def khopesh(L, grip, ang, info):
    """A great khopesh of tarnished gold: a bound neck, then the deep forward hook; the honed outer edge still bright."""
    ca, sa = dirv(ang)
    nx, ny = -sa, ca
    outer, inner = [], []
    for k in range(21):
        t = k / 20
        u = 4.0 + t * 31.0
        curl = max(0.0, t - 0.36) ** 1.6 * 15.5
        w = 2.0 if t < 0.36 else 2.0 + (t - 0.36) * 7.6 * (1 - max(0, t - 0.86) * 5)
        c = (grip[0] + ca * u - nx * curl, grip[1] + sa * u - ny * curl)
        outer.append((c[0] + nx * w, c[1] + ny * w))
        inner.append((c[0] - nx * 1.2, c[1] - ny * 1.2))
    m = poly_mask(outer + inner[::-1])
    L.paint(n_plate(m, 1.8, (-0.25, -0.3), 1.4), GOLD, 0, ao=0)
    edge = [q for q in {ip(q) for q in outer} if q in m]
    L.decal(edge, ("g", 4))
    L.decal([q for q in m if hash01(q[0], q[1], 13) < 0.07], (GOLD, 1))                         # pitting and engraving
    mid = [ip((grip[0] + ca * u, grip[1] + sa * u)) for u in range(6, 16)]
    L.decal([q for q in mid if q in m], (LAP, 3))
    L.paint(n_capsule(grip, (grip[0] - ca * 5.5, grip[1] - sa * 5.5), 1.8, 1.6, 1.0), LIN, 0, ao=0)
    L.paint(n_dome((grip[0] + ca * 3.0, grip[1] + sa * 3.0), 2.4, 2.4), GOLD, 0, ao=0)
    L.paint(n_dome((grip[0] - ca * 6.2, grip[1] - sa * 6.2), 1.9, 1.9), GOLD, 0, ao=0)
    info["hit"] |= m
    info["ktip"] = outer[-1]
    return m


def jackal_head(L, base, fwd, up, s=1.0, bias=0):
    def P_(a, b):
        return (base[0] + fwd[0] * a * s + up[0] * b * s, base[1] + fwd[1] * a * s + up[1] * b * s)
    skull = [P_(-2.4, -1.8), P_(-2.2, 2.4), P_(0.4, 3.2), P_(2.4, 2.4), P_(6.4, 1.2), P_(7.0, 0.2), P_(6.2, -0.6), P_(1.6, -1.8)]
    m = poly_mask(skull)
    L.paint(n_plate(m, 1.2, (-0.2, -0.3), 1.4), "h", bias, ao=0)                                   # a black jackal, gold-lined
    for ex in (-1.2, 0.6):
        em = poly_mask([P_(ex - 0.9, 2.2), P_(ex + 0.2, 7.4), P_(ex + 1.1, 2.2)])
        L.paint(n_plate(em, 0.6, (-0.2, -0.3)), "h", bias - (1 if ex < 0 else 0), ao=0)
        L.decal([q for q in em if (q[0], q[1] - 1) not in em], (GOLD, 7))
    L.decal(polyline([ip(P_(1.0, 1.0)), ip(P_(5.8, 0.6))]), (GOLD, 6))
    L.fixed({ip(P_(2.0, 1.0)): "a3"})
    return m


def sceptre(L, FX, grip, ang, u0, u1, glow, fi, info):
    ca, sa = dirv(ang)
    a = (grip[0] + ca * u0, grip[1] + sa * u0)
    b = (grip[0] + ca * u1, grip[1] + sa * u1)
    L.paint(n_capsule(a, b, 1.6, 1.6, 1.0), "b", -1, ao=0)
    for k in range(5):
        u = u0 + (u1 - u0) * (0.12 + 0.18 * k)
        L.paint(n_dome((grip[0] + ca * u, grip[1] + sa * u), 2.2, 2.2), GOLD, 0, ao=0)
    nx, ny = -sa, ca
    fwd = (nx, ny) if nx >= 0 else (-nx, -ny)
    jackal_head(L, b, fwd, (ca, sa), 1.7)
    dc = (b[0] + ca * 14.0 + fwd[0] * 3.0, b[1] + sa * 14.0 + fwd[1] * 3.0)
    sun_disc(L, dc, 4.8, fi, glow=max(1, glow), FX=FX)
    for sgn in (-1, 1):
        for q in polyline([ip(a), ip((a[0] - ca * 4.6 + nx * sgn * 2.6, a[1] - sa * 4.6 + ny * sgn * 2.6))]):
            L.fixed({q: "b3"})
    info["tip"] = dc
    return dc


def lames(L, c, down, s, bias, n=3):
    """A pauldron of stacked crescent lames wrapped over the shoulder cap and following the upper arm (`down` = arm direction)."""
    ux, uy = down
    vx, vy = -uy, ux
    if vx < 0:
        vx, vy = -vx, -vy
    allm = set()
    for k in range(n):
        rx, ry = (10.5 - k * 1.6) * s, (6.0 - k * 0.8) * s
        cc = (c[0] + ux * k * 3.6 * s, c[1] + uy * k * 3.6 * s)
        pts = []
        for i in range(13):
            a = math.pi + i * math.pi / 12
            pts.append((cc[0] + vx * math.cos(a) * rx - ux * (-math.sin(a)) * ry, cc[1] + vy * math.cos(a) * rx - uy * (-math.sin(a)) * ry))
        for i in range(13):
            a = 2 * math.pi - i * math.pi / 12
            pts.append((cc[0] + vx * math.cos(a) * rx * 0.94 + ux * (2.8 * s + math.sin(a) * ry * 0.25),
                        cc[1] + vy * math.cos(a) * rx * 0.94 + uy * (2.8 * s + math.sin(a) * ry * 0.25)))
        m = poly_mask(pts)
        L.paint(n_plate(m, 2.0, (-0.35, -0.4), 1.5), GOLD, bias - k, ao=1)
        L.decal([q for q in m if (q[0], q[1] - 1) not in m], (GOLD, 7 if bias >= 0 else 5))
        if k == n - 1:
            L.decal([q for q in m if (q[0], q[1] + 1) not in m], (LAP, 3))
        allm |= m
    return allm


# --------------------------------------------------------------------------- the sand mantle
def cloak(Lc, FXB, FX, sh_back, sh_front, P, fi, strength, sw, wind, info):
    """A heavy mantle of dark pouring sand hung from the shoulders: it billows back in rolling folds and its trailing hem tears
    into long flame-like tongues that stream away into grains."""
    k = strength
    flow = -sw * 0.8 - wind * 1.0
    hem_y = FL - 3
    back_edge = []
    n = 22
    for i in range(n + 1):
        t = i / n
        y = sh_back[1] + (hem_y - sh_back[1]) * t
        wave = math.sin(fi * 0.9 + t * 6.0) * (1.6 + 5.0 * t) * k + math.sin(fi * 1.7 + t * 11.0) * 1.2 * t
        x = sh_back[0] - 5.0 - t * (14.0 + 14.0 * k) + wave + flow * t * 3.0
        # three trailing tongues torn out of the hem, flicking with the wind
        for (tc, ln_) in ((0.45, 10.0), (0.68, 14.0), (0.88, 12.0)):
            d = abs(t - tc)
            if d < 0.07:
                x -= (1 - d / 0.07) * (ln_ + 4 * math.sin(fi * 1.3 + tc * 9)) * k
                y += (1 - d / 0.07) * 3.0 * math.sin(fi * 0.8 + tc * 7)
        back_edge.append((x, y))
    front_edge = [(sh_front[0] - 2.0, sh_front[1] + 3.0), (P[0] - 10.0, P[1] - 8.0), (P[0] - 14.0 + flow * 0.5, hem_y - 18.0), (P[0] - 18.0 + flow, hem_y)]
    m = poly_mask([sh_front, sh_back] + back_edge + front_edge[::-1])
    Lc.paint(n_plate(m, 5.0, (-0.2, -0.1), 1.3, fold=lambda x, y: (0.9 * math.sin(y * 0.22 + fi * 0.8 - x * 0.12), 0.2 * math.cos(x * 0.3))), SAND, -2, ao=0)
    Lc.decal([q for q in m if int(q[1] * 0.3 - q[0] * 0.18 + fi * 1.4 + 3 * hash01(q[0] // 3, q[1] // 8, 5)) % 7 == 0], (SAND, 0))
    Lc.decal([q for q in m if int(q[1] * 0.3 - q[0] * 0.18 + fi * 1.4 + 3 * hash01(q[0] // 4, q[1] // 6, 6)) % 11 == 5], (SAND, 5))
    Lc.decal([q for q in m if (q[0] - 1, q[1]) not in m], (SAND, 4))                   # the lit leading edge of every fold
    for j in range(int(70 * k)):
        t = hash01(j, 1, 31)
        base = back_edge[min(n, int(t * n))]
        age = (fi * 0.37 + hash01(j, 2, 31)) % 1.0
        q = ip((base[0] - age * (20 + 14 * k) + math.sin(j + fi) * 1.5, base[1] + age * 8 * (t - 0.3)))
        if K.inb(*q) and q[1] < FL:
            (FXB if j % 3 else FX).put([q], ("z6", "z5", "z4", "z3")[int(age * 4)])
    info["cloak"] = m


def amber_rim(Ls, names, src, radius, cols=("a2", "a1")):
    """Warm rim light thrown by the eye / sun-disc onto the edges of forms that face it."""
    sx, sy = src
    for n in names:
        L = Ls.get(n)
        if not L:
            continue
        pts = []
        for (x, y), e in L.px.items():
            d = math.hypot(x - sx, y - sy)
            if d > radius or d < 1:
                continue
            dx, dy = (sx - x) / d, (sy - y) / d
            nb = (x + (1 if dx > 0.4 else -1 if dx < -0.4 else 0), y + (1 if dy > 0.4 else -1 if dy < -0.4 else 0))
            if nb != (x, y) and nb not in L.px:
                pts.append(((x, y), d))
        for (q, d) in pts:
            if hash01(q[0], q[1], 3) < 0.85:
                L.decal([q], cols[0] if d < radius * 0.5 else cols[1])


# --------------------------------------------------------------------------- the figure
def draw(p0, fi, sw):
    p = conv(p0)
    # a wider, planted stance for the heavier body
    if p["fb"][1] >= FL - 0.5:
        p["fb"] = (p["fb"][0] - 4.0, p["fb"][1])
    if p["ff"][1] >= FL - 0.5:
        p["ff"] = (p["ff"][0] + 4.0, p["ff"][1])
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
    shN, shF = F(8.0, -ln + 6.0), F(-8.5, -ln + 7.0)
    hipN, hipF = F(6.0, 1.0), F(-6.0, 1.0)

    cloak(Ls["Cloak"], FXB, FX, T(F(-15.0, -ln + 2.0)), T(F(2.0, -ln + 0.0)), T(Pp), fi, p["cloak"], sw, p["wind"], info)

    # ---- legs: heavy, wrapped in blackened grave-linen, great greaves of tarnished gold, knee-cops
    kf = leg(R, Ls["NearLeg"], hipN, p["ff"], THIGH, SHIN, 7.4, 5.8, LIN, bias=0, knee=p["kf"], flen=8.0, heel=3.4, boot_h=4.0, pref=(1, -0.15))
    kb = leg(R, Ls["FarLeg"], hipF, p["fb"], THIGH, SHIN, 7.4, 5.8, LIN, bias=-2, knee=p["kb"], flen=8.0, heel=3.4, boot_h=4.0, pref=(1, -0.15))
    for nm, hip, kn, ft, b in (("NearLeg", hipN, kf, p["ff"], 0), ("FarLeg", hipF, kb, p["fb"], -2)):
        L = Ls[nm]
        m = set(L.px)
        bands(L, m, T(hip), T(ft), 3.2, (LIN, 1), phase=0.3)
        bands(L, m, T(hip), T(ft), 7.0, (LIN, 5 if b == 0 else 4), phase=1.9)
        ank = (ft[0], ft[1] - 3.5)
        d = unit(sub(ank, kn))
        nx_ = (-d[1], d[0])
        gr = [add(kn, (d[0] * 4.0 + nx_[0] * 6.4, d[1] * 4.0 + nx_[1] * 6.4)), add(kn, (d[0] * 4.0 - nx_[0] * 5.8, d[1] * 4.0 - nx_[1] * 5.8)),
              add(ank, (-nx_[0] * 4.8 - d[0] * 2.0, -nx_[1] * 4.8 - d[1] * 2.0)), add(ank, (nx_[0] * 5.4 - d[0] * 2.0, nx_[1] * 5.4 - d[1] * 2.0))]
        gm = poly_mask([T(q) for q in gr])
        L.paint(n_plate(gm, 2.2, (-0.35, -0.1), 1.5), GOLD, b, ao=1)
        L.decal(polyline([ip(T(add(kn, (d[0] * 5.0 + nx_[0] * 2.0, d[1] * 5.0 + nx_[1] * 2.0)))), ip(T(add(ank, (-d[0] * 4.0 + nx_[0] * 1.0, -d[1] * 4.0))))]),
                (GOLD, 8 if b == 0 else 6))
        for yy in (0.35, 0.7):
            c_ = T(lerp(add(kn, (d[0] * 4, d[1] * 4)), ank, yy))
            L.decal([q for q in gm if abs((q[0] - c_[0]) * d[0] + (q[1] - c_[1]) * d[1]) < 0.6], (GOLD, 2))
        L.paint(n_dome(T(kn), 4.6, 4.0, tilt=(-0.3, -0.3)), GOLD, b, ao=0)
        L.paint(n_dome(T((ft[0] + 2.0, ft[1] - 1.6)), 3.6, 1.8, tilt=(-0.2, -0.5)), GOLD, b - 1, ao=0)   # sandal plate

    # ---- war kilt: blackened linen under hanging lamellae, a heavy belt with a sun buckle, the glyph apron
    sway = sw * 0.6 - p["wind"] * 0.5
    Sk = Ls["Skirt"]
    sk = [F(-14.0, -3.0), F(14.0, -3.0), add(F(17.0, THIGH + 3.0), (sway * 0.4, 0)), add(F(-16.5, THIGH + 2.0), (sway, 0))]
    skm = R.plate(Sk, sk, LIN, bevel=3.0, tilt=(-0.15, 0), strength=1.2, fold=lambda x, y: (0.8 * math.sin(x * 0.8), 0), bias=0)
    Sk.decal([q for q in skm if (q[0] + (q[1] // 3)) % 4 == 0], (LIN, 1))
    for k_ in range(-5, 6):
        top = F(k_ * 2.4, -2.0)
        bot = add(F(k_ * 2.9, THIGH * 0.6), (sway * 0.3, 0))
        Sk.paint(n_capsule(T(top), T(bot), 1.1, 1.1, 0.9), GOLD, -1 if k_ < -1 else 0, ao=1, clip=skm)
    apron = poly_mask([T(F(2.0, -2.0)), T(F(10.0, -2.0)), T(F(11.5, THIGH + 1.5)), T(F(3.0, THIGH + 1.5))])
    Sk.paint(n_plate(apron, 1.4, (-0.1, 0)), GOLD, -1, ao=1)
    for k_ in range(6):
        y0 = T(F(6.0, 3.0 + k_ * 4.0))[1]
        Sk.decal([q for q in apron if abs(q[1] - y0) < 0.6], (LAP, 2))
    belt = poly_mask([T(F(-14.5, -7.0)), T(F(15.0, -7.0)), T(F(15.0, -2.4)), T(F(-14.5, -2.4))])
    Sk.paint(n_plate(belt, 1.2, (0, -0.3)), GOLD, 0, ao=0)
    Sk.decal([q for q in belt if q[0] % 4 == 0], (LAP, 2))
    sun_disc(Sk, T(F(7.0, -4.6)), 3.0, fi)
    info["skirt"] = skm

    # ---- torso: a deep, heavy chest tapering to the waist (the V), bound in blackened linen; a feathered gold cuirass
    Bd = Ls["Body"]
    torso = [F(-10.5, -0.5), F(-13.5, -ln * 0.42), F(-16.5, -ln + 8.0), F(-14.0, -ln - 2.5), F(12.5, -ln - 2.5), F(18.0, -ln + 6.0),
             F(14.0, -ln * 0.42), F(11.0, -0.5)]
    tm = R.plate(Bd, torso, LIN, bevel=4.2, tilt=(-0.2, -0.05), strength=1.4, bias=0)
    bands(Bd, tm, T(Pp), T(Cc), 3.4, (LIN, 1), phase=0.8)
    Ar = Ls["Armour"]
    cui = [F(-14.0, -ln + 7.0), F(-10.5, -ln + 0.5), F(13.0, -ln + 0.0), F(17.0, -ln + 6.0), F(14.0, -ln * 0.42), F(1.5, -ln * 0.3), F(-12.0, -ln * 0.42)]
    cm = R.plate(Ar, cui, GOLD, bevel=4.0, tilt=(-0.3, -0.2), strength=1.5, bias=-1)
    for row in range(7):                                                                  # rishi feathers: rows of scale arcs
        yy = -ln + 3.0 + row * 3.2
        for col in range(-6, 8):
            cx_ = col * 3.0 + (1.5 if row % 2 else 0)
            arc = [ip(T(F(cx_ + a_ * 1.5, yy + (a_ * a_) * 0.5))) for a_ in (-1, -0.5, 0, 0.5, 1)]
            Ar.decal([q for q in polyline(arc) if q in cm], (GOLD, 2))
    Ar.decal([q for q in cm if (q[0], q[1] - 1) not in cm], (GOLD, 7))
    # winged scarab pectoral
    pc_ = T(F(2.5, -ln + 13.0))
    Ar.paint(n_dome(pc_, 3.4, 2.8, tilt=(-0.2, -0.3)), "c", 0, ao=1)
    for s_ in (-1, 1):
        wg = poly_mask([add(pc_, (s_ * 2.0, -1.0)), add(pc_, (s_ * 9.0, -3.2)), add(pc_, (s_ * 8.0, 0.4)), add(pc_, (s_ * 2.0, 1.4))])
        Ar.paint(n_plate(wg, 0.8, (-0.2, -0.2)), GOLD, 0, ao=0)
        Ar.decal([q for q in wg if q[0] % 2 == 0], (LAP, 3))
    info["torso"] = tm | cm

    # ---- far arm + the was-sceptre
    FA = Ls["FarArm"]
    elF = arm(R, FA, shF, p["hb"], UARM, FARM, 6.0, 5.0, LIN, bias=-2, fist="n", fist_r=3.4, pref=(-1, 0.6), elbow=p["eb"])
    bands(FA, set(FA.px), T(shF), T(p["hb"]), 3.0, (LIN, 0), phase=0.1)
    lames(FA, T(add(shF, (0.0, -1.5))), unit(sub(T(elF), T(shF))), 0.85, -2, n=2)
    if p["sang"] is not None:
        sceptre(Ls["Sceptre"], FX, T(p["hb"]), R.A(p["sang"]), p["su0"], p["su1"], p["glow"], fi, info)

    # ---- the great usekh collar, spanning the shoulders
    Cl = Ls["Collar"]
    cc = F(1.5, -ln + 1.2)
    for rr, mat in ((21.0, GOLD), (18.0, LAP), (15.2, GOLD), (12.4, "r"), (9.8, GOLD), (7.2, LAP)):
        m = {q for q in mask_disc(T(cc), rr, rr * 0.5) if (q[1] - T(cc)[1]) >= -0.5}
        if mat == GOLD:
            Cl.paint(n_dome(T(cc), rr, rr * 0.5, flat=0.7, tilt=(-0.2, -0.3)), GOLD, 0, ao=0, clip=m)
            Cl.decal([q for q in m if q[0] % 3 == 0 and abs(math.hypot((q[0] + .5 - T(cc)[0]) / rr, (q[1] + .5 - T(cc)[1]) / (rr * 0.5)) - 0.9) < 0.1], (GOLD, 2))
        else:
            Cl.paint({q: (0, 0, 1) for q in m}, mat, 0, ao=0)
            Cl.decal([q for q in m if q[0] % 2 == 0], (mat, 3 if mat == LAP else 2))
    Cl.decal([q for q in Cl.px if (q[0], q[1] + 1) not in Cl.px and hash01(q[0], 1, 4) < 0.6], (GOLD, 5))   # bead drops on the hem

    # ---- head: a heavy nemes of dark gold and lapis, the bright death mask as the focal point, one amber eye
    G0 = basis(Hd, p["hup"])
    G = lambda a, b: G0(a * HS, b * HS)
    Hl = Ls["Head"]
    Hl.paint(n_tube([T(F(2.0, -ln - 1.0)), T(G(-0.8, 5.0))], [5.4, 4.6]), LIN, -1)
    nemes = [G(-5.8, -0.6), G(-4.8, -5.2), G(-1.2, -7.4), G(2.8, -6.8), G(4.8, -4.2), G(4.8, -3.0), G(2.0, -3.0), G(1.0, 1.6),
             G(2.2, 4.0), G(3.8, 12.6), G(0.8, 13.6), G(-1.4, 5.6), G(-5.2, 9.4), G(-8.2, 8.2), G(-6.8, 2.6)]
    nm = R.plate(Hl, nemes, GOLD, bevel=3.0, tilt=(-0.25, -0.3), strength=1.4, bias=-1)
    hu = unit(sub(T(G0(0, -1)), T(G0(0, 0))))
    Hl.decal([q for q in nm if int(((q[0] - T(G(0, -8))[0]) * hu[0] + (q[1] - T(G(0, -8))[1]) * hu[1]) * -0.5 + 40) % 3 == 0], (LAP, 2))
    mask_pts = [G(-0.6, -3.6), G(2.8, -4.4), G(4.8, -2.6), G(6.0, -0.2), G(5.8, 2.2), G(4.2, 4.4), G(1.4, 5.2), G(-0.6, 3.6)]
    mm = R.plate(Hl, mask_pts, "g", bevel=2.4, tilt=(-0.3, -0.2), strength=1.5, bias=-1)
    Hl.decal([q for q in mm if any((q[0] + a, q[1] + b) in nm and (q[0] + a, q[1] + b) not in mm for a, b in ((-1, 0), (0, -1), (0, 1)))], (GOLD, 0))
    Hl.decal(polyline([ip(T(G(5.0, -0.6))), ip(T(G(6.4, 1.6))), ip(T(G(5.6, 2.2)))]), ("g", 4))
    Hl.decal(polyline([ip(T(G(4.2, 3.4))), ip(T(G(5.4, 3.2)))]), (GOLD, 1))
    Hl.decal([q for q in mm if q[0] > T(G(3.0, 0))[0] and q[1] > T(G(0, 1.0))[1] and hash01(q[0], q[1], 9) < 0.3], ("g", 2))   # the jaw in shadow
    beard = [G(2.4, 4.8), G(4.0, 4.8), G(3.8, 10.0), G(2.6, 10.4)]
    bm = R.plate(Hl, beard, GOLD, bevel=1.0, tilt=(-0.2, 0), bias=-1)
    Hl.decal([q for q in bm if q[1] % 2 == 0], (LAP, 2))
    sock = poly_mask([T(G(1.4, -2.4)), T(G(5.6, -2.6)), T(G(5.8, 0.2)), T(G(1.6, 0.4))])
    Hl.decal([q for q in sock if q in mm], (GOLD, 0))
    Hl.decal(polyline([ip(T(G(2.0, -1.0))), ip(T(G(5.4, -1.2)))]), ("n", 0))
    info["eye"] = T(G(4.0, -1.1))
    if p["eye"]:
        e0, e1 = ip(T(G(2.2, -1.0))), ip(T(G(5.0, -1.2)))
        FX.put(polyline([e0, e1]), "a4" if p["eye"] >= 2 else "a3")
        FX.put([(q[0], q[1] - 1) for q in polyline([e0, e1])][1:-1], "a2")
        FX.put([e1, (e1[0] - 1, e1[1])], "a5" if p["eye"] >= 2 else "a4")
        FX.put([(e1[0] + 1, e1[1]), (e1[0] + 1, e1[1] - 1)], "a2")
        if p["eye"] >= 2:
            FX.put([(e1[0] + 2, e1[1]), (e1[0] + 3, e1[1]), (e1[0] + 4, e1[1]), (e1[0] + 1, e1[1] + 1), (e1[0] + 2, e1[1] - 1)], "a2")
    if p["crack"] > 0:
        Hl.decal([q for q in polyline([ip(T(G(3.0, -4.4))), ip(T(G(4.2, -0.6))), ip(T(G(2.4, 2.4))), ip(T(G(3.8, 5.0)))]) if q in mm], (GOLD, 0))
    info["head"] = nm | mm

    # ---- crown: the sun-disc between long dark horns, twin plumes, a rearing uraeus
    Cr = Ls["Crown"]
    top = G(-0.8, -7.2)
    for s_, off in ((-1, -1.4), (1, 1.0)):
        pl = [add(top, (off - 1.2, 0.0)), add(top, (off + 1.2, 0.0)), add(top, (off + 0.6 * s_ + 0.4, -22.0)), add(top, (off + 0.6 * s_ - 1.4, -21.0))]
        pm = poly_mask([T(q) for q in pl])
        Cr.paint(n_plate(pm, 1.2, (-0.2, -0.1)), GOLD, -1 if s_ < 0 else -2, ao=0)
        Cr.decal([q for q in pm if q[1] % 3 == 0], (LAP, 2))
    dc = T(add(top, (0.0, -12.5)))
    for s_ in (-1, 1):
        hp = curve([T(add(top, (s_ * 2.0, 1.0))), T(add(top, (s_ * 9.4, -4.0))), T(add(top, (s_ * 11.6, -13.4))), T(add(top, (s_ * 8.8, -21.0))),
                    T(add(top, (s_ * 4.2, -24.0)))], 5)
        Cr.paint(n_tube(hp, [2.6 - 1.9 * i / (len(hp) - 1) for i in range(len(hp))]), "h", 0 if s_ > 0 else -1, ao=0)    # black horn
    Cr.paint(n_tube([T(add(top, (0.0, 1.0))), T(add(top, (0.0, -6.0)))], [1.8, 1.4]), GOLD, -1, ao=0)
    sun_disc(Cr, dc, 7.6, fi, glow=max(1, p["glow"]), FX=FX)
    Cr.decal([q for q in mask_disc(dc, 8.0) if abs(math.hypot(q[0] + .5 - dc[0], q[1] + .5 - dc[1]) - 6.8) < 0.5], (GOLD, 4))
    ur = curve([T(G(3.0, -4.0)), T(G(4.4, -6.6)), T(G(5.8, -7.0))], 3)
    Cr.paint(n_tube(ur, [1.6, 1.5, 1.1]), GOLD, 0, ao=0)
    FX.put([ip(T(G(5.6, -7.0)))], "a3")
    info["crown"] = dc

    # ---- near arm (connected: shoulder lames -> bandaged upper arm -> gold bracer -> fist on the grip) + the khopesh
    if p["kang"] is not None:
        khopesh(Ls["Khopesh"], T(p["hf"]), R.A(p["kang"]), info)
    NA = Ls["NearArm"]
    el = arm(R, NA, shN, p["hf"], UARM, FARM, 6.6, 5.4, LIN, bias=0, fist="n", fist_r=3.6, pref=(-1, 0.7), elbow=p["ef"])
    bands(NA, set(NA.px), T(shN), T(p["hf"]), 3.0, (LIN, 1), phase=0.4)
    fa, fb_ = T(el), T(p["hf"])
    d = unit(sub(fb_, fa))
    br0, br1 = lerp(fa, fb_, 0.38), lerp(fa, fb_, 0.86)
    nx_ = (-d[1], d[0])
    brm = poly_mask([add(br0, (nx_[0] * 5.8, nx_[1] * 5.8)), add(br1, (nx_[0] * 5.0, nx_[1] * 5.0)), add(br1, (-nx_[0] * 5.0, -nx_[1] * 5.0)),
                     add(br0, (-nx_[0] * 5.8, -nx_[1] * 5.8))])
    NA.paint(n_plate(brm, 1.8, (-0.3, -0.2), 1.5), GOLD, 0, ao=1)
    NA.decal([q for q in brm if any((q[0] + a, q[1] + b) not in brm for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) and
              abs((q[0] - br0[0]) * d[0] + (q[1] - br0[1]) * d[1]) < 1.0], (LAP, 3))
    NA.decal([q for q in brm if abs((q[0] - br0[0]) * d[0] + (q[1] - br0[1]) * d[1] - 5.0) < 0.6], (GOLD, 2))
    NA.paint(n_dome(T(el), 4.0, 3.8, tilt=(-0.3, -0.3)), GOLD, -1, ao=0)
    lames(Ls["Pauldron"], T(add(shN, (0.0, -1.8))), unit(sub(T(el), T(shN))), 1.0, 0, n=3)
    info["hand"] = T(p["hf"])
    info["handb"] = T(p["hb"])

    # ---- light: the sun-disc and the eye throw a warm rim onto the forms around them
    amber_rim(Ls, ["Head", "Collar", "Pauldron", "Armour", "Crown"], dc, 40)
    amber_rim(Ls, ["Head", "Pauldron", "Collar"], info["eye"], 16, ("a3", "a2"))

    # ---- FX
    if p["smear"]:
        for (g0, a0, g1, a1) in p["smear"]:
            info["hit"] |= swept(FX, T(g0), R.A(a0), T(g1), R.A(a1), 18, 35, hw=1.8, pal="khopesh_d", taper=0.6)
    if p["glint"]:
        glint(FX, p["glint"], big=True)
    if p["shock"]:
        cx = info["tip"][0] if "tip" in info else Pp[0] + 30
        for k_ in range(30):
            a = -math.pi * (0.05 + 0.9 * hash01(k_, fi, 9))
            rr = 4 + 20 * hash01(k_, fi + 2, 9)
            FX.put([ip((cx + math.cos(a) * rr * 1.4, FL - 1 + math.sin(a) * rr))], ("a4", "g4", "z6", "z5")[k_ % 4])
    if p["sink"] > 0:
        dy = int(round(p["sink"] * 138))
        for L in Ls.values():
            if isinstance(L, Layer):
                L.px = {(q[0], q[1] + dy): e_ for q, e_ in L.px.items() if q[1] + dy < FL - 1}
        for F_ in (FX, FXB):
            F_.px = {(q[0], q[1] + dy): c for q, c in F_.px.items() if q[1] + dy < FL - 1}
        info["hit"] = {(q[0], q[1] + dy) for q in info["hit"] if q[1] + dy < FL - 1}
        info["eye"] = (info["eye"][0], info["eye"][1] + dy)
        info["tip"] = (info["tip"][0], info["tip"][1] + dy) if "tip" in info else None
    if p["spray"]:
        for k_ in range(48):
            a = -math.pi * (0.06 + 0.88 * hash01(k_, fi, 7))
            rr = 5 + 38 * hash01(k_, fi + 1, 7) * p["spray"]
            FX.put([ip((Pp[0] + 8 + math.cos(a) * rr * 1.2, FL - 1 + math.sin(a) * rr))], ("z7", "z6", "z5", "z4")[k_ % 4])
        for x in range(int(Pp[0] - 30), int(Pp[0] + 42)):
            h = int(2 + 5 * max(0.0, 1 - abs(x - Pp[0] - 6) / 36))
            for y in range(FL - h, FL + 1):
                FX.put([(x, y)], "z6" if y == FL - h else "z5")
    if p["dust"]:
        for k_ in range(20):
            FX.put([(int(Pp[0] + (hash01(k_, fi, 3) - 0.5) * 64), FL - int(hash01(k_, fi, 4) * 6))], ("z6", "z5", "z4")[k_ % 3])
    return Ls, info


# =========================================================================== animations (authored in v1 space; FL there = OFL)
ST = dict(P=(70.0, 84.0), C=(72.0, 55.0), Hd=(75.4, 42.0), hup=(0.18, -1.0), fb=(62.0, OFL), ff=(80.0, OFL))


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
                           ff=(71.0 + 10.0 * c, OFL - max(0, s) * 3.0), fb=(69.0 - 10.0 * c, OFL - max(0, -s) * 3.0),
                           hf=(84.0 + 1.2 * c, 84.0 + bob), kang=62 + 4 * c, hb=(60.0 - 1.4 * c, 80.0 + bob), wind=-1.0)))
    return fr


CROSS = dict(P=(70.0, 84.0), C=(71.0, 55.2), Hd=(72.6, 43.6), hup=(0.05, -1.0), fb=(66.0, OFL), ff=(76.0, OFL),
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


def a_beam():
    """Sceptre raised forward-high, the disc gathers light (0-5); the beam fires (6-10) as the sceptre sweeps down; recover."""
    brace = dict(P=(67.0, 85.0), C=(66.0, 56.4), Hd=(68.6, 43.6), hup=(-0.05, -1.0), fb=(54.0, OFL), ff=(80.0, OFL))
    fire = dict(P=(70.0, 85.0), C=(72.0, 56.0), Hd=(76.0, 43.2), hup=(0.3, -1.0), fb=(56.0, OFL), ff=(84.0, OFL))
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
    up = dict(P=(69.0, 84.0), C=(69.6, 55.0), Hd=(72.4, 42.4), hup=(0.05, -1.0), fb=(58.0, OFL), ff=(80.0, OFL))
    down = dict(P=(72.0, 88.0), C=(78.0, 61.0), Hd=(83.0, 50.0), hup=(0.8, -1.0), fb=(58.0, OFL), ff=(86.0, OFL))
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
    spread = dict(P=(70.0, 84.0), C=(70.4, 54.6), Hd=(72.6, 41.6), hup=(-0.1, -1.0), fb=(58.0, OFL), ff=(82.0, OFL))
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
    lift = dict(P=(69.0, 84.0), C=(69.0, 55.0), Hd=(71.6, 42.2), hup=(-0.05, -1.0), fb=(58.0, OFL), ff=(80.0, OFL))
    fling = dict(P=(73.0, 85.0), C=(78.0, 57.0), Hd=(83.0, 45.0), hup=(0.6, -1.0), fb=(60.0, OFL), ff=(88.0, OFL))
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
    up = dict(P=(72.0, 84.0), C=(75.0, 55.0), Hd=(79.0, 42.6), hup=(0.3, -1.0), fb=(62.0, OFL), ff=(86.0, OFL))
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
    rock = dict(P=(66.0, 85.0), C=(62.0, 58.0), Hd=(62.0, 46.0), hup=(-0.5, -1.0), fb=(58.0, OFL), ff=(78.0, OFL))
    slump = dict(P=(68.0, 90.0), C=(74.0, 64.0), Hd=(80.0, 54.0), hup=(0.9, -0.9), fb=(56.0, OFL), ff=(80.0, OFL))
    return [(90, PS(**rock, hf=(76.0, 60.0), kang=-120, hb=(52.0, 64.0), sang=-120, eye=1)),
            (140, PS(**slump, hf=(86.0, 100.0), kang=70, hb=(62.0, 96.0), sang=-80, su0=-30, su1=40, eye=1)),
            (300, PS(**slump, hf=(86.0, 102.0), kang=72, hb=(62.0, 98.0), sang=-80, su0=-30, su1=40, eye=1)),
            (300, PS(**dict(slump, C=(74.4, 64.6), Hd=(80.6, 54.8)), hf=(86.0, 103.0), kang=74, hb=(62.0, 99.0), sang=-80, su0=-30, su1=40, eye=1))]


def a_death():
    kneel = dict(P=(68.0, 99.0), C=(74.0, 72.0), Hd=(80.0, 61.0), hup=(0.8, -1.0), kf=(84.0, 104.0), ff=(82.0, OFL), kb=(62.0, 121.0),
                 fb=(44.0, OFL), hf=(92.0, 114.0), kang=90, hb=(58.0, 106.0), sang=-86, su0=-18, su1=50)
    names = [n for n in LAYERS if n not in NOOUT]
    pal = ("a3", "g4", "z6", "z5", "z4")
    fr = [(110, PS(P=(66.0, 85.0), C=(61.0, 58.0), Hd=(60.0, 46.0), hup=(-0.6, -1.0), fb=(58.0, OFL), ff=(78.0, OFL), hf=(78.0, 60.0), kang=-120,
                   hb=(50.0, 62.0), sang=-120, eye=2)),
          (200, PS(P=(67.0, 92.0), C=(70.0, 64.0), Hd=(74.0, 52.0), hup=(0.4, -1.0), kf=(80.0, 98.0), kb=(60.0, 110.0), fb=(52.0, OFL), ff=(84.0, OFL),
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




def a_combo():
    """Four khopesh cuts: rising diagonal (3-4), backhand upswing (7-8), overhead slam (11-12), a spinning low sweep (16-17)."""
    wind1 = dict(P=(68.0, 85.0), C=(67.0, 56.4), Hd=(69.6, 43.8), hup=(-0.05, -1.0), fb=(58.0, OFL), ff=(78.0, OFL))
    cut1 = dict(P=(74.0, 85.4), C=(80.0, 57.6), Hd=(85.0, 45.4), hup=(0.55, -1.0), fb=(60.0, OFL), ff=(90.0, OFL))
    wind2 = dict(P=(73.0, 85.4), C=(76.0, 57.0), Hd=(80.4, 44.6), hup=(0.4, -1.0), fb=(60.0, OFL), ff=(88.0, OFL))
    over = dict(P=(72.0, 84.0), C=(72.4, 55.0), Hd=(75.0, 42.2), hup=(0.05, -1.0), fb=(60.0, OFL), ff=(86.0, OFL))
    slam = dict(P=(78.0, 88.0), C=(86.0, 62.0), Hd=(92.0, 51.0), hup=(0.9, -1.0), fb=(62.0, OFL), ff=(96.0, OFL))
    low = dict(P=(76.0, 90.0), C=(80.0, 62.0), Hd=(85.0, 50.0), hup=(0.5, -1.0), fb=(62.0, OFL), ff=(94.0, OFL))
    return [
        (100, PS(**wind1, hf=(78.0, 70.0), kang=-100, hb=(58.0, 78.0))),
        (140, PS(**wind1, hf=(70.0, 60.0), kang=-150, hb=(56.0, 76.0), eye=2)),
        (150, PS(**wind1, hf=(66.0, 56.0), kang=-165, hb=(55.0, 76.0), eye=2, glint=(56.0, 36.0))),
        (60, PS(**cut1, hf=(102.0, 74.0), kang=-10, hb=(64.0, 80.0), eye=2, smear=[((66.0, 56.0), -165, (102.0, 74.0), -10)], dust=1)),
        (70, PS(**cut1, hf=(100.0, 86.0), kang=40, hb=(64.0, 82.0), eye=2, smear=[((102.0, 74.0), -10, (100.0, 86.0), 40)])),
        (90, PS(**cut1, hf=(96.0, 90.0), kang=70, hb=(64.0, 82.0))),
        (120, PS(**wind2, hf=(90.0, 94.0), kang=150, hb=(64.0, 82.0), eye=2, glint=(80.0, 112.0))),
        (60, PS(**cut1, hf=(104.0, 64.0), kang=-60, hb=(66.0, 80.0), eye=2, smear=[((90.0, 94.0), 150, (104.0, 64.0), -60)])),
        (70, PS(**cut1, hf=(96.0, 52.0), kang=-110, hb=(66.0, 78.0), eye=2, smear=[((104.0, 64.0), -60, (96.0, 52.0), -110)])),
        (130, PS(**over, hf=(80.0, 36.0), kang=-165, hb=(62.0, 76.0), eye=2)),
        (170, PS(**over, hf=(76.0, 32.0), kang=-175, hb=(62.0, 76.0), eye=2, glint=(70.0, 18.0), glow=1)),
        (60, PS(**slam, hf=(108.0, 86.0), kang=30, hb=(70.0, 84.0), eye=2, smear=[((76.0, 32.0), -175, (108.0, 86.0), 30)], dust=1)),
        (80, PS(**slam, hf=(110.0, 96.0), kang=62, hb=(70.0, 86.0), eye=2, smear=[((108.0, 86.0), 30, (110.0, 96.0), 62)], dust=1, shock=1)),
        (120, PS(**slam, hf=(106.0, 100.0), kang=70, hb=(70.0, 86.0))),
        (120, PS(**low, hf=(70.0, 96.0), kang=178, hb=(62.0, 88.0), eye=2)),
        (150, PS(**low, hf=(64.0, 98.0), kang=185, hb=(60.0, 88.0), eye=2, glint=(46.0, 104.0))),
        (60, PS(**low, hf=(98.0, 100.0), kang=8, hb=(66.0, 88.0), eye=2, smear=[((64.0, 98.0), 185, (98.0, 100.0), 8)], dust=1)),
        (70, PS(**low, hf=(106.0, 94.0), kang=-20, hb=(66.0, 88.0), eye=2, smear=[((98.0, 100.0), 8, (106.0, 94.0), -20)])),
        (180, PS(**low, hf=(102.0, 92.0), kang=-10, hb=(66.0, 86.0))),
        (200, PS(P=(72.0, 85.0), C=(76.0, 56.4), Hd=(80.0, 43.8), hup=(0.4, -1.0), ff=(88.0, OFL), hf=(90.0, 86.0), kang=66)),
    ]


def a_lunge():
    """A crouching wind-up, then a lunging hooked thrust across the sand (engine drives him forward on 4-6)."""
    crouch = dict(P=(64.0, 90.0), C=(62.0, 63.0), Hd=(64.0, 50.0), hup=(0.0, -1.0), fb=(50.0, OFL), ff=(76.0, OFL))
    lunge = dict(P=(80.0, 90.0), C=(90.0, 64.0), Hd=(97.0, 53.0), hup=(1.0, -0.9), fb=(58.0, OFL), ff=(102.0, OFL))
    return [
        (110, PS(**crouch, hf=(70.0, 80.0), kang=170, hb=(56.0, 84.0))),
        (150, PS(**crouch, hf=(62.0, 82.0), kang=178, hb=(52.0, 86.0), eye=2)),
        (160, PS(**crouch, hf=(58.0, 82.0), kang=180, hb=(50.0, 86.0), eye=2, glint=(40.0, 78.0))),
        (120, PS(**crouch, hf=(56.0, 82.0), kang=182, hb=(50.0, 86.0), eye=2, cloak=1.4, wind=-3.0)),
        (60, PS(**lunge, hf=(116.0, 80.0), kang=-6, hb=(70.0, 82.0), eye=2, wind=5.0, dust=1, smear=[((56.0, 82.0), 182, (116.0, 80.0), -6)])),
        (70, PS(**lunge, hf=(120.0, 84.0), kang=10, hb=(72.0, 82.0), eye=2, wind=5.0, dust=1, smear=[((116.0, 80.0), -6, (120.0, 84.0), 10)])),
        (80, PS(**lunge, hf=(118.0, 90.0), kang=30, hb=(72.0, 84.0), eye=2, wind=3.0, dust=1)),
        (130, PS(**lunge, hf=(114.0, 94.0), kang=48, hb=(70.0, 84.0))),
        (140, PS(P=(76.0, 88.0), C=(82.0, 60.0), Hd=(88.0, 47.0), hup=(0.6, -1.0), fb=(60.0, OFL), ff=(94.0, OFL), hf=(100.0, 90.0), kang=56)),
        (140, PS(P=(73.0, 86.0), C=(76.0, 57.0), Hd=(80.0, 44.4), hup=(0.4, -1.0), ff=(88.0, OFL), hf=(92.0, 86.0), kang=60)),
        (140, PS(hf=(86.0, 85.0))),
        (150, PS()),
    ]


def a_slam():
    """The was-sceptre heaved overhead in both hands and driven into the sand (8: shockwaves + erupting sand spikes)."""
    lift = dict(P=(68.0, 84.0), C=(67.4, 55.0), Hd=(69.0, 42.6), hup=(-0.2, -1.0), fb=(56.0, OFL), ff=(80.0, OFL))
    down = dict(P=(76.0, 90.0), C=(86.0, 66.0), Hd=(93.0, 56.0), hup=(1.0, -0.8), fb=(58.0, OFL), ff=(94.0, OFL))
    return [
        (110, PS(**lift, hb=(66.0, 64.0), sang=-120, su0=-40, su1=36, hf=(76.0, 66.0), kang=-60)),
        (130, PS(**lift, hb=(64.0, 48.0), sang=-150, su0=-40, su1=40, hf=(70.0, 50.0), kang=-100, eye=2)),
        (140, PS(**lift, hb=(60.0, 38.0), sang=-160, su0=-36, su1=40, hf=(66.0, 40.0), kang=-130, eye=2, glow=1)),
        (160, PS(**lift, hb=(58.0, 34.0), sang=-150, su0=-34, su1=40, hf=(64.0, 36.0), kang=-140, eye=2, glow=2, glint=(34.0, 18.0))),
        (160, PS(**lift, hb=(56.0, 34.0), sang=-152, su0=-34, su1=40, hf=(62.0, 36.0), kang=-145, eye=2, glow=2)),
        (90, PS(**lift, hb=(56.0, 36.0), sang=-156, su0=-34, su1=40, hf=(62.0, 38.0), kang=-145, eye=2, glow=3, cloak=1.4)),
        (60, PS(**down, hb=(90.0, 56.0), sang=60, su0=-40, su1=40, hf=(96.0, 60.0), kang=-40, eye=2, glow=3, wind=4.0)),
        (60, PS(**down, hb=(98.0, 78.0), sang=75, su0=-40, su1=44, hf=(104.0, 80.0), kang=0, eye=2, glow=3, spray=1.0, dust=1, shock=1)),
        (120, PS(**down, hb=(98.0, 80.0), sang=76, su0=-40, su1=44, hf=(104.0, 82.0), kang=10, eye=2, glow=2, spray=0.7, dust=1, shock=1)),
        (160, PS(**down, hb=(98.0, 80.0), sang=76, su0=-40, su1=44, hf=(104.0, 84.0), kang=20, glow=1, spray=0.3)),
        (140, PS(P=(74.0, 88.0), C=(80.0, 60.0), Hd=(86.0, 48.0), hup=(0.6, -1.0), fb=(58.0, OFL), ff=(90.0, OFL), hb=(84.0, 76.0), sang=-60, su0=-40,
                 su1=40, hf=(96.0, 84.0), kang=40)),
        (140, PS(P=(72.0, 86.0), C=(75.0, 57.0), Hd=(79.0, 44.4), hup=(0.4, -1.0), hb=(66.0, 78.0), sang=-86, su0=-42, su1=40, hf=(88.0, 84.0), kang=56)),
        (140, PS(hb=(62.0, 80.0))),
        (150, PS()),
    ]


def a_command():
    """The khopesh lifted to the sky, the eye flares: the sun-skulls answer (spawn at 5)."""
    up = dict(P=(70.0, 84.0), C=(71.4, 54.6), Hd=(74.0, 41.6), hup=(0.05, -1.0), fb=(58.0, OFL), ff=(82.0, OFL))
    return [
        (110, PS(**up, hf=(88.0, 60.0), kang=-70, hb=(58.0, 78.0))),
        (130, PS(**up, hf=(90.0, 40.0), kang=-100, hb=(56.0, 76.0), eye=2)),
        (140, PS(**up, hf=(88.0, 26.0), kang=-92, hb=(56.0, 76.0), eye=2, glow=1, glint=(90.0, 2.0))),
        (140, PS(**up, hf=(88.0, 24.0), kang=-90, hb=(56.0, 76.0), eye=2, glow=2, cloak=1.4, wind=-2.0)),
        (140, PS(**up, hf=(88.0, 24.0), kang=-90, hb=(56.0, 76.0), eye=2, glow=3, cloak=1.6, wind=-3.0)),
        (160, PS(**up, hf=(88.0, 24.0), kang=-88, hb=(56.0, 76.0), eye=2, glow=3, cloak=1.7, wind=-3.0)),
        (200, PS(**up, hf=(88.0, 26.0), kang=-88, hb=(56.0, 76.0), eye=2, glow=2, cloak=1.5, wind=-2.0)),
        (150, PS(**up, hf=(90.0, 50.0), kang=-40, hb=(58.0, 78.0), glow=1)),
        (140, PS(hf=(86.0, 76.0), kang=40)),
        (150, PS()),
    ]


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("rise", a_rise), ("stagger", a_stagger), ("combo", a_combo), ("lunge", a_lunge), ("slam", a_slam),
           ("beam", a_beam), ("coffin", a_coffin), ("summon", a_summon), ("disc", a_disc), ("command", a_command), ("vanish", a_vanish),
           ("emerge", a_emerge), ("death", a_death)]
SHEETS = {"pharaoh_a": ("idle", "walk"), "pharaoh_b": ("rise", "stagger"), "pharaoh_c": ("combo",), "pharaoh_d": ("lunge",), "pharaoh_e": ("slam",),
          "pharaoh_f": ("beam",), "pharaoh_g": ("coffin",), "pharaoh_h": ("summon",), "pharaoh_i": ("disc", "command"),
          "pharaoh_j": ("vanish", "emerge"), "pharaoh_k": ("death",)}
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
        "hurtbox": [tb[0] + 3, tb[1] + 2, tb[2] - 6, H - tb[1] - 2],
        "sheets": {t: s for s, ts in SHEETS.items() for t in ts},
        "attacks": {
            "combo": {"windows": [{"active": [3, 4], "hit": hit(infos, "combo", [3, 4], AX)},
                                  {"active": [7, 8], "hit": hit(infos, "combo", [7, 8], AX)},
                                  {"active": [11, 12], "hit": hit(infos, "combo", [11, 12], AX)},
                                  {"active": [16, 17], "hit": hit(infos, "combo", [16, 17], AX - 30)}]},
            "lunge": {"active": [4, 6], "hit": hit(infos, "lunge", [4, 6], AX)},
            "slam": {"active": [7, 8], "hit": hit(infos, "slam", [7, 8], AX)},
            "emerge": {"active": [4, 5], "hit": hit(infos, "emerge", [4, 5], AX - 10)},
        },
        "telegraph": {"combo": {"frame": 1, "at": pt(M((56.0, 36.0)))}, "lunge": {"frame": 1, "at": pt(M((40.0, 78.0)))},
                      "slam": {"frame": 2, "at": pt(M((34.0, 18.0)))}, "emerge": {"frame": 2, "at": pt(M((96.0, 110.0)))}},
        "events": {"beam_on": 6, "beam_off": 10, "coffin": 6, "summon": 7, "disc": 7, "command": 5, "slam": 7},
        "spawn": {"tip": {"frames": {t: [pt(i.get("tip")) for i in infos[t]] for t in infos}}},
        "eye": {t: [pt(i.get("eye")) for i in infos[t]] for t in infos},
        "notes": "v2 god-king. combo = four khopesh cuts (3-4, 7-8, 11-12 overhead slam, 16-17 spinning low sweep that also reaches "
                 "behind). lunge = hooked thrust, the engine drives him forward on 4-6. slam = the was-sceptre driven into the sand at 7 "
                 "(engine: shockwaves + sand spikes). command = khopesh raised, the sun-skull blasters appear at 5. beam: disc gathers light "
                 "(0-5), beam fires 6-10 from spawn.tip. coffin at 6, summon at 7, disc thrown at 7. vanish/emerge: into and out of the "
                 "storm (emerge cut 4-5). rise = intro (frame 0 = the dormant sarcophagus pose). eye = per-frame eye-slit point.",
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
