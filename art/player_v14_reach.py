"""v14 combo pass: new player tags for the reach group -- Staff (st_, quarterstaff) and Whip (wh_, headsman_chain).
Registered by gen_player.py with the same register(G) contract as player_v13_a.py: [(tag, fn, opts)], fn() -> [(cels, ms)].

Every attack is timed to its move row in web/src/76_mech_reach.js (wind-up = the frames before the first active frame,
total = all frames; tm() rescales the hand-timed frames onto those two numbers) and reads anticipation -> smear -> impact
-> follow-through -> settle.

  st_rise      J J K        pole launcher: plant low behind, heave the staff up through the foe, ride it up   170 / 470
  st_vkick     I -> J       vault kick: tucked over the pole, both legs swung through in a flying kick          110 / 360
  st_air2      air J J      cartwheel: turn over the staff, butt end down behind, then the head chops in front 120 / 400 (2)
  st_pdrop     ↓J -> K      pole drop: hang, flip the point down, ride it into the floor, a shock both sides   150 / 520
  wh_trip      J J K        trip lash: sink low, the chain skims the floor at full length and snaps at the ankle 200 / 560
  wh_coil      L -> K       coil spin: the chain whirled tight round the waist, front, back, then flung out    140 / 520 (2)
  wh_reelkick  grapple -> J reel kick: turn, the chain wrapped round the boot, a spinning heel kick             150 / 460
  wh_air2      air J J      skyfall crack: arm high, the lash cracked down to the floor ahead                  150 / 400
"""

G = None   # gen_player, set by register()


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


# ============================================================================================================== STAFF
def st_rise():  # J J K: the far end planted low behind, then heaved up through the foe -- the vault's lift carries you up
    OX, FF, GT, P_WIND = G.OX, G.FF, G.GRIP_STAFF, G.P_WIND
    up = dict(footB=(OX + 9, 36), footF=(OX + 17, 37), air=True)
    fr = [(dict(dx=-1, dy=3, hand=(29, 28), ang=164, footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.3), 80),
          (dict(dx=-2, dy=4, head_dy=1, head_dx=-1, hand=(28, 29), ang=172, footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.2,
                flutter=1, fx=[("glint", "tip"), ("dust", 12, 2)]), 90),
          (dict(dx=2, dy=1, hand=(36, 21), ang=-62, footB=(OX + 7, 39), footF=(FF[0] + 3, 39), flow=1.2, flutter=2,
                fx=[G.sw(w=0.55), ("dust", 44, 4), ("speed", (36, 34), 3, 8, P_WIND)]), 45),
          (dict(dx=1, dy=-2, hand=(35, 13), ang=-96, flow=1.4, flutter=3, fx=[("vspeed", (24, 34), 2, 9, P_WIND), ("vspeed", (38, 33), 2, 7, P_WIND),
                                                                          ("flare", "tip", 4, P_WIND)], **up), 55),
          (dict(dy=-3, hand=(34, 15), ang=-118, flow=1.1, flutter=4, **G.TUCK), 110),
          (dict(dy=-2, hand=(33, 22), ang=-40, flow=0.6, flutter=5, **G.AIR), 90)]
    return G.mseq(tm(fr, 170, 470, 2), grip=GT)


def st_vkick():  # I -> J: tucked over the planted pole, legs drawn back, then both swung through in a flying kick
    OX, GT, P_WIND = G.OX, G.GRIP_STAFF, G.P_WIND
    fr = G.mseq(tm([
        (dict(dy=-3, hand=(34, 26), ang=94, slen=20, footB=(OX + 9, 33), footF=(OX + 17, 33), air=True, flow=1.0), 55),
        (dict(dx=-1, dy=-3, head_dx=-1, hand=(32, 24), ang=122, footB=(OX + 5, 32), footF=(OX + 9, 34), bendB=-1, bendF=-1, air=True,
              flow=0.8, flutter=1), 55),
        (dict(dx=2, dy=-2, hand=(29, 22), ang=172, footB=(OX + 22, 32), footF=(OX + 26, 29), air=True, flow=1.6, flutter=2,
              fx=[("speed", (18, 25), 4, 12, P_WIND), ("flare", (41, 29), 5)]), 50),
        (dict(dx=2, dy=-2, hand=(29, 22), ang=170, footB=(OX + 22, 33), footF=(OX + 27, 30), air=True, flow=1.3, flutter=3,
              fx=[("speed", (17, 26), 3, 10, P_WIND), ("flare", (42, 30), 3)]), 50),
        (dict(dx=1, dy=-2, hand=(32, 22), ang=-30, footB=(OX + 10, 35), footF=(OX + 18, 35), air=True, flow=0.9, flutter=4), 70),
        (dict(hand=(33, 24), ang=-25, flow=0.5, flutter=5, **G.AIR), 80)], 110, 360, 2), grip=GT)
    return G.cape_trail(fr, [2, 3], dy=-4)


def st_air2():  # air J J: turn over the staff -- the butt end comes down behind you, then the head chops through in front
    GT, P_WIND = G.GRIP_STAFF, G.P_WIND
    fr = [(dict(hand=(33, 15), ang=-170, flow=0.6), 60),
          (dict(dx=-1, head_dx=-1, hand=(31, 14), ang=-140, flow=0.8, flutter=1, fx=[("glint", "tip")]), 60),
          (dict(dx=1, hand=(37, 23), ang=34, flow=1.4, flutter=2, mirror=True, fx=[G.sw(w=0.55)]), 60),
          (dict(hand=(33, 13), ang=-100, flow=1.2, flutter=3, fx=[("ring", (34, 22), 15, -170, -100, dict(sq=1.0, w=3.4))]), 60),
          (dict(dx=2, hand=(39, 24), ang=32, flow=1.5, flutter=4, fx=[G.sw(w=0.6), ("flare", "tip", 4, P_WIND)], fx_pal=P_WIND), 50),
          (dict(dx=2, hand=(38, 26), ang=40, flow=0.9, flutter=5), 50),
          (dict(hand=(33, 25), ang=-20, flow=0.5, flutter=6, **G.AIR), 60)]
    return G.mseq(tm(fr, 120, 400, 2), G.AIRB, grip=GT)


def st_pdrop():  # dive kick -> K: hang with the staff overhead, flip the point down, ride it into the floor
    OX, FF, GT, P_WIND = G.OX, G.FF, G.GRIP_STAFF, G.P_WIND
    stomp = dict(footB=(OX + 12, 36), footF=(OX + 16, 37), air=True)
    fr = G.mseq(tm([
        (dict(dy=-3, hand=(33, 13), ang=-90, flow=0.8, **G.TUCK), 70),
        (dict(dy=-4, hand=(34, 22), ang=90, slen=22, flow=1.2, flutter=1, fx=G.DIVE(6), **G.TUCK), 40),
        (dict(dy=-4, hand=(33, 21), ang=90, slen=22, flow=1.5, flutter=2, fx=[("streak", 10)] + G.DIVE(9, 1), **stomp), 40),
        (dict(dy=4, head_dy=1, hand=(38, 26), ang=92, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.6, flutter=3,
              fx=[("dust", 30, 8), ("dust", 46, 8), ("flare", (39, 37), 10, P_WIND), ("speed", (24, 35), 3, 9, P_WIND)]), 60),
        (dict(dy=4, head_dy=1, hand=(38, 26), ang=92, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.4, flutter=4,
              fx=[("dust", 16, 7), ("dust", 58, 7), ("flare", (39, 37), 5, P_WIND)]), 80),
        (dict(dy=2, hand=(34, 22), ang=-80, flow=0.4, flutter=5), 110),
        (dict(hand=(33, 27), ang=-14, flow=0.3, flutter=6), 120)], 150, 520, 3), grip=GT)
    return G.cape_dive(fr, [1, 2], dy=-3)


# ============================================================================================================== WHIP
def wh_trip():  # J J K: sink low and send the chain skimming along the floor at full length; it snaps round the ankle
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=2, hand=(30, 28), ang=160, footB=(OX + 6, 39), flow=0.3, lash=[(25, 32), (19, 36), (13, 38.5), (7, 38.5)]), 80),
          (dict(dx=-2, dy=4, head_dy=1, hand=(28, 30), ang=172, footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.2, flutter=1,
                lash=[(22, 34), (16, 37.5), (10, 38.5), (4, 38.5)], fx=[("glint", (28, 31))]), 120),
          (dict(dx=2, dy=4, head_dy=1, hand=(40, 31), ang=10, footB=(OX + 6, 39), footF=(OX + 24, 39), flow=1.3, flutter=2,
                lash=[(47, 35), (53, 36.5), (58, 37), (63.5, 36.5)], fx=[("dust", 50, 3), ("dust", 60, 3), ("speed", (32, 32), 3, 10)]), 45),
          (dict(dx=2, dy=4, head_dy=1, hand=(41, 31), ang=6, footB=(OX + 6, 39), footF=(OX + 24, 39), flow=1.1, flutter=3,
                lash=[(48, 35.5), (54, 37), (59, 37.5), (63.5, 36)], fx=[("flare", (61, 37), 6), ("dust", 58, 4)]), 55),
          (dict(dx=1, dy=3, hand=(37, 29), ang=30, footF=(FF[0] + 2, 39), flow=0.6, flutter=4,
                lash=[(42, 34), (47, 38.5), (53, 38.5), (58, 36)]), 100),
          (dict(dy=1, hand=(35, 27), ang=0, flow=0.4, flutter=5, lash=[(39, 31), (43, 36), (48, 38.5), (54, 38.5)]), 90),
          (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=6), 70)]
    return G.mseq(tm(fr, 200, 560, 2))


def wh_coil():  # L -> K: the chain whirled tight round the waist -- front, behind -- then flung out flat to the tip
    FF = G.FF
    RG = dict(sq=0.3, w=9.0)
    ring = lambda r: ("ring", (32, 26), r, 180, 0, RG)
    fr = [(dict(dx=-1, dy=2, hand=(31, 24), ang=-150, flow=0.4, lash=[(27, 20), (22, 18), (18, 21), (17, 26)]), 70),
          (dict(dy=1, hand=(30, 20), ang=-120, flow=0.6, flutter=1, lash=[(28, 12), (22, 10), (16, 13), (12, 19)]), 70),
          (dict(dy=1, hand=(37, 23), ang=-5, flow=1.3, flutter=2, lash=[(44, 25), (50, 28), (54, 31), (56, 34)], fx=[ring(22)]), 70),
          (dict(dy=1, hand=(37, 23), ang=-5, flow=1.5, flutter=3, mirror=True, lash=[(44, 25), (50, 28), (54, 31), (56, 34)],
                fx=[ring(22)]), 70),
          (dict(dx=2, hand=(41, 22), ang=-8, footF=(FF[0] + 2, 39), flow=1.5, flutter=4, lash=[(48, 21), (54, 20), (59, 21), (63.5, 22)],
                fx=[("flare", (60, 22), 6), ring(24)]), 50),
          (dict(dx=1, hand=(38, 25), ang=20, flow=0.8, flutter=5, lash=[(44, 29), (49, 34), (54, 38), (60, 38.5)]), 90),
          (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=6), 100)]
    return G.mseq(tm(fr, 140, 520, 2))


def wh_reelkick():  # grapple -> J: turn your back, the chain wrapped round the boot, and a spinning heel kick sends it out
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, hand=(31, 24), ang=160, footF=(OX + 19, 35), flow=0.4, lash=[(27, 30), (25, 34), (28, 37), (32, 36)]), 70),
          (dict(hand=(33, 22), ang=-140, footF=(OX + 18, 36), flow=0.9, flutter=1, mirror=True,
                lash=[(29, 18), (25, 15), (21, 17), (19, 22)], fx=[("speed", (40, 24), 3, 8)]), 80),
          (dict(dx=1, dy=-1, hand=(29, 22), ang=-160, footB=(OX + 8, 39), footF=(OX + 27, 28), flow=1.5, flutter=2,
                lash=[(24, 18), (18, 17), (12, 19), (8, 23)], fx=[("flare", (42, 27), 6), ("speed", (20, 27), 3, 10)]), 50),
          (dict(dx=1, dy=-1, hand=(29, 23), ang=-150, footB=(OX + 8, 39), footF=(OX + 27, 29), flow=1.2, flutter=3,
                lash=[(24, 20), (19, 21), (14, 24), (11, 28)], fx=[("flare", (42, 28), 3)]), 60),
          (dict(dx=1, hand=(32, 25), ang=-60, footF=(FF[0] + 3, 39), flow=0.6, flutter=4, lash=[(36, 30), (38, 35), (42, 38.5), (47, 38.5)]), 90),
          (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=5), 110)]
    return G.mseq(tm(fr, 150, 460, 2))


def wh_air2():  # air J J: out of the circle the arm goes high, then the lash is cracked down to the floor ahead
    fr = [(dict(hand=(32, 13), ang=-110, flow=0.6, lash=[(29, 6), (23, 4), (17, 6), (13, 11)]), 75),
          (dict(dx=-1, head_dx=-1, hand=(30, 12), ang=-135, flow=0.4, flutter=1, lash=[(25, 6), (18, 7), (13, 11), (11, 17)],
                fx=[("glint", (31, 11))]), 75),
          (dict(dx=2, hand=(40, 24), ang=40, flow=1.4, flutter=2, lash=[(46, 29), (52, 33), (57, 36), (62, 39)],
                fx=[("speed", (30, 18), 3, 10), ("flare", (60, 38), 5)]), 45),
          (dict(dx=2, hand=(40, 25), ang=45, flow=1.1, flutter=3, lash=[(45, 31), (51, 35), (56, 38), (61, 39.5)],
                fx=[("flare", (60, 39), 4)]), 55),
          (dict(dx=1, hand=(37, 23), ang=10, flow=0.7, flutter=4, lash=[(42, 27), (46, 32), (49, 36), (51, 39)]), 80),
          (dict(hand=(35, 26), ang=-40, flow=0.5, flutter=5, **G.AIR), 70)]
    return G.mseq(tm(fr, 150, 400, 2), G.AIRB)


def register(g):
    global G
    G = g
    settled = G.settled
    moves = [
        ("st_rise", st_rise, dict(active=(2, 3), up=True)),
        ("st_vkick", st_vkick, dict(active=(2, 3), hit=[-2, -26, 18, -4], fxat=(14, -10))),
        ("st_air2", st_air2, dict(active=(2, 4), hits=[2, 4], both=True)),
        ("st_pdrop", st_pdrop, dict(active=(3, 4), hit=[-34, -30, 34, 0], fxat=(6, -2))),
        ("wh_trip", settled(wh_trip), dict(active=(2, 3), x0=0, fxat=(32, -3))),
        ("wh_coil", settled(wh_coil), dict(active=(2, 4), hits=[2, 4], both=True)),
        ("wh_reelkick", settled(wh_reelkick), dict(active=(2, 3), hit=[0, -24, 16, -4], fxat=(14, -12))),
        ("wh_air2", wh_air2, dict(active=(2, 3), x0=0, fxat=(32, -2))),
    ]
    return moves
