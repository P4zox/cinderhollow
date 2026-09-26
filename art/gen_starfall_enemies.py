#!/usr/bin/env python3
"""Starfall Crater enemies (agent SF).  python3 art/gen_starfall_enemies.py [--preview]

sf_pilgrim 48x48  idle(4) walk(6) attack(9) hurt(2) death(6)   star-touched pilgrim: hooded, a star where the face was,
                                                               a crook-staff with a star lantern; overhead staff strike
sf_golem   64x64  idle(4) walk(6) smash(10) hurt(2) death(8)   glass golem: tall, angular obsidian shards, a star in the
                                                               chest; double-handed smash; shatters on death
sf_wisp    40x32  fly(6) dive(6) hurt(2) death(6)              comet wisp: a pale comet head with a long tail (anchor = centre)
"""
import math, os, sys
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, hash01, n_dome, n_plate, leg, arm, swept, mask_disc  # noqa: E402

BUILD = "--preview" not in sys.argv
EXTRA = {
    "X0": "#1a2a66", "X1": "#3a5ac4", "X2": "#7a9cf2", "X3": "#c6d8ff", "X4": "#ffffff",
    "Z0": "#07070f", "Z1": "#0f1022", "Z2": "#191c3a", "Z3": "#262c56", "Z4": "#3a4680", "Z5": "#7e92d6",
    "N0": "#0c0c18", "N1": "#1a1a32", "N2": "#2a2d50", "N3": "#40466e", "N4": "#646c9c",
    "J0": "#1c1e2c", "J1": "#3a3e52", "J2": "#636a80", "J3": "#9aa2b6", "J4": "#d2d8e4",
}
for k_, v_ in EXTRA.items():
    K.HEX[k_] = v_
    K.RGBA[k_] = tuple(int(v_[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k_[0], []).append(k_)
K.SHINY["Z"] = 0.88
K.SMEAR["star"] = ["X4", "X3", "X2", "X1"]


# ======================================================================== pilgrim
def pilgrim_frame(p, fi):
    K.setup(48, 48)
    Ls = {n: Layer(n) for n in ("Back", "Robe", "Staff", "Arm")}
    FX = FXLayer("FX")
    FL = 47
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P); ln = math.hypot(*upv); F = basis(P, upv)
    # robe: a tall tattered cone from the shoulders to the floor
    sw = p.get("sw", 0)
    hem = []
    for i in range(9):
        t = i / 8
        x0_, x1_ = F(-6.5, 0)[0] - 1 + sw, F(6.0, 0)[0] + 1 + sw * 0.5
        x = x0_ + (x1_ - x0_) * t
        hem.append((x, FL - (1.5 if i % 2 else 0) - p.get("lift", 0)))
    robe = [F(-3.6, -ln + 0.5), F(3.2, -ln)] + [F(5.0, -ln * 0.4)] + hem[::-1] + [F(-5.2, -ln * 0.4)]
    rm = ID.plate(Ls["Robe"], robe, "N", bevel=2.0, tilt=(-0.3, -0.1), strength=1.0,
                  fold=lambda x, y: (0.6 * math.sin(x * 0.9 + sw), 0))
    for q in rm:                                      # starlight stitched into the hem
        if q[1] > FL - 4 and hash01(q[0], 1, fi // 2) < 0.12:
            Ls["Robe"].decal([q], "X2")
    ID.dline(Ls["Robe"], F(0.6, -ln + 2), F(1.2, -2), ("N", 1))
    # hood with a star where the face was
    G = basis(Hd, (0.15, -1))
    hood = [G(-3.8, 3.5), G(-3.6, -2.5), G(-1.0, -5.0), G(2.8, -4.0), G(4.2, -0.5), G(3.6, 3.6)]
    ID.plate(Ls["Robe"], hood, "N", bevel=1.6, tilt=(-0.3, -0.3), strength=1.2)
    face = [G(0.6, -2.0), G(3.2, -1.8), G(3.4, 2.4), G(0.8, 2.6)]
    Ls["Robe"].fill(K.poly_mask(face), "N0")
    s = ip(G(2.0, 0.2))
    Ls["Robe"].fixed({s: "X4", (s[0] + 1, s[1]): "X3", (s[0] - 1, s[1]): "X2", (s[0], s[1] - 1): "X3", (s[0], s[1] + 1): "X2"})
    # the crook-staff with its star lantern
    ang = p["sang"]; grip = p["hand"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    top = (grip[0] + ca * 20, grip[1] + sa * 20); bot = (grip[0] - ca * 14, grip[1] - sa * 14)
    for q in line(bot, top):
        Ls["Staff"].fixed({q: "W2"})
    hook = bezier(top, add(top, (ca * 3 - sa * 3, sa * 3 + ca * 3)), add(top, (-sa * 6, ca * 6)), add(top, (-sa * 6 - ca * 2, ca * 6 - sa * 2)), n=8)
    for q in polyline(hook):
        Ls["Staff"].fixed({q: "W3"})
    lan = ip(add(hook[-1], (0, 2)))
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        FX.put([(lan[0] + dx, lan[1] + dy)], "X4" if (dx, dy) == (0, 0) else "X3")
    for dx, dy in ((-1, 0), (2, 1), (0, -1), (1, 2)):
        FX.put([(lan[0] + dx, lan[1] + dy)], "X1" if p.get("glow", 0) < 0.5 else "X2")
    # the arm (sleeve) holding it
    sh = F(2.4, -ln + 2)
    arm(ID, Ls["Arm"], sh, grip, 7.5, 7.0, 1.6, 1.3, "N", fist="J", fist_r=1.2, pref=(-1, 0.5))
    if p.get("smear"):
        g0, a0 = p["smear"]
        swept(FX, g0, a0, grip, ang, 12, 22, hw=0.8, pal="star")
    imgs = {n: K.render_layer(L) for n, L in Ls.items()}
    imgs["FX"] = FX.image()
    if p.get("dis", 0):
        imgs = K.ember_dissolve(imgs, p["dis"], ["Back", "Robe", "Staff", "Arm"], fx_name="FX", pal=("X4", "X3", "X2", "X1", "X0"))
    return imgs, {"tip": top, "lan": lan}


def pilgrim():
    base = dict(P=(22, 30), C=(23, 18), Hd=(24, 12), hand=(29, 26), sang=-78)
    A = []
    A.append(("idle", [(dict(base, C=(23, 18 + (i % 2) * 0.5), Hd=(24, 12 + (i % 2) * 0.6), hand=(29, 26 + (i % 2) * 0.5), sw=math.sin(i * 1.6)), 180) for i in range(4)]))
    A.append(("walk", [(dict(base, P=(22, 30 + abs(math.sin(i / 6 * math.pi)) * -0.8), hand=(29 + math.sin(i / 6 * 2 * math.pi) * 1.5, 26), sang=-78 + math.sin(i / 6 * 2 * math.pi) * 6, sw=math.sin(i / 6 * 2 * math.pi) * 2), 140) for i in range(6)]))
    atk = []
    keys = [dict(base), dict(base, C=(21, 18), Hd=(21.5, 12.5), hand=(24, 18), sang=-120), dict(base, C=(20, 18.5), Hd=(20.5, 13), hand=(22, 14), sang=-140, glow=1),
            dict(base, C=(20, 18.5), Hd=(20.5, 13), hand=(22, 14), sang=-145, glow=1), dict(base, C=(26, 20), Hd=(28, 14.5), hand=(34, 26), sang=10),
            dict(base, C=(26, 20.5), Hd=(28, 15), hand=(34, 30), sang=38), dict(base, C=(25, 20), Hd=(27, 14), hand=(32, 28), sang=20), dict(base, C=(24, 19), Hd=(25, 13), hand=(30, 27), sang=-30), dict(base)]
    ms = [100, 110, 130, 180, 60, 80, 120, 120, 120]
    for i, k in enumerate(keys):
        if i in (4, 5):
            k = dict(k, smear=(keys[i - 1]["hand"], keys[i - 1]["sang"]))
        atk.append((k, ms[i]))
    A.append(("attack", atk))
    A.append(("hurt", [(dict(base, C=(20, 19), Hd=(19.5, 13.5), hand=(26, 28), sang=-60), 100), (dict(base, C=(21, 18.5), Hd=(21, 13)), 120)]))
    A.append(("death", [(dict(base, C=(20, 19), Hd=(19.5, 13.5), dis=0.1 + i * 0.17, hand=(26, 30), sang=-40), 110) for i in range(6)]))
    return A


# ======================================================================== golem
def golem_frame(p, fi):
    K.setup(64, 64)
    Ls = {n: Layer(n) for n in ("BackArm", "Legs", "Body", "FrontArm")}
    FX = FXLayer("FX")
    FL = 63
    P, C = p["P"], p["C"]
    # legs: two tapering shards
    for nm, hip, ft, b in (("Legs", add(P, (-4, 0)), (P[0] - 7 + p.get("step", 0), FL), -1), ("Legs", add(P, (4, 0)), (P[0] + 6 - p.get("step", 0), FL), 0)):
        m = ID.plate(Ls[nm], [add(hip, (-3.5, -1)), add(hip, (3.5, -1)), (ft[0] + 3.5, ft[1] - 3), (ft[0] + 4.5, ft[1] + 0.5), (ft[0] - 3.5, ft[1] + 0.5), (ft[0] - 2.5, ft[1] - 4)],
                     "Z", bevel=1.4, tilt=(-0.4, -0.1), bias=b)
    # torso: an angular slab of glass, broad at the shoulders, a star at its heart
    torso = [add(P, (-4, 1)), add(P, (4, 1)), add(C, (8, 2)), add(C, (11, -5)), add(C, (2, -9)), add(C, (-8, -7)), add(C, (-9, 0))]
    tm = ID.plate(Ls["Body"], torso, "Z", bevel=2.2, tilt=(0.25, 0.15), strength=1.2, bias=-1)
    for sp, tipd in ((add(C, (-6, -6)), (-5, -9)), (add(C, (6, -7)), (3, -11))):          # crystal spurs on the shoulders
        ID.plate(Ls["Body"], [add(sp, (-2.2, 1)), add(sp, (2.2, 1)), add(sp, tipd)], "Z", bevel=0.8, tilt=(-0.5, -0.2))
    for a, b in ((add(C, (-4, -6)), add(P, (-2, -1))), (add(C, (5, -4)), add(C, (1, 6))), (add(C, (-8, 0)), add(C, (-2, 3)))):
        ID.dline(Ls["Body"], a, b, ("Z", 5))
    core = ip(add(C, (0, 3)))
    k = p.get("core", 0.5)
    for q in mask_disc(core, 2.6):
        Ls["Body"].fixed({q: "X2"})
    for q in mask_disc(core, 1.5):
        Ls["Body"].fixed({q: "X4" if k > 0.5 else "X3"})
    for i in range(6):                                   # light leaking through the cracks
        a = i / 6 * 2 * math.pi
        for r in range(3, 3 + int(2 + k * 3)):
            q = ip((core[0] + math.cos(a) * r, core[1] + math.sin(a) * r))
            if q in tm:
                Ls["Body"].decal([q], "X1" if r > 4 else "X2")
    # head: a small shard with two slit eyes
    hd = add(C, (2, -11))
    ID.plate(Ls["Body"], [add(hd, (-3, 3)), add(hd, (-2, -3)), add(hd, (3, -4)), add(hd, (4, 2))], "Z", bevel=1.2, tilt=(-0.3, -0.3))
    Ls["Body"].fixed({ip(add(hd, (2, -1))): "X3", ip(add(hd, (3, -1))): "X4"})
    # arms: long shard limbs ending in heavy glass fists
    for nm, sh, hand, b in (("BackArm", add(C, (-7, -3)), p["hb"], -1), ("FrontArm", add(C, (7, -3)), p["hf"], 0)):
        arm(ID, Ls[nm], sh, hand, 11, 11, 3.0, 2.6, "Z", bias=b, fist="Z", fist_r=3.6, pref=(-1, 0.5))
        ID.dome(Ls[nm], add(sh, (0, -1)), 4.0, 3.4, "Z", bias=b)
        ID.decal(Ls[nm], [add(hand, (0.5, -1))], ("X", 2))
    imgs = {n: K.render_layer(L) for n, L in Ls.items()}
    imgs["FX"] = FX.image()
    if p.get("shatter", 0):
        imgs = K.ember_dissolve(imgs, p["shatter"], ["BackArm", "Legs", "Body", "FrontArm"], fx_name="FX", seed=2, rise=10, pal=("X4", "X3", "Z5", "Z4", "X1"))
    return imgs, {}


def golem():
    base = dict(P=(32, 40), C=(33, 28), hf=(42, 42), hb=(24, 42))
    A = []
    A.append(("idle", [(dict(base, C=(33, 28 + (i % 2) * 0.6), core=0.4 + 0.3 * (i % 2)), 200) for i in range(4)]))
    A.append(("walk", [(dict(base, P=(32, 40 - abs(math.sin(i / 6 * math.pi)) * 1.2), step=math.sin(i / 6 * 2 * math.pi) * 3, hf=(42 + math.sin(i / 6 * 2 * math.pi) * 2, 42), hb=(24 - math.sin(i / 6 * 2 * math.pi) * 2, 42)), 150) for i in range(6)]))
    up = dict(base, C=(31, 27), hf=(36, 10), hb=(30, 10), core=0.8)
    sm = []
    for i, (k, ms) in enumerate([(base, 100), (dict(base, C=(32, 27.5), hf=(40, 30), hb=(28, 30)), 100), (dict(base, C=(31, 27), hf=(38, 18), hb=(30, 18)), 110), (up, 140), (dict(up, core=1), 160),
                                  (dict(base, C=(34, 29), hf=(44, 34), hb=(38, 34), core=1), 50), (dict(base, C=(36, 31), P=(33, 41), hf=(50, 58), hb=(44, 58), core=1), 60),
                                  (dict(base, C=(36, 31), P=(33, 41), hf=(50, 59), hb=(44, 59)), 110), (dict(base, C=(35, 30), hf=(47, 52), hb=(40, 50)), 160), (base, 140)]):
        sm.append((k, ms))
    A.append(("smash", sm))
    A.append(("hurt", [(dict(base, C=(31, 28.5), hf=(38, 44), hb=(22, 40)), 100), (base, 120)]))
    A.append(("death", [(dict(base, C=(32, 29 + i), hf=(40, 46 + i), hb=(24, 46), shatter=0.12 * i, core=max(0, 1 - i * 0.2)), 100) for i in range(8)]))
    return A


# ======================================================================== wisp
def wisp_frame(p, fi):
    K.setup(40, 32)
    FX = FXLayer("Body")
    cx, cy = p["c"]
    L = p["tail"]
    for i in range(int(L * 3)):                               # the tail, streaming back and thinning
        t = i / (L * 3)
        x = cx - 2 - t * L
        y = cy + math.sin(t * 5 + fi * 1.4) * 2.2 * t
        w = 3.6 * (1 - t) ** 0.8
        for v in range(-int(w), int(w) + 1):
            if hash01(i, v, fi) < 0.85 - t * 0.4:
                c = "X4" if abs(v) < w * 0.3 and t < 0.25 else "X3" if abs(v) < w * 0.6 and t < 0.5 else "X2" if t < 0.75 else "X1"
                FX.put([ip((x, y + v))], c)
    for q in mask_disc((cx, cy), 4.6):                        # the head: a hot little star with a hollow face
        d = math.hypot(q[0] + 0.5 - cx, q[1] + 0.5 - cy)
        FX.put([q], "X4" if d < 2.4 else "X3" if d < 3.6 else "X2")
    for dx in (1, 3):
        FX.put([ip((cx + dx, cy - 1))], "X0")
    FX.put([ip((cx + 2, cy + 2))], "X1")
    if p.get("dis"):
        FX.px = {q: c for q, c in FX.px.items() if hash01(q[0], q[1], 7) > p["dis"]}
    return {"Body": FX.image()}, {}


def wisp():
    A = []
    A.append(("fly", [(dict(c=(24, 16 + math.sin(i / 6 * 2 * math.pi) * 1.5), tail=14 + math.sin(i) * 2), 100) for i in range(6)]))
    A.append(("dive", [(dict(c=(22, 16), tail=10), 100), (dict(c=(20, 16), tail=8), 120), (dict(c=(28, 16), tail=20), 60), (dict(c=(30, 16), tail=22), 60),
                       (dict(c=(30, 16), tail=22), 60), (dict(c=(26, 16), tail=16), 100)]))
    A.append(("hurt", [(dict(c=(22, 15), tail=8), 100), (dict(c=(23, 16), tail=10), 100)]))
    A.append(("death", [(dict(c=(24, 16), tail=12 - i * 2, dis=0.15 * i + 0.1), 90) for i in range(6)]))
    return A


def export_simple(name, w, h, drawfn, anims, meta, layers):
    K.setup(w, h)
    out = []
    for tag, frs in anims:
        seq = []
        for fi, (p, ms) in enumerate(frs):
            imgs, _ = drawfn(p, fi)
            seq.append((ms, imgs))
        out.append((tag, seq))
    K.setup(w, h)
    K.export(name, layers, out, meta, build=BUILD, flat_order=layers)
    print(name, "built" if BUILD else "previewed")


def main():
    export_simple("sf_pilgrim", 48, 48, pilgrim_frame, pilgrim(),
                  {"native": 1, "anchor": [22, 48], "hurtbox": [16, 10, 14, 38], "attacks": {"attack": {"active": [4, 5], "hit": [22, 6, 24, 42]}},
                   "telegraph": {"attack": {"frame": 3, "at": [18, 2]}}}, ["Back", "Robe", "Staff", "Arm", "FX"])
    export_simple("sf_golem", 64, 64, golem_frame, golem(),
                  {"native": 1, "anchor": [32, 64], "hurtbox": [20, 14, 26, 50], "attacks": {"smash": {"active": [6, 7], "hit": [34, 30, 26, 34]}},
                   "telegraph": {"smash": {"frame": 4, "at": [33, 8]}}}, ["BackArm", "Legs", "Body", "FrontArm", "FX"])
    export_simple("sf_wisp", 40, 32, wisp_frame, wisp(),
                  {"native": 1, "anchor": [24, 16], "hurtbox": [18, 10, 12, 12], "attacks": {"dive": {"active": [2, 4], "hit": [18, 8, 16, 16]}}}, ["Body"])


if __name__ == "__main__":
    main()
