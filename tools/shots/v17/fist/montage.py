"""Crop each snapshot round the player (POS from snaps.js's output) into one montage. python3 montage.py <snapdir> <out.png> <snaps_out.txt>"""
import json, os, sys
from PIL import Image, ImageDraw
d, out, log = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(log).read(); res = json.loads(s[s.index('{'):s.rindex('}') + 1])
cells = []
for n in res['shots']:
    x, y, sc = res['POS'][n]
    im = Image.open(os.path.join(d, n + '.png')).convert('RGBA')
    w, h = int(150 * sc), int(70 * sc)
    c = im.crop((x - int(40 * sc), y - int(58 * sc), x - int(40 * sc) + w, y - int(58 * sc) + h))
    c = c.resize((450, 210), Image.NEAREST)
    ImageDraw.Draw(c).text((6, 4), n, fill=(255, 255, 255, 255))
    cells.append(c)
cols = 4
M = Image.new('RGBA', (cols * 452, ((len(cells) + cols - 1) // cols) * 212), (20, 18, 24, 255))
for i, c in enumerate(cells):
    M.paste(c, ((i % cols) * 452, (i // cols) * 212))
M.save(out); print(out, M.size)
