"""Crop the snaps around the knight and lay them out with labels: python3 montage.py <snapdir> <snaps.json-ish log> out.png"""
import json, re, sys
from PIL import Image, ImageDraw
d, log, out = sys.argv[1], sys.argv[2], sys.argv[3]
rows = []
for line in open(log):
    m = re.match(r'\s*"(\S+) (\[.*\])",?', line)
    if m:
        rows.append((m.group(1), json.loads(m.group(2).replace(chr(92) + chr(34), chr(34)))))
W, H, cols = 300, 210, 4
sheet = Image.new("RGB", (cols * W, ((len(rows) + cols - 1) // cols) * (H + 16)), (30, 28, 34))
dr = ImageDraw.Draw(sheet)
for i, (name, (x, y, sc, st, tag, fi)) in enumerate(rows):
    im = Image.open(f"{d}/{name}.png").convert("RGB")
    c = im.crop((x - W // 2 + 20, y - H + 30, x + W // 2 + 20, y + 30))
    X, Y = (i % cols) * W, (i // cols) * (H + 16)
    sheet.paste(c, (X, Y + 16))
    dr.text((X + 4, Y + 2), f"{name}  {st}/{tag}#{fi}", fill=(230, 220, 200))
sheet.save(out)
