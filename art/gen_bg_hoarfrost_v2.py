#!/usr/bin/env python3
"""Hoarfrost Aqueduct backdrop v2 (bg rollout, agent B; docs/v17/bg_rollout_b.md, method in docs/v17/bg_pilot.md).

  python3 art/gen_bg_hoarfrost_v2.py            build bg_hoarfrost_{far,mid} from the saved renders in art/bg_src/hoarfrost/
  python3 art/gen_bg_hoarfrost_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_hoarfrost_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  python3 art/gen_bg_hoarfrost_v2.py --sweep far|mid 1,2,3   pass-1 seed sweep into the scratch dir ($BG_SWEEP or /tmp)
  --no-ase                                       write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/hoarfrost_bg.py (kept for rollback).
The moon stays at far (150,36) as in v1; hoarfrost has no far-layer GFX_SUN entry (screen-space source), so nothing moves.
The HF14 aurora overlay (51_rb.js) draws on top of these layers and is unchanged; a faint painted curtain stays in the far sky.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgv2b

B = 'hoarfrost'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#070a12'
MOON = (150, 36, 10)

# v1 ramps (hoarfrost_bg.py FAR / AUR, hoarfrost_tiles ICE) extended upward in the same cold blue family
FARR = ['03050a', '070a11', '0c1019', '121824', '1a2231', '1f2838', '252f41', '2c374a', '344055', '3e4a60', '4a576d', '58667d',
        '6a788f', '8190a6', '9dabbf', 'b6c2d2', 'd0d9e4', 'e8eef4']
AUR = ['123036', '173d42', '1f5250', '2a6a62']
ICE = ['15344c', '1d4a66', '286684', '3886a6', '55a6c4', '82c6dc', 'b6e4f2']
HALO = ['16222e', '1c2c38', '243844', '2e4450']                     # moon-halo steps between the navy sky and the lit haze
FAR_PAL = [hexc(c) for c in FARR + AUR + ICE + HALO]
SIL = ['05070b', '0a0d14', '0d111a', '111621', '161c29', '1c2332', '232b3c', '2c3548', '374256']
RIM = ['55667d', '6d7f96', '8a9cb2']
MID_PAL = [hexc(c) for c in SIL + RIM + ['111f2c', '1f3548', '2a4459', '1d4a66', '286684', '3a5a78', '557a9a']]

PROMPT_FAR = ('pixel art, dark fantasy, moonlit frozen mountain gorge at night, a colossal ancient stone aqueduct with two tiers of arches '
              'crossing the gorge and receding into the distance, snow-capped jagged peaks lit by a pale full moon, frozen waterfalls '
              'hanging from the cliffs, a faint teal aurora curtain in the starry sky, cold mist in the gorge, a frozen lake below with '
              'the moon reflected, snowy pine forest on the shore, side-scroller game background, muted cold blue and slate palette, '
              'atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, ruined ancient stone aqueduct arches in the snow, massive weathered masonry piers with frost and '
              'long icicles, a broken channel span with a huge frozen waterfall of blue ice pouring from the break, snow-laden pine trees '
              'and jagged rocks at the base, isolated on a flat grey background, side-scroller game background layer, dark slate blue '
              'stone with cold moonlit rim light, detailed')


# -------------------------------------------------------------------------------------------------- guides
def aqueduct_geom(G):
    """Per 3x column: scale s (0.42..1, nearest at x=380, receding toward the moon) and the arch coordinate u (whole number
    of upper arches per period, so it tiles)."""
    x = (np.arange(WS) + 0.5) / S
    s = 0.71 + 0.29 * np.cos(2 * np.pi * (x - 380) / W)
    acc = np.cumsum(1.0 / (30.0 * s)) / S
    n = round(acc[-1]); u = acc * n / acc[-1]
    return s, u, n


def guide_far():
    rng = np.random.default_rng(3)
    G = Guide(hexc('101828'))
    X, Y = G.X, G.Y
    nz = tile_noise(WS, HS, 96, 48, 31); nz2 = tile_noise(WS, HS, 24, 12, 32, octaves=2)
    mx, my, mr = MOON
    # sky: deep navy at the top, colder and lighter toward the horizon, a wide moon halo
    v = smooth(-10, 150, Y)
    G.rgb = lerp(hexc('0e1426'), hexc('4a5c7c'), v[..., None])
    dm = np.sqrt(G.wdx(mx) ** 2 + ((Y - my) * 1.2) ** 2)
    G.add(np.exp(-(dm / 70) ** 2), hexc('3a4a66'), 0.9); G.add(np.exp(-(dm / 22) ** 2), hexc('6a7a98'), 0.8)
    # faint aurora curtain (kept from v1, a bit stronger): a ribbon from x≈210 to x≈500 with vertical rays
    cy = 34 + 12 * np.sin(X / W * 2 * np.pi * 2 + 0.6) + 5 * np.sin(X / W * 2 * np.pi * 5)
    span = smooth(190, 260, X) * (1 - smooth(470, 520, X)) + smooth(-60, 0, X - 512) * 0
    rays = 0.55 + 0.45 * np.sin(X * 1.9 + nz2 * 8) ** 2
    cur = np.exp(-((Y - cy) / 7) ** 2) + 0.7 * np.clip((Y - cy) / 30, 0, 1) * np.exp(-np.clip(Y - cy, 0, None) / 18)
    G.add(np.clip(cur * span * rays, 0, 1), hexc('2a7a70'), 0.75)
    # stars
    for _ in range(90):
        sx, sy = rng.uniform(0, W), rng.uniform(0, 80)
        G.fill(G.mask_ellipse(sx, sy, 0.45, 0.45), hexc('c8d4e4'), rng.uniform(0.4, 1))
    # the moon
    d = np.sqrt(G.wdx(mx) ** 2 + (Y - my) ** 2)
    G.fill((d < mr).astype(float), hexc('e8eef4'))
    G.fill(((d < mr) & (tile_noise(WS, HS, 6, 6, 33, 1) > 0.62)).astype(float), hexc('b6c2d2'), 0.7)
    # far range: pale snow peaks, lit on the flanks facing the moon
    def range_(base, amp, cell, seed, rock, snow_lit, snow_dark, snowline, haze):
        p = bgv2b.profile(cell, seed, 4, ridged=True)
        top = base - amp * p ** 1.6                                          # 3x columns -> 1x y
        k = np.ones(31) / 31; ts = np.convolve(np.concatenate([top[-15:], top, top[:15]]), k, 'valid')
        slope = np.gradient(ts)
        topm = top[None, :]
        m = (Y >= topm).astype(float)
        # lit when the face turns toward the moon (moon at x=150: left of the column -> rising-to-the-right faces)
        toward = np.sign(G.wdx(mx))[0]
        depth = np.clip((Y - topm) / snowline, 0, 1)
        lit = np.clip(-slope * toward * 4, 0, 1)[None, :] * (1 - 0.6 * depth)
        n3 = tile_noise(WS, HS, 6, 24, seed + 7, 3)                         # tall cells: snow gullies run down the faces
        snow = (n3 * 0.8 + 0.62 - depth * 1.2) > 0.5
        col = np.where(snow[..., None], lerp(hexc(snow_dark), hexc(snow_lit), lit[..., None]), lerp(hexc(rock), hexc(rock) * 1.4, lit[..., None]))
        col = lerp(col, hexc(haze), smooth(0, 60, Y - topm)[..., None] * 0.55)
        G.fill_img(m, col)
        return top
    range_(104, 70, 128, 41, '3a4a62', 'c8d4e2', '7a8ca8', 46, '5a6c88')
    G.add(np.exp(-((Y - 108) / 14) ** 2), hexc('3a4a62'), 0.5)             # mist between the ranges
    top2 = range_(150, 58, 96, 43, '222c40', '9aaccA'.lower(), '4e607e', 34, '3e4e68')
    # frozen falls hanging from the near cliffs
    for fx, ft, fl in ((44, 0, 34), (262, 0, 30), (330, 0, 40), (468, 0, 26)):
        t0 = top2[int(fx * S) % WS] + 6
        m = G.mask_poly([(fx - 2.5, t0), (fx + 2.5, t0), (fx + 4.5, t0 + fl), (fx - 3.5, t0 + fl)], blur=0.3)
        G.fill(m, hexc('82a6c4'), 0.85); G.fill(G.mask_lines([(fx - 1, t0, fx - 1.5, t0 + fl, 0.8)]), hexc('d0e4f2'), 0.8)
    G.add(np.exp(-((Y - 150) / 16) ** 2), hexc('4a5c7a'), 0.55)             # gorge mist
    # the frozen lake at the bottom with the moon reflected, snowy banks and pines
    LK = 176
    lake = (Y >= LK).astype(float)
    refl = np.exp(-(G.wdx(mx) / 9) ** 2) * (0.6 + 0.4 * (np.sin(Y * 3 + nz2 * 6) > 0))
    lc = lerp(hexc('2a3a54'), hexc('1a2436'), smooth(LK, 216, Y)[..., None])
    lc = lc + refl[..., None] * hexc('9aaccA'.lower()) * 0.8
    cracks = (np.abs(tile_noise(WS, HS, 24, 6, 35, 2) - 0.5) < 0.012).astype(float)
    G.fill_img(lake, lc); G.fill(cracks * lake, hexc('6a7c98'), 0.6)
    G.fill(G.mask_lines([(0, LK, W, LK, 0.8)]), hexc('8a9cb4'), 0.7)
    # the aqueduct across the gorge: two tiers, nearest at x=380, receding toward the moon
    s, u, n = aqueduct_geom(G)
    s2 = s[None, :]; u2 = u[None, :]
    yt = 158 - 36 * s2; yb = 162 + 18 * s2; ym = yt + (yb - yt) * 0.42
    body = (Y >= yt) & (Y <= yb)
    stone = lerp(hexc('3a465c'), hexc('5a6880'), (0.5 + 0.5 * (nz2 - 0.5))[..., None])
    G.fill_img(body.astype(float), stone)
    # lower tier: tall arches, period = 2 upper arches
    def openings(period_u, y0, y1, hw):
        ph = (u2 / period_u) % 1.0 - 0.5
        R = hw * 30 * period_u * s2
        px = ph * 30 * period_u * s2
        spring = y0 + 3 * s2 + R
        inside = np.abs(ph) < hw
        ytop = spring - np.sqrt(np.clip(R ** 2 - px ** 2, 0, None))
        return inside & (Y > ytop) & (Y < y1), ph
    o1, ph1 = openings(2, ym, yb + 1, 0.34)
    o2, ph2 = openings(1, yt + 5 * s2, ym - 1, 0.30)
    behind = G.rgb.copy()
    G.rgb = np.where((o1 | o2)[..., None] & body[..., None], behind * 0 + lerp(hexc('3e4e68'), hexc('2a3650'), smooth(110, 180, Y)[..., None]), G.rgb)
    # moonlit pier faces (the side toward the moon), cornices, snow on the deck, icicles under the arches
    lf = ((ph1 > 0.34) & (ph1 < 0.40) & body & ~o1 & (Y > ym)) | ((ph2 > 0.30) & (ph2 < 0.35) & body & ~o2 & (Y < ym))
    G.fill(lf.astype(float), hexc('8a9cb4'), 0.8)
    G.fill(((np.abs(Y - ym) < 1.2 * s2) & body).astype(float), hexc('6a7a94'))
    G.fill(((Y >= yt - 2.2 * s2) & (Y < yt + 1.2)).astype(float), hexc('d8e2ee'))
    ic = (o1 | o2) & (np.abs(np.sin(X * 3.1)) > 0.6) & (tile_noise(WS, HS, 3, 3, 36, 1) > 0.45)
    G.fill((ic & (np.roll(~(o1 | o2), 6, axis=0))).astype(float), hexc('b6d4e8'), 0.8)
    # pines on the near shore (in front of the lake)
    for _ in range(46):
        px, h = rng.uniform(0, W), rng.uniform(10, 22)
        if abs(((px - mx + W / 2) % W) - W / 2) < 18: continue
        base = rng.uniform(190, 214)
        for k in range(4):
            ty = base - h + h * k / 4; hw = 1.5 + h * 0.2 * (k + 1) / 4
            G.fill(G.mask_poly([(px, ty - 2), (px + hw, ty + h / 4 + 1), (px - hw, ty + h / 4 + 1)]), hexc('141c2a'))
            G.fill(G.mask_poly([(px, ty - 2), (px - hw * 0.8, ty + h / 4), (px - hw * 0.2, ty + h / 4 - 1.5)]), hexc('8a9cb4'), 0.55)
    G.fill((Y > 208).astype(float) * (0.5 + 0.5 * nz), hexc('3a4a62'), 0.7)
    return G


def guide_mid():
    rng = np.random.default_rng(11)
    G = Guide(hexc('2a3240'), alpha=True)
    X, Y = G.X, G.Y
    nz = tile_noise(WS, HS, 12, 6, 41, 2)
    stone, lit, dark, snow = hexc('4a5670'), hexc('8a9cb8'), hexc('2a3244'), hexc('d0dcea')
    DECK, DECKB, SPR = 98, 110, 140
    piers = [(18, 26), (152, 24), (300, 22), (362, 16), (424, 24)]
    spans = [(18, 152, False), (152, 300, True), (300, 362, False), (362, 424, False)]
    def masonry(m, seed):
        """courses and joints on a mask (dark mortar lines), light from the left"""
        cy = (np.floor(Y / 7) % 2)
        jx = ((X + cy * 6 + seed) % 12) < 0.7
        jy = (Y % 7) < 0.6
        G.fill(m * (jx | jy), dark, 0.55)
        G.fill(m * (nz > 0.62), hexc('5e6a84'), 0.35)
    for (px, pw) in piers:   # piers from the deck down to the ground, a lit left face, cutwater footing
        m = G.mask_poly([(px - pw / 2, DECK), (px + pw / 2, DECK), (px + pw / 2 + 3, 206), (px - pw / 2 - 3, 206)])
        if px == 424:   # the last pier stands alone, snapped off below the springing
            m = G.mask_poly([(px - pw / 2, 150), (px - 4, 138), (px + 2, 146), (px + pw / 2, 132), (px + pw / 2 + 3, 206), (px - pw / 2 - 3, 206)])
        G.fill(m, stone); masonry(m, px)
        G.fill(m * (G.wdx(px) < -pw / 2 + 3), lit, 0.75)
        G.fill(m * (G.wdx(px) > pw / 2 - 4), dark, 0.6)
        G.fill(G.mask_poly([(px - pw / 2 - 5, SPR - 4), (px + pw / 2 + 5, SPR - 4), (px + pw / 2 + 3, SPR + 2), (px - pw / 2 - 3, SPR + 2)]), hexc('5e6a84'))   # impost
    for (x0, x1, broken) in spans:
        cx, half = (x0 + x1) / 2, (x1 - x0) / 2 - 12
        deck = G.mask_poly([(x0, DECK), (x1, DECK), (x1, DECKB + 40), (x0, DECKB + 40)])
        hole = G.mask_poly(arch_pts(cx, half, SPR, DECKB + 4, 230, pointed=False, n=40))
        ring = np.clip(G.mask_poly(arch_pts(cx, half + 6, SPR, DECKB - 2, 230, pointed=False, n=40)) - hole, 0, 1)
        body = np.clip(deck - hole, 0, 1)
        if broken:   # the channel span is snapped in the middle: a ragged gap
            jag = 10 * (tile_noise(WS, HS, 4, 4, 42, 1) - 0.5)
            gap = (np.abs(G.wdx(cx) + jag) < 34).astype(float)
            body = body * (1 - gap); ring = ring * (1 - gap)
        G.fill(body, stone); masonry(body, x0)
        G.fill(ring, hexc('5a6680'))
        # voussoir joints radiating from the arch centre
        ang = np.arctan2(Y - SPR, G.wdx(cx)); G.fill(ring * (np.abs(np.sin(ang * 22)) < 0.12), dark, 0.7)
        G.fill(np.clip(G.mask_poly(arch_pts(cx, half + 1.5, SPR, DECKB + 2.5, 230, pointed=False, n=40)) - hole, 0, 1) * (1 - (gap if broken else 0)), lit, 0.6)
        # icicles hanging from the arch soffit
        for k in range(int(half * 2 / 4)):
            ix = cx - half + 2 + k * 4 + rng.uniform(-1, 1)
            dx = (ix - cx) / half
            if abs(dx) > 0.95: continue
            iy = SPR - math.sqrt(max(0, 1 - dx * dx)) * (SPR - DECKB - 4)
            if broken and abs(ix - cx) < 38: continue
            ln = rng.uniform(3, 12)
            G.fill(G.mask_poly([(ix - 1.2, iy - 1), (ix + 1.2, iy - 1), (ix, iy + ln)]), hexc('a8c8e0'), 0.9)
    # cornice + snow on the deck (thick, drifting over the edge)
    deck_all = G.mask_poly([(5, DECK - 1), (437, DECK - 1), (437, DECK + 4), (5, DECK + 4)])
    span_x = G.mask_poly([(5, 0), (437, 0), (437, 216), (5, 216)])
    cx_b = (152 + 300) / 2
    gapm = (np.abs(G.wdx(cx_b) + 10 * (tile_noise(WS, HS, 4, 4, 42, 1) - 0.5)) < 34).astype(float)
    G.fill(deck_all * (1 - gapm), hexc('6a7894'))
    sn = DECK - 2 - 2.5 * tile_noise(WS, HS, 8, 4, 43, 2)
    G.fill(((Y > sn) & (Y < DECK + 1.5)).astype(float) * (1 - gapm) * span_x, snow)
    G.fill(((Y > DECK + 3) & (Y < DECK + 6 + 4 * nz)).astype(float) * (1 - gapm) * (np.sin(X * 0.7) > 0.3) * span_x, snow, 0.8)   # drips of snow over the cornice
    # broken ends: long icicle fringes
    for ex in (cx_b - 34, cx_b + 34):
        for k in range(6):
            ix = ex + (k - 2.5) * 2.2; ln = 10 + 14 * rng.random()
            G.fill(G.mask_poly([(ix - 1.3, DECK + 2), (ix + 1.3, DECK + 2), (ix, DECK + 2 + ln)]), hexc('b6d4ea'))
    # the frozen waterfall poured from the break: a widening column of blue ice with vertical flutes and a frozen splash pool
    fx = cx_b
    wfm = G.mask_poly([(fx - 24, DECK + 4), (fx + 22, DECK + 4), (fx + 30, 150), (fx + 40, 206), (fx - 42, 206), (fx - 30, 150)], blur=0.6)
    flutes = 0.5 + 0.5 * np.sin(G.wdx(fx) * 0.9 + tile_noise(WS, HS, 6, 24, 44, 2) * 6)
    ice = lerp(hexc('2a4a68'), hexc('9ac8e2'), (flutes ** 1.5 * (0.6 + 0.4 * (G.wdx(fx) < 0)))[..., None])
    ice = lerp(ice, hexc('d8ecf6'), (smooth(0.88, 1.0, flutes) * 0.7)[..., None])
    G.fill_img(wfm, ice)
    G.fill(G.mask_ellipse(fx, 206, 58, 14), hexc('6a94b4'))
    G.fill(G.mask_ellipse(fx - 6, 201, 40, 6), hexc('b6d4ea'), 0.8)
    # snow-laden pines and rock spurs at the base (in front of the piers)
    def pine(cx, base, h):
        nt = max(3, int(h / 10))
        G.fill(G.mask_lines([(cx, base - h * 0.2, cx, base + 6, 2.0)]), hexc('2a2420'))
        for i in range(nt):
            ty = base - h + h * 0.8 * i / nt; th = h * 0.8 / nt + 5; hw = 3 + h * 0.24 * (0.4 + 0.6 * (i + 1) / nt)
            G.fill(G.mask_poly([(cx, ty - 1), (cx + hw, ty + th), (cx + hw + 1.5, ty + th + 1.5), (cx - hw - 1.5, ty + th + 1.5), (cx - hw, ty + th)]), hexc('1e2a30'))
            G.fill(G.mask_poly([(cx, ty - 1), (cx - hw * 0.9, ty + th * 0.85), (cx - hw * 0.2, ty + th * 0.6), (cx + hw * 0.6, ty + th * 0.8)]), snow, 0.75)
    for (cx, h) in ((70, 64), (88, 44), (104, 30), (212, 34), (356, 58), (376, 40), (482, 50), (498, 30)):
        pine(cx, 210, h)
    for (x0, x1, top) in ((-14, 46, 168), (232, 262, 182), (392, 440, 174)):
        pts = [(x0, 218), (x0 + (x1 - x0) * 0.2, top + 14), (x0 + (x1 - x0) * 0.45, top), (x0 + (x1 - x0) * 0.6, top + 6), (x0 + (x1 - x0) * 0.85, top + 18), (x1, 218)]
        m = G.mask_poly(pts); G.fill(m, hexc('3a4458'))
        G.fill(m * (G.mask_poly([(x, y - 3) for x, y in pts]) * 0 + (Y < top + 6)), snow, 0.7)
    G.fill((Y > 206 + 1.5 * np.sin(X * 0.3)).astype(float), hexc('a8b8cc'))
    # the far end of the deck has fallen in: cut a ragged notch out of the top over the last small arch
    cut = G.mask_poly([(392, 0), (440, 0), (440, 132), (430, 126), (421, 118), (414, 106), (404, 100), (396, 92)])
    G.rgb = G.rgb * (1 - cut[..., None]) + hexc('2a3240') * cut[..., None]; G.a = G.a * (1 - cut)
    for (ex, ey) in ((396, 93), (404, 101), (414, 107)):
        G.fill(G.mask_poly([(ex - 1.2, ey), (ex + 1.2, ey), (ex, ey + 9)]), hexc('b6d4ea'))
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image()).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


# -------------------------------------------------------------------------------------------------- render + build
RENDER = {   # picked by eye from seed sweeps (docs/v17/bg_rollout_b.md)
    'far': dict(prompt=PROMPT_FAR, seed=6, denoise=0.72, cn=0.45, cn_end=0.6, pix=0.45, guide_blur=1.3),
    'mid': dict(prompt=PROMPT_MID, seed=6, denoise=0.7, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=1.0, seam_band=96),
}


def do_render():
    bgv2b.set_prefix(B); times = {}
    for layer, kw in RENDER.items():
        times[layer] = round(render_layer(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


def far_post(a, stage):
    """'hi' (lead review, HF6): the snow ranges sit right behind the play layer, so the band y≈56-128 (1x) is dropped ~2 value steps
    and softened (calmer texture there); the moon, the aurora above it and the aqueduct below it keep their values."""
    if stage != 'hi': return a
    from PIL import ImageFilter
    yy = (np.arange(a.shape[0]) / S)[:, None, None]
    band = smooth(50, 66, yy) * (1 - smooth(118, 132, yy))
    pad = np.concatenate([a[:, -24:], a, a[:, :24]], 1)                          # wrap-padded so the blur keeps the seam
    soft = np.asarray(Image.fromarray(np.clip(pad, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), float)[:, 24:-24]
    a = a * (1 - 0.6 * band) + soft * 0.6 * band
    l = a.mean(2, keepdims=True)
    k = 1 - band * 0.24 * smooth(60, 160, l)                                # brightest snow drops most
    return a * k


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=6, grade_kw=dict(black=6, white=262, gamma=0.88, sat=0.8), post=far_post, dk=0.3)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=3,
                                  grade_kw=dict(black=16, white=400, gamma=0.8, sat=0.95), rim_col=hexc('55667d'))
    far_im, mid_im = to_rgba(far), to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png')
    preview(far_im, mid_im, TINT, f'{SRC}/preview.png')
    st = {'far': stats(far_im), 'mid': stats(mid_im), 'accents_far': ['%02x%02x%02x' % c for c in acc_f], 'accents_mid': ['%02x%02x%02x' % c for c in acc_m]}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase:
        ase_build(f'bg_{B}_far', far_im); ase_build(f'bg_{B}_mid', mid_im)


if __name__ == '__main__':
    if '--sweep' in sys.argv:
        i = sys.argv.index('--sweep'); layer = sys.argv[i + 1]; seeds = [int(s) for s in sys.argv[i + 2].split(',')]
        kw = dict(RENDER[layer]); kw.pop('seed'); kw.pop('seam_band', None)
        for k in ('denoise', 'cn', 'pix'):
            if f'--{k}' in sys.argv: kw[k] = float(sys.argv[sys.argv.index(f'--{k}') + 1])
        bgv2b.set_prefix(B)
        print(bgv2b.sweep(SRC, layer, kw.pop('prompt'), seeds, os.path.join(os.environ.get('BG_SWEEP', '/tmp'), B), label=os.environ.get('BG_LABEL'), **kw))
        sys.exit()
    if '--guide' in sys.argv or '--render' in sys.argv: paint_guides()
    if '--render' in sys.argv: do_render()
    if '--guide' not in sys.argv: build(ase='--no-ase' not in sys.argv)
