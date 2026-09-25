"""Rig layer for Cindervane, the Last Drake (Tempest Spire main boss).

The drawing code is the APPROVED concept generator art/concepts/gen_cindervane.py (imported read-only): one swept
spine tube (tail + torso + neck) with a shingled scute field in arc space, armoured IK legs, torn wing-arms and a
faceted horned head, lightning path-traced through the plate seams.  The concept keys each pose by hand as absolute
joint lists; this module turns a small set of animatable controls into those dicts so poses can be interpolated
into smooth animation:

    hip, sh            torso ends (spine keys 7 and 9); belly key 8 = midpoint lifted by `sag`
    tail               7 absolute segment angles (deg, y down) walking back from the hip to the club
    head, head_ang     head position + facing; the neck (keys 10..15) is a constant-length cubic from the shoulder
    neck_a0            departure angle of the neck at the shoulder (deg)
    feet / hands       hind feet + fore hands (ground contacts); knees / elbows solved by 2-bone IK
    wings              far / near wing joint sets RELATIVE to the shoulder point
Faces RIGHT.  Frame 288x176, ground line y = GROUND.
"""
import copy, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "concepts"))
import gen_cindervane as CV  # noqa: E402  (read-only reuse of the approved concept's drawing code)

W, H = CV.W, CV.H
GROUND = 168

RAD = [(0.8, 0.8), (2.0, 2.0), (3.3, 3.3), (4.8, 4.8), (6.2, 6.2), (8.0, 8.0), (11.0, 11.5), (15.0, 16.0),
       (19.0, 20.5), (20.0, 21.0), (16.5, 17.5), (13.0, 13.0), (11.2, 11.0), (10.0, 9.8), (9.0, 8.8), (8.0, 8.0)]
TAIL_LEN = [20.1, 21.1, 22.4, 22.6, 22.2, 15.6, 17.0]          # hip -> ... -> club
TAIL_IDLE = [153.4, 148.6, 153.4, 167.2, 187.8, 225.0, 273.4]
NECK_SEG = [16.1, 13.9, 13.4, 11.7, 10.2, 9.0]
NECK_L = sum(NECK_SEG)
HIP_OFF = [(-16, 2), (-4, 6)]            # far, near hind-leg hips relative to the spine hip
SH_OFF = [(15, 6), (3, 12)]              # far, near fore-leg shoulders relative to the spine shoulder
LEG_SZ = [1.0, 1.08]
LEG_BIAS = [-1.0, 1.2]


def v(p):
    return np.array(p, float)


def dirv(deg):
    return np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])


def bez3(p0, p1, p2, p3, n=120):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def curve_len(pts):
    return float(np.sum(np.hypot(*np.diff(pts, axis=0).T)))


def neck_points(S, Hd, a0, a1, L=NECK_L):
    """Cubic from S leaving at angle a0, arriving at Hd along a1 (head direction); handle length solved so the
    arc length is L.  Returns the 6 neck keys (10..15) at the concept's segment proportions."""
    S, Hd = v(S), v(Hd)
    d0, d1 = dirv(a0), dirv(a1)
    lo, hi = 0.0, 160.0
    if curve_len(bez3(S, S, Hd, Hd)) >= L:
        m = 0.0
    else:
        for _ in range(40):
            m = (lo + hi) / 2
            if curve_len(bez3(S, S + d0 * m, Hd - d1 * m, Hd)) < L:
                lo = m
            else:
                hi = m
    pts = bez3(S, S + d0 * m, Hd - d1 * m, Hd, 400)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    tot = cum[-1]
    out = []
    acc = 0.0
    for s in NECK_SEG:
        acc += s
        f = acc / NECK_L * tot
        i = int(np.clip(np.searchsorted(cum, f), 1, len(cum) - 1))
        k = (f - cum[i - 1]) / max(1e-6, cum[i] - cum[i - 1])
        out.append(pts[i - 1] + (pts[i] - pts[i - 1]) * k)
    return out


def ik2(a, b, L1, L2, pref):
    return CV.ik2(a, b, L1, L2, pref)


# ------------------------------------------------------------------ default controls (reproduce concept "idle")
WING_IDLE = [
    dict(shoulder=(3, -10), elbow=(-5, -42), wrist=(13, -76), thumb=(3, -4),
         tips=[(-35, -98), (-53, -80), (-51, -56), (-29, -36)], root=(-3, -16), bends=[3, 3, 3, 2.5],
         sag=[0.22, 0.24, 0.24, 0.3], bias=-2.0, seed=31, nholes=3, tears=3, bolts=1, fore_r=(2.8, 2.0),
         hum_r=(4.4, 2.6), lead_spikes=3),
    dict(shoulder=(-13, -8), elbow=(-33, -38), wrist=(-15, -74), thumb=(3, -4),
         tips=[(-67, -88), (-85, -66), (-81, -40), (-59, -20)], root=(-31, -6), bends=[3, 3, 3, 2.5],
         sag=[0.22, 0.24, 0.24, 0.3], bias=0.0, seed=33, nholes=5, tears=4, bolts=2),
]


def base():
    return dict(
        hip=(122, 130), sh=(163, 122), sag=2.0,
        tail=list(TAIL_IDLE),
        head=(234, 141), head_ang=4.0, neck_a0=6.0, jaw=0.0, head_sc=1.12, throat=0, mouth_glow=0, crown=1.0,
        feet=[(113, 164), (129, 165)], hands=[(199, 163), (185, 165)],
        wrist_off=[(-7, -5), (-7, -5)], claw_dir=[(1, 0.45), (1, 0.45)], grip=[1.0, 1.0],
        wings=copy.deepcopy(WING_IDLE),
        spike_k=1.2, fan_k=1.3, fan=[-165, -135, -105, 170, 140],
        seam_bolts=(9, 1), wing_bolts=3,
    )


def build(R):
    """Rig controls -> concept pose dict (consumed by render())."""
    hip, sh = v(R["hip"]), v(R["sh"])
    # tail: walk back from the hip
    tail = [hip]
    for L, a in zip(TAIL_LEN, R["tail"]):
        p = tail[-1] + dirv(a) * L
        tail.append(p)
    tail = tail[1:][::-1]                    # key 0 = club ... key 6 = tail base
    for p in tail:                            # never through the floor
        p[1] = min(p[1], GROUND - 3)
    d = sh - hip
    n_up = np.array([d[1], -d[0]]) / (np.hypot(*d) or 1)
    belly = (hip + sh) / 2 + n_up * R.get("sag", 2.0)
    neck = neck_points(sh, R["head"], R["neck_a0"], R["head_ang"])
    keys = list(tail) + [hip, belly, sh] + neck
    spine = [(float(p[0]), float(p[1]), RAD[i][0], RAD[i][1]) for i, p in enumerate(keys)]
    legs = []
    for k in range(2):
        sz = LEG_SZ[k]
        hp = hip + v(HIP_OFF[k])
        ft = v(R["feet"][k])
        an = ft + v(R.get("ankle_off", [(-9, -6), (-9, -6)])[k]) * sz
        kn = ik2(hp, an, 22.8 * sz, 23.3 * sz, (1, 0))
        legs.append(dict(hip=tuple(hp), knee_at=tuple(kn), ankle=tuple(an), foot=tuple(ft), bias=LEG_BIAS[k], sz=sz))
    arms = []
    for k in range(2):
        sz = [0.95, 1.08][k]
        sp = sh + v(SH_OFF[k])
        hd = v(R["hands"][k])
        wr = hd + v(R["wrist_off"][k]) * sz
        el = ik2(sp, wr, 20.9 * sz, 22.4 * sz, R.get("elbow_pref", (-1, 0.3)))
        arms.append(dict(shoulder=tuple(sp), elbow=tuple(el), wrist=tuple(wr), hand=tuple(hd),
                         claw_dir=tuple(R["claw_dir"][k]), bias=[-1.0, 1.2][k], sz=sz, grip=R["grip"][k]))
    wings = []
    for wg in R["wings"]:
        o = dict(wg)
        for key in ("shoulder", "elbow", "wrist", "root"):
            o[key] = tuple(sh + v(wg[key]))
        o["tips"] = [tuple(sh + v(t)) for t in wg["tips"]]
        for key in ("seed", "nholes", "tears", "bolts", "lead_spikes"):
            if key in o:
                o[key] = int(round(o[key]))
        wings.append(o)
    P = dict(ground=GROUND, spine=spine, marks=dict(s_hip=tuple(hip), s_shoulder=tuple(sh)),
             throat=int(round(R.get("throat", 0))), spike_k=R.get("spike_k", 1.2), fan_k=R.get("fan_k", 1.3), fan=R.get("fan"),
             head=tuple(neck[-1]), head_ang=R["head_ang"], jaw=R.get("jaw", 0), mouth_glow=int(round(R.get("mouth_glow", 0))),
             head_sc=R.get("head_sc", 1.12), crown=R.get("crown", 1.0),
             legs=legs, arms=arms, wings=wings, seam_bolts=tuple(R.get("seam_bolts", (9, 1))),
             wing_bolts=R.get("wing_bolts", 3))
    if P["fan"] is None:
        P.pop("fan")
    return P


# ------------------------------------------------------------------ interpolation
def lerp_any(a, b, t):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        r = [lerp_any(x, y, t) for x, y in zip(a, b)]
        return tuple(r) if isinstance(a, tuple) else r
    if isinstance(a, dict) and isinstance(b, dict):
        return {k: (lerp_any(a[k], b[k], t) if k in b else a[k]) for k in a}
    return a if t < 0.5 else b


def lerp_angles(a, b, t):
    """Tail angle lists: interpolate along the short way round."""
    out = []
    for x, y in zip(a, b):
        d = (y - x + 180) % 360 - 180
        out.append(x + d * t)
    return out


def mix(A, B, t):
    R = lerp_any(A, B, t)
    R["tail"] = lerp_angles(A["tail"], B["tail"], t)
    # keep integer-valued knobs integral and seeds fixed
    for k in ("seam_bolts",):
        R[k] = A[k] if t < 0.5 else B[k]
    for i, wg in enumerate(R["wings"]):
        for k in ("seed", "nholes", "tears", "bolts", "lead_spikes"):
            if k in A["wings"][i]:
                wg[k] = A["wings"][i][k]
    return R


def ease(t, kind="io"):
    if kind == "in":
        return t * t
    if kind == "out":
        return 1 - (1 - t) ** 2
    if kind == "lin":
        return t
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ transforms used by the pose library
def shifted(R, dx, dy, feet=False):
    """Move the whole body (not the planted feet/hands unless feet=True)."""
    R = copy.deepcopy(R)
    R["hip"] = (R["hip"][0] + dx, R["hip"][1] + dy)
    R["sh"] = (R["sh"][0] + dx, R["sh"][1] + dy)
    R["head"] = (R["head"][0] + dx, R["head"][1] + dy)
    if feet:
        R["feet"] = [(x + dx, y + dy) for x, y in R["feet"]]
        R["hands"] = [(x + dx, y + dy) for x, y in R["hands"]]
    return R


def rot_pts(pts, deg, sx=1.0, sy=1.0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(sx * (x * c - y * s), sy * (x * s + y * c)) for x, y in pts]


def wing_xform(wg, deg=0.0, sx=1.0, sy=1.0, about="shoulder", flipbend=False):
    """Rotate / squash a wing joint set around its own shoulder."""
    wg = copy.deepcopy(wg)
    o = v(wg["shoulder"])
    for key in ("elbow", "wrist", "root"):
        p = v(wg[key]) - o
        q = rot_pts([p], deg, sx, sy)[0]
        wg[key] = (o[0] + q[0], o[1] + q[1])
    wg["tips"] = [tuple(o + v(rot_pts([v(t) - o], deg, sx, sy)[0])) for t in wg["tips"]]
    if flipbend:
        wg["bends"] = [-b for b in wg["bends"]]
    return wg


def render(P, phase=1, seed=5, storm=1.0):
    """render_pose from the concept, without sky bolts / breath beam.  Returns (RGBA image, info)."""
    C = CV.Canvas()
    fxl = CV.FX()
    rng = np.random.RandomState(seed)
    tb = CV.body_tube(P)
    for k, (x, y) in P["marks"].items():
        P[k] = CV.arc_of(tb, x, y)
    P["s_head"] = tb.length
    fw, nw = P["wings"]
    fl, nl = P["legs"]
    fa, na = P["arms"]
    fi = CV.wing(C, fw, bias=fw.get("bias", -1.4), far=True, seed=fw.get("seed", 1))
    CV.hind_leg(C, fl, bias=fl["bias"], far=1.0)
    CV.fore_leg(C, fa, bias=fa["bias"], far=1.0)
    dtips = CV.paint_dorsal(C, P, tb)
    ttips = CV.paint_tail_club(C, P, tb)
    CV.paint_body(C, P, tb)
    CV.hind_leg(C, nl, bias=nl["bias"])
    CV.head(C, fxl, P)
    CV.fore_leg(C, na, bias=na["bias"])
    ni = CV.wing(C, nw, bias=nw.get("bias", 0), far=False, seed=nw.get("seed", 2))
    nb, br = P.get("seam_bolts", (8, 1))
    nb = int(round(nb * storm))
    CV.seam_lightning(C, rng, nb, strength=phase, branches=br)
    CV.membrane_lightning(C, fi, rng, n=int(round(fw.get("bolts", P.get("wing_bolts", 3)) * storm)), strength=phase)
    CV.membrane_lightning(C, ni, rng, n=int(round(P.get("wing_bolts", 3) * storm)), strength=phase)
    img = C.render()
    if phase >= 2:
        CV.arcs(fxl, C, dtips, rng, 7, reach=(5, 12))
        CV.arcs(fxl, C, ttips, rng, 3, reach=(5, 10))
        wt = [t for info in (fi, ni) for t in info["tips"]] + [fi["wrist"], ni["wrist"]]
        CV.arcs(fxl, C, wt, rng, 4, reach=(6, 13))
    img.alpha_composite(fxl.image())
    info = dict(tb=tb, mouth=P.get("_mouth"), filled=C.filled(), mat=C.mat, dtips=dtips, ttips=ttips)
    return img, info
