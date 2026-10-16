"""Background v2 pipeline (docs/v17/bg_pilot.md): layout guide -> ComfyUI img2img at 3x -> seamless wrap -> pixel scale,
palette lock, cleanup, alpha keying, grade -> asebuild.

Two halves:
  * render side (needs the ComfyUI server on :8188): `Guide` paints a tileable 3x layout/value sketch, `render()` runs
    SDXL + pixel-art-xl + Lightning img2img over it with ControlNet Union (lineart from the guide's edges) and an optional
    IP-Adapter style reference, `seam_pass()` rolls the image by half and regenerates only a feathered centre band.
  * build side (no server): `to_pixels()` BOX-downscales, palette-locks to ramps (+ a few accents) with ordered dither only
    on smooth gradients, removes 1px orphans; `key_mid()` cuts the mid layer with the guide's own alpha; `rim()` adds the
    1px rim light. The per-biome gen_bg_<biome>_v2.py scripts only use the build side unless run with --render.
"""
import math, os, sys, time, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 3
W, H = 512, 216
WS, HS = W * S, H * S
ART = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ART)


# ----------------------------------------------------------------------------------------------- colour helpers
def hexc(s):
    s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], float)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def tile_noise(w, h, cell_x, cell_y, seed, octaves=3):
    """Tileable-in-x value noise on a w x h grid (w % cell_x == 0 for each octave)."""
    rng = np.random.default_rng(seed); out = np.zeros((h, w)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        cx, cy = max(1, cell_x >> o), max(1, cell_y >> o)
        nx, ny = w // cx, h // cy + 2
        grid = rng.random((ny, nx))
        xs = np.arange(w) / cx; ys = np.arange(h) / cy
        x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
        tx = xs - x0; ty = ys - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
        a = grid[y0][:, x0 % nx]; b = grid[y0][:, (x0 + 1) % nx]; c = grid[y0 + 1][:, x0 % nx]; d = grid[y0 + 1][:, (x0 + 1) % nx]
        top = a + (b - a) * tx[None]; bot = c + (d - c) * tx[None]
        out += amp * (top + (bot - top) * ty[:, None]); tot += amp; amp *= 0.5
    return out / tot


# ----------------------------------------------------------------------------------------------- the guide painter
class Guide:
    """A tileable layout/value sketch at 3x. Coordinates are given in 1x layer pixels (floats ok); every shape is drawn
    three times (x - W, x, x + W) so it wraps. `rgb` is float HxWx3, `a` the coverage (for mid layers)."""

    def __init__(self, base=(0, 0, 0), alpha=False):
        self.rgb = np.zeros((HS, WS, 3)); self.rgb[:] = base
        self.a = np.zeros((HS, WS)) if alpha else None
        yy, xx = np.mgrid[0:HS, 0:WS]
        self.X = (xx + 0.5) / S; self.Y = (yy + 0.5) / S

    # masks ---------------------------------------------------------------------------------------------------
    def mask_poly(self, pts, blur=0.0):
        m = Image.new('L', (WS, HS), 0); d = ImageDraw.Draw(m)
        for dx in (-W, 0, W):
            d.polygon([((x + dx) * S, y * S) for x, y in pts], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def mask_lines(self, segs, blur=0.0):
        """segs: [(x0, y0, x1, y1, width)] -> coverage mask (round caps)."""
        m = Image.new('L', (WS, HS), 0); d = ImageDraw.Draw(m)
        for dx in (-W, 0, W):
            for x0, y0, x1, y1, w in segs:
                ww = max(1, int(round(w * S)))
                d.line([((x0 + dx) * S, y0 * S), ((x1 + dx) * S, y1 * S)], fill=255, width=ww)
                r = ww / 2
                for (px, py) in ((x0, y0), (x1, y1)):
                    d.ellipse([(px + dx) * S - r, py * S - r, (px + dx) * S + r, py * S + r], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def wdx(self, cx):
        """signed wrapped x distance to cx, per pixel (1x units)."""
        return (self.X - cx + W / 2) % W - W / 2

    def mask_ellipse(self, cx, cy, rx, ry, soft=1.0):
        d = np.sqrt((self.wdx(cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        return np.clip((1 - d) * max(rx, ry) * S * soft, 0, 1)        # solid, ~1 px (at 3x) antialiased edge

    # paint ---------------------------------------------------------------------------------------------------
    def fill(self, mask, col, alpha=1.0):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]
        self.rgb = self.rgb * (1 - m) + np.asarray(col, float) * m
        if self.a is not None: self.a = np.maximum(self.a, np.clip(mask, 0, 1) * (1 if alpha > 0.5 else 0))

    def fill_img(self, mask, img, alpha=1.0):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]
        self.rgb = self.rgb * (1 - m) + img * m
        if self.a is not None: self.a = np.maximum(self.a, np.clip(mask, 0, 1))

    def add(self, mask, col, k=1.0):
        self.rgb = self.rgb + np.clip(mask, 0, 1)[..., None] * np.asarray(col, float) * k

    def glow(self, cx, cy, rx, ry, col, k=1.0, p=2.0):
        d = np.sqrt((self.wdx(cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        self.add(np.clip(1 - d, 0, 1) ** p, col, k)

    def image(self):
        return Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8))

    def alpha_img(self):
        return Image.fromarray((np.clip(self.a, 0, 1) * 255).astype(np.uint8))


def arch_pts(cx, half, spring, apex, bottom, pointed=True, n=24):
    """Polygon of an arch opening: vertical jambs from bottom to spring, a pointed (or round) head up to apex."""
    pts = [(cx - half, bottom), (cx - half, spring)]
    rise = spring - apex
    for i in range(1, n + 1):
        t = i / n
        if pointed:   # two arcs meeting at the apex (equilateral-ish)
            ang = t * math.pi / 2
            x = cx - half + half * (1 - math.cos(ang)) ; y = spring - rise * math.sin(ang)
        else:
            ang = math.pi - t * math.pi / 2
            x = cx + half * math.cos(ang); y = spring - rise * math.sin(t * math.pi / 2)
        pts.append((x, y))
    for (x, y) in reversed(pts[2:-1]):
        pts.append((2 * cx - x, y))
    pts += [(cx + half, spring), (cx + half, bottom)]
    return pts


def root_segs(rng, x, y, ang, length, width, depth, step=2.5, curl=0.0, spread=(0.3, 0.6), shrink=(0.55, 0.72), droop=0.012):
    """A hanging root: wandering tapered polyline with side branches. Returns [(x0,y0,x1,y1,w)]."""
    segs = []
    n = max(2, int(length / step))
    for i in range(n):
        w = width * (1 - 0.7 * i / n)
        nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
        segs.append((x, y, nx, ny, max(0.6, w)))
        x, y = nx, ny
        ang += curl + rng.normal(0, 0.12)
        ang += (math.pi / 2 - ang) * droop      # gravity pulls toward straight down
        if depth > 0 and rng.random() < 0.08 + 0.04 * depth and i > n * 0.15:
            s = 1 if rng.random() < 0.5 else -1
            segs += root_segs(rng, x, y, ang + s * rng.uniform(*spread), length * rng.uniform(*shrink) * (1 - i / n * 0.5),
                              w * 0.6, depth - 1, step, curl, spread, shrink, droop)
    return segs


def edges_of(img, lo=14, blur=0.6):
    """Lineart control image from a guide (white lines on black)."""
    g = img.convert('L').filter(ImageFilter.GaussianBlur(blur * S))
    e = g.filter(ImageFilter.FIND_EDGES)
    return e.point(lambda v: 255 if v > lo else 0).filter(ImageFilter.MaxFilter(3))


# ----------------------------------------------------------------------------------------------- ComfyUI render side
NEG = 'text, watermark, signature, person, character, people, cartoon, chibi, bright saturated colors, blurry, jpeg artifacts, frame, border'


def _comfy():
    sys.path.insert(0, os.path.expanduser('~/Claude/pixelgen'))
    import comfy
    return comfy


def render(guide_png, edge_png, prompt, seed, out_png, denoise=0.78, cn=0.45, cn_end=0.6, ref_png=None, ref_w=0.35, ckpt=None,
           steps=8, cfg=1.0, loras=None, sampler='euler', scheduler='sgm_uniform'):
    c = _comfy()
    up = c.upload(guide_png); ue = c.upload(edge_png); ur = c.upload(ref_png) if ref_png else None
    wf = c.workflow(prompt, seed, init_image=up, denoise=denoise, negative=NEG, pose=ue, pose_type='canny/lineart/anime_lineart/mlsd',
                    pose_strength=cn, ref=ur, ref_weight=ref_w, ckpt=ckpt, steps=steps, cfg=cfg, loras=loras, sampler=sampler, scheduler=scheduler)
    wf['43']['inputs']['end_percent'] = cn_end
    if ur:   # style only: IP-Adapter on the whole run but lighter at the end
        wf['32']['inputs']['weight_type'] = 'style transfer'
    t = time.time(); c.run(wf, out_png); return time.time() - t


def seam_pass(src_png, prompt, seed, out_png, band=128, denoise=0.5, ref_png=None, ref_w=0.3, ckpt=None, steps=8, cfg=1.0, loras=None,
              sampler='euler', scheduler='sgm_uniform', work=None):
    """Roll by half so the wrap seam sits in the middle, regenerate a feathered centre band (band = half-width in 1x px),
    keep every pixel outside it, roll back."""
    c = _comfy(); work = work or os.path.dirname(out_png)
    g = Image.open(src_png).convert('RGB'); w = g.width
    r = Image.fromarray(np.roll(np.asarray(g), w // 2, axis=1)); rp = os.path.join(work, '_rolled.png'); r.save(rp)
    bs = band * S; cx = w // 2; m = np.zeros((g.height, w), np.uint8)
    for x in range(cx - bs, cx + bs):
        m[:, x] = int(255 * min(1, (bs - abs(x - cx)) / (bs * 0.5)))
    mp = os.path.join(work, '_seam_mask.png'); Image.fromarray(m).save(mp)
    ur, um = c.upload(rp), c.upload(mp); uref = c.upload(ref_png) if ref_png else None
    wf = c.workflow(prompt, seed, init_image=ur, denoise=denoise, negative=NEG, pose=ur, pose_type='tile', pose_strength=0.6, ref=uref, ref_weight=ref_w,
                    ckpt=ckpt, steps=steps, cfg=cfg, loras=loras, sampler=sampler, scheduler=scheduler)
    wf['50'] = {'class_type': 'LoadImage', 'inputs': {'image': um}}
    wf['51'] = {'class_type': 'ImageToMask', 'inputs': {'image': ['50', 0], 'channel': 'red'}}
    wf['52'] = {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': ['21', 0], 'mask': ['51', 0]}}
    wf['7']['inputs']['latent_image'] = ['52', 0]
    tmp = os.path.join(work, '_seam_gen.png'); t = time.time(); c.run(wf, tmp); dt = time.time() - t
    g2 = np.asarray(Image.open(tmp).convert('RGB')).astype(float); rr = np.asarray(r).astype(float); a = (m.astype(float) / 255)[..., None]
    comp = (g2 * a + rr * (1 - a)).astype(np.uint8)
    Image.fromarray(np.roll(comp, -(w // 2), axis=1)).save(out_png)
    for p in (rp, mp, tmp): os.remove(p)
    return dt


# ----------------------------------------------------------------------------------------------- build side
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float)


def grade(img, black=0, white=255, gamma=1.0, sat=1.0, tint=None, tint_k=0.0, lift=None):
    """Levels + gamma + saturation + optional colour tint on a float RGB array or image. Returns float array."""
    a = np.asarray(img, float)[..., :3]
    a = np.clip((a - black) / max(1, white - black), 0, 1) ** (1 / gamma) * 255
    l = a.mean(2, keepdims=True); a = l + (a - l) * sat
    if tint is not None: a = a * (1 - tint_k) + (a.mean(2, keepdims=True) / 128) * np.asarray(tint, float) * tint_k
    if lift is not None: a = a + np.asarray(lift, float)[None, None] * (1 - a / 255)
    return np.clip(a, 0, 255)


def box_down(img_or_arr, w=W, h=H):
    im = img_or_arr if isinstance(img_or_arr, Image.Image) else Image.fromarray(np.clip(img_or_arr, 0, 255).astype(np.uint8))
    return np.asarray(im.convert('RGB').resize((w, h), Image.BOX), float)


def _lab(c):
    c = np.asarray(c, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def pick_accents(arr, pal, n=8, min_de=9.0, k=40, mask=None):
    """The n most-used colours of a k-means reduction that are at least min_de (Lab) from every palette colour."""
    im = Image.fromarray(arr.astype(np.uint8))
    q = im.quantize(colors=k, method=Image.Quantize.MEDIANCUT, kmeans=4, dither=Image.Dither.NONE)
    idx = np.asarray(q); qp = np.array(q.getpalette()[:k * 3], float).reshape(-1, 3)
    w = mask if mask is not None else np.ones(idx.shape, bool)
    counts = np.bincount(idx[w].ravel(), minlength=k)
    out = list(map(tuple, pal)); acc = []
    for i in np.argsort(-counts):
        if counts[i] == 0 or len(acc) >= n: break
        c = qp[i]; de = np.sqrt(((_lab(np.array(out)) - _lab(c)) ** 2).sum(1)).min()
        if de >= min_de: out.append(tuple(c)); acc.append(tuple(int(v) for v in c))
    return acc


def palette_lock(arr, pal, dither_flat=True, flat_thresh=6.0, dk=0.55):
    """Nearest palette colour in Lab. Where the source is a smooth gradient (low local contrast) and dither_flat is on,
    an ordered (Bayer 4x4) dither between the two nearest colours replaces banding, like the hand-built layers."""
    P = np.array(pal, float); PL = _lab(P); L = _lab(arr)
    d = ((L[..., None, :] - PL[None, None]) ** 2).sum(-1)
    o = np.argsort(d, -1); i1, i2 = o[..., 0], o[..., 1]
    out = P[i1]
    if dither_flat:
        lum = (arr * np.array([0.299, 0.587, 0.114])).sum(-1)
        lp = np.pad(lum, 1, mode='edge')
        loc = np.max([np.abs(lp[1 + dy:lp.shape[0] - 1 + dy, 1 + dx:lp.shape[1] - 1 + dx] - lum) for dy in (-1, 0, 1) for dx in (-1, 0, 1)], 0)
        d1 = np.take_along_axis(d, i1[..., None], -1)[..., 0] ** 0.5; d2 = np.take_along_axis(d, i2[..., None], -1)[..., 0] ** 0.5
        t = d1 / np.maximum(1e-6, d1 + d2)                                     # 0 = on c1, 0.5 = halfway to c2
        yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
        th = (B4[yy & 3, xx & 3] + 0.5) / 16
        near = np.sqrt(((PL[i1] - PL[i2]) ** 2).sum(-1)) < 22               # only dither between close ramp neighbours
        use = (loc < flat_thresh) & near & (t * 2 * dk > th)
        out = np.where(use[..., None], P[i2], out)
    return out


def majority(arr, alpha=None, passes=1):
    """Replace 1px orphans (a colour that matches none of its 8 neighbours) by the most common neighbour colour."""
    a = arr.copy()
    for _ in range(passes):
        q = (a[..., 0].astype(np.int64) << 16) | (a[..., 1].astype(np.int64) << 8) | a[..., 2].astype(np.int64)
        qp = np.pad(q, 1, mode='wrap')
        nb = np.stack([qp[1 + dy:qp.shape[0] - 1 + dy, 1 + dx:qp.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx], -1)
        lonely = ~(nb == q[..., None]).any(-1)
        if alpha is not None: lonely &= alpha
        ys, xs = np.nonzero(lonely)
        for y, x in zip(ys, xs):
            vals, cnt = np.unique(nb[y, x], return_counts=True); v = vals[np.argmax(cnt)]
            a[y, x] = [(v >> 16) & 255, (v >> 8) & 255, v & 255]
    return a


def key_mid(guide_alpha_png, thresh=0.5, dilate=0):
    """1x binary alpha from the 3x guide coverage."""
    a = Image.open(guide_alpha_png).convert('L').resize((W, H), Image.BOX)
    if dilate: a = a.filter(ImageFilter.MaxFilter(1 + 2 * dilate))
    return np.asarray(a, float) / 255 >= thresh


def rim(arr, alpha, col, col2=None, side='top'):
    """1px rim light on edges whose neighbour (above / above-left) is transparent; col2 (optional) for the 2nd px."""
    out = arr.copy(); ap = np.pad(alpha, 1, mode='wrap')
    up = ~ap[0:-2, 1:-1]; left = ~ap[1:-1, 0:-2]
    e1 = alpha & (up | (left if side == 'topleft' else False))
    out[e1] = col
    if col2 is not None:
        e2 = alpha & ~e1 & np.roll(e1, 1, axis=0)
        out[e2] = col2
    return out


def to_rgba(arr, alpha=None):
    a = np.clip(arr, 0, 255).astype(np.uint8)
    al = np.full(a.shape[:2], 255, np.uint8) if alpha is None else (alpha * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, al]), 'RGBA')


def seam_score(img):
    x = np.asarray(img.convert('RGB'), float); d = np.abs(x[:, 1:] - x[:, :-1]).sum(2).mean(); w = np.abs(x[:, 0] - x[:, -1]).sum(1).mean()
    return round(w / d, 2)


def repeat_score(img):
    a = np.asarray(img.convert('RGBA'), float); al = a[..., 3] > 0
    lum = (a[..., :3] * np.array([0.299, 0.587, 0.114])).sum(-1); prof = np.where(al, lum, 0).mean(0); prof -= prof.mean()
    best = 0
    for s in range(24, 257):
        c = (prof * np.roll(prof, s)).sum() / (prof ** 2).sum(); best = max(best, c)
    return round(float(best), 2)


def stats(img):
    a = np.asarray(img.convert('RGBA'), float); al = a[..., 3] > 0; lum = (a[..., :3] * np.array([0.299, 0.587, 0.114])).sum(-1)
    return dict(colors=len({tuple(p) for p in a.reshape(-1, 4)[al.ravel()]}), lum=round(float(lum[al].mean()), 1),
                dark=round(float((lum[al] < 20).mean()), 2), seam=seam_score(img), repeat=repeat_score(img))


# ----------------------------------------------------------------------------------------------- per-biome driver
def lora_set(pix=0.6):
    return [('pixel-art-xl.safetensors', pix), ('sdxl_lightning_8step_lora.safetensors', 1.0)]


def render_layer(src, layer, prompt, seed, denoise, cn, cn_end, pix, guide_blur=1.5, seam_band=128, seam_dn=0.5, seam_seed=None, ref=None, ref_w=0.35):
    """guide_<layer>.png + edge_<layer>.png in `src` -> <layer>_render.png (seamless, 3x). Returns seconds."""
    g = Image.open(f'{src}/guide_{layer}.png').filter(ImageFilter.GaussianBlur(guide_blur)); gp = f'{src}/_gblur_{layer}.png'; g.save(gp)
    raw = f'{src}/{layer}_pass1.png'; L = lora_set(pix)
    t = render(gp, f'{src}/edge_{layer}.png', prompt, seed, raw, denoise=denoise, cn=cn, cn_end=cn_end, loras=L, ref_png=ref, ref_w=ref_w)
    t += seam_pass(raw, prompt, seam_seed or seed + 100, f'{src}/{layer}_render.png', band=seam_band, denoise=seam_dn, loras=L, ref_png=ref, ref_w=ref_w)
    os.remove(gp)
    return t


def far_pipeline(render_png, pal, n_acc=8, grade_kw=None, post=None, dither=True, dk=0.55):
    a = np.asarray(Image.open(render_png).convert('RGB'), float)
    if grade_kw: a = grade(a, **grade_kw)
    if post: a = post(a, 'hi')
    s = box_down(a)
    if post: s = post(s, 'lo')
    acc = pick_accents(s, pal, n=n_acc)
    P = [tuple(c) for c in pal] + acc
    q = palette_lock(s, P, dither_flat=dither, dk=dk)
    q = majority(q)
    return q, acc


def mid_pipeline(render_png, alpha_png, pal, n_acc=4, grade_kw=None, post=None, rim_col=None, rim_col2=None, dither=False):
    a = np.asarray(Image.open(render_png).convert('RGB'), float)
    if grade_kw: a = grade(a, **grade_kw)
    s = box_down(a); al = key_mid(alpha_png)
    if post: s = post(s, 'lo')
    acc = pick_accents(s, pal, n=n_acc, mask=al)
    q = palette_lock(s, [tuple(c) for c in pal] + acc, dither_flat=dither)
    q = majority(q, alpha=al)
    if rim_col is not None: q = rim(q, al, rim_col, rim_col2)
    q = np.where(al[..., None], q, 0)
    return q, al, acc


def ase_build(name, rgba):
    import asebuild
    asebuild.build(name, W, H, ['Layer'], [{'ms': 1000, 'cels': {'Layer': rgba}}], [('loop', 0, 0)])
    j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    assert len(j['frames']) == 1 and [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']] == [('loop', 0, 0)]
    assert (j['frames'][0]['sourceSize']['w'], j['frames'][0]['sourceSize']['h']) == (W, H)


def preview(far, mid_rgba, tint, out_png, cams=(0, 700, 1400)):
    """Parallax-only composites (tint + far + mid) at a few camera x, as drawParallax() lays them out, 2x."""
    far_im = far if isinstance(far, Image.Image) else to_rgba(far)
    rows = []
    for cx in cams:
        c = Image.new('RGBA', (384, 216), tint)
        for L, fac in ((far_im, 0.08), (mid_rgba, 0.3)):
            ox = -((cx * fac) % W); x = round(ox)
            while x < 384: c.alpha_composite(L, (x, 0)); x += W
        rows.append(c)
    out = Image.new('RGBA', (384 * len(rows) + 8 * (len(rows) - 1), 216), '#111')
    for i, r in enumerate(rows): out.alpha_composite(r, (i * 392, 0))
    out.resize((out.width * 2, out.height * 2), Image.NEAREST).save(out_png)
