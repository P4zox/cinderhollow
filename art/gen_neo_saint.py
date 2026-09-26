#!/usr/bin/env python3
"""SAINT-0, the Null Saint (agent NH) -- the secret main boss of NEO-HALLOW.

    python3 art/gen_neo_saint.py [--preview]

saint0       112x144, faces right, hovers: anchor = the tip of its tail [56, 143].  ~125 px tall.
saint0_wire  the same frames as a navy wireframe on transparent (phase 3, the inverted cyberspace arena).

A towering, sleek white-and-chrome AI angel: a small faceless egg helm with one glowing visor band and a swept crest
fin, a slender ceramic cuirass traced with cyan circuitry and a magenta core, long jointed arms, and instead of legs a
long tail of overlapping chrome plates that tapers to a point.  Its six wings of floating holographic panels, its halo of
data rings and its energy lance are drawn live by the engine from the per-frame meta points exported here
(meta.frames[tag][i] = {g: lance grip, a: lance angle (deg, native facing), l: lance length, h: head, b: back, c: core}).
ONE rig for every frame: all proportions (head, torso, arms, tail) are constants; only the pose changes.

Tags: idle(8) glide(6) thrust(12, active 6-8) sweep(12, active 5-7) cast(10, spawn f5) wings(8, spawn f4)
      delete(10, spawn f4) stagger(4) death(12)
"""
import math, os, sys
import neo_kit  # noqa: F401
from neo_kit import K, E3, Layer, FXLayer, Rig, lerp, ip, line, poly_mask, n_plate, n_dome, n_capsule, n_tube, madd, disc_glow, halo_dots, circuit
from enemy_kit import hash01, ik
from PIL import Image

BUILD = "--preview" not in sys.argv
ART = os.path.dirname(os.path.abspath(__file__))
E3.BUILD = BUILD
TAGS = dict(idle=8, glide=6, thrust=12, sweep=12, cast=10, wings=8, delete=10, stagger=4, death=12)
E3.SPEC_FRAMES["saint0"] = dict(TAGS)
LAYERS = ["FarArm", "Tail", "Body", "Head", "NearArm", "FX"]
FW, FH = 112, 144
TIP_Y = 143.0
# rig constants (model space, upright)
WAIST = (56.0, 72.0)
CHEST_UP = 27.0          # waist -> chest length
NECK = 9.0
UPPER, FORE = 17.0, 16.0  # arm segment lengths (constant: no proportion drift)
TAIL_LEN = 70.0

NEU = dict(lean=0.0, dy=0.0, sway=0.0, swirl=0.0, nh=(72.0, 72.0), fh=(50.0, 84.0), a=-78.0, l=74.0, tilt=0.0,
           glow=1.0, core=1.0, dead=0.0, spark=0, fi=0, wire=False, reach=0.0)


def P_(**kw):
    d = dict(NEU); d.update(kw); return d


def rotp(p, piv, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y = p[0] - piv[0], p[1] - piv[1]
    return (piv[0] + x * c - y * s, piv[1] + x * s + y * c)


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX"); Ls["FX"] = FX
    info = {"hit": set()}
    dy = p["dy"]
    W_ = (WAIST[0], WAIST[1] + dy)
    lean = p["lean"]
    up = (math.sin(math.radians(lean)), -math.cos(math.radians(lean)))    # torso axis
    fw = (-up[1], up[0])                                                   # torso "forward" (right when upright)
    C_ = madd(W_, (up, CHEST_UP))
    Hd = madd(C_, (up, NECK + 7.0), (fw, 2.0 + p["tilt"] * 0.1))
    # ---------------- the tail: overlapping chrome plates tapering to the tip (hovering: tip on the anchor row)
    T = Ls["Tail"]
    sway, swirl = p["sway"], p["swirl"]
    pts = []
    for i in range(15):
        t = i / 14
        x = W_[0] + math.sin(t * 2.6 + swirl) * sway * t - t * 2.0
        y = W_[1] + t * (TIP_Y - W_[1])
        pts.append((x, y))
    # three long tapered chrome blades (a closed-wing robe): the centre one reaches the tip, the side ones stop short
    def blade(off, reach, w0, bias, edge):
        n = int(14 * reach)
        L_, R_ = [], []
        for i in range(n + 1):
            t = i / 14
            q = pts[i]
            w = w0 * (1 - (i / n)) ** 0.75 + 0.3
            cx = q[0] + off * (1 - t * 0.6)
            L_.append((cx - w, q[1])); R_.append((cx + w, q[1]))
        tipq = (pts[n][0] + off * (1 - n / 14 * 0.6), pts[n][1] + 4.0)
        poly = L_ + [tipq] + R_[::-1]
        c0 = pts[0][0] + off
        m_ = poly_mask(poly)
        T.paint(n_plate(m_, 2.0, (0.0, 0.05), 1.0, fold=lambda x, y: (-(x + 0.5 - (c0 - 1.5 * (y - pts[0][1]) / 70 * 0)) / (w0 * 1.6), 0.1)), "S", bias, ao=1)
        T.decal([q for q in line(L_[1], L_[-1]) if q in T.px], edge)
        return m_
    blade(-6.5, 0.72, 6.0, -1, "S2")
    blade(6.5, 0.78, 6.0, -1, "S2")
    blade(0.0, 1.0, 8.0, 0, "S4")
    circuit(T, [madd(pp, ((1, 0), 1.5)) for pp in pts[1:13]], "X2")
    info["tip"] = pts[-1]
    # ---------------- far arm (behind the body)
    shF = madd(C_, (up, -3.0), (fw, -6.0))
    elF = ik(shF, p["fh"], UPPER, FORE, (-0.6, 0.8))
    FA = Ls["FarArm"]
    FA.paint(n_tube([shF, elF], [3.2, 2.5]), "S", -1)
    FA.paint(n_tube([elF, p["fh"]], [2.6, 2.0]), "S", -1)
    FA.paint(n_dome(elF, 1.9, 1.9), "U", -1, ao=0)
    FA.paint(n_dome(p["fh"], 2.2, 2.0), "S", -1, ao=0)
    circuit(FA, [elF, lerp(elF, p["fh"], 0.8)], "X1")
    # ---------------- torso: narrow waist, ceramic cuirass, pauldrons, spine
    B = Ls["Body"]
    B.paint(n_tube([madd(W_, (up, -3.0)), madd(W_, (up, 8.0))], [4.0, 3.6]), "S", -2)
    # hip faulds: a flared skirt of plates that seats the tail into the waist
    fa = [madd(W_, (fw, -7.0), (up, 1.0)), madd(W_, (fw, 7.5), (up, 1.0)), madd(W_, (fw, 9.0), (up, -5.0)), madd(W_, (fw, 1.0), (up, -8.0)), madd(W_, (fw, -8.0), (up, -5.0))]
    B.paint(n_plate(poly_mask(fa), 2.5, (0.0, 0.0), 1.1, fold=lambda x, y: (-(x + 0.5 - W_[0]) / 13.0, 0.2)), "S", -1, ao=1)
    cuirass = [madd(W_, (fw, -3.2), (up, 2.0)), madd(W_, (fw, 3.8), (up, 2.0)), madd(C_, (fw, 5.0), (up, -9.0)), madd(C_, (fw, 10.0), (up, 1.0)),
               madd(C_, (fw, 9.0), (up, 5.0)), madd(C_, (fw, 3.0), (up, 7.0)), madd(C_, (fw, -7.0), (up, 6.5)), madd(C_, (fw, -10.0), (up, 2.0)), madd(C_, (fw, -5.0), (up, -9.0))]
    B.paint(n_plate(poly_mask(cuirass), 3.2, (-0.05, -0.1), 1.15, fold=lambda x, y: (-(x + 0.5 - C_[0] - 1.0) / 12.0, 0.0)), "S", 0)
    # pectoral plate: a brighter, raised ceramic shell over the upper chest
    pec = [madd(C_, (fw, -6.0), (up, 5.5)), madd(C_, (fw, 3.0), (up, 6.0)), madd(C_, (fw, 8.5), (up, 3.5)), madd(C_, (fw, 8.0), (up, -2.5)), madd(C_, (fw, 2.0), (up, -5.0)), madd(C_, (fw, -5.0), (up, -2.0))]
    B.paint(n_plate(poly_mask(pec), 2.2, (-0.1, -0.2), 1.3, fold=lambda x, y: (-(x + 0.5 - C_[0] - 1.5) / 10.0, 0.0)), "S", 1, ao=1)
    # abdominal plates
    for k in range(3):
        a0 = madd(W_, (up, 6.0 + k * 3.2))
        B.decal([q for q in line(madd(a0, (fw, -4.0)), madd(a0, (fw, 5.5))) if q in B.px], "S3")
    # circuit traces + the core
    circuit(B, [madd(C_, (fw, 1.0), (up, -8.0)), madd(C_, (fw, 3.0), (up, -2.0)), madd(C_, (fw, 3.0), (up, 3.0)), madd(C_, (fw, -2.0), (up, 5.0))], "X2")
    circuit(B, [madd(C_, (fw, 3.0), (up, -2.0)), madd(C_, (fw, 7.0), (up, 1.0))], "X2")
    core = madd(C_, (fw, 3.0), (up, -1.0))
    cq = ip(core)
    B.fixed({cq: "T3", (cq[0] + 1, cq[1]): "T2", (cq[0], cq[1] - 1): "T2", (cq[0] - 1, cq[1]): "T1", (cq[0], cq[1] + 1): "T1"})
    if p["core"] > 0.5: FX.put([cq], "T4")
    # pauldrons: small, smooth, swept back
    for side, b in ((-1, -1), (1, 0)):
        sh = madd(C_, (up, 3.0), (fw, 7.5 * side))
        B.paint(n_dome(madd(sh, (fw, -0.5)), 4.2, 3.4, 1.0, (-0.2, -0.3)), "S", b, ao=0)
        B.decal([ip(madd(sh, (fw, -3.0), (up, 1.0)))], "X2")
    # ---------------- neck + head: faceless egg helm, a visor band, a swept crest fin
    Hh = Ls["Head"]
    Hh.paint(n_tube([madd(C_, (up, 5.0)), madd(Hd, (up, -4.0))], [1.6, 1.4]), "U", -1)
    Hh.paint(n_dome(Hd, 5.2, 6.8, 1.0, (-0.2, -0.15)), "S", 0)
    fin = [madd(Hd, (up, 4.0), (fw, -2.0)), madd(Hd, (up, 6.0), (fw, -4.0)), madd(Hd, (up, 7.0), (fw, -13.0)), madd(Hd, (up, 1.5), (fw, -6.0))]
    Hh.paint(n_plate(poly_mask(fin), 0.8, (-0.3, -0.6), 1.2), "S", 0, ao=0)
    vis = [ip(madd(Hd, (fw, x), (up, 0.5))) for x in (-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0)]
    Hh.fixed({q: ("X2" if i == 0 else "X3") for i, q in enumerate(vis)})
    Hh.fixed({ip(madd(Hd, (fw, x), (up, 1.5))): "X2" for x in (1.0, 2.0, 3.0, 4.0)})
    Hh.fixed({ip(madd(Hd, (fw, x), (up, -0.5))): "T2" for x in (1.0, 2.0, 3.0, 4.0)})
    if p["glow"] > 0.5: FX.put(vis[2:6], "X4")
    # ---------------- near arm (in front): holds the lance
    shN = madd(C_, (up, 2.0), (fw, 6.5))
    elN = ik(shN, p["nh"], UPPER, FORE, (-0.2, 1))
    NA = Ls["NearArm"]
    NA.paint(n_tube([shN, elN], [3.3, 2.6]), "S", 0)
    NA.paint(n_tube([elN, p["nh"]], [2.8, 2.1]), "S", 0)
    NA.paint(n_dome(elN, 2.0, 2.0), "U", 0, ao=0)
    NA.paint(n_capsule(lerp(elN, p["nh"], 0.35), lerp(elN, p["nh"], 0.8), 2.6, 2.3), "S", 1, ao=0)   # vambrace
    NA.paint(n_dome(p["nh"], 2.4, 2.2), "S", 0, ao=0)
    circuit(NA, [shN, lerp(shN, elN, 0.8)], "X1")
    # ---------------- fx: sparks / dissolve
    if p["spark"]:
        for k in range(8):
            FX.put([(int(C_[0] + (hash01(k, fi, 3) - 0.5) * 30), int(C_[1] + (hash01(fi, k, 4) - 0.5) * 50))], ["X4", "T3", "S6", "X3"][k % 4])
    if p["dead"]:
        for L in Ls.values():
            if isinstance(L, Layer):
                for q in list(L.px):
                    if hash01(q[0], q[1] // 2, 7) < p["dead"] * 0.9 - (q[1] / FH) * 0.3: L.erase([q])
        for k in range(int(p["dead"] * 40)):
            FX.put([(int(40 + hash01(k, fi, 5) * 36), int(10 + hash01(fi, k, 6) * 120))], ["X3", "T3", "S6", "X2"][k % 4])
    info["g"] = p["nh"]; info["h"] = Hd; info["b"] = madd(C_, (fw, -4.0), (up, 1.0)); info["c"] = core
    return Ls, info


def lerp_pose(a, b, t):
    out = {}
    for k in a:
        va, vb = a[k], b.get(k, a[k])
        if isinstance(va, tuple): out[k] = (va[0] + (vb[0] - va[0]) * t, va[1] + (vb[1] - va[1]) * t)
        elif isinstance(va, (int, float)) and not isinstance(va, bool): out[k] = va + (vb - va) * t
        else: out[k] = vb if t > 0.5 else va
    return out


def anims():
    I = []
    for k in range(8):
        s = math.sin(k / 8 * 2 * math.pi)
        I.append((130, P_(dy=s * 1.5, sway=2.0 + s * 1.5, swirl=k / 8 * 6.283, nh=(72.0, 72.0 + s * 1.5), fh=(50.0, 84.0 + s * 1.2), a=-78.0, l=74.0)))
    G = []
    for k in range(6):
        s = math.sin(k / 6 * 2 * math.pi)
        G.append((100, P_(lean=12.0, dy=2.0, sway=-7.0 + s * 1.5, swirl=k, nh=(68.0, 68.0), fh=(38.0, 66.0 + s), a=165.0 + s * 3, l=66.0)))
    base = P_(dy=0.0, sway=2.0, nh=(72.0, 72.0), fh=(50.0, 84.0), a=-78.0, l=74.0)
    th = [
        (110, P_(lean=-3, nh=(64.0, 64.0), fh=(42.0, 70.0), a=-20.0, l=72.0, sway=3.0)),
        (110, P_(lean=-6, nh=(54.0, 58.0), fh=(40.0, 64.0), a=-4.0, l=76.0, sway=5.0)),
        (110, P_(lean=-8, nh=(48.0, 56.0), fh=(40.0, 60.0), a=0.0, l=80.0, sway=6.0)),
        (120, P_(lean=-9, nh=(46.0, 55.0), fh=(40.0, 58.0), a=0.0, l=82.0, sway=7.0)),
        (170, P_(lean=-9, nh=(46.0, 55.0), fh=(40.0, 58.0), a=0.0, l=82.0, sway=7.0, glow=1.0)),
        (110, P_(lean=-9, nh=(46.0, 55.0), fh=(40.0, 58.0), a=0.0, l=82.0, sway=7.0)),
        (60, P_(lean=10, nh=(80.0, 55.0), fh=(34.0, 62.0), a=0.0, l=96.0, sway=-6.0)),
        (70, P_(lean=14, nh=(86.0, 56.0), fh=(32.0, 64.0), a=1.0, l=100.0, sway=-8.0)),
        (80, P_(lean=14, nh=(86.0, 57.0), fh=(32.0, 64.0), a=2.0, l=100.0, sway=-8.0)),
        (130, P_(lean=10, nh=(80.0, 60.0), fh=(36.0, 66.0), a=8.0, l=90.0, sway=-5.0)),
        (130, P_(lean=5, nh=(76.0, 66.0), fh=(40.0, 70.0), a=-30.0, l=80.0, sway=-2.0)),
        (130, lerp_pose(P_(lean=5, nh=(76.0, 66.0), fh=(40.0, 70.0), a=-30.0, l=80.0), base, 0.6)),
    ]
    sw = [
        (110, P_(lean=-3, nh=(66.0, 60.0), fh=(44.0, 70.0), a=-100.0, l=76.0)),
        (110, P_(lean=-6, nh=(62.0, 48.0), fh=(44.0, 66.0), a=-120.0, l=78.0, sway=4.0)),
        (110, P_(lean=-8, nh=(58.0, 40.0), fh=(44.0, 62.0), a=-135.0, l=80.0, sway=5.0)),
        (120, P_(lean=-9, nh=(56.0, 38.0), fh=(44.0, 60.0), a=-142.0, l=80.0, sway=6.0)),
        (150, P_(lean=-9, nh=(56.0, 38.0), fh=(44.0, 60.0), a=-142.0, l=80.0, sway=6.0)),
        (60, P_(lean=4, nh=(72.0, 42.0), fh=(40.0, 64.0), a=-60.0, l=84.0, sway=-2.0)),
        (60, P_(lean=10, nh=(80.0, 52.0), fh=(36.0, 64.0), a=10.0, l=86.0, sway=-6.0)),
        (70, P_(lean=12, nh=(80.0, 64.0), fh=(36.0, 66.0), a=50.0, l=86.0, sway=-7.0)),
        (130, P_(lean=10, nh=(78.0, 68.0), fh=(38.0, 68.0), a=62.0, l=82.0, sway=-6.0)),
        (130, P_(lean=6, nh=(76.0, 70.0), fh=(40.0, 72.0), a=30.0, l=78.0, sway=-3.0)),
        (130, P_(lean=3, nh=(74.0, 72.0), fh=(42.0, 74.0), a=-30.0, l=76.0, sway=0.0)),
        (130, lerp_pose(P_(lean=3, nh=(74.0, 72.0), fh=(42.0, 74.0), a=-30.0, l=76.0), base, 0.6)),
    ]
    ca = [
        (110, P_(nh=(70.0, 62.0), fh=(46.0, 66.0), a=-84.0, l=76.0)),
        (110, P_(lean=-2, nh=(68.0, 48.0), fh=(46.0, 54.0), a=-88.0, l=78.0)),
        (110, P_(lean=-4, nh=(66.0, 38.0), fh=(46.0, 42.0), a=-90.0, l=80.0, dy=-2.0)),
        (110, P_(lean=-5, nh=(65.0, 32.0), fh=(46.0, 34.0), a=-90.0, l=82.0, dy=-3.0)),
        (120, P_(lean=-5, nh=(65.0, 30.0), fh=(45.0, 30.0), a=-90.0, l=84.0, dy=-4.0, spark=1)),
        (150, P_(lean=-6, nh=(65.0, 29.0), fh=(44.0, 29.0), a=-90.0, l=86.0, dy=-4.0, spark=1)),
        (150, P_(lean=-6, nh=(65.0, 29.0), fh=(44.0, 29.0), a=-90.0, l=86.0, dy=-4.0)),
        (130, P_(lean=-5, nh=(65.0, 31.0), fh=(45.0, 32.0), a=-90.0, l=84.0, dy=-3.0)),
        (120, P_(lean=-2, nh=(68.0, 50.0), fh=(45.0, 56.0), a=-86.0, l=78.0, dy=-1.0)),
        (120, P_(nh=(71.0, 66.0), fh=(44.0, 70.0), a=-80.0, l=75.0)),
    ]
    wi = [
        (110, P_(nh=(76.0, 66.0), fh=(40.0, 68.0), a=-60.0, l=74.0)),
        (110, P_(lean=-2, nh=(82.0, 58.0), fh=(34.0, 60.0), a=-30.0, l=74.0, dy=-1.0)),
        (110, P_(lean=-4, nh=(86.0, 52.0), fh=(29.0, 52.0), a=-10.0, l=76.0, dy=-2.0)),
        (140, P_(lean=-5, nh=(88.0, 50.0), fh=(27.0, 48.0), a=0.0, l=76.0, dy=-3.0, spark=1)),
        (160, P_(lean=-5, nh=(88.0, 49.0), fh=(27.0, 47.0), a=0.0, l=76.0, dy=-3.0, spark=1)),
        (140, P_(lean=-4, nh=(86.0, 51.0), fh=(29.0, 50.0), a=-6.0, l=76.0, dy=-2.0)),
        (120, P_(lean=-2, nh=(80.0, 60.0), fh=(36.0, 62.0), a=-40.0, l=75.0, dy=-1.0)),
        (120, P_(nh=(73.0, 70.0), fh=(42.0, 73.0), a=-72.0, l=74.0)),
    ]
    de = [
        (110, P_(nh=(70.0, 72.0), fh=(50.0, 66.0), a=-80.0, l=74.0)),
        (110, P_(lean=2, nh=(69.0, 72.0), fh=(62.0, 58.0), a=-80.0, l=74.0)),
        (110, P_(lean=4, nh=(68.0, 72.0), fh=(76.0, 52.0), a=-80.0, l=74.0)),
        (130, P_(lean=6, nh=(68.0, 72.0), fh=(84.0, 50.0), a=-80.0, l=74.0, spark=1)),
        (150, P_(lean=7, nh=(68.0, 72.0), fh=(86.0, 49.0), a=-80.0, l=74.0, spark=1)),
        (150, P_(lean=7, nh=(68.0, 72.0), fh=(86.0, 49.0), a=-80.0, l=74.0)),
        (140, P_(lean=7, nh=(68.0, 72.0), fh=(86.0, 50.0), a=-80.0, l=74.0)),
        (120, P_(lean=5, nh=(69.0, 72.0), fh=(76.0, 56.0), a=-80.0, l=74.0)),
        (120, P_(lean=2, nh=(70.0, 72.0), fh=(60.0, 66.0), a=-79.0, l=74.0)),
        (120, P_(nh=(72.0, 72.0), fh=(46.0, 75.0), a=-78.0, l=74.0)),
    ]
    st = [
        (90, P_(lean=-12, dy=4.0, tilt=-10, nh=(66.0, 82.0), fh=(40.0, 84.0), a=100.0, l=70.0, glow=0.0, spark=1, sway=6.0)),
        (120, P_(lean=-16, dy=7.0, tilt=-14, nh=(64.0, 88.0), fh=(40.0, 88.0), a=110.0, l=70.0, glow=0.0, spark=1, sway=8.0)),
        (220, P_(lean=-16, dy=8.0, tilt=-16, nh=(64.0, 90.0), fh=(40.0, 90.0), a=112.0, l=70.0, glow=0.0, sway=8.0)),
        (200, P_(lean=-10, dy=5.0, tilt=-8, nh=(66.0, 84.0), fh=(42.0, 84.0), a=100.0, l=70.0, glow=1.0, sway=5.0)),
    ]
    dth = []
    for k in range(12):
        t = k / 11
        dth.append((110 if k < 11 else 500, P_(lean=-10 - t * 14, dy=4.0 + t * 12, tilt=-12 - t * 10, nh=(66.0 - t * 4, 82.0 + t * 20), fh=(40.0, 86.0 + t * 16),
                                              a=100.0 + t * 30, l=70.0, glow=1.0 if k % 3 == 0 and k < 6 else 0.0, spark=1 if k < 8 else 0, sway=8.0 - t * 4,
                                              core=1.0 if k < 5 else 0.0, dead=max(0.0, (t - 0.25) / 0.75))))
    return [("idle", I), ("glide", G), ("thrust", th), ("sweep", sw), ("cast", ca), ("wings", wi), ("delete", de), ("stagger", st), ("death", dth)]


def wire_frame(im):
    """The phase-3 wireframe: silhouette + internal contours in navy, the visor/core in magenta, a few scan dots."""
    w, h = im.size; src = im.load(); out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); o = out.load()
    def lum(c): return (c[0] * 3 + c[1] * 6 + c[2]) / 10
    for y in range(h):
        for x in range(w):
            c = src[x, y]
            if c[3] == 0: continue
            edge = any(not (0 <= x + a < w and 0 <= y + b < h) or src[x + a, y + b][3] == 0 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            glow = (c[0] > 200 and c[2] > 150 and c[1] < 160) or (c[2] > 200 and c[1] > 180 and c[0] < 120)
            if edge: o[x, y] = (11, 16, 48, 255)
            elif glow: o[x, y] = (255, 63, 192, 255)
            elif any(0 <= x + a < w and 0 <= y + b < h and src[x + a, y + b][3] and abs(lum(src[x + a, y + b]) - lum(c)) > 70 for a, b in ((1, 0), (0, 1))):
                o[x, y] = (44, 58, 154, 255)
            elif y % 4 == 0 and x % 2 == 0: o[x, y] = (150, 165, 215, 255)
    return out


def build():
    K.setup(FW, FH)
    spec = anims()
    out, infos = [], {}
    for tag, frames in spec:
        lst, inf = [], []
        for k, (ms, p) in enumerate(frames):
            Ls, info = draw(p, k, 0)
            imgs = {n: (K.render_layer(v) if isinstance(v, Layer) else v.image()) for n, v in Ls.items()}
            lst.append((ms, imgs)); inf.append((info, p))
        out.append((tag, lst)); infos[tag] = inf
    fr_meta = {}
    for tag, inf in infos.items():
        fr_meta[tag] = [{"g": [round(i["g"][0], 1), round(i["g"][1], 1)], "a": p["a"], "l": p["l"], "h": [round(i["h"][0], 1), round(i["h"][1], 1)],
                         "b": [round(i["b"][0], 1), round(i["b"][1], 1)], "c": [round(i["c"][0], 1), round(i["c"][1], 1)]} for i, p in inf]
    meta = {"native": 1, "anchor": [56, 143], "hurtbox": [42, 18, 30, 110],
            "attacks": {"thrust": {"active": [6, 8]}, "sweep": {"active": [5, 7]}},
            "spawn": {"cast": {"frame": 5, "at": [56, 20]}, "wings": {"frame": 4, "at": [48, 44]}, "delete": {"frame": 4, "at": [86, 49]}},
            "telegraph": {"thrust": {"frame": 4}, "sweep": {"frame": 3}},
            "frames": fr_meta}
    tags, flats = K.export("saint0", LAYERS, out, None, build=BUILD)
    import json
    with open(os.path.join(ART, "..", "assets", "saint0_meta.json"), "w") as fh:
        json.dump(meta, fh)
    # wire sheet: one flattened layer
    wires = [(ms, {"Wire": wire_frame(K.flatten(imgs, LAYERS))}) for tag, lst in out for ms, imgs in lst]
    wanims, i = [], 0
    for tag, lst in out:
        wanims.append((tag, wires[i:i + len(lst)])); i += len(lst)
    K.export("saint0_wire", ["Wire"], wanims, None, build=BUILD)
    # preview with the live-drawn lance so poses can be judged
    prev = Image.new("RGBA", (9 * (FW + 4), len(spec) * (FH + 4)), (40, 40, 52, 255))
    fi = 0
    for r, (tag, lst) in enumerate(out):
        for c, (ms, imgs) in enumerate(lst[:9]):
            fr = K.flatten(imgs, LAYERS).copy()
            m = fr_meta[tag][c]; a = math.radians(m["a"]); gx, gy = m["g"]
            for s in range(-22, int(m["l"])):
                x, y = int(gx + math.cos(a) * s), int(gy + math.sin(a) * s)
                if 0 <= x < FW and 0 <= y < FH: fr.putpixel((x, y), (184, 246, 255, 255) if s > 0 else (70, 85, 122, 255))
            prev.alpha_composite(fr, (c * (FW + 4), r * (FH + 4)))
    prev = prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST)
    prev.save(os.path.join(ART, "previews", "saint0_lance.png"))


if __name__ == "__main__":
    build()
