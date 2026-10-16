"""v16 fatality tags for the agile group (registered by gen_player.py after V15, same register(G) contract as v13/v14/v15).

Each fatality is ONE tag played on the fatality's own clock (web/src/79_fatality.js time-maps the tag over the
fatality's `dur`, so the frame ms below ARE the choreography: keep them in step with web/src/79e_fatal_agile.js).
No `active` meta: fatalities deal their damage through the framework's hit beats.

  tw_fatal   DUAL BLADES "Crimson Requiem" (1600 ms): coil low with the blades crossed back, a lunge that blurs out of
             sight (240 ms: the body VANISHES -- blank frames -- while crimson phantoms strike from every angle, drawn
             in-engine), reappear tucked above the foe, hang with both blades crossed behind the head, open them in an
             X on the dive (beat at ~1050 ms), land low with the blades spread while the crimson cross burns.
  st_fatal   STAFF "Tempest Ascension" (1700 ms): plant the staff ahead and vault onto the foe feet-first (beat ~200),
             a rising four-turn spin in the air with the staff level at the waist (beats ~450 / ~700; wind rings),
             hang with the staff overhead, flip it point-down and plunge it into the floor (beat ~1090: the vortex).
  wh_fatal   WHIP "Thunder Leash" (1700 ms): coil, fling the chain at the neck (the chain past the handle is drawn
             in-engine: stub lash here), the wrap (~260), lean back and haul it taut (~380), one full turn with the
             chain whirled overhead, plant with the arm high, crack it down (thunder runs the chain, beat ~1130),
             let it fall slack and gather it in.
  ft_fatal   MARTIAL ARTS "Hundred Embers" (1700 ms): a Swift palm flurry (eight blows, near / far, ~60 ms each), the
             switch to Iron mid-flurry (a rooted palm at 600), three Iron blows, then the Ember palm: sink with both
             hands at the hip as the wraps catch, both palms driven out as one (beat ~1160), hold, settle into Iron.

`python3 art/player_v16_fatal_agile.py` prints the frames/total check.
"""
import math

G = None   # gen_player, set by register()
SPEC = {}

DEMON = ((255, 196, 186), (226, 52, 64), (120, 16, 34))          # crimson (as the dual's demon mode)
SWIFT = ((236, 246, 255), (168, 204, 240), (86, 118, 170))       # martial arts: Swift smears
IRON = ((255, 236, 190), (255, 150, 70), (168, 66, 30))          # martial arts: Iron smears
EMBERP = ((255, 244, 200), (255, 170, 80), (200, 70, 30))        # the Ember palm
KN = "penitent_knuckles"


def _ow(h, a, front=False, slen=18):          # dual: the off-hand blade
    return (h, a, slen, front) if front or slen != 18 else (h, a)


# =================================================================================================== DUAL BLADES
def tw_fatal():
    OX, FF, AIRB = G.OX, G.FF, G.AIRB
    sw, DIVE = G.sw, G.DIVE
    A = [   # 0 .. 240: the coil and the vanishing lunge
        (dict(dx=-1, dy=2, hand=(29, 26), ang=174, offw=_ow((28, 28), 178), footB=(OX + 6, 39), flow=0.3,
              aura=1, aura_pal=DEMON), 90),
        (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 27), ang=178, offw=_ow((27, 28), 172), footB=(OX + 5, 39), flow=0.4,
              flutter=1, aura=2, aura_pal=DEMON, fx=[("glint", "tip"), ("flare", (27, 22), 4, DEMON)]), 110),
        (dict(dx=4, dy=4, head_dy=1, hand=(35, 31), ang=172, offw=_ow((33, 31), 166), footB=(OX + 3, 39), footF=(OX + 27, 39),
              flow=1.9, flutter=2, aura=2, aura_pal=DEMON, fx=[("speed", (24, 20), 5, 18, DEMON)]), 40),
    ]
    B = [   # 760 .. 1600: reappear above, the X, the landing
        (dict(AIRB, dx=0, hand=(31, 15), ang=-118, offw=_ow((32, 16), -64, True), flow=1.2, flutter=3, aura=2, aura_pal=DEMON,
              fx=[("flare", (31, 20), 5, DEMON)]), 80),
        (dict(AIRB, dx=-1, dy=-4, hand=(30, 11), ang=-112, offw=_ow((31, 12), -58, True), flow=0.9, flutter=4, aura=2,
              aura_pal=DEMON, fx=[("glint", (30, 4))], fx_pal=DEMON), 160),
        (dict(AIRB, dx=2, dy=-3, head_dx=1, hand=(40, 26), ang=35, offw=_ow((40, 20), -30, True), offsw=0.55, flow=1.5,
              flutter=5, fx=[sw(w=0.55)] + DIVE(8), fx_pal=DEMON), 40),
        (dict(AIRB, dx=3, dy=-2, head_dx=1, hand=(41, 31), ang=62, offw=_ow((42, 27), 40, True), offsw=0.5, flow=1.6,
              flutter=6, fx=[sw(w=0.5)] + DIVE(10, 1), fx_pal=DEMON), 50),
        (dict(dx=3, dy=4, head_dy=1, hand=(42, 29), ang=8, offw=_ow((21, 29), 176), footB=(OX + 5, 39), footF=(FF[0] + 4, 39),
              flow=1.0, flutter=7, fx=[("dust", 46, 4), ("dust", 18, 2)], fx_pal=DEMON), 70),
        (dict(dx=3, dy=4, head_dy=1, hand=(42, 29), ang=10, offw=_ow((21, 29), 174), footB=(OX + 5, 39), footF=(FF[0] + 4, 39),
              flow=0.6, flutter=8), 190),
        (dict(dx=1, dy=1, hand=(36, 27), ang=-20, offw=_ow((31, 27), 150), footB=(OX + 8, 39), footF=(FF[0] + 2, 39),
              flow=0.4, flutter=9), 130),
        (dict(hand=(35, 27), ang=-35, offw=_ow((29, 28), 152), flow=0.3, flutter=10), 120),
    ]
    a = G.mseq(A)
    b = G.mseq(B)
    G.cape_trail(a, [2], dy=-1, ang=182)
    G.cape_dive(b, [2, 3], dy=-2)
    return a + [({}, 520)] + b      # 240 .. 760: gone (the phantoms are drawn in-engine)


# =================================================================================================== STAFF
def st_fatal():
    OX, FF, GT, PW, TUCK = G.OX, G.FF, G.GRIP_STAFF, G.P_WIND, G.TUCK
    RG = dict(sq=0.3, w=11.0)
    ring = lambda a0, a1: ("ring", (30, 28), 24, a0, a1, RG)
    fr = [
        # plant the far end ahead and push off it
        (dict(dx=1, dy=1, hand=(37, 26), ang=58, footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.4, fx=[("dust", 46, 2)]), 100),
        (dict(dy=-2, hand=(35, 25), ang=72, footB=(OX + 7, 36), footF=(OX + 20, 34), air=True, flow=0.9, flutter=1), 90),
        # the vault: both feet kicking up through the foe
        (dict(dx=-1, dy=-4, head_dx=-1, hand=(33, 24), ang=82, footB=(OX + 20, 31), footF=(OX + 25, 27), air=True, flow=1.5,
              flutter=2, fx=[("flare", (40, 26), 6, PW), ("vspeed", (38, 34), 2, 8, PW)]), 60),
        (dict(dx=-2, dy=-5, head_dx=-1, hand=(32, 22), ang=96, footB=(OX + 16, 27), footF=(OX + 21, 24), air=True, flow=1.3,
              flutter=3), 70),
    ]
    # the rising spin: four turns, the staff level at the waist, front / back alternating
    for i in range(8):
        back = i % 2 == 1
        fr.append((dict(dy=-2, hand=(33, 28), ang=(2, -4, 4, -2, 6, -6, 2, 0)[i], flow=1.2 + 0.05 * i, flutter=4 + i,
                        mirror=back, behind=back, fx=[ring(180, 0)], fx_pal=PW, **TUCK), 65))
    fr += [
        # the apex: staff raised overhead, hanging
        (dict(dy=-3, hand=(33, 13), ang=-90, flow=0.8, flutter=12, fx=[("glint", "tip")], fx_pal=PW, **TUCK), 160),
        # flip the point down, plunge
        (dict(dy=-4, hand=(34, 22), ang=90, slen=22, flow=1.2, flutter=13, fx=G.DIVE(6), **TUCK), 40),
        (dict(dy=-4, hand=(33, 21), ang=90, slen=22, flow=1.5, flutter=14, fx=[("streak", 10)] + G.DIVE(9, 1),
              footB=(OX + 12, 36), footF=(OX + 16, 37), air=True), 50),
        # impact: driven into the floor
        (dict(dy=4, head_dy=1, hand=(38, 26), ang=92, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.6, flutter=15,
              fx=[("dust", 30, 8), ("dust", 46, 8), ("flare", (39, 37), 10, PW), ("speed", (24, 35), 3, 9, PW)]), 70),
        (dict(dy=4, head_dy=1, hand=(38, 26), ang=92, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.4, flutter=16,
              fx=[("dust", 16, 7), ("dust", 58, 7), ("flare", (39, 37), 5, PW)]), 100),
        (dict(dy=4, head_dy=1, hand=(38, 26), ang=92, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.3, flutter=17), 160),
        (dict(dy=2, hand=(34, 22), ang=-80, flow=0.4, flutter=18), 140),
        (dict(hand=(33, 27), ang=-14, flow=0.3, flutter=19), 140),
    ]
    out = G.mseq(fr, grip=GT)
    G.cape_trail(out, [1, 2, 3], dy=-3, ang=200)
    return G.cape_dive(out, [13, 14], dy=-3)


# =================================================================================================== WHIP
def _stub(hand, ang):
    """A lash stub (< 7 px: no ornament) pointing along the handle: the chain past it is drawn in-engine."""
    a = math.radians(ang)
    return [(hand[0] + math.cos(a) * 5.0, hand[1] + math.sin(a) * 5.0)]


# frames: (ms, pose) -- the JS (WH_HAND in 79e_fatal_agile.js) mirrors hand / ang / dx / dy / mirror per frame
WH_FRAMES = None


def wh_frames():
    OX, FF, PS = G.OX, G.FF, G.P_STORM
    S = lambda d: dict(d, lash=_stub(d["hand"], d["ang"]))
    return [
        (dict(dx=-1, dy=1, hand=(30, 18), ang=-130, flow=0.3, lash=[(28, 10), (22, 9), (19, 14), (22, 18)]), 80),
        (dict(dx=-2, dy=2, head_dx=-1, hand=(28, 16), ang=-150, footB=(OX + 5, 39), flow=0.2, flutter=1,
              lash=[(22, 10), (16, 12), (12, 18), (11, 25)], fx=[("glint", (29, 14))]), 100),
        # the throw
        (S(dict(dx=1, dy=1, hand=(38, 19), ang=-30, footF=(FF[0] + 2, 39), flow=0.9, flutter=2, fx=[("speed", (30, 16), 3, 10)])), 50),
        (S(dict(dx=2, dy=1, hand=(41, 21), ang=-20, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.0, flutter=3)), 130),
        # the yank: lean back, both hands on the chain
        (S(dict(dx=-3, dy=1, head_dx=-1, hand=(30, 23), ang=-8, off=(37, 22), footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2,
                flutter=4, fx=[("speed", (50, 20), 3, 12)])), 60),
        (S(dict(dx=-3, dy=2, head_dx=-1, hand=(29, 24), ang=-6, off=(36, 23), footB=(OX + 4, 39), flow=0.3, flutter=5)), 140),
        # one full turn, the chain whirled overhead
        (S(dict(dx=-1, hand=(33, 14), ang=-100, flow=0.9, flutter=6, mirror=True)), 90),
        (S(dict(dy=-1, hand=(34, 12), ang=-80, flow=1.3, flutter=7, mirror=True)), 90),
        (S(dict(dy=-1, hand=(32, 12), ang=-100, flow=1.4, flutter=8)), 90),
        (S(dict(hand=(35, 14), ang=-70, flow=1.1, flutter=9)), 90),
        # plant, the arm high behind: the static gathers
        (S(dict(dx=-1, dy=1, head_dx=-1, hand=(29, 11), ang=-130, footB=(OX + 4, 39), footF=(FF[0] + 3, 39), flow=0.5, flutter=10,
                fx=[("glint", (29, 10))], fx_pal=PS)), 140),
        # the crack
        (S(dict(dx=2, dy=2, hand=(41, 26), ang=20, footB=(OX + 6, 39), footF=(OX + 24, 39), flow=1.5, flutter=11,
                fx=[("speed", (30, 18), 3, 10, PS)])), 50),
        (S(dict(dx=3, dy=3, head_dy=1, hand=(42, 28), ang=30, footB=(OX + 6, 39), footF=(OX + 25, 39), flow=1.3, flutter=12,
                fx=[("flare", (47, 31), 4, PS)])), 60),
        (S(dict(dx=3, dy=3, head_dy=1, hand=(41, 29), ang=40, footB=(OX + 6, 39), footF=(OX + 25, 39), flow=0.7, flutter=13)), 250),
        # gather it in: the chain back in the sprite, lying along the floor
        (dict(dx=1, dy=1, hand=(36, 26), ang=10, flow=0.5, flutter=14, lash=[(40, 31), (44, 36), (49, 38.5), (54, 38.5)]), 150),
        (dict(hand=(35, 27), ang=-50, flow=0.3, flutter=15), 130),
    ]


def wh_fatal():
    return G.mseq(wh_frames())


# =================================================================================================== MARTIAL ARTS
def ft_fatal():
    OX, OY, FF = G.OX, G.OY, G.FF
    ow = lambda x, y, a, front=True: ((x, y), a, 18, front)
    SW = dict(hand=(34, 20), ang=-62, offw=ow(37, 21, -34), footB=(OX + 9, 39), footF=(OX + 19, 39))
    IR = dict(dy=3, hand=(30, 29), ang=-10, offw=ow(38, 21, -75), footB=(OX + 4, 39), footF=(OX + 23, 39), bendF=1)
    P = lambda base, **k: dict(base, **k)
    fr = [(P(SW, dx=1, dy=1, hand=(35, 21), offw=ow(38, 22, -34), flow=0.6), 120)]
    # the Swift flurry: eight palms, near / far, walking the height up and down the foe
    HS = (((46, 20), (35, 22)), ((35, 21), (46, 23)), ((46, 23), (35, 21)), ((35, 22), (46, 19)),
          ((47, 18), (35, 22)), ((35, 21), (46, 25)), ((46, 24), (35, 21)), ((35, 22), (47, 21)))
    for i, (h, o) in enumerate(HS):
        near = i % 2 == 0
        tip = h if near else o
        fr.append((P(SW, dx=2 + (i >= 4), dy=1, lean=1, hand=h, ang=-3 if near else -60, offw=ow(o[0], o[1], -60 if near else -3),
                     footB=(OX + 10, 39), footF=(OX + 22, 39), flow=0.9 + 0.05 * i, flutter=i + 1,
                     fx=[("speed", (tip[0] - 3, tip[1] + 1), 2, 8), ("flare", (tip[0] + 5, tip[1]), 2 + (i % 3 == 0))], fx_pal=SWIFT), 60))
    fr += [
        # the switch: the feet root mid-flurry, a heavy palm
        (P(IR, dx=3, dy=3, lean=1, hand=(46, 24), ang=0, offw=ow(31, 27, -100, False), footB=(OX + 7, 39), footF=(OX + 26, 39), flow=1.0,
           flutter=9, fx=[("speed", (42, 25), 3, 12), ("flare", (51, 24), 5), ("dust", 40, 2), ("dust", 14, 2)], fx_pal=IRON), 80),
        # Iron blows: far palm, elbow, near palm
        (P(IR, dx=3, dy=3, lean=1, hand=(32, 27), ang=-60, offw=ow(47, 22, 0), footB=(OX + 7, 39), footF=(OX + 26, 39), flow=1.0,
           flutter=10, fx=[("speed", (43, 23), 3, 10), ("flare", (52, 22), 5)], fx_pal=IRON), 70),
        (P(IR, dx=4, dy=3, lean=2, hand=(36, 21), ang=180, offw=ow(31, 25, -100, False), footB=(OX + 8, 39), footF=(OX + 27, 39), flow=1.1,
           flutter=11, fx=[("ring", (31, 23), 10, -120, 0, dict(sq=0.5, w=2.8)), ("flare", (43, 22), 5), ("dust", 41, 2)], fx_pal=IRON), 70),
        (P(IR, dx=4, dy=3, lean=2, hand=(47, 21), ang=0, offw=ow(32, 26, -100, False), footB=(OX + 8, 39), footF=(OX + 27, 39), flow=1.2,
           flutter=12, fx=[("speed", (43, 22), 3, 12), ("flare", (52, 21), 6)], fx_pal=IRON), 80),
        # the Ember palm: sink, both hands at the hip, the wraps catch
        (P(IR, dx=-1, dy=4, head_dx=-1, hand=(26, 29), ang=180, offw=ow(27, 30, 180, False), footB=(OX + 3, 39), footF=(OX + 21, 39),
           flow=0.4, flutter=13, aura=1, aura_pal=EMBERP, fx=[("flare", (25, 29), 4), ("dust", 18, 2), ("dust", 40, 2)], fx_pal=EMBERP), 130),
        (P(IR, dx=-2, dy=5, head_dx=-1, head_dy=1, hand=(25, 30), ang=180, offw=ow(26, 31, 180, False), footB=(OX + 3, 39), footF=(OX + 21, 39),
           flow=0.6, flutter=14, aura=2, aura_pal=EMBERP, fx=[("flare", (24, 30), 7), ("embers", (26, 23), 7, 5)], fx_pal=EMBERP), 120),
        # both palms out as one
        (P(IR, dx=5, dy=3, lean=2, hand=(47, 21), ang=0, offw=ow(47, 25, 0), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=2.0, flutter=15,
           aura=2, aura_pal=EMBERP, fx=[("speed", (43, 23), 4, 18), ("flare", (53, 23), 11), ("dust", 46, 4)], fx_pal=EMBERP), 80),
        (P(IR, dx=5, dy=3, lean=2, hand=(46, 21), ang=0, offw=ow(46, 25, 0), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=1.4, flutter=16,
           fx=[("flare", (53, 23), 6), ("embers", (52, 22), 8, 9)], fx_pal=EMBERP), 120),
        (P(IR, dx=5, dy=3, lean=2, hand=(46, 22), ang=0, offw=ow(46, 25, 0), footB=(OX + 9, 39), footF=(OX + 28, 39), flow=0.9, flutter=17), 130),
        (P(IR, dx=3, dy=3, flow=0.7, flutter=18, footB=(OX + 7, 39), footF=(OX + 26, 39)), 110),
        (P(IR, dx=1, flow=0.4, flutter=19, footB=(OX + 5, 39), footF=(OX + 24, 39)), 110),
    ]
    # the fist rig's kicking-leg pass isn't needed (no kicks): plain mseq with the twin knuckles
    return G.mseq(fr)


# =================================================================================================== registry
def register(g):
    global G
    G = g
    if KN not in G.TWIN_KINDS:            # both fists read (the v15 fist module registers this too)
        G.TWIN_KINDS = tuple(G.TWIN_KINDS) + (KN,)
    G.EXTRA_KINDS.add(KN)
    E = []

    def add(tag, fn, total):
        SPEC[tag] = total
        E.append((tag, fn, {}))

    add("tw_fatal", tw_fatal, 1600)
    add("st_fatal", st_fatal, 1700)
    add("wh_fatal", wh_fatal, 1700)
    add("ft_fatal", ft_fatal, 1700)
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    mod = sys.modules.get("player_v16_fatal_agile")
    for t in [e[0] for e in mod.register(GP)]:
        ms = [m for _, m in fns[t]()]
        print(f"{t:12} frames {len(ms):3}  total {sum(ms):5}  spec {mod.SPEC.get(t)}  {'OK' if sum(ms) == mod.SPEC.get(t) else 'MISMATCH'}")
