"""pair.py <out.png> <a.png> <b.png> [crop x0 y0 x1 y1 (in 1152x648 px)] [zoom]  — side by side (or stacked when cropped)"""
import sys
from PIL import Image, ImageDraw
o, a, b = sys.argv[1:4]
A, B = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
if len(sys.argv) > 7:
    box = tuple(int(v) for v in sys.argv[4:8]); z = float(sys.argv[8]) if len(sys.argv) > 8 else 1
    A, B = A.crop(box), B.crop(box)
    if z != 1: A = A.resize((int(A.width * z), int(A.height * z)), Image.NEAREST); B = B.resize((int(B.width * z), int(B.height * z)), Image.NEAREST)
out = Image.new('RGB', (A.width + B.width + 6, max(A.height, B.height) + 16), (12, 10, 16))
out.paste(A, (0, 16)); out.paste(B, (A.width + 6, 16))
d = ImageDraw.Draw(out); d.text((4, 2), 'before: ' + a.split('/')[-2], fill=(220, 210, 180)); d.text((A.width + 10, 2), 'after: ' + b.split('/')[-2], fill=(220, 210, 180))
out.save(o)
