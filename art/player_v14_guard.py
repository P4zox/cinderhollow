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
          (dict(dx=3, dy=2, hand=(40, 26), ang=-1, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.5, flutter=2,
                fx=[("streak", 22), ("speed", (20, 17), 4, 12)]), 50),
          (dict(dx=3, dy=2, hand=(39, 26), ang=0, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.0, flutter=3,
                fx=[("streak", 8)]), 70),
          (dict(dx=5, dy=3, head_dy=1, hand=(44, 25), ang=2, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.6, flutter=4,
                fx=[("streak", 14), ("flare", "tip", 6), ("dust", 34, 3)]), 50),
          (dict(dx=5, dy=3, head_dy=1, hand=(44, 25), ang=1, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.0, flutter=5,
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
          (dict(dx=5, dy=3, hand=(44, 27), ang=1, footB=(OX + 7, 39), footF=(OX + 29, 39), flow=1.8, flutter=2,
                fx=[("streak", 26), ("speed", (20, 18), 5, 16)]), 50),
          (dict(dx=5, dy=4, head_dy=1, hand=(44, 27), ang=2, footB=(OX + 7, 39), footF=(OX + 29, 39), flow=1.3, flutter=3,
                fx=[("streak", 12), ("dust", 46, 4)]), 70),
          (dict(dx=4, dy=4, head_dy=1, hand=(42, 27), ang=2, footB=(OX + 8, 39), footF=(OX + 28, 39), flow=0.8, flutter=4), 120),
          (dict(dx=2, dy=2, hand=(36, 26), ang=-3, footF=(OX + 23, 39), flow=0.5, flutter=5), 100),
          (dict(dx=1, dy=1, hand=(33, 27), ang=-7, flow=0.3, flutter=6), 80)]
    return G.mseq(tm(fr, 200, 540, 2), grip=GS)


def sp_wheel():  # J J (pause) J: slide the hands to the middle of the haft and wheel it flat round the waist, both ends cutting
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    RG = dict(sq=0.24, w=5.0)
    ring = lambda a0, a1: ("ring", (31, 30), 27, a0, a1, RG)
    low = dict(dy=4, head_dy=1, footB=(OX + 4, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(low, dx=-1, hand=(30, 29), ang=176, flow=0.6, grip=3.0), 90),
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
          (dict(dx=1, dy=-1, hand=(35, 14), ang=-78, footB=(OX + 9, 37), footF=(FF[0] + 3, 39), flow=1.2, flutter=3,
                fx=[G.sw(w=0.5), ("flare", "tip", 5)]), 60),
          (dict(dx=0, dy=-1, hand=(32, 12), ang=-110, footB=(OX + 8, 38), footF=(FF[0] + 2, 39), flow=0.8, flutter=4), 120),
          (dict(dx=0, dy=1, hand=(32, 20), ang=-60, flow=0.5, flutter=5), 100),
          (dict(hand=(33, 27), ang=-8, flow=0.3, flutter=6), 95)]
    return G.mseq(tm(fr, 160, 500, 2), grip=GS)


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
    add("sp_drive", sp_drive, 220, 660, A(2, 4), hits=[2, 4], x0=-4)
    add("sp_hoplunge", sp_hoplunge, 200, 540, A(2, 3), x0=-4)
    add("sp_wheel", sp_wheel, 180, 600, A(2, 3), hits=[2, 3], both=True)
    add("sp_rsweep", sp_rsweep, 160, 500, A(2, 3), up=True, x0=-4)
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
