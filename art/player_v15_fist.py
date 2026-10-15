"""v15 tags for the Martial Arts (fist, prefix ft_, weapon penitent_knuckles) -- docs/WEAPON_REVAMP.md C3, docs/v15/fist.md.

Same register(G) contract as player_v13_a.py / player_v14_*.py: [(tag, fn, opts)], fn() -> [(cels, ms)].
Each attack is timed to its move row in web/src/78_mech_fist.js (tm(): the frames before the first active frame last the
wind-up, the rest the recovery) and reads anticipation -> smear -> impact -> follow-through -> settle.

The rig for a fighter without a weapon:
  * BOTH fists read: the knuckles are registered as a "twin" weapon here (G.TWIN_KINDS), so every frame's `offw` pose
    puts the second spiked knuckle on the far hand (front=True draws it over the body when the hand is out in front).
  * KICKS: `kF` / `kB` replace the front / back leg with a longer IK leg (seg 6.0 instead of 5.2) and a real foot that
    points along `toe` (deg) -- a heel, an instep, a ball of the foot -- instead of the standing foot's flat bar.
  * Smears are coded by style: Swift moves smear pale steel-blue (SWIFT), Iron moves ember (IRON); kick arcs are
    ("ring", hip, R, a0, a1) bands swept round the hip; punches leave ("speed") dash lines and an impact flare.
  * Two stances: Swift (ft_sw_idle / ft_sw_run) light on the toes, guard high, the far fist leading; Iron
    (ft_ir_idle / ft_ir_walk) low and wide, the lead palm open, the rear fist chambered at the hip. The walk / run plant
    the foot on the backward half of the stride and lift it on the forward swing.
"""
import math

G = None   # gen_player, set by register()
KN = "penitent_knuckles"
SWIFT = ((236, 246, 255), (168, 204, 240), (86, 118, 170))      # Swift smears: pale steel-blue
IRON = ((255, 236, 190), (255, 150, 70), (168, 66, 30))         # Iron smears: ember
EMBERP = ((255, 244, 200), (255, 170, 80), (200, 70, 30))       # the Ember palm / full Flow


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


def ft_leg(hip, foot, front, bend=1, seg=6.0, toe=0.0, tl=3.2):
    """A kicking leg: two-bone IK from the hip to the ankle, then a foot pointing along `toe` (degrees, 0 = forward)."""
    g = G.blank()
    knee = G.ik(hip, foot, seg, seg, bend)
    ramp = ('4', '3', '2') if front else ('3', '2', '1')
    G.limb(g, [hip, knee], 4.2, *ramp)
    G.limb(g, [knee, foot], 3.4, *ramp)
    a = math.radians(toe)
    tip = (foot[0] + math.cos(a) * tl, foot[1] + math.sin(a) * tl)
    G.limb(g, [foot, tip], 2.8, *ramp)
    G.put(g, tip[0], tip[1], ramp[0])
    G.put(g, knee[0] + 0.5, knee[1], '5' if front else '4')
    return G.outline(g)


def fseq(frames, base=None):
    """G.mseq, then the kicking legs (kF / kB = dict(foot, toe, seg, bend)) drawn over the standing ones."""
    out = G.mseq(frames, base)
    for i, (p, ms) in enumerate(frames):
        q = {**(base or {}), **p}
        bx, by = q.get("dx", 0), q.get("dy", 0)
        for key, hip, front, layer in (("kF", (G.OX + 15 + bx, G.OY + 21 + by), True, "FrontLeg"),
                                       ("kB", (G.OX + 11 + bx, G.OY + 21 + by), False, "BackLeg")):
            if key in q:
                k = q[key]
                leg = ft_leg(hip, k["foot"], front, k.get("bend", 1), k.get("seg", 6.0), k.get("toe", 0.0), k.get("tl", 3.2))
                out[i][0][layer] = G.mirror_grid(leg) if q.get("mirror") else leg
    return out


def ow(x, y, a, front=True):
    """The far fist: offw = ((x, y), knuckle angle, -, drawn over the body?)."""
    return ((x, y), a, 18, front)


# ---- the two stances (pose fragments)
SW = {}
IR = {}


def register(g):
    global G, SW, IR
    G = g
    OX, OY, FF = G.OX, G.OY, G.FF
    # both fists read: the knuckles become a "twin" weapon (the far hand's knuckle comes from each frame's offw)
    if KN not in G.TWIN_KINDS:
        G.TWIN_KINDS = tuple(G.TWIN_KINDS) + (KN,)
    G.EXTRA_KINDS.add(KN)
    # Swift guard: up on the balls of the feet, narrow, the far fist leading at the chin line, the near fist by the jaw
    SW = dict(hand=(34, 20), ang=-62, offw=ow(37, 21, -34), footB=(OX + 9, 39), footF=(OX + 19, 39))
    # Iron guard: low and wide, the lead (far) palm open at the chest, the near fist chambered at the hip
    IR = dict(dy=3, hand=(30, 29), ang=-10, offw=ow(38, 21, -75), footB=(OX + 4, 39), footF=(OX + 23, 39), bendF=1)

    def P(base, **k):
        d = dict(base)
        d.update(k)
        return d

    # ------------------------------------------------------------------ stances
    def ft_sw_idle():  # light on the toes, a small bounce, guard high; the fists breathe with it
        fr = []
        for i, b in enumerate((0, 1, 1, 0, -1, -1)[:6]):
            up = 1 if b < 0 else 0
            fr.append((P(SW, dy=max(0, b), hand=(34, 20 + max(0, b)), offw=ow(37, 21 + max(0, b) - up, -34),
                         footB=(OX + 9, 39 - up), footF=(OX + 19, 39 - up * 0), flow=0.3 + 0.05 * i, flutter=i), 110))
        return fseq(fr)

    def ft_sw_run():  # a light boxer's run: guard up, leaning in; each foot planted on the back half, lifted forward
        def foot(ph, hip_x):
            ph %= 1.0
            if ph < 0.5:
                return (hip_x + 7 - 28 * ph, 39)
            s = (ph - 0.5) * 2
            e = s * s * (3 - 2 * s)
            return (hip_x - 7 + 14 * e, 39 - 4.0 * math.sin(math.pi * s))
        out = []
        for i in range(8):
            ph = i / 8
            dy = [1, 0, -1, 0, 1, 0, -1, 0][i] + 1
            sw = math.sin(2 * math.pi * ph)
            out.append((dict(dx=1, dy=dy, head_dx=1, lean=2, footF=foot(ph, OX + 15), footB=foot(ph + 0.5, OX + 11), leg=5.6,
                             hand=(35 + sw * 0.8, 21 + dy * 0.5), ang=-55, offw=ow(37 - sw * 0.8, 22 + dy * 0.5, -40),
                             flow=1.0 + 0.25 * math.sin(ph * 4 * math.pi), flutter=i), 45))
        return fseq(out)

    def ft_ir_idle():  # rooted: a slow, deep breath; nothing moves but the chest and the cape
        fr = []
        for i, b in enumerate((0, 0, 1, 1)):
            fr.append((P(IR, dy=3 + b, hand=(30, 29 + b), offw=ow(38, 21 + b, -75), flow=0.2 + 0.04 * i, flutter=i), 200))
        return fseq(fr)

    def ft_ir_walk():  # a heavy, measured stride, kept low; the planted foot pushes back, the free one lifts and swings
        out = []
        n = 8
        for i in range(n):
            t = i / n * 2 * math.pi
            cx = OX + 13.5
            fF = (cx + 6.5 * math.cos(t), 39 - max(0.0, -math.sin(t)) * 2.6)
            fB = (cx + 6.5 * math.cos(t + math.pi), 39 - max(0.0, -math.sin(t + math.pi)) * 2.6)
            dy = 3 if i % (n // 2) == 0 else 2
            out.append((P(IR, dy=dy, hand=(30, 29 + (dy - 2)), offw=ow(38, 21 + (dy - 2), -75), footF=fF, footB=fB, leg=5.4,
                          flow=0.4 + 0.1 * math.sin(t * 2), flutter=i), 105))
        return fseq(out)

    # ------------------------------------------------------------------ SWIFT
    def ft_jab():  # the far fist snaps straight out from the guard and back
        fr = [(P(SW, dx=0, dy=1, offw=ow(35, 22, -20), flow=0.4), 40),
              (P(SW, dx=2, dy=1, hand=(35, 21), offw=ow(45, 21, -2), footF=(OX + 21, 39), flow=0.8, flutter=1,
                 fx=[("speed", (42, 21), 2, 9), ("flare", (50, 21), 3)], fx_pal=SWIFT), 50),
              (P(SW, dx=2, dy=1, hand=(35, 21), offw=ow(43, 21, -4), footF=(OX + 21, 39), flow=0.7, flutter=2), 50),
              (P(SW, dx=1, flow=0.4, flutter=3), 80)]
        return fseq(tm(fr, 80, 220, 1))

    def ft_cross():  # the hips turn, the near fist drives straight through; the far fist comes home to the jaw
        fr = [(P(SW, dx=-1, dy=1, head_dx=-1, hand=(32, 21), ang=-30, offw=ow(37, 22, -40), footB=(OX + 8, 39), flow=0.4), 40),
              (P(SW, dx=3, dy=1, head_dx=1, lean=1, hand=(45, 21), ang=-2, offw=ow(34, 21, -60), footB=(OX + 11, 38),
                 footF=(OX + 22, 39), flow=1.0, flutter=1, fx=[("speed", (41, 22), 2, 11), ("flare", (50, 21), 4)], fx_pal=SWIFT), 50),
              (P(SW, dx=3, dy=1, lean=1, hand=(43, 21), ang=-4, offw=ow(34, 21, -60), footB=(OX + 11, 38), footF=(OX + 22, 39),
                 flow=0.8, flutter=2), 50),
              (P(SW, dx=1, flow=0.4, flutter=3), 80)]
        return fseq(tm(fr, 80, 220, 1))


    def ft_hook():  # the far fist loops round from outside at head height, the hips turning through it
        fr = [(P(SW, dx=-1, dy=1, head_dx=-1, offw=ow(35, 19, -130), hand=(33, 21), flow=0.4), 50),
              (P(SW, dx=0, dy=1, offw=ow(37, 17, -95), hand=(33, 21), flow=0.6, flutter=1), 50),
              (P(SW, dx=2, dy=1, lean=1, offw=ow(43, 19, -12), hand=(33, 22), ang=-70, footB=(OX + 10, 38), flow=1.1, flutter=2,
                 fx=[("ring", (36, 22), 8, -150, -15, dict(sq=0.55, w=2.6)), ("flare", (48, 19), 3)], fx_pal=SWIFT), 50),
              (P(SW, dx=2, dy=1, lean=1, offw=ow(41, 22, 40), hand=(33, 22), ang=-70, footB=(OX + 10, 38), flow=0.8, flutter=3), 60),
              (P(SW, dx=1, flow=0.4, flutter=4), 70)]
        return fseq(tm(fr, 100, 260, 2))

    def ft_knee():  # clinch the head with both hands, then three driving knees: front, back, then a hopping front knee
        CL = dict(hand=(40, 19), ang=-30, offw=ow(41, 18, -40))
        fr = [(P(SW, dx=1, dy=1, **CL, flow=0.5), 70),
              (P(SW, dx=0, dy=0, **CL, footB=(OX + 9, 39), flow=0.6, flutter=1), 50),
              (P(SW, dx=1, dy=0, lean=-1, hand=(39, 21), ang=-10, offw=ow(40, 20, -20), kF=dict(foot=(OX + 18, 34), toe=100, bend=1, seg=5.4),
                 footB=(OX + 10, 39), flow=1.0, flutter=2, fx=[("flare", (OX + 25, 24), 3)], fx_pal=SWIFT), 70),
              (P(SW, dx=2, dy=1, **CL, footF=(OX + 21, 39), footB=(OX + 11, 39), flow=0.8, flutter=3), 40),
              (P(SW, dx=2, dy=0, lean=-1, hand=(40, 21), ang=-10, offw=ow(41, 20, -20), kB=dict(foot=(OX + 16, 34), toe=100, bend=1, seg=5.6),
                 footF=(OX + 21, 39), flow=1.1, flutter=4, fx=[("flare", (OX + 26, 24), 3)], fx_pal=SWIFT), 70),
              (P(SW, dx=3, dy=1, **CL, footF=(OX + 22, 39), footB=(OX + 13, 39), flow=0.9, flutter=5), 40),
              (P(SW, dx=4, dy=-2, lean=-1, hand=(41, 22), ang=10, offw=ow(42, 21, 0), kF=dict(foot=(OX + 21, 31), toe=100, bend=1, seg=5.4),
                 footB=(OX + 14, 36), air=True, flow=1.4, flutter=6,
                 fx=[("flare", (OX + 30, 21), 5), ("speed", (OX + 24, 22), 2, 7)], fx_pal=SWIFT), 80),
              (P(SW, dx=4, dy=1, footF=(OX + 23, 39), footB=(OX + 14, 39), flow=0.8, flutter=7), 110),
              (P(SW, dx=2, flow=0.4, flutter=8), 100)]
        return fseq(tm(fr, 120, 480, 2))

    def ft_backfist():  # wait a beat, turn your back on the foe, and whip the near fist round in a backhand
        fr = [(P(SW, dx=0, dy=1, head_dx=-1, hand=(31, 22), ang=-120, offw=ow(36, 21, -40), flow=0.5), 60),
              (P(SW, dx=1, dy=1, hand=(30, 22), ang=170, offw=ow(33, 23, -60), mirror=True, footB=(OX + 10, 39), flow=1.0, flutter=1), 80),
              (P(SW, dx=3, dy=0, lean=1, hand=(45, 19), ang=-20, offw=ow(33, 22, -60), footB=(OX + 11, 38), footF=(OX + 22, 39), flow=1.4,
                 flutter=2, fx=[("ring", (32, 22), 14, 200, -20, dict(sq=0.45, w=3.0)), ("flare", (49, 18), 4)], fx_pal=SWIFT), 60),
              (P(SW, dx=3, dy=0, lean=1, hand=(43, 22), ang=20, offw=ow(33, 22, -60), footB=(OX + 11, 38), footF=(OX + 22, 39), flow=1.0,
                 flutter=3), 90),
              (P(SW, dx=1, flow=0.5, flutter=4), 110)]
        return fseq(tm(fr, 140, 400, 2))

    def ft_snap():  # chamber the front knee high, snap the ball of the foot out at the belly, re-chamber, set down
        fr = [(P(SW, dx=-1, dy=0, lean=-1, kF=dict(foot=(OX + 18, 34), toe=60), flow=0.4), 70),
              (P(SW, dx=-1, dy=-1, lean=-1, kF=dict(foot=(OX + 22, 28), toe=30), footB=(OX + 10, 39), flow=0.6, flutter=1), 70),
              (P(SW, dx=0, dy=-1, lean=-2, hand=(33, 21), offw=ow(35, 22, -50), kF=dict(foot=(OX + 28, 26), toe=-8, seg=6.4),
                 footB=(OX + 10, 39), flow=1.0, flutter=2,
                 fx=[("ring", (OX + 15, OY + 20), 12, 70, -5, dict(sq=1.0, w=3.4)), ("flare", (OX + 32, 25), 3)], fx_pal=SWIFT), 60),
              (P(SW, dx=0, dy=-1, lean=-2, kF=dict(foot=(OX + 27, 27), toe=-6, seg=6.4), footB=(OX + 10, 39), flow=0.8, flutter=3), 70),
              (P(SW, dx=-1, dy=0, lean=-1, kF=dict(foot=(OX + 21, 31), toe=40), footB=(OX + 10, 39), flow=0.5, flutter=4), 70),
              (P(SW, dx=1, flow=0.3, flutter=5), 80)]
        return fseq(tm(fr, 140, 380, 2))

    def ft_round():  # a front roundhouse at the ribs, then spin through and bring the back leg round higher at the head
        fr = [(P(SW, dx=-1, dy=0, lean=-1, kF=dict(foot=(OX + 19, 32), toe=20), footB=(OX + 9, 39), flow=0.5), 80),
              (P(SW, dx=0, dy=-1, lean=-2, kF=dict(foot=(OX + 28, 24), toe=-15, seg=6.4), footB=(OX + 10, 39), flow=1.1, flutter=1,
                 fx=[("ring", (OX + 15, OY + 20), 12, 100, -15, dict(sq=0.7, w=3.4)), ("flare", (OX + 32, 22), 3)], fx_pal=SWIFT), 70),
              (P(SW, dx=1, dy=0, mirror=True, hand=(34, 21), ang=-60, offw=ow(36, 22, -40), footB=(OX + 11, 39), footF=(OX + 18, 39),
                 flow=1.4, flutter=2), 80),
              (P(SW, dx=2, dy=-1, lean=-2, hand=(33, 22), offw=ow(34, 23, -60), kB=dict(foot=(OX + 29, 20), toe=-25, seg=6.6),
                 footF=(OX + 17, 39), flow=1.5, flutter=3,
                 fx=[("ring", (OX + 13, OY + 20), 14, 140, -25, dict(sq=0.75, w=3.6)), ("flare", (OX + 33, 17), 4)], fx_pal=SWIFT), 80),
              (P(SW, dx=2, dy=0, lean=-1, kB=dict(foot=(OX + 22, 30), toe=30), footF=(OX + 18, 39), flow=1.0, flutter=4), 110),
              (P(SW, dx=2, flow=0.5, flutter=5, footF=(OX + 21, 39), footB=(OX + 11, 39)), 140)]
        return fseq(tm(fr, 160, 560, 1))

    def ft_rknee():  # dip, spring off the back foot and drive the front knee up through the chin, hands pulling down
        fr = [(P(SW, dx=0, dy=3, head_dy=1, hand=(38, 23), ang=-30, offw=ow(39, 22, -30), footB=(OX + 8, 39), footF=(OX + 19, 39), flow=0.4), 70),
              (P(SW, dx=1, dy=-1, hand=(39, 24), ang=40, offw=ow(40, 25, 40), kF=dict(foot=(OX + 20, 33), toe=100, seg=5.6),
                 footB=(OX + 10, 37), air=True, flow=0.9, flutter=1), 50),
              (P(SW, dx=2, dy=-4, lean=-1, hand=(38, 27), ang=70, offw=ow(39, 28, 70), kF=dict(foot=(OX + 19, 30), toe=95, seg=5.4),
                 footB=(OX + 11, 34), air=True, flow=1.3, flutter=2,
                 fx=[("flare", (OX + 27, 20), 4), ("vspeed", (OX + 22, 34), 2, 7)], fx_pal=SWIFT), 70),
              (P(SW, dx=2, dy=-2, hand=(36, 23), ang=-40, offw=ow(38, 22, -40), footB=(OX + 10, 37), footF=(OX + 20, 37), air=True,
                 flow=0.9, flutter=3), 90),
              (P(SW, dx=2, dy=2, footF=(OX + 21, 39), footB=(OX + 10, 39), flow=0.5, flutter=4), 100)]
        return fseq(tm(fr, 120, 380, 2))

    def ft_whirl():  # crouch and spin: the leg sweeps round behind you (seen from the back), then on round in front
        fr = [(P(SW, dx=0, dy=2, head_dx=-1, hand=(33, 22), offw=ow(36, 22, -40), footB=(OX + 7, 39), footF=(OX + 19, 39), flow=0.5), 80),
              (P(SW, dx=0, dy=-1, lean=-2, mirror=True, hand=(33, 21), offw=ow(34, 22, -50), kF=dict(foot=(OX + 28, 24), toe=-10, seg=6.4),
                 footB=(OX + 10, 39), flow=1.3, flutter=1,
                 fx=[("ring", (OX + 15, OY + 20), 12, 120, -10, dict(sq=0.6, w=3.4))], fx_pal=SWIFT), 80),
              (P(SW, dx=1, dy=-1, lean=-2, hand=(33, 21), offw=ow(34, 22, -50), kF=dict(foot=(OX + 29, 23), toe=-10, seg=6.4),
                 footB=(OX + 10, 39), flow=1.5, flutter=2,
                 fx=[("ring", (OX + 15, OY + 20), 13, 170, -10, dict(sq=0.6, w=3.6)), ("flare", (OX + 33, 22), 4)], fx_pal=SWIFT), 70),
              (P(SW, dx=1, dy=0, lean=-1, kF=dict(foot=(OX + 22, 31), toe=30), footB=(OX + 10, 39), flow=1.0, flutter=3), 120),
              (P(SW, dx=1, flow=0.5, flutter=4), 170)]
        return fseq(tm(fr, 160, 520, 1))

    def ft_hundred():  # (loop) a blur of jabs, near and far fists in turn, the fists smeared into a fan of knuckles
        fr = []
        for i, (h, o) in enumerate((((46, 20), (35, 22)), ((35, 21), (46, 23)), ((46, 23), (35, 21)), ((35, 22), (46, 19)))):
            near = i % 2 == 0
            tip = (h if near else o)
            fr.append((P(SW, dx=2, dy=1, lean=1, hand=h, ang=-3 if near else -60, offw=ow(o[0], o[1], -60 if near else -3),
                         footB=(OX + 10, 39), footF=(OX + 22, 39), flow=0.9 + 0.1 * i, flutter=i,
                         fx=[("speed", (tip[0] - 3, tip[1] + 1), 2, 8), ("flare", (tip[0] + 5, tip[1]), 2)], fx_pal=SWIFT), 55))
        return fseq(fr)

    def ft_upper():  # dip under the guard, then spring onto the toes and drive the near fist straight up
        fr = [(P(SW, dx=0, dy=4, head_dy=1, hand=(32, 31), ang=-80, offw=ow(37, 22, -40), footB=(OX + 7, 39), footF=(OX + 20, 39), flow=0.4), 70),
              (P(SW, dx=1, dy=3, hand=(35, 28), ang=-85, offw=ow(37, 23, -40), footB=(OX + 8, 39), footF=(OX + 20, 39), flow=0.6, flutter=1), 50),
              (P(SW, dx=2, dy=-2, head_dy=-1, hand=(37, 9), ang=-88, offw=ow(35, 22, -50), footB=(OX + 11, 37), footF=(OX + 20, 38), flow=1.3,
                 flutter=2, fx=[("vspeed", (37, 24), 2, 10), ("flare", (37, 3), 4)], fx_pal=SWIFT), 70),
              (P(SW, dx=2, dy=-1, hand=(37, 11), ang=-80, offw=ow(35, 22, -50), footB=(OX + 11, 38), flow=1.0, flutter=3), 90),
              (P(SW, dx=1, flow=0.5, flutter=4), 120)]
        return fseq(tm(fr, 120, 400, 2))

    def ft_slip():  # the slip step: duck the head under, weave low to one side, come up guarded
        return fseq([(P(SW, dx=-1, dy=3, head_dx=-2, head_dy=1, hand=(33, 25), offw=ow(35, 25, -50), footB=(OX + 7, 39), footF=(OX + 20, 39), flow=1.0), 50),
                     (P(SW, dx=-2, dy=5, head_dx=-2, head_dy=1, lean=-1, hand=(32, 27), offw=ow(34, 27, -50), footB=(OX + 6, 39), footF=(OX + 21, 39),
                        flow=1.4, flutter=1), 70),
                     (P(SW, dx=-1, dy=3, head_dx=-1, hand=(33, 24), offw=ow(36, 24, -40), footB=(OX + 8, 39), footF=(OX + 20, 39), flow=1.0, flutter=2), 60),
                     (P(SW, dy=1, flow=0.6, flutter=3), 60)])

    def ft_sjab():  # out of the slip: still low, the far fist darts out and up as you come in
        fr = [(P(SW, dx=-1, dy=4, head_dx=-1, hand=(33, 25), offw=ow(35, 25, -40), footB=(OX + 7, 39), footF=(OX + 20, 39), flow=0.8), 100),
              (P(SW, dx=3, dy=2, lean=2, hand=(35, 22), offw=ow(47, 21, -5), footB=(OX + 11, 38), footF=(OX + 24, 39), flow=1.3, flutter=1,
                 fx=[("speed", (43, 22), 3, 12), ("flare", (52, 21), 3)], fx_pal=SWIFT), 60),
              (P(SW, dx=3, dy=1, lean=1, hand=(35, 22), offw=ow(45, 21, -5), footB=(OX + 11, 39), footF=(OX + 24, 39), flow=0.9, flutter=2), 80),
              (P(SW, dx=1, flow=0.5, flutter=3), 80)]
        return fseq(tm(fr, 100, 320, 1))

    def ft_sweep():  # drop onto the back knee and scythe the front leg along the floor through the foe's ankles
        fr = [(P(SW, dx=-1, dy=5, head_dy=1, hand=(32, 29), ang=60, offw=ow(36, 30, 80), footB=(OX + 6, 39), footF=(OX + 19, 39), flow=0.8), 70),
              (P(SW, dx=0, dy=7, head_dy=1, lean=1, hand=(31, 33), ang=90, offw=ow(37, 34, 90), footB=(OX + 7, 39),
                 kF=dict(foot=(OX + 22, 38), toe=0, seg=6.2), flow=1.0, flutter=1), 70),
              (P(SW, dx=1, dy=7, head_dy=1, lean=1, hand=(31, 33), ang=90, offw=ow(37, 34, 90), footB=(OX + 7, 39),
                 kF=dict(foot=(OX + 31, 38), toe=-5, seg=6.6), flow=1.5, flutter=2,
                 fx=[("ring", (OX + 15, 37), 15, 160, 0, dict(sq=0.22, w=2.6)), ("dust", 44, 3)], fx_pal=SWIFT), 70),
              (P(SW, dx=1, dy=7, head_dy=1, lean=1, hand=(31, 33), ang=90, offw=ow(37, 34, 90), footB=(OX + 7, 39),
                 kF=dict(foot=(OX + 30, 38), toe=-5, seg=6.6), flow=1.0, flutter=3), 100),
              (P(SW, dx=1, dy=4, head_dy=1, hand=(33, 26), offw=ow(36, 26, -40), footB=(OX + 8, 39), footF=(OX + 21, 39), flow=0.6, flutter=4), 80),
              (P(SW, dx=1, flow=0.4, flutter=5), 70)]
        return fseq(tm(fr, 140, 460, 2))

    def ft_fcounter():  # out of the perfect slip, already inside: a silver open palm to the sternum, the whole body behind it
        SIL = ((255, 255, 255), (214, 228, 250), (130, 150, 190))
        fr = [(P(SW, dx=0, dy=4, head_dx=-1, hand=(30, 27), ang=180, offw=ow(37, 23, -50), footB=(OX + 7, 39), footF=(OX + 21, 39),
                 flow=1.0, fx=[("glint", (31, 26))], fx_pal=SIL), 80),
              (P(SW, dx=4, dy=2, lean=2, hand=(46, 22), ang=0, offw=ow(33, 24, -60), footB=(OX + 12, 38), footF=(OX + 25, 39), flow=1.6,
                 flutter=1, fx=[("speed", (42, 23), 3, 14), ("flare", (51, 22), 6)], fx_pal=SIL), 60),
              (P(SW, dx=4, dy=2, lean=2, hand=(45, 22), ang=0, offw=ow(33, 24, -60), footB=(OX + 12, 38), footF=(OX + 25, 39), flow=1.2,
                 flutter=2, fx=[("flare", (51, 22), 3)], fx_pal=SIL), 110),
              (P(SW, dx=3, dy=1, hand=(40, 23), ang=-20, footB=(OX + 11, 39), footF=(OX + 24, 39), flow=0.7, flutter=3), 70),
              (P(SW, dx=1, flow=0.4, flutter=4), 80)]
        return fseq(tm(fr, 80, 400, 1))

    # ------------------------------------------------------------------ IRON
    def ft_palm():  # sink, draw the near hand back to the hip, and drive the heel of the palm out from the floor up
        fr = [(P(IR, dx=-1, dy=4, hand=(27, 30), ang=180, offw=ow(39, 22, -75), flow=0.3), 130),
              (P(IR, dx=-1, dy=4, hand=(26, 30), ang=180, offw=ow(38, 23, -75), footB=(OX + 3, 39), flow=0.3, flutter=1,
                 fx=[("glint", (27, 30))], fx_pal=IRON), 130),
              (P(IR, dx=3, dy=3, lean=1, hand=(46, 24), ang=0, offw=ow(31, 27, -100, False), footB=(OX + 7, 39), footF=(OX + 26, 39), flow=1.0,
                 flutter=2, fx=[("speed", (42, 25), 3, 12), ("flare", (51, 24), 5), ("dust", 40, 2)], fx_pal=IRON), 60),
              (P(IR, dx=3, dy=3, lean=1, hand=(45, 24), ang=0, offw=ow(31, 27, -100, False), footB=(OX + 7, 39), footF=(OX + 26, 39), flow=0.7,
                 flutter=3), 120),
              (P(IR, dx=2, flow=0.4, flutter=4, footF=(OX + 25, 39), footB=(OX + 6, 39)), 120)]
        return fseq(tm(fr, 260, 560, 2))

    def ft_elbow():  # step in deep and drive the near elbow through, the fist folded back at the chest
        fr = [(P(IR, dx=-1, dy=3, head_dx=-1, hand=(30, 18), ang=-160, offw=ow(38, 22, -75), flow=0.3), 140),
              (P(IR, dx=0, dy=3, hand=(31, 17), ang=-170, offw=ow(37, 23, -75), footB=(OX + 4, 39), flow=0.4, flutter=1), 120),
              (P(IR, dx=4, dy=3, lean=2, hand=(36, 21), ang=180, offw=ow(31, 25, -100, False), footB=(OX + 8, 39), footF=(OX + 27, 39), flow=1.1,
                 flutter=2, fx=[("ring", (31, 23), 10, -120, 0, dict(sq=0.5, w=2.8)), ("flare", (43, 22), 5), ("dust", 41, 2)], fx_pal=IRON), 60),
              (P(IR, dx=4, dy=3, lean=2, hand=(36, 22), ang=180, offw=ow(31, 25, -100, False), footB=(OX + 8, 39), footF=(OX + 27, 39), flow=0.8,
                 flutter=3), 120),
              (P(IR, dx=2, flow=0.4, flutter=4, footF=(OX + 25, 39), footB=(OX + 6, 39)), 120)]
        return fseq(tm(fr, 260, 560, 2))

    def ft_shoulder():  # coil low on the back foot, then the whole body behind the near shoulder: an armoured charge
        fr = [(P(IR, dx=-2, dy=4, head_dx=-1, hand=(31, 25), ang=-100, offw=ow(30, 26, -100, False), footB=(OX + 3, 39), footF=(OX + 20, 39), flow=0.3), 160),
              (P(IR, dx=-2, dy=5, head_dx=-1, head_dy=1, hand=(30, 26), ang=-110, offw=ow(29, 27, -100, False), footB=(OX + 3, 39), footF=(OX + 20, 39),
                 flow=0.3, flutter=1, fx=[("dust", 22, 2)], fx_pal=IRON), 160),
              (P(IR, dx=5, dy=3, lean=3, head_dx=1, hand=(35, 25), ang=-100, offw=ow(33, 26, -100, False), footB=(OX + 9, 39), footF=(OX + 28, 39),
                 flow=1.6, flutter=2, fx=[("speed", (32, 18), 4, 14), ("flare", (44, 21), 5), ("dust", 24, 3)], fx_pal=IRON), 70),
              (P(IR, dx=6, dy=3, lean=3, head_dx=1, hand=(35, 25), ang=-100, offw=ow(33, 26, -100, False), footB=(OX + 10, 39), footF=(OX + 28, 39),
                 flow=1.2, flutter=3, fx=[("dust", 46, 3)], fx_pal=IRON), 150),
              (P(IR, dx=4, dy=3, lean=1, flow=0.6, flutter=4, footB=(OX + 8, 39), footF=(OX + 26, 39)), 120),
              (P(IR, dx=3, flow=0.4, flutter=5, footB=(OX + 7, 39), footF=(OX + 25, 39)), 100)]
        return fseq(tm(fr, 320, 740, 2))

    def ft_hammer():  # both fists raised high and joined, then brought straight down like a mallet
        fr = [(P(IR, dx=0, dy=1, head_dy=-1, hand=(31, 9), ang=-100, offw=ow(32, 10, -95, False), footB=(OX + 5, 39), flow=0.4), 170),
              (P(IR, dx=-1, dy=0, head_dx=-1, head_dy=-1, lean=-1, hand=(29, 7), ang=-130, offw=ow(30, 8, -125, False), footB=(OX + 5, 39),
                 flow=0.4, flutter=1, fx=[("glint", (30, 4))], fx_pal=IRON), 170),
              (P(IR, dx=3, dy=4, lean=2, hand=(42, 29), ang=70, offw=ow(41, 28, 70), footB=(OX + 6, 39), footF=(OX + 25, 39), flow=1.2, flutter=2,
                 fx=[("ring", (31, 21), 14, -110, 50, dict(sq=1.0, w=3.2)), ("flare", (44, 33), 5)], fx_pal=IRON), 60),
              (P(IR, dx=3, dy=5, lean=2, hand=(42, 31), ang=80, offw=ow(41, 30, 80), footB=(OX + 6, 39), footF=(OX + 25, 39), flow=0.8, flutter=3,
                 fx=[("dust", 46, 3)], fx_pal=IRON), 180),
              (P(IR, dx=2, flow=0.4, flutter=4, footF=(OX + 24, 39)), 220)]
        return fseq(tm(fr, 340, 800, 2))

    def ft_stomp():  # haul the front knee up to the chest, then stamp it through the floor: the ground cracks both ways
        fr = [(P(IR, dx=0, dy=1, hand=(30, 26), offw=ow(37, 21, -75), kF=dict(foot=(OX + 20, 32), toe=10, seg=5.6), footB=(OX + 7, 39), flow=0.4), 180),
              (P(IR, dx=0, dy=-1, lean=-1, hand=(30, 24), offw=ow(36, 19, -75), kF=dict(foot=(OX + 21, 28), toe=15, seg=5.6), footB=(OX + 8, 39),
                 flow=0.5, flutter=1), 180),
              (P(IR, dx=2, dy=5, hand=(32, 31), ang=60, offw=ow(39, 29, 40), footB=(OX + 5, 39), footF=(OX + 24, 39), flow=1.0, flutter=2,
                 fx=[("dust", 39, 7), ("dust", 14, 4), ("flare", (39, 38), 7), ("vspeed", (38, 30), 2, 7)], fx_pal=IRON), 80),
              (P(IR, dx=2, dy=5, hand=(32, 31), ang=60, offw=ow(39, 29, 40), footB=(OX + 5, 39), footF=(OX + 24, 39), flow=0.6, flutter=3,
                 fx=[("dust", 46, 5), ("dust", 8, 3)], fx_pal=IRON), 220),
              (P(IR, dx=1, flow=0.3, flutter=4), 240)]
        return fseq(tm(fr, 360, 900, 2))

    def ft_ichg():  # (loop) the iron fist: wound back to the far hip, the lead palm aimed, the knuckles slowly heating
        fr = []
        for i in range(4):
            fr.append((P(IR, dx=-2, dy=4 + (i % 2), head_dx=-1, hand=(25, 30 + (i % 2)), ang=180, offw=ow(39, 23 + (i % 2), -70),
                         footB=(OX + 3, 39), footF=(OX + 22, 39), flow=0.3, flutter=i,
                         fx=[("flare", (22, 30 + (i % 2)), 2 + (i % 2))], fx_pal=IRON), 130))
        return fseq(fr)

    def ft_ifist():  # out of the coil: one long step, the hip snaps round, the iron fist straight through
        fr = [(P(IR, dx=-2, dy=4, head_dx=-1, hand=(25, 30), ang=180, offw=ow(39, 23, -70), footB=(OX + 3, 39), footF=(OX + 22, 39),
                 flow=0.3, fx=[("flare", (22, 30), 4)], fx_pal=IRON), 160),
              (P(IR, dx=5, dy=3, lean=2, hand=(48, 23), ang=0, offw=ow(31, 26, -100, False), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=1.6,
                 flutter=1, fx=[("speed", (44, 24), 4, 16), ("flare", (53, 23), 7), ("dust", 44, 3)], fx_pal=IRON), 70),
              (P(IR, dx=5, dy=3, lean=2, hand=(47, 23), ang=0, offw=ow(31, 26, -100, False), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=1.1,
                 flutter=2, fx=[("flare", (53, 23), 3)], fx_pal=IRON), 170),
              (P(IR, dx=3, dy=3, flow=0.6, flutter=3, footB=(OX + 7, 39), footF=(OX + 26, 39)), 120),
              (P(IR, dx=2, flow=0.4, flutter=4, footB=(OX + 6, 39), footF=(OX + 25, 39)), 100)]
        return fseq(tm(fr, 160, 620, 1))

    def ft_throw():  # seize the foe with both hands, haul it in, and heave it over the near shoulder to slam behind you
        fr = [(P(IR, dx=1, dy=3, hand=(42, 22), ang=-10, offw=ow(42, 20, -20), footF=(OX + 25, 39), flow=0.5), 140),
              (P(IR, dx=2, dy=3, hand=(44, 22), ang=0, offw=ow(44, 20, -5), footF=(OX + 26, 39), flow=0.7, flutter=1,
                 fx=[("flare", (48, 21), 4)], fx_pal=IRON), 100),
              (P(IR, dx=0, dy=4, lean=-1, hand=(36, 21), ang=-60, offw=ow(37, 20, -60), footB=(OX + 4, 39), footF=(OX + 24, 39), flow=0.6, flutter=2), 110),
              (P(IR, dx=-1, dy=2, lean=-2, head_dx=-1, hand=(29, 9), ang=-110, offw=ow(30, 10, -110, False), footB=(OX + 4, 39), footF=(OX + 22, 39),
                 flow=1.0, flutter=3, fx=[("ring", (28, 21), 14, -10, -170, dict(sq=1.0, w=3.0))], fx_pal=IRON), 110),
              (P(IR, dx=-2, dy=5, lean=-1, head_dx=-1, hand=(19, 30), ang=150, offw=ow(20, 29, 150, False), footB=(OX + 2, 39), footF=(OX + 21, 39),
                 flow=0.5, flutter=4, fx=[("dust", 10, 6), ("flare", (12, 36), 6)], fx_pal=IRON), 160),
              (P(IR, dx=-1, flow=0.3, flutter=5), 180)]
        return fseq(tm(fr, 240, 800, 1))

    def ft_pillar():  # sink, then the front leg rises straight up the foe's body: a heel aimed at the sky
        fr = [(P(IR, dx=0, dy=5, head_dy=1, hand=(30, 30), offw=ow(37, 25, -75), footB=(OX + 4, 39), footF=(OX + 22, 39), flow=0.3), 150),
              (P(IR, dx=0, dy=1, lean=-1, hand=(30, 27), offw=ow(36, 23, -60), kF=dict(foot=(OX + 25, 29), toe=-40, seg=6.4), footB=(OX + 8, 39),
                 flow=0.6, flutter=1), 150),
              (P(IR, dx=0, dy=1, lean=-3, hand=(29, 27), ang=150, offw=ow(33, 25, 130, False), kF=dict(foot=(OX + 22, 16), toe=-85, seg=6.8),
                 footB=(OX + 9, 39), flow=1.2, flutter=2,
                 fx=[("ring", (OX + 15, OY + 20), 13, 10, -85, dict(sq=1.0, w=3.4)), ("vspeed", (OX + 23, 30), 2, 9), ("flare", (OX + 22, 10), 5)],
                 fx_pal=IRON), 90),
              (P(IR, dx=0, dy=1, lean=-3, hand=(29, 27), ang=150, offw=ow(33, 25, 130, False), kF=dict(foot=(OX + 22, 17), toe=-85, seg=6.8),
                 footB=(OX + 9, 39), flow=0.9, flutter=3), 160),
              (P(IR, dx=0, dy=2, lean=-1, kF=dict(foot=(OX + 22, 30), toe=10, seg=5.8), footB=(OX + 7, 39), flow=0.6, flutter=4), 110),
              (P(IR, dx=1, flow=0.3, flutter=5), 100)]
        return fseq(tm(fr, 300, 760, 2))

    def ft_heaven():  # the deepest crouch, the near fist near the floor; then the whole body rises behind one uppercut
        fr = [(P(IR, dx=0, dy=6, head_dy=1, hand=(32, 33), ang=-70, offw=ow(37, 25, -75), footB=(OX + 3, 39), footF=(OX + 23, 39), flow=0.3), 160),
              (P(IR, dx=0, dy=6, head_dy=1, hand=(33, 34), ang=-80, offw=ow(37, 26, -75), footB=(OX + 3, 39), footF=(OX + 23, 39), flow=0.3,
                 flutter=1, fx=[("glint", (34, 37))], fx_pal=IRON), 140),
              (P(IR, dx=2, dy=-2, head_dy=-1, hand=(37, 5), ang=-88, offw=ow(33, 24, -100, False), footB=(OX + 8, 39), footF=(OX + 22, 39), flow=1.3,
                 flutter=2, fx=[("vspeed", (37, 26), 3, 12), ("flare", (37, 0), 6), ("dust", 36, 3)], fx_pal=IRON), 80),
              (P(IR, dx=2, dy=-1, hand=(37, 7), ang=-85, offw=ow(33, 24, -100, False), footB=(OX + 8, 39), footF=(OX + 22, 39), flow=1.0, flutter=3), 160),
              (P(IR, dx=1, dy=2, flow=0.5, flutter=4), 160)]
        return fseq(tm(fr, 300, 700, 2))

    def ft_istep():  # the iron step: weight shifts, one heavy planted step, settle low again
        return fseq([(P(IR, dx=-1, dy=4, footB=(OX + 4, 39), footF=(OX + 22, 39), flow=0.6), 90),
                     (P(IR, dx=1, dy=2, footB=(OX + 7, 37), footF=(OX + 24, 39), flow=0.9, flutter=1), 110),
                     (P(IR, dx=2, dy=4, footB=(OX + 6, 39), footF=(OX + 25, 39), flow=0.5, flutter=2, fx=[("dust", 39, 2)], fx_pal=IRON), 80),
                     (P(IR, dx=1, dy=3, flow=0.3, flutter=3), 60)])

    def ft_bash():  # out of the iron step: a short hop in behind the near shoulder
        fr = [(P(IR, dx=-1, dy=4, head_dx=-1, hand=(31, 25), ang=-100, offw=ow(30, 26, -100, False), footB=(OX + 4, 39), flow=0.6), 200),
              (P(IR, dx=5, dy=3, lean=3, head_dx=1, hand=(35, 24), ang=-100, offw=ow(33, 25, -100, False), footB=(OX + 10, 38), footF=(OX + 27, 39),
                 flow=1.6, flutter=1, fx=[("speed", (32, 17), 4, 12), ("flare", (44, 20), 5)], fx_pal=IRON), 70),
              (P(IR, dx=5, dy=3, lean=2, hand=(35, 24), ang=-100, offw=ow(33, 25, -100, False), footB=(OX + 9, 39), footF=(OX + 27, 39),
                 flow=1.0, flutter=2, fx=[("dust", 45, 3)], fx_pal=IRON), 150),
              (P(IR, dx=2, flow=0.4, flutter=3, footB=(OX + 6, 39), footF=(OX + 25, 39)), 140)]
        return fseq(tm(fr, 200, 560, 1))

    # ------------------------------------------------------------------ SWITCHING
    def ft_toiron():  # from the toes down into the roots: the guard opens, both palms press down, the knuckles take the heat
        return fseq([(P(SW, dy=0, hand=(36, 18), ang=-80, offw=ow(37, 17, -90), flow=0.4), 70),
                     (P(SW, dy=2, hand=(37, 26), ang=10, offw=ow(38, 25, 10), footB=(OX + 7, 39), footF=(OX + 20, 39), flow=0.4, flutter=1), 70),
                     (P(IR, dy=4, hand=(31, 30), offw=ow(38, 22, -75), flow=0.3, flutter=2, fx=[("flare", (32, 31), 4), ("flare", (39, 22), 3),
                                                                                                     ("dust", 14, 3), ("dust", 38, 3)], fx_pal=IRON), 90),
                     (P(IR, flow=0.2, flutter=3), 70)])

    def ft_toswift():  # out of the roots onto the toes: a light hop, the fists flick up into the high guard
        return fseq([(P(IR, dy=4, flow=0.3), 70),
                     (P(SW, dy=-1, hand=(35, 18), offw=ow(38, 19, -40), footB=(OX + 9, 37), footF=(OX + 19, 38), air=True, flow=0.8, flutter=1,
                        fx=[("speed", (30, 19), 2, 6)], fx_pal=SWIFT), 80),
                     (P(SW, dy=1, flow=0.5, flutter=2, fx=[("glint", (40, 18))], fx_pal=SWIFT), 80),
                     (P(SW, flow=0.3, flutter=3), 70)])

    def ft_fstar():  # the Shift into Iron: a hop, the front heel raised over the head, dropped like a falling star
        fr = [(P(SW, dx=0, dy=1, lean=-1, kF=dict(foot=(OX + 22, 30), toe=-20), footB=(OX + 9, 39), flow=0.5), 90),
              (P(SW, dx=1, dy=-2, lean=-3, hand=(31, 22), ang=150, offw=ow(33, 23, 140, False), kF=dict(foot=(OX + 23, 13), toe=-80, seg=6.8),
                 footB=(OX + 10, 37), air=True, flow=0.9, flutter=1, fx=[("glint", (OX + 23, 10))], fx_pal=IRON), 170),
              (P(IR, dx=3, dy=1, lean=1, hand=(32, 26), ang=60, offw=ow(37, 25, 40), kF=dict(foot=(OX + 28, 37), toe=10, seg=6.6),
                 footB=(OX + 9, 39), flow=1.4, flutter=2,
                 fx=[("ring", (OX + 18, OY + 20), 13, -80, 70, dict(sq=1.0, w=3.6)), ("flare", (OX + 30, 37), 6), ("dust", OX + 30, 5)],
                 fx_pal=IRON), 70),
              (P(IR, dx=3, dy=4, hand=(32, 28), ang=60, offw=ow(37, 25, -40), footB=(OX + 7, 39), footF=(OX + 26, 39), flow=0.9, flutter=3,
                 fx=[("dust", OX + 30, 3)], fx_pal=IRON), 160),
              (P(IR, dx=2, flow=0.4, flutter=4, footF=(OX + 25, 39)), 150)]
        return fseq(tm(fr, 260, 640, 2))

    def ft_wind():  # the Shift into Swift: four quick blows, far, near, far, near, the body unwinding out of the root
        fr = [(P(IR, dx=0, dy=3, flow=0.4), 120)]
        for i in range(4):
            near = i % 2 == 1
            y = 21 + (i % 3) - 1
            fr.append((P(SW, dx=2 + i // 2, dy=1, lean=1, hand=(46, y) if near else (34, 22), ang=-3 if near else -60,
                         offw=ow(34, 22, -60) if near else ow(46, y, -3), footB=(OX + 10, 39), footF=(OX + 22, 39), flow=1.0 + 0.1 * i, flutter=i,
                         fx=[("speed", (42, y + 1), 2, 9), ("flare", (51, y), 3)], fx_pal=SWIFT), 65))
        fr += [(P(SW, dx=3, dy=1, flow=0.7, flutter=5, footF=(OX + 22, 39)), 70), (P(SW, dx=1, flow=0.4, flutter=6), 80)]
        return fseq(tm(fr, 120, 520, 1))

    def ft_tempest():  # Tempest to mountain: a Swift flurry of four, then both fists rise and fall as one Iron hammer
        fr = [(P(SW, dx=0, dy=1, flow=0.5), 100)]
        for i in range(4):
            near = i % 2 == 1
            y = 21 + (i % 3) - 1
            fr.append((P(SW, dx=2 + i // 2, dy=1, lean=1, hand=(46, y) if near else (34, 22), ang=-3 if near else -60,
                         offw=ow(34, 22, -60) if near else ow(46, y, -3), footB=(OX + 10, 39), footF=(OX + 22, 39), flow=1.0 + 0.1 * i, flutter=i,
                         fx=[("speed", (42, y + 1), 2, 9), ("flare", (51, y), 3)], fx_pal=SWIFT), 70))
        fr += [(P(IR, dx=3, dy=0, head_dy=-1, lean=-1, hand=(31, 7), ang=-120, offw=ow(32, 8, -115, False), footB=(OX + 7, 39), footF=(OX + 26, 39),
                  flow=0.8, flutter=5, fx=[("glint", (31, 3))], fx_pal=IRON), 160),
               (P(IR, dx=5, dy=4, lean=2, hand=(44, 29), ang=70, offw=ow(43, 28, 70), footB=(OX + 8, 39), footF=(OX + 27, 39), flow=1.4, flutter=6,
                  fx=[("ring", (33, 21), 14, -120, 50, dict(sq=1.0, w=3.4)), ("flare", (46, 33), 6), ("dust", 47, 5)], fx_pal=IRON), 70),
               (P(IR, dx=5, dy=5, lean=2, hand=(44, 31), ang=80, offw=ow(43, 30, 80), footB=(OX + 8, 39), footF=(OX + 27, 39), flow=0.8, flutter=7), 200),
               (P(IR, dx=3, flow=0.4, flutter=8, footF=(OX + 25, 39)), 160)]
        return fseq(tm(fr, 100, 900, 1))

    def ft_release():  # Iron to wind: the coiled fist let go as a flying straight, the body stretched out through the foe
        fr = [(P(IR, dx=-2, dy=4, head_dx=-1, hand=(25, 30), ang=180, offw=ow(39, 23, -70), footB=(OX + 3, 39), footF=(OX + 22, 39),
                 flow=0.4, fx=[("flare", (22, 30), 4)], fx_pal=IRON), 90),
              (P(SW, dx=6, dy=2, lean=3, head_dx=1, hand=(49, 22), ang=0, offw=ow(32, 24, -100, False), footB=(OX + 9, 38), footF=(OX + 27, 38),
                 air=True, flow=2.0, flutter=1, fx=[("speed", (45, 23), 4, 22), ("flare", (54, 22), 5)], fx_pal=SWIFT), 80),
              (P(SW, dx=5, dy=2, lean=2, hand=(47, 22), ang=0, offw=ow(32, 24, -100, False), footB=(OX + 10, 39), footF=(OX + 26, 39), flow=1.4,
                 flutter=2, fx=[("speed", (40, 23), 3, 12)], fx_pal=SWIFT), 110),
              (P(SW, dx=3, dy=1, flow=0.8, flutter=3, footF=(OX + 23, 39)), 100),
              (P(SW, dx=1, flow=0.4, flutter=4), 100)]
        return fseq(tm(fr, 90, 480, 1))

    def ft_ember():  # Ember palm: both hands drawn to the hip as the wraps catch, then both palms driven out as one
        fr = [(P(IR, dx=-1, dy=4, head_dx=-1, hand=(26, 29), ang=180, offw=ow(27, 30, 180, False), footB=(OX + 3, 39), footF=(OX + 21, 39),
                 flow=0.4, aura=1, aura_pal=EMBERP, fx=[("flare", (25, 29), 4)], fx_pal=EMBERP), 130),
              (P(IR, dx=-2, dy=5, head_dx=-1, head_dy=1, hand=(25, 30), ang=180, offw=ow(26, 31, 180, False), footB=(OX + 3, 39), footF=(OX + 21, 39),
                 flow=0.6, flutter=1, aura=2, aura_pal=EMBERP, fx=[("flare", (24, 30), 6), ("embers", (26, 24), 6, 3)], fx_pal=EMBERP), 130),
              (P(IR, dx=-2, dy=5, head_dx=-1, head_dy=1, hand=(25, 29), ang=180, offw=ow(26, 30, 180, False), footB=(OX + 3, 39), footF=(OX + 21, 39),
                 flow=0.6, flutter=2, aura=2, aura_pal=EMBERP, fx=[("flare", (24, 29), 7), ("embers", (26, 22), 7, 5)], fx_pal=EMBERP), 120),
              (P(IR, dx=5, dy=3, lean=2, hand=(47, 21), ang=0, offw=ow(47, 25, 0), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=2.0, flutter=3,
                 aura=2, aura_pal=EMBERP, fx=[("speed", (43, 23), 4, 18), ("flare", (53, 23), 11), ("dust", 46, 4)], fx_pal=EMBERP), 80),
              (P(IR, dx=5, dy=3, lean=2, hand=(46, 21), ang=0, offw=ow(46, 25, 0), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=1.4, flutter=4,
                 fx=[("flare", (53, 23), 6), ("embers", (52, 22), 8, 9)], fx_pal=EMBERP), 220),
              (P(IR, dx=3, dy=3, flow=0.7, flutter=5, footB=(OX + 7, 39), footF=(OX + 26, 39)), 120),
              (P(IR, dx=2, flow=0.4, flutter=6, footB=(OX + 6, 39), footF=(OX + 25, 39)), 100)]
        return fseq(tm(fr, 380, 900, 3))

    # ------------------------------------------------------------------ AIR
    AIRL = dict(footB=(OX + 9, 35), footF=(OX + 18, 35), air=True)

    def ft_akick():  # in the air: the front leg snaps straight out, the body tipping back behind it
        fr = [(P(SW, dy=-2, lean=-1, kF=dict(foot=(OX + 20, 30), toe=40, seg=5.6), footB=(OX + 9, 34), air=True, flow=0.8), 110),
              (P(SW, dy=-2, lean=-2, kF=dict(foot=(OX + 29, 27), toe=-5, seg=6.4), footB=(OX + 9, 35), air=True, flow=1.3, flutter=1,
                 fx=[("ring", (OX + 15, OY + 18), 12, 80, -5, dict(sq=1.0, w=3.0)), ("flare", (OX + 33, 26), 3)], fx_pal=SWIFT), 70),
              (P(SW, dy=-2, lean=-1, kF=dict(foot=(OX + 27, 28), toe=-5, seg=6.4), footB=(OX + 9, 35), air=True, flow=1.0, flutter=2), 60),
              (P(SW, dy=-2, flow=0.6, flutter=3, **AIRL), 60)]
        return fseq(tm(fr, 110, 300, 1))

    def ft_akick3():  # three scissor kicks in the air: back leg, front leg, back leg, each snapping past the last
        fr = [(P(SW, dy=-3, lean=-1, kB=dict(foot=(OX + 18, 31), toe=40, seg=5.6), footF=(OX + 22, 33), air=True, flow=0.8), 100)]
        for i, (k, y) in enumerate((("kB", 27), ("kF", 25), ("kB", 23))):
            other = dict(footF=(OX + 19, 34)) if k == "kB" else dict(footB=(OX + 10, 34))
            fr.append((P(SW, dy=-3, lean=-2, **{k: dict(foot=(OX + 29, y), toe=-8 - 6 * i, seg=6.4)}, **other, air=True, flow=1.2 + 0.1 * i,
                         flutter=i + 1, fx=[("ring", (OX + 14, OY + 17), 12, 90, -8 - 6 * i, dict(sq=1.0, w=3.0)), ("flare", (OX + 33, y - 1), 3)],
                         fx_pal=SWIFT), 70))
            if i < 2:
                fr.append((P(SW, dy=-3, lean=-1, footB=(OX + 12, 33), footF=(OX + 19, 33), air=True, flow=1.0, flutter=i + 4), 20))
        fr.append((P(SW, dy=-2, flow=0.6, flutter=7, **AIRL), 120))
        return fseq(tm(fr, 100, 440, 1))

    def ft_aelbow():  # hang, the near elbow cocked high; then drop at a slant, elbow first, and crash into the floor
        TK = dict(footB=(OX + 8, 32), footF=(OX + 16, 33), air=True)
        fr = [(P(IR, dy=-4, hand=(32, 14), ang=-150, offw=ow(37, 22, -75), flow=0.8, **TK), 80),
              (P(IR, dy=-4, head_dx=-1, hand=(31, 12), ang=-160, offw=ow(36, 21, -75), flow=0.9, flutter=1, fx=[("glint", (36, 15))], fx_pal=IRON, **TK), 80),
              (P(IR, dx=2, dy=-3, lean=2, hand=(33, 19), ang=180, offw=ow(34, 23, -100, False), flow=1.4, flutter=2,
                 fx=[("flare", (39, 25), 4)] + G.DIVE(8), fx_pal=IRON, footB=(OX + 5, 31), footF=(OX + 10, 33), bendB=-1, bendF=-1, air=True), 70),
              (P(IR, dx=2, dy=-3, lean=2, hand=(33, 19), ang=180, offw=ow(34, 23, -100, False), flow=1.6, flutter=3,
                 fx=[("flare", (39, 25), 3)] + G.DIVE(10, 1), fx_pal=IRON, footB=(OX + 5, 32), footF=(OX + 11, 33), bendB=-1, bendF=-1, air=True), 70),
              (P(IR, dx=3, dy=6, head_dy=1, lean=2, hand=(36, 29), ang=150, offw=ow(37, 31, 90), footB=(OX + 5, 39), footF=(OX + 24, 39), flow=0.8,
                 flutter=4, fx=[("dust", 42, 6), ("flare", (42, 37), 6)], fx_pal=IRON), 120),
              (P(IR, dx=2, flow=0.4, flutter=5), 140)]
        return G.cape_dive(fseq(fr), [2, 3], dy=-2)

    def ft_aheel():  # hang, the heel lifted overhead; then a steep heel-first dive, and a stamp that cracks the floor
        fr = [(P(SW, dy=-4, lean=-1, kF=dict(foot=(OX + 21, 29), toe=-30, seg=5.6), footB=(OX + 9, 33), air=True, flow=0.8), 75),
              (P(SW, dy=-4, lean=-3, hand=(31, 22), ang=150, offw=ow(33, 23, 140, False), kF=dict(foot=(OX + 22, 12), toe=-80, seg=6.6),
                 footB=(OX + 10, 34), air=True, flow=1.0, flutter=1, fx=[("glint", (OX + 22, 9))]), 75),
              (P(SW, dx=1, dy=-5, lean=0, hand=(33, 20), ang=-90, offw=ow(35, 21, -90), kF=dict(foot=(OX + 22, 38), toe=70, seg=6.0),
                 footB=(OX + 9, 31), bendB=-1, air=True, flow=1.6, flutter=2, fx=G.DIVE(9) + [("flare", (OX + 22, 38), 3)]), 85),
              (P(SW, dx=1, dy=-5, hand=(33, 20), ang=-90, offw=ow(35, 21, -90), kF=dict(foot=(OX + 22, 38), toe=70, seg=6.0),
                 footB=(OX + 9, 32), bendB=-1, air=True, flow=1.8, flutter=3, fx=G.DIVE(11, 1)), 85),
              (P(SW, dx=1, dy=5, head_dy=1, hand=(34, 28), ang=-30, offw=ow(37, 27, -30), footB=(OX + 6, 39), footF=(OX + 22, 39), flow=0.8,
                 flutter=4, fx=[("dust", 37, 7), ("flare", (37, 37), 7)], fx_pal=IRON), 140),
              (P(SW, dx=1, flow=0.4, flutter=5), 160)]
        return G.cape_dive(fseq(fr), [2, 3], dy=-2)

    def ft_astomp():  # pull both knees up, then stamp both heels straight down: bounce off whatever is underneath
        fr = [(P(SW, dy=-4, hand=(34, 19), offw=ow(37, 20, -40), footB=(OX + 9, 32), footF=(OX + 17, 32), air=True, flow=0.7), 100),
              (P(SW, dy=-6, hand=(33, 18), offw=ow(36, 19, -40), kF=dict(foot=(OX + 16, 36), toe=90, seg=6.0), kB=dict(foot=(OX + 12, 36), toe=95, seg=6.0),
                 air=True, flow=1.2, flutter=1, fx=[("vspeed", (OX + 14, 26), 2, 8), ("flare", (OX + 15, 39), 4)], fx_pal=SWIFT), 70),
              (P(SW, dy=-6, hand=(33, 18), offw=ow(36, 19, -40), kF=dict(foot=(OX + 16, 36), toe=90, seg=6.0), kB=dict(foot=(OX + 12, 36), toe=95, seg=6.0),
                 air=True, flow=1.0, flutter=2), 60),
              (P(SW, dy=-3, flow=0.6, flutter=3, **AIRL), 50)]
        return fseq(tm(fr, 100, 280, 1))

    # ------------------------------------------------------------------ registry
    T = lambda a, b: dict(active=(a, b))
    moves = [
        ("ft_sw_idle", ft_sw_idle, {}, False), ("ft_sw_run", ft_sw_run, {}, False), ("ft_ir_idle", ft_ir_idle, {}, False),
        ("ft_ir_walk", ft_ir_walk, {}, False), ("ft_slip", ft_slip, {}, False), ("ft_istep", ft_istep, {}, False),
        ("ft_hundred", ft_hundred, {}, False), ("ft_ichg", ft_ichg, {}, False),
        ("ft_toiron", ft_toiron, {}, False), ("ft_toswift", ft_toswift, {}, False),
        ("ft_jab", ft_jab, dict(T(1, 1), hit=[6, -27, 26, -11], fxat=(20, -19)), True),
        ("ft_cross", ft_cross, dict(T(1, 1), hit=[6, -27, 27, -11], fxat=(21, -19)), True),
        ("ft_hook", ft_hook, dict(T(2, 2), hit=[4, -30, 24, -12], fxat=(18, -21)), True),
        ("ft_knee", ft_knee, dict(T(2, 6), hits=[2, 4, 6], hit=[2, -28, 22, -6], fxat=(14, -16)), True),
        ("ft_backfist", ft_backfist, dict(T(2, 2), hit=[-4, -30, 26, -12], fxat=(20, -22)), True),
        ("ft_snap", ft_snap, dict(T(2, 3), hit=[4, -24, 30, -6], fxat=(22, -13)), True),
        ("ft_round", ft_round, dict(T(1, 3), hits=[1, 3], hit=[2, -32, 30, -8], fxat=(20, -18)), True),
        ("ft_rknee", ft_rknee, dict(T(2, 2), hit=[2, -32, 22, -6], fxat=(13, -20)), True),
        ("ft_whirl", ft_whirl, dict(T(1, 2), hits=[1, 2], both=True, hit=[-30, -28, 30, -8], fxat=(20, -16)), True),
        ("ft_upper", ft_upper, dict(T(2, 3), hit=[0, -46, 18, -14], fxat=(9, -32)), True),
        ("ft_sjab", ft_sjab, dict(T(1, 1), hit=[6, -26, 28, -10], fxat=(22, -19)), True),
        ("ft_sweep", ft_sweep, dict(T(2, 3), hit=[0, -14, 32, 0], fxat=(20, -3)), True),
        ("ft_fcounter", ft_fcounter, dict(T(1, 2), hit=[4, -28, 28, -10], fxat=(22, -18)), True),
        ("ft_palm", ft_palm, dict(T(2, 2), hit=[6, -26, 28, -8], fxat=(22, -16)), True),
        ("ft_elbow", ft_elbow, dict(T(2, 2), hit=[4, -28, 24, -8], fxat=(16, -18)), True),
        ("ft_shoulder", ft_shoulder, dict(T(2, 3), hit=[2, -30, 24, -4], fxat=(16, -18)), True),
        ("ft_hammer", ft_hammer, dict(T(2, 3), hit=[2, -32, 26, 0], fxat=(16, -8)), True),
        ("ft_stomp", ft_stomp, dict(T(2, 2), hit=[-4, -16, 22, 0], fxat=(11, -3)), True),
        ("ft_ifist", ft_ifist, dict(T(1, 2), hit=[6, -26, 30, -8], fxat=(24, -16)), True),
        ("ft_throw", ft_throw, dict(T(1, 1), hit=[4, -28, 24, -6], fxat=(18, -18)), True),
        ("ft_pillar", ft_pillar, dict(T(2, 3), hit=[0, -44, 18, -8], fxat=(8, -28)), True),
        ("ft_heaven", ft_heaven, dict(T(2, 3), hit=[0, -50, 18, -12], fxat=(9, -36)), True),
        ("ft_bash", ft_bash, dict(T(1, 2), hit=[2, -30, 24, -4], fxat=(16, -18)), True),
        ("ft_fstar", ft_fstar, dict(T(2, 3), hit=[2, -40, 26, 0], fxat=(16, -6)), True),
        ("ft_wind", ft_wind, dict(T(1, 4), hits=[1, 2, 3, 4], hit=[6, -27, 27, -11], fxat=(20, -19)), True),
        ("ft_tempest", ft_tempest, dict(T(1, 6), hits=[1, 2, 3, 4, 6], hit=[4, -30, 27, 0], fxat=(20, -14)), True),
        ("ft_release", ft_release, dict(T(1, 2), hit=[4, -28, 30, -8], fxat=(24, -18)), True),
        ("ft_ember", ft_ember, dict(T(3, 4), hit=[4, -30, 32, -6], fxat=(25, -17)), True),
        ("ft_akick", ft_akick, dict(T(1, 2), hit=[2, -24, 28, -6], fxat=(20, -14)), False),
        ("ft_akick3", ft_akick3, dict(T(1, 5), hits=[1, 3, 5], hit=[2, -28, 28, -6], fxat=(20, -16)), False),
        ("ft_aelbow", ft_aelbow, dict(T(2, 3), hit=[-2, -26, 18, 6], fxat=(11, -15)), False),
        ("ft_aheel", ft_aheel, dict(T(2, 3), hit=[-6, -14, 12, 8], fxat=(8, -2)), False),
        ("ft_astomp", ft_astomp, dict(T(1, 2), down=True, hit=[-8, -12, 10, 12], fxat=(1, 0)), False),
    ]
    SETTLE = {"ft_hook", "ft_backfist", "ft_upper", "ft_fcounter"}   # ground attacks that end near the guard ease back
    return [(t, G.settled(f) if t in SETTLE else f, o) for t, f, o, _ in moves]
