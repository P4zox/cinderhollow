#!/usr/bin/env python3
"""SUPERSEDED for Vael (see art/gen_necro_vael2.py) -- still builds his spectral court.  Original notes:
King Vael, the Hollow Crown (agent N) + his spectral court. Built from the user's reference art/concepts/ref_king_vael.png:
an undead king in corroded gold-and-bone armour, a spiked crown fused to a skull with pale-blue ghost-fire eyes, a tattered
purple cape, a massive bone greatsword, spectral chains on his wrists.

    python3 art/gen_necro_vael.py [--preview] [--only vael,vael_b,vael_p3,vael_b_p3,vael_knight,vael_priest,vael_exec]

    vael       176x112  idle(6) walk(8) combo(14; windows 3-4, 7-8, 11-12) overhead(12; 7-8) thrust(10; 3-4)
                        chain(11; spawn 5) stagger(4) death(14)
    vael_b     176x112  ghostfire(11; spawn 6) summon(12; spawn 8) absorb(14) leap(12; 9-10) sweep(10; 5-6) rise(8)
    vael_p3 / vael_b_p3  the same frames, phase 3: the crown blazes, the armour cracks with ghost-fire, brighter chains
    vael_knight 80x64   spectral knight: idle(4) walk(6) slash(9; 4-5) bash(8; 4-5) hurt(2) death(7) appear(8)
    vael_priest 80x64   spectral priest: idle(4) walk(6) cast(10; spawn 6) ward(10; spawn 6) hurt(2) death(7) appear(8)
    vael_exec   96x80   spectral executioner: idle(6) walk(8) chop(11; 5-6) sweep(10; 4-6) hurt(2) death(8) appear(8)
Faces right, feet on the bottom row. Anchors: Vael x 72; court x 32 / 32 / 38.
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import necro_rig as NR  # noqa: E402
import necro_gen as NG  # noqa: E402
from necro_rig import P_  # noqa: E402
from enemy_kit import hash01  # noqa: E402

S = 2.1
VAEL = dict(s=S, head_s=0.74, leg=(7.0, 7.4, 1.95, 1.55), arm=(5.4, 5.2, 1.6, 1.35), shoulder=5.6, emblem="skull", hip=3.3, torso="plate",
            skirt=8.0, skirt_rag=1.5, skirt_spread=1.1, head="crown", weapon="greatsword", blade=30, two_hand=False,
            cape=True, cape_len=14, cape_w=13, cape_rag=5.0, pauldron=True, pauldron_spikes=False, belt_skull=True,
            vambrace="X", kneecop="X", chains=True, smear="ghost", eye_cols=("U5", "U4"),
            mats=dict(torso="X", skirt="H", leg="X", boot="X", arm="X", fore="X", hand="X", belt="B", cape="H", pauldron="X"))
IDLE = dict(P=(24, 33.4), C=(25, 21.2), Hd=(26.4, 13.6), hup=(0.12, -1), fb=(18, 47), ff=(30, 47), hf=(31, 30), hb=(19.5, 31),
            wang=38)


def corrode(p3=False):
    """Verdigris blotches on the gold; in phase 3 ghost-fire cracks open in the plate."""
    X = [K.RGBA[k] for k in K.RAMP["X"]]
    N = [K.RGBA[k] for k in K.RAMP["N"]]
    U = [K.RGBA[k] for k in K.RAMP["U"]]
    xs = {c: i for i, c in enumerate(X)}

    def f(imgs, tag, k):
        out = dict(imgs)
        for n in ("Body", "FrontArm", "BackArm", "FrontLeg", "BackLeg", "Head"):
            if n not in imgs:
                continue
            im = imgs[n].copy()
            px = im.load()
            w, h = im.size
            for y in range(h):
                for x in range(w):
                    c = px[x, y]
                    if c[3] == 0 or c not in xs:
                        continue
                    i = xs[c]
                    b = hash01(x // 3, y // 3, 71) * 0.6 + hash01(x, y, 72) * 0.4
                    if b < 0.2 and n != "Head":
                        px[x, y] = N[min(4, max(0, i - 1))]
                    if p3 and n in ("Body", "FrontArm", "BackArm") and hash01(x // 2, y, 73) < 0.05 and i <= 2:
                        px[x, y] = U[3 if hash01(x, y, 74) < 0.5 else 2]
            out[n] = im
        return out
    return f


def V(**kw):
    d = dict(IDLE)
    d.update(kw)
    return P_(**d)


def idle():
    fr = []
    for i in range(6):
        b = (0, 0.25, 0.5, 0.7, 0.5, 0.25)[i]
        fr.append((200, V(C=(25, 21.2 + b), Hd=(26.4, 13.6 + b), hf=(31, 30 + b * 0.4), hb=(19.5, 31 + b), wang=38 - b * 2)))
    return fr


def walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.8 * abs(s_)
        fr.append((150, V(P=(24 + 0.3 * c, 33.4 + b * 0.4), C=(25.4 + 0.4 * c, 21.2 + b), Hd=(26.8 + 0.4 * c, 13.6 + b),
                          fb=(21 - 4 * c, 47), ff=(27 + 4 * c, 47), hf=(31 + 0.6 * c, 30 + b), hb=(19.5 - 1.5 * c, 31 + b),
                          wang=36, wind=-1)))
    return fr


def combo():
    back = dict(P=(23, 33.6), C=(22.8, 21.6), Hd=(24, 14.2), hup=(-0.05, -1), fb=(16, 47), ff=(30, 47))
    fwd = dict(P=(26, 34.4), C=(29, 22.8), Hd=(31.4, 15.6), hup=(0.5, -1), fb=(16, 47), ff=(34, 47))
    low = dict(P=(25, 34.8), C=(27.4, 23.4), Hd=(29.4, 16.4), hup=(0.35, -1), fb=(17, 47), ff=(33, 47))
    return [
        (120, V()),
        (130, V(**back, hf=(24, 18), hb=(19, 27), wang=-150)),
        (230, V(**back, hf=(22.5, 16.5), hb=(18.5, 26), wang=-158, glint=1)),
        (60, V(**fwd, hf=(33, 26), hb=(22, 30), wang=18, smear=[((22.5, 16.5), -158, (33, 26), 18, 8, 30)])),
        (80, V(**fwd, hf=(34, 30), hb=(22, 31), wang=48, smear=[((33, 26), 18, (34, 30), 48, 8, 30)])),
        (120, V(**low, hf=(30, 33), hb=(21, 31), wang=120)),
        (160, V(**low, hf=(28.5, 34), hb=(21, 31), wang=135, glint=1)),
        (60, V(**fwd, hf=(33, 21), hb=(22, 29), wang=-45, smear=[((28.5, 34), 135, (33, 21), -45, 8, 30)])),
        (80, V(**fwd, hf=(31, 15), hb=(22, 28), wang=-95, smear=[((33, 21), -45, (31, 15), -95, 8, 30)])),
        (130, V(**back, hf=(21, 14), hb=(18, 25), wang=-170)),
        (280, V(**back, hf=(20, 13.5), hb=(17.5, 24.5), wang=-175, glint=1, fire=0.6)),
        (60, V(**fwd, hf=(33, 24), hb=(24, 28), wang=0, smear=[((20, 13.5), -175, (33, 24), 0, 6, 31)])),
        (90, V(**fwd, hf=(35, 31), hb=(25, 30), wang=42, smear=[((33, 24), 0, (35, 31), 42, 6, 31)], dust=2)),
        (240, V(**{**fwd, "C": (27.5, 22.2), "Hd": (29.6, 14.8)}, hf=(33, 31), hb=(22, 31), wang=45)),
    ]


def overhead():
    up_ = dict(P=(23.4, 34), C=(23.4, 21.6), Hd=(24.6, 14.2), hup=(-0.1, -1), fb=(16, 47), ff=(30, 47))
    down = dict(P=(26.5, 35.6), C=(30, 24.6), Hd=(32.5, 17.6), hup=(0.6, -1), fb=(15, 47), ff=(34, 47))
    return [
        (120, V()),
        (130, V(**up_, hf=(27, 22), hb=(24, 24), wang=-80)),
        (130, V(**up_, hf=(25.5, 13), hb=(23.5, 15), wang=-92)),
        (130, V(**up_, hf=(24.5, 9), hb=(23, 11), wang=-100, fire=0.5)),
        (220, V(**up_, hf=(24, 8), hb=(22.6, 10), wang=-104, glint=1, fire=1.0)),
        (220, V(**up_, hf=(23.6, 7.6), hb=(22.4, 9.6), wang=-106, fire=1.2)),
        (60, V(**down, hf=(30, 13), hb=(27, 15), wang=-50, smear=[((24, 8), -104, (30, 13), -50, 8, 31)])),
        (60, V(**down, hf=(34, 26), hb=(30, 26), wang=20, smear=[((30, 13), -50, (34, 26), 20, 8, 31)])),
        (90, V(**down, hf=(35, 31), hb=(31, 31), wang=42, smear=[((34, 26), 20, (35, 31), 42, 8, 31)], dust=3)),
        (300, V(**down, hf=(35, 32), hb=(31, 32), wang=46, dust=1)),
        (200, V(**{**down, "C": (28, 23.4), "Hd": (30.4, 16.2)}, hf=(33, 31), hb=(26, 31), wang=44)),
        (180, V()),
    ]


def thrust():
    back = dict(P=(22.5, 34), C=(21.6, 22), Hd=(22.6, 14.6), hup=(-0.1, -1), fb=(15, 47), ff=(29, 47), hb=(16, 25))
    lung = dict(P=(28, 35.4), C=(32, 24.4), Hd=(34.8, 17.4), hup=(0.55, -1), fb=(15, 47), ff=(38, 47), hb=(19, 26))
    return [
        (120, V()),
        (140, V(**back, hf=(24, 27), wang=-4)),
        (260, V(**back, hf=(21.5, 26.6), wang=-2, glint=1)),
        (60, V(**lung, hf=(40, 26), wang=0, thrust=((34, 26), 0, 10, 36))),
        (90, V(**lung, hf=(41, 26), wang=1, thrust=((35, 26), 1, 12, 37))),
        (160, V(**lung, hf=(39, 27), wang=6)),
        (140, V(**{**lung, "C": (30, 23.4), "Hd": (32.5, 16.2)}, hf=(36, 29), wang=20)),
        (140, V(P=(25, 34), C=(26.4, 22), Hd=(28, 14.4), hup=(0.2, -1), fb=(17, 47), ff=(31, 47), hf=(32, 30), hb=(20, 30), wang=32)),
        (140, V()),
        (120, V()),
    ]


def chain():
    """Chain lash: the back wrist's spectral chain whipped forward (the engine draws the long lash from spawn 5)."""
    r = dict(P=(23.5, 33.8), C=(23.4, 21.6), Hd=(24.6, 14), hup=(0, -1), fb=(16, 47), ff=(30, 47), hf=(29, 31), wang=50)
    t = dict(P=(26, 34.4), C=(28.4, 22.4), Hd=(30.6, 15.2), hup=(0.45, -1), fb=(16, 47), ff=(33, 47), hf=(30, 32), wang=58)
    return [
        (120, V()),
        (140, V(**r, hb=(21, 20), chain=[(18, 16), (14, 20), (12, 27)])),
        (140, V(**r, hb=(20, 14), chain=[(16, 10), (11, 12), (8, 18)])),
        (260, V(**r, hb=(19.5, 12.5), chain=[(15, 8), (10, 10), (6, 15)], glint=1)),
        (60, V(**t, hb=(33, 20), chain=[(40, 19), (47, 20)])),
        (90, V(**t, hb=(36, 22), chain=[(44, 22), (50, 23)])),
        (200, V(**t, hb=(35, 23), chain=[(43, 24), (50, 25)])),
        (130, V(**t, hb=(31, 26), chain=[(37, 31), (42, 35)])),
        (130, V(**{**t, "C": (27, 22), "Hd": (29, 14.6)}, hb=(26, 29))),
        (140, V()),
        (120, V()),
    ]


def stagger():
    st = dict(P=(22.4, 36.6), C=(21.4, 25.4), Hd=(21.6, 18.4), hup=(-0.3, -1), fb=(15, 47), ff=(29, 47), kf=(30, 41), hb=(18, 36),
              hf=(30, 40), wang=62, eye=0.4)
    return [(90, V(**st)), (160, V(**{**st, "C": (22, 26.2), "Hd": (22.6, 19.4)})), (500, V(**{**st, "C": (22.2, 26.6), "Hd": (23, 19.8)})),
            (200, V(**{**st, "C": (23, 25), "Hd": (24, 18)}))]


def death():
    sn = NG.BODY
    kneel = dict(P=(23, 40), C=(24.6, 28.6), Hd=(26.6, 22), hup=(0.3, -1), fb=(15, 47), ff=(30, 47), kf=(31, 43), hb=(22, 38),
                 hf=(31, 33), wang=88, eye=0.6)
    bow = dict(kneel, C=(26, 30), Hd=(29.4, 25.4), hup=(0.8, -1), eye=0.2)
    return [
        (120, V(P=(22.6, 35), C=(21.6, 23.4), Hd=(21.8, 16.4), hup=(-0.4, -1), fb=(15, 47), ff=(29, 47), hb=(16, 30), hf=(29, 34),
                wang=60, eye=1)),
        (160, V(P=(23, 38), C=(24, 27), Hd=(25.6, 20.4), hup=(0.2, -1), fb=(15, 47), ff=(30, 47), hb=(20, 34), hf=(31, 34),
                wang=80, eye=0.8)),
        (260, V(**kneel)),
        (300, V(**kneel)),
        (260, V(**bow)),
        (400, V(**bow, crown=0.8)),
        (140, V(**bow, crown=0.6, post=NG.collapse(sn, 0.92, 0.08, spread=0.1))),
        (140, V(**bow, crown=0.4, post=NG.collapse(sn, 0.8, 0.18, spread=0.2))),
        (140, V(**bow, post=NG.collapse(sn, 0.66, 0.3, spread=0.25))),
        (140, V(**bow, post=NG.collapse(sn, 0.5, 0.45, spread=0.3))),
        (140, V(**bow, post=NG.collapse(sn, 0.36, 0.6, spread=0.4))),
        (160, V(**bow, post=NG.collapse(sn, 0.22, 0.75, spread=0.5))),
        (180, V(**bow, post=NG.collapse(sn, 0.12, 0.88, spread=0.6))),
        (700, V(**bow, post=NG.collapse(sn, 0.06, 0.97, spread=0.7))),
    ]


# ---------------------------------------------------------------- sheet b
def ghostfire():
    c = dict(P=(23.6, 34), C=(24.2, 21.6), Hd=(25.8, 14.2), hup=(0.1, -1), fb=(17, 47), ff=(30, 47), hf=(29, 32), wang=55, fire_hand="b")
    return [
        (120, V()),
        (130, V(**c, hb=(24, 27))),
        (130, V(**c, hb=(30, 22), fire=0.3)),
        (160, V(**c, hb=(33, 19), fire=0.6)),
        (160, V(**c, hb=(34, 18), fire=1.0, glint=1)),
        (160, V(**c, hb=(34.5, 17.6), fire=1.4)),
        (90, V(**{**c, "C": (26, 22), "Hd": (28, 14.8)}, hb=(38, 21), fire=1.8, sparks=(40, 20, 14))),
        (120, V(**{**c, "C": (26, 22), "Hd": (28, 14.8)}, hb=(38, 22), fire=0.9)),
        (140, V(**c, hb=(33, 25), fire=0.3)),
        (140, V(**c, hb=(26, 29))),
        (120, V()),
    ]


def summon():
    a = dict(P=(24, 34), C=(24.4, 21.4), Hd=(25.2, 13.8), hup=(-0.1, -1), fb=(17, 47), ff=(31, 47))
    return [
        (120, V()),
        (140, V(**a, hf=(28, 24), hb=(21, 28), wang=-60)),
        (140, V(**a, hf=(26.5, 14), hb=(22, 24), wang=-86)),
        (160, V(**a, hf=(26, 9), hb=(21, 22), wang=-90, fire=0.4)),
        (200, V(**a, hf=(26, 8), hb=(18, 18), wang=-90, fire=0.8, glint=1)),
        (200, V(**a, hf=(26, 7.6), hb=(16, 16), wang=-90, fire=1.2, sparks=(26, 6, 10))),
        (200, V(**a, hf=(26, 7.4), hb=(15, 15), wang=-90, fire=1.5, sparks=(26, 4, 14))),
        (200, V(**a, hf=(26, 7.4), hb=(15, 15), wang=-90, fire=1.8, sparks=(26, 3, 18))),
        (160, V(**a, hf=(27, 9), hb=(16, 17), wang=-88, fire=1.2, sparks=(26, 3, 18))),
        (160, V(**a, hf=(29, 18), hb=(18, 24), wang=-60)),
        (160, V(**a, hf=(31, 27), hb=(19, 29), wang=10)),
        (140, V()),
    ]


def absorb(p3=False):
    kn = dict(P=(23, 40), C=(24.6, 28.4), Hd=(26.6, 21.4), hup=(0.25, -1), fb=(15, 47), ff=(30, 47), kf=(31, 43), hb=(20, 37),
              hf=(31, 33), wang=88)
    st = dict(P=(24, 33.6), C=(24, 21), Hd=(24.6, 13.2), hup=(-0.4, -1), fb=(16, 47), ff=(31, 47), hb=(14, 19), hf=(34, 19), wang=-70)
    return [
        (120, V()),
        (160, V(**kn, eye=0.6)),
        (200, V(**kn, eye=0.4, sparks=(24, 22, 10))),
        (200, V(**kn, eye=0.3, sparks=(24, 20, 16))),
        (200, V(**kn, eye=0.3, sparks=(24, 18, 20))),
        (200, V(**{**kn, "hup": (0.6, -1)}, eye=0.2, sparks=(24, 16, 24))),
        (140, V(**{**kn, "P": (23, 38), "C": (24, 26), "Hd": (25, 18.6)}, eye=1.0, sparks=(24, 14, 26))),
        (140, V(**st, eye=1.4, fire=0.8, blaze=1.0, sparks=(24, 12, 30), jaw=1.0)),
        (200, V(**st, eye=1.6, fire=1.2, blaze=1.6, sparks=(24, 10, 34), jaw=1.2)),
        (200, V(**st, eye=1.6, fire=1.2, blaze=1.8, jaw=1.2)),
        (200, V(**st, eye=1.6, fire=1.0, blaze=1.6, jaw=1.0)),
        (140, V(**{**st, "hup": (0, -1), "hb": (18, 26), "hf": (32, 27), "wang": 10}, blaze=1.4)),
        (140, V(blaze=1.2)),
        (120, V(blaze=1.0)),
    ]


def leap():
    cr = dict(P=(23, 38), C=(24, 27), Hd=(26, 20), hup=(0.3, -1), fb=(16, 47), ff=(31, 47), kf=(33, 41))
    air = dict(P=(24, 30), C=(24.6, 18.4), Hd=(26, 11), hup=(0.2, -1), fb=(19, 41), ff=(29, 40))
    dn = dict(P=(25.5, 36.6), C=(27.5, 25.4), Hd=(29.6, 18.6), hup=(0.4, -1), fb=(17, 47), ff=(32, 47), kf=(33, 41))
    return [
        (120, V()),
        (150, V(**cr, hf=(30, 32), hb=(20, 34), wang=60)),
        (260, V(**cr, hf=(29, 31), hb=(19, 33), wang=66, glint=1)),
        (110, V(**air, hf=(28, 14), hb=(22, 22), wang=-80)),
        (110, V(**air, hf=(27, 11), hb=(21, 20), wang=-86)),
        (110, V(**air, hf=(27, 11), hb=(21, 20), wang=-88)),
        (110, V(**air, hf=(28, 14), hb=(22, 21), wang=-40)),
        (90, V(**air, hf=(29, 18), hb=(25, 20), wang=40)),
        (70, V(**air, hf=(29, 22), hb=(26, 23), wang=88, fire=0.8)),
        (70, V(**dn, hf=(30, 31), hb=(27, 30), wang=90, dust=3, fire=1.0)),
        (300, V(**dn, hf=(30, 31), hb=(27, 30), wang=90, dust=1)),
        (220, V()),
    ]


def sweep():
    b = dict(P=(23, 35), C=(22, 23.4), Hd=(22.6, 16.4), hup=(-0.2, -1), fb=(14, 47), ff=(31, 47))
    t = dict(P=(26, 35.4), C=(29, 24.2), Hd=(31.6, 17.4), hup=(0.5, -1), fb=(15, 47), ff=(35, 47))
    return [
        (120, V()),
        (140, V(**b, hf=(20, 31), hb=(17, 30), wang=172)),
        (250, V(**b, hf=(17, 32), hb=(15, 31), wang=176, glint=1)),
        (60, V(**t, hf=(27, 34), hb=(22, 33), wang=110, smear=[((17, 32), 176, (27, 34), 110, 8, 31)])),
        (60, V(**t, hf=(34, 33), hb=(26, 32), wang=10, smear=[((27, 34), 110, (34, 33), 10, 8, 31)])),
        (80, V(**t, hf=(36, 30), hb=(27, 30), wang=-25, smear=[((34, 33), 10, (36, 30), -25, 8, 31)])),
        (220, V(**t, hf=(35, 28), hb=(26, 29), wang=-40)),
        (180, V(**{**t, "C": (27, 23), "Hd": (29, 15.6)}, hf=(32, 29), hb=(22, 30), wang=10)),
        (140, V()),
        (120, V()),
    ]


def rise():
    kn = dict(P=(23, 40), C=(24.4, 28.6), Hd=(26, 21.8), hup=(0.2, -1), fb=(15, 47), ff=(30, 47), kf=(31, 43), hb=(20, 37),
              hf=(31, 33), wang=88)
    return [(300, V(**kn, eye=0)), (300, V(**kn, eye=0.4)), (200, V(**kn, eye=1.0, sparks=(26, 20, 8))),
            (160, V(**{**kn, "P": (23, 38), "C": (24, 26.6), "Hd": (25.6, 19.6)}, eye=1.0)),
            (160, V(P=(23.5, 36), C=(24.4, 24), Hd=(25.8, 16.8), hup=(0.15, -1), fb=(16, 47), ff=(30, 47), hb=(20, 34), hf=(31, 32),
                    wang=60)),
            (160, V(P=(24, 34.4), C=(25, 22), Hd=(26.4, 14.4), fb=(17, 47), ff=(30, 47), hf=(31, 31), wang=45)),
            (200, V()), (200, V())]


A_ANIMS = [("idle", idle), ("walk", walk), ("combo", combo), ("overhead", overhead), ("thrust", thrust), ("chain", chain),
           ("stagger", stagger), ("death", death)]
B_ANIMS = [("ghostfire", ghostfire), ("summon", summon), ("absorb", absorb), ("leap", leap), ("sweep", sweep), ("rise", rise)]


def build_vael(name, anims_def, p3):
    K.setup(176, 112)
    O = dict(VAEL)
    anims_in = []
    for t, f in anims_def:
        fr = f()
        if p3:     # the crown blazes, eyes burn, chains brighten
            fr = [(ms, {**p, "blaze": max(p.get("blaze", 0), 1.0), "eye": max(p.get("eye", 1), 1.4)}) for ms, p in fr]
        anims_in.append((t, fr))
    anims_in = [(t, [(ms, {**p, "Hd": (p["Hd"][0] + (p["C"][0] - p["Hd"][0]) * 0.16, p["Hd"][1] + (p["C"][1] - p["Hd"][1]) * 0.16)})
                     for ms, p in fr]) for t, fr in anims_in]
    anims, infos = NG.render(O, anims_in, S, 72, 111, post=corrode(p3))
    meta = None
    if name == "vael":
        meta = {"native": 1, "frame": [176, 112], "anchor": [72, 112],
                "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(4, 2, 4)),
                "attacks": {
                    "combo": {"windows": [{"active": [3, 4], "hit": NG.hit_rect(infos, "combo", [3, 4], x_min=70)},
                                          {"active": [7, 8], "hit": NG.hit_rect(infos, "combo", [7, 8], x_min=70)},
                                          {"active": [11, 12], "hit": NG.hit_rect(infos, "combo", [11, 12], x_min=70)}]},
                    "overhead": {"active": [7, 8], "hit": NG.hit_rect(infos, "overhead", [7, 8], x_min=70)},
                    "thrust": {"active": [3, 4], "hit": NG.hit_rect(infos, "thrust", [3, 4], x_min=80)}},
                "spawn": {"chain": {"frame": 4, "at": NG.pt(infos["chain"][4]["hand_b"])},
                          "overhead": {"frame": 8, "at": NG.pt(infos["overhead"][8]["tip"])}},
                "telegraph": {"combo": {"frame": 2, "at": NG.pt(infos["combo"][2]["tip"])},
                              "overhead": {"frame": 4, "at": NG.pt(infos["overhead"][4]["tip"])},
                              "thrust": {"frame": 2, "at": NG.pt(infos["thrust"][2]["tip"])},
                              "chain": {"frame": 3, "at": NG.pt(infos["chain"][3]["hand_b"])}}}
        NG.export(name, anims, meta)
    elif name == "vael_b":
        meta = {"native": 1, "frame": [176, 112], "anchor": [72, 112],
                "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(4, 2, 4), tag=5, frame=6),
                "attacks": {"leap": {"active": [8, 9], "hit": NG.hit_rect(infos, "leap", [8, 9], x_min=60)},
                            "sweep": {"active": [3, 5], "hit": NG.hit_rect(infos, "sweep", [3, 4, 5], x_min=40)}},
                "spawn": {"ghostfire": {"frame": 6, "at": NG.pt(infos["ghostfire"][6]["hand_b"])},
                          "summon": {"frame": 7, "at": NG.pt(infos["summon"][7]["tip"])},
                          "leap": {"frame": 9, "at": NG.pt(infos["leap"][9]["tip"])}},
                "telegraph": {"ghostfire": {"frame": 4, "at": NG.pt(infos["ghostfire"][4]["hand_b"])},
                              "leap": {"frame": 2, "at": NG.pt(infos["leap"][2]["head"])},
                              "sweep": {"frame": 2, "at": NG.pt(infos["sweep"][2]["tip"])}},
                "leap": {"rise": 3, "land": 9}}
        NG.export(name, anims, meta)
    else:
        NG.export(name, anims, None)
    if name in ("vael", "vael_p3"):
        NG.closeup(name, anims, [("idle", 0), ("combo", 2), ("combo", 3), ("overhead", 5), ("thrust", 4), ("chain", 5)], scale=3)
    else:
        NG.closeup(name, anims, [("ghostfire", 6), ("summon", 6), ("absorb", 8), ("leap", 5), ("sweep", 4), ("rise", 0)], scale=3)
    return meta


# =========================================================================== the spectral court
def ghost_post(imgs, tag, k):
    return NR.ghostify(imgs, NG.BODY)


KNIGHT = dict(s=1.05, head_s=0.9, leg=(7.0, 7.2, 1.5, 1.2), arm=(5.2, 5.0, 1.3, 1.1), shoulder=4.6, hip=3.0, torso="plate", skirt=6,
              head="helm", weapon="sword", pauldron=True, cape=True, cape_len=10, cape_w=9, smear="ghost", eye_cols=("U5", "U4"),
              mats=dict(torso="K", skirt="K", leg="K", boot="K", arm="K", fore="K", hand="K", belt="L", cape="M", pauldron="K", helm="K"))
K_IDLE = dict(P=(24, 34), C=(25, 22), Hd=(26.4, 14.2), hup=(0.1, -1), fb=(19, 47), ff=(30, 47), hf=(32, 29), hb=(21, 28), wang=-35)


def kp(**kw):
    d = dict(K_IDLE)
    d.update(kw)
    return P_(**d)


def shield(Ls, info, q, k, tag):
    """A kite shield on the back arm (drawn over the back arm, under the body)."""
    s = 1.05
    h = info.get("hand_b")
    if h is None:
        return
    up_ = q.get("shield_up", 0.0)
    cx, cy = h[0] + 1 + up_ * 3, h[1] - 3 - up_ * 3
    pts = [(cx - 4 * s, cy - 6 * s), (cx + 4 * s, cy - 6 * s), (cx + 4 * s, cy + 2 * s), (cx, cy + 8 * s), (cx - 4 * s, cy + 2 * s)]
    m = K.poly_mask(pts)
    Ls["BackArm"].paint(K.n_plate(m, 1.6, (-0.2, -0.1), 1.2), "K", 1)
    Ls["BackArm"].decal([p for p in m if abs(p[0] - cx) < 0.8 or abs(p[1] - (cy - 1)) < 0.6], ("K", 4))


def knight_anims():
    lunge = dict(P=(27, 35), C=(30, 23.4), Hd=(32.4, 16.4), hup=(0.5, -1), fb=(17, 47), ff=(35, 47), hb=(24, 28))
    back = dict(P=(23, 34.4), C=(22.6, 22.4), Hd=(23.6, 15), hup=(-0.05, -1), fb=(17, 47), ff=(30, 47), hb=(22, 27))
    sh_ = dict(P=(26, 35), C=(29, 23), Hd=(31, 16), hup=(0.4, -1), fb=(17, 47), ff=(34, 47), hf=(26, 30), wang=-120)
    walkf = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.7 * abs(s_)
        walkf.append((140, kp(P=(24 + 0.3 * c, 34 + b * 0.3), C=(25.3 + 0.3 * c, 22 + b), Hd=(26.7 + 0.3 * c, 14.2 + b),
                              fb=(21 - 4 * c, 47), ff=(27 + 4 * c, 47), hf=(32, 29 + b), hb=(21, 28 + b))))
    return [
        ("idle", [(200, kp(C=(25, 22 + b), Hd=(26.4, 14.2 + b), hf=(32, 29 + b * 0.5), hb=(21, 28 + b))) for b in (0, 0.4, 0.8, 0.4)]),
        ("walk", walkf),
        ("slash", [(120, kp()), (130, kp(**back, hf=(23, 17), wang=-150)), (240, kp(**back, hf=(22, 16), wang=-160, glint=1)),
                   (120, kp(**back, hf=(22, 16), wang=-162)),
                   (60, kp(**lunge, hf=(34, 25), wang=20, smear=[((22, 16), -160, (34, 25), 20, 5, 17)])),
                   (80, kp(**lunge, hf=(35, 30), wang=50, smear=[((34, 25), 20, (35, 30), 50, 5, 17)])),
                   (200, kp(**lunge, hf=(34, 31), wang=55)), (150, kp(P=(25, 34.4), C=(27, 22.6), Hd=(28.4, 15), hf=(33, 30), wang=0)),
                   (140, kp())]),
        ("bash", [(120, kp()), (140, kp(**back, hf=(26, 30), wang=-120, shield_up=0.5)), (240, kp(**back, hf=(25, 30), wang=-125, shield_up=0.8, glint=1)),
                  (80, kp(**sh_, hb=(35, 24), shield_up=1.2)), (60, kp(**sh_, hb=(37, 24), shield_up=1.4)), (90, kp(**sh_, hb=(37, 24), shield_up=1.4)),
                  (180, kp(**sh_, hb=(33, 26), shield_up=0.8)), (140, kp())]),
        ("hurt", [(90, kp(C=(23, 22.6), Hd=(23.4, 15.2), hup=(-0.3, -1), eye=0.5)), (140, kp())]),
        ("death", [(100, kp(C=(22.6, 22.6), Hd=(22.6, 15.4), hup=(-0.4, -1))),
                   (140, kp(P=(23, 38), C=(24, 27), Hd=(26, 20), hup=(0.3, -1), fb=(17, 47), ff=(30, 47), kf=(31, 42), hf=(31, 37), wang=60))]
         + [(120, kp(P=(23, 38), C=(24, 27), Hd=(26, 20), hup=(0.3, -1), fb=(17, 47), ff=(30, 47), kf=(31, 42), hf=(31, 37), wang=60,
                     post=NG.collapse(NG.BODY, 1 - 0.18 * i, 0.2 + 0.16 * i, spread=0.2))) for i in range(5)]),
        ("appear", [(110, kp(post=NG.collapse(NG.BODY, 0.1 + 0.18 * i, 0.9 - 0.18 * i, spread=0.3))) for i in range(5)]
         + [(120, kp(eye=1.4)), (140, kp()), (140, kp())]),
    ]


PRIEST = dict(s=1.0, head_s=0.9, leg=(6.8, 7.0, 1.3, 1.1), arm=(5.0, 5.0, 1.2, 1.0), shoulder=4.0, hip=3.2, torso="robe", skirt=12,
              skirt_rag=1.6, skirt_spread=1.6, head="mitre", weapon="censer", smear="ghost", eye_cols=("U5", "U4"),
              mats=dict(torso="P", skirt="P", leg="P", boot="P", arm="P", fore="P", hand="B", belt="X", hood="P"))
PR_IDLE = dict(P=(24, 34), C=(24.6, 22), Hd=(25.6, 14.2), hup=(0.05, -1), fb=(21, 47), ff=(27, 47), hf=(30, 26), hb=(20, 30), wang=-95)


def pp(**kw):
    d = dict(PR_IDLE)
    d.update(kw)
    return P_(**d)


def priest_anims():
    walkf = [(160, pp(C=(24.6 + 0.3 * math.cos(i), 22 + 0.4 * abs(math.sin(i))), Hd=(25.6, 14.2 + 0.4 * abs(math.sin(i))),
                      fb=(22 - 2 * math.cos(i * 1.05), 47), ff=(26 + 2 * math.cos(i * 1.05), 47))) for i in range(6)]
    cast = [(120, pp()), (130, pp(hb=(26, 24))), (140, pp(hb=(30, 20), fire=0.4, fire_hand="b")),
            (160, pp(hb=(32, 18), fire=0.8, fire_hand="b", glint=1)), (160, pp(hb=(33, 17), fire=1.2, fire_hand="b")),
            (160, pp(hb=(33, 17), fire=1.5, fire_hand="b")), (90, pp(hb=(36, 20), fire=1.8, fire_hand="b", sparks=(38, 19, 12))),
            (120, pp(hb=(34, 22), fire=0.8, fire_hand="b")), (140, pp(hb=(28, 27))), (120, pp())]
    ward = [(120, pp()), (130, pp(hf=(29, 20), wang=-92)), (140, pp(hf=(28, 14), wang=-90, fire=0.4)),
            (160, pp(hf=(28, 11), wang=-90, fire=0.8, glint=1)), (160, pp(hf=(28, 10), wang=-90, fire=1.2, sparks=(28, 6, 10))),
            (160, pp(hf=(28, 10), wang=-90, fire=1.5, sparks=(28, 5, 14))), (160, pp(hf=(28, 10), wang=-90, fire=1.5, sparks=(28, 4, 18))),
            (140, pp(hf=(29, 16), wang=-92, fire=0.8)), (140, pp(hf=(30, 22), wang=-94)), (120, pp())]
    return [
        ("idle", [(220, pp(C=(24.6, 22 + b), Hd=(25.6, 14.2 + b), hf=(30, 26 + b * 0.5), hb=(20, 30 + b))) for b in (0, 0.5, 0.9, 0.5)]),
        ("walk", walkf), ("cast", cast), ("ward", ward),
        ("hurt", [(90, pp(C=(23, 22.4), Hd=(23.4, 15), hup=(-0.3, -1))), (140, pp())]),
        ("death", [(100, pp(C=(23, 22.4), Hd=(23, 15), hup=(-0.3, -1)))]
         + [(120, pp(post=NG.collapse(NG.BODY, 1 - 0.15 * i, 0.2 + 0.14 * i, spread=0.25))) for i in range(6)]),
        ("appear", [(110, pp(post=NG.collapse(NG.BODY, 0.1 + 0.18 * i, 0.9 - 0.18 * i, spread=0.3))) for i in range(5)]
         + [(120, pp(eye=1.4)), (140, pp()), (140, pp())]),
    ]


def build_knight():
    K.setup(80, 64)
    anims, infos = NG.render(KNIGHT, knight_anims(), 1.05, 32, 63, post=ghost_post, extra=shield)
    meta = {"native": 1, "frame": [80, 64], "anchor": [32, 64],
            "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(2, 1, 2)),
            "attacks": {"slash": {"active": [4, 5], "hit": NG.hit_rect(infos, "slash", [4, 5], x_min=32)},
                        "bash": {"active": [3, 5], "hit": [38, 20, 20, 44]}},
            "telegraph": {"slash": {"frame": 2, "at": NG.pt(infos["slash"][2]["tip"])}, "bash": {"frame": 2, "at": NG.pt(infos["bash"][2]["hand_b"])}}}
    NG.export("vael_knight", anims, meta)
    NG.closeup("vael_knight", anims, [("idle", 0), ("slash", 2), ("slash", 4), ("bash", 4), ("appear", 2)], scale=4)
    return meta


def build_priest():
    K.setup(80, 64)
    anims, infos = NG.render(PRIEST, priest_anims(), 1.0, 32, 63, post=ghost_post)
    meta = {"native": 1, "frame": [80, 64], "anchor": [32, 64],
            "hurtbox": NG.hurtbox(anims, ["Body", "Head"], inset=(2, 1, 2)),
            "attacks": {},
            "spawn": {"cast": {"frame": 6, "at": NG.pt(infos["cast"][6]["hand_b"])}, "ward": {"frame": 6, "at": NG.pt(infos["ward"][6]["tip"])}},
            "telegraph": {"cast": {"frame": 3, "at": NG.pt(infos["cast"][3]["hand_b"])}}}
    NG.export("vael_priest", anims, meta)
    NG.closeup("vael_priest", anims, [("idle", 0), ("cast", 6), ("ward", 6), ("appear", 2)], scale=4)
    return meta


def build_exec():
    import gen_necro_executioners as GE
    K.setup(96, 80)
    O = dict(GE.OUT_A, s=1.32, eye_cols=("U5", "U4"), smear="ghost")
    sink = lambda fr: [(ms, {**p, "Hd": (p["Hd"][0] + (p["C"][0] - p["Hd"][0]) * 0.17, p["Hd"][1] + (p["C"][1] - p["Hd"][1]) * 0.17)}) for ms, p in fr]
    appear = [(110, P_(**GE.IDLE, post=NG.collapse(NG.BODY + ["Chains"], 0.1 + 0.18 * i, 0.9 - 0.18 * i, spread=0.3))) for i in range(5)]
    appear += [(120, P_(**GE.IDLE)), (140, P_(**GE.IDLE)), (140, P_(**GE.IDLE))]
    hurt = [(90, P_(**{**GE.IDLE, "C": (23, 22), "Hd": (23.4, 15.4), "hup": (-0.3, -1)})), (140, P_(**GE.IDLE))]
    death = [(100, P_(**{**GE.IDLE, "C": (23, 22), "Hd": (23.4, 15.4), "hup": (-0.3, -1)}))]
    death += [(110, P_(**GE.IDLE, post=NG.collapse(NG.BODY + ["Chains"], 1 - 0.14 * i, 0.2 + 0.13 * i, spread=0.25))) for i in range(7)]
    anims_in = [("idle", sink(GE.idle())), ("walk", sink(GE.walk())), ("chop", sink(GE.chop())), ("sweep", sink(GE.sweep())),
                ("hurt", sink(hurt)), ("death", sink(death)), ("appear", sink(appear))]
    anims, infos = NG.render(O, anims_in, 1.32, 38, 79, post=lambda im, t, k: NR.ghostify(im, NG.BODY + ["Chains"]))
    meta = {"native": 1, "frame": [96, 80], "anchor": [38, 80],
            "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(3, 1, 3)),
            "attacks": {"chop": {"active": [5, 6], "hit": NG.hit_rect(infos, "chop", [5, 6], x_min=40)},
                        "sweep": {"active": [4, 6], "hit": NG.hit_rect(infos, "sweep", [4, 5, 6], x_min=22)}},
            "telegraph": {"chop": {"frame": 4, "at": NG.pt(infos["chop"][4]["tip"])}, "sweep": {"frame": 3, "at": NG.pt(infos["sweep"][3]["tip"])}}}
    NG.export("vael_exec", anims, meta)
    NG.closeup("vael_exec", anims, [("idle", 0), ("chop", 4), ("chop", 6), ("sweep", 5)], scale=4)
    return meta


if __name__ == "__main__":
    # King Vael himself is now built by art/gen_necro_vael2.py (Morvain's rig); this file only builds his spectral court.
    jobs = [("vael_knight", build_knight), ("vael_priest", build_priest), ("vael_exec", build_exec)]
    for name, fn in jobs:
        if NG.ONLY and name not in NG.ONLY:
            continue
        m = fn()
        print(name, "ok", m and m.get("hurtbox"))
