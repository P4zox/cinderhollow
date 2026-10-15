"""v14 combo pass: new player tags for the dual group (registered by gen_player.py, same contract as player_v13_a.py).

register(G) returns [(tag, fn) or (tag, fn, opts)]; fn() returns [(cels, ms), ...] like the v13 tags.

Dual Blades (web/src/76_mech_agile.js). Each tag's wind-up (ms before its first active frame) and total match its move row:
  tw_barrage   J J (pause) J      110 / 470   five alternating stabs, stepping in
  tw_skyward   J J J K            130 / 460   a crouch, then a rising double cut that springs you up
  tw_crossfall air J J            130 / 480   hang, open an X, dive at a slant and land planted
  tw_dfin      Demon J x6 -> K    150 / 640   two crimson spins, a leap, and a crossed cut down
  tw_reversal  L -> K             110 / 420   turn out of the roll low, two rising cuts
v14c (J/K mixes):
  tw_spiral    K -> J             120 / 480   a corkscrew: two turns with the blades held out like a wheel (4 hits)
  tw_pounce    K -> K             230 / 600   hop off the lunge, blades raised, chop both down together
  tw_hook      J J -> K           140 / 440   a wide low stance, both blades hooked in from outside at knee height
  tw_bwheel    Demon K -> J       120 / 440   a somersault: both blades wheel overhead and down in front
"""

DEMON = ((255, 196, 186), (226, 52, 64), (120, 16, 34))          # demon mode crimson (as player_v13_b)
SILVER = ((250, 252, 255), (196, 206, 228), (120, 130, 160))     # the perfect-dodge silver

TIMING = {   # tag -> (wind-up ms, total ms, active (i0, i1))
    "tw_barrage": (110, 470, (2, 6)),
    "tw_skyward": (130, 460, (2, 3)),
    "tw_crossfall": (130, 480, (2, 3)),
    "tw_dfin": (150, 640, (2, 5)),
    "tw_reversal": (110, 420, (2, 3)),
    "tw_spiral": (120, 480, (2, 5)),
    "tw_pounce": (230, 600, (3, 4)),
    "tw_hook": (140, 440, (2, 3)),
    "tw_bwheel": (120, 440, (2, 4)),
}


def register(G):
    mseq, sw, settled = G.mseq, G.sw, G.settled
    OX, FF = G.OX, G.FF
    AIR, AIRB, TUCK = G.AIR, G.AIRB, G.TUCK
    DIVE, cape_dive, cape_trail = G.DIVE, G.cape_dive, G.cape_trail

    def ow(h, a, front=False, slen=18):
        return (h, a, slen, front) if front or slen != 18 else (h, a)

    # ------------------------------------------------------------------ J J (pause) J: fang barrage
    def tw_barrage():  # sink and draw both blades back to the hip, then five stabs, main / off / main / off, the last both at once
        ST = dict(sq=0.3, w=0.35)
        return mseq([(dict(dx=-2, dy=2, head_dx=-1, hand=(28, 27), ang=172, offw=ow((27, 28), 176), footB=(OX + 5, 39), flow=0.3), 60),
                     (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=-8, offw=ow((26, 27), -4), footB=(OX + 5, 39), flow=0.4,
                           flutter=1, fx=[("glint", "tip")]), 50),
                     # 1: main, chest height
                     (dict(dx=1, dy=1, hand=(41, 24), ang=-4, offw=ow((27, 27), 170), footF=(FF[0] + 2, 39), flow=1.0, flutter=2,
                           fx=[("streak", 12)]), 60),
                     # 2: off blade, a little lower, the main drawn back
                     (dict(dx=2, dy=1, hand=(30, 26), ang=174, offw=ow((42, 27), 4, True), offsw=0.35, footF=(FF[0] + 3, 39), flow=1.2,
                           flutter=3), 60),
                     # 3: main, high, rising onto the toes
                     (dict(dx=3, dy=0, hand=(42, 20), ang=-14, offw=ow((29, 28), 168), footB=(OX + 9, 38), footF=(FF[0] + 3, 39),
                           flow=1.2, flutter=4, fx=[("streak", 13)]), 60),
                     # 4: off blade, low, sinking again
                     (dict(dx=3, dy=2, hand=(31, 27), ang=176, offw=ow((43, 29), 10, True), offsw=0.35, footF=(FF[0] + 4, 39), flow=1.3,
                           flutter=5), 60),
                     # 5: both together, a lunge with the whole body behind it
                     (dict(dx=5, dy=2, head_dx=1, hand=(44, 24), ang=-2, offw=ow((42, 27), 6, True), offsw=0.4, footB=(OX + 9, 39),
                           footF=(FF[0] + 6, 39), flow=1.5, flutter=6, fx=[("streak", 15), ("flare", (50, 24), 4)]), 60),
                     (dict(dx=2, dy=1, hand=(37, 26), ang=-20, offw=ow((32, 27), 150), footF=(FF[0] + 3, 39), flow=0.6, flutter=7), 60)])

    # ------------------------------------------------------------------ J J J K: skyward fangs (springs you up)
    def tw_skyward():  # crouch with both blades low behind, then rip them up one after the other, carried off the floor
        fr = mseq([(dict(dx=-1, dy=3, head_dy=1, hand=(30, 31), ang=160, offw=ow((28, 31), 168), footB=(OX + 5, 39),
                          footF=(FF[0] + 1, 39), flow=0.3), 70),
                   (dict(dx=-2, dy=4, head_dx=-1, head_dy=1, hand=(29, 32), ang=150, offw=ow((27, 32), 160), footB=(OX + 4, 39),
                         footF=(FF[0] + 1, 39), flow=0.5, flutter=1, fx=[("glint", "tip"), ("dust", 44, 2)]), 60),
                   # hit 1: the main blade up through the front, legs uncoiling
                   (dict(dx=1, dy=0, hand=(39, 18), ang=-70, offw=ow((30, 30), 160), footB=(OX + 9, 37), footF=(FF[0] + 1, 38),
                         flow=1.2, flutter=2, fx=[sw(w=0.55), ("dust", 44, 3)]), 45),
                   # hit 2: the off blade follows it up, off the floor now
                   (dict(dx=1, dy=-3, hand=(36, 13), ang=-95, offw=ow((39, 15), -62, True), offsw=0.55, flow=1.5, flutter=3,
                         fx=[sw(w=0.45)], **AIR), 45),
                   (dict(dx=0, dy=-4, hand=(35, 12), ang=-100, offw=ow((38, 14), -70, True), flow=1.3, flutter=4,
                         fx=[("vspeed", (24, 30), 2, 7)], **TUCK), 100),
                   (dict(dx=0, dy=-3, hand=(35, 20), ang=-50, offw=ow((32, 22), -20), flow=0.8, flutter=5, **AIR), 140)])
        return cape_trail(fr, [3, 4], dy=-1, ang=200)

    # ------------------------------------------------------------------ air J J: crossfall
    def tw_crossfall():  # in the air, both blades raised crossed behind the head; they open in an X as you dive to the floor
        fr = mseq([(dict(dx=-1, hand=(30, 14), ang=-140, offw=ow((29, 15), -120), flow=0.7), 70),
                   (dict(dx=-1, dy=-1, hand=(29, 12), ang=-160, offw=ow((28, 13), -150), flow=0.9, flutter=1,
                         fx=[("glint", (30, 4))]), 60),
                   # hit 1: the X opens forward-down, the body tipping into the dive
                   (dict(dx=2, dy=0, head_dx=1, hand=(40, 26), ang=35, offw=ow((40, 20), -30, True), offsw=0.55, flow=1.5,
                         flutter=2, fx=[sw(w=0.55)] + DIVE(8)), 60),
                   # hit 2: the blades sweep through to point down-forward
                   (dict(dx=3, dy=1, head_dx=1, hand=(41, 31), ang=62, offw=ow((42, 27), 40, True), offsw=0.5, flow=1.6, flutter=3,
                         fx=[sw(w=0.5)] + DIVE(10, 1)), 60),
                   # landing: knees taken low, blades spread wide, a puff of dust
                   (dict(dx=3, dy=4, head_dy=1, hand=(42, 32), ang=20, offw=ow((40, 31), 170), footB=(OX + 5, 39),
                         footF=(FF[0] + 4, 39), flow=1.0, flutter=4, air=False, fx=[("dust", 46, 4)]), 100),
                   (dict(dx=1, dy=1, hand=(36, 27), ang=-20, offw=ow((31, 27), 150), footB=(OX + 8, 39), footF=(FF[0] + 2, 39),
                         flow=0.4, flutter=5, air=False), 130)],
                  AIRB)
        return cape_dive(fr, [2, 3], dy=-2)

    # ------------------------------------------------------------------ Demon J x6 -> K: rending cyclone
    def tw_dfin():  # coil, two crimson spins, a leap with both blades raised, then a crossed cut down that bursts
        AR = dict(sq=0.42, w=0.6, pal=DEMON)
        return mseq([(dict(dx=-1, dy=2, hand=(29, 26), ang=174, offw=ow((28, 28), 178), footB=(OX + 6, 39), flow=0.3,
                           aura=1, aura_pal=DEMON), 80),
                     (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 27), ang=178, offw=ow((27, 28), 172), footB=(OX + 5, 39), flow=0.4,
                           flutter=1, aura=1, aura_pal=DEMON, fx=[("glint", "tip"), ("flare", (27, 22), 4, DEMON)]), 70),
                     # spin 1
                     (dict(dx=1, dy=1, hand=(37, 26), ang=-5, offw=ow((35, 27), 5, True), footF=(FF[0] + 2, 39), flow=1.3, flutter=2,
                           fx=[("arc", (29, 27), 172, -5, AR)]), 85),
                     # spin 2 (the turn seen from behind)
                     (dict(dx=2, dy=1, hand=(37, 26), ang=8, offw=ow((35, 27), 12, True), flow=1.5, flutter=3, mirror=True,
                           fx=[("arc", (29, 27), 185, 5, AR)]), 85),
                     # the leap: both blades thrown up, crossing overhead
                     (dict(dx=3, dy=-3, hand=(36, 12), ang=-80, offw=ow((38, 13), -100, True), offsw=0.5, footB=(OX + 10, 35),
                           footF=(OX + 20, 36), flow=1.4, flutter=4, aura=1, aura_pal=DEMON, fx=[sw(w=0.5)], fx_pal=DEMON), 85),
                     # the crossed cut down: an X that bursts crimson at the floor
                     (dict(dx=5, dy=3, head_dy=1, hand=(42, 30), ang=58, offw=ow((42, 18), -58, True), offsw=0.6, footB=(OX + 9, 39),
                           footF=(OX + 27, 39), flow=1.8, flutter=5,
                           fx=[sw(w=0.6, a0=-70), ("flare", (47, 24), 9, DEMON), ("dust", 50, 4)], fx_pal=DEMON), 90),
                     (dict(dx=5, dy=3, head_dy=1, hand=(41, 31), ang=64, offw=ow((41, 17), -64, True), footB=(OX + 9, 39),
                           footF=(OX + 27, 39), flow=0.9, flutter=6), 100),
                     (dict(dx=2, dy=1, hand=(36, 27), ang=-20, offw=ow((31, 27), 150), footF=(FF[0] + 2, 39), flow=0.4, flutter=7), 45)])

    # ------------------------------------------------------------------ L -> K: reversal cut
    def tw_reversal():  # out of the roll on one knee, the blades trailing; pivot, then main and off blade rip upward in turn
        return mseq([(dict(dx=-2, dy=5, head_dy=1, hand=(28, 33), ang=172, offw=ow((26, 32), 176), footB=(OX + 4, 39),
                           footF=(FF[0] + 2, 39), flow=1.2), 60),
                     (dict(dx=-1, dy=4, head_dy=1, hand=(31, 33), ang=150, offw=ow((28, 33), 165), footB=(OX + 5, 39),
                           footF=(FF[0] + 2, 39), flow=0.9, flutter=1, fx=[("glint", "tip")]), 50),
                     # hit 1: the main blade from the floor up through the front
                     (dict(dx=2, dy=1, hand=(41, 20), ang=-58, offw=ow((30, 31), 160), footF=(FF[0] + 3, 39), flow=1.3, flutter=2,
                           fx=[sw(w=0.55)]), 45),
                     # hit 2: the off blade crosses it, higher
                     (dict(dx=3, dy=-1, hand=(38, 15), ang=-80, offw=ow((41, 17), -50, True), offsw=0.55, footB=(OX + 9, 38),
                           footF=(FF[0] + 3, 39), flow=1.4, flutter=3, fx=[("flare", (46, 12), 4, SILVER)]), 45),
                     (dict(dx=3, dy=-1, hand=(37, 13), ang=-88, offw=ow((40, 14), -64, True), footB=(OX + 9, 38),
                           footF=(FF[0] + 3, 39), flow=1.0, flutter=4), 90),
                     (dict(dx=2, hand=(36, 20), ang=-60, offw=ow((33, 22), -40), footF=(FF[0] + 2, 39), flow=0.6, flutter=5), 70),
                     (dict(dx=1, hand=(35, 27), ang=-25, offw=ow((31, 27), 150), flow=0.3, flutter=6), 60)])

    # ------------------------------------------------------------------ v14c: K -> J spiral pursuit
    def tw_spiral():  # rise out of the lunge's crouch, blades spread flat; two full turns drifting forward, low then high
        AR = dict(sq=0.38, w=0.55)
        AH = dict(sq=0.3, w=0.5)
        return mseq([(dict(dx=1, dy=2, hand=(38, 29), ang=40, offw=ow((37, 22), -40, True), footB=(OX + 7, 39), footF=(FF[0] + 2, 39),
                           flow=0.6), 60),
                     (dict(dx=-1, dy=1, head_dx=-1, hand=(28, 26), ang=176, offw=ow((27, 27), 172), footB=(OX + 6, 39), flow=0.4,
                           flutter=1, fx=[("glint", "tip")]), 60),
                     # turn 1: low
                     (dict(dx=1, dy=2, hand=(38, 28), ang=4, offw=ow((36, 29), 10, True), footF=(FF[0] + 2, 39), flow=1.3, flutter=2,
                           fx=[("arc", (30, 29), 176, 4, AR), ("dust", 46, 2)]), 75),
                     (dict(dx=2, dy=2, hand=(38, 28), ang=10, offw=ow((36, 29), 14, True), footF=(FF[0] + 3, 39), flow=1.5, flutter=3,
                           mirror=True, fx=[("arc", (30, 29), 186, 8, AR)]), 75),
                     # turn 2: higher, rising onto the toes
                     (dict(dx=3, dy=0, hand=(39, 22), ang=-12, offw=ow((37, 24), -4, True), footB=(OX + 9, 38), footF=(FF[0] + 4, 39),
                           flow=1.5, flutter=4, fx=[("arc", (30, 23), 170, -12, AH)]), 75),
                     (dict(dx=4, dy=0, hand=(39, 22), ang=-6, offw=ow((37, 24), 2, True), footB=(OX + 9, 38), footF=(FF[0] + 5, 39),
                           flow=1.6, flutter=5, mirror=True, fx=[("arc", (30, 23), 182, -2, AH), ("flare", (46, 22), 4)]), 75),
                     (dict(dx=2, dy=1, hand=(36, 26), ang=-25, offw=ow((32, 27), 150), footF=(FF[0] + 3, 39), flow=0.6, flutter=6), 60)])

    # ------------------------------------------------------------------ v14c: K -> K fang pounce
    def tw_pounce():  # sink out of the lunge, spring up with both blades thrown back over the head, chop them down side by side
        fr = mseq([(dict(dx=1, dy=3, head_dy=1, hand=(36, 30), ang=30, offw=ow((35, 29), 40, True), footB=(OX + 6, 39),
                          footF=(FF[0] + 2, 39), flow=0.5), 80),
                   (dict(dx=1, dy=-2, hand=(31, 14), ang=-120, offw=ow((30, 15), -110), flow=1.1, flutter=1, **AIR), 80),
                   (dict(dx=1, dy=-3, hand=(28, 11), ang=-165, offw=ow((27, 12), -158), flow=1.2, flutter=2,
                         fx=[("glint", (27, 4))], **TUCK), 70),
                   # the chop: both blades down together, parallel
                   (dict(dx=4, dy=1, hand=(41, 27), ang=40, offw=ow((40, 26), 46, True), offsw=0.55, footB=(OX + 8, 38),
                         footF=(FF[0] + 4, 39), flow=1.6, flutter=3, fx=[sw(w=0.6), ("flare", (47, 31), 5)]), 50),
                   (dict(dx=4, dy=4, head_dy=1, hand=(41, 33), ang=70, offw=ow((40, 33), 74, True), footB=(OX + 6, 39),
                         footF=(FF[0] + 5, 39), flow=1.0, flutter=4, fx=[("dust", 48, 5)]), 120),
                   (dict(dx=4, dy=4, head_dy=1, hand=(41, 33), ang=72, offw=ow((40, 33), 76, True), footB=(OX + 6, 39),
                         footF=(FF[0] + 5, 39), flow=0.6, flutter=5), 110),
                   (dict(dx=2, dy=1, hand=(36, 27), ang=-20, offw=ow((32, 27), 150), footB=(OX + 8, 39), footF=(FF[0] + 2, 39),
                         flow=0.4, flutter=6), 90)])
        return cape_trail(fr, [1, 2], dy=-1, ang=200)

    # ------------------------------------------------------------------ v14c: J J -> K hooking cross
    def tw_hook():  # step wide and low with the blades flung out to either side, then hook them in at the knees, crossing
        return mseq([(dict(dx=0, dy=3, hand=(42, 22), ang=-60, offw=ow((22, 22), -125), footB=(OX + 4, 39), footF=(FF[0] + 3, 39),
                           flow=0.6), 70),
                     (dict(dx=-1, dy=4, head_dy=1, hand=(44, 25), ang=-40, offw=ow((20, 25), -150), footB=(OX + 3, 39),
                           footF=(FF[0] + 4, 39), flow=0.5, flutter=1, fx=[("glint", "tip")]), 70),
                     # main hooks in from the front, low
                     (dict(dx=1, dy=4, head_dy=1, hand=(38, 32), ang=150, offw=ow((22, 27), -160), footB=(OX + 3, 39),
                           footF=(FF[0] + 4, 39), flow=1.2, flutter=2, fx=[sw(w=0.5), ("dust", 44, 2)]), 80),
                     # off hooks in from behind and across: the blades cross at the knees
                     (dict(dx=2, dy=4, head_dy=1, hand=(37, 33), ang=160, offw=ow((40, 32), 20, True), offsw=0.55, footB=(OX + 4, 39),
                           footF=(FF[0] + 4, 39), flow=1.4, flutter=3, fx=[("flare", (40, 33), 4)]), 80),
                     (dict(dx=2, dy=4, head_dy=1, hand=(36, 33), ang=165, offw=ow((39, 33), 15, True), footB=(OX + 4, 39),
                           footF=(FF[0] + 4, 39), flow=0.8, flutter=4), 80),
                     (dict(dx=1, dy=1, hand=(35, 27), ang=-20, offw=ow((31, 27), 150), footF=(FF[0] + 2, 39), flow=0.4, flutter=5), 60)])

    # ------------------------------------------------------------------ v14c: Demon K -> J bloodwheel
    def tw_bwheel():  # spring off the flurry, tuck, and wheel both blades over the head and down in front -- main, off, both
        fr = mseq([(dict(dx=0, dy=3, hand=(32, 31), ang=150, offw=ow((30, 31), 160), footB=(OX + 6, 39), footF=(FF[0] + 2, 39),
                          flow=0.6, aura=1, aura_pal=DEMON), 60),
                   (dict(dx=0, dy=-2, hand=(26, 22), ang=-170, offw=ow((25, 24), 170), flow=1.2, flutter=1, aura=1, aura_pal=DEMON,
                         **TUCK), 60),
                   # the main blade over the top and down in front
                   (dict(dx=2, dy=-4, head_dy=1, hand=(40, 26), ang=60, offw=ow((27, 15), -120), flow=1.5, flutter=2,
                         fx=[sw(w=0.55, a0=-150)], fx_pal=DEMON, **TUCK), 90),
                   # the off blade follows it round
                   (dict(dx=3, dy=-3, head_dy=1, hand=(36, 30), ang=100, offw=ow((41, 25), 55, True), offsw=0.55, flow=1.6, flutter=3,
                         fx_pal=DEMON, **TUCK), 90),
                   # both come down together as you land
                   (dict(dx=4, dy=2, hand=(42, 28), ang=45, offw=ow((41, 27), 50, True), footB=(OX + 6, 39), footF=(FF[0] + 4, 39),
                         flow=1.4, flutter=4, fx=[sw(w=0.55), ("flare", (47, 30), 6, DEMON), ("dust", 48, 3)], fx_pal=DEMON), 90),
                   (dict(dx=2, dy=1, hand=(36, 27), ang=-20, offw=ow((32, 27), 150), footF=(FF[0] + 2, 39), flow=0.5, flutter=5), 50)])
        return cape_trail(fr, [2, 3], dy=-2, ang=210)

    moves = [("tw_barrage", tw_barrage), ("tw_skyward", tw_skyward), ("tw_crossfall", tw_crossfall), ("tw_dfin", tw_dfin),
             ("tw_reversal", tw_reversal), ("tw_spiral", tw_spiral), ("tw_pounce", tw_pounce), ("tw_hook", tw_hook),
             ("tw_bwheel", tw_bwheel)]
    SETTLE = {"tw_barrage", "tw_dfin", "tw_reversal", "tw_spiral", "tw_pounce", "tw_hook", "tw_bwheel"}   # ground attacks that end in the neutral stance ease back to idle
    moves = [(n, settled(f) if n in SETTLE else f) for n, f in moves]
    OPTS = {
        "tw_barrage": dict(extras=True, x0=0, hits=[2, 3, 4, 5, 6]),
        "tw_skyward": dict(extras=True, x0=-2, hits=[2, 3], up=True),
        "tw_crossfall": dict(extras=True, hits=[2, 3], hit=[-2, -32, 30, 4], fxat=(18, -12)),
        "tw_dfin": dict(extras=True, both=True, hits=[2, 3, 4, 5], fxat=(16, -14)),
        "tw_reversal": dict(extras=True, x0=0, hits=[2, 3]),
        "tw_spiral": dict(extras=True, both=True, hits=[2, 3, 4, 5], fxat=(14, -14)),
        "tw_pounce": dict(extras=True, x0=0),
        "tw_hook": dict(extras=True, x0=-2, hits=[2, 3], fxat=(20, -8)),
        "tw_bwheel": dict(extras=True, x0=0, hits=[2, 3, 4]),
    }
    out = []
    for n, f in moves:
        o = dict(OPTS.get(n, {}))
        o["active"] = TIMING[n][2]
        out.append((n, f, o))
    return out
