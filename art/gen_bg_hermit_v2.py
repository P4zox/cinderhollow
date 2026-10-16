#!/usr/bin/env python3
"""The Hermit's Hollow backdrop v2 (bg rollout C, docs/v17/bg_rollout_c.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_hermit_v2.py            build bg_hermit_{far,mid} from the saved renders in art/bg_src/hermit/
  python3 art/gen_bg_hermit_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_hermit_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  --no-ase                                    write previews only, leave the assets alone

Dusk seen from a mountain cave: a real horizon under a banded dusk sky, the Pale Root breaching the far range as a colossal pale
arching root catching the last light (v1 drew it lying flat as a glowing bar that read as a lens streak), and near pines with
branch structure (v1: stacked triangles). Same asset names, size, tag and frame count as art/secrets_env.py (kept for rollback).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa

B = 'hermit'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#0e0b0c'

# v1 ramps (secrets_env.py DUSK / GOLDR / MTN), plus a pale ivory for the Root's bark and a cold violet haze step
DUSK = ['0c0a17', '120e22', '19122b', '221733', '2c1c3a', '38213f', '462742', '552d44', '663445', '7a3d46', '8e4a47', 'a25a4a',
        'b46c4e', 'c48054', 'd29760', 'deb070', 'e9ca88']
GOLDR = ['3a2616', '6a4630', '8e6038', 'b4843e', 'd4a44a', 'ecc466', 'f8e098', 'fff6d0']
MTN = ['140f1c', '1a1424', '20192c', '281f34', '30263c', '3a2e46', '4a3a52']
IVORY = ['6e6058', '9a8a78', 'c8b89c', 'e8dcc0']
FAR_PAL = [hexc(c) for c in DUSK + GOLDR + MTN + IVORY]
SIL = ['07060a', '0c0a10', '120e18', '181320', '201a2a', '2a2234', '362c40']
MID_PAL = [hexc(c) for c in SIL + ['4a3a52', '663445', '8e4a47', 'b4843e']]

PROMPT_FAR = ('pixel art, dark fantasy, dusk seen from a high mountain cave, layered mountain ranges fading into violet haze, a deep '
              'violet to orange sunset sky with long thin streaks of cloud lit pink and gold from below, a few stars, a colossal pale white '
              'tree root arches up out of the far mountains and plunges back into them, ancient and petrified, rootlets hanging from '
              'it, its bark catching the last golden light, side-scroller game background, muted violet, rose and '
              'gold palette, atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, a near mountain ridge silhouette with wind bent pine trees with drooping layered branches, '
              'jagged rocks, isolated on a flat pale background, side-scroller game background layer, very dark violet silhouette with '
              'a faint warm rim light from the sunset, detailed')

HY = 118    # the horizon the Root lies on


def guide_far():
    rng = np.random.default_rng(31)
    G = Guide(hexc('19122b'))
    nz = tile_noise(WS, HS, 128, 20, 5); nz2 = tile_noise(WS, HS, 32, 6, 6, octaves=2)
    # sky: violet overhead to rose and gold at the horizon
    v = np.clip((G.Y / 130) ** 1.3 + 0.05 * (nz - 0.5), 0, 1)
    ramp_ = [hexc(c) for c in ('120e22', '221733', '38213f', '552d44', '7a3d46', 'a25a4a', 'c48054', 'deb070')]
    f = v * (len(ramp_) - 1); i = np.clip(np.floor(f).astype(int), 0, len(ramp_) - 2); t = (f - i)[..., None]
    G.rgb = np.array(ramp_)[i] * (1 - t) + np.array(ramp_)[i + 1] * t
    # long thin cloud streaks lit from below
    for (y0, y1, seed, k) in ((30, 60, 41, 0.6), (60, 96, 42, 0.8), (88, 110, 43, 0.7)):
        d = tile_noise(WS, HS, 160 * S, 4 * S, seed, octaves=3)
        m = smooth(0.58, 0.66, d) * smooth(y0, y0 + 8, G.Y) * (1 - smooth(y1 - 8, y1, G.Y))
        lit = lerp(hexc('663445'), hexc('d29760'), smooth(30, 110, G.Y)[..., None])
        G.fill_img(m, lit, k)
        G.fill(np.clip(m - np.roll(m, int(-1.5 * S), axis=0), 0, 1), hexc('e9ca88'), 0.5 * k)
    for k in range(60):   # stars
        x, y = rng.uniform(0, W), rng.uniform(2, 60)
        G.fill(G.mask_ellipse(x, y, 0.5, 0.5), hexc('e9ca88') if k % 6 else hexc('fff6d0'), 0.8)
    # the farthest range, hazy rose-violet
    top0 = HY - 4 - 10 * tile_noise(WS, 1, 96 * S, 1, 7)[0] - 4 * tile_noise(WS, 1, 20 * S, 1, 8)[0]
    G.fill((G.Y > top0[None, :]).astype(float), hexc('663445'))
    G.fill(((G.Y > top0[None, :]) & (G.Y < top0[None, :] + 1.5)).astype(float), hexc('a25a4a'))
    # the Pale Root breaching the far range: a colossal pale root arching up out of the mountains and down into them again,
    # a smaller loop beyond, rootlets hanging from its underside (v1 laid it flat, a glowing bar that read as a lens streak)
    def arch_root(xa, xb, hgt, w0, w1, seed):
        r = np.random.default_rng(seed); segs = []; under = []
        n = 70
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            def P(t):   # an uneven, twisting path: steeper rise, a long sag, knots
                return (xa + (xb - xa) * (t + 0.05 * math.sin(t * 9 + seed)),
                        HY + 8 - hgt * math.sin(math.pi * t ** 0.8) ** 0.7 + 5 * math.sin(t * 11 + seed) * math.sin(math.pi * t))
            pa, pb = P(t0), P(t1)
            w = w0 + (w1 - w0) * math.sin(math.pi * t0) ** 0.5 + 2.5 * math.sin(t0 * 31 + seed) ** 3
            segs.append((*pa, *pb, w))
            if 0.12 < t0 < 0.88 and r.random() < 0.35:                          # rootlets hanging from the underside
                under += root_segs(r, pa[0], pa[1] + w * 0.4, math.pi / 2 + r.uniform(-0.3, 0.3), r.uniform(6, 20), r.uniform(0.8, 1.6), 1, step=1.5, spread=(0.3, 0.6))
        # a side root splitting off and diving back into the range
        ts = 0.62; sx_, sy_ = P(ts)
        segs += root_segs(r, sx_, sy_, math.pi * 0.42, hgt * 0.9, w1 * 0.55, 1, step=2.0, spread=(0.2, 0.4), droop=0.02)
        body = G.mask_lines(segs)
        G.fill(G.mask_lines(under), hexc('6e6058'))
        G.fill(body, hexc('9a8a78'))
        G.fill(np.clip(body - np.roll(body, int(3 * S), axis=0), 0, 1), hexc('e8dcc0'), 0.9)      # last light on the top
        G.fill(np.clip(body - np.roll(body, int(-5 * S), axis=0), 0, 1), hexc('4a3a52'), 0.8)     # the underside in shadow
        G.fill((np.sin(G.X * 0.9 - G.Y * 0.6 + nz2 * 7) > 0.8) * body, hexc('6e6058'), 0.45)      # twisted fibres
    arch_root(58, 336, 70, 20, 13, 3)
    arch_root(352, 472, 30, 12, 9, 4)
    # a nearer far range in front of the trunk's lower flank, so it lies ON the mountains, not over them
    topn = HY + 3 - 9 * tile_noise(WS, 1, 70 * S, 1, 17)[0] - 3 * tile_noise(WS, 1, 12 * S, 1, 18)[0]
    mn = (G.Y > topn[None, :]).astype(float)
    G.fill(mn, hexc('462742'))
    G.fill(((G.Y > topn[None, :]) & (G.Y < topn[None, :] + 1.2)).astype(float), hexc('8e4a47'), 0.8)
    # last light pooled behind it
    G.glow(240, HY - 6, 200, 28, hexc('deb070'), 0.25, 1.6)
    # two dark ranges in front, haze between
    for (base, amp, sx, seed, col, rim) in ((142, 26, 110, 11, '30263c', '552d44'), (170, 34, 60, 12, '1a1424', '30263c')):
        top = base - amp * tile_noise(WS, 1, sx * S, 1, seed)[0] - 6 * tile_noise(WS, 1, 14 * S, 1, seed + 5)[0]
        m = (G.Y > top[None, :]).astype(float)
        G.add(np.exp(-((G.Y - top[None, :] + 6) / 7) ** 2) * (1 - m), hexc('462742'), 0.35)   # haze in the valley
        G.fill(m, hexc(col))
        G.fill(((G.Y > top[None, :]) & (G.Y < top[None, :] + 1.2)).astype(float), hexc(rim), 0.9)
        # ridged faces: diagonal light strokes
        G.fill(m * (np.sin((G.X + G.Y * 0.8) * 0.5 + nz2 * 6) > 0.85), hexc(rim), 0.35)
    return G


def guide_mid():
    rng = np.random.default_rng(37)
    G = Guide(hexc('b0a0b0'), alpha=True)
    top = 186 - 14 * tile_noise(WS, 1, 128 * S, 1, 31)[0] - 5 * tile_noise(WS, 1, 32 * S, 1, 32)[0]
    ground = (G.Y > top[None, :]).astype(float)
    G.fill(ground, hexc('181320'))
    G.fill(((G.Y > top[None, :]) & (G.Y < top[None, :] + 1.2)).astype(float), hexc('663445'), 0.9)
    def ground_y(x):
        i = int(x * S) % WS
        return float(186 - 14 * tile_noise(WS, 1, 128 * S, 1, 31)[0][i] - 5 * tile_noise(WS, 1, 32 * S, 1, 32)[0][i])
    def pine(x, h, lean, seed, dead=False):
        """A ragged, wind-bent mountain spruce: a curving trunk, irregular clumps of needles on drooping branches with sky
        between the tiers, the crown bent downwind; or a dead snag."""
        r = np.random.default_rng(seed); base = ground_y(x)
        pts = [(x + lean * h * (j / 10) ** 1.6 + r.uniform(-0.4, 0.4), base + 2 - h * j / 10) for j in range(11)]
        G.fill(G.mask_lines([(a[0], a[1], b_[0], b_[1], 2.2 * (1 - j / 10) + 0.8) for j, (a, b_) in enumerate(zip(pts, pts[1:]))]), hexc('120e18'))
        if dead:
            for k in range(5):
                j = r.integers(3, 10); px, py = pts[j]; s_ = r.choice([-1, 1])
                l_ = r.uniform(4, 10); G.fill(G.mask_lines([(px, py, px + s_ * l_, py - l_ * r.uniform(0.5, 1.1), 0.9)]), hexc('120e18'))
            return
        n = int(h / 4.5)
        for k in range(n):
            t = (k + 0.5) / n; j = t * 10; jj = int(j); f = j - jj
            px = pts[jj][0] * (1 - f) + pts[min(10, jj + 1)][0] * f; py = pts[jj][1] * (1 - f) + pts[min(10, jj + 1)][1] * f
            if t < 0.18: continue                                                # bare lower trunk
            reach = (1 - t) ** 0.9 * h * 0.26 + 2
            for s_ in (-1, 1):
                if r.random() < 0.15: continue                                   # a missing branch
                l2 = reach * (0.6 if s_ < 0 else 1.2) * r.uniform(0.7, 1.15)     # longer downwind
                ex, ey = px + s_ * l2, py + l2 * 0.45                            # drooping
                G.fill(G.mask_poly([(px, py - 1.6), (px + s_ * l2 * 0.5, py + l2 * 0.12), (ex, ey), (px + s_ * l2 * 0.45, py + l2 * 0.3), (px, py + 2.6)]), hexc('181320'))
                for c in range(int(l2 / 2.5)):                                   # needle fringe hanging under the branch
                    u = (c + 0.6) / (int(l2 / 2.5) + 0.5)
                    fx, fy = px + (ex - px) * u, py + (ey - py) * u + 0.6
                    G.fill(G.mask_poly([(fx - 1.0, fy), (fx + 1.0, fy), (fx + s_ * 0.4, fy + r.uniform(1.5, 3.2))]), hexc('181320'))
        # a dense spire for the top quarter (a sparse top with gaps read as a tiny figure where only the tip shows in game)
        tx, ty = pts[-1]; bx_, by_ = pts[7]; cw_ = h * 0.035 + 1.2
        jag = [(tx + 0.6, ty - 3)]
        for j in range(1, 7):
            u = j / 6; yy = ty - 3 + (by_ + 2 - ty + 3) * u; xx = tx + (bx_ - tx) * u
            jag.append((xx + cw_ * u * 1.25 + (0.8 if j % 2 else -0.6), yy + (1.2 if j % 2 else 0)))
        right = jag[:]
        left = [(2 * (tx + (bx_ - tx) * (k / 6 if k else 0)) - x_, y_) for k, (x_, y_) in enumerate(jag)]
        G.fill(G.mask_poly(right + left[::-1]), hexc('181320'))
    # a continuous band of spruce on the near ridge, heights varied, crowns overlapping: isolated trees showed only their tips
    # over the rooms' terrain and read as small standing figures; a tree line reads as forest at any crop
    xs = np.arange(0, W, 7.0); xs = xs + rng.uniform(-2.5, 2.5, len(xs))
    for i, x in enumerate(xs):
        h = 16 + 22 * float(tile_noise(64, 1, 16, 1, 77)[0][int(x / 8) % 64]) + rng.uniform(-4, 8)
        pine(float(x) % W, h, rng.uniform(0.04, 0.12), 100 + i)
    for (x, r) in ((140, 6), (350, 8), (440, 5)):   # rocks
        G.fill(G.mask_poly([(x - r * 1.4, 190), (x - r * 0.6, 190 - r), (x + r * 0.3, 190 - r * 1.2), (x + r * 1.3, 190)]), hexc('201a2a'))
        G.fill(G.mask_lines([(x - r * 0.6, 190 - r, x + r * 0.3, 190 - r * 1.2, 0.8)]), hexc('552d44'), 0.8)
    G.fill(((G.Y > top[None, :] + 4)).astype(float), hexc('181320'))   # under the tree line
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image(), lo=10).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=3, denoise=0.5, cn=0.55, cn_end=0.7, pix=0.45, guide_blur=1.2),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.45, cn=0.6, cn_end=0.8, pix=0.5, guide_blur=0.8, seam_band=96),
}


def do_render(layers=('far', 'mid')):
    for layer in layers:
        print(layer, round(render_layer(SRC, layer, **RENDER[layer]), 1), 's')


def far_post(a, stage):
    """'hi': the Root rendered near-white (frosted); warm it to ivory-gold and pull it down a step so it doesn't outshine the
    sunset or compete with the player."""
    if stage != 'hi': return a
    l = a.mean(2, keepdims=True); sat = (a.max(2, keepdims=True) - a.min(2, keepdims=True)) / np.maximum(1, a.max(2, keepdims=True))
    k = np.clip((l - 120) / 60, 0, 1) * np.clip((0.35 - sat) / 0.2, 0, 1)
    warm = l * np.array([1.0, 0.86, 0.66]) * 0.86
    return np.clip(a * (1 - k) + warm * k, 0, 255)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=4, grade_kw=dict(black=0, white=255, gamma=1.0, sat=0.85), post=far_post, dk=0.3)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=2,
                                  grade_kw=dict(black=0, white=420, gamma=0.8, sat=0.6), rim_col=hexc('552d44'))
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
