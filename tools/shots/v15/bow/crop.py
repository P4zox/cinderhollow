"""Montage of snaps.js output: python3 crop.py <outdir> <pos.json> <out.png>"""
import json, sys
from PIL import Image, ImageDraw
d, pos, outp = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
names = list(pos); cw, ch = 360, 170; S = 1
out = Image.new('RGB', (3 * cw, ((len(names) + 2) // 3) * ch), (20, 20, 20)); dr = ImageDraw.Draw(out)
for i, n in enumerate(names):
    x, y, sc = pos[n][:3]
    im = Image.open(f'{d}/s_{n}.png').crop((x - 120, y - 110, x + 240, y + 60))
    out.paste(im, ((i % 3) * cw, (i // 3) * ch)); dr.text(((i % 3) * cw + 4, (i // 3) * ch + 2), n + ' ' + str(pos[n][3:]), fill=(255, 220, 120))
out.save(outp)
