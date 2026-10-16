#!/usr/bin/env python3
"""Necropolis of Vael backdrop v2 (bg rollout, agent B; docs/v17/bg_rollout_b.md, method in docs/v17/bg_pilot.md).

  python3 art/gen_bg_necropolis_v2.py            build bg_necropolis_{far,mid} from the saved renders in art/bg_src/necropolis/
  python3 art/gen_bg_necropolis_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_necropolis_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  python3 art/gen_bg_necropolis_v2.py --sweep far|mid 1,2,3   pass-1 seed sweep into $BG_SWEEP
  --no-ase                                        write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/necro_bg.py (kept for rollback). Necropolis has no
GFX_SUN entry. Far: the city of the dead in three planes under a night sky, the focal great bell-cathedral at x≈200.
Mid: an ossuary arcade with six different bays (no 256 period) and **no opaque band across the top** (v1 had ~25 px).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgv2b

B = 'necropolis'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#05060c'
FOCAL = 205

# v1 ramps (necro_bg.py SKY / P3 / P2 / P1 / WIN) extended upward in the same blue family, plus bone
SKY = ['04050a', '070910', '0b0f1c', '111829', '18223b', '20304f', '2a3f64', '344c74', '405a84', '4e6894', '627ca6']
PL = ['06070d', '0c0f1c', '0f152a', '141c36', '1b2742', '22304e', '2c3a5a', '384868']
WIN = ['1e3a6a', '3a70c0', '7fb4ee', 'cfe6ff']
BONE = ['5a5a68', '7a7884', 'a09ca4']
FAR_PAL = [hexc(c) for c in SKY + PL + WIN + BONE]
SIL = ['04040a', '07070e', '0b0b15', '11121e', '191a2a', '20223a', '282c48', '313656']
MID_PAL = [hexc(c) for c in SIL + ['3a4466', '4a5478'] + WIN[:3] + BONE[:2]]

PROMPT_FAR = ('pixel art, dark fantasy, a vast gothic city of the dead at night, a towering black cathedral with twin needle spires and a '
              'huge bell hanging in its open belfry, a great round window glowing with cold blue ghost fire, rows of mausoleums with domes '
              'and pointed roofs, obelisks and tall thin bone spires, cold blue mist rising between the tombs, a starry deep blue night sky, '
              'side-scroller game background, muted dark navy and slate blue palette with pale blue ghost-light windows, atmospheric '
              'depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, ruined gothic ossuary arcade, pointed stone arches on heavy piers, carved skulls lining the arches, '
              'niches with stacked skulls, hanging iron chains with small bells and blue ghost-fire lanterns, wrought iron railing between '
              'the piers, isolated on a flat grey background, side-scroller game background layer, dark blue-black stone with cold rim '
              'light, detailed')


# -------------------------------------------------------------------------------------------------- guides
def needle(G, x, base, w, h, col, lit=None, windows=0, rng=None, ribs=True):
    """A bone needle-spire: tapering tower with balconies (ribs), a pointed cap and a few ghost-lit slits."""
    pts = [(x - w / 2, base)]
    for t in np.linspace(0, 1, 18):
        hw = w / 2 * (1 - t) ** 0.7 + 0.3
        pts.append((x - hw, base - h * t))
    pts_r = [(2 * x - px, py) for px, py in reversed(pts)]
    poly = pts + pts_r
    G.fill(G.mask_poly(poly), col)
    if lit is not None:
        G.fill(G.mask_poly(pts + [(x, base - h), (x, base)]), lit, 0.5)
    if ribs:
        for k in range(1, int(h / 13)):
            yy = base - k * 13; t = k * 13 / h
            if t > 0.8: break
            hw = w / 2 * (1 - t) ** 0.7 + 1.2
            G.fill(G.mask_lines([(x - hw, yy, x + hw, yy, 1.0)]), col * 1.25)
    for k in range(windows):
        yy = base - h * rng.uniform(0.1, 0.65)
        G.fill(G.mask_lines([(x, yy, x, yy + 2.5, 1.0)]), hexc(WIN[1] if rng.random() < 0.7 else WIN[2]))


def guide_far():
    rng = np.random.default_rng(13)
    G = Guide(hexc('0b0f1c'))
    X, Y = G.X, G.Y
    nz = tile_noise(WS, HS, 96, 32, 61, 3)
    # night sky: blue-black at the top, a cold glow of haze rising from below the city
    G.rgb = lerp(hexc('070910'), hexc('2e4470'), (smooth(0, 200, Y) ** 1.4)[..., None])
    G.add(np.exp(-(G.wdx(FOCAL) / 160) ** 2) * smooth(40, 170, Y), hexc('18223b'), 0.8)
    cl = tile_noise(WS, HS, 128, 24, 62, 4)
    G.fill(smooth(0.55, 0.72, cl) * (1 - smooth(60, 110, Y)), hexc('1b2742'), 0.6)                  # thin night cloud
    for _ in range(110):
        sx, sy = rng.uniform(0, W), rng.uniform(0, 90)
        G.fill(G.mask_ellipse(sx, sy, 0.45, 0.45), hexc('a0b4d8'), rng.uniform(0.3, 0.9))
    # a pale waning moon low on the right, half veiled
    d = np.sqrt(G.wdx(372) ** 2 + (Y - 30) ** 2); d2 = np.sqrt(G.wdx(376) ** 2 + (Y - 28) ** 2)
    G.glow(372, 30, 40, 40, hexc('1e2c4c'), 0.8)
    G.fill(((d < 7) & (d2 > 6.2)).astype(float), hexc('b8c8e0'))
    # plane 3 (farthest, hazy): a skyline of needles, domes and towers of different heights
    P3, P3L = hexc('22304e'), hexc('2c3a5a')
    for i in range(30):
        x = (i + rng.uniform(0, 0.8)) * W / 30
        if abs(((x - FOCAL + W / 2) % W) - W / 2) < 46: continue
        kind = rng.random(); base = 150
        if kind < 0.55: needle(G, x, base, rng.uniform(5, 9), rng.uniform(40, 96), P3, P3L, 2, rng)
        elif kind < 0.8:
            r = rng.uniform(7, 12); top = base - rng.uniform(20, 40)
            G.fill(G.mask_poly([(x - r, base), (x - r, top), (x + r, top), (x + r, base)]), P3)
            G.fill(G.mask_ellipse(x, top, r, r * 0.9), P3); needle(G, x, top - r * 0.8, 2.5, 12, P3, ribs=False)
        else:
            w = rng.uniform(10, 18); top = base - rng.uniform(30, 60)
            G.fill(G.mask_poly([(x - w / 2, base), (x - w / 2, top), (x, top - w * 0.9), (x + w / 2, top), (x + w / 2, base)]), P3)
    G.fill((Y > 140).astype(float), hexc('22304e'))
    G.add(np.exp(-((Y - 146) / 12) ** 2) * (0.6 + 0.4 * nz), hexc('2a3f64'), 0.9)                 # mist band
    # --- focal: the great bell-cathedral (plane 2.5)
    fx = FOCAL; base = 168; C2, C2L = hexc('141c36'), hexc('2c3a5a')
    G.fill(G.mask_poly([(fx - 40, base), (fx - 40, 104), (fx, 78), (fx + 40, 104), (fx + 40, base)]), C2)       # nave front + gable
    G.fill(G.mask_poly([(fx - 40, 104), (fx, 78), (fx, 82), (fx - 36, 106)]), C2L, 0.7)                         # moonlit gable edge
    for sx in (-1, 1):   # twin needle towers
        needle(G, fx + sx * 34, base, 16, 150, C2, C2L if sx < 0 else None, 4, rng)
    # central belfry tower with an open pointed arch and the great bell
    G.fill(G.mask_poly([(fx - 13, 104), (fx - 13, 40), (fx, 24), (fx + 13, 40), (fx + 13, 104)]), C2)
    needle(G, fx, 30, 9, 36, C2, None, 0, rng, ribs=False)
    bel = arch_pts(fx, 8.5, 54, 40, 82)
    G.fill(G.mask_poly(bel), hexc('2a3f64')); G.glow(fx, 52, 14, 16, hexc('1e3a6a'), 0.8)
    G.fill(G.mask_lines([(fx, 41, fx, 52, 0.8)]), hexc('5a5a68'))
    G.fill(G.mask_poly([(fx - 2.5, 52), (fx + 2.5, 52), (fx + 4.5, 60), (fx + 7, 66), (fx - 7, 66), (fx - 4.5, 60)]), hexc('7a7884'))   # the bell
    G.fill(G.mask_poly([(fx - 2.5, 52), (fx - 0.5, 52), (fx - 4, 64), (fx - 6.5, 66), (fx - 4.5, 60)]), hexc('a09ca4'), 0.8)
    # the great pointed window of ghost fire (a tall lancet with tracery, not a round rose: a round window read as a clock face)
    win = G.mask_poly(arch_pts(fx, 11, 112, 92, 148))
    G.fill(G.mask_poly(arch_pts(fx, 13.5, 112, 89, 149)), hexc('3a4a70'))
    G.fill_img(win, lerp(hexc(WIN[1]), hexc(WIN[3]), (np.exp(-((Y - 122) / 18) ** 2) * np.exp(-(G.wdx(fx) / 9) ** 2))[..., None]))
    for k in (-5.5, 0, 5.5):
        G.fill(G.mask_lines([(fx + k, 104 + abs(k) * 0.6, fx + k, 148, 1.0)]), hexc('141c36'))
    for yy in (118, 130):
        G.fill(G.mask_lines([(fx - 11, yy, fx + 11, yy, 0.8)]), hexc('141c36'))
    G.fill(np.clip(G.mask_ellipse(fx, 101, 4.5, 4.5) - G.mask_ellipse(fx, 101, 3.4, 3.4), 0, 1), hexc('141c36'))
    G.glow(fx, 122, 46, 40, hexc('1e3a6a'), 0.7)
    door = arch_pts(fx, 8, 150, 136, base)
    G.fill(G.mask_poly(door), hexc('0c0f1c')); G.fill(G.mask_poly(arch_pts(fx, 5, 152, 141, base)), hexc(WIN[0]), 0.8)
    for wx in (fx - 24, fx + 24):
        G.fill(G.mask_poly(arch_pts(wx, 3, 128, 118, 146)), hexc(WIN[1]), 0.9)
    # plane 2: a row of varied mausolea along a terrace (domes, gables, a pyramid tomb, obelisks), a few lit doors
    P2, P2L = hexc('0f152a'), hexc('22304e')
    xs = [12, 44, 78, 112, 138, 262, 292, 330, 356, 392, 430, 470, 498]
    for i, x in enumerate(xs):
        k = i % 5; base = 186 + rng.uniform(-2, 2); w = rng.uniform(18, 28)
        if k == 0:     # domed tomb
            G.fill(G.mask_poly([(x - w / 2, base), (x - w / 2, base - 22), (x + w / 2, base - 22), (x + w / 2, base)]), P2)
            G.fill(G.mask_ellipse(x, base - 22, w / 2 - 2, w / 2.4), P2); needle(G, x, base - 22 - w / 2.4 + 1, 2, 9, P2, ribs=False)
            G.fill(G.mask_ellipse(x - w / 6, base - 26, w / 6, w / 6), P2L, 0.5)
        elif k == 1:   # gabled crypt with columns
            G.fill(G.mask_poly([(x - w / 2, base), (x - w / 2, base - 18), (x, base - 30), (x + w / 2, base - 18), (x + w / 2, base)]), P2)
            for c in np.linspace(x - w / 2 + 3, x + w / 2 - 3, 4):
                G.fill(G.mask_lines([(c, base - 17, c, base, 1.0)]), P2L, 0.6)
        elif k == 2:   # obelisk pair
            for o in (-6, 6):
                G.fill(G.mask_poly([(x + o - 3, base), (x + o - 2, base - 40), (x + o, base - 44), (x + o + 2, base - 40), (x + o + 3, base)]), P2)
        elif k == 3:   # stepped pyramid tomb
            for s_ in range(4):
                G.fill(G.mask_poly([(x - w / 2 + s_ * 3, base - s_ * 7), (x + w / 2 - s_ * 3, base - s_ * 7), (x + w / 2 - s_ * 3, base - s_ * 7 - 7), (x - w / 2 + s_ * 3, base - s_ * 7 - 7)]), P2)
        else:          # tall chapel with a needle
            G.fill(G.mask_poly([(x - w / 3, base), (x - w / 3, base - 30), (x, base - 42), (x + w / 3, base - 30), (x + w / 3, base)]), P2)
            needle(G, x, base - 40, 4, 22, P2, ribs=False)
        if rng.random() < 0.45:
            G.fill(G.mask_poly(arch_pts(x, 2.5, base - 6, base - 10, base)), hexc(WIN[1]), 0.8)
    G.fill((Y > 186).astype(float), hexc('0f152a'))
    G.add(np.exp(-((Y - 186) / 8) ** 2) * (0.5 + 0.5 * nz), hexc('22304e'), 0.9)
    # plane 1: the cemetery ground with cypresses, crosses and headstones in silhouette, an iron fence
    P1 = hexc('080a12')
    G.fill((Y > 200 + 2 * tile_noise(WS, HS, 16, 4, 63, 2)).astype(float), P1)
    for _ in range(14):
        x = rng.uniform(0, W); h = rng.uniform(16, 30)
        if abs(((x - FOCAL + W / 2) % W) - W / 2) < 30: continue
        G.fill(G.mask_poly([(x, 204 - h), (x + 3.5, 204 - h * 0.6), (x + 3, 204), (x - 3, 204), (x - 3.5, 204 - h * 0.6)]), P1)
    for _ in range(26):
        x = rng.uniform(0, W)
        if rng.random() < 0.5: G.fill(G.mask_lines([(x, 206, x, 196, 1.2), (x - 3, 199, x + 3, 199, 1.0)]), P1)
        else: G.fill(G.mask_poly([(x - 3, 207), (x - 3, 199), (x, 197), (x + 3, 199), (x + 3, 207)]), P1)
    G.fill(G.mask_lines([(0, 201, W, 201, 0.7)] + [(x, 201, x, 207, 0.5) for x in range(0, W, 4)]), P1)
    # the model renders flat dark silhouettes as nothing (pilot lesson): lift the whole guide, grade it back down in build()
    G.rgb = np.clip(G.rgb * 1.9 + 8, 0, 255)
    return G


def guide_mid():
    rng = np.random.default_rng(17)
    G = Guide(hexc('383c48'), alpha=True)
    X, Y = G.X, G.Y
    nz = tile_noise(WS, HS, 12, 6, 71, 2)
    stone, lit, dark, bone = hexc('4a5270'), hexc('7a88ac'), hexc('262a3c'), hexc('a09ca4')
    # piers (x, width, top) and bays (x0, x1, spring, kind)
    piers = [(0, 22, 124), (100, 18, 128), (170, 20, 124), (306, 22, 124), (384, 16, 140), (444, 18, 128)]
    def masonry(m, seed):
        cy = (np.floor(Y / 6) % 2); jx = ((X + cy * 5 + seed) % 10) < 0.6; jy = (Y % 6) < 0.6
        G.fill(m * (jx | jy), dark, 0.5); G.fill(m * (nz > 0.64), hexc('5a6280'), 0.35)
    for (px, pw, top) in piers:
        m = G.mask_poly([(px - pw / 2, top), (px + pw / 2, top), (px + pw / 2 + 2, 210), (px - pw / 2 - 2, 210)])
        if px == 384:   # a snapped pier
            m = G.mask_poly([(px - pw / 2, 150), (px - 3, 128), (px + 1, 138), (px + pw / 2, 120), (px + pw / 2 + 2, 210), (px - pw / 2 - 2, 210)])
        G.fill(m, stone); masonry(m, px)
        G.fill(m * (G.wdx(px) < -pw / 2 + 3), lit, 0.6); G.fill(m * (G.wdx(px) > pw / 2 - 4), dark, 0.6)
        if px != 384:
            G.fill(G.mask_poly([(px - pw / 2 - 4, top), (px + pw / 2 + 4, top), (px + pw / 2 + 2, top + 6), (px - pw / 2 - 2, top + 6)]), hexc('5a6280'))
            # a skull niche in the pier
            ny = top + 40 + rng.uniform(0, 20)
            G.fill(G.mask_poly(arch_pts(px, pw / 2 - 4, ny, ny - 6, ny + 14)), hexc('101420'))
            for k in range(3):
                for j in range(2):
                    G.fill(G.mask_ellipse(px - pw / 2 + 6 + k * (pw - 12) / 2, ny + 3 + j * 5, 1.8, 1.6), bone, 0.85)
    def arch(x0, x1, spring, rise_k, thick, broken=None, skulls=True):
        cx, half = (x0 + x1) / 2, (x1 - x0) / 2 - 10; apex = spring - half * rise_k
        outer = arch_pts(cx, half + thick, spring, apex - thick * 1.1, spring + 1, n=40)
        inner = arch_pts(cx, half, spring + 0.5, apex, 182, n=40)
        inner_m = G.mask_poly(inner)
        ring = np.clip(G.mask_poly(outer) - G.mask_poly(inner), 0, 1)
        if broken is not None:
            jag = 6 * (tile_noise(WS, HS, 5, 5, 72, 1) - 0.5); ring = ring * (np.abs(G.wdx(broken) + jag) > 9)
        G.fill(ring, stone)
        ang = np.arctan2(Y - spring, G.wdx(cx)); G.fill(ring * (np.abs(np.sin(ang * 26)) < 0.12), dark, 0.7)
        G.fill(np.clip(G.mask_poly(arch_pts(cx, half + 2, spring, apex - 2.2, spring + 1, n=40)) - G.mask_poly(inner), 0, 1) * (ring > 0.5), lit, 0.55)
        if skulls:   # skulls set along the intrados
            for t in np.linspace(0.08, 0.92, int(half / 4.5)):
                a = math.pi * (1 - t); sx = cx + math.cos(a) * (half + thick * 0.45); sy = spring - math.sin(a) * (spring - apex + thick * 0.5)
                if broken is not None and abs(sx - broken) < 12: continue
                G.fill(G.mask_ellipse(sx, sy, 1.7, 1.5), bone, 0.8); G.fill(G.mask_ellipse(sx, sy + 0.4, 0.5, 0.4), dark)
        G.rgb = G.rgb * (1 - inner_m[..., None]) + hexc('383c48') * inner_m[..., None]; G.a = G.a * (1 - inner_m)
        return cx, apex
    # the spandrel wall over the arcade: a ragged ruined top at y≈76-90, broken down over the snapped crown and the collapsed bay
    wt = 80 + 9 * tile_noise(WS, HS, 24, 4, 73, 3) + 30 * np.exp(-(G.wdx(238) / 18) ** 2)
    wall = ((Y > wt) & (Y < 132)).astype(float) * (1 - G.mask_poly([(392, 0), (436, 0), (436, 216), (392, 216)]))
    G.fill(wall, hexc('424a66')); masonry(wall, 3)
    G.fill(wall * (Y < wt + 2.5), lit, 0.6)                                                  # moonlit broken top
    G.fill(G.mask_lines([(x0, 132, x1, 132, 2.4) for x0, x1 in ((-12, 392), (436, 524))]), hexc('5a6280'))   # string course at the springing
    bays = [arch(0, 100, 132, 0.75, 9), arch(100, 170, 136, 0.6, 8, skulls=False), arch(170, 306, 132, 0.62, 10, broken=238),
            arch(306, 384, 132, 0.7, 9)]
    c6 = arch(444, 512, 136, 0.65, 8)
    # chains with small bells and ghost lanterns, different lengths; one chain hangs free over the broken crown
    for (cx, apex), ln, kind in ((bays[0], 46, 'bell'), (bays[2], 30, 'lantern'), (bays[3], 56, 'bell'), (c6, 24, 'lantern')):
        y1 = apex + ln; G.fill(G.mask_lines([(cx, apex - 2, cx, y1, 0.8)]), hexc('5a5a68'))
        if kind == 'bell':
            G.fill(G.mask_poly([(cx - 2, y1), (cx + 2, y1), (cx + 4, y1 + 6), (cx + 5, y1 + 8), (cx - 5, y1 + 8), (cx - 4, y1 + 6)]), hexc('6a6a78'))
        else:
            G.fill(G.mask_poly([(cx - 3, y1), (cx + 3, y1), (cx + 3.5, y1 + 8), (cx, y1 + 10), (cx - 3.5, y1 + 8)]), hexc('2a2e40'))
            G.fill(G.mask_ellipse(cx, y1 + 5, 1.8, 2.4), hexc(WIN[2])); G.glow(cx, y1 + 5, 7, 7, hexc(WIN[1]), 0.6)
    # wrought-iron railing between the piers, with spear finials; a bone ossuary heap in the collapsed bay
    rail = G.mask_lines([(0, 184, W, 184, 1.2), (0, 198, W, 198, 1.0)] + [(x, 180, x, 210, 0.8) for x in np.arange(0, W, 5)])
    G.fill(rail, hexc('2a2e40'))
    for x in np.arange(0, W, 5):
        G.fill(G.mask_poly([(x - 1.2, 181), (x, 177), (x + 1.2, 181)]), hexc('3a4466'))
    heap = G.mask_poly([(392, 212), (402, 194), (414, 188), (428, 192), (440, 212)])
    G.fill(heap, hexc('3a3c4c'))
    for _ in range(26):
        G.fill(G.mask_ellipse(rng.uniform(398, 436), rng.uniform(192, 208), 1.8, 1.5), bone, 0.8)
    G.fill((Y > 208).astype(float), hexc('20223a'))
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image()).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


# -------------------------------------------------------------------------------------------------- render + build
RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=5, denoise=0.74, cn=0.45, cn_end=0.6, pix=0.45, guide_blur=1.3),
    'mid': dict(prompt=PROMPT_MID, seed=2, denoise=0.7, cn=0.5, cn_end=0.7, pix=0.55, guide_blur=1.0, seam_band=96),
}


def do_render():
    bgv2b.set_prefix(B); times = {}
    for layer, kw in RENDER.items():
        times[layer] = round(render_layer(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


def far_post(a, stage):
    """'hi': soft-knee the highlights (the ghost-fire window sits behind the player at camera start in NV10 and must not
    out-shine the play layer): luminance above 120 is compressed 2:1."""
    if stage != 'hi': return a
    l = a.mean(2, keepdims=True); k = np.where(l > 120, (120 + (l - 120) * 0.5) / np.maximum(l, 1), 1.0)
    return a * k


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=5, grade_kw=dict(black=4, white=250, gamma=1.0, sat=0.85), post=far_post, dk=0.4)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=2,
                                  grade_kw=dict(black=10, white=330, gamma=0.85, sat=0.6, tint=(70, 84, 140), tint_k=0.35), rim_col=hexc('3a4466'))
    far_im, mid_im = to_rgba(far), to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png')
    preview(far_im, mid_im, TINT, f'{SRC}/preview.png')
    st = {'far': stats(far_im), 'mid': stats(mid_im), 'accents_far': ['%02x%02x%02x' % c for c in acc_f], 'accents_mid': ['%02x%02x%02x' % c for c in acc_m]}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase:
        ase_build(f'bg_{B}_far', far_im); ase_build(f'bg_{B}_mid', mid_im)


if __name__ == '__main__':
    if '--sweep' in sys.argv:
        i = sys.argv.index('--sweep'); layer = sys.argv[i + 1]; seeds = [int(s) for s in sys.argv[i + 2].split(',')]
        kw = dict(RENDER[layer]); kw.pop('seed'); kw.pop('seam_band', None)
        for k in ('denoise', 'cn', 'pix'):
            if f'--{k}' in sys.argv: kw[k] = float(sys.argv[sys.argv.index(f'--{k}') + 1])
        bgv2b.set_prefix(B)
        print(bgv2b.sweep(SRC, layer, kw.pop('prompt'), seeds, os.path.join(os.environ.get('BG_SWEEP', '/tmp'), B), label=os.environ.get('BG_LABEL'), **kw))
        sys.exit()
    if '--guide' in sys.argv or '--render' in sys.argv: paint_guides()
    if '--render' in sys.argv: do_render()
    if '--guide' not in sys.argv: build(ase='--no-ase' not in sys.argv)
