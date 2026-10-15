"""v13 weapon revamp (docs/WEAPON_REVAMP_CONTRACT.md): new player tags, agent WA1.
register(G) receives the gen_player module (all its helpers: mseq, sw, poses, SH, ...) and returns [(tag, fn, opts)].
Tags registered here are appended to gen_player's ANIMS after every existing tag, so no existing frame index moves.

Timing: every attack is authored to WEAPON_REVAMP.md Part A at speed 1 -- the frames before the first active frame add up to
the table's wind-up, all frames to its total (tm() rescales a hand-timed sequence onto those two numbers). Moves that release a
held charge are timed from the release ("450 charge + 380 / 1100" -> the release tag is 380 / 650; the hold is its own loop).
Loops (holds, walks, spins) start and end on the same pose so they repeat without a seam.

Weapons: Longsword ls_ (longsword), Katana kt_ (katana), Greatsword gs_ (greatsword), Maul ml_ (maul), Sword & Shield sh_
(knight_shield)."""
import math

G = None   # gen_player, set by register()

# (tag, wind-up ms, total ms) -- the spec each attack tag is timed to (printed by `python3 art/player_v13_a.py`)
SPEC = {}


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


def walk_legs(i, n, stride=5.0, lift=2.4, cx=None):
    """Feet of a walk cycle (frame i of n): contact at 0 and n/2, the lifted foot passing at n/4 and 3n/4."""
    cx = G.OX + 14 if cx is None else cx
    t = i / n * 2 * math.pi
    fF = (cx + stride * math.cos(t), 39 - max(0.0, math.sin(t)) * lift)
    fB = (cx + stride * math.cos(t + math.pi), 39 - max(0.0, math.sin(t + math.pi)) * lift)
    dy = 1 if i % (n // 2) == 0 else 0
    return dict(footF=fF, footB=fB, dy=dy)


# =================================================================================================== LONGSWORD
def ls_kc_hold():  # charged overhead (loop): two hands on the hilt, blade cocked far back over the head, coiled on the back foot
    base = dict(dx=-1, dy=1, head_dx=-1, hand=(28, 12), ang=-146, footB=(G.OX + 6, 39), footF=(G.FF[0] + 1, 39))
    return G.mseq([(dict(flow=0.25, flutter=0, **base), 130),
                   (dict(flow=0.3, flutter=1, **{**base, "dy": 2, "hand": (28, 13)}), 130),
                   (dict(flow=0.25, flutter=2, fx=[("glint", "tip")], **{**base, "dy": 2, "hand": (28, 13)}), 130),
                   (dict(flow=0.2, flutter=3, **base), 130)], grip=3.0)


def ls_kc():  # release: rise onto the toes, the blade flashes, then one straight two-handed cleave into the floor
    fr = [(dict(dx=-2, dy=2, head_dx=-1, hand=(27, 12), ang=-152, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.2,
                fx=[("glint", "tip")]), 150),
          (dict(dx=-1, dy=0, hand=(28, 10), ang=-140, footB=(G.OX + 7, 38), flow=0.3, flutter=1, fx=[("flare", "tip", 5)]), 160),
          (dict(dx=0, dy=0, hand=(32, 11), ang=-100, footF=(G.FF[0] + 2, 39), flow=0.6, flutter=2, fx=[G.sw(w=0.3)]), 70),
          (dict(dx=2, dy=1, hand=(38, 20), ang=-18, footF=(G.FF[0] + 3, 39), flow=1.1, flutter=3, fx=[G.sw(w=0.55)]), 45),
          (dict(dx=3, dy=3, head_dy=1, hand=(38, 30), ang=52, footB=(G.OX + 7, 39), footF=(G.FF[0] + 4, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.5), ("dust", 50, 5), ("flare", (50, 37), 6)]), 60),
          (dict(dx=3, dy=4, head_dy=1, hand=(38, 31), ang=56, footB=(G.OX + 7, 39), footF=(G.FF[0] + 4, 39), flow=0.6, flutter=5,
                fx=[("dust", 51, 3)]), 220),
          (dict(dx=1, dy=2, hand=(36, 29), ang=30, footF=(G.FF[0] + 2, 39), flow=0.3), 200)]
    return G.mseq(tm(fr, 380, 650, 3), grip=3.0)


def ls_jjk():  # horizontal slash: wind the blade round to the back hip, then one flat 150-degree sweep across the front
    ARC = dict(sq=0.42, w=0.6)
    fr = [(dict(dx=-1, dy=1, head_dx=-1, hand=(27, 26), ang=178, off=(35, 24), footB=(G.OX + 6, 39), flow=0.3), 150),
          (dict(dx=-2, dy=2, head_dx=-1, hand=(26, 27), ang=174, off=(36, 23), footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39),
                flow=0.2, flutter=1, fx=[("glint", "tip")]), 130),
          (dict(dx=0, dy=2, hand=(32, 27), ang=150, slen=14, off=(31, 25), footF=(G.FF[0] + 2, 39), flow=0.8, flutter=2), 50),
          (dict(dx=2, dy=2, hand=(39, 25), ang=-4, off=(25, 25), footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3,
                fx=[("arc", (29, 26), 176, -4, ARC)]), 50),
          (dict(dx=2, dy=1, hand=(39, 21), ang=-38, off=(25, 24), footF=(G.FF[0] + 3, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.45)]), 60),
          (dict(dx=2, dy=1, hand=(36, 16), ang=-80, off=(26, 25), footF=(G.FF[0] + 2, 39), flow=0.7, flutter=5), 110),
          (dict(dx=1, hand=(35, 24), ang=-60, off=(30, 26), flow=0.3), 90)]
    return G.mseq(tm(fr, 330, 640, 3))


def ls_jjjk():  # heavy poke: sink low with the off hand along the flat, then a long lunging two-handed thrust that runs through
    fr = [(dict(dx=-2, dy=2, hand=(28, 26), ang=-3, off=(24, 27), footB=(G.OX + 5, 39), flow=0.3), 120),
          (dict(dx=-3, dy=4, head_dx=-1, head_dy=1, hand=(26, 27), ang=-2, off=(22, 28), footB=(G.OX + 3, 39), footF=(G.OX + 18, 39),
                flow=0.2, flutter=1, fx=[("glint", "tip")]), 180),
          (dict(dx=1, dy=2, hand=(33, 26), ang=-1, off=(28, 27), footB=(G.OX + 6, 38), footF=(G.OX + 23, 38), flow=1.2, flutter=2,
                fx=[("speed", (20, 17), 4, 10)]), 50),
          (dict(dx=4, dy=2, hand=(43, 26), ang=0, off=(37, 26), footB=(G.OX + 9, 39), footF=(G.OX + 27, 39), flow=1.6, flutter=3,
                fx=[("streak", 24)]), 50),
          (dict(dx=5, dy=3, head_dy=1, hand=(44, 26), ang=1, off=(38, 27), footB=(G.OX + 10, 39), footF=(G.OX + 28, 39), flow=1.4,
                flutter=4, fx=[("streak", 12), ("flare", "tip", 5)]), 60),
          (dict(dx=5, dy=3, head_dy=1, hand=(43, 27), ang=2, off=(37, 27), footB=(G.OX + 10, 39), footF=(G.OX + 28, 39), flow=0.9,
                flutter=5), 120),
          (dict(dx=3, dy=1, hand=(39, 26), ang=-12, off=(31, 26), footF=(G.OX + 24, 39), flow=0.5, flutter=6), 110),
          (dict(dx=1, hand=(35, 27), ang=-40, off=(30, 26), flow=0.3), 100)]
    return G.mseq(tm(fr, 350, 680, 3))


def ls_quick():  # roll -> J: out of the roll's crouch, the blade comes up from behind the heel in one rising cut
    fr = [(dict(dx=-1, dy=3, hand=(30, 31), ang=165, off=(33, 27), footB=(G.OX + 6, 39), footF=(G.OX + 20, 39), flow=0.8), 80),
          (dict(dx=1, dy=3, hand=(34, 31), ang=115, off=(31, 27), footB=(G.OX + 7, 39), footF=(G.OX + 21, 39), flow=1.0, flutter=1,
                fx=[G.sw(w=0.3)]), 60),
          (dict(dx=3, dy=1, hand=(40, 24), ang=-22, off=(26, 25), footB=(G.OX + 8, 39), footF=(G.OX + 24, 39), flow=1.3, flutter=2,
                fx=[G.sw(w=0.55)]), 45),
          (dict(dx=3, dy=0, hand=(37, 16), ang=-72, off=(26, 25), footB=(G.OX + 8, 38), footF=(G.OX + 23, 39), flow=1.1, flutter=3,
                fx=[G.sw(w=0.45)]), 55),
          (dict(dx=2, hand=(34, 15), ang=-105, off=(28, 25), footF=(G.OX + 22, 39), flow=0.6, flutter=4), 110),
          (dict(dx=1, hand=(35, 25), ang=-60, off=(30, 26), flow=0.3), 100)]
    return G.mseq(tm(fr, 140, 400, 2))


def ls_step():  # step slash: glide forward low (no roll), the blade drawn back flat, then a level cut as you arrive
    fr = [(dict(dx=-1, dy=2, hand=(29, 25), ang=-175, off=(35, 24), footB=(G.OX + 6, 39), flow=0.4), 60),
          (dict(dx=3, dy=3, head_dx=1, hand=(30, 25), ang=-178, off=(38, 24), footB=(G.OX + 5, 37), footF=(G.OX + 26, 39), flow=1.8,
                flutter=1, fx=[("speed", (18, 18), 5, 16)]), 100),
          (dict(dx=4, dy=2, hand=(41, 24), ang=-3, off=(30, 25), footB=(G.OX + 10, 39), footF=(G.OX + 26, 39), flow=1.5, flutter=2,
                fx=[("arc", (33, 25), 178, -3, dict(sq=0.38, w=0.5))]), 50),
          (dict(dx=4, dy=2, hand=(41, 22), ang=-28, off=(30, 25), footB=(G.OX + 10, 39), footF=(G.OX + 26, 39), flow=1.2, flutter=3,
                fx=[G.sw(w=0.4)]), 60),
          (dict(dx=3, dy=1, hand=(39, 20), ang=-50, off=(29, 25), footF=(G.OX + 24, 39), flow=0.7, flutter=4), 100),
          (dict(dx=1, hand=(35, 26), ang=-50, off=(30, 26), flow=0.3), 90)]
    return G.mseq(tm(fr, 160, 420, 2))




def ls_fore_stance():  # foresight: the blade raised upright before the visor in both hands, knees bent, utterly still
    st = dict(dx=-1, dy=2, hand=(34, 24), ang=-90, footB=(G.OX + 6, 39), footF=(G.FF[0] + 1, 39))
    return G.mseq([(dict(flow=0.4, **{**st, "dy": 1, "hand": (34, 25)}), 60),
                   (dict(flow=0.25, flutter=1, fx=[("glint", (37, 6))], **st), 170),
                   (dict(flow=0.2, flutter=2, **st), 170)], grip=3.0)


def ls_fore_cut():  # the answer: a sidelong step through the blow and one falling diagonal cut, flaring
    fr = [(dict(dx=-1, dy=2, hand=(33, 18), ang=-118, footB=(G.OX + 6, 39), flow=0.6), 50),
          (dict(dx=1, dy=1, hand=(33, 13), ang=-120, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=1, fx=[G.sw(w=0.3)]), 50),
          (dict(dx=4, dy=2, hand=(41, 21), ang=-20, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.5, flutter=2,
                fx=[G.sw(w=0.6), ("flare", (50, 18), 6)]), 45),
          (dict(dx=4, dy=3, head_dy=1, hand=(40, 30), ang=46, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.3, flutter=3,
                fx=[G.sw(w=0.5)]), 60),
          (dict(dx=4, dy=3, head_dy=1, hand=(39, 31), ang=64, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=0.8, flutter=4), 170),
          (dict(dx=2, dy=1, hand=(37, 28), ang=20, footF=(G.OX + 22, 39), flow=0.4, flutter=5), 110),
          (dict(dx=1, hand=(35, 26), ang=-35, flow=0.3), 90)]
    return G.mseq(tm(fr, 100, 560, 2), grip=3.0)


def ls_pommel():  # pommel strike: the blade turned back over the arm, both fists drive the pommel into the foe's guard
    fr = [(dict(dx=-1, dy=1, hand=(32, 24), ang=-150, off=(29, 25), flow=0.3), 110),
          (dict(dx=-2, dy=2, head_dx=-1, hand=(29, 24), ang=-160, off=(26, 25), footB=(G.OX + 5, 39), flow=0.2, flutter=1), 190),
          (dict(dx=3, dy=1, hand=(42, 22), ang=-168, off=(39, 23), footB=(G.OX + 8, 39), footF=(G.OX + 24, 39), flow=1.4, flutter=2,
                fx=[("speed", (24, 18), 4, 12), ("flare", (46, 21), 6)]), 50),
          (dict(dx=3, dy=1, hand=(42, 22), ang=-166, off=(39, 23), footB=(G.OX + 8, 39), footF=(G.OX + 24, 39), flow=1.0, flutter=3,
                fx=[("flare", (46, 21), 3)]), 80),
          (dict(dx=2, hand=(37, 23), ang=-120, off=(33, 24), footF=(G.OX + 22, 39), flow=0.6, flutter=4), 120),
          (dict(dx=1, hand=(35, 26), ang=-60, off=(31, 26), flow=0.3), 100)]
    return G.mseq(tm(fr, 300, 650, 2))


# =================================================================================================== KATANA
SILVER = ((236, 242, 255), (170, 182, 214), (96, 106, 140))   # the perfect-dodge afterimage
SHEATHED = dict(hand=(30, 29), ang=168, off=(32, 28), sheath=True)   # hand on the hilt at the left hip, scabbard angled back


def kt_sheathe():  # chiburi flick, the blade swept back across the body and slid home; a glint at the mouth as it clicks shut
    return G.mseq([(dict(dx=1, hand=(39, 28), ang=34, off=(31, 26), footF=(G.FF[0] + 1, 39), flow=0.5, fx=[G.sw(w=0.3)]), 60),
                   (dict(dx=0, dy=1, hand=(33, 24), ang=-176, off=(31, 27), flow=0.4, flutter=1), 70),
                   (dict(dy=1, hand=(31, 27), ang=172, off=(32, 28), flow=0.3, flutter=2, sheath=True), 80),
                   (dict(dy=1, flow=0.2, flutter=3, fx=[("glint", (32, 30))], **SHEATHED), 90)])


def kt_sheathed_idle():  # sheathed (loop): weight low, the right hand resting on the hilt
    return G.mseq([(dict(dy=dy, flow=0.2 + 0.05 * i, flutter=i, footB=(G.OX + 7, 39), footF=(G.FF[0] + 1, 39), **SHEATHED), 160)
                   for i, dy in enumerate((1, 1, 2, 2))])


def kt_sheathed_walk():  # sheathed (loop): a measured stalking walk (70% speed), hand never leaving the hilt
    out = []
    n = 8
    for i in range(n):
        lg = walk_legs(i, n, stride=5.5, lift=3.0)
        out.append((dict(flow=0.5 + 0.15 * math.sin(i / n * 4 * math.pi), flutter=i, head_dx=0, **lg, **SHEATHED), 100))
    return G.mseq(out)


def kt_iai():  # Iai draw: thumb pops the guard, one flash of a draw-cut, held high, done
    fr = [(dict(dy=2, flow=0.3, fx=[("glint", (32, 30))], footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39), **SHEATHED), 50),
          (dict(dx=1, dy=2, hand=(35, 27), ang=-172, off=(31, 28), footB=(G.OX + 7, 39), footF=(G.OX + 23, 39), flow=1.0, flutter=1), 40),
          (dict(dx=3, dy=2, hand=(41, 25), ang=-5, off=(24, 27), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=2,
                fx=[("flash", 27, 4, 62), ("arc", (31, 27), 172, -5, dict(sq=0.35, w=0.3))]), 45),
          (dict(dx=3, dy=2, hand=(41, 21), ang=-36, off=(24, 27), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.3, flutter=3,
                fx=[("flash", 27, 14, 52), G.sw(w=0.35)]), 55),
          (dict(dx=3, dy=2, hand=(40, 18), ang=-50, off=(24, 27), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=0.8, flutter=4), 180),
          (dict(dx=1, dy=1, hand=(37, 27), ang=30, off=(29, 27), footF=(G.OX + 22, 39), flow=0.4, flutter=5), 150)]
    return G.mseq(tm(fr, 90, 520, 2))




def kt_focus_hold():  # focus (loop): sunk into a deep iaido crouch, the guard thumbed loose; a glint breathes at the mouth
    st = dict(dx=-1, dy=5, head_dy=1, footB=(G.OX + 4, 39), footF=(G.OX + 21, 39), **SHEATHED)
    return G.mseq([(dict(flow=0.15, flutter=0, **st), 120),
                   (dict(flow=0.1, flutter=1, fx=[("glint", (31, 32))], **st), 120),
                   (dict(flow=0.15, flutter=2, **{**st, "head_dy": 2}), 120)])


def kt_focus():  # focus draw: from the crouch a dash clean through the foe -- the cut is a line left hanging in the air
    dash = dict(dy=4, head_dx=1, footB=(G.OX + 3, 37), footF=(G.OX + 27, 39))
    fr = [(dict(dx=-1, dy=5, head_dy=1, footB=(G.OX + 4, 39), footF=(G.OX + 21, 39), flow=0.1, fx=[("glint", (31, 32))],
                **SHEATHED), 60),
          (dict(dx=2, hand=(35, 28), ang=-174, off=(33, 29), flow=1.8, flutter=1, fx=[("speed", (20, 21), 5, 18)], **dash), 60),
          (dict(dx=4, hand=(40, 26), ang=-4, off=(26, 28), flow=2.0, flutter=2,
                fx=[("flash", 29, 0, 63), ("arc", (32, 29), 174, -4, dict(sq=0.3, w=0.3)), ("speed", (20, 21), 5, 20)], **dash), 45),
          (dict(dx=4, dy=4, hand=(33, 30), ang=172, slen=17, off=(37, 28), footB=(G.OX + 8, 39), footF=(G.OX + 26, 39), flow=1.6,
                flutter=3, fx=[("flash", 29, 0, 40), G.sw(w=0.3)]), 60),
          (dict(dx=3, dy=4, head_dy=1, hand=(32, 31), ang=168, off=(37, 28), footB=(G.OX + 8, 39), footF=(G.OX + 26, 39), flow=1.0,
                flutter=4, fx=[("flash", 29, 0, 22)]), 160),
          (dict(dx=1, dy=2, hand=(35, 28), ang=20, off=(31, 27), footF=(G.OX + 22, 39), flow=0.4, flutter=5), 140)]
    return G.mseq(tm(fr, 120, 500, 2))


def kt_iai_parry():  # Iai parry: an inch of steel catches the blow at the guard (spark), then the draw answers it
    fr = [(dict(dy=2, flow=0.3, footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39), **SHEATHED), 40),
          (dict(dx=-1, dy=2, hand=(33, 26), ang=-150, slen=9, off=(31, 28), footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.6,
                flutter=1, fx=[("flare", (38, 21), 6)]), 110),
          (dict(dx=0, dy=3, hand=(32, 29), ang=170, off=(32, 28), footB=(G.OX + 5, 39), footF=(G.OX + 21, 39), flow=0.4, flutter=2,
                sheath=True, fx=[("glint", (32, 30))]), 50),
          (dict(dx=3, dy=2, hand=(41, 24), ang=-8, off=(24, 27), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=3,
                fx=[("flash", 26, 4, 62), ("arc", (31, 27), 170, -8, dict(sq=0.38, w=0.35))]), 45),
          (dict(dx=3, dy=1, hand=(40, 17), ang=-58, off=(24, 27), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.3, flutter=4,
                fx=[("flash", 26, 16, 50), G.sw(w=0.4)]), 55),
          (dict(dx=3, dy=1, hand=(38, 15), ang=-80, off=(25, 26), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=0.8, flutter=5), 170),
          (dict(dx=1, hand=(36, 26), ang=-45, off=(30, 26), flow=0.3), 130)]
    return G.mseq(tm(fr, 200, 600, 3))


def kt_sidestep():  # sidestep: a low gliding shuffle, the body leaves a pale afterimage behind
    blade = dict(hand=(33, 30), ang=150, off=(30, 27))
    return G.mseq([(dict(dy=2, flow=0.4, footB=(G.OX + 7, 39), **blade), 40),
                   (dict(dx=2, dy=3, head_dx=1, footB=(G.OX + 6, 38), footF=(G.OX + 24, 39), flow=1.5, flutter=1,
                         fx=[("ghost", -6, 1, SILVER), ("speed", (18, 20), 4, 12)], **blade), 70),
                   (dict(dx=2, dy=3, footB=(G.OX + 10, 39), footF=(G.OX + 22, 39), flow=1.0, flutter=2, fx=[("ghost", -10, 2, SILVER)], **blade), 70),
                   (dict(dx=1, dy=1, footF=(G.FF[0] + 1, 39), flow=0.5, flutter=3, **{**blade, "hand": (34, 29), "ang": 120}), 80)])


def kt_stepcut():  # step cut: out of the sidestep's crouch, a flat cut at the waist and a flick upward
    fr = [(dict(dx=1, dy=3, hand=(32, 30), ang=158, off=(31, 27), footB=(G.OX + 7, 39), footF=(G.OX + 22, 39), flow=0.8), 60),
          (dict(dx=2, dy=2, hand=(35, 29), ang=-176, off=(30, 27), footB=(G.OX + 8, 39), footF=(G.OX + 23, 39), flow=1.0, flutter=1), 60),
          (dict(dx=3, dy=2, hand=(40, 25), ang=-6, off=(25, 26), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.3, flutter=2,
                fx=[("arc", (30, 27), 176, -6, G.KARC)]), 45),
          (dict(dx=3, dy=1, hand=(39, 19), ang=-48, off=(25, 26), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.1, flutter=3,
                fx=[G.sw(w=0.35)]), 55),
          (dict(dx=2, hand=(36, 16), ang=-82, off=(27, 25), footF=(G.OX + 23, 39), flow=0.6, flutter=4), 90),
          (dict(dx=1, hand=(35, 26), ang=-45, off=(30, 26), flow=0.3), 90)]
    return G.mseq(tm(fr, 120, 360, 2))


def kt_flurry():  # triple flurry: falling cut, rising cut, a flat finishing cut -- three strokes in one breath
    fr = [(dict(dx=-1, dy=1, hand=(30, 17), ang=-128, flow=0.3), 90),
          (dict(dx=0, dy=1, hand=(32, 14), ang=-112, footB=(G.OX + 7, 39), flow=0.5, flutter=1), 90),
          # 1: falling diagonal
          (dict(dx=2, dy=2, hand=(39, 24), ang=10, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=2, fx=[G.sw(w=0.4)]), 50),
          (dict(dx=2, dy=2, hand=(36, 30), ang=128, slen=15, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=3), 50),
          # 2: rising diagonal
          (dict(dx=3, dy=1, hand=(39, 20), ang=-48, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=4, fx=[G.sw(w=0.4)]), 50),
          (dict(dx=2, dy=1, hand=(30, 22), ang=-172, slen=15, footF=(G.FF[0] + 3, 39), flow=1.1, flutter=5), 50),
          # 3: flat finishing cut
          (dict(dx=4, dy=2, hand=(41, 24), ang=-3, footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.4, flutter=6,
                fx=[("arc", (30, 25), 178, -3, G.KARC)]), 50),
          (dict(dx=4, dy=2, hand=(40, 21), ang=-30, footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=1.0, flutter=7,
                fx=[G.sw(w=0.35)]), 70),
          (dict(dx=1, hand=(35, 26), ang=-45, flow=0.3), 100)]
    return G.mseq(tm(fr, 180, 600, 2), grip=G.GRIP_KATANA)


def kt_rush():  # rushing draw (K while drawn): dash in low, one rising cut, flick the blood off and slide it home -- sheathed again
    fr = [(dict(dx=-1, dy=2, hand=(31, 29), ang=160, off=(31, 27), footB=(G.OX + 6, 39), flow=0.4), 110),
          (dict(dx=-2, dy=4, head_dy=1, hand=(29, 30), ang=166, off=(30, 28), footB=(G.OX + 4, 39), footF=(G.OX + 19, 39), flow=0.3,
                flutter=1, fx=[("glint", "tip")]), 90),
          (dict(dx=3, dy=3, head_dx=1, hand=(34, 30), ang=150, off=(33, 28), footB=(G.OX + 4, 37), footF=(G.OX + 27, 39), flow=1.8,
                flutter=2, fx=[("speed", (20, 20), 5, 16)]), 60),
          (dict(dx=4, dy=2, hand=(41, 23), ang=-24, off=(26, 26), footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.6, flutter=3,
                fx=[G.sw(w=0.5), ("speed", (20, 20), 4, 12)]), 45),
          (dict(dx=4, dy=1, hand=(38, 15), ang=-76, off=(26, 25), footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.4)]), 60),
          (dict(dx=3, dy=1, hand=(40, 28), ang=34, off=(28, 26), footB=(G.OX + 9, 39), footF=(G.OX + 25, 39), flow=0.7, flutter=5,
                fx=[G.sw(w=0.25)]), 90),
          (dict(dx=2, dy=2, hand=(32, 25), ang=-178, off=(31, 27), footF=(G.OX + 23, 39), flow=0.4, flutter=6), 70),
          (dict(dx=1, dy=1, flow=0.3, flutter=7, fx=[("glint", (32, 30))], footF=(G.OX + 21, 39), **SHEATHED), 95)]
    return G.mseq(tm(fr, 260, 620, 3))


def kt_flash():  # flash step: gone from the crouch, there is only a line -- and you stand beyond it, blade out behind
    fr = [(dict(dx=-1, dy=4, head_dy=1, footB=(G.OX + 5, 39), footF=(G.OX + 21, 39), flow=0.2, fx=[("glint", (31, 31))], **SHEATHED), 60),
          (dict(dx=3, dy=4, head_dx=1, hand=(36, 28), ang=-174, off=(34, 29), footB=(G.OX + 3, 37), footF=(G.OX + 28, 39), flow=2.0,
                flutter=1, fx=[("ghost", -12, 2, SILVER), ("speed", (22, 20), 6, 22)]), 40),
          (dict(dx=4, dy=4, head_dy=1, hand=(32, 30), ang=170, off=(37, 28), footB=(G.OX + 8, 39), footF=(G.OX + 26, 39), flow=1.8,
                flutter=2, fx=[("flash", 28, 0, 63), ("flash", 22, 6, 30), ("speed", (12, 21), 5, 12)]), 50),
          (dict(dx=4, dy=4, head_dy=1, hand=(32, 31), ang=168, off=(37, 28), footB=(G.OX + 8, 39), footF=(G.OX + 26, 39), flow=1.1,
                flutter=3, fx=[("flash", 28, 0, 30)]), 150),
          (dict(dx=1, dy=2, hand=(35, 28), ang=20, off=(31, 27), footF=(G.OX + 22, 39), flow=0.4, flutter=4), 120)]
    return G.mseq(tm(fr, 100, 420, 2))


# =================================================================================================== GREATSWORD


def _gs_hold(dy=3, **k):
    return dict(dx=-2, dy=dy, head_dx=-1, hand=(27, 14 + max(0, dy - 3)), ang=-150, footB=(G.OX + 5, 39),
                footF=(G.FF[0] + 2, 39), **k)


def gs_charge_hold():  # charge (loop): the blade laid back over the shoulder, sunk into a wide stance, breathing
    return G.mseq([(dict(flow=0.2, flutter=0, **_gs_hold(3)), 130),
                   (dict(flow=0.25, flutter=1, **_gs_hold(4)), 130),
                   (dict(flow=0.2, flutter=2, **_gs_hold(4)), 130),
                   (dict(flow=0.15, flutter=3, **_gs_hold(3)), 130)], grip=G.GRIP_GREAT)


def _gs_cleave(step, dust=7, flare=None, pal=None, hard=True):
    """Shared shape of the charged cleaves: heave, pivot, strike, bury, hold, rise (6 frames, hit on 2)."""
    s = step
    ex = dict(fx_pal=pal) if pal else {}
    imp = [G.sw(w=0.5), ("dust", 48 + s, dust)] + ([("flare", (49 + s, 35), flare)] if flare else [])
    return [(dict(dx=-2, dy=2, head_dx=-1, hand=(27, 12), ang=-152, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.3,
                  **ex), 90),
            (dict(dx=0 + s // 3, dy=0, hand=(31, 12), ang=-104, footF=(G.FF[0] + 2 + s // 2, 39), flow=0.8, flutter=1,
                  fx=[G.sw(w=0.35)], **ex), 110),
            (dict(dx=2 + s // 2, dy=2, hand=(38, 21), ang=-16, slen=15, footF=(G.FF[0] + 3 + s, 39), flow=1.2, flutter=2,
                  fx=[G.sw(w=0.55)], **ex), 50),
            (dict(dx=3 + s // 2, dy=5, head_dy=1, hand=(37, 30), ang=48, slen=16, footB=(G.OX + 6 + s // 2, 39),
                  footF=(G.FF[0] + 4 + s, 39), flow=1.3, flutter=3, fx=imp, **ex), 60),
            (dict(dx=3 + s // 2, dy=6 if hard else 5, head_dy=1, hand=(37, 31), ang=52, footB=(G.OX + 6 + s // 2, 39),
                  footF=(G.FF[0] + 4 + s, 39), flow=0.6, flutter=4, fx=[("dust", 49 + s, dust // 2)], **ex), 200),
            (dict(dx=1, dy=3, hand=(35, 29), ang=35, footF=(G.FF[0] + 2, 39), flow=0.3, flutter=5), 180)]


def gs_charged():  # charged slash: out of the shoulder rest, one hammering vertical cleave into the floor
    return G.mseq(tm(_gs_cleave(0, dust=6), 200, 500, 2), grip=G.GRIP_GREAT)


def gs_strong():  # strong charged slash: a full pivot -- the body wheels round with the blade, then it comes over and down, flaring
    ARC = dict(sq=0.38, w=0.5)
    fr = _gs_cleave(5, dust=10, flare=8)
    pivot = (dict(dx=1, dy=3, hand=(37, 26), ang=-6, footF=(G.FF[0] + 2, 39), flow=1.4, flutter=1, mirror=True, behind=True,
                  fx=[("arc", (29, 27), 10, -170, ARC)]), 70)
    rise = (dict(dx=1, dy=0, hand=(31, 12), ang=-110, footF=(G.FF[0] + 4, 39), flow=1.0, flutter=2,
                 fx=[("speed", (20, 14), 3, 10)]), 60)
    fr = [fr[0], pivot, rise] + fr[2:]
    return G.mseq(tm(fr, 220, 560, 3), grip=G.GRIP_GREAT)


def gs_true1():  # true charged slash I: a fast rising backhand that whips the blade round and back onto the shoulder
    fr = [(dict(dx=0, dy=3, hand=(34, 30), ang=60, footF=(G.FF[0] + 2, 39), flow=0.4), 90),
          (dict(dx=1, dy=3, hand=(37, 30), ang=30, footF=(G.FF[0] + 3, 39), flow=0.8, flutter=1, fx=[G.sw(w=0.3)]), 90),
          (dict(dx=2, dy=1, hand=(39, 22), ang=-40, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=2, fx=[G.sw(w=0.55)]), 50),
          (dict(dx=1, dy=0, hand=(33, 13), ang=-110, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3, fx=[G.sw(w=0.5)]), 60),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(27, 13), ang=-160, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.6,
                flutter=4, fx=[G.sw(w=0.3)]), 110),
          (dict(flow=0.3, flutter=5, **_gs_hold(3)), 120)]
    return G.mseq(tm(fr, 180, 480, 2), grip=G.GRIP_GREAT)


def gs_true2():  # true charged slash II: a leaping heave with the blade blazing, brought down with everything -- the ground splits
    fr = [(dict(dx=-2, dy=4, head_dx=-1, hand=(27, 14), ang=-152, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.2,
                fx=[("glint", "tip")]), 110),
          (dict(dx=-1, dy=-2, hand=(28, 10), ang=-150, footB=(G.OX + 8, 37), footF=(G.FF[0] + 2, 38), flow=0.6, flutter=1), 100),
          (dict(dx=2, dy=-2, hand=(33, 10), ang=-96, footB=(G.OX + 9, 37), footF=(G.FF[0] + 4, 38), flow=1.0, flutter=2,
                fx=[G.sw(w=0.35)]), 50),
          (dict(dx=4, dy=2, hand=(40, 21), ang=-14, slen=15, footF=(G.FF[0] + 6, 39), flow=1.4, flutter=3, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=5, dy=6, head_dy=1, hand=(38, 31), ang=52, slen=16, footB=(G.OX + 8, 39), footF=(G.FF[0] + 7, 39), flow=1.5,
                flutter=4, fx=[G.sw(w=0.55), ("dust", 53, 11), ("flare", (53, 34), 10)]), 70),
          (dict(dx=5, dy=7, head_dy=2, hand=(38, 31), ang=55, footB=(G.OX + 8, 39), footF=(G.FF[0] + 7, 39), flow=0.8, flutter=5,
                fx=[("dust", 53, 6), ("flare", (53, 36), 5)]), 220),
          (dict(dx=4, dy=6, head_dy=1, hand=(38, 31), ang=55, footB=(G.OX + 8, 39), footF=(G.FF[0] + 7, 39), flow=0.5, flutter=6), 160),
          (dict(dx=2, dy=3, hand=(36, 29), ang=36, footF=(G.FF[0] + 3, 39), flow=0.3, flutter=7), 180)]
    return G.mseq(tm(fr, 260, 800, 3), grip=G.GRIP_GREAT)


def gs_guard():  # blade guard (loop): the slab driven point-down into the floor before you, both fists on the hilt, sheltering behind it
    st = dict(dx=-1, dy=3, head_dx=-1, hand=(40, 17), ang=90, sword=False, planted=(39, 20), off=(37, 21),
              footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39))
    return G.mseq([(dict(flow=0.25, flutter=0, **st), 220),
                   (dict(flow=0.2, flutter=1, **{**st, "dy": 4, "hand": (40, 16)}), 220)])


def gs_tackle():  # shoulder tackle: the charge kept on the shoulder, the pauldron driven into the foe
    fr = [(dict(dx=0, dy=3, head_dx=1, hand=(28, 15), ang=-150, footB=(G.OX + 5, 39), footF=(G.FF[0] + 3, 39), flow=0.6), 90),
          (dict(dx=4, dy=3, head_dx=2, hand=(31, 15), ang=-150, footB=(G.OX + 7, 39), footF=(G.OX + 27, 39), flow=1.6, flutter=1,
                fx=[("speed", (20, 16), 5, 14), ("flare", (47, 22), 6)]), 60),
          (dict(dx=4, dy=3, head_dx=2, hand=(31, 15), ang=-150, footB=(G.OX + 9, 39), footF=(G.OX + 27, 39), flow=1.2, flutter=2,
                fx=[("flare", (46, 22), 3)]), 60),
          (dict(flow=0.4, flutter=3, **_gs_hold(3)), 90)]
    return G.mseq(tm(fr, 90, 300, 1), grip=G.GRIP_GREAT)


def gs_rollheavy():  # rolling heavy: rising out of the roll's crouch the blade comes over in one swing (banked charge)
    fr = [(dict(dx=-1, dy=4, head_dy=1, hand=(30, 31), ang=158, footB=(G.OX + 6, 39), footF=(G.OX + 21, 39), flow=0.9), 80),
          (dict(dx=-1, dy=1, head_dx=-1, hand=(28, 13), ang=-150, footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39), flow=0.6, flutter=1), 70),
          (dict(dx=1, dy=0, hand=(32, 12), ang=-100, footF=(G.FF[0] + 3, 39), flow=0.9, flutter=2, fx=[G.sw(w=0.35)]), 60),
          (dict(dx=3, dy=2, hand=(38, 21), ang=-16, slen=15, footF=(G.FF[0] + 4, 39), flow=1.2, flutter=3, fx=[G.sw(w=0.55)]), 50),
          (dict(dx=3, dy=5, head_dy=1, hand=(37, 30), ang=48, slen=16, footB=(G.OX + 7, 39), footF=(G.FF[0] + 4, 39), flow=1.2,
                flutter=4, fx=[G.sw(w=0.5), ("dust", 50, 6)]), 60),
          (dict(dx=3, dy=5, head_dy=1, hand=(37, 31), ang=52, footB=(G.OX + 7, 39), footF=(G.FF[0] + 4, 39), flow=0.6, flutter=5,
                fx=[("dust", 51, 3)]), 200),
          (dict(dx=1, dy=3, hand=(35, 29), ang=35, footF=(G.FF[0] + 2, 39), flow=0.3, flutter=6), 170)]
    return G.mseq(tm(fr, 220, 600, 3), grip=G.GRIP_GREAT)


def gs_wrath():  # wrath charge: the blade runs red-hot from the hilt, the cleave bursts into flame where it lands
    E = G.EMBER
    fr = _gs_cleave(5, dust=9, flare=10, pal=E[:3])
    for i, (p, _) in enumerate(fr[:5]):
        p["heat"] = (0, 40)
    fr[3][0]["fx"] = fr[3][0]["fx"] + [("embers", (50, 30), 8, 1)]
    fr[4][0]["fx"] = fr[4][0]["fx"] + [("flare", (51, 35), 7, E[:3]), ("embers", (49, 28), 9, 2)]
    return G.mseq(tm(fr, 220, 640, 2), grip=G.GRIP_GREAT)


# =================================================================================================== MAUL
GRIP_MAUL = 4.0


def _mlow(**k):   # walk-charge carry: leaning in, the hammer dragged low behind the heel in both hands
    d = dict(dx=1, dy=3, head_dx=1, hand=(29, 26), ang=166, slen=18)
    d.update(k)
    return d


def ml_1():  # overhead smash: the hammer goes up over the back and comes straight down in front, the floor jumps
    fr = [(dict(dy=1, hand=(32, 21), ang=-100, flow=0.3), 90),
          (dict(dx=-1, dy=0, head_dx=-1, hand=(29, 12), ang=-150, footB=(G.OX + 6, 39), flow=0.3, flutter=1), 110),
          (dict(dx=-1, dy=-1, head_dx=-1, hand=(29, 10), ang=-170, footB=(G.OX + 6, 38), flow=0.2, flutter=2), 60),
          (dict(dx=1, dy=0, hand=(33, 12), ang=-92, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=3, fx=[G.sw(w=0.4)]), 45),
          (dict(dx=2, dy=3, hand=(38, 22), ang=10, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=4, fx=[G.sw(w=0.55)]), 45),
          (dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=78, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=1.1, flutter=5,
                fx=[G.sw(w=0.4), ("dust", 38, 7), ("flare", (38, 37), 5)]), 60),
          (dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=80, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=6,
                fx=[("dust", 38, 3)]), 200),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=7), 150)]
    return G.mseq(tm(fr, 260, 620, 4), grip=GRIP_MAUL)


def ml_2():  # overhead smash II: a windmill -- the hammer swung up from behind the heel, over the top and down again
    RG = dict(sq=1.0, w=3.0)
    fr = [(dict(dx=-1, dy=2, hand=(29, 30), ang=150, footB=(G.OX + 6, 39), flow=0.4, fx=[("dust", 12, 2)]), 100),
          (dict(dx=-1, dy=0, head_dx=-1, hand=(27, 20), ang=-150, footB=(G.OX + 6, 39), flow=0.6, flutter=1,
                fx=[("ring", (29, 22), 13, 160, 210, RG)]), 90),
          (dict(dx=0, dy=-1, hand=(31, 11), ang=-110, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=2,
                fx=[("ring", (29, 22), 13, 200, 250, RG)]), 70),
          (dict(dx=2, dy=2, hand=(38, 20), ang=-10, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3, fx=[G.sw(w=0.55)]), 45),
          (dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=80, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.45), ("dust", 38, 7), ("flare", (38, 37), 5)]), 60),
          (dict(dx=2, dy=5, head_dy=1, hand=(37, 27), ang=82, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=5,
                fx=[("dust", 38, 3)]), 200),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=6), 150)]
    return G.mseq(tm(fr, 260, 620, 3), grip=GRIP_MAUL)


def ml_3():  # upswing: the head scrapes the floor behind you, then a golf-swing heave that lifts you onto your toes
    fr = [(dict(dx=-1, dy=3, hand=(28, 31), ang=162, footB=(G.OX + 6, 39), flow=0.3, fx=[("dust", 10, 2)]), 120),
          (dict(dx=-2, dy=4, head_dx=-1, head_dy=1, hand=(27, 31), ang=168, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.2,
                flutter=1, fx=[("dust", 8, 3), ("glint", (16, 35))]), 120),
          (dict(dx=1, dy=3, hand=(33, 32), ang=120, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=2, fx=[G.sw(w=0.4), ("dust", 26, 3)]), 60),
          (dict(dx=2, dy=0, hand=(39, 25), ang=-30, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=3, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=2, dy=-2, hand=(36, 14), ang=-84, footB=(G.OX + 9, 37), footF=(G.FF[0] + 3, 38), flow=1.3, flutter=4,
                fx=[G.sw(w=0.5)]), 60),
          (dict(dx=1, dy=-1, hand=(31, 13), ang=-122, footB=(G.OX + 9, 38), footF=(G.FF[0] + 2, 39), flow=0.8, flutter=5), 180),
          (dict(dx=0, dy=1, hand=(31, 18), ang=-140, flow=0.4, flutter=6), 150),
          (dict(dy=1, hand=(33, 24), ang=-80, flow=0.3, flutter=7), 120)]
    return G.mseq(tm(fr, 300, 720, 3), grip=GRIP_MAUL)


def ml_charge_idle():  # walk-charge, standing (loop): low and coiled, the hammer drawn back behind the heel
    return G.mseq([(dict(flow=0.3, flutter=i, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), **_mlow(dy=3 + (i in (1, 2)))), 130)
                   for i in range(4)], grip=GRIP_MAUL)


def ml_charge_walk():  # walk-charge (loop): stalking in at 60% speed, the hammer low behind, the head never quite touching
    out = []
    n = 8
    for i in range(n):
        lg = walk_legs(i, n, stride=4.6, lift=2.0)
        dy = 3 + lg.pop("dy")
        out.append((dict(flow=0.6 + 0.2 * math.sin(i / n * 4 * math.pi), flutter=i, **lg, **_mlow(dy=dy)), 110))
    return G.mseq(out, grip=GRIP_MAUL)


def ml_upswing():  # charged upswing: straight out of the carry, an uppercut that rips the hammer from the heel to the sky
    fr = [(dict(dx=1, dy=3, head_dx=1, hand=(29, 26), ang=166, footB=(G.OX + 5, 39), footF=(G.FF[0] + 3, 39), flow=0.5), 70),
          (dict(dx=2, dy=4, hand=(35, 32), ang=110, footF=(G.FF[0] + 3, 39), flow=1.0, flutter=1, fx=[G.sw(w=0.4), ("dust", 30, 3)]), 70),
          (dict(dx=3, dy=1, hand=(40, 25), ang=-28, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=2, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=3, dy=-2, hand=(37, 13), ang=-86, footB=(G.OX + 9, 37), footF=(G.FF[0] + 4, 38), flow=1.4, flutter=3,
                fx=[G.sw(w=0.5)]), 55),
          (dict(dx=2, dy=-1, hand=(32, 12), ang=-118, footB=(G.OX + 9, 38), footF=(G.FF[0] + 3, 39), flow=0.8, flutter=4), 150),
          (dict(dx=1, dy=1, hand=(33, 20), ang=-100, flow=0.4, flutter=5), 130)]
    return G.mseq(tm(fr, 140, 520, 2), grip=GRIP_MAUL)


def ml_double():  # double smash: up and down, up and down -- two hammer blows into the same spot
    def smash(k):
        return [(dict(dx=2 + k, dy=2, hand=(38, 21), ang=-8, footF=(G.FF[0] + 3 + k, 39), flow=1.2, flutter=2 + 4 * k,
                      fx=[G.sw(w=0.55)]), 45),
                (dict(dx=2 + k, dy=5, head_dy=1, hand=(37, 27), ang=80, footB=(G.OX + 6 + k, 39), footF=(G.FF[0] + 3 + k, 39), flow=1.1,
                      flutter=3 + 4 * k, fx=[G.sw(w=0.4), ("dust", 38 + k, 6 + k), ("flare", (38 + k, 37), 4 + k)]), 60)]
    fr = [(dict(dx=1, dy=1, hand=(31, 14), ang=-128, footF=(G.FF[0] + 2, 39), flow=0.5), 80),
          (dict(dx=1, dy=0, hand=(32, 11), ang=-104, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=1, fx=[G.sw(w=0.35)]), 80)] \
        + smash(0) \
        + [(dict(dx=2, dy=4, head_dy=1, hand=(36, 26), ang=70, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=4,
                 fx=[("dust", 38, 3)]), 70),
           (dict(dx=1, dy=0, hand=(31, 12), ang=-130, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=5, fx=[G.sw(w=0.35)]), 90),
           (dict(dx=2, dy=-1, hand=(33, 10), ang=-100, footF=(G.FF[0] + 4, 39), flow=0.9, flutter=6, fx=[G.sw(w=0.35)]), 60)] \
        + smash(1) \
        + [(dict(dx=3, dy=6, head_dy=1, hand=(37, 27), ang=82, footB=(G.OX + 7, 39), footF=(G.FF[0] + 4, 39), flow=0.6, flutter=8,
                 fx=[("dust", 39, 3)]), 200),
           (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=9), 150)]
    # hits on frames 2 and 7: 160 ms to the first, the second lands ~520 ms in; 900 ms in all
    fr = tm(fr, 160, 900, 2)
    return G.mseq(fr, grip=GRIP_MAUL)


def ml_bigsmash():  # big smash: from the low carry the hammer goes all the way round over the top -- a blow that cracks stone
    fr = [(dict(dx=1, dy=3, head_dx=1, hand=(29, 26), ang=166, footB=(G.OX + 5, 39), footF=(G.FF[0] + 3, 39), flow=0.5,
                fx=[("glint", (15, 36))]), 70),
          (dict(dx=0, dy=1, head_dx=-1, hand=(27, 21), ang=-160, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=1,
                fx=[("ring", (29, 22), 13, 150, 205, dict(sq=1.0, w=3.0))]), 70),
          (dict(dx=0, dy=-2, hand=(30, 10), ang=-125, footB=(G.OX + 7, 38), footF=(G.FF[0] + 3, 39), flow=0.8, flutter=2,
                fx=[("ring", (29, 22), 13, 195, 240, dict(sq=1.0, w=3.0))]), 60),
          (dict(dx=1, dy=-2, hand=(32, 9), ang=-100, footB=(G.OX + 7, 38), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=3,
                fx=[("glint", "tip")]), 50),
          (dict(dx=3, dy=2, hand=(39, 21), ang=-6, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=4, fx=[G.sw(w=0.6)]), 40),
          (dict(dx=3, dy=6, head_dy=1, hand=(38, 27), ang=82, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.4, flutter=5,
                fx=[G.sw(w=0.45), ("dust", 39, 11), ("flare", (39, 36), 9), ("rings", (39, 37), (6, 10))]), 70),
          (dict(dx=3, dy=6, head_dy=2, hand=(38, 27), ang=84, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.8, flutter=6,
                fx=[("dust", 39, 6), ("rings", (39, 37), (11, 15))]), 230),
          (dict(dx=2, dy=4, head_dy=1, hand=(37, 27), ang=80, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.5, flutter=7), 150),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=8), 150)]
    return G.mseq(tm(fr, 240, 820, 4), grip=GRIP_MAUL)


SPIN_RG = dict(sq=0.32, w=9.0)


def ml_spin():  # spinning bludgeon (loop): the hammer whirled flat round the waist; one full turn per loop
    ring = lambda a0, a1: ("ring", (31, 28), 20, a0, a1, SPIN_RG)
    st = dict(dy=3, footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39))
    return G.mseq([(dict(dx=1, hand=(36, 28), ang=4, flow=1.2, flutter=0, fx=[ring(180, 4)], **st), 80),
                   (dict(dx=1, hand=(33, 27), ang=-10, slen=10, flow=1.4, flutter=1, mirror=True, behind=True, fx=[ring(180, 0)], **st), 80),
                   (dict(dx=1, hand=(36, 28), ang=4, flow=1.5, flutter=2, mirror=True, behind=True, fx=[ring(180, 4)], **st), 80),
                   (dict(dx=1, hand=(33, 27), ang=-10, slen=10, flow=1.3, flutter=3, fx=[ring(180, 0)], **st), 80)], grip=GRIP_MAUL)


def ml_spin_end():  # spin finisher: the last turn unwinds into a rising blow that throws the hammer at the sky
    fr = [(dict(dx=1, dy=3, hand=(33, 27), ang=-10, slen=10, footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39), flow=1.3, mirror=True,
                behind=True, fx=[("ring", (31, 28), 20, 180, 0, SPIN_RG)]), 70),
          (dict(dx=0, dy=4, head_dx=-1, hand=(29, 31), ang=165, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=1.0, flutter=1,
                fx=[("dust", 14, 3)]), 90),
          (dict(dx=2, dy=2, hand=(39, 26), ang=-22, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=2, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=2, dy=-2, hand=(36, 13), ang=-86, footB=(G.OX + 9, 37), footF=(G.FF[0] + 4, 38), flow=1.4, flutter=3,
                fx=[G.sw(w=0.5), ("flare", (39, 3), 5)]), 60),
          (dict(dx=1, dy=-1, hand=(31, 12), ang=-122, footB=(G.OX + 9, 38), footF=(G.FF[0] + 3, 39), flow=0.8, flutter=4), 200),
          (dict(dx=0, dy=1, hand=(31, 18), ang=-140, flow=0.4, flutter=5), 130),
          (dict(dy=1, hand=(33, 24), ang=-80, flow=0.3, flutter=6), 110)]
    return G.mseq(tm(fr, 160, 700, 2), grip=GRIP_MAUL)


def ml_brace():  # brace: the head set on the floor before you, both fists on the haft, shoulders down -- let it come
    st = dict(dx=0, dy=4, head_dy=1, hand=(36, 24), ang=90, sword=False, planted=(41, 24), off=(34, 27), footB=(G.OX + 4, 39),
              footF=(G.FF[0] + 2, 39))
    return G.mseq([(dict(dy=2, hand=(36, 26), ang=60, footB=(G.OX + 5, 39), flow=0.4, fx=[("dust", 42, 2)]), 80),
                   (dict(flow=0.15, flutter=1, fx=[("dust", 42, 3)], **st), 260),
                   (dict(flow=0.1, flutter=2, **{**st, "dy": 5}), 260),
                   (dict(dx=1, dy=2, hand=(35, 28), ang=40, flow=0.3, flutter=3), 120)])


def ml_rollswing():  # rolling swing: up out of the roll, the hammer swept low-to-high across the front
    fr = [(dict(dx=-1, dy=4, head_dy=1, hand=(30, 31), ang=160, footB=(G.OX + 6, 39), footF=(G.OX + 21, 39), flow=0.9), 100),
          (dict(dx=1, dy=3, hand=(34, 32), ang=118, footF=(G.FF[0] + 3, 39), flow=1.0, flutter=1, fx=[G.sw(w=0.4), ("dust", 28, 3)]), 100),
          (dict(dx=3, dy=1, hand=(40, 25), ang=-20, footF=(G.FF[0] + 4, 39), flow=1.3, flutter=2, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=3, dy=-1, hand=(38, 16), ang=-72, footB=(G.OX + 9, 38), footF=(G.FF[0] + 4, 39), flow=1.2, flutter=3,
                fx=[G.sw(w=0.5)]), 55),
          (dict(dx=2, dy=0, hand=(33, 13), ang=-112, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=4), 130),
          (dict(dx=1, dy=1, hand=(33, 21), ang=-95, flow=0.3, flutter=5), 130)]
    return G.mseq(tm(fr, 200, 560, 2), grip=GRIP_MAUL)


BB_ARC = dict(sq=0.42, w=0.6)


def ml_bb1():  # Big Bang I: a flat hooking swing across the chest
    fr = [(dict(dx=-1, dy=2, head_dx=-1, hand=(28, 26), ang=176, footB=(G.OX + 6, 39), flow=0.3), 110),
          (dict(dx=0, dy=2, hand=(31, 27), ang=160, slen=14, footF=(G.FF[0] + 2, 39), flow=0.8, flutter=1), 90),
          (dict(dx=2, dy=2, hand=(39, 25), ang=-4, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=2,
                fx=[("arc", (29, 26), 176, -4, BB_ARC), ("flare", (52, 22), 4)]), 50),
          (dict(dx=2, dy=2, hand=(37, 23), ang=-40, footF=(G.FF[0] + 3, 39), flow=1.1, flutter=3, fx=[G.sw(w=0.45)]), 60),
          (dict(dx=2, dy=2, hand=(35, 20), ang=-70, footF=(G.FF[0] + 3, 39), flow=0.6, flutter=4), 110),
          (dict(dx=1, dy=1, hand=(34, 22), ang=-60, flow=0.4, flutter=5), 80)]
    return G.mseq(tm(fr, 200, 500, 2), grip=GRIP_MAUL)


def ml_bb2():  # Big Bang II: the backhand return -- turned through, the hammer comes back the other way
    fr = [(dict(dx=1, dy=2, hand=(36, 21), ang=-58, footF=(G.FF[0] + 2, 39), flow=0.5), 100),
          (dict(dx=1, dy=2, hand=(37, 26), ang=-30, slen=12, footF=(G.FF[0] + 2, 39), flow=0.9, flutter=1, mirror=True, behind=True), 100),
          (dict(dx=2, dy=2, hand=(39, 26), ang=-2, footF=(G.FF[0] + 3, 39), flow=1.4, flutter=2,
                fx=[("arc", (29, 26), 176, -2, BB_ARC), ("flare", (52, 24), 4)]), 50),
          (dict(dx=3, dy=2, hand=(38, 28), ang=34, footF=(G.FF[0] + 4, 39), flow=1.3, flutter=3, fx=[G.sw(w=0.45)]), 60),
          (dict(dx=3, dy=3, hand=(36, 30), ang=120, slen=15, footF=(G.FF[0] + 4, 39), flow=0.7, flutter=4), 110),
          (dict(dx=2, dy=3, hand=(33, 30), ang=150, flow=0.4, flutter=5), 80)]
    return G.mseq(tm(fr, 200, 500, 2), grip=GRIP_MAUL)


def ml_bb3():  # Big Bang III: from the low follow-through, a rising uppercut that lifts the foe
    fr = [(dict(dx=1, dy=4, head_dy=1, hand=(30, 31), ang=162, footB=(G.OX + 6, 39), footF=(G.FF[0] + 3, 39), flow=0.4,
                fx=[("dust", 15, 2)]), 120),
          (dict(dx=2, dy=4, hand=(35, 32), ang=112, footF=(G.FF[0] + 3, 39), flow=1.0, flutter=1, fx=[G.sw(w=0.4)]), 100),
          (dict(dx=3, dy=1, hand=(40, 24), ang=-32, footF=(G.FF[0] + 4, 39), flow=1.4, flutter=2, fx=[G.sw(w=0.6)]), 45),
          (dict(dx=3, dy=-2, hand=(36, 12), ang=-90, footB=(G.OX + 9, 37), footF=(G.FF[0] + 4, 38), flow=1.3, flutter=3,
                fx=[G.sw(w=0.5)]), 60),
          (dict(dx=2, dy=-2, hand=(31, 10), ang=-128, footB=(G.OX + 9, 37), footF=(G.FF[0] + 3, 38), flow=0.8, flutter=4), 130),
          (dict(dx=1, dy=-1, hand=(29, 11), ang=-150, footB=(G.OX + 8, 38), footF=(G.FF[0] + 2, 39), flow=0.5, flutter=5), 110)]
    return G.mseq(tm(fr, 220, 560, 2), grip=GRIP_MAUL)


def ml_bb4():  # Big Bang IV: a leap, the hammer held high and blazing, and everything brought down at once
    fr = [(dict(dx=-1, dy=3, head_dx=-1, hand=(29, 12), ang=-160, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.3,
                fx=[("glint", "tip")]), 110),
          (dict(dx=0, dy=-5, hand=(30, 9), ang=-150, footB=(G.OX + 9, 34), footF=(G.OX + 18, 33), flow=1.0, flutter=1, air=True,
                fx=[("dust", 30, 4)]), 90),
          (dict(dx=1, dy=-8, hand=(30, 8), ang=-162, footB=(G.OX + 9, 32), footF=(G.OX + 18, 31), flow=1.2, flutter=2, air=True,
                fx=[("glint", "tip")]), 100),
          (dict(dx=2, dy=-5, hand=(33, 9), ang=-96, footB=(G.OX + 9, 35), footF=(G.OX + 19, 34), flow=0.6, flutter=3, air=True,
                fx=[G.sw(w=0.4)]), 60),
          (dict(dx=3, dy=1, hand=(39, 21), ang=-4, footF=(G.FF[0] + 4, 39), flow=0.2, flutter=4, fx=[G.sw(w=0.6)]), 40),
          (dict(dx=3, dy=6, head_dy=1, hand=(38, 27), ang=84, footB=(G.OX + 5, 39), footF=(G.FF[0] + 4, 39), flow=1.6, flutter=5,
                fx=[G.sw(w=0.45), ("dust", 39, 13), ("flare", (39, 35), 12), ("rings", (39, 37), (7, 12))]), 80),
          (dict(dx=3, dy=7, head_dy=2, hand=(38, 27), ang=86, footB=(G.OX + 5, 39), footF=(G.FF[0] + 4, 39), flow=1.0, flutter=6,
                fx=[("dust", 39, 8), ("flare", (39, 36), 6), ("rings", (39, 37), (13, 19))]), 260),
          (dict(dx=3, dy=6, head_dy=1, hand=(38, 27), ang=84, footB=(G.OX + 5, 39), footF=(G.FF[0] + 4, 39), flow=0.6, flutter=7,
                fx=[("dust", 39, 4)]), 160),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=8), 180)]
    return G.mseq(tm(fr, 360, 1000, 4), grip=GRIP_MAUL)


def ml_quake():  # Earthshaker: the overcharge slammed straight down beside you -- the floor breaks both ways
    fr = [(dict(dx=0, dy=3, head_dx=1, hand=(29, 26), ang=166, footB=(G.OX + 5, 39), footF=(G.FF[0] + 3, 39), flow=0.6,
                fx=[("embers", (16, 32), 4, 1)]), 60),
          (dict(dx=0, dy=-1, hand=(31, 10), ang=-112, footB=(G.OX + 7, 38), footF=(G.FF[0] + 2, 39), flow=1.0, flutter=1,
                fx=[G.sw(w=0.4)]), 80),
          (dict(dx=1, dy=1, hand=(36, 18), ang=-30, footF=(G.FF[0] + 2, 39), flow=0.6, flutter=2, fx=[G.sw(w=0.55)]), 40),
          (dict(dx=1, dy=6, head_dy=1, hand=(34, 28), ang=88, footB=(G.OX + 4, 39), footF=(G.FF[0] + 3, 39), flow=1.6, flutter=3,
                fx=[("dust", 34, 15), ("flare", (34, 35), 11), ("rings", (34, 38), (8, 14)), ("embers", (34, 30), 12, 2)]), 80),
          (dict(dx=1, dy=7, head_dy=2, hand=(34, 28), ang=89, footB=(G.OX + 4, 39), footF=(G.FF[0] + 3, 39), flow=1.0, flutter=4,
                fx=[("dust", 34, 10), ("rings", (34, 38), (16, 24)), ("embers", (34, 28), 14, 3)]), 250),
          (dict(dx=1, dy=5, head_dy=1, hand=(34, 28), ang=88, footB=(G.OX + 4, 39), footF=(G.FF[0] + 3, 39), flow=0.6, flutter=5,
                fx=[("dust", 34, 4)]), 140),
          (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(G.FF[0] + 1, 39), flow=0.3, flutter=6), 150)]
    return G.mseq(tm(fr, 180, 700, 3), grip=GRIP_MAUL)


# =================================================================================================== SWORD & SHIELD
def sh_4():  # shield-bash finisher: step under the foe's guard and drive the shield up into it, rim first
    fr = [(dict(dx=-1, dy=2, hand=(30, 28), ang=150, off=(31, 28), footB=(G.OX + 6, 39), flow=0.3, shield=dict(abs=(34.5, 25.5), rot=-12, sx=0.5, layer="over")), 110),
          (dict(dx=-1, dy=4, head_dy=1, hand=(29, 29), ang=160, off=(32, 30), footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.2,
                flutter=1, shield=dict(abs=(35.5, 27.5), rot=-28, sx=0.45, layer="over"), fx=[("glint", (37, 22))]), 110),
          (dict(dx=3, dy=1, hand=(30, 28), ang=150, off=(39, 21), footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.4, flutter=2,
                shield=dict(rot=28, sx=0.42), fx=[("speed", (22, 22), 4, 10), ("flare", (45, 15), 6)]), 50),
          (dict(dx=3, dy=0, hand=(30, 27), ang=150, off=(39, 17), footB=(G.OX + 8, 38), footF=(G.OX + 25, 39), flow=1.1, flutter=3,
                shield=dict(rot=40, sx=0.42)), 80),
          (dict(dx=2, dy=1, hand=(31, 28), ang=140, off=(36, 22), footF=(G.OX + 22, 39), flow=0.6, flutter=4, shield=dict(rot=15, sx=0.5)), 120),
          (dict(hand=(34, 28), ang=-20, off=(32, 25), flow=0.3), 90)]
    return G.mseq(tm(fr, 220, 560, 2))




def sh_rush_hold():  # charged rush (loop): crouched behind the raised shield, sword drawn back low, weight on the back foot
    st = dict(dx=-2, dy=3, head_dx=-1, hand=(28, 30), ang=166, off=(33, 23), footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39),
              shield=dict(sx=0.5))
    return G.mseq([(dict(flow=0.25, flutter=0, **st), 140),
                   (dict(flow=0.2, flutter=1, fx=[("glint", (36, 17))], **{**st, "dy": 4}), 140),
                   (dict(flow=0.25, flutter=2, **{**st, "dy": 4}), 140)])


def sh_rush():  # charged shield rush: a headlong charge behind the shield, a ringing impact at the end of it
    SB = dict(sx=0.42)
    fr = [(dict(dx=-1, dy=3, hand=(29, 30), ang=162, off=(35, 23), footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.6,
                shield=SB), 80),
          (dict(dx=3, dy=3, head_dx=1, hand=(30, 29), ang=160, off=(39, 23), footB=(G.OX + 4, 37), footF=(G.OX + 27, 39), flow=1.8,
                flutter=1, shield=SB, fx=[("speed", (20, 17), 6, 18)]), 70),
          (dict(dx=5, dy=2, head_dx=1, hand=(30, 29), ang=158, off=(40, 23), footB=(G.OX + 12, 36), footF=(G.OX + 24, 39), flow=1.8,
                flutter=2, shield=SB, fx=[("speed", (21, 17), 6, 20)]), 70),
          (dict(dx=5, dy=2, hand=(30, 29), ang=158, off=(41, 23), footB=(G.OX + 9, 39), footF=(G.OX + 27, 39), flow=1.5, flutter=3,
                shield=SB, fx=[("speed", (22, 17), 5, 14), ("flare", (46, 22), 7)]), 60),
          (dict(dx=4, dy=2, hand=(30, 29), ang=158, off=(40, 23), footB=(G.OX + 9, 39), footF=(G.OX + 27, 39), flow=1.0, flutter=4,
                shield=SB, fx=[("flare", (46, 22), 4)]), 90),
          (dict(dx=2, dy=1, hand=(31, 29), ang=150, off=(36, 25), footF=(G.OX + 22, 39), flow=0.6, flutter=5), 120),
          (dict(hand=(34, 28), ang=-20, off=(32, 25), flow=0.3), 100)]
    return G.mseq(tm(fr, 220, 450, 3))


def sh_backhop():  # backhop: a short hop back off both feet, shield up before the face, landing ready
    air = dict(footB=(G.OX + 7, 35), footF=(G.OX + 17, 36))
    blade = dict(hand=(31, 25), ang=-30, off=(34, 21), shield=dict(sx=0.6))
    return G.mseq([(dict(dy=3, footB=(G.OX + 7, 39), footF=(G.FF[0] - 1, 39), flow=0.4, **blade), 50),
                   (dict(dx=-2, dy=-3, head_dx=-1, flow=-0.2, flutter=1, fx=[("dust", 26, 2)], **air, **blade), 90),
                   (dict(dx=-2, dy=-3, head_dx=-1, flow=0.2, flutter=2, **air, **blade), 80),
                   (dict(dx=-1, dy=2, footB=(G.OX + 6, 39), footF=(G.FF[0], 39), flow=0.6, flutter=3, **blade), 80)])


def sh_leap():  # leaping slash: spring forward off the backhop, blade high behind the head, and come down cutting
    fr = [(dict(dx=-1, dy=4, head_dy=1, hand=(30, 22), ang=-120, off=(33, 26), footB=(G.OX + 6, 39), footF=(G.FF[0] + 1, 39), flow=0.4), 90),
          (dict(dx=2, dy=-4, hand=(30, 13), ang=-150, off=(37, 21), footB=(G.OX + 9, 35), footF=(G.OX + 19, 34), flow=1.2, flutter=1,
                air=True, fx=[("dust", 28, 3)]), 110),
          (dict(dx=4, dy=-6, head_dx=-1, hand=(29, 11), ang=-168, off=(38, 20), footB=(G.OX + 9, 33), footF=(G.OX + 20, 33), flow=1.4,
                flutter=2, air=True, fx=[("glint", "tip")]), 120),
          (dict(dx=5, dy=-2, hand=(40, 19), ang=-30, off=(37, 22), footB=(G.OX + 9, 36), footF=(G.OX + 21, 37), flow=0.8, flutter=3,
                air=True, fx=[G.sw(w=0.55)]), 45),
          (dict(dx=5, dy=3, head_dy=1, hand=(40, 30), ang=50, off=(36, 24), footB=(G.OX + 8, 39), footF=(G.OX + 24, 39), flow=1.3,
                flutter=4, fx=[G.sw(w=0.5), ("dust", 47, 5)]), 60),
          (dict(dx=5, dy=4, head_dy=1, hand=(39, 31), ang=60, off=(36, 24), footB=(G.OX + 8, 39), footF=(G.OX + 24, 39), flow=0.7,
                flutter=5, fx=[("dust", 48, 3)]), 150),
          (dict(dx=3, dy=1, hand=(37, 28), ang=20, off=(33, 25), footF=(G.OX + 22, 39), flow=0.4, flutter=6), 120)]
    return G.mseq(tm(fr, 320, 700, 3))


def sh_slam():  # shield slam: out of the guard the shield is hauled up high and its rim brought down like a gate
    fr = [(dict(dx=-1, dy=2, hand=(31, 22), ang=-15, off=(35, 22), footB=(G.OX + 6, 39), footF=(G.FF[0] + 1, 39), flow=0.3,
                shield=dict(sx=0.66)), 90),
          (dict(dx=0, dy=0, hand=(31, 25), ang=-30, off=(36, 12), footB=(G.OX + 7, 39), flow=0.6, flutter=1,
                shield=dict(rot=-25, sx=0.5)), 140),
          (dict(dx=2, dy=3, hand=(31, 27), ang=-20, off=(41, 21), footF=(G.FF[0] + 3, 39), flow=1.2, flutter=2,
                shield=dict(rot=40, sx=0.45), fx=[("speed", (30, 12), 3, 8)]), 50),
          (dict(dx=3, dy=5, head_dy=1, hand=(32, 28), ang=-10, off=(42, 28), footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.3,
                flutter=3, shield=dict(rot=70, sx=0.45), fx=[("dust", 46, 8), ("flare", (46, 36), 7)]), 60),
          (dict(dx=3, dy=5, head_dy=1, hand=(32, 28), ang=-10, off=(42, 28), footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.7,
                flutter=4, shield=dict(rot=72, sx=0.45), fx=[("dust", 46, 4)]), 170),
          (dict(dx=1, dy=2, hand=(33, 26), ang=-25, off=(36, 24), footF=(G.FF[0] + 2, 39), flow=0.4, flutter=5), 110)]
    return G.mseq(tm(fr, 240, 620, 3))


def sh_fallbash():  # falling bash: the shield turned face-down under the boots, both arms bearing on it -- it lands like an anvil
    base = dict(dy=-4, head_dy=1, **G.TUCK)
    under = dict(abs=(37.5, 38.0), rot=118, sx=0.5, layer="front")
    ride = dict(hand=(30, 17), ang=-125, off=(36, 32), footB=(G.OX + 9, 33), footF=(G.OX + 16, 32), shield=under)
    fr = G.mseq([(dict(dy=-6, head_dy=0, hand=(34, 17), ang=-115, off=(37, 19), flow=0.9, footB=(G.OX + 9, 34), footF=(G.OX + 17, 34),
                       shield=dict(rot=60, sx=0.5)), 90),
                 (dict(flow=1.4, flutter=1, fx=G.DIVE(10, 0, 17, 47) + [("flare", (39, 40), 5)], **ride), 60),
                 (dict(dy=-3, flow=1.6, flutter=3, fx=G.DIVE(8, 1, 17, 46), **ride), 70),
                 (dict(flow=1.3, flutter=5, **ride), 80),
                 (dict(dy=-3, head_dy=0, hand=(35, 26), ang=-30, off=(32, 25), flow=0.7, flutter=4, **G.AIR), 120)], base)
    return G.cape_dive(fr, [1, 2, 3])


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

    # ---- longsword
    add("ls_kc_hold", ls_kc_hold, settle=False)
    add("ls_kc", ls_kc, 380, 650, A(3, 4))
    add("ls_jjk", ls_jjk, 330, 640, A(3, 4), x0=-6)
    add("ls_jjjk", ls_jjjk, 350, 680, A(3, 4), x0=0)
    add("ls_quick", ls_quick, 140, 400, A(2, 3))
    add("ls_step", ls_step, 160, 420, A(2, 3), x0=-2)
    add("ls_fore_stance", ls_fore_stance, settle=False)
    add("ls_fore_cut", ls_fore_cut, 100, 560, A(2, 3))
    add("ls_pommel", ls_pommel, 300, 650, A(2, 3), hit=[2, -32, 26, -10], fxat=(18, -18))
    # ---- katana
    add("kt_sheathe", kt_sheathe, settle=False)
    add("kt_sheathed_idle", kt_sheathed_idle, settle=False)
    add("kt_sheathed_walk", kt_sheathed_walk, settle=False)
    add("kt_iai", kt_iai, 90, 520, A(2, 3), x0=-2)
    add("kt_focus_hold", kt_focus_hold, settle=False)
    add("kt_focus", kt_focus, 120, 500, A(2, 3), x0=-24)
    add("kt_iai_parry", kt_iai_parry, 200, 600, A(3, 4), x0=-2)
    add("kt_sidestep", kt_sidestep, settle=False)
    add("kt_stepcut", kt_stepcut, 120, 360, A(2, 3), x0=-2)
    add("kt_flurry", kt_flurry, 180, 600, A(2, 6), hits=[2, 4, 6], x0=-4)
    add("kt_rush", kt_rush, 260, 620, A(3, 4), settle=False, x0=-2)   # extra: the rushing draw that re-sheathes (K -> K loop)
    add("kt_flash", kt_flash, 100, 420, A(2, 3), x0=-30, fxat=(2, -12))
    # ---- greatsword
    add("gs_charge_hold", gs_charge_hold, settle=False, kinds=("greatsword",))
    add("gs_charged", gs_charged, 200, 500, A(2, 3), kinds=("greatsword",))
    add("gs_strong", gs_strong, 220, 560, A(3, 4), kinds=("greatsword",))
    add("gs_true1", gs_true1, 180, 480, A(2, 3), settle=False, kinds=("greatsword",))
    add("gs_true2", gs_true2, 260, 800, A(3, 4), kinds=("greatsword",))
    add("gs_guard", gs_guard, settle=False, kinds=("greatsword",))
    add("gs_tackle", gs_tackle, 90, 300, A(1, 2), settle=False, kinds=("greatsword",), body=True, hit=[-2, -32, 22, 0], fxat=(16, -18))
    add("gs_rollheavy", gs_rollheavy, 220, 600, A(3, 4), kinds=("greatsword",))
    add("gs_wrath", gs_wrath, 220, 640, A(2, 3), kinds=("greatsword",))
    # ---- maul
    add("ml_1", ml_1, 260, 620, A(4, 5))
    add("ml_2", ml_2, 260, 620, A(3, 4))
    add("ml_3", ml_3, 300, 720, A(3, 4), up=True)
    add("ml_charge_walk", ml_charge_walk, settle=False)
    add("ml_charge_idle", ml_charge_idle, settle=False)
    add("ml_upswing", ml_upswing, 140, 520, A(2, 3), up=True)
    add("ml_double", ml_double, 160, 900, A(2, 8), hits=[2, 7], x0=0)
    add("ml_bigsmash", ml_bigsmash, 240, 820, A(4, 5))
    add("ml_spin", ml_spin, settle=False, active=A(0, 3), hits=[0], both=True)   # one 0.5 hit per full turn (loop); the box covers both sides
    add("ml_spin_end", ml_spin_end, 160, 700, A(2, 3), up=True, x0=-2)
    add("ml_brace", ml_brace, settle=False)
    add("ml_rollswing", ml_rollswing, 200, 560, A(2, 3), up=True)
    add("ml_bb1", ml_bb1, 200, 500, A(2, 3), x0=-4)
    add("ml_bb2", ml_bb2, 200, 500, A(2, 3), x0=-4)
    add("ml_bb3", ml_bb3, 220, 560, A(2, 3), up=True)
    add("ml_bb4", ml_bb4, 360, 1000, A(4, 5))
    add("ml_quake", ml_quake, 180, 700, A(3, 4), hit=[-36, -16, 40, 0], fxat=(6, -4))
    # ---- sword & shield
    add("sh_4", sh_4, 220, 560, A(2, 3), extras=True, x0=0, fxat=(16, -22))
    add("sh_rush_hold", sh_rush_hold, settle=False)
    add("sh_rush", sh_rush, 220, 450, A(3, 4), extras=True, x0=0, fxat=(17, -17))
    add("sh_backhop", sh_backhop, settle=False)
    add("sh_leap", sh_leap, 320, 700, A(3, 4), x0=-2)
    add("sh_slam", sh_slam, 240, 620, A(3, 4), extras=True, x0=0)
    add("sh_fallbash", sh_fallbash, 90, 420, A(1, 3), settle=False, extras=True, down=True, fxat=(6, 6))
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    print(f"{'tag':18} {'frames':>6} {'wind':>5} {'total':>5}   {'spec':>9}   ok")
    SPEC = GP._v13a.SPEC
    for t in [e[0] for e in GP._v13a.register(GP)]:
        fr = list(fns[t]())
        ms = [m for _, m in fr]
        act = GP.ACTIVE.get(t)
        wind = sum(ms[:act[0]]) if act else None
        tot = sum(ms)
        sp = SPEC.get(t)
        ok = "" if not sp else ("OK" if (wind, tot) == sp else "MISMATCH")
        print(f"{t:18} {len(fr):6} {wind if wind is not None else '-':>5} {tot:5}   {('%d/%d' % sp) if sp else 'loop/stance':>11}   {ok}")
