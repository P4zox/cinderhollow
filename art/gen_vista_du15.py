#!/usr/bin/env python3
"""DU15 The Last Oasis: painted vista (agent V2, docs/v17/vista_v2.md).

Kept from the old sky (xsb_sky 'sunset', 54_sb.js): the sun-kings' evening, a great sun going down behind dunes and a pyramid.
Raised (lore sb_7, "the evening ... arrives here every evening, on water that has never learned it is underground"): a still
lake runs from the pool to the horizon and holds the whole sunset upside down; far pyramids and a sun temple stand in the
haze, the sun half sunk behind the dunes. Near bank (by hand, 1x): a broken colonnade, an obelisk and a dune spit.

Planes: `far` (sky, sun, dunes, pyramids, the lake and its reflection; one painting), `glint` (4 frames over far: the sun's
road shimmering), `mid` (the near bank, 1x). fx: heat shimmer over the horizon, the first stars, drifting cirrus.

  python3 art/gen_vista_du15.py [--guide | --sweep far 1,2 | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v2lib as L
from bgv2lib import smooth, lerp, S

ROOM = 'du15'
SRC = os.path.join(HERE, 'bg_src', 'vista_' + ROOM); os.makedirs(SRC, exist_ok=True)
FW, FH = 400, 232          # far: fac 0.04 over cam.x 0..192 (8 px)
MW, MH = 416, 232          # mid: fac 0.1 (20 px)
SUN = (212, 120, 15)
HZ = 128                   # the far shore / horizon

PROMPT = ('pixel art, breathtaking desert sunset, a huge red-gold sun half sunk behind distant dunes, ancient pyramids and a sun temple '
          'silhouetted in warm haze on the horizon, a vast perfectly still lake in the foreground mirroring the whole sunset sky '
          'upside down, soft rippled reflections of light on calm water, two tall obelisks, banded sky from deep crimson violet zenith to orange and gold, thin '
          'glowing cirrus streaks, first stars, serene, majestic, side-scroller game background, highly detailed, beautiful')
RENDER = dict(far=dict(denoise=0.66, cn=0.45, cn_end=0.6, pix=0.4))
PICK = dict(far=1)


def paint_far():
    C = L.Canvas(FW, FH); X, Y = C.X, C.Y; sx, sy, sr = SUN
    sky = C.vgrad([(0, (40, 16, 52)), (40, (96, 28, 70)), (80, (200, 60, 60)), (108, (246, 130, 50)), (HZ, (255, 200, 90))])
    C.rgb = sky.copy()
    ds = np.sqrt(((X - sx) * 0.6) ** 2 + (Y - sy) ** 2)
    C.add(np.exp(-(ds / 60) ** 2), (60, 40, 10), 1.0)
    nz = C.noise(70, 8, 5, 4)
    for cy, th, x0, x1 in [(30, 2.5, 140, 400), (46, 3, 0, 240), (64, 3, 160, 400), (82, 3.5, 20, 280), (98, 2.5, 220, 400)]:
        wob = cy + (X - x0) * -0.03 + 3 * (nz - 0.5)
        band = np.clip(1 - np.abs(Y - wob) / th, 0, 1) ** 1.4 * smooth(x0 - 30, x0 + 30, X) * (1 - smooth(x1 - 30, x1 + 30, X))
        C.fill(band, lerp(np.array((200, 90, 110.)), np.array((255, 190, 110.)), np.clip(Y / 100, 0, 1)[..., None]), 0.7)
    rng = np.random.default_rng(9)
    for _ in range(36):
        x, y = rng.uniform(0, FW), rng.uniform(2, 34)
        C.fill(C.ellipse(x, y, 0.7, 0.7), (255, 230, 240), rng.uniform(0.4, 0.9))
    C.fill(C.ellipse(sx, sy, sr, sr) * (Y < HZ - 3), (255, 236, 170))
    # far dunes (two hazy ranges), pyramids and a sun temple
    xs = np.arange(FW * S) / S
    for k, (top, col) in enumerate([(HZ - 7, (200, 96, 70)), (HZ - 3, (160, 70, 60))]):
        prof = top + 3 * np.sin(xs / 41 + k * 2) + 2 * np.sin(xs / 13 + k)
        m = (Y > prof[None, :]).astype(float); C.fill(m, col)
        C.add(np.clip(m - np.roll(m, 3 * S // 3, axis=0), 0, 1), (60, 40, 20), 0.8)
    for cx, half, hh, col in [(92, 26, 30, (150, 66, 66)), (128, 15, 17, (170, 80, 70)), (318, 20, 22, (156, 70, 66))]:
        py = C.mask_poly([(cx - half, HZ - 2), (cx, HZ - 2 - hh), (cx + half, HZ - 2)]); C.fill(py, col)
        C.add(py * (X < cx), (70, 40, 10), 0.8)                          # the sunward face
    tm = np.zeros(C.rgb.shape[:2])
    for cx, hh in [(258, 30), (272, 24)]:   # two far obelisks before a low temple
        tm = np.maximum(tm, C.mask_poly([(cx - 2, HZ - 2), (cx - 1.5, HZ - hh), (cx, HZ - hh - 3), (cx + 1.5, HZ - hh), (cx + 2, HZ - 2)]))
    tm = np.maximum(tm, C.mask_poly([(240, HZ - 2), (242, HZ - 8), (290, HZ - 8), (292, HZ - 2)]))
    C.fill(tm, (150, 68, 66))
    # the lake: the sky mirrored (darkened, bluer), the sun's road, a lit far shore line
    lake = (Y >= HZ).astype(float)
    my = np.clip(2 * HZ - Y, 0, FH - 1)
    mir = C.rgb[(my * S).astype(int).clip(0, C.HS - 1), np.arange(C.WS)[None, :].repeat(C.HS, 0)]
    mir = mir * 0.72 + np.array([10, 6, 30]) * 0.28
    C.rgb = C.rgb * (1 - lake[..., None]) + mir * lake[..., None]
    road = np.exp(-((X - sx) / (5 + (Y - HZ) * 0.5)) ** 2) * lake
    rip = 0.75 + 0.25 * C.noise(9, 1.5, 17, 3)
    C.add(L.feather(road, 2) * rip, (110, 80, 40), 0.8)
    C.fill(np.clip(1 - np.abs(Y - HZ) / 0.8, 0, 1), (255, 210, 130), 0.8)
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
SUN_R = (210, 111, 10)     # where the picked render put the sun (1x)
HZ_R = 129                 # and the water line


def grade(a):
    """Pulled down from the render's blaze (the game's bloom and the oasis's own warm light add to it): highlights compressed
    above lum 150 except on the sun's disc, a touch more depth in the zenith."""
    P = L.Canvas(FW, FH); X, Y = P.X[::S, ::S], P.Y[::S, ::S]
    l = L.lum(a)[..., None]; disc = (np.hypot(X - SUN_R[0], Y - SUN_R[1]) < SUN_R[2] + 1)[..., None]
    k = np.where(l > 150, (150 + (l - 150) * 0.55) / np.maximum(l, 1), 1.0)
    b = a * k * (0.92 - 0.12 * np.clip((60 - Y) / 60, 0, 1))[..., None]
    green = ((b[..., 1] > b[..., 0] - 8) & (L.lum(b) > 120))[..., None]  # the render's pale suns lean green: push them warm
    b = np.where(green, b * 0.4 + np.array([250, 214, 150]) * 0.6, b)
    warm = a * 0.5 + np.array([255, 236, 186]) * 0.5                     # the disc stays white-gold (no green cast)
    return np.clip(np.where(disc, warm, b), 0, 255)


def glints(q):
    """4 frames: the sun's reflection breaks and re-forms (ripple rows brighten / dim in turn), a few sparkles on the lake."""
    h, w = q.shape[:2]; l = L.lum(q); yy, xx = np.mgrid[0:h, 0:w]
    col = (yy > HZ_R + 1) & (np.abs(xx - SUN_R[0]) < 6 + (yy - HZ_R) * 0.45) & (l > 120)
    rng = np.random.default_rng(3); sp = (yy > HZ_R + 3) & (rng.random((h, w)) < 0.004) & (np.abs(xx - SUN_R[0]) < 60)
    frames = []
    for f in range(4):
        o = np.zeros((h, w, 4))
        ph = np.random.default_rng(100 + f).random((h, 1)); seg = ((xx + (ph * 40).astype(int)) // (3 + (yy % 3))) % 3
        on = col & (seg == 0) & ((yy % 2) == (f % 2))
        o[on, :3] = np.clip(q[on] * 1.15 + 16, 0, 255); o[on, 3] = 255
        off = col & (seg == 2) & ((yy % 2) != (f % 2))
        o[off, :3] = q[off] * 0.8; o[off, 3] = 255
        s = sp & (((xx + yy) % 4) == f); o[s, :3] = (255, 230, 170); o[s, 3] = 255
        frames.append(Image.fromarray(o.astype(np.uint8)))
    return frames


def build(no_ase=False):
    hero = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    f1 = grade(L.down(hero, FW, FH))
    q, _ = L.to_pixels(f1, 40, dk=0.35, hi=8, hi_lum=180, lo=6, lo_lum=50)
    far = L.rgba(q); far.save(f'{SRC}/out_far.png'); gl = glints(q)
    L.composite_preview([(far, 0.04, 0.05, 0, False), (gl[0], 0.04, 0.05, 0, False)], f'{SRC}/preview.png', [(0, 70), (192, 70), (40, 0)])
    if not no_ase:
        L.build(f'vista_{ROOM}_far', [far]); L.build(f'vista_{ROOM}_glint', gl, ms=220)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' not in a and '--sweep' not in a: build(no_ase='--no-ase' in a)
