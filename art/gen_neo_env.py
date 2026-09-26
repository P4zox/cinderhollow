#!/usr/bin/env python3
"""NEO-HALLOW environment (agent NH): tilesets, parallax, props, small FX.

    python3 art/gen_neo_env.py [--preview]

tiles_neohallow        48x(16x16)  rain-slick rooftop concrete + gunmetal, neon rim strips; variants show the
                                   fossilised Pale Root (ivory fibres) the city is built on, lit windows, vents
tiles_neohallow_cyber  48x(16x16)  cyberspace: inverted palette -- pale data-planes with navy wireframe edges
bg_neohallow_far/mid   512x216     night megacity on the petrified Root; holo billboards flicker (4 frames)
bg_neohallow_cyber_*   512x216     pale wireframe void: receding grid, wire towers
nh_deco   64x80  bottom-anchored decor: sign0-2, billboard0-2, lamp, antenna, vent, canopy, pylon, rack, glyph
nh_term   24x32  hack terminal: idle(4) on(4)
nh_train  112x48 maglev car: idle(1) run(4) (roof = top 8px: the engine draws it so the roof sits at y-(48-8))
nh_portal 32x64  the crack in reality: loop(8)
fx_nh_blast 48x48 (7), fx_nh_warp 24x64 (8, bottom), fx_nh_missile 16x8 (4)
Previews: art/previews/neo_env_*.png
"""
import math, os, random, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
from envlib import C, ramp, bt, h01, clamp, pick, vnoise  # noqa: E402

BUILD = "--preview" not in sys.argv
T = (0, 0, 0, 0)
OUT = C("05060c")
# ---------------------------------------------------------------- palette
NAVY = ramp("04050a", "080a13", "0c101c", "111726", "171f33", "1e2842", "283554", "344468", "46587e")
METAL = ramp("1b1f2e", "2c3245", "3e4660", "58627e", "7d88a4", "a9b3c8", "d9e1ee")
CY = ramp("06202e", "0b4d66", "13a3c9", "3fe0ff", "b8f6ff", "f2feff")
MG = ramp("2a0624", "6e0f5c", "c21d97", "ff3fc0", "ff9fe2", "fff0fb")
AMB = ramp("3a1e06", "7a4410", "c87a20", "ffb050", "ffe0a0")
FOS = ramp("2e2b28", "4a4640", "6f6a60", "9c968a", "c9c3b4", "e8e3d6")   # fossil root ivory
RED = ramp("3a0610", "8a0f22", "e0223f", "ff6a7e")
# cyberspace (inverted): pale planes, navy wire
PALE = ramp("9aa8bc", "b3bfd0", "c8d2df", "d8e0ea", "e6ecf3", "f4f7fb")
WIRE = ramp("060a26", "0b1030", "1a2360", "2c3a9a", "4a5ad0")


def img(w, h, c=T):
    return Image.new("RGBA", (w, h), c)


def put(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height and c is not None:
        im.putpixel((int(x), int(y)), c)


def rect(im, x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        for x in range(int(x0), int(x0 + w)):
            put(im, x, y, c)


def line(im, x0, y0, x1, y1, c):
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
    for i in range(n + 1):
        put(im, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def outline(im, col=OUT):
    src = im.copy(); px = src.load(); w, h = im.size
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 and any(0 <= x + a < w and 0 <= y + b < h and px[x + a, y + b][3] > 0 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), col)
    return im


# =========================================================================== tiles (city)
N_, E_, S_, W_ = 1, 2, 4, 8


def panel_px(x, y):
    """16x16 torus: concrete/gunmetal cladding panels 8 wide, courses 8 tall, offset per course."""
    course = y // 8
    ox = (x + (4 if course % 2 else 0)) % 8
    oy = y % 8
    joint = ox == 0 or oy == 0
    rivet = (ox == 2 or ox == 6) and oy == 2
    return joint, rivet, ox, oy


def city_tile(mask, var=False, seed=0):
    t = img(16, 16)
    for y in range(16):
        for x in range(16):
            # depth from exposed sides
            d = 9
            if mask & N_: d = min(d, y)
            if mask & S_: d = min(d, 15 - y)
            if mask & W_: d = min(d, x)
            if mask & E_: d = min(d, 15 - x)
            joint, rivet, ox, oy = panel_px(x, y)
            n = vnoise(x, y, 4, 4, 11) * 0.5 + h01(x, y, 3) * 0.2
            v = 0.34 + n * 0.25 - (0.12 if joint else 0) + (0.12 if rivet else 0)
            if d >= 4: v -= 0.18 + min(0.12, (d - 4) * 0.04)
            elif d == 3: v -= 0.08
            c = pick(NAVY[2:8], v, x, y)
            if rivet and d < 5: c = NAVY[6]
            put(t, x, y, c)
    if var:
        decorate_variant(t, mask, seed)
    # --- edges
    if mask & N_:
        for x in range(16):
            put(t, x, 0, METAL[5] if h01(x, 1, seed) > 0.2 else METAL[4])
            put(t, x, 1, METAL[3])
            put(t, x, 2, METAL[1])
            # neon rim strip, broken here and there
            if h01(x // 4, 7, seed) > 0.25: put(t, x, 3, CY[2] if (x + seed) % 6 else CY[3])
            else: put(t, x, 3, NAVY[3])
            # rain sheen glints on the lip
            if h01(x, 9, seed) > 0.88: put(t, x, 0, METAL[6])
    if mask & W_:
        for y in range(16):
            if not (mask & N_ and y < 3): put(t, 0, y, NAVY[7] if y % 5 else METAL[3])
    if mask & E_:
        for y in range(16):
            if not (mask & N_ and y < 3): put(t, 15, y, NAVY[1])
    if mask & S_:
        for x in range(16):
            put(t, x, 15, NAVY[1]); put(t, x, 14, MG[1] if h01(x // 3, 5, seed) > 0.55 else NAVY[2])
    if mask & N_ and mask & W_: put(t, 0, 0, METAL[4])
    if mask & N_ and mask & E_: put(t, 15, 0, METAL[3]); put(t, 15, 1, METAL[2])
    return t


def decorate_variant(t, mask, seed):
    k = seed % 4
    if k == 0:   # fossil Pale Root fibres running through the concrete
        y0 = 5 + (seed * 3) % 7
        for x in range(16):
            y = y0 + math.sin(x * 0.45 + seed) * 2.2
            for dy, c in ((0, FOS[3]), (1, FOS[1])):
                yy = int(round(y + dy))
                if 4 <= yy < 15: put(t, x, yy, c)
            if h01(x, seed, 2) > 0.85 and 4 <= int(y) - 1 < 15: put(t, x, int(y) - 1, FOS[4])
    elif k == 1:          # a column of lit windows
        for wy in range(6, 14, 3):
            for wx in (4, 10):
                if h01(wx, wy, seed) > 0.35:
                    c = [AMB[3], CY[3], MG[3], AMB[2]][int(h01(wx, wy, seed + 1) * 4)]
                    put(t, wx, wy, c); put(t, wx + 1, wy, c); put(t, wx, wy + 1, NAVY[5]); put(t, wx + 1, wy + 1, NAVY[5])
    else:                 # a vent grille + a drip stain
        for yy in range(7, 12):
            for xx in range(4, 12):
                put(t, xx, yy, NAVY[1] if yy % 2 else NAVY[5])
        for yy in range(12, 16): put(t, 9, yy, NAVY[1])


def platform(kind, cyber=False):
    t = img(16, 16)
    if cyber:
        for x in range(16):
            put(t, x, 0, WIRE[1]); put(t, x, 4, WIRE[1])
            if x % 4 == 0: line(t, x, 0, x, 4, WIRE[2])
        return t
    for x in range(16):
        put(t, x, 0, METAL[5]); put(t, x, 1, METAL[3])
        put(t, x, 2, METAL[1] if x % 3 else METAL[2]); put(t, x, 3, NAVY[3] if x % 3 else METAL[2])
        put(t, x, 4, CY[2] if x % 2 else CY[1])
    if kind in ("L", "single"):
        rect(t, 0, 0, 1, 5, METAL[4]); line(t, 1, 5, 4, 8, METAL[1])
    if kind in ("R", "single"):
        rect(t, 15, 0, 1, 5, METAL[2]); line(t, 14, 5, 11, 8, METAL[1])
    return t


def spikes(up=True, cyber=False):
    t = img(16, 16)
    for i in range(4):
        cx = 2 + i * 4
        for h in range(8):
            w = max(0, 1 - h // 5)
            y = 15 - h if up else h
            c = (WIRE[1] if cyber else (CY[3] if h > 5 else METAL[3 + (h % 2)]))
            for xx in range(cx - w, cx + w + 1): put(t, xx, y, c)
    return t


def bg_wall(k, cyber=False):
    t = img(16, 16)
    for y in range(16):
        for x in range(16):
            if cyber:
                c = PALE[1] if (x % 8 == 0 or y % 8 == 0) else PALE[3]
            else:
                joint = x % 8 == 0 or y % 16 == 0
                c = NAVY[1] if joint else pick(NAVY[1:4], 0.3 + vnoise(x, y, 5, 5, 3 + k) * 0.4, x, y)
            put(t, x, y, c)
    if not cyber:
        if k == 1:       # server status LEDs
            for yy in range(3, 14, 3):
                for xx in range(3, 13, 2):
                    if h01(xx, yy, k) > 0.5: put(t, xx, yy, [CY[2], CY[1], MG[1], NAVY[5]][int(h01(xx, yy, 9) * 4)])
        elif k == 2:     # a cable conduit
            rect(t, 6, 0, 4, 16, NAVY[3]); line(t, 6, 0, 6, 15, NAVY[5]); line(t, 9, 0, 9, 15, NAVY[1])
        elif k == 3:     # a faint glyph panel
            for yy in range(4, 13, 2):
                for xx in range(4, 12):
                    if h01(xx, yy, 5) > 0.55: put(t, xx, yy, CY[0])
    else:
        if k == 1:
            for yy in range(2, 15, 3): line(t, 2, yy, 13, yy, PALE[2])
    return t


def deco(kind, cyber=False):
    t = img(16, 16)
    if cyber:
        if kind == 0: line(t, 8, 0, 8, 15, WIRE[2])
        return t
    if kind == 0:        # hanging cable
        for y in range(16): put(t, 7 + int(math.sin(y * 0.4) * 1.2), y, NAVY[5]); put(t, 8 + int(math.sin(y * 0.4) * 1.2), y, NAVY[2])
    elif kind == 1:      # cable bundle with a lit tag
        for i, off in enumerate((4, 7, 10)):
            for y in range(12 - i * 2): put(t, off + int(math.sin(y * 0.5 + i) * 1), y, [NAVY[5], NAVY[4], MG[1]][i])
        put(t, 7, 6, CY[3])
    elif kind == 2:      # small neon tube light on the floor
        rect(t, 3, 12, 10, 2, METAL[2]); rect(t, 4, 11, 8, 1, MG[3]); put(t, 4, 11, MG[4]); put(t, 11, 11, MG[4])
    else:                # debris: cans, a broken drone shell
        rect(t, 3, 13, 3, 3, METAL[3]); put(t, 3, 13, METAL[5]); rect(t, 8, 12, 5, 4, NAVY[5]); put(t, 9, 13, RED[2]); rect(t, 13, 14, 2, 2, AMB[1])
    return t


def breakable():
    t = city_tile(0)
    pts = [(2, 3), (5, 6), (7, 5), (9, 9), (12, 10), (14, 14)]
    for (a, b), (c, d) in zip(pts, pts[1:]): line(t, a, b, c, d, NAVY[0])
    for (a, b), (c, d) in zip(pts, pts[1:]): line(t, a, b + 1, c, d + 1, NAVY[5])
    put(t, 8, 7, CY[1]); put(t, 11, 10, CY[1])
    return t


def tuft(cyber=False):
    t = img(16, 16)
    if cyber: return t
    # a rain puddle sheen on the rooftop lip
    for x in range(2, 14):
        put(t, x, 15, CY[1] if x % 3 else CY[2])
        if 4 < x < 11: put(t, x, 14, NAVY[6])
    put(t, 6, 14, CY[4])
    return t


def cyber_tile(mask, var=False):
    t = img(16, 16)
    for y in range(16):
        for x in range(16):
            gx = x % 8 == 0 or y % 8 == 0
            put(t, x, y, PALE[2] if gx else PALE[4] if (x + y) % 2 else PALE[5])
    if var:
        for i in range(3, 13, 3): put(t, i, i, WIRE[3]); put(t, 15 - i, i, WIRE[3])
    if mask & N_:
        for x in range(16): put(t, x, 0, WIRE[1]); put(t, x, 1, WIRE[3] if x % 2 else PALE[1])
    if mask & S_:
        for x in range(16): put(t, x, 15, WIRE[1])
    if mask & W_:
        for y in range(16): put(t, 0, y, WIRE[1])
    if mask & E_:
        for y in range(16): put(t, 15, y, WIRE[1])
    return t


def build_tiles(cyber):
    if cyber:
        ts = [cyber_tile(m) for m in range(16)] + [cyber_tile(m, True) for m in range(16)]
        ts += [platform(k, True) for k in ("L", "M", "R", "single")]
        ts += [spikes(True, True), spikes(False, True)] + [bg_wall(k, True) for k in range(4)]
        ts += [deco(k, True) for k in range(4)]
        b = cyber_tile(0); line(b, 3, 3, 12, 12, WIRE[2]); ts += [b, tuft(True)]
    else:
        ts = [city_tile(m, False, m) for m in range(16)] + [city_tile(m, True, m * 7 + 3) for m in range(16)]
        ts += [platform(k) for k in ("L", "M", "R", "single")]
        ts += [spikes(True), spikes(False)] + [bg_wall(k) for k in range(4)]
        ts += [deco(k) for k in range(4)] + [breakable(), tuft()]
    assert len(ts) == 48
    return ts


# =========================================================================== parallax
BW, BH = 512, 216


def sky_col(y, cyber):
    if cyber:
        v = y / BH
        return pick(PALE, 0.95 - v * 0.55, 0, y)
    v = y / BH
    return None, v


def build_far(frame, cyber=False):
    im = img(BW, BH)
    px = im.load()
    rnd = random.Random(7)
    if cyber:
        for y in range(BH):
            for x in range(BW):
                v = 0.95 - (y / BH) * 0.5
                px[x, y] = pick(PALE, v, x, y)
        horizon = 128
        # the receding grid floor
        lasty = -9
        for i in range(1, 30):
            y = horizon + int((i / 30) ** 2.2 * (BH - horizon))
            if y - lasty < 3: continue
            lasty = y
            for x in range(BW): px[x, y] = WIRE[2] if i % 4 else WIRE[1]
        for k in range(-40, 41):
            x0 = BW // 2 + k * 14
            for y in range(horizon + 4, BH):
                t = (y - horizon) / (BH - horizon)
                x = int(BW / 2 + (x0 - BW / 2) * (0.06 + t * 1.6))
                if 0 <= x < BW: px[x % BW, y] = WIRE[2]
        # wire towers on the horizon
        for tw in range(14):
            cx = rnd.randint(0, BW - 1); w = rnd.randint(10, 30); h = rnd.randint(30, 100)
            for y in range(horizon - h, horizon):
                for x in (cx, cx + w):
                    px[x % BW, y] = WIRE[2]
            for y in range(horizon - h, horizon, 6):
                for x in range(cx, cx + w + 1): px[x % BW, y] = WIRE[3] if (y // 6 + frame) % 5 else WIRE[4]
        # a vast wire sphere (the archive)
        cx, cy, r = 360, 64, 40
        for a in range(0, 360, 2):
            for lat in range(-60, 61, 30):
                x = cx + r * math.cos(math.radians(a)) * math.cos(math.radians(lat)); y = cy + r * math.sin(math.radians(lat))
                px[int(x) % BW, int(y)] = WIRE[2]
            for lon in range(0, 180, 30):
                ang = math.radians(lon + frame * 7)
                x = cx + r * math.cos(math.radians(a)) * math.cos(ang); y = cy + r * math.sin(math.radians(a))
                px[int(x) % BW, int(y)] = WIRE[3] if lon % 60 == 0 else WIRE[2]
        return im
    # ---- night sky: deep navy to a violet city-glow near the horizon, dithered
    for y in range(BH):
        v = y / BH
        for x in range(BW):
            n = vnoise(x, y, 64, 24, 3) * 0.12
            if v < 0.55:
                c = pick([NAVY[0], NAVY[1], NAVY[2], NAVY[3]], v * 1.1 + n, x, y)
            else:
                c = pick([NAVY[3], C("1c1838"), C("2a1c48"), C("3a1e52")], (v - 0.55) * 2.2 + n, x, y)
            px[x, y] = c
    # clouds lit magenta from below
    for y in range(8, 90):
        for x in range(BW):
            cl = vnoise(x, y, 48, 10, 21) * 0.7 + vnoise(x, y, 16, 5, 22) * 0.3
            if cl > 0.62:
                px[x, y] = pick([NAVY[2], NAVY[3], C("2a1a44"), C("40204e")], (cl - 0.62) * 3 + y / 200, x, y)
    # ---- the fossilised Pale Root: a colossal petrified trunk rising behind the city, its dead crown in the clouds
    FOSD = [C("0e0f18"), C("16161f"), C("1f1e27"), C("2a2830"), C("37343a"), C("484449"), C("5e5a5c")]   # fossil, hazed by distance
    def trunk_w(y):   # half width at row y (trunk centre drifts a little)
        t = y / BH
        return 16 + 30 * t ** 1.3
    def trunk_x(y):
        return 300 + math.sin(y / 60) * 10 - (BH - y) * 0.12
    limbs = []
    for (sy, ang, ln, w0) in ((70, -150, 150, 9), (55, -35, 130, 8), (40, -110, 70, 6), (90, -20, 110, 7), (30, -70, 60, 5), (100, -165, 120, 7)):
        pts = []
        x, y = trunk_x(sy), sy
        a_ = math.radians(ang)
        for i in range(ln):
            t = i / ln
            a2 = a_ + math.sin(t * 3 + sy) * 0.25 + (0.25 * t if ang < -90 else -0.25 * t)
            x += math.cos(a2); y += math.sin(a2) * 0.7
            pts.append((x, y, max(1.0, w0 * (1 - t) ** 0.9)))
        limbs.append(pts)
    def shade(x, y, s, w):
        # cylinder shading lit from the city glow below-left + vertical petrified striations
        stri = vnoise(x * 3, y, 2, 30, 8) * 0.25
        v = 0.55 - s * 0.35 + stri + (y / BH) * 0.15
        if abs(s) > 0.85: v -= 0.2
        return pick(FOSD, v, int(x), int(y))
    for y in range(0, BH):
        cx, w = trunk_x(y), trunk_w(y)
        for x in range(int(cx - w), int(cx + w) + 1):
            s = (x - cx) / w
            if 0 <= x < BW: px[x, y] = shade(x, y, s, w)
    for pts in limbs:
        for (x0, y0, w) in pts:
            for dy in range(-int(w), int(w) + 1):
                x, y = int(x0), int(y0 + dy)
                if 0 <= x < BW and 0 <= y < BH: px[x, y] = shade(x, y, dy / max(1, w), w)
    # city lights crawling up the trunk (sparse, in bands like terraces)
    for y in range(20, BH, 7):
        cx, w = trunk_x(y), trunk_w(y)
        for x in range(int(cx - w + 3), int(cx + w - 3), 3):
            if h01(x, y, 3) > 0.7:
                px[x % BW, y] = [AMB[2], CY[2], MG[2], AMB[3]][int(h01(x, y, 4) * 4)]
        if y % 21 == 0:   # a lit terrace ring
            for x in range(int(cx - w), int(cx + w)): 
                if h01(x, y, 5) > 0.3: px[x % BW, y] = C("3a2a40")

    # ---- skyline (far): towers with tiny windows
    for tw in range(70):
        cx = rnd.randint(0, BW - 1); w = rnd.randint(8, 26); h = rnd.randint(30, 120)
        top = BH - h
        shade = rnd.choice([NAVY[1], NAVY[2], C("0f0d1e")])
        for y in range(top, BH):
            for x in range(cx, cx + w):
                px[x % BW, y] = shade
        if rnd.random() < 0.5:   # antenna with a blinking tip
            for y in range(top - rnd.randint(4, 14), top): px[(cx + w // 2) % BW, y] = NAVY[4]
            px[(cx + w // 2) % BW, top - 1] = RED[2] if frame % 2 else RED[1]
        for y in range(top + 3, BH, 3):
            for x in range(cx + 1, cx + w - 1, 2):
                if h01(x // 4, y // 6, tw) > 0.55 and h01(x, y, tw) > 0.62:
                    px[x % BW, y] = [AMB[2], AMB[1], CY[1], MG[1], CY[2]][int(h01(x, y, tw + 50) * 5)]
    # ---- holographic billboards (flicker per frame)
    for bi, (bx, by, bw, bh, col) in enumerate(((60, 110, 34, 20, MG), (228, 90, 26, 34, CY), (400, 124, 40, 18, MG), (470, 70, 18, 30, CY))):
        on = not (frame == (bi % 4) and bi % 2)
        for y in range(by, by + bh):
            for x in range(bx, bx + bw):
                edge = x in (bx, bx + bw - 1) or y in (by, by + bh - 1)
                if edge: px[x % BW, y] = col[3] if on else col[1]
                elif on and (y - by) % 3 == 0 and h01(x // 3, y + frame * 5, bi) > 0.45: px[x % BW, y] = col[2]
                elif on and h01(x, y, bi) > 0.93: px[x % BW, y] = col[4]
    # maglev lines with a moving train
    for ly, sp in ((150, 40), (176, -60)):
        for x in range(BW): px[x, ly] = NAVY[5]
        tx = (frame * sp) % BW
        for x in range(tx, tx + 22): px[x % BW, ly - 1] = CY[3]; px[x % BW, ly - 2] = NAVY[6]
    return im


def build_mid(frame, cyber=False):
    im = img(BW, BH); px = im.load()
    rnd = random.Random(31)
    if cyber:
        for tw in range(10):
            cx = rnd.randint(0, BW - 1); w = rnd.randint(30, 60); h = rnd.randint(60, 150); top = BH - h
            for y in range(top, BH):
                px[cx % BW, y] = WIRE[1]; px[(cx + w) % BW, y] = WIRE[1]
            for x in range(cx, cx + w + 1):
                px[x % BW, top] = WIRE[1]
            for y in range(top + 8, BH, 12):
                for x in range(cx + 3, cx + w - 2, 5): px[x % BW, y] = WIRE[2]
            # glitch block
            if (tw + frame) % 3 == 0:
                gy = top + rnd.randint(4, max(5, h - 10))
                for x in range(cx, cx + 12): px[x % BW, gy] = MG[2]
        return im
    for tw in range(16):
        cx = rnd.randint(0, BW - 1); w = rnd.randint(34, 70); h = rnd.randint(70, 170); top = BH - h
        base = rnd.choice([NAVY[1], NAVY[2], C("0b0a17")])
        for y in range(top, BH):
            for x in range(cx, cx + w):
                c = base
                if x == cx: c = NAVY[3]
                px[x % BW, y] = c
        # roof details
        for y in range(top - 3, top):
            for x in range(cx + 4, cx + 12): px[x % BW, y] = NAVY[3]
        if rnd.random() < 0.6:
            wx = cx + w - 10
            for y in range(top - 12, top): px[wx % BW, y] = NAVY[4]; px[(wx + 6) % BW, y] = NAVY[4]
            for x in range(wx - 2, wx + 9):
                for y in range(top - 20, top - 12): px[x % BW, y] = NAVY[3]
        # lit windows
        for y in range(top + 6, BH, 5):
            for x in range(cx + 3, cx + w - 3, 4):
                r = h01(x, y, tw + frame * 0)
                if r > 0.8: px[x % BW, y] = AMB[2]; px[(x + 1) % BW, y] = AMB[2]
                elif r > 0.74: px[x % BW, y] = CY[1]; px[(x + 1) % BW, y] = CY[1]
        # a vertical neon sign in the invented script
        if tw % 2 == 0:
            col = MG if tw % 4 == 0 else CY
            sx = cx + (w - 8 if tw % 3 else 3); sy = top + 10
            flick = (frame + tw) % 7 != 0
            for y in range(sy, sy + 44):
                px[sx % BW, y] = NAVY[4]; px[(sx + 6) % BW, y] = NAVY[4]
            for k in range(6):
                gy = sy + 3 + k * 7
                glyph = int(h01(tw, k, 9) * 16)
                for gx in range(4):
                    for gyy in range(5):
                        if (glyph >> ((gx + gyy) % 4)) & 1 and (gx in (0, 3) or gyy in (0, 2, 4)):
                            px[(sx + 1 + gx) % BW, gy + gyy] = col[3] if flick else col[1]
    return im


# =========================================================================== props
def deco_sheet():
    FW, FH = 64, 80
    frames, tags = [], []

    def add(tag, ims):
        tags.append((tag, len(frames), len(frames) + len(ims) - 1)); frames.extend(ims)

    def neon_glyphs(im, x0, y0, n, col, horiz=True, on=True, seed=0):
        for k in range(n):
            g = int(h01(k, seed, 9) * 16) | 1
            ox, oy = (x0 + k * 7, y0) if horiz else (x0, y0 + k * 7)
            for a in range(5):
                for b in range(5):
                    if ((g >> ((a * 3 + b) % 4)) & 1) and (a in (0, 4) or b in (0, 2, 4)) and not (a in (0, 4) and b in (0, 4)):
                        put(im, ox + a, oy + b, col[4] if on and (a + b) % 3 == 0 else col[3] if on else col[1])
    for v, col in enumerate((MG, CY, AMB)):   # sign0-2: a box sign on a bracket
        ims = []
        for f in range(2):
            im = img(FW, FH)
            rect(im, 31, 44, 2, 36, METAL[1]); rect(im, 31, 44, 1, 36, METAL[3])
            rect(im, 14, 20, 36, 24, NAVY[2]);
            for x in range(14, 50): put(im, x, 20, col[2]); put(im, x, 43, col[2])
            for y in range(20, 44): put(im, 14, y, col[2]); put(im, 49, y, col[2])
            neon_glyphs(im, 18, 26, 4, col, True, f == 0 or v != 1, v)
            rect(im, 17, 37, 30, 1, col[1])
            outline(im)
            ims.append(im)
        add(f"sign{v}", ims)
    for v, col in enumerate((MG, CY, MG)):    # billboard0-2: a tall hologram on a pylon
        ims = []
        for f in range(4):
            im = img(FW, FH)
            rect(im, 30, 50, 4, 30, METAL[1]); rect(im, 30, 50, 1, 30, METAL[3]); rect(im, 24, 76, 16, 4, METAL[2])
            rect(im, 26, 46, 12, 4, METAL[2])
            # projected panel (translucent-looking via dither)
            x0, y0, w, h = 6, 4, 52, 40
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                    scan = (y + f * 3) % 4 == 0
                    if edge: put(im, x, y, col[3])
                    elif (x + y) % 2 == 0: put(im, x, y, col[1] if not scan else col[2])
            # content: a stylised face / eye logo (v0), a glyph wall (v1), a pale root logo (v2)
            if v == 0:
                for a in range(0, 360, 12):
                    put(im, int(32 + 9 * math.cos(math.radians(a))), int(22 + 5 * math.sin(math.radians(a))), col[4])
                rect(im, 30, 20, 5, 5, col[5]); rect(im, 31, 21, 3, 3, NAVY[1])
            elif v == 1:
                neon_glyphs(im, 10, 10, 6, col, True, True, f); neon_glyphs(im, 10, 26, 6, col, True, True, f + 3)
            else:
                for i in range(30):
                    t = i / 29; x = 20 + t * 24; y = 36 - t * 24 + math.sin(t * 6) * 2
                    put(im, int(x), int(y), FOS[5]); put(im, int(x) + 1, int(y), FOS[4])
                neon_glyphs(im, 10, 8, 3, col, True, True, 5)
            if f == 3:   # glitch frame
                for y in range(12, 18):
                    row = [im.getpixel((x, y)) for x in range(64)]
                    for x in range(64): put(im, (x + 5) % 64, y, row[x]) if row[x][3] else None
            outline(im)
            ims.append(im)
        add(f"billboard{v}", ims)
    ims = []
    for f in range(2):   # street lamp, cyan tube head
        im = img(FW, FH)
        rect(im, 31, 30, 2, 50, METAL[2]); put(im, 31, 30, METAL[4])
        line(im, 32, 30, 42, 24, METAL[2]); rect(im, 38, 24, 10, 3, METAL[1])
        rect(im, 39, 27, 8, 1, CY[4] if f == 0 else CY[3]); rect(im, 28, 76, 8, 4, METAL[1])
        outline(im); ims.append(im)
    add("lamp", ims)
    im = img(FW, FH)   # antenna mast
    rect(im, 31, 16, 2, 64, METAL[2]);
    for y in range(20, 76, 8): line(im, 27, y, 36, y + 6, METAL[1])
    line(im, 32, 16, 22, 8, METAL[3]); line(im, 32, 16, 42, 10, METAL[3]); put(im, 32, 15, RED[3])
    outline(im); add("antenna", [im])
    im = img(FW, FH)   # rooftop vent box
    rect(im, 20, 62, 24, 18, METAL[1]); rect(im, 20, 62, 24, 2, METAL[3])
    for y in range(66, 78, 2): rect(im, 23, y, 18, 1, NAVY[1])
    rect(im, 26, 56, 12, 6, METAL[2]); outline(im); add("vent", [im])
    im = img(FW, FH)   # station canopy
    rect(im, 4, 22, 56, 4, METAL[3]); rect(im, 4, 26, 56, 1, CY[2]); rect(im, 10, 26, 2, 54, METAL[1]); rect(im, 52, 26, 2, 54, METAL[1])
    for x in range(4, 60, 6): put(im, x, 22, METAL[5])
    neon_glyphs(im, 20, 30, 4, CY, True, True, 2); outline(im); add("canopy", [im])
    im = img(FW, FH)   # maglev pylon rising from the abyss
    rect(im, 28, 36, 8, 44, NAVY[4]); rect(im, 28, 36, 2, 44, NAVY[6]); rect(im, 22, 32, 20, 4, METAL[2])
    for y in range(40, 80, 6): put(im, 32, y, CY[2])
    outline(im); add("pylon", [im])
    ims = []
    for f in range(2):   # server rack
        im = img(FW, FH)
        rect(im, 20, 30, 24, 50, NAVY[3]); rect(im, 20, 30, 24, 2, METAL[3]); rect(im, 21, 32, 1, 48, NAVY[5])
        for y in range(34, 78, 4):
            rect(im, 23, y, 18, 3, NAVY[1])
            for x in range(25, 39, 3):
                if h01(x, y + f * 7, 3) > 0.5: put(im, x, y + 1, [CY[3], CY[2], MG[3], AMB[3]][int(h01(x, y, 4) * 4)])
        outline(im); ims.append(im)
    add("rack", ims)
    ims = []
    for f in range(4):   # floor hologram glyph (a rotating sigil of the Root)
        im = img(FW, FH)
        rect(im, 22, 76, 20, 4, METAL[2]); rect(im, 24, 75, 16, 1, CY[2])
        for a in range(0, 360, 8):
            ang = math.radians(a + f * 22)
            x = 32 + 12 * math.cos(ang); y = 52 + 12 * math.sin(ang) * 0.9
            if (a // 8) % 3: put(im, int(x), int(y), CY[3])
        for i in range(24):
            t = i / 23; put(im, int(32 + math.sin(t * 6 + f) * 4), int(64 - t * 22), FOS[4])
        ims.append(im)
    add("glyph", ims)
    return FW, FH, frames, tags


def term_sheet():
    frames, tags = [], []
    for tag, col in (("idle", CY), ("on", ramp("0b3a2c", "157a58", "2fd09a", "5affd2", "c8fff0", "f0fff8"))):
        a = len(frames)
        for f in range(4):
            im = img(24, 32)
            rect(im, 6, 12, 12, 20, METAL[1]); rect(im, 6, 12, 12, 1, METAL[3]); rect(im, 6, 12, 1, 20, METAL[2])
            rect(im, 4, 29, 16, 3, METAL[2])
            rect(im, 4, 4, 16, 10, NAVY[2]); rect(im, 5, 5, 14, 8, col[1])
            for y in range(6, 12, 2):
                ln = 3 + int(h01(y, f, 7 if tag == 'idle' else 8) * 9)
                rect(im, 6, y, ln, 1, col[3] if y != 6 + (f % 3) * 2 else col[4])
            rect(im, 9, 18, 6, 2, NAVY[1]); put(im, 10, 18, col[3]); put(im, 13, 18, RED[2] if tag == 'idle' else col[3])
            for y in range(22, 28, 2): rect(im, 8, y, 8, 1, NAVY[3])
            outline(im)
            frames.append(im)
        tags.append((tag, a, len(frames) - 1))
    return 24, 32, frames, tags


def train_sheet():
    FW, FH = 112, 48
    frames = []
    for f in range(5):
        im = img(FW, FH)
        # roof (walkable) at the top: rows 0..3, body below, mag skids at the bottom
        x0, x1 = 8, 104
        for x in range(x0, x1):
            put(im, x, 0, METAL[6] if x % 7 else METAL[5]); put(im, x, 1, METAL[4]); put(im, x, 2, METAL[3])
        for y in range(3, 30):
            nose = max(0, (y - 18) * 0.9)
            for x in range(int(x0 + nose * 0.3), int(x1 - nose)):
                v = 0.55 - y / 70 + (0.12 if x < x0 + 3 else 0)
                c = pick(METAL[0:5], v, x, y)
                put(im, x, y, c)
        # window band (people inside, backlit)
        for x in range(x0 + 6, x1 - 12):
            for y in range(8, 15):
                c = CY[1] if (x // 9) % 2 == 0 else NAVY[4]
                if y == 8: c = CY[3]
                if (x - x0) % 9 == 0: c = METAL[2]
                put(im, x, y, c)
            if h01(x // 9, 3, 1) > 0.5 and (x % 9) in (3, 4):
                for y in range(11, 15): put(im, x, y, NAVY[1])
        # livery stripes
        for x in range(x0 + 2, x1 - 10): put(im, x, 18, MG[3]); put(im, x, 19, MG[2])
        # headlight at the nose (front = right)
        rect(im, x1 - 12, 20, 4, 2, CY[5]); put(im, x1 - 9, 20, (255, 255, 255, 255))
        # tail light
        rect(im, x0 + 1, 20, 2, 2, RED[2])
        # mag skids + glow
        for sx in (20, 84):
            rect(im, sx, 30, 12, 3, NAVY[5]); rect(im, sx, 33, 12, 1, CY[3] if f < 4 else CY[2])
            if f < 4:
                for x in range(sx, sx + 12):
                    if h01(x, f, 2) > 0.4: put(im, x, 34 + (x + f) % 2, CY[2])
        outline(im)
        frames.append(im)
    return FW, FH, frames, [("idle", 4, 4), ("run", 0, 3)]


def portal_sheet():
    FW, FH = 32, 64
    frames = []
    for f in range(8):
        im = img(FW, FH)
        rnd = random.Random(f * 13 + 1)
        pts = []
        x = 16
        for y in range(6, 62):
            x += rnd.choice((-1, 0, 0, 1)) if y % 3 == 0 else 0
            x = max(12, min(20, x))
            pts.append((x, y))
        for (x, y) in pts:
            w = int(2 + 3 * math.sin((y - 6) / 56 * math.pi))
            for dx in range(-w, w + 1):
                c = (255, 255, 255, 255) if abs(dx) <= w // 3 else (CY[4] if dx < 0 else MG[4])
                if abs(dx) == w: c = CY[2] if dx < 0 else MG[2]
                put(im, x + dx, y, c)
        # chromatic fringes + drifting pixels
        for (x, y) in pts[::3]:
            put(im, x - 6 - rnd.randint(0, 2), y, CY[3]); put(im, x + 6 + rnd.randint(0, 2), y, MG[3])
        for k in range(10):
            put(im, rnd.randint(3, 28), rnd.randint(2, 62), [CY[3], MG[3], (255, 255, 255, 255)][k % 3])
        # a displaced slice (glitch)
        sy = rnd.randint(10, 50)
        for y in range(sy, sy + 3):
            row = [im.getpixel((xx, y)) for xx in range(FW)]
            for xx in range(FW): im.putpixel(((xx + 3) % FW, y), row[xx])
        frames.append(im)
    return FW, FH, frames, [("loop", 0, 7)]


def blast_sheet():
    frames = []
    for f in range(7):
        im = img(48, 48)
        r = 4 + f * 3.4
        for y in range(48):
            for x in range(48):
                d = math.hypot(x - 24, y - 24)
                if d < r:
                    k = d / r
                    if f < 2: c = (255, 255, 255, 255) if k < 0.6 else MG[4]
                    elif k > 0.85: c = MG[3] if f < 5 else MG[1]
                    elif k > 0.65 and f < 5: c = CY[3] if (x + y + f) % 3 else CY[4]
                    elif f < 4 and k < 0.35: c = MG[5]
                    else: continue
                    if f >= 5 and h01(x, y, f) > 0.5: continue
                    put(im, x, y, c)
        frames.append(im)
    return 48, 48, frames, [("nh_blast", 0, 6)]


def warp_sheet():
    frames = []
    for f in range(8):
        im = img(24, 64)
        k = f / 7
        for y in range(64):
            if h01(y, f, 3) < 0.6 - k * 0.4:
                w = int(2 + 8 * math.sin(k * math.pi) * h01(y, f, 4))
                c = [CY[3], MG[3], (255, 255, 255, 255), CY[4]][int(h01(y, f, 5) * 4)]
                for dx in range(-w, w + 1, 2): put(im, 12 + dx, y, c)
        frames.append(im)
    return 24, 64, frames, [("nh_warp", 0, 7)]


def missile_sheet():
    frames = []
    for f in range(4):
        im = img(16, 8)
        rect(im, 4, 3, 8, 2, METAL[4]); rect(im, 4, 3, 8, 1, METAL[5]); put(im, 12, 3, RED[3]); put(im, 12, 4, RED[2])
        put(im, 5, 2, METAL[2]); put(im, 5, 5, METAL[2])
        for x in range(0, 4): put(im, x, 3 + (x + f) % 2, [MG[4], MG[3], (255, 255, 255, 255), MG[2]][(x + f) % 4])
        frames.append(im)
    return 16, 8, frames, [("nh_missile", 0, 3)]


# =========================================================================== build + previews
def save_sheet(name, fw, fh, frames, tags, ms=100, msmap=None):
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    cols = min(len(frames), 12); rows = (len(frames) + cols - 1) // cols; sc = 3 if fw <= 64 else 2
    pv = Image.new("RGBA", (cols * (fw + 2) * sc, rows * (fh + 2) * sc), (86, 86, 94, 255))
    for i, fr in enumerate(frames):
        cell = Image.new("RGBA", (fw, fh), (40, 40, 52, 255)); cell.alpha_composite(fr)
        pv.alpha_composite(cell.resize((fw * sc, fh * sc), Image.NEAREST), ((i % cols) * (fw + 2) * sc, (i // cols) * (fh + 2) * sc))
    pv.save(os.path.join(ART, "previews", f"neo_env_{name}.png"))
    if BUILD:
        fr = [{"ms": (msmap or {}).get(i, ms), "cels": {"art": f}} for i, f in enumerate(frames)]
        asebuild.build(name, fw, fh, ["art"], fr, tags)


def main():
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="): only = set(a[7:].split(","))
    want = lambda n: only is None or n in only
    if want("tiles"):
        save_sheet("tiles_neohallow", 16, 16, build_tiles(False), [("all", 0, 47)])
        save_sheet("tiles_neohallow_cyber", 16, 16, build_tiles(True), [("all", 0, 47)])
    if want("bg"):
        save_sheet("bg_neohallow_far", BW, BH, [build_far(f) for f in range(4)], [("loop", 0, 3)], ms=160)
        save_sheet("bg_neohallow_mid", BW, BH, [build_mid(f) for f in range(4)], [("loop", 0, 3)], ms=160)
        save_sheet("bg_neohallow_cyber_far", BW, BH, [build_far(f, True) for f in range(4)], [("loop", 0, 3)], ms=160)
        save_sheet("bg_neohallow_cyber_mid", BW, BH, [build_mid(f, True) for f in range(4)], [("loop", 0, 3)], ms=160)
    if want("props"):
        fw, fh, fr, tg = deco_sheet(); save_sheet("nh_deco", fw, fh, fr, tg, ms=140)
        fw, fh, fr, tg = term_sheet(); save_sheet("nh_term", fw, fh, fr, tg, ms=120)
        fw, fh, fr, tg = train_sheet(); save_sheet("nh_train", fw, fh, fr, tg, ms=80)
        fw, fh, fr, tg = portal_sheet(); save_sheet("nh_portal", fw, fh, fr, tg, ms=70)
    if want("fx"):
        fw, fh, fr, tg = blast_sheet(); save_sheet("fx_nh_blast", fw, fh, fr, tg, ms=60)
        fw, fh, fr, tg = warp_sheet(); save_sheet("fx_nh_warp", fw, fh, fr, tg, ms=90)
        fw, fh, fr, tg = missile_sheet(); save_sheet("fx_nh_missile", fw, fh, fr, tg, ms=60)


if __name__ == "__main__":
    main()
