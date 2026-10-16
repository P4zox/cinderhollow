#!/usr/bin/env python3
"""Ember's Hollow backdrop v2 (bg rollout C, docs/v17/bg_rollout_c.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_ember_v2.py            build bg_ember_{far,mid} from the saved renders in art/bg_src/ember/
  python3 art/gen_bg_ember_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_ember_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  --no-ase                                   write previews only, leave the assets alone

The hollow beneath the Crown: a vast dark cavern of basalt columns standing in groups at several depths, a distant lake of
embers whose glow lights them from below, and the Pale Root's burning taproots hanging from the vault. v1 was rows of
identical posts with dotted squiggles, and its mid ground band hid the one good thing, the lava horizon; here the horizon
sits higher (y~150-168) and the mid ground is low (y>196). Same asset names, size, tag and frame count as
art/secrets_env.py (kept for rollback).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa

B = 'ember'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#0c0607'

# v1 ramps (secrets_env.py ember_far R / EMB, the ember tileset ST) plus two ash-haze steps
R = ['050304', '0a0506', '100809', '170b0b', '200e0d', '2c120f', '3a1810', '4e1e10', '6a2810', '8e3812']
EMB = ['5a1408', 'a02a0c', 'e0561a', 'ff9a3a', 'ffd88a']
ST = ['181113', '1f1618', '271c1d', '302224', '3a2a2b', '463334', '553d3d', '684a48']
HAZE = ['5e3426', '7a4430']
FAR_PAL = [hexc(c) for c in R + EMB + ST + HAZE]
SIL = ['050304', '080506', '0c0708', '10090a', '150c0c', '1a0f0f', '201212', '2c1612']
MID_PAL = [hexc(c) for c in SIL + ['5a1408', 'a02a0c', 'e0561a']]

PROMPT_FAR = ('pixel art, dark fantasy, a vast dark volcanic cavern, groups of tall hexagonal basalt columns of different heights at '
              'several depths, a distant lake of glowing embers and lava on the cavern floor lighting the columns orange from below, '
              'thick gnarled burning tree roots hanging from the cavern ceiling with glowing ember cracks, smoke and ash haze, '
              'side-scroller game background, very dark red-black and ember orange palette, atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, near silhouettes of tall hexagonal basalt column clusters and broken stumps, charred hanging '
              'roots with faint glowing ember cracks, isolated on a flat pale background, side-scroller game background layer, '
              'near-black volcanic rock with a thin orange rim light from below, detailed')

LAKE = 156    # top of the ember lake (1x)


def columns(G, x, top, w, n, rng, far_k, bottom):
    """A cluster of n hexagonal basalt columns with stepped tops; far_k 0 (near) .. 1 (far, hazed). Faces lit from the lake
    below: a warm rim on the lower half, dark tops."""
    cw = w / n
    for i in range(n):
        cx = x + i * cw + rng.uniform(-0.5, 0.5); t_ = top + rng.uniform(-14, 14) + abs(i - n / 2) * 4
        m = G.mask_poly([(cx, bottom), (cx + cw - 0.6, bottom), (cx + cw - 0.6, t_ + 2), (cx + cw * 0.5, t_ - 1.5), (cx, t_ + 2)])
        base = lerp(hexc('170b0b'), hexc('3a1810'), far_k)
        G.fill(m, base)
        G.fill(m * (G.X > cx + cw * 0.55), lerp(hexc('271c1d'), hexc('4e1e10'), far_k), 0.9)          # second face
        G.fill(G.mask_lines([(cx + cw * 0.55, t_ + 1, cx + cw * 0.55, bottom, 0.5)]), hexc('0a0506'), 0.7)
        glow = smooth(t_ + 10, bottom, G.Y) * m
        G.fill(glow, lerp(hexc('8e3812'), hexc('a02a0c'), far_k), 0.55 * (1 - 0.5 * far_k))             # lake light from below
        for yy in np.arange(t_ + 6, bottom, rng.uniform(9, 16)):                                       # cooling joints
            G.fill(G.mask_lines([(cx, yy, cx + cw - 0.6, yy + rng.uniform(-1, 1), 0.5)]) * m, hexc('0a0506'), 0.6)


def taproot(G, x, length, w, rng, far_k):
    segs = root_segs(rng, x, -2, math.pi / 2 + rng.uniform(-0.25, 0.25), length, w, 2, step=2.0, spread=(0.25, 0.5), droop=0.03)
    G.fill(G.mask_lines([(a, b, c, d, ww + 0.8) for a, b, c, d, ww in segs]), lerp(hexc('0a0506'), hexc('2c120f'), far_k))
    G.fill(G.mask_lines(segs), lerp(hexc('200e0d'), hexc('4e1e10'), far_k))
    cracks = [(a + ww * 0.15, b, c + ww * 0.15, d, max(0.6, ww * 0.22)) for a, b, c, d, ww in segs if ww > 1.6]
    G.fill(G.mask_lines(cracks), hexc('e0561a'), 0.85)
    G.fill(G.mask_lines([(a, b, c, d, max(0.5, ww * 0.1)) for a, b, c, d, ww in cracks]), hexc('ff9a3a'), 0.8)
    tips = [(c, d) for a, b, c, d, ww in segs if ww < 1.0]
    for (tx, ty) in tips[::9]:
        G.glow(tx, ty, 2.5, 2.5, hexc('ff9a3a'), 0.4)


def guide_far():
    rng = np.random.default_rng(51)
    G = Guide(hexc('100809'))
    nz = tile_noise(WS, HS, 96, 32, 5); nz2 = tile_noise(WS, HS, 48, 10, 6, octaves=2)
    # cavern air: black under the vault, warming toward the lake's glow
    v = 0.05 + 0.75 * smooth(40, LAKE, G.Y) ** 1.6 + 0.1 * (nz - 0.5)
    G.rgb = lerp(hexc('0a0506'), hexc('7a4430'), np.clip(v, 0, 1)[..., None])
    # smoke banks drifting at mid height, lit from below
    d = tile_noise(WS, HS, 128 * S, 10 * S, 61, octaves=3)
    m = smooth(0.55, 0.68, d) * smooth(70, 100, G.Y) * (1 - smooth(130, 150, G.Y))
    G.fill(m, hexc('5e3426'), 0.5)
    # the farthest columns, deep in haze
    for (x, w, n, top) in ((20, 34, 4, 96), (150, 26, 3, 108), (250, 40, 5, 90), (370, 30, 4, 104), (470, 24, 3, 100)):
        columns(G, x, top, w, n, rng, 0.9, LAKE + 2)
    # the ember lake: a bright horizon line, crust plates, reflections of the glow
    lake = (G.Y > LAKE).astype(float)
    lv = 1 - smooth(LAKE, LAKE + 22, G.Y) * 0.6 + 0.25 * (nz2 - 0.5)
    G.fill_img(lake, lerp(hexc('a02a0c'), hexc('ff9a3a'), np.clip(lv, 0, 1)[..., None]))
    crust = (tile_noise(WS, HS, 18 * S, 4 * S, 71, octaves=2) > 0.56) * lake * smooth(LAKE + 2, LAKE + 10, G.Y)
    G.fill(crust, hexc('3a1810'), 0.85)
    G.fill(G.mask_lines([(0, LAKE + 0.5, W, LAKE + 0.5, 1.0)]), hexc('ffd88a'), 0.9)
    G.add(np.exp(-((G.Y - LAKE) / 12) ** 2) * (1 - lake), hexc('e0561a'), 0.35)        # glow on the haze above
    # nearer column groups standing out in the lake (reflections below them)
    for (x, w, n, top) in ((60, 30, 4, 64), (196, 22, 3, 80), (300, 36, 5, 52), (430, 28, 4, 72)):
        columns(G, x, top, w, n, rng, 0.45, LAKE + 8)
        refl = G.mask_poly([(x, LAKE + 8), (x + w, LAKE + 8), (x + w, LAKE + 20), (x, LAKE + 20)]) * (np.sin(G.Y * 2.5) > 0)
        G.fill(refl, hexc('2c120f'), 0.6)
    # the floor beyond the lake's near shore
    shore = LAKE + 26 + 4 * tile_noise(WS, 1, 24 * S, 1, 81)[0]
    G.fill((G.Y > shore[None, :]).astype(float), hexc('170b0b'))
    G.fill(((G.Y > shore[None, :]) & (G.Y < shore[None, :] + 1)).astype(float), hexc('8e3812'), 0.8)
    # the vault and the burning taproots of the Pale Root
    roof = 10 + 12 * tile_noise(WS, 1, 96 * S, 1, 91)[0]
    G.fill((G.Y < roof[None, :]).astype(float), hexc('050304'))
    for (x, ln, w) in ((40, 110, 6), (128, 70, 4), (236, 140, 7), (330, 60, 3.5), (408, 120, 5.5), (486, 80, 4)):
        taproot(G, x, ln, w, rng, 0.3)
    return G


def guide_mid():
    rng = np.random.default_rng(53)
    G = Guide(hexc('c0a0a0'), alpha=True)
    top = 198 - 6 * tile_noise(WS, 1, 64 * S, 1, 41)[0] - 3 * tile_noise(WS, 1, 16 * S, 1, 42)[0]
    G.fill((G.Y > top[None, :]).astype(float), hexc('0c0708'))
    G.fill(((G.Y > top[None, :]) & (G.Y < top[None, :] + 1.2)).astype(float), hexc('a02a0c'), 0.9)
    # near column clusters, tall, and a few broken stumps (no identical posts: widths, counts and tops all vary)
    # stepped like a causeway: tallest in the middle of each group, falling away in uneven steps; a few broken stumps
    for (x0, n, cw, tp, step) in ((6, 7, 7, 92, 13), (178, 4, 8, 150, 9), (300, 8, 6.5, 70, 15), (448, 3, 7, 160, 6)):
        c = rng.uniform(0.15, 0.4) * (n - 1)                                     # the tallest column off-centre
        for i in range(n):
            t_ = tp + abs(i - c) ** 1.3 * step * rng.uniform(0.5, 1.4) + rng.uniform(-6, 10)
            if rng.random() < 0.2: t_ += rng.uniform(20, 40)                      # a snapped one
            cx = x0 + i * cw
            m = G.mask_poly([(cx, 216), (cx + cw - 0.7, 216), (cx + cw - 0.7, t_ + 1.5), (cx + cw * 0.5, t_ - 1.5 + rng.uniform(-1, 2)), (cx, t_ + 1.5)])
            G.fill(m, hexc('170b0b'))
            G.fill(m * (G.X > cx + cw * 0.55), hexc('271c1d'))
            G.fill(np.clip(m - np.roll(m, int(2 * S), axis=0), 0, 1), hexc('8e3812'), 0.9)          # top lip catches the glow
            G.fill(m * smooth(t_ + 30, 216, G.Y), hexc('6a2810'), 0.5)
            for yy in np.arange(t_ + 8, 216, rng.uniform(10, 18)):
                G.fill(G.mask_lines([(cx, yy, cx + cw - 0.7, yy + rng.uniform(-1, 1), 0.5)]) * m, hexc('050304'), 0.7)
    # charred roots hanging near, a few ember cracks
    for (x, ln, w) in ((130, 50, 3.5), (400, 64, 4.5)):
        segs = root_segs(rng, x, -2, math.pi / 2 + rng.uniform(-0.2, 0.2), ln, w, 1, step=2.0, spread=(0.25, 0.45), droop=0.03)
        G.fill(G.mask_lines(segs), hexc('100809'))
        G.fill(G.mask_lines([(a + ww * 0.2, b, c + ww * 0.2, d, max(0.5, ww * 0.18)) for a, b, c, d, ww in segs if ww > 2.2]), hexc('a02a0c'), 0.8)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image(), lo=10).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=2, denoise=0.55, cn=0.55, cn_end=0.7, pix=0.45, guide_blur=1.2),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.45, cn=0.6, cn_end=0.8, pix=0.5, guide_blur=0.8, seam_band=96),
}


def do_render(layers=('far', 'mid')):
    for layer in layers:
        print(layer, round(render_layer(SRC, layer, **RENDER[layer]), 1), 's')


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=4, grade_kw=dict(black=0, white=255, gamma=1.0, sat=0.9), dk=0.3)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=2,
                                  grade_kw=dict(black=0, white=380, gamma=0.8, sat=0.8), rim_col=hexc('5a1408'))
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
