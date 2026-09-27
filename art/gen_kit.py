"""Kit mechanics sheets (agent KM) -> assets/kit_plat, kit_gate, kit_parts (+ .aseprite sources).

kit_plat  16x16: per skin tag `<skin>` = [left, mid, right, single] slab segments; tag `crack` = 2 crack overlays.
kit_gate  16x16: `bar_<skin>`, `foot_<skin>`, `cap_<skin>`, `yoke_<skin>`, `anchor_<skin>` (+ neon laser caps).
kit_parts 32x32: lever/switch/plate/crate/spring/brazier/blade per skin, bell, lantern, glyph(+glyph_lit), stop, frame,
                 emitter/mirror/socket per beam style (sun/star/neon).
Run: python3 art/gen_kit.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asebuild                    # noqa: E402
import kit_draw as KD              # noqa: E402

SK = KD.SKINS


def sheet(name, size, groups):
    """groups: list of (tag, [images], ms)."""
    frames, tags = [], []
    for tag, imgs, ms in groups:
        a = len(frames)
        for im in imgs:
            frames.append({"ms": ms, "cels": {"art": im}})
        tags.append((tag, a, len(frames) - 1))
    asebuild.build(name, size, size, ["art"], frames, tags)
    print(name, len(frames), 'frames')


def main():
    sheet('kit_plat', 16, [(s, [KD.slab(s, p, i) for i, p in enumerate('lmrs')], 100) for s in SK] +
          [('crack', [KD.cracks(1), KD.cracks(2)], 100)])
    g = []
    for s in SK:
        if s == 'neon':
            g += [('cap_neon', [KD.gate_cap('neon')], 100), ('foot_neon', [KD.gate_foot_neon()], 100)]
        else:
            g += [('bar_' + s, [KD.gate_bar(s)], 100), ('foot_' + s, [KD.gate_foot(s)], 100), ('cap_' + s, [KD.gate_cap(s)], 100)]
        g += [('yoke_' + s, [KD.yoke(s)], 100), ('anchor_' + s, [KD.anchor(s)], 100)]
    sheet('kit_gate', 16, g)
    p = []
    for s in SK:
        p += [('lever_' + s, [KD.lever(s, False), KD.lever(s, True)], 100),
              ('switch_' + s, [KD.switch(s, False), KD.switch(s, True)], 100),
              ('plate_' + s, [KD.plate(s, False), KD.plate(s, True)], 100),
              ('crate_' + s, [KD.crate(s)], 100),
              ('spring_' + s, [KD.spring(s, False), KD.spring(s, True)], 100),
              ('brazier_' + s, [KD.brazier(s, f) for f in range(4)], 100),
              ('blade_' + s, [KD.blade(s)], 100)]
    p += [('bell', [KD.bell(False), KD.bell(True)], 100), ('lantern', [KD.lantern(False), KD.lantern(True)], 100),
          ('glyph', [KD.glyph(i, False) for i in range(8)], 100), ('glyph_lit', [KD.glyph(i, True) for i in range(8)], 100),
          ('stop', [KD.organ_stop(False), KD.organ_stop(True)], 100), ('frame', [KD.portrait(False), KD.portrait(True)], 100)]
    for st in ('sun', 'star', 'neon'):
        p += [('emitter_' + st, [KD.emitter(st)], 100), ('mirror_' + st, [KD.mirror(st, r) for r in range(4)], 100),
              ('socket_' + st, [KD.socket(st, False), KD.socket(st, True)], 100)]
    sheet('kit_parts', 32, p)


if __name__ == '__main__':
    main()
