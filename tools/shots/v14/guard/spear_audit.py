"""Spear art audit: every sp_* tag keeps the spear at full length in every frame.
gen_player.draw_weapon shrinks a weapon (down to 45%) until it fits the 64x40 frame; for the spear that made thrusts
whose tip would pass the frame edge (x 63) or a vertical spear passing the top/bottom shrink at their impact frames.
Prints each tag's per-frame length factor @ tip distance from the feet; exits 1 if any frame is shrunk.
  python3 tools/shots/v14/guard/spear_audit.py [tag ...]"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../art'))
import gen_player as G
fns = dict(G.ANIMS)
tags = sys.argv[1:] or [t for t, _ in G.ANIMS if t.startswith('sp_')]
bad = []
for t in tags:
    out = []
    for i, (cels, ms) in enumerate(fns[t]()):
        w = cels.get('Sword')
        if not isinstance(w, G.Wpn):
            out.append('-'); continue
        info = {}
        G.draw_weapon('spear', w.hand, w.ang, w.slen, w.planted, w.held, w.fitb, info)
        k = info['L'] / (19 * w.slen / 18.0)
        tip = info['hand'][0] + math.cos(math.radians(info['ang'])) * info['tip'] - 28
        out.append('%.2f@%d' % (k, tip) + ('*' if k < 0.99 else ''))
        if k < 0.99:
            bad.append('%s:%d' % (t, i))
    print('%-15s %s' % (t, ' '.join(out)))
print('shrunk frames:', ', '.join(bad) if bad else 'none')
sys.exit(1 if bad else 0)
