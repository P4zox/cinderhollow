# zoomed-out world map around the RC wings (every room's tiles; RC rooms tinted): python3 tools/shots/rc/worldmap.py out.png
import sys
RC_ARGS = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
from PIL import Image, ImageDraw
RC = {'SP9','SP10','SP11','SP12','SP8','SP15','SP14','SP17','SP13','SP16','LF1','D9','D10','D11','D12','D13','D14','D15','D16','D17','X6','X7','X8','X9','X10','X11','X12'}
views = [('Stormward Spire + Last Field', -120, -262, 160, -60), ('The Deep', 220, 180, 410, 360), ('The Crown', 500, -90, 770, 10)]
S = 4
tiles = []
for (title, x0, y0, x1, y1) in views:
    im = Image.new('RGB', ((x1 - x0) * S, (y1 - y0) * S + 18), (10, 10, 12)); d = ImageDraw.Draw(im)
    for R in ROOMS:
        if R.gx + R.w < x0 or R.gx > x1 or R.gy + R.h < y0 or R.gy > y1: continue
        mine = R.id in RC
        for yy in range(R.h):
            for xx in range(R.w):
                gx, gy = R.gx + xx, R.gy + yy
                if not (x0 <= gx < x1 and y0 <= gy < y1): continue
                ch = R.g[yy][xx]
                if ch in SOLID: col = (70, 58, 52) if mine else (48, 48, 54)
                elif ch in HAZARD: col = (200, 70, 30)
                elif ch == 'S': col = (255, 220, 120)
                elif ch == '=': col = (150, 140, 110)
                else: col = (38, 30, 26) if mine else (22, 22, 26)
                px, py = (gx - x0) * S, (gy - y0) * S + 18
                d.rectangle([px, py, px + S - 1, py + S - 1], fill=col)
        px, py = (R.gx - x0) * S, (R.gy - y0) * S + 18
        d.rectangle([px, py, px + R.w * S - 1, py + R.h * S - 1], outline=(230, 150, 70) if mine else (90, 90, 110))
        d.text((px + 3, py + 2), R.id, fill=(255, 210, 150) if mine else (150, 150, 170))
    d.text((4, 3), title + '  (orange = RC rooms; yellow = shrines)', fill=(240, 230, 210))
    tiles.append(im)
W = max(t.size[0] for t in tiles); H = sum(t.size[1] + 8 for t in tiles)
out = Image.new('RGB', (W, H), (0, 0, 0)); y = 0
for t in tiles: out.paste(t, (0, y)); y += t.size[1] + 8
out.save(RC_ARGS[0]); print(out.size)
