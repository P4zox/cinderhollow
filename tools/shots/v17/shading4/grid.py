"""grid.py out.png [--cols N] [--crop x0,y0,x1,y1] [--z 2] [--w W] [--labels] img ... : a labelled grid (NEAREST zoom for crops)."""
import sys, os
from PIL import Image, ImageDraw
a = sys.argv[1:]; cols = 2; crop = None; z = 1.0; w = None
def opt(n, f):
    global a
    if n in a: i = a.index(n); v = f(a[i + 1]); del a[i:i + 2]; return v
cols = opt('--cols', int) or cols; crop = opt('--crop', lambda s: tuple(map(int, s.split(',')))); z = opt('--z', float) or z; w = opt('--w', int)
out, files = a[0], a[1:]
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    if crop: im = im.crop(crop)
    if w: z = w / im.width
    if z != 1: im = im.resize((round(im.width * z), round(im.height * z)), Image.NEAREST if crop else Image.LANCZOS)
    ims.append((os.path.splitext(os.path.basename(f))[0] + ' (' + os.path.basename(os.path.dirname(os.path.abspath(f))) + ')', im))
cw, ch = max(i.width for _, i in ims), max(i.height for _, i in ims); rows = (len(ims) + cols - 1) // cols
M = Image.new('RGB', (cols * (cw + 6) - 6, rows * (ch + 18)), (24, 22, 28)); d = ImageDraw.Draw(M)
for k, (n, im) in enumerate(ims):
    x, y = (k % cols) * (cw + 6), (k // cols) * (ch + 18)
    M.paste(im, (x, y + 16)); d.text((x + 3, y + 2), n, fill=(255, 226, 120))
M.save(out)
