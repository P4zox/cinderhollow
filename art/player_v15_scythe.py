"""v15 tags for the Scythe (type `scythe`, prefix scy_, weapon requiem_scythe) -- docs/WEAPON_REVAMP.md C4, docs/v15/scythe.md.

New tag names (scy_*): the v9 sc_1 sc_2 sc_3 sc_heavy sc_up sc_air sc_down tags stay as they were (fallbacks only).
Every attack is timed to its move row in web/src/78_mech_scythe.js (tm(): the frames before the hit index last `wind` ms,
the rest `total - wind`) and reads anticipation -> smear -> impact -> follow-through -> settle. The look: a long, low,
sleek reaper -- the blade drawn far back before each cut, long flat crescents (the "ring" smear round a pivot, squashed
for the flat sweeps, round for the overhead moons), long follow-throughs with the blade trailing, the soul palette only
on the soul-fed moves (Reap, charged crescent, backstab).

  scy_1        J             low reap: coil back low, a flat crescent at shin height                160 / 380
  scy_2        J J           high reap: blade cocked over the shoulder, a flat crescent at neck height 160 / 380
  scy_3        J J J         turning harvest: crescent ahead, a turn, the same crescent behind         200 / 540 (2)
  scy_4        J J J J       harvest moon: the blade hoisted high, one round moon over the top          280 / 680
  scy_pend     J J (pause) J pendulum: out ahead under the hands, then back behind                  180 / 560 (2)
  scy_hook     J K           hook pull: thrown out to full reach, the hook bites, haul it home         200 / 560
  scy_spiral   J J K         scything spiral: three turns of the blade, rising                         220 / 700 (3)
  scy_heavy    K             wide crescent: wound far back, one huge flat arc round both sides         280 / 680
  scy_twin     K K           twin crescent: a rising moon over the top, then a flat crescent           260 / 760 (2)
  scy_charge   hold K        the charge (loop): coiled low, the blade far behind, a cold gleam
  scy_charged  release       charged crescent: the wide crescent in soul-light                          240 / 720
  scy_reap     hold K souls  Reap: souls rise round the feet, hoisted high, a great spinning moon      320 / 900
  scy_up       up J          rising harvest: from the floor ahead, swept up over the head              180 / 460
  scy_rollj    L -> J        ghost slash: low out of the roll, a long thin crescent                    140 / 420
  scy_rollk    L -> K        leg sweep: crouched turn at the ankles, both sides                        200 / 560
  scy_hstep    I             hook step: blade flung out round the foe, tucked swing over, land behind  120 / 380
  scy_backstab I -> J        backstab reap: from the raised blade, a reaping moon down its back        120 / 480
  scy_air      air J         air arc: a full circle round the body                                     150 / 380
  scy_dive     air J J       crescent dive: hang, then dive at a slant behind the falling blade        150 / 480
  scy_down     air down J    grave pogo: the blade hooked under the feet                               100 / 300
  scy_plunge   air K         the shared plunge's fall: blade flipped point-down under the boots
"""

G = None   # gen_player, set by register()

P_SOUL = ((246, 238, 255), (188, 150, 255), (96, 64, 176))
GHOST = ((236, 244, 255), (176, 160, 255), (110, 84, 200))


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


def ring(c, r, a0, a1, sq=0.35, w=7.0, pal=None):
    o = dict(sq=sq, w=w)
    if pal:
        o["pal"] = pal
    return ("ring", c, r, a0, a1, o)


def S(fr, wind, total, hit, **k):
    return G.mseq(tm(fr, wind, total, hit), grip=G.GRIP_SCYTHE, **k)


# ============================================================================================================ J chain
def scy_1():  # low reap: coil back low, then one flat crescent skimming at shin height; the blade trails on, hooked
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=2, hand=(29, 27), ang=158, footB=(OX + 6, 39), flow=0.3), 70),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 28), ang=172, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 90),
          (dict(dx=2, dy=3, hand=(38, 29), ang=4, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=1.2, flutter=2,
                fx=[ring((30, 28), 27, 182, 4, sq=0.32, w=11), ("speed", (30, 24), 2, 8)]), 45),
          (dict(dx=3, dy=3, hand=(40, 28), ang=14, footB=(OX + 7, 39), footF=(FF[0] + 3, 39), flow=1.1, flutter=3,
                fx=[ring((30, 28), 27, 110, 14, sq=0.32, w=7), ("dust", 52, 2)]), 55),
          (dict(dx=2, dy=2, hand=(38, 26), ang=-18, footF=(FF[0] + 2, 39), flow=0.6, flutter=4), 90),
          (dict(dx=1, dy=1, hand=(35, 26), ang=-38, flow=0.3, flutter=5), 90)]
    return S(fr, 160, 360, 2)


def scy_2():  # high reap: the blade cocked high over the back shoulder, a flat crescent at neck height, the hook dropping
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, hand=(30, 18), ang=-122, flow=0.3), 60),
          (dict(dx=-2, dy=-1, head_dx=-1, hand=(27, 16), ang=-158, footB=(OX + 5, 39), flow=0.2, flutter=1, fx=[("glint", "tip")]), 90),
          (dict(dx=2, hand=(38, 19), ang=-14, footF=(FF[0] + 2, 39), flow=1.2, flutter=2,
                fx=[ring((29, 20), 26, 196, -14, sq=0.36, w=10), ("speed", (28, 14), 2, 8)]), 45),
          (dict(dx=2, dy=1, hand=(40, 22), ang=10, footF=(FF[0] + 2, 39), flow=1.0, flutter=3,
                fx=[ring((29, 20), 26, 120, 10, sq=0.34, w=5)]), 55),
          (dict(dx=1, dy=1, hand=(37, 25), ang=32, footF=(FF[0] + 1, 39), flow=0.6, flutter=4), 90),
          (dict(hand=(35, 26), ang=-24, flow=0.3, flutter=5), 80)]
    return S(fr, 160, 360, 2)


def scy_3():  # turning harvest: crescent ahead, the body turns with the blade, the same crescent behind
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 6, 39), footF=(FF[0] + 2, 39))
    fr = [(dict(dx=-1, dy=2, hand=(29, 27), ang=176, footB=(OX + 5, 39), flow=0.3), 80),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=-176, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 120),
          (dict(dx=1, dy=2, hand=(37, 27), ang=4, flow=1.3, flutter=2, fx=[ring((29, 28), 27, 182, 4, sq=0.34, w=11)], **low), 45),
          (dict(dx=1, dy=1, hand=(33, 17), ang=-96, flow=1.3, flutter=3, mirror=True,
                fx=[ring((28, 22), 22, 40, -96, sq=0.8, w=4)]), 55),
          (dict(dx=1, dy=2, hand=(37, 27), ang=4, flow=1.5, flutter=4, mirror=True, fx=[ring((29, 28), 27, 182, 4, sq=0.34, w=11)], **low), 45),
          (dict(dx=2, dy=2, hand=(39, 28), ang=14, flow=1.2, flutter=5, mirror=True, fx=[ring((29, 28), 27, 110, 14, sq=0.34, w=7)], **low), 60),
          (dict(dx=1, dy=1, hand=(36, 27), ang=-12, flow=0.6, flutter=6), 110),
          (dict(hand=(34, 26), ang=-34, flow=0.3, flutter=7), 90)]
    return S(fr, 200, 540, 2)


def scy_4():  # harvest moon: hoist the blade high behind, hold, then one round moon over the top that bites the floor
    OX, FF = G.OX, G.FF
    bite = dict(footB=(OX + 7, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dy=1, hand=(31, 20), ang=-110, flow=0.3), 80),
          (dict(dx=-1, dy=-1, hand=(29, 14), ang=-150, footB=(OX + 6, 39), flow=0.3, flutter=1), 110),
          (dict(dx=-2, dy=-1, head_dx=-1, hand=(27, 13), ang=-174, footB=(OX + 5, 39), flow=0.2, flutter=2, fx=[("glint", "tip")]), 120),
          (dict(dx=1, dy=-1, hand=(32, 12), ang=-96, flow=0.8, flutter=3, fx=[G.sw(w=0.4)]), 40),
          (dict(dx=3, dy=2, hand=(39, 19), ang=-20, footF=(FF[0] + 3, 39), flow=1.2, flutter=4,
                fx=[ring((29, 24), 28, -168, -20, sq=0.95, w=9)]), 45),
          (dict(dx=3, dy=4, head_dy=1, hand=(39, 26), ang=30, flow=1.3, flutter=5,
                fx=[ring((29, 24), 28, -96, 34, sq=0.95, w=8), ("dust", 55, 5)], **bite), 50),
          (dict(dx=3, dy=5, head_dy=1, hand=(38, 27), ang=34, flow=0.6, flutter=6, fx=[("dust", 56, 2)], **bite), 200),
          (dict(dx=1, dy=2, hand=(35, 27), ang=-10, flow=0.3, flutter=7), 140)]
    return S(fr, 280, 680, 4)


def scy_pend():  # pendulum: the blade swung out ahead under the hands, hung a beat, then back through behind you
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=1, hand=(31, 25), ang=148, flow=0.3), 70),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(30, 26), ang=160, footB=(OX + 5, 39), flow=0.2, flutter=1, fx=[("glint", "tip")]), 90),
          (dict(dx=2, dy=2, hand=(38, 24), ang=18, footF=(FF[0] + 3, 39), flow=1.2, flutter=2,
                fx=[ring((33, 25), 22, 150, 18, sq=0.85, w=6)]), 45),
          (dict(dx=2, dy=1, hand=(39, 21), ang=-12, footF=(FF[0] + 3, 39), flow=1.0, flutter=3), 90),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(28, 26), ang=166, footB=(OX + 5, 39), flow=1.3, flutter=4,
                fx=[ring((33, 25), 22, 20, 166, sq=0.85, w=6)]), 45),
          (dict(dx=-1, dy=2, hand=(27, 23), ang=-168, footB=(OX + 5, 39), flow=1.0, flutter=5,
                fx=[ring((33, 25), 22, 100, 192, sq=0.85, w=4)]), 70),
          (dict(dy=1, hand=(32, 24), ang=-60, flow=0.5, flutter=6), 110),
          (dict(hand=(34, 26), ang=-40, flow=0.3, flutter=7), 80)]
    return S(fr, 180, 560, 2)


def scy_hook():  # hook pull: flung out to full length, the hook bites, then the haul home -- set feet, lean back
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=1, hand=(33, 20), ang=-82, flow=0.3), 70),
          (dict(dx=-1, hand=(31, 16), ang=-122, footB=(OX + 6, 39), flow=0.3, flutter=1, fx=[("glint", "tip")]), 90),
          (dict(dx=3, dy=1, hand=(41, 22), ang=-4, footF=(FF[0] + 3, 39), flow=1.1, flutter=2, fx=[G.sw(w=0.5)]), 45),
          (dict(dx=3, dy=2, hand=(41, 24), ang=8, footF=(FF[0] + 3, 39), flow=0.9, flutter=3, fx=[("flare", "tip", 4)]), 60),
          (dict(dx=-2, dy=2, head_dx=-1, hand=(32, 25), ang=4, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.4, flutter=4,
                fx=[("speed", (54, 24), 3, 12)]), 90),
          (dict(dx=-2, dy=2, hand=(30, 26), ang=12, footB=(OX + 4, 39), flow=0.3, flutter=5), 100),
          (dict(dx=-1, dy=1, hand=(33, 26), ang=-30, flow=0.3, flutter=6), 90)]
    return S(fr, 200, 560, 2)


def scy_spiral():  # scything spiral: three turns of the blade round the body, each a little higher
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=2, hand=(29, 24), ang=-162, flow=0.3), 80),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 27), ang=178, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 110),
          (dict(dx=1, dy=2, hand=(37, 27), ang=-2, footF=(FF[0] + 2, 39), flow=1.3, flutter=2, fx=[ring((29, 28), 27, 182, -2, sq=0.36, w=10)]), 45),
          (dict(dx=1, dy=1, hand=(37, 24), ang=-8, footF=(FF[0] + 2, 39), flow=1.5, flutter=3, mirror=True,
                fx=[ring((29, 25), 27, 182, -8, sq=0.4, w=10)]), 55),
          (dict(dx=2, hand=(38, 21), ang=-20, footF=(FF[0] + 3, 39), flow=1.5, flutter=4, fx=[ring((29, 21), 27, 190, -20, sq=0.46, w=11)]), 45),
          (dict(dx=2, dy=-1, hand=(37, 15), ang=-62, footB=(OX + 8, 38), flow=1.2, flutter=5, fx=[ring((29, 21), 27, 60, -62, sq=0.46, w=5)]), 70),
          (dict(dx=1, hand=(35, 22), ang=-48, flow=0.6, flutter=6), 130),
          (dict(hand=(34, 26), ang=-40, flow=0.3, flutter=7), 90)]
    return S(fr, 220, 700, 2)


# ============================================================================================================ K
def scy_heavy():  # wide crescent: wound far back and low, then one huge flat arc that carries round behind you
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 6, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(dx=-1, dy=2, hand=(30, 28), ang=150, flow=0.3), 90),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=176, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1), 130),
          (dict(dx=-3, dy=3, head_dx=-1, hand=(26, 24), ang=-170, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=2,
                fx=[("glint", "tip")]), 110),
          (dict(dx=2, dy=3, hand=(38, 25), ang=-6, flow=1.3, flutter=3, fx=[ring((28, 25), 31, 188, -6, sq=0.38, w=13)], **low), 45),
          (dict(dx=2, dy=3, hand=(38, 26), ang=4, flow=1.5, flutter=4, mirror=True, fx=[ring((28, 25), 31, 188, 4, sq=0.38, w=13)], **low), 55),
          (dict(dx=3, dy=3, hand=(40, 27), ang=14, flow=1.0, flutter=5, fx=[ring((28, 25), 31, 100, 14, sq=0.38, w=5), ("dust", 52, 3)], **low), 70),
          (dict(dx=2, dy=3, hand=(38, 28), ang=24, flow=0.5, flutter=6, **low), 180),
          (dict(dx=1, dy=1, hand=(34, 27), ang=-20, flow=0.3, flutter=7), 140)]
    return S(fr, 280, 680, 3)


def scy_twin():  # twin crescent: a moon rising over the top to behind you, a drop, then a flat crescent through again
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 5, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(dx=1, dy=3, hand=(37, 28), ang=30, flow=0.4), 80),
          (dict(dx=1, dy=4, head_dy=1, hand=(38, 30), ang=42, footF=(FF[0] + 3, 39), flow=0.3, flutter=1, fx=[("glint", "tip")]), 120),
          (dict(dy=-1, hand=(33, 14), ang=-100, flow=1.3, flutter=2, fx=[ring((28, 22), 26, 44, -150, sq=0.9, w=7)]), 45),
          (dict(dx=-1, dy=-1, hand=(28, 15), ang=-160, footB=(OX + 6, 39), flow=1.2, flutter=3,
                fx=[ring((28, 22), 26, -60, -172, sq=0.9, w=4)]), 70),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 27), ang=176, flow=0.4, flutter=4, **low), 100),
          (dict(dx=2, dy=3, hand=(39, 27), ang=6, flow=1.4, flutter=5, fx=[ring((29, 26), 29, 186, 6, sq=0.34, w=12)], **low), 45),
          (dict(dx=3, dy=3, hand=(40, 28), ang=16, flow=1.0, flutter=6, fx=[ring((29, 26), 29, 100, 16, sq=0.34, w=7), ("dust", 52, 3)], **low), 70),
          (dict(dx=2, dy=2, hand=(37, 28), ang=22, flow=0.5, flutter=7), 170),
          (dict(dx=1, dy=1, hand=(34, 27), ang=-24, flow=0.3, flutter=8), 130)]
    return S(fr, 260, 760, 2)


def scy_charge():  # hold K (loop): coiled low, the blade held far behind, a cold gleam crawling up the edge
    OX, FF = G.OX, G.FF
    base = dict(dx=-3, dy=3, head_dx=-1, footB=(OX + 4, 39), footF=(FF[0] + 1, 39))
    fr = [(dict(hand=(26, 24), ang=-170, flow=0.25, flutter=0, aura=1, aura_pal=P_SOUL, **base), 110),
          (dict(hand=(26, 25), ang=-172, flow=0.35, flutter=1, aura=1, aura_pal=P_SOUL, fx=[("glint", "tip")], **base), 110),
          (dict(hand=(26, 24), ang=-170, flow=0.3, flutter=2, aura=2, aura_pal=P_SOUL, **base), 110),
          (dict(hand=(26, 25), ang=-171, flow=0.35, flutter=3, aura=1, aura_pal=P_SOUL, **base), 110)]
    return G.mseq(fr, grip=G.GRIP_SCYTHE)


def scy_charged():  # release: the wide crescent, bigger and in soul-light
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 6, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dx=-3, dy=3, head_dx=-1, hand=(26, 24), ang=-170, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.3, aura=2,
                aura_pal=P_SOUL), 120),
          (dict(dx=-1, dy=2, hand=(29, 22), ang=-128, flow=0.8, flutter=1, fx=[G.sw(w=0.4)], fx_pal=P_SOUL), 60),
          (dict(dx=3, dy=3, hand=(39, 25), ang=-4, flow=1.5, flutter=2, fx=[ring((28, 24), 33, 192, -4, sq=0.42, w=14, pal=P_SOUL),
                                                                         ("flare", "tip", 5, P_SOUL)], **low), 45),
          (dict(dx=3, dy=3, hand=(39, 26), ang=4, flow=1.6, flutter=3, mirror=True, fx=[ring((28, 24), 33, 192, 4, sq=0.42, w=14, pal=P_SOUL)],
                **low), 55),
          (dict(dx=3, dy=3, hand=(40, 27), ang=16, flow=1.1, flutter=4, fx=[ring((28, 24), 33, 100, 16, sq=0.42, w=5, pal=P_SOUL),
                                                                          ("dust", 54, 4)], **low), 70),
          (dict(dx=2, dy=3, hand=(38, 28), ang=24, flow=0.5, flutter=5, **low), 200),
          (dict(dx=1, dy=1, hand=(34, 27), ang=-20, flow=0.3, flutter=6), 130)]
    return S(fr, 240, 720, 2)


def scy_reap():  # Reap: the souls rise round the feet as the blade is hoisted, then one great moon spun round both sides
    OX, FF = G.OX, G.FF
    bite = dict(footB=(OX + 7, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dy=1, hand=(31, 19), ang=-110, flow=0.3, aura=1, aura_pal=P_SOUL, fx=[("wisps", (26, 39), (34, 39), 2, 1, GHOST)]), 90),
          (dict(dx=-1, dy=-1, hand=(30, 13), ang=-150, footB=(OX + 6, 39), flow=0.4, flutter=1, aura=2, aura_pal=P_SOUL,
                fx=[("wisps", (22, 39), (38, 39), 3, 2, GHOST)]), 120),
          (dict(dx=-2, dy=-1, head_dx=-1, hand=(28, 12), ang=-170, footB=(OX + 5, 39), flow=0.3, flutter=2, aura=2, aura_pal=P_SOUL,
                fx=[("glint", "tip"), ("wisps", (20, 39), (40, 39), 4, 3, GHOST)]), 110),
          (dict(dx=1, hand=(33, 12), ang=-95, flow=0.9, flutter=3, fx=[G.sw(w=0.5)], fx_pal=P_SOUL), 40),
          (dict(dx=3, dy=2, hand=(39, 21), ang=-14, footF=(FF[0] + 3, 39), flow=1.4, flutter=4,
                fx=[ring((29, 25), 31, -172, -14, sq=0.7, w=10, pal=P_SOUL), ("flare", "tip", 6, P_SOUL)]), 45),
          (dict(dx=3, dy=3, hand=(39, 25), ang=10, flow=1.6, flutter=5, mirror=True,
                fx=[ring((29, 26), 31, -110, 10, sq=0.55, w=10, pal=P_SOUL)], **bite), 50),
          (dict(dx=3, dy=4, head_dy=1, hand=(39, 27), ang=30, flow=1.2, flutter=6,
                fx=[ring((29, 27), 31, -40, 30, sq=0.45, w=7, pal=P_SOUL), ("dust", 54, 6), ("wisps", (42, 39), (60, 39), 4, 4, GHOST)], **bite), 55),
          (dict(dx=3, dy=5, head_dy=1, hand=(38, 28), ang=34, flow=0.6, flutter=7, fx=[("wisps", (46, 39), (58, 39), 2, 5, GHOST)], **bite), 230),
          (dict(dx=1, dy=2, hand=(35, 27), ang=-10, flow=0.3, flutter=8), 160)]
    return S(fr, 320, 1000, 4)


# ============================================================================================================ up, roll, I
def scy_up():  # rising harvest: blade low on the floor ahead, swept up through the air over the head
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=3, hand=(32, 29), ang=58, footB=(OX + 6, 39), flow=0.3), 70),
          (dict(dx=-1, dy=4, head_dy=1, hand=(33, 30), ang=70, footF=(FF[0] + 1, 39), flow=0.2, flutter=1, fx=[("glint", "tip")]), 90),
          (dict(dx=1, dy=-1, hand=(35, 14), ang=-80, flow=1.3, flutter=2, fx=[ring((28, 22), 25, 54, -80, sq=0.9, w=7)]), 45),
          (dict(dy=-2, hand=(33, 11), ang=-112, footB=(OX + 9, 38), flow=1.2, flutter=3, fx=[ring((28, 22), 25, -20, -122, sq=0.9, w=5)]), 55),
          (dict(dy=-1, hand=(32, 13), ang=-132, flow=0.7, flutter=4), 110),
          (dict(hand=(34, 25), ang=-46, flow=0.3, flutter=5), 90)]
    return S(fr, 180, 460, 2)


def scy_rollj():  # ghost slash: low out of the roll, the blade drawn through in one long, thin crescent
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=4, head_dy=1, hand=(29, 30), ang=170, footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.6), 60),
          (dict(dy=4, head_dy=1, hand=(30, 28), ang=-170, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.8, flutter=1, fx=[("glint", "tip")]), 80),
          (dict(dx=3, dy=3, hand=(40, 26), ang=-2, footB=(OX + 7, 39), footF=(FF[0] + 5, 39), flow=1.6, flutter=2,
                fx=[ring((30, 27), 31, 194, -2, sq=0.25, w=9), ("speed", (28, 20), 3, 10)]), 45),
          (dict(dx=3, dy=3, hand=(41, 27), ang=8, footB=(OX + 7, 39), footF=(FF[0] + 5, 39), flow=1.2, flutter=3,
                fx=[ring((30, 27), 31, 100, 8, sq=0.22, w=4)]), 60),
          (dict(dx=2, dy=2, hand=(37, 27), ang=-14, footF=(FF[0] + 3, 39), flow=0.6, flutter=4), 110),
          (dict(dx=1, dy=1, hand=(34, 26), ang=-36, flow=0.3, flutter=5), 80)]
    return S(fr, 140, 420, 2)


def scy_rollk():  # leg sweep: sunk to a crouch, one turn of the blade at the ankles, ahead and behind
    OX, FF = G.OX, G.FF
    deep = dict(head_dy=1, footB=(OX + 3, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(dx=-1, dy=4, hand=(30, 30), ang=170, flow=0.3, **deep), 70),
          (dict(dx=-1, dy=5, hand=(28, 31), ang=178, flow=0.2, flutter=1, fx=[("glint", "tip")], **deep), 110),
          (dict(dx=1, dy=5, hand=(37, 31), ang=8, flow=1.3, flutter=2, fx=[ring((29, 28), 28, 182, 4, sq=0.22, w=10), ("dust", 48, 3)], **deep), 45),
          (dict(dx=1, dy=5, hand=(37, 31), ang=10, flow=1.5, flutter=3, mirror=True,
                fx=[ring((29, 28), 28, 182, 6, sq=0.22, w=10), ("dust", 48, 3)], **deep), 50),
          (dict(dx=1, dy=4, hand=(38, 30), ang=14, flow=1.1, flutter=4, fx=[ring((29, 28), 28, 100, 12, sq=0.22, w=6)], **deep), 60),
          (dict(dx=1, dy=3, hand=(36, 29), ang=-10, flow=0.5, flutter=5), 160),
          (dict(hand=(34, 26), ang=-36, flow=0.3, flutter=6), 110)]
    return S(fr, 200, 560, 2)


def scy_hstep():  # hook step: blade flung out and round the foe, a tucked swing over on the haft, land behind it, blade up
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=1, hand=(37, 18), ang=-44, flow=0.5), 60),
          (dict(dx=3, dy=-1, hand=(41, 19), ang=-8, footF=(FF[0] + 3, 39), flow=0.9, flutter=1, fx=[G.sw(w=0.4), ("glint", "tip")]), 60),
          (dict(dx=2, dy=-3, hand=(40, 18), ang=-22, flow=1.4, flutter=2, fx=[("speed", (24, 20), 3, 12)], **G.TUCK), 60),
          (dict(dx=1, dy=-4, hand=(37, 15), ang=-62, flow=1.6, flutter=3, fx=[("speed", (24, 18), 3, 10)], **G.TUCK), 60),
          (dict(dx=-1, dy=3, head_dx=-1, hand=(33, 21), ang=-110, footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=1.0, flutter=4,
                fx=[("dust", 30, 3)]), 60),
          (dict(dy=2, hand=(32, 19), ang=-122, flow=0.5, flutter=5), 80)]
    return S(fr, 120, 380, 2)


def scy_backstab():  # backstab reap: from the raised blade, a reaping moon down into the foe's back
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=2, hand=(32, 19), ang=-125, flow=0.4), 50),
          (dict(dx=-1, dy=1, hand=(30, 16), ang=-152, footB=(OX + 6, 39), flow=0.3, flutter=1, fx=[("glint", "tip")]), 70),
          (dict(dx=3, dy=3, hand=(40, 23), ang=0, footF=(FF[0] + 3, 39), flow=1.3, flutter=2,
                fx=[ring((29, 22), 26, -152, 0, sq=0.8, w=8, pal=P_SOUL)]), 40),
          (dict(dx=3, dy=4, head_dy=1, hand=(39, 27), ang=36, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.0, flutter=3,
                fx=[ring((29, 22), 26, -60, 36, sq=0.8, w=5, pal=P_SOUL), ("flare", "tip", 4, P_SOUL)]), 60),
          (dict(dx=2, dy=3, hand=(37, 28), ang=30, footF=(FF[0] + 3, 39), flow=0.5, flutter=4), 150),
          (dict(dx=1, dy=1, hand=(34, 27), ang=-14, flow=0.3, flutter=5), 110)]
    return S(fr, 120, 480, 2)


# ============================================================================================================ air
def scy_air():  # air arc: a full circle of the blade round the body
    fr = [(dict(hand=(31, 16), ang=-130, flow=0.6), 60),
          (dict(dx=-1, head_dx=-1, hand=(29, 14), ang=-160, flow=0.5, flutter=1, fx=[("glint", "tip")]), 60),
          (dict(dx=1, hand=(38, 24), ang=20, flow=1.3, flutter=2, fx=[ring((28, 22), 25, -164, 20, sq=0.7, w=7)]), 45),
          (dict(dx=1, hand=(38, 24), ang=24, flow=1.5, flutter=3, mirror=True, fx=[ring((28, 22), 25, -110, 24, sq=0.7, w=7)]), 55),
          (dict(hand=(35, 27), ang=50, flow=0.9, flutter=4), 70),
          (dict(hand=(34, 24), ang=-20, flow=0.5, flutter=5, **G.AIR), 90)]
    return G.mseq(tm(fr, 150, 380, 2), G.AIRB, grip=G.GRIP_SCYTHE)


def scy_dive():  # crescent dive: hang with the blade overhead, then dive at a slant behind it and land low
    OX, FF = G.OX, G.FF
    dive = dict(footB=(OX + 6, 34), footF=(OX + 13, 36), air=True)
    fr = [(dict(dy=-3, hand=(31, 13), ang=-120, flow=0.6, **G.TUCK), 70),
          (dict(dy=-3, head_dx=-1, hand=(29, 12), ang=-150, flow=0.4, flutter=1, fx=[("glint", "tip")], **G.TUCK), 80),
          (dict(dx=1, dy=-2, hand=(39, 27), ang=40, flow=1.4, flutter=2, fx=[ring((29, 20), 25, -150, 40, sq=0.9, w=7), ("speed", (26, 14), 3, 10)],
                **dive), 45),
          (dict(dx=1, dy=-2, hand=(39, 28), ang=44, flow=1.2, flutter=3, fx=[ring((29, 20), 25, -40, 44, sq=0.9, w=4)], **dive), 60),
          (dict(dx=2, dy=4, head_dy=1, hand=(38, 29), ang=40, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.8, flutter=4,
                fx=[("dust", 48, 5)]), 90),
          (dict(dx=1, dy=2, hand=(36, 28), ang=18, flow=0.5, flutter=5), 90),
          (dict(hand=(34, 26), ang=-34, flow=0.3, flutter=6), 70)]
    return S(fr, 150, 480, 2)


def scy_down():  # grave pogo: the blade swung down and hooked under the boots
    fr = [(dict(dy=-3, hand=(31, 15), ang=-120, flow=0.6, **G.TUCK), 50),
          (dict(dy=-3, hand=(36, 23), ang=50, flow=0.9, flutter=1, fx=[G.sw(w=0.5)], **G.TUCK), 50),
          (dict(dy=-3, hand=(35, 29), ang=92, flow=1.2, flutter=2, fx=[ring((31, 24), 18, -10, 96, sq=1.0, w=6)], **G.TUCK), 45),
          (dict(dy=-3, hand=(35, 30), ang=96, flow=1.0, flutter=3, **G.TUCK), 60),
          (dict(hand=(34, 24), ang=-30, flow=0.5, flutter=4, **G.AIR), 80)]
    return G.mseq(tm(fr, 100, 300, 2), grip=G.GRIP_SCYTHE)


def scy_plunge():  # the shared plunge's fall (plays once, then holds): the blade flipped point-down under the boots
    OX = G.OX
    stomp = dict(footB=(OX + 11, 35), footF=(OX + 16, 36), air=True)
    fr = [(dict(dy=-3, hand=(33, 14), ang=-90, flow=0.8, **G.TUCK), 60),
          (dict(dy=-3, hand=(36, 25), ang=78, flow=1.2, flutter=1, fx=[G.sw(w=0.5), ("vspeed", (26, 22), 3, 8)], **stomp), 60),
          (dict(dy=-3, hand=(35, 29), ang=92, flow=1.5, flutter=2, fx=[("vspeed", (25, 24), 3, 10), ("vspeed", (40, 20), 2, 8)], **stomp), 70),
          (dict(dy=-3, hand=(35, 29), ang=92, flow=1.6, flutter=3, fx=[("vspeed", (24, 23), 3, 11), ("vspeed", (41, 21), 2, 9)], **stomp), 70)]
    return G.mseq(fr, grip=G.GRIP_SCYTHE)


def register(g):
    global G
    G = g
    G.MOVE_CLASS["scy"] = ("requiem_scythe",)   # hit boxes of scy_* tags are measured with the Requiem
    settled = G.settled
    return [
        ("scy_1", settled(scy_1), dict(active=(2, 3), x0=-12)),
        ("scy_2", settled(scy_2), dict(active=(2, 3), x0=-12)),
        ("scy_3", settled(scy_3), dict(active=(2, 5), hits=[2, 4], both=True)),
        ("scy_4", settled(scy_4), dict(active=(4, 5))),
        ("scy_pend", settled(scy_pend), dict(active=(2, 4), hits=[2, 4], both=True)),
        ("scy_hook", settled(scy_hook), dict(active=(2, 3))),
        ("scy_spiral", settled(scy_spiral), dict(active=(2, 4), hits=[2, 3, 4], both=True)),
        ("scy_heavy", settled(scy_heavy), dict(active=(3, 4), both=True)),
        ("scy_twin", settled(scy_twin), dict(active=(2, 5), hits=[2, 5], both=True)),
        ("scy_charge", scy_charge, None),
        ("scy_charged", settled(scy_charged), dict(active=(2, 3), both=True)),
        ("scy_reap", settled(scy_reap), dict(active=(4, 5), both=True)),
        ("scy_up", settled(scy_up), dict(active=(2, 3), up=True)),
        ("scy_rollj", settled(scy_rollj), dict(active=(2, 3))),
        ("scy_rollk", settled(scy_rollk), dict(active=(2, 3), both=True)),
        ("scy_hstep", settled(scy_hstep), None),
        ("scy_backstab", settled(scy_backstab), dict(active=(2, 3))),
        ("scy_air", scy_air, dict(active=(2, 3), both=True)),
        ("scy_dive", settled(scy_dive), dict(active=(2, 3))),
        ("scy_down", scy_down, dict(active=(2, 3), down=True)),
        ("scy_plunge", scy_plunge, None),
    ]
