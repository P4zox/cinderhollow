"""crop sig_shots.js frames around the player (screen coords in the result JSON) and tile them: crop.py <dir> <json> [out.png]"""
import json, os, sys
from PIL import Image, ImageDraw
d, js = sys.argv[1], sys.argv[2]; out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(d.rstrip('/')), 'sig_montage.png')
raw = open(js).read(); pos = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
tiles = []
for name, (x, y) in pos.items():
    f = os.path.join(d, name + '.png')
    if not os.path.exists(f): continue
    im = Image.open(f).convert('RGB').crop((x - 150, y - 200, x + 330, y + 30))
    ImageDraw.Draw(im).text((6, 4), name, fill=(255, 230, 160)); tiles.append(im)
cols = 4; w, h = tiles[0].size; rows = (len(tiles) + cols - 1) // cols
M = Image.new('RGB', (cols * w, rows * h), (0, 0, 0))
for i, t in enumerate(tiles): M.paste(t, ((i % cols) * w, (i // cols) * h))
M.save(out); print(out, M.size)
