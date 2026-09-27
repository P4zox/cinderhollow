#!/usr/bin/env python3
"""EMBER HATCHLING — Cindervane's last cub, a summoned spell familiar  (+ the xrc_icons item icons).

    python3 art/gen_xrc_cub.py              full build (Aseprite) + preview
    python3 art/gen_xrc_cub.py --preview    preview only (no Aseprite)

xrc_cub: frames 40x32, faces RIGHT, body centre at (20,16) in every frame.
  tags: appear(7) fly(6, loop) spit(5, release = 3rd frame) dive(6) vanish(7) fireball(4, loop)
xrc_icons: 16x16, one frame/tag each: s_ember_hatchling c_x3_storm c_x3_slag c_x3_crown egg

Drawing: a tiny analytic rig (one continuous spine tube tail-tip -> head base, small wedge head + jaw,
swept horns, 3D-projected bat wings) sampled 4x4 per pixel with a majority vote, so silhouettes are clean
hard pixel clusters; shaded with a 5-tone slate ramp from tube normals and lit by ember seams.
"""
import math, os, sys, random
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
PREV = os.path.join(HERE, "previews")
PREVIEW_ONLY = "--preview" in sys.argv[1:]

W, H = 40, 32
CX, CY = 20.0, 16.0
SS = 4


def hx(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ------------------------------------------------------------------ palettes
OUT = hx("#07060a")          # exterior outline
OUT_EMB = hx("#3a120c")      # outline next to glow
SLATE = [hx(c) for c in ("#111016", "#1b1a21", "#28272f", "#3a3942", "#56545e")]
SLATE_FAR = [hx(c) for c in ("#0c0b10", "#131218", "#1c1b22", "#28272f", "#3a3942")]
EMB = [hx(c) for c in ("#8e2414", "#e0621e", "#ffb444", "#fff2c0")]      # deep red, orange, gold, pale
EMB_DIM = hx("#5a1a10")
MEM = [hx(c) for c in ("#1e0f12", "#2e1416", "#44191a")]                # near membrane
MEM_FAR = [hx(c) for c in ("#120a0d", "#1a0e11", "#241215")]
MEM_EDGE = hx("#5e2016")     # warm transition row inside the glowing trailing edge
BONE = [hx(c) for c in ("#2a2930", "#46444d", "#66636d")]
BONE_FAR = [hx(c) for c in ("#1b1a21", "#28272f", "#34333b")]
EMB_SET = set(EMB) | {EMB_DIM, MEM_EDGE}
HORN_C = hx("#8a8690")

LIGHT = np.array([-0.35, -0.8, 0.5]); LIGHT = LIGHT / np.linalg.norm(LIGHT)

# sample grid (pixel-space coordinates of the 4x4 subsamples)
_gy, _gx = np.mgrid[0:H * SS, 0:W * SS]
SXg = (_gx + 0.5) / SS
SYg = (_gy + 0.5) / SS


# ------------------------------------------------------------------ geometry helpers
def v(a, r=1.0):
    a = math.radians(a); return np.array([math.cos(a) * r, math.sin(a) * r])


def rot(p, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return np.array([p[0] * c - p[1] * s, p[0] * s + p[1] * c])


def catmull(pts, rads, step=0.35):
    """Catmull-Rom through pts, radii linearly interpolated per segment -> dense polyline."""
    P = [np.array(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    outp, outr = [], []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for j in range(n):
            t = j / n
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                       + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            outp.append(q); outr.append(rads[i - 1] + (rads[i] - rads[i - 1]) * t)
    outp.append(P[-2]); outr.append(rads[-1])
    return np.array(outp), np.array(outr)


def tube(poly, rads):
    """Tapered tube over dense polyline -> inside mask, normal (nx,ny,nz), signed side s (+ = right of
    direction = belly for forward-pointing chains), arc param a in [0,1]."""
    best = np.full(SXg.shape, 1e9); S = np.zeros(SXg.shape); A = np.zeros(SXg.shape)
    NX = np.zeros(SXg.shape); NY = np.zeros(SXg.shape)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    tot = max(L[-1], 1e-6)
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]; d = b - a; ll = d @ d
        if ll < 1e-9:
            continue
        t = np.clip(((SXg - a[0]) * d[0] + (SYg - a[1]) * d[1]) / ll, 0, 1)
        qx = a[0] + d[0] * t; qy = a[1] + d[1] * t
        ex, ey = SXg - qx, SYg - qy
        dist = np.sqrt(ex * ex + ey * ey)
        r = rads[i] + (rads[i + 1] - rads[i]) * t
        sc = dist - r
        upd = sc < best
        best[upd] = sc[upd]
        rr = np.maximum(r, 1e-3)
        NX[upd] = (ex / rr)[upd]; NY[upd] = (ey / rr)[upd]
        dn = np.sqrt(ll)
        S[upd] = ((ex * -d[1] + ey * d[0]) / dn / rr)[upd]
        A[upd] = ((L[i] + t * dn) / tot)[upd]
    m = best < 0
    NZ = np.sqrt(np.clip(1 - NX * NX - NY * NY, 0, 1))
    return m, NX, NY, NZ, S, A


def poly_mask(pts):
    """Even-odd point in polygon on the sample grid."""
    pts = np.array(pts, float); m = np.zeros(SXg.shape, bool)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        if y1 == y2:
            continue
        cond = (SYg >= min(y1, y2)) & (SYg < max(y1, y2))
        xi = x1 + (SYg - y1) * (x2 - x1) / (y2 - y1)
        m ^= cond & (SXg < xi)
    return m


def scallop(a, b, toward, k):
    """Inward-curving trailing edge a->b (quadratic, control pulled toward `toward`)."""
    mid = (a + b) / 2; d = b - a; L = np.linalg.norm(d) + 1e-9
    n = np.array([-d[1], d[0]]) / L
    if n @ (toward - mid) < 0:
        n = -n
    c = mid + n * (2 * k * L)
    return [(1 - t) ** 2 * a + 2 * (1 - t) * t * c + t * t * b for t in np.linspace(0, 1, 7)[1:]]


# ------------------------------------------------------------------ wing keys (body-local, relative to the shoulder)
def WK(elbow, wrist, tips, root):
    return [np.array(p, float) for p in [elbow, wrist] + tips + [root]]


W_UP = WK((-2.4, -3.6), (-0.8, -8.0), [(-4.6, -13.0), (-10.8, -10.0), (-13.4, -4.4)], (-7.0, -0.1))
W_MID = WK((-3.0, -2.2), (-0.6, -5.4), [(-8.0, -8.6), (-13.2, -5.4), (-13.8, -0.8)], (-7.0, -0.1))
W_DOWN = WK((-1.0, 2.6), (1.2, 5.6), [(-0.8, 11.2), (-5.8, 9.8), (-9.8, 4.4)], (-7.0, -0.1))
W_REC = WK((-2.6, -2.8), (-1.2, -6.8), [(-7.0, -10.4), (-11.6, -7.4), (-12.0, -2.8)], (-7.0, -0.1))
W_FOLD = WK((-2.2, -1.4), (0.2, -2.6), [(-9.6, -3.4), (-10.8, -2.0), (-9.8, -0.8)], (-7.0, -0.1))
FLAP_KEYS = [(0.0, W_UP), (0.22, W_MID), (0.45, W_DOWN), (0.72, W_REC), (1.0, W_UP)]


def _polar_lerp(A, B, k):
    out = []
    for a, b in zip(A, B):
        ra, rb = np.linalg.norm(a), np.linalg.norm(b)
        ta, tb = math.atan2(a[1], a[0]), math.atan2(b[1], b[0])
        d = (tb - ta + math.pi) % (2 * math.pi) - math.pi
        t = ta + d * k; r = ra + (rb - ra) * k
        out.append(np.array([math.cos(t) * r, math.sin(t) * r]))
    return out


def wing_key(flap, fold, rot_deg=0.0, scale=1.0):
    t = flap % 1.0
    for (t0, A), (t1, B) in zip(FLAP_KEYS[:-1], FLAP_KEYS[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0); k = k * k * (3 - 2 * k)
            shp = _polar_lerp(A, B, k); break
    if fold > 0:
        shp = _polar_lerp(shp, W_FOLD, fold)
    return [rot(p * scale, rot_deg) for p in shp]


# ------------------------------------------------------------------ pose
def pose(**k):
    P = dict(bx=0.0, by=0.0, ang=-4.0, neck_a=-62.0, neck_b=42.0, head_a=18.0, jaw=0.0,
             droop=34.0, curl=[-2, 6, 14, 20, 22, 22], sway=0.0, sway_ph=0.0,
             flap=0.0, fold=0.0, flap_far=None, fold_far=None, wrot=0.0, legs=0.0,
             pulse=0.0, mouth_glow=0.0, throat=0.0)
    P.update(k)
    return P


def render_cub(P):
    """-> RGBA 40x32 image (outlined), plus dict of key points (screen)."""
    C = np.array([CX + P["bx"], CY + P["by"]])

    def S(p):   # body-local -> screen
        return C + rot(np.array(p, float), P["ang"])

    # ---- spine: tail tip ... hip, mid, chest, neck, head base
    hip = np.array([-4.0, 0.3]); mid = np.array([-0.1, 0.5]); chest = np.array([3.6, -0.2])
    n1 = chest + v(P["neck_a"], 2.8)
    hb = n1 + v(P["neck_a"] + P["neck_b"], 2.4)
    tail = [hip]; th = 180 - P["droop"]
    segl = [2.1, 2.0, 1.8, 1.6, 1.4, 1.2]
    for i, sl in enumerate(segl):
        th += P["curl"][i] + P["sway"] * (i + 1) / 6 * math.sin(P["sway_ph"] - i * 0.8)
        tail.append(tail[-1] + v(th, sl))
    spine_pts = list(reversed(tail[1:])) + [hip, mid, chest, n1, hb]
    spine_r = [0.5, 0.62, 0.8, 1.0, 1.2, 1.5, 1.85, 2.3, 2.4, 1.2, 0.95]
    spine_scr = [S(p) for p in spine_pts]
    tail_tip = [S(p) for p in tail[3:]]
    poly, rads = catmull(spine_scr, spine_r)
    a_hip = 6 / 10; a_chest = 8 / 10  # approx (param by arc later)

    ha = P["head_a"]; habs = ha + P["ang"]
    def Hh(x, y):   # head-local -> screen
        return S(hb + rot(np.array([x, y]), ha))
    skull = [Hh(-0.6, -0.1), Hh(1.0, -0.2), Hh(2.8, 0.1), Hh(4.6, 0.35)]
    skull_r = [1.35, 1.3, 0.85, 0.45]
    hinge = Hh(0.4, 0.7)
    jd = v(habs + P["jaw"])
    jaw_pts = [hinge, hinge + jd * 2.0, hinge + jd * 3.9]
    jaw_r = [0.7, 0.55, 0.38]
    horn = [Hh(0.2, -1.2), Hh(-2.2, -2.4), Hh(-4.6, -3.1)]
    horn_r = [0.62, 0.42, 0.22]
    horn2 = [Hh(-0.6, 0.2), Hh(-2.4, 0.3)]
    horn2_r = [0.5, 0.2]
    eye = Hh(1.25, -0.55)
    mouth = Hh(4.4, 0.9) if P["jaw"] < 10 else (Hh(4.6, 0.4) + hinge + jd * 4.0) / 2 + 0.0

    # legs
    def leg(base, off, far):
        a = base + np.array(off)
        tuck = P["legs"]
        pts = [a, a + np.array([-2.0 - tuck, 2.0 - tuck * 0.5]), a + np.array([-4.0 - tuck * 1.5, 2.3 - tuck])]
        return [S(p + (np.array([0.9, -0.5]) if far else 0)) for p in pts]
    hind_n = leg(hip, (0.9, 1.4), False); hind_f = leg(hip, (0.9, 1.4), True)
    def fleg(far):
        a = chest + np.array([-0.4, 1.7]); tuck = P["legs"]
        pts = [a, a + np.array([0.9 - tuck, 1.7 - tuck * 0.4]), a + np.array([2.1 - tuck * 1.2, 1.8 - tuck * 0.6])]
        return [S(p + (np.array([0.9, -0.5]) if far else 0)) for p in pts]
    fore_n = fleg(False); fore_f = fleg(True)

    # wings
    def wing(side):
        far = side < 0
        flap = P["flap_far"] if (far and P["flap_far"] is not None) else P["flap"]
        fold = P["fold_far"] if (far and P["fold_far"] is not None) else P["fold"]
        sh = np.array([2.7, -2.2]) if far else np.array([1.6, -1.6])
        sh2 = np.array([1.0, -2.3]) if far else np.array([0.0, -2.0])
        sh3 = np.array([-1.5, -2.2]) if far else np.array([-2.5, -1.9])
        pts = wing_key(flap, fold, P["wrot"] + (10.0 if far else 0.0) * (1 - fold), 0.78 if far else 0.9)
        def Wp(o): return S(sh + o)
        el, wr = Wp(pts[0]), Wp(pts[1]); tips = [Wp(q) for q in pts[2:5]]; root = Wp(pts[5])
        outline = [S(sh), el, wr, tips[0]]
        for i in range(2):
            outline += scallop(tips[i], tips[i + 1], wr, 0.13)
        tr = scallop(tips[2], root, wr, 0.08)
        outline += tr
        ntrail = len(outline) - 3
        outline += [S(sh3), S(sh2)]
        arm = [S(sh), el, wr]
        return dict(outline=outline, arm=arm, wr=wr, tips=tips, root=root, sh=S(sh),
                    lead=[S(sh), el, wr, tips[0]], trail=outline[3:3 + ntrail])
    wn = wing(+1); wf = wing(-1)

    # ---- composite on the sample grid
    LAB = np.zeros(SXg.shape, np.int16)
    NXg = np.zeros(SXg.shape); NYg = np.zeros(SXg.shape); NZg = np.ones(SXg.shape)
    SSg = np.zeros(SXg.shape); AAg = np.zeros(SXg.shape)
    own = {}

    def put(lab, m, nx=None, ny=None, nz=None, s=None, a=None):
        LAB[m] = lab
        if nx is not None:
            NXg[m] = nx[m]; NYg[m] = ny[m]; NZg[m] = nz[m]
        else:
            NXg[m] = 0; NYg[m] = 0; NZg[m] = 1
        SSg[m] = s[m] if s is not None else 0
        AAg[m] = a[m] if a is not None else 0

    def tubeput(lab, pts, rs, dense=True):
        pp, rr = catmull(pts, rs, 0.3) if dense else (np.array(pts), np.array(rs))
        m, nx, ny, nz, s, a = tube(pp, rr)
        put(lab, m, nx, ny, nz, s, a)
        return m

    ID = dict(fwm=1, fwa=2, fleg=3, mouth=4, body=5, horn=6, head=7, jaw=8, nleg=9, nwm=10, nwa=11)

    
    if P["jaw"] > 6:
        mm = poly_mask([hinge, Hh(4.8, 0.5), hinge + jd * 4.1, hinge + jd * 1.0])
        put(ID["mouth"], mm)
    m, nx, ny, nz, s, a = tube(poly, rads); put(ID["body"], m, nx, ny, nz, s, a)
    tubeput(ID["head"], skull, skull_r)
    tubeput(ID["jaw"], jaw_pts, jaw_r)
    tubeput(ID["nleg"], hind_n[:2], [0.9, 0.6])

    # ---- downsample: majority coverage, then mode label
    def blocks(arr):
        return arr.reshape(H, SS, W, SS).transpose(0, 2, 1, 3).reshape(H, W, SS * SS)
    LB = blocks(LAB)
    cov = (LB > 0).sum(-1)
    lab1 = np.zeros((H, W), np.int16); best = np.zeros((H, W), int)
    for l in range(1, 12):
        c = (LB == l).sum(-1)
        upd = c > best; lab1[upd] = l; best[upd] = c[upd]
    lab1[cov < SS * SS // 2] = 0
    def avg(arr):
        B = blocks(arr); sel = (LB == lab1[..., None])
        return (B * sel).sum(-1) / np.maximum(sel.sum(-1), 1)
    nx1, ny1, nz1, s1, a1 = avg(NXg), avg(NYg), avg(NZg), avg(SSg), avg(AAg)

    # cleanup: drop pixels with no opaque 4-neighbour
    op = lab1 > 0
    nb = np.zeros_like(op, int)
    nb[1:] += op[:-1]; nb[:-1] += op[1:]; nb[:, 1:] += op[:, :-1]; nb[:, :-1] += op[:, 1:]
    lab1[op & (nb == 0)] = 0

    # ---- shade
    img = np.zeros((H, W, 4), np.uint8)
    ndl = nx1 * LIGHT[0] + ny1 * LIGHT[1] + nz1 * LIGHT[2]
    def ramp5(val, pal):
        i = 0 if val < -0.05 else 1 if val < 0.3 else 2 if val < 0.62 else 3 if val < 0.86 else 4
        return pal[i]
    def band(y, x, pal, bias=0.0):
        t = -ny1[y, x] * 0.85 - nx1[y, x] * 0.25 + bias
        i = 4 if t > 0.62 else 3 if t > 0.12 else 2 if t > -0.35 else 1 if t > -0.72 else 0
        return pal[i]
    pulse = P["pulse"]
    for y in range(H):
        for x in range(W):
            l = lab1[y, x]
            if l == 0:
                continue
            d = ndl[y, x]
            if l in (ID["body"], ID["head"]):
                c = band(y, x, SLATE)
                if l == ID["body"]:
                    s, a = s1[y, x], a1[y, x]
                    # belly/throat seam: a glowing line on the underside from tail base to throat
                    if 0.6 < s < 0.86 and 0.38 < a < 0.97:
                        if a > 0.8:
                            c = EMB[2] if (pulse > 0.5 or P["throat"] > 0.3) else EMB[1]
                            if P["throat"] > 0.7:
                                c = EMB[3]
                        elif a > 0.56:
                            c = EMB[1] if pulse > 0.5 else EMB[0]
                        else:
                            c = EMB[0]
                    elif s >= 0.86 and 0.5 < a < 0.95:
                        c = SLATE[0]
            elif l == ID["jaw"]:
                c = band(y, x, SLATE, -0.5)
            elif l == ID["horn"]:
                c = SLATE[3] if d > 0.35 else SLATE[2]
            elif l in (ID["fleg"],):
                c = SLATE_FAR[2] if d > 0.3 else SLATE_FAR[1]
            elif l == ID["nleg"]:
                c = SLATE[2] if d > 0.3 else SLATE[1]
            elif l == ID["fwa"]:
                c = BONE_FAR[2] if d > 0.3 else BONE_FAR[1]
            elif l == ID["nwa"]:
                c = BONE[2] if d > 0.45 else BONE[1]
            elif l == ID["fwm"]:
                c = MEM_FAR[1]
            elif l == ID["nwm"]:
                c = MEM[1]
            elif l == ID["mouth"]:
                c = EMB[0]
            img[y, x] = c

    # ---- wings, drawn at 1x as clean vector shapes (sharp finger tips, 1px bones)
    NOWING = os.environ.get("NOWING")
    def seg_dist(p, a, b):
        d = b - a; t = np.clip((p - a) @ d / max(d @ d, 1e-9), 0, 1); return np.linalg.norm(p - (a + d * t))
    def raster_poly(pts):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).polygon([(float(q[0]) - 0.5, float(q[1]) - 0.5) for q in pts], fill=255)
        return np.array(im) > 0
    def line_px(a_, b_):
        out = []; n = int(max(abs(b_ - a_)) * 3) + 1
        for j in range(n + 1):
            q = a_ + (b_ - a_) * j / n; pt = (int(math.floor(q[0])), int(math.floor(q[1])))
            if not out or out[-1] != pt:
                out.append(pt)
        return out
    for wg, far in ((wf, True), (wn, False)):
        if NOWING:
            break
        lab = ID["fwm"] if far else ID["nwm"]
        om = raster_poly(wg["outline"])
        memc = MEM_FAR if far else MEM
        pal = BONE_FAR if far else BONE
        for y in range(H):
            for x in range(W):
                if not om[y, x]:
                    continue
                if far and lab1[y, x] != 0:
                    continue
                p = np.array([x + 0.5, y + 0.5])
                dlead = min(seg_dist(p, q0, q1) for q0, q1 in zip(wg["lead"][:-1], wg["lead"][1:]))
                dtrail = min(seg_dist(p, q0, q1) for q0, q1 in zip(wg["trail"][:-1], wg["trail"][1:]))
                edge = any(not (0 <= y + dy < H and 0 <= x + dx < W and om[y + dy, x + dx])
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                droot = seg_dist(p, wg["sh"], wg["root"])
                if edge and dtrail < dlead and droot > 1.2:
                    c = EMB_DIM if far else (EMB[1] if pulse > 0.5 else EMB[0])
                elif dlead < 1.6:
                    c = memc[2]
                else:
                    c = memc[1]
                img[y, x] = c; lab1[y, x] = lab
        # finger struts (secondary fingers), then the leading-edge bones
        if not far:
            for t in wg["tips"][1:]:
                for (xx, yy) in line_px(wg["wr"], t)[1:-1]:
                    if 0 <= yy < H and 0 <= xx < W and lab1[yy, xx] == lab and tuple(int(c) for c in img[yy, xx]) not in EMB_SET:
                        img[yy, xx] = memc[2]
        bone = [wg["sh"], wg["arm"][1], wg["wr"], wg["tips"][0]]
        for k, (a_, b_) in enumerate(zip(bone[:-1], bone[1:])):
            for (xx, yy) in line_px(a_, b_):
                if 0 <= yy < H and 0 <= xx < W and (lab1[yy, xx] in (0, lab) or not far):
                    if far and lab1[yy, xx] not in (0, lab):
                        continue
                    img[yy, xx] = pal[2] if k < 2 else pal[1]
                    lab1[yy, xx] = lab
        # claw at the wrist
        wx, wy = int(math.floor(wg["wr"][0])), int(math.floor(wg["wr"][1]))
        if 0 <= wy < H and 0 <= wx < W and not far:
            img[wy, wx] = HORN_C

    # horns: crisp 1px swept-back lines (outline gives them body)
    HORN = HORN_C
    for hp, cols in ((tail_tip, (SLATE[2], SLATE[2], SLATE[1])), (horn, (SLATE[4], HORN, HORN, SLATE[4])), (horn2, (SLATE[2], SLATE[2]))):
        qs = []
        for a_, b_ in zip(hp[:-1], hp[1:]):
            n = int(max(abs(b_ - a_)) * 3) + 1
            qs += [a_ + (b_ - a_) * j / n for j in range(n + 1)]
        is_tail = hp is tail_tip
        for j, q in enumerate(qs):
            xx, yy = int(q[0]), int(q[1])
            if not (0 <= yy < H and 0 <= xx < W):
                continue
            if is_tail:
                if lab1[yy, xx] == 0:
                    img[yy, xx] = cols[min(len(cols) - 1, j * len(cols) // len(qs))]; lab1[yy, xx] = ID["body"]
            elif lab1[yy, xx] not in (ID["head"],):
                img[yy, xx] = cols[min(len(cols) - 1, j * len(cols) // len(qs))]
                lab1[yy, xx] = ID["horn"]
    # eye
    ex, ey_ = int(eye[0]), int(eye[1])
    if 0 <= ey_ < H and 0 <= ex < W and lab1[ey_, ex] == ID["head"]:
        img[ey_, ex] = EMB[3] if P["pulse"] > 0.5 else EMB[2]
    # mouth glow
    mg = P["mouth_glow"]
    if lab1.any() and P["jaw"] > 6:
        for y in range(H):
            for x in range(W):
                if lab1[y, x] == ID["mouth"]:
                    p = np.array([x + 0.5, y + 0.5])
                    dd = np.linalg.norm(p - hinge)
                    img[y, x] = EMB[1] if (mg > 0.3 and dd > 1.2) else EMB[0]
    # internal outlines: far wing against everything in front of it; body against the near membrane
    grp = np.zeros((H, W), np.int8)
    grp[(lab1 == ID["fwa"])] = 1
    grp[(lab1 >= ID["fleg"]) & (lab1 <= ID["nleg"])] = 2
    grp[lab1 == ID["horn"]] = 2
    grp[(lab1 == ID["nwm"]) | (lab1 == ID["nwa"])] = 3
    src = img.copy()
    for y in range(H):
        for x in range(W):
            g = grp[y, x]
            if g == 0 or g == 3:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and grp[yy, xx] > g:
                    front = tuple(int(q) for q in src[yy, xx])
                    if g == 1 or (g == 2 and lab1[yy, xx] == ID["nwm"] and front not in EMB_SET):
                        if g == 2 and lab1[y, x] in (ID["head"], ID["jaw"]):
                            continue
                        img[y, x] = OUT
                        break
    return img, dict(mouth=mouth, hinge=hinge, eye=eye, head=hb)


def outline(img):
    a = img[..., 3] > 0
    out = img.copy()
    for y in range(H):
        for x in range(W):
            if a[y, x]:
                continue
            glow = False; hit = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and a[yy, xx]:
                    hit = True
                    if tuple(img[yy, xx]) in (EMB[1], EMB[2], EMB[3]):
                        glow = True
            if hit:
                out[y, x] = OUT_EMB if glow else OUT
    return out


# ------------------------------------------------------------------ fx helpers
def put_px(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        img[y, x] = c


def spark(img, x, y, size):
    """size 0: 1px dim  1: 1px bright  2: plus-shape  3: big plus with pale core"""
    if size == 0:
        put_px(img, x, y, EMB[0])
    elif size == 1:
        put_px(img, x, y, EMB[2])
    elif size == 2:
        put_px(img, x, y, EMB[2])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put_px(img, x + dx, y + dy, EMB[0])
    else:
        put_px(img, x, y, EMB[3])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put_px(img, x + dx, y + dy, EMB[1])


def ember_tint(img, k, core_pale=False):
    """Glow creeping in from the silhouette edge: pixels within k*maxdepth of the edge turn ember."""
    a = img[..., 3] > 0
    if not a.any() or k <= 0:
        return img
    # depth from edge (4-connected BFS)
    depth = np.full((H, W), 99)
    q = []
    for y in range(H):
        for x in range(W):
            if a[y, x] and any(not (0 <= y + dy < H and 0 <= x + dx < W and a[y + dy, x + dx])
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                depth[y, x] = 0; q.append((x, y))
    i = 0
    while i < len(q):
        x, y = q[i]; i += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= yy < H and 0 <= xx < W and a[yy, xx] and depth[yy, xx] > depth[y, x] + 1:
                depth[yy, xx] = depth[y, x] + 1; q.append((xx, yy))
    md = max(1, depth[a].max())
    out = img.copy()
    for y in range(H):
        for x in range(W):
            if not a[y, x]:
                continue
            c = tuple(int(q) for q in img[y, x])
            dep = depth[y, x]
            is_out = c in (OUT, OUT_EMB)
            glowing = c in (EMB[1], EMB[2], EMB[3])
            lum = sum(c[:3]) / 3
            if k >= 0.99:
                if dep == 0:
                    out[y, x] = OUT_EMB
                else:
                    d = dep / md
                    out[y, x] = EMB[3] if (core_pale and d > 0.45) else EMB[2] if d > 0.18 else EMB[1]
            elif k >= 0.4:
                # the whole body heats: dark-ember body, hot rim, bright seams
                if dep == 0:
                    out[y, x] = OUT_EMB
                elif dep == 1:
                    out[y, x] = EMB[1]
                elif glowing:
                    out[y, x] = EMB[2]
                elif is_out:
                    out[y, x] = EMB_DIM
                else:
                    out[y, x] = EMB[0] if lum > 45 else EMB_DIM
            else:
                # only a thin hot rim just inside the outline
                if dep == 1 and not is_out and not glowing:
                    out[y, x] = EMB[0] if k < 0.25 else EMB[1]
    return out


def _vnoise(x, y, seed, cell=2.0):
    def h(i, j):
        return ((i * 73856093) ^ (j * 19349663) ^ (seed * 83492791)) % 1000 / 1000.0
    gx, gy = x / cell, y / cell; i, j = int(math.floor(gx)), int(math.floor(gy)); fx, fy = gx - i, gy - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = h(i, j) + (h(i + 1, j) - h(i, j)) * fx
    b = h(i, j + 1) + (h(i + 1, j + 1) - h(i, j + 1)) * fx
    return a + (b - a) * fy


def dissolve(img, k, seed, drift=(0.4, -2.2)):
    """Crumble a glowing silhouette into embers: clustered holes eat in from the rim; lost pixels become a
    sparse set of drifting sparks."""
    rng = random.Random(seed)
    out = np.zeros_like(img)
    a = img[..., 3] > 0
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return out
    rmax = max(math.hypot(x + 0.5 - CX, y + 0.5 - CY) for x, y in zip(xs, ys)) + 0.5
    for y, x in zip(ys, xs):
        c = tuple(int(q) for q in img[y, x])
        rr = math.hypot(x + 0.5 - CX, y + 0.5 - CY) / rmax
        n = _vnoise(x, y, seed) * 0.65 + rr * 0.35
        if n > 1 - k:        # eaten
            if rng.random() < 0.2 * max(0.0, 1.0 - k) + 0.012:
                push = 1.0 + k * 0.8
                nx_ = CX + (x + 0.5 - CX) * push + drift[0] * k * 3 + rng.uniform(-1, 1)
                ny_ = CY + (y + 0.5 - CY) * push + drift[1] * k * 3 + rng.uniform(-1, 1)
                put_px(out, nx_, ny_, EMB[2] if rng.random() < 0.4 else EMB[1])
            continue
        if c in (OUT, OUT_EMB, EMB_DIM):
            # keep a dim rim only where the core survives
            out[y, x] = EMB[0]
        else:
            out[y, x] = c
    return out


def finish(P, glow=0.0, core_pale=False):
    img, pts = render_cub(P)
    img = outline(img)
    if glow > 0:
        img = ember_tint(img, glow, core_pale)
    return img, pts


# ------------------------------------------------------------------ poses
def fly_pose(t):
    return pose(by=0.8 * math.cos(2 * math.pi * t) - 0.2, flap=t, flap_far=(t - 0.05) % 1.0,
                neck_a=-62 + 4 * math.sin(2 * math.pi * t - 1.2), head_a=18 - 3 * math.sin(2 * math.pi * t - 1.4),
                sway=10.0, sway_ph=2 * math.pi * t, pulse=0.5 + 0.5 * math.cos(2 * math.pi * t))


CURL = pose(ang=-5, bx=-0.5, neck_a=-70, neck_b=130, head_a=125, droop=95, curl=[34, 36, 36, 34, 32, 30],
            flap=0.3, fold=0.75, flap_far=0.3, fold_far=0.75, wrot=-10.0, legs=1.2, pulse=1.0)


def lerp_pose(A, B, k):
    out = {}
    for key in A:
        a, b = A[key], B[key]
        if a is None or b is None:
            out[key] = b if k > 0.5 else a
        elif isinstance(a, list):
            out[key] = [x + (y - x) * k for x, y in zip(a, b)]
        else:
            out[key] = a + (b - a) * k
    for key in ("flap_far", "fold_far"):
        if A[key] is None or B[key] is None:
            pa = A[key] if A[key] is not None else A[key.replace("_far", "")]
            pb = B[key] if B[key] is not None else B[key.replace("_far", "")]
            out[key] = pa + (pb - pa) * k
    return out


def ease(t):
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ tags
FRAMES = []   # (img, ms, tagname, info)


def tag_appear():
    out = []
    rng = random.Random(7)
    egg_rx, egg_ry = 5.6, 7.0
    def egg_pts(n, scale, jitter, seed):
        r = random.Random(seed); pts = []
        for i in range(n):
            a = 2 * math.pi * i / n + r.uniform(-0.15, 0.15)
            rr = scale * (1 + r.uniform(-jitter, jitter))
            yy = -math.sin(a) * egg_ry * rr
            ww = egg_rx * rr * (1 - 0.12 * (yy / egg_ry))   # narrower top
            pts.append((CX + math.cos(a) * ww, CY + yy + 0.5))
        return pts
    # 0: a small ember
    img = np.zeros((H, W, 4), np.uint8)
    spark(img, CX - 0.5, CY, 3)
    for (x, y), s in zip(egg_pts(5, 1.9, 0.2, 1), (0, 1, 0, 0, 1)):
        spark(img, x, y, s)
    out.append((img, 90))
    # 1: egg-shaped burst of sparks condensing
    img = np.zeros((H, W, 4), np.uint8)
    for (x, y) in egg_pts(16, 1.25, 0.12, 2):
        spark(img, x, y, rng.choice((0, 1, 1)))
    for yy in range(-2, 3):
        for xx in range(-2, 2):
            if abs(xx + 0.5) + abs(yy) <= 2.5:
                put_px(img, CX + xx, CY + yy, EMB[2] if abs(xx + 0.5) + abs(yy) < 1.5 else EMB[1])
    put_px(img, CX - 1, CY, EMB[3]); put_px(img, CX, CY, EMB[3])
    out.append((img, 80))
    # 2: solid glowing egg
    img = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            dx = (x + 0.5 - CX); dy = (y + 0.5 - CY - 0.5)
            ww = egg_rx * (1 - 0.12 * (-dy / egg_ry))
            d = math.hypot(dx / ww, dy / egg_ry)
            if d <= 1.0:
                c = EMB[0] if d > 0.82 else EMB[1] if d > 0.55 else EMB[2] if d > 0.25 else EMB[3]
                # highlight shift up-left
                if d < 0.62 and dx < 0 and dy < 0 and c == EMB[1]:
                    c = EMB[2]
                img[y, x] = c
    img = outline_glow(img)
    for (x, y) in egg_pts(8, 1.45, 0.15, 3):
        spark(img, x, y, 0)
    out.append((img, 90))
    # 3: the egg bursts: glowing curled cub + shell shards
    cub, _ = finish(CURL, glow=1.0, core_pale=True)
    img = cub.copy()
    for i, (x, y) in enumerate(egg_pts(10, 1.25, 0.1, 4)):
        spark(img, x, y, 2 if i % 3 == 0 else 1)
    out.append((img, 80))
    # 4: curled cub, glow receding to the rim
    cub, _ = finish(lerp_pose(CURL, fly_pose(0.0), 0.15), glow=0.55)
    img = cub
    for (x, y) in egg_pts(7, 1.6, 0.2, 5):
        spark(img, x, y, 0)
    out.append((img, 80))
    # 5: wings unfolding
    P = lerp_pose(CURL, fly_pose(0.0), 0.6); P["fold"] = 0.45; P["fold_far"] = 0.45
    cub, _ = finish(P, glow=0.22)
    img = cub
    for (x, y) in egg_pts(5, 1.9, 0.25, 6):
        spark(img, x, y, 0)
    out.append((img, 80))
    # 6: first fly pose
    img, _ = finish(fly_pose(0.0))
    for (x, y) in egg_pts(3, 2.2, 0.2, 7):
        put_px(img, x, y, EMB[0]) if img[int(y) % H, int(x) % W, 3] == 0 else None
    out.append((img, 90))
    return out


def outline_glow(img):
    a = img[..., 3] > 0; o = img.copy()
    for y in range(H):
        for x in range(W):
            if not a[y, x] and any(0 <= y + dy < H and 0 <= x + dx < W and a[y + dy, x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[y, x] = OUT_EMB
    return o


def tag_fly():
    out = []; pts = []
    for i in range(6):
        img, p = finish(fly_pose(i / 6)); out.append((img, 90)); pts.append(p)
    return out, pts


def tag_spit():
    base = fly_pose(0.0)
    keys = [
        dict(neck_a=-72, neck_b=20, head_a=-18, jaw=8, flap=0.9, throat=0.4, bx=-0.6),                # rear
        dict(neck_a=-80, neck_b=16, head_a=-30, jaw=14, flap=0.0, throat=0.9, bx=-1.0, mouth_glow=0.4),  # max rear, glow
        dict(neck_a=-18, neck_b=10, head_a=6, jaw=34, flap=0.4, throat=1.0, bx=1.0, mouth_glow=1.0),    # RELEASE
        dict(neck_a=-30, neck_b=20, head_a=10, jaw=16, flap=0.55, throat=0.4, bx=0.6, mouth_glow=0.4),
        dict(neck_a=-52, neck_b=36, head_a=16, jaw=2, flap=0.78, throat=0.0, bx=0.2),
    ]
    out = []; pts = []
    for i, k in enumerate(keys):
        P = dict(base); P.update(k); P["pulse"] = 1.0 if i in (1, 2) else 0.5
        P["flap_far"] = (P["flap"] - 0.05) % 1.0; P["fold"] = 0.0; P["fold_far"] = 0.0
        P["sway_ph"] = i * 1.1
        img, p = finish(P)
        if i == 2:   # bright ember in the open jaws
            mx, my = p["mouth"]
            spark(img, mx, my, 3)
            put_px(img, mx + 2, my - 1, EMB[2]); put_px(img, mx + 2, my + 2, EMB[1])
        if i == 1:
            mx, my = p["mouth"]; put_px(img, mx, my, EMB[2])
        out.append((img, [90, 110, 120, 90, 90][i])); pts.append(p)
    return out, pts


def tag_dive():
    base = fly_pose(0.25)
    keys = [
        dict(ang=14, neck_a=-30, neck_b=18, head_a=4, flap=0.2, fold=0.4, droop=4, curl=[3, 3, 3, 3, 3, 3], legs=0.4),
        dict(ang=28, neck_a=-14, neck_b=8, head_a=2, flap=0.25, fold=0.8, droop=2, curl=[1, 1, 1, 1, 1, 1], legs=0.8),
        dict(ang=40, neck_a=-6, neck_b=4, head_a=0, flap=0.25, fold=1.0, droop=0, curl=[0, 0, 0, 0, 0, 0], legs=1.0),
        dict(ang=40, neck_a=-5, neck_b=3, head_a=0, flap=0.25, fold=1.0, droop=-1, curl=[0, 1, 0, -1, 0, 1], legs=1.0),
        dict(ang=40, neck_a=-8, neck_b=4, head_a=-2, flap=0.25, fold=1.0, droop=0, curl=[0, 0, 1, 0, -1, 0], legs=1.0, jaw=28),
        dict(ang=40, neck_a=-8, neck_b=4, head_a=-4, flap=0.25, fold=1.0, droop=-1, curl=[0, 1, 0, -1, 0, 1], legs=1.0, jaw=42, mouth_glow=0.5),
    ]
    out = []
    for i, k in enumerate(keys):
        P = dict(base); P.update(k); P["flap_far"] = P["flap"]; P["fold_far"] = P["fold"]; P["sway"] = 0
        P["pulse"] = 1.0 if i >= 3 else 0.5
        img, p = finish(P)
        # a few trailing embers behind the arrow once it is sleek
        if i >= 2:
            back = rot(np.array([-1.0, 0.0]), P["ang"])
            for j, dd in enumerate((14, 16.5, 19)):
                q = np.array([CX, CY]) + back * dd + rot(np.array([0, (j - 1) * 2.2 + (i % 2)]), P["ang"])
                if img[int(q[1]) % H, int(q[0]) % W, 3] == 0:
                    put_px(img, q[0], q[1], EMB[0] if j else EMB[1])
        out.append((img, [80, 70, 70, 70, 80, 100][i]))
    return out


def tag_vanish():
    out = []
    f0 = fly_pose(0.0)
    P1 = lerp_pose(f0, CURL, 0.45)
    img, _ = finish(P1, glow=0.18); out.append((img, 80))
    P2 = lerp_pose(f0, CURL, 0.8)
    img, _ = finish(P2, glow=0.5); out.append((img, 80))
    img, _ = finish(CURL, glow=1.0, core_pale=True)
    full = img.copy(); out.append((img, 90))
    rng = random.Random(11)
    for k, n in ((0.35, 3), (0.62, 4), (0.86, 4), (1.01, 3)):
        img = dissolve(full, k, seed=5)
        for j in range(n):
            a = rng.uniform(0, 2 * math.pi); r = 7 + k * 8 + rng.uniform(-1.5, 1.5)
            put_px(img, CX + math.cos(a) * r, CY + math.sin(a) * r * 0.75 - k * 4, EMB[2] if j % 2 == 0 else EMB[0])
        out.append((img, 80 if k < 1 else 100))
    return out


def tag_fireball():
    out = []
    for f in range(4):
        img = np.zeros((H, W, 4), np.uint8)
        # tail: tapered tongues to the LEFT
        for y in range(H):
            for x in range(W):
                dx = x + 0.5 - CX; dy = y + 0.5 - CY
                # core disc r~3.5
                d = math.hypot(dx * 1.0, dy * 1.0)
                if d <= 3.6:
                    c = EMB[3] if math.hypot(dx - 0.6, dy + 0.3) < 1.6 else EMB[2] if d < 2.7 else EMB[1]
                    img[y, x] = c
                    continue
                if dx < 0:
                    L = -dx
                    wob = 0.7 * math.sin(L * 0.9 - f * 1.6)
                    half = 3.3 * (1 - L / (10.5 + (f % 2)))
                    if L < 11.5 and abs(dy - wob * (L / 8)) < half:
                        inner = abs(dy - wob * (L / 8)) < half * 0.45
                        img[y, x] = EMB[1] if (inner and L < 7) else EMB[0]
        # outline in deep red
        a = img[..., 3] > 0; o = img.copy()
        for y in range(H):
            for x in range(W):
                if not a[y, x] and any(0 <= y + dy < H and 0 <= x + dx < W and a[y + dy, x + dx]
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    o[y, x] = OUT_EMB
        img = o
        # trailing sparks
        rng = random.Random(40 + f)
        for j in range(3):
            put_px(img, CX - 9 - rng.uniform(0, 5), CY + rng.uniform(-4, 4), EMB[1] if j == 0 else EMB[0])
        out.append((img, 70))
    return out


# ------------------------------------------------------------------ icons (16x16, hand-placed)
IPAL = {
    ".": None, "o": hx("#08070c"),
    # slate
    "1": hx("#16151c"), "2": hx("#23222a"), "3": hx("#35343d"), "4": hx("#4f4d57"), "5": hx("#6e6b76"),
    # ember
    "r": hx("#8e2414"), "e": hx("#e0621e"), "g": hx("#ffb444"), "p": hx("#fff2c0"), "d": hx("#3a120c"),
    # storm glass
    "b": hx("#1c3060"), "c": hx("#3f6fb8"), "l": hx("#86b8ec"), "w": hx("#d4ecff"), "W": hx("#ffffff"),
    "s": hx("#96a2c4"),
    # gold / petal
    "y": hx("#aa6e28"), "Y": hx("#f0c060"), "P": hx("#fff8e6"), "k": hx("#6a4a26"), "h": hx("#e6d8b8"),
    # iron
    "i": hx("#2a2226"), "j": hx("#483a3a"), "J": hx("#7a665c"),
    # membrane
    "m": hx("#2e1f26"),
}

ICONS = {
    "s_ember_hatchling": [
        "................",
        "..o.......oo....",
        ".o3o.....o4o....",
        ".o43o...o43o....",
        "..o43ooo432o....",
        "..o3444442o.oo..",
        "...o43p3342o44o.",
        "...o3gg33ooo2ooo",
        "..orreeg2ooorro.",
        ".oreggegeo.orr..",
        ".oreggpgero.....",
        ".oreegggero.....",
        "..oreeeero......",
        "...orrrro.......",
        "....oooo........",
        "................",
    ],
    "c_x3_storm": [
        "................",
        "...........oo...",
        "...l......owWo..",
        "..lWl....owlWo..",
        "...l....owlclo..",
        ".......owlcwlo..",
        "......owlcWlo...",
        ".....owcWwlo....",
        "....owlcwlco....",
        "...owlclwlo.....",
        "...owlclco......",
        "..olwlcbo.......",
        "..olcbbo........",
        ".osbbo..........",
        "oso.............",
        "oo..............",
    ],
    "c_x3_slag": [
        "................",
        "......oooo......",
        ".....oj44jo.....",
        "....oj3443jo....",
        "....oi3ee3io....",
        "....oi2eg2io....",
        "....oi32e3io....",
        ".....oi3e3io....",
        ".....oi2g2io....",
        ".....oie2e3o....",
        "....oi3gp3io....",
        "....oi2e2e2o....",
        "....oi3232io....",
        ".....oiiiio.....",
        "......oooo......",
        "................",
    ],
    "c_x3_crown": [
        "................",
        "...o...oo...o...",
        "..oYo.oYYo.oYo..",
        "..oyo.oyYo.oyo..",
        "...oYooYyooYo...",
        "....oyYyYyYo....",
        "....ooooooo.....",
        "...ohPPPPPho....",
        "..ohPooooPPho...",
        "..oPo.....oPo...",
        "..oPo.....oho...",
        "..ohPo...oPho...",
        "...ohPPPPPho....",
        "....ooooooo.....",
        "................",
        "................",
    ],
    "egg": [
        "................",
        "......oooo......",
        ".....o3443o.....",
        "....o345432o....",
        "....o34e432o....",
        "...o334g4322o...",
        "...o33ge33r2o...",
        "...o32e332e2o...",
        "...o2e3322g1o...",
        "...o2g32eee1o...",
        "...o22rpg221o...",
        "....o2reer1o....",
        "....o112111o....",
        ".....o1111o.....",
        "......oooo......",
        "................",
    ],
}


def _icon_outline(im, col=None):
    col = col or IPAL["o"]
    a = im[..., 3] > 0; o = im.copy()
    for y in range(16):
        for x in range(16):
            if not a[y, x] and any(0 <= y + dy < 16 and 0 <= x + dx < 16 and a[y + dy, x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[y, x] = col
    return o


def _ipoly(pts):
    m = Image.new("L", (16, 16), 0)
    ImageDraw.Draw(m).polygon([(x - 0.5, y - 0.5) for x, y in pts], fill=255)
    return np.array(m) > 0


def _iline(im, a, b, col, only=None):
    a, b = np.array(a, float), np.array(b, float); n = int(max(abs(b - a)) * 3) + 1
    for j in range(n + 1):
        q = a + (b - a) * j / n; x, y = int(math.floor(q[0])), int(math.floor(q[1]))
        if 0 <= x < 16 and 0 <= y < 16 and (only is None or only[y, x]):
            im[y, x] = col


E_RED, E_ORG, E_GLD, E_PAL = hx("#c8461a"), hx("#f48028"), hx("#ffd278"), hx("#fff8e6")


def icon_hatchling():
    im = np.zeros((16, 16, 4), np.uint8)
    # ember egg glow (lower centre)
    egg = np.zeros((16, 16), bool)
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - 7.4, y + 0.5 - 11.0
            ry = 4.7; rx = 4.3 * (1 - 0.12 * (-dy / ry))
            d = math.hypot(dx / rx, dy / ry)
            if d <= 1.0:
                egg[y, x] = True
                dc = math.hypot((dx + 1.0) / rx, (dy + 0.6) / ry)
                im[y, x] = E_PAL if dc < 0.28 else E_GLD if dc < 0.58 else E_ORG if d < 0.84 else E_RED
    SL = [hx("#16151c"), hx("#23222a"), hx("#35343d"), hx("#4f4d57")]
    MM = [hx("#2e1416"), hx("#44191a")]
    wing = _ipoly([(8.0, 8.4), (6.6, 4.6), (4.2, 0.8), (3.0, 3.4), (0.8, 4.2), (1.6, 6.8), (0.9, 9.0), (4.2, 8.6), (7.2, 9.6)])
    body = _ipoly([(8.6, 2.8), (10.6, 2.0), (12.6, 2.8), (15.3, 4.4), (12.8, 5.5), (10.9, 6.1), (10.4, 9.8), (7.8, 9.8), (8.4, 5.4)])
    for y in range(16):
        for x in range(16):
            if wing[y, x]:
                im[y, x] = MM[0]
    # wing trailing edge glows where it borders open space
    for y in range(16):
        for x in range(16):
            if wing[y, x] and any(0 <= x + dx < 16 and 0 <= y + dy < 16 and not wing[y + dy, x + dx] and not egg[y + dy, x + dx]
                                  and not body[y + dy, x + dx] for dx, dy in ((-1, 0), (0, 1))):
                im[y, x] = E_RED
    _iline(im, (7.8, 8.6), (6.6, 4.8), SL[3]); _iline(im, (6.6, 4.8), (4.4, 1.2), SL[3])
    _iline(im, (6.6, 4.8), (1.6, 4.4), MM[1], wing); _iline(im, (6.6, 4.8), (1.8, 8.2), MM[1], wing)
    for y in range(16):
        for x in range(16):
            if body[y, x]:
                top = any(0 <= x + dx < 16 and 0 <= y + dy < 16 and not body[y + dy, x + dx] for dx, dy in ((0, -1),))
                im[y, x] = SL[2] if (top and y < 6) else SL[0] if y > 5 else SL[1]
    _iline(im, (9.4, 2.6), (6.6, 0.5), SL[3])       # swept horn
    im[3, 11] = E_GLD; im[3, 12] = E_PAL            # glowing eye
    im[5, 13] = E_RED                               # throat ember
    return _icon_outline(im)


def icon_slag():
    im = np.zeros((16, 16, 4), np.uint8)
    I = [hx("#1e171f"), hx("#2a2226"), hx("#483a3a"), hx("#7a665c")]
    sole = np.zeros((16, 16), bool); U = np.zeros((16, 16)); V = np.zeros((16, 16))
    ang = math.radians(20)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - 8.0, y + 0.5 - 8.0
            lx = px * math.cos(ang) + py * math.sin(ang); ly = -px * math.sin(ang) + py * math.cos(ang)
            toe = (lx / 3.9) ** 2 + ((ly + 3.2) / 3.8) ** 2 <= 1
            heel = (lx / 3.2) ** 2 + ((ly - 4.2) / 2.7) ** 2 <= 1
            waist = -1.0 <= ly <= 3.0 and abs(lx + 0.3) <= 2.8
            if toe or heel or waist:
                sole[y, x] = True; U[y, x] = lx; V[y, x] = ly
    for y in range(16):
        for x in range(16):
            if sole[y, x]:
                lx = U[y, x]
                im[y, x] = I[3] if lx < -2.3 else I[2] if lx < -0.6 else I[1] if lx < 1.9 else I[0]
                if abs(V[y, x] - 0.9) < 0.6 or abs(V[y, x] + 4.6) < 0.55:      # iron straps
                    im[y, x] = I[3] if lx < 0.5 else I[2]
    def R(lx, ly):
        return (8.0 + lx * math.cos(ang) - ly * math.sin(ang), 8.0 + lx * math.sin(ang) + ly * math.cos(ang))
    crack = [(0.4, -5.6), (-0.6, -3.4), (0.7, -1.8), (-0.3, 0.0), (0.5, 2.4), (-0.5, 4.2), (0.3, 5.8)]
    for a_, b_ in zip(crack[:-1], crack[1:]):
        _iline(im, R(*a_), R(*b_), E_ORG, sole)
    _iline(im, R(0.7, -1.8), R(2.3, -3.0), E_RED, sole)
    _iline(im, R(0.5, 2.4), R(-1.7, 3.0), E_RED, sole)
    for q, c in (((-0.6, -3.4), E_GLD), ((0.5, 2.4), E_GLD), ((0.2, -1.0), E_PAL)):
        x, y = R(*q); im[int(y), int(x)] = c
    return _icon_outline(im)


def icon_crown():
    im = np.zeros((16, 16, 4), np.uint8)
    G = [hx("#6a4a26"), hx("#aa6e28"), hx("#f0c060"), hx("#fff8e6")]
    cx, cy = 8.0, 10.6
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if 2.3 <= d <= 4.5:
                lit = (-dx - dy) / max(d, 1e-6)          # light from top-left
                inner = d < 3.2
                c = G[3] if (lit > 0.55 and not inner) else G[2] if lit > -0.25 else G[1]
                if inner and lit < 0.3:
                    c = G[1] if lit > -0.5 else G[0]
                im[y, x] = c
    # crown of branches rising from the ring
    br = np.zeros((16, 16, 4), np.uint8)
    _iline(br, (8.0, 6.4), (8.0, 1.6), G[2])
    _iline(br, (6.2, 6.9), (4.0, 2.6), G[2]); _iline(br, (9.8, 6.9), (12.0, 2.6), G[2])
    _iline(br, (8.0, 4.2), (9.6, 3.0), G[1]); _iline(br, (5.1, 4.6), (3.4, 4.8), G[1]); _iline(br, (10.9, 4.6), (12.6, 4.8), G[1])
    a = br[..., 3] > 0
    im[a] = br[a]
    for (x, y) in ((8, 1), (4, 2), (11, 2)):
        im[y, x] = G[3]
    im = _icon_outline(im)
    # petal-white glow motes
    for (x, y) in ((14, 7), (1, 9), (2, 13)):
        im[y, x] = G[3]
    return im


def icon_img(rows):
    im = np.zeros((16, 16, 4), np.uint8)
    for y, row in enumerate(rows):
        assert len(row) == 16, (y, row)
        for x, ch in enumerate(row):
            c = IPAL[ch]
            if c:
                im[y, x] = c
    return im


# ------------------------------------------------------------------ build
def to_pil(a):
    return Image.fromarray(a)


def main():
    appear = tag_appear()
    fly, fly_pts = tag_fly()
    spit, spit_pts = tag_spit()
    dive = tag_dive()
    vanish = tag_vanish()
    fireball = tag_fireball()
    groups = [("appear", appear), ("fly", fly), ("spit", spit), ("dive", dive), ("vanish", vanish), ("fireball", fireball)]
    frames, tags, i0 = [], [], 0
    for name, fr in groups:
        tags.append((name, i0, i0 + len(fr) - 1)); i0 += len(fr)
        frames += fr
    # report points
    info = {"fly_mouth": [tuple(np.round(p["mouth"], 1)) for p in fly_pts],
            "spit_mouth": [tuple(np.round(p["mouth"], 1)) for p in spit_pts]}
    print("tags:", tags)
    print("fly mouth:", info["fly_mouth"])
    print("spit mouth:", info["spit_mouth"])

    icons = [("s_ember_hatchling", icon_hatchling()), ("c_x3_storm", icon_img(ICONS["c_x3_storm"])),
             ("c_x3_slag", icon_slag()), ("c_x3_crown", icon_crown()), ("egg", icon_img(ICONS["egg"]))]

    if not PREVIEW_ONLY:
        import asebuild
        asebuild.build("xrc_cub", W, H, ["cub"], [{"ms": ms, "cels": {"cub": to_pil(im)}} for im, ms in frames], tags)
        asebuild.build("xrc_icons", 16, 16, ["icon"], [{"ms": 100, "cels": {"icon": to_pil(im)}} for _, im in icons],
                       [(n, i, i) for i, (n, _) in enumerate(icons)])

    # ---- preview
    S4 = 4
    rows = [(n, fr) for n, fr in groups]
    maxn = max(len(fr) for _, fr in rows)
    cw, ch = W * S4 + 6, H * S4 + 6
    pw = 90 + maxn * cw
    ph = 10 + len(rows) * ch + ch + 10 + 16 * S4 * 2 + 30 + 90
    prev = Image.new("RGBA", (pw, ph), (18, 16, 22, 255))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(prev)
    y = 10
    for name, fr in rows:
        dr.text((6, y + ch // 2 - 6), name, fill=(200, 190, 180, 255))
        for j, (im, ms) in enumerate(fr):
            bg = Image.new("RGBA", (W * S4, H * S4), (28, 26, 34, 255))
            bg.alpha_composite(to_pil(im).resize((W * S4, H * S4), Image.NEAREST))
            # centre mark
            prev.paste(bg, (90 + j * cw, y))
        y += ch
    # sunset row: fly frames + spit + a dive frame
    dr.text((6, y + ch // 2 - 6), "sunset bg", fill=(200, 190, 180, 255))
    sun = [im for im, _ in fly] + [spit[2][0], dive[5][0]]
    for j, im in enumerate(sun[:maxn]):
        bg = Image.new("RGBA", (W * S4, H * S4), (226, 128, 60, 255))
        g = ImageDraw.Draw(bg)
        for yy in range(H * S4):
            t = yy / (H * S4)
            g.line([(0, yy), (W * S4, yy)], fill=(int(240 - 60 * t), int(150 - 70 * t), int(70 - 20 * t), 255))
        bg.alpha_composite(to_pil(im).resize((W * S4, H * S4), Image.NEAREST))
        prev.paste(bg, (90 + j * cw, y))
    y += ch + 10
    dr.text((6, y + 20), "icons", fill=(200, 190, 180, 255))
    for j, (n, im) in enumerate(icons):
        bg = Image.new("RGBA", (16 * S4 * 2, 16 * S4 * 2), (28, 26, 34, 255))
        bg.alpha_composite(to_pil(im).resize((16 * S4 * 2, 16 * S4 * 2), Image.NEAREST))
        prev.paste(bg, (90 + j * (16 * S4 * 2 + 10), y))
    # existing icons for comparison
    try:
        ref = Image.open(os.path.join(ASSETS, "ui_icons3.png")).convert("RGBA")
        for j, k in enumerate((44, 47, 48, 34)):
            c = ref.crop((k * 16, 0, k * 16 + 16, 16)).resize((16 * S4 * 2, 16 * S4 * 2), Image.NEAREST)
            bg = Image.new("RGBA", c.size, (28, 26, 34, 255)); bg.alpha_composite(c)
            prev.paste(bg, (90 + (5 + j) * (16 * S4 * 2 + 10) + 20, y))
    except Exception:
        pass
    y += 16 * S4 * 2 + 20
    # game scale 2x: cub next to the player
    dr.text((6, y + 30), "2x scale", fill=(200, 190, 180, 255))
    strip = Image.new("RGBA", (400, 44), (28, 26, 34, 255))
    try:
        pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
        strip.alpha_composite(pl, (0, 4))
    except Exception:
        pass
    for j, (im, _) in enumerate(fly[:3] + [spit[2]] + [dive[5]]):
        strip.alpha_composite(to_pil(im), (60 + j * 42, 4))
    prev.paste(strip.resize((800, 88), Image.NEAREST), (90, y))
    os.makedirs(PREV, exist_ok=True)
    prev.save(os.path.join(PREV, "xrc_cub_preview.png"))
    print("preview ->", os.path.join(PREV, "xrc_cub_preview.png"))


if __name__ == "__main__":
    main()
