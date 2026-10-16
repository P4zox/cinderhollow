"""Review montage of the Hearthkeeper's moves: for every attack its tell frame and its first hit frame (2x, from the
built sheets), labelled; plus a 1x lineup of the idle of each phase beside the player.  python3 tools/shots/v17/boss/montage.py"""
import json, os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
A = os.path.join(ROOT, 'assets')
M = json.load(open(os.path.join(A, 'hearthkeeper_meta.json')))
W, H = M['frame']
try: F = ImageFont.truetype('/System/Library/Fonts/Avenir Next.ttc', 15, index=2)
except Exception: F = ImageFont.load_default()
def frame(ph, tag, i):
    name = M['sheets']['p%d' % ph][tag]
    js = json.load(open(os.path.join(A, name + '.json')))
    tg = next(t for t in js['meta']['frameTags'] if t['name'] == tag)
    f = js['frames'][tg['from'] + i]['frame']
    return Image.open(os.path.join(A, name + '.png')).convert('RGBA').crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h']))
ORDER = {1: ['slam', 'sweep', 'combo', 'grab', 'grabhold', 'snap', 'ring', 'leap', 'sparks', 'backhand', 'temper'],
         2: ['draw_blade', 'bl_rising', 'bl_cleave', 'bl_charge', 'draw_spear', 'sp_thrust', 'sp_lunge', 'sp_hurl', 'draw_chain', 'ch_lash', 'ch_sweep', 'ch_hook', 'coal_kick', 'temper'],
         3: ['ft_sweep', 'ember_rain', 'bellows_lo', 'bellows_hi', 'flame_grab', 'fgrabhold', 'nova', 'ft_combo', 'dark_lunge', 'temper', 'death']}
cells = []
for ph, tags in ORDER.items():
    for t in tags:
        P = 'p%d' % ph
        tel = (M['telegraph'].get(P, {}).get(t) or [{}])[0].get('frame')
        ev = M['events'].get(P, {}).get(t, {})
        wins = (M['attacks'].get(P, {}).get(t) or {}).get('windows') or []
        hit = wins[0]['active'][0] if wins else (sorted(ev.values())[0] if ev else None)
        picks = [i for i in (tel, hit) if i is not None] or [0]
        cells.append((f'P{ph} {t}', [frame(ph, t, i) for i in dict.fromkeys(picks)], wins[0]['rects'] if wins else None, hit))
CW, CH = W * 2, H * 2 + 24
cols = 4
rows = (len(cells) + cols - 1) // cols
sh = Image.new('RGBA', (cols * CW * 2 + 16, rows * CH + 16), (24, 26, 32, 255))
d = ImageDraw.Draw(sh)
for k, (lab, ims, rects, hit) in enumerate(cells):
    x0, y0 = 8 + (k % cols) * CW * 2, 8 + (k // cols) * CH
    for j, im in enumerate(ims):
        bg = Image.new('RGBA', (W, H), (58, 60, 70, 255)); bg.alpha_composite(im)
        dd = ImageDraw.Draw(bg); dd.line((0, M['anchor'][1], W, M['anchor'][1]), fill=(40, 36, 36, 255))
        if rects and j == len(ims) - 1 and str(hit) in rects:
            r = rects[str(hit)]; dd.rectangle((r[0], r[1], r[0] + r[2], r[1] + r[3]), outline=(255, 70, 60, 255))
        sh.alpha_composite(bg.resize((CW, H * 2), Image.NEAREST), (x0 + j * CW, y0 + 22))
    d.text((x0 + 4, y0 + 2), lab + ('   tell | hit (red: hit rect)' if len(ims) > 1 else ''), font=F, fill=(220, 222, 230, 255))
out = os.path.join(os.path.dirname(__file__), 'out', 'hk_moves_montage.png')
sh.save(out); print(out, sh.size, len(cells), 'tags')
