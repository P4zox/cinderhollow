"""contact sheet: tools/shots/sc/out/sheets/sheet_*.png -> tools/shots/sc/contact_sc.png (labelled, one tile per room)"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'out', 'sheets')
order = sys.argv[1:] or ['SF10','SF16','SF13','SF14','SF17','SF11','SF12','SF15','SF18','SF19','W6','NH8','NH17','NH14','NH10','NH9','NH13','NH11','NH16','NH12','NH15','E4','E5','E6','E7','H2','H3','H4']
TW, TH, COLS = 560, 330, 4
rows = (len(order) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * TW, rows * TH), (12, 10, 14)); dr = ImageDraw.Draw(sheet)
for i, r in enumerate(order):
    im = Image.open(os.path.join(D, f'sheet_{r}.png')).convert('RGB'); w, h = im.size
    k = min((TW - 8) / w, (TH - 26) / h); im = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    x, y = (i % COLS) * TW, (i // COLS) * TH
    sheet.paste(im, (x + (TW - im.width) // 2, y + 22 + (TH - 26 - im.height) // 2)); dr.text((x + 6, y + 5), r, fill=(240, 220, 180))
out = os.path.join(HERE, 'contact_sc.png'); sheet.save(out); print(out, sheet.size)
