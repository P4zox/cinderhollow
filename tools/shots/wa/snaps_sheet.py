"""Crop the snaps.js frames around the player (positions from the script's JSON) into one contact sheet."""
import json, sys, os
from PIL import Image
d, posf, out = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(posf).read(); pos = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
names = sorted(pos)
rows = sorted({n.split('_')[0] for n in names}, key=lambda c: names.index(next(n for n in names if n.startswith(c + '_'))))
cols = sorted({n.split('_', 1)[1] for n in names})
cw, ch = 64 * 3 + 60, 52 * 3 + 60
S = Image.new('RGB', (cw * len(cols), ch * len(rows)), (20, 20, 24))
for n, v in pos.items():
    x, y = v[0], v[1]
    c, k = n.split('_', 1)
    im = Image.open(os.path.join(d, n + '.png')).convert('RGB')
    S.paste(im.crop((x - cw // 2, y - ch + 50, x + cw // 2, y + 50)), (cols.index(k) * cw, rows.index(c) * ch))
S.save(out); print(out, S.size)
