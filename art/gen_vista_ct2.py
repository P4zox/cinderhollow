#!/usr/bin/env python3
"""CT2 The Last Gate: the vista (docs/v17/vista_v3.md). The World 2 view. Keep the beyond vague.

"There is light behind it with no sun to make it. Ash falls upward here, as if the world beyond were breathing in."
A pale storm ceiling in long strata over an abyss of mist. Ahead, where the gate stands (the prop, 82_forge.js), the cloud
is thin and lit from behind by a light with no source: a tall soft glow, faint rays fanning UP into the cloud, and in it,
barely there, impossibly tall pale shapes -- spires, or not -- that could be cloud. Behind the player the old causeway
recedes into the mist on broken piers. The light sits at sky x 331: as the player walks east it stays where it is on
screen ("it does not seem to get nearer") and when seated it stands behind the gate prop.

  python3 art/gen_vista_ct2.py [--guide | --sweep <far|mid> 1,2,3 [tag] | --pick <name> <seed> [tag] | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from vista_v3lib import *  # noqa
import vista_v3lib as L

ROOM = 'CT2'; SRC = src_dir(ROOM)
LW, LH = 512, 240
TINT = '#2d3849'
LX, LY = 331, 150          # the light (sky layer)
HOR = 154                  # the mist horizon


def sky(C):
    nz = C.noise(120, 30, 3); nz2 = C.noise(30, 6, 4)
    near_l = np.exp(-((C.X - LX) / 120) ** 2)
    v = 0.12 + 0.55 * smooth(0, HOR, C.Y) + 0.3 * near_l * smooth(20, HOR, C.Y) + 0.12 * (nz - 0.5)
    C.rgb = lerp(hexc('2d3849'), hexc('d2d8df'), np.clip(v, 0, 1)[..., None])
    # long strata, darker undersides, lit toward the light
    for (y0, y1, cx, cy, sd, lo, hi, k) in ((0, 50, 200, 9, 31, '364356', '6b7686', 0.85), (36, 96, 170, 7, 32, '4f6079', 'a5afbc', 0.8),
                                          (80, 140, 130, 5, 33, '6b7686', 'dfe4ea', 0.7)):
        d = C.noise(cx, cy, sd, 3); band = smooth(y0, y0 + 12, C.Y) * (1 - smooth(y1 - 12, y1, C.Y))
        m = smooth(0.5, 0.62, d) * band; shade = np.clip(0.25 + 0.75 * near_l + 0.3 * (d - 0.55), 0, 1)
        C.fill_img(m, lerp(hexc(lo), hexc(hi), shade[..., None]), k)
        C.fill(np.clip(m - np.roll(m, int(-2 * S), axis=0), 0, 1), hexc(lo), 0.5 * k)
    # the rift: the cloud thins over the light; a tall soft glow with no disc; rays fan UP from below the horizon
    C.glow(LX, LY, 80, 120, hexc('eef1f4'), 0.55, 1.3)
    C.glow(LX, LY - 10, 30, 90, hexc('f6f7f8'), 0.45, 1.2)
    C.glow(LX, LY + 4, 120, 14, hexc('f4efe6'), 0.35, 1.5)
    for k, ang in enumerate((-0.6, -0.36, -0.16, 0.0, 0.18, 0.4, 0.62)):
        x1 = LX + math.tan(ang) * 150
        ray = C.mask_poly([(LX - 3, LY + 8), (LX + 3, LY + 8), (x1 + 10, LY - 150), (x1 - 10, LY - 150)], blur=3)
        C.add(ray * smooth(LY + 8, LY - 100, C.Y) * smooth(LY - 160, LY - 60, C.Y), hexc('f6f7f8'), 0.09 + 0.04 * (k % 2))
    # impossible shapes in the light, deep in the haze: tall, pale, barely darker than the glow
    for (x, w, h, lean) in ((LX - 34, 7, 104, 0.04), (LX - 18, 4, 78, -0.03), (LX + 22, 9, 120, -0.02), (LX + 44, 4, 70, 0.05), (LX + 6, 3, 56, 0.0)):
        C.fill(C.mask_poly([(x - w / 2, HOR + 2), (x + w / 2, HOR + 2), (x + w * 0.15 + lean * h, HOR - h), (x - w * 0.15 + lean * h, HOR - h)], blur=0.8),
               hexc('a5afbc'), 0.55)
    return C


def far(C):
    """The mist sea and the old causeway receding into it on broken piers (cover = far)."""
    cov = np.zeros_like(C.X)
    near_l = np.exp(-((C.X - LX) / 140) ** 2)
    sea_top = HOR + 3 * np.sin(C.X * 0.07) + 2 * np.sin(C.X * 0.19 + 1) + 3 * (C.noise(20, 400, 81, 1) - 0.5)
    sea = (C.Y > sea_top).astype(float)
    sv = 0.66 - 0.5 * smooth(HOR, LH, C.Y) + 0.12 * (C.noise(30, 6, 82, 2) - 0.5) + 0.3 * near_l * (1 - smooth(HOR, HOR + 40, C.Y))
    C.fill_img(sea, lerp(hexc('4f6079'), hexc('dfe4ea'), np.clip(sv, 0, 1)[..., None])); cov = np.maximum(cov, sea)
    rng = np.random.default_rng(83)
    for k in range(30):     # billows
        bx = rng.uniform(0, LW); by = rng.uniform(HOR + 4, LH - 10); r = rng.uniform(8, 22)
        bm = C.mask_ellipse(bx, by, r * 2, r * 0.45) * sea
        C.fill(bm, lerp(hexc('6b7686'), hexc('b0b9c4'), 1 - (by - HOR) / 90), 0.45, cover=False)
        C.fill(C.mask_ellipse(bx, by - r * 0.2, r * 1.6, r * 0.2) * sea, hexc('c4ccd5'), 0.35, cover=False)
    # the old causeway: a deck on piers, receding left into the mist (perspective: lower and hazier with distance)
    deck = lambda x: HOR - 2 + 26 * smooth(250, 0, x)
    for x0 in range(-10, 240, 1):
        pass
    pts_top = [(x, deck(x) - 3 - 3 * smooth(250, 0, x)) for x in np.linspace(-10, 236, 40)]
    pts_bot = [(x, deck(x) + 2 + 2 * smooth(250, 0, x)) for x in np.linspace(236, -10, 40)]
    dm = C.mask_poly(pts_top + pts_bot)
    gap = (C.X > 120) & (C.X < 146)          # a fallen span
    dm = dm * ~gap
    haze_k = smooth(0, 236, C.X)
    C.fill_img(dm, lerp(hexc('3f4c60'), hexc('a5afbc'), haze_k[..., None])); cov = np.maximum(cov, dm)
    px = 8
    while px < 236:
        sp = 30 * (1 - 0.7 * px / 236)
        h = deck(px); w = 6 * (1 - 0.6 * px / 236) + 1
        pm = C.mask_poly([(px - w / 2, h), (px + w / 2, h), (px + w / 2 + 1, LH + 2), (px - w / 2 - 1, LH + 2)])
        if not (120 < px < 146):
            C.fill_img(pm * (C.Y < sea_top + 30), lerp(hexc('364356'), hexc('9aa4b2'), haze_k[..., None])); cov = np.maximum(cov, pm * (C.Y < sea_top + 30))
        px += sp
    # tall banded obelisks along the old road, the farthest barely there
    for (x, h, w) in ((30, 64, 7), (96, 46, 5), (176, 30, 3.5), (222, 20, 2.5)):
        b = deck(x) - 3; m = C.mask_poly([(x - w / 2, b), (x + w / 2, b), (x + w * 0.3, b - h), (x, b - h - w), (x - w * 0.3, b - h)])
        C.fill_img(m, lerp(hexc('3f4c60'), hexc('a5afbc'), haze_k[..., None])); cov = np.maximum(cov, m)
        C.fill(m * (C.X > x), hexc('c4ccd5'), 0.25 * (1 - x / 240))
    return cov


def near(C):
    """Nearer broken piers and a snapped obelisk on the left, one pylon right (cover = mid)."""
    cov = np.zeros_like(C.X)
    for (x, top, w) in ((-4, 150, 22), (56, 168, 16), (470, 160, 18)):
        m = C.mask_poly([(x, LH + 2), (x + w, LH + 2), (x + w - 1, top), (x + w * 0.6, top - 4), (x + w * 0.3, top + 3), (x + 1, top)])
        C.fill_img(m, lerp(hexc('2d3849'), hexc('4f6079'), smooth(top, LH, C.Y)[..., None])); cov = np.maximum(cov, m)
        C.fill(m * (C.X > x + w - 3), hexc('8f9aa8'), 0.5)
    x, b = 26, 168
    m = C.mask_poly([(x - 6, b), (x + 6, b), (x + 4, b - 70), (x + 1, b - 76), (x - 3, b - 66)])     # a snapped obelisk on a pier
    C.fill(m, hexc('364356')); C.fill(m * (C.X > x + 1), hexc('8f9aa8'), 0.5); cov = np.maximum(cov, m)
    for y in (b - 20, b - 44): C.fill(C.mask_poly([(x - 6, y), (x + 6, y), (x + 6, y + 2), (x - 6, y + 2)]) * m, hexc('4f6079'), 0.8)
    return cov


def guides():
    gs = sky(Canvas(LW, LH)); gs.save(f'{SRC}/guide_sky.png')
    gf = sky(Canvas(LW, LH)); cf = far(gf); gf.save(f'{SRC}/guide_far.png'); Image.fromarray((np.clip(cf, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_far.png')
    edges(gf.image()).save(f'{SRC}/edge_far.png')
    gm = sky(Canvas(LW, LH)); far(gm); cm = near(gm); gm.save(f'{SRC}/guide_mid.png'); Image.fromarray((np.clip(cm, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_mid.png')
    edges(gm.image()).save(f'{SRC}/edge_mid.png')
    gm.image().save(f'{SRC}/guide_preview.png')


PROMPT = ('pixel art, dark fantasy, the edge of the world, a pale cold ash grey sky of long stratus clouds over an endless sea of '
          'mist, ahead the clouds thin where a soft sourceless white light glows from beyond the horizon, faint rays rising up '
          'into the clouds, vague impossibly tall pale spires barely visible in the haze of the light, an ancient broken stone '
          'causeway on piers receding into the mist, tall weathered obelisks, mysterious, solemn, atmospheric perspective, '
          'muted slate blue and ash grey palette with faint warm white, highly detailed')
RENDER = {
    'far': (PROMPT, dict(denoise=0.55, pix=0.4, edge=True, cn=0.45, cn_end=0.65)),
    'mid': (PROMPT, dict(denoise=0.52, pix=0.45, edge=True, cn=0.5, cn_end=0.7)),
}
ASH = ['1f2633', '262f3e', '2d3849', '364356', '3f4c60', '4f6079', '566273', '5f6b7d', '6b7686', '76818f', '7c8ea8', '8f9aa8', '9aa4b2',
       'a5afbc', 'b0b9c4', 'b7c0cb', 'c4ccd5', 'd2d8df', 'dfe4ea', 'eef1f4', 'f6f7f8', 'e8e2d8', 'f4efe6']


def build(ase=True):
    a = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    a = knee(grade(a, black=2, white=255, gamma=1.05, sat=0.9), 175, 0.42, 'f4efe6', 0.35)
    # the glow is held two steps under white: the room's light pool around the player and the bloom pass lift it again
    h_, w_ = a.shape[:2]; yy, xx = np.mgrid[0:h_, 0:w_]
    a = a * (1 - 0.18 * np.exp(-((xx / S - LX) / 70) ** 2) * np.exp(-((yy / S - 110) / 60) ** 2))[..., None]
    # and the whole view a step lower in value (the player's light pool reads as a disc on a pale sky; less so on a mid one),
    # the light's core kept
    core = np.exp(-((xx / S - LX) / 40) ** 2) * np.exp(-((yy / S - 120) / 50) ** 2)
    a = a * (0.84 + 0.16 * core)[..., None]
    s = down(a, LW, LH); cov = cover_alpha(f'{SRC}/cover_far.png', LW, LH, 0.02)
    sk = fill_under(s, np.asarray(Image.fromarray((cov * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), float) > 0)
    q, _ = pixelize(sk, ASH, n_acc=3, dk=0.3); sky_im = to_rgba(q)
    al = cover_alpha(f'{SRC}/cover_far.png', LW, LH)
    q, _ = pixelize(s, ASH, n_acc=3, dk=0.25, mask=al); far_im = to_rgba(np.where(al[..., None], q, 0), al)
    a = np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float)
    s = down(knee(grade(a, black=6, white=255, gamma=0.95, sat=0.9), 215, 0.6), LW, LH); al = cover_alpha(f'{SRC}/cover_mid.png', LW, LH)
    q, _ = pixelize(s, ASH, n_acc=2, dk=0.2, mask=al, dither=False); mid_im = to_rgba(np.where(al[..., None], q, 0), al)
    ims = {'sky': sky_im, 'far': far_im, 'mid': mid_im}
    for k, im in ims.items(): im.save(f'{SRC}/out_{k}.png')
    preview([(sky_im, 0.02, 0.04, {}), (far_im, 0.05, 0.05, {}), (mid_im, 0.1, 0.08, {})], TINT, f'{SRC}/preview.png', [(0, 344), (448, 344), (1088, 344), (774, 115)])
    if ase:
        for k, im in ims.items(): L.build(f'vista_ct2_{k}', [im])


if __name__ == '__main__':
    cli(ROOM, SRC, guides, RENDER, build)
