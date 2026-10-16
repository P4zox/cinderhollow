# contact sheets: python3 tools/shots/movehelp/montage.py <outdir> <prefix> <dest.png> [cols] [scale] [crop x0,y0,x1,y1]
import sys, glob, os
from PIL import Image, ImageDraw
d, pre, dest = sys.argv[1], sys.argv[2], sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 3
k = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
crop = tuple(int(v) for v in sys.argv[6].split(',')) if len(sys.argv) > 6 else None
fs = sorted(glob.glob(os.path.join(d, pre + '*.png')))
ims = []
for f in fs:
    im = Image.open(f).convert('RGB')
    if crop: im = im.crop(crop)
    ims.append((os.path.basename(f)[:-4], im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)))
w, h = ims[0][1].size; rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (w + 6) + 6, rows * (h + 20) + 6), (12, 10, 14)); dr = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate(ims):
    x, y = 6 + (i % cols) * (w + 6), 6 + (i // cols) * (h + 20)
    sheet.paste(im, (x, y + 14)); dr.text((x, y + 1), n, fill=(230, 199, 122))
sheet.save(dest); print(dest, len(ims), sheet.size)
