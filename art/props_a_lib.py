"""Props batch A (docs/v17/props_a.md): shared kit for the Dunes + Necropolis prop rework.

Per target: paint a value/colour guide at high resolution (frame px * S) with real volume (normals lit from the upper left),
optionally run it through ComfyUI img2img + lineart ControlNet for material (bgv2 recipe), then come back down to the
frame: premultiplied BOX downscale, key with the guide's own coverage, palette lock to the region ramp, orphan cleanup,
1 px outline (darkest on the shadow side, a step lighter on the lit side) and a top rim light. Frames are swapped into the
old sheets in place (same frame size, tags, frame counts, durations), via asebuild.

Render side needs ComfyUI on :8188 (shared server; outputs go under the `props_a/` prefix). Renders are cached in
art/bg_src/props_a/<key>_render.png (gitignored), so the sheet build itself needs no server.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ART = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(ART)
sys.path.insert(0, ART)
from bgv2lib import _lab, palette_lock, majority, NEG  # noqa: E402

SRC = os.path.join(ART, 'bg_src', 'props_a'); os.makedirs(SRC, exist_ok=True)
V1 = os.path.join(SRC, 'v1')


def hx(s):
    s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], float)


def hexes(*ss):
    return [tuple(int(v) for v in hx(s)) for s in ss]


# ----------------------------------------------------------------------------------------------- region ramps
# Dunes: sampled from bg_dunes_mid / bg_dunes_far / tiles_dunes (sandstone umber -> sun-bleached ochre).
DU_STONE = ['#0d0806', '#190f0a', '#2a1a10', '#3f2919', '#543a22', '#6c4b2b', '#8a5f2e', '#a17440', '#b58845', '#c99e56', '#e3c68f', '#f4df9f']
DU_SAND = ['#2a1c12', '#47301c', '#704518', '#9c7042', '#b58752', '#d6a048', '#e8bd66', '#f6d994']
DU_GOLD = ['#3d2410', '#704518', '#a56d28', '#d6a048', '#f6d994', '#fff0c4']
DU_LAPIS = ['#121a2c', '#1d2a44', '#2c3f60', '#46608a']          # faded lapis (tiles use #22407a / #3a64a8 at full strength)
DU_CLAY = ['#2b140c', '#4a2414', '#6b3820', '#8a4e2c', '#a8683a', '#c4864c']   # fired clay, burnt umber not toy orange
DU_LEAF = ['#151408', '#252412', '#38361a', '#4d4a22', '#66602c', '#827838', '#9c9048']   # dusty date-palm green
DU_FIRE = ['#7a2a12', '#c4521e', '#f59a3a', '#ffd27a', '#fff2c4']
DU_BONE = ['#4a3a28', '#7a6648', '#a8916a', '#d2bf94', '#efe2bf']

# Necropolis: sampled from bg_necropolis_far/mid + tiles_necropolis (blue-black stone, bone, ghost blue).
NV_STONE = ['#06060a', '#0d0d14', '#14141e', '#1c1d2c', '#2b2b3e', '#36354b', '#44425c', '#56536f', '#6e6a86', '#8a87a0', '#a8a6bc']
NV_BONE = ['#2e2922', '#4a4236', '#6f6550', '#978a6c', '#bcae8c', '#ddd2b2', '#f1ead4']
NV_GHOST = ['#0b1732', '#1e3a6a', '#22498a', '#3a70c0', '#63a0e6', '#a2cdf8', '#e4f2ff']
NV_BRONZE = ['#0e0c0c', '#1a1612', '#2a221a', '#3d3124', '#54432f', '#6c573b', '#8a7149', '#a88c5e']   # tarnished bell bronze
NV_IRON = ['#07080d', '#10121a', '#1a1d28', '#262a38', '#363b4c', '#4c5266', '#6a7088']
NV_WOOD = ['#0f0b0a', '#1c1512', '#2a201a', '#3a2c22', '#4c3a2c', '#614a37']
NV_CLOTH = ['#120c1c', '#1e1430', '#2c1e46', '#3e2a5e']                 # the necropolis' funeral violet (banners)

LIGHT = np.array([-0.55, -0.68, 0.48]); LIGHT = LIGHT / np.linalg.norm(LIGHT)


def ramp(v, cols):
    """v in [0,1] -> colour along the ramp (linear between stops)."""
    C = np.array([hx(c) if isinstance(c, str) else np.asarray(c, float) for c in cols])
    v = np.clip(np.asarray(v, float), 0, 1) * (len(C) - 1)
    i = np.clip(np.floor(v).astype(int), 0, len(C) - 2); t = (v - i)[..., None]
    return C[i] * (1 - t) + C[i + 1] * t


def pal_of(*ramps):
    out = []
    for r in ramps:
        for c in r:
            t = tuple(int(v) for v in (hx(c) if isinstance(c, str) else c))
            if t not in out: out.append(t)
    return out


# ----------------------------------------------------------------------------------------------- hi-res painter
class Cv:
    """A frame (fw x fh px) painted at S x resolution. Coordinates are frame px (floats ok)."""

    def __init__(self, fw, fh, S=None, key=(128, 128, 128)):
        if S is None: S = max(4, int(round(1024 / max(fw, fh))))
        self.fw, self.fh, self.S = fw, fh, S
        self.W, self.H = fw * S, fh * S
        self.rgb = np.zeros((self.H, self.W, 3)); self.rgb[:] = key
        self.cov = np.zeros((self.H, self.W))
        self.mat = np.zeros((self.H, self.W), np.int16)       # material id per pixel (0 = none)
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        self.X = (xx + 0.5) / S; self.Y = (yy + 0.5) / S
        self.key = key

    # masks ------------------------------------------------------------------------------------------------------
    def _img(self):
        return Image.new('L', (self.W, self.H), 0)

    def _arr(self, m, blur=0.0):
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur * self.S))
        return np.asarray(m, float) / 255

    def poly(self, pts, blur=0.0):
        m = self._img(); ImageDraw.Draw(m).polygon([(x * self.S, y * self.S) for x, y in pts], fill=255); return self._arr(m, blur)

    def rect(self, x0, y0, x1, y1, blur=0.0):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], blur)

    def ell(self, cx, cy, rx, ry, blur=0.0):
        m = self._img(); ImageDraw.Draw(m).ellipse([(cx - rx) * self.S, (cy - ry) * self.S, (cx + rx) * self.S, (cy + ry) * self.S], fill=255)
        return self._arr(m, blur)

    def lines(self, segs, blur=0.0):
        """segs: [(x0, y0, x1, y1, width)] with round caps."""
        m = self._img(); d = ImageDraw.Draw(m); S = self.S
        for x0, y0, x1, y1, w in segs:
            ww = max(1, int(round(w * S))); d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=255, width=ww); r = ww / 2
            for px, py in ((x0, y0), (x1, y1)): d.ellipse([px * S - r, py * S - r, px * S + r, py * S + r], fill=255)
        return self._arr(m, blur)

    def path(self, pts, w0, w1=None, blur=0.0):
        """A tapered stroke along a polyline (width w0 -> w1)."""
        w1 = w0 if w1 is None else w1; n = len(pts) - 1
        return self.lines([(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], w0 + (w1 - w0) * (i + 0.5) / n) for i in range(n)], blur)

    def blur(self, m, r):
        return self._arr(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)), r)

    # shading ----------------------------------------------------------------------------------------------------
    def lam(self, nx, ny, nz, amb=0.22, k=0.85, light=None):
        L = LIGHT if light is None else light
        n = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        d = (nx * L[0] + ny * L[1] + nz * L[2]) / n
        return np.clip(amb + k * np.clip(d, 0, 1), 0, 1)

    def pillow(self, m, r, depth=1.0, **kw):
        """Normals of a soft dome over mask m (radius r frame px) -> lit value."""
        h = self.blur(m, r) * depth * r * self.S
        gy, gx = np.gradient(h)
        return self.lam(-gx, -gy, np.ones_like(gx) * 1.0, **kw)

    def relief(self, h, k_h=1.0, **kw):
        """Lit value of a height field h (in frame px) - real sculpted volume."""
        gy, gx = np.gradient(h * k_h * self.S)
        gx = gx / self.S; gy = gy / self.S
        return self.lam(-gx, -gy, np.ones_like(gx), **kw)

    def revolve(self, cx, y0, y1, rfun, amb=0.18, k=0.85, light=None):
        """A body of revolution about a vertical axis at cx, profile r = rfun(y) for y0..y1 (frame px).
        Returns (mask, lit value)."""
        ys = np.linspace(y0, y1, 400); rs = np.maximum(0, np.array([rfun(y) for y in ys]))
        r = np.interp(self.Y, ys, rs, left=0, right=0)
        dr = np.gradient(rs, ys); drY = np.interp(self.Y, ys, dr)
        inside = (np.abs(self.X - cx) < r) & (self.Y >= y0) & (self.Y <= y1)
        u = np.clip((self.X - cx) / np.maximum(r, 1e-3), -1, 1); cz = np.sqrt(1 - u * u)
        v = self.lam(u, -drY * cz, cz, amb=amb, k=k, light=light)
        m = inside.astype(float)
        m = self.blur(m, 0.08) if self.S >= 8 else m
        return m, v

    def g2(self, cx, cy, rx, ry, rot=0.0):
        """2D gaussian bump (value 1 at centre) for height fields."""
        dx, dy = self.X - cx, self.Y - cy
        if rot: c, s = math.cos(rot), math.sin(rot); dx, dy = c * dx + s * dy, -s * dx + c * dy
        return np.exp(-((dx / rx) ** 2 + (dy / ry) ** 2))

    def cyl(self, cx, r, axis='v', bulge=1.0, **kw):
        """Cylinder along y (axis 'v') centred cx with radius r (both may be arrays over Y)."""
        if axis == 'v':
            u = np.clip((self.X - cx) / np.maximum(1e-3, r), -1, 1)
            return self.lam(u * bulge, np.zeros_like(u), np.sqrt(1 - u * u), **kw)
        u = np.clip((self.Y - cx) / np.maximum(1e-3, r), -1, 1)
        return self.lam(np.zeros_like(u), u * bulge, np.sqrt(1 - u * u), **kw)

    def face(self, nx, ny, nz, **kw):
        return np.full((self.H, self.W), float(self.lam(np.array(nx, float), np.array(ny, float), np.array(nz, float), **kw)))

    # noise ------------------------------------------------------------------------------------------------------
    def noise(self, cell, seed, octaves=3):
        """Smooth value noise in [0,1] with features of ~cell frame px."""
        rng = np.random.default_rng(seed); out = np.zeros((self.H, self.W)); amp = 1.0; tot = 0
        for o in range(octaves):
            c = max(0.5, cell / (2 ** o)); gw = int(self.fw / c) + 3; gh = int(self.fh / c) + 3
            g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8)).resize((int(gw * c * self.S), int(gh * c * self.S)), Image.BICUBIC)
            out += amp * np.asarray(g, float)[:self.H, :self.W] / 255; tot += amp; amp *= 0.5
        return out / tot

    # paint ------------------------------------------------------------------------------------------------------
    def paint(self, m, col, mat=1, a=1.0):
        """col: hex, rgb triple, or an HxWx3 array. Coverage and material follow the mask."""
        m = np.clip(m, 0, 1) * a
        if isinstance(col, str): col = hx(col)
        col = np.asarray(col, float)
        self.rgb = self.rgb * (1 - m[..., None]) + col * m[..., None]
        self.cov = np.maximum(self.cov, m if a >= 0.99 else self.cov)
        if mat is not None: self.mat = np.where(m > 0.5, mat, self.mat)

    def shade(self, m, v, cols, mat=1, a=1.0):
        self.paint(m, ramp(v, cols), mat, a)

    def tint(self, m, col, k):
        """Glaze over existing paint (no coverage change)."""
        m = np.clip(m, 0, 1)[..., None] * k
        self.rgb = self.rgb * (1 - m) + np.asarray(hx(col) if isinstance(col, str) else col, float) * m

    def mulv(self, m, f):
        m = np.clip(m, 0, 1)[..., None]
        self.rgb = self.rgb * (1 - m) + np.clip(self.rgb * np.asarray(f)[..., None] if np.ndim(f) else self.rgb * f, 0, 255) * m

    def erase(self, m):
        m = np.clip(m, 0, 1); self.cov = self.cov * (1 - m); self.rgb = self.rgb * (1 - m[..., None]) + np.asarray(self.key, float) * m[..., None]

    def rotate(self, deg, cx, cy):
        """Rotate everything painted so far about (cx, cy) frame px (counter-clockwise for deg > 0)."""
        c = (cx * self.S, cy * self.S)
        rgb = Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8)).rotate(deg, Image.BICUBIC, center=c, fillcolor=tuple(self.key))
        cov = Image.fromarray((np.clip(self.cov, 0, 1) * 255).astype(np.uint8)).rotate(deg, Image.BILINEAR, center=c)
        mat = Image.fromarray(self.mat.astype(np.uint8)).rotate(deg, Image.NEAREST, center=c)
        self.rgb = np.asarray(rgb, float); self.cov = np.asarray(cov, float) / 255; self.mat = np.asarray(mat).astype(np.int16)

    def image(self, bg=None):
        if bg is None: return Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8))
        a = self.cov[..., None]
        return Image.fromarray(np.clip(self.rgb * a + np.asarray(bg, float) * (1 - a), 0, 255).astype(np.uint8))

    def cov_img(self):
        return Image.fromarray((np.clip(self.cov, 0, 1) * 255).astype(np.uint8))


def edges(img, S, lo=16, blur=0.35):
    g = img.convert('L').filter(ImageFilter.GaussianBlur(max(0.6, blur * S)))
    e = g.filter(ImageFilter.FIND_EDGES)
    return e.point(lambda v: 255 if v > lo else 0).filter(ImageFilter.MaxFilter(3))


# ----------------------------------------------------------------------------------------------- ComfyUI
def _comfy():
    sys.path.insert(0, os.path.expanduser('~/Claude/pixelgen'))
    import comfy
    return comfy


def pad8(img):
    w, h = img.size; W, H = -(-w // 8) * 8, -(-h // 8) * 8
    if (W, H) == (w, h): return img
    o = Image.new(img.mode, (W, H), img.getpixel((0, 0))); o.paste(img, (0, 0)); return o


def render(key, guide, edge, prompt, seed, denoise=0.55, cn=0.55, cn_end=0.7, ref=None, ref_w=0.3, pix=0.6, ckpt=None, neg_extra='', out=None):
    """guide/edge: PIL images. Writes SRC/<key>_render.png (or out). Returns the render as float array (cropped to guide size)."""
    c = _comfy(); w, h = guide.size
    gp = os.path.join(SRC, f'_{key}_guide.png'); ep = os.path.join(SRC, f'_{key}_edge.png')
    pad8(guide.convert('RGB')).save(gp); pad8(edge.convert('L').convert('RGB')).save(ep)
    up, ue = c.upload(gp), c.upload(ep); ur = c.upload(ref) if ref else None
    loras = [('pixel-art-xl.safetensors', pix), ('sdxl_lightning_8step_lora.safetensors', 1.0)]
    wf = c.workflow(prompt, seed, init_image=up, denoise=denoise, negative=NEG + ', ' + PNEG + (', ' + neg_extra if neg_extra else ''), pose=ue,
                    pose_type='canny/lineart/anime_lineart/mlsd', pose_strength=cn, ref=ur, ref_weight=ref_w, ckpt=ckpt, steps=8, cfg=1.0, loras=loras,
                    sampler='euler', scheduler='sgm_uniform')
    wf['43']['inputs']['end_percent'] = cn_end
    wf['9']['inputs']['filename_prefix'] = 'props_a/' + key
    if ur: wf['32']['inputs']['weight_type'] = 'style transfer'
    out = out or os.path.join(SRC, f'{key}_render.png')
    c.run(wf, out)
    for p in (gp, ep): os.remove(p)
    im = Image.open(out).convert('RGB').crop((0, 0, w, h)); im.save(out)
    return np.asarray(im, float)


PNEG = ('cartoon, chibi, toy, plastic, glossy, saturated, neon, vector art, flat colors, cel shading, text, letters, logo, ui, '
        'multiple objects, collage, sprite sheet, grid, border, frame, person, character, face of a person, smooth 3d render')


# ----------------------------------------------------------------------------------------------- back down to the frame
def down(cv, rgb_hi=None, thresh=0.5, cov=None):
    """Premultiplied BOX downscale (background never bleeds into edge pixels) + binary alpha."""
    S = cv.S; a = np.clip(cv.cov if cov is None else cov, 0, 1)
    rgb = cv.rgb if rgb_hi is None else rgb_hi
    def box(x):
        return x.reshape(cv.fh, S, cv.fw, S, *x.shape[2:]).mean((1, 3))
    A = box(a); C = box(rgb * a[..., None]) / np.maximum(1e-6, A)[..., None]
    M = None
    if cv.mat is not None:   # majority material per frame pixel
        mats = np.unique(cv.mat)
        cnt = np.stack([box((cv.mat == m).astype(float)) for m in mats], -1)
        M = mats[np.argmax(cnt, -1)]
    return C, A >= thresh, M


def lock(rgb, alpha, pal, mats=None, mat_pals=None, dither=False):
    """Palette lock; with mats/mat_pals each material snaps only to its own ramp (no stray hues)."""
    out = np.zeros_like(rgb)
    if mats is None or not mat_pals:
        out = palette_lock(rgb, pal, dither_flat=dither)
    else:
        out = palette_lock(rgb, pal, dither_flat=dither)
        for m, p in mat_pals.items():
            sel = alpha & (mats == m)
            if sel.any():
                q = palette_lock(rgb, p, dither_flat=dither); out[sel] = q[sel]
    out[~alpha] = 0
    return out


def neighbours(alpha):
    ap = np.pad(alpha, 1)
    return dict(up=ap[:-2, 1:-1], dn=ap[2:, 1:-1], lf=ap[1:-1, :-2], rt=ap[1:-1, 2:])


def outline(q, alpha, dark, lit=None, inner=False, keep_bottom=True, skip=None):
    """1 px outline. inner=False draws it just outside the silhouette (the default for standing props); inner=True
    recolours the silhouette's own edge pixels. Pixels on the lit side (upper-left) take `lit`, the rest `dark`."""
    q = q.copy(); al = alpha.copy(); lit = dark if lit is None else lit
    if inner:
        n = neighbours(alpha)
        edge = alpha & ~(n['up'] & n['dn'] & n['lf'] & n['rt'])
        if keep_bottom: edge[-1, :] = edge[-1, :] & ~(n['up'][-1, :] & n['lf'][-1, :] & n['rt'][-1, :])
        litside = alpha & (~n['up'] | ~n['lf']) & n['dn'] & n['rt']
        if skip is not None: edge &= ~skip
        q[edge] = dark; q[edge & litside] = lit
        return q, al
    n = neighbours(alpha)
    ring = ~alpha & (n['up'] | n['dn'] | n['lf'] | n['rt'])
    if skip is not None: ring &= ~skip
    litside = ring & (n['dn'] | n['rt']) & ~n['up'] & ~n['lf']
    q[ring] = dark; q[ring & litside] = lit; al = alpha | ring
    return q, al


def rim(q, alpha, pal, k=0.5, col=None, side='top', mask=None, depth=1):
    """Top (or top-left) rim: edge pixels facing the light are pushed toward `col` and re-snapped to the palette."""
    q = q.copy(); a = alpha
    for d in range(depth):
        n = neighbours(a)
        e = a & (~n['up'] | ((~n['lf']) if side == 'topleft' else False))
        if mask is not None: e &= mask
        if col is not None:
            tgt = q[e] * (1 - k) + np.asarray(col, float) * k
            P = np.array(pal, float); d2 = ((_lab(tgt)[:, None] - _lab(P)[None]) ** 2).sum(-1)
            q[e] = P[np.argmin(d2, 1)]
        a = a & ~e
        k *= 0.5
    return q


def to_img(q, alpha):
    a = np.clip(q, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, (alpha * 255).astype(np.uint8)]), 'RGBA')


def from_img(im):
    a = np.asarray(im.convert('RGBA'), float); return a[..., :3], a[..., 3] > 0


# ----------------------------------------------------------------------------------------------- sheets
def old_frames(sheet):
    """The v1 sheet (backup) -> (frames [RGBA], json)."""
    j = json.load(open(os.path.join(V1, sheet + '.json'))); im = Image.open(os.path.join(V1, sheet + '.png')).convert('RGBA')
    fr = []
    for f in j['frames']:
        r = f['frame']; fr.append(im.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])))
    return fr, j


def tag_range(j, name):
    if name == 'all': return 0, len(j['frames']) - 1
    t = [t for t in j['meta']['frameTags'] if t['name'] == name][0]; return t['from'], t['to']


def rebuild(sheet, replace):
    """replace: {tag: [RGBA frames]} (exactly the tag's frame count). Everything else stays pixel-identical to v1."""
    import asebuild
    fr, j = old_frames(sheet)
    fw, fh = fr[0].size
    for tag, ims in replace.items():
        a, b = tag_range(j, tag)
        assert len(ims) == b - a + 1, (sheet, tag, len(ims), b - a + 1)
        for i, im in enumerate(ims):
            assert im.size == (fw, fh), (sheet, tag, im.size); fr[a + i] = im
    frames = [{'ms': f['duration'], 'cels': {'Layer': fr[i]}} for i, f in enumerate(j['frames'])]
    tags = [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']]
    asebuild.build(sheet, fw, fh, ['Layer'], frames, tags)
    # contract check
    k = json.load(open(os.path.join(ROOT, 'assets', sheet + '.json')))
    assert [(t['name'], t['from'], t['to']) for t in k['meta']['frameTags']] == tags, sheet
    assert [f['duration'] for f in k['frames']] == [f['duration'] for f in j['frames']], sheet
    assert all((f['sourceSize']['w'], f['sourceSize']['h']) == (fw, fh) for f in k['frames']), sheet
    return len(fr)


def contact(rows, out, scale=3, player=True, bg=(74, 72, 70), label=True):
    """rows: [(label, [RGBA frames])] -> a contact sheet with the player at the same scale at the left of each row."""
    from PIL import ImageFont
    F = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
    pl = None
    if player:
        pj = json.load(open(os.path.join(ROOT, 'assets', 'player.json'))); pim = Image.open(os.path.join(ROOT, 'assets', 'player.png')).convert('RGBA')
        r = pj['frames'][0]['frame']; pl = pim.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
        pl = pl.crop(pl.getbbox())
    gap = 8; rimgs = []
    for lab, ims in rows:
        fh = max(i.height for i in ims); w = sum(i.width for i in ims) + gap * (len(ims) - 1)
        if pl: w += pl.width + gap * 2
        R = Image.new('RGBA', (w, fh), bg + (255,)); x = 0
        if pl: R.alpha_composite(pl, (0, fh - pl.height)); x = pl.width + gap * 2
        for i in ims: R.alpha_composite(i, (x, fh - i.height)); x += i.width + gap
        rimgs.append((lab, R.resize((R.width * scale, R.height * scale), Image.NEAREST)))
    W = max(r.width for _, r in rimgs) + 16; H = sum(r.height + 22 for _, r in rimgs) + 8
    O = Image.new('RGBA', (W, H), (34, 33, 32, 255)); d = ImageDraw.Draw(O); y = 4
    for lab, r in rimgs:
        if label: d.text((8, y), lab, fill=(255, 226, 160), font=F)
        O.alpha_composite(r, (8, y + 18)); y += r.height + 22
    O.save(out); return O.size


# ----------------------------------------------------------------------------------------------- 1x pixel touch-up
class Px:
    """Pixel-level edits on a locked frame: step a pixel along its own ramp (carving, highlights) or set a ramp colour."""

    def __init__(self, q, alpha, ramps):
        self.q, self.a = q, alpha
        self.ramps = [[tuple(int(v) for v in hx(c)) for c in r] for r in ramps]
        self.idx = {}
        for ri, r in enumerate(self.ramps):
            for ci, c in enumerate(r): self.idx.setdefault(c, (ri, ci))

    def inside(self, x, y):
        return 0 <= x < self.q.shape[1] and 0 <= y < self.q.shape[0]

    def step(self, x, y, d, only_opaque=True):
        x, y = int(x), int(y)
        if not self.inside(x, y) or (only_opaque and not self.a[y, x]): return
        k = tuple(int(v) for v in self.q[y, x])
        if k not in self.idx: return
        ri, ci = self.idx[k]; r = self.ramps[ri]
        self.q[y, x] = r[int(np.clip(ci + d, 0, len(r) - 1))]

    def set(self, x, y, ramp_i, ci, opaque=True):
        x, y = int(x), int(y)
        if not self.inside(x, y): return
        r = self.ramps[ramp_i]; self.q[y, x] = r[int(np.clip(ci, 0, len(r) - 1))]
        if opaque: self.a[y, x] = True

    def get(self, x, y):
        k = tuple(int(v) for v in self.q[int(y), int(x)]); return self.idx.get(k)
