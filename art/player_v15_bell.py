"""v15 tags for the Warbell (bell, tags wb_*, weapon dirge_bell) -- docs/WEAPON_REVAMP.md C5, docs/v15/bell.md.

Same register(G) contract as player_v13_a.py / player_v14_*.py: return [(tag, fn, opts)], fn() -> [(cels, ms)].
Timing: each attack is authored to its row in web/src/78_mech_bell.js -- the frames before the first active frame add up to
the move's wind-up, all frames to its total (tm() rescales a hand-timed sequence onto those two numbers). Loops (the wind-up
hold, the plunge's fall) are driven by the engine and not settled.

The bell is a pendulum: every swing is a heave against its weight, a contact where the lip rings (the "rings" fx in the bell's
pale-gold smear), and a follow-through the knight has to lean against. The light chain flows end to start: the left swing ends
low in front, the right swing rises from there and ends high, the overhead clang starts high.

  python3 art/player_v15_bell.py        # prints each tag's frames / wind / total against its spec
"""
import math

G = None   # gen_player, set by register()
SPEC = {}
GRIP = 4.0   # two hands on the haft, as the maul


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


def _sw(w):
    return G.sw(w=w)


SPIN_RG = dict(sq=0.32, w=9.0)
FLAT = dict(sq=0.42, w=0.65)


def _ring(a0, a1):   # the bell whirled flat round the waist
    return ("ring", (31, 28), 20, a0, a1, SPIN_RG)


def _floor(x, k=0, **kw):   # the bell mouth-down on the floor in front, knees bent over it (k: how hard it bit)
    # the hand rides high and the haft slants (64-70 deg) so the whole bell fits above the floor instead of being shrunk to it;
    # its lip lands about 2 px past x. An `ang` given in the old vertical terms (74-88) is mapped onto the slant.
    d = dict(dx=3, dy=5 + k, head_dy=1 + k, hand=(x - 1, 21), ang=58 + 2 * k, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39))
    if "ang" in kw:
        kw["ang"] = 58 + (kw["ang"] - 80) * 0.5
    d.update(kw)
    return d


# =================================================================================================== Ash: the J chain
def wb_1():  # left swing: the bell cocked over the back shoulder, brought down across the front, its weight hanging after it
    fr = [(dict(dx=0, dy=1, hand=(31, 20), ang=-110, flow=0.3), 70),
          (dict(dx=-1, dy=0, head_dx=-1, hand=(28, 13), ang=-142, footB=(G.OX + 6, 39), flow=0.3, flutter=1), 120),
          (dict(dx=1, dy=1, hand=(34, 15), ang=-72, footF=(G.FF[0] + 2, 39), flow=0.9, flutter=2, fx=[_sw(0.45)]), 40),
          (dict(dx=2, dy=3, hand=(39, 23), ang=6, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=3,
                fx=[_sw(0.55), ("rings", (57, 25), (4, 8))]), 50),
          (dict(dx=2, dy=4, head_dy=1, hand=(38, 28), ang=46, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=1.0, flutter=4,
                fx=[_sw(0.4)]), 70),
          (dict(dx=2, dy=4, head_dy=1, hand=(37, 29), ang=62, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=5), 120),
          (dict(dx=1, dy=3, hand=(36, 29), ang=66, footF=(G.FF[0] + 2, 39), flow=0.3, flutter=6), 90)]
    return G.mseq(tm(fr, 190, 460, 3), grip=GRIP)


def wb_2():  # right swing: from low in front the bell is swung back past the heel, then up across the front and over
    fr = [(dict(dx=1, dy=3, hand=(36, 29), ang=66, footF=(G.FF[0] + 2, 39), flow=0.4), 60),
          (dict(dx=-1, dy=3, head_dx=-1, hand=(28, 30), ang=165, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.3, flutter=1,
                fx=[("dust", 12, 2)]), 130),
          (dict(dx=1, dy=3, hand=(33, 31), ang=124, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=2, fx=[_sw(0.4)]), 40),
          (dict(dx=3, dy=1, hand=(40, 24), ang=-24, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=3,
                fx=[_sw(0.6), ("rings", (56, 17), (4, 8))]), 50),
          (dict(dx=3, dy=-1, hand=(37, 15), ang=-80, footB=(G.OX + 9, 38), footF=(G.FF[0] + 4, 39), flow=1.2, flutter=4,
                fx=[_sw(0.45)]), 60),
          (dict(dx=2, dy=0, hand=(33, 13), ang=-110, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=5), 120),
          (dict(dx=1, dy=1, hand=(33, 15), ang=-105, flow=0.4, flutter=6), 90)]
    return G.mseq(tm(fr, 190, 460, 3), grip=GRIP)


def wb_3():  # overhead clang: on up over the back, a hang at the top -- then mouth-first into the floor, and it rings
    fr = [(dict(dx=1, dy=0, hand=(33, 15), ang=-105, flow=0.5), 80),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(29, 10), ang=-155, footB=(G.OX + 6, 38), flow=0.4, flutter=1), 110),
          (dict(dx=-1, dy=-2, head_dx=-1, hand=(29, 9), ang=-172, footB=(G.OX + 6, 38), footF=(G.FF[0] + 1, 39), flow=0.2, flutter=2,
                fx=[("glint", "tip")]), 80),
          (dict(dx=1, dy=0, hand=(34, 12), ang=-88, footF=(G.FF[0] + 2, 39), flow=0.9, flutter=3, fx=[_sw(0.4)]), 40),
          (dict(dx=2, dy=2, hand=(38, 21), ang=-8, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=4, fx=[_sw(0.55)]), 40),
          (dict(flow=1.4, flutter=5, fx=[_sw(0.4), ("dust", 40, 9), ("flare", (40, 37), 6), ("rings", (40, 37), (6, 11))], **_floor(38)), 70),
          (dict(flow=0.8, flutter=6, fx=[("dust", 40, 4), ("rings", (40, 37), (12, 16))], **_floor(38, 1)), 230),
          (dict(dx=2, dy=3, hand=(36, 28), ang=60, footF=(G.FF[0] + 2, 39), flow=0.4, flutter=7), 130),
          (dict(dx=1, dy=2, hand=(35, 28), ang=42, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=8), 110)]
    return G.mseq(tm(fr, 290, 720, 4), grip=GRIP)


def wb_chime():  # chime spin (II): the bell whirled flat round the waist, one ring in front, the turn, one behind
    st = dict(dy=3, footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39))
    fr = [(dict(dx=0, dy=3, hand=(29, 27), ang=168, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.5, fx=[("dust", 14, 2)]), 110),
          (dict(dx=1, hand=(33, 27), ang=-10, slen=10, mirror=True, behind=True, flow=1.0, flutter=1, fx=[_ring(180, 0)], **st), 60),
          (dict(dx=1, hand=(37, 28), ang=4, flow=1.4, flutter=2, fx=[_ring(180, 4), ("rings", (56, 28), (4, 8))], **st), 80),
          (dict(dx=1, hand=(33, 27), ang=-10, slen=10, flow=1.4, flutter=3, behind=True, fx=[_ring(180, 0)], **st), 70),
          (dict(dx=1, hand=(37, 28), ang=4, flow=1.5, flutter=4, mirror=True, fx=[_ring(180, 4), ("rings", (56, 28), (4, 8))], **st), 80),
          (dict(dx=1, dy=3, hand=(36, 26), ang=-22, flow=0.9, flutter=5), 110),
          (dict(dx=1, dy=2, hand=(34, 21), ang=-62, flow=0.5, flutter=6), 120),
          (dict(dx=0, dy=1, hand=(33, 22), ang=-84, flow=0.3, flutter=7), 90)]
    return G.mseq(tm(fr, 220, 640, 2), grip=GRIP)


def wb_knell():  # knell (J J J -> K): the bell hauled back along the floor behind the heel, then dragged low round the front
    fr = [(dict(dx=1, dy=3, hand=(36, 28), ang=50, footF=(G.FF[0] + 2, 39), flow=0.4, fx=[("dust", 44, 3)]), 80),
          (dict(dx=-1, dy=4, head_dx=-1, head_dy=1, hand=(28, 30), ang=172, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.6,
                flutter=1, fx=[("dust", 14, 3)]), 140),
          (dict(dx=-2, dy=4, head_dx=-1, head_dy=1, hand=(27, 30), ang=176, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.3,
                flutter=2, fx=[("dust", 10, 4), ("glint", (12, 35))]), 100),
          (dict(dx=1, dy=4, hand=(33, 31), ang=150, slen=15, footF=(G.FF[0] + 3, 39), flow=1.0, flutter=3), 50),
          (dict(dx=3, dy=4, hand=(41, 30), ang=6, footB=(G.OX + 7, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=4,
                fx=[("arc", (30, 30), 176, 6, dict(sq=0.3, w=0.7)), ("dust", 50, 6), ("rings", (57, 31), (5, 9))]), 50),
          (dict(dx=3, dy=2, hand=(39, 24), ang=-40, footB=(G.OX + 7, 39), footF=(G.OX + 25, 39), flow=1.3, flutter=5, fx=[_sw(0.45)]), 60),
          (dict(dx=3, dy=1, hand=(35, 17), ang=-86, footF=(G.OX + 24, 39), flow=0.7, flutter=6), 200),
          (dict(dx=1, dy=1, hand=(34, 20), ang=-80, flow=0.4, flutter=7), 140)]
    return G.mseq(tm(fr, 320, 820, 4), grip=GRIP)


# =================================================================================================== Ember: the K side
def wb_back():  # backswing (J -> K): the knight turns his back into it -- the bell's shoulder comes round flat at head height
    fr = [(dict(dx=1, dy=2, hand=(36, 24), ang=-30, flow=0.5), 70),
          (dict(dx=0, dy=2, hand=(33, 21), ang=-150, slen=14, mirror=True, behind=True, flow=0.9, flutter=1), 110),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(29, 19), ang=-174, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.4, flutter=2,
                fx=[("glint", "tip")]), 80),
          (dict(dx=1, dy=1, hand=(32, 20), ang=-162, slen=14, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=3), 40),
          (dict(dx=3, dy=1, hand=(40, 20), ang=-12, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=4,
                fx=[("arc", (30, 20), 178, -12, FLAT), ("rings", (57, 16), (4, 8))]), 50),
          (dict(dx=3, dy=1, hand=(39, 17), ang=-50, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.1, flutter=5, fx=[_sw(0.4)]), 60),
          (dict(dx=2, dy=1, hand=(35, 15), ang=-90, footF=(G.OX + 23, 39), flow=0.6, flutter=6), 150),
          (dict(dx=1, dy=1, hand=(34, 20), ang=-76, flow=0.3, flutter=7), 110)]
    return G.mseq(tm(fr, 240, 620, 4), grip=GRIP)


def _wind(i=0, **k):   # the wind-up hold: swung round behind and up, the bell hanging over the back of the head
    d = dict(dx=-2, dy=3 + (1 if i in (1, 2) else 0), head_dx=-1, hand=(27, 13 + (1 if i in (1, 2) else 0)),
             ang=-150 - (4 if i in (1, 2) else 0), footB=(G.OX + 4, 39), footF=(G.FF[0] + 2, 39))
    d.update(k)
    return d


def wb_kwind():  # wind-up toll (loop): coiled low on the back foot, the bell's weight swaying behind the head
    return G.mseq([(dict(flow=0.3 + 0.1 * (i % 2), flutter=i, fx=[("glint", "tip")] if i == 2 else [], **_wind(i)), 130)
                   for i in range(4)], grip=GRIP)


def wb_slam():  # forward slam: the bell lifted straight up in front, on the toes -- then mouth-first into the floor
    fr = [(dict(dx=1, dy=2, hand=(34, 25), ang=40, flow=0.4), 70),
          (dict(dx=0, dy=1, hand=(33, 15), ang=-75, footF=(G.FF[0] + 1, 39), flow=0.7, flutter=1), 90),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(32, 10), ang=-95, footB=(G.OX + 7, 38), footF=(G.FF[0] + 1, 39), flow=0.5, flutter=2,
                fx=[("glint", "tip")]), 100),
          (dict(dx=1, dy=1, hand=(37, 17), ang=-30, footF=(G.FF[0] + 3, 39), flow=1.1, flutter=3, fx=[_sw(0.5)]), 40),
          (dict(flow=1.4, flutter=4, fx=[_sw(0.45), ("dust", 42, 9), ("flare", (42, 37), 6), ("rings", (42, 37), (6, 10))],
                **_floor(39, 0, ang=74)), 70),
          (dict(flow=0.8, flutter=5, fx=[("dust", 42, 4), ("rings", (42, 37), (11, 15))], **_floor(39, 1, ang=76)), 200),
          (dict(dx=1, dy=3, hand=(36, 27), ang=58, flow=0.4, flutter=6), 130)]
    return G.mseq(tm(fr, 280, 680, 4), grip=GRIP)


def wb_dslam():  # double slam: up off the floor and down again into the same spot, twice
    def smash(k):
        return [(dict(dx=2 + k, dy=2, hand=(38, 21), ang=-8, footF=(G.FF[0] + 3 + k, 39), flow=1.2, flutter=2 + 4 * k, fx=[_sw(0.55)]), 45),
                (dict(flow=1.2, flutter=3 + 4 * k, fx=[_sw(0.4), ("dust", 41 + k, 7 + k), ("flare", (41 + k, 37), 5 + k),
                                                       ("rings", (41 + k, 37), (5 + k, 9 + k))],
                      **_floor(38 + k, 0, dx=2 + k, ang=76, footB=(G.OX + 6 + k, 39), footF=(G.FF[0] + 3 + k, 39))), 60)]
    fr = [(dict(dx=1, dy=1, hand=(31, 14), ang=-118, footF=(G.FF[0] + 2, 39), flow=0.5), 110),
          (dict(dx=0, dy=-1, hand=(32, 10), ang=-98, footB=(G.OX + 7, 38), footF=(G.FF[0] + 2, 39), flow=0.7, flutter=1,
                fx=[("glint", "tip")]), 130)] \
        + smash(0) \
        + [(dict(flow=0.6, flutter=4, fx=[("dust", 41, 3), ("rings", (41, 37), (10, 14))], **_floor(38, 0, dx=2, dy=4, ang=72)), 70),
           (dict(dx=1, dy=0, hand=(31, 12), ang=-128, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=5), 90),
           (dict(dx=2, dy=-1, hand=(33, 10), ang=-100, footF=(G.FF[0] + 4, 39), flow=0.9, flutter=6, fx=[("glint", "tip")]), 60)] \
        + smash(1) \
        + [(dict(flow=0.6, flutter=8, fx=[("dust", 42, 4), ("rings", (42, 37), (11, 16))], **_floor(39, 1, dx=3, ang=78)), 200),
           (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=9), 150)]
    return G.mseq(tm(fr, 300, 880, 3), grip=GRIP)


def wb_toll():  # wind-up toll (release): out of the coil the bell goes all the way over the top and comes down with everything
    E = G.EMBER
    fr = [(dict(flow=0.6, fx=[("glint", "tip")], **_wind(0)), 60),
          (dict(dx=-1, dy=-2, hand=(30, 9), ang=-125, footB=(G.OX + 7, 38), footF=(G.FF[0] + 2, 39), flow=0.9, flutter=1,
                fx=[("ring", (29, 20), 13, 195, 240, dict(sq=1.0, w=3.0))]), 70),
          (dict(dx=1, dy=-1, hand=(34, 11), ang=-80, footF=(G.FF[0] + 3, 39), flow=1.1, flutter=2, fx=[_sw(0.45)]), 40),
          (dict(dx=3, dy=2, hand=(40, 21), ang=-6, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=3, fx=[_sw(0.6)]), 30),
          (dict(flow=1.6, flutter=4, fx=[_sw(0.45), ("dust", 44, 13), ("flare", (44, 36), 10, E[:3]), ("rings", (44, 37), (7, 12))],
                **_floor(40, 1, ang=74)), 70),
          (dict(flow=1.0, flutter=5, fx=[("dust", 44, 7), ("rings", (44, 37), (13, 19)), ("embers", (44, 30), 10, 2)],
                **_floor(40, 2, ang=76)), 260),
          (dict(flow=0.6, flutter=6, fx=[("dust", 44, 3)], **_floor(39, 0, ang=74)), 150),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=7), 150)]
    return G.mseq(tm(fr, 200, 760, 4), grip=GRIP)


# =================================================================================================== Gold: the up J
def wb_up():  # peal uppercut: crouched over the bell, then heaved straight up past the helm -- it peals at the top
    fr = [(dict(dx=0, dy=3, hand=(33, 29), ang=108, footF=(G.FF[0] + 1, 39), flow=0.4, fx=[("dust", 38, 2)]), 100),
          (dict(dx=1, dy=4, head_dy=1, hand=(35, 31), ang=80, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.6, flutter=1), 100),
          (dict(dx=2, dy=1, hand=(39, 23), ang=-30, footF=(G.FF[0] + 3, 39), flow=1.1, flutter=2, fx=[_sw(0.5)]), 40),
          (dict(dx=2, dy=-2, hand=(35, 12), ang=-88, footB=(G.OX + 9, 37), footF=(G.FF[0] + 3, 38), flow=1.4, flutter=3,
                fx=[_sw(0.55), ("flare", "tip", 6)]), 55),
          (dict(dx=2, dy=-2, hand=(34, 11), ang=-95, footB=(G.OX + 9, 37), footF=(G.FF[0] + 3, 38), flow=1.0, flutter=4,
                fx=[("flare", "tip", 4)]), 70),
          (dict(dx=1, dy=-1, hand=(32, 13), ang=-115, footF=(G.FF[0] + 2, 39), flow=0.6, flutter=5), 150),
          (dict(dx=0, dy=1, hand=(32, 17), ang=-112, flow=0.3, flutter=6), 100)]
    return G.mseq(tm(fr, 220, 560, 3), grip=GRIP)


def wb_peal():  # falling peal (up J -> J): the bell is already up -- it comes straight down on whatever went up
    fr = [(dict(dx=1, dy=-1, hand=(32, 12), ang=-118, footB=(G.OX + 9, 38), footF=(G.FF[0] + 2, 39), flow=0.6), 80),
          (dict(dx=0, dy=-2, head_dx=-1, hand=(30, 9), ang=-150, footB=(G.OX + 8, 38), footF=(G.FF[0] + 2, 39), flow=0.5, flutter=1,
                fx=[("glint", "tip")]), 120),
          (dict(dx=2, dy=2, hand=(39, 21), ang=-6, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=2, fx=[_sw(0.6)]), 45),
          (dict(flow=1.2, flutter=3, fx=[_sw(0.45), ("dust", 41, 8), ("flare", (41, 37), 6), ("rings", (41, 37), (6, 10))],
                **_floor(38, 0, dx=2, ang=78)), 60),
          (dict(flow=0.6, flutter=4, fx=[("dust", 41, 3), ("rings", (41, 37), (11, 14))], **_floor(38, 0, dx=2, ang=80)), 180),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=5), 130)]
    return G.mseq(tm(fr, 200, 560, 2), grip=GRIP)


# =================================================================================================== I: Perform / Encore
def wb_perform():  # perform: the bell raised and let peal, then whirled once round the body -- front, turn, back -- and set down
    st = dict(dy=3, footB=(G.OX + 4, 39), footF=(G.FF[0] + 4, 39))
    fr = [(dict(dx=0, dy=2, hand=(33, 24), ang=-40, flow=0.4), 80),
          (dict(dx=-1, dy=0, head_dx=-1, hand=(30, 12), ang=-118, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.6, flutter=1), 110),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(30, 10), ang=-98, footB=(G.OX + 4, 39), footF=(G.FF[0] + 3, 39), flow=0.4, flutter=2,
                fx=[("flare", "tip", 5)]), 110),
          (dict(dx=1, hand=(37, 27), ang=4, flow=1.4, flutter=3, fx=[_ring(180, 4), ("rings", (56, 26), (5, 9))], **st), 70),
          (dict(dx=1, hand=(33, 26), ang=-10, slen=10, behind=True, flow=1.5, flutter=4, fx=[_ring(180, 0)], **st), 70),
          (dict(dx=1, hand=(37, 27), ang=4, mirror=True, flow=1.3, flutter=5, fx=[_ring(180, 4), ("rings", (56, 26), (5, 9))], **st), 70),
          (dict(flow=0.8, flutter=6, fx=[("dust", 39, 6), ("rings", (39, 37), (8, 13))], **_floor(37, 0, dx=1, ang=82, footB=(G.OX + 4, 39))), 220),
          (dict(dx=1, dy=3, hand=(35, 27), ang=68, flow=0.5, flutter=7), 120),
          (dict(dx=0, dy=2, hand=(34, 26), ang=42, flow=0.3, flutter=8), 100)]
    return G.mseq(tm(fr, 300, 900, 3), grip=GRIP)


def wb_encore():  # encore (Perform -> I): heaved off the floor straight overhead, and tolled down again -- the ring opens both ways
    fr = [(dict(flow=0.5, **_floor(37, 0, dx=1, ang=80, footB=(G.OX + 4, 39))), 70),
          (dict(dx=0, dy=-1, hand=(33, 11), ang=-92, footB=(G.OX + 5, 39), footF=(G.FF[0] + 3, 39), flow=0.9, flutter=1), 100),
          (dict(dx=-1, dy=-2, head_dx=-1, hand=(31, 9), ang=-100, footB=(G.OX + 4, 38), footF=(G.FF[0] + 3, 39), flow=0.5, flutter=2,
                fx=[("flare", "tip", 6)]), 90),
          (dict(dx=1, dy=1, hand=(36, 17), ang=-30, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3, fx=[_sw(0.5)]), 40),
          (dict(flow=1.5, flutter=4, fx=[_sw(0.4), ("dust", 39, 12), ("flare", (39, 36), 9), ("rings", (39, 37), (6, 11)),
                                          ("ring", (39, 38), 16, 0, 359, dict(sq=0.25, w=2.0))],
                **_floor(37, 1, dx=1, ang=84, footB=(G.OX + 4, 39))), 70),
          (dict(flow=0.9, flutter=5, fx=[("dust", 39, 6), ("rings", (39, 37), (12, 17)), ("ring", (39, 38), 22, 0, 359, dict(sq=0.25, w=1.5))],
                **_floor(37, 1, dx=1, ang=86, footB=(G.OX + 4, 39))), 240),
          (dict(dx=1, dy=3, hand=(35, 27), ang=66, flow=0.5, flutter=6), 150),
          (dict(dx=0, dy=2, hand=(34, 26), ang=42, flow=0.3, flutter=7), 120)]
    return G.mseq(tm(fr, 260, 800, 4), grip=GRIP)


# =================================================================================================== roll / air
def wb_rollj():  # ringing lunge: up out of the roll on a long step, the bell swept flat through the front
    fr = [(dict(dx=-1, dy=4, head_dy=1, hand=(30, 30), ang=160, footB=(G.OX + 6, 39), footF=(G.OX + 21, 39), flow=0.9), 90),
          (dict(dx=1, dy=3, hand=(33, 30), ang=132, footB=(G.OX + 7, 39), footF=(G.OX + 24, 39), flow=1.2, flutter=1,
                fx=[("speed", (20, 24), 4, 12)]), 70),
          (dict(dx=4, dy=2, head_dx=1, hand=(42, 24), ang=-6, footB=(G.OX + 9, 39), footF=(G.OX + 27, 39), flow=1.5, flutter=2,
                fx=[("arc", (30, 26), 170, -6, FLAT), ("rings", (58, 22), (4, 8))]), 50),
          (dict(dx=4, dy=1, hand=(40, 19), ang=-45, footB=(G.OX + 9, 39), footF=(G.OX + 27, 39), flow=1.2, flutter=3, fx=[_sw(0.45)]), 60),
          (dict(dx=3, dy=1, hand=(36, 15), ang=-85, footF=(G.OX + 25, 39), flow=0.6, flutter=4), 120),
          (dict(dx=1, dy=1, hand=(34, 20), ang=-75, flow=0.3, flutter=5), 90)]
    return G.mseq(tm(fr, 160, 440, 2), grip=GRIP)


def wb_rollk():  # bell drop: out of the roll's crouch the bell is hauled up over the shoulder and simply let fall
    fr = [(dict(dx=-1, dy=5, head_dy=1, hand=(31, 31), ang=160, footB=(G.OX + 5, 39), footF=(G.OX + 20, 39), flow=0.8), 80),
          (dict(dx=0, dy=0, hand=(30, 11), ang=-130, footB=(G.OX + 7, 38), footF=(G.FF[0] + 2, 39), flow=1.0, flutter=1), 100),
          (dict(dx=0, dy=-2, hand=(31, 9), ang=-150, footB=(G.OX + 8, 37), footF=(G.FF[0] + 2, 38), flow=0.6, flutter=2,
                fx=[("glint", "tip")]), 80),
          (dict(dx=2, dy=1, hand=(38, 19), ang=-15, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3, fx=[_sw(0.55)]), 40),
          (dict(flow=1.4, flutter=4, fx=[_sw(0.4), ("dust", 43, 10), ("flare", (43, 36), 7), ("rings", (43, 37), (6, 10))],
                **_floor(40, 0, ang=74)), 70),
          (dict(flow=0.7, flutter=5, fx=[("dust", 43, 5), ("rings", (43, 37), (11, 15))], **_floor(40, 1, ang=76)), 200),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=6), 150)]
    return G.mseq(tm(fr, 260, 640, 4), grip=GRIP)


def wb_air():  # air swing: legs tucked, the bell brought over the top and flat through the front
    A = dict(G.AIR)
    fr = [(dict(dy=-1, hand=(29, 14), ang=-150, flow=0.9, **A), 90),
          (dict(dx=-1, dy=-2, head_dx=-1, hand=(28, 14), ang=-170, flow=1.0, flutter=1, fx=[("glint", "tip")], **A), 90),
          (dict(dx=2, dy=0, hand=(39, 23), ang=0, flow=1.4, flutter=2, fx=[_sw(0.6), ("rings", (56, 23), (4, 7))], **A), 50),
          (dict(dx=2, hand=(38, 26), ang=40, flow=1.1, flutter=3, fx=[_sw(0.45)], **A), 60),
          (dict(dx=1, hand=(35, 27), ang=78, flow=0.7, flutter=4, **A), 120),
          (dict(dy=-1, hand=(33, 22), ang=-40, flow=0.4, flutter=5, **A), 90)]
    return G.mseq(tm(fr, 180, 420, 2), grip=GRIP)


def wb_down():  # bell pogo: knees up, the bell turned mouth-down under the feet and driven onto the foe
    T = dict(G.TUCK)
    fr = [(dict(dy=-2, hand=(31, 18), ang=-60, flow=0.8, **T), 50),
          (dict(dy=-3, hand=(34, 20), ang=68, flow=1.2, flutter=1, fx=[("vspeed", (36, 18), 3, 6)], **T), 60),
          (dict(dy=-3, hand=(34, 20), ang=70, flow=1.0, flutter=2, fx=[("flare", "tip", 4)], **T), 90),
          (dict(dy=-2, hand=(32, 22), ang=60, flow=0.6, flutter=3, **dict(G.AIR)), 100)]
    return G.mseq(tm(fr, 100, 300, 1), grip=GRIP)


def wb_plunge():  # bell plunge (engine-driven): heave overhead (0-1), then the dive mouth-first with the cape torn up (2-3 loop)
    A, T = dict(G.AIR), dict(G.TUCK)
    return G.mseq([(dict(dx=-1, dy=-2, hand=(30, 10), ang=-110, flow=1.0, **A), 100),
                   (dict(dx=-1, dy=-3, head_dx=-1, hand=(29, 9), ang=-150, flow=1.2, flutter=1, fx=[("glint", "tip")], **A), 100),
                   (dict(dx=1, dy=-2, hand=(36, 19), ang=62, flow=1.7, flutter=2, fx=[("vspeed", (38, 14), 4, 10)], **T), 70),
                   (dict(dx=1, dy=-2, hand=(36, 20), ang=66, flow=1.9, flutter=3, fx=[("vspeed", (38, 13), 4, 12)], **T), 70)],
                  grip=GRIP)


def wb_pland():  # the plunge lands: crouched over the bell in the floor, the floor rings out both ways, then up
    fr = [(dict(flow=1.2, fx=[("dust", 38, 12)], **_floor(36, 0, dx=1, ang=86, footB=(G.OX + 4, 39))), 40),
          (dict(flow=1.4, flutter=1, fx=[("dust", 38, 14), ("flare", (38, 36), 10), ("rings", (38, 37), (7, 12)),
                                         ("ring", (38, 38), 16, 0, 359, dict(sq=0.25, w=2.0))],
                **_floor(36, 1, dx=1, ang=88, footB=(G.OX + 4, 39))), 80),
          (dict(flow=0.8, flutter=2, fx=[("dust", 38, 6), ("rings", (38, 37), (13, 18))], **_floor(36, 1, dx=1, ang=88, footB=(G.OX + 4, 39))), 220),
          (dict(dx=1, dy=3, hand=(35, 27), ang=60, flow=0.5, flutter=3), 130),
          (dict(dx=0, dy=2, hand=(34, 27), ang=40, flow=0.3, flutter=4), 90)]
    return G.mseq(tm(fr, 40, 560, 1), grip=GRIP)


# =================================================================================================== the weapon (restyled)
# The platform's Dirgebell drew a gold outline round a dark body, so at 64x40 it read as a hollow frame and sank into the
# knight's armour. Here: a cast-iron bell shaded across its width (lit flank, dark flank, a black outline edge), gold only
# where a real bell is bright -- the worn lip at the mouth and one sound-bow band -- a dark mouth with the gold clapper in it,
# ember glints in the rune cuts, and a chain-wound haft. Slightly larger head (9.5 px, 11-12 px across the lip).
IRON_B = ((150, 146, 162), (108, 104, 120), (70, 66, 82), (40, 36, 48), (22, 18, 26))
GOLD_B = ((246, 218, 140), (196, 150, 72), (120, 82, 36))


def shp_dirge_bell(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 9.5
    if h0 <= u <= tip:
        t = (u - h0) / 9.5                           # domed crown, a straight waist, the flare of the lip
        if t < 0.16:
            hw = 3.0 * math.sqrt(max(0.0, t) / 0.16)
        elif t < 0.72:
            hw = 3.0 + 0.6 * (t - 0.16) / 0.56
        else:
            hw = 3.6 + 2.2 * ((t - 0.72) / 0.28) ** 1.5
        av = abs(v)
        if av <= hw:
            edge = hw - av
            if u > tip - 1.1:                        # the lip, seen edge-on: worn gold, the mouth dark inside it
                if av < 0.75:
                    return GOLD_B[0]                 # the clapper's ball hanging in the mouth
                if edge > 1.2 and u > tip - 0.7:
                    return IRON_B[4]
                return GOLD_B[0] if vl > 0.5 else (GOLD_B[1] if vl > -1.5 else GOLD_B[2])
            if edge < 0.55:
                return IRON_B[4]                     # the dark rim that keeps the silhouette off the armour
            if abs(u - (tip - 2.6)) < 0.5:
                return GOLD_B[1] if vl > -0.5 else GOLD_B[2]   # the sound-bow band
            if ((int(u * 1.3) * 5 + int(v * 1.1) * 3) % 13) == 0 and -1.5 < vl < 1.5 and 0.2 < t < 0.7:
                return (220, 110, 50)                # an ember glint in a rune cut
            q = vl / max(1.0, hw)                    # shaded across the width: lit flank -> dark flank
            if q > 0.45:
                return IRON_B[0]
            if q > -0.05:
                return IRON_B[1]
            if q > -0.55:
                return IRON_B[2]
            return IRON_B[3]
    if h0 - 2.0 <= u < h0 + 0.3 and 0.5 <= abs(v) <= 1.6:   # the crown loop
        return GOLD_B[1] if vl > 0 else GOLD_B[2]
    if -3.4 <= u < h0 - 0.8 and abs(v - 0.4) <= 0.75:      # haft, chain-wound below the head
        iu = int(math.floor(u))
        if u > h0 - 5.5 and (iu + (1 if v > 0.4 else 0)) % 2 == 0:
            return IRON_B[0] if vl > 0 else IRON_B[2]
        return (92, 64, 44) if vl > 0 else (56, 38, 28)
    if -4.8 <= u < -3.4 and abs(v - 0.4) <= 1.2:            # iron pommel
        return IRON_B[1] if vl > 0 else IRON_B[3]
    return None


# =================================================================================================== registry
def register(g):
    global G
    G = g
    if "dirge_bell" in g.WPN:
        _, L0, back, _w, style = g.WPN["dirge_bell"]
        g.WPN["dirge_bell"] = (shp_dirge_bell, L0, back, 6.9, style)
    S = g.settled
    A = lambda a, b=None: (a, a if b is None else b)
    E = []

    def add(tag, fn, wind=None, total=None, active=None, settle=True, **meta):
        if wind is not None:
            SPEC[tag] = (wind, total)
        if active is not None:
            meta["active"] = active
        E.append((tag, S(fn) if settle else fn, meta))

    add("wb_1", wb_1, 190, 460, A(3, 4))
    add("wb_2", wb_2, 190, 460, A(3, 4))
    add("wb_3", wb_3, 290, 720, A(4, 5))
    add("wb_chime", wb_chime, 220, 640, A(2, 4), hits=[2, 4], both=True)
    add("wb_knell", wb_knell, 320, 820, A(4, 5), x0=-8)
    add("wb_back", wb_back, 240, 620, A(4, 5), x0=-6)
    add("wb_kwind", wb_kwind, settle=False)
    add("wb_slam", wb_slam, 280, 680, A(4, 5))
    add("wb_dslam", wb_dslam, 300, 880, A(3, 8), hits=[3, 8])
    add("wb_toll", wb_toll, 200, 760, A(4, 5))
    add("wb_up", wb_up, 220, 560, A(3, 4), up=True)
    add("wb_peal", wb_peal, 200, 560, A(2, 3))
    add("wb_perform", wb_perform, 300, 900, A(3, 5), both=True)
    add("wb_encore", wb_encore, 260, 800, A(4, 5), hit=[-36, -30, 40, 0])
    add("wb_rollj", wb_rollj, 160, 440, A(2, 3))
    add("wb_rollk", wb_rollk, 260, 640, A(4, 5))
    add("wb_air", wb_air, 180, 420, A(2, 3))
    add("wb_down", wb_down, 100, 300, A(1, 2), down=True)
    add("wb_plunge", wb_plunge, settle=False)
    add("wb_pland", wb_pland, 40, 560, A(1, 2), hit=[-12, -20, 30, 0])
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    mod = sys.modules.get("player_v15_bell")
    fns = dict(GP.ANIMS)
    print(f"{'tag':12} {'frames':>6} {'wind':>5} {'total':>5}   {'spec':>9}   ok")
    for t, (w, tot0) in mod.SPEC.items():
        fr = list(fns[t]())
        ms = [m for _, m in fr]
        act = GP.ACTIVE.get(t)
        wind = sum(ms[:act[0]]) if act else None
        tot = sum(ms)
        print(f"{t:12} {len(fr):6} {wind:>5} {tot:5}   {'%d/%d' % (w, tot0):>9}   {'OK' if (wind, tot) == (w, tot0) else 'MISMATCH'}")
