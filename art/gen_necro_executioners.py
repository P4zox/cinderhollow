#!/usr/bin/env python3
"""The Twin Executioners (agent N) -- mini-boss duo of the Headsman's Yard.

    python3 art/gen_necro_executioners.py [--preview] [--only executioner_a,executioner_b]

    executioner_a  "The Headsman": oxblood leather hood, scarred leather jerkin, a crescent greataxe
    executioner_b  "The Gaoler":  blackened iron hood, chains wound around the chest, the same greataxe,
                                  heavier shackle chains (it throws them)
    Both 128x80, faces right, feet on the bottom row, anchor x 48, ~60px tall, identical rig and proportions.
    tags: idle(6) walk(8) chop(11, active 6-7) sweep(10, active 5-6) chain(10, spawn 5) leap(12, active 9-10)
          charge(4 loop) stagger(4) death(10) roar(8)
Shared meta: assets/executioner_a_meta.json (b borrows it).
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import necro_rig as NR  # noqa: E402
import necro_gen as NG  # noqa: E402
from necro_rig import P_  # noqa: E402

S = 1.72
BASE = dict(s=S, head_s=0.7, leg=(7.2, 7.4, 2.4, 1.8), arm=(5.6, 5.4, 2.4, 2.0), shoulder=7.4, hip=4.0, torso="plate",
            skirt=7.0, skirt_rag=1.6, head="exec", weapon="axe", two_hand=True, haft=21, axe_w=8.0, smear="steel",
            belt_skull=False, shackles=9, pauldron=True, kneecop="Z", vambrace="Z", eye_cols=("C5", "C4"))
OUT_A = dict(BASE, mats=dict(torso="L", skirt="L", leg="L", boot="Z", arm="F", fore="F", hand="F", belt="Z", hood="E", pauldron="Z"))
OUT_B = dict(BASE, shackles=13, mats=dict(torso="Z", skirt="L", leg="L", boot="Z", arm="A", fore="A", hand="A", belt="I", hood="Z", pauldron="I"),
             eye_cols=("U5", "U3"))

IDLE = dict(P=(24, 33.6), C=(25, 21.4), Hd=(26.6, 14.6), hup=(0.15, -1), fb=(17, 47), ff=(31, 47), hb=(28, 25),
            hf=(31, 32), wang=-142)


def idle():
    fr = []
    for i in range(6):
        b = (0, 0.3, 0.6, 0.8, 0.6, 0.3)[i]
        fr.append((190, P_(**{**IDLE, "C": (25, 21.4 + b), "Hd": (26.6, 14.6 + b), "hf": (31, 31 + b * 0.5), "hb": (28, 25 + b)})))
    return fr


def walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.9 * abs(s_)
        fr.append((140, P_(**{**IDLE, "P": (24 + 0.4 * c, 33.6 + b * 0.4), "C": (25.4 + 0.5 * c, 21.4 + b), "Hd": (27 + 0.5 * c, 14.6 + b),
                              "fb": (21 - 4.5 * c, 47), "ff": (27 + 4.5 * c, 47), "hf": (31 + 0.5 * c, 31 + b), "hb": (28 + 0.5 * c, 25 + b)})))
    return fr


def chop():
    wind = dict(P=(23, 33.8), C=(22.6, 21.6), Hd=(23.8, 14.8), hup=(-0.05, -1), fb=(16, 47), ff=(30, 47))
    down = dict(P=(26, 35), C=(29.5, 24), Hd=(32.5, 17.8), hup=(0.6, -1), fb=(16, 47), ff=(34, 47))
    return [
        (140, P_(**IDLE)),
        (140, P_(**wind, hf=(27, 22), hb=(23, 24), wang=-125)),
        (150, P_(**wind, hf=(24, 13), hb=(22, 17), wang=-165)),
        (160, P_(**wind, hf=(22.5, 11), hb=(21, 15), wang=-175)),
        (260, P_(**wind, hf=(22, 10.5), hb=(20.5, 14.5), wang=178, glint=1)),
        (60, P_(**down, hf=(31, 17), hb=(27, 20), wang=-70, smear=[((22, 10.5), 178, (31, 17), -70, 12, 23)])),
        (70, P_(**down, hf=(34, 30), hb=(30, 30), wang=20, smear=[((31, 17), -70, (34, 30), 20, 12, 23)], dust=2)),
        (90, P_(**down, hf=(34, 32), hb=(30, 31), wang=38, dust=1)),
        (260, P_(**down, hf=(34, 32), hb=(30, 31.5), wang=40)),
        (180, P_(**{**down, "C": (27.5, 22.6), "Hd": (30, 15.8)}, hf=(32, 30), hb=(29, 29), wang=10)),
        (180, P_(**IDLE)),
    ]


def sweep():
    back = dict(P=(23, 34.4), C=(21.8, 22.4), Hd=(22.6, 15.6), hup=(-0.15, -1), fb=(15, 47), ff=(31, 47))
    thru = dict(P=(26, 34.6), C=(28.5, 23), Hd=(31, 16.4), hup=(0.45, -1), fb=(16, 47), ff=(34, 47))
    return [
        (140, P_(**IDLE)),
        (150, P_(**back, hf=(21, 30), hb=(19, 28), wang=170)),
        (170, P_(**back, hf=(18, 31), hb=(17, 29), wang=172)),
        (240, P_(**back, hf=(17.5, 31.5), hb=(16.5, 29.5), wang=174, glint=1)),
        (60, P_(**thru, hf=(28, 33), hb=(25, 31), wang=100, smear=[((17.5, 31.5), 174, (28, 33), 100, 12, 23)])),
        (70, P_(**thru, hf=(34, 32), hb=(30, 31), wang=15, smear=[((28, 33), 100, (34, 32), 15, 12, 23)])),
        (80, P_(**thru, hf=(35, 30), hb=(31, 29), wang=-20, smear=[((34, 32), 15, (35, 30), -20, 12, 23)])),
        (220, P_(**thru, hf=(34, 29), hb=(30, 28), wang=-35)),
        (180, P_(**{**thru, "C": (27, 22), "Hd": (29, 15.2)}, hf=(32, 30), hb=(29, 27), wang=-90)),
        (180, P_(**IDLE)),
    ]


def chain_throw():
    """The shackle chain: the axe shifts to the back hand, the front arm whips the chain forward (engine draws the lash)."""
    b = dict(P=(23.4, 33.8), C=(23, 21.8), Hd=(24.6, 15), hup=(0.05, -1), fb=(16, 47), ff=(30, 47), hb=(20, 30), wang=-120, whand="b")
    t = dict(P=(26, 34.4), C=(29, 22.6), Hd=(31.5, 16), hup=(0.5, -1), fb=(16, 47), ff=(33, 47), hb=(21, 31), wang=-115, whand="b")
    return [
        (140, P_(**IDLE)),
        (150, P_(**b, hf=(22, 22), chain=[(19, 16), (15, 18), (13, 24)])),
        (150, P_(**b, hf=(21, 18), chain=[(16, 12), (12, 13), (10, 19)])),
        (240, P_(**b, hf=(20, 16), chain=[(14, 9), (9, 11), (7, 16)], glint=1)),
        (70, P_(**t, hf=(35, 21), chain=[(40, 20), (45, 21)])),
        (90, P_(**t, hf=(37, 22), chain=[(42, 22), (46, 22)])),
        (200, P_(**t, hf=(36, 23), chain=[(41, 24), (46, 24)])),
        (140, P_(**t, hf=(32, 27), chain=[(36, 32), (40, 36)])),
        (150, P_(**{**t, "C": (27, 22), "Hd": (29, 15.4)}, hf=(31, 29), chain=[(33, 35), (36, 39)])),
        (160, P_(**IDLE)),
    ]


def leap():
    crouch = dict(P=(23, 37), C=(24, 26), Hd=(26, 19.4), hup=(0.25, -1), fb=(16, 47), ff=(31, 47), kf=(33, 40))
    air = dict(P=(24, 30), C=(24.5, 18), Hd=(26, 11.4), hup=(0.1, -1), fb=(19, 41), ff=(29, 40))
    down = dict(P=(26, 36), C=(29.5, 25), Hd=(32.5, 18.8), hup=(0.6, -1), fb=(15, 47), ff=(34, 47))
    return [
        (130, P_(**IDLE)),
        (150, P_(**crouch, hf=(27, 30), hb=(24, 31), wang=-150)),
        (250, P_(**crouch, hf=(25, 29), hb=(22, 30), wang=-160, glint=1)),
        (110, P_(**air, hf=(24, 10), hb=(22, 14), wang=-170, lift=10)),
        (110, P_(**air, hf=(23, 8), hb=(21, 12), wang=-178, lift=18)),
        (110, P_(**air, hf=(22.5, 8), hb=(21, 12), wang=178, lift=22)),
        (110, P_(**air, hf=(23, 9), hb=(21, 13), wang=175, lift=18)),
        (90, P_(**air, hf=(26, 12), hb=(24, 15), wang=-120, lift=10)),
        (70, P_(**air, hf=(30, 16), hb=(27, 18), wang=-60, lift=3, smear=[((23, 9), 175, (30, 16), -60, 12, 23)])),
        (70, P_(**down, hf=(34, 31), hb=(30, 31), wang=30, smear=[((30, 16), -60, (34, 31), 30, 12, 23)], dust=3)),
        (300, P_(**down, hf=(34, 32), hb=(30, 32), wang=40, dust=1)),
        (200, P_(**IDLE)),
    ]


def charge():
    r = dict(P=(26, 35), C=(30, 24), Hd=(33.5, 18.6), hup=(0.7, -1), hb=(24, 29), hf=(27, 31), wang=-160)
    return [(100, P_(**r, fb=(17, 47), ff=(33, 47), wind=2)), (100, P_(**{**r, "C": (30.4, 24.6)}, fb=(22, 47), ff=(28, 46), wind=2)),
            (100, P_(**r, fb=(31, 47), ff=(20, 47), wind=2)), (100, P_(**{**r, "C": (30.4, 24.6)}, fb=(26, 46), ff=(24, 47), wind=2))]


def stagger():
    st = dict(P=(22.5, 36), C=(21.5, 25), Hd=(21.8, 18), hup=(-0.3, -1), fb=(15, 47), ff=(29, 47), kf=(30, 41), hb=(19, 36),
              hf=(30, 38), wang=20, eye=0.3)
    return [(90, P_(**st)), (160, P_(**{**st, "C": (22, 26), "Hd": (22.8, 19)})), (500, P_(**{**st, "C": (22.2, 26.4), "Hd": (23.2, 19.6)})),
            (200, P_(**{**st, "C": (23, 25), "Hd": (24, 18)}))]


def death():
    sn = NG.BODY + ["Chains"]
    kneel = dict(P=(23, 40), C=(25, 29), Hd=(27.4, 22.6), hup=(0.4, -1), fb=(15, 47), ff=(30, 47), kf=(31, 43), hb=(22, 40),
                 hf=(33, 42), wang=40, eye=0)
    ash = ("B4", "B3", "E3", "E2", "E1")
    return [
        (100, P_(**{**IDLE, "C": (23, 22), "Hd": (23.4, 15.4), "hup": (-0.3, -1), "eye": 0.6})),
        (140, P_(P=(23, 37), C=(24, 26), Hd=(26, 19.6), hup=(0.3, -1), fb=(15, 47), ff=(30, 47), hb=(21, 34), hf=(31, 37), wang=30,
                 eye=0.3)),
        (240, P_(**kneel)),
        (200, P_(**kneel)),
        (120, P_(**kneel, post=NG.collapse(sn, 0.85, 0.1, pal=ash, spread=0.2))),
        (120, P_(**kneel, post=NG.collapse(sn, 0.65, 0.25, pal=ash, spread=0.3))),
        (120, P_(**kneel, post=NG.collapse(sn, 0.45, 0.4, pal=ash, spread=0.4))),
        (140, P_(**kneel, post=NG.collapse(sn, 0.28, 0.6, pal=ash, spread=0.5))),
        (160, P_(**kneel, post=NG.collapse(sn, 0.15, 0.8, pal=ash, spread=0.6))),
        (600, P_(**kneel, post=NG.collapse(sn, 0.08, 0.95, pal=ash, spread=0.7))),
    ]


def roar():
    r = dict(P=(23.5, 34), C=(23.6, 21.6), Hd=(24.4, 14.4), hup=(-0.35, -1), fb=(16, 47), ff=(31, 47))
    return [(140, P_(**IDLE)), (150, P_(**r, hf=(31, 25), hb=(17, 25), wang=-100)), (150, P_(**r, hf=(33, 20), hb=(15, 20), wang=-95)),
            (160, P_(**r, hf=(34, 17), hb=(14, 17), wang=-92, jaw=1, sparks=(26, 14, 10))),
            (160, P_(**r, hf=(34.4, 16.6), hb=(13.6, 16.6), wang=-92, jaw=1)),
            (160, P_(**r, hf=(34, 17), hb=(14, 17), wang=-92, jaw=1)), (150, P_(**r, hf=(32, 24), hb=(18, 26), wang=-110)),
            (150, P_(**IDLE))]


ANIMS = [("idle", idle), ("walk", walk), ("chop", chop), ("sweep", sweep), ("chain", chain_throw), ("leap", leap),
         ("charge", charge), ("stagger", stagger), ("death", death), ("roar", roar)]


def build(name, outfit):
    K.setup(128, 80)
    sink = lambda fr: [(ms, {**p, "Hd": (p["Hd"][0] + (p["C"][0] - p["Hd"][0]) * 0.17, p["Hd"][1] + (p["C"][1] - p["Hd"][1]) * 0.17)}) for ms, p in fr]
    anims, infos = NG.render(outfit, [(t, sink(f())) for t, f in ANIMS], S, 48, 79, loops=("idle", "walk", "charge"))
    meta = None
    if name == "executioner_a":
        meta = {"native": 1, "frame": [128, 80], "anchor": [48, 80],
                "hurtbox": NG.hurtbox(anims, ["Body", "Head", "FrontLeg", "BackLeg"], inset=(3, 1, 3)),
                "attacks": {"chop": {"active": [5, 6], "hit": NG.hit_rect(infos, "chop", [5, 6], x_min=52)},
                            "sweep": {"active": [4, 6], "hit": NG.hit_rect(infos, "sweep", [4, 5, 6], x_min=30)},
                            "leap": {"active": [8, 9], "hit": NG.hit_rect(infos, "leap", [8, 9], x_min=48)},
                            "charge": {"active": [0, 3], "hit": [52, 30, 22, 50]}},
                "spawn": {"chain": {"frame": 4, "at": NG.pt(infos["chain"][4]["hand_f"])},
                          "chop": {"frame": 6, "at": NG.pt(infos["chop"][6]["tip"])},
                          "leap": {"frame": 9, "at": NG.pt(infos["leap"][9]["tip"])}},
                "telegraph": {"chop": {"frame": 4, "at": NG.pt(infos["chop"][4]["tip"])},
                              "sweep": {"frame": 3, "at": NG.pt(infos["sweep"][3]["tip"])},
                              "chain": {"frame": 3, "at": NG.pt(infos["chain"][3]["hand_f"])},
                              "leap": {"frame": 2, "at": NG.pt(infos["leap"][2]["head"])}},
                "leap": {"rise": 3, "land": 9},
                "notes": "chain: the engine draws the thrown shackle chain from spawn.at; leap is drawn in place (lift), "
                         "the engine moves the body between frames 3 and 9."}
        NG.export(name, anims, meta)
    else:
        NG.export(name, anims, None)
    NG.closeup(name, anims, [("idle", 0), ("chop", 4), ("chop", 6), ("sweep", 5), ("chain", 5)], scale=5)
    return meta


if __name__ == "__main__":
    for name, o in (("executioner_a", OUT_A), ("executioner_b", OUT_B)):
        if NG.ONLY and name not in NG.ONLY:
            continue
        m = build(name, o)
        print(name, "ok", m and m["hurtbox"])
