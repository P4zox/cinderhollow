"""v16 fatality tags for the blade group (registered by gen_player.py after V15, same register(G) contract as v13/v14/v15).

Each fatality is ONE tag played on the fatality's own clock (web/src/79_fatality.js time-maps the tag over the
fatality's `dur`, so the frame ms below are the choreography: keep them in step with the steps in
web/src/79b_fatal_blade.js). No `active` meta: fatalities deal their damage through the framework's hit beats.

  ls_fatal   LONGSWORD "Ashen Verdict" (1600 ms): step in, plant the blade point-down and kneel over it while light
             gathers along the steel (aura 1 -> 3), wrench it up out of the floor in a rising cut (beat 1 at ~540 ms),
             hold it cocked high behind the head (the giant aura blade forms), then one huge descending slash into the
             floor (beat 2 at ~860 ms), a long low follow-through while the crescent lingers, and recover.

The katana (kt_fatal) is added here later by the blade agent. `python3 art/player_v16_fatal_blade.py` prints the check.
"""

G = None   # gen_player, set by register()
SPEC = {}


# =================================================================================================== LONGSWORD
def ls_fatal():  # Ashen Verdict: plant -> gather -> rip-up cut -> overhead -> great descending slash -> low hold -> recover
    OX, FF = G.OX, G.FF
    PL = dict(planted=(40, 21), ang=90)                            # the blade driven point-down a step ahead of the boots
    KN = dict(dy=5, footB=(OX + 3, 39), footF=(OX + 20, 39), bendB=-1)   # kneeling over the hilt
    fr = [
        # step in, the blade swung low and turned over in the hands
        (dict(dx=1, hand=(35, 24), ang=-30, footF=(FF[0] + 2, 39), flow=0.9, flutter=1), 90),
        (dict(dx=1, dy=-1, hand=(38, 15), ang=88, footB=(OX + 9, 38), footF=(FF[0] + 2, 39), flow=0.6, flutter=2,
              fx=[("glint", "tip")]), 110),
        # PLANT: driven into the floor, both hands on the pommel
        (dict(dy=3, hand=(40, 18), footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.3, flutter=3, aura=1,
              fx=[("dust", 40, 4), ("flare", (40, 38), 4)], **PL), 130),
        (dict(head_dy=1, hand=(40, 16), flow=0.1, flutter=4, aura=2, **KN, **PL), 120),
        (dict(head_dy=2, hand=(40, 16), flow=0.0, flutter=5, aura=3, fx=[("glint", (40, 22))], **KN, **PL), 80),
        # RIP UP: wrenched out of the floor in one rising cut through the foe
        (dict(dx=3, dy=1, hand=(41, 20), ang=-40, footB=(OX + 8, 39), footF=(FF[0] + 3, 39), flow=1.4, flutter=6, aura=1,
              fx=[G.sw(w=0.55, a0=92), ("dust", 44, 5), ("flare", "tip", 4)]), 45),
        (dict(dx=2, dy=-2, hand=(37, 10), ang=-100, footB=(OX + 10, 37), footF=(FF[0] + 3, 38), flow=1.2, flutter=7,
              fx=[G.sw(w=0.4)]), 60),
        # the apex: cocked high behind the head, on the toes (the aura blade forms over it)
        (dict(dx=0, dy=-1, head_dx=-1, hand=(32, 9), ang=-145, footB=(OX + 9, 38), footF=(FF[0] + 2, 39), flow=0.6, flutter=8,
              aura=2, fx=[("glint", "tip")]), 200),
        # the great descending slash
        (dict(dx=3, dy=1, hand=(41, 21), ang=8, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.7, flutter=9, aura=1,
              fx=[("arc", (31, 19), -145, 8, dict(sq=1.0, w=0.6)), ("speed", (18, 16), 3, 10)]), 40),
        (dict(dx=3, dy=5, head_dy=1, hand=(40, 28), ang=26, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.4, flutter=10,
              fx=[G.sw(w=0.5), ("dust", 52, 7), ("flare", (52, 37), 6)]), 50),
        # follow-through: crouched low over the blade, the crescent lingering above
        (dict(dx=3, dy=5, head_dy=1, hand=(40, 28), ang=30, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.8, flutter=11,
              fx=[("dust", 52, 4)]), 300),
        (dict(dx=2, dy=3, hand=(38, 27), ang=18, footF=(FF[0] + 3, 39), flow=0.5, flutter=12), 200),
        (dict(dx=1, dy=1, hand=(35, 26), ang=-30, flow=0.3, flutter=13), 175),
    ]
    return G.mseq(fr, grip=3.0)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    E = []

    def add(tag, fn, total, settle=True, **meta):
        SPEC[tag] = total
        E.append((tag, g.settled(fn) if settle else fn, meta))

    add("ls_fatal", ls_fatal, 1600)
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    mod = sys.modules.get("player_v16_fatal_blade")
    for t in [e[0] for e in mod.register(GP)]:
        ms = [m for _, m in fns[t]()]
        print(f"{t:12} frames {len(ms):3}  total {sum(ms):5}  spec {mod.SPEC.get(t)}  {'OK' if sum(ms) == mod.SPEC.get(t) else 'MISMATCH'}")
