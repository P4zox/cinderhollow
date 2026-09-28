#!/usr/bin/env python3
"""True-epilogue panels (agent X), in the style of art/gen_story.py (reuses its helpers read-only).

    python3 art/gen_secrets_story.py [--preview]

    sc_story_true_1  the First Ember gutters out in the dark hollow; the knight holds the first spark
    sc_story_true_2  dawn: a golden sapling rising out of the ash, the knight and Venn watching it grow
384x216 opaque, 1 frame, tag `p`. Previews: art/previews/sc_story_true_1.png / _2.png (3x).
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
EMBER = GS.ramp("050304", "0c0607", "140a0a", "1e0e0c", "2c140e", "3e1a10", "5a2412", "7e3414", "a84a18", "d86a24", "ff9a3a",
                "ffd88a", "fff4d8")
DAWN, GOLD, HOT, SIL, STEEL, CRIM, ASH, GREEN = GS.DAWN, GS.GOLD, GS.HOT, GS.SIL, GS.STEEL, GS.CRIM, GS.ASH, GS.GREEN


def panel_1():
    rnd = random.Random(501)
    Bg, Cols, Ghost, Floor, Knight, FX = (Layer(n) for n in ("Bg", "Cols", "Ghost", "Floor", "Knight", "FX"))
    SX, SY = 192, 150                                   # the spark in the knight's hands
    v = 0.05 + 0.2 * radial(SX, SY, 260, 150) ** 1.4 + 0.04 * fbm(64, 32, 3)
    Bg.put(np.ones((H, W), bool), pick(EMBER, v))
    # basalt columns receding into the dark, rim-lit by the spark
    for k in range(11):
        cx = 12 + k * 36 + rnd.uniform(-6, 6)
        if abs(cx - SX) < 50:
            continue
        w = rnd.uniform(10, 18)
        top = rnd.uniform(0, 40)
        m = (XX > cx) & (XX < cx + w) & (YY > top) & (YY < 190)
        near = 1 - min(1.0, abs(cx - SX) / 200)
        Cols.put(m, pick(EMBER, 0.08 + 0.1 * near + 0.05 * ((XX - cx) / w < 0.3)))
        Cols.put(m & ((XX - cx) > w - 1.5) if cx < SX else m & ((XX - cx) < 1.5), EMBER[int(3 + 4 * near)])
    # the First Ember, dissolving: a tall dark silhouette breaking into rising sparks
    gx, gy = SX + 64, 190
    body = polymask([(gx - 8, gy), (gx - 9, gy - 40), (gx - 12, gy - 62), (gx - 7, gy - 74), (gx + 7, gy - 74), (gx + 12, gy - 62),
                     (gx + 9, gy - 40), (gx + 8, gy)]) | ellmask(gx, gy - 82, 7, 8)
    brk = fbm(8, 8, 41)
    fade = smooth(gy - 90, gy - 10, YY)                  # dissolving from the top down
    keep = body & (brk * 0.8 + fade * 0.6 > 0.46)
    Ghost.put(keep, pick(EMBER, 0.06 + 0.08 * brk))
    Ghost.put(keep & ~shift(keep, -1, 0), EMBER[9])
    cr = keep & (np.abs(np.sin(XX * 0.9 + YY * 0.5 + brk * 6)) < 0.08)
    Ghost.put(cr, EMBER[10])
    for _ in range(420):                                 # the sparks it is becoming
        x = gx + rnd.gauss(0, 9)
        y = gy - 90 + rnd.uniform(-60, 70) * rnd.random()
        FX.dot(x + rnd.uniform(-2, 2), y - rnd.uniform(0, 40), EMBER[rnd.choice((9, 10, 10, 11, 12))])
    # floor of ash
    fl = below(ridge(188, 4, 80, 7))
    Floor.put(fl, pick(ASH, 0.12 + 0.25 * radial(SX, 190, 180, 30)))
    Floor.put(fl & ~shift(fl, 0, 1), pick(EMBER, 0.45 + 0.4 * radial(SX, 190, 150, 30)))
    # the knight from behind, kneeling-low (drawn standing, sunk into the ash a little), the spark before him
    GS.draw_knight_back(Knight, SX - 18, 202, 0.78, (1, -0.3), EMBER[10], CRIM[6], wind=0.2, sword=False)
    glow = radial(SX, SY, 60, 50)
    core = ellmask(SX, SY, 3.5, 3.5)
    halo = ellmask(SX, SY, 9, 8) & ~core
    FX.put(halo & ((radial(SX, SY, 9, 8) * 1.4) > GS.TH), EMBER[10])
    FX.put(core, EMBER[12])
    for a in range(0, 360, 45):
        for r in range(5, 13):
            if r % 2 == 0:
                FX.dot(SX + math.cos(math.radians(a)) * r, SY + math.sin(math.radians(a)) * r * 0.8, EMBER[11])
    particles(FX, rnd, 30, (0, 20, W, 200), [EMBER[7], EMBER[8]], avoid=Knight.a)
    return [Bg, Cols, Ghost, Floor, Knight, FX]


def panel_2():
    rnd = random.Random(502)
    Sky, Far, Hill, Tree, People, FX = (Layer(n) for n in ("Sky", "Far", "Hill", "Tree", "People", "FX"))
    HZ = 140
    SXn, SYn = 250, HZ - 4
    v = 0.1 + 0.62 * smooth(-10, HZ, YY) ** 1.3 + 0.3 * radial(SXn, SYn, 220, 80) ** 1.5 + 0.04 * rays(SXn, SYn, 17, 0.7, 5) * (YY < HZ)
    Sky.put(np.ones((H, W), bool), pick(DAWN, v))
    # the old fallen Root, dim and grey on the horizon
    rl = ridge(HZ, 3, 90, 4)
    Far.put(below(rl), pick(DAWN, 0.35 - 0.2 * smooth(HZ, HZ + 40, YY)))
    trunk = (YY > HZ - 3 - 1.5 * np.sin(XX / 30.0) - 3 * smooth(170, 40, XX)) & (YY < HZ) & (XX > 36) & (XX < 170)
    Far.put(trunk, pick(DAWN, 0.22 + 0.1 * (YY < HZ - 3)))
    rp = []
    for i in range(7):
        branch_tree(rnd, 38, HZ - 4, math.radians(60 + i * 12), rnd.uniform(8, 16), 1.4, 1, 0.0, rp, step=2.0, twig=False)
    rpm, _, _ = segs_mask(rp)
    Far.put(rpm, DAWN[2])
    # the ash hill with a sapling on its crown
    hl = ridge(176, 10, 120, 9) - 16 * np.exp(-((np.arange(W) - 192) ** 2) / 4000.0)
    hill = below(hl)
    Hill.put(hill, pick(ASH, 0.25 + 0.18 * smooth(220, 150, YY) + 0.2 * radial(192, 160, 90, 30)))
    Hill.put(hill & ~shift(hill, 0, 1), pick(DAWN, 0.8 + 0.2 * radial(SXn, SYn, 250, 80)))
    for _ in range(60):                                   # green shoots in the ash
        x = rnd.uniform(0, W)
        y = hl[int(x)] + rnd.uniform(1, 30)
        if y < H:
            People.dot(x, y, GREEN[rnd.randrange(3, 6)])
            People.dot(x, y - 1, GREEN[4])
    # the sapling: slender gold trunk, a few branches, glowing leaves
    segs = []
    tx, ty = 192, int(hl[192]) + 1
    branch_tree(rnd, tx, ty, math.pi / 2, 44, 2.8, 3, 0.0, segs, spread=(0.35, 0.6), shrink=(0.55, 0.7), step=2.0, twig=True)
    tm, tw, ts = segs_mask(segs)
    Tree.put(tm, pick(GOLD, 0.45 + 0.35 * (ts < 0) + 0.15 * (tw > 1.8)))
    leaf = np.zeros((H, W), bool)
    for (x0, y0, x1, y1, *_r) in segs:
        if y1 < ty - 18 and rnd.random() < 0.5:
            leaf |= ellmask(x1, y1, 2.2, 1.6)
    Tree.put(leaf & ~tm, pick(HOT, 0.3 + 0.5 * radial(tx, ty - 40, 30, 30)))
    glow = radial(tx, ty - 30, 50, 44)
    Sky.put((glow > 0.2) & ~below(hl), pick(DAWN, v + 0.18 * glow))
    # the knight and Venn watching, small, on the slope
    GS.walker_back(People, 150, int(hl[150]) + 2, 0.42, 0.0, (1, -0.3), DAWN[10])
    vm = polymask([(118, hl[118] + 2), (120, hl[118] - 16), (123, hl[118] - 22), (127, hl[118] - 22), (130, hl[118] - 16), (132, hl[118] + 2)])
    People.put(vm, pick(GS.SIL, 0.35 + 0.4 * (XX > 126)))                    # her black habit (as portrait_venn)
    People.put(ellmask(125, hl[118] - 25, 3, 3.5), GS.SIL[2])                 # the black veil
    People.put(polymask([(126, hl[118] - 25), (128, hl[118] - 25), (128, hl[118] - 12), (126, hl[118] - 14)]), GS.PALE[4])  # silver hair
    People.dot(128, hl[118] - 24, GS.PALE[3])                                 # her face
    People.dot(131, hl[118] - 12, GS.PALE[5])                                 # her lantern: a white light
    rim(People, vm, 1, -0.3, DAWN[10])
    particles(FX, rnd, 40, (100, 60, 290, 170), [GOLD[5], GOLD[6], HOT[2]])
    return [Sky, Far, Hill, Tree, People, FX]


PANELS = {"sc_story_true_1": panel_1, "sc_story_true_2": panel_2}


def main():
    for name, fn in PANELS.items():
        layers = fn()
        img = GS.compose(layers)
        img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(ART, "previews", f"{name}.png"))
        if BUILD:
            asebuild.build(name, W, H, [L.name for L in layers], [{"ms": 1000, "cels": {L.name: L.image() for L in layers}}], [("p", 0, 0)])
        print("built", name)


if __name__ == "__main__":
    main()
