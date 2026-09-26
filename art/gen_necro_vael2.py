#!/usr/bin/env python3
"""King Vael, the Hollow Crown -- rework on Morvain's rig (agent N).  Parts: art/necro_vael_parts.py.

    python3 art/gen_necro_vael2.py [--preview] [--only idle,combo]

Sheets (176x128, faces RIGHT after mirroring, feet on the bottom row, anchor x 76):
    vael      idle(6) walk(8) combo(14) string(18) spin(10) overhead(11) thrust(8) charge(8) stagger(4) death(12)
    vael_b    leap(10) chain(10) ghostfire(10) rain(10) nova(10) summon(10) absorb(12) rise(8)
    vael_p3 / vael_b_p3   the same frames, phase 3: the crown blazes, ghost-fire cracks in the plate, streaming wisps
Meta (assets/vael_meta.json, vael_b_meta.json): per-frame hit rects ("attacks": {tag: {"frames": {i: [x,y,w,h]}}}),
telegraph frames/points, spawn frames/points, hurtbox; all in right-facing frame coords.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import necro_vael_parts as VP  # noqa: E402  (patches gen_boss)
import gen_boss as GB  # noqa: E402
from gen_boss import P_, add, lerp, hash01, line, polyline, mask_disc, inb, W, H, GROUND  # noqa: E402

BUILD = "--preview" not in sys.argv
AXR = W - GB.AX            # anchor x after mirroring (76)
WB = dict(wlayer="WeaponBack")
NEU = dict(P=(100, 85), C=(98, 61), Hd=(94, 40), grip=(80, 84), wang=148)


# =========================================================================== extra FX (ghost fire)
def fx_hand_fire(FX, info, j, fi, side, size):
    h = j["hand_" + side]
    VP.ghost_flame(FX, (h[0], h[1] - 2), size, fi, seed=3)


def fx_crown_nova(FX, info, j, fi, r, strength):
    cx, cy = add(j["Hd"], (1, -8))
    ring = [q for q in mask_disc((cx, cy), r, r * 0.85) if q not in mask_disc((cx, cy), r - 2.6, r * 0.85 - 2.4)]
    for q in ring:
        if hash01(q[0] // 2, q[1] // 2, 71) < 0.3 + 0.7 * strength:
            FX["FX"].put([q], "Y3" if strength > 0.7 else "Y2")
    inner = [q for q in mask_disc((cx, cy), r - 2.6, r * 0.85 - 2.4) if q not in mask_disc((cx, cy), r - 4.0, r * 0.85 - 3.6)]
    FX["FXBack"].put([q for q in inner if (q[0] + q[1]) % 2 == 0], "Y0")
    for k in range(14):
        a = math.radians(k * 360 / 14 + fi * 9)
        r0, r1 = r * 0.4, r * 0.4 + 5 + (k % 2) * 5
        FX["FXBack"].put(line((cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.85), (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.85)),
                         "Y1" if k % 2 else "Y2")


def fx_swords(FX, info, j, fi, n, drop):
    """Spectral swords conjured above the King (the sword-rain tell)."""
    cx, cy = add(j["Hd"], (2, -30))
    for k in range(n):
        x = cx + (k - (n - 1) / 2) * 11
        y = cy - abs(k - (n - 1) / 2) * 3 + drop * (6 + k % 2 * 4)
        for i in range(16):
            c = "Y3" if i < 2 else "Y2" if i < 9 else "Y1"
            FX["FX"].put([(int(x), int(y + i))], c)
            if 2 < i < 12:
                FX["FX"].put([(int(x) - 1, int(y + i))], "Y0")
        FX["FX"].put(line((x - 3, y + 3), (x + 3, y + 3)), "Y1")
        FX["FX"].put([(int(x), int(y) - 1)], "Y1")


def fx_souls(FX, info, j, fi, strength):
    """Souls of the court streaming in toward the chest from both sides."""
    cx, cy = j["C"]
    for k in range(int(18 * strength)):
        side = -1 if k % 2 else 1
        t = (hash01(k, 1, 61) + fi * 0.13) % 1.0
        x = cx + side * (70 * (1 - t) + 4)
        y = cy - 10 + math.sin(t * 6 + k) * 10 * (1 - t)
        FX["FX"].put([(int(x), int(y))], "Y3" if t > 0.8 else "Y2" if t > 0.5 else "Y1")
        FX["FX"].put([(int(x + side), int(y))], "Y0")


def fx_ghostcracks(FX, info, j, fi, cx, reach, bright):
    GB.fx_cracks(FX, info, j, fi, cx, reach, bright)


GB.FX_FUNCS.update({"handfire": fx_hand_fire, "nova": fx_crown_nova, "swords": fx_swords, "souls": fx_souls,
                    "gcracks": fx_ghostcracks})


# =========================================================================== animations (authored facing LEFT)
def anim_string():
    """Five-hit string: diagonal cut, backhand, rising cut, thrust, overhead finisher into the ground."""
    f = []
    f.append((110, P_(P=(101, 86), C=(103, 62), Hd=(99, 42), tw=0.7, grip=(98, 50), wang=316, **WB, foot_near=(78, 127), foot_far=(122, 127))))
    f.append((200, P_(P=(103, 90), C=(108, 63), Hd=(104, 44), tw=1.1, grip=(108, 36), wang=328, **WB, foot_near=(76, 127), foot_far=(124, 127), eyes=1.5)))
    f.append((60, P_(P=(95, 91), C=(83, 70), Hd=(73, 52), tw=-0.9, grip=(66, 88), wang=150, foot_near=(66, 127), foot_far=(122, 127), cape_wind=2,
                     smear=dict(frm=((108, 36), 328), mid=(76, 40), start=0.3, inner=14, taper=22))))
    f.append((80, P_(P=(95, 92), C=(83, 72), Hd=(73, 54), tw=-0.9, grip=(68, 94), wang=153, foot_near=(66, 127), foot_far=(122, 127), cape_wind=1)))
    # backhand: sweep back across to the rear-high side
    f.append((100, P_(P=(96, 90), C=(86, 69), Hd=(77, 50), tw=-0.8, grip=(70, 92), wang=170, foot_near=(66, 127), foot_far=(122, 127), eyes=1.3)))
    f.append((60, P_(P=(99, 87), C=(96, 64), Hd=(90, 44), tw=0.3, grip=(98, 66), wang=10, wflip=-1, **WB, foot_near=(70, 127), foot_far=(122, 127),
                     cape_wind=-3, fx=[("hsweep", (96, 82), 22, 70, 0.3, 175, 355)])))
    f.append((70, P_(P=(100, 87), C=(100, 64), Hd=(95, 44), tw=0.6, grip=(104, 64), wang=340, **WB, foot_near=(72, 127), foot_far=(122, 127))))
    # rising cut from low
    f.append((110, P_(P=(98, 96), C=(89, 77), Hd=(80, 59), tw=-1.1, grip=(84, 98), wang=168, look=-1, foot_near=(68, 127), foot_far=(124, 127), eyes=1.3)))
    f.append((60, P_(P=(96, 84), C=(90, 57), Hd=(84, 36), tw=-0.3, grip=(74, 56), wang=242, look=1, foot_near=(72, 127), foot_far=(120, 127), cape_wind=-2,
                     smear=dict(frm=((84, 98), 168), mid=(56, 100), start=0.0, inner=14, taper=22, hot=1.0))))
    f.append((70, P_(P=(97, 84), C=(93, 58), Hd=(87, 37), tw=0.1, grip=(80, 54), wang=256, foot_near=(74, 127), foot_far=(120, 127))))
    # thrust
    f.append((130, P_(P=(104, 91), C=(107, 68), Hd=(102, 49), tw=0.9, grip=(112, 82), wang=170, foot_near=(78, 127), foot_far=(126, 127), eyes=1.6)))
    f.append((60, P_(P=(92, 98), C=(84, 78), Hd=(74, 59), tw=-1.2, foot_near=(54, 127), foot_far=(126, 127), look=-1, grip=(58, 88), wang=162,
                     cape_wind=5, cape_flare=6, fx=[("dlines", (-6, -4, 8, 10)), ("tipflash", 7)])))
    f.append((80, P_(P=(93, 97), C=(85, 77), Hd=(75, 58), tw=-1.1, foot_near=(55, 127), foot_far=(126, 127), look=-1, grip=(60, 88), wang=162)))
    # overhead finisher
    f.append((140, P_(P=(100, 84), C=(98, 59), Hd=(94, 38), grip=(84, 40), wang=150, look=1, foot_near=(66, 127), foot_far=(122, 127))))
    f.append((260, P_(P=(100, 82), C=(97, 57), Hd=(94, 36), tw=-0.2, grip=(80, 22), wang=91, look=1, eyes=2.0, foot_near=(70, 127), foot_far=(122, 127), cape_wind=-1)))
    f.append((60, P_(P=(96, 97), C=(87, 76), Hd=(78, 57), tw=-0.7, grip=(76, 84), wang=92, bury=126, look=-1, foot_near=(66, 127), foot_far=(122, 127),
                     cape_wind=3, cape_flare=4, fx=[("impact", 74, 0)], smear=dict(frm=((80, 22), 91), n=8, inner=10, taper=4))))
    f.append((200, P_(P=(96, 97), C=(87, 76), Hd=(78, 57), tw=-0.7, grip=(76, 84), wang=92, bury=126, look=-1, foot_near=(66, 127), foot_far=(122, 127),
                      fx=[("impact", 74, 1), ("gcracks", 74, 44, 1.0)])))
    f.append((180, P_(P=(99, 88), C=(95, 64), Hd=(89, 44), grip=(80, 80), wang=140)))
    return f


def anim_overhead():
    hold = dict(P=(96, 97), C=(87, 76), Hd=(78, 57), tw=-0.7, grip=(76, 84), wang=92, bury=126, look=-1, foot_near=(68, 127), foot_far=(122, 127))
    return [
        (150, P_(P=(100, 86), C=(98, 61), Hd=(93, 41), grip=(86, 66), wang=210)),
        (150, P_(P=(100, 84), C=(98, 59), Hd=(94, 38), grip=(84, 40), wang=150, look=1)),
        (280, P_(P=(100, 82), C=(97, 57), Hd=(94, 36), tw=-0.2, grip=(80, 22), wang=91, look=1, eyes=1.8, foot_near=(76, 127), foot_far=(122, 127),
                 cape_wind=-1, fx=[("handfire", "near", 3.0)])),
        (60, P_(**hold, cape_wind=3, cape_flare=4, fx=[("impact", 74, 0)], smear=dict(frm=((80, 22), 91), n=8, inner=10, taper=4))),
        (300, P_(**hold, eyes=1.5, fx=[("gcracks", 74, 40, 1.0), ("impact", 74, 1)])),
        (240, P_(**hold, eyes=1.5, fx=[("gcracks", 74, 60, 1.0)])),
        (180, P_(**hold, fx=[("gcracks", 74, 66, 0.5)])),
        (150, P_(P=(98, 90), C=(93, 68), Hd=(86, 48), tw=-0.4, grip=(79, 72), wang=94, bury=126, foot_near=(70, 127), foot_far=(122, 127))),
        (150, P_(P=(99, 87), C=(96, 63), Hd=(90, 43), grip=(82, 66), wang=130)),
        (160, P_(P=(100, 86), C=(97, 62), Hd=(92, 41), grip=(80, 80), wang=146)),
        (160, P_(**NEU)),
    ]


def anim_charge():
    rush = dict(P=(96, 92), C=(84, 72), Hd=(74, 56), tw=-1.3, look=-1, grip=(104, 92), wang=20, wflip=-1, **WB, cape_wind=6, cape_flare=10, tab_wind=5)
    return [
        (140, P_(P=(102, 90), C=(104, 67), Hd=(100, 47), tw=0.8, grip=(96, 90), wang=160, foot_near=(80, 127), foot_far=(126, 127))),
        (260, P_(P=(104, 95), C=(108, 72), Hd=(104, 53), tw=1.2, grip=(108, 94), wang=40, wflip=-1, **WB, look=-1, foot_near=(76, 127), foot_far=(130, 127), eyes=2.0)),
        (90, P_(**rush, foot_near=(70, 127), foot_far=(118, 121), fx=[("lines", 112, 170, (60, 70, 82, 96))])),
        (90, P_(**rush, foot_near=(82, 121), foot_far=(112, 127), fx=[("lines", 112, 170, (64, 76, 88, 100))])),
        (90, P_(**rush, foot_near=(72, 127), foot_far=(120, 122), fx=[("lines", 112, 170, (58, 72, 86, 94))])),
        (90, P_(**rush, foot_near=(84, 122), foot_far=(110, 127), fx=[("lines", 112, 170, (62, 74, 90, 98))])),
        (160, P_(P=(98, 94), C=(90, 72), Hd=(82, 53), tw=-0.8, grip=(92, 94), wang=150, foot_near=(66, 127), foot_far=(122, 127), cape_wind=3)),
        (180, P_(**NEU)),
    ]


def anim_chain():
    """The far wrist's spectral chain whipped forward like a lash (the engine continues the lash from spawn)."""
    base = dict(twohand=False, grip=(80, 86), wang=150, chain_hand="far")
    return [
        (120, P_(**NEU)),
        (130, P_(**base, P=(102, 86), C=(104, 62), Hd=(100, 42), tw=0.7, hand_far=(126, 34), chain=[(134, 24), (142, 30), (146, 42)])),
        (130, P_(**base, P=(103, 87), C=(106, 63), Hd=(102, 44), tw=1.0, hand_far=(132, 26), chain=[(142, 18), (152, 22), (158, 34)])),
        (240, P_(**base, P=(104, 88), C=(108, 64), Hd=(104, 45), tw=1.2, hand_far=(134, 24), eyes=1.8, chain=[(146, 14), (158, 18), (164, 30)])),
        (60, P_(**base, P=(96, 88), C=(86, 66), Hd=(76, 47), tw=-0.8, hand_far=(66, 58), cape_wind=3, chain=[(46, 60), (22, 64), (2, 66)])),
        (90, P_(**base, P=(96, 88), C=(86, 66), Hd=(76, 47), tw=-0.8, hand_far=(62, 62), chain=[(40, 66), (18, 70), (0, 72)])),
        (200, P_(**base, P=(96, 88), C=(86, 66), Hd=(76, 47), tw=-0.8, hand_far=(62, 64), chain=[(40, 70), (18, 74), (0, 76)])),
        (130, P_(**base, P=(98, 87), C=(92, 64), Hd=(84, 44), tw=-0.4, hand_far=(80, 70), chain=[(66, 84), (56, 96), (50, 106)])),
        (140, P_(**base, P=(99, 86), C=(95, 62), Hd=(90, 42), hand_far=(104, 80))),
        (140, P_(**NEU)),
    ]


def anim_ghostfire():
    up = dict(P=(100, 84), C=(99, 59), Hd=(95, 37), tw=0.2, grip=(76, 66), wang=268, look=1)
    return [
        (140, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(82, 78), wang=205)),
        (140, P_(P=(100, 85), C=(99, 60), Hd=(95, 38), tw=0.1, grip=(78, 70), wang=250, look=1)),
        (180, P_(**up, eyes=1.3, fx=[("orb", 2, 6)])),
        (180, P_(**up, eyes=1.6, fx=[("orb", 4, 8)])),
        (200, P_(**up, eyes=2.0, fx=[("orb", 6.5, 10)])),
        (80, P_(P=(99, 90), C=(93, 68), Hd=(86, 49), tw=-0.4, grip=(70, 96), wang=160, eyes=2.0, fx=[("impact", 60, 0), ("gcracks", 60, 50, 1.0)])),
        (200, P_(P=(99, 90), C=(93, 68), Hd=(86, 49), tw=-0.4, grip=(70, 98), wang=162, eyes=1.6, fx=[("gcracks", 60, 70, 0.8)])),
        (150, P_(P=(100, 88), C=(96, 64), Hd=(90, 44), grip=(76, 92), wang=156)),
        (160, P_(P=(100, 86), C=(97, 62), Hd=(92, 41), grip=(80, 86), wang=150)),
        (160, P_(**NEU)),
    ]


def anim_rain():
    up = dict(P=(100, 83), C=(99, 58), Hd=(95, 36), tw=0.1, grip=(92, 38), wang=270, look=1)
    return [
        (140, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(86, 70), wang=220)),
        (140, P_(P=(100, 84), C=(99, 60), Hd=(95, 38), grip=(90, 48), wang=260, look=1)),
        (180, P_(**up, eyes=1.4, fx=[("swords", 3, 0)])),
        (180, P_(**up, eyes=1.7, fx=[("swords", 5, 0)])),
        (200, P_(**up, eyes=2.0, fx=[("swords", 7, 0), ("tipflash", 6)])),
        (90, P_(**up, eyes=2.0, fx=[("swords", 7, 1), ("flash",)])),
        (160, P_(**up, eyes=1.6)),
        (150, P_(P=(100, 85), C=(98, 60), Hd=(94, 39), grip=(86, 60), wang=220)),
        (160, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 78), wang=165)),
        (160, P_(**NEU)),
    ]


def anim_nova():
    spread = dict(twohand=False, grip=(62, 62), wang=198, hand_far=(138, 40), look=1, tw=0.4)
    fr = [(150, P_(P=(100, 90), C=(96, 68), Hd=(88, 49), grip=(82, 88), wang=152, look=-1)),
          (150, P_(P=(100, 93), C=(96, 72), Hd=(88, 53), grip=(84, 92), wang=156, look=-1, eyes=1.4, fx=[("nova", 8, 1.0)])),
          (260, P_(P=(101, 87), C=(101, 62), Hd=(98, 40), twohand=False, grip=(68, 70), wang=175, hand_far=(130, 48), look=1, eyes=1.8,
                   fx=[("nova", 12, 1.0)]))]
    for k, (r, stg) in enumerate(((18, 1.0), (32, 0.9), (46, 0.7), (60, 0.5), (74, 0.3))):
        fr.append((130, P_(P=(102, 86), C=(107, 58), Hd=(107, 35), **spread, eyes=2.2, cape_wind=-3, cape_flare=8,
                           shake=(1 if k % 2 == 0 else -1), fx=[("nova", r, stg), ("roar", r * 0.6, stg * 0.6)])))
    fr.append((200, P_(P=(100, 86), C=(100, 60), Hd=(96, 39), twohand=False, grip=(70, 76), wang=160, hand_far=(122, 70), eyes=1.5)))
    fr.append((200, P_(**NEU)))
    return fr


def anim_summon():
    plant = dict(grip=(76, 92), wang=93, bury=126, twohand=False)
    return [
        (140, P_(**NEU)),
        (150, P_(P=(100, 88), C=(96, 65), Hd=(90, 44), grip=(78, 88), wang=110, look=-1)),
        (150, P_(P=(100, 90), C=(95, 67), Hd=(88, 47), **plant, hand_far=(100, 88), fx=[("impact", 70, 0)])),
        (200, P_(P=(101, 86), C=(99, 61), Hd=(95, 39), **plant, hand_far=(128, 40), look=1, eyes=1.5, fx=[("souls", 0.5)])),
        (200, P_(P=(101, 85), C=(100, 60), Hd=(96, 38), **plant, hand_far=(132, 30), look=1, eyes=1.8, fx=[("souls", 1.0), ("handfire", "far", 3)])),
        (200, P_(P=(101, 85), C=(100, 60), Hd=(96, 38), **plant, hand_far=(133, 28), look=1, eyes=2.0, fx=[("souls", 1.0), ("handfire", "far", 4)])),
        (200, P_(P=(101, 85), C=(100, 60), Hd=(96, 38), **plant, hand_far=(133, 28), look=1, eyes=2.0, fx=[("flash",), ("handfire", "far", 5)])),
        (180, P_(P=(100, 87), C=(98, 63), Hd=(93, 42), **plant, hand_far=(122, 60))),
        (160, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(80, 86), wang=140)),
        (160, P_(**NEU)),
    ]


def anim_absorb():
    kb = dict(GB.KNEEL_BOTH)
    fr = [(150, P_(P=(102, 90), C=(98, 67), Hd=(92, 47), grip=(78, 88), wang=95, bury=126, foot_near=(80, 127), foot_far=(124, 127))),
          (200, P_(**kb)),
          (220, P_(**kb, eyes=0.6, fx=[("souls", 0.6)])),
          (220, P_(**kb, eyes=0.6, fx=[("souls", 1.0)])),
          (220, P_(**kb, eyes=1.0, fx=[("souls", 1.2)])),
          (200, P_(**dict(kb, Hd=(86, 60), C=(94, 80)), eyes=1.4, fx=[("souls", 1.4)])),
          (120, P_(P=(101, 87), C=(101, 62), Hd=(98, 40), twohand=False, grip=(68, 70), wang=175, hand_far=(130, 48), look=1, eyes=2.2, blaze=1.0,
                   fx=[("nova", 14, 1.0)])),
          (200, P_(P=(102, 86), C=(107, 58), Hd=(107, 35), twohand=False, grip=(62, 62), wang=198, hand_far=(138, 40), look=1, tw=0.4, eyes=2.4, blaze=1.4,
                   fx=[("nova", 30, 1.0), ("roar", 20, 1.0)])),
          (200, P_(P=(102, 86), C=(107, 58), Hd=(107, 35), twohand=False, grip=(62, 62), wang=198, hand_far=(138, 40), look=1, tw=0.4, eyes=2.4, blaze=1.6,
                   fx=[("nova", 48, 0.7), ("roar", 36, 0.7)])),
          (200, P_(P=(102, 86), C=(107, 58), Hd=(107, 35), twohand=False, grip=(62, 62), wang=198, hand_far=(138, 40), look=1, tw=0.4, eyes=2.2, blaze=1.6,
                   fx=[("nova", 64, 0.4)])),
          (200, P_(P=(100, 86), C=(100, 60), Hd=(96, 39), twohand=False, grip=(70, 76), wang=160, hand_far=(122, 70), eyes=1.8, blaze=1.3)),
          (200, P_(**NEU, blaze=1.0)),
    ]
    return fr


def anim_rise():
    kb = dict(GB.KNEEL_ONE)
    return [(300, P_(**kb, eyes=0.0)), (300, P_(**kb, eyes=0.5)), (220, P_(**kb, eyes=1.4)),
            (180, P_(P=(102, 94), C=(97, 72), Hd=(90, 53), look=-1, twohand=False, grip=(80, 88), wang=96, bury=126, hand_far=(114, 92),
                     foot_near=(80, 127), foot_far=(124, 127), kneel_far=(113, 116))),
            (160, P_(P=(101, 89), C=(98, 66), Hd=(92, 46), grip=(80, 84), wang=120, foot_near=(80, 127), foot_far=(122, 127))),
            (160, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(80, 84), wang=140)),
            (200, P_(**NEU, eyes=1.6)), (200, P_(**NEU))]


A_TAGS = [("idle", GB.anim_idle), ("walk", GB.anim_walk), ("combo", GB.anim_combo), ("string", anim_string), ("spin", GB.anim_spin),
          ("overhead", anim_overhead), ("thrust", GB.anim_thrust), ("charge", anim_charge), ("stagger", GB.anim_stagger),
          ("death", GB.anim_death)]
B_TAGS = [("leap", GB.anim_leap), ("chain", anim_chain), ("ghostfire", anim_ghostfire), ("rain", anim_rain), ("nova", anim_nova),
          ("summon", anim_summon), ("absorb", anim_absorb), ("rise", anim_rise)]
# frames that strike (hit rects are taken from the blade + smear on these frames)
ACTIVE = {"combo": [2, 3, 6, 7, 10, 11], "string": [2, 5, 8, 11, 15], "spin": [3, 4, 5], "overhead": [3], "thrust": [3, 4],
          "charge": [2, 3, 4, 5], "leap": [5]}
TELE = {"combo": [1, 5, 9], "string": [1, 4, 7, 10, 14], "spin": [2], "overhead": [2], "thrust": [2], "charge": [1], "leap": [1],
        "chain": [3], "ghostfire": [4], "rain": [4], "nova": [2]}
SPAWN = {"chain": 4, "ghostfire": 5, "rain": 5, "nova": 3, "summon": 6, "overhead": 3, "leap": 5, "string": 15}


# =========================================================================== phase-3 layers: the crown blazes
P3_LAYERS = ["CrownFire", "Cracks", "Wisps"]


def p3_layers(info, fi, k, imgs):
    out = {n: GB.FXLayer(n) for n in P3_LAYERS}
    if k <= 0.01:
        return {n: out[n].image() for n in P3_LAYERS}
    FXw = {"FX": out["CrownFire"]}
    j = info["j"]
    hx, hy = j["Hd"]
    for kk, t in enumerate((0.02, 0.24, 0.46, 0.68, 0.9)):
        q = lerp((hx - 9, hy - 5), (hx + 9, hy - 7), t)
        ht = (7, 11, 15, 11, 7)[kk]
        VP.ghost_flame(FXw, (q[0] + (t - 0.5) * 3, q[1] - ht + 2), (2.2 + (kk == 2) * 0.8) * k, fi, seed=kk * 5)
    for e in info.get("eyes", []):     # flaring eyes
        for i in range(int(5 * k)):
            out["CrownFire"].put([(e[0] + i, e[1] - 1 - i // 2)], "Y2" if i < 2 else "Y1")
    C, P = j["C"], j["P"]
    cracks = {"Body": [[add(C, (-6, -8)), add(C, (-3, -3)), add(C, (-5, 2)), add(C, (-1, 7))], [add(C, (-3, -3)), add(C, (3, -2)), add(C, (6, 3))],
                       [add(P, (-6, -12)), add(P, (-2, -8)), add(P, (-4, -4))]],
              "Legs": [[add(j.get("knee_near", P), (0, 4)), add(j.get("knee_near", P), (-1, 10)), add(j.get("knee_near", P), (1, 15))]]}
    above = {n: GB.BASE_LAYERS[GB.BASE_LAYERS.index(n) + 1:] for n in cracks}
    for lname, polys in cracks.items():
        src = imgs[lname].load()
        for pl in polys:
            for i, q in enumerate(polyline(pl)):
                if not inb(*q) or src[q][3] == 0:
                    continue
                if any(imgs[a].load()[q][3] and a not in ("Glow", "FX", "FXBack") for a in above[lname]):
                    continue
                out["Cracks"].put([q], "Y2" if i % 3 else "Y1")
    cape = imgs["Cape"].load()
    cols = {}
    for y in range(30, H):
        for x in range(W - 1, 60, -1):
            if cape[x, y][3]:
                cols[y] = x
                break
    ys = sorted(cols)
    for t in range(int(16 * k)):
        if not ys:
            break
        y0 = ys[int(hash01(t, 5, 87) * len(ys))]
        age = (fi * 0.37 + hash01(t, 6, 88)) % 1.0
        x = cols[y0] + 1 + age * 12 + math.sin(age * 6 + t) * 2
        y = y0 - age * 24
        out["Wisps"].put([(int(x), int(y))], "Y2" if age < 0.3 else "Y1" if age < 0.6 else "Y0")
    return {n: out[n].image() for n in P3_LAYERS}


P3_ORDER = GB.BASE_LAYERS[:-2] + ["Cracks", "Glow", "CrownFire", "Wisps", "FX"]


# =========================================================================== render + export
def render_tags(tagdefs):
    frames, frames3, tags, infos = [], [], [], {}
    for name, fn in tagdefs:
        fr = fn()
        sec = GB.secondary(fr, loop=name in ("idle", "walk"))
        a = len(frames)
        infos[name] = []
        for k, (ms, p) in enumerate(fr):
            L, FX, info = GB.render(p, a + k, sec[k])
            VP.draw_chains(FX, info["j"], p, a + k)
            if p["weapon"]:    # the bone blade (Morvain's filter only keeps his steel/gold colours)
                wpx, _ = VP.weapon_geom(p["grip"], p["wang"], p["wflip"])
                ca, sa = math.cos(math.radians(p["wang"])), math.sin(math.radians(p["wang"]))
                info["blade"] = {q for q in wpx if inb(*q) and (q[0] + .5 - p["grip"][0]) * ca + (q[1] + .5 - p["grip"][1]) * sa > 8
                                 and q[1] < p.get("bury", 999)}
            imgs = GB.compose(L, FX, info)
            if p.get("shake"):
                imgs = GB.shift_imgs(imgs, p["shake"])
            blaze = p.get("blaze", 0)
            p3k = 1.0 if not p.get("dissolve") else max(0.0, 1 - p["dissolve"] * 1.4)
            p3 = p3_layers(info, a + k, p3k, imgs)
            if blaze:     # the absorb/phase-change frames show the blaze on the phase-1 sheet too
                b3 = p3_layers(info, a + k, blaze * 0.8, imgs)
                imgs["FX"] = Image.alpha_composite(imgs["FX"], b3["CrownFire"])
            if p.get("dissolve"):
                both = GB.dissolve({**imgs, **p3}, p["dissolve"])
                imgs = {n: both[n] for n in imgs}
                p3 = {n: both[n] for n in p3}
            flip = lambda d: {n: im.transpose(Image.FLIP_LEFT_RIGHT) for n, im in d.items()}
            imgs, p3 = flip(imgs), flip(p3)
            frames.append({"ms": ms, "cels": imgs})
            frames3.append({"ms": ms, "cels": {**imgs, **p3}})
            infos[name].append(info)
        tags.append((name, a, len(frames) - 1))
        print("rendered", name, len(fr))
    return frames, frames3, tags, infos


def mx(x):
    return W - 1 - x


def mrect(r):
    x, y, w, h = r
    return [W - x - w, y, w, h]


def mpt(p):
    return [int(round(mx(p[0]))), int(round(p[1]))]


def rect_of(info):
    pts = {q for q in (info["blade"] | info["smear"]) if inb(*q)}
    return mrect(GB.bbox(pts, pad=1)) if pts else None


def glint_of(info):
    j = info["j"]
    if j.get("weapon", True) and info.get("tip"):
        q = VP.weapon_point(j["grip"], j["wang"], VP.BLADE["end"] - 8, 1.5, j["wflip"])
        return mpt(q)
    return mpt(j["Hd"])


def spawn_of(tag, info):
    j = info["j"]
    if tag == "chain":
        return mpt(j["hand_far"])
    if tag in ("overhead", "string", "leap"):
        t = info.get("tip") or (74, GROUND)
        return [int(round(mx(t[0]))), GROUND]
    if tag == "ghostfire":
        return mpt(info["tip"]) if info.get("tip") else mpt((74, GROUND))
    if tag in ("rain", "nova", "summon"):
        return mpt(add(j["Hd"], (1, -8)))
    return mpt(j["C"])


def build_meta(tags, infos, frames):
    start = {t: a for t, a, _ in tags}
    meta = {"native": 1, "frame": [W, H], "anchor": [AXR, H], "attacks": {}, "telegraph": {}, "spawn": {}}
    for t, _, _ in tags:
        if t == "charge":    # the shoulder rush: the body itself is the weapon
            meta["attacks"][t] = {"frames": {str(k): [AXR + 4, 46, 40, 82] for k in ACTIVE[t]}}
        elif t in ACTIVE:
            meta["attacks"][t] = {"frames": {str(k): rect_of(infos[t][k]) for k in ACTIVE[t] if rect_of(infos[t][k])}}
        if t in TELE:
            meta["telegraph"][t] = [{"frame": k, "at": glint_of(infos[t][k])} for k in TELE[t]]
        if t in SPAWN:
            meta["spawn"][t] = {"frame": SPAWN[t], "at": spawn_of(t, infos[t][SPAWN[t]])}
    im = frames[0]["cels"]
    core = set()
    for n in ("Legs", "Body", "FrontArm"):
        if n in im:
            src = im[n].load()
            core |= {(x, y) for y in range(H) for x in range(W) if src[x, y][3]}
    hb = GB.bbox(core, pad=0)
    top = int(NEU["Hd"][1] - 10)
    meta["hurtbox"] = [hb[0] + 5, top, hb[2] - 10, H - top]
    return meta


def preview(frames, tags, path, order, scale=2):
    cols = max(b - a + 1 for _, a, b in tags)
    pad = 2
    sheet = Image.new("RGBA", (cols * (W + pad) * scale + 60, len(tags) * (H + pad) * scale), (0x0e, 0x0d, 0x16, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))
            fr.alpha_composite(GB.flatten(frames[i]["cels"], order))
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), ((i - a) * (W + pad) * scale, r * (H + pad) * scale))
        d.text((4, r * (H + pad) * scale + 2), t, fill=(230, 230, 230, 255))
    sheet.save(path)


def hitcheck(frames, tags, meta, name):
    start = {t: a for t, a, _ in tags}
    items = [(t, int(k), r) for t, d in meta["attacks"].items() for k, r in d["frames"].items()]
    if not items:
        return
    s = 2
    sheet = Image.new("RGBA", (min(8, len(items)) * (W + 2) * s, ((len(items) + 7) // 8) * (H + 2) * s), (0x0e, 0x0d, 0x16, 255))
    for i, (t, k, r) in enumerate(items):
        fr = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))
        fr.alpha_composite(GB.flatten(frames[start[t] + k]["cels"], GB.BASE_LAYERS))
        dd = ImageDraw.Draw(fr)
        dd.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], outline=(255, 60, 60, 255))
        hb = meta["hurtbox"]
        dd.rectangle([hb[0], hb[1], hb[0] + hb[2] - 1, hb[1] + hb[3] - 1], outline=(60, 230, 90, 255))
        dd.text((2, 2), f"{t} {k}", fill=(255, 255, 255, 255))
        sheet.alpha_composite(fr.resize((W * s, H * s), Image.NEAREST), ((i % 8) * (W + 2) * s, (i // 8) * (H + 2) * s))
    sheet.save(os.path.join(ART, "previews", f"{name}_hitcheck.png"))


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    for sheet, defs in (("vael", A_TAGS), ("vael_b", B_TAGS)):
        d2 = [(n, f) for n, f in defs if not only or n in only]
        if not d2:
            continue
        frames, frames3, tags, infos = render_tags(d2)
        preview(frames, tags, os.path.join(ART, "previews", f"{sheet}2.png"), GB.BASE_LAYERS)
        preview(frames3, tags, os.path.join(ART, "previews", f"{sheet}2_p3.png"), P3_ORDER)
        if only:
            continue
        meta = build_meta(tags, infos, frames)
        hitcheck(frames, tags, meta, sheet)
        with open(os.path.join(asebuild.ASSETS, f"{sheet}_meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
        if BUILD:
            asebuild.build(sheet, W, H, GB.BASE_LAYERS, frames, tags)
            asebuild.build(sheet + "_p3", W, H, P3_ORDER, frames3, tags)
        print(sheet, "ok", len(frames), "frames")
    c = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))


if __name__ == "__main__":
    main()
