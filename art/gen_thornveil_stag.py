#!/usr/bin/env python3
"""THE WARDEN UNBOUND (agent T) -- phase 2 of the Antlered Warden: the god lets go of its human shape and becomes
the forest's first stag. A huge spectral stag of dark twisted wood and moss, a small deer skull, colossal antlers
burning with green spirit-fire, veins of spirit-light, root tendrils trailing from its belly, pale ribbons in its tail.

    python3 art/gen_thornveil_stag.py [--preview] [--only tag,tag]

Output: warden_stag (256x176, faces RIGHT, hooves on the bottom row, anchor [128,176]) + warden_stag_meta.json
(per-frame hurtboxes + antler/hoof points, attack windows), previews art/previews/warden_stag*.png.

One quadruped skeleton with fixed bone lengths drives every frame (thigh/gaskin/cannon 26/26/26 behind, upper/fore/
cannon 22/22/26 in front, neck 34, antler beam 3.8x), so the proportions never drift; the gallop is a rotary
gallop computed from per-leg phases (stance sweeps back at body speed, swing arcs forward).
"""
import math, os, sys
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import thornveil_ckit as C  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, poly_mask, n_plate, n_dome, n_capsule, dirv  # noqa: E402
from thornveil_ckit import mk, rot, madd, curve, chain, taper, deer_skull, antler, ribbon_px, glow_dots, render_anims, collapse, spawn_pt, contact  # noqa: E402

W_, H_ = 256, 176
FL = 175
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
LAYERS = ["AntlerFar", "FarLegs", "Tail", "Belly", "Body", "NearHind", "NearFore", "Neck", "Head", "AntlerNear", "Mound", "Flames", "FX"]
FXL = {"Flames", "FX"}
HT, HG, HC = 26.0, 26.0, 26.0          # hind: thigh, gaskin, cannon
FU, FF, FCn = 22.0, 22.0, 26.0         # fore: upper arm, forearm, cannon
NECK = 34.0
P0, S0 = (100.0, 100.0), (158.0, 97.0)
BL = math.hypot(S0[0] - P0[0], S0[1] - P0[1])

NEU = dict(P=P0, S=S0, na=-48.0, ha=58.0, at=0.0, jaw=0.0, hf=(94.0, 0.0, 0.0), hn=(104.0, 0.0, 0.0), ff=(154.0, 0.0, 0.0), fn=(164.0, 0.0, 0.0),
           flame=1, glow=1, wind=0.0, sink=0.0, mound=0.0, trail=0, dust=0, burst=0, eye=2)
PP = mk(NEU)


def clamp_reach(s, t, L):
    d = sub(t, s)
    ln = math.hypot(*d)
    return t if ln <= L - 0.3 else madd(s, ((d[0] / ln, d[1] / ln), L - 0.3))


def bark(L, mask, seed, cell=6.5, glow=1, vein_p=0.16, mat="E"):
    """Bark plates over a painted mask: jittered cells, a lit upper lip on each plate, dark cracks between plates,
    and a few cracks glowing with spirit-light."""
    cells = {}
    def cid(x, y):
        gx, gy = int(x // (cell * 1.7)), int(y // (cell * 0.6))
        best, bd = None, 1e9
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                cx = (gx + ox + 0.5 + (hash01(gx + ox, gy + oy, seed) - 0.5) * 0.9) * cell * 1.7
                cy = (gy + oy + 0.5 + (hash01(gx + ox, gy + oy, seed + 1) - 0.5) * 0.7) * cell * 0.6
                d = ((x - cx) / 1.7) ** 2 + ((y - cy) / 0.6) ** 2
                if d < bd:
                    bd, best = d, (gx + ox, gy + oy)
        return best
    ids = {q: cid(q[0] + .5, q[1] + .5) for q in mask if q in L.px}
    for q, c in ids.items():
        x, y = q
        up_, dn_, lf, rt = ids.get((x, y - 1)), ids.get((x, y + 1)), ids.get((x - 1, y)), ids.get((x + 1, y))
        edge = (up_ is not None and up_ != c) or (lf is not None and lf != c)
        if edge:
            if hash01(c[0] * 7 + c[1], x + y, seed + 3) < vein_p * glow:
                L.fixed({q: "S3" if (x + y) % 3 else "S4"})
            else:
                L.decal([q], (mat, 1))
        elif (x, y - 1) in ids and ids.get((x, y - 1)) == c and ids.get((x, y - 2)) != c:
            e = L.px.get(q)
            if e and not isinstance(e[3], str):
                e[2] += 1                      # the plate's lit upper lip


def veins(L, start, ang, length, seed, lv=3, branch=True):
    """A continuous crack of spirit-light wandering across the bark (like the drake's lightning seams, but green)."""
    x, y = start
    a = ang
    for i in range(int(length)):
        a += (hash01(i, seed, 3) - 0.5) * 50
        x += math.cos(math.radians(a)); y += math.sin(math.radians(a))
        q = ip((x, y))
        if q not in L.px:
            break
        L.fixed({q: f"S{lv if i % 5 else min(5, lv + 1)}"})
        side = ip((x, y + 1))
        if side in L.px and not isinstance(L.px[side][3], str):
            L.decal([side], ("E", 0))
        if branch and i > 4 and hash01(i, seed, 9) < 0.08:
            veins(L, (x, y), a + (40 if hash01(i, seed, 10) < 0.5 else -40), length * 0.35, seed + i, lv - 1 if lv > 2 else lv, False)


def hoof(L, f, bias, facing=1):
    """Cloven hoof: two dark toes with a split, and a dew-claw behind."""
    x, y = f
    L.paint(n_dome((x + 1.2, y - 1.9), 2.8, 2.2, tilt=(0, -0.3)), "E", bias - 1, ao=0)
    L.paint(n_dome((x + 3.8, y - 1.6), 2.5, 2.0, tilt=(0, -0.3)), "E", bias - 1, ao=0)
    L.fixed({ip((x + 2.2, y - 0.6)): "E0", ip((x + 2.2, y - 1.6)): "E0", ip((x - 1.4, y - 3.6)): "J1"})
    L.fixed({ip((x + 4.4, y - 0.4)): "J2" if bias == 0 else "J1", ip((x + 1.8, y - 0.2)): "J1"})


def root_wrap(L, pts, seed, n=3):
    """Roots spiralling round a limb: dark twisting lines on its surface with a few green-lit beads."""
    for k in range(n):
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            for j in range(6):
                t = j / 6
                q = lerp(a, b, t)
                d = sub(b, a)
                l_ = math.hypot(*d) or 1
                nrm = (-d[1] / l_, d[0] / l_)
                off = 2.2 * math.sin((i + t) * 2.4 + k * 2.1 + seed)
                qq = ip(madd(q, (nrm, off)))
                if qq in L.px:
                    L.decal([qq], ("E", 1))
                    if hash01(qq[0], qq[1], seed + k) < 0.05:
                        L.fixed({qq: "S3"})


def hind_leg(L, hip, foot, bias, dy):
    """foot = (x, lift, fold). Bones: thigh 26, gaskin 26, cannon 26 (the backward-bending hock between gaskin and cannon)."""
    fx, lift, fold = foot
    f = (fx, FL - lift + dy)
    ca = -104 + 70 * fold
    hock = madd(f, (dirv(ca), HC))
    hock = clamp_reach(hip, hock, HT + HG)
    stifle = ik(hip, hock, HT, HG, (1, 0.35))
    fet = madd(f, (dirv(ca), 4.0))
    # thigh: heavy muscle, bulging to the front
    C.smooth_tube(L, [hip, madd(lerp(hip, stifle, 0.5), (dirv(math.degrees(math.atan2(stifle[1] - hip[1], stifle[0] - hip[0])) - 90), 2.0)), stifle],
                  [10.5, 8.0, 5.0], "E", bias)
    # gaskin: a strong muscle belly high on the shank, tendon behind, tapering into the hock
    gpts = [stifle, lerp(stifle, hock, 0.35), hock]
    C.smooth_tube(L, gpts, [6.8, 6.0, 3.4], "E", bias, ao=0)
    L.paint(n_dome(madd(hock, ((-1, 0), 1.0)), 3.8, 3.2), "E", bias + 1, ao=0)       # the bony hock, jutting back
    # slim cannon, fetlock knob, short pastern
    C.smooth_tube(L, [hock, lerp(hock, fet, 0.5), fet], [3.0, 2.6, 2.7], "E", bias - 1, ao=0)
    L.paint(n_dome(fet, 3.1, 2.8), "E", bias, ao=0)
    C.smooth_tube(L, [fet, (f[0] + 0.6, f[1] - 2.2)], [2.5, 2.3], "E", bias - 1, ao=0)
    hoof(L, f, bias)
    root_wrap(L, [hip, stifle, hock, fet], 3 + bias)
    return stifle, hock, f


def fore_leg(L, sho, foot, bias, dy):
    """Bones: upper arm 22, forearm 22, cannon 26 (the knee/carpus bends forward-under when lifted)."""
    fx, lift, fold = foot
    f = (fx, FL - lift + dy)
    ca = -86 - 80 * fold
    knee = madd(f, (dirv(ca), FCn))
    knee = clamp_reach(sho, knee, FU + FF)
    elbow = ik(sho, knee, FU, FF, (-1, 0.1))
    fet = madd(f, (dirv(ca), 4.0))
    C.smooth_tube(L, [sho, lerp(sho, elbow, 0.5), elbow], [9.0, 7.6, 5.0], "E", bias)                  # upper arm under the shoulder
    L.paint(n_dome(madd(elbow, (dirv(math.degrees(math.atan2(knee[1] - sho[1], knee[0] - sho[0])) + 180), 1.5)), 3.4, 3.0), "E", bias, ao=0)   # elbow point
    C.smooth_tube(L, [elbow, lerp(elbow, knee, 0.3), knee], [7.0, 6.0, 3.6], "E", bias, ao=0)           # forearm muscle
    L.paint(n_dome(knee, 3.8, 3.4), "E", bias + 1, ao=0)                                                  # the knee
    C.smooth_tube(L, [knee, lerp(knee, fet, 0.5), fet], [3.0, 2.6, 2.7], "E", bias - 1, ao=0)
    L.paint(n_dome(fet, 3.1, 2.8), "E", bias, ao=0)
    C.smooth_tube(L, [fet, (f[0] + 0.6, f[1] - 2.2)], [2.5, 2.3], "E", bias - 1, ao=0)
    hoof(L, f, bias)
    root_wrap(L, [sho, elbow, knee, fet], 7 + bias)
    return elbow, knee, f


def spirit_flame(FX, base, size, fi, seed):
    """A tongue of green spirit-fire standing on an antler tine."""
    K.flame(FX, base, size, fi, seed=seed, pal=("S5", "S4", "S3", "S3", "S2", "S1"))


def grand_antler(L, base, ang, s, bias, fi, seed, spread=1.0):
    """A colossal crown seen from the side: a thick beam sweeping up and back, curling forward at the top, with a
    brow tine over the face, bez and trez tines, and a palm of crown tines fanning upward (some forking again).
    `ang` is the beam's base direction (about -110 = up and back); every tine rotates with it."""
    rotk = ang + 110                     # how far the whole crown is tilted from its rest pose
    beam = [base]
    Lb = 15.5 * s
    for i in range(1, 7):
        t = i / 6
        a = ang - 44 * spread * math.sin(t * math.pi * 0.6) + 74 * t * t
        beam.append(madd(beam[-1], (dirv(a), Lb / 6)))
    cp = curve(beam, 3)
    rr = [3.8 * (1 - 0.6 * (i / (len(cp) - 1))) + 0.7 for i in range(len(cp))]
    C.smooth_tube(L, cp, rr, "J", bias, ao=0)
    L.paint(n_dome(base, 4.2, 3.4), "J", bias - 1, ao=0)              # the coronet burr
    tips = []
    def tine(t, a, ln, r0, fork=False):
        q = cp[int(t * (len(cp) - 1))]
        a = a + rotk
        tp = madd(q, (dirv(a), ln))
        mid = madd(lerp(q, tp, 0.55), (dirv(a - 90), 1.6))
        C.smooth_tube(L, [q, mid, tp], [r0 * 1.12, r0 * 0.75, 0.6], "J", bias, ao=0)
        tips.append(tp)
        if fork:
            q2 = lerp(q, tp, 0.6)
            tp2 = madd(q2, (dirv(a - 36), ln * 0.46))
            C.smooth_tube(L, [q2, tp2], [r0 * 0.6, 0.6], "J", bias, ao=0)
            tips.append(tp2)
    tine(0.06, -18, 5.4 * s, 2.0)                    # brow tine, forward over the face
    tine(0.2, -40, 4.4 * s, 1.8)                     # bez
    tine(0.42, -66, 4.8 * s, 1.6, fork=True)         # trez
    for k, (t, a, ln) in enumerate(((0.66, -84, 4.2), (0.78, -100, 4.6), (0.88, -120, 4.0), (0.95, -140, 3.2))):
        tine(t, a, ln * s, 1.35, fork=(k in (1, 2)))
    tips.append(cp[-1])
    for i in range(0, len(cp) - 1, 2):
        q = ip(cp[i])
        if q in L.px:
            L.decal([q], ("J", 2))
    L.fixed({ip(t): "J5" for t in tips if ip(t) in L.px})
    return tips, cp


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FLm = FXLayer("FX"), FXLayer("Flames")
    Ls["FX"], Ls["Flames"] = FX, FLm
    info = {"ant": set(), "body": set(), "hooves": []}
    dy = p["sink"] * 140.0
    D = lambda q: (q[0], q[1] + dy)
    P, Sk = D(p["P"]), D(p["S"])
    dk = sub(Sk, P)
    lk = math.hypot(*dk) or 1
    S = madd(P, ((dk[0] / lk, dk[1] / lk), BL))           # fixed body length: the keyed S only gives the direction
    fdx = S[0] - Sk[0]
    p = dict(p, ff=(p["ff"][0] + fdx, p["ff"][1], p["ff"][2]), fn=(p["fn"][0] + fdx, p["fn"][1], p["fn"][2]))
    ax_ = sub(S, P)
    ln = math.hypot(*ax_) or 1
    fwd = (ax_[0] / ln, ax_[1] / ln)
    up = (fwd[1], -fwd[0])
    dn = (-up[0], -up[1])
    s = sw * 0.6 + p["wind"]
    glow = p["glow"]
    # -------------------------------------------------------------- far legs (behind the body, shaded down)
    hipF = madd(P, (dn, 5.0), (fwd, -2.0))
    shoF = madd(S, (dn, 8.0), (fwd, -3.0))
    _, _, hfF = hind_leg(Ls["FarLegs"], hipF, p["hf"], -2, dy)
    _, _, ffF = fore_leg(Ls["FarLegs"], shoF, p["ff"], -2, dy)
    # -------------------------------------------------------------- the barrel: massive, deep-chested, arched back, sculpted bark
    Bd = Ls["Body"]
    pts = [madd(P, (fwd, -15), (dn, 1.0)), madd(P, (up, 3.5)), madd(lerp(P, S, 0.5), (up, 3.5)), madd(S, (fwd, -2), (up, 2.0)),
           madd(S, (fwd, 9.0), (dn, 5.0))]
    cp = curve(pts, 4)
    keys = [(0, 12.5), (0.2, 16.0), (0.5, 13.5), (0.78, 18.5), (1.0, 13.5)]
    rr = []
    for i in range(len(cp)):
        t = i / (len(cp) - 1)
        for (ta, ra), (tb, rb) in zip(keys, keys[1:]):
            if ta <= t <= tb:
                u = (t - ta) / (tb - ta)
                rr.append(ra + (rb - ra) * u * u * (3 - 2 * u))
                break
    bm = C.smooth_tube(Bd, cp, rr, "E", 0, flat=0.9)
    # the deep brisket hanging below the shoulders, and the tucked flank
    bm |= Bd.paint(n_dome(madd(S, (dn, 11.0), (fwd, 3.0)), 13.0, 12.5, tilt=(-0.1, 0.1)), "E", 0, ao=0)
    bm |= Bd.paint(n_dome(madd(S, (up, 10.0), (fwd, -4.0)), 11.0, 7.0, tilt=(-0.1, -0.25)), "E", 0, ao=0)    # withers hump
    bark(Bd, set(Bd.px), 5, cell=7.5, glow=1 + (glow >= 2), vein_p=0.02)
    lvv = 3 if glow < 3 else 4
    for k, (t, da, L_) in enumerate(((0.2, 20, 26), (0.45, -15, 30), (0.7, 30, 26), (0.9, 70, 20))):
        veins(Bd, madd(lerp(P, S, t), (up, 6.0 - k * 2)), math.degrees(math.atan2(fwd[1], fwd[0])) + da, L_, 50 + k, lvv)
    # moss mantle along the spine, dripping down the flanks
    for q in list(Bd.px):
        if (q[0], q[1] - 1) not in Bd.px:
            depth = 3 + int(hash01(q[0] // 2, 3, 9) * 4)
            for k in range(depth):
                qq = (q[0], q[1] + k)
                if qq in Bd.px:
                    Bd.decal([qq], ("H", 5 if k == 0 else 4 if k < 2 else 3 if k < depth - 1 else 2))
            if hash01(q[0], 1, 11) < 0.22:
                drip = 4 + int(hash01(q[0], 2, 12) * 8)
                for k in range(depth, depth + drip):
                    qq = (q[0], q[1] + k)
                    if qq in Bd.px:
                        Bd.decal([qq], ("H", 3 if k < depth + drip - 2 else 2))
    heart = ip(madd(S, (fwd, 3.0), (dn, 6.0)))
    hr = {}
    for qq in K.mask_disc(heart, 2.4):
        dd = math.hypot(qq[0] + .5 - heart[0], qq[1] + .5 - heart[1])
        hr[qq] = "S5" if dd < 1.0 else "S4" if dd < 1.8 else "S3"
    Bd.fixed(hr)
    info["heart"] = heart
    info["body"] |= set(Bd.px)
    # -------------------------------------------------------------- cloak of roots, moss and pale ribbons hanging from the belly and flanks
    Bl = Ls["Belly"]
    for k in range(9):
        t = 0.08 + k * 0.105
        a0 = madd(lerp(P, S, t), (dn, 9.0 + 4 * math.sin(t * math.pi)))
        L_ = 12 + (k * 7) % 13
        e = madd(a0, (dn, L_), (fwd, -s * 2.0 - 3.0 - (k % 3)))
        cpr = curve([a0, madd(lerp(a0, e, 0.5), (fwd, 1.6 * math.sin(fi * 0.9 + k))), e], 3)
        C.smooth_tube(Bl, cpr, taper(len(cpr), 1.8 if k % 2 else 1.3, 0.5), "E" if k % 3 else "H", -1, ao=0)
        if k % 3 == 1:
            Bl.fixed({ip(e): "S3" if glow >= 2 else "H4"})
    for k, t in enumerate((0.25, 0.62)):
        a0 = madd(lerp(P, S, t), (dn, 6.0))
        for q, c in ribbon_px((a0[0], a0[1]), fi, 3.1 + k, L=18 + k * 6, sway=-0.7 - s * 0.2).items():
            FX.put([q], c)
    # tail: a heavy tuft of moss with roots and two pale ribbons
    Tl = Ls["Tail"]
    tb = madd(P, (fwd, -15.0), (up, 5.0))
    tt = madd(tb, (fwd, -7.0 - s * 0.6), (dn, 7.0))
    C.smooth_tube(Tl, [tb, lerp(tb, tt, 0.5), tt], [4.0, 3.4, 2.0], "H", 0, ao=0)
    for k in range(2 if p["flame"] >= 0 else 0):
        for q, c in ribbon_px((tt[0] - 1 + k, tt[1] + 1), fi, k * 2.3, L=12 + k * 6, sway=-0.6 - s * 0.2).items():
            FX.put([q], c)
    # -------------------------------------------------------------- near legs with the great haunch and shoulder muscles
    hipN = madd(P, (dn, 6.0), (fwd, 2.0))
    shoN = madd(S, (dn, 9.0), (fwd, 1.0))
    NH, NF = Ls["NearHind"], Ls["NearFore"]
    NH.paint(n_dome(madd(hipN, (up, 4.5), (fwd, -1.5)), 12.5, 14.0, tilt=(-0.12, -0.18)), "E", 0)     # haunch
    NF.paint(n_dome(madd(shoN, (up, 6.0), (fwd, -1.0)), 9.5, 13.0, tilt=(-0.12, -0.25)), "E", 0)      # shoulder blade
    st, hk, hfN = hind_leg(NH, hipN, p["hn"], 0, dy)
    el, kn, ffN = fore_leg(NF, shoN, p["fn"], 0, dy)
    for L_, sd in ((NH, 21), (NF, 22)):
        mus = {q for q in L_.px if q[1] < (hipN[1] if L_ is NH else shoN[1]) + 12}
        bark(L_, mus, sd, cell=6.5, glow=1 + (glow >= 2), vein_p=0.02)
    veins(NH, madd(hipN, (up, 8.0)), 100, 24, 61, 3 if glow < 3 else 4)
    veins(NF, madd(shoN, (up, 10.0)), 95, 22, 62, 3 if glow < 3 else 4)
    info["hooves"] = [ffF, ffN, hfF, hfN]
    info["body"] |= set(NH.px) | set(NF.px)
    # -------------------------------------------------------------- neck: thick and powerful, arching; a mane of roots and moss
    Nk = Ls["Neck"]
    nb = madd(S, (fwd, 7.0), (up, 6.0))
    ndir = dirv(p["na"])
    nend = madd(nb, (ndir, NECK))
    npts = curve([nb, madd(lerp(nb, nend, 0.5), (dirv(p["na"] - 90), 3.0)), nend], 3)
    C.smooth_tube(Nk, npts, taper(len(npts), 13.5, 7.0, 0.8), "E", 0, flat=0.9)
    bark(Nk, set(Nk.px), 31, cell=6.0, glow=1 + (glow >= 2), vein_p=0.02)
    veins(Nk, lerp(nb, nend, 0.15), p["na"] + 10, 26, 71, 3 if glow < 3 else 4)
    # throat mane: long hanging strands of moss and root fibres
    for k in range(9):
        a0 = madd(lerp(nb, nend, 0.05 + k * 0.1), (dirv(p["na"] + 90), 6.5 - k * 0.35))
        L_ = 10 + (k % 4) * 4
        pts_ = [a0, madd(a0, ((0, 1), L_ * 0.55), ((1, 0), -s * 0.9 - 1.5)), madd(a0, ((0, 1), L_), ((1, 0), -s * 1.4 - 3))]
        cpm = curve(pts_, 2)
        C.smooth_tube(Nk, cpm, taper(len(cpm), 2.2, 0.6), "H" if k % 3 else "E", -1, ao=0)
    # crest of moss along the top of the neck
    for i in range(len(npts)):
        q = madd(npts[i], (dirv(p["na"] - 90), 11.0 * (1 - i / len(npts)) + 5))
        if i % 2 == 0:
            Nk.paint(n_dome(q, 2.6, 2.0), "H", 0, ao=0)
    info["body"] |= set(Nk.px)
    # -------------------------------------------------------------- head: a small deer skull with burning eyes
    hk_ = deer_skull(Ls["Head"], madd(nend, (dirv(p["ha"]), 2.0)), p["ha"], 2.4, eye=max(1, p["eye"]), jaw=p["jaw"])
    info["eye"], info["snout"] = hk_["eye"], hk_["snout"]
    e = hk_["eye"]
    if p["eye"] >= 1:
        FX.put([(e[0] - 1, e[1] - 1), (e[0], e[1] - 1), (e[0] + 1, e[1] - 1)], "S4")
        for j in range(3 + 2 * p["eye"]):                      # a trail of eye-light streaming back
            FX.put([(e[0] - 2 - j, e[1] - (j // 3))], "S3" if j < 3 else "S2")
    at = p["at"]
    tipsF, bF = grand_antler(Ls["AntlerFar"], hk_["ab2"], -146 + (p["ha"] - 58) * 0.4 + at, 3.8, -1, fi, 3, spread=1.0)
    tipsN, bN = grand_antler(Ls["AntlerNear"], hk_["ab"], -122 + (p["ha"] - 58) * 0.4 + at, 4.1, 0, fi, 7, spread=0.9)
    info["ant"] |= set(Ls["AntlerNear"].px) | set(Ls["AntlerFar"].px) | set(Ls["Head"].px)
    # moss draped over the beams, ribbons knotted to the tines, spirit-fire along every tine
    for L_, beam, sd in ((Ls["AntlerFar"], bF, 3), (Ls["AntlerNear"], bN, 7)):
        C.moss_drape(L_, [beam[int(len(beam) * f_)] for f_ in (0.15, 0.3, 0.45, 0.6, 0.75)], fi, sd, n=5, maxlen=15)
    if p["flame"] >= 0:
        for k, t in enumerate(tipsN + tipsF):
            spirit_flame(FLm, (t[0], t[1] + 1), 1.4 + 0.6 * p["flame"] + (k % 3) * 0.35, fi, k * 2)
        for k, bm_ in enumerate((bN, bF)):
            for f_ in (0.35, 0.6):
                q = bm_[int(len(bm_) * f_)]
                spirit_flame(FLm, (q[0] + 1, q[1]), 1.2 + 0.4 * p["flame"], fi, 40 + k * 3 + int(f_ * 10))
        for k, t in enumerate(tipsN[2:5]):
            for q, c in ribbon_px((t[0], t[1] + 2), fi, 1.1 + k, L=16 + k * 8, sway=-0.4 - s * 0.15).items():
                FX.put([q], c)
    info["tips"] = tipsN + tipsF
    info["crown"] = hk_["crown"]
    # -------------------------------------------------------------- lighting: cold rim on top, spirit-fire rim from the antlers
    for L_ in (Bd, Nk, Ls["Head"], NH, NF):
        C.rim(L_, {"E"}, 5)
    C.rim(Ls["AntlerNear"], {"J"}, 5)
    fire = madd(info["crown"], ((0, -1), 22))
    for L_ in (Nk, Bd, NF):
        add_ = {}
        for (x, y), e_ in L_.px.items():
            if e_[0] != "E" or isinstance(e_[3], str):
                continue
            d = math.hypot(fire[0] - x, fire[1] - y)
            if d < 70 and (x, y - 1) not in L_.px and hash01(x, y, 5) < 0.85:
                add_[(x, y)] = "S2" if d < 40 else "S1"
            elif d < 50 and (x + (1 if fire[0] > x else -1), y) not in L_.px and (x, y - 1) in L_.px and hash01(x, y, 6) < 0.5:
                add_[(x, y)] = "S1"
        L_.fixed(add_)
    # -------------------------------------------------------------- fx: spirit trail, dust, burst
    if p["trail"]:
        for k in range(10):
            src = [info["crown"], hfN, ffN, madd(P, (fwd, -14))][k % 4]
            L_ = 8 + k * 2
            y = src[1] + (k % 3) - 1 + math.sin(fi + k) * 1.5
            for j in range(L_):
                if (j + fi + k) % 3 == 0:
                    FX.put([ip((src[0] - 6 - j * 1.6, y + j * 0.05))], "S3" if j < L_ * 0.4 else "S2" if j < L_ * 0.75 else "S1")
    if p["dust"]:
        for k in range(14):
            a = -math.pi * (0.05 + 0.9 * hash01(k, p["dust"], 2))
            r = 3 + 6 * hash01(k, fi, 3) * p["dust"]
            for hv in ([ffN] if p["dust"] >= 2 else [hfN]):
                FX.put([ip((hv[0] + math.cos(a) * r * 1.6, FL - 1 + math.sin(a) * r * 0.6))], "E4" if k % 2 else "H3")
    if p["burst"]:
        c = info["heart"]
        for k in range(26):
            a = k / 26 * 2 * math.pi
            r = 10 + p["burst"] * 9 + (k % 3) * 2
            FX.put([ip((c[0] + math.cos(a) * r * 1.3, c[1] + math.sin(a) * r * 0.9))], "S4" if k % 2 else "S3")
    # -------------------------------------------------------------- the root mound it rises out of
    if p["mound"] > 0:
        Mn = Ls["Mound"]
        mw = 60 * p["mound"]
        cx = (P[0] + S[0]) / 2
        for k in range(34):
            t = k / 33
            x0 = cx - mw + 2 * mw * t
            hgt = (14 + 20 * math.sin(t * math.pi)) * p["mound"] * (0.6 + 0.4 * hash01(k, 1, 9))
            tip = (x0 + (hash01(k, 2, 9) - 0.5) * 12, FL - hgt)
            cp2 = curve([(x0, FL), (lerp((x0, FL), tip, 0.55)[0] + 3 * (1 if k % 2 else -1), lerp((x0, FL), tip, 0.55)[1]), tip], 3)
            chain(Mn, cp2, taper(len(cp2), 2.8, 0.7), "E", 0 if k % 2 else -1, ao=0)
            if k % 3 == 0:
                Mn.fixed({ip(tip): "S3"})
    for n_, L_ in Ls.items():
        for q in [q for q in L_.px if q[1] > FL]:
            L_.px.pop(q, None)
            if isinstance(L_, Layer):
                L_.noout.discard(q)
    return Ls, info


# =========================================================================== gait helpers
def leg_cycle(u, base, stride, lift_h, fold_k=0.7):
    """u in 0..1: stance [0,0.5) hoof on the floor sweeping front->back; swing [0.5,1) arcing forward."""
    u %= 1.0
    if u < 0.5:
        k = u / 0.5
        return (base + stride * (1 - 2 * k), 0.0, 0.0)
    k = (u - 0.5) / 0.5
    return (base - stride + 2 * stride * (k * k * (3 - 2 * k)), lift_h * math.sin(k * math.pi), fold_k * math.sin(k * math.pi))


def body_at(t, bob, pitch):
    P = (P0[0], P0[1] + bob)
    S = add(P, rot(sub(S0, P0), pitch))
    return P, S


# =========================================================================== animations
def idle():
    fr = []
    for i in range(8):
        b = math.sin(i / 8 * 2 * math.pi)
        fr.append((150, PP(P=(96.0, 100.0 + b * 0.8), S=(164.0, 98.0 + b * 1.0), na=-48 + b * 2, ha=58 + b * 3, at=b * 1.5, flame=1 + (i % 2), wind=b * 0.6)))
    return fr


def walk():
    fr = []
    for i in range(8):
        t = i / 8
        bob = abs(math.sin(t * 2 * math.pi * 2)) * 1.2
        P, S = body_at(t, -bob, 0.0)
        fr.append((130, PP(P=P, S=S, na=-46 + 2 * math.sin(t * 6.28), ha=56, hf=leg_cycle(t + 0.0, 92, 10, 7), hn=leg_cycle(t + 0.5, 100, 10, 7),
                           ff=leg_cycle(t + 0.25, 162, 10, 8), fn=leg_cycle(t + 0.75, 170, 10, 8), wind=-0.8)))
    return fr


def gallop():
    fr = []
    for i in range(6):
        t = i / 6
        pitch = 7 * math.sin(t * 2 * math.pi)
        bob = -4 * abs(math.sin(t * math.pi))
        P, S = body_at(t, bob - 2, pitch)
        fr.append((70, PP(P=P, S=S, na=-30 - pitch, ha=70, at=10.0, hf=leg_cycle(t + 0.0, 88, 22, 16, 0.9), hn=leg_cycle(t + 0.1, 98, 22, 16, 0.9),
                          ff=leg_cycle(t + 0.5, 164, 24, 18, 0.9), fn=leg_cycle(t + 0.6, 172, 24, 18, 0.9), trail=1, flame=2, glow=2, wind=-3.0)))
    return fr


def cprep():
    low = dict(P=(94.0, 104.0), S=(162.0, 108.0), na=-12.0, ha=78.0, at=34.0, hf=(86.0, 0.0, 0.0), hn=(96.0, 0.0, 0.0), ff=(166.0, 0.0, 0.0), fn=(176.0, 0.0, 0.0))
    return [(110, PP(P=(95.0, 102.0), S=(163.0, 103.0), na=-30.0, ha=68.0, at=16.0)),
            (120, PP(**low)),
            (120, PP(**dict(low, fn=(180.0, 8.0, 0.8), dust=1))),
            (120, PP(**dict(low, fn=(174.0, 0.0, 0.0), dust=2))),
            (200, PP(**dict(low, fn=(180.0, 8.0, 0.8), glow=2, flame=3, dust=1))),                 # telegraph
            (90, PP(**dict(low, glow=2, flame=3, trail=1)))]


def skid():
    return [(90, PP(P=(98.0, 104.0), S=(164.0, 104.0), na=-20.0, ha=74.0, at=26.0, hf=(78.0, 0.0, 0.0), hn=(86.0, 0.0, 0.0), ff=(186.0, 0.0, 0.0), fn=(196.0, 0.0, 0.0), dust=2, wind=-2.0)),
            (100, PP(P=(96.0, 104.0), S=(162.0, 102.0), na=-26.0, ha=70.0, at=20.0, hf=(80.0, 0.0, 0.0), hn=(90.0, 0.0, 0.0), ff=(180.0, 0.0, 0.0), fn=(190.0, 0.0, 0.0), dust=2)),
            (110, PP(P=(96.0, 102.0), S=(163.0, 100.0), na=-36.0, ha=64.0, at=10.0, hf=(84.0, 0.0, 0.0), hn=(94.0, 0.0, 0.0), ff=(172.0, 0.0, 0.0), fn=(182.0, 0.0, 0.0), dust=1)),
            (130, PP(na=-44.0, ha=60.0, at=4.0, ff=(166.0, 0.0, 0.0), fn=(176.0, 0.0, 0.0))),
            (140, PP()), (140, PP())]


def rear():
    """Rears onto its hind legs, forelegs pawing the air, then stamps down: a shockwave (frame 6)."""
    fr = []
    ks = [(0, 0.0), (1, -16.0), (2, -28.0), (3, -38.0), (4, -41.0), (5, -26.0), (6, 2.0), (7, 4.0), (8, 2.0), (9, 0.0), (10, 0.0), (11, 0.0)]
    ms = [110, 110, 120, 140, 200, 70, 60, 120, 140, 140, 140, 150]
    for (i, pitch), m in zip(ks, ms):
        P = (96.0 + (4 if 1 <= i <= 5 else 0), 100.0 + (4 if 1 <= i <= 5 else 0))
        S = add(P, rot(sub(S0, P0), pitch))
        up = pitch < -10
        kw = dict(P=P, S=S, na=-48 - pitch * 0.6, ha=58 + pitch * 0.2, at=-pitch * 0.2, hf=(94.0, 0.0, 0.0), hn=(104.0, 0.0, 0.0))
        if up:
            kw.update(ff=(S[0] + 10, FL - S[1] - 26 + 30, 0.9), fn=(S[0] + 18 + 4 * math.sin(i), FL - S[1] - 30 + 34, 0.95))
            kw["ff"] = (S[0] + 8, max(0.0, (FL - S[1]) - 40), 0.95)
            kw["fn"] = (S[0] + 16 + 4 * math.sin(i * 1.3), max(0.0, (FL - S[1]) - 46), 1.0)
        else:
            kw.update(ff=(160.0 + (6 if i in (6, 7) else 0), 0.0, 0.0), fn=(172.0 + (6 if i in (6, 7) else 0), 0.0, 0.0))
        if i == 4:
            kw.update(glow=3, flame=3, jaw=0.8)
        if i in (6, 7):
            kw.update(dust=2, burst=1 if i == 6 else 2, flame=3, glow=2)
        fr.append((m, PP(**kw)))
    return fr


def toss():
    """Head low, then a violent upward sweep of the burning antlers (frames 4-5)."""
    low = dict(P=(92.0, 104.0), S=(160.0, 108.0), na=-8.0, ha=84.0, at=38.0, hf=(86.0, 0.0, 0.0), hn=(96.0, 0.0, 0.0), ff=(164.0, 0.0, 0.0), fn=(174.0, 0.0, 0.0))
    return [(100, PP(P=(94.0, 102.0), S=(162.0, 104.0), na=-28.0, ha=70.0, at=18.0)),
            (110, PP(**low)),
            (120, PP(**dict(low, fn=(178.0, 0.0, 0.0), ff=(168.0, 0.0, 0.0)))),
            (180, PP(**dict(low, glow=2, flame=3))),                                                         # telegraph
            (60, PP(P=(98.0, 100.0), S=(166.0, 96.0), na=-62.0, ha=28.0, at=-22.0, hf=(90.0, 0.0, 0.0), hn=(100.0, 0.0, 0.0), ff=(170.0, 0.0, 0.0), fn=(180.0, 0.0, 0.0), flame=3, wind=2.0)),
            (80, PP(P=(98.0, 99.0), S=(166.0, 94.0), na=-72.0, ha=12.0, at=-30.0, hf=(90.0, 0.0, 0.0), hn=(100.0, 0.0, 0.0), ff=(170.0, 0.0, 0.0), fn=(180.0, 0.0, 0.0), flame=3, wind=2.5)),
            (130, PP(P=(97.0, 100.0), S=(165.0, 97.0), na=-60.0, ha=34.0, at=-14.0, ff=(168.0, 0.0, 0.0), fn=(178.0, 0.0, 0.0))),
            (140, PP(na=-52.0, ha=48.0, at=-4.0)),
            (140, PP()), (140, PP())]


def leap():
    """A bounding leap (the engine carries it on frames 3..7), landing on frame 8."""
    crouch = dict(P=(94.0, 110.0), S=(162.0, 106.0), na=-38.0, ha=62.0, hf=(92.0, 0.0, 0.0), hn=(102.0, 0.0, 0.0), ff=(158.0, 0.0, 0.0), fn=(168.0, 0.0, 0.0))
    air1 = dict(P=(96.0, 96.0), S=add((96.0, 96.0), rot(sub(S0, P0), -14)), na=-40.0, ha=60.0, at=6.0, hf=(70.0, 18.0, 0.2), hn=(78.0, 16.0, 0.2),
                ff=(186.0, 34.0, 0.5), fn=(194.0, 30.0, 0.4), trail=1, flame=2, glow=2, wind=-2.0)
    air2 = dict(P=(96.0, 94.0), S=add((96.0, 94.0), rot(sub(S0, P0), 4)), na=-36.0, ha=64.0, at=8.0, hf=(82.0, 30.0, 0.9), hn=(90.0, 28.0, 0.9),
                ff=(176.0, 36.0, 0.9), fn=(184.0, 32.0, 0.9), trail=1, flame=2, glow=2, wind=-2.0)
    air3 = dict(P=(96.0, 96.0), S=add((96.0, 96.0), rot(sub(S0, P0), 12)), na=-30.0, ha=70.0, at=10.0, hf=(96.0, 24.0, 0.6), hn=(104.0, 22.0, 0.6),
                ff=(178.0, 14.0, 0.0), fn=(186.0, 12.0, 0.0), trail=1, flame=2, glow=2, wind=-1.5)
    return [(110, PP(**crouch)), (120, PP(**dict(crouch, P=(94.0, 114.0), S=(162.0, 110.0)))),
            (160, PP(**dict(crouch, P=(94.0, 114.0), S=(162.0, 110.0), glow=2, flame=3))),                  # telegraph
            (80, PP(**air1)), (100, PP(**air2)), (100, PP(**air2)), (90, PP(**air3)), (70, PP(**dict(air3, hf=(100.0, 10.0, 0.2), hn=(108.0, 8.0, 0.2), ff=(176.0, 2.0, 0.0), fn=(184.0, 0.0, 0.0)))),
            (80, PP(P=(98.0, 108.0), S=(166.0, 110.0), na=-30.0, ha=70.0, at=10.0, hf=(96.0, 0.0, 0.0), hn=(104.0, 0.0, 0.0), ff=(172.0, 0.0, 0.0), fn=(182.0, 0.0, 0.0), dust=2, burst=1, flame=3)),   # land
            (140, PP(P=(97.0, 104.0), S=(165.0, 103.0), na=-40.0, ha=62.0, ff=(170.0, 0.0, 0.0), fn=(180.0, 0.0, 0.0), dust=1))]


def bellow():
    up = dict(P=(98.0, 102.0), S=(166.0, 94.0), na=-80.0, ha=-20.0, at=-26.0, jaw=1.0, flame=3, glow=3)
    return [(110, PP(na=-54.0, ha=46.0)), (120, PP(P=(97.0, 101.0), S=(165.0, 97.0), na=-66.0, ha=20.0, at=-10.0, jaw=0.3)),
            (130, PP(**up)), (130, PP(**dict(up, burst=1))), (140, PP(**dict(up, burst=2, wind=1.5))), (150, PP(**dict(up, burst=3, wind=2.0))),
            (150, PP(**dict(up, jaw=0.7, wind=1.5))), (140, PP(P=(97.0, 101.0), S=(165.0, 97.0), na=-60.0, ha=30.0, at=-8.0, jaw=0.3)),
            (140, PP(na=-50.0, ha=52.0)), (140, PP())]


def stagger():
    low = dict(P=(94.0, 112.0), S=(160.0, 118.0), na=-6.0, ha=90.0, at=30.0, hf=(88.0, 0.0, 0.0), hn=(98.0, 0.0, 0.0), ff=(154.0, 0.0, 0.0), fn=(166.0, 0.0, 0.0), flame=0, glow=1, eye=1)
    return [(100, PP(P=(92.0, 102.0), S=(158.0, 96.0), na=-70.0, ha=10.0, at=-20.0, eye=1, wind=2.5)),
            (130, PP(**dict(low, P=(94.0, 108.0), S=(160.0, 110.0)))), (160, PP(**low)), (400, PP(**dict(low, ha=92.0))), (400, PP(**dict(low, ha=91.0)))]


def death():
    names = [n for n in LAYERS if n not in FXL]
    lie = dict(P=(92.0, 150.0), S=(162.0, 154.0), na=10.0, ha=100.0, at=40.0, hf=(70.0, 0.0, 1.0), hn=(80.0, 0.0, 1.0), ff=(180.0, 0.0, 1.0), fn=(190.0, 0.0, 1.0), flame=0, glow=1, eye=1, mound=0.2)
    fr = [(120, PP(P=(92.0, 102.0), S=(158.0, 94.0), na=-80.0, ha=-10.0, at=-24.0, jaw=1.0, flame=3, glow=3, wind=3.0)),
          (150, PP(P=(94.0, 118.0), S=(160.0, 126.0), na=-10.0, ha=86.0, at=26.0, hf=(86.0, 0.0, 0.3), hn=(96.0, 0.0, 0.3), ff=(166.0, 0.0, 0.5), fn=(176.0, 0.0, 0.5), flame=1, eye=1)),
          (170, PP(**dict(lie, P=(92.0, 136.0), S=(162.0, 140.0), mound=0.0))),
          (220, PP(**lie)),
          (200, PP(**dict(lie, mound=0.5, eye=0, glow=0)))]
    for k, (sq, burn) in enumerate(((0.9, 0.06), (0.78, 0.14), (0.64, 0.24), (0.5, 0.34), (0.36, 0.44), (0.26, 0.52), (0.2, 0.56))):
        fr.append((170 if k < 6 else 700, PP(**dict(lie, mound=0.7, eye=0, glow=0, flame=-1), post=collapse(names, sq, burn, seed=11, spread=0.3))))
    return fr


def rise():
    """The transformation: the stag heaves itself up out of the root mound, burning."""
    fr = []
    sk = [1.0, 0.85, 0.65, 0.45, 0.28, 0.14, 0.04, 0.0, 0.0, 0.0]
    mo = [1.0, 1.0, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4, 0.2, 0.0]
    for i in range(10):
        kw = dict(sink=sk[i], mound=mo[i], flame=2 + (i > 4), glow=2 + (i > 6), na=-60.0 + i * 1.2, ha=30.0 + i * 3, at=-12.0 + i * 1.2)
        if i >= 7:
            kw.update(jaw=0.6 if i == 8 else 0.2, burst=i - 6)
        fr.append((120 if i < 7 else 140, PP(**kw)))
    return fr


ANIMS = [("idle", idle), ("walk", walk), ("gallop", gallop), ("cprep", cprep), ("skid", skid), ("rear", rear), ("toss", toss),
         ("leap", leap), ("bellow", bellow), ("stagger", stagger), ("death", death), ("rise", rise)]


def build():
    K.setup(W_, H_)
    use = [a for a in ANIMS if ONLY is None or a[0] in ONLY]
    anims, infos = render_anims(LAYERS, draw, use, sway_key="S", loops=("idle", "walk", "gallop"))
    meta = None
    if ONLY is None:
        def box(pts, pad=1, floor=False, x_min=None):
            r = K.bbox(pts, pad)
            if x_min is not None and r[0] < x_min:
                r[2] -= x_min - r[0]; r[0] = x_min
            if floor:
                r[3] = H_ - r[1]
            return r
        def hb(i):   # a hurtbox around the barrel + neck (not the antlers or legs)
            r = box(i["body"], 0)
            if r is None: return None
            return [r[0] + 6, r[1] + 2, max(8, r[2] - 12), r[3] - 2]
        ant = lambda tag, ks, **kw: box(set().union(*[infos[tag][k]["ant"] for k in ks]), **kw)
        hooves = lambda tag, k: infos[tag][k]["hooves"]
        meta = {"native": 1, "frame": [W_, H_], "anchor": [128, 176],
                "hurtbox": hb(infos["idle"][0]),
                "attacks": {
                    "gallop": {"active": [0, 5], "hit": box(set().union(*[infos["gallop"][k]["ant"] | infos["gallop"][k]["body"] for k in range(6)]), floor=True, x_min=150)},
                    "toss": {"active": [4, 5], "hit": ant("toss", [3, 4, 5], floor=True, x_min=150)},
                    "rear": {"active": [6, 6], "hit": [150, 110, 64, 66]},
                    "leap": {"active": [8, 8], "hit": [60, 120, 150, 56]}},
                "spawn": {"rear": {"frame": 6, "at": spawn_pt(hooves("rear", 6)[1])},
                          "leap": {"frame": 8, "at": spawn_pt(hooves("leap", 8)[1])},
                          "bellow": {"frame": 3, "at": spawn_pt(infos["bellow"][3]["heart"])}},
                "telegraph": {"cprep": {"frame": 4, "at": spawn_pt(infos["cprep"][4]["eye"])},
                              "rear": {"frame": 4, "at": spawn_pt(infos["rear"][4]["eye"])},
                              "toss": {"frame": 3, "at": spawn_pt(infos["toss"][3]["eye"])},
                              "leap": {"frame": 2, "at": spawn_pt(infos["leap"][2]["eye"])},
                              "bellow": {"frame": 2, "at": spawn_pt(infos["bellow"][2]["eye"])}},
                "points": {tag: [{"eye": spawn_pt(i["eye"]), "heart": spawn_pt(i["heart"]), "hb": hb(i)} for i in infos[tag]] for tag, _ in ANIMS}}
    # gameplay is tuned to the shipped hitboxes: keep the existing meta (same rig, same bone lengths, same animations)
    keep = os.path.join(K.asebuild.ASSETS, "warden_stag_meta.json")
    if os.path.exists(keep) and "--new-meta" not in sys.argv:
        meta = None
    tags, flats = K.export("warden_stag", LAYERS, anims, meta, build=BUILD)
    contact("warden_stag", tags, flats, per_row=12, scale=2)
    print("built warden_stag")


if __name__ == "__main__":
    build()
