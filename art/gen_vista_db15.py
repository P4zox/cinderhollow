#!/usr/bin/env python3
"""DB15 Pearl Lagoon: painted vista (agent V2, docs/v17/vista_v2.md).

"Light comes down here from somewhere no one has found" (lore sa_5). Beyond the grotto shelf a vast drowned sea-cave: its far
wall opens in a towering natural arch full of pale pearl light with no source anyone can see, shafts of it falling through
the cave's air, still water holding the arch upside down, the half-sunk arches and a stair of an older barrow going down into
the lagoon, stalactites and hanging roots overhead. The room's own flat lagoon backdrop (xsa_lagoon) gives way to it.

Planes: `far` (one painting), `glint` (4 frames: pearl glints and ripples of light on the water). fx: caustic light wavering
on the cave roof, the shafts breathing, motes.

  python3 art/gen_vista_db15.py [--guide | --sweep far 1,2 | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v2lib as L
from bgv2lib import smooth, lerp, S

ROOM = 'db15'
SRC = os.path.join(HERE, 'bg_src', 'vista_' + ROOM); os.makedirs(SRC, exist_ok=True)
FW, FH = 400, 240
ARCH = (236, 150, 34, 104)      # centre x, water line y, half width, height
WL = 150

PROMPT = ('pixel art, inside a vast dark drowned sea cave looking out through a rugged natural rock arch, through the cave mouth a '
          'pale misty sea stretches to a far horizon with tall distant sea stacks fading in luminous pearl haze, soft sourceless '
          'light, god rays slanting into the cave, the inner edges of the rock arch lit, still dark teal water in the cave reflecting '
          'the opening in broken ripples, stalactites and hanging roots, mysterious, serene, beautiful, deep teal and turquoise '
          'palette with pearl light, side-scroller game background, highly detailed')
RENDER = dict(far=dict(denoise=0.8, cn=0.35, cn_end=0.6, pix=0.4))


def paint_far():
    C = L.Canvas(FW, FH); X, Y = C.X, C.Y; ax, wl, ah, aht = ARCH
    C.rgb = C.vgrad([(0, (6, 20, 24)), (80, (14, 44, 48)), (WL, (30, 80, 82)), (FH, (6, 22, 26))])
    nz = C.noise(18, 12, 3, 4)
    # the far wall's rock (mottled) and the arch opening full of light
    rock = (Y < wl).astype(float)
    C.rgb = C.rgb * (1 - rock[..., None] * 0.2) + rock[..., None] * (np.stack([nz * 30, nz * 50, nz * 50], -1))
    # a rugged cave mouth: its outline wanders (two octaves of noise on the radius), wider at the waterline
    rng0 = np.random.default_rng(21); pts = []
    for t in np.linspace(0, math.pi, 40):
        r = 1 + 0.05 * math.sin(t * 7 + 1) + 0.03 * math.sin(t * 17 + 2) + rng0.uniform(-0.02, 0.02)
        pts.append((ax - ah * 1.15 * math.cos(t) * r, wl - aht * math.sin(t) ** 0.55 * r))
    arch = C.mask_poly([(ax - ah * 1.3, wl)] + pts + [(ax + ah * 1.3, wl)])
    # seen through it: a pale sea under luminous mist to a far horizon, sea stacks fading into the haze; the light has no
    # visible source (a brighter band of mist high in the opening). Brightest value kept near 215, not white.
    hz = wl - 26
    view = C.vgrad([(wl - aht, (96, 158, 160)), (hz - 30, (150, 204, 198)), (hz - 2, (196, 228, 218)), (hz, (206, 232, 222)),
                    (hz + 1, (150, 200, 196)), (wl, (176, 214, 206))])
    view += (C.radial(ax + 6, hz - 40, ah * 1.4, 22, 1.5)[..., None] * np.array([20, 18, 14]))
    C.rgb = C.rgb * (1 - arch[..., None]) + view * arch[..., None]
    for sx_, sw, sh_, col in [(ax - 22, 5, 30, (118, 168, 168)), (ax - 14, 3, 18, (130, 180, 178)), (ax + 20, 7, 24, (124, 174, 172)),
                              (ax + 30, 3, 12, (140, 188, 184)), (ax + 2, 14, 5, (150, 196, 192))]:
        stack = C.mask_poly([(sx_ - sw, hz + 1), (sx_ - sw * 0.7, hz - sh_ * 0.6), (sx_ - sw * 0.2, hz - sh_), (sx_ + sw * 0.5, hz - sh_ * 0.9),
                             (sx_ + sw * 0.8, hz - sh_ * 0.4), (sx_ + sw, hz + 1)]) * arch
        C.fill(stack, col); C.fill(stack * (X < sx_ - sw * 0.3), np.array(col) + 18, 0.6)
        refl = C.mask_poly([(sx_ - sw, hz + 1), (sx_ + sw, hz + 1), (sx_ + sw * 0.6, hz + 1 + sh_ * 0.35), (sx_ - sw * 0.6, hz + 1 + sh_ * 0.35)]) * arch
        C.fill(refl, np.array(col) - 10, 0.5)
    # the mouth's inner edges catch the light: a lit band of rock just outside the opening, rough
    rim = np.clip(L.dilate(arch, 5) - arch, 0, 1) * (C.noise(2, 3, 31, 2) > 0.35)
    C.fill(rim * (Y < wl), (70, 130, 126), 0.9)
    rim2 = np.clip(L.dilate(arch, 2) - arch, 0, 1)
    C.fill(rim2 * (Y < wl), (120, 180, 170), 0.8)
    C.add(C.radial(ax, wl - aht * 0.4, ah * 3.2, aht * 1.3, 1.6) * (1 - arch), (40, 90, 84), 1.0)   # light spilling into the cave
    # shafts falling from the arch's top and from cracks in the roof, leaning right
    for k, (x0, wd, al) in enumerate([(ax - 20, 8, 0.35), (ax - 4, 5, 0.3), (ax + 14, 6, 0.25)]):   # god-rays out of the mouth, down into the cave
        xr = X - (x0 - (Y - (wl - aht)) * 0.35); sh = np.clip(1 - np.abs(xr) / wd, 0, 1) * (Y < wl) * (Y > wl - aht * 0.8) * (1 - arch)
        C.add(sh, (80, 140, 130), al)
    # ceiling with stalactites
    ceil = (Y < 20 + 6 * np.sin(X / 23) + 4 * np.sin(X / 7)).astype(float)
    rng = np.random.default_rng(6)
    for _ in range(26):
        x = rng.uniform(0, FW); ln = rng.uniform(10, 40); wd = rng.uniform(2, 6)
        ceil = np.maximum(ceil, C.mask_poly([(x - wd, 0), (x + wd, 0), (x + 0.5, 18 + ln), (x - 0.5, 18 + ln)]))
    C.fill(ceil, (8, 24, 28)); C.add(ceil * np.clip((Y - 10) / 40, 0, 1) * np.exp(-((X - ax) / 140) ** 2), (30, 70, 64), 0.8)
    # the sunken barrow: arches and pillars half in the water, mid distance left; a stair descending
    for cx, hh in [(60, 60), (100, 70), (140, 56)]:
        p = C.mask_poly([(cx - 5, wl + 2), (cx - 5, wl - hh), (cx + 5, wl - hh), (cx + 5, wl + 2)]); C.fill(p, (20, 52, 56))
        C.add(p * (X > cx + 2), (40, 90, 84), 0.6)
    for a0, a1, top in [(60, 100, 60), (100, 140, 70)]:
        cx = (a0 + a1) / 2; r = (a1 - a0) / 2
        ring = (np.abs(np.sqrt((X - cx) ** 2 + ((Y - (wl - top + 6)) * 1.0) ** 2) - r) < 4) & (Y < wl - top + 6)
        C.fill(ring.astype(float), (20, 52, 56))
    for i in range(7):
        st = C.mask_poly([(160 + i * 6, wl - 30 + i * 4), (200, wl - 30 + i * 4), (200, wl - 26 + i * 4), (160 + i * 6, wl - 26 + i * 4)])
        C.fill(st, (28, 66, 70)); C.add(st * (Y < wl - 29 + i * 4), (60, 110, 104), 0.7)
    # the water: mirror of everything above, darker, with the arch's light laid on it
    water = (Y >= wl).astype(float)
    my = np.clip(2 * wl - Y, 0, FH - 1)
    mir = C.rgb[(my * S).astype(int).clip(0, C.HS - 1), np.arange(C.WS)[None, :].repeat(C.HS, 0)] * 0.6 + np.array([4, 14, 18]) * 0.4
    C.rgb = C.rgb * (1 - water[..., None]) + mir * water[..., None]
    C.fill(np.clip(1 - np.abs(Y - wl) / 0.8, 0, 1), (190, 240, 230), 0.6)
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
PICK = dict(far=('c', 14))   # (the first pass used ('b', 6): a flat bright slab in the mouth, replaced after the lead review)
ARCH_R = (240, 108)        # the opening's light, as rendered (1x)
WL_R = 150                 # the water line, as rendered


def clean(hero):
    """(The first pick, b6, had letter-like marks on an islet that were filled from around here; c14 needs nothing.)"""
    return hero


def grade(a):
    """The room's lamps light the backdrop through a per-tile shadow mask, so a mid-bright painting shows their 16 px shadow
    boxes. The light of the opening is therefore pushed past the emissive knee (it shows as painted, lamps or not) and the
    cave around it is held darker, where the lamps' boxes stay faint."""
    l = L.lum(a)[..., None]
    t = np.clip((l - 120) / 50, 0, 1)
    mx = a.max(-1, keepdims=True)
    tgt = 188 + 16 * np.clip((l - 150) / 70, 0, 1)                  # the opening's own shading kept; its brightest ~204: short of white and of the bloom, so its stacks read standing too
    hi = a * np.clip(tgt / np.maximum(mx, 1), 0.9, 1.6)
    b = a * 0.82 * (1 - t) + hi * t
    # inside the opening: more local contrast, so the sea stacks and the horizon read through the haze and the room light
    blur = np.stack([L.gblur(b[..., i], 3) for i in range(3)], -1)
    inner = np.clip((L.gblur(L.lum(a), 5) - 150) / 30, 0, 1)[..., None]       # well inside the opening only: no halo on its rim
    b = b + (b - blur) * 1.3 * inner
    # cross the emissive knee (~214) in a narrow step, not a wide dithered ring
    mx = b.max(-1, keepdims=True)
    push = np.where(mx > 214, np.maximum(mx, 232) / np.maximum(mx, 1), np.minimum(mx, 196) / np.maximum(mx, 1))
    b = np.where((mx > 196) & (mx < 232), b * push, b)
    # the water: the mirrored opening breaks into ripples (rows shifted side to side, fading with depth) instead of a clean
    # column with straight sides
    h, w = b.shape[:2]; out = b.copy()
    for y in range(WL_R + 1, h):
        d = y - WL_R; sh = int(round(math.sin(d * 0.9) * (1 + d * 0.06) + math.sin(d * 0.37 + 1) * 1.5))
        row = np.roll(b[y], sh, axis=0)
        out[y] = row * (1 - min(0.45, d * 0.006)) + np.array([6, 20, 24]) * min(0.45, d * 0.006)
    return np.clip(out, 0, 255)


def glints(q):
    """4 frames: ripples of the arch's light running across its reflection, and pearl glints on the dark water."""
    h, w = q.shape[:2]; l = L.lum(q); yy, xx = np.mgrid[0:h, 0:w]
    refl = (yy > WL_R + 1) & (l > 110)
    rng = np.random.default_rng(8); pearl = (yy > WL_R + 4) & (rng.random((h, w)) < 0.003)
    frames = []
    for f in range(4):
        o = np.zeros((h, w, 4))
        ph = np.random.default_rng(40 + f).random((h, 1)); seg = ((xx + (ph * 30).astype(int)) // (4 + (yy % 2))) % 3
        on = refl & (seg == 0) & (yy % 2 == f % 2); o[on, :3] = np.clip(q[on] * 1.15 + 14, 0, 255); o[on, 3] = 255
        off = refl & (seg == 1) & (yy % 2 != f % 2); o[off, :3] = q[off] * 0.82; o[off, 3] = 255
        p = pearl & ((xx + yy) % 4 == f); o[p, :3] = (220, 250, 240); o[p, 3] = 255
        frames.append(Image.fromarray(o.astype(np.uint8)))
    return frames


def build(no_ase=False):
    hero = clean(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float))
    f1 = grade(L.down(hero, FW, FH))
    q, _ = L.to_pixels(f1, 36, dk=0.35, hi=8, hi_lum=170, lo=6, lo_lum=30)
    far = L.rgba(q); far.save(f'{SRC}/out_far.png'); gl = glints(q)
    L.composite_preview([(far, 0.03, 0.1, 0, False), (gl[0], 0.03, 0.1, 0, False)], f'{SRC}/preview.png', [(0, 38), (192, 104), (7, 0)])
    if not no_ase: L.build(f'vista_{ROOM}_far', [far]); L.build(f'vista_{ROOM}_glint', gl, ms=240)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' not in a and '--sweep' not in a: build(no_ase='--no-ase' in a)
