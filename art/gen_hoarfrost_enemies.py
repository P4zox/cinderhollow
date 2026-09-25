#!/usr/bin/env python3
"""Hoarfrost Aqueduct creatures (docs/EXPANSION_CONTRACT.md agent H), same contract as ART_SPEC section 4.

    python3 art/gen_hoarfrost_enemies.py                  build everything (Aseprite)
    python3 art/gen_hoarfrost_enemies.py --preview        previews + meta only (no Aseprite)
    python3 art/gen_hoarfrost_enemies.py --only hf_wraith,fx [--preview]

Outputs per creature <name>: art/<name>.aseprite, assets/<name>.png/.json, assets/<name>_meta.json,
art/previews/<name>.png (4x, one row per tag), art/previews/<name>_hitbox.png (hurtbox green, hit rects red,
spawn magenta, telegraph cyan). FX: fx_hf_breath, fx_hf_frostwave -> art/previews/fx_hf_enemies.png.
Region read check: art/previews/hf_sanity.png (1x and 2x on #0b0f18).

Hoarfrost look: blue-black dressed stone, white-blue rime, glassy ice; frost-light (#6fbaf2 / #c4ecff / white)
is the only glow and stays restrained.
    hf_wraith   48x40  frost wraith, floats (anchor = body centre)
    hf_golem    64x56  sleek angular sentinel of aqueduct stone bound by ice
    hf_lurker   48x32  pale under-ice eel-serpent rising from a pool (anchor = water surface)
All face RIGHT. Method + helpers: enemy_kit.py, hoarfrost_enemykit.py.
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import hoarfrost_enemykit as HK  # noqa: E402  (registers the cold ramps)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,  # noqa: E402
                       poly_mask, n_plate, n_dome, n_capsule, norm3, swept, dirv, bbox)
from hoarfrost_enemykit import (mk, spawn_pt, rot, madd, curve, n_tube, resample, ribbon, nearest_t,  # noqa: E402
                                disc_glow, star, rim, render_anims, hit_rect, hurtbox, frost_dissolve, shatter)
from PIL import Image, ImageDraw  # noqa: E402

BUILD = "--preview" not in sys.argv

SPEC = {
    "hf_wraith": dict(fly=6, breath=10, dive=6, hurt=2, death=6),
    "hf_golem": dict(idle=4, walk=6, slam=12, swipe=9, hurt=2, death=8),
    "hf_lurker": dict(lurk=4, emerge=7, idle=4, grab=9, submerge=5, hurt=2, death=6),
}


FLATS = {}


def export(name, layers, anims, meta):
    tags, flats = K.export(name, layers, anims, meta, build=BUILD)
    if meta is not None:
        HK.hitbox_preview(name, tags, flats, meta)
    FLATS[name] = ({t: (a, b) for t, a, b in tags}, flats, (K.W, K.H), meta)
    return tags, flats


# =========================================================================== 1. FROST WRAITH
WR_L = ["VeilBack", "ArmBack", "Veil", "Mask", "ArmFront", "FX"]
W_NEU = dict(O=(24.0, 20.0), tilt=0.0, hd=(4.6, -10.6), hup=0.0, jaw=0.0, eye=1, throat=0, chest=0.0,
             hf=(13.0, 0.6), hb=(9.6, 2.4), claw=45.0, clawb=55.0, ph=0.0, amp=1.0, breath=0, inhale=0,
             streak=0, glint=False, wind=0.0, lean=0.0)
WP = mk(W_NEU)


def wraith_arm(R, L, M, sh, hand, claw, bias, fi, sleeve_seed):
    """Long skeletal arm: tattered veil sleeve over the upper arm, bone forearm, three long ice claws."""
    s, h = R.T(M(*sh)), R.T(M(*hand))
    el = ik(s, h, 7.0, 7.8, R_pref(R, (-0.8, 0.7)))
    # bone forearm + hand
    L.paint(n_tube([el, h], [0.95, 0.75]), "H", bias)
    L.paint(n_capsule(s, lerp(s, el, 0.5), 0.9, 0.9), "H", bias - 1)
    # sleeve: ragged cloth from the shoulder over the upper arm, hanging below the elbow
    d = sub(el, s)
    ln = math.hypot(*d) or 1
    ca = R.A(0)
    poly, _ = ribbon([s, lerp(s, el, 0.55), el, add(el, (-0.6, 2.6))], [1.9, 1.7, 1.5, 0.3], [1.6, 1.5, 1.2, 0.3],
                     n=4, jag=0.9, jag_from=0.55, fi=fi, seed=sleeve_seed)
    L.paint(n_plate(poly_mask(poly), 1.2, (-0.1, -0.2), 1.0), "X", bias)
    # claws: three long thin hooked ice blades
    tips = []
    a = claw
    for k, (da, cl) in enumerate(((-24, 4.6), (0, 5.6), (22, 4.2))):
        dd = dirv(a + da)
        pts = []
        for j in range(int(cl * 2) + 1):
            u = j / 2
            hook = 0.06 * u * u
            pts.append(ip((h[0] + dd[0] * (u + 0.7) - dd[1] * hook, h[1] + dd[1] * (u + 0.7) + dd[0] * hook)))
        pts = list(dict.fromkeys(pts))
        L.fill([q for q in pts[1:]], None)
        for j, q in enumerate(pts[1:]):
            if q not in L.px:
                continue
            L.px[q][3] = ("U5" if j == len(pts) - 2 and k == 1 and bias >= 0 else
                          "U4" if j >= len(pts) - 3 and bias >= 0 else "U3" if bias >= 0 else "U2")
            L.noout.add(q)
        tips.append(pts[-1])
    L.paint(n_dome(h, 0.9, 0.9), "H", bias, ao=0)
    return el, h, tips


def R_pref(R, v):
    return rot(v, R.rot)


def breath_cone(FX, m, ang, stage, fi):
    """Freezing breath: a short cone of frost mist with bright crystals, in frame from the mouth (frame coords)."""
    pts = set()
    if stage <= 0:
        return pts
    L_ = {1: 7.0, 2: 15.0, 3: 16.5, 4: 16.5}[stage]
    d0 = 0.0 if stage < 4 else 5.0
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for y in range(int(m[1] - 12), int(m[1] + 13)):
        for x in range(int(m[0]), int(m[0] + L_ + 3)):
            dx, dy = x + .5 - m[0], y + .5 - m[1]
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if u < d0 or u > L_:
                continue
            half = 1.0 + u * 0.36 + 0.8 * math.sin(u * 0.9 - fi * 1.7)
            r = abs(v) / half
            if r > 1.0:
                continue
            hh = hash01(x, y, fi * 7 + stage)
            edge = 1 - r
            fade = u / L_
            dens = 0.95 - fade * 0.55 - (0.35 if stage == 4 else 0.0)
            if hh > dens + edge * 0.25:
                continue
            if r < 0.28 and fade < 0.55:
                c = "J5" if fade < 0.22 else "J4"
            elif r < 0.55:
                c = "J4" if fade < 0.35 else "J3"
            elif r < 0.8:
                c = "J3" if fade < 0.6 else "J2"
            else:
                c = "J2" if fade < 0.7 else "J1"
            if stage == 4 and c in ("J5", "J4"):
                c = "J3"
            FX.put([(x, y)], c)
            pts.add((x, y))
    # ice crystals glinting in the stream
    for k in range(6 if stage > 1 else 2):
        u = L_ * (0.3 + 0.7 * hash01(k, fi, 41))
        v = (hash01(k, fi, 42) - 0.5) * (2 + u * 0.6)
        q = ip((m[0] + u * ca - v * sa, m[1] + u * sa + v * ca))
        FX.put([q], "J5" if k % 2 == 0 else "U5")
        pts.add(q)
    return pts


def draw_wraith(p, fi, sw):
    Ls = {n: Layer(n) for n in WR_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    O = p["O"]
    R = Rig(p["tilt"], O)
    M = lambda x, y: (O[0] + x, O[1] + y)
    info = {"hit": set()}
    ph, amp = p["ph"], p["amp"]
    wv = lambda k: math.sin(ph + k * 0.9) * amp
    # ---- body: gaunt veil hanging from the shoulders, tapering into a trailing wisp of ice-mist
    sp = [(1.2 + p["lean"] * 0.5, -8.0), (0.6, -3.0), (-1.2, 2.6), (-4.8 + sw * 0.2, 6.8 + wv(0) * 0.4),
          (-9.4 + sw * 0.4, 8.8 + wv(1) * 0.8), (-14.0 + sw * 0.6, 8.8 + wv(2) * 1.3),
          (-18.4 + sw * 0.8, 7.0 + wv(3) * 1.7), (-21.8 + sw, 3.8 + wv(4) * 2.0)]
    ch = p["chest"]
    wu = [2.6 + ch, 3.2 + ch, 3.0, 2.4, 1.6, 1.0, 0.5, 0.2]
    wd = [3.2, 3.0 + ch * 0.5, 2.6, 1.9, 1.3, 0.8, 0.4, 0.1]
    poly, samp = ribbon([R.T(M(*q)) for q in sp], wu, wd, n=6, jag=1.8, jag_from=0.3, jag_up=0.6, fi=fi // 2, seed=3)
    vm = poly_mask(poly)
    Vl = Ls["Veil"]
    Vb = Ls["VeilBack"]
    Vl.paint(n_plate(vm, 2.0, (-0.05, -0.1), 1.0,
                     fold=lambda x, y: (0.55 * math.sin((x - O[0]) * 0.8 + (y - O[1]) * 0.35 + ph * 0.6), 0.0)), "X", -1)
    # shredded tatters hanging from the waist and trailing back
    tat = []
    for k, (a0, e0, w0) in enumerate((((1.4, 2.6), (-1.6, 14.6), 1.4), ((-2.0, 5.4), (-7.0, 16.2), 1.3),
                                       ((-5.6, 8.4), (-11.6, 14.8), 1.0))):
        pts = [a0]
        for j in range(1, 4):
            u = j / 3
            pts.append((a0[0] + (e0[0] - a0[0]) * u + sw * 0.5 * u * u + wv(k * 2 + j) * 0.5 * u,
                        a0[1] + (e0[1] - a0[1]) * u - 1.2 * math.sin(u * math.pi) * 0.5))
        pl, sm_ = ribbon([R.T(M(*q)) for q in pts], [w0, w0 * 0.8, w0 * 0.5, 0.1], [w0, w0 * 0.7, 0.4, 0.1], n=5,
                         jag=0.7, jag_from=0.5, fi=fi // 2, seed=31 + k)
        tm = poly_mask(pl)
        (Vb if k != 1 else Vl).paint(n_plate(tm, 1.0, (-0.1, -0.1), 1.0), "X", -1 - (k % 2))
        tat.append((tm, sm_, Vb if k != 1 else Vl))
    # the tail ends turn to mist: solid cloth gives way to un-outlined frost motes
    mist = []
    for mm, ss, LL, t0 in [(vm, samp, Vl, 0.72)] + [(a, b, c, 0.8) for a, b, c in tat]:
        for q in list(mm):
            if q not in LL.px:
                continue
            t = nearest_t(ss, q)
            if t > t0:
                k = (t - t0) / (1 - t0)
                LL.erase([q])
                if hash01(q[0], q[1], fi // 2 + 5) < 0.7 - k * 0.45:
                    mist.append((q, "U2" if k < 0.35 and hash01(q[0], q[1], 9) < 0.5 else "X3" if k < 0.6 else "J1"))
            elif t > t0 - 0.2:
                LL.shift([q], -1)
    for q, c in mist:
        FX.put([q], c)
    # trailing motes shed by the wisp
    tip = R.T(M(*sp[-1]))
    for k in range(6):
        tt = (fi * 0.17 + k / 6) % 1.0
        q = ip((tip[0] - 1 - tt * 6 + math.sin(k * 2.1 + fi) * 0.8, tip[1] - 1 + math.sin(k * 1.3) * 2.5 - tt * 2))
        FX.put([q], "J2" if tt < 0.25 else "J1" if tt < 0.6 else "X3")
    # ---- hood: pointed cowl, drooping tip swept back
    G = lambda x, y: R.T(add(M(*p["hd"]), rot((x, y), p["hup"])))
    hood = [G(-3.4, 6.0), G(-4.8, 1.4), G(-5.6, -2.0), G(-8.4 - sw * 0.3, -3.4 + wv(0) * 0.3), G(-4.4, -5.4),
            G(-1.6, -7.0), G(1.2, -6.8), G(3.4, -5.0), G(4.6, -3.0), G(3.0, -2.6),
            G(0.8, 1.4), G(1.4, 5.6), G(-0.8, 7.2)]
    hm = poly_mask(hood)
    Vl.paint(n_plate(hm, 1.8, (-0.15, -0.25), 1.1), "X", 0)
    # hood opening in deep shadow
    Vl.decal([q for q in poly_mask([G(0.6, -3.4), G(4.2, -2.6), G(3.2, 3.4), G(0.8, 4.6)]) if q in hm], ("X", 0))
    rim(Vl, ("X",), 3)
    # ---- mask: small skull face with cold light in the sockets
    Mk = Ls["Mask"]
    ja = p["jaw"] * 38.0
    hinge = (1.4, 1.2)
    J = lambda x, y: G(*add(hinge, rot(sub((x, y), hinge), ja)))
    if p["jaw"] > 0.1:     # glowing maw
        mouth = poly_mask([G(1.2, 1.0), G(5.8, 0.9), J(5.6, 1.3), J(1.4, 1.6)])
        Mk.fixed({q: ("J4" if p["breath"] or p["throat"] >= 2 else "J3") if hash01(*q, 2) < 0.6 else "J3"
                  for q in mouth})
    jaw = [J(1.0, 1.3), J(5.4, 1.3), J(5.0, 2.5), J(3.2, 3.1), J(1.2, 2.8)]
    Mk.paint(n_plate(poly_mask(jaw), 0.8, (-0.1, 0.2)), "H", -1)
    skull = [G(0.6, -3.0), G(3.0, -3.6), G(5.0, -2.4), G(6.0, -0.6), G(6.2, 0.6), G(5.2, 1.3), G(1.2, 1.5),
             G(0.0, -0.8)]
    sm = poly_mask(skull)
    Mk.paint(n_plate(sm, 1.0, (-0.25, -0.15), 1.0), "H", 1)
    Mk.decal([q for q in line(G(2.4, 0.6), G(4.8, 0.2)) if q in sm], ("H", 2))      # cheekbone shadow
    # brow of the hood overhanging the mask
    brow = [G(-0.2, -3.8), G(3.6, -4.8), G(5.4, -3.2), G(4.2, -2.6), G(1.0, -2.4)]
    Mk.paint(n_plate(poly_mask(brow), 0.8, (-0.1, -0.5)), "X", 1, ao=0)
    e = ip(G(3.9, -1.2))
    eg = ("X0", "J2", "J3", "J4")[min(3, p["eye"])]
    Mk.fixed({e: "J5" if p["eye"] >= 3 else "J4" if p["eye"] >= 1 else "X0",
              (e[0] - 1, e[1]): eg if p["eye"] else "X0", (e[0] - 1, e[1] + 1): "OUT"})
    Mk.fixed({ip(G(5.6, 0.4)): "H1"})                               # nasal pit
    if p["jaw"] <= 0.1:
        Mk.fixed({ip(G(3.2, 1.3)): "H1", ip(G(4.4, 1.3)): "H1"})     # clenched teeth seam
    info["eye"] = e
    info["mouth"] = G(6.4, 1.8 + p["jaw"] * 1.4)
    # throat glow through the veil
    th = G(0.8, 4.4)
    if p["throat"]:
        tl = p["throat"]
        Vl.fixed({ip(th): ("J2", "J3", "J4", "J5")[min(3, tl)], ip((th[0], th[1] + 1)): ("J1", "J2", "J3", "J4")[min(3, tl)]})
        if tl >= 2:
            for k in range(8 + tl * 2):
                a = k * 2 * math.pi / (8 + tl * 2) + fi * 0.6
                r = 2.4 + tl * 0.5 + (k % 2) * 0.8
                if (k + fi) % 2 == 0:
                    FX.put([ip((th[0] + math.cos(a) * r, th[1] + math.sin(a) * r * 0.9))], "J2" if k % 3 else "J3")
    info["throat"] = th
    # inhale: motes drawn in toward the mouth
    if p["inhale"]:
        mo = info["mouth"]
        for k in range(10):
            tt = (k / 10 + fi * 0.21) % 1.0
            a = -0.9 + 1.8 * hash01(k, 3, 17)
            r = 3 + 11 * tt
            q = ip((mo[0] + 1 + math.cos(a) * r, mo[1] + math.sin(a) * r * 0.8))
            FX.put([q], "J3" if tt < 0.35 else "J2" if tt < 0.7 else "J1")
    # ---- arms
    Ab, Af = Ls["ArmBack"], Ls["ArmFront"]
    _, hb, tb = wraith_arm(R, Ab, M, (-0.6, -6.6), p["hb"], R.A(p["clawb"]), -2, fi, 21)
    _, hf, tf = wraith_arm(R, Af, M, (3.4, -6.2), p["hf"], R.A(p["claw"]), 0, fi, 23)
    info["claws"] = tf + tb
    info["hand"] = hf
    info["hit"] |= set(Af.px) | set(Ab.px)
    info["body"] = set(Vl.px) | set(Mk.px)
    # ---- fx
    if p["breath"]:
        ang = R.A(p["hup"]) + 14
        info["breath"] = breath_cone(FX, info["mouth"], ang, p["breath"], fi)
    if p["streak"]:
        # speed streaks trailing the swoop (opposite to the dive direction)
        d = dirv(R.A(0) + 180 - 20)
        base = R.T(M(-2, -2))
        for k, off in enumerate((-6, -2, 2, 6)):
            a0 = madd(base, (d, 6 + (k % 2) * 3), ((-d[1], d[0]), off))
            b0 = madd(a0, (d, 7 + p["streak"] * 2 - (k * 3) % 4))
            seg = line(a0, b0)
            for j, q in enumerate(seg):
                if (q not in Vl.px) and (q not in Mk.px):
                    FX.put([q], "J3" if j < len(seg) * 0.3 else "J2" if j < len(seg) * 0.65 else "J1")
    if p["glint"]:
        star(FX, tf[1], 2)
        info["glint"] = tf[1]
    return Ls, info


def w_fly():
    fr = []
    for i in range(6):
        a = i * 2 * math.pi / 6
        bob = -math.sin(a) * 1.0
        fr.append((110, WP(O=(24.0, 20.0 + bob), ph=a, tilt=math.cos(a) * 2.0, hup=math.sin(a + 1) * 3,
                           hf=(13.0 + math.sin(a + 0.8) * 0.8, 0.6 + math.cos(a + 0.8) * 1.2),
                           hb=(9.6 + math.sin(a + 1.6) * 0.8, 2.4 + math.cos(a + 1.6) * 1.0),
                           claw=45 + math.sin(a + 0.8) * 8, clawb=55 + math.sin(a + 1.6) * 8)))
    return fr


def w_breath():
    return [
        (140, WP(O=(23.6, 19.6), hup=-8, throat=1, hf=(11.0, -0.6), hb=(7.6, 1.0), ph=0.6, chest=0.3, claw=30)),
        (140, WP(O=(22.8, 19.0), hup=-20, tilt=-4, throat=2, hf=(8.6, -2.6), hb=(5.4, -1.0), ph=1.2, chest=0.6,
                 inhale=1, eye=2, claw=0, clawb=20)),
        (180, WP(O=(22.2, 18.6), hup=-30, tilt=-8, throat=3, hf=(7.4, -3.8), hb=(4.2, -2.0), ph=1.8, chest=0.9,
                 inhale=1, eye=2, claw=-15, clawb=5)),
        (260, WP(O=(22.0, 18.4), hup=-34, tilt=-9, throat=3, hf=(7.0, -4.4), hb=(3.8, -2.4), ph=2.4, chest=1.0,
                 inhale=1, eye=3, claw=-20, clawb=0)),
        (80, WP(O=(24.4, 19.8), hup=10, tilt=5, jaw=1.0, throat=3, eye=3, breath=1, hf=(13.0, 4.4), hb=(9.6, 5.6),
                ph=3.0, wind=3, lean=1, claw=70, clawb=80)),
        (110, WP(O=(24.8, 20.0), hup=12, tilt=6, jaw=1.0, throat=2, eye=3, breath=2, hf=(13.4, 5.0), hb=(10.0, 6.0),
                 ph=3.6, lean=1, claw=75, clawb=85)),
        (110, WP(O=(24.8, 20.2), hup=11, tilt=6, jaw=1.0, throat=2, eye=2, breath=3, hf=(13.4, 5.2), hb=(10.0, 6.2),
                 ph=4.2, lean=1, claw=75, clawb=85)),
        (100, WP(O=(24.6, 20.2), hup=8, tilt=4, jaw=0.7, throat=1, eye=2, breath=4, hf=(13.2, 4.2), hb=(9.8, 5.4),
                 ph=4.8, claw=65, clawb=75)),
        (140, WP(O=(24.2, 20.0), hup=3, tilt=1, jaw=0.3, throat=1, hf=(13.0, 2.2), hb=(9.6, 3.6), ph=5.4, claw=55)),
        (160, WP(ph=6.0)),
    ]


def w_dive():
    return [
        (140, WP(O=(23.2, 20.2), tilt=-8, hup=-8, hf=(8.4, -10.0), hb=(4.6, -8.8), claw=-55, clawb=-70, ph=0.5,
                 eye=2)),
        (220, WP(O=(22.6, 20.4), tilt=-12, hup=-12, hf=(7.6, -11.4), hb=(3.6, -9.8), claw=-65, clawb=-80, ph=1.0,
                 eye=3, glint=True)),
        (70, WP(O=(24.6, 20.4), tilt=30, hup=4, hf=(16.0, -3.0), hb=(14.0, 0.0), claw=0, clawb=10, ph=1.8, eye=3,
                streak=1, wind=4, jaw=0.4)),
        (70, WP(O=(25.4, 21.0), tilt=38, hup=6, hf=(16.4, 0.4), hb=(14.4, 2.8), claw=25, clawb=32, ph=2.4, eye=3,
                streak=2, wind=4, jaw=0.5)),
        (90, WP(O=(25.4, 21.0), tilt=26, hup=4, hf=(14.4, 4.6), hb=(12.0, 6.0), claw=65, clawb=72, ph=3.0, eye=2,
                streak=1, jaw=0.2)),
        (170, WP(O=(24.4, 20.4), tilt=6, hf=(13.0, 1.8), hb=(9.6, 3.2), ph=3.6)),
    ]


def w_hurt():
    return [(90, WP(O=(22.4, 19.0), tilt=-14, hup=-18, jaw=0.6, eye=3, hf=(9.0, 4.6), hb=(5.0, 5.4), ph=1.0,
                    claw=80, clawb=90)),
            (140, WP(O=(23.4, 19.6), tilt=-5, hup=-6, jaw=0.2, eye=2, hf=(11.4, 2.6), hb=(7.6, 3.8), ph=1.6))]


def wraith_fade(frac, seed=0):
    return lambda imgs: frost_dissolve(imgs, frac, ["VeilBack", "ArmBack", "Veil", "Mask", "ArmFront"], seed=seed,
                                       rise=-9, drift=2, pal=("J4", "J3", "U4", "J2", "J1"))


def w_death():
    base = dict(O=(22.6, 19.0), tilt=-16, hup=-24, jaw=1.0, eye=3, hf=(9.0, -5.0), hb=(5.0, -3.0), claw=-40,
                clawb=-60, ph=1.0)
    return [
        (100, WP(**base)),
        (120, WP(**dict(base, eye=2, O=(22.6, 19.4)), post=wraith_fade(0.22, 1))),
        (120, WP(**dict(base, eye=2, O=(22.6, 19.8)), post=wraith_fade(0.42, 1))),
        (130, WP(**dict(base, eye=1, O=(22.6, 20.2)), post=wraith_fade(0.62, 1))),
        (140, WP(**dict(base, eye=1, O=(22.6, 20.6)), post=wraith_fade(0.85, 1))),
        (600, WP(**dict(base, eye=0, O=(22.6, 21.0)), post=wraith_fade(1.12, 1))),
    ]


def build_wraith():
    K.setup(48, 40)
    anims, infos = render_anims(SPEC["hf_wraith"], WR_L, draw_wraith,
                                [("fly", w_fly), ("breath", w_breath), ("dive", w_dive), ("hurt", w_hurt),
                                 ("death", w_death)], sway_key="O", loops=("fly",))
    mo4 = infos["breath"][4]["mouth"]
    bx, by = int(round(mo4[0])), int(round(mo4[1]))
    cone = set()
    for k in (5, 6):
        cone |= infos["breath"][k]["breath"]
    cr = bbox(cone)
    # extend the drawn cone (clipped by the frame) to ~26px along its own slope
    slope = ((cr[1] + cr[3] / 2) - by) / max(1, cr[0] + cr[2] - bx)
    y_end = by + slope * 26
    y0 = int(min(cr[1], y_end - 6))
    y1 = int(max(cr[1] + cr[3], y_end + 6))
    breath_hit = [bx, y0, 26, y1 - y0]
    dive_pts = set()
    for k in (2, 3, 4):
        dive_pts |= infos["dive"][k]["hit"]
    dr = bbox(dive_pts)
    meta = {"native": 1, "frame": [48, 40], "anchor": [24, 20], "flying": True,
            "hurtbox": hurtbox(anims, ["Veil", "Mask"], inset=(4, 2, 2), floor=False),
            "attacks": {"breath": {"active": [4, 7], "hit": breath_hit},
                        "dive": {"active": [2, 4], "hit": dr}},
            "spawn": {"breath": {"frame": 4, "at": spawn_pt(mo4)}},
            "telegraph": {"breath": {"frame": 2, "at": spawn_pt(infos["breath"][2]["mouth"])},
                          "dive": {"frame": 1, "at": spawn_pt(infos["dive"][1]["glint"])}},
            "notes": "faces right; floats (anchor = body centre). breath: rears back and inhales 0-3 (throat glow "
                     "builds, 3 = held), exhales 4-7 (in-frame mist burst; hit = ~26px cone in front of the mouth, "
                     "may extend past the frame), emit fx_hf_breath from spawn.breath.at; recovery 8-9. dive: wind-up "
                     "0-1 (claws raised, glint on 1), claws-first swoop 2-4 (engine moves it), recover 5."}
    export("hf_wraith", WR_L, anims, meta)
    return meta


# =========================================================================== shared: ice shards
def ice_shard(L, base, ang, length, width, lit=0, tip_glow=False, lean=0.0, ridge=5):
    """Faceted ice shard (sharp triangle) rising from base along ang (frame coords). Lit left facet, dark right
    facet, bright ridge; written as fixed colours into an outlined Layer. Returns the pixel set."""
    d = dirv(ang)
    pv = (-d[1], d[0])
    tip = madd(base, (d, length), (pv, lean))
    a = madd(base, (pv, -width * 0.5))
    b = madd(base, (pv, width * 0.5))
    m = poly_mask([a, tip, b])
    if not m:
        return set()
    out = {}
    for q in m:
        # which side of the ridge (base -> tip)
        cx, cy = q[0] + .5 - base[0], q[1] + .5 - base[1]
        side = cx * pv[0] + cy * pv[1]
        u = (cx * d[0] + cy * d[1]) / max(1e-6, length)
        # light comes from the upper left: the facet whose normal points left/up is lit
        facing_left = (pv[0] * -1 + pv[1] * -0.6) > 0
        lit_side = (side > 0) == facing_left
        if abs(side) < 0.55:
            c = f"U{ridge}" if u > 0.25 else f"U{ridge - 1}"
        elif lit_side:
            c = ("U4" if u > 0.5 else "U3") if lit >= 0 else "U3"
        else:
            c = "U2" if u > 0.3 else "U1"
        out[q] = c
    if tip_glow:
        out[ip(madd(tip, (d, -0.8)))] = "J5"
    L.fixed(out)
    return set(out)


# =========================================================================== 2. ICE GOLEM (v2: basalt plates)
GO_L = ["BackArm", "BackLeg", "Body", "FrontLeg", "Head", "FrontArm", "Shards", "FX"]
GW, GH = 64, 64
FLOOR_G = 63.0
G_NEU = dict(P=(28.0, 45.0), C=(31.4, 30.0), hdo=(0.0, 0.0), hup=(0.3, -1.0),
             hfF=(49.0, 53.0), hfB=(22.0, 53.5), elF=None, elB=None, ff=(41.0, FLOOR_G), fb=(26.0, FLOOR_G),
             glow=1, slit=1, glint=None, burst=0, smear=None, crack=0, wind=0.0, fistang=None, steam=0,
             impact=None, lift=(0.0, 0.0))
GP_ = mk(G_NEU)
UA, FA = 11.0, 12.5          # upper arm / forearm


def smooth_poly(pts, n=5):
    """Closed Catmull-Rom through pts: smooth curved plate outlines (no staircase corners)."""
    m = len(pts)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


def spindle(a, b, w0, w1, bulge=0.0, curv=0.0, tip0=0.55, tip1=0.55, n=14):
    """Tapered, bevel-ready limb plate from a to b: smooth sides, softly pointed ends, optional sweep (curv)."""
    d = sub(b, a)
    ln = math.hypot(*d) or 1
    d = (d[0] / ln, d[1] / ln)
    pv = (-d[1], d[0])
    L_, R_ = [], []
    for i in range(n + 1):
        t = i / n
        w = (w0 + (w1 - w0) * t) * 0.5 + bulge * 0.5 * math.sin(math.pi * t)
        e0 = min(1.0, t / 0.22)
        e1 = min(1.0, (1 - t) / 0.22)
        f = (tip0 + (1 - tip0) * math.sin(e0 * math.pi / 2)) * (tip1 + (1 - tip1) * math.sin(e1 * math.pi / 2))
        c = madd(a, (d, ln * t), (pv, curv * math.sin(math.pi * t)))
        L_.append(madd(c, (pv, w * f)))
        R_.append(madd(c, (pv, -w * f)))
    return L_ + R_[::-1]


def plate(L, pts, mat, bias=0, tilt=(-0.2, -0.3), bevel=1.8, strength=1.15, ao=1, smooth=True, clip=None):
    m = poly_mask(smooth_poly(pts) if smooth else pts)
    if clip is not None:
        m = {q for q in m if clip(q)}
    L.paint(n_plate(m, bevel, tilt, strength), mat, bias, ao)
    return m


def ice_claw(L, hand, ang, bias, glow, spread=1.0):
    """Gauntlet of glassy ice: a tapered crystal knuckle-block and three sharp talons along the forearm dir."""
    d = dirv(ang)
    pv = (-d[1], d[0])
    F = lambda u, v: madd(hand, (d, u), (pv, v))
    blk = [F(-2.4, -2.6), F(1.6, -3.4), F(4.2, -2.0), F(4.6, 1.2), F(2.2, 3.2), F(-2.2, 2.6)]
    m = poly_mask(smooth_poly(blk, 4))
    L.paint(n_plate(m, 1.4, (-0.15, -0.2), 1.2), "U", bias)
    L.decal([q for q in line(F(0.4, -2.8), F(3.8, -0.6)) if q in m], ("U", 4 if bias >= 0 else 3))
    tips = []
    for k, (da, ln_, w_) in enumerate(((-20 * spread, 5.6, 2.2), (0, 7.2, 2.6), (20 * spread, 5.2, 2.0))):
        a = ang + da
        base = F(3.0, (k - 1) * 1.5)
        ice_shard(L, base, a, ln_, w_, lit=bias, ridge=5 if bias >= 0 else 4)
        tips.append(madd(base, (dirv(a), ln_)))
    if glow:
        c = ip(F(0.6, 0.0))
        L.fixed({c: "J3" if glow >= 2 else "J2", (c[0] - 1, c[1]): "J2" if glow >= 2 else "J1"})
    return m, tips


def golem_arm(L, sh, hand, el_pref, bias, glow, fistang=None):
    el = ik(sh, hand, UA, FA, el_pref)
    L.paint(n_dome(el, 1.9, 1.9), "U", bias - 1)
    plate(L, spindle(sh, lerp(sh, el, 1.0), 4.8, 3.2, bulge=1.0, tip0=0.7, tip1=0.5), "S", bias, (-0.25, -0.35),
          smooth=False)
    fa = sub(hand, el)
    ang = math.degrees(math.atan2(fa[1], fa[0]))
    plate(L, spindle(lerp(el, hand, 0.04), lerp(el, hand, 0.9), 3.0, 4.8, bulge=0.4, tip0=0.5, tip1=0.8), "S", bias,
          (-0.3, -0.15), smooth=False)
    fm, tips = ice_claw(L, hand, ang if fistang is None else fistang, bias, glow)
    return el, fm, tips, ang


def golem_leg(L, hip, toe, bias, lift=0.0):
    """Digitigrade leg: thigh forward to the knee, shin back to a raised hock, long tapered foot to the toe claw."""
    tx, ty = toe
    hock = (tx - 5.0, ty - 5.4 - lift * 0.4)
    kn = ik(hip, hock, 9.0, 8.4, (1, -0.25))
    plate(L, spindle(hip, kn, 5.4, 3.2, bulge=1.2, tip0=0.8, tip1=0.5), "S", bias, (-0.25, -0.3), smooth=False)
    L.paint(n_dome(kn, 1.5, 1.5), "U", bias - 1)
    plate(L, spindle(kn, hock, 3.0, 2.4, bulge=0.3, tip0=0.6, tip1=0.7), "S", bias, (-0.3, -0.15), smooth=False)
    plate(L, spindle(hock, (tx, ty - 0.4), 3.0, 1.6, bulge=0.2, curv=-0.6, tip0=0.8, tip1=0.4), "S", bias,
          (-0.1, -0.5), smooth=False)
    ice_shard(L, (tx - 0.6, ty - 0.2), -8, 2.6, 1.6, lit=bias, ridge=4)          # small ice toe claw
    return kn


def draw_golem(p, fi, sw):
    Ls = {n: Layer(n) for n in GO_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    P, C = p["P"], p["C"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    Hd = F(2.4 + p["hdo"][0], -ln - 6.4 + p["hdo"][1])       # small head sunk low between the shoulder crowns
    gl = p["glow"]
    # ---- legs
    Bl, Fl = Ls["BackLeg"], Ls["FrontLeg"]
    golem_leg(Bl, F(-2.2, 1.0), p["fb"], -2, p["lift"][1])
    golem_leg(Fl, F(2.0, 1.4), p["ff"], 0, p["lift"][0])
    # ---- torso: glassy ice core bound inside carved basalt plates; seams left open so the ice shows
    Bd = Ls["Body"]
    core = [F(-3.0, 2.0), F(-2.8, -6.0), F(-10.0, -ln - 2.0), F(-6.0, -ln - 7.0), F(8.0, -ln - 7.4),
            F(12.4, -ln - 2.4), F(3.2, -6.0), F(3.2, 2.0)]
    cm = poly_mask(smooth_poly(core, 3))
    Bd.paint(n_plate(cm, 2.0, (0.0, 0.0), 0.8), "U", -1)
    # pelvis: a pointed fauld plate
    plate(Bd, [F(-4.6, -1.4), F(4.4, -1.8), F(5.2, 1.0), F(1.0, 4.8), F(-3.6, 2.6)], "S", 0, (-0.2, -0.4))
    # abdomen: two narrow tapered rib plates rising into the chest
    plate(Bd, [F(-2.4, -2.8), F(2.4, -3.0), F(4.2, -8.0), F(7.0, -ln + 3.4), F(-6.2, -ln + 3.0), F(-3.4, -8.0)],
          "S", 0, (-0.2, -0.35), bevel=2.2)
    # chest carapace: one sweeping wedge split by a sternum seam; the front half faces away from the light
    chest = [F(-11.6, -ln - 1.2), F(-7.6, -ln - 6.4), F(0.4, -ln - 7.8), F(8.6, -ln - 7.0), F(12.8, -ln - 2.6),
             F(8.2, -ln + 2.0), F(0.0, -ln + 2.8), F(-7.0, -ln + 2.0)]
    s0, s1 = F(0.0, -ln - 8.0), F(-0.6, -ln + 3.0)
    side = lambda q: (q[0] + .5 - s0[0]) * (s1[1] - s0[1]) - (q[1] + .5 - s0[1]) * (s1[0] - s0[0])
    plate(Bd, chest, "S", 0, (-0.45, -0.35), clip=lambda q: side(q) > 0.7)
    plate(Bd, chest, "S", 0, (0.35, -0.2), clip=lambda q: side(q) < -0.7)
    # the binding ice shows in the seams; frost-light lives deep in it (restrained)
    seam = [q for q in cm if Bd.px.get(q, [None])[0] == "U"]
    heart = ip(F(-0.2, -ln - 1.0))
    info["heart"] = heart
    for q in seam:
        h = hash01(q[0], q[1], 5)
        dh = math.hypot(q[0] - heart[0], q[1] - heart[1])
        if gl and h < 0.12 + 0.12 * gl - dh * 0.02:
            Bd.fixed({q: ("J1", "J2", "J3")[min(2, gl - 1 + (1 if dh < 2.5 else 0))]})
    if gl and heart in Bd.px:
        Bd.fixed({heart: ("J2", "J3", "J4", "J5")[min(3, gl)]})
    # ---- shoulder crowns: sweeping crescent plates grown with sharp ice crystals
    shF = F(12.2, -ln - 3.2)
    shB = F(-10.8, -ln - 2.8)
    Sh = Ls["Shards"]
    crystals = []

    def crown(c, L_, bias, scale, back):
        # a crescent sweeping up and back from the shoulder
        if back:
            a = madd(c, ((1, 0.4), 4.4 * scale))
            b = madd(c, ((-1, -0.9), 6.6 * scale))
        else:
            a = madd(c, ((1, 0.5), 3.8 * scale))
            b = madd(c, ((-0.25, -1), 5.6 * scale))
        plate(L_, spindle(a, b, 6.4 * scale, 1.4, bulge=1.6 * scale, curv=-2.2 * scale, tip0=0.8, tip1=0.3), "S",
              bias, (-0.3, -0.5), smooth=False)
        ridge = [lerp(a, b, 0.35), lerp(a, b, 0.8)]
        return ridge
    rB = crown(shB, Bd, -1, 1.1, True)
    for (k, (a, l_, w_)) in enumerate(((-126, 10.5, 3.4), (-146, 7.0, 2.6), (-108, 6.0, 2.4))):
        crystals.append((lerp(rB[0], rB[1], 0.25 + 0.3 * k), a, l_, w_, -1))
    # ---- head: small low wedge helm with one frost-light slit and a swept-back horn
    Hdl = Ls["Head"]
    G = K.basis(Hd, p["hup"])
    Hdl.paint(n_dome(G(0.0, 2.4), 3.8, 2.2), "U", -1)                     # ice collar the head sinks into
    plate(Hdl, [G(-3.0, 2.2), G(-3.2, -1.2), G(-0.8, -3.4), G(2.6, -3.0), G(6.0, -0.6), G(4.8, 1.2), G(1.4, 2.6)],
          "S", 1, (-0.25, -0.4), bevel=1.2)
    plate(Hdl, spindle(G(-0.4, -2.6), G(-6.4, -5.2), 2.2, 0.6, curv=-0.8, tip0=0.9, tip1=0.3), "S", 0,
          (-0.3, -0.5), bevel=1.0, smooth=False)
    s0_, s1_ = G(1.4, -0.6), G(5.6, -0.4)
    hm = set(Hdl.px)
    slit = [q for q in line(s0_, s1_) if q in hm]
    Hdl.fixed({q: ("J3" if p["slit"] < 2 else "J4") if i < len(slit) - 2 else ("J4" if p["slit"] < 2 else "J5")
               for i, q in enumerate(slit)})
    info["slit"] = G(5.0, -0.5)
    if p["slit"] >= 3:
        star(FX, G(5.6, -0.5), 2)
    # ---- arms
    Ba, Fa = Ls["BackArm"], Ls["FrontArm"]
    shB2 = add(shB, (0.6, 1.8))
    shF2 = add(shF, (-0.4, 1.8))
    elB, fmB, tipB, angB = golem_arm(Ba, shB2, p["hfB"], p["elB"] or (-0.6, 0.3), -2, max(0, gl - 1), p["fistang"])
    elF, fmF, tipF, angF = golem_arm(Fa, shF2, p["hfF"], p["elF"] or (-0.4, 0.2), 0, gl, p["fistang"])
    rF = crown(shF, Fa, 0, 0.95, False)                                   # the front crown sits over the arm
    for (k, (a, l_, w_)) in enumerate(((-100, 7.0, 3.0), (-78, 4.6, 2.2))):
        crystals.append((lerp(rF[0], rF[1], 0.6 - 0.4 * k), a, l_, w_, 0))
    info["fists"] = (p["hfF"], p["hfB"])
    info["claws"] = tipF + tipB
    fist_px = {q for q in Fa.px if Fa.px[q][0] == "U" or isinstance(Fa.px[q][3], str)} | \
              {q for q in Ba.px if Ba.px[q][0] == "U" or isinstance(Ba.px[q][3], str)}
    info["hit"] |= {q for q in fist_px if math.hypot(q[0] - p["hfF"][0], q[1] - p["hfF"][1]) < 10
                    or math.hypot(q[0] - p["hfB"][0], q[1] - p["hfB"][1]) < 10}
    for base, a, l_, w_, bias in crystals:
        ice_shard(Sh, base, a, l_, w_, lit=bias, ridge=4 if bias >= 0 else 3)
    # rim light on stone edges facing up so the dark stone separates from the dark background
    for L_ in (Bd, Fa, Fl):
        rim(L_, ("S",), 4)
    rim(Hdl, ("S",), 5)
    # ---- cracks (death)
    if p["crack"]:
        for L_ in (Bd, Fa, Fl, Hdl):
            pts = sorted(L_.px)
            for k in range(1 + p["crack"]):
                if not pts:
                    break
                cur = pts[int(hash01(k, 3, 77) * len(pts))]
                for j in range(3 + p["crack"] * 2):
                    if cur in L_.px and L_.px[cur][0] == "S":
                        L_.fixed({cur: "J3" if p["crack"] >= 2 and j % 2 == 0 else "J2"})
                    cur = (cur[0] + (1 if hash01(k, j, 78) > 0.4 else -1), cur[1] + (1 if hash01(k, j, 79) > 0.5 else 0))
    # ---- fx
    if p["glint"]:
        for c in p["glint"]:
            star(FX, c, 3)
        info["glint"] = p["glint"][0]
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= swept(FX, g0, a0, g1, a1, u0, u1, hw=1.3, pal="rime", taper=0.3, exclude=set(Fa.px))
    if p["burst"]:
        info["impact"] = impact_burst(Sh, FX, p["impact"], p["burst"], fi)
        info["hit"] |= info["impact"]
    if p["steam"]:
        for k in range(10):
            t = (k / 10 + fi * 0.13) % 1.0
            x = p["impact"][0] + (hash01(k, 1, 5) - 0.5) * 16
            FX.put([ip((x + math.sin(k + t * 4) * 1.2, FLOOR_G - 1 - t * 8 * p["steam"]))], "J1" if t < 0.5 else "X3")
    return Ls, info


def impact_burst(Sh, FX, at, stage, fi):
    """Ice bursting out of the floor where the fists land (stage 1 flash + low shards, 2 tall shards, 3 crumble)."""
    x0 = at[0]
    pts = set()
    spec = [(-8.0, -118, 5.0, 2.8), (4.0, -86, 8.0, 3.6), (7.6, -68, 11.0, 4.2), (11.2, -54, 7.5, 3.4),
            (-4.6, -104, 6.5, 3.0)]
    sc = {1: 0.55, 2: 1.0, 3: 0.7, 4: 0.35}[stage]
    for k, (dx, a, l_, w_) in enumerate(spec):
        l2 = l_ * sc * (0.85 + 0.3 * hash01(k, stage, 4))
        if l2 < 1.5:
            continue
        pts |= ice_shard(Sh, (x0 + dx, FLOOR_G + 1.0), a, l2, w_ * (0.8 if stage >= 3 else 1.0),
                         tip_glow=stage == 2 and k in (1, 2, 3))
    for k in range(16 if stage < 4 else 9):
        u = hash01(k, stage, 21)
        x = x0 + (u - 0.5) * (14 + stage * 7)
        y = FLOOR_G - hash01(k, stage, 22) * (3 + stage * 2.2) * (1 - abs(u - 0.5))
        q = ip((x, y))
        FX.put([q], ("J4", "J3", "J2")[k % 3] if stage == 1 else ("J2", "J1", "X3")[k % 3])
        pts.add(q)
    if stage == 1:
        star(FX, (x0, FLOOR_G - 2), 4)
        disc_glow(FX, (x0 + .5, FLOOR_G - 1.5), 2.6, ("J5", "J4", "J3"))
    for k in range(8):
        a = -math.pi * (0.1 + 0.8 * hash01(k, 7, 31))
        r = (3 + 8 * hash01(k, 8, 31)) * (0.6 + 0.4 * stage)
        q = ip((x0 + math.cos(a) * r * 1.3, FLOOR_G - 2 + math.sin(a) * r * (1.0 if stage < 3 else 0.6) + (stage - 1) * 2))
        if stage < 4:
            FX.put([q], "U5" if k % 2 else "J4")
    return {q for q in pts if 0 <= q[1] < K.H}


def g_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        fr.append((220, GP_(C=(31.4, 30.0 + b * 0.5), hfF=(49.0 + b * 0.2, 53.0 + b * 0.4),
                            hfB=(22.0 - b * 0.2, 53.5 + b * 0.3), glow=1 + (i == 2), slit=1)))
    return fr


def g_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        lift = max(0.0, s_)
        liftb = max(0.0, -s_)
        bob = 0.9 * abs(c)
        fr.append((160, GP_(P=(28.0 + 0.4 * c, 45.0 + bob), C=(31.8 + 0.6 * c, 30.0 + bob),
                            ff=(34.0 + 7.5 * c, FLOOR_G - 2.6 * lift), fb=(33.0 - 7.5 * c, FLOOR_G - 2.6 * liftb),
                            lift=(lift * 3, liftb * 3),
                            hfF=(48.0 - 2.6 * c, 53.0 + bob - 0.8 * abs(s_)), hfB=(23.0 + 2.6 * c, 53.5 + bob),
                            glow=1, wind=-1.0)))
    return fr


def g_slam():
    up_ = dict(P=(27.0, 45.4), C=(29.0, 29.8), hup=(0.05, -1))
    arch = dict(P=(26.6, 45.6), C=(27.6, 29.8), hup=(-0.15, -1))
    lung = dict(P=(29.6, 46.4), C=(36.4, 33.6), hup=(0.7, -1))
    low = dict(P=(30.4, 48.0), C=(39.4, 37.0), hup=(1.0, -1), ff=(42.0, FLOOR_G), fb=(24.0, FLOOR_G))
    IMP = (53.0, FLOOR_G)
    return [
        (140, GP_(P=(27.8, 45.8), C=(30.8, 31.0), hfF=(42.0, 46.0), hfB=(27.0, 47.0), glow=1)),
        (130, GP_(**up_, hfF=(40.0, 34.0), hfB=(32.0, 36.0), elF=(1, 0.3), elB=(1, 0.2), glow=1, fistang=-40)),
        (130, GP_(**up_, hfF=(38.0, 20.0), hfB=(32.0, 21.0), elF=(1, 0.0), elB=(1, -0.2), glow=2, fistang=-80)),
        (130, GP_(**arch, hfF=(34.0, 13.0), hfB=(30.0, 14.0), elF=(1, 0.2), elB=(1, 0.0), glow=2, fistang=-95)),
        (160, GP_(**arch, hfF=(32.4, 11.4), hfB=(29.0, 12.4), elF=(1, 0.3), elB=(1, 0.1), glow=2, fistang=-100)),
        (380, GP_(**arch, hfF=(32.0, 11.0), hfB=(28.6, 12.0), elF=(1, 0.3), elB=(1, 0.1), glow=3, slit=3, fistang=-102,
                  glint=[(33.0, 3.4)])),
        (70, GP_(**lung, hfF=(49.0, 28.0), hfB=(45.0, 30.0), elF=(-0.2, -1), elB=(-0.2, -1), glow=3, slit=2, fistang=-10,
                 smear=[((38.0, 30.0), -110, (38.4, 30.4), -40, 15.0, 22.0)], wind=4)),
        (90, GP_(**low, hfF=(51.0, 54.0), hfB=(47.0, 54.6), elF=(-0.4, -1), elB=(-0.4, -1), glow=3, slit=2, fistang=80,
                 smear=[((39.4, 33.0), -40, (39.6, 33.2), 45, 15.0, 22.0)], burst=1, impact=IMP, wind=3)),
        (110, GP_(**low, hfF=(51.0, 54.4), hfB=(47.0, 55.0), elF=(-0.4, -1), elB=(-0.4, -1), glow=2, fistang=82,
                  burst=2, impact=IMP)),
        (150, GP_(**low, hfF=(50.6, 54.6), hfB=(46.6, 55.0), elF=(-0.4, -1), elB=(-0.4, -1), glow=2, fistang=84,
                  burst=3, impact=IMP, steam=1)),
        (160, GP_(P=(29.0, 46.4), C=(34.0, 32.0), hup=(0.5, -1), hfF=(48.0, 51.6), hfB=(41.0, 52.6),
                  glow=1, burst=4, impact=IMP, steam=2)),
        (180, GP_(P=(28.4, 45.4), C=(32.2, 30.6), hup=(0.35, -1), hfF=(47.0, 50.6), hfB=(26.0, 51.0), glow=1)),
    ]


def g_swipe():
    tw = dict(P=(27.0, 45.4), C=(27.8, 30.6), hup=(0.1, -1))
    fwd = dict(P=(29.4, 45.8), C=(34.4, 31.2), hup=(0.55, -1), ff=(40.0, FLOOR_G))
    return [
        (130, GP_(P=(27.4, 45.4), C=(29.8, 30.4), hfF=(38.0, 48.0), hfB=(20.0, 48.0), glow=1)),
        (130, GP_(**tw, hfF=(22.0, 46.0), hfB=(16.0, 46.0), elF=(0.2, -1), glow=1, fistang=170)),
        (260, GP_(**tw, hfF=(16.4, 42.0), hfB=(15.0, 47.0), elF=(0.4, -1), glow=2, slit=3, fistang=190,
                  glint=[(12.0, 41.0)])),
        (90, GP_(**tw, hfF=(18.0, 48.0), hfB=(16.0, 47.0), elF=(0.4, -1), glow=2, fistang=150,
                 smear=[((36.0, 28.0), 145, (36.0, 28.0), 128, 17.0, 24.0)], wind=2)),
        (70, GP_(**fwd, hfF=(52.0, 50.0), hfB=(22.0, 48.0), elF=(0.0, 1), glow=2, fistang=15,
                 smear=[((43.0, 29.0), 130, (43.0, 29.0), 40, 17.0, 25.0)], wind=4)),
        (80, GP_(**fwd, hfF=(58.0, 38.0), hfB=(24.0, 48.0), elF=(0.0, 1), glow=2, fistang=-25,
                 smear=[((43.0, 29.0), 40, (43.0, 29.0), -25, 17.0, 25.0)], wind=3)),
        (140, GP_(**fwd, hfF=(56.0, 42.0), hfB=(24.0, 49.0), elF=(0.0, 1), glow=1, fistang=-10)),
        (160, GP_(P=(28.4, 45.4), C=(32.2, 30.4), hup=(0.35, -1), hfF=(50.0, 47.0), hfB=(22.6, 50.0), glow=1)),
        (170, GP_(hfF=(49.0, 52.6), glow=1)),
    ]


def g_hurt():
    return [(90, GP_(P=(26.8, 45.2), C=(27.6, 29.6), hup=(-0.3, -1), hfF=(42.0, 50.0), hfB=(18.0, 50.0),
                     glow=3, slit=3)),
            (150, GP_(P=(27.6, 45.2), C=(30.2, 30.0), hup=(0.1, -1), hfF=(45.0, 50.4), hfB=(20.0, 50.6),
                      glow=2, slit=2))]


GBODY = ["BackArm", "BackLeg", "Body", "FrontLeg", "Head", "FrontArm", "Shards"]


def g_shatter(t, seed=4):
    return lambda imgs: shatter(imgs, GBODY, t, seeds=22, seed=seed, floor=int(FLOOR_G), spread=0.55, target="Body")


def g_death():
    kneel = dict(P=(28.0, 51.0), C=(32.0, 37.4), hup=(0.6, -1), hfF=(44.0, 57.0), hfB=(23.0, 57.6),
                 ff=(40.0, FLOOR_G), fb=(24.0, FLOOR_G))
    return [
        (120, GP_(P=(26.8, 45.2), C=(26.8, 29.8), hup=(-0.4, -1), hfF=(40.0, 50.0), hfB=(17.0, 50.0),
                  glow=3, slit=3, crack=1)),
        (160, GP_(P=(27.4, 48.0), C=(30.0, 33.6), hup=(0.3, -1), hfF=(42.0, 54.0), hfB=(21.0, 54.4),
                  glow=2, slit=2, crack=2)),
        (160, GP_(**kneel, glow=2, slit=2, crack=3)),
        (100, GP_(**kneel, glow=2, slit=1, crack=3, post=g_shatter(0.25))),
        (100, GP_(**kneel, glow=2, slit=1, crack=3, post=g_shatter(0.55))),
        (120, GP_(**kneel, glow=1, slit=0, crack=3, post=g_shatter(0.85))),
        (200, GP_(**kneel, glow=1, slit=0, crack=3, post=g_shatter(1.0), steam=1, impact=(31.0, FLOOR_G))),
        (700, GP_(**kneel, glow=0, slit=0, crack=2, post=g_shatter(1.0), steam=2, impact=(31.0, FLOOR_G))),
    ]


def build_golem():
    K.setup(GW, GH)
    anims, infos = render_anims(SPEC["hf_golem"], GO_L, draw_golem,
                                [("idle", g_idle), ("walk", g_walk), ("slam", g_slam), ("swipe", g_swipe),
                                 ("hurt", g_hurt), ("death", g_death)], sway_key="C", loops=("idle", "walk"))
    # every body pixel must stay inside the frame (no clipping at the top on the raised slam)
    for tag, frs in anims:
        for k, (ms, imgs) in enumerate(frs):
            box = K.opaque_bbox(imgs, GBODY)
            if box and box[1] <= 0:
                print(f"  WARN hf_golem {tag}[{k}] touches the top edge: {box}")
    meta = {"native": 1, "frame": [GW, GH], "anchor": [29, GH],
            "hurtbox": hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(3, 3, 3)),
            "attacks": {"slam": {"active": [7, 8], "hit": hit_rect(infos, "slam", [7, 8], x_min=40)},
                        "swipe": {"active": [4, 5], "hit": hit_rect(infos, "swipe", [4, 5], x_min=37)}},
            "spawn": {"slam": {"frame": 7, "at": [53, GH - 1]}},
            "telegraph": {"slam": {"frame": 5, "at": spawn_pt(infos["slam"][5]["glint"])},
                          "swipe": {"frame": 2, "at": spawn_pt(infos["swipe"][2]["glint"])}},
            "notes": "faces right; slow heavy sentinel of basalt plates bound by ice. slam: both ice claws hoisted "
                     "overhead 0-5 (5 = long held telegraph glint), smashed down 6, floor impact + ice burst on "
                     "active 7-8 (spawn fx_hf_frostwave at spawn.slam.at, frame 7), slow recovery 9-11. swipe: arm "
                     "wound back 0-3 (2 = held, glint), wide low backhand sweep active 4-5, recovery 6-8. death: "
                     "cracks glow, kneels, shatters into a pile of stone and ice (7 = settled)."}
    export("hf_golem", GO_L, anims, meta)
    return meta


# =========================================================================== 3. UNDER-ICE LURKER
LU_L = ["ArmBack", "Body", "Head", "ArmFront", "Shards", "FX"]
LW, LH = 56, 40
SURF = LH - 1        # bottom row = water surface / floor line
LSC = 1.2            # pose scale: poses are authored for a 48x32 layout and mapped up around the surface


def LX(q):
    return (22.0 + (q[0] - 19.0) * LSC, LH - (32.0 - q[1]) * LSC)
L_NEU = dict(sp=[(19.0, 40.0), (18.6, 31.0), (19.6, 23.4), (22.6, 16.8), (26.4, 11.8)], rad=[4.9, 4.4, 3.6, 2.8, 2.3],
             Hh=(28.6, 9.8), ha=10.0, jaw=0.0, hF=(28.6, 23.4), hB=(25.6, 25.4), cF=78.0, cB=86.0, sink=0.0,
             glow=1, foam=1, spray=0, streak=0, glint=False, lurk=False, bub=0, splash=0, limp=0.0, wind=0.0,
             C=0.0)
LPp = mk(L_NEU)


def lurker_claws(L, h, ang, bias, n=3, ln=4.6):
    pts_all = []
    for k, (da, cl) in enumerate(((-20, ln * 0.9), (0, ln), (20, ln * 0.8))[:n]):
        dd = dirv(ang + da)
        pts = []
        for j in range(int(cl * 2) + 1):
            u = j / 2
            hook = 0.08 * u * u
            pts.append(ip((h[0] + dd[0] * (u + 0.6) - dd[1] * hook, h[1] + dd[1] * (u + 0.6) + dd[0] * hook)))
        pts = list(dict.fromkeys(pts))[1:]
        L.fill(pts, None)
        for j, q in enumerate(pts):
            if q not in L.px:
                continue
            L.px[q][3] = ("U5" if j == len(pts) - 1 and bias >= 0 else "U4" if bias >= 0 else "U3") \
                if j >= len(pts) - 2 else ("E4" if bias >= 0 else "E3")
            L.noout.add(q)
        pts_all += pts
    return pts_all


def draw_lurker(p, fi, sw):
    Ls = {n: Layer(n) for n in LU_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    dy = p["sink"] * LSC
    D = lambda q: (LX(q)[0], LX(q)[1] + dy)
    sp = [D(q) for q in p["sp"]]
    Hh = D(p["Hh"])
    # ---- body: sinuous tube rising out of the pool
    Bd = Ls["Body"]
    cp, rr = resample(sp + [Hh], p["rad"] + [p["rad"][-1] * 0.85])
    Bd.paint(n_tube(cp, rr), "E", 0)
    # ventral scutes (paler belly plates) on the front side, darker veins, spine glow + dorsal fin on the back
    fin, glow_pts, belly = [], [], []
    for i in range(1, len(cp) - 1):
        a, b = cp[i - 1], cp[i + 1]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        tx, ty = tx / l, ty / l
        nx, ny = ty, -tx          # left of travel (travel is upward -> left normal points... right/front)
        if nx < 0:
            nx, ny = -nx, -ny     # force the normal to point to the front (+x)
        r = rr[i]
        fr = ip((cp[i][0] + nx * (r - 0.9), cp[i][1] + ny * (r - 0.9)))
        belly.append((i, fr))
        bk = ip((cp[i][0] - nx * (r - 1.0), cp[i][1] - ny * (r - 1.0)))
        glow_pts.append((i, bk))
        fin.append((i, ip((cp[i][0] - nx * (r + 0.6), cp[i][1] - ny * (r + 0.6)))))
    for i, q in belly:                                # a smooth pale belly stripe
        if q in Bd.px:
            Bd.decal([q], ("E", 4))
    for i, q in glow_pts:                             # cold bioluminescent line down the spine
        if q in Bd.px and i % 4 == 0 and p["glow"]:
            Bd.fixed({q: ("J1", "J2", "J3", "J3")[min(3, p["glow"])]})
    for i, q in fin:                                  # translucent dorsal fin membrane along the neck
        t = i / len(cp)
        if 0.4 < t < 0.92 and q not in Bd.px:
            FX.put([q], "J1" if i % 4 == 0 else "U2")
    info["hit"] |= {q for q in Bd.px if q[1] < SURF - 2}
    # ---- head: eyeless narrow skull, hinged jaw of glassy ice teeth
    Hd = Ls["Head"]
    G = lambda x, y: add(Hh, rot((x * 1.32, y * 1.3), p["ha"]))
    ja = p["jaw"] * 46.0
    hinge = (-0.4, 0.9)
    J = lambda x, y: G(*add(hinge, rot(sub((x, y), hinge), ja)))
    if p["jaw"] > 0.12:
        gul = poly_mask([G(-0.6, 0.8), G(9.8, 0.6), J(9.0, 1.2), J(0.0, 1.6)])
        hc = G(-0.2, 1.1)
        Hd.fixed({q: "J1" if math.hypot(q[0] + .5 - hc[0], q[1] + .5 - hc[1]) < 2.2 else "S1" for q in gul})
    jaw = [J(-1.4, 0.9), J(9.4, 0.9), J(8.8, 2.2), J(3.0, 3.3), J(-1.6, 2.8)]
    jm = poly_mask(jaw)
    Hd.paint(n_plate(jm, 0.8, (0.0, 0.3)), "E", 0)
    skull = [G(-2.8, -1.6), G(-0.6, -2.8), G(3.4, -2.6), G(7.8, -1.2), G(10.6, 0.0), G(10.2, 0.8), G(1.0, 1.0),
             G(-2.8, 1.8)]
    sm = poly_mask(skull)
    Hd.paint(n_plate(sm, 1.3, (-0.2, -0.3), 1.1), "E", 1)
    Hd.decal([q for q in line(G(-1.0, 0.6), G(8.0, 0.4)) if q in sm], ("E", 2))       # lip line
    # eyeless: a row of faint sensory pits instead of eyes
    for k, x in enumerate((1.4, 3.2, 5.0)):
        q = ip(G(x, -1.2 + k * 0.15))
        if q in sm:
            Hd.fixed({q: "J3" if (p["glow"] >= 2 and k == 0) else "J2" if p["glow"] else "E1"})
    teeth = {}
    if p["jaw"] > 0.12:
        for k, x in enumerate((2.0, 3.8, 5.6, 7.4, 9.0)):
            teeth[ip(G(x, 1.2))] = "U5" if k % 2 else "J4"
            if k in (1, 3):
                teeth[ip(G(x, 1.9))] = "U4"
        for k, x in enumerate((2.8, 4.8, 6.8, 8.4)):
            teeth[ip(J(x, 0.6))] = "U4" if k % 2 else "U5"
    else:
        for x in (3.0, 5.4, 7.6):
            teeth[ip(G(x, 1.2))] = "U4"
    Hd.fixed(teeth)
    rim(Hd, ("E",), 5)
    rim(Bd, ("E",), 4, side=(-1, 0))
    info["hit"] |= set(Hd.px)
    info["jaw"] = G(10.4, 0.8)
    info["teeth"] = G(6.0, 1.2)
    # ---- forelimbs: long thin arms with hooked glass claws
    def arm(L, sh, hand, cang, bias):
        el = ik(sh, hand, 7.8, 8.2, (-0.6, 0.8))
        L.paint(n_tube([sh, el], [1.7, 1.3]), "E", bias)
        L.paint(n_tube([el, hand], [1.3, 1.0]), "E", bias)
        L.paint(n_dome(hand, 1.2, 1.1), "E", bias, ao=0)
        return lurker_claws(L, hand, cang, bias, ln=5.8)
    ti = int(len(cp) * 0.42)
    shp = cp[ti]
    shF = (shp[0] + rr[ti] * 0.6, shp[1] + 0.5)
    shB = (shp[0] + rr[ti] * 0.2, shp[1] + 1.4)
    cb = arm(Ls["ArmBack"], shB, D(p["hB"]), p["cB"], -2)
    cf = arm(Ls["ArmFront"], shF, D(p["hF"]), p["cF"], 0)
    info["hit"] |= set(Ls["ArmFront"].px) | set(cf)
    info["claws"] = cf
    # ---- water: foam where the body breaks the surface, ripples, bubbles, spray
    xs = [q[0] for q in Bd.px if q[1] >= SURF - 1]
    if p["foam"] and xs:
        x0, x1 = min(xs) - 2, max(xs) + 2
        for x in range(x0 - 3, x1 + 4):
            inside = x0 <= x <= x1
            if inside or (x + fi) % 2 == 0:
                FX.put([(x, SURF)], "U4" if inside and (x + fi) % 3 else "J2" if inside else "U3")
            if inside and (x * 3 + fi) % 4 == 0:
                FX.put([(x, SURF - 1)], "U5" if x % 2 else "J3")
        for k in range(2):
            rx = x1 + 5 + k * 5 + (fi % 2)
            lx = x0 - 5 - k * 5 - (fi % 2)
            for x in (rx, rx + 1, lx, lx - 1):
                FX.put([(x, SURF)], "U3" if k == 0 else "U2")
    if p["splash"]:
        cx = (min(xs) + max(xs)) / 2 if xs else 22
        st = p["splash"]
        for k in range(12):
            a = -math.pi * (0.12 + 0.76 * hash01(k, 1, 51))
            r = (2 + 7 * hash01(k, 2, 51)) * (0.6 + 0.35 * st)
            q = ip((cx + math.cos(a) * r * 1.4, SURF - 1 + math.sin(a) * r * (1.0 if st < 3 else 0.5) + (st - 1) * 1.5))
            if q[1] <= SURF:
                FX.put([q], ("U5", "J3", "U4")[k % 3] if st < 3 else ("U3", "J2")[k % 2])
    if p["spray"]:
        cx = (min(xs) + max(xs)) / 2 if xs else 20
        st = p["spray"]
        for k in range(18):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 3, 61))
            r = (3 + 12 * hash01(k, 4, 61)) * (0.55 + 0.3 * st)
            q = ip((cx + math.cos(a) * r * 1.2, SURF - 2 + math.sin(a) * r + (st - 1) * st * 1.6))
            if q[1] <= SURF:
                FX.put([q], ("U5", "J4", "U4", "J3")[k % 4] if st < 3 else ("U4", "J2", "U3")[k % 3])
        for k, (dx, a, l_) in enumerate(((-7, -128, 5.0), (6, -58, 6.0), (-3, -104, 4.0), (10, -40, 3.5))):
            off = (st - 1) * 3.0
            b = (cx + dx + math.cos(math.radians(a)) * off, SURF + 1 + math.sin(math.radians(a)) * off * 1.4
                 + (st - 1) ** 2 * 1.2)
            ice_shard(Ls["Shards"], b, a, l_ * (1.0 if st < 3 else 0.7), 2.2)
    if p["bub"]:
        for k in range(3):
            t = (fi * 0.3 + k * 0.37) % 1.0
            x = 12 + k * 8 + int(hash01(k, 1, 71) * 5)
            y = SURF - int(t * 4)
            FX.put([(x, y)], "U4" if t < 0.5 else "U3")
            if t > 0.6:
                FX.put([(x - 1, SURF), (x + 1, SURF)], "U3")
    if p["streak"]:
        for k, y in enumerate((8, 12, 16, 20)[:3 + p["streak"] - 1]):
            yy = int(Hh[1]) - 3 + k * 3
            a = int(Hh[0]) - 14 + (k * 3) % 5
            for x in range(a, a + 8 - k):
                if (x, yy) not in Bd.px and (x, yy) not in Hd.px:
                    FX.put([(x, yy)], "J2" if x > a + 3 else "J1")
    if p["glint"]:
        star(FX, info["teeth"], 1, diag=False)
        info["glint"] = info["teeth"]
    return Ls, info


def submerged(imgs):
    """Lurk: everything under the surface becomes a dark silhouette (no outline), only the spine glow survives."""
    out = dict(imgs)
    W, H = K.W, K.H
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in ("ArmBack", "Body", "Head", "ArmFront"):
        if n in imgs:
            comp.alpha_composite(imgs[n])
            out[n] = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    src = comp.load()
    res = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rp = res.load()
    glow = {K.RGBA[k][:3] for k in ("J1", "J2", "J3", "J4")}
    for y in range(H):
        for x in range(W):
            c = src[x, y]
            if not c[3]:
                continue
            if c[:3] in glow:
                rp[x, y] = K.RGBA["J2" if y >= SURF else "J1"]
            else:
                lum = c[0] + c[1] + c[2]
                rp[x, y] = K.RGBA["E1" if lum > 150 and y == SURF - 2 else "S1" if lum > 60 else "S0"]
    out["Body"] = res
    return out


LURK = dict(sp=[(2.0, 36.0), (10.0, 34.2), (19.0, 33.4), (27.0, 33.2)], rad=[2.6, 3.0, 3.2, 2.8],
            Hh=(29.0, 32.6), ha=2.0, hF=(33.0, 36.0), hB=(30.0, 36.5), cF=10, cB=10, foam=0)


def u_lurk():
    fr = []
    for i in range(4):
        w = math.sin(i * math.pi / 2)
        sp = [(x, y + (0.3 * math.sin(i * math.pi / 2 + x * 0.2))) for x, y in LURK["sp"]]
        fr.append((220, LPp(**dict(LURK, sp=sp, Hh=(29.0 + w * 0.5, 32.6)), bub=1, glow=1 + (i == 1),
                            post=submerged)))
    return fr


IDLE_SP = [(19.0, 40.0), (18.6, 31.0), (19.6, 23.4), (22.6, 16.8), (26.4, 11.8)]


def sway(sp, dx, dy=0.0):
    n = len(sp)
    return [(x + dx * (i / (n - 1)) ** 1.5, y + dy * (i / (n - 1))) for i, (x, y) in enumerate(sp)]


def u_idle():
    fr = []
    for i in range(4):
        a = i * math.pi / 2
        dx, dy = math.sin(a) * 1.2, math.cos(a) * 0.4
        fr.append((180, LPp(sp=sway(IDLE_SP, dx, dy), Hh=(28.6 + dx, 9.8 + dy), ha=10 + math.sin(a + 0.6) * 5,
                            hF=(28.6 + dx * 0.6, 23.4 + math.sin(a + 1) * 0.8), hB=(25.6 + dx * 0.5, 25.4), C=dx,
                            glow=1 + (i == 1))))
    return fr


def u_emerge():
    strike = [(19.0, 40.0), (19.2, 31.0), (22.0, 24.2), (27.6, 18.4), (32.0, 14.6)]
    return [
        (90, LPp(sp=IDLE_SP, Hh=(26.0, 11.0), ha=-70, sink=21.0, hF=(22, 30), hB=(20, 30), splash=1, foam=1)),
        (70, LPp(sp=sway(IDLE_SP, -1.0), Hh=(27.2, 9.2), ha=-62, sink=8.0, hF=(24.0, 24.0), hB=(22.0, 25.0),
                 cF=-60, cB=-70, spray=1, jaw=0.2, glow=2)),
        (80, LPp(sp=[(19.0, 40.0), (18.0, 31.0), (17.8, 23.0), (19.4, 15.6), (22.6, 9.4)], Hh=(24.6, 6.4), ha=-18,
                 hF=(26.4, 17.0), hB=(24.0, 18.6), cF=-20, cB=-10, jaw=0.7, spray=2, glow=2)),
        (70, LPp(sp=strike, Hh=(33.6, 12.6), ha=8, jaw=1.0, hF=(36.0, 25.4), hB=(33.0, 27.0), cF=30, cB=40,
                 spray=3, glow=2, streak=1, wind=4)),
        (90, LPp(sp=strike, Hh=(34.4, 13.6), ha=14, jaw=0.08, hF=(37.4, 28.0), hB=(34.4, 29.0), cF=70, cB=80,
                 glow=2, streak=1, wind=3)),
        (140, LPp(sp=sway(IDLE_SP, 3.0), Hh=(30.8, 11.0), ha=14, hF=(31.0, 24.0), hB=(27.6, 25.6), glow=1)),
        (160, LPp(sp=sway(IDLE_SP, 0.8), Hh=(29.2, 10.2), ha=11, hF=(29.2, 23.6), glow=1)),
    ]


def u_grab():
    coil1 = [(19.0, 40.0), (18.2, 31.0), (17.0, 23.4), (16.6, 17.0), (18.2, 12.4)]
    coil2 = [(19.0, 40.0), (18.0, 31.0), (16.0, 23.6), (14.6, 17.6), (15.4, 12.8)]
    lunge = [(19.0, 40.0), (20.0, 32.0), (23.0, 25.6), (27.6, 20.8), (31.8, 18.0)]
    return [
        (140, LPp(sp=coil1, Hh=(20.4, 10.0), ha=18, jaw=0.2, hF=(24.0, 17.4), hB=(22.0, 19.2), cF=30, cB=40)),
        (140, LPp(sp=coil2, Hh=(17.6, 10.4), ha=22, jaw=0.5, hF=(21.6, 15.6), hB=(19.6, 17.6), cF=10, cB=20, glow=2)),
        (280, LPp(sp=[(x - 0.4, y + 0.3) for x, y in coil2], Hh=(17.0, 10.8), ha=24, jaw=0.75, hF=(21.0, 15.0),
                  hB=(19.0, 17.0), cF=0, cB=10, glow=3, glint=True)),
        (70, LPp(sp=sway(IDLE_SP, 4.0), Hh=(28.6, 13.4), ha=18, jaw=0.9, hF=(31.0, 20.0), hB=(28.0, 22.0), cF=20, cB=30,
                 glow=3, streak=1, wind=3)),
        (70, LPp(sp=lunge, Hh=(34.4, 16.8), ha=18, jaw=1.0, hF=(36.4, 27.4), hB=(33.6, 28.6), cF=20, cB=30, glow=2,
                 streak=2, wind=4)),
        (80, LPp(sp=lunge, Hh=(34.8, 17.8), ha=24, jaw=0.08, hF=(38.4, 28.6), hB=(35.6, 29.4), cF=60, cB=70, glow=2)),
        (100, LPp(sp=lunge, Hh=(34.4, 18.0), ha=24, jaw=0.08, hF=(38.0, 29.4), hB=(35.2, 29.8), cF=85, cB=90, glow=1)),
        (140, LPp(sp=sway(IDLE_SP, 3.0), Hh=(31.0, 12.0), ha=16, hF=(32.0, 24.0), hB=(29.0, 25.6), glow=1)),
        (160, LPp(sp=sway(IDLE_SP, 0.8), Hh=(29.2, 10.2), ha=11, hF=(29.2, 23.6), glow=1)),
    ]


def u_submerge():
    return [
        (100, LPp(sp=sway(IDLE_SP, 1.5), Hh=(29.6, 12.6), ha=40, sink=3.0, hF=(28.0, 26.0), hB=(25.0, 27.0), jaw=0.1)),
        (80, LPp(sp=sway(IDLE_SP, 2.0), Hh=(29.4, 14.0), ha=62, sink=10.0, hF=(26.0, 27.0), hB=(24.0, 28.0),
                 splash=1)),
        (80, LPp(sp=sway(IDLE_SP, 2.0), Hh=(28.6, 15.6), ha=80, sink=19.0, hF=(26.0, 27.0), hB=(24.0, 28.0),
                 splash=2)),
        (100, LPp(sp=IDLE_SP, Hh=(27.6, 16.0), ha=86, sink=27.0, splash=3, foam=1)),
        (160, LPp(sp=IDLE_SP, Hh=(27.6, 16.0), ha=86, sink=45.0, foam=0, bub=1, splash=0)),
    ]


def u_hurt():
    return [(90, LPp(sp=sway(IDLE_SP, -3.0, 1.0), Hh=(23.4, 10.6), ha=-30, jaw=0.6, hF=(26.0, 22.0), hB=(23.0, 24.0),
                     cF=40, glow=3)),
            (140, LPp(sp=sway(IDLE_SP, -1.2), Hh=(26.6, 10.2), ha=-4, jaw=0.2, hF=(27.4, 23.0), glow=2))]


def lurk_fade(frac, seed=0):
    return lambda imgs: frost_dissolve(imgs, frac, ["ArmBack", "Body", "Head", "ArmFront"], seed=seed, rise=8, drift=1,
                                       pal=("J4", "J3", "U4", "J2", "J1"), bottom_up=False)


def u_death():
    limp = [(19.0, 40.0), (19.4, 31.0), (21.4, 24.0), (25.6, 19.4), (29.6, 18.4)]
    return [
        (100, LPp(sp=sway(IDLE_SP, -3.6, 1.0), Hh=(22.6, 10.8), ha=-40, jaw=1.0, hF=(26.0, 21.0), hB=(23.0, 23.0),
                  cF=0, glow=3)),
        (130, LPp(sp=limp, Hh=(31.0, 19.4), ha=60, jaw=0.5, hF=(28.0, 27.0), hB=(25.0, 28.0), cF=100, cB=100, glow=1,
                  sink=2.0)),
        (130, LPp(sp=limp, Hh=(31.4, 20.4), ha=70, jaw=0.4, hF=(28.0, 27.0), hB=(25.0, 28.0), cF=100, cB=100, glow=1,
                  sink=7.0, splash=1, post=lurk_fade(0.2, 2))),
        (140, LPp(sp=limp, Hh=(31.4, 20.4), ha=74, jaw=0.4, hF=(28.0, 27.0), hB=(25.0, 28.0), cF=100, cB=100, glow=0,
                  sink=13.0, splash=2, post=lurk_fade(0.45, 2))),
        (150, LPp(sp=limp, Hh=(31.4, 20.4), ha=78, jaw=0.4, hF=(28.0, 27.0), hB=(25.0, 28.0), cF=100, cB=100, glow=0,
                  sink=19.0, splash=3, post=lurk_fade(0.7, 2))),
        (600, LPp(sp=limp, Hh=(31.4, 20.4), ha=80, glow=0, sink=40.0, foam=0, bub=1, post=lurk_fade(1.1, 2))),
    ]


def build_lurker():
    K.setup(LW, LH)
    anims, infos = render_anims(SPEC["hf_lurker"], LU_L, draw_lurker,
                                [("lurk", u_lurk), ("emerge", u_emerge), ("idle", u_idle), ("grab", u_grab),
                                 ("submerge", u_submerge), ("hurt", u_hurt), ("death", u_death)],
                                sway_key="C", loops=("lurk", "idle"))
    meta = {"native": 1, "frame": [LW, LH], "anchor": [28, LH],
            "hurtbox": hurtbox(anims, ["Body", "Head"], inset=(1, 1, 1), tag=2),
            "attacks": {"emerge": {"active": [3, 4], "hit": hit_rect(infos, "emerge", [3, 4], x_min=28)},
                        "grab": {"active": [4, 6], "hit": hit_rect(infos, "grab", [4, 6], x_min=30)}},
            "telegraph": {"grab": {"frame": 2, "at": spawn_pt(infos["grab"][2]["glint"])}},
            "surface_y": SURF + 1,
            "notes": "faces right; anchor = water surface / floor line (engine draws the freezing-water overlay). "
                     "lurk: nearly hidden dark shape below the surface (only bottom rows + bubbles). emerge: bursts "
                     "up with spray + ice shards 0-2, ambush strike active 3-4, settles 5-6. idle: surfaced sway "
                     "(hurtbox = surfaced body, idle frame 0). grab: coils back 0-3 (2 = held, teeth glint), jaws+"
                     "claws lunge active 4-6, retract 7-8. submerge: dives back, splash. death: goes limp, sinks, "
                     "dissolves into frost."}
    export("hf_lurker", LU_L, anims, meta)
    return meta



# =========================================================================== FX
def _rgba(key, a=255):
    c = K.RGBA[key]
    return (c[0], c[1], c[2], a)


def fx_breath():
    """32x24, 4 frames loop, centred pivot: a puff of freezing breath rolling RIGHT -- soft icy cloud (a few alpha
    steps on the fringe), a brighter leading edge, glinting ice crystals, wisps trailing behind."""
    K.setup(32, 24)
    frames = []
    for i in range(4):
        ph = i * math.pi / 2
        mist = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
        core = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
        mp, cp_ = mist.load(), core.load()
        lobes = [((18.5 + 0.6 * math.sin(ph), 12.0), 6.2 + 0.4 * math.sin(ph + 1)),
                 ((14.0 + 0.8 * math.cos(ph), 9.6 + 0.8 * math.sin(ph)), 4.4),
                 ((13.6 + 0.8 * math.sin(ph + 2), 14.6 + 0.6 * math.cos(ph)), 4.2),
                 ((23.2, 11.4 + 0.7 * math.sin(ph + 1.4)), 3.8 + 0.3 * math.cos(ph)),
                 ((9.0 - i * 0.6, 12.4 + math.sin(ph + 2.2)), 2.8)]
        for y in range(24):
            for x in range(32):
                px, py = x + .5, y + .5
                f = -1.0
                for (cx, cy), r in lobes:
                    d = math.hypot(px - cx, (py - cy) * 1.15) / r
                    f = max(f, 1 - d)
                if f <= -0.05:
                    continue
                f += 0.12 * math.sin(px * 0.9 + py * 0.7 + ph * 2) * math.sin(py * 1.1 - ph)
                lead = max(0.0, (px - 16) / 12)                     # leading edge brighter
                if f <= 0.0:
                    continue
                if f < 0.12:
                    mp[x, y] = _rgba("J1", 120)
                elif f < 0.26:
                    mp[x, y] = _rgba("J2", 170)
                elif f < 0.46:
                    cp_[x, y] = _rgba("J2" if lead < 0.3 else "J3")
                elif f < 0.66:
                    cp_[x, y] = _rgba("J3" if lead < 0.55 else "J4")
                else:
                    cp_[x, y] = _rgba("J4" if lead < 0.5 else "J5")
        # trailing wisps
        for k, (y0, ln) in enumerate(((9, 7), (13, 9), (16, 5))):
            off = (i * 2 + k) % 4
            for x in range(2 + off, 2 + off + ln):
                a = 90 + int(80 * (x - off) / (ln + 2))
                if mp[x, y0][3] == 0 and cp_[x, y0][3] == 0:
                    mp[x, y0 + (1 if (x + k) % 5 == 0 else 0)] = _rgba("J2" if x > off + ln // 2 else "J1", a)
        # ice crystals glinting in the cloud
        for k in range(5):
            cx = int(10 + 18 * hash01(k, i, 3))
            cy = int(6 + 12 * hash01(k, i, 4))
            cp_[cx, cy] = _rgba("J5")
            if k % 2 == 0:
                for q in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= q[0] < 32 and 0 <= q[1] < 24:
                        cp_[q] = _rgba("U5")
        frames.append((70, {"Mist": mist, "Core": core}))
    return frames


def fx_frostwave():
    """32x24, 4 frames loop, pivot bottom-centre: a creeping ground wave of jagged ice shards travelling RIGHT --
    fresh shards erupt at the crest, older ones behind shrink and crumble into frost."""
    K.setup(32, 24)
    frames = []
    crest = 23.0
    for i in range(4):
        Lb = Layer("Shards")
        FXl = FXLayer("Glow")
        sp = 4.6
        off = i * sp / 4
        xs = []
        x = 1.0 + off
        while x < 31:
            xs.append(x)
            x += sp
        for k, x in enumerate(xs):
            if x <= crest:
                env = 0.25 + 0.75 * ((x - 1) / (crest - 1)) ** 1.6
            else:
                env = max(0.0, 1 - (x - crest) / (31 - crest)) ** 0.7
            # crumbling: the older (left) shards lose height and break
            hgt = 3.0 + 14.0 * env
            wid = 3.4 + 2.8 * env
            ang = -72 + 10 * (1 - env) + (5 if k % 2 else -3)
            if x > crest:                     # the newest shard is still erupting at the very front
                hgt *= 0.8
                ang = -64
            ice_shard(Lb, (x, 24.4), ang, hgt, wid, tip_glow=env > 0.85)
            # a smaller companion shard for a jagged cluster
            if env > 0.6:
                ice_shard(Lb, (x - 1.8, 24.4), ang - 20, hgt * 0.45, wid * 0.7)
        # crumbling chips behind the crest
        for k in range(7):
            cx = 2 + hash01(k, i, 11) * 14
            cy = 22 - hash01(k, i, 12) * (3 + cx * 0.3)
            FXl.put([ip((cx, cy))], ("U4", "U3", "J2")[k % 3])
        # frost-light seam along the ground under the wave
        for x in range(0, 32):
            env = min(1.0, max(0.0, (x - 2) / (crest - 2))) if x <= crest else max(0.0, 1 - (x - crest) / 8)
            if env > 0.15:
                FXl.put([(x, 23)], "J3" if env > 0.7 and (x + i) % 3 else "J2")
        # rime spray flicked from the crest
        for k in range(6):
            cx = crest - 3 + hash01(k, i, 21) * 8
            cy = 24 - 14 - hash01(k, i, 22) * 7
            FXl.put([ip((cx, cy))], ("J5", "U5", "J4")[k % 3])
        img = K.render_layer(Lb)
        glow = FXl.image()
        back = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
        # a translucent cold haze hugging the ground (the FX alpha steps)
        bp = back.load()
        for y in range(16, 24):
            for x in range(0, 30):
                env = min(1.0, max(0.0, (x - 1) / crest)) if x <= crest else max(0.0, 1 - (x - crest) / 7)
                h = 3 + env * 5 + math.sin(x * 0.7 + i * 1.6) * 1.0
                if 23 - y < h:
                    a = int(70 + 70 * env * (1 - (23 - y) / max(h, 1)))
                    bp[x, y] = _rgba("J1" if (23 - y) > h * 0.5 else "J2", a)
        frames.append((80, {"Haze": back, "Shards": img, "Glow": glow}))
    return frames


def build_fx():
    br, fw = fx_breath(), fx_frostwave()
    # preview: rows breath / frostwave, on the mid-grey preview background and on the region's dark blue
    s = 5
    sheet = Image.new("RGBA", (2 * 4 * 34 * s + 20, 2 * 26 * s + 30), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    for col, bgc in enumerate(((86, 86, 94, 255), (11, 15, 24, 255))):
        for r, (frs, order) in enumerate(((br, ["Mist", "Core"]), (fw, ["Haze", "Shards", "Glow"]))):
            for i, (ms, cels) in enumerate(frs):
                fr = Image.new("RGBA", (32, 24), bgc)
                for n in order:
                    fr.alpha_composite(cels[n])
                sheet.alpha_composite(fr.resize((32 * s, 24 * s), Image.NEAREST),
                                      (col * (4 * 34 * s + 20) + i * 34 * s, 15 + r * 26 * s))
        d.text((col * (4 * 34 * s + 20) + 4, 2), "breath / frostwave  " + ("mid-grey" if col == 0 else "#0b0f18"),
               fill=(235, 235, 240, 255))
    sheet.save(os.path.join(ART, "previews", "fx_hf_enemies.png"))
    if BUILD:
        K.asebuild.build("fx_hf_breath", 32, 24, ["Mist", "Core"],
                         [{"ms": ms, "cels": c} for ms, c in br], [("hf_breath", 0, 3)])
        K.asebuild.build("fx_hf_frostwave", 32, 24, ["Haze", "Shards", "Glow"],
                         [{"ms": ms, "cels": c} for ms, c in fw], [("hf_frostwave", 0, 3)])
    return {"fx_hf_breath": [32, 24, "hf_breath x4, centred"], "fx_hf_frostwave": [32, 24, "hf_frostwave x4, pivot bottom"]}



# =========================================================================== region read check
SANITY = [("hf_wraith", [("fly", 0), ("breath", 3), ("breath", 5), ("dive", 3)]),
          ("hf_golem", [("idle", 0), ("slam", 5), ("slam", 7), ("swipe", 4), ("death", 7)]),
          ("hf_lurker", [("lurk", 0), ("emerge", 1), ("idle", 0), ("grab", 4)])]


def build_sanity():
    """1x and 2x on the region's dark blue (#0b0f18) with a stone floor and a 10x26 player-size box for scale."""
    if not all(n in FLATS for n, _ in SANITY):
        return None
    bg = (11, 15, 24, 255)
    W1, H1 = 384, 216
    strip = Image.new("RGBA", (W1, H1), bg)
    d = ImageDraw.Draw(strip)
    floors = (70, 140, 206)
    for fy in floors:
        d.rectangle([0, fy, W1, fy + 9], fill=(21, 27, 38, 255))
        d.line([(0, fy), (W1, fy)], fill=(48, 62, 82, 255))
    x = 6
    for r, (name, picks) in enumerate(SANITY):
        tags, flats, (w, h), meta = FLATS[name]
        fy = floors[r]
        x = 6
        d.rectangle([x, fy - 26, x + 9, fy - 1], outline=(120, 110, 90, 255))       # player-size reference
        x += 18
        for t, k in picks:
            im = flats[tags[t][0] + k]
            if name == "hf_wraith":
                y = fy - 24 - h // 2 - 4       # hovering
            else:
                y = fy - h
            if name == "hf_lurker":            # the pool: a translucent water overlay above the floor line
                pool = Image.new("RGBA", (w + 8, 6), (40, 90, 140, 90))
                strip.alpha_composite(im, (x, y))
                strip.alpha_composite(pool, (x - 4, fy - 6))
            else:
                strip.alpha_composite(im, (x, y))
            x += w + 8
    big = strip.resize((W1 * 2, H1 * 2), Image.NEAREST)
    out = Image.new("RGBA", (W1 * 3 + 12, H1 * 2), (30, 30, 36, 255))
    out.alpha_composite(strip, (0, 0))
    out.alpha_composite(big, (W1 + 12, 0))
    out.save(os.path.join(ART, "previews", "hf_sanity.png"))
    return "art/previews/hf_sanity.png"



# =========================================================================== main
ENEMIES = {
    "hf_wraith": build_wraith,
    "hf_golem": build_golem,
    "hf_lurker": build_lurker,
    "fx": build_fx,
}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    for name, fn in ENEMIES.items():
        if only and name not in only:
            continue
        meta = fn()
        print(name, json.dumps(meta))
        if BUILD and name in SPEC:
            print("  tags", HK.verify(name, SPEC[name]))
        if BUILD and name == "fx":
            for n, sp_ in (("fx_hf_breath", {"hf_breath": 4}), ("fx_hf_frostwave", {"hf_frostwave": 4})):
                print("  tags", n, HK.verify(n, sp_))
    sv = build_sanity()
    if sv:
        print("sanity", sv)


if __name__ == "__main__":
    main()
