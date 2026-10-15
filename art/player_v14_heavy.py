"""v14 combo pass: new player tags for the heavy group -- Greatsword gs_ and Maul ml_ (registered by gen_player.py, same
contract as player_v13_a.py: register(G) returns [(tag, fn, opts)], fn() returns [(cels, ms), ...]).

Timing: each attack is authored to its row in web/src/76_mech_heavy.js -- the frames before the first active frame add up to
the move's wind-up, all frames to its total (tm() rescales a hand-timed sequence onto those two numbers). Tags that hand over
to a hold (the hilt bash -> the charge, the haft jab -> the walk-charge) end on that hold's pose and are not settled.

  python3 art/player_v14_heavy.py        # prints each tag's frames / wind / total against its spec
"""
G = None   # gen_player, set by register()
SPEC = {}
GRIP_MAUL = 4.0


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


# =================================================================================================== GREATSWORD
def _gs_hold(dy=3, **k):   # the charge's shoulder rest (as player_v13_a.gs_charge_hold)
    return dict(dx=-2, dy=dy, head_dx=-1, hand=(27, 14 + max(0, dy - 3)), ang=-150, footB=(G.OX + 5, 39),
                footF=(G.FF[0] + 2, 39), **k)


def gs_bash():  # hilt bash: the slab hauled onto the shoulder, both fists driven forward pommel-first -- and it stays there, charging
    fr = [(dict(dx=-1, dy=2, hand=(31, 18), ang=-118, footB=(G.OX + 6, 39), flow=0.3), 90),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 16), ang=-150, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.2,
                flutter=1), 100),
          (dict(dx=3, dy=2, head_dx=1, hand=(38, 18), ang=-162, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=2,
                fx=[("speed", (20, 18), 4, 12), ("flare", (43, 17), 6)]), 50),
          (dict(dx=3, dy=2, head_dx=1, hand=(37, 18), ang=-160, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.0, flutter=3,
                fx=[("flare", (42, 17), 3)]), 70),
          (dict(dx=0, dy=3, hand=(30, 15), ang=-154, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.5, flutter=4), 90),
          (dict(flow=0.3, flutter=5, **_gs_hold(3)), 90)]
    return G.mseq(tm(fr, 180, 480, 2), grip=G.GRIP_GREAT)


def gs_mcleave():  # momentum cleave: the finisher's spin never stops -- the blade wheels up over the top and comes down on the floor
    fr = [(dict(dx=1, dy=2, hand=(37, 28), ang=12, footF=(G.FF[0] + 2, 39), flow=0.9), 80),
          (dict(dx=0, dy=1, hand=(34, 22), ang=-58, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=1, fx=[G.sw(w=0.35)]), 90),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(29, 11), ang=-148, footB=(G.OX + 7, 38), footF=(G.FF[0] + 2, 39), flow=0.8,
                flutter=2, fx=[G.sw(w=0.4)]), 120),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(28, 10), ang=-166, footB=(G.OX + 7, 38), footF=(G.FF[0] + 2, 39), flow=0.4,
                flutter=3, fx=[("glint", "tip")]), 70),
          (dict(dx=2, dy=2, hand=(38, 21), ang=-16, slen=15, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=4, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=3, dy=5, head_dy=1, hand=(37, 30), ang=48, slen=16, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.4,
                flutter=5, fx=[G.sw(w=0.5), ("dust", 50, 8), ("flare", (50, 35), 7)]), 60),
          (dict(dx=3, dy=6, head_dy=1, hand=(37, 31), ang=52, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.6, flutter=6,
                fx=[("dust", 50, 4)]), 220),
          (dict(dx=1, dy=3, hand=(35, 29), ang=35, footF=(G.FF[0] + 2, 39), flow=0.3, flutter=7), 160)]
    return G.mseq(tm(fr, 360, 820, 4), grip=G.GRIP_GREAT)


def gs_retort():  # retort: the blocked blow still ringing, the blade is ripped up out of the floor in one rising diagonal
    fr = [(dict(dx=-1, dy=3, head_dx=-1, hand=(40, 18), ang=88, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.3,
                fx=[("dust", 42, 3)]), 60),
          (dict(dx=0, dy=2, hand=(39, 25), ang=58, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=1, fx=[G.sw(w=0.3), ("dust", 45, 5)]), 70),
          (dict(dx=2, dy=0, hand=(40, 22), ang=-34, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=2,
                fx=[G.sw(w=0.6), ("flare", (52, 11), 5)]), 45),
          (dict(dx=2, dy=-1, hand=(36, 14), ang=-94, footB=(G.OX + 8, 38), footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3,
                fx=[G.sw(w=0.45)]), 60),
          (dict(dx=1, dy=0, hand=(32, 12), ang=-130, footF=(G.FF[0] + 2, 39), flow=0.6, flutter=4), 170),
          (dict(dx=0, dy=1, hand=(32, 19), ang=-100, flow=0.3, flutter=5), 120)]
    return G.mseq(tm(fr, 150, 560, 2), grip=G.GRIP_GREAT)


def gs_leap():  # leaping wide slash: out of the tackle a short bound, the slab swung flat round at the height of a man's chest
    ARC = dict(sq=0.42, w=0.65)
    fr = [(dict(dx=1, dy=3, head_dx=1, hand=(28, 15), ang=-150, footB=(G.OX + 5, 39), footF=(G.FF[0] + 3, 39), flow=0.6), 80),
          (dict(dx=2, dy=-4, hand=(28, 21), ang=-176, footB=(G.OX + 9, 34), footF=(G.OX + 19, 33), air=True, flow=1.2, flutter=1), 100),
          (dict(dx=3, dy=-5, hand=(30, 25), ang=172, slen=15, footB=(G.OX + 10, 33), footF=(G.OX + 20, 33), air=True, flow=1.4,
                flutter=2, fx=[("speed", (18, 20), 4, 12)]), 80),
          (dict(dx=4, dy=-2, hand=(41, 24), ang=-2, footB=(G.OX + 10, 36), footF=(G.OX + 22, 36), air=True, flow=1.5, flutter=3,
                fx=[("arc", (30, 25), 176, -2, ARC), ("flare", (56, 22), 5)]), 50),
          (dict(dx=4, dy=2, hand=(40, 26), ang=22, footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.45), ("dust", 36, 6)]), 60),
          (dict(dx=4, dy=3, head_dy=1, hand=(38, 29), ang=32, footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=0.7, flutter=5,
                fx=[("dust", 38, 3)]), 180),
          (dict(dx=2, dy=2, hand=(36, 29), ang=30, footF=(G.OX + 22, 39), flow=0.4, flutter=6), 150)]
    return G.mseq(tm(fr, 260, 700, 3), grip=G.GRIP_GREAT)


# ---- v14c: more J / K mixes (all as slow and weighty as the 25%-slower Greatsword)
def _gs_buried(**k):   # the end of a cleave: the slab bitten into the floor in front, knees bent over it
    d = dict(dx=3, dy=6, head_dy=1, hand=(37, 31), ang=52, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39))
    d.update(k)
    return d


def gs_heave():  # upheaval (charged slash -> J): the buried blade wrenched up out of the floor, grit flying, all the way overhead
    fr = [(dict(flow=0.3, **_gs_buried()), 110),
          (dict(flow=0.2, fx=[("dust", 48, 4)], **_gs_buried(dx=1, dy=5, head_dx=-1, head_dy=0, ang=58, footB=(G.OX + 5, 39),
                                                             footF=(G.FF[0] + 3, 39))), 160),
          (dict(dx=2, dy=4, hand=(38, 29), ang=30, footF=(G.FF[0] + 3, 39), flow=0.8, flutter=1, fx=[G.sw(w=0.35), ("dust", 50, 8)]), 120),
          (dict(dx=3, dy=1, hand=(40, 22), ang=-32, footF=(G.FF[0] + 4, 39), flow=1.3, flutter=2,
                fx=[G.sw(w=0.6), ("dust", 50, 5), ("flare", (52, 12), 5)]), 50),
          (dict(dx=3, dy=-1, hand=(36, 13), ang=-92, footB=(G.OX + 9, 38), footF=(G.FF[0] + 4, 39), flow=1.3, flutter=3,
                fx=[G.sw(w=0.45)]), 60),
          (dict(dx=2, dy=0, hand=(32, 12), ang=-125, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=4), 220),
          (dict(dx=1, dy=1, hand=(32, 18), ang=-105, flow=0.4, flutter=5), 160),
          (dict(dy=1, hand=(33, 22), ang=-90, flow=0.3, flutter=6), 130)]
    return G.mseq(tm(fr, 440, 1000, 3), grip=G.GRIP_GREAT)


def gs_turn():  # turning sweep (hilt bash -> J): off the shoulder the body wheels round, the slab carried flat through a full half-circle
    ARC = dict(sq=0.42, w=0.65)
    fr = [(dict(flow=0.4, **_gs_hold(3)), 100),
          (dict(dx=-1, dy=3, head_dx=-1, hand=(26, 20), ang=-170, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.5, flutter=1), 140),
          (dict(dx=0, dy=3, hand=(30, 25), ang=176, slen=14, footF=(G.FF[0] + 2, 39), flow=0.9, flutter=2, mirror=True, behind=True,
                fx=[("speed", (22, 22), 3, 10)]), 120),
          (dict(dx=2, dy=3, hand=(40, 25), ang=-2, footF=(G.FF[0] + 3, 39), flow=1.4, flutter=3,
                fx=[("arc", (29, 26), 176, -2, ARC), ("flare", (56, 24), 5)]), 50),
          (dict(dx=3, dy=3, hand=(40, 23), ang=-30, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=4, fx=[G.sw(w=0.45)]), 60),
          (dict(dx=3, dy=3, hand=(38, 20), ang=-55, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=5), 220),
          (dict(dx=1, dy=2, hand=(35, 24), ang=-40, flow=0.3, flutter=6), 190)]
    return G.mseq(tm(fr, 420, 1000, 3), grip=G.GRIP_GREAT)


def gs_split():  # earthsplitter (momentum cleave -> K): the buried slab ploughed forward through the floor, ripped out level in a spray
    fr = [(dict(flow=0.3, **_gs_buried()), 120),
          (dict(flow=1.0, flutter=1, fx=[("dust", 52, 6), ("speed", (20, 26), 4, 10)],
                **_gs_buried(dx=4, dy=5, head_dx=1, hand=(39, 31), ang=40, footB=(G.OX + 8, 39), footF=(G.OX + 26, 39))), 170),
          (dict(flow=1.2, flutter=2, fx=[("dust", 54, 8)],
                **_gs_buried(dx=5, dy=5, head_dx=1, head_dy=0, hand=(40, 31), ang=30, footB=(G.OX + 10, 39), footF=(G.OX + 27, 39))), 160),
          (dict(dx=4, dy=3, hand=(38, 27), ang=-12, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.6, flutter=3,
                fx=[G.sw(w=0.65), ("dust", 56, 12), ("flare", (58, 26), 8), ("speed", (22, 26), 5, 14)]), 50),
          (dict(dx=4, dy=1, hand=(38, 20), ang=-55, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.3, flutter=4,
                fx=[G.sw(w=0.45), ("dust", 56, 6)]), 70),
          (dict(dx=4, dy=1, hand=(37, 19), ang=-62, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=0.7, flutter=5,
                fx=[("dust", 57, 3)]), 260),
          (dict(dx=2, dy=1, hand=(36, 23), ang=-50, footF=(G.OX + 23, 39), flow=0.4, flutter=6), 180),
          (dict(dy=1, hand=(35, 25), ang=-40, flow=0.3, flutter=7), 140)]
    return G.mseq(tm(fr, 520, 1200, 3), grip=G.GRIP_GREAT)


# =================================================================================================== MAUL
def _mlow(**k):   # the walk-charge carry (as player_v13_a._mlow): leaning in, the hammer low behind the heel
    d = dict(dx=1, dy=3, head_dx=1, hand=(29, 26), ang=166, slen=18, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39))
    d.update(k)
    return d


def ml_payback():  # payback: the braced head torn up off the floor -- a full-body uppercut that throws the hammer at the sky
    fr = [(dict(dx=0, dy=4, head_dy=1, hand=(37, 26), ang=80, footB=(G.OX + 4, 39), footF=(G.FF[0] + 2, 39), flow=0.3,
                fx=[("dust", 42, 3)]), 60),
          (dict(dx=1, dy=3, hand=(37, 28), ang=48, footF=(G.FF[0] + 3, 39), flow=0.8, flutter=1, fx=[G.sw(w=0.35), ("dust", 44, 5)]), 70),
          (dict(dx=3, dy=1, hand=(40, 24), ang=-26, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=2,
                fx=[G.sw(w=0.65), ("flare", (52, 14), 6)]), 45),
          (dict(dx=3, dy=-2, hand=(37, 13), ang=-88, footB=(G.OX + 9, 37), footF=(G.FF[0] + 4, 38), flow=1.4, flutter=3,
                fx=[G.sw(w=0.5), ("flare", (40, 2), 4)]), 60),
          (dict(dx=2, dy=-1, hand=(32, 12), ang=-118, footB=(G.OX + 9, 38), footF=(G.FF[0] + 3, 39), flow=0.8, flutter=4), 200),
          (dict(dx=1, dy=1, hand=(33, 20), ang=-100, flow=0.4, flutter=5), 120),
          (dict(dy=1, hand=(33, 24), ang=-80, flow=0.3, flutter=6), 100)]
    return G.mseq(tm(fr, 160, 600, 2), grip=GRIP_MAUL)


def ml_jab():  # haft jab: still charging, the hammer whipped under and rammed straight out, head first -- then back to the carry
    fr = [(dict(flow=0.5, **_mlow()), 70),
          (dict(dx=1, dy=3, hand=(33, 29), ang=100, slen=16, footF=(G.FF[0] + 3, 39), flow=0.9, flutter=1, fx=[G.sw(w=0.35)]), 50),
          (dict(dx=4, dy=3, head_dx=1, hand=(42, 26), ang=-4, slen=15, footB=(G.OX + 8, 39), footF=(G.OX + 26, 39), flow=1.6,
                flutter=2, fx=[("speed", (20, 22), 5, 14), ("flare", (58, 25), 6)]), 50),
          (dict(dx=4, dy=3, head_dx=1, hand=(41, 26), ang=-2, slen=15, footB=(G.OX + 8, 39), footF=(G.OX + 26, 39), flow=1.1,
                flutter=3, fx=[("flare", (57, 25), 3)]), 60),
          (dict(dx=2, dy=3, hand=(34, 29), ang=118, slen=16, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=4), 70),
          (dict(flow=0.5, flutter=5, **_mlow()), 60)]
    return G.mseq(tm(fr, 120, 360, 2), grip=GRIP_MAUL)


def ml_pound():  # third pound: out of the double smash a little hop, the hammer heaved high -- and the floor takes it a third time
    fr = [(dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=80, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.5), 60),
          (dict(dx=0, dy=-2, hand=(30, 11), ang=-125, footB=(G.OX + 8, 36), footF=(G.OX + 18, 35), air=True, flow=1.0, flutter=1,
                fx=[("dust", 30, 4)]), 100),
          (dict(dx=0, dy=-4, hand=(29, 9), ang=-160, footB=(G.OX + 9, 34), footF=(G.OX + 18, 33), air=True, flow=1.2, flutter=2,
                fx=[("glint", "tip")]), 100),
          (dict(dx=2, dy=1, hand=(39, 21), ang=-4, footF=(G.FF[0] + 4, 39), flow=0.4, flutter=3, fx=[G.sw(w=0.6)]), 40),
          (dict(dx=3, dy=6, head_dy=1, hand=(38, 27), ang=84, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.5, flutter=4,
                fx=[G.sw(w=0.45), ("dust", 39, 12), ("flare", (39, 36), 8), ("rings", (39, 37), (6, 11))]), 70),
          (dict(dx=3, dy=7, head_dy=2, hand=(38, 27), ang=86, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.9, flutter=5,
                fx=[("dust", 39, 6), ("rings", (39, 37), (12, 16))]), 220),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=6), 150)]
    return G.mseq(tm(fr, 260, 700, 3), grip=GRIP_MAUL)


def ml_spike():  # hammer spike: in the air the hammer goes back over the head and is spiked down in front, dragging the foe with it
    A = dict(G.AIR)
    fr = [(dict(dy=-2, hand=(30, 13), ang=-138, flow=0.9, **A), 100),
          (dict(dx=-1, dy=-3, head_dx=-1, hand=(29, 10), ang=-152, flow=1.1, flutter=1, fx=[("glint", "tip")], **A), 100),
          (dict(dx=2, dy=0, hand=(38, 21), ang=18, flow=1.4, flutter=2, fx=[G.sw(w=0.6)], **A), 45),
          (dict(dx=2, dy=1, hand=(36, 29), ang=74, flow=1.2, flutter=3, fx=[G.sw(w=0.5), ("flare", (40, 38), 5)], **A), 60),
          (dict(dx=1, dy=0, hand=(36, 27), ang=60, flow=0.7, flutter=4, **A), 150),
          (dict(dy=-1, hand=(35, 24), ang=-30, flow=0.4, flutter=5, **A), 100)]
    return G.mseq(tm(fr, 200, 500, 2), grip=GRIP_MAUL)


# ---- v14c: more J / K mixes for the brawler
def ml_side():  # side blow (J -> K tap): the hammer slung round from behind the hip, a flat hook that knocks the foe aside
    fr = [(dict(dx=-1, dy=2, head_dx=-1, hand=(27, 27), ang=-178, footB=(G.OX + 5, 39), flow=0.3), 110),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(26, 28), ang=172, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 130),
          (dict(dx=3, dy=2, hand=(41, 26), ang=-6, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=2,
                fx=[("arc", (30, 27), 176, -6, dict(sq=0.38, w=0.7)), ("flare", (58, 24), 6)]), 50),
          (dict(dx=3, dy=2, hand=(39, 22), ang=-48, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.2, flutter=3, fx=[G.sw(w=0.45)]), 60),
          (dict(dx=2, dy=2, hand=(35, 20), ang=-80, footF=(G.OX + 23, 39), flow=0.7, flutter=4), 150),
          (dict(dx=1, dy=1, hand=(34, 24), ang=-60, flow=0.4, flutter=5), 120)]
    return G.mseq(tm(fr, 240, 620, 2), grip=GRIP_MAUL)


def ml_drop():  # hammer drop (upswing -> J): the hammer is already in the sky -- it comes straight down on whatever went up
    fr = [(dict(dx=1, dy=-1, hand=(31, 11), ang=-125, footB=(G.OX + 9, 38), footF=(G.FF[0] + 2, 39), flow=0.6), 90),
          (dict(dx=0, dy=-2, head_dx=-1, hand=(29, 9), ang=-158, footB=(G.OX + 8, 38), footF=(G.FF[0] + 2, 39), flow=0.5, flutter=1,
                fx=[("glint", "tip")]), 130),
          (dict(dx=2, dy=2, hand=(39, 21), ang=-6, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=2, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=80, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3,
                fx=[G.sw(w=0.45), ("dust", 38, 8), ("flare", (38, 37), 6)]), 60),
          (dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=82, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=4,
                fx=[("dust", 38, 3)]), 180),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=5), 130)]
    return G.mseq(tm(fr, 220, 600, 2), grip=GRIP_MAUL)


def ml_backslam():  # backswing slam (side blow -> K): the hook's momentum carries the body all the way round, up and over -- crack
    fr = [(dict(dx=2, dy=2, hand=(35, 20), ang=-80, footF=(G.OX + 23, 39), flow=0.6), 80),
          (dict(dx=1, dy=2, hand=(37, 26), ang=-6, footF=(G.FF[0] + 2, 39), flow=1.3, flutter=1, mirror=True, behind=True,
                fx=[("arc", (29, 27), 10, -170, dict(sq=0.38, w=0.5))]), 90),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(28, 10), ang=-150, footB=(G.OX + 6, 38), footF=(G.FF[0] + 2, 39), flow=0.6, flutter=2), 110),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(28, 9), ang=-168, footB=(G.OX + 6, 38), footF=(G.FF[0] + 2, 39), flow=0.3, flutter=3,
                fx=[("glint", "tip")]), 90),
          (dict(dx=2, dy=2, hand=(39, 21), ang=-4, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=4, fx=[G.sw(w=0.6)]), 40),
          (dict(dx=3, dy=6, head_dy=1, hand=(38, 27), ang=84, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.5, flutter=5,
                fx=[G.sw(w=0.45), ("dust", 39, 11), ("flare", (39, 36), 8), ("rings", (39, 37), (6, 10))]), 70),
          (dict(dx=3, dy=6, head_dy=2, hand=(38, 27), ang=86, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.8, flutter=6,
                fx=[("dust", 39, 5), ("rings", (39, 37), (11, 15))]), 220),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=7), 170)]
    return G.mseq(tm(fr, 320, 820, 4), grip=GRIP_MAUL)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    S = g.settled
    A = lambda a, b=None: (a, a if b is None else b)
    E = []

    def add(tag, fn, wind=None, total=None, active=None, settle=True, **meta):
        if wind is not None:
            SPEC[tag] = (wind, total)
        if active is not None:
            meta["active"] = active
        E.append((tag, S(fn) if settle else fn, meta))

    gs = dict(kinds=("greatsword",))
    add("gs_bash", gs_bash, 180, 480, A(2, 3), settle=False, hit=[-2, -32, 26, -10], fxat=(20, -22), **gs)
    add("gs_mcleave", gs_mcleave, 360, 820, A(4, 5), **gs)
    add("gs_retort", gs_retort, 150, 560, A(2, 3), up=True, **gs)
    add("gs_leap", gs_leap, 260, 700, A(3, 4), x0=-6, **gs)
    add("ml_payback", ml_payback, 160, 600, A(2, 3), up=True)
    add("ml_jab", ml_jab, 120, 360, A(2, 3), settle=False, x0=0)
    add("ml_pound", ml_pound, 260, 700, A(3, 4))
    add("ml_spike", ml_spike, 200, 500, A(2, 3))
    # v14c
    add("gs_heave", gs_heave, 440, 1000, A(3, 4), up=True, **gs)
    add("gs_turn", gs_turn, 420, 1000, A(3, 4), x0=-10, **gs)
    add("gs_split", gs_split, 520, 1200, A(3, 4), **gs)
    add("ml_side", ml_side, 240, 620, A(2, 3), x0=-4)
    add("ml_drop", ml_drop, 220, 600, A(2, 3))
    add("ml_backslam", ml_backslam, 320, 820, A(4, 5))
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    mod = sys.modules.get("player_v14_heavy")
    fns = dict(GP.ANIMS)
    print(f"{'tag':14} {'frames':>6} {'wind':>5} {'total':>5}   {'spec':>9}   ok")
    for t, (w, tot0) in mod.SPEC.items():
        fr = list(fns[t]())
        ms = [m for _, m in fr]
        act = GP.ACTIVE.get(t)
        wind = sum(ms[:act[0]]) if act else None
        tot = sum(ms)
        print(f"{t:14} {len(fr):6} {wind:>5} {tot:5}   {'%d/%d' % (w, tot0):>9}   {'OK' if (wind, tot) == (w, tot0) else 'MISMATCH'}")
