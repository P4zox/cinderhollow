"""The Unforged (elite, cf_unforged_<type>) -- body + the 14 weapons.  Driven by art/gen_forge_foes.py.

A tall armoured knight bound together from failed and broken blades: a dark soot-black core under plates that are
all blades (ribs, pauldrons, tassets, greaves, vambraces), a mantle of broken blades hanging from the shoulders, a
small blade-tip helm with one ember slit, a hot heart showing between the rib-blades.  Faces RIGHT.
Frame 176x112, floor row 106 (feet on y=106), anchor x=64.  ~76 px to the crest.
"""
import math
from forge_foes_kit import *  # noqa

W, H, FLOOR, AX = 176, 112, 106, 64
L_TH, L_SH = 19.5, 19.0
L_UA, L_FA = 14.5, 13.5
TORSO = 25.0

BASE = dict(hip=(64.0, 70.0), lean=5.0, head=0.0, nf=(73.0, 106.0), ff=(54.0, 106.0),
            na=48.0, nr=0.78, fa=95.0, fr=0.8, npref=(0.3, 1.0), fpref=(-0.4, 1.0),
            w=14.0, w2=None, two=0.0, heat=0.0, sway=(0.0, 0.0), ext=0.0, ext2=0.0, sheath=0.0, axe=0.0,
            nopen=0.0, fopen=0.0, shield=0.0, dead=0.0, eye=1.0, crouch=0.0, dark=0.0, glow=0.0, heap=0.0, flip=0.0)


def Pz(**kw):
    p = dict(BASE); p.update(kw); return p


def frame_of(hip, lean):
    """Spine vectors: up (hip -> neck) and fwd (toward the face) for a torso leaning `lean` deg forward."""
    up = dirv(-90 + lean)
    fwd = (-up[1], up[0])
    if fwd[0] < 0:
        fwd = (-fwd[0], -fwd[1])
    return up, fwd


def T(hip, lean, t, off):
    up, fwd = frame_of(hip, lean)
    return add(add(hip, mul(up, TORSO * t)), mul(fwd, off))


# ================================================================ the body parts
def groove(cv, a, b, lit_side=(0, -1), only=("I",)):
    """A seam between two plate-blades: a dark line, the pixels just above it catching the light (the blade's edge)."""
    pts = line(a, b)
    cv.decal(pts, ("I", 0), only=only)
    cv.decal([(q[0] + lit_side[0], q[1] + lit_side[1]) for q in pts], ("I", 5), only=only)


def mantle(cv, p, fi):
    """A mantle of broken blades hanging from the back of the shoulders, fanned, swaying with the body."""
    hip, lean, sw = p["hip"], p["lean"], p["sway"]
    up, fwd = frame_of(hip, lean)
    spec = [(-2.0, 0.97, 96, 34, 3.0), (-3.6, 0.95, 103, 37, 3.2), (-4.8, 0.90, 111, 35, 3.0), (-5.6, 0.84, 119, 31, 2.8),
            (-6.0, 0.76, 128, 25, 2.5), (-6.2, 0.68, 137, 18, 2.2)]
    out = set()
    for i, (off, t, ang, ln, w) in enumerate(spec):
        a0 = T(hip, lean, t, off)
        a = ang + lean * 0.7 - sw[0] * (2.4 + i * 0.4) - sw[1] * 1.0
        a += math.sin(fi * 0.9 + i * 1.3) * 0.0
        tip = add(a0, mul(dirv(a), ln * (1 - 0.2 * p["dead"])))
        m = blade(cv, a0, tip, w, 1.0, bias=-2 + (i % 2), edge=-1, tip="broken", seed=i + 3, lit=4, fuller=False)
        out |= m
    return out


def torso(cv, p, fi):
    hip, lean = p["hip"], p["lean"]
    Tt = lambda t, o: T(hip, lean, t, o)
    # soot-black core (waist / abdomen) and the cuirass of stacked blades over the chest
    core = [Tt(0.0, -3.4), Tt(0.0, 3.4), Tt(0.28, 4.0), Tt(0.5, 5.6), Tt(0.5, -5.2), Tt(0.25, -4.0)]
    cv.paint(n_plate(poly_mask(core), bevel=2.0, tilt=(0.05, -0.1), strength=1.0), "S")
    for t in (0.12, 0.27):     # two blade bands round the waist
        blade(cv, Tt(t + 0.05, -4.2), Tt(t - 0.03, 4.6), 1.5, 1.1, bias=-1, edge=-1, tip="point", lit=4, fuller=False,
              tilt=(0.0, -0.5))
    cu = [Tt(0.40, -4.8), Tt(0.42, 5.4), Tt(0.62, 8.0), Tt(0.84, 7.4), Tt(1.0, 4.0), Tt(1.04, -1.0), Tt(0.98, -5.2),
          Tt(0.80, -6.6), Tt(0.58, -6.0)]
    m = poly_mask(cu)
    cv.paint(n_plate(m, bevel=3.2, tilt=(0.18, -0.35), strength=1.25), "I")
    # the seams of the stacked blades: back-top to front-bottom, the upper blade's edge lit
    for (t0, o0, t1, o1) in ((0.96, -5.0, 0.80, 7.6), (0.82, -6.4, 0.62, 7.8), (0.66, -6.0, 0.47, 5.8)):
        groove(cv, Tt(t0, o0), Tt(t1, o1))
    # each seam ends in a blade point jutting past the chest line
    for (t0, o0) in ((0.80, 7.4), (0.62, 7.8)):
        a0 = Tt(t0, o0 - 1.5)
        blade(cv, a0, add(a0, mul(dirv(60 + lean), 4.0)), 1.2, 0.3, edge=1, tip="point", fuller=False)
    heart = Tt(0.57, 5.2)
    return heart


def tassets(cv, p, front, fi):
    hip, lean, sw = p["hip"], p["lean"], p["sway"]
    foot = p["nf" if front else "ff"]
    hp = T(hip, lean, 0.0, 1.2 if front else -1.6)
    kn = ik(hp, add(foot, (0, -1.6)), L_TH, L_SH, (1, -0.12))
    d = unit(sub(kn, hp))
    a = math.degrees(math.atan2(d[1], d[0])) - sw[0] * 1.5
    b = 0 if front else -2
    a0 = add(T(hip, lean, 0.05, 2.4 if front else -1.0), mul(perp(d), 0.0))
    m = blade(cv, a0, add(a0, mul(dirv(a - 6), L_TH * 0.82)), 3.4, 1.6, bias=b, edge=1, tip="point", lit=5 if front else 4,
              fuller=False, tilt=(0.25, -0.3))
    if front:   # a second, shorter blade behind it at the hip
        a1 = T(hip, lean, 0.04, -2.6)
        blade(cv, a1, add(a1, mul(dirv(a + 14), L_TH * 0.6)), 2.6, 1.0, bias=-1, edge=-1, tip="broken", seed=31, lit=4,
              fuller=False)
    # belt: wire binding
    if front:
        cv.paint(n_plate(poly_mask([T(hip, lean, -0.02, -3.8), T(hip, lean, -0.02, 4.0), T(hip, lean, 0.07, 4.2),
                                    T(hip, lean, 0.07, -4.0)]), bevel=0.8), "S", bias=-1)
        cv.decal(line(T(hip, lean, 0.03, -3.4), T(hip, lean, 0.03, 3.8)), ("B", 3), only="S")


def leg_full(cv, p, near):
    hip0 = p["hip"]
    hip = T(hip0, p["lean"], 0.0, 1.2 if near else -1.6)
    foot = p["nf" if near else "ff"]
    b = 0 if near else -2
    kn = leg(cv, hip, foot, L_TH, L_SH, R=(3.6, 3.1, 2.2, 2.5, 1.5), pref=(1, -0.12), mat="S", bias=b, toe=7.0)
    ank = add(foot, (0, -1.6))
    dsh = unit(sub(ank, kn))
    v = perp(dsh)
    if v[0] < 0: v = (-v[0], -v[1])      # toward the shin's front
    # greave: one long blade down the front of the shin, its point at the instep
    gv = [add(kn, mul(v, 3.0)), add(lerp(kn, ank, 0.5), mul(v, 2.8)), add(lerp(kn, ank, 0.92), mul(v, 2.2)),
          add(ank, add(mul(v, 3.4), mul(dsh, 1.6))), add(lerp(kn, ank, 0.9), mul(v, -1.4)), add(lerp(kn, ank, 0.25), mul(v, -1.8)),
          add(kn, mul(v, -1.6))]
    cv.paint(n_plate(poly_mask(gv), bevel=1.6, tilt=(0.3, -0.15), strength=1.2), "I", bias=b)
    cv.decal(line(add(kn, mul(v, 2.2)), add(lerp(kn, ank, 0.9), mul(v, 1.6))), ("I", 5 if near else 4), only="I")
    # knee cop with a short forward spike
    cv.paint(n_dome(add(kn, mul(v, 0.8)), 2.6, 2.6), "I", bias=b)
    blade(cv, add(kn, mul(v, 1.6)), add(kn, add(mul(v, 5.0), mul(dsh, -2.0))), 1.3, 0.3, bias=b, edge=0, tip="point", fuller=False)
    return kn


def shoulder_pts(p):
    hip, lean = p["hip"], p["lean"]
    return T(hip, lean, 0.9, 1.2), T(hip, lean, 0.93, -2.8)


def wrist_of(p, near):
    sn, sf = shoulder_pts(p)
    if near:
        return add(sn, mul(dirv(p["na"]), (L_UA + L_FA) * p["nr"]))
    if p["two"] > 0 and p.get("w") is not None:
        g = add(sn, mul(dirv(p["na"]), (L_UA + L_FA) * p["nr"]))
        return sub(g, mul(dirv(p["w"]), p["two"]))
    return add(sf, mul(dirv(p["fa"]), (L_UA + L_FA) * p["fr"]))


def arm_full(cv, p, near, draw_fist=True):
    sn, sf = shoulder_pts(p)
    sh = sn if near else sf
    wr = wrist_of(p, near)
    b = 0 if near else -2
    pref = p["npref" if near else "fpref"]
    el = arm(cv, sh, wr, L_UA, L_FA, pref, R=(3.2, 2.8, 2.1, 2.7, 1.7), mat="S", bias=b)
    d = unit(sub(wr, el))
    v = perp(d)
    side = 1 if v[1] < 0 else -1      # the upper side of the forearm
    vu = mul(v, side)
    # rerebrace: a plate down the upper arm (keeps the arm from reading as a dark pipe across the chest)
    du = unit(sub(el, sh)); pu = perp(du)
    if pu[0] < 0: pu = (-pu[0], -pu[1])
    rb = [add(lerp(sh, el, 0.15), mul(pu, 3.0)), add(lerp(sh, el, 0.82), mul(pu, 2.6)), add(lerp(sh, el, 0.95), mul(pu, 0.0)),
          add(lerp(sh, el, 0.82), mul(pu, -2.6)), add(lerp(sh, el, 0.15), mul(pu, -3.0))]
    cv.paint(n_plate(poly_mask(rb), bevel=1.6, tilt=(0.1, -0.25), strength=1.2), "I", bias=b - 1)
    cv.decal(line(add(lerp(sh, el, 0.55), mul(pu, 2.8)), add(lerp(sh, el, 0.55), mul(pu, -2.8))), ("I", 0), only="I")
    # vambrace: a broad plate over the forearm, swelling below the elbow, a blade spur jutting past the elbow
    va = [add(lerp(el, wr, 0.05), mul(vu, 3.2)), add(lerp(el, wr, 0.35), mul(vu, 3.4)), add(lerp(el, wr, 0.95), mul(vu, 2.2)),
          add(lerp(el, wr, 0.95), mul(vu, -1.8)), add(lerp(el, wr, 0.3), mul(vu, -2.6)), add(lerp(el, wr, 0.02), mul(vu, -2.2))]
    cv.paint(n_plate(poly_mask(va), bevel=1.6, tilt=(-0.1 + vu[0] * 0.4, -0.2 + vu[1] * 0.4), strength=1.2), "I", bias=b)
    cv.decal(line(add(lerp(el, wr, 0.1), mul(vu, 2.6)), add(lerp(el, wr, 0.9), mul(vu, 1.6))), ("I", 5 if near else 4), only="I")
    blade(cv, add(el, mul(vu, 1.2)), add(sub(el, mul(d, 5.5)), mul(vu, 1.8)), 1.6, 0.3, bias=b, edge=side, tip="point",
          lit=5 if near else 4, fuller=False)
    c = None
    if draw_fist:
        c = fist(cv, wr, d, 2.1, "I", bias=b, open_=p["nopen" if near else "fopen"])
    return el, wr, c


def pauldron(cv, p, near):
    sn, sf = shoulder_pts(p)
    sh = sn if near else sf
    lean, sw = p["lean"], p["sway"]
    b = 0 if near else -2
    R_ = lambda q: add(sh, rot(q, lean * 0.5 - sw[0] * 1.0))
    poly = [R_(q) for q in ((4.0, 2.4), (4.6, -1.2), (2.0, -3.8), (-3.0, -4.6), (-9.0, -6.6), (-6.0, -2.8), (-8.4, -0.6),
                            (-5.0, 1.8), (-6.4, 4.6), (-2.2, 4.4), (1.4, 4.8))]
    m = poly_mask(poly)
    cv.paint(n_plate(m, bevel=2.6, tilt=(-0.05, -0.4), strength=1.3), "I", bias=b)
    groove(cv, R_((3.4, -0.4)), R_((-5.8, -2.6)))
    groove(cv, R_((3.0, 2.2)), R_((-4.8, 1.8)))
    return m


def head(cv, p, fi):
    hip, lean = p["hip"], p["lean"]
    neck = T(hip, lean, 1.0, 0.8)
    tilt = lean * 0.4 + p["head"]
    hd = add(neck, rot((0.8, -5.2), tilt))
    R_ = lambda q: add(hd, rot(q, tilt))
    # crown: broken blades swept back from the crown of the helm (behind the helm)
    for i, (o, a, ln, w) in enumerate((((-2.0, -1.6), -172, 8.5, 1.6), ((-1.4, -2.8), -152, 11.0, 1.8), ((0.0, -3.2), -128, 8.0, 1.5),
                                       ((1.2, -3.0), -104, 5.0, 1.2))):
        a0 = R_(o)
        blade(cv, a0, add(a0, mul(dirv(a + tilt - p["sway"][0] * 1.5), ln)), w, 0.4, bias=-1, edge=-1,
              tip="broken" if i in (0, 2) else "point", seed=40 + i, lit=5, fuller=False)
    # gorget
    blade(cv, T(hip, lean, 0.86, -3.0), add(neck, rot((3.6, 0.6), tilt)), 2.4, 1.4, bias=-1, edge=-1, tip="point", fuller=False)
    # helm: a narrow blade-tip, its point forward like a beak; a slit with one ember
    helm = [R_(q) for q in ((-3.2, 1.6), (-3.0, -2.0), (-1.0, -3.6), (2.2, -3.2), (4.6, -1.2), (6.6, 1.2), (3.6, 2.4),
                            (1.0, 3.8), (-1.8, 3.6))]
    cv.paint(n_plate(poly_mask(helm), bevel=1.8, tilt=(0.15, -0.35), strength=1.3), "I")
    cv.decal(line(R_((-2.0, -2.6)), R_((4.6, -1.0))), ("I", 5), only="I")
    cv.decal(line(R_((0.6, -0.4)), R_((5.2, 0.6))), ("I", 0), only="I")
    eye = [ipt(R_((2.2, -0.2))), ipt(R_((3.2, 0.0))), ipt(R_((4.2, 0.3)))]
    return eye, hd


# ================================================================ the weapons
WCOL = "I"


def heat_tint(cv, m, heat, base=None, tip=None):
    """Heated metal: a smooth glow over the part, hotter toward the base of a blade (no speckle)."""
    for q in m:
        t = 0.5
        if base is not None and tip is not None:
            L = math.hypot(tip[0] - base[0], tip[1] - base[1]) or 1
            t = 1 - ((q[0] - base[0]) * (tip[0] - base[0]) + (q[1] - base[1]) * (tip[1] - base[1])) / (L * L)
        k = max(0.0, min(1.0, heat * (0.55 + 0.45 * t)))
        cv.glow([q], heat_col(0.15 + 0.55 * k), int(70 + 150 * k))


def hot_crack(cv, a, b, heat):
    cv.glow(line(a, b), heat_col(0.35 + 0.4 * heat), 255)


def w_sword(cv, grip, ang, ln=30.0, width=2.4, guard=4.5, pommel=True, heat=0.0, bias=0, crack=0.55, curve=0.0):
    d = dirv(ang); v = perp(d)
    hb = sub(grip, mul(d, 5.0))
    limb(cv, [hb, add(grip, mul(d, 2.0))], [1.1, 1.0], WCOL, bias=bias, ao=0)
    if pommel:
        cv.paint(n_dome(sub(hb, mul(d, 0.8)), 1.5, 1.5), "I", bias=bias)
    gc = add(grip, mul(d, 2.6))
    if guard:
        blade(cv, add(gc, mul(v, guard)), add(gc, mul(v, -guard)), 1.0, 0.8, bias=bias, edge=0, tip="flat", fuller=False)
    base = add(grip, mul(d, 3.4))
    tip = add(grip, mul(d, ln))
    if curve:
        pts = [add(lerp(base, tip, t), mul(v, -curve * math.sin(math.pi * t * 0.9) * t)) for t in (i / 12 for i in range(13))]
        m = set()
        for a_, b_ in zip(pts, pts[1:]):
            pass
        sp = pts
        ws = [width * min(1.0, (1 - i / 12) * 4 + 0.1) for i in range(13)]
        m = poly_mask(ribbon(sp, ws))
        cv.paint(n_plate(m, bevel=0.9, tilt=(-0.35 * v[0] - 0.1, -0.35 * v[1] - 0.3), strength=1.3), WCOL, bias=bias, iline=True)
        cv.decal([ipt(add(q, mul(v, -(w_ - 0.6)))) for q, w_ in zip(sp, ws) if ipt(add(q, mul(v, -(w_ - 0.6)))) in m], (WCOL, 5), only=WCOL)
        tip = sp[-1]
    else:
        m = blade(cv, base, tip, width, width * 0.55, bias=bias, edge=1, tip="point", lit=5)
    if crack and heat >= 0:
        q = lerp(base, tip, crack)
        hot_crack(cv, add(q, mul(v, -width * 0.8)), add(q, mul(v, width * 0.6)), heat)
    if heat > 0.05:
        heat_tint(cv, m, heat, base, tip)
    return dict(tip=tip, base=base, m=m)


def w_haft(cv, a, b, r=1.1, bias=0):
    limb(cv, [a, b], [r, r * 0.95], WCOL, bias=bias, ao=0)
    for t in (0.0, 1.0):
        cv.paint(n_dome(lerp(a, b, t), r + 0.5, r + 0.5), "I", bias=bias)


def weapon(cv, p, wt, wr_n, wr_f, info, fi):
    """Draws the rolled weapon for the pose.  Fills info['hit'] (damaging pixels) and info['tip']."""
    ang = p["w"]
    d = dirv(ang)
    heat = p["heat"]
    hit = set()
    if wt == "longsword":
        r = w_sword(cv, wr_n, ang, 31, 2.4, 4.0, heat=heat)
        hit |= r["m"]; info["tip"] = r["tip"]
    elif wt == "katana":
        if p["sheath"] > 0.5:
            # sheathed: the scabbard at the hip, the hand on the hilt
            sc0 = add(wr_n, mul(dirv(ang), -4.0))
            sc1 = add(wr_n, mul(dirv(ang), 30.0))
            blade(cv, add(wr_n, mul(dirv(ang), 3.0)), sc1, 1.8, 1.4, mat="S", bias=-1, edge=1, tip="flat", fuller=False)
            limb(cv, [sc0, add(wr_n, mul(dirv(ang), 2.5))], [1.0, 1.0], WCOL, ao=0)
            info["tip"] = None      # no smear out of the scabbard
        else:
            r = w_sword(cv, wr_n, ang, 31, 1.9, 2.0, heat=heat, curve=2.6, pommel=False)
            hit |= r["m"]; info["tip"] = r["tip"]
    elif wt == "greatsword":
        r = w_sword(cv, wr_n, ang, 44, 3.4, 6.0, heat=heat, crack=0.45)
        hit |= r["m"]; info["tip"] = r["tip"]
    elif wt == "maul":
        butt = sub(wr_n, mul(d, 8.0)); hd = add(wr_n, mul(d, 26.0))
        w_haft(cv, butt, hd, 1.2)
        v = perp(d)
        head_poly = [add(hd, add(mul(v, 5.2), mul(d, 4.6))), add(hd, add(mul(v, 5.6), mul(d, -4.2))),
                     add(hd, add(mul(v, -5.0), mul(d, -4.6))), add(hd, add(mul(v, -5.4), mul(d, 4.2)))]
        m = poly_mask(head_poly)
        cv.paint(n_plate(m, bevel=2.2, tilt=(-0.15, -0.3), strength=1.5), "I", iline=True)
        cv.decal(line(add(hd, add(mul(v, 5.0), mul(d, 3.4))), add(hd, add(mul(v, 5.0), mul(d, -3.4)))), ("I", 5), only="I")
        hot_crack(cv, add(hd, add(mul(v, -2.0), mul(d, 4.0))), add(hd, add(mul(v, 1.0), mul(d, -1.0))), heat)
        if heat > 0.05:
            heat_tint(cv, m, heat)
        hit |= m; info["tip"] = add(hd, mul(v, 5.0))
    elif wt == "sns":
        r = w_sword(cv, wr_n, ang, 25, 2.2, 3.4, heat=heat)
        hit |= r["m"]; info["tip"] = r["tip"]
    elif wt == "dual":
        r = w_sword(cv, wr_n, ang, 19, 1.8, 2.4, heat=heat, crack=0.6)
        hit |= r["m"]; info["tip"] = r["tip"]
    elif wt == "spear":
        butt = sub(wr_n, mul(d, 18.0)); tipb = add(wr_n, mul(d, 36.0))
        w_haft(cv, butt, tipb, 1.0)
        m = blade(cv, sub(tipb, mul(d, 1.0)), add(tipb, mul(d, 10.0)), 2.0, 0.4, edge=1, tip="point", lit=5)
        hot_crack(cv, add(tipb, mul(perp(d), -1.2)), add(tipb, add(mul(perp(d), 1.0), mul(d, 2.0))), heat)
        hit |= m | {ipt(lerp(wr_n, tipb, t / 10)) for t in range(6, 11)}
        info["tip"] = add(tipb, mul(d, 10.0))
    elif wt == "staff":
        a = sub(wr_n, mul(d, 24.0)); b = add(wr_n, mul(d, 26.0))
        w_haft(cv, a, b, 1.1)
        for e in (a, b):
            blade(cv, e, add(e, mul(sub(e, wr_n), 0.16)), 1.4, 0.4, edge=0, tip="point", fuller=False)
        hit |= {ipt(lerp(a, b, t / 40)) for t in range(41)}
        info["tip"] = b; info["tip2"] = a
    elif wt == "whip":
        # a chain of blade-links from the hand along a curve: ext = how far it has lashed (0 coiled .. 1 full)
        L = 14 + 66 * p["ext"]
        bend = p["ext2"]
        pts = [wr_n]
        a = ang
        for i in range(24):
            a += bend * (1 - i / 24) * 2.2
            pts.append(add(pts[-1], mul(dirv(a), L / 24)))
        for i, (q0, q1) in enumerate(zip(pts, pts[1:])):
            cv.paint({q: (0.2, -0.5, 0.85) for q in line(q0, q1)}, "I", bias=0 if i % 3 else 1, ao=0)
            if i % 3 == 0:
                cv.paint(n_dome(q1, 0.9, 0.9), "I")
        tipb = pts[-1]
        m = blade(cv, pts[-2], add(tipb, mul(unit(sub(tipb, pts[-2])), 4.0)), 1.4, 0.3, edge=1, tip="point")
        hit |= {ipt(q) for q in pts[int(len(pts) * 0.3):]} | m
        info["tip"] = tipb
        limb(cv, [sub(wr_n, mul(d, 3.0)), add(wr_n, mul(d, 2.0))], [1.2, 1.1], WCOL, ao=0)
    elif wt == "saxe":
        if p["axe"] > 0.5:
            butt = sub(wr_n, mul(d, 6.0)); hd = add(wr_n, mul(d, 30.0))
            w_haft(cv, butt, hd, 1.2)
            v = perp(d)
            ax = [add(hd, mul(v, 1.0)), add(add(hd, mul(d, 6.0)), mul(v, 2.0)), add(add(hd, mul(d, 8.0)), mul(v, 10.0)),
                  add(add(hd, mul(d, -8.0)), mul(v, 11.0)), add(add(hd, mul(d, -5.0)), mul(v, 2.0))]
            m = poly_mask(ax)
            cv.paint(n_plate(m, bevel=1.8, tilt=(-0.2, -0.3), strength=1.4), "I", iline=True)
            edge = line(add(add(hd, mul(d, 8.0)), mul(v, 10.0)), add(add(hd, mul(d, -8.0)), mul(v, 11.0)))
            cv.glow(edge, heat_col(0.5 + 0.4 * heat))
            # teeth
            for k in range(0, len(edge), 3):
                cv.glow([add(edge[k], (0, 0))], "E6")
            hit |= m; info["tip"] = add(hd, mul(v, 10.0))
        else:
            r = w_sword(cv, wr_n, ang, 30, 2.8, 3.0, heat=heat, crack=0.35)
            hit |= r["m"]; info["tip"] = r["tip"]
            # the folded axe-head along the spine of the blade
            v = perp(d)
            blade(cv, add(wr_n, add(mul(d, 6.0), mul(v, -2.6))), add(wr_n, add(mul(d, 20.0), mul(v, -2.6))), 1.4, 1.0, bias=-1,
                  edge=0, tip="flat", fuller=False)
    elif wt == "bow":
        # the bow in the FAR hand (front), the near hand draws the string; ext = draw (0..1)
        bc = wr_f
        da = p["w2"] if p["w2"] is not None else -90.0
        ud = dirv(da)        # along the bow (up)
        fw = perp(ud)        # facing direction of the belly
        if fw[0] < 0: fw = (-fw[0], -fw[1])
        top = add(bc, add(mul(ud, 15.0), mul(fw, -2.0)))
        bot = add(bc, add(mul(ud, -15.0), mul(fw, -2.0)))
        limb_pts = qbez(top, add(bc, mul(fw, 4.5)), bot, 20)
        tips = []
        for q0, q1 in zip(limb_pts, limb_pts[1:]):
            cv.paint({q: (0.2, -0.4, 0.88) for q in line(q0, q1)}, "I", ao=0)
        for e, s in ((top, 1), (bot, -1)):
            rec = add(e, add(mul(ud, s * 2.4), mul(fw, 1.6)))
            cv.paint({q: (0.2, -0.4, 0.88) for q in line(e, rec)}, "I", ao=0)
            tips.append(rec)
        cv.paint(n_capsule(add(bc, mul(ud, 1.6)), add(bc, mul(ud, -1.6)), 1.3), "I")
        nock = wr_n if p["ext"] > 0.05 else lerp(top, bot, 0.5)
        for e in (top, bot):
            cv.glow(line(e, nock), "Q3", 220)
        if p["ext2"] > 0.5:      # an arrow on the string
            ad = unit(sub(bc, nock)) if math.hypot(*sub(bc, nock)) > 1 else fw
            atip = add(bc, mul(ad, 9.0))
            cv.paint({q: (0.2, -0.4, 0.88) for q in line(nock, atip)}, "I", ao=0)
            cv.glow([ipt(atip), ipt(sub(atip, ad))], heat_col(0.5 + 0.4 * heat))
            info["tip"] = atip
        else:
            info["tip"] = add(bc, mul(fw, 6.0))
        hit |= {ipt(q) for q in limb_pts}
    elif wt == "fist":
        # no held weapon: blade-knuckles over both gauntlets (drawn by the hands), hits = the fists
        info["tip"] = add(wr_n, mul(d, 4.0))
    elif wt == "scythe":
        butt = sub(wr_n, mul(d, 14.0)); top = add(wr_n, mul(d, 30.0))
        w_haft(cv, butt, top, 1.0)
        v = perp(d)
        bd = dirv(ang - 90 + 180 * p["flip"])      # the blade's direction off the haft (flip turns it over)
        sp = []
        for i in range(15):
            t = i / 14
            sp.append(add(top, add(mul(bd, 26.0 * t), mul(d, -10.0 * t * t + 2.0 * t))))
        ws = [2.6 * (1 - t) ** 0.7 + 0.3 for t in (i / 14 for i in range(15))]
        m = poly_mask(ribbon(sp, ws))
        cv.paint(n_plate(m, bevel=1.0, tilt=(-0.3, -0.3), strength=1.4), "I", iline=True)
        cv.decal([ipt(add(q, mul(perp(unit(sub(sp[min(14, k + 1)], sp[max(0, k - 1)]))), -(w_ - 0.6))))
                  for k, (q, w_) in enumerate(zip(sp, ws))], ("I", 5), only="I")
        hot_crack(cv, sp[5], add(sp[5], mul(d, 1.6)), heat)
        hit |= m; info["tip"] = sp[-1]; info["tip2"] = top
    elif wt == "bell":
        hb = add(wr_n, mul(d, 14.0))
        w_haft(cv, sub(wr_n, mul(d, 6.0)), hb, 1.1)
        # chain + the bell hanging off the haft end along the swing
        ba = p["w2"] if p["w2"] is not None else ang
        bd = dirv(ba)
        c1 = add(hb, mul(bd, 5.0))
        cv.paint({q: (0.2, -0.4, 0.88) for q in line(hb, c1)}, "I", ao=0)
        bv = perp(bd)
        bell = [add(c1, mul(bv, 2.2)), add(c1, add(mul(bd, 2.0), mul(bv, 3.6))), add(c1, add(mul(bd, 11.0), mul(bv, 6.2))),
                add(c1, add(mul(bd, 12.2), mul(bv, 0.0))), add(c1, add(mul(bd, 11.0), mul(bv, -6.2))),
                add(c1, add(mul(bd, 2.0), mul(bv, -3.6))), add(c1, mul(bv, -2.2))]
        m = poly_mask(bell)
        cv.paint(n_plate(m, bevel=2.2, tilt=(-0.2, -0.3), strength=1.5), "I", iline=True)
        cv.decal(line(add(c1, add(mul(bd, 9.6), mul(bv, 5.4))), add(c1, add(mul(bd, 9.6), mul(bv, -5.4)))), ("B", 3), only="I")
        hot_crack(cv, add(c1, add(mul(bd, 4.0), mul(bv, 2.0))), add(c1, add(mul(bd, 7.0), mul(bv, 0.5))), heat)
        if heat > 0.05:
            heat_tint(cv, m, heat)
        hit |= m; info["tip"] = add(c1, mul(bd, 12.0))
    info["hit"] = hit


def offhand(cv, p, wt, wr_f, fi):
    """What the far hand holds (drawn behind the body): the shield, the second blade, the katana's scabbard."""
    hit = set()
    if wt == "sns":
        d = dirv(p["w2"] if p["w2"] is not None else -80.0)
        v = perp(d)
        c = add(wr_f, mul(v, -1.0))
        k = 1.0 + 0.0 * p["shield"]
        sh = [add(c, add(mul(d, 9.0 * k), mul(v, 4.4))), add(c, add(mul(d, 9.5 * k), mul(v, -4.0))),
              add(c, add(mul(d, -2.0), mul(v, -5.0))), add(c, add(mul(d, -10.0 * k), mul(v, 0.0))),
              add(c, add(mul(d, -2.0), mul(v, 5.2)))]
        m = poly_mask(sh)
        cv.paint(n_plate(m, bevel=2.0, tilt=(0.2, -0.3), strength=1.4), "I", bias=-1, iline=True)
        cv.decal(polyline([add(c, add(mul(d, 7.0), mul(v, 0.0))), add(c, add(mul(d, -7.0), mul(v, 0.2)))]), ("I", 4), only="I")
        cv.glow([ipt(c)], "E3")
        hit |= m
    elif wt == "dual":
        r = w_sword(cv, wr_f, p["w2"] if p["w2"] is not None else 70.0, 19, 1.8, 2.4, heat=p["heat"], bias=-1, crack=0.4)
        hit |= r["m"]
    return hit


# ================================================================ the figure
def heap(cv, p, wt, fi):
    """The binding fails: a dozen broken blades fall out of the body into a heap; the helm rolls; the heart dims."""
    k = p["heap"]
    info = {"hit": set(), "tip": (AX + 20, FLOOR - 4), "heart": (AX, FLOOR - 3), "head": (AX + 14, FLOOR - 3)}
    for i in range(20):
        x0 = AX - 10 + 22 * hash01(i, 1, 77); y0 = 54 + 44 * hash01(i, 2, 77)
        x1 = AX - 22 + 48 * hash01(i, 3, 77); y1 = FLOOR - 1 - 7 * hash01(i, 4, 77) * (1 - abs(hash01(i, 3, 77) - 0.5) * 1.6)
        e = min(1.0, k * (1.2 + 0.6 * hash01(i, 5, 77)))
        e = e * e
        c = (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
        a = (60 + 200 * hash01(i, 6, 77)) * (1 - e) + (165 + 30 * hash01(i, 7, 77) if i % 2 else 15 - 32 * hash01(i, 7, 77)) * e
        ln = 8 + 10 * hash01(i, 8, 77)
        d = dirv(a)
        blade(cv, sub(c, mul(d, ln / 2)), add(c, mul(d, ln / 2)), 1.6 + 0.8 * hash01(i, 9, 77), 0.5, bias=-1 + (i % 2), edge=1,
              tip="broken" if i % 3 else "point", seed=60 + i, lit=4, fuller=False)
    hc = (AX + 6 + 10 * k, 66 + (FLOOR - 70) * min(1.0, k * 1.3))
    helm = [add(hc, rot(q, 90 * k)) for q in ((-3.2, 1.6), (-3.0, -2.0), (-1.0, -3.6), (2.2, -3.2), (4.6, -1.2), (6.6, 1.2),
                                                (3.6, 2.4), (1.0, 3.8), (-1.8, 3.6))]
    cv.paint(n_plate(poly_mask(helm), bevel=1.8, tilt=(0.15, -0.35), strength=1.3), "I")
    if k < 0.9:
        cv.glow([ipt(add(hc, rot((3.2, 0.0), 90 * k)))], "E3")
    ember = (AX + 2, FLOOR - 2)
    cv.glow([ipt(ember)], "E3" if k < 0.8 else "E2")
    return info


REACH = {"longsword": 31, "katana": 31, "greatsword": 44, "maul": 32, "sns": 25, "dual": 19, "spear": 46, "staff": 28,
         "whip": 0, "saxe": 31, "bow": 0, "fist": 0, "scythe": 30, "bell": 30}


def floor_clamp(p, wt):
    """A swing that would drive the weapon through the floor ends with it resting on the floor instead."""
    L = REACH.get(wt, 0) + (10 if (wt == "saxe" and p["axe"] > 0.5) else 0)
    if not L or p["w"] is None:
        return
    g = wrist_of(p, True)
    room = FLOOR - 1.5 - g[1]
    a = p["w"] % 360
    if a > 180: a -= 360
    if 0 < a < 180 and math.sin(math.radians(a)) * L > room:
        s_ = max(-1.0, min(1.0, room / L))
        base = math.degrees(math.asin(s_))
        p["w"] = base if a <= 90 else 180 - base


def draw(p, wt, fi=0, active=False):
    cv = Canvas(W, H)
    p = dict(p)
    floor_clamp(p, wt)
    if p["heap"] > 0:
        k = p["heap"]
        if k < 0.75:      # the body comes apart in chunks while the blades fall out of it
            q = dict(p); q["heap"] = 0.0; q["glow"] = -1.0; q["eye"] = 0.0
            cv2, _ = draw(q, wt, fi)
            gone = min(1.0, k * 1.5)
            cv2.px = {pt: e for pt, e in cv2.px.items() if hash01(pt[0] // 2, pt[1] // 2, 31) > gone or pt[1] > FLOOR - 3 * (1 - gone)}
            cv2.fx = {}
            info = heap(cv2, p, wt, fi)
            return cv2, info
        return cv, heap(cv, p, wt, fi)
    info = {"hit": set()}
    hip, lean = p["hip"], p["lean"]
    heart = T(hip, lean, 0.56, 3.2)
    cv.lights.append((heart, 9.0, 0.16 + 0.12 * max(0.0, p["glow"])))
    if p["heat"] > 0.2:
        cv.lights.append((wrist_of(p, True), 18.0, 0.35 * p["heat"]))
    mantle(cv, p, fi)
    # the far arm + whatever it holds, behind the body
    wr_n = wrist_of(p, True)
    wr_f = wrist_of(p, False)
    two = p["two"] > 0
    arm_full(cv, p, False, draw_fist=not two)
    off = offhand(cv, p, wt, wr_f, fi)
    pauldron(cv, p, False)
    leg_full(cv, p, False)
    tassets(cv, p, False, fi)
    torso(cv, p, fi)
    leg_full(cv, p, True)
    tassets(cv, p, True, fi)
    eye, hd = head(cv, p, fi)
    under = {k: id(v) for k, v in cv.px.items()}      # what the arm / weapon in front may cover
    if wt == "bow":
        weapon(cv, p, wt, wr_n, wr_f, info, fi)
        fist(cv, wr_f, unit(sub(wr_f, shoulder_pts(p)[1])), 2.0, "I", bias=0)
        pauldron(cv, p, True)
        arm_full(cv, p, True)
    else:
        pauldron(cv, p, True)
        el, wr, _ = arm_full(cv, p, True, draw_fist=False)
        weapon(cv, p, wt, wr_n, wr_f, info, fi)
        fd = unit(sub(wr_n, el))
        if wt == "fist":
            c = fist(cv, wr_n, fd, 2.5, "I", bias=0)
            for k in (-1, 1):
                blade(cv, add(c, mul(perp(fd), k * 1.0)), add(c, add(mul(fd, 4.5), mul(perp(fd), k * 1.4))), 0.9, 0.3, edge=0)
            info["hit"] |= {q for q in mask_disc(add(c, mul(fd, 2.0)), 4.0)}
        else:
            fist(cv, wr_n, dirv(p["w"] + 90 * (1 if wt not in ("staff", "spear") else 0.0)) if False else fd, 2.0, "I", bias=0)
        if two:
            fist(cv, wr_f, unit(sub(wr_f, shoulder_pts(p)[1])), 2.0, "I", bias=0)
    if wt == "fist":
        # the far fist too (it punches in the combos)
        sf = shoulder_pts(p)[1]
        fd2 = unit(sub(wr_f, sf))
        c2 = fist(cv, wr_f, fd2, 2.4, "I", bias=-1)
        info["hit"] |= {q for q in mask_disc(add(c2, mul(fd2, 2.0)), 3.6)} if p["fr"] > 0.9 else set()
    info["hit"] |= off if wt == "dual" else set()
    info["shield"] = off if wt == "sns" else set()
    # emissives: the heart between the ribs, the eye slit
    hk = 0.6 + 0.4 * p["glow"]
    vis = lambda pts: [q for q in pts if q in cv.px and under.get(q) == id(cv.px[q])]
    cv.glow(vis([ipt(heart), ipt(add(heart, (1, 0))), ipt(add(heart, (0, 1)))]), "E5" if hk > 0.8 else "E4")
    cv.glow(vis([ipt(add(heart, (-1, 1))), ipt(add(heart, (1, 1)))]), "E3", 200)
    if p["eye"] > 0:
        cv.glow(vis(eye), "E5" if p["eye"] > 0.7 else "E3")
        cv.glow(vis([eye[-1]]), "E6")
    info["heart"] = heart
    info["head"] = hd
    info["foot"] = p["nf"]
    info["body"] = {ipt(T(hip, lean, t / 8, o)) for t in range(0, 9) for o in range(-5, 9)} | set(info.get("shield", set()))
    return cv, info


def render(p, wt, fi=0, active=False, smear_from=None):
    cv, info = draw(p, wt, fi, active)
    img = cv.render(ref_y=60, ydark=0.006)
    return img, info
