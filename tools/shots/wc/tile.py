# tight 3x crops around the player, one row per prefix: python3 tile.py <outdir> <crops.json> <out.png> [w h]
import sys, json, os, re
from PIL import Image, ImageDraw
d, cj, outp = sys.argv[1:4]; W = int(sys.argv[4]) if len(sys.argv) > 4 else 240; H = int(sys.argv[5]) if len(sys.argv) > 5 else 200
c = json.load(open(cj)); rows = {}
for n in sorted(c): rows.setdefault(n.rsplit('_', 1)[0], []).append(n)
cols = max(len(v) for v in rows.values())
S = Image.new('RGB', (W * cols + 70, H * len(rows)), (16, 12, 20)); dr = ImageDraw.Draw(S)
for r, (k, ns) in enumerate(rows.items()):
    dr.text((4, r * H + 4), k, fill=(230, 220, 180))
    for i, n in enumerate(ns):
        x, y = c[n]; im = Image.open(os.path.join(d, n + '.png')).convert('RGB')
        S.paste(im.crop((x - W // 3, y - H * 3 // 4, x - W // 3 + W, y + H // 4)), (70 + i * W, r * H))
S.save(outp); print(S.size)
