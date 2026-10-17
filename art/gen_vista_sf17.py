#!/usr/bin/env python3
"""SF17 The Crater Edge: the vista (docs/v17/vista_v3.md). Looking OUT, low and wide, at first light.

"This is the garden's last morning, and it has lasted a thousand years." Dawn that never finishes: a rose-gold band low
on the horizon under thin lit stratus, the last stars and the morning star above. The crater lies open below the far rim:
a black glass plain that mirrors the dawn, and in its heart the fallen star still breathing, a cold blue column of light
rising out of the crater into the morning. On the left crag, the shattered observatory: broken dome ribs and a snapped
telescope against the sky. (SF16 is the other starfall view: the deep night zenith.)

  python3 art/gen_vista_sf17.py [--guide | --sweep <sky|far|mid> 1,2,3 [tag] | --pick <name> <seed> [tag] | --no-ase]
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from vista_v3lib import *  # noqa

ROOM = 'SF17'; SRC = src_dir(ROOM)
LW, LH = 512, 240
TINT = '#0a1024'
DAWN = (300, 120)      # the glow on the horizon (below it, the sun that never rises)
HEART = (196, 150)     # the fallen star in the crater floor; its column rises from here
RIM_Y = 122
PATCH = [(141.7, 79, 7), (119.3, 87.3, 3.5)]      # far_render (seed b5): two lens-flare orbs the model added


def sky(C):
    nz = C.noise(90, 30, 3); nz2 = C.noise(24, 6, 4)
    C.rgb = C.vgrad([(0, '060a1e'), (40, '0c1430'), (80, '1c2c50'), (100, '3a4a6c'), (112, '6a5a78'), (120, 'a87880'), (126, 'c89088'), (134, '906878'), (240, '403c58')])
    dx = (C.X - DAWN[0]) / 150
    C.add(np.exp(-dx ** 2) * np.exp(-((C.Y - DAWN[1]) / 26) ** 2), hexc('ffd0a0'), 0.28)
    C.add(np.exp(-dx ** 2 * 0.3) * np.exp(-((C.Y - DAWN[1]) / 60) ** 2), hexc('a07080'), 0.35)
    # long thin stratus, lit rose underneath, high ones still blue-grey
    for (y0, y1, cx, cy, sd, lo, hi, k) in ((52, 74, 140, 5, 31, '2a3658', '6a6a8c', 0.7), (78, 100, 110, 4, 32, '4a4a6a', 'e0a090', 0.8),
                                          (96, 112, 90, 3, 33, '6a5a74', 'f0c0a0', 0.75)):
        d = C.noise(cx, cy, sd, 3)
        band = smooth(y0, y0 + 6, C.Y) * (1 - smooth(y1 - 6, y1, C.Y))
        m = smooth(0.5, 0.62, d) * band
        lit = np.clip(np.exp(-dx ** 2 * 0.8) * 1.2 + 0.15, 0, 1)
        C.fill_img(m, lerp(hexc(lo), hexc(hi), lit[..., None]), k)
        under = np.clip(m - np.roll(m, int(-1.5 * S), axis=0), 0, 1)
        C.fill(under * lit, hexc('ffd0a8'), 0.6 * k)
    # the column of cold light out of the crater, and its halo
    col = np.exp(-((C.X - HEART[0]) / (3 + 0.04 * np.clip(HEART[1] - C.Y, 0, 200))) ** 2) * smooth(-10, 120, C.Y) * (C.Y < HEART[1])
    C.add(col, hexc('a8d0ff'), 0.75)
    C.glow(HEART[0], RIM_Y - 4, 60, 34, hexc('5a8ad0'), 0.45, 1.6)
    return C


def rim_profile(C):
    x = np.arange(C.WS) / S
    notch = 7 * np.exp(-((x - DAWN[0]) / 30) ** 2)
    return C.profile(RIM_Y, (4, 3, 1.4), 81, (90, 22, 6)) + notch - 5 * np.exp(-((x - 420) / 40) ** 2)


def land(C, rgb_only=False):
    """The far rim and the black glass crater floor (cover = the far layer)."""
    rp = rim_profile(C)
    m = C.mask_below(rp)
    nz = C.noise(40, 8, 91); nz2 = C.noise(10, 3, 92, 2)
    # far rim: cliffs in haze, lit rose on their faces toward the dawn
    rimband = smooth(RIM_Y - 12, RIM_Y + 4, C.Y) * (1 - smooth(RIM_Y + 4, RIM_Y + 12, C.Y))
    land_rgb = lerp(hexc('3a3a5a'), hexc('1a1e36'), smooth(RIM_Y, RIM_Y + 14, C.Y)[..., None])
    land_rgb = land_rgb + (np.exp(-((C.X - DAWN[0]) / 90) ** 2) * rimband)[..., None] * hexc('604050') * 0.8
    C.fill_img(m, land_rgb)
    # the glass plain: black, mirror bands, the dawn's reflection a vertical smear under the glow, the column's under the heart
    plain = smooth(RIM_Y + 10, RIM_Y + 16, C.Y)
    pr = lerp(hexc('0c1024'), hexc('141a34'), smooth(140, 240, C.Y)[..., None])
    C.fill_img(m * plain, pr)
    refl = np.exp(-((C.X - DAWN[0]) / (18 + 0.4 * (C.Y - RIM_Y))) ** 2) * np.exp(-((C.Y - RIM_Y - 18) / 40) ** 2) * (0.6 + 0.6 * nz2)
    C.add(m * plain * refl, hexc('c08878'), 0.55)
    cr = np.exp(-((C.X - HEART[0]) / 5) ** 2) * smooth(HEART[1], HEART[1] + 50, C.Y) * (1 - smooth(HEART[1] + 50, 230, C.Y)) * (0.5 + 0.8 * nz2)
    C.add(m * cr, hexc('7aa8f0'), 0.6)
    for y in range(RIM_Y + 18, 240, 7):      # mirror bands across the glass
        C.add(m * C.mask_lines([(0, y + 0.3 * (y % 5), LW, y, 0.6)]) * (0.3 + 0.7 * nz), hexc('3a4670'), 0.35)
    # the heart: a cluster of blue star-glass shards breathing light, a lit mist around it
    C.glow(HEART[0], HEART[1] + 2, 46, 12, hexc('3c6ab8'), 0.55, 1.5)
    for (dx, h, w, lean) in ((0, 18, 5, 0.0), (-6, 11, 4, -0.3), (6, 13, 4, 0.25), (-12, 6, 3, -0.4), (11, 7, 3, 0.4)):
        b = HEART[1] + 4; x = HEART[0] + dx
        C.fill(C.mask_poly([(x - w / 2, b), (x + w / 2, b), (x + lean * h, b - h)]), hexc('bfe0ff'))
        C.fill(C.mask_poly([(x, b), (x + w / 2, b), (x + lean * h, b - h)]), hexc('6a9ae0'), 0.7)
    C.glow(HEART[0], HEART[1] - 4, 16, 14, hexc('e0f0ff'), 0.6, 1.2)
    return m


def crag(C):
    """The left crag with the shattered observatory, and the near rim's inner slope along the bottom (cover = mid layer)."""
    top = lambda x: 74 + 0.5 * max(0, x - 60) ** 1.25
    pts = [(-4, 240), (-4, 78), (8, 70), (22, 66), (40, 64), (58, 66), (72, 74), (88, 92), (104, 112), (118, 132), (140, 150), (180, 168),
           (240, 182), (320, 190), (420, 194), (520, 196), (520, 240)]
    m = C.mask_poly(pts)
    nz = C.noise(16, 10, 101)
    C.fill_img(m, lerp(hexc('141830'), hexc('0a0c1c'), smooth(70, 200, C.Y)[..., None]) * (0.85 + 0.3 * nz[..., None]))
    # the dawn catches the crag's right shoulder
    lit = np.clip(m - np.roll(np.roll(m, int(-3 * S), axis=1), int(2 * S), axis=0), 0, 1) * (C.X > 40)
    C.fill(lit, hexc('8a5a6a'), 0.7)
    # the shattered observatory: a broken drum, two standing dome ribs, a snapped telescope tube canted at the sky
    C.fill(C.mask_poly([(18, 66), (54, 66), (52, 50), (44, 48), (40, 52), (30, 47), (20, 52)]), hexc('1e2240'))
    for x0, y0, x1, y1 in ((22, 50, 30, 28), (30, 28, 40, 24), (50, 50, 44, 32)):
        C.fill(C.mask_lines([(x0, y0, x1, y1, 2.2)]), hexc('22264a'))
    C.fill(C.mask_lines([(36, 50, 60, 30, 3.4)]), hexc('2a2e56'))
    C.fill(C.mask_lines([(36, 50, 60, 30, 1.0)]), hexc('7a5a70'), 0.6)
    # frost crystals on the near slope, catching the dawn
    rng = np.random.default_rng(111)
    for k in range(18):
        x = rng.uniform(100, 500); yb = np.interp(x, [p[0] for p in pts[8:]], [p[1] for p in pts[8:]]) + rng.uniform(2, 14)
        h = rng.uniform(4, 13); lean = rng.uniform(-0.3, 0.3)
        C.fill(C.mask_poly([(x - 2, yb), (x + 2, yb), (x + lean * h, yb - h)]), hexc('2a3a6a'))
        C.fill(C.mask_poly([(x, yb), (x + 2, yb), (x + lean * h, yb - h)]), hexc('8aa0d0'), 0.6)
    return m


def ruins(q, al):
    """The shattered observatory on the crag, drawn crisp at 1x (the model melts it): a broken drum wall, three standing dome
    ribs, a snapped telescope tube canted at the sky. Dark against the dawn, lit rose on the faces toward it."""
    D, R, K = (30, 34, 64, 255), (122, 80, 100, 255), (20, 22, 44, 255)
    def fn(d):
        d.polygon([(16, 68), (56, 68), (55, 56), (50, 53), (47, 57), (42, 50), (36, 54), (31, 47), (26, 52), (20, 50), (17, 56)], fill=K)
        for y in range(54, 68, 4): d.line([(18, y), (54, y)], fill=D)              # courses
        d.line([(55, 56), (55, 67)], fill=R); d.line([(50, 53), (54, 55)], fill=R)
        for (x0, y0), (x1, y1), (x2, y2) in (((20, 50), (22, 34), (30, 25)), ((31, 47), (33, 30), (38, 23)), ((50, 53), (52, 40), (47, 30))):
            d.line([(x0, y0), (x1, y1), (x2, y2)], fill=K, width=2)
            d.line([(x0 + 1, y0), (x1 + 1, y1), (x2 + 1, y2)], fill=R, width=1)
        d.line([(34, 52), (62, 33)], fill=K, width=4); d.line([(36, 50), (63, 32)], fill=R, width=1)   # the tube
        d.polygon([(60, 31), (66, 29), (67, 33), (62, 36)], fill=K); d.line([(66, 29), (67, 33)], fill=(176, 122, 122, 255))
        d.line([(38, 54), (34, 66)], fill=K, width=2); d.line([(42, 54), (46, 66)], fill=K, width=2)    # its broken mount
    draw1x(q, al, fn)


def guides():
    gs = sky(Canvas(LW, LH)); gs.save(f'{SRC}/guide_sky.png')
    gf = sky(Canvas(LW, LH)); cf = land(gf); gf.save(f'{SRC}/guide_far.png'); Image.fromarray((cf * 255).astype(np.uint8)).save(f'{SRC}/cover_far.png')
    edges(gf.image()).save(f'{SRC}/edge_far.png')
    gm = sky(Canvas(LW, LH)); land(gm); cm = crag(gm); gm.save(f'{SRC}/guide_mid.png'); Image.fromarray((cm * 255).astype(np.uint8)).save(f'{SRC}/cover_mid.png')
    edges(gm.image()).save(f'{SRC}/edge_mid.png')
    gm.image().save(f'{SRC}/guide_preview.png')


PROMPT = ('pixel art, dark fantasy landscape at dawn, view from the rim of a vast meteor crater, the crater floor a black glass '
          'plain mirroring the sky, at its heart a cluster of glowing blue crystal shards with a pillar of cold blue light rising '
          'into the sky, far jagged crater rim cliffs in haze, rose gold dawn glow low on the horizon, thin lit stratus clouds, '
          'last stars in a deep blue sky, serene, melancholy, highly detailed, atmospheric perspective')
PROMPT_MID = PROMPT + ', a dark rocky crag in the foreground with the shattered ruins of a stone observatory dome and a broken telescope'
RENDER = {
    'sky': (PROMPT, dict(denoise=0.5, pix=0.45)),
    'far': (PROMPT, dict(denoise=0.55, pix=0.5, edge=True, cn=0.45, cn_end=0.6)),
    'mid': (PROMPT_MID, dict(denoise=0.55, pix=0.55, edge=True, cn=0.5, cn_end=0.7)),
}

PAL_SKY = ['060a1e', '0a1026', '0e162e', '142038', '1c2c50', '24365c', '2e4268', '3a4a6c', '4a5478', '5a6084', '6a6a8c', '7a6a80',
           '8a7088', 'a07884', 'b88a88', 'c89088', 'd8a08c', 'e8b490', 'f0c8a0', 'f8dcb8', 'fff0dc', 'a8d0ff', 'd8ecff', '6a8ad0']
PAL_LAND = ['06081a', '0a0c1c', '0c1024', '10142c', '141830', '1a1e36', '22264a', '2a2e56', '3a3a5a', '3a4670', '4a4a6a', '604858',
            '8a5a6a', 'b07a7a', 'c08878', '3c6ab8', '6a9ae0', '8aa0d0', 'bfe0ff', 'e0f0ff']


def build(ase=True):
    rng = np.random.default_rng(17)
    # the sky comes from the far render (one light for both): below the rim, each column continues the horizon colour down
    a = patch_rows(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float), PATCH)
    a = knee(grade(a, black=2, white=255, gamma=1.0, sat=1.05), 185, 0.55, 'f0c0a0', 0.4)    # the dawn glows rose-gold, never white
    s = down(a, LW, LH)
    cov = np.asarray(Image.open(f'{SRC}/cover_far.png').convert('L').resize((LW, LH), Image.BOX), float) / 255 > 0.02
    for x in range(LW):
        ys = np.nonzero(cov[:, x])[0]
        if len(ys): y0 = max(0, ys[0] - 2); s[y0:, x] = s[y0 - 1, x]
    q, _ = pixelize(s, PAL_SKY, n_acc=4, dk=0.3)
    yy = np.arange(LH)[:, None] * np.ones((1, LW))
    w = np.clip(1 - yy / 90, 0, 1) ** 1.5                                     # the last stars: only high up, fading toward the dawn
    stars(q, rng, 220, cols=('6a6a8c', '8a8aa8', 'a8a8c8'), weight=w + 1e-6)
    stars(q, rng, 30, cols=('d8ecff', 'fff0dc'), weight=w + 1e-6)
    ms = (340, 30); q[ms[1], ms[0]] = hexc('fff0dc')                        # the morning star
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): q[ms[1] + dy, ms[0] + dx] = hexc('d8a08c')
    sky_im = to_rgba(q)
    # far: the rim + glass plain, cut by the guide's cover
    a = patch_rows(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float), PATCH)
    s = down(knee(grade(a, black=2, white=250, gamma=0.95), 185, 0.55, 'f0c0a0', 0.4), LW, LH); al = cover_alpha(f'{SRC}/cover_far.png', LW, LH)
    q, _ = pixelize(s, PAL_LAND + PAL_SKY[8:20], n_acc=4, dk=0.3, mask=al)
    far_im = to_rgba(np.where(al[..., None], q, 0), al)
    a = np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float)
    s = down(grade(a, black=6, white=255, gamma=0.9, sat=0.9), LW, LH); al = cover_alpha(f'{SRC}/cover_mid.png', LW, LH)
    q, _ = pixelize(s, PAL_LAND, n_acc=3, dk=0.2, mask=al, dither=False)
    ruins(q, al)
    mid_im = to_rgba(np.where(al[..., None], q, 0), al)
    ims = {'sky': sky_im, 'far': far_im, 'mid': mid_im}
    for k, im in ims.items(): im.save(f'{SRC}/out_{k}.png')
    preview([(sky_im, 0.02, 0.03, {}), (far_im, 0.05, 0.04, {}), (mid_im, 0.12, 0.08, {})], TINT, f'{SRC}/preview.png', [(0, 72), (256, 72), (0, -92)])
    if ase:
        for k, im in ims.items(): L.build(f'vista_sf17_{k}', [im])


import vista_v3lib as L  # noqa: E402
if __name__ == '__main__':
    cli(ROOM, SRC, guides, RENDER, build)
