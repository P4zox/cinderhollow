#!/usr/bin/env python3
"""Enemies of the Burning Deep (agent D) -- same contract as ART_SPEC section 4, method + helpers from enemy_kit.py /
gen_enemies3.py (read-only reuse).

    python3 art/gen_deep_enemies.py [--preview] [--only dp_slag_imp,...]

    dp_slag_imp       40x32  a wiry forge-imp of cooling slag: swept horns, ember-cracked limbs, whip tail; hurls
                             molten slag in arcs.  idle(4) run(6) throw(8, spawn f5) hop(5) claw(7) hurt(2) death(6)
    dp_forge_sentry   56x48  a tall armoured forge-guard automaton: blackened plate with Ashwright-gold trim, a visor
                             slit lit by the furnace in its chest, a flame-jet gauntlet.
                             idle(4) walk(6) jet(14, flame 5-10) bash(9) hurt(2) death(8)
    dp_magma_crawler  64x32  a long plated lava-salamander: obsidian scutes over magma seams, wedge head, whip tail.
                             sub(4) burst(8, leap from f3) crawl(6) bite(7) sink(5) hurt(2) death(6)
All face RIGHT, feet on the bottom row.  Previews: art/previews/<name>.png + <name>_hitbox.png
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,  # noqa: E402
                       poly_mask, n_plate, n_dome, n_capsule, swept, dirv, bbox)
import gen_enemies3 as E3  # noqa: E402   (read-only reuse of its helpers)
from gen_enemies3 import n_tube, curve, hit_rect, hurtbox, mk, spawn_pt, rot, madd, disc_glow, halo_dots, collapse  # noqa: E402
from PIL import Image  # noqa: E402

BUILD = "--preview" not in sys.argv

NEW_RAMPS = {
    # cooling slag hide: warm charcoal with a faint violet sheen
    "S": ["#0b0708", "#150e0f", "#211618", "#2f2022", "#433033", "#5e4648"],
    # heat-lit plate (the forge glow on iron)
    "U": ["#1c0909", "#300f0b", "#4b170d", "#70220e", "#9c3410"],
    # blackened forge iron (warm)
    "F": ["#070506", "#0e0a0b", "#161012", "#201718", "#2e211f", "#443029", "#6a4c3c"],
}
for _r, _cols in NEW_RAMPS.items():
    _keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        _keys.append(_k)
    K.RAMP[_r] = _keys
K.SHINY.update({"F": 0.93, "S": 0.97})
K.SMEAR.update({"magma": ["O5", "O4", "O3", "O2"], "slag": ["Y3", "O4", "O3", "O1"]})
GLOW = ("O5", "O4", "O3", "O2", "O1", "O0")

SPEC_FRAMES = {
    "dp_slag_imp": dict(idle=4, run=6, throw=8, hop=5, claw=7, hurt=2, death=6),
    "dp_forge_sentry": dict(idle=4, walk=6, jet=14, bash=9, hurt=2, death=8),
    "dp_magma_crawler": dict(sub=4, burst=8, crawl=6, bite=7, sink=5, hurt=2, death=6),
}
E3.SPEC_FRAMES.update(SPEC_FRAMES)       # its render_anims / verify read the spec table
E3.BUILD = BUILD


def export(name, layers, anims, meta, flat_order=None):
    tags, flats = K.export(name, layers, anims, meta, build=BUILD, flat_order=flat_order)
    if meta is not None:
        E3.hitbox_preview3(name, tags, flats, meta)
    return tags, flats


def cracks(L, pts, cols=("O3", "O2"), only=None):
    """Ember crack decal along a polyline, restricted to pixels the layer owns."""
    ps = [q for q in polyline([ip(p) for p in pts]) if q in L.px and (only is None or q in only)]
    L.decal(ps[::1], cols[0])
    return ps


def glow_under(L, cols=("U2", "U1"), depth=2):
    """Heat bounce: the undersides of forms pick up the magma light from below."""
    add_ = {}
    for (x, y), e in L.px.items():
        if (x, y + 1) not in L.px and not isinstance(e[3], str):
            add_[(x, y)] = cols[0]
            if (x, y - 1) in L.px and depth > 1:
                add_.setdefault((x, y - 1), cols[1])
    for p, c in add_.items():
        L.px[p][3] = c


# =========================================================================== 1. SLAG IMP
IMP_L = ["Tail", "FarLimbs", "Body", "Head", "NearLimbs", "FX"]
FL = 31.0
I_NEU = dict(P=(17.0, 20.0), C=(21.0, 14.2), Hd=(25.4, 10.6), ha=0.0,
             nk=(20.2, 24.2), nh=(16.8, 27.6), nt=(20.0, FL), fk=(18.4, 24.6), fh=(14.4, 28.0), ft=(17.2, FL),
             ne=(21.4, 18.8), nhand=(24.6, 21.4), fe=(18.4, 18.4), fhand=(20.8, 21.2),
             tail=((-4.0, -1.0), (-4.0, 2.0), (-3.4, -2.6)), glob=0.0, eye=1, smear=None, jaw=0.0,
             rot=0.0, piv=(0, 0), sparks=0, wind=0.0, emb=1.0)
IP = mk(I_NEU)


def imp_leg(L, hip, knee, hock, toe, bias):
    L.paint(n_tube([hip, knee, hock, toe], [1.6, 1.1, 0.8, 0.7]), "S", bias)
    L.paint(n_dome(add(toe, (0.8, -0.3)), 1.4, 0.7), "S", bias, ao=0)
    t = ip(add(toe, (2.0, -0.2)))
    L.fixed({t: "S5" if bias >= 0 else "S3"})
    return [hip, knee, hock]


def imp_arm(L, sh, el, hand, bias, claws=True):
    L.paint(n_tube([sh, el, hand], [1.4, 1.05, 0.9]), "S", bias)
    L.paint(n_dome(hand, 1.1, 1.0), "S", bias, ao=0)
    if claws:
        d = sub(hand, el)
        l = math.hypot(*d) or 1
        d = (d[0] / l, d[1] / l)
        for k in (-1, 1):
            q = ip(madd(hand, (d, 1.8), ((-d[1], d[0]), k * 0.9)))
            L.fixed({q: "S5" if bias >= 0 else "S3"})


def draw_imp(p, fi, sw):
    Ls = {n: Layer(n) for n in IMP_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    P, C, Hd = T(p["P"]), T(p["C"]), T(p["Hd"])
    # tail: long whip, ember tip
    Tl = Ls["Tail"]
    t0 = madd(P, ((-1, 0), 1.6))
    pts = [t0]
    for (dx, dy) in p["tail"]:
        pts.append(add(pts[-1], (dx - sw * 0.2, dy)))
    tp = curve(pts, 5)
    Tl.paint(n_tube(tp, [1.2 - 0.85 * i / (len(tp) - 1) for i in range(len(tp))]), "S", -1)
    tip = ip(pts[-1])
    FX.put([tip], "O4"); FX.put([(tip[0] - 1, tip[1])], "O2")
    # far limbs
    Fl = Ls["FarLimbs"]
    imp_leg(Fl, madd(P, ((-1, 0), 0.6)), T(p["fk"]), T(p["fh"]), T(p["ft"]), -2)
    imp_arm(Fl, madd(C, ((-1, 0), 1.0)), T(p["fe"]), T(p["fhand"]), -2)
    # body: hunched, lean, a molten slit down the sternum
    Bd = Ls["Body"]
    mid = madd(lerp(P, C, 0.5), ((-0.6, -0.8), 1.0))
    bm = Bd.paint(n_tube(curve([P, mid, C], 4), [2.1, 2.3, 2.5, 2.6, 2.7, 2.8, 2.9, 2.9, 2.8]), "S", 0)
    Bd.paint(n_dome(madd(C, ((-1, -0.6), 1.2)), 2.8, 2.2, tilt=(-0.1, -0.3)), "S", 0)       # shoulder hump
    ch = [q for q in polyline([ip(madd(C, ((0.7, 1.0), 1.4))), ip(madd(lerp(P, C, 0.45), ((1, 0.2), 1.8)))]) if q in Bd.px]
    Bd.decal(ch, "O3")
    if ch:
        Bd.decal(ch[len(ch) // 2: len(ch) // 2 + 1], "O5")
    for k in range(3):   # ribs of ember cracks on the flank
        a = madd(lerp(P, C, 0.3 + 0.2 * k), ((-1, 0), 0.8))
        cracks(Bd, [a, madd(a, ((0.4, 1), 1.6))], ("O2",))
    info["hit"] |= set(bm)
    # head: small wedge skull, swept horns, ember eyes
    Hl = Ls["Head"]
    ha = p["ha"]
    G = lambda x, y: add(Hd, rot((x, y), ha))
    Hl.paint(n_tube([madd(C, ((0.6, -0.8), 0.8)), G(-1.8, 0.8)], [1.9, 1.6]), "S", 0)       # neck
    skull = [G(-2.6, -1.8), G(0.6, -2.5), G(3.2, -1.3), G(5.4, 0.3), G(3.8, 1.6), G(0.6, 2.1), G(-2.4, 1.3)]
    sm = R.mask(skull) if False else poly_mask(skull)
    Hl.paint(n_plate(sm, 1.2, (-0.15, -0.3), 1.1), "S", 0)
    if p["jaw"] > 0.1:
        jaw = poly_mask([G(0.4, 1.4), G(4.8, 1.2), G(4.0, 1.2 + 2.0 * p["jaw"]), G(0.4, 2.6)])
        Hl.fixed({q: "O2" for q in jaw})
    for (a0, a1, a2, bias) in (((-1.2, -1.6), (-5.0, -3.2), (-9.0, -2.6), -1), ((0.6, -2.2), (-2.8, -5.0), (-7.4, -5.8), 1)):
        hp = curve([G(*a0), G(*a1), G(*a2)], 5)
        Hl.paint(n_tube(hp, [1.25 - 0.9 * i / (len(hp) - 1) for i in range(len(hp))]), "S", bias, ao=0)
        e = ip(G(*a2))
        Hl.fixed({e: "O4"})
    e = ip(G(2.3, -0.7))
    if p["eye"]:
        Hl.fixed({e: "O5", (e[0] - 1, e[1]): "O3"})
    info["eye"] = G(2.3, -0.7)
    info["hit"] |= set(Hl.px)
    # near limbs
    Nl = Ls["NearLimbs"]
    legp = imp_leg(Nl, P, T(p["nk"]), T(p["nh"]), T(p["nt"]), 1)
    cracks(Nl, [lerp(legp[0], legp[1], 0.3), lerp(legp[0], legp[1], 0.85)], ("O2",))
    hand = T(p["nhand"])
    imp_arm(Nl, madd(C, ((1, 0), 0.4)), T(p["ne"]), hand, 1)
    cracks(Nl, [lerp(T(p["ne"]), hand, 0.2), lerp(T(p["ne"]), hand, 0.8)], ("O3",))
    info["hand"] = hand
    # the slag glob in the throwing hand
    if p["glob"] > 0:
        r = 0.9 + p["glob"] * 0.7
        c = madd(hand, ((0, -1), 0.8 + r * 0.6))
        disc_glow(FX, c, r, GLOW[:4])
        if p["glob"] >= 2:
            halo_dots(FX, c, r + 2.2, 8, fi, ("O3", "O2"))
        info["glob"] = c
    # heat bounce on undersides, rim on top edges
    for L_ in (Bd, Hl):
        glow_under(L_, ("U2", "U1"), depth=1)
    for L_ in (Bd, Hl, Nl):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "S" and not isinstance(e_[3], str)], ("S", 5))
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= swept(FX, T(g0), a0, T(g1), a1, u0, u1, hw=1.0, pal="magma", taper=0.5)
    if p["sparks"]:
        for k in range(8):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 1, 7))
            rr = 2 + 6 * hash01(k, 2, 7)
            FX.put([ip((P[0] + math.cos(a) * rr, FL + math.sin(a) * rr * 0.6))], ("O4", "O3", "O2")[k % 3])
    # embers drifting off the hide
    for k in range(int(3 * p["emb"])):
        q = ip((P[0] + (hash01(k, fi, 3) - 0.5) * 10, C[1] - 2 - ((fi * 2 + k * 3) % 7)))
        FX.put([q], "O3" if k % 2 else "O2")
    return Ls, info


def i_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        fr.append((170, IP(C=(21.0, 14.2 + b * 0.5), Hd=(25.4, 10.6 + b * 0.7), ne=(21.4, 18.9 + b * 0.5),
                           nhand=(24.6, 21.6 + b * 0.4), fhand=(20.8, 21.4 + b * 0.4),
                           tail=((-4.0, -1.0 + b * 0.6), (-4.0, 2.0 - b), (-3.4, -2.6 + b * 1.4)))))
    return fr


def i_run():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        up = 1.2 * abs(math.sin(ph))
        P = (16.5, 20.0 - up)
        fr.append((75, IP(P=P, C=(22.4, 15.4 - up), Hd=(27.4, 12.8 - up), ha=8,
                          nk=(19.5 + 3 * c, 24.0 - up), nh=(15.5 + 3 * c, 27.4 - up * 0.5), nt=(18.5 + 4.5 * c, FL - max(0, s) * 2.2),
                          fk=(18.0 - 3 * c, 24.4 - up), fh=(14.0 - 3 * c, 27.8 - up * 0.5), ft=(17.0 - 4.5 * c, FL - max(0, -s) * 2.2),
                          ne=(22.0 - 2 * c, 19.0 - up), nhand=(24.0 - 3 * c, 21.0 - up), fe=(20.0 + 2 * c, 19.0 - up), fhand=(22.0 + 3 * c, 21.0 - up),
                          tail=((-4.6, 0.4), (-4.4, -0.8 + s), (-3.8, -1.2 - s)), wind=-2)))
    return fr


def i_throw():
    back = dict(C=(19.6, 14.0), Hd=(23.6, 10.2), ha=-8)
    return [
        (120, IP(glob=1, nhand=(25.0, 20.0), ne=(22.0, 18.6))),
        (130, IP(**back, glob=2, ne=(17.0, 12.0), nhand=(13.0, 8.2), nk=(19.4, 24.4), nt=(21.0, FL), jaw=0.3)),
        (160, IP(**back, glob=3, ne=(16.4, 11.4), nhand=(12.2, 7.0), nk=(19.4, 24.4), nt=(21.0, FL), jaw=0.6)),
        (170, IP(**back, glob=3, ne=(16.4, 11.2), nhand=(12.0, 6.6), nk=(19.4, 24.4), nt=(21.0, FL), jaw=0.8)),
        (70, IP(P=(18.4, 20.0), C=(23.0, 14.4), Hd=(27.4, 11.0), ha=6, glob=3, ne=(22.0, 10.0), nhand=(24.4, 5.4),
                nk=(22.0, 24.0), nt=(24.0, FL), fk=(17.0, 24.6), ft=(13.6, FL), jaw=0.6)),
        (70, IP(P=(18.8, 20.0), C=(24.0, 14.8), Hd=(28.4, 11.8), ha=14, ne=(27.4, 13.0), nhand=(31.4, 14.0),
                nk=(22.4, 24.0), nt=(24.4, FL), fk=(17.0, 24.6), ft=(13.6, FL), jaw=0.4,
                smear=[((24.4, 5.4), -100, (31.4, 14.0), 20, 0.5, 3.5)])),
        (110, IP(P=(18.6, 20.0), C=(23.8, 15.2), Hd=(28.2, 12.0), ha=12, ne=(26.6, 17.6), nhand=(29.0, 21.6),
                 nk=(22.2, 24.0), nt=(24.4, FL), fk=(17.0, 24.6), ft=(13.6, FL))),
        (150, IP(P=(17.4, 20.0), C=(21.6, 14.4), Hd=(26.0, 10.8), nk=(20.8, 24.2), nt=(21.6, FL))),
    ]


def i_hop():
    tuck = dict(nk=(21.0, 21.0), nh=(17.6, 23.6), nt=(20.6, 25.6), fk=(19.0, 21.4), fh=(15.4, 24.0), ft=(18.2, 26.0))
    return [
        (90, IP(P=(17.0, 22.0), C=(21.4, 16.4), Hd=(25.4, 12.8), nk=(21.0, 25.0), nh=(16.0, 28.4), fk=(19.0, 25.4), fh=(13.8, 28.6))),
        (90, IP(P=(16.0, 15.0), C=(19.0, 9.4), Hd=(22.6, 6.0), ha=-14, **tuck, ne=(21.0, 12.0), nhand=(24.4, 10.6),
                tail=((-4.4, 2.0), (-3.4, 3.0), (-2.6, 1.0)))),
        (120, IP(P=(16.0, 13.0), C=(20.0, 8.0), Hd=(24.0, 5.0), ha=-6, **{k: (v[0], v[1] - 2) for k, v in tuck.items()},
                 ne=(22.0, 11.0), nhand=(25.0, 12.0), tail=((-4.4, 1.0), (-3.4, 2.4), (-2.6, 1.8)))),
        (90, IP(P=(17.0, 22.4), C=(21.8, 17.0), Hd=(26.0, 13.4), nk=(21.2, 25.4), nh=(16.2, 28.6), fk=(19.2, 25.8), fh=(14.0, 28.8),
                sparks=1)),
        (110, IP()),
    ]


def i_claw():
    return [
        (110, IP(C=(20.0, 14.0), Hd=(24.4, 10.4), ne=(20.6, 11.0), nhand=(22.6, 6.8), jaw=0.2)),
        (150, IP(C=(19.4, 13.6), Hd=(23.6, 10.0), ha=-6, ne=(19.6, 10.4), nhand=(21.0, 5.6), jaw=0.6, eye=1)),
        (70, IP(P=(18.4, 20.0), C=(24.0, 15.0), Hd=(28.0, 12.0), ha=12, ne=(26.6, 14.4), nhand=(31.4, 17.2), nk=(22.0, 24.0),
                nt=(24.0, FL), jaw=0.8, smear=[((21.0, 5.6), -80, (31.4, 17.2), 30, 0.5, 4.0)])),
        (70, IP(P=(18.6, 20.0), C=(24.2, 15.4), Hd=(28.4, 12.4), ha=14, ne=(26.8, 18.0), nhand=(30.4, 22.4), nk=(22.0, 24.0),
                nt=(24.0, FL), jaw=0.5, smear=[((31.4, 17.2), 30, (30.4, 22.4), 70, 0.5, 4.0)])),
        (100, IP(P=(18.4, 20.0), C=(23.6, 15.6), Hd=(27.6, 12.4), ha=10, ne=(25.8, 19.4), nhand=(28.0, 23.0), nk=(21.8, 24.0), nt=(23.6, FL))),
        (120, IP(P=(17.6, 20.0), C=(22.0, 14.8), Hd=(26.2, 11.2), ne=(22.8, 19.4), nhand=(25.4, 22.0), nk=(20.8, 24.2), nt=(21.0, FL))),
        (120, IP()),
    ]


def i_hurt():
    return [(90, IP(P=(16.0, 20.0), C=(18.6, 14.0), Hd=(22.0, 10.2), ha=-22, jaw=0.8, ne=(18.0, 17.0), nhand=(20.0, 19.0),
                    tail=((-4.0, 2.4), (-3.6, 2.4), (-2.6, 1.0)))),
            (130, IP(P=(16.6, 20.0), C=(20.2, 14.2), Hd=(24.2, 10.6), ha=-8))]


def i_death():
    lie = dict(P=(17.0, 27.0), C=(23.0, 26.4), Hd=(27.4, 27.0), ha=40, nk=(20.0, 28.0), nh=(15.0, 29.4), nt=(12.0, FL),
               fk=(18.4, 28.6), fh=(14.0, 30.0), ft=(11.0, FL), ne=(25.0, 29.0), nhand=(28.0, FL - 0.5), fe=(21.0, 29.0),
               fhand=(24.0, FL - 0.5), tail=((-4.4, 0.6), (-4.0, 1.0), (-3.6, 0.6)), eye=0, emb=0.0)
    sn = ["Tail", "FarLimbs", "Body", "Head", "NearLimbs"]
    ash = ("O4", "O3", "O2", "S3", "S2")
    return [
        (100, IP(P=(16.0, 20.0), C=(18.0, 14.0), Hd=(20.6, 9.8), ha=-30, jaw=1.0, ne=(17.0, 16.0), nhand=(15.0, 12.0))),
        (120, IP(P=(16.4, 24.0), C=(20.4, 19.6), Hd=(24.6, 18.4), ha=20, jaw=0.4, nk=(20.0, 27.0), nh=(15.0, 29.6), nt=(17.0, FL),
                 ne=(22.0, 24.0), nhand=(25.0, 27.0))),
        (140, IP(**lie)),
        (140, IP(**lie, post=collapse(sn, 0.65, 0.15, pal=ash, spread=0.35))),
        (160, IP(**lie, post=collapse(sn, 0.35, 0.3, pal=ash, spread=0.5))),
        (600, IP(**lie, post=collapse(sn, 0.14, 0.34, pal=ash, spread=0.6))),
    ]


def build_imp():
    K.setup(40, 32)
    anims, infos = E3.render_anims("dp_slag_imp", IMP_L, draw_imp,
                                   [("idle", i_idle), ("run", i_run), ("throw", i_throw), ("hop", i_hop), ("claw", i_claw),
                                    ("hurt", i_hurt), ("death", i_death)], sway_key="C", loops=("idle", "run"))
    meta = {"native": 1, "frame": [40, 32], "anchor": [18, 32],
            "hurtbox": hurtbox(anims, ["Body", "Head"], inset=(1, 1, 1)),
            "attacks": {"claw": {"active": [2, 3], "hit": hit_rect(infos, "claw", [2, 3], x_min=21)}},
            "spawn": {"throw": {"frame": 5, "at": spawn_pt(infos["throw"][4]["glob"])}},
            "telegraph": {"throw": {"frame": 3, "at": spawn_pt(infos["throw"][3]["glob"])},
                          "claw": {"frame": 1, "at": spawn_pt(infos["claw"][1]["hand"])}},
            "notes": "faces right; throw: glob kindles in the near hand (0), wound back overhead (1-3, 3 = telegraph), "
                     "whipped over (4) and released at frame 5 from the spawn point; hop drawn in place (engine moves it)."}
    export("dp_slag_imp", IMP_L, anims, meta)
    return meta


# =========================================================================== 2. FORGE SENTRY
SEN_L = ["Back", "FarLimbs", "Body", "Head", "NearLimbs", "FX"]
FL2 = 47.0
S_NEU = dict(P=(24.0, 29.0), C=(25.0, 17.0), Hd=(26.4, 9.6), ha=0.0,
             nk=(27.4, 37.6), nf=(28.6, FL2), fk=(22.2, 37.8), ff=(20.8, FL2),
             ne=(29.6, 25.6), nhand=(34.4, 27.6), noz=0.0, fe=(21.0, 25.0), fhand=(22.6, 31.4),
             visor=1.0, core=1.0, rot=0.0, piv=(0, 0), smoke=0, flare=0.0, smear=None, sparks=0, wind=0.0, bash=0.0)
SP = mk(S_NEU)


def draw_sentry(p, fi, sw):
    Ls = {n: Layer(n) for n in SEN_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    P, C, Hd = T(p["P"]), T(p["C"]), T(p["Hd"])
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    # back: a slim chimney stack venting smoke
    Bk = Ls["Back"]
    st0, st1 = F(-5.4, -ln + 1.0), F(-7.6, -ln - 7.5)
    Bk.paint(n_capsule(st0, st1, 1.6, 1.3), "F", -1)
    Bk.paint(n_capsule(st1, F(-7.8, -ln - 8.6), 1.9, 1.9), "F", 0, ao=0)
    q = ip(F(-7.8, -ln - 9.4))
    FX.put([q], "O2")
    for k in range(4 + p["smoke"] * 3):
        t = (k / (4 + p["smoke"] * 3) + fi * 0.21) % 1.0
        FX.put([ip((q[0] - t * 5 + math.sin(k * 2.1 + t * 6) * 1.2, q[1] - 1 - t * 9))], "S3" if t < 0.5 else "S2")
    # far leg + far arm (a heavy fist)
    Fl = Ls["FarLimbs"]
    hipF = F(-2.2, 0.6)
    Fl.paint(n_tube([hipF, T(p["fk"]), T(p["ff"])], [3.0, 2.5, 2.1]), "F", -2)
    Fl.paint(n_plate(poly_mask([add(T(p["ff"]), (-3, 0.8)), add(T(p["ff"]), (-3, -2.6)), add(T(p["ff"]), (3.6, -1.6)), add(T(p["ff"]), (4.2, 0.8))]), 1.0, (0, -0.4)), "F", -2)
    shF = F(-3.4, -ln + 2.0)
    Fl.paint(n_tube([shF, T(p["fe"]), T(p["fhand"])], [2.6, 2.2, 2.0]), "F", -2)
    Fl.paint(n_dome(T(p["fhand"]), 2.2, 2.2), "F", -2, ao=0)
    # body: V-shaped plate cuirass, tapered waist, faulds; the furnace core glowing through a grille
    Bd = Ls["Body"]
    torso = [F(-5.4, -ln - 1.0), F(4.6, -ln - 0.8), F(5.6, -ln + 3.6), F(3.0, -ln + 9.0), F(2.2, -1.0), F(-2.6, -1.0), F(-4.0, -ln + 8.6),
             F(-6.0, -ln + 3.0)]
    tm = poly_mask(torso)
    Bd.paint(n_plate(tm, 2.2, (-0.25, -0.2), 1.2), "F", 0)
    # faulds (skirt of lames) + belt
    fau = [F(-4.6, -1.8), F(3.6, -1.8), F(4.8, 4.6), F(-5.6, 4.6)]
    fm = poly_mask(fau)
    Bd.paint(n_plate(fm, 1.4, (-0.2, 0.1)), "F", -1)
    for k in range(3):
        Bd.decal([q for q in line(F(-5.0, 0.2 + k * 1.6), F(4.4, 0.2 + k * 1.6)) if q in fm], ("F", 1))
    Bd.decal([q for q in line(F(-4.8, -1.8), F(3.8, -1.8)) if q in Bd.px], "G3")
    # gold trim along the cuirass edges + the maker's seal
    Bd.decal([q for q in polyline([ip(F(-5.6, -ln - 1.0)), ip(F(5.0, -ln - 0.6))]) if q in tm], "G3")
    cc = ip(F(0.4, -ln + 6.0))
    grille = {}
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            qq = (cc[0] + dx, cc[1] + dy)
            if abs(dx) + abs(dy) <= 3:
                grille[qq] = ("F1" if dx % 2 else ("O4" if p["core"] > 1.3 else "O3") if abs(dy) < 2 else "O2") if p["core"] > 0 else "F1"
    Bd.fixed(grille)
    Bd.fixed({(cc[0], cc[1] - 3): "G4", (cc[0], cc[1] + 3): "G2"})
    info["core"] = cc
    info["hit"] |= set(tm)
    # head: tall closed forge-helm, sleek crest, one vertical visor slit lit from within
    Hl = Ls["Head"]
    G = lambda x, y: add(Hd, rot((x, y), p["ha"]))
    Hl.paint(n_tube([F(0.4, -ln - 0.4), G(-0.4, 2.6)], [2.4, 2.2]), "F", -1)
    helm = [G(-2.6, 2.6), G(-2.9, -1.2), G(-2.0, -3.6), G(0.4, -4.6), G(2.6, -3.5), G(3.4, -0.8), G(3.1, 2.0), G(1.4, 2.9)]
    hm = poly_mask(helm)
    Hl.paint(n_plate(hm, 1.4, (-0.3, -0.35), 1.3), "F", 0)
    Hl.decal([q for q in line(G(-2.4, -0.2), G(3.2, -0.2)) if q in hm], ("F", 1))                 # brow ridge
    crest = [G(-0.6, -4.2), G(0.8, -4.6), G(-3.2, -7.4), G(-6.4, -7.8), G(-3.0, -5.6)]
    Hl.paint(n_plate(poly_mask(crest), 0.7, (-0.1, -0.4)), "F", 1, ao=0)
    Hl.decal([ip(G(-5.4, -7.6)), ip(G(-4.4, -7.2))], "G4")
    Hl.decal([q for q in line(G(-2.8, 2.4), G(1.6, 2.8)) if q in hm], "G2")                          # gilt gorget edge
    vis = [ip(G(x, 0.6)) for x in (0.6, 1.6, 2.6)]
    Hl.fixed({q: ("O4" if i == 2 and p["visor"] > 1.2 else "O3" if p["visor"] > 0.5 else "F1") for i, q in enumerate(vis)})
    Hl.fixed({ip(G(3.4, 0.6)): "O2" if p["visor"] > 0.5 else "F1"})
    info["visor"] = G(2.6, 0.6)
    info["hit"] |= set(Hl.px)
    # near leg: greave + sabaton
    Nl = Ls["NearLimbs"]
    hipN = F(1.6, 0.4)
    Nl.paint(n_tube([hipN, T(p["nk"]), T(p["nf"])], [3.2, 2.6, 2.2]), "F", 0)
    Nl.paint(n_dome(T(p["nk"]), 2.5, 2.3, tilt=(-0.2, -0.2)), "F", 1, ao=0)          # knee cop
    Nl.decal([ip(T(p["nk"]))], "G3")
    ft = T(p["nf"])
    Nl.paint(n_plate(poly_mask([add(ft, (-3.2, 0.8)), add(ft, (-3.0, -2.8)), add(ft, (3.4, -1.8)), add(ft, (4.6, 0.8))]), 1.0, (0, -0.4)), "F", 0)
    # near arm: pauldron + the flame-jet gauntlet (a stout nozzle fed by a hose)
    shN = F(3.6, -ln + 2.0)
    Nl.paint(n_dome(madd(shN, ((0, -1), 0.6)), 4.2, 3.4, tilt=(-0.2, -0.4)), "F", 1)
    Nl.decal([q for q in polyline([ip(madd(shN, ((-1, 0), 3.8))), ip(madd(shN, ((1, 0.3), 3.8)))]) if q in Nl.px], "G3")
    el, hand = T(p["ne"]), T(p["nhand"])
    Nl.paint(n_tube([madd(shN, ((0, 1), 1.0)), el], [2.4, 2.2]), "F", 0)
    d = sub(hand, el)
    l = math.hypot(*d) or 1
    d = (d[0] / l, d[1] / l)
    nz0, nz1 = madd(el, (d, 0.6)), madd(hand, (d, 3.0))
    Nl.paint(n_capsule(nz0, nz1, 2.8, 2.2), "F", 1)                  # gauntlet cannon
    Nl.paint(n_capsule(madd(nz1, (d, -0.6)), madd(nz1, (d, 1.2)), 2.6, 2.6), "F", 2, ao=0)    # muzzle ring
    muzzle = madd(nz1, (d, 1.8))
    Nl.decal([q for q in line(madd(nz0, ((-d[1], d[0]), 2.6)), madd(nz1, ((-d[1], d[0]), 2.2))) if q in Nl.px], "G2")
    glowc = "O5" if p["noz"] > 1.5 else "O4" if p["noz"] > 0.8 else "O2"
    Nl.fixed({ip(muzzle): glowc, ip(madd(muzzle, (d, -0.8))): "O2"})
    if p["noz"] > 0.3:
        disc_glow(FX, madd(muzzle, (d, 1.0)), 0.8 + p["noz"] * 0.9, GLOW[:4])
    if p["noz"] > 1.0:
        halo_dots(FX, madd(muzzle, (d, 1.0)), 3.0 + p["noz"], 10, fi, ("O3", "O2"))
    info["muzzle"] = muzzle
    info["pauldron"] = madd(shN, ((1, 0), 3.0))
    # hose from the back stack to the gauntlet
    hose = curve([F(-4.6, -ln + 4.0), F(-1.0, -ln + 10.0), lerp(el, madd(shN, ((0, 1), 1.0)), 0.3)], 5)
    for q in dict.fromkeys(polyline([ip(v) for v in hose])):
        if q not in Nl.px:
            Bd.fixed({q: "F3"})
    # heat light from below / rim along the top
    for L_ in (Bd, Hl, Nl, Fl):
        glow_under(L_)
    for L_ in (Bd, Hl, Nl):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "F" and not isinstance(e_[3], str)], ("F", 5))
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= swept(FX, T(g0), a0, T(g1), a1, u0, u1, hw=1.4, pal="ember", taper=0.5)
    if p["bash"] > 0:
        pd = info["pauldron"]
        for k, y in enumerate((-4, -1, 2, 5)):
            a = ip((pd[0] - 10 - k, pd[1] + y))
            for x in range(a[0], a[0] + 7 - k):
                FX.put([(x, a[1])], "O3" if x > a[0] + 3 else "O1")
        info["hit"] |= {ip(madd(pd, ((1, 0), dx))) for dx in range(0, 5)} | {ip(add(pd, (dx, dy))) for dx in range(-1, 5) for dy in range(-5, 7)}
    if p["sparks"]:
        for k in range(12):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 3, 11))
            rr = 3 + 9 * hash01(k, 4, 11)
            FX.put([ip((P[0] + 4 + math.cos(a) * rr, FL2 + math.sin(a) * rr * 0.5))], ("O4", "O3", "Y2")[k % 3])
    return Ls, info


def s_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        fr.append((200, SP(C=(25.0, 17.0 + b * 0.4), Hd=(26.4, 9.6 + b * 0.5), ne=(29.6, 25.6 + b * 0.4), nhand=(34.4, 27.8 + b * 0.4),
                           fhand=(22.6, 31.6 + b * 0.3), core=1.0 + 0.3 * b, noz=0.3 + 0.2 * (i % 2))))
    return fr


def s_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        b = 0.8 * abs(s)
        fr.append((140, SP(P=(24.0, 29.0 + b * 0.3), C=(25.4, 17.2 + b), Hd=(26.8, 9.8 + b),
                           nk=(27.4 + 2.6 * c, 37.8), nf=(27.8 + 4 * c, FL2 - max(0, s) * 1.6),
                           fk=(22.2 - 2.6 * c, 37.8), ff=(21.4 - 4 * c, FL2 - max(0, -s) * 1.6),
                           ne=(29.6 - c, 25.6 + b), nhand=(34.4 - c * 1.4, 27.6 + b), fhand=(22.6 + c * 1.6, 31.4 + b), noz=0.3,
                           smoke=1 if i % 3 == 0 else 0)))
    return fr


def s_jet():
    brace = dict(P=(23.2, 29.6), C=(25.4, 17.8), Hd=(27.0, 10.4), nk=(29.4, 37.6), nf=(31.0, FL2), fk=(21.2, 38.0), ff=(18.4, FL2))
    aim = dict(ne=(31.0, 22.4), nhand=(36.6, 22.6))
    frs = [
        (140, SP(**brace, ne=(30.0, 25.0), nhand=(34.8, 26.0), noz=0.6, visor=1.4)),
        (140, SP(**brace, ne=(30.6, 23.6), nhand=(36.0, 23.8), noz=1.0, visor=1.6, core=1.4)),
        (160, SP(**brace, **aim, noz=1.6, visor=2.0, core=1.6)),
        (180, SP(**brace, **aim, noz=2.0, visor=2.0, core=1.8, smoke=1)),
        (90, SP(**brace, **aim, noz=2.4, visor=2.0, core=2.0)),
    ]
    for k in range(6):    # flame frames: recoil shudder, core flaring
        frs.append((110, SP(P=(22.8 - 0.3 * (k % 2), 29.6), C=(24.8 - 0.3 * (k % 2), 17.9), Hd=(26.2, 10.6),
                             nk=(29.0, 37.6), nf=(31.0, FL2), fk=(20.8, 38.0), ff=(18.4, FL2),
                             ne=(30.4, 22.6 + 0.3 * (k % 2)), nhand=(36.0 - 0.4 * (k % 2), 22.8), noz=2.6, visor=2.0, core=2.0, smoke=1)))
    frs += [
        (140, SP(**brace, ne=(30.0, 24.6), nhand=(34.6, 25.8), noz=1.0, visor=1.4, core=1.4, smoke=2)),
        (150, SP(ne=(29.8, 25.4), nhand=(34.6, 27.2), noz=0.5, smoke=2)),
        (150, SP(noz=0.3, smoke=1)),
    ]
    return frs


def s_bash():
    return [
        (130, SP(P=(22.6, 29.0), C=(22.0, 17.2), Hd=(23.2, 10.0), ha=-6, ne=(26.6, 24.4), nhand=(31.0, 27.0), nk=(26.0, 37.8), nf=(26.4, FL2))),
        (200, SP(P=(21.6, 29.4), C=(20.4, 17.8), Hd=(21.4, 10.8), ha=-10, ne=(25.4, 24.0), nhand=(29.6, 27.6), nk=(25.6, 38.0),
                 nf=(26.0, FL2), fk=(19.0, 38.0), ff=(15.6, FL2), visor=1.6)),
        (150, SP(P=(21.4, 29.6), C=(20.0, 18.0), Hd=(21.0, 11.2), ha=-12, ne=(25.0, 24.0), nhand=(29.0, 28.0), nk=(25.6, 38.0),
                 nf=(26.4, FL2), fk=(18.6, 38.0), ff=(15.0, FL2), visor=2.0, core=1.6)),
        (80, SP(P=(26.0, 29.4), C=(30.0, 18.6), Hd=(32.6, 12.0), ha=10, ne=(33.0, 25.0), nhand=(36.0, 29.4), nk=(31.0, 37.6),
                nf=(34.0, FL2), fk=(22.4, 38.0), ff=(18.0, FL2), bash=1, visor=2.0)),
        (90, SP(P=(27.0, 29.4), C=(31.4, 18.8), Hd=(34.0, 12.4), ha=12, ne=(34.0, 25.2), nhand=(37.0, 29.6), nk=(32.0, 37.6),
                nf=(35.0, FL2), fk=(23.0, 38.0), ff=(19.0, FL2), bash=1, visor=2.0, sparks=1)),
        (110, SP(P=(27.0, 29.4), C=(30.6, 18.4), Hd=(33.0, 11.6), ha=8, ne=(33.4, 25.4), nhand=(36.8, 28.6), nk=(32.0, 37.6),
                 nf=(35.0, FL2), fk=(23.0, 38.0), ff=(19.0, FL2))),
        (150, SP(P=(26.0, 29.0), C=(28.4, 17.6), Hd=(30.4, 10.6), ha=4, ne=(32.0, 25.4), nhand=(36.0, 28.0), nk=(30.0, 37.6), nf=(32.0, FL2))),
        (160, SP(P=(25.0, 29.0), C=(26.4, 17.2), Hd=(28.0, 9.8), nk=(28.6, 37.6), nf=(30.0, FL2))),
        (160, SP()),
    ]


def s_hurt():
    return [(90, SP(P=(23.0, 29.2), C=(21.6, 17.6), Hd=(22.0, 10.6), ha=-16, ne=(27.4, 24.4), nhand=(31.4, 24.0), visor=0.3, core=2.0)),
            (140, SP(P=(23.6, 29.0), C=(23.6, 17.2), Hd=(24.6, 10.0), ha=-6))]


def s_death():
    kneel = dict(P=(24.0, 36.0), C=(27.0, 25.0), Hd=(30.0, 19.6), ha=24, nk=(30.0, 42.0), nf=(26.0, FL2), fk=(20.0, 44.0), ff=(15.0, FL2),
                 ne=(31.0, 33.0), nhand=(34.0, 40.0), fe=(22.0, 33.0), fhand=(24.0, 42.0), visor=0.0, core=0.4, noz=0.0)
    sn = ["Back", "FarLimbs", "Body", "Head", "NearLimbs"]
    iron = ("O4", "O3", "F3", "F2", "F1")
    return [
        (110, SP(P=(22.6, 29.2), C=(20.8, 17.6), Hd=(20.6, 10.8), ha=-24, visor=0.2, core=2.4, sparks=1)),
        (130, SP(P=(23.6, 32.0), C=(24.4, 20.6), Hd=(26.4, 14.2), ha=10, nk=(28.0, 39.4), fk=(21.6, 40.0), visor=0.4, core=2.0)),
        (180, SP(**kneel)),
        (120, SP(**dict(kneel, core=2.6), sparks=1)),
        (160, SP(**kneel, smoke=2)),
        (140, SP(**kneel, smoke=2, post=collapse(sn, 0.7, 0.1, pal=iron, spread=0.2))),
        (160, SP(**kneel, smoke=1, post=collapse(sn, 0.42, 0.2, pal=iron, spread=0.3))),
        (600, SP(**kneel, post=collapse(sn, 0.25, 0.22, pal=iron, spread=0.4))),
    ]


def build_sentry():
    K.setup(56, 48)
    anims, infos = E3.render_anims("dp_forge_sentry", SEN_L, draw_sentry,
                                   [("idle", s_idle), ("walk", s_walk), ("jet", s_jet), ("bash", s_bash), ("hurt", s_hurt),
                                    ("death", s_death)], sway_key="C", loops=("idle", "walk"))
    meta = {"native": 1, "frame": [56, 48], "anchor": [24, 48],
            "hurtbox": hurtbox(anims, ["Body", "Head"], inset=(1, 0, 1)),
            "attacks": {"bash": {"active": [3, 4], "hit": hit_rect(infos, "bash", [3, 4], x_min=28)}},
            "spawn": {"jet": {"frame": 5, "at": spawn_pt(infos["jet"][5]["muzzle"])}},
            "jet_frames": [5, 10],
            "telegraph": {"jet": {"frame": 2, "at": spawn_pt(infos["jet"][2]["muzzle"])},
                          "bash": {"frame": 2, "at": spawn_pt(infos["bash"][2]["visor"])}},
            "notes": "faces right; jet: brace + raise the gauntlet (0-1), nozzle kindles (2-4, telegraph 2), flame frames "
                     "5-10 (engine draws fx_dp_flame from the spawn point and deals tick damage), vent + recover 11-13. "
                     "bash: coil (1-2), pauldron charge active 3-4 (engine lunges it)."}
    export("dp_forge_sentry", SEN_L, anims, meta)
    return meta


# =========================================================================== 3. MAGMA CRAWLER
CR_L = ["FarLegs", "Tail", "Body", "Head", "NearLegs", "FX"]
FL3 = 31.0
C_NEU = dict(P=(22.0, 24.0), S=(38.0, 23.6), Hh=(46.0, 22.0), ha=4.0, arch=0.0, jaw=0.0, eye=1,
             hn=(18.0, FL3), hf=(21.0, FL3), fn=(40.0, FL3), ff=(43.0, FL3), lift=(0, 0, 0, 0),
             tail=((-5.0, 0.6), (-5.0, 1.2), (-4.6, 0.6), (-4.0, -0.8)), seam=1.0, rot=0.0, piv=(0, 0),
             smear=None, splash=0, drip=0, wind=0.0, sub=False)
CP = mk(C_NEU)


def cr_leg(L, hip, foot, front, bias):
    k = ik(hip, (foot[0], foot[1] - 0.8), 4.0, 3.8, (-1, -0.6) if front else (1, -0.6))
    L.paint(n_tube([hip, k, (foot[0], foot[1] - 0.8)], [1.7, 1.2, 0.9]), "S", bias)
    L.paint(n_dome((foot[0] + 0.8, foot[1] - 0.4), 1.5, 0.7), "S", bias, ao=0)
    L.fixed({ip((foot[0] + 2.2, foot[1] - 0.2)): "S5" if bias >= 0 else "S3"})
    return k


def draw_crawler(p, fi, sw):
    Ls = {n: Layer(n) for n in CR_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    P, S = T(p["P"]), T(p["S"])
    ax = sub(S, P)
    ln = math.hypot(*ax)
    fwd = (ax[0] / ln, ax[1] / ln)
    up = (fwd[1], -fwd[0])
    dn = (-up[0], -up[1])
    # far legs
    Fl = Ls["FarLegs"]
    cr_leg(Fl, madd(P, (fwd, 1.0), (dn, 1.0)), add(T(p["hf"]), (0, -p["lift"][1])), False, -2)
    cr_leg(Fl, madd(S, (fwd, -1.0), (dn, 1.0)), add(T(p["ff"]), (0, -p["lift"][3])), True, -2)
    # tail
    Tl = Ls["Tail"]
    pts = [madd(P, (fwd, -2.0))]
    for (dx, dy) in p["tail"]:
        pts.append(add(pts[-1], rot((dx - sw * 0.2, dy), math.degrees(math.atan2(fwd[1], fwd[0])) * 0.5)))
    tp = curve(pts, 4)
    tm = Tl.paint(n_tube(tp, [2.6 - 2.0 * i / (len(tp) - 1) for i in range(len(tp))]), "S", -1)
    # body: long, low, a row of overlapping obsidian scutes along the spine with magma between them
    Bd = Ls["Body"]
    c0, c1 = madd(P, (fwd, -1.6)), madd(lerp(P, S, 0.5), (up, 0.8 + p["arch"]))
    cp = curve([c0, c1, madd(S, (fwd, 1.6))], 6)
    radii = [3.4 + 0.7 * math.sin(math.pi * i / (len(cp) - 1)) for i in range(len(cp))]
    bm = Bd.paint(n_tube(cp, radii), "S", 0)
    # belly glows (it swims in lava)
    Bd.decal([q for q in bm if (q[0], q[1] + 1) not in bm], "O2")
    Bd.decal([q for q in bm if (q[0], q[1] + 1) in bm and (q[0], q[1] + 2) not in bm], "U3")
    # scutes: plates along the dorsal line separated by molten seams
    scut = {}
    for k in range(7):
        t = 0.02 + k * 0.15
        c = madd(lerp(c0, madd(S, (fwd, 1.6)), t), (up, radii[min(len(radii) - 1, int(t * len(radii)))] * 0.55 + p["arch"] * math.sin(math.pi * t)))
        for q in mask_disc(c, 2.3, 1.6):
            if q in bm:
                scut[q] = k
    for q, k in scut.items():
        e = Bd.px[q]
        e[2] += 1
    for q, k in scut.items():
        for d in ((1, 0), (-1, 0)):
            nq = (q[0] + d[0], q[1] + d[1])
            if nq in scut and scut[nq] != k and p["seam"] > 0:
                Bd.decal([q], "O3" if p["seam"] > 1.2 else "O2")
    # spine ridge spikes
    for k in range(6):
        t = 0.08 + k * 0.16
        c = madd(lerp(c0, S, t), (up, 3.8 + p["arch"] * math.sin(math.pi * t)))
        q = ip(c)
        while q in bm:
            q = (q[0], q[1] - 1)
        Bd.fixed({q: "S4", (q[0] - 1, q[1] + 1): "S3"})
    info["hit"] |= set(bm)
    # head: wedge skull, heavy jaw, ember eye
    Hl = Ls["Head"]
    Hh = T(p["Hh"])
    ha = p["ha"] + p["rot"]
    G = lambda x, y: add(Hh, rot((x, y), ha))
    Hl.paint(n_tube([madd(S, (fwd, 0.4)), G(-3.0, 0.6)], [3.3, 2.7]), "S", 0)
    hinge = (-2.0, 1.2)
    J = lambda x, y: G(*add(hinge, rot(sub((x, y), hinge), p["jaw"] * 40)))
    if p["jaw"] > 0.1:
        Hl.fixed({q: ("O4" if hash01(*q, 3) < 0.4 else "O2") for q in poly_mask([G(-1.8, 1.0), G(8.4, 1.2), J(8.0, 1.6), J(-1.6, 1.6)])})
    jm = poly_mask([J(-2.4, 1.2), J(8.4, 1.4), J(8.0, 2.6), J(1.0, 3.2), J(-2.6, 2.6)])
    Hl.paint(n_plate(jm, 0.8, (0, 0.3)), "S", -1)
    skull = [G(-3.6, -1.8), G(-0.6, -3.0), G(3.0, -2.6), G(8.4, -0.6), G(9.8, 0.6), G(8.6, 1.4), G(0.0, 1.6), G(-3.8, 1.4)]
    sm = poly_mask(skull)
    Hl.paint(n_plate(sm, 1.3, (-0.15, -0.35), 1.1), "S", 0)
    for x in (3.0, 5.4, 7.6):
        q = ip(G(x, 1.3)); Hl.fixed({q: "S5"})
    e = ip(G(1.8, -1.2))
    if p["eye"]:
        Hl.fixed({e: "O5", (e[0] + 1, e[1]): "O4", (e[0] - 1, e[1]): "O2"})
    Hl.decal([q for q in line(G(-2.4, -2.0), G(3.0, -2.6)) if q in sm], ("S", 5))
    info["jaw"] = G(8.4, 1.6)
    info["eye"] = G(1.8, -1.2)
    info["hit"] |= set(Hl.px)
    # near legs
    Nl = Ls["NearLegs"]
    cr_leg(Nl, madd(P, (fwd, 0.6), (dn, 1.2)), add(T(p["hn"]), (0, -p["lift"][0])), False, 0)
    cr_leg(Nl, madd(S, (fwd, -1.2), (dn, 1.4)), add(T(p["fn"]), (0, -p["lift"][2])), True, 0)
    for L_ in (Bd, Hl, Tl, Nl, Fl):
        glow_under(L_, ("O1", "U2"))
    for L_ in (Bd, Hl, Tl):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "S" and not isinstance(e_[3], str)], ("S", 5))
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= swept(FX, T(g0), a0, T(g1), a1, u0, u1, hw=1.3, pal="magma", taper=0.5)
    if p["drip"]:
        for k, src in enumerate((madd(lerp(P, S, 0.3), (dn, 3.4)), madd(lerp(P, S, 0.7), (dn, 3.6)), G(6.0, 2.8), tp[len(tp) // 2])):
            ph = (fi * 0.45 + k * 0.33) % 1.0
            x0, y0 = ip(src)
            n = 1 + int(ph * 3)
            for j in range(n):
                FX.put([(x0, y0 + j)], "O4" if j < n - 1 else "O5")
    if p["splash"]:
        cx = P[0] + 8
        for k in range(14):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 1, 23))
            r = (3 + 8 * hash01(k, 2, 23)) * (0.8 if p["splash"] == 1 else 1.2)
            FX.put([ip((cx + math.cos(a) * r * 1.6, FL3 - 0.5 + math.sin(a) * r * (0.9 if p["splash"] == 1 else 0.5)))],
                   ("O5", "O4", "O3", "O2")[k % 4] if p["splash"] == 1 else ("O2", "O1")[k % 2])
    return Ls, info


def c_sub():
    fr = []
    for i in range(4):
        ph = 2 * math.pi * i / 4
        w = math.sin(ph)
        fr.append((170, CP(P=(22.0, 25.0 + 0.4 * w), S=(38.0, 24.6 - 0.4 * w), Hh=(46.0, 23.6), ha=0, eye=1,
                           hn=(16.0, 29.0), hf=(19.0, 29.6), fn=(42.0, 29.0), ff=(45.0, 29.6), seam=1.4,
                           tail=((-5.0, 0.6 + w), (-5.0, 1.2 - w * 1.4), (-4.6, 0.6 + w * 1.6), (-4.0, -0.8 - w)))))
    return fr


def c_burst():
    fr = [
        (130, CP(P=(22.0, 26.0), S=(38.0, 24.0), Hh=(45.0, 20.0), ha=-24, jaw=0.2, seam=1.8, drip=1)),
        (130, CP(P=(22.0, 25.0), S=(37.0, 21.6), Hh=(44.0, 17.0), ha=-34, jaw=0.35, seam=2.0, drip=1, splash=1)),
        (150, CP(P=(21.0, 24.4), S=(36.0, 19.6), Hh=(42.4, 13.6), ha=-46, jaw=0.6, seam=2.0, drip=1, splash=1)),
    ]
    arc = [(-40, 0.9), (-22, 1.0), (-4, 0.8), (12, 0.6), (26, 0.3)]
    for k, (a, jw) in enumerate(arc):
        fr.append((90, CP(P=(20.0, 20.0), S=(36.0, 20.0), Hh=(44.0, 19.0), ha=a * 0.3, rot=a, piv=(30.0, 20.0), jaw=jw, seam=2.0,
                          hn=(13.0, 24.0), hf=(15.0, 25.0), fn=(44.0, 25.0), ff=(46.0, 26.0), drip=1,
                          tail=((-5.0, 1.6), (-5.0, 1.2), (-4.4, -0.4), (-3.6, -1.6)))))
    return fr


def c_crawl():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        fr.append((95, CP(P=(22.0 + 0.4 * c, 24.0), S=(38.0 + 0.4 * c, 23.6 + 0.4 * s), Hh=(46.0, 22.0 + 0.4 * s), ha=4 + 3 * s,
                          hn=(18.0 + 3.0 * c, FL3), hf=(21.0 - 3.0 * c, FL3), fn=(40.0 - 3.0 * c, FL3), ff=(43.0 + 3.0 * c, FL3),
                          lift=(max(0, s) * 1.6, max(0, -s) * 1.6, max(0, -s) * 1.6, max(0, s) * 1.6),
                          tail=((-5.0, 0.6 + s * 0.8), (-5.0, 1.2 - s), (-4.6, 0.6 + s * 1.2), (-4.0, -0.8 - s * 0.8)))))
    return fr


def c_bite():
    return [
        (120, CP(S=(36.6, 23.0), Hh=(43.6, 20.4), ha=-10, jaw=0.3, seam=1.4)),
        (200, CP(P=(21.0, 24.0), S=(35.0, 22.6), Hh=(41.4, 19.0), ha=-24, jaw=0.9, seam=1.8)),
        (90, CP(P=(21.0, 24.0), S=(35.0, 22.6), Hh=(41.0, 18.6), ha=-28, jaw=1.0, seam=2.0)),
        (70, CP(P=(24.0, 24.0), S=(41.0, 24.0), Hh=(50.0, 24.0), ha=12, jaw=0.9, seam=2.0, hn=(20.0, FL3), fn=(44.0, FL3), ff=(47.0, FL3),
                smear=[((42.0, 16.0), -60, (56.0, 26.0), 20, 0.5, 3.5)])),
        (80, CP(P=(24.6, 24.0), S=(42.0, 24.4), Hh=(51.0, 25.0), ha=16, jaw=0.1, seam=1.6, hn=(20.0, FL3), fn=(44.0, FL3), ff=(47.0, FL3))),
        (150, CP(P=(23.0, 24.0), S=(40.0, 24.0), Hh=(48.0, 23.0), ha=8, seam=1.2, hn=(19.0, FL3), fn=(42.0, FL3), ff=(45.0, FL3))),
        (150, CP()),
    ]


def c_sink():
    return [
        (100, CP(S=(38.0, 24.6), Hh=(46.0, 24.0), ha=14, seam=1.4)),
        (100, CP(P=(22.0, 26.0), S=(38.0, 26.6), Hh=(46.0, 27.0), ha=22, seam=1.6, splash=1)),
        (110, CP(P=(22.0, 28.0), S=(38.0, 29.0), Hh=(46.0, 30.0), ha=26, seam=1.6, splash=1)),
        (120, CP(P=(22.0, 30.0), S=(38.0, 31.0), Hh=(46.0, 32.0), ha=26, seam=1.4, splash=2)),
        (140, CP(P=(22.0, 33.0), S=(38.0, 34.0), Hh=(46.0, 35.0), ha=26, seam=1.2, splash=2)),
    ]


def c_hurt():
    return [(90, CP(S=(36.4, 22.0), Hh=(42.0, 17.0), ha=-34, jaw=0.9, seam=2.2)),
            (140, CP(S=(37.4, 23.0), Hh=(44.6, 20.6), ha=-8, jaw=0.2))]


def c_death():
    lie = dict(P=(22.0, 27.0), S=(38.0, 27.6), Hh=(46.6, 28.0), ha=10, eye=0, seam=0.4,
               hn=(18.0, FL3), hf=(21.0, FL3), fn=(40.0, FL3), ff=(43.0, FL3), tail=((-5.0, 1.6), (-5.0, 1.0), (-4.6, 0.4), (-4.0, 0.0)))
    sn = ["FarLegs", "Tail", "Body", "Head", "NearLegs"]
    pal = ("O4", "O3", "O2", "S3", "S2")
    return [
        (100, CP(S=(36.0, 21.0), Hh=(41.0, 15.0), ha=-46, jaw=1.0, seam=2.4)),
        (120, CP(**dict(lie, seam=1.6, eye=1), jaw=0.5)),
        (160, CP(**lie)),
        (140, CP(**lie, post=collapse(sn, 0.7, 0.12, pal=pal, spread=0.15))),
        (160, CP(**lie, post=collapse(sn, 0.45, 0.24, pal=pal, spread=0.2))),
        (600, CP(**lie, post=collapse(sn, 0.25, 0.3, pal=pal, spread=0.25))),
    ]


def build_crawler():
    K.setup(64, 32)
    anims, infos = E3.render_anims("dp_magma_crawler", CR_L, draw_crawler,
                                   [("sub", c_sub), ("burst", c_burst), ("crawl", c_crawl), ("bite", c_bite), ("sink", c_sink),
                                    ("hurt", c_hurt), ("death", c_death)], sway_key="S", loops=("sub", "crawl"))
    meta = {"native": 1, "frame": [64, 32], "anchor": [30, 32],
            "hurtbox": hurtbox(anims, ["Body", "Head"], inset=(2, 1, 2), frame=0),
            "attacks": {"bite": {"active": [3, 4], "hit": hit_rect(infos, "bite", [3, 4], x_min=40)}},
            "burst_leap": 3,
            "telegraph": {"bite": {"frame": 1, "at": spawn_pt(infos["bite"][1]["eye"])},
                          "burst": {"frame": 0, "at": spawn_pt(infos["burst"][0]["eye"])}},
            "notes": "faces right; sub = swimming undulation drawn low (the engine sinks it so only the scutes break the "
                     "lava surface); burst 0-2 = rising from the lava (telegraph), 3-7 = the arching leap (engine flies it); "
                     "sink = diving back in."}
    # hurtbox from the crawl pose (feet on the floor)
    meta["hurtbox"] = hurtbox([a for a in anims if a[0] == "crawl"], ["Body", "Head"], inset=(2, 1, 2), frame=0)
    export("dp_magma_crawler", CR_L, anims, meta)
    return meta


ENEMIES = {"dp_slag_imp": build_imp, "dp_forge_sentry": build_sentry, "dp_magma_crawler": build_crawler}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    for name, fn in ENEMIES.items():
        if only and name not in only:
            continue
        meta = fn()
        print(name, json.dumps({k: v for k, v in meta.items() if k != "notes"}))
        if BUILD:
            print("  tags", E3.verify(name))


if __name__ == "__main__":
    main()
