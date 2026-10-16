#!/usr/bin/env python3
"""Sunscorched Dunes backdrop v2 (bg rollout, agent B; docs/v17/bg_rollout_b.md, method in docs/v17/bg_pilot.md).

  python3 art/gen_bg_dunes_v2.py            build bg_dunes_{far,mid} from the saved renders in art/bg_src/dunes/
  python3 art/gen_bg_dunes_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_dunes_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  python3 art/gen_bg_dunes_v2.py --sweep far|mid 1,2,3   pass-1 seed sweep into $BG_SWEEP
  --no-ase                                   write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/dunes_bg.py (kept for rollback).
Identity kept: a buried desert seen through a rift in a cavern roof ("somewhere far above, the sun still burns"). Changes: the
sun stays at far (297,34) so GFX_SUN.dunes is unchanged; saturation is toned down (dusty ochre instead of amber); the crude
jagged roof band is now eroded strata rock; the blocky mid-layer Anubis bust is gone, the jackal god is now a distant seated
colossus at background scale in the haze; the mid layer has a broken colonnade, a fallen colossal head and two obelisks.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgv2b

B = 'dunes'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#2a1a0c'
SUN = (297, 34)

# v1 ramps (dunes_bg.py ROCK / SKY / HAZE / DUNE / SIL / RIM) with the saturation pulled down ~40% (same hue family)
# v1 ramps (dunes_bg.py ROCK / SKY / HAZE / DUNE / SIL / RIM), saturation scaled by DESAT (same hues and values). The first pass used
# ~0.6 and read hazy and muddy (lead review), so 0.8: far saturation 0.69 (v1) -> ~0.55
DESAT = 0.8


def _ds(hexes, k=DESAT):
    out = []
    for h in hexes:
        c = hexc(h); l = c.mean(); c = l + (c - l) * k
        out.append('%02x%02x%02x' % tuple(int(round(v)) for v in np.clip(c, 0, 255)))
    return out


ROCK = _ds(['0c0705', '120a07', '190e09', '20130b', '2a180e', '341e11', '42281a', '553422'])
SKY = _ds(['5a3410', '7a4814', '9c6018', 'c07c20', 'e0a032', 'f4c65a', 'fde392', 'fff4cc', 'fffcf0'])
HAZE = _ds(['3a220e', '4e2e12', '643c16', '7c4c1c', '956022', 'ac742a', 'c28a36', 'd6a046', 'e6b85a'])
DUNE = _ds(['24150a', '321d0d', '422711', '553216', '6a3f1b', '7f4e22', '96602a', 'ad7434'])
SKY_MID = ['%02x%02x%02x' % tuple(int(round(v)) for v in (hexc(a) + hexc(b)) / 2) for a, b in zip(SKY[2:], SKY[3:])]   # half steps: no halo rings
FAR_PAL = [hexc(c) for c in ROCK + SKY + SKY_MID + HAZE + DUNE]
SIL = _ds(['0e0805', '140b06', '1b0f08', '24140a', '2e1a0d', '382010', '442814'])
RIM = _ds(['7a5018', 'a8742a', 'd6a044', 'f4ca6c'])
MID_PAL = [hexc(c) for c in SIL + RIM + _ds(['5a3a1c', '6e4822'])]

PROMPT_FAR = ('pixel art, dark fantasy, a vast buried desert seen through a long rift in a dark cavern roof of layered sandstone, a pale '
              'hazy sun burning high in the rift, thin streams of sand falling from the rock, far away in the dust haze an ancient rock-cut temple carved into a sandstone '
              'cliff with four colossal seated stone statues of ancient gods flanking a dark doorway, an empty lifeless desert, weathered pyramids on the horizon, '
              'rolling dunes with wind ripples in soft light '
              'and shadow, side-scroller game background, muted dusty ochre and umber palette, desaturated, atmospheric depth, haze, '
              'highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, ancient desert temple ruins half buried in sand, a broken colonnade of carved sandstone columns '
              'with papyrus capitals under a cracked architrave, the fallen colossal stone head of a pharaoh with a striped headcloth half '
              'sunk in a dune, a ruined temple pylon tower with a winged sun disc relief, two tall obelisks with worn hieroglyphs, sand dune crests, isolated on a flat grey background, side-scroller game background '
              'layer, dark umber stone with warm golden rim light, detailed')


# -------------------------------------------------------------------------------------------------- guides
def guide_far():
    rng = np.random.default_rng(23)
    G = Guide(hexc('a0805c'))
    X, Y = G.X, G.Y
    sx, sy = SUN
    nz = tile_noise(WS, HS, 64, 16, 81, 3)
    # sky in the rift: pale and hazy around the sun, dustier toward the edges and the horizon
    ds = np.sqrt((G.wdx(sx) * 0.8) ** 2 + ((Y - sy) * 1.2) ** 2)
    v = 0.45 + 0.5 * np.exp(-(ds / 95) ** 2) - 0.22 * smooth(40, 150, Y) + 0.04 * (nz - 0.5)
    G.rgb = lerp(hexc('6e5434'), hexc('f6ead2'), np.clip(v, 0, 1)[..., None])
    d = np.sqrt(G.wdx(sx) ** 2 + (Y - sy) ** 2)
    G.fill((d < 11).astype(float), hexc('fffaf0')); G.add(np.exp(-(d / 26) ** 2), hexc('3a3026'), 0.9)
    # far haze band; two pyramids on the right horizon
    HZ = 114 + 3 * np.sin(2 * np.pi * X * 2 / W)
    G.fill_img((Y > HZ).astype(float), lerp(hexc('a4845c'), hexc('6e5438'), smooth(HZ, 216, Y)[..., None]))
    for (cx, w, h) in ((428, 54, 42), (480, 26, 19)):
        base = 117
        m = G.mask_poly([(cx - w, base), (cx - 2.5, base - h + 3), (cx + 2.5, base - h + 3), (cx + w, base)])   # capstones long gone
        G.fill(m, hexc('b4966a')); G.fill(m * (G.wdx(cx) > 0), hexc('6e5438'), 0.9)
        for k in range(1, int(h / 4)):
            G.fill(m * (np.abs(Y - (base - k * 4)) < 0.35), hexc('5e4630'), 0.4)
    # --- focal: a rock temple carved into a far sandstone mesa (x≈90-230): four seated jackal-headed colossi in a row, a dark
    # doorway between them; the mythic statue now lives at background scale, faint in the haze
    mesa = G.mask_poly([(70, 152), (78, 96), (86, 88), (104, 84), (210, 82), (226, 90), (236, 104), (246, 152)])
    G.fill(mesa, hexc('92724e'))
    G.fill(mesa * (np.sin(Y * 1.4 + 3 * tile_noise(WS, HS, 32, 8, 84, 2)) > 0.75), hexc('7a5e40'), 0.6)      # bedding planes
    G.fill(mesa * (G.wdx(160) > 62), hexc('6e5438'), 0.7)                                                      # shaded east flank
    G.fill(G.mask_poly([(100, 150), (100, 96), (220, 96), (220, 150)]), hexc('806244'))                         # the cut facade
    for cx in (114, 140, 180, 206):                                                                            # deep shadowed niches behind the statues
        G.fill(G.mask_poly([(cx - 12, 150), (cx - 12, 108), (cx + 12, 108), (cx + 12, 150)]), hexc('4e3a28'))
    G.fill(G.mask_lines([(98, 96, 222, 96, 1.6)]), hexc('b4966a'))
    for k in range(13):                                                                                        # frieze of seated baboons/jackals
        G.fill(G.mask_ellipse(104 + k * 9.3, 99.5, 2.2, 2.6), hexc('6e5438'))
    for i, cx in enumerate((114, 140, 180, 206)):
        base = 150; c, lt, sh = hexc('c4a67c'), hexc('e2cea6'), hexc('806244')
        G.fill(G.mask_poly([(cx - 11, base), (cx - 11, base - 18), (cx - 8, base - 22), (cx + 8, base - 22), (cx + 11, base - 18), (cx + 11, base)]), c)   # legs, lap
        G.fill(G.mask_poly([(cx - 8, base - 20), (cx - 8, base - 36), (cx - 5, base - 40), (cx + 5, base - 40), (cx + 8, base - 36), (cx + 8, base - 20)]), c)  # torso
        G.fill(G.mask_poly([(cx - 9, base - 34), (cx - 6, base - 44), (cx - 3, base - 38)]), sh, 0.8)          # headcloth lappets
        G.fill(G.mask_poly([(cx + 9, base - 34), (cx + 6, base - 44), (cx + 3, base - 38)]), sh, 0.8)
        G.fill(G.mask_poly([(cx - 4, base - 38), (cx - 4.5, base - 46), (cx, base - 48), (cx + 4.5, base - 46), (cx + 4, base - 38)]), c)          # head
        G.fill(G.mask_poly([(cx - 1.6, base - 41), (cx, base - 36.5), (cx + 1.6, base - 41)]), c)                  # long muzzle (frontal)
        for e in (-2.6, 2.6):                                                                                       # tall ears
            G.fill(G.mask_poly([(cx + e - 1.4, base - 46), (cx + e * 1.25, base - 55), (cx + e + 1.4, base - 46)]), c)
        G.fill(G.mask_lines([(cx - 6, base - 22, cx + 6, base - 22, 0.8)]), sh, 0.7)                               # forearms
        G.fill(G.mask_poly([(cx - 11, base), (cx - 11, base - 18), (cx - 8, base - 22), (cx - 8, base - 40), (cx - 5, base - 40), (cx - 6, base)]), lt, 0.45)
        if i == 2: G.fill(G.mask_poly([(cx + 2, base - 48), (cx + 10, base - 30), (cx + 11, base), (cx + 4, base)]), hexc('806244'))  # one has lost its shoulder
    G.fill(G.mask_poly(arch_pts(160, 6, 136, 128, 150, pointed=False)), hexc('3e2e20'))                       # the dark doorway
    G.fill(G.mask_poly([(150, 128), (170, 128), (170, 125), (150, 125)]), hexc('ccb08a'), 0.8)                  # lintel with a sun disc
    G.fill(G.mask_ellipse(160, 122, 2.2, 2.2), hexc('dcc4a0'))
    G.fill(G.mask_poly([(60, 160), (90, 140), (130, 146), (170, 142), (230, 140), (262, 162)]), hexc('a4845c'))  # sand drifted against the facade
    G.add(np.exp(-((Y - 150) / 14) ** 2), hexc('3a2e22'), 0.5)                                                  # dust haze at its foot
    # three dune ranges, far to near (smooth light and lee-side shade, no posterized steps)
    for (base, amp, per, ph, seed, c_hi, c_lo) in ((150, 9, 3, 0.5, 11, 'a4845c', '6e5438'), (168, 14, 2, 2.1, 12, '806244', '4e3a28'),
                                                     (190, 18, 1, 4.0, 13, '62482e', '2e2117')):
        p = bgv2b.profile(48, seed, 3)
        top = base - amp * (0.55 + 0.45 * np.sin(2 * np.pi * (np.arange(WS) / S) * per / W + ph)) - 6 * (p - 0.5)
        slope = np.gradient(top)[None, :]
        m = (Y >= top[None, :]).astype(float)
        t = smooth(0, 50, Y - top[None, :])
        c = lerp(hexc(c_hi), hexc(c_lo), t[..., None])
        lee = smooth(0.0, 0.12, slope) * np.exp(-np.clip(Y - top[None, :], 0, None) / 22)      # lee faces in soft shade near the crest
        c = c * (1 - 0.22 * lee)[..., None]
        G.fill_img(m, c)
        G.fill(m * (Y - top[None, :] < 1.2), hexc(c_hi) * 1.15, 0.8)
    # wind ripples on the dune faces (soft, slanted)
    rip = np.sin(X * 2 * np.pi * 73 / W + Y * 2.6 + 4 * tile_noise(WS, HS, 32, 8, 85, 2)) > 0.82
    G.fill(rip * (Y > 128).astype(float), hexc('3a2a1c'), 0.18)
    # the cavern roof: layered sandstone strata, thick at the sides and thin over the sun, an eroded lower lip with a lit underside
    rift = 32 - 18 * np.cos(2 * np.pi * (np.arange(WS) / S - sx) / W) + 7 * np.sin(2 * np.pi * (np.arange(WS) / S) * 3 / W + 1.2) \
           + 6 * (bgv2b.profile(24, 91, 3) - 0.5)
    rift = rift + 10 * np.exp(-(((np.arange(WS) / S - 40 + W / 2) % W - W / 2) / 30) ** 2)     # a hanging rock tongue at x≈40
    rm = (Y <= rift[None, :]).astype(float)
    strata = np.sin((Y + 6 * tile_noise(WS, HS, 64, 16, 92, 2) + X * 0.08) * 0.9)
    rc = lerp(hexc('1a120c'), hexc('382819'), (0.5 + 0.3 * strata + 0.3 * smooth(-30, 0, Y - rift[None, :]))[..., None])
    G.fill_img(rm, rc)
    G.fill(rm * (rift[None, :] - Y < 2.5), hexc('7a5e3a'))                                       # sunlit lip
    G.fill(rm * (rift[None, :] - Y >= 2.5) * (rift[None, :] - Y < 6), hexc('46321f'), 0.8)
    for (fx, ln) in ((96, 40), (188, 24), (352, 54), (402, 30), (470, 36)):                   # thin sand trickles from the lip
        t0 = rift[int(fx * S) % WS]
        G.fill(G.mask_lines([(fx, t0, fx + 0.5, t0 + ln, 0.8)]), hexc('dcc4a0'), 0.6)
    return G


def guide_mid():
    """Painted bright (stone values, carvings) and graded dark in build(): the model adds nothing to flat dark silhouettes."""
    rng = np.random.default_rng(29)
    G = Guide(hexc('3a3c40'), alpha=True)
    X, Y = G.X, G.Y
    stone, lit, dark, mid_ = hexc('a4845c'), hexc('dcc4a0'), hexc('5e4630'), hexc('86684a')
    # near dune crests along the bottom (two overlapping), lit edge
    for (base, amp, per, ph, seed, col) in ((194, 10, 2, 0.7, 31, '86684a'), (205, 7, 3, 2.4, 32, '6e5438')):
        p = bgv2b.profile(32, seed, 2)
        top = base - amp * (0.5 + 0.5 * np.sin(2 * np.pi * (np.arange(WS) / S) * per / W + ph)) - 4 * (p - 0.5)
        m = (Y >= top[None, :]).astype(float); G.fill(m, hexc(col)); G.fill(m * (Y - top[None, :] < 1.5), lit, 0.7)
    def glyphs(m, x0, x1, y0, y1, step=6):
        for yy in np.arange(y0, y1, step):
            for xx in np.arange(x0 + 1.5, x1 - 1, 3.2):
                if rng.random() < 0.6: G.fill(m * G.mask_ellipse(xx, yy, 0.9, 1.5), dark, 0.55)
    def column(x, top, w=11, base=202, broken=False):
        pts = [(x - w / 2, top), (x + w / 2, top), (x + w / 2 + 0.5, base), (x - w / 2 - 0.5, base)]
        if broken: pts = [(x - w / 2, top + 5), (x - 1, top), (x + 2, top + 6), (x + w / 2, top + 2), (x + w / 2 + 0.5, base), (x - w / 2 - 0.5, base)]
        m = G.mask_poly(pts); G.fill(m, stone)
        for k in np.arange(top + 9, base, 10): G.fill(m * (np.abs(Y - k) < 0.45), dark, 0.7)      # drums
        G.fill(m * (G.wdx(x) < -w / 2 + 2.5), lit, 0.8); G.fill(m * (G.wdx(x) > w / 2 - 3), dark, 0.6)
        glyphs(m, x - w / 2 + 1, x + w / 2 - 1, top + 16, top + 40)
        if not broken:   # papyrus-bundle capital
            G.fill(G.mask_poly([(x - w / 2, top), (x - w / 2 - 4, top - 8), (x + w / 2 + 4, top - 8), (x + w / 2, top)]), mid_)
            for f in np.linspace(x - w / 2 - 2, x + w / 2 + 2, 5): G.fill(G.mask_lines([(x + (f - x) * 0.4, top, f, top - 7, 0.5)]), dark, 0.6)
            G.fill(G.mask_poly([(x - w / 2 - 5, top - 8), (x + w / 2 + 5, top - 8), (x + w / 2 + 5, top - 11), (x - w / 2 - 5, top - 11)]), stone)
    # the colonnade (left): three standing under a broken architrave and cavetto cornice, a fourth snapped short
    for x in (18, 46, 74): column(x, 98)
    column(102, 132, broken=True)
    arch_ = G.mask_poly([(4, 87), (88, 87), (90, 80), (84, 76), (86, 72), (4, 72)])
    G.fill(arch_, stone); G.fill(arch_ * (Y < 75), lit, 0.8); G.fill(arch_ * (np.abs(Y - 80) < 0.5), dark, 0.7)
    corn = G.mask_poly([(2, 72), (84, 72), (88, 64), (2, 64)]); G.fill(corn, mid_); G.fill(corn * (Y < 66), lit, 0.7)
    for xx in np.arange(4, 84, 3): G.fill(corn * (np.abs(G.wdx(xx)) < 0.35), dark, 0.5)        # cavetto fluting
    G.fill(G.mask_ellipse(46, 79, 7, 3), lit, 0.6); G.fill(G.mask_lines([(36, 79, 30, 77, 1.2), (56, 79, 62, 77, 1.2)]), lit, 0.6)   # winged sun disc
    G.fill(G.mask_poly([(108, 200), (114, 192), (128, 193), (132, 200)]), stone)                # a fallen drum
    # the fallen colossal head of a sun-king, tilted and sunk to the cheek in the dune (a ruin, not a figure), x≈232
    hx, hy, tilt, k = 232, 222, math.radians(14), 1.1   # sunk to the lips, low in the layer: it sat right behind the player in DU1
    def rot(pts):
        return [(hx + (x - hx) * k * math.cos(tilt) - (y - hy) * k * math.sin(tilt), hy + (x - hx) * k * math.sin(tilt) + (y - hy) * k * math.cos(tilt)) for x, y in pts]
    nm = G.mask_poly(rot([(hx - 30, hy + 6), (hx - 29, hy - 30), (hx - 20, hy - 50), (hx, hy - 56), (hx + 20, hy - 50), (hx + 29, hy - 30), (hx + 30, hy + 6)]))
    G.fill(nm, mid_)
    G.fill(nm * (np.sin((Y * math.cos(tilt) - G.wdx(hx) * math.sin(tilt)) * 1.1) > 0.35), dark, 0.6)     # nemes stripes
    fm = G.mask_poly(rot([(hx - 15, hy - 40), (hx + 15, hy - 40), (hx + 16, hy - 18), (hx + 11, hy - 2), (hx + 4, hy + 6), (hx - 4, hy + 6), (hx - 11, hy - 2), (hx - 16, hy - 18)]))
    G.fill(fm, stone); G.fill(fm * (G.wdx(hx) < -6), lit, 0.6); G.fill(fm * (G.wdx(hx) > 12), dark, 0.4)
    for ex in (-7, 7):   # heavy-lidded eyes, brows, nose, lips
        G.fill(G.mask_lines([rot([(hx + ex - 4.5, hy - 26)])[0] + rot([(hx + ex + 4.5, hy - 26)])[0] + (1.0,)]), dark, 0.9)
        G.fill(G.mask_lines([rot([(hx + ex - 5, hy - 31)])[0] + rot([(hx + ex + 5, hy - 31)])[0] + (0.8,)]), dark, 0.5)
    G.fill(G.mask_poly(rot([(hx - 1.5, hy - 24), (hx + 3.5, hy - 12), (hx - 3, hy - 12)])), dark, 0.45)
    G.fill(G.mask_lines([rot([(hx - 6, hy - 5)])[0] + rot([(hx + 6, hy - 5)])[0] + (1.0,)]), dark, 0.7)
    G.fill(G.mask_lines([rot([(hx + 9, hy - 54)])[0] + rot([(hx + 3, hy - 36)])[0] + (0.8,), rot([(hx + 3, hy - 36)])[0] + rot([(hx + 8, hy - 20)])[0] + (0.7,)]), dark)
    G.fill(G.mask_poly([(hx - 56, 216), (hx - 44, 207), (hx - 12, 203), (hx + 24, 205), (hx + 58, 210), (hx + 66, 216)]), hexc('86684a'))   # drift over the chin
    G.fill(G.mask_poly([(hx - 44, 208), (hx - 12, 204), (hx + 24, 206), (hx + 58, 211), (hx + 58, 213), (hx + 24, 208), (hx - 12, 206), (hx - 44, 210)]), lit, 0.6)
    # a pylon tower fragment (right): battered walls, torus edges, cavetto cornice, a sunk relief of a winged disc, top corner fallen
    px0, px1 = 328, 392
    pyl = G.mask_poly([(px0, 202), (px0 + 7, 100), (366, 100), (372, 108), (380, 106), (px1 - 7, 114), (px1, 202)])
    G.fill(pyl, stone)
    for yy in np.arange(106, 200, 7): G.fill(pyl * (np.abs(Y - yy) < 0.4), dark, 0.45)          # courses
    G.fill(pyl * (np.abs(G.wdx(px0 + 7 - (Y - 100) * 7 / 102)) < 1.6), lit, 0.8)              # torus roll on the lit edge
    G.fill(G.mask_poly([(px0 + 5, 100), (366, 100), (366, 92), (px0 + 3, 92)]), mid_); G.fill(G.mask_poly([(px0 + 3, 92), (366, 92), (366, 89), (px0 + 3, 89)]), lit, 0.8)
    G.fill(G.mask_ellipse(358, 124, 6, 5), dark, 0.6)
    G.fill(G.mask_poly([(338, 124), (352, 120), (352, 128)]), dark, 0.5); G.fill(G.mask_poly([(378, 124), (364, 120), (364, 128)]), dark, 0.5)
    glyphs(pyl, px0 + 10, px1 - 10, 140, 190, step=8)
    G.fill(G.mask_poly([(392, 204), (398, 196), (414, 198), (420, 204)]), stone)                  # the fallen corner block
    # two obelisks (one snapped), right
    for (ox, top, w, snapped) in ((434, 62, 11, False), (462, 124, 9, True)):
        pts = [(ox - w / 2, 202), (ox - w / 2 + 1.5, top + 6), (ox, top - 4), (ox + w / 2 - 1.5, top + 6), (ox + w / 2, 202)]
        if snapped: pts = [(ox - w / 2, 202), (ox - w / 2 + 1, top + 3), (ox - 1, top), (ox + 2, top + 5), (ox + w / 2 - 1, top + 1), (ox + w / 2, 202)]
        m = G.mask_poly(pts); G.fill(m, stone); G.fill(m * (G.wdx(ox) < -w / 2 + 2.5), lit, 0.8)
        glyphs(m, ox - w / 2 + 1, ox + w / 2 - 1, top + 12, 196, step=6)
        if not snapped: G.fill(G.mask_poly([(ox - 3.5, top + 4), (ox, top - 4), (ox + 3.5, top + 4)]), hexc('eadab8'), 0.9)
    for (bx, by, bw, bh) in ((150, 196, 16, 8), (290, 197, 18, 8), (486, 196, 20, 9)):
        m = G.mask_poly([(bx, by + bh), (bx, by), (bx + bw, by + 1), (bx + bw, by + bh)]); G.fill(m, stone); G.fill(m * (Y < by + 1.5), lit, 0.6)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image()).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


# -------------------------------------------------------------------------------------------------- render + build
RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=11, denoise=0.62, cn=0.55, cn_end=0.65, pix=0.45, guide_blur=1.3, seam_dn=0.68),
    'mid': dict(prompt=PROMPT_MID, seed=2, denoise=0.7, cn=0.5, cn_end=0.7, pix=0.55, guide_blur=1.0, seam_band=96),
}


def do_render():
    bgv2b.set_prefix(B); times = {}
    for layer, kw in RENDER.items():   # the far pass 1 has a strong wrap step in the dune bands: smear it before the seam pass
        times[layer] = round((bgv2b.render_layer_smear if layer == 'far' else render_layer)(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


PATCH = [(324, 130, 342, 148)]   # 1x boxes: the model put a small creature-like stump in the dunes (could read as an enemy)


def far_post(a, stage):
    """'hi': fill the PATCH boxes row by row with a blend of the pixels just outside them (sand), so no figure remains."""
    if stage != 'hi': return a
    a = a.copy()
    for (x0, y0, x1, y1) in PATCH:
        X0, Y0, X1, Y1 = x0 * S, y0 * S, x1 * S, y1 * S
        t = np.linspace(0, 1, X1 - X0)[None, :, None]
        a[Y0:Y1, X0:X1] = a[Y0:Y1, X0 - 1:X0] * (1 - t) + a[Y0:Y1, X1:X1 + 1] * t
    # value contrast (lead review: the first grade read hazy and muddy): an S-curve on luminance deepens the shaded faces of the
    # temple and colossi and clears the sky glow; the horizon haze band is lifted a little for aerial depth
    l = a.mean(2, keepdims=True) / 255
    l2 = np.clip(l + 0.55 * (l * l * (3 - 2 * l) - l), 0, 1)
    yy = (np.arange(a.shape[0]) / S)[:, None, None]
    l2 = l2 + 0.09 * np.exp(-((yy - 130) / 22) ** 2) * smooth(0.4, 0.55, l2)
    return np.clip(a * (l2 / np.maximum(l, 1e-3)), 0, 255)


HEAD = (232, 192, 38, 30)   # the fallen head (1x ellipse: cx, cy, rx, ry)


def mid_post(a, stage):
    """'lo': the fallen head is lifted ~35 % inside its ellipse so its carved face reads as stone, not as a dark mass (lead review, DU1)."""
    cx, cy, rx, ry = HEAD
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    k = 1 + 0.35 * np.clip(1.4 - np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2), 0, 1)
    return np.clip(a * k[..., None], 0, 255)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=5, grade_kw=dict(black=4, white=255, gamma=1.0, sat=1.35), post=far_post, dk=0.3)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=3,
                                  grade_kw=dict(black=52, white=480, gamma=0.78, sat=1.0), post=mid_post, rim_col=hexc(RIM[3]), rim_col2=hexc(RIM[1]))
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
