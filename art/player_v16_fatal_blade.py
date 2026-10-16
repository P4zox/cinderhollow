"""v16 fatality tags for the blade group (registered by gen_player.py after V15, same register(G) contract as v13/v14/v15).

Each fatality is ONE tag played on the fatality's own clock (web/src/79_fatality.js time-maps the tag over the
fatality's `dur`, so the frame ms below are the choreography: keep them in step with the steps in
web/src/79b_fatal_blade.js). No `active` meta: fatalities deal their damage through the framework's hit beats.

  ls_fatal   LONGSWORD "Ashen Verdict" (1600 ms): step in, plant the blade point-down and kneel over it while light
             gathers along the steel (aura 1 -> 3), wrench it up out of the floor in a rising cut (beat 1 at ~540 ms),
             hold it cocked high behind the head (the giant aura blade forms), then one huge descending slash into the
             floor (beat 2 at ~860 ms), a long low follow-through while the crescent lingers, and recover.

  kt_fatal   KATANA "Moonsever" (1500 ms): sink into the iai crouch, thumb on the guard; a blink dash THROUGH the foe with
             the draw (beat 1 at ~320 ms), land behind it in a low zanshin with the blade out, a chiburi flick, then the
             blade slid home slowly (slen shrinks as the hand nears the saya) -- CLICK at ~990 ms (beat 2): the screen-wide
             slash line splits the foe; stand sheathed while it holds and bursts.
  sx_fatal   SWITCH AXE "Grinder's Mercy" (1700 ms, from the SWORD form): drawn back level, the blade rammed in (beat 1 at
             ~285 ms), the mechanism unfolds INSIDE the foe (forms step sword -> axe, 420..660 ms), the chain grinds
             (660..1150, the body shaking, bites at ~760 / ~960 ms), the phial bursts (beat 4 at ~1150 ms), the blast throws
             the head up and the grinder folds back into the sword.
  sx_fatal_a the same from the AXE form: off the shoulder the blade jack-knifes out for the stab, the same middle, and the
             axe ends back over the shoulder. Both tags carry their own form per cel (w.sxf, player_v15_saxe.sxseq).
  scy_fatal  SCYTHE "Last Harvest" (1600 ms): the blade raised and dropped behind the foe's neck (the hook, beat 1 at
             ~290 ms), the haul, then pulled through in one full circle round the body (beat 2 at ~620 ms) to a low
             finish; rise with the blade upright while the souls stream into it, and rest.

`python3 art/player_v16_fatal_blade.py` prints the check.
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


# =================================================================================================== KATANA
SHEATHED = dict(hand=(30, 29), ang=168, off=(32, 28), sheath=True)   # hand on the hilt at the left hip (as player_v14_blade)


def kt_fatal():  # Moonsever: iai crouch -> blink dash through (draw) -> zanshin behind -> chiburi -> slow sheathe -> CLICK
    OX, FF = G.OX, G.FF
    IAI = dict(footB=(OX + 4, 39), footF=(OX + 21, 39), **SHEATHED)
    LOW = dict(footB=(OX + 5, 39), footF=(OX + 27, 39))
    fr = [
        # the iai crouch: sink, the thumb on the guard (the glint), held
        (dict(dy=3, head_dy=1, flow=0.3, **IAI), 110),
        (dict(dx=-1, dy=5, head_dy=2, flow=0.15, flutter=1, **IAI), 110),
        (dict(dx=-1, dy=5, head_dy=2, flow=0.1, flutter=2, fx=[("glint", (31, 27))], **IAI), 80),
        # the blink: stretched flat out along the floor, the draw flashing across the frame
        (dict(dx=5, dy=4, hand=(41, 27), ang=-4, off=(24, 28), footB=(OX + 2, 39), footF=(OX + 29, 39), flow=1.9, flutter=3,
              fx=[("flash", 29, 0, 63), ("speed", (20, 22), 4, 16)]), 45),
        (dict(dx=4, dy=3, hand=(41, 22), ang=-26, off=(24, 27), footB=(OX + 4, 39), footF=(OX + 28, 39), flow=1.7, flutter=4,
              fx=[("flash", 29, 8, 50), G.sw(w=0.35)]), 55),
        # zanshin: landed behind it, low and wide, the blade held out forward-low, quite still
        (dict(dx=3, dy=4, head_dy=1, hand=(42, 26), ang=8, off=(24, 27), flow=1.2, flutter=5, **LOW), 160),
        (dict(dx=3, dy=4, head_dy=1, hand=(42, 26), ang=9, off=(24, 27), flow=0.6, flutter=6, fx=[("glint", "tip")], **LOW), 100),
        # chiburi: one sharp flick down off the edge
        (dict(dx=3, dy=3, hand=(40, 30), ang=52, off=(25, 27), flow=0.7, flutter=7, fx=[G.sw(w=0.25)], **LOW), 60),
        # the slow sheathe: the back of the blade laid on the saya's mouth and slid home
        (dict(dx=2, dy=3, hand=(36, 25), ang=-176, off=(31, 27), footB=(OX + 6, 39), footF=(OX + 25, 39), flow=0.5, flutter=8), 80),
        (dict(dx=2, dy=3, hand=(34, 26), ang=-176, off=(31, 28), slen=13, footB=(OX + 6, 39), footF=(OX + 24, 39), flow=0.4,
              flutter=9), 100),
        (dict(dx=1, dy=3, hand=(32, 28), ang=-174, off=(31, 28), slen=9, footB=(OX + 6, 39), footF=(OX + 23, 39), flow=0.35,
              flutter=10), 90),
        # CLICK: home. Stand while the line holds and bursts
        (dict(dx=1, dy=2, flow=0.3, flutter=11, fx=[("glint", (32, 30))], footB=(OX + 6, 39), footF=(OX + 23, 39), **SHEATHED), 210),
        (dict(dy=1, flow=0.3, flutter=12, footF=(OX + 21, 39), **SHEATHED), 300),
    ]
    return G.mseq(fr, grip=G.GRIP_KATANA)


# =================================================================================================== SWITCH AXE
def _sx():
    import player_v15_saxe as SX   # registered by gen_player (its G set); the form machinery lives there
    return SX


def _sx_frames(start_axe):
    SX = _sx()
    OX, FF = G.OX, G.FF
    S, A, GS, GA = SX.SWORD, SX.AXE, SX.GRIP_S, SX.GRIP_A
    X = dict
    LUNGE = dict(footB=(OX + 9, 39), footF=(OX + 26, 39))
    if not start_axe:   # drawn back level at the hip, the phial lit
        pre = [(X(dx=-1, dy=2, hand=(30, 26), ang=-10, footB=(OX + 6, 39), flow=0.3, sxf=S, grip=GS), 100),
               (X(dx=-3, dy=3, head_dx=-1, hand=(26, 26), ang=-4, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                  sxf=S, grip=GS, fx=[("glint", "tip"), ("flare", (31, 26), 3)]), 180)]
    else:               # off the shoulder, swung down level -- the blade jack-knifes out of the haft for the stab
        pre = [(SX._carry(flow=0.3, sxf=A, grip=GA, ph=0), 90),
               (X(dx=-1, dy=2, hand=(29, 26), ang=-6, footB=(OX + 5, 39), flow=0.4, flutter=1, sxf=(1.0, 0.6), grip=GA,
                  fx=[("glint", (40, 25))]), 100),
               (X(dx=-3, dy=3, head_dx=-1, hand=(26, 26), ang=-4, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=2,
                  sxf=S, grip=GS, fx=[("glint", "tip"), ("flare", (31, 26), 3)]), 90)]
    mid = [
        # THE STAB: rammed in to the hilt
        (X(dx=4, dy=2, hand=(43, 24), ang=-3, flow=1.6, flutter=3, sxf=S, grip=GS, fx=[("streak", 18), ("flare", "tip", 7)], **LUNGE), 45),
        (X(dx=4, dy=2, hand=(42, 24), ang=-3, flow=1.0, flutter=4, sxf=S, grip=GS, fx=[("flare", "tip", 3)], **LUNGE), 95),
        # the unfold inside: unlatch, the blade swings back round its pin, the head rides up the haft, LOCK
        (X(dx=4, dy=3, hand=(41, 25), ang=-2, flow=0.8, flutter=5, sxf=(0.0, 0.3), grip=GS, **LUNGE), 60),
        (X(dx=4, dy=3, hand=(41, 25), ang=-4, flow=0.7, flutter=6, sxf=(0.15, 0.68), grip=4.2, **LUNGE), 60),
        (X(dx=3, dy=3, hand=(40, 25), ang=-3, flow=0.7, flutter=7, sxf=(0.65, 0.95), grip=GA, **LUNGE), 60),
        (X(dx=3, dy=2, hand=(40, 24), ang=-5, flow=1.0, flutter=8, sxf=A, ph=1, grip=GA, fx=[("flare", "tip", 6)], **LUNGE), 60),
    ]
    # the grind: leaning into it, the body shaking, the chain crawling, sparks pouring off the head
    for k in range(7):
        j = k % 2
        mid.append((X(dx=3 + j, dy=2 + j, hand=(40 + j, 25 - j), ang=-4 - 3 * j, flow=0.9 + 0.3 * j, flutter=9 + k, sxf=A,
                      ph=2 + k * 2, grip=GA, fx=[("flare", "tip", 4 + 2 * j), ("embers", (56, 23), 5, 3 + k * 9)], **LUNGE), 70))
    # PHIAL BURST, the blast throws the head up out of the wound
    mid += [(X(dx=4, dy=2, hand=(42, 23), ang=-12, flow=1.8, flutter=16, sxf=A, ph=17, grip=GA,
               fx=[("flare", "tip", 11), ("rings", (54, 24), (5, 9))], **LUNGE), 50),
            (X(dx=1, dy=2, head_dx=-1, hand=(37, 18), ang=-58, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=1.4, flutter=17,
               sxf=A, ph=18, grip=GA, fx=[G.sw(w=0.4), ("embers", (46, 14), 6, 5)]), 100)]
    if not start_axe:   # folds back into the sword
        post = [(X(dx=1, dy=1, hand=(37, 22), ang=-62, footF=(FF[0] + 2, 39), flow=0.8, flutter=18, sxf=(1.0, 0.6), grip=GA,
                   fx=[("embers", (44, 16), 5, 9)]), 120),
                (X(dx=1, dy=1, hand=(36, 24), ang=-56, flow=0.5, flutter=19, sxf=(0.4, 0.2), grip=GS), 140),
                (X(hand=(35, 26), ang=-50, flow=0.3, flutter=20, sxf=S, grip=GS, fx=[("glint", (40, 18))]), 140)]
    else:               # hoisted back onto the shoulder, the chain still ticking
        post = [(X(dx=1, dy=1, hand=(35, 18), ang=-100, footF=(FF[0] + 2, 39), flow=0.7, flutter=18, sxf=A, ph=19, grip=GA), 150),
                (SX._carry(flow=0.3, flutter=19, sxf=A, ph=20, grip=GA, footB=(OX + 7, 39), footF=(FF[0] + 1, 39)), 250)]
    return SX.sxseq(pre + mid + post, grip=GS)


def sx_fatal():  # Grinder's Mercy from the sword form (ends a sword)
    return _sx_frames(False)


def sx_fatal_a():  # Grinder's Mercy from the axe form (ends an axe, on the shoulder)
    return _sx_frames(True)


# =================================================================================================== SCYTHE
P_SOUL = ((246, 238, 255), (188, 150, 255), (96, 64, 176))
GHOST = ((236, 244, 255), (176, 160, 255), (110, 84, 200))


def _ring(c, r, a0, a1, sq=0.35, w=7.0, pal=None):
    o = dict(sq=sq, w=w)
    if pal:
        o["pal"] = pal
    return ("ring", c, r, a0, a1, o)


def scy_fatal():  # Last Harvest: raise -> hook behind the neck -> haul -> one full circle -> low finish -> harvest -> rest
    OX, FF = G.OX, G.FF
    BITE = dict(footB=(OX + 7, 39), footF=(FF[0] + 4, 39))
    fr = [
        # raised and reached up over the foe
        (dict(dy=1, hand=(33, 20), ang=-82, flow=0.3), 120),
        (dict(dx=1, dy=-1, hand=(37, 13), ang=-52, footB=(OX + 9, 38), flow=0.6, flutter=1, fx=[("glint", "tip")]), 120),
        # THE HOOK: dropped behind the neck
        (dict(dx=3, dy=1, hand=(41, 19), ang=-12, footF=(FF[0] + 3, 39), flow=1.1, flutter=2, fx=[G.sw(w=0.4)]), 60),
        # set, then the haul: leaning back on the haft
        (dict(dx=1, dy=2, head_dx=-1, hand=(39, 21), ang=-8, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.5, flutter=3,
              fx=[("flare", "tip", 3, P_SOUL)]), 120),
        (dict(dx=-1, dy=2, head_dx=-1, hand=(35, 22), ang=-6, footB=(OX + 4, 39), footF=(FF[0] + 2, 39), flow=0.3, flutter=4,
              fx=[("glint", "tip")]), 140),
        # the full circle: pulled through low, round behind, over the top and down in front
        (dict(dx=1, dy=3, hand=(38, 27), ang=22, footF=(FF[0] + 3, 39), flow=1.4, flutter=5,
              fx=[_ring((29, 26), 30, -10, 22, sq=0.7, w=10, pal=P_SOUL)]), 45),
        (dict(dx=1, dy=2, hand=(37, 25), ang=-6, flow=1.6, flutter=6, mirror=True,
              fx=[_ring((29, 25), 30, -80, -6, sq=0.7, w=10, pal=P_SOUL)]), 50),
        (dict(dy=-1, hand=(33, 13), ang=-100, flow=1.5, flutter=7, fx=[_ring((28, 22), 27, 30, -100, sq=0.9, w=8, pal=P_SOUL)]), 45),
        (dict(dx=3, dy=2, hand=(39, 21), ang=-14, footF=(FF[0] + 3, 39), flow=1.5, flutter=8,
              fx=[_ring((29, 24), 30, -172, -14, sq=0.9, w=10, pal=P_SOUL), ("flare", "tip", 6, P_SOUL)]), 60),
        # low finish, the blade trailing down past the foe
        (dict(dx=3, dy=4, head_dy=1, hand=(39, 27), ang=30, flow=1.0, flutter=9,
              fx=[_ring((29, 26), 30, -60, 30, sq=0.6, w=6, pal=P_SOUL), ("dust", 55, 4)], **BITE), 90),
        (dict(dx=3, dy=5, head_dy=1, hand=(38, 28), ang=34, flow=0.5, flutter=10, **BITE), 110),
        # the harvest: risen, the blade held upright while the souls stream into it
        (dict(dx=1, dy=1, hand=(34, 16), ang=-92, flow=0.4, flutter=11, aura=1, aura_pal=P_SOUL), 160),
        (dict(dy=0, hand=(33, 13), ang=-96, flow=0.3, flutter=12, aura=2, aura_pal=P_SOUL,
              fx=[("wisps", (24, 39), (40, 39), 3, 6, GHOST)]), 150),
        (dict(dy=0, hand=(33, 13), ang=-96, flow=0.3, flutter=13, aura=3, aura_pal=P_SOUL, fx=[("glint", "tip")]), 150),
        # rest
        (dict(dy=1, hand=(34, 22), ang=-70, flow=0.3, flutter=14, aura=1, aura_pal=P_SOUL), 100),
        (dict(hand=(34, 26), ang=-40, flow=0.3, flutter=15), 80),
    ]
    return G.mseq(fr, grip=G.GRIP_SCYTHE)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    E = []

    def add(tag, fn, total, settle=True, **meta):
        SPEC[tag] = total
        E.append((tag, g.settled(fn) if settle else fn, meta))

    add("ls_fatal", ls_fatal, 1600)
    add("kt_fatal", kt_fatal, 1500, settle=False)
    add("sx_fatal", sx_fatal, 1700, settle=False)
    add("sx_fatal_a", sx_fatal_a, 1700, settle=False)
    add("scy_fatal", scy_fatal, 1600, settle=False)
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
