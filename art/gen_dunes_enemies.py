#!/usr/bin/env python3
"""Enemies of the Sunscorched Dunes (agent DU) -- ART_SPEC section 4 contract, method + helpers from enemy_kit.py /
gen_enemies3.py (read-only reuse), palette from dunes_kit.py.

    python3 art/gen_dunes_enemies.py [--preview] [--only du_priest,...]

    du_priest    48x48  a gaunt mummified sun-priest: dusty linen wrappings, a gold usekh collar, a sun-disc crest between
                        slender horns, amber pin-light eyes; a tall staff crowned with a sun-disc.
                        idle(4) walk(6) cast(10, spawn f6) swipe(8, active 4-5) hurt(2) death(6)
    du_scarab    40x24  a swarm of three black-green scarabs with a bronze sheen; burrows and bursts out of the sand.
                        idle(4) crawl(6) bite(7, active 3-4) burrow(6) emerge(6) hurt(2) death(6)
    du_jackal    64x64  a jackal-headed temple guardian: obsidian-black body, gold collar and armbands, white linen kilt,
                        a long crescent glaive.  idle(4) walk(6) guard(2) combo(12, active 4-5 / 8-9) lunge(9, 4-6) hurt(2) death(8)
    du_soldier   40x40  a soldier of packed sand called up by the Pharaoh: a crude helm, amber eye-slits, a sand-bronze
                        khopesh.  rise(6) idle(4) walk(6) attack(8, active 4-5) hurt(2) death(6)
All face RIGHT, feet on the bottom row.  Previews: art/previews/<name>.png + <name>_hitbox.png
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,  # noqa: E402
                       poly_mask, n_plate, n_dome, n_capsule, swept, dirv, bbox, basis, leg, arm)
import gen_enemies3 as E3  # noqa: E402   (read-only reuse of its helpers)
from gen_enemies3 import n_tube, curve, hit_rect, hurtbox, mk, spawn_pt, rot, madd, disc_glow, halo_dots, collapse  # noqa: E402
import dunes_kit as DK  # noqa: E402
from dunes_kit import tube, bands, glint, sun_disc, AMBER  # noqa: E402

BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None

SPEC_FRAMES = {
    "du_priest": dict(idle=4, walk=6, cast=10, swipe=8, hurt=2, death=6),
    "du_scarab": dict(idle=4, crawl=6, bite=7, burrow=6, emerge=6, hurt=2, death=6),
    "du_jackal": dict(idle=4, walk=6, guard=2, combo=12, lunge=9, hurt=2, death=8),
    "du_soldier": dict(rise=6, idle=4, walk=6, attack=8, hurt=2, death=6),
}
E3.SPEC_FRAMES.update(SPEC_FRAMES)
E3.BUILD = BUILD


def export(name, layers, anims, meta, flat_order=None):
    tags, flats = K.export(name, layers, anims, meta, build=BUILD, flat_order=flat_order)
    if meta is not None:
        E3.hitbox_preview3(name, tags, flats, meta)
    return tags, flats


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def pole(L, a, b, mat, r=0.7, bias=0):
    """A thin pole (staff / shaft) as a narrow capsule."""
    return L.paint(n_capsule(a, b, r, r, 1.0), mat, bias, ao=0)


def sandify(Ls, names, k, seed=0):
    """Speckle some pixels of the named layers toward sand (dust clinging to the dead)."""
    for n in names:
        L = Ls.get(n)
        if not L:
            continue
        pts = [q for q, e in L.px.items() if hash01(q[0], q[1], seed) < k and not isinstance(e[3], str)]
        L.decal(pts, ("z", 5))


# =========================================================================== 1. MUMMIFIED SUN-PRIEST
PR_L = ["FarArm", "FarLeg", "Skirt", "NearLeg", "Body", "Collar", "Head", "Crest", "Staff", "NearArm", "FX"]
FLp = 47
PR_NEU = dict(P=(21.5, 32.0), C=(23.0, 21.0), Hd=(25.6, 13.4), hup=(0.32, -1.0),
              fb=(18.0, FLp), ff=(25.5, FLp), kb=None, kf=None,
              hf=(31.0, 30.0), hb=(19.0, 30.5), sb=(33.0, FLp), st=(34.0, 11.0),   # staff butt / top (frame coords)
              glow=0, eye=1, lean=0.0, swipe=None, dust=0, rot=0.0, piv=(22, 40), crest=1.0, wind=0.0)
PP = mk(PR_NEU)


def draw_priest(p, fi, sw):
    Ls = {n: Layer(n) for n in PR_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    Pp, Cc, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(Cc, Pp)
    ln = math.hypot(*upv)
    F = basis(Pp, upv)
    shN, shF = F(1.6, -ln + 1.6), F(-2.0, -ln + 2.0)
    hipN, hipF = F(1.4, 0.8), F(-1.4, 0.8)
    # legs: thin, wrapped
    kf = leg(R, Ls["NearLeg"], hipN, p["ff"], 7.4, 7.6, 1.5, 1.15, "s", bias=0, knee=p["kf"], flen=2.6, heel=1.2, boot_h=1.6, pref=(1, -0.1))
    kb = leg(R, Ls["FarLeg"], hipF, p["fb"], 7.4, 7.6, 1.5, 1.15, "s", bias=-2, knee=p["kb"], flen=2.6, heel=1.2, boot_h=1.6, pref=(1, -0.1))
    for nm, hip, kn, ft, b in (("NearLeg", hipN, kf, p["ff"], 1), ("FarLeg", hipF, kb, p["fb"], 0)):
        m = set(Ls[nm].px)
        bands(Ls[nm], m, T(hip), T(ft), 2.0, ("s", 1 + b), phase=fi * 0.2)
    # skirt: pleated linen from the hips to the knee, a gold belt
    sway = sw * 0.4 - p["wind"] * 0.3
    sk = [F(-4.2, -1.6), F(4.4, -1.6), add(F(5.4, 9.0), (sway * 0.3, 0)), add(F(-5.0, 9.4), (sway, 0))]
    skm = R.plate(Ls["Skirt"], sk, "s", bevel=1.4, tilt=(-0.1, 0), strength=1.0,
                  fold=lambda x, y: (0.7 * math.sin(x * 1.3), 0), bias=0)
    Ls["Skirt"].decal([q for q in skm if (q[0] + (q[1] // 3)) % 3 == 0], ("s", 2))
    belt = poly_mask([T(F(-4.4, -2.4)), T(F(4.6, -2.4)), T(F(4.6, -0.6)), T(F(-4.4, -0.6))])
    Ls["Skirt"].paint(n_plate(belt, 0.8, (0, -0.3)), "g", 0, ao=0)
    Ls["Skirt"].decal([q for q in belt if q[0] % 3 == 0], ("u", 2))
    info["hit"] |= skm
    # torso: gaunt, wrapped; darker gaps where the linen has rotted through
    Bd = Ls["Body"]
    torso = [F(-3.6, -0.4), F(-3.2, -ln + 3.0), F(-2.4, -ln - 0.6), F(2.8, -ln - 0.6), F(3.6, -ln + 3.0), F(3.4, -0.4)]
    tm = R.plate(Bd, torso, "s", bevel=2.0, tilt=(-0.2, -0.05), strength=1.2)
    bands(Bd, tm, T(Pp), T(Cc), 2.4, ("s", 2), phase=0.4)
    Bd.decal([q for q in tm if hash01(q[0], q[1], 7) < 0.12], ("n", 2))
    info["torso"] = tm
    # far arm (holds nothing, or the staff too when casting)
    arm(R, Ls["FarArm"], shF, p["hb"], 6.4, 6.4, 1.3, 1.1, "s", bias=-2, fist="n", fist_r=1.1, pref=(-1, 0.6))
    # collar: a broad usekh of gold and lapis rows
    Cl = Ls["Collar"]
    cc = F(0.4, -ln + 0.6)
    for k, (rr, mat, lvl) in enumerate(((4.6, "g", None), (3.6, "u", 2), (2.6, "g", None))):
        m = {q for q in mask_disc(T(cc), rr, rr * 0.75) if q[1] >= T(cc)[1] - 0.5}
        if mat == "g":
            Cl.paint(n_dome(T(cc), rr, rr * 0.75, flat=0.7, tilt=(-0.2, -0.3)), "g", 0, ao=0, clip=m)
        else:
            Cl.paint({q: (0, 0, 1) for q in m}, "u", 0, ao=0)
    info["collar"] = T(cc)
    # head: a small wrapped skull, face in shadow, amber pin-light eyes
    G = basis(Hd, p["hup"])
    Hl = Ls["Head"]
    Hl.paint(n_tube([T(F(0.4, -ln - 0.2)), T(G(-0.4, 2.6))], [1.3, 1.2]), "s", -1)
    skull = [G(-2.8, 2.2), G(-3.0, -1.6), G(-1.2, -3.2), G(1.8, -3.0), G(3.4, -0.8), G(3.8, 1.4), G(2.6, 3.0), G(-0.4, 3.4)]
    hm = R.plate(Hl, skull, "s", bevel=1.6, tilt=(-0.2, -0.2), strength=1.2, bias=-1)
    bands(Hl, hm, T(G(-3, 0)), T(G(3, 0)), 2.0, ("s", 1), phase=0.7)
    face = [T(G(1.4, -1.0)), T(G(3.6, -0.6)), T(G(3.8, 1.8)), T(G(1.6, 2.4))]
    Hl.decal(list(poly_mask(face)), ("n", 1))
    e = ip(T(G(2.8, -0.2)))
    if p["eye"]:
        FX.put([e], "a4" if p["eye"] == 2 else "a3")
        FX.put([(e[0] - 1, e[1])], "a2")
    info["head"] = hm
    info["eye"] = T(G(2.8, -0.2))
    # crest: a sun-disc cradled between two slender horns
    Cr = Ls["Crest"]
    top = G(0.2, -3.0)
    disc_c = T(add(top, (-0.4, -3.8 * p["crest"])))
    for s_ in (-1, 1):
        hp = curve([T(add(top, (s_ * 1.2, 0.4))), T(add(top, (s_ * 3.8, -2.8))), T(add(top, (s_ * 3.4, -6.8))), T(add(top, (s_ * 1.8, -8.6)))], 4)
        Cr.paint(n_tube(hp, [0.9 - 0.5 * i / (len(hp) - 1) for i in range(len(hp))]), "b", 0 if s_ > 0 else -1, ao=0)
    sun_disc(Cr, disc_c, 2.1, fi, glow=p["glow"] if p["glow"] >= 2 else 0, FX=FX)
    info["disc"] = disc_c
    # the staff: bronze pole, a sun-disc on a crescent at the top
    Sf = Ls["Staff"]
    sb, st = T(p["sb"]), T(p["st"])
    staff_m = pole(Sf, sb, st, "b", 0.75, 0)
    d = unit(sub(st, sb))
    cres = [add(st, (-d[1] * k + d[0] * (1.4 - abs(k) * 0.35), d[0] * k + d[1] * (1.4 - abs(k) * 0.35))) for k in (-2.8, -1.6, 0, 1.6, 2.8)]
    Sf.paint(n_tube(cres, [0.7, 0.8, 0.8, 0.8, 0.7]), "g", 0, ao=0)
    sdc = add(st, (d[0] * 3.2, d[1] * 3.2))
    sun_disc(Sf, sdc, 2.4, fi, glow=p["glow"], FX=FX)
    info["tip"] = sdc
    info["staff"] = staff_m
    # near arm grips the staff
    arm(R, Ls["NearArm"], shN, p["hf"], 6.4, 6.4, 1.4, 1.15, "s", bias=0, fist="n", fist_r=1.2, pref=(-1, 0.7))
    bands(Ls["NearArm"], set(Ls["NearArm"].px), T(shN), T(p["hf"]), 2.0, ("s", 2), phase=0.2)
    # the swipe smear
    if p["swipe"]:
        g0, a0, g1, a1 = p["swipe"]
        L_ = math.hypot(*sub(T(p["st"]), T(p["hf"])))
        info["hit"] |= swept(FX, T(g0), a0, T(g1), a1, L_ - 4, L_ + 3, hw=0.8, pal="sun", taper=0.6)
    if p["dust"]:
        for k in range(8):
            q = (int(Pp[0] + (hash01(k, fi, 3) - 0.5) * 16), FLp - int(hash01(k, fi, 4) * 3))
            FX.put([q], ("z6", "z5", "z4")[k % 3])
    return Ls, info


def p_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        fr.append((200, PP(C=(23.0, 21.0 + b * 0.5), Hd=(25.6, 13.4 + b * 0.7), hb=(19.0, 30.6 + b * 0.4), hf=(31.0, 30.0 + b * 0.3),
                           glow=1 if i == 2 else 0)))
    return fr


def p_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        bob = 0.8 * abs(s)
        fr.append((140, PP(P=(21.5, 32.0 + bob), C=(23.4, 21.2 + bob), Hd=(26.2, 13.8 + bob), hup=(0.38, -1.0),
                           ff=(22.0 + 4.2 * c, FLp - max(0, s) * 1.8), fb=(21.0 - 4.2 * c, FLp - max(0, -s) * 1.8),
                           hf=(31.0 + 0.6 * c, 30.0 + bob), sb=(33.0 + 1.4 * c, FLp - max(0, s) * 1.0), st=(34.0 + 1.0 * c, 11.0 + bob),
                           hb=(19.5 - 1.6 * c, 30.4 + bob))))
    return fr


def p_cast():
    raise_ = dict(P=(21.0, 32.4), C=(22.0, 21.4), Hd=(24.2, 13.6), hup=(0.1, -1.0))
    up = dict(hf=(31.0, 17.0), sb=(33.0, 39.0), st=(31.4, 1.0), hb=(27.0, 19.0))
    return [
        (140, PP(**raise_, hf=(31.0, 26.0), sb=(33.0, 44.0), st=(33.0, 6.0), hb=(21.0, 27.0), glow=1)),
        (140, PP(**raise_, hf=(31.0, 21.0), sb=(33.0, 41.0), st=(32.2, 3.0), hb=(23.0, 21.0), glow=1)),
        (160, PP(**raise_, **up, glow=2, eye=2)),
        (160, PP(**raise_, **up, glow=2, eye=2)),
        (160, PP(**raise_, **up, glow=3, eye=2)),
        (120, PP(**raise_, **up, glow=3, eye=2)),
        (90, PP(P=(22.0, 32.2), C=(24.0, 21.4), Hd=(27.0, 14.2), hup=(0.5, -1.0), hf=(30.0, 20.0), sb=(33.0, 40.0), st=(33.4, 1.6),
                hb=(26.0, 22.0), glow=3, eye=2)),
        (120, PP(P=(22.0, 32.2), C=(24.0, 21.4), Hd=(27.0, 14.2), hup=(0.5, -1.0), hf=(30.4, 22.0), sb=(33.4, 42.0), st=(33.8, 3.6),
                 hb=(24.0, 25.0), glow=1)),
        (140, PP(hf=(31.0, 28.0), sb=(33.0, 46.0), st=(33.6, 9.0), glow=0)),
        (160, PP()),
    ]


def p_swipe():
    wind = dict(P=(21.0, 32.4), C=(21.6, 21.6), Hd=(23.8, 14.0), hup=(0.05, -1.0))
    lunge = dict(P=(23.0, 32.6), C=(26.4, 22.2), Hd=(29.6, 15.4), hup=(0.62, -1.0), ff=(29.0, FLp), fb=(17.0, FLp))
    return [
        (120, PP(**wind, hf=(26.0, 24.0), sb=(22.0, 40.0), st=(33.0, 6.0), hb=(19.0, 28.0))),
        (150, PP(**wind, hf=(22.0, 19.0), sb=(26.0, 36.0), st=(12.0, 4.0), hb=(18.0, 24.0), eye=2, glow=1)),
        (170, PP(**wind, hf=(21.0, 18.0), sb=(27.0, 35.0), st=(10.0, 5.0), hb=(18.0, 24.0), eye=2, glow=1)),
        (60, PP(**lunge, hf=(31.0, 22.0), sb=(24.0, 30.0), st=(44.0, 12.0), hb=(27.0, 24.0), eye=2,
                swipe=((21.0, 18.0), -128, (31.0, 22.0), -18))),
        (70, PP(**lunge, hf=(32.0, 26.0), sb=(22.0, 24.0), st=(45.0, 34.0), hb=(28.0, 27.0), eye=2,
                swipe=((31.0, 22.0), -18, (32.0, 26.0), 40))),
        (120, PP(**lunge, hf=(31.0, 28.0), sb=(24.0, 22.0), st=(42.0, 40.0), hb=(27.0, 28.0))),
        (140, PP(P=(22.0, 32.2), C=(24.0, 21.6), Hd=(27.0, 14.2), hup=(0.4, -1.0), hf=(30.0, 29.0), sb=(32.0, 45.0), st=(33.0, 9.0))),
        (150, PP()),
    ]


def p_hurt():
    return [(90, PP(P=(20.4, 32.0), C=(19.4, 21.4), Hd=(19.4, 14.0), hup=(-0.4, -1.0), hf=(27.0, 29.0), sb=(30.0, 45.0), st=(24.0, 8.0),
                    hb=(16.0, 27.0), eye=2)),
            (130, PP(P=(21.0, 32.0), C=(21.6, 21.2), Hd=(23.4, 13.8), hup=(0.1, -1.0)))]


def p_death():
    kneel = dict(P=(21.0, 38.0), C=(23.6, 28.0), Hd=(26.6, 21.4), hup=(0.6, -1.0), kf=(26.0, 40.0), ff=(24.0, FLp),
                 kb=(18.0, 45.0), fb=(12.0, FLp), hf=(29.0, 38.0), sb=(38.0, FLp), st=(40.0, 12.0), hb=(21.0, 38.0), eye=0)
    names = ["FarArm", "FarLeg", "Skirt", "NearLeg", "Body", "Collar", "Head", "Crest", "Staff", "NearArm"]
    pal = ("a3", "z6", "z5", "z4", "z3")
    return [
        (100, PP(P=(20.4, 32.4), C=(19.0, 22.0), Hd=(18.6, 14.6), hup=(-0.5, -1.0), hf=(27.0, 28.0), st=(22.0, 10.0), hb=(16.0, 28.0), eye=2)),
        (160, PP(**kneel)),
        (160, PP(**kneel, post=collapse(names, 0.75, 0.15, seed=3, pal=pal, spread=0.3))),
        (160, PP(**kneel, post=collapse(names, 0.45, 0.3, seed=3, pal=pal, spread=0.5))),
        (180, PP(**kneel, post=collapse(names, 0.2, 0.42, seed=3, pal=pal, spread=0.8))),
        (600, PP(**kneel, dust=1, post=collapse(names, 0.08, 0.5, seed=3, pal=pal, spread=1.0))),
    ]


def build_priest():
    K.setup(48, 48)
    anims, infos = E3.render_anims("du_priest", PR_L, draw_priest,
                                   [("idle", p_idle), ("walk", p_walk), ("cast", p_cast), ("swipe", p_swipe), ("hurt", p_hurt),
                                    ("death", p_death)], sway_key="C", loops=("idle", "walk"))
    meta = {"native": 1, "frame": [48, 48], "anchor": [22, 48],
            "hurtbox": hurtbox(anims, ["Body", "Head", "Skirt"], inset=(1, 2, 1)),
            "attacks": {"swipe": {"active": [3, 4], "hit": hit_rect(infos, "swipe", [3, 4], x_min=24)}},
            "spawn": {"cast": {"frame": 6, "at": spawn_pt(infos["cast"][6]["tip"])}},
            "telegraph": {"cast": {"frame": 2, "at": spawn_pt(infos["cast"][2]["tip"])},
                          "swipe": {"frame": 1, "at": spawn_pt(infos["swipe"][1]["tip"])}},
            "notes": "faces right. cast: the staff rises, its sun-disc flares (2-5), the engine calls a sun-flare down on the "
                     "player at frame 6. swipe: staff swung overhead and down in front (active 3-4)."}
    export("du_priest", PR_L, anims, meta)
    return meta


# =========================================================================== 2. SCARAB SWARM
SC_L = ["Back", "Mid", "Front", "FX"]
FLs = 23
SC_NEU = dict(bs=[(26.0, 0.0, 1.0, 0.0), (15.0, -0.5, 0.78, 0.0), (8.5, 0.0, 0.64, 0.0)],   # beetles: (x, lift, scale, tilt)
              ph=0.0, sink=0.0, spray=0, flip=False, scatter=0.0, bite=0.0, gone=0.0)
SCP = mk(SC_NEU)


def beetle(L, FX, x, lift, s, tilt, ph, fi, bias, bite=0.0, flip=False, info=None, idx=0):
    """One scarab in profile facing right: domed carapace, small head, forward mandibles, three legs a side."""
    by = FLs - 2.6 * s - lift
    if flip:
        by = FLs - 3.4 * s - lift
    c = (x, by - 1.6 * s)
    rx, ry = 5.2 * s, 3.4 * s
    # legs (drawn first; the near three over the carapace edge get drawn on the Front layer by caller order)
    for k in range(3):
        base = (x - 2.6 * s + k * 2.4 * s, by)
        swing = math.sin(ph + k * 2.1 + idx) * 1.4 * s
        knee = (base[0] + swing * 0.6 + 0.6 * s, base[1] + 0.6 * s - (1.4 * s if flip else 0))
        foot = (base[0] + swing + (1.2 * s if k == 2 else -0.4 * s), FLs - lift * 0.2 if not flip else by - 3.4 * s)
        for q in polyline([ip(base), ip(knee), ip(foot)]):
            L.fixed({q: "h1" if bias < 0 else "h2"})
    rx, ry = 4.4 * s, 3.2 * s
    c = (x - 0.6 * s, by - 1.4 * s)
    m = mask_disc(c, rx, ry)
    m = {q for q in m if q[1] <= by + 0.5}
    L.paint(n_dome(c, rx, ry, flat=0.85, tilt=(-0.2 + tilt, -0.35)), "c", bias, ao=0, clip=m)
    # elytra seam, and the bronze sheen arcing along the top
    L.decal([q for q in m if abs(q[1] + .5 - (c[1] + ry * 0.1)) < 0.5 and q[0] < c[0] + rx * 0.5], ("c", 1))
    L.decal([q for q in m if (q[0], q[1] - 1) not in m and q[0] < c[0] + rx * 0.5], ("c", 6))
    # pronotum (thorax shield) + head + mandibles
    tc = (c[0] + rx * 0.95, c[1] + ry * 0.2)
    tm = mask_disc(tc, 2.2 * s, 2.0 * s)
    tm = {q for q in tm if q[1] <= by + 0.5}
    L.paint(n_dome(tc, 2.2 * s, 2.0 * s, tilt=(-0.2, -0.35)), "c", bias, ao=1, clip=tm)
    m = m | tm
    hc = (tc[0] + 2.1 * s, tc[1] + 0.9 * s)
    L.paint(n_dome(hc, 1.3 * s, 1.1 * s, tilt=(-0.1, -0.3)), "h", bias, ao=0)
    op = 0.6 + bite * 1.2
    for sgn in (-1, 1):
        a = (hc[0] + 1.0 * s, hc[1] + sgn * 0.3)
        b_ = (hc[0] + 2.6 * s, hc[1] + sgn * op * s + 0.4)
        for q in polyline([ip(a), ip(b_)]):
            L.fixed({q: "g4" if sgn < 0 else "g3"})
    # tiny amber eye
    FX.put([ip((hc[0] + 0.4 * s, hc[1] - 0.6 * s))], "a3")
    if info is not None:
        info.setdefault("bodies", set()).update(m)
        info["head%d" % idx] = hc


def draw_scarab(p, fi, sw):
    Ls = {n: Layer(n) for n in SC_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    order = [("Back", 2, -2), ("Mid", 1, -1), ("Front", 0, 0)]
    for nm, i, bias in order:
        x, lift, s, tilt = p["bs"][i]
        if p["scatter"] > 0:
            x += (i - 1) * p["scatter"] * 8
            lift += p["scatter"] * (4 + i * 3)
        beetle(Ls[nm], FX, x, lift, s, tilt, p["ph"] + i * 1.3, fi, bias, bite=p["bite"] if i == 0 else 0, flip=p["flip"], info=info, idx=i)
    # sinking into / rising out of the sand: everything below the sand line is gone; a low mound of sand marks the spot
    if p["sink"] > 0:
        sk = min(1.0, p["sink"])
        for L in Ls.values():
            if isinstance(L, Layer):
                moved = {}
                for q, e in L.px.items():
                    moved[(q[0], q[1] + int(round(sk * 9)))] = e
                L.px = {q: e for q, e in moved.items() if q[1] < FLs - 1}
        FX.px = {(q[0], q[1] + int(round(sk * 9))): c for q, c in FX.px.items() if q[1] + int(round(sk * 9)) < FLs - 1}
        for x in range(4, 36):
            h = int(1 + 2 * sk * (1 - abs(x - 20) / 16) + 0.6 * math.sin(x * 0.9 + fi))
            for y in range(FLs - h, FLs + 1):
                FX.put([(x, y)], "z6" if y == FLs - h else "z5")
    if p["spray"]:
        for k in range(14):
            a = -math.pi * (0.1 + 0.8 * hash01(k, fi, 7))
            rr = 2 + 9 * hash01(k, fi + 1, 7) * p["spray"]
            cx_ = 8 + 22 * hash01(k, 3, 7)
            FX.put([ip((cx_ + math.cos(a) * rr, FLs - 1 + math.sin(a) * rr * 0.7))], ("z7", "z6", "z5")[k % 3])
    info["hit"] |= info.get("bodies", set())
    if p["gone"] > 0:
        for L in Ls.values():
            if isinstance(L, Layer):
                L.erase([q for q in list(L.px) if hash01(q[0], q[1], 11) < p["gone"]])
    return Ls, info


def s_idle():
    fr = []
    for i in range(4):
        ph = i * math.pi / 2
        fr.append((150, SCP(bs=[(26.0, 0.3 * math.sin(ph), 1.0, 0.0), (15.0, -0.5 + 0.3 * math.cos(ph), 0.78, 0.0), (8.5, 0.3 * math.sin(ph + 1), 0.64, 0.0)],
                            ph=ph * 0.2)))
    return fr


def s_crawl():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        fr.append((70, SCP(bs=[(26.0 + 0.5 * math.sin(ph), 0.4 * abs(math.sin(ph)), 1.0, 0.0), (15.0 + 0.5 * math.sin(ph + 2), -0.5 + 0.4 * abs(math.sin(ph + 2)), 0.78, 0.0),
                               (8.5 + 0.5 * math.sin(ph + 4), 0.4 * abs(math.sin(ph + 4)), 0.64, 0.0)], ph=ph)))
    return fr


def s_bite():
    return [
        (110, SCP(bs=[(24.0, 0.0, 1.0, 0.1), (14.0, -0.5, 0.78, 0.0), (8.0, 0.0, 0.64, 0.0)], bite=0.5)),
        (160, SCP(bs=[(23.0, 0.0, 1.0, 0.15), (13.4, -0.5, 0.78, 0.1), (7.6, 0.0, 0.64, 0.0)], bite=1.0)),
        (70, SCP(bs=[(28.0, 3.0, 1.0, -0.1), (17.0, 1.6, 0.78, 0.0), (10.0, 0.6, 0.64, 0.0)], bite=1.0, ph=1.0)),
        (70, SCP(bs=[(31.0, 2.0, 1.0, -0.2), (19.0, 1.0, 0.78, -0.1), (11.0, 0.4, 0.64, 0.0)], bite=0.1, ph=2.0)),
        (90, SCP(bs=[(31.0, 0.0, 1.0, 0.0), (19.0, -0.5, 0.78, 0.0), (11.0, 0.0, 0.64, 0.0)], bite=0.3, ph=3.0)),
        (110, SCP(bs=[(29.0, 0.0, 1.0, 0.0), (17.0, -0.5, 0.78, 0.0), (10.0, 0.0, 0.64, 0.0)], ph=4.0)),
        (120, SCP()),
    ]


def s_burrow():
    return [(90, SCP(sink=min(1.0, k / 5.0), spray=1 if k < 5 else 0, ph=k * 1.2)) for k in range(1, 7)]


def s_emerge():
    fr = []
    for k in range(6):
        sink = max(0.0, 1.0 - k * 0.3)
        fr.append((80, SCP(sink=sink, spray=1 if k < 4 else 0, ph=k, bite=0.8 if k in (2, 3) else 0.0,
                           bs=[(26.0, 1.6 if k == 3 else 0.0, 1.0, 0.0), (15.0, -0.5, 0.78, 0.0), (8.5, 0.0, 0.64, 0.0)])))
    return fr


def s_hurt():
    return [(90, SCP(bs=[(24.0, 1.0, 1.0, 0.3), (14.0, 0.5, 0.78, 0.3), (8.0, 0.4, 0.64, 0.2)])), (120, SCP())]


def s_death():
    return [(90, SCP(flip=True)), (100, SCP(flip=True, scatter=0.3)), (100, SCP(flip=True, scatter=0.6, gone=0.2)),
            (110, SCP(flip=True, scatter=0.8, gone=0.45, spray=1)), (130, SCP(flip=True, scatter=1.0, gone=0.75, spray=1)),
            (500, SCP(flip=True, scatter=1.1, gone=1.0))]


def build_scarab():
    K.setup(40, 24)
    anims, infos = E3.render_anims("du_scarab", SC_L, draw_scarab,
                                   [("idle", s_idle), ("crawl", s_crawl), ("bite", s_bite), ("burrow", s_burrow), ("emerge", s_emerge),
                                    ("hurt", s_hurt), ("death", s_death)], sway_key="ph", loops=("idle", "crawl"))
    meta = {"native": 1, "frame": [40, 24], "anchor": [20, 24],
            "hurtbox": hurtbox(anims, ["Front", "Mid", "Back"], inset=(1, 1, 1)),
            "attacks": {"bite": {"active": [2, 3], "hit": hit_rect(infos, "bite", [2, 3], x_min=20)}},
            "telegraph": {"bite": {"frame": 1, "at": spawn_pt(infos["bite"][1]["head0"])}},
            "notes": "a swarm of three; bite = the lead beetle leaps (engine lunges it); burrow/emerge sink into / burst from the sand "
                     "(the engine hides it and draws a ripple while it travels under the sand)."}
    export("du_scarab", SC_L, anims, meta)
    return meta


# =========================================================================== 3. JACKAL-HEADED GUARDIAN
JK_L = ["Glaive_back", "FarArm", "FarLeg", "Body", "Kilt", "NearLeg", "Head", "NearArm", "Glaive", "FX"]
FLj = 63
JK_NEU = dict(P=(27.0, 42.0), C=(28.4, 27.4), Hd=(31.4, 17.6), hup=(0.28, -1.0),
              fb=(22.0, FLj), ff=(32.5, FLj), kb=None, kf=None,
              hf=(36.0, 40.0), hb=(22.0, 38.0), gang=-78, gu0=-16, gu1=30, back=False,   # glaive: grip at hf, angle, extent
              eye=1, smear=None, thrust=None, rot=0.0, piv=(28, 50), dust=0, jaw=0.0, wind=0.0, guard=False, lean=0.0)
JP = mk(JK_NEU)


def glaive(Lg, FX, grip, ang, u0, u1, fi, info, phase_glow=0):
    """Long bronze shaft, a gold crescent blade at the head, a forked butt (the was-sceptre fork)."""
    ca, sa = dirv(ang)
    a = (grip[0] + ca * u0, grip[1] + sa * u0)
    b_ = (grip[0] + ca * u1, grip[1] + sa * u1)
    shaft = pole(Lg, a, b_, "b", 0.8, 0)
    # forked butt
    for sgn in (-1, 1):
        f0 = a
        f1 = (a[0] - ca * 2.6 - sa * sgn * 1.4, a[1] - sa * 2.6 + ca * sgn * 1.4)
        for q in polyline([ip(f0), ip(f1)]):
            Lg.fixed({q: "b4"})
    # crescent blade: an arc bulging to the blade's "front" side (+normal), tips curling back
    nx, ny = -sa, ca
    pts_o, pts_i = [], []
    for k in range(13):
        t = k / 12
        u = u1 - 9.5 + t * 12.0
        bulge = math.sin(t * math.pi)
        pts_o.append((grip[0] + ca * u + nx * (1.0 + 5.8 * bulge), grip[1] + sa * u + ny * (1.0 + 5.8 * bulge)))
        pts_i.append((grip[0] + ca * u + nx * (0.8 + 2.2 * bulge), grip[1] + sa * u + ny * (0.8 + 2.2 * bulge)))
    bm = poly_mask(pts_o + pts_i[::-1])
    Lg.paint(n_plate(bm, 1.2, (-0.25, -0.3), 1.2), "g", 0, ao=0)
    edge = {ip(q) for q in pts_o}
    Lg.decal([q for q in edge if q in bm], ("g", 5))
    info["hit"] |= bm | shaft
    info["blade"] = (grip[0] + ca * (u1 - 3) + nx * 4, grip[1] + sa * (u1 - 3) + ny * 4)
    info["tip"] = b_
    return bm


def draw_jackal(p, fi, sw):
    Ls = {n: Layer(n) for n in JK_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    Pp, Cc, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(Cc, Pp)
    ln = math.hypot(*upv)
    F = basis(Pp, upv)
    shN, shF = F(3.2, -ln + 1.6), F(-3.4, -ln + 2.0)
    hipN, hipF = F(2.0, 0.6), F(-2.0, 0.6)
    # legs: long, lean, digitigrade feel; gold anklets
    kf = leg(R, Ls["NearLeg"], hipN, p["ff"], 10.6, 10.8, 2.3, 1.7, "h", bias=0, knee=p["kf"], flen=3.4, heel=1.6, boot_h=2.0, pref=(1, -0.1))
    kb = leg(R, Ls["FarLeg"], hipF, p["fb"], 10.6, 10.8, 2.3, 1.7, "h", bias=-2, knee=p["kb"], flen=3.4, heel=1.6, boot_h=2.0, pref=(1, -0.1))
    for nm, ft in (("NearLeg", p["ff"]), ("FarLeg", p["fb"])):
        Ls[nm].decal([q for q in Ls[nm].px if abs(q[1] - (ft[1] - 4)) < 0.6], ("g", 3))
    # torso: v-shaped, obsidian skin with a violet sheen, gold collar
    Bd = Ls["Body"]
    torso = [F(-4.0, -0.4), F(-5.6, -ln + 4.0), F(-5.8, -ln + 0.4), F(-2.0, -ln - 1.4), F(3.0, -ln - 1.4), F(6.2, -ln + 0.6),
             F(5.6, -ln + 4.4), F(3.8, -0.4)]
    tm = R.plate(Bd, torso, "h", bevel=2.6, tilt=(-0.2, -0.1), strength=1.3)
    Bd.decal([q for q in polyline([ip(T(F(0.4, -ln + 3.0))), ip(T(F(0.2, -2.0)))]) if q in tm], ("h", 1))   # sternum line
    cc = F(0.6, -ln + 0.8)
    for rr, mat in ((5.8, "g"), (4.4, "u"), (3.2, "g")):
        m = {q for q in mask_disc(T(cc), rr, rr * 0.62) if q[1] >= T(cc)[1] - 0.5}
        if mat == "g":
            Bd.paint(n_dome(T(cc), rr, rr * 0.62, flat=0.7, tilt=(-0.2, -0.3)), "g", 0, ao=0, clip=m)
        else:
            Bd.paint({q: (0, 0, 1) for q in m}, "u", 0, ao=0)
    info["torso"] = tm
    # kilt: white linen shendyt, gold belt, a front apron panel
    sway = sw * 0.3 - p["wind"] * 0.3
    ktm = R.plate(Ls["Kilt"], [F(-5.0, -2.2), F(5.2, -2.2), add(F(6.2, 8.4), (sway * 0.3, 0)), add(F(-5.6, 8.0), (sway, 0))], "s",
                  bevel=1.4, tilt=(-0.15, 0), strength=1.0, fold=lambda x, y: (0.6 * math.sin(x * 1.1), 0))
    Ls["Kilt"].decal([q for q in ktm if (q[0] + (q[1] // 2)) % 3 == 0], ("s", 3))
    apron = poly_mask([T(F(1.0, -1.0)), T(F(4.4, -1.0)), T(F(4.8, 7.6)), T(F(1.6, 7.6))])
    Ls["Kilt"].paint(n_plate(apron, 0.8, (0, 0)), "g", 0, ao=0, clip=ktm | apron)
    Ls["Kilt"].decal([q for q in apron if q[1] % 3 == 0], ("u", 2))
    belt = poly_mask([T(F(-5.2, -3.4)), T(F(5.4, -3.4)), T(F(5.4, -1.6)), T(F(-5.2, -1.6))])
    Ls["Kilt"].paint(n_plate(belt, 0.8, (0, -0.3)), "g", 0, ao=0)
    info["hit"] |= ktm
    # head: jackal profile -- long narrow snout, tall ears lined with gold, amber eye
    G = basis(Hd, p["hup"])
    Hl = Ls["Head"]
    Hl.paint(n_tube([T(F(0.8, -ln - 0.6)), T(G(-1.2, 3.4))], [2.3, 2.0]), "h", -1)
    skull = [G(-3.6, 2.6), G(-3.8, -1.6), G(-1.6, -3.4), G(1.8, -3.0), G(4.0, -1.4), G(9.6, 0.0), G(10.4, 1.2), G(9.4, 2.4),
             G(3.4, 3.6), G(-0.6, 4.0)]
    hm = R.plate(Hl, skull, "h", bevel=1.6, tilt=(-0.25, -0.3), strength=1.3)
    if p["jaw"] > 0.1:
        jw = poly_mask([T(G(3.0, 3.2)), T(G(9.0, 2.6)), T(G(8.6, 2.6 + 2.4 * p["jaw"])), T(G(3.0, 4.2 + p["jaw"]))])
        Hl.fixed({q: "n1" for q in jw})
    for (ex, bias) in ((-1.4, -1), (0.8, 0)):
        ear = [G(ex - 1.4, -2.2), G(ex + 0.2, -10.8), G(ex + 1.6, -2.2)]
        em = R.plate(Hl, ear, "h", bevel=0.9, tilt=(-0.2, -0.3), bias=bias)
        Hl.decal([q for q in em if abs(q[0] - T(G(ex + 0.2, -5.6))[0]) < 0.7 and q[1] > T(G(0, -9.4))[1]], ("g", 3 if bias >= 0 else 2))
    Hl.decal(polyline([ip(T(G(2.0, -0.6))), ip(T(G(5.8, 0.4)))]), ("g", 4))                     # kohl-gold eye line
    e = ip(T(G(3.0, -0.8)))
    if p["eye"]:
        FX.put([e], "a4" if p["eye"] == 2 else "a3")
    info["head"] = hm
    info["eye"] = T(G(3.0, -0.8))
    # far arm (second hand on the glaive, or free)
    arm(R, Ls["FarArm"], shF, p["hb"], 8.6, 8.4, 1.9, 1.6, "h", bias=-2, fist="h", fist_r=1.5, pref=(-1, 0.6))
    # glaive
    gl = Ls["Glaive_back"] if p["back"] else Ls["Glaive"]
    glaive(gl, FX, T(p["hf"]), R.A(p["gang"]), p["gu0"], p["gu1"], fi, info)
    # near arm with gold armband
    el = arm(R, Ls["NearArm"], shN, p["hf"], 8.6, 8.4, 2.1, 1.7, "h", bias=0, fist="h", fist_r=1.6, pref=(-1, 0.7))
    Ls["NearArm"].decal([q for q in Ls["NearArm"].px if abs(q[1] - (T(lerp(shN, el, 0.55))[1])) < 0.8 and
                         math.hypot(q[0] - T(lerp(shN, el, 0.55))[0], q[1] - T(lerp(shN, el, 0.55))[1]) < 3], ("g", 4))
    info["hand"] = T(p["hf"])
    if p["smear"]:
        for sm in p["smear"]:
            g0, a0, g1, a1 = sm
            info["hit"] |= swept(FX, T(g0), R.A(a0), T(g1), R.A(a1), p["gu1"] - 12, p["gu1"] + 2, hw=1.3, pal="khopesh", taper=0.6)
    if p["thrust"]:
        info["hit"] |= K.thrust_lines(FX, T(p["hf"]), R.A(p["gang"]), -6, p["gu1"], (-3, -1, 2), pal="khopesh", flash=p["gu1"] - 1)
    if p["dust"]:
        for k in range(10):
            q = (int(Pp[0] + (hash01(k, fi, 3) - 0.5) * 24), FLj - int(hash01(k, fi, 4) * 4))
            FX.put([q], ("z6", "z5", "z4")[k % 3])
    return Ls, info


def j_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        fr.append((190, JP(C=(28.4, 27.4 + b * 0.5), Hd=(31.4, 17.6 + b * 0.7), hf=(36.0, 40.0 + b * 0.3), hb=(22.0, 38.0 + b * 0.4))))
    return fr


def j_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        bob = 1.0 * abs(s)
        fr.append((110, JP(P=(27.0, 42.0 + bob), C=(28.8, 27.6 + bob), Hd=(32.0, 17.8 + bob), hup=(0.34, -1.0),
                           ff=(28.0 + 6 * c, FLj - max(0, s) * 2.6), fb=(26.0 - 6 * c, FLj - max(0, -s) * 2.6),
                           hf=(36.4 + 0.8 * c, 40.0 + bob), gang=-78 + 2 * c, hb=(22.0 - 1.4 * c, 38.0 + bob))))
    return fr


def j_guard():
    g = dict(P=(26.0, 43.0), C=(27.0, 29.0), Hd=(30.6, 19.4), hup=(0.3, -1.0), fb=(20.0, FLj), ff=(33.5, FLj),
             hf=(35.0, 32.0), gang=-100, gu0=-18, gu1=26, hb=(31.0, 36.0))
    return [(200, JP(**g)), (200, JP(**dict(g, C=(27.0, 29.4), Hd=(30.6, 19.8)), eye=2))]


def j_combo():
    wind = dict(P=(25.6, 42.6), C=(25.4, 28.4), Hd=(27.6, 18.6), hup=(0.0, -1.0), fb=(19.0, FLj), ff=(32.0, FLj))
    cut = dict(P=(29.0, 43.0), C=(33.0, 29.4), Hd=(37.0, 20.4), hup=(0.55, -1.0), fb=(20.0, FLj), ff=(39.0, FLj))
    back = dict(P=(28.0, 43.0), C=(30.4, 28.6), Hd=(34.0, 19.0), hup=(0.4, -1.0), fb=(21.0, FLj), ff=(37.0, FLj))
    return [
        (110, JP(**wind, hf=(30.0, 32.0), gang=-120, hb=(24.0, 34.0))),
        (160, JP(**wind, hf=(26.0, 27.0), gang=-150, gu1=30, hb=(21.0, 30.0), eye=2, jaw=0.4)),
        (170, JP(**wind, hf=(24.0, 26.0), gang=-160, gu1=30, hb=(20.0, 29.0), eye=2, jaw=0.6)),
        (60, JP(**cut, hf=(40.0, 34.0), gang=-40, hb=(34.0, 36.0), eye=2, jaw=0.8, smear=[((24.0, 26.0), -160, (40.0, 34.0), -40)])),
        (70, JP(**cut, hf=(41.0, 40.0), gang=20, hb=(34.0, 40.0), eye=2, jaw=0.5, smear=[((40.0, 34.0), -40, (41.0, 40.0), 20)])),
        (120, JP(**cut, hf=(39.0, 42.0), gang=40, hb=(33.0, 42.0), jaw=0.3)),
        (150, JP(**back, hf=(37.0, 44.0), gang=60, hb=(31.0, 43.0), eye=2)),
        (160, JP(**back, hf=(36.0, 46.0), gang=70, gu1=30, hb=(30.0, 44.0), eye=2, jaw=0.4)),
        (60, JP(**cut, hf=(42.0, 32.0), gang=-60, hb=(35.0, 34.0), eye=2, jaw=0.8, smear=[((36.0, 46.0), 70, (42.0, 32.0), -60)])),
        (70, JP(**cut, hf=(38.0, 24.0), gang=-110, hb=(32.0, 28.0), eye=2, jaw=0.5, smear=[((42.0, 32.0), -60, (38.0, 24.0), -110)])),
        (130, JP(**back, hf=(36.0, 30.0), gang=-100, hb=(28.0, 33.0))),
        (170, JP()),
    ]


def j_lunge():
    low = dict(P=(24.0, 44.4), C=(23.4, 31.0), Hd=(25.4, 21.6), hup=(0.1, -1.0), fb=(15.0, FLj), ff=(31.0, FLj))
    dash = dict(P=(31.0, 44.0), C=(37.0, 32.0), Hd=(42.4, 24.0), hup=(0.9, -1.0), fb=(18.0, FLj - 1), ff=(44.0, FLj))
    return [
        (120, JP(**low, hf=(28.0, 38.0), gang=-4, gu0=-20, gu1=24, hb=(22.0, 38.0))),
        (160, JP(**low, hf=(24.0, 38.0), gang=-2, gu0=-20, gu1=24, hb=(19.0, 38.0), eye=2)),
        (170, JP(**low, hf=(22.0, 38.4), gang=-2, gu0=-20, gu1=24, hb=(18.0, 38.4), eye=2, jaw=0.5)),
        (70, JP(**dash, hf=(46.0, 34.0), gang=-4, gu0=-24, gu1=18, hb=(38.0, 35.0), eye=2, jaw=0.8, thrust=True, dust=1)),
        (70, JP(**dash, hf=(48.0, 34.0), gang=-3, gu0=-24, gu1=16, hb=(40.0, 35.0), eye=2, jaw=0.8, thrust=True, dust=1)),
        (80, JP(**dash, hf=(47.0, 35.0), gang=-2, gu0=-24, gu1=16, hb=(39.0, 36.0), eye=2, jaw=0.4, dust=1)),
        (120, JP(P=(29.0, 43.0), C=(32.0, 29.0), Hd=(36.0, 19.6), hup=(0.5, -1.0), fb=(19.0, FLj), ff=(38.0, FLj), hf=(41.0, 36.0),
                 gang=-30, hb=(33.0, 38.0))),
        (140, JP(P=(28.0, 42.6), C=(29.6, 28.0), Hd=(32.8, 18.2), hup=(0.36, -1.0), hf=(38.0, 38.0), gang=-60)),
        (150, JP()),
    ]


def j_hurt():
    return [(90, JP(P=(25.6, 42.0), C=(24.4, 28.0), Hd=(24.8, 18.6), hup=(-0.4, -1.0), hf=(32.0, 38.0), gang=-60, hb=(19.0, 34.0), jaw=0.8)),
            (130, JP(P=(26.4, 42.0), C=(27.2, 27.6), Hd=(29.8, 17.8), hup=(0.1, -1.0)))]


def j_death():
    kneel = dict(P=(26.0, 50.0), C=(29.0, 37.0), Hd=(33.0, 29.0), hup=(0.7, -1.0), kf=(33.0, 54.0), ff=(31.0, FLj), kb=(22.0, 61.0),
                 fb=(14.0, FLj), hf=(38.0, 56.0), gang=10, gu0=-26, gu1=22, hb=(28.0, 52.0), eye=0)
    names = [n for n in JK_L if n != "FX"]
    pal = ("a3", "g4", "z5", "z4", "z3")
    return [
        (100, JP(P=(25.0, 42.0), C=(23.4, 28.0), Hd=(23.0, 18.6), hup=(-0.6, -1.0), hf=(32.0, 36.0), gang=-40, jaw=1.0, eye=2)),
        (160, JP(P=(26.0, 46.0), C=(28.0, 33.0), Hd=(31.4, 24.0), hup=(0.5, -1.0), kf=(32.0, 50.0), kb=(22.0, 55.0), hf=(37.0, 48.0),
                 gang=-20, jaw=0.6)),
        (200, JP(**kneel)),
        (240, JP(**dict(kneel, C=(29.6, 38.0), Hd=(34.4, 31.0), hup=(0.9, -1.0)))),
        (160, JP(**dict(kneel, C=(29.6, 38.0), Hd=(34.4, 31.0), hup=(0.9, -1.0)), post=collapse(names, 0.7, 0.2, seed=5, pal=pal, spread=0.3))),
        (160, JP(**dict(kneel, C=(29.6, 38.0), Hd=(34.4, 31.0), hup=(0.9, -1.0)), post=collapse(names, 0.42, 0.35, seed=5, pal=pal, spread=0.5))),
        (180, JP(**dict(kneel, C=(29.6, 38.0), Hd=(34.4, 31.0), hup=(0.9, -1.0)), post=collapse(names, 0.18, 0.45, seed=5, pal=pal, spread=0.8))),
        (600, JP(**dict(kneel, C=(29.6, 38.0), Hd=(34.4, 31.0), hup=(0.9, -1.0)), dust=1, post=collapse(names, 0.07, 0.5, seed=5, pal=pal, spread=1.0))),
    ]


def build_jackal():
    K.setup(64, 64)
    anims, infos = E3.render_anims("du_jackal", JK_L, draw_jackal,
                                   [("idle", j_idle), ("walk", j_walk), ("guard", j_guard), ("combo", j_combo), ("lunge", j_lunge),
                                    ("hurt", j_hurt), ("death", j_death)], sway_key="C", loops=("idle", "walk", "guard"))
    meta = {"native": 1, "frame": [64, 64], "anchor": [28, 64],
            "hurtbox": hurtbox(anims, ["Body", "Head", "Kilt"], inset=(2, 4, 2)),
            "attacks": {"combo": {"windows": [{"active": [3, 4], "hit": hit_rect(infos, "combo", [3, 4], x_min=30)},
                                              {"active": [8, 9], "hit": hit_rect(infos, "combo", [8, 9], x_min=30)}]},
                        "lunge": {"active": [3, 5], "hit": hit_rect(infos, "lunge", [3, 5], x_min=30)}},
            "telegraph": {"combo": {"frame": 1, "at": spawn_pt(infos["combo"][1]["blade"])},
                          "lunge": {"frame": 1, "at": spawn_pt(infos["lunge"][1]["tip"])}},
            "notes": "faces right; combo = overhead crescent cut (3-4) then a rising back-cut (8-9); lunge = low wind-up and a dashing "
                     "thrust (engine lunges it on 3-5); guard = glaive held across (the engine blocks frontal light blows)."}
    export("du_jackal", JK_L, anims, meta)
    return meta


# =========================================================================== 4. SAND-SOLDIER
SO_L = ["FarArm", "FarLeg", "Body", "NearLeg", "Head", "Blade", "NearArm", "FX"]
FLo = 39
SO_NEU = dict(P=(18.0, 26.0), C=(19.0, 17.0), Hd=(20.6, 10.2), hup=(0.2, -1.0), fb=(15.0, FLo), ff=(22.0, FLo), kb=None, kf=None,
              hf=(25.0, 24.0), hb=(14.0, 24.0), bang=-60, eye=1, smear=None, rot=0.0, piv=(18, 30), rise=1.0, stream=1.0, dust=0)
SOP = mk(SO_NEU)


def khopesh(L, grip, ang, info, mat="b"):
    """A sickle-sword: straight neck then a deep forward curve; the outer edge is the cutting edge."""
    ca, sa = dirv(ang)
    nx, ny = -sa, ca
    pts_o, pts_i = [], []
    for k in range(11):
        t = k / 10
        u = 2.0 + t * 10.0
        curl = (t ** 2) * 4.2
        w = 1.1 if t < 0.35 else 1.1 + (t - 0.35) * 2.2
        c = (grip[0] + ca * u - nx * curl, grip[1] + sa * u - ny * curl)
        pts_o.append((c[0] + nx * w, c[1] + ny * w))
        pts_i.append((c[0] - nx * 0.6, c[1] - ny * 0.6))
    m = poly_mask(pts_o + pts_i[::-1])
    L.paint(n_plate(m, 1.0, (-0.2, -0.3), 1.2), mat, 0, ao=0)
    L.decal([q for q in {ip(q) for q in pts_o} if q in m], (mat, 5))
    for q in polyline([ip(grip), ip((grip[0] - ca * 2.4, grip[1] - sa * 2.4))]):
        L.fixed({q: "n2"})
    info["hit"] |= m
    info["tip"] = pts_o[-1]
    return m


def draw_soldier(p, fi, sw):
    Ls = {n: Layer(n) for n in SO_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    T = R.T
    info = {"hit": set()}
    Pp, Cc, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(Cc, Pp)
    ln = math.hypot(*upv)
    F = basis(Pp, upv)
    shN, shF = F(2.4, -ln + 1.2), F(-2.4, -ln + 1.6)
    hipN, hipF = F(1.6, 0.6), F(-1.6, 0.6)
    leg(R, Ls["NearLeg"], hipN, p["ff"], 6.6, 6.8, 2.0, 1.6, "z", bias=0, knee=p["kf"], flen=2.6, heel=1.2, boot_h=1.8)
    leg(R, Ls["FarLeg"], hipF, p["fb"], 6.6, 6.8, 2.0, 1.6, "z", bias=-2, knee=p["kb"], flen=2.6, heel=1.2, boot_h=1.8)
    torso = [F(-2.8, 0.6), F(-3.8, -ln + 2.4), F(-2.8, -ln - 0.8), F(2.8, -ln - 0.8), F(4.2, -ln + 2.0), F(3.0, 0.6)]
    tm = R.plate(Ls["Body"], torso, "z", bevel=2.2, tilt=(-0.2, -0.1), strength=1.3)
    Ls["Body"].decal([q for q in tm if hash01(q[0], q[1] // 2, 3) < 0.1], ("z", 2))            # cracks in the packed sand
    Ls["Body"].decal(polyline([ip(T(F(-3.0, -2.0))), ip(T(F(3.4, -2.6)))]), ("b", 3))           # a bronze belt
    G = basis(Hd, p["hup"])
    Hl = Ls["Head"]
    helm = [G(-2.8, 2.2), G(-3.0, -1.8), G(-1.2, -3.4), G(1.8, -3.2), G(3.4, -1.2), G(3.4, 2.4)]
    hm = R.plate(Hl, helm, "z", bevel=1.4, tilt=(-0.2, -0.3), strength=1.2)
    lap = [G(-3.2, -1.0), G(-1.0, -1.4), G(-0.6, 5.6), G(-4.6, 6.4)]                         # a crude headcloth lappet
    lm = R.plate(Hl, lap, "z", bevel=1.0, tilt=(-0.1, 0), bias=-1)
    Hl.decal([q for q in lm if q[1] % 2 == 0], ("z", 2))
    hm = hm | lm
    slit = [ip(T(G(0.6, 0.2))), ip(T(G(3.4, 0.2)))]
    Hl.decal(polyline(slit), ("n", 0))
    if p["eye"]:
        e = ip(T(G(2.4, 0.2)))
        FX.put([e], "a4" if p["eye"] == 2 else "a3")
    info["head"] = hm
    arm(R, Ls["FarArm"], shF, p["hb"], 5.6, 5.6, 1.6, 1.4, "z", bias=-2, fist="z", fist_r=1.3, pref=(-1, 0.6))
    khopesh(Ls["Blade"], T(p["hf"]), R.A(p["bang"]), info)
    arm(R, Ls["NearArm"], shN, p["hf"], 5.6, 5.6, 1.8, 1.5, "z", bias=0, fist="z", fist_r=1.4, pref=(-1, 0.7))
    if p["smear"]:
        g0, a0, g1, a1 = p["smear"]
        info["hit"] |= swept(FX, T(g0), a0, T(g1), a1, 4, 13, hw=1.1, pal="sand", taper=0.5)
    # sand streaming off the body
    for k in range(int(6 * p["stream"])):
        a = hash01(k, 1, 9)
        q = ip((Pp[0] - 3 + a * 8 - ((fi * 1.7 + k * 2.3) % 5), Cc[1] + a * 10 + ((fi * 2 + k * 3) % 8)))
        FX.put([q], "z6" if k % 2 else "z5")
    # rising out of the sand: the whole figure sits lower and everything under the floor line is buried
    if p["rise"] < 1.0:
        dy = int(round((1 - p["rise"]) * 36))
        for L in Ls.values():
            if isinstance(L, Layer):
                L.px = {(q[0], q[1] + dy): e for q, e in L.px.items() if q[1] + dy < FLo - 1}
        FX.px = {(q[0], q[1] + dy): c for q, c in FX.px.items() if q[1] + dy < FLo - 1}
        for x in range(6, 32):
            h = 2 + int(3 * (1 - abs(x - 19) / 13))
            for y in range(FLo - h, FLo + 1):
                FX.put([(x, y)], "z6" if y == FLo - h else "z5")
    if p["dust"]:
        for k in range(10):
            FX.put([(int(18 + (hash01(k, fi, 3) - 0.5) * 20), FLo - int(hash01(k, fi, 4) * 3))], ("z6", "z5", "z4")[k % 3])
    return Ls, info


def o_rise():
    return [(110, SOP(rise=r, eye=1 if r > 0.5 else 0, hf=(24.0, 22.0 + (1 - r) * 4), bang=-20 - r * 40, stream=2.0)) for r in (0.15, 0.35, 0.55, 0.75, 0.92, 1.0)]


def o_idle():
    return [(180, SOP(C=(19.0, 17.0 + b), Hd=(20.6, 10.2 + b * 1.2), hf=(25.0, 24.0 + b * 0.5))) for b in (0.0, 0.5, 1.0, 0.5)]


def o_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        bob = 0.8 * abs(s)
        fr.append((120, SOP(P=(18.0, 26.0 + bob), C=(19.4, 17.2 + bob), Hd=(21.0, 10.4 + bob), ff=(19.0 + 4 * c, FLo - max(0, s) * 2),
                            fb=(17.0 - 4 * c, FLo - max(0, -s) * 2), hf=(25.0 + c, 24.0 + bob), hb=(14.0 - c, 24.0 + bob))))
    return fr


def o_attack():
    up = dict(C=(18.0, 17.6), Hd=(19.4, 10.8), hup=(0.0, -1.0))
    cut = dict(P=(20.0, 26.4), C=(23.0, 18.4), Hd=(25.4, 11.6), hup=(0.6, -1.0), ff=(26.0, FLo), fb=(14.0, FLo))
    return [
        (120, SOP(**up, hf=(21.0, 14.0), bang=-110, hb=(15.0, 20.0))),
        (160, SOP(**up, hf=(18.0, 10.0), bang=-150, hb=(14.0, 18.0), eye=2)),
        (170, SOP(**up, hf=(17.0, 9.0), bang=-160, hb=(14.0, 18.0), eye=2)),
        (60, SOP(**cut, hf=(29.0, 20.0), bang=-10, hb=(19.0, 23.0), eye=2, smear=((17.0, 9.0), -160, (29.0, 20.0), -10))),
        (70, SOP(**cut, hf=(29.0, 26.0), bang=40, hb=(19.0, 25.0), eye=2, smear=((29.0, 20.0), -10, (29.0, 26.0), 40))),
        (130, SOP(**cut, hf=(28.0, 28.0), bang=60, hb=(19.0, 26.0))),
        (140, SOP(hf=(26.0, 25.0), bang=-20)),
        (150, SOP()),
    ]


def o_hurt():
    return [(90, SOP(C=(17.0, 17.4), Hd=(17.6, 10.8), hup=(-0.4, -1.0), hf=(23.0, 22.0), bang=-100)), (120, SOP())]


def o_death():
    names = [n for n in SO_L if n != "FX"]
    pal = ("z7", "z6", "z5", "z4", "z3")
    return [(100, SOP(C=(17.0, 17.4), Hd=(17.6, 10.8), hup=(-0.4, -1.0), eye=2)),
            (110, SOP(post=collapse(names, 0.72, 0.12, seed=7, pal=pal, spread=0.3), eye=0)),
            (120, SOP(post=collapse(names, 0.46, 0.25, seed=7, pal=pal, spread=0.6), eye=0)),
            (130, SOP(post=collapse(names, 0.25, 0.35, seed=7, pal=pal, spread=0.9), eye=0, dust=1)),
            (150, SOP(post=collapse(names, 0.12, 0.45, seed=7, pal=pal, spread=1.1), eye=0, dust=1)),
            (500, SOP(post=collapse(names, 0.06, 0.55, seed=7, pal=pal, spread=1.3), eye=0, dust=1))]


def build_soldier():
    K.setup(40, 40)
    anims, infos = E3.render_anims("du_soldier", SO_L, draw_soldier,
                                   [("rise", o_rise), ("idle", o_idle), ("walk", o_walk), ("attack", o_attack), ("hurt", o_hurt),
                                    ("death", o_death)], sway_key="C", loops=("idle", "walk"))
    meta = {"native": 1, "frame": [40, 40], "anchor": [18, 40],
            "hurtbox": hurtbox(anims[1:], ["Body", "Head"], inset=(1, 1, 1)),
            "attacks": {"attack": {"active": [3, 4], "hit": hit_rect(infos, "attack", [3, 4], x_min=20)}},
            "telegraph": {"attack": {"frame": 1, "at": spawn_pt(infos["attack"][1]["tip"])}},
            "notes": "the Pharaoh's summons; rise = forming out of the sand (no hurtbox until frame 2 in the engine)."}
    export("du_soldier", SO_L, anims, meta)
    return meta


def main():
    for name, fn in (("du_priest", build_priest), ("du_scarab", build_scarab), ("du_jackal", build_jackal), ("du_soldier", build_soldier)):
        if ONLY and name not in ONLY:
            continue
        m = fn()
        print(name, "hurtbox", m["hurtbox"], {t: (a.get("windows") or a) for t, a in m["attacks"].items()})


if __name__ == "__main__":
    main()
