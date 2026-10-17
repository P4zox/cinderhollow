"""Prop rework batch B (Crimson + Barrows), docs/v17/props_b.md: a small 2.5D relief painter + the bgv2 AI pass + a
pixel finisher, shared by art/gen_props_b_*.py.

Every prop is modelled at S x its frame size as a stack of parts. A part is a coverage mask with a material ramp
(dark -> light colours), a base value inside that ramp, a height profile (round bevel, cylinder, flat panel ...)
and optional texture (wood grain, stone, velvet sheen, brass speckle). `Rel.light()` turns the height field into
normals and lights it (key light from the upper left or from the room's real source, ambient, cavity occlusion, a
cast-shadow march, a coloured rim from behind). `ai_detail()` runs the lit preview through ComfyUI img2img with a
lineart ControlNet (bgv2lib.render, cached as art/bg_src/props_b/<name>_render.png) and folds the render's
light/dark detail back into the value map, so the AI adds painterly material and never moves the silhouette.
`Rel.pixels()` box-downscales to the frame, takes each pixel's material by majority, quantises the value to that
material's ramp (ordered dither only on smooth ramps), removes orphans, adds the edge rim and the 1 px outline
(the region's darkest colour on the shadow side, one step lighter on the lit side).

Contract: `build_sheet()` rebuilds a sheet with exactly the frame size, tag names, frame ranges and per-frame
durations of the v1 export kept in art/bg_src/props_b/v1/, and asserts the new json matches it.
"""
import json, math, os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ART = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(ART)
SRC = os.path.join(ART, 'bg_src', 'props_b'); V1 = os.path.join(ART, 'props_b_v1')   # the v1 sheets (contract + kept tags)
sys.path.insert(0, ART)
os.makedirs(SRC, exist_ok=True)
NOAI = '--noai' in sys.argv
RENDER = '--render' in sys.argv          # regenerate the ComfyUI renders (else use the cached ones)


def C(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def ramp(*hs):
    return np.array([C(h) for h in hs])


OUTLINE = C('08070c')


# ------------------------------------------------------------------------------------------------ small numeric kit
def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def _box(a, r, axis):
    if r < 1: return a
    n = a.shape[axis]; pad = [(0, 0)] * a.ndim; pad[axis] = (r + 1, r); p = np.pad(a, pad, mode='edge')
    c = np.cumsum(p, axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis); lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def blur(a, s):
    """~gaussian blur (3 box passes) with sigma s pixels."""
    if s <= 0.3: return a
    r = max(1, int(round(math.sqrt(12 * s * s / 3 + 1) / 2 - 0.5)))
    for _ in range(3): a = _box(_box(a, r, 0), r, 1)
    return a


def vnoise(w, h, cell, seed, octaves=3, sx=1.0, sy=1.0):
    """value noise in [0,1] on a w x h grid, cell size in pixels (anisotropic via sx/sy multipliers)."""
    rng = np.random.default_rng(seed); out = np.zeros((h, w)); tot = 0; amp = 1.0
    for o in range(octaves):
        cx = max(1.0, cell * sx / 2 ** o); cy = max(1.0, cell * sy / 2 ** o)
        nx = int(w / cx) + 3; ny = int(h / cy) + 3; g = rng.random((ny, nx))
        xs = np.arange(w) / cx; ys = np.arange(h) / cy; x0 = xs.astype(int); y0 = ys.astype(int)
        tx = xs - x0; ty = ys - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        top = a + (b - a) * tx; bot = c + (d - c) * tx
        out += amp * (top + (bot - top) * ty[:, None]); tot += amp; amp *= 0.5
    return out / tot


B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float)


# ------------------------------------------------------------------------------------------------ the relief painter
class Rel:
    """w, h = frame size; S = supersampling. All drawing coordinates are frame pixels (floats)."""

    def __init__(self, w, h, S=4, mats=None, ox=0.0, oy=0.0):
        self.w, self.h, self.S = w, h, S; self.ox, self.oy = ox, oy
        self.W, self.H = w * S, h * S
        self.val = np.zeros((self.H, self.W)); self.hgt = np.zeros((self.H, self.W)); self.a = np.zeros((self.H, self.W))
        self.mat = np.full((self.H, self.W), -1, int); self.spec = np.zeros((self.H, self.W)); self.gloss = np.full((self.H, self.W), 12.0)
        self.emis = np.zeros((self.H, self.W)); self.lit_k = np.ones((self.H, self.W))      # lit_k 0 = unlit (flames, glass glow)
        self.mats = []; self.mat_ix = {}
        yy, xx = np.mgrid[0:self.H, 0:self.W]; self.X = (xx + 0.5) / S - ox; self.Y = (yy + 0.5) / S - oy
        for m in (mats or []): self.add_mat(*m)

    def add_mat(self, name, rmp, dither=True):
        if name in self.mat_ix: return self.mat_ix[name]
        self.mat_ix[name] = len(self.mats); self.mats.append((name, np.asarray(rmp, float), dither)); return self.mat_ix[name]

    # masks ----------------------------------------------------------------------------------------------------
    def _canvas(self):
        return Image.new('L', (self.W * 2, self.H * 2), 0)

    def _fin(self, im):
        return np.asarray(im.resize((self.W, self.H), Image.BOX), float) / 255

    def poly(self, pts):
        im = self._canvas(); ImageDraw.Draw(im).polygon([((x + self.ox) * self.S * 2, (y + self.oy) * self.S * 2) for x, y in pts], fill=255); return self._fin(im)

    def rect(self, x0, y0, x1, y1):
        """x1/y1 exclusive in frame px."""
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def ell(self, cx, cy, rx, ry):
        im = self._canvas(); k = self.S * 2
        cx += self.ox; cy += self.oy
        ImageDraw.Draw(im).ellipse([(cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k], fill=255); return self._fin(im)

    def line(self, pts, w):
        im = self._canvas(); d = ImageDraw.Draw(im); k = self.S * 2; ww = max(1, int(round(w * k)))
        P = [((x + self.ox) * k, (y + self.oy) * k) for x, y in pts]; d.line(P, fill=255, width=ww, joint='curve')
        for x, y in P: d.ellipse([x - ww / 2, y - ww / 2, x + ww / 2, y + ww / 2], fill=255)
        return self._fin(im)

    def tube(self, pts, w0, w1=None):
        """tapered round stroke along pts (width w0 -> w1)."""
        w1 = w0 if w1 is None else w1; im = self._canvas(); d = ImageDraw.Draw(im); k = self.S * 2
        P = np.array(pts, float) + np.array([self.ox, self.oy]); L = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; L = L / max(L[-1], 1e-6)
        n = int(max(8, L.size * 6))
        for t in np.linspace(0, 1, n * 4):
            x = np.interp(t, L, P[:, 0]); y = np.interp(t, L, P[:, 1]); r = (w0 + (w1 - w0) * t) / 2 * k
            d.ellipse([x * k - r, y * k - r, x * k + r, y * k + r], fill=255)
        return self._fin(im)

    # height profiles ------------------------------------------------------------------------------------------
    def prof(self, m, kind='round', r=1.5, amp=1.0, box=None):
        S = self.S
        if kind == 'flat': return np.zeros_like(m)
        if kind == 'round':      # circular bevel of radius r frame px
            b = blur((m > 0.5).astype(float), r * S * 0.55)
            t = np.clip((b - 0.5) / 0.5, 0, 1); return amp * np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1)) * r
        if kind == 'dome':       # whole-shape dome (pillows, heads, bells)
            b = blur((m > 0.5).astype(float), r * S)
            t = np.clip((b - 0.5) / 0.5, 0, 1); return amp * np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1)) * r
        ys, xs = np.nonzero(m > 0.5)
        if box is None:
            if not len(xs): return np.zeros_like(m)
            box = (xs.min() / S - self.ox, ys.min() / S - self.oy, (xs.max() + 1) / S - self.ox, (ys.max() + 1) / S - self.oy)
        x0, y0, x1, y1 = box
        if kind == 'cylx':
            u = np.clip((self.X - (x0 + x1) / 2) / ((x1 - x0) / 2), -1, 1); return amp * np.sqrt(1 - u * u) * (x1 - x0) / 2
        if kind == 'cyly':
            u = np.clip((self.Y - (y0 + y1) / 2) / ((y1 - y0) / 2), -1, 1); return amp * np.sqrt(1 - u * u) * (y1 - y0) / 2
        if kind == 'sphere':
            u = (self.X - (x0 + x1) / 2) / ((x1 - x0) / 2); v = (self.Y - (y0 + y1) / 2) / ((y1 - y0) / 2)
            return amp * np.sqrt(np.clip(1 - u * u - v * v, 0, 1)) * (x1 - x0) / 2
        raise ValueError(kind)

    # put a part -----------------------------------------------------------------------------------------------
    def put(self, m, mat, v=0.5, z=0.0, prof='round', r=1.2, amp=1.0, h=None, tex=None, spec=0.0, gloss=14, box=None,
            emis=0.0, lit=1.0, add_h=False, cover=0.5):
        """Paint part mask m. v: base value in the ramp (0..1); tex: (H,W) value offset; h: explicit height array."""
        mi = self.mat_ix[mat] if isinstance(mat, str) else mat
        hh = h if h is not None else self.prof(m, prof, r, amp, box)
        sel = m > cover
        vv = v + (tex if tex is not None else 0)
        self.val = np.where(sel, vv, self.val)
        self.hgt = np.where(sel, (self.hgt if add_h else 0) + z + hh, self.hgt)
        self.mat = np.where(sel, mi, self.mat)
        self.spec = np.where(sel, spec, self.spec); self.gloss = np.where(sel, gloss, self.gloss)
        self.emis = np.where(sel, emis, self.emis); self.lit_k = np.where(sel, lit, self.lit_k)
        self.a = np.maximum(self.a, m)
        return sel

    def shade(self, sel, dv):
        """adjust value inside a selection (dv scalar or array)."""
        self.val = np.where(sel, self.val + dv, self.val)

    def carve(self, m, depth=1.0, dv=-0.15):
        """cut a groove / recess into whatever is there (keeps material)."""
        sel = (m > 0.5) & (self.a > 0.5)
        self.hgt = np.where(sel, self.hgt - depth * blur(m, self.S * 0.3), self.hgt); self.val = np.where(sel, self.val + dv, self.val)

    def clear(self, m):
        sel = m > 0.5; self.a = np.where(sel, 0, self.a); self.mat = np.where(sel, -1, self.mat)

    # textures ---------------------------------------------------------------------------------------------------
    def grain(self, seed, k=0.12, along='x', cell=6.0, streak=8.0):
        """wood grain: long streaks along x or y + knots."""
        sx, sy = (streak, 0.35) if along == 'x' else (0.35, streak)
        n = vnoise(self.W, self.H, cell * self.S, seed, 3, sx, sy)
        n2 = vnoise(self.W, self.H, cell * self.S * 0.5, seed + 1, 2, sx, sy)
        g = np.sin((n * 7 + n2 * 2) * math.pi * 2) * 0.5 + 0.5
        return (g - 0.5) * k * 2 + (n - 0.5) * k

    def stone(self, seed, k=0.12, cell=5.0):
        n = vnoise(self.W, self.H, cell * self.S, seed, 4); n2 = vnoise(self.W, self.H, cell * self.S * 0.4, seed + 7, 2)
        pits = (n2 > 0.78) * -0.6
        return (n - 0.5) * k * 2 + pits * k

    def speck(self, seed, k=0.1, cell=1.2):
        return (vnoise(self.W, self.H, cell * self.S, seed, 1) - 0.5) * k * 2

    # lighting ---------------------------------------------------------------------------------------------------
    def light(self, L=(-0.55, -0.7, 0.55), amb=0.38, key=0.85, ao=0.6, shadow=0.45, shadow_len=10, rim=None, fill=None,
              point=None, top_fade=None):
        """-> self.lv: lit value 0..1 per pixel. rim = (dir2d, k): back light along edges facing dir.
        point = (x, y, z, radius, k): a local light (a candle/hearth) adds on top. top_fade = (y0, y1, k) darkens toward
        the floor (contact)."""
        S = self.S; h = self.hgt
        gy, gx = np.gradient(blur(h, 0.6 * S) * S)
        n = np.dstack([-gx, -gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
        Lv = np.array(L, float); Lv /= np.linalg.norm(Lv)
        dif = np.clip((n * Lv).sum(2), 0, 1)
        Hv = Lv + np.array([0, 0, 1.0]); Hv /= np.linalg.norm(Hv)
        sp = np.clip((n * Hv).sum(2), 0, 1) ** self.gloss * self.spec
        # cast shadow: march toward the light over the height field
        sh = np.zeros_like(h)
        if shadow:
            d2 = np.array(L[:2], float); d2 /= max(np.linalg.norm(d2), 1e-6); tz = Lv[2] / max(np.hypot(*Lv[:2]), 1e-6)
            for k in range(1, int(shadow_len * S) + 1, max(1, S // 2)):
                # sample toward the light: the height at p + k * (L.x, L.y)
                hs = np.roll(np.roll(h, -int(round(d2[1] * k)), 0), -int(round(d2[0] * k)), 1)
                occ = hs - h - (k / S) * tz
                sh = np.maximum(sh, np.clip(occ / 2.0, 0, 1))
        cav = np.clip((blur(h, 2.0 * S) - h) / 3.0, 0, 1)
        lv = self.val * (amb + key * dif * (1 - shadow * sh)) * (1 - ao * cav) + sp
        if fill is not None:     # (dir3, k) a weak opposite fill
            Fv = np.array(fill[0], float); Fv /= np.linalg.norm(Fv); lv += self.val * fill[1] * np.clip((n * Fv).sum(2), 0, 1)
        if point is not None:
            px, py, pz, pr, pk = point
            dx = px - self.X; dy = py - self.Y; dz = pz - h; dd = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6
            pd = np.clip((n[..., 0] * dx + n[..., 1] * dy + n[..., 2] * dz) / dd, 0, 1) * np.clip(1 - dd / pr, 0, 1) ** 1.5
            lv += self.val * pk * pd
        if rim is not None:
            (rx, ry), rk = rim
            ae = blur((self.a > 0.5).astype(float), 0.8 * S)
            ey, ex = np.gradient(ae); en = np.hypot(ex, ey) + 1e-6
            facing = np.clip(-(ex * rx + ey * ry) / en, 0, 1) * np.clip(en * S * 3, 0, 1)
            lv += rk * facing
        if top_fade is not None:
            y0, y1, k = top_fade; lv *= 1 - k * smoothstep(y0, y1, self.Y)
        lv = lv * self.lit_k + self.val * (1 - self.lit_k) + self.emis
        self.lv = lv
        return lv

    # preview (continuous colour, for the AI pass and for eyeballing) ---------------------------------------------
    def colour(self, lv=None, bg=None):
        lv = self.lv if lv is None else lv
        out = np.zeros((self.H, self.W, 3))
        for i, (name, rmp, _) in enumerate(self.mats):
            sel = self.mat == i
            if not sel.any(): continue
            t = np.clip(lv[sel], 0, 1) * (len(rmp) - 1); i0 = np.floor(t).astype(int); i1 = np.minimum(i0 + 1, len(rmp) - 1); f = (t - i0)[:, None]
            out[sel] = rmp[i0] * (1 - f) + rmp[i1] * f
        al = np.clip(self.a, 0, 1)[..., None]
        if bg is not None: out = out * al + np.asarray(bg, float) * (1 - al)
        return out

    # the pixel finisher ------------------------------------------------------------------------------------------
    def pixels(self, lv=None, outline=True, rim_step=1, dither=0.5, outline_lit=None, edge_dark=True, a_thresh=0.5, keep_inner=False,
               outline_col=OUTLINE):
        lv = self.lv if lv is None else lv
        S, w, h = self.S, self.w, self.h
        A = self.a.reshape(h, S, w, S).mean((1, 3)) >= a_thresh
        V = lv.reshape(h, S, w, S).mean((1, 3))
        M = self.mat.reshape(h, S, w, S).transpose(0, 2, 1, 3).reshape(h, w, S * S)
        # majority material per block (ignoring -1)
        mm = np.full((h, w), -1, int); best = np.zeros((h, w))
        for i in range(len(self.mats)):
            c = (M == i).sum(2); upd = c > best; mm = np.where(upd, i, mm); best = np.maximum(best, c)
        A &= mm >= 0
        idx = np.zeros((h, w), int)
        yy, xx = np.mgrid[0:h, 0:w]; th = (B4[yy & 3, xx & 3] + 0.5) / 16
        for i, (name, rmp, dith) in enumerate(self.mats):
            sel = mm == i; n = len(rmp)
            t = np.clip(V, 0, 1) * (n - 1)
            base = np.floor(t); fr = t - base
            if dith and dither: q = base + ((fr - 0.5) * 1.0 + 0.5 > (th * dither + (1 - dither) * 0.5))
            else: q = np.round(t)
            idx = np.where(sel, np.clip(q, 0, n - 1).astype(int), idx)
        # orphan cleanup on (mat, idx)
        key = np.where(A, mm * 64 + idx, -1)
        for _ in range(2):
            kp = np.pad(key, 1, constant_values=-2)
            nb = np.stack([kp[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx], -1)
            lonely = A & ~(nb == key[..., None]).any(-1)
            same_mat = (nb // 64 == mm[..., None]) & (nb >= 0)
            for y, x in zip(*np.nonzero(lonely)):
                cand = nb[y, x][same_mat[y, x]]
                if len(cand):
                    # nearest value among same-material neighbours
                    vals = cand % 64; j = vals[np.argmin(np.abs(vals - idx[y, x]))]
                    if abs(int(j) - int(idx[y, x])) <= 1: idx[y, x] = j; key[y, x] = mm[y, x] * 64 + j
        # rim: opaque pixels whose upper or left neighbour is empty go one step up
        if rim_step:
            Ap = np.pad(A, 1)
            e = A & (~Ap[0:-2, 1:-1] | ~Ap[1:-1, 0:-2])
            for i, (name, rmp, _) in enumerate(self.mats):
                s = e & (mm == i); idx = np.where(s, np.minimum(idx + rim_step, len(rmp) - 1), idx)
        if edge_dark:   # lower/right silhouette edge one step down
            Ap = np.pad(A, 1)
            e = A & (~Ap[2:, 1:-1] | ~Ap[1:-1, 2:]) & ~(~Ap[0:-2, 1:-1] | ~Ap[1:-1, 0:-2])
            idx = np.where(e, np.maximum(idx - 1, 0), idx)
        out = np.zeros((h, w, 4), np.uint8)
        for i, (name, rmp, _) in enumerate(self.mats):
            s = A & (mm == i); out[s, :3] = rmp[idx[s]].astype(np.uint8); out[s, 3] = 255
        if outline:
            Ap = np.pad(A, 1)
            nb_any = np.zeros((h, w), bool)
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb_any |= Ap[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx]
            ol = ~A & nb_any
            # lit side: the object lies below / right of this outline pixel
            lit_side = ~A & (Ap[2:, 1:-1] | Ap[1:-1, 2:]) & ~(Ap[0:-2, 1:-1] | Ap[1:-1, 0:-2])
            out[ol, :3] = outline_col.astype(np.uint8); out[ol, 3] = 255
            if outline_lit is not None:
                s = ol & lit_side; out[s, :3] = np.asarray(outline_lit, float).astype(np.uint8)
        self.A1, self.M1, self.I1 = A, mm, idx
        return Image.fromarray(out, 'RGBA')


# ------------------------------------------------------------------------------------------------ AI detail pass
NEG = ('text, watermark, signature, cartoon, chibi, anime, toy, plastic, bright saturated colors, neon, blurry, jpeg artifacts, '
       'frame border, person, people, character, extra objects, background scenery')


def ai_detail(name, rel, prompt, seed=7, denoise=0.45, cn=0.6, cn_end=0.75, k_hp=0.9, k_lf=0.25, hp_sigma=1.2, ref=None, ref_w=0.3,
              bg=(118, 112, 116), pix=0.55, ckpt=None, long_side=1024, fit=None):
    """Run (or load the cached) img2img of the lit preview and fold its value detail into rel.lv. Returns new lv."""
    sys.path.insert(0, ART)
    import bgv2lib
    lv = rel.lv
    if NOAI: return lv
    prev = rel.colour(lv, bg=bg)
    H, W = prev.shape[:2]; sc = long_side / max(H, W)
    tw, th = int(round(W * sc / 8)) * 8, int(round(H * sc / 8)) * 8
    gp = os.path.join(SRC, f'{name}_guide.png'); ep = os.path.join(SRC, f'{name}_edge.png'); rp = os.path.join(SRC, f'{name}_render.png')
    gim = Image.fromarray(np.clip(prev, 0, 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
    gim.save(gp)
    if RENDER or not os.path.exists(rp):
        e = gim.convert('L').filter(ImageFilter.GaussianBlur(1.2)).filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 10 else 0).filter(ImageFilter.MaxFilter(3))
        e.save(ep)
        c = bgv2lib._comfy()
        up = c.upload(gp); ue = c.upload(ep); ur = c.upload(ref) if ref else None
        wf = c.workflow(prompt, seed, init_image=up, denoise=denoise, negative=NEG, pose=ue, pose_type='canny/lineart/anime_lineart/mlsd',
                        pose_strength=cn, ref=ur, ref_weight=ref_w, ckpt=ckpt, loras=bgv2lib.lora_set(pix))
        wf['43']['inputs']['end_percent'] = cn_end
        if ur: wf['32']['inputs']['weight_type'] = 'style transfer'
        wf['9']['inputs']['filename_prefix'] = 'props_b/' + name
        c.run(wf, rp); print('  rendered', os.path.basename(rp))
    ai = np.asarray(Image.open(rp).convert('RGB').resize((W, H), Image.LANCZOS), float)
    lum = lambda a: (a * np.array([0.299, 0.587, 0.114])).sum(-1) / 255
    La, Lp = lum(ai), lum(prev)
    s = hp_sigma * rel.S
    hp = (La - blur(La, s)) - (Lp - blur(Lp, s))
    lf = blur(La, s * 3) - blur(Lp, s * 3)
    # value detail is expressed in ramp units: scale by the local ramp's value span (approx 1)
    nlv = lv + k_hp * hp * 1.6 + k_lf * lf * 1.6
    nlv = np.where(rel.lit_k > 0.5, nlv, lv)        # glow / flames stay as modelled
    rel.ai = ai
    return nlv


# ------------------------------------------------------------------------------------------------ sheets
def v1_meta(name):
    j = json.load(open(os.path.join(V1, f'{name}.json')))
    fr = j['frames']; tags = [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']]
    return dict(w=fr[0]['sourceSize']['w'], h=fr[0]['sourceSize']['h'], ms=[f['duration'] for f in fr], tags=tags, n=len(fr))


def v1_frames(name):
    m = v1_meta(name); im = Image.open(os.path.join(V1, f'{name}.png')).convert('RGBA')
    return [im.crop((i * m['w'], 0, (i + 1) * m['w'], m['h'])) for i in range(m['n'])]


def build_sheet(name, frames_by_tag, keep_v1=()):
    """frames_by_tag: {tag: [PIL RGBA]} for reworked tags; tags in keep_v1 (or missing) reuse the v1 frames pixel-exact."""
    import asebuild
    m = v1_meta(name); old = v1_frames(name); frames = []
    for tag, a, b in m['tags']:
        new = frames_by_tag.get(tag)
        if new is None or tag in keep_v1:
            new = old[a:b + 1]
        assert len(new) == b - a + 1, (name, tag, len(new), b - a + 1)
        for k, im in enumerate(new):
            assert im.size == (m['w'], m['h']), (name, tag, im.size)
            frames.append({'ms': m['ms'][a + k], 'cels': {'main': im}})
    asebuild.build(name, m['w'], m['h'], ['main'], frames, m['tags'])
    j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
    assert [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']] == m['tags'], name
    assert [f['duration'] for f in j['frames']] == m['ms'], name
    assert all((f['sourceSize']['w'], f['sourceSize']['h']) == (m['w'], m['h']) for f in j['frames']), name
    print('built', name, len(frames), 'frames, contract ok')


# ------------------------------------------------------------------------------------------------ previews
def contact(rows, out, scale=3, bg='#4a4846', player=True, label=True):
    """rows: [(title, [(label, PIL RGBA), ...])] -> a contact sheet with the player sprite at the same scale."""
    pl = None
    if player:
        try:
            pj = json.load(open(os.path.join(ROOT, 'assets', 'player.json'))); pim = Image.open(os.path.join(ROOT, 'assets', 'player.png')).convert('RGBA')
            f = pj['frames'][0]['frame']; pl = pim.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h']))
        except Exception:
            pl = None
    from PIL import ImageFont
    font = ImageFont.load_default()
    pad = 6; blocks = []
    for title, items in rows:
        ims = ([('player', pl)] if pl is not None else []) + items
        hh = max(i.height for _, i in ims) * scale + 14
        ww = sum(i.width * scale + pad for _, i in ims) + pad
        blk = Image.new('RGBA', (ww, hh + 14), bg); d = ImageDraw.Draw(blk); d.text((4, 1), title, fill='#e8d8b0', font=font)
        x = pad
        for lab, im in ims:
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            blk.alpha_composite(big, (x, 14 + hh - 14 - big.height))
            if label: d.text((x, hh + 1), lab, fill='#c8c0b0', font=font)
            x += big.width + pad
        blocks.append(blk)
    W = max(b.width for b in blocks); H = sum(b.height for b in blocks)
    out_im = Image.new('RGBA', (W, H), '#1c1a1c'); y = 0
    for b in blocks: out_im.alpha_composite(b, (0, y)); y += b.height
    out_im.save(out); return out_im


def save_dbg(rel, name, lv=None):
    Image.fromarray(np.clip(rel.colour(lv, bg=(90, 88, 92)), 0, 255).astype(np.uint8)).save(os.path.join(SRC, f'{name}_lit.png'))


# ------------------------------------------------------------------------------------------------ furniture helpers
def box(R, x0, y0, x1, y1, mat, v=0.5, z=0.0, r=1.0, tex=None, **kw):
    m = R.rect(x0, y0, x1, y1); R.put(m, mat, v, z=z, prof='round', r=r, tex=tex, **kw); return m


def panel(R, x0, y0, x1, y1, mat, v=0.5, z=0.0, inset=2.0, r=0.8, tex=None, raised=True, arch=False):
    """a door/side panel: a bevelled frame with a sunk moulding and a raised field (optionally arched at the top)."""
    m = R.rect(x0, y0, x1, y1); R.put(m, mat, v, z=z, prof='round', r=r, tex=tex)
    ix0, iy0, ix1, iy1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    if arch:
        cx = (ix0 + ix1) / 2; hw = (ix1 - ix0) / 2
        pts = [(ix0, iy1), (ix0, iy0 + hw)] + [(cx - hw * math.cos(a), iy0 + hw - hw * math.sin(a)) for a in np.linspace(0, math.pi, 16)] + [(ix1, iy0 + hw), (ix1, iy1)]
        f = R.poly(pts)
    else:
        f = R.rect(ix0, iy0, ix1, iy1)
    sh = blur((f > 0.5).astype(float), 0.6 * R.S); inner = sh > 0.97
    R.carve(((f > 0.5) & ~inner).astype(float), 0.8, -0.14)
    if raised:
        R.hgt = np.where(inner, R.hgt + 1.4, R.hgt); R.val = np.where(inner, R.val + 0.08, R.val)
    return m


def turned(R, cx, prof, mat, v=0.5, z=0.0, tex=None, **kw):
    """a lathe-turned form (legs, posts, finials, urns): prof = [(y, radius), ...] top -> bottom."""
    ys = np.array([p[0] for p in prof], float); rs = np.array([p[1] for p in prof], float)
    pts = [(cx - r, y) for y, r in prof] + [(cx + r, y) for y, r in reversed(prof)]
    m = R.poly(pts)
    rr = np.interp(R.Y, ys, rs); u = np.clip((R.X - cx) / np.maximum(rr, 0.3), -1, 1)
    h = np.sqrt(1 - u * u) * rr
    R.put(m, mat, v, z=z, h=h, tex=tex, **kw); return m


def flame(R, cx, base, h, w, seed=0, phase=0.0, z=30.0, mat='fire', core=1.0):
    """an emissive flame tongue (unlit), brightest at the root, flickering with phase."""
    X, Y = R.X, R.Y
    t = np.clip((base - Y) / h, 0, 1)
    sway = math.sin(phase * 2.1 + seed) * 0.8 * t ** 1.5
    wid = w * (1 - t) ** 0.8 * (0.6 + 0.4 * np.sin(t * math.pi * 0.9 + 0.3))
    m = ((np.abs(X - cx - sway) < wid) & (Y <= base) & (Y >= base - h)).astype(float)
    val = np.clip(core * (1 - t * 0.85) - np.abs(X - cx - sway) / np.maximum(wid, 0.1) * 0.35, 0, 1)
    R.put(m, mat, 0.0, z=z, prof='flat', lit=0.0, tex=val)
    return m


def rotate_rel(R, angle, center, S=None):
    """a rotated copy of a modelled Rel (angle in degrees, counter-clockwise; center in frame px)."""
    Q = Rel(R.w, R.h, R.S, ox=R.ox, oy=R.oy); Q.mats = R.mats; Q.mat_ix = R.mat_ix
    c = ((center[0] + R.ox) * R.S, (center[1] + R.oy) * R.S)
    def rot(a, nearest=False, fill=0):
        im = Image.fromarray(a.astype(np.float32), 'F')
        return np.asarray(im.rotate(angle, resample=Image.NEAREST if nearest else Image.BILINEAR, center=c, fillcolor=fill), float)
    Q.val = rot(R.val); Q.hgt = rot(R.hgt); Q.a = rot(R.a); Q.mat = rot(R.mat.astype(float), True, -1).astype(int)
    Q.spec = rot(R.spec); Q.gloss = rot(R.gloss, fill=12); Q.emis = rot(R.emis); Q.lit_k = rot(R.lit_k, fill=1)
    return Q


def crop_rel(R, x0, y0, w, h):
    """a w x h (frame px) window of R starting at canvas px (x0, y0) -> a new Rel with logical coords = window coords."""
    Q = Rel(w, h, R.S); Q.mats = R.mats; Q.mat_ix = R.mat_ix; S = R.S
    sl = (slice(y0 * S, (y0 + h) * S), slice(x0 * S, (x0 + w) * S))
    for k in ('val', 'hgt', 'a', 'mat', 'spec', 'gloss', 'emis', 'lit_k'):
        setattr(Q, k, getattr(R, k)[sl].copy())
    return Q
