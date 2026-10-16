"""Line-up sheets of the Cold Forge foes from the built assets.  python3 tools/shots/v17/foes/lineup.py
 -> tools/shots/v17/foes/lineup_foes.png (1x beside the player, then 3x) and lineup_unforged.png (the 14 types, 3x)."""
import json, os
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
A = os.path.join(ROOT, 'assets'); OUT = os.path.dirname(os.path.abspath(__file__))
BG, BG2, TXT = (22, 24, 31, 255), (48, 51, 61, 255), (220, 222, 230, 255)

def frame(name, tag=None, i=0):
    d = json.load(open(os.path.join(A, name + '.json'))); im = Image.open(os.path.join(A, name + '.png')).convert('RGBA')
    t = [x for x in d['meta']['frameTags'] if x['name'] == tag][0] if tag else d['meta']['frameTags'][0]
    f = d['frames'][t['from'] + i]['frame']; m = json.load(open(os.path.join(A, name + '_meta.json'))) if os.path.exists(os.path.join(A, name + '_meta.json')) else {}
    c = im.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'])); an = m.get('anchor', [f['w'] // 2, f['h']])
    return c, an

def place(sheet, img, an, x, floor, k):
    big = img.resize((img.width * k, img.height * k), Image.NEAREST)
    sheet.alpha_composite(big, (x - an[0] * k, floor - an[1] * k))

def lineup(items, k, path, title, gap=24):
    ws = []
    for name, tag, i, lab in items:
        c, an = frame(name, tag, i); bb = c.getbbox(); ws.append((c, an, bb, lab))
    W_ = sum((bb[2] - bb[0]) * k + gap for c, an, bb, lab in ws) + gap
    H_ = max((an[1] - bb[1]) * k for c, an, bb, lab in ws) + 60
    S = Image.new('RGBA', (W_, H_), BG2); d = ImageDraw.Draw(S); d.text((8, 4), title, fill=TXT)
    x = gap; floor = H_ - 26
    for c, an, bb, lab in ws:
        place(S, c, (an[0] - 0, an[1]), x + (an[0] - bb[0]) * k, floor, k)
        d.text((x, floor + 6), lab, fill=TXT); x += (bb[2] - bb[0]) * k + gap
    d.line((0, floor, W_, floor), fill=(90, 94, 110, 255))
    S.save(path); print(path, S.size)

foes = [('player', None, 0, 'player'), ('cf_mite', 'crawl', 0, 'Cinder Mite'), ('cf_smith', 'idle', 0, 'Hollow Smith'),
        ('cf_wraith', 'idle', 0, 'Quench Wraith'), ('cf_hulk', 'idle', 0, 'Bellows Hulk'), ('cf_unforged_greatsword', 'idle', 0, 'The Unforged')]
lineup(foes, 1, os.path.join(OUT, 'lineup_foes_1x.png'), 'The Cold Forge foes, 1x (in-game scale)')
lineup(foes, 4, os.path.join(OUT, 'lineup_foes.png'), 'The Cold Forge foes, 4x')
T = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip', 'saxe', 'bow', 'fist', 'scythe', 'bell']
lineup([('cf_unforged_' + t, 'idle', 0, t) for t in T[:7]], 3, os.path.join(OUT, 'lineup_unforged_a.png'), 'The Unforged: the 14 weapon types (idle), 3x')
lineup([('cf_unforged_' + t, 'idle', 0, t) for t in T[7:]], 3, os.path.join(OUT, 'lineup_unforged_b.png'), 'The Unforged: the 14 weapon types (idle), 3x')
