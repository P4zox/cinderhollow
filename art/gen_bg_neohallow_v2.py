#!/usr/bin/env python3
"""NEO-HALLOW backdrop v2 (docs/v17/neohallow_upgrade.md): the rain-soaked vertical megacity behind every NH room.

  python3 art/gen_bg_neohallow_v2.py            build bg_neohallow_{far,mid} (uses art/bg_src/neohallow/far_render.png if present)
  python3 art/gen_bg_neohallow_v2.py --guide    only (re)paint the far sky guide
  python3 art/gen_bg_neohallow_v2.py --render [seed]   re-render the sky (ComfyUI on :8188, prefix neo/), then build
  --no-ase                                       write previews only, leave the assets alone

Same names, size (512x216), tag `loop` and 4 frames as art/gen_neo_env.py (which still builds the cyber layers and the
v1 set for rollback). Values are composed for the rooms: the rooftop floors cover the layers below y ~168, so the
fog glow peaks just above that and the skyline layers stand against it.

Far (scroll 0.08): the sky and cloud deck lit from below (ComfyUI img2img over the painted guide at low denoise, for
the cloud texture), then drawn at 1x: three depths of towers fading into a magenta / cyan fog (each nearer depth darker,
with more lights), Arcology Zero (the megastructure the World 2 Megacity grows into) with its crown in the cloud, and
the petrified Pale Root rising through the city into the cloud. Holo boards glow into the fog. The 4 frames only blink
the red aviation lights.
Mid (scroll 0.3): near towers drawn at 1x: dark glass curtain walls (floor slabs, mullions, offices lit in clusters),
neon signs that light the walls around them, rim light, skybridges, tanks, vents, masts, their feet lost in the street
fog. Gaps between them show the far city. No figures, no text, no real brands.
The motion (traffic, searchlights, sign stutter, steam) is drawn by 36_neohallow.js nhParallax at the points this
script writes to art/bg_src/neohallow/fx.json (copied into the code as NH_BGFX).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bgv2lib as V  # noqa: E402
from bgv2lib import Guide, hexc, lerp, smooth, tile_noise, S, W  # noqa: E402
import nh2lib as N  # noqa: E402
from nh2lib import B4, CYAN, MAG, AMBER, RED, glyph_panel, ramp  # noqa: E402

LH = 216
B = 'neohallow'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#05050d'
ROOT_X = 336          # the Pale Root (far layer x)
ARC_X = 120           # Arcology Zero's axis
FX = {}
YY, XX = np.mgrid[0:LH, 0:W].astype(float)
OWN = np.zeros((LH, W), int)       # which piece painted each far pixel last (a window only shows on its own tower)
NID = [0]


def own(m):
    NID[0] += 1; OWN[m] = NID[0]; return NID[0]


def wdx(cx):
    return (XX - cx + W / 2) % W - W / 2


# =========================================================================== the fog / sky model (1x, smooth)
FOG_ROWS = [(0, '05060f'), (28, '080919'), (60, '0e0c26'), (92, '181232'), (118, '28173f'), (140, '3c1d4e'), (156, '55245c'),
            (168, '6c2c66'), (180, '7a3268'), (196, '6a2c62'), (216, '4a2252')]


def fog():
    ys = np.array([r[0] for r in FOG_ROWS], float); cs = np.array([hexc(r[1]) for r in FOG_ROWS])
    F = np.stack([np.interp(YY, ys, cs[:, i]) for i in range(3)], -1)
    teal = np.exp(-(wdx(ARC_X - 10) / 120) ** 2)[..., None] * smooth(90, 175, YY)[..., None]
    F = F * (1 - 0.55 * teal) + hexc('1c4a62') * 0.55 * teal * (0.6 + 0.6 * smooth(120, 175, YY)[..., None])
    mg = np.exp(-(wdx(ROOT_X + 50) / 140) ** 2)[..., None] * smooth(120, 178, YY)[..., None]
    F = F + hexc('3a0c34') * 0.6 * mg
    l = F.mean(2, keepdims=True); F = l + (F - l) * 0.85
    return np.clip(F, 0, 255)


# =========================================================================== far: the painted sky (guide -> render)
def guide_far():
    G = Guide()
    F = fog()
    G.rgb = np.asarray(Image.fromarray(F.astype(np.uint8)).resize((V.WS, V.HS), Image.BICUBIC), float)
    cl = tile_noise(V.WS, V.HS, 128 * S, 18 * S, 11, 4); cl2 = tile_noise(V.WS, V.HS, 32 * S, 6 * S, 12, 3)
    band = smooth(10, 30, G.Y) * (1 - smooth(80, 104, G.Y))
    d = cl * 0.72 + cl2 * 0.28
    m = smooth(0.45, 0.6, d) * band
    lo = np.interp(G.Y, [10, 60, 100], [0.1, 0.45, 0.85])[..., None]
    G.fill_img(m, lerp(hexc('0b0a1c'), hexc('3a2452'), lo), 0.95)
    under = np.clip(m - np.roll(m, int(-4 * S), axis=0), 0, 1)
    side = np.clip(0.5 + 0.5 * np.cos((G.X - ARC_X) / W * 2 * np.pi), 0, 1)[..., None]
    G.add(under, lerp(hexc('a04a8a'), hexc('3a8aa8'), side * 0.8), 0.5)
    G.add(smooth(64, 104, G.Y) * band * smooth(0.4, 0.62, d), hexc('6a2a6a'), 0.25)
    st = tile_noise(V.WS, V.HS, 64 * S, 3 * S, 14, 2)
    G.fill(smooth(0.6, 0.7, st) * (1 - smooth(8, 24, G.Y)), hexc('100d24'), 0.8)
    # rain curtains: long faint slanted streaks in the fog (the model keeps them as texture)
    rn = tile_noise(V.WS, V.HS, 2 * S, 90 * S, 15, 1)
    G.add(smooth(0.8, 0.95, rn) * smooth(90, 160, G.Y), hexc('2a1838'), 0.35)
    G.image().save(f'{SRC}/guide_far.png')
    V.edges_of(G.image(), lo=10).save(f'{SRC}/edge_far.png')
    return G


PROMPT_FAR = ('pixel art, night sky over a vast cyberpunk megacity in heavy rain, low clouds lit magenta and cyan from below by the '
              'city lights, rain haze, glowing pink fog, atmospheric depth, melancholy, cinematic, side-scroller game background, '
              'deep navy and violet palette with magenta glow, highly detailed, no people')
RENDER = dict(seed=4, denoise=0.42, cn=0.42, cn_end=0.6, pix=0.4)


def render(seed=None):
    sys.path.insert(0, os.path.expanduser('~/Claude/pixelgen'))
    import comfy
    run0 = comfy.run

    def run(wf, out):
        for n in wf.values():
            if n.get('class_type') == 'SaveImage': n['inputs']['filename_prefix'] = 'neo/bg_far'
        return run0(wf, out)
    comfy.run = run
    r = dict(RENDER); s = r.pop('seed') if seed is None else seed
    t = V.render_layer(SRC, 'far', PROMPT_FAR, s, r['denoise'], r['cn'], r['cn_end'], r['pix'], guide_blur=1.2)
    print('rendered far seed', s, round(t, 1), 's')


# =========================================================================== far: the city in three depths (1x)
def skyline(rng, x0, x1, top_lo, top_hi, w_lo, w_hi, gap=(-2, 4), avoid=()):
    out = []; x = x0
    while x < x1:
        w = float(rng.uniform(w_lo, w_hi)); top = float(rng.uniform(top_lo, top_hi))
        for ax, r, dt in avoid:
            if abs(((x + w / 2 - ax + W / 2) % W) - W / 2) < r: top += dt
        kind = int(rng.choice([0, 0, 1, 2, 3], p=[0.45, 0.15, 0.2, 0.08, 0.12]))
        sb = [(int(rng.integers(5, 14)), int(rng.integers(1, 3)))] if w > 12 and rng.random() < 0.45 else []
        out.append(dict(x=x, w=w, top=top, kind=kind, setbacks=sb, mast_at=float(rng.uniform(0.25, 0.75)), mast=bool(rng.random() < 0.55)))
        x += w + float(rng.uniform(*gap))
    return out


def tower_mask(T):
    m = np.zeros((LH, W), bool)
    segs = sorted([(T['top'], T['x'], T['w'])] + [(T['top'] + dy, T['x'] - i, T['w'] + 2 * i) for dy, i in T.get('setbacks', [])])
    for k, (y0, x, w) in enumerate(segs):
        y1 = segs[k + 1][0] if k + 1 < len(segs) else LH
        xs = wdx(x + w / 2)
        m |= (np.abs(xs + 0.5) <= w / 2) & (YY >= round(y0)) & (YY < y1)
    top, x, w, kind = T['top'], T['x'], T['w'], T['kind']
    cx = x + w / 2; ax = np.abs(wdx(cx) + 0.5)
    if kind == 1:
        for i in range(3): m |= (ax <= w / 2 - 1 - i * 2) & (YY >= round(top) - 2 - 2 * i) & (YY < round(top) - 2 * i)
    elif kind == 2:
        h = w * 0.9; t = (top - YY) / h
        m |= (YY < round(top)) & (t >= 0) & (t < 1) & (ax <= np.maximum(0.5, w * 0.22 * (1 - t)))
    elif kind == 3:
        m |= (ax <= w / 2 + 1) & (YY >= round(top) - 2) & (YY < round(top))
    if T.get('mast'):
        mx = x + w * T['mast_at']; mh = 5 + w * 0.35; base = top - (w * 0.9 if kind == 2 else 6 if kind == 1 else 2)
        m |= (np.abs(wdx(mx) + 0.5) < 0.5) & (YY >= round(base - mh)) & (YY < round(base) + 1)
        T['tip'] = (int(round(mx)) % W, int(round(base - mh)) - 1)
    return m


DEPTH = [  # opacity over the fog (top, bottom), lit window density, window colour mix toward the fog
    dict(k=(0.3, 0.06), lit=0.05, wk=0.35, dark='1c1234'),
    dict(k=(0.55, 0.18), lit=0.1, wk=0.55, dark='130e28'),
    dict(k=(0.8, 0.42), lit=0.2, wk=0.8, dark='0b0918'),
]
WINC = [('c08040', 6), ('e0a050', 3), ('a8b0c8', 2), ('3fe0ff', 0.5), ('ff8ad8', 0.4)]


def paint_depth(base, F, towers, d, rng, lights, floor_h=3):
    D = DEPTH[d]; dark = hexc(D['dark'])
    for T in towers:
        m = tower_mask(T)
        bot = 176
        t = smooth(T['top'], bot, YY)
        k = D['k'][0] * (1 - t) + D['k'][1] * t
        col = F * (1 - k[..., None]) + dark * k[..., None]
        # shadow side + a faint rim on the lit side (the fog glow wraps the edges)
        xs = wdx(T['x'] + T['w'] / 2) + 0.5
        sh = (xs > T['w'] / 2 - max(1, T['w'] / 4))
        col = np.where(sh[..., None], col * 0.88, col)
        base[:] = np.where(m[..., None], col, base); oid = own(m)
        # lit windows: floors x columns, offices cluster
        top = int(round(T['top'])); x0 = int(round(T['x']))
        for fy in range(top + 3, 200, floor_h):
            mode = rng.random(); p = D['lit'] * (0.3 if mode < 0.3 else 2.2 if mode > 0.94 else 1.0)
            grp = rng.random(8)
            for cx in range(x0 + 1, x0 + int(T['w']) - 1, 2):
                if not m[fy, cx % W] or not m[fy, (cx + 1) % W] or not m[fy, (cx - 1) % W]: continue
                if rng.random() < p * (0.3 + 1.4 * grp[((cx - x0) // 6) % 8]):
                    cs, ws = zip(*WINC); c = hexc(cs[rng.choice(len(cs), p=np.array(ws) / sum(ws))])
                    kk = D['wk'] * (1 - 0.6 * smooth(T['top'], 190, fy))
                    lights.append((cx % W, fy, base[fy, cx % W] * (1 - kk) + c * kk, oid))
        if T.get('tip') and d >= 1: FX.setdefault('far_blink', []).append(list(T['tip']))


def draw_root(base, F, rng):
    """The Pale Root: a colossal petrified trunk rising out of the city into the cloud, far beyond the towers. Violet-grey
    bark hazed by distance, furrows along the limb, neon rim light (cyan left, magenta right) brighter toward the city,
    its foot drowned in fog, its crown and limbs cut away by the cloud deck."""
    from vista_v3lib import seg_field, noise
    trunk = []; x, y = ROOT_X, 236.0
    for i in range(72):
        t = i / 72; nx = x + 0.1 + 0.4 * math.sin(i / 9); ny = y - 3.4
        trunk.append((x, y, nx, ny, 62 * (1 - 0.38 * t) + 16 * (1 - smooth(0, 0.16, t)))); x, y = nx, ny
    chains = [trunk]
    for frac, ang, ln, w in ((0.74, -0.7, 34, 15),):
        ch = []; px_, py = trunk[int(frac * 71)][0], trunk[int(frac * 71)][1]; a = ang
        for j in range(int(ln / 3)):
            a += rng.normal(0, 0.11) + (-math.pi / 2 - a) * 0.012 + (0.25 if j % 9 == 4 else -0.2 if j % 9 == 8 else 0)
            nx, ny = px_ + math.cos(a) * 3, py + math.sin(a) * 3
            ch.append((px_, py, nx, ny, max(2.5, w * (1 - 0.6 * j / (ln / 3))))); px_, py = nx, ny
        chains.append(ch)
    inside, u, along, hw, ch = seg_field(chains, W, LH)
    nz = noise(W, LH, 5, 22, 91, 2); nzb = noise(W, LH, 3, 9, 92, 2)
    fpos = (u * hw / 3.4 + 0.5 * np.sin(along / 14 + ch * 1.9) + 0.3 * (nzb - 0.5)) % 1
    furrow = (fpos < 0.22) & (np.abs(u) < 0.9); ridge = (fpos > 0.22) & (fpos < 0.38) & (u < 0.5)
    v = 0.5 - 0.3 * u + 0.18 * (nz - 0.5) + np.where(furrow, -0.22, np.where(ridge, 0.14, 0))
    bark = lerp(hexc('140f22'), hexc('5a5270'), np.clip(v, 0, 1)[..., None])
    haze = (0.38 + 0.5 * smooth(70, 172, YY))[..., None]                        # distance: the fog swallows it toward its foot
    col = bark * (1 - haze) + F * haze
    rimL = (u < -0.8) & (hw > 3); rimR = (u > 0.82) & (hw > 3)
    rk = ((0.12 + 0.3 * smooth(30, 120, YY)) * (1 - smooth(120, 170, YY)))[..., None]      # a faint rim, fading into the fog with the bark
    col = np.where(rimL[..., None], col * (1 - rk) + hexc('4a8aa8') * rk, col)
    col = np.where(rimR[..., None], col * (1 - rk) + hexc('9a4a86') * rk, col)
    cl = noise(W, LH, 46, 5, 93, 3)
    lim = np.clip((YY - 4) / 100, 0, 1) * 0.5 + 0.44
    cut = cl > lim
    draw = inside & ~cut
    thin = inside & (cl > lim - 0.09) & ~cut
    col = np.where(thin[..., None], col * 0.45 + F * 0.15 + hexc('241a3c') * 0.4, col)
    base[:] = np.where(draw[..., None], col, base); own(draw)
    return draw


ARC = [(16, -8, 16), (36, -12, 24), (62, -18, 36), (96, -24, 48), (132, -30, 60)]   # tiers: (top y, x offset from axis, w)


def draw_arcology(base, F, rng, lights):
    m = np.zeros((LH, W), bool)
    for i, (ty, ox, w) in enumerate(ARC):
        mm = (np.abs(wdx(ARC_X + ox + w / 2) + 0.5) <= w / 2) & (YY >= ty); m |= mm
    k = (0.8 - 0.42 * smooth(40, 185, YY))[..., None]
    col = F * (1 - k) + hexc('100c22') * k
    sh = wdx(ARC_X) > 4
    col = np.where(sh[..., None], col * 0.86, col)
    base[:] = np.where(m[..., None], col, base); oid = own(m)
    for i, (ty, ox, w) in enumerate(ARC):     # deck rims and ring decks lit floor by floor
        x0 = ARC_X + ox
        for xx in range(int(x0), int(x0 + w)): lights.append((xx % W, ty, base[ty, xx % W] * 0.4 + hexc('7a6a9a') * 0.6, oid))
        nxt = ARC[i + 1][0] if i + 1 < len(ARC) else 200
        for dy in range(ty + 3, nxt - 1, 3):
            lvl = 0.25 + 0.2 * ((dy // 9) % 2)
            for xx in range(int(x0) + 1, int(x0 + w) - 1, 2):
                if rng.random() < lvl * 0.7:
                    c = hexc(rng.choice(['c08040', 'a8b0c8', '6a7aa0', 'e0a050'])); kk = 0.55 * (1 - 0.6 * smooth(20, 190, dy))
                    lights.append((xx % W, dy, base[dy, xx % W] * (1 - kk) + c * kk, oid))
        for r in range(ty + 1, min(nxt, ty + 14)):   # a short cyan light strip under each deck, on the lit corner
            lights.append((int(x0) % W, r, base[r, int(x0) % W] * (0.4 + 0.04 * (r - ty)) + hexc(CYAN[2]) * (0.6 - 0.04 * (r - ty)), oid))
    for i in range(34):                          # the crown needle, through the cloud
        ww = max(1, int(round(9 * (1 - i / 34))))
        for xx in range(int(ARC_X - ww / 2), int(ARC_X - ww / 2) + ww):
            if 16 - i >= 0: base[16 - i, xx % W] = F[16 - i, xx % W] * 0.5 + hexc('171230') * 0.5
    for xx in range(ARC_X - 8, ARC_X + 8): lights.append((xx % W, 24, hexc(CYAN[2]) * 0.7 + base[24, xx % W] * 0.3, oid))
    FX['arc'] = [ARC_X, 0]
    return m


FAR_PAL = (['05060f', '080919', '0b0b20', '0e0c26', '130f2e', '181232', '1e1438', '25163e', '2c1844', '341b4a', '3c1d4e', '461f54',
            '50235a', '5a265e', '642962', '6c2c66', '74306a', '7e346c', '883a70',
            '0e1a2c', '132438', '1a3044', '203c52', '284860', '30566c', '1c4a62', '2a6a88', '3a90b0', '5ac8e8',
            '0b0918', '100c20', '150f28', '1c1230', '231636', '2a1a3e', '1a1428', '2a2238', '3a3248', '4a4258', '5a5268', '6a6080',
            'a04a8a', 'e05ab0', '3a2452', '4a2c5c'])


def build_far():
    rng = np.random.default_rng(21); OWN[:] = 0; NID[0] = 0
    F = fog()
    src = f'{SRC}/far_render.png'
    sky = V.box_down(Image.open(src) if os.path.exists(src) else Image.open(f'{SRC}/guide_far.png'))
    # keep the render only where it is sky / cloud; below the cloud deck use the clean fog model under its texture
    wsky = 1 - smooth(110, 140, YY)[..., None]
    base = sky * wsky + (F * 0.85 + sky * 0.15) * (1 - wsky)
    lights = []
    L0 = skyline(rng, -8, W, 96, 136, 9, 22, (1, 10), avoid=[(ARC_X, 40, 30), (ROOT_X, 30, 20)])
    L1 = skyline(rng, -6, W, 118, 150, 10, 24, (-1, 7), avoid=[(ARC_X, 34, 18)])
    L2 = skyline(rng, -4, W, 140, 166, 9, 26, (-2, 4))
    paint_depth(base, F, L0, 0, rng, lights)
    draw_root(base, F, rng)
    draw_arcology(base, F, rng, lights)
    paint_depth(base, F, L1, 1, rng, lights)
    # holo boards in the fog: a soft halo first (it lights the haze), the crisp panel after the palette lock
    boards = [(ARC_X - 14, 68, 8, 46, MAG, True, 7, 'm'), (200, 128, 22, 11, MAG, False, 3, 'm'), (452, 122, 8, 26, CYAN, True, 5, 'c'), (26, 136, 7, 20, AMBER[2:], True, 9, 'a'),
              (286, 140, 16, 9, CYAN, False, 13, 'c'), (380, 132, 7, 18, MAG, True, 21, 'm')]
    glowc = {'m': hexc('c0308a'), 'c': hexc('2a8ab0'), 'a': hexc('b0702a')}
    for bx, by, bw, bh, _, _, _, nk in boards:
        d = np.sqrt((wdx(bx + bw / 2) / (bw * 1.4 + 10)) ** 2 + ((YY - by - bh / 2) / (bh * 1.2 + 10)) ** 2)
        base += (np.clip(1 - d, 0, 1) ** 1.8 * 0.55)[..., None] * glowc[nk]
    paint_depth(base, F, L2, 2, rng, lights)
    base = np.clip(base, 0, 255)
    pal = [tuple(hexc(c)) for c in FAR_PAL]
    q = V.palette_lock(base, pal, dither_flat=True, dk=0.5)
    q = V.majority(q)
    px = N.Px(W, LH, wrap=True, base=q)
    for x, y, c, oid in lights:
        if 0 <= y < LH and OWN[y, x] == oid: px.rgb[y, x] = c
    for bx, by, bw, bh, neon, vert, sd, nk in boards:
        glyph_panel(px, bx, by, bw, bh, neon, sd, vertical=vert)
    # a few neon bands on far-row crowns (not on every roof)
    for T in L2[::5]:
        ram = MAG if int(T['x']) % 2 else CYAN
        px.rect(T['x'], T['top'] + 2, T['w'], 1, ram[2], 0.8)
    FX['far_boards'] = [[bx, by, bw, bh, {'m': '255,63,192', 'c': '63,224,255', 'a': '255,176,80'}[nk]] for bx, by, bw, bh, _, _, _, nk in boards]
    FX['lanes'] = [[96, 1.5], [110, 2.0], [124, 1.2]]
    FX['search'] = [[ARC_X + 46, 150, '150,220,255'], [ROOT_X + 74, 156, '255,150,220']]
    FX['root'] = [ROOT_X, 100]
    blink = FX.get('far_blink', [])[::3] + [[ARC_X, -18]]
    FX['far_blink'] = blink
    frames = []
    for f in range(4):
        fp = N.Px(W, LH, wrap=True, base=px.rgb)
        for i, (x, y) in enumerate(blink):
            if y < 0: continue
            on = ((f + i) % 4) < 2 if i % 3 else f == 0
            fp.px(x, y, 'ff3a4a' if on else '4a1424')
        frames.append(V.to_rgba(fp.rgb))
    frames[0].save(f'{SRC}/out_far.png')
    return frames


# =========================================================================== mid: near towers (1x)
MID = [  # tower specs (x, w, top in mid-layer px); edge = (neon, side); sign = (neon, side -1/1, y off, w, h); board = (x frac, w, h, neon)
    dict(x=-6, w=46, top=46, setbacks=[(16, 3)], edge=('c', 1), sign=('m', 1, 26, 7, 48), crown='ring'),
    dict(x=96, w=40, top=84, edge=('m', -1), board=(0.1, 30, 16, 'c'), tank=0.7),
    dict(x=176, w=30, top=110, edge=('a', 1), vent=0.3, sign=('c', -1, 18, 6, 30)),
    dict(x=244, w=58, top=-24, setbacks=[(70, 4)], edge=('m', -1), sign=('a', 1, 84, 6, 36), face=('m', 0.62, 36, 12, 64)),
    dict(x=350, w=34, top=96, edge=('c', 1), tank=0.4, vent=0.75),
    dict(x=420, w=48, top=60, setbacks=[(30, 4)], edge=('c', -1), sign=('m', -1, 30, 7, 50), crown='step'),
]
BRIDGES = [(40, 96, 128, 'c'), (300, 350, 140, 'm')]
NEONC = {'c': CYAN, 'm': MAG, 'a': AMBER[2:]}
NEONRGB = {'c': '63,224,255', 'm': '255,63,192', 'a': '255,176,80'}
SPILL = {'c': hexc('145a78'), 'm': hexc('7a1a62'), 'a': hexc('5a3812')}
MID_PAL = ['050510', '07070f', '090914', '0b0b18', '0e0d1e', '110f24', '15122a', '1a1630', '201b38', '282244', '322a52',
           '1c1030', '24143a', '2e1a44', '3a1e4c',                                    # street fog toward the feet
           '0e2a3a', '144050', '1c5a6c', '102028',                                    # cyan spill
           '3a0e34', '5a1450', '7a1a66', '28102a',                                    # magenta spill
           '1e1418', '2a1c16', '3a2414', '4a2e16']                                    # amber spill
MID_FOG = hexc('2a1640')


def mid_mask(T):
    m = np.zeros((LH, W), bool)
    segs = sorted([(T['top'], T['x'], T['w'])] + [(T['top'] + dy, T['x'] - i, T['w'] + 2 * i) for dy, i in T.get('setbacks', [])])
    for k, (y0, x, w) in enumerate(segs):
        y1 = segs[k + 1][0] if k + 1 < len(segs) else LH
        m |= (np.abs(wdx(x + w / 2) + 0.5) <= w / 2) & (YY >= y0) & (YY < y1)
    return m, segs


def build_mid():
    rng = np.random.default_rng(33)
    base = np.zeros((LH, W, 3)); al = np.zeros((LH, W), bool)
    lights = []          # (x, y, rgb) crisp after the lock
    signs, boards, blink, steam, faces = [], [], [], [], []
    glass = lerp(hexc('120f26'), hexc('080812'), smooth(10, 150, YY)[..., None])
    for T in MID:
        m, segs = mid_mask(T)
        x, w, top = T['x'], T['w'], T['top']
        col = glass.copy()
        rel = wdx(x + w / 2) + 0.5
        col = np.where((rel > w / 2 - w / 4)[..., None], col * 0.75, col)                # shadow third
        # curtain wall: floor slabs every 4 px (a lighter spandrel line), mullions every 4 px (darker)
        slab = ((YY - top) % 4 == 0)
        col = np.where(slab[..., None], col * 1.25 + 3, col)
        mull = ((np.floor(rel + 200) % 4) == 0)
        col = np.where((mull & ~slab)[..., None], col * 0.8, col)
        # the street fog swallowing the feet
        fk = smooth(120, 196, YY)[..., None] * 0.75
        col = col * (1 - fk) + MID_FOG * fk
        base = np.where(m[..., None], col, base); al |= m
        # the roof rim of each setback catches the sky glow
        for (y0, sx, sw) in segs:
            for xx in range(int(round(sx)), int(round(sx + sw))):
                lights.append((xx % W, int(y0), hexc('3a3058')))
        # crowns
        cx = x + w / 2
        if T.get('crown') == 'ring':
            for xx in range(int(x) - 2, int(x + w) + 2): base[top - 3, xx % W] = hexc('1a1630'); base[top - 2, xx % W] = hexc('100e20'); al[top - 3:top - 1, xx % W] = True
            for xx in range(int(x) - 2, int(x + w) + 2, 2): lights.append((xx % W, top - 3, hexc(CYAN[2]) * 0.7 + hexc('100e20') * 0.3))
        if T.get('crown') == 'spire':
            for i in range(30):
                ww = max(1, int(round(w * 0.3 * (1 - i / 30))))
                for xx in range(int(cx - ww / 2), int(cx - ww / 2) + ww): base[top - 1 - i, xx % W] = hexc('0e0c1e'); al[top - 1 - i, xx % W] = True
            for xx in range(int(cx) - 1, int(cx) + 1):
                for yy in range(top - 50, top - 30): base[yy, xx % W] = hexc('0e0c1e'); al[yy, xx % W] = True
            blink.append([int(cx) % W, top - 51])
        if T.get('crown') == 'step':
            for i in range(3):
                for xx in range(int(x) + 2 + i * 3, int(x + w) - 2 - i * 3):
                    for yy in range(top - 3 - i * 3, top - i * 3): base[yy, xx % W] = hexc('110f22'); al[yy, xx % W] = True
            blink.append([int(cx) % W, top - 11])
        # neon spill on the facade around the signs / boards (lit walls), and the lit edge
        if T.get('edge'):
            nk, sd = T['edge']; ex = int(round(x if sd < 0 else x + w - 1))
            for r in range(max(0, top), 186):
                if al[r, ex % W]: lights.append((ex % W, r, hexc(NEONC[nk][2]) * (0.25 + 0.35 * smooth(top, 160, r)) + base[r, ex % W] * 0.5))
        if T.get('sign'):   # the sign hangs off the side: its light washes the facade next to it (falls off from the rect)
            nk, sd, dy, sw, sh = T['sign']; sx = int(round(x - sw - 2 if sd < 0 else x + w + 2)); sy = top + dy
            dxr = np.maximum(0, np.abs(wdx(sx + sw / 2) + 0.5) - sw / 2); dyr = np.maximum(0, np.abs(YY - sy - sh / 2) - sh / 2)
            base = base + (np.exp(-dxr / 7) * np.exp(-dyr / 8) * 0.8 * m)[..., None] * SPILL[nk]
            signs.append((sx, sy, sw, sh, nk, sd, x, w))
        if T.get('face'):   # a holo column mounted flat on the facade, washing the glass around it
            nk, fx_, fy_, fw, fh = T['face']; fxx = int(round(x + w * fx_ - fw / 2))
            dxr = np.maximum(0, np.abs(wdx(fxx + fw / 2) + 0.5) - fw / 2); dyr = np.maximum(0, np.abs(YY - fy_ - fh / 2) - fh / 2)
            base = base + (np.exp(-dxr / 6) * np.exp(-dyr / 8) * 0.6 * m)[..., None] * SPILL[nk]
            faces.append((fxx, fy_, fw, fh, nk))
        if T.get('board'):  # the rooftop board lights the roof edge and the top floors under it
            fx_, bw, bh, nk = T['board']; bx = int(round(x + w * fx_)); by = top - bh - 6
            dxr = np.maximum(0, np.abs(wdx(bx + bw / 2) + 0.5) - bw / 2); dyr = np.maximum(0, YY - top)
            base = base + (np.exp(-dxr / 6) * np.exp(-dyr / 7) * 0.9 * m)[..., None] * SPILL[nk]
            boards.append((bx, by, bw, bh, nk))
        # side boxes cantilevered off the walls (AC stacks, pods, little lit rooms), a duct down one face
        for b in range(int(rng.integers(1, 4))):
            sd = -1 if rng.random() < 0.5 else 1; bw_ = int(rng.integers(6, 12)); bh_ = int(rng.integers(6, 15)); by_ = int(rng.integers(max(10, top + 10), 150))
            seg = [sg for sg in segs if sg[0] <= by_]; sgx, sgw = (seg[-1][1], seg[-1][2]) if seg else (x, w)
            bx_ = int(round(sgx - bw_ if sd < 0 else sgx + sgw))
            for yy in range(by_, by_ + bh_):
                for xx in range(bx_, bx_ + bw_):
                    c = hexc('282244') if yy == by_ else hexc('0c0b18') if yy == by_ + bh_ - 1 else hexc('15122a')
                    base[yy, xx % W] = c * (1 - 0.6 * smooth(130, 190, yy)) + MID_FOG * 0.6 * smooth(130, 190, yy); al[yy, xx % W] = True
            if rng.random() < 0.5: lights.append(((bx_ + bw_ // 2) % W, by_ + 2, None, hexc(rng.choice(['c0803a', '13a3c9', 'a02a80'])), 0.7))
        if rng.random() < 0.7:
            dxp = int(round(x + (2 if rng.random() < 0.5 else w - 4)))
            for yy in range(top + 2, 190):
                for xx in (dxp, dxp + 1):
                    if al[yy, xx % W]: lights.append((xx % W, yy, None, hexc('2a2448' if xx == dxp else '0b0a16'), 0.8 if yy % 9 else 1.0))
        # windows: offices lit in clusters (3 x 2 px cells in the curtain-wall grid), dim with the fog
        for fy in range(top + 2 + 4 * max(0, -(top + 2) // 4 + 1) if top + 2 < 0 else top + 2, 184, 4):
            mode = rng.random(); p = 0.16 * (0.25 if mode < 0.4 else 2.4 if mode > 0.94 else 1.0)
            grp = rng.random(12)
            for cxx in range(int(x) + 1, int(x + w) - 3, 4):
                if not (m[fy, cxx % W] and m[fy, (cxx + 3) % W] and m[fy + 2, cxx % W]): continue
                if rng.random() < p * (0.2 + 1.6 * grp[((cxx - int(x)) // 8) % 12]):
                    cs, ws = zip(*[('9c6428', 5), ('c0803a', 3), ('7a8098', 2), ('13a3c9', 0.5), ('a02a80', 0.4)])
                    c = hexc(cs[rng.choice(len(cs), p=np.array(ws) / sum(ws))])
                    kk = 0.75 * (1 - 0.7 * smooth(top, 176, fy))
                    for dx in range(3):
                        for dy_ in range(2): lights.append(((cxx + dx) % W, fy + 1 + dy_, None, c, kk * (0.85 if dy_ else 1)))
        if T.get('tank'):
            tx = int(round(x + w * T['tank'])) - 4; ty = top - 12
            for (rx, ry, rw, rh, c) in ((tx, ty, 9, 8, '15122a'), (tx - 1, ty + 1, 11, 1, '201b38'), (tx + 6, ty + 1, 3, 7, '0b0b18'), (tx + 1, ty + 8, 1, 4, '15122a'),
                                        (tx + 7, ty + 8, 1, 4, '15122a'), (tx + 4, ty - 3, 1, 3, '15122a')):
                for yy in range(ry, ry + rh):
                    for xx in range(rx, rx + rw): base[yy, xx % W] = hexc(c); al[yy, xx % W] = True
            for xx in range(tx, tx + 9): lights.append((xx % W, ty, hexc('3a3058')))
        if T.get('vent'):
            vx = int(round(x + w * T['vent'])) - 2
            for yy in range(top - 6, top):
                for xx in range(vx, vx + 5): base[yy, xx % W] = hexc('15122a' if yy > top - 6 else '282244'); al[yy, xx % W] = True
            steam.append([vx + 2, top - 7])
        for k in range(int(w // 12)):   # AC units on the roof line
            ax = int(round(x + 3 + k * 11 + rng.integers(0, 3)))
            if rng.random() < 0.55:
                for yy in range(top - 3, top):
                    for xx in range(ax, ax + 5): base[yy, xx % W] = hexc('15122a' if yy > top - 3 else '282244'); al[yy, xx % W] = True
    # skybridges
    for x0, x1, y, nk in BRIDGES:
        for yy in range(y, y + 5):
            for xx in range(x0 - 1, x1 + 1): base[yy, xx % W] = hexc('110f22' if yy > y else '282244'); al[yy, xx % W] = True
        for xx in range(x0 - 1, x1 + 1): lights.append((xx % W, y + 5, hexc(NEONC[nk][2]) * 0.8)); al[y + 5, xx % W] = True
        for xx in range(x0, x1, 3): lights.append((xx % W, y + 2, hexc(NEONC[nk][1])))
        for xx in range(x0 - 1, x1 + 1):
            base[y - 3, xx % W] = hexc('1a1630'); al[y - 3, xx % W] = True
            if xx % 3 == 0:
                for yy in range(y - 3, y): base[yy, xx % W] = hexc('1a1630'); al[yy, xx % W] = True
    # cables between towers
    for x0, y0, x1, y1, sag in ((40, 64, 96, 92, 6), (206, 120, 244, 70, 5), (300, 58, 350, 104, 7), (384, 108, 420, 92, 4), (468, 70, 506, 52, 5)):
        for i in range(61):
            t = i / 60; xx = int(round(x0 + (x1 - x0) * t)) % W; yy = int(round(y0 + (y1 - y0) * t + math.sin(t * math.pi) * sag))
            base[yy, xx] = hexc('15122a'); al[yy, xx] = True
    base = np.clip(base, 0, 255)
    pal = [tuple(hexc(c)) for c in MID_PAL]
    q = V.palette_lock(base, pal, dither_flat=True, dk=0.45)
    q = np.where(al[..., None], q, 0)
    px = N.Px(W, LH, wrap=True, base=q, alpha=True); px.a = al.copy()
    for L in lights:
        if len(L) == 3:
            x, y, c = L
            if 0 <= y < LH and al[y, x]: px.rgb[y, x] = c
        else:
            x, y, _, c, kk = L
            if 0 <= y < LH and al[y, x]: px.rgb[y, x] = px.rgb[y, x] * (1 - kk) + c * kk
    for sx, sy, sw, sh, nk, sd, tx, tw in signs:
        bxx = sx + sw if sd < 0 else sx - 2
        for yy in (sy + 4, sy + sh - 6): px.rect(bxx, yy, 2, 1, '282244')
        glyph_panel(px, sx, sy, sw, sh, NEONC[nk], int(sx) + 17)
        px.a[sy:sy + sh, sx % W:(sx % W) + sw] = True
    for fxx, fy_, fw, fh, nk in faces:
        glyph_panel(px, fxx, fy_, fw, fh, NEONC[nk], int(fxx) + 31)
    for bx, by, bw, bh, nk in boards:
        for lx in (bx + 3, bx + bw - 4): px.rect(lx, by + bh, 1, 6, '1a1630')
        px.rect(bx + 1, by + bh + 3, bw - 2, 1, '15122a')
        glyph_panel(px, bx, by, bw, bh, NEONC[nk], int(bx) + 5, vertical=False)
    FX['mid_signs'] = [[sx, sy, sw, sh, NEONRGB[nk]] for sx, sy, sw, sh, nk, *_ in signs] + [[a, b, c, d, NEONRGB[nk]] for a, b, c, d, nk in faces]
    FX['mid_boards'] = [[bx, by, bw, bh, NEONRGB[nk]] for bx, by, bw, bh, nk in boards]
    FX['mid_blink'] = blink; FX['steam'] = steam
    al = px.a
    frames = []
    for f in range(4):
        fp = N.Px(W, LH, wrap=True, base=px.rgb)
        for i, (x, y) in enumerate(blink):
            on = ((f + i) % 4) < 2
            fp.px(x, y, 'ff3a4a' if on else '4a1424'); al[y, x % W] = True
        frames.append(V.to_rgba(np.where(al[..., None], fp.rgb, 0), al))
    frames[0].save(f'{SRC}/out_mid.png')
    return frames


def preview(far, mid):
    from vista_v3lib import comp
    rows = []
    for cx, cy in ((0, 40), (560, 40), (1150, 600)):
        c = Image.new('RGBA', (384, 216), TINT)
        for L, fac, vf in ((far, 0.08, 0.02), (mid, 0.3, 0.08)):
            ox = -((cx * fac) % W); x = int(round(ox)); oy = int(round(np.clip(-cy * vf, -20, 20)))
            while x < 384: comp(c, L, x, oy); x += W
        rows.append(c)
    out = Image.new('RGBA', (384, 220 * len(rows)), '#111')
    for i, r in enumerate(rows): out.alpha_composite(r, (0, i * 220))
    out.resize((out.width * 2, out.height * 2), Image.NEAREST).save(f'{SRC}/preview.png')


def build_inmid():
    """Indoor rooms (the Server Cathedral, the Megablock, the tunnels): the mid layer becomes the hall's own glass wall: steel
    piers every 128 px with a pointed tracery head (the corporate cathedral of the World 2 Megacity), transoms, server towers
    standing in two bays, a dark wainscot with a cable tray. The panes are open: the city shows through them."""
    rng = np.random.default_rng(44)
    base = np.zeros((LH, W, 3)); al = np.zeros((LH, W), bool); leds = []
    sb = ['07070e', '0b0b15', '10101c', '161726', '1d1f31', '262a3f', '32374f', '434a66']
    def R(x, y, w, h, c):
        for yy in range(max(0, y), min(LH, y + h)):
            for xx in range(x, x + w): base[yy, xx % W] = hexc(c); al[yy, xx % W] = True
    for b in range(4):
        x0 = b * 128
        # the tracery head: two arcs meeting at the bay's centre, everything above them solid
        for xx in range(x0, x0 + 128):
            u = abs(xx - (x0 + 64)) / 64.0
            ya = int(8 + 44 * (u ** 1.6))
            for yy in range(0, ya): base[yy, xx % W] = hexc(sb[2] if yy < ya - 3 else sb[5] if yy == ya - 1 else sb[3]); al[yy, xx % W] = True
            if ya - 1 >= 0: base[ya - 1, xx % W] = hexc(sb[6])
        for xx in range(x0 + 24, x0 + 105):                                     # an inner rib echoing the arch
            u = abs(xx - (x0 + 64)) / 40.0; ya = int(22 + 30 * (u ** 1.6))
            if ya < 60:
                for yy in (ya, ya + 1): base[yy, xx % W] = hexc(sb[4] if yy == ya else sb[1]); al[yy, xx % W] = True
        # the pier
        R(x0 - 7, 0, 14, LH, sb[3]); R(x0 - 7, 0, 2, LH, sb[6]); R(x0 + 5, 0, 2, LH, sb[1])
        for yy in range(0, LH, 12): R(x0 - 7, yy, 14, 1, sb[1]); leds.append((x0 - 4, yy + 3, 'r'))
        for yy in range(4, 176): 
            if (yy // 3) % 2: base[yy, (x0 + 1) % W] = hexc('13a3c9') * 0.7 + hexc(sb[3]) * 0.3
        # slim mullions and transoms
        for mx in (x0 + 64,): R(mx - 1, 30, 3, 146, sb[4]); R(mx - 1, 30, 1, 146, sb[6])
        for ty in (70, 132): R(x0 + 7, ty, 114, 3, sb[4]); R(x0 + 7, ty, 114, 1, sb[6])
        # server towers in two bays
        if b in (1, 3):
            sx = x0 + 18
            R(sx, 84, 30, 92, sb[2]); R(sx, 84, 30, 1, sb[6]); R(sx, 84, 1, 92, sb[5])
            for yy in range(88, 172, 4):
                R(sx + 3, yy, 24, 3, sb[1]); R(sx + 3, yy, 24, 1, sb[3])
                for xx in range(sx + 5, sx + 25, 3):
                    if rng.random() < 0.55: leds.append((xx, yy + 1, rng.choice(['c', 'c', 'm', 'a', 'g'])))
            R(sx + 34, 120, 3, 56, sb[3])                                         # a cable trunk beside it
    R(0, 176, W, LH - 176, sb[2]); R(0, 176, W, 1, sb[6]); R(0, 177, W, 1, sb[4])      # the wainscot, a cable tray, an LED strip
    for xx in range(0, W, 2): base[184, xx] = hexc('6e0f5c') if (xx // 2) % 4 else hexc('c21d97')
    for xx in range(0, W, 9): R(xx, 190, 6, 4, sb[1])
    LEDC = {'c': ('13a3c9', '3fe0ff'), 'm': ('c21d97', 'ff3fc0'), 'a': ('c87a20', 'ffb050'), 'g': ('2fd09a', '5affd2'), 'r': ('8a0f22', 'e0223f')}
    frames = []
    for f in range(4):
        b2 = base.copy()
        for i, (x, y, k) in enumerate(leds):
            on = h01(i, f // 2 if k != 'r' else f) > 0.3 if k != 'r' else (f + i) % 4 == 0
            b2[y, x % W] = hexc(LEDC[k][1] if on else LEDC[k][0])
        frames.append(V.to_rgba(np.where(al[..., None], b2, 0), al))
    frames[0].save(f'{SRC}/out_inmid.png')
    return frames


def h01(*a):
    v = 0
    for x in a: v = (v * 1103515245 + int(x) * 2654435761 + 12345) & 0xffffffff
    v ^= v >> 13; v = (v * 1274126177) & 0xffffffff; v ^= v >> 16
    return (v & 0xffff) / 65535


def build(ase=True):
    FX.clear()
    far = build_far(); mid = build_mid(); inmid = build_inmid()
    json.dump(FX, open(f'{SRC}/fx.json', 'w'))
    if ase:   # the fx points go into the game code between the markers (36_neohallow.js NH_BGFX)
        jp = os.path.join(V.ROOT, 'web', 'src', '36_neohallow.js'); js = open(jp).read()
        a, b = js.index('// <nh-bgfx>\n'), js.index('// </nh-bgfx>')
        keep = {k: FX[k] for k in ('lanes', 'search', 'far_boards', 'mid_signs', 'steam')}
        js = js[:a] + '// <nh-bgfx>\nconst NH_BGFX = ' + json.dumps(keep, separators=(',', ':')) + ';\n' + js[b:]
        open(jp, 'w').write(js)
    preview(far[0], mid[0])
    if ase:
        import asebuild
        for name, fr in (('bg_neohallow_far', far), ('bg_neohallow_mid', mid), ('bg_neohallow_inmid', inmid)):
            asebuild.build(name, W, LH, ['Layer'], [{'ms': 160, 'cels': {'Layer': im}} for im in fr], [('loop', 0, 3)])
            j = json.load(open(os.path.join(V.ROOT, 'assets', f'{name}.json')))
            assert len(j['frames']) == 4 and (j['frames'][0]['sourceSize']['w'], j['frames'][0]['sourceSize']['h']) == (W, LH)
    st = {k: V.stats(im) for k, im in (('far', far[0]), ('mid', mid[0]))}
    json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1); print(st)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' in a or not os.path.exists(f'{SRC}/guide_far.png'): guide_far()
    if '--guide' in a: sys.exit()
    if '--render' in a:
        i = a.index('--render'); sd = int(a[i + 1]) if len(a) > i + 1 and a[i + 1].isdigit() else None
        guide_far(); render(sd)
    build('--no-ase' not in a)
