"""Trees pass: before/after montage of the in-game shots (before/ = the old tree sheets, after/ = the new ones; snap.js)."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = [('TV14_stand', 'TV14 Mossbed Glade, standing at the bench (Mother Oak)'), ('TV14_seat', 'TV14 seated at the bench: the vista view'),
        ('TV14_east', 'TV14 east end (oak + tv_tree v1)'), ('TV2', 'TV2 Mossgrave Verge (tv_tree v0 / v2)'),
        ('TV10', "TV10 The Hunter's Trail (tv_tree v1 / v0)"), ('TV9_elder', 'TV9 The Elder Canopy: the Elder (xsa_elder)')]
K = 0.75; W, H = int(1152 * K), int(648 * K); PAD = 8; LAB = 26
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
except Exception: font = ImageFont.load_default()
out = Image.new('RGB', (2 * W + 3 * PAD, len(ROWS) * (H + LAB + PAD) + PAD + LAB), (18, 18, 20))
d = ImageDraw.Draw(out)
d.text((PAD + 4, 4), 'BEFORE', fill=(230, 200, 140), font=font); d.text((2 * PAD + W + 4, 4), 'AFTER (trees pass)', fill=(150, 230, 160), font=font)
y = LAB
for name, label in ROWS:
    d.text((PAD + 4, y + 4), label, fill=(220, 220, 220), font=font)
    for i, side in enumerate(('before', 'after')):
        im = Image.open(os.path.join(HERE, side, name + '.png')).convert('RGB').resize((W, H), Image.LANCZOS)
        out.paste(im, (PAD + i * (W + PAD), y + LAB))
    y += H + LAB + PAD
out.save(os.path.join(HERE, 'before_after.png')); print(out.size)
