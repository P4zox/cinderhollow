"""v15 tags for the Switch Axe (saxe, prefix sx_, weapon gravegrinder) -- docs/WEAPON_REVAMP.md C1, docs/v15/saxe.md.

Same register(G) contract as player_v13_a.py / player_v14_*.py: return [(tag, fn, opts)], fn() -> [(cels, ms)].
Timing: every attack is authored to its row in web/src/78_mech_saxe.js -- tm() rescales the hand-timed frames so the frames
before the first active frame add up to the wind-up and all frames to the total.

THE TWO FORMS (the weapon morphs). The Gravegrinder is one jack-knife mechanism drawn by one blade-space shape whose
geometry is driven by a form (slide, rot), both 0..1:
  * slide: the axe head rides up the telescoping haft (0 = head folded down at the hilt, 1 = head at the haft's end);
  * rot:   the sword blade swings 180 degrees round its hinge pin, out through the open side (0 = blade straight out
           ahead = SWORD, 1 = blade folded back along the haft, edge tucked in = AXE).
A morph tag steps the two through a mechanical order (unlatch, swing, slide, lock) frame by frame.
Every Wpn cel of an sx_ tag carries its form (w.sxf, set by sxseq); a cel without one (every shared tag: idle, run,
roll, jump, hurt ...) takes the overlay's own form. Two overlays are built from the same shape:
  wpn_gravegrinder      shared tags in SWORD form (the blade mode, where you spend most of the fight)
  wpn_gravegrinder_axe  shared tags in AXE form
Both draw the sx_ tags identically (their own forms). The game draws the _axe sheet while P.sxAxe is set (78_mech_saxe.js
redirects sheet('wpn_gravegrinder')), so a roll, a jump or a hurt in axe mode shows the axe.
The chain teeth crawl along the head's edge: w.sxph (the frame's phase) shifts the tooth pattern.

  python3 art/player_v15_saxe.py        # prints each tag's frames / wind / total against its spec
"""
import math

G = None   # gen_player, set by register()
SPEC = {}
WID, AXE_ID = "gravegrinder", "gravegrinder_axe"
SWORD, AXE = (0.0, 0.0), (1.0, 1.0)
GRIP_S, GRIP_A = 3.5, 5.0          # two-handed grip: the sword's hands close, the axe's spread along the haft
_FORM, _PH = SWORD, 0              # the form / chain phase of the cel being rasterised (set by the render hook)

IRON = ((156, 156, 172), (98, 98, 114), (54, 52, 64), (30, 28, 36))
STEEL = ((232, 236, 248), (176, 182, 202), (112, 118, 140), (66, 70, 88))
EMB = ((255, 236, 160), (255, 156, 64), (196, 72, 30), (110, 34, 24))
GOLD = ((214, 172, 92), (140, 100, 46))
HAFT = ((78, 58, 50), (40, 30, 28))


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


def _lerp(a, b, t):
    return a + (b - a) * t


def _lit(vl, hi, mid, lo, k=0.3):
    return hi if vl > k else (lo if vl < -k else mid)


# ================================================================================================ the weapon
def shp_gravegrinder(u, v, s, L):
    """Blade space (u along the haft from the hand, v across, s = lit side). Geometry from _FORM = (slide, rot)."""
    sl, rt = _FORM
    vl = v * s
    tip = L + 1.5
    hu = _lerp(4.2, tip - 5.6, sl)                 # the hinge pin: at the hilt (sword) .. under the head (axe)
    LB = tip - 6.6                                 # the sword blade's length from the pin
    th = -math.pi * rt                             # blade direction: 0 = ahead, -pi = folded back (swings out on -v)
    vh = -1.5 * math.sin(math.pi * 0.5 * rt)       # folded, it lies beside the haft
    du, dv = u - hu, v - vh
    c, sn = math.cos(th), math.sin(th)
    bu, bv = du * c + dv * sn, -du * sn + dv * c   # blade-local: bu along the blade, bv across (+bv = spine)
    # -- the hinge pin (gold), always on top
    if du * du + (v - vh * 0.5) ** 2 <= 0.8:
        return GOLD[0] if vl >= 0 else GOLD[1]
    # -- the sword blade: knuckle at the pin, broad straight body, a clipped point; edge on -bv, ember fuller
    if -1.2 <= bu <= LB:
        wk = _lerp(1.0, 0.72, rt)                  # folded, it sits slimmer against the haft
        if bu < 1.0:
            hw = 1.5 * wk
        elif bu < LB - 4.5:
            hw = 1.8 * wk
        else:
            hw = 1.8 * wk * (LB - bu) / 4.5 + 0.25
        lo, hi = -hw, hw if bu < LB - 4.5 else min(hw, 1.8 * wk - (bu - (LB - 4.5)) * 0.15)
        if lo <= bv <= hi:
            if bu < 0.4:
                return IRON[1] if vl > 0 else IRON[2]  # the knuckle
            if rt > 0.85:                          # folded away: a dark slab, edge tucked into the haft
                return STEEL[2] if bv > hi - 0.7 else STEEL[3]
            if bv < lo + 0.75:
                return STEEL[0] if vl > -0.6 else STEEL[1]   # the edge
            if bv > hi - 0.6:
                return IRON[2]                     # the spine
            if 1.6 < bu < LB - 5.0 and 0.15 <= bv <= 0.6:
                return EMB[2] if int(bu) % 4 == 1 else EMB[3]   # the ember fuller (the phial's channel)
            return STEEL[1] if vl > 0.4 else STEEL[2]
    # -- the crescent head on +v: folded flat at the hilt in sword form, opened at the haft's end in axe form
    uc = _lerp(4.6, tip - 5.0, sl)                 # head centre along the haft
    ha, hb_ = _lerp(4.4, 5.5, sl), _lerp(3.4, 7.4, sl)   # outer half-length / height: flat (sword) .. open (axe)
    eu = (u - uc) / ha
    if v >= 0.4 and abs(eu) <= 1.0:
        ro = math.hypot(eu, v / hb_)               # 1 = the cutting edge
        ia, ib = ha * 0.62, hb_ * 0.6              # the lunette cut out of the head's middle (axe only)
        ri = 9.0                                   # (lunettes tried: unreadable at this size)
        socket = abs(u - uc) <= 1.3
        if ro <= 1.0 and (ri > 1.0 or socket or v < 1.0):
            if ro > 0.8:                           # the chain: steel teeth on a dark track, crawling with the phase
                ang = math.atan2(v / hb_, eu)
                tooth = int(math.floor(ang * 5.2 - _PH * 0.75)) % 2
                if ro > 0.91:
                    return (240, 240, 248) if tooth else (118, 118, 134)
                return (150, 150, 166) if tooth else (62, 58, 70)
            if 0.68 < ro <= 0.8 and abs(eu) < 0.7 and v > 1.6:
                return EMB[3] if int(u * 1.5) % 3 else EMB[2]   # the grinding channel, ember-hot
            if ro < 0.42 and sl > 0.5 and v > 1.0:
                return IRON[2]                     # the boss's dark centre
            return _lit(vl, IRON[0], IRON[1], IRON[2])
        if ri <= 1.0 and ro <= 1.0:
            return None                            # the lunettes: see-through
    if abs(u - uc) <= 1.6 and -1.4 <= v < 0.4 and sl > 0.4:   # the head's collar round the haft
        return _lit(vl, IRON[1], IRON[2], IRON[3])
    # -- the phial housing below the pin, an ember core
    if hu - 3.4 <= u < hu - 0.9 and abs(v) <= 1.15:
        if abs(v) < 0.5 and hu - 3.0 < u < hu - 1.2:
            return EMB[0]
        return EMB[1] if vl > 0 else (EMB[3] if abs(v) > 0.8 else EMB[2])
    # -- the telescoping haft: short grip (sword) .. long haft (axe)
    he = _lerp(hu, tip - 2.0, sl)
    hb = _lerp(-3.8, -7.0, sl)
    if hb <= u < he and abs(v) <= 0.72:
        iu = int(math.floor(u))
        if iu in (-1, 5, 11) and u < hu - 3.4:
            return GOLD[0] if vl > 0 else GOLD[1]  # bands
        if u < 1.0 and (iu % 2 == 0):
            return (96, 64, 52) if vl > 0 else (52, 34, 30)   # the grip's wrap
        return HAFT[0] if vl > 0 else HAFT[1]
    if hb - 1.5 <= u < hb and abs(v) <= 1.1:       # the iron butt cap
        return IRON[1] if vl > 0 else IRON[3]
    return None


SMEAR = ((255, 236, 200), (240, 150, 70), (130, 60, 34))
SMEAR_AXE = ((255, 224, 170), (232, 112, 48), (120, 44, 26))   # the axe's arcs burn hotter and darker


def _install(g):
    g.WPN[WID] = (shp_gravegrinder, 22, 9.0, 18.0, "blade")
    g.WPN[AXE_ID] = (shp_gravegrinder, 22, 9.0, 18.0, "blade")
    g.SMEAR[WID] = SMEAR
    g.SMEAR[AXE_ID] = SMEAR_AXE
    if AXE_ID not in g.WPN_IDS:
        g.WPN_IDS.append(AXE_ID)
    if not getattr(g.Wpn, "_sx_hooked", False):   # the per-cel form: set the shape's globals just before each render
        orig = g.Wpn.render

        def render(self, kind, dust=True, extras=True):
            global _FORM, _PH
            if kind in (WID, AXE_ID):
                f = getattr(self, "sxf", None)
                _FORM = f if f is not None else (AXE if kind == AXE_ID else SWORD)
                _PH = getattr(self, "sxph", 0)
            return orig(self, kind, dust, extras)
        g.Wpn.render = render
        g.Wpn._sx_hooked = True


def sxseq(frames, form=SWORD, grip=GRIP_S, crawl=False, base=None):
    """mseq + the weapon form. A frame dict may carry sxf=(slide, rot) (else `form`; None = the overlay's own form) and
    ph=n (the chain phase; crawl=True: the frame index)."""
    forms, phs, clean = [], [], []
    for i, (p, ms) in enumerate(frames):
        forms.append(p.get("sxf", form))
        phs.append(p.get("ph", i * 2 if crawl else 0))
        clean.append(({k: v for k, v in p.items() if k not in ("sxf", "ph")}, ms))
    out = G.mseq(clean, base, grip)
    for i, (cels, _) in enumerate(out):
        j = min(i, len(frames) - 1)
        w = cels.get("Sword")
        while isinstance(w, G.RotWpn):
            w = w.inner
        if isinstance(w, G.Wpn):
            w.sxf, w.sxph = forms[j], phs[j] + (i - j) * (2 if crawl else 0)
    return out


# ================================================================================================ poses
def X(**k):
    return k


def walk_legs(i, n, stride=5.0, lift=2.4, cx=None):
    """Feet of a walk cycle: each foot is planted while it pushes back and lifts only on its forward swing."""
    cx = G.OX + 14 if cx is None else cx
    t = i / n * 2 * math.pi
    fF = (cx + stride * math.cos(t), 39 - max(0.0, -math.sin(t)) * lift)
    fB = (cx + stride * math.cos(t + math.pi), 39 - max(0.0, -math.sin(t + math.pi)) * lift)
    return dict(footF=fF, footB=fB, dy=1 if i % (n // 2) == 0 else 0)


def _carry(**k):   # axe mode at rest: the grinder laid back over the shoulder, the head riding behind the helm
    d = dict(dy=1, hand=(34, 25), ang=-154)
    d.update(k)
    return d


# ---------------------------------------------------------------- BLADE MODE (sword form)
def sx_1():  # rising edge: the blade scooped up from behind the heel, forward and up past the shoulder
    fr = [(X(dx=-1, dy=2, hand=(31, 29), ang=150, footB=(G.OX + 6, 39), flow=0.3), 70),
          (X(dx=0, dy=2, hand=(33, 30), ang=118, flow=0.5, flutter=1), 50),
          (X(dx=2, dy=1, hand=(40, 24), ang=-20, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=2, fx=[G.sw(w=0.5)]), 45),
          (X(dx=2, dy=0, hand=(38, 17), ang=-72, footF=(G.FF[0] + 2, 39), flow=0.9, flutter=3, fx=[G.sw(w=0.4)]), 50),
          (X(dx=1, hand=(35, 18), ang=-96, flow=0.5, flutter=4), 100),
          (X(hand=(35, 24), ang=-66, flow=0.3, flutter=5), 90)]
    return sxseq(tm(fr, 140, 360, 2))


def sx_2():  # falling edge: straight back down from the top of the rise, through the foe to the knee
    fr = [(X(dx=1, dy=0, hand=(34, 16), ang=-104, flow=0.5), 60),
          (X(dx=-1, dy=0, head_dx=-1, hand=(30, 12), ang=-140, footB=(G.OX + 7, 39), flow=0.3, flutter=1), 60),
          (X(dx=2, dy=1, hand=(39, 21), ang=-4, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=2, fx=[G.sw(w=0.55)]), 45),
          (X(dx=2, dy=2, hand=(38, 28), ang=44, footF=(G.FF[0] + 2, 39), flow=1.1, flutter=3, fx=[G.sw(w=0.4)]), 55),
          (X(dx=1, dy=2, hand=(36, 29), ang=40, flow=0.6, flutter=4), 100),
          (X(dy=1, hand=(35, 27), ang=-4, flow=0.3, flutter=5), 90)]
    return sxseq(tm(fr, 140, 360, 2))


def sx_3():  # double slash: a flat cut across, the wrists roll over, and a second diagonal down through the same line
    fr = [(X(dx=-1, dy=1, head_dx=-1, hand=(29, 24), ang=176, footB=(G.OX + 6, 39), flow=0.3), 70),
          (X(dx=0, dy=1, hand=(32, 25), ang=150, flow=0.5, flutter=1), 50),
          (X(dx=2, dy=1, hand=(40, 24), ang=-6, footF=(G.FF[0] + 2, 39), flow=1.1, flutter=2,
             fx=[("arc", (30, 25), 176, -6, dict(sq=0.42, w=0.6))]), 45),
          (X(dx=2, dy=0, hand=(39, 18), ang=-58, footF=(G.FF[0] + 2, 39), flow=1.0, flutter=3, fx=[G.sw(w=0.35)]), 50),
          (X(dx=3, dy=2, hand=(40, 27), ang=28, footF=(G.FF[0] + 3, 39), flow=1.2, flutter=4, fx=[G.sw(w=0.55)]), 45),
          (X(dx=2, dy=2, hand=(37, 29), ang=56, footF=(G.FF[0] + 3, 39), flow=0.7, flutter=5), 90),
          (X(dx=1, dy=1, hand=(35, 27), ang=12, flow=0.4, flutter=6), 80)]
    return sxseq(tm(fr, 160, 420, 2))


def sx_4():  # edge rush: drawn back low, a long driving step and one flat cleave through -- the blade bites, sparks
    fr = [(X(dx=-1, dy=2, head_dx=-1, hand=(29, 25), ang=-172, footB=(G.OX + 5, 39), flow=0.3), 80),
          (X(dx=-2, dy=3, head_dx=-1, hand=(27, 25), ang=178, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.2,
             flutter=1, fx=[("glint", "tip")]), 120),
          (X(dx=2, dy=3, hand=(33, 27), ang=164, footB=(G.OX + 6, 39), footF=(G.OX + 24, 39), flow=1.3, flutter=2,
             fx=[("speed", (20, 22), 4, 12)]), 40),
          (X(dx=4, dy=2, hand=(42, 25), ang=-4, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.6, flutter=3,
             fx=[("arc", (31, 26), 170, -4, dict(sq=0.4, w=0.65)), ("flare", (58, 24), 6)]), 45),
          (X(dx=4, dy=2, hand=(41, 21), ang=-40, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.3, flutter=4,
             fx=[G.sw(w=0.45)]), 55),
          (X(dx=4, dy=2, hand=(39, 19), ang=-60, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=0.8, flutter=5), 180),
          (X(dx=2, dy=1, hand=(36, 24), ang=-52, footF=(G.OX + 22, 39), flow=0.4, flutter=6), 120)]
    return sxseq(tm(fr, 220, 560, 3))


def sx_ratchet():  # ratchet cut: the blade driven in level, then sawn -- out, in, out, in -- the teeth catch three times
    def saw(dx, hx, a, f, k):
        return X(dx=dx, dy=2, hand=(hx, 25), ang=a, footB=(G.OX + 7, 39), footF=(G.OX + 24, 39), flow=1.0 + 0.2 * (k % 2),
                 flutter=k, fx=f)
    fr = [(X(dx=-1, dy=2, hand=(30, 26), ang=-8, footB=(G.OX + 6, 39), flow=0.3), 70),
          (X(dx=0, dy=2, hand=(32, 26), ang=-6, flow=0.5, flutter=1), 50),
          (saw(3, 41, -4, [("streak", 14), ("flare", "tip", 4)], 2), 45),
          (saw(2, 38, 3, [], 3), 40),
          (saw(3, 42, -6, [("flare", "tip", 4), ("embers", (54, 24), 4, 3)], 4), 45),
          (saw(2, 38, 4, [], 5), 40),
          (saw(4, 43, -10, [("flare", "tip", 6), ("embers", (55, 22), 5, 7)], 6), 50),
          (X(dx=3, dy=2, hand=(39, 21), ang=-42, footF=(G.OX + 23, 39), flow=0.8, flutter=7, fx=[G.sw(w=0.4)]), 120),
          (X(dx=1, dy=1, hand=(36, 25), ang=-44, flow=0.4, flutter=8), 130)]
    return sxseq(tm(fr, 160, 600, 2))


def sx_heavy():  # phial thrust: the blade drawn back level at the hip, then rammed out -- the phial coughs fire at the point
    fr = [(X(dx=-1, dy=2, hand=(30, 26), ang=-10, footB=(G.OX + 6, 39), flow=0.3), 80),
          (X(dx=-3, dy=3, head_dx=-1, hand=(26, 26), ang=-6, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.2, flutter=1), 140),
          (X(dx=-3, dy=3, head_dx=-1, hand=(26, 25), ang=-4, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.2, flutter=2,
             fx=[("glint", "tip")]), 60),
          (X(dx=4, dy=2, hand=(43, 24), ang=-3, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.6, flutter=3,
             fx=[("streak", 18), ("flare", "tip", 7)]), 45),
          (X(dx=4, dy=2, hand=(42, 24), ang=-3, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.2, flutter=4,
             fx=[("flare", "tip", 3), ("embers", (56, 22), 4, 5)]), 60),
          (X(dx=3, dy=2, hand=(39, 25), ang=-10, footF=(G.OX + 24, 39), flow=0.7, flutter=5), 160),
          (X(dx=1, dy=1, hand=(36, 26), ang=-30, flow=0.4, flutter=6), 140)]
    return sxseq(tm(fr, 240, 600, 3))


def sx_twist():  # ratchet twist: still buried, the blade re-driven, then wrenched up and ripped down through the wound
    F = dict(footB=(G.OX + 8, 39), footF=(G.OX + 25, 39))
    fr = [(X(dx=3, dy=2, hand=(40, 25), ang=-4, flow=0.8, **F), 60),
          (X(dx=2, dy=3, hand=(38, 26), ang=8, flow=0.5, flutter=1, fx=[("glint", "tip")], **F), 80),
          (X(dx=4, dy=2, hand=(42, 24), ang=-2, flow=1.3, flutter=2, fx=[("streak", 12), ("flare", "tip", 4)], **F), 45),
          (X(dx=4, dy=1, hand=(42, 22), ang=-36, flow=1.2, flutter=3, fx=[G.sw(w=0.4)], **F), 45),
          (X(dx=4, dy=3, hand=(42, 27), ang=26, flow=1.4, flutter=4, fx=[G.sw(w=0.5), ("flare", "tip", 6)], **F), 45),
          (X(dx=3, dy=3, hand=(39, 28), ang=46, flow=0.8, flutter=5, **F), 150),
          (X(dx=1, dy=1, hand=(36, 27), ang=4, flow=0.4, flutter=6), 130)]
    return sxseq(tm(fr, 200, 640, 2))


def sx_hook():  # hook heave: the point dipped under the foe's guard, hooked, and heaved up over the shoulder
    fr = [(X(dx=0, dy=3, hand=(33, 29), ang=40, flow=0.4), 80),
          (X(dx=1, dy=4, head_dy=1, hand=(36, 31), ang=70, footF=(G.FF[0] + 3, 39), flow=0.3, flutter=1), 120),
          (X(dx=2, dy=4, head_dy=1, hand=(39, 31), ang=24, footF=(G.FF[0] + 3, 39), flow=0.8, flutter=2,
             fx=[G.sw(w=0.3), ("dust", 50, 4)]), 60),
          (X(dx=3, dy=1, hand=(40, 22), ang=-50, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=3,
             fx=[G.sw(w=0.6), ("flare", (50, 9), 5)]), 45),
          (X(dx=2, dy=-1, hand=(36, 14), ang=-96, footB=(G.OX + 9, 38), footF=(G.FF[0] + 3, 39), flow=1.1, flutter=4,
             fx=[G.sw(w=0.45)]), 60),
          (X(dx=1, hand=(33, 14), ang=-116, flow=0.6, flutter=5), 170),
          (X(hand=(34, 21), ang=-82, flow=0.3, flutter=6), 120)]
    return sxseq(tm(fr, 220, 620, 3))


def sx_hone():  # hone (loop): crouched over it, the point ground into the floor and dragged back and forth -- sparks spray
    out = []
    for i, (hx, a, sp) in enumerate(((36, 31, 3), (37, 30, 5), (35, 32, 4), (37, 30, 6))):
        out.append((X(dx=1, dy=4, head_dy=1, hand=(hx, 30), ang=a, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39),
                      flow=0.3 + 0.1 * (i % 2), flutter=i,
                      fx=[("embers", (54 + (i % 2), 36), sp, 11 + i * 7), ("flare", (54 + (i % 2), 38), 3 + (i % 2))]), 90))
    return sxseq(out)


def sx_up():  # skyward edge: from point-down at the feet, one straight arc up over the helm
    fr = [(X(dx=0, dy=2, hand=(33, 29), ang=100, flow=0.4), 70),
          (X(dx=1, dy=3, hand=(35, 30), ang=62, footB=(G.OX + 6, 39), flow=0.3, flutter=1), 50),
          (X(dx=2, dy=0, hand=(38, 20), ang=-60, flow=1.0, flutter=2, fx=[G.sw(w=0.5)]), 45),
          (X(dx=1, dy=-1, hand=(35, 12), ang=-94, footB=(G.OX + 9, 38), flow=1.0, flutter=3, fx=[G.sw(w=0.45)]), 60),
          (X(dx=1, hand=(34, 13), ang=-100, flow=0.6, flutter=4), 120),
          (X(hand=(35, 22), ang=-72, flow=0.3, flutter=5), 90)]
    return sxseq(tm(fr, 160, 400, 2))


def sx_rollj():  # lunging edge: up out of the roll's crouch, a long low step and a flat cut through
    fr = [(X(dx=-1, dy=4, head_dy=1, hand=(31, 30), ang=165, footB=(G.OX + 5, 39), footF=(G.FF[0] + 1, 39), flow=0.6), 60),
          (X(dx=2, dy=3, hand=(36, 29), ang=150, footF=(G.OX + 23, 39), flow=1.3, flutter=1, fx=[("speed", (20, 24), 4, 12)]), 40),
          (X(dx=4, dy=2, hand=(42, 25), ang=-6, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=2,
             fx=[("arc", (31, 27), 168, -6, dict(sq=0.42, w=0.6))]), 45),
          (X(dx=4, dy=2, hand=(41, 21), ang=-42, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.2, flutter=3,
             fx=[G.sw(w=0.4)]), 55),
          (X(dx=3, dy=1, hand=(38, 21), ang=-55, footF=(G.OX + 23, 39), flow=0.7, flutter=4), 140),
          (X(dx=1, hand=(35, 25), ang=-50, flow=0.4, flutter=5), 110)]
    return sxseq(tm(fr, 140, 400, 2))


def sx_air():  # air edge: blade hoisted over the head in the hang, then brought down across the front
    A = dict(G.AIR)
    fr = [(X(dy=-2, hand=(31, 16), ang=-120, flow=0.8, **A), 70),
          (X(dx=-1, dy=-2, head_dx=-1, hand=(29, 14), ang=-152, flow=1.0, flutter=1, **A), 60),
          (X(dx=2, hand=(39, 22), ang=0, flow=1.0, flutter=2, fx=[G.sw(w=0.55)], **A), 45),
          (X(dx=2, dy=1, hand=(38, 28), ang=50, flow=1.1, flutter=3, fx=[G.sw(w=0.4)], **A), 55),
          (X(dx=1, hand=(36, 27), ang=30, flow=0.6, flutter=4, **A), 100)]
    return sxseq(tm(fr, 150, 330, 2))


def sx_down():  # pogo (both forms: the overlay's own): the weapon reversed under the feet, driven straight down
    base = dict(dy=-4, head_dy=1, **G.TUCK)
    fr = [(X(dy=-6, head_dy=0, hand=(36, 18), ang=82, slen=13, flow=0.9, footB=(G.OX + 9, 34), footF=(G.OX + 17, 34)), 60),
          (X(hand=(34, 27), ang=90, slen=15, flow=1.3, flutter=1, fx=[("streak", 10)] + G.DIVE(9)), 40),
          (X(dy=-3, hand=(34, 27), ang=90, slen=15, flow=1.5, flutter=3, fx=G.DIVE(7, 1)), 60),
          (X(hand=(34, 27), ang=90, slen=15, flow=1.3, flutter=5), 70),
          (X(dy=-3, head_dy=0, hand=(35, 25), ang=30, flow=0.7, flutter=4, **G.AIR), 70)]
    out = sxseq(tm(fr, 100, 300, 1), form=None, base=base)
    return G.cape_dive(out, [1, 2, 3])


def sx_morph():  # MORPH SLASH: hoisted overhead, the blade unlatches and swings back round its pin, the head rides up the
    # haft and locks with a clank -- and the whole grinder comes down as an axe, into the floor
    fr = [(X(dx=0, dy=1, hand=(33, 20), ang=-80, flow=0.4, sxf=SWORD), 70),
          (X(dx=-1, dy=0, hand=(30, 13), ang=-118, flow=0.3, flutter=1, sxf=(0.0, 0.3), fx=[("flare", (31, 9), 3)]), 70),
          (X(dx=-1, dy=-1, head_dx=-1, hand=(29, 11), ang=-140, flow=0.3, flutter=2, sxf=(0.15, 0.68)), 70),
          (X(dx=-2, dy=0, head_dx=-1, hand=(28, 10), ang=-158, footB=(G.OX + 6, 39), flow=0.2, flutter=3, sxf=(0.65, 0.95)), 50),
          (X(dx=-2, dy=0, head_dx=-1, hand=(28, 10), ang=-166, footB=(G.OX + 6, 39), flow=0.2, flutter=4, sxf=AXE, ph=1,
             fx=[("flare", "tip", 5), ("glint", (22, 6))]), 40),
          (X(dx=2, dy=2, hand=(39, 21), ang=-4, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=5, sxf=AXE, ph=3, fx=[G.sw(w=0.65)]), 45),
          (X(dx=3, dy=5, head_dy=1, hand=(38, 28), ang=70, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.5, flutter=6,
             sxf=AXE, ph=5, fx=[G.sw(w=0.45), ("dust", 47, 10), ("flare", (49, 36), 8)]), 60),
          (X(dx=3, dy=6, head_dy=1, hand=(38, 29), ang=74, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.8, flutter=7,
             sxf=AXE, ph=7, fx=[("dust", 47, 5)]), 220),
          (X(dx=1, dy=3, hand=(35, 27), ang=30, flow=0.4, flutter=8, sxf=AXE), 90),
          (X(dx=0, dy=2, hand=(33, 25), ang=-110, flow=0.3, flutter=9, sxf=AXE), 50)]
    return sxseq(tm(fr, 300, 700, 5), grip=GRIP_A)


# ---------------------------------------------------------------- AXE MODE (axe form, chain running)
def sx_aidle():  # axe idle (loop): the grinder over the shoulder, the chain ticking round
    return sxseq([(_carry(dy=dy, hand=(33, 24 + dy), flow=0.2 + 0.05 * i, flutter=i, footB=(G.OX + 7, 39),
                          footF=(G.FF[0] + 1, 39), ph=i), 180) for i, dy in enumerate((1, 1, 2, 2))], form=AXE, grip=GRIP_A)


def sx_awalk():  # axe walk (loop): a heavy, shortened stride under the weight on the shoulder
    out = []
    n = 8
    for i in range(n):
        lg = walk_legs(i, n, stride=4.5, lift=2.6)
        out.append((_carry(hand=(33, 24 + lg["dy"]), flow=0.5 + 0.15 * math.sin(i / n * 4 * math.pi), flutter=i, ph=i,
                           **lg), 105))
    return sxseq(out, form=AXE, grip=GRIP_A)


def sx_a1():  # axe overhead: off the shoulder, up, a held beat at the top -- and down into the floor
    fr = [(_carry(flow=0.3), 80),
          (X(dx=-1, dy=0, head_dx=-1, hand=(30, 14), ang=-150, flow=0.3, flutter=1), 120),
          (X(dx=-2, dy=-1, head_dx=-1, hand=(28, 10), ang=-165, footB=(G.OX + 6, 39), footF=(G.FF[0] + 1, 39), flow=0.2,
             flutter=2), 150),
          (X(dx=-2, dy=-1, head_dx=-1, hand=(28, 10), ang=-172, footB=(G.OX + 6, 39), footF=(G.FF[0] + 1, 39), flow=0.2,
             flutter=3, fx=[("glint", "tip")]), 140),
          (X(dx=2, dy=2, hand=(39, 21), ang=-4, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=4, fx=[G.sw(w=0.6)]), 45),
          (X(dx=3, dy=6, head_dy=1, hand=(38, 28), ang=72, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=1.5, flutter=5,
             fx=[G.sw(w=0.45), ("dust", 47, 10), ("flare", (49, 36), 7)]), 60),
          (X(dx=3, dy=6, head_dy=1, hand=(38, 29), ang=76, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39), flow=0.8, flutter=6,
             fx=[("dust", 47, 5), ("embers", (49, 33), 4, 3)]), 280),
          (X(dx=2, dy=4, hand=(36, 28), ang=50, flow=0.4, flutter=7), 160),
          (_carry(dx=0, hand=(33, 24), ang=-118, flow=0.3, flutter=8, behind=False), 140)]
    return sxseq(tm(fr, 420, 920, 4), form=AXE, grip=GRIP_A, crawl=True)


def sx_a2():  # wild swing: wrenched out of the floor and slung all the way back, then round, flat and wide
    fr = [(X(dx=2, dy=4, hand=(36, 28), ang=50, flow=0.4), 80),
          (X(dx=-1, dy=2, head_dx=-1, hand=(27, 25), ang=-176, footB=(G.OX + 5, 39), flow=0.6, flutter=1,
             fx=[G.sw(w=0.3)]), 160),
          (X(dx=-2, dy=3, head_dx=-1, hand=(26, 26), ang=172, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.3,
             flutter=2, fx=[("glint", "tip")]), 160),
          (X(dx=3, dy=2, hand=(41, 25), ang=-4, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.6, flutter=3,
             fx=[("arc", (30, 26), 174, -4, dict(sq=0.4, w=0.7)), ("flare", (58, 24), 6)]), 45),
          (X(dx=3, dy=2, hand=(40, 21), ang=-45, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=1.3, flutter=4,
             fx=[G.sw(w=0.45)]), 60),
          (X(dx=3, dy=2, hand=(37, 18), ang=-76, footB=(G.OX + 8, 39), footF=(G.OX + 25, 39), flow=0.8, flutter=5), 240),
          (X(dx=1, dy=1, hand=(34, 21), ang=-110, footF=(G.OX + 22, 39), flow=0.4, flutter=6), 150),
          (_carry(flow=0.3, flutter=7), 110)]
    return sxseq(tm(fr, 400, 900, 3), form=AXE, grip=GRIP_A, crawl=True)


def sx_a3():  # grinder sweep: brought down in front and leaned on -- the chain chews through, five bites -- then ripped out
    def bite(dx, dy, hx, hy, a, k, sz):
        return X(dx=dx, dy=dy, hand=(hx, hy), ang=a, footB=(G.OX + 7, 39), footF=(G.OX + 24, 39), flow=1.0 + 0.2 * (k % 2),
                 flutter=k, fx=[("flare", "tip", sz), ("embers", (52 + k % 2, 30), 4, k * 5)])
    fr = [(X(dx=0, dy=1, hand=(33, 20), ang=-120, flow=0.4), 80),
          (X(dx=-1, dy=0, head_dx=-1, hand=(29, 13), ang=-150, flow=0.3, flutter=1), 130),
          (X(dx=1, dy=2, hand=(36, 20), ang=-60, flow=0.9, flutter=2, fx=[G.sw(w=0.4)]), 60),
          (bite(3, 3, 40, 25, 8, 3, 5), 50),
          (bite(3, 4, 41, 26, 12, 4, 4), 60),
          (bite(3, 3, 40, 25, 9, 5, 5), 60),
          (bite(4, 4, 41, 26, 13, 6, 4), 60),
          (X(dx=4, dy=3, hand=(42, 24), ang=-20, footB=(G.OX + 7, 39), footF=(G.OX + 24, 39), flow=1.4, flutter=7,
             fx=[G.sw(w=0.55), ("flare", "tip", 7)]), 60),
          (X(dx=3, dy=2, hand=(39, 19), ang=-62, footF=(G.OX + 23, 39), flow=0.8, flutter=8), 230),
          (_carry(dx=1, hand=(34, 23), ang=-112, flow=0.4, flutter=9, behind=False), 160)]
    return sxseq(tm(fr, 360, 1100, 3), form=AXE, grip=GRIP_A, crawl=True)


def sx_arev():  # rev thrust: swung down level, the head held out at the foe with the chain screaming -- four bites
    def rev(dx, hx, hy, a, k, sz):
        return X(dx=dx, dy=2, hand=(hx, hy), ang=a, footB=(G.OX + 7, 39), footF=(G.OX + 25, 39), flow=1.0 + 0.2 * (k % 2),
                 flutter=k, fx=[("flare", "tip", sz)])
    fr = [(_carry(flow=0.3), 70),
          (X(dx=-2, dy=2, head_dx=-1, hand=(27, 25), ang=-4, footB=(G.OX + 5, 39), flow=0.3, flutter=1), 140),
          (X(dx=-2, dy=2, head_dx=-1, hand=(27, 25), ang=-4, footB=(G.OX + 5, 39), flow=0.3, flutter=2,
             fx=[("glint", "tip")]), 90),
          (X(dx=3, dy=2, hand=(40, 25), ang=-4, footB=(G.OX + 7, 39), footF=(G.OX + 25, 39), flow=1.5, flutter=3,
             fx=[("streak", 12), ("flare", "tip", 5)]), 45),
          (rev(3, 41, 24, -6, 4, 4), 60),
          (rev(3, 40, 25, -3, 5, 5), 60),
          (rev(4, 42, 24, -6, 6, 6), 60),
          (X(dx=3, dy=2, hand=(38, 25), ang=-20, footF=(G.OX + 23, 39), flow=0.7, flutter=7), 200),
          (_carry(dx=1, hand=(34, 24), ang=-100, flow=0.4, flutter=8, behind=False), 170)]
    return sxseq(tm(fr, 300, 900, 3), form=AXE, grip=GRIP_A, crawl=True)


def _grind(i, legs=None):
    d = X(dx=3, dy=2, hand=(40 + (i % 2), 25 - (i % 2)), ang=-4 - 3 * (i % 2), footB=(G.OX + 7, 39), footF=(G.OX + 24, 39),
          flow=0.9 + 0.2 * (i % 2), flutter=i, ph=i * 2,
          fx=[("flare", "tip", 4 + 2 * (i % 2)), ("embers", (55, 24), 4, 3 + i * 9)])
    if legs:
        d.update(footB=legs["footB"], footF=legs["footF"])
    return d


def sx_grind():  # chainsaw grind (hold, loop): the head held into the foe, the body shaking with it, sparks pouring
    return sxseq([(_grind(i), 80) for i in range(4)], form=AXE, grip=GRIP_A)


def sx_grindw():  # chainsaw grind while walking (loop): the same hold, short planted steps under it
    out = []
    for i in range(8):
        lg = walk_legs(i, 8, stride=3.0, lift=1.8, cx=G.OX + 16)
        out.append((_grind(i, lg), 80))
    return sxseq(out, form=AXE, grip=GRIP_A)


def sx_rip():  # ripping heave: the head dropped to the floor in front, then torn up through the foe and over -- launches
    fr = [(X(dx=3, dy=2, hand=(39, 25), ang=-6, flow=0.6), 80),
          (X(dx=1, dy=4, head_dy=1, hand=(36, 30), ang=40, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.3,
             flutter=1), 150),
          (X(dx=1, dy=5, head_dy=1, hand=(36, 31), ang=52, footB=(G.OX + 5, 39), footF=(G.FF[0] + 2, 39), flow=0.2, flutter=2,
             fx=[("dust", 49, 4), ("glint", "tip")]), 190),
          (X(dx=3, dy=1, hand=(40, 22), ang=-40, footF=(G.FF[0] + 4, 39), flow=1.5, flutter=3,
             fx=[G.sw(w=0.65), ("flare", (52, 10), 7), ("dust", 50, 8)]), 45),
          (X(dx=3, dy=-2, hand=(37, 12), ang=-90, footB=(G.OX + 9, 37), footF=(G.FF[0] + 4, 38), flow=1.4, flutter=4,
             fx=[G.sw(w=0.5)]), 60),
          (X(dx=2, dy=-1, hand=(33, 11), ang=-125, footF=(G.FF[0] + 3, 39), flow=0.8, flutter=5), 260),
          (X(dx=1, dy=1, hand=(33, 18), ang=-135, flow=0.4, flutter=6), 200),
          (_carry(flow=0.3, flutter=7), 100)]
    return sxseq(tm(fr, 420, 1000, 3), form=AXE, grip=GRIP_A, crawl=True)


def sx_release():  # FULL RELEASE: crouched, the phial lit; a lunge and the head bites in -- eight grinding bites, the phial
    # bursts through the foe, and the spent grinder folds back into the blade
    def bite(k, sz):
        return X(dx=4, dy=2, hand=(41 + (k % 2), 25 - (k % 2)), ang=-3 - 3 * (k % 2), footB=(G.OX + 9, 39),
                 footF=(G.OX + 26, 39), flow=1.0 + 0.3 * (k % 2), flutter=k, ph=k * 2,
                 fx=[("flare", "tip", sz), ("embers", (56, 23), 5, k * 7)])
    fr = [(_carry(flow=0.3), 80),
          (X(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=-6, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.3, flutter=1,
             fx=[("glint", "tip")]), 160),
          (X(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=-6, footB=(G.OX + 4, 39), footF=(G.FF[0] + 1, 39), flow=0.3, flutter=2,
             fx=[("flare", (36, 25), 4)]), 150),
          (X(dx=2, dy=2, hand=(36, 25), ang=-4, footB=(G.OX + 6, 39), footF=(G.OX + 24, 39), flow=1.5, flutter=3,
             fx=[("speed", (20, 22), 5, 14)]), 60),
          (X(dx=4, dy=2, hand=(42, 24), ang=-4, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.6, flutter=4, ph=0,
             fx=[("flare", "tip", 7), ("streak", 10)]), 50)]
    fr += [(bite(k, 4 + 2 * (k % 2)), 60) for k in range(1, 8)]
    fr += [(X(dx=4, dy=2, hand=(42, 23), ang=-12, footB=(G.OX + 9, 39), footF=(G.OX + 26, 39), flow=1.8, flutter=8, ph=16,
              fx=[("flare", "tip", 11), ("rings", (54, 24), (5, 9))]), 50),
           (X(dx=3, dy=2, hand=(39, 24), ang=-40, footF=(G.OX + 24, 39), flow=1.0, flutter=9, sxf=(1.0, 0.6),
              fx=[("embers", (46, 18), 5, 3)]), 120),
           (X(dx=2, dy=1, hand=(37, 24), ang=-60, footF=(G.OX + 22, 39), flow=0.6, flutter=10, sxf=(0.4, 0.2)), 160),
           (X(dx=1, dy=1, hand=(35, 26), ang=-55, flow=0.3, flutter=11, sxf=SWORD), 200)]
    return sxseq(tm(fr, 500, 1500, 4), form=AXE, grip=GRIP_A)


def sx_unmorph():  # MORPH BACK: the axe swung low, and as it comes up the blade jack-knifes forward out of the haft -- a rising cut
    fr = [(X(dx=0, dy=2, hand=(32, 27), ang=150, flow=0.4, sxf=AXE), 80),
          (X(dx=1, dy=3, hand=(34, 29), ang=128, footB=(G.OX + 6, 39), flow=0.3, flutter=1, sxf=(1.0, 0.8),
             fx=[("glint", (30, 31))]), 90),
          (X(dx=1, dy=3, hand=(35, 29), ang=108, footB=(G.OX + 6, 39), flow=0.5, flutter=2, sxf=(0.6, 0.42)), 90),
          (X(dx=3, dy=1, hand=(40, 23), ang=-30, footF=(G.FF[0] + 3, 39), flow=1.3, flutter=3, sxf=(0.12, 0.06),
             fx=[G.sw(w=0.55), ("flare", "tip", 5)]), 45),
          (X(dx=2, dy=-1, hand=(37, 15), ang=-85, footB=(G.OX + 9, 38), flow=1.0, flutter=4, sxf=SWORD, fx=[G.sw(w=0.4)]), 60),
          (X(dx=1, hand=(34, 15), ang=-100, flow=0.6, flutter=5, sxf=SWORD), 160),
          (X(hand=(35, 23), ang=-70, flow=0.3, flutter=6, sxf=SWORD), 115)]
    return sxseq(tm(fr, 260, 620, 3), grip=GRIP_S)


def sx_vent():  # VENTED: the gauge ran dry -- the phial blows steam, the axe sags and folds shut, the knight staggers under it
    fr = [(X(dx=1, dy=2, hand=(36, 27), ang=20, flow=0.6, sxf=AXE, fx=[("embers", (38, 22), 6, 2), ("flare", (34, 24), 4)]), 100),
          (X(dx=0, dy=3, head_dy=1, hand=(34, 29), ang=40, footB=(G.OX + 6, 39), flow=0.4, flutter=1, sxf=(1.0, 0.7),
             fx=[("embers", (36, 24), 7, 5)]), 100),
          (X(dx=-1, dy=4, head_dy=1, hand=(32, 30), ang=60, footB=(G.OX + 5, 39), flow=0.3, flutter=2, sxf=(0.5, 0.3)), 120),
          (X(dx=-1, dy=4, head_dy=1, hand=(32, 30), ang=66, footB=(G.OX + 5, 39), flow=0.2, flutter=3, sxf=SWORD), 140),
          (X(dy=2, hand=(34, 28), ang=10, flow=0.3, flutter=4, sxf=SWORD), 140)]
    return sxseq(fr, grip=GRIP_S)


def sx_astep():  # heavy sidestep (axe mode's L): a low, short shuffle under the weight, the grinder hugged in
    return sxseq([(_carry(dx=0, dy=3, hand=(31, 26), ang=-150, footB=(G.OX + 6, 39), footF=(G.FF[0] + 2, 39), flow=0.4), 80),
                  (_carry(dx=2, dy=2, hand=(33, 25), ang=-150, footB=(G.OX + 6, 39), footF=(G.OX + 25, 39), flow=1.2, flutter=1,
                          fx=[("speed", (18, 26), 3, 10)]), 100),
                  (_carry(dx=3, dy=3, hand=(34, 26), ang=-148, footB=(G.OX + 11, 39), footF=(G.OX + 24, 39), flow=1.0,
                          flutter=2), 100),
                  (_carry(dx=2, dy=2, hand=(33, 25), ang=-145, footB=(G.OX + 10, 39), footF=(G.FF[0] + 1, 39), flow=0.6,
                          flutter=3), 120),
                  (_carry(flow=0.3, flutter=4), 120)], form=AXE, grip=GRIP_A)


def sx_aair():  # falling cleave (axe, air J): heaved over the head in the hang, then chopped down in front as you drop
    A = dict(G.AIR)
    fr = [(X(dy=-2, hand=(30, 14), ang=-140, flow=0.8, **A), 90),
          (X(dx=-1, dy=-3, head_dx=-1, hand=(28, 10), ang=-165, flow=1.0, flutter=1, fx=[("glint", "tip")], **A), 110),
          (X(dx=2, hand=(39, 22), ang=0, flow=1.0, flutter=2, fx=[G.sw(w=0.6)], **A), 45),
          (X(dx=2, dy=1, hand=(37, 29), ang=68, flow=1.2, flutter=3, fx=[G.sw(w=0.45), ("flare", "tip", 5)], **A), 60),
          (X(dx=1, hand=(36, 28), ang=60, flow=0.7, flutter=4, **A), 150),
          (X(dy=-1, hand=(34, 24), ang=-40, flow=0.4, flutter=5, **A), 100)]
    return sxseq(tm(fr, 200, 520, 2), form=AXE, grip=GRIP_A, crawl=True)


def sx_aup():  # rising grinder (axe, up J): the head dragged up off the floor and over, chain howling
    fr = [(X(dx=0, dy=2, hand=(33, 28), ang=120, flow=0.4), 80),
          (X(dx=1, dy=4, head_dy=1, hand=(35, 30), ang=82, footB=(G.OX + 5, 39), flow=0.3, flutter=1, fx=[("glint", "tip")]), 140),
          (X(dx=2, dy=0, hand=(38, 20), ang=-60, flow=1.3, flutter=2, fx=[G.sw(w=0.6), ("flare", (44, 3), 6)]), 45),
          (X(dx=1, dy=-2, hand=(35, 11), ang=-95, footB=(G.OX + 9, 37), flow=1.2, flutter=3, fx=[G.sw(w=0.45)]), 60),
          (X(dx=1, hand=(33, 11), ang=-112, flow=0.6, flutter=4), 220),
          (_carry(flow=0.3, flutter=5), 150)]
    return sxseq(tm(fr, 300, 760, 2), form=AXE, grip=GRIP_A, crawl=True)


# ================================================================================================ registry
def register(g):
    global G
    G = g
    _install(g)
    S = g.settled
    A = lambda a, b=None: (a, a if b is None else b)
    E = []

    def add(tag, fn, wind=None, total=None, active=None, settle=True, **meta):
        if wind is not None:
            SPEC[tag] = (wind, total)
        if active is not None:
            meta["active"] = active
        E.append((tag, S(fn) if settle else fn, meta))

    # blade mode (settles toward the sword idle)
    add("sx_1", sx_1, 140, 360, A(2, 3), up=True)
    add("sx_2", sx_2, 140, 360, A(2, 3))
    add("sx_3", sx_3, 160, 420, A(2, 4), hits=[2, 4])
    add("sx_4", sx_4, 220, 560, A(3, 4), x0=-6)
    add("sx_ratchet", sx_ratchet, 160, 600, A(2, 6), hits=[2, 4, 6], x0=0)
    add("sx_heavy", sx_heavy, 240, 600, A(3, 4), x0=0)
    add("sx_twist", sx_twist, 200, 640, A(2, 4), hits=[2, 4], x0=0)
    add("sx_hook", sx_hook, 220, 620, A(3, 4), up=True)
    add("sx_hone", sx_hone, settle=False)
    add("sx_up", sx_up, 160, 400, A(2, 3), up=True)
    add("sx_rollj", sx_rollj, 140, 400, A(2, 3), x0=-4)
    add("sx_air", sx_air, 150, 330, A(2, 3))
    add("sx_down", sx_down, 100, 300, A(1, 3), settle=False, down=True)
    add("sx_morph", sx_morph, 300, 700, A(5, 6), settle=False)
    add("sx_unmorph", sx_unmorph, 260, 620, A(3, 4), up=True)
    add("sx_vent", sx_vent, settle=False)
    # axe mode (end on the shoulder carry: no settle toward the sword idle)
    add("sx_aidle", sx_aidle, settle=False)
    add("sx_awalk", sx_awalk, settle=False)
    add("sx_a1", sx_a1, 420, 920, A(4, 5), settle=False)
    add("sx_a2", sx_a2, 400, 900, A(3, 4), settle=False, x0=-8)
    add("sx_a3", sx_a3, 360, 1100, A(3, 7), hits=[3, 4, 5, 6, 7], settle=False)
    add("sx_arev", sx_arev, 300, 900, A(3, 6), hits=[3, 4, 5, 6], settle=False, x0=0)
    add("sx_grind", sx_grind, settle=False)
    add("sx_grindw", sx_grindw, settle=False)
    add("sx_rip", sx_rip, 420, 1000, A(3, 4), settle=False, up=True)
    add("sx_release", sx_release, 500, 1500, A(4, 12), hits=list(range(4, 13)), settle=False, x0=0)
    add("sx_astep", sx_astep, settle=False)
    add("sx_aair", sx_aair, 200, 520, A(2, 3), settle=False)
    add("sx_aup", sx_aup, 300, 760, A(2, 3), settle=False, up=True)
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    mod = sys.modules.get("player_v15_saxe")
    fns = dict(GP.ANIMS)
    print(f"{'tag':14} {'frames':>6} {'wind':>5} {'total':>5}   {'spec':>9}   ok")
    for t, (w, tot0) in mod.SPEC.items():
        fr = list(fns[t]())
        ms = [m for _, m in fr]
        act = GP.ACTIVE.get(t)
        wind = sum(ms[:act[0]]) if act else None
        tot = sum(ms)
        print(f"{t:14} {len(fr):6} {wind:>5} {tot:5}   {'%d/%d' % (w, tot0):>9}   {'OK' if (wind, tot) == (w, tot0) else 'MISMATCH'}")
