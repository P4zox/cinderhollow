"""v16 fatality tags for the guard group (role `fguard`): Sword & Shield, Spear, and the Close-range Bow. Registered by
gen_player.py after V15 (same register(G) contract as player_v16_fatal_blade.py: [(tag, fn, opts)]).

Each tag is played on the fatality's own clock (web/src/79_fatality.js time-maps it over the def's `dur`), so the frame
ms below ARE the choreography: keep them in step with the steps in web/src/79d_fatal_guard.js (frame starts listed).
No `active` meta: fatalities deal their damage through the framework's hit beats.

  sh_fatal        SWORD & SHIELD "Bulwark's End" (1500 ms)
                  0 step in | 90 coil behind the shield | 220 SHIELD BASH | 350 step in, blade cocked high point-down |
                  560 DOWNWARD STAB | 730 wrench free, shield hauled overhead | 980 SHIELD SLAM | 1080 low hold (the crest
                  blooms) | 1300 rise | 1410 recover
  sp_fatal        SPEAR "Skypiercer", small foes (1600 ms): the foe is impaled and hoisted on the spear
                  0 coil | 200 IMPALE | 340 lever it up | 460 hoisted high | 600 hold (lightning runs down the haft) |
                  820 sink | 880 SKYWARD THRUST | 930 held at full stretch | 1200 lower | 1400 recover
  sp_fatal_vault  SPEAR "Skypiercer", bosses (1600 ms): the spear stays in the boss and you vault up the haft
                  0 coil | 200 IMPALE | 340 spring | 410 swinging up the haft | 500 apex (lightning) | 810 DRIVE IT HOME |
                  860 hold | 1060 wrench free, drop | 1180 land | 1350 rise
                  (the body never leaves the frame: the height comes from the engine's move steps, the art only poses)
  bw_fatal        BOW "Point-Blank Pyre" (1500 ms)
                  0 step in | 90 chamber the kick | 170 KICK | 300 set | 380 nock three | 480 full draw (smouldering) |
                  680 LOOSE point-blank | 730 recoil | 850 bow swept down and away | 980 the pyre ignites (hold) |
                  1350 recover

`python3 art/player_v16_fatal_guard.py` prints the frames/total check.
"""
import math

G = None   # gen_player, set by register()
SPEC = {}


# =================================================================================================== SWORD & SHIELD
def sh_fatal():  # Bulwark's End: shield bash -> step in, downward stab -> shield hauled overhead -> slam (the golden crest)
    OX, FF = G.OX, G.FF
    SB = dict(sx=0.42)
    HIGH = dict(sx=0.5, rot=-32)
    SLAM = dict(sx=0.45, rot=74)
    low = dict(footB=(OX + 6, 39), footF=(FF[0] + 5, 39))
    fr = [
        # step in behind the shield, the blade turned back
        (dict(dx=1, dy=1, hand=(30, 23), ang=-40, off=(35, 23), footF=(FF[0] + 2, 39), flow=0.8, flutter=1,
              shield=dict(sx=0.6)), 90),
        # coil: sunk low behind the rim, the whole body loaded
        (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 30), ang=166, off=(31, 24), footB=(OX + 5, 39), footF=(FF[0] + 1, 39),
              flow=0.2, flutter=2, shield=dict(sx=0.5), fx=[("glint", (34, 19))]), 130),
        # SHIELD BASH (beat 1)
        (dict(dx=4, dy=2, hand=(29, 29), ang=158, off=(40, 24), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.5, flutter=3,
              shield=SB, fx=[("speed", (21, 19), 5, 14), ("flare", (45, 24), 6)]), 50),
        (dict(dx=4, dy=2, hand=(29, 29), ang=158, off=(40, 24), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.1, flutter=4,
              shield=SB), 80),
        # step in: the blade cocked high, point down at the foe; the shield swung wide
        (dict(dx=2, dy=-1, hand=(37, 8), ang=32, off=(30, 26), footB=(OX + 8, 39), footF=(FF[0] + 3, 39), flow=0.7, flutter=5,
              shield=dict(sx=0.55, rot=14), fx=[("glint", "tip")]), 130),
        (dict(dx=2, dy=-2, head_dx=-1, hand=(36, 7), ang=30, off=(29, 26), footB=(OX + 10, 38), footF=(FF[0] + 3, 39), flow=0.5,
              flutter=6, shield=dict(sx=0.55, rot=18)), 80),
        # DOWNWARD STAB (beat 2), then driven deeper
        (dict(dx=5, dy=2, hand=(42, 20), ang=38, off=(31, 26), footB=(OX + 9, 39), footF=(OX + 27, 39), flow=1.6, flutter=7,
              shield=dict(sx=0.55, rot=10), fx=[("streak", 14), ("flare", "tip", 5)]), 50),
        (dict(dx=5, dy=3, head_dy=1, hand=(43, 22), ang=40, off=(31, 27), footB=(OX + 9, 39), footF=(OX + 27, 39), flow=1.0,
              flutter=8, shield=dict(sx=0.55, rot=10), fx=[("dust", 50, 3)]), 120),
        # wrench free, the shield hauled up overhead, rim to the sky
        (dict(dx=3, dy=0, hand=(30, 28), ang=160, off=(35, 10), footB=(OX + 7, 38), footF=(FF[0] + 3, 39), flow=0.6, flutter=9,
              shield=HIGH, fx=[("glint", (38, 6))]), 140),
        (dict(dx=3, dy=-1, head_dx=-1, hand=(30, 27), ang=162, off=(34, 8), footB=(OX + 8, 37), footF=(FF[0] + 3, 39), flow=0.4,
              flutter=10, shield=dict(sx=0.5, rot=-38)), 110),
        # SHIELD SLAM (beat 3): rim first, down onto the foe
        (dict(dx=5, dy=3, hand=(31, 28), ang=150, off=(42, 20), footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.5, flutter=11,
              shield=dict(sx=0.45, rot=38), fx=[("vspeed", (43, 8), 3, 10)]), 40),
        (dict(dx=5, dy=5, head_dy=1, hand=(32, 29), ang=140, off=(43, 28), flow=1.4, flutter=12, shield=SLAM,
              fx=[("dust", 47, 8), ("flare", (47, 35), 7), ("rings", (47, 38), (5, 11))], **low), 60),
        # the low hold under the crest
        (dict(dx=5, dy=5, head_dy=1, hand=(32, 29), ang=140, off=(43, 28), flow=0.7, flutter=13, shield=SLAM,
              fx=[("dust", 47, 3)], **low), 220),
        (dict(dx=3, dy=2, hand=(33, 27), ang=60, off=(37, 24), footF=(FF[0] + 2, 39), flow=0.5, flutter=14,
              shield=dict(sx=0.55, rot=10)), 110),
        (dict(dx=1, hand=(34, 27), ang=-25, off=(32, 25), flow=0.3, flutter=15), 90),
    ]
    return G.mseq(fr)


# =================================================================================================== SPEAR
def sp_fatal():  # Skypiercer (small foes): impale -> hoist the foe on the spear -> lightning -> skyward thrust through it
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [
        # coil low, the point level at the foe's belly
        (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 28), ang=-4, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.3,
              fx=[("glint", "tip")]), 200),
        # IMPALE (beat 1)
        (dict(dx=4, dy=2, hand=(38, 26), ang=-2, footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.6, flutter=1,
              fx=[("streak", 22), ("flare", "tip", 6)]), 50),
        (dict(dx=4, dy=3, head_dy=1, hand=(37, 26), ang=-3, footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.0, flutter=2), 90),
        # lever it up, the feet braced wide
        (dict(dx=2, dy=2, hand=(34, 26), ang=-28, footB=(OX + 5, 39), footF=(OX + 24, 39), flow=0.8, flutter=3,
              fx=[("dust", 40, 3)]), 120),
        # hoisted high on the spear, the arms driven up
        (dict(dx=1, dy=1, head_dx=-1, hand=(35, 20), ang=-46, footB=(OX + 5, 39), footF=(OX + 23, 39), flow=0.6, flutter=4), 140),
        (dict(dx=1, dy=2, head_dx=-1, head_dy=1, hand=(35, 21), ang=-47, footB=(OX + 5, 39), footF=(OX + 23, 39), flow=0.5,
              flutter=5), 220),
        # sink, then the SKYWARD THRUST (beat 3) clean through it
        (dict(dx=0, dy=3, head_dy=1, hand=(31, 25), ang=-50, footB=(OX + 4, 39), footF=(OX + 22, 39), flow=0.3, flutter=6), 60),
        (dict(dx=3, dy=-1, hand=(37, 17), ang=-58, footB=(OX + 9, 37), footF=(OX + 26, 39), flow=1.6, flutter=7,
              fx=[("streak", 24), ("flare", "tip", 7)]), 50),
        (dict(dx=3, dy=-1, hand=(37, 16), ang=-59, footB=(OX + 9, 37), footF=(OX + 26, 39), flow=1.0, flutter=8), 270),
        (dict(dx=2, dy=1, hand=(35, 24), ang=-32, footF=(OX + 23, 39), flow=0.6, flutter=9), 200),
        (dict(dx=1, hand=(33, 27), ang=-8, flow=0.3, flutter=10), 200),
    ]
    return G.mseq(fr, grip=GS)


def sp_fatal_vault():  # Skypiercer (bosses): impale -> vault up the haft -> lightning at the apex -> drive it home -> drop
    OX, FF, GS = G.OX, G.FF, G.GRIP_SPEAR
    fr = [
        (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 28), ang=-8, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.3,
              fx=[("glint", "tip")]), 200),
        # IMPALE (beat 1), slightly upward into the chest
        (dict(dx=4, dy=2, hand=(38, 25), ang=-30, footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.6, flutter=1,
              fx=[("streak", 22), ("flare", "tip", 6)]), 50),
        (dict(dx=4, dy=3, head_dy=1, hand=(38, 26), ang=-30, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.0, flutter=2,
              fx=[("dust", 40, 3)]), 90),
        # spring off the floor, both hands on the lodged haft
        (dict(dx=3, dy=0, hand=(36, 22), ang=-10, footB=(OX + 9, 37), footF=(OX + 20, 36), flow=1.2, flutter=3, air=True,
              fx=[("dust", 22, 4)]), 70),
        # swinging up over it
        (dict(hand=(37, 24), ang=25, flow=1.5, flutter=4, **G.TUCK), 90),
        # the apex: pressed up on the haft like a gymnast, legs swept back
        (dict(dy=-1, hand=(36, 25), ang=58, footB=(OX + 5, 34), footF=(OX + 13, 35), air=True, flow=1.0, flutter=5,
              fx=[("glint", (40, 25))]), 150),
        (dict(dy=-1, head_dy=1, hand=(36, 25), ang=59, footB=(OX + 5, 34), footF=(OX + 13, 35), air=True, flow=0.8, flutter=6), 160),
        # DRIVE IT HOME (beat 3): the whole weight shoved down the haft
        (dict(dy=1, head_dy=1, hand=(39, 28), ang=64, footB=(OX + 3, 33), footF=(OX + 10, 36), air=True, flow=1.6, flutter=7,
              fx=[("streak", 18), ("flare", (44, 33), 7)]), 50),
        (dict(dy=1, head_dy=1, hand=(39, 28), ang=64, footB=(OX + 3, 33), footF=(OX + 10, 36), air=True, flow=1.0, flutter=8), 200),
        # wrench it free and drop
        (dict(hand=(34, 22), ang=-30, flow=0.9, flutter=9, **G.AIR), 120),
        (dict(dy=4, head_dy=1, hand=(34, 28), ang=-10, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.7, flutter=10,
              fx=[("dust", 30, 5)]), 170),
        (dict(dy=1, hand=(33, 27), ang=-8, flow=0.3, flutter=11), 250),
    ]
    return G.mseq(fr, grip=GS)


# =================================================================================================== BOW
def bw_fatal():  # Point-Blank Pyre: a kick that stuns -> nock three -> point-blank loose -> the bow swept away, the pyre lights
    OX, FF = G.OX, G.FF
    import player_v15_bow as B
    AIM, LOOSE = B.AIM, B.LOOSE
    st = dict(footB=(OX + 6, 39), footF=(FF[0] + 3, 39))
    fr = [
        (dict(dx=1, dy=1, hand=(36, 25), ang=-30, bwD=0.0, footF=(FF[0] + 2, 39), flow=0.8, flutter=1), 90),
        # chamber the kick: weight on the back foot, the front knee drawn up, the bow pulled back out of the way
        (dict(dx=-1, dy=0, head_dx=-1, hand=(33, 25), ang=-48, bwD=0.0, footB=(OX + 8, 39), footF=(OX + 20, 31), flow=0.5,
              flutter=2), 80),
        # KICK (beat 1): the heel driven straight out into the foe
        (dict(dx=-1, dy=0, head_dx=-2, hand=(31, 25), ang=-56, bwD=0.0, footB=(OX + 7, 39), footF=(OX + 24, 27), bendF=-1,
              flow=1.3, flutter=3, fx=[("speed", (26, 27), 3, 10), ("flare", (41, 27), 5)]), 60),
        (dict(dx=-1, dy=0, head_dx=-2, hand=(31, 25), ang=-56, bwD=0.0, footB=(OX + 7, 39), footF=(OX + 24, 27), bendF=-1,
              flow=1.0, flutter=4), 70),
        # set the feet, bow up
        (dict(dx=-1, dy=1, hand=(37, 24), ang=-18, bwD=0.0, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.6, flutter=5), 80),
        # nock three (the two outer shafts are drawn by the engine), then the full draw, the heads smouldering
        (dict(dx=0, dy=1, **AIM(39, 22, -3, 5.0), flow=0.45, flutter=6, **st), 100),
        (dict(dx=-1, dy=1, head_dx=-1, **AIM(41, 21, 0, 9.5), flow=0.5, flutter=7, **st, fx=[("glint", "tip")]), 200),
        # LOOSE (beat 2) at point-blank, the bow kicks up
        (dict(dx=0, dy=1, **LOOSE(42, 21, 0, (22, 19)), flow=1.1, flutter=8, **st,
              fx=[("streak", 14), ("flare", (46, 21), 5)]), 50),
        (dict(dx=-1, dy=1, **LOOSE(41, 19, -14, (21, 18)), flow=0.9, flutter=9, footB=(OX + 5, 39), footF=(FF[0] + 2, 39)), 120),
        # the bow swept down and away, the string hand flung back: the match struck
        (dict(dx=-2, dy=1, head_dx=-1, hand=(37, 28), ang=34, bwD=0.0, bwA=False, bwPullAt=(24, 21), footB=(OX + 4, 39),
              footF=(FF[0] + 1, 39), flow=0.9, flutter=10), 130),
        # the pyre ignites: standing tall, the bow held low and out, the cape thrown by the blast
        (dict(dx=-2, dy=0, hand=(38, 30), ang=62, bwD=0.0, bwA=False, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=1.4,
              flutter=11), 220),
        (dict(dx=-2, dy=0, hand=(38, 30), ang=62, bwD=0.0, bwA=False, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.6,
              flutter=12), 150),
        (dict(dx=-1, hand=(36, 25), ang=-26, bwD=0.0, flow=0.3, flutter=13), 150),
    ]
    return B.bseq(fr)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    E = []

    def add(tag, fn, total, settle=True, **meta):
        SPEC[tag] = total
        E.append((tag, g.settled(fn) if settle else fn, meta))

    add("sh_fatal", sh_fatal, 1500)
    add("sp_fatal", sp_fatal, 1600)
    add("sp_fatal_vault", sp_fatal_vault, 1600, settle=False)
    try:
        import player_v15_bow  # noqa: F401  (the bow's draw-state weapon cel)
        add("bw_fatal", bw_fatal, 1500, settle=False)
    except Exception as e:  # noqa: BLE001
        import sys
        print("WARNING: bw_fatal skipped: %r" % (e,), file=sys.stderr)
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    mod = sys.modules.get("player_v16_fatal_guard")
    for t in [e[0] for e in mod.register(GP)]:
        ms = [m for _, m in fns[t]()]
        print(f"{t:15} frames {len(ms):3}  total {sum(ms):5}  spec {mod.SPEC.get(t)}  {'OK' if sum(ms) == mod.SPEC.get(t) else 'MISMATCH'}")
