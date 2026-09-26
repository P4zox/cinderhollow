"""Closeup contact sheet of art/previews/venn_wip_<tag>_p<n>.png strips (4x, 192x128 frames).
usage: python3 tools/shots/v/closeup.py out.png tag:phase[:frames] ... [--box x0,y0,x1,y1] [--s 4]"""
import sys
from PIL import Image
args = sys.argv[1:]
out = args.pop(0)
box = (40, 20, 152, 124); s = 4
if '--box' in args:
    i = args.index('--box'); box = tuple(int(v) for v in args[i + 1].split(',')); del args[i:i + 2]
if '--s' in args:
    i = args.index('--s'); s = int(args[i + 1]); del args[i:i + 2]
rows = []
for a in args:
    parts = a.split(':'); tag, ph = parts[0], parts[1]
    im = Image.open(f'/Users/halstonchen/Claude/cinderhollow/art/previews/venn_wip_{tag}_p{ph}.png')
    n = im.width // (192 * 4)
    idx = [int(v) for v in parts[2].split(',')] if len(parts) > 2 else list(range(n))
    fr = []
    for k in idx:
        c = im.crop((k * 768 + box[0] * 4, box[1] * 4, k * 768 + box[2] * 4, box[3] * 4))
        fr.append(c.resize((c.width * s // 4, c.height * s // 4), Image.NEAREST))
    rows.append(fr)
w = max(sum(f.width + 4 for f in r) for r in rows); h = sum(r[0].height + 4 for r in rows)
sh = Image.new('RGBA', (w, h), (30, 30, 34, 255))
y = 0
for r in rows:
    x = 0
    for f in r:
        sh.paste(f, (x, y)); x += f.width + 4
    y += r[0].height + 4
sh.save(out)
print(sh.size)
