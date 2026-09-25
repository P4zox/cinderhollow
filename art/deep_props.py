"""Props for the Burning Deep: the hanging Crucible (D8) and the forge hatch grate (D1/D7 shortcut).

dp_crucible  96x72  idle(4 loop)   a vast riveted iron crucible on two lugs, its molten charge heaving and glowing,
                                   Ashwright's gold seal on the flank. Drawn by the engine with pivot [48, 10] (the lug axis).
dp_props     32x32  hatch(1) hatch_open(1)   the grate as shut (top-left 32x16) and swung open (top-left 8x32)
"""
import math
from PIL import Image
from envlib import C, ramp, K, T, h01, blank
import deep_tiles as DT

IR, MG, GD = DT.IR, DT.MG, DT.GD


def crucible(f):
    W_, H_ = 96, 72
    img = blank(W_, H_)
    px = img.load()
    cx = 48
    # body: a deep bowl, flared rim at y 14..18, tapering to a rounded foot at ~66
    for y in range(14, 67):
        t = (y - 14) / 52
        hw = 36 - 10 * t ** 1.8
        if y >= 62:
            hw -= (y - 61) * 2.2
        for x in range(int(cx - hw), int(cx + hw) + 1):
            d = (x + .5 - cx) / hw
            # round bowl: lit from the upper-left, the far side lost in soot; the charge's heat glows through the base
            nz = math.sqrt(max(0.0, 1 - d * d))
            lv = 0.6 + 2.6 * max(0.0, -0.55 * d + 0.45 * nz) - 1.2 * t
            band = abs(((x - cx) % 14) - 7) < 1
            if band:
                lv += 0.9
                if (y % 6) == 3:
                    lv = 4
            c = IR[int(max(0, min(5, round(lv))))]
            if d > 0.82 and not band:
                c = MG[1] if d > 0.93 and t < 0.8 else IR[1]           # hot rim on the shadow side
            if t > 0.86 and abs(d) < 0.7:
                c = MG[1] if (x + y) % 2 else IR[1]                     # the base glows with the charge's heat
            if h01(x, y // 2, 5) < 0.015 and 0.2 < t < 0.8:
                c = MG[3]
            px[x, y] = c
    # rim: thick iron lip, gold banding
    for y in range(10, 16):
        for x in range(cx - 40, cx + 41):
            if y < 12 and abs(x - cx) > 38:
                continue
            c = IR[4] if y == 10 else IR[3] if y == 11 else GD[3] if y == 13 else GD[2] if y == 14 else IR[2]
            px[x, y] = c
    # molten charge: heaving surface inside the rim
    for x in range(cx - 36, cx + 37):
        w = 1.2 * math.sin(f * math.pi / 2 + x * 0.25) + 0.8 * math.sin(-f * math.pi / 2 + x * 0.11)
        top = int(round(8 + w))
        for y in range(top, 10):
            d = y - top
            px[x, y] = MG[7] if d == 0 else MG[6] if d == 1 else MG[5]
    # spouts both sides
    for sgn in (-1, 1):
        for i in range(7):
            x = cx + sgn * (40 + i)
            for y in range(10 - i // 3, 14 - i // 2):
                px[x, y] = IR[3] if y > 10 - i // 3 else IR[4]
        px[cx + sgn * 46, 9] = MG[5]
    # lugs (pivots) + chain rings
    for sgn in (-1, 1):
        lx = cx + sgn * 30
        for y in range(4, 12):
            for x in range(lx - 3, lx + 4):
                d = math.hypot(x + .5 - lx, y + .5 - 7)
                if 1.6 < d < 3.6:
                    px[x, y] = IR[4] if y < 7 else IR[2]
    # Ashwright's seal on the flank
    MARK = ["..GGG..", ".GkkkH.", "GkmmmkH", "GkkmkkH", "GkkmkkH", ".gkkkH.", "..ggg.."]
    KEY = {"G": GD[3], "H": GD[4], "g": GD[2], "k": IR[0], "m": GD[5]}
    for j, row in enumerate(MARK):
        for i, ch in enumerate(row):
            if ch != ".":
                px[cx - 16 + i, 30 + j] = KEY[ch]
    px[cx - 13, 33] = MG[5 + (f % 2)]
    # drips of molten metal hanging from the lip
    for k, dx in enumerate((-22, 9, 27)):
        ln = 2 + (f + k) % 4
        for y in range(16, 16 + ln):
            px[cx + dx, y] = MG[5] if y < 15 + ln else MG[6]
    return DT.outline_k(img)


def build_crucible():
    frames = [{"ms": 160, "cels": {"Crucible": crucible(f)}} for f in range(4)]
    return 96, 72, ["Crucible"], frames, [("idle", 0, 3)]


def build_hatch():
    a = blank(32, 32); a.alpha_composite(DT.hatch(False), (0, 0))
    b = blank(32, 32); b.alpha_composite(DT.hatch(True), (0, 0))
    frames = [{"ms": 100, "cels": {"Prop": a}}, {"ms": 100, "cels": {"Prop": b}}]
    return 32, 32, ["Prop"], frames, [("hatch", 0, 0), ("hatch_open", 1, 1)]


def build_fx_tiles():
    frames, tags = [], []
    def add(tag, ims):
        a = len(frames)
        for im in ims:
            frames.append({"ms": 100, "cels": {"Tiles": im}})
        tags.append((tag, a, len(frames) - 1))
    add("lava_top", [DT.lava_top(f) for f in range(8)])
    add("lava_body", [DT.lava_body(f) for f in range(4)])
    for k, n in (("belt_l", "L"), ("belt_m", "M"), ("belt_r", "R")):
        add(k, [DT.belt(n, f) for f in range(4)])
    return 16, 16, ["Tiles"], frames, tags


PROPS = {"dp_crucible": build_crucible, "dp_props": build_hatch, "tiles_deep_fx": build_fx_tiles}
