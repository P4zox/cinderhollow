"""cm_servant -- a gaunt pale vampire manservant of the Crimson Manor (64x48, anchor [28, 48], ~34px, hunched).

Black tailcoat livery, crimson waistcoat, white gloves and collar, slicked black hair, glowing red eyes, a long
carving knife in each hand.  Faces RIGHT, feet on the bottom row.  Built by gen_crimson_enemies.py.

Tags: idle(4 loop) walk(6 loop) slash(9: crouch windup, two quick slashes, windows [4,4] [6,6])
      lunge(10: coils then leaps knife-first, active [5,6], drawn in place) emerge(6: drops out of a portrait above,
      lands in a crouch, rises) hurt(2) death(6: collapses into ash and blood)
"""
import math

import crimson_kit as CK
import enemy_kit as K
from enemy_kit import (Layer, FXLayer, ID, basis, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,
                       poly_mask, n_plate, n_dome, n_capsule, blade_px, swept, dirv)

W, H = 64, 48
FLOOR = H - 1
AX = 28
LAYERS = ["FXBack", "Tails", "KnifeBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "KnifeFront", "FrontArm",
          "FX"]
FXL = {"FXBack", "FX"}
BODY = [n for n in LAYERS if n not in FXL]
THIGH, SHIN = 8.2, 8.2
UARM, FARM = 6.6, 6.4
TORSO, NECK = 10.07, 6.1
KNIFE = dict(pommel=-2.6, grip_end=0.3, grip="q2", grip_w=0.6, pommel_c="s3", guard=(0.3, 0.9, 1.3), guard_c="s3",
             guard_hi="s4", b0=0.9, end=12.0, w_edge=1.05, w_spine=0.55, taper=0.45, fuller=None, edge_hi="w5",
             edge="s5", spine="s3")

NEU = dict(P=(26.5, 31.5), C=(30.8, 22.4), Hd=(35.2, 18.2), hup=(0.18, -1), fb=(22.0, FLOOR), ff=(31.5, FLOOR),
           kb=None, kf=None, hf=(38.5, 30.5), af=20, hb=(35.0, 32.5), ab=35, eye=1, smearF=None, smearB=None,
           flare=0.0, dust=0, wind=0.0, jaw=0, glint=None)
PTS = ("P", "C", "Hd", "fb", "ff", "kb", "kf", "hf", "hb")


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def up(p, dy, dx=0.0):
    q = dict(p)
    for k in PTS:
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] - dy)
    return q


def leg(L, hip, foot, kn, bias):
    fx, fy = foot
    ank = (fx, fy - 1.3)
    ank = CK.clamp_reach(hip, ank, THIGH + SHIN - 0.05)
    if kn is not None:                      # a knee key is only a bend hint: segment lengths stay exact
        m = lerp(hip, ank, 0.5)
        kn = ik(hip, ank, THIGH, SHIN, (kn[0] - m[0], kn[1] - m[1]))
    else:
        kn = ik(hip, ank, THIGH, SHIN, (1, -0.2))
    L.paint(n_capsule(hip, kn, 1.7, 1.4), "k", bias)
    L.paint(n_capsule(kn, ank, 1.4, 1.1), "k", bias)
    sole = [(fx - 1.6, fy + 1), (fx - 1.6, fy - 1.8), (fx + 0.6, fy - 2.0), (fx + 3.4, fy - 0.6), (fx + 3.4, fy + 1)]
    L.paint(n_plate(poly_mask(sole), 0.9, (0, -0.35), 1.1), "q", bias, ao=0)
    return kn


def arm(L, sh, hand, bias, pref=(0.35, 1.0)):
    el = ik(sh, hand, UARM, FARM, pref)
    L.paint(n_capsule(sh, el, 1.45, 1.25), "k", bias)
    L.paint(n_capsule(el, hand, 1.25, 1.05), "k", bias)
    L.paint(n_capsule(lerp(el, hand, 0.78), lerp(el, hand, 0.92), 1.3, 1.25), "w", bias, ao=0)
    L.paint(n_dome(hand, 1.25, 1.15), "w", bias)
    return el


def draw(p, fi, sw, phase=1):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    p = CK.normalize_spine(p, TORSO, NECK)
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    G = basis(Hd, p["hup"])
    shF, shB = F(-1.3, -ln + 2.2), F(-1.9, -ln + 2.3)
    hF, hB = F(0.9, 0.6), F(-1.0, 0.6)
    p["hf"] = CK.clamp_reach(shF, p["hf"], UARM + FARM - 0.05)
    p["hb"] = CK.clamp_reach(shB, p["hb"], UARM + FARM - 0.05)
    p["ff"] = CK.clamp_reach((hF[0], hF[1] - 1.3), p["ff"], THIGH + SHIN - 0.05) if p["kf"] is None else p["ff"]
    p["fb"] = CK.clamp_reach((hB[0], hB[1] - 1.3), p["fb"], THIGH + SHIN - 0.05) if p["kb"] is None else p["fb"]
    info = {"hit": set(), "hitF": set(), "hitB": set()}

    # ---------------- knives
    for key, grip, ang, lay in (("B", p["hb"], p["ab"], "KnifeBack"), ("F", p["hf"], p["af"], "KnifeFront")):
        pix, bl, tip = blade_px(ID, grip, ang, KNIFE)
        pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
        Ls[lay].fixed(pix)
        info["hit" + key] |= {q for q in bl if q[1] <= FLOOR}
        info["tip" + key] = tip

    # ---------------- coat tails (flare up when falling / leaping)
    Tl = Ls["Tails"]
    fl = p["flare"]
    root = F(-1.6, -1.2)
    dn = (-upv[0] / ln, -upv[1] / ln)
    back = (dn[1], -dn[0])                                    # perpendicular, towards the back
    if back[0] > 0:
        back = (-back[0], -back[1])
    tail_dir = lerp((-0.42, 1.0), (-0.55, -0.9), fl)
    tl = math.hypot(*tail_dir)
    tail_dir = (tail_dir[0] / tl, tail_dir[1] / tl)
    side = (-tail_dir[1], tail_dir[0])
    if side[0] < 0:
        side = (-side[0], -side[1])
    Lt = 10.5 - fl * 1.5
    sx = sw * 0.3
    t0 = add(root, (side[0] * 1.2, side[1] * 1.2))
    t1 = add(root, (-side[0] * 1.4, -side[1] * 1.4))
    tip1 = add(root, (tail_dir[0] * Lt - side[0] * 2.2 + sx, tail_dir[1] * Lt - side[1] * 2.2))
    notch = add(root, (tail_dir[0] * (Lt - 3.0) + sx * 0.8, tail_dir[1] * (Lt - 3.0)))
    tip2 = add(root, (tail_dir[0] * (Lt - 0.8) + side[0] * 1.0 + sx, tail_dir[1] * (Lt - 0.8) + side[1] * 1.0))
    tm = poly_mask([t1, t0, tip2, notch, tip1])
    Tl.paint(n_plate(tm, 1.2, (0.1, -0.1), 1.0), "k", -1, ao=0)
    Tl.decal([q for q in line(root, notch) if q in tm], ("k", 1))

    # ---------------- back arm + legs
    arm(Ls["BackArm"], shB, p["hb"], -1, pref=p.get("prefB", (0.3, -1.0)))
    info["kb"] = leg(Ls["BackLeg"], hB, p["fb"], p["kb"], -1)
    info["kf"] = leg(Ls["FrontLeg"], hF, p["ff"], p["kf"], 0)

    # ---------------- torso: black coat, crimson waistcoat at the front, white collar
    Bd = Ls["Body"]
    Bd.paint(n_plate(poly_mask([F(-2.2, -1.6), F(2.2, -1.6), F(2.4, 1.8), F(-2.0, 2.2)]), 1.2, (0, 0.2), 1.0), "k", -1)
    torso = [F(-2.2, -0.4), F(-2.6, -ln + 4.0), F(-2.6, -ln + 0.6), F(-0.8, -ln - 0.8), F(1.8, -ln - 0.6),
             F(3.0, -ln + 2.2), F(3.2, -ln + 5.6), F(2.4, -1.4), F(0.6, -0.2)]
    tmask = poly_mask(torso)
    Bd.paint(n_plate(tmask, 1.8, (-0.3, -0.15), 1.2), "k", 0)
    info["torso"] = tmask
    vest = poly_mask([F(0.6, -ln + 0.2), F(3.4, -ln + 2.0), F(3.6, -ln + 5.6), F(2.8, -0.6), F(-0.4, -0.8)])
    Bd.decal([q for q in vest if q in tmask], ("r", 4))
    Bd.decal([q for q in vest if q in tmask and (q[0] - 1, q[1]) not in vest], ("r", 1))
    Bd.decal([q for q in vest if q in tmask and (q[0] + 1, q[1]) not in tmask], ("r", 4))
    Bd.decal([ip(F(2.6, -ln + 4.0)), ip(F(2.4, -ln + 6.4))], ("s", 4))            # waistcoat buttons
    Bd.paint(n_capsule(F(0.4, -ln - 0.3), lerp(F(0.4, -ln - 0.3), G(-0.2, 2.4), 0.8), 1.1, 0.9), "v", -1)
    Bd.paint(n_capsule(F(-0.2, -ln - 0.4), F(2.0, -ln - 0.6), 1.0, 0.9), "w", 0, ao=0)

    # ---------------- head: gaunt, long nose, pointed ear, slicked black hair, red eye
    Hl = Ls["Head"]
    face = [G(-2.2, -0.8), G(-1.4, -2.9), G(0.6, -3.3), G(2.0, -2.6), G(2.5, -1.2), G(4.4, 1.0), G(3.2, 1.2),
            G(2.6, 1.1), G(2.6, 1.8), G(2.3, 2.6), G(1.4, 3.2), G(0.0, 2.9), G(-1.6, 1.6)]
    hm = poly_mask(face)
    Hl.paint(n_plate(hm, 1.4, (-0.05, -0.25), 1.0), "v", 0)
    info["head"] = hm
    hair = poly_mask([G(1.9, -2.7), G(0.8, -3.8), G(-1.4, -3.8), G(-2.8, -2.4), G(-4.4, 0.0), G(-2.8, 0.4),
                      G(-1.4, -1.0), G(0.4, -2.3)])
    Hl.paint(n_plate(hair, 1.2, (-0.3, -0.4), 1.1), "q", 0, ao=0)
    Hl.decal([q for q in line(G(0.8, -3.0), G(-2.8, -1.2)) if q in hair], ("q", 4))
    ear = poly_mask([G(-0.2, -0.3), G(-0.3, 1.6), G(-1.2, 1.4), G(-3.0, -1.4)])
    Hl.paint(n_plate(ear, 0.8, (-0.2, -0.3), 1.0), "v", 0, ao=1)
    Hl.decal([ip(G(1.0, 1.2))], ("v", 2))                                     # hollow cheek
    if p["jaw"]:
        gape = poly_mask([G(1.2, 1.6), G(2.8, 1.5), G(2.6, 2.8), G(1.4, 2.4)])
        Hl.fixed({q: "b1" for q in gape if q in hm})
        Hl.fixed({ip(G(2.2, 1.6)): "w5", ip(G(2.0, 2.6)): "w4"})
    else:
        Hl.decal(line(G(1.6, 1.8), G(2.5, 1.8)), "OUT")
        Hl.decal([ip(G(2.2, 2.2))], "w5")
    e = ip(G(1.7, -0.9))
    info["eye"] = e
    CK.eye_glow(FX, e, p["eye"], 1)

    # ---------------- front arm
    arm(Ls["FrontArm"], shF, p["hf"], 0, pref=p.get("prefF", (0.3, -1.0)))
    Ls["FrontArm"].paint(n_dome(add(shF, (-0.2, -0.2)), 1.7, 1.6), "k", 0)
    for nm in ("Body", "FrontArm", "FrontLeg", "Tails"):
        L_ = Ls[nm]
        L_.decal([q for q, e_ in L_.px.items() if e_[0] == "k" and not isinstance(e_[3], str)
                  and (q[0] - 1, q[1]) not in L_.px and (q[0], q[1] - 1) not in L_.px], ("k", 4))

    # ---------------- fx
    for key, sm, grip, ang in (("F", p["smearF"], p["hf"], p["af"]), ("B", p["smearB"], p["hb"], p["ab"])):
        if sm:
            hot = swept(FX, sm["g0"], sm["a0"], grip, ang, sm.get("u0", 5), KNIFE["end"] + 0.5, hw=0.7,
                        mid=sm.get("mid"), start=sm.get("start", 0.0), pal="silver", taper=sm.get("taper", 0.7),
                        clip_y=FLOOR)
            info["hit" + key] |= hot
    if p["glint"]:
        g = info["tip" + p["glint"][-1]] if isinstance(p["glint"], str) else p["glint"]
        info["glint"] = g
        x, y = ip(g)
        FX.put([(x, y)], "w5")
        FX.put([(x + 1, y), (x - 1, y), (x, y - 1), (x, y + 1)], "s4")
    if p["dust"]:
        for k in range(8):
            side_ = -1 if k % 2 else 1
            x = int(p["P"][0] + side_ * (3 + k * 1.3) + (hash01(k, fi, 9) - 0.5) * 2)
            y = FLOOR - int(hash01(k, fi, 10) * (1 + k * 0.4) * (1.0 if p["dust"] == 1 else 0.5))
            FX.put([(x, y)], ("a2", "a1", "a3")[k % 3])
    info["hit"] = info["hitF"] | info["hitB"]
    return Ls, info


# =========================================================================== animations
def a_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 0.8, 0.4)[i]
        fr.append((170, P_(P=(26.5, 31.5 + b * 0.3), C=(30.8, 22.4 + b * 0.7), Hd=(35.2, 18.2 + b * 0.8),
                           hf=(38.5, 30.5 + b * 0.5), af=20 + b * 3, hb=(35.0, 32.5 + b * 0.5), ab=35 + b * 3)))
    return fr


def a_walk():
    """Stalking crouch-walk: planted foot travels back 3px per frame, the other swings through."""
    fr = []
    A = 4.5
    for i in range(6):
        ph = i / 6.0
        feet = []
        for off in (0.0, 0.5):
            q = (ph + off) % 1.0
            if q < 0.5:
                x, lift = A - 4 * A * q, 0.0
            else:
                s = (q - 0.5) / 0.5
                x, lift = -A + 2 * A * (s * s * (3 - 2 * s)), 2.2 * math.sin(math.pi * s)
            feet.append((x, lift))
        (xf, lf), (xb, lb) = feet
        bob = 0.8 * abs(math.cos(2 * math.pi * ph))
        sw = math.sin(2 * math.pi * ph)
        fr.append((110, P_(P=(26.8, 31.6 + bob), C=(31.2, 22.6 + bob), Hd=(35.6, 18.5 + bob),
                           ff=(27.5 + xf, FLOOR - lf), fb=(27.0 + xb, FLOOR - lb),
                           hf=(38.4 - sw * 1.2, 30.6 + bob), af=22 - sw * 4, hb=(35.0 + sw * 1.2, 32.6 + bob),
                           ab=35 + sw * 4)))
    return fr


def a_slash():
    crouch = dict(P=(25.6, 34.0), C=(29.8, 25.0), Hd=(34.0, 21.4), hup=(0.18, -1), fb=(20.5, FLOOR), ff=(31.5, FLOOR))
    lunge = dict(P=(29.0, 32.6), C=(34.2, 24.2), Hd=(38.8, 20.8), hup=(0.28, -1), fb=(21.5, FLOOR), ff=(36.0, FLOOR))
    return [
        (120, P_(**crouch, hf=(31.0, 26.0), af=-100, hb=(28.0, 33.0), ab=160)),
        (130, P_(**dict(crouch, P=(25.0, 35.0), C=(28.6, 26.0), Hd=(32.6, 22.4)), hf=(27.5, 19.5), af=-130,
                 hb=(24.0, 32.5), ab=175)),
        (230, P_(**dict(crouch, P=(24.8, 35.4), C=(28.2, 26.4), Hd=(32.2, 22.8)), hf=(27.0, 19.0), af=-134,
                 hb=(23.5, 32.8), ab=176, eye=2, jaw=1, glint="tipF")),
        (70, P_(**dict(lunge, P=(27.6, 33.0), C=(32.4, 24.4), Hd=(37.0, 21.0)), hf=(33.0, 18.5), af=-90,
                hb=(26.0, 32.0), ab=178, jaw=1)),
        (60, P_(**lunge, hf=(43.0, 33.0), af=40, hb=(27.0, 31.0), ab=176, jaw=1,
                smearF=dict(g0=(33.0, 18.5), a0=-90, mid=(43.0, 20.0), u0=4))),
        (80, P_(**lunge, hf=(40.0, 38.0), af=95, hb=(28.0, 29.0), ab=190, jaw=1)),
        (60, P_(**dict(lunge, C=(34.6, 24.6), Hd=(39.2, 21.2)), hf=(40.0, 38.0), af=100, hb=(43.5, 31.0), ab=-8, jaw=1,
                smearB=dict(g0=(28.0, 29.0), a0=190, mid=(36.0, 36.0), u0=4))),
        (120, P_(**dict(lunge, P=(28.4, 32.4), C=(33.2, 23.6), Hd=(37.8, 20.0)), hf=(38.0, 35.0), af=70,
                 hb=(40.0, 28.0), ab=-40)),
        (140, P_(P=(27.0, 31.8), C=(31.2, 22.6), Hd=(35.4, 18.8), fb=(21.5, FLOOR), ff=(33.0, FLOOR - 1.5),
                 hf=(38.0, 31.0), af=24, hb=(34.5, 32.5), ab=34)),
    ]


def a_lunge():
    coil = dict(P=(24.0, 36.0), C=(28.4, 27.6), Hd=(32.8, 24.8), hup=(0.28, -1), fb=(19.5, FLOOR), ff=(31.0, FLOOR))
    return [
        (110, P_(P=(25.6, 33.4), C=(29.8, 24.4), Hd=(34.0, 20.8), hup=(0.18, -1), fb=(20.5, FLOOR), ff=(31.5, FLOOR),
                 hf=(33.0, 32.0), af=20, hb=(29.0, 33.0), ab=10)),
        (120, P_(**coil, hf=(27.0, 30.0), af=-8, hb=(24.0, 32.0), ab=-4)),
        (130, P_(**dict(coil, P=(23.4, 37.0), C=(27.6, 28.8), Hd=(32.2, 26.2)), hf=(25.5, 30.5), af=-6,
                 hb=(22.5, 32.5), ab=-2)),
        (240, P_(**dict(coil, P=(23.2, 37.4), C=(27.3, 29.2), Hd=(31.9, 26.7)), hf=(25.0, 31.0), af=-6,
                 hb=(22.0, 33.0), ab=-2, eye=2, jaw=1)),
        (70, P_(P=(27.0, 31.0), C=(33.0, 24.6), Hd=(38.0, 22.4), hup=(0.48, -1), fb=(19.0, FLOOR), ff=(27.5, FLOOR - 3.0),
                kf=(31.0, 38.0), hf=(40.0, 26.0), af=-5, hb=(37.0, 27.0), ab=-3, jaw=1, dust=1, flare=0.4)),
        (80, up(P_(P=(27.0, 30.0), C=(35.4, 25.6), Hd=(41.4, 24.2), hup=(0.75, -1), fb=(15.5, 35.0), ff=(20.0, 37.0),
                   kb=(21.0, 31.6), kf=(25.0, 35.0), hf=(47.0, 27.0), af=6, hb=(45.0, 29.0), ab=10, jaw=1, flare=0.8,
                   eye=2), 4)),
        (90, up(P_(P=(27.0, 30.0), C=(35.4, 26.2), Hd=(41.4, 25.0), hup=(0.75, -1), fb=(17.0, 37.5), ff=(22.0, 39.0),
                   kb=(22.0, 33.0), kf=(26.5, 36.5), hf=(47.0, 28.0), af=10, hb=(45.0, 30.0), ab=14, jaw=1, flare=0.6,
                   eye=2), 3)),
        (90, P_(P=(28.0, 36.2), C=(33.0, 28.4), Hd=(37.8, 26.0), hup=(0.48, -1), fb=(21.0, FLOOR), ff=(35.0, FLOOR),
                hf=(42.0, 38.0), af=40, hb=(39.0, 40.0), ab=35, dust=1, flare=0.2)),
        (130, P_(P=(27.6, 34.4), C=(32.0, 25.6), Hd=(36.4, 22.2), hup=(0.28, -1), fb=(21.0, FLOOR), ff=(35.0, FLOOR),
                 hf=(39.0, 34.0), af=40, hb=(35.0, 35.0), ab=30, dust=2)),
        (140, P_(P=(27.0, 32.0), C=(31.2, 22.9), Hd=(35.4, 19.1), fb=(21.5, FLOOR), ff=(33.0, FLOOR),
                 hf=(38.5, 30.8), af=22, hb=(35.0, 32.6), ab=35)),
    ]


def a_emerge():
    """Drops out of a portrait above: feet first from the top edge, falls with the coat flaring, lands in a
    crouch (dust) and rises into the hunched stance."""
    crouch = dict(P=(26.0, 37.6), C=(30.8, 29.8), Hd=(35.2, 27.4), hup=(0.38, -1), fb=(20.5, FLOOR), ff=(32.0, FLOOR))
    return [
        (90, up(P_(P=(27.0, 30.0), C=(28.4, 20.0), Hd=(30.4, 14.2), hup=(-0.1, -1), fb=(24.5, 44.0), ff=(29.5, 45.0),
                   hf=(34.0, 13.0), af=-70, hb=(24.0, 12.0), ab=-110, flare=1.0, eye=2), 27)),
        (80, up(P_(P=(27.0, 30.0), C=(28.6, 20.0), Hd=(30.8, 14.4), hup=(-0.05, -1), fb=(23.5, 44.0), ff=(30.0, 45.5),
                   hf=(35.0, 16.0), af=-60, hb=(22.5, 15.0), ab=-120, flare=0.9, eye=2), 11)),
        (90, P_(**crouch, hf=(37.0, 42.0), af=20, hb=(22.0, 42.0), ab=160, dust=1, flare=0.3, eye=2, jaw=1)),
        (170, P_(**dict(crouch, P=(26.0, 37.2), C=(30.8, 29.4), Hd=(35.2, 27.0)), hf=(37.0, 41.5), af=24,
                 hb=(22.5, 41.5), ab=156, dust=2, eye=2, jaw=1)),
        (130, P_(P=(26.2, 34.4), C=(30.6, 25.6), Hd=(35.0, 22.0), hup=(0.23, -1), fb=(20.5, FLOOR), ff=(32.0, FLOOR),
                 hf=(36.0, 36.0), af=40, hb=(28.0, 36.0), ab=70)),
        (140, P_(P=(26.5, 31.8), C=(30.8, 22.6), Hd=(35.0, 18.8), fb=(21.5, FLOOR), ff=(32.0, FLOOR),
                 hf=(38.5, 30.8), af=22, hb=(35.0, 32.6), ab=35)),
    ]


def a_hurt():
    return [
        (90, P_(P=(25.4, 31.6), C=(27.4, 22.2), Hd=(29.8, 17.4), hup=(-0.4, -1), hf=(33.0, 28.0), af=-30,
                hb=(27.0, 27.0), ab=-40, eye=2, jaw=1)),
        (130, P_(P=(26.0, 32.0), C=(29.8, 22.8), Hd=(33.6, 18.6), hup=(-0.02, -1), hf=(35.0, 31.5), af=30,
                 hb=(30.0, 31.0), ab=20)),
    ]


def a_death():
    def ash(frac, pool):
        def f(imgs, ph):
            out = CK.crumble(imgs, frac, BODY, (30.0, 42.0), seed=5, radius=20.0)
            fx = out["FX"].copy()
            px = fx.load()
            for x in range(int(30 - pool), int(30 + pool) + 1):
                t = abs(x + .5 - 30) / max(1.0, pool)
                if t < 1 and px[x, FLOOR][3] == 0:
                    px[x, FLOOR] = K.RGBA["b2" if t < 0.6 else "b1"]
                if t < 0.5 and px[x, FLOOR - 1][3] == 0 and K.hash01(x, 1, 3) < 0.6 and pool > 5:
                    px[x, FLOOR - 1] = K.RGBA["a2" if K.hash01(x, 2, 3) < 0.5 else "b3"]
            out["FX"] = fx
            return out
        return f
    kneel = dict(P=(25.0, 39.4), C=(29.0, 30.8), Hd=(33.0, 28.4), hup=(0.48, -1), kb=(24.0, 45.8), fb=(15.8, FLOOR),
                 ff=(32.0, FLOOR))
    down = dict(P=(26.0, 42.4), C=(33.8, 38.6), Hd=(38.8, 40.0), hup=(1.0, 0.2), kb=(22.8, 45.6), fb=(14.6, FLOOR),
                kf=(30.0, 45.4), ff=(22.0, FLOOR), hf=(42.0, 45.0), af=10, hb=(38.0, 45.5), ab=175, eye=0)
    return [
        (90, P_(P=(25.2, 31.6), C=(27.0, 22.2), Hd=(29.0, 17.2), hup=(-0.5, -1), hf=(32.0, 26.0), af=-40,
                hb=(26.0, 26.0), ab=-50, eye=2, jaw=1)),
        (140, P_(**kneel, hf=(34.0, 42.0), af=60, hb=(30.0, 42.0), ab=80, eye=1, jaw=1)),
        (150, P_(**down, post=ash(0.0, 3))),
        (130, P_(**down, post=ash(0.4, 6))),
        (140, P_(**down, post=ash(0.75, 9))),
        (500, P_(**down, post=ash(1.01, 11))),
    ]


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("slash", a_slash), ("lunge", a_lunge), ("emerge", a_emerge),
           ("hurt", a_hurt), ("death", a_death)]
COUNTS = dict(idle=4, walk=6, slash=9, lunge=10, emerge=6, hurt=2, death=6)
LOOPS = ("idle", "walk")
ALLOW_TOP = ("emerge",)


def setup():
    K.setup(W, H)


draw_fn = draw
