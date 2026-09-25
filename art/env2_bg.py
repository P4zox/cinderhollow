"""Parallax backgrounds for the v2 biomes (docs/ART_SPEC2.md section F).

bg_mire_far / bg_crown_far : 512x216 opaque, horizontally tileable (period 512)
bg_mire_mid / bg_crown_mid : 512x216 transparent except silhouettes (mostly lower 2/3), tileable

Built the same way as env_bg.py (wrapping Canvas, tileable value noise, ordered dithering,
recursive limb trees, 1px rim light on the sky-facing edges, haze toward the bottom).
"""
import math, random
from envlib import C, ramp, T, K, bt, pick, pick_i, h01, smooth, clamp, Canvas
from env_bg import limb_tree, raster_segs, haze_toward, tn, wrapdx
from envlib import fbm

W, H = 512, 216


def rect(cv, x0, x1, y0, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            cv.set(x, y, c)


def rim_pass(cv, bodies, top_c, left_c, right_c=None, right_p=0.0, skip=()):
    """1px rim light on the sky-facing edges of silhouette pixels whose colour is in `bodies`."""
    px = cv.img.load()
    hits = []
    for y in range(1, H):
        for x in range(W):
            c = px[x, y]
            if c not in bodies:
                continue
            up, lf, rt = px[x, y - 1], px[(x - 1) % W, y], px[(x + 1) % W, y]
            if up[3] == 0 or up in skip:
                hits.append((x, y, top_c))
            elif lf[3] == 0 or lf in skip:
                hits.append((x, y, left_c))
            elif right_c and (rt[3] == 0) and h01(x, y, 5) < right_p:
                hits.append((x, y, right_c))
    for (x, y, c) in hits:
        px[x, y] = c


def shade_limbs(segs, light=(0.6, 0.8)):
    """Rasterise limb segments -> {(x, y): (w, v)}; v in 0..1 = lambert-ish light from upper-left
    (thicker limbs win where they overlap so twigs never paint over trunks)."""
    out = {}
    for (x0, y0, x1, y1, w) in segs:
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        r = max(0.5, w / 2)
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for yy in range(int(y - r) - 1, int(y + r) + 2):
                for xx in range(int(x - r) - 1, int(x + r) + 2):
                    d2 = (xx - x) ** 2 + (yy - y) ** 2
                    if d2 > r * r + 0.25:
                        continue
                    ox, oy = (xx - x) / r, (yy - y) / r
                    v = 0.5 - 0.5 * (ox * light[0] + oy * light[1])
                    k = (xx % W, yy)
                    pw, pv = out.get(k, (0, 0))
                    if w > pw + 0.01 or (abs(w - pw) <= 0.01 and v > pv):
                        out[k] = (w, v)
    return out


def leaf_clump(cv, cx, cy, r, ramp_, seed, bias=0.0, squash=0.7):
    """Irregular clump of foliage/blossom, lit from the upper-left, dithered edge."""
    for yy in range(int(cy - r) - 1, int(cy + r) + 2):
        for xx in range(int(cx - r * 1.5) - 1, int(cx + r * 1.5) + 2):
            dx, dy = (xx - cx) / (r * 1.5), (yy - cy) / (r * squash * 1.4)
            f = 1 - dx * dx - dy * dy + 0.55 * (tn(xx, yy, 4, 4, seed) - 0.5) + 0.3 * (tn(xx, yy, 2, 2, seed + 1) - 0.5)
            if f > 0.05:
                v = 0.5 - 0.45 * (dx * 0.6 + dy * 0.8) + 0.25 * f + bias
                cv.set(xx, yy, pick(ramp_, v, xx, yy))


# =========================================================================== MIRE
M_SKY = ramp("080d0c", "0b1210", "0f1714", "131c18", "17221c", "1c2821", "212f26", "27362b", "2e3d30",
             "364535", "404d3a", "4b5640", "576047", "656a4e", "757656", "88865e")
M_WAT = ramp("050a0a", "081010", "0b1515", "0f1b1a", "13221f", "182a26", "1e332d", "263d35")
M_WISP = ramp("6a2a0c", "c0561a", "ff9a3a", "ffd890")
MOON = (338, 58)


def m_sky_v(x, y):
    v = 0.10 + 0.55 * smooth(0, 150, y) ** 1.2
    dx, dy = wrapdx(x, MOON[0]) / 150.0, (y - MOON[1] - 20) / 90.0
    d = math.sqrt(dx * dx + dy * dy)
    v += 0.28 * max(0.0, 1 - d) ** 2
    return v


def dead_tree_px(rnd, x, y, h, w, depth=3, lean=0.0, spread=(0.35, 0.85)):
    segs = limb_tree(rnd, x, y, math.radians(90 + lean), h, w, depth, lean * -0.002, [],
                     spread=spread, shrink=(0.5, 0.72), step=2.5, twig=True)
    return raster_segs(segs), segs


def build_mire_far():
    cv = Canvas(W, H, wrap=True)
    # 1) murky sky, veiled sickly moon
    for y in range(H):
        for x in range(W):
            cv.set(x, y, pick(M_SKY, m_sky_v(x, y), x, y))
    for y in range(MOON[1] - 10, MOON[1] + 11):
        for x in range(MOON[0] - 10, MOON[0] + 11):
            d = math.hypot(x - MOON[0], y - MOON[1])
            if d <= 9.2:
                v = 0.86 + 0.12 * (1 - d / 9.2) - (0.05 if tn(x, y, 4, 4, 7) > 0.6 else 0)
                cv.set(x, y, pick(M_SKY, v, x, y))
    # 2) long fog streaks (drifting stratus), lit near the moon
    for y in range(20, 150):
        for x in range(W):
            n = fbm(x, y, 128, 5, 40) * 0.7 + tn(x, y, 32, 2, 41) * 0.3
            f = n + 0.2 * math.sin(y * 0.21 + fbm(x, 0, 256, 1, 42) * 5) - 0.63
            if f > 0 and f * 12 > bt(x, y):
                cv.set(x, y, pick(M_SKY, m_sky_v(x, y) + 0.09 + 0.2 * f, x, y))
    # 3) far dead-tree line on the horizon (very hazy), several depths
    rnd = random.Random(77)
    HZ = 150
    for (count, hmin, hmax, wd, val, base) in ((26, 10, 22, 1.8, 0.50, HZ - 2), (14, 18, 34, 2.6, 0.38, HZ + 2)):
        for i in range(count):
            x0 = (i + rnd.random() * 0.8) * W / count
            pxs, _ = dead_tree_px(rnd, x0, base, rnd.uniform(hmin, hmax), wd, 2, rnd.uniform(-8, 8))
            for (x, y), (w, core) in pxs.items():
                if y < base + 1:
                    cv.set(x, y, pick(M_SKY, val - 0.04 * smooth(80, 150, y), x, y))
        for x in range(W):          # the wooded shore under them
            top = base - 3 - 3 * tn(x, 0, 16, 1, 50 + count)
            for y in range(int(top), HZ + 8):
                cv.set(x, y, pick(M_SKY, val - 0.02, x, y))
    # 4) murky water with reflections of the sky/trees, ripples
    WL = HZ + 6
    for y in range(WL, H):
        for x in range(W):
            my = 2 * WL - y - 1
            rip = int(2.0 * math.sin(y * 0.8 + x * 0.04))
            src = cv.get(x + rip, my)
            i = M_SKY.index(src) if src in M_SKY else 4
            v = 0.22 + i / (len(M_SKY) - 1) * 0.45 - 0.14 * smooth(WL, H, y)
            c = pick(M_WAT, v, x, y)
            if (y - WL) % 4 == 1 and h01(x // 7, y, 60) < 0.35:
                c = M_WAT[min(7, M_WAT.index(c) + 2)]      # ripple glints
            cv.set(x, y, c)
    for x in range(W):
        cv.set(x, WL, M_SKY[9] if h01(x // 3, 0, 61) < 0.5 else M_SKY[8])
    # 5) low fog bank lying on the water line
    for y in range(HZ - 14, HZ + 26):
        for x in range(W):
            n = fbm(x, y, 64, 6, 62)
            a = smooth(HZ - 14, HZ + 2, y) * (1 - smooth(HZ + 8, HZ + 26, y)) * (0.5 + n)
            if a > 0.35 + 0.5 * bt(x, y):
                cv.set(x, y, pick(M_SKY, 0.62 + 0.1 * n, x, y))
    # 6) mid-distance islets with bigger dead trees (darker)
    for (cx, hw) in ((70, 38), (230, 26), (446, 44)):
        for x in range(cx - hw, cx + hw):
            t = 1 - ((x - cx) / hw) ** 2
            top = WL + 2 - 7 * t ** 0.6 - 2 * tn(x, 0, 8, 1, 63)
            for y in range(int(top), WL + 4):
                cv.set(x, y, M_SKY[3] if y > top else M_SKY[5])
        for k in range(2):
            pxs, _ = dead_tree_px(rnd, cx + (k * 2 - 1) * hw * 0.35, WL - 3, rnd.uniform(34, 50), 3.4, 3,
                                  rnd.uniform(-10, 10))
            for (x, y), (w, core) in pxs.items():
                if y < WL:
                    cv.set(x, y, M_SKY[4] if core else M_SKY[5])
    # 7) will-o'-wisps (rot glow) + their reflections
    for (x, y) in ((40, 140), (180, 146), (262, 132), (390, 143), (470, 138)):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if abs(dx) + abs(dy) == 1:
                    cv.set(x + dx, y + dy, M_WISP[1])
        cv.set(x, y, M_WISP[3])
        ry = 2 * WL - y
        if ry < H:
            cv.set(x, ry, M_WISP[1])
            cv.set(x, ry + 2, M_WISP[0])
    # 8) drifting spores
    rnd = random.Random(9)
    for _ in range(60):
        x, y = rnd.randrange(W), rnd.randrange(30, 150)
        cv.set(x, y, M_SKY[12] if rnd.random() < 0.7 else M_WISP[1])
    return cv.img


# ---------------------------------------------------------------------------- mire mid
M_SIL = ramp("070a09", "0b100e", "0f1512", "141b17", "19221c", "1f2921")
M_RIMC = ramp("2c3c2e", "3c5038", "516a44")
M_MOSSC = ramp("0e1a10", "142414", "1c301a")
M_FOGMAP = {M_SIL[0]: M_SIL[1], M_SIL[1]: M_SIL[2], M_SIL[2]: M_SIL[3], M_SIL[3]: M_SIL[4], M_SIL[4]: M_SIL[5],
            M_MOSSC[0]: M_SIL[3], M_MOSSC[1]: M_SIL[4], M_MOSSC[2]: M_SIL[5],
            M_RIMC[0]: M_SIL[5], M_RIMC[1]: M_RIMC[0], M_RIMC[2]: M_RIMC[1]}


def build_mire_mid():
    cv = Canvas(W, H, wrap=True)
    body, shade, dark = M_SIL[2], M_SIL[1], M_SIL[0]
    rnd = random.Random(314)
    GROUND = 196

    # ---- far row: hazy stumps and snags (lighter)
    for (x0, h, w) in ((20, 40, 5), (120, 28, 4), (196, 52, 6), (330, 34, 4), (380, 22, 7), (476, 46, 5)):
        for y in range(GROUND - h, H):
            hw = w / 2 + (y - (GROUND - h)) * 0.03
            for x in range(int(x0 - hw), int(x0 + hw) + 1):
                cv.set(x, y, M_SIL[4])
        for k in range(int(h01(x0, 0, 1) * 5) + 3):      # splintered top
            cv.set(x0 - w // 2 + k, GROUND - h - int(h01(x0, k, 2) * 5), M_SIL[4])

    # ---- great dead trees with moss beards
    trees = [(64, 150, 20, 3, -6), (262, 132, 16, 3, 8), (410, 160, 22, 3, -3)]
    mosspts = []
    for (tx, th, tw, dep, lean) in trees:
        segs = limb_tree(rnd, tx, H + 4, math.radians(90 + lean), th * 0.55, tw, dep, 0.0, [],
                         spread=(0.45, 0.95), shrink=(0.55, 0.72), step=2.5, twig=True, grav=0.0)
        pxs = raster_segs(segs)
        for (x, y), (w, core) in pxs.items():
            if y < 0:
                continue
            c = body
            if w > 5 and core and (h01(x // 1, y // 4, 3) < 0.35):
                c = shade                                  # bark furrows on the trunk
            if w > 5 and (x - tx) > w * 0.15 and core:
                c = shade if c == body else dark
            cv.set(x, y, c)
        # root flare at the base
        for y in range(GROUND - 14, H):
            t = (y - (GROUND - 14)) / 34
            hw = tw / 2 + 12 * t ** 1.6
            for x in range(int(tx - hw), int(tx + hw) + 1):
                cv.set(x, y, body if x < tx + hw * 0.3 else shade)
        for (x0, y0, x1, y1, w) in segs:
            if 1.2 < w < 5.5 and rnd.random() < 0.22:
                mosspts.append((x0, y0, w))
    # hanging moss beards (Spanish moss) from the limbs
    for (x0, y0, w) in mosspts:
        L = rnd.randint(8, 26)
        for s in range(-1, 2):
            for k in range(L - abs(s) * 5):
                x = x0 + s * 1.5 + math.sin(k * 0.25 + x0) * 1.2
                cv.set(x, y0 + w / 2 + k, M_MOSSC[1] if k < L * 0.6 else M_MOSSC[0])
    # ---- broken stilt boardwalk
    BW = 168
    for x in range(300, 372):
        sag = int(3 * math.sin((x - 300) / 72 * math.pi))
        if 340 <= x <= 346:
            continue                                      # broken gap
        y = BW + sag + (int((x - 346) * 0.25) if x > 346 else 0)
        rect(cv, x, x, y, y + 2, body)
        if x % 6 == 0:
            cv.set(x, y + 1, shade)
    for px_ in (302, 322, 352, 369):
        top = BW - 4 + int(h01(px_, 0, 5) * 4)
        for y in range(top, H):
            cv.set(px_, y, body)
            cv.set(px_ + 1, y, shade)
        cv.set(px_ + 2, top + 6, M_SIL[3])               # rope wrap
    # a lantern post with a dead rot-lamp
    for y in range(BW - 30, BW):
        cv.set(318, y, body)
    for x in range(318, 326):
        cv.set(x, BW - 30, body)
    for y in range(BW - 29, BW - 22):
        cv.set(325, y, dark)
    # ---- sunken ruin: a half-drowned stone arch
    ax, ar = 150, 20
    for y in range(GROUND - 58, H):
        for x in range(ax - ar - 7, ax + ar + 8):
            d = math.hypot(x - ax, y - (GROUND - 30))
            inside = abs(x - ax) <= ar and (y >= GROUND - 30 or d <= ar)
            if not inside and (d <= ar + 7 or y >= GROUND - 30) and abs(x - ax) <= ar + 7:
                if y < GROUND - 58 + int(h01(x // 3, 0, 9) * 14) and x > ax + 4:
                    continue                              # broken right shoulder
                cv.set(x, y, M_SIL[3] if abs(d - ar - 3.5) < 0.6 and y < GROUND - 30 else body)
    # ---- peat bank + reeds along the bottom
    for x in range(W):
        top = GROUND + int(5 * (tn(x, 5, 32, 1, 11) - 0.5)) + int(3 * tn(x, 6, 8, 1, 12))
        rect(cv, x, x, top, H - 1, shade)
    # ---- rim light from the fog glow (top / left edges)
    rim_pass(cv, (body, shade, M_SIL[3], M_SIL[4]), M_RIMC[1], M_RIMC[0])
    # reeds after the rim pass so the thin blades stay dark silhouettes (tips catch a little light)
    for i in range(90):
        x0 = rnd.randrange(W)
        h = rnd.randint(8, 22)
        lean = rnd.uniform(-0.25, 0.25)
        for k in range(h):
            cv.set(x0 + lean * k, GROUND + 2 - k, shade if k < h - 2 else M_SIL[3])
        if rnd.random() < 0.3:
            for k in range(3):
                cv.set(x0 + lean * h, GROUND + 2 - h - k, body)
    # moss beards get their own dim green tips lit
    # ---- rot-orange fungus clusters glowing on the trunks and ruin
    for (x, y) in ((70, 150), (58, 118), (268, 160), (256, 128), (414, 170), (420, 140), (160, 176), (366, 176)):
        for (dx, dy, c) in ((0, 0, 3), (1, 0, 2), (-1, 1, 1), (0, 1, 2), (1, 1, 1), (2, 2, 2), (3, 2, 1),
                            (-2, 3, 2), (-1, 3, 1)):
            cv.set(x + dx, y + dy, M_WISP[c])
    haze_toward(cv, 150, 226, M_FOGMAP, 1.0)
    return cv.img


# =========================================================================== CROWN
S_SKY = ramp("56689a", "5e72a4", "687cac", "7388b4", "8094bc", "8ea0c4", "9cacca", "acb8d0", "bcc4d6",
             "cad0da", "d8dade", "e4e2de", "eee8dc", "f6eedc", "fcf4e2", "fffaec")
S_CLOUD = ramp("8c90b8", "a0a2c4", "b4b4cc", "c8c6d4", "dcd8dc", "ece6e0", "f8f2e6", "fffcf0")
S_BR = ramp("8c90b0", "9a9cba", "a8a8c2", "b8b4c8", "c8c0cc", "d6ccce", "e2d6cc", "eee0cc", "f8ecd4")
S_GOLD = ramp("c8ac86", "dcc096", "ead2a6", "f6e4bc", "fff4d8")
SUN = (132, 64)


def s_sky_v(x, y):
    v = 0.05 + 0.80 * smooth(-10, 175, y) ** 1.15
    dx, dy = wrapdx(x, SUN[0]) / 160.0, (y - SUN[1]) / 100.0
    d = math.sqrt(dx * dx + dy * dy)
    v += 0.35 * max(0.0, 1 - d) ** 2.2
    return v


def cumulus(cv, cx, cy, rw, rh, seed, ramp_, lit_bias=0.0, floor=None):
    """Billowy cloud: union of noisy blobs, lit from the upper-left / sun."""
    rnd = random.Random(seed)
    blobs = [(cx, cy, rw * 0.5, rh)]
    for i in range(9):
        bx = cx + rnd.uniform(-1, 1) * rw * 0.8
        by = cy + rnd.uniform(-0.6, 0.5) * rh
        blobs.append((bx, by, rnd.uniform(0.25, 0.45) * rw, rnd.uniform(0.5, 0.9) * rh))
    x0, x1 = int(cx - rw * 1.4), int(cx + rw * 1.4)
    y0, y1 = int(cy - rh * 1.8), int(cy + rh * 1.2)
    base = floor if floor is not None else cy + rh * 0.55
    for y in range(y0, y1):
        if y > base:
            continue
        for x in range(x0, x1):
            best = -1.0
            nl = 0
            for (bx, by, brx, bry) in blobs:
                dx, dy = (x - bx) / brx, (y - by) / bry
                f = 1 - (dx * dx + dy * dy)
                if f > best:
                    best, nl = f, -(dx * 0.6 + dy * 0.8)
            if best < -0.15:
                continue
            best += 0.25 * (tn(x, y, 8, 8, seed) - 0.5)
            if best <= 0:
                continue
            v = 0.55 + 0.35 * nl + 0.25 * best + lit_bias - 0.35 * smooth(base - rh * 0.8, base, y)
            cv.set(x, y, pick(ramp_, v, x, y))


def build_crown_far():
    cv = Canvas(W, H, wrap=True)
    # 1) luminous sky
    for y in range(H):
        for x in range(W):
            v = s_sky_v(x, y)
            ang = math.atan2(y - SUN[1], wrapdx(x, SUN[0]))
            ray = 0.5 + 0.5 * math.sin(ang * 19 + 0.7)
            v += 0.04 * ray * smooth(10, 40, math.hypot(wrapdx(x, SUN[0]), y - SUN[1])) * \
                max(0, 1 - math.hypot(wrapdx(x, SUN[0]), y - SUN[1]) / 230)
            cv.set(x, y, pick(S_SKY, v, x, y))
    # thin cirrus streaks
    for y in range(8, 90):
        for x in range(W):
            n = fbm(x, y, 128, 3, 70) * 0.6 + tn(x, y, 64, 2, 71) * 0.4
            f = n + 0.25 * math.sin(y * 0.35 + x * 0.02 + fbm(x, 0, 256, 1, 72) * 4) - 0.72
            if f > 0 and f * 10 > bt(x, y):
                cv.set(x, y, pick(S_SKY, s_sky_v(x, y) + 0.10, x, y))
    # 2) enormous distant branches of the fallen Root, rising out of the cloud sea, hazed into the sky
    rnd = random.Random(2024)
    for (bx, ang, ln, wd, haze, seed) in ((58, 72, 120, 30, 0.10, 1), (330, 100, 150, 38, 0.0, 2),
                                          (470, 86, 70, 16, 0.22, 3)):
        segs = limb_tree(rnd, bx, H + 30, math.radians(ang), ln, wd, 3, (-0.006 if ang < 90 else 0.006), [],
                         spread=(0.3, 0.7), shrink=(0.5, 0.66), step=3.0, twig=True)
        for (x, y), (w, v) in shade_limbs(segs).items():
            if 0 <= y < H:
                vv = 0.18 + 0.55 * v + haze + 0.25 * smooth(90, 200, y) - (0.1 if (w > 8 and h01(x // 2, y // 14 + x // 11, seed) < 0.15) else 0)
                cv.set(x, y, pick(S_BR, vv, x, y))
        for (x0, y0, x1, y1, w) in segs:
            if w < 5 and rnd.random() < 0.22 and 0 < y1 < 150:
                r = rnd.uniform(5, 10)
                cumulus(cv, x1, y1, r * 1.3, r * 0.55, int(x1 * 7 + y1), S_GOLD, haze - 0.1 - 0.15 * smooth(40, 150, y1))
    # 3) towering cumulus near the horizon
    for (cx, cy, rw, rh, s) in ((96, 150, 60, 22, 1), (238, 156, 44, 16, 2), (362, 146, 70, 26, 3),
                                (486, 154, 40, 16, 4)):
        cumulus(cv, cx, cy, rw, rh, 80 + s, S_CLOUD, 0.05)
    # 4) sea of clouds below the Crown
    for x in range(W):
        top = 172 + 6 * math.sin(x / W * 2 * math.pi * 3 + 0.4) + 7 * fbm(x, 0, 64, 1, 90)
        for y in range(int(top), H):
            # rolling billows: domed tops every ~24px
            ph = (x + 11 * math.sin(y * 0.2)) / 24.0
            dome = abs(math.sin(ph * math.pi))
            v = 0.82 - 0.35 * smooth(top, top + 22, y) + 0.12 * dome * (1 - smooth(top, top + 8, y)) \
                + 0.08 * (tn(x, y, 16, 8, 91) - 0.5)
            cv.set(x, y, pick(S_CLOUD, v, x, y))
        cv.set(x, int(top), S_CLOUD[7] if h01(x // 2, 0, 92) < 0.6 else S_CLOUD[6])
    # 5) the sun itself
    for y in range(SUN[1] - 9, SUN[1] + 10):
        for x in range(SUN[0] - 9, SUN[0] + 10):
            d = math.hypot(x - SUN[0], y - SUN[1])
            if d <= 7.5:
                cv.set(x, y, S_SKY[15] if d < 6 else S_SKY[14])
    # 6) drifting petals / motes of light
    rnd = random.Random(33)
    for _ in range(90):
        x, y = rnd.randrange(W), rnd.randrange(10, 170)
        c = S_GOLD[4] if rnd.random() < 0.6 else S_GOLD[2]
        cv.set(x, y, c)
        if rnd.random() < 0.3:
            cv.set(x + 1, y, S_GOLD[1])
    return cv.img


# ---------------------------------------------------------------------------- crown mid
B_BODY = ramp("5a5270", "6c627e", "807490", "96889a", "ac9ea4", "c2b2ae", "d6c6b6")
B_LIT = ramp("e8d8bc", "f6e6c6", "fff4d8")
B_LEAF = ramp("b0a0a8", "cebeb6", "e4d6c2", "f4e8d0", "fffae8")
B_SAP = ramp("c08a3a", "e8b850", "ffe89a")
B_FOG = {B_BODY[0]: B_BODY[1], B_BODY[1]: B_BODY[2], B_BODY[2]: B_BODY[3], B_BODY[3]: B_BODY[4],
         B_BODY[4]: B_BODY[5], B_BODY[5]: B_BODY[6], B_LIT[0]: B_LIT[1], B_LEAF[0]: B_LEAF[1], B_LEAF[1]: B_LEAF[2]}


def build_crown_mid():
    cv = Canvas(W, H, wrap=True)
    rnd = random.Random(55)

    def paint(pxs, ridge_seed, lo=0.0):
        for (x, y), (w, v) in pxs.items():
            if y < 0:
                continue
            vv = 0.08 + 0.8 * v + lo
            if w > 6 and h01(x // 2, y // 5, ridge_seed) < 0.22:
                vv -= 0.18                              # bark furrows
            cv.set(x, y, pick(B_BODY, vv, x, y))

    # a) great limb sweeping across the lower middle (periodic in x -> tiles seamlessly)
    def limb_y(x):
        return 170 + 9 * math.sin(2 * math.pi * x / W + 1.0) + 4 * math.sin(2 * math.pi * 3 * x / W + 0.3)

    segs = []
    for x in range(0, W, 2):
        segs.append((x, limb_y(x), x + 2, limb_y(x + 2), 22 + 5 * math.sin(2 * math.pi * 2 * x / W)))
    paint(shade_limbs(segs), 3)
    # b) rising limbs with forks, thick and pale
    tips = []
    for (x0, ang, ln, wd, dep) in ((140, 98, 70, 18, 2), (392, 80, 80, 20, 2), (262, 90, 40, 10, 1)):
        segs = limb_tree(rnd, x0, 190, math.radians(ang), ln, wd, dep + 1, 0.004, [],
                         spread=(0.35, 0.75), shrink=(0.5, 0.68), step=2.5, twig=True)
        paint(shade_limbs(segs), 7 + dep, -0.04)
        tips += [(x1, y1) for (_, _, x1, y1, w) in segs if w < 5]
    # blossom clumps on a few tips
    for (x, y) in tips[::4]:
        if y < 170:
            r = rnd.uniform(4, 8)
            cumulus(cv, x, y, r * 1.3, r * 0.55, int(x * 7 + y), B_LEAF, -0.05)
            if rnd.random() < 0.35:
                cv.set(x + 1, y, B_SAP[2])
    # c) hanging rootlets with glowing sap beads
    for i in range(22):
        x0 = rnd.randrange(W)
        y0 = limb_y(x0) + 11
        L = rnd.randint(8, 24)
        for k in range(L):
            cv.set(x0 + math.sin(k * 0.3 + i) * 1.3, y0 + k, B_BODY[1])
        cv.set(x0 + math.sin(L * 0.3 + i) * 1.3, y0 + L, B_SAP[2])
    rim_pass(cv, tuple(B_BODY), B_LIT[1], B_LIT[0])
    # d) glowing sap veins along the great limb
    for x in range(W):
        y = limb_y(x) + 3 + 3 * math.sin(2 * math.pi * 11 * x / W)
        if h01(x // 5, 0, 13) < 0.12 and x % 5 < 3:
            cv.set(x, y, B_SAP[1] if x % 5 else B_SAP[2])
    # e) cloud wisps drifting past the lower edge
    for y in range(184, H):
        for x in range(W):
            n = fbm(x, y, 64, 6, 120)
            a = smooth(184, 212, y) * (0.6 + n)
            if a > 0.45 + 0.4 * bt(x, y):
                cv.set(x, y, pick(S_CLOUD, 0.5 + 0.4 * n, x, y))
    haze_toward(cv, 160, 230, B_FOG, 0.9)
    rnd = random.Random(8)
    for _ in range(40):
        x, y = rnd.randrange(W), rnd.randrange(60, 200)
        cv.set(x, y, B_LEAF[4])
    return cv.img


BUILDERS = {"mire": (build_mire_far, build_mire_mid), "crown": (build_crown_far, build_crown_mid)}
