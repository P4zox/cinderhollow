"""Crop arts_test.js snaps around the player (positions from the test's JSON output) into labelled contact sheets.
python3 tools/shots/aa/snaps_sheet.py <snapdir> <test_output.txt> <out_prefix> [per_sheet]"""
import json, sys, os
from PIL import Image, ImageDraw
d, posf, out = sys.argv[1], sys.argv[2], sys.argv[3]
per = int(sys.argv[4]) if len(sys.argv) > 4 else 20
raw = open(posf).read(); res = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
pos = res["pos"]
names = list(pos)
cw, ch, cols = 300, 210, 5
for si in range(0, len(names), per):
    chunk = names[si:si + per]
    rows = (len(chunk) + cols - 1) // cols
    S = Image.new('RGB', (cw * cols, ch * rows), (20, 20, 24))
    dr = ImageDraw.Draw(S)
    for k, n in enumerate(chunk):
        x, y, lab = pos[n]
        im = Image.open(os.path.join(d, n + '.png')).convert('RGB')
        S.paste(im.crop((x - cw // 2, y - ch + 40, x + cw // 2, y + 40)), ((k % cols) * cw, (k // cols) * ch))
        dr.text(((k % cols) * cw + 4, (k // cols) * ch + 4), f"{n}  {lab}", fill=(255, 230, 160))
    fn = f"{out}_{si // per}.png"; S.save(fn); print(fn, S.size)
