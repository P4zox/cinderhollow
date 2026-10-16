"""Small helpers for the bg rollout scripts of agent B (hoarfrost, mire, necropolis, dunes); see docs/v17/bg_rollout_b.md.

  * set_prefix(biome): every ComfyUI SaveImage of this process writes under `bgroll/<biome>_*` on the shared server
    (the server is shared by three agents; the prefix keeps the outputs apart).
  * sweep(): pass-1 renders over the guide for a list of seeds (no seam pass) plus a 1x contact sheet, for picking by eye.
    Sweep files go to a scratch dir, not to art/bg_src.
  * profile(): a tileable 1-D noise profile at 3x (mountain ridges, dune lines).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import bgv2lib as L


def set_prefix(biome):
    c = L._comfy()
    if getattr(c, '_bgroll_wrapped', None) == biome: return
    base = getattr(c, '_bgroll_base', c.workflow)

    def wf(*a, **k):
        w = base(*a, **k); w['9']['inputs']['filename_prefix'] = f'bgroll/{biome}'; return w
    c._bgroll_base = base; c.workflow = wf; c._bgroll_wrapped = biome


def profile(cell, seed, octaves=4, ridged=False):
    n = L.tile_noise(L.WS, 6, cell * L.S, 2, seed, octaves)[3]
    if ridged: n = 1 - np.abs(2 * n - 1)
    return n


def sweep(src, layer, prompt, seeds, outdir, denoise, cn, cn_end, pix, guide_blur=1.5, label=None, **kw):
    """Render pass 1 for each seed -> <outdir>/<layer>_s<seed>.png and a contact sheet <outdir>/<layer>_sheet.png (1x, 2 per row)."""
    os.makedirs(outdir, exist_ok=True)
    g = Image.open(f'{src}/guide_{layer}.png').filter(ImageFilter.GaussianBlur(guide_blur)); gp = f'{outdir}/_gblur_{layer}.png'; g.save(gp)
    outs = []
    for s in seeds:
        o = f'{outdir}/{layer}{label or ""}_s{s}.png'
        L.render(gp, f'{src}/edge_{layer}.png', prompt, s, o, denoise=denoise, cn=cn, cn_end=cn_end, loras=L.lora_set(pix), **kw)
        outs.append((s, o))
    os.remove(gp)
    tiles = [Image.open(f'{src}/guide_{layer}.png').resize((L.W, L.H), Image.BOX)] + [Image.open(o).convert('RGB').resize((L.W, L.H), Image.BOX) for _, o in outs]
    names = ['guide'] + [f'seed {s}' for s, _ in outs]
    cols = 2; rows = (len(tiles) + 1) // 2
    sh = Image.new('RGB', (cols * (L.W + 6), rows * (L.H + 16)), '#111'); d = ImageDraw.Draw(sh)
    for i, (t, n) in enumerate(zip(tiles, names)):
        x, y = (i % cols) * (L.W + 6), (i // cols) * (L.H + 16)
        sh.paste(t, (x, y + 14)); d.text((x + 2, y + 1), n, fill='#e6c77a')
    sp = f'{outdir}/{layer}{label or ""}_sheet.png'; sh.save(sp); return sp


def smear_wrap(src_png, out_png, f=48):
    """Replace the 2f columns around the wrap seam (x = 0) with a linear blend between the columns just outside them, so the
    seam pass starts from a soft gap instead of a hard step (the tile ControlNet in seam_pass otherwise keeps a strong step)."""
    a = np.asarray(Image.open(src_png).convert('RGB')).astype(float); w = a.shape[1]
    r = np.roll(a, f, axis=1)                                   # the seam now sits at column f
    lo, hi = r[:, 0:1], r[:, 2 * f - 1:2 * f]
    t = np.linspace(0, 1, 2 * f)[None, :, None]
    r[:, 0:2 * f] = lo * (1 - t) + hi * t
    Image.fromarray(np.roll(r, -f, axis=1).astype(np.uint8)).save(out_png)


def render_layer_smear(src, layer, prompt, seed, denoise, cn, cn_end, pix, guide_blur=1.5, seam_band=128, seam_dn=0.6, seam_seed=None, smear=48):
    """bgv2lib.render_layer with smear_wrap() between pass 1 and the seam pass (for layers whose pass 1 has a strong wrap step)."""
    g = Image.open(f'{src}/guide_{layer}.png').filter(ImageFilter.GaussianBlur(guide_blur)); gp = f'{src}/_gblur_{layer}.png'; g.save(gp)
    raw = f'{src}/{layer}_pass1.png'; LS = L.lora_set(pix)
    t = L.render(gp, f'{src}/edge_{layer}.png', prompt, seed, raw, denoise=denoise, cn=cn, cn_end=cn_end, loras=LS)
    sm = f'{src}/_smear_{layer}.png'; smear_wrap(raw, sm, smear)
    t += L.seam_pass(sm, prompt, seam_seed or seed + 100, f'{src}/{layer}_render.png', band=seam_band, denoise=seam_dn, loras=LS)
    os.remove(gp); os.remove(sm)
    return t


def wrap_step(png):
    a = np.asarray(Image.open(png).convert('RGB')).astype(float)
    return round(float(np.abs(a[:, 0] - a[:, -1]).sum(1).mean() / np.abs(a[:, 1:] - a[:, :-1]).sum(2).mean()), 2)
