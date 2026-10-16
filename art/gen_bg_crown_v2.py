#!/usr/bin/env python3
"""The Pale Crown backdrop v2 (bg rollout agent A, docs/v17/bg_rollout_a.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_crown_v2.py               build bg_crown_{far,mid} from the saved renders in art/bg_src/crown/
  python3 art/gen_bg_crown_v2.py --guide       only (re)paint the layout guides
  python3 art/gen_bg_crown_v2.py --sweep far 1,2,3,4    guides + pass-1 renders for those seeds (ComfyUI on :8188), sheet in sweep/
  python3 art/gen_bg_crown_v2.py --render      guides + render the picked seeds (RENDER) incl. the seam pass, then build
  --no-ase                                      write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/env2_bg.py (rollback: python3 art/gen_env2.py crown).
v1 read as cartoony (cumulus puffs, cotton-ball foliage, flat-block root). v2: a colossal pale world-tree in a sea of mist,
real bark and sharp bare-branch structure, thin high cirrus; the mid layer is an ashen bark bough with sharp-twigged trees.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgroll_a_lib as A

B = 'crown'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#cfd8e6'

# v1 ramps (env2_bg.py S_SKY / S_CLOUD / S_BR / S_GOLD, B_BODY / B_LIT / B_LEAF) plus a darker bark end for structure
SKY = ['56689a', '5e72a4', '687cac', '7388b4', '8094bc', '8ea0c4', '9cacca', 'acb8d0', 'bcc4d6', 'cad0da', 'd8dade', 'e4e2de', 'eee8dc', 'f6eedc', 'fcf4e2', 'fffaec']
CLOUD = ['8c90b8', 'a0a2c4', 'b4b4cc', 'c8c6d4', 'dcd8dc', 'ece6e0', 'f8f2e6']
BR = ['6c6886', '7c7896', '8c90b0', '9a9cba', 'a8a8c2', 'b8b4c8', 'c8c0cc', 'd6ccce', 'e2d6cc', 'eee0cc', 'f8ecd4']
GOLD = ['c8ac86', 'dcc096', 'ead2a6', 'f6e4bc', 'fff4d8']
NEUT = ['767688', '868698', '9696a8', 'a6a6b6', 'b6b4c2', 'c6c2cc']   # neutral ash greys (the trunk in haze)
FAR_PAL = [hexc(c) for c in SKY + CLOUD + BR + GOLD + NEUT]
BODY = ['4a4462', '5a5270', '6c627e', '807490', '96889a', 'ac9ea4', 'c2b2ae', 'd6c6b6']
LIT = ['e8d8bc', 'f6e6c6', 'fff4d8']
LEAF = ['cebeb6', 'e4d6c2', 'f4e8d0']
SAP = ['c08a3a', 'e8b850']
MID_PAL = [hexc(c) for c in BODY + LIT + LEAF + SAP]

PROMPT_FAR = ('pixel art, dark fantasy, a colossal ancient pale world tree rising out of a sea of mist, ashen white bark with deep furrows, '
              'vast bare branches spreading across a pale sky with fine twigs, a faint golden glow of the sun behind the crown, thin high '
              'wispy cirrus clouds, distant giant roots arching out of the mist, mythic and solemn, side-scroller game background, '
              'muted pale ivory, ash grey and cold lavender blue palette, atmospheric perspective, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, a massive gnarled pale tree root bough with deeply furrowed ashen bark, bare dead white trees '
              'growing from it with sharp thin twigs and a few small pale golden leaves, isolated on a flat grey background, '
              'side-scroller game background layer, ash white and lavender grey bark, crisp silhouette, detailed')

SUN = (168, 40)
TREE_X = 206


def bark_fill(G, mask, cx, half, dark, light, k_side=0.45, seed=1, lit_left=True):
    """Fill a vertical trunk mask with bark: vertical furrows that follow the trunk, side shading (lit side toward the sun)."""
    nz = tile_noise(WS, HS, 6, 48, seed, octaves=2)
    side = np.clip(G.wdx(cx) / np.maximum(1, half), -1, 1) * (-1 if lit_left else 1)
    fur = np.sin(G.wdx(cx) * 1.9 + nz * 7.0)
    v = 0.5 + k_side * side + 0.18 * fur
    img = lerp(hexc(dark), hexc(light), np.clip(v, 0, 1)[..., None])
    G.fill_img(mask, img)


def limb(G, segs, dark, light, lit=(-0.55, -0.55)):
    """A branch drawn as a dark body plus a thinner lit stroke shifted toward the light (up-left)."""
    G.fill(G.mask_lines(segs), hexc(dark))
    G.fill(G.mask_lines([(x0 + lit[0] * w * 0.35, y0 + lit[1] * w * 0.35, x1 + lit[0] * w * 0.35, y1 + lit[1] * w * 0.35, w * 0.45)
                         for x0, y0, x1, y1, w in segs if w > 1.4]), hexc(light), 0.85)


def haze(G, k, col):
    """Blend everything painted so far toward a haze colour (atmospheric depth)."""
    G.rgb = lerp(G.rgb, np.asarray(col, float), k)


def guide_far():
    rng = np.random.default_rng(11)
    G = Guide(hexc('8ea0c4'))
    nz = tile_noise(WS, HS, 128, 32, 21); nz2 = tile_noise(WS, HS, 32, 6, 22, octaves=2)
    # sky: cool lavender-blue zenith to an ivory horizon, a soft sun bloom behind the crown
    t = smooth(-20, 165, G.Y) ** 1.1
    d = np.sqrt((G.wdx(SUN[0]) / 150) ** 2 + ((G.Y - SUN[1]) / 95) ** 2)
    t = np.clip(t + 0.45 * np.clip(1 - d, 0, 1) ** 2 + 0.06 * (nz - 0.5), 0, 1)
    G.rgb = lerp(hexc('6c80b0'), hexc('fcf4e2'), t[..., None])
    # cirrus: long thin sheared streaks, high and few
    for (x0, y0, ln, th, k) in ((-30, 22, 190, 2.4, 0.5), (120, 14, 120, 1.6, 0.4), (260, 30, 230, 2.8, 0.55), (300, 52, 120, 1.4, 0.35),
                                (40, 58, 140, 1.8, 0.35), (420, 18, 150, 2.0, 0.45), (180, 72, 90, 1.2, 0.3)):
        segs = []
        for j in range(4):
            yy = y0 + j * th * 0.9 + rng.uniform(-0.6, 0.6); xx = x0 + j * 9 + rng.uniform(-6, 6); ll = ln * rng.uniform(0.55, 1.0)
            segs.append((xx, yy, xx + ll, yy - ll * 0.06, th * rng.uniform(0.5, 1.0)))
        G.add(G.mask_lines(segs, blur=1.2), hexc('2a2620'), k)
    # far ghost trees (deep haze): two smaller world-trees, different heights
    for (tx, top, base_w, k_haze, sd) in ((452, 104, 12, 0.68, 31), (40, 120, 9, 0.75, 32)):
        g2 = Guide(hexc('000000'), alpha=True)
        trunk = g2.mask_poly([(tx - base_w, 170), (tx - base_w * 0.55, top + 20), (tx + base_w * 0.55, top + 20), (tx + base_w, 170)])
        g2.fill(trunk, hexc('a8a8c2'))
        r2 = np.random.default_rng(sd)
        segs = []
        for a in (-2.4, -2.0, -1.6, -1.2, -0.8):
            segs += A.tree_segs(r2, tx + r2.uniform(-2, 2), top + 22, a + r2.normal(0, 0.1), r2.uniform(40, 70), base_w * 0.45, 2,
                                target=a * 0.8 - 0.3, trop=0.02)
        g2.fill(g2.mask_lines(segs), hexc('a8a8c2'))
        G.fill(g2.a, hexc('a8a8c2'), 1 - k_haze)   # deep haze: mostly sky shows through
    # giant roots humping out of the mist (right of the tree): thick tapered bows, half sunk
    for (cx, hw, top, th0, th1) in ((338, 44, 118, 13, 6), (408, 26, 138, 7, 4)):
        a_ = np.linspace(0, math.pi, 40); tk = np.linspace(th1, th0, 40)
        pts_o = [(cx + hw * math.cos(a), 164 - (164 - top) * math.sin(a)) for a in a_]
        pts_i = [(cx + (hw - t) * math.cos(a), 164 - (164 - top - t) * math.sin(a)) for a, t in zip(a_, tk)]
        ring = G.mask_poly(pts_o + list(reversed(pts_i)))
        bark_fill(G, ring, cx, hw, '9a9cba', 'e2d6cc', k_side=0.2, seed=int(cx))
        G.fill(ring, hexc('d8dade'), 0.35)
    # the world tree: a colossal trunk with flared roots, furrowed bark, lit from the upper left (the sun); the crown runs off the top
    cx = TREE_X
    trunk_pts = [(cx - 52, 176), (cx - 34, 150), (cx - 26, 120), (cx - 22, 92), (cx - 24, 70), (cx - 30, 58), (cx + 30, 56), (cx + 25, 70),
                 (cx + 23, 92), (cx + 27, 120), (cx + 34, 150), (cx + 56, 176)]
    tm = G.mask_poly(trunk_pts)
    bark_fill(G, tm, cx, 26, '7c7896', 'e2d6cc', seed=41)
    segs_all = []
    for (a, ln, w) in ((-2.95, 230, 11), (-2.6, 200, 10), (-2.2, 150, 9), (-1.8, 120, 8), (-1.35, 120, 8), (-0.95, 160, 9), (-0.55, 210, 10), (-0.2, 240, 11)):
        x0 = cx + (a + 1.57) * 14; y0 = 66 + abs(a + 1.57) * 5
        tgt = -math.pi / 2 + (a + math.pi / 2) * 1.15
        segs_all += A.tree_segs(rng, x0, y0, a, ln, w, 3, step=2.2, target=tgt, trop=0.015, jitter=0.08, p_branch=0.07, min_w=0.45, taper=0.85)
    limb(G, segs_all, '8c90b0', 'f8ecd4')
    rs = []
    for (a, ln) in ((2.8, 60), (3.0, 90), (0.34, 70), (0.12, 95)):
        rs += A.tree_segs(rng, cx + (-36 if a > 1.5 else 36), 166, a, ln, 9, 1, target=(math.pi if a > 1.5 else 0) * 0.9, trop=0.05, p_branch=0.04)
    limb(G, rs, '8c90b0', 'eee0cc')
    # a faint gold veil in the crown (light caught in the fine twigs), not foliage blobs
    G.glow(cx - 6, 30, 200, 70, hexc('3a2e10'), 0.6, 1.4)
    for _ in range(420):
        s = segs_all[rng.integers(len(segs_all))]
        if s[4] < 1.2 and s[1] < 70:
            G.fill(G.mask_ellipse(s[2] + rng.uniform(-1.5, 1.5), s[3] + rng.uniform(-1, 1), 0.9, 0.7), hexc('f6e4bc'), 0.8)
    # sea of mist: flat stratus layers with soft rolling tops, lighter toward the horizon line
    for (y0, amp, col, k, sd) in ((146, 3.0, 'eee8dc', 0.9, 61), (160, 4.0, 'f6eedc', 0.95, 62), (176, 5.0, 'e4e2de', 1.0, 63), (194, 5.0, 'd8dade', 1.0, 64)):
        top = y0 + amp * (tile_noise(WS, 1, 96, 1, sd, 2)[0] - 0.5) * 2 + 1.5 * np.sin(G.X / 13 + sd)
        m = smooth(top - 2.5, top + 1.5, G.Y)
        shade = lerp(hexc(col), hexc('b4b4cc'), np.clip((G.Y - top) / 40, 0, 1)[..., None] * 0.6)
        G.fill_img(m, shade, k)
        G.add(np.clip(1 - np.abs(G.Y - top - 1) / 1.5, 0, 1), hexc('101010'), 1.0)
    return G


def guide_mid():
    rng = np.random.default_rng(7)
    G = Guide(hexc('808080'), alpha=True)
    nz = tile_noise(WS, HS, 64, 8, 71)
    # the great bough: a gnarled root crossing the whole width, swelling and dipping
    xs = np.linspace(-20, W + 20, 140)
    cy = 170 + 9 * np.sin(xs / W * 2 * math.pi * 2 + 0.6) + 5 * np.sin(xs / W * 2 * math.pi * 3 + 2.1)
    th = 13 + 5 * np.sin(xs / W * 2 * math.pi * 1 + 1.0) + 3 * np.sin(xs / W * 2 * math.pi * 4)
    top = [(x, c - t) for x, c, t in zip(xs, cy, th)]; bot = [(x, c + t * 0.8) for x, c, t in zip(xs, cy, th)]
    bm = G.mask_poly(A.poly_band(top, bot))
    cyi = np.interp(G.X, xs, cy); thi = np.interp(G.X, xs, th)
    u = (G.Y - cyi) / thi                                     # -1 top .. 0.8 bottom
    fur = np.sin(u * 9 + nz * 9 + G.X * 0.08)                 # furrows running along the bough
    v = 0.62 - 0.42 * u + 0.16 * fur
    G.fill_img(bm, lerp(hexc('5a5270'), hexc('e2d6cc'), np.clip(v, 0, 1)[..., None]))
    G.fill(bm * (u < -0.8), hexc('f6e6c6'), 0.8)               # lit crest
    # burls: darker swellings on the bough (shading only, no rings)
    for kx in (60, 150, 300, 445):
        ky = float(np.interp(kx, xs, cy)) - 1
        G.fill(G.mask_ellipse(kx, ky, 7, 4), hexc('807490'), 0.45)
    # buttress roots dropping to the bottom edge (so the bough is not floating)
    drops = []
    for (dx, w) in ((24, 7), (118, 5), (212, 8), (338, 6), (470, 7)):
        y0 = float(np.interp(dx, xs, cy)); drops += A.tree_segs(rng, dx, y0, math.pi / 2 + rng.normal(0, 0.15), 216 - y0 + 10, w, 1,
                                                               target=math.pi / 2, trop=0.06, jitter=0.07, p_branch=0.03, taper=0.3)
    limb(G, drops, '6c627e', 'c2b2ae')
    # hanging rootlets under the bough
    hang = []
    for hx in rng.uniform(0, W, 18):
        y0 = float(np.interp(hx, xs, cy)) + float(np.interp(hx, xs, th)) * 0.6
        hang += A.tree_segs(rng, hx, y0, math.pi / 2, rng.uniform(8, 22), 1.2, 0, target=math.pi / 2, trop=0.1, taper=0.5, min_w=0.5)
    G.fill(G.mask_lines(hang), hexc('807490'))
    # ashen trees growing from the bough: sharp bare twigs, very different sizes
    for (tx, h, w, sd) in ((84, 120, 7.0, 81), (262, 72, 4.5, 82), (402, 132, 8.0, 83), (176, 26, 4.0, 84)):
        r = np.random.default_rng(sd)
        y0 = float(np.interp(tx, xs, cy)) - float(np.interp(tx, xs, th)) * 0.5
        segs = A.tree_segs(r, tx, y0, -math.pi / 2 + r.normal(0, 0.08), h, w, 4 if h > 40 else 1, step=2.0, trop=0.025, jitter=0.11,
                           spread=(0.35, 0.9), p_branch=0.075, min_w=0.45, taper=0.85)
        if h < 30:   # a snapped snag: no twigs, a jagged top
            segs = [s for s in segs if s[4] > 1.6]
        limb(G, segs, '807490', 'eee0cc')
        G.fill(G.mask_poly([(tx - w * 1.4, y0 + 4), (tx - w * 0.5, y0 - 10), (tx + w * 0.5, y0 - 10), (tx + w * 1.4, y0 + 4)]), hexc('96889a'))
        # sparse pale-gold leaf sprays at a few twig tips (thin strokes, not puffs)
        tips = [s for s in segs if s[4] < 0.9]
        for _ in range(min(len(tips), 26)):
            s = tips[r.integers(len(tips))]
            ang = math.atan2(s[3] - s[1], s[2] - s[0]) + r.uniform(-0.6, 0.6)
            G.fill(G.mask_lines([(s[2], s[3], s[2] + math.cos(ang) * 2.6, s[3] + math.sin(ang) * 2.6, 0.9)]), hexc('f4e8d0'))
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image(), lo=10).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=5, denoise=0.78, cn=0.45, cn_end=0.6, pix=0.6, guide_blur=1.3),
    'mid': dict(prompt=PROMPT_MID, seed=5, denoise=0.55, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=1.0, seam_band=96),
}


def do_sweep(layer, seeds, tag=''):
    A.use_prefix(B); kw = dict(RENDER[layer]); kw.pop('seed'); kw.pop('seam_band', None)
    A.sweep(SRC, layer, seeds=seeds, tag=tag, **kw)


def do_finish():
    """Seam pass for the picked sweep renders (RENDER seeds; far from sweep tag 'b')."""
    A.use_prefix(B)
    A.finish(SRC, 'far', RENDER['far']['seed'], PROMPT_FAR, RENDER['far']['pix'], tag='b')
    A.finish(SRC, 'mid', RENDER['mid']['seed'], PROMPT_MID, RENDER['mid']['pix'], seam_band=96, tag='c')


def do_render():
    A.use_prefix(B); times = {}
    for layer, kw in RENDER.items():
        times[layer] = round(render_layer(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


def far_post(a, stage):
    """'hi' (3x): more value range for depth: a cool, slightly deeper zenith behind the pale limbs, and a faint warm gold light
    behind the crown (the sun behind the world tree), so the far layer reads mythic rather than foggy-grey."""
    if stage != 'hi': return a
    h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w] / S
    dx = (xx - TREE_X + W / 2) % W - W / 2
    zen = (1 - smooth(0, 95, yy)) * 0.22
    a = a * (1 - zen[..., None]) + hexc('5e72a4') * zen[..., None]
    g = np.clip(1 - np.sqrt((dx / 170) ** 2 + ((yy - 34) / 80) ** 2), 0, 1) ** 1.6
    a = a + g[..., None] * np.array([34, 24, 2])
    return np.clip(a, 0, 255)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=4, grade_kw=dict(black=0, white=255, gamma=1.0, sat=0.8), post=far_post, dk=0.4)
    mid, al, acc_m = A.mid_pipeline_ck(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=0,
                                  grade_kw=dict(black=0, white=262, gamma=0.92, sat=0.75), rim_col=hexc('f6e6c6'),
                                  key_kw=dict(union=0.5, close=True))
    far_im, mid_im = to_rgba(far), to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png')
    preview(far_im, mid_im, TINT, f'{SRC}/preview.png')
    st = {'far': stats(far_im), 'mid': stats(mid_im), 'accents_far': ['%02x%02x%02x' % c for c in acc_f], 'accents_mid': ['%02x%02x%02x' % c for c in acc_m]}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase:
        ase_build(f'bg_{B}_far', far_im); ase_build(f'bg_{B}_mid', mid_im)


if __name__ == '__main__':
    a = sys.argv
    if '--guide' in a or '--render' in a or '--sweep' in a: paint_guides()
    if '--sweep' in a:
        i = a.index('--sweep'); do_sweep(a[i + 1], [int(s) for s in a[i + 2].split(',')], tag=(a[i + 3] if len(a) > i + 3 and not a[i + 3].startswith('--') else ''))
    elif '--render' in a: do_render()
    elif '--finish' in a: do_finish()
    if '--guide' not in a and '--sweep' not in a: build(ase='--no-ase' not in a)
