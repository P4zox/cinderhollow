import json, sys
from PIL import Image
names = sys.argv[1].split(',')
out = sys.argv[2]; scale = int(sys.argv[3]) if len(sys.argv) > 3 else 2
ims = []
for n in names:
    im = Image.open(f'assets/{n}.png').convert('RGBA'); ims.append(im)
W = max(i.width for i in ims); Hh = sum(i.height + 6 for i in ims)
cv = Image.new('RGBA', (min(W, 1800), Hh), (52, 50, 60, 255)); y = 0
for i in ims:
    cv.paste(i.crop((0, 0, min(i.width, 1800), i.height)), (0, y), i.crop((0, 0, min(i.width, 1800), i.height))); y += i.height + 6
cv = cv.resize((cv.width * scale, cv.height * scale), Image.NEAREST); cv.save(out); print(cv.size)
