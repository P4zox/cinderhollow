"""montage.py OUT.png ROOM ... : stack sheet_<ROOM>.png images (scaled to fit 1400 px wide) with labels"""
import sys, os
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
out, ids = sys.argv[1], sys.argv[2:]
ims = []
for r in ids:
    im = Image.open(os.path.join(D, f'sheet_{r}.png')).convert('RGB')
    k = min(1.0, 1400 / im.size[0], 700 / im.size[1]); im = im.resize((int(im.size[0] * k), int(im.size[1] * k)), Image.LANCZOS)
    ImageDraw.Draw(im).text((4, 4), r, fill=(255, 255, 0)); ims.append(im)
W = max(i.size[0] for i in ims); H = sum(i.size[1] + 4 for i in ims)
M = Image.new('RGB', (W, H), (40, 0, 40)); y = 0
for i in ims: M.paste(i, (0, y)); y += i.size[1] + 4
M.save(out)
