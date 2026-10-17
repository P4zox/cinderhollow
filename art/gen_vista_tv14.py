#!/usr/bin/env python3
"""TV14 Mossbed Glade: painted vista (agent V2, docs/v17/vista_v2.md).

Seen past the Mother Oak (lore sa_1: "a tree that old does not speak"): the old forest opens behind her onto a sunlit glade far
off, light falling through the canopy in slanted shafts into green-gold mist, colossal moss-hung trunks receding into it. The
regular Thornveil backdrop is dark teal trunks in gloom; this is the one place in the wood where the morning gets in, and the
oak stands black against it.

Planes: `far` (the glade, the mist, the far trunks and the shafts: one painting), `mid` (near trunks, hanging moss, ferns; by
hand at 1x, dark, rim-lit). fx: the shafts breathe, motes and a few fireflies drift in the light, mist drifts.

  python3 art/gen_vista_tv14.py [--guide | --sweep far 1,2 | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v2lib as L
from bgv2lib import smooth, lerp, S

ROOM = 'tv14'
SRC = os.path.join(HERE, 'bg_src', 'vista_' + ROOM); os.makedirs(SRC, exist_ok=True)
FW, FH = 400, 232
MW, MH = 416, 232
GLADE = (214, 120)          # the brightest point: the far glade (painting px; screen y = row - 16 + s)

PROMPT = ('pixel art, ancient enchanted forest, a vast cathedral of colossal moss-covered tree trunks receding into glowing green-gold '
          'mist, a sunlit glade far away in the distance, slanted god rays of warm morning sunlight falling through the high canopy, '
          'hanging moss and vines, ferns, soft light, depth, atmospheric perspective, serene, mystical, side-scroller game background, '
          'highly detailed, beautiful')
RENDER = dict(far=dict(denoise=0.66, cn=0.45, cn_end=0.6, pix=0.4))


def paint_far():
    C = L.Canvas(FW, FH); X, Y = C.X, C.Y; gx, gy = GLADE
    C.rgb = C.vgrad([(0, (18, 34, 26)), (60, (40, 70, 44)), (110, (120, 150, 80)), (150, (70, 100, 56)), (FH, (24, 40, 28))])
    dg = np.sqrt(((X - gx) * 0.5) ** 2 + ((Y - gy) * 1.0) ** 2)
    C.add(np.exp(-(dg / 46) ** 2), (150, 140, 70), 1.0); C.add(np.exp(-(dg / 16) ** 2), (60, 50, 20), 1.0)
    rng = np.random.default_rng(4)
    # trunks in four depths: far ones pale in the mist, nearer ones darker and wider
    for depth, n, wr, colk in [(0, 9, (3, 6), 0.75), (1, 7, (6, 10), 0.5), (2, 5, (10, 16), 0.25)]:
        xs = np.sort(rng.uniform(0, FW, n))
        for x in xs:
            if abs(x - gx) < 24 + depth * 10: x += 50 * np.sign(x - gx + 0.1)
            wd = rng.uniform(*wr); lean = rng.uniform(-0.04, 0.04)
            m = C.mask_poly([(x - wd - 4, FH), (x - wd + lean * 200, 0), (x + wd + lean * 200, 0), (x + wd + 4, FH)])
            haze = lerp(np.array((24, 40, 30.)), np.array((120, 150, 96.)), colk * np.exp(-((X - gx) / 160) ** 2)[..., None] + colk * 0.3)
            C.fill(m, haze)
            C.add(m * np.clip(1 - np.abs(X - (x - wd + 1)) / 2, 0, 1), (60, 80, 30), 0.6 * colk)    # a lit moss edge toward the light
    # slanted shafts from the upper left
    for k, x0 in enumerate((120, 170, 230, 280)):
        xr = X - (x0 + (Y - 0) * 0.45)
        sh = np.clip(1 - np.abs(xr) / (5 + k), 0, 1) * np.clip(1 - Y / 190, 0, 1)
        C.add(sh, (110, 110, 60), 0.6)
    # the glade floor glow and ferns line
    C.add(C.radial(gx, 150, 90, 14, 2), (90, 90, 40), 1.0)
    return C


def save_guides():
    F = paint_far(); im = F.image(); im.save(f'{SRC}/guide_far.png'); L.edges(im).save(f'{SRC}/edge_far.png')
    im.resize((FW * 2, FH * 2), Image.LANCZOS).save(f'{SRC}/guide_preview.png')


def cli_sweep(a):
    k = a[a.index('--sweep') + 1]; seeds = [int(s) for s in a[a.index('--sweep') + 2].split(',')]
    save_guides(); L.use_prefix(ROOM)
    kw = dict(RENDER[k])
    for i in range(len(a)):
        if a[i].startswith('--') and a[i][2:] in ('denoise', 'cn', 'cn_end', 'pix'): kw[a[i][2:]] = float(a[i + 1])
    tag = a[a.index('--tag') + 1] if '--tag' in a else ''
    L.sweep(SRC, k, PROMPT, seeds, tag=tag, **kw)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' in a: save_guides(); sys.exit()
    if '--sweep' in a: cli_sweep(a); sys.exit()


# ------------------------------------------------------------------------------------------------- build
PICK = dict(far=('b', 6))   # sweep tag b (denoise 0.84, cn 0.3: the guide's flat bars only hold the light where it is)


def grade(a):
    """Thornveil's room light multiplies the backdrop by ~0.57 except near-white pixels, so the glade's core is kept at the
    emissive knee and the mid-tones are lifted a little; the render's edge rows (a thin pale frame) are dropped."""
    l = L.lum(a)[..., None]
    b = a * (1.0 + 0.18 * np.clip((l - 60) / 80, 0, 1) * np.clip((200 - l) / 60, 0, 1))
    return np.clip(b, 0, 255)


def build(no_ase=False):
    hero = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    hero = hero[6:-6, 6:-6]
    f1 = grade(L.down(hero, FW, FH))
    q, _ = L.to_pixels(f1, 40, dk=0.35, hi=8, hi_lum=170, lo=6, lo_lum=30)
    far = L.rgba(q); far.save(f'{SRC}/out_far.png')
    L.composite_preview([(far, 0.03, 0.04, 0, False)], f'{SRC}/preview.png', [(0, 72), (192, 0), (56, 0)])
    if not no_ase: L.build(f'vista_{ROOM}_far', [far])


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' not in a and '--sweep' not in a: build(no_ase='--no-ase' in a)
