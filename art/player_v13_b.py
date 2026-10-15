"""v13 weapon revamp (docs/WEAPON_REVAMP_CONTRACT.md): new player tags, agent WA2.
register(G) receives the gen_player module (all its helpers: mseq, sw, poses, SH, ...) and returns [(tag, fn)].
Tags registered here are appended to gen_player's ANIMS after every existing tag, so no existing frame index moves.

WA2 owns Dual Blades (tw_), Spear (sp_), Staff (st_) and Whip (wh_). Every tag's total time and wind-up (the ms before
its first active frame) follow docs/WEAPON_REVAMP.md Part A; TIMING below is the single table the self-test checks.
The metadata each attack needs (active window, hit-box rules) is registered here too, into gen_player's own tables
(ACTIVE / HIT_EXTRAS / HIT_X0 / HIT_OVERRIDE / FXAT_OVERRIDE), so meta_for picks it up with no edit to gen_player.py.
"""
import math

SILVER = ((250, 252, 255), (196, 206, 228), (120, 130, 160))     # perfect dodge: the afterimage / counter glints
DEMON = ((255, 196, 186), (226, 52, 64), (120, 16, 34))          # demon mode: crimson (the twinfangs' own smear family)

# tag -> (wind-up ms | None, total ms, active (i0, i1) | None, kind of tag)   kind: atk / loop / move / stance
TIMING = {
    # Dual Blades (A7)
    "tw_demon_on": (None, 200, None, "move"),
    "tw_d5": (100, 280, (2, 3), "atk"),
    "tw_d6": (100, 280, (2, 4), "atk"),
    "tw_dflurry": (150, 800, (2, 7), "atk"),
    "tw_ddash": (None, 120, None, "move"),
    "tw_dance": (120, 1400, (2, 11), "atk"),
    "tw_dance2": (120, 1680, (2, 14), "atk"),
    "tw_dashslash": (100, 320, (2, 3), "atk"),
    "tw_counter": (80, 300, (1, 3), "atk"),
    "tw_pdodge": (None, 180, None, "move"),            # extra (optional): the perfect-dodge afterimage beat
    # Spear (A8)
    "sp_guard": (None, 600, None, "loop"),
    "sp_guard_walk": (None, 660, None, "loop"),
    "sp_gpoke": (140, 380, (2, 3), "atk"),
    "sp_counter": (160, 520, (2, 3), "atk"),
    "sp_hop": (None, 260, None, "move"),
    "sp_charge_wind": (None, 400, None, "move"),       # extra (optional): the 400 ms charge-dash wind-up
    "sp_charge_run": (0, 480, (0, 7), "loop"),
    "sp_finish": (120, 480, (2, 3), "atk"),
    "sp_pguard": (None, 1000, None, "stance"),
    "sp_ccounter": (360, 800, (3, 4), "atk"),
    # Staff (A9)
    "st_vault": (None, 350, None, "move"),
    "st_aspin": (180, 460, (2, 5), "atk"),
    "st_aspin2": (120, 540, (2, 6), "atk"),
    "st_divekick": (100, 300, (2, 3), "atk"),
    "st_lowsweep": (140, 380, (2, 3), "atk"),
    "st_twirl_up": (140, 340, (2, 4), "atk"),
    "st_gale": (220, 700, (2, 6), "atk"),
    # Whip (A10)
    "wh_overhead_hold": (None, 480, None, "loop"),
    "wh_overhead": (300, 600, (3, 4), "atk"),
    "wh_thunder": (300, 700, (3, 4), "atk"),
    "wh_grapple": (None, 300, None, "move"),
    "wh_grapple_pull": (None, 300, None, "move"),
    "wh_grapple_zip": (None, 120, None, "loop"),       # extra (optional): yanked along the chain to a ring / big foe
    "wh_retreat": (160, 420, (2, 3), "atk"),
    "wh_snap": (80, 320, (2, 3), "atk"),
    "wh_slam": (250, 600, (3, 4), "atk"),
    "wh_double": (220, 550, (2, 3), "atk"),
    "wh_thousand": (0, 360, (0, 5), "loop"),
}


def register(G):
    mseq, sw, settled = G.mseq, G.sw, G.settled
    OX, FF = G.OX, G.FF
    TUCK, AIR, AIRB, LEGS_BACK = G.TUCK, G.AIR, G.AIRB, G.LEGS_BACK
    DIVE, cape_dive, cape_trail = G.DIVE, G.cape_dive, G.cape_trail
    GS, GT = G.GRIP_SPEAR, G.GRIP_STAFF
    P_WIND, P_STORM, P_GOLD, P_BLOOD = G.P_WIND, G.P_STORM, G.P_GOLD, G.P_BLOOD

    # ============================================================ Dual Blades: Demon Mode, the dance, the perfect dodge
    LOW = ((30, 27), 150)            # off blade carried low behind (the twin idle)

    def ow(h, a, front=False, slen=18):
        return (h, a, slen, front) if front or slen != 18 else (h, a)

    def tw_demon_on():  # blades crossed low, scraped apart with a crimson spark, then flung wide into the crouched demon stance
        return mseq([(dict(dy=2, hand=(34, 29), ang=118, offw=ow((32, 29), 62, True), footB=(OX + 6, 39), flow=0.3), 40),
                     (dict(dy=1, hand=(37, 25), ang=-18, offw=ow((26, 26), -160), footB=(OX + 6, 39), flow=0.6, flutter=1,
                           aura=1, aura_pal=DEMON, fx=[("flare", "tip", 4, DEMON)]), 50),
                     (dict(dy=3, head_dy=1, hand=(41, 24), ang=-10, offw=ow((22, 23), -168), footB=(OX + 3, 39), footF=(FF[0] + 3, 39),
                           flow=1.3, flutter=2, aura=1, aura_pal=DEMON, fx=[("flare", "tip", 6, DEMON)]), 50),
                     (dict(dy=3, head_dy=1, hand=(40, 25), ang=-6, offw=ow((23, 24), -172), footB=(OX + 3, 39), footF=(FF[0] + 3, 39),
                           flow=0.8, flutter=3, aura=1, aura_pal=DEMON), 60)])

    def tw_d5():  # demon chain 5: a downward cut, then the off blade backhands through (2 hits)
        return mseq([(dict(dx=-1, dy=1, hand=(30, 19), ang=-135, offw=ow((28, 28), 165), footB=(OX + 7, 39), flow=0.3), 55),
                     (dict(dx=-1, dy=1, hand=(30, 17), ang=-150, offw=ow((29, 27), 172), footB=(OX + 6, 39), flow=0.3, flutter=1), 45),
                     (dict(dx=2, hand=(39, 25), ang=8, offw=ow((29, 28), 162), footF=(FF[0] + 2, 39), flow=1.0, flutter=2,
                           fx=[sw(w=0.5)]), 40),
                     (dict(dx=2, hand=(36, 29), ang=52, offw=ow((39, 24), -12, True), offsw=0.5, footF=(FF[0] + 2, 39), flow=1.1,
                           flutter=3), 40),
                     (dict(dx=1, hand=(36, 27), ang=-15, offw=ow((32, 27), -25), flow=0.4, flutter=4), 100)])

    def tw_d6():  # demon chain 6: coil low, a full spinning cut, then the off blade rips upward (3 hits)
        AR = dict(sq=0.42, w=0.55)
        return mseq([(dict(dx=-1, dy=2, hand=(29, 26), ang=174, offw=ow((28, 27), 178), footB=(OX + 6, 39), flow=0.3), 50),
                     (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 26), ang=176, offw=ow((28, 28), 172), footB=(OX + 5, 39), flow=0.2,
                           flutter=1, fx=[("glint", "tip")]), 50),
                     (dict(dx=1, dy=1, hand=(37, 26), ang=-5, offw=ow((35, 27), 5, True), footF=(FF[0] + 2, 39), flow=1.1, flutter=2,
                           fx=[("arc", (29, 27), 172, -5, AR)]), 35),
                     (dict(dx=1, dy=1, hand=(37, 26), ang=5, offw=ow((35, 27), 10, True), flow=1.4, flutter=3, mirror=True,
                           fx=[("arc", (29, 27), 185, 5, AR)]), 35),
                     (dict(dx=2, hand=(37, 22), ang=-30, offw=ow((38, 19), -72, True), offsw=0.5, footF=(FF[0] + 3, 39), flow=1.2,
                           flutter=4, fx=[sw(w=0.4)]), 35),
                     (dict(dx=1, hand=(35, 24), ang=-40, offw=ow((33, 22), -80), flow=0.5, flutter=5), 75)])

    def flurry_hits(dx0=2):
        """Six alternating crimson cuts at different heights (the demon flurry body; the dance reuses the shapes)."""
        return [
            (dict(dx=dx0, hand=(40, 22), ang=-12, offw=ow((30, 29), 152), footF=(FF[0] + 2, 39), flow=1.1, fx=[sw(w=0.5)]), 75),
            (dict(dx=dx0, dy=1, hand=(32, 27), ang=150, offw=ow((40, 25), -18, True), offsw=0.5, footF=(FF[0] + 2, 39), flow=1.3,
                  flutter=1), 75),
            (dict(dx=dx0 + 1, dy=1, hand=(41, 28), ang=14, offw=ow((31, 22), -130), footF=(FF[0] + 3, 39), flow=1.2, flutter=2,
                  fx=[sw(w=0.5)]), 75),
            (dict(dx=dx0 + 1, hand=(33, 19), ang=-125, offw=ow((40, 27), 38, True), offsw=0.5, footF=(FF[0] + 3, 39), flow=1.3,
                  flutter=3), 75),
            (dict(dx=dx0 + 1, dy=-1, hand=(39, 18), ang=-62, offw=ow((31, 28), 162), footB=(OX + 8, 38), footF=(FF[0] + 3, 39),
                  flow=1.2, flutter=4, fx=[sw(w=0.5)]), 75),
            (dict(dx=dx0 + 2, dy=1, hand=(34, 26), ang=170, offw=ow((42, 24), -2, True), offsw=0.4, footB=(OX + 8, 39),
                  footF=(FF[0] + 4, 39), flow=1.4, flutter=5), 75)]

    def tw_dflurry():  # demon K: crouch with the blades crossed low, then six alternating cuts advancing, a held follow-through
        return mseq([(dict(dx=-1, dy=2, hand=(30, 29), ang=166, offw=ow((28, 30), 172), footB=(OX + 5, 39),
                           footF=(FF[0] + 1, 39), flow=0.3), 70),
                     (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 29), ang=172, offw=ow((27, 30), 176), footB=(OX + 4, 39),
                           footF=(FF[0] + 1, 39), flow=0.4, flutter=1, aura=1, aura_pal=DEMON, fx=[("glint", "tip")]), 80)]
                    + flurry_hits()
                    + [(dict(dx=4, dy=2, hand=(40, 28), ang=30, offw=ow((40, 20), -40, True), footB=(OX + 8, 39), footF=(FF[0] + 4, 39),
                             flow=0.9, flutter=6), 100),
                       (dict(dx=1, hand=(36, 27), ang=-20, offw=ow((31, 27), 150), flow=0.4, flutter=7), 100)])

    def tw_ddash():  # demon dash: a flat crimson streak, blades trailing low behind (not an attack)
        streak = dict(dy=3, hand=(30, 30), ang=168, offw=ow((27, 31), 172), footB=(OX + 3, 39), footF=(OX + 23, 39))
        fr = mseq([(dict(dx=2, flow=1.6, fx=[("speed", (24, 18), 4, 12, DEMON)], **streak), 30),
                   (dict(dx=3, flow=1.9, flutter=1, fx=[("speed", (25, 17), 5, 16, DEMON), ("ghost", -9, 1, DEMON)], **streak), 50),
                   (dict(dx=2, dy=2, hand=(33, 28), ang=-20, offw=ow((29, 29), 160), footB=(OX + 5, 39), footF=(OX + 21, 39),
                         flow=1.0, flutter=2), 40)])
        return cape_trail(fr, [0, 1], dy=1)

    def tw_pdodge():  # perfect dodge (extra): you slip aside; a silver afterimage stays where the blow fell, then fades
        slip = dict(dx=-3, dy=3, head_dx=-1, hand=(32, 28), ang=-20, offw=ow((28, 28), 165), footB=(OX + 4, 39), footF=(OX + 18, 39))
        return mseq([(dict(flow=1.0, fx=[("ghost", 8, 3, SILVER), ("glint", (38, 17))], **slip), 60),
                     (dict(flow=0.7, flutter=1, fx=[("ghost", 9, 2, SILVER)], **slip), 60),
                     (dict(dx=-2, dy=2, hand=(33, 27), ang=-25, offw=ow((29, 27), 155), footB=(OX + 5, 39), footF=(OX + 19, 39),
                           flow=0.4, flutter=2, fx=[("ghost", 10, 1, SILVER)]), 60)])

    def tw_dashslash():  # out of the roll: spring low and cut straight through, the off blade following
        return mseq([(dict(dx=-1, dy=3, hand=(30, 29), ang=170, offw=ow((28, 30), 172), footB=(OX + 5, 39), footF=(FF[0] + 1, 39),
                           flow=0.6), 50),
                     (dict(dx=2, dy=2, hand=(33, 28), ang=176, offw=ow((30, 29), 168), footB=(OX + 5, 39), footF=(OX + 23, 39),
                           flow=1.5, flutter=1, fx=[("speed", (22, 18), 4, 12)]), 50),
                     (dict(dx=4, dy=2, hand=(42, 25), ang=-5, offw=ow((30, 29), 165), footB=(OX + 8, 39), footF=(OX + 26, 39),
                           flow=1.7, flutter=2, fx=[("arc", (31, 26), 170, -5, dict(sq=0.45, w=0.55))]), 45),
                     (dict(dx=4, dy=2, hand=(40, 20), ang=-45, offw=ow((41, 26), 5, True), offsw=0.5, footB=(OX + 8, 39),
                           footF=(OX + 26, 39), flow=1.4, flutter=3, fx=[sw(w=0.45)]), 45),
                     (dict(dx=3, dy=2, hand=(39, 19), ang=-55, offw=ow((40, 27), 12, True), footB=(OX + 8, 39), footF=(OX + 25, 39),
                           flow=0.8, flutter=4), 70),
                     (dict(dx=1, dy=1, hand=(35, 26), ang=-30, offw=ow((31, 27), 150), footF=(OX + 21, 39), flow=0.4, flutter=5), 60)])

    def tw_counter():  # counter flurry: from a silver afterimage, three cuts at once -- main, off, then an X
        return mseq([(dict(dx=-1, dy=2, hand=(31, 26), ang=176, offw=ow((30, 27), 170), footB=(OX + 5, 39), flow=0.6,
                           fx=[("ghost", -7, 3, SILVER), ("glint", (38, 18))]), 80),
                     (dict(dx=3, dy=1, hand=(41, 24), ang=-6, offw=ow((31, 28), 160), footF=(FF[0] + 3, 39), flow=1.4, flutter=1,
                           fx=[sw(w=0.5), ("ghost", -10, 1, SILVER)]), 40),
                     (dict(dx=3, dy=1, hand=(34, 27), ang=160, offw=ow((41, 26), 22, True), offsw=0.5, footF=(FF[0] + 3, 39),
                           flow=1.4, flutter=2), 40),
                     (dict(dx=4, dy=2, hand=(41, 30), ang=58, offw=ow((41, 18), -58, True), offsw=0.5, footB=(OX + 9, 39),
                           footF=(FF[0] + 4, 39), flow=1.5, flutter=3, fx=[sw(w=0.5), ("flare", (46, 24), 6, SILVER)]), 40),
                     (dict(dx=2, dy=1, hand=(37, 27), ang=10, offw=ow((34, 26), -20), flow=0.6, flutter=4), 100)])

    def dance_hits():  # the eight Blade Dance cuts: forward, spin, rising pair, a hop-cut, spin, low, high, a crossing pair
        AR = dict(sq=0.42, w=0.55, pal=DEMON)
        return [
            (dict(dx=2, hand=(40, 22), ang=-12, offw=ow((30, 29), 152), footF=(FF[0] + 2, 39), flow=1.2, flutter=2,
                  fx=[sw(w=0.5)], fx_pal=DEMON), 95),
            (dict(dx=1, dy=1, hand=(37, 26), ang=-5, offw=ow((35, 27), 5, True), footF=(FF[0] + 2, 39), flow=1.4, flutter=3,
                  mirror=True, fx=[("ring", (29, 27), 13, 185, 5, AR)]), 95),
            (dict(dx=2, dy=-1, hand=(38, 17), ang=-70, offw=ow((37, 20), -55, True), offsw=0.5, footB=(OX + 8, 38),
                  footF=(FF[0] + 2, 39), flow=1.3, flutter=4, fx=[sw(w=0.5)], fx_pal=DEMON), 95),
            (dict(dx=3, dy=-2, hand=(41, 27), ang=40, offw=ow((39, 18), -50, True), offsw=0.5, footB=(OX + 10, 36),
                  footF=(OX + 20, 37), flow=1.6, flutter=5, fx=[sw(w=0.55)], fx_pal=DEMON), 95),
            (dict(dx=2, dy=1, hand=(37, 26), ang=-5, offw=ow((35, 27), 5, True), footF=(FF[0] + 2, 39), flow=1.4, flutter=6,
                  fx=[("ring", (29, 27), 13, 172, -5, AR)]), 95),
            (dict(dx=2, dy=3, hand=(41, 31), ang=12, offw=ow((32, 25), -140), footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=1.3,
                  flutter=7, fx=[sw(w=0.5), ("dust", 50, 2)], fx_pal=DEMON), 95),
            (dict(dx=2, hand=(33, 18), ang=-130, offw=ow((40, 20), -30, True), offsw=0.5, footF=(FF[0] + 2, 39), flow=1.3,
                  flutter=8), 95),
            (dict(dx=3, dy=1, hand=(41, 23), ang=-20, offw=ow((40, 28), 25, True), offsw=0.5, footF=(FF[0] + 3, 39), flow=1.5,
                  flutter=9, fx=[sw(w=0.5)], fx_pal=DEMON), 95)]

    def dance_open():
        return [(dict(dx=-1, dy=2, hand=(30, 29), ang=166, offw=ow((28, 30), 172), footB=(OX + 5, 39), footF=(FF[0] + 1, 39),
                      flow=0.3, aura=1, aura_pal=DEMON), 70),
                (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 29), ang=174, offw=ow((27, 30), 178), footB=(OX + 4, 39),
                      footF=(FF[0] + 1, 39), flow=0.6, flutter=1, aura=1, aura_pal=DEMON, fx=[("glint", "tip")]), 50)]

    def dance_finish(big=False):  # blades raised crossed overhead, then brought down in an X that bursts crimson
        burst = 10 if big else 8
        return [(dict(dx=1, dy=-2, hand=(33, 12), ang=-104, offw=ow((30, 13), -76, True), footB=(OX + 8, 38), footF=(OX + 18, 39),
                      flow=0.9, flutter=10, aura=1, aura_pal=DEMON, fx=[("flare", (32, 3), 5, DEMON)]), 130 if not big else 120),
                (dict(dx=4, dy=3, hand=(41, 30), ang=60, offw=ow((41, 17), -60, True), offsw=0.6, footB=(OX + 9, 39),
                      footF=(OX + 26, 39), flow=1.7, flutter=11,
                      fx=[sw(w=0.6, a0=-60), ("flare", (46, 23), burst, DEMON), ("dust", 50, 4)] + ([("rings", (46, 23), (8, 12))]
                                                                                                if big else []),
                      fx_pal=DEMON), 60)]

    def dance_tail(hold):
        return [(dict(dx=4, dy=3, head_dy=1, hand=(40, 31), ang=64, offw=ow((40, 16), -64, True), footB=(OX + 9, 39),
                      footF=(OX + 26, 39), flow=0.9, flutter=12), hold),
                (dict(dx=1, hand=(35, 27), ang=-25, offw=ow((30, 27), 150), flow=0.3, flutter=13), 150)]

    def tw_dance():  # Archdemon hold K: eight crimson cuts (spins, a hop-cut) then a crossed overhead X  (1.4 s)
        return mseq(dance_open() + dance_hits() + dance_finish() + dance_tail(180))

    def tw_dance2():  # Blade Dance II: the eight cuts, three more (spin, low, rising), and a bigger cross-cut finisher
        AR = dict(sq=0.42, w=0.6, pal=DEMON)
        extra = [(dict(dx=2, dy=1, hand=(37, 26), ang=5, offw=ow((35, 27), 10, True), footF=(FF[0] + 2, 39), flow=1.5, flutter=10,
                       mirror=True, fx=[("ring", (29, 27), 14, 185, 5, AR)]), 90),
                 (dict(dx=3, dy=3, hand=(42, 31), ang=8, offw=ow((40, 30), 20, True), offsw=0.5, footB=(OX + 5, 39),
                       footF=(FF[0] + 4, 39), flow=1.4, flutter=11, fx=[sw(w=0.5), ("dust", 52, 2)], fx_pal=DEMON), 90),
                 (dict(dx=3, dy=-1, hand=(38, 15), ang=-80, offw=ow((39, 17), -65, True), offsw=0.5, footB=(OX + 8, 38),
                       footF=(FF[0] + 3, 39), flow=1.4, flutter=12, fx=[sw(w=0.55)], fx_pal=DEMON), 90)]
        return mseq(dance_open() + dance_hits() + extra + dance_finish(big=True) + dance_tail(200))

    # ============================================================ Spear: the planted guard, the poke, the charge
    GD = dict(dx=-1, dy=3, hand=(36, 23), ang=-36, grip=7.5, footB=(OX + 5, 39), footF=(FF[0] + 2, 39))   # braced guard

    def guard(**k):
        return {**GD, **k}

    def sp_guard():  # held guard (loop): feet planted wide, the haft braced diagonally across the body, a slow breath
        return mseq([(guard(flow=0.3, flutter=0), 150),
                     (guard(flow=0.25, flutter=1), 150),
                     (guard(dy=4, hand=(36, 23), flow=0.2, flutter=2), 150),
                     (guard(dy=4, hand=(36, 23), flow=0.25, flutter=3), 150)], grip=GS)

    def sp_guard_walk():  # guard walk (loop): a slow shuffle that never breaks the brace; the lead foot slides, the back follows
        out = []
        for i in range(6):
            t = i / 6 * 2 * math.pi
            # a foot lifts while it moves forward (cos > 0) and is planted while it pushes back (v14b: was the other way)
            fF = (FF[0] + 2 + 2.6 * math.sin(t), 39 - max(0.0, math.cos(t)) * 2.0)
            fB = (OX + 5 + 2.6 * math.sin(t + math.pi), 39 - max(0.0, math.cos(t + math.pi)) * 2.0)
            dy = 3 + (1 if i % 3 == 0 else 0)
            out.append((guard(dy=dy, footF=fF, footB=fB, flow=0.35 + 0.1 * (i % 2), flutter=i), 110))
        return mseq(out, grip=GS)

    def sp_gpoke():  # guard poke: a short thrust that leaves the brace intact, then back into the guard
        return mseq([(guard(dx=-2, hand=(34, 24), ang=-28, flow=0.3), 70),
                     (guard(dx=-2, hand=(31, 24), ang=-20, flow=0.25, flutter=1), 70),
                     (guard(dx=1, hand=(42, 23), ang=-14, footF=(FF[0] + 3, 39), flow=0.9, flutter=2, fx=[("streak", 18)]), 45),
                     (guard(dx=1, hand=(42, 23), ang=-15, footF=(FF[0] + 3, 39), flow=0.7, flutter=3, fx=[("streak", 8)]), 55),
                     (guard(hand=(38, 23), ang=-28, flow=0.4, flutter=4), 80),
                     (guard(flow=0.3, flutter=5), 60)], grip=GS)

    def sp_counter():  # counter-thrust: jolted by the block, coil, then an explosive lunge out of the guard
        return mseq([(guard(dx=-3, head_dx=-1, flow=0.8, fx=[("flare", (44, 15), 5)]), 60),
                     (dict(dx=-3, dy=3, head_dx=-1, hand=(26, 26), ang=-4, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.2,
                           flutter=1, fx=[("glint", "tip")]), 100),
                     (dict(dx=4, dy=2, hand=(42, 25), ang=-2, footB=(OX + 8, 39), footF=(OX + 26, 39), flow=1.6, flutter=2,
                           fx=[("streak", 24), ("flare", "tip", 5), ("speed", (20, 17), 4, 12)]), 50),
                     (dict(dx=4, dy=2, hand=(42, 25), ang=-1, footB=(OX + 8, 39), footF=(OX + 26, 39), flow=1.3, flutter=3,
                           fx=[("streak", 12)]), 60),
                     (dict(dx=4, dy=3, head_dy=1, hand=(41, 26), ang=0, footB=(OX + 9, 39), footF=(OX + 26, 39), flow=0.9,
                           flutter=4), 120),
                     (dict(dx=1, dy=1, hand=(34, 26), ang=-4, footF=(OX + 21, 39), flow=0.4, flutter=5), 130)], grip=GS)

    def sp_hop():  # hop (L): a short, tucked bound with the spear kept level, a soft landing
        return mseq([(dict(dy=3, hand=(32, 27), ang=-8, footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.4), 40),
                     (dict(dy=-3, hand=(33, 24), ang=-10, footB=(OX + 9, 35), footF=(OX + 18, 36), air=True, flow=1.1, flutter=1), 70),
                     (dict(dy=-2, hand=(33, 25), ang=-8, footB=(OX + 8, 36), footF=(OX + 18, 37), air=True, flow=0.9, flutter=2), 70),
                     (dict(dy=3, hand=(33, 28), ang=-6, footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.6, flutter=3,
                           fx=[("dust", 28, 2)]), 50),
                     (dict(dy=1, hand=(33, 27), ang=-8, flow=0.3, flutter=4), 30)], grip=GS)

    def sp_charge_wind():  # (extra) charge-dash wind-up: sink low, draw the spear back level, the tip glints
        return mseq([(dict(dx=-1, dy=2, hand=(30, 26), ang=-3, footB=(OX + 5, 39), flow=0.3), 120),
                     (dict(dx=-2, dy=4, head_dx=-1, hand=(27, 27), ang=-2, footB=(OX + 4, 39), footF=(FF[0] + 2, 39), flow=0.2,
                           flutter=1), 140),
                     (dict(dx=-2, dy=4, head_dx=-1, hand=(27, 27), ang=-2, footB=(OX + 4, 39), footF=(FF[0] + 2, 39), flow=0.3,
                           flutter=2, fx=[("glint", "tip")]), 140)], grip=GS)

    def sp_charge_run():  # charge dash (loop): a hard lean-forward sprint, the spear leveled at the hip like a lance
        out = []
        for i in range(8):
            t = i / 8 * 2 * math.pi
            dy = [2, 1, 0, 1, 2, 1, 0, 1][i]
            fF = (OX + 17 + 8 * math.cos(t), 39 - max(0, math.sin(t)) * 4)
            fB = (OX + 17 + 8 * math.cos(t + math.pi), 39 - max(0, math.sin(t + math.pi)) * 4)
            fx = [("streak", 14 + 3 * (i % 2)), ("speed", (22, 8 + dy), 2, 9 + 2 * (i % 2))]
            if i in (0, 4):
                fx.append(("dust", int(round(min(fF[0], fB[0]))) - 1, 2))
            out.append((dict(dx=3, dy=dy, head_dx=1, hand=(40, 26), ang=1, footF=fF, footB=fB, flow=1.2, flutter=i, fx=fx), 60))
        fr = mseq(out, grip=GS)
        for i, (cels, _) in enumerate(fr):   # the cape streams flat behind, its ripple travelling back once per loop
            dy = out[i][0]["dy"]
            cels["Cape"] = G.draw_streamer((OX + 11, G.OY + 11 + dy), 172, 21, 5, 7, -i * math.pi / 4, amp=1.1, k=0.55)
        return fr

    def sp_finish():  # finishing thrust: plant the lead foot out of the run and drive the whole body through the spear
        return mseq([(dict(dx=1, dy=2, hand=(31, 26), ang=-3, footB=(OX + 6, 39), footF=(OX + 22, 39), flow=1.3,
                           fx=[("dust", 37, 2)]), 60),
                     (dict(dx=-1, dy=3, head_dx=-1, hand=(27, 26), ang=-2, footB=(OX + 5, 39), footF=(OX + 21, 39), flow=0.9,
                           flutter=1, fx=[("glint", "tip")]), 60),
                     (dict(dx=5, dy=2, hand=(44, 25), ang=-1, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.8, flutter=2,
                           fx=[("streak", 26), ("flare", "tip", 6), ("speed", (22, 17), 5, 14)]), 50),
                     (dict(dx=5, dy=2, hand=(44, 25), ang=0, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.4, flutter=3,
                           fx=[("streak", 12)]), 60),
                     (dict(dx=4, dy=3, head_dy=1, hand=(42, 26), ang=1, footB=(OX + 9, 39), footF=(OX + 27, 39), flow=0.9, flutter=4,
                           fx=[("dust", 26, 3)]), 130),
                     (dict(dx=1, dy=1, hand=(34, 26), ang=-4, footF=(OX + 21, 39), flow=0.4, flutter=5), 120)], grip=GS)

    def sp_pguard():  # power guard: a stamp, then rooted -- the haft braced low like a pike, a gold sheen pulsing (1 s)
        PG = dict(dx=-1, dy=4, hand=(37, 25), ang=-28, grip=8.0, footB=(OX + 4, 39), footF=(FF[0] + 3, 39))
        return mseq([(dict(PG, dy=5, head_dy=1, flow=0.9, fx=[("dust", 20, 3), ("dust", 37, 3)]), 80),
                     (dict(PG, flow=0.4, flutter=1, aura=1, aura_pal=P_GOLD, fx=[("flare", (37, 25), 5, P_GOLD)]), 120),
                     (dict(PG, flow=0.3, flutter=2, aura=1, aura_pal=P_GOLD, fx=[("glint", "tip")]), 200),
                     (dict(PG, flow=0.25, flutter=3, aura=1, aura_pal=P_GOLD), 200),
                     (dict(PG, flow=0.3, flutter=4, aura=1, aura_pal=P_GOLD, fx=[("glint", "tip")]), 200),
                     (dict(PG, flow=0.25, flutter=5, aura=1, aura_pal=P_GOLD), 200)], grip=GS)

    def sp_ccounter():  # charged counter: jolted, coil deep while gold gathers on the tip, then a huge piercing lunge
        return mseq([(guard(dx=-3, head_dx=-1, flow=0.8, fx=[("flare", (44, 15), 5)]), 60),
                     (dict(dx=-3, dy=3, head_dx=-1, hand=(26, 26), ang=-4, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.2,
                           flutter=1, aura=1, aura_pal=P_GOLD), 150),
                     (dict(dx=-4, dy=4, head_dx=-1, hand=(25, 27), ang=-5, footB=(OX + 3, 39), footF=(OX + 17, 39), flow=0.2,
                           flutter=2, aura=1, aura_pal=P_GOLD, fx=[("flare", "tip", 5, P_GOLD)]), 150),
                     (dict(dx=5, dy=2, hand=(44, 25), ang=-1, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.9, flutter=3,
                           aura=1, aura_pal=P_GOLD, fx=[("streak", 28), ("flare", "tip", 8, P_GOLD), ("speed", (22, 17), 6, 16, P_GOLD)]),
                      50),
                     (dict(dx=5, dy=2, hand=(44, 25), ang=0, footB=(OX + 10, 39), footF=(OX + 28, 39), flow=1.5, flutter=4,
                           fx=[("streak", 16), ("flare", "tip", 5, P_GOLD)]), 70),
                     (dict(dx=4, dy=3, head_dy=1, hand=(42, 26), ang=1, footB=(OX + 9, 39), footF=(OX + 27, 39), flow=0.9,
                           flutter=5), 160),
                     (dict(dx=1, dy=1, hand=(34, 26), ang=-4, footF=(OX + 21, 39), flow=0.4, flutter=6), 160)], grip=GS)

    # ============================================================ Staff: the vault, the air game
    def st_vault():  # plant the staff's end ahead, spring off it, sail over the top, swing it free (not an attack)
        fr = mseq([(dict(dy=2, hand=(35, 25), ang=58, footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.4,
                         fx=[("dust", 44, 2)]), 50),
                   (dict(dx=1, dy=-2, hand=(35, 26), ang=74, footB=(OX + 4, 34), footF=(OX + 10, 35), bendB=-1, bendF=-1, air=True,
                         flow=1.2, flutter=1), 80),
                   (dict(dx=3, dy=-4, hand=(34, 30), ang=96, footB=(OX + 12, 30), footF=(OX + 19, 30), air=True, flow=1.5,
                         flutter=2), 100),
                   (dict(dx=2, dy=-2, hand=(33, 23), ang=-32, flow=1.1, flutter=3, **AIR), 120)], grip=GT)
        return cape_trail(fr, [1, 2], dy=-3, ang=200)

    def st_aspin():  # aerial spin: coil tight, then the staff whirls flat round the waist -- front, back, front, back
        RG = dict(sq=0.32, w=10.0)
        ring = lambda a0, a1: ("ring", (30, 24), 23, a0, a1, RG)
        return mseq([(dict(dx=-1, hand=(29, 22), ang=178, flow=0.6), 90),
                     (dict(dx=-2, head_dx=-1, hand=(28, 23), ang=176, flow=0.5, flutter=1, fx=[("glint", "tip")]), 90),
                     (dict(dx=1, hand=(34, 23), ang=2, flow=1.3, flutter=2, fx=[ring(180, 0)]), 45),
                     (dict(dx=1, hand=(34, 23), ang=2, flow=1.5, flutter=3, mirror=True, behind=True, fx=[ring(180, 0)]), 45),
                     (dict(dx=1, hand=(34, 23), ang=-2, flow=1.4, flutter=4, fx=[ring(180, 0)]), 45),
                     (dict(dx=1, hand=(34, 23), ang=2, flow=1.5, flutter=5, mirror=True, behind=True, fx=[ring(180, 0)]), 45),
                     (dict(hand=(33, 24), ang=-20, flow=0.6, flutter=6, **AIR), 100)], AIRB, grip=GT)

    def st_aspin2():  # spin finisher: a second, wider spin trailing wind, ending in an overhead chop through the floor-line
        RG = dict(sq=0.34, w=12.0, pal=P_WIND)
        ring = lambda a0, a1: ("ring", (30, 24), 25, a0, a1, RG)
        return mseq([(dict(dx=-1, hand=(29, 23), ang=-176, flow=0.7, fx=[("speed", (40, 18), 3, 8, P_WIND)]), 60),
                     (dict(dx=1, hand=(34, 23), ang=2, flow=1.4, flutter=1, fx=[ring(180, 0)]), 60),
                     (dict(dx=1, hand=(34, 23), ang=2, flow=1.6, flutter=2, mirror=True, behind=True, fx=[ring(180, 0)]), 40),
                     (dict(dx=1, hand=(34, 23), ang=-2, flow=1.5, flutter=3, fx=[ring(180, 0)]), 40),
                     (dict(dx=1, hand=(34, 23), ang=2, flow=1.6, flutter=4, mirror=True, behind=True, fx=[ring(180, 0)]), 40),
                     (dict(dx=1, dy=-1, hand=(31, 14), ang=-150, flow=1.0, flutter=5, fx=[sw(w=0.4)], fx_pal=P_WIND), 40),
                     (dict(dx=2, dy=1, hand=(39, 26), ang=30, flow=1.3, flutter=6, fx=[sw(w=0.6), ("flare", (50, 33), 6, P_WIND)],
                           fx_pal=P_WIND), 60),
                     (dict(dx=2, dy=1, hand=(38, 27), ang=34, flow=0.8, flutter=7), 100),
                     (dict(hand=(33, 25), ang=-20, flow=0.5, flutter=8, **AIR), 100)], AIRB, grip=GT)

    def st_divekick():  # dive kick: the staff swung up behind for balance, the lead leg driven down-forward like a spike
        KB = dict(head_dy=0, hand=(34, 11), ang=-174, footB=(OX + 6, 33), bendB=-1)
        fr = mseq([(dict(dy=-4, hand=(32, 17), ang=-150, footB=(OX + 9, 34), footF=(OX + 18, 34), flow=0.9), 60),
                   (dict(dy=-2, footF=(OX + 22, 34), flow=1.2, flutter=1, fx=DIVE(8), **KB), 40),
                   (dict(dx=1, dy=0, footF=(OX + 23, 36), flow=1.4, flutter=2,
                         fx=[("flare", (38, 37), 5)] + DIVE(9, 1), **KB), 50),
                   (dict(dx=1, dy=0, footF=(OX + 23, 36), flow=1.3, flutter=3, fx=DIVE(7, 2), **KB), 50),
                   (dict(dy=-3, hand=(33, 25), ang=-20, flow=0.7, flutter=4, **AIR), 100)], dict(air=True, footF=(OX + 18, 37)),
                  grip=GT)
        return cape_dive(fr, [1, 2, 3], dy=-2)

    def st_lowsweep():  # out of the roll: a crouched spinning sweep, the staff skimming the floor front then back
        RG = dict(sq=0.22, w=6.0)
        ring = lambda a0, a1: ("ring", (31, 34), 25, a0, a1, RG)
        low = dict(dy=5, head_dy=1, footB=(OX + 4, 39), footF=(FF[0] + 3, 39))
        return mseq([(dict(low, dx=-1, hand=(29, 30), ang=178, flow=0.8), 70),
                     (dict(low, dx=-2, head_dx=-1, hand=(29, 31), ang=172, flow=0.5, flutter=1), 70),
                     (dict(low, dx=1, hand=(35, 32), ang=3, flow=1.3, flutter=2, fx=[ring(180, 0), ("dust", 50, 3)]), 45),
                     (dict(low, dx=1, hand=(35, 32), ang=3, flow=1.5, flutter=3, mirror=True, behind=True,
                           fx=[ring(180, 0), ("dust", 50, 3)]), 45),
                     (dict(low, dx=2, hand=(36, 32), ang=6, flow=0.8, flutter=4), 90),
                     (dict(dx=1, dy=2, hand=(34, 28), ang=-12, footF=(FF[0] + 1, 39), flow=0.4, flutter=5), 60)], grip=GT)

    def st_twirl_up():  # rising twirl: stretched upward, the staff wheels in a vertical circle overhead, both ends cutting
        P0 = (35, 13)
        wheel = lambda a0, a1: [("ring", (P0[0] + 1, P0[1]), 16, a0, a1, dict(sq=1.0, w=4.5))]
        up = dict(footB=(OX + 9, 37), footF=(OX + 17, 38), air=True)
        fr = mseq([(dict(dy=1, hand=(31, 24), ang=160, flow=0.6, **TUCK), 70),
                   (dict(dy=-1, hand=(33, 18), ang=-150, flow=0.8, flutter=1, **up), 70),
                   (dict(dy=-2, hand=P0, ang=-100, flow=1.0, flutter=2, fx=wheel(-170, -100), **up), 40),
                   (dict(dy=-2, hand=P0, ang=-30, flow=1.1, flutter=3, fx=wheel(-100, -30), **up), 40),
                   (dict(dy=-2, hand=P0, ang=40, flow=1.1, flutter=4, fx=wheel(-30, 40), **up), 40),
                   (dict(dy=-1, hand=(33, 22), ang=-40, flow=0.6, flutter=5, **AIR), 80)], dict(dy=-2), grip=GT)
        return fr

    def st_gale():  # gale: the spin gathers wind into a tornado, then the staff flings it forward
        RG = dict(sq=0.3, w=11.0, pal=P_WIND)
        ring = lambda a0, a1: ("ring", (30, 28), 24, a0, a1, RG)
        sp = dict(dy=2, footF=(FF[0] + 2, 39))
        return mseq([(dict(dx=-2, dy=3, head_dx=-1, hand=(28, 28), ang=176, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3,
                           fx=[("glint", "tip"), ("speed", (44, 20), 3, 9, P_WIND)]), 110),
                     (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 29), ang=178, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.6,
                           flutter=1, fx=[("speed", (46, 19), 4, 12, P_WIND), ("dust", 30, 2)]), 110),
                     (dict(sp, dx=1, hand=(33, 28), ang=2, flow=1.3, flutter=2, fx=[ring(180, 0), ("dust", 34, 4)]), 45),
                     (dict(sp, dx=1, hand=(33, 28), ang=2, flow=1.5, flutter=3, mirror=True, behind=True, fx=[ring(180, 0)]), 45),
                     (dict(sp, dx=1, hand=(33, 28), ang=-2, flow=1.5, flutter=4, fx=[ring(180, 0), ("dust", 26, 4)]), 45),
                     (dict(sp, dx=1, hand=(33, 28), ang=2, flow=1.6, flutter=5, mirror=True, behind=True, fx=[ring(180, 0)]), 45),
                     (dict(dx=3, dy=1, hand=(41, 25), ang=-4, footB=(OX + 7, 39), footF=(OX + 24, 39), flow=1.5, flutter=6,
                           fx=[("wave", (49, 25), 12, 7), ("speed", (46, 16), 4, 14), ("dust", 50, 4)], fx_pal=P_WIND), 60),
                     (dict(dx=3, dy=1, hand=(40, 25), ang=-2, footB=(OX + 7, 39), footF=(OX + 24, 39), flow=1.0, flutter=7,
                           fx=[("wave", (54, 25), 11, 5)], fx_pal=P_WIND), 130),
                     (dict(dx=1, dy=1, hand=(35, 27), ang=-12, footF=(FF[0] + 2, 39), flow=0.4, flutter=8), 110)], grip=GT)

    # ============================================================ Whip: crack, thunder, grapple, the thousand lashes
    def ell(cx, cy, rx, ry, th, n=4, lag=26.0):
        """Lash control points whirling round an ellipse overhead: the tip leads at angle th, the links trail behind it."""
        pts = []
        for k in range(1, n + 1):
            a = math.radians(th - lag * (n - k))
            r = (0.45 + 0.55 * k / n)
            pts.append((cx + rx * r * math.cos(a), max(0.5, cy + ry * r * math.sin(a))))
        return pts

    def wh_overhead_hold():  # charging the overhead crack (loop): the chain whirls flat over the head, faster than the eye
        out = []
        for i in range(6):
            th = i * 60.0
            front = math.cos(math.radians(th)) > 0.5
            fx = [("flare", ell(37, 5, 16, 3.5, th)[-1], 3)] if front else []
            out.append((dict(dy=1 - (i % 2), hand=(36, 15), ang=-80, footB=(OX + 7, 39), footF=(FF[0] + 1, 39), flow=0.5 + 0.1 * (i % 2),
                             flutter=i, lash=ell(37, 5, 16, 3.5, th), fx=fx), 80))
        return mseq(out)

    def wh_overhead():  # overhead crack: lean back, the chain sails over the top and snaps out flat at full length
        return mseq([(dict(dx=-1, hand=(31, 11), ang=-110, flow=0.3, lash=[(28, 5), (22, 3), (15, 5), (10, 10)]), 100),
                     (dict(dx=-2, head_dx=-1, hand=(28, 13), ang=-145, footB=(OX + 5, 39), flow=0.2, flutter=1,
                           lash=[(22, 10), (15, 13), (10, 19), (8, 26)]), 100),
                     (dict(dx=0, hand=(34, 13), ang=-72, flow=0.8, flutter=2, lash=[(36, 5), (42, 1), (48, 1), (53, 4)]), 100),
                     (dict(dx=3, hand=(42, 22), ang=-6, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.4, flutter=3,
                           lash=[(50, 21), (56, 20), (61, 20), (63.5, 20)], fx=[("flare", (60, 20), 6), ("speed", (30, 16), 3, 10)]), 50),
                     (dict(dx=3, hand=(41, 23), ang=0, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.1, flutter=4,
                           lash=[(49, 24), (55, 26), (60, 27), (63.5, 28)]), 60),
                     (dict(dx=2, hand=(38, 26), ang=30, footF=(OX + 22, 39), flow=0.6, flutter=5,
                           lash=[(43, 31), (48, 37), (54, 38.5), (60, 38.5)]), 90),
                     (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=6), 100)])

    def wh_thunder():  # thunderclap: the charged chain crackles overhead, then cracks down with a lightning blast at the tip
        fr = [(dict(dx=-1, dy=2, hand=(31, 24), ang=150, footB=(OX + 6, 39), flow=0.3,
                    lash=[(25, 28), (20, 33), (14, 36), (8, 38.5)], fx=[("flare", (30, 25), 3)]), 120),
              (dict(dy=-1, hand=(33, 11), ang=-95, footB=(OX + 7, 38), flow=0.7, flutter=1,
                    lash=[(34, 4), (39, 1), (46, 1), (51, 3)], fx=[("flare", (50, 3), 4)]), 100),
              (dict(dx=-1, dy=-1, head_dx=-1, hand=(30, 12), ang=-130, footB=(OX + 6, 39), flow=0.4, flutter=2,
                    lash=[(27, 4), (20, 3), (14, 6), (10, 12)], fx=[("flare", (11, 11), 4)]), 80),
              (dict(dx=3, dy=2, hand=(42, 24), ang=12, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.4, flutter=3,
                    lash=[(47, 27), (51, 31), (54, 35), (56, 38.5)], fx=[("flare", (55, 35), 9), ("rings", (52, 33), (3, 6))]), 50),
              (dict(dx=3, dy=2, hand=(41, 25), ang=16, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.1, flutter=4,
                    lash=[(46, 30), (50, 34), (54, 37.5), (58, 38.5)],
                    fx=[("flare", (55, 36), 5), ("rings", (52, 33), (7, 10)), ("dust", 55, 5)]), 70),
              (dict(dx=2, dy=2, hand=(38, 27), ang=34, footF=(OX + 22, 39), flow=0.6, flutter=5,
                    lash=[(43, 32), (48, 37.5), (54, 38.5), (60, 38.5)]), 130),
              (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=6), 150)]
        for p, _ in fr[:5]:
            p["fx_pal"] = P_STORM
        return mseq(fr)

    def wh_grapple():  # grapple throw: wind back, fling the hook out and up -- the engine carries the line on to the target
        return mseq([(dict(dx=-1, hand=(30, 19), ang=-130, flow=0.3, lash=[(27, 12), (21, 11), (17, 15), (18, 20)]), 70),
                     (dict(dx=1, hand=(37, 18), ang=-40, flow=0.8, flutter=1, lash=[(42, 13), (48, 10), (54, 8), (58, 7)]), 60),
                     (dict(dx=2, hand=(41, 20), ang=-25, footF=(FF[0] + 2, 39), flow=1.1, flutter=2,
                           lash=[(47, 17), (53, 14), (58, 11.5), (63.5, 9)], fx=[("speed", (36, 13), 3, 8)]), 80),
                     (dict(dx=2, hand=(41, 20), ang=-24, footF=(FF[0] + 2, 39), flow=0.8, flutter=3,
                           lash=[(47, 17.5), (53, 15), (58, 12.5), (63.5, 10)]), 90)])

    def wh_grapple_pull():  # haul: the chain snaps taut, lean back and yank it in to the hip
        return mseq([(dict(dx=-1, hand=(39, 22), ang=-15, footF=(FF[0] + 1, 39), flow=0.5,
                           lash=[(46, 21), (53, 20), (59, 19), (63.5, 18.5)], fx=[("flare", (61, 18), 3)]), 60),
                     (dict(dx=-3, dy=1, head_dx=-1, hand=(29, 25), ang=170, footB=(OX + 4, 39), footF=(FF[0], 39), flow=0.2, flutter=1,
                           lash=[(38, 24), (47, 23), (55, 22), (63.5, 21)], fx=[("speed", (62, 18), 3, 12)]), 80),
                     (dict(dx=-2, dy=1, head_dx=-1, hand=(30, 26), ang=165, footB=(OX + 5, 39), flow=0.3, flutter=2,
                           lash=[(36, 26), (42, 28), (47, 30), (51, 33)]), 80),
                     (dict(hand=(34, 27), ang=-40, flow=0.3, flutter=3), 80)])

    def wh_grapple_zip():  # (extra, loop) yanked along the taut chain: stretched forward, legs trailing, cape torn back
        fr = mseq([(dict(dx=3, dy=-2, hand=(42, 21), ang=-20, footB=(OX + 4, 28), footF=(OX + 5, 31), air=True,
                         flow=1.8, lash=[(48, 19), (54, 17), (59, 15.5), (63.5, 14)], fx=[("speed", (22, 18), 4, 14)]), 60),
                   (dict(dx=3, dy=-2, hand=(42, 21), ang=-21, footB=(OX + 4, 29), footF=(OX + 5, 32), air=True,
                         flow=1.9, flutter=1, lash=[(48, 19), (54, 17), (59, 15.5), (63.5, 14)], fx=[("speed", (21, 19), 4, 12)]), 60)])
        return cape_trail(fr, [0, 1], dy=-2)

    def wh_retreat():  # retreat lash: back-pedal, leaning away, and crack it forward from the full stretch
        return mseq([(dict(dx=-1, hand=(30, 18), ang=-120, footB=(OX + 5, 39), flow=0.2, lash=[(26, 12), (20, 12), (15, 15), (13, 21)]), 80),
                     (dict(dx=-3, head_dx=-1, hand=(31, 12), ang=-100, footB=(OX + 3, 39), footF=(FF[0] - 1, 39), flow=0.1, flutter=1,
                           lash=[(33, 6), (39, 3), (45, 4), (50, 8)]), 80),
                     (dict(dx=-2, hand=(38, 22), ang=-10, footB=(OX + 3, 39), footF=(FF[0] + 1, 39), flow=0.6, flutter=2,
                           lash=[(45, 21), (52, 20), (58, 20), (63, 21)], fx=[("flare", (60, 21), 5)]), 45),
                     (dict(dx=-2, hand=(37, 23), ang=0, footB=(OX + 3, 39), footF=(FF[0] + 1, 39), flow=0.5, flutter=3,
                           lash=[(44, 24), (51, 26), (56, 29), (60, 32)]), 60),
                     (dict(dx=-2, hand=(35, 26), ang=30, footB=(OX + 4, 39), flow=0.4, flutter=4,
                           lash=[(40, 31), (44, 36), (49, 38.5), (55, 38.5)]), 80),
                     (dict(dx=-1, hand=(35, 27), ang=-50, flow=0.3, flutter=5), 75)])

    def wh_snap():  # snap counter: a flinch, then a wrist-snap so fast the chain kinks, a white spark where it bites
        return mseq([(dict(dx=-2, dy=1, head_dx=-1, hand=(31, 27), ang=150, footB=(OX + 5, 39), flow=0.2,
                           lash=[(26, 30), (21, 34), (15, 37), (9, 38.5)]), 40),
                     (dict(dx=0, dy=1, hand=(34, 24), ang=60, flow=0.6, flutter=1, lash=[(36, 30), (38, 35), (42, 38), (47, 38.5)]), 40),
                     (dict(dx=2, hand=(41, 23), ang=-6, footF=(FF[0] + 2, 39), flow=1.2, flutter=2,
                           lash=[(47, 21), (53, 24), (58, 21), (62.5, 23)], fx=[("flare", (59, 23), 7, SILVER)]), 40),
                     (dict(dx=2, hand=(40, 24), ang=4, footF=(FF[0] + 2, 39), flow=1.0, flutter=3,
                           lash=[(46, 26), (51, 30), (55, 28), (59, 31)], fx=[("flare", (60, 30), 3, SILVER)]), 50),
                     (dict(dx=1, hand=(37, 26), ang=30, flow=0.6, flutter=4, lash=[(41, 31), (45, 36), (50, 38.5), (56, 38.5)]), 90),
                     (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=5), 60)])

    def wh_slam():  # grapple slam: haul the catch up over the head and smash it down ahead
        return mseq([(dict(dx=-2, dy=1, head_dx=-1, hand=(30, 25), ang=170, footB=(OX + 4, 39), flow=0.3,
                           lash=[(38, 24), (46, 23), (54, 22), (61, 21)]), 80),
                     (dict(dx=-1, dy=-1, hand=(32, 11), ang=-100, footB=(OX + 6, 38), flow=0.5, flutter=1,
                           lash=[(30, 4), (24, 2), (17, 4), (12, 9)]), 90),
                     (dict(dx=1, dy=-1, hand=(36, 13), ang=-50, flow=0.9, flutter=2, lash=[(40, 5), (47, 3), (53, 6), (57, 12)]), 80),
                     (dict(dx=3, dy=3, hand=(40, 26), ang=40, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.4, flutter=3,
                           lash=[(45, 32), (50, 37), (55, 38.5), (61, 38.5)], fx=[("dust", 53, 7), ("flare", (55, 37), 7)]), 50),
                     (dict(dx=3, dy=3, head_dy=1, hand=(40, 27), ang=44, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.0,
                           flutter=4, lash=[(45, 33), (50, 38), (55, 38.5), (61, 38.5)], fx=[("dust", 53, 4)]), 80),
                     (dict(dx=2, dy=2, hand=(38, 27), ang=40, footF=(OX + 22, 39), flow=0.6, flutter=5,
                           lash=[(43, 33), (48, 38.5), (54, 38.5), (60, 38.5)]), 120),
                     (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=6), 100)])

    def wh_double():  # double crack: from the floor behind, a rising backhand whirl into a second, harder crack
        return mseq([(dict(dx=-1, dy=2, hand=(30, 29), ang=160, footB=(OX + 6, 39), flow=0.3,
                           lash=[(24, 34), (18, 38.5), (12, 38.5), (6, 38.5)]), 90),
                     (dict(dy=-1, hand=(33, 14), ang=-85, footB=(OX + 7, 38), flow=0.8, flutter=1,
                           lash=[(31, 7), (25, 4), (19, 6), (14, 11)], fx=[("glint", (32, 10))]), 130),
                     (dict(dx=3, hand=(42, 21), ang=-14, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.4, flutter=2,
                           lash=[(48, 19), (54, 18), (59, 19), (63.5, 18)], fx=[("flare", (60, 18), 6)]), 45),
                     (dict(dx=3, hand=(41, 24), ang=8, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.2, flutter=3,
                           lash=[(47, 24), (53, 28), (58, 31), (62, 34)], fx=[("flare", (61, 33), 4)]), 65),
                     (dict(dx=2, hand=(38, 26), ang=34, footF=(OX + 22, 39), flow=0.6, flutter=4,
                           lash=[(43, 31), (48, 37), (54, 38.5), (60, 38.5)]), 120),
                     (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=5), 100)])

    def wh_thousand():  # thousand lashes (loop): the arm stays out, the wrist snaps -- high, low, mid -- every crack at the tip
        rec = [(44, 20), (48, 23), (51, 21), (54, 24)]
        cr = {"hi": [(48, 18), (54, 14), (59, 12), (63.5, 10.5)],
              "lo": [(48, 27), (54, 30), (59, 32), (63.5, 33.5)],
              "mid": [(48, 22), (54, 21), (59, 22), (63.5, 21.5)]}
        tipy = {"hi": 11, "lo": 33, "mid": 22}
        out = []
        for i, k in enumerate(("hi", None, "lo", None, "mid", None)):
            body = dict(dx=2, dy=1 - (i % 2), hand=(40, 23 - (1 if k == "hi" else 0) + (1 if k == "lo" else 0)),
                        ang=-12 if k == "hi" else (10 if k == "lo" else -3), footB=(OX + 6, 39), footF=(FF[0] + 3, 39),
                        flow=0.9 + 0.2 * (i % 2), flutter=i)
            if k:
                out.append((dict(body, lash=cr[k], fx=[("flare", (60, tipy[k]), 5)]), 60))
            else:
                out.append((dict(body, lash=rec), 60))
        return mseq(out)

    moves = [("tw_demon_on", tw_demon_on), ("tw_d5", tw_d5), ("tw_d6", tw_d6), ("tw_dflurry", tw_dflurry),
             ("tw_ddash", tw_ddash), ("tw_dance", tw_dance), ("tw_dance2", tw_dance2), ("tw_dashslash", tw_dashslash),
             ("tw_counter", tw_counter), ("tw_pdodge", tw_pdodge),
             ("sp_guard", sp_guard), ("sp_guard_walk", sp_guard_walk), ("sp_gpoke", sp_gpoke), ("sp_counter", sp_counter),
             ("sp_hop", sp_hop), ("sp_charge_wind", sp_charge_wind), ("sp_charge_run", sp_charge_run), ("sp_finish", sp_finish),
             ("sp_pguard", sp_pguard), ("sp_ccounter", sp_ccounter),
             ("st_vault", st_vault), ("st_aspin", st_aspin), ("st_aspin2", st_aspin2), ("st_divekick", st_divekick),
             ("st_lowsweep", st_lowsweep), ("st_twirl_up", st_twirl_up), ("st_gale", st_gale),
             ("wh_overhead_hold", wh_overhead_hold), ("wh_overhead", wh_overhead), ("wh_thunder", wh_thunder),
             ("wh_grapple", wh_grapple), ("wh_grapple_pull", wh_grapple_pull), ("wh_grapple_zip", wh_grapple_zip),
             ("wh_retreat", wh_retreat), ("wh_snap", wh_snap), ("wh_slam", wh_slam), ("wh_double", wh_double),
             ("wh_thousand", wh_thousand)]

    # ease back toward idle at the end (v10 polish), for ground attacks that end in the neutral stance
    SETTLE = {"tw_d5", "tw_d6", "tw_dflurry", "tw_dance", "tw_dance2", "tw_dashslash", "tw_counter",
              "sp_counter", "sp_finish", "sp_ccounter", "st_lowsweep", "st_gale",
              "wh_overhead", "wh_thunder", "wh_retreat", "wh_snap", "wh_slam", "wh_double"}
    moves = [(n, settled(f) if n in SETTLE else f) for n, f in moves]

    # ---- metadata for meta_for, through gen_player's v13 opts interface: (tag, fn, opts)
    OPTS = {
        "tw_d5": dict(extras=True, x0=0, hits=[2, 3]),
        "tw_d6": dict(extras=True, hits=[2, 3, 4], both=True),
        "tw_dflurry": dict(extras=True, x0=0, hits=[2, 3, 4, 5, 6, 7]),
        "tw_dance": dict(extras=True, both=True, hits=[2, 3, 4, 5, 6, 7, 8, 9, 11], fxat=(16, -14)),
        "tw_dance2": dict(extras=True, both=True, hits=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14], fxat=(16, -14)),
        "tw_dashslash": dict(extras=True, x0=0),
        "tw_counter": dict(extras=True, x0=0, hits=[1, 2, 3]),
        "sp_gpoke": dict(x0=-4), "sp_counter": dict(x0=-4), "sp_finish": dict(x0=-4), "sp_ccounter": dict(x0=-4),
        "sp_charge_run": dict(x0=-4),                       # hits every 0.3 s: the engine's cadence over the loop
        "st_aspin": dict(hit=[-27, -28, 27, -6]), "st_aspin2": dict(both=True), "st_lowsweep": dict(both=True), "st_gale": dict(both=True),
        "st_twirl_up": dict(up=True),
        "st_divekick": dict(hit=[0, -12, 16, 22], fxat=(10, -3)),   # the kicking foot, reaching under the feet like every pogo
        "wh_overhead": dict(x0=0), "wh_thunder": dict(x0=0, fxat=(32, -7)), "wh_retreat": dict(x0=0), "wh_snap": dict(x0=0),
        "wh_slam": dict(x0=0), "wh_double": dict(x0=0),
        "wh_thousand": dict(x0=6, hits=[0, 2, 4], fxat=(34, -18)),
    }
    out = []
    for n, f in moves:
        o = dict(OPTS.get(n, {}))
        act = TIMING[n][2]
        if act is not None:
            o["active"] = act
        out.append((n, f, o))
    return out
