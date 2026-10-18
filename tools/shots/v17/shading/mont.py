#!/usr/bin/env python3
"""mont.py out.png cols w a/b.png ... -> grid montage (labels drawn on top)."""
import sys
from PIL import Image, ImageDraw
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
h = w * 9 // 16; rows = (len(fs) + cols - 1) // cols
M = Image.new('RGB', (w * cols, h * rows), (20, 20, 20)); d = ImageDraw.Draw(M)
for i, f in enumerate(fs):
    x, y = (i % cols) * w, (i // cols) * h
    M.paste(Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS), (x, y))
    d.rectangle([x, y, x + 8 * len(f.split('/')[-2] + '/' + f.split('/')[-1]) // 1 + 4, y + 14], fill=(0, 0, 0)); d.text((x + 3, y + 2), f.split('/')[-2] + '/' + f.split('/')[-1], fill=(255, 255, 0))
M.save(out)
