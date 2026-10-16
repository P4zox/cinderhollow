#!/usr/bin/env python3
"""Weeping Mire backdrop v2, far layer only (bg rollout, agent B; docs/v17/bg_rollout_b.md, method in docs/v17/bg_pilot.md).

Light rework (audit: "needs variety and one focal point, not a redo"): the three identical islets are gone, a drowned shrine is the
focal point at far x≈215, the banded sky is replaced by soft cloud masses. The mid layer (bg_mire_mid, art/env2_bg.py) is kept.

  python3 art/gen_bg_mire_v2.py            build bg_mire_far from the saved render in art/bg_src/mire/
  python3 art/gen_bg_mire_v2.py --guide    only (re)paint the layout guide
  python3 art/gen_bg_mire_v2.py --render   repaint the guide and re-render with ComfyUI (server on :8188), then build
  python3 art/gen_bg_mire_v2.py --sweep far 1,2,3   pass-1 seed sweep into $BG_SWEEP
  --no-ase                                  write previews only, leave the assets alone

Same asset name, size (512x216), tag (`loop`) and frame count as env2_bg.py (kept for rollback). The moon stays at (338,58);
mire has no GFX_SUN entry.
"""
import json, math, os, random, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgv2b
from env2_bg import dead_tree_px

B = 'mire'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#0b120e'
MOON = (338, 58)
SHRINE = 215

# v1 ramps (env2_bg.py M_SKY / M_WAT / M_WISP), M_SKY extended one step up, plus a little shrine stone
SKY = ['080d0c', '0b1210', '0f1714', '131c18', '17221c', '1c2821', '212f26', '27362b', '2e3d30', '364535', '404d3a', '4b5640',
       '576047', '656a4e', '757656', '88865e', '9c9a70', 'b4b088']
WAT = ['050a0a', '081010', '0b1515', '0f1b1a', '13221f', '182a26', '1e332d', '263d35']
WISP = ['6a2a0c', 'c0561a', 'ff9a3a', 'ffd890']
FAR_PAL = [hexc(c) for c in SKY + WAT + WISP]

PROMPT_FAR = ('pixel art, dark fantasy, a misty swamp at night under a veiled sickly moon, a small drowned stone chapel half sunk in black '
              'water with a broken bell tower and a faint orange glow in its doorway, bare leafless gnarled dead trees with hanging moss on muddy banks, no foliage, '
              'a hazy line of dead trees on the far shore, low fog lying on the water, still water reflecting the trees, thin streaks of misty cloud, '
              'side-scroller game background, muted murky green and olive palette with tiny orange will-o-wisp lights, atmospheric depth, '
              'haze, highly detailed')


def guide_far():
    rnd = random.Random(77); rng = np.random.default_rng(5)
    G = Guide(hexc('0f1714'))
    X, Y = G.X, G.Y
    HZ, WL = 150, 157
    mx, my = MOON
    # sky: smooth vertical ramp plus the moon glow, then soft cloud masses (no horizontal stripes)
    v = 0.10 + 0.55 * smooth(0, 150, Y) ** 1.2
    dm = np.sqrt((G.wdx(mx) / 150) ** 2 + ((Y - my - 20) / 90) ** 2)
    v += 0.28 * np.clip(1 - dm, 0, 1) ** 2
    G.rgb = lerp(hexc('0a100e'), hexc('7a7a58'), np.clip(v, 0, 1)[..., None])
    cl = tile_noise(WS, HS, 128, 12, 21, 4)
    cl2 = tile_noise(WS, HS, 64, 6, 22, 3)
    cm = smooth(0.52, 0.7, cl * 0.75 + cl2 * 0.25) * smooth(10, 40, Y) * (1 - smooth(120, 150, Y))
    lit = np.clip(1 - dm, 0, 1)
    G.fill_img(cm, lerp(hexc('1c2821'), hexc('9c9a70'), np.clip(v + 0.08 + 0.2 * lit, 0, 1)[..., None]), 0.45)
    G.fill(smooth(0.6, 0.75, cl2) * cm, hexc('2e3d30'), 0.3)                       # cloud undersides
    d = np.sqrt(G.wdx(mx) ** 2 + (Y - my) ** 2)
    G.fill((d < 9.2).astype(float), hexc('c4c094'))
    G.fill(((d < 9.2) & (np.abs(Y - my - 1) < 1.6)).astype(float), hexc('656a4e'), 0.8)     # a veil of cloud across the moon
    # far dead-tree lines (two depths, hazy) and the wooded far shore
    for (count, hmin, hmax, wd, col, base) in ((26, 10, 22, 1.8, '4b5640', HZ - 2), (14, 18, 34, 2.6, '364535', HZ + 2)):
        segs = []
        for i in range(count):
            x0 = (i + rnd.random() * 0.8) * W / count
            _, s = dead_tree_px(rnd, x0, base, rnd.uniform(hmin, hmax), wd, 2, rnd.uniform(-8, 8)); segs += s
        G.fill(G.mask_lines(segs), hexc(col))
        top = base - 3 - 3 * bgv2b.profile(16, 50 + count, 2)[None, :]
        G.fill(((Y > top) & (Y < HZ + 8)).astype(float), hexc(col))
    # fog lying on the far shore
    fn = tile_noise(WS, HS, 64, 6, 62, 3)
    G.fill(smooth(HZ - 14, HZ + 2, Y) * (1 - smooth(HZ + 6, HZ + 20, Y)) * smooth(0.35, 0.7, fn), hexc('656a4e'), 0.7)
    # left bank: a long low mud bank with three big moss-hung dead trees of different heights
    def bank(x0, x1, h, col='131c18'):
        cx, hw = (x0 + x1) / 2, (x1 - x0) / 2
        t = np.clip(1 - (G.wdx(cx) / hw) ** 2, 0, 1)
        top = WL + 3 - h * t ** 0.5 - 2 * tile_noise(WS, HS, 8, 4, int(x0) + 70, 2)
        m = ((Y > top) & (Y < WL + 5) & (t > 0)).astype(float); G.fill(m, hexc(col))
        G.fill(m * (Y < top + 1.5), hexc('364535'), 0.8)
    def big_tree(x, h, wd, lean, moss=True):
        _, s = dead_tree_px(rnd, x, WL - 3, h, wd, 3, lean)
        G.fill(G.mask_lines(s), hexc('0f1714'))
        G.fill(G.mask_lines([(a, b, c, d_, w * 0.45) for a, b, c, d_, w in s if c < a]), hexc('2e3d30'), 0.8)   # moonlit (right) sides
        if moss:   # moss strands hanging from the outer limbs
            for (a, b, c, d_, w) in s[::9]:
                if w < 1.6 and b < WL - 20:
                    ln = rng.uniform(5, 14); G.fill(G.mask_lines([(c, d_, c + rng.uniform(-1, 1), d_ + ln, 0.9)]), hexc('27362b'), 0.9)
    bank(-40, 120, 9); bank(392, 470, 6)
    big_tree(10, 54, 3.6, -6); big_tree(58, 40, 3.0, 8); big_tree(96, 30, 2.6, 4)
    big_tree(420, 34, 2.8, -10); big_tree(452, 24, 2.2, 6, moss=False)
    # reeds on the left bank
    for _ in range(70):
        rx = rng.uniform(-30, 125); rh = rng.uniform(4, 11)
        G.fill(G.mask_lines([(rx, WL + 2, rx + rng.uniform(-1.5, 1.5), WL + 2 - rh, 0.6)]), hexc('27362b'))
    # --- focal: the drowned shrine, a ruined gothic chapel half sunk in the water: a steep gable with an empty tracery window,
    # stepped buttresses, the right roof slope fallen in, and a leaning bell tower with an open belfry; a faint candle glow inside
    sx = SHRINE; st, lt, dk = hexc('27362b'), hexc('4b5640'), hexc('131c18')
    def rot(pts, cx, a):
        t = math.radians(a)
        return [(cx + (x - cx) * math.cos(t) - (y - WL) * math.sin(t), WL + (x - cx) * math.sin(t) + (y - WL) * math.cos(t)) for x, y in pts]
    front = rot([(sx - 18, WL + 4), (sx - 18, WL - 30), (sx, WL - 64), (sx + 6, WL - 54), (sx + 9, WL - 50), (sx + 12, WL - 42), (sx + 18, WL - 34), (sx + 18, WL + 4)], sx, -3)
    G.fill(G.mask_poly(front), st)
    G.fill(G.mask_poly(rot([(sx - 18, WL - 30), (sx, WL - 64), (sx, WL - 60), (sx - 15, WL - 30)], sx, -3)), lt, 0.8)          # moonlit coping
    G.fill(G.mask_poly(rot([(sx - 18, WL + 4), (sx - 18, WL - 30), (sx - 15, WL - 30), (sx - 15, WL + 4)], sx, -3)), lt, 0.5)
    for bx, s_ in ((sx - 22, -1), (sx + 22, 1)):                                                                                 # stepped buttresses
        G.fill(G.mask_poly(rot([(bx - 3, WL + 4), (bx - 3, WL - 22), (bx, WL - 26), (bx + 3, WL - 22), (bx + 3 + 2 * s_, WL - 8), (bx + 3 + 3 * s_, WL + 4)], sx, -3)), dk)
    win = rot(arch_pts(sx, 8, WL - 36, WL - 52, WL - 14), sx, -3)
    G.fill(G.mask_poly(win), hexc('404d3a'))                                                                                     # sky/fog seen through it
    for k in (-4, 0, 4):
        G.fill(G.mask_lines([rot([(sx + k, WL - 48 + abs(k)), (sx + k, WL - 14)], sx, -3)[0] + rot([(sx + k, WL - 14)], sx, -3)[0] + (0.9,)]), st)
    G.fill(G.mask_lines([rot([(sx - 8, WL - 30)], sx, -3)[0] + rot([(sx + 8, WL - 30)], sx, -3)[0] + (0.8,)]), st)
    G.glow(sx - 2, WL - 18, 7, 6, hexc('c0561a'), 0.55); G.fill(G.mask_ellipse(sx - 2, WL - 18, 1.0, 1.4), hexc('ff9a3a'), 0.9)  # a candle inside
    for yy in range(WL - 28, WL + 2, 5):
        G.fill(G.mask_lines([rot([(sx - 17, yy)], sx, -3)[0] + rot([(sx + 17, yy)], sx, -3)[0] + (0.5,)]), dk, 0.5)
    # the leaning bell tower (separate, left), its spire and open belfry
    tx = sx - 38
    tower = rot([(tx - 6, WL + 4), (tx - 6, WL - 54), (tx - 7, WL - 56), (tx, WL - 84), (tx + 7, WL - 56), (tx + 6, WL - 54), (tx + 6, WL + 4)], tx, -7)
    G.fill(G.mask_poly(tower), st)
    G.fill(G.mask_poly(rot([(tx - 6, WL + 4), (tx - 6, WL - 54), (tx - 3, WL - 54), (tx - 3, WL + 4)], tx, -7)), lt, 0.6)
    G.fill(G.mask_poly(rot(arch_pts(tx, 3, WL - 44, WL - 51, WL - 36), tx, -7)), hexc('404d3a'))
    bx_, by_ = rot([(tx, WL - 41)], tx, -7)[0]; G.fill(G.mask_ellipse(bx_, by_, 2.0, 2.4), hexc('131c18'))
    for yy in range(WL - 50, WL + 2, 6):
        G.fill(G.mask_lines([rot([(tx - 6, yy)], tx, -7)[0] + rot([(tx + 6, yy)], tx, -7)[0] + (0.5,)]), dk, 0.5)
    # a leaning cross and two grave posts sticking out of the water beside it
    G.fill(G.mask_lines([(sx + 34, WL + 3, sx + 37, WL - 14, 1.4), (sx + 31, WL - 9, sx + 41, WL - 10, 1.2)]), hexc('1c2821'))
    G.fill(G.mask_lines([(sx + 52, WL + 3, sx + 53, WL - 4, 1.4)]), hexc('1c2821'))
    # water: dark, with a mirrored reflection of everything above the line, rippled, plus the doorway glow
    above = G.rgb.copy()
    hh = HS; wl = WL * S
    nz = tile_noise(WS, HS, 48, 6, 77, 2)
    for y in range(wl, hh):
        dd = y - wl; sy = int(np.clip(wl - 1 - dd * 1.15, 0, hh - 1))
        xs = (np.arange(WS) + (2 + dd * 0.05) * np.sin(y * 0.6 + nz[y] * 8)).astype(int) % WS
        row = above[sy, xs] * (0.42 - 0.2 * dd / (hh - wl)) * np.array([0.8, 0.95, 0.95]) + np.array([3, 6, 6])
        G.rgb[y] = row
    G.fill(G.mask_lines([(0, WL, W, WL, 0.7)]), hexc('576047'), 0.8)
    # will-o'-wisps and their reflections
    for (x, y) in ((40, 140), (150, 146), (262, 132), (360, 143), (470, 138), (232, 122)):
        G.fill(G.mask_ellipse(x, y, 1.4, 1.4), hexc('ff9a3a')); G.glow(x, y, 6, 6, hexc('6a2a0c'), 0.6)
        if 2 * WL - y < H: G.fill(G.mask_ellipse(x, 2 * WL - y, 1.0, 0.6), hexc('c0561a'), 0.7)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image()).save(f'{SRC}/edge_far.png')
    far1 = box_down(f.image()); Image.fromarray(far1.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {'far': dict(prompt=PROMPT_FAR, seed=2, denoise=0.48, cn=0.7, cn_end=0.65, pix=0.5, guide_blur=1.2)}


def do_render():
    bgv2b.set_prefix(B); times = {}
    for layer, kw in RENDER.items():
        times[layer] = round(render_layer(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=5, grade_kw=dict(black=10, white=225, gamma=1.12, sat=0.9), dk=0.4)
    far_im = to_rgba(far); far_im.save(f'{SRC}/out_far.png')
    mid_im = Image.open(os.path.join(ROOT, 'assets', 'bg_mire_mid.png')).convert('RGBA')
    preview(far_im, mid_im, TINT, f'{SRC}/preview.png')
    st = {'far': stats(far_im), 'mid_v1': stats(mid_im), 'accents_far': ['%02x%02x%02x' % c for c in acc_f]}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase: ase_build(f'bg_{B}_far', far_im)


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
