#!/usr/bin/env python3
"""Environment art for THE COLD FORGE and THE ASHEN THRESHOLD (v17, agent AREA).

Builds (art/asebuild.py -> art/<name>.aseprite + assets/<name>.png/.json):
  tiles_forge, tiles_threshold   48 x 16x16, tag `all` (ART_SPEC section 6 index layout)
  bg_forge_far / bg_forge_mid     512x216, tag `loop` (far opaque, mid transparent above)
  bg_threshold_far / _mid         the same for the threshold: pale sourceless ash-light, impossible shapes far off
  cfa_s (32x32)  cfa_m (64x64)  cfa_rack (96x80)  cfa_bellows (48x80)  cfa_furnace (256x288)  cfa_doors (96x112)
  cfa_coals (176x24)  cfa_gate (224x352)  cfa_guard (48x128)  cfa_ganvil (96x64)          props (gen_forge_props.py)
Look: the approved concept moods (art/concepts/forge/*.png): cold slate, black iron, soot, still black water; the only warm
light the flue shaft and the arena coals. Palette: forge_env_lib.FORGE. Previews -> art/previews/forge_*.png.

Usage: python3 art/gen_forge_env.py [--preview]   (--preview: previews only, no Aseprite export)
"""
import os, sys, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from forge_env_lib import *   # noqa
import asebuild               # noqa

PREV = os.path.join(HERE, "previews")
os.makedirs(PREV, exist_ok=True)
EXPORT = "--preview" not in sys.argv

# ================================================================== tiles
SKINS = {
    "forge": dict(br=("#18202b", "#1e2734", "#1b2330", "#202a37"), mortar="#06080b", lip="#62748f", lip2="#364356", top_dust=("#4f6079", "#2d3849"),
                  edgeL="#2d3849", dark="#05070a", bg=("#121822", "#141a24", "#111620"), bgm="#080b10", strap=True,
                  steel=("#252f3e", "#415066", "#7c8ea8", "#0e1219"), plat=("#4f6079", "#2d3849", "#131822", "#0a0d12")),
    "threshold": dict(br=("#4f6079", "#566273", "#62748f", "#5a6779"), mortar="#2d3849", lip="#dfe4ea", lip2="#b7c0cb", top_dust=("#c9d0d9", "#a5afbc"),
                      edgeL="#8f9aa8", dark="#252f3e", bg=("#364356", "#3a475a", "#334054"), bgm="#252f3e", strap=False,
                      steel=("#62748f", "#8f9aa8", "#dfe4ea", "#364356"), plat=("#c9d0d9", "#8f9aa8", "#566273", "#364356")),
}


def tile_bricks(p, S, seed, dim=1.0):
    """16x16 slate ashlar: two 8px courses (running bond), each brick bevelled (lit top/left, shadowed bottom/right),
    tone jitter per brick and a fine grain, so the tiles tile and read as cut stone."""
    cols = [hexc(c) for c in S["br"]]
    mort = hexc(S["mortar"])
    for y in range(16):
        course = y // 8; ly = y % 8
        for x in range(16):
            sx = (x + (8 if course else 0)) % 16
            bid = (course * 2 + (x + (8 if course else 0)) // 16 + seed * 5) % 7
            if ly == 0 or sx == 0:
                c = mort
            else:
                base = cols[int(hh(bid, course, seed) * len(cols)) % len(cols)].copy()
                k = 1.0
                if ly == 1: k = 1.22
                elif ly == 7: k = 0.78
                if sx == 1 and ly > 1: k *= 1.1
                if sx == 15: k *= 0.82
                k *= 0.94 + 0.12 * hh(x * 3 + seed, y * 7, 11)
                c = base * k
                if hh(x, y, seed + 40) < 0.06: c = c * 0.8
            p.c[y, x] = c * dim
    p.a[:] = True


def solid_tile(sk, m, var, seed):
    S = SKINS[sk]
    p = Cv(16, 16)
    tile_bricks(p, S, seed + var * 3, dim=0.68 if m == 0 else 1.0)
    if var and S["strap"] and not (m & 4):
        y0 = 9
        p.rect(0, y0, 16, y0 + 4, "#0e1219"); p.rect(0, y0, 16, y0 + 1, "#364356"); p.rect(0, y0 + 1, 16, y0 + 2, "#18202b"); p.rect(0, y0 + 3, 16, y0 + 4, "#05070a")
        for x in (3, 11):
            p.px(x, y0 + 1, "#62748f"); p.px(x, y0 + 2, "#06080b")
    elif var and not S["strap"]:
        for i in range(5):   # threshold variant: a hairline fracture
            p.px(4 + i * 2, 3 + (i % 2) + i, S["mortar"])
    elif var:
        pass
    if not var and sk == "forge" and (m & 1) == 0 and hh(m, seed, 3) < 0.5:   # soot running down the face
        for y in range(16):
            x = 5 + int(hh(m, 1, seed) * 6)
            if hh(x, y, seed) < 0.75: p.c[y, x] *= 0.6
    if m & 1:   # walking surface: a lit lip, ash dust on it
        p.rect(0, 0, 16, 1, S["lip"]); p.rect(0, 1, 16, 2, S["lip2"]); p.rect(0, 2, 16, 3, S["mortar"])
        for x in range(16):
            if hh(x, seed, 5 + var) < 0.35:
                p.px(x, 0, S["top_dust"][0])
            elif hh(x, seed, 6 + var) < 0.25:
                p.px(x, 1, S["top_dust"][1])
    if m & 8:
        p.rect(0, 1 if (m & 1) else 0, 1, 16, S["edgeL"])
    if m & 2:
        p.rect(15, 0, 16, 16, S["dark"]); p.rect(14, 2 if (m & 1) else 0, 15, 16, S["mortar"])
    if m & 4:
        p.rect(0, 15, 16, 16, S["dark"]); p.rect(0, 14, 16, 15, S["mortar"])
    return p.to_image(dither=0.0)


def platform_tile(sk, kind):
    S = SKINS[sk]; c = S["plat"]
    p = Cv(16, 16)
    if sk == "forge":   # iron grating catwalk: lit rail, a lattice, a lower rail; ends bolt to brackets
        p.rect(0, 0, 16, 2, c[1]); p.rect(0, 0, 16, 1, c[0])
        for x in range(16):
            for y in range(2, 6):
                if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                    p.px(x, y, c[2])
        p.rect(0, 6, 16, 7, c[3])
        if kind in ("L", "S"):
            p.rect(0, 0, 2, 7, c[2]); p.line((1, 7), (5, 12), c[3]); p.px(1, 1, c[0])
        if kind in ("R", "S"):
            p.rect(14, 0, 16, 7, c[2]); p.line((14, 7), (10, 12), c[3]); p.px(14, 1, c[0])
    else:               # a slab of pale stone with an ash skin
        p.rect(0, 0, 16, 5, c[1]); p.rect(0, 0, 16, 1, c[0]); p.rect(0, 4, 16, 5, c[3])
        for x in range(16):
            if hh(x, 3, 71) < 0.4:
                p.px(x, 0, "#eef1f4")
        if kind in ("L", "S"):
            p.rect(0, 0, 1, 5, c[2])
        if kind in ("R", "S"):
            p.rect(15, 0, 16, 5, c[3])
    return p.to_image(dither=0.0)


def spikes_tile(sk, down=False):
    """broken blades standing point-up out of the floor (or hanging point-down): lit edge, dark flat, a dull core"""
    S = SKINS[sk]; st = S["steel"]
    p = Cv(16, 16)
    for (x, h, lean) in ((3, 10, -0.18), (8, 14, 0.06), (12, 9, 0.22)):
        for k in range(h):
            w = 1.6 * (1 - k / h) + 0.5
            cx = x + lean * k
            y = 15 - k if not down else k
            for xx in range(int(cx - w), int(cx + w) + 1):
                d = xx - cx
                c = st[2] if d < -w + 1 else (st[3] if d > w - 1 else st[1])
                p.px(xx, y, c)
        tip = (x + lean * (h - 1), 15 - (h - 1) if not down else h - 1)
        p.px(tip[0], tip[1], st[2])
    if not down:
        p.rect(0, 15, 16, 16, st[3])
    else:
        p.rect(0, 0, 16, 1, st[3])
    return p.to_image(dither=0.0)


def bg_tile(sk, v):
    S = SKINS[sk]
    p = Cv(16, 16)
    bricks(p, p.rectm(0, 0, 16, 16), bw=8, bh=4, cols=S["bg"], mortar=S["bgm"], seed=40 + v, lip=1.06)
    if v == 1:   # a soot streak
        for y in range(16):
            for x in (6, 7, 8):
                if hh(x, y, 3) < 0.7:
                    p.px(x, y, "#05070a" if sk == "forge" else "#2d3849")
    if v == 2 and False:   # (rings read as a pattern: off)
        for a in range(0, 360, 30):
            p.px(8 + 3 * math.cos(math.radians(a)), 9 + 3 * math.sin(math.radians(a)), "#1e2734" if sk == "forge" else "#4f6079")
        p.rect(7, 4, 9, 6, "#131822" if sk == "forge" else "#415066")
    if v == 3 and False:   # (off)
        p.rect(5, 6, 11, 8, "#030405" if sk == "forge" else "#252f3e"); p.rect(5, 6, 11, 7, "#010203" if sk == "forge" else "#1e2734")
    return p.to_image(dither=0.0)


def deco_tile(sk, k):
    S = SKINS[sk]
    p = Cv(16, 16)
    hi, lo = ("#364356", "#131822") if sk == "forge" else ("#8f9aa8", "#4f6079")
    if k == 0:   # chain
        for y in range(16):
            if y % 4 == 0:
                p.px(7, y, lo); p.px(9, y, lo); p.px(8, y, hi)
            else:
                p.px(8, y, lo)
    elif k == 1:   # soot / ash strands hanging from the roof
        for i, x in enumerate((3, 7, 8, 12)):
            n = int(5 + hh(i, 1, sk == "forge") * 9)
            for y in range(n):
                p.px(x + (1 if y > n * 0.6 and i % 2 else 0), y, "#0b0a0b" if sk == "forge" else "#a5afbc")
    elif k == 2:   # a hook on a short chain
        for y in range(8):
            p.px(8, y, lo)
        for (x, y) in ((8, 8), (8, 9), (8, 10), (9, 11), (10, 11), (11, 10), (11, 9)):
            p.px(x, y, hi)
    elif k == 3:   # a scrap pile of broken blades
        for i in range(7):
            x = 2 + hh(i, 2, 9) * 11; y = 12 + hh(i, 3, 9) * 3; L = 3 + hh(i, 4, 9) * 5; a = (hh(i, 5, 9) - 0.5) * 2.4
            p.line((x, y), (x + math.cos(a) * L, y - abs(math.sin(a)) * L * 0.5), "#415066" if i % 2 else "#252f3e")
        p.rect(1, 15, 15, 16, lo)
    return p.to_image(dither=0.0)


def tuft_tile(sk):
    p = Cv(16, 16)
    c1, c2 = ("#272324", "#141213") if sk == "forge" else ("#c9d0d9", "#a5afbc")
    m = p.ellm(8, 16.5, 7, 3.2)
    p.fill(m, c2); p.fill(p.ellm(7, 15.8, 4, 1.6), c1)
    if sk == "forge":
        p.line((10, 15), (12, 9), "#415066"); p.px(12, 9, "#7c8ea8"); p.px(11, 12, "#252f3e")
    return p.to_image(dither=0.0)


def tileset(sk):
    tiles = []
    for var in (0, 1):
        for m in range(16):
            tiles.append(solid_tile(sk, m, var, seed=m * 3 + 11))
    for k in ("L", "M", "R", "S"):
        tiles.append(platform_tile(sk, k))
    tiles.append(spikes_tile(sk)); tiles.append(spikes_tile(sk, True))
    for v in range(4):
        tiles.append(bg_tile(sk, v))
    for k in range(4):
        tiles.append(deco_tile(sk, k))
    b = solid_tile(sk, 0, 0, seed=11).copy()   # breakable: a block with a crack
    bp = b.load()
    for (x, y) in ((4, 3), (5, 4), (5, 5), (6, 6), (7, 6), (8, 7), (8, 8), (9, 9), (10, 10), (10, 11), (11, 12)):
        bp[x, y] = (5, 7, 10, 255) if sk == "forge" else (37, 47, 62, 255)
    tiles.append(b)
    tiles.append(tuft_tile(sk))
    assert len(tiles) == 48
    return tiles


# ================================================================== parallax: the Cold Forge
def forge_far():
    p = Cv(512, 216, base="#06080b")
    p.vgrad(p.rectm(0, 0, 512, 216), "#05070a", "#0e1219", 0, 216)
    for i, bx in enumerate(range(0, 512, 64)):
        arch = p.poly([(bx + 6, 168), (bx + 6, 64)] + [(bx + 32 + 26 * math.cos(math.radians(a)), 64 - 30 * math.sin(math.radians(a))) for a in range(180, -1, -15)] + [(bx + 58, 168)])
        p.fill(arch, "#0a0d12")
        blade_rack(p, bx + 10, bx + 54, 70, 158, scale=1.0, cols=("#0a0d12", "#131822", "#131822", "#1e2734", "#0a0d12"), glint="#252f3e", seed=i + 10, fill=0.9, posts=False)
        for a in range(180, -1, -6):
            p.px(bx + 32 + 26 * math.cos(math.radians(a)), 64 - 30 * math.sin(math.radians(a)), "#18202b")
        p.fill(p.rectm(bx + 58, 18, bx + 70, 172), "#0a0d12"); p.fill(p.rectm(bx + 58, 18, bx + 59, 172), "#131822")
        p.fill(p.rectm(bx + 56, 170, bx + 72, 176), "#0e1219")
    # the floor of the far hall, receding in haze
    p.fill(p.rectm(0, 172, 512, 216), "#0b0e14")
    for x in range(0, 512, 32):
        p.fill(p.rectm(x, 172, x + 1, 216), "#080a0e")
    p.add_light(np.clip(1 - np.abs(p.yy - 128) / 80, 0, 1) * 0.6, "#1e2734", 0.32)
    p.fill(p.rectm(0, 0, 512, 18), "#040507")
    for x in range(0, 512, 48):
        p.fill(p.rectm(x, 18, x + 6, 24), "#040507")
    for i, x in enumerate((30, 98, 170, 236, 310, 380, 446)):
        chain(p, (x, 18), (x, 40 + (i * 17) % 40), col="#0b0e14", hi="#18202b")
    for (x, w) in ((120, 18), (376, 14)):
        p.shaft(x, x + w, x - 18, x + w + 22, 18, 190, "#4f6079", strength=0.13, soft=10, fade=0.8)
        p.fill(p.rectm(x, 16, x + w, 18), "#2d3849")
    return p.to_image(dither=0.35, alpha=False)


def forge_mid():
    p = Cv(512, 216)
    # two great pillars with iron straps, a beam between them; slack chains with hooks; a dark rack silhouette
    for x0 in (40, 300):
        m = p.rectm(x0, 0, x0 + 30, 216)
        bricks(p, m, bw=15, bh=8, cols=("#0a0d12", "#0c1016", "#0e1219"), mortar="#030405", seed=x0, soot=1.0, lip=1.05)
        p.fill(p.rectm(x0, 0, x0 + 1, 216), "#18202b"); p.fill(p.rectm(x0 + 29, 0, x0 + 30, 216), "#030405")
        for y in (40, 120, 190):
            iron_band(p, x0 - 2, x0 + 32, y, 6)
        p.fill(p.rectm(x0 - 4, 196, x0 + 34, 216), "#080a0e"); p.fill(p.rectm(x0 - 4, 196, x0 + 34, 197), "#1e2734")
    p.fill(p.rectm(0, 22, 512, 30), "#06080b"); p.fill(p.rectm(0, 22, 512, 23), "#18202b")
    for x in range(6, 512, 14):
        p.px(x, 25, "#252f3e")
    for i, (x, ln) in enumerate(((130, 70), (150, 46), (220, 92), (420, 60), (462, 84))):
        chain(p, (x, 30), (x + (i % 2) * 3, 30 + ln), col="#0a0d12", hi="#1e2734", sway=2)
        p.line((x - 1, 30 + ln), (x + 2, 33 + ln), "#1e2734"); p.line((x + 2, 33 + ln), (x + 4, 30 + ln), "#1e2734")
    blade_rack(p, 360, 470, 150, 212, scale=1.6, cols=("#06080b", "#0e1219", "#10151d", "#1e2734", "#06080b"), glint="#252f3e", seed=7, fill=0.85)
    blade_rack(p, 100, 170, 162, 214, scale=1.6, cols=("#06080b", "#0e1219", "#10151d", "#1e2734", "#06080b"), glint="#252f3e", seed=8, fill=0.8, rows=1)
    return p.to_image(dither=0.25)


# ================================================================== parallax: the Ashen Threshold
def threshold_far():
    p = Cv(512, 216, base="#8f9aa8")
    sky = p.rectm(0, 0, 512, 216)
    p.vgrad(sky, "#a5afbc", "#566273", 0, 216, gamma=0.9)
    n = p.noise2(128, 26, 71, 3, wrap=True)
    p.add_light(np.clip(n - 0.45, 0, 1), "#dfe4ea", 0.55)
    p.eglow(196, 58, 54, 54, "#eef1f4", 0.4, power=0.8)
    p.fill(p.ellm(196, 58, 15, 15), "#dfe4ea", 0.6)
    p.fill(p.ellm(196, 58, 11, 11), "#eef1f4", 0.5)
    far = "#7c8ea8"
    for (x, w, h, lean) in ((40, 6, 120, 0.10), (58, 4, 84, -0.05), (300, 8, 140, -0.08), (322, 4, 96, 0.04), (452, 5, 110, 0.12)):
        p.fill(p.poly([(x, 186), (x + w, 186), (x + w * 0.5 + lean * h, 186 - h)]), far, 0.5)
    for a in range(0, 360, 2):   # a ring standing in the haze
        x = 400 + 34 * math.cos(math.radians(a)); y = 140 + 10 * math.sin(math.radians(a))
        if a < 180 or hh(a, 1, 72) > 0.4:
            p.px(x, y, far, 0.5)
    for i in range(16):         # a stair into the sky
        p.fill(p.rectm(110 + i * 4, 176 - i * 8, 115 + i * 4, 178 - i * 8), far, 0.35)
    mist = np.clip((p.yy - 140) / 70, 0, 1) * (0.6 + 0.4 * p.noise2(64, 12, 73, 2, wrap=True))
    p.add_light(mist, "#b7c0cb", 0.5)
    return p.to_image(dither=0.55, alpha=False)


def threshold_mid():
    p = Cv(512, 216)
    # far below the hall: the causeway's arches stepping away into the mist, and broken colonnades on it, pale in the haze
    deck = 156
    under = p.rectm(0, deck + 6, 512, 216)
    p.fill(under, "#4f6079")
    for x0 in range(0, 512, 64):   # the arches: shadowed openings under the deck
        op = p.poly([(x0 + 12, 216)] + [(x0 + 32 + 20 * math.cos(math.radians(a)), deck + 34 - 22 * math.sin(math.radians(a))) for a in range(180, -1, -10)] + [(x0 + 52, 216)])
        p.fill(op, "#364356")
        p.fill(op & ~np.roll(op, -1, axis=0), "#2d3849")
        p.fill(p.rectm(x0 + 10, deck + 6, x0 + 12, 216), "#62748f")
    p.fill(p.rectm(0, deck, 512, deck + 7), "#6b7686"); p.fill(p.rectm(0, deck, 512, deck + 1), "#a5afbc")
    p.add_light(np.clip((p.yy - deck) / 60, 0, 1), "#b7c0cb", 0.35, mask=under)   # the mist rising round the piers
    for i, (x, h) in enumerate(((30, 70), (96, 40), (170, 92), (250, 56), (350, 84), (430, 48))):
        p.fill(p.rectm(x, deck - h, x + 10, deck), "#6b7686"); p.fill(p.rectm(x, deck - h, x + 1, deck), "#a5afbc")
        p.fill(p.poly([(x - 2, deck - h), (x + 12, deck - h), (x + 9, deck - h - 6 - (i % 3) * 3), (x + 3, deck - h - 2)]), "#6b7686")
    return p.to_image(dither=0.4)


def build_sheet(name, frames_by_tag, w, h, ms=100):
    """frames_by_tag: list of (tag, [PIL images]); every image w x h."""
    frames, tags, i = [], [], 0
    for tag, ims in frames_by_tag:
        for im in ims:
            assert im.size == (w, h), (name, tag, im.size)
            frames.append({"ms": ms, "cels": {"art": im}})
        tags.append((tag, i, i + len(ims) - 1)); i += len(ims)
    if EXPORT:
        asebuild.build(name, w, h, ["art"], frames, tags)
    return frames


def preview_tiles(name, tiles, k=4):
    out = Image.new("RGBA", (16 * 12 * k, 16 * 4 * k), (40, 40, 48, 255))
    for i, t in enumerate(tiles):
        out.alpha_composite(t.resize((16 * k, 16 * k), Image.NEAREST), ((i % 12) * 16 * k, (i // 12) * 16 * k))
    out.save(os.path.join(PREV, f"{name}.png"))


def mock_room(sk, tiles, far, mid, out):
    """a small mock room over the parallax: walls, a floor, a ledge, a platform run, spikes, bg walls"""
    W_, H_ = 384, 216
    img = Image.new("RGBA", (W_, H_)); img.alpha_composite(far.convert("RGBA").crop((0, 0, W_, H_)))
    img.alpha_composite(mid.crop((0, 0, W_, H_)))
    gw, gh = 24, 14
    g = [["." for _ in range(gw)] for _ in range(gh)]
    for y in range(gh):
        for x in range(gw):
            if y >= 11 or x == 0 or y == 0 or (x >= 18 and y >= 7) or (2 <= x <= 5 and 5 <= y <= 6):
                g[y][x] = "#"
    for x in range(8, 13):
        g[7][x] = "="
    g[10][14] = "^"; g[10][15] = "^"
    sol = lambda x, y: x < 0 or y < 0 or x >= gw or y >= gh or g[y][x] == "#"
    for y in range(gh):
        for x in range(gw):
            ch = g[y][x]
            if ch != "#":
                img.alpha_composite(tiles[38 + int(hh(x, y, 2) * 4)], (x * 16, y * 16))
    for y in range(gh):
        for x in range(gw):
            ch = g[y][x]
            if ch == "#":
                m = (0 if sol(x, y - 1) else 1) | (0 if sol(x + 1, y) else 2) | (0 if sol(x, y + 1) else 4) | (0 if sol(x - 1, y) else 8)
                img.alpha_composite(tiles[m + (16 if hh(x, y, 5) < 0.28 else 0)], (x * 16, y * 16))
            elif ch == "=":
                L, R = g[y][x - 1] == "=", g[y][x + 1] == "="
                img.alpha_composite(tiles[33 if L and R else 32 if R else 34 if L else 35], (x * 16, y * 16))
            elif ch == "^":
                img.alpha_composite(tiles[36], (x * 16, y * 16))
    img.save(out)


if __name__ == "__main__":
    import gen_forge_props as PR
    for sk in ("forge", "threshold"):
        t = tileset(sk)
        preview_tiles(f"forge_tiles_{sk}", t)
        far = forge_far() if sk == "forge" else threshold_far()
        mid = forge_mid() if sk == "forge" else threshold_mid()
        far.save(os.path.join(PREV, f"forge_bg_{sk}_far.png")); mid.save(os.path.join(PREV, f"forge_bg_{sk}_mid.png"))
        mock_room(sk, t, far, mid, os.path.join(PREV, f"forge_room_{sk}.png"))
        build_sheet(f"tiles_{sk}", [("all", t)], 16, 16)
        build_sheet(f"bg_{sk}_far", [("loop", [far.convert("RGBA")])], 512, 216)
        build_sheet(f"bg_{sk}_mid", [("loop", [mid])], 512, 216)
    PR.build_all(build_sheet, PREV)
    import gen_forge_bg as BG
    BG.build(build_sheet, PREV)   # room-themed parallax (and the generic bg_forge_* = the Hall of Racks)
    print("forge env done", "(preview only)" if not EXPORT else "")
