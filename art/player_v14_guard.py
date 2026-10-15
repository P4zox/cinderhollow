"""v14 combo pass: new player tags for the guard group -- Sword & Shield (sh_, knight_shield) and Spear (sp_, spear).
Registered by gen_player.py with the same register(G) contract as player_v13_a.py: [(tag, fn, opts)], fn() -> [(cels, ms)].

Every attack is timed to its move row in web/src/76_mech_guard.js (wind-up = the frames before the first active frame,
total = all frames; tm() rescales a hand-timed sequence onto those two numbers) and reads anticipation -> smear -> impact
-> follow-through -> settle.

  sh_jab     J K          shield jab: the shield punched straight out from the hip, rim first          110 / 330
  sh_rim     J J J K      rim upper: crouch under the foe and drive the shield's rim up through it       200 / 540
  sh_charge  L -> K       shield charge: out of the backhop, a short low rush behind the shield          200 / 520
  sh_wheel   J J . J      wheel cut: a full turn, blade out flat, the shield edge leading round the back  160 / 560 (2 hits)
  sp_drive   J J J K      impaling drive: the thrust driven in, then twisted and wrenched deeper         220 / 660 (2 hits)
  sp_hoplunge L -> K      hop lunge: off the hop, a long low lunge at full stretch                       200 / 540
  sp_wheel   J J . J      wheeling haft: the spear spun flat round the waist, tip in front, butt behind  180 / 600 (2 hits)
  sp_rsweep  block K, J   rising sweep: out of the counter-thrust, the haft swept up overhead            160 / 500
"""
import math

G = None   # gen_player, set by register()
SPEC = {}  # tag -> (wind, total)


def tm(frames, wind, total, hit):
    """Rescale (pose, ms) frames: frames[:hit] last `wind` ms, the rest `total - wind` (5 ms steps, >= 20 ms each)."""
    def fit(seg, want):
        if not seg:
            return []
        s = sum(ms for _, ms in seg) or 1
        out = [[p, max(20, int(round(ms * want / s / 5.0)) * 5)] for p, ms in seg]
        err = want - sum(ms for _, ms in out)
        out[max(range(len(out)), key=lambda i: out[i][1])][1] += err
        return [(p, ms) for p, ms in out]
    return fit(frames[:hit], wind) + fit(frames[hit:], total - wind)


# =================================================================================================== SWORD & SHIELD
def sh_jab():  # J K: the shield snapped out from the hip like a fist, rim first, the blade held back ready for the next cut
    OX, FF, HIP = G.OX, G.FF, G.HIP
    SB = dict(sx=0.42, rot=8)
    fr = [(dict(dx=-1, dy=1, hand=(30, 22), ang=-40, off=(31, 27), footB=(OX + 6, 39), flow=0.3, shield=HIP), 60),
          (dict(dx=-2, dy=2, head_dx=-1, hand=(29, 23), ang=-46, off=(30, 25), footB=(OX + 5, 39), flow=0.2, flutter=1,
                shield=dict(sx=0.55, rot=-6)), 50),
          (dict(dx=3, dy=1, hand=(30, 22), ang=-38, off=(40, 22), footB=(OX + 8, 39), footF=(G.FF[0] + 4, 39), flow=1.3, flutter=2,
                shield=SB, fx=[("speed", (25, 19), 4, 11), ("flare", (45, 22), 5)]), 40),
          (dict(dx=3, dy=1, hand=(30, 22), ang=-36, off=(40, 22), footB=(OX + 8, 39), footF=(G.FF[0] + 4, 39), flow=1.0, flutter=3,
                shield=SB), 60),
          (dict(dx=1, dy=1, hand=(32, 22), ang=-40, off=(35, 24), footF=(G.FF[0] + 2, 39), flow=0.6, flutter=4,
                shield=dict(sx=0.55)), 90),
          (dict(hand=(34, 25), ang=-30, off=(32, 25), flow=0.3, flutter=5), 80)]
    return G.mseq(tm(fr, 110, 330, 2))


def sh_rim():  # J J J K: sink under the foe's guard, then heave the shield's rim straight up through its chin
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=3, hand=(30, 27), ang=150, off=(33, 29), footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.3,
                shield=dict(sx=0.5, rot=-40)), 90),
          (dict(dx=-1, dy=5, head_dy=1, hand=(29, 29), ang=160, off=(34, 32), footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.2,
                flutter=1, shield=dict(sx=0.45, rot=-58), fx=[("glint", (38, 30))]), 110),
          (dict(dx=2, dy=1, hand=(30, 26), ang=150, off=(39, 20), footB=(OX + 8, 38), footF=(FF[0] + 4, 39), flow=1.3, flutter=2,
                shield=dict(sx=0.42, rot=30), fx=[("vspeed", (42, 30), 3, 10), ("dust", 44, 3)]), 45),
          (dict(dx=2, dy=-1, hand=(31, 24), ang=140, off=(39, 11), footB=(OX + 9, 37), footF=(FF[0] + 4, 39), flow=1.2, flutter=3,
                shield=dict(sx=0.42, rot=62), fx=[("flare", (43, 8), 7)]), 60),
          (dict(dx=1, dy=-1, hand=(32, 24), ang=120, off=(37, 12), footB=(OX + 8, 38), footF=(FF[0] + 3, 39), flow=0.8, flutter=4,
                shield=dict(sx=0.45, rot=55)), 120),
          (dict(dx=1, dy=1, hand=(33, 25), ang=40, off=(35, 21), footF=(FF[0] + 2, 39), flow=0.5, flutter=5,
                shield=dict(sx=0.55, rot=15)), 110),
          (dict(hand=(34, 27), ang=-25, off=(32, 25), flow=0.3, flutter=6), 90)]
    return G.mseq(tm(fr, 200, 540, 2))


def sh_charge():  # L -> K: land from the backhop already low behind the shield and drive back in with it
    OX = G.OX
    SB = dict(sx=0.42)
    fr = [(dict(dx=-2, dy=4, head_dy=1, hand=(28, 30), ang=166, off=(33, 23), footB=(OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.5,
                shield=dict(sx=0.5)), 90),
          (dict(dx=-2, dy=4, head_dx=-1, hand=(28, 30), ang=168, off=(34, 23), footB=(OX + 4, 39), footF=(G.FF[0] + 2, 39), flow=0.3,
                flutter=1, shield=dict(sx=0.48), fx=[("glint", (37, 17))]), 110),
          (dict(dx=4, dy=3, head_dx=1, hand=(30, 29), ang=160, off=(40, 23), footB=(OX + 6, 37), footF=(OX + 27, 39), flow=1.8,
                flutter=2, shield=SB, fx=[("speed", (22, 17), 6, 18), ("flare", (46, 22), 6)]), 50),
          (dict(dx=4, dy=2, hand=(30, 29), ang=158, off=(41, 23), footB=(OX + 9, 39), footF=(OX + 27, 39), flow=1.4, flutter=3,
                shield=SB, fx=[("speed", (22, 17), 4, 10), ("dust", 50, 4)]), 70),
          (dict(dx=3, dy=2, hand=(31, 29), ang=150, off=(38, 24), footB=(OX + 9, 39), footF=(OX + 25, 39), flow=0.9, flutter=4,
                shield=SB), 110),
          (dict(dx=1, dy=1, hand=(32, 27), ang=60, off=(35, 25), footF=(OX + 22, 39), flow=0.5, flutter=5), 100),
          (dict(hand=(34, 27), ang=-22, off=(32, 25), flow=0.3, flutter=6), 90)]
    return G.mseq(tm(fr, 200, 520, 2))


def sh_wheel():  # J J (pause) J: wind the hips back, then a whole turn -- the blade cuts the front, the shield's edge the back
    OX, FF = G.OX, G.FF
    RG = dict(sq=0.3, w=4.0)
    ring = lambda a0, a1: ("ring", (31, 26), 22, a0, a1, RG)
    low = dict(dy=3, footB=(OX + 5, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(low, dx=-1, head_dx=-1, hand=(27, 26), ang=176, off=(34, 24), flow=0.6, shield=dict(sx=0.6)), 80),
          (dict(low, dx=-2, head_dx=-1, hand=(26, 27), ang=172, off=(35, 24), flow=0.4, flutter=1, shield=dict(sx=0.62),
                fx=[("glint", (12, 27))]), 80),
          (dict(low, dx=1, hand=(37, 26), ang=2, off=(30, 26), flow=1.4, flutter=2, fx=[ring(180, 2)]), 45),
          (dict(low, dx=1, hand=(37, 26), ang=4, off=(30, 26), flow=1.6, flutter=3, mirror=True, behind=True,
                shield=dict(sx=0.42, rot=10), fx=[ring(180, 0), ("dust", 48, 3)]), 50),
          (dict(low, dx=2, hand=(38, 27), ang=12, off=(31, 26), flow=1.0, flutter=4, fx=[("dust", 22, 2)]), 120),
          (dict(dx=1, dy=1, hand=(36, 26), ang=-10, off=(32, 25), footF=(FF[0] + 1, 39), flow=0.6, flutter=5), 110),
          (dict(hand=(34, 27), ang=-28, off=(32, 25), flow=0.3, flutter=6), 90)]
    return G.mseq(tm(fr, 160, 560, 2))


# =================================================================================================== SPEAR
def sp_drive():  # J J J K: out of the sweep's follow-through, coil, thrust it home -- then twist and drive it a hand deeper
    OX, GS = G.OX, G.GRIP_SPEAR
    fr = [(dict(dx=-1, dy=2, hand=(30, 26), ang=-4, footB=(OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.4), 100),
          (dict(dx=-3, dy=3, head_dx=-1, hand=(26, 27), ang=-3, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 120),
          (dict(dx=3, dy=2, hand=(36, 26), ang=-1, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.5, flutter=2,
                fx=[("streak", 22), ("speed", (20, 17), 4, 12)]), 50),
          (dict(dx=3, dy=2, hand=(36, 26), ang=0, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.0, flutter=3,
                fx=[("streak", 8)]), 70),
          (dict(dx=4, dy=3, head_dy=1, hand=(37, 25), ang=2, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.6, flutter=4,
                fx=[("streak", 14), ("flare", "tip", 6), ("dust", 34, 3)]), 50),
          (dict(dx=4, dy=3, head_dy=1, hand=(37, 25), ang=1, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.0, flutter=5,
                fx=[("flare", "tip", 3)]), 120),
          (dict(dx=2, dy=2, hand=(36, 26), ang=-3, footB=(OX + 8, 39), footF=(OX + 23, 39), flow=0.6, flutter=6), 130),
          (dict(dx=1, dy=1, hand=(34, 26), ang=-6, footF=(OX + 21, 39), flow=0.4, flutter=7), 100)]
    return G.mseq(tm(fr, 220, 660, 2), grip=GS)


def sp_hoplunge():  # L -> K: land from the hop on the back foot, spring, and lunge at full stretch, the body behind the tip
    OX, GS = G.OX, G.GRIP_SPEAR
    fr = [(dict(dx=-2, dy=4, head_dy=1, hand=(27, 28), ang=-2, footB=(OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.5,
                fx=[("dust", 22, 2)]), 100),
          (dict(dx=0, dy=1, hand=(30, 26), ang=-2, footB=(OX + 6, 37), footF=(OX + 21, 36), flow=1.2, flutter=1, air=True,
                fx=[("glint", "tip")]), 100),
          (dict(dx=4, dy=3, hand=(37, 27), ang=1, footB=(OX + 7, 39), footF=(OX + 29, 39), flow=1.8, flutter=2,
                fx=[("streak", 26), ("speed", (20, 18), 5, 16)]), 50),
          (dict(dx=4, dy=4, head_dy=1, hand=(37, 27), ang=2, footB=(OX + 7, 39), footF=(OX + 29, 39), flow=1.3, flutter=3,
                fx=[("streak", 12), ("dust", 46, 4)]), 70),
          (dict(dx=4, dy=4, head_dy=1, hand=(37, 27), ang=2, footB=(OX + 8, 39), footF=(OX + 28, 39), flow=0.8, flutter=4), 120),
          (dict(dx=2, dy=2, hand=(36, 26), ang=-3, footF=(OX + 23, 39), flow=0.5, flutter=5), 100),
          (dict(dx=1, dy=1, hand=(33, 27), ang=-7, flow=0.3, flutter=6), 80)]
    return G.mseq(tm(fr, 200, 540, 2), grip=GS)


def sp_high():  # K: the high thrust -- sink with the tip low, step in, and drive it up at 40 degrees at a flier's chest
    # (the move row always asked for 'sp_high'; the sheet never had it, so the K played the level sp_heavy lunge under a
    # tall upward hit box)
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [(dict(dx=-1, dy=2, hand=(31, 27), ang=8, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3), 100),
          (dict(dx=-3, dy=4, head_dy=1, hand=(27, 30), ang=12, footB=(OX + 4, 39), footF=(FF[0] + 2, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 160),
          (dict(dx=2, dy=0, hand=(36, 22), ang=-40, footB=(OX + 8, 37), footF=(FF[0] + 4, 39), flow=1.5, flutter=2,
                fx=[("streak", 22), ("dust", 30, 3)]), 50),
          (dict(dx=2, dy=0, hand=(36, 22), ang=-41, footB=(OX + 8, 37), footF=(FF[0] + 4, 39), flow=1.1, flutter=3,
                fx=[("streak", 10), ("flare", "tip", 4)]), 70),
          (dict(dx=2, dy=1, hand=(35, 23), ang=-38, footF=(FF[0] + 4, 39), flow=0.8, flutter=4), 140),
          (dict(dx=1, dy=1, hand=(34, 25), ang=-20, footF=(FF[0] + 2, 39), flow=0.5, flutter=5), 100),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=6), 80)]
    return G.mseq(tm(fr, 260, 600, 2), grip=GS)


def sp_wheel():  # J J (pause) J: slide the hands to the middle of the haft and wheel it flat round the waist, both ends cutting
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    RG = dict(sq=0.24, w=5.0)
    ring = lambda a0, a1: ("ring", (31, 30), 27, a0, a1, RG)
    low = dict(dy=4, head_dy=1, footB=(OX + 4, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(low, dx=-1, hand=(31, 22), ang=-100, flow=0.6, grip=3.0), 90),
          (dict(low, dx=-2, head_dx=-1, hand=(29, 30), ang=172, flow=0.4, flutter=1, grip=3.0, fx=[("glint", (8, 31))]), 90),
          (dict(low, dx=1, hand=(34, 30), ang=3, flow=1.4, flutter=2, grip=3.0, fx=[ring(180, 2), ("dust", 54, 3)]), 45),
          (dict(low, dx=1, hand=(34, 30), ang=4, flow=1.6, flutter=3, grip=3.0, mirror=True, behind=True,
                fx=[ring(180, 0), ("dust", 54, 3)]), 50),
          (dict(low, dx=2, hand=(35, 30), ang=8, flow=1.0, flutter=4, grip=3.0), 130),
          (dict(dx=1, dy=2, hand=(33, 28), ang=-4, footF=(FF[0] + 1, 39), flow=0.6, flutter=5), 130),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=6), 110)]
    return G.mseq(tm(fr, 180, 600, 2), grip=GS)


def sp_rsweep():  # counter -> J: from the counter's full stretch, drop the tip and sweep the haft up over the head, lifting the foe
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [(dict(dx=2, dy=3, hand=(38, 28), ang=18, footB=(OX + 7, 39), footF=(OX + 24, 39), flow=0.6), 80),
          (dict(dx=1, dy=4, head_dy=1, hand=(36, 31), ang=28, footB=(OX + 6, 39), footF=(OX + 23, 39), flow=0.3, flutter=1,
                fx=[("dust", 52, 2)]), 80),
          (dict(dx=2, dy=1, hand=(38, 22), ang=-40, footB=(OX + 8, 38), footF=(FF[0] + 4, 39), flow=1.3, flutter=2,
                fx=[G.sw(w=0.55)]), 45),
          (dict(dx=1, dy=-1, hand=(36, 21), ang=-72, footB=(OX + 9, 37), footF=(FF[0] + 3, 39), flow=1.2, flutter=3,
                fx=[G.sw(w=0.5), ("flare", "tip", 5)]), 60),
          (dict(dx=0, dy=-1, hand=(33, 21), ang=-112, footB=(OX + 8, 38), footF=(FF[0] + 2, 39), flow=0.8, flutter=4), 120),
          (dict(dx=0, dy=1, hand=(33, 23), ang=-60, flow=0.5, flutter=5), 100),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=6), 95)]
    return G.mseq(tm(fr, 160, 500, 2), grip=GS)


# =================================================================================================== v14c: J/K mixes
def sh_kj():  # K -> J: the bash has shoved the foe off the rim -- a fast flat cut swept out from under the shield, waist high
    OX, FF = G.OX, G.FF
    SB = dict(sx=0.45)
    fr = [(dict(dx=1, dy=2, hand=(30, 29), ang=160, off=(37, 23), footF=(FF[0] + 2, 39), flow=0.6, shield=SB), 60),
          (dict(dx=0, dy=3, head_dx=-1, hand=(28, 31), ang=172, off=(36, 23), footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.3,
                flutter=1, shield=SB), 50),
          (dict(dx=2, dy=2, hand=(38, 26), ang=4, off=(35, 22), footF=(FF[0] + 3, 39), flow=1.3, flutter=2, shield=SB,
                fx=[G.sw(w=0.55), ("dust", 46, 2)]), 40),
          (dict(dx=2, dy=2, hand=(38, 27), ang=30, off=(35, 22), footF=(FF[0] + 3, 39), flow=1.0, flutter=3, shield=SB,
                fx=[G.sw(w=0.45)]), 60),
          (dict(dx=1, dy=2, hand=(35, 28), ang=-10, off=(34, 24), footF=(FF[0] + 2, 39), flow=0.5, flutter=4), 90),
          (dict(hand=(34, 27), ang=-28, off=(32, 25), flow=0.3, flutter=5), 80)]
    return G.mseq(tm(fr, 110, 330, 2))


def sh_kk():  # K -> K: haul the shield up overhead and hammer its rim straight down onto the foe's head
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=2, dy=2, hand=(30, 29), ang=160, off=(39, 22), footF=(FF[0] + 3, 39), flow=0.7, shield=dict(sx=0.45)), 70),
          (dict(dx=0, dy=0, head_dx=-1, hand=(31, 27), ang=150, off=(35, 10), footB=(OX + 7, 38), footF=(FF[0] + 2, 39), flow=0.4,
                flutter=1, shield=dict(sx=0.5, rot=-30), fx=[("glint", (38, 7))]), 150),
          (dict(dx=2, dy=3, hand=(31, 28), ang=150, off=(40, 20), footF=(FF[0] + 3, 39), flow=1.3, flutter=2,
                shield=dict(sx=0.45, rot=35), fx=[("vspeed", (41, 8), 3, 9)]), 45),
          (dict(dx=3, dy=5, head_dy=1, hand=(32, 29), ang=140, off=(41, 28), footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.3,
                flutter=3, shield=dict(sx=0.45, rot=72), fx=[("dust", 45, 7), ("flare", (45, 35), 6)]), 60),
          (dict(dx=3, dy=5, head_dy=1, hand=(32, 29), ang=140, off=(41, 28), footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.7,
                flutter=4, shield=dict(sx=0.45, rot=72), fx=[("dust", 45, 3)]), 130),
          (dict(dx=1, dy=2, hand=(33, 27), ang=60, off=(36, 24), footF=(FF[0] + 2, 39), flow=0.4, flutter=5, shield=dict(sx=0.55)), 100),
          (dict(hand=(34, 27), ang=-25, off=(32, 25), flow=0.3, flutter=6), 80)]
    return G.mseq(tm(fr, 220, 560, 2))


def sh_jkk():  # J K K: from the jab, the shield drawn across the chest and flung out again edge-first in a backhand
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=2, dy=1, hand=(30, 22), ang=-38, off=(39, 22), footF=(FF[0] + 3, 39), flow=0.8, shield=dict(sx=0.42, rot=8)), 60),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(30, 23), ang=-50, off=(27, 20), footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3,
                flutter=1, shield=dict(sx=0.6, rot=-40, layer="over")), 140),
          (dict(dx=3, dy=1, hand=(30, 23), ang=-40, off=(41, 22), footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.5, flutter=2,
                shield=dict(sx=0.4, rot=18), fx=[("speed", (24, 18), 5, 14), ("flare", (46, 21), 6)]), 45),
          (dict(dx=3, dy=1, hand=(30, 23), ang=-36, off=(41, 23), footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.1, flutter=3,
                shield=dict(sx=0.42, rot=24)), 70),
          (dict(dx=2, dy=1, hand=(32, 24), ang=-36, off=(37, 24), footF=(OX + 23, 39), flow=0.6, flutter=4, shield=dict(sx=0.55)), 110),
          (dict(hand=(34, 26), ang=-28, off=(32, 25), flow=0.3, flutter=5), 95)]
    return G.mseq(tm(fr, 200, 520, 2))


def sh_aegis():  # J J J J K (II): after the finisher, the shield lifted high and planted rim-down -- the ground rings round you
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=1, dy=1, hand=(31, 28), ang=150, off=(37, 21), footF=(FF[0] + 2, 39), flow=0.6, shield=dict(sx=0.5)), 70),
          (dict(dx=0, dy=-1, hand=(31, 26), ang=140, off=(34, 11), footB=(OX + 7, 38), footF=(FF[0] + 1, 38), flow=0.4, flutter=1,
                shield=dict(sx=0.55, rot=-10), fx=[("glint", (36, 6))]), 130),
          (dict(dx=1, dy=5, head_dy=1, hand=(31, 29), ang=140, off=(37, 30), footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=1.5,
                flutter=2, shield=dict(sx=0.45, rot=88), fx=[("dust", 38, 10), ("rings", (38, 38), (5, 10)), ("flare", (38, 34), 7)]), 60),
          (dict(dx=1, dy=6, head_dy=2, hand=(31, 29), ang=140, off=(37, 30), footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=1.0,
                flutter=3, shield=dict(sx=0.45, rot=88), fx=[("dust", 38, 6), ("rings", (38, 38), (11, 17))]), 80),
          (dict(dx=1, dy=5, head_dy=1, hand=(31, 29), ang=140, off=(37, 30), footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=0.6,
                flutter=4, shield=dict(sx=0.45, rot=88)), 170),
          (dict(dx=1, dy=2, hand=(33, 27), ang=40, off=(35, 24), footF=(FF[0] + 2, 39), flow=0.4, flutter=5, shield=dict(sx=0.55)), 100),
          (dict(hand=(34, 27), ang=-25, off=(32, 25), flow=0.3, flutter=6), 90)]
    return G.mseq(tm(fr, 200, 600, 2))


def sp_jk():  # J K: the twin thrust -- a quick low poke at the knee, snapped back, and a second at the chest
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [(dict(dx=0, dy=2, hand=(32, 27), ang=-4, footF=(FF[0] + 1, 39), flow=0.4), 70),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 29), ang=4, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 80),
          (dict(dx=2, dy=4, hand=(38, 31), ang=8, footB=(OX + 7, 39), footF=(OX + 24, 39), flow=1.2, flutter=2, fx=[("streak", 18)]), 40),
          (dict(dx=0, dy=3, hand=(32, 28), ang=0, footB=(OX + 6, 39), footF=(OX + 23, 39), flow=0.6, flutter=3), 60),
          (dict(dx=2, dy=1, hand=(38, 24), ang=-14, footB=(OX + 8, 39), footF=(OX + 24, 39), flow=1.3, flutter=4,
                fx=[("streak", 20), ("flare", "tip", 4)]), 40),
          (dict(dx=2, dy=1, hand=(38, 24), ang=-14, footB=(OX + 8, 39), footF=(OX + 24, 39), flow=0.9, flutter=5, fx=[("streak", 8)]), 70),
          (dict(dx=1, dy=1, hand=(34, 26), ang=-8, footF=(OX + 21, 39), flow=0.5, flutter=6), 90),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=7), 70)]
    return G.mseq(tm(fr, 150, 520, 2), grip=GS)


def sp_jjk():  # J J K: the recoil thrust -- the feet step back while the arms drive the spear out: hit, and keep your distance
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [(dict(dx=1, dy=1, hand=(35, 23), ang=-16, footF=(FF[0] + 2, 39), flow=0.5), 60),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(30, 26), ang=-3, footB=(OX + 3, 39), footF=(FF[0] - 2, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip"), ("dust", 18, 2)]), 100),
          (dict(dx=-2, dy=2, hand=(43, 25), ang=0, footB=(OX + 2, 39), footF=(FF[0] - 1, 39), flow=-0.4, flutter=2,
                fx=[("streak", 22), ("dust", 16, 3)]), 45),
          (dict(dx=-2, dy=2, hand=(43, 25), ang=0, footB=(OX + 2, 39), footF=(FF[0] - 1, 39), flow=-0.2, flutter=3,
                fx=[("streak", 10)]), 70),
          (dict(dx=-1, dy=2, hand=(37, 26), ang=-4, footB=(OX + 4, 39), footF=(FF[0], 39), flow=0.3, flutter=4), 110),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=5), 75)]
    return G.mseq(tm(fr, 160, 460, 2), grip=GS)


def sp_kj():  # K -> J: from the high thrust, raise the spear straight up and chop the haft down in front like a falling gate
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [(dict(dx=1, dy=1, hand=(35, 23), ang=-45, footF=(FF[0] + 3, 39), flow=0.6), 70),
          (dict(dx=0, dy=0, head_dx=-1, hand=(32, 21), ang=-98, footB=(OX + 7, 38), footF=(FF[0] + 2, 39), flow=0.3, flutter=1,
                fx=[("glint", "tip")]), 110),
          (dict(dx=2, dy=3, hand=(37, 25), ang=22, footF=(FF[0] + 4, 39), flow=1.4, flutter=2, fx=[G.sw(w=0.5)]), 45),
          (dict(dx=2, dy=4, head_dy=1, hand=(37, 27), ang=40, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.1, flutter=3,
                fx=[G.sw(w=0.4), ("dust", 52, 5), ("flare", (52, 38), 5)]), 60),
          (dict(dx=2, dy=4, head_dy=1, hand=(37, 27), ang=41, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.7, flutter=4), 130),
          (dict(dx=1, dy=2, hand=(34, 27), ang=8, footF=(FF[0] + 2, 39), flow=0.4, flutter=5), 110),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=6), 75)]
    return G.mseq(tm(fr, 180, 520, 2), grip=GS)


def sp_kk():  # K -> K (II): the sky rake -- sink under the first high thrust and drive a second one steeper, lifting the foe
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [(dict(dx=1, dy=1, hand=(35, 23), ang=-36, footF=(FF[0] + 3, 39), flow=0.6), 60),
          (dict(dx=-1, dy=4, head_dy=1, hand=(30, 28), ang=-30, footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 140),
          (dict(dx=2, dy=-1, hand=(35, 22), ang=-58, footB=(OX + 9, 37), footF=(FF[0] + 4, 39), flow=1.5, flutter=2,
                fx=[("streak", 22), ("dust", 32, 3)]), 45),
          (dict(dx=2, dy=-1, hand=(35, 22), ang=-59, footB=(OX + 9, 37), footF=(FF[0] + 4, 39), flow=1.1, flutter=3,
                fx=[("streak", 10), ("flare", "tip", 5)]), 70),
          (dict(dx=2, dy=0, hand=(35, 23), ang=-55, footF=(FF[0] + 4, 39), flow=0.8, flutter=4), 135),
          (dict(dx=1, dy=1, hand=(34, 25), ang=-25, footF=(FF[0] + 2, 39), flow=0.5, flutter=5), 100),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=6), 80)]
    return G.mseq(tm(fr, 200, 560, 2), grip=GS)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    S = g.settled
    A = lambda a, b=None: (a, a if b is None else b)
    E = []

    def add(tag, fn, wind, total, active, settle=True, **meta):
        SPEC[tag] = (wind, total)
        meta["active"] = active
        E.append((tag, S(fn) if settle else fn, meta))

    # ---- sword & shield (knight_shield)
    add("sh_jab", sh_jab, 110, 330, A(2, 3), extras=True, x0=0, fxat=(16, -18))
    add("sh_rim", sh_rim, 200, 540, A(2, 3), extras=True, x0=0, up=True, fxat=(14, -26))
    add("sh_charge", sh_charge, 200, 520, A(2, 3), extras=True, x0=0, fxat=(17, -17))
    add("sh_wheel", sh_wheel, 160, 560, A(2, 3), hits=[2, 3], both=True, extras=True)
    # ---- spear
    add("sp_high", sp_high, 260, 600, A(2, 3), x0=-4, up=True)
    add("sp_drive", sp_drive, 220, 660, A(2, 4), hits=[2, 4], x0=-4)
    add("sp_hoplunge", sp_hoplunge, 200, 540, A(2, 3), x0=-4)
    add("sp_wheel", sp_wheel, 180, 600, A(2, 3), hits=[2, 3], both=True)
    add("sp_rsweep", sp_rsweep, 160, 500, A(2, 3), up=True, x0=-4)
    # ---- v14c J/K mixes
    add("sh_kj", sh_kj, 110, 330, A(2, 3), x0=-2)
    add("sh_kk", sh_kk, 220, 560, A(2, 3), extras=True, x0=0)
    add("sh_jkk", sh_jkk, 200, 520, A(2, 3), extras=True, x0=0, fxat=(17, -18))
    add("sh_aegis", sh_aegis, 200, 600, A(2, 3), extras=True, both=True, hit=[-30, -18, 30, 0], fxat=(8, -4))
    add("sp_jk", sp_jk, 150, 520, A(2, 4), hits=[2, 4], x0=-4)
    add("sp_jjk", sp_jjk, 160, 460, A(2, 3), x0=-4)
    add("sp_kj", sp_kj, 180, 520, A(2, 3), x0=-4)
    add("sp_kk", sp_kk, 200, 560, A(2, 3), x0=-4, up=True)
    # the guard walk played backwards: backing away behind the guard (the guard never turns, so stepping back with the
    # forward cycle read as a moonwalk). Same frames in reverse order: planted feet now push the body backwards.
    walk = dict(getattr(g, "V13_MOVES", []) or []).get("sp_guard_walk")
    if walk:
        E.append(("sp_guard_back", lambda: list(reversed(walk())), {}))
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    mod = sys.modules.get("player_v14_guard") or sys.modules[__name__]
    for t, _f, _o in register(GP):
        fr = list(fns[t]())
        ms = [m for _, m in fr]
        act = GP.ACTIVE.get(t)
        wind = sum(ms[:act[0]]) if act else None
        sp = mod.SPEC.get(t) or SPEC.get(t)
        print("%-12s %2d frames  %s/%d  spec %s  %s" % (t, len(fr), wind, sum(ms), sp, "OK" if sp == (wind, sum(ms)) else "MISMATCH"))
