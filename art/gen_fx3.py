#!/usr/bin/env python3
"""FX v3 (ART_SPEC2 section B) -> art/fx_*.aseprite, assets/fx_*.png/.json

Weapon-art and spell effects for the full game. Same house style as gen_fx.py / gen_fx2.py
(reuses their helpers): crisp colour bands, Bayer-ordered falloff instead of blur, a few
alpha steps only for soft glows, >= 2 layers per sprite, one tag per sprite named without
the "fx_" prefix. Projectiles travel RIGHT; "pivot bottom" sprites sit on their last row.
Palette families: moon/frost blue (moonwave, lance), wind & ash (stormleap), crimson (bloodstep),
ember-gold fire (cinderblade), gold (warcry, warmth), violet-gold (shards), rot green (rotmist,
rot_hit), white-gold (holy_burst, petal).
Re-runnable: python3 art/gen_fx3.py [fx_name ...]
"""
import os, sys, math, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from gen_fx import (blank, put, disc, line, clean, breakup, bt, crescent, emit, comp_frame,  # noqa: E402
                    EMBER, DUST)
from gen_fx2 import A, CORE, G, CR, ASH, ramp_at, radial, ring, iflare, spark, outline_img  # noqa: E402

TR = (0, 0, 0, 0)
# ---------------------------------------------------------------- extra ramps (dark -> light)
MOON = [A((30, 52, 110)), A((62, 116, 200)), A((132, 192, 248)), A((206, 236, 255)), A((250, 252, 255))]
FROST = [A((26, 64, 120)), A((52, 132, 204)), A((126, 204, 244)), A((206, 244, 255)), A((250, 254, 255))]
ROT = [A((22, 38, 22)), A((48, 84, 34)), A((92, 138, 44)), A((150, 196, 70)), A((212, 238, 138))]
VIO = [A((46, 22, 80)), A((96, 52, 156)), A((164, 114, 226)), A((224, 198, 255)), CORE]
EMB = [A(EMBER[0][:3]), A(EMBER[1][:3]), A(EMBER[2][:3]), A(EMBER[3][:3]), A(EMBER[4][:3])]
WIND = [A((58, 64, 88)), A((104, 118, 150)), A((166, 186, 214)), A((226, 236, 250))]


def lay(*names):
    return {n: None for n in names}


def fin(d, refs=True):
    """clean() every layer (stray single pixels), each counting the others as neighbours."""
    out = {}
    keys = list(d.keys())
    for k in keys:
        others = tuple(d[o] for o in keys if o != k)
        out[k] = clean(d[k], ref=others) if refs else d[k]
    return out


def build(name, W, H, layers, cels, ms, tag):
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build(name, W, H, layers, frames, [(tag, 0, len(frames) - 1)])
    return frames


def blob(img, cx, cy, rx, ry, ramp, lx=-0.6, ly=-0.8, bands=(0.55, 0.05, -0.5), rim=None, soft=0.0):
    """Sphere-shaded blob lit from the upper-left, hard colour bands (ramp dark -> light).
    soft > 0 dithers the outer rim away (ordered, not noise) for wispy dust/smoke."""
    w, h = img.size
    for y in range(max(0, int(cy - ry - 1)), min(h, int(cy + ry + 2))):
        for x in range(max(0, int(cx - rx - 1)), min(w, int(cx + rx + 2))):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1:
                continue
            v = lx * nx + ly * ny
            if soft and d > 1 - soft and bt(x, y) < (d - (1 - soft)) / soft:
                continue
            if rim is not None and d > 0.82:
                img.putpixel((x, y), rim)
                continue
            i = 3 if v > bands[0] else (2 if v > bands[1] else (1 if v > bands[2] else 0))
            img.putpixel((x, y), ramp[i])


# ================================================================ moonwave
def moon_fn(dim=0.0):
    def f(s, u, x, y):
        v = (1 - s) - dim
        if s < 0.16:
            return (0, MOON[4] if dim < 0.1 else MOON[3])
        if s < 0.38:
            return (0, MOON[3] if v > 0.5 else MOON[2])
        if s < 0.66:
            return (1, MOON[2] if v > 0.3 else MOON[1])
        if s < 0.88 or bt(x, y) < 0.5:
            return (1, MOON[1] if v > 0.2 else MOON[0])
        return None
    return f


def fx_moonwave():
    """Pale-blue crescent wave travelling RIGHT, convex front at x~41, centred vertically.
    Loop: the crest breathes, glints run along the rim, a faint echo crescent and a few
    staggered streaks trail behind, motes peel off backwards."""
    W, H = 48, 48
    cels = []
    rnd = random.Random(3)
    motes = [(rnd.uniform(0, 24), rnd.uniform(-15, 15)) for _ in range(8)]
    STREAKS = [(13, 9, 0), (21, 12, 3), (28, 10, 6), (35, 8, 2)]      # (y, length, phase)
    for k in range(4):
        trail, glow, core, sp = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        th = 11.0 + 0.9 * math.sin(k * math.pi / 2)
        c2, g2, _ = crescent(W, H, 12, 24, 21, 21, -72, 72, 4.0, moon_fn(0.5), peak=1.0)
        trail.alpha_composite(g2)
        trail.alpha_composite(c2)
        c1, g1, _ = crescent(W, H, 19, 24, 22, 22, -80, 80, th, moon_fn(0.0), peak=1.0)
        glow.alpha_composite(g1)
        core.alpha_composite(c1)
        # staggered speed streaks well behind the crest (slide left 3px / frame, 12px cycle)
        for (yy, L, ph) in STREAKS:
            x1 = 22 - ((k * 3 + ph) % 12)
            for x in range(x1 - L, x1):
                if x < 0:
                    continue
                t = (x1 - x) / L
                if t > 0.7 and (x + yy) % 2:
                    continue
                put(trail, x, yy, MOON[3] if t < 0.2 else (MOON[2] if t < 0.55 else MOON[1]))
        # glints travelling along the leading rim (loop in 4)
        for j in range(2):
            ang = math.radians(-54 + ((k * 27 + j * 54) % 108))
            gx = 19 + math.cos(ang) * 21.5 - 0.5
            gy = 24 - math.sin(ang) * 21.5
            put(sp, gx, gy, CORE)
            for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(sp, gx + a, gy + b, MOON[3])
        # motes peeling off behind (drift left 6px / frame over a 24px cycle)
        for (x0, yo) in motes:
            x = 28 - ((x0 + k * 6) % 24)
            y = 24 + yo * (0.55 + 0.45 * (x / 28))
            put(sp, x, y, MOON[3] if x > 16 else MOON[2])
        cels.append({"Trail": clean(trail, ref=(glow, core)), "Glow": clean(glow, ref=(core,)),
                     "Core": clean(core, ref=(glow,)), "Sparkle": sp})
    return build("fx_moonwave", W, H, ["Trail", "Glow", "Core", "Sparkle"], cels, [70] * 4, "moonwave")


# ================================================================ stormleap
def ell_ring(front, back, cx, cy, rx, ry, wf, cf, cf2, cb, keep=1.0, seed=0):
    """Crisp perspective ring: the near (lower) half is wf px thick (bright outer pixel cf,
    inner cf2) on `front`; the far (upper) half is a 1px line cb on `back`."""
    n = int(8 * (rx + ry)) + 16
    for i in range(n):
        a = 2 * math.pi * i / n
        if keep < 1 and random.Random(seed * 977 + int(a * 6)).random() > keep:
            continue
        x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        if math.sin(a) >= -0.05:
            w = max(1, int(round(wf * (0.45 + 0.55 * math.sin(a)) if wf > 1 else 1)))
            for j in range(w):
                put(front, x, y + j - (w - 1) * 0.5, cf if j == w - 1 else cf2)
        else:
            if cb:
                put(back, x, y, cb)


def fx_stormleap():
    """Leap launch: a flat shock ring blasts out along the ground, rings of wind climb the
    column, ash clouds roll out to both sides. 96x40, pivot bottom-centre (48, 39)."""
    W, H = 96, 40
    cx, gy = 48.0, 35.5
    rnd = random.Random(12)
    specks = [(rnd.choice((-1, 1)), rnd.uniform(0.4, 1.0), rnd.uniform(0.6, 1.4), rnd.uniform(-1, 1)) for _ in range(18)]
    streaks = [(rnd.uniform(-8, 8), rnd.uniform(0.8, 1.25), rnd.uniform(0, 6)) for _ in range(8)]
    GR = [8, 20, 30, 37, 42, 45, 47, 0]                  # ground ring rx
    RINGS = [[], [(11, 28)], [(15, 23), (9, 30)], [(19, 17), (14, 25)], [(22, 11), (18, 19)],
             [(24, 6), (21, 13)], [(25, 2), (23, 8)], []]  # (rx, y) climbing wind rings
    ms = [40, 50, 60, 60, 70, 70, 80, 90]
    cels = []
    for k in range(8):
        back, dust, rings, front = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        lv = 0 if k < 4 else (1 if k < 6 else 2)
        if k == 0:
            for x in range(W):
                d = abs(x + 0.5 - cx)
                if d < 18:
                    put(front, x, gy + 1, WIND[3] if d < 8 else WIND[2])
                    if d < 10:
                        put(front, x, gy, WIND[2])
            radial(rings, cx, gy, 7, WIND[:4], 0.8)
            disc(front, cx - 0.5, gy - 1.5, 2.2, CORE)
        if GR[k]:
            r = GR[k]
            ell_ring(front, back, cx, gy, r, r * 0.12 + 1.4, 3 if k < 4 else 2,
                     WIND[3 - lv], WIND[2 - lv] if lv < 2 else WIND[0], WIND[1 - min(lv, 1)],
                     keep=1 if k < 5 else 0.7, seed=k)
        for i, (rx, y) in enumerate(RINGS[k]):
            l2 = min(2, lv + i)
            ell_ring(rings, back, cx, y, rx, rx * 0.22 + 1.0, 2 if k < 5 else 1,
                     CORE if (k < 3 and i == 0) else WIND[3 - l2], WIND[2 - l2] if l2 < 2 else WIND[0],
                     WIND[1] if l2 < 2 else WIND[0], keep=1 if k < 5 else 0.75, seed=k * 3 + i)
        # rising wind streaks up the column
        if 1 <= k <= 5:
            for (ox, spd, ph) in streaks:
                y1 = gy - 4 - k * 5.0 * spd
                L = 8 - abs(k - 3) * 1.5
                for j in range(int(L)):
                    put(front, cx + ox + math.sin((y1 + j) * 0.35 + ph) * 0.8, y1 + j,
                        WIND[3] if j < 2 and k < 4 else (WIND[2] if j < L - 2 else WIND[1]))
        # ash clouds rolling out along the ground on both sides (soft, low, lighter on top)
        if 1 <= k <= 7:
            t = k
            for side in (-1, 1):
                for (off, sz, lift) in ((0, 1.0, 0), (-6, 0.7, 1.5), (7, 0.65, 0.5), (3, 0.55, 3.5)):
                    px_ = cx + side * (12 + t * 4.4 + off)
                    r = (2.4 + 1.2 * min(t, 4)) * sz
                    py = gy - r * 0.45 - lift - t * 0.35
                    blob(dust, px_, py, r * 1.45, r * 0.7, [ASH[1], ASH[1], ASH[2], ASH[3]],
                         bands=(0.45, -0.1, -0.6), soft=0.45)
            if k >= 5:
                breakup(dust, [0.7, 0.45, 0.25][k - 5], k * 7, block=2)
        # grit flung out
        if 1 <= k <= 6:
            t = k
            for (side, spd, sz, ph) in specks:
                x = cx + side * (10 + t * 6.5 * spd)
                y = gy - (t * 2.6 * sz - 0.33 * t * t * sz) - 1 + ph
                if y > gy + 1:
                    continue
                put(front, x, y, ASH[3] if k < 4 else ASH[2])
        cels.append({"Back": clean(back, ref=(rings, front)), "Dust": dust, "Rings": clean(rings, ref=(back, front)),
                     "Front": clean(front, ref=(rings,))})
    return build("fx_stormleap", W, H, ["Back", "Dust", "Rings", "Front"], cels, ms, "stormleap")


# ================================================================ bloodstep
DASH = [
    "..............###.....",
    ".............#####....",
    ".............#####....",
    ".............####.....",
    "..........########....",
    "........###########...",
    ".....#############.###",
    "...##########.####..##",
    ".#########....###.....",
    "##########....###.....",
    ".########.....####....",
    "..######......####....",
    "...####.......#####...",
    "....##.......###.###..",
    "............###...###.",
    "...........###.....###",
    "..........###......###",
    ".........###........##",
    "........###.........#.",
    ".......###............",
    "......###.............",
    ".....##...............",
]
DASH_X, DASH_Y = 15, 6


def dash_body(x, y, ox=0):
    """Hand-drawn dashing knight silhouette (leaning in, cape streaming back, stride)."""
    gx, gy = int(x - ox - DASH_X), int(y - DASH_Y)
    return 0 <= gy < len(DASH) and 0 <= gx < len(DASH[0]) and DASH[gy][gx] == '#'


def fx_bloodstep():
    """Crimson afterimage streak of a dashing figure; the dash goes RIGHT. 48x32, centred.
    f0 vivid crimson ghost + smear lines; then the ghost splits into scanline slices that
    slide back (left) at different speeds and thin out, droplets trail and fall."""
    W, H = 48, 32
    rnd = random.Random(21)
    motes = [(rnd.uniform(6, 34), rnd.uniform(6, 28), rnd.uniform(0.5, 1.5)) for _ in range(14)]
    ms = [50, 60, 70, 80, 90]
    # per-row slide speed for the slicing afterimage (px per frame, leftward)
    slide = [rnd.choice((1, 2, 3, 4)) for _ in range(H)]
    cels = []
    for k in range(5):
        ghost, streak, sp = blank(W, H), blank(W, H), blank(W, H)
        for y in range(H):
            # rows vanish progressively: every 3rd, then every 2nd, then most
            if k == 2 and y % 3 == 0:
                continue
            if k == 3 and y % 3 != 1:
                continue
            if k == 4:
                continue
            ox = -slide[y] * max(0, k - 1) * 1.5
            for x in range(W):
                if not dash_body(x, y, ox):
                    continue
                front = not dash_body(x + 1, y, ox) or not dash_body(x, y - 1, ox)
                if k == 0:
                    c = CR[3] if front else CR[2]
                elif k == 1:
                    c = CR[2] if front else CR[1]
                else:
                    c = CR[2] if front and k == 2 else CR[1]
                ghost.putpixel((x, y), c)
        # horizontal smear lines trailing from the body's back edge
        rows = [(8, 8), (10, 14), (12, 18), (14, 12), (16, 10), (20, 14), (23, 9), (26, 7)]
        for i, (yy, L) in enumerate(rows):
            xb = min((x for x in range(W) if dash_body(x, yy)), default=24)
            L2 = L + k * 4
            fade = [0.0, 0.2, 0.4, 0.6, 0.8][k]
            for x in range(int(xb - L2), int(xb + 2)):
                if x < 0:
                    continue
                t = (xb + 2 - x) / (L2 + 2)
                if t < fade or (t > 0.75 and (x + yy) % 2):
                    continue
                c = CORE if (t < 0.3 and k == 0 and i in (2, 5)) else (CR[3] if t < 0.35 and k < 2 else
                                                                     (CR[2] if t < 0.65 else CR[1]))
                put(streak, x, yy, c)
        # droplets flung off, trailing left and falling
        if k >= 1:
            for (mx, my, sz) in motes:
                x = mx - k * 2.5 * sz
                y = my + 0.3 * k * k * sz
                if x < 0 or y >= H or not (k < 4 or sz > 1.0):
                    continue
                put(sp, x, y, CR[3] if k < 3 else CR[2])
                if k < 3:
                    put(sp, x + 1, y, CR[1])
        cels.append({"Streak": clean(streak, ref=(ghost,)), "Ghost": ghost, "Droplets": sp})
    return build("fx_bloodstep", W, H, ["Streak", "Ghost", "Droplets"], cels, ms, "bloodstep")


# ================================================================ cinderblade
def fire_tongue(img_back, img_front, bx, by, h, w, sway, front, dim=0.0):
    """Rising flame tongue from (bx, by); ember-gold bands, crimson-ember tip."""
    img = img_front if front else img_back
    if h < 1:
        return
    for i in range(int(h) + 1):
        t = i / h
        y = by - i
        hw = w * (1 - t) ** 0.7 + 0.3
        sx = sway * t * t
        for x in range(int(bx - w - 4), int(bx + w + 5)):
            d = abs(x + 0.5 - (bx + sx))
            if d > hw:
                continue
            v = (1 - t) * 1.05 - (d / hw) * 0.35 - dim - (0 if front else 0.18)
            if v > 0.78:
                c = CORE if front else G[3]
            elif v > 0.58:
                c = G[3]
            elif v > 0.42:
                c = EMB[3]
            elif v > 0.26:
                c = EMB[2]
            elif v > 0.1:
                c = EMB[1]
            elif v > -0.05 and t > 0.3:
                c = EMB[0]
            else:
                continue
            put(img, x, y, c)


def fx_cinderblade():
    """Fire aura licking around a blade: a ring of ember-gold tongues rising off an empty
    (transparent) core so the weapon shows through. 32x32 centred, 4-frame loop."""
    W, H = 32, 32
    cx, cy = 16.0, 18.0
    N = 11
    rnd = random.Random(5)
    base = [(i * 360 / N + rnd.uniform(-6, 6), rnd.uniform(0.75, 1.2), rnd.uniform(0, 2 * math.pi)) for i in range(N)]
    sparks = [(rnd.uniform(-9, 9), rnd.uniform(0, 1)) for _ in range(6)]
    cels = []
    for k in range(4):
        back, front, emb = blank(W, H), blank(W, H), blank(W, H)
        for (ang, hm, ph) in sorted(base, key=lambda b: -math.sin(math.radians(b[0]))):
            a = math.radians(ang)
            s = math.sin(a)
            bx = cx + math.cos(a) * 7.0
            by = cy - s * 8.0
            flick = 0.5 + 0.5 * math.sin(ph + k * math.pi / 2)
            # tongues on the upper arc are tallest; on the underside they're short licks
            h = (3 + 6 * (0.5 + 0.5 * s)) * hm * (0.75 + 0.45 * flick)
            sway = math.sin(ph * 2 + k * math.pi / 2) * 1.6
            fire_tongue(back, front, bx, by, h, 1.9 + 0.3 * hm, sway, front=(s <= 0.2 or abs(math.cos(a)) > 0.6))
        # clear the core so the blade reads through (soft rounded hole)
        for img in (back, front):
            p = img.load()
            for y in range(H):
                for x in range(W):
                    if ((x + 0.5 - cx) / 4.6) ** 2 + ((y + 0.5 - cy) / 6.0) ** 2 < 1:
                        p[x, y] = TR
        # embers breaking off the top (4-frame cycle, 5px per frame)
        for (ox, ph) in sparks:
            t = (ph + k / 4) % 1.0
            x = cx + ox * (1 - 0.3 * t) + math.sin(t * 6 + ox) * 1.0
            y = cy - 8 - t * 16
            if y < 0:
                continue
            put(emb, x, y, G[3] if t < 0.4 else (EMB[2] if t < 0.75 else EMB[1]))
        cels.append({"Back": clean(back, ref=(front,)), "Front": clean(front, ref=(back,)), "Embers": emb})
    return build("fx_cinderblade", W, H, ["Back", "Front", "Embers"], cels, [80] * 4, "cinderblade")


# ================================================================ warcry
def fx_warcry():
    """Expanding gold shout ring, centred (32, 32). Two rings (a hard leading edge and a
    softer echo), radial speed streaks, and a sound-burst flash at the mouth."""
    W, H = 64, 64
    cx = cy = 32.0
    R1 = [5, 11, 17, 22, 26, 29, 31, 0]
    R2 = [0, 0, 7, 12, 16, 20, 23, 25]
    TH = [3.5, 3.4, 3.0, 2.6, 2.0, 1.5, 1.0, 0]
    ms = [40, 50, 50, 60, 60, 70, 80, 90]
    cels = []
    for k in range(8):
        inner, rng, streaks, core = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        r = R1[k]
        if r:
            lv = 4 if k < 3 else (3 if k < 5 else 2)
            ring(rng, cx, cy, r, r, TH[k], G[lv] if lv < 4 else G[3], keep=1 if k < 5 else 0.7, seed=k,
                 col_in=G[lv - 1])
            if k < 4:
                ring(core, cx, cy, r, r, 1.0, CORE if k < 2 else G[3])
            # faint fill just inside the ring (dithered)
            for y in range(H):
                for x in range(W):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    q = (r - TH[k] - d) / 6
                    if 0 <= q <= 0.6 and bt(x, y) > 0.7 + q * 0.5 and k < 6:
                        inner.putpixel((x, y), G[1] if q < 0.25 and k < 4 else G[0])
        if R2[k]:
            ring(rng, cx, cy, R2[k], R2[k], 1.2, G[2] if k < 5 else G[1], keep=0.85 if k < 5 else 0.55,
                 seed=k + 20)
        if k == 0:
            disc(core, cx - 0.5, cy - 0.5, 3.0, CORE)
            iflare(core, rng, cx, cy, 11, 6, 2.0, CORE, G[3], G[2], G[2])
        elif k == 1:
            disc(core, cx - 0.5, cy - 0.5, 1.8, G[3])
        # 12 radial streaks riding just outside the leading ring
        if 1 <= k <= 5:
            for i in range(12):
                a = math.radians(i * 30 + 15 * (k % 2))
                for j in range(2, 2 + 6 - abs(k - 2)):
                    put(streaks, cx + math.cos(a) * (r + j), cy - math.sin(a) * (r + j),
                        G[3] if j < 4 and k < 4 else G[2])
        if k == 7:
            breakup(rng, 0.5, 9)
        cels.append({"Inner": inner, "Ring": clean(rng, ref=(core,)), "Streaks": streaks, "Core": core})
    return build("fx_warcry", W, H, ["Inner", "Ring", "Streaks", "Core"], cels, ms, "warcry")


# ================================================================ shards
SHARD_POSES = [
    # 12x12, tip at (10, 6). J/j/I/i violet light->dark, W white, Y/y gold. Top facet lit.
    ["............",
     "............",
     "............",
     "............",
     "......J.....",
     "...IjJJJj...",
     ".yYjJJWJJJW.",
     "...iIIIIi...",
     "......i.....",
     "............",
     "............",
     "............"],
    # rolled edge-on
    ["............",
     "............",
     "............",
     "............",
     "............",
     "...jJJJJJ...",
     "yYIjjJWJJJW.",
     "...iIIIIi...",
     "............",
     "............",
     "............",
     "............"],
    # bottom facet lit (rolled half-way)
    ["............",
     "............",
     "............",
     "............",
     "......i.....",
     "...iIIIIi...",
     ".yYjJJWJJJW.",
     "...IjJJJj...",
     "......J.....",
     "............",
     "............",
     "............"],
    ["............",
     "............",
     "............",
     "............",
     "............",
     "...iIIIIj...",
     "yYIjjJJWJJW.",
     "...jJJJJJ...",
     "............",
     "............",
     "............",
     "............"],
]


def fx_shards():
    """Small violet-gold crystal shard flying RIGHT, tip at (10, 6). 12x12, 4-frame loop:
    the crystal rolls (the lit facet flips), a gold glint rides the spine, motes trail."""
    W, H = 12, 12
    cmap = {'J': VIO[3], 'j': VIO[2], 'I': VIO[1], 'i': VIO[0], 'W': CORE, 'Y': G[3], 'y': G[2]}
    cels = []
    for k, pose in enumerate(SHARD_POSES):
        body, trail = blank(W, H), blank(W, H)
        for y, row in enumerate(pose):
            for x, ch in enumerate(row):
                if ch != '.':
                    body.putpixel((x, y), cmap[ch])
        put(body, [5, 7, 5, 8][k], 6, G[3])                 # gold glint on the spine
        # trailing motes: violet + gold, alternating heights (2-frame flicker, 4-frame loop)
        put(trail, 1 - (k % 2), 4 + (k % 2), VIO[2] if k < 2 else G[2])
        put(trail, 0 + (k % 2), 8 - (k % 2), G[2] if k < 2 else VIO[2])
        cels.append({"Trail": trail, "Body": body})
    return build("fx_shards", W, H, ["Trail", "Body"], cels, [60] * 4, "shards")


# ================================================================ warmth
def fx_warmth():
    """Gentle golden healing motes rising around the player. 32x48, pivot bottom (16, 47).
    Seamless 6-frame loop: each mote climbs 6px per frame on a 36px cycle."""
    W, H = 32, 48
    cx = 16.0
    rnd = random.Random(8)
    motes = [(rnd.uniform(-11, 11), rnd.uniform(0, 36), rnd.random() < 0.35, rnd.uniform(0, 6)) for _ in range(13)]
    cels = []
    for k in range(6):
        halo, glow, mo = blank(W, H), blank(W, H), blank(W, H)
        p = 0.5 + 0.5 * math.cos(2 * math.pi * k / 6)
        # soft ground glow (alpha steps) + a faint rising column
        for y in range(H):
            for x in range(W):
                dx = (x + 0.5 - cx) / (11 + 1.5 * p)
                dy = (y + 0.5 - 45.5) / 2.6
                d = dx * dx + dy * dy
                if d <= 1:
                    halo.putpixel((x, y), A(G[3], 130) if d < 0.3 else (A(G[3], 85) if d < 0.65 else A(G[2], 60)))
        # rising motes
        for (ox, y0, big, ph) in motes:
            t = (y0 + k * 6) % 36                     # 0 .. 36 climb
            y = 44 - t
            x = cx + ox * (1 - t / 80) + math.sin(t * 0.25 + ph) * 1.3
            life = t / 36
            if life > 0.92:
                continue
            c = CORE if life < 0.35 else (G[3] if life < 0.7 else G[2])
            if big and life < 0.75:
                put(mo, x, y, c)
                for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(glow, x + a, y + b, G[3] if life < 0.35 else G[2])
            else:
                put(mo, x, y, c)
                if life < 0.5:
                    put(glow, x, y + 1, G[2])
        cels.append({"Halo": halo, "Glow": glow, "Motes": mo})
    return build("fx_warmth", W, H, ["Halo", "Glow", "Motes"], cels, [100] * 6, "warmth")


# ================================================================ frost lance
def fx_lance():
    """Frost lance travelling RIGHT: long faceted ice spike (tip x=38, centre row 5/6),
    facet seams, back-swept crystal spurs, a soft cold halo, frost motes shedding behind.
    40x12, 4-frame loop."""
    W, H = 40, 12
    cy = 6.0
    rnd = random.Random(14)
    motes = [(rnd.uniform(0, 16), rnd.uniform(-3.5, 3.5)) for _ in range(8)]
    cels = []
    for k in range(4):
        body, glow, sp = blank(W, H), blank(W, H), blank(W, H)
        for x in range(7, 39):
            t = (x - 7) / 31                          # 0 = back end, 1 = tip
            half = 3.0 * (1 - t) ** 0.85 + 0.2 if t > 0.22 else 3.0 * (0.45 + 0.55 * t / 0.22) + 0.2
            seam = (x - 7) % 7 == 3 and t < 0.8        # facet seams slanting back
            for y in range(H):
                dy = y + 0.5 - cy
                if abs(dy) > half:
                    continue
                if -1.0 < dy <= 0:
                    c = FROST[4] if t > 0.1 else FROST[3]
                elif dy < 0:
                    c = FROST[3] if abs(dy) < half - 0.9 else FROST[2]
                else:
                    c = FROST[2] if abs(dy) < half - 0.9 else FROST[1]
                if seam and abs(dy) > 0.9:
                    c = FROST[1] if dy > 0 else FROST[2]
                body.putpixel((x, y), c)
        # back-swept crystal spurs off the rear half
        for (bx, up, L) in ((12, True, 3), (16, False, 3), (21, True, 2), (25, False, 2)):
            for j in range(L):
                yy = cy - 3.5 - j if up else cy + 2.5 + j
                put(body, bx - j - 1, yy, FROST[3] if up else FROST[2])
        # splintered back end
        for (x, y, c) in ((6, 4, FROST[2]), (5, 6, FROST[3]), (6, 8, FROST[1]), (4, 5, FROST[1])):
            put(body, x, y, c)
        # travelling glint along the ridge + the tip
        gx = 12 + k * 6
        put(body, gx, cy - 1, CORE)
        put(body, gx + 1, cy - 1, CORE)
        put(body, 38, cy - 1, CORE)
        # cold halo: translucent 1px rim around the whole lance
        bp = body.load()
        for y in range(H):
            for x in range(W):
                if bp[x, y][3]:
                    continue
                if any(0 <= x + a < W and 0 <= y + b < H and bp[x + a, y + b][3]
                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    glow.putpixel((x, y), A(FROST[2][:3], 90 if x > 20 else 60))
        # frost motes shedding behind (drift left 4px / frame over a 16px cycle)
        for (x0, yo) in motes:
            x = 16 - ((x0 + k * 4) % 16)
            y = cy + yo * (1.2 - x / 20)
            put(sp, x, y, FROST[3] if x > 8 else FROST[2])
        cels.append({"Glow": glow, "Body": body, "Frost": sp})
    return build("fx_lance", W, H, ["Glow", "Body", "Frost"], cels, [60] * 4, "lance")


# ================================================================ rot mist
def fx_rotmist():
    """Rot-green poison cloud billowing up from the ground, lingering, then thinning away.
    64x48, pivot bottom (32, 47). Puffs have soft dithered rims (gas, not foliage); the
    lingering/dissipating frames rise, loosen and drop to two alpha steps."""
    W, H = 64, 48
    rnd = random.Random(33)
    # puffs: (x, y_final, r_final, delay)
    puffs = [(32, 36, 11, 0), (20, 39, 8, 0.3), (44, 39, 8, 0.3), (26, 27, 9, 0.8), (39, 28, 9, 0.9),
             (12, 42, 6, 1.0), (52, 42, 6, 1.0), (32, 19, 8, 1.4), (18, 31, 6, 1.4), (47, 32, 6, 1.6)]
    bubbles = [(rnd.uniform(10, 54), rnd.uniform(0, 1), rnd.uniform(0.7, 1.3)) for _ in range(12)]
    ms = [60, 70, 80, 90, 100, 100, 110, 120]
    SOFT = [0.3, 0.3, 0.3, 0.3, 0.35, 0.5, 0.7, 0.85]
    ALPHA = [255, 255, 255, 255, 255, 255, 200, 150]
    cels = []
    for k in range(8):
        back, cloud, bub = blank(W, H), blank(W, H), blank(W, H)
        for (px, py, pr, dl) in sorted(puffs, key=lambda p: p[1]):
            g = max(0.0, min(1.0, (k + 1.4 - dl * 1.5) / 3.4))
            if g <= 0.12:
                continue
            r = pr * (0.45 + 0.55 * g) * (1 + 0.03 * max(0, k - 4))
            y = 47 - (47 - py) * g - r * 0.25 - max(0, k - 4) * 1.2
            ramp = [ROT[1], ROT[2], ROT[3], ROT[4]] if k < 5 else [ROT[1], ROT[1], ROT[2], ROT[3]]
            blob(cloud, px, y, r * 1.12, r * 0.9, ramp, bands=(0.7, 0.1, -0.45), soft=SOFT[k])
            blob(back, px + 1, y + 2, r * 1.2, r * 0.85, [ROT[0], ROT[0], ROT[1], ROT[1]], soft=SOFT[k] + 0.1)
        # soft ground stain
        for x in range(6, 58):
            d = abs(x + 0.5 - 32) / 26
            if d < 1 and bt(x, 46) < 1.1 - d:
                put(back, x, 46, ROT[1])
                put(back, x, 47, ROT[0])
        if ALPHA[k] < 255:
            for img in (cloud, back):
                px_ = img.load()
                for y in range(H):
                    for x in range(W):
                        c = px_[x, y]
                        if c[3]:
                            px_[x, y] = (c[0], c[1], c[2], ALPHA[k])
        # rising bubbles / spores
        if k >= 1:
            for (bx, ph, spd) in bubbles:
                t = (k - 1) + ph * 2
                y = 40 - t * 5 * spd
                if y < 1:
                    continue
                c = ROT[4] if (k < 6 and spd > 1.0) else ROT[3]
                put(bub, bx + math.sin(t + bx) * 1.2, y, c)
                if spd > 1.15 and k < 6:
                    put(bub, bx + math.sin(t + bx) * 1.2 + 1, y, ROT[2])
        cels.append({"Back": back, "Cloud": outline_rot(cloud), "Spores": bub})
    return build("fx_rotmist", W, H, ["Back", "Cloud", "Spores"], cels, ms, "rotmist")


def outline_rot(img):
    """Darken the lower/right boundary of the cloud so the puff shapes read (no black line)."""
    w, h = img.size
    p = img.load()
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if p[x, y][3] and ((y + 1 < h and not p[x, y + 1][3]) or (x + 1 < w and not p[x + 1, y][3])):
                base = ROT[0] if p[x, y][:3] in (ROT[1][:3], ROT[0][:3]) else ROT[1]
                op[x, y] = base[:3] + (p[x, y][3],)
    return out


# ================================================================ rot hit
def fx_rot_hit():
    """Green rot splatter, centred (16, 16): pale flash, lobed splash, thick falling gobs."""
    W, H = 32, 32
    cx = cy = 16.0
    rnd = random.Random(44)
    gobs = []
    for i in range(14):
        a = math.radians(i * 360 / 14 + rnd.uniform(-10, 10))
        gobs.append((math.cos(a) * rnd.uniform(1.8, 3.0), -math.sin(a) * rnd.uniform(1.6, 2.8) - 0.6,
                     rnd.uniform(0.9, 1.8)))
    ms = [40, 50, 60, 70, 90]
    cels = []
    for k in range(5):
        splash, dl, core = blank(W, H), blank(W, H), blank(W, H)
        rc = [4.5, 6.5, 5.0, 2.5, 0][k]
        if rc:
            for y in range(H):
                for x in range(W):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    ang = math.atan2(dy, dx)
                    rr = rc * (1 + 0.35 * math.sin(ang * 6 + 1) + 0.12 * math.sin(ang * 3))
                    d = math.hypot(dx, dy)
                    if d <= rr:
                        c = ROT[4] if (d < rr * 0.4 and dy < 0 and k < 2) else (
                            ROT[3] if d < rr * 0.7 else ROT[2] if k < 3 else ROT[1])
                        splash.putpixel((x, y), c)
        if k == 0:
            disc(core, cx - 0.5, cy - 0.5, 2.0, A((236, 250, 190)))
            iflare(core, splash, cx - 0.5, cy - 0.5, 8, 4, 1.4, A((236, 250, 190)), ROT[4], ROT[3], ROT[3])
        elif k == 1:
            ring(splash, cx, cy, 10, 10, 1.3, ROT[3], keep=0.75, seed=1, col_in=ROT[2])
        t = k + 1
        for (vx, vy, sz) in gobs:
            x = cx + vx * t
            y = cy + vy * t + 0.4 * t * t
            s = sz * (1.0 - 0.12 * k)
            if s < 0.45:
                continue
            if k < 3:
                line(dl, x - vx * 0.9, y - (vy + 0.8 * t) * 0.9, x, y, ROT[2])
            disc(dl, x - 0.5, y - 0.5, s * 0.8, ROT[3] if k < 3 else ROT[2])
            put(dl, x - 0.5, y - 0.5, ROT[4] if k < 2 else ROT[3])
            if s > 1.0:
                put(dl, x - 0.5, y + 0.5 + s * 0.5, ROT[1])
        cels.append({"Splash": clean(splash, ref=(dl, core)), "Gobs": clean(dl, ref=(splash,)), "Core": core})
    return build("fx_rot_hit", W, H, ["Splash", "Gobs", "Core"], cels, ms, "rot_hit")


# ================================================================ holy burst
def fx_holy_burst():
    """White-gold radiant explosion, centred (32, 32): blinding core + 8-point star, a hard
    shock ring, long light rays, then drifting motes and a fading halo."""
    W, H = 64, 64
    cx = cy = 32.0
    rnd = random.Random(55)
    motes = [(rnd.uniform(0, 360), rnd.uniform(0.6, 1.2), rnd.random() < 0.3) for _ in range(22)]
    rays = [i * 45 + (22.5 if i % 2 else 0) for i in range(8)]
    ms = [40, 50, 60, 60, 70, 80, 90, 100]
    cels = []
    for k in range(8):
        halo, glow, core, sp = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            radial(glow, cx, cy, 9, G[1:4], 0.7)
            disc(core, cx - 0.5, cy - 0.5, 4.5, CORE)
            iflare(core, glow, cx, cy, 14, 7, 2.2, CORE, CORE, G[3], G[3])
        elif k in (1, 2):
            R = [0, 13, 11][k]
            for y in range(H):
                for x in range(W):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d <= R + 6 and d > R and bt(x, y) < 1 - (d - R) / 6:
                        halo.putpixel((x, y), A(G[3][:3], 110))
            disc(glow, cx - 0.5, cy - 0.5, R, G[3])
            disc(core, cx - 0.5, cy - 0.5, R * 0.72, CORE)
            iflare(core, glow, cx, cy, 30 if k == 1 else 27, 16 if k == 1 else 12, 3.2 if k == 1 else 2.4,
                   CORE, CORE, G[3], G[3])
            ring(glow, cx, cy, R + 5 + 3 * k, R + 5 + 3 * k, 1.6, G[3], col_in=G[2])
        elif k == 3:
            disc(glow, cx - 0.5, cy - 0.5, 7, G[2])
            disc(glow, cx - 0.5, cy - 0.5, 5, G[3])
            disc(core, cx - 0.5, cy - 0.5, 3, CORE)
            iflare(core, glow, cx, cy, 18, 8, 1.8, CORE, G[3], G[2], G[2])
            ring(glow, cx, cy, 22, 22, 1.4, G[3], keep=0.9, seed=3, col_in=G[2])
        elif k == 4:
            disc(glow, cx - 0.5, cy - 0.5, 3.5, G[2])
            disc(core, cx - 0.5, cy - 0.5, 1.6, G[3])
            iflare(core, glow, cx, cy, 10, 4, 1.2, G[3], G[2], G[1], G[1])
            ring(glow, cx, cy, 26, 26, 1.0, G[2], keep=0.65, seed=4)
        elif k == 5:
            put(core, cx - 0.5, cy - 0.5, G[3])
            ring(glow, cx, cy, 29, 29, 1.0, G[1], keep=0.45, seed=5)
        # long thin rays between the flare arms (frames 1-3)
        if 1 <= k <= 3:
            for a_ in rays[1::2]:
                a = math.radians(a_)
                L = [0, 26, 29, 24][k]
                for j in range(6, L):
                    t = j / L
                    if k == 3 and bt(j, int(a_)) < t:
                        continue
                    put(core if t < 0.5 else glow, cx - 0.5 + math.cos(a) * j, cy - 0.5 - math.sin(a) * j,
                        CORE if t < 0.4 else (G[3] if t < 0.75 else G[2]))
        # drifting motes, slowing and floating up
        if k >= 2:
            t = k - 1
            for (a_, spd, big) in motes:
                a = math.radians(a_)
                r = (10 + 14 * (1 - math.exp(-t * 0.6))) * spd * 1.2
                x, y = cx + math.cos(a) * r, cy - math.sin(a) * r - t * 0.8
                lvl = 4 if k < 4 else (3 if k < 6 else 2)
                c = CORE if lvl == 4 else G[lvl]
                put(sp, x, y, c)
                if big and k < 6:
                    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        put(sp, x + dx, y + dy, G[lvl - 1])
        cels.append({"Halo": halo, "Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,)), "Motes": sp})
    return build("fx_holy_burst", W, H, ["Halo", "Glow", "Core", "Motes"], cels, ms, "holy_burst")


# ================================================================ petal
PETAL_POSES = [
    # 8x8 white-gold petal tumbling: face-on, tilting, edge-on, flipped (W core, Y light, y mid, G dark)
    ["........",
     "...WW...",
     "..WWWY..",
     ".YWWYYy.",
     ".yYYYyG.",
     "..yyyG..",
     "...GG...",
     "........"],
    ["........",
     "....WY..",
     "...WWYy.",
     "..WWYyG.",
     ".YWYyG..",
     ".yYyG...",
     "..GG....",
     "........"],
    ["........",
     "........",
     "......G.",
     ".WWYYyG.",
     ".GyyyG..",
     "........",
     "........",
     "........"],
    ["........",
     "..YW....",
     ".yYWW...",
     ".GyYWW..",
     "..GyYWY.",
     "...GyYy.",
     "....GG..",
     "........"],
]


def fx_petal():
    """A falling white-gold petal (engine moves it); 4-frame tumble loop, centred."""
    W, H = 8, 8
    cmap = {'W': CORE, 'Y': G[3], 'y': G[2], 'G': G[1]}
    cels = []
    for k, pose in enumerate(PETAL_POSES):
        body, glint = blank(W, H), blank(W, H)
        for y, row in enumerate(pose):
            for x, ch in enumerate(row):
                if ch != '.':
                    body.putpixel((x, y), cmap[ch])
        if k == 0:
            glint.putpixel((3, 2), CORE)
        cels.append({"Body": body, "Glint": glint})
    return build("fx_petal", W, H, ["Body", "Glint"], cels, [110, 90, 90, 110], "petal")


# ================================================================ preview
BG = (92, 92, 100, 255)
CELL_BG = (44, 42, 54, 255)


def preview(all_fx, S=3):
    """All effects as rows (one row per sprite, frames left->right) on mid-grey, 3x;
    small sprites get an extra 4x zoom so their pixels can be judged."""
    rows = []
    for name, frames, layers in all_fx:
        w, h = frames[0]["cels"][layers[0]].size
        z = 4 if max(w, h) <= 12 else 1
        strip = Image.new("RGBA", (len(frames) * (w * z + 2) + 2, h * z + 4), BG)
        for i, fr in enumerate(frames):
            cell = Image.new("RGBA", (w, h), CELL_BG)
            cell.alpha_composite(comp_frame(fr, layers))
            if z > 1:
                cell = cell.resize((w * z, h * z), Image.NEAREST)
            strip.paste(cell, (2 + i * (w * z + 2), 2))
        rows.append((name, strip))
    LBL = 40
    Wt = max(r.width for _, r in rows) + LBL
    Ht = sum(r.height for _, r in rows)
    sheet = Image.new("RGBA", (Wt, Ht), BG)
    y = 0
    for name, r in rows:
        sheet.paste(r, (LBL, y))
        y += r.height
    sheet = sheet.resize((Wt * S, Ht * S), Image.NEAREST)
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, r in rows:
        d.text((4, y * S + 4), name.replace("fx_", ""), fill=(255, 255, 255, 255))
        y += r.height
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "fx3.png"))


ALL = [fx_moonwave, fx_stormleap, fx_bloodstep, fx_cinderblade, fx_warcry, fx_shards, fx_warmth,
       fx_lance, fx_rotmist, fx_rot_hit, fx_holy_burst, fx_petal]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    out = []
    for fn in ALL:
        if only and fn.__name__ not in only:
            continue
        frames = fn()
        out.append((fn.__name__, frames, list(frames[0]["cels"].keys())))
        print("built", fn.__name__, len(frames), "frames")
    if not only:          # a partial run would overwrite fx3.png with a partial sheet
        preview(out)
