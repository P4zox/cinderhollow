"""BG rollout agent A helpers (docs/v17/bg_rollout_a.md): seed sweeps on top of bgv2lib, with a per-biome ComfyUI
output prefix (the server is shared by three agents), and a few guide-painting helpers (upward branch trees, bark).

    sweep(src, layer, prompt, seeds, ...)   pass-1 renders for several seeds -> <src>/sweep/<layer>_s<seed>.png + a 1x sheet
    finish(src, layer, seed, prompt, ...)   copy the picked sweep render to <layer>_pass1.png and run the seam pass
"""
import math, os, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import bgv2lib as V


def use_prefix(biome):
    """Every SaveImage of this process goes to output/bgv2/<biome>_* on the shared server."""
    c = V._comfy()
    if getattr(c, '_bgroll_prefixed', None) == biome: return
    run0 = getattr(c, '_bgroll_run0', c.run); c._bgroll_run0 = run0
    def run(wf, out):
        for n in wf.values():
            if n.get('class_type') == 'SaveImage': n['inputs']['filename_prefix'] = f'bgv2/{biome}'
        return run0(wf, out)
    c.run = run; c._bgroll_prefixed = biome


def sweep(src, layer, prompt, seeds, denoise, cn, cn_end, pix, guide_blur=1.5, ref=None, ref_w=0.35, tag=''):
    os.makedirs(f'{src}/sweep', exist_ok=True)
    g = Image.open(f'{src}/guide_{layer}.png').filter(ImageFilter.GaussianBlur(guide_blur)); gp = f'{src}/_gblur_{layer}.png'; g.save(gp)
    outs = []
    for s in seeds:
        o = f'{src}/sweep/{layer}{tag}_s{s}.png'
        V.render(gp, f'{src}/edge_{layer}.png', prompt, s, o, denoise=denoise, cn=cn, cn_end=cn_end, loras=V.lora_set(pix), ref_png=ref, ref_w=ref_w)
        outs.append(o)
    os.remove(gp)
    sheet(outs, f'{src}/sweep/{layer}{tag}_sheet.png')
    return outs


def sheet(paths, out, scale=1):
    ims = [Image.open(p).convert('RGB').resize((V.W * scale, V.H * scale), Image.BOX) for p in paths]
    cols = 2; rows = (len(ims) + 1) // 2
    S = Image.new('RGB', (cols * (V.W * scale + 6), rows * (V.H * scale + 6)), (20, 20, 20))
    d = ImageDraw.Draw(S)
    for i, (im, p) in enumerate(zip(ims, paths)):
        x, y = (i % cols) * (V.W * scale + 6), (i // cols) * (V.H * scale + 6)
        S.paste(im, (x, y)); d.text((x + 4, y + 2), os.path.basename(p), fill=(255, 60, 60))
    S.save(out)


def finish(src, layer, seed, prompt, pix, seam_band=128, seam_dn=0.5, tag='', ref=None, ref_w=0.35):
    shutil.copy(f'{src}/sweep/{layer}{tag}_s{seed}.png', f'{src}/{layer}_pass1.png')
    return V.seam_pass(f'{src}/{layer}_pass1.png', prompt, seed + 100, f'{src}/{layer}_render.png', band=seam_band, denoise=seam_dn,
                       loras=V.lora_set(pix), ref_png=ref, ref_w=ref_w)


def tree_segs(rng, x, y, ang, length, width, depth, step=2.5, target=-math.pi / 2, trop=0.035, jitter=0.10,
              spread=(0.35, 0.8), shrink=(0.5, 0.72), p_branch=0.07, min_w=0.5, taper=0.75):
    """An upward branching limb: a wandering tapered polyline bending toward `target`, forking into thinner limbs.
    Returns [(x0, y0, x1, y1, w)] in 1x px. Sharp: tips taper to min_w."""
    segs = []
    n = max(2, int(length / step))
    for i in range(n):
        w = width * (1 - taper * i / n)
        nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
        segs.append((x, y, nx, ny, max(min_w, w)))
        x, y = nx, ny
        ang += rng.normal(0, jitter)
        ang += (target - ang) * trop
        if depth > 0 and rng.random() < p_branch + 0.03 * depth and i > n * 0.12:
            s = 1 if rng.random() < 0.5 else -1
            segs += tree_segs(rng, x, y, ang + s * rng.uniform(*spread), length * rng.uniform(*shrink) * (1 - i / n * 0.5),
                              w * 0.62, depth - 1, step, target, trop, jitter, spread, shrink, p_branch, min_w, taper)
    return segs


def poly_band(pts_top, pts_bot):
    """Closed polygon from a top polyline and a bottom polyline (both left->right)."""
    return list(pts_top) + list(reversed(pts_bot))


def key_color(render_png, guide_alpha_png, bg=(128, 128, 128), thr=22.0, env=2, min_nb=2, union=0.0, close=False):
    """1x binary alpha for a mid layer rendered on a flat ground: pixels that differ from the ground colour, inside the
    guide's coverage dilated by `env` px (so the model's own twig and edge shapes survive, strays far from the guide don't).
    Isolated pixels with fewer than `min_nb` opaque 8-neighbours are dropped."""
    ga = Image.open(guide_alpha_png).convert('L').resize((V.W, V.H), Image.BOX)
    envm = np.asarray(ga.filter(ImageFilter.MaxFilter(1 + 2 * env)), float) / 255 > 0.2
    a = V.box_down(Image.open(render_png))
    al = (np.sqrt(((a - np.asarray(bg, float)) ** 2).sum(-1)) > thr) & envm
    if union: al |= np.asarray(ga, float) / 255 >= union          # keep the guide's own thin twigs connected
    if close:   # 3x3 closing: fills 1px pinholes and notches inside solid parts
        im = Image.fromarray((al * 255).astype(np.uint8))
        cl = np.asarray(im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)), float) > 127
        solid = np.asarray(ga.filter(ImageFilter.MinFilter(5)), float) / 255 > 0.6   # only inside wide shapes, never between twigs
        al = al | (cl & solid)
    for _ in range(2):
        p = np.pad(al, 1, mode='wrap')
        nb = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx].astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
        al = al & (nb >= min_nb)
    return al


def mid_pipeline_ck(render_png, guide_alpha_png, pal, n_acc=3, grade_kw=None, post=None, rim_col=None, rim_col2=None, dither=False,
                    key_kw=None):
    """bgv2lib.mid_pipeline with colour keying (key_color) instead of the guide's own alpha."""
    a = np.asarray(Image.open(render_png).convert('RGB'), float)
    al = key_color(render_png, guide_alpha_png, **(key_kw or {}))
    if grade_kw: a = V.grade(a, **grade_kw)
    s = V.box_down(a)
    if post: s = post(s, 'lo')
    acc = V.pick_accents(s, pal, n=n_acc, mask=al)
    q = V.palette_lock(s, [tuple(c) for c in pal] + acc, dither_flat=dither)
    q = V.majority(q, alpha=al)
    if rim_col is not None:   # rim only where the shape is at least 2 px thick (thin twigs stay one colour, no speckle)
        thick = al & np.roll(al, -1, axis=0)
        r = V.rim(q, al, rim_col, rim_col2)
        q = np.where((thick & al)[..., None], r, q)
    q = np.where(al[..., None], q, 0)
    return q, al, acc


def seam_pass_free(src_png, prompt, seed, out_png, band=128, denoise=0.6, tile=0.2, loras=None):
    """bgv2lib.seam_pass with a weaker tile ControlNet (bgv2lib uses 0.6), for layers where the tile control made the model
    redraw the wrap discontinuity itself (deep far: the molten sea's crust plates kept a hard vertical edge)."""
    c = V._comfy(); work = os.path.dirname(out_png)
    g = Image.open(src_png).convert('RGB'); w = g.width
    r = Image.fromarray(np.roll(np.asarray(g), w // 2, axis=1)); rp = os.path.join(work, '_rolled.png'); r.save(rp)
    bs = band * V.S; cx = w // 2; m = np.zeros((g.height, w), np.uint8)
    for x in range(cx - bs, cx + bs):
        m[:, x] = int(255 * min(1, (bs - abs(x - cx)) / (bs * 0.5)))
    mp = os.path.join(work, '_seam_mask.png'); Image.fromarray(m).save(mp)
    ur, um = c.upload(rp), c.upload(mp)
    wf = c.workflow(prompt, seed, init_image=ur, denoise=denoise, negative=V.NEG, pose=ur, pose_type='tile', pose_strength=tile, loras=loras)
    wf['50'] = {'class_type': 'LoadImage', 'inputs': {'image': um}}
    wf['51'] = {'class_type': 'ImageToMask', 'inputs': {'image': ['50', 0], 'channel': 'red'}}
    wf['52'] = {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': ['21', 0], 'mask': ['51', 0]}}
    wf['7']['inputs']['latent_image'] = ['52', 0]
    tmp = os.path.join(work, '_seam_gen.png'); c.run(wf, tmp)
    g2 = np.asarray(Image.open(tmp).convert('RGB')).astype(float); rr = np.asarray(r).astype(float); a = (m.astype(float) / 255)[..., None]
    Image.fromarray(np.roll((g2 * a + rr * (1 - a)).astype(np.uint8), -(w // 2), axis=1)).save(out_png)
    for p in (rp, mp, tmp): os.remove(p)
