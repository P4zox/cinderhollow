# contact sheets of the RC tour shots: python3 tools/shots/rc/contact.py PREFIX out.png [cols]
import sys, glob, re
from PIL import Image, ImageDraw
pre, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
order = ['SP9','SP10','SP11','SP12','SP8','SP15','SP14','SP17','SP13','SP16','LF1','D9','D10','D11','D12','D13','D14','D15','D16','D17','X6','X10','X11','X7','X8','X9','X12']
fs = []
for rid in order: fs += sorted(glob.glob(f'tools/shots/rc/out/{pre}{rid}_*.png'), key=lambda f: int(re.findall(r'_(\d+)\.png$', f)[0]))
W, H = 384, 216
rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * (H + 14)), (12, 12, 14))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB').resize((W, H))
    x, y = (i % cols) * W, (i // cols) * (H + 14)
    sheet.paste(im, (x, y + 14)); d.text((x + 4, y + 1), f.split('/')[-1][len(pre):-4], fill=(230, 220, 200))
sheet.save(out); print(len(fs), sheet.size)
