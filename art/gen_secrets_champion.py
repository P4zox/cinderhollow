#!/usr/bin/env python3
"""The Hollow Champion (agent X mini-boss, R4 gauntlet) -- a tall, gaunt hollowed duelist with twin sabres.

    python3 art/gen_secrets_champion.py              full build: champion + champion_p2 (+ assets/champion_meta.json)
    python3 art/gen_secrets_champion.py --preview    previews + meta only
    python3 art/gen_secrets_champion.py --only flurry --preview

Frame 96x72, faces RIGHT, feet on the bottom row, anchor x = 40. ~54px tall: blackened-bronze half plate over a lean frame,
a narrow helm with one swept-back blade crest, a long tattered crimson waist-sash, two curved bone-white sabres.
Phase 2 (champion_p2): the blades burn (ember edges), the visor glows, embers rise off the sash.
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, basis, add, sub, lerp, ip, line, polyline, bezier,  # noqa: E402
                       hash01, n_plate, leg, arm, swept, thrust_lines, dirv)

W, H = 96, 72
K.setup(W, H)
import secrets_kit as S  # noqa: E402
from secrets_kit import tube, rag_hem, star, flat_arc, bbox  # noqa: E402

FLOOR = H - 1
AX = 40
BUILD = "--preview" not in sys.argv

LAYERS = ["FXBack", "SashBack", "BladeBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Sash", "Head", "BladeFront", "FrontArm", "FX"]
FXL = {"FXBack", "FX"}

NEU = dict(P=(39.5, 47.0), C=(40.8, 34.4), Hd=(42.6, 24.2), hup=(0.18, -1), fb=(32.0, 71), ff=(48.0, 71), kb=None, kf=None,
           hf=(50.0, 44.0), wf=24, hb=(31.0, 40.0), wb=-150, smear=None, smear2=None, flat=None, thrust=None, eye=1, wind=0.0,
           lift=0.0, dust=0, rot=0.0, piv=(40, 44), dissolve=0.0, glint=None, kneel=False, bl="BladeBack")


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def M(*ds, **kw):
    d = dict(NEU)
    for x in ds:
        d.update(x)
    d.update(kw)
    return d


def up(p, dy, dx=0.0):
    q = dict(p)
    for k in ("P", "C", "Hd", "fb", "ff", "kb", "kf", "hf", "hb"):
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] - dy)
    return q


GUARD = dict(P=(39.0, 48.4), C=(40.4, 35.8), Hd=(42.4, 25.6), hup=(0.2, -1), fb=(30.0, 71), ff=(48.5, 71),
             hf=(51.0, 45.0), wf=18, hb=(33.0, 39.0), wb=-152)
SAB = 20.0          # sabre length (tip distance from the grip)


def sabre_px(grip, ang, phase, length=SAB, curve=2.6):
    """Curved single-edged sabre: bone-white blade (ember-edged in phase 2), gold crossguard, dark grip."""
    ca, sa = dirv(ang)
    vdir = (-sa, ca)
    lit = -(vdir[0] * K.LIGHT[0] + vdir[1] * K.LIGHT[1]) > 0
    out, blade = {}, set()
    R_ = length + 4
    for y in range(int(grip[1] - R_), int(grip[1] + R_) + 1):
        for x in range(int(grip[0] - R_), int(grip[0] + R_) + 1):
            dx, dy = x + .5 - grip[0], y + .5 - grip[1]
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            c = None
            if -3.6 <= u <= 1.0 and abs(v) <= 0.8:
                c = "L1" if int(u) % 2 else "L2"
            if abs(u + 4.2) <= 0.8 and abs(v) <= 1.0:
                c = "G3"
            if 1.0 <= u <= 2.0 and abs(v) <= 2.4:
                c = "G4" if v * (1 if lit else -1) > 0 else "G2"
            if 2.0 < u <= length:
                t = (u - 2.0) / (length - 2.0)
                cv = curve * t * t                          # the blade sweeps back toward the spine
                w_e, w_s = 1.25 * (1 - t ** 3) + 0.2, 0.75 * (1 - t ** 2) + 0.15
                vv = v + cv
                if -w_s <= vv <= w_e:
                    edge = vv > w_e * 0.2
                    if phase == 2:
                        c = ("X4" if t > 0.5 else "X3") if edge else ("U3" if vv < -0.3 else "X1")
                    else:
                        c = ("N5" if lit else "N4") if edge else ("N2" if vv < -0.3 else "N3")
                    blade.add((x, y))
            if c:
                out[(x, y)] = c
    tipv = (grip[0] + ca * length - sa * (-curve), grip[1] + sa * length + ca * (-curve))
    return out, blade, tipv


def draw(p, fi, sw, phase):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    shF, shB = F(2.4, -ln + 2.0), F(-3.0, -ln + 2.2)
    hB, hF = F(-2.2, 1.0), F(2.4, 1.0)
    info = {"hit": set()}
    sx = sw - p["wind"] - (1.0 if phase == 2 else 0)

    # ---------------- sabres
    blades = set()
    for which, hnd, ang, layer in (("f", p["hf"], p["wf"], "BladeFront"), ("b", p["hb"], p["wb"], p["bl"])):
        g0, a0 = R.T(hnd), R.A(ang)
        pix, bl, tip = sabre_px(g0, a0, phase)
        pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
        Ls[layer].fixed(pix)
        blades |= {q for q in bl if q[1] <= FLOOR}
        info["tip_" + which] = tip
        info["g_" + which] = g0
        info["a_" + which] = a0
    info["hit"] |= blades

    # ---------------- sash: long tattered crimson tails from the waist, streaming back
    SB, SF = Ls["SashBack"], Ls["Sash"]
    knot = F(-4.6, -0.2)
    for k, (L0, off) in enumerate(((22.0, 0.0), (17.0, 1.6), (12.0, -1.2))):
        a_ = add(knot, (0, off * 0.4))
        tl = bezier(a_, add(a_, (-4 - sx * 0.8, 3 + k)), add(a_, (-10 - sx * 1.8, 6 + k * 1.5 - p["lift"] * 0.2)),
                    add(a_, (-L0 * 0.8 - sx * 2.6, L0 * 0.45 - p["lift"] * 0.5 + k)), n=10)
        m = tube(R, SB, tl, 1.25 - k * 0.15, 0.5, "C", bias=-1 if k else 0)
        SB.decal([q for q in m if hash01(q[0], q[1], 41 + k) < 0.12], ("C", 0))
        if phase == 2 and k == 0:
            e = R.pt(tl[-1])
            FX.put([e], "X3")
    band = [F(-5.4, -2.6), F(5.4, -2.6), F(5.6, 0.8), F(-5.6, 0.8)]
    R.plate(SF, band, "C", bevel=1.0, tilt=(0, -0.2))
    R.dline(SF, F(-5.4, -1.0), F(5.4, -1.0), ("C", 1))
    # front apron: a hanging strip of crimson cloth over the front thigh
    ap = [F(1.4, 0.2), F(5.2, 0.2), add(F(5.6, 9.0), (sx * 0.2, 0)), add(F(3.6, 11.4), (sx * 0.3, 0)), add(F(1.2, 9.6), (sx * 0.4, 0))]
    am = R.mask(ap)
    SF.paint(n_plate(am, 1.2, (-0.1, 0), 1.0, fold=lambda x, y: (0.5 * math.sin(x * 1.4), 0)), "C", bias=0, ao=1)

    # ---------------- legs: dark leather, bronze greaves
    kn_f = kn_b = None
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(R, Ls[nm], hip, ft, 11.8, 11.8, 2.6, 2.0, "L", bias=bias, knee=kn, boot="U", flen=4.2, heel=2.0, boot_h=3.0, pref=(1, -0.1))
        R.dome(Ls[nm], add(k, (0.6, 0)), 2.2, 2.0, "U", bias=bias)
        R.cap(Ls[nm], lerp(k, ft, 0.2), lerp(k, (ft[0], ft[1] - 3), 0.9), 2.1, 1.8, "U", bias, ao=0)
        R.decal(Ls[nm], [add(k, (1.0, -0.2))], ("G", 3 + bias))
        if nm == "FrontLeg":
            kn_f = k
        else:
            kn_b = k

    # ---------------- torso: lean, blackened bronze half-plate; hollow ribs showing at the flank
    Bd = Ls["Body"]
    torso = [F(-4.4, -1.0), F(-5.6, -ln + 4.0), F(-4.2, -ln - 0.6), F(2.4, -ln - 1.8), F(5.4, -ln + 1.0), F(5.0, -ln + 7.0),
             F(3.6, -1.0)]
    tm = R.plate(Bd, torso, "U", bevel=2.6, tilt=(-0.35, -0.15), strength=1.35)
    info["torso"] = tm
    R.dline(Bd, F(1.8, -ln - 1.4), F(2.4, -2.4), ("U", 5))               # keel ridge
    R.dline(Bd, F(-3.8, -ln - 1.0), F(2.4, -ln - 1.7), ("G", 3))         # gilt neck trim
    for k in range(3):                                                  # hollow ribs through a torn flank
        R.dline(Bd, F(-4.4, -ln + 6.4 + k * 1.8), F(-1.6, -ln + 7.2 + k * 1.8), ("A", 1) if k % 2 else ("B", 2))
    R.cap(Bd, F(0.2, -ln - 1.0), add(Hd, (-0.8, 4.6)), 1.8, 1.6, "A", bias=-1)   # gaunt neck
    # ---------------- head: narrow helm, T-visor, one swept-back blade crest
    G = basis(Hd, p["hup"])
    Hl = Ls["Head"]
    helm = [G(-2.8, 3.6), G(-3.4, -1.0), G(-2.4, -3.8), G(0.2, -4.8), G(2.8, -3.6), G(3.8, -1.2), G(4.6, 1.2), G(2.8, 3.8), G(0.0, 4.2)]
    hm = R.plate(Hl, helm, "U", bevel=2.0, tilt=(-0.3, -0.2), strength=1.3)
    info["head"] = hm
    R.dline(Hl, G(0.6, -0.8), G(4.2, -0.8), "OUT")                     # visor slit
    R.dline(Hl, G(2.4, -0.8), G(2.4, 2.4), "OUT")                      # T
    crest = [G(-0.4, -4.4), G(1.2, -4.8), G(-2.8, -8.2), G(-11.0, -10.0 - sx * 0.2), G(-5.0, -6.8), G(-2.6, -4.2)]
    cm = R.mask(crest)
    Hl.paint(n_plate(cm, 1.0, (-0.2, -0.4), 1.2), "U", bias=0, ao=0)
    Hl.decal([q for q in cm if (q[0] + q[1]) % 3 == 0], ("G", 3))
    e = R.pt(G(3.4, -0.8))
    if p["eye"]:
        if phase == 2:
            FX.put([e, (e[0] - 1, e[1])], "X3" if p["eye"] == 1 else "X4")
        else:
            FX.put([e], "N4" if p["eye"] == 1 else "N5")
        if p["eye"] == 2:
            FX.put([(e[0] + 1, e[1]), (e[0] + 2, e[1])], "X2" if phase == 2 else "N3")

    # ---------------- arms: dark sleeves, bronze pauldron + vambraces
    arm(R, Ls["BackArm"], shB, p["hb"], 8.0, 8.0, 2.2, 1.9, "L", bias=-1, fist="U", fist_r=1.8, fore="U", pref=(-1, 0.6))
    R.dome(Ls["BackArm"], add(shB, (0, -0.6)), 3.0, 2.6, "U", bias=-1)
    Fa = Ls["FrontArm"]
    el = arm(R, Fa, shF, p["hf"], 8.0, 8.0, 2.3, 2.0, "L", bias=0, fist="U", fist_r=1.9, fore="U", pref=(-1, 0.7))
    for k, (dx, dy, rx, ry) in enumerate(((0.6, 1.8, 3.4, 2.2), (0.0, -0.8, 4.0, 3.0))):
        m = R.dome(Fa, add(shF, (dx, dy)), rx, ry, "U", tilt=(0.05, 0.1))
        Fa.decal([q for q in m if (q[0], q[1] + 1) not in m], ("G", 3) if k else ("C", 3))

    # ---------------- phase 2: embers off the blades and sash
    if phase == 2:
        for k in range(10):
            t = (fi * 0.29 + hash01(k, 2, 5)) % 1.0
            src = info["tip_f"] if k % 2 else info["tip_b"]
            q = ip((src[0] - t * 6 + math.sin(k + fi) * 2, src[1] - t * 14))
            if K.inb(*q) and q[1] <= FLOOR:
                FX.put([q], "X3" if t < 0.4 else "X2" if t < 0.7 else "X1")

    # ---------------- smears
    pal = "bonew" if phase == 1 else "emberw"
    for sm in (p["smear"], p["smear2"]):
        if not sm:
            continue
        which = sm.get("w", "f")
        g_e, a_e = info["g_" + which], info["a_" + which]
        hot = swept(FX, R.T(sm["g0"]), R.A(sm["a0"]), g_e, a_e, sm.get("u0", 8), SAB + 0.5, hw=1.0, mid=sm.get("mid"),
                    start=sm.get("start", 0.0), pal=pal, exclude=blades, taper=sm.get("taper", 0.7), clip_y=FLOOR)
        info["hit"] |= hot
    if p["flat"]:
        info["hit"] |= flat_arc(FX, p["flat"], pal, exclude=blades, back=FXB, floor=FLOOR)
    if p["thrust"]:
        th = p["thrust"]
        pts = thrust_lines(FX, info["g_f"], info["a_f"], th.get("u0", -24), th.get("u1", 4), th.get("offs", (-3, -1, 2)),
                           pal="steel" if phase == 1 else "ember", flash=th.get("flash"))
        info["hit"] |= {q for q in pts if q[0] > AX}
    if p["dust"]:
        for fx_ in ((p["fb"][0], -1), (p["ff"][0], 1)):
            for k in range(6):
                x = int(fx_[0] + fx_[1] * (1 + k * 1.3) + (hash01(k, fi, 9) - 0.5) * 2)
                y = FLOOR - int(hash01(k, fi, 10) * (2 + k * 0.5))
                FX.put([(x, y)], ("A3", "A2", "I3")[k % 3])
    if p["glint"]:
        star(FX, p["glint"], "N5" if phase == 1 else "X4", "N3" if phase == 1 else "X2")
    return Ls, info


# =========================================================================== animations
def a_idle():
    fr = []
    for i in range(6):
        b = (0, 0.4, 0.8, 1.0, 0.8, 0.4)[i]
        fr.append((170, M(GUARD, P=(39.0, 48.4 + b * 0.3), C=(40.4, 35.8 + b * 0.8), Hd=(42.4, 25.6 + b * 0.9), hf=(51.0, 45.0 + b * 0.5),
                          hb=(33.0, 39.0 + b * 0.6), wf=18 + b * 2, wind=0.5 * math.sin(i * 1.05))))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        ff = (40.0 + 8.0 * c, 71 - max(0.0, -s) * 3.6)
        fb = (39.0 - 8.0 * c, 71 - max(0.0, s) * 3.6)
        bob = 1.4 * abs(c)
        fr.append((105, M(GUARD, P=(39.4, 48.0 + bob), C=(41.0, 35.4 + bob), Hd=(43.0, 25.2 + bob), fb=fb, ff=ff,
                          hf=(51.5 + 0.6 * c, 45.0 + bob), hb=(33.0 - 0.6 * c, 39.0 + bob), wf=18 + 3 * s)))
    return fr


def a_salute():
    up_ = dict(P=(40.0, 47.0), C=(41.0, 34.2), Hd=(42.6, 24.0), hup=(0.05, -1), fb=(34.0, 71), ff=(46.0, 71))
    return [
        (140, M(GUARD)),
        (160, M(up_, hf=(46.0, 38.0), wf=-80, hb=(42.0, 38.0), wb=-100)),
        (400, M(up_, hf=(44.0, 32.0), wf=-60, hb=(43.0, 32.0), wb=-120, eye=2, glint=(43.5, 16.0), bl="BladeFront")),
        (160, M(up_, hf=(47.0, 38.0), wf=-20, hb=(38.0, 38.0), wb=-160)),
        (160, M(GUARD, wf=10, hb=(33.0, 40.0), wb=-158)),
        (240, M(GUARD)),
    ]


def a_flurry():
    L1 = dict(P=(43.0, 49.6), C=(46.6, 37.6), Hd=(49.2, 27.8), hup=(0.4, -1), fb=(32.0, 71), ff=(54.0, 71))
    L2 = dict(P=(45.0, 49.8), C=(48.6, 38.0), Hd=(51.4, 28.2), hup=(0.42, -1), fb=(34.0, 71), ff=(57.0, 71))
    X = dict(P=(46.4, 50.6), C=(50.4, 39.4), Hd=(53.4, 29.8), hup=(0.5, -1), fb=(34.0, 71), ff=(59.0, 71))
    return [
        (100, M(GUARD, hf=(49.0, 42.0), wf=-40)),
        (230, M(GUARD, P=(38.0, 49.0), C=(38.6, 36.6), Hd=(40.2, 26.6), hf=(45.0, 30.0), wf=-120, hb=(31.0, 44.0), wb=160, eye=2, glint=(34.0, 16.0))),
        (50, M(L1, hf=(56.0, 48.0), wf=40, hb=(32.0, 44.0), wb=170, smear=dict(g0=(45.0, 30.0), a0=-120, mid=(58.0, 26.0), start=0.1))),
        (70, M(L1, hf=(54.0, 50.0), wf=58, hb=(52.0, 38.0), wb=-6, smear=dict(w="b", g0=(32.0, 44.0), a0=170, mid=(44.0, 34.0), start=0.1))),
        (70, M(L1, hf=(52.0, 52.0), wf=70, hb=(50.0, 38.0), wb=10)),
        (120, M(L1, hf=(46.0, 56.0), wf=150, hb=(40.0, 36.0), wb=-60, eye=2)),
        (50, M(L2, hf=(59.0, 38.0), wf=-40, hb=(40.0, 38.0), wb=-80, smear=dict(g0=(46.0, 56.0), a0=150, mid=(60.0, 62.0), start=0.1))),
        (70, M(L2, hf=(56.0, 32.0), wf=-80, hb=(40.0, 38.0), wb=-90)),
        (170, M(L2, P=(43.0, 50.0), C=(44.6, 37.6), Hd=(46.4, 27.6), hup=(0.2, -1), hf=(45.0, 26.0), wf=-130, hb=(40.0, 27.0), wb=-140, eye=2,
                glint=(40.0, 12.0))),
        (50, M(X, hf=(62.0, 50.0), wf=50, hb=(60.0, 46.0), wb=30, smear=dict(g0=(45.0, 26.0), a0=-130, mid=(62.0, 24.0), start=0.1),
               smear2=dict(w="b", g0=(40.0, 27.0), a0=-140, mid=(58.0, 28.0), start=0.15))),
        (80, M(X, hf=(60.0, 55.0), wf=72, hb=(56.0, 54.0), wb=66, smear=dict(g0=(62.0, 50.0), a0=50, taper=0.4, u0=12))),
        (120, M(X, hf=(58.0, 56.0), wf=78, hb=(52.0, 55.0), wb=80)),
        (160, M(GUARD, P=(41.0, 49.0), C=(42.6, 36.6), Hd=(44.6, 26.6), hf=(53.0, 48.0), wf=40, hb=(38.0, 44.0), wb=160)),
        (200, M(GUARD)),
    ]


def a_cross():
    crouch = dict(P=(38.0, 52.0), C=(39.6, 40.0), Hd=(42.0, 30.4), hup=(0.36, -1), fb=(28.0, 71), ff=(47.0, 71))
    lunge = dict(P=(48.0, 53.0), C=(54.0, 42.4), Hd=(58.4, 33.6), hup=(0.62, -1), fb=(30.0, 71), ff=(64.0, 71))
    return [
        (120, M(crouch, hf=(40.0, 50.0), wf=170, hb=(36.0, 48.0), wb=175)),
        (280, M(crouch, P=(37.0, 53.0), C=(38.0, 41.4), Hd=(40.2, 31.8), hf=(34.0, 50.0), wf=176, hb=(31.0, 47.0), wb=178, eye=2, glint=(18.0, 48.0))),
        (60, M(lunge, hf=(64.0, 44.0), wf=-14, hb=(62.0, 48.0), wb=14, wind=5, thrust=dict(u0=-30, u1=2, offs=(-3, 0, 3)))),
        (70, M(lunge, hf=(66.0, 36.0), wf=-60, hb=(64.0, 55.0), wb=60, wind=3,
               smear=dict(g0=(64.0, 44.0), a0=-14, taper=0.5, u0=8), smear2=dict(w="b", g0=(62.0, 48.0), a0=14, taper=0.5, u0=8))),
        (90, M(lunge, hf=(64.0, 34.0), wf=-80, hb=(62.0, 58.0), wb=80)),
        (120, M(lunge, P=(46.0, 52.0), C=(51.0, 40.6), Hd=(55.0, 31.2), hf=(60.0, 40.0), wf=-40, hb=(58.0, 52.0), wb=40)),
        (140, M(GUARD, P=(43.0, 49.6), C=(45.4, 37.2), Hd=(48.0, 27.2), hf=(55.0, 46.0), wf=10, hb=(40.0, 42.0), wb=-160)),
        (140, M(GUARD, P=(41.0, 49.0), C=(42.6, 36.6), Hd=(44.6, 26.6), hf=(53.0, 46.0), wf=14, hb=(36.0, 41.0), wb=-156)),
        (160, M(GUARD)),
        (160, M(GUARD)),
    ]


def a_whirl():
    sp = dict(P=(41.0, 49.0), C=(41.8, 36.4), Hd=(43.6, 26.4), hup=(0.12, -1), fb=(32.0, 71), ff=(50.0, 71))
    c = (40.0, 44.0)
    return [
        (120, M(GUARD, hf=(46.0, 44.0), wf=170, hb=(36.0, 42.0), wb=0)),
        (220, M(GUARD, P=(38.0, 50.0), C=(37.6, 37.6), Hd=(38.8, 27.6), hf=(40.0, 46.0), wf=178, hb=(38.0, 40.0), wb=-5, eye=2, glint=(22.0, 44.0))),
        (55, M(sp, hf=(52.0, 42.0), wf=0, hb=(30.0, 44.0), wb=180, flat=dict(c=c, rx=30.0, ry=8.0, th0=-200, th1=12, w=5.0))),
        (55, M(sp, hf=(30.0, 44.0), wf=180, hb=(51.0, 42.0), wb=0, flat=dict(c=c, rx=30.0, ry=8.0, th0=12, th1=190, w=5.0))),
        (55, M(sp, hf=(52.0, 45.0), wf=6, hb=(29.0, 42.0), wb=176, flat=dict(c=(40.0, 46.0), rx=30.0, ry=8.0, th0=-190, th1=12, w=5.0))),
        (70, M(sp, hf=(30.0, 46.0), wf=176, hb=(50.0, 44.0), wb=4, flat=dict(c=(40.0, 46.0), rx=30.0, ry=8.0, th0=12, th1=190, w=3.5, fade=0.5))),
        (120, M(GUARD, hf=(48.0, 46.0), wf=30, hb=(34.0, 40.0), wb=-150)),
        (160, M(GUARD)),
        (140, M(GUARD)),
        (140, M(GUARD)),
    ]


def a_leap():
    crouch = dict(P=(39.0, 53.0), C=(41.4, 41.0), Hd=(44.0, 31.4), hup=(0.36, -1), fb=(30.0, 71), ff=(48.0, 71))
    air = dict(P=(40.0, 46.0), C=(40.6, 33.6), Hd=(41.8, 23.6), hup=(0.05, -1), fb=(35.0, 64.0), ff=(46.0, 62.0))
    land = dict(P=(42.0, 56.0), C=(46.0, 45.0), Hd=(49.4, 36.0), hup=(0.55, -1), fb=(30.0, 71), ff=(53.0, 71))
    return [
        (140, M(crouch, hf=(46.0, 50.0), wf=150, hb=(34.0, 48.0), wb=170)),
        (220, M(crouch, P=(38.6, 55.0), C=(41.0, 43.2), Hd=(43.8, 33.6), hf=(45.0, 52.0), wf=155, hb=(33.0, 50.0), wb=172, eye=2, dust=1,
                glint=(52.0, 30.0))),
        (80, up(M(air, hf=(46.0, 26.0), wf=-100, hb=(38.0, 26.0), wb=-110, lift=6, dust=1), 2)),
        (100, up(M(air, hf=(44.0, 22.0), wf=-120, hb=(38.0, 23.0), wb=-128, lift=8), 4)),
        (120, up(M(air, hf=(43.0, 21.0), wf=-128, hb=(37.0, 22.0), wb=-134, lift=5, eye=2), 4)),
        (140, up(M(air, hf=(43.0, 21.0), wf=-132, hb=(37.0, 22.0), wb=-138, lift=2), 3)),
        (60, up(M(air, P=(42.0, 47.0), C=(44.4, 35.2), Hd=(46.8, 25.4), hup=(0.3, -1), hf=(52.0, 44.0), wf=80, hb=(47.0, 43.0), wb=86, lift=-8,
                  smear=dict(g0=(43.0, 21.0), a0=-132, mid=(56.0, 20.0), start=0.2)), 2)),
        (60, M(land, hf=(56.0, 52.0), wf=84, hb=(52.0, 52.0), wb=88, dust=1)),
        (120, M(land, hf=(56.0, 53.0), wf=86, hb=(52.0, 53.0), wb=90)),
        (160, M(GUARD, P=(41.0, 51.0), C=(43.0, 38.8), Hd=(45.4, 28.8), hf=(54.0, 50.0), wf=50, hb=(40.0, 46.0), wb=150)),
        (180, M(GUARD)),
    ]


def a_backstep():
    return [
        (90, M(GUARD, P=(39.0, 50.0), C=(40.6, 37.6), Hd=(42.6, 27.6))),
        (80, up(M(GUARD, P=(37.4, 47.0), C=(36.4, 34.6), Hd=(37.0, 24.6), hup=(-0.16, -1), fb=(32.0, 69.0), ff=(47.0, 71.0), wind=-2, lift=3, dust=1), 2)),
        (110, up(M(GUARD, P=(36.0, 46.0), C=(35.4, 33.6), Hd=(36.2, 23.6), hup=(-0.1, -1), fb=(32.0, 64.0), ff=(44.0, 63.0), wind=-4, lift=7), 6)),
        (90, M(GUARD, P=(38.0, 50.4), C=(39.4, 38.0), Hd=(41.4, 28.0), dust=1)),
        (150, M(GUARD)),
    ]


def a_stagger():
    return [
        (90, M(GUARD, P=(37.6, 48.0), C=(35.6, 35.8), Hd=(34.8, 26.0), hup=(-0.4, -1), hf=(44.0, 34.0), wf=-100, hb=(30.0, 38.0), wb=-170, eye=0)),
        (130, M(GUARD, P=(38.0, 52.0), C=(39.4, 40.0), Hd=(41.6, 30.4), hup=(0.3, -1), hf=(46.0, 54.0), wf=86, hb=(32.0, 52.0), wb=100, eye=0)),
        (260, M(GUARD, P=(38.4, 53.0), C=(40.4, 41.2), Hd=(43.4, 32.0), hup=(0.5, -1), hf=(47.0, 56.0), wf=88, hb=(33.0, 54.0), wb=96, eye=0)),
        (260, M(GUARD, P=(38.2, 53.4), C=(40.0, 41.6), Hd=(42.8, 32.4), hup=(0.48, -1), hf=(46.6, 56.4), wf=88, hb=(32.6, 54.4), wb=96, eye=0)),
    ]


def a_death():
    KN = dict(P=(38.0, 57.0), C=(41.0, 45.4), Hd=(44.4, 36.4), hup=(0.55, -1), kb=(33.0, 69.0), fb=(24.0, 71), ff=(47.0, 71),
              kf=(46.0, 57.0), hf=(50.0, 60.0), wf=92, hb=(34.0, 60.0), wb=96, eye=0)
    fr = [
        (100, M(GUARD, P=(37.6, 48.0), C=(35.6, 35.8), Hd=(34.8, 26.0), hup=(-0.45, -1), hf=(44.0, 34.0), wf=-100, hb=(30.0, 38.0), wb=-170, eye=2)),
        (160, M(GUARD, P=(38.0, 52.0), C=(39.8, 40.0), Hd=(42.0, 30.4), hup=(0.3, -1), hf=(47.0, 56.0), wf=80, hb=(33.0, 54.0), wb=100, eye=1)),
        (200, M(KN)),
        (500, M(KN, Hd=(45.0, 37.2), hup=(0.62, -1))),
        (300, M(KN, C=(41.6, 46.0), Hd=(45.6, 37.8), hup=(0.72, -1))),
    ]
    for d, ms in ((0.16, 140), (0.34, 140), (0.52, 140), (0.74, 160), (0.97, 900)):
        fr.append((ms, M(KN, C=(41.6, 46.0), Hd=(45.6, 37.8), hup=(0.72, -1), dissolve=d)))
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("salute", a_salute), ("flurry", a_flurry), ("cross", a_cross), ("whirl", a_whirl),
           ("leap", a_leap), ("backstep", a_backstep), ("stagger", a_stagger), ("death", a_death)]
LOOPS = ("idle", "walk")


def render_frame(p, fi, sw, phase):
    Ls, info = draw(p, fi, sw, phase)
    imgs = {}
    for n in LAYERS:
        v = Ls.get(n)
        if v is None:
            continue
        imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
    if p["dissolve"] > 0:
        pal = ("N5", "N4", "N3", "A3", "A2") if phase == 1 else ("X4", "X3", "X2", "X1", "X0")
        imgs = K.ember_dissolve(imgs, p["dissolve"], [n for n in LAYERS if n not in ("FX", "FXBack")], fx_name="FX", seed=7, rise=26, pal=pal)
    return imgs, info


def render_all(only=None):
    out = {1: [], 2: []}
    infos, tags = {}, []
    n = 0
    for tag, fn in TAGDEFS:
        fr = fn()
        if only and tag not in only:
            continue
        drv = [p["C"][0] for _, p in fr]
        sway = K.spring(drv, loop=tag in LOOPS, extra=[p.get("wind", 0.0) for _, p in fr])
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            for ph in (1, 2):
                imgs, info = render_frame(p, a + k, sway[k], ph)
                out[ph].append((ms, imgs))
                if ph == 1:
                    infos[tag].append(info)
            n += 1
        tags.append((tag, a, n - 1))
        print("rendered", tag, len(fr))
    return out, infos, tags


def build_meta(infos):
    idle = infos["idle"][0]
    tb = bbox(idle["torso"] | idle["head"])
    hurt = [tb[0], tb[1], tb[2] + 1, H - tb[1]]
    at = S.attack
    return {
        "native": 1, "frame": [W, H], "anchor": [AX, H], "hurtbox": hurt,
        "attacks": {
            "flurry": {"windows": [at(infos, "flurry", 2, 2, AX + 2), at(infos, "flurry", 3, 3, AX + 2), at(infos, "flurry", 6, 6, AX + 2),
                                   at(infos, "flurry", 9, 10, AX + 2)]},
            "cross": at(infos, "cross", 2, 3, AX + 2),
            "whirl": {"windows": [at(infos, "whirl", 2, 3, 0, both=True), at(infos, "whirl", 4, 5, 0, both=True)]},
            "leap": at(infos, "leap", 7, 8, AX - 6),
        },
        "telegraph": {
            "flurry": {"frame": 1, "at": [34, 16]},
            "cross": {"frame": 1, "at": [18, 48]},
            "whirl": {"frame": 1, "at": [22, 44]},
            "leap": {"frame": 1, "at": [52, 30]},
        },
        "notes": "Hollow Champion faces right, anchor = feet. flurry = 4 cuts (windows), cross = lunging X-cut (engine steps him "
                 "forward), whirl = spinning blade dance hitting both sides, leap = jump + double plunge (airborne 2-6, drawn in "
                 "place). salute = intro. champion_p2 shares this meta.",
    }


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    out, infos, tags = render_all(only)
    pv = S.PREV
    flats = {ph: [K.flatten(imgs, LAYERS) for _, imgs in out[ph]] for ph in (1, 2)}
    sfx = "_wip" if only else ""
    S.preview_rows(tags, flats[1], os.path.join(pv, f"champion{sfx}.png"))
    S.preview_rows(tags, flats[2], os.path.join(pv, f"champion_p2{sfx}.png"))
    S.closeup(flats[1] + flats[2], [0, len(flats[1])], os.path.join(pv, f"champion_closeup{sfx}.png"))
    if only:
        return
    meta = build_meta(infos)
    S.hitbox_preview(tags, flats[1], meta, os.path.join(pv, "champion_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "champion_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        for w_ in d.get("windows", [d]):
            print("attack", t, w_["active"], w_["hit"])
    print("hurtbox", meta["hurtbox"])
    if BUILD:
        asebuild.build("champion", W, H, LAYERS, [{"ms": ms, "cels": imgs} for ms, imgs in out[1]], tags)
        asebuild.build("champion_p2", W, H, LAYERS, [{"ms": ms, "cels": imgs} for ms, imgs in out[2]], tags)


if __name__ == "__main__":
    main()
