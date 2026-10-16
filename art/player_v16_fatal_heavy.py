"""v16 fatality tags for the heavy group (registered by gen_player.py after V15, same register(G) contract as v13/v14/v15).

Each fatality is ONE tag played on the fatality's own clock (web/src/79_fatality.js time-maps the tag over the fatality's
`dur`, so the frame ms below ARE the choreography: keep them in step with the steps in web/src/79c_fatal_heavy.js).
No `active` meta: fatalities deal their damage through the framework's hit beats. The player's sprite anchor is (28, 40):
frame x 42 = 14 px ahead of the feet, row 39 = the floor.

  gs_fatal   GREATSWORD "Grave Sunder" (1700 ms): haul the slab up into a deep coil, spring (the engine lifts the body
             ~30 px), turn it point-down in both fists at the apex, dive, IMPALE it through the foe into the floor (beat 1
             at 620), kneel over the hilt while the buried steel runs molten from the floor up, then rip it free in one
             rising cleave (beat 2 at 1080) and hold it high while the pillar burns.
  ml_fatal   MAUL "Death Knell" (1650 ms): one full wind-up spin round the waist, the hammer wheeled up over the top and
             hung there, CRASH onto the foe (beat 1 at 650), the rebound heaved straight back overhead on the toes, and the
             second pound drives it into the floor (beat 2 at 1120) -- knelt over the haft while the knell rings out.
  wb_fatal   WARBELL "Grand Requiem" (1800 ms): three tolls on the foe, each heavier than the last -- a lift-and-drop
             (400), a heave over the back shoulder (810), then the full wind-up over the top (1270) -- and a long kneel
             over the bell while the giant bell of light hangs over the foe.

  python3 art/player_v16_fatal_heavy.py   # prints the frames / total check
"""

G = None   # gen_player, set by register()
SPEC = {}
GRIP_MAUL = 4.0
GRIP_BELL = 4.0


# =================================================================================================== GREATSWORD
def gs_fatal():  # Grave Sunder: coil -> leap -> point-down at the apex -> dive -> IMPALE -> molten kneel -> rip-up cleave -> hold
    OX, FF, AIR, TUCK = G.OX, G.FF, G.AIR, G.TUCK
    KN = dict(footB=(OX + 4, 39), footF=(FF[0] + 3, 39))                 # kneeling wide over the buried slab
    PL = dict(planted=(42, 21), ang=90)                                   # driven point-first through the foe into the floor
    fr = [
        # haul: the slab dragged up from the trailing low guard, the body sinking
        (dict(dx=1, dy=2, hand=(33, 27), ang=128, footF=(FF[0] + 2, 39), flow=0.6, fx=[("dust", 12, 2)]), 100),
        # the coil: deep crouch, the blade wound up behind the shoulder, everything loaded into the legs
        (dict(dx=-1, dy=5, head_dy=1, head_dx=-1, hand=(28, 16), ang=-140, footB=(OX + 5, 39), footF=(FF[0] + 2, 39),
              flow=0.2, flutter=1, fx=[("glint", "tip")]), 160),
        # spring: off the floor, the slab swung up over the head
        (dict(dx=1, dy=-2, hand=(34, 9), ang=-82, flow=1.3, flutter=2, fx=[G.sw(w=0.4), ("dust", 28, 5)], **AIR), 90),
        # the apex: turned point-down in both fists above the head, knees up -- the hang
        (dict(dx=1, dy=-3, hand=(39, 7), ang=92, flow=1.0, flutter=3, fx=[("glint", (39, 5))], **TUCK), 160),
        # the dive: straight down, the cape torn up
        (dict(dx=2, dy=-2, hand=(41, 10), ang=90, flow=1.8, flutter=4, fx=[("vspeed", (41, 6), 4, 9)], **TUCK), 110),
        # IMPALE: through the foe into the stone, the floor bursts round the blade
        (dict(dx=2, dy=4, head_dy=1, hand=(42, 18), flow=1.6, flutter=5, aura=1,
              fx=[("dust", 42, 11), ("flare", (42, 37), 9)], **KN, **PL), 70),
        # the kneel over the hilt: the buried steel runs molten from the floor up
        (dict(dx=2, dy=6, head_dy=2, hand=(42, 18), flow=0.5, flutter=6, heat=(15, 40), fx=[("dust", 42, 5)], **KN, **PL), 110),
        (dict(dx=2, dy=6, head_dy=2, hand=(42, 18), flow=0.3, flutter=7, heat=(8, 40), **KN, **PL), 110),
        (dict(dx=2, dy=5, head_dy=1, hand=(42, 18), flow=0.2, flutter=8, heat=(2, 40), aura=1,
              fx=[("embers", (42, 30), 6, 3)], **KN, **PL), 110),
        # the wrench: shoulders thrown back, the slab tearing up out of the floor, still red-hot
        (dict(dx=3, dy=3, hand=(43, 24), ang=62, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.0, flutter=9, heat=(0, 40),
              fx=[("dust", 46, 8), ("embers", (46, 32), 8, 4)]), 70),
        # THE SUNDER: one rising cleave, the blade wheeled from the floor to the sky
        (dict(dx=3, dy=-1, hand=(40, 13), ang=-62, footB=(OX + 10, 37), footF=(FF[0] + 4, 38), flow=1.6, flutter=10, heat=(0, 40),
              fx=[G.sw(w=0.65), ("flare", "tip", 7)]), 45),
        (dict(dx=2, dy=-2, hand=(35, 9), ang=-100, footB=(OX + 10, 37), footF=(FF[0] + 3, 38), flow=1.3, flutter=11,
              fx=[G.sw(w=0.45)]), 75),
        # held high while the pillar burns: on the toes, chin up
        (dict(dx=2, dy=-1, hand=(33, 9), ang=-112, footB=(OX + 9, 38), footF=(FF[0] + 3, 39), flow=0.8, flutter=12,
              fx=[("embers", (40, 6), 7, 5)]), 190),
        # lowered onto the shoulder, then back to the guard
        (dict(dx=1, dy=1, hand=(30, 14), ang=-145, footF=(FF[0] + 2, 39), flow=0.5, flutter=13), 150),
        (dict(dx=0, dy=2, hand=(33, 24), ang=-60, flow=0.3, flutter=14), 150),
    ]
    return G.mseq(fr, grip=G.GRIP_GREAT)


# =================================================================================================== MAUL
SPIN_RG = dict(sq=0.32, w=9.0)


def _ring(a0, a1):   # the hammer whirled flat round the waist
    return ("ring", (31, 28), 20, a0, a1, SPIN_RG)


def ml_fatal():  # Death Knell: spin -> wheel overhead -> hang -> CRASH -> rebound overhead -> POUND into the floor -> kneel
    OX, FF = G.OX, G.FF
    st = dict(dy=3, footB=(OX + 6, 39), footF=(FF[0] + 2, 39))
    RG = dict(sq=1.0, w=3.0)
    fr = [
        # step in, the hammer dragged low behind the heel
        (dict(dx=1, dy=3, head_dx=1, hand=(29, 26), ang=166, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.6,
              fx=[("dust", 12, 3)]), 90),
        # the wind-up spin: one full turn, the head whirled flat round the waist
        (dict(dx=1, hand=(36, 28), ang=4, flow=1.3, flutter=1, fx=[_ring(180, 4)], **st), 70),
        (dict(dx=1, hand=(33, 27), ang=-10, slen=10, flow=1.5, flutter=2, mirror=True, behind=True, fx=[_ring(180, 0)], **st), 70),
        (dict(dx=1, hand=(36, 28), ang=4, flow=1.6, flutter=3, mirror=True, behind=True, fx=[_ring(180, 4)], **st), 70),
        (dict(dx=1, hand=(33, 27), ang=-10, slen=10, flow=1.5, flutter=4, fx=[_ring(180, 0)], **st), 70),
        # out of the turn the hammer is wheeled up behind and over the top
        (dict(dx=0, dy=1, head_dx=-1, hand=(27, 21), ang=-160, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=1.0, flutter=5,
              fx=[("ring", (29, 22), 13, 150, 205, RG)]), 70),
        (dict(dx=0, dy=-2, hand=(30, 10), ang=-125, footB=(OX + 7, 38), footF=(FF[0] + 3, 39), flow=0.9, flutter=6,
              fx=[("ring", (29, 22), 13, 195, 240, RG)]), 60),
        # the hang: on the toes, the head high over the helm
        (dict(dx=1, dy=-2, hand=(32, 9), ang=-100, footB=(OX + 7, 38), footF=(FF[0] + 3, 39), flow=0.5, flutter=7,
              fx=[("glint", "tip")]), 110),
        # CRASH: down on the foe
        (dict(dx=3, dy=2, hand=(39, 21), ang=-6, footF=(FF[0] + 4, 39), flow=1.4, flutter=8, fx=[G.sw(w=0.6)]), 40),
        (dict(dx=3, dy=6, head_dy=1, hand=(38, 27), ang=82, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.5, flutter=9,
              fx=[G.sw(w=0.45), ("dust", 39, 11), ("flare", (39, 36), 9), ("rings", (39, 37), (6, 10))]), 70),
        (dict(dx=3, dy=6, head_dy=2, hand=(38, 27), ang=84, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.9, flutter=10,
              fx=[("dust", 39, 6), ("rings", (39, 37), (11, 15))]), 120),
        # the rebound: heaved straight back up, onto the toes, higher than before
        (dict(dx=2, dy=0, hand=(33, 12), ang=-92, footB=(OX + 8, 38), footF=(FF[0] + 4, 39), flow=1.2, flutter=11,
              fx=[G.sw(w=0.45)]), 70),
        (dict(dx=2, dy=-3, hand=(31, 8), ang=-106, footB=(OX + 9, 37), footF=(FF[0] + 4, 38), flow=0.7, flutter=12,
              fx=[("flare", "tip", 5)]), 170),
        # POUND: driven into the floor with everything
        (dict(dx=3, dy=2, hand=(39, 20), ang=-4, footF=(FF[0] + 4, 39), flow=1.5, flutter=13, fx=[G.sw(w=0.6)]), 40),
        (dict(dx=3, dy=7, head_dy=2, hand=(38, 28), ang=86, footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=1.7, flutter=14,
              fx=[G.sw(w=0.45), ("dust", 39, 15), ("flare", (39, 35), 12), ("rings", (39, 37), (7, 12))]), 80),
        # knelt over the haft while the knell rings out
        (dict(dx=3, dy=7, head_dy=2, hand=(38, 28), ang=88, footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=1.0, flutter=15,
              fx=[("dust", 39, 8), ("rings", (39, 37), (13, 19))]), 140),
        (dict(dx=3, dy=6, head_dy=2, hand=(38, 28), ang=88, footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=0.5, flutter=16,
              fx=[("dust", 39, 3)]), 120),
        (dict(dx=2, dy=4, head_dy=1, hand=(37, 27), ang=80, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=0.4, flutter=17), 90),
        (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(FF[0] + 1, 39), flow=0.3, flutter=18), 100),
    ]
    return G.mseq(fr, grip=GRIP_MAUL)


# =================================================================================================== WARBELL
def _floor(x, k=0, **kw):   # the bell mouth-down on the floor in front, knees bent over it (as player_v15_bell._floor)
    d = dict(dx=3, dy=5 + k, head_dy=1 + min(k, 1), hand=(x - 1, 21), ang=58 + 2 * k, footB=(G.OX + 6, 39),
             footF=(G.FF[0] + 4, 39))
    if "ang" in kw:
        kw["ang"] = 58 + (kw["ang"] - 80) * 0.5
    d.update(kw)
    return d


def wb_fatal():  # Grand Requiem: toll I (lift & drop) -> toll II (over the back shoulder) -> toll III (full wind, over the top)
    OX, FF, E = G.OX, G.FF, G.EMBER
    fr = [
        # step in, the bell swinging low in front
        (dict(dx=1, dy=2, hand=(34, 25), ang=40, flow=0.4), 80),
        # TOLL I: lifted straight up in front, onto the toes, and let drop
        (dict(dx=0, dy=1, hand=(33, 15), ang=-75, footF=(FF[0] + 1, 39), flow=0.7, flutter=1), 110),
        (dict(dx=-1, dy=-1, head_dx=-1, hand=(32, 10), ang=-95, footB=(OX + 7, 38), footF=(FF[0] + 1, 39), flow=0.5, flutter=2,
              fx=[("glint", "tip")]), 160),
        (dict(dx=1, dy=1, hand=(37, 17), ang=-30, footF=(FF[0] + 3, 39), flow=1.1, flutter=3, fx=[G.sw(w=0.5)]), 50),
        (dict(flow=1.3, flutter=4, fx=[G.sw(w=0.4), ("dust", 41, 8), ("flare", (41, 37), 5), ("rings", (41, 37), (6, 10))],
              **_floor(39, 0, ang=74)), 70),
        (dict(flow=0.7, flutter=5, fx=[("dust", 41, 3), ("rings", (41, 37), (11, 15))], **_floor(39, 1, ang=76)), 130),
        # TOLL II: heaved up off the floor and over the back shoulder, then brought down harder
        (dict(dx=1, dy=0, hand=(31, 12), ang=-128, footF=(FF[0] + 3, 39), flow=0.9, flutter=6, fx=[G.sw(w=0.35)]), 90),
        (dict(dx=-1, dy=-2, head_dx=-1, hand=(29, 9), ang=-160, footB=(OX + 7, 38), footF=(FF[0] + 2, 39), flow=0.5, flutter=7,
              fx=[("glint", "tip")]), 80),
        (dict(dx=2, dy=2, hand=(38, 19), ang=-10, footF=(FF[0] + 3, 39), flow=1.3, flutter=8, fx=[G.sw(w=0.6)]), 40),
        (dict(flow=1.4, flutter=9, fx=[G.sw(w=0.45), ("dust", 42, 10), ("flare", (42, 37), 7), ("rings", (42, 37), (6, 11))],
              **_floor(40, 1, ang=76)), 70),
        (dict(flow=0.8, flutter=10, fx=[("dust", 42, 4), ("rings", (42, 37), (12, 17))], **_floor(40, 1, ang=78)), 140),
        # TOLL III: the full wind-up -- coiled low on the back foot, the bell's weight hanging behind the head ...
        (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 13), ang=-150, footB=(OX + 4, 39), footF=(FF[0] + 2, 39), flow=0.4, flutter=11,
              fx=[("glint", "tip")]), 110),
        # ... all the way over the top ...
        (dict(dx=-1, dy=-2, hand=(30, 9), ang=-125, footB=(OX + 7, 38), footF=(FF[0] + 2, 39), flow=0.9, flutter=12,
              fx=[("ring", (29, 20), 13, 195, 240, dict(sq=1.0, w=3.0))]), 70),
        (dict(dx=1, dy=-1, hand=(34, 11), ang=-80, footF=(FF[0] + 3, 39), flow=1.2, flutter=13, fx=[G.sw(w=0.45)]), 40),
        (dict(dx=3, dy=2, hand=(40, 21), ang=-6, footF=(FF[0] + 4, 39), flow=1.5, flutter=14, fx=[G.sw(w=0.6)]), 30),
        # ... and down with everything: it rings
        (dict(flow=1.7, flutter=15, fx=[G.sw(w=0.45), ("dust", 44, 13), ("flare", (44, 36), 10, E[:3]), ("rings", (44, 37), (7, 12))],
              **_floor(41, 2, ang=74)), 80),
        # the long kneel over the bell while the requiem hangs in the air
        (dict(flow=1.0, flutter=16, fx=[("dust", 44, 7), ("rings", (44, 37), (13, 19))], **_floor(41, 2, ang=76)), 120),
        (dict(flow=0.5, flutter=17, fx=[("rings", (44, 37), (18, 24))], **_floor(41, 2, ang=76, head_dy=2)), 100),
        (dict(flow=0.3, flutter=18, fx=[("dust", 44, 2)], **_floor(40, 1, ang=74)), 80),
        (dict(dx=1, dy=3, hand=(36, 27), ang=58, footF=(FF[0] + 2, 39), flow=0.4, flutter=19), 70),
        (dict(dx=1, dy=2, hand=(35, 28), ang=40, footF=(FF[0] + 1, 39), flow=0.3, flutter=20), 80),
    ]
    return G.mseq(fr, grip=GRIP_BELL)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    E = []

    def add(tag, fn, total, settle=True, **meta):
        SPEC[tag] = total
        E.append((tag, g.settled(fn) if settle else fn, meta))

    add("gs_fatal", gs_fatal, 1700)
    add("ml_fatal", ml_fatal, 1650)
    add("wb_fatal", wb_fatal, 1800)
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    mod = sys.modules.get("player_v16_fatal_heavy")
    for t in [e[0] for e in mod.register(GP)]:
        ms = [m for _, m in fns[t]()]
        starts, acc = [], 0
        for m in ms:
            starts.append(acc); acc += m
        print(f"{t:12} frames {len(ms):3}  total {sum(ms):5}  spec {mod.SPEC.get(t)}  {'OK' if sum(ms) == mod.SPEC.get(t) else 'MISMATCH'}")
        print("             starts", starts)
