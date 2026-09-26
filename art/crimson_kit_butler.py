"""Rig for "The Butler" (Crimson Manor mini-boss), used by gen_crimson_butler.py.

A tall, gaunt vampire butler (~62px) in a 128x80 frame, faces RIGHT, feet on the bottom row, anchor [56, 80].
Parts (bottom -> top): FXBack, WingBack (far coat-tail / bat wing, crimson lining side), WeaponBack, BackArm
(the off hand: folded behind his back by default, throws the silver knives in `serve`), BackLeg, Body (tailcoat,
white shirt front, crimson cravat), FrontLeg, WingFront (near coat-tail / bat wing, black outer face), Head
(slicked silver-white hair, aquiline nose, pointed ear), Weapon (long silver serving blade), FrontArm, Blood
(phase 2 only: fresh blood on the blade and cuffs), FX (eyes, smears, bats).

The coat tails ARE folded bat wings: each tail is a wing whose finger bones hang down; `wingB` / `wingF` (0..1)
unfold them (polar interpolation around the waist root, so the tips swing outward and up like a real wing).
Phase 2 reuses the same poses: wings at least half open and torn, eyes blazing, blood on blade and cuffs.

`face` = -1 mirrors the pose about AX (used for the spin in `flourish`); lighting stays upper-left.
"""
import math

import crimson_kit as CK
import enemy_kit as K
from enemy_kit import (Layer, FXLayer, ID, basis, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,
                       poly_mask, n_plate, n_dome, n_capsule, blade_px, swept, thrust_lines, dirv)
from PIL import Image

W, H = 128, 80
FLOOR = H - 1
AX = 56

LAYERS = ["FXBack", "WingBack", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "WingFront", "Head",
          "Weapon", "FrontArm", "Blood", "FX"]
FXL = {"FXBack", "Blood", "FX"}
LEG = 13.9
TORSO, NECK = 17.32, 8.83
BODY_LAYERS = [n for n in LAYERS if n not in ("FXBack", "FX", "Blood")]

BLADE = dict(pommel=-4.6, grip_end=0.4, grip="q2", grip_w=0.75, pommel_c="s4", guard=(0.4, 1.5, 2.6),
             guard_c="s3", guard_hi="s5", b0=1.5, end=31.0, w_edge=1.05, w_spine=0.75, taper=0.28, fuller=None,
             edge_hi="w5", edge="s4", spine="s2")
KNIFE = dict(pommel=-2.2, grip_end=0.3, grip="q2", grip_w=0.6, pommel_c="s3", guard=(0.3, 0.9, 1.2),
             guard_c="s3", guard_hi="s4", b0=0.9, end=6.5, w_edge=0.8, w_spine=0.4, taper=0.35, fuller=None,
             edge_hi="w5", edge="s4", spine="s3")

NEU = dict(P=(55.5, 50.5), C=(56.4, 33.2), Hd=(58.4, 24.6), hup=(0.1, -1), fb=(50.5, FLOOR), ff=(61.5, FLOOR),
           kb=None, kf=None, hf=(64.0, 51.5), wang=52, wl="Weapon", hb=None, knives=0, wingB=0.0, wingF=0.0, eye=1,
           face=1, smear=None, flat=None, thrust=None, glint=None, bats=0.0, bseed=0, dissolve=0.0, dust=0,
           wind=0.0, blade=True, blade_floor=None, flick=None, bow=0.0, brow=0.0, hold_chest=False, tilt=0.0)

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


def mirror(p):
    q = dict(p)
    for k in PTS:
        if q.get(k) is not None:
            q[k] = (2 * AX - q[k][0], q[k][1])
    q["hup"] = (-p["hup"][0], p["hup"][1])
    q["wang"] = 180 - p["wang"]
    return q


# =========================================================================== helpers
def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def polar_lerp(a, b, t):
    r0, r1 = math.hypot(*a), math.hypot(*b)
    a0, a1 = math.atan2(a[1], a[0]), math.atan2(b[1], b[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    r = r0 + (r1 - r0) * t
    an = a0 + da * t
    return (math.cos(an) * r, math.sin(an) * r)


def qarc(p0, mid, p1, n=8):
    """Quadratic arc from p0 to p1 passing through mid (scalloped wing edge)."""
    c = (2 * mid[0] - (p0[0] + p1[0]) / 2, 2 * mid[1] - (p0[1] + p1[1]) / 2)
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]))
    return out


# wing keypoints in local (u = outward from the body, v = down): folded (coat tail) -> open (bat wing)
WING = {
    "wr": ((1.4, 5.0), (10.0, -13.0)),
    "t1": ((3.6, 20.5), (12.5, -31.0)),
    "s1": ((2.6, 17.4), (15.0, -19.0)),
    "t2": ((1.5, 22.0), (26.5, -21.0)),
    "s2": ((0.5, 17.8), (19.5, -9.5)),
    "t3": ((-0.9, 20.2), (30.5, -4.5)),
    "s3": ((-1.1, 15.5), (18.0, 2.5)),
    "at": ((-1.7, 6.0), (4.5, 9.0)),
}


def wing(L, FX, root, openv, dirx, fi, mat, bias, torn=0.0, lining=None, sw=0.0, seed=0, arot=0.0, scl=1.0):
    """Coat-tail / bat wing hanging from root.  dirx = -1 extends to the left (behind a right-facing body)."""
    t = smooth(openv)
    pts = {}
    ca_, sa_ = math.cos(math.radians(arot)), math.sin(math.radians(arot))
    for k, (fo, op) in WING.items():
        op = ((op[0] * ca_ - op[1] * sa_) * scl, (op[0] * sa_ + op[1] * ca_) * scl)
        u, v = polar_lerp(fo, op, t)
        # folded tails sway with the body, open wings flutter a little
        u += sw * 0.35 * max(0.0, v) / 20.0 * (1 - t)
        if t > 0.3 and k in ("t1", "t2", "t3"):
            v += math.sin(fi * 1.7 + ord(k[1])) * 0.8 * t
        if torn and k in ("t2", "t3", "s2", "s3"):
            u -= torn * (1.5 + hash01(ord(k[1]), seed, 3) * 2.0) * (1 if k[0] == "t" else 0.3)
        pts[k] = (root[0] + dirx * u, root[1] + v)
    edge = [root, pts["wr"], pts["t1"]]
    edge += qarc(pts["t1"], pts["s1"], pts["t2"])[1:]
    edge += qarc(pts["t2"], pts["s2"], pts["t3"])[1:]
    edge += qarc(pts["t3"], pts["s3"], pts["at"], 6)[1:]
    m = poly_mask(edge)
    if torn:
        # ragged holes in the membrane and a frayed trailing edge
        for k, (a, b, f) in enumerate((("wr", "s1", 0.62), ("wr", "s2", 0.7), ("wr", "s3", 0.55))):
            c = lerp(pts[a], pts[b], f)
            r = (0.9 + 0.9 * hash01(k, seed, 7)) * (0.6 + 0.6 * t)
            m -= mask_disc(add(c, (hash01(k, seed, 8) - 0.5, 0)), r, r * 1.4)
        for q in list(m):
            near = sum((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if near and hash01(q[0], q[1], 60 + seed) < 0.3 * torn:
                m.discard(q)
    fold = (lambda x, y: (0.5 * math.sin((x - root[0]) * 0.9 + y * 0.3), 0.0)) if t < 0.35 else \
        (lambda x, y: (0.35 * math.sin(math.atan2(y - pts["wr"][1], x - pts["wr"][0]) * 7.0), 0.0))
    L.paint(n_plate(m, 1.4, (0.15, -0.1), 0.9, fold=fold), mat, bias, ao=0)
    # finger bones (ridges) + the arm bone along the leading edge
    ridge = (mat, len(K.RAMP[mat]) - 2 + (bias if bias < 0 else 0))
    shade = (mat, max(0, 1 + bias))
    bones = [line(root, pts["wr"]), line(pts["wr"], pts["t1"]), line(pts["wr"], pts["t2"]), line(pts["wr"], pts["t3"])]
    for i, bl in enumerate(bones):
        if t < 0.25 and i in (0,):
            continue
        L.decal([q for q in bl if q in m], ridge)
        L.decal([(q[0], q[1] + 1) for q in bl if (q[0], q[1] + 1) in m and (q[0], q[1] + 1) not in bl], shade)
    if lining and t >= 0.3:
        # the velvet lining shows along the scalloped trailing edge of the open coat-wing
        tr = set(qarc(pts["t1"], pts["s1"], pts["t2"], 12) + qarc(pts["t2"], pts["s2"], pts["t3"], 12)
                 + qarc(pts["t3"], pts["s3"], pts["at"], 10))
        tr = {ip(q) for q in tr}
        L.decal([q for q in m if q in tr or any((q[0] + a, q[1] + b) in tr for a, b in ((0, -1), (dirx, 0)))
                 and (q[0], q[1] + 1) not in m], (lining, 2))
    if t > 0.2:
        # thumb claw at the wrist
        w_ = ip(pts["wr"])
        L.fixed({(w_[0] + dirx, w_[1] - 1): "s3", (w_[0] + dirx * 2, w_[1] - 1): "s4"})
    return m, pts


def shoe_leg(L, hip, foot, kn_hint, face, bias):
    """Slim trousered leg with a satin side stripe and a pointed patent shoe.  foot = (x, floor row)."""
    fx, fy = foot
    ank = (fx, fy - 1.6)
    ank = CK.clamp_reach(hip, ank, 2 * LEG - 0.05)
    if kn_hint is not None:                 # a knee key is only a bend hint: segment lengths stay exact
        m = lerp(hip, ank, 0.5)
        kn = ik(hip, ank, LEG, LEG, (kn_hint[0] - m[0], kn_hint[1] - m[1]))
    else:
        kn = ik(hip, ank, LEG, LEG, (face, -0.15))
    L.paint(n_capsule(hip, kn, 2.4, 2.0), "k", bias)
    L.paint(n_capsule(kn, ank, 2.0, 1.55), "k", bias)
    L.decal(line(add(hip, (0.3 * face, 1.0)), add(kn, (0.2 * face, 0))) + line(kn, add(ank, (0, -1))),
            ("q", 3 + min(0, bias)))
    toe = face
    sole = [(fx - 2.0 * toe, fy + 1), (fx - 2.0 * toe, fy - 2.3), (fx + 0.8 * toe, fy - 2.6), (fx + 3.6 * toe, fy - 1.0),
            (fx + 5.0 * toe, fy + 0.2), (fx + 5.0 * toe, fy + 1)]
    L.paint(n_plate(poly_mask(sole), 1.0, (0, -0.35), 1.1), "q", bias, ao=0)
    return kn


def flat_arc(FX, spec, pal, exclude=(), back=None):
    """Horizontal cleave seen side-on (flattened crescent).  spec: c, rx, ry, th0, th1 (deg), w, fade."""
    cols = K.SMEAR[pal]
    cx, cy = spec["c"]
    rx, ry, th0, th1, wd = spec["rx"], spec["ry"], spec["th0"], spec["th1"], spec.get("w", 5.0)
    fade = spec.get("fade", 0.0)
    hot = set()
    for y in range(int(cy - ry - wd - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            ux, uy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = math.hypot(ux, uy)
            if d == 0:
                continue
            th = math.degrees(math.atan2(uy, ux))
            if th0 > th1:
                th = th if th <= th0 else th - 360
                tt = (th0 - th) / (th0 - th1)
            else:
                th = th if th >= th0 else th + 360
                tt = (th - th0) / (th1 - th0)
            if not (0 <= tt <= 1):
                continue
            thick = wd * (0.25 + 0.75 * math.sin(math.pi * min(1.0, tt * 1.15)) ** 0.7) * (1 - fade * 0.6)
            grad = math.hypot(ux / rx, uy / ry) / d
            dd = (1 - d) / max(grad, 1e-6)
            if dd < -0.5 or dd > thick:
                continue
            if (x, y) in exclude or not K.inb(x, y) or y > FLOOR:
                continue
            age = 1 - tt
            if fade and hash01(x, y, 77) < fade * 0.7:
                continue
            if age > 0.7 and int(dd) % 2 == 1:
                continue
            if dd < 1.2 and age < 0.5:
                c = cols[0]
            elif dd < thick * 0.45:
                c = cols[1] if age < 0.6 else cols[2]
            else:
                c = cols[2] if age < 0.5 else cols[3]
            (back if (back is not None and uy < -0.2) else FX).put([(x, y)], c)
            if age < 0.8 and not fade:
                hot.add((x, y))
    return hot


def star(FX, c, core="w5", arm_="s4", big=True):
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], core if big else arm_)
    if big:
        for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0)):
            FX.put([(x + d[0], y + d[1])], arm_)


# =========================================================================== the butler
def draw(p, fi, sw, phase):
    face = p["face"]
    if face < 0:
        p = mirror(p)
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB, BL = FXLayer("FX"), FXLayer("FXBack"), FXLayer("Blood")
    Ls["FX"], Ls["FXBack"], Ls["Blood"] = FX, FXB, BL
    R = ID
    p = CK.normalize_spine(p, TORSO, NECK)
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F0 = basis(P, upv)
    F = lambda a, b: F0(a * face, b)          # noqa: E731
    G0 = basis(Hd, p["hup"])
    G = lambda a, b: G0(a * face, b)          # noqa: E731
    shF, shB = F(0.3, -ln + 2.3), F(-2.2, -ln + 2.5)
    hF, hB = F(1.3, 0.8), F(-1.5, 0.8)
    info = {"hit": set(), "smear": set()}
    p2 = phase == 2
    p["hf"] = CK.clamp_reach(shF, p["hf"], 10.6 + 10.4 - 0.05)
    if p["hb"] is not None:
        p["hb"] = CK.clamp_reach(shB, p["hb"], 10.5 + 10.3 - 0.05)

    # ---------------- weapon
    blade = set()
    if p["blade"]:
        grip, wang = p["hf"], p["wang"]
        pix, blade, tip = blade_px(ID, grip, wang, BLADE)
        pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
        blade = {q for q in blade if q[1] <= FLOOR}
        Ls[p["wl"]].fixed(pix)
        info["hit"] |= blade
        info["tip"] = tip
        if p2:
            ca, sa = dirv(wang)
            bl = []
            for q in blade:
                u = (q[0] + .5 - grip[0]) * ca + (q[1] + .5 - grip[1]) * sa
                if u > 12 and hash01(q[0], q[1], 31) < 0.25 + 0.5 * (u - 12) / 19:
                    bl.append((q, "b3" if hash01(q[0], q[1], 32) < 0.6 else "b2"))
            for q, c in bl:
                BL.put([q], c)
            if -30 < wang < 150:                 # blood running off the lower edge
                for k, u in enumerate((17, 23, 29)):
                    src = (grip[0] + ca * u, grip[1] + sa * u + 1.5)
                    if src[1] < FLOOR - 3:
                        CK.blood_drip(BL, src, fi, 3.0, seed=k)
    elif p["blade_floor"]:
        grip, wang = p["blade_floor"]
        pix, _, _ = blade_px(ID, grip, wang, BLADE)
        Ls["Weapon"].fixed({q: c for q, c in pix.items() if q[1] <= FLOOR})

    # ---------------- coat tails / bat wings
    oB, oF = p["wingB"], p["wingF"]
    if p2:
        oB, oF = max(oB, 0.45), max(oF, 0.42)
    torn = 1.0 if p2 else 0.0
    rootB = F(-2.6, -1.6)
    rootF = F(-2.2, -1.0)
    mB, wpB = wing(Ls["WingBack"], FX, add(rootB, (0.0, -0.6 * smooth(oB))), oB, -face, fi,
                   "r" if oB > 0.3 else "k", -1, torn, None, sw, seed=1, arot=-24.0, scl=1.08)
    mF, wpF = wing(Ls["WingFront"], FX, rootF, oF, -face, fi, "k", 0, torn, "r", sw * 1.2, seed=2, arot=6.0,
                   scl=1.1)
    info["wings"] = mB | mF
    info["wing_pts"] = (wpB, wpF)

    # ---------------- back arm (off hand): folded behind the back unless posed
    Ba = Ls["BackArm"]
    behind = p["hb"] is None
    if behind:
        el = F(-5.4, -ln + 10.6)
        hb = F(1.0, -3.4)
    else:
        hb = p["hb"]
        el = ik(shB, hb, 10.5, 10.3, (-face * 0.3, 1.0))
    Ba.paint(n_capsule(shB, el, 1.9, 1.7), "k", -1)
    Ba.paint(n_capsule(el, hb, 1.7, 1.4), "k", -1)
    if not behind:
        cuff = lerp(el, hb, 0.8)
        Ba.paint(n_capsule(cuff, lerp(el, hb, 0.93), 1.7, 1.6), "w", -1, ao=0)
        if p["knives"]:
            d = sub(hb, el)
            base = math.degrees(math.atan2(d[1], d[0]))
            for k, da in enumerate((-26, 0, 26)[:p["knives"]]):
                kp, kb_, _ = blade_px(ID, add(hb, (dirv(base + da)[0] * 0.8, dirv(base + da)[1] * 0.8)),
                                      base + da * 1.0, KNIFE)
                Ba.fixed(kp)
        Ba.paint(n_dome(hb, 1.5, 1.4), "w", -1)
        if p2:
            Ba.decal([q for q in mask_disc(cuff, 1.8) if hash01(q[0], q[1], 33) < 0.55], "b2")
    info["hb"] = hb
    info["el_b"] = el

    # ---------------- legs
    kb = shoe_leg(Ls["BackLeg"], hB, p["fb"], p["kb"], face, -1)
    kf = shoe_leg(Ls["FrontLeg"], hF, p["ff"], p["kf"], face, 0)
    info["knees"] = (kb, kf)

    # ---------------- torso: trousers seat, tailcoat, shirt front, cravat
    Bd = Ls["Body"]
    pel = [F(-3.0, -2.4), F(2.8, -2.4), F(3.3, 2.2), F(1.0, 3.6), F(-2.6, 3.0)]
    Bd.paint(n_plate(poly_mask(pel), 1.6, (0, 0.2), 1.0), "k", -1)
    torso = [F(-2.9, -0.6), F(-3.3, -ln + 7.0), F(-4.3, -ln + 1.2), F(-2.2, -ln - 0.9), F(2.2, -ln - 0.9),
             F(4.6, -ln + 2.2), F(5.1, -ln + 6.6), F(3.6, -ln + 11.5), F(2.9, -2.4), F(1.2, -0.2)]
    tm = poly_mask(torso)
    Bd.paint(n_plate(tm, 2.4, (-0.3, -0.15), 1.25), "k", 0)
    info["torso"] = tm
    shirt = poly_mask([F(1.4, -ln - 0.9), F(2.8, -ln - 1.0), F(4.8, -ln + 2.2), F(5.3, -ln + 6.6),
                       F(4.4, -ln + 7.8), F(2.8, -ln + 2.4)])
    Bd.decal([q for q in shirt if q in tm], ("w", 4))
    Bd.decal([q for q in shirt if q in tm and (q[0] - face, q[1]) not in shirt], ("w", 2))
    Bd.decal(line(F(2.4, -ln + 2.0), F(3.9, -ln + 8.6)), ("q", 4))           # satin lapel edge
    Bd.decal(line(F(1.7, -ln + 2.4), F(3.2, -ln + 9.0)), ("q", 2))
    for b in (-ln + 9.6, -ln + 12.2):                                          # silver buttons
        Bd.decal([ip(F(3.0, b))], ("s", 4))
    ch = polyline([F(2.8, -3.4), F(1.6, -2.4), F(0.2, -2.6)])                # watch chain
    Bd.decal([q for i, q in enumerate(ch) if i % 2 == 0], ("s", 4))
    Bd.decal(line(F(-3.0, -2.6), F(3.0, -2.6)), ("k", 1))                     # waist seam
    # neck, high wing collar, crimson cravat with a silver pin
    Hl = Ls["Head"]
    neck_a, neck_b = F(0.7, -ln - 0.6), G(-0.6, 3.2)
    Bd.paint(n_capsule(neck_a, neck_b, 1.5, 1.3), "v", -1)
    Bd.paint(n_capsule(F(-0.4, -ln - 0.4), lerp(F(1.6, -ln - 1.0), G(1.2, 4.4), 0.55), 1.4, 1.1), "w", 0)
    cr = F(3.9, -ln + 0.6)
    Bd.paint(n_dome(cr, 1.7, 1.9), "r", 0)
    Bd.paint(n_capsule(cr, F(4.5, -ln + 4.2), 1.5, 0.9), "r", 0, ao=0)
    Bd.decal([ip(add(cr, (0.3 * face, 0.6)))], ("s", 5))

    # ---------------- head: small, gaunt, aquiline; slicked silver-white hair; pointed ear
    face_poly = [G(-3.0, -1.2), G(-2.0, -4.0), G(0.6, -4.6), G(2.7, -3.8), G(3.5, -2.2), G(3.6, -1.2), G(5.1, 0.7),
                 G(6.2, 1.9), G(5.2, 2.0), G(4.0, 2.0), G(3.9, 2.9), G(3.5, 3.1), G(3.4, 3.9), G(2.6, 4.7),
                 G(1.0, 4.4), G(-0.6, 3.3), G(-2.6, 1.6)]
    hm = poly_mask(face_poly)
    Hl.paint(n_plate(hm, 1.8, (-0.05, -0.25), 1.0), "v", 0)
    info["head"] = hm
    hair = poly_mask([G(2.9, -3.4), G(1.4, -5.0), G(-1.4, -5.3), G(-3.6, -3.8), G(-4.9, -1.6), G(-6.2, 1.0),
                      G(-4.6, 1.2), G(-2.4, 0.4), G(-0.8, -1.8), G(1.2, -3.0)])
    Hl.paint(n_plate(hair, 1.6, (-0.3, -0.4), 1.1), "j", 0, ao=0)
    Hl.decal([q for q in line(G(1.0, -4.0), G(-4.6, -0.6)) if q in hair], ("j", 2))          # one comb groove
    ear = poly_mask([G(-0.2, -0.4), G(-0.2, 2.4), G(-1.4, 2.2), G(-4.4, -1.4)])
    Hl.paint(n_plate(ear, 0.9, (-0.2, -0.3), 1.0), "v", 0, ao=1)
    Hl.decal([ip(G(-1.0, 1.0))], ("v", 1))
    # features: brow ridge, sunken socket, cheek hollow, nostril, thin mouth, a fang
    Hl.decal([ip(G(2.4, -1.9)), ip(G(3.2, -1.9))], ("v", 1 if p["brow"] < 0.5 else 0))
    Hl.decal([ip(G(1.2, 1.5)), ip(G(2.0, 1.8))], ("v", 2))
    Hl.decal([ip(G(4.6, 1.5))], ("v", 1))
    Hl.decal(line(G(2.6, 2.9), G(3.6, 2.9)), "OUT")
    Hl.decal([ip(G(3.3, 3.3))], "w5")
    e = ip(G(2.5, -0.9))
    info["eye"] = e
    lvl = p["eye"]
    if p2 and lvl > 0:
        lvl = 3
    CK.eye_glow(FX, e, lvl, face, trail=(3 if p2 and lvl > 0 else 0))

    # ---------------- front arm (blade hand)
    Fa = Ls["FrontArm"]
    hf = p["hf"]
    if p["hold_chest"]:
        hf = F(3.6, -ln + 5.0)
    elf = ik(shF, hf, 10.6, 10.4, (-face, 0.7))
    Fa.paint(n_capsule(shF, elf, 2.0, 1.7), "k", 0)
    Fa.paint(n_capsule(elf, hf, 1.7, 1.45), "k", 0)
    Fa.paint(n_dome(add(shF, (-0.3 * face, -0.4)), 2.4, 2.2, tilt=(0.05, 0.1)), "k", 0)
    cuff = lerp(elf, hf, 0.8)
    Fa.paint(n_capsule(cuff, lerp(elf, hf, 0.93), 1.75, 1.65), "w", 0, ao=0)
    Fa.paint(n_dome(hf, 1.6, 1.5), "w", 0)
    if p2:
        Fa.decal([q for q in mask_disc(cuff, 2.0) | mask_disc(hf, 1.8) if hash01(q[0], q[1], 34) < 0.55],
                 "b3" if fi % 2 else "b2")
    info["hf"] = hf

    # ---------------- rim light so the black livery separates from dark rooms
    for nm in ("Body", "FrontArm", "FrontLeg", "BackArm"):
        L_ = Ls[nm]
        L_.decal([q for q, e_ in L_.px.items() if e_[0] == "k" and not isinstance(e_[3], str)
                  and (q[0] - face, q[1]) not in L_.px and (q[0], q[1] - 1) not in L_.px], ("k", 4))

    # ---------------- fx: smears, thrust streaks, glints, dust, the flick of knives
    pal = "blood" if p2 else "silver"
    if p["smear"]:
        sm = p["smear"]
        hot = swept(FX, sm["g0"], sm["a0"], p["hf"], p["wang"], sm.get("u0", 21), BLADE["end"] + 0.5, hw=0.8,
                    mid=sm.get("mid"), start=sm.get("start", 0.0), pal=pal, exclude=blade,
                    taper=sm.get("taper", 0.7), clip_y=FLOOR)
        info["hit"] |= hot
        info["smear"] |= hot
    for spec in (p["flat"] or []):
        hot = flat_arc(FX, spec, pal, exclude=blade, back=FXB)
        info["hit"] |= hot
        info["smear"] |= hot
    if p["thrust"]:
        th = p["thrust"]
        pts = thrust_lines(FX, p["hf"], p["wang"], th.get("u0", -20), th.get("u1", 6), th.get("offs", (-2, 2, 3)),
                           pal=pal, flash=th.get("flash"))
        info["hit"] |= {q for q in pts if q[0] > AX}
    if p["glint"]:
        star(FX, p["glint"], "w5", "e3" if p2 else "s4")
    if p["flick"]:
        # three knives just released from the off hand: short silver streaks fanning forward
        o, ang = p["flick"]
        for k, da in enumerate((-9, 0, 9)):
            dd = dirv(ang + da)
            a_ = add(o, (dd[0] * (2 + k), dd[1] * (2 + k)))
            b_ = add(a_, (dd[0] * 12, dd[1] * 12))
            seg = line(a_, b_)
            for j, q in enumerate(seg):
                FX.put([q], "s2" if j < len(seg) * 0.35 else "s4" if j < len(seg) - 3 else "w5")
            FX.put([(seg[-1][0], seg[-1][1] - 1), (seg[-1][0], seg[-1][1] + 1)], "s3")
        star(FX, add(o, (2, 0)), "w5", "s4", big=False)
    if p["dust"]:
        for fx_ in ((p["fb"][0], -1), (p["ff"][0], 1)):
            for k in range(5):
                x = int(fx_[0] + fx_[1] * (1 + k * 1.4) + (hash01(k, fi, 9) - 0.5) * 2)
                y = FLOOR - int(hash01(k, fi, 10) * (1.5 + k * 0.5))
                FX.put([(x, y)], ("a2", "a1", "a3")[k % 3])
    return Ls, info


# =========================================================================== bats (vanish / death)
def bat_dissolve(imgs, s, seed, fi, center, keep_eye=None, n_bats=30, spread=34, phase=1, names=None):
    """Body layers break apart into a swarm of small bats flying outward.  s = 0 intact .. 1 gone.
    Used backwards (s decreasing) the bats converge and the body re-forms."""
    names = list(names or BODY_LAYERS) + ["Blood"]
    cx, cy = center
    out = dict(imgs)
    body_px = []
    for n in names:
        if n not in imgs:
            continue
        src = imgs[n].load()
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = new.load()
        for y in range(H):
            for x in range(W):
                if src[x, y][3] == 0:
                    continue
                body_px.append((x, y))
                d = min(1.0, math.hypot((x - cx) / 1.0, (y - cy) / 1.5) / 32.0)
                t = 0.3 * hash01(x // 3, y // 3, 40 + seed) + 0.7 * (1 - d) ** 1.3
                if t >= s:
                    if t < s + 0.035 and s > 0.02:
                        dst[x, y] = K.RGBA["k1"]
                    else:
                        dst[x, y] = src[x, y]
        out[n] = new
    fx = imgs["FX"].copy()
    if s > 0.99:
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fp = fx.load()
    if s > 0.0 and body_px:
        nb = int(n_bats * min(1.0, 0.25 + s * 1.2))
        for k in range(nb):
            o = body_px[int(hash01(k, seed, 42) * len(body_px)) % len(body_px)]
            dx, dy = o[0] - cx, o[1] - cy
            dl = math.hypot(dx, dy) or 1.0
            a = math.atan2(dy / dl, dx / dl) + (hash01(k, seed, 43) - 0.5) * 1.2
            ux, uy = math.cos(a), math.sin(a) * 0.7 - 0.45
            born = hash01(k, seed, 44) * 0.6          # when this bat peels off
            if s < born:
                continue
            dist = (s - born) / (1 - born) * spread * (0.5 + hash01(k, seed, 45))
            dist *= 1 + 2.2 * max(0.0, s - 0.72) / 0.28           # at the end most of the swarm has left
            q = (o[0] + ux * dist, o[1] + uy * dist + math.sin(k + fi) * 1.2)
            small = dist > spread * 0.55 or k % 3 == 0
            flap = (fi + k) % 3
            pix = CK.bat_px(q, flap, small=small, body="k2" if k % 2 else "m1", rim="k4" if k % 2 else "m3",
                            eye=("e3" if phase == 1 else "e4") if k % 3 == 1 else None,
                            facing=1 if ux >= 0 else -1)
            ol = CK.outline_px(pix)
            for (x, y), c in list(ol.items()) + list(pix.items()):
                if 0 <= x < W and 0 <= y <= FLOOR:
                    if c == "OUT" and fp[x, y][3]:
                        continue
                    fp[x, y] = K.RGBA[c]
    if keep_eye is not None and s > 0.3:
        x, y = keep_eye
        if 0 <= x < W and 0 <= y < H:
            fp[x, y] = K.RGBA["e4" if phase == 2 else "e3"]
            fp[x + 1 if x + 1 < W else x, y] = K.RGBA["e2"]
    out["FX"] = fx
    return out
