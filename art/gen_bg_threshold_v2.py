#!/usr/bin/env python3
"""The Ashen Threshold backdrop v2 (bg rollout C, docs/v17/bg_rollout_c.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_threshold_v2.py            build bg_threshold_{far,mid} from the saved renders in art/bg_src/threshold/
  python3 art/gen_bg_threshold_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_threshold_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  --no-ase                                       write previews only, leave the assets alone

The World 2 entrance (CT1 through the broken arch, CT2 the causeway vista). Pale cold ash-light with no sun to make it:
a storm ceiling, a sea of ash-cloud, and far off on the horizon a colossal wall with a seam of light down its middle
(the gate, too far and too vast to read as more than that). The seam sits at far x=340: CT2 shows far x 0..471, so it is on
the right as the player sets out and slides behind the gate prop (screen x ~264 at the east end); CT1 sees it through the
broken arch. The beyond stays vague: no figures, faint impossible shapes in the haze.

Same asset names, size (512x216), tag (`loop`) and frame count as art/gen_forge_env.py (the v1 generator, kept for rollback).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa

B = 'threshold'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#7c8796'
SEAM_X = 340
SEAM_PX = 339    # where the picked render put the seam (1x)

# v1 ramps (gen_forge_env.py threshold_far/mid: 8 colours) extended both ways in the same cold slate family, plus a faint
# warm white for the light behind the wall ("rain on hot stone")
ASH = ['2d3849', '364356', '3f4c60', '4f6079', '566273', '5f6b7d', '6b7686', '76818f', '7c8ea8', '8f9aa8', '9aa4b2', 'a5afbc',
       'b0b9c4', 'b7c0cb', 'c4ccd5', 'd2d8df', 'dfe4ea', 'eef1f4', 'f6f7f8']
WARM = ['e8e2d8', 'f4efe6']
FAR_PAL = [hexc(c) for c in ASH + WARM]
SIL = ['1f2633', '262f3e', '2d3849', '364356', '3f4c60', '4a5669', '566273', '62748f', '6b7686', '7c8796']
MID_PAL = [hexc(c) for c in SIL + ['8f9aa8', 'a5afbc']]

PROMPT_FAR = ('pixel art, dark fantasy, pale cold ash grey overcast sky with long streaks of stratus cloud above an endless sea of '
              'mist, far away on the horizon a titanic ancient stone wall stretching across the world, its top lost in the clouds, a '
              'colossal shut gate recessed in it with a thin vertical seam of white light, sourceless pale light glowing behind the '
              'clouds, a vast broken stair rising into the clouds in the distance, side-scroller game background, muted desaturated '
              'slate blue and ash grey palette, atmospheric perspective, heavy haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, ancient stone causeway viaduct with tall arches, weathered stone obelisks with carved bands '
              'and pyramid caps standing on the causeway, cracked masonry blocks, a broken fallen obelisk, ash dust on the ledges, '
              'isolated on a flat pale background, side-scroller game background layer, cold slate grey stone lit by pale light, detailed')


# -------------------------------------------------------------------------------------------------- guides
def cloud_mass(G, cx, cy, rx, ry, rng, lit_from, base, top, under, n=7):
    """A cloud bank: overlapping ellipses, lit along the side facing the light, darker underside."""
    m = np.zeros_like(G.X)
    for i in range(n):
        ex = cx + rng.uniform(-rx, rx) * 0.75; ey = cy + rng.uniform(-ry, ry) * 0.35
        m = np.maximum(m, G.mask_ellipse(ex, ey, rx * rng.uniform(0.35, 0.6), ry * rng.uniform(0.5, 0.9)))
    m = np.maximum(m, G.mask_ellipse(cx, cy + ry * 0.2, rx, ry * 0.45))
    G.fill(m, base)
    # lit rim: the mask shifted away from the light, subtracted
    dx = np.sign(lit_from - cx) * 2.0
    sh = np.roll(np.roll(m, int(round(-dx * S)), axis=1), int(2 * S), axis=0)
    G.fill(np.clip(m - sh, 0, 1), top, 0.8)
    und = np.clip(m - np.roll(m, int(-3 * S), axis=0), 0, 1)
    G.fill(und, under, 0.6)
    return m


def guide_far():
    rng = np.random.default_rng(21)
    G = Guide(hexc('8f9aa8'))
    nz = tile_noise(WS, HS, 128, 24, 3); nz2 = tile_noise(WS, HS, 32, 8, 4, octaves=2)
    lx, ly = SEAM_X, 112
    near_l = np.exp(-(G.wdx(lx) / 150) ** 2)
    # sky: a storm ceiling (darker, banded strata) brightening toward the horizon and toward the light
    v = 0.18 + 0.55 * smooth(0, 150, G.Y) + 0.25 * near_l * smooth(10, 120, G.Y) + 0.18 * (nz - 0.5)
    strata = 0.07 * np.sin(G.Y * 0.22 + nz2 * 5)
    G.rgb = lerp(hexc('3f4c60'), hexc('dfe4ea'), np.clip(v + strata, 0, 1)[..., None])
    # cloud strata: long streaked layers (no puffy cumulus), darker undersides, edges lit toward the light
    for (y0, y1, cx_, cy_, seed, lo, hi, k) in ((0, 60, 192, 7, 31, '4f6079', '9aa4b2', 0.9), (40, 110, 160, 6, 32, '6b7686', 'c4ccd5', 0.75),
                                               (90, 150, 128, 5, 33, '8f9aa8', 'dfe4ea', 0.6)):
        d = tile_noise(WS, HS, cx_ * S, cy_ * S, seed, octaves=3)
        band = smooth(y0, y0 + 15, G.Y) * (1 - smooth(y1 - 15, y1, G.Y))
        m = smooth(0.52, 0.62, d) * band
        shade = np.clip(0.35 + 0.65 * near_l + 0.4 * (d - 0.55), 0, 1)
        G.fill_img(m, lerp(hexc(lo), hexc(hi), shade[..., None]), k)
        under = np.clip(m - np.roll(m, int(-2 * S), axis=0), 0, 1)
        G.fill(under, hexc(lo), 0.5 * k)
    # the light: no disc. A tall soft glow behind the clouds, centred on the seam, and faint rays fanning down
    G.glow(lx, ly, 70, 110, hexc('dfe4ea'), 0.55, 1.4)
    G.glow(lx, ly + 10, 26, 80, hexc('f6f7f8'), 0.45, 1.2)
    for k, ang in enumerate((-0.55, -0.32, -0.12, 0.1, 0.3, 0.52)):
        x1 = lx + math.tan(ang) * 140
        ray = G.mask_poly([(lx - 2, 40), (lx + 2, 40), (x1 + 9, 180), (x1 - 9, 180)], blur=3)
        G.add(ray * smooth(40, 120, G.Y) * (1 - smooth(130, 180, G.Y)), hexc('eef1f4'), 0.10 + 0.04 * (k % 2))
    # impossible shapes far off, deep in the haze (low contrast)
    haze = hexc('9aa4b2')
    for (x, w, h, lean) in ((36, 6, 92, 0.10), (52, 3, 64, -0.05), (470, 5, 84, 0.13), (488, 3, 50, -0.08)):
        G.fill(G.mask_poly([(x, 150), (x + w, 150), (x + w * 0.5 + lean * h, 150 - h)]), haze, 0.55)
    # the wall at the edge of the world: colossal, its upper reaches dissolving into the cloud, deep in haze; a seam of light
    # down its middle where the gate is (too far and too vast to read as more than a recess and a line of light)
    # it runs the whole width (wrapping): highest at the gate, where its top is lost in the cloud, lower, broken and hazier
    # away from it, so it has no box ends
    dg = np.abs(G.wdx(lx))
    ragged = 8 * (tile_noise(WS, 1, 10 * S, 1, 9, 2)[0] - 0.5)[None, :] + 5 * (tile_noise(WS, 1, 3 * S, 1, 10, 1)[0] > 0.6)[None, :]
    wtop = 40 + 78 * smooth(30, 230, dg) + ragged * smooth(40, 120, dg)
    rise = (1 - smooth(20, 70, G.Y)) * (1 - smooth(60, 120, dg))       # near the gate it fades upward into the cloud
    wall = smooth(-1.5, 1.5, G.Y - wtop) * (1 - rise) * (G.Y < 156)
    far_k = smooth(60, 240, dg)                                          # haze with distance from the gate
    wv = 0.36 + 0.25 * np.exp(-(dg / 70) ** 2) + 0.18 * smooth(70, 156, G.Y) + 0.06 * (nz2 - 0.5) + 0.22 * far_k
    G.fill_img(wall, lerp(hexc('566273'), hexc('a5afbc'), np.clip(wv, 0, 1)[..., None]), 0.92)
    for y in range(52, 156, 11):     # huge courses, faint
        G.fill(G.mask_lines([(0, y, W, y, 0.5)]) * wall * (1 - far_k), hexc('4f6079'), 0.25)
    for bx in (226, 282, 398, 454, 120, 30):  # buttresses
        d_ = abs(((bx - lx + W / 2) % W) - W / 2); t_ = 40 + 78 * float(smooth(30, 230, d_)) - 10
        bm = G.mask_poly([(bx - 7, 156), (bx + 7, 156), (bx + 5, t_), (bx - 5, t_)]) * (1 - rise)
        G.fill(bm, lerp(hexc('6b7686'), hexc('a5afbc'), float(smooth(60, 240, d_))), 0.8)
        G.fill(bm * (G.wdx(bx) > 3), hexc('9aa4b2'), 0.35)
    # the gate: a tall pointed recess, shut, the seam of light down its middle
    G.fill(G.mask_poly(arch_pts(lx, 24, 80, 30, 156)), hexc('8f9aa8'), 0.8)        # lit outer order
    G.fill(G.mask_poly(arch_pts(lx, 20, 82, 36, 156)), hexc('4f6079'), 0.9)
    G.fill(G.mask_poly(arch_pts(lx, 15, 86, 44, 156)), hexc('3f4c60'), 0.9)
    G.fill(G.mask_lines([(lx, 46, lx, 156, 0.9)]), hexc('f6f7f8'), 0.95)
    G.glow(lx, 110, 9, 60, hexc('f4efe6'), 0.45, 1.5)
    # the sea of ash-cloud below the horizon: billowing tops lit pale, darker troughs, mist veiling the wall's foot
    sea_top = 150 + 4 * np.sin(G.X * 0.09) + 3 * np.sin(G.X * 0.23 + 1) + 4 * (tile_noise(WS, 1, 16, 1, 11)[0] - 0.5)[None, :]
    sea = (G.Y > sea_top).astype(float)
    sv = 0.75 - 0.35 * smooth(150, 216, G.Y) + 0.15 * (nz2 - 0.5) + 0.12 * near_l
    G.fill_img(sea, lerp(hexc('6b7686'), hexc('dfe4ea'), np.clip(sv, 0, 1)[..., None]))
    for k in range(26):   # billow rows
        bx = rng.uniform(0, W); by = rng.uniform(160, 206); r = rng.uniform(8, 20)
        G.fill(G.mask_ellipse(bx, by, r * 1.8, r * 0.5), lerp(hexc('8f9aa8'), hexc('c4ccd5'), 1 - (by - 160) / 50), 0.6)
        G.fill(G.mask_ellipse(bx, by - r * 0.25, r * 1.4, r * 0.2), hexc('d2d8df'), 0.5)
    G.add(np.exp(-((G.Y - 152) / 8) ** 2), hexc('b7c0cb'), 0.12)
    return G


def masonry(G, mask, base, course=5.0, bw=9.0, seed=0, lit_x=SEAM_X):
    yi = np.floor(G.Y / course); off = (yi % 2) * bw / 2
    xi = np.floor((G.X + off) / bw)
    jit = (((xi.astype(np.int64) % 512) * 73856093 ^ yi.astype(np.int64) * 19349663 ^ seed * 83492791) & 1023) / 1023.0
    v = 0.85 + 0.3 * jit
    col = base[None, None] * v[..., None]
    fy = (G.Y / course) % 1; fx = ((G.X + off) / bw) % 1
    mort = (fy < 0.18) | (fx < 0.1)
    col = np.where(mort[..., None], col * 0.62, col)
    G.fill_img(mask, col)


def obelisk(G, x, h, w, deck, rng, broken=False, bands=2):
    top = deck - h
    body = G.mask_poly([(x - w / 2, deck), (x + w / 2, deck), (x + w * 0.36, top), (x - w * 0.36, top)])
    masonry(G, body, hexc('7c8ea8'), course=7, bw=w + 2, seed=int(x))
    G.fill(body * (G.wdx(x) > w * 0.12), hexc('a5afbc'), 0.55)        # lit face (the light is east)
    G.fill(body * (G.wdx(x) < -w * 0.2), hexc('4f6079'), 0.5)
    for k in range(bands):   # carved bands
        y = top + h * (0.18 + 0.22 * k)
        G.fill(G.mask_lines([(x - w * 0.42, y, x + w * 0.42, y, 1.0)]) * body, hexc('4f6079'), 0.8)
        G.fill(G.mask_lines([(x - w * 0.42, y + 1.2, x + w * 0.42, y + 1.2, 0.6)]) * body, hexc('b7c0cb'), 0.6)
    if broken:   # a snapped top: jagged
        pts = [(x - w * 0.36, top), (x - w * 0.2, top - 4), (x - w * 0.05, top - 1), (x + w * 0.1, top - 6), (x + w * 0.36, top)]
        G.fill(G.mask_poly(pts), hexc('7c8ea8'))
    else:    # pyramidion
        G.fill(G.mask_poly([(x - w * 0.38, top), (x + w * 0.38, top), (x, top - w * 0.9)]), hexc('8f9aa8'))
        G.fill(G.mask_poly([(x, top), (x + w * 0.38, top), (x, top - w * 0.9)]), hexc('b7c0cb'), 0.7)
    # plinth
    G.fill(G.mask_poly([(x - w / 2 - 3, deck), (x + w / 2 + 3, deck), (x + w / 2 + 2, deck - 4), (x - w / 2 - 2, deck - 4)]), hexc('6b7686'))
    G.fill(G.mask_lines([(x - w / 2 - 2, deck - 4, x + w / 2 + 2, deck - 4, 0.8)]), hexc('a5afbc'), 0.8)


def guide_mid():
    rng = np.random.default_rng(23)
    G = Guide(hexc('a5afbc'), alpha=True)
    deck = 152
    # the viaduct: spandrel wall from the deck down, arches cut out at an irregular rhythm
    body = (G.Y > deck).astype(float)
    masonry(G, body, hexc('6b7686'), course=6, bw=11, seed=3)
    G.a = np.maximum(G.a, body)
    piers = [(0, 22), (80, 20), (154, 24), (236, 20), (304, 22), (382, 20), (446, 24), (512, 22)]
    for i in range(len(piers) - 1):
        (x0, w0), (x1, w1) = piers[i], piers[i + 1]
        a0, a1 = x0 + w0 / 2, x1 - w1 / 2
        cx, half = (a0 + a1) / 2, (a1 - a0) / 2
        spring = deck + 22 + (i % 3) * 3
        op = G.mask_poly(arch_pts(cx, half, spring, spring - half * 0.9, 230, pointed=(i % 2 == 0), n=30))
        if i == 4:   # a collapsed span: the arch and the deck above it gone, a ragged break
            jag = deck + 3 + 6 * (tile_noise(WS, HS, 4, 4, 51, 1) - 0.5)
            gap = ((G.X > a0 + 6) & (G.X < a1 - 8) & (G.Y < jag + 12 * (1 - np.abs(G.X - cx) / half))).astype(float)
            op = np.maximum(op, gap * (G.Y > deck - 2))
        # voussoir ring
        ring = np.clip(G.mask_poly(arch_pts(cx, half + 4, spring, spring - half * 0.9 - 4, 230, pointed=(i % 2 == 0), n=30)) - op, 0, 1)
        G.fill(ring * (G.Y > deck + 3), hexc('7c8ea8'), 0.8)
        G.fill(ring * (G.Y > deck + 3) * (G.wdx(cx) < 0), hexc('566273'), 0.4)
        G.rgb = G.rgb * (1 - op[..., None]) + hexc('a5afbc') * op[..., None]
        G.a = G.a * (1 - op)
        # intrados lit on the east-facing side
        lip = np.clip(op - np.roll(op, int(-1.5 * S), axis=1), 0, 1) * (G.wdx(cx) > -half * 0.2)
    # deck: cornice with a lit top edge, a low parapet
    G.fill(G.mask_poly([(0 - W, deck - 1), (2 * W, deck - 1), (2 * W, deck + 4), (0 - W, deck + 4)]) * (G.a > 0.5) + 0 * G.X, hexc('8f9aa8'))
    G.fill(G.mask_lines([(0, deck - 1, W, deck - 1, 0.9)]), hexc('c4ccd5'))
    G.a = np.maximum(G.a, G.mask_lines([(0, deck - 1, W, deck - 1, 0.9)]) * (1 - ((G.X > 304 + 13) & (G.X < 382 - 14))))
    # the obelisks and stumps on the causeway (no figures)
    d = deck - 1
    obelisk(G, 40, 88, 15, d, rng, bands=3)                   # the tall one
    # a fluted column stump, snapped
    stump = G.mask_poly([(112, d), (128, d), (127, d - 30), (124, d - 34), (120, d - 29), (116, d - 36), (113, d - 31)])
    masonry(G, stump, hexc('7c8ea8'), course=9, bw=40, seed=5)
    for fx_ in (115, 118.5, 122, 125.5):
        G.fill(G.mask_lines([(fx_, d - 2, fx_, d - 30, 0.7)]) * stump, hexc('566273'), 0.6)
    G.fill(stump * (G.X > 124), hexc('a5afbc'), 0.5)
    # a cenotaph: a long block on a stepped base with a carved ring
    G.fill(G.mask_poly([(176, d), (216, d), (214, d - 4), (178, d - 4)]), hexc('6b7686'))
    ceno = G.mask_poly([(181, d - 4), (211, d - 4), (211, d - 24), (181, d - 24)])
    masonry(G, ceno, hexc('7c8ea8'), course=10, bw=15, seed=9)
    G.fill(G.mask_poly([(179, d - 24), (213, d - 24), (210, d - 28), (182, d - 28)]), hexc('8f9aa8'))
    G.fill(np.clip(G.mask_ellipse(196, d - 14, 6, 6) - G.mask_ellipse(196, d - 14, 4.2, 4.2), 0, 1), hexc('4f6079'))
    G.fill(ceno * (G.X > 208), hexc('a5afbc'), 0.5)
    obelisk(G, 272, 64, 13, d, rng, broken=True, bands=2)
    # a ruined portal on the causeway: two posts and a cracked lintel (an echo of the gate)
    for px_ in (416, 446):
        post = G.mask_poly([(px_ - 5, d), (px_ + 5, d), (px_ + 4, d - 62), (px_ - 4, d - 62)])
        masonry(G, post, hexc('7c8ea8'), course=8, bw=12, seed=px_)
        G.fill(post * (G.wdx(px_) > 1.5), hexc('a5afbc'), 0.5)
    G.fill(G.mask_poly([(406, d - 62), (433, d - 62), (431, d - 70), (408, d - 69)]), hexc('8f9aa8'))
    G.fill(G.mask_poly([(434, d - 63), (456, d - 61), (455, d - 69), (435, d - 71)]), hexc('8f9aa8'))
    G.fill(G.mask_lines([(406, d - 69, 456, d - 69, 0.8)]), hexc('c4ccd5'), 0.8)
    obelisk(G, 492, 34, 11, d, rng, broken=True, bands=1)
    # a fallen obelisk lying across the break, its tip in the gap
    fallen = G.mask_poly([(326, deck - 2), (380, deck + 10), (378, deck + 16), (324, deck + 5)])
    masonry(G, fallen, hexc('76818f'), course=4, bw=8, seed=7)
    G.fill(G.mask_lines([(326, deck - 2, 380, deck + 10, 0.9)]), hexc('b0b9c4'), 0.9)
    # rubble at the foot of the broken span
    for (bx, by, r) in ((330, 212, 5), (346, 214, 4), (366, 211, 6)):
        pts = [(bx + r * 1.4 * math.cos(a) + rng.uniform(-1, 1), by + r * math.sin(a) * 0.7) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
        G.fill(G.mask_poly(pts), hexc('6b7686')); G.fill(G.mask_poly([(x, min(y, by - 1)) for x, y in pts]), hexc('a5afbc'), 0.6)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image(), lo=10).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=8, denoise=0.62, cn=0.55, cn_end=0.7, pix=0.4, guide_blur=1.5),
    'mid': dict(prompt=PROMPT_MID, seed=2, denoise=0.62, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=1.0, seam_band=96),
}


def do_render(layers=('far', 'mid')):
    times = {}
    for layer in layers:
        times[layer] = round(render_layer(SRC, layer, **RENDER[layer]), 1)
    print('render s', times)


def far_post(a, stage):
    """'hi': aerial haze over the wall (it should stay vague: the beyond is not shown, only felt), stronger upward and away
    from the gate; the light behind it. 'lo': the seam of light down the gate (x=SEAM_X), 1 px, kept crisp."""
    h, w = a.shape[:2]
    if stage == 'hi':
        yy, xx = np.mgrid[0:h, 0:w] / S
        dg = np.abs((xx - SEAM_X + W / 2) % W - W / 2)
        haze = hexc('a5afbc')
        k = (0.08 + 0.12 * (1 - smooth(40, 150, yy)) + 0.12 * smooth(40, 200, dg)) * (1 - smooth(148, 162, yy))
        k *= 1 - 0.55 * np.exp(-((xx - SEAM_X) / 14) ** 2) * (yy > 60)      # the gate's recess stays a little darker
        out = a * (1 - k[..., None]) + haze * k[..., None]
        glow = np.exp(-((xx - SEAM_X) / 70) ** 2) * np.exp(-((yy - 70) / 70) ** 2)      # light from behind the wall
        out = out + glow[..., None] * (hexc('eef1f4') - out) * 0.62
        sea = smooth(146, 170, yy)                                            # the mist sea: mid-grey, not glare
        lum = out.mean(2, keepdims=True)
        out = out * (1 - 0.55 * sea[..., None]) + (hexc('7c8796') * 0.75 + lum * 0.25 * np.array([0.95, 1.0, 1.08])) * 0.55 * sea[..., None]
        ceil = (1 - smooth(0, 70, yy)) * (1 - 0.6 * np.exp(-(dg / 60) ** 2))   # the storm ceiling: darker overhead
        out = out * (1 - 0.12 * ceil[..., None]) + hexc('3f4c60') * 0.05 * ceil[..., None]
        return np.clip(out, 0, 255)
    out = a.copy()
    for y in range(40, 152):     # the picked render (seed 8) already has a clean seam: only sharpen it to 1 px
        t = float(smooth(40, 70, y))
        out[y, SEAM_PX] = out[y, SEAM_PX] * (1 - t) + hexc('f6f7f8') * t
        for dx in (-1, 1):
            out[y, SEAM_PX + dx] = out[y, SEAM_PX + dx] * (1 - 0.35 * t) + hexc('dfe4ea') * 0.35 * t
    return out


DECK = 152


def fill_vaults(mid, al):
    """The arch openings under the deck are filled (opaque): the shadowed underside of each vault, lifting to mist at the
    foot of the piers. Seen through, the far layer's bright cloud sea sat right behind the player at causeway height and
    the room lights blew it out to white."""
    h, w = al.shape
    yy, xx = np.mgrid[0:h, 0:w]
    hole = (~al) & (yy > DECK + 2)
    # the depth of each hole pixel below the solid above it (0 at the vault crown)
    depth = np.zeros((h, w)); run = np.zeros(w)
    for y in range(h):
        run = np.where(hole[y], run + 1, 0); depth[y] = run
    ramp_ = [hexc(c) for c in ('3f4c60', '4a5669', '566273', '62748f', '6b7686', '7c8796', '8f9aa8')]
    t = np.clip(depth / 30, 0, 1) * 0.7 + 0.3 * smooth(DECK + 20, 216, yy)
    f = t * (len(ramp_) - 1); i = np.floor(f).astype(int); fr = f - i
    i = np.where(fr > (B4[yy & 3, xx & 3] + 0.5) / 16, i + 1, i).clip(0, len(ramp_) - 1)
    col = np.array(ramp_)[i]
    out = np.where(hole[..., None], col, mid)
    return out, al | hole


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=4, grade_kw=dict(black=0, white=255, gamma=1.0, sat=0.6), post=far_post, dk=0.3)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=2,
                                  grade_kw=dict(black=0, white=300, gamma=0.95, sat=0.5), rim_col=hexc('b7c0cb'))
    mid, al = fill_vaults(mid, al)
    far_im, mid_im = to_rgba(far), to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png')
    preview(far_im, mid_im, TINT, f'{SRC}/preview.png')
    st = {'far': stats(far_im), 'mid': stats(mid_im), 'accents_far': ['%02x%02x%02x' % c for c in acc_f], 'accents_mid': ['%02x%02x%02x' % c for c in acc_m]}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase:
        ase_build(f'bg_{B}_far', far_im); ase_build(f'bg_{B}_mid', mid_im)


if __name__ == '__main__':
    if '--guide' in sys.argv or '--render' in sys.argv: paint_guides()
    if '--render' in sys.argv: do_render()
    if '--guide' not in sys.argv: build(ase='--no-ase' not in sys.argv)
