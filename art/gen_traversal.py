#!/usr/bin/env python3
"""Traversal props & FX (grapple, Gale Cloak glide, ember dash, slam) -> art/*.aseprite, assets/*.png/.json

Same house style as gen_fx*.py: crisp colour bands, ordered (Bayer) falloff instead of blur, a few
alpha steps only for glows / translucent ash, >= 2 layers per sprite. Props use the tag `loop`;
FX use one tag named without the "fx_" prefix. Centered pivot unless noted "bottom".

  prop_hookpoint  16x16  loop(4)  golden root-ring anchor in stone, pulsing glow
  prop_ashveil    32x64  loop(6)  translucent wall of swirling ash + drifting embers (ember-dash gate)
  prop_updraft    16x64  loop(6)  column of rising pale wind streaks + ash motes (glide lift)
  fx_slam_impact  96x40  8        ground-shattering ember shockwave + rock chunks, pivot bottom
  fx_ember_dash   48x32  5        crimson-ember afterimage streak, trailing left
  fx_veil_burst   48x64  6        ash veil bursting apart as something passes through
  fx_gale         32x24  4 loop   small wind puffs / streaks

Re-runnable: python3 art/gen_traversal.py [--preview-only] [name ...]
"""
import os, sys, math, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from gen_fx import blank, put, bt, clean, breakup, rock, comp_frame, EMBER, DUST, ROCK  # noqa: E402
from gen_fx2 import A, CORE, G, CR, ASH, radial, spark, outline_img  # noqa: E402
from gen_fx3 import blob  # noqa: E402

TR = (0, 0, 0, 0)
K = A((8, 7, 12))
WIND = [A((58, 64, 88)), A((104, 118, 150)), A((166, 186, 214)), A((226, 236, 250))]
EMB = EMBER                    # dark -> white-hot: 7a2210 c8461a f07c28 ffb65a ffe2a0
TAU = 2 * math.pi


def al(c, a):
    return (c[0], c[1], c[2], a)


def out(name, w, h, layers, cels, ms, tag):
    return dict(name=name, w=w, h=h, layers=layers, frames=[{"ms": m, "cels": c} for m, c in zip(ms, cels)],
                tags=[(tag, 0, len(cels) - 1)])


# ================================================================ prop_hookpoint
def prop_hookpoint():
    """Golden root-ring anchor set in a knot of stone/bark; roots vein out of it; the ring pulses."""
    W = H = 16
    cx, cy = 8.0, 8.0
    base = blank(W, H)
    rnd = random.Random(3)
    rim = [6.6 + 0.6 * math.sin(a * 3 + 1) + 0.4 * math.sin(a * 5) for a in [i / 32 * TAU for i in range(32)]]
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx) % TAU
            if r > rim[int(a / TAU * 32) % 32]:
                continue
            v = -(dx + dy) / 9.0                               # lit from the upper-left
            i = 3 if v > 0.45 else (2 if v > -0.05 else (1 if v > -0.5 else 0))
            base.putpixel((x, y), ROCK[i])
    for x, y in ((3, 6), (4, 6), (12, 10), (11, 11), (6, 13), (5, 13), (10, 3)):   # cracks
        put(base, x, y, ROCK[0])
    base = outline_img(base, K)
    roots = [(math.radians(a), L) for a, L in ((205, 6.6), (320, 6.4), (95, 6.6))]
    cels = []
    for k, p in enumerate((0, 1, 2, 1)):
        glow, ring, sp = blank(W, H), blank(W, H), blank(W, H)
        # halo: gold light spilling onto the stone and 1px past its rim (alpha steps)
        for y in range(H):
            for x in range(W):
                r = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if 4.6 < r <= 5.6 and bt(x, y) < 0.25 + 0.3 * p:
                    glow.putpixel((x, y), al(G[3], 60 + 50 * p))
                elif 5.6 < r <= 7.9 and p >= 1 and bt(x, y) < 0.18 * p:
                    glow.putpixel((x, y), al(G[2], 70 + 40 * p))
        # the ring itself: gold annulus, bright upper-left, dark socket in the middle
        for y in range(H):
            for x in range(W):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                r = math.hypot(dx, dy)
                if r <= 1.9:
                    ring.putpixel((x, y), A((22, 16, 14)) if p < 2 else A((70, 40, 16)))
                elif 2.4 < r <= 4.1:
                    v = -(dx + dy) / r
                    i = 3 if v > 0.9 else (2 if v > -0.3 else 1)
                    if r < 3.1 and v > 0.3:
                        i -= 1                                  # inner lip in shadow (far side lit)
                    ring.putpixel((x, y), G[max(0, min(4, i + (1 if p == 2 else 0)))])
        ring = outline_img(ring, A((40, 22, 10)))
        # thin root veins running out of the ring into the stone (1px, brighten on the pulse)
        for a, L in roots:
            for j in range(7):
                t = 5.0 + j * (L - 5.0) / 6
                wob = 0.6 * math.sin(j * 1.3 + a * 3)
                x, y = cx - 0.5 + math.cos(a) * t - math.sin(a) * wob, cy - 0.5 + math.sin(a) * t + math.cos(a) * wob
                put(ring, x, y, G[1] if (j > 3 and p == 0) else G[2 if p < 2 or j > 3 else 3])
        # glint on the upper-left of the ring, flaring at the pulse peak
        gx, gy = 5, 5
        put(sp, gx, gy, CORE)
        if p >= 1:
            for d in (1,) if p == 1 else (1, 2):
                for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(sp, gx + sx * d, gy + sy * d, al(G[3], 255 if d == 1 else 150))
        cels.append({"Base": base, "Glow": glow, "Ring": ring, "Spark": sp})
    return out("prop_hookpoint", W, H, ["Base", "Glow", "Ring", "Spark"], cels, [140, 110, 150, 110], "loop")


# ================================================================ prop_ashveil
def prop_ashveil():
    """Translucent wall of ash swirling upward, embers drifting through it (crossable only by ember dash)."""
    W, H = 32, 64
    LV = [(0.2, al(ASH[0], 96)), (0.38, al(ASH[1], 132)), (0.56, al(ASH[2], 168)), (0.76, al(ASH[3], 200)),
          (0.92, A((190, 180, 184), 220))]
    embers = [(random.Random(i).uniform(6, 26), random.Random(i * 7 + 1).uniform(0, 36), i) for i in range(9)]
    cels = []
    for k in range(6):
        ph = TAU * k / 6
        back, swirl, emb = blank(W, H), blank(W, H), blank(W, H)
        for y in range(H):
            hw = 13.8 + 1.4 * math.sin(y * 0.19 + ph) + 1.0 * math.sin(y * 0.47 - 2 * ph)
            c = 16 + 1.2 * math.sin(y * 0.13 - ph)
            for x in range(W):
                e = abs(x + 0.5 - c) / hw
                if e >= 1:
                    continue
                env = 1 - e ** 5
                s = (0.5 + 0.22 * math.sin(0.42 * x + 0.24 * y + ph)
                     + 0.18 * math.sin(-0.33 * x + 0.35 * y + 2 * ph)
                     + 0.14 * math.sin(0.9 * (x - c) * math.cos(0.11 * y + ph) + 0.2 * y + ph))
                d = env * (0.5 + 0.55 * s)
                d += (bt(x, y) - 0.5) * 0.12                    # ordered dither between the bands
                col = None
                for th, cc in LV:
                    if d > th:
                        col = cc
                        lvl = th
                if col is None:
                    continue
                (swirl if lvl >= 0.56 else back).putpixel((x, y), col)
        # dim crimson smoulder deep inside the veil (the dash's colour)
        for y in range(H):
            for x in range(W):
                q = math.sin(0.5 * x - 0.3 * y + ph) + math.sin(0.27 * y + 0.2 * x - 2 * ph)
                if q > 1.55 and 9 < x < 23 and back.getpixel((x, y))[3]:
                    back.putpixel((x, y), A((120, 32, 30), 150))
        # embers rising 6px/frame on a 36px period (loops in 6 frames)
        for ex, ey, i in embers:
            for rep in (0, 36):
                y = (ey - 6 * k) % 36 + rep - 4
                x = ex + 1.5 * math.sin(ph + i)
                if 0 <= y < H:
                    put(emb, x, y, EMB[4] if i % 3 == 0 else EMB[3])
                    put(emb, x, y + 1, EMB[2])
                    if i % 2:
                        put(emb, x - (1 if math.sin(ph + i) > 0 else -1), y + 2, EMB[1])
        cels.append({"Back": back, "Swirl": swirl, "Embers": emb})
    return out("prop_ashveil", W, H, ["Back", "Swirl", "Embers"], cels, [110] * 6, "loop")


# ================================================================ prop_updraft
def prop_updraft():
    """Column of rising pale wind: faint haze, streaks rising 12px/frame (72px period), ash motes."""
    W, H = 16, 64
    streaks = [(4, 0, 12), (11, 18, 9), (7, 34, 14), (9, 52, 8), (5, 60, 10), (12, 44, 7), (8, 8, 9), (3, 28, 6),
               (13, 64, 8)]
    motes = [(3.5, 5), (12.5, 14), (8, 22), (5.5, 31), (10.5, 3), (7, 12)]
    cels = []
    for k in range(6):
        ph = TAU * k / 6
        haze, st, mo = blank(W, H), blank(W, H), blank(W, H)
        for y in range(H):
            for x in range(W):
                e = abs(x + 0.5 - 8 - 0.8 * math.sin(y * 0.15 + ph)) / 6.5
                if e > 1:
                    continue
                v = (1 - e * e) * (0.55 + 0.45 * math.sin(y * 0.3 + ph * 2 + x * 0.4))
                if v > 0.55 and bt(x, y + 2 * k) < 0.5:
                    haze.putpixel((x, y), al(WIND[2], 60))
                elif v > 0.25 and bt(x, y + 2 * k) < 0.22:
                    haze.putpixel((x, y), al(WIND[2], 40))
        for i, (x0, y0, L) in enumerate(streaks):
            top = (y0 - 12 * k) % 72 - 6
            for j in range(L):
                y = top + j
                x = x0 + 1.2 * math.sin(y * 0.2 + i)
                q = j / L
                c = al(WIND[3], 230) if q < 0.2 else (al(WIND[2], 170) if q < 0.6 else al(WIND[1], 110))
                if q > 0.75 and j % 2:
                    continue
                put(st, x, y, c)
                if q < 0.2 and i % 3 == 0:
                    put(st, x + 1, y + 1, al(WIND[2], 140))       # a few doubled, wider gusts
        for i, (x0, y0) in enumerate(motes):
            for rep in (0, 36):
                y = (y0 - 6 * k) % 36 + rep
                x = x0 + math.sin(ph + i * 2)
                put(mo, x, y, ASH[3] if i % 2 else ASH[2])
                if i % 3 == 0:
                    put(mo, x + 1, y, ASH[2])
        cels.append({"Haze": haze, "Streaks": st, "Motes": mo})
    return out("prop_updraft", W, H, ["Haze", "Streaks", "Motes"], cels, [100] * 6, "loop")


# ================================================================ fx_slam_impact
def fx_slam_impact():
    """Ember shockwave rolling out both ways from the impact (48, 39), fissures glowing along the
    floor, a flare column, rock chunks and sparks thrown up. Pivot bottom."""
    W, H = 96, 40
    GY, CX = 39, 48
    fronts = [5, 13, 21, 28, 34, 39, 43, 46]
    crest = [8, 11, 11, 10, 8, 6, 4, 2]
    rnd = random.Random(11)
    rocks = [(sd * rnd.uniform(0.8, 2.2), rnd.uniform(3.0, 4.4), rnd.randrange(4)) for sd in (-1, 1, -1, 1, 1, -1, 1, -1)]
    sparks = [(rnd.uniform(-2.6, 2.6), rnd.uniform(2.5, 5.0)) for _ in range(14)]
    fis = []
    for sd in (-1, 1):                                   # jagged fissure paths along the floor
        x, yv = CX, GY
        pts = []
        for i in range(40):
            x += sd
            if rnd.random() < 0.25:
                yv = GY - 1 if yv == GY else GY
            pts.append((x, yv, i))
        fis.append(pts)
    cels = []
    for k in range(8):
        glow, wave, crk, deb, core = (blank(W, H) for _ in range(5))
        dim = 0 if k < 3 else (1 if k < 5 else 2)
        # rolling crest both ways
        R, Hc = fronts[k], crest[k]
        for x in range(W):
            d = abs(x + 0.5 - CX)
            u = d - R
            if u > 1.5 or u < -13:
                continue
            h = (Hc * max(0.0, 1 - (u + 2) / 2.6) ** 0.5 if u > -2 else Hc * max(0.0, 1 + (u + 2) / 11) ** 1.4)
            h = int(round(h))
            for j in range(h):
                y = GY - j
                t = j / max(1, h)
                top = j >= h - 1
                if top:
                    i = 4 if u > -4 else 3
                elif u > -2.5:
                    i = 4 if t > 0.3 else 3
                else:
                    i = 2 if t < 0.5 else 3
                    if (y + x // 3 + k) % 4 == 0:
                        i += 1
                i -= dim
                if i < 0:
                    continue
                (wave if i >= 3 else glow).putpixel((x, y), EMB[i])
            if dim < 2 and h and bt(x, GY - h) < 0.5:
                glow.putpixel((x, GY - h), al(EMB[1], 170))
        if k >= 4:
            breakup(glow, 0.75 if k < 6 else 0.5, 70 + k)
            breakup(wave, 0.8 if k < 6 else 0.55, 90 + k)
        # glowing fissures along the floor, reaching out with the wave, cooling down
        for pts in fis:
            for x, y, i in pts:
                if i > fronts[k] + 2:
                    break
                heat = 4 - dim - (1 if i > 28 else 0) - (1 if k >= 6 else 0)
                if heat >= 1:
                    put(crk, x, y, EMB[heat])
                    if i % 7 == 3 and heat >= 2:
                        put(crk, x, y - 1, EMB[heat - 1])
        # impact flare column + core burst (first frames)
        if k < 3:
            rr = [10, 7, 4][k]
            radial(core, CX, GY - 2, rr, [EMB[1], EMB[2], EMB[3], EMB[4], CORE])
            hgt = [24, 30, 18][k]
            for j in range(hgt):
                w = (3 - k * 0.8) * (1 - j / hgt) ** 0.6
                for x in range(int(CX - w - 1), int(CX + w + 1)):
                    if abs(x + 0.5 - CX) <= w:
                        q = abs(x + 0.5 - CX) / max(w, 0.1)
                        c = CORE if q < 0.35 and j < hgt * 0.7 else (EMB[3] if q < 0.7 else EMB[2])
                        if j > hgt * 0.75 and bt(x, j) < 0.5:
                            continue
                        put(core, x, GY - j, c)
        # rock chunks in parabolas, glowing undersides early
        t = (k + 1) * 0.85
        for i, (vx, vy, sh) in enumerate(rocks):
            x = CX + vx * t * 3.3
            y = GY - 3 - (vy * t * 3.0 - t * t * 1.7)
            if y > GY - 2 or not (0 <= x < W - 3):
                continue
            rock(deb, x, y, sh, (k + i) % 2 == 1, glow=k < 4)
        # sparks
        for i, (vx, vy) in enumerate(sparks):
            tt = (k + 0.5) * 0.8
            x = CX + vx * tt * 4
            y = GY - 2 - (vy * tt * 3.2 - tt * tt * 1.4)
            if y < GY and k < 7 and (i + k) % 4:
                spark(deb, x, y, vx, -(vy - tt * 0.9), EMB[4] if k < 3 else EMB[3], EMB[2], n=2 if k < 4 else 1)
        # dust puffs kicked up behind the crest
        if 2 <= k:
            for sd in (-1, 1):
                for j, off in enumerate((0.55, 0.8)):
                    bx = CX + sd * fronts[k] * off
                    r = 1.6 + 0.35 * (k - 2) + j * 0.5
                    blob(deb, bx, GY - r * 0.8, r * 1.3, r, [DUST[0], DUST[1], DUST[2], DUST[3]], soft=0.3 + 0.08 * k)
            if k >= 5:
                breakup(deb, 0.8 if k < 7 else 0.6, 30 + k)
        cels.append({"Glow": clean(glow, ref=(wave,)), "Cracks": crk, "Wave": clean(wave, ref=(glow,)),
                     "Debris": deb, "Core": core})
    return out("fx_slam_impact", W, H, ["Glow", "Cracks", "Wave", "Debris", "Core"], cels,
               [40, 50, 60, 60, 70, 80, 90, 100], "slam_impact")


# ================================================================ fx_ember_dash
def _dash_mask():
    """Silhouette of the player's ember_dash stretch frame (so the afterimage matches the body)."""
    import gen_player as gp
    cels, _ = gp.ember_dash()[2]
    body = gp.compose(gp.imgs({k: v for k, v in cels.items() if k != "Item"}, None))
    bb = body.getbbox()
    m = body.crop(bb)
    return m, bb


def fx_ember_dash():
    """Crimson-ember afterimage: a ghost of the dashing knight smeared into a streak trailing left."""
    W, H = 48, 32
    mask, _ = _dash_mask()
    mw, mh = mask.size
    mp = mask.load()
    solid = {(x, y) for y in range(mh) for x in range(mw) if mp[x, y][3]}
    oy = H - 2 - mh                                        # ghost sits low in the frame (feet ~ row 30)
    rnd = random.Random(5)
    cels = []
    ghosts = [[(40, 255)], [(37, 230), (31, 130)], [(34, 170), (27, 100)], [(31, 110)], []]
    streak_len = [22, 34, 40, 30, 16]
    for k in range(5):
        st, gh, em = blank(W, H), blank(W, H), blank(W, H)
        # ghosts: right edge of the silhouette sits at ex, interior crimson, leading rim hot
        for gi, (ex, a) in enumerate(ghosts[k]):
            ox = ex - mw
            for (x, y) in solid:
                X, Y = ox + x, oy + y
                if not (0 <= X < W and 0 <= Y < H):
                    continue
                lead = (x + 1, y) not in solid
                top = (x, y - 1) not in solid
                aa = a
                if lead:
                    c = EMB[4] if (gi == 0 and k < 2) else CR[3]
                elif top:
                    c = CR[3] if gi == 0 else CR[2]
                else:
                    c = CR[2] if (y % 3 == 0 and x > mw * 0.4) else CR[1]
                    aa = int(a * 0.5)
                if k >= 3 and bt(X, Y) > (0.7 if k == 3 else 0.4):
                    continue
                gh.putpixel((X, Y), al(c, aa))
            # smear: every row's trailing edge stretches back into a streak
            for y in range(mh):
                xs = [x for x in range(mw) if (x, y) in solid]
                if not xs or y % 2:
                    continue
                x0 = ox + xs[0]
                n = int(streak_len[k] * (0.4 + 0.6 * ((y * 7 + gi * 3) % 5) / 4) * (0.6 if gi else 1.0))
                for i in range(n):
                    X = x0 - 1 - i
                    q = i / max(1, n)
                    if X < 0 or (q > 0.55 and (i + y) % 2):
                        continue
                    c = CR[3] if q < 0.2 and gi == 0 else (CR[2] if q < 0.5 else CR[1])
                    st.putpixel((X, oy + y), al(c, int(a * (1 - 0.5 * q))))
        # a hot core line through the body height on the first frames
        if k < 3:
            cy = oy + mh // 2
            for x in range(max(0, 40 - streak_len[k] - 8), 44 - 3 * k):
                q = (44 - 3 * k - x) / (streak_len[k] + 8)
                if q < 0.9 or x % 2:
                    put(st, x, cy, CORE if q < 0.3 and k == 0 else (EMB[4] if q < 0.55 else EMB[3]))
                    if q < 0.5:
                        put(st, x, cy + 1, EMB[2])
        # embers peeling off, drifting up and back
        for i in range(12 if k < 4 else 7):
            h = random.Random(i * 31 + 7)
            bx, by = h.uniform(8, 40), h.uniform(oy + 2, H - 3)
            x = bx - k * h.uniform(2, 4)
            y = by - k * h.uniform(0.8, 2.0)
            if k == 0 and bx < 28:
                continue
            if 0 <= x < W and 0 <= y < H:
                put(em, x, y, EMB[4] if i % 3 == 0 else (EMB[3] if i % 3 == 1 else CR[2]))
                if i % 2 and k < 4:
                    put(em, x + 1, y, EMB[2])
        cels.append({"Streak": st, "Ghost": gh, "Embers": em})
    return out("fx_ember_dash", W, H, ["Streak", "Ghost", "Embers"], cels, [40, 50, 60, 70, 80], "ember_dash")


# ================================================================ fx_veil_burst
def fx_veil_burst():
    """The ash veil blown apart around a body passing through at (24, 44): crimson-ember flash, a ring
    tearing open, ash puffs thrown left/right (hardest at the hole), cinders, dispersal."""
    W, H = 48, 64
    CX, CY = 24, 44
    rnd = random.Random(9)
    puffs = []
    for i in range(36):
        y0 = rnd.uniform(3, 61)
        sd = -1 if i % 2 else 1
        near = math.exp(-((y0 - CY) / 14.0) ** 2)
        puffs.append((y0, sd, 0.5 + 3.2 * near + rnd.uniform(0, 0.8), rnd.uniform(2.2, 3.6), rnd.uniform(-6, 6)))
    ash_r = [A((52, 48, 58), 210), A((78, 72, 84), 210), A((112, 106, 116), 220), A((150, 143, 150), 230)]
    cels = []
    for k in range(6):
        back, ash, flash, cind = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        t = k + 0.6
        # ash puffs: drift outward (easing), grow, fade (ordered breakup)
        for (y0, sd, v, r0, jx) in puffs:
            x = CX + jx * 0.5 + sd * v * (1 - math.exp(-t * 0.55)) * 5.0
            y = y0 - 0.5 * t
            r = r0 + 0.45 * t
            blob(ash if r0 > 2.9 else back, x, y, r * 1.25, r, ash_r, soft=min(0.9, 0.25 + 0.12 * k))
        if k >= 3:
            breakup(ash, [0.8, 0.6, 0.4][k - 3], 40 + k)
            breakup(back, [0.7, 0.5, 0.3][k - 3], 50 + k)
        # the tearing ring and flash where the body punched through
        if k < 4:
            rx, ry = [4, 8, 11, 13][k], [6, 10, 13, 15][k]
            wth = [3.0, 2.2, 1.6, 1.0][k]
            for y in range(H):
                for x in range(W):
                    ux, uy = (x + 0.5 - CX) / rx, (y + 0.5 - CY) / ry
                    d = math.hypot(ux, uy)
                    dd = (1 - d) * min(rx, ry)
                    if 0 <= dd <= wth:
                        if k >= 2 and bt(x, y) < 0.35 * (k - 1):
                            continue
                        c = [CORE, EMB[3], CR[2], CR[1]][min(3, k + (1 if dd > wth * 0.6 else 0))]
                        flash.putpixel((x, y), c)
            if k == 0:
                radial(flash, CX, CY, 5, [CR[1], CR[2], EMB[3], CORE])
        # cinders flung out with the ash
        for i in range(16):
            h = random.Random(i * 13 + 3)
            ang = h.uniform(-0.7, 0.7) + (math.pi if i % 2 else 0)
            sp = h.uniform(3, 6)
            x = CX + math.cos(ang) * sp * t
            y = CY + math.sin(ang) * sp * t * 0.6 - 0.4 * t * t * 0.3 + h.uniform(-10, 10)
            if 0 <= x < W and 0 <= y < H and k < 5 and (i + k) % 3:
                spark(cind, x, y, math.cos(ang), math.sin(ang) * 0.6, EMB[4] if k < 2 else EMB[3], CR[2], n=2 if k < 3 else 1)
        cels.append({"Back": back, "Ash": ash, "Flash": flash, "Cinders": cind})
    return out("fx_veil_burst", W, H, ["Back", "Ash", "Flash", "Cinders"], cels, [50, 60, 70, 80, 90, 100], "veil_burst")


# ================================================================ fx_gale
def fx_gale():
    """Small wind curls streaming back (left) off the Gale Cloak: 8px/frame over a 32px loop, faded
    at the frame edges so nothing pops."""
    W, H = 32, 24
    streaks = [(4, 0, 13, 1), (11, 12, 10, -1), (18, 22, 12, 1), (8, 20, 6, 0), (15, 5, 7, 0)]
    cels = []
    for k in range(4):
        back, front = blank(W, H), blank(W, H)
        for i, (y0, x0, L, curl) in enumerate(streaks):
            head = (x0 - 8 * k) % 32 + 8                     # head x (0..40), tail trails to the right
            for j in range(L):
                x = head + j
                y = y0 + 0.8 * math.sin((x + i * 5) * 0.35)
                env = min(1.0, (x - 0) / 6, (W - 1 - x) / 6)
                if env <= 0:
                    continue
                q = j / L
                a = int((230 if q < 0.3 else (170 if q < 0.7 else 110)) * env)
                if a < 40 or (q > 0.7 and j % 2):
                    continue
                put(front if q < 0.5 else back, x, y, al(WIND[3] if q < 0.3 else WIND[2], a))
            if curl:                                          # the leading end curls into a hook
                env = min(1.0, head / 6, (W - 1 - head) / 6)
                if env > 0.3:
                    for dx, dy in ((-1, -curl), (-1, -2 * curl), (0, -3 * curl + (1 if curl < 0 else 0)), (1, -3 * curl)):
                        put(front, head + dx, y0 + dy, al(WIND[3], int(220 * env)))
        # soft puffs
        for i, (px, py) in enumerate(((6, 16), (22, 7))):
            x = (px - 8 * k) % 32
            env = min(1.0, x / 6, (W - 1 - x) / 6)
            if env > 0.3:
                blob(back, x, py, 2.2, 1.6, [al(WIND[0], int(90 * env)), al(WIND[1], int(110 * env)),
                                             al(WIND[2], int(130 * env)), al(WIND[3], int(150 * env))], soft=0.4)
        cels.append({"Puffs": back, "Streaks": front})
    return out("fx_gale", W, H, ["Puffs", "Streaks"], cels, [90] * 4, "gale")


# ================================================================ preview
BG = (92, 92, 100, 255)
CELL_BG = (44, 42, 54, 255)
ALL = [prop_hookpoint, prop_ashveil, prop_updraft, fx_slam_impact, fx_ember_dash, fx_veil_burst, fx_gale]


def preview(sprites, S=3):
    """Every sprite's tag as a row (frames left->right) on dark cells over mid-grey, 3x, labelled."""
    rows = []
    for sp in sprites:
        w, h = sp["w"], sp["h"]
        for tag, a, b in sp["tags"]:
            strip = Image.new("RGBA", ((b - a + 1) * (w + 2) + 2, h + 4), BG)
            for i in range(a, b + 1):
                cell = Image.new("RGBA", (w, h), CELL_BG)
                cell.alpha_composite(comp_frame(sp["frames"][i], sp["layers"]))
                strip.paste(cell, (2 + (i - a) * (w + 2), 2))
            rows.append((f"{sp['name']}:{tag}", strip))
    LBL = 40
    Wt = max(r.width for _, r in rows) + LBL
    Ht = sum(r.height for _, r in rows)
    sheet = Image.new("RGBA", (Wt, Ht), BG)
    y = 0
    for _, r in rows:
        sheet.paste(r, (LBL, y))
        y += r.height
    sheet = sheet.resize((Wt * S, Ht * S), Image.NEAREST)
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, r in rows:
        n, t = name.split(":")
        d.text((4, y * S + 4), n.replace("prop_", "").replace("fx_", ""), fill=(255, 255, 255, 255))
        d.text((4, y * S + 18), t, fill=(200, 200, 210, 255))
        y += r.height
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "traversal.png"))


def main():
    build = "--preview-only" not in sys.argv
    only = {a for a in sys.argv[1:] if not a.startswith("--")}
    sprites = []
    for fn in ALL:
        sp = fn()
        sprites.append(sp)
        if build and (not only or sp["name"] in only):
            asebuild.build(sp["name"], sp["w"], sp["h"], sp["layers"], sp["frames"], sp["tags"])
            print("built", sp["name"], len(sp["frames"]), sp["tags"])
    preview(sprites)


if __name__ == "__main__":
    main()
