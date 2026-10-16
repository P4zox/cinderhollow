#!/usr/bin/env python3
"""The Burning Deep backdrop v2 (bg rollout agent A, docs/v17/bg_rollout_a.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_deep_v2.py               build bg_deep_{far,mid} from the saved renders in art/bg_src/deep/
  python3 art/gen_bg_deep_v2.py --guide       only (re)paint the layout guides
  python3 art/gen_bg_deep_v2.py --sweep far 1,2,3,4 [tag]   guides + pass-1 renders for those seeds (ComfyUI on :8188)
  python3 art/gen_bg_deep_v2.py --finish      seam pass for the picked sweep renders (PICK), then build
  --no-ase                                     write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/deep_bg.py (rollback: restore art/bg_src/deep/v1/).
v1: repeating kiln cones with orange "eye" blobs, ruler-straight sine lava falls, flat cartoon gears and pipes (a steampunk
read). v2: a root-forge cavern -- petrified heartwood roots hanging from the vault, three different distant furnace works with
molten seams, ragged lava curtains that widen and break as they fall, a crusted molten sea; the mid layer is root-bound iron
girders, chains and crucibles, and a great anvil, rim-lit from the heat below.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgroll_a_lib as A

B = 'deep'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#170604'

# v1 ramps (deep_bg.py SKY / SIL / MG / IRN / RIM)
SKY = ['060303', '0a0505', '0e0706', '130908', '190c0a', '200f0b', '28130d', '31170f', '3c1c10', '4a2212', '5a2913', '6d3114', '833a14', '9c4515', 'b85418', 'd6661c']
SIL = ['070404', '0b0605', '100807', '160a08', '1d0d0a', '26110c']
MG = ['3a0906', '661107', '9c1f09', 'cf3b0c', 'f26414', 'ff9a2e', 'ffcf66', 'fff3cc']
IRN = ['050303', '0a0606', '100a09', '18100e', '221612', '2e1d17', '3a2620', '4a3028']
RIM = ['5a1a08', '8a2c0c', 'c04a12', 'f07a22', 'ffb050']
FAR_PAL = [hexc(c) for c in SKY + SIL + MG]
MID_PAL = [hexc(c) for c in IRN + RIM + MG[:4]]

PROMPT_FAR = ('pixel art, dark fantasy, a vast volcanic root-forge cavern, a ceiling of colossal petrified tree roots hanging down, '
              'distant monumental furnace towers and smelting works with glowing molten cracks, ragged curtains of lava pouring from '
              'high ledges and breaking into spray, a crusted molten sea glowing below, rising smoke and heat haze, embers, '
              'side-scroller game background, deep warm black, rust and ember orange palette, atmospheric depth, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, massive riveted iron girders and beams bound and overgrown by thick petrified roots, heavy hanging '
              'chains with iron crucibles pouring thin streams of molten metal, a giant blacksmith anvil on a stone plinth, '
              'isolated on a flat grey background, side-scroller game background layer, dark iron and charred wood lit orange from below, detailed')


def lava_fall(G, x0, y0, y1, w, seed, n_strands=4, lean=0.0):
    """A lava fall pouring over a rock lip: several wavering strands of different widths (some breaking into drops), a hot core,
    a glow halo and a steam/spray burst where it lands. Never a ruler-straight line."""
    r = np.random.default_rng(seed)
    nzf = tile_noise(WS, HS, 8, 24, 100 + seed, 2)
    for k in range(n_strands):
        off = (k - (n_strands - 1) / 2) * w / max(1, n_strands - 1) + r.normal(0, w * 0.1)
        sw = w * r.uniform(0.18, 0.45); segs = []; x, y = x0 + off, y0; wob = 0.0
        brk = r.uniform(0.55, 0.95) if r.random() < 0.5 else 2.0
        while y < y1:
            t = (y + 3 - y0) / (y1 - y0)
            wob = float(np.clip(wob + r.normal(0, 0.4), -2.5, 2.5))
            nx_ = x0 + off * (1 + 0.5 * t) + lean * 1.8 * t * t + wob + 0.8 * math.sin(y / (7 + k) + seed)
            ny_ = y + 3
            if t < brk or r.random() < 0.35:
                segs.append((x, y, nx_, ny_, sw * (1 + 0.6 * t)))
            x, y = nx_, ny_
        G.fill(G.mask_lines(segs), hexc('f26414'))
        G.fill(G.mask_lines([(a, b, c, d, e * 0.4) for a, b, c, d, e in segs]), hexc('ffcf66'))
    G.glow(x0 + lean, (y0 + y1) / 2, w * 2.4 + 6, (y1 - y0) * 0.6, hexc('5a1a08'), 0.9, 1.2)
    G.glow(x0 + lean * 1.8, y1, w * 2 + 10, 12, hexc('ff9a2e'), 0.9)
    for _ in range(40):
        G.fill(G.mask_ellipse(x0 + lean * 1.8 + r.normal(0, w + 4), y1 - abs(r.normal(0, 9)), 0.8, 0.8), hexc('ffcf66'))
    # steam rising from the impact (dark-warm, soft)
    G.fill(np.exp(-((G.wdx(x0 + lean * 1.8) / (w + 10)) ** 2)) * smooth(y1 - 70, y1, G.Y) * (G.Y < y1) * 0.35, hexc('6d3114'))
    # the lip it pours over
    G.fill(G.mask_poly([(x0 - w - 10, y0 - 3), (x0 + w + 10, y0 - 3), (x0 + w + 6, y0 + 4), (x0 - w - 8, y0 + 4)]), hexc('1d0d0a'))
    G.fill(G.mask_lines([(x0 - w * 0.7, y0 + 0.5, x0 + w * 0.7, y0 + 0.5, 1.6)]), hexc('ffcf66'))


def cascade(G, pts, w, seed, end_y=192):
    """A stepped lava cascade: it arcs off each rock lip, drops, pools along the next ledge and spills again, so no fall is a
    straight column. pts = the lips [(x, y), ...] from the top; the last drop runs to end_y."""
    r = np.random.default_rng(seed)
    lips = list(pts) + [(pts[-1][0] + (pts[-1][0] - pts[-2][0]) * 0.3 if len(pts) > 1 else pts[-1][0], end_y)]
    for i in range(len(lips) - 1):
        (xa, ya), (xb, yb) = lips[i], lips[i + 1]
        d = 1 if xb >= xa else -1
        ww = w * (0.8 + 0.25 * i)
        # the ledge it spilled from (dark rock, lit top edge)
        G.fill(G.mask_poly([(xa - d * 16, ya - 1), (xa + d * 2, ya - 1), (xa + d * 3, ya + 5), (xa - d * 14, ya + 7)]), hexc('1d0d0a'))
        # the arc off the lip, then the drop (parabola), as a few strands
        for k in range(3):
            o = (k - 1) * ww * 0.3; segs = []; px_, py_ = xa + o, ya
            for t in np.linspace(0, 1, 30)[1:]:
                x = xa + o + d * (6 + ww * 0.4) * math.sqrt(t) + r.normal(0, 0.35)
                y = ya + (yb - ya) * t
                segs.append((px_, py_, x, y, ww * (0.35 if k == 1 else 0.22) * (1 + 0.5 * t))); px_, py_ = x, y
            G.fill(G.mask_lines(segs), hexc('f26414'))
            if k == 1: G.fill(G.mask_lines([(a, b, c, e_, f * 0.45) for a, b, c, e_, f in segs]), hexc('ffcf66'))
        xl = xa + d * (6 + ww * 0.4)
        # the pool running along the next ledge to its lip
        if i < len(lips) - 2:
            G.fill(G.mask_lines([(xl, yb - 1, xb, yb - 1, 2.0)]), hexc('ff9a2e'))
        G.glow(xl, yb, ww * 2 + 8, 8, hexc('ff9a2e'), 0.8)
        G.glow((xa + xl) / 2, (ya + yb) / 2, ww * 2 + 8, (yb - ya) * 0.6 + 4, hexc('5a1a08'), 0.8, 1.2)
        for _ in range(14):
            G.fill(G.mask_ellipse(xl + r.normal(0, ww + 3), yb - abs(r.normal(0, 5)), 0.8, 0.8), hexc('ffcf66'))


def guide_far():
    rng = np.random.default_rng(3)
    G = Guide(hexc('100807'))
    nz = tile_noise(WS, HS, 64, 32, 31); nz2 = tile_noise(WS, HS, 16, 48, 32, 2)
    # haze: dark vault, glowing floor; hotter behind the great furnace and the falls
    v = 0.04 + 0.6 * smooth(30, 216, G.Y) ** 1.5
    for (fx, k) in ((178, 0.32), (400, 0.18), (84, 0.14)):
        v = v + k * np.exp(-(G.wdx(fx) / 80) ** 2) * smooth(40, 216, G.Y)
    v = np.clip(v + 0.08 * (nz - 0.5), 0, 1)
    G.rgb = lerp(hexc('0e0706'), hexc('b85418'), v[..., None] ** 1.2)
    # depth 1 (farthest): hazy cavern pillars and a far rock wall, orange-brown in the heat haze
    for (px, w0, w1, top) in ((30, 18, 34, 20), (268, 14, 26, 40), (470, 22, 40, 10)):
        G.fill(G.mask_poly([(px - w1, 196), (px - w0, top + 40), (px - w0 * 0.7, top), (px + w0 * 0.7, top), (px + w0, top + 40), (px + w1, 196)]), hexc('5a2913'), 0.55)
    # smoke columns rising from the works (dark against the glow)
    for sx in (150, 236, 336, 452):
        m = np.exp(-((G.wdx(sx + 9 * np.sin(G.Y / 21 + sx)) / (9 + 0.12 * (216 - G.Y))) ** 2)) * smooth(0, 140, 200 - G.Y) * (0.5 + 0.5 * nz2)
        G.fill(m * 0.55, hexc('1d0d0a'))
    # (1) the great furnace (focal, x 178): a massive stepped forge-temple with buttresses, an arched glowing mouth behind bars
    fx = 178
    G.fill(G.mask_poly([(fx - 62, 200), (fx - 54, 124), (fx - 40, 116), (fx - 34, 74), (fx - 18, 66), (fx - 14, 28), (fx + 14, 28), (fx + 18, 66),
                        (fx + 34, 74), (fx + 40, 116), (fx + 54, 124), (fx + 62, 200)]), hexc('26110c'))
    for bx in (-48, 48):   # buttresses
        G.fill(G.mask_poly([(fx + bx - 8, 200), (fx + bx - 3, 120), (fx + bx + 3, 120), (fx + bx + 8, 200)]), hexc('1d0d0a'))
    mouth = G.mask_poly(arch_pts(fx, 17, 166, 142, 200, pointed=False, n=30))
    G.fill(mouth, hexc('ff9a2e'))
    G.glow(fx, 188, 26, 20, hexc('fff3cc'), 0.8)
    for gx in np.arange(fx - 14, fx + 15, 5):
        G.fill(G.mask_lines([(gx, 150, gx, 200, 1.0)]), hexc('3c1c10'))
    G.glow(fx, 176, 70, 44, hexc('cf3b0c'), 0.7, 1.4)
    G.glow(fx, 26, 12, 8, hexc('f26414'), 0.9)                                   # the flue's glow at the top
    for (x0, y0, x1, y1) in ((160, 80, 156, 110), (198, 74, 204, 106), (176, 36, 172, 60), (132, 130, 128, 166), (226, 126, 230, 160)):
        segs = []; x, y = x0, y0
        for i in range(7):
            nx_, ny_ = x + (x1 - x0) / 7 + rng.uniform(-1.2, 1.2), y + (y1 - y0) / 7
            segs.append((x, y, nx_, ny_, 0.8)); x, y = nx_, ny_
        G.fill(G.mask_lines(segs), hexc('f26414'))
    G.fill(G.mask_lines([(fx - 18, 66, fx + 18, 66, 1.0), (fx - 40, 116, fx + 40, 116, 1.0)]), hexc('9c4515'))
    # (2) a slender chimney stack (x 330), banded, glowing crown
    G.fill(G.mask_poly([(318, 200), (322, 64), (325, 44), (339, 44), (342, 64), (346, 200)]), hexc('1d0d0a'))
    G.glow(332, 42, 16, 9, hexc('f26414'), 0.8)
    for k in range(8):
        y = 70 + k * 16; G.fill(G.mask_lines([(321, y, 343, y, 1.0)]), hexc('3c1c10'))
    G.fill(G.mask_lines([(330, 90, 333, 120, 0.8), (333, 120, 331, 150, 0.8)]), hexc('cf3b0c'))
    # (3) a broad crucible works (x 450) on stilts, a spout pouring
    G.fill(G.mask_poly([(418, 160), (424, 138), (476, 138), (482, 160)]), hexc('1d0d0a'))
    for sx in (426, 450, 474):
        G.fill(G.mask_lines([(sx, 160, sx, 200, 2.4)]), hexc('1d0d0a'))
    G.fill(G.mask_lines([(476, 146, 490, 142, 2)]), hexc('1d0d0a'))
    cascade(G, [(490, 142)], 2.5, 9)
    # lava cascades: stepped falls arcing off rock lips, pooling on ledges, spilling again (never a straight column)
    cascade(G, [(70, 28), (88, 96), (78, 148)], 6, 1)
    cascade(G, [(254, 58), (270, 128)], 3, 2)
    cascade(G, [(380, 14), (396, 70), (410, 122)], 8, 3)
    # the petrified root ceiling: a dense canopy of gnarled roots, undersides lit by the glow below
    segs = []
    for rx in np.arange(0, W, 22) + rng.uniform(-6, 6, len(np.arange(0, W, 22))):
        segs += root_segs(rng, rx, -6, math.pi / 2 + rng.normal(0, 0.35), rng.uniform(28, 70), rng.uniform(5, 11), 2, step=2.5, droop=0.03)
    G.fill(G.mask_lines(segs), hexc('1d0d0a'))
    G.fill(G.mask_lines([(x0 + 0.3 * w * 0.3, y0 + 0.45 * w * 0.3 + 0.6, x1 + 0.3 * w * 0.3, y1 + 0.45 * w * 0.3 + 0.6, w * 0.3) for x0, y0, x1, y1, w in segs if w > 2]), hexc('833a14'), 0.8)
    G.fill((G.Y < 9 + 6 * tile_noise(WS, HS, 32, 8, 33, 2)).astype(float), hexc('130908'))
    # the molten sea: a glowing surface broken into dark crust floes, brightest at the far shore line
    sea = smooth(192, 196, G.Y)
    floes = tile_noise(WS, HS, 24, 6, 34, 3)
    crust = smooth(0.5, 0.56, floes)
    sea_col = lerp(hexc('ff9a2e'), hexc('31170f'), crust[..., None] * 0.9)
    sea_col = lerp(sea_col, hexc('cf3b0c'), smooth(198, 216, G.Y)[..., None] * 0.4)
    G.fill_img(sea, sea_col)
    G.fill(np.clip(1 - np.abs(G.Y - 193) / 1.2, 0, 1), hexc('ffcf66'), 0.85)
    return G


def guide_mid():
    rng = np.random.default_rng(8)
    G = Guide(hexc('808080'), alpha=True)
    iron = hexc('5a4038'); lit = hexc('e8803a'); dark = hexc('3a2620')
    def girder(x0, y0, x1, y1, w):
        G.fill(G.mask_lines([(x0, y0, x1, y1, w)]), iron)
        nx_, ny_ = -(y1 - y0), (x1 - x0); L = math.hypot(nx_, ny_); nx_, ny_ = nx_ / L, ny_ / L
        o = w * 0.38
        G.fill(G.mask_lines([(x0 + nx_ * o, y0 + ny_ * o, x1 + nx_ * o, y1 + ny_ * o, w * 0.22)]), lit, 0.8)     # lit lower flange
        G.fill(G.mask_lines([(x0 - nx_ * o, y0 - ny_ * o, x1 - nx_ * o, y1 - ny_ * o, w * 0.18)]), dark)
        n = int(math.hypot(x1 - x0, y1 - y0) / 6)
        for i in range(n):   # rivets
            t = (i + 0.5) / n; G.fill(G.mask_ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.7, 0.7), hexc('8a5a40'))
    # a braced gantry: two columns, a cross beam, diagonal braces (wraps across the seam on the right)
    for (cx, top) in ((40, 70), (150, 90)):
        G.fill(G.mask_poly([(cx - 5, top), (cx + 5, top), (cx + 6, 216), (cx - 6, 216)]), iron)
        G.fill(G.mask_lines([(cx + 4.5, top, cx + 5.5, 216, 1.2)]), lit, 0.7)
    girder(20, 92, 172, 100, 7); girder(40, 100, 150, 180, 4); girder(150, 104, 40, 186, 4)
    girder(300, 40, 512 + 36, 66, 8)                                            # a long beam over the seam
    G.fill(G.mask_poly([(394, 66), (402, 66), (404, 216), (392, 216)]), iron)
    # petrified roots binding the iron
    segs = []
    for (x, y, a, ln, w) in ((10, -4, 1.3, 120, 9), (120, -4, 1.9, 90, 7), (330, -4, 1.4, 70, 8), (430, -4, 1.7, 150, 10)):
        segs += root_segs(rng, x, y, a, ln, w, 2, step=2.5, droop=0.04)
    for (x, y) in ((60, 96), (150, 100), (396, 70), (360, 56)):   # roots coiled around the beams
        segs += root_segs(rng, x, y, math.pi / 2 + rng.normal(0, 0.4), 40, 4, 1, step=2, droop=0.05)
    G.fill(G.mask_lines(segs), hexc('4a3028'))
    G.fill(G.mask_lines([(x0 + 0.35 * w, y0 + 0.3 * w, x1 + 0.35 * w, y1 + 0.3 * w, w * 0.3) for x0, y0, x1, y1, w in segs if w > 2]), hexc('b0602a'), 0.6)
    # chains with crucibles, one pouring
    for (cx, y1, pour) in ((236, 120, True), (276, 84, False), (466, 140, False)):
        for y in range(0, int(y1), 4):
            G.fill(G.mask_ellipse(cx, y + 2, 1.2 if (y // 4) % 2 else 0.6, 2.0), hexc('6a4a40'))
        G.fill(G.mask_poly([(cx - 9, y1), (cx + 9, y1), (cx + 7, y1 + 12), (cx - 7, y1 + 12)]), iron)
        G.fill(G.mask_lines([(cx - 9, y1, cx + 9, y1, 1.4)]), hexc('ffb050'))
        if pour:
            G.fill(G.mask_lines([(cx + 9, y1 + 1, cx + 13, y1 + 8, 1.6), (cx + 13, y1 + 8, cx + 14, 200, 1.2)]), hexc('ffcf66'))
    # the great anvil on a stone plinth
    ax = 330
    G.fill(G.mask_poly([(ax - 22, 216), (ax - 18, 188), (ax + 18, 188), (ax + 22, 216)]), hexc('4a3a34'))
    G.fill(G.mask_poly([(ax - 10, 188), (ax - 8, 176), (ax + 8, 176), (ax + 10, 188)]), iron)
    G.fill(G.mask_poly([(ax - 30, 176), (ax - 40, 170), (ax - 22, 166), (ax + 26, 166), (ax + 30, 176)]), iron)
    G.fill(G.mask_lines([(ax - 38, 167, ax + 28, 165, 1.4)]), lit, 0.9)
    # slag and broken stone at the base, the floor line
    G.fill((G.Y > 204 + 3 * tile_noise(WS, HS, 16, 4, 81, 2)).astype(float), hexc('2e1d17'))
    G.fill(np.clip(1 - np.abs(G.Y - (204 + 3 * tile_noise(WS, HS, 16, 4, 81, 2))) / 0.8, 0, 1), hexc('c04a12'), 0.7)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image(), lo=10).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=1, denoise=0.78, cn=0.45, cn_end=0.6, pix=0.6, guide_blur=1.3),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.58, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=0.8, seam_band=96),
}
PICK = {'far': ('c', 3), 'mid': ('', 1)}   # (sweep tag, seed) picked by eye


def do_sweep(layer, seeds, tag=''):
    A.use_prefix(B); kw = dict(RENDER[layer]); kw.pop('seed'); kw.pop('seam_band', None)
    A.sweep(SRC, layer, seeds=seeds, tag=tag, **kw)


def do_finish():
    A.use_prefix(B)
    import shutil
    tag, seed = PICK['far']   # far: the standard seam pass (tile CN 0.6) redrew the sea's wrap edge; tile 0 + denoise 0.6 fixes it
    shutil.copy(f'{SRC}/sweep/far{tag}_s{seed}.png', f'{SRC}/far_pass1.png')
    A.seam_pass_free(f'{SRC}/far_pass1.png', PROMPT_FAR, 108, f'{SRC}/far_render.png', denoise=0.6, tile=0.0, loras=lora_set(RENDER['far']['pix']))
    tag, seed = PICK['mid']
    A.finish(SRC, 'mid', seed, PROMPT_MID, RENDER['mid']['pix'], seam_band=96, tag=tag)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=6, grade_kw=dict(black=0, white=255, gamma=1.0, sat=0.9), dk=0.4)
    mid, al, acc_m = A.mid_pipeline_ck(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=0,
                                       grade_kw=dict(black=6, white=420, gamma=0.9, sat=0.9), rim_col=hexc('8a2c0c'),
                                       key_kw=dict(union=0.5, close=True))
    # the crucible's pour (the model greyed it): a 2 px molten stream, opaque in the key
    for x, c in ((249, 'ff9a2e'), (250, 'f26414')):
        ys = np.arange(127, 201); m_ = al[ys, x]; mid[ys[m_], x] = hexc(c)
    far_im, mid_im = to_rgba(far), to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png')
    preview(far_im, mid_im, TINT, f'{SRC}/preview.png')
    st = {'far': stats(far_im), 'mid': stats(mid_im), 'accents_far': ['%02x%02x%02x' % c for c in acc_f], 'accents_mid': ['%02x%02x%02x' % c for c in acc_m]}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase:
        ase_build(f'bg_{B}_far', far_im); ase_build(f'bg_{B}_mid', mid_im)


if __name__ == '__main__':
    a = sys.argv
    if '--guide' in a or '--sweep' in a: paint_guides()
    if '--sweep' in a:
        i = a.index('--sweep'); do_sweep(a[i + 1], [int(s) for s in a[i + 2].split(',')], tag=(a[i + 3] if len(a) > i + 3 and not a[i + 3].startswith('--') else ''))
    elif '--finish' in a: do_finish()
    if '--guide' not in a and '--sweep' not in a: build(ase='--no-ase' not in a)
