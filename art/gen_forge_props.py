"""Props for the Cold Forge (v17, agent AREA) — called by gen_forge_env.py (build_all). Same kit and palette as the tiles:
cold slate and black iron, soot; warm colours only where fire is (the coals, the furnace seam, the vents, the hearth).
Sheets (bottom-centre anchored in the game): cfa_s 32x32, cfa_m 64x64, cfa_rack 96x80, cfa_bellows 48x80,
cfa_furnace 256x288, cfa_doors 96x112, cfa_coals 176x24, cfa_gate 224x352, cfa_guard 48x128, cfa_ganvil 96x64.
"""
import os, math
import numpy as np
from PIL import Image
from forge_env_lib import *   # noqa

IRON = ("#06080b", "#0e1219", "#18202b", "#252f3e", "#364356", "#4f6079", "#7c8ea8")


# ------------------------------------------------------------------ anvils
def anvil(p, cx, base, s=1.0, lit=0.0, plinth=True, mark=None):
    """horn left, flat face, heel right, a waisted body on a wide foot; a stone plinth under it"""
    X = lambda v: cx + v * s
    Y = lambda v: base - v * s
    if plinth:
        pl = p.rectm(X(-13), Y(6), X(13), base)
        p.fill(pl, "#18202b"); p.fill(p.rectm(X(-13), Y(6), X(13), Y(6) + 1), "#364356"); p.fill(p.rectm(X(-13), base - 1, X(13), base), "#06080b")
        p.fill(p.rectm(X(-13), Y(6), X(-12), base), "#252f3e")
        base0 = Y(6)
    else:
        base0 = base
    Yb = lambda v: base0 - v * s
    body = p.poly([(X(-16), Yb(17)), (X(-6), Yb(19)), (X(13), Yb(19)), (X(15), Yb(18)), (X(15), Yb(14)), (X(10), Yb(13)), (X(6), Yb(10)),
                   (X(5), Yb(5)), (X(10), Yb(2)), (X(11), Yb(0)), (X(-10), Yb(0)), (X(-9), Yb(2)), (X(-4), Yb(5)), (X(-5), Yb(10)), (X(-9), Yb(13)), (X(-13), Yb(15))])
    p.fill(body, "#141a24")
    # roundness / cold rim light from upper-left
    k = np.clip(1.15 - (p.xx - X(-16)) / (31 * s) * 0.5, 0.6, 1.2)
    p.mul(k, body)
    face = p.poly([(X(-16), Yb(17)), (X(-6), Yb(19)), (X(13), Yb(19)), (X(15), Yb(18)), (X(15), Yb(17)), (X(-6), Yb(18)), (X(-15), Yb(16))])
    p.fill(face, "#7c8ea8" if lit < 0.5 else "#dfe4ea")
    p.fill(p.poly([(X(-6), Yb(18)), (X(13), Yb(18)), (X(13), Yb(17)), (X(-6), Yb(17))]), "#364356")
    p.fill(p.rectm(X(-9), Yb(2), X(11), Yb(0)), "#0e1219"); p.fill(p.rectm(X(-9), Yb(2), X(11), Yb(2) + 1), "#2d3849")
    p.fill(p.rectm(X(9), Yb(18), X(12), Yb(16)), "#06080b")    # the hardy hole
    p.edge_dark(body, "#05070a")
    if lit:
        p.eglow(X(2), Yb(18), 18 * s, 6 * s, "#b7c0cb", 0.5 * lit, mask=body)


# ------------------------------------------------------------------ marks (the anvils' signs)
MARKS = {
    "hammer": ["#####", "#####", "..#..", "..#..", "..#..", "..#.."],
    "tongs": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "flame": ["..#..", ".##..", ".###.", "#####", "##.##", ".###."],
    "ox": ["#...#", "#...#", ".###.", "#####", ".###.", "..#.."],
    "crown": ["#.#.#", "#.#.#", "#####", "#####", ".....", "....."],
}
MARK_LIT = {"hammer": "#dfe4ea", "tongs": "#dfe4ea", "flame": "#f7ad4c", "ox": "#c9d0d9", "crown": "#eef1f4"}


def mark_img(m, lit=False):
    p = Cv(32, 32)
    rows = MARKS[m]
    if not lit:
        p.rect(11, 22, 21, 31, "#131822"); p.rect(11, 22, 21, 23, "#364356"); p.rect(11, 30, 21, 31, "#06080b"); p.rect(20, 22, 21, 31, "#0a0d12")
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#": p.px(13 + i, 23 + j + 1, "#4f6079")
    else:
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#": p.px(13 + i, 23 + j + 1, MARK_LIT[m])
    return p.to_image(dither=0)


# ------------------------------------------------------------------ small things
def small_sheet():
    T = {}
    for lit in (0, 1):
        pass
    a0, a1 = Cv(32, 32), Cv(32, 32)
    anvil(a0, 16, 32, 0.62, 0, plinth=True); anvil(a1, 16, 32, 0.62, 1, plinth=True)
    T["anvil_s"] = [a0.to_image(0), a1.to_image(0)]
    for m in MARKS:
        T["mark_" + m] = [mark_img(m), mark_img(m, True)]
    # scrap: broken blades in a heap of soot
    p = Cv(32, 32)
    p.fill(p.ellm(16, 32, 13, 4), "#141213"); p.fill(p.ellm(15, 31.5, 9, 2), "#1d1a1b")
    for i in range(6):
        x = 6 + hh(i, 1, 3) * 20; L = 6 + hh(i, 2, 3) * 8; a = 0.3 + hh(i, 3, 3) * 0.9
        d = -1 if i % 2 else 1
        p.line((x, 30), (x + d * math.cos(a) * L, 30 - math.sin(a) * L), "#415066"); p.line((x + 1, 30), (x + 1 + d * math.cos(a) * L, 30 - math.sin(a) * L), "#18202b")
    T["scrap"] = [p.to_image(0)]
    # bucket (a quench bucket with a rope handle)
    p = Cv(32, 32)
    b = p.poly([(9, 18), (23, 18), (21, 31), (11, 31)]); p.fill(b, "#2a2121")
    for y in (20, 28): p.rect(9 + (y - 18) / 7, y, 23 - (y - 18) / 7, y + 1, "#364356")
    p.rect(9, 18, 23, 19, "#4e3829"); p.edge_dark(b)
    for a in range(0, 181, 12): p.px(16 + 7 * math.cos(math.radians(a)), 18 - 7 * math.sin(math.radians(a)), "#3a2b26")
    T["bucket"] = [p.to_image(0)]
    # ingots stacked in a crossed pile
    p = Cv(32, 32)
    for row, (y, xs) in enumerate(((27, (6, 13, 20)), (22, (9, 16)), (17, (12,)))):
        for x in xs:
            m = p.poly([(x, y + 5), (x + 7, y + 5), (x + 6, y), (x + 1, y)]); p.fill(m, "#18202b"); p.rect(x + 1, y, x + 6, y + 1, "#4f6079"); p.edge_dark(m)
    T["ingots"] = [p.to_image(0)]
    # a stone trough with blades standing in it
    p = Cv(32, 32)
    for i, x in enumerate((8, 12, 17, 21, 25)):
        L = 10 + hh(i, 1, 8) * 8
        p.line((x, 24), (x + (hh(i, 2, 8) - 0.5) * 4, 24 - L), "#4f6079"); p.line((x + 1, 24), (x + 1 + (hh(i, 2, 8) - 0.5) * 4, 24 - L), "#18202b")
    p.rect(3, 23, 29, 32, "#131822"); p.rect(3, 23, 29, 24, "#364356"); p.rect(28, 23, 29, 32, "#06080b")
    T["trough_blades"] = [p.to_image(0)]
    # a heap of failed blades (the Reject Pile): crossed, chipped, some broken short
    p = Cv(32, 32)
    p.fill(p.ellm(16, 33, 15, 7), "#0e1219")
    for i in range(14):
        x = 3 + hh(i, 1, 21) * 26; y = 31 - hh(i, 4, 21) * 6; L = 7 + hh(i, 2, 21) * 10; a = 0.15 + hh(i, 3, 21) * 1.1
        d = -1 if hh(i, 5, 21) < 0.5 else 1
        p.line((x, y), (x + d * math.cos(a) * L, y - math.sin(a) * L), "#4f6079" if i % 3 else "#7c8ea8")
        p.line((x, y + 1), (x + d * math.cos(a) * L, y + 1 - math.sin(a) * L), "#18202b")
        if i % 4 == 0: p.line((x - 2, y), (x + 2, y), "#252f3e")
    T["heap"] = [p.to_image(0)]
    # a floor vent: a grate let into the floor (16 wide)
    p = Cv(32, 32)
    p.rect(9, 29, 23, 32, "#06080b"); p.rect(9, 29, 23, 30, "#252f3e")
    for x in range(10, 23, 3): p.rect(x, 30, x + 1, 32, "#030405")
    T["vent"] = [p.to_image(0)]
    return T


# ------------------------------------------------------------------ medium things (64x64)
def medium_sheet():
    T = {}
    a0, a1 = Cv(64, 64), Cv(64, 64)
    anvil(a0, 32, 64, 1.0, 0); anvil(a1, 32, 64, 1.0, 1)
    T["anvil"] = [a0.to_image(0), a1.to_image(0)]
    # quench tank: a riveted iron tank with black water at the brim
    p = Cv(64, 64)
    m = p.rectm(4, 24, 60, 64); plates(p, m, pw=14, ph=10, seed=3, lit="#252f3e")
    p.rect(2, 22, 62, 26, "#18202b"); p.rect(2, 22, 62, 23, "#4f6079")
    p.rect(6, 24, 58, 25, "#141c22")
    for y in (34, 50): p.rect(4, y, 60, y + 2, "#06080b")
    p.edge_dark(p.rectm(2, 22, 62, 64))
    T["tank"] = [p.to_image(0)]
    # a rack of quenching tongs / hooks
    p = Cv(64, 64)
    p.rect(6, 20, 58, 23, "#18202b"); p.rect(6, 20, 58, 21, "#364356")
    for x in (8, 54): p.rect(x, 20, x + 3, 64, "#0e1219"); p.rect(x, 20, x + 1, 64, "#252f3e")
    for i, x in enumerate(range(14, 52, 6)):
        L = 22 + (i % 3) * 6
        p.line((x, 22), (x - 2, 22 + L), "#2d3849"); p.line((x + 2, 22), (x + 4, 22 + L), "#2d3849"); p.px(x + 1, 22, "#62748f")
    T["tongs_rack"] = [p.to_image(0)]
    # a quench rack: a cradle with blades laid across it, tips in a trough
    p = Cv(64, 64)
    for x in (10, 50): p.rect(x, 36, x + 4, 64, "#0e1219"); p.rect(x, 36, x + 1, 64, "#252f3e")
    p.rect(6, 34, 58, 37, "#18202b"); p.rect(6, 34, 58, 35, "#364356")
    for i in range(6):
        y = 30 - i * 3; p.line((4, y + 6), (60, y), "#4f6079"); p.line((4, y + 7), (60, y + 1), "#131822")
    p.rect(4, 54, 60, 64, "#131822"); p.rect(4, 54, 60, 55, "#364356"); p.rect(6, 55, 58, 56, "#141c22")
    T["quench_rack"] = [p.to_image(0)]
    # an ore/slag cart on a short rail, tipped, frozen slag spilling
    p = Cv(64, 64)
    p.rect(0, 62, 64, 64, "#252f3e")
    cart = p.poly([(10, 34), (54, 30), (50, 56), (14, 58)]); plates(p, cart, pw=12, ph=8, seed=8)
    p.edge_dark(cart)
    for x in (18, 46): p.fill(p.ellm(x, 58, 5, 5), "#0e1219"); p.fill(p.ellm(x, 58, 2, 2), "#364356")
    p.fill(p.poly([(14, 34), (50, 31), (44, 26), (22, 27)]), "#0b0a0b")
    p.px(32, 29, "#3d2419"); p.px(33, 29, "#5a311c")
    T["slag_cart"] = [p.to_image(0)]
    # the ledger desk: a slanted lectern with an open book, an inkwell, a stool
    p = Cv(64, 64)
    p.rect(26, 38, 30, 64, "#141213"); p.rect(16, 60, 40, 64, "#141213")
    top = p.poly([(10, 36), (46, 28), (48, 34), (12, 42)]); p.fill(top, "#272324"); p.edge_dark(top)
    book = p.poly([(16, 34), (42, 28), (43, 31), (17, 37)]); p.fill(book, "#8f9aa8"); p.line((29, 31), (30, 34), "#364356")
    for i in range(4): p.line((19 + i * 1, 35 - i * 0), (27, 33 - i * 0), "#566273")
    p.rect(48, 52, 56, 64, "#1d1a1b"); p.rect(46, 50, 58, 52, "#272324")
    T["ledger_desk"] = [p.to_image(0)]
    # a broken rack: a frame fallen askew, blades spilled
    p = Cv(64, 64)
    p.line((6, 64), (22, 18), "#18202b"); p.line((7, 64), (23, 18), "#0e1219")
    p.line((22, 18), (58, 34), "#252f3e"); p.line((22, 19), (58, 35), "#0e1219")
    for i in range(7):
        x = 26 + i * 4; y = 20 + i * 1.8
        p.line((x, y), (x + 1, y + 16 + (i % 3) * 4), "#4f6079")
    for i in range(5):
        x = 30 + i * 6; p.line((x, 62), (x + 8, 58), "#415066")
    T["broken_rack"] = [p.to_image(0)]
    # a tempering rack: blades hung by the tang over a cold brazier tray
    p = Cv(64, 64)
    blade_rack(p, 6, 58, 8, 44, scale=1.3, seed=5, rows=1, glint="#b7c0cb")
    p.rect(8, 52, 56, 56, "#131822"); p.rect(8, 52, 56, 53, "#364356"); p.rect(14, 56, 16, 64, "#0e1219"); p.rect(48, 56, 50, 64, "#0e1219")
    for i in range(10): p.px(12 + i * 4, 51, "#272324")
    T["temper_rack"] = [p.to_image(0)]
    # the mouth of the soot duct (back layer): an arch of flue brick into black
    p = Cv(64, 64)
    arch = p.poly([(8, 64), (8, 26)] + [(32 + 24 * math.cos(math.radians(a)), 26 - 20 * math.sin(math.radians(a))) for a in range(180, -1, -10)] + [(56, 64)])
    bricks(p, p.rectm(0, 0, 64, 64) & ~arch, bw=10, bh=5, cols=("#131822", "#18202b", "#1e2734"), mortar="#06080b", seed=4, soot=1)
    p.fill(arch, "#030405")
    p.a[:] = p.ellm(32, 36, 34, 34) | arch
    T["flue_mouth"] = [p.to_image(0)]
    # a fallen iron flue pipe
    p = Cv(64, 64)
    m = p.poly([(2, 64), (2, 50), (60, 44), (62, 56), (60, 64)]); plates(p, m, pw=10, ph=6, seed=6)
    for x in (16, 34, 50): p.line((x, 64), (x + 1, 48 - (x - 16) * 0.1), "#06080b")
    p.fill(p.ellm(60, 52, 3, 7), "#030405"); p.edge_dark(m)
    T["pipe"] = [p.to_image(0)]
    return T


# ------------------------------------------------------------------ racks of unfinished blades (96x80)
def rack_sheet():
    T = {}
    for v in range(3):
        p = Cv(96, 80)
        blade_rack(p, 4, 92, 12, 78, scale=2.0, cols=("#0a0d12", "#1e2734", "#252f3e", "#4f6079", "#0e1219"), glint="#7c8ea8", seed=3 + v * 7, fill=0.8 + v * 0.05)
        p.rect(0, 76, 96, 80, "#0e1219"); p.rect(0, 76, 96, 77, "#2d3849")
        T[["rack_a", "rack_b", "rack_c"][v]] = [p.to_image(0)]
    p = Cv(96, 80)
    blade_rack(p, 22, 74, 40, 78, scale=1.4, cols=("#0a0d12", "#1e2734", "#252f3e", "#4f6079", "#0e1219"), glint="#7c8ea8", seed=40, rows=1)
    T["rack_s"] = [p.to_image(0)]
    return T


# ------------------------------------------------------------------ bellows (48x80): 6 frames, emptied -> full
def bellows_sheet():
    out = []
    for f in range(6):
        k = f / 5
        p = Cv(48, 80)
        cx, top, h = 24, 2, 60
        w = 20 + 16 * k
        p.rect(cx - 18, top, cx + 18, top + 4, "#131822"); p.rect(cx - 18, top, cx + 18, top + 1, "#4f6079")
        for dx in (-15, 15): p.rect(cx + dx - 1, top - 2, cx + dx + 2, top + 1, "#0e1219")
        pts = []
        for i in range(21):
            t = i / 20
            hw = (w / 2) * (0.35 + 0.65 * math.sin(math.pi * min(1, 0.12 + t * 0.88)))
            pts.append((cx - hw, top + 4 + t * h))
        shape = p.poly(pts + [(2 * cx - a, b) for a, b in reversed(pts)])
        p.fill(shape, "#1d1a1b")
        for j in range(1, 8):   # pleats
            yy = top + 4 + j * h / 8
            for xx in range(48):
                if shape[min(79, int(yy)), xx]:
                    p.px(xx, yy + 0.8 * math.cos((xx - cx) / max(1, w) * 3.0), "#0b0a0b")
                    p.px(xx, yy - 1 + 0.8 * math.cos((xx - cx) / max(1, w) * 3.0), "#272324")
        left = shape & ~np.roll(shape, 1, axis=1)
        p.mul(np.clip(1.2 - (p.xx - (cx - w / 2)) / max(1, w) * 0.7, 0.5, 1.2), shape)
        p.fill(left, "#3a2b26"); p.edge_dark(shape, "#0b0a0b")
        p.rect(cx - 6, top + 4, cx + 6, top + 9, "#272324")   # the board's iron shoe
        p.fill(p.poly([(cx - 3, top + 4 + h - 1), (cx + 3, top + 4 + h - 1), (cx + 1, 79), (cx - 1, 79)]), "#0e1219")
        p.px(cx - 1, top + 4 + h + 2, "#364356")
        out.append(p.to_image(0))
    return {"breath": out}


# ------------------------------------------------------------------ the Great Furnace (256x288; mouth centre at x 128)
def furnace_sheet():
    p = Cv(256, 288)
    cx, base = 128, 288
    # the wall behind the furnace on its right side (that part of the arena is solid terrain: never show the sky)
    wall = p.rectm(144, 0, 256, 288)
    bricks(p, wall, bw=24, bh=12, cols=("#0a0d12", "#0e1219", "#0c1016"), mortar="#030405", seed=31, soot=1.0)
    p.mul(0.75, wall)
    half, sh_y, ch = 104, 168, 26
    left = [(cx - half, base), (cx - half + 4, sh_y)]
    for a in range(0, 91, 5):     # the dome: an ogive from the shoulder in to the chimney
        t = a / 90
        left.append((cx - half + 4 + (half - 4 - ch) * (1 - math.cos(math.radians(a))) ** 0.9, sh_y - 128 * math.sin(math.radians(a)) ** 1.15))
    left += [(cx - ch, -2)]
    body = p.poly(left + [(2 * cx - x, y) for x, y in reversed(left)])
    plates(p, body, pw=30, ph=20, cols=("#131822", "#18202b", "#151b26"), seam="#06080b", lit="#364356", seed=21)
    # vertical seams bend with the dome; cylindrical shading; a cold rim on the left flank
    for k in (-0.62, -0.25, 0.25, 0.62):
        for y in range(0, 288):
            row = np.where(body[y])[0]
            if len(row) < 8: continue
            x = (row[0] + row[-1]) / 2 + k * (row[-1] - row[0]) / 2
            p.px(x, y, "#05070a", cover=False); p.px(x + 1, y, "#1e2734", cover=False)
    p.mul(1 - np.clip(np.abs(p.xx - cx) / half, 0, 1) ** 2.0 * 0.75, body)
    rim = body & ~np.roll(body, 2, axis=1)
    p.fill(rim, "#4f6079")
    rim1 = body & ~np.roll(body, 1, axis=1)
    p.fill(rim1, "#7c8ea8")
    top = body & ~np.roll(body, 2, axis=0)
    p.fill(top & (p.xx < cx), "#415066")
    p.eglow(cx - 50, 70, 40, 60, "#2d3849", 0.35, mask=body)   # cold light on the dome's shoulder
    edge = body & ~np.roll(body, 1, axis=1)
    p.fill(edge, "#2d3849")
    for y in (40, sh_y - 66, sh_y - 8, sh_y + 52):
        m = p.rectm(0, y, 256, y + 5) & body
        p.fill(m, "#0a0d12"); p.fill(p.rectm(0, y, 256, y + 1) & body, "#415066")
        for x in range(0, 256, 9):
            if body[min(287, y + 2), x]: p.px(x, y + 2, "#415066")
    # the mouth: an arched opening 64 wide, 96 tall, a heavy frame; the throat inside is black (the doors fill it)
    dw, dh = 64, 96
    arch_pts = [(cx - dw / 2, base)] + [(cx + (dw / 2) * math.cos(math.radians(a)), base - dh + dh * 0.3 - dh * 0.3 * math.sin(math.radians(a))) for a in range(180, -1, -10)] + [(cx + dw / 2, base)]
    frame = p.poly([(x + (-8 if x < cx else 8), y - (8 if y < base - 4 else 0)) for x, y in arch_pts])
    p.fill(frame, "#06080b")
    inner = p.poly([(x + (-7 if x < cx else 7), y - (7 if y < base - 4 else 0)) for x, y in arch_pts])
    p.fill(inner & ~p.poly(arch_pts), "#252f3e")
    for i, (x, y) in enumerate(arch_pts[1:-1]):   # voussoirs
        p.line((x, y), (x + (x - cx) * 0.18, y - 8), "#0a0d12")
    mouth = p.poly(arch_pts)
    p.fill(mouth, "#020304")
    p.eglow(cx + 24, base - 40, 30, 60, "#0e1219", 0.6, mask=mouth)   # the throat turns away to the right
    # rivets still holding heat around the mouth (the seal is heat)
    for i, (x, y) in enumerate(arch_pts[1:-1]):
        if i % 2 == 0: p.px(x + (x - cx) * 0.22, y - 10, "#a3531f")
    # the coals' warmth on the furnace's face, low and from the front
    p.eglow(cx - 40, base, 160, 130, "#7c401d", 0.5, power=1.5, mask=body & ~mouth)
    p.eglow(cx - 40, base, 100, 50, "#a3531f", 0.35, power=1.4, mask=body & ~mouth)
    return {"body": [p.to_image(0.35)]}


# ------------------------------------------------------------------ the doors (96x112): shut, opening (6), bar, the open leaf in CT1
def doors_sheet():
    def door(k, hot):
        p = Cv(96, 112)
        cx, base, dw, dh = 48, 112, 64, 96
        arch_pts = [(cx - dw / 2, base)] + [(cx + (dw / 2) * math.cos(math.radians(a)), base - dh + dh * 0.3 - dh * 0.3 * math.sin(math.radians(a))) for a in range(180, -1, -10)] + [(cx + dw / 2, base)]
        mouth = p.poly(arch_pts)
        p.fill(mouth, "#020304")
        # each leaf swings toward us on its outer hinge: it narrows to a lit edge-on slab
        for side in (-1, 1):
            hinge = cx + side * dw / 2
            wcl = (dw / 2) * (1 - 0.86 * k)
            x0, x1 = (hinge, hinge - side * wcl)
            lo, hi = min(x0, x1), max(x0, x1)
            leaf = mouth & p.rectm(lo, 0, hi + 0.5, 112)
            if not leaf.any():
                continue
            plates(p, leaf, pw=16, ph=12, seed=7 + side, cols=("#10151d", "#131822", "#0e1219"), lit="#252f3e")
            if k > 0:   # turned: the face catches the cold draught's light, darker toward the hinge
                p.mul(np.clip(0.6 + 0.7 * k * (1 - np.abs(p.xx - hinge) / max(1, wcl)), 0.4, 1.3), leaf)
            p.fill(leaf & ~np.roll(leaf, side, axis=1), "#364356" if k < 0.95 else "#4f6079")
            for y in range(28, 110, 18):
                for x in (lo + 4, hi - 4):
                    if leaf[y, int(x)]: p.px(x, y, "#4f6079")
        if hot and k == 0:
            p.fill(p.rectm(cx - 1, base - dh + 4, cx + 1, base) & mouth, "#a3531f")
            p.eglow(cx, base - dh * 0.5, 6, dh * 0.6, "#7c401d", 0.9, power=1.4, mask=mouth)
            for i, (x, y) in enumerate(arch_pts[1:-1]):
                if i % 2 == 0: p.px(x, y + 2, "#c96a22")
        return p.to_image(0.2)
    shut = [door(0, True)]
    opening = [door(k, False) for k in (0.0, 0.18, 0.4, 0.62, 0.82, 1.0)]
    p = Cv(96, 112)
    p.rect(4, 104, 92, 110, "#06080b"); p.rect(4, 104, 92, 105, "#364356")
    for x in (8, 86): p.rect(x - 2, 101, x + 3, 112, "#0a0d12")
    bar = [p.to_image(0)]
    p = Cv(96, 112)   # the open leaf from inside the threshold (it stands against the wall)
    leaf = p.poly([(30, 4), (58, 12), (58, 112), (30, 112)])
    plates(p, leaf, pw=14, ph=12, seed=12)
    p.fill(leaf & ~np.roll(leaf, -1, axis=1), "#62748f"); p.edge_dark(leaf)
    p.rect(24, 0, 30, 112, "#0a0d12")
    leafim = [p.to_image(0)]
    return {"shut": shut, "open": opening, "bar": bar, "leaf": leafim}


# ------------------------------------------------------------------ the coal bed (176x24)
def coals_sheet():
    out = []
    for f in range(5):
        dead = f == 4
        p = Cv(176, 24)
        ring = p.poly([(2, 24), (8, 15), (168, 15), (174, 24)])
        p.fill(ring, "#0e1219"); p.rect(8, 15, 168, 16, "#252f3e")
        for i in range(120):
            x = 12 + hh(i, 1, 40) * 152; y = 13 + hh(i, 2, 40) * 6
            if dead:
                c = ["#0b0a0b", "#141213", "#1d1a1b", "#272324"][int(hh(i, 3, 40) * 4)]
            else:
                v = (hh(i, 3, 40) + 0.35 * math.sin(f * 1.6 + i)) % 1
                c = ["#3d2419", "#7c401d", "#a3531f", "#c96a22", "#e88a30", "#f7ad4c", "#ffd27e"][int(v * 7)]
            p.fill(p.ellm(x, y, 2.4, 1.5), c)
        if not dead:
            p.eglow(88, 16, 86, 9, "#e88a30", 0.25, power=1.2, mask=p.a)
        out.append(p.to_image(0.2))
    return {"loop": out[:4], "dead": out[4:]}


# ------------------------------------------------------------------ the Last Gate (224x352) and its guardians (48x128)
def gate_sheet():
    p = Cv(224, 352)
    gx, gy, gw, gh = 112, 352, 150, 316

    def arch_poly(w, h, pad=0):
        return [(gx - w / 2, gy)] + [(gx + (w / 2) * math.cos(math.radians(a)), gy - h + h * 0.34 - h * 0.34 * math.sin(math.radians(a)) - pad * math.sin(math.radians(a))) for a in range(180, -1, -5)] + [(gx + w / 2, gy)]
    but = p.poly([(x + (-34 if x < gx else 34), y) for x, y in arch_poly(gw, gh, 22)])
    bricks(p, but, bw=20, bh=10, cols=("#62748f", "#6b7686", "#566273"), mortar="#364356", seed=91, lip=1.08)
    mid = p.poly([(x + (-16 if x < gx else 16), y) for x, y in arch_poly(gw, gh, 10)])
    p.fill(mid, "#4f6079")
    p.fill(mid & ~np.roll(mid, 2, axis=1), "#8f9aa8")
    arch = p.poly(arch_poly(gw, gh))
    p.fill(arch, "#364356")
    for x in range(int(gx - gw / 2), int(gx + gw / 2), 12):   # tall panels
        p.fill(p.rectm(x, gy - gh, x + 1, gy) & arch, "#252f3e"); p.fill(p.rectm(x + 1, gy - gh, x + 2, gy) & arch, "#4f6079")
    for y in range(int(gy - gh + 60), gy, 46):              # bands, studded
        p.fill(p.rectm(0, y, 224, y + 5) & arch, "#2d3849"); p.fill(p.rectm(0, y, 224, y + 1) & arch, "#6b7686")
        for x in range(int(gx - gw / 2) + 4, int(gx + gw / 2), 8):
            if arch[y + 3, x]: p.px(x, y + 3, "#8f9aa8")
    p.mul(np.clip(0.8 + 0.35 * (1 - np.abs(p.xx - gx) / (gw / 2)), 0.6, 1.15), arch)
    for x in (gx - gw / 4, gx + gw / 4):
        p.fill(p.rectm(x, gy - gh, x + 2, gy) & arch, "#2d3849")
    p.fill(p.rectm(gx - 1, gy - gh + 16, gx + 1, gy) & arch, "#252f3e")
    # the keeper's grate-crown, writ huge at the apex
    sc = (gx, gy - gh - 4)
    for a in range(0, 360, 4):
        p.px(sc[0] + 13 * math.cos(math.radians(a)), sc[1] + 13 * math.sin(math.radians(a)), "#8f9aa8")
    for a in range(200, 341, 20):
        x = sc[0] + 13 * math.cos(math.radians(a)); y = sc[1] + 13 * math.sin(math.radians(a))
        p.line((x, y), (x + (x - sc[0]) * 0.6, y + (y - sc[1]) * 0.7), "#8f9aa8")
    # pale light raking from above, ash caught on every ledge
    p.add_light(np.clip(1 - p.yy / 352, 0, 1) * 0.5, "#b7c0cb", 0.35, mask=p.a)
    for i in range(160):
        x, y = hh(i, 1, 93) * 224, hh(i, 2, 93) * 352
        if p.a[int(y), int(x)] and hh(i, 3, 93) < 0.6: p.px(x, y, "#c9d0d9")
    gate = [p.to_image(0.4)]
    g = Cv(48, 128)
    C1, C2, C3, HI = "#4f6079", "#566273", "#62748f", "#a5afbc"
    g.fill(g.poly([(10, 128), (14, 92), (16, 60), (18, 44), (30, 44), (32, 60), (34, 92), (38, 128)]), C2)   # the long cloak
    g.fill(g.poly([(16, 50), (12, 64), (14, 70), (20, 58)]), C1); g.fill(g.poly([(32, 50), (36, 64), (34, 70), (28, 58)]), C1)   # shoulders
    g.fill(g.poly([(19, 46), (21, 30), (25, 26), (29, 30), (29, 46)]), C1)    # the veiled, bowed head
    g.fill(g.poly([(22, 28), (25, 22), (27, 24), (27, 30)]), C1)             # its crown of bars
    for x in (22, 24, 26): g.line((x, 26), (x - 1, 21), C3)
    for y in range(60, 126, 9): g.line((14 + (y - 60) * 0.06, y), (34 - (y - 60) * 0.06, y + 2), C1)   # fold lines
    g.rect(23, 70, 25, 126, "#8f9aa8"); g.rect(23, 70, 24, 126, HI); g.rect(18, 68, 30, 70, "#8f9aa8")   # the blade, point down
    g.rect(22, 62, 26, 68, C1)                                                   # hands on the pommel
    g.rect(8, 122, 40, 128, "#566273"); g.rect(8, 122, 40, 123, HI)             # the plinth
    g.fill(g.a & ~np.roll(g.a, 1, axis=1), HI)
    g.edge_dark(g.a, "#364356")
    return {"shut": gate}, {"idle": [g.to_image(0.3)]}


def great_anvil_sheet():
    p = Cv(96, 64)
    p.rect(14, 48, 82, 64, "#18202b"); p.rect(14, 48, 82, 49, "#364356"); p.rect(10, 56, 86, 64, "#131822"); p.rect(10, 56, 86, 57, "#2d3849")
    anvil(p, 48, 48, 2.0, 0, plinth=False)
    p.eglow(40, 14, 30, 8, "#4f6079", 0.25, mask=p.a)
    return {"idle": [p.to_image(0.2)]}


def build_all(build_sheet, prev):
    sheets = [("cfa_s", small_sheet(), 32, 32), ("cfa_m", medium_sheet(), 64, 64), ("cfa_rack", rack_sheet(), 96, 80),
              ("cfa_bellows", bellows_sheet(), 48, 80), ("cfa_furnace", furnace_sheet(), 256, 288), ("cfa_doors", doors_sheet(), 96, 112),
              ("cfa_coals", coals_sheet(), 176, 24), ("cfa_ganvil", great_anvil_sheet(), 96, 64)]
    gt, gd = gate_sheet()
    sheets += [("cfa_gate", gt, 224, 352), ("cfa_guard", gd, 48, 128)]
    for name, T, w, h in sheets:
        build_sheet(name, list(T.items()), w, h, ms=160 if name == "cfa_coals" else 100)
        # preview: every frame on a mid-grey card, 2x
        ims = [im for tag, l in T.items() for im in l]
        cols = max(1, min(len(ims), 1024 // (w * 2)))
        rows = (len(ims) + cols - 1) // cols
        card = Image.new("RGBA", (cols * w * 2, rows * h * 2), (52, 54, 62, 255))
        for i, im in enumerate(ims):
            card.alpha_composite(im.resize((w * 2, h * 2), Image.NEAREST), ((i % cols) * w * 2, (i // cols) * h * 2))
        card.save(os.path.join(prev, f"forge_{name}.png"))
