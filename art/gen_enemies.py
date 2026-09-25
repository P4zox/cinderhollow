#!/usr/bin/env python3
"""Enemy generator -- spec section 4 (docs/ART_SPEC.md).

    python3 art/gen_enemies.py                      build every enemy + projectile (Aseprite)
    python3 art/gen_enemies.py --preview            previews + meta only (no Aseprite)
    python3 art/gen_enemies.py --only hollow_soldier,rot_crawler [--preview]

Outputs per enemy <name>:
    art/<name>.aseprite, assets/<name>.png + .json, assets/<name>_meta.json,
    art/previews/<name>.png (4x, one row per tag), art/previews/<name>_hitbox.png (debug overlay)
Projectiles: proj_arrow (16x8, fly 2), proj_fireball (16x16, fly 4 loop).

All creatures face RIGHT, feet on the bottom row (gloom_wisp floats; anchor = body centre).
Method + helpers live in enemy_kit.py (normal-field shading, sel-out outline, Rig with rotation).
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, leg, arm, blade_px, swept,
                       speed_lines, thrust_lines, rot_pt, dirv, bbox, flame)

BUILD = "--preview" not in sys.argv


# =========================================================================== generic driver
SPEC_FRAMES = {   # docs/ART_SPEC.md section 4
    "hollow_soldier": dict(idle=4, walk=6, attack=8, hurt=2, death=6),
    "shield_warden": dict(idle=4, walk=6, guard=2, bash=9, hurt=2, death=6),
    "rot_crawler": dict(idle=4, crawl=6, lunge=7, hurt=2, death=6),
    "gloom_wisp": dict(fly=6, dive=6, hurt=2, death=6),
    "hollow_archer": dict(idle=4, walk=6, shoot=9, hurt=2, death=6),
    "ember_acolyte": dict(idle=4, walk=6, cast=10, blink=6, hurt=2, death=6),
    "grave_knight": dict(idle=4, walk=6, combo=12, slam=10, hurt=2, death=8),
}


def render_anims(layers, draw, anims, sway_key="C", loops=("idle", "walk", "fly", "guard", "crawl")):
    out, infos = [], {}
    for tag, fn in anims:
        fr = fn()
        spec = [d for d in SPEC_FRAMES.values() if list(d) == [t for t, _ in anims]]
        assert spec and spec[0][tag] == len(fr), (tag, len(fr))
        drv = [p[sway_key][0] if isinstance(p[sway_key], tuple) else p[sway_key] for _, p in fr]
        sway = K.spring(drv, loop=tag in loops, extra=[p.get("wind", 0.0) for _, p in fr])
        lst, inf = [], []
        for k, (ms, p) in enumerate(fr):
            Ls, info = draw(p, k, sway[k])
            imgs = {}
            for n in layers:
                v = Ls.get(n)
                if v is None:
                    continue
                imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
            if p.get("post"):
                imgs = p["post"](imgs)
            if p.get("snap"):
                box = K.opaque_bbox(imgs, p["snap"])
                if box and box[3] != K.H:
                    dy = K.H - box[3]
                    imgs = K.shift_imgs(imgs, 0, dy, p["snap"])
                    info["hit"] = {(x, y + dy) for (x, y) in info.get("hit", set())}
            lst.append((ms, imgs))
            inf.append(info)
        out.append((tag, lst))
        infos[tag] = inf
    return out, infos


def hit_rect(infos, tag, ks, floor=True, min_w=0, x_min=None):
    pts = set()
    for k in ks:
        pts |= infos[tag][k].get("hit", set())
    r = bbox(pts)
    if x_min is not None and r[0] < x_min:
        r[2] -= x_min - r[0]; r[0] = x_min
    if floor:
        r[3] = K.H - r[1]
    return r


def hurtbox(anims, names, inset=(1, 0, 1)):
    imgs = anims[0][1][0][1]
    b = K.opaque_bbox(imgs, names)
    x0, y0, x1, y1 = b
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2], K.H - (y0 + inset[1])]


def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def rag_hem(x0, x1, y, fi, seed, depth=2.5, sway=0.0):
    """Ragged cloth hem: list of polygon points from x1 back to x0 along y (teeth hang down)."""
    pts = []
    n = max(2, int((x1 - x0) / 1.6))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = depth * (0.3 + hash01(i, fi // 2, seed)) if i % 2 == 0 else depth * 0.15
        pts.append((x + sway * (0.4 + 0.6 * t), y + d))
    return pts


# =========================================================================== 1. HOLLOW SOLDIER
SOLDIER_L = ["BackArm", "BackLeg", "Body", "FrontLeg", "Cloth", "Head", "Weapon", "FrontArm", "FX"]
S_SWORD = dict(pommel=-2.6, grip_end=0.4, grip="L2", pommel_c="I3", guard=(0.5, 1.5, 2.6), guard_c="I2",
               guard_hi="I4", b0=1.6, end=13.5, w_edge=1.25, w_spine=0.85, broken=True,
               edge_hi="I5", edge="I4", spine="I2")
S_NEU = dict(P=(18.0, 26.5), C=(19.3, 19.5), Hd=(21.2, 13.6), hup=(0.2, -1), fb=(14.5, 39), ff=(22.0, 39),
             hb=(16.0, 28.5), hf=(25.0, 27.5), wang=66, rot=0.0, piv=(0, 0), eye=1, sword="hand",
             kb=None, kf=None, legs_fixed=False, smear=None, wind=0.0)
SP = mk(S_NEU)


def draw_soldier(p, fi, sw):
    Ls = {n: Layer(n) for n in SOLDIER_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    LR = ID if p["legs_fixed"] else R
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(0.9, -ln + 0.9), F(-1.4, -ln + 1.1)
    hB, hF = F(-1.1, 0.4), F(1.1, 0.4)
    if p["legs_fixed"]:
        hB, hF = R.T(hB), R.T(hF)
    # ---- back arm (limp)
    arm(R, Ls["BackArm"], shB, p["hb"], 4.6, 4.8, 1.5, 1.25, "L", bias=-1, fore="A", fist_r=1.1)
    # ---- legs
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(LR, Ls[nm], hip, ft, 6.3, 6.4, 1.7, 1.35, "T", bias=bias - 1, boot="L", flen=2.6, heel=1.3,
                boot_h=2.3, knee=kn)
        LR.dome(Ls[nm], add(k, (0.3, 0)), 1.5, 1.4, "I", bias=bias)       # rusty knee-cop
        LR.decal(Ls[nm], [add(k, (0.2, -0.4))], ("R", 3 + bias))
    # ---- torso: rusted mail under a ragged olive tabard
    Bd = Ls["Body"]
    torso = [F(-3.2, 0.9), F(-3.8, -ln + 2.6), F(-2.5, -ln - 0.9), F(1.6, -ln - 1.3), F(3.4, -ln + 1.0),
             F(3.1, -2.5), F(2.6, 0.9)]
    tm = R.plate(Bd, torso, "I", bevel=2.0, tilt=(-0.2, -0.1), bias=-1)
    Bd.decal([q for q in tm if (q[0] + (q[1] % 2)) % 2 == 0 and q[1] % 2 == 0], ("I", 1))
    tab = [F(0.2, -ln - 0.6), F(2.0, -ln - 1.0), F(3.7, -ln + 1.2), F(3.4, 0.4), F(0.6, 0.4)]
    tb = R.plate(Bd, tab, "T", bevel=1.3, tilt=(-0.35, -0.1), strength=1.1)
    Bd.decal([q for q in tb if hash01(q[0] - int(P[0]), q[1] - int(P[1]), 3) < 0.12], ("T", 1))
    R.decal(Bd, [F(2.0, -ln + 3.2), F(2.0, -ln + 4.2), F(1.2, -ln + 3.6), F(2.8, -ln + 3.6)], ("G", 1))
    R.dline(Bd, F(-3.4, -0.5), F(3.4, -0.5), ("L", 1))
    R.decal(Bd, [F(2.6, -0.5)], ("G", 2))
    # neck (dry sinew)
    R.cap(Bd, F(0.6, -ln - 0.3), add(Hd, (-0.6, 2.4)), 1.0, 0.9, "A", bias=-1)
    # ---- ragged tabard skirt (secondary sway)
    Cl = Ls["Cloth"]
    bl, br = F(-2.2, -0.2), F(3.6, -0.2)
    if not p["legs_fixed"] and abs(p["rot"]) < 1:
        ybot = max(bl[1], br[1]) + 4.2
        sx = -sw * 0.7
        pts = [bl, br, (br[0] + 1.0 + sx * 0.4, br[1] + 2.5)] + \
              rag_hem(bl[0] - 0.6 + sx * 0.2, br[0] + 1.4 + sx * 0.6, ybot, fi, 7, 2.6) + \
              [(bl[0] - 0.8 + sx * 0.2, bl[1] + 2.0)]
        m = R.mask(pts)
        Cl.paint(n_plate(m, 1.4, (0.05, 0.05), 0.9, fold=lambda x, y: (0.6 * math.sin((x - P[0] + sw * 0.3) * 1.4), 0)),
                 "T", bias=0)
        Cl.decal([q for q in m if hash01(q[0], q[1], 9) < 0.1], ("T", 1))
    else:
        pts = [bl, br, F(4.2, 3.2), F(2.0, 4.6), F(-0.2, 3.6), F(-2.6, 4.0)]
        R.plate(Cl, pts, "T", bevel=1.4, tilt=(0.1, 0.05))
    # ---- head: dented kettle-helm with a wide droopy brim, hollow face with one ember eye
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    R.dome(Hl, G(0.8, 1.0), 2.2, 2.5, "A", bias=-1)
    R.decal(Hl, [G(2.0, 2.8), G(1.2, 3.0)], ("B", 2))
    crown = [G(-3.0, 0.2), G(-3.2, -2.1), G(-1.9, -3.8), G(0.4, -4.3), G(2.3, -3.6), G(3.2, -1.9), G(3.1, 0.2)]
    cm = R.plate(Hl, crown, "I", bevel=1.6, tilt=(-0.15, -0.25), strength=1.3)
    Hl.decal([q for q in cm if hash01(q[0] - int(Hd[0]), q[1] - int(Hd[1]), 5) < 0.18], ("R", 2))
    R.decal(Hl, [G(-1.3, -3.1), G(-0.5, -3.4)], ("I", 0))        # the dent
    R.decal(Hl, [G(-1.0, -2.3), G(-0.2, -2.5)], ("I", 4))
    brim = [G(-5.2, -0.4), G(-1, -0.7), G(5.4, -1.0), G(6.1, 0.2), G(4.6, 1.0), G(-3.4, 1.3), G(-5.5, 1.1)]
    R.plate(Hl, brim, "I", bevel=0.9, tilt=(0.0, -0.6), strength=1.0)
    R.decal(Hl, [G(5.8, 0.5), G(-5.2, 0.8)], ("R", 3))
    if p["eye"]:
        e = R.pt(G(2.3, 1.2))
        FX.put([e], "O4" if p["eye"] == 1 else "O5")
        if p["eye"] > 1:
            FX.put([(e[0] + 1, e[1]), (e[0] + 2, e[1] - 1)], "O3")
    # ---- near arm + pauldron
    Fa = Ls["FrontArm"]
    hold = p["sword"] == "hand"
    arm(R, Fa, shF, p["hf"], 4.6, 4.8, 1.6, 1.35, "L", bias=0, fore="A", fist_r=1.3)
    pm = R.dome(Fa, add(shF, (-0.2, -0.4)), 2.5, 2.1, "I", tilt=(0.0, -0.15))
    Fa.decal([q for q in pm if hash01(q[0], q[1], 6) < 0.2], ("R", 2))
    # ---- weapon
    info = {"hit": set()}
    if hold:
        pix, blade, tip = blade_px(R, p["hf"], p["wang"], S_SWORD)
    else:
        g, a = p["sword"]
        pix, blade, tip = blade_px(ID, g, a, S_SWORD)
    ca, sa = dirv(R.A(p["wang"] if hold else p["sword"][1]))
    g0 = R.T(p["hf"]) if hold else p["sword"][0]
    for q in blade:   # a couple of rust blooms near the break and the guard
        u = (q[0] + .5 - g0[0]) * ca + (q[1] + .5 - g0[1]) * sa
        if pix[q] != S_SWORD["edge_hi"] and (6.5 < u < 8.0 or u > 11.8):
            pix[q] = "R2" if u > 11.8 else "R3"
    Ls["Weapon"].fixed(pix)
    info["hit"] |= blade
    if p["smear"]:
        sm = p["smear"]
        hot = swept(FX, R.T(sm["g0"]), sm["a0"], R.T(p["hf"]), R.A(p["wang"]), 4, S_SWORD["end"] + 0.5, hw=0.8,
                    mid=sm.get("mid"), start=sm.get("start", 0.0), pal="bone", exclude=blade,
                    taper=sm.get("taper", 0.7), clip_y=K.H - 1)
        info["hit"] |= hot
    return Ls, info


def s_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((200, SP(P=(18, 26.5 + b * 0.5), C=(19.3, 19.5 + b), Hd=(21.2 + b * 0.3, 13.6 + b * 1.1),
                           hb=(16.2, 28.5 + b), hf=(25, 27.5 + b * 0.7), wang=66 + b * 3)))
    return fr


def s_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        ff = (18.5 + 4.6 * c, 39 - max(0.0, -s) * 2.6)
        fb = (18.0 - 4.6 * c, 39 - max(0.0, s) * 2.0)
        bob = 1.1 * abs(c)
        lurch = 0.6 * s
        fr.append((120, SP(P=(18.2, 26.0 + bob), C=(19.6 + lurch, 19.2 + bob), Hd=(21.6 + lurch * 1.3, 13.4 + bob),
                           ff=ff, fb=fb, hb=(16.5 - 1.5 * c, 28.2 + bob), hf=(24.8 + 1.2 * c, 27.4 + bob),
                           wang=64 - 6 * c)))
    return fr


def s_attack():
    WIND = dict(P=(16.2, 27.4), C=(14.9, 20.4), Hd=(15.6, 14.4), hup=(-0.3, -1), fb=(11.0, 39), ff=(22.0, 39),
                hb=(12.5, 27.5))
    return [
        (130, SP(P=(17.4, 27.0), C=(18.0, 20.0), Hd=(19.8, 14.2), hf=(22.5, 21.0), wang=-35, hb=(15, 28.5))),
        (130, SP(P=(16.8, 27.2), C=(16.6, 20.2), Hd=(17.6, 14.2), hup=(-0.1, -1), fb=(12.5, 39), hf=(19.0, 15.0),
                 wang=-100, hb=(14, 28))),
        (150, SP(**WIND, hf=(15.5, 11.0), wang=-148, eye=2)),
        (460, SP(**dict(WIND, P=(16.0, 27.6), C=(14.5, 20.7), Hd=(15.1, 14.7)), hf=(14.9, 10.6), wang=-156, eye=2)),
        (60, SP(P=(19.2, 28.2), C=(22.4, 21.6), Hd=(24.8, 16.2), hup=(0.5, -1), fb=(12.5, 39), ff=(25.5, 39),
                hb=(15.5, 26.5), hf=(29.0, 24.0), wang=18, wind=3,
                smear=dict(g0=(14.9, 10.6), a0=-156, mid=(21, 7), start=0.12))),
        (90, SP(P=(19.4, 28.6), C=(22.6, 22.4), Hd=(25.0, 17.0), hup=(0.5, -1), fb=(12.5, 39), ff=(25.5, 39),
                hb=(16, 27.5), hf=(28.5, 29.0), wang=72, wind=2,
                smear=dict(g0=(29.0, 24.0), a0=18, taper=0.5))),
        (170, SP(P=(19.0, 28.4), C=(22.0, 22.0), Hd=(24.3, 16.6), hup=(0.45, -1), fb=(12.5, 39), ff=(25.5, 39),
                 hb=(16, 28.5), hf=(28.0, 30.0), wang=82)),
        (190, SP(P=(18.4, 27.2), C=(20.2, 20.4), Hd=(22.2, 14.6), fb=(13.5, 39), ff=(23.5, 39), hf=(26.0, 28.5),
                 wang=72)),
    ]


def s_hurt():
    return [
        (80, SP(P=(16.8, 26.8), C=(15.6, 20.0), Hd=(15.6, 14.2), hup=(-0.5, -1), fb=(13.5, 39), ff=(21.0, 39),
                hb=(12.5, 26.5), hf=(22.5, 25.0), wang=35, eye=2)),
        (140, SP(P=(17.4, 26.8), C=(17.2, 19.9), Hd=(18.0, 14.0), hup=(-0.2, -1), hb=(14.5, 28), hf=(24.0, 27.0),
                 wang=55)),
    ]


def s_death():
    KN = dict(P=(16.2, 32.8), C=(18.4, 26.4), Hd=(21.3, 21.6), hup=(0.6, -1), kb=(14.8, 37.6), kf=(20.2, 37.8),
              fb=(9.0, 39), ff=(14.5, 39), hb=(16.5, 34), hf=(22.5, 35.0), eye=0, sword=((25.0, 38.4), 2))
    piv = (19.5, 37.5)
    fall = []
    for rot, ms in ((28, 120), (62, 110), (86, 700)):
        fall.append((ms, SP(**dict(KN, P=(16.6, 32.4), C=(18.0, 25.6), Hd=(20.0, 20.2), hup=(0.2, -1),
                                   hb=(17.5, 33.0), hf=(21.0, 33.5)),
                            rot=rot, piv=piv, legs_fixed=True, snap=["BackArm", "Body", "Cloth", "Head", "FrontArm",
                                                                     "BackLeg", "FrontLeg"])))
    return [
        (110, SP(P=(16.6, 26.8), C=(15.2, 20.0), Hd=(14.8, 14.4), hup=(-0.6, -1), fb=(13.0, 39), ff=(21.0, 39),
                 hb=(12.0, 25.5), hf=(22.0, 24.0), wang=20, eye=2)),
        (140, SP(P=(16.8, 30.0), C=(17.6, 23.2), Hd=(19.6, 17.8), hup=(0.3, -1), fb=(12.0, 39), ff=(22.0, 39),
                 hb=(15.5, 31.5), hf=(23.0, 31.0), wang=88, eye=1)),
        (200, SP(**dict(KN, sword=((23.5, 34.5), 40)))),
    ] + fall


def build_soldier():
    K.setup(48, 40)
    anims, infos = render_anims(SOLDIER_L, draw_soldier, [("idle", s_idle), ("walk", s_walk), ("attack", s_attack),
                                                          ("hurt", s_hurt), ("death", s_death)])
    meta = {"native": 1, "frame": [48, 40], "anchor": [18, 40],
            "hurtbox": hurtbox(anims, ["Body", "Head", "BackLeg", "FrontLeg"], inset=(1, 0, 1)),
            "attacks": {"attack": {"active": [4, 5], "hit": hit_rect(infos, "attack", [4, 5], x_min=20)}}}
    K.export("hollow_soldier", SOLDIER_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== 2. SHIELD WARDEN
WARDEN_L = ["Spear", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "ShieldArm", "Shield", "FX"]
W_SPEAR = dict(pommel=-10.5, grip_end=19.2, grip="W3", grip_w=0.55, pommel_c="I3", guard=(18.2, 19.4, 1.1),
               guard_c="I2", guard_hi="I4", b0=19.4, end=26.0, w_edge=1.25, w_spine=1.25, taper=0.55,
               edge_hi="I5", edge="I4", spine="I2")
W_NEU = dict(P=(22.0, 33.5), C=(23.0, 24.5), Hd=(24.6, 17.2), hup=(0.1, -1), fb=(17.0, 47), ff=(27.5, 47),
             hb=(19.5, 31.0), sang=-96, S=(31.0, 33.2), sup=(0.0, -1), rot=0.0, piv=(0, 0), legs_fixed=False,
             kb=None, kf=None, eye=1, smear=None, lines=None, wind=0.0)
WP = mk(W_NEU)


def shield_mask(R, S, sup):
    Sb = basis(S, sup)
    pts = [Sb(-4.4, -11.2), Sb(-3.0, -12.9), Sb(0.2, -13.6), Sb(3.4, -13.0), Sb(4.8, -11.0), Sb(5.2, 0.0),
           Sb(4.8, 11.6), Sb(0.4, 12.9), Sb(-4.2, 12.0), Sb(-4.7, 0.0)]
    return R.mask(pts), Sb


def draw_warden(p, fi, sw):
    Ls = {n: Layer(n) for n in WARDEN_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    LR = ID if p["legs_fixed"] else R
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(1.0, -ln + 1.2), F(-2.2, -ln + 1.4)
    hB, hF = F(-1.8, 0.6), F(1.8, 0.6)
    if p["legs_fixed"]:
        hB, hF = R.T(hB), R.T(hF)
    info = {"hit": set(), "shield": set(), "spear": set()}
    # ---- spear (behind the body; overhand grip in the back hand)
    if p.get("spear_free"):
        pix, blade, tip = blade_px(ID, *p["spear_free"], W_SPEAR)
    else:
        pix, blade, tip = blade_px(R, p["hb"], p["sang"], W_SPEAR)
    Ls["Spear"].fixed(pix)
    info["spear"] = blade
    info["tip"] = tip
    # ---- back arm
    arm(R, Ls["BackArm"], shB, p["hb"], 5.4, 5.6, 2.1, 1.8, "I", bias=-1, fist="L", fist_r=1.5)
    R.dome(Ls["BackArm"], add(shB, (0, -0.4)), 2.8, 2.4, "I", bias=-1)
    # ---- legs: plate greaves, heavy sabatons
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(LR, Ls[nm], hip, ft, 7.3, 7.4, 2.7, 2.2, "I", bias=bias, flen=3.6, heel=2.0, boot_h=3.0,
                knee=kn)
        LR.dome(Ls[nm], add(k, (0.4, 0)), 2.1, 2.0, "I", bias=bias)
        LR.decal(Ls[nm], [add(k, (0.6, 0.1))], ("G", 3 + bias))
    # ---- torso: barrel breastplate, crimson surcoat skirt, gold neck trim
    Bd = Ls["Body"]
    skirt = [F(-5.0, -1.0), F(4.6, -1.0), F(5.4 - sw * 0.3, 6.5), F(2.2 - sw * 0.5, 7.4), F(-0.6 - sw * 0.5, 6.6),
             F(-3.4 - sw * 0.5, 7.6), F(-5.8 - sw * 0.3, 6.2)]
    sm_ = R.plate(Bd, skirt, "C", bevel=1.6, tilt=(0.0, 0.1),
                  fold=lambda x, y: (0.6 * math.sin((x - P[0]) * 1.2), 0), bias=-1)
    Bd.decal([q for q in sm_ if (q[0] - int(P[0])) % 3 == 0], ("C", 1))
    torso = [F(-5.0, 0.6), F(-5.6, -ln + 2.4), F(-3.8, -ln - 1.4), F(2.4, -ln - 1.8), F(5.0, -ln + 0.8),
             F(5.4, -ln + 5.0), F(4.2, 0.6)]
    tm = R.plate(Bd, torso, "I", bevel=2.6, tilt=(-0.3, -0.1), strength=1.3)
    for k in range(2):
        yy = -2.4 - k * 2.4
        R.dline(Bd, F(-4.6, yy), F(4.6, yy), ("I", 1))
        R.dline(Bd, F(-4.2, yy + 0.8), F(4.2, yy + 0.8), ("I", 3))
    R.dline(Bd, F(-3.2, -ln - 1.0), F(2.4, -ln - 1.4), ("G", 3))
    R.dline(Bd, F(-5.0, 0.2), F(4.4, 0.2), ("L", 1))
    R.decal(Bd, [F(1.0, 0.2), F(1.8, 0.2)], ("G", 3))
    # ---- head: bucket great-helm, visor slit, gold crest ridge
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    R.cap(Hl, G(-0.5, 5.2), G(-0.5, 3.0), 2.4, 2.4, "I", bias=-1)          # gorget
    helm = [G(-3.6, 3.8), G(-4.0, -2.6), G(-2.6, -4.6), G(1.8, -4.8), G(3.8, -3.2), G(4.2, 1.0), G(3.6, 3.9)]
    hm = R.plate(Hl, helm, "I", bevel=1.7, tilt=(-0.3, -0.2), strength=1.3)
    R.dline(Hl, G(-0.8, -4.6), G(-0.6, 3.6), ("I", 4))
    R.dline(Hl, G(-2.4, -4.8), G(2.0, -5.0), ("G", 3))
    R.dline(Hl, G(0.6, -0.6), G(4.2, -0.6), "OUT")
    R.decal(Hl, [G(1.2, -1.5), G(2.4, -1.5), G(3.4, -1.5)], ("I", 4))
    for k in range(3):
        R.decal(Hl, [G(1.6 + k * 1.0, 1.6 + (k % 2))], "OUT")
    if p["eye"]:
        e = R.pt(G(2.6, -0.6))
        FX.put([e], "Y1" if p["eye"] == 1 else "Y3")
        if p["eye"] > 1:
            FX.put([(e[0] + 1, e[1])], "Y1")
    # plume stub (crimson horsehair) at the back of the crown
    plume = [G(-2.2, -4.4), G(-0.8, -5.4), G(-2.5 + sw * 0.2, -3.0), G(-5.0 + sw * 0.5, -0.6), G(-4.6 + sw * 0.4, -2.4)]
    R.plate(Hl, plume, "C", bevel=1.0, tilt=(0.1, -0.3), bias=0)
    # ---- shield arm + big pauldron (arm mostly hidden by the shield)
    Sa = Ls["ShieldArm"]
    hs = add(p["S"], (-1.5, -2.0))
    arm(R, Sa, shF, hs, 5.4, 5.6, 2.2, 1.9, "I", bias=0, pref=(-1, 0.6), fist="L", fist_r=1.5)
    pd = R.dome(Sa, add(shF, (-0.4, -0.3)), 3.6, 3.0, "I", tilt=(0, -0.1))
    Sa.decal([q for q in pd if (q[0], q[1] + 1) not in pd], ("G", 3))
    # ---- tower shield: tarnished bronze face, iron rim, Pale-Root sigil, rivets
    Sh = Ls["Shield"]
    sm, Sb = shield_mask(R, p["S"], p["sup"])
    cx = R.T(p["S"])[0]
    Sh.paint(n_plate(sm, 2.0, (-0.25, -0.05), 1.1, fold=lambda x, y: ((x + .5 - cx) * 0.11, 0)), "G", bias=-1)
    rim = [q for q in sm if any((q[0] + a, q[1] + b) not in sm for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    Sh.decal(rim, ("I", 3))
    Sh.decal([q for q in rim if (q[0] + q[1]) % 5 == 0], ("I", 5))
    trunk = [Sb(0.3, 9.5), Sb(0.3, -7.0)]
    R.dline(Sh, *trunk, ("G", 4))
    R.dline(Sh, Sb(1.3, 9.5), Sb(1.3, -6.0), ("G", 1))
    for a, b in (((0.3, -3.0), (-2.6, -6.6)), ((0.3, -4.5), (3.0, -8.4)), ((0.3, -1.0), (3.2, -3.2)),
                 ((0.3, 5.0), (-2.6, 9.4)), ((0.3, 6.0), (3.0, 9.6))):
        R.dline(Sh, Sb(*a), Sb(*b), ("G", 4))
    R.dome(Sh, Sb(0.4, -1.2), 1.6, 1.6, "I", ao=0)
    info["shield"] = sm
    # ---- FX: smears / speed lines
    if p["smear"]:
        sm_ = p["smear"]
        hot = thrust_lines(FX, R.T(p["hb"]), R.A(p["sang"]), sm_.get("u0", 6), sm_.get("u1", 20),
                           sm_.get("offs", (-2.5, 2.5, -4.5)), pal="steel", flash=sm_.get("flash"))
        info["hit"] |= {q for q in hot if q[0] > R.T(p["hb"])[0] + 12}
    if p["lines"]:
        x0, x1, ys = p["lines"]
        speed_lines(FX, x0, x1, ys, pal="steel", seed=fi)
    return Ls, info


def w_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((220, WP(P=(22, 33.5 + b * 0.4), C=(23, 24.5 + b), Hd=(24.6, 17.2 + b), hb=(19.5, 31 + b),
                           S=(31, 33.2 + b * 0.5))))
    return fr


def w_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        ff = (22.8 + 4.2 * c, 47 - max(0.0, -s) * 2.4)
        fb = (21.5 - 4.2 * c, 47 - max(0.0, s) * 2.4)
        bob = 1.2 * abs(c)
        fr.append((140, WP(P=(22.2, 33.0 + bob), C=(23.4, 24.0 + bob), Hd=(25.0, 16.8 + bob), ff=ff, fb=fb,
                           hb=(19.8 - 0.8 * c, 30.6 + bob), sang=-96 + 3 * c, S=(31.4 + 0.6 * c, 32.8 + bob))))
    return fr


GUARD = dict(P=(21.6, 35.0), C=(23.0, 26.6), Hd=(25.2, 19.8), hup=(0.25, -1), fb=(15.5, 47), ff=(28.0, 47),
             hb=(21.5, 19.6), sang=6, S=(32.0, 34.4))


def w_guard():
    return [(260, WP(**GUARD)),
            (260, WP(**dict(GUARD, C=(23.0, 27.0), Hd=(25.2, 20.2), hb=(21.5, 20.0), S=(32.0, 34.6))))]


def w_bash():
    shove = dict(P=(25.6, 34.6), C=(28.6, 26.4), Hd=(31.0, 19.6), hup=(0.4, -1), fb=(17.0, 47), ff=(33.5, 47),
                 hb=(25.5, 20.5), sang=10, S=(39.5, 33.2), sup=(0.12, -1))
    thrust = dict(P=(25.2, 34.8), C=(28.2, 26.2), Hd=(30.4, 19.6), hup=(0.35, -1), fb=(17.0, 47), ff=(32.5, 47),
                  S=(34.2, 34.2), sup=(0.05, -1))
    return [
        (140, WP(**dict(GUARD, P=(21.0, 35.4), C=(21.6, 27.0), Hd=(23.4, 20.2), S=(30.0, 34.5), hb=(20.5, 20), sang=2))),
        (240, WP(P=(19.2, 35.4), C=(18.2, 27.2), Hd=(19.4, 20.2), hup=(-0.15, -1), fb=(12.5, 47), ff=(26.5, 47),
                 hb=(18.2, 20.4), sang=-4, S=(26.8, 34.6), sup=(-0.15, -1), eye=2)),
        (70, WP(**shove, lines=(9, 22, (24, 31, 38, 44)), wind=3)),
        (120, WP(**dict(shove, P=(25.2, 34.8), C=(28.0, 26.6), S=(39.0, 33.4)), lines=(13, 22, (28, 41)))),
        (170, WP(P=(22.8, 34.8), C=(22.4, 26.4), Hd=(24.0, 19.4), hup=(0.0, -1), fb=(16.0, 47), ff=(30.0, 47),
                 hb=(16.5, 18.6), sang=-3, S=(32.6, 34.2))),
        (280, WP(P=(22.4, 35.2), C=(21.4, 26.8), Hd=(23.0, 19.8), hup=(-0.1, -1), fb=(15.5, 47), ff=(30.0, 47),
                 hb=(14.2, 18.2), sang=-6, S=(31.8, 34.4), eye=2)),
        (60, WP(**thrust, hb=(28.0, 22.0), sang=4, wind=3, smear=dict(u0=4, u1=22, offs=(-2.2, 2.4, -4.2),
                                                                           flash=25.5))),
        (110, WP(**thrust, hb=(28.4, 22.0), sang=4, smear=dict(u0=10, u1=20, offs=(-2.2, 2.4)))),
        (220, WP(**dict(GUARD, P=(22.6, 34.6), C=(24.0, 26.0), Hd=(26.0, 19.0), hb=(22.5, 20.5), sang=2))),
    ]


def w_hurt():
    return [
        (80, WP(P=(20.4, 33.8), C=(19.4, 25.0), Hd=(20.0, 17.8), hup=(-0.35, -1), hb=(17.5, 30), sang=-110,
                S=(28.4, 33.2), sup=(-0.2, -1), eye=2)),
        (150, WP(P=(21.2, 33.6), C=(21.6, 24.8), Hd=(23.0, 17.4), hb=(18.5, 30.5), sang=-100, S=(30.0, 33.2))),
    ]


def w_death():
    KN = dict(P=(21.0, 40.0), C=(23.2, 31.4), Hd=(25.4, 24.4), hup=(0.35, -1), kb=(19.5, 45.8), kf=(25.6, 46.0),
              fb=(13.0, 47), ff=(19.0, 47), hb=(20, 36), sang=-125, S=(31.5, 36.0), sup=(0.3, -1), eye=0)
    piv = (25.0, 46.0)
    fall = []
    for (rot, ms), spr in zip(((24, 120), (55, 110), (78, 700)),
                              (((11.8, 43.6), -12), ((14.5, 46.4), 0), ((14.5, 46.4), 0))):
        fall.append((ms, WP(**KN, rot=rot, piv=piv, legs_fixed=True, spear_free=spr,
                            snap=["Spear", "BackArm", "Body", "Head", "ShieldArm", "Shield", "BackLeg", "FrontLeg"])))
    return [
        (110, WP(P=(20.6, 33.8), C=(19.2, 25.0), Hd=(19.6, 17.8), hup=(-0.4, -1), hb=(16.5, 28), sang=-112,
                 S=(29.0, 34.0), sup=(0.1, -1), eye=2)),
        (150, WP(P=(21.0, 37.0), C=(22.0, 28.4), Hd=(24.0, 21.2), hup=(0.2, -1), fb=(15.5, 47), ff=(27.5, 47),
                 hb=(19, 34), sang=-122, S=(31.0, 35.4), sup=(0.2, -1), eye=1)),
        (220, WP(**KN)),
    ] + fall


def build_warden():
    K.setup(56, 48)
    anims, infos = render_anims(WARDEN_L, draw_warden, [("idle", w_idle), ("walk", w_walk), ("guard", w_guard),
                                                        ("bash", w_bash), ("hurt", w_hurt), ("death", w_death)])
    for k in (2, 3):
        infos["bash"][k]["hit"] = set(infos["bash"][k]["shield"])
    for k in (6, 7):
        infos["bash"][k]["hit"] = set(infos["bash"][k]["hit"]) | {q for q in infos["bash"][k]["spear"]
                                                                   if q[0] > infos["bash"][k]["tip"][0] - 9}
    meta = {"native": 1, "frame": [56, 48], "anchor": [22, 48],
            "hurtbox": hurtbox(anims, ["Body", "Head", "BackLeg", "FrontLeg", "Shield"], inset=(1, 0, 1)),
            "attacks": {"bash": {"windows": [
                {"active": [2, 3], "hit": hit_rect(infos, "bash", [2, 3], x_min=28)},
                {"active": [6, 7], "hit": hit_rect(infos, "bash", [6, 7], x_min=30)}]}}}
    K.export("shield_warden", WARDEN_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== 3. ROT CRAWLER
CRAWLER_L = ["BackLegs", "Body", "Sac", "Head", "FrontLegs", "FX"]
C_NEU = dict(B=(17.0, 17.2), tilt=0.0, stretch=1.0, mand=0.2, pulse=0.0, glow=1, ph=0.0, gait=0.0, sy=1.0,
             lift=1.4, legs="walk", ant=0.0, burst=0, lines=None, wind=0.0, sac=1.0)
CP = mk(C_NEU)
C_SPINE = [(-10.5, 0.8, 2.9), (-6.3, 0.0, 3.8), (-1.6, -0.6, 4.5), (3.2, -0.2, 4.0)]
C_ROOTS = [-6.5, -2.8, 0.8, 4.2]


def draw_crawler(p, fi, sw):
    Ls = {n: Layer(n) for n in CRAWLER_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    B = p["B"]
    R = Rig(-p["tilt"], B, sy=p["sy"])
    st = p["stretch"]
    Fb = lambda a, b: (B[0] + a * st, B[1] + b)
    ground = K.H - 1 if p["sy"] > 0 else B[1] - (K.H - 1 - B[1])
    info = {"hit": set()}
    # ---- legs (far side darker, behind body; near side in front): arched, jointed, fanned out
    SPREAD = (-4.8, -2.2, 2.0, 4.6)
    for side, nm in ((1, "BackLegs"), (0, "FrontLegs")):
        L = Ls[nm]
        for i, rx in enumerate(C_ROOTS):
            root = Fb(rx + (0.7 if side else 0), 0.8)
            ph = p["ph"] + (i % 2) * math.pi + side * math.pi
            spread = SPREAD[i] * (0.85 if side else 1.0)
            if p["legs"] == "walk":
                fx_ = root[0] + spread * 1.35 + p["gait"] * math.cos(ph)
                fy_ = (K.H - 1.0 if p["sy"] > 0 else B[1] + 6) - max(0.0, math.sin(ph)) * p["lift"]
                knee = (root[0] + spread * 0.75 + p["gait"] * 0.4 * math.cos(ph), root[1] - 2.6 - (0.5 if side else 0)
                        - max(0.0, math.sin(ph)) * p["lift"] * 0.5)
            elif p["legs"] == "trail":      # lunging: legs thrown back / scrabbling
                fx_ = root[0] - 4.0 - i * 0.3 + (1.5 if i == 3 else 0)
                fy_ = B[1] + 4.6 + (0.8 if side else 0)
                knee = (root[0] - 0.5, root[1] - 2.4)
            else:                           # curled (dead): folded towards the belly, twitching
                cur = p["legs"]
                twitch = math.sin(fi * 2.1 + i * 1.7) * 0.9 * (1 - cur)
                fx_ = root[0] + spread * (0.8 - 0.8 * cur) + twitch - 1.0 * cur
                fy_ = root[1] + 7.6 - 3.0 * cur
                knee = (root[0] + spread * (0.6 - 0.2 * cur), root[1] + 7.4 - 0.6 * cur + twitch * 0.5)
            pts = [R.T(root), R.T(knee), R.T((fx_, fy_))]
            pix = {}
            for q in polyline(pts[:2]):
                pix[q] = "F2" if side else "F3"
            for q in polyline(pts[1:]):
                pix[q] = "F1" if side else "F2"
            pix[ip(pts[1])] = "F3" if side else "F4"
            pix[ip(pts[2])] = "B2" if side else "B3"   # bone claw tip
            L.fixed(pix)
    # ---- belly (dead-flesh underside) then carapace segments tail -> thorax
    Bd = Ls["Body"]
    R.cap(Bd, Fb(-10.5, 2.2), Fb(4.5, 2.0), 2.3, 2.6, "F", bias=-1)
    for k, (a, b, r) in enumerate(C_SPINE):
        c = Fb(a, b)
        m = R.dome(Bd, c, r * (1.05 if st > 1 else 1.0) * 1.08, r * 0.86, "V", bias=0, tilt=(-0.05, 0.05))
        # segment seam + lit ridge + spines
        R.decal(Bd, [add(c, (r * 0.8, t)) for t in (-2.0, -1.0, 0.0, 1.0)], ("V", 1))
        R.decal(Bd, [add(c, (-1.0, -r * 0.62)), add(c, (0.0, -r * 0.7))], ("V", 5))
        if k in (0, 1, 3):
            sp = R.T(add(c, (0.4, -r * 0.86)))
            Bd.fixed({ip(sp): "V3", ip((sp[0] - 0.5, sp[1] - 1 * p["sy"])): "V2"})
    # rot blotches
    Bd.decal([q for q in list(Bd.px) if Bd.px[q][0] == "V" and hash01(q[0] - int(B[0]), q[1] - int(B[1]), 17) < 0.07],
             ("F", 3))
    # ---- sac: swollen orange blister on the back (fixed glow colours + dark veins)
    Sc = Ls["Sac"]
    if p["sac"] > 0:
        pr = (1.0 + 0.1 * p["pulse"]) * p["sac"]
        sc = Fb(-3.4, -4.4 + 0.3 * (1 - p["sac"]))
        scT = R.T(sc)
        rx, ry = 4.4 * pr, 3.5 * pr * abs(p["sy"])
        m = K.mask_disc(scT, rx, max(0.8, ry))
        g = p["glow"]
        pal = ("O1", "O2", "O3", "O4", "O5") if g >= 1 else ("O0", "O1", "O1", "O2", "O3")
        if g >= 2:
            pal = ("O2", "O3", "O4", "O5", "O5")
        pix = {}
        for q in m:
            ex, ey = (q[0] + .5 - scT[0]) / rx, (q[1] + .5 - scT[1]) / max(0.8, ry)
            d = math.hypot(ex + 0.35, ey + 0.4 * (1 if p["sy"] > 0 else -1))
            pix[q] = pal[4] if d < 0.28 else pal[3] if d < 0.6 else pal[2] if d < 0.9 else pal[1]
            if ex * ex + ey * ey > 0.75:
                pix[q] = pal[1] if ey < 0 else pal[0]
        for t in range(-3, 4, 2):   # veins
            for q in line((scT[0] + t * 0.9, scT[1] + ry * 0.9), (scT[0] + t * 0.4 + 0.5, scT[1] - ry * 0.3)):
                if q in pix and hash01(q[0], q[1], 21) < 0.7:
                    pix[q] = "O1" if g >= 1 else "O0"
        Sc.fixed(pix)
        info["sac"] = scT
    # ---- head: small armoured dome, glowing eyes, bone mandibles, antennae
    Hl = Ls["Head"]
    hc = Fb(8.1, 0.8)
    R.dome(Hl, hc, 3.1, 2.7, "V", bias=0)
    R.decal(Hl, [add(hc, (-0.6, -2.0)), add(hc, (0.4, -2.2))], ("V", 5))
    eyes = [R.pt(add(hc, (1.4, -0.6))), R.pt(add(hc, (2.3, -0.2)))]
    FX.put([eyes[0]], "O4" if p["glow"] else "O1")
    FX.put([eyes[1]], "O3" if p["glow"] else "O0")
    op = p["mand"]
    mpix = {}
    for sgn in (-1, 1):
        a0 = add(hc, (2.4, 0.9 + sgn * 0.6))
        a1 = add(hc, (5.0, 0.9 + sgn * (0.8 + 1.8 * op)))
        a2 = add(hc, (6.4, 0.9 + sgn * (0.2 + 1.2 * op)))
        pts = polyline([R.T(a0), R.T(a1), R.T(a2)])
        for q in pts:
            mpix[q] = "B4" if sgn < 0 else "B2"
        mpix[ip(R.T(a2))] = "B5" if sgn < 0 else "B3"
    Hl.fixed(mpix)
    info["hit"] |= set(mpix) | set(Hl.px)
    info["head"] = R.T(hc)
    ant = p["ant"]
    for k, (dx, dy) in enumerate(((3.2, -3.8), (1.6, -4.2))):
        pts = polyline([R.T(add(hc, (0.6, -2.0))), R.T(add(hc, (dx * 0.6, dy * 0.7 + ant))),
                        R.T(add(hc, (dx + 1.4 - ant * 0.3, dy + ant * 1.3)))])
        Ls["BackLegs" if k else "FrontLegs"].fill(pts[1:], "F1" if k else "F2", noout=True)
    # ---- fx
    if p["lines"]:
        x0, x1, ys = p["lines"]
        speed_lines(FX, x0, x1, ys, pal="ember", seed=fi)
    if p["burst"]:
        sc = info.get("sac") or R.T(Fb(-3.4, -4.4))
        n = p["burst"]
        for k in range(22):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 1, 31))
            r = (2.0 + 7.0 * hash01(k, 2, 32)) * (0.6 if n == 1 else 1.0 if n == 2 else 1.25)
            q = ip((sc[0] + math.cos(a) * r * 1.3, sc[1] + math.sin(a) * r * (1.0 if n < 3 else 0.6) + (n - 1) * 1.5 * (r / 6) ** 2))
            if n == 3 and hash01(k, 3, 33) < 0.5:
                continue
            FX.put([q], ("O5", "O4", "O3")[k % 3] if n == 1 else ("O4", "O3", "O2")[k % 3] if n == 2 else "O1")
    return Ls, info


def c_idle():
    fr = []
    for i in range(4):
        b = (0, 0.4, 0.8, 0.4)[i]
        fr.append((170, CP(B=(17, 17.2 + b * 0.5), pulse=(0, 0.5, 1.0, 0.5)[i], mand=(0.2, 0.5, 0.2, 0.0)[i],
                           ph=i * math.pi / 2, gait=0.4, lift=0.4, ant=(0, 0.6, 1.0, 0.4)[i],
                           glow=2 if i == 2 else 1)))
    return fr


def c_crawl():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        fr.append((70, CP(B=(17.2, 17.0 + 0.4 * abs(math.sin(ph * 2))), ph=ph, gait=2.2, lift=1.6,
                          tilt=0.8 * math.sin(ph), mand=0.3 + 0.2 * math.sin(ph), pulse=0.5 + 0.5 * math.sin(ph),
                          ant=0.6 * math.cos(ph))))
    return fr


def c_lunge():
    return [
        (110, CP(B=(15.5, 18.0), ph=0.4, gait=1.0, lift=0.4, mand=0.4, pulse=0.6)),
        (150, CP(B=(15.4, 16.8), tilt=14, ph=0.8, gait=1.2, lift=0.4, mand=1.0, pulse=1.0, glow=2, ant=1.2)),
        (240, CP(B=(15.0, 16.6), tilt=17, ph=0.9, gait=1.2, lift=0.4, mand=1.1, pulse=1.4, glow=2, ant=1.4)),
        (60, CP(B=(21.0, 17.4), tilt=-4, stretch=1.12, legs="trail", mand=0.9, pulse=0.4,
                lines=(1, 12, (13, 16, 19)))),
        (90, CP(B=(21.2, 17.6), tilt=-6, stretch=1.1, legs="trail", mand=0.0, pulse=0.2,
                lines=(3, 11, (15, 19)))),
        (150, CP(B=(19.4, 17.6), tilt=-2, ph=2.0, gait=1.8, lift=0.8, mand=0.1, pulse=0.3)),
        (160, CP(B=(17.6, 17.3), ph=3.0, gait=1.2, lift=0.6, mand=0.2, pulse=0.4)),
    ]


def c_hurt():
    return [(80, CP(B=(15.0, 17.6), tilt=10, mand=1.0, pulse=1.5, glow=2, ph=1, gait=2.6, lift=1.6, ant=1.5)),
            (140, CP(B=(16.2, 17.4), tilt=4, mand=0.5, pulse=0.8, ph=2, gait=1.0, lift=0.6))]


def c_death():
    return [
        (90, CP(B=(15.0, 17.4), tilt=12, mand=1.1, pulse=1.6, glow=2, ph=1, gait=2.8, lift=2.0, ant=1.5)),
        (90, CP(B=(16.0, 17.6), tilt=6, sy=0.35, mand=1.0, pulse=1.4, glow=2, legs=0.0, snap=CRAWLER_L[:-1])),
        (110, CP(B=(16.0, 14.0), tilt=-3, sy=-1.0, mand=0.9, pulse=1.8, glow=2, legs=0.1, burst=1,
                 snap=CRAWLER_L[:-1])),
        (110, CP(B=(16.0, 14.0), tilt=-3, sy=-1.0, mand=0.6, sac=0.55, glow=0, legs=0.4, burst=2, snap=CRAWLER_L[:-1])),
        (130, CP(B=(16.0, 14.0), tilt=-3, sy=-1.0, mand=0.3, sac=0.4, glow=0, legs=0.75, burst=3, snap=CRAWLER_L[:-1])),
        (700, CP(B=(16.0, 14.0), tilt=-3, sy=-1.0, mand=0.2, sac=0.35, glow=0, legs=1.0, snap=CRAWLER_L[:-1])),
    ]


def build_crawler():
    K.setup(40, 24)
    anims, infos = render_anims(CRAWLER_L, draw_crawler, [("idle", c_idle), ("crawl", c_crawl), ("lunge", c_lunge),
                                                          ("hurt", c_hurt), ("death", c_death)], sway_key="B")
    meta = {"native": 1, "frame": [40, 24], "anchor": [17, 24],
            "hurtbox": hurtbox(anims, ["Body", "Sac", "Head"], inset=(1, 0, 0)),
            "attacks": {"lunge": {"active": [3, 4], "hit": hit_rect(infos, "lunge", [3, 4], x_min=24)}}}
    K.export("rot_crawler", CRAWLER_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== 4. GLOOM WISP
WISP_L = ["WingBack", "Tail", "Body", "Skull", "WingFront", "FX"]
G_NEU = dict(O=(20.0, 16.0), tilt=0.0, wing=-100.0, fold=0.0, eye=1, tailph=0.0, crack=0, glow=1,
             lines=None, wind=0.0, drop=0.0, tail=1.0, motes=True, wings=True)
GP = mk(G_NEU)
FOREWING = [(0, -0.6), (4.0, -1.6), (8.6, -2.2), (12.2, -1.4), (13.0, 1.0), (11.6, 4.8), (8.0, 7.4), (3.8, 6.8),
            (0.6, 3.2)]
HINDWING = [(0, 0), (3.0, -0.6), (6.6, 0.2), (8.0, 2.6), (6.6, 5.4), (3.4, 5.8), (0.6, 3.0)]


def wing_shape(R, L, root, ang, scale, bias, fold, fi, hind=False):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    shape = HINDWING if hind else FOREWING
    k = scale * (1 - 0.3 * fold)
    wv = (0.9 if not hind else 0.85) * (1 - 0.6 * fold)
    Wf = lambda u, v: (root[0] + ca * u * k + sa * v * k * wv, root[1] + sa * u * k - ca * v * k * wv)
    pts = [Wf(u, v) for u, v in shape]
    m = R.mask(pts)
    if not m:
        return m
    L.paint(n_plate(m, 1.4, (-0.1, -0.25), 1.0), "M", bias=bias, ao=0)
    edge = [q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    tip = R.T(Wf(12 if not hind else 7, 0))
    L.decal([q for q in edge if math.hypot(q[0] - tip[0], q[1] - tip[1]) < 5], ("M", 4 + bias))
    # veins
    for vv in ((-0.8, 11.0), (1.8, 10.0), (4.0, 7.0)):
        R.dline(L, Wf(1.0, 0.8), Wf(vv[1] if not hind else vv[1] * 0.6, vv[0]), ("M", 1), only_on=("M",))
    if not hind and fold < 0.6:
        # dull-gold eye-spot
        c = R.T(Wf(7.8, 2.2))
        ring = [q for q in mask_disc(c, 1.8 * k, 1.8 * k * max(0.5, wv)) if q in m]
        L.decal(ring, ("G", 2 + bias))
        L.decal([ip(c)], "OUT")
        L.decal([(ip(c)[0] - 1, ip(c)[1] - 1)], ("G", 4 + bias))
    return m


def draw_wisp(p, fi, sw):
    Ls = {n: Layer(n) for n in WISP_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    O = (p["O"][0], p["O"][1] + p["drop"])
    R = Rig(p["tilt"], O)
    info = {"hit": set()}
    sh = add(O, (-0.6, -2.0))
    # ---- wings
    if p["wings"]:
        wing_shape(R, Ls["WingBack"], add(sh, (1.4, -0.6)), R.A(p["wing"]) + 22 - p["tilt"], 0.85, -1, p["fold"], fi)
        wing_shape(R, Ls["WingBack"], add(sh, (0.2, 1.2)), R.A(p["wing"]) + 55 - p["tilt"], 0.85, -1, p["fold"], fi, hind=True)
    # ---- wraith tail: tattered shroud ribbon streaming back-down, rippling
    Tl = Ls["Tail"]
    if p["tail"] > 0:
        n = 14
        spine = []
        for i in range(n + 1):
            t = i / n
            x = O[0] - 1.5 - 13.0 * t * p["tail"] + sw * 0.4 * t
            y = O[1] + 1.5 + 7.5 * t * p["tail"] + math.sin(p["tailph"] + t * 5.0) * 1.6 * t
            spine.append((x, y))
        up_, dn = [], []
        for i, (x, y) in enumerate(spine):
            t = i / n
            wd = 3.6 * (1 - t) ** 0.8 + 0.5
            up_.append((x + 0.3, y - wd * 0.8))
            dn.append((x - 0.3, y + wd * 0.9 + (1.2 if i % 3 == 1 and t > 0.3 else 0)))
        m = R.mask(up_ + dn[::-1])
        if p["tail"] < 1:
            m = {q for q in m if hash01(q[0], q[1], 40 + fi) < 0.25 + 0.75 * p["tail"] ** 2 or q[0] > O[0] - 6}
        Tl.paint(n_plate(m, 1.6, (0.1, 0.0), 0.9, fold=lambda x, y: (0.0, 0.5 * math.sin(x * 1.1 + p["tailph"]))),
                 "M", bias=-1, ao=0)
        # ghost-light hem strands
        for q in m:
            if (q[0], q[1] + 1) not in m and hash01(q[0], fi // 2, 41) < 0.35:
                Tl.decal([q], "Q1")
    # ---- thorax: furred moth body
    Bd = Ls["Body"]
    R.dome(Bd, add(O, (-1.4, 0.8)), 3.4, 3.0, "M", bias=0)
    R.decal(Bd, [add(O, (-2.6 + k, 2.0 + (k % 2))) for k in range(4)], ("M", 1))
    R.decal(Bd, [add(O, (-2.4, -1.2)), add(O, (-1.6, -1.6))], ("M", 5))
    # ---- skull
    Sk = Ls["Skull"]
    S = add(O, (3.0, -0.8))
    R.dome(Sk, S, 3.9, 3.5, "B", tilt=(-0.05, -0.05))
    R.plate(Sk, [add(S, (0.0, 1.8)), add(S, (3.6, 1.2)), add(S, (4.0, 2.9)), add(S, (3.0, 3.9 + 0.6 * (p["eye"] > 1))),
                 add(S, (0.6, 4.1))], "B", bevel=1.0, bias=-1)
    R.dline(Sk, add(S, (1.0, 2.6)), add(S, (3.8, 2.4)), ("B", 1))
    R.decal(Sk, [add(S, (3.1, 1.0))], ("B", 0))                     # nasal
    sock = [add(S, (1.2, -0.6)), add(S, (2.2, -0.6)), add(S, (1.2, 0.4)), add(S, (2.2, 0.4))]
    R.decal(Sk, sock, "OUT")
    R.decal(Sk, [add(S, (-0.8, -2.4)), add(S, (0.4, -2.8))], ("B", 5))
    if p["crack"]:
        R.dline(Sk, add(S, (-1.5, -3.2)), add(S, (0.2, -0.8)), ("B", 0))
        if p["crack"] > 1:
            R.dline(Sk, add(S, (0.2, -0.8)), add(S, (-1.8, 1.2)), ("B", 0))
    # feathery antennae sweeping back
    for k, (dx, dy) in enumerate(((-4.5, -5.8), (-2.6, -6.6))):
        pts = polyline([R.T(add(S, (-0.4 + k, -2.8))), R.T(add(S, (dx * 0.5, dy * 0.8))), R.T(add(S, (dx, dy)))])
        (Ls["WingBack"] if k == 0 else Sk).fill(pts[1:], "M3" if k else "M2", noout=False)
    info["hit"] |= set(Sk.px) | set(Bd.px)
    e = R.pt(add(S, (1.9, -0.2)))
    if p["eye"]:
        FX.put([e], "Q4" if p["eye"] > 1 else "Q3")
        FX.put([(e[0] - 1, e[1])], "Q2")
        if p["eye"] > 1:
            for k in range(4):     # eye-trail flare
                FX.put([(e[0] - 2 - k, e[1] - (k // 2))], "Q3" if k < 2 else "Q1")
    # ---- near wings
    if p["wings"]:
        wing_shape(R, Ls["WingFront"], add(sh, (-0.6, 1.4)), R.A(p["wing"]) + 38 - p["tilt"], 1.0, 0, p["fold"], fi, hind=True)
        wing_shape(R, Ls["WingFront"], sh, R.A(p["wing"]) - p["tilt"], 1.0, 0, p["fold"], fi)
    # ---- fx: ghost motes, dive streaks
    if p["motes"]:
        for k in range(3):
            t = ((fi * 0.37 + k * 0.33) % 1.0)
            q = ip((O[0] - 6 - t * 9 + k * 2, O[1] + 4 - t * 7 + k * 2))
            FX.put([q], "Q3" if t < 0.3 else "Q2" if t < 0.6 else "Q1")
    if p["lines"]:
        (x0, y0), (x1, y1), offs = p["lines"]
        for i, o in enumerate(offs):
            seg = line((x0, y0 + o), (x1 - (i % 2) * 3, y1 + o))
            for j, q in enumerate(seg):
                FX.put([q], "Q3" if j > len(seg) * 0.7 else "Q2" if j > len(seg) * 0.35 else "Q1")
    return Ls, info


FLAP = [-100, -128, -162, 168, -168, -132]


def g_fly():
    fr = []
    for i in range(6):
        bob = (0.0, 0.3, 0.6, 1.0, 0.4, -0.3)[i]
        fr.append((90, GP(O=(20.0, 16.0 - bob), wing=FLAP[i], tailph=i * math.pi / 3, tilt=-2 + bob * 2)))
    return fr


def g_dive():
    return [
        (140, GP(O=(19.0, 15.4), tilt=-16, wing=-100, eye=2, tailph=0.5)),
        (240, GP(O=(18.4, 15.8), tilt=-20, wing=-102, eye=2, tailph=1.2)),
        (70, GP(O=(22.0, 16.4), tilt=32, wing=-178, fold=0.5, eye=2, tailph=2.0, wind=4,
                lines=((6, 6), (18, 14), (-2, 1, 4)))),
        (90, GP(O=(23.0, 17.6), tilt=38, wing=-176, fold=0.55, eye=2, tailph=2.8, wind=3,
                lines=((8, 9), (19, 16), (-1, 2)))),
        (150, GP(O=(21.4, 16.4), tilt=6, wing=160, eye=1, tailph=3.5)),
        (150, GP(O=(20.2, 15.4), tilt=-2, wing=-120, eye=1, tailph=4.2)),
    ]


def g_hurt():
    return [(80, GP(O=(18.4, 14.4), tilt=-18, wing=-150, fold=0.3, eye=2, crack=1, tailph=1)),
            (140, GP(O=(19.4, 14.8), tilt=-8, wing=-120, eye=1, crack=1, tailph=2))]


def g_death():
    return [
        (90, GP(O=(18.4, 14.2), tilt=-20, wing=-150, fold=0.3, eye=2, crack=2, tailph=1)),
        (120, GP(O=(19.0, 15.0), tilt=-8, wing=175, fold=0.7, eye=1, crack=2, tailph=2, tail=0.8)),
        (110, GP(O=(19.4, 15.0), tilt=20, wing=150, fold=0.9, eye=1, crack=2, tailph=3, tail=0.6, drop=4.0)),
        (100, GP(O=(19.8, 15.0), tilt=45, wing=140, fold=1.0, eye=0, crack=2, tailph=4, tail=0.35, drop=8.5,
                 motes=False)),
        (110, GP(O=(20.2, 15.0), tilt=80, wing=130, fold=1.0, eye=0, crack=2, tail=0.15, drop=12.2, motes=False)),
        (700, GP(O=(20.6, 15.0), tilt=95, wing=130, fold=1.0, eye=0, crack=2, tail=0.0, drop=12.8, motes=False,
                 wings=False)),
    ]


def build_wisp():
    K.setup(40, 32)
    anims, infos = render_anims(WISP_L, draw_wisp, [("fly", g_fly), ("dive", g_dive), ("hurt", g_hurt),
                                                    ("death", g_death)], sway_key="O")
    meta = {"native": 1, "frame": [40, 32], "anchor": [20, 16], "flying": True,
            "hurtbox": [14, 10, 13, 11],
            "attacks": {"dive": {"active": [2, 3], "hit": hit_rect(infos, "dive", [2, 3], floor=False)}}}
    K.export("gloom_wisp", WISP_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== 5. HOLLOW ARCHER
ARCHER_L = ["Cloak", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "Bow", "Arrow", "FrontArm", "FX"]
A_NEU = dict(P=(18.0, 27.0), C=(18.8, 20.0), Hd=(20.2, 14.2), hup=(0.15, -1), fb=(14.5, 39), ff=(21.8, 39),
             hb=(15.5, 27.5), hf=(24.0, 27.0), bax=-58, draw=None, arrow=False, rot=0.0, piv=(0, 0),
             legs_fixed=False, kb=None, kf=None, eye=1, glint=False, twang=0, bow="hand", wind=0.0, lines=None)
AP = mk(A_NEU)
BOW_HALF = 11.5


def bow_geom(grip, axis, pull):
    """Longbow: grip point, axis = direction (deg) of the upper limb, pull = how far the string is drawn."""
    ux, uy = dirv(axis)           # along the bow, towards the top tip
    fx, fy = uy * -1, ux          # 'forward' (belly side) = perpendicular, pointing away from the archer
    if fx < 0:
        fx, fy = -fx, -fy
    bend = 1.4 + 2.4 * pull
    pts = []
    for i in range(-12, 13):
        t = i / 12
        a = BOW_HALF * t * (1 - 0.06 * pull * abs(t))
        b = -bend * t * t + 0.4 * (1 - t * t)
        pts.append((grip[0] + ux * -a + fx * b, grip[1] + uy * -a + fy * b))
    return pts, (fx, fy)


def draw_archer(p, fi, sw):
    Ls = {n: Layer(n) for n in ARCHER_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    LR = ID if p["legs_fixed"] else R
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(0.9, -ln + 0.8), F(-1.3, -ln + 1.0)
    hB, hF = F(-1.0, 0.4), F(1.0, 0.4)
    if p["legs_fixed"]:
        hB, hF = R.T(hB), R.T(hF)
    info = {"hit": set()}
    # ---- cloak: tattered moss-grey mantle down the back (secondary sway)
    Ck = Ls["Cloak"]
    sx = -sw * 0.8
    top = F(-2.6, -ln - 1.2)
    if not p["legs_fixed"]:
        hem_y = min(K.H - 3.0, P[1] + 8.5)
        pts = [add(top, (1.4, -0.4)), F(0.2, -ln + 0.8), F(-1.4, 0.0), (P[0] - 0.6 + sx * 0.3, hem_y - 1.0)] + \
            rag_hem(P[0] - 6.8 + sx, P[0] - 0.6 + sx * 0.4, hem_y, fi, 13, 2.8) + \
            [(P[0] - 6.4 + sx * 0.8, P[1] + 2.0), add(top, (-2.6, 2.0))]
    else:
        pts = [add(top, (1.4, -0.4)), F(0.2, -ln + 0.8), F(-0.5, 3.5), F(-4.0, 7.5), F(-6.0, 5.0), add(top, (-2.4, 2.0))]
    cm = R.mask(pts)
    Ck.paint(n_plate(cm, 1.6, (0.15, 0.05), 1.0, fold=lambda x, y: (0.55 * math.sin((x - P[0] - sw * 0.3) * 1.3), 0)),
             "D", bias=-1, ao=0)
    Ck.decal([q for q in cm if hash01(q[0], q[1], 19) < 0.08], ("D", 0))
    # quiver on the back with bone-white fletchings
    q0, q1 = F(-3.0, -ln + 0.5), F(-4.8, -1.2)
    R.cap(Ck, q0, q1, 1.25, 1.1, "L", bias=0)
    for k, d in enumerate(((0.0, -1.6), (0.9, -2.2), (-0.8, -1.9))):
        Ck.fixed({R.pt(add(q0, (d[0] - 0.4, d[1]))): "B4" if k != 1 else "B3"})
    # ---- draw arm (far side)
    arm(R, Ls["BackArm"], shB, p["hb"], 4.6, 4.8, 1.0, 0.9, "B", bias=-1, fore="L", fist="B", fist_r=0.9,
        pref=(-1, 0.9))
    # ---- legs: bone shanks with rag wraps
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        leg(LR, Ls[nm], hip, ft, 6.2, 6.4, 1.4, 1.0, "B", bias=bias, boot="L", flen=2.6, heel=1.2, boot_h=2.2, knee=kn)
    # ---- torso: leather jerkin over a ribcage
    Bd = Ls["Body"]
    torso = [F(-2.6, 0.8), F(-3.0, -ln + 2.2), F(-2.0, -ln - 0.9), F(1.4, -ln - 1.1), F(2.8, -ln + 1.2),
             F(2.2, -2.4), F(2.0, 0.8)]
    R.plate(Bd, torso, "L", bevel=1.6, tilt=(-0.2, 0.0))
    for k in range(3):
        R.dline(Bd, F(0.0, -ln + 2.2 + k * 1.5), F(2.2, -ln + 2.6 + k * 1.5), ("B", 3 - (k > 1)))
    R.dline(Bd, F(-2.8, -0.3), F(2.4, -0.3), ("L", 1))
    R.decal(Bd, [F(1.8, -0.3)], ("I", 4))
    R.cap(Bd, F(0.4, -ln - 0.4), add(Hd, (-0.4, 2.0)), 0.8, 0.8, "B", bias=-1)
    # skirt rags
    R.plate(Bd, [F(-2.8, 0.2), F(2.6, 0.2), F(3.0, 3.4), F(1.4, 2.6), F(0.2, 4.0), F(-1.4, 2.8), F(-3.0, 3.8)],
            "D", bevel=1.0, tilt=(0.1, 0))
    # ---- head: peaked hood, skull in shadow, one pale eye
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    R.dome(Hl, G(1.0, 0.8), 2.2, 2.5, "B", bias=0)
    R.decal(Hl, [G(1.6, 0.0), G(2.4, 0.0), G(1.6, -0.6)], ("B", 1))
    R.dline(Hl, G(1.4, 2.4), G(3.0, 2.2), ("B", 1))
    hood = [G(-3.4, 3.6), G(-3.8, -0.8), G(-2.8, -3.2), G(-0.6, -4.4), G(-2.2, -6.2), G(1.6, -4.2), G(3.4, -2.2),
            G(3.9, 0.4), G(2.4, -1.4), G(0.6, -1.0), G(0.0, 1.4), G(0.4, 3.6)]
    R.plate(Hl, hood, "D", bevel=1.4, tilt=(-0.1, -0.2), strength=1.2)
    R.dline(Hl, G(0.9, -1.1), G(3.1, -1.8), ("D", 0))
    if p["eye"]:
        e = R.pt(G(2.3, 0.0))
        FX.put([e], "Y2" if p["eye"] == 1 else "Y3")
        if p["eye"] > 1:
            FX.put([(e[0] + 1, e[1]), (e[0] - 1, e[1] - 1)], "Y1")
    # ---- bow + string + arrow
    if p["bow"] == "hand":
        grip, axis = p["hf"], p["bax"]
        gT, axT = R.T(grip), R.A(axis)
    else:
        gT, axT = p["bow"]
    pull = 0.0 if p["draw"] is None else p["draw"]
    bpts, fwd = bow_geom(gT, axT, pull)
    bpix = {}
    for i, (a, b) in enumerate(zip(bpts, bpts[1:])):
        for q in line(a, b):
            bpix[q] = "W4" if i < 7 else "W3" if i < 17 else "W2"
    for q in (ip(bpts[0]), ip(bpts[-1])):
        bpix[q] = "B4"
    gq = ip(gT)
    for d in ((0, 0), (0, 1), (0, -1)):
        bpix[(gq[0] + d[0], gq[1] + d[1])] = "L3"
    Ls["Bow"].fixed(bpix)
    tipT, tipB = bpts[0], bpts[-1]
    if p["draw"] is not None:
        nock = R.T(p["hb"])
        spts = line(tipT, nock) + line(nock, tipB)
    elif p["twang"]:
        mid = lerp(tipT, tipB, 0.5)
        mid = (mid[0] + p["twang"], mid[1])
        spts = line(tipT, mid) + line(mid, tipB)
    else:
        spts = line(tipT, tipB)
    Ls["Bow"].fill([q for q in spts if q not in bpix], "B3", noout=True)
    if p["arrow"]:
        nock = R.T(p["hb"]) if p["draw"] is not None else p["arrow"]
        head = (gT[0] + fwd[0] * 3.0 + 1.5, nock[1]) if p["draw"] is not None else (nock[0] + 13, nock[1])
        apix = {}
        for q in line(nock, head):
            apix[q] = "W4"
        hq = ip(head)
        apix.update({hq: "I5", (hq[0] - 1, hq[1]): "I4", (hq[0] - 1, hq[1] - 1): "I3", (hq[0] - 1, hq[1] + 1): "I2"})
        nq = ip(nock)
        apix.update({(nq[0], nq[1] - 1): "B4", (nq[0] + 1, nq[1] - 1): "B4", (nq[0], nq[1] + 1): "B3"})
        Ls["Arrow"].fixed(apix)
        info["arrow_head"] = head
        if p["glint"]:
            FX.put([(hq[0] + 1, hq[1] - 1), (hq[0] + 2, hq[1] - 2)], "B5")
            FX.put([(hq[0], hq[1] - 2), (hq[0] + 2, hq[1])], "B4")
    info["grip"] = gT
    info["fwd"] = fwd
    # ---- bow arm (near side), bony, with bracer
    Fa = Ls["FrontArm"]
    arm(R, Fa, shF, p["hf"], 4.6, 4.8, 1.1, 0.95, "B", bias=0, fore="L", fist="B", fist_r=1.0, pref=(-0.3, 1))
    R.dome(Fa, add(shF, (-0.3, 0.0)), 1.8, 1.6, "D", bias=0)
    if p["lines"]:
        x0, x1, ys = p["lines"]
        speed_lines(FX, x0, x1, ys, pal="bone", seed=fi)
    return Ls, info


def a_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((210, AP(P=(18, 27 + b * 0.4), C=(18.8, 20 + b), Hd=(20.2 + b * 0.2, 14.2 + b), hb=(15.5, 27.5 + b),
                           hf=(24, 27 + b * 0.8), bax=-58 + b * 2)))
    return fr


def a_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        ff = (18.6 + 4.4 * c, 39 - max(0.0, -s) * 2.6)
        fb = (18.0 - 4.4 * c, 39 - max(0.0, s) * 2.6)
        bob = 1.0 * abs(c)
        fr.append((115, AP(P=(18.2, 26.6 + bob), C=(19.2, 19.6 + bob), Hd=(20.8, 13.8 + bob), ff=ff, fb=fb,
                           hb=(16.0 - 1.6 * c, 27.2 + bob), hf=(23.6 + 1.4 * c, 26.8 + bob), bax=-60 + 5 * c)))
    return fr


AIM = dict(P=(17.6, 27.2), C=(17.8, 20.2), Hd=(19.0, 14.2), hup=(0.05, -1), fb=(13.0, 39), ff=(22.5, 39),
           hf=(27.4, 19.6), bax=-92)


def a_shoot():
    return [
        (140, AP(hb=(14.2, 16.6), hf=(24.0, 26.0), bax=-62, P=(18, 27.2), C=(18.4, 20.2), Hd=(19.8, 14.4))),
        (130, AP(**AIM, hb=(23.2, 19.8), draw=0.05, arrow=True)),
        (130, AP(**AIM, hb=(21.4, 19.6), draw=0.35, arrow=True)),
        (150, AP(**AIM, hb=(19.4, 19.3), draw=0.7, arrow=True)),
        (170, AP(**dict(AIM, C=(17.4, 20.3), Hd=(18.6, 14.4)), hb=(17.6, 19.1), draw=1.0, arrow=True, eye=2)),
        (380, AP(**dict(AIM, C=(17.3, 20.4), Hd=(18.5, 14.5)), hb=(17.3, 19.1), draw=1.0, arrow=True, eye=2,
                 glint=True)),
        (60, AP(**dict(AIM, hf=(28.0, 19.6)), hb=(13.4, 17.6), twang=1.6, lines=(29, 40, (19,)), wind=2)),
        (130, AP(**AIM, hb=(14.0, 18.4), twang=-0.8)),
        (200, AP(hb=(15.2, 26.0), hf=(25.0, 25.0), bax=-66, P=(18, 27.0), C=(18.6, 20.0), Hd=(20.0, 14.2))),
    ]


def a_hurt():
    return [(80, AP(P=(16.8, 27.2), C=(15.8, 20.4), Hd=(15.8, 14.8), hup=(-0.5, -1), hb=(13, 25.5), hf=(22, 24.5),
                    bax=-40, eye=2)),
            (140, AP(P=(17.4, 27.0), C=(17.4, 20.2), Hd=(18.4, 14.4), hup=(-0.2, -1), hb=(14.5, 27), hf=(23, 26.5),
                     bax=-50))]


def a_death():
    KN = dict(P=(16.4, 33.0), C=(17.6, 26.4), Hd=(19.4, 21.2), hup=(0.5, -1), kb=(14.4, 37.8), kf=(20.0, 37.8),
              fb=(9.5, 39), ff=(14.5, 39), hb=(16.0, 33.5), hf=(20.0, 34.0), eye=0, bow=((27.0, 36.6), 178))
    piv = (18.5, 37.5)
    fall = []
    for rot, ms in ((30, 110), (64, 110), (88, 700)):
        fall.append((ms, AP(**KN, rot=rot, piv=piv, legs_fixed=True,
                            snap=["Cloak", "BackArm", "Body", "Head", "FrontArm", "BackLeg", "FrontLeg"])))
    return [
        (100, AP(P=(16.6, 27.2), C=(15.4, 20.4), Hd=(15.2, 14.8), hup=(-0.6, -1), hb=(12.5, 25), hf=(22, 23.5),
                 bax=-30, eye=2)),
        (140, AP(P=(16.8, 30.0), C=(17.2, 23.4), Hd=(18.8, 17.8), hup=(0.3, -1), hb=(15, 31), hf=(22, 31),
                 bax=10, eye=1, fb=(12.5, 39), ff=(21.5, 39))),
        (200, AP(**dict(KN, bow=((25.5, 33.0), 150)))),
    ] + fall


def build_archer():
    K.setup(48, 40)
    anims, infos = render_anims(ARCHER_L, draw_archer, [("idle", a_idle), ("walk", a_walk), ("shoot", a_shoot),
                                                        ("hurt", a_hurt), ("death", a_death)])
    rel = infos["shoot"][5]["arrow_head"]
    meta = {"native": 1, "frame": [48, 40], "anchor": [18, 40],
            "hurtbox": hurtbox(anims, ["Body", "Head", "BackLeg", "FrontLeg"], inset=(1, 0, 1)),
            "attacks": {},
            "spawn": {"shoot": {"frame": 6, "at": [int(round(rel[0])), int(round(rel[1]))]}}}
    K.export("hollow_archer", ARCHER_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== 6. EMBER ACOLYTE
ACOLYTE_L = ["BackArm", "Robe", "Body", "Head", "Staff", "Censer", "FrontArm", "FX"]
E_NEU = dict(P=(20.0, 33.0), C=(20.6, 25.2), Hd=(21.8, 18.6), hup=(0.15, -1), hb=(17.0, 32.0), hf=(26.0, 31.0),
             sang=-84, csw=0.0, fire=1.0, eye=1, rot=0.0, piv=(0, 0), fallen=False, hem=0, staff="hand",
             wind=0.0, flash=False, orbit=0, puff=0, heap=0.0)
EP = mk(E_NEU)
STAFF = dict(lo=-12.0, hi=15.5)


def draw_acolyte(p, fi, sw):
    Ls = {n: Layer(n) for n in ACOLYTE_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(0.8, -ln + 0.8), F(-1.6, -ln + 1.0)
    info = {"hit": set()}
    floor = K.H - 1.0
    # ---- back sleeve
    arm(R, Ls["BackArm"], shB, p["hb"], 4.8, 5.0, 1.7, 2.2, "C", bias=-1, fist="B", fist_r=1.0, pref=(-1, 0.6))
    # ---- robe: long bell to the floor, burnt ragged hem, gold trim, rope belt
    Rb = Ls["Robe"]
    sx = -sw * 0.6
    if not p["fallen"]:
        hem = floor + 0.6 - p["heap"] * 0.4
        spread = 7.0 + p["heap"] * 4.0
        pts = [F(-3.2, -ln - 0.2), F(2.8, -ln - 0.6), F(3.6, -2.0), F(3.8, 1.0),
               (P[0] + spread * 0.95 + sx * 0.3, hem - 1.2)]
        n = 9
        for i in range(n + 1):     # flickering burnt hem teeth
            t = i / n
            x = P[0] + spread + sx * 0.3 - (2 * spread + 0.8) * t + sx * 0.4 * t
            d = 0.9 if (i + p["hem"]) % 2 == 0 else -0.3
            pts.append((x, hem + d))
        pts += [(P[0] - spread - 0.8 + sx * 0.7, hem - 1.4), F(-3.8, 1.0), F(-3.8, -2.0)]
        m = R.mask(pts)
    else:
        m = R.mask([F(-3.2, -ln - 0.2), F(2.8, -ln - 0.6), F(4.2, 3.0), F(6.0, 12.0), F(-1.0, 14.5), F(-6.0, 11.0),
                    F(-4.2, 2.0)])
    Rb.paint(n_plate(m, 2.2, (-0.05, 0.0), 1.0, fold=lambda x, y: (0.6 * math.sin((x - P[0] - sw * 0.2) * 1.15)
                                                                  * min(1.0, max(0.0, (y - P[1] + 4) / 10)), 0)),
             "C", bias=0)
    ys = [q[1] for q in m]
    ybot = max(ys) if ys else 0
    Rb.decal([q for q in m if q[1] >= ybot - 1 and not p["fallen"]], ("G", 2))
    Rb.decal([q for q in m if q[1] == ybot - 1 and q[0] % 2 == 0 and not p["fallen"]], ("G", 3))
    front = R.dline(Rb, F(2.4, -ln + 1.0), F(3.2, 0.0), ("G", 3))
    if not p["fallen"]:
        R.dline(Rb, F(3.2, 0.6), (P[0] + 4.6 + sx * 0.4, floor - 1.5), ("C", 1))
    R.dline(Rb, F(-3.6, -1.2), F(3.4, -1.2), ("L", 3))
    R.decal(Rb, [F(1.0, 0.0), F(1.2, 1.2), F(0.6, 2.2)], ("L", 2))
    if not p["fallen"] and p["fire"] > 0:
        for i in range(4):          # smouldering sparks on the hem
            x = int(P[0] - 6 + ((i * 5 + fi * 3) % 13))
            q = (x, int(floor) - (i + fi) % 2)
            if q in m:
                Rb.decal([q], "O3" if (i + fi) % 3 else "O4")
    # ---- head: tall peaked cowl + bone mask with ember eye-holes
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    R.plate(Hl, [G(-0.4, 3.4), G(0.4, -1.4), G(2.6, -1.0), G(3.4, 1.2), G(2.8, 3.8), G(0.8, 4.2)], "B", bevel=1.2,
            tilt=(-0.4, -0.1))
    R.dline(Hl, G(1.2, 2.6), G(2.8, 2.4), ("B", 1))
    hood = [G(-3.6, 4.4), G(-4.0, 0.0), G(-3.0, -3.4), G(-1.0, -5.2), G(1.6, -7.6), G(2.6, -4.0), G(3.8, -1.6),
            G(3.8, -0.6), G(0.8, -1.8), G(-0.4, 0.4), G(-0.6, 4.2)]
    R.plate(Hl, hood, "C", bevel=1.6, tilt=(-0.1, -0.2), strength=1.2, bias=-1)
    R.dline(Hl, G(0.4, -1.6), G(3.6, -1.0), ("G", 2))
    if p["eye"]:
        for k, d in enumerate(((1.4, 0.4), (2.8, 0.4))):
            FX.put([R.pt(G(*d))], ("O4" if k == 0 else "O3") if p["eye"] == 1 else "O5")
        if p["eye"] > 1:
            e = R.pt(G(2.8, 0.4))
            FX.put([(e[0] + 1, e[1] - 1), (e[0] + 2, e[1] - 2)], "O3")
    # ---- censer-staff: iron shaft, hooked crook, hanging burning censer
    St = Ls["Staff"]
    if p["staff"] == "hand":
        g, a = R.T(p["hf"]), R.A(p["sang"])
    else:
        g, a = p["staff"]
    ca, sa = dirv(a)
    s0 = (g[0] + ca * STAFF["lo"], g[1] + sa * STAFF["lo"])
    s1 = (g[0] + ca * STAFF["hi"], g[1] + sa * STAFF["hi"])
    spix = {}
    for i, q in enumerate(line(s0, s1)):
        spix[q] = "I4" if i % 5 else "I3"
    # crook: curls forward and down from the top
    fwd = (1 if ca * 0 - sa * 1 >= 0 else -1)
    px_, py_ = -sa, ca                     # perpendicular (right of the shaft direction)
    if px_ < 0:
        px_, py_ = -px_, -py_
    hook = [s1, (s1[0] + ca * 1.8 + px_ * 1.6, s1[1] + sa * 1.8 + py_ * 1.6),
            (s1[0] + ca * 0.8 + px_ * 3.4, s1[1] + sa * 0.8 + py_ * 3.4),
            (s1[0] - ca * 0.6 + px_ * 3.8, s1[1] - sa * 0.6 + py_ * 3.8)]
    for q in polyline(hook):
        spix[q] = "I4"
    spix[ip(s0)] = "G3"
    St.fixed(spix)
    hang = hook[-1]
    info["hook"] = hang
    cs = p["csw"]
    chain_end = (hang[0] + math.sin(math.radians(cs)) * 2.6, hang[1] + math.cos(math.radians(cs)) * 2.6)
    Ls["Censer"].fill(line(hang, chain_end)[1:], "I2", noout=True)
    cc = (chain_end[0], chain_end[1] + 2.4)
    Ce = Ls["Censer"]
    Ce.paint(n_dome(cc, 2.4, 2.5), "I", ao=0)
    cq = ip(cc)
    Ce.decal([(cq[0] - 1, cq[1]), (cq[0], cq[1]), (cq[0] + 1, cq[1]), (cq[0], cq[1] + 1)],
             "O4" if p["fire"] > 0 else "O0")
    Ce.decal([(cq[0], cq[1] - 1)], "O2" if p["fire"] > 0 else "I1")
    Ce.decal([(cq[0] - 1, cq[1] + 2), (cq[0], cq[1] + 2), (cq[0] + 1, cq[1] + 2)], ("G", 3))
    info["censer"] = cc
    if p["fire"] > 0:
        flame(FX, (cc[0], cc[1] - 1.6), 1.6 + p["fire"] * 1.1, fi, seed=3)
    # ---- near sleeve + bony hand on the staff
    arm(R, Ls["FrontArm"], shF, p["hf"], 4.8, 5.0, 1.8, 2.3, "C", bias=0, fist="B", fist_r=1.1, pref=(-1, 0.7))
    # ---- fx: charge orbit, release flash, smoke puff
    if p["orbit"]:
        n = p["orbit"]
        for k in range(3 + n * 2):
            ang = fi * 0.9 + k * 2 * math.pi / (3 + n * 2)
            r = 9.0 - n * 1.6
            q = ip((cc[0] + math.cos(ang) * r, cc[1] - 2 + math.sin(ang) * r * 0.7))
            FX.put([q], "O4" if k % 2 else "O3")
            FX.put([ip((cc[0] + math.cos(ang - 0.3) * (r + 1.2), cc[1] - 2 + math.sin(ang - 0.3) * (r + 1.2) * 0.7))],
                   "O2")
    if p["flash"]:
        c = ip(cc)
        for ang in range(0, 360, 45):
            L_ = 6 if ang % 90 == 0 else 3.5
            FX.put(line(c, (c[0] + math.cos(math.radians(ang)) * L_, c[1] + math.sin(math.radians(ang)) * L_)),
                   "O4" if ang % 90 == 0 else "O3")
        FX.put(list(mask_disc((c[0] + .5, c[1] + .5), 2.2)), "Y2")
        FX.put([c], "Y3")
    if p["puff"]:
        c = cc
        for k in range(7):
            q = ip((c[0] - 1 + math.cos(k * 0.9) * (2 + p["puff"]), c[1] - 3 - p["puff"] * 1.5 + math.sin(k * 1.3) * 1.6))
            FX.put([q], "A3" if k % 2 else "A2")
    return Ls, info


def e_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((170, EP(C=(20.6, 25.2 + b * 0.6), Hd=(21.8, 18.6 + b * 0.6), hf=(26, 31 + b * 0.4), hem=i,
                           csw=(0, 6, 0, -6)[i], fire=(1.0, 1.25, 0.9, 1.15)[i])))
    return fr


def e_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        b = 0.6 * abs(math.sin(ph))
        fr.append((130, EP(P=(20.2, 33.0 + b * 0.5), C=(21.2, 25.0 + b), Hd=(22.6, 18.4 + b), hf=(26.4, 30.6 + b),
                           sang=-80, hem=i, csw=-10 + 6 * math.sin(ph), fire=1.0 + 0.2 * math.sin(ph * 2), wind=-1.5)))
    return fr


def e_cast():
    up = dict(C=(19.8, 25.0), Hd=(20.8, 18.4), hup=(0.0, -1), hf=(26.0, 24.0), sang=-76, hb=(15.5, 26.5))
    cock = dict(P=(19.4, 33.2), C=(18.6, 25.4), Hd=(19.2, 18.8), hup=(-0.2, -1), hf=(22.8, 23.4), sang=-100,
                hb=(14.5, 25.5))
    return [
        (140, EP(hf=(25.6, 26.4), sang=-92, csw=10, fire=1.2)),
        (140, EP(**up, csw=-18, fire=1.5, eye=2, orbit=1)),
        (160, EP(**up, csw=-8, fire=1.9, eye=2, orbit=1)),
        (160, EP(**up, csw=4, fire=2.3, eye=2, orbit=2)),
        (160, EP(**dict(up, hf=(25.8, 23.6)), csw=0, fire=2.7, eye=2, orbit=3)),
        (220, EP(**cock, csw=24, fire=2.9, eye=2, orbit=3)),
        (70, EP(P=(20.6, 33.0), C=(22.4, 25.4), Hd=(24.2, 19.0), hup=(0.4, -1), hf=(28.8, 24.4), sang=-50,
                hb=(17.5, 30), csw=-40, fire=0.5, eye=2, flash=True, wind=3)),
        (120, EP(P=(20.4, 33.0), C=(22.0, 25.4), Hd=(23.8, 18.9), hup=(0.35, -1), hf=(28.4, 25.4), sang=-56,
                 hb=(17.5, 30.5), csw=-25, fire=0.5, puff=1)),
        (160, EP(hf=(27.0, 28.4), sang=-70, csw=10, fire=0.7, puff=2)),
        (160, EP(hf=(26.2, 30.6), sang=-82, csw=-4, fire=0.9)),
    ]


BURN = ["BackArm", "Robe", "Body", "Head", "Staff", "Censer", "FrontArm"]


def e_blink():
    def burn(frac, seed=0):
        return lambda imgs: K.ember_dissolve(imgs, frac, BURN, seed=seed)
    crouch = dict(P=(20.0, 34.0), C=(20.2, 26.6), Hd=(21.2, 20.0), hf=(25.4, 30.6), sang=-86, hb=(16.5, 32.5))
    return [
        (100, EP(**crouch, fire=2.2, eye=2, csw=8, orbit=2)),
        (80, EP(**crouch, fire=2.4, eye=2, csw=6, post=burn(0.22))),
        (80, EP(**crouch, fire=1.8, eye=2, csw=4, post=burn(0.48))),
        (80, EP(**crouch, fire=1.2, eye=2, csw=2, post=burn(0.72))),
        (80, EP(**crouch, fire=0.6, eye=0, post=burn(0.95))),
        (100, EP(**crouch, fire=0.0, eye=0, post=burn(1.25))),
    ]


def e_hurt():
    return [(80, EP(P=(19.2, 33.2), C=(18.4, 25.6), Hd=(18.6, 19.2), hup=(-0.45, -1), hf=(24.6, 29.6), sang=-70,
                    hb=(15.0, 29.0), csw=25, fire=1.6, eye=2)),
            (140, EP(P=(19.6, 33.0), C=(19.8, 25.4), Hd=(20.6, 18.8), hup=(-0.1, -1), hf=(25.4, 30.6), sang=-80,
                     csw=12, fire=1.1))]


def e_death():
    heap = dict(P=(19.6, 40.0), C=(21.0, 33.2), Hd=(23.2, 27.6), hup=(0.6, -1), hf=(25.0, 40.0), hb=(17.0, 40.0),
                heap=1.0, staff=((31.0, 46.4), 182), csw=90, fire=0.4, eye=0)
    piv = (22.0, 44.0)
    return [
        (100, EP(P=(19.0, 33.2), C=(17.8, 25.6), Hd=(17.8, 19.2), hup=(-0.5, -1), hf=(23.6, 28.6), sang=-60,
                 hb=(14.5, 28.0), csw=30, fire=1.6, eye=2)),
        (140, EP(P=(19.4, 36.0), C=(20.0, 28.4), Hd=(21.4, 21.8), hup=(0.2, -1), hf=(25.0, 34.0), sang=-40,
                 hb=(17.0, 35.0), heap=0.4, csw=-20, fire=1.0, eye=1)),
        (180, EP(**dict(heap, staff=((27.0, 43.0), 200), csw=40, fire=0.8))),
        (120, EP(**heap, rot=35, piv=piv, snap=["BackArm", "Robe", "Head", "FrontArm"])),
        (120, EP(**dict(heap, fire=0.15), rot=62, piv=piv, fallen=True, snap=["BackArm", "Robe", "Head", "FrontArm"])),
        (700, EP(**dict(heap, fire=0.0, puff=2), rot=76, piv=piv, fallen=True,
                 snap=["BackArm", "Robe", "Head", "FrontArm"])),
    ]


def build_acolyte():
    K.setup(48, 48)
    anims, infos = render_anims(ACOLYTE_L, draw_acolyte, [("idle", e_idle), ("walk", e_walk), ("cast", e_cast),
                                                          ("blink", e_blink), ("hurt", e_hurt), ("death", e_death)],
                                loops=("idle", "walk"))
    cc = infos["cast"][6]["censer"]
    meta = {"native": 1, "frame": [48, 48], "anchor": [20, 48],
            "hurtbox": hurtbox(anims, ["Robe", "Head"], inset=(2, 0, 2)),
            "attacks": {},
            "spawn": {"cast": {"frame": 6, "at": [int(round(cc[0])), int(round(cc[1]))]}}}
    K.export("ember_acolyte", ACOLYTE_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== 7. GRAVE KNIGHT
KNIGHT_L = ["Cape", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "Weapon", "FrontArm", "FX"]
GSWORD = dict(pommel=-6.2, grip_end=0.8, grip="L1", grip_w=0.8, pommel_c="G3", guard=(1.0, 2.4, 4.4), guard_c="G2",
              guard_hi="G4", b0=2.4, end=27.0, w_edge=1.7, w_spine=1.4, taper=0.16, fuller="I1",
              edge_hi="I5", edge="I4", spine="I3")
N_NEU = dict(P=(27.5, 35.5), C=(28.6, 24.6), Hd=(30.2, 14.6), hup=(0.12, -1), fb=(21.0, 55), ff=(34.0, 55),
             hf=(36.0, 34.5), wang=52, wl="Weapon", rot=0.0, piv=(0, 0), legs_fixed=False, kb=None, kf=None,
             eye=1, smear=None, sword="hand", onehand=False, hb=None, wind=0.0, impact=0, fallen=False)
NP = mk(N_NEU)


def draw_knight(p, fi, sw):
    Ls = {n: Layer(n) for n in KNIGHT_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    LR = ID if p["legs_fixed"] else R
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(1.2, -ln + 2.0), F(-3.2, -ln + 2.2)
    hB, hF = F(-2.6, 1.0), F(2.6, 1.0)
    if p["legs_fixed"]:
        hB, hF = R.T(hB), R.T(hF)
    info = {"hit": set()}
    floor = K.H - 1
    # ---- weapon geometry first (hands depend on it)
    if p["sword"] == "hand":
        pix, blade, tip = blade_px(R, p["hf"], p["wang"], GSWORD)
        ca, sa = dirv(p["wang"])
        hand2 = (p["hf"][0] - ca * 3.6, p["hf"][1] - sa * 3.6)
    else:
        pix, blade, tip = blade_px(ID, *p["sword"], GSWORD)
        hand2 = None
    pix = {q: c for q, c in pix.items() if q[1] <= floor}
    blade = {q for q in blade if q[1] <= floor}
    Ls[p["wl"]].fixed(pix)
    info["hit"] |= blade
    info["tip"] = tip
    # ---- cape: tattered ash-pale cloak behind
    Cp = Ls["Cape"]
    sx = -sw * 0.9
    ctop = F(-3.6, -ln - 0.4)
    if not p["fallen"]:
        hem = min(floor - 2.0, P[1] + 15.5)
        pts = [add(ctop, (3.0, -1.0)), F(0.0, -ln + 2.0), F(-3.4, 0.0), (P[0] - 3.4 + sx * 0.3, hem - 1)] + \
            rag_hem(P[0] - 13.5 + sx * 1.1, P[0] - 3.2 + sx * 0.4, hem, fi, 23, 3.4) + \
            [(P[0] - 12.6 + sx * 1.0, P[1] + 2.0), add(ctop, (-4.6, 3.0))]
    else:
        pts = [add(ctop, (3.0, -1.0)), F(0.0, -ln + 2.0), F(-2.0, 6.0), F(-7.0, 12.0), F(-10.0, 8.0),
               add(ctop, (-4.0, 3.0))]
    cm = R.mask(pts)
    Cp.paint(n_plate(cm, 2.2, (0.2, 0.05), 1.0, fold=lambda x, y: (0.6 * math.sin((x - P[0] - sw * 0.3) * 0.9), 0)),
             "P", bias=-1, ao=0)
    Cp.decal([q for q in cm if hash01(q[0], q[1], 29) < 0.06], ("P", 0))
    # ---- back arm (two-handed grip or free)
    hbk = p["hb"] or hand2 or F(-3.5, -2.0)
    arm(R, Ls["BackArm"], shB, hbk, 7.6, 7.8, 2.4, 2.1, "K", bias=-1, fist_r=1.9, pref=(-1, 0.6))
    R.dome(Ls["BackArm"], add(shB, (0.2, -0.6)), 3.4, 3.0, "K", bias=-1)
    # ---- legs: black plate with gold-dotted poleyns
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(LR, Ls[nm], hip, ft, 9.9, 10.0, 3.0, 2.5, "K", bias=bias, flen=4.4, heel=2.2, boot_h=3.4, knee=kn)
        LR.dome(Ls[nm], add(k, (0.6, 0.0)), 2.6, 2.4, "K", bias=bias)
        LR.decal(Ls[nm], [add(k, (0.9, 0.2))], ("G", 4 + bias))
        LR.dline(Ls[nm], add(k, (-1.4, 2.4)), add(k, (1.8, 2.2)), ("G", 2 + bias))
    # ---- torso
    Bd = Ls["Body"]
    faulds = [F(-6.0, -2.0), F(5.4, -2.0), F(6.2, 4.6), F(-6.6, 4.6)]
    fm = R.plate(Bd, faulds, "K", bevel=1.6, tilt=(0.0, 0.2), bias=-1)
    for k in range(2):
        R.dline(Bd, F(-6.2, 0.4 + k * 2.2), F(5.8, 0.4 + k * 2.2), ("K", 0))
    R.dline(Bd, F(-6.4, 4.2), F(6.0, 4.2), ("G", 2))
    torso = [F(-6.0, -1.0), F(-6.8, -ln + 3.4), F(-4.6, -ln - 1.6), F(3.0, -ln - 2.2), F(6.4, -ln + 1.0),
             F(6.6, -ln + 6.0), F(5.2, -1.0)]
    tm = R.plate(Bd, torso, "K", bevel=3.0, tilt=(-0.35, -0.15), strength=1.35)
    R.dline(Bd, F(1.6, -ln - 1.8), F(2.2, -2.0), ("K", 4))           # ridge
    R.dline(Bd, F(2.4, -ln - 1.6), F(3.0, -2.0), ("K", 1))
    R.dline(Bd, F(-4.4, -ln - 1.3), F(3.0, -ln - 1.9), ("G", 3))     # neck trim
    R.dline(Bd, F(-5.6, -1.2), F(5.2, -1.2), ("G", 2))               # waist trim
    ec = F(3.6, -ln + 4.2)                                            # gold grave-sun emblem
    ring = [q for q in mask_disc(R.T(ec), 2.2) if q not in mask_disc(R.T(ec), 1.2)]
    Bd.decal(ring, ("G", 3))
    Bd.decal([R.pt(ec)], ("G", 4))
    R.decal(Bd, [add(ec, (0, -3.0)), add(ec, (0, 3.0)), add(ec, (-3.0, 0)), add(ec, (3.0, 0))], ("G", 2))
    # tabard strip (ash cloth) hanging in front
    tx = F(1.8, -2.0)
    if not p["fallen"]:
        tb = [add(tx, (-2.6, 0)), add(tx, (2.8, 0)), add(tx, (3.4 - sw * 0.4, 9.0)), add(tx, (1.4 - sw * 0.6, 12.0)),
              add(tx, (0.2 - sw * 0.6, 10.0)), add(tx, (-1.4 - sw * 0.6, 12.4)), add(tx, (-3.0 - sw * 0.4, 9.0))]
        tbm = R.plate(Bd, tb, "P", bevel=1.4, tilt=(-0.2, 0.0), fold=lambda x, y: (0.4 * math.sin(x * 1.3), 0))
        Bd.decal([q for q in tbm if hash01(q[0], q[1], 31) < 0.08], ("P", 1))
    # neck / gorget
    R.cap(Bd, F(0.4, -ln - 1.0), add(Hd, (-0.6, 4.4)), 2.6, 2.4, "K", bias=-1)
    # ---- head: great helm with a tall tombstone crest, T-visor, pale-gold eyes
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    crest = [G(-3.0, -4.2), G(-2.8, -8.0), G(-1.2, -10.4), G(0.6, -10.6), G(2.0, -8.4), G(2.0, -4.4)]
    cr = R.plate(Hl, crest, "K", bevel=1.2, tilt=(-0.3, -0.2))
    Hl.decal([q for q in cr if any((q[0] + a, q[1] + b) not in cr for a, b in ((1, 0), (-1, 0), (0, -1)))], ("G", 3))
    helm = [G(-4.4, 4.6), G(-4.8, -1.6), G(-3.6, -4.8), G(2.4, -5.4), G(4.8, -3.0), G(5.2, 1.6), G(4.2, 4.8)]
    R.plate(Hl, helm, "K", bevel=2.0, tilt=(-0.3, -0.2), strength=1.3)
    R.dline(Hl, G(0.6, -5.2), G(0.8, 4.6), ("K", 4))
    R.dline(Hl, G(1.4, -1.2), G(5.0, -1.2), "OUT")
    R.dline(Hl, G(3.0, -1.2), G(3.0, 3.2), "OUT")
    R.dline(Hl, G(-4.2, 4.2), G(3.8, 4.4), ("G", 3))
    for k in range(3):
        R.decal(Hl, [G(-2.4 + k * 1.3, 1.6)], ("G", 2))
    if p["eye"]:
        for k, d in enumerate(((1.8, -1.2), (4.2, -1.2))):
            FX.put([R.pt(G(*d))], ("Y2" if k == 0 else "Y1") if p["eye"] == 1 else "Y3")
        if p["eye"] > 1:
            e = R.pt(G(4.2, -1.2))
            FX.put([(e[0] + 1, e[1]), (e[0] + 2, e[1] - 1), (e[0] + 3, e[1] - 1)], "Y1")
            FX.put([(e[0] - 3, e[1] - 1)], "Y2")
    # ---- near arm + layered pauldron
    Fa = Ls["FrontArm"]
    arm(R, Fa, shF, p["hf"], 7.6, 7.8, 2.6, 2.2, "K", bias=0, fist_r=2.0, pref=(-1, 0.7))
    for k, (dx, dy, rx, ry) in enumerate(((0.8, 3.4, 4.0, 2.4), (0.4, 1.2, 4.6, 2.8), (0.0, -1.2, 5.0, 3.6))):
        c = add(shF, (dx, dy))
        m = R.dome(Fa, c, rx, ry, "K", tilt=(0.05, 0.1))
        rim = [q for q in m if (q[0], q[1] + 1) not in m]
        Fa.decal(rim, ("G", 3))
    R.decal(Fa, [add(shF, (-1.4, -3.4)), add(shF, (-0.4, -4.0))], ("K", 5))
    # ---- fx
    if p["smear"]:
        sm = p["smear"]
        hot = swept(FX, R.T(sm["g0"]), sm["a0"], R.T(p["hf"]), R.A(p["wang"]), 8, GSWORD["end"] + 0.5, hw=1.2,
                    mid=sm.get("mid"), start=sm.get("start", 0.0), pal="steel", exclude=blade,
                    taper=sm.get("taper", 0.72), clip_y=floor)
        info["hit"] |= hot
    if p["impact"]:
        stage = p["impact"]
        ix = int(round(min(tip[0], K.W - 4)))
        pts = set()
        for k in range(14):
            a = -math.pi * (0.08 + 0.84 * hash01(k, 7, 50))
            r = (3 + 12 * hash01(k, 8, 51)) * (0.6 if stage == 1 else 1.0)
            q = ip((ix + math.cos(a) * r * 1.2, floor - 1 + math.sin(a) * r * (0.9 if stage == 1 else 0.7)
                    + (0 if stage == 1 else 2.5 * (r / 10) ** 2)))
            c = ("B5", "B4", "I4")[k % 3] if stage == 1 else ("I4", "A3", "A2")[k % 3]
            FX.put([q], c)
            if k % 3 == 0 and stage == 1:
                FX.put([(q[0] + 1, q[1])], c)
            pts.add(q)
        for dx in range(-10, 11):     # ground crack glow along the floor
            if abs(dx) < (9 if stage == 1 else 11) and hash01(dx, 3, 52) < 0.7:
                FX.put([(ix + dx, floor)], "B4" if abs(dx) < 3 else "I4" if stage == 1 else "I2")
        if stage == 1:
            for ang in range(-160, -10, 30):
                FX.put(line((ix, floor - 1), (ix + math.cos(math.radians(ang)) * 7, floor - 1 + math.sin(math.radians(ang)) * 5)),
                       "B5" if ang % 60 == 0 else "B4")
        info["hit"] |= pts
        info["impact_x"] = ix
    return Ls, info


def n_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((230, NP(P=(27.5, 35.5 + b * 0.4), C=(28.6, 24.6 + b), Hd=(30.2, 14.6 + b), hf=(36.0, 34.5 + b * 0.6),
                           wang=52 - b)))
    return fr


def n_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        ff = (28.2 + 6.4 * c, 55 - max(0.0, -s) * 3.4)
        fb = (27.2 - 6.4 * c, 55 - max(0.0, s) * 3.4)
        bob = 1.4 * abs(c)
        fr.append((150, NP(P=(27.8, 35.0 + bob), C=(29.2, 24.2 + bob), Hd=(30.9, 14.2 + bob), ff=ff, fb=fb,
                           hf=(36.4 + 0.8 * c, 34.0 + bob), wang=50 + 3 * c)))
    return fr


def n_combo():
    WB = dict(wl="WeaponBack")
    cock = dict(P=(26.4, 36.4), C=(25.4, 25.4), Hd=(26.0, 15.6), hup=(-0.2, -1), fb=(18.0, 55), ff=(34.5, 55))
    lunge = dict(P=(31.0, 37.8), C=(34.4, 27.4), Hd=(37.4, 18.4), hup=(0.45, -1), fb=(20.5, 55), ff=(40.5, 55))
    low = dict(P=(27.6, 38.6), C=(26.8, 28.0), Hd=(28.0, 18.4), hup=(-0.1, -1), fb=(19.5, 55), ff=(37.0, 55))
    rise = dict(P=(31.0, 36.4), C=(33.4, 25.6), Hd=(35.6, 16.0), hup=(0.3, -1), fb=(21.0, 55), ff=(40.0, 55))
    return [
        (150, NP(P=(27.0, 35.8), C=(27.6, 24.8), Hd=(29.0, 14.8), hf=(33.0, 26.0), wang=-58)),
        (200, NP(**cock, hf=(27.6, 19.6), wang=-142, **WB)),
        (320, NP(**dict(cock, C=(25.0, 25.8), Hd=(25.4, 16.0)), hf=(25.6, 18.4), wang=-150, eye=2, **WB)),
        (60, NP(**lunge, hf=(43.0, 33.0), wang=38, wind=4,
                smear=dict(g0=(25.6, 18.4), a0=-150, mid=(38.0, 12.0), start=0.15))),
        (90, NP(**lunge, hf=(41.5, 38.5), wang=86, wind=3, smear=dict(g0=(43.0, 33.0), a0=38, taper=0.55))),
        (140, NP(**dict(lunge, C=(33.4, 28.0), Hd=(36.0, 19.0)), hf=(36.0, 42.0), wang=150, **WB)),
        (160, NP(**low, hf=(28.6, 40.0), wang=170, **WB)),
        (240, NP(**dict(low, C=(26.2, 28.4), Hd=(27.2, 18.8)), hf=(28.2, 40.2), wang=174, eye=2, **WB)),
        (60, NP(**rise, hf=(44.0, 27.0), wang=-18, wind=4,
                smear=dict(g0=(28.2, 40.2), a0=174 - 360, mid=(40.0, 46.0), start=0.1))),
        (90, NP(**rise, hf=(42.0, 20.0), wang=-62, wind=3, smear=dict(g0=(44.0, 27.0), a0=-18, taper=0.5))),
        (180, NP(P=(29.0, 36.0), C=(30.6, 25.2), Hd=(32.4, 15.4), fb=(20.0, 55), ff=(37.0, 55), hf=(38.0, 30.0),
                 wang=10)),
        (200, NP(P=(28.0, 35.6), C=(29.0, 24.8), Hd=(30.6, 14.8), hf=(36.4, 33.6), wang=46)),
    ]


def n_slam():
    WB = dict(wl="WeaponBack")
    up = dict(P=(27.0, 34.6), C=(26.8, 23.6), Hd=(27.8, 13.6), hup=(-0.05, -1), fb=(21.0, 55), ff=(34.0, 55))
    land = dict(P=(30.8, 38.8), C=(34.2, 28.6), Hd=(37.4, 19.8), hup=(0.5, -1), fb=(20.0, 55), ff=(40.0, 55))
    return [
        (160, NP(P=(27.2, 36.8), C=(28.0, 26.0), Hd=(29.4, 16.2), hf=(34.0, 32.0), wang=18)),
        (160, NP(P=(27.2, 36.0), C=(27.6, 25.0), Hd=(29.0, 15.2), hf=(33.0, 25.0), wang=-58)),
        (180, NP(**up, hf=(29.5, 11.0), wang=-162, **WB)),
        (200, NP(**dict(up, P=(26.8, 34.0), C=(26.2, 23.0), Hd=(26.8, 13.0), fb=(21.5, 54)), hf=(28.6, 7.6),
                 wang=-200, **WB)),
        (320, NP(**dict(up, P=(26.6, 34.0), C=(25.8, 23.0), Hd=(26.2, 13.2), hup=(-0.2, -1), fb=(21.5, 54)),
                 hf=(28.0, 7.2), wang=-212, eye=2, **WB)),
        (60, NP(**dict(land, P=(29.6, 37.0), C=(32.0, 26.0), Hd=(34.6, 16.6)), hf=(40.0, 19.0), wang=-20, wind=4,
                smear=dict(g0=(28.0, 7.2), a0=-212, mid=(33.0, 0.0), start=0.2))),
        (70, NP(**land, hf=(44.0, 37.0), wang=34, impact=1, wind=3,
                smear=dict(g0=(40.0, 19.0), a0=-20, taper=0.5))),
        (120, NP(**land, hf=(44.0, 37.4), wang=34, impact=2)),
        (220, NP(**dict(land, P=(29.8, 37.4), C=(32.4, 26.8), Hd=(35.0, 17.6)), hf=(41.0, 35.0), wang=42)),
        (220, NP(P=(28.2, 36.0), C=(29.4, 25.2), Hd=(31.0, 15.2), hf=(37.0, 34.0), wang=48)),
    ]


def n_hurt():
    return [(80, NP(P=(26.2, 35.8), C=(25.0, 25.0), Hd=(25.2, 15.2), hup=(-0.35, -1), hf=(33.5, 32.0), wang=30, eye=2)),
            (150, NP(P=(27.0, 35.6), C=(27.4, 24.8), Hd=(28.6, 14.8), hup=(-0.1, -1), hf=(35.0, 34.0), wang=44))]


def n_death():
    KN = dict(P=(25.6, 44.6), C=(28.2, 33.6), Hd=(31.2, 24.0), hup=(0.35, -1), kb=(23.0, 54.0), kf=(33.0, 54.2),
              fb=(13.5, 55), ff=(23.5, 55), eye=0)
    plant = ((40.0, 37.0), 90)
    piv = (26.0, 44.6)
    fall = []
    for rot, ms in ((22, 130), (52, 120), (74, 800)):
        fall.append((ms, NP(**dict(KN, C=(27.6, 33.4), Hd=(30.0, 23.6)), rot=rot, piv=piv, legs_fixed=True,
                            fallen=True, sword=((42.0, 54.4), 2), hf=(34.0, 44.0), hb=(30.0, 45.0),
                            snap=["Cape", "BackArm", "Body", "Head", "FrontArm"])))
    return [
        (130, NP(P=(26.0, 35.8), C=(24.6, 25.2), Hd=(24.4, 15.6), hup=(-0.5, -1), hf=(33.0, 30.0), wang=20, eye=2)),
        (150, NP(P=(26.6, 39.6), C=(28.4, 28.8), Hd=(30.8, 19.2), hup=(0.2, -1), fb=(19.5, 55), ff=(33.5, 55),
                 sword=plant, hf=(39.6, 36.6), hb=(38.0, 38.0), eye=1)),
        (220, NP(**KN, sword=plant, hf=(39.4, 37.0), hb=(37.6, 38.4))),
        (320, NP(**dict(KN, C=(28.6, 34.2), Hd=(32.0, 25.6), hup=(0.6, -1)), sword=plant, hf=(39.4, 37.6),
                 hb=(37.6, 38.8))),
        (140, NP(**dict(KN, C=(29.4, 35.0), Hd=(33.4, 27.0), hup=(0.7, -1)), sword=((42.0, 42.0), 60),
                 hf=(38.0, 41.0), hb=(36.0, 41.0))),
    ] + fall


def build_knight():
    K.setup(72, 56)
    anims, infos = render_anims(KNIGHT_L, draw_knight, [("idle", n_idle), ("walk", n_walk), ("combo", n_combo),
                                                        ("slam", n_slam), ("hurt", n_hurt), ("death", n_death)])
    meta = {"native": 1, "frame": [72, 56], "anchor": [28, 56],
            "hurtbox": hurtbox(anims, ["Body", "Head", "BackLeg", "FrontLeg"], inset=(2, 0, 2)),
            "attacks": {
                "combo": {"windows": [
                    {"active": [3, 4], "hit": hit_rect(infos, "combo", [3, 4], x_min=32)},
                    {"active": [8, 9], "hit": hit_rect(infos, "combo", [8, 9], x_min=32)}]},
                "slam": {"active": [6, 7], "hit": hit_rect(infos, "slam", [6, 7], x_min=32)}}}
    K.export("grave_knight", KNIGHT_L, anims, meta, build=BUILD)
    return meta


# =========================================================================== projectiles
def build_projectiles():
    # ---- arrow 16x8, flying right, centred on (8, 4)
    K.setup(16, 8)
    frames = []
    for i in range(2):
        L = Layer("Arrow")
        fx = FXLayer("FX")
        pix = {}
        for x in range(3, 13):
            pix[(x, 4)] = "W4" if x % 3 else "W3"
        pix.update({(13, 3): "I4", (13, 4): "I5", (13, 5): "I2", (14, 4): "I5", (12, 4): "I3"})
        fl = 1 if i else 0
        pix.update({(2, 4): "B3", (3, 3 - fl): "B5", (4, 3): "B4", (2, 3 - fl): "B4",
                    (3, 5 + fl): "B3", (4, 5): "B2", (2, 5 + fl): "B2"})
        L.fixed(pix)
        for x in range(0, 2 + i):
            fx.put([(x, 4)], "B2" if x == 1 else "B1")
        frames.append((70, {"Arrow": K.render_layer(L), "FX": fx.image()}))
    K.export("proj_arrow", ["FX", "Arrow"], [("fly", frames)], None, build=BUILD)
    # ---- fireball 16x16, flying right, centred on (8, 8)
    K.setup(16, 16)
    frames = []
    for i in range(4):
        core, glow = FXLayer("Core"), FXLayer("Glow")
        cx, cy = 9.5, 8.0
        for y in range(16):
            for x in range(16):
                dx, dy = x + .5 - cx, y + .5 - cy
                r = math.hypot(dx * (0.9 if dx < 0 else 1.1), dy)
                # flame tail streaming left, flickering per frame
                tail = 0.0
                if dx < 0:
                    wav = math.sin(-dx * 0.9 + i * 1.6) * 1.1
                    tail = max(0.0, 1 - abs(dy - wav * (-dx / 8)) / max(0.6, 4.4 - (-dx) * 0.42))
                    if -dx > 9.5:
                        tail = 0.0
                if r < 1.6:
                    core.put([(x, y)], "Y3")
                elif r < 2.7:
                    core.put([(x, y)], "Y2")
                elif r < 3.7:
                    core.put([(x, y)], "Y1" if (x + y + i) % 5 else "Y2")
                elif r < 4.6:
                    glow.put([(x, y)], "O4")
                elif r < 5.4 and hash01(x, y, i) < 0.8:
                    glow.put([(x, y)], "O3")
                elif tail > 0.1 and (tail > 0.35 or hash01(x, y, 70 + i) < 0.5):
                    glow.put([(x, y)], "Y1" if tail > 0.75 and -dx < 6.5 else "O4" if tail > 0.5 else
                             "O3" if tail > 0.3 else "O2")
        for k in range(3):   # loose sparks trailing
            t = (i * 0.25 + k * 0.33) % 1.0
            q = (int(cx - 5 - t * 6), int(cy + (k - 1) * 3 - t * 1.5))
            glow.put([q], "O4" if t < 0.4 else "O2")
        frames.append((70, {"Glow": glow.image(), "Core": core.image()}))
    K.export("proj_fireball", ["Glow", "Core"], [("fly", frames)], None, build=BUILD)
    return {"proj_arrow": [16, 8], "proj_fireball": [16, 16]}


# =========================================================================== main
ENEMIES = {
    "hollow_soldier": build_soldier,
    "shield_warden": build_warden,
    "rot_crawler": build_crawler,
    "gloom_wisp": build_wisp,
    "hollow_archer": build_archer,
    "ember_acolyte": build_acolyte,
    "grave_knight": build_knight,
    "projectiles": build_projectiles,
}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    for name, fn in ENEMIES.items():
        if only and name not in only:
            continue
        meta = fn()
        print(name, meta)


if __name__ == "__main__":
    main()
