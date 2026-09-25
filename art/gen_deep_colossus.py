#!/usr/bin/env python3
"""The Molten Colossus (agent D) -- main boss of the Burning Deep, built from the APPROVED concept
art/concepts/colossus.png (drawing code reused via art/deep_colossus.py: sculpted height-field anatomy, obsidian
shell, molten veins, horned iron crown, anvil-hammer, scorched loincloth, chains, Ashwright's seals).

    python3 art/gen_deep_colossus.py [--preview] [--only colossus,colossus_b,...] [--frames tag:i,j]

Frames 256x176, faces RIGHT, feet on row 175, anchor [107, 176].  ~165 px tall (the Pale Sovereign is ~130).
Phase 1 sheets (armoured: iron knee plates, a vambrace, a breastplate -- drawn on separate PLATE sheets so the engine
can drop each plate when it breaks; the body underneath shows the glowing weak point):
  colossus      idle(6) walk(8) slam(14) fist(12) stomp(10) stagger(4)      + colossus_pl   (plates only)
  colossus_b    sweep(12) breath(16) rain(10) grab(16)                      + colossus_b_pl
  colossus_c    topple(8: legs buckle, crash forward f3, held) rise(8: heave up, stamp f4)   + colossus_c_pl
Phase 2 sheets (the shell has sloughed off, the magma body shows; no plates):
  colossus_p2   idle walk slam fist stomp stagger      colossus_p2b  sweep breath rain grab      colossus_p2c  shed(12) death(14)   colossus_p2d  topple rise
Meta: assets/colossus_meta.json -- per tag, per frame: part rects (knee_n, knee_f, arm, chest), points (mouth + breath
angle, heart, hammer face, near/far hand, feet); attack windows; telegraph frames; sheet map.
"""
import json, math, os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
import asebuild  # noqa: E402
import deep_colossus as C  # noqa: E402

BUILD = "--preview" not in sys.argv
W, H, GROUND = C.W, C.H, C.GROUND
ANCHOR = [107, 176]
PREV = os.path.join(HERE, "previews")
ASSETS = asebuild.ASSETS
DEG = math.pi / 180


# =========================================================================== keypose model
# q: lean, off, hd (torso-space head), hang, roar, wN/wF wrists, eN/eF elbows (None -> ik), fN/fF fist dirs, openN,
#    aN/aF ankles, kN/kF knees (None -> ik), hammer: hc (face centre) + ha (angle face->haft) or grip/gd, hlen, hlay,
#    heat: glow under face rune fis horn, chains: chN/chF (free-end offsets), cloth sway
IDLE = dict(lean=0.13, off=(-3.0, 2.0), hd=(137.0, 57.0), hang=0.0, roar=0.0,
            wN=(42.0, 122.0), eN=(46.0, 94.0), fN=(-0.12, 1.0), openN=True,
            wF=(180.0, 102.0), eF=(170.0, 86.0), fF=(0.05, 1.0),
            aN=(62.0, 163.0), kN=(70.0, 140.0), aF=(152.0, 163.0), kF=(144.0, 138.0),
            hc=(182.0, 175.0), ha=math.atan2(-1, -0.06), hlen=66.0, hlay="mid", snap=True, grip=None, gd=40.0,
            glow=1.0, under=0.35, face=0.8, rune=0.6, fis=0.0, horn=0.8, chN=(-7.0, 25.0), chF=(0.0, 22.0), cloth=0.0,
            embers=1.0, fx=None)


def Q(**kw):
    q = dict(IDLE)
    q.update(kw)
    return q


def T_of(q):
    return C.make_T(q["lean"], q["off"])


def unit(v):
    l = math.hypot(*v) or 1
    return (v[0] / l, v[1] / l)


OUTL = [(0, -19), (0, 13), (1.2, 19), (2.6, 24), (4.5, 29), (6.5, 25), (9.5, 19), (12, 13), (13, 9), (15.5, 7.5),
        (18, 10.5), (19, 13.5), (26, 13.5), (26, -17.5), (19, -17.5), (18, -14.5), (15.5, -11.5), (13, -13),
        (12, -19), (10, -21.5), (3, -21.5)]
HK = 1.25


def ham_pts(hc, ang):
    u = (math.cos(ang), math.sin(ang)); v = (-u[1], u[0])
    return [(hc[0] + u[0] * a * HK + v[0] * b * HK, hc[1] + u[1] * a * HK + v[1] * b * HK) for a, b in OUTL]


def resolve(q):
    """Fill elbows / knees by IK, the hammer face centre from a grip, and snap a grounded hammer."""
    q = dict(q)
    T = T_of(q)
    Sn, Sf = T((64, 60)), T((151, 61))
    if q["eN"] is None:
        q["eN"] = C.ik(Sn, q["wN"], 33, 30, q.get("pN", (-1, -0.2)))
    if q["eF"] is None:
        q["eF"] = C.ik(Sf, q["wF"], 33, 30, q.get("pF", (1, -0.6)))
    hn, hf = T((90, 112)), T((120, 110))
    if q["kN"] is None:
        q["kN"] = C.ik(hn, q["aN"], 32, 25, q.get("pkN", (-1, -0.8)))
    if q["kF"] is None:
        q["kF"] = C.ik(hf, q["aF"], 32, 25, q.get("pkF", (1, -0.8)))
    if q.get("grip") is not None:
        u = (math.cos(q["ha"]), math.sin(q["ha"]))
        q["hc"] = (q["grip"][0] - u[0] * (26 * HK + q["gd"]), q["grip"][1] - u[1] * (26 * HK + q["gd"]))
    if q["snap"]:
        my = max(p[1] for p in ham_pts(q["hc"], q["ha"]))
        q["hc"] = (q["hc"][0], q["hc"][1] + GROUND - my)
    return q


def lerp(a, b, t):
    if isinstance(a, tuple) and isinstance(b, tuple):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    return a if t < 0.5 else b


def tween(qa, qb, t, ease=True):
    if ease:
        t = t * t * (3 - 2 * t)
    ra, rb = resolve(qa), resolve(qb)
    out = {}
    for k in ra:
        if k == "ha":
            d = (rb[k] - ra[k] + math.pi) % (2 * math.pi) - math.pi
            out[k] = ra[k] + d * t
        elif k in ("grip", "snap"):
            out[k] = None if k == "grip" else False
        else:
            out[k] = lerp(ra[k], rb.get(k, ra[k]), t)
    return out


def to_pose(q, p2=False, shell=None):
    q = resolve(q)
    T = T_of(q)
    p = dict(name="X", lean=q["lean"], T=T, glow=q["glow"] * (1.15 if p2 else 1.0), under=q["under"] + (0.1 if p2 else 0))
    p["Hd"] = T(q["hd"]); p["head_ang"] = q["hang"]; p["roar"] = q["roar"]
    Sn, Sf = T((64, 60)), T((151, 61))
    p["arms"] = dict(near=(Sn, q["eN"], q["wN"]), far=(Sf, q["eF"], q["wF"]))
    p["fist_near"] = q["fN"]; p["fist_far"] = q["fF"]; p["open_near"] = q["openN"]
    p["legs"] = dict(near=(T((90, 112)), q["kN"], q["aN"]), far=(T((120, 110)), q["kF"], q["aF"]))
    if q["hc"] is not None:
        p["ham_c"] = q["hc"]; p["ham_ang"] = q["ha"]; p["ham_len"] = q["hlen"]
        p["ham_back"] = q["hlay"] == "back"; p["ham_front"] = q["hlay"] == "front"
        p["ham_before_torso"] = q["hlay"] == "mid0"
    p["face_heat"] = q["face"]; p["rune_heat"] = q["rune"]; p["fissure"] = q["fis"]; p["horn_heat"] = q["horn"]
    p["cloth_sw"] = q["cloth"]
    p["delt_shards_near"] = [((-3, -7), (-15, -24), 4.2), ((3, -10), (0, -25), 3.4), ((-10, -1), (-25, -9), 3.4)]
    p["delt_shards_far"] = [((2, -9), (8, -22), 3.2)]
    if p2:
        p.update(shell=0.35 if shell is None else shell, p2=True, face_heat=1.0, rune_heat=0.95)
    elif shell is not None:
        p["shell"] = shell
    return q, p


# =========================================================================== rendering (C.frame + weak cores + plates)
def group_idx(fb, name):
    for i, g in enumerate(fb.groups):
        if g.name == name:
            return i
    return -1


def core_patch(fb, gi, c, rx, ry, ang, hot=1.0):
    """A molten weak point burnt into the body: white-hot centre, banded heat, floating crust flecks."""
    cs, sn = math.cos(ang), math.sin(ang)
    for y in range(int(c[1] - max(rx, ry) - 1), int(c[1] + max(rx, ry) + 2)):
        for x in range(int(c[0] - max(rx, ry) - 1), int(c[0] + max(rx, ry) + 2)):
            if not (0 <= x < W and 0 <= y < H) or fb.gid[y, x] != gi:
                continue
            dx, dy = x + .5 - c[0], y + .5 - c[1]
            u, v = dx * cs + dy * sn, -dx * sn + dy * cs
            e = (u / rx) ** 2 + (v / ry) ** 2 + 0.12 * math.sin(x * 1.3 + y * 0.7)
            if e < 1:
                d = math.sqrt(max(0, e))
                fb.mat[y, x] = C.MI["M"]
                fb.heat[y, x] = hot * (1.0 if d < 0.3 else 0.84 if d < 0.55 else 0.66 if d < 0.8 else 0.48)
                if 0.35 < d < 0.8 and C.hsh(x, y, 5) < 0.12:
                    fb.heat[y, x] = 0.22
                fb.fix[y, x] = ""
            elif e < 1.5:
                fb.fix[y, x] = "H4" if e < 1.2 else "H2"


KNEE_POLY = [(-9, -9), (0, -12.5), (9, -9), (10.5, 3), (7, 11), (0, 14), (-7, 11), (-10.5, 3)]
CHEST_POLY = [(-14, -11), (0, -14), (14, -12), (15, 0), (9, 12), (0, 17), (-9, 12), (-15, 0)]
MARK = C.MARK


def xform(pts, c, ang):
    cs, sn = math.cos(ang), math.sin(ang)
    return [(c[0] + x * cs - y * sn, c[1] + x * sn + y * cs) for x, y in pts]


def arm_poly(E, Wr):
    u = unit((Wr[0] - E[0], Wr[1] - E[1])); v = (-u[1], u[0])
    a, b = C.lerp(E, Wr, 0.18), C.lerp(E, Wr, 0.86)
    w0, w1 = 11.0, 9.0
    return [(a[0] + v[0] * w0, a[1] + v[1] * w0), (b[0] + v[0] * w1, b[1] + v[1] * w1), (b[0] + u[0] * 2, b[1] + u[1] * 2),
            (b[0] - v[0] * w1, b[1] - v[1] * w1), (a[0] - v[0] * w0, a[1] - v[1] * w0), (a[0] - u[0] * 3, a[1] - u[1] * 3)]


def part_geometry(q, info):
    T = T_of(q)
    hn, hf = T((90, 112)), T((120, 110))
    kn, an, kf, af = q["kN"], q["aN"], q["kF"], q["aF"]
    sang = lambda k, a: math.atan2(a[1] - k[1], a[0] - k[0]) - math.pi / 2
    geo = {
        "knee_n": xform(KNEE_POLY, (kn[0] + (an[0] - kn[0]) * 0.12, kn[1] + (an[1] - kn[1]) * 0.12), sang(kn, an)),
        "knee_f": xform(KNEE_POLY, (kf[0] + (af[0] - kf[0]) * 0.12, kf[1] + (af[1] - kf[1]) * 0.12), sang(kf, af)),
        "arm": arm_poly(q["eN"], q["wN"]),
        "chest": xform(CHEST_POLY, info["heart"], q["lean"]),
    }
    return geo


RGB = C.RGB


def render_plates(fb, geo, gids, heat_under=0.5):
    """Iron armour plates (gold rim, rivets, seal on the breastplate) -- only where their limb is the frontmost part."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for name, poly in geo.items():
        gi = gids[name]
        m = C.mask_poly(poly) & (fb.gid == gi)
        if m.sum() < 8:
            continue
        d = C.dist_in(m, 4)
        ys, xs = np.nonzero(m)
        cx, cy = xs.mean(), ys.mean()
        rx, ry = max(1, xs.max() - xs.min()) / 2, max(1, ys.max() - ys.min()) / 2
        for y, x in zip(ys, xs):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            lit = -0.45 * nx - 0.65 * ny + 0.5 * (1 - min(1, nx * nx + ny * ny))
            if d[y, x] <= 1:
                k = "OUT" if (nx > 0.2 or ny > 0.3) else "I4"
            elif d[y, x] <= 2:
                k = "G4" if lit > 0.35 else "G3" if lit > -0.1 else "G2"
            else:
                k = "I%d" % int(max(1, min(5, round(2.2 + lit * 2.6))))
                if ny > 0.55 and d[y, x] <= 3.5:
                    k = "M2" if C.hsh(x, y, 3) < heat_under else "H3"      # the core's heat leaking under the rim
            px[int(x), int(y)] = RGB[k] + (255,)
        # rivets
        for (fx_, fy_) in ((-0.6, -0.45), (0.6, -0.45), (-0.55, 0.45), (0.55, 0.45)):
            x, y = int(cx + fx_ * rx * 0.8), int(cy + fy_ * ry * 0.8)
            if 0 <= x < W and 0 <= y < H and m[y, x] and d[y, x] > 2:
                px[x, y] = RGB["I5"] + (255,)
                if y + 1 < H and m[y + 1, x]:
                    px[x, y + 1] = RGB["I0"] + (255,)
        if name == "chest":
            KEY = {"G": "G3", "H": "G4", "g": "G2", "k": "I0", "m": "M6"}
            for j, row in enumerate(MARK):
                for i, ch in enumerate(row):
                    x, y = int(cx) - 3 + i, int(cy) - 3 + j
                    if ch != "." and 0 <= x < W and 0 <= y < H and m[y, x]:
                        px[x, y] = RGB[KEY[ch]] + (255,)
    return img


def render(q, p2=False, shell=None, plates=True, fire=None, dissolve=0.0, cool=0.0):
    q, p = to_pose(q, p2, shell)
    fb, info = C.build(p)
    gids = {"knee_n": group_idx(fb, "legN"), "knee_f": group_idx(fb, "legF"), "arm": group_idx(fb, "armN"), "chest": group_idx(fb, "torso")}
    geo = part_geometry(q, info)
    # weak points burnt into the body (hidden under the plates in phase 1)
    T = T_of(q)
    core_patch(fb, gids["knee_n"], C.lerp(q["kN"], q["aN"], 0.1), 7.5, 6.0, math.atan2(q["aN"][1] - q["kN"][1], q["aN"][0] - q["kN"][0]))
    core_patch(fb, gids["knee_f"], C.lerp(q["kF"], q["aF"], 0.1), 7.0, 5.5, math.atan2(q["aF"][1] - q["kF"][1], q["aF"][0] - q["kF"][0]))
    core_patch(fb, gids["arm"], C.lerp(q["eN"], q["wN"], 0.52), 10.0, 5.2, math.atan2(q["wN"][1] - q["eN"][1], q["wN"][0] - q["eN"][0]))
    vis = fb.gid == gids["chest"]
    C._open_heart(fb, vis, info["heart"], max(0.72, q["fis"]), T)
    if cool > 0:   # death: the magma crusts over
        m = fb.mat == C.MI["M"]
        fb.heat[m] = fb.heat[m] * (1 - cool)
    out, fig, warm = C.shade(fb, glow=p.get("glow", 1.0) * (1 - 0.6 * cool), under=p.get("under", 0.35) * (1 - cool))
    img = C.to_image(out, fig)
    ov = C.Overlay()
    C.trickles(ov, fb, fig, 7 if p2 else 3, 11, minheat=0.6, ymin=50)
    fr = C.Fire()
    for key, (sag, dn) in (("armN", (4, q["chN"])), ("armF", (3, q["chF"]))):
        g = info[key]
        cu, pf = g.cuff
        a = C.add(cu, C.mul(pf, -6 if key == "armN" else 7))
        C.chain(ov, a, C.add(a, dn), sag=sag, seed=1)
    C.chain(ov, T((84, 108.5)), T((126, 107)), sag=3.5, seed=2, broken=False, hot_end=False, sc=1.25)
    C.lock_plate(ov, T((106, 110.5)))
    if q["embers"] > 0 and cool < 0.5:
        C.embers(ov, (56, 14, 170, 50), int(22 * q["embers"] * (1.6 if p2 else 1)), 4 + int(q["lean"] * 100) % 7)
    C.ash(ov, (46, 6, 184, 50), 14, 5)
    fn = info["armN"].fist
    if cool < 0.5:
        C.drip(ov, fn[0] + 2, fn[1] + 7, 4, seed=1)
    if p2 and cool < 0.5:
        hd = p["Hd"]
        rnd = random.Random(7 + int(q["hang"] * 50))
        for i in range(5):
            dx = -13 + i * 6.8 + rnd.uniform(-0.8, 0.8)
            hh = (12 + 16 * math.sin(math.pi * (i + 0.5) / 5) + rnd.uniform(-2, 2)) * (1 - cool)
            fr.tongue(C.rot(C.add(hd, (dx, -14 - (dx + 14) * 0.1)), hd, q["hang"]), hh, 6.6 + rnd.uniform(0, 1.0), seed=i * 5 + 1 + int(q["hang"] * 9), lean=-0.32)
        C.drip(ov, 112, 84, 6, seed=3)
        C.embers(ov, (40, 30, 200, 120), 26, 13, hot=1.5)
    if fire:
        fr.cone(*fire)
    fr.to(ov)
    img = C.compose(img, ov, fig)
    plate_img = render_plates(fb, geo, gids) if plates else None
    if dissolve > 0:
        img = dissolve_img(img, dissolve)
    # meta for this frame
    rects = {}
    for name, poly in geo.items():
        xs = [x for x, _ in poly]; ys = [y for _, y in poly]
        rects[name] = [int(min(xs)), int(min(ys)), int(max(xs) - min(xs) + 1), int(max(ys) - min(ys) + 1)]
    hd = p["Hd"]
    mouth = C.rot(C.add(hd, (9, 12)), hd, q["hang"])
    u = (math.cos(q["ha"]), math.sin(q["ha"]))
    hface = q["hc"]
    hbottom = max(pp[1] for pp in ham_pts(q["hc"], q["ha"]))
    hxs = [pp[0] for pp in ham_pts(q["hc"], q["ha"])]
    fd = {"parts": rects, "mouth": [round(mouth[0], 1), round(mouth[1], 1)], "breath": round(q["hang"] * 1.0 + 0.28, 3),
          "heart": [round(info["heart"][0], 1), round(info["heart"][1], 1)], "hammer": [round(hface[0], 1), round(hface[1], 1)],
          "hbox": [int(min(hxs)), int(hbottom - 36), int(max(hxs) - min(hxs)), 36], "hand": [round(fn[0], 1), round(fn[1], 1)],
          "handF": [round(info["armF"].fist[0], 1), round(info["armF"].fist[1], 1)],
          "feet": [[round(q["aN"][0], 1), GROUND], [round(q["aF"][0], 1), GROUND]]}
    return img, plate_img, fd


def dissolve_img(img, frac):
    """Death: the cooled husk crumbles to slag and ash from the top down, motes drifting up."""
    a = np.array(img)
    out = a.copy()
    h, w = a.shape[:2]
    rnd = np.random.RandomState(4)
    noise = rnd.rand(h, w)
    for y in range(h):
        t = 0.55 * (y / h) + 0.45 * noise[y]
        kill = (1 - t) < frac
        row = out[y]
        edge = kill & ((1 - t) > frac - 0.06)
        row[kill & ~edge] = 0
        row[edge & (a[y, :, 3] > 0)] = list(RGB["M3"]) + [255]
    motes = rnd.rand(h, w) < 0.004 * frac
    ys, xs = np.nonzero(motes & (a[:, :, 3] > 0))
    for y, x in zip(ys, xs):
        yy = max(0, int(y - frac * 40))
        out[yy, x] = list(RGB["M5" if rnd.rand() < 0.5 else "M3"]) + [255]
    return Image.fromarray(out)


# =========================================================================== animations
LIFT = lambda a, dy: (a[0], a[1] - dy)


def seq(keys):
    """keys: [(ms, q) ...] -> frames; ('tw', ms, qa, qb, t) entries are tweens."""
    out = []
    for k in keys:
        if k[0] == "tw":
            _, ms, qa, qb, t = k
            out.append((ms, tween(qa, qb, t)))
        else:
            out.append(k)
    return out


def a_idle():
    fr = []
    for i in range(6):
        b = 0.5 - 0.5 * math.cos(i * math.pi / 3)
        fr.append((200, Q(off=(-3.0, 2.0 + b * 1.2), hd=(137.0, 57.0 + b * 0.4), wN=(42.0, 122.0 + b * 1.4), eN=(46.0, 94.0 + b),
                          face=0.7 + 0.25 * b, rune=0.5 + 0.2 * b, glow=0.95 + 0.1 * b, chN=(-7.0 + b * 2, 25.0), cloth=b)))
    return fr


CARRY = dict(hc=None, grip=(188.0, 112.0), ha=math.atan2(-1, 0.18), gd=6.0, hlen=46.0, snap=False, wF=(188.0, 112.0), eF=(174.0, 90.0),
             fF=(0.3, 1.0))


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        bob = abs(s) * 2.0
        aN = (66.0 + 14 * c, 163.0)
        aF = (148.0 - 14 * c, 163.0)
        kN = (74.0 + 10 * c, 140.0 - max(0, s) * 8 + bob)
        kF = (140.0 - 10 * c, 138.0 - max(0, -s) * 8 + bob)
        q = Q(**CARRY, off=(-3.0, 2.0 + bob), aN=aN, kN=kN, aF=aF, kF=kF, lean=0.15 + 0.02 * s,
              wN=(46.0 - 8 * c, 120.0 + bob), eN=(48.0 - 4 * c, 93.0 + bob), cloth=2 * c, chN=(-7.0 - 4 * c, 24.0))
        q["grip"] = (188.0 + 3 * c, 112.0 + bob); q["wF"] = q["grip"]
        fr.append((150, q))
    return fr


WINDUP = Q(lean=-0.05, off=(0.0, 15.0), hang=0.14, wN=(100.0, 51.0), eN=None, wF=(108.0, 42.0), eF=None, fN=(0.99, -0.16), fF=(0.99, -0.16),
           openN=False, aN=(52.0, 163.0), kN=None, aF=(162.0, 163.0), kF=None, hc=None, grip=(106.0, 46.0), ha=math.atan2(0.99, 0.16), gd=7.0,
           hlen=44.0, hlay="back", snap=False, face=0.95, rune=0.85, glow=1.2, chN=(-10.0, 20.0), chF=(6.0, 18.0))
GRAB2 = Q(**{**CARRY, "wN": (150.0, 118.0), "eN": None, "openN": False, "fN": (0.4, 0.9), "lean": 0.22, "off": (0.0, 6.0), "aN": (56.0, 163.0),
             "kN": None, "aF": (160.0, 163.0), "kF": None})
GRAB2["grip"] = (160.0, 120.0); GRAB2["wF"] = (164.0, 116.0); GRAB2["wN"] = (150.0, 124.0); GRAB2["ha"] = math.atan2(-1, -0.4)
MID = Q(lean=-0.12, off=(0.0, 8.0), hang=0.05, wN=(118.0, 30.0), eN=None, wF=(126.0, 24.0), eF=None, fN=(0.8, -0.6), fF=(0.8, -0.6), openN=False,
        aN=(54.0, 163.0), kN=None, aF=(160.0, 163.0), kF=None, hc=None, grip=(124.0, 28.0), ha=math.atan2(0.95, -0.3), gd=7.0, hlen=44.0,
        hlay="back", snap=False, face=0.9, rune=0.8)
IMPACT = Q(lean=0.42, off=(14.0, 14.0), hang=0.32, wN=(172.0, 118.0), eN=None, wF=(180.0, 112.0), eF=None, fN=(0.7, 0.7), fF=(0.7, 0.7),
           openN=False, aN=(60.0, 163.0), kN=None, aF=(168.0, 163.0), kF=None, hc=None, grip=(176.0, 114.0),
           ha=math.atan2(-0.8, -0.6), gd=8.0, hlen=44.0, hlay="front", snap=True, face=1.0, rune=1.0, glow=1.25, chN=(10.0, 22.0), chF=(12.0, 18.0))


def a_slam():
    # hammer face centre after the snap -> hands follow the haft
    imp = resolve(IMPACT)
    u = (math.cos(imp["ha"]), math.sin(imp["ha"]))
    grip = (imp["hc"][0] + u[0] * (26 * HK + 8), imp["hc"][1] + u[1] * (26 * HK + 8))
    IMP = dict(IMPACT, grip=None, snap=False, hc=imp["hc"], wF=grip, wN=(grip[0] - u[0] * 7, grip[1] - u[1] * 7))
    SWING = tween(MID, IMP, 0.55, ease=False)
    SWING.update(hlay="front")
    RISE = dict(IMP, lean=0.3, off=(10.0, 10.0), hang=0.2)
    return seq([
        (150, Q(**CARRY)),
        ("tw", 150, Q(**CARRY), GRAB2, 1.0),
        ("tw", 140, GRAB2, MID, 0.45),
        (150, MID),
        ("tw", 160, MID, WINDUP, 0.6),
        (260, WINDUP),
        (320, dict(WINDUP, face=1.0, rune=1.0, glow=1.35)),          # held: telegraph
        (70, SWING),
        (90, IMP),
        (220, dict(IMP, glow=1.3)),
        (260, IMP),
        (200, RISE),
        ("tw", 170, RISE, Q(**CARRY), 0.5),
        (170, Q(**CARRY)),
    ])


FIST_UP = Q(lean=-0.1, off=(-6.0, 6.0), hang=-0.12, wN=(30.0, 20.0), eN=(34.0, 52.0), openN=True, fN=(0.2, -1.0), **{k: v for k, v in CARRY.items()},
            aN=(56.0, 163.0), kN=None, aF=(156.0, 163.0), kF=None, face=0.95, glow=1.15, chN=(-14.0, 10.0))
FIST_HIT = Q(lean=0.62, off=(12.0, 30.0), hang=0.42, wN=(146.0, 146.0), eN=None, pN=(-0.4, -1), openN=True, fN=(0.3, 1.0),
             **{k: v for k, v in CARRY.items()}, aN=(58.0, 163.0), kN=None, aF=(190.0, 163.0), kF=None, face=1.0, rune=1.0, glow=1.25,
             chN=(10.0, 16.0))
FIST_HIT["grip"] = (196.0, 124.0); FIST_HIT["wF"] = (196.0, 124.0)


def a_fist():
    return seq([
        (130, Q(**CARRY)),
        ("tw", 140, Q(**CARRY), FIST_UP, 0.5),
        (170, FIST_UP),
        (380, dict(FIST_UP, face=1.0, glow=1.25)),                  # telegraph
        (70, tween(FIST_UP, FIST_HIT, 0.5, ease=False)),
        (90, FIST_HIT),                                               # impact
        (220, FIST_HIT),
        (260, dict(FIST_HIT, glow=1.1)),
        (240, dict(FIST_HIT, glow=1.0)),
        ("tw", 180, FIST_HIT, Q(**CARRY), 0.4),
        ("tw", 160, FIST_HIT, Q(**CARRY), 0.8),
        (170, Q(**CARRY)),
    ])


def a_stomp():
    up = Q(**CARRY, lean=0.02, off=(-2.0, 0.0), aN=(78.0, 132.0), kN=(88.0, 108.0), hang=-0.08, wN=(30.0, 104.0), eN=(40.0, 84.0))
    down = Q(**CARRY, lean=0.2, off=(-2.0, 8.0), aN=(76.0, 163.0), kN=None, aF=(160.0, 163.0), kF=None, hang=0.2, face=1.0, glow=1.2)
    return seq([
        (130, Q(**CARRY)),
        ("tw", 150, Q(**CARRY), up, 0.5),
        (160, up),
        (240, dict(up, face=1.0)),
        (220, dict(up, aN=(78.0, 128.0), kN=(88.0, 104.0))),
        (60, tween(up, down, 0.6, ease=False)),
        (100, down),
        (240, down),
        ("tw", 180, down, Q(**CARRY), 0.5),
        (170, Q(**CARRY)),
    ])


KNEEL = Q(lean=0.36, off=(4.0, 34.0), hang=0.3, aN=(40.0, 163.0), kN=(78.0, 170.0), aF=(160.0, 163.0), kF=None,
          wN=(44.0, 150.0), eN=None, pN=(-1, 0.3), openN=True, fN=(0.0, 1.0), **{k: v for k, v in CARRY.items() if k not in ("grip", "wF", "eF")},
          face=0.5, rune=0.4, glow=0.9, chN=(-4.0, 10.0))
KNEEL["grip"] = (190.0, 136.0); KNEEL["wF"] = (190.0, 136.0); KNEEL["eF"] = None; KNEEL["ha"] = math.atan2(-1, 0.1)


def a_stagger():
    return [(120, tween(Q(**CARRY), KNEEL, 0.55)), (200, KNEEL), (500, dict(KNEEL, face=0.35, glow=0.85)), (400, KNEEL)]


def a_sweep():
    back = Q(lean=-0.12, off=(-8.0, 12.0), hang=-0.05, hc=(18.0, 170.0), ha=math.atan2(-0.35, 0.94), hlen=44.0, snap=True, grip=None,
             wF=(64.0, 142.0), eF=None, pF=(-1, -0.5), wN=(56.0, 150.0), eN=None, openN=False, fN=(0.9, 0.3), fF=(0.9, 0.3),
             aN=(52.0, 163.0), kN=None, aF=(160.0, 163.0), kF=None, hlay="mid", face=0.95, glow=1.15)
    fwd = Q(lean=0.3, off=(10.0, 18.0), hang=0.22, hc=(236.0, 170.0), ha=math.atan2(-0.45, -0.89), hlen=44.0, snap=True, grip=None,
            wF=(182.0, 146.0), eF=None, wN=(172.0, 150.0), eN=None, openN=False, fN=(0.9, 0.2), fF=(0.9, 0.2),
            aN=(62.0, 163.0), kN=None, aF=(176.0, 163.0), kF=None, hlay="front", face=1.0, glow=1.25)

    def at(t):
        q = tween(back, fwd, t, ease=False)
        # hands ride the haft
        u = (math.cos(q["ha"]), math.sin(q["ha"]))
        g = (q["hc"][0] + u[0] * (26 * HK + 8), q["hc"][1] + u[1] * (26 * HK + 8))
        q["wF"] = g; q["wN"] = (g[0] - u[0] * 7, g[1] - u[1] * 7); q["eF"] = None; q["eN"] = None
        q["hlay"] = "front" if t > 0.45 else "mid"
        return q
    follow = Q(lean=0.1, off=(4.0, 6.0), hang=0.05, hc=None, grip=(206.0, 70.0), ha=math.atan2(0.9, -0.44), gd=6.0, hlen=44.0,
               wF=(206.0, 70.0), eF=None, wN=(196.0, 78.0), eN=None, openN=False, hlay="front", aN=(62.0, 163.0), kN=None, aF=(170.0, 163.0), kF=None)
    return seq([
        (140, Q(**CARRY)),
        ("tw", 150, Q(**CARRY), at(0.0), 0.5),
        (160, at(0.0)),
        (400, dict(at(0.0), face=1.0, glow=1.3)),      # telegraph: hammer dragged back, face white-hot
        (80, at(0.2)),
        (70, at(0.45)),
        (70, at(0.7)),
        (80, at(1.0)),
        (140, tween(at(1.0), follow, 0.5)),
        (200, follow),
        ("tw", 180, follow, Q(**CARRY), 0.5),
        (170, Q(**CARRY)),
    ])


def a_breath():
    rear = Q(lean=-0.18, off=(-4.0, 2.0), hang=-0.34, roar=0.3, fis=0.6, wN=(26.0, 104.0), eN=None, pN=(-1, 0.2), wF=(196.0, 96.0), eF=None,
             hc=(196.0, 175.0), ha=math.atan2(-1, 0.14), hlen=60.0, snap=True, grip=None, face=1.0, glow=1.3, under=0.5)
    blow = lambda a: Q(lean=0.1 + a * 0.3, off=(0.0, 4.0 + a * 6), hang=-0.1 + a * 0.45, roar=0.8, fis=1.0, wN=(24.0, 104.0), eN=None,
                       pN=(-1, 0.2), wF=(184.0, 104.0), eF=None, hc=(182.0, 175.0), ha=math.atan2(-1, 0.14), hlen=60.0, snap=True, grip=None,
                       face=1.0, glow=1.35, under=0.5)
    fr = [(130, Q()), ("tw", 150, Q(), rear, 0.4), (170, rear), (260, dict(rear, roar=0.45, fis=0.8)), (240, dict(rear, roar=0.6, fis=1.0))]
    for k in range(8):
        fr.append((110, blow(k / 7)))
    fr += [(160, dict(blow(1.0), roar=0.3, fis=0.6)), ("tw", 170, blow(1.0), Q(), 0.6), (170, Q())]
    return seq(fr)


def a_rain():
    rear = Q(lean=-0.26, off=(-6.0, 4.0), hang=-0.5, roar=0.9, fis=0.5, wN=(20.0, 70.0), eN=None, pN=(-1, 0.4), wF=(206.0, 72.0), eF=None,
             pF=(1, 0.3), fF=(0.6, -0.8), hc=None, grip=(206.0, 72.0), ha=math.atan2(0.2, 0.98), gd=6.0, hlen=46.0, face=1.0, glow=1.35, under=0.5)
    return seq([(130, Q(**CARRY)), ("tw", 150, Q(**CARRY), rear, 0.4), (170, dict(rear, roar=0.4)), (250, dict(rear, roar=0.6)),
                (140, rear), (200, dict(rear, roar=1.0)), (220, rear), (200, dict(rear, roar=0.6)), ("tw", 170, rear, Q(**CARRY), 0.6),
                (170, Q(**CARRY))])


def a_grab():
    reach = Q(**CARRY, lean=-0.1, off=(-4.0, -2.0), hang=-0.45, wN=(84.0, 8.0), eN=None, pN=(-1, 0.1), openN=True, fN=(0.3, -1.0),
              aN=(64.0, 163.0), kN=None, aF=(150.0, 163.0), kF=None, face=0.95, glow=1.15, chN=(-6.0, 18.0))
    pull = dict(reach, lean=-0.2, off=(-8.0, 4.0), wN=(66.0, 18.0), eN=None, hang=-0.35, fN=(0.0, -1.0), roar=0.3)
    pour = dict(pull, lean=-0.24, off=(-10.0, 6.0), wN=(60.0, 26.0), roar=0.5, face=1.0, glow=1.25)
    return seq([(130, Q(**CARRY)), ("tw", 150, Q(**CARRY), reach, 0.35), ("tw", 150, Q(**CARRY), reach, 0.7), (170, reach),
                (200, dict(reach, wN=(86.0, 6.0))), (200, reach),
                ("tw", 170, reach, pull, 0.5), (200, pull), (220, pull), ("tw", 180, pull, pour, 0.6),
                (260, pour), (260, pour), (260, pour), (220, dict(pour, roar=0.2)),
                ("tw", 170, pour, Q(**CARRY), 0.5), (170, Q(**CARRY))])


def a_shed():   # phase transition (p2 sheet): the shell bursts off in stages
    roar = Q(lean=-0.2, off=(-4.0, 2.0), hang=-0.4, roar=0.9, fis=1.0, wN=(22.0, 96.0), eN=None, pN=(-1, 0.2), wF=(200.0, 92.0), eF=None,
             hc=(196.0, 175.0), ha=math.atan2(-1, 0.14), hlen=60.0, snap=True, grip=None, face=1.0, glow=1.4, under=0.55)
    hunch = dict(KNEEL, glow=1.3, face=1.0, fis=0.8)
    out = [(120, hunch, 1.0), (140, hunch, 0.9), (160, hunch, 0.8), (120, tween(hunch, roar, 0.3), 0.7), (120, tween(hunch, roar, 0.6), 0.6),
           (140, roar, 0.5), (160, roar, 0.42), (200, roar, 0.35), (200, dict(roar, roar=1.0), 0.35), (180, roar, 0.35),
           (170, tween(roar, Q(), 0.5), 0.35), (170, Q(), 0.35)]
    return out


def a_death():
    fall = dict(KNEEL, lean=0.7, off=(20.0, 44.0), hang=0.6, wN=(60.0, 160.0), eN=None, face=0.3, glow=0.8)
    out = [(120, tween(Q(), KNEEL, 0.5), 0.0, 0.0), (160, KNEEL, 0.0, 0.0), (240, dict(KNEEL, roar=0.8, hang=-0.2), 0.0, 0.0),
           (200, dict(KNEEL, roar=0.5, hang=-0.1), 0.0, 0.0), (160, tween(KNEEL, fall, 0.5), 0.05, 0.0), (200, fall, 0.15, 0.0),
           (240, fall, 0.3, 0.0), (240, fall, 0.45, 0.0), (240, fall, 0.6, 0.0), (240, fall, 0.75, 0.0),
           (200, fall, 0.85, 0.15), (200, fall, 0.9, 0.35), (220, fall, 0.95, 0.6), (900, fall, 1.0, 0.9)]
    return out


FALLEN = dict(KNEEL, lean=0.78, off=(26.0, 50.0), hang=0.5, wN=(70.0, 166.0), eN=None, pN=(-1, 0.4), aN=(34.0, 163.0), kN=(70.0, 172.0),
              aF=(150.0, 163.0), kF=(128.0, 170.0), face=0.4, rune=0.3, glow=0.95, fis=1.0, chN=(4.0, 8.0))
FALLEN["grip"] = (214.0, 150.0); FALLEN["wF"] = (214.0, 150.0); FALLEN["eF"] = None; FALLEN["ha"] = math.atan2(-1, 0.6)


def a_topple():   # legs buckle -> it crashes forward onto its knees and fists, the chest (core) near the ground
    buck = dict(KNEEL, face=0.9, glow=1.1, fis=0.5)
    return [(110, tween(Q(**CARRY), buck, 0.4)), (110, tween(Q(**CARRY), buck, 0.8)), (120, tween(buck, FALLEN, 0.5)),
            (90, FALLEN), (200, dict(FALLEN, glow=1.05)), (400, dict(FALLEN, face=0.5)), (500, dict(FALLEN, face=0.3)), (500, FALLEN)]


def a_rise():     # heaves itself up and slams a foot down (shockwave on frame 4)
    up = Q(**CARRY, lean=0.2, off=(-2.0, 8.0), aN=(76.0, 163.0), kN=None, aF=(160.0, 163.0), kF=None, hang=0.2, face=1.0, glow=1.25)
    return [(160, tween(FALLEN, KNEEL, 0.5)), (180, dict(KNEEL, face=0.9, glow=1.15)), (200, tween(KNEEL, up, 0.5)), (80, up),
            (100, dict(up, glow=1.35)), (220, up), (170, tween(up, Q(**CARRY), 0.6)), (160, Q(**CARRY))]


P1_A = [("idle", a_idle), ("walk", a_walk), ("slam", a_slam), ("fist", a_fist), ("stomp", a_stomp), ("stagger", a_stagger)]
P1_B = [("sweep", a_sweep), ("breath", a_breath), ("rain", a_rain), ("grab", a_grab)]
SHEETS = {
    "colossus": (P1_A, False), "colossus_b": (P1_B, False),
    "colossus_c": ([("topple", a_topple), ("rise", a_rise)], False), "colossus_p2d": ([("topple", a_topple), ("rise", a_rise)], True),
    "colossus_p2": (P1_A, True), "colossus_p2b": (P1_B, True), "colossus_p2c": ([("shed", a_shed), ("death", a_death)], True),
}
WINDOWS = {   # attack windows (frame indices within the tag) -> hit rect derived from the frame data
    "slam": dict(active=[8, 9], src="hbox", pad=(10, 6), floor=True),
    "fist": dict(active=[5, 6], src="hand", box=(-26, -18, 52, 36), floor=True),
    "stomp": dict(active=[6, 6], src="feet0", box=(-44, -26, 88, 26), floor=True),
    "sweep": dict(active=[4, 7], src="hbox", pad=(8, 4), floor=True, union=True),
}
TELEGRAPH = {"slam": (6, "hammer"), "fist": (3, "hand"), "stomp": (3, "feet0"), "sweep": (3, "hammer"), "breath": (3, "mouth"),
             "rain": (3, "mouth"), "grab": (4, "hand")}


def build_sheet(name, anims, p2, meta_frames, only_tags=None):
    frames, tags, plates = [], [], []
    has_plates = not p2
    for tag, fn in anims:
        a = len(frames)
        data = fn()
        fl = []
        for item in data:
            if name == "colossus_p2c":
                if tag == "shed":
                    ms, q, shell = item
                    img, _, fd = render(q, p2=True, shell=shell, plates=False)
                else:
                    ms, q, cool, dis = item
                    img, _, fd = render(q, p2=True, plates=False, cool=cool, dissolve=dis)
                pl = None
            else:
                ms, q = item
                img, pl, fd = render(q, p2=p2, plates=has_plates)
            frames.append({"ms": ms, "cels": {"Body": img}})
            plates.append(pl)
            fl.append(fd)
            print(f"  {name} {tag} {len(fl) - 1}", flush=True)
        tags.append((tag, a, len(frames) - 1))
        meta_frames.setdefault(tag, fl)
    if BUILD:
        asebuild.build(name, W, H, ["Body"], frames, tags)
        if has_plates:
            asebuild.build(name + "_pl", W, H, ["Plates"], [{"ms": f["ms"], "cels": {"Plates": p}} for f, p in zip(frames, plates)], tags)
    return frames, tags, plates


def preview(name, frames, tags, plates, k=2):
    rows = len(tags)
    cols = max(b - a + 1 for _, a, b in tags)
    cell = (W * k + 4, H * k + 16)
    sheet = Image.new("RGBA", (cols * cell[0] + 4, rows * cell[1] + 4), (38, 30, 28, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        for i in range(a, b + 1):
            bg = Image.new("RGBA", (W, H), (58, 50, 48, 255))
            bg.alpha_composite(frames[i]["cels"]["Body"])
            if plates[i] is not None:
                bg.alpha_composite(plates[i])
            x, y = 4 + (i - a) * cell[0], 4 + r * cell[1]
            sheet.alpha_composite(bg.resize((W * k, H * k), Image.NEAREST), (x, y + 12))
            d.text((x, y), f"{t} {i - a}", fill=(230, 200, 160, 255))
    sheet.save(os.path.join(PREV, f"{name}.png"))


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    meta_frames = {}
    mp = os.path.join(ASSETS, "colossus_meta.json")
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    if only:
        meta_frames.update(old.get("frames", {}))
    k = 1 if "--small" in sys.argv else 2
    for name, (anims, p2) in SHEETS.items():
        if only and name not in only:
            continue
        frames, tags, plates = build_sheet(name, anims, p2, meta_frames)
        preview(name, frames, tags, plates, k)
    attacks = {}
    for tag, w in WINDOWS.items():
        if tag not in meta_frames:
            continue
        fl = meta_frames[tag]
        rects = []
        for i in range(w["active"][0], w["active"][1] + 1):
            fd = fl[i]
            if w["src"] == "hbox":
                x, y, ww, hh = fd["hbox"]
                rects.append([x - w["pad"][0], y - w["pad"][1], ww + 2 * w["pad"][0], hh + w["pad"][1]])
            else:
                pt = fd["feet"][0] if w["src"] == "feet0" else fd[w["src"]]
                bx = w["box"]
                rects.append([int(pt[0] + bx[0]), int(pt[1] + bx[1]), bx[2], bx[3]])
        if w.get("union") or len(rects) > 1:
            x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
            x1 = max(r[0] + r[2] for r in rects); y1 = max(r[1] + r[3] for r in rects)
            r = [x0, y0, x1 - x0, y1 - y0]
        else:
            r = rects[0]
        if w.get("floor"):
            r[3] = H - r[1]
        attacks[tag] = {"active": w["active"], "hit": [int(v) for v in r]}
    tele = {}
    for tag, (fi, key) in TELEGRAPH.items():
        if tag in meta_frames:
            fd = meta_frames[tag][fi]
            pt = fd["feet"][0] if key == "feet0" else fd[key]
            tele[tag] = {"frame": fi, "at": [int(pt[0]), int(pt[1])]}
    meta = {"native": 1, "frame": [W, H], "anchor": ANCHOR, "hurtbox": [60, 40, 100, 136],
            "sheets": {"p1": {t: n for n, (an, p2) in SHEETS.items() if not p2 for t, _ in an},
                       "p2": {t: n for n, (an, p2) in SHEETS.items() if p2 for t, _ in an}},
            "attacks": attacks, "telegraph": tele, "frames": meta_frames,
            "notes": "faces right. parts: knee_n/knee_f/arm/chest rects per frame (frame coords). Plate sheets (<sheet>_pl) hold the "
                     "armour; clip them to a part rect to draw only intact plates. breath: fire from mouth at angle breath (rad, "
                     "facing right) on breath frames 5-12. grab: the near hand grips the crucible lip on frames 4-12."}
    for s in ("colossus", "colossus_p2"):
        with open(os.path.join(ASSETS, f"{s}_meta.json"), "w") as fh:
            json.dump(meta, fh, separators=(",", ":"))
    print("meta frames", {t: len(v) for t, v in meta_frames.items()}, "attacks", attacks)


if __name__ == "__main__":
    main()
