"""Crop each in-game shot round the player (shots.json positions) into one labelled montage: python3 montage.py <outdir>"""
import json, os, sys
from PIL import Image, ImageDraw
d = sys.argv[1]
s = open(os.path.join(d, 'shots.json')).read()
items = json.loads(s[s.index('['):s.rindex(']') + 1])
cw, ch, cols = 300, 200, 5
rows = (len(items) + cols - 1) // cols
out = Image.new('RGB', (cols * cw, rows * (ch + 16)), (20, 18, 24))
dr = ImageDraw.Draw(out)
for i, it in enumerate(items):
    p = os.path.join(d, 'shots', it['name'] + '.png')
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert('RGB')
    x, y, sc = it['sc'][0], it['sc'][1], it['sc'][2]
    box = (int(x - 50 * sc), int(y - 55 * sc), int(x + 50 * sc), int(y + 12 * sc))
    c = im.crop(box).resize((cw, ch), Image.NEAREST)
    ox, oy = (i % cols) * cw, (i // cols) * (ch + 16)
    out.paste(c, (ox, oy + 16))
    dr.text((ox + 4, oy + 2), f"{it['name']}  ({it['st']} @{it['t']}ms)", fill=(220, 210, 240))
out.save(os.path.join(d, 'montage.png'))
print(out.size)
