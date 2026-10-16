"""v17 weapon art for the Close-range Bow: Ashen Volley (art_ashen_volley) -- docs/v17/ARTS_BRIEF.md A1, docs/v17/bow_art.md.

Same register(G) contract as player_v15_bow.py (whose bow, draw state and pull arm it reuses: bseq / AIM / LOOSE).
Kick off the foe, back-flip, and at the top of the flip -- lying back in the air, feet toward the foe -- draw and loose a
fan of burning arrows down into the spot you left; finish the turn and land crouched, facing the same way.

The flip frames are posed upright and then turned whole (every layer, the bow overlay included) with G.xform_frame, a
lossless nearest-neighbour turn about the body's middle; the arrowhead keeps its two marker colours, so the engine's
bwTip() still finds it in the turned frames. The bow's aim in the turned shot frames is posed so that, once turned, the
arrow points down and forward (AIM_SCREEN degrees below the horizon).

Frames (the engine, web/src/81_art_bow.js, drives them through ART_SYNC from P.g2):
  0  coil       a low crouch, an arrow nocked; the charge hold (hold O) stays here           wind
  1  kick       a snap kick off the foe, leaning back (release frame = the meta "active")    80 ms
  2  launch     turned 35 deg, pushing off, the string hand reaching for the nock            50 ms
  3  turn       turned 70 deg, tucked, drawing                                               60 ms
  4  aim        turned ROT_SHOT, full draw, the glint on the head (held until the shot)      held
  5  loose      the same turn, string loosed, flare                                          60 ms
  6  over       turned 200 deg, tucked tight, bow in                                         50 ms
  7  open       turned 300 deg, legs coming down (held while falling)                        held
  8  land       a deep landing crouch, dust                                                  90 ms
  9  recover    rising back to the bow's rest                                               130 ms
"""
import math

G = None
B = None   # player_v15_bow

ROT_SHOT = 270         # the body's turn when it shoots (deg, counter-clockwise = a back-flip facing right): belly-down, head to the foe
AIM_SCREEN = 42        # where the arrow points once turned (deg below the horizon, forward)
CENTER = (28.0, 25.0)  # the turn's centre (the body's middle, pose space before dx/dy)
ROT = {2: (90, (0, 0)), 3: (180, (0, -3)), 4: (ROT_SHOT, (0, -5)), 5: (ROT_SHOT, (0, -5)), 6: (320, (0, -2))}


def art_ashen_volley():
    OX, FF = G.OX, G.FF
    AIM, LOOSE = B.AIM, B.LOOSE
    a_up = AIM_SCREEN + ROT_SHOT - 360   # the bow's axis in the upright pose: overhead (turned head-down it points down-forward)
    tuck = dict(footB=(OX + 10, 33), footF=(OX + 18, 32), air=True)
    tight = dict(footB=(OX + 12, 31), footF=(OX + 19, 30), air=True, leg=5.0)
    ext = dict(footB=(OX + 9, 37), footF=(OX + 15, 38), air=True)
    fr = [
        # 0 coil: crouched low on the back foot, the bow low and canted, an arrow on the string
        (dict(dx=-1, dy=3, head_dy=1, hand=(36, 27), ang=-28, bwD=1.5, bwPull=True, flow=0.3,
              footB=(OX + 5, 39), footF=(FF[0] + 1, 39)), 90),
        # 1 kick: the front foot snapped out at the foe's chest, leaning back off it; the bow swung low behind for balance
        (dict(dx=-2, dy=1, head_dx=-1, hand=(33, 29), ang=-62, bwD=0.0, flow=0.7, flutter=1, leg=5.5,
              footB=(OX + 7, 39), footF=(FF[0] + 9, 27), fx=[("flare", (FF[0] + 11, 26), 3), ("dust", 22, 2)]), 80),
        # 2 launch (turned 90, lying back): knees coming up, the bow rising to the chest
        (dict(dy=-1, hand=(37, 24), ang=-20, bwD=0.0, flow=0.2, flutter=2, **tuck), 50),
        # 3 over (180, inverted): tucked, nocking
        (dict(dy=-1, **AIM(37, 21, a_up + 10, 4.0), flow=0.4, flutter=3, **tuck), 60),
        # 4 aim (270, belly-down at the top, head to the foe): full draw down into the spot you left; held until the shot
        (dict(dy=-1, head_dx=-1, **AIM(39, 18, a_up, 9.0), flow=0.25, flutter=4, **ext, fx=[("glint", "tip")]), 90),
        # 5 loose
        (dict(dy=-1, **LOOSE(40, 18, a_up, (24, 18)), flow=0.35, flutter=5, **ext,
              fx=[("streak", 12), ("flare", "tip", 4)]), 60),
        # 6 come round (320): tucked tight, the bow pulled in
        (dict(dy=-1, hand=(35, 24), ang=-50, bwD=0.0, flow=0.8, flutter=6, **tight), 50),
        # 7 open (340): the legs reach for the floor; held while falling
        (dict(dy=-1, hand=(35, 25), ang=-40, bwD=0.0, flow=0.6, flutter=7,
              footB=(OX + 8, 37), footF=(OX + 17, 38), air=True), 60),
        # 8 land: a deep crouch, the bow arm out low, dust
        (dict(dx=1, dy=4, head_dy=1, hand=(38, 28), ang=-14, bwD=0.0, flow=0.9, flutter=8,
              footB=(OX + 4, 39), footF=(FF[0] + 3, 39), fx=[("dust", 26, 4)]), 90),
        # 9 recover: rising to the bow's rest, a fresh arrow at the hip
        (dict(dy=1, hand=(36, 25), ang=-24, bwD=0.0, flow=0.4, flutter=9), 130),
    ]
    out = B.bseq(fr)
    import os
    if os.environ.get("V17_NOROT"):
        return out
    for i, (rot, off) in ROT.items():
        cels, ms = out[i]
        p = fr[i][0]
        c = (CENTER[0] + p.get("dx", 0), CENTER[1] + p.get("dy", 0))
        out[i] = (G.xform_frame(cels, rot, c, off), ms)
    return out


def register(g):
    global G, B
    G = g
    import player_v15_bow as _b
    B = _b
    if B.G is None:   # normally set when gen_player loaded the v15 modules
        B.G = g
        B._install(g)
    return [
        ("art_ashen_volley", art_ashen_volley, dict(active=(1, 1))),
    ]
