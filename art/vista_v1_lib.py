"""Vista agent V1 helpers (docs/v17/vista_v1.md): painted, non-wrapping vista layers for the bench rooms.

The vista layers are single paintings (85_vistas.js `wrap: false`), sized to cover every camera position of their room, so
there is no wrap seam. Per room: `art/gen_vista_<room>.py` paints a value/colour guide at 3x (`VG`), renders it with the
bg pipeline's SDXL + pixel-art-xl + Lightning img2img + ControlNet lineart (`bgv2lib.render`), then BOX-downscales,
palette-locks and cleans it up to pixel art and builds the sheets with asebuild.

    geometry(room, layer)      which painting rows / cols each camera state shows (standing and seated)
    VG(w, h)                   guide painter (1x coordinates, drawn at 3x), with an alpha channel for cut-out layers
    sweep(...) / pick(...)     pass-1 renders for several seeds (+ contact sheet) / copy the picked one to <layer>_render.png
    pixelize(...)              render -> 1x pixel art (grade, BOX down, palette lock with ordered dither on flats, majority)
"""
import math, os, shutil, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bgv2lib as V

S = 3
W, H = 384, 216
ART = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(ART)

# camera states measured in game (tools/shots/v17/vista/cams_v1.js): x range, y range, the bench (standing) and the seat
CAMS = {
    'R11': dict(x=(0, 256), y=(-28, 0), stand=(140, 0), seat=(0, -28)),
    'K11': dict(x=(0, 256), y=(0, 104), stand=(12, 104), seat=(44, 0)),
    'M14': dict(x=(0, 96), y=(0, 40), stand=(44, 6), seat=(25, 0)),
    'A14': dict(x=(0, 0), y=(0, 8), stand=(0, 8), seat=(0, 0)),
    'HF14': dict(x=(0, 320), y=(-60, 136), stand=(60, 102), seat=(6, -60)),
    'SP15': dict(x=(0, 128), y=(0, 8), stand=(12, 0), seat=(0, 8)),
}


def place(L, cx, cy):
    """Where layer L (w, h, fac, vfac, x, dy) sits on screen at camera (cx, cy): (screen x of col 0, screen y of row 0),
    exactly as 85_vistas.js vistaLayer does it."""
    oy = round(min(20, max(-(L['h'] - H) - 20, -cy * L.get('vfac', 0)))) + (H - L['h']) + L.get('dy', 0)
    return round(L.get('x', 0) - cx * L.get('fac', 0)), oy


def geometry(room, L):
    c = CAMS[room]; out = {}
    for k, (cx, cy) in dict(stand=c['stand'], seat=c['seat'], x0y0=(c['x'][0], c['y'][0]), x1y1=(c['x'][1], c['y'][1]),
                            x0y1=(c['x'][0], c['y'][1]), x1y0=(c['x'][1], c['y'][0])).items():
        sx, sy = place(L, cx, cy)
        out[k] = dict(cols=(-sx, -sx + W), rows=(-sy, -sy + H), ok=(sx <= 0 and sx + L['w'] >= W and sy <= 0 and sy + L['h'] >= H))
    return out


# ------------------------------------------------------------------------------------------------ guide painter
class VG:
    """A layout/value sketch at 3x for a w x h (1x) painting. Coordinates in 1x px. No wrap."""

    def __init__(self, w, h, base=(0, 0, 0), alpha=False):
        self.w, self.h = w, h; self.WS, self.HS = w * S, h * S
        self.rgb = np.zeros((self.HS, self.WS, 3)); self.rgb[:] = base
        self.a = np.zeros((self.HS, self.WS)) if alpha else None
        yy, xx = np.mgrid[0:self.HS, 0:self.WS]; self.X = (xx + 0.5) / S; self.Y = (yy + 0.5) / S

    def poly(self, pts, blur=0.0):
        m = Image.new('L', (self.WS, self.HS), 0); ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in pts], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def lines(self, segs, blur=0.0):
        m = Image.new('L', (self.WS, self.HS), 0); d = ImageDraw.Draw(m)
        for x0, y0, x1, y1, w in segs:
            ww = max(1, int(round(w * S))); d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=255, width=ww); r = ww / 2
            for px, py in ((x0, y0), (x1, y1)): d.ellipse([px * S - r, py * S - r, px * S + r, py * S + r], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def ellipse(self, cx, cy, rx, ry, soft=1.0):
        d = np.sqrt(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        return np.clip((1 - d) * max(rx, ry) * S * soft, 0, 1)

    def radial(self, cx, cy, rx, ry, p=2.0):
        d = np.sqrt(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2); return np.clip(1 - d, 0, 1) ** p

    def vgrad(self, stops, x=None):
        """Vertical gradient image from [(y, (r,g,b)), ...] (1x rows)."""
        ys = np.array([s[0] for s in stops], float); cs = np.array([s[1] for s in stops], float)
        Y = self.Y[:, 0]; img = np.stack([np.interp(Y, ys, cs[:, i]) for i in range(3)], -1)
        return np.broadcast_to(img[:, None, :], (self.HS, self.WS, 3)).copy()

    def noise(self, cell_x, cell_y, seed, octaves=3):
        """Value noise on the 3x grid (cells in 1x px)."""
        cx, cy = cell_x * S, cell_y * S; w = int(math.ceil(self.WS / cx) * cx)
        return V.tile_noise(w, self.HS, int(cx), int(cy), seed, octaves)[:, :self.WS]

    def fill(self, mask, col, alpha=1.0, cover=True):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]
        self.rgb = self.rgb * (1 - m) + np.asarray(col, float) * m
        if self.a is not None and cover: self.a = np.maximum(self.a, np.clip(mask, 0, 1) * (1 if alpha > 0.5 else 0))

    def fill_img(self, mask, img, alpha=1.0, cover=True):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]; self.rgb = self.rgb * (1 - m) + img * m
        if self.a is not None and cover: self.a = np.maximum(self.a, np.clip(mask, 0, 1))

    def add(self, mask, col, k=1.0):
        k = np.asarray(k, float); k = k[..., None] if k.ndim == 2 else k
        self.rgb = self.rgb + np.clip(mask, 0, 1)[..., None] * np.asarray(col, float) * k

    def glow(self, cx, cy, rx, ry, col, k=1.0, p=2.0):
        self.add(self.radial(cx, cy, rx, ry, p), col, k)

    def image(self):
        return Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8))

    def save(self, src, layer, edge_lo=14, edge_blur=0.6):
        os.makedirs(src, exist_ok=True)
        im = self.image(); im.save(f'{src}/guide_{layer}.png')
        V.edges_of(im, lo=edge_lo, blur=edge_blur).save(f'{src}/edge_{layer}.png')
        if self.a is not None: Image.fromarray((np.clip(self.a, 0, 1) * 255).astype(np.uint8)).save(f'{src}/alpha_{layer}.png')
        im.resize((self.w, self.h), Image.BOX).resize((self.w * 2, self.h * 2), Image.NEAREST).save(f'{src}/guide_{layer}_1x.png')


def smooth_curve(xs, ys, xx, k=None):
    """A smooth curve through control points (linear interp, then a wide box smoothing; no scipy here)."""
    y = np.interp(xx, xs, ys); step = xx[1] - xx[0] if len(xx) > 1 else 1
    k = k or max(1, int(round(np.min(np.diff(xs)) * 0.45 / step)))
    pad = np.pad(y, k, mode='edge'); ker = np.ones(2 * k + 1) / (2 * k + 1)
    for _ in range(2): pad = np.convolve(pad, ker, mode='same')
    return pad[k:-k]


def profile(w, seed, base, amp, cells=((40, 1.0), (13, 0.45), (5, 0.18)), lo=None):
    """1-D ridge profile (1x px, w + 1 samples): y = base - amp * noise."""
    rng = np.random.default_rng(seed); x = np.arange(w + 1, dtype=float); y = np.zeros_like(x); tot = 0
    for cell, k in cells:
        n = int(w / cell) + 3; pts = rng.random(n); xi = x / cell; i0 = np.floor(xi).astype(int); t = xi - i0; t = t * t * (3 - 2 * t)
        y += k * (pts[i0] * (1 - t) + pts[i0 + 1] * t); tot += k
    return base - amp * y / tot


# ------------------------------------------------------------------------------------------------ render side
def use_prefix(room):
    c = V._comfy()
    run0 = getattr(c, '_v1_run0', c.run); c._v1_run0 = run0
    def run(wf, out):
        for n in wf.values():
            if n.get('class_type') == 'SaveImage': n['inputs']['filename_prefix'] = f'vista_v1/{room}'
        return run0(wf, out)
    c.run = run


def sweep(room, src, layer, prompt, seeds, denoise, cn, cn_end, pix, blur=1.2, tag='', ckpt=None):
    use_prefix(room); os.makedirs(f'{src}/sweep', exist_ok=True)
    g = Image.open(f'{src}/guide_{layer}.png').filter(ImageFilter.GaussianBlur(blur)); gp = f'{src}/_gblur_{layer}.png'; g.save(gp)
    outs = []
    for s in seeds:
        o = f'{src}/sweep/{layer}{tag}_s{s}.png'
        V.render(gp, f'{src}/edge_{layer}.png', prompt, s, o, denoise=denoise, cn=cn, cn_end=cn_end, loras=V.lora_set(pix), ckpt=ckpt)
        outs.append(o); print('rendered', o, flush=True)
    os.remove(gp)
    contact(outs, f'{src}/sweep/{layer}{tag}_sheet.png')
    return outs


def contact(paths, out, w=None):
    ims = [Image.open(p).convert('RGB') for p in paths]; w = w or ims[0].width // S; h = round(ims[0].height / ims[0].width * w)
    ims = [im.resize((w, h), Image.BOX) for im in ims]
    cols = 2; rows = (len(ims) + 1) // 2; Sh = Image.new('RGB', (cols * (w + 6), rows * (h + 6)), (20, 20, 20)); d = ImageDraw.Draw(Sh)
    for i, (im, p) in enumerate(zip(ims, paths)):
        x, y = (i % cols) * (w + 6), (i // cols) * (h + 6); Sh.paste(im, (x, y)); d.text((x + 4, y + 2), os.path.basename(p), fill=(255, 60, 60))
    Sh.resize((Sh.width * 2, Sh.height * 2), Image.NEAREST).save(out)


def pick(src, layer, seed, tag=''):
    shutil.copy(f'{src}/sweep/{layer}{tag}_s{seed}.png', f'{src}/{layer}_render.png')


# ------------------------------------------------------------------------------------------------ build side
def kpal(arr, n, mask=None, seed=0):
    """A limited palette from the painting itself: k-means (Lab-ish via PIL median cut + kmeans) on the 1x image."""
    a = np.clip(arr, 0, 255).astype(np.uint8)
    if mask is not None:
        pix = a[mask]; side = int(math.ceil(math.sqrt(len(pix)))); buf = np.zeros((side * side, 3), np.uint8); buf[:len(pix)] = pix
        buf[len(pix):] = pix[0] if len(pix) else 0; a = buf.reshape(side, side, 3)
    q = Image.fromarray(a).quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=6, dither=Image.Dither.NONE)
    p = np.array(q.getpalette()[:n * 3]).reshape(-1, 3); used = np.unique(np.asarray(q))
    return [tuple(int(v) for v in p[i]) for i in used]


def pixelize(arr_hi, w, h, pal, dk=0.4, flat=6.0, alpha=None, passes=1):
    s = V.box_down(arr_hi, w, h)
    q = V.palette_lock(s, pal, dither_flat=dk > 0, flat_thresh=flat, dk=dk)
    q = V.majority(q, alpha=alpha, passes=passes)
    return q


def to_rgba(arr, alpha=None):
    return V.to_rgba(arr, alpha)


def ase(name, frames_rgba, ms=1000, tag='loop'):
    """frames_rgba: list of PIL RGBA images (same size) -> art/<name>.aseprite + assets/<name>.png/.json, tag `loop`."""
    import asebuild
    w, h = frames_rgba[0].size
    asebuild.build(name, w, h, ['Layer'], [{'ms': ms, 'cels': {'Layer': f}} for f in frames_rgba], [(tag, 0, len(frames_rgba) - 1)])
    j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    assert len(j['frames']) == len(frames_rgba) and j['meta']['frameTags'][0]['name'] == tag
    assert (j['frames'][0]['sourceSize']['w'], j['frames'][0]['sourceSize']['h']) == (w, h)


def comp_preview(room, layers, tint, out, scale=2, fx=None):
    """Parallax-only composites of the vista layers at the stand and seat cameras (as 85_vistas.js draws them)."""
    c = CAMS[room]; rows = []
    for cx, cy in (c['stand'], c['seat']):
        cv = Image.new('RGBA', (W, H), tint)
        for L, im in layers:
            sx, sy = place(L, cx, cy); a = L.get('alpha', 1)
            if a < 1: im = im.copy(); im.putalpha(Image.fromarray((np.asarray(im)[..., 3] * a).astype(np.uint8)))
            cv.alpha_composite(im, (0, 0), (max(0, -sx), max(0, -sy))) if False else cv.paste(im, (sx, sy), im)
        rows.append(cv)
    o = Image.new('RGBA', (W * 2 + 8, H), '#111'); o.paste(rows[0], (0, 0)); o.paste(rows[1], (W + 8, 0))
    o.resize((o.width * scale, o.height * scale), Image.NEAREST).save(out)


def cli(M, argv=None):
    """Shared command line of the art/gen_vista_<room>.py scripts (module M: ROOM, SRC, RENDER, PROMPTS {layer: prompt},
    guides() -> {layer: VG} (+ optional extra files), build(no_ase)).
      (no args)                 build from the saved renders
      --guide                   only (re)paint the guides
      --sweep <layer> 1,2,3 [--dn x --cn x --pix x --tag t]   pass-1 renders (ComfyUI :8188) + contact sheet in sweep/
      --render                  guides + render the picked seeds (RENDER, incl. tag), then build
      --no-ase                  previews only, leave the assets alone"""
    args = sys.argv[1:] if argv is None else argv
    os.makedirs(M.SRC, exist_ok=True)
    if '--guide' in args or '--sweep' in args or '--render' in args:
        for layer, G in M.guides().items(): G.save(M.SRC, layer)
    if '--sweep' in args:
        i = args.index('--sweep'); layer = args[i + 1]; seeds = [int(s) for s in args[i + 2].split(',')]
        R = dict(M.RENDER[layer])
        for k in ('dn', 'cn', 'pix'):
            if f'--{k}' in args: R[k] = float(args[args.index(f'--{k}') + 1])
        tag = args[args.index('--tag') + 1] if '--tag' in args else ''
        sweep(M.ROOM, M.SRC, layer, M.PROMPTS[layer], seeds, R['dn'], R['cn'], R['cn_end'], R['pix'], tag=tag, blur=R.get('blur', 1.2))
    elif '--render' in args:
        for layer, R in M.RENDER.items():
            sweep(M.ROOM, M.SRC, layer, M.PROMPTS[layer], [R['seed']], R['dn'], R['cn'], R['cn_end'], R['pix'], tag=R.get('tag', ''), blur=R.get('blur', 1.2))
            pick(M.SRC, layer, R['seed'], tag=R.get('tag', ''))
        M.build('--no-ase' in args)
    elif '--guide' not in args:
        M.build('--no-ase' in args)
