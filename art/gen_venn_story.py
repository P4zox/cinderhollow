#!/usr/bin/env python3
"""The fourth ending, "The Ember Unbound" (agent V) -- panels in the style of art/gen_story.py (its helpers, read-only).

    python3 art/gen_venn_story.py [--preview]

    story_end_venn_1  the ruined Heart: Venn's ashes and her fallen scythe; the knight holds the last white flame
    story_end_venn_2  night over the Hallow: shrine after shrine going dark, the dead Root on the horizon
    story_end_venn_3  the knight, tiny, walking on across the dark ash plain -- the only light in the world
384x216 opaque, 1 frame, tag `p`. Previews: art/previews/story_end_venn_*.png (3x).
"""
import math, os, random, sys
import numpy as np
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
_argv = sys.argv
sys.argv = [sys.argv[0], "--preview"]            # import gen_story without building its own panels
import gen_story as GS  # noqa: E402
sys.argv = _argv
import asebuild  # noqa: E402

BUILD = "--preview" not in sys.argv
W, H = GS.W, GS.H
XX, YY = GS.XX, GS.YY
Layer, pick, radial, rays, fbm, smooth, shift, polymask, ellmask, below, ridge, rim, particles, segs_mask, branch_tree = (
    GS.Layer, GS.pick, GS.radial, GS.rays, GS.fbm, GS.smooth, GS.shift, GS.polymask, GS.ellmask, GS.below, GS.ridge, GS.rim,
    GS.particles, GS.segs_mask, GS.branch_tree)
ASH, COLD, STEEL, CRIM, SIL, PALE = GS.ASH, GS.COLD, GS.STEEL, GS.CRIM, GS.SIL, GS.PALE
# the last flame: white, barely warm
WHITE = GS.ramp("2a2a34", "4a4a5a", "7c7c8c", "b4b2bc", "dcd8d8", "f2eee6", "fffcf2", "ffffff")
NIGHT = GS.ramp("040408", "07070d", "0a0b13", "0e1019", "13161f", "191c27", "20242f", "282c38", "323644", "3e4252")


def flame(L, FX, x, y, r=3.0, glow=60):
    """The last flame: a small white tongue with a faint cold halo."""
    g = radial(x, y, glow, glow * 0.85)
    FX.put((g > 0.35) & ((g * 0.55) > GS.TH) & ~L.a, WHITE[2])
    FX.put((g > 0.7) & ((g * 0.8) > GS.TH) & ~L.a, WHITE[3])
    core = ellmask(x, y, r * 0.55, r * 0.8)
    tongue = polymask([(x - r * 0.7, y), (x, y - r * 2.6), (x + r * 0.7, y)])
    FX.put(ellmask(x, y, r, r * 1.1) | tongue, WHITE[6])
    FX.put(core, WHITE[7])


def panel_1():
    rnd = random.Random(701)
    Bg, Root, Floor, Ash, Knight, FX = (Layer(n) for n in ("Bg", "Root", "Floor", "Ash", "Knight", "FX"))
    FXX, FXY = 176, 160                                         # the flame in the knight's hand
    # the Heart gone dark: a cold dusk, all the gold drained out of it
    v = 0.1 + 0.28 * smooth(0, 150, YY) + 0.25 * radial(FXX, FXY, 230, 140) ** 1.6 + 0.03 * fbm(64, 24, 3)
    Bg.put(np.ones((H, W), bool), pick(NIGHT, v))
    # the great dead Root overhead: grey arches of bark with no light left in them
    segs = []
    for i, (x0, deg) in enumerate(((-20, 60), (40, 75), (330, 110), (400, 125), (260, 95))):
        branch_tree(rnd, x0, 190, math.radians(deg), rnd.uniform(70, 110), rnd.uniform(5, 8), 3, 0.25 if x0 < 200 else -0.25,
                    segs, spread=(0.3, 0.6), shrink=(0.55, 0.7), step=3.0, twig=False)
    rm, _, rs = segs_mask(segs)
    Root.put(rm, pick(ASH, 0.12 + 0.12 * (rs < 0) + 0.06 * radial(FXX, FXY, 250, 160)))
    Root.put(rm & ~shift(rm, -1, 0), ASH[3])
    # the floor of the Heart
    fl = below(GS.ridge(170, 2, 90, 7))
    Floor.put(fl, pick(ASH, 0.08 + 0.2 * radial(FXX, 175, 170, 36) + 0.05 * fbm(80, 8, 9)))
    Floor.put(fl & ~shift(fl, 0, 1), pick(WHITE, 0.1 + 0.4 * radial(FXX, 170, 150, 30)))
    # Venn's ashes: a low drift in the shape of someone kneeling, her scythe fallen beside it, the halo a cold ring
    AX_, AY_ = 250, 171
    heap = polymask([(AX_ - 26, AY_), (AX_ - 16, AY_ - 6), (AX_ - 6, AY_ - 14), (AX_ + 2, AY_ - 17), (AX_ + 8, AY_ - 12),
                     (AX_ + 18, AY_ - 5), (AX_ + 30, AY_)])
    Ash.put(heap, pick(ASH, 0.3 + 0.35 * radial(AX_ - 20, AY_ - 20, 60, 40) + 0.08 * fbm(6, 6, 11)))
    Ash.put(heap & ~shift(heap, 0, 1), ASH[6])
    # what is left of her (agent VN, after portrait_venn): a scrap of her black veil with its silver-embroidered
    # band lying over the drift, a few strands of silver hair, the little silver cross in the ash
    veil = polymask([(AX_ - 5, AY_ - 16), (AX_ + 5, AY_ - 15), (AX_ + 13, AY_ - 8), (AX_ + 21, AY_ - 1), (AX_ + 9, AY_ - 2),
                     (AX_ + 1, AY_ - 6), (AX_ - 8, AY_ - 9)])
    Ash.put(veil, pick(SIL, 0.25 + 0.5 * radial(AX_ - 12, AY_ - 24, 44, 30)))
    Ash.put(veil & ~shift(veil, 0, 1), WHITE[3])
    for k in range(9):                                           # silver hair spilling from under it
        Ash.dot(AX_ + 14 + k * 1.6, AY_ - 3 + (k % 3) * 0.7, WHITE[4] if k % 2 else WHITE[3])
    CXc, CYc = AX_ - 17, AY_ - 3
    for dy in range(-3, 2):
        Ash.dot(CXc, CYc + dy, WHITE[5] if dy < 0 else WHITE[4])
    Ash.dot(CXc - 1, CYc - 2, WHITE[4]); Ash.dot(CXc + 1, CYc - 2, WHITE[4])
    # her halo: a thin white ring, broken
    ang = np.degrees(np.arctan2((YY - (AY_ + 1)) / 3.2, (XX - (AX_ + 4)) / 13.0))
    ring = (np.abs(np.hypot((XX - (AX_ + 4)) / 13.0, (YY - (AY_ + 1)) / 3.2) - 1) < 0.12)
    gaps = (np.abs(ang - 20) < 16) | (np.abs(ang + 120) < 12) | (np.abs(ang - 150) < 9)
    Ash.put(ring & ~gaps, WHITE[4])
    shaft, _, _ = segs_mask([(AX_ - 40, AY_ + 2, AX_ + 44, AY_ - 3, 1.6, 1.3)])
    Ash.put(shaft, ASH[2])                                      # the ebony haft
    Ash.put(shaft & ~shift(shaft, 0, 1), ASH[5])
    blade = polymask([(AX_ + 44, AY_ - 3), (AX_ + 58, AY_ - 5), (AX_ + 72, AY_ - 2), (AX_ + 78, AY_ + 1), (AX_ + 66, AY_),
                      (AX_ + 52, AY_ - 1)])
    Ash.put(blade, ASH[3])
    Ash.put(blade & ~shift(blade, 0, -1), ASH[6])
    for _ in range(180):                                        # ash lifting off the drift toward the flame
        t = rnd.random()
        x = AX_ + rnd.gauss(0, 12) + (FXX - AX_) * t * 0.7
        y = AY_ - 8 - t * 70 - rnd.uniform(0, 20)
        FX.dot(x, y, ASH[6] if t < 0.5 else WHITE[4] if rnd.random() < 0.3 else ASH[5])
    # the knight from behind, the flame held low in his right hand
    km = GS.draw_knight_back(Knight, 160, 204, 0.6, (1, -0.2), WHITE[5], CRIM[5], wind=0.3, sword=False, seed=7)
    flame(Knight, FX, FXX, FXY, r=3.2, glow=46)
    particles(FX, rnd, 60, (0, 0, W, 200), [ASH[4], ASH[5]], avoid=Knight.a)
    return [Bg, Root, Floor, Ash, Knight, FX]


def shrine(L, FX, x, y, s, lit, smoke_rnd=None):
    """A little wayside shrine: plinth, post, a lantern cup. lit: 0 dark .. 1 burning."""
    base = polymask([(x - 5 * s, y), (x - 4 * s, y - 3 * s), (x + 4 * s, y - 3 * s), (x + 5 * s, y)])
    post = polymask([(x - 1.2 * s, y - 3 * s), (x - 1.2 * s, y - 14 * s), (x + 1.2 * s, y - 14 * s), (x + 1.2 * s, y - 3 * s)])
    cup = polymask([(x - 3 * s, y - 14 * s), (x - 2 * s, y - 17 * s), (x + 2 * s, y - 17 * s), (x + 3 * s, y - 14 * s)])
    L.put(base | post | cup, NIGHT[1])
    L.put((base | post | cup) & ~shift(base | post | cup, -1, 0), NIGHT[8])
    if lit > 0:
        g = radial(x, y - 18 * s, 22 * s * lit, 18 * s * lit)
        FX.put((g > 0.5) & ((g * 0.7) > GS.TH) & ~L.a, GS.GOLD[1])
        FX.put(ellmask(x, y - 18.5 * s, 1.4 * s, 2.2 * s), GS.GOLD[6])
    elif smoke_rnd is not None:
        for k in range(10):
            FX.dot(x + math.sin(k * 0.7) * 1.5 * s + k * 0.4, y - 18 * s - k * 2.2 * s, NIGHT[9] if k < 4 else NIGHT[7])


def panel_2():
    rnd = random.Random(702)
    Sky, Far, Hills, Shrines, FX = (Layer(n) for n in ("Sky", "Far", "Hills", "Shrines", "FX"))
    HZ = 118
    v = 0.12 + 0.5 * smooth(-20, HZ + 10, YY) ** 1.6 + 0.02 * fbm(96, 12, 21)
    Sky.put(np.ones((H, W), bool), pick(NIGHT, v))
    for _ in range(70):                                         # a few cold stars
        Sky.dot(rnd.uniform(0, W), rnd.uniform(0, HZ - 30), NIGHT[8] if rnd.random() < 0.7 else WHITE[3])
    # the dead Root on the horizon, a grey ruin
    RX, RY = 300, HZ - 4
    segs = []
    for i in range(9):
        deg = 20 + i * 17 + rnd.uniform(-5, 5)
        branch_tree(rnd, RX + math.cos(math.radians(deg)) * 5, RY - math.sin(math.radians(deg)) * 5, math.radians(deg),
                    rnd.uniform(12, 22), rnd.uniform(1.6, 2.4), 2, 0.0, segs, spread=(0.3, 0.5), shrink=(0.45, 0.6), step=2.0,
                    twig=False)
    rm, _, _ = segs_mask(segs)
    Far.put(rm | ellmask(RX, RY, 7, 8) | polymask([(RX - 60, HZ + 1), (RX, RY - 4), (RX + 4, RY + 4), (RX - 60, HZ + 3)]), NIGHT[5])
    # layered hills, each ridge carrying its shrine; the nearest are dark and smoking, the farthest still lit
    ridges = [(HZ + 4, 3, 70, 31, 0.0), (HZ + 26, 5, 90, 32, 0.12), (HZ + 52, 7, 110, 33, 0.22), (HZ + 82, 8, 120, 34, 0.3)]
    for i, (base, amp, sc, seed, shade) in enumerate(ridges):
        rl = ridge(base, amp, sc, seed)
        m = below(rl)
        Hills.put(m, pick(NIGHT, 0.34 + shade * 0.5 - 0.2 * smooth(base, base + 40, YY)))
        Hills.put(m & ~shift(m, 0, 1), NIGHT[5 + i // 2])
    spots = [(60, 0, 0.8, 0.5), (140, 0, 0.8, 1.0), (240, 0, 0.8, 0.35), (210, 1, 1.2, 0.0), (330, 1, 1.2, 0.0), (90, 2, 1.7, 0.0),
             (270, 2, 1.7, 0.0), (180, 3, 2.3, 0.0)]
    for x, ri, s, lit in spots:
        base, amp, sc, seed, _ = ridges[ri]
        y = ridge(base, amp, sc, seed)[int(x)]
        shrine(Shrines, FX, x, y + 1, s, lit, smoke_rnd=rnd)
    # one ember of the last lit shrine drifting up
    for k in range(8):
        FX.dot(140 + k * 0.8, ridge(HZ + 4, 3, 70, 31)[140] - 12 - k * 3, GS.GOLD[4] if k < 3 else GS.GOLD[2])
    particles(FX, rnd, 90, (0, 0, W, H), [NIGHT[6], NIGHT[7]])
    return [Sky, Far, Hills, Shrines, FX]


def panel_3():
    rnd = random.Random(703)
    Sky, Far, Plain, Walker, FX = (Layer(n) for n in ("Sky", "Far", "Plain", "Walker", "FX"))
    HZ = 132
    WX, WY = 208, 176                                           # the walker's feet
    v = 0.08 + 0.3 * smooth(0, HZ, YY) ** 1.5 + 0.02 * fbm(80, 10, 41)
    Sky.put(np.ones((H, W), bool), pick(NIGHT, v))
    # the Root rotted to a stump far behind
    Far.put(polymask([(40, HZ + 1), (52, HZ - 18), (58, HZ - 24), (63, HZ - 16), (74, HZ + 1)]), NIGHT[4])
    Far.put(polymask([(58, HZ - 22), (48, HZ - 34), (52, HZ - 34), (60, HZ - 24)]), NIGHT[4])
    rl = ridge(HZ, 2, 60, 42)
    pl = below(rl)
    Plain.put(pl, pick(NIGHT, 0.18 + 0.2 * smooth(HZ, H, YY) + 0.22 * radial(WX + 6, WY - 20, 90, 40) + 0.03 * fbm(90, 6, 43)))
    # his footprints behind him, back toward the stump
    for k in range(18):
        x = WX - 10 - k * 9 + math.sin(k) * 1.5
        y = WY + 1 - k * 1.8 + (k % 2) * 2
        if y > HZ + 3:
            Plain.put(ellmask(x, y, 1.8, 0.7), NIGHT[2])
    wm = GS.walker_back(Walker, WX, WY, 0.42, 0.3, (1, 0), WHITE[5], cape_c=CRIM)
    rim(Walker, wm, 1, 0, WHITE[6], 1)
    flame(Walker, FX, WX + 11, WY - 12, r=1.8, glow=36)
    # ash falling like snow
    particles(FX, rnd, 220, (0, 0, W, H), [NIGHT[7], NIGHT[8], ASH[4]], avoid=Walker.a)
    return [Sky, Far, Plain, Walker, FX]


PANELS = {"story_end_venn_1": panel_1, "story_end_venn_2": panel_2, "story_end_venn_3": panel_3}


def main():
    ims = []
    for name, fn in PANELS.items():
        layers = fn()
        img = GS.compose(layers)
        ims.append(img)
        img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(ART, "previews", f"{name}.png"))
        if BUILD:
            asebuild.build(name, W, H, [L.name for L in layers], [{"ms": 1000, "cels": {L.name: L.image() for L in layers}}],
                           [("p", 0, 0)])
        print("built", name)
    sheet = Image.new("RGBA", (W * 2 * 2 + 4, H * 2 * 2 + 4), (30, 30, 34, 255))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((W * 2, H * 2), Image.NEAREST), ((i % 2) * (W * 2 + 4), (i // 2) * (H * 2 + 4)))
    sheet.save(os.path.join(ART, "previews", "story_end_venn_all.png"))


if __name__ == "__main__":
    main()
