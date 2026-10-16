#!/usr/bin/env python3
"""Rootbound Catacombs backdrop v2 (bg pilot, docs/v17/bg_pilot.md).

  python3 art/gen_bg_catacombs_v2.py            build bg_catacombs_{far,mid} from the saved renders in art/bg_src/catacombs/
  python3 art/gen_bg_catacombs_v2.py --guide    only (re)paint the layout guides
  python3 art/gen_bg_catacombs_v2.py --render   repaint guides and re-render with ComfyUI (server on :8188), then build
  --no-ase                                       write previews only, leave the assets alone

Same asset names, size (512x216), tag (`loop`) and frame count as art/env_bg.py, so nothing in web/src changes.
The old generator stays for rollback: `python3 art/gen_env.py` rebuilds the v1 layers.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa

B = 'catacombs'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)

# -------------------------------------------------------------------------------------------------- palette (v2 ramps)
# the v1 ramps (env_bg.py K_CAVE / K_TEAL / K_GOLD) extended upward in the same hue family: the v1 layer topped out at
# #382c2e, which the indoor ambient (x0.39) and the back-wall veil turned into black.
CAVE = ['070507', '0b080b', '100c0f', '161114', '1d161a', '251c20', '2e2427', '382c2e', '443635', '524139', '614d42', '735b4c', '876b58']
TEAL = ['152322', '1b2d2b', '223835', '2b4541', '36554f', '46685f', '5e8579', '84ab9b']
GOLD = ['4a301c', '684622', '8a602c', 'ac7e38', 'cca04c', 'e8c470', 'f6e2a4']
BONE = ['6e6252', '8c7d68', 'a89880']
FAR_PAL = [hexc(c) for c in CAVE + TEAL + GOLD + BONE]
SIL = ['0d090a', '130e0f', '1a1415', '221a1a', '2b2120', '352927', '403230', '4c3b37']
RIM = ['2a4541', '3e6158', '5e8579']
MID_PAL = [hexc(c) for c in SIL + ['2a4541'] + GOLD[:4]]

PROMPT_FAR = ('pixel art, dark fantasy, vast underground ossuary catacomb, walls built of stacked human skulls and bones in rows, a great pointed stone arch '
              'opening onto a receding vaulted crypt corridor, distant small chapel lit by a shaft of golden light, gnarled dark tree roots '
              'hanging from the vault ceiling, dust in the air, side-scroller game background, muted warm brown and umber palette with teal '
              'accents, atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, ruined crypt stone arches and broken pillars, weathered masonry blocks, thick gnarled tree roots draped over the '
              'arches, rubble and skulls at the base, isolated on a flat dark background, side-scroller game background layer, '
              'muted dark brown stone with teal rim light, detailed')


# -------------------------------------------------------------------------------------------------- guides
def guide_far():
    rng = np.random.default_rng(7)
    G = Guide(hexc('120d0f'))
    nz = tile_noise(WS, HS, 96, 48, 1); nz2 = tile_noise(WS, HS, 24, 12, 2, octaves=2)
    # cavern air: brighter in the middle distance and toward the main opening (x=232), darker at roof and floor
    cx_main = 232
    lit = np.exp(-(G.wdx(cx_main) / 130) ** 2)
    v = 0.22 + 0.30 * lit + 0.10 * (nz - 0.5)
    v *= 0.65 + 0.35 * smooth(0, 70, G.Y) - 0.35 * smooth(170, 216, G.Y)
    air = lerp(hexc('140e10'), hexc('5a4840'), v[..., None])
    G.rgb = air
    # the ossuary wall (a plane at mid distance) with a ragged top under the vault
    top = 30 + 8 * np.sin(G.X / W * 2 * math.pi * 3 + 1) + 6 * (nz[0:1, :] - 0.5)
    wall = (G.Y > top) & (G.Y < 186)
    wv = 0.30 + 0.28 * lit + 0.18 * (nz2 - 0.5) - 0.18 * smooth(140, 186, G.Y)
    wall_col = lerp(hexc('241a1c'), hexc('6a5548'), np.clip(wv, 0, 1)[..., None])
    G.fill_img(wall.astype(float), wall_col)
    # courses of masonry: faint horizontal joints
    for y in range(40, 186, 11):
        G.fill(G.mask_lines([(x, y + (x // 31) % 2, x + 30, y + (x // 31) % 2, 0.7) for x in range(0, W, 31)]) * wall, hexc('1c1416'), 0.5)
    # ossuary wall: bands of stacked skulls between courses of long bones, a few arched burial niches (varied per section)
    sections = [(4, 136, 50, 5), (334, 412, 58, 4), (470, 508, 70, 3), (154, 176, 66, 4), (290, 312, 66, 4)]
    for (x0, x1, y0, tiers) in sections:
        for t in range(tiers):
            ty = y0 + t * 22
            near = float(np.exp(-(((x0 + x1) / 2 - cx_main) / 160) ** 2))
            bone = hexc('8a7a64') * (0.8 + 0.3 * near); skull = hexc('a8977e') * (0.8 + 0.3 * near)
            # recess the band sits in
            G.fill(G.mask_poly([(x0, ty - 1), (x1, ty - 1), (x1, ty + 16), (x0, ty + 16)]), hexc('1a1214'))
            # long-bone courses above and below (bundled femurs: a pale line with knobbed ends every few px)
            for yy in (ty + 0.5, ty + 15):
                G.fill(G.mask_lines([(x0, yy, x1, yy, 1.6)]), bone * 0.85)
                for kx in np.arange(x0 + 1, x1, 4.0):
                    G.fill(G.mask_ellipse(kx, yy, 1.3, 1.3), bone)
            # the skull row: packed, slightly irregular, every other band offset; gaps where skulls fell
            jit = 0
            for nx in np.arange(x0 + 3 + (t % 2) * 2.5, x1 - 2, 5.2):
                if rng.random() < 0.08: continue
                jit = rng.uniform(-0.6, 0.6)
                cy_ = ty + 8 + jit
                G.fill(G.mask_ellipse(nx, cy_, 2.4, 2.6), skull * rng.uniform(0.85, 1.05))
                G.fill(G.mask_ellipse(nx - 0.9, cy_ + 0.3, 0.75, 0.8), hexc('1a1214'))
                G.fill(G.mask_ellipse(nx + 0.9, cy_ + 0.3, 0.75, 0.8), hexc('1a1214'))
                G.fill(G.mask_ellipse(nx, cy_ + 2.0, 1.4, 0.6), hexc('3a2e28'))
        # one or two arched loculi breaking the bands
        for k in range(1 if x1 - x0 < 60 else 2):
            lx = x0 + (x1 - x0) * (0.3 + 0.4 * k) + rng.uniform(-6, 6); ly = y0 + 22 * rng.integers(1, tiers)
            G.fill(G.mask_poly(arch_pts(lx, 6, ly + 6, ly - 2, ly + 18, pointed=False, n=8)), hexc('5e4a3e'))
            G.fill(G.mask_poly(arch_pts(lx, 4.5, ly + 7, ly + 0.5, ly + 18, pointed=False, n=8)), hexc('0e0a0b'))
    # --- the focal point: a great pointed arch into a receding vault, a lit chapel at its end
    half, spring, apex, bot = 54, 82, 30, 186
    G.fill(G.mask_poly(arch_pts(cx_main, half + 7, spring, apex - 7, bot)), hexc('7c6450'))      # voussoirs, lit
    G.fill(G.mask_poly(arch_pts(cx_main, half + 7, spring, apex - 7, bot)) * (G.X < cx_main), hexc('5a483e'), 0.6)
    G.fill(G.mask_poly(arch_pts(cx_main, half, spring, apex, bot)), hexc('1a1214'))
    vpx, vpy = cx_main + 4, 128                                                                # vanishing point
    for k in range(1, 8):                                                                      # nested receding arch frames
        s = 0.80 ** k
        hh, sp, ap, bt_ = half * s, vpy + (spring - vpy) * s, vpy + (apex - vpy) * s, vpy + (bot - vpy) * s
        cxk = vpx + (cx_main - vpx) * s
        t = 1 - s
        frame = lerp(hexc('4a3a34'), hexc('9a8466'), t)
        inner = lerp(hexc('241a1a'), hexc('6e5a48'), t)
        G.fill(G.mask_poly(arch_pts(cxk, hh * 1.0, sp, ap, bt_)), frame)
        G.fill(G.mask_poly(arch_pts(cxk, hh * 0.86, sp + 1, ap + hh * 0.12, bt_)), inner)
    # receding floor: a lit path running to the chapel
    G.fill(G.mask_poly([(cx_main - half, bot), (vpx - 4, vpy + 24), (vpx + 4, vpy + 24), (cx_main + half, bot)]), hexc('3e302a'), 0.9)
    G.fill(G.mask_poly([(cx_main - 16, bot), (vpx - 2, vpy + 24), (vpx + 2, vpy + 24), (cx_main + 16, bot)]), hexc('6a5644'), 0.7)
    # the chapel door at the far end, and its glow
    G.glow(vpx, vpy + 8, 34, 46, hexc('d8a860'), 0.55, 1.8)
    G.fill(G.mask_poly(arch_pts(vpx, 5.5, vpy + 6, vpy - 4, vpy + 24)), hexc('f0d08a'))
    G.fill(G.mask_poly(arch_pts(vpx, 3, vpy + 9, vpy + 2, vpy + 24)), hexc('fff4d0'))
    # shaft of root-light falling through a crack in the vault onto it
    shaft = G.mask_poly([(vpx - 12, 34), (vpx + 2, 34), (vpx + 7, vpy + 24), (vpx - 3, vpy + 24)], blur=2.5)
    G.add(shaft * (0.6 + 0.4 * smooth(34, 130, G.Y)), hexc('e8c070'), 0.35)
    # secondary: a low side passage with a cold teal glow (x=440) and a collapsed wall where roots pour in (x=70)
    G.fill(G.mask_poly(arch_pts(441, 22, 128, 104, 186, pointed=False)), hexc('5e4a40'))
    G.fill(G.mask_poly(arch_pts(441, 18, 130, 109, 186, pointed=False)), hexc('120d0f'))
    G.glow(446, 160, 22, 26, hexc('46a08a'), 0.55, 1.4)
    G.glow(441, 186, 30, 40, hexc('2a6a5a'), 0.6, 1.2)
    # buttresses in front of the wall, lit on the side that faces the main opening
    for (bx, bw) in ((148, 16), (318, 18), (500, 12)):
        m = G.mask_poly([(bx - bw / 2, 24), (bx + bw / 2, 24), (bx + bw / 2 + 2, 190), (bx - bw / 2 - 2, 190)])
        G.fill(m, hexc('2e2224'))
        face = 1 if bx < cx_main else -1
        G.fill(m * (np.sign(G.wdx(bx)) == face) * (np.abs(G.wdx(bx)) > bw / 2 - 3), hexc('6a5446'))
    # the vault: rock roof and huge golden roots hanging through it
    roof = 6 + 10 * tile_noise(WS, 1, 96, 1, 5)[0] + 8 * (tile_noise(WS, 1, 12, 1, 6, 1)[0] ** 6)
    G.fill((G.Y < roof[None, :] / 1.0).astype(float), hexc('0e0a0b'))
    roots = []
    for (rx, w, n, ln) in ((190, 7, 2, 66), (80, 6, 3, 90), (282, 4, 2, 40), (382, 5, 2, 60), (470, 4, 2, 64), (20, 3, 1, 36)):
        for j in range(n):
            roots += root_segs(rng, rx + rng.uniform(-14, 14), -2, math.pi / 2 + rng.uniform(-0.6, 0.6), ln * rng.uniform(0.7, 1.1), w * (1 - j * 0.25), 2, step=2.0, spread=(0.2, 0.45))
    G.fill(G.mask_lines([(a, b, c, d, w + 1.0) for a, b, c, d, w in roots]), hexc('1e140f'))
    G.fill(G.mask_lines(roots), hexc('4e3422'))
    G.fill(G.mask_lines([(a + 0.5, b, c + 0.5, d, w * 0.45) for a, b, c, d, w in roots if w > 1.5]), hexc('6e4c2c'))
    G.fill(G.mask_lines([(a - w * 0.3, b, c - w * 0.3, d, 0.8) for a, b, c, d, w in roots if w > 2.5]), hexc('b08848'), 0.8)
    # bone-strewn floor and low dust haze over it
    G.fill((G.Y > 186 + 3 * (nz2 - 0.5)).astype(float), hexc('1e1618'))
    G.add(np.exp(-((G.Y - 180) / 10) ** 2) * (0.5 + 0.5 * lit), hexc('3a2e2a'), 0.8)
    return G


def masonry(G, mask, rng, base, lit_x=232, course=6.0, seed=0, light=None):
    """Paint stone blocks into `mask`: running-bond courses, per-block value jitter, dark mortar, faces toward lit_x
    brighter. light: optional per-pixel 0..1 multiplier."""
    yi = np.floor(G.Y / course); off = (yi % 2) * 5.5
    bw = 11.0
    xi = np.floor((G.X + off) / bw)
    jit = np.vectorize(lambda a, b: ((int(a) * 73856093 ^ int(b) * 19349663 ^ seed * 83492791) & 1023) / 1023.0)(xi % (W / bw * 2), yi)
    v = 0.8 + 0.35 * jit
    toward = np.exp(-(G.wdx(lit_x) / 150) ** 2)
    v *= 0.75 + 0.45 * toward
    if light is not None: v *= light
    col = base[None, None] * v[..., None]
    fy = (G.Y / course) % 1; fx = ((G.X + off) / bw) % 1
    mort = (fy < 0.16) | (fx < 0.09)
    col = np.where(mort[..., None], col * 0.45, col)
    top = (fy >= 0.16) & (fy < 0.34)                       # top bevel catches light
    col = np.where(top[..., None] & ~mort[..., None], col * 1.18, col)
    G.fill_img(mask, col)


def guide_mid():
    rng = np.random.default_rng(11)
    G = Guide(hexc('4a4440'), alpha=True)
    stone = hexc('6a5a4e')
    def pier(x, w, top, cap=True, seed=1):
        m = G.mask_poly([(x - w / 2, top), (x + w / 2, top), (x + w / 2 + 2, 206), (x - w / 2 - 2, 206)])
        masonry(G, m, rng, stone, seed=seed)
        side = np.sign(G.wdx(x)) == (1 if x < 232 else -1)
        G.fill(m * side * (np.abs(G.wdx(x)) > w / 2 - 2.5), hexc('9a8470'), 0.8)   # face lit by the distant chapel
        G.fill(m * ~side * (np.abs(G.wdx(x)) > w / 2 - 4), hexc('2a201c'), 0.6)
        if cap:
            G.fill(G.mask_poly([(x - w / 2 - 4, top - 5), (x + w / 2 + 4, top - 5), (x + w / 2 + 2, top + 1), (x - w / 2 - 2, top + 1)]), hexc('8a7462'))
            G.fill(G.mask_lines([(x - w / 2 - 3, top + 1, x + w / 2 + 3, top + 1, 1.0)]), hexc('2a201c'))
    def arch_span(x0, x1, spring, thick, broken_at=None, seed=2):
        cx, half = (x0 + x1) / 2, (x1 - x0) / 2; rise = half * 0.95
        ring = np.clip(G.mask_poly(arch_pts(cx, half + thick, spring, spring - rise - thick, spring + 1, pointed=False, n=40))
                       - G.mask_poly(arch_pts(cx, half, spring + 0.5, spring - rise, spring + 40, pointed=False, n=40)), 0, 1)
        if broken_at is not None:
            side, bx = broken_at
            jag = bx + 5 * (tile_noise(WS, HS, 6, 6, 31, 1) - 0.5)
            ring = ring * ((G.X < jag) if side < 0 else (G.X > jag))
        # voussoirs: radial joints around the arch centre
        dx = G.wdx(cx); dy = G.Y - spring; ang = np.arctan2(-dy, dx); r = np.hypot(dx, dy / 0.95)
        vou = (np.floor(ang / (math.pi / max(8, int(half / 4)))) % 2)
        col = stone[None, None] * (0.85 + 0.25 * vou[..., None]) * (0.8 + 0.4 * np.exp(-(G.wdx(232) / 150) ** 2))[..., None]
        joint = (np.abs(((ang / (math.pi / max(8, int(half / 4)))) % 1) - 0.5) > 0.42) | (np.abs(r - half - thick / 2) > thick / 2 - 0.8)
        col = np.where(joint[..., None], col * 0.5, col)
        G.fill_img(ring, col)
        G.fill(ring * (r < half + 1.6), hexc('a08a72'), 0.7)       # lit intrados
    # piers and arches, irregular rhythm (512 wide, no repeat)
    pier(13, 26, 96, seed=3); arch_span(26, 120, 96, 11, broken_at=(-1, 94), seed=4)
    pier(176, 22, 104, seed=5); pier(306, 22, 104, seed=6); arch_span(187, 295, 104, 13, seed=7)
    pier(384, 16, 140, cap=False, seed=8)                                        # broken pier stub
    G.fill(G.mask_poly([(376, 141), (378, 137), (381, 138), (384, 134), (388, 137), (391, 135), (393, 141)]), hexc('5a4a40'))
    pier(452, 20, 112, seed=9); arch_span(462, 512, 112, 10, seed=10)              # wraps onto the pier at x=13 (=525)
    # fallen voussoirs and a skull pile at the stub, the floor strip
    for (bx, by, r) in ((362, 192, 6), (404, 194, 5), (416, 197, 4), (100, 196, 5)):   # angular fallen blocks
        pts = [(bx + r * 1.5 * math.cos(a) + rng.uniform(-1, 1), by + r * math.sin(a) * (0.6 if math.sin(a) < 0 else 1)) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
        G.fill(G.mask_poly(pts), hexc('5e4e44'))
        G.fill(G.mask_poly([(x, min(y, by - r * 0.1)) for x, y in pts]), hexc('8a7462'), 0.8)
    for k in range(9):
        sx, sy = 396 + rng.uniform(-10, 10), 186 + rng.uniform(-3, 6)
        G.fill(G.mask_ellipse(sx, sy, 2.4, 2.2), hexc('b0a08a')); G.fill(G.mask_ellipse(sx - 0.8, sy + 0.3, 0.7, 0.7), hexc('1a1214')); G.fill(G.mask_ellipse(sx + 0.8, sy + 0.3, 0.7, 0.7), hexc('1a1214'))
    base = 198 + 5 * tile_noise(WS, 1, 32, 1, 41)[0]
    G.fill((G.Y > base[None, :]).astype(float), hexc('3a2e28'))
    # thick root cables draped over the arch extrados and hanging down the faces, plus tails from the intrados
    cables = []
    def drape(cx, spring, R, a0, a1, drop, w, wig=1.5):
        pts = [(cx + R * math.cos(a), spring - R * 0.95 * math.sin(a)) for a in np.linspace(a0, a1, 14)]
        x, y = pts[-1]
        for k in range(1, int(drop / 3) + 1):
            pts.append((x + wig * math.sin(k * 0.9 + cx), y + 3 * k))
        n = len(pts)
        for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
            cables.append((x0, y0, x1, y1, w * (1 - 0.55 * i / n)))
        return pts[-1]
    big = (241, 104, 54 + 13)
    for (a0, a1, drop, w) in ((1.75, 2.55, 40, 4.5), (1.62, 2.75, 66, 3.5), (1.45, 0.6, 30, 4.0), (1.3, 0.75, 70, 2.8), (1.9, 2.2, 22, 2.5)):
        end = drape(*big, a0, a1, drop, w)
        cables.extend(root_segs(rng, end[0], end[1], math.pi / 2 + rng.uniform(-0.3, 0.3), 14, w * 0.4, 1, step=2.0))
    for (cx_, y_, ln, w) in ((222, 56, 34, 2.4), (256, 54, 52, 2.0), (236, 54, 22, 1.6)):   # tails through the crown joints
        cables.extend(root_segs(rng, cx_, y_, math.pi / 2, ln, w, 1, step=2.0, spread=(0.15, 0.3)))
    drape(73, 96, 47 + 11, 1.55, 2.6, 50, 3.6); drape(73, 96, 47 + 11, 1.35, 1.0, 34, 2.6)       # the broken arch
    drape(487, 112, 25 + 10, 1.7, 2.6, 30, 2.6)
    G.fill(G.mask_lines([(a, b, c, d, w + 1.2) for a, b, c, d, w in cables]), hexc('241810'))
    G.fill(G.mask_lines(cables), hexc('6a4a2c'))
    G.fill(G.mask_lines([(a - w * 0.25, b - w * 0.2, c - w * 0.25, d - w * 0.2, max(0.7, w * 0.3)) for a, b, c, d, w in cables]), hexc('a07a44'), 0.8)
    return G


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image()).save(f'{SRC}/edge_far.png')
    m = guide_mid(); m.image().save(f'{SRC}/guide_mid.png'); m.alpha_img().save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m.image(), lo=10).save(f'{SRC}/edge_mid.png')
    # a 1x preview of both (far + keyed mid) for checking the composition
    far1 = box_down(f.image()); mid1 = box_down(m.image()); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')




# -------------------------------------------------------------------------------------------------- render + build
RENDER = {   # the picked settings (see docs/v17/bg_pilot.md); seeds were picked by eye from a sweep
    'far': dict(prompt=PROMPT_FAR, seed=2, denoise=0.8, cn=0.45, cn_end=0.6, pix=0.6, guide_blur=1.5),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.6, cn=0.5, cn_end=0.7, pix=0.6, guide_blur=1.0, seam_band=96),
}
TINT = '#0a0c10'


def do_render():
    times = {}
    for layer, kw in RENDER.items():
        times[layer] = round(render_layer(SRC, layer, **kw), 1)
    json.dump(times, open(f'{SRC}/render_times.json', 'w')); print('render s', times)


def far_post(a, stage):
    if stage != 'hi': return a
    # value structure for the game: darker roof and floor, the light pooled around the arch, nothing near-black in between
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]] / S
    dx = (xx - 236 + W / 2) % W - W / 2
    pool = np.exp(-(dx / 120) ** 2) * np.exp(-((yy - 125) / 90) ** 2)
    k = (0.86 + 0.4 * pool) * (0.72 + 0.28 * smooth(0, 40, yy)) * (1 - 0.3 * smooth(186, 216, yy))
    return np.clip(a * k[..., None], 0, 255)


def build(ase=True):
    far, acc_f = far_pipeline(f'{SRC}/far_render.png', FAR_PAL, n_acc=8, grade_kw=dict(black=6, white=228, gamma=1.25, sat=0.92), post=far_post)
    mid, al, acc_m = mid_pipeline(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', MID_PAL, n_acc=3,
                                  grade_kw=dict(black=14, white=360, gamma=0.85, sat=0.6), rim_col=hexc('6a5440'))
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
