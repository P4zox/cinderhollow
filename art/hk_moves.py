"""The Hearthkeeper's move library (keyframes).  Imported by art/gen_hearthkeeper.py.

Angles: 0 = forward (+x), 90 = down, -90 = up, 180 = back.  A swing over the top runs through increasing angles
(150 back-down -> 270 up -> 360 forward -> 420 forward-down), so tweens travel the arc he would really cut.
Hands: an/af + rn/rf (polar from the shoulder), or hn/hf = (dx from the anchor, dy from the floor line) for a
planted hand.  x/y move the hip (the root) from the anchor; a move that ends with x != 0 travels (meta shift).
"""

PHASE_TAGS = {1: [], 2: [], 3: []}
AX, AY, FLOOR = 80, 139, 138


def register(ANIMS, K, Anim):
    def anim(tag, phases, loop=False):
        def deco(fn):
            for p_ in phases:      # per phase: idle / walk / stagger / temper differ between phases
                ANIMS[(tag, p_)] = lambda ph, fn=fn: Anim(tag, fn(ph), loop=loop, common=COMMON[ph], phase=ph)
            for p in phases:
                PHASE_TAGS[p].append(tag)
            return fn
        return deco

    # ------------------------------------------------------------ per-phase look
    COMMON = {
        1: dict(weapon="hammer", tongs_far=True, eyes=0.55, wabove=34.0, wbelow=6.0),
        2: dict(weapon=None, eyes=0.8, theat=0.0, crown=0.25, mn="claw", mf="claw",
                lights=[((AX + 16, FLOOR + 4), 54.0, 0.5), ((AX - 14, FLOOR + 4), 40.0, 0.4)]),
        3: dict(weapon="ftongs", eyes=1.0, fire=0.55, crown=0.8, chest=0.6, coal=1.0, mf="claw"),
    }

    # P1 idle: the hammer planted head-down beside him, a long arm resting on its butt; the tongs hang from the far hand
    IDLE1 = dict(x=0, y=0, lean=3, tilt=2, fn=8, ff=-7, hn=(17.5, -43.5), wa=90, wbelow=1.5, wabove=38.5, wflip=-1,
                 af=116, rf=0.88, ta=100, topen=3, wind=1.0)

    @anim("idle", [1], loop=True)
    def idle(ph):
        import math
        ks = []
        for i in range(7):
            a = 2 * math.pi * i / 6
            b = -0.7 * math.sin(a)
            k = dict(IDLE1, y=b, hn=(17.5, -43.5), lean=3 + 0.6 * math.sin(a), tilt=2 - 0.8 * math.sin(a - 0.6),
                     af=116 + 1.5 * math.sin(a - 0.5), ta=100 + 2 * math.sin(a - 1.0), eyes=0.5 + 0.08 * math.sin(a * 2))
            ks.append(K(1, 170, "io", **k))
        return ks

    @anim("walk", [1], loop=True)
    def walk(ph):
        # a slow, heavy stride; the hammer carried low at his side, its beak trailing; the tongs swing with the far arm
        base = dict(lean=7, tilt=-2, an=72, rn=0.86, wa=128, wbelow=4.0, wabove=36.0, wflip=1, rf=0.92, ta=100, wind=2.5)
        S = 11.0
        ks = [K(1, 115, **dict(base, x=0, y=1.4, fn=S, ff=-S, lock="n", af=112, an=70, ta=104)),
              K(1, 115, "out", **dict(base, y=0.2, fn=S * 0.5, ff=-S * 0.3, ffl=3.5, lock="n", af=104, an=74, ta=101)),
              K(1, 115, "io", **dict(base, y=-0.6, fn=0, ff=S * 0.4, ffl=4.0, lock="n", af=96, an=78, ta=98)),
              K(1, 115, "in", **dict(base, y=0.2, fn=-S * 0.5, ff=S * 0.85, ffl=1.5, lock="n", af=90, an=82, ta=96)),
              K(1, 115, **dict(base, y=1.4, fn=-S, ff=S, ffl=0, lock="f", af=86, an=84, ta=94)),
              K(1, 115, "out", **dict(base, y=0.2, fn=-S * 0.3, ff=S * 0.5, fnl=3.5, lock="f", af=92, an=80, ta=97)),
              K(1, 115, "io", **dict(base, y=-0.6, fn=S * 0.4, ff=0, fnl=4.0, lock="f", af=100, an=76, ta=100)),
              K(1, 115, "in", **dict(base, y=0.2, fn=S * 0.85, ff=-S * 0.5, fnl=1.5, lock="f", af=106, an=72, ta=103)),
              K(1, 115, **dict(base, x=0, y=1.4, fn=S, ff=-S, fnl=0, lock="n", af=112, an=70, ta=104))]
        return ks

    @anim("slam", [1])
    def slam(ph):
        # the overhead slam: lifts the hammer from the floor, rears back over his shoulder (held: the tell), then one
        # long lunge brings it down ahead of him; the head bites the floor, he settles over it, and gathers back up
        return [
            K(1, 90, **IDLE1),
            K(2, 230, "out", lean=-2, tilt=4, y=-1, an=-10, rn=0.62, wa=-70, wbelow=6, wabove=34, hn=None, fn=10, ff=-8, af=110, ta=104, lift_n=0.3),
            K(2, 250, "out", hold=200, lean=-11, tilt=8, y=0.5, an=-112, rn=0.82, wa=205, fn=13, ff=-10, lift_n=1.0,
              af=135, rf=0.8, ta=140, topen=6, tel=True, eyes=0.8),
            K(1, 75, "in", lean=12, tilt=2, x=10, y=3, an=-58, rn=0.92, wa=300, fn=30, ff=-12, lift_n=0.8, af=155, rf=0.78, ta=165, sm=1),
            K(1, 60, "in", lean=24, tilt=-6, x=17, y=7, an=38, rn=0.86, wa=422, gnd=1, fn=37, ff=-14, lift_n=0.0, af=168, rf=0.8, ta=176, topen=7,
              act=1, ev="land", fx=[("sparks", None, None, 30, -90, 150, 18), ("ring", None, 24, 1.0)]),
            K(2, 230, "out", hold=140, lean=21, tilt=-3, x=18, y=7.5, an=44, rn=0.85, wa=424, gnd=1, fn=37, ff=-14, af=165, ta=166, eyes=0.7),
            K(2, 280, "io", lean=10, tilt=1, x=18, y=2, an=20, rn=0.75, wa=330, gnd=0, fn=30, ff=4, af=120, ta=110, topen=4),
            K(2, 300, "io", **dict(IDLE1, x=18, fn=8 + 18, ff=-7 + 18, hn=(17.5 + 18, -43.5))),
        ]

    # ------------------------------------------------------------------------------------------------ P1 THE SMITH
    def back_to(base, dx=0, n=2, ms=300, e="io", **kw):
        d = dict(base); d.update(kw)
        d["x"] = base.get("x", 0) + dx
        d["fn"] = base["fn"] + dx; d["ff"] = base["ff"] + dx
        if "hn" in base and base["hn"]:
            d["hn"] = (base["hn"][0] + dx, base["hn"][1])
        return K(n, ms, e, **d)

    @anim("sweep", [1])
    def sweep(ph):
        # the low sweep: the beak drawn back along the floor behind him (crouched, the tell), then dragged round
        # through the space at your ankles -- jump it -- and up past his front in a follow-through
        return [
            K(1, 90, **IDLE1),
            K(2, 240, "out", y=4, lean=10, tilt=4, an=120, rn=0.8, hn=None, wa=168, wbelow=6, wabove=34, wflip=-1, fn=14, ff=-10,
              af=60, rf=0.7, ta=40, topen=4),
            K(1, 160, "out", hold=170, y=6, lean=14, tilt=2, an=150, rn=0.86, wa=176, ff=-13, af=40, ta=20, tel=True, eyes=0.8),
            K(1, 70, "in", y=6, x=6, lean=12, an=96, rn=0.92, wa=112, fn=22, act=1),
            K(1, 60, "in", y=5, x=10, lean=8, an=50, rn=0.9, wa=40, fn=26, ff=-8, af=120, ta=150, act=1),
            K(1, 70, "out", y=3, x=11, lean=2, tilt=-2, an=10, rn=0.86, wa=-30, sm=1),
            K(2, 240, "out", hold=120, y=2, x=11, lean=0, an=-10, rn=0.8, wa=-48, af=130, ta=130),
            back_to(IDLE1, 11, n=3, ms=380),
        ]

    @anim("combo", [1])
    def combo(ph):
        # three blows: a quick downward forehand, the beak ripped back up, then a held overhead that falls late
        return [
            K(1, 90, **IDLE1),
            K(2, 200, "out", lean=-4, tilt=5, an=-75, rn=0.72, hn=None, wa=250, wbelow=6, wabove=34, fn=11, ff=-8, af=120, ta=125, lift_n=0.8, tel=True),
            K(1, 60, "in", lean=12, x=6, an=-10, rn=0.92, wa=345, fn=20, sm=1),
            K(1, 60, "in", lean=18, x=9, y=4, an=45, rn=0.86, wa=410, fn=24, lift_n=0.1, act=1),
            K(2, 170, "out", lean=16, x=9, y=4, an=55, rn=0.84, wa=425, wflip=-1),
            K(1, 70, "in", lean=4, x=12, y=1, an=5, rn=0.9, wa=330, fn=27, ff=-4, act=2),
            K(1, 60, "out", lean=-4, x=12, y=-1, an=-55, rn=0.86, wa=260, lift_n=0.8, act=2),
            K(2, 200, "out", hold=320, lean=-10, tilt=8, x=12, y=0, an=-112, rn=0.82, wa=205, wflip=1, lift_n=1.0, af=135, ta=140,
              topen=6, tel=True, eyes=0.85),
            K(1, 70, "in", lean=12, x=20, y=3, an=-58, rn=0.92, wa=300, fn=40, ff=-2, sm=1),
            K(1, 60, "in", lean=24, tilt=-6, x=26, y=7, an=38, rn=0.86, wa=422, gnd=1, fn=46, ff=-4, lift_n=0, af=168, ta=176, topen=7,
              act=3, ev="land", fx=[("sparks", None, None, 26, -90, 150, 16), ("ring", None, 20, 1.0)]),
            K(2, 240, "out", hold=120, lean=21, x=27, y=7.5, an=44, rn=0.85, wa=424, gnd=1, eyes=0.7),
            K(2, 260, "io", lean=10, x=27, y=2, an=20, rn=0.75, wa=330, gnd=0, fn=40, ff=14, af=120, ta=110, topen=4),
            back_to(IDLE1, 27, n=2, ms=300),
        ]

    @anim("grab", [1])
    def grab(ph):
        # the tongs: opened low and drawn back (the glint is on the jaws), a long lunge, the jaws snap shut
        return [
            K(1, 90, **IDLE1),
            K(2, 230, "out", y=3, lean=8, tilt=3, an=105, rn=0.85, hn=None, wa=118, fn=12, ff=-11, af=150, rf=0.72, ta=175, topen=9, mf="fist"),
            K(1, 120, "out", hold=200, y=4, lean=10, af=165, rf=0.8, ta=185, tel="tong", eyes=0.85),
            K(1, 75, "in", y=8, x=16, lean=24, tilt=-2, fn=34, ff=-9, af=50, rf=0.97, ta=36, topen=9, an=120, wa=130, act=1, hw="tong", ev="lunge"),
            K(1, 65, "out", y=8, x=18, lean=25, af=48, rf=0.97, ta=34, topen=0.5, act=1),
            K(2, 260, "out", hold=160, y=2, x=18, lean=12, af=30, rf=0.85, ta=40, topen=1, hw=None),
            back_to(IDLE1, 18, n=2, ms=320),
        ]

    @anim("grabhold", [1])
    def grabhold(ph):
        # caught: lifted in the shut jaws, the hammer raised over you and brought down twice, then flung away
        S = dict(y=8, x=18, lean=25, af=48, rf=0.97, ta=34, topen=0.5, an=120, rn=0.85, wa=130, fn=34, ff=-9, tilt=-2)
        return [
            K(1, 80, **S),
            K(2, 240, "out", y=0, lean=4, tilt=4, af=-28, rf=0.85, ta=-40, an=-110, rn=0.82, wa=205, lift_n=1.0, lift_f=0.6, fn=30, ff=-4),
            K(1, 100, "out", hold=120, lean=0, af=-34, ta=-46, an=-118, wa=200, tel=True, eyes=0.9),
            K(1, 70, "in", lean=12, an=-20, rn=0.92, wa=320, lift_n=0.4, sm=1, ev="strike1", fx=[("burst", 12, 10, "tong")]),
            K(2, 220, "out", lean=2, an=-100, rn=0.8, wa=212, lift_n=1.0),
            K(1, 70, "in", lean=14, an=-12, rn=0.94, wa=326, lift_n=0.3, sm=1, ev="strike2", fx=[("burst", 18, 13, "tong")]),
            K(2, 160, "out", lean=6, af=-8, rf=0.97, ta=-18, topen=9, an=40, rn=0.8, wa=60, ev="throw"),
            K(2, 240, "out", lean=10, af=20, rf=0.85, ta=20, topen=6),
            back_to(IDLE1, 18, n=2, ms=320),
        ]

    @anim("snap", [1])
    def snap(ph):
        # a short, quick pinch of the tongs at close range (parryable)
        return [
            K(1, 80, **IDLE1),
            K(1, 120, "out", hold=90, lean=-2, tilt=3, af=135, rf=0.7, ta=100, topen=8, hn=None, an=100, rn=0.86, wa=110, tel="tong"),
            K(1, 55, "in", x=7, y=7, lean=20, fn=18, af=56, rf=0.95, ta=46, topen=8, act=1, hw="tong"),
            K(1, 60, "out", x=8, y=8, lean=22, af=55, rf=0.96, ta=44, topen=0.5, act=1),
            K(2, 200, "out", hold=80, x=8, lean=8, af=40, rf=0.85, ta=40, topen=1, hw=None),
            back_to(IDLE1, 8, n=2, ms=260),
        ]

    @anim("ring", [1])
    def ring(ph):
        # the hammer stood on its handle and driven straight down: the floor rings, and the ring runs both ways
        return [
            K(1, 80, **IDLE1),
            K(2, 240, "out", y=-1, lean=-3, tilt=5, an=-25, rn=0.5, hn=None, wa=-92, fn=10, ff=-8, af=125, ta=130, lift_n=0.5),
            K(1, 140, "out", hold=200, y=-2, lean=-5, an=-40, rn=0.55, wa=-94, lift_n=0.7, tel=True, eyes=0.85),
            K(1, 60, "in", y=4, lean=12, x=3, an=62, rn=0.78, wa=90, gnd=1, fn=14, lift_n=0, act=1, ev="ring",
              fx=[("sparks", None, None, 22, -90, 170, 12), ("ring", None, 30, 1.0)]),
            K(2, 260, "out", hold=200, y=5, lean=14, x=3, an=64, rn=0.78, wa=90, gnd=1, fx=[("ring", None, 18, 0.6)]),
            back_to(IDLE1, 3, n=2, ms=320, gnd=0),
        ]

    @anim("leap", [1])
    def leap(ph):
        # crouch, spring (the code lifts him and carries him to you), the hammer raised at the top, brought down
        # as he lands -- a slam that shakes the floor
        return [
            K(1, 80, **IDLE1),
            K(2, 240, "out", hold=140, y=9, lean=14, tilt=4, fn=12, ff=-12, an=140, rn=0.8, hn=None, wa=150, af=140, ta=150, tel=True, eyes=0.85),
            K(1, 70, "in", y=-3, lean=6, fn=10, ff=-8, fnl=8, ffl=3, an=-60, rn=0.8, wa=240, lift_n=0.8, ev="takeoff"),
            K(2, 200, "out", y=-4, lean=-6, tilt=6, fn=16, ff=-4, fnl=13, ffl=9, an=-115, rn=0.82, wa=203, lift_n=1.0, af=130, ta=140, topen=6, ev="apex"),
            K(1, 90, "in", y=-1, lean=10, fn=22, ff=-6, fnl=7, ffl=5, an=-45, rn=0.9, wa=300, lift_n=0.6, sm=1, ev="fall"),
            K(1, 60, "in", y=7, x=17, lean=24, tilt=-6, fn=37, ff=-14, fnl=0, ffl=0, an=38, rn=0.86, wa=422, gnd=1, lift_n=0, af=168, ta=176,
              act=1, ev="land", fx=[("sparks", None, None, 30, -90, 160, 18), ("ring", None, 28, 1.0)]),
            K(2, 240, "out", hold=150, y=7.5, x=18, lean=21, an=44, rn=0.85, wa=424, gnd=1),
            K(2, 280, "io", y=2, x=18, lean=10, an=20, rn=0.75, wa=330, gnd=0, fn=30, ff=4, af=120, ta=110, topen=4),
            back_to(IDLE1, 18, n=2, ms=300),
        ]

    @anim("sparks", [1])
    def sparks(ph):
        # the hammer held out flat, the tongs swung down across its face: a fan of sparks flies at you
        return [
            K(1, 80, **IDLE1),
            K(2, 250, "out", lean=-2, tilt=4, an=0, rn=0.62, hn=None, wa=-6, wflip=-1, af=-120, rf=0.8, ta=-110, topen=2, lift_f=0.9),
            K(1, 130, "out", hold=180, lean=-5, af=-135, rf=0.85, ta=-125, tel=True, eyes=0.85),
            K(1, 70, "in", lean=8, x=3, an=4, af=-10, rf=0.92, ta=10, lift_f=0.3, sm=1, hw="tong", ev="sparks", fx=[("burst", 22, 16, "head")]),
            K(2, 200, "out", hold=140, lean=10, x=3, an=10, af=35, rf=0.85, ta=60, hw=None),
            back_to(IDLE1, 3, n=2, ms=320),
        ]

    @anim("backhand", [1])
    def backhand(ph):
        # you are behind him: the hammer is ripped back over his shoulder, beak first, and down behind him
        return [
            K(1, 70, **IDLE1),
            K(1, 120, "out", hold=90, lean=6, tilt=-4, an=-30, rn=0.6, hn=None, wa=-62, wflip=-1, af=80, ta=80, tel=True, eyes=0.85),
            K(1, 60, "in", lean=-12, tilt=-8, x=-3, ff=-16, an=-150, rn=0.86, wa=200, lift_n=1.0, sm=1),
            K(1, 60, "in", lean=-10, x=-5, y=5, ff=-20, an=150, rn=0.92, wa=112, lift_n=0.2, act=1),
            K(2, 240, "out", hold=110, lean=-14, x=-5, an=150, rn=0.86, wa=126, lift_n=0.1),
            back_to(IDLE1, -5, n=3, ms=360),
        ]

    @anim("temper", [1])
    def temper(ph):
        # tempering: down on one knee, the hammer's head driven into the coals (the channel loops loop0..loop1, and
        # can be broken); it comes up glowing
        KN = dict(y=12, lean=17, tilt=8, fn=13, ff=-21, an=62, rn=0.78, hn=None, wa=84, gnd=1, af=78, rf=0.8, ta=82, topen=2)
        return [
            K(1, 80, **IDLE1),
            K(2, 280, "out", **KN),
            K(2, 320, "io", y=12.5, lean=18, tilt=10, eyes=0.95, wheat=0.4, ev="loop0", fx=[("coals", 92, 116, 6, 6), ("embers", 84, 60, 118, 120, 6)]),
            K(2, 320, "io", y=11.5, lean=15, tilt=7, eyes=0.75, wheat=0.6, ev="loop1", fx=[("coals", 90, 118, 7, 9), ("embers", 84, 60, 118, 120, 6)]),
            K(2, 260, "out", y=2, lean=0, tilt=2, fn=10, ff=-9, an=-12, rn=0.6, wa=-88, gnd=0, wheat=1.0, af=105, ta=100, eyes=1.0,
              ev="tempered", fx=[("burst", 18, 12, "head")]),
            K(1, 180, "out", hold=140, wheat=1.0, an=-16, wa=-90),
            back_to(IDLE1, 0, n=3, ms=380, wheat=0.5),
        ]

    @anim("stagger", [1])
    def stagger(ph):
        return [
            K(1, 90, x=-3, y=-1, lean=-12, tilt=-10, an=110, rn=0.9, hn=None, wa=128, af=140, rf=0.85, ta=150, eyes=0.3, fn=8, ff=-10),
            K(2, 200, "out", x=-8, y=3, lean=-6, tilt=-4, fn=2, ff=-20, an=95, wa=118),
            K(2, 260, "io", x=-8, y=13, lean=20, tilt=24, fn=6, ff=-24, an=72, rn=0.8, wa=88, gnd=1, af=100, ta=96, eyes=0.2, ev="kneel"),
            K(2, 420, "io", x=-8, y=13.5, lean=21, tilt=26, eyes=0.15),
            K(2, 280, "out", x=-8, y=4, lean=6, tilt=6, fn=0, ff=-17, eyes=0.5, gnd=0),
            back_to(IDLE1, -8, n=2, ms=260),
        ]

    @anim("intro", [1])
    def intro(ph):
        # dormant: knelt by the fire, head bowed, the eye-light out.  He rises, the eye kindles, the hammer comes up.
        KN = dict(IDLE1, y=13, lean=19, tilt=26, fn=13, ff=-21, hn=None, an=64, rn=0.8, wa=86, gnd=1, af=100, rf=0.8, ta=96, eyes=0.0)
        return [
            K(1, 600, **KN),
            K(2, 400, "io", eyes=0.0, y=12, lean=16, tilt=18),
            K(2, 360, "out", y=4, lean=6, tilt=4, fn=11, ff=-11, eyes=0.15),
            K(1, 120, "out", hold=200, eyes=1.0, ev="ignite", fx=[("embers", 92, 40, 112, 60, 5)]),
            K(2, 320, "out", y=-1, lean=-3, an=-30, rn=0.55, wa=-90, gnd=0, lift_n=0.6),
            K(1, 90, "in", y=2, lean=6, an=58, rn=0.82, wa=90, gnd=1, lift_n=0, ev="plant", fx=[("sparks", None, None, 14, -90, 160, 9)]),
            back_to(IDLE1, 0, n=2, ms=300, gnd=0, eyes=0.6),
        ]

    @anim("p2shift", [1])
    def p2shift(ph):
        # the change: both hands on the haft, the hammer driven into the coals to the collar -- and left there
        G = "keep"
        return [
            K(1, 80, **IDLE1),
            K(2, 320, "out", y=-1, lean=-6, tilt=6, an=-95, rn=0.62, hn=None, wa=-92, two=1, tw=10, two_front=True, lift_n=1, lift_f=1, fn=11, ff=-9),
            K(1, 200, "out", hold=380, y=-2, lean=-9, an=-100, rn=0.7, tel=True, eyes=0.9),
            K(1, 70, "in", y=9, lean=20, tilt=-4, x=6, fn=22, ff=-12, an=58, rn=0.82, wa=90, gnd=1, lift_n=0, lift_f=0, ev="impact",
              fx=[("sparks", None, None, 34, -90, 170, 20), ("ring", None, 34, 1.0), ("coals", 80, 150, 12, 10)]),
            K(2, 300, "out", hold=300, y=10, lean=22, tilt=8, wheat=0.5),
            K(2, 320, "io", y=6, lean=12, wfree=G, an=80, rn=0.75, mn="claw", two=0, two_front=False, af=100, mf="claw", tongs_far=False, wheat=0.7),
            K(3, 420, "io", **dict(x=6, y=1, lean=8, tilt=6, fn=16, ff=-3, an=72, rn=0.8, af=105, rf=0.8, eyes=0.9, wheat=0.8), ev="free"),
        ]

    # ------------------------------------------------------------------------------------------------ P2 THE ARSENAL
    IDLE2 = dict(x=0, y=1.5, lean=9, tilt=6, fn=10, ff=-9, an=74, rn=0.78, af=110, rf=0.78, wind=1.5, weapon=None, mn="claw", mf="claw")
    G_BLADE = dict(IDLE2, y=2, lean=8, tilt=3, fn=14, ff=-10, an=48, rn=0.74, weapon="blade", mn="fist", wa=-38, af=125, rf=0.75)
    G_SPEAR = dict(IDLE2, y=4, lean=10, tilt=2, fn=16, ff=-10, an=42, rn=0.72, weapon="spear", mn="fist", wa=16, wbelow=18, two=1, tw=15,
                   mf="fist", spear_front=False)
    G_CHAIN = dict(IDLE2, y=2, lean=8, tilt=3, fn=13, ff=-10, an=52, rn=0.72, weapon="chain", mn="fist", ca=118, cl=36, cb=-5, cs=4)

    def loop_idle(base, n=6, ms=170, sway=1.0, **extra):
        import math
        ks = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            k = dict(base, y=base.get("y", 0) - 0.8 * math.sin(a), lean=base["lean"] + 0.7 * sway * math.sin(a),
                     tilt=base["tilt"] - 1.0 * math.sin(a - 0.6), an=base["an"] + 2.5 * sway * math.sin(a - 0.4),
                     af=base["af"] + 2 * sway * math.sin(a - 0.9), spread_n=1 + 0.25 * math.sin(a), spread_f=1 + 0.25 * math.sin(a + 1))
            for kk, (amp, ph) in extra.items():
                k[kk] = base[kk] + amp * math.sin(a + ph)
            ks.append(K(1, ms, "io", **k))
        return ks

    def loop_walk(base, S=11.0, ms=115, swing=10):
        b = dict(base)
        b["wind"] = b.get("wind", 0) + 1.0
        a0, f0 = base["an"], base["af"]
        return [K(1, ms, **dict(b, y=b["y"] + 1.4, fn=S, ff=-S, lock="n", af=f0 + swing, an=a0 - swing * 0.6)),
                K(1, ms, "out", **dict(b, y=b["y"] + 0.2, fn=S * 0.5, ff=-S * 0.3, ffl=3.5, lock="n", af=f0 + swing * 0.5, an=a0 - swing * 0.3)),
                K(1, ms, "io", **dict(b, y=b["y"] - 0.6, fn=0, ff=S * 0.4, ffl=4.0, lock="n", af=f0, an=a0)),
                K(1, ms, "in", **dict(b, y=b["y"] + 0.2, fn=-S * 0.5, ff=S * 0.85, ffl=1.5, lock="n", af=f0 - swing * 0.5, an=a0 + swing * 0.3)),
                K(1, ms, **dict(b, y=b["y"] + 1.4, fn=-S, ff=S, ffl=0, lock="f", af=f0 - swing, an=a0 + swing * 0.6)),
                K(1, ms, "out", **dict(b, y=b["y"] + 0.2, fn=-S * 0.3, ff=S * 0.5, fnl=3.5, lock="f", af=f0 - swing * 0.5, an=a0 + swing * 0.3)),
                K(1, ms, "io", **dict(b, y=b["y"] - 0.6, fn=S * 0.4, ff=0, fnl=4.0, lock="f", af=f0, an=a0)),
                K(1, ms, "in", **dict(b, y=b["y"] + 0.2, fn=S * 0.85, ff=-S * 0.5, fnl=1.5, lock="f", af=f0 + swing * 0.5, an=a0 - swing * 0.3)),
                K(1, ms, **dict(b, y=b["y"] + 1.4, fn=S, ff=-S, fnl=0, lock="n", af=f0 + swing, an=a0 - swing * 0.6))]

    def stagger_of(base, weapon_keep=None):
        return [
            K(1, 90, **dict(base, x=-3, y=-1, lean=-12, tilt=-10, an=110, rn=0.9, af=140, rf=0.85, eyes=0.3, fn=8, ff=-10)),
            K(2, 200, "out", x=-8, y=3, lean=-6, tilt=-4, fn=2, ff=-20, an=95),
            K(2, 260, "io", x=-8, y=13, lean=20, tilt=24, fn=6, ff=-24, an=82, rn=0.75, af=96, eyes=0.2, ev="kneel"),
            K(2, 420, "io", x=-8, y=13.5, lean=21, tilt=26, eyes=0.15),
            K(2, 280, "out", x=-8, y=4, lean=6, tilt=6, fn=0, ff=-17, eyes=0.5),
            back_to(base, -8, n=2, ms=260),
        ]

    @anim("idle", [2], loop=True)
    def idle2(ph):
        return loop_idle(IDLE2, sway=1.4)

    @anim("walk", [2], loop=True)
    def walk2(ph):
        return loop_walk(dict(IDLE2, lean=11, tilt=2, an=80, af=100), swing=14)

    @anim("stagger", [2])
    def stagger2(ph):
        return stagger_of(IDLE2)

    def draw_from_coals(guard, weapon, grip_wa, rise_wa, ev_fx):
        """kneel, the hand into the coals, a weapon ripped up glowing (a flare and a spray of coals), into its guard"""
        return [
            K(1, 80, **IDLE2),
            K(2, 240, "out", y=11, lean=24, tilt=12, fn=14, ff=-14, hn=(30, -8), mn="claw", af=130, rf=0.8),
            K(1, 120, "out", hold=150, y=12, lean=25, tilt=12, weapon=weapon, mn="fist", wa=grip_wa, hn=(31, -7), wheat=1.0,
              tel=True, fx=[("coals", 98, 124, 8, 4)]),
            K(2, 200, "in", y=3, lean=6, tilt=2, wa=rise_wa, hn=None, an=-30, rn=0.8, fn=14, ff=-10, ev="draw",
              fx=ev_fx),
            back_to(guard, 0, n=2, ms=240, e="out"),
        ]

    @anim("draw_blade", [2])
    def draw_blade(ph):
        return draw_from_coals(G_BLADE, "blade", 96, -70, [("coals", 90, 140, 14, 22), ("flare", 120, 70, 10)])

    @anim("bl_rising", [2])
    def bl_rising(ph):
        # the concept's rising cut: the blade trails low behind him (glint), then rips up through you, and its heat
        # runs on along the floor
        return [
            K(1, 80, **G_BLADE),
            K(2, 230, "out", hold=150, y=6, lean=16, tilt=4, an=135, rn=0.85, wa=165, ff=-14, af=60, rf=0.75, tel=True, eyes=1.0),
            K(1, 60, "in", y=5, x=8, lean=14, an=75, rn=0.92, wa=72, fn=26, act=1),
            K(1, 60, "in", y=1, x=14, lean=-2, tilt=-4, an=-18, rn=0.95, wa=-40, fn=32, ff=-8, af=140, act=1, ev="rise",
              fx=[("coals", 110, 150, 8, 6)]),
            K(2, 220, "out", hold=100, y=0, x=14, lean=-6, an=-58, rn=0.92, wa=-76),
            back_to(G_BLADE, 14, n=2, ms=280),
        ]

    @anim("bl_cleave", [2])
    def bl_cleave(ph):
        # two cuts: a long diagonal down across you, then ripped back up the other way
        return [
            K(1, 80, **G_BLADE),
            K(2, 210, "out", hold=120, y=0, lean=-6, tilt=6, an=-120, rn=0.8, wa=192, lift_n=1, af=60, rf=0.7, tel=True),
            K(1, 60, "in", x=8, lean=10, an=-20, rn=0.92, wa=330, fn=26, lift_n=0.5, sm=1),
            K(1, 60, "in", x=12, y=5, lean=20, an=48, rn=0.9, wa=428, fn=30, lift_n=0, act=1),
            K(2, 170, "out", hold=90, x=12, y=6, lean=20, an=60, rn=0.86, wa=440, tel=True),
            K(1, 60, "in", x=16, y=2, lean=4, an=-12, rn=0.95, wa=330, fn=34, ff=-6, act=2),
            K(1, 60, "out", x=16, y=0, lean=-6, an=-60, rn=0.92, wa=262, lift_n=0.8, act=2),
            K(2, 220, "out", hold=100, x=16, lean=-8, an=-80, rn=0.88, wa=245),
            back_to(G_BLADE, 16, n=2, ms=300, lift_n=0),
        ]

    @anim("bl_charge", [2])
    def bl_charge(ph):
        # both hands, the blade raised straight up and held while it whitens (the long tell); one chop that splits the
        # floor and sends the heat running on
        return [
            K(1, 80, **G_BLADE),
            K(2, 260, "out", y=-1, lean=-6, tilt=5, an=-98, rn=0.7, wa=-94, two=1, tw=8, two_front=True, lift_n=1, lift_f=1, fn=12, ff=-9),
            K(2, 420, "io", hold=260, y=-2, lean=-8, tilt=8, wheat=1.0, tel=True, ev="charge", fx=[("flare", None, None, 8)]),
            K(1, 70, "in", y=2, x=8, lean=10, an=-30, rn=0.86, wa=330, fn=24, sm=1),
            K(1, 60, "in", y=8, x=14, lean=24, tilt=-6, an=52, rn=0.88, wa=430, fn=36, ff=-12, lift_n=0, lift_f=0, act=1, ev="chop",
              fx=[("sparks", None, None, 24, -90, 160, 16), ("ring", None, 26, 1.0)]),
            K(2, 280, "out", hold=220, y=9, x=14, lean=24, an=56, wa=434),
            back_to(G_BLADE, 14, n=3, ms=360, two=0, two_front=False),
        ]

    def drop_of(guard, toss_an, toss_wa):
        return [
            K(1, 80, **guard),
            K(2, 220, "out", lean=2, an=toss_an, rn=0.85, wa=toss_wa, ca=150, cl=30),
            K(1, 60, "in", lean=6, an=toss_an + 20, rn=0.9, weapon=None, mn="claw", two=0, two_front=False, mf="claw", ev="drop",
              fx=[("steam", 50, 125, 8)]),
            back_to(IDLE2, 0, n=3, ms=360),
        ]

    @anim("drop_blade", [2])
    def drop_blade(ph):
        return drop_of(G_BLADE, 130, 150)

    @anim("draw_spear", [2])
    def draw_spear(ph):
        return draw_from_coals(G_SPEAR, "spear", 92, -92, [("coals", 90, 140, 14, 22), ("flare", 110, 40, 9)])

    @anim("sp_thrust", [2])
    def sp_thrust(ph):
        # three thrusts, telegraphed like a spear's: drawn to the hip, a short jab, a higher jab, a held breath, a long lunge
        return [
            K(1, 80, **G_SPEAR),
            K(1, 150, "out", hold=90, x=-3, y=5, lean=6, an=100, rn=0.45, wa=18, tel=True),
            K(1, 55, "in", x=8, y=10, lean=22, an=50, rn=0.95, wa=29, fn=26, act=1),
            K(1, 110, "out", x=5, y=7, lean=12, an=95, rn=0.5, wa=16),
            K(1, 55, "in", x=10, y=11, lean=22, an=52, rn=0.95, wa=27, fn=28, act=2),
            K(1, 120, "out", hold=150, x=6, y=8, lean=8, an=105, rn=0.42, wa=20, fn=22, ff=-12, tel=True),
            K(1, 60, "in", x=24, y=12, lean=26, an=48, rn=1.0, wa=24, fn=44, ff=-6, act=3),
            K(2, 260, "out", hold=120, x=25, y=12, lean=24, an=50, rn=0.98, wa=26),
            back_to(G_SPEAR, 25, n=2, ms=300),
        ]

    @anim("sp_lunge", [2])
    def sp_lunge(ph):
        # crouched behind the levelled point (the glint), then the dash: the code carries him across the floor on the
        # 'dash' frame; a skid, and he rises
        return [
            K(1, 80, **G_SPEAR),
            K(2, 260, "out", hold=220, y=11, lean=24, tilt=-4, an=60, rn=0.7, wa=22, fn=20, ff=-16, tel=True, eyes=1.0, ev="aim"),
            K(1, 70, "in", y=12, x=10, lean=30, an=50, rn=0.98, wa=24, fn=36, ff=-16, ffl=3, act=1, ev="dash"),
            K(2, 260, "out", y=6, x=10, lean=4, an=50, rn=0.8, wa=14, fn=32, ff=-4, ffl=0, fx=[("dust", 100, 10, 30)], ev="skid"),
            back_to(G_SPEAR, 10, n=2, ms=300),
        ]

    @anim("sp_hurl", [2])
    def sp_hurl(ph):
        # the javelin: raised over the shoulder, the other hand points at you (the tell), thrown -- he is left empty-handed
        return [
            K(1, 80, **G_SPEAR),
            K(2, 260, "out", hold=240, y=0, lean=-8, tilt=4, an=-150, rn=0.75, wa=-10, two=0, two_front=False, wbelow=22, lift_n=1,
              af=-8, rf=0.95, mf="open", fn=14, ff=-12, tel=True, eyes=1.0),
            K(1, 70, "in", x=6, lean=14, an=-20, rn=0.95, wa=-6, lift_n=0.4, af=120, rf=0.8, mf="claw", fn=24, ev="throw"),
            K(2, 220, "out", x=6, lean=16, an=20, rn=0.95, weapon=None, mn="open"),
            back_to(IDLE2, 6, n=3, ms=360),
        ]

    @anim("draw_chain", [2])
    def draw_chain(ph):
        return [
            K(1, 80, **IDLE2),
            K(2, 240, "out", y=11, lean=24, tilt=12, fn=14, ff=-14, hn=(30, -8), mn="claw", af=130, rf=0.8),
            K(1, 120, "out", hold=150, y=12, lean=25, weapon="chain", mn="fist", hn=(31, -7), ca=88, cl=10, cs=0, cb=0, tel=True,
              fx=[("coals", 98, 124, 8, 4)]),
            K(2, 220, "in", y=2, lean=4, tilt=2, hn=None, an=-50, rn=0.8, ca=96, cl=40, cs=4, cb=6, ev="draw",
              fx=[("coals", 92, 140, 14, 20), ("flare", 112, 100, 8)]),
            back_to(G_CHAIN, 0, n=2, ms=260, e="out"),
        ]

    @anim("ch_lash", [2])
    def ch_lash(ph):
        # the chain swung up behind and cracked down at length: the hooked weight is the dangerous end
        return [
            K(1, 80, **G_CHAIN),
            K(2, 240, "out", hold=160, lean=-6, tilt=6, an=-130, rn=0.82, ca=205, cl=40, cb=12, cs=0, lift_n=1, tel=True),
            K(1, 60, "in", x=4, lean=4, an=-50, rn=0.9, ca=280, cl=52, cb=14, sm=1),
            K(1, 60, "in", x=7, lean=14, an=12, rn=0.95, ca=8, cl=74, cb=-5, lift_n=0.2, act=1, ev="crack",
              fx=[("burst", 10, 8, "head")]),
            K(1, 70, "out", x=7, lean=14, ca=26, cl=72, cb=8, cs=6, act=1),
            K(2, 220, "out", hold=100, x=7, lean=10, an=30, ca=18, cl=68, cb=2, cs=12),
            back_to(G_CHAIN, 7, n=3, ms=360),
        ]

    @anim("ch_sweep", [2])
    def ch_sweep(ph):
        # whirled round twice beside him, low and wide: the arc reaches the floor in front and behind
        return [
            K(1, 80, **G_CHAIN),
            K(2, 220, "out", y=-1, lean=-2, an=-15, rn=0.6, ca=100, cl=44, cb=0, cs=2, tel=True),
            K(2, 240, "in", lean=0, ca=250, cl=60, cb=8, cs=0, sm=1),
            K(3, 270, "lin", ca=430, cl=64, cb=10, act=1),
            K(3, 270, "lin", ca=610, cl=64, cb=10, act=1),
            K(3, 270, "lin", ca=790, cl=64, cb=10, act=1),
            K(2, 300, "out", ca=840, cl=50, cb=4, cs=6),
            back_to(G_CHAIN, 0, n=2, ms=280, ca=838),
        ]

    @anim("ch_hook", [2])
    def ch_hook(ph):
        # the hooked weight thrown low along the floor; if it bites, it hauls you in to a hot backhand
        return [
            K(1, 80, **G_CHAIN),
            K(1, 200, "out", hold=150, y=3, lean=4, an=150, rn=0.7, ca=170, cl=22, cb=-6, cs=2, tel=True),
            K(1, 70, "in", y=4, x=4, lean=16, an=12, rn=0.95, ca=6, cl=92, cb=0, cs=0, fn=22, act=1, ev="hook"),
            K(1, 80, "out", y=4, x=4, lean=16, ca=7, cl=102, cs=3, act=1),
            K(2, 200, "out", y=2, x=4, lean=-4, an=125, rn=0.7, ca=20, cl=38, cs=6, ev="yank"),
            K(1, 70, "in", y=8, x=10, lean=22, an=40, rn=0.95, ca=78, cl=34, cs=2, fn=26, act=2),
            K(2, 240, "out", hold=100, x=10, lean=10, an=10, rn=0.9),
            back_to(G_CHAIN, 10, n=2, ms=300),
        ]

    @anim("drop_chain", [2])
    def drop_chain(ph):
        return drop_of(G_CHAIN, 120, 120)

    @anim("coal_kick", [2])
    def coal_kick(ph):
        # empty-handed: one foot raked back through the coals and kicked through them -- the coals fly at you
        return [
            K(1, 80, **IDLE2),
            K(2, 220, "out", hold=140, lean=-4, tilt=4, fn=-6, fnl=5, an=40, rn=0.8, af=160, rf=0.8, tel="hand"),
            K(1, 60, "in", lean=-10, fn=30, fnl=9, an=100, af=130, ev="kick", fx=[("coals", 96, 150, 16, 18)]),
            K(2, 220, "out", lean=2, fn=24, fnl=0),
            back_to(IDLE2, 0, n=2, ms=300),
        ]

    @anim("temper", [2])
    def temper2(ph):
        KN = dict(y=12, lean=20, tilt=10, fn=13, ff=-21, hn=(30, -6), hf=(14, -6), mn="claw", mf="claw")
        return [
            K(1, 80, **IDLE2),
            K(2, 280, "out", **KN),
            K(2, 320, "io", y=12.5, lean=21, tilt=12, eyes=1.0, ev="loop0", fx=[("coals", 86, 118, 7, 7), ("embers", 84, 60, 118, 120, 6)]),
            K(2, 320, "io", y=11.5, lean=18, tilt=9, eyes=0.8, ev="loop1", fx=[("coals", 86, 120, 7, 9), ("embers", 84, 60, 118, 120, 6)]),
            K(2, 260, "out", y=1, lean=2, tilt=0, hn=None, an=-60, rn=0.7, af=-120, rf=0.75, eyes=1.0, crown=0.8, ev="tempered",
              fx=[("flare", 106, 42, 10)]),
            back_to(IDLE2, 0, n=3, ms=380),
        ]

    @anim("p3shift", [2])
    def p3shift(ph):
        # the last fire: down into the coals with both hands; the tongs come up holding the white coal, and the forge's
        # light goes into him
        KN = dict(y=12, lean=22, tilt=12, fn=13, ff=-21, hn=(28, -6), hf=(16, -6), mn="claw", mf="claw")
        I3 = dict(IDLE2, weapon="ftongs", mn="fist", an=4, rn=0.6, wa=-52, tilt=-3, lean=4, y=0, eyes=1.0, fire=0.55, crown=0.8, chest=0.6, coal=1.0)
        return [
            K(1, 80, **IDLE2),
            K(2, 300, "out", **KN),
            K(2, 500, "io", hold=300, y=12.5, eyes=1.0, crown=0.6, ev="kneel", fx=[("coals", 86, 120, 8, 8)]),
            K(1, 120, "out", hold=200, weapon="ftongs", mn="fist", hn=(29, -6), wa=92, coal=0.6, fire=0.2, ev="lift",
              fx=[("flare", 109, 132, 12), ("coals", 90, 130, 12, 14)]),
            K(3, 520, "out", **dict(I3, hn=None), ev="kindle", fx=[("embers", 70, 30, 130, 120, 10)]),
            K(1, 200, "io", **I3),
        ]

    # ------------------------------------------------------------------------------------------------ P3 THE LAST FIRE
    IDLE3 = dict(x=0, y=0, lean=4, tilt=-3, fn=10, ff=-9, an=4, rn=0.6, wa=-52, af=112, rf=0.78, mf="claw", mn="fist", wind=2.0)

    @anim("idle", [3], loop=True)
    def idle3(ph):
        return loop_idle(IDLE3, sway=1.0, wa=(4, 0.5))

    @anim("walk", [3], loop=True)
    def walk3(ph):
        return loop_walk(dict(IDLE3, lean=8, an=10, af=104), swing=12)

    @anim("stagger", [3])
    def stagger3(ph):
        return stagger_of(IDLE3)

    @anim("ft_sweep", [3])
    def ft_sweep(ph):
        # the concept's last pose: the coal raised high in the tongs (the light climbs: that is the tell), then a
        # crescent of fire sweeps down before him and runs on along the floor
        return [
            K(1, 80, **IDLE3),
            K(2, 260, "out", hold=240, y=-1, lean=-6, tilt=-8, an=-96, rn=0.92, wa=-82, lift_n=1, af=130, tel=True),
            K(1, 70, "in", x=4, lean=6, an=-30, rn=0.95, wa=320, lift_n=0.6, sm=1),
            K(1, 60, "in", x=10, y=6, lean=20, tilt=-2, an=44, rn=0.9, wa=420, lift_n=0, fn=28, act=1, ev="sweep",
              fx=[("embers", 110, 100, 160, 136, 10)]),
            K(2, 260, "out", hold=160, x=10, y=7, lean=20, an=52, wa=432),
            back_to(IDLE3, 10, n=2, ms=320),
        ]

    @anim("ember_rain", [3])
    def ember_rain(ph):
        # the coal lifted overhead and crushed in the jaws: it bursts upward, and the embers come down in curtains
        return [
            K(1, 80, **IDLE3),
            K(2, 300, "out", y=-1, lean=-8, tilt=-16, an=-90, rn=0.95, wa=-90, lift_n=1, af=-150, rf=0.7, mf="open", tel=True),
            K(1, 110, "out", hold=240, topen=0.5, coal=1.6, ev="rain", fx=[("flare", None, None, 12), ("embers", 70, 0, 140, 50, 16)]),
            K(3, 420, "io", **dict(IDLE3, topen=4.0, coal=1.0)),
        ]

    @anim("bellows_lo", [3])
    def bellows_lo(ph):
        # crouched, the coal drawn back low -- then thrust out low: a jet of fire along the floor (jump it)
        return [
            K(1, 80, **IDLE3),
            K(2, 280, "out", hold=220, y=8, lean=-4, tilt=4, an=150, rn=0.72, wa=172, fn=14, ff=-14, af=20, rf=0.8, mf="open", tel=True),
            K(1, 70, "in", y=9, x=10, lean=18, an=24, rn=0.95, wa=10, fn=30, ff=-12, af=150, mf="claw", ev="blast",
              fx=[("flare", None, None, 10)]),
            K(3, 600, "lin", y=9.5, x=10, lean=19, an=22, wa=8, fx=[("embers", 120, 110, 200, 134, 8)]),
            back_to(IDLE3, 10, n=2, ms=320),
        ]

    @anim("bellows_hi", [3])
    def bellows_hi(ph):
        # reared up tall, the coal thrown back high -- then thrust out high: a jet of fire above the floor (stay down)
        return [
            K(1, 80, **IDLE3),
            K(2, 280, "out", hold=220, y=-3, lean=-12, tilt=-10, an=-140, rn=0.8, wa=-150, lift_n=1, af=-20, rf=0.85, mf="open", tel=True),
            K(1, 70, "in", y=-1, x=8, lean=8, an=-22, rn=0.95, wa=-14, lift_n=0.5, fn=24, af=150, mf="claw", ev="blast",
              fx=[("flare", None, None, 10)]),
            K(3, 600, "lin", y=-1, x=8, lean=9, an=-20, wa=-12, fx=[("embers", 120, 40, 200, 80, 8)]),
            back_to(IDLE3, 8, n=2, ms=320, lift_n=0),
        ]

    @anim("flame_grab", [3])
    def flame_grab(ph):
        # the bare hand opened and drawn back (the coal held close behind it lights it: the tell), a lunge to take you
        return [
            K(1, 80, **IDLE3),
            K(2, 240, "out", hold=200, y=3, lean=6, af=165, rf=0.75, mf="open", spread_f=1.6, an=60, rn=0.6, wa=-10, tel="handf"),
            K(1, 75, "in", y=14, x=28, lean=30, fn=46, ff=-3, af=70, rf=0.98, act=1, hw="handf", ev="lunge"),
            K(1, 65, "out", y=14, x=30, lean=30, af=68, fn=48, mf="claw", spread_f=0.6, act=1),
            K(2, 260, "out", hold=160, y=2, x=30, lean=12, af=40, rf=0.8, hw=None),
            back_to(IDLE3, 30, n=2, ms=320),
        ]

    @anim("fgrabhold", [3])
    def fgrabhold(ph):
        # held up by the throat; the white coal pressed to you twice; thrown down
        S = dict(IDLE3, y=14, x=30, lean=30, af=68, rf=0.98, mf="claw", spread_f=0.6, fn=48, ff=-3)
        return [
            K(1, 80, **S),
            K(2, 240, "out", y=0, lean=4, af=-30, rf=0.85, lift_f=0.7, an=-30, rn=0.6, wa=-30),
            K(1, 140, "in", an=-12, rn=0.82, wa=-10, ev="burn1", fx=[("flare", None, None, 8)]),
            K(2, 240, "out", an=30, rn=0.55, wa=-40),
            K(1, 140, "in", an=-8, rn=0.85, wa=-8, ev="burn2", fx=[("flare", None, None, 10)]),
            K(2, 200, "out", lean=14, af=30, rf=0.95, lift_f=0, mf="open", ev="throw"),
            back_to(IDLE3, 30, n=2, ms=320),
        ]

    @anim("nova", [3])
    def nova(ph):
        # the coal drawn into his chest (he folds over it, the light gathers -- the tell), then it bursts out of him
        return [
            K(1, 80, **IDLE3),
            K(2, 300, "out", hold=320, y=4, lean=14, tilt=16, an=110, rn=0.32, wa=-60, af=60, rf=0.35, coal=1.5, chest=1.0, crown=1.0, tel=True),
            K(1, 70, "in", y=-2, lean=-8, tilt=-10, an=-40, rn=0.95, wa=-40, af=-140, rf=0.95, mf="open", lift_n=0.8, lift_f=0.8, coal=1.0,
              ev="nova", fx=[("flare", None, None, 14), ("embers", 50, 30, 130, 120, 14)]),
            K(2, 300, "out", hold=200, y=-1, lean=-6, chest=0.8),
            back_to(IDLE3, 0, n=2, ms=340, lift_n=0, lift_f=0),
        ]

    @anim("ft_combo", [3])
    def ft_combo(ph):
        # three fast blows with the flame tongs: down, back up, and a thrust of the coal at your face
        return [
            K(1, 70, **IDLE3),
            K(1, 150, "out", hold=60, lean=-4, an=-80, rn=0.8, wa=270, lift_n=1, tel=True),
            K(1, 55, "in", x=6, lean=14, y=4, an=40, rn=0.92, wa=420, lift_n=0, fn=24, act=1),
            K(1, 90, "out", x=7, lean=14, y=4, an=50, wa=430),
            K(1, 55, "in", x=10, lean=-2, y=0, an=-40, rn=0.92, wa=290, fn=28, lift_n=0.8, act=2),
            K(1, 120, "out", hold=80, x=10, lean=0, an=100, rn=0.45, wa=-4, lift_n=0, tel=True),
            K(1, 55, "in", x=18, lean=24, y=11, an=52, rn=1.0, wa=30, fn=38, ff=-6, act=3),
            K(2, 240, "out", hold=100, x=18, lean=20, y=9, an=44, rn=0.96),
            back_to(IDLE3, 18, n=2, ms=300),
        ]

    @anim("dark_lunge", [3])
    def dark_lunge(ph):
        # he folds the coal away behind him and his eye goes out (the code dims him to the dark; only the coal shows
        # where he is) -- then the lunge, eye and coal flaring together
        return [
            K(1, 80, **IDLE3),
            K(2, 300, "out", hold=300, y=7, lean=18, tilt=6, an=150, rn=0.6, wa=180, fn=16, ff=-14, eyes=0.0, chest=0.1, crown=0.2,
              fire=0.1, ev="dark", tel=True),
            K(1, 70, "in", y=5, x=24, lean=24, an=2, rn=1.0, wa=0, fn=44, ff=-10, eyes=1.0, chest=0.6, crown=0.8, fire=0.55, act=1, ev="lunge"),
            K(2, 260, "out", hold=120, y=4, x=25, lean=18),
            back_to(IDLE3, 25, n=2, ms=320),
        ]

    @anim("temper", [3])
    def temper3(ph):
        # the coal pressed into the grate of his chest; the crown bars blaze
        return [
            K(1, 80, **IDLE3),
            K(2, 280, "out", y=4, lean=12, tilt=14, an=115, rn=0.34, wa=-70, af=70, rf=0.4, coal=1.2),
            K(2, 320, "io", chest=1.0, crown=1.0, ev="loop0", fx=[("embers", 80, 50, 120, 100, 8)]),
            K(2, 320, "io", y=5, chest=0.8, ev="loop1", fx=[("embers", 80, 50, 120, 100, 8)]),
            K(2, 260, "out", y=-1, lean=-6, tilt=-12, chest=1.0, crown=1.0, fire=0.9, ev="tempered", fx=[("flare", 88, 60, 12)]),
            back_to(IDLE3, 0, n=3, ms=360),
        ]

    @anim("death", [3])
    def death(ph):
        # the fire leaves him: down to his knees, the coal falls from the tongs, the eye goes out, and he burns away
        # to ash from the crown down; the grate crown drops into the ash
        return [
            K(1, 120, **dict(IDLE3, x=-3, y=-1, lean=-12, tilt=-12, eyes=0.6)),
            K(2, 300, "out", x=-6, y=4, lean=-2, tilt=6, an=100, rn=0.85, wa=100, fn=4, ff=-18),
            K(2, 360, "io", x=-6, y=13, lean=18, tilt=26, fn=8, ff=-22, an=90, rn=0.8, wa=92, af=98, coal=0.3, eyes=0.3, fire=0.3,
              chest=0.3, crown=0.3, ev="kneel"),
            K(2, 500, "io", hold=300, y=14, lean=22, tilt=30, coal=0.0, eyes=0.0, fire=0.0, chest=0.0, crown=0.0, ev="out"),
            K(4, 900, "lin", dissolve=0.6, ev="ash"),
            K(3, 700, "out", dissolve=1.0, ev="gone"),
        ]
