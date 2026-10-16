#!/usr/bin/env python3
"""The Ashen Archives backdrop v2 (bg rollout agent A, docs/v17/bg_rollout_a.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_archives_v2.py               build bg_archives_{far,mid} from the saved renders in art/bg_src/archives/
  python3 art/gen_bg_archives_v2.py --guide       only (re)paint the layout guides
  python3 art/gen_bg_archives_v2.py --sweep far 1,2,3,4 [tag]   guides + pass-1 renders for those seeds (ComfyUI on :8188)
  python3 art/gen_bg_archives_v2.py --finish      seam pass for the picked sweep renders (RENDER), then build
  --no-ase                                        write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/archives_bg.py (rollback: python3 art/gen_archives_env.py
or restore art/bg_src/archives/v1/). The v1 composition was good (the curved tower wall of shelf galleries, the central spiral
book-tower, the bell in the light) but violet-on-violet, 63 % near-black, shelves as bare lines. v2 keeps that composition: the
guide is the v1 layer itself, lifted 2-3 value steps, with coloured book spines in every shelf row, stronger light shafts from
the bell chamber and warm candle glows on the gallery rails.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgroll_a_lib as A
import archives_bg as AB

B = 'archives'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#0c0a12'

# v1 ramps (archives_bg.py FAR, archives_tiles GOLD / PARCH / VIO) extended upward; muted leather book hues
FARR = ['07060c', '0d0b15', '151121', '1a1528', '201a30', '261f38', '2d2541', '352c4b', '3f3456', '4a3e62', '574970', '66577e', '7a6b90', '9486a8', 'b4a8c4', 'd2c8dc']
GOLD = ['5a3c14', '8a6224', 'c09440', 'ecc870', 'fff0b8']
PARCH = ['3e3428', '6a5c44', '9a8a68', 'c4b48c']
BOOK = ['4a2430', '2c3e3a', '2e3456', '5a4428']
FAR_PAL = [hexc(c) for c in FARR + GOLD]
MDR = ['08070d', '0c0a12', '110e18', '16121f', '1c1727', '231d30', '2c2540', '3a3052', '4a3e66']
MID_PAL = [hexc(c) for c in MDR + ['3c3058', '54447a'] + GOLD[:3] + ['3a1a22', '1c3030', '20284a', '3e2e1a', '6a5c44']]

PROMPT_FAR = ('pixel art, dark fantasy, interior of a colossal cylindrical library tower, curved walls lined with tier upon tier of '
              'bookshelf galleries packed with old leather-bound books, a central spiral tower of bookshelves wound by a helical walkway, '
              'pale shafts of light falling from a bell chamber high above, a great bell hanging in the light, rows of small lit candles '
              'along the gallery rails, drifting dust, side-scroller game background, muted dusty violet palette with warm candle gold, '
              'atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, tall gothic bookcases with pointed carved crowns packed with leather-bound books, rolling library '
              'ladders, an iron bridge, hanging iron cages full of books on chains, a giant tome bound in chains, piles of fallen books, '
              'isolated on a flat grey background, side-scroller game background layer, dark violet wood with gold trim, detailed')

BOOK_HUES = [hexc(c) for c in ('7a3a48', '3e6a5a', '46508a', '8a6a3a', '6a4a86', 'a08a60', '5a2a34')]


def h01(*a):
    return AB.h01(*a)


def books_1x():
    """Per-pixel book-spine colour (or None) for the v1 far wall, using archives_bg's own ring geometry."""
    out = np.zeros((H, W, 3)); m = np.zeros((H, W))
    for y in range(H):
        for x in range(W):
            r = AB.ring_r(x, y); t = (r - 6) % 24; tier = int((r - 6) // 24); xx = x % 64
            if xx < 5 or not (6 <= t < 19): continue
            s = (t - 6) % 6.5
            if s < 1: continue
            col = (x + tier * 7) // 2; top = 1 + AB.h01(col, tier, 3) * 3.4
            if s < top: continue
            out[y, x] = BOOK_HUES[int(AB.h01(col, tier * 3 + int(t // 6.5), 7) * len(BOOK_HUES)) % len(BOOK_HUES)]
            m[y, x] = 1
    # keep the spiral column and the bell area clear (their own forms)
    yy, xx_ = np.mgrid[0:H, 0:W]
    dx = (xx_ - AB.CX + W / 2) % W - W / 2
    colw = 22 + 18 * np.clip((yy - 50) / 166, 0, 1)
    m *= ~((np.abs(dx) < colw + 14) & (yy > 32))
    return out, m


def beams_1x():
    return np.array([[AB.beam(x, y) for x in range(W)] for y in range(H)])


def up3(a, smooth_=True):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.resize((WS, HS), Image.BICUBIC if smooth_ else Image.NEAREST), float)


def guide_far():
    v1 = np.asarray(Image.open(f'{SRC}/v1/bg_archives_far.png').convert('RGB'), float)
    lum = (v1 * [0.299, 0.587, 0.114]).sum(-1, keepdims=True)
    lift = 255 * (np.clip(v1 / 190, 0, 1)) ** 0.62                  # +2-3 value steps, darks opened up
    g = lift
    bk, bm = books_1x()
    g = np.where(bm[..., None] > 0, bk * (0.45 + 1.6 * lum / 60) * 0.85, g)
    # candle glows: every gold pixel of v1 becomes a small warm halo
    gold = ((v1[..., 0] > 90) & (v1[..., 0] > v1[..., 2] * 1.4)).astype(float)
    halo = np.asarray(Image.fromarray((gold * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), float) / 255
    g = g + np.clip(halo * 5, 0, 1)[..., None] * np.array([120, 80, 30])
    g = np.where(gold[..., None] > 0, hexc('ffe8a0'), g)
    # stronger light shafts from the bell chamber
    bt_ = beams_1x()
    g = g + bt_[..., None] * np.array([150, 140, 170])
    G = up3(g)
    return Image.fromarray(np.clip(G, 0, 255).astype(np.uint8))


def guide_far2():
    """Contre-jour version: the back-wall veil and the indoor ambient flatten mid-on-mid values, so the focal must be a bold
    dark shape on light: the spiral book-tower as a silhouette against the column of light falling from the bell chamber,
    its helical gallery picked out by lit treads and warm windows; the wall tiers darker and quieter around it."""
    v1 = np.asarray(Image.open(f'{SRC}/v1/bg_archives_far.png').convert('RGB'), float)
    g = 255 * (np.clip(v1 / 190, 0, 1)) ** 0.7 * 0.85
    bk, bm = books_1x()
    lum = (v1 * [0.299, 0.587, 0.114]).sum(-1, keepdims=True)
    g = np.where(bm[..., None] > 0, bk * (0.35 + 1.2 * lum / 60) * 0.6 + g * 0.3, g)
    G = up3(g)
    yy, xx = np.mgrid[0:HS, 0:WS] / S
    cx = AB.CX; dx = (xx - cx + W / 2) % W - W / 2
    # the column of light from the oculus: bright at the top, falling to the floor, slightly wider at the bottom
    col = np.exp(-(dx / (46 + 0.25 * yy)) ** 2) * (1.0 - 0.45 * smooth(0, 216, yy))
    G = G * (1 - 0.65 * col[..., None]) + hexc('b8acd0') * 0.65 * col[..., None]
    for (bx, bw, sl, amp) in AB.BEAMS:   # the slanted shafts, stronger than v1
        e = np.exp(-(((xx - bx - sl * yy + W / 2) % W - W / 2) / bw) ** 2) * amp * 2.2 * (1 - 0.6 * smooth(0, 216, yy))
        G = G + e[..., None] * np.array([120, 110, 150])
    # tower silhouette: cone roof, body, base widening (v1 geometry)
    CT = 52
    rad = np.where(yy >= CT, 22 + 18 * smooth(CT, 216, yy), np.clip((yy - (CT - 22)) / 22, 0, 1) * 22)
    body = (np.abs(dx) < rad).astype(float)
    nx = np.clip(dx / np.maximum(rad, 1), -1, 1)
    shade = 0.5 + 0.5 * (-0.5 * nx)                          # faint turning: a little lighter on the left
    tcol = lerp(hexc('1a1528'), hexc('3a3052'), shade[..., None])
    # book rows on the body (dark, low contrast) between the gallery turns
    rows = ((yy - CT) % 9 < 6) & (yy > CT)
    noise = tile_noise(WS, HS, 6, 3, 91, 1)
    tcol = np.where((rows & (noise > 0.45))[..., None], tcol * 1.25 + np.array([10, 4, 0]), tcol)
    G = G * (1 - body[..., None]) + tcol * body[..., None]
    # the helical gallery: front half lit treads and balusters, back half hidden
    P = 46.0; th = np.linspace(0, 40, 9000)
    ycs = 236 - P * th / (2 * np.pi); keep = ycs > CT + 2; th, ycs = th[keep], ycs[keep]
    rh = 22 + 18 * smooth(CT, 216, ycs) + 12
    xs = cx + rh * np.sin(th); front = np.cos(th) >= 0
    tread = np.zeros((HS, WS)); under = np.zeros((HS, WS))
    for x_, y_, f_ in zip(xs, ycs, front):
        if not f_: continue
        X = int(round(x_ * S)) % WS; Y = int(round(y_ * S))
        if 0 <= Y < HS - 9:
            tread[max(0, Y - 2):Y + 1, X] = 1; under[Y + 1:Y + 8, X] = 1
    G = np.where(under[..., None] > 0, hexc('241d34'), G)
    G = np.where(tread[..., None] > 0, hexc('cfc2e0'), G)
    # warm windows / candles along the gallery
    rng = np.random.default_rng(4)
    for x_, y_, f_ in zip(xs[::160], ycs[::160], front[::160]):
        if f_ and rng.random() < 0.7:
            X, Y = int(x_ * S) % WS, int((y_ - 4) * S)
            G[max(0, Y - 3):Y + 3, max(0, X - 2):X + 2] = hexc('ffd890')
    # the bell hanging in the light above the cone
    bell = (np.abs(dx) < (3 + 7 * np.clip((yy - 8) / 20, 0, 1) ** 1.8)) & (yy > 8) & (yy < 29)
    G = np.where(bell[..., None], hexc('2a2236'), G)
    G = np.where(((np.abs(dx) < 0.6) & (yy < 8))[..., None], hexc('2a2236'), G)
    return Image.fromarray(np.clip(G, 0, 255).astype(np.uint8))


def guide_mid():
    v1 = Image.open(f'{SRC}/v1/bg_archives_mid.png').convert('RGBA'); a = np.asarray(v1, float)
    al = a[..., 3] > 0
    rgb = a[..., :3]
    lum = (rgb * [0.299, 0.587, 0.114]).sum(-1, keepdims=True)
    # the books are dark leather (BOOKM): saturate and lift them so the model reads spines; the wood gets a violet mid value
    chroma = rgb - lum
    g = np.clip(255 * (np.clip(rgb / 70, 0, 1)) ** 0.55 + chroma * 3.0, 0, 255)
    g = np.where(al[..., None], g, 128)
    G = up3(g, smooth_=False)
    A3 = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((WS, HS), Image.NEAREST), float)
    G = np.where(A3[..., None] > 127, G, 128)
    return Image.fromarray(G.astype(np.uint8)), Image.fromarray(A3.astype(np.uint8))


def paint_guides():
    f = guide_far2(); f.save(f'{SRC}/guide_far.png'); edges_of(f, lo=12).save(f'{SRC}/edge_far.png')
    m, ma = guide_mid(); m.save(f'{SRC}/guide_mid.png'); ma.save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m, lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f); mid1 = box_down(m); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=1, denoise=0.72, cn=0.5, cn_end=0.65, pix=0.6, guide_blur=1.2),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.55, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=0.8, seam_band=96),
}
PICK = {'far': ('cj', 5), 'mid': ('', 2)}   # (sweep tag, seed) picked by eye


def do_sweep(layer, seeds, tag=''):
    A.use_prefix(B); kw = dict(RENDER[layer]); kw.pop('seed'); kw.pop('seam_band', None)
    A.sweep(SRC, layer, seeds=seeds, tag=tag, **kw)


def do_finish():
    A.use_prefix(B)
    for layer in ('far', 'mid'):
        tag, seed = PICK[layer]
        A.finish(SRC, layer, seed, RENDER[layer]['prompt'], RENDER[layer]['pix'], seam_band=RENDER[layer].get('seam_band', 128), tag=tag)


TOWER_X = 256   # the spiral book-tower (guide_far2, v1 CX)


def far_post(a, stage):
    """'hi' (3x): the far wall sits behind back-wall tiles that are themselves bookshelves, so its own shelves must not add
    texture there: soften the wall away from the spiral tower (haze, the wall is far away) and pool the value toward the light,
    keeping the tower, the shafts and the candle points crisp."""
    if stage != 'hi': return a
    h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w] / S
    dx = (xx - TOWER_X + W / 2) % W - W / 2
    tower = np.clip(1 - (np.abs(dx) - 34) / 14, 0, 1) * smooth(-10, 20, yy)
    lum = (a * [0.299, 0.587, 0.114]).sum(-1)[..., None]
    hot = smooth(150, 220, lum[..., 0])                         # candle points and lit glints keep their colour
    k = (0.3 * (1 - tower) * (1 - hot))[..., None]
    a = a * (1 - k) + (lum * 0.9 + np.array([4, 0, 10])) * k     # far wall: books desaturated toward the violet air
    pool = 0.9 + 0.2 * np.exp(-(dx / 150) ** 2)
    return np.clip(a * pool[..., None], 0, 255)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=10, grade_kw=dict(black=4, white=245, gamma=0.95, sat=0.8), post=far_post, dk=0.3)
    mid, al, acc_m = A.mid_pipeline_ck(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=4,
                                       grade_kw=dict(black=10, white=640, gamma=0.95, sat=1.0), rim_col=hexc('3c3058'),
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
    if '--guide' in a or '--sweep' in a: paint_guides()
    if '--sweep' in a:
        i = a.index('--sweep'); do_sweep(a[i + 1], [int(s) for s in a[i + 2].split(',')], tag=(a[i + 3] if len(a) > i + 3 and not a[i + 3].startswith('--') else ''))
    elif '--finish' in a: do_finish()
    if '--guide' not in a and '--sweep' not in a: build(ase='--no-ase' not in a)
