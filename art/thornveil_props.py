"""Thornveil Wood props (all bottom-anchored unless noted). Each builder returns (w, h, frames[list of RGBA], tags)."""
import math
from PIL import Image
from thornveil_kit import (SOIL, BARK, MOSS, STONE, SPIRIT, RIBBON, BONE, THORN, DEEP, FOG, K, C, Pix, ramp_pick,
                           h01, bt, clamp, curve_pts, stroke, outline)

DIM = [C(h) for h in ("#0b0c0b", "#121411", "#1a1d17", "#23271f", "#2e3328", "#3b4133", "#4b523f")]   # shadowed bark
DMOSS = [C(h) for h in ("#0c1a14", "#12281c", "#1a3824", "#24492d", "#325e38")]


# ---------------------------------------------------------------- giant background trees (painted into the room's back layer)
def tree(v):
    w, h = 96, 240
    P = Pix(w, h)
    cx = w / 2
    for y in range(h):
        base = max(0, (y - h * 0.8) / (h * 0.2))
        tw = (26 if v != 1 else 30) * (1 + 1.1 * base ** 2)
        sway = (math.sin(y * 0.02 + v * 2) * 4 if v == 2 else math.sin(y * 0.01) * 1.5)
        for x in range(w):
            dx = x + 0.5 - (cx + sway)
            if abs(dx) > tw / 2:
                continue
            u = (dx + tw / 2) / tw
            grain = math.sin((dx * 0.8 + 6 * math.sin(y * 0.05 + x * 0.1)) * 1.1)
            vv = 0.72 - 0.6 * u + 0.12 * grain + 0.05 * math.sin(y * 0.3 + x)
            c = ramp_pick(DIM, vv, x, y)
            if abs(dx) > tw / 2 - 1:
                c = DIM[0]
            P.set(x, y, c)
        # moss running down the lit (left) side
        if 0.35 < math.sin(y * 0.045 + v) + 0.4 and y < h * 0.9:
            for k in range(3 + int(2 * math.sin(y * 0.2))):
                P.set(cx + sway - tw / 2 + 1 + k, y, DMOSS[3 - min(3, k)])
    # root flare fingers at the base
    for r in range(6):
        side = -1 if r % 2 else 1
        L = 14 + h01(v, r, 3) * 18
        for i in range(int(L)):
            t = i / L
            x = cx + side * (12 + i)
            y = h - 16 + t * t * 15 + (r // 2) * 2
            for k in range(max(1, int(4 * (1 - t)))):
                P.set(x, y + k, DIM[3] if k == 0 else DIM[1])
    # knots with hanging moss beards
    for kk in range(3):
        ky = 40 + kk * 55 + int(h01(v, kk, 1) * 20)
        side = -1 if (kk + v) % 2 else 1
        kx = cx + side * 10
        for dy in range(-3, 4):
            for dx in range(-4, 5):
                if dx * dx / 16 + dy * dy / 9 <= 1:
                    P.set(kx + dx, ky + dy, DIM[4] if dy < 0 and dx < 0 else DIM[1])
        ml = 18 + int(h01(v, kk, 4) * 26)
        for yy in range(ml):
            wdt = max(1, int(4 * (1 - yy / ml)))
            for xx in range(-wdt // 2, wdt - wdt // 2):
                if h01(int(kx) + xx, ky + yy, 7) < 0.9 - yy / ml * 0.45:
                    P.set(kx + xx + int(1.5 * math.sin(yy * 0.2)), ky + 3 + yy, DMOSS[2] if yy < ml * 0.5 else DMOSS[1])
    if v == 1:        # a hollow with a pale ribbon tied above it
        hy = 150
        for dy in range(-12, 13):
            for dx in range(-6, 7):
                if dx * dx / 36 + dy * dy / 144 <= 1:
                    P.set(cx + dx, hy + dy, C("#050706"))
                elif dx * dx / 56 + dy * dy / 190 <= 1:
                    P.set(cx + dx, hy + dy, DIM[4] if dx < 0 else DIM[2])
        for x in range(int(cx - 14), int(cx + 15)):
            P.set(x, 118, RIBBON[2]); P.set(x, 119, RIBBON[1])
        for yy in range(22):
            x = cx + 9 + math.sin(yy * 0.3) * 2
            P.set(x, 120 + yy, RIBBON[2] if yy < 12 else RIBBON[1]); P.set(x + 1, 120 + yy, RIBBON[1])
    if v == 2:        # a spirit-lit knot: veins of green light in the bark
        ky = 120
        for i in range(30):
            a = i * 0.7
            x = cx + math.sin(a) * 5 + 2
            P.set(x, ky + i * 1.5, SPIRIT[2] if i % 3 else SPIRIT[3])
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            P.set(cx + 2 + dx, ky + 20 + dy, SPIRIT[4] if (dx, dy) == (0, 0) else SPIRIT[3])
    return P.img


def trees():
    fr = [tree(v) for v in range(3)]
    return 96, 240, fr, [("v0", 0, 0), ("v1", 1, 1), ("v2", 2, 2)]


# ---------------------------------------------------------------- antlered idols
def antler(P, x0, y0, side, s=1.0, col=BONE):
    """A branching antler from (x0,y0) growing up and outward; side = -1 left / 1 right."""
    beam = [(x0, y0), (x0 + side * 5 * s, y0 - 7 * s), (x0 + side * 7 * s, y0 - 15 * s), (x0 + side * 6 * s, y0 - 23 * s)]
    cp = curve_pts(beam, 8)
    for i, (x, y) in enumerate(cp):
        t = i / (len(cp) - 1)
        P.set(math.floor(x), math.floor(y), col[4] if t > 0.7 else col[3])
        if t < 0.5:
            P.set(math.floor(x) + side, math.floor(y), col[2])
    for (t, L, a) in ((0.3, 6, -0.9), (0.55, 7, -0.6), (0.8, 5, -0.3)):
        x, y = cp[int(t * (len(cp) - 1))]
        for i in range(int(L * s)):
            P.set(math.floor(x + side * i * 0.55), math.floor(y - i * 0.9), col[4] if i < L * s - 1 else col[5])
    return cp


def ribbon(P, x, y, L, ph, fl=0.0):
    for i in range(L):
        xx = x + math.sin(i * 0.28 + ph) * (1.2 + i * 0.06) + fl * i * 0.25
        c = RIBBON[3] if i < 3 else RIBBON[2] if i < L * 0.7 else RIBBON[1]
        P.set(math.floor(xx), y + i, c)
        if i < L - 3:
            P.set(math.floor(xx) + 1, y + i, RIBBON[1] if i % 4 else c)


SKULL = ["...####.....",
         "..######....",
         ".##oo####...",
         ".#oo#######.",
         "..#########w",
         "...###.####.",
         "....#...##.."]


def skull(P, x0, y0, glow=False):
    for j, row in enumerate(SKULL):
        for i, ch in enumerate(row):
            if ch == "#":
                P.set(x0 + i, y0 + j, BONE[5] if j <= 1 and i < 7 else BONE[4] if j <= 3 else BONE[3] if j == 4 else BONE[2])
            elif ch == "w":
                P.set(x0 + i, y0 + j, BONE[3])
            elif ch == "o":
                P.set(x0 + i, y0 + j, (SPIRIT[4] if glow else BONE[1]) if (i, j) == (3, 3) else K)


def idol(v, f):
    w, h = 40, 64
    P = Pix(w, h)
    cx = 20
    if v == 0:      # a carved post with a deer skull
        for y in range(28, h):
            for dx in range(-4, 5):
                vv = 0.75 - (dx + 4) / 9 * 0.65
                P.set(cx + dx, y, ramp_pick(BARK[1:5], vv, cx + dx, y))
            if y % 7 == 0:
                for dx in range(-4, 5):
                    P.set(cx + dx, y, BARK[1])
        for y in range(h - 5, h):     # moss at the foot
            for dx in range(-5, 6):
                if abs(dx) < 5 - (h - 1 - y) * 0.6:
                    P.set(cx + dx, y, MOSS[4] if y == h - 5 else MOSS[3])
        sy = 26
    else:           # a cairn of mossy stones
        stones = [(0, 58, 9, 5), (-2, 50, 7, 4), (2, 43, 6, 4), (0, 37, 5, 3)]
        for (dx0, yc, rx, ry) in stones:
            for y in range(yc - ry, yc + ry + 1):
                for x in range(cx + dx0 - rx, cx + dx0 + rx + 1):
                    q = ((x + .5 - cx - dx0) / rx) ** 2 + ((y + .5 - yc) / ry) ** 2
                    if q <= 1:
                        vv = 0.6 - 0.4 * (x - cx - dx0) / rx - 0.4 * (y - yc) / ry
                        P.set(x, y, ramp_pick(STONE[:5], vv, x, y))
                        if y < yc - ry + 2 and h01(x, y, 3) < 0.6:
                            P.set(x, y, MOSS[4])
        sy = 33
    # the skull (profile, snout to the right) + antlers
    skull(P, cx - 5, sy - 4, glow=(v == 1))
    antler(P, cx - 3, sy - 3, -1, 0.9)
    antler(P, cx + 1, sy - 3, 1, 0.9)
    # ribbons hanging from the antlers, fluttering
    ph = f * 1.57
    ribbon(P, cx - 8, sy - 14, 18, ph, 0.1 * math.sin(ph))
    ribbon(P, cx + 7, sy - 12, 22, ph + 1.2, 0.1 * math.sin(ph + 1))
    if v == 0:
        ribbon(P, cx - 3, sy + 6, 12, ph + 2.2)
    return outline(P.img, K)


def idols():
    fr, tags = [], []
    for v in range(2):
        a = len(fr)
        fr += [idol(v, f) for f in range(4)]
        tags.append((f"v{v}", a, a + 3))
    return 40, 64, fr, tags


# ---------------------------------------------------------------- ribbon sapling, fern, glowing shrooms, rope-root vine
def ribbons_prop(f):
    w, h = 32, 48
    P = Pix(w, h)
    stem = [(14, 47), (13, 34), (15, 20), (19, 9)]
    stroke(P, stem, 1.4, 0.6, lambda t, lit: BARK[4] if lit > 0.2 else BARK[3] if lit > -0.3 else BARK[2])
    for (bx, by, s) in ((13, 30, -1), (15, 22, 1)):
        for i in range(6):
            P.set(bx + s * i, by - i // 2, BARK[3])
    ph = f * 1.57
    ribbon(P, 18, 10, 26, ph, 0.25)
    ribbon(P, 15, 18, 20, ph + 1.6, 0.2)
    ribbon(P, 8, 27, 14, ph + 0.8, -0.1)
    for x in range(10, 19):
        P.set(x, 47, MOSS[3]); P.set(x, 46, MOSS[4] if h01(x, 1, 1) < 0.6 else None)
    return outline(P.img, K)


def fern():
    P = Pix(32, 20)
    for k, (ang, L) in enumerate(((-2.4, 13), (-2.0, 15), (-1.57, 12), (-1.1, 15), (-0.7, 12))):
        x0, y0 = 16, 19
        for i in range(L):
            t = i / L
            a = ang + 0.5 * t * (1 if ang > -1.57 else -1)
            x = x0 + math.cos(a) * i
            y = y0 + math.sin(a) * i
            P.set(x, y, MOSS[5] if t < 0.8 else MOSS[6])
            if i % 2 == 0 and 0.1 < t < 0.9:     # leaflets
                for s in (-1, 1):
                    P.set(x + math.cos(a + s * 1.2) * 2, y + math.sin(a + s * 1.2) * 2, MOSS[4])
    return outline(P.img, K)


def shroom():
    P = Pix(24, 20)
    for (x, hh, r) in ((6, 8, 3), (12, 12, 4), (17, 6, 2.5)):
        for y in range(19 - hh, 20):
            P.set(x, y, BONE[4]); P.set(x + 1, y, BONE[2])
        cy = 19 - hh
        for yy in range(-3, 1):
            for xx in range(-int(r) - 1, int(r) + 2):
                if (xx / (r + 0.5)) ** 2 + (yy / 3.2) ** 2 <= 1:
                    c = SPIRIT[5] if yy == -3 else SPIRIT[4] if yy == -2 else SPIRIT[3] if yy == -1 else SPIRIT[2]
                    P.set(x + xx, cy + yy, c)
        for xx in range(-int(r), int(r) + 1, 2):
            P.set(x + xx, cy + 1, SPIRIT[1])
    return outline(P.img, K)


def vine(f):
    """A rope-root hanging from the ceiling (top-anchored), swaying."""
    P = Pix(16, 64)
    ph = f * 1.57
    pts = [(8, 0), (8 + 2 * math.sin(ph), 22), (8 + 3 * math.sin(ph + 0.6), 44), (8 + 3.5 * math.sin(ph + 1.1), 62)]
    stroke(P, pts, 1.2, 0.7, lambda t, lit: BARK[4] if lit > 0.2 else BARK[3] if lit > -0.4 else BARK[2])
    cp = curve_pts(pts, 8)
    for i in range(3, len(cp), 9):
        x, y = cp[i]
        P.set(x - 1, y, MOSS[4]); P.set(x - 2, y + 1, MOSS[3])
    return outline(P.img, K)


def small_props():
    return {
        "tv_ribbons": (32, 48, [ribbons_prop(f) for f in range(4)], [("loop", 0, 3)]),
        "tv_fern": (32, 20, [fern()], [("idle", 0, 0)]),
        "tv_shroom": (24, 20, [shroom()], [("idle", 0, 0)]),
        "tv_vine": (16, 64, [vine(f) for f in range(4)], [("loop", 0, 3)]),
    }


# ---------------------------------------------------------------- spore pod (top-anchored: hangs from a ceiling tile)
def pod(state, f):
    P = Pix(24, 32)
    # stalk
    sw = {"shake": [-1, 1, -1, 1][f % 4], "burst": 0}.get(state, 0)
    for y in range(0, 10):
        P.set(12 + (sw if y > 5 else 0), y, BARK[3]); P.set(13 + (sw if y > 5 else 0), y, BARK[2])
    if state == "empty":
        for (x, y) in ((11, 10), (13, 11), (12, 12), (14, 10)):
            P.set(x, y, BARK[3])
        return outline(P.img, K)
    grow = 1.0
    if state == "regrow":
        grow = 0.4 + 0.15 * f
    if state == "burst":
        grow = max(0, 1 - f * 0.34)
    pulse = 1 + (0.06 * math.sin(f * 1.57) if state == "idle" else 0)
    cx, cy = 12.5 + sw, 17
    rx, ry = 6 * grow * pulse, 7.5 * grow * pulse
    if rx > 0.8:
        for y in range(32):
            for x in range(24):
                dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
                q = dx * dx + dy * dy
                if q <= 1:
                    vv = 0.6 - 0.45 * dx - 0.35 * dy
                    c = ramp_pick(MOSS[1:6], vv, x, y)
                    # glowing spore vents
                    if (abs(dx) < 0.25 and dy > -0.6) or (h01(x, y, 5) < 0.08):
                        c = SPIRIT[3] if state != "idle" or f % 2 else SPIRIT[2]
                    P.set(x, y, c)
    if state == "burst":
        for k in range(10 + f * 6):
            a = h01(k, f, 1) * 6.28
            r = 3 + f * 3 + h01(k, f, 2) * 4
            P.set(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8, SPIRIT[3] if k % 3 else SPIRIT[4])
    return outline(P.img, K)


def pods():
    fr, tags = [], []
    for st, n in (("idle", 4), ("shake", 4), ("burst", 3), ("empty", 1), ("regrow", 4)):
        a = len(fr)
        fr += [pod(st, f) for f in range(n)]
        tags.append((st, a, a + n - 1))
    return 24, 32, fr, tags


# ---------------------------------------------------------------- thorn hatch (the lattice in TV7's floor), 48x16
def hatch(f):
    P = Pix(48, 16)
    open_k = f / 5.0
    # woven thorny branches, pulled apart toward both sides as it opens
    for k in range(7):
        y0 = 2 + (k % 3) * 4
        for x in range(48):
            side = -1 if x < 24 else 1
            dxo = side * open_k * 26
            xx = x + dxo
            if not (0 <= xx < 48):
                continue
            if open_k > 0 and abs(x - 24) < open_k * 26:
                continue
            y = y0 + 1.5 * math.sin(x * 0.35 + k * 1.3)
            P.set(xx, y, THORN[3] if k % 2 else THORN[2])
            P.set(xx, y + 1, THORN[1])
            if x % 5 == k % 5:
                P.set(xx, y - 1, THORN[4]); P.set(xx + (1 if k % 2 else -1), y - 2, THORN[5])
    for x in range(0, 48, 11):     # knotted binding cords (pale)
        if open_k < 0.2:
            for y in range(3, 12):
                P.set(x + 5, y, RIBBON[2] if y % 3 else RIBBON[3])
    return outline(P.img, K)


def hatches():
    fr = [hatch(f) for f in range(6)]
    return 48, 16, fr, [("closed", 0, 0), ("open", 0, 5)]


# ---------------------------------------------------------------- hazard tiles: brambles '(' and thorn walls ')'  (24x24, bottom-centred on a tile)
def bramble(v):
    P = Pix(24, 24)
    rnd = [h01(v, k, 3) for k in range(20)]
    stems = [(5 + v, 13 + int(rnd[0] * 5), -0.25), (11, 17 + int(rnd[1] * 4), 0.05), (17 - v, 12 + int(rnd[2] * 5), 0.3)]
    for i, (x0, hg, lean) in enumerate(stems):
        pts = [(x0, 23), (x0 + lean * hg * 0.5 + (1 - i) * 1.5, 23 - hg * 0.55), (x0 + lean * hg + (i - 1) * 2, 23 - hg)]
        cp = curve_pts(pts, 8)
        for k, (x, y) in enumerate(cp):
            t = k / max(1, len(cp) - 1)
            P.set(x, y, THORN[3] if t < 0.75 else THORN[4])
            if t < 0.5:
                P.set(x + 1, y, THORN[2])
        tx, ty = cp[-1]
        P.set(tx, ty - 1, THORN[5])
        for j in range(4):
            x, y = cp[int((0.2 + j * 0.18) * (len(cp) - 1))]
            s = 1 if (i + j) % 2 else -1
            P.set(x + s * 2, y - 1, THORN[4]); P.set(x + s * 3, y - 2, THORN[5])
            P.set(x + s, y, THORN[3])
    # a tangle of dark leaves at the base + a few blood-red berries
    for x in range(2, 22):
        for y in range(19, 24):
            if h01(x, y, v + 9) < 0.55 - (23 - y) * 0.06:
                P.set(x, y, DMOSS[2] if h01(x, y, 3) < 0.5 else THORN[2])
    for k in range(3):
        P.set(4 + int(rnd[5 + k] * 16), 17 + int(rnd[9 + k] * 4), C("#8a1c24"))
    return outline(P.img, K)


def thornwall(part, v):
    """A column of woven thorn vines filling a 16px-wide cell (drawn 24 wide so thorns bristle out)."""
    P = Pix(24, 24)
    y0 = 8 if part == "top" else 8
    for k in range(4):
        ph = k * 1.6 + v
        for y in range(8, 24):
            x = 12 + 5.5 * math.sin(y * 0.38 + ph) * (0.9 if k % 2 else 1)
            P.set(x, y, THORN[3] if k % 2 else THORN[2])
            P.set(x + 1, y, THORN[1])
            if (y + k * 3) % 6 == 0:
                s = 1 if x < 12 else -1
                P.set(x - s * 2, y - 1, THORN[4]); P.set(x - s * 3, y - 2, THORN[5])
    for y in range(8, 24):
        for x in range(6, 18):
            if not P.on(x, y) and h01(x, y, v + 3) < 0.4:
                P.set(x, y, THORN[1])
    if part == "top":    # a pale binding cord where the thorns are knotted to the ceiling
        for x in range(5, 19):
            P.set(x, 9, RIBBON[2]); P.set(x, 10, RIBBON[1])
    if part == "bot":
        for x in range(4, 20):
            if h01(x, 1, 2) < 0.7:
                P.set(x, 23, DMOSS[3]); P.set(x, 22, DMOSS[2] if h01(x, 3, 3) < 0.5 else None)
    return outline(P.img, K)


def hazards():
    fr = [bramble(v) for v in range(3)] + [thornwall("top", 0), thornwall("mid", 0), thornwall("mid", 1), thornwall("bot", 0)]
    return 24, 24, fr, [("bramble", 0, 2), ("wall_top", 3, 3), ("wall_mid", 4, 5), ("wall_bot", 6, 6)]


# ---------------------------------------------------------------- fog bank texture (tileable in x, soft alpha)
def fog():
    from envlib import fbm
    w, h = 128, 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            n = fbm(x, y, 32, 16, 4, w, 3)
            e = math.sin(y / h * math.pi) ** 0.8
            a = clamp((n - 0.28) * 1.9) * e
            lvl = int(a * 4 + bt(x, y) * 0.99)
            if lvl <= 0:
                continue
            c = FOG[min(3, lvl - 1)]
            px[x, y] = (c[0], c[1], c[2], [0, 70, 110, 150, 185][min(4, lvl)])
    return w, h, [img], [("loop", 0, 0)]


PROPS = {"tv_tree": trees, "tv_idol": idols, "tv_pod": pods, "tv_hatch": hatches, "tv_hazards": hazards, "tv_fog": fog}
