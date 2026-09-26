#!/usr/bin/env python3
"""Boss generator -- "Astrel, the Fallen Star" (agent SF, Starfall Crater).

    python3 art/gen_starfall_astrel.py              full build (both phases) + meta + previews
    python3 art/gen_starfall_astrel.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_starfall_astrel.py --only combo,thrust --preview

A celestial swordswoman: slender, graceful, obsidian-glass armour with starlight shining through its cracks, a halo of
orbiting star fragments, long nebula hair, a faceless serene silver mask and a long curved starlight sword.
Frame 128x88, faces RIGHT, feet on the bottom row, anchor x = 60. ~60 px tall (the player is ~26).
Every frame is drawn by one draw(pose) from the same rig with FIXED bone lengths (proportions never drift); hands and
feet are clamped to the reach of their limbs, so nothing ever detaches.

Sheets (tags split to keep strips short; all share assets/astrel_meta.json):
    astrel   : idle walk dash counter riposte stagger kneel getup
    astrel_b : combo thrust upslash
    astrel_c : leap cast nova death
    astrel2* : the same frames for phase 2 (cracks blaze, the halo widens, the hair burns brighter)
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, leg, arm, swept, thrust_lines, dirv)

W, H = 128, 88
K.setup(W, H)
FLOOR = H - 1
AX = 60
BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

EXTRA = {
    # obsidian glass armour (deep blue-black, glossy)
    "Z0": "#07070f", "Z1": "#0f1022", "Z2": "#191c3a", "Z3": "#262c56", "Z4": "#3a4680", "Z5": "#7e92d6",
    # silver mask
    "J0": "#1c1e2c", "J1": "#3a3e52", "J2": "#636a80", "J3": "#9aa2b6", "J4": "#d2d8e4", "J5": "#f4f6fa",
    # nebula hair
    "H0": "#100820", "H1": "#1e1040", "H2": "#321a64", "H3": "#4c2a8c", "H4": "#7448b8", "H5": "#a67ee0",
    # starlight blade
    "E0": "#16244e", "E1": "#2c4892", "E2": "#5e84d8", "E3": "#a4c2f6", "E4": "#e2ecff",
    # dark undersuit
    "U0": "#08080f", "U1": "#10101c", "U2": "#1a1a2c", "U3": "#262640",
    # starlight glow (fixed)
    "X0": "#1a2a66", "X1": "#3a5ac4", "X2": "#7a9cf2", "X3": "#c6d8ff", "X4": "#ffffff",
}
for k_, v_ in EXTRA.items():
    K.HEX[k_] = v_
    K.RGBA[k_] = tuple(int(v_[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k_[0], []).append(k_)
K.SHINY["Z"] = 0.9
K.SHINY["J"] = 0.88
K.SMEAR["star"] = ["X4", "X3", "X2", "X1"]
K.SMEAR["star2"] = ["X4", "X4", "X3", "X2"]

LAYERS = ["FXBack", "Hair", "SkirtBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Skirt", "Head", "Weapon", "FrontArm", "FX"]
FXL = {"FXBack", "FX"}

# ---------------------------------------------------------------- fixed proportions
L_TH, L_SH = 15.2, 15.4          # thigh, shin
L_UA, L_FA = 10.6, 10.2          # upper arm, forearm
BLADE = 38.0
NEU = dict(P=(60.0, 57.0), C=(61.5, 42.0), Hd=(63.0, 32.6), ff=(67.0, FLOOR), fb=(53.0, FLOOR),
           hf=(69.0, 54.0), hb=None, wang=25.0, two=False, kf=None, kb=None, hair=0.0, skirt=0.0, lift=0.0,
           halo=1.0, glow=0.0, smear=None, thrust=None, dissolve=0.0, burst=0.0, rot=0.0, piv=(60, 60),
           hup=(0.05, -1.0), fb_toe=1, sparkle=0.0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


PTS = ("P", "C", "Hd", "fb", "ff", "hf", "hb", "kf", "kb")


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
    lit = -(n[0] * K.LIGHT[0] + n[1] * K.LIGHT[1])      # >0: the +n side faces the light
    u = 0.0
    tip = grip
    while u <= BLADE:
        t = u / BLADE
        off = bend * 4.4 * t * t
        c = (grip[0] + d[0] * u + n[0] * off, grip[1] + d[1] * u + n[1] * off)
        tx, ty = d[0] + n[0] * bend * 8.8 * t / BLADE, d[1] + n[1] * bend * 8.8 * t / BLADE
        tl = math.hypot(tx, ty)
        nn = (-ty / tl, tx / tl)
        taper = 1.0 if t < 0.78 else max(0.0, (1 - t) / 0.22) ** 0.9
        we, ws = 1.35 * taper + 0.15, 0.95 * taper + 0.1
        v = -ws
        while v <= we:
            q = ip((c[0] + nn[0] * v, c[1] + nn[1] * v))
            side = v if lit > 0 else -v
            if v > we * 0.45:
                col = "E4" if side > 0 else "E3"            # the cutting edge (bend side is the spine)
            elif v < -ws * 0.45:
                col = "E1" if side < 0 else "E2"
            else:
                col = "X3" if (glow > 0.5 or phase == 2) and int(u) % 5 != 0 else "E2"
            if q not in pix or col in ("E4", "X3"):
                pix[q] = col
            blade.add(q)
            v += 0.45
        tip = c
        u += 0.3
    # guard: a thin crescent of silver
    for k in range(-5, 6):
        q = ip((grip[0] + n[0] * k * 0.55 - d[0] * (0.4 + abs(k) * 0.12), grip[1] + n[1] * k * 0.55 - d[1] * (0.4 + abs(k) * 0.12)))
        pix[q] = "J4" if k < 0 else "J2"
    # grip + star pommel
    for i in range(1, 12):
        uu = -i * 0.5
        q = ip((grip[0] + d[0] * uu, grip[1] + d[1] * uu))
        pix[q] = "U3" if i % 3 else "J2"
    pq = ip((grip[0] - d[0] * 6.8, grip[1] - d[1] * 6.8))
    pix[pq] = "X4"
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pix[(pq[0] + dx, pq[1] + dy)] = "X2"
    return pix, blade, tip


# ---------------------------------------------------------------- one frame
def draw(p, fi, phase):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    G = basis(Hd, p["hup"])
    info = {"hit": set()}
    p2 = phase == 2
    sw, hs = p["skirt"], p["hair"]

    # ---------------- shoulders, hips
    shF, shB = F(2.0, -ln + 1.6), F(-2.2, -ln + 1.9)
    hipF, hipB = F(1.6, 0.4), F(-1.6, 0.4)

    # ---------------- weapon: always in the front hand (clamped to arm reach)
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
        hb = (grip[0] - d_[0] * 3.4, grip[1] - d_[1] * 3.4)
    if hb is None:
        hb = F(-4.5, -3.0)
    hb = reach(shB, hb, L_UA + L_FA)

    # ---------------- halo: star fragments orbiting behind the head
    hc = G(-1.2, -1.6)
    hr = (9.5 if not p2 else 11.5) * p["halo"]
    nfr = 8 if not p2 else 11
    ph = p.get("halo_ph", 0.0)
    if p["halo"] > 0.05:
        for k in range(48):                             # the faint ring
            a = k / 48 * 2 * math.pi
            if k % 3 == 0:
                FXB.put([ip(R.T((hc[0] + math.cos(a) * hr, hc[1] + math.sin(a) * hr * 1.05)))], "X0" if not p2 else "X1")
        for k in range(nfr):
            a = ph + k / nfr * 2 * math.pi
            q = ip(R.T((hc[0] + math.cos(a) * hr, hc[1] + math.sin(a) * hr * 1.05)))
            big = (k % 3 == 0)
            FXB.put([q], "X4")
            FXB.put([(q[0] + 1, q[1]), (q[0], q[1] + 1)], "X2")
            if big:
                FXB.put([(q[0] - 1, q[1]), (q[0], q[1] - 1)], "X3")
                FXB.put([(q[0], q[1] - 2), (q[0], q[1] + 2)], "X1")

    # ---------------- hair: a long river of nebula flowing back from the head
    Hr = Ls["Hair"]
    root = G(-2.8, -2.4)
    L0 = 30.0
    pts = bezier(root, add(root, (-6.0 + hs * 0.2, 6.0)), add(root, (-9.0 + hs * 0.9, 22.0 - abs(hs) * 0.4)),
                 add(root, (-17.0 + hs * 1.8, 36.0 - abs(hs) * 1.2 - p["lift"] * 0.6)), n=20)
    for i in range(len(pts) - 1):
        t0, t1 = i / (len(pts) - 1), (i + 1) / (len(pts) - 1)
        r0, r1 = 3.2 - 2.5 * t0 ** 0.8, 3.2 - 2.5 * t1 ** 0.8
        m = R.cap(Hr, pts[i], pts[i + 1], r0, r1, "H", bias=0 if i < 6 else -1, ao=0)
    for k in range(3):                                   # strands, magenta-violet highlights
        sp = [add(q, (0.3 * k - 0.4, -1.0 + k * 0.9)) for q in pts[1:17 - k * 3]]
        Hr.decal(polyline([R.T(q) for q in sp]), ("H", 4 if k != 1 else 3))
    for i, q in enumerate(pts[3:]):                      # stars caught in the hair
        if hash01(i, fi, 71) < (0.35 if not p2 else 0.6):
            FX.put([ip(R.T(add(q, (hash01(i, 1, fi) * 4 - 2, hash01(i, 2, fi) * 4 - 2))))], "X3" if hash01(i, 3, fi) < 0.6 else "X4")
    tipq = pts[-1]
    for i in range(5 + (4 if p2 else 0)):                # the ends dissolve into motes
        q = add(tipq, (-hash01(i, fi, 72) * 6 - 1, hash01(i, fi, 73) * 6 - 2))
        FXB.put([ip(R.T(q))], "X2" if i % 2 else "H5")

    # ---------------- the star-cloth train: a long fall of night sky from the back of the waist
    SB = Ls["SkirtBack"]
    w0 = F(-2.6, -3.2)
    lift = p["lift"]
    hem = FLOOR - 9 - lift * 0.4
    tr_pts = bezier(w0, add(w0, (-3.0 + sw * 0.3, 8.0)), add(w0, (-7.0 + sw * 0.9, 16.0 - lift * 0.2)),
                    (w0[0] - 11.0 + sw * 1.8, min(hem, w0[1] + 27.0)), n=12)
    left = [add(q, (-1.6 - 2.4 * i / 11, 0.4 * i / 11)) for i, q in enumerate(tr_pts)]
    right = [add(q, (1.8 + 1.4 * i / 11, -0.8 * i / 11)) for i, q in enumerate(tr_pts)]
    hem_pts = []
    a_, b_ = left[-1], right[-1]
    for k in range(7):
        t = k / 6
        x, y = lerp(a_, b_, t)
        hem_pts.append((x, y + (2.2 if k % 2 else 0.2)))
    trm = R.plate(SB, [left[0]] + left[1:] + hem_pts + right[::-1], "U", bevel=1.6, tilt=(0.1, 0.05), strength=0.9,
                  fold=lambda x, y: (0.5 * math.sin((x - P[0]) * 0.9 + y * 0.12 + sw), 0), bias=0)
    for q in trm:                                        # the night inside the cloth
        hv = hash01(q[0], q[1], 61 + fi // 3)
        if hv < (0.035 if not p2 else 0.06):
            SB.decal([q], "X4" if hv < 0.012 else "X2")
        elif hv > 0.985:
            SB.decal([q], ("H", 3))
    edge = [q for q in trm if (q[0] - 1, q[1]) not in trm]
    SB.decal(edge[::2], ("H", 2))

    # ---------------- back arm
    arm(R, Ls["BackArm"], shB, hb, L_UA, L_FA, 1.8, 1.45, "Z", bias=-1, fist="U", fist_r=1.4, fore="Z", pref=(-1, 0.6))
    R.dome(Ls["BackArm"], add(shB, (-0.2, -0.4)), 2.8, 2.4, "Z", bias=-1)

    # ---------------- legs
    for nm, hip, ft, bias, kn in (("BackLeg", hipB, p["fb"], -1, p["kb"]), ("FrontLeg", hipF, p["ff"], 0, p["kf"])):
        ftc = reach(hip, (ft[0], ft[1] - 1.4), L_TH + L_SH)
        ftc = (ftc[0], ftc[1] + 1.4)
        k = leg(R, Ls[nm], hip, ftc, L_TH, L_SH, 2.1, 1.55, "Z", bias=bias, flen=4.2, heel=1.4, boot_h=2.4, knee=kn,
                boot=None)
        R.dome(Ls[nm], add(k, (0.5, 0.0)), 1.5, 1.4, "Z", bias=bias)
        # a starlight crack down the shin
        a_ = lerp(k, (ftc[0], ftc[1] - 2), 0.25)
        b_ = lerp(k, (ftc[0], ftc[1] - 2), 0.7)
        R.dline(Ls[nm], add(a_, (0.6, 0)), add(b_, (0.2, 0)), ("X", 3 if (p2 or bias == 0) else 2))
        R.decal(Ls[nm], [lerp(hip, k, 0.55)], ("X", 2 + bias))
        info["knee_" + nm] = k

    # ---------------- torso: a sleek glass cuirass, narrow waist
    Bd = Ls["Body"]
    torso = [F(-3.4, 1.0), F(-2.2, -4.8), F(-3.2, -ln + 3.4), F(-2.6, -ln - 0.4), F(2.2, -ln - 0.6), F(4.0, -ln + 2.6),
             F(3.3, -ln + 5.8), F(2.0, -5.2), F(3.2, 1.0)]
    tm = R.plate(Bd, torso, "Z", bevel=2.2, tilt=(-0.35, -0.2), strength=1.1)
    info["torso"] = tm
    R.dline(Bd, F(-2.2, -4.9), F(2.0, -5.1), ("J", 2))                        # silver girdle
    R.dline(Bd, F(-2.4, -4.2), F(2.1, -4.4), ("J", 1))
    R.dline(Bd, F(-2.4, -ln - 0.2), F(2.0, -ln - 0.4), ("J", 3))              # silver collar
    R.dline(Bd, F(3.6, -ln + 2.0), F(2.6, -ln + 5.2), ("Z", 5))              # gloss on the breastplate                       # waist seam
    crack = [F(1.2, -ln + 0.6), F(0.2, -ln + 3.6), F(1.4, -ln + 6.2), F(0.4, -5.8), F(1.2, -2.8)]
    for a, b in zip(crack, crack[1:]):
        R.dline(Bd, a, b, ("X", 3))
    if p2:
        R.dline(Bd, F(0.8, -ln + 6.5), F(3.2, -ln + 8.0), ("X", 3))
        R.dline(Bd, F(-0.4, -ln + 4.0), F(-3.0, -ln + 5.4), ("X", 2))
    R.decal(Bd, [F(0.2, -ln + 5.0)], ("X", 4))
    # gorget
    
    # ---------------- front tasset: a short blade of glass over the hip
    Sk = Ls["Skirt"]
    ft_ = F(1.6, -0.4)
    fh = add(ft_, (1.2 - sw * 0.5, 6.0 - p["lift"] * 0.1))
    R.plate(Sk, [add(ft_, (-2.0, -0.6)), add(ft_, (2.4, -0.8)), add(fh, (1.2, 0)), fh], "Z", bevel=1.0, tilt=(-0.35, 0.0), bias=0)
    R.dline(Sk, add(ft_, (1.4, 0.2)), add(fh, (0.6, -0.6)), ("X", 3 if p2 else 2))

    # ---------------- head: dark hood of hair behind, a faceless silver mask in front, a starlit circlet
    Hl = Ls["Head"]
    back = [G(-4.3, 1.8), G(-4.4, -2.6), G(-2.4, -5.2), G(0.4, -5.6), G(-0.4, 4.4), G(-2.8, 4.4)]
    R.plate(Hl, back, "H", bevel=1.5, tilt=(-0.3, -0.3), strength=1.2)
    mask = [G(-1.2, -5.0), G(1.8, -5.2), G(3.8, -3.0), G(4.5, 0.2), G(4.0, 3.2), G(2.2, 5.2), G(-0.6, 5.0), G(-1.6, 0.6)]
    mm = R.plate(Hl, mask, "J", bevel=2.4, tilt=(0.0, 0.0), strength=1.4, bias=0)
    info["head"] = mm
    R.dline(Hl, G(0.6, -4.6), G(3.2, -3.2), ("J", 4))
    R.decal(Hl, [G(1.6, -4.2)], ("J", 5))
    R.dline(Hl, G(4.2, -1.2), G(3.8, 2.6), ("J", 2))                          # the mask's quiet profile ridge
    R.dline(Hl, G(-1.4, -4.6), G(-1.8, 3.6), ("H", 3))                        # where the hair meets the mask
    R.dline(Hl, G(-4.0, -3.2), G(1.6, -5.0), ("X", 3 if not p2 else 4))       # circlet
    R.decal(Hl, [G(0.8, -5.0)], ("X", 4))
    # neck
    R.cap(Ls["Body"], F(0.4, -ln - 0.2), add(Hd, (-0.4, 4.2)), 1.2, 1.0, "U", bias=-1)

    # ---------------- front arm (over the grip)
    arm(R, Ls["FrontArm"], shF, hf, L_UA, L_FA, 1.8, 1.45, "Z", bias=0, fist="U", fist_r=1.5, fore="Z", pref=(-1, 0.6))
    R.dome(Ls["FrontArm"], add(shF, (0.3, -0.5)), 3.0, 2.6, "Z", bias=0)       # pauldron
    R.dline(Ls["FrontArm"], add(shF, (-1.4, -1.6)), add(shF, (1.8, 0.8)), ("X", 2 if not p2 else 3))

    # ---------------- smear / thrust fx
    if p["smear"]:
        g0, a0, st = p["smear"]
        hot = swept(FX, R.T(g0), R.A(a0), R.T(grip), R.A(wang), BLADE * 0.5, BLADE + 1.0, hw=0.9, start=st, taper=0.7,
                    pal="star2" if p2 else "star", clip_y=FLOOR)
        info["hit"] |= hot
    if p["thrust"]:
        pts_ = thrust_lines(FX, R.T(grip), R.A(wang), 6, BLADE + 8, (-3, -1.5, 1.5, 3), pal="star", flash=BLADE + 2)
        info["hit"] |= pts_
    if p["glow"] > 0:                                     # the blade gathers light
        tq = ip(tip)
        r = 2 + int(p["glow"] * 3)
        for dx in range(-r, r + 1):
            FX.put([(tq[0] + dx, tq[1])], "X3" if abs(dx) < r - 1 else "X1")
        for dy in range(-r, r + 1):
            FX.put([(tq[0], tq[1] + dy)], "X3" if abs(dy) < r - 1 else "X1")
        FX.put([tq], "X4")
    if p["sparkle"] > 0:                                  # motes rising off the body (nova / cast)
        for i in range(int(20 * p["sparkle"])):
            q = (P[0] + (hash01(i, fi, 81) - 0.5) * 34, P[1] - hash01(i, fi, 82) * 44)
            FX.put([ip(q)], "X4" if i % 4 == 0 else "X2")

    imgs = {n: (L.image() if n in FXL else K.render_layer(L)) for n, L in Ls.items()}
    if p["dissolve"] > 0:
        imgs = K.ember_dissolve(imgs, p["dissolve"], [n for n in LAYERS if n not in FXL], fx_name="FX", seed=3, rise=34,
                                pal=("X4", "X3", "X2", "X1", "X0"))
    return imgs, info


# ======================================================================== animation
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
    wind = P_(P=(56, 58), C=(54, 44), Hd=(54, 34.5), ff=(66, FLOOR), fb=(46, FLOOR), hf=(50, 44), wang=-4, hb=(64, 42), hair=3, skirt=1.5, glow=0.3)
    wind2 = dict(wind, hf=(48, 43), glow=0.8)
    lunge = P_(P=(72, 61), C=(82, 50), Hd=(87, 42.5), ff=(92, FLOOR), fb=(52, FLOOR), hf=(96, 48), wang=0, hb=(58, 50),
               hair=-9, skirt=-3.5, hup=(0.45, -0.9))
    hold = dict(lunge, hf=(95, 49), wang=2)
    back = P_(P=(68, 59), C=(74, 45.5), Hd=(77, 36.5), ff=(84, FLOOR), fb=(54, FLOOR), hf=(84, 56), wang=20, hair=-5, skirt=-2)
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
    rise = P_(P=(60, 44), C=(61, 29), Hd=(62, 19.5), ff=(64, 72), fb=(56, 70), kf=(66, 60), kb=(54, 58), hf=(60, 14), wang=-90,
              two=True, hair=8, skirt=3, lift=14)
    top = dict(rise, P=(60, 40), C=(60.5, 25), Hd=(61.5, 15.5), ff=(65, 68), fb=(55, 66), kf=(67, 56), kb=(55, 54), hf=(56, 10), wang=-110, glow=0.9)
    dive = P_(P=(60, 46), C=(61, 31), Hd=(62, 21.5), ff=(63, 74), fb=(57, 72), kf=(65, 62), kb=(55, 60), hf=(64, 50), wang=90, two=True,
              hair=-6, skirt=-3, lift=10)
    impact = P_(P=(59, 67), C=(62, 53.5), Hd=(65, 45), ff=(70, FLOOR), fb=(52, FLOOR), kb=(56, 84), hf=(66, 64), wang=90, two=True,
                hair=3, skirt=1, hup=(0.5, -0.85))
    fr = [(STANCE, 60), (crouch, 90), (tw(crouch, rise, 0.5), 60), (rise, 80), (top, 110), (top, 120), (tw(top, dive, 0.5), 50),
          (dive, 60), (impact, 70), (impact, 150), (tw(impact, STANCE, 0.5), 110), (STANCE, 100)]
    with_smear(fr, 7, 0.0)
    return fr


def anim_cast():
    raise_ = P_(P=(60, 57), C=(60.5, 42), Hd=(61.5, 32.5), ff=(67, FLOOR), fb=(52, FLOOR), hf=(62, 18), wang=-92, hb=(46, 40),
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


ANIMS = [
    ("astrel", [("idle", anim_idle), ("walk", anim_walk), ("dash", anim_dash), ("counter", anim_counter), ("riposte", anim_riposte),
                ("stagger", anim_stagger), ("kneel", anim_kneel), ("getup", anim_getup)]),
    ("astrel_b", [("combo", anim_combo), ("thrust", anim_thrust), ("upslash", anim_upslash)]),
    ("astrel_c", [("leap", anim_leap), ("cast", anim_cast), ("nova", anim_nova), ("death", anim_death)]),
]
# hit windows: tag -> list of frame ranges within the tag
WINDOWS = {"combo": [[3, 4], [7, 8], [11, 12]], "thrust": [[4, 5]], "upslash": [[3, 5]], "riposte": [[3, 4]], "leap": [[7, 8]]}


def bbox_of(pts):
    pts = [q for q in pts if 0 <= q[0] < W and 0 <= q[1] < H]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def build():
    meta = {"native": 1, "anchor": [AX, H], "hurtbox": [54, 30, 15, 57], "attacks": {}, "telegraph": {}, "spawn": {}}
    halo_t = 0.0
    all_tags = {}
    for phase in (1, 2):
        for sheet_name, tags in ANIMS:
            name = sheet_name.replace("astrel", "astrel2") if phase == 2 else sheet_name
            anims = []
            for tag, fn in tags:
                if ONLY and tag not in ONLY:
                    continue
                frs = fn()
                out = []
                infos = []
                for fi, (pose, ms) in enumerate(frs):
                    halo_t += ms
                    pose = dict(pose); pose["halo_ph"] = halo_t / 1000.0 * 1.4
                    imgs, info = draw(pose, fi, phase)
                    out.append((ms, imgs))
                    infos.append(info)
                anims.append((tag, out))
                if phase == 1:
                    all_tags[tag] = infos
                    if tag in WINDOWS:
                        wins = []
                        for (a, b) in WINDOWS[tag]:
                            pts = set()
                            for k in range(a, b + 1):
                                pts |= infos[k]["hit"]
                            wins.append({"active": [a, b], "hit": bbox_of(pts)})
                        meta["attacks"][tag] = {"windows": wins}
                        t0 = WINDOWS[tag][0][0] - 1
                        meta["telegraph"][tag] = {"frame": max(0, t0 - 1), "at": [round(infos[max(0, t0 - 1)]["tip"][0]), round(infos[max(0, t0 - 1)]["tip"][1])]}
                    if tag == "cast":
                        meta["spawn"]["cast"] = {"frame": 5, "at": [round(infos[5]["tip"][0]), round(infos[5]["tip"][1])]}
                    if tag == "nova":
                        meta["spawn"]["nova"] = {"frame": 0, "at": [60, 34]}
            if anims:
                K.export(name, LAYERS, anims, meta if (phase == 1 and sheet_name == "astrel") else None, build=BUILD,
                         flat_order=LAYERS)
                print("built" if BUILD else "previewed", name, sum(len(f) for _, f in anims), "frames")
    if not ONLY:
        with open(os.path.join(asebuild.ASSETS, "astrel_meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
    # close-up of the idle frame for design review
    imgs, _ = draw(dict(STANCE, halo_ph=0.3), 0, 1)
    imgs2, _ = draw(dict(STANCE, halo_ph=0.3), 0, 2)
    fl = K.flatten(imgs, LAYERS); fl2 = K.flatten(imgs2, LAYERS)
    cl = Image.new("RGBA", (W * 2 + 8, H), K.BG_CELL)
    cl.alpha_composite(fl, (0, 0)); cl.alpha_composite(fl2, (W + 8, 0))
    cl.crop((30, 8, 100, H)).resize((70 * 8, (H - 8) * 8), Image.NEAREST).save(os.path.join(ART, "previews", "astrel_closeup.png"))


if __name__ == "__main__":
    build()
