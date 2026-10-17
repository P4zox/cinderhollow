#!/usr/bin/env python3
"""H3 The Hermit's Garden: the vista (docs/v17/vista_v3.md). Seen through the long window of Oswin's garden wall.

The hour after sunset, very still. The sun has just gone behind the far range; its last gold pools in the notch between
two peaks and spills across a mountain lake that mirrors it. Mist lies in layers between the ranges. (The Pale
Root arching over the range like a bridge of bone, ivory against the afterglow, it was tried, but every render turned it into a rainbow, so this view leaves it to the region's own dusk.
Dark spruce on the near slopes frame it, the first stars come out. (The region's own dusk is wide and
banded; this is one framed, deep view, warm in the middle and cool at the edges.)

  python3 art/gen_vista_h3.py [--guide | --sweep <far|mid> 1,2,3 [tag] | --pick <name> <seed> [tag] | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from vista_v3lib import *  # noqa
import vista_v3lib as L

ROOM = 'H3'; SRC = src_dir(ROOM)
LW, LH = 512, 240
TINT = '#140e18'
SUN = (226, 132)        # where the sun went down (the notch)
LAKE_Y = 150


def sky(C):
    nz = C.noise(80, 20, 3)
    C.rgb = C.vgrad([(0, '141430'), (40, '2a2448'), (80, '5a3a5a'), (110, 'a05a5a'), (126, 'e09060'), (136, 'f0c080'), (150, 'c08060'), (240, '3a2838')])
    C.add(np.exp(-((C.X - SUN[0]) / 120) ** 2) * np.exp(-((C.Y - SUN[1]) / 34) ** 2), hexc('ffd890'), 0.5)
    C.add(np.exp(-((C.X - SUN[0]) / 40) ** 2) * np.exp(-((C.Y - SUN[1]) / 14) ** 2), hexc('fff0c0'), 0.45)
    # long lit cloud streaks: rose undersides near the sun, violet away from it
    dxs = (C.X - SUN[0]) / 170
    for (y0, y1, cx, cy, sd, lo, hi, k) in ((30, 60, 160, 5, 31, '3a2a50', '8a5a78', 0.7), (62, 96, 130, 4, 32, '5a3a5a', 'e0907a', 0.8),
                                          (92, 116, 100, 3, 33, '7a4a5a', 'f8c090', 0.75)):
        d = C.noise(cx, cy, sd, 3); band = smooth(y0, y0 + 6, C.Y) * (1 - smooth(y1 - 6, y1, C.Y))
        m = smooth(0.5, 0.62, d) * band; lit = np.clip(np.exp(-dxs ** 2) * 1.1, 0, 1)
        C.fill_img(m, lerp(hexc(lo), hexc(hi), lit[..., None]), k)
        C.fill(np.clip(m - np.roll(m, int(-1.5 * S), axis=0), 0, 1) * lit, hexc('ffd8a0'), 0.55 * k)
    return C


def ranges(C):
    """Far ranges + the Root + the lake (cover = far)."""
    cov = np.zeros_like(C.X)
    x = np.arange(C.WS) / S
    # the farthest range: two peaks with the notch where the sun went down
    p1 = C.profile(128, (5, 3, 1.2), 11, (90, 24, 7)) - 20 * np.exp(-((x - 172) / 30) ** 2) - 24 * np.exp(-((x - 284) / 36) ** 2) + 5 * np.exp(-((x - SUN[0]) / 16) ** 2)
    m1 = C.mask_below(p1)
    C.fill_img(m1, lerp(hexc('8a5a6a'), hexc('6a4a62'), smooth(100, 150, C.Y)[..., None])); cov = np.maximum(cov, m1)
    C.fill(np.clip(m1 - np.roll(m1, int(1.5 * S), axis=0), 0, 1) * np.exp(-((C.X - SUN[0]) / 80) ** 2), hexc('f8c890'), 0.7)
    # the Pale Root arching over the far range, ivory on the afterglow
    segs = []; n = 70
    for i in range(n + 1):
        t = i / n; ax = 104 + t * 250; ay = 134 - 46 * math.sin(math.pi * t) ** 0.8 + 3 * math.sin(t * 11) + 5 * t
        if i: segs.append((px, py, ax, ay, 9 - 4.5 * math.sin(math.pi * t) ** 0.6 + 1.2 * math.sin(t * 23)))
        px, py = ax, ay
    rm = C.mask_lines(segs) * 0          # (the arch rendered as a rainbow every time: dropped, see the docstring)
    rshade = lerp(hexc('c8b4a0'), hexc('8a7072'), smooth(100, 60, C.Y)[..., None])
    C.fill_img(rm, rshade); C.fill(rm * (C.Y > np.roll(C.Y, 0)) * 0, (0, 0, 0)); cov = np.maximum(cov, rm)
    C.fill(np.clip(rm - np.roll(rm, int(-2 * S), axis=0), 0, 1), hexc('f8e0b8'), 0.6)            # its lit underside edge
    # the second range: darker, cooler, mist at its foot
    p2 = C.profile(138, (5, 3, 1), 21, (70, 20, 6)) - 18 * np.exp(-((x - 80) / 50) ** 2) - 14 * np.exp(-((x - 400) / 60) ** 2) + 6 * np.exp(-((x - SUN[0]) / 50) ** 2)
    m2 = C.mask_below(p2)
    C.fill_img(m2, lerp(hexc('4a3450'), hexc('3a2a44'), smooth(120, 160, C.Y)[..., None])); cov = np.maximum(cov, m2)
    C.add(cov * np.exp(-((C.Y - 146) / 6) ** 2), hexc('c08a8a'), 0.35)                              # mist on the water line
    # the lake: the afterglow mirrored, darker toward us, a gold path under the notch
    lake = C.mask_poly([(-5, LAKE_Y), (LW + 5, LAKE_Y), (LW + 5, LH + 2), (-5, LH + 2)])
    lc = lerp(hexc('a0706a'), hexc('2a2034'), smooth(LAKE_Y, LAKE_Y + 60, C.Y)[..., None])
    C.fill_img(lake, lc); cov = np.maximum(cov, lake)
    path = np.exp(-((C.X - SUN[0]) / (10 + 0.5 * (C.Y - LAKE_Y))) ** 2) * (C.Y > LAKE_Y) * (0.6 + 0.5 * C.noise(14, 2, 12, 2))
    C.add(lake * path * (1 - smooth(LAKE_Y, LAKE_Y + 70, C.Y)), hexc('ffd890'), 0.7)
    for y in range(LAKE_Y + 3, LH, 5):
        C.add(lake * C.mask_lines([(0, y, LW, y, 0.5)]) * (0.4 + 0.6 * C.noise(30, 2, y, 1)), hexc('d8a080'), 0.12)
    return cov


def spruce(C, x, base, h, w):
    pts = [(x, base - h)]
    for k in range(1, 9):
        t = k / 8; pts.append((x + w * t * (1 if k % 2 else 0.7) * 0.5 + 0.5, base - h + h * t))
    pts.append((x, base))
    for k in range(8, 0, -1):
        t = k / 8; pts.append((x - w * t * (1 if k % 2 else 0.7) * 0.5 - 0.5, base - h + h * t))
    return C.mask_poly(pts)


def near(C):
    """Near slopes with spruce framing the view, left and right (cover = mid)."""
    cov = np.zeros_like(C.X)
    x = np.arange(C.WS) / S
    pl = 150 + 0.004 * (x - 0) ** 2 * 0 + 50 * smooth(130, 40, x) * 0
    slope = 168 + 34 * np.exp(-((x - 0) / 90) ** 2) * -1 + 60 * smooth(150, 0, x) * 0
    prof = 176 - 40 * np.exp(-((x - 10) / 80) ** 2) - 34 * np.exp(-((x - 500) / 70) ** 2) + 30 * np.exp(-((x - 230) / 120) ** 2)
    ms = C.mask_below(prof)
    C.fill(ms, hexc('1a1220')); cov = np.maximum(cov, ms)
    rng = np.random.default_rng(3)
    for (x0, x1, n, hl, hh) in ((-8, 110, 9, 30, 64), (380, 520, 10, 30, 70), (140, 330, 5, 10, 18)):
        for i in range(n):
            tx = rng.uniform(x0, x1); b = float(np.interp(tx, x, prof)) + 6; h = rng.uniform(hl, hh)
            m = spruce(C, tx, b, h, h * rng.uniform(0.32, 0.42))
            C.fill(m, lerp(hexc('1e1626'), hexc('2a1e30'), rng.random())); cov = np.maximum(cov, m)
            C.fill(m * (C.X > tx) * np.exp(-((C.X - SUN[0]) / 200) ** 2) * (C.X < SUN[0]), hexc('6a4048'), 0.4)
            C.fill(m * (C.X < tx) * (C.X > SUN[0]), hexc('6a4048'), 0.4)
    return cov


def guides():
    gf = sky(Canvas(LW, LH)); cf = ranges(gf); gf.save(f'{SRC}/guide_far.png'); Image.fromarray((np.clip(cf, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_far.png')
    edges(gf.image()).save(f'{SRC}/edge_far.png')
    gm = sky(Canvas(LW, LH)); ranges(gm); cm = near(gm); gm.save(f'{SRC}/guide_mid.png'); Image.fromarray((np.clip(cm, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_mid.png')
    edges(gm.image()).save(f'{SRC}/edge_mid.png')
    gm.image().save(f'{SRC}/guide_preview.png')


PROMPT = ('pixel art, serene mountain valley at dusk just after sunset, golden afterglow in a notch between two mountain peaks, '
          'a still mountain lake mirroring the glow, layers of soft mist between the ranges, a colossal ancient pale ivory root '
          'arching over the far mountains like a stone bridge, dark spruce forest on the near slopes, rose and violet clouds, '
          'first stars, peaceful, melancholy, painterly, highly detailed, dark fantasy')
RENDER = {
    'far': (PROMPT, dict(denoise=0.55, pix=0.45, edge=True, cn=0.45, cn_end=0.65)),
    'mid': (PROMPT, dict(denoise=0.52, pix=0.5, edge=True, cn=0.5, cn_end=0.7)),
}
PAL = ['141430', '1a1220', '1e1626', '241a2e', '2a1e30', '2a2034', '2a2448', '3a2838', '3a2a44', '4a3450', '5a3a5a', '6a4a62',
       '7a4a5a', '8a5a6a', '8a7072', 'a05a5a', 'a0706a', 'b87a6a', 'c08060', 'c8b4a0', 'd8a080', 'e09060', 'f0c080', 'f8d8a8',
       'fff0c8', '3a3a60', '5a5a80']


def build(ase=True):
    rng = np.random.default_rng(3)
    a = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    a = knee(grade(a, black=2, white=252, gamma=1.0, sat=1.05), 190, 0.5, 'f8c890', 0.5)
    s = down(a, LW, LH); cov = cover_alpha(f'{SRC}/cover_far.png', LW, LH, 0.02)
    sk = fill_under(s, np.asarray(Image.fromarray((cov * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), float) > 0)
    q, _ = pixelize(sk, PAL, n_acc=4, dk=0.3)
    yy = np.arange(LH)[:, None] * np.ones((1, LW))
    stars(q, rng, 70, cols=('8a8aa8', 'c8c8e0'), weight=np.clip(1 - yy / 60, 0, 1) ** 2 + 1e-6)
    stars(q, rng, 0, big=3, big_cols=('fff0c8',), weight=np.clip(1 - yy / 50, 0, 1) ** 2 + 1e-6)
    sky_im = to_rgba(q)
    al = cover_alpha(f'{SRC}/cover_far.png', LW, LH)
    q, _ = pixelize(s, PAL, n_acc=4, dk=0.25, mask=al); far_im = to_rgba(np.where(al[..., None], q, 0), al)
    a = np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float)
    s = down(knee(grade(a, black=6, white=255, gamma=0.9), 190, 0.5), LW, LH); al = cover_alpha(f'{SRC}/cover_mid.png', LW, LH)
    q, _ = pixelize(s, PAL, n_acc=3, dk=0.2, mask=al, dither=False); mid_im = to_rgba(np.where(al[..., None], q, 0), al)
    ims = {'sky': sky_im, 'far': far_im, 'mid': mid_im}
    for k, im in ims.items(): im.save(f'{SRC}/out_{k}.png')
    preview([(sky_im, 0.02, 0.03, {}), (far_im, 0.05, 0.04, {}), (mid_im, 0.12, 0.08, {})], TINT, f'{SRC}/preview.png', [(0, 4), (128, 4), (49, 0)])
    if ase:
        for k, im in ims.items(): L.build(f'vista_h3_{k}', [im])


if __name__ == '__main__':
    cli(ROOM, SRC, guides, RENDER, build)
