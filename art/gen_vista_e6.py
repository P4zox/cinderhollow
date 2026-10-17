#!/usr/bin/env python3
"""E6 The Last Hearth: the vista (docs/v17/vista_v3.md). Seen through the hall's broken window, and dimly across it.

Outside the only warm room left in the Hallow: the ember hollow at night. Far off, the ember lake lights the underside of
the vault; the Pale Root's taproots come down out of the dark into the lake like burning pillars, cracks glowing, smoke
climbing off them; basalt columns stand in the glow; ash drifts. The hearth is warm, the world outside is ending slowly.
After SAVE.flags['w2:open'] the furnace stands open and no one keeps the fire: the hearth burns low (82_forge.js) and the
view answers it. The taproots have gone out (grey and cold, a last red in the deepest cracks), the lake is a dull ember
crust, and a pale cold light has come up far off on the horizon, from wherever that draught comes from.

  python3 art/gen_vista_e6.py [--guide | --sweep <far|mid> 1,2,3 [tag] | --pick <name> <seed> [tag] | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from vista_v3lib import *  # noqa
import vista_v3lib as L

ROOM = 'E6'; SRC = src_dir(ROOM)
LW, LH = 512, 240
TINT = '#0c0606'
LAKE_Y = 168
ROOTS = [(100, 24, 0.02), (156, 11, 0.08), (58, 8, -0.06), (318, 10, -0.05)]   # x at the lake, width, lean


def vault(C):
    nz = C.noise(60, 30, 3); nz2 = C.noise(16, 10, 4)
    C.rgb = C.vgrad([(0, '080404'), (60, '120808'), (120, '2a120c'), (150, '5a2414'), (165, '9a4018'), (172, 'c85a20'), (180, '5a2414'), (240, '1a0a08')])
    C.add(np.exp(-((C.X - 110) / 120) ** 2) * np.exp(-((C.Y - 150) / 40) ** 2), hexc('a04018'), 0.45)   # the lake's light on the vault
    # smoke banks under the vault, lit from below
    for (y0, y1, cx, cy, sd, lo, hi, k) in ((20, 80, 110, 16, 31, '160a08', '3a1a12', 0.8), (70, 130, 90, 12, 32, '2a120c', '7a3018', 0.75),
                                          (110, 158, 80, 8, 33, '4a1e12', 'b04a1c', 0.7)):
        d = C.noise(cx, cy, sd, 3); band = smooth(y0, y0 + 12, C.Y) * (1 - smooth(y1 - 12, y1, C.Y))
        m = smooth(0.48, 0.62, d) * band
        C.fill_img(m, lerp(hexc(lo), hexc(hi), smooth(y0, y1 + 20, C.Y)[..., None] * (0.6 + 0.6 * nz2[..., None])), k)
    return C


def root_segs(x, w, lean):
    segs = []; y = LAKE_Y + 4.0; xx = x
    while y > -10:
        ny = y - 3; nx = xx + lean * 3 + 0.8 * math.sin(y / 17 + x)
        ww = w * (1 + 0.5 * smooth(60, -10, ny)) + 2 * math.sin(y / 9)                # thicker toward the vault
        segs.append((xx, y, nx, ny, max(2, ww))); xx, y = nx, ny
    return segs


def _chain(pts, widths, wob=0.0, seed=0):
    """A polyline through pts (sampled every ~3 px, a little wobble), widths interpolated along it."""
    out = []; L = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]): L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    n = max(2, int(L[-1] / 3)); prev = None
    for i in range(n + 1):
        d = L[-1] * i / n; k = max(j for j in range(len(L)) if L[j] <= d) if d < L[-1] else len(L) - 2; k = min(k, len(pts) - 2)
        t = (d - L[k]) / max(1e-6, L[k + 1] - L[k]); x = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * t; y = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t
        x += wob * math.sin(d / 9 + seed) + 0.5 * wob * math.sin(d / 3.7 + 2 * seed)
        w = float(np.interp(i / n, np.linspace(0, 1, len(widths)), widths))
        if prev: out.append((prev[0], prev[1], x, y, w))
        prev = (x, y)
    return out


# (lead review 2: the root crown read as a giant spider.) One massive gnarled taproot out of the vault, leaning a little,
# tapering as it goes down; near the lake it parts into three roots of unequal length that plunge straight DOWN into the
# lava, and a few thin rootlets hang and trail from its flanks, ending in the air. No bulge where it parts.
ROOT_FEET = ((113, 22), (128, 8), (90, 9))       # x at the waterline, width there (the three roots that reach the lake)


def taproot_chains():
    ly = LAKE_Y + 6
    trunk = _chain([(84, -14), (88, 30), (96, 70), (104, 104), (110, 128), (113, 150), (113, ly)],
                   [56, 50, 46, 40, 36, 33, 30, 28, 26, 24, 23, 22], wob=1.6, seed=1)      # the trunk itself goes on into the lava
    gn = []
    for i, (x0, y0, x1, y1, w) in enumerate(trunk):       # gnarled: the girth swells and pinches as it goes down
        gn.append((x0, y0, x1, y1, w * (1 + 0.1 * math.sin(i * 0.55) + 0.06 * math.sin(i * 1.7 + 1))))
    chains = [gn]
    chains.append(_chain([(94, 92), (91, 120), (90, 145), (90, ly)], [12, 10, 9, 9], wob=0.7, seed=5))    # a long root off the left flank
    chains.append(_chain([(120, 146), (126, 156), (128, ly)], [9, 8, 8], wob=0.4, seed=7))              # a short one, low on the right
    for x0, y0, x1, y1, w in ((90, 58, 79, 126, 3.0), (124, 96, 136, 140, 2.6), (106, 118, 99, 146, 1.8)):    # thin rootlets, hanging
        chains.append(_chain([(x0, y0), ((x0 + x1) / 2 + (x1 - x0) * 0.3, (y0 + y1) / 2), (x1, y1)], [w, w * 0.8, 0.9], wob=0.9, seed=x0))
    return chains


FAR_COLS = ((30, 6, 26, 0.5), (220, 8, 34, 0.55), (420, 7, 22, 0.45), (250, 5, 16, 0.75), (470, 4, 30, 0.6))
NEAR_COLS = ((-6, 5, 70), (196, 4, 30), (330, 6, 46), (470, 6, 60))


def far_columns():
    rng = np.random.default_rng(5); out = []
    for gx, n, h0, sh in FAR_COLS:
        for i in range(n):
            x = gx + i * rng.uniform(3, 5); h = h0 * rng.uniform(0.5, 1.1); w = rng.uniform(2.5, 4); out.append((x, h, w, sh))
    return out


def near_columns():
    rng = np.random.default_rng(9); out = []
    for gx, n, h0 in NEAR_COLS:
        for i in range(n):
            x = gx + i * rng.uniform(5, 7); h = h0 * rng.uniform(0.6, 1.1); w = rng.uniform(5, 7); out.append((x, h, w))
    return out


# the crisp 1x pass (lead review): the taproot as a clear dark silhouette with ember-lit edges and a defined foot in the
# lake, and faceted basalt columns, drawn over the palette-locked render. Same shapes in both states, colours per state.
CR = {'': dict(core=['0a0404', '120806', '1a0c0a', '22100c'], rim=['5a2414', '8a3418', 'c85a20', 'f0a040'], fis=['b04a1c', 'e88030', 'f4b458'],
               foot='f4b458', ref='2a1210', col=['140808', '22100c', '3a1a14', '6a2614', '8a3418'], base='a04018'),
      'cold': dict(core=['080606', '0e0a0a', '141010', '1a1414'], rim=['221a1a', '2a2424', '3a3232', '4a4040'], fis=['2a1210', '3a1a14', '4a1e12'],
                   foot='4a4040', ref='141010', col=['0c0a0a', '141010', '1e1a1a', '2e2828', '3a3232'], base='2a2424')}


def draw_taproot(q, al, cold):
    c = CR['cold' if cold else '']; P = lambda k: hexc(k)
    inside, u, along, hw, ch = seg_field(taproot_chains(), LW, LH)
    inside &= np.arange(LH)[:, None] <= LAKE_Y + 3                     # the roots go INTO the lava: cut at the waterline
    yy = np.arange(LH)[:, None] * np.ones((1, LW))
    nz = noise(LW, LH, 6, 18, 71, 2)
    # core: dark, a slow value roll across the limb (backlit: darkest in the middle), furrows along it
    v = np.clip(0.55 * np.abs(u) ** 1.5 + 0.25 * (nz - 0.5), 0, 0.99)
    core = np.array([P(k) for k in c['core']])[(v * 3.99).astype(int)]
    fur = (np.abs(((u * hw / 3.2) + 0.35 * np.sin(along / 11 + ch * 2.1)) % 1 - 0.5) < 0.13) & (np.abs(u) < 0.8)
    core = np.where(fur[..., None], P(c['core'][0]), core)
    out = np.where(inside[..., None], core, q)
    # rim: the lake glow behind lights both edges, brighter toward the lake
    hk = np.clip((yy - 10) / (LAKE_Y - 10), 0, 1)                                      # 0 at the vault .. 1 at the lake
    edge = inside & (np.abs(u) * hw > hw - 1.1)
    edge2 = inside & ~edge & (np.abs(u) * hw > hw - 2.1) & (hk > 0.45) & (hw > 5)
    ri = np.clip((hk * 3.2 + 0.4 * (nz - 0.5) - (hw < 4) * 1.0).astype(int), 0, 3)
    rimc = np.array([P(k) for k in c['rim']])
    out = np.where(edge[..., None], rimc[ri], out)
    out = np.where(edge2[..., None], rimc[np.clip(ri - 2, 0, 3)], out)
    # fissures: a few thin seams following the limb, broken, glowing hotter toward the lake
    fis = np.zeros((LH, LW), bool)
    for k, (u0, ph) in enumerate(((-0.35, 0.0), (0.1, 1.7), (0.45, 3.1), (-0.05, 4.4))):
        uk = u0 + 0.22 * np.sin(along / (13 + 4 * k) + ph)
        on = np.abs(u - uk) * hw < 0.55
        brk = noise(LW, LH, 4, 9, 80 + k, 1) > 0.42
        fis |= inside & on & brk & (np.abs(u) < 0.7) & ((ch == 0) | ((k == 1) & (hw > 4.5)))
    fi = np.clip((hk * 2.9).astype(int), 0, 2); fisc = np.array([P(k) for k in c['fis']])
    out = np.where(fis[..., None], fisc[fi], out)
    # the foot: where each rootlet enters the lake, a hot meniscus; under it, its dark rippled reflection
    for fx, wd in ROOT_FEET:
        r = int(wd / 2 + 2); ly = LAKE_Y + 4
        for xx in range(fx - r, fx + r + 1):
            if 0 <= xx < LW: out[ly, xx] = P(c['foot']); al[ly, xx] = True
        for dy in range(1, 14):
            rr = max(1, int(wd / 2 * (1 - dy / 16))); sh = int(round(1.5 * math.sin(dy * 1.3 + fx)))
            if dy % 3 == 2: continue
            for xx in range(fx - rr + sh, fx + rr + sh + 1):
                if 0 <= xx < LW and ly + dy < LH: out[ly + dy, xx] = P(c['ref']); al[ly + dy, xx] = True
    al |= inside
    return out


def draw_columns(q, al, cols, base_y, cold, near=False):
    """Faceted basalt columns, crisp: a lit facet toward the lake glow (x 104), a mid facet, a dark facet, a lit cap."""
    c = CR['cold' if cold else '']['col']; P = lambda k: hexc(k)
    for col in cols:
        x, h, w = col[0], col[1], col[2]
        x0, x1 = int(round(x)), int(round(x + w)); top = int(round(base_y - h)); ww = max(2, x1 - x0)
        lit_left = (x + w / 2) > 104
        for xx in range(x0, x0 + ww):
            if not 0 <= xx < LW: continue
            f = (xx - x0) / ww; f = f if lit_left else 1 - f            # 0 = the lit side
            k = 3 if f < 0.34 else (1 if f < 0.67 else 0)
            if near: k = max(0, k - 1)
            cap = top + (1 if abs(xx - (x0 + ww / 2)) > ww / 4 else 0)
            for yy in range(max(0, cap), min(LH, int(base_y) + (LH if near else 2))):
                kk = k if yy > cap + 1 else min(4, k + 1)
                if not near and yy > base_y - 3: kk = min(4, k + 1)       # the lake light on the foot
                out_c = P(c[kk]); q[yy, xx] = out_c; al[yy, xx] = True
        for xx in range(x0, x0 + ww - 1):                                # a joint line across the column now and then
            for jy in range(top + 6, int(base_y), 9 + int(w) % 4):
                if 0 <= xx < LW and 0 <= jy < LH and (x0 * 7 + jy * 13) % 3: q[jy, xx] = P(c[0])
    return q


def land(C, cold=False):
    """The far plane: taproots, the lake, basalt columns in the glow (cover = far layer)."""
    cov = np.zeros_like(C.X)
    nz = C.noise(8, 40, 51, 2)
    # far basalt columns standing in the lake glow (groups at two depths)
    rng = np.random.default_rng(5)
    for gx, n, h0, sh in FAR_COLS:
        for i in range(n):
            x = gx + i * rng.uniform(3, 5); h = h0 * rng.uniform(0.5, 1.1); w = rng.uniform(2.5, 4)
            m = C.mask_poly([(x, LAKE_Y + 2), (x + w, LAKE_Y + 2), (x + w, LAKE_Y - h + 1), (x + w * 0.5, LAKE_Y - h), (x, LAKE_Y - h + 1)])
            C.fill(m, lerp(hexc('1a0c0a'), hexc('3a1a12'), sh)); C.fill(m * (C.X < x + 1), hexc('7a3018'), 0.6); cov = np.maximum(cov, m)
    # the lake: molten under a crust, brightest far, mirror of the vault glow
    lake = C.mask_poly([(-5, LAKE_Y), (LW + 5, LAKE_Y), (LW + 5, LH + 2), (-5, LH + 2)])
    v = np.exp(-((C.X - 110) / 160) ** 2) * (1 - smooth(LAKE_Y, LH, C.Y))
    crust = smooth(0.45, 0.6, C.noise(10, 3, 52, 3))
    lc = lerp(hexc('3a1410'), hexc('f8a040'), (np.clip(v * 1.2 * (1 - 0.55 * crust), 0, 1) ** 1.0)[..., None])
    C.fill_img(lake, lc); cov = np.maximum(cov, lake)
    # the great taproot: one colossal charred root out of the vault, splitting into rootlets that plunge into the lake;
    # two more far off in the haze
    segs = [q for ch in taproot_chains() for q in ch]
    m = C.mask_lines(segs)
    C.fill_img(m, lerp(hexc('140808'), hexc('2e1410'), smooth(0, LAKE_Y, C.Y)[..., None])); cov = np.maximum(cov, m)
    C.fill(m * (C.X < np.interp(C.Y, [0, 110, 170], [84, 82, 60]) + 3), hexc('6a2614'), 0.5)      # the lake's light on its flank
    vn = C.noise(6, 22, 61, 3)
    C.fill(m * np.clip(1 - np.abs(vn - 0.5) / 0.03, 0, 1) * smooth(-10, 150, C.Y), hexc('f08a30') if not cold else hexc('5a2018'), 0.95)
    C.fill(m * smooth(LAKE_Y - 40, LAKE_Y, C.Y), hexc('e86a20') if not cold else hexc('3a1a14'), 0.7)
    C.glow(104, LAKE_Y, 70, 14, hexc('f8b050'), 0.0 if cold else 0.6, 1.3)
    for x, w, lean in ((292, 9, -0.04), (356, 6, 0.05)):
        mm = C.mask_lines(root_segs(x, w, lean))
        C.fill(mm, hexc('3a1a12')); cov = np.maximum(cov, mm)
        C.fill(mm * smooth(LAKE_Y - 30, LAKE_Y, C.Y), hexc('a04018'), 0.6)
    # reflections of the glow in the molten lake
    C.add(lake * np.exp(-((C.X - 104) / 22) ** 2) * smooth(LAKE_Y, LAKE_Y + 6, C.Y) * (1 - smooth(LAKE_Y, LH, C.Y)) * (0.5 + crust * 0.0 + 0.6 * C.noise(14, 2, 62, 2)), hexc('f8c870'), 0.5)
    return cov


def near(C):
    """Near basalt columns along the bottom and the left edge (cover = mid)."""
    cov = np.zeros_like(C.X); rng = np.random.default_rng(9)
    for gx, n, h0 in NEAR_COLS:
        for i in range(n):
            x = gx + i * rng.uniform(5, 7); h = h0 * rng.uniform(0.6, 1.1); w = rng.uniform(5, 7)
            top = LH - 12 - h
            m = C.mask_poly([(x, LH + 2), (x + w, LH + 2), (x + w, top + 2), (x + w * 0.5, top), (x, top + 2)])
            C.fill(m, hexc('120806')); C.fill(m * (C.X < x + 1.2), hexc('6a2614'), 0.8); C.fill(m * (C.Y < top + 2.2), hexc('8a3418'), 0.7)
            cov = np.maximum(cov, m)
    return cov


def guides():
    gf = vault(Canvas(LW, LH)); cf = land(gf); gf.save(f'{SRC}/guide_far.png'); Image.fromarray((np.clip(cf, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_far.png')
    edges(gf.image()).save(f'{SRC}/edge_far.png')
    gm = vault(Canvas(LW, LH)); land(gm); cm = near(gm); gm.save(f'{SRC}/guide_mid.png'); Image.fromarray((np.clip(cm, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_mid.png')
    edges(gm.image()).save(f'{SRC}/edge_mid.png')
    gm.image().save(f'{SRC}/guide_preview.png')


PROMPT = ('pixel art, dark fantasy, a vast volcanic cavern at night, one colossal charred tree taproot hanging from the dark cavern '
          'vault down into a glowing molten ember lake, glowing cracks in the charred roots, smoke rising, groups of hexagonal '
          'basalt columns silhouetted against the lake glow, ash drifting, deep red and orange embers, atmospheric haze, '
          'melancholy, highly detailed')
RENDER = {
    'far': (PROMPT, dict(denoise=0.5, pix=0.45, edge=True, cn=0.5, cn_end=0.7)),
    'mid': (PROMPT + ', dark basalt columns in the foreground', dict(denoise=0.48, pix=0.5, edge=True, cn=0.55, cn_end=0.7)),
}
PAL = ['080404', '0c0606', '120806', '1a0c0a', '22100c', '2a1210', '3a1a14', '4a1e12', '5a2414', '6a2614', '7a3018', '8a3418',
       'a04018', 'b04a1c', 'c85a20', 'e06a24', 'e88030', 'f09038', 'f0a040', 'f4b458', '2a2424', '3a3232', '4a4040', '6a6060', '2e343e', '444e5a', '5e6a78', '7e8a98', 'a0aab6']


def cold_grade(a, rk):
    """The fire gone out (w2:open): the vault's light falls away, the oranges drain to ash-grey and dull red, the roots go
    cold; a pale cold light rises far off on the horizon (right of the taproot, where the draught comes from)."""
    lum = a.mean(2, keepdims=True)
    grey = lum * np.array([1.0, 0.92, 0.9]) * 0.55
    ember = a * np.array([0.55, 0.28, 0.2])
    out = grey * 0.65 + ember * 0.35
    h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; sc = w / LW
    dx = (xx / sc - 300) / 90; dy = yy / sc - (LAKE_Y - 3)
    cold = np.exp(-dx ** 2) * np.exp(-(dy / np.where(dy < 0, 16, 5)) ** 2)            # a thin band on the horizon, a soft glow above it
    out = out * (1 - 0.5 * cold[..., None]) + cold[..., None] * np.array([150, 166, 184]) * 0.5
    return np.clip(out, 0, 255)


def build(ase=True):
    rng = np.random.default_rng(6)
    for variant in ('', 'cold'):
        a = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
        a = knee(grade(a, black=2, white=250, gamma=0.95, sat=1.05), 150, 0.4, 'e88030', 0.7)     # the lake's heart orange-gold, not a flat yellow
        if variant: a = cold_grade(a, None)
        s = down(a, LW, LH); cov = cover_alpha(f'{SRC}/cover_far.png', LW, LH, 0.02)
        sk = fill_under(s, np.asarray(Image.fromarray((cov * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), float) > 0)
        q, _ = pixelize(sk, PAL, n_acc=4, dk=0.3); sky_im = to_rgba(q)
        al = cover_alpha(f'{SRC}/cover_far.png', LW, LH)
        q, _ = pixelize(s, PAL, n_acc=4, dk=0.25, mask=al); al = al.copy()
        old = cover_alpha(f'{SRC}/cover_far.png', LW, LH, 0.15)            # the guide's (old) root, as the render painted it
        yy, xx = np.mgrid[0:LH, 0:LW]
        al &= ~(old & (yy < LAKE_Y + 2) & (xx >= 36) & (xx <= 180))      # cleared: the sky layer's haze shows; columns + root redrawn below
        draw_columns(q, al, far_columns(), LAKE_Y + 2, bool(variant))
        q = draw_taproot(q, al, bool(variant))
        far_im = to_rgba(np.where(al[..., None], q, 0), al)
        a = np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float)
        a = knee(grade(a, black=8, white=255, gamma=0.85, sat=0.95), 200, 0.55)
        if variant: a = cold_grade(a, None)
        s = down(a, LW, LH); al = cover_alpha(f'{SRC}/cover_mid.png', LW, LH)
        q, _ = pixelize(s, PAL, n_acc=3, dk=0.2, mask=al, dither=False); al = al.copy()
        draw_columns(q, al, [(x, h, w) for x, h, w in near_columns()], LH - 12, bool(variant), near=True)
        mid_im = to_rgba(np.where(al[..., None], q, 0), al)
        ims = {'sky' + variant: sky_im, 'far' + variant: far_im, 'mid' + variant: mid_im}
        for k, im in ims.items(): im.save(f'{SRC}/out_{k}.png')
        preview([(sky_im, 0.02, 0.03, {}), (far_im, 0.05, 0.04, {}), (mid_im, 0.12, 0.08, {})], TINT, f'{SRC}/preview{variant}.png', [(0, 72), (120, 72), (0, 0)])
        if ase:
            for k, im in ims.items(): L.build(f'vista_e6_{k}', [im])


if __name__ == '__main__':
    cli(ROOM, SRC, guides, RENDER, build)
