"""Shared humanoid rig for the Necropolis creatures (agent N): nobles, ringers, the Twin Executioners, King Vael and his
spectral court. Built on enemy_kit.py (normal-field shading, sel-out outlines, Rig) -- the same method as gen_kalden.py.

A pose is a dict of joints in frame coords (faces RIGHT, feet on the bottom row):
    P hip centre, C chest centre, Hd head centre, hup head up-vector, fb/ff back/front foot (sole point),
    hb/hf back/front hand, wang weapon angle (deg, 0 = pointing right, -90 = up), plus per-frame extras
    (smear arcs, lift, cape wind, fx flags).
An outfit dict fixes the body: scale, limb lengths/radii, materials, head type, cape, weapon, chains, shield.
Proportions come from the outfit only, so every frame of a creature keeps the same head/limb/torso sizes.
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,  # noqa: E402
                       poly_mask, n_plate, n_dome, n_capsule, norm3, swept, dirv, bbox, blade_px)

RAMPS = {
    "U": ["#142c58", "#22498a", "#3a70c0", "#63a0e6", "#a2cdf8", "#e4f3ff"],        # ghost-fire (fixed use)
    "X": ["#1a1209", "#342412", "#56401a", "#7e6128", "#a8883e", "#d4b86a"],        # corroded gold (shiny)
    "N": ["#0d1916", "#19302b", "#2a4a42", "#3f6a5c", "#5c8c78"],                   # verdigris / corrosion
    "H": ["#0b0611", "#170b21", "#261338", "#381f52", "#4e2f70", "#6a4892"],        # royal purple cloth
    "S": ["#122a52", "#1f4584", "#3668b4", "#5e92dc", "#96c2f4", "#d8ecff"],        # spectral (translucent ghosts)
    "E": ["#0b0708", "#170d0e", "#261517", "#381f21", "#4e2b2b", "#673a36"],        # executioner hood / oxblood
    "Z": ["#08080b", "#111117", "#1b1b24", "#282834", "#3a3a4a", "#585868"],        # blackened iron
}
for _r, _cols in RAMPS.items():
    keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        keys.append(_k)
    K.RAMP[_r] = keys
K.SHINY.update({"X": 0.9, "Z": 0.93})
K.SMEAR.update({
    "ghost": ["U5", "U4", "U3", "U2"],
    "bone": ["B5", "B4", "B3", "B2"],
    "steel": ["B5", "I5", "I4", "I3"],
    "blood": ["B5", "C5", "C4", "C3"],
})

LAYERS = ["FXBack", "Cape", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "Weapon", "FrontArm",
          "Chains", "FX"]
FXL = {"FXBack", "Chains", "FX"}

NEU = dict(P=(24, 34), C=(25, 22), Hd=(26.5, 14), hup=(0.1, -1), fb=(20, 47), ff=(29, 47), hb=(19, 31), hf=(31, 30),
           kb=None, kf=None, eb=None, ef=None, wang=-60, wl="Weapon", grip2=True, weapon_on=True, smear=None,
           thrust=None, wind=0.0, lift=0.0, rot=0.0, piv=(0, 0), glow=1.0, eye=1.0, fire=0.0, chain=None,
           burst=0.0, sparks=None, shield_up=0.0, crown=1.0, cape_on=True, flat=None, post=None, jaw=0.0, open_hand=False,
           bell_ring=0.0, dust=0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


JOINTS = ("P", "C", "Hd", "fb", "ff", "hb", "hf", "kb", "kf", "eb", "ef")


def scaled(pose, s, ox, oy, floor):
    """Poses are authored for a unit human (feet on y=47, hip x=24); scale about the feet and move into a frame."""
    q = dict(pose)
    for k in JOINTS:
        if q.get(k) is not None:
            x, y = q[k]
            q[k] = (ox + (x - 24) * s, floor + (y - 47) * s)
    if q.get("smear"):
        tr = lambda pt: (ox + (pt[0] - 24) * s, floor + (pt[1] - 47) * s)
        q["smear"] = [(tr(sm[0]), sm[1], tr(sm[2])) + tuple(sm[3:]) for sm in q["smear"]]
    if q.get("sparks"):
        cx, cy, n = q["sparks"]
        q["sparks"] = (ox + (cx - 24) * s, floor + (cy - 47) * s, n)
    if q.get("thrust"):
        g0, a0, u0, u1 = q["thrust"]
        q["thrust"] = ((ox + (g0[0] - 24) * s, floor + (g0[1] - 47) * s), a0, u0, u1)
    if q.get("chain"):
        q["chain"] = [(ox + (x - 24) * s, floor + (y - 47) * s) for (x, y) in q["chain"]]
    return q


def up(p, dy, dx=0.0):
    q = dict(p)
    for k in JOINTS:
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] - dy)
    return q


# =========================================================================== helpers
def tube(R, L, pts, radii, mat, bias=0, ao=1):
    m = set()
    for i in range(len(pts) - 1):
        m |= R.cap(L, pts[i], pts[i + 1], radii[i], radii[i + 1], mat, bias, ao=ao)
    return m


def rag(x0, x1, y, fi, seed, depth, sway=0.0, step=1.8):
    pts = []
    n = max(2, int(abs(x1 - x0) / step))
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        d = depth * (0.35 + hash01(i, fi // 2, seed)) if i % 2 == 0 else depth * 0.1
        pts.append((x + sway * t, y + d))
    return pts


def skull_head(R, L, G, s, eye_cols, jaw=0.0, glow=1.0, bone="B"):
    """A narrow skull (small, menacing): cranium dome, cheekbone, dark sockets with an eye-light, jaw."""
    L.paint(n_dome(R.T(G(0.4, -1.2)), 3.6 * s, 3.4 * s, flat=0.9, tilt=(-0.1, -0.1)), bone, 0, ao=0)
    face = [G(0.6, -1.0), G(3.9, -1.2), G(4.1, 1.2), G(3.1, 2.3), G(0.4, 2.4)]
    L.paint(n_plate(R.mask(face), 1.0 * s, (-0.2, 0.1)), bone, 0, ao=0)
    jw = [G(0.4, 2.0 + jaw), G(3.4, 2.1 + jaw), G(3.0, 3.8 + jaw), G(0.8, 3.6 + jaw)]
    L.paint(n_plate(R.mask(jw), 0.8 * s, (-0.1, 0.3)), bone, -1, ao=1)
    # sockets
    for (a, b) in ((2.5, -0.1),):
        e = R.T(G(a, b))
        L.fixed({ip(e): "OUT", (ip(e)[0] - 1, ip(e)[1]): "OUT", (ip(e)[0], ip(e)[1] + 1): "OUT"})
        if glow > 0:
            L.fixed({ip(e): eye_cols[0]})
    nose = R.T(G(3.6, 1.0))
    L.fixed({ip(nose): "B1"})
    teeth = R.T(G(2.2, 2.4 + jaw * 0.5))
    for k in range(3):
        L.fixed({(ip(teeth)[0] + k, ip(teeth)[1]): "B4" if k % 2 == 0 else "B1"})
    return R.T(G(2.5, -0.1))


# =========================================================================== the body
def draw_body(p, fi, sw, O):
    """Returns (layers dict, info). O = outfit."""
    Ls = {n: (FXLayer(n) if n in FXL else Layer(n)) for n in LAYERS}
    FX, FXB, CH = Ls["FX"], Ls["FXBack"], Ls["Chains"]
    R = Rig(p["rot"], p["piv"])
    s = O["s"]
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = K.basis(P, upv)
    info = {"hit": set(), "grip": None, "tip": None}
    floor = K.H - 1
    sw_ = sw * s
    # ------------------------------------------------ shoulders / hips
    shW = O.get("shoulder", 4.6) * s
    shF, shB = F(shW * 0.55, -ln + 1.2 * s), F(-shW * 0.75, -ln + 1.6 * s)
    hipF, hipB = F(1.6 * s, 0.6 * s), F(-1.8 * s, 0.8 * s)
    mats = O["mats"]
    # ------------------------------------------------ cape (behind everything)
    if O.get("cape") and p["cape_on"]:
        Cl = Ls["Cape"]
        cm = mats.get("cape", "H")
        cw, cl = O.get("cape_w", 11), O.get("cape_len", 13)
        hem = min(floor - 1, P[1] + cl * s) + min(0, p["lift"]) * 0.8
        fly = abs(p["lift"]) * 0.4 + max(0, p["wind"]) * 1.5
        back = P[0] - cw * s + sw_ * 1.2 - fly
        x0 = P[0] - 1.0 * s + sw_ * 0.3
        t1, t0 = F(shW * 0.35, -ln - 0.5 * s), F(-shW * 0.8, -ln + 0.4 * s)
        mid_back = (P[0] - cw * 0.55 * s + sw_ * 0.6 - fly * 0.5, P[1] - 7 * s)
        pts = [t1, F(-0.6 * s, -ln * 0.45), (x0, hem - 3 * s)]
        pts += rag(x0, back, hem, fi, 41, O.get("cape_rag", 3.4) * s, sway=0, step=1.6 * max(1, s * 0.7))
        pts += [(back - 0.3 * s, hem - cl * 0.35 * s), mid_back, lerp(t0, mid_back, 0.4), t0]
        m = R.mask(pts)
        for k in range(int(3 * s)):                      # holes in the tatters, low on the cloth
            hx = x0 + (back - x0) * (0.15 + 0.75 * hash01(k, 3, 7))
            hy = hem - (1.5 + hash01(k, 4, 7) * cl * 0.45) * s
            m -= mask_disc((hx, hy), 0.5 * s + 0.4, 0.8 * s + 0.4)
        Cl.paint(n_plate(m, 2.2 * s, (-0.1, 0.0), 1.0, fold=lambda x, y: (math.sin(x * 0.7 / s + sw) * 0.45, 0)), cm, 0)
        Cl.decal([q for q in m if int(q[0] + q[1] * 0.08 + sw_) % max(3, int(3.2 * s)) == 0 and hash01(q[0], q[1] // 3, 9) < 0.8], (cm, 1))
        info["cape"] = m
        if O.get("cape_trim"):
            ys = sorted(q[1] for q in m)
            Cl.decal([q for q in m if hash01(q[0], q[1], 5) < 0.07], (cm, 1))
    # ------------------------------------------------ weapon (grip in the front hand unless planted)
    wpn = O.get("weapon")
    hf, hb = R.T(p["hf"]), R.T(p["hb"])
    if wpn and p["weapon_on"]:
        wl = Ls[p["wl"]]
        info.update(draw_weapon(wl, FX, p, hb if p.get("whand") == "b" else hf, R.A(p["wang"]), O, fi))
    # ------------------------------------------------ back leg + back arm
    lg = O["leg"]
    mat_leg, mat_boot = mats.get("leg", "I"), mats.get("boot", "I")
    kb = K.leg(R, Ls["BackLeg"], hipB, p["fb"], lg[0] * s, lg[1] * s, lg[2] * s, lg[3] * s, mat_leg, -1, pref=(1, -0.1),
               boot=mat_boot, flen=2.6 * s, knee=p["kb"], boot_h=2.4 * s, heel=1.6 * s)
    am = O["arm"]
    Ba = Ls["BackArm"]
    back_hand = hb
    if p["grip2"] and wpn and p["weapon_on"] and O.get("two_hand") and info.get("grip2") and p.get("whand") != "b":
        back_hand = info["grip2"]
    elb = ik(R.T(shB), back_hand, am[0] * s, am[1] * s, (-1, 0.6))
    Ba.paint(n_capsule(R.T(shB), elb, am[2] * s, am[3] * s), mats.get("arm", "I"), -1)
    Ba.paint(n_capsule(elb, back_hand, am[3] * s, am[3] * s * 0.9), mats.get("fore", mats.get("arm", "I")), -1)
    Ba.paint(n_dome(back_hand, 1.2 * s, 1.1 * s), mats.get("hand", "I"), -1, ao=0)
    if O.get("pauldron"):
        Ba.paint(n_dome(R.T(add(shB, (0, -0.4 * s))), 2.6 * s, 2.0 * s, tilt=(-0.1, -0.3)), mats.get("pauldron", "X"), -1)
    info["hand_b"] = back_hand
    # ------------------------------------------------ torso
    Bd = Ls["Body"]
    tt = O.get("torso", "coat")
    hw = O.get("hip", 3.2) * s
    chest = [F(-shW, -ln + 0.8 * s), F(-shW * 0.55, -ln - 0.2 * s), F(shW * 0.45, -ln - 0.1 * s), F(shW * 0.82, -ln + 0.9 * s),
             F(shW * 0.72, -ln * 0.55), F(hw * 0.95, -ln * 0.28), F(hw, 0.8 * s), F(-hw * 1.05, 0.9 * s), F(-hw * 1.1, -ln * 0.3),
             F(-shW * 0.95, -ln * 0.6)]
    tm = R.mask(chest)
    Bd.paint(n_plate(tm, 2.0 * s, (-0.1, -0.05), 1.1), mats.get("torso", "I"), 0)
    tmat = mats.get("torso", "I")
    if tt == "plate":       # gorget, pectoral plates, centre ridge, fauld bands
        Bd.paint(n_dome(R.T(F(0.6 * s, -ln + 1.0 * s)), shW * 0.62, 1.8 * s, tilt=(-0.1, -0.35)), tmat, 1)
        for sx_ in (-1, 1):
            Bd.paint(n_dome(R.T(F(0.4 * s + sx_ * shW * 0.33, -ln * 0.62)), shW * 0.42, 2.4 * s, tilt=(-0.15 * sx_ - 0.1, -0.2)), tmat, 0, ao=1)
        R.dline(Bd, F(0.9 * s, -ln + 2.2 * s), F(0.5 * s, -1.2 * s), (tmat, 4))
        for k in range(3):
            y = -ln * (0.34 - k * 0.12)
            R.dline(Bd, F(-hw * 1.05, y), F(hw * 0.95, y - 0.1 * s), (tmat, 1))
        if O.get("emblem") == "skull":
            c = R.T(F(0.7 * s, -ln * 0.56))
            Bd.paint(n_dome(c, 1.7 * s, 1.5 * s, tilt=(-0.2, -0.2)), "B", 1, ao=1)
            for dx in (-0.55, 0.55):
                Bd.fixed({ip((c[0] + dx * s, c[1] - 0.1 * s)): "OUT"})
            Bd.fixed({ip((c[0], c[1] + 1.0 * s)): "B1"})
    # neck: vertebrae (skulls) or a collar, so the head never floats
    if O.get("head") in ("crown", "noble", "mitre"):
        hs_ = O.get("head_s", 1.0)
        nb = add(p["Hd"], (-p["hup"][0] * 2.8 * s * hs_, -p["hup"][1] * 2.8 * s * hs_))
        Bd.paint(n_capsule(R.T(F(0.3 * s, -ln + 0.5 * s)), R.T(nb), 0.8 * s, 0.7 * s), "B", -2, ao=0)
    if tt in ("coat", "robe", "plate", "apron"):
        # skirts: coat tails / robe / tassets
        sk = O.get("skirt", 7.5) * s
        skm = mats.get("skirt", mats.get("torso", "I"))
        spread = O.get("skirt_spread", 1.0)
        L_ = F(-hw * 1.1, 0.4 * s)
        R_ = F(hw * 1.05, 0.2 * s)
        hemL = (L_[0] - 2.0 * s * spread + sw_ * 0.5 - p["wind"] * 0.6, L_[1] + sk)
        hemR = (R_[0] + 1.5 * s * spread + sw_ * 0.2, R_[1] + sk * 0.92)
        sp = [L_, R_, hemR] + rag(hemR[0], hemL[0], (hemR[1] + hemL[1]) / 2, fi, 13, O.get("skirt_rag", 1.4) * s) + [hemL]
        sm = R.mask(sp)
        # split between the legs for coats/aprons
        if tt in ("coat", "plate"):
            mid = F(0.2 * s, 2.0 * s)
            sm -= poly_mask([mid, (mid[0] - 1.6 * s, hemL[1] + 3), (mid[0] + 1.6 * s, hemR[1] + 3)])
        Bd.paint(n_plate(sm, 1.4 * s, (-0.1, 0.1), 1.0, fold=lambda x, y: (math.sin(x * 0.8 / s) * 0.4, 0)), skm, 0)
        info["skirt"] = sm
    belt_y = 0.2 * s
    R.dline(Bd, F(-hw, belt_y), F(hw, belt_y - 0.2 * s), (mats.get("belt", "L"), 1))
    if O.get("belt_skull"):
        c = R.T(F(0.6 * s, 0.4 * s))
        Bd.paint(n_dome(c, 1.6 * s, 1.5 * s), "B", 0, ao=0)
        Bd.fixed({ip((c[0] - 0.5 * s, c[1])): "OUT", ip((c[0] + 0.6 * s, c[1])): "OUT"})
    if O.get("trim"):       # gold trim down the coat front + cuffs
        R.dline(Bd, F(1.2 * s, -ln + 1.6 * s), F(1.4 * s, 0.4 * s), (O["trim"], 3))
    if O.get("ruff"):       # lace ruff at the neck
        rc = R.T(F(0.4 * s, -ln - 0.4 * s))
        Bd.paint(n_dome(rc, 2.8 * s, 1.3 * s, flat=0.8), "P", 1, ao=0)
        for k in range(-2, 3):
            Bd.fixed({ip((rc[0] + k * 1.1 * s, rc[1] + 0.8 * s)): "P2"})
    # ------------------------------------------------ front leg
    kf = K.leg(R, Ls["FrontLeg"], hipF, p["ff"], lg[0] * s, lg[1] * s, lg[2] * s, lg[3] * s, mat_leg, 0, pref=(1, -0.1),
               boot=mat_boot, flen=2.8 * s, knee=p["kf"], boot_h=2.4 * s, heel=1.6 * s)
    if O.get("kneecop"):
        Ls["FrontLeg"].paint(n_dome(kf, 1.4 * s, 1.3 * s), O["kneecop"], 0, ao=0)
    # ------------------------------------------------ head
    Hl = Ls["Head"]
    Gb = K.basis(Hd, p["hup"])
    hs = O.get("head_s", 1.0)
    G = lambda a, b: Gb(a * s * hs, b * s * hs)
    htype = O["head"]
    eyes = O.get("eye_cols", ("U5", "U3"))
    eye_at = draw_head(R, Hl, FX, G, s, htype, eyes, p, fi, O)
    info["eye"] = eye_at
    info["head"] = R.T(G(1.0 * s, -1.0 * s))
    # ------------------------------------------------ front arm (over the weapon grip)
    Fa = Ls["FrontArm"]
    elf = ik(R.T(shF), hf, am[0] * s, am[1] * s, (-1, 0.5))
    Fa.paint(n_capsule(R.T(shF), elf, am[2] * s, am[3] * s), mats.get("arm", "I"), 0)
    Fa.paint(n_capsule(elf, hf, am[3] * s, am[3] * s * 0.95), mats.get("fore", mats.get("arm", "I")), 0)
    if O.get("vambrace"):
        Fa.paint(n_capsule(lerp(elf, hf, 0.3), lerp(elf, hf, 0.85), am[3] * s * 1.15, am[3] * s * 1.1), O["vambrace"], 0, ao=0)
    Fa.paint(n_dome(hf, 1.3 * s, 1.2 * s), mats.get("hand", "I"), 0, ao=0)
    if O.get("pauldron"):
        Fa.paint(n_dome(R.T(add(shF, (-0.3 * s, -0.6 * s))), 2.9 * s, 2.3 * s, tilt=(-0.1, -0.35)), mats.get("pauldron", "X"), 0)
        if O.get("pauldron_spikes"):
            base = R.T(add(shF, (-0.8 * s, -2.6 * s)))
            for k, (dx, h) in enumerate(((-1.2, 3.0), (0.4, 4.2), (1.8, 2.6))):
                a = (base[0] + dx * s, base[1])
                t = (base[0] + dx * s + 0.6 * s, base[1] - h * s)
                Fa.paint(n_capsule(a, t, 0.8 * s, 0.25 * s), "B", 0, ao=0)
    info["hand_f"] = hf
    info["shoulder_f"] = R.T(shF)
    info["chest"] = R.T(C)
    # ------------------------------------------------ spectral wrist chains
    if O.get("chains"):
        for hand, k in ((hf, 0), (back_hand, 1)):
            cuff = mask_disc(hand, 1.7 * s, 1.0 * s)
            CH.put(cuff, "U3")
            pts = p["chain"] if (p["chain"] and k == 0) else None
            if pts:
                draw_chain(CH, [hand] + list(pts), s)
            else:
                # dangling loose loops, swaying
                a = (hand[0] - 2 * s - sw_ * 0.6, hand[1] + 6 * s)
                b = (hand[0] + (2 if k else -3) * s - sw_, hand[1] + 11 * s + hash01(fi, k, 3))
                draw_chain(CH, [hand, a, b], s, dim=True)
    # ------------------------------------------------ iron shackles with broken chains (executioners)
    if O.get("shackles"):
        for hand, k in ((hf, 0), (back_hand, 1)):
            cuff = R.T(hand) if False else hand
            Fa_ = Ls["FrontArm"] if k == 0 else Ls["BackArm"]
            Fa_.paint(n_capsule((cuff[0] - 1.2 * s, cuff[1] - 1.6 * s), (cuff[0] - 1.2 * s, cuff[1] + 0.6 * s), 1.3 * s, 1.3 * s), "Z", 0, ao=0)
            L = O["shackles"]
            if p.get("chain") and k == 0:
                pts = [hand] + list(p["chain"])
            else:
                a = (hand[0] - 2.5 * s - sw_ * 0.8, hand[1] + L * 0.5 * s)
                b = (hand[0] - (4.0 if k else 1.0) * s - sw_ * 1.4, hand[1] + L * s)
                pts = [hand, a, b]
            q = polyline(pts)
            for i, c in enumerate(q):
                CH.put([c], ("I4", "I2", "I3")[i % 3])
                if i % 3 == 1:
                    CH.put([(c[0] + 1, c[1])], "I1")
    # ------------------------------------------------ glows + smears
    if p["smear"]:
        for sm in p["smear"]:
            g0, a0, g1, a1, u0, u1 = sm[:6]
            pal = sm[6] if len(sm) > 6 else O.get("smear", "bone")
            u0 = max(u0, u1 * O.get("smear_in", 0.5))
            info["hit"] |= swept(FX, R.T(g0), R.A(a0), R.T(g1), R.A(a1), u0 * s, u1 * s, hw=1.2 * s, pal=pal, taper=0.65)
    if p["thrust"]:
        g0, a0, u0, u1 = p["thrust"]
        info["hit"] |= K.thrust_lines(FX, R.T(g0), R.A(a0), u0 * s, u1 * s, (-1.5 * s, 0, 1.5 * s), pal=O.get("smear", "steel"),
                                     flash=u1 - 1)
    if p["fire"] > 0:
        c = info.get("hand_b") if p.get("fire_hand") == "b" else hf
        ghost_flame(FX, (c[0], c[1] - 1), 2.2 * s * p["fire"], fi)
    if p["sparks"]:
        cx, cy, n = p["sparks"]
        for k in range(n):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 1, 13))
            r = (2 + 7 * hash01(k, 2, 13)) * s
            FX.put([ip((cx + math.cos(a) * r * 1.3, cy + math.sin(a) * r * 0.6))], ("U5", "U4", "U3")[k % 3])
    if p["dust"]:
        for k in range(10 * p["dust"]):
            x = P[0] + (hash01(k, 1, 9) - 0.5) * 30 * s
            y = floor - hash01(k, 2, 9) * 4 * s
            FX.put([ip((x, y))], ("B3", "B2", "Z4")[k % 3])
    return Ls, info


def draw_chain(L, pts, s, dim=False):
    """A spectral chain along a polyline (links alternate bright/dim)."""
    q = polyline(pts)
    for i, c in enumerate(q):
        if i % 3 == 0:
            L.put([c], "U4" if not dim else "U3")
        elif i % 3 == 1:
            L.put([c], "U2")
            L.put([(c[0], c[1] - 1)], "U1" if dim else "U3")
        else:
            L.put([c], "U3" if not dim else "U2")


def ghost_flame(FX, base, size, fi, seed=0):
    bx, by = base
    hgt = size * 1.9
    for y in range(int(by - hgt) - 1, int(by) + 2):
        t = (by - (y + .5)) / hgt
        if t < -0.1 or t > 1:
            continue
        wob = math.sin(fi * 1.9 + t * 5 + seed) * 0.8 * t
        half = size * 0.55 * max(0.0, 1 - t) ** 0.7 + 0.3
        for x in range(int(bx - half - 2), int(bx + half + 2)):
            dx = x + .5 - (bx + wob)
            if abs(dx) <= half:
                r = abs(dx) / max(half, 0.5) * 0.6 + t * 0.7
                if hash01(x, y, fi + seed) < 0.15 * t:
                    continue
                FX.put([(x, y)], "U5" if r < 0.35 else "U4" if r < 0.6 else "U3" if r < 0.85 else "U2" if r < 1.05 else "U1")


# =========================================================================== heads
def draw_head(R, Hl, FX, G, s, htype, eyes, p, fi, O):
    glow = p["eye"]
    if htype == "noble":        # skull under a powdered, ribbon-tied queue wig (ghostly-grey), gaunt
        at = skull_head(R, Hl, G, s, eyes, p["jaw"], glow)
        wig = [G(-3.6, -3.8), G(0.8, -4.6), G(3.2, -3.4), G(2.2, -1.8), G(-0.4, -1.6), G(-1.8, 1.2), G(-3.2, 3.6),
               G(-4.4, 2.0)]
        Hl.paint(n_plate(R.mask(wig), 1.2 * s, (-0.2, -0.3), 1.1), "P", 1, ao=0)
        q = R.T(G(-4.2, 2.8))
        Hl.paint(n_dome(q, 1.1 * s, 1.6 * s), "P", 0, ao=0)
        Hl.fixed({ip(R.T(G(-3.6, 1.4))): "H3", ip(R.T(G(-3.9, 1.9))): "H4"})
        return at
    if htype == "hood":         # deep cowl; only the skull's jaw and one eye-light show
        hood = [G(-4.4, 3.8), G(-4.6, -1.4), G(-2.8, -5.0), G(0.6, -6.2), G(3.4, -4.4), G(5.0, -1.4), G(5.2, 1.8),
                G(3.4, 3.2), G(1.0, 4.6)]
        Hl.paint(n_plate(R.mask(hood), 1.6 * s, (-0.15, -0.2), 1.1), O["mats"].get("hood", "M"), 0)
        face = [G(1.6, -1.6), G(4.0, -1.2), G(4.2, 2.2), G(2.2, 3.2)]
        fm = R.mask(face)
        Hl.paint(n_plate(fm, 0.6 * s), O["mats"].get("hood", "M"), -3, ao=0)
        jaw = [G(2.0, 0.8), G(4.3, 0.9), G(4.0, 2.6), G(2.4, 3.0)]
        Hl.paint(n_plate(R.mask(jaw), 0.7 * s, (-0.2, 0.2)), "B", 0, ao=0)
        Hl.fixed({ip(R.T(G(3.0, 2.0))): "B1", ip(R.T(G(3.8, 2.0))): "B1"})
        e = R.T(G(3.0, -0.2))
        Hl.fixed({ip(e): eyes[0] if glow > 0 else "OUT", (ip(e)[0] + 1, ip(e)[1]): eyes[1] if glow > 0 else "OUT"})
        return e
    if htype == "exec":         # executioner: pointed leather hood with eye-slits over a heavy jaw
        hood = [G(-3.8, 4.2), G(-4.4, -0.6), G(-3.4, -4.2), G(-1.2, -7.4), G(0.6, -9.6), G(2.2, -6.4), G(4.4, -3.0),
                G(4.8, 1.0), G(4.2, 3.4), G(1.0, 4.8)]
        Hl.paint(n_plate(R.mask(hood), 1.5 * s, (-0.15, -0.2), 1.1), O["mats"].get("hood", "E"), 0)
        for dx in (1.8, 3.6):
            e = R.T(G(dx, -0.6))
            Hl.fixed({ip(e): "OUT", (ip(e)[0] + 1, ip(e)[1]): "OUT"})
            if glow > 0:
                Hl.fixed({ip(e): eyes[0]})
        # stitched seam
        R.dline(Hl, G(0.4, -7.0), G(1.2, 3.0), ("E", 1))
        return R.T(G(3.6, -0.6))
    if htype == "crown":        # King Vael: a skull fused into a spiked crown of corroded gold, blue fire in the sockets
        hs_ = O.get("head_s", 1.0)
        k = s * hs_
        Hl.paint(n_dome(R.T(G(0.2, -1.4)), 3.0 * k, 2.8 * k, flat=0.9, tilt=(-0.15, -0.1)), "B", 0, ao=0)
        face = [G(0.4, -1.0), G(3.3, -1.1), G(3.8, 0.4), G(3.7, 1.7), G(2.6, 2.3), G(0.2, 2.2)]
        Hl.paint(n_plate(R.mask(face), 0.9 * k, (-0.2, 0.05)), "B", 0, ao=0)
        jw = [G(0.5, 2.0 + p["jaw"]), G(3.1, 2.1 + p["jaw"]), G(2.8, 3.3 + p["jaw"]), G(0.9, 3.2 + p["jaw"])]
        Hl.paint(n_plate(R.mask(jw), 0.7 * k, (-0.1, 0.3)), "B", -1, ao=1)
        for q in line(R.T(G(1.2, 2.15 + p["jaw"] * 0.5)), R.T(G(3.2, 2.1 + p["jaw"] * 0.5))):
            Hl.decal([q], "B1" if q[0] % 2 else "B5")
        Hl.decal(line(R.T(G(0.6, 1.2)), R.T(G(2.2, 1.9))), ("B", 2))          # cheekbone shadow
        sock = R.mask([G(2.0, -0.4), G(3.5, -0.3), G(3.3, 0.9), G(2.1, 0.8)])
        Hl.decal(sock, "OUT")
        Hl.fixed({ip(R.T(G(3.4, 1.2))): "B1"})
        band = R.mask([G(-2.9, -2.7), G(3.1, -2.8), G(3.3, -1.6), G(-2.8, -1.5)])
        Hl.paint(n_plate(band, 0.8 * k, (-0.1, -0.5)), "X", 0, ao=1)
        for (dx, h) in ((-2.3, 2.0), (-0.9, 3.2), (0.5, 4.6), (1.9, 3.2), (3.0, 2.0)):
            b0 = R.T(G(dx, -2.6))
            t = R.T(G(dx + 0.15 * dx / 3.0, -2.6 - h * p["crown"]))
            Hl.paint(n_capsule(b0, t, 0.6 * k, 0.15 * k), "X", 1, ao=0)
            if p.get("blaze", 0) > 0:
                ghost_flame(FX, t, 1.0 * k * p["blaze"], fi, seed=int(dx * 3 + 5))
        gem = R.T(G(0.4, -2.2))
        Hl.fixed({ip(gem): "U5", (ip(gem)[0] + 1, ip(gem)[1]): "U3"})
        e = R.T(G(2.8, 0.2))
        if glow > 0:
            Hl.fixed({ip(e): "U5", (ip(e)[0] + 1, ip(e)[1]): "U4", (ip(e)[0], ip(e)[1] + 1): "U3"})
            for j in range(int(2 + 2.5 * glow)):      # ghost-fire streaming back from the socket
                FX.put([ip((e[0] - 1 - j * 0.9, e[1] - 1 - j * 0.55 + (j % 2) * 0.4))], "U5" if j < 1 else "U4" if j < 3 else "U3")
        return e
    if htype == "helm":         # spectral knight: tall sallet with a narrow visor slit
        helm = [G(-3.4, 3.0), G(-3.8, -2.0), G(-2.2, -4.6), G(1.2, -5.2), G(3.8, -3.2), G(4.6, 0.2), G(4.2, 2.4),
                G(1.0, 3.6)]
        Hl.paint(n_plate(R.mask(helm), 1.3 * s, (-0.15, -0.25), 1.2), O["mats"].get("helm", "K"), 0)
        R.dline(Hl, G(1.0, -0.6), G(4.4, -0.8), "OUT")
        e = R.T(G(3.4, -0.7))
        Hl.fixed({ip(e): eyes[0]})
        crest = [G(-2.0, -4.6), G(0.8, -7.0), G(1.4, -5.0)]
        Hl.paint(n_plate(R.mask(crest), 0.6 * s), O["mats"].get("helm", "K"), 1, ao=0)
        return e
    if htype == "mitre":        # spectral priest: a tall mitre over a veiled skull
        at = skull_head(R, Hl, G, s, eyes, p["jaw"], glow)
        mitre = [G(-3.0, -2.0), G(-2.2, -7.4), G(0.4, -9.4), G(2.8, -7.4), G(3.4, -2.2)]
        Hl.paint(n_plate(R.mask(mitre), 1.0 * s, (-0.1, -0.3)), O["mats"].get("hood", "P"), 1, ao=0)
        R.dline(Hl, G(0.3, -8.6), G(0.3, -2.4), ("X", 3))
        veil = [G(-3.6, -1.6), G(-4.4, 4.0), G(-2.0, 4.6), G(-1.0, 0.0)]
        Hl.paint(n_plate(R.mask(veil), 0.8 * s), O["mats"].get("hood", "P"), 0, ao=0)
        return at
    return R.T(G(2, 0))


# =========================================================================== weapons
def draw_weapon(L, FX, p, grip, ang, O, fi):
    s = O["s"]
    kind = O["weapon"]
    out = {}
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    if kind == "rapier":
        spec = dict(pommel=-3.2 * s, grip_end=0.4, grip="L2", grip_w=0.6, pommel_c="X4", guard=(0.2, 1.4, 2.6 * s),
                    guard_c="X2", guard_hi="X4", b0=1.4, end=20 * s, w_edge=0.5, w_spine=0.4, taper=0.3,
                    edge_hi="B5", edge="I4", spine="I3")
        pix, blade, tip = blade_px(ID, grip, ang, spec)
        # cup-hilt ring
        for q in mask_disc((grip[0] + ca * 0.8, grip[1] + sa * 0.8), 1.8 * s, 1.8 * s):
            if q not in pix and hash01(q[0], q[1], 2) < 0.55:
                pix[q] = "X3"
        L.fixed(pix)
        out.update(tip=tip, blade=blade)
    elif kind in ("greatsword",):     # Vael's bone greatsword: a spine-ridged blade of fused bone, jagged edge
        blen = O.get("blade", 30) * s
        spec = dict(pommel=-5.5 * s, grip_end=0.8, grip="L1", grip_w=0.9 * s, pommel_c="B4", guard=(0.4, 2.6, 4.2 * s),
                    guard_c="X2", guard_hi="X4", b0=2.6, end=blen, w_edge=1.9 * s, w_spine=1.5 * s, taper=0.14,
                    edge_hi="B5", edge="B4", spine="B2", fuller="B3")
        pix, blade, tip = blade_px(ID, grip, ang, spec)
        for q in list(pix):
            u = (q[0] + .5 - grip[0]) * ca + (q[1] + .5 - grip[1]) * sa
            v = -(q[0] + .5 - grip[0]) * sa + (q[1] + .5 - grip[1]) * ca
            if pix[q] == "B3":                            # vertebrae ridge along the fuller
                pix[q] = "B5" if int(u / (1.6 * s)) % 2 else "B2"
            if u > 3 and v > 1.1 * s and int(u) % 5 == 0:
                pix[q] = "B1"                             # notches in the edge
            if 3 < u < 9 * s and abs(v) < 1.2 * s and hash01(q[0], q[1], 8) < 0.2:
                pix[q] = "C3"                             # old blood-red wrap bleeding onto the ricasso
        L.fixed(pix)
        out.update(tip=tip, blade=blade)
    elif kind == "axe":             # executioner's greataxe: long haft, crescent head with a back spike
        hl = O.get("haft", 22) * s
        pts = polyline([(grip[0] - ca * 4 * s, grip[1] - sa * 4 * s), (grip[0] + ca * hl, grip[1] + sa * hl)])
        pix = {}
        for i, q in enumerate(pts):
            pix[q] = "W3" if i % 5 else "W1"
            nq = (q[0] + int(round(-sa)), q[1] + int(round(ca)))
            pix.setdefault(nq, "W2")
        head_c = (grip[0] + ca * (hl - 3 * s), grip[1] + sa * (hl - 3 * s))
        nx, ny = -sa, ca                      # blade side (below the haft when pointing right)
        blade = set()
        hw = O.get("axe_w", 8.5) * s
        for y in range(int(head_c[1] - hw * 1.6), int(head_c[1] + hw * 1.6) + 1):
            for x in range(int(head_c[0] - hw * 1.6), int(head_c[0] + hw * 1.6) + 1):
                dx, dy = x + .5 - head_c[0], y + .5 - head_c[1]
                u = dx * ca + dy * sa
                v = dx * nx + dy * ny
                if -3.2 * s < u < 3.2 * s + 0.0 and 0 < v < hw and abs(u) < 3.2 * s * (0.55 + 0.45 * (v / hw) ** 0.5) + (v / hw) * 1.8 * s:
                    edge = v > hw - 1.3
                    c = "B5" if edge else "Z4" if u < -0.8 * s else "Z3" if u < 1.2 * s else "Z2"
                    if not edge and hash01(x, y, 4) < 0.08:
                        c = "R2"                  # rust
                    pix[(x, y)] = c
                    blade.add((x, y))
                if -1.4 * s < u < 1.4 * s and -3.6 * s < v < 0 and abs(u) < 1.4 * s * (1 + v / (3.6 * s)):
                    pix[(x, y)] = "Z3"            # back spike
        L.fixed(pix)
        out.update(tip=head_c, blade=blade, grip2=(grip[0] + ca * 6.5 * s, grip[1] + sa * 6.5 * s))
    elif kind == "bell":            # a bone-bell on a short haft (the ringer)
        hl = 7 * s
        pts = polyline([grip, (grip[0] + ca * hl, grip[1] + sa * hl)])
        pix = {q: "W3" for q in pts}
        bc = (grip[0] + ca * hl, grip[1] + sa * hl)
        blade = set()
        for y in range(int(bc[1] - 7 * s), int(bc[1] + 7 * s) + 1):
            for x in range(int(bc[0] - 7 * s), int(bc[0] + 7 * s) + 1):
                dx, dy = x + .5 - bc[0], y + .5 - bc[1]
                u = dx * ca + dy * sa
                v = -dx * sa + dy * ca
                if 0 <= u <= 6 * s:
                    half = (1.6 + 2.8 * (u / (6 * s)) ** 1.6) * s
                    if abs(v) <= half:
                        c = "N3" if v < -half * 0.3 else "N2" if v < half * 0.4 else "N1"
                        if u > 5.2 * s:
                            c = "B4"
                        pix[(x, y)] = c
                        blade.add((x, y))
        if p.get("bell_ring", 0) > 0:
            for k in range(3):
                r = (6 + k * 3) * s * p["bell_ring"]
                for t in range(0, 360, 20):
                    a = math.radians(t)
                    FX.put([ip((bc[0] + ca * 6 * s + math.cos(a) * r, bc[1] + sa * 6 * s + math.sin(a) * r))], ("U5", "U4", "U3")[k])
        L.fixed(pix)
        out.update(tip=bc, blade=blade)
    elif kind == "sword":           # spectral knight's longsword
        spec = dict(pommel=-3.5 * s, grip_end=0.6, grip="L2", grip_w=0.7, pommel_c="I4", guard=(0.4, 1.6, 3.2 * s),
                    guard_c="I3", guard_hi="I5", b0=1.6, end=17 * s, w_edge=0.9 * s, w_spine=0.8 * s, taper=0.22,
                    edge_hi="B5", edge="I4", spine="I3", fuller="I2")
        pix, blade, tip = blade_px(ID, grip, ang, spec)
        L.fixed(pix)
        out.update(tip=tip, blade=blade)
    elif kind == "censer":          # spectral priest's censer staff: staff + hanging censer of ghost-fire
        hl = 18 * s
        a = (grip[0] - ca * 8 * s, grip[1] - sa * 8 * s)
        b = (grip[0] + ca * hl, grip[1] + sa * hl)
        pix = {q: "X3" for q in polyline([a, b])}
        for q in polyline([(a[0] + 1, a[1]), (b[0] + 1, b[1])]):
            pix.setdefault(q, "X1")
        cen = (b[0], b[1] + 5 * s)
        for q in polyline([b, cen]):
            pix[q] = "X2"
        for q in mask_disc(cen, 2.0 * s, 2.2 * s):
            pix[q] = "X3" if q[0] < cen[0] else "X1"
        L.fixed(pix)
        ghost_flame(FX, (cen[0], cen[1] - 1.5 * s), 1.2 * s, fi)
        out.update(tip=cen, blade=set())
    out["grip"] = grip
    return out


# =========================================================================== post: spectral recolour
def ghostify(imgs, names, keep_fx=True):
    """Recolour the named layers into the spectral palette by luminance (outline -> deep blue)."""
    S = [K.RGBA[k] for k in K.RAMP["S"]]
    out = dict(imgs)
    for n in names:
        if n not in imgs:
            continue
        src = imgs[n]
        im = Image.new("RGBA", src.size, (0, 0, 0, 0))
        sp, dp = src.load(), im.load()
        for y in range(src.size[1]):
            for x in range(src.size[0]):
                r, g, b, a = sp[x, y]
                if not a:
                    continue
                lum = (0.3 * r + 0.55 * g + 0.15 * b) / 255
                if lum < 0.07:
                    dp[x, y] = (10, 22, 52, 255)
                    continue
                i = min(5, int(math.sqrt(lum) * 6.2))
                dp[x, y] = S[i]
        out[n] = im
    return out
