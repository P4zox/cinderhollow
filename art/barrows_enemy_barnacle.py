"""db_barnacle -- the barnacle crawler (48x32, anchor [24,32], faces right, feet on the bottom row).
See gen_barrows_enemies.py.

A low, sleek crab-thing that wears a drowned corpse's ribcage as its shell: a long tapered carapace of pale
drowned bone with dark rib grooves (teal bioluminescent specks glinting in the cracks), a vertebral ridge along
the top, the skull fused at the front as a face-plate, barnacles crusting the back; six thin jointed dark legs
and two long pale bone pincers in front. Tags: idle(4) crawl(6) snap(9) shell(4) hurt(2) death(6).
"""
import math
import enemy_kit as K
from enemy_kit import Layer, FXLayer, Rig, ip, line, lerp, add, sub, ik, hash01, n_dome, n_plate, n_capsule, \
    poly_mask, dirv, mask_disc
import spire_enemy_kit as S
from spire_enemy_kit import mk, madd
import barrows_enemy_kit as B

SPEC = dict(idle=4, crawl=6, snap=9, shell=4, hurt=2, death=6)
LAYERS = ["LegsB", "PincerB", "Legs", "Body", "Shell", "Pincer", "FX"]
FLOOR = 31
L1, L2 = 7.5, 13.0         # leg femur / tibia (long, spidery)
A1, A2 = 5.4, 6.0          # pincer upper arm / forearm

# shell outline (model coords, standing pose)
SHELL = [(6.6, 19.6), (10.4, 17.4), (15.6, 15.2), (22.0, 14.2), (28.0, 14.3), (32.2, 15.2), (35.2, 16.6),
         (37.2, 18.4), (37.8, 20.0), (36.4, 21.6), (31.0, 22.2), (22.0, 22.5), (14.0, 21.8), (8.6, 20.6)]
HIPS_N = [(31.0, 20.0), (24.0, 20.6), (17.0, 20.0)]         # near legs: front, mid, rear
HIPS_F = [(32.4, 19.4), (25.4, 19.8), (18.4, 19.4)]
FEET = [41.6, 33.0, 6.2]                                     # neutral foot x (near side); far = +1.6
SH_N, SH_F = (34.4, 20.8), (33.4, 20.2)                      # pincer shoulders

NEU = dict(rot=0.0, piv=(24.0, 31.0), off=(0.0, 0.0), sy=1.0, bob=0.0,
           feet=None, lift=None, fold=0.0, claw_n=None, claw_f=None, glow=1.0, glint=False, flare=0.0,
           smear=None, eye=2, flail=None, dust=None, wind=0.0, shake=0.0, snapfx=False, curl=0.0)
BP = mk(NEU)


def claw_pose(base, ang, opn):
    return dict(base=base, ang=ang, open=opn)


IDLE_N = claw_pose((38.4, 23.0), 22.0, 0.25)
IDLE_F = claw_pose((37.4, 22.2), 14.0, 0.2)


# =========================================================================== parts
FAR_DX = (2.2, 2.6, -2.2)                                     # far feet offset from the near ones
KNEES_N = [(37.8, 17.2), (30.8, 18.6), (10.0, 17.2)]          # base knee positions (define segment lengths)


def leg_geom(i, far):
    hip = HIPS_F[i] if far else HIPS_N[i]
    dx = (2.0, 2.2, -2.0)[i] if far else 0.0
    kn = (KNEES_N[i][0] + dx, KNEES_N[i][1] - (1.2 if far else 0.0))
    foot = (FEET[i] + (FAR_DX[i] if far else 0.0), FLOOR)
    l1 = math.hypot(kn[0] - hip[0], kn[1] - hip[1])
    l2 = math.hypot(foot[0] - kn[0], foot[1] - kn[1])
    mid = lerp(hip, foot, 0.5)
    return hip, l1, l2, (kn[0] - mid[0], kn[1] - mid[1])


def draw_leg(L, R, i, far, foot, lift, bias):
    """Thin jointed crab leg splaying out from under the shell: femur out and up to a knuckle, long tibia down
    to a pale needle tip on the floor. Segment lengths are fixed per leg (IK), so the legs never stretch."""
    hip, l1, l2, pref_m = leg_geom(i, far)
    h = R.T(hip)
    f = R.T((foot, FLOOR - lift))
    p0 = R.T((0.0, 0.0))
    p1 = R.T(pref_m)
    pref = (p1[0] - p0[0], p1[1] - p0[1])
    B.check_reach("leg", h, f, l1 + l2)
    kn = ik(h, f, l1, l2, pref)
    L.paint(n_capsule(h, kn, 0.75, 0.6), "dK", bias)
    L.paint(n_capsule(kn, f, 0.6, 0.3), "dK", bias, ao=0)
    L.fixed({ip(kn): "dK4" if bias >= 0 else "dK3"})               # knee knuckle catches light
    L.fixed({ip(f): "dB3" if bias >= 0 else "dB2"})                # pale tip
    return kn


def draw_pincer(L, FX, R, sh, cp, bias, info, key):
    s = R.T(sh)
    base = R.T(cp["base"])
    ang = R.A(cp["ang"])
    B.check_reach("pincer", s, base, A1 + A2)
    pv = R.T((sh[0] + 0.2, sh[1] - 1.0))
    el = ik(s, base, A1, A2, (pv[0] - s[0], pv[1] - s[1]))
    mat = "dB"
    a1 = L.paint(n_capsule(s, el, 0.85, 0.7), mat, bias - 1)
    a2 = L.paint(n_capsule(el, base, 0.7, 0.95), mat, bias - 1, ao=0)
    d = dirv(ang)
    n = (-d[1], d[0])
    # palm: a slim tapered bone case
    palm_end = madd(base, (d, 3.8))
    palm = L.paint(n_capsule(base, palm_end, 1.35, 1.15), mat, bias, ao=0)
    # fixed finger (outer/lower) + dactyl (inner/upper, opens), both curved inward to needle tips
    o = cp["open"]
    fa = math.degrees(math.atan2(d[1], d[0]))
    fr = madd(palm_end, (n, 0.55))
    dr = madd(palm_end, (n, -0.55))
    fmid = madd(fr, (dirv(fa + 6 + o * 12), 2.2))
    fixed_tip = madd(fmid, (dirv(fa - 10 + o * 8), 2.2))
    dmid = madd(dr, (dirv(fa - 8 - o * 50), 2.2))
    dact_tip = madd(dmid, (dirv(fa + 10 - o * 50), 2.1))
    f1 = L.paint(S.n_tube([fr, fmid, fixed_tip], [0.75, 0.6, 0.3]), mat, bias + 1, ao=0)
    f2 = L.paint(S.n_tube([dr, dmid, dact_tip], [0.75, 0.6, 0.3]), mat, bias + 1, ao=0)
    L.fixed({ip(fixed_tip): "dB5", ip(dact_tip): "dB5"})
    pix = palm | f1 | f2
    info["hit"] |= pix
    info[key] = lerp(fixed_tip, dact_tip, 0.5)
    info[key + "_palm"] = lerp(base, palm_end, 0.6)
    return pix


def draw_crawler(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    R = Rig(p["rot"], p["piv"], off=(p["off"][0] + p["shake"], p["off"][1] + p["bob"]), sy=p["sy"])
    fold = p["fold"]
    # ---- legs (far side first, darker)
    feet = p["feet"] or [(FEET[i], FEET[i] + FAR_DX[i]) for i in range(3)]
    lift = p["lift"] or [(0.0, 0.0)] * 3
    if p["flail"] is not None:
        # upside down: legs claw at the air, drawn in model space above the (flipped) body
        for side, (Lr, hips, bias) in enumerate(((Ls["LegsB"], HIPS_F, -2), (Ls["Legs"], HIPS_N, 0))):
            for i, hip in enumerate(hips):
                h = R.T(hip)
                a = -90 + (i - 1) * 32 + math.sin(fi * 1.7 + i * 2.1 + side) * p["flail"] * 18 + side * 6
                c = p["curl"]
                kn = madd(h, (dirv(a), L1 * (1 - 0.35 * c)))
                tip = madd(kn, (dirv(a + 60 + 70 * c), L2 * (1 - 0.3 * c)))
                Lr.paint(n_capsule(h, kn, 0.95, 0.8), "dK", bias)
                Lr.paint(n_capsule(kn, tip, 0.8, 0.45), "dK", bias, ao=0)
                Lr.fixed({ip(tip): "dB3" if bias >= 0 else "dB2", ip(kn): "dK4" if bias >= 0 else "dK3"})
    else:
        for i in range(3):
            if fold > 0:
                for Lr, hip, bias in ((Ls["LegsB"], HIPS_F[i], -2), (Ls["Legs"], HIPS_N[i], 0)):
                    sgn = 1 if i < 2 else -1
                    kn_m = lerp((hip[0] + sgn * 4.0, hip[1] - 5.0), (hip[0] + sgn * 5.0, hip[1] + 0.6), fold)
                    tip_m = lerp((hip[0] + sgn * 8.0, FLOOR), (hip[0] + sgn * 1.5, hip[1] + 2.6), fold)
                    h, kn, tip = R.T(hip), R.T(kn_m), R.T(tip_m)
                    tip = (tip[0], min(tip[1], FLOOR))
                    Lr.paint(n_capsule(h, kn, 0.85, 0.7), "dK", bias)
                    Lr.paint(n_capsule(kn, tip, 0.7, 0.35), "dK", bias, ao=0)
                    Lr.fixed({ip(kn): "dK4" if bias >= 0 else "dK3"})
            else:
                draw_leg(Ls["LegsB"], R, i, True, feet[i][1], lift[i][1], -2)
                draw_leg(Ls["Legs"], R, i, False, feet[i][0], lift[i][0], 0)
    # ---- soft underbody
    Bd = Ls["Body"]
    Bd.paint(n_dome(R.T((23.0, 21.6)), 8.0, 1.8), "dK", 0)
    # ---- pincers (far behind, near on top)
    cn = p["claw_n"] or IDLE_N
    cf = p["claw_f"] or IDLE_F
    draw_pincer(Ls["PincerB"], FX, R, SH_F, cf, -2, info, "claw_f")
    draw_pincer(Ls["Pincer"], FX, R, SH_N, cn, 0, info, "claw_n")
    # ---- shell: ribcage carapace + skull face-plate
    Sh = Ls["Shell"]
    m = R.mask(SHELL)
    Sh.paint(n_plate(m, 3.0, (-0.05, -0.1), 1.0), "dB", 0)
    # the lower rim of the ribcage sits in shadow
    rimy = {}
    for (x, y) in m:
        rimy[x] = max(rimy.get(x, -1), y)
    Sh.decal([(x, y) for x, y in m if y >= rimy[x] - 1], ("dB", 1))
    # rib grooves (slanting back), with teal specks glowing in the cracks
    specks = {}
    for k, x in enumerate((14.4, 19.2, 24.0, 28.6)):
        top = (x, 15.0 + max(0.0, (22.0 - x)) * 0.36 if x < 22 else 14.4)
        bot = (x - 3.0, 22.2)
        g = [q for q in K.polyline([R.pt(top), R.pt(lerp(top, bot, 0.5)), R.pt(bot)]) if q in m]
        Sh.decal(g, ("dB", 1))
        # rib highlight just in front of each groove
        if len(g) > 4:
            j = int(len(g) * (0.45 + 0.2 * hash01(k, 1, 7)))
            on = (k + fi) % 3 != 0 or p["flare"] > 0
            if p["glow"] > 0.1 and k in (0, 2, 3):
                specks[g[j]] = ("dG3" if p["flare"] > 0.5 else "dG2") if on else "dG1"
                if k % 2 == 0 and j + 1 < len(g):
                    specks[g[j + 1]] = "dG1"
    Sh.fixed(specks)
    # vertebral ridge: little knuckles along the top line
    for x in (12.0, 15.2, 18.4, 21.6, 24.8, 28.0):
        y = 14.8 + max(0.0, (22.0 - x)) * 0.36 if x < 22 else 14.6
        q = R.pt((x, y))
        Sh.paint(n_dome((q[0] + 0.5, q[1] + 0.5), 1.0, 0.9, tilt=(-0.1, -0.3)), "dB", 1, ao=0)
    # skull face-plate: brow, dark eye socket with a teal eye-point, nasal pit, teeth along the rim
    Sh.decal([q for q in K.polyline([R.pt((31.2, 15.4)), R.pt((30.4, 18.6)), R.pt((31.2, 22.0))]) if q in m],
             ("dB", 1))
    eye = R.pt((34.0, 17.8))
    sock = {eye: "dC0", (eye[0] - 1, eye[1]): "dC0", (eye[0], eye[1] + 1): "dC1", (eye[0] - 1, eye[1] + 1): "dC0"}
    ecol = {0: "dC0", 1: "dG1", 2: "dG2", 3: "dG4"}[p["eye"]]
    sock[eye] = ecol
    Sh.fixed({q: c for q, c in sock.items() if q in m})
    info["eye"] = eye
    nas = R.pt((36.8, 19.2))
    Sh.fixed({q: "dC1" for q in (nas, (nas[0], nas[1] + 1)) if q in m})
    teeth = {}
    for k, x in enumerate((32.4, 33.6, 34.8, 36.0)):
        q = R.pt((x, 21.4))
        if q in m:
            teeth[q] = "dB5" if k % 2 == 0 else "dB3"
    Sh.fixed(teeth)
    # barnacle clusters crusting the back
    B.barnacles(Sh, [(R.T((18.6, 15.2)), 1.3), (R.T((20.9, 14.5)), 1.05), (R.T((16.5, 16.5)), 0.9),
                     (R.T((26.4, 14.0)), 0.95), (R.T((11.8, 18.0)), 0.8)], seed=5)
    info["body"] = m
    info["glint"] = R.T((cn["base"][0] + 2.0, cn["base"][1] - 0.5))
    # ---- light: faint teal under-glow around the specks is left implicit (restrained)
    if p["glint"]:
        B.star(FX, info["claw_n"], 3)
    if p["smear"]:
        for (a, b_) in p["smear"]:
            pts = K.line(a, b_)
            for j, q in enumerate(pts):
                if j > len(pts) * 0.25 and q[1] <= FLOOR:
                    FX.put([q], "dB5" if j > len(pts) * 0.75 else "dB3" if j > len(pts) * 0.5 else "dB2")
                    FX.put([(q[0], q[1] - 2)], "dB2") if j > len(pts) * 0.5 and j % 2 else None
            info["hit"] |= set(pts)
    if p["snapfx"]:
        c = info["claw_n"]
        B.star(FX, c, 2, cols=("dB5", "dB4", "dW5"))
    if p["dust"]:
        x0, n = p["dust"]
        for k in range(n):
            dx = (k - n / 2) * 2.0 + hash01(k, 5, 17) * 1.5
            h_ = 1 + int(hash01(k, 6, 17) * 2.5)
            for j in range(h_):
                FX.put([(int(x0 + dx + j * (0.6 if dx > 0 else -0.6)), FLOOR - j - (k % 2))], "dW5" if j else "dW4")
    # dripping water from the shell rim
    rim = [R.T((12.0, 21.8)), R.T((21.0, 23.4)), R.T((30.0, 22.6))]
    B.drips(FX, rim, fi, floor=FLOOR, period=6, fall=1.6, seed=4,
            skip=set().union(*[set(L.px) for L in Ls.values() if isinstance(L, Layer)]))
    return Ls, info


# =========================================================================== animation
def gait(i):
    """Tripod crawl: feet planted 3 frames moving back 2px/frame (no sliding), 3 frames swinging forward."""
    def one(x0, k):
        k %= 6
        if k < 3:
            return x0 + 2.0 - 2.0 * k, 0.0
        return [(x0 - 1.6, 1.4), (x0 + 0.6, 2.0), (x0 + 2.6, 0.9)][k - 3]
    feet, lift = [], []
    for leg in range(3):
        pn = i + (0 if leg != 1 else 3)          # near: front+rear together, mid opposite
        pf = i + (3 if leg != 1 else 0)
        xn, ln = one(FEET[leg], pn)
        xf, lf = one(FEET[leg] + FAR_DX[leg], pf)
        feet.append((xn, xf))
        lift.append((ln, lf))
    return feet, lift


def a_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.4, 0.8, 0.4)[i]
        o = (0.25, 0.35, 0.2, 0.1)[i]
        fr.append((210, BP(bob=b * 0.5, claw_n=claw_pose((38.4, 23.0 + b * 0.4), 22.0 - b * 3, o),
                           claw_f=claw_pose((37.4, 22.2 + b * 0.3), 14.0 + b * 2, 0.35 - o),
                           glow=(1.0, 1.2, 1.0, 0.85)[i])))
    return fr


def a_crawl():
    fr = []
    for i in range(6):
        feet, lift = gait(i)
        s_ = math.sin(2 * math.pi * i / 3)
        fr.append((110, BP(feet=feet, lift=lift, bob=0.25 * s_,
                           claw_n=claw_pose((38.4 + 0.4 * s_, 23.0), 22.0 + 3 * s_, 0.2),
                           claw_f=claw_pose((37.4 - 0.4 * s_, 22.2), 14.0 - 3 * s_, 0.25), wind=-1)))
    return fr


def a_snap():
    return [
        (120, BP(bob=0.4, claw_n=claw_pose((38.8, 18.6), -10.0, 0.5), claw_f=claw_pose((37.8, 18.0), -16.0, 0.5))),
        (120, BP(bob=0.6, off=(-0.8, 0.0), claw_n=claw_pose((37.8, 14.6), -40.0, 0.9),
                 claw_f=claw_pose((36.8, 14.0), -46.0, 0.9), glow=1.2)),
        (130, BP(bob=0.8, off=(-1.4, 0.0), rot=-3.0, claw_n=claw_pose((37.0, 12.2), -58.0, 1.0),
                 claw_f=claw_pose((36.0, 11.6), -64.0, 1.0), glow=1.4, eye=3)),
        (320, BP(bob=0.8, off=(-1.6, 0.0), rot=-4.0, claw_n=claw_pose((36.8, 11.6), -60.0, 1.0),
                 claw_f=claw_pose((35.8, 11.0), -66.0, 1.0), glow=1.6, flare=0.8, eye=3, glint=True)),
        (60, BP(off=(-0.2, 0.0), rot=2.0, claw_n=claw_pose((38.6, 25.2), 20.0, 0.1),
                claw_f=claw_pose((37.6, 24.6), 14.0, 0.15), glow=1.3, eye=3, wind=3,
                smear=[((39.0, 13.0), (46.6, 25.0)), ((36.0, 15.0), (45.6, 28.6))])),
        (80, BP(off=(-0.2, 0.0), rot=3.0, claw_n=claw_pose((38.8, 25.8), 24.0, 0.0),
                claw_f=claw_pose((37.8, 25.2), 18.0, 0.0), glow=1.2, eye=3, snapfx=True, dust=(45, 4))),
        (130, BP(off=(0.6, 0.0), rot=2.0, claw_n=claw_pose((38.6, 25.6), 30.0, 0.1),
                 claw_f=claw_pose((37.6, 25.0), 24.0, 0.1), glow=1.1, eye=2, dust=(45, 6))),
        (150, BP(off=(0.3, 0.0), claw_n=claw_pose((38.6, 23.8), 26.0, 0.2), claw_f=claw_pose((37.6, 23.0), 18.0, 0.2),
                 glow=1.0)),
        (160, BP()),
    ]


def a_shell():
    tuck_n = claw_pose((36.4, 23.8), 150.0, 0.0)
    tuck_f = claw_pose((35.6, 23.2), 156.0, 0.0)
    return [
        (90, BP(off=(0.0, 2.6), fold=0.5, claw_n=claw_pose((38.4, 24.4), 95.0, 0.0),
                claw_f=claw_pose((37.6, 23.8), 100.0, 0.0), eye=2)),
        (90, BP(off=(0.0, 5.0), fold=0.9, claw_n=tuck_n, claw_f=tuck_f, eye=1, glow=0.8, dust=(24, 8))),
        (260, BP(off=(0.0, 5.6), fold=1.0, claw_n=tuck_n, claw_f=tuck_f, eye=1, glow=0.7)),
        (260, BP(off=(0.0, 5.6), fold=1.0, claw_n=tuck_n, claw_f=tuck_f, eye=1, glow=0.9)),
    ]


def a_hurt():
    return [(80, BP(off=(-1.6, 0.0), rot=-5.0, shake=0.0, claw_n=claw_pose((38.0, 17.6), -40.0, 1.0),
                    claw_f=claw_pose((37.0, 18.0), -20.0, 0.9), eye=3, glow=1.5, flare=0.6)),
            (140, BP(off=(-0.8, 0.0), rot=-2.0, claw_n=claw_pose((39.4, 21.6), 20.0, 0.6),
                     claw_f=claw_pose((38.4, 21.0), 10.0, 0.5), eye=2))]


def a_death():
    FL = dict(rot=180.0, piv=(23.0, 20.0), off=(0.0, 4.8))
    return [
        (90, BP(off=(-1.6, 0.0), rot=-6.0, claw_n=claw_pose((38.0, 17.6), -40.0, 1.0),
                claw_f=claw_pose((37.0, 18.0), -20.0, 0.9), eye=3, glow=1.5, flare=0.6)),
        (110, BP(rot=-24.0, piv=(8.0, 31.0), claw_n=claw_pose((39.0, 21.0), 10.0, 1.0),
                 claw_f=claw_pose((38.0, 21.0), 20.0, 1.0), eye=2, glow=1.2, dust=(12, 5))),
        (120, BP(rot=-62.0, piv=(22.0, 28.0), off=(2.0, 3.0), claw_n=claw_pose((38.6, 19.0), 0.0, 0.8),
                 claw_f=claw_pose((37.6, 19.0), 10.0, 0.8), eye=2, glow=1.0, flail=1.2, curl=0.5)),
        (130, BP(**FL, flail=1.0, claw_n=claw_pose((38.0, 17.0), -50.0, 0.9), claw_f=claw_pose((37.0, 17.0), -40.0, 0.9),
                 eye=1, glow=0.8, dust=(24, 9))),
        (170, BP(**FL, flail=0.6, curl=0.6, claw_n=claw_pose((37.0, 16.4), -80.0, 0.5),
                 claw_f=claw_pose((36.0, 16.4), -70.0, 0.5), eye=1, glow=0.5)),
        (900, BP(**FL, flail=0.0, curl=1.0, claw_n=claw_pose((36.0, 15.8), -100.0, 0.2),
                 claw_f=claw_pose((35.0, 15.8), -90.0, 0.2), eye=0, glow=0.0)),
    ]


def build(build_ase):
    K.setup(48, 32)
    anims, infos = S.render_anims(SPEC, LAYERS, draw_crawler,
                                  [("idle", a_idle), ("crawl", a_crawl), ("snap", a_snap), ("shell", a_shell),
                                   ("hurt", a_hurt), ("death", a_death)],
                                  sway_key="bob", loops=("idle", "crawl"))
    hb = S.hurtbox(anims, ["Shell"], inset=(2, 1, 1, 0), tag=0)
    for k in (4, 5):
        infos["snap"][k]["hit"] = {q for q in infos["snap"][k]["hit"] if q[1] >= 20}
    snap = S.hit_rect(infos, "snap", [4, 5], x_min=35)
    meta = {"native": 1, "frame": [48, 32], "anchor": [24, 32],
            "hurtbox": hb,
            "attacks": {"snap": {"active": [4, 5], "hit": snap}},
            "telegraph": {"snap": {"frame": 3, "at": S.spawn_pt(infos["snap"][3]["claw_n"])}},
            "guard": {"tag": "shell", "held": [2, 3],
                      "hurtbox": S.hurtbox(anims, ["Shell"], inset=(1, 1, 1, 0), frame=2, tag=3)},
            "notes": "faces right, feet on the bottom row. crawl: tripod gait, feet planted 3 frames moving back "
                     "2px/frame at 110ms -> engine crawl speed ~18 px/s keeps feet from sliding; body steady. snap: "
                     "0-2 rears back and raises the pincers wide open, 3 = held (glint on the near claw = "
                     "telegraph), 4-5 ACTIVE: both pincers snap shut forward and low (~20px ahead of the anchor), "
                     "6-8 recover. shell: withdraws flat under its ribcage shell (legs + pincers tucked); frames "
                     "2-3 are the held guard pose (use guard.hurtbox; engine should block/reduce frontal hits "
                     "while held, loop 2-3 while guarding, play 1..0 reversed or idle to un-guard). death: flips "
                     "onto its back, legs twitch then curl (hold last)."}
    S.export("db_barnacle", LAYERS, anims, meta, build_ase)
    return meta
