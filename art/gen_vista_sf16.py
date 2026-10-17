#!/usr/bin/env python3
"""SF16 The Stargazer's Seat: the vista (docs/v17/vista_v3.md). Looking UP: the night the astronomers counted.

The great galactic arch climbs out of the far ranges at the left and sweeps across the whole sky, its bright core low over
the mountains, dark rifts of dust down its length, violet and teal nebula pockets in it. On the far ridge, the astronomers'
road: two small observatory domes and a ruined tower, one slit still faintly lit. Glass spires in the near dark.
(SF17 is the other starfall view: first light over the crater, low and wide. This one is night, high and deep.)

  python3 art/gen_vista_sf16.py              build assets from the saved renders (art/bg_src/vista_sf16/*_render.png)
  python3 art/gen_vista_sf16.py --guide      paint the guides only
  python3 art/gen_vista_sf16.py --sweep sky 1,2,3 [tag]   seed sweep (ComfyUI)   --pick sky 2 [tag]   copy a pick to *_render.png
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from vista_v3lib import *  # noqa
import vista_v3lib as L

ROOM = 'SF16'; SRC = src_dir(ROOM)
LW, LH = 512, 240
TINT = '#070716'
CORE = (104, 140)            # the galactic core (1x, sky layer)


def band_coords(C):
    """Distance across the galactic band (signed, px) and the position along it, for a gently curved arch."""
    # the arch: a circle through (-40, 236), CORE, (540, -20)
    p1, p2, p3 = np.array([-20, 250.0]), np.array(CORE, float), np.array([420, 196.0])
    ax, ay = p1; bx, by = p2; cx, cy = p3
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    R = math.hypot(ax - ux, ay - uy)
    r = np.sqrt((C.X - ux) ** 2 + (C.Y - uy) ** 2)
    ang = np.arctan2(C.Y - uy, C.X - ux); a0 = math.atan2(by - uy, bx - ux)
    along = (ang - a0) * R
    return r - R, along


def guide_sky():
    C = Canvas(LW, LH)
    nz = C.noise(80, 40, 3); nz2 = C.noise(18, 10, 4); nz3 = C.noise(6, 4, 5, 2)
    C.rgb = C.vgrad([(0, '05061a'), (70, '0b0c26'), (150, '161840'), (196, '252656'), (214, '35386a'), (240, '2b2d58')])
    # faint airglow band on the horizon: a thin green-teal over the violet
    C.add(np.exp(-((C.Y - 206) / 10) ** 2), hexc('2a5a5a'), 0.45)
    across, along = band_coords(C)
    wid = 26 + 12 * (nz - 0.5) * 2 + 16 * np.exp(-(along / 60) ** 2)          # wider at the core
    core_k = np.exp(-(along / 60) ** 2)
    band = np.exp(-(across / wid) ** 2)
    # the band's glow: lavender-blue body, warm cream core
    body = lerp(hexc('3a3878'), hexc('9a96d0'), np.clip(band * (0.55 + 0.6 * nz2), 0, 1)[..., None])
    C.fill_img(band, body, 0.85)
    C.add(np.exp(-((across) / (wid * 0.55)) ** 2) * core_k, hexc('f2d8a8'), 0.85)
    C.glow(CORE[0], CORE[1], 56, 30, hexc('ffe8c0'), 0.55, 1.6)
    C.glow(CORE[0], CORE[1], 24, 14, hexc('fff4dc'), 0.6, 1.4)
    # nebula pockets: magenta and teal clouds along the band edges (kept in C.neb: the build adds them again over the render)
    C.neb = np.zeros_like(C.rgb)
    for (dx, side, col, k) in ((-120, 1, 'a04898', 0.5), (-60, -1, '3a8ca0', 0.45), (60, 1, '8a3c9a', 0.4), (150, -1, '3c7ca8', 0.4),
                               (240, 1, '7a3a8c', 0.35)):
        m = np.exp(-((along - dx) / 46) ** 2) * np.exp(-((across - side * wid * 0.6) / (wid * 0.6)) ** 2) * smooth(0.3, 0.7, nz2)
        C.add(m, hexc(col), k * 1.6); C.neb += m[..., None] * hexc(col) * k
    # dust lanes: the great rift down the band, broken and wandering, darker at the core
    rift = np.exp(-((across - 6 * np.sin(along / 37) - 10 * (nz3 - 0.5)) / (5 + 6 * core_k)) ** 2) * smooth(0.25, 0.6, nz)
    C.fill(rift * band, hexc('120f2a'), 0.85)
    lanes = smooth(0.62, 0.72, nz2) * band * (1 - core_k * 0.5)
    C.fill(lanes, hexc('1a1838'), 0.55)
    # haze rising off the far ranges
    C.add(np.exp(-((C.Y - 196) / 18) ** 2) * (0.6 + 0.4 * nz), hexc('3a3a70'), 0.35)
    return C


def ridge_profiles(C):
    x = np.arange(C.WS) / S
    peak = 30 * np.exp(-((x - 236) / 46) ** 2) + 14 * np.exp(-((x - 318) / 26) ** 2) + 10 * np.exp(-((x - 60) / 40) ** 2)
    far = C.profile(192, (6, 4, 1.6), 41, (120, 30, 8)) - peak
    near = C.profile(204, (12, 6, 2.5), 51, (90, 26, 7))
    return far, near


DOMES = [(244, 'far'), (322, 'far')]


def guide_ridge():
    """The far ranges (alpha layer): two ridges in haze, a road of observatory domes and a ruined tower."""
    C = Canvas(LW, LH, base=hexc('101030'), alpha=True)
    far, near = ridge_profiles(C)
    nz = C.noise(30, 12, 7)
    mf = C.mask_below(far)
    C.fill_img(mf, lerp(hexc('2a2a58'), hexc('1c1c40'), smooth(186, 230, C.Y)[..., None]))
    C.fill(np.clip(mf - np.roll(mf, 2 * S, axis=0), 0, 1), hexc('5a5aa0'), 0.6)          # airglow catching the crest
    mn = C.mask_below(near)
    C.fill_img(mn, lerp(hexc('1a1a3a'), hexc('0e0e22'), smooth(200, 240, C.Y)[..., None]) * (0.9 + 0.2 * nz[..., None]))
    C.fill(np.clip(mn - np.roll(mn, 2 * S, axis=0), 0, 1), hexc('24284c'), 0.5)
    # observatory domes on the crests: a drum, a hemispherical cap with the shutter slit, one slit faintly lit
    for i, (x, which) in enumerate(DOMES):
        prof = far if which == 'far' else near
        y = float(prof[int(x * S)]) + 1
        r = 7 if which == 'far' else 9
        col = hexc('34346a') if which == 'far' else hexc('202044')
        C.fill(C.mask_poly([(x - r - 1, y + 4), (x + r + 1, y + 4), (x + r, y - 3), (x - r, y - 3)]), col)
        C.fill(C.mask_ellipse(x, y - 3, r, r * 0.9) * (C.Y < y - 3), col)
        C.fill(C.mask_ellipse(x, y - 3, r, r * 0.9) * (C.Y < y - 3) * (C.X < x - r * 0.3), hexc('6a6ab0'), 0.35)
        C.fill(C.mask_lines([(x + 1, y - 3 - r * 0.85, x + 1, y - 3, 1.2)]), hexc('e8c890') if i == 1 else hexc('141432'), 0.9)
    # the ruined tower of the road, snapped
    tx = 222; ty = float(far[int(tx * S)])
    C.fill(C.mask_poly([(tx - 4, ty + 3), (tx + 4, ty + 3), (tx + 3, ty - 30), (tx + 1, ty - 34), (tx - 3, ty - 27)]), hexc('2c2c5c'))
    C.fill(C.mask_poly([(tx - 4, ty + 3), (tx - 2, ty + 3), (tx - 2, ty - 28), (tx - 3, ty - 27)]), hexc('5a5aa0'), 0.4)
    return C


def guide_near():
    """Near glass spires: dark star-glass shards rising from the bottom (alpha layer, rendered on a flat key)."""
    C = Canvas(LW, LH, base=hexc('808080'), alpha=True)
    rng = np.random.default_rng(61)
    base = C.profile(232, (5, 2), 71, (60, 12))
    C.fill(C.mask_below(base), hexc('141634'))
    for x, h, w, lean in ((28, 46, 7, -0.15), (40, 30, 5, 0.1), (52, 18, 4, 0.2), (372, 40, 6, 0.12), (386, 58, 8, -0.05),
                          (400, 26, 5, 0.25), (466, 34, 6, -0.2), (478, 20, 4, 0.1), (130, 16, 4, -0.1), (300, 14, 4, 0.15)):
        b = float(base[int(x * S)]) + 2
        top = (x + lean * h, b - h)
        C.fill(C.mask_poly([(x - w / 2, b), (x + w / 2, b), top]), hexc('1c2050'))
        C.fill(C.mask_poly([(x - w / 2, b), (x - w * 0.1, b), top]), hexc('4a62b0'), 0.55)      # the lit facet (light from the core, left)
    return C


PROMPT_SKY = ('pixel art, breathtaking night sky, the milky way galaxy arching across the whole sky, bright glowing galactic core '
              'low over distant mountains, dark dust lanes, faint violet and teal nebula clouds, countless tiny stars, faint airglow '
              'on the horizon, serene, dark fantasy, deep indigo and violet palette with warm cream core, highly detailed, atmospheric')
PROMPT_RIDGE = ('pixel art, dark fantasy, distant mountain ranges at night in silhouette under a starry sky, small ancient stone '
                'observatory domes on the mountain crests, a ruined stone tower, cold blue mist in the valleys, starlight on the ridges, '
                'deep indigo palette, side-scroller game background, highly detailed')
PROMPT_NEAR = ('pixel art, dark fantasy, sharp dark crystal shards and glass spires rising from black rock, faceted, rim lit by cold '
               'starlight, isolated on a flat grey background, side-scroller game background layer, deep indigo and blue palette')


def guides():
    gs = guide_sky(); gs.save(f'{SRC}/guide_sky.png')
    gr = guide_ridge(); gr.save(f'{SRC}/guide_ridge.png', f'{SRC}/cover_ridge.png'); edges(gr.image()).save(f'{SRC}/edge_ridge.png')
    gn = guide_near(); gn.save(f'{SRC}/guide_near.png', f'{SRC}/cover_near.png'); edges(gn.image()).save(f'{SRC}/edge_near.png')
    Image.fromarray(np.clip(gs.rgb * (1 - gr.a[..., None]) + gr.rgb * gr.a[..., None], 0, 255).astype(np.uint8)).save(f'{SRC}/guide_preview.png')


RENDER = {   # name: (prompt, kwargs)
    'sky': (PROMPT_SKY, dict(denoise=0.55, pix=0.45)),
    'ridge': (PROMPT_RIDGE, dict(denoise=0.6, pix=0.5, edge=True, cn=0.5, cn_end=0.7)),
    'near': (PROMPT_NEAR, dict(denoise=0.62, pix=0.55, edge=True, cn=0.5, cn_end=0.7)),
}


def do_sweep(name, seeds, tag=''):
    use_prefix(ROOM)
    p, kw = RENDER[name]; kw = dict(kw)
    if kw.pop('edge', False): kw['edge_png'] = f'{SRC}/edge_{name}.png'
    return sweep(SRC, name, f'{SRC}/guide_{name}.png', p, seeds, tag, **kw)


# ----------------------------------------------------------------------------------------------- build
SKY_PAL = ['05061a', '080920', '0b0c26', '10112e', '141638', '1a1c44', '22244e', '2a2c5a', '343668', '403f78', '4c4a88', '5c5a9a',
           '6e6cae', '8482c0', '9c98d0', 'aaa4d6', 'b6b0dc', 'c4bce0', 'd0c8e4', 'dcd0dc', 'e8d6c8', 'f0dcb0', 'f8ead0', 'fff6e6',
           '7a5c98', '9a72a8', 'c09868', '2a5a5a', '3a7080',
           '6a3070', '8a3c8a', 'a858a0', '3a6c98']


def build_sky():
    a = np.asarray(Image.open(f'{SRC}/sky_render.png').convert('RGB'), float)
    gd = guide_sky(); across, along = band_coords(gd)
    a = grade(a, black=4, white=250, gamma=0.95, sat=1.08)
    # post (3x): the nebula colour back in (the render greys it), one coherent warm core instead of two blobs, the band a
    # step quieter where it crosses behind the play layer
    a = a * 0.9 + gd.neb * 0.9
    lum = a.mean(2, keepdims=True)
    cg = Canvas(LW, LH); cg.glow(CORE[0] + 4, CORE[1] - 2, 46, 26, (1, 1, 1), 1.0, 1.5)
    core = np.clip(cg.rgb[..., :1], 0, 1)
    a = a + core * np.array([60, 40, 10]) * 0.6          # a faint warm breath over the core, no new shape
    a = np.where(a > 190, 190 + (a - 190) * 0.45, a)                  # soft knee: the core glows, it does not blow out
    s = down(a, LW, LH)
    q, P = pixelize(s, SKY_PAL, n_acc=4, dk=0.3)
    rng = np.random.default_rng(16)
    bandk = np.asarray(Image.fromarray((np.exp(-(across / 40) ** 2) * 255).astype(np.uint8)).resize((LW, LH), Image.BOX), float) / 255
    sky_m = np.ones((LH, LW)); sky_m[200:] = 0
    w = 0.25 + 2.5 * bandk                                                                   # dense in the band, sparse out of it
    lum = q.mean(2); w = w * (lum < 200)
    st = stars(q, rng, 900, cols=('6e6cae', '8482c0', '9c98d0', 'b6b0dc'), mask=sky_m, weight=w)
    st += stars(q, rng, 140, cols=('d0c8e4', 'fff6e6', 'f8ead0'), mask=sky_m, weight=w)
    st += stars(q, rng, 0, big=9, big_cols=('fff6e6', 'd0c8e4', 'f8ead0'), mask=sky_m * (np.arange(LH)[:, None] < 170), weight=np.ones((LH, LW)))
    return q, st


def build_ridge():
    a = np.asarray(Image.open(f'{SRC}/ridge_render.png').convert('RGB'), float)
    a = grade(a, black=6, white=240, gamma=0.9, sat=0.9)
    s = down(a, LW, LH); al = cover_alpha(f'{SRC}/cover_ridge.png', LW, LH)
    q, P = pixelize(s, ['0e0e22', '141430', '1a1a3a', '20204a', '28285a', '30306a', '3c3c7a', '4a4a8c', '5a5aa0', '6e70b8', 'e8c890'],
                    n_acc=3, mask=al, dither=False)
    # rim light only along the far crest (the near ridge stays a dark mass), a step below the sky's band
    far, near = ridge_profiles(Canvas(LW, LH)); fy = np.asarray(far[1::S][:LW] if len(far) >= LW * S else far, float)
    rows = np.arange(LH)[:, None]; crest = np.abs(rows - fy[None, :LW]) < 3
    q = np.where((rim(q, al, hexc('5a5aa0')) != q).any(-1, keepdims=True) & crest[..., None], hexc('5a5aa0'), q)
    for x, which in DOMES:      # the observatory domes, stamped crisp (the model drops them): drum, cap, shutter slit
        y = int(round(float(far[int(x * S)])))
        lit = x == DOMES[1][0]
        for yy in range(y - 4, y + 3):
            for xx in range(x - 6, x + 7): q[yy, xx] = hexc('2a2a5a'); al[yy, xx] = True
        for yy in range(y - 10, y - 3):
            for xx in range(x - 6, x + 7):
                if (xx - x) ** 2 + ((yy - (y - 4)) * 1.1) ** 2 <= 36.5: q[yy, xx] = hexc('30306a'); al[yy, xx] = True
        for yy in range(y - 10, y - 3):      # the cap's lit left limb
            for xx in range(x - 6, x - 2):
                if al[yy, xx] and not al[yy, xx - 1] or (al[yy, xx] and not al[yy - 1, xx]): q[yy, xx] = hexc('5a5aa0')
        q[y - 4, x - 6:x + 7] = hexc('3c3c7a')                             # the ring under the cap
        for yy in range(y - 9, y - 3): q[yy, x + 1] = hexc('e8c890') if lit else hexc('141432')
        if lit: q[y - 1, x - 3] = hexc('c09868')                              # a lit door in the drum
    return q, al


def build_near():
    al = key_flat(f'{SRC}/near_render.png', LW, LH, f'{SRC}/cover_near.png', (128, 128, 128))
    a = np.asarray(Image.open(f'{SRC}/near_render.png').convert('RGB'), float)
    a = grade(a, black=10, white=300, gamma=0.85, sat=0.9)
    s = down(a, LW, LH)
    q, P = pixelize(s, ['07081a', '0c0e24', '12142e', '181c3c', '20264c', '2c3664', '3c4c84', '5068a8', '7088c8'], n_acc=2, mask=al, dither=False)
    q = rim(q, al, hexc('7088c8'))
    return q, al


def main():
    args = sys.argv[1:]
    if '--guide' in args or not os.path.exists(f'{SRC}/guide_sky.png'): guides()
    if '--guide' in args: return
    if '--sweep' in args:
        i = args.index('--sweep'); name, seeds = args[i + 1], [int(s) for s in args[i + 2].split(',')]
        tag = args[i + 3] if len(args) > i + 3 and not args[i + 3].startswith('--') else ''
        print(do_sweep(name, seeds, tag)); return
    if '--pick' in args:
        i = args.index('--pick'); tag = args[i + 3] if len(args) > i + 3 else ''
        pick(SRC, args[i + 1], int(args[i + 2]), tag); return
    sky, st = build_sky(); ridge, ral = build_ridge(); near, nal = build_near()
    ims = {'sky': to_rgba(sky), 'ridge': to_rgba(np.where(ral[..., None], ridge, 0), ral), 'near': to_rgba(np.where(nal[..., None], near, 0), nal)}
    for k, im in ims.items(): im.save(f'{SRC}/out_{k}.png')
    import json; json.dump([s for s in st if s[2] == 3 or s[1] < 190][:400], open(f'{SRC}/stars.json', 'w'))
    lay = [(ims['sky'], 0.02, 0.03, {}), (ims['ridge'], 0.06, 0.05, {}), (ims['near'], 0.16, 0.1, {})]
    preview(lay, TINT, f'{SRC}/preview.png', [(0, 56), (192, 56), (0, -58)])
    if '--no-ase' not in args:
        for k, im in ims.items(): build(f'vista_sf16_{k}', [im])
    print('ok')


if __name__ == '__main__':
    main()
