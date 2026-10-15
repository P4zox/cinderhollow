"""Split a wide preview sheet into stacked chunks (label column repeated) so long tags can be read: split.py in.png out.png [w]"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]); w = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
lw = 38 * 3
cell = 65 * 3
per = max(1, (w - lw) // cell)
n = (im.width - lw + cell - 1) // cell
chunks = [(i, min(n, i + per)) for i in range(0, n, per)]
out = Image.new("RGBA", (lw + per * cell, im.height * len(chunks)), (92, 92, 100, 255))
for k, (a, b) in enumerate(chunks):
    out.paste(im.crop((0, 0, lw, im.height)), (0, k * im.height))
    out.paste(im.crop((lw + a * cell, 0, lw + b * cell, im.height)), (lw, k * im.height))
out.save(sys.argv[2]); print(sys.argv[2], out.size)
