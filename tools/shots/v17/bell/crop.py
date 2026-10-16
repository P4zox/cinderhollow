"""Crop a row of Funeral Peal snapshots around the knight into one montage: python3 crop.py <dir> <out.png> name1 name2 ..."""
import sys, os
from PIL import Image
d, out, names = sys.argv[1], sys.argv[2], sys.argv[3:]
ims = [Image.open(os.path.join(d, n + '.png')).convert('RGB') for n in names]
w, h = ims[0].size
# the knight sits near screen centre; keep a band around him
fx, fy = [float(v) / 1000 for v in os.environ.get('CAM', '500,700').split(',')]
box = (int(w * (fx - 0.24)), int(h * (fy - 0.38)), int(w * (fx + 0.24)), int(h * (fy + 0.08)))
cw, ch = box[2] - box[0], box[3] - box[1]
cols = min(4, len(ims)); rows = (len(ims) + cols - 1) // cols
m = Image.new('RGB', (cols * cw, rows * ch))
for i, im in enumerate(ims):
    m.paste(im.crop(box), ((i % cols) * cw, (i // cols) * ch))
m.save(out); print(out, m.size)
