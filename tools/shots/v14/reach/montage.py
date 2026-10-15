"""Crop each vis.js shot around the player (positions from the test's JSON) into one montage."""
import json, sys, os
from PIL import Image, ImageDraw
d, pos = sys.argv[1], json.load(open(sys.argv[2]))
cells = []
for name, (x, y, st, tag, i) in sorted(pos.items()):
    im = Image.open(os.path.join(d, name + '.png')).convert('RGB').crop((x - 150, y - 170, x + 330, y + 30))
    ImageDraw.Draw(im).text((4, 4), f"{name} {tag}:{i}", fill=(255, 230, 120))
    cells.append(im)
w, h = cells[0].size; cols = 3; rows = (len(cells) + cols - 1) // cols
out = Image.new('RGB', (w * cols, h * rows))
for k, c in enumerate(cells): out.paste(c, ((k % cols) * w, (k // cols) * h))
out.save(os.path.join(d, 'montage.png')); print(out.size)
