#!/usr/bin/env python3
"""pairs.py out.png dirA dirB name [name...] [--w 864] [--crop x0,y0,x1,y1] -> rows of A | B (labelled)."""
import sys
from PIL import Image, ImageDraw
args = sys.argv[1:]; w = 864; crop = None
if '--w' in args: i = args.index('--w'); w = int(args[i + 1]); del args[i:i + 2]
if '--crop' in args: i = args.index('--crop'); crop = tuple(map(int, args[i + 1].split(','))); del args[i:i + 2]
out, A, B, names = args[0], args[1], args[2], args[3:]
src = [Image.open(f'{A}/{names[0]}.png')]
cw, ch = (crop[2] - crop[0], crop[3] - crop[1]) if crop else src[0].size
h = w * ch // cw
M = Image.new('RGB', (w * 2 + 6, (h + 4) * len(names)), (40, 40, 40)); d = ImageDraw.Draw(M)
for r, n in enumerate(names):
    for c, D in enumerate((A, B)):
        im = Image.open(f'{D}/{n}.png').convert('RGB')
        if crop: im = im.crop(crop)
        M.paste(im.resize((w, h), Image.NEAREST if crop else Image.LANCZOS), (c * (w + 6), r * (h + 4)))
        lab = f'{D.split("/")[-1]}/{n}'; d.rectangle([c * (w + 6), r * (h + 4), c * (w + 6) + 7 * len(lab) + 6, r * (h + 4) + 13], fill=(0, 0, 0)); d.text((c * (w + 6) + 3, r * (h + 4) + 1), lab, fill=(255, 230, 0))
M.save(out)
