# stack <dir>/<name>.png images vertically into <out>; optional CROP=x,y,w,h env (screen px of the 1152x648 shot) at full size
import sys, os
from PIL import Image
d, out = sys.argv[1], sys.argv[2]; names = sys.argv[3:]
ims = [Image.open(f"{d}/{n}.png").convert('RGB') for n in names]
c = os.environ.get('CROP')
if c:
    x, y, w, h = map(int, c.split(',')); ims = [im.crop((x, y, x + w, y + h)) for im in ims]
w, h = ims[0].size
S = Image.new('RGB', (w, h * len(ims)))
for i, im in enumerate(ims): S.paste(im, (0, i * h))
if not c: S = S.resize((int(w * 0.85), int(h * len(ims) * 0.85)))
S.save(out)
