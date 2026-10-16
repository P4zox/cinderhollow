"""Contact sheet: python3 sheet.py <dir> <prefix> <out.png> [cols]  -- crops each <prefix>_*.png round the middle third."""
import sys, os, glob
from PIL import Image, ImageDraw
d, pre, outp = sys.argv[1], sys.argv[2], sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
fs = sorted(glob.glob(os.path.join(d, pre + '_*.png')), key=lambda f: (0 if 'before' in f else 2 if 'after' in f else 1, f))
ims = []
for f in fs:
    im = Image.open(f).convert('RGB'); w, h = im.size
    ims.append((os.path.basename(f)[len(pre) + 1:-4], im.crop((int(w * 0.12), int(h * 0.05), int(w * 0.88), int(h * 0.95))).resize((int(w * 0.76 * 0.5), int(h * 0.9 * 0.5)))))
cw, ch = ims[0][1].size
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * cw, rows * (ch + 14)), (20, 18, 24))
dr = ImageDraw.Draw(S)
for i, (lab, im) in enumerate(ims):
    x, y = (i % cols) * cw, (i // cols) * (ch + 14)
    S.paste(im, (x, y + 14)); dr.text((x + 4, y + 1), lab, fill=(240, 220, 170))
S.save(outp); print(outp, S.size)
