"""Room-themed parallax for the Cold Forge (v17 AREA, lead review pass): each part of the forge reads as itself.
Sheets cfa_bg_<theme> (512x216, tags `far` = opaque, `mid` = transparent silhouettes with a cool rim). Themes:
  flue     CF1-CF3   soot shafts receding upward, iron bands, a warm flue glow far above, buckets on chains
  racks    CF4 CF9 CF13   arched bays of unfinished blades, grey vent shafts, great racks in the mid-ground
  cistern  CF5 CF10  a vaulted cistern hall mirrored in still black water, pale vent light, steam
  bellows  CF6       rows of great bellows hanging in the dark, distant coal glints, piston beams
  court    CF7 CF11 CF12   a vaulted court: a round cold grate-window, racks of great hammers, columns
  hearth   CF8       the furnace hall: huge courses, pillars, embers drifting up from below
Cold and dark, values lifted a few steps over the first pass so the depth reads under the game's lighting; warm
accents only where fire is (the flue, coal glints, embers). Called from gen_forge_env.py (build_all).
"""
import math, os
import numpy as np
from PIL import Image
from forge_env_lib import *   # noqa

W, H = 512, 216
SKY = ("#0b0f15", "#131822")            # far base, top -> bottom


def base_far(seed):
    p = Cv(W, H, base="#0e1219")
    p.vgrad(p.rectm(0, 0, W, H), "#0a0d12", "#18202b", 0, H)
    return p


def wall(p, mask, bw=16, bh=8, cols=("#18202b", "#1b2330", "#1e2734"), mortar="#0e1219", seed=0, soot=0.8):
    bricks(p, mask, bw=bw, bh=bh, cols=cols, mortar=mortar, seed=seed, soot=soot, wrap=True, lip=1.1)


def haze(p, y, h, col="#2d3849", k=0.35):
    p.add_light(np.clip(1 - np.abs(p.yy - y) / h, 0, 1), col, k)


def arch_poly(cx, base, w, top, spring):
    return [(cx - w / 2, base), (cx - w / 2, spring)] + [(cx + (w / 2) * math.cos(math.radians(a)), spring - (spring - top) * math.sin(math.radians(a))) for a in range(180, -1, -10)] + [(cx + w / 2, base)]


def rim(p, mask, col="#4f6079", side=1):
    """a 1px cool rim on the lit (left) side of a silhouette, and a softer second pixel"""
    e = mask & ~np.roll(mask, side, axis=1)
    p.fill(e, col)


def ember_dots(p, n, region, seed, cols=("#a3531f", "#c96a22", "#e88a30")):
    x0, y0, x1, y1 = region
    for i in range(n):
        x, y = x0 + hh(i, 1, seed) * (x1 - x0), y0 + hh(i, 2, seed) * (y1 - y0)
        p.px(x, y, cols[i % len(cols)])


def hanging_chain(p, x, y0, y1, col="#18202b", hi="#364356", hook=True):
    chain(p, (x, y0), (x, y1), col=col, hi=hi)
    if hook:
        p.line((x, y1), (x, y1 + 3), hi); p.line((x, y1 + 3), (x + 3, y1 + 5), hi); p.line((x + 3, y1 + 5), (x + 4, y1 + 2), hi)


def bellows_shape(p, cx, top, w, h, col="#141213", rimc="#3a2b26", pleat="#0b0a0b"):
    pts = []
    for i in range(21):
        t = i / 20
        hw = (w / 2) * (0.35 + 0.65 * math.sin(math.pi * min(1, 0.12 + t * 0.88)))
        pts.append((cx - hw, top + t * h))
    m = p.poly(pts + [(2 * cx - a, b) for a, b in reversed(pts)])
    p.fill(m, col)
    for j in range(1, 7):
        yy = top + j * h / 7
        p.fill(p.rectm(cx - w / 2, yy, cx + w / 2, yy + 1) & m, pleat)
    rim(p, m, rimc)
    p.fill(p.poly([(cx - 2, top + h - 1), (cx + 2, top + h - 1), (cx + 1, top + h + 9), (cx - 1, top + h + 9)]), col)
    p.fill(p.rectm(cx - w * 0.45, top - 3, cx + w * 0.45, top), "#0e1219")
    return m


# ------------------------------------------------------------------ the flue (CF1-CF3)
def flue():
    p = base_far(1)
    # far: a forest of soot chimneys receding, each lit faintly from above; one carries a warm glow far up
    for i, (x, w, shade) in enumerate(((20, 46, 0.55), (96, 30, 0.42), (150, 54, 0.6), (240, 36, 0.45), (300, 58, 0.62), (390, 32, 0.4), (440, 50, 0.58))):
        m = p.rectm(x, 0, x + w, H)
        wall(p, m, bw=10, bh=5, cols=("#131822", "#18202b", "#1b2330"), mortar="#0a0d12", seed=10 + i, soot=1.1)
        p.mul(np.clip(0.55 + shade * 0.7 - p.yy / 600, 0.3, 1.1), m)
        p.fill(p.rectm(x, 0, x + 1, H), "#2d3849"); p.fill(p.rectm(x + w - 1, 0, x + w, H), "#06080b")
        for y in range(20 + i * 13, H, 54):
            p.fill(p.rectm(x - 1, y, x + w + 1, y + 3), "#0a0d12"); p.fill(p.rectm(x - 1, y, x + w + 1, y + 1), "#364356")
    # the warm one: the far flue under a hearth
    p.shaft(318, 340, 306, 352, 0, 216, "#a3531f", strength=0.22, soft=10, fade=0.85)
    p.fill(p.rectm(318, 0, 340, 6), "#c96a22")
    for x in range(318, 340, 4):
        p.fill(p.rectm(x, 0, x + 2, 7), "#141213")
    haze(p, 150, 70, "#252f3e", 0.4)
    ember_dots(p, 10, (310, 8, 350, 120), 3, ("#7c401d", "#a3531f"))
    far = p.to_image(0.4, alpha=False)
    q = Cv(W, H)
    # mid: big iron flue pipes, diagonal stays, buckets on chains, a bracket ledge
    for x0, x1 in ((60, 92), (330, 356)):
        m = q.rectm(x0, 0, x1, H)
        plates(q, m, pw=x1 - x0, ph=18, cols=("#0e1219", "#10151d", "#0c1016"), lit="#252f3e", seed=x0)
        q.mul(1 - np.clip(np.abs(q.xx - (x0 + x1) / 2) / ((x1 - x0) / 2), 0, 1) ** 2 * 0.6, m)
        rim(q, m, "#4f6079")
        for y in range(30, H, 60):
            q.fill(q.rectm(x0 - 2, y, x1 + 2, y + 4), "#0a0d12"); q.fill(q.rectm(x0 - 2, y, x1 + 2, y + 1), "#415066")
    q.line((92, 120), (150, 60), "#0e1219"); q.line((92, 121), (150, 61), "#0e1219"); q.line((92, 119), (150, 59), "#364356")
    for x, ln in ((180, 90), (240, 60), (460, 110)):
        hanging_chain(q, x, 0, ln, "#10151d", "#364356", hook=False)
        b = q.poly([(x - 7, ln), (x + 7, ln), (x + 5, ln + 12), (x - 5, ln + 12)]); q.fill(b, "#141213"); rim(q, b, "#4f6079")
        q.fill(q.rectm(x - 7, ln, x + 7, ln + 1), "#364356")
    return far, q.to_image(0.3)


# ------------------------------------------------------------------ the hall of racks (CF4, CF9, CF13)
def racks():
    p = base_far(2)
    p.vgrad(p.rectm(0, 0, W, H), "#0a0d12", "#1b2330", 0, H)
    for i, bx in enumerate(range(0, 512, 64)):
        a = p.poly(arch_poly(bx + 32, 176, 52, 30, 66))
        p.fill(a, "#10151d")
        blade_rack(p, bx + 10, bx + 54, 72, 166, scale=1.0, cols=("#0e1219", "#1e2734", "#1b2330", "#2d3849", "#0e1219"), glint="#415066", seed=i + 10, fill=0.9, posts=False)
        e = a & ~np.roll(a, 1, axis=0); p.fill(e, "#2d3849")
        p.fill(p.rectm(bx + 58, 14, bx + 70, 178), "#0e1219"); p.fill(p.rectm(bx + 58, 14, bx + 59, 178), "#252f3e")
        p.fill(p.rectm(bx + 55, 174, bx + 73, 180), "#131822"); p.fill(p.rectm(bx + 55, 174, bx + 73, 175), "#364356")
    p.fill(p.rectm(0, 178, W, H), "#10151d")
    for x in range(0, W, 32):
        p.fill(p.rectm(x, 178, x + 1, H), "#0a0d12")
    p.fill(p.rectm(0, 0, W, 14), "#06080b")
    for (x, w) in ((88, 16), (344, 16)):   # grey light falling from ceiling vents: the focal points
        p.shaft(x, x + w, x - 26, x + w + 30, 14, 200, "#62748f", strength=0.3, soft=12, fade=0.7)
        p.fill(p.rectm(x, 12, x + w, 15), "#4f6079")
        for xx in range(x + 1, x + w, 3):
            p.fill(p.rectm(xx, 12, xx + 1, 15), "#131822")
    haze(p, 132, 70, "#252f3e", 0.35)
    far = p.to_image(0.35, alpha=False)
    q = Cv(W, H)
    for (x0, x1, y0, sc, sd) in ((20, 170, 96, 2.2, 3), (300, 440, 104, 2.2, 4)):
        blade_rack(q, x0, x1, y0, 212, scale=sc, cols=("#06080b", "#18202b", "#141a24", "#4f6079", "#0a0d12"), glint="#7c8ea8", seed=sd)
    q.fill(q.rectm(0, 210, W, H), "#0a0d12")
    for x, ln in ((200, 64), (226, 40), (476, 80)):
        hanging_chain(q, x, 0, ln, "#0e1219", "#415066")
    return far, q.to_image(0.3)


# ------------------------------------------------------------------ the quench cisterns (CF5, CF10)
def cistern():
    p = base_far(3)
    wl = 150   # the water line in the far hall
    hall = p.rectm(0, 0, W, wl)
    wall(p, hall, bw=16, bh=8, cols=("#141a24", "#18202b", "#1b2330"), mortar="#0b0f15", seed=31, soot=0.6)
    for i, cx in enumerate(range(32, 512, 96)):   # vaulted arches marching away
        a = p.poly(arch_poly(cx + 16, wl, 70, 40, 84))
        p.fill(a, "#0b0f15")
        p.fill(a & ~np.roll(a, 2, axis=0), "#364356")
        p.fill(p.rectm(cx + 50, 20, cx + 64, wl), "#10151d"); p.fill(p.rectm(cx + 50, 20, cx + 51, wl), "#2d3849")
        p.eglow(cx + 16, 70, 18, 30, "#2d3849", 0.45, mask=a)   # a pale opening far off in each bay
    p.fill(p.rectm(0, 0, W, 16), "#06080b")
    p.shaft(250, 266, 228, 290, 16, wl, "#7c8ea8", strength=0.26, soft=12, fade=0.6)
    p.fill(p.rectm(250, 13, 266, 16), "#62748f")
    # still black water: the hall mirrored, darker, broken by a few slow ripple lines
    water = p.rectm(0, wl, W, H)
    refl = p.c[max(0, 2 * wl - H):wl][::-1].copy()
    p.c[wl:H] = refl[:H - wl] * 0.42 + hexc("#06080b") * 0.58; p.a |= water
    for i in range(14):
        y = wl + 4 + hh(i, 1, 7) * (H - wl - 8); x = hh(i, 2, 7) * W
        p.fill(p.rectm(x, y, x + 10 + hh(i, 3, 7) * 30, y + 1) & water, "#2b3c45")
    p.fill(p.rectm(0, wl, W, wl + 1), "#415066")
    haze(p, wl - 6, 22, "#2b3c45", 0.5)
    far = p.to_image(0.35, alpha=False)
    q = Cv(W, H)
    # mid: riveted quench tanks and a pipe gantry, their tops caught by the cold light
    for x0, w, h in ((40, 90, 70), (300, 120, 86)):
        m = q.rectm(x0, H - h, x0 + w, H)
        plates(q, m, pw=18, ph=12, cols=("#0e1219", "#10151d", "#0c1016"), lit="#252f3e", seed=x0)
        q.fill(q.rectm(x0 - 3, H - h - 3, x0 + w + 3, H - h + 1), "#18202b"); q.fill(q.rectm(x0 - 3, H - h - 3, x0 + w + 3, H - h - 2), "#62748f")
        rim(q, m, "#415066")
    q.fill(q.rectm(0, 40, W, 45), "#0a0d12"); q.fill(q.rectm(0, 40, W, 41), "#364356")
    for x in range(10, W, 46):
        q.fill(q.rectm(x, 45, x + 3, 70), "#0e1219")
    for x in (170, 210, 470):
        q.fill(q.rectm(x, 45, x + 6, 216), "#0e1219"); rim(q, q.rectm(x, 45, x + 6, 216), "#2d3849")
    return far, q.to_image(0.3)


# ------------------------------------------------------------------ the bellows gallery (CF6)
def bellows():
    p = base_far(4)
    wall(p, p.rectm(0, 0, W, H), bw=20, bh=10, cols=("#10151d", "#131822", "#141a24"), mortar="#0a0d12", seed=41, soot=1.0)
    p.mul(np.clip(1.25 - p.yy / 300, 0.5, 1.2))
    p.fill(p.rectm(0, 0, W, 18), "#06080b"); p.fill(p.rectm(0, 18, W, 20), "#252f3e")
    # far rows of bellows hanging in the dark, smaller and greyer with distance
    for i, (x, top, w, h, k) in enumerate(((40, 30, 26, 52, 0.55), (120, 34, 22, 44, 0.45), (200, 28, 30, 58, 0.6), (290, 36, 20, 40, 0.42), (360, 30, 28, 54, 0.58), (450, 34, 22, 46, 0.48))):
        for dx in (-8, 8):
            chain(p, (x + dx, 20), (x + dx, top), col="#18202b", hi="#2d3849")
        m = bellows_shape(p, x, top, w, h, col="#1d1a1b", rimc="#3a3328", pleat="#141213")
        p.mul(np.full((H, W), 1.0 + k * 0.7, np.float32), m)
        rim(p, m, "#4f6079")
    # the hearth grates in the far floor: coal glints still alive under the ash
    p.fill(p.rectm(0, 184, W, H), "#0e1219"); p.fill(p.rectm(0, 184, W, 185), "#2d3849")
    for gx in (70, 230, 400):
        p.fill(p.rectm(gx, 186, gx + 40, 190), "#06080b")
        for x in range(gx + 1, gx + 40, 4):
            p.fill(p.rectm(x, 186, x + 2, 190), "#2a1a14")
        p.eglow(gx + 20, 188, 26, 6, "#7c401d", 0.5)
        ember_dots(p, 6, (gx + 4, 186, gx + 36, 189), gx, ("#a3531f", "#e88a30"))
    haze(p, 150, 60, "#252f3e", 0.3)
    far = p.to_image(0.35, alpha=False)
    q = Cv(W, H)
    # mid: piston beams and a great walking beam that pumps the bellows, chains, a near bellows silhouette
    beam = q.poly([(0, 60), (W, 52), (W, 60), (0, 68)]); plates(q, beam, pw=40, ph=8, seed=5); rim(q, beam & ~np.roll(beam, 1, axis=0), "#4f6079")
    q.fill(beam & ~np.roll(beam, 1, axis=0), "#4f6079")
    for x in (100, 360):
        m = q.rectm(x, 64, x + 10, H); q.fill(m, "#0e1219"); rim(q, m, "#364356")
        q.fill(q.ellm(x + 5, 64, 8, 8), "#131822"); q.fill(q.ellm(x + 5, 64, 3, 3), "#4f6079")
    bm = bellows_shape(q, 250, 90, 46, 92, col="#100e0f", rimc="#4e3829", pleat="#0b0a0b")
    for dx in (-14, 14):
        chain(q, (250 + dx, 0), (250 + dx, 88), col="#10151d", hi="#364356")
    return far, q.to_image(0.3)


# ------------------------------------------------------------------ the anvil court (CF7, CF11, CF12)
def court():
    p = base_far(5)
    wall(p, p.rectm(0, 0, W, H), bw=24, bh=12, cols=("#131822", "#18202b", "#151b26"), mortar="#0a0d12", seed=51, soot=0.7)
    p.mul(np.clip(1.2 - p.yy / 360, 0.6, 1.15))
    # a round grate-window high in the court: the cold light's source (focal point), its grate a crown of bars
    cx, cy, r = 256, 96, 36
    win = p.ellm(cx, cy, r, r)
    p.fill(win, "#364356"); p.eglow(cx, cy, r, r, "#8f9aa8", 0.55, mask=win)
    for a in range(0, 180, 18):
        dx, dy = math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r
        p.line((cx - dx, cy - dy), (cx + dx, cy + dy), "#0e1219")
    p.fill(p.ellm(cx, cy, 8, 8), "#0e1219")
    ring = p.ellm(cx, cy, r + 5, r + 5) & ~win; p.fill(ring, "#18202b"); p.fill(ring & (p.yy < cy), "#2d3849")
    p.shaft(cx - 24, cx + 24, cx - 70, cx + 70, cy + r, 210, "#62748f", strength=0.2, soft=20, fade=0.7)
    # tall columns and, between them, wall racks of great hammers
    for x in (60, 140, 372, 452):
        m = p.rectm(x, 0, x + 18, H); p.fill(m, "#10151d"); p.fill(p.rectm(x, 0, x + 1, H), "#2d3849")
        p.fill(p.rectm(x - 3, 182, x + 21, 190), "#18202b"); p.fill(p.rectm(x - 3, 182, x + 21, 183), "#415066")
    for x0 in (82, 394):
        p.fill(p.rectm(x0, 100, x0 + 54, 104), "#18202b"); p.fill(p.rectm(x0, 100, x0 + 54, 101), "#364356")
        for k, x in enumerate(range(x0 + 4, x0 + 52, 8)):
            L = 46 + (k % 3) * 8
            p.fill(p.rectm(x, 104, x + 2, 104 + L), "#252f3e")
            p.fill(p.rectm(x - 3, 104 + L, x + 5, 104 + L + 6), "#1e2734"); p.fill(p.rectm(x - 3, 104 + L, x + 5, 104 + L + 1), "#415066")
    p.fill(p.rectm(0, 190, W, H), "#10151d"); p.fill(p.rectm(0, 190, W, 191), "#364356")
    haze(p, 160, 50, "#252f3e", 0.3)
    far = p.to_image(0.35, alpha=False)
    q = Cv(W, H)
    # mid: an arcade of heavy arches, chains with great tongs
    for x0 in (0, 256):
        outer = q.rectm(x0, 0, x0 + 256, 44)
        hole = q.poly(arch_poly(x0 + 128, 44, 230, 10, 34))
        m = outer & ~hole
        wall(q, m, bw=16, bh=8, cols=("#0a0d12", "#0c1016", "#0e1219"), mortar="#05070a", seed=x0 + 3, soot=0.5)
        q.fill(m & ~np.roll(m, -1, axis=0) & q.rectm(0, 8, W, 46), "#364356")
        q.fill(q.rectm(x0 + 8, 0, x0 + 18, H), "#0a0d12"); rim(q, q.rectm(x0 + 8, 0, x0 + 18, H), "#364356")
    for x, ln in ((120, 120), (400, 96)):
        hanging_chain(q, x, 40, ln, "#0e1219", "#415066", hook=False)
        q.line((x, ln), (x - 6, ln + 30), "#10151d"); q.line((x, ln), (x + 6, ln + 30), "#10151d"); q.px(x, ln, "#62748f")
    return far, q.to_image(0.3)


# ------------------------------------------------------------------ the hearth below (CF8)
def hearth():
    p = base_far(6)
    wall(p, p.rectm(0, 0, W, H), bw=28, bh=14, cols=("#10151d", "#141a24", "#121822"), mortar="#06080b", seed=61, soot=0.45)
    p.mul(np.clip(0.75 + p.yy / 500, 0.7, 1.2))
    for x in (40, 200, 360):
        m = p.rectm(x, 0, x + 24, H); p.fill(m, "#0b0f15"); p.fill(p.rectm(x, 0, x + 1, H), "#2d3849")
        for y in (50, 130):
            p.fill(p.rectm(x - 4, y, x + 28, y + 5), "#18202b"); p.fill(p.rectm(x - 4, y, x + 28, y + 1), "#415066")
    p.eglow(256, 230, 300, 120, "#5a311c", 0.35, power=1.4)   # the coals' glow from below, far off
    ember_dots(p, 34, (0, 30, W, 200), 9, ("#7c401d", "#a3531f", "#c96a22"))
    far = p.to_image(0.35, alpha=False)
    q = Cv(W, H)
    for x, ln in ((110, 70), (300, 100), (420, 56)):
        hanging_chain(q, x, 0, ln, "#0e1219", "#415066")
    beam = q.rectm(0, 0, W, 10); plates(q, beam, pw=32, ph=10, seed=8); q.fill(q.rectm(0, 9, W, 10), "#364356")
    return far, q.to_image(0.3)


THEMES = {"flue": flue, "racks": racks, "cistern": cistern, "bellows": bellows, "court": court, "hearth": hearth}


def build(build_sheet, prev):
    cards = []
    for name, fn in THEMES.items():
        far, mid = fn()
        build_sheet(f"cfa_bg_{name}", [("far", [far.convert("RGBA")]), ("mid", [mid])], W, H)
        comp = far.convert("RGBA").copy(); comp.alpha_composite(mid)
        cards.append(comp)
        if name == "racks":   # the generic biome layers are the Hall of Racks
            build_sheet("bg_forge_far", [("loop", [far.convert("RGBA")])], W, H)
            build_sheet("bg_forge_mid", [("loop", [mid])], W, H)
    sheet = Image.new("RGBA", (W, H * len(cards)))
    for i, c in enumerate(cards):
        sheet.paste(c, (0, i * H))
    sheet.save(os.path.join(prev, "forge_bg_themes.png"))
