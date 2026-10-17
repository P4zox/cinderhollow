"""Vista agent V2 helpers (docs/v17/vista_v2.md) on top of bgv2lib: one painted composition per bench room, split into
depth layers with clean alpha.

  Canvas(w, h)           a 3x layout/value sketch of any size (no wrap unless wrap=True); masks + paint like bgv2lib.Guide
  render(...)            ComfyUI img2img (SDXL + pixel-art-xl + Lightning, ControlNet lineart from the guide's edges), outputs
                         go to output/vista_v2/<room>_* on the shared server
  sweep(...)             several seeds -> <src>/sweep/<name>_s<seed>.png + a contact sheet
  to_pixels(...)         BOX down to 1x, k-means palette (+ optional fixed colours), Lab lock with flat-area Bayer dither,
                         orphan cleanup
  key(mask3x)            1x binary alpha from a 3x coverage mask
  build(name, layers)    Aseprite source + sheet (any size, 1 frame or several, tag 'loop')
"""
import math, os, sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ART = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ART)
import bgv2lib as V

S = 3
ROOT = V.ROOT


# ----------------------------------------------------------------------------------------------- guide canvas
class Canvas:
    def __init__(self, w, h, base=(0, 0, 0), wrap=False):
        self.w, self.h, self.wrap = w, h, wrap
        self.WS, self.HS = w * S, h * S
        self.rgb = np.zeros((self.HS, self.WS, 3)); self.rgb[:] = base
        yy, xx = np.mgrid[0:self.HS, 0:self.WS]
        self.X = (xx + 0.5) / S; self.Y = (yy + 0.5) / S

    def _dxs(self):
        return (-self.w, 0, self.w) if self.wrap else (0,)

    def mask_poly(self, pts, blur=0.0):
        m = Image.new('L', (self.WS, self.HS), 0); d = ImageDraw.Draw(m)
        for dx in self._dxs(): d.polygon([((x + dx) * S, y * S) for x, y in pts], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def mask_lines(self, segs, blur=0.0):
        m = Image.new('L', (self.WS, self.HS), 0); d = ImageDraw.Draw(m)
        for dx in self._dxs():
            for x0, y0, x1, y1, w in segs:
                ww = max(1, int(round(w * S)))
                d.line([((x0 + dx) * S, y0 * S), ((x1 + dx) * S, y1 * S)], fill=255, width=ww)
                r = ww / 2
                for (px, py) in ((x0, y0), (x1, y1)): d.ellipse([(px + dx) * S - r, py * S - r, (px + dx) * S + r, py * S + r], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def dx(self, cx):
        return ((self.X - cx + self.w / 2) % self.w - self.w / 2) if self.wrap else (self.X - cx)

    def ellipse(self, cx, cy, rx, ry):
        d = np.sqrt((self.dx(cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        return np.clip((1 - d) * max(rx, ry) * S, 0, 1)

    def radial(self, cx, cy, rx, ry, p=2.0):
        d = np.sqrt((self.dx(cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        return np.clip(1 - d, 0, 1) ** p

    def vgrad(self, stops):
        """Vertical gradient from [(y, rgb), ...] (1x y, sorted)."""
        ys = np.array([s[0] for s in stops], float); cs = np.array([s[1] for s in stops], float)
        y = self.Y[:, 0]
        out = np.stack([np.interp(y, ys, cs[:, i]) for i in range(3)], -1)
        return np.broadcast_to(out[:, None, :], self.rgb.shape).copy()

    def fill(self, mask, col, alpha=1.0):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]
        col = np.asarray(col, float)
        self.rgb = self.rgb * (1 - m) + col * m

    def add(self, mask, col, k=1.0):
        k = np.asarray(k, float); k = k[..., None] if k.ndim == 2 else k
        self.rgb = self.rgb + np.clip(mask, 0, 1)[..., None] * np.asarray(col, float) * k

    def image(self):
        return Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8))

    def noise(self, cell_x, cell_y, seed, octaves=3):
        """value noise over the canvas (1x cell sizes)."""
        rng = np.random.default_rng(seed); out = np.zeros((self.HS, self.WS)); amp = 1.0; tot = 0.0
        for o in range(octaves):
            cx, cy = max(1, cell_x / 2 ** o), max(1, cell_y / 2 ** o)
            nx, ny = int(self.w / cx) + 3, int(self.h / cy) + 3
            grid = rng.random((ny, nx))
            xs = self.X[0] / cx; ys = self.Y[:, 0] / cy
            x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
            tx = xs - x0; ty = ys - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
            if self.wrap: x0m, x1m = x0 % (nx - 3), (x0 + 1) % (nx - 3)
            else: x0m, x1m = x0, x0 + 1
            a = grid[y0][:, x0m]; b = grid[y0][:, x1m]; c = grid[y0 + 1][:, x0m]; d = grid[y0 + 1][:, x1m]
            top = a + (b - a) * tx[None]; bot = c + (d - c) * tx[None]
            out += amp * (top + (bot - top) * ty[:, None]); tot += amp; amp *= 0.5
        return out / tot


def profile(w, base, amps, seed, wrap=False):
    """A 1-D ridge profile (1x px, len w): base + sum of sines/noise."""
    rng = np.random.default_rng(seed); x = np.arange(w + 1, dtype=float); y = np.full_like(x, base)
    for per, amp in amps:
        ph = rng.uniform(0, 2 * math.pi)
        if wrap: per = w / max(1, round(w / per))
        y += amp * np.sin(2 * math.pi * x / per + ph)
    return y


def ridge_pts(prof, bottom):
    pts = [(i, float(v)) for i, v in enumerate(prof)]
    return pts + [(len(prof) - 1, bottom), (0, bottom)]


def edges(img, lo=14, blur=0.6):
    return V.edges_of(img, lo, blur)


# ----------------------------------------------------------------------------------------------- ComfyUI
def use_prefix(room):
    c = V._comfy()
    if getattr(c, '_v2_prefixed', None) == room: return
    run0 = getattr(c, '_v2_run0', c.run); c._v2_run0 = run0
    def run(wf, out):
        for n in wf.values():
            if n.get('class_type') == 'SaveImage': n['inputs']['filename_prefix'] = f'vista_v2/{room}'
        return run0(wf, out)
    c.run = run; c._v2_prefixed = room


def render(guide_png, edge_png, prompt, seed, out_png, denoise=0.7, cn=0.45, cn_end=0.6, pix=0.5, blur=1.2, ckpt=None):
    g = Image.open(guide_png).convert('RGB')
    if blur: g = g.filter(ImageFilter.GaussianBlur(blur))
    gp = out_png + '.gblur.png'; g.save(gp)
    try:
        return V.render(gp, edge_png, prompt, seed, out_png, denoise=denoise, cn=cn, cn_end=cn_end, loras=V.lora_set(pix), ckpt=ckpt)
    finally:
        os.remove(gp)


def sweep(src, name, prompt, seeds, tag='', **kw):
    os.makedirs(f'{src}/sweep', exist_ok=True)
    outs = []
    for s in seeds:
        o = f'{src}/sweep/{name}{tag}_s{s}.png'
        if not os.path.exists(o): render(f'{src}/guide_{name}.png', f'{src}/edge_{name}.png', prompt, s, o, **kw)
        outs.append(o)
    contact(outs, f'{src}/sweep/{name}{tag}_sheet.png')
    return outs


def contact(paths, out, width=600):
    ims = [Image.open(p).convert('RGB') for p in paths]
    w0, h0 = ims[0].size; sc = width / w0; tw, th = width, int(h0 * sc)
    cols = 2; rows = (len(ims) + 1) // 2
    Sh = Image.new('RGB', (cols * (tw + 6), rows * (th + 6)), (20, 20, 20)); d = ImageDraw.Draw(Sh)
    for i, (im, p) in enumerate(zip(ims, paths)):
        x, y = (i % cols) * (tw + 6), (i // cols) * (th + 6)
        Sh.paste(im.resize((tw, th), Image.LANCZOS), (x, y)); d.text((x + 4, y + 2), os.path.basename(p), fill=(255, 60, 60))
    Sh.save(out)


# ----------------------------------------------------------------------------------------------- build side
def down(arr_or_img, w, h):
    im = arr_or_img if isinstance(arr_or_img, Image.Image) else Image.fromarray(np.clip(arr_or_img, 0, 255).astype(np.uint8))
    return np.asarray(im.convert('RGB').resize((w, h), Image.BOX), float)


def kpal(arr, n, mask=None, fixed=()):
    """n representative colours of arr (inside mask) by median cut + k-means, plus fixed colours."""
    a = arr if mask is None else arr[mask]
    a = a.reshape(-1, 3)
    if len(a) == 0: return [tuple(c) for c in fixed]
    side = int(math.ceil(math.sqrt(len(a)))); pad = np.zeros((side * side, 3)); pad[:len(a)] = a; pad[len(a):] = a[0]
    im = Image.fromarray(pad.reshape(side, side, 3).astype(np.uint8))
    q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=6, dither=Image.Dither.NONE)
    p = np.array(q.getpalette()[:n * 3], float).reshape(-1, 3)
    cnt = np.bincount(np.asarray(q).ravel(), minlength=n)
    pal = [tuple(c) for c, k in zip(p, cnt) if k > 0]
    return pal + [tuple(float(v) for v in c) for c in fixed]


def to_pixels(arr1x, n, mask=None, fixed=(), dither=True, dk=0.4, flat=6.0, clean=True, hi=0, hi_lum=170, lo=0, lo_lum=40):
    """k-means palette; hi / lo add that many extra colours fitted to the bright / dark pixels only (a moon's maria, a sun's
    rings and the shadow ramps otherwise collapse into one colour each)."""
    pal = kpal(arr1x, n, mask, fixed)
    l = lum(arr1x); base = np.ones(l.shape, bool) if mask is None else mask
    if hi and (base & (l > hi_lum)).sum() > hi * 4: pal += kpal(arr1x, hi, base & (l > hi_lum))
    if lo and (base & (l < lo_lum)).sum() > lo * 4: pal += kpal(arr1x, lo, base & (l < lo_lum))
    q = V.palette_lock(arr1x, pal, dither_flat=dither, flat_thresh=flat, dk=dk)
    if clean: q = V.majority(q, alpha=mask)
    return q, pal


def key(mask3x, w, h, thresh=0.5, close=0):
    m = Image.fromarray((np.clip(mask3x, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BOX)
    if close:
        m = m.filter(ImageFilter.MaxFilter(1 + 2 * close)).filter(ImageFilter.MinFilter(1 + 2 * close))
    a = np.asarray(m, float) / 255 >= thresh
    # drop isolated alpha specks
    p = np.pad(a, 1); nb = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx].astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return a & (nb >= 2)


def rgba(arr, alpha=None):
    return V.to_rgba(arr, alpha)


def build(name, frames, ms=1000, durs=None):
    """frames: list of RGBA images (same size). -> art/<name>.aseprite + assets/<name>.png/.json, tag 'loop' over all."""
    import asebuild
    w, h = frames[0].size
    fr = [{'ms': (durs[i] if durs else ms), 'cels': {'Layer': im}} for i, im in enumerate(frames)]
    asebuild.build(name, w, h, ['Layer'], fr, [('loop', 0, len(frames) - 1)])
    j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    assert len(j['frames']) == len(frames)
    assert (j['frames'][0]['sourceSize']['w'], j['frames'][0]['sourceSize']['h']) == (w, h)


def lum(a):
    return (np.asarray(a, float)[..., :3] * np.array([0.299, 0.587, 0.114])).sum(-1)


def composite_preview(layers, out_png, cams, W=384, H=216, tint=(10, 10, 16), scale=2):
    """layers: [(rgba Image, fac, vfac, x, wrap)], cams: [(cam_x, cam_y)] -> side-by-side previews as the engine lays them out."""
    rows = []
    for cx, cy in cams:
        c = Image.new('RGBA', (W, H), tint + (255,))
        for im, fac, vfac, x0, wrap in layers:
            fh = im.height; s = max(-(fh - H) - 20, min(20, -cy * vfac)); oy = round(s) + (H - fh)
            if wrap:
                ox = -((cx * fac) % im.width); x = round(ox)
                while x < W: c.alpha_composite(im, (x, oy)) if 0 else _paste(c, im, x, oy); x += im.width
            else:
                _paste(c, im, round(x0 - cx * fac), oy)
        rows.append(c)
    out = Image.new('RGBA', (W * len(rows) + 6 * (len(rows) - 1), H), (17, 17, 17, 255))
    for i, r in enumerate(rows): out.alpha_composite(r, (i * (W + 6), 0))
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(out_png)


def _paste(c, im, x, y):
    tmp = Image.new('RGBA', c.size, (0, 0, 0, 0)); tmp.paste(im, (x, y)); c.alpha_composite(tmp)


# ----------------------------------------------------------------------------------------------- layer separation
def _box1(a, r, axis):
    if r < 1: return a
    n = a.shape[axis]; pad = [(0, 0)] * a.ndim; pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis); lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def gblur(a, s):
    """~Gaussian blur (3 box passes per axis) of a 2-D float array, sigma s px."""
    r = max(1, int(round(math.sqrt(12 * s * s / 3 + 1) - 1) // 2))
    for _ in range(3): a = _box1(_box1(a, r, 0), r, 1)
    return a


def fill_from_outside(arr, mask, sigmas=(2, 6, 18, 48)):
    """Fill the masked area of arr (float HxWx3) with colours pushed in from outside (normalized convolution, coarse to fine)."""
    gaussian_filter = gblur
    w = 1 - np.clip(mask, 0, 1)
    out = arr.copy()
    est = None
    for s in sorted(sigmas, reverse=True):
        num = np.stack([gaussian_filter(arr[..., i] * w, s) for i in range(3)], -1)
        den = gaussian_filter(w, s)[..., None]
        e = num / np.maximum(den, 1e-6)
        est = e if est is None else np.where(den > 0.05, e, est)
    return out * w[..., None] + est * (1 - w[..., None])


def dilate(mask, px):
    if px <= 0: return mask
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(m.filter(ImageFilter.MaxFilter(int(px) * 2 + 1)), float) / 255


def erode(mask, px):
    if px <= 0: return mask
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(m.filter(ImageFilter.MinFilter(int(px) * 2 + 1)), float) / 255


def feather(mask, px):
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(m.filter(ImageFilter.GaussianBlur(px)), float) / 255


def inpaint(src_png, mask3x, prompt, seed, out_png, denoise=0.75, pix=0.45, prefill=True, feather_px=6, cn=0.0, edge_png=None, cn_end=0.6):
    """Regenerate only the masked area of a 3x render (SetLatentNoiseMask); the masked area is pre-filled with colours pushed in
    from outside, so the model paints sky / water / shore there instead of the old silhouette. Composite back with a feathered mask."""
    c = V._comfy(); work = os.path.dirname(out_png)
    a = np.asarray(Image.open(src_png).convert('RGB'), float)
    m = np.clip(mask3x, 0, 1)
    base = fill_from_outside(a, m) if prefill else a
    bp = out_png + '.base.png'; Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save(bp)
    mf = feather(dilate(m, 2), feather_px); mp = out_png + '.mask.png'; Image.fromarray((mf * 255).astype(np.uint8)).save(mp)
    ub, um = c.upload(bp), c.upload(mp)
    ue = c.upload(edge_png) if (cn and edge_png) else None
    wf = c.workflow(prompt, seed, init_image=ub, denoise=denoise, negative=V.NEG, loras=V.lora_set(pix),
                    pose=ue, pose_type='canny/lineart/anime_lineart/mlsd', pose_strength=cn)
    if ue: wf['43']['inputs']['end_percent'] = cn_end
    wf['50'] = {'class_type': 'LoadImage', 'inputs': {'image': um}}
    wf['51'] = {'class_type': 'ImageToMask', 'inputs': {'image': ['50', 0], 'channel': 'red'}}
    wf['52'] = {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': ['21', 0], 'mask': ['51', 0]}}
    wf['7']['inputs']['latent_image'] = ['52', 0]
    tmp = out_png + '.gen.png'; c.run(wf, tmp)
    g2 = np.asarray(Image.open(tmp).convert('RGB').resize((a.shape[1], a.shape[0])), float)
    comp = g2 * mf[..., None] + a * (1 - mf[..., None])
    Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).save(out_png)
    for p in (bp, mp, tmp): os.remove(p)
    return out_png


def seg_dark(hero, prior, grow=6, margin=10.0, core=2, sky_mask=None):
    """Silhouette mask on a 3x render: pixels darker than the local sky estimate (the render with the prior pushed out) by
    `margin`, inside the prior dilated by `grow` 1x px, plus the prior's eroded core. Returns 3x float mask."""
    zone = dilate(prior, grow * S)
    ref = fill_from_outside(hero, zone)
    d = lum(ref) - lum(hero)
    m = ((d > margin) & (zone > 0.5)) | (erode(prior, core * S) > 0.5)
    return m.astype(float)
