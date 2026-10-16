"""Montage of in-game snapshots: python3 tools/shots/v17/foes/montage.py <dir> <out.png> [crop x0,y0,x1,y1] [cols] [scale] [glob]"""
import sys, os, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
crop = tuple(map(int, sys.argv[3].split(','))) if len(sys.argv) > 3 else (150, 110, 1010, 560)
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
sc = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
pat = sys.argv[6] if len(sys.argv) > 6 else '*.png'
fs = sorted(glob.glob(os.path.join(d, pat)))
w, h = int((crop[2] - crop[0]) * sc), int((crop[3] - crop[1]) * sc)
rows = (len(fs) + cols - 1) // cols
M = Image.new('RGB', (cols * (w + 4), rows * (h + 18)), (20, 20, 26))
dr = ImageDraw.Draw(M)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB').crop(crop).resize((w, h), Image.LANCZOS if sc < 1 else Image.NEAREST)
    x, y = (i % cols) * (w + 4), (i // cols) * (h + 18)
    M.paste(im, (x, y + 16)); dr.text((x + 2, y + 2), os.path.basename(f)[:-4], fill=(220, 220, 220))
M.save(out); print(out, M.size, len(fs))
