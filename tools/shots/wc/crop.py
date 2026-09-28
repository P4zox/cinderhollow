# crop the WC screenshots around the player and tile them: python3 crop.py <outdir> <json-with-crops> <montage.png> [cols]
import sys, json, glob, os
from PIL import Image
d, cj, outp = sys.argv[1], sys.argv[2], sys.argv[3]; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
crops = json.load(open(cj)); W, H = 360, 240
names = sorted(crops); tiles = []
for n in names:
    f = os.path.join(d, n + '.png')
    if not os.path.exists(f): continue
    x, y = crops[n]; im = Image.open(f).convert('RGB')
    box = (max(0, min(im.width - W, x - W // 2)), max(0, min(im.height - H, y - H * 2 // 3)))
    tiles.append((n, im.crop((box[0], box[1], box[0] + W, box[1] + H))))
rows = (len(tiles) + cols - 1) // cols
S = Image.new('RGB', (W * cols, (H + 14) * rows), (20, 16, 24))
from PIL import ImageDraw
dr = ImageDraw.Draw(S)
for i, (n, t) in enumerate(tiles):
    X, Y = (i % cols) * W, (i // cols) * (H + 14)
    S.paste(t, (X, Y + 14)); dr.text((X + 4, Y + 1), n, fill=(230, 220, 180))
S.save(outp); print(len(tiles), S.size)
