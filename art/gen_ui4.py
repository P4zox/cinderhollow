#!/usr/bin/env python3
"""UI icons v4: the four traversal techniques (key items) -> art/ui_icons4.aseprite + assets/ui_icons4.png/.json
16x16, one tag per icon, same style as ui_icons2 (strong silhouette, upper-left light, 1px near-black outline layer).
Re-runnable: python3 art/gen_ui4.py"""
import math, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import asebuild  # noqa: E402

S = 16
OUT = (14, 10, 16, 255)
GOLD = [(96, 62, 22), (168, 118, 40), (226, 178, 72), (255, 232, 160)]
EMBER = [(122, 34, 16), (200, 70, 26), (244, 128, 40), (255, 214, 120)]
WIND = [(40, 56, 78), (84, 110, 140), (150, 184, 210), (228, 242, 255)]
ROCK = [(40, 32, 30), (86, 70, 60), (130, 110, 92)]

def canvas(): return Image.new('RGBA', (S, S), (0, 0, 0, 0))
def put(im, x, y, c):
    if 0 <= x < S and 0 <= y < S: im.putpixel((int(x), int(y)), c if len(c) == 4 else c + (255,))

def arc(im, cx, cy, r, a0, a1, cols, w=1.6):
    for y in range(S):
        for x in range(S):
            d = math.hypot(x + .5 - cx, y + .5 - cy); a = math.degrees(math.atan2(y + .5 - cy, x + .5 - cx)) % 360
            inside = (a0 <= a <= a1) if a0 <= a1 else (a >= a0 or a <= a1)
            if inside and abs(d - r) <= w / 2:
                k = (x - y) / 20 + .5; put(im, x, y, cols[min(len(cols) - 1, max(0, int(1 + k * (len(cols) - 1))))])

def outline(img):
    o = canvas(); a = img.getchannel('A')
    for y in range(S):
        for x in range(S):
            if a.getpixel((x, y)): continue
            if any(0 <= x + dx < S and 0 <= y + dy < S and a.getpixel((x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o.putpixel((x, y), OUT)
    return o

def hook():
    im = canvas()
    for i in range(9): put(im, 11 - i * .45, 2 + i, GOLD[2 if i < 6 else 1]); put(im, 12 - i * .45, 2 + i, GOLD[1])   # living root shaft
    arc(im, 6.5, 10.5, 3.6, 40, 250, GOLD[1:], 1.8)                    # the hook's curl
    for x, y in ((3, 8), (4, 6)): put(im, x, y, GOLD[3])                 # barb glint
    arc(im, 11.5, 3.5, 2.2, 0, 359, [GOLD[1], GOLD[2], GOLD[3]], 1.2)    # anchor ring
    for x, y in ((13, 7), (9, 13), (14, 11)): put(im, x, y, (120, 150, 60))   # root leaves
    return im

def emberdash():
    im = canvas()
    for i, y in enumerate((5, 8, 11)):                                   # speed streaks
        for x in range(1 + i, 9 + i): put(im, x, y, EMBER[0] if x < 4 + i else EMBER[1])
    for y in range(4, 13):                                               # flame head, teardrop pointing right
        for x in range(7, 15):
            dx, dy = x + .5 - 10.5, y + .5 - 8.5
            if (dx / 3.8) ** 2 + (dy / 3.6) ** 2 <= 1 and not (dx < -1 and abs(dy) > 2):
                r = math.hypot(dx - .8, dy); put(im, x, y, EMBER[3] if r < 1.4 else EMBER[2] if r < 2.6 else EMBER[1])
    put(im, 14, 8, EMBER[2]); put(im, 15, 8, EMBER[1])
    return im

def gale():
    im = canvas()
    for y in range(3, 14):                                               # billowing cape
        for x in range(2, 10):
            if x >= 3 + (13 - y) * .1 and x <= 9 - abs(y - 8) * .35 and (y > 4 or x > 5):
                put(im, x, y, WIND[1] if x < 5 else WIND[2])
    for x, y in ((3, 13), (5, 14), (7, 13)): put(im, x, y, WIND[1])
    for y, x0, x1 in ((4, 10, 15), (8, 11, 15), (12, 10, 14)):         # wind streaks sweeping past the cape
        for x in range(x0, x1): put(im, x, y, WIND[3] if x > x0 + 1 else WIND[2])
        put(im, x1, y - 1, WIND[2]); put(im, x0 - 1, y + 1, WIND[1])
    return im

def slam():
    im = canvas()
    for y in range(1, 9):                                                # falling blow: blade of force pointing down
        w = 1 if y < 4 else 2
        for x in range(8 - w, 8 + w): put(im, x, y, EMBER[2] if x == 7 else EMBER[1])
    for x, y in ((6, 8), (9, 8), (5, 7), (10, 7)): put(im, x, y, EMBER[3])
    for x in range(1, 15): put(im, x, 13, ROCK[1]); put(im, x, 14, ROCK[0])   # ground
    for x, y in ((7, 12), (8, 12), (6, 11), (9, 11), (7, 10), (8, 10)): put(im, x, y, EMBER[3])   # impact flare
    for (x0, y0, dx) in ((6, 13, -1), (9, 13, 1)):                        # glowing cracks
        for k in range(5): put(im, x0 + dx * k, y0 + (k % 2), EMBER[2] if k < 3 else EMBER[1])
    for x, y in ((2, 11), (13, 11), (3, 9), (12, 9)): put(im, x, y, ROCK[2])   # flung rubble
    return im

ICONS = [('i_hook', hook), ('i_emberdash', emberdash), ('i_gale', gale), ('i_slam', slam)]
frames, tags = [], []
for i, (name, fn) in enumerate(ICONS):
    body = fn(); frames.append({'ms': 100, 'cels': {'outline': outline(body), 'body': body}}); tags.append((name, i, i))
asebuild.build('ui_icons4', S, S, ['outline', 'body'], frames, tags)
prev = Image.new('RGBA', (S * len(ICONS) * 6, S * 6), (40, 36, 44, 255))
sheet = Image.open(os.path.join(HERE, '..', 'assets', 'ui_icons4.png'))
prev.alpha_composite(sheet.resize((sheet.width * 6, sheet.height * 6), Image.NEAREST))
os.makedirs(os.path.join(HERE, 'previews'), exist_ok=True); prev.save(os.path.join(HERE, 'previews', 'ui_icons4.png'))
print('ui_icons4:', [n for n, _ in ICONS])
