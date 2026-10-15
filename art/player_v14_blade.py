"""v14 combo pass: new player tags for the blade group (registered by gen_player.py, same contract as player_v13_a.py).

register(G) returns [(tag, fn) or (tag, fn, opts)]; fn() returns [(cels, ms), ...] like the v13 tags.

Longsword (ls_, two hands on the hilt): ls_jk lifting cleave (J K), ls_rollk wheeling cut (L -> K), ls_air2 falling
crescent (air J J), ls_wheel wheel slash (J J (beat) J, two hits: behind, then in front).
Katana (kt_): kt_draw draw cut (J while sheathed), kt_jjk crescent sheathe (J J K, ends sheathed), kt_tsubame swallow
return (Iai -> J), kt_turn turning draw (focus draw -> K, starts facing away, ends sheathed).

Every attack: anticipation -> smear -> impact -> follow-through -> settle, timed to its move row (wind-up / total) in
web/src/76_mech_blade.js by tm() (frames before the hit frame = wind-up, all = total). `python3 art/player_v14_blade.py`
prints the check.
"""

G = None   # gen_player, set by register()
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


# =================================================================================================== LONGSWORD
def ls_jk():  # lifting cleave: sink with the blade trailing low behind the heel, then heave it up through the foe onto the toes
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=3, hand=(29, 31), ang=158, footB=(OX + 6, 39), flow=0.3), 70),
          (dict(dx=-2, dy=4, head_dx=-1, head_dy=1, hand=(27, 32), ang=166, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2,
                flutter=1, fx=[("glint", "tip"), ("dust", 12, 2)]), 120),
          (dict(dx=1, dy=3, hand=(33, 32), ang=118, footF=(FF[0] + 2, 39), flow=0.9, flutter=2, fx=[G.sw(w=0.35), ("dust", 26, 2)]), 50),
          (dict(dx=3, dy=0, hand=(40, 22), ang=-38, footB=(OX + 9, 38), footF=(FF[0] + 3, 39), flow=1.4, flutter=3,
                fx=[G.sw(w=0.6), ("flare", "tip", 5)]), 45),
          (dict(dx=2, dy=-2, hand=(36, 12), ang=-92, footB=(OX + 10, 37), footF=(FF[0] + 3, 38), flow=1.3, flutter=4,
                fx=[G.sw(w=0.5)]), 60),
          (dict(dx=1, dy=-1, hand=(32, 11), ang=-114, footB=(OX + 9, 38), footF=(FF[0] + 2, 39), flow=0.7, flutter=5), 150),
          (dict(dx=1, dy=0, hand=(33, 18), ang=-90, flow=0.4, flutter=6), 110)]
    return G.mseq(tm(fr, 260, 600, 3), grip=3.0)


def ls_rollk():  # wheeling cut: still coiled from the roll and facing away, pivot on the heel and cut flat back across the foe
    OX, FF = G.OX, G.FF
    ARC = dict(sq=0.4, w=0.6)
    fr = [(dict(dx=-1, dy=4, head_dy=1, hand=(30, 31), ang=162, footB=(OX + 6, 39), footF=(OX + 21, 39), flow=0.8, mirror=True), 80),
          (dict(dx=0, dy=3, hand=(34, 27), ang=-12, slen=12, footF=(FF[0] + 1, 39), flow=1.2, flutter=1, mirror=True, behind=True,
                fx=[("ring", (29, 26), 12, 160, 220, dict(sq=0.45, w=3.0))]), 70),
          (dict(dx=0, dy=2, hand=(28, 25), ang=-178, off=(34, 24), footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.9, flutter=2,
                fx=[("glint", "tip")]), 70),
          (dict(dx=3, dy=2, hand=(41, 25), ang=-3, footB=(OX + 9, 39), footF=(FF[0] + 4, 39), flow=1.5, flutter=3,
                fx=[("arc", (29, 26), 178, -3, ARC), ("speed", (18, 22), 3, 10)]), 45),
          (dict(dx=3, dy=1, hand=(40, 20), ang=-40, footB=(OX + 9, 39), footF=(FF[0] + 4, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.45)]), 60),
          (dict(dx=2, dy=1, hand=(37, 16), ang=-74, footF=(FF[0] + 3, 39), flow=0.7, flutter=5), 150),
          (dict(dx=1, hand=(35, 25), ang=-52, flow=0.3, flutter=6), 125)]
    return G.mseq(tm(fr, 240, 600, 3), grip=3.0)


def ls_air2():  # falling crescent: the blade wound up over the head, then one huge arc from overhead to below the boots
    base = dict(dy=-3, **G.TUCK)
    fr = [(dict(head_dx=-1, hand=(29, 13), ang=-128, flow=0.5), 70),
          (dict(hand=(32, 10), ang=-88, flow=0.8, flutter=1, fx=[G.sw(w=0.3)]), 40),
          (dict(dx=1, hand=(40, 22), ang=18, flow=1.3, flutter=2,
                fx=[("arc", (31, 22), -100, 18, dict(sq=1.0, w=0.5))]), 45),
          (dict(dx=1, hand=(37, 31), ang=78, slen=16, flow=1.2, flutter=3, fx=[G.sw(w=0.45), ("flare", "tip", 4)]), 55),
          (dict(hand=(35, 30), ang=62, flow=0.8, flutter=4), 70),
          (dict(hand=(35, 26), ang=-20, flow=0.5, flutter=5, **G.AIR), 90)]
    out = G.mseq(tm(fr, 150, 360, 2), base, grip=3.0)
    return G.cape_trail(out, [2, 3])


def ls_wheel():  # wheel slash: coil, spin on the spot -- the blade passes behind you (hit 1) and comes round in front (hit 2)
    OX, FF = G.OX, G.FF
    ARC = dict(sq=0.42, w=0.6)
    fr = [(dict(dx=-1, dy=2, hand=(29, 25), ang=-176, footB=(OX + 6, 39), flow=0.3), 90),
          (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=176, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                fx=[("glint", "tip")]), 110),
          # hit 1: the body has turned, the blade sweeps the side behind you
          (dict(dx=0, dy=2, hand=(40, 25), ang=-4, footF=(FF[0] + 2, 39), flow=1.3, flutter=2, mirror=True,
                fx=[("arc", (29, 26), 178, -4, ARC)]), 50),
          (dict(dx=0, dy=2, hand=(33, 26), ang=-12, slen=11, footF=(FF[0] + 2, 39), flow=1.5, flutter=3, mirror=True, behind=True,
                fx=[("ring", (29, 26), 13, 170, 230, dict(sq=0.45, w=3.0))]), 70),
          # hit 2: round to the front
          (dict(dx=2, dy=2, hand=(41, 25), ang=-3, footB=(OX + 8, 39), footF=(FF[0] + 4, 39), flow=1.5, flutter=4,
                fx=[("arc", (29, 26), 178, -3, ARC)]), 50),
          (dict(dx=2, dy=1, hand=(40, 20), ang=-40, footB=(OX + 8, 39), footF=(FF[0] + 4, 39), flow=1.1, flutter=5,
                fx=[G.sw(w=0.4)]), 70),
          (dict(dx=1, dy=1, hand=(37, 17), ang=-74, footF=(FF[0] + 2, 39), flow=0.6, flutter=6), 140),
          (dict(dx=1, hand=(35, 25), ang=-52, flow=0.3, flutter=7), 110)]
    return G.mseq(tm(fr, 200, 620, 2), grip=3.0)


# =================================================================================================== KATANA
SHEATHED = dict(hand=(30, 29), ang=168, off=(32, 28), sheath=True)   # (as player_v13_a: hand on the hilt at the left hip)


def kt_draw():  # draw cut: thumb on the guard, one low flat draw from the scabbard at knee height, the tip flicking up
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=2, flow=0.3, fx=[("glint", (32, 30))], footB=(OX + 6, 39), footF=(FF[0] + 2, 39), **SHEATHED), 60),
          (dict(dx=1, dy=3, hand=(35, 29), ang=-176, off=(31, 29), footB=(OX + 7, 39), footF=(OX + 23, 39), flow=0.9, flutter=1), 60),
          (dict(dx=3, dy=3, hand=(41, 28), ang=6, off=(24, 28), footB=(OX + 9, 39), footF=(OX + 25, 39), flow=1.4, flutter=2,
                fx=[("flash", 30, 8, 62), ("arc", (31, 29), 176, 6, G.KARC)]), 45),
          (dict(dx=3, dy=2, hand=(40, 24), ang=-28, off=(24, 27), footB=(OX + 9, 39), footF=(OX + 25, 39), flow=1.2, flutter=3,
                fx=[("flash", 30, 18, 52), G.sw(w=0.35)]), 55),
          (dict(dx=2, dy=1, hand=(37, 19), ang=-62, off=(26, 26), footF=(OX + 23, 39), flow=0.7, flutter=4), 100),
          (dict(dx=1, hand=(35, 26), ang=-42, off=(30, 26), flow=0.3, flutter=5), 80)]
    return G.mseq(tm(fr, 120, 400, 2))


def kt_jjk():  # crescent sheathe: a pivot, one wide flat crescent, a chiburi flick, and the blade slid home -- sheathed again
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=-1, dy=1, hand=(31, 21), ang=-150, flow=0.4), 80),
          (dict(dx=0, dy=3, hand=(33, 27), ang=-12, slen=12, footF=(FF[0] + 1, 39), flow=1.0, flutter=1, mirror=True, behind=True), 90),
          (dict(dx=-1, dy=3, hand=(29, 27), ang=178, footB=(OX + 5, 39), footF=(FF[0] + 2, 39), flow=0.7, flutter=2,
                fx=[("glint", "tip")]), 70),
          (dict(dx=3, dy=3, hand=(41, 25), ang=-2, footB=(OX + 8, 39), footF=(OX + 27, 39), flow=1.6, flutter=3,
                fx=[("arc", (29, 26), 178, -2, dict(sq=0.38, w=0.45)), ("speed", (18, 22), 3, 10)]), 45),
          (dict(dx=3, dy=2, hand=(40, 21), ang=-32, footB=(OX + 8, 39), footF=(OX + 27, 39), flow=1.2, flutter=4,
                fx=[G.sw(w=0.35)]), 60),
          (dict(dx=2, dy=2, hand=(39, 29), ang=34, off=(29, 27), footB=(OX + 8, 39), footF=(OX + 25, 39), flow=0.8, flutter=5,
                fx=[G.sw(w=0.25)]), 100),
          (dict(dx=1, dy=2, hand=(33, 24), ang=-176, off=(31, 27), footF=(OX + 23, 39), flow=0.5, flutter=6), 80),
          (dict(dx=0, dy=1, flow=0.3, flutter=7, fx=[("glint", (32, 30))], footF=(OX + 21, 39), **SHEATHED), 105)]
    return G.mseq(tm(fr, 240, 660, 3), grip=G.GRIP_KATANA)


def kt_tsubame():  # swallow return: from the Iai's high finish the wrist turns over and the edge snaps back up the same line
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=2, dy=1, hand=(38, 17), ang=-58, footF=(OX + 23, 39), flow=0.5), 40),
          (dict(dx=1, dy=3, hand=(36, 31), ang=118, footB=(OX + 6, 39), footF=(OX + 23, 39), flow=1.0, flutter=1,
                fx=[G.sw(w=0.3)]), 60),
          (dict(dx=3, dy=1, hand=(41, 22), ang=-38, footB=(OX + 9, 38), footF=(OX + 25, 39), flow=1.5, flutter=2,
                fx=[("arc", (31, 25), 118, -38, dict(sq=1.0, w=0.4)), ("flare", "tip", 4)]), 45),
          (dict(dx=3, dy=-1, hand=(37, 13), ang=-96, footB=(OX + 10, 37), footF=(OX + 25, 39), flow=1.3, flutter=3,
                fx=[G.sw(w=0.4)]), 55),
          (dict(dx=2, dy=0, hand=(33, 12), ang=-122, footF=(OX + 23, 39), flow=0.7, flutter=4), 150),
          (dict(dx=1, hand=(35, 25), ang=-46, off=(30, 26), flow=0.3, flutter=5), 130)]
    return G.mseq(tm(fr, 100, 480, 2), grip=G.GRIP_KATANA)


def kt_turn():  # turning draw: you stand past the foe, blade out behind; whirl round, one flash back along the line, sheathe
    OX, FF = G.OX, G.FF
    fr = [(dict(dx=3, dy=4, head_dy=1, hand=(32, 31), ang=168, off=(37, 28), footB=(OX + 8, 39), footF=(OX + 26, 39), flow=1.0,
                mirror=True), 60),
          (dict(dx=0, dy=3, hand=(30, 28), ang=176, off=(33, 28), footB=(OX + 5, 39), footF=(OX + 22, 39), flow=1.2, flutter=1,
                fx=[("speed", (30, 20), 3, 10)]), 100),
          (dict(dx=3, dy=2, hand=(41, 24), ang=-6, off=(24, 27), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.6, flutter=2,
                fx=[("flash", 27, 2, 62), ("arc", (31, 27), 176, -6, dict(sq=0.35, w=0.3))]), 45),
          (dict(dx=3, dy=1, hand=(40, 19), ang=-44, off=(24, 27), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.3, flutter=3,
                fx=[("flash", 27, 14, 52), G.sw(w=0.35)]), 60),
          (dict(dx=2, dy=2, hand=(39, 28), ang=32, off=(29, 27), footF=(OX + 24, 39), flow=0.7, flutter=4, fx=[G.sw(w=0.2)]), 120),
          (dict(dx=1, dy=2, hand=(32, 25), ang=-176, off=(31, 27), footF=(OX + 22, 39), flow=0.4, flutter=5), 80),
          (dict(dy=1, flow=0.3, flutter=6, fx=[("glint", (32, 30))], **SHEATHED), 155)]
    return G.mseq(tm(fr, 160, 620, 2))


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

    add("ls_jk", ls_jk, 260, 600, A(3, 4), up=True, x0=-2)
    add("ls_rollk", ls_rollk, 240, 600, A(3, 4), x0=-6)
    add("ls_air2", ls_air2, 150, 360, A(2, 3), settle=False)
    add("ls_wheel", ls_wheel, 200, 620, A(2, 4), hits=[2, 4], both=True)
    add("kt_draw", kt_draw, 120, 400, A(2, 3), x0=-2)
    add("kt_jjk", kt_jjk, 240, 660, A(3, 4), settle=False, x0=-6)
    add("kt_tsubame", kt_tsubame, 100, 480, A(2, 3), up=True, x0=-2)
    add("kt_turn", kt_turn, 160, 620, A(2, 3), settle=False, x0=-2)
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    fns = dict(GP.ANIMS)
    mod = sys.modules.get("player_v14_blade")
    print(f"{'tag':14} {'frames':>6} {'wind':>5} {'total':>5}   {'spec':>9}   ok")
    for t in [e[0] for e in mod.register(GP)]:
        fr = list(fns[t]())
        ms = [m for _, m in fr]
        act = GP.ACTIVE.get(t)
        wind = sum(ms[:act[0]]) if act else None
        tot = sum(ms)
        sp = mod.SPEC.get(t)
        ok = "" if not sp else ("OK" if (wind, tot) == sp else "MISMATCH")
        print(f"{t:14} {len(fr):6} {wind if wind is not None else '-':>5} {tot:5}   {('%d/%d' % sp) if sp else '-':>9}   {ok}")
