"""Props batch C (docs/v17/props_c.md): a small supersampled prop painter shared by art/gen_props_c_*.py.

A prop is modelled on a 4x grid as stacked shapes. Each shape writes a material name and a value (0..1, lit to dark) per
sub-pixel, plus an optional emissive flag for glowing parts. Shading comes from the shape's own geometry: `dome()` lights a
height field grown from the mask (pillows, caps, rocks, mounds), `facet()` lights flat planes (crystals, cut stone), and
tapered strokes (`stroke()`) are lit as cylinders across their axis (stems, fronds, posts). `resolve()` brings the grid to 1x
(majority material, mean value), locks every pixel to its material's hand-picked ramp with a light ordered dither, and the
finishing passes add the rim light on the lit edges and a selective 1 px outline (dark on the shadow side, one step lighter on
the lit side), the way the player and the cfa_* props are drawn.

Wood (roots, dead trees) reuses art/treelib.py (the trees pass) so it shades and textures exactly like the new tv_tree.
`ai_texture()` is the optional ComfyUI pass for the big props: the procedural colours go through img2img with a tile
ControlNet of themselves, and only the model's luminance texture comes back (histogram-matched to the procedural values),
so forms, palette and lighting stay ours. Renders are cached in art/bg_src/props_c/ (gitignored *_render.png).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import treelib as T                     # noqa: E402  (shared with the trees pass: Noise, Wood, gblur, down, bayer, ...)
from treelib import S                    # noqa: E402

ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets')
SRC = os.path.join(HERE, 'bg_src', 'props_c'); os.makedirs(SRC, exist_ok=True)
PREV = os.path.join(SRC, 'preview'); os.makedirs(PREV, exist_ok=True)
LIGHT = (-0.55, -0.72, 0.42)            # upper-left key light (x right, y down, z to the viewer)


def C(h):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def ramp(*hs):
    return np.array([C(h) for h in hs], float)


def unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)


# =============================================================================================== the 4x canvas
class Pc:
    def __init__(self, w, h):
        self.w, self.h = w, h; Wd, Hd = w * S, h * S
        self.cov = np.zeros((Hd, Wd), bool); self.mat = np.full((Hd, Wd), -1, int); self.val = np.zeros((Hd, Wd))
        self.names = []
        yy, xx = np.mgrid[0:Hd, 0:Wd]
        self.X = (xx + 0.5) / S; self.Y = (yy + 0.5) / S

    # ---------------------------------------------------------------- masks (1x coordinates, floats ok)
    def poly(self, pts):
        m = Image.new('L', (self.w * S, self.h * S), 0)
        ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in pts], fill=255)
        return np.asarray(m) > 127

    def ell(self, cx, cy, rx, ry, rot=0.0):
        dx, dy = self.X - cx, self.Y - cy
        c, s = math.cos(rot), math.sin(rot)
        u, v = dx * c + dy * s, -dx * s + dy * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1.0

    def rect(self, x0, y0, x1, y1):
        return (self.X >= x0) & (self.X < x1) & (self.Y >= y0) & (self.Y < y1)

    def stroke(self, pts, r0, r1=None, per=16, rprof=None, smooth_pts=True):
        """A tapered stroke along a Catmull-Rom spine. Returns (mask, u across -1..1, t along 0..1, tangent x, tangent y)."""
        r1 = r0 if r1 is None else r1
        c = T.catmull(pts, per) if (smooth_pts and len(pts) > 2) else np.array(pts, float)
        c, s, L = T.resample(c, 0.2)
        tng = np.gradient(c, axis=0); tng /= np.maximum(1e-9, np.hypot(tng[:, 0], tng[:, 1]))[:, None]
        t = s / max(L, 1e-6)
        rr = rprof(t) if rprof else r0 + (r1 - r0) * t
        Hd, Wd = self.cov.shape
        m = np.zeros((Hd, Wd), bool); U = np.zeros((Hd, Wd)); TT = np.zeros((Hd, Wd)); AX = np.zeros((Hd, Wd)); AY = np.ones((Hd, Wd))
        for (cx, cy), (tx, ty), r, tv in zip(c, tng, np.maximum(rr, 0.12), t):
            X0 = int(max(0, math.floor((cx - r) * S))); X1 = int(min(Wd, math.ceil((cx + r) * S) + 1))
            Y0 = int(max(0, math.floor((cy - r) * S))); Y1 = int(min(Hd, math.ceil((cy + r) * S) + 1))
            if X0 >= X1 or Y0 >= Y1: continue
            sl = (slice(Y0, Y1), slice(X0, X1))
            px = self.X[sl] - cx; py = self.Y[sl] - cy
            k = px * px + py * py <= r * r
            if not k.any(): continue
            u = (px * -ty + py * tx) / r
            m[sl] |= k; U[sl] = np.where(k, u, U[sl]); TT[sl] = np.where(k, tv, TT[sl])
            AX[sl] = np.where(k, tx, AX[sl]); AY[sl] = np.where(k, ty, AY[sl])
        return m, np.clip(U, -1, 1), TT, AX, AY

    # ---------------------------------------------------------------- shading
    def dome(self, mask, sigma=2.0, light=LIGHT, amb=0.18, key=0.82, bulge=1.0, spec=0.0, wrap=0.0):
        """Value of a pillow grown from the mask: height = blurred mask, normal from its gradient."""
        if not mask.any(): return np.zeros(mask.shape)
        hgt = T.gblur(mask.astype(float), sigma * S) * bulge * sigma * 2.2
        gy, gx = np.gradient(hgt * S)
        nx, ny, nz = -gx, -gy, np.ones_like(gx)
        n = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / n, ny / n, nz / n
        L = unit(light)
        d = nx * L[0] + ny * L[1] + nz * L[2]
        d = np.clip((d + wrap) / (1 + wrap), 0, 1)
        v = amb + key * d
        if spec:
            H = unit(L + np.array([0, 0, 1.0])); v += spec * np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1) ** 24
        return v

    def normals(self, mask, sigma=2.0, bulge=1.0):
        hgt = T.gblur(mask.astype(float), sigma * S) * bulge * sigma * 2.2
        gy, gx = np.gradient(hgt * S)
        n = np.sqrt(gx * gx + gy * gy + 1)
        return -gx / n, -gy / n, 1 / n

    def noise(self, seed, scale=1.0, cells=(32, 16, 8, 4), sy=None):
        """0..1 smooth noise; `scale` stretches it (bigger = smoother), sy the vertical scale (streaks when sy > scale)."""
        nz = T.Noise(seed, cells=cells)
        return nz(self.X * S / scale, self.Y * S / (sy or scale))

    def cracks(self, seed, cell=4.0, aspect=1.0, width=0.12):
        """0..1 crack strength (worley cell edges) in 1x units: cell size `cell` px, stretched by aspect along y."""
        f1, f2, cid = T.worley(self.X / cell, self.Y / (cell * aspect), seed)
        return 1 - T.smooth(width * 0.3, width, f2 - f1), cid

    def wood(self, Wd, nz, mask=None, bark='bark', moss='moss', rim_k=0.35, **shade_kw):
        """Shade a treelib.Wood like the tv_tree trunks and paint it (moss on the up-facing surfaces)."""
        kw = dict(light=(-0.7, -0.45, 0.55), rim_dir=[(-1.0, -0.25, 1.0), (1.0, -0.1, 0.35)], ridges=0.6, furrow_depth=0.85,
                  plate_len=14, ambient=0.15, key=0.74, pattern='fissure', gaps=0.28, fw=0.15, moss_amt=0.5, moss_side=(-1.0, 0.0), side_k=1.0)
        kw.update(shade_kw)
        val, rim, mo, fur = Wd.shade(nz, **kw)
        m = Wd.cov if mask is None else (Wd.cov & mask)
        v = val + rim * rim_k
        self.put(m & ~(mo > 0.5), bark, v)
        if moss: self.put(m & (mo > 0.5), moss, v * 1.1 + 0.06)
        return val, rim, mo

    def cyl(self, U, AX, AY, light=LIGHT, amb=0.18, key=0.82):
        """Value of a cylinder across its axis (u -1..1 from stroke())."""
        th = np.arcsin(np.clip(U, -0.999, 0.999))
        nx_, ny_ = -AY, AX
        Nx = np.sin(th) * nx_; Ny = np.sin(th) * ny_; Nz = np.cos(th)
        L = unit(light)
        return amb + key * np.clip(Nx * L[0] + Ny * L[1] + Nz * L[2], 0, 1)

    def facet(self, normal, light=LIGHT, amb=0.15, key=0.85):
        L = unit(light); n = unit(normal)
        return amb + key * max(0.0, float(n @ L))

    # ---------------------------------------------------------------- paint
    def mid(self, name):
        if name not in self.names: self.names.append(name)
        return self.names.index(name)

    def put(self, mask, mat, val, under=False):
        """Paint mat/val where mask (val scalar or array). under=True only fills sub-pixels nothing covers yet."""
        m = mask & ~self.cov if under else mask
        self.cov |= m; self.mat[m] = self.mid(mat)
        self.val[m] = val[m] if isinstance(val, np.ndarray) else val

    def shift(self, mask, dv, mat=None):
        m = mask & self.cov
        if mat is not None: m &= self.mat == self.mid(mat)
        self.val[m] += dv[m] if isinstance(dv, np.ndarray) else dv

    def remat(self, mask, frm, to):
        m = mask & (self.mat == self.mid(frm)); self.mat[m] = self.mid(to)

    def erase(self, mask):
        self.cov &= ~mask; self.mat[mask] = -1

    # ---------------------------------------------------------------- 4x -> 1x
    def resolve(self, thresh=0.5):
        w, h = self.w, self.h
        covd = T.down(self.cov.astype(float), w, h)
        n = len(self.names)
        cnt = np.stack([T.down((self.mat == i).astype(float), w, h) for i in range(n)], -1) if n else np.zeros((h, w, 1))
        lay = np.where(covd >= thresh, cnt.argmax(-1), -1)
        val = np.zeros((h, w))
        for i in range(n):
            m = (self.mat == i).astype(float); c = np.maximum(T.down(m, w, h), 1e-6)
            val = np.where(lay == i, T.down(self.val * m, w, h) / c, val)
        return Spr(lay, val, list(self.names))


class Spr:
    """A resolved 1x sprite: material layer per pixel (-1 = empty), value, ramp index once coloured."""

    def __init__(self, lay, val, names):
        self.lay, self.val, self.names = lay, val, names
        self.h, self.w = lay.shape
        self.idx = np.zeros(lay.shape, int)
        self.over = {}                      # (y, x) -> rgb set by hand after colouring

    @property
    def alpha(self):
        return self.lay >= 0

    def m(self, name):
        return self.lay == self.names.index(name) if name in self.names else np.zeros(self.lay.shape, bool)

    def index(self, ramps, dk=0.45, dks=None, orphan=True):
        """value -> ramp index per material (ordered dither of width dk bands)."""
        dks = dks or {}
        for i, nm in enumerate(self.names):
            sel = self.lay == i
            if not sel.any(): continue
            R = ramps[nm]
            ix = T.ramp_index(self.val, len(R), dk=dks.get(nm, dk))
            if orphan: ix = T.orphans(np.where(sel, ix, -1), sel)
            self.idx = np.where(sel, ix, self.idx)
        return self

    def rim(self, ramps, mats=None, wts=(1.0, 0.7, 0.0, 0.0), steps=2, minv=0.0):
        """Push lit-edge pixels up the ramp: edges whose up/left/right/down neighbour is empty, weighted by wts."""
        a = self.alpha
        up, dn, lf, rt = T.neighbours(a)
        w1 = np.maximum.reduce([~up * wts[0], ~lf * wts[1], ~rt * wts[2], ~dn * wts[3]]) * a
        for i, nm in enumerate(self.names):
            if mats is not None and nm not in mats: continue
            sel = (self.lay == i) & (w1 > 0) & (self.val >= minv)
            n = len(ramps[nm])
            self.idx = np.where(sel, np.minimum(n - 1, self.idx + np.round(w1 * steps).astype(int)), self.idx)
        return self

    def rgba(self, ramps):
        out = np.zeros((self.h, self.w, 4))
        for i, nm in enumerate(self.names):
            sel = self.lay == i
            if sel.any():
                R = ramps[nm]; out[sel, :3] = R[np.clip(self.idx[sel], 0, len(R) - 1)]; out[sel, 3] = 255
        for (y, x), c in self.over.items():
            if 0 <= y < self.h and 0 <= x < self.w: out[y, x, :3] = c[:3]; out[y, x, 3] = c[3] if len(c) > 3 else 255
        return out


def selout(rgba, dark=(8, 9, 10), lit=None, lit_k=0.45, ext=True, min_hole=10 ** 6, skip=None, near=None):
    """Selective 1 px outline on the open silhouette: `dark` where the outline is on the shadow side (below / right of the
    shape), and on the lit side (above / left) a mix of `dark` and the neighbouring fill (or `lit`)."""
    a = rgba[..., 3] > 0
    exterior = T.exterior(a, min_hole=min_hole) if ext else ~a
    up, dn, lf, rt = T.neighbours(a)          # neighbour above me is opaque, etc.
    o = exterior & (up | dn | lf | rt)
    if near is not None:                       # only around these pixels (e.g. caps but not the thin stems between them)
        nu, nd, nl, nr = T.neighbours(near); o &= (nu | nd | nl | nr)
    if skip is not None: o &= ~skip
    out = rgba.copy(); out[o, :3] = dark; out[o, 3] = 255
    litside = o & (dn | rt) & ~up & ~lf        # the shape lies below/right of this pixel: the outline faces the light
    if lit_k:
        src = np.zeros(rgba.shape[:2] + (3,))
        p = np.pad(rgba[..., :3], ((1, 1), (1, 1), (0, 0)))
        src = np.where(dn[..., None], p[2:, 1:-1], p[1:-1, 2:])
        col = np.asarray(lit, float) if lit is not None else src * 0.55
        out[litside, :3] = np.asarray(dark, float) * (1 - lit_k) + (col[litside] if col.ndim == 3 else col) * lit_k
    return out


def to_img(rgba):
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')


# =============================================================================================== sheets
def read_contract(name, src_dir=None):
    """Frame w/h, per-frame durations and tags of the v1 sheet (backed up in art/bg_src/props_c/v1)."""
    d = src_dir or os.path.join(SRC, 'v1')
    j = json.load(open(os.path.join(d, f'{name}.json')))
    fr = j['frames']; fr = list(fr.values()) if isinstance(fr, dict) else fr
    w, h = fr[0]['frame']['w'], fr[0]['frame']['h']
    durs = [f['duration'] for f in fr]
    tags = [(t['name'], t['from'], t['to']) for t in j['meta'].get('frameTags', [])]
    return w, h, durs, tags


def v1_frames(name):
    """The v1 sheet's frames (RGBA PIL images), in order."""
    w, h, durs, tags = read_contract(name)
    im = Image.open(os.path.join(SRC, 'v1', f'{name}.png')).convert('RGBA')
    return [im.crop((i * w, 0, (i + 1) * w, h)) for i in range(len(durs))]


def build_sheet(name, replace):
    """Rebuild `name` with exactly the v1 contract (frame size, durations, tags, order). `replace` maps tag -> list of
    frames (PIL RGBA, one per frame of the tag) or a single-frame tag -> image; every other tag keeps its v1 pixels."""
    import asebuild
    w, h, durs, tags = read_contract(name)
    frames = v1_frames(name)
    tagd = {t: (a, b) for t, a, b in tags}
    for tag, imgs in replace.items():
        a, b = tagd[tag]
        imgs = imgs if isinstance(imgs, list) else [imgs]
        assert len(imgs) == b - a + 1, (name, tag, len(imgs), b - a + 1)
        for k, im in enumerate(imgs):
            assert im.size == (w, h), (name, tag, im.size)
            frames[a + k] = im
    asebuild.build(name, w, h, ['Layer'], [{'ms': durs[i], 'cels': {'Layer': frames[i]}} for i in range(len(frames))], tags)
    w2, h2, d2, t2 = read_contract(name, ASSETS)
    assert (w2, h2, d2, t2) == (w, h, durs, tags), f'{name}: contract changed'
    return frames


# =============================================================================================== previews
_PLAYER = None


def player_ref():
    global _PLAYER
    if _PLAYER is None:
        im = Image.open(os.path.join(ASSETS, 'player.png')).convert('RGBA'); _PLAYER = im.crop((0, 0, 64, 40))
    return _PLAYER


def preview(name, imgs, bg=(28, 34, 30), scale=3, floor=None, player=True):
    """imgs side by side on a flat backdrop with the player at the same scale, 'scale'x nearest."""
    pw = 64 if player else 0
    W = pw + sum(i.width + 6 for i in imgs) + 6; H = max([i.height for i in imgs] + [40]) + 4
    c = Image.new('RGBA', (W, H), (*bg, 255)); x = 4
    if player: c.alpha_composite(player_ref(), (0, H - 2 - 40)); x = pw + 4
    for im in imgs:
        c.alpha_composite(im, (x, H - 2 - im.height)); x += im.width + 6
    if floor:
        ImageDraw.Draw(c).line([(0, H - 2), (W, H - 2)], fill=floor)
    c = c.resize((W * scale, H * scale), Image.NEAREST); c.save(os.path.join(PREV, f'{name}.png'))
    return c


# =============================================================================================== optional ComfyUI texture pass
AI_NEG = ('text, watermark, signature, person, character, people, cartoon, chibi, blurry, jpeg artifacts, frame, border, '
          'flat colors, vector, smooth gradient, bright saturated colors')


def ai_texture(name, rgba, prompt, seed, bg=(40, 44, 48), denoise=0.5, cn=0.65, cn_end=0.8, pix=0.5, render=False, up=8):
    """procedural colours over a flat key -> img2img with a tile ControlNet of itself -> 1x luminance (BOX). Cached as
    art/bg_src/props_c/<name>_render.png with its guide; without a matching render (and render=False) returns None."""
    from PIL import ImageFilter
    h, w = rgba.shape[:2]
    out = os.path.join(SRC, f'{name}_render.png'); gp = os.path.join(SRC, f'{name}_guide.png')
    im = Image.new('RGBA', (w, h), (*bg, 255)); im.alpha_composite(to_img(rgba))
    g = im.convert('RGB').resize((w * up, h * up), Image.NEAREST).filter(ImageFilter.GaussianBlur(up * 0.35))
    same = os.path.exists(gp) and np.array_equal(np.asarray(Image.open(gp).convert('RGB')), np.asarray(g))
    if not render:
        if not (same and os.path.exists(out)): return None
    else:
        import bgv2lib as V
        c = V._comfy(); g.save(gp); u = c.upload(gp)
        wf = c.workflow(prompt, seed, init_image=u, denoise=denoise, negative=AI_NEG, pose=u, pose_type='tile', pose_strength=cn,
                        loras=V.lora_set(pix))
        wf['43']['inputs']['end_percent'] = cn_end
        wf['9']['inputs']['filename_prefix'] = f'props_c/{name}'
        c.run(wf, out)
    return np.asarray(Image.open(out).convert('RGB').resize((w, h), Image.BOX), float)


def hist_match(src, ref):
    if len(src) == 0: return src
    o = np.argsort(src); r = np.sort(ref); out = np.empty_like(src, float)
    out[o] = np.interp(np.linspace(0, 1, len(src)), np.linspace(0, 1, len(r)), r)
    return out


def apply_ai(spr, ai_rgb, k=0.6, mats=None):
    """Blend the model's luminance (histogram-matched per material to our values) into spr.val."""
    lum = ai_rgb @ np.array([0.299, 0.587, 0.114])
    for i, nm in enumerate(spr.names):
        if mats is not None and nm not in mats: continue
        m = spr.lay == i
        if m.sum() < 4: continue
        spr.val[m] = (1 - k) * spr.val[m] + k * hist_match(lum[m], spr.val[m])
    return spr
