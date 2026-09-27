#!/usr/bin/env python3
"""Agent SC vista backdrops (Expansion 3): painted layers drawn over each region's own parallax in the vista rooms.
-> assets xsc_bg_meteor (SF16), xsc_bg_crater (SF17), xsc_bg_skyline (NH15), xsc_bg_garden (H2/H3), xsc_bg_hearth (E6).
Each sheet: 512x216, tags 'far' (slow) and 'mid' (a little faster), horizontally tileable.
Re-runnable: python3 art/gen_xsc_bg.py [--preview-only]   (preview -> art/previews/xsc_bg.png)"""
import math, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from envlib import C, K, T, h01, clamp, blank, pick, bt, vnoise, fbm, lerpc, scale  # noqa: E402
from xsc_lib import *  # noqa: E402,F401

W, H = 512, 216


def ridge(x, base, amp, sx, seed, octv=3):
    return base - amp * fbm(x, 0, sx, 1, seed, W=W, octaves=octv)


def fill_below(img, fy, fn):
    for x in range(W):
        y0 = int(fy(x))
        for y in range(max(0, y0), H):
            c = fn(x, y, y - y0)
            if c is not None: put(img, x, y, c)


def dots(img, n, seed, y0, y1, cols):
    for i in range(n):
        x, y = int(h01(i, seed) * W), int(y0 + h01(i, seed + 1) * (y1 - y0))
        put(img, x, y, cols[i % len(cols)])


# ---------------------------------------------------------------- SF16: the meteor shower over the old observatory ridge
def meteor_far():
    img = blank(W, H)
    # a band of nebula light across the lower sky (dithered, so it reads as pixel paint)
    for y in range(60, 170):
        for x in range(W):
            band = math.exp(-((y - 118 - 18 * math.sin(x / W * math.tau * 2)) / 26) ** 2)
            n = fbm(x, y, 64, 32, 7, W=W)
            a = band * (0.35 + 0.65 * n) * 0.8
            if a > bt(x, y) + 0.15:
                put(img, x, y, pick(VIOLET, 0.1 + 0.55 * a, x, y) if n < 0.55 else pick(GL, 0.15 + 0.5 * a, x, y))
    # the radiant: where the shower pours from
    rx, ry = 380, 34
    for r in range(18, 0, -1):
        ell(img, rx, ry, r, r, lambda nx, ny, x, y, r=r: (STAR[4] if r < 3 else STAR[3] if r < 7 else STAR[1]) if h01(x, y, r) > r / 20 else None)
    dots(img, 160, 3, 0, 140, [STAR[2], STAR[3], STAR[1]])
    return img


def meteor_mid():
    img = blank(W, H)
    fy = lambda x: ridge(x, 196, 30, 128, 11)
    fill_below(img, fy, lambda x, y, d: pick(OB, 0.22 - 0.02 * min(d, 8) + (0.18 if d == 0 else 0), x, y))
    # the old observatory: domes and slim towers along the ridge, one window still burning cold blue
    for cx, r, tower in ((70, 16, 0), (150, 10, 1), (236, 22, 0), (330, 12, 1), (430, 18, 0)):
        by = int(fy(cx)) + 2
        rect(img, cx - r - 2, by - 12, cx + r + 2, by, lambda x, y: pick(OB, 0.3, x, y))
        ell(img, cx, by - 12, r, r * 0.9, lambda nx, ny, x, y: pick(OB, 0.32 - 0.1 * nx, x, y) if ny < 0 else None)
        if tower: rect(img, cx + r, by - 44, cx + r + 4, by, lambda x, y: pick(OB, 0.3, x, y)); put(img, cx + r + 2, by - 38, STAR[3])
        put(img, cx - 2, by - 8, STAR[3]); put(img, cx - 2, by - 7, STAR[2])
        for a in range(0, 180, 6): put(img, cx + math.cos(math.radians(180 + a)) * r, by - 12 + math.sin(math.radians(180 + a)) * r * 0.9, OB[5])
        line(img, (cx + 2, by - 18), (cx + r + 6, by - 28), OB[4])       # the telescopes
    return img


# ---------------------------------------------------------------- SF17: the whole crater from the rim, the fallen star's glow below
def crater_far():
    img = blank(W, H)
    cx, cy = 256, 200
    for y in range(108, H):                         # the bowl of black glass, curving away below the rim
        for x in range(W):
            nx, ny = (x - cx) / 300, (y - cy) / 80
            rim = 116 + 10 * math.cos(nx * 2.2) + 3 * math.sin(x * 0.07)
            if y < rim: continue
            d = nx * nx + ny * ny
            glow = math.exp(-d * 9)
            v = 0.1 + 0.08 * (fbm(x, y, 32, 8, 5, W=W) - 0.5) + 0.05 * (y - rim) / 90
            if (int(x * 0.7 + y * 2.3) % 23 == 0) and h01(x, y) < 0.5: v += 0.16      # glass facets catching the light
            if y - rim < 1: v += 0.2
            if glow > 0.12: put(img, x, y, pick(GL, 0.1 + glow * 0.75, x, y))
            else: put(img, x, y, pick(OB, v + glow * 1.5, x, y))
    for r in range(18, 0, -1):                      # the heart of the fall
        ell(img, cx, cy + 4, r * 1.5, r * 0.55, lambda nx, ny, x, y, r=r: (STAR[4] if r < 5 else STAR[3] if r < 10 else STAR[2]) if h01(x, y, r) > r / 22 else None)
    for k in range(11):                             # light rays climbing out of it
        a = -math.pi / 2 + (k - 5) * 0.16
        for i in range(14, 70):
            if h01(k, i) < 0.4: put(img, cx + math.cos(a) * i * 1.8, cy + math.sin(a) * i, STAR[2] if i < 40 else STAR[1])
    for sx in (120, 172, 330, 390):                 # glass spires far across
        by = 122 + int(10 * math.cos((sx - cx) / 300 * 2.2))
        line(img, (sx, by), (sx + 2, by - 14), OB[5]); line(img, (sx + 1, by), (sx + 3, by - 12), OB[3])
    ob = 124 + int(10 * math.cos((308 - cx) / 300 * 2.2))   # the shattered observatory, tiny
    rect(img, 302, ob - 8, 314, ob, lambda x, y: pick(PALESTONE, 0.28, x, y))
    ell(img, 308, ob - 8, 7, 5, lambda nx, ny, x, y: pick(PALESTONE, 0.32, x, y) if ny < 0 and nx < 0.35 else None)
    return img


def crater_mid():
    img = blank(W, H)
    fy = lambda x: ridge(x, 222, 22, 64, 21, 2)
    fill_below(img, fy, lambda x, y, d: pick(OB, 0.18 + (0.25 if d == 0 else 0), x, y))
    for sx in (40, 60, 210, 380, 470):
        by = int(fy(sx)) if fy(sx) < H else None
        if by: line(img, (sx, by), (sx - 3, by - 20), GL[3]); line(img, (sx + 1, by), (sx - 2, by - 18), GL[2])
    return img


# ---------------------------------------------------------------- NH15: the neon skyline in the rain
def skyline_far():
    img = blank(W, H)
    x = 0
    i = 0
    while x < W:
        w = 10 + int(h01(i, 4) * 26); h = 40 + int(h01(i, 5) * 90); top = 190 - h
        for yy in range(top, H):
            for xx in range(x, min(W, x + w)):
                put(img, xx, yy, NV[2] if xx - x > 1 else NV[3])
        for yy in range(top + 4, H - 6, 4):          # lit windows
            for xx in range(x + 2, min(W, x + w) - 2, 3):
                r = h01(xx, yy, 9)
                if r > 0.72: put(img, xx, yy, AMB[3] if r < 0.9 else CY[3] if r < 0.96 else MG[3])
        if h01(i, 6) > 0.7: rect(img, x + 2, top - 10, x + 3, top, NV[3]); put(img, x + 2, top - 11, MG[3])
        if h01(i, 7) > 0.8: rect(img, x + 2, top + 10, min(W - 1, x + w - 3), top + 14, MG[2] if i % 2 else CY[2])   # a sign
        x += w + int(h01(i, 8) * 4); i += 1
    for y in range(0, H):                           # rain haze
        for xx in range(W):
            if (xx + y * 3) % 97 == 0 and h01(xx, y) < 0.5: put(img, xx, y, NV[4])
    return img


def skyline_mid():
    img = blank(W, H)
    x = 0; i = 0
    while x < W:
        w = 40 + int(h01(i, 14) * 50); h = 30 + int(h01(i, 15) * 50); top = 216 - h
        rect(img, x, top, min(W - 1, x + w), H - 1, lambda xx, yy: NV[1] if xx - x > 2 else NV[3])
        for yy in range(top + 5, H - 4, 4):
            for xx in range(x + 4, min(W, x + w) - 4, 4):
                r = h01(xx, yy, 19)
                if r > 0.78: rect(img, xx, yy, xx + 1, yy, AMB[2] if h01(xx, yy, 2) < 0.8 else CY[2])
        if h01(i, 16) > 0.4:                          # a rooftop sign
            sx = x + 6; col = [MG, CY, AMB][i % 3]
            rect(img, sx, top - 16, sx + 22, top - 4, col[1]); rect(img, sx + 1, top - 15, sx + 21, top - 5, col[2])
            for k in range(3): rect(img, sx + 3 + k * 6, top - 13, sx + 6 + k * 6, top - 7, col[4])
            line(img, (sx + 4, top - 4), (sx + 4, top), NV[4]); line(img, (sx + 18, top - 4), (sx + 18, top), NV[4])
        if h01(i, 17) > 0.6: rect(img, x + w - 10, top - 8, x + w - 4, top, RUST[3])       # water tanks
        x += w + 6; i += 1
    return img


# ---------------------------------------------------------------- H2/H3: dusk hills beyond the Hermit's garden
def garden_far():
    img = blank(W, H)
    DUSK = ramp("1a1420", "261c2a", "342634", "46323e", "5e4248")
    fy = lambda x: ridge(x, 150, 60, 128, 31)
    fill_below(img, fy, lambda x, y, d: pick(DUSK, 0.55 - 0.012 * d + (0.3 if d == 0 else 0), x, y))
    # the Ashen Ramparts, far along the ridge: towers with a light or two
    for tx in (96, 118, 350):
        by = int(fy(tx)) + 1
        rect(img, tx, by - 22, tx + 5, by, lambda x, y: DUSK[1]); rect(img, tx - 1, by - 24, tx + 6, by - 22, DUSK[1])
        put(img, tx + 2, by - 15, AMB[3])
    rect(img, 101, int(fy(110)) - 10, 118, int(fy(110)), lambda x, y: DUSK[1])
    return img


def garden_mid():
    img = blank(W, H)
    HILL = ramp("0e0c10", "16121a", "1e1822", "28202a")
    fy = lambda x: ridge(x, 196, 34, 64, 41)
    fill_below(img, fy, lambda x, y, d: pick(HILL, 0.6 - 0.02 * min(d, 20), x, y))
    for i in range(22):                               # pines on the hill
        px = int(h01(i, 43) * W); by = int(fy(px)) + 2; hh = 14 + int(h01(i, 44) * 16)
        for k in range(hh):
            w = int((1 - k / hh) * (5 + hh / 6)) if k % 4 != 0 else int((1 - k / hh) * (3 + hh / 8))
            line(img, (px - w, by - k), (px + w, by - k), HILL[0])
    for i in range(5):                                # stone lanterns lit along a far path
        px = 60 + i * 97; by = int(fy(px)) + 3
        rect(img, px, by - 4, px + 1, by, HILL[1]); put(img, px, by - 5, AMB[4]); put(img, px + 1, by - 5, AMB[3])
    return img


# ---------------------------------------------------------------- E6: the ashen expanse through the Last Hearth's window
def hearth_far():
    img = blank(W, H)
    for y in range(H):
        for x in range(W):
            t = y / H
            glow = math.exp(-((y - 170) / 40) ** 2)
            if glow * 0.9 > bt(x, y) * 0.9 + 0.05:
                put(img, x, y, pick(FIRE, 0.05 + 0.35 * glow, x, y))
    fy = lambda x: ridge(x, 186, 16, 64, 51, 2)
    fill_below(img, fy, lambda x, y, d: pick(ASH, 0.25 - 0.01 * d + (0.2 if d == 0 else 0), x, y))
    cx = 330                                          # the Cinder Tree, far away, burning inside
    for y in range(90, int(fy(cx)) + 1):
        w = 2 + (int(fy(cx)) - y) // 18
        for dx in range(-w, w + 1): put(img, cx + dx, y, CHAR[1])
        if y % 5 == 0: put(img, cx + (y % 3) - 1, y, FIRE[4])
    for a, L in ((-0.6, 40), (0.7, 36), (-0.2, 30), (0.3, 44)):
        line(img, (cx, 108), (cx + math.sin(a) * L, 108 - math.cos(a) * L), CHAR[1])
    for i in range(40):
        put(img, int(h01(i, 55) * W), int(60 + h01(i, 56) * 120), FIRE[3] if i % 3 else FIRE[5])
    return img


def hearth_mid():
    img = blank(W, H)
    fy = lambda x: ridge(x, 206, 10, 32, 61, 2)
    fill_below(img, fy, lambda x, y, d: pick(ASH, 0.12, x, y))
    for i in range(8):
        px = int(h01(i, 63) * W); by = int(fy(px)) + 2
        line(img, (px, by), (px + 2, by - 30), CHAR[0]); line(img, (px + 1, by - 18), (px + 9, by - 26), CHAR[0]); line(img, (px + 1, by - 24), (px - 6, by - 33), CHAR[0])
    return img


def shifted(fn, dy):
    def f():
        src, out = fn(), blank(W, H)
        out.alpha_composite(src.crop((0, max(0, -dy), W, H if dy < 0 else H - dy)), (0, max(0, dy)))
        # continue the bowl's floor down so the shifted layer has no hard bottom edge
        if dy < 0:
            for y in range(H + dy, H):
                for x in range(W): put(out, x, y, pick(OB, 0.1 + 0.05 * h01(x, y), x, y))
        return out
    return f


SETS = {"xsc_bg_meteor": (meteor_far, meteor_mid), "xsc_bg_crater": (shifted(crater_far, -64), shifted(crater_mid, -36)), "xsc_bg_skyline": (skyline_far, skyline_mid),
        "xsc_bg_garden": (garden_far, garden_mid), "xsc_bg_hearth": (hearth_far, hearth_mid)}


def main():
    ase = "--preview-only" not in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    pv = []
    BGS = {"xsc_bg_meteor": "bg_starfall", "xsc_bg_crater": "bg_starfall", "xsc_bg_skyline": "bg_neohallow", "xsc_bg_garden": "bg_hermit", "xsc_bg_hearth": "bg_ember"}
    for name, (ff, fm) in SETS.items():
        if only and name not in only: continue
        far, mid = ff(), fm()
        if ase: asebuild.build(name, W, H, ["Layer"], [{"ms": 1000, "cels": {"Layer": far}}, {"ms": 1000, "cels": {"Layer": mid}}], [("far", 0, 0), ("mid", 1, 1)])
        comp = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        base = BGS[name]
        for l in ("far", "mid"):
            p = os.path.join(os.path.dirname(HERE), "assets", f"{base}_{l}.png")
            if os.path.exists(p):
                b = Image.open(p).convert("RGBA").crop((0, 0, W, H)); comp.alpha_composite(b)
        comp.alpha_composite(far); comp.alpha_composite(mid)
        pv.append(comp)
    sheet = Image.new("RGBA", (W, H * len(pv)))
    for i, c in enumerate(pv): sheet.paste(c, (0, i * H))
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    scale(sheet, 2).save(os.path.join(HERE, "previews", "xsc_bg.png"))
    print("xsc backdrops", "(preview only)" if not ase else "built")


if __name__ == "__main__":
    main()
