#!/usr/bin/env python3
"""Necropolis enemies (agent N) -- same contract as ART_SPEC section 4 (face right, feet on the bottom row, meta).

    python3 art/gen_necro_enemies.py [--preview] [--only nv_noble,nv_ringer,nv_hound]

    nv_noble   48x48  hollow noble: a gaunt skeletal courtier in a faded violet coat, lace ruff, powdered queue, rapier
               idle(4) walk(6) thrust(8, active 4-5) flurry(10, active 3-4 + 6-7) parry(4) hurt(2) death(7)
    nv_ringer  48x48  bone-bell ringer: hunched hooded skeleton with a verdigris hand-bell on a haft
               idle(4) walk(6) ring(9, spawn frame 5) swing(8, active 4-5) hurt(2) death(7)
    nv_hound   48x32  skeletal hound: a lean ribcage on long legs, ghost-fire in the skull and along the spine
               idle(4) walk(6) lunge(8, active 3-5) bite(7, active 3-4) hurt(2) death(6)
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import necro_rig as NR  # noqa: E402
import necro_gen as NG  # noqa: E402
from necro_rig import P_  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc, poly_mask,  # noqa: E402
                       n_plate, n_dome, n_capsule)

# =========================================================================== 1. HOLLOW NOBLE
NOBLE = dict(s=0.92, leg=(7.0, 7.2, 1.5, 1.15), arm=(5.2, 5.0, 1.2, 1.0), shoulder=4.0, hip=2.8, torso="coat", skirt=8.0,
             skirt_rag=1.2, head="noble", weapon="rapier", ruff=True, trim="X", smear="steel",
             mats=dict(torso="H", skirt="H", leg="P", boot="K", arm="H", fore="H", hand="B", belt="X"))
N_IDLE = dict(P=(22, 34), C=(23.2, 22.2), Hd=(24.6, 14.2), hup=(0.12, -1), fb=(18, 47), ff=(28, 47), hb=(16, 26),
              hf=(30.5, 27.5), wang=-18)


def n_idle():
    fr = []
    for i in range(4):
        b = (0, 0.4, 0.8, 0.4)[i]
        fr.append((200, P_(**{**N_IDLE, "C": (23.2, 22.2 + b), "Hd": (24.6, 14.2 + b), "hf": (30.5, 27.5 + b * 0.5),
                              "hb": (16, 26 + b), "wang": -18 + b * 3})))
    return fr


def n_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.8 * abs(s_)
        fr.append((130, P_(**{**N_IDLE, "P": (22 + 0.4 * c, 34 + b * 0.4), "C": (23.6 + 0.4 * c, 22.2 + b),
                              "Hd": (25.0 + 0.4 * c, 14.2 + b), "fb": (20 - 4 * c, 47), "ff": (25 + 4 * c, 47),
                              "hf": (30.5 + 0.4 * c, 27.5 + b), "hb": (16, 26 + b), "wind": -1.0})))
    return fr


def n_thrust():
    back = dict(P=(20.5, 34.4), C=(20.4, 22.8), Hd=(21.4, 14.8), hup=(-0.05, -1), fb=(15, 47), ff=(27, 47), hb=(14, 21))
    lunge = dict(P=(27, 36), C=(30.5, 25.2), Hd=(33, 17.8), hup=(0.45, -1), fb=(15, 47), ff=(37, 47), hb=(16, 25))
    return [
        (140, P_(**back, hf=(26, 27.5), wang=-10)),
        (140, P_(**back, hf=(23, 27.0), wang=-4)),
        (260, P_(**back, hf=(21.5, 26.8), wang=-2, glint=1)),
        (60, P_(**lunge, hf=(40, 26.5), wang=-2, thrust=((34, 26.6), -2, 4, 18))),
        (80, P_(**lunge, hf=(41, 26.5), wang=-1, thrust=((35, 26.6), -1, 6, 20))),
        (130, P_(**lunge, hf=(39, 27.5), wang=4)),
        (140, P_(P=(24, 34.6), C=(26, 22.8), Hd=(27.4, 15), hup=(0.2, -1), fb=(17, 47), ff=(31, 47), hb=(16.5, 23),
                 hf=(33, 28.5), wang=-10)),
        (140, P_(**N_IDLE)),
    ]


def n_flurry():
    a = dict(P=(23, 34.4), C=(25, 22.8), Hd=(26.6, 15), hup=(0.25, -1), fb=(17, 47), ff=(31, 47), hb=(16, 22))
    return [
        (110, P_(**a, hf=(27, 26), wang=-40)),
        (110, P_(**a, hf=(25, 24), wang=-60)),
        (180, P_(**a, hf=(24.5, 23.5), wang=-64)),
        (60, P_(**a, hf=(37, 25.5), wang=-6, thrust=((31, 25.5), -6, 4, 18))),
        (80, P_(**a, hf=(38, 26), wang=-2, smear=[((31, 24), -40, (38, 26), -2, 6, 18)])),
        (90, P_(**a, hf=(29, 29), wang=10)),
        (60, P_(**a, hf=(38, 29.5), wang=8, thrust=((32, 29), 8, 4, 18))),
        (80, P_(**a, hf=(39, 30), wang=6)),
        (150, P_(**a, hf=(34, 29), wang=-6)),
        (150, P_(**N_IDLE)),
    ]


def n_parry():
    g = dict(P=(21.5, 34.6), C=(21.5, 22.8), Hd=(22.6, 15), hup=(-0.1, -1), fb=(15, 47), ff=(27, 47), hb=(15, 22))
    return [(60, P_(**g, hf=(28, 24), wang=-75, sparks=(30, 18, 8))), (90, P_(**g, hf=(28.5, 23), wang=-70)),
            (110, P_(**g, hf=(30, 25), wang=-35)), (120, P_(**N_IDLE))]


def n_hurt():
    return [(90, P_(P=(21, 34.6), C=(19.6, 23.2), Hd=(19.6, 15.4), hup=(-0.4, -1), fb=(16, 47), ff=(27, 47), hb=(14, 26),
                    hf=(27, 30), wang=5, eye=0)),
            (140, P_(**{**N_IDLE, "C": (22.2, 22.6), "Hd": (23.2, 14.8)}))]


def n_death():
    sn = NG.BODY
    kneel = dict(P=(23, 40), C=(25.5, 29), Hd=(28, 22), hup=(0.5, -1), fb=(17, 47), ff=(30, 47), kf=(30, 42), hb=(21, 38),
                 hf=(33, 40), wang=40, eye=0)
    return [
        (100, P_(P=(21, 34.6), C=(19.4, 23.4), Hd=(19, 15.8), hup=(-0.5, -1), fb=(16, 47), ff=(27, 47), hb=(13, 27),
                 hf=(27, 31), wang=20, eye=0.5)),
        (130, P_(P=(22, 37), C=(23, 26), Hd=(25, 19), hup=(0.3, -1), fb=(16, 47), ff=(29, 47), hb=(18, 33), hf=(31, 36),
                 wang=35, eye=0.3)),
        (220, P_(**kneel)),
        (120, P_(**kneel, post=NG.collapse(sn, 0.7, 0.15, spread=0.3))),
        (120, P_(**kneel, post=NG.collapse(sn, 0.45, 0.3, spread=0.4))),
        (140, P_(**kneel, post=NG.collapse(sn, 0.25, 0.5, spread=0.5))),
        (500, P_(**kneel, post=NG.collapse(sn, 0.12, 0.75, spread=0.6))),
    ]


def build_noble():
    K.setup(64, 48)
    anims, infos = NG.render(NOBLE, [("idle", n_idle()), ("walk", n_walk()), ("thrust", n_thrust()), ("flurry", n_flurry()),
                                     ("parry", n_parry()), ("hurt", n_hurt()), ("death", n_death())], 0.92, 20, 47)
    meta = {"native": 1, "frame": [64, 48], "anchor": [20, 48],
            "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(2, 1, 2)),
            "attacks": {"thrust": {"active": [3, 4], "hit": NG.hit_rect(infos, "thrust", [3, 4], x_min=24)},
                        "flurry": {"windows": [{"active": [3, 4], "hit": NG.hit_rect(infos, "flurry", [3, 4], x_min=22)},
                                               {"active": [6, 7], "hit": NG.hit_rect(infos, "flurry", [6, 7], x_min=22)}]}},
            "telegraph": {"thrust": {"frame": 2, "at": NG.pt(infos["thrust"][2]["tip"])},
                          "flurry": {"frame": 2, "at": NG.pt(infos["flurry"][2]["tip"])}},
            "notes": "hollow noble; parry = a guard flick (engine plays it on a parried hit, then a thrust)."}
    NG.export("nv_noble", anims, meta)
    NG.closeup("nv_noble", anims, [("idle", 0), ("thrust", 2), ("thrust", 4), ("flurry", 4), ("parry", 0), ("death", 3)])
    return meta


# =========================================================================== 2. BONE-BELL RINGER
RINGER = dict(s=0.9, head_s=0.78, leg=(6.4, 6.8, 1.3, 1.05), arm=(5.0, 5.4, 1.1, 0.95), shoulder=4.0, hip=3.2, torso="robe", skirt=10.5,
              skirt_rag=1.8, skirt_spread=1.3, head="hood", weapon="bell", smear="ghost",
              mats=dict(torso="M", skirt="M", leg="B", boot="B", arm="M", fore="B", hand="B", belt="W", hood="M"))
R_IDLE = dict(P=(22, 35), C=(25, 25), Hd=(29, 19.5), hup=(0.7, -1), fb=(19, 47), ff=(27, 47), hb=(21, 33), hf=(29, 32),
              wang=70)


def r_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 0.9, 0.5)[i]
        fr.append((220, P_(**{**R_IDLE, "C": (25, 25 + b), "Hd": (29, 19.5 + b), "hf": (29, 32 + b * 0.4), "wang": 70 + b * 4})))
    return fr


def r_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.7 * abs(s_)
        fr.append((150, P_(**{**R_IDLE, "P": (22 + 0.3 * c, 35 + b * 0.4), "C": (25.3 + 0.3 * c, 25 + b), "Hd": (29.3 + 0.3 * c, 19.5 + b),
                              "fb": (20 - 3 * c, 47), "ff": (24 + 3 * c, 47), "hf": (29 + 0.6 * c, 32 + b), "wang": 70 - 12 * c,
                              "wind": -1})))
    return fr


def r_ring():
    up_ = dict(P=(21, 35), C=(22.4, 24), Hd=(25, 17.5), hup=(0.3, -1), fb=(17, 47), ff=(27, 47), hb=(18, 30))
    return [
        (150, P_(**R_IDLE)),
        (150, P_(**up_, hf=(27, 24), wang=-30)),
        (150, P_(**up_, hf=(26, 16), wang=-80)),
        (260, P_(**up_, hf=(25, 13), wang=-95, glint=1)),
        (70, P_(**up_, hf=(28, 15), wang=-60, bell_ring=0.5)),
        (90, P_(**up_, hf=(27, 14), wang=-100, bell_ring=1.0, sparks=(30, 10, 10))),
        (120, P_(**up_, hf=(28, 15), wang=-65, bell_ring=1.5)),
        (160, P_(**up_, hf=(28, 22), wang=-10)),
        (160, P_(**R_IDLE)),
    ]


def r_swing():
    wind_ = dict(P=(21, 35), C=(21.6, 24.6), Hd=(24.6, 18.6), hup=(0.25, -1), fb=(16, 47), ff=(27, 47), hb=(18, 32))
    hit_ = dict(P=(24, 35.6), C=(28, 26), Hd=(32, 21), hup=(0.8, -1), fb=(17, 47), ff=(31, 47), hb=(22, 34))
    return [
        (140, P_(**wind_, hf=(22, 28), wang=150)),
        (140, P_(**wind_, hf=(19, 22), wang=-150)),
        (220, P_(**wind_, hf=(20, 18), wang=-120, glint=1)),
        (70, P_(**hit_, hf=(31, 23), wang=-30, smear=[((20, 18), -120, (31, 23), -30, 4, 12)])),
        (80, P_(**hit_, hf=(34, 33), wang=40, smear=[((31, 23), -30, (34, 33), 40, 4, 12)])),
        (130, P_(**hit_, hf=(33, 35), wang=70, dust=1)),
        (150, P_(**{**hit_, "C": (26, 25.5), "Hd": (30, 20)}, hf=(30, 34), wang=75)),
        (150, P_(**R_IDLE)),
    ]


def r_hurt():
    return [(90, P_(**{**R_IDLE, "C": (22.6, 25), "Hd": (25.6, 19), "hup": (0.3, -1), "eye": 0})),
            (140, P_(**{**R_IDLE, "C": (24.4, 25.2), "Hd": (28.4, 19.6)}))]


def r_death():
    sn = NG.BODY
    heap = dict(P=(23, 41), C=(26, 33), Hd=(30, 28), hup=(0.8, -1), fb=(17, 47), ff=(29, 47), kf=(29, 43), hb=(22, 42),
                hf=(34, 44), wang=10, eye=0)
    return [
        (100, P_(**{**R_IDLE, "C": (22, 25), "Hd": (24, 19), "hup": (0.1, -1), "eye": 0.5})),
        (130, P_(P=(22, 38), C=(24.5, 29), Hd=(28, 23.5), hup=(0.6, -1), fb=(17, 47), ff=(28, 47), hb=(21, 37), hf=(31, 40),
                 wang=40, eye=0.3)),
        (200, P_(**heap)),
        (120, P_(**heap, post=NG.collapse(sn, 0.7, 0.15, spread=0.3))),
        (120, P_(**heap, post=NG.collapse(sn, 0.45, 0.3, spread=0.4))),
        (140, P_(**heap, post=NG.collapse(sn, 0.25, 0.5, spread=0.5))),
        (500, P_(**heap, post=NG.collapse(sn, 0.12, 0.75, spread=0.6))),
    ]


def sink_head(frames, k=0.2):   # the small hood sits low between the shoulders
    return [(ms, {**p, "Hd": (p["Hd"][0] + (p["C"][0] - p["Hd"][0]) * k, p["Hd"][1] + (p["C"][1] - p["Hd"][1]) * k)}) for ms, p in frames]


def build_ringer():
    K.setup(48, 48)
    anims, infos = NG.render(RINGER, [("idle", sink_head(r_idle())), ("walk", sink_head(r_walk())), ("ring", sink_head(r_ring())),
                                      ("swing", sink_head(r_swing())), ("hurt", sink_head(r_hurt())), ("death", sink_head(r_death()))],
                             0.9, 18, 47)
    meta = {"native": 1, "frame": [48, 48], "anchor": [18, 48],
            "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(2, 1, 2)),
            "attacks": {"swing": {"active": [3, 4], "hit": NG.hit_rect(infos, "swing", [3, 4], x_min=21)}},
            "spawn": {"ring": {"frame": 5, "at": NG.pt(infos["ring"][5]["tip"])}},
            "telegraph": {"swing": {"frame": 2, "at": NG.pt(infos["swing"][2]["tip"])}},
            "notes": "ring: bell raised overhead and shaken -> the engine emits a stunning toll ring from spawn.at."}
    NG.export("nv_ringer", anims, meta)
    NG.closeup("nv_ringer", anims, [("idle", 0), ("ring", 5), ("swing", 2), ("swing", 4), ("death", 3)])
    return meta


# =========================================================================== 3. SKELETAL HOUND (quadruped, own draw)
HOUND_L = ["FXBack", "BackLegs", "Body", "FrontLegs", "Head", "FX"]


def draw_hound(p, fi, sw):
    Ls = {n: (FXLayer(n) if n.startswith("FX") else Layer(n)) for n in HOUND_L}
    FX = Ls["FX"]
    R = Rig(p.get("rot", 0.0), p.get("piv", (0, 0)))
    info = {"hit": set()}
    hip, sho = p["hip"], p["sho"]
    # spine: a chain of vertebra domes from the tail through the hips to the shoulders and neck
    tail = [add(hip, (-4, 1 + sw * 0.3)), add(hip, (-8, 3 + sw * 0.6)), add(hip, (-11, 6 + sw))]
    spine = [tail[2], tail[1], tail[0], hip, lerp(hip, sho, 0.33), lerp(hip, sho, 0.66), sho, p["neck"]]
    for i, q in enumerate(spine):
        r = 0.7 if i < 3 else 1.2 if i in (3, 6) else 1.0
        Ls["Body"].paint(n_dome(R.T(q), r, r * 0.9), "B", 0 if i >= 3 else -1, ao=0)
    # ribcage: curved ribs hanging from the spine
    for k in range(5):
        t = 0.28 + k * 0.14
        top = lerp(hip, sho, t)
        dep = 5.2 - abs(k - 2.6) * 0.8
        a = add(top, (0.5, 0.8))
        b = add(top, (1.8 - k * 0.3, dep))
        c = add(top, (0.2, dep + 0.8))
        for q in polyline([R.T(a), R.T(b), R.T(c)]):
            Ls["Body"].fixed({q: "B4" if k % 2 == 0 else "B2"})
    # pelvis + scapula plates
    Ls["Body"].paint(n_plate(R.mask([add(hip, (-3, -1)), add(hip, (2, -1.6)), add(hip, (2.6, 2)), add(hip, (-2, 2.4))]), 1.0), "B", 0)
    Ls["Body"].paint(n_plate(R.mask([add(sho, (-2.6, -1.4)), add(sho, (2, -1.2)), add(sho, (1.4, 3.6)), add(sho, (-1.8, 3))]), 1.0), "B", 1)
    # legs: thin bones, digitigrade
    for (base, feet, lay, bias) in ((hip, (p["bl"], p["bl2"]), "BackLegs", -1), (sho, (p["fl"], p["fl2"]), "FrontLegs", 0)):
        for j, foot in enumerate(feet):
            L = Ls["BackLegs"] if j == 0 else Ls[lay]
            b = add(base, (0.6 if j else -0.4, 1.4))
            if lay == "BackLegs":
                kn = add(b, (2.2, 3.6))
                hock = (foot[0] - 1.8, foot[1] - 3.4)
                pts = [b, kn, hock, foot]
            else:
                el = ik(b, foot, 4.6, 4.8, (-1, 0))
                pts = [b, el, foot]
            for a_, c_ in zip(pts, pts[1:]):
                L.paint(n_capsule(R.T(a_), R.T(c_), 0.65, 0.5), "B", bias - (1 if j == 0 else 0))
            L.fixed({ip(R.T((foot[0] + 1, foot[1]))): "B3", ip(R.T((foot[0] + 2, foot[1]))): "B2"})
    # head: long narrow skull, open jaw on bites, ghost-fire eye
    H = Ls["Head"]
    n, d, jaw = p["neck"], p["hdir"], p["jaw"]
    nx, ny = d
    L_ = 7.6
    side = (-ny, nx)
    tip = add(n, (nx * L_, ny * L_))
    top = [add(n, (-side[0] * 1.8 - nx, -side[1] * 1.8 - ny)), add(n, (nx * 2.6 - side[0] * 2.3, ny * 2.6 - side[1] * 2.3)),
           add(tip, (-side[0] * 0.6, -side[1] * 0.6)), tip, add(n, (nx * 3.6 + side[0] * 0.6, ny * 3.6 + side[1] * 0.6)),
           add(n, (side[0] * 1.2, side[1] * 1.2))]
    H.paint(n_plate(R.mask(top), 1.2, (-0.2, -0.3)), "B", 1)
    ja = math.radians(jaw)
    jd = (nx * math.cos(ja) - ny * math.sin(ja), nx * math.sin(ja) + ny * math.cos(ja))
    j0 = add(n, (side[0] * 1.2, side[1] * 1.2))
    jt = add(j0, (jd[0] * 6.2, jd[1] * 6.2))
    H.paint(n_capsule(R.T(j0), R.T(jt), 1.1, 0.5), "B", -1)
    for k in range(3):               # teeth
        q = lerp(add(n, (nx * 4, ny * 4)), tip, k / 3)
        H.fixed({ip(R.T(add(q, (side[0] * 0.9, side[1] * 0.9)))): "B5"})
    e = R.T(add(n, (nx * 3.2 - side[0] * 1.0, ny * 3.2 - side[1] * 1.0)))
    H.fixed({ip(e): "U5", (ip(e)[0] + 1, ip(e)[1]): "U4"})
    info["mouth"] = R.T(tip)
    info["hit"] |= set(K.mask_disc(R.T(tip), 3.5, 3.5)) if p.get("snap") else set()
    # ghost-fire along the spine
    for k in range(4):
        q = R.T(lerp(hip, sho, 0.15 + k * 0.25))
        t = (fi * 0.37 + k * 0.29) % 1
        FX.put([ip((q[0] - sw * 0.5, q[1] - 2 - t * 3))], "U4" if t < 0.4 else "U3")
        if t < 0.3:
            FX.put([ip((q[0], q[1] - 1.5))], "U5")
    FX.put([ip((e[0] - 1, e[1] - 1))], "U4")
    if p.get("streak"):
        for k in range(4):
            y = int(sho[1] + k * 2 - 2)
            for x in range(int(hip[0] - 14), int(hip[0] - 4)):
                if (x + k) % 3:
                    FX.put([(x, y)], "U2" if x < hip[0] - 10 else "U3")
    return Ls, info


H_N = dict(hip=(16, 22), sho=(28, 21), neck=(32, 17.5), hdir=(0.92, 0.36), jaw=12, bl=(13, 31), bl2=(18, 31),
           fl=(28, 31), fl2=(32, 31))


def hp(**kw):
    d = dict(H_N)
    d.update(kw)
    return d


def h_idle():
    return [(200, hp(hip=(16, 22 + b), sho=(28, 21 + b * 0.8), neck=(32, 17.5 + b), jaw=12 + b * 3)) for b in (0, 0.5, 1, 0.5)]


def h_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.8 * abs(s_)
        fr.append((90, hp(hip=(16, 22 + b), sho=(28, 21 + b), neck=(32.5, 17.5 + b), bl=(13 + 3 * c, 31), bl2=(18 - 3 * c, 31),
                          fl=(28 - 3 * c, 31), fl2=(32 + 3 * c, 31), wind=-1)))
    return fr


def h_lunge():
    crouch = dict(hip=(15, 24), sho=(26, 24), neck=(30, 21), hdir=(0.96, 0.25))
    return [
        (140, hp(**crouch, bl=(12, 31), bl2=(17, 31), fl=(27, 31), fl2=(31, 31))),
        (240, hp(**crouch, bl=(11, 31), bl2=(16, 31), fl=(27, 31), fl2=(31, 31), jaw=30)),
        (80, hp(hip=(18, 18), sho=(30, 16), neck=(35, 13), hdir=(0.95, 0.3), bl=(9, 25), bl2=(13, 28), fl=(36, 22), fl2=(39, 24),
                jaw=45, streak=1)),
        (80, hp(hip=(21, 17), sho=(33, 15.5), neck=(38, 13), hdir=(0.96, 0.28), bl=(12, 24), bl2=(15, 27), fl=(39, 22), fl2=(42, 23),
                jaw=40, snap=1, streak=1)),
        (90, hp(hip=(22, 20), sho=(34, 18.5), neck=(39, 15.5), hdir=(0.95, 0.3), bl=(16, 29), bl2=(19, 30), fl=(37, 31), fl2=(41, 31),
                jaw=6, snap=1)),
        (90, hp(hip=(22, 22), sho=(34, 21), neck=(38.5, 17.5), bl=(18, 31), bl2=(22, 31), fl=(34, 31), fl2=(38, 31), jaw=6, snap=1)),
        (140, hp(hip=(20, 22), sho=(32, 21), neck=(36.5, 17.5), bl=(17, 31), bl2=(21, 31), fl=(32, 31), fl2=(36, 31))),
        (140, hp()),
    ]


def h_bite():
    return [
        (140, hp(neck=(31, 17), hdir=(0.8, 0.6), jaw=10)),
        (140, hp(sho=(27, 21.5), neck=(30, 16), hdir=(0.85, -0.2), jaw=40)),
        (220, hp(sho=(26.5, 21.5), neck=(29, 15), hdir=(0.8, -0.35), jaw=50)),
        (70, hp(sho=(30, 21), neck=(35, 18), hdir=(0.95, 0.3), jaw=4, snap=1)),
        (90, hp(sho=(30, 21), neck=(35.5, 18.5), hdir=(0.95, 0.3), jaw=2, snap=1)),
        (140, hp(sho=(29, 21), neck=(33.5, 18), jaw=8)),
        (140, hp()),
    ]


def h_hurt():
    return [(90, hp(hip=(15, 21), sho=(26, 20), neck=(28.5, 15.5), hdir=(0.7, -0.6), jaw=25)), (140, hp())]


def h_death():
    down = dict(hip=(16, 27), sho=(28, 27), neck=(33, 26), hdir=(0.95, 0.2), bl=(10, 31), bl2=(20, 31), fl=(24, 31), fl2=(36, 31), jaw=30)
    sn = ["BackLegs", "Body", "FrontLegs", "Head"]
    return [
        (100, hp(hip=(15, 21), sho=(26, 21), neck=(29, 16), hdir=(0.7, -0.6), jaw=30)),
        (140, hp(hip=(16, 25), sho=(28, 25), neck=(32, 23), hdir=(0.95, 0.1), bl=(11, 31), bl2=(19, 31), fl=(26, 31), fl2=(35, 31))),
        (200, hp(**down)),
        (140, hp(**down, post=NG.collapse(sn, 0.6, 0.25, spread=0.2))),
        (140, hp(**down, post=NG.collapse(sn, 0.3, 0.5, spread=0.3))),
        (400, hp(**down, post=NG.collapse(sn, 0.15, 0.8, spread=0.4))),
    ]


def build_hound():
    K.setup(48, 32)
    out, infos = [], {}
    for tag, fn in [("idle", h_idle), ("walk", h_walk), ("lunge", h_lunge), ("bite", h_bite), ("hurt", h_hurt), ("death", h_death)]:
        fr = fn()
        sway = K.spring([f[1]["sho"][0] for f in fr], loop=tag in ("idle", "walk"), extra=[f[1].get("wind", 0) for f in fr])
        lst, inf = [], []
        for k, (ms, p) in enumerate(fr):
            Ls, info = draw_hound(p, k, sway[k])
            imgs = {n: (K.render_layer(v) if isinstance(v, Layer) else v.image()) for n, v in Ls.items()}
            if p.get("post"):
                imgs = p["post"](imgs)
            lst.append((ms, imgs))
            inf.append(info)
        out.append((tag, lst))
        infos[tag] = inf

    def hr(tag, ks):
        pts = set()
        for k in ks:
            pts |= infos[tag][k]["hit"]
        r = K.bbox(pts, 1)
        r[3] = K.H - r[1]
        return r
    imgs0 = out[0][1][0][1]
    x0, y0, x1, y1 = K.opaque_bbox(imgs0, ["Body", "Head"])
    meta = {"native": 1, "frame": [48, 32], "anchor": [22, 32], "hurtbox": [x0 + 3, y0 + 1, x1 - x0 - 6, 32 - y0 - 1],
            "attacks": {"lunge": {"active": [3, 5], "hit": hr("lunge", [3, 4, 5])}, "bite": {"active": [3, 4], "hit": hr("bite", [3, 4])}},
            "telegraph": {"lunge": {"frame": 1, "at": NG.pt(infos["lunge"][1]["mouth"])}},
            "notes": "skeletal hound; the lunge leaps (engine lunge velocity), the bite is a short snap."}
    K.export("nv_hound", HOUND_L, out, meta, build=NG.BUILD)
    return meta


if __name__ == "__main__":
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    for name, fn in [("nv_noble", build_noble), ("nv_ringer", build_ringer), ("nv_hound", build_hound)]:
        if NG.ONLY and name not in NG.ONLY:
            continue
        m = fn()
        print(name, "ok", m.get("hurtbox"), {k: v.get("active", [w["active"] for w in v.get("windows", [])]) for k, v in m["attacks"].items()})
