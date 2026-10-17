#!/usr/bin/env python3
"""SP15 Lighthouse Balcony vista (agent V1, docs/v17/vista_v1.md): the storm over the open sea, a moon through the break.

  python3 art/gen_vista_sp15.py [--guide | --sweep <layer> 1,2,3 [--dn x --cn x --pix x --tag t] | --render] [--no-ase]
  (vista_v1_lib.cli; builds assets/vista_sp15_{far,mid,flash} from the saved renders in art/bg_src/vista_sp15/)

Lore (rc_2, the Keeper's Log): "When lightning takes the sea, for one breath I can see all the way to the edge of the world.
It is only more storm." The regular spire backdrop is a bruised violet storm over the cliffs and the hamlet; the balcony looks
west over open water: a break in the clouds with the moon laying a silver road on the swells, and on the horizon the storm
front, lit from inside when the lightning comes (a flash frame the fx fades in), while the lamp's beam turns over the sea.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v1_lib as L
import bgv2lib as V
from bgv2lib import lerp

ROOM = 'SP15'
SRC = os.path.join(HERE, 'bg_src', 'vista_sp15')
TINT = '#0a0d16'
FAR = dict(sheet='vista_sp15_far', w=408, h=224, fac=0.03, vfac=0.1, x=-4, dy=4)
MID = dict(sheet='vista_sp15_mid', w=408, h=224, fac=0.12, vfac=0.1, x=-4, dy=4)
HOR = 100
MOON = (124, 40)
STORM = 246   # the thunderhead's tower: left of the lighthouse, which hides the painting's right third

PROMPTS = {
    'far': ('pixel art, dark fantasy seascape at night seen from high on a sea cliff, a vast stormy open sea with long dark swells '
            'and whitecaps, a pale full moon in a clear patch of starry sky casting a glittering silver road across the waves, a '
            'colossal cumulonimbus thunderhead storm front with a flat anvil top on the far horizon, lit from inside by violet '
            'lightning, grey curtains of rain falling into the sea, a distant lone sea stack, empty sea, dramatic and lonely, '
            'highly detailed, slate blue, silver and deep teal palette'),
    'mid': ('pixel art, dark fantasy, tall jagged black sea stacks rising from a stormy sea at night, white foam and spray breaking at '
            'their feet, wet rock edges lit silver by the moon, storm clouds and a silver moon road on the waves behind, highly '
            'detailed, slate blue and silver palette'),
}
RENDER = {'far': dict(seed=1, dn=0.55, cn=0.6, cn_end=0.65, pix=0.5, tag='f'),
          'mid': dict(seed=1, dn=0.55, cn=0.6, cn_end=0.7, pix=0.55, tag='f')}


def sky(G):
    G.rgb = G.vgrad([(0, (18, 22, 36)), (60, (28, 34, 52)), (100, (40, 50, 68)), (HOR, (58, 70, 86))])
    nz = G.noise(46, 18, 4, 4); nz2 = G.noise(14, 6, 5, 3)
    # clear starry sky over the moon (upper left), a cloud bank thickening to the right and low over the sea
    bank = np.clip((G.X - 150) / 100, 0, 1) * 0.55 + np.clip((G.Y - 60) / 40, 0, 1) * 0.45 + np.clip((40 - G.X) / 60, 0, 1) * 0.4
    hole = np.clip(1 - bank * 1.6, 0, 1) * G.radial(MOON[0], MOON[1] - 10, 110, 80, 0.6)
    cloud = np.clip((nz * 0.75 + nz2 * 0.35 - 0.38) * 3.2 - hole * 2.6 + (bank - 0.5) * 0.8, 0, 1)
    # cloud bodies: dark undersides, silver-lit where they face the moon
    lit = np.clip(1 - np.sqrt(((G.X - MOON[0]) / 120) ** 2 + ((G.Y - MOON[1]) / 70) ** 2), 0, 1)
    under = np.clip((np.roll(cloud, -3 * L.S, axis=0) - cloud) * 3, 0, 1)
    body = lerp(np.array((22, 26, 40), float), np.array((70, 80, 100), float), (lit ** 1.5 * 0.9)[..., None])
    G.fill_img(cloud, body)
    edge = np.clip(cloud * (1 - cloud) * 4, 0, 1) * lit
    G.add(edge, (150, 160, 175), 0.9)
    G.add(np.clip(np.roll(cloud, 2 * L.S, axis=0) - cloud, 0, 1) * lit, (90, 100, 120), 0.6)
    # the clear sky in the break, a few stars, the moon and its halo
    G.fill(hole, (26, 38, 64), 0.5, cover=False)
    rng = np.random.default_rng(3)
    for _ in range(50):
        x, y = MOON[0] + rng.normal(0, 50), MOON[1] + rng.normal(-6, 22)
        G.fill(G.ellipse(x, y, 0.5, 0.5, 2) * hole, (210, 220, 240), rng.uniform(0.4, 1))
    G.glow(MOON[0], MOON[1], 44, 34, (60, 66, 80), 1.0, 1.8)
    G.fill(G.ellipse(*MOON, 9.5, 9.5), (232, 234, 226))
    G.add(G.ellipse(MOON[0] + 2, MOON[1] - 1, 3, 2.5) + G.ellipse(MOON[0] - 3, MOON[1] + 3, 2, 1.6), (-24, -22, -18), 1.0)
    # the storm front on the horizon (right): a cumulonimbus built of billows, its anvil spreading flat at the top, lit within
    rng = np.random.default_rng(8); m = np.zeros_like(G.X)
    for k in range(150):
        t = rng.random(); x = STORM - 95 + t * 300
        topy = HOR - 26 - 58 * math.exp(-((x - STORM) / 60) ** 2) - 10 * rng.random()
        y = topy + (HOR - topy) * rng.random() ** 1.6; r = rng.uniform(8, 16)
        m = np.maximum(m, G.ellipse(x, y, r * 1.3, r))
    for k in range(26):                                  # the anvil: flattened billows spreading at the top
        x = rng.uniform(STORM - 60, STORM + 140); y = rng.uniform(8, 18)
        m = np.maximum(m, G.ellipse(x, y, rng.uniform(14, 26), rng.uniform(4, 7)))
    m = np.clip(np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2 * L.S)), float) / 255 * 1.4, 0, 1)
    shade = np.clip(1 - np.abs(np.roll(m, -4 * L.S, axis=0) - m) * 0, 0, 1)
    storm = lerp(np.array((10, 12, 22), float), np.array((34, 38, 56), float), G.noise(12, 8, 9, 3)[..., None])
    G.fill_img(m, storm)
    top_lit = np.clip(m - np.roll(m, 4 * L.S, axis=0), 0, 1)
    G.add(top_lit, (50, 56, 72), 0.5)
    G.add(m * G.radial(STORM + 10, 56, 70, 36, 1.4) * (0.6 + 0.4 * G.noise(8, 6, 13, 2)), (54, 50, 92), 0.9)
    # rain veils: soft grey haze hanging from the cloud base to the sea (streaks rendered as cliffs, so no streaks)
    veil = np.clip((G.Y - (HOR - 34)) / 30, 0, 1) * (G.Y < HOR) * np.clip(1 - np.abs(G.X - STORM - 20) / 150, 0, 1) ** 0.7
    veil = veil * (0.6 + 0.4 * np.sin(G.X / 13 + G.Y / 30))
    G.fill(veil, (52, 60, 78), 0.75, cover=False)


def sea(G):
    below = np.clip((G.Y - HOR) * 3, 0, 1)
    G.fill_img(below, G.vgrad([(HOR, (40, 52, 66)), (HOR + 10, (22, 32, 44)), (224, (8, 13, 22))]))
    # swells: long horizontal crests, finer and denser toward the horizon, coarser near the viewer
    d = np.clip((G.Y - HOR) / (224 - HOR), 0, 1)
    nf = G.noise(10, 1.2, 21, 2); nn = G.noise(34, 3.5, 22, 3); nm = G.noise(20, 2.2, 23, 2)
    n = np.where(d < 0.35, lerp(nf, nm, d / 0.35), lerp(nm, nn, np.clip((d - 0.35) / 0.65, 0, 1)))
    crest = np.clip((n - 0.56) * 5, 0, 1) * below
    trough = np.clip((0.42 - n) * 4, 0, 1) * below
    G.add(trough, (-8, -10, -12), 1.0)
    G.add(crest, (22, 30, 38), 1.0)
    # the moon road: a glittering column widening toward the viewer
    w = 6 + (G.Y - HOR) * 0.5
    road = np.clip(1 - np.abs(G.X - MOON[0] - (G.Y - HOR) * 0.08) / w, 0, 1) ** 1.2 * below
    G.add(road * crest, (200, 206, 210), 1.0)
    G.add(road * 0.35, (60, 66, 76), 1.0)
    # whitecaps scattered under the storm
    nz = G.noise(3, 1, 31, 2)
    caps = np.clip((nz - 0.8) * 8, 0, 1) * crest * (G.X > STORM - 60)
    G.add(caps, (90, 100, 110), 1.0)
    # the storm's shadow on the water under the front
    G.add(below * np.clip((G.X - STORM + 40) / 80, 0, 1) * np.clip(1 - (G.Y - HOR) / 50, 0, 1), (-12, -14, -16), 1.0)
    # a distant lone stack
    G.fill(G.poly([(106, HOR + 1), (108, HOR - 12), (111, HOR - 17), (114, HOR - 13), (117, HOR - 5), (119, HOR + 1)]), (20, 26, 38))
    G.fill(G.poly([(122, HOR + 1), (123.5, HOR - 6), (126, HOR - 8), (128, HOR + 1)]), (24, 30, 42))


def guide_far():
    G = L.VG(FAR['w'], FAR['h']); sky(G); sea(G); return G


def guide_mid():
    G = guide_far(); G.a = np.zeros_like(G.X)
    rng = np.random.default_rng(5)
    def crag(x0, x1, base, h, seed, lean=0.0):
        pr = L.profile(int(x1 - x0) + 2, seed, 0, 1, cells=((9, 1.0), (4, 0.5), (2, 0.25)))
        pts = [(x0, base)]
        for k in range(int(x1 - x0) + 1):
            t = k / (x1 - x0); env = math.sin(t * math.pi) ** 0.5
            pts.append((x0 + k, base - h * env * (0.75 + 0.25 * (1 - abs(t - 0.5 + lean))) + 8 * pr[k] * env))
        return pts + [(x1, base)]
    m = np.zeros_like(G.X)
    for x0, x1, base, h, sd, ln in [(14, 70, 226, 56, 1, 0.15), (62, 90, 222, 26, 2, -0.1), (196, 250, 228, 30, 4, -0.2)]:
        m = np.maximum(m, G.poly(crag(x0, x1, base, h, sd, ln)))
    arch = G.poly([(30, 226), (32, 210), (38, 203), (44, 210), (46, 226)], blur=0.3)
    m = np.clip(m - arch, 0, 1)
    rock = lerp(np.array((10, 14, 22), float), np.array((28, 34, 46), float), G.noise(3, 8, 7, 3)[..., None])
    G.fill_img(m, rock)
    lit = np.clip(np.roll(m, 2 * L.S, axis=1) - m, 0, 1) * 0 + (np.roll(m, 2 * L.S, axis=0) < 0.5) * m
    G.add(lit, (110, 120, 136), 0.9)
    side = (np.roll(m, 2 * L.S, axis=1) < 0.5) * m
    G.add(side, (60, 66, 80), 0.6)

    return G


def guides():
    return {'far': guide_far(), 'mid': guide_mid()}


def flash_frame(far_hi):
    """The lightning frame: the storm front lit from inside, its edges silvered, the sea under it catching the light, and a
    crisp bolt from the cloud base to the sea; the fx crossfades it in for a breath."""
    a = far_hi.copy(); hh, ww = a.shape[:2]; S = L.S
    X = (np.arange(ww)[None, :] + 0.5) / S; Y = (np.arange(hh)[:, None] + 0.5) / S
    lum = a @ np.array([0.299, 0.587, 0.114])
    k = np.clip(1 - np.sqrt(((X - STORM) / 170) ** 2 + ((Y - 52) / 80) ** 2), 0, 1) ** 0.9 * (Y < HOR + 1)
    cloudy = np.clip(1 - np.sqrt(((X - MOON[0]) / 80) ** 2 + ((Y - MOON[1]) / 44) ** 2), 0, 1).__rsub__(1)
    k = k * cloudy
    a = a * (1 + 2.6 * k)[..., None] * np.array([1.0, 0.98, 1.12]) + (k ** 2)[..., None] * np.array([40, 36, 70])
    sea = np.clip(1 - np.sqrt(((X - STORM) / 170) ** 2 + ((Y - HOR - 14) / 26) ** 2), 0, 1) * (Y > HOR)
    a = a + (sea * np.clip((lum - 30) / 60, 0, 1))[..., None] * np.array([90, 96, 130])
    return np.clip(a, 0, 255)


def bolt(q, pal):
    rng = np.random.default_rng(42)
    P = np.array(pal, float); near = lambda c: P[np.argmin(((P - np.array(c, float)) ** 2).sum(1))]
    core, glow = near((240, 238, 255)), near((150, 146, 210))
    x, y = STORM + 16.0, HOR - 26.0; pts = []
    while y < HOR:
        pts.append((int(round(x)), int(y))); y += 1; x += rng.normal(0.25, 0.9) if rng.random() < 0.4 else 0.25
    for i, (px, py) in enumerate(pts):
        q[py, px] = core
        if 0 < px < q.shape[1] - 1:
            for dx in (-1, 1):
                if (q[py, px + dx] != core).any(): q[py, px + dx] = glow
    # one fork
    x, y = pts[len(pts) // 3]
    for i in range(14):
        x -= 1 if rng.random() < 0.6 else 0; y += 1; q[int(y), int(x)] = glow if i > 8 else core
    return q


def build(no_ase=False):
    far_hi = V.grade(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float), black=2, white=235, gamma=1.22, sat=1.05)
    fl_hi = flash_frame(far_hi)
    pal = L.kpal(V.box_down(far_hi, FAR['w'], FAR['h']), 36) + L.kpal(V.box_down(fl_hi, FAR['w'], FAR['h']), 10)
    pal += [(240, 238, 255), (150, 146, 210)]
    far = L.pixelize(far_hi, FAR['w'], FAR['h'], pal, dk=0.35)
    fl = bolt(L.pixelize(fl_hi, FAR['w'], FAR['h'], pal, dk=0.35), pal)
    # the flash layer only carries what lightning changes (alpha where it differs), drawn over the far layer
    diff = np.abs(fl - far).sum(2) > 0
    mid_hi = V.grade(np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float), black=4, white=270, gamma=0.95)
    al = np.asarray(Image.open(f'{SRC}/alpha_mid.png').convert('L').resize((MID['w'], MID['h']), Image.BOX), float) / 255 >= 0.5
    mpal = L.kpal(V.box_down(mid_hi, MID['w'], MID['h']), 14, mask=al)
    mid = np.where(al[..., None], L.pixelize(mid_hi, MID['w'], MID['h'], mpal, dk=0, alpha=al), 0)
    far_im, mid_im, fl_im = L.to_rgba(far), L.to_rgba(mid, al), L.to_rgba(fl, diff)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png'); fl_im.save(f'{SRC}/out_flash.png')
    full = far_im.copy(); full.alpha_composite(fl_im); full.save(f'{SRC}/out_far_flash.png')
    L.comp_preview(ROOM, [(FAR, far_im), (MID, mid_im)], TINT, f'{SRC}/preview.png')
    print('far colours', len(pal), 'mid colours', len(mpal))
    if not no_ase:
        L.ase('vista_sp15_far', [far_im]); L.ase('vista_sp15_mid', [mid_im]); L.ase('vista_sp15_flash', [fl_im])


if __name__ == '__main__':
    L.cli(sys.modules[__name__])
