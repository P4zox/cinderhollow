#!/usr/bin/env python3
"""NEO-HALLOW enemies (agent NH) -- ART_SPEC section 4 contract, method from enemy_kit.py.

    python3 art/gen_neo_enemies.py [--preview] [--only nh_drone,...]

nh_drone   40x32  security drone: chrome teardrop hull, one sensor eye (cyan / red on alert), twin thruster pods,
                  an antenna fin.  fly(4) alert(2) fire(4) hurt(2) death(6)   (floats: anchor = body centre)
nh_cyborg  56x48  chrome hollow: a gaunt cyborg husk, skull helm with a magenta visor slit, forearm blades with
                  cyan edges.  idle(4) walk(6) slash(9, active 4-5) dash(10, active 4-6) hurt(2) death(7)
nh_turret  32x32  turret node: armoured dome on a floor mount; the engine draws the barrel from the pivot (16,17).
                  closed(1) deploy(4) idle(2) hurt(2) death(6)
"""
import math, sys
import neo_kit  # noqa: F401  (palette)
from neo_kit import K, E3, Layer, FXLayer, Rig, lerp, ip, line, poly_mask, n_plate, n_dome, n_capsule, n_tube, mk, madd, disc_glow, halo_dots, dirv, spawn_pt, circuit, glow_line
from enemy_kit import hash01, mask_disc, ik

BUILD = "--preview" not in sys.argv
E3.BUILD = BUILD
E3.SPEC_FRAMES.update({
    "nh_drone": dict(fly=4, alert=2, fire=4, hurt=2, death=6),
    "nh_cyborg": dict(idle=4, walk=6, slash=9, dash=10, hurt=2, death=7),
    "nh_turret": dict(closed=1, deploy=4, idle=2, hurt=2, death=6),
})


# =========================================================================== DRONE
DR_L = ["Pods", "Hull", "FX"]
D_NEU = dict(C=(20.0, 15.0), tilt=0.0, eye="X", eyeglow=1.0, thr=1.0, fi=0, dead=0.0, charge=0.0, alert=False)
DP = mk(D_NEU)


def draw_drone(p, fi, sw):
    Ls = {"Pods": Layer("Pods"), "Hull": Layer("Hull")}
    FX = FXLayer("FX"); Ls["FX"] = FX
    R = Rig(p["tilt"], p["C"])
    c = p["C"]
    info = {"hit": set()}
    # thruster pods (angled under the hull)
    for sx, b in ((-8.0, -1), (8.0, 0)):
        a, bb = (c[0] + sx, c[1] + 3.0), (c[0] + sx * 1.15, c[1] + 7.0)
        R.cap(Ls["Pods"], a, bb, 2.2, 1.8, "U", b)
        R.dome(Ls["Pods"], bb, 2.0, 1.4, "S", b)
        if p["thr"] > 0 and not p["dead"]:
            tip = ip(R.T((bb[0], bb[1] + 2.0)))
            for k in range(int(1 + p["thr"] * 3)):
                FX.put([(tip[0], tip[1] + k)], ["X4", "X3", "X2", "X1"][min(3, k)])
            if (fi + int(sx)) % 2 == 0: FX.put([(tip[0] - 1, tip[1] + 1), (tip[0] + 1, tip[1] + 1)], "X1")
    H = Ls["Hull"]
    # teardrop hull: gunmetal belly, chrome dorsal shell, fin
    R.plate(H, [(c[0] - 11, c[1] + 1), (c[0] - 6, c[1] - 4), (c[0] + 4, c[1] - 5), (c[0] + 10, c[1] - 1), (c[0] + 9, c[1] + 3), (c[0] + 2, c[1] + 5), (c[0] - 7, c[1] + 4)], "U", bevel=2.0, tilt=(0, 0.1))
    R.plate(H, [(c[0] - 9, c[1] - 1), (c[0] - 4, c[1] - 6), (c[0] + 5, c[1] - 6.5), (c[0] + 9, c[1] - 2), (c[0] + 2, c[1] - 1.5)], "S", bevel=1.6, tilt=(-0.2, -0.4), ao=0)
    R.plate(H, [(c[0] - 6, c[1] - 5), (c[0] - 11, c[1] - 10), (c[0] - 9, c[1] - 10), (c[0] - 2, c[1] - 6)], "S", bevel=0.8, tilt=(-0.3, -0.5), ao=0)
    circuit(H, [R.T((c[0] - 8, c[1] + 1)), R.T((c[0] - 2, c[1] + 1)), R.T((c[0] + 1, c[1] + 3))], "X1")
    # the sensor eye
    e = R.T((c[0] + 7.0, c[1] + 0.5))
    lens = {ip(e): p["eye"] + "3", (ip(e)[0] - 1, ip(e)[1]): p["eye"] + "2", (ip(e)[0], ip(e)[1] + 1): p["eye"] + "1", (ip(e)[0] + 1, ip(e)[1]): p["eye"] + "3"}
    H.fixed(lens)
    if p["eyeglow"] > 0.5 and not p["dead"]:
        FX.put([ip(e)], p["eye"] + ("3" if p["eye"] == "R" else "4"))
    if p["charge"] > 0:
        disc_glow(FX, (e[0] + 1.5, e[1]), 1.0 + p["charge"] * 2.4, ["X4", "X3", "X2", "X1"])
    if p["dead"]:
        for k in range(int(p["dead"] * 10)):
            q = (int(c[0] + (hash01(k, fi, 3) - 0.5) * 22), int(c[1] + (hash01(fi, k, 4) - 0.5) * 14))
            FX.put([q], ["X3", "T3", "S6", "X2"][k % 4])
        for q in list(H.px)[:: max(1, int(6 - p["dead"] * 5))]:
            if hash01(q[0], q[1], fi) < p["dead"] * 0.6: H.erase([q])
    info["spawn"] = (e[0] + 2, e[1])
    return Ls, info


def d_fly():
    return [(110, DP(C=(20.0, 15.0 + [0, -0.6, -1, -0.4][k]), thr=1 + (k % 2) * 0.5)) for k in range(4)]


def d_alert():
    return [(120, DP(eye="R", eyeglow=1, tilt=-4)), (120, DP(eye="R", eyeglow=0, tilt=-4, C=(20.0, 14.0)))]


def d_fire():
    return [(110, DP(charge=0.4, tilt=-3)), (110, DP(charge=0.9, tilt=-5)), (90, DP(charge=1.2, tilt=-5, C=(19.0, 15.0))), (140, DP(tilt=4, C=(18.0, 15.0), thr=2))]


def d_hurt():
    return [(80, DP(tilt=14, C=(19.0, 15.0), eyeglow=0)), (110, DP(tilt=7, eyeglow=1))]


def d_death():
    return [(90, DP(tilt=18 + k * 10, C=(20.0, 15.0 + k * 1.6), eye="R", eyeglow=k % 2, thr=max(0, 1 - k), dead=min(1, k / 5))) for k in range(6)]


def build_drone():
    K.setup(40, 32)
    anims, infos = E3.render_anims("nh_drone", DR_L, draw_drone, [("fly", d_fly), ("alert", d_alert), ("fire", d_fire), ("hurt", d_hurt), ("death", d_death)], loops=("fly",))
    meta = {"native": 1, "anchor": [20, 16], "hurtbox": [9, 8, 22, 14],
            "attacks": {}, "spawn": {"fire": {"frame": 2, "at": spawn_pt(infos["fire"][2]["spawn"])}}}
    E3.export("nh_drone", DR_L, anims, meta)


# =========================================================================== CYBORG
CY_L = ["FarArm", "FarLeg", "Body", "Head", "NearLeg", "NearArm", "FX"]
FL = 47.0
C_NEU = dict(P=(24.0, 28.0), C=(25.0, 16.0), Hd=(26.5, 9.0), nf=(28.0, FL), ff=(21.0, FL), nk=None, fk=None,
             nh=(31.0, 26.0), fh=(19.0, 26.0), na=60.0, fa=70.0, visor=1.0, smear=None, lean=0.0, dead=0.0, fi=0, spark=0, streak=False)
CP = mk(C_NEU)


def forearm_blade(L, FX, hand, el, extra_ang=0.0, ln=15.0, bias=0):
    """Long forearm blade: rides the ulna past the fist; chrome body, a cyan monomolecular edge."""
    d = (hand[0] - el[0], hand[1] - el[1]); m = math.hypot(*d) or 1
    d = (d[0] / m, d[1] / m)
    if extra_ang:
        a = math.atan2(d[1], d[0]) + math.radians(extra_ang); d = (math.cos(a), math.sin(a))
    pv = (-d[1], d[0])
    b0 = madd(hand, (d, -4.0), (pv, 1.2))
    tip = madd(hand, (d, ln))
    poly = [madd(b0, (pv, -1.0)), madd(b0, (pv, 1.4)), madd(tip, (pv, 0.2)), madd(tip, (d, 1.0))]
    m_ = poly_mask(poly)
    L.paint(n_plate(m_, 0.9, (-0.2, -0.4), 1.2), "S", bias, ao=0)
    edge = [q for q in line(madd(b0, (pv, -1.0)), madd(tip, (d, 0.6)))]
    L.decal([q for q in edge if q in L.px], "X3")
    return tip, d


def draw_cyborg(p, fi, sw):
    Ls = {n: Layer(n) for n in CY_L if n != "FX"}
    FX = FXLayer("FX"); Ls["FX"] = FX
    info = {"hit": set()}
    P_, C_, Hd = p["P"], p["C"], p["Hd"]
    up = (C_[0] - P_[0], C_[1] - P_[1])
    # ---- far arm + blade
    shF = madd(C_, (up, -0.12), ((1, 0), -2.5))
    fe = ik(shF, p["fh"], 7.0, 7.0, (-1, 0.6))
    Ls["FarArm"].paint(n_tube([shF, fe, p["fh"]], [1.8, 1.5, 1.4]), "U", -1)
    Ls["FarArm"].paint(n_capsule(fe, lerp(fe, p["fh"], 0.8), 1.7, 1.5), "S", -1, ao=0)
    ftip, _ = forearm_blade(Ls["FarArm"], FX, p["fh"], fe, 0, 13.0, -1)
    # ---- legs
    for name, foot, pref, b in (("FarLeg", p["ff"], (1, 0.1), -1), ("NearLeg", p["nf"], (1, -0.1), 0)):
        L = Ls[name]
        hip = madd(P_, ((1, 0), -1.5 if name == "FarLeg" else 1.5))
        ank = (foot[0], foot[1] - 1.5)
        kn = p["fk" if name == "FarLeg" else "nk"] or ik(hip, ank, 9.2, 9.2, pref)
        L.paint(n_tube([hip, kn, ank], [2.4, 1.8, 1.4]), "U", b)
        L.paint(n_capsule(lerp(kn, ank, 0.1), lerp(kn, ank, 0.75), 1.9, 1.5), "S", b, ao=0)   # chrome shin guard
        L.paint(n_dome(kn, 1.8, 1.6), "S", b, ao=0)
        sole = poly_mask([(ank[0] - 2, foot[1] + 1), (ank[0] - 2, foot[1] - 2), (ank[0] + 1, foot[1] - 2.5), (ank[0] + 4, foot[1] - 0.5), (ank[0] + 4, foot[1] + 1)])
        L.paint(n_plate(sole, 1.0, (0, -0.4)), "U", b)
    # ---- torso: gunmetal undersuit, chrome ribcage plate, spine cables, a magenta core
    B = Ls["Body"]
    B.paint(n_tube([P_, lerp(P_, C_, 0.5), C_], [3.0, 2.4, 3.6]), "U", 0)
    nrm = (-up[1] / (math.hypot(*up) or 1), up[0] / (math.hypot(*up) or 1))
    ch = [madd(C_, (nrm, -3.6), (up, 0.12)), madd(C_, (nrm, 3.4), (up, 0.1)), madd(C_, (nrm, 3.8), (up, -0.3)), madd(C_, (nrm, 1.0), (up, -0.55)), madd(C_, (nrm, -2.5), (up, -0.45))]
    B.paint(n_plate(poly_mask(ch), 1.4, (-0.3, -0.3), 1.2), "S", 0, ao=0)
    for k in range(3):
        rib = [madd(C_, (nrm, 1.2), (up, -0.12 - k * 0.1)), madd(C_, (nrm, 3.0), (up, -0.16 - k * 0.1))]
        B.decal(line(*rib), "S2")
    core = ip(madd(C_, (nrm, 1.6), (up, -0.05)))
    B.fixed({core: "T3", (core[0], core[1] + 1): "T2"})
    FX.put([core], "T4" if fi % 2 == 0 and not p["dead"] else "T3")
    # pelvis plate
    B.paint(n_plate(poly_mask([madd(P_, (nrm, -3.0), (up, 0.1)), madd(P_, (nrm, 3.2), (up, 0.1)), madd(P_, (nrm, 2.2), (up, -0.2)), madd(P_, (nrm, -2.4), (up, -0.2))]), 1.0, (0, -0.3)), "S", 0, ao=0)
    # ---- head: a narrow chrome skull-helm, magenta visor slit, cable queue
    Hh = Ls["Head"]
    neck0 = madd(C_, (up, 0.25))
    Hh.paint(n_capsule(neck0, Hd, 1.1, 1.0), "U", 0)
    Hh.paint(n_dome(Hd, 3.0, 3.6, 1.0, (-0.1, -0.1)), "S", 0)
    Hh.paint(n_plate(poly_mask([(Hd[0] - 1, Hd[1] + 1.5), (Hd[0] + 3.4, Hd[1] + 1.0), (Hd[0] + 3.0, Hd[1] + 3.6), (Hd[0] + 0.5, Hd[1] + 4.2)]), 0.8, (0.1, 0.2)), "S", -1, ao=0)   # jaw
    for k in range(4):
        Hh.paint(n_capsule((Hd[0] - 2.5 - k * 0.8, Hd[1] + k * 1.5), (Hd[0] - 3.8 - k * 0.8 + math.sin(fi + k) * 0.4, Hd[1] + 1.6 + k * 1.5), 0.6), "U", -1, ao=0)
    vis = [(ip((Hd[0] + x, Hd[1] - 0.2))) for x in (0.0, 1.0, 2.0, 3.0)]
    Hh.fixed({q: ("T3" if i else "T2") for i, q in enumerate(vis)})
    if p["visor"] > 0.5: FX.put(vis[1:], "T4")
    # ---- near arm + blade
    shN = madd(C_, (up, -0.1), ((1, 0), 2.2))
    ne = ik(shN, p["nh"], 7.0, 7.0, (-1, 0.6))
    A = Ls["NearArm"]
    A.paint(n_tube([shN, ne, p["nh"]], [2.0, 1.6, 1.5]), "U", 0)
    A.paint(n_dome(shN, 2.3, 2.0), "S", 0, ao=0)
    A.paint(n_capsule(ne, lerp(ne, p["nh"], 0.85), 1.8, 1.6), "S", 0, ao=0)
    ntip, nd = forearm_blade(A, FX, p["nh"], ne, 0, 15.0, 0)
    # ---- slash smear / dash streaks
    if p["smear"]:
        g0, a0, g1, a1 = p["smear"]
        info["hit"] |= K.swept(FX, g0, a0, g1, a1, 3.0, 18.0, hw=0.9, pal="cyan", start=0.1)
    info["hit"] |= {ip(ntip), ip(ftip)}
    if p["streak"]:
        for k, y in enumerate((18, 24, 30, 36)):
            for x in range(2, 14 - k * 2): FX.put([(x + k, y)], "X1" if x < 8 else "X2")
    if p["spark"]:
        for k in range(6):
            FX.put([(int(C_[0] + (hash01(k, fi, 1) - 0.5) * 12), int(C_[1] + (hash01(fi, k, 2) - 0.5) * 16))], ["X3", "T3", "S6"][k % 3])
    if p["dead"]:
        for L in Ls.values():
            if isinstance(L, Layer):
                for q in list(L.px):
                    if hash01(q[0], q[1], 7) < p["dead"] * 0.5: L.erase([q])
    info["tip"] = ntip
    return Ls, info


def c_idle():
    out = []
    for k in range(4):
        b = [0, 0.5, 1, 0.5][k]
        out.append((180, CP(C=(25.0, 16.0 + b), Hd=(26.5, 9.0 + b), P=(24.0, 28.0 + b * 0.5), nh=(31.0, 26.0 + b), fh=(19.5, 26.5 + b))))
    return out


def c_walk():
    out = []
    for k in range(6):
        t = k / 6 * 2 * math.pi
        nf = (24.0 + math.sin(t) * 5, FL - max(0, math.cos(t)) * 2.5)
        ff = (24.0 - math.sin(t) * 5, FL - max(0, -math.cos(t)) * 2.5)
        b = abs(math.sin(t)) * 1.0
        out.append((110, CP(nf=nf, ff=ff, C=(25.5, 16.0 + b), Hd=(27.0, 9.0 + b), P=(24.0, 28.0 + b * 0.6), nh=(30.0 - math.sin(t) * 3, 26.0 + b), fh=(20.0 + math.sin(t) * 3, 26.5 + b))))
    return out


def c_slash():
    # wind the near blade back over the shoulder, hold, carve down through the front, recover
    kf = [
        (120, dict(nh=(28.0, 20.0), C=(24.5, 16.5), Hd=(25.5, 9.5))),
        (120, dict(nh=(21.0, 14.0), C=(23.5, 16.5), Hd=(24.5, 10.0), fh=(27.0, 24.0))),
        (120, dict(nh=(18.0, 13.5), C=(23.0, 17.0), Hd=(24.0, 10.5), fh=(28.0, 23.0))),
        (200, dict(nh=(17.5, 13.0), C=(23.0, 17.0), Hd=(24.0, 10.5), fh=(28.0, 23.0), visor=1)),
        (60, dict(nh=(36.0, 20.0), C=(27.0, 17.0), Hd=(29.0, 10.5), P=(25.0, 28.5), nf=(31.0, FL), fh=(21.0, 27.0), smear=((20.0, 10.0), -90, (36.0, 20.0), 20))),
        (80, dict(nh=(37.0, 30.0), C=(27.5, 18.0), Hd=(29.5, 11.5), P=(25.5, 29.0), nf=(32.0, FL), fh=(20.0, 28.0), smear=((30.0, 14.0), -30, (37.0, 30.0), 60))),
        (140, dict(nh=(34.0, 32.0), C=(27.0, 18.0), Hd=(29.0, 11.5), P=(25.5, 29.0), nf=(32.0, FL), fh=(20.0, 28.0))),
        (140, dict(nh=(32.0, 28.0), C=(26.0, 17.0), Hd=(27.5, 10.0), nf=(30.0, FL))),
        (120, dict(nh=(31.0, 26.0))),
    ]
    return [(ms, CP(**d)) for ms, d in kf]


def c_dash():
    kf = [
        (110, dict(C=(23.0, 18.0), Hd=(24.5, 11.5), P=(23.0, 30.0), nh=(20.0, 26.0), fh=(16.0, 27.0), nf=(29.0, FL), ff=(18.0, FL))),
        (110, dict(C=(22.0, 20.0), Hd=(24.0, 13.5), P=(22.0, 31.0), nh=(16.0, 25.0), fh=(13.0, 26.0), nf=(30.0, FL), ff=(16.0, FL))),
        (110, dict(C=(22.0, 21.0), Hd=(24.0, 14.5), P=(22.0, 32.0), nh=(15.0, 24.0), fh=(12.0, 25.0), nf=(30.0, FL), ff=(15.0, FL))),
        (180, dict(C=(22.0, 21.0), Hd=(24.0, 14.5), P=(22.0, 32.0), nh=(15.0, 23.5), fh=(12.0, 24.5), nf=(30.0, FL), ff=(15.0, FL), visor=1)),
        (70, dict(C=(31.0, 20.0), Hd=(35.0, 15.0), P=(24.0, 29.0), nh=(40.0, 22.0), fh=(38.0, 25.0), nf=(33.0, FL), ff=(13.0, FL - 1), streak=True)),
        (70, dict(C=(32.0, 20.0), Hd=(36.0, 15.0), P=(25.0, 29.0), nh=(42.0, 21.0), fh=(39.0, 24.0), nf=(34.0, FL), ff=(15.0, FL - 2), streak=True)),
        (80, dict(C=(31.0, 19.0), Hd=(35.0, 14.0), P=(25.0, 29.0), nh=(41.0, 24.0), fh=(37.0, 26.0), nf=(34.0, FL), ff=(18.0, FL), streak=True)),
        (140, dict(C=(28.0, 18.0), Hd=(31.0, 12.0), P=(25.0, 29.0), nh=(36.0, 28.0), fh=(30.0, 28.0), nf=(32.0, FL), ff=(20.0, FL))),
        (140, dict(C=(26.0, 17.0), Hd=(28.0, 10.0), P=(24.5, 28.5), nh=(33.0, 27.0), fh=(22.0, 27.0), nf=(30.0, FL), ff=(21.0, FL))),
        (120, dict()),
    ]
    return [(ms, CP(**d)) for ms, d in kf]


def c_hurt():
    return [(90, CP(C=(22.0, 17.0), Hd=(22.5, 10.5), P=(23.5, 28.5), nh=(27.0, 23.0), fh=(16.0, 24.0), spark=1, visor=0)),
            (130, CP(C=(23.0, 16.5), Hd=(24.0, 10.0), nh=(29.0, 25.0), fh=(18.0, 26.0)))]


def c_death():
    out = []
    for k in range(7):
        t = k / 6
        yb = t * 16
        out.append((110 if k < 6 else 400, CP(C=(24.0 - t * 4, 16.0 + yb), Hd=(24.0 - t * 7, 9.5 + yb * 1.15), P=(24.0 - t * 2, 28.0 + yb * 0.55),
                                          nf=(28.0, FL), ff=(20.0, FL), nk=(29.0 + t * 3, 37.0 + t * 7), fk=(21.0 - t * 2, 37.0 + t * 7),
                                          nh=(31.0 - t * 2, 26.0 + t * 18), fh=(18.0 - t * 4, 27.0 + t * 17), visor=0 if k > 1 else 1, spark=1 if k < 4 else 0,
                                          dead=max(0, (t - 0.5) * 1.2))))
    return out


def build_cyborg():
    K.setup(56, 48)
    anims, infos = E3.render_anims("nh_cyborg", CY_L, draw_cyborg, [("idle", c_idle), ("walk", c_walk), ("slash", c_slash), ("dash", c_dash), ("hurt", c_hurt), ("death", c_death)])
    slash = E3.hit_rect(infos, "slash", (4, 5), floor=True, x_min=26)
    dash = E3.hit_rect(infos, "dash", (4, 5, 6), floor=True, x_min=30)
    meta = {"native": 1, "anchor": [24, 48], "hurtbox": [18, 6, 13, 42],
            "attacks": {"slash": {"active": [4, 5], "hit": slash}, "dash": {"active": [4, 6], "hit": dash}},
            "telegraph": {"slash": {"frame": 3, "at": [19, 8]}, "dash": {"frame": 3, "at": [16, 23]}}}
    E3.export("nh_cyborg", CY_L, anims, meta)


# =========================================================================== TURRET
TU_L = ["Mount", "Head", "FX"]
T_NEU = dict(rise=1.0, open=1.0, eye=1.0, dead=0.0, tilt=0.0, spark=0)
TP = mk(T_NEU)


def draw_turret(p, fi, sw):
    Ls = {"Mount": Layer("Mount"), "Head": Layer("Head")}
    FX = FXLayer("FX"); Ls["FX"] = FX
    M, Hh = Ls["Mount"], Ls["Head"]
    # floor mount: a low armoured plinth with vents
    M.paint(n_plate(poly_mask([(5, 32), (7, 26), (25, 26), (27, 32)]), 1.5, (-0.1, -0.5)), "U", 0)
    M.paint(n_plate(poly_mask([(9, 27), (11, 23), (21, 23), (23, 27)]), 1.2, (-0.1, -0.5)), "S", -1, ao=0)
    for x in range(10, 23, 3): M.decal([(x, 29), (x, 30)], "U1")
    M.fixed({(15, 28): "X2" if p["eye"] > 0.5 else "U3", (16, 28): "X3" if p["eye"] > 0.5 else "U3"})
    # the head: a sphere that rises out of the mount; armour petals open around it
    cy = 17 + (1 - p["rise"]) * 7
    c = (16.0, cy)
    R = Rig(p["tilt"], (16, 24))
    R.dome(Hh, c, 5.2, 5.0, mat="U", bias=0)
    for side in (-1, 1):   # armour petals
        o = p["open"]
        pts = [(16 + side * (2 + o * 2.6), cy - 5.5), (16 + side * (5.5 + o * 1.6), cy - 2), (16 + side * (5.8 + o * 1.8), cy + 3), (16 + side * (3.5 + o * 1.0), cy + 5)]
        R.plate(Hh, pts, "S", bevel=1.1, tilt=(-0.3 * side, -0.3), ao=0)
    ey = ip(R.T((16.0, cy)))
    if p["eye"] > 0.3:
        Hh.fixed({ey: "R3", (ey[0] + 1, ey[1]): "R2", (ey[0] - 1, ey[1]): "R2"})
        if p["eye"] > 0.8: FX.put([ey], "R3")
    else:
        Hh.fixed({ey: "U4"})
    if p["spark"]:
        for k in range(5): FX.put([(int(8 + hash01(k, fi, 1) * 16), int(12 + hash01(fi, k, 2) * 14))], ["X3", "T3", "S6"][k % 3])
    if p["dead"]:
        for L in (M, Hh):
            for q in list(L.px):
                if hash01(q[0], q[1], 5) < p["dead"] * 0.55 and q[1] < 30: L.erase([q])
    return Ls, {"hit": set()}


def build_turret():
    K.setup(32, 32)
    anims, infos = E3.render_anims("nh_turret", TU_L, draw_turret, [
        ("closed", lambda: [(200, TP(rise=0, open=0, eye=0))]),
        ("deploy", lambda: [(90, TP(rise=0.2, open=0, eye=0)), (90, TP(rise=0.55, open=0.3, eye=0.4)), (90, TP(rise=0.9, open=0.7, eye=0.9)), (120, TP(rise=1, open=1, eye=1))]),
        ("idle", lambda: [(260, TP()), (260, TP(eye=0.6))]),
        ("hurt", lambda: [(80, TP(tilt=-10, spark=1, eye=0)), (120, TP(tilt=-4))]),
        ("death", lambda: [(100, TP(tilt=-12 - k * 6, rise=1 - k * 0.15, open=1 + k * 0.2, eye=0, spark=1, dead=k / 6)) for k in range(6)]),
    ], sway_key="rise", loops=("idle",))
    meta = {"native": 1, "anchor": [16, 32], "hurtbox": [7, 11, 18, 21], "attacks": {}, "pivot": [16, 17]}
    E3.export("nh_turret", TU_L, anims, meta)


def main():
    only = None
    if "--only" in sys.argv: only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    for name, fn in (("nh_drone", build_drone), ("nh_cyborg", build_cyborg), ("nh_turret", build_turret)):
        if only is None or name in only: fn()


if __name__ == "__main__":
    main()
