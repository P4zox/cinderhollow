"""Big contact sheet of bw_ tags: python3 tools/shots/v15/bow/zoom.py out.png tag[:frames] ... (6x, ashstring)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../art'))
import player_preview as PP
from PIL import Image, ImageDraw
out = sys.argv[1]; rows = []
S = int(os.environ.get('S', '5'))
for a in sys.argv[2:]:
    tag, _, fs = a.partition(':')
    fr = PP.render(tag, 'ashstring')
    idx = [int(x) for x in fs.split(',')] if fs else range(len(fr))
    rows.append((tag, [(i, fr[i][0], fr[i][1]) for i in idx]))
n = max(len(r[1]) for r in rows)
img = Image.new('RGBA', (n * 64 * S, len(rows) * 40 * S), (70, 70, 78, 255))
d = ImageDraw.Draw(img)
for ry, (tag, fr) in enumerate(rows):
    for cx, (i, im, ms) in enumerate(fr):
        bg = Image.new('RGBA', im.size, (70, 70, 78, 255)); bg.alpha_composite(im)
        img.paste(bg.resize((64 * S, 40 * S), Image.NEAREST), (cx * 64 * S, ry * 40 * S))
        d.text((cx * 64 * S + 3, ry * 40 * S + 2), f'{tag} {i} {ms}', fill=(255, 220, 120, 255))
img.save(out); print(out, img.size)
