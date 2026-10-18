"""rows.py out.png dir a1 b1 [a2 b2 ...] [--crop x0,y0,x1,y1] [--w 700]: rows of dir/a | dir/b (same frame, two settings)."""
import sys
from PIL import Image, ImageDraw
args = sys.argv[1:]; w = 700; crop = None
if '--w' in args: i = args.index('--w'); w = int(args[i + 1]); del args[i:i + 2]
if '--crop' in args: i = args.index('--crop'); crop = tuple(map(int, args[i + 1].split(','))); del args[i:i + 2]
out, D, names = args[0], args[1], args[2:]
pairs = list(zip(names[::2], names[1::2]))
cw, ch = (crop[2] - crop[0], crop[3] - crop[1]) if crop else Image.open(f'{D}/{names[0]}.png').size
h = w * ch // cw
M = Image.new('RGB', (w * 2 + 6, (h + 4) * len(pairs)), (40, 40, 40)); d = ImageDraw.Draw(M)
for r, pr in enumerate(pairs):
    for c, n in enumerate(pr):
        im = Image.open(f'{D}/{n}.png').convert('RGB')
        if crop: im = im.crop(crop)
        M.paste(im.resize((w, h), Image.NEAREST if crop else Image.LANCZOS), (c * (w + 6), r * (h + 4)))
        d.rectangle([c * (w + 6), r * (h + 4), c * (w + 6) + 7 * len(n) + 6, r * (h + 4) + 13], fill=(0, 0, 0)); d.text((c * (w + 6) + 3, r * (h + 4) + 1), n, fill=(255, 230, 0))
M.save(out)
