"""v17: the Martial Arts' own weapon art, Litany of Fists (`litany`) -- docs/v17/ARTS_BRIEF.md A2, docs/v17/fist_art.md.

Same register(G) contract as player_v15_fist.py (whose rig it reuses: fseq / tm / ow and the two stances SW / IR, so
both fists read and the kicking leg is the real IK leg). Two tags, one per style; web/src/81_art_fist.js picks the tag
from the style at the start of the art and drives the frames itself (the flurry loops its four strike frames once per
blow, the knee waits for the hop, the Iron palm holds its extension while the wave runs):

  art_litany        SWIFT  0 the litany: palms pressed together at the chest, head bowed
                           1 (charge hold) the prayer held, a pale glint between the palms
                           2-5 the flurry: far palm high, near knuckle mid, far knuckle low, near palm high (looped)
                           6 the clinch: both hands haul down, the weight sinks onto the back foot
                           7 the rising knee (airborne), 8 the float down, 9 landed, guard up
  art_litany_iron   IRON   0 rooted: the near palm draws back to the hip, the far hand raised upright before the face
                           1 (charge hold) the coil: deeper, the knuckles take the heat
                           2 the bell-breaker: one long planted step, the near palm driven out at the chest, the far
                             hand pulled to the hip, the shock opening off the palm
                           3 held through the wave, 4 drawing back, 5 the iron guard
Release frame (meta active[0]) = 2 for both; the charge holds frame 1.
"""
G = None   # gen_player, set by register()
F = None   # player_v15_fist (the rig)


def register(g):
    global G, F
    G = g
    import player_v15_fist as _f   # already registered by gen_player's v15 loop: its SW / IR stances are set
    F = _f
    OX = G.OX
    SW, IR, ow, fseq = F.SW, F.IR, F.ow, F.fseq
    SWIFT, IRON = F.SWIFT, F.IRON
    PALE = ((255, 255, 255), (214, 232, 252), (120, 150, 196))     # the litany's own pale steel (prayer glint, knee)
    BELL = ((255, 240, 200), (255, 168, 80), (176, 70, 32))        # the bell-breaker's shock: ember with a hot core

    OY_K = G.OY + 20   # the knee arc's pivot (the hip)

    def P(base, **k):
        d = dict(base)
        d.update(k)
        return d

    # ------------------------------------------------------------------ SWIFT
    PRAY = dict(hand=(35, 20), ang=-92, offw=ow(37, 20, -88))      # palms pressed together, fingers up, at the sternum
    FLUR = dict(lean=1, footB=(OX + 10, 39), footF=(OX + 22, 39))

    def art_litany():
        fr = [
            # 0: the litany begins -- the guard opens and the palms meet at the chest, the head bows over them
            (P(SW, dx=0, dy=1, head_dy=1, **PRAY, footB=(OX + 9, 39), footF=(OX + 20, 39), flow=0.3), 90),
            # 1: (charge hold) the prayer held: a little lower, a pale glint where the palms meet
            (P(SW, dx=0, dy=2, head_dy=1, hand=(35, 21), ang=-92, offw=ow(37, 21, -88), footB=(OX + 8, 39), footF=(OX + 20, 39),
               flow=0.2, flutter=1, fx=[("glint", (36, 17))], fx_pal=PALE), 110),
            # 2: far palm, high (the heel of the hand at the jaw)
            (P(SW, dx=2, dy=1, hand=(34, 22), ang=-60, offw=ow(46, 19, -6), **FLUR, flow=0.9, flutter=2,
               fx=[("speed", (42, 19), 2, 9), ("flare", (50, 19), 3)], fx_pal=SWIFT), 60),
            # 3: near knuckle, mid (straight through the chest)
            (P(SW, dx=3, dy=1, hand=(46, 22), ang=-2, offw=ow(35, 21, -60), **FLUR, flow=1.0, flutter=3,
               fx=[("speed", (42, 23), 2, 10), ("flare", (50, 22), 3)], fx_pal=SWIFT), 60),
            # 4: far knuckle, low (under the ribs, the body dropping behind it)
            (P(SW, dx=3, dy=2, head_dy=1, hand=(34, 23), ang=-50, offw=ow(45, 26, 12), **FLUR, flow=1.1, flutter=4,
               fx=[("speed", (41, 27), 2, 9), ("flare", (49, 27), 3)], fx_pal=SWIFT), 60),
            # 5: near palm, high (rising back up onto the toes)
            (P(SW, dx=3, dy=0, hand=(46, 18), ang=-10, offw=ow(35, 22, -60), **FLUR, flow=1.2, flutter=5,
               fx=[("speed", (42, 19), 2, 10), ("flare", (50, 18), 3)], fx_pal=SWIFT), 60),
            # 6: the clinch: both hands haul the head down, the weight rocks back onto the rear foot
            (P(SW, dx=3, dy=2, lean=-1, hand=(40, 25), ang=50, offw=ow(41, 24, 45), footB=(OX + 10, 39), footF=(OX + 21, 39),
               flow=0.7, flutter=6), 80),
            # 7: the rising knee: off the ground, the front knee driven up through the chin, the hands still pulling
            (P(SW, dx=4, dy=-4, lean=-1, hand=(42, 20), ang=80, offw=ow(43, 21, 80), kF=dict(foot=(OX + 19, 31), toe=100, seg=5.6),
               footB=(OX + 12, 34), air=True, flow=1.4, flutter=7,
               fx=[("ring", (OX + 15, OY_K), 10, 85, -40, dict(sq=1.0, w=2.6)), ("flare", (OX + 26, 18), 4), ("vspeed", (OX + 22, 35), 2, 7)],
               fx_pal=PALE), 90),
            # 8: floating down, guard back up, the knee folding
            (P(SW, dx=3, dy=-2, hand=(36, 21), ang=-45, offw=ow(38, 21, -40), footB=(OX + 11, 36), footF=(OX + 20, 36), air=True,
               flow=1.0, flutter=8), 110),
            # 9: landed, light on the toes again
            (P(SW, dx=1, dy=1, footB=(OX + 9, 39), footF=(OX + 20, 39), flow=0.5, flutter=9), 140),
        ]
        return fseq(fr)

    # ------------------------------------------------------------------ IRON
    def art_litany_iron():
        fr = [
            # 0: rooted: sink into the stance, the near palm draws back to the hip, the far hand rises upright before the face
            (P(IR, dx=-1, dy=4, hand=(26, 30), ang=180, offw=ow(37, 17, -92), footB=(OX + 3, 39), footF=(OX + 22, 39), flow=0.3), 150),
            # 1: (charge hold) the coil: lower still, the head down behind the raised hand, the knuckles at the hip heating
            (P(IR, dx=-2, dy=5, head_dy=1, hand=(25, 31), ang=180, offw=ow(36, 17, -92), footB=(OX + 2, 39), footF=(OX + 21, 39),
               flow=0.3, flutter=1, fx=[("flare", (23, 31), 3), ("glint", (36, 13))], fx_pal=IRON), 170),
            # 2: the bell-breaker: one long planted step, the hip snaps round, the near palm driven out flat at the chest;
            #    the far hand pulls back to the hip; the shock opens off the palm and the floor kicks up under the front foot
            (P(IR, dx=4, dy=3, lean=2, hand=(48, 24), ang=-4, offw=ow(30, 28, -100, False), footB=(OX + 7, 39), footF=(OX + 27, 39),
               flow=1.6, flutter=2,
               fx=[("speed", (44, 25), 3, 14), ("flare", (52, 24), 6), ("rings", (51, 25), (4, 8)), ("dust", 44, 4)], fx_pal=BELL), 70),
            # 3: held through the wave: the palm stays out, the rings open wider and fade
            (P(IR, dx=4, dy=3, lean=2, hand=(47, 24), ang=-4, offw=ow(30, 28, -100, False), footB=(OX + 7, 39), footF=(OX + 27, 39),
               flow=1.1, flutter=3, fx=[("rings", (53, 25), (9,)), ("dust", 50, 3)], fx_pal=BELL), 220),
            # 4: drawing the palm back, the weight settling over the planted foot
            (P(IR, dx=3, dy=3, lean=1, hand=(38, 27), ang=-30, offw=ow(33, 26, -90, False), footB=(OX + 6, 39), footF=(OX + 26, 39),
               flow=0.6, flutter=4), 150),
            # 5: the iron guard
            (P(IR, dx=2, flow=0.4, flutter=5, footB=(OX + 5, 39), footF=(OX + 25, 39)), 130),
        ]
        return fseq(fr)

    K = ("penitent_knuckles",)
    return [
        ("art_litany", art_litany, dict(active=(2, 7), kinds=K, hit=[4, -32, 28, -6], fxat=(20, -19))),
        ("art_litany_iron", art_litany_iron, dict(active=(2, 3), kinds=K, hit=[4, -30, 32, -6], fxat=(24, -16))),
    ]
