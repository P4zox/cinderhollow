#!/usr/bin/env python3
"""Sunken Cathedral backdrop v2 (bg pilot, docs/v17/bg_pilot.md).

  python3 art/gen_bg_cathedral_v2.py            build bg_cathedral_{far,mid} from the saved renders in art/bg_src/cathedral/
  python3 art/gen_bg_cathedral_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_cathedral_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  --no-ase                                       write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/env_bg.py; the old generator stays for rollback.
The rose window sits at far x=150, under the existing GFX_SUN.cathedral ray source (uv x 0.38 = 146 px, above the view).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa

B = 'cathedral'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#0e0c14'

# v1 ramps (env_bg.py N_AIR / N_LIGHT / N_GOLD) extended upward; plus a few muted stained-glass hues
AIR = ['0a0b14', '0e1019', '12151f', '171b27', '1d222f', '232937', '2a3140', '32394a', '3b4356', '434c62', '4c566e', '56607a', '606b86', '6c7894', '7884a0']
LIGHT = ['4c5670', '62708c', '7e8eaa', 'a0b0c8', 'c6d2e2', 'e6eef6']
GOLD = ['3a2e1c', '5a4626', '7e6230', 'a8843e', 'd0aa56']
GLASS = ['2e4a7a', '6a2a3a']
FAR_PAL = [hexc(c) for c in AIR + LIGHT + GOLD + GLASS]
SIL = ['0b0c14', '10121c', '151824', '1b1f2d', '222737', '2a3042', '343b50']
RIM = ['2e3850', '44527a', '5e6e96']
MID_PAL = [hexc(c) for c in SIL + RIM + GOLD[:4]]

PROMPT_FAR = ('pixel art, dark fantasy, interior of a vast flooded gothic cathedral at night, a great rose window with muted stained glass '
              'above three tall lancet windows, cold pale moonlight streaming in shafts, clustered stone piers and ribbed vaults, a shattered '
              'lancet window, still black water covering the nave floor with reflections, broken pews half sunk, side-scroller game background, '
              'muted desaturated slate blue palette with faint gold, atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, gothic cathedral nave arcade, pointed stone arches on clustered pillars with carved capitals, '
              'hanging bronze censers on long chains, broken wooden pews in water, isolated on a flat dark background, side-scroller game '
              'background layer, dark slate blue stone with cold moonlit rim light, detailed')

ROSE = (150, 44, 27)       # x, y, radius


def lancet(G, cx, half, apex, bot, glass, frame='4a5470', mull=True, panes=None, rng=None):
    spring = apex + half * 1.6
    G.fill(G.mask_poly(arch_pts(cx, half + 2, spring, apex - 2, bot + 2)), hexc(frame))
    G.fill(G.mask_poly(arch_pts(cx, half, spring, apex, bot)), glass)
    if mull:   # a central mullion and transoms (lead lines)
        G.fill(G.mask_lines([(cx, apex + 3, cx, bot, 0.9)]), hexc('2a3140'))
        for y in np.arange(spring + 8, bot, 13):
            G.fill(G.mask_lines([(cx - half, y, cx + half, y, 0.8)]), hexc('2a3140'))
    if panes is not None and rng is not None:
        for (c, n) in panes:
            for _ in range(n):
                py = rng.uniform(spring, bot - 6); px = cx + (rng.choice([-1, 1])) * half * 0.5
                G.fill(G.mask_poly([(px - half * 0.4, py), (px + half * 0.4, py), (px + half * 0.4, py + 5), (px - half * 0.4, py + 5)]), hexc(c), 0.75)


def guide_far():
    rng = np.random.default_rng(5)
    G = Guide(hexc('12151f'))
    nz = tile_noise(WS, HS, 96, 48, 51); nz2 = tile_noise(WS, HS, 24, 12, 52, octaves=2)
    rx, ry, rr = ROSE
    lit = np.exp(-(G.wdx(rx + 30) / 170) ** 2)
    # nave air and the far wall: a vertical value ramp, lighter where the moonlight falls
    v = 0.30 + 0.30 * lit + 0.12 * (nz - 0.5)
    v *= 0.6 + 0.4 * smooth(0, 90, G.Y)
    G.rgb = lerp(hexc('10131c'), hexc('5a6584'), np.clip(v, 0, 1)[..., None])
    # ashlar on the wall
    for y in range(8, 168, 9):
        G.fill(G.mask_lines([(x, y, x + 20, y, 0.6) for x in range(0, W, 22)]), hexc('1a1e2a'), 0.35)
    # bays: piers at irregular spacing, pointed vault ribs between them
    piers = [(62, 16), (240, 18), (382, 14), (470, 12)]
    for i, (px, pw) in enumerate(piers):
        nxt = piers[(i + 1) % len(piers)][0] + (W if i == len(piers) - 1 else 0)
        mid = (px + nxt) / 2; half = (nxt - px) / 2
        rib = np.clip(G.mask_poly(arch_pts(mid, half + 1, 30, -18, 31, n=30)) - G.mask_poly(arch_pts(mid, half - 3, 31, -13, 40, n=30)), 0, 1)
        G.fill(rib, hexc('3a4258'))
    for (px, pw) in piers:   # clustered shafts: a lit edge facing the rose window, dark on the far side
        m = G.mask_poly([(px - pw / 2, 0), (px + pw / 2, 0), (px + pw / 2 + 1, 170), (px - pw / 2 - 1, 170)])
        G.fill(m, hexc('262c3c'))
        for k in (-pw / 4, pw / 4):
            G.fill(G.mask_lines([(px + k, 0, px + k, 170, 1.0)]), hexc('1a1e2a'))
        face = np.sign(G.wdx(px)) == (1 if G.wdx(rx)[0, int(px * S) % WS] < 0 else -1)
        G.fill(m * face * (np.abs(G.wdx(px)) > pw / 2 - 2), hexc('6a7898'), 0.8)
        G.fill(G.mask_poly([(px - pw / 2 - 3, 26), (px + pw / 2 + 3, 26), (px + pw / 2 + 1, 31), (px - pw / 2 - 1, 31)]), hexc('7e6230'))  # capital
    # --- focal: the rose window over a triple lancet (bay 62..240)
    G.glow(rx, ry + 50, 120, 120, hexc('3a4a70'), 0.8, 1.6)
    d = np.sqrt(G.wdx(rx) ** 2 + (G.Y - ry) ** 2); ang = np.arctan2(G.Y - ry, G.wdx(rx))
    G.fill((d < rr + 4).astype(float), hexc('4a5470'))
    glass = lerp(hexc('a0b0c8'), hexc('e6eef6'), np.clip(1 - d / rr, 0, 1)[..., None] ** 0.7)
    G.fill_img((d < rr).astype(float), glass)
    seg = (np.floor((ang + math.pi) / (2 * math.pi) * 12) % 12)
    tint = np.where((seg % 4 == 0)[..., None], hexc('2e4a7a'), np.where((seg % 4 == 2)[..., None], hexc('6a2a3a'), hexc('3a6a6e')))
    ringm = ((d > rr * 0.45) & (d < rr * 0.92)).astype(float) * ((seg % 2) == 0)
    G.fill_img(ringm, tint, 0.55)
    spokes = (np.abs(((ang + math.pi) / (2 * math.pi) * 12) % 1 - 0.5) > 0.44) & (d < rr) & (d > rr * 0.2)
    G.fill(spokes.astype(float), hexc('2a3140'))
    for k in range(12):   # foils: small circles on the outer ring
        a = k / 12 * 2 * math.pi + math.pi / 12
        G.fill(np.clip(G.mask_ellipse(rx + math.cos(a) * rr * 0.72, ry + math.sin(a) * rr * 0.72, 3.4, 3.4) - G.mask_ellipse(rx + math.cos(a) * rr * 0.72, ry + math.sin(a) * rr * 0.72, 2.4, 2.4), 0, 1), hexc('2a3140'))
    for r_ in (rr * 0.2, rr * 0.92):
        G.fill(((d > r_ - 0.6) & (d < r_ + 0.6)).astype(float), hexc('2a3140'))
    G.fill((d < rr * 0.16).astype(float), hexc('d0aa56'))
    for (cx, half, apex) in ((128, 6.5, 86), (150, 7.5, 80), (172, 6.5, 86)):
        lancet(G, cx, half, apex, 150, lerp(hexc('a0b0c8'), hexc('e6eef6'), 0.5), panes=[('2e4a7a', 2), ('6a2a3a', 1)], rng=rng)
    G.fill(G.mask_lines([(110, 152, 190, 152, 2.0)]), hexc('7e6230'))     # gilded sill
    # bay 240..382: one tall lancet, its tracery shattered (a ragged dark hole in the upper glass)
    lancet(G, 312, 12, 40, 152, hexc('8090ae'))
    hole = G.mask_poly([(304, 60), (310, 52), (318, 58), (322, 72), (316, 86), (306, 80), (302, 70)], blur=0.4)
    G.fill(hole, hexc('1a2030'))
    # bay 382..470: two narrow, dimmer lancets
    for cx in (414, 438):
        lancet(G, cx, 5, 72, 140, hexc('6a7898'), mull=False)
    # bay 470..62 (over the seam): dark, a chandelier ring on chains
    G.fill(G.mask_lines([(10, 0, 10, 54, 0.8), (2, 34, 10, 0, 0.6), (18, 34, 10, 0, 0.6)]), hexc('2a3040'))
    G.fill(np.clip(G.mask_ellipse(10, 58, 14, 4) - G.mask_ellipse(10, 57, 12, 2.5), 0, 1), hexc('7e6230'))
    for k in range(5):
        G.fill(G.mask_lines([(0 + k * 5, 52, 0 + k * 5, 55, 0.8)]), hexc('a8843e'))
    # moonlight: shafts from the windows falling down-right to the water (soft, additive)
    for (x0, w0, k) in ((rx, 22, 0.5), (150, 16, 0.35), (312, 12, 0.3), (426, 8, 0.15)):
        y0 = ry if x0 == rx and w0 == 22 else 90
        sh_ = G.mask_poly([(x0 - w0 / 2, y0), (x0 + w0 / 2, y0), (x0 + w0 / 2 + 46, 172), (x0 - w0 / 2 + 46 - w0 * 0.3, 172)], blur=3)
        G.add(sh_ * (1 - 0.5 * smooth(y0, 172, G.Y)), hexc('7a8ab0'), k)
    # the flooded floor: black water with window reflections and ripple glints, sunken pews
    WL = 170
    water = (G.Y >= WL).astype(float)
    refl = np.zeros_like(G.X)
    for (cx, w, k) in ((150, 30, 1.0), (128, 8, 0.6), (172, 8, 0.6), (312, 14, 0.6), (414, 6, 0.35), (438, 6, 0.35)):
        refl += k * np.exp(-(G.wdx(cx) / w) ** 2)
    rip = (np.sin(G.Y * 2.2 + nz2 * 6) > 0.6).astype(float)
    wcol = lerp(hexc('0c0f18'), hexc('3a4660'), np.clip(refl * (0.4 + 0.6 * rip) * (1 - 0.5 * smooth(WL, 216, G.Y)), 0, 1)[..., None])
    G.fill_img(water, wcol)
    G.fill(G.mask_lines([(0, WL, W, WL, 0.8)]), hexc('5a6584'), 0.8)
    for (px, pw, tilt) in ((40, 26, 2), (100, 22, -1.5), (214, 30, 1.5), (280, 18, -2), (356, 24, 1), (462, 20, -1)):   # pew backs
        G.fill(G.mask_lines([(px - pw / 2, WL - 3 + tilt, px + pw / 2, WL - 3 - tilt, 2.2)]), hexc('2a2420'))
        G.fill(G.mask_lines([(px - pw / 2 + 2, WL - 3 + tilt, px - pw / 2 + 2, WL + 1, 1.4), (px + pw / 2 - 2, WL - 3 - tilt, px + pw / 2 - 2, WL + 1, 1.4)]), hexc('2a2420'))
        G.fill(G.mask_lines([(px - pw / 2, WL - 4 + tilt, px + pw / 2, WL - 4 - tilt, 0.7)]), hexc('6a5a48'), 0.8)
    return G


def guide_mid():
    rng = np.random.default_rng(9)
    G = Guide(hexc('2a2e3a'), alpha=True)
    stone = hexc('4a5268'); lit = hexc('8a98b8')
    def pier(x, w, top, cap='foliate'):
        m = G.mask_poly([(x - w / 2, top), (x + w / 2, top), (x + w / 2 + 1, 204), (x - w / 2 - 1, 204)])
        G.fill(m, stone)
        for k in np.linspace(-w / 2 + 3, w / 2 - 3, 3):   # clustered shafts
            G.fill(G.mask_lines([(x + k, top, x + k, 204, 1.0)]), hexc('2a3042'))
        G.fill(m * (G.wdx(x) < -w / 2 + 2.5), lit, 0.7)
        base = G.mask_poly([(x - w / 2 - 3, 194), (x + w / 2 + 3, 194), (x + w / 2 + 3, 204), (x - w / 2 - 3, 204)])
        G.fill(base, hexc('3a4256'))
        if cap == 'foliate':
            G.fill(G.mask_poly([(x - w / 2 - 6, top - 7), (x + w / 2 + 6, top - 7), (x + w / 2 + 1, top + 2), (x - w / 2 - 1, top + 2)]), hexc('5a6278'))
            for k in np.arange(x - w / 2 - 4, x + w / 2 + 5, 3.5):
                G.fill(G.mask_ellipse(k, top - 1, 1.6, 2.2), hexc('7e6230'))
        elif cap == 'plain':
            G.fill(G.mask_poly([(x - w / 2 - 3, top - 4), (x + w / 2 + 3, top - 4), (x + w / 2 + 1, top + 1), (x - w / 2 - 1, top + 1)]), hexc('5a6278'))
        elif cap == 'broken':
            G.fill(G.mask_poly([(x - w / 2, top), (x - w / 2 + 3, top - 6), (x, top - 2), (x + 3, top - 9), (x + w / 2, top - 3), (x + w / 2, top)]), stone)
    def arch(x0, x1, spring, rise_k, thick, broken=None):
        cx, half = (x0 + x1) / 2, (x1 - x0) / 2; apex = spring - half * rise_k
        outer = arch_pts(cx, half + thick, spring, apex - thick * 1.1, spring + 1, n=40)
        inner = arch_pts(cx, half, spring + 0.5, apex, spring + 40, n=40)
        ring = np.clip(G.mask_poly(outer) - G.mask_poly(inner), 0, 1)
        if broken is not None:
            jag = broken + 5 * (tile_noise(WS, HS, 6, 6, 61, 1) - 0.5); ring = ring * (G.X < jag)
        G.fill(ring, stone)
        mould = np.clip(G.mask_poly(arch_pts(cx, half + 2.2, spring, apex - 2.2, spring + 1, n=40)) - G.mask_poly(inner), 0, 1)
        G.fill(mould * (ring > 0.5), lit, 0.75)                                      # moulded intrados catching moonlight
        G.fill(np.clip(G.mask_poly(arch_pts(cx, half + thick - 1.5, spring, apex - thick * 1.1 + 1.5, spring + 1, n=40)) - G.mask_poly(arch_pts(cx, half + thick - 3, spring, apex - thick * 1.1 + 3, spring + 1, n=40)), 0, 1) * (ring > 0.5), hexc('2a3042'), 0.8)
        return cx, apex
    # irregular arcade: wide arch, narrower arch, a collapsed bay, an arch over the seam
    pier(30, 20, 98, 'foliate'); pier(172, 16, 104, 'plain'); pier(292, 22, 98, 'foliate'); pier(426, 16, 98, 'plain'); pier(368, 14, 128, 'broken')
    c1 = arch(40, 162, 98, 1.05, 11); c2 = arch(180, 281, 104, 0.95, 10)
    arch(303, 420, 98, 1.05, 11, broken=338)                                       # snapped: only the springer stub on pier 292
    c4 = arch(434, 512 + 20, 98, 1.05, 11)                                      # spans the seam onto pier 30 (=542)
    # fallen voussoirs in the water below the broken bay
    for (bx, by, r) in ((346, 197, 5), (386, 199, 4), (400, 197, 5)):
        pts = [(bx + r * 1.4 * math.cos(a) + rng.uniform(-1, 1), by + r * math.sin(a) * 0.8) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
        G.fill(G.mask_poly(pts), hexc('3a4256')); G.fill(G.mask_poly([(x, min(y, by - 1)) for x, y in pts]), lit, 0.5)
    # censers on chains from the arch crowns (different lengths), and a broken chain
    for (cx, apex), ln in ((c1, 52), (c2, 30), (c4, 64)):
        top = 0 if apex < 4 else apex - 6
        y1 = apex + ln
        G.fill(G.mask_lines([(cx, top, cx, y1, 0.8)]), hexc('4a4a50'))
        G.fill(G.mask_poly([(cx - 4, y1), (cx + 4, y1), (cx + 5, y1 + 4), (cx + 3, y1 + 8), (cx - 3, y1 + 8), (cx - 5, y1 + 4)]), hexc('7e6230'))
        G.fill(G.mask_poly([(cx - 3, y1 + 1), (cx - 1, y1 + 1), (cx - 2, y1 + 7)]), hexc('d0aa56'), 0.8)
        G.fill(G.mask_lines([(cx - 4.5, y1 + 4, cx + 4.5, y1 + 4, 0.7)]), hexc('3a2e1c'))
    G.fill(G.mask_lines([(338 + 10, 0, 350, 46, 0.8)]), hexc('4a4a50'))              # chain hanging free over the collapse
    # broken pews jutting from the water (near, larger than the far ones), water line strip
    for (px, pw, tilt) in ((96, 34, 3), (236, 28, -4), (470, 30, 2.5)):
        G.fill(G.mask_lines([(px - pw / 2, 196 + tilt, px + pw / 2, 196 - tilt, 3.0)]), hexc('2a2420'))
        G.fill(G.mask_lines([(px - pw / 2, 194.5 + tilt, px + pw / 2, 194.5 - tilt, 0.9)]), hexc('6a5a48'))
        for k in (-pw / 2 + 3, pw / 2 - 3):
            G.fill(G.mask_lines([(px + k, 196, px + k, 205, 1.6)]), hexc('2a2420'))
    G.fill((G.Y > 203 + 1.5 * np.sin(G.X * 0.4)).astype(float), hexc('1a1e2a'))
    G.fill(G.mask_lines([(0, 203, W, 203, 0.7)]), hexc('5e6e96'), 0.6)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image()).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=3, denoise=0.78, cn=0.45, cn_end=0.6, pix=0.6, guide_blur=1.3),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.72, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=1.0, seam_band=96),
}


def do_render():
    times = {}
    for layer, kw in RENDER.items():
        times[layer] = round(render_layer(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


WL = 170   # water line (1x)


def far_post(a, stage):
    """'hi' (3x): the model drops the guide's water, so the drowned floor is built here: below the water line, a rippled,
    darkened, blue-shifted mirror of the nave (windows and shafts reflect as broken vertical glints), a lit edge on the line."""
    if stage != 'hi': return a
    h, w = a.shape[:2]; wl = WL * S; out = a.copy()
    nz = tile_noise(w, h, 48, 6, 77, octaves=2)
    for y in range(wl, h):
        d = y - wl
        sy = int(np.clip(wl - 1 - d * 1.1, 0, h - 1))
        xs = (np.arange(w) + (2.5 + d * 0.06) * np.sin(y * 0.55 + nz[y] * 9)).astype(int) % w
        row = a[sy, xs] * (0.42 - 0.18 * d / (h - wl))
        row = row * np.array([0.85, 0.95, 1.15])
        band = (np.sin(y * 0.9 + nz[y] * 5) > 0.55)          # horizontal ripple bands catch more of the reflection
        row = np.where(band[:, None], row * 1.45, row)
        out[y] = np.clip(row + np.array([6, 8, 14]), 0, 255)
    out[wl:wl + 2] = np.clip(a[wl - 4:wl - 2] * 0.5 + np.array([60, 70, 95]), 0, 255)
    return out


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=4, grade_kw=dict(black=8, white=240, gamma=1.1, sat=0.75), post=far_post, dk=0.35)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=3,
                                  grade_kw=dict(black=10, white=330, gamma=0.85, sat=0.7), rim_col=hexc('44527a'))
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
