#!/usr/bin/env python3
"""Boss generator -- "Astrel, the Fallen Star" (agent SF, Starfall Crater).  v2: heroic proportions.

    python3 art/gen_starfall_astrel.py              full build (both phases) + meta + previews
    python3 art/gen_starfall_astrel.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_starfall_astrel.py --only combo,thrust --preview

A celestial knight-queen: obsidian-glass plate with starlight in its cracks, broad layered pauldrons, a heavy mantle of
night sky, a sleek helm crowned with swept star-glass spines over a faceless silver mask, nebula hair streaming from under
the helm, a halo of orbiting star shards and a long curved starlight sword.
Proportions (fixed for every frame): ~7 heads tall (~67 px), head 11 px, shoulders 17 px across the pauldrons, waist 8,
thigh 17 / shin 17.2, upper arm 12 / forearm 11.5, blade 46. Poses are keyed in a compact reference space and mapped
through tf() (scale 1.12 about the pelvis) so the whole move set shares one skeleton; hands/feet are clamped to reach.
Frame 144x120, faces RIGHT, feet on the bottom row, anchor x = 66.

Sheets (all share assets/astrel_meta.json):
    astrel   : idle walk dash counter riposte stagger kneel getup
    astrel_b : combo thrust upslash flurry
    astrel_c : leap cast nova death wave
    astrel2* : the same frames for phase 2 (cracks blaze, the halo widens, the mantle burns with stars)
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, leg, arm, swept, thrust_lines, dirv)

W, H = 144, 120
K.setup(W, H)
FLOOR = H - 1
AX = 66
BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

EXTRA = {
    # obsidian glass plate (wider value range so the armour reads at 1x)
    "Z0": "#07070f", "Z1": "#11132a", "Z2": "#1d2244", "Z3": "#2e3766", "Z4": "#48578f", "Z5": "#7f95d8", "Z6": "#c0d0ff",
    # silver (mask, trims)
    "J0": "#1c1e2c", "J1": "#3a3e52", "J2": "#656c84", "J3": "#9ca4ba", "J4": "#d4dae6", "J5": "#f6f8fc",
    # nebula hair / mantle lining
    "H0": "#100820", "H1": "#1e1040", "H2": "#321a64", "H3": "#4c2a8c", "H4": "#7448b8", "H5": "#a67ee0",
    # starlight blade
    "E0": "#16244e", "E1": "#2c4892", "E2": "#5e84d8", "E3": "#a4c2f6", "E4": "#e2ecff",
    # night cloth (mantle)
    "U0": "#07070e", "U1": "#0e0f1e", "U2": "#171a32", "U3": "#232848", "U4": "#343b64",
    # starlight glow (fixed)
    "X0": "#1a2a66", "X1": "#3a5ac4", "X2": "#7a9cf2", "X3": "#c6d8ff", "X4": "#ffffff",
}
for k_, v_ in EXTRA.items():
    K.HEX[k_] = v_
    K.RGBA[k_] = tuple(int(v_[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k_[0], []).append(k_)
K.SHINY["Z"] = 0.9
K.SHINY["J"] = 0.86
K.SMEAR["star"] = ["X4", "X3", "X2", "X1"]
K.SMEAR["star2"] = ["X4", "X4", "X3", "X2"]

LAYERS = ["FXBack", "CapeBack", "Hair", "BackArm", "BackLeg", "Body", "FrontLeg", "Tasset", "Head", "Weapon", "FrontArm", "FX"]
FXL = {"FXBack", "FX"}

# ---------------------------------------------------------------- reference space -> frame (one skeleton for every pose)
SC = 1.12
REF_P, NEW_P = (60.0, 57.0), (66.0, 85.4)
REF_FLOOR = 87


def tf(q):
    return (NEW_P[0] + (q[0] - REF_P[0]) * SC, NEW_P[1] + (q[1] - REF_P[1]) * SC)


L_TH, L_SH = 15.2 * SC, 15.4 * SC
L_UA, L_FA = 10.7 * SC, 10.3 * SC
BLADE = 46.0
NEU = dict(P=(60.0, 57.0), C=(61.5, 42.0), Hd=(63.0, 32.6), ff=(67.0, REF_FLOOR), fb=(53.0, REF_FLOOR),
           hf=(69.0, 54.0), hb=None, wang=25.0, two=False, kf=None, kb=None, hair=0.0, skirt=0.0, lift=0.0,
           halo=1.0, glow=0.0, smear=None, thrust=None, dissolve=0.0, burst=0.0, rot=0.0, piv=(60, 60),
           hup=(0.05, -1.0), sparkle=0.0)
PTS = ("P", "C", "Hd", "fb", "ff", "hf", "hb", "kf", "kb")


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def shift(p, dx, dy):
    q = dict(p)
    for k in PTS:
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] + dy)
    return q


def reach(s, h, L):
    d = math.hypot(h[0] - s[0], h[1] - s[1])
    if d <= L - 0.3:
        return h
    k = (L - 0.3) / d
    return (s[0] + (h[0] - s[0]) * k, s[1] + (h[1] - s[1]) * k)


# ---------------------------------------------------------------- the curved starlight sword
def sword(grip, ang, glow, phase):
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    n = (-math.sin(a), math.cos(a))
    bend = -1.0
    pix, blade = {}, set()
    lit = -(n[0] * K.LIGHT[0] + n[1] * K.LIGHT[1])
    u, tip = 0.0, grip
    while u <= BLADE:
        t = u / BLADE
        off = bend * 5.2 * t * t
        c = (grip[0] + d[0] * u + n[0] * off, grip[1] + d[1] * u + n[1] * off)
        tx, ty = d[0] + n[0] * bend * 10.4 * t / BLADE, d[1] + n[1] * bend * 10.4 * t / BLADE
        tl = math.hypot(tx, ty)
        nn = (-ty / tl, tx / tl)
        taper = 1.0 if t < 0.8 else max(0.0, (1 - t) / 0.2) ** 0.9
        we, ws = 1.75 * taper + 0.15, 1.2 * taper + 0.1
        v = -ws
        while v <= we:
            q = ip((c[0] + nn[0] * v, c[1] + nn[1] * v))
            side = v if lit > 0 else -v
            if v > we * 0.5:
                col = "E4" if side > 0 else "E3"
            elif v < -ws * 0.5:
                col = "E1" if side < 0 else "E2"
            else:
                col = "X3" if (glow > 0.5 or phase == 2) and int(u) % 6 != 0 else "E2"
            if q not in pix or col in ("E4", "X3"):
                pix[q] = col
            blade.add(q)
            v += 0.45
        tip = c
        u += 0.3
    for k in range(-7, 8):                               # guard: a crescent of silver
        q = ip((grip[0] + n[0] * k * 0.55 - d[0] * (0.5 + abs(k) * 0.14), grip[1] + n[1] * k * 0.55 - d[1] * (0.5 + abs(k) * 0.14)))
        pix[q] = "J4" if k < 0 else "J2"
    for i in range(1, 15):                               # grip + star pommel
        uu = -i * 0.5
        for w in (-0.5, 0.5):
            q = ip((grip[0] + d[0] * uu + n[0] * w, grip[1] + d[1] * uu + n[1] * w))
            pix[q] = "U3" if i % 3 else "J2"
    pq = ip((grip[0] - d[0] * 8.2, grip[1] - d[1] * 8.2))
    pix[pq] = "X4"
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pix[(pq[0] + dx, pq[1] + dy)] = "X2"
    return pix, blade, tip


# ---------------------------------------------------------------- one frame
def draw(p0, fi, phase):
    p = dict(p0)
    for k in PTS:
        if p.get(k) is not None:
            p[k] = tf(p[k])
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    R = Rig(p["rot"], tf(p["piv"]))
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    G = basis(Hd, p["hup"])
    info = {"hit": set()}
    p2 = phase == 2
    sw, hs, lift = p["skirt"], p["hair"], p["lift"] * SC

    shF, shB = F(2.6, -ln + 2.2), F(-2.8, -ln + 2.6)
    hipF, hipB = F(2.2, 0.6), F(-2.2, 0.6)

    # ---------------- weapon (front hand, clamped to reach)
    hf = reach(shF, p["hf"], L_UA + L_FA)
    grip, wang = hf, p["wang"]
    pix, blade, tip = sword(R.T(grip), R.A(wang), p["glow"], phase)
    pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
    Ls["Weapon"].fixed(pix)
    info["hit"] |= {q for q in blade if q[1] <= FLOOR}
    info["tip"], info["grip"] = tip, R.T(grip)
    d_ = dirv(R.A(wang))
    hb = p["hb"]
    if p["two"]:
        hb = (grip[0] - d_[0] * 4.2, grip[1] - d_[1] * 4.2)
    if hb is None:
        hb = F(-5.5, -3.5)
    hb = reach(shB, hb, L_UA + L_FA)

    # ---------------- halo of star shards behind the head
    hc = G(-1.4, -2.2)
    hr = (13.0 if not p2 else 15.5) * p["halo"]
    nfr = 9 if not p2 else 12
    ph = p.get("halo_ph", 0.0)
    if p["halo"] > 0.05:
        for k in range(64):
            if k % 3 == 0:
                a = k / 64 * 2 * math.pi
                FXB.put([ip(R.T((hc[0] + math.cos(a) * hr, hc[1] + math.sin(a) * hr)))], "X0" if not p2 else "X1")
        for k in range(nfr):
            a = ph + k / nfr * 2 * math.pi
            q = ip(R.T((hc[0] + math.cos(a) * hr, hc[1] + math.sin(a) * hr)))
            FXB.put([q], "X4")
            FXB.put([(q[0] + 1, q[1]), (q[0], q[1] + 1)], "X2")
            if k % 3 == 0:
                FXB.put([(q[0] - 1, q[1]), (q[0], q[1] - 1), (q[0] + 1, q[1] + 1)], "X3")
                FXB.put([(q[0], q[1] - 2), (q[0], q[1] + 2), (q[0] - 2, q[1]), (q[0] + 2, q[1])], "X1")

    # ---------------- the mantle: a heavy fall of night sky from both shoulders
    Cb = Ls["CapeBack"]
    top = F(-1.0, -ln + 0.8)
    hemy = min(FLOOR - 6, P[1] + 23 - lift * 0.3)
    back_x = P[0] - 15 + sw * 2.0 - abs(lift) * 0.3
    pts = [add(top, (4.6, -1.8)), add(shB, (-2.8, 0.6)),
           (P[0] - 8.5 + sw * 0.6, P[1] - 4), (back_x - 2, hemy - 8 + abs(sw) * 0.4)]
    n = 8
    hem = []
    for i in range(n + 1):
        t = i / n
        x = lerp((back_x, hemy), (P[0] - 1.5 + sw * 0.4, hemy - 3), t)[0]
        y = hemy - 3 * t + (2.6 if i % 2 else 0.2) * (0.7 + 0.3 * hash01(i, fi // 3, 5))
        hem.append((x, y))
    pts += hem + [(P[0] - 1.0, P[1] - 2), F(-1.5, -ln + 4)]
    cm = R.mask(pts)
    Cb.paint(n_plate(cm, 2.6, (0.25, 0.05), 1.0, fold=lambda x, y: (0.8 * math.sin((x - P[0]) * 0.55 + y * 0.06 + sw * 0.8), 0)), "U", bias=0, ao=0)
    for q in cm:                                          # the night inside the cloth
        hv = hash01(q[0], q[1], 61 + fi // 4)
        if hv < (0.03 if not p2 else 0.055):
            Cb.decal([q], "X4" if hv < 0.01 else "X2")
    edge = [q for q in cm if (q[0] + 1, q[1]) not in cm and q[1] > top[1] + 4]
    Cb.decal(edge, ("H", 3))                               # violet lining catching light along the inner edge
    hemq = [q for q in cm if (q[0], q[1] + 1) not in cm]
    Cb.decal(hemq[::2], "X1" if not p2 else "X2")

    # ---------------- hair: nebula streaming from under the helm
    Hr = Ls["Hair"]
    root = G(-3.8, 1.2)
    hp_ = bezier(root, add(root, (-5.5 + hs * 0.2, 5.0)), add(root, (-9.0 + hs * 0.9, 16.0 - abs(hs) * 0.4)),
                 add(root, (-15.0 + hs * 1.8, 26.0 - abs(hs) * 1.0 - lift * 0.5)), n=18)
    for i in range(len(hp_) - 1):
        t0, t1 = i / (len(hp_) - 1), (i + 1) / (len(hp_) - 1)
        R.cap(Hr, hp_[i], hp_[i + 1], 3.8 - 2.9 * t0 ** 0.8, 3.8 - 2.9 * t1 ** 0.8, "H", bias=0 if i < 6 else -1, ao=0)
    for k in range(3):
        sp = [add(q, (0.3 * k - 0.4, -1.2 + k * 1.1)) for q in hp_[1:15 - k * 3]]
        Hr.decal(polyline([R.T(q) for q in sp]), ("H", 4 if k != 1 else 3))
    for i, q in enumerate(hp_[3:]):
        if hash01(i, fi, 71) < (0.3 if not p2 else 0.55):
            FX.put([ip(R.T(add(q, (hash01(i, 1, fi) * 4 - 2, hash01(i, 2, fi) * 4 - 2))))], "X3" if hash01(i, 3, fi) < 0.6 else "X4")
    for i in range(5 + (4 if p2 else 0)):
        q = add(hp_[-1], (-hash01(i, fi, 72) * 6 - 1, hash01(i, fi, 73) * 6 - 2))
        FXB.put([ip(R.T(q))], "X2" if i % 2 else "H5")

    # ---------------- back arm + pauldron
    arm(R, Ls["BackArm"], shB, hb, L_UA, L_FA, 2.5, 2.2, "Z", bias=-1, fist="Z", fist_r=2.2, fore="Z", pref=(-1, 0.6))
    R.dome(Ls["BackArm"], add(shB, (-0.4, -0.4)), 4.4, 3.8, "Z", bias=-1)
    R.dome(Ls["BackArm"], add(shB, (-0.8, 2.6)), 3.4, 2.6, "Z", bias=-1)

    # ---------------- legs: greaves, knee cops, pointed sabatons
    for nm, hip, ft, bias, kn in (("BackLeg", hipB, p["fb"], -1, p["kb"]), ("FrontLeg", hipF, p["ff"], 0, p["kf"])):
        ftc = reach(hip, (ft[0], ft[1] - 1.4), L_TH + L_SH)
        ftc = (ftc[0], ftc[1] + 1.4)
        k = leg(R, Ls[nm], hip, ftc, L_TH, L_SH, 3.2, 2.5, "Z", bias=bias, flen=5.4, heel=1.8, boot_h=3.2, knee=kn, boot=None)
        R.dome(Ls[nm], add(k, (0.8, 0.0)), 2.5, 2.3, "Z", bias=bias)
        R.decal(Ls[nm], [add(k, (1.4, -0.4)), add(k, (1.0, -0.8))], ("J", 3 + bias))
        a_ = lerp(k, (ftc[0], ftc[1] - 2), 0.18)
        b_ = lerp(k, (ftc[0], ftc[1] - 2), 0.72)
        R.dline(Ls[nm], add(a_, (1.3, 0)), add(b_, (1.0, 0)), ("Z", 6 if bias == 0 else 4))      # greave gloss
        R.dline(Ls[nm], add(a_, (-0.4, 2)), add(b_, (-0.2, -2)), ("X", 3 if (p2 or bias == 0) else 2))
        info["knee_" + nm] = k

    # ---------------- cuirass: broad chest, tapered waist, silver girdle and collar
    Bd = Ls["Body"]
    torso = [F(-5.0, 1.2), F(-3.4, -5.2), F(-5.2, -ln + 4.2), F(-4.6, -ln - 0.2), F(3.2, -ln - 1.0), F(5.8, -ln + 3.2),
             F(5.0, -ln + 8.0), F(3.3, -5.4), F(4.8, 1.2)]
    tm = R.plate(Bd, torso, "Z", bevel=2.6, tilt=(-0.3, -0.18), strength=1.25)
    info["torso"] = tm
    R.dline(Bd, F(4.8, -ln + 2.4), F(3.8, -ln + 7.0), ("Z", 6))                   # gloss on the breastplate
    R.dline(Bd, F(-4.6, -ln + 3.6), F(-3.0, -5.6), ("Z", 1))                      # shadowed back line
    R.dline(Bd, F(-3.4, -5.3), F(3.4, -5.5), ("J", 3))                           # silver girdle
    R.dline(Bd, F(-3.6, -4.4), F(3.6, -4.6), ("J", 1))
    R.decal(Bd, [F(0.4, -5.4), F(1.0, -5.4)], "X3")
    crack = [F(1.6, -ln + 1.0), F(0.4, -ln + 4.0), F(2.0, -ln + 6.8), F(0.8, -7.0), F(1.8, -2.4)]
    for a, b in zip(crack, crack[1:]):
        R.dline(Bd, a, b, ("X", 3))
    if p2:
        R.dline(Bd, F(2.0, -ln + 6.8), F(4.4, -ln + 8.6), ("X", 4))
        R.dline(Bd, F(0.4, -ln + 4.0), F(-2.8, -ln + 5.6), ("X", 3))
        R.dline(Bd, F(0.8, -7.0), F(-2.0, -6.0), ("X", 3))
    R.decal(Bd, [F(0.8, -ln + 5.4)], ("X", 4))
    R.cap(Bd, F(0.2, -ln - 0.6), add(Hd, (-0.6, 5.4)), 2.2, 1.9, "J", bias=-1)   # silver gorget

    # ---------------- tassets: glass plates over the hips (front) and a back fauld
    Ts = Ls["Tasset"]
    for (ox, L_, w_, bias) in ((2.6, 11.0, 3.4, 0), (-1.2, 9.0, 3.0, -1)):
        tt = F(ox, 0.4)
        th = add(tt, (1.4 - sw * 0.6 + ox * 0.15, L_ - lift * 0.12))
        R.plate(Ts, [add(tt, (-w_, -1.2)), add(tt, (w_, -1.4)), add(th, (w_ * 0.55, 0)), add(th, (-w_ * 0.4, 1.0))], "Z",
                bevel=1.2, tilt=(-0.35, 0.0), bias=bias)
        R.dline(Ts, add(tt, (w_ * 0.5, 0.0)), add(th, (w_ * 0.3, -1.0)), ("Z", 5 + bias))
        R.dline(Ts, add(tt, (-w_ + 0.6, -0.6)), add(tt, (w_ - 0.6, -0.8)), ("J", 3 + bias))

    # ---------------- head: sleek helm, star-glass crest, faceless silver mask, starlit circlet
    Hl = Ls["Head"]
    helm = [G(-5.4, 3.6), G(-5.6, -2.4), G(-3.4, -5.8), G(0.4, -6.6), G(3.2, -5.4), G(1.2, 5.2), G(-2.8, 5.6)]
    R.plate(Hl, helm, "Z", bevel=2.0, tilt=(-0.35, -0.35), strength=1.3)
    for (bx, by, ex, ey, w_) in ((-5.0, -2.6, -13.5, -2.6, 0.9), (-3.6, -4.6, -15.0, -6.4, 1.0), (-1.8, -5.8, -15.5, -10.4, 1.1), (0.4, -6.4, -12.5, -13.6, 1.25)):
        b0, e0 = G(bx, by), G(ex, ey)
        R.plate(Hl, [add(b0, (-w_, w_)), add(b0, (w_, -w_)), e0], "Z", bevel=0.8, tilt=(-0.5, -0.4), bias=0)
        R.dline(Hl, lerp(b0, e0, 0.2), lerp(b0, e0, 0.92), ("X", 3 if not p2 else 4))
    mask = [G(-0.6, -5.2), G(2.4, -5.0), G(4.8, -2.2), G(5.4, 1.2), G(4.6, 4.2), G(2.2, 6.0), G(-0.4, 5.6), G(-1.4, 0.8)]
    mm = R.plate(Hl, mask, "J", bevel=2.4, tilt=(-0.1, -0.1), strength=1.3, bias=0)
    info["head"] = mm
    R.dline(Hl, G(0.8, -4.8), G(4.0, -3.0), ("J", 4))
    R.decal(Hl, [G(2.0, -4.4)], ("J", 5))
    R.dline(Hl, G(5.0, -1.0), G(4.4, 3.2), ("J", 2))                            # the mask's quiet profile ridge
    R.dline(Hl, G(1.6, -1.6), G(4.6, -1.8), ("J", 1))                           # a brow shadow, no eyes
    R.dline(Hl, G(-1.4, -4.8), G(-1.8, 4.6), ("Z", 0))                          # where the helm meets the mask
    R.dline(Hl, G(-4.8, -3.6), G(2.2, -5.6), ("X", 3 if not p2 else 4))         # circlet
    R.decal(Hl, [G(0.4, -5.6)], ("X", 4))

    # ---------------- front arm + layered pauldron (over the grip)
    arm(R, Ls["FrontArm"], shF, hf, L_UA, L_FA, 2.5, 2.2, "Z", bias=0, fist="Z", fist_r=2.3, fore="Z", pref=(-1, 0.6))
    R.dome(Ls["FrontArm"], add(shF, (0.4, -0.8)), 4.8, 4.0, "Z", bias=0)
    R.dome(Ls["FrontArm"], add(shF, (0.8, 2.4)), 3.8, 2.8, "Z", bias=0)
    R.dline(Ls["FrontArm"], add(shF, (-3.2, -2.6)), add(shF, (3.6, -1.6)), ("J", 3))
    R.dline(Ls["FrontArm"], add(shF, (-1.6, -3.0)), add(shF, (2.6, 1.4)), ("X", 3 if not p2 else 4))
    R.decal(Ls["FrontArm"], [add(hf, (0.6, -1.0))], ("J", 4))

    # ---------------- smear / thrust / glow / motes
    if p["smear"]:
        g0, a0, st = p["smear"]
        hot = swept(FX, R.T(tf(g0)), R.A(a0), R.T(grip), R.A(wang), BLADE * 0.55, BLADE + 1.0, hw=0.9, start=st, taper=0.85,
                    pal="star2" if p2 else "star", clip_y=FLOOR)
        info["hit"] |= hot
    if p["thrust"]:
        info["hit"] |= thrust_lines(FX, R.T(grip), R.A(wang), 8, BLADE + 10, (-3.5, -1.5, 1.5, 3.5), pal="star", flash=BLADE + 3)
    if p["glow"] > 0:
        tq = ip(tip)
        r = 2 + int(p["glow"] * 3)
        for dx in range(-r, r + 1):
            FX.put([(tq[0] + dx, tq[1])], "X3" if abs(dx) < r - 1 else "X1")
        for dy in range(-r, r + 1):
            FX.put([(tq[0], tq[1] + dy)], "X3" if abs(dy) < r - 1 else "X1")
        FX.put([tq], "X4")
    if p["sparkle"] > 0:
        for i in range(int(24 * p["sparkle"])):
            q = (P[0] + (hash01(i, fi, 81) - 0.5) * 40, P[1] - hash01(i, fi, 82) * 54)
            FX.put([ip(q)], "X4" if i % 4 == 0 else "X2")

    imgs = {n: (L.image() if n in FXL else K.render_layer(L)) for n, L in Ls.items()}
    if p["dissolve"] > 0:
        imgs = K.ember_dissolve(imgs, p["dissolve"], [n for n in LAYERS if n not in FXL], fx_name="FX", seed=3, rise=38,
                                pal=("X4", "X3", "X2", "X1", "X0"))
    return imgs, info

# ======================================================================== animation (reference space, see tf())
def ease(t):
    return t * t * (3 - 2 * t)


def tw(a, b, t):
    """interpolate two poses (points linearly, angles the short way unless keyed with 'spin')"""
    q = dict(a)
    for k, va in a.items():
        vb = b.get(k, va)
        if va is None or vb is None:
            q[k] = vb if t >= 0.5 else va
        elif isinstance(va, tuple) and len(va) == 2 and isinstance(va[0], (int, float)):
            q[k] = lerp(va, vb, t)
        elif isinstance(va, (int, float)) and not isinstance(va, bool) and k not in ("fb_toe",):
            q[k] = va + (vb - va) * t
        else:
            q[k] = vb if t >= 0.5 else va
    for k in ("smear", "thrust"):
        q[k] = None
    return q


STANCE = P_()


def seq(keys):
    """keys: list of (pose, ms, n_inbetween_before) -> list of (pose, ms); inbetweens eased from the previous key"""
    out = []
    prev = None
    for pose, ms, nb in keys:
        if prev is not None and nb:
            for i in range(1, nb + 1):
                out.append((tw(prev, pose, ease(i / (nb + 1))), ms))
        out.append((pose, ms))
        prev = pose
    return out


def with_smear(frames, idx, st=0.0):
    """give frame idx a smear from the previous frame's grip/angle"""
    p0, _ = frames[idx - 1]
    p1, ms = frames[idx]
    p1 = dict(p1)
    p1["smear"] = (p0["hf"], p0["wang"], st)
    frames[idx] = (p1, ms)
    return frames


def anim_idle():
    out = []
    for i in range(8):
        s = math.sin(i / 8 * 2 * math.pi)
        p = shift(STANCE, 0, 0)
        p["C"] = add(STANCE["C"], (0, s * 0.6))
        p["Hd"] = add(STANCE["Hd"], (0, s * 0.7))
        p["hf"] = add(STANCE["hf"], (0, s * 0.8))
        p["wang"] = 25 + s * 2
        p["hair"] = math.sin(i / 8 * 2 * math.pi + 0.8) * 2.2
        p["skirt"] = math.sin(i / 8 * 2 * math.pi + 0.4) * 0.8
        out.append((p, 130))
    return out


def anim_walk():
    out = []
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        st = math.sin(ph)
        p = P_()
        bob = abs(math.cos(ph)) * 1.2
        p = shift(p, 0, -bob + 1.0)
        p["ff"] = (61 + st * 9, FLOOR - max(0, math.cos(ph)) * 2.5)
        p["fb"] = (59 - st * 9, FLOOR - max(0, -math.cos(ph)) * 2.5)
        p["hf"] = (69 - st * 1.5, 55 - bob)
        p["wang"] = 28 + st * 4
        p["hb"] = (55 + st * 3, 52)
        p["hair"] = -2.0 + math.sin(ph + 1) * 1.6
        p["skirt"] = -1.0 + st * 1.2
        out.append((p, 110))
    return out


def anim_dash():
    crouch = P_(P=(58, 61), C=(62, 47), Hd=(65.5, 38.5), ff=(69, FLOOR), fb=(50, FLOOR), hf=(56, 60), wang=160, hair=2, skirt=1)
    run = P_(P=(62, 60), C=(70, 48), Hd=(75, 40.5), ff=(78, FLOOR), fb=(46, FLOOR - 3), hf=(56, 58), wang=172,
             hb=(52, 50), hair=-9, skirt=-3, hup=(0.5, -0.9))
    run2 = dict(run, fb=(48, FLOOR - 5), ff=(76, FLOOR), hair=-10.5, skirt=-3.5)
    rec = P_(P=(61, 58), C=(64, 43.5), Hd=(66, 34), ff=(70, FLOOR), fb=(54, FLOOR), hf=(66, 58), wang=150, hair=-4, skirt=-1.5)
    return [(crouch, 70), (run, 60), (run2, 60), (run, 60), (run2, 60), (rec, 110)]


def anim_counter():
    out = []
    for i in range(6):
        p = P_(P=(59, 58), C=(60.5, 43), Hd=(62, 33.5), ff=(66, FLOOR), fb=(51, FLOOR), hf=(66, 46), wang=-88, hb=(64, 42),
               hair=math.sin(i) * 1.5, skirt=0.4 * math.sin(i))
        p["glow"] = 0.35 + 0.35 * math.sin(i / 6 * 2 * math.pi)
        out.append((p, 100))
    return out


def anim_riposte():
    guard = P_(P=(59, 58), C=(60.5, 43), Hd=(62, 33.5), ff=(66, FLOOR), fb=(51, FLOOR), hf=(66, 46), wang=-88, hb=(64, 42))
    up = P_(P=(60, 58), C=(61, 42.5), Hd=(62.5, 33), ff=(68, FLOOR), fb=(52, FLOOR), hf=(62, 34), wang=-125, two=True, hair=2)
    cut = P_(P=(66, 60), C=(72, 46), Hd=(76, 37.5), ff=(80, FLOOR), fb=(52, FLOOR), hf=(82, 55), wang=40, two=True, hair=-5, skirt=-2)
    fol = P_(P=(66, 60), C=(71, 46.5), Hd=(75, 38), ff=(80, FLOOR), fb=(52, FLOOR), hf=(78, 62), wang=75, two=True, hair=-3, skirt=-1.5)
    fr = seq([(guard, 70, 0), (up, 80, 1), (cut, 50, 0), (fol, 60, 0), (STANCE, 110, 2)])
    with_smear(fr, 3, 0.0)
    with_smear(fr, 4, 0.5)
    return fr


def anim_stagger():
    a = P_(P=(57, 58), C=(54, 44), Hd=(52.5, 35), ff=(64, FLOOR), fb=(50, FLOOR), hf=(64, 62), wang=100, hb=(46, 48), hair=4, skirt=2, hup=(-0.5, -0.9))
    b = P_(P=(56, 62), C=(55, 48), Hd=(55.5, 39), ff=(64, FLOOR), fb=(48, FLOOR), hf=(66, 66), wang=95, hb=(50, 60), hair=3, skirt=1.5, hup=(0.3, -1))
    return [(a, 90), (b, 160), (b, 240), (dict(b, Hd=(56, 39.5)), 240)]


KNEEL = P_(P=(58, 68), C=(62, 54.5), Hd=(65.5, 46.5), ff=(70, FLOOR), fb=(52, FLOOR), kb=(56, 84), hf=(74, 62), wang=90,
           hb=(66, 60), hair=2, skirt=0.5, hup=(0.6, -0.8), halo=0.5)


def anim_kneel():
    return [(KNEEL, 200)]


def anim_getup():
    mid = P_(P=(59, 62), C=(62, 48), Hd=(64.5, 39), ff=(68, FLOOR), fb=(53, FLOOR), hf=(72, 60), wang=80, hb=(58, 56),
             hair=1, halo=0.8, hup=(0.3, -0.95))
    tall = P_(P=(60, 56.5), C=(61, 41.5), Hd=(62.5, 32), ff=(66, FLOOR), fb=(54, FLOOR), hf=(66, 40), wang=-90, hb=(52, 52),
              hair=-1, halo=1.15, glow=0.8)
    fr = seq([(KNEEL, 160, 0), (mid, 110, 2), (tall, 140, 1), (STANCE, 110, 1)])
    return fr


def anim_combo():
    # window 1: rising diagonal
    w1a = P_(P=(58, 60), C=(59, 46), Hd=(60, 37), ff=(67, FLOOR), fb=(50, FLOOR), hf=(54, 62), wang=150, hair=2, skirt=1)
    w1b = P_(P=(64, 57), C=(68, 42), Hd=(70.5, 32.5), ff=(76, FLOOR), fb=(52, FLOOR), hf=(78, 34), wang=-62, hair=-5, skirt=-2)
    w1c = dict(w1b, hf=(74, 30), wang=-80, hair=-3)
    # window 2: descending cut over the top
    w2a = P_(P=(62, 57), C=(64, 42), Hd=(65.5, 32.5), ff=(72, FLOOR), fb=(52, FLOOR), hf=(62, 30), wang=-128, hair=0, two=True)
    w2b = P_(P=(66, 59), C=(72, 45), Hd=(75.5, 36), ff=(80, FLOOR), fb=(54, FLOOR), hf=(82, 52), wang=35, hair=-6, skirt=-2.5, two=True)
    w2c = dict(w2b, hf=(78, 60), wang=70, hair=-4)
    # window 3: the great falling-star cut
    w3a = P_(P=(60, 58), C=(58, 43), Hd=(58.5, 33.5), ff=(70, FLOOR), fb=(50, FLOOR), hf=(54, 26), wang=-150, two=True, hair=3, skirt=1, glow=0.6)
    w3b = P_(P=(68, 62), C=(76, 50), Hd=(80, 42), ff=(84, FLOOR), fb=(54, FLOOR), hf=(86, 62), wang=62, two=True, hair=-7, skirt=-3)
    w3c = dict(w3b, hf=(84, 68), wang=84, hair=-5)
    fr = seq([(STANCE, 80, 0), (w1a, 90, 1), (w1b, 50, 0), (w1c, 60, 0), (w2a, 90, 1), (w2b, 50, 0), (w2c, 60, 0),
              (w3a, 110, 1), (w3b, 50, 0), (w3c, 90, 0), (STANCE, 120, 0)])
    # indices: 0 stance,1 inb,2 w1a,3 w1b,4 w1c,5 inb,6 w2a,7 w2b,8 w2c,9 inb,10 w3a,11 w3b,12 w3c,13 stance
    for i, st in ((3, 0), (4, 0.55), (7, 0), (8, 0.55), (11, 0), (12, 0.55)):
        with_smear(fr, i, st)
    return fr


def anim_thrust():
    wind = P_(P=(56, 60), C=(54, 46), Hd=(54, 36.5), ff=(66, REF_FLOOR), fb=(46, REF_FLOOR), hf=(50, 60), wang=-2, hb=(62, 50), hair=3, skirt=1.5, glow=0.3)
    wind2 = dict(wind, hf=(48, 61), glow=0.8)
    lunge = P_(P=(72, 65), C=(83, 55), Hd=(89, 48), ff=(93, REF_FLOOR), fb=(50, REF_FLOOR), hf=(97, 68), wang=2, hb=(58, 58),
               hair=-9, skirt=-3.5, hup=(0.5, -0.87))
    hold = dict(lunge, hf=(96, 69), wang=3)
    back = P_(P=(68, 60), C=(74, 46), Hd=(77, 37), ff=(84, REF_FLOOR), fb=(54, REF_FLOOR), hf=(84, 60), wang=20, hair=-5, skirt=-2)
    fr = [(STANCE, 70), (tw(STANCE, wind, 0.6), 80), (wind, 110), (wind2, 140), (lunge, 50), (hold, 70), (back, 100),
          (tw(back, STANCE, 0.5), 100), (STANCE, 110)]
    p = dict(fr[4][0]); p["thrust"] = True; fr[4] = (p, 50)
    p = dict(fr[5][0]); p["thrust"] = True; fr[5] = (p, 70)
    return fr


def anim_upslash():
    crouch = P_(P=(58, 63), C=(61, 49), Hd=(63.5, 40), ff=(68, FLOOR), fb=(50, FLOOR), hf=(70, 68), wang=30, hair=2, skirt=1, hup=(0.3, -0.95))
    crouch2 = dict(crouch, hf=(66, 72), wang=40, glow=0.6)
    up = P_(P=(62, 53), C=(63, 37.5), Hd=(63, 28), ff=(68, FLOOR - 2), fb=(56, FLOOR), hf=(72, 20), wang=-78, hair=4, skirt=2, two=True, hup=(-0.1, -1))
    up2 = dict(up, hf=(66, 16), wang=-102)
    fr = [(STANCE, 70), (crouch, 90), (crouch2, 110), (tw(crouch2, up, 0.4), 40), (up, 50), (up2, 70), (tw(up2, STANCE, 0.35), 90),
          (tw(up2, STANCE, 0.65), 90), (STANCE, 100), (STANCE, 90)]
    with_smear(fr, 3, 0.0)
    with_smear(fr, 4, 0.0)
    with_smear(fr, 5, 0.5)
    return fr


def anim_leap():
    crouch = P_(P=(58, 64), C=(61, 50), Hd=(63.5, 41), ff=(67, FLOOR), fb=(51, FLOOR), hf=(66, 64), wang=40, hair=2, skirt=1)
    rise = P_(P=(60, 44), C=(61, 29), Hd=(62, 19.5), ff=(64, 72), fb=(56, 70), kf=(66, 60), kb=(54, 58), hf=(58, 18), wang=-128,
              two=True, hair=8, skirt=3, lift=14)
    top = dict(rise, P=(60, 40), C=(60.5, 25), Hd=(61.5, 15.5), ff=(65, 68), fb=(55, 66), kf=(67, 56), kb=(55, 54), hf=(55, 16), wang=-145, glow=0.9)
    dive = P_(P=(60, 46), C=(61, 31), Hd=(62, 21.5), ff=(63, 74), fb=(57, 72), kf=(65, 62), kb=(55, 60), hf=(64, 50), wang=90, two=True,
              hair=-6, skirt=-3, lift=10)
    impact = P_(P=(59, 67), C=(62, 53.5), Hd=(65, 45), ff=(70, FLOOR), fb=(52, FLOOR), kb=(56, 84), hf=(66, 64), wang=90, two=True,
                hair=3, skirt=1, hup=(0.5, -0.85))
    fr = [(STANCE, 60), (crouch, 90), (tw(crouch, rise, 0.5), 60), (rise, 80), (top, 110), (top, 120), (tw(top, dive, 0.5), 50),
          (dive, 60), (impact, 70), (impact, 150), (tw(impact, STANCE, 0.5), 110), (STANCE, 100)]
    with_smear(fr, 7, 0.0)
    return fr


def anim_cast():
    raise_ = P_(P=(60, 57), C=(60.5, 42), Hd=(61.5, 32.5), ff=(67, FLOOR), fb=(52, FLOOR), hf=(62, 24), wang=-100, hb=(46, 40),
                hair=-1, halo=1.2, hup=(-0.15, -1))
    fr = [(STANCE, 80), (tw(STANCE, raise_, 0.35), 80), (tw(STANCE, raise_, 0.7), 80), (raise_, 100)]
    for i in range(4):
        q = dict(raise_, glow=0.6 + 0.4 * (i % 2), sparkle=0.6 + 0.2 * i, halo=1.25 + 0.05 * i, hair=-1 + math.sin(i) * 1.5)
        fr.append((q, 110))
    fr += [(tw(raise_, STANCE, 0.5), 90), (STANCE, 100)]
    return fr


def anim_nova():
    out = []
    for i in range(8):
        s = math.sin(i / 8 * 2 * math.pi)
        p = P_(P=(60, 50 + s), C=(60, 35 + s), Hd=(59.5, 25.5 + s), ff=(62, 80 + s), fb=(57, 79 + s), kf=(64, 66), kb=(56, 66),
               hf=(80, 30 + s), wang=-60, hb=(40, 30 + s), hair=6 + s * 2, skirt=2 + s, halo=1.35 + 0.08 * s, glow=1,
               sparkle=1.0, hup=(-0.3, -1), lift=8)
        out.append((p, 110))
    return out


def anim_death():
    fr = []
    a = P_(P=(57, 58), C=(54, 44), Hd=(52.5, 35), ff=(64, FLOOR), fb=(50, FLOOR), hf=(64, 62), wang=100, hb=(46, 48), hair=4, skirt=2, hup=(-0.5, -0.9))
    fr += [(a, 120), (tw(a, KNEEL, 0.5), 120), (KNEEL, 300)]
    for i in range(9):
        k = (i + 1) / 9
        fr.append((dict(KNEEL, dissolve=0.15 + 0.85 * k, halo=max(0.0, 0.5 - k * 0.5)), 110))
    return fr




def anim_flurry():
    w = P_(P=(58, 58), C=(58, 43), Hd=(59, 33.5), ff=(67, REF_FLOOR), fb=(50, REF_FLOOR), hf=(56, 30), wang=-130, two=True, hair=2, glow=0.5)
    cuts = []
    for k in range(4):
        x = 61 + k * 2.2
        lo = P_(P=(x + 2, 59), C=(x + 6, 45), Hd=(x + 8.5, 36), ff=(x + 12, REF_FLOOR), fb=(x - 8, REF_FLOOR), hf=(x + 18, 56), wang=45 + (k % 2) * 10,
                hair=-5, skirt=-2)
        hi = P_(P=(x + 3, 57), C=(x + 5, 42), Hd=(x + 7, 32.5), ff=(x + 13, REF_FLOOR), fb=(x - 7, REF_FLOOR), hf=(x + 14, 30), wang=-62 - (k % 2) * 8,
                hair=-3, skirt=-1)
        cuts.append(lo if k % 2 == 0 else hi)
    big_w = P_(P=(66, 60), C=(64, 46), Hd=(64.5, 37), ff=(76, REF_FLOOR), fb=(56, REF_FLOOR), hf=(58, 40), wang=-170, two=True, hair=3, glow=1)
    big = P_(P=(70, 60), C=(77, 48), Hd=(81, 40), ff=(86, REF_FLOOR), fb=(58, REF_FLOOR), hf=(90, 48), wang=8, two=True, hair=-8, skirt=-3.5)
    big2 = dict(big, hf=(88, 54), wang=30, hair=-6)
    fr = [(STANCE, 60), (w, 100)]
    for k, c in enumerate(cuts):
        fr.append((c, 45))
        fr.append((dict(c, hf=add(c["hf"], (1.5, 4 if k % 2 == 0 else -3)), wang=c["wang"] + (12 if k % 2 == 0 else -12)), 50))
    fr += [(big_w, 90), (big, 45), (big2, 90), (STANCE, 120)]
    for i in (2, 4, 6, 8, 11):
        with_smear(fr, i, 0.0)
    for i in (3, 5, 7, 9, 12):
        with_smear(fr, i, 0.55)
    return fr


def anim_wave():
    wind = P_(P=(58, 61), C=(56, 47), Hd=(56, 38), ff=(68, REF_FLOOR), fb=(48, REF_FLOOR), hf=(50, 58), wang=172, hair=3, skirt=1.5, glow=0.4)
    wind2 = dict(wind, hf=(48, 57), wang=178, glow=1)
    cut = P_(P=(66, 59), C=(72, 45), Hd=(75, 36), ff=(80, REF_FLOOR), fb=(52, REF_FLOOR), hf=(88, 50), wang=-2, hair=-7, skirt=-3)
    fol = dict(cut, hf=(84, 42), wang=-38, hair=-6)
    fr = [(STANCE, 70), (tw(STANCE, wind, 0.5), 80), (wind, 110), (wind2, 160), (cut, 45), (fol, 70), (dict(fol, hf=(82, 40)), 120),
          (tw(fol, STANCE, 0.4), 100), (tw(fol, STANCE, 0.75), 100), (STANCE, 100)]
    with_smear(fr, 4, 0.0)
    with_smear(fr, 5, 0.5)
    return fr


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


ANIMS = [
    ("astrel", [("idle", anim_idle), ("walk", anim_walk), ("dash", anim_dash), ("counter", anim_counter), ("riposte", anim_riposte),
                ("stagger", anim_stagger), ("kneel", anim_kneel), ("getup", anim_getup)]),
    ("astrel_b", [("combo", anim_combo), ("thrust", anim_thrust), ("upslash", anim_upslash), ("flurry", anim_flurry)]),
    ("astrel_c", [("leap", anim_leap), ("cast", anim_cast), ("nova", anim_nova), ("death", anim_death), ("wave", anim_wave)]),
]
WINDOWS = {"combo": [[3, 4], [7, 8], [11, 12]], "thrust": [[4, 5]], "upslash": [[3, 5]], "riposte": [[3, 4]], "leap": [[7, 8]],
           "flurry": [[2, 3], [4, 5], [6, 7], [8, 9], [11, 12]], "wave": [[4, 5]]}


def bbox_of(pts):
    pts = [q for q in pts if 0 <= q[0] < W and 0 <= q[1] < H]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def build():
    meta = {"native": 1, "anchor": [AX, H], "hurtbox": [57, 52, 19, 67], "attacks": {}, "telegraph": {}, "spawn": {}}
    halo_t = 0.0
    for phase in (1, 2):
        for sheet_name, tags in ANIMS:
            name = sheet_name.replace("astrel", "astrel2") if phase == 2 else sheet_name
            anims = []
            for tag, fn in tags:
                if ONLY and tag not in ONLY:
                    continue
                frs = fn()
                out, infos = [], []
                for fi, (pose, ms) in enumerate(frs):
                    halo_t += ms
                    pose = dict(pose); pose["halo_ph"] = halo_t / 1000.0 * 1.4
                    imgs, info = draw(pose, fi, phase)
                    out.append((ms, imgs)); infos.append(info)
                anims.append((tag, out))
                if phase == 1:
                    if tag in WINDOWS:
                        wins = []
                        for (a, b) in WINDOWS[tag]:
                            pts = set()
                            for k in range(a, b + 1):
                                pts |= infos[k]["hit"]
                            wins.append({"active": [a, b], "hit": bbox_of(pts)})
                        meta["attacks"][tag] = {"windows": wins}
                    for sp_tag, fr_ in (("cast", 5), ("wave", 5)):
                        if tag == sp_tag:
                            meta["spawn"][sp_tag] = {"frame": fr_, "at": [round(infos[fr_]["tip"][0]), round(infos[fr_]["tip"][1])]}
            if anims:
                K.export(name, LAYERS, anims, None, build=BUILD, flat_order=LAYERS)
                print("built" if BUILD else "previewed", name, sum(len(f) for _, f in anims), "frames")
    if not ONLY:
        with open(os.path.join(asebuild.ASSETS, "astrel_meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
    # close-up of the idle frame, both phases, for design review
    imgs, _ = draw(dict(STANCE, halo_ph=0.3), 0, 1)
    imgs2, _ = draw(dict(STANCE, halo_ph=0.3), 0, 2)
    fl = K.flatten(imgs, LAYERS); fl2 = K.flatten(imgs2, LAYERS)
    cl = Image.new("RGBA", (W * 2 + 8, H), K.BG_CELL)
    cl.alpha_composite(fl, (0, 0)); cl.alpha_composite(fl2, (W + 8, 0))
    cl.crop((30, 30, W + 8 + 110, H)).resize(((W + 88) * 4, (H - 30) * 4), Image.NEAREST).save(os.path.join(ART, "previews", "astrel_closeup.png"))


if __name__ == "__main__":
    build()
