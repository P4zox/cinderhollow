"""v15 tags for the Close-range Bow (bow, prefix bw_, weapon ashstring) -- docs/WEAPON_REVAMP.md C2, docs/v15/bow.md.

Same register(G) contract as player_v13_a.py / player_v14_*.py: [(tag, fn, opts)], fn() -> [(cels, ms)].

The bow is restyled here (G.WPN["ashstring"]): a bigger horn-tipped recurve whose STRING AND ARROW FOLLOW THE DRAW. Every
frame of a bw_ tag says how far the string is drawn (bwD, px behind the brace), whether an arrow is nocked (bwA), and
where the drawing hand is (bwPull: on the nock; bwPullAt: an explicit point once the string is loosed). The drawing arm
is the far arm, its elbow driven back past the shoulder; its fist is drawn over the body so the hand on the string reads.
The broadhead uses two colours found nowhere else in the overlay ((232,238,252) / (128,134,158)): the game finds the
arrowhead in each frame by those pixels and hangs the charge-level glow and the sweet-spot glint on it.

Tags (wind / total, ms -- matched to web/src/78_mech_bow.js; tm() rescales the hand timing):
  bw_1        J        quick shot: snap the bow up, half draw, loose                                120 / 340
  bw_2        J J      quick shot: a step in, bow canted, loose two                                 120 / 340
  bw_3        J J J    quick shot: low wide stance, bow flat-canted, loose three                    120 / 340
  bw_pin      J x4     pinning shot: step in, a deep draw, one heavy arrow, the bow kicks            200 / 520
  bw_draw     hold K   the draw (frames picked by the engine): raise, nock, lv1, lv2, lv3, lv3 strain   loop
  bw_drawwalk hold K   walking at full draw: feet plant on the back half, lift on the forward swing    loop
  bw_power    release  power shot: loose from full draw, the bow arm recoils, a half step back        70 / 520
  bw_hollow   K (III)  hollow piercer: sink, bow vertical, a long strained draw, loose a drilling arrow 360 / 1100
  bw_stab     J K      arrow stab: the nocked arrow jabbed like a dagger, bow and string hand together 120 / 380
  bw_recoil   J K K    recoil shot: point-blank, the shot kicks you up and back                         140 / 520
  bw_arc      ↑J       arc shot: lean back, bow raised high, loose a volley into the sky                300 / 760
  bw_step     L        charge step: a low sideways skip, the string drawn a notch                       (dodge)
  bw_dash     L J      dash shot: skid in low and loose                                              140 / 400
  bw_leap     L K      leaping point-blank: hop in, loose a fan down into the foe, land               220 / 600
  bw_deflect  I        limb deflect: the bow swept up, its upper limb turned out to catch the blow    150 / 260
  bw_counter  deflect  counter shot: the bow snapped level, point-blank                               80 / 460
  bw_air      air J    aerial shot: tucked, aim down at a slant, loose                               150 / 380
  bw_down     air ↓J   talon stomp: the bow's lower limb stamped down like a talon (pogo)          100 / 300
  bw_dive     air K    hunter's dive: tucked, bow forward, diving (loops)                                  loop
  bw_diveshot dive     dive shot: land low and loose a fan point-blank                                60 / 460
"""
import math

G = None   # gen_player, set by register()

_DRAW = [0.0, True]   # (draw px, arrow nocked) of the weapon cel being rendered (set by the Wpn.render_core wrap)
HEAD_LIT, HEAD_DARK = (232, 238, 252), (128, 134, 158)   # the broadhead: the engine looks for exactly these
LIMB_LIT, LIMB_DARK, LIMB_EDGE = (124, 76, 50), (70, 40, 30), (40, 22, 20)
HORN = (226, 206, 158)
STRING = (214, 210, 198)
SHAFT, FLETCH, FLETCH2 = (176, 150, 110), (190, 60, 50), (130, 36, 32)
SPAN = 9.6   # half height of the bow (px)


def _limb_u(av, d):
    """The limb's centre line (u) at height av for a draw of d px: bowed back toward the archer, flicked at the tips."""
    t = min(av / SPAN, 1.0)
    u = 0.9 - 3.3 * math.sin(t * math.pi * 0.5) ** 1.3
    if av > 7.4:
        u += 1.5 * ((av - 7.4) / 2.2) ** 2
    return u - 0.2 * d * t * t


def shp_ashstring_bw(u, v, s, L):
    d, arrow = _DRAW
    vl = v * s
    av = abs(v)
    tip_v = SPAN - 0.25 * max(0.0, d) * 0.3
    # limbs
    if 0.7 <= av <= tip_v + 0.4:
        uc = _limb_u(av, max(0.0, d))
        w = 1.05 if av < 6.0 else 0.75
        if abs(u - uc) <= w:
            if av > tip_v - 1.1:
                return HORN if vl >= -0.5 else (160, 140, 100)
            if abs(u - uc) > w - 0.35 and (u - uc) < 0:
                return LIMB_EDGE
            return LIMB_LIT if vl > 0 else LIMB_DARK
    # grip (wrapped)
    if av <= 1.1 and -0.5 <= u <= 1.7:
        return (156, 124, 82) if (int(math.floor(v * 1.6 + u)) % 2 == 0) else (100, 76, 48)
    # the string: from each limb tip to the nock point
    ut = _limb_u(tip_v, max(0.0, d)) - 0.3
    un = ut - 0.6 - d
    if av <= tip_v:
        ul = un + (ut - un) * (av / tip_v)
        if abs(u - ul) <= 0.42:
            return STRING
    if not arrow:
        return None
    # the nocked arrow along v = 0, nock at the string, broadhead at the tip
    tip = L + 1.5 - max(0.0, d)
    if un - 0.4 <= u <= un + 2.6 and 0.45 < av <= 1.3 and u < un + 0.6 + (2.6 - (av - 0.45) * 2.0):
        return FLETCH if v > 0 else FLETCH2
    if av <= 0.45 and un - 0.4 <= u <= tip - 2.8:
        if u <= un + 2.4:
            return FLETCH
        return SHAFT
    if tip - 3.0 <= u <= tip and av <= 1.45 * (tip - u) / 3.0 + 0.2:
        return HEAD_LIT if vl >= 0 else HEAD_DARK
    return None


def _install(g):
    """Restyle the Ashstring, and teach the weapon cel to render the draw state of its frame."""
    g.WPN["ashstring"] = (shp_ashstring_bw, 15, 4.0, 10.2, "blade")
    if getattr(g.Wpn, "_bw_wrapped", False):
        return
    orig = g.Wpn.render_core

    def render_core(self, kind, dust=True):
        _DRAW[0], _DRAW[1] = getattr(self, "bw_draw", 0.0), getattr(self, "bw_arrow", True)
        try:
            return orig(self, kind, dust)
        finally:
            _DRAW[0], _DRAW[1] = 0.0, True
    g.Wpn.render_core = render_core
    g.Wpn._bw_wrapped = True
    # the hit-box measurer rasterises with draw_weapon directly (no cel): it sees the braced bow with its arrow


# ------------------------------------------------------------------------------------------------ frame building
def _fist(g, hx, hy):
    hx, hy = int(round(hx)), int(round(hy))
    pts = ((0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (1, -1))
    for a, b in pts:
        G.put(g, hx + a, hy + b, '3')
    G.put(g, hx + 1, hy - 1, '5')
    G.put(g, hx, hy - 1, '4')
    return [(hx + a, hy + b) for a, b in pts]


def _pull_arm(cels, sh, hand, elbow):
    """The drawing (far) arm: shoulder -> elbow driven back -> the hand on the string. The arm goes behind the torso, the
    fist is drawn over everything so the hand on the string always reads."""
    g = G.blank()
    G.limb(g, [sh, elbow, hand], 3.0, '4', '3', '2')
    cels["OffArm"] = G.outline(g)
    f = G.blank()
    px = _fist(f, hand[0] - 0.5, hand[1] - 0.5)
    G.item_merge(cels, G.outline(f))
    return px


def bseq(frames, base=None, grip=None):
    """mseq + the bow state of each frame (bwD draw px, bwA arrow nocked, bwPull hand on the nock, bwPullAt a free hand,
    bwElbow the drawing elbow (pose space, default: behind the shoulder))."""
    base = base or {}
    fixed = []
    for p, ms in frames:   # a "tip" glint means the broadhead: where it is once the string is drawn
        q = {**base, **p}
        if "hand" in q and any(f[0] == "glint" and f[1] == "tip" for f in q.get("fx", ())):
            a = math.radians(q["ang"]); u = 15 * q.get("slen", 18) / 18.0 + 1.5 - max(0.0, q.get("bwD", 0.0)) - 1.5
            pt = (q["hand"][0] + math.cos(a) * u, q["hand"][1] + math.sin(a) * u)
            p = {**p, "fx": [("glint", pt) if (f[0] == "glint" and f[1] == "tip") else f for f in q["fx"]]}
        fixed.append((p, ms))
    frames = fixed
    out = G.mseq(frames, base, grip=grip)
    for (cels, ms), (p, _) in zip(out, frames):
        q = {**base, **p}
        w = cels.get("Sword")
        if not isinstance(w, G.Wpn):
            continue
        d = q.get("bwD", 0.0)
        w.bw_draw, w.bw_arrow = d, q.get("bwA", True)
        bx, by = q.get("dx", 0), q.get("dy", 0)
        sh = (G.OX + 11 + bx, G.OY + 14 + by)
        hand = None
        if q.get("bwPull") and "hand" in q:
            a = math.radians(q["ang"])
            ut = _limb_u(SPAN - 0.075 * max(0.0, d), max(0.0, d)) - 0.3
            un = ut - 0.6 - d
            hx, hy = q["hand"][0] + bx, q["hand"][1] + by
            hand = (hx + math.cos(a) * (un - 0.3), hy + math.sin(a) * (un - 0.3))
        elif q.get("bwPullAt"):
            hand = (q["bwPullAt"][0] + bx, q["bwPullAt"][1] + by)
        if hand is not None:
            el = q.get("bwElbow")
            elbow = (el[0] + bx, el[1] + by) if el else (min(sh[0] - 3.5, hand[0] - 6.5), (sh[1] + hand[1]) / 2 - 2.5)
            px = _pull_arm(cels, sh, hand, elbow)
            w.clear = tuple(w.clear) + tuple((x, y) for x, y in px if 0 <= x < G.W and 0 <= y < G.H)
    return out


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


# poses (pose space; body drawn at dx/dy; the bow hand is "hand", the bow axis "ang" (0 = arrow level, ahead))
def AIM(hx=40, hy=21, ang=0, d=0.0, **k):
    return dict(hand=(hx, hy), ang=ang, bwD=d, bwPull=True, **k)


def LOOSE(hx=40, hy=21, ang=0, pull=(26, 19), **k):
    return dict(hand=(hx, hy), ang=ang, bwD=-0.6, bwA=False, bwPullAt=pull, **k)


def REST(**k):   # bow low and forward, string hand back at the hip on a fresh arrow
    return dict(hand=(35, 26), ang=-35, bwD=0.0, **k)


# ================================================================================================= the draw
def bw_draw():
    """Engine-driven frames: 0 raise, 1 nock, 2 lv1, 3 lv2, 4 lv3, 5 lv3 strain."""
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 6, 39), footF=(FF[0] + 2, 39))
    fr = [(dict(dy=1, hand=(37, 24), ang=-20, bwD=0.0, flow=0.3, **st), 60),
          (dict(dy=1, **AIM(39, 22, -4, 2.0), flow=0.3, **st), 60),
          (dict(dy=1, **AIM(40, 21, -1, 4.5), flow=0.35, **st), 400),
          (dict(dy=1, head_dx=-1, **AIM(41, 21, 0, 7.0), flow=0.4, flutter=1, **st), 400),
          (dict(dy=1, dx=-1, head_dx=-1, **AIM(41, 21, 0, 9.0), flow=0.45, flutter=2, **st), 140),
          (dict(dy=1, dx=-1, head_dx=-1, **AIM(41, 20, -1, 9.5), flow=0.5, flutter=3, **st), 140)]
    return bseq(fr)


def bw_drawwalk():
    """Stalking at full draw (8 x 60 ms, 12 px stride: ~50 px/s, the engine's 40% walk). The upper body stays locked on
    the aim; each foot is planted for half the cycle and pushed straight back along the floor, then lifted and carried
    forward (no moonwalk)."""
    OX = G.OX

    def foot(ph, hip_x):
        ph %= 1.0
        if ph < 0.5:
            return (hip_x + 6 - 24 * ph, 39)
        s2 = (ph - 0.5) * 2
        e = s2 * s2 * (3 - 2 * s2)
        return (hip_x - 6 + 12 * e, 39 - 3.0 * math.sin(math.pi * s2))
    fr = []
    for i in range(8):
        ph = i / 8
        bob = [1, 1, 0, 1, 1, 1, 0, 1][i]
        fr.append((dict(dy=bob, head_dx=-1, **AIM(41, 21 - bob, 0, 8.0), footF=foot(ph, OX + 15), footB=foot(ph + 0.5, OX + 11),
                        leg=5.5, flow=0.45 + 0.1 * math.sin(ph * 2 * math.pi), flutter=i), 60))
    return bseq(fr)


# ================================================================================================= quick shots
def bw_1():  # snap up, half draw, loose
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=1, hand=(36, 25), ang=-25, bwD=0.0, flow=0.3, footF=(FF[0] + 1, 39)), 50),
          (dict(dy=1, **AIM(39, 22, -3, 4.0), flow=0.35, footF=(FF[0] + 2, 39), fx=[("glint", "tip")]), 70),
          (dict(dy=1, **LOOSE(41, 21, 0, (28, 20)), flow=0.6, flutter=1, footF=(FF[0] + 2, 39),
                fx=[("streak", 10), ("flare", (44, 21), 3)]), 50),
          (dict(dy=1, **LOOSE(40, 21, -2, (25, 21)), flow=0.5, flutter=2, footF=(FF[0] + 2, 39), fx=[("streak", 6)]), 60),
          (dict(dy=1, hand=(38, 23), ang=-12, bwD=0.0, bwPullAt=(29, 23), flow=0.35, flutter=3), 80),
          (dict(hand=(36, 25), ang=-25, bwD=0.0, flow=0.3, flutter=4), 70)]
    return bseq(tm(fr, 120, 340, 2))


def bw_2():  # step in, the a lean into it, loose two
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 8, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dx=1, dy=1, hand=(37, 24), ang=-30, bwD=0.0, flow=0.4, footF=(FF[0] + 2, 38)), 50),
          (dict(dx=1, dy=2, **AIM(40, 22, -3, 5.0), flow=0.45, **st), 70),
          (dict(dx=2, dy=2, **LOOSE(42, 21, -1, (29, 21)), flow=0.7, flutter=1, **st, fx=[("streak", 10), ("flare", (45, 20), 3)]), 50),
          (dict(dx=2, dy=2, **LOOSE(41, 21, -3, (26, 22)), flow=0.6, flutter=2, **st, fx=[("streak", 6)]), 60),
          (dict(dx=1, dy=1, hand=(38, 23), ang=-20, bwD=0.0, bwPullAt=(29, 24), flow=0.4, flutter=3, **st), 80),
          (dict(dx=1, hand=(36, 25), ang=-28, bwD=0.0, flow=0.3, flutter=4), 70)]
    return bseq(tm(fr, 120, 340, 2))


def bw_3():  # low wide stance, the shot driven slightly down into the foe, a fan of three
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 3, 39), footF=(FF[0] + 5, 39))
    fr = [(dict(dx=1, dy=2, hand=(37, 25), ang=-40, bwD=0.0, flow=0.4, **st), 50),
          (dict(dx=1, dy=3, head_dy=1, **AIM(41, 23, 2, 5.5), flow=0.5, **st), 70),
          (dict(dx=2, dy=3, head_dy=1, **LOOSE(43, 23, 3, (30, 23)), flow=0.8, flutter=1, **st,
                fx=[("streak", 9), ("flare", (46, 20), 3)]), 50),
          (dict(dx=2, dy=3, head_dy=1, **LOOSE(42, 23, 1, (27, 24)), flow=0.7, flutter=2, **st), 60),
          (dict(dx=1, dy=2, hand=(38, 23), ang=-30, bwD=0.0, bwPullAt=(29, 25), flow=0.4, flutter=3, **st), 80),
          (dict(dy=1, hand=(36, 25), ang=-28, bwD=0.0, flow=0.3, flutter=4), 70)]
    return bseq(tm(fr, 120, 340, 2))


# ================================================================================================= heavy shots
def bw_pin():  # J J J J: plant the front foot, a deep draw, one heavy arrow; the bow kicks up and the string hand flies back
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 5, 39), footF=(FF[0] + 5, 39))
    fr = [(dict(dx=1, dy=1, hand=(37, 24), ang=-20, bwD=0.0, flow=0.4, footF=(FF[0] + 3, 38)), 50),
          (dict(dx=1, dy=2, **AIM(40, 21, -1, 6.0), flow=0.4, **st), 60),
          (dict(dx=1, dy=2, head_dx=-1, **AIM(41, 21, 0, 9.5), flow=0.45, flutter=1, **st, fx=[("glint", "tip")]), 90),
          (dict(dx=2, dy=2, **LOOSE(42, 21, -2, (24, 19)), flow=0.9, flutter=2, **st,
                fx=[("streak", 14), ("flare", (46, 21), 4)]), 50),
          (dict(dx=1, dy=1, **LOOSE(41, 19, -12, (22, 18)), flow=0.8, flutter=3, **st), 80),
          (dict(dx=1, dy=1, hand=(40, 21), ang=-6, bwD=0.0, bwPullAt=(27, 22), flow=0.5, flutter=4, **st), 100),
          (dict(dy=1, hand=(37, 24), ang=-20, bwD=0.0, flow=0.35, flutter=5), 90)]
    return bseq(tm(fr, 200, 520, 3))


def bw_power():  # release: from the full draw, loose; the bow arm recoils up, a half step back
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 6, 39), footF=(FF[0] + 2, 39))
    fr = [(dict(dy=1, dx=-1, head_dx=-1, **AIM(41, 21, 0, 9.5), flow=0.5, flutter=0, **st), 70),
          (dict(dy=1, **LOOSE(42, 21, 0, (22, 19)), flow=1.0, flutter=1, **st,
                fx=[("streak", 16), ("flare", (46, 21), 5)]), 50),
          (dict(dy=1, dx=-1, **LOOSE(41, 19, -14, (21, 18)), flow=0.9, flutter=2, footB=(OX + 4, 39), footF=(FF[0] + 1, 39),
                fx=[("streak", 8)]), 90),
          (dict(dy=1, dx=-1, **LOOSE(40, 20, -10, (23, 20)), flow=0.6, flutter=3, footB=(OX + 4, 39), footF=(FF[0] + 1, 39)), 110),
          (dict(dy=1, hand=(38, 23), ang=-16, bwD=0.0, bwPullAt=(28, 23), flow=0.4, flutter=4), 100),
          (dict(hand=(36, 25), ang=-26, bwD=0.0, flow=0.3, flutter=5), 100)]
    return bseq(tm(fr, 70, 520, 1))


def bw_hollow():  # III: sink low and square, the bow dead level, a long straining draw, then a drilling arrow that shoves you back
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 3, 39), footF=(FF[0] + 5, 39))
    ST = dict(footB=(OX + 2, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dy=2, hand=(38, 24), ang=-10, bwD=0.0, flow=0.4, **st), 70),
          (dict(dy=3, head_dy=1, **AIM(40, 21, 0, 5.0), flow=0.4, flutter=1, **st, fx=[("dust", 22, 2)]), 90),
          (dict(dy=3, head_dy=1, head_dx=-1, **AIM(41, 21, 0, 9.0), flow=0.5, flutter=2, **st), 100),
          (dict(dy=3, dx=-1, head_dy=1, head_dx=-1, **AIM(41, 20, 0, 10.0), flow=0.55, flutter=3, **st, fx=[("glint", "tip")]), 100),
          (dict(dy=3, dx=-3, head_dy=1, **LOOSE(39, 21, 0, (19, 19)), flow=1.4, flutter=4, **ST,
                fx=[("streak", 18), ("flare", (44, 21), 6), ("dust", 20, 4)]), 70),
          (dict(dy=3, dx=-4, head_dy=1, **LOOSE(38, 19, -10, (18, 18)), flow=1.2, flutter=5, **ST, fx=[("dust", 16, 3), ("streak", 8)]), 110),
          (dict(dy=2, dx=-3, **LOOSE(37, 20, -14, (21, 20)), flow=0.8, flutter=6, **ST), 160),
          (dict(dy=2, dx=-2, hand=(36, 23), ang=-20, bwD=0.0, bwPullAt=(25, 23), flow=0.5, flutter=7, **ST), 200),
          (dict(dy=1, dx=-1, hand=(35, 25), ang=-26, bwD=0.0, flow=0.35, flutter=8), 200)]
    return bseq(tm(fr, 360, 1100, 4))


# ================================================================================================= close quarters
def bw_stab():  # J -> K: the nocked arrow jabbed home like a dagger, bow and string hand driven in together
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=1, **AIM(34, 23, 4, 3.0), flow=0.4, footF=(FF[0] + 1, 39)), 60),
          (dict(dx=-1, dy=2, head_dx=-1, **AIM(33, 23, 6, 4.0), flow=0.4, flutter=1, footB=(OX + 6, 39), footF=(FF[0] + 1, 39)), 60),
          (dict(dx=2, dy=2, **AIM(45, 23, 2, 0.5), flow=1.1, flutter=2, footB=(OX + 7, 39), footF=(FF[0] + 5, 39), fx=[("streak", 8)]), 50),
          (dict(dx=2, dy=2, **AIM(44, 23, 3, 0.5), flow=0.9, flutter=3, footB=(OX + 7, 39), footF=(FF[0] + 5, 39)), 60),
          (dict(dx=1, dy=1, **AIM(40, 23, 0, 1.5), flow=0.5, flutter=4, footF=(FF[0] + 3, 39)), 80),
          (dict(dy=1, hand=(36, 25), ang=-20, bwD=0.0, flow=0.3, flutter=5), 70)]
    return bseq(tm(fr, 120, 380, 2))


def bw_recoil():  # J K K: shoved in at point-blank, the bow angled down into the foe; the shot kicks you up and back
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 5, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dx=1, dy=3, head_dy=1, **AIM(40, 24, 14, 5.0), flow=0.5, **low), 70),
          (dict(dx=1, dy=3, head_dy=1, **AIM(40, 24, 16, 8.5), flow=0.5, flutter=1, **low), 70),
          (dict(dx=-1, dy=-1, **LOOSE(39, 24, 12, (22, 19)), flow=1.4, flutter=2, footB=(OX + 7, 37), footF=(OX + 17, 36), air=True,
                fx=[("streak", 12), ("flare", (44, 26), 5)]), 60),
          (dict(dx=-2, dy=-2, **LOOSE(37, 20, -24, (22, 18)), flow=1.6, flutter=3, footB=(OX + 7, 35), footF=(OX + 16, 35), air=True), 110),
          (dict(dx=-1, dy=3, head_dy=1, hand=(37, 26), ang=-10, bwD=0.0, bwPullAt=(26, 25), flow=0.8, flutter=4,
                footB=(OX + 5, 39), footF=(FF[0] + 2, 39), fx=[("dust", 20, 3)]), 110),
          (dict(dy=1, hand=(36, 25), ang=-24, bwD=0.0, flow=0.4, flutter=5), 100)]
    return bseq(tm(fr, 140, 520, 2))


def bw_arc():  # up J: lean back, the bow raised high, a volley loosed into the sky (it rains down ahead)
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 6, 39), footF=(FF[0] + 2, 39))
    fr = [(dict(dy=1, hand=(37, 22), ang=-40, bwD=0.0, flow=0.3, **st), 80),
          (dict(dy=1, head_dx=-1, **AIM(36, 17, -62, 5.0), bwElbow=(22, 18), flow=0.35, flutter=1, **st), 90),
          (dict(dx=-1, dy=1, head_dx=-1, **AIM(36, 16, -64, 9.0), bwElbow=(21, 18), flow=0.4, flutter=2, **st, fx=[("glint", "tip")]), 130),
          (dict(dx=-1, dy=1, **LOOSE(37, 16, -64, (23, 20)), flow=0.8, flutter=3, **st,
                fx=[("streak", 14), ("flare", "tip", 4)]), 60),
          (dict(dx=-1, dy=1, **LOOSE(36, 15, -70, (23, 21)), flow=0.7, flutter=4, **st, fx=[("streak", 6)]), 140),
          (dict(dy=1, hand=(37, 20), ang=-50, bwD=0.0, bwPullAt=(27, 23), flow=0.4, flutter=5), 130),
          (dict(hand=(36, 25), ang=-30, bwD=0.0, flow=0.3, flutter=6), 130)]
    return bseq(tm(fr, 300, 760, 3))


def bw_step():  # L: charge step -- a low, quick sideways skip, the string drawn a notch further (+1 level)
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=2, **AIM(39, 23, -4, 3.0), flow=0.5, footB=(OX + 7, 39), footF=(FF[0] + 1, 39)), 50),
          (dict(dx=1, dy=1, **AIM(40, 22, -3, 4.0), flow=1.3, flutter=1, footB=(OX + 9, 37), footF=(OX + 18, 36),
                fx=[("dust", 24, 1)]), 80),
          (dict(dx=1, dy=2, **AIM(40, 22, -2, 5.5), flow=1.1, flutter=2, footB=(OX + 6, 39), footF=(FF[0] + 3, 39),
                fx=[("dust", 22, 2), ("glint", "tip")]), 80),
          (dict(dy=1, **AIM(39, 23, -4, 4.0), flow=0.6, flutter=3), 90)]
    return bseq(fr)


def bw_dash():  # L -> J: skid in low out of the step and loose on the slide
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 4, 39), footF=(FF[0] + 6, 39))
    fr = [(dict(dx=1, dy=3, head_dy=1, **AIM(41, 24, 2, 5.0), flow=1.2, **low, fx=[("speed", (18, 26), 3, 12), ("dust", 34, 2)]), 70),
          (dict(dx=2, dy=3, head_dy=1, **AIM(42, 24, 2, 8.0), flow=1.0, flutter=1, **low, fx=[("dust", 38, 3)]), 70),
          (dict(dx=2, dy=3, head_dy=1, **LOOSE(43, 24, 2, (25, 22)), flow=0.9, flutter=2, **low,
                fx=[("streak", 12), ("flare", (47, 24), 4)]), 50),
          (dict(dx=1, dy=2, **LOOSE(41, 22, -8, (24, 22)), flow=0.6, flutter=3, **low), 90),
          (dict(dy=1, hand=(37, 24), ang=-18, bwD=0.0, bwPullAt=(28, 24), flow=0.4, flutter=4), 70),
          (dict(hand=(36, 25), ang=-26, bwD=0.0, flow=0.3, flutter=5), 60)]
    return bseq(tm(fr, 140, 400, 2))


def bw_leap():  # L -> K: hop in over the foe's guard and loose a fan straight down into it, then land
    OX, FF = G.OX, G.FF
    fr = [(dict(dy=3, head_dy=1, **AIM(38, 24, 10, 4.0), flow=0.6, footB=(OX + 5, 39), footF=(FF[0] + 2, 39)), 70),
          (dict(dy=-4, **AIM(40, 23, 24, 8.5), flow=1.3, flutter=1, **G.TUCK, fx=[("glint", "tip")]), 150),
          (dict(dy=-4, **LOOSE(41, 24, 26, (24, 18)), flow=1.4, flutter=2, **G.TUCK,
                fx=[("streak", 12), ("flare", (45, 27), 5)]), 60),
          (dict(dy=-3, **LOOSE(39, 21, 0, (23, 19)), flow=1.0, flutter=3, **G.AIR), 110),
          (dict(dy=3, head_dy=1, hand=(38, 27), ang=-8, bwD=0.0, bwPullAt=(27, 25), flow=0.7, flutter=4,
                footB=(OX + 5, 39), footF=(FF[0] + 3, 39), fx=[("dust", 22, 3)]), 120),
          (dict(dy=1, hand=(36, 25), ang=-24, bwD=0.0, flow=0.4, flutter=5), 90)]
    return bseq(tm(fr, 220, 600, 2))


def bw_deflect():  # I: the bow swept up across the body, its upper limb turned out to take the blow
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 6, 39), footF=(FF[0] + 1, 39))
    fr = [(dict(dx=-1, dy=1, hand=(37, 20), ang=-78, bwD=0.0, flow=0.4, **st, fx=[("glint", (44, 18))]), 60),
          (dict(dx=-1, dy=2, head_dx=-1, hand=(38, 19), ang=-84, bwD=0.0, flow=0.5, flutter=1, **st), 90),
          (dict(dx=-1, dy=1, hand=(37, 21), ang=-60, bwD=0.0, flow=0.4, flutter=2, **st), 60),
          (dict(hand=(36, 24), ang=-36, bwD=0.0, flow=0.3, flutter=3), 50)]
    return bseq(tm(fr, 150, 260, 2))


def bw_counter():  # deflect -> the counter shot: the bow snapped level off the parry, string to the jaw, point-blank
    OX, FF = G.OX, G.FF
    st = dict(footB=(OX + 6, 39), footF=(FF[0] + 3, 39))
    fr = [(dict(dx=1, dy=2, head_dx=-1, **AIM(41, 22, 0, 8.5), flow=0.7, **st, fx=[("glint", "tip")]), 80),
          (dict(dx=1, dy=2, **LOOSE(42, 22, 0, (22, 19)), flow=1.1, flutter=1, **st,
                fx=[("streak", 14), ("flare", (46, 22), 5)]), 50),
          (dict(dy=1, **LOOSE(41, 20, -12, (22, 19)), flow=0.8, flutter=2, footB=(OX + 5, 39), footF=(FF[0] + 2, 39)), 110),
          (dict(dy=1, hand=(38, 23), ang=-16, bwD=0.0, bwPullAt=(27, 23), flow=0.5, flutter=3), 120),
          (dict(hand=(36, 25), ang=-26, bwD=0.0, flow=0.3, flutter=4), 100)]
    return bseq(tm(fr, 80, 460, 1))


# ================================================================================================= air
def bw_air():  # air J: knees tucked, the bow tipped down at the foe below-ahead, loosed at a slant
    base = dict(dy=-3, **G.TUCK)
    fr = [(dict(hand=(37, 22), ang=10, bwD=2.0, bwPull=True, flow=0.6), 60),
          (dict(**AIM(39, 23, 22, 7.5), flow=0.8, flutter=1), 90),
          (dict(**LOOSE(40, 24, 24, (24, 19)), flow=1.1, flutter=2, fx=[("streak", 12), ("flare", (44, 26), 4)]), 50),
          (dict(**LOOSE(38, 21, 6, (24, 20)), flow=0.9, flutter=3), 90),
          (dict(hand=(36, 24), ang=-20, bwD=0.0, flow=0.6, flutter=4, **G.AIR), 90)]
    return bseq(tm(fr, 150, 380, 2), base)


def bw_down():  # air down J: talon stomp -- the bow turned point-down under the feet, its arrow the talon, stamped through
    base = dict(dy=-4, head_dy=1, **G.TUCK)
    fr = [(dict(dy=-5, head_dy=0, hand=(31, 20), ang=80, slen=13, bwD=0.0, flow=0.9, footB=(G.OX + 9, 34), footF=(G.OX + 17, 34)), 50),
          (dict(hand=(33, 28), ang=90, slen=14, bwD=0.0, flow=1.3, flutter=1, footB=(G.OX + 10, 38), footF=(G.OX + 16, 38),
                fx=[("streak", 9)] + G.DIVE(9)), 50),
          (dict(dy=-3, hand=(33, 28), ang=90, slen=14, bwD=0.0, flow=1.5, flutter=2, footB=(G.OX + 10, 38), footF=(G.OX + 16, 38),
                fx=G.DIVE(7, 1)), 60),
          (dict(dy=-3, head_dy=0, hand=(35, 24), ang=10, bwD=0.0, flow=0.7, flutter=3, **G.AIR), 140)]
    fr = bseq(tm(fr, 100, 300, 1), base)
    return G.cape_dive(fr, [1, 2])


def bw_dive():  # air K: hunter's dive -- tucked, bow forward and down, string drawn; loops while diving
    base = dict(dy=-3, **G.TUCK)
    fr = [(dict(**AIM(39, 25, 34, 6.0), flow=1.4, flutter=0, fx=G.DIVE(7)), 60),
          (dict(**AIM(39, 25, 36, 6.5), flow=1.6, flutter=2, fx=G.DIVE(8, 1)), 60),
          (dict(**AIM(39, 25, 35, 6.0), flow=1.5, flutter=4, fx=G.DIVE(7)), 60)]
    fr = bseq(fr, base)
    return G.cape_dive(fr, [0, 1, 2])


def bw_diveshot():  # the dive lands (or meets the foe): crouched low, a point-blank fan loosed into it
    OX, FF = G.OX, G.FF
    low = dict(footB=(OX + 4, 39), footF=(FF[0] + 4, 39))
    fr = [(dict(dy=4, head_dy=1, **AIM(40, 25, 6, 8.5), flow=1.2, **low, fx=[("dust", 22, 4)]), 60),
          (dict(dy=4, head_dy=1, **LOOSE(41, 25, 6, (23, 21)), flow=1.0, flutter=1, **low,
                fx=[("streak", 12), ("flare", (45, 26), 5), ("dust", 30, 3)]), 60),
          (dict(dy=3, dx=-1, **LOOSE(40, 22, -10, (22, 20)), flow=0.8, flutter=2, **low), 110),
          (dict(dy=2, hand=(37, 25), ang=-16, bwD=0.0, bwPullAt=(27, 24), flow=0.5, flutter=3), 120),
          (dict(hand=(36, 25), ang=-26, bwD=0.0, flow=0.3, flutter=4), 110)]
    return bseq(tm(fr, 60, 460, 1))


def register(g):
    global G
    G = g
    _install(g)
    return [
        ("bw_1", bw_1, dict(active=(2, 3))),
        ("bw_2", bw_2, dict(active=(2, 3))),
        ("bw_3", bw_3, dict(active=(2, 3))),
        ("bw_pin", bw_pin, dict(active=(3, 4))),
        ("bw_draw", bw_draw, dict(active=(2, 3))),
        ("bw_drawwalk", bw_drawwalk, dict(active=(1, 2))),
        ("bw_power", bw_power, dict(active=(1, 2))),
        ("bw_hollow", bw_hollow, dict(active=(4, 5))),
        ("bw_stab", bw_stab, dict(active=(2, 3), fxat=(30, -17))),
        ("bw_recoil", bw_recoil, dict(active=(2, 3))),
        ("bw_arc", bw_arc, dict(active=(3, 4), up=True)),
        ("bw_step", bw_step, dict(active=(1, 2))),
        ("bw_dash", bw_dash, dict(active=(2, 3))),
        ("bw_leap", bw_leap, dict(active=(2, 3))),
        ("bw_deflect", bw_deflect, dict(active=(0, 1))),
        ("bw_counter", bw_counter, dict(active=(1, 2))),
        ("bw_air", bw_air, dict(active=(2, 3))),
        ("bw_down", bw_down, dict(active=(1, 2), down=True)),
        ("bw_dive", bw_dive, dict(active=(0, 1))),
        ("bw_diveshot", bw_diveshot, dict(active=(1, 2))),
    ]
