"""Vista agent V3 helpers (docs/v17/vista_v3.md, brief docs/v17/VISTA_BRIEF.md) on top of bgv2lib.

Painted bench views are single postcards, not tiling strips: every layer is a fixed-size painting (no seam pass) shown
through a 384x216 window that barely moves (the vista rooms are small; CT2 is the exception and gets wider layers).

  Canvas(w, h)        a guide painter at 3x for any layer size (no wrap); same paint verbs as bgv2lib.Guide
  use_prefix(room)    every ComfyUI SaveImage of this process goes to output/vista_v3/<room>_* (the server is shared)
  render(...)         img2img over a guide (optional ControlNet lineart from its edges), any size
  sweep(...)          several seeds -> <src>/sweep/<name>_s<seed>.png + a contact sheet
  pixelize(...)       BOX down to 1x, palette lock (region ramps + k-means accents), ordered dither on flats, orphans out
  key_flat(...)       1x binary alpha for a layer rendered on a flat key colour, limited to the guide's coverage
  stars(...)          crisp 1 px stars / 3 px cross stars stamped after the palette lock (the model paints mush)
  build(name, frames) asebuild with tag 'loop' (1+ frames), any size
"""
import json, math, os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bgv2lib as V  # noqa: E402
from bgv2lib import hexc, lerp, smooth, grade, palette_lock, majority, pick_accents, _lab  # noqa: E402,F401

S = 3
ROOT = os.path.dirname(HERE)


def src_dir(room):
    d = os.path.join(HERE, 'bg_src', f'vista_{room.lower()}'); os.makedirs(d, exist_ok=True); return d


def noise(w, h, cx, cy, seed, octaves=3):
    """Value noise (not tileable), w x h, cell sizes cx, cy (px of the grid it is sampled on)."""
    rng = np.random.default_rng(seed); out = np.zeros((h, w)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        sx, sy = max(1, cx >> o), max(1, cy >> o)
        nx, ny = w // sx + 3, h // sy + 3
        grid = rng.random((ny, nx))
        xs = np.arange(w) / sx; ys = np.arange(h) / sy
        x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
        tx = xs - x0; ty = ys - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
        a = grid[y0][:, x0]; b = grid[y0][:, x0 + 1]; c = grid[y0 + 1][:, x0]; d = grid[y0 + 1][:, x0 + 1]
        top = a + (b - a) * tx[None]; bot = c + (d - c) * tx[None]
        out += amp * (top + (bot - top) * ty[:, None]); tot += amp; amp *= 0.5
    return out / tot


class Canvas:
    """Guide painter at 3x for a w x h (1x) layer. Coordinates in 1x px. rgb float HxWx3, a = coverage (alpha layers)."""

    def __init__(self, w, h, base=(0, 0, 0), alpha=False):
        self.w, self.h = w, h; self.WS, self.HS = w * S, h * S
        self.rgb = np.zeros((self.HS, self.WS, 3)); self.rgb[:] = base
        self.a = np.zeros((self.HS, self.WS)) if alpha else None
        yy, xx = np.mgrid[0:self.HS, 0:self.WS]
        self.X = (xx + 0.5) / S; self.Y = (yy + 0.5) / S

    def noise(self, cx, cy, seed, octaves=3):
        return noise(self.WS, self.HS, int(cx * S), int(cy * S), seed, octaves)

    def mask_poly(self, pts, blur=0.0):
        m = Image.new('L', (self.WS, self.HS), 0); ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in pts], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def mask_lines(self, segs, blur=0.0):
        m = Image.new('L', (self.WS, self.HS), 0); d = ImageDraw.Draw(m)
        for x0, y0, x1, y1, w in segs:
            ww = max(1, int(round(w * S))); r = ww / 2
            d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=255, width=ww)
            for px, py in ((x0, y0), (x1, y1)): d.ellipse([px * S - r, py * S - r, px * S + r, py * S + r], fill=255)
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(m, float) / 255

    def mask_ellipse(self, cx, cy, rx, ry, soft=1.0):
        d = np.sqrt(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        return np.clip((1 - d) * max(rx, ry) * S * soft, 0, 1)

    def mask_below(self, prof, soft=1.0):
        """prof: 1-D array of length WS (a y per 3x column, in 1x px) -> coverage below it."""
        return np.clip((self.Y - np.asarray(prof)[None, :]) * S / soft + 0.5, 0, 1)

    def profile(self, base, amps, seed, cells=(60, 20, 7)):
        """A ridge line: base y (scalar or array over 3x cols) + noise octaves (amps per cell size)."""
        p = np.zeros(self.WS) + base
        for i, (a, c) in enumerate(zip(amps, cells)):
            p = p + a * (noise(self.WS, 1, int(c * S), 1, seed + i, 1)[0] - 0.5) * 2
        return p

    def fill(self, mask, col, alpha=1.0, cover=True):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]
        self.rgb = self.rgb * (1 - m) + np.asarray(col, float) * m
        if self.a is not None and cover: self.a = np.maximum(self.a, np.clip(mask, 0, 1) * (1 if alpha > 0.5 else 0))

    def fill_img(self, mask, img, alpha=1.0, cover=True):
        m = (np.clip(mask, 0, 1) * alpha)[..., None]
        self.rgb = self.rgb * (1 - m) + img * m
        if self.a is not None and cover: self.a = np.maximum(self.a, np.clip(mask, 0, 1) * (1 if alpha > 0.5 else 0))

    def add(self, mask, col, k=1.0):
        self.rgb = self.rgb + np.clip(mask, 0, 1)[..., None] * np.asarray(col, float) * k

    def glow(self, cx, cy, rx, ry, col, k=1.0, p=2.0):
        d = np.sqrt(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2)
        self.add(np.clip(1 - d, 0, 1) ** p, col, k)

    def vgrad(self, stops):
        """Vertical gradient from [(y, hex), ...] (1x y)."""
        ys = [s[0] for s in stops]; cs = [hexc(s[1]) for s in stops]
        out = np.zeros_like(self.rgb)
        for c in range(3): out[..., c] = np.interp(self.Y, ys, [q[c] for q in cs])
        return out

    def image(self):
        return Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8))

    def alpha_img(self):
        return Image.fromarray((np.clip(self.a, 0, 1) * 255).astype(np.uint8))

    def save(self, path, alpha_path=None):
        self.image().save(path)
        if alpha_path and self.a is not None: self.alpha_img().save(alpha_path)


def edges(img, lo=14, blur=0.6):
    return V.edges_of(img, lo, blur)


# ----------------------------------------------------------------------------------------------- ComfyUI side
def use_prefix(room):
    c = V._comfy()
    if getattr(c, '_v3_prefix', None) == room: return
    run0 = getattr(c, '_v3_run0', c.run); c._v3_run0 = run0

    def run(wf, out):
        for n in wf.values():
            if n.get('class_type') == 'SaveImage': n['inputs']['filename_prefix'] = f'vista_v3/{room.lower()}'
        return run0(wf, out)
    c.run = run; c._v3_prefix = room


NEG = V.NEG + ', figure, silhouette of a man, human, animal, bird, creature, monster, ufo, spaceship, logo'


def render(guide_png, prompt, seed, out_png, denoise=0.7, pix=0.5, edge_png=None, cn=0.4, cn_end=0.6, blur=1.2):
    c = V._comfy()
    g = Image.open(guide_png).convert('RGB')
    if blur: g = g.filter(ImageFilter.GaussianBlur(blur))
    tmp = out_png + '.guide.png'; g.save(tmp)
    up = c.upload(tmp); os.remove(tmp)
    kw = {}
    if edge_png:
        kw = dict(pose=c.upload(edge_png), pose_type='canny/lineart/anime_lineart/mlsd', pose_strength=cn)
    wf = c.workflow(prompt, seed, init_image=up, denoise=denoise, negative=NEG, loras=V.lora_set(pix), **kw)
    if edge_png: wf['43']['inputs']['end_percent'] = cn_end
    c.run(wf, out_png)
    return out_png


def sheet(paths, out, w=512, cols=2):
    ims = [Image.open(p).convert('RGB') for p in paths]
    ims = [im.resize((w, round(im.height * w / im.width)), Image.BOX) for im in ims]
    h = max(im.height for im in ims); rows = (len(ims) + cols - 1) // cols
    S_ = Image.new('RGB', (cols * (w + 6), rows * (h + 6)), (20, 20, 20)); d = ImageDraw.Draw(S_)
    for i, (im, p) in enumerate(zip(ims, paths)):
        x, y = (i % cols) * (w + 6), (i // cols) * (h + 6)
        S_.paste(im, (x, y)); d.text((x + 4, y + 2), os.path.basename(p), fill=(255, 60, 60))
    S_.save(out)


def sweep(src, name, guide_png, prompt, seeds, tag='', **kw):
    os.makedirs(f'{src}/sweep', exist_ok=True); outs = []
    for s in seeds:
        o = f'{src}/sweep/{name}{tag}_s{s}.png'; render(guide_png, prompt, s, o, **kw); outs.append(o)
    sheet(outs, f'{src}/sweep/{name}{tag}_sheet.png')
    return outs


def pick(src, name, seed, tag=''):
    """Copy the chosen sweep render to <name>_render.png (the build input; gitignored)."""
    shutil.copy(f'{src}/sweep/{name}{tag}_s{seed}.png', f'{src}/{name}_render.png')


# ----------------------------------------------------------------------------------------------- build side
def down(img_or_arr, w, h):
    im = img_or_arr if isinstance(img_or_arr, Image.Image) else Image.fromarray(np.clip(img_or_arr, 0, 255).astype(np.uint8))
    return np.asarray(im.convert('RGB').resize((w, h), Image.BOX), float)


def kpal(arr, n, mask=None):
    """n colours from a median-cut + k-means reduction of arr (optionally only where mask)."""
    a = arr if mask is None else arr[mask]
    a = a.reshape(-1, 1, 3) if mask is not None else a
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=6, dither=Image.Dither.NONE)
    return [tuple(c) for c in np.array(q.getpalette()[:n * 3], float).reshape(-1, 3)]


def pixelize(arr, pal=None, n=28, n_acc=6, dk=0.4, mask=None, dither=True):
    """1x float RGB -> palette-locked RGB. pal: base ramps (list of hex/rgb); None = pure k-means of n colours."""
    if pal is None: P = kpal(arr, n, mask)
    else:
        P = [tuple(hexc(c)) if isinstance(c, str) else tuple(c) for c in pal]
        P += pick_accents(arr, P, n=n_acc, mask=mask)
    q = palette_lock(arr, P, dither_flat=dither, dk=dk)
    return majority(q, alpha=mask), P


def key_flat(render_png, w, h, cover_png, bg, thr=26.0, env=2, min_nb=2, union=0.55):
    """Alpha for a layer rendered on a flat bg colour: differs from bg, within the guide coverage dilated by env px;
    the guide's own solid core (>= union) is always kept."""
    ga = Image.open(cover_png).convert('L').resize((w, h), Image.BOX)
    envm = np.asarray(ga.filter(ImageFilter.MaxFilter(1 + 2 * env)), float) / 255 > 0.15
    a = down(Image.open(render_png), w, h)
    al = (np.sqrt(((a - np.asarray(bg, float)) ** 2).sum(-1)) > thr) & envm
    al |= np.asarray(ga, float) / 255 >= union
    for _ in range(2):
        p = np.pad(al, 1)
        nb = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx].astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
        al = al & (nb >= min_nb)
    return al


def cover_alpha(cover_png, w, h, thr=0.5):
    return np.asarray(Image.open(cover_png).convert('L').resize((w, h), Image.BOX), float) / 255 >= thr


def rim(arr, alpha, col, side='top', col2=None):
    out = arr.copy(); ap = np.pad(alpha, 1)
    up = ~ap[0:-2, 1:-1]; left = ~ap[1:-1, 0:-2]; right = ~ap[1:-1, 2:]
    e = alpha & (up | (left if side == 'left' else False) | (right if side == 'right' else False))
    out[e] = col
    if col2 is not None:
        e2 = alpha & ~e & np.roll(e, 1, axis=0); out[e2] = col2
    return out


def stars(arr, rng, n, region=None, cols=('ffffff',), big=0, big_cols=None, mask=None, weight=None):
    """Stamp n crisp 1 px stars (and `big` 3 px cross stars) into arr (in place). weight: per-pixel density map."""
    h, w = arr.shape[:2]; out = []
    if weight is None: weight = np.ones((h, w))
    if mask is not None: weight = weight * mask
    p = (weight / weight.sum()).ravel()
    idx = rng.choice(h * w, size=n + big, replace=False, p=p)
    for i, k in enumerate(idx):
        y, x = divmod(int(k), w); c = hexc(rng.choice(cols))
        if i < n:
            arr[y, x] = c; out.append((x, y, 1))
        else:
            c = hexc(rng.choice(big_cols or cols)); arr[y, x] = c
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if 0 <= y + dy < h and 0 <= x + dx < w: arr[y + dy, x + dx] = arr[y + dy, x + dx] * 0.4 + c * 0.6
            out.append((x, y, 3))
    return out


def to_rgba(arr, alpha=None):
    return V.to_rgba(arr, alpha)


def build(name, frames, ms=None, tag='loop'):
    """frames: list of RGBA PIL images (same size). Writes art/<name>.aseprite + assets/<name>.png/.json."""
    import asebuild
    w, h = frames[0].size
    ms = ms or [1000] * len(frames)
    asebuild.build(name, w, h, ['Layer'], [{'ms': m, 'cels': {'Layer': f}} for f, m in zip(frames, ms)], [(tag, 0, len(frames) - 1)])
    j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    assert len(j['frames']) == len(frames), name
    assert (j['frames'][0]['sourceSize']['w'], j['frames'][0]['sourceSize']['h']) == (w, h), name


def comp(dst, im, x, y):
    """alpha_composite that allows negative / out-of-range offsets."""
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def preview(layers, tint, out_png, cams, scale=2):
    """Parallax-only composites like vistaLayer(): layers = [(rgba PIL, fac, vfac, dict(x=, wrap=, dy=))], cams = [(cx, cy)]."""
    rows = []
    for cx, cy in cams:
        c = Image.new('RGBA', (384, 216), tint)
        for im, fac, vfac, o in layers:
            fw, fh = im.size
            oy = int(round(np.clip(-cy * vfac, -(fh - 216) - 20, 20))) + (216 - fh) + o.get('dy', 0)
            if o.get('wrap', True) is False:
                comp(c, im, int(round(o.get('x', 0) - cx * fac)), oy)
            else:
                ox = -(((cx * fac) % fw + fw) % fw); x = int(round(ox))
                while x < 384: comp(c, im, x, oy); x += fw
        rows.append(c)
    out = Image.new('RGBA', (384, 224 * len(rows)), '#111')
    for i, r in enumerate(rows): out.alpha_composite(r, (0, i * 224))
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(out_png)


def cli(room, src, guides_fn, render_table, build_fn):
    """Shared CLI: (no args) build from saved renders | --guide | --sweep <name> <s1,s2> [tag] | --pick <name> <seed> [tag] | --no-ase"""
    args = sys.argv[1:]
    if '--guide' in args or not os.path.exists(f'{src}/guide_preview.png'): guides_fn()
    if '--guide' in args: return
    if '--sweep' in args:
        i = args.index('--sweep'); name, seeds = args[i + 1], [int(s) for s in args[i + 2].split(',')]
        tag = args[i + 3] if len(args) > i + 3 and not args[i + 3].startswith('--') else ''
        use_prefix(room)
        p, kw = render_table[name]; kw = dict(kw); gname = kw.pop('guide', name)
        if kw.pop('edge', False): kw['edge_png'] = f'{src}/edge_{gname}.png'
        print(sweep(src, name, f'{src}/guide_{gname}.png', p, seeds, tag, **kw)); return
    if '--pick' in args:
        i = args.index('--pick'); tag = args[i + 3] if len(args) > i + 3 else ''
        pick(src, args[i + 1], int(args[i + 2]), tag); return
    build_fn('--no-ase' not in args)
    print('ok')


def knee(a, t=170, k=0.5, warm=None, wk=0.0):
    """Soft highlight knee on a float RGB array: luminance above t is compressed by k; optionally pulled toward `warm`."""
    lum = a.mean(2, keepdims=True)
    over = np.clip(lum - t, 0, None)
    out = a - over * (1 - k)
    if warm is not None and wk:
        w = np.clip(over / max(1, 255 - t), 0, 1) * wk
        out = out * (1 - w) + np.asarray(hexc(warm) if isinstance(warm, str) else warm, float) * (out.mean(2, keepdims=True) / 200) * w
    return np.clip(out, 0, 255)


def draw1x(arr, alpha, fn):
    """Draw with PIL at 1x onto arr/alpha: fn(draw) paints RGBA on a transparent overlay; the overlay is composited in."""
    h, w = arr.shape[:2]
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0)); fn(ImageDraw.Draw(ov))
    o = np.asarray(ov, float); m = o[..., 3:] / 255
    arr[:] = arr * (1 - m) + o[..., :3] * m
    if alpha is not None: alpha[:] = alpha | (o[..., 3] > 127)


def patch_rows(a, boxes):
    """Erase small render artefacts (hi-res float array): each (cx, cy, r) box (1x coords) is refilled row by row by a linear
    blend between the pixels just left and right of it (skies are mostly horizontal, so this leaves no trace)."""
    for cx, cy, r in boxes:
        x0, x1 = int((cx - r) * S) - 2, int((cx + r) * S) + 2
        for y in range(int((cy - r) * S), int((cy + r) * S)):
            L_, R_ = a[y, x0 - 1].copy(), a[y, x1 + 1].copy()
            t = np.linspace(0, 1, x1 - x0)[:, None]
            a[y, x0:x1] = L_ * (1 - t) + R_ * t
    return a


def fill_under(s, cov, maxw=90):
    """The sky behind a cut-out layer (1x float RGB, cov bool): covered runs narrower than maxw in a row are bridged by a
    linear blend of their two ends (behind trunks, towers); wider runs continue the colour above them (behind horizons)."""
    s = s.copy(); h, w = cov.shape; done = ~cov.copy()
    for y in range(h):
        x = 0
        while x < w:
            if cov[y, x]:
                x0 = x
                while x < w and cov[y, x]: x += 1
                if x - x0 < maxw and x0 > 0 and x < w:
                    t = np.linspace(0, 1, x - x0 + 2)[1:-1, None]
                    s[y, x0:x] = s[y, x0 - 1] * (1 - t) + s[y, x] * t; done[y, x0:x] = True
            else: x += 1
    for x in range(w):
        for y in range(1, h):
            if not done[y, x]: s[y, x] = s[y - 1, x]
    return s


def seg_field(chains, w, h, ss=1):
    """For tapered polyline chains [[(x0, y0, x1, y1, width), ...], ...] (1x px): per pixel `inside` (bool), `u` (signed
    offset across the limb: -1 screen-left .. 1 screen-right for steep limbs, top .. bottom for flat ones), `along` (px along its chain), `hw` (half width
    there), `chain` (index). Used to draw trunks and roots crisp at 1x with bark that follows the limb."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float); px, py = xx + 0.5, yy + 0.5
    best = np.full((h, w), np.inf); U = np.zeros((h, w)); A = np.zeros((h, w)); HW = np.ones((h, w)); CH = np.full((h, w), -1)
    for ci, segs in enumerate(chains):
        acc = 0.0
        for x0, y0, x1, y1, wd in segs:
            dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-6; Ln = L2 ** 0.5
            t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
            qx, qy = x0 + t * dx, y0 + t * dy; d = np.hypot(px - qx, py - qy); hw = wd / 2
            nd = d / hw
            m = nd < best
            if m.any():
                side = np.where(px - qx >= 0, 1.0, -1.0) if abs(dy) >= abs(dx) else np.where(py - qy >= 0, 1.0, -1.0)
                best[m] = nd[m]; U[m] = (side * nd)[m]; A[m] = (acc + t * Ln)[m]; HW[m] = hw; CH[m] = ci
            acc += Ln
    return best <= 1.0, np.clip(U, -1, 1), A, HW, CH
