"""dev helper: crop one tag row of a kit preview (4x) into a readable strip. usage: starfall_crop.py name row f0 f1 out"""
import sys
from PIL import Image
name, row, f0, f1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
fw, fh = int(sys.argv[6]), int(sys.argv[7])
im = Image.open(f"art/previews/{name}.png")
s = 4
y0 = row * (fh + 12) * s + 10 * s
x0 = f0 * (fw + 2) * s
x1 = (f1 + 1) * (fw + 2) * s
c = im.crop((x0, y0, x1, y0 + fh * s))
k = float(sys.argv[8]) if len(sys.argv) > 8 else 0.5
c.resize((int(c.size[0] * k), int(c.size[1] * k)), Image.NEAREST).save(out)
