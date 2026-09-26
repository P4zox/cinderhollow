"""Props for THE CRIMSON MANOR (part 2: art pieces and the blood veil). Each builder returns (w,h,layers,frames,tags).

cm_portrait  32x40  a b c d e (1 each)  tear(6)  torn(1)
             painted portraits in ornate tarnished-gilt frames. EYES: in every portrait the two eyes are dark sockets
             at exactly (13,15) and (18,15) -- the engine overlays glowing red pupils there that follow the player.
             a = the Countess (young noblewoman, crimson high-collared gown, black hair)   b = the late Count (stern,
             grey-bearded, in black)   c = a pale child in white lace   d = a hunter in black leather, silver crest
             e = a veiled woman in mourning.   tear = the canvas splits open diagonally from inside, a pale clawed
             hand pushes through, the canvas hangs in shreds (subject-neutral dark canvas).  torn = empty frame, shreds.
cm_bloodveil 32x64  loop(6)  a column of flowing blood (Ember-Dash barrier); tiles vertically (rows join seamlessly)
cm_statue    32x64  lady(1) gargoyle(1)
cm_fountain  64x48  loop(4)  black-marble fountain with a weeping angel, blood trickling from its basins
"""
import math
from PIL import Image, ImageDraw
from envlib import K, T, h01, clamp, blank, ramp, vnoise
from crimson_env_lib import (ST, MB, SV, BL, VV, DM, WD, IR, GL, WX, FL, SK, GR, GS, Spr, outline)
from crimson_env_props import poly, turned

EYES = ((13, 15), (18, 15))
PALE = ramp("2a1a22", "5a3c46", "8a6468", "b89490", "dcc0b4")
CHILD = ramp("262030", "4a4052", "6e6478", "948a9c", "b6aebc")
SHADE = ramp("1c1216", "3a282a", "5c4240", "7e6056", "9e7e6c")
VEILD = ramp("140e14", "281e26", "42343c", "5e4c52", "7a666a")
HAIR = ramp("08060a", "120e16", "1e1824", "2e2638", "44385a")          # black hair, violet sheen
GREY = ramp("2a282c", "484448", "6a6468", "8e888a", "b4aeac")          # grey hair / beard
LACE = ramp("2e2a34", "4a4652", "6a6672", "8e8a94", "b0acb2")          # white lace (painted, dim)
LEATH = ramp("0a0808", "141011", "1e1819", "2a2223", "3a3030")         # black leather
VOID = (12, 6, 10, 255)
FG = ramp("17110c", "2a2017", "3f3222", "54452f", "6c5a3c", "877148", "a08a5c")   # tarnished gilt (frames)


# =========================================================================== portrait parts
def canvas_bg(s, tone):
    """Dark varnished oil ground with a soft lighter glow behind the head (x 5..26, y 5..34)."""
    R = {"warm": ramp("100a0a", "180f0e", "221612", "2c1d17"),
         "olive": ramp("0c0c0a", "14130f", "1c1a14", "26231a"),
         "violet": ramp("0c0910", "130e18", "1b1422", "241a2c"),
         "slate": ramp("090a0e", "0f1116", "161920", "1f222b"),
         "crimson": ramp("120709", "1c0a0e", "280e13", "341318")}[tone]
    for y in range(5, 35):
        for x in range(5, 27):
            d = math.hypot((x + .5 - 15.5) / 11, (y + .5 - 13) / 13)
            v = 0.85 - 0.75 * d
            i = int(clamp(v) * (len(R) - 1) + (0.5 if (x + y) % 2 else 0.25))
            s.set(x, y, R[max(0, min(len(R) - 1, i))])


def face(s, SKN, lips=None, child=False, brow=None, veil=False):
    rx, ry, cx, cy = 4.3, 5.7, 16.0, 15.3
    for y in range(9, 22):
        for x in range(11, 21):
            v = (y + .5 - cy) / ry
            rxe = rx * (1 - max(0.0, v - 0.25) ** 2 * (0.75 if not child else 0.45))
            u = (x + .5 - cx) / rxe
            if u * u + v * v > 1.0:
                continue
            l = 0.72 - 0.38 * u - 0.12 * max(0.0, v)
            if v < -0.75:
                l -= 0.1
            s.set(x, y, SKN[int(clamp(l) * (len(SKN) - 1) + 0.5)])
    # brows, lids, sockets (sockets are EXACTLY the engine's eye points)
    bc = brow or SKN[1]
    for (x, y) in ((12, 13), (13, 13), (14, 13), (17, 13), (18, 13), (19, 13)):
        s.set(x, y, bc)
    if not child:
        s.set(12, 14, SKN[2]); s.set(19, 14, SKN[1])
    s.set(13, 14, SKN[1]); s.set(18, 14, SKN[1])
    for (x, y) in EYES:
        s.set(x, y, SKN[0])
    s.set(14, 15, SKN[2]); s.set(17, 15, SKN[2])
    # nose + mouth
    s.set(16, 16, SKN[2]); s.set(16, 17, SKN[1]); s.set(15, 17, SKN[3])
    s.set(15, 18, SKN[2]); s.set(16, 18, SKN[2])
    if lips:
        s.set(15, 19, lips[1]); s.set(16, 19, lips[0]); s.set(14, 19, lips[1]); s.set(17, 19, lips[0])
    else:
        s.set(15, 19, SKN[1]); s.set(16, 19, SKN[1])
    s.set(15, 20, SKN[3])
    # neck
    for y in range(21, 24):
        for x in range(14, 18):
            s.set(x, y, SKN[1] if y == 21 or x == 17 else SKN[2])


def frame(s):
    """Ornate tarnished-gilt frame: bevelled moulding with a bead row, corner cartouches and a top crest."""
    W_, H_ = 32, 40
    for y in range(H_):
        for x in range(W_):
            d = min(x, y, W_ - 1 - x, H_ - 1 - y)
            if d > 4:
                continue
            lit_side = (x < 16 and x <= y) or (y < 20 and y <= x and y < W_ - 1 - x) or (x < W_ - 1 - x and y <= x)
            top_left = (min(x, y) == d)
            if d == 0:
                c = K
            elif d == 1:
                c = FG[5] if top_left else FG[2]
            elif d == 2:
                c = FG[4] if top_left else FG[3]
                along = y if min(x, W_ - 1 - x) == d else x
                if along % 3 == 0:
                    c = FG[5] if top_left else FG[4]                  # bead row
            elif d == 3:
                c = FG[2] if top_left else FG[1]
            else:
                c = FG[0] if top_left else K                        # inner lip / shadow onto the canvas
            s.set(x, y, c)
    # corner cartouches: small raised rosettes
    for (cx, cy) in ((3, 3), (28, 3), (3, 36), (28, 36)):
        for (dx, dy, c) in ((0, 0, FG[6]), (1, 0, FG[4]), (0, 1, FG[4]), (1, 1, FG[2]), (-1, 0, FG[4]), (0, -1, FG[5]),
                            (-1, -1, FG[5]), (2, 1, FG[1]), (1, 2, FG[1])):
            s.set(cx + dx, cy + dy, c)
    # top crest: a small shell over the moulding
    for (dx, dy, c) in ((0, 0, FG[6]), (-1, 1, FG[5]), (0, 1, FG[5]), (1, 1, FG[4]), (-2, 2, FG[4]), (-1, 2, FG[5]),
                        (0, 2, FG[4]), (1, 2, FG[3]), (2, 2, FG[3]), (-2, 3, FG[3]), (2, 3, FG[2]), (-1, 3, FG[4]),
                        (0, 3, FG[3]), (1, 3, FG[3]), (-3, 3, FG[2]), (3, 3, FG[1])):
        s.set(15 + dx, 1 + dy, c)
        s.set(16 + dx, 1 + dy, c) if dx >= 0 else None
    # bottom plaque
    for x in range(13, 19):
        s.set(x, 37, FG[5] if x < 16 else FG[3])
        s.set(x, 38, FG[3] if x < 16 else FG[1])


def portrait_a():
    """The Countess: black hair swept up, pale, red lips, a crimson high standing collar fanning behind her head."""
    s = Spr(32, 40)
    canvas_bg(s, "crimson")
    RED = VV
    # the standing collar: two lace-edged crimson fans rising behind the head
    for sg in (-1, 1):
        pts = [(16 + sg * 3, 22), (16 + sg * 11, 7), (16 + sg * 12, 12), (16 + sg * 9, 23)]
        poly(s, pts, lambda x, y, sg=sg: RED[3] if (x + y) % 3 else RED[4] if sg < 0 else RED[2])
        for i in range(12):
            t = i / 11
            x = 16 + sg * (11 - 0.5 * t) + (0 if sg > 0 else 0)
            s.set(16 + sg * (11 + int(t)), 7 + int(t * 4), LACE[2] if sg < 0 else LACE[1])
    for sg in (-1, 1):
        s.line(16 + sg * 11, 7, 16 + sg * 4, 21, RED[5] if sg < 0 else RED[2])
    # gown: crimson velvet, shoulders + bodice with a pale V
    poly(s, [(6, 35), (8, 25), (12, 22), (20, 22), (24, 25), (26, 35)],
         lambda x, y: RED[4] if x < 12 else RED[3] if x < 20 else RED[2])
    poly(s, [(13, 23), (19, 23), (16, 29)], lambda x, y: PALE[3] if x < 16 else PALE[2])
    for x in range(8, 25):                                                # velvet highlight on the shoulders
        if s.get(x, 24) in (RED[4], RED[3]) and x < 14:
            s.set(x, 24, RED[5])
    s.line(12, 22, 16, 30, RED[1]); s.line(20, 22, 16, 30, RED[1])
    face(s, PALE, lips=(BL[4], BL[5]), brow=HAIR[1])
    # choker with a blood-red gem
    for x in range(14, 18):
        s.set(x, 22, HAIR[1])
    s.set(15, 22, BL[6]); s.set(16, 22, BL[5])
    # hair: black, a high swept crown, heavy locks framing the face
    poly(s, [(10, 12), (10, 7), (13, 5), (18, 5), (21, 7), (22, 12), (21, 19), (20, 12), (17, 10), (14, 10),
             (12, 12), (12, 19), (10, 19)], lambda x, y: HAIR[2] if x < 16 else HAIR[1])
    for (x, y) in ((12, 7), (13, 6), (14, 6), (11, 9), (11, 10), (15, 6), (12, 8)):
        s.set(x, y, HAIR[4])
    for (x, y) in ((16, 6), (17, 7), (18, 8), (19, 9)):
        s.set(x, y, HAIR[3])
    for y in range(11, 20):
        s.set(11, y, HAIR[3] if y % 3 else HAIR[2])
    frame(s)
    return s.img


def portrait_b():
    """The late Count: receding grey hair, heavy brow, a grey beard to the chest, black coat, silver chain of office."""
    s = Spr(32, 40)
    canvas_bg(s, "olive")
    # black coat with an upturned collar
    poly(s, [(5, 35), (7, 25), (12, 21), (20, 21), (25, 25), (27, 35)],
         lambda x, y: LEATH[3] if x < 12 else LEATH[2] if x < 21 else LEATH[1])
    poly(s, [(9, 24), (11, 17), (14, 21)], lambda x, y: LEATH[4])
    poly(s, [(23, 24), (21, 17), (18, 21)], lambda x, y: LEATH[2])
    face(s, PALE, brow=GREY[1])
    s.set(12, 14, PALE[3]); s.set(19, 14, PALE[2])
    s.set(15, 13, PALE[2]); s.set(16, 13, PALE[2])
    s.set(14, 13, GREY[0]); s.set(17, 13, GREY[0])                        # brows knitted into a scowl
    # beard + moustache (grey), pointed below the chin
    poly(s, [(12, 17), (14, 18), (18, 18), (20, 17), (20, 21), (18, 25), (16, 28), (14, 25), (12, 21)],
         lambda x, y: GREY[3] if x < 15 else GREY[2] if x < 18 else GREY[1])
    for (x, y) in ((13, 20), (14, 22), (15, 24), (13, 22)):
        s.set(x, y, GREY[4])
    for (x, y) in ((17, 21), (18, 22), (16, 25)):
        s.set(x, y, GREY[0])
    s.set(15, 19, PALE[0]); s.set(16, 19, PALE[0])                        # the mouth, a hard line in the beard
    for (x, y) in ((14, 18), (15, 18), (16, 18), (17, 18)):
        s.set(x, y, GREY[3] if x < 16 else GREY[2])
    # receding hair at the temples, swept back
    for (x, y, c) in ((11, 11, GREY[2]), (11, 12, GREY[2]), (11, 13, GREY[1]), (12, 10, GREY[3]), (11, 10, GREY[2]),
                      (20, 11, GREY[1]), (20, 12, GREY[1]), (20, 13, GREY[0]), (19, 10, GREY[1]), (20, 10, GREY[1]),
                      (11, 14, GREY[1]), (20, 14, GREY[0]), (13, 9, GREY[3]), (18, 9, GREY[2])):
        s.set(x, y, c)
    # chain of office: silver links across the shoulders, a medallion
    for i in range(15):
        t = i / 14
        x = int(round(8 + t * 16))
        y = int(round(27 + 3.5 * math.sin(t * math.pi)))
        s.set(x, y, SV[4] if i % 2 else SV[2])
    for (dx, dy, c) in ((0, 0, SV[5]), (1, 0, SV[3]), (0, 1, SV[3]), (1, 1, SV[2]), (0, 2, BL[4]), (1, 2, SV[1])):
        s.set(16 + dx - 1, 31 + dy, c)
    frame(s)
    return s.img


def portrait_c():
    """A pale child in white lace: ash-blond ringlets, a huge ruffled collar, a black ribbon."""
    s = Spr(32, 40)
    canvas_bg(s, "violet")
    # lace dress
    poly(s, [(7, 35), (9, 27), (12, 24), (20, 24), (23, 27), (25, 35)],
         lambda x, y: LACE[3] if x < 13 else LACE[2] if x < 20 else LACE[1])
    for y in range(27, 35, 3):                                             # lace tiers
        for x in range(8, 25):
            if s.get(x, y) in LACE and (x + y) % 2 == 0:
                s.set(x, y, LACE[4] if x < 14 else LACE[2])
    face(s, CHILD, child=True, brow=CHILD[2])
    s.set(15, 19, CHILD[1]); s.set(16, 19, CHILD[1])
    # ruffled collar: a scalloped ring of lace under the chin
    for x in range(9, 23):
        for y in range(21, 25):
            scal = (x % 3 == 0 and y == 24)
            if y == 21 and not (11 <= x <= 20):
                continue
            c = LACE[4] if x < 14 else LACE[3] if x < 19 else LACE[2]
            if y == 24:
                c = LACE[1] if scal else LACE[2]
            if (x + y) % 3 == 0 and y in (22, 23):
                c = LACE[1]
            s.set(x, y, c)
    for (x, y, c) in ((15, 24, HAIR[1]), (16, 24, HAIR[1]), (14, 25, HAIR[2]), (17, 25, HAIR[1]), (15, 25, HAIR[0]),
                      (16, 25, HAIR[0]), (14, 26, HAIR[1]), (17, 26, HAIR[0])):
        s.set(x, y, c)                                                     # black ribbon bow
    # ash-blond ringlets
    ASH = ramp("3a3230", "5c524a", "80746a", "a2968a")
    poly(s, [(10, 14), (10, 9), (12, 6), (16, 5), (20, 6), (22, 9), (22, 14), (20, 11), (16, 9), (12, 11)],
         lambda x, y: ASH[2] if x < 16 else ASH[1])
    for (cx, top) in ((10, 12), (21, 12), (11, 16), (20, 16)):
        for y in range(top, top + 6):
            s.set(cx, y, ASH[2] if (y - top) % 2 == 0 else ASH[1])
            s.set(cx + (1 if cx < 16 else -1), y, ASH[1] if (y - top) % 2 == 0 else ASH[0])
    for (x, y) in ((13, 7), (14, 6), (12, 8), (15, 6)):
        s.set(x, y, ASH[3])
    frame(s)
    return s.img


def portrait_d():
    """A hunter in black leather: wide-brimmed hat, the face shadowed, a scarf over mouth and nose, silver crest."""
    s = Spr(32, 40)
    canvas_bg(s, "slate")
    # coat + short cape over the shoulders
    poly(s, [(5, 35), (6, 26), (11, 22), (21, 22), (26, 26), (27, 35)],
         lambda x, y: LEATH[3] if x < 11 else LEATH[2] if x < 21 else LEATH[1])
    poly(s, [(6, 28), (9, 23), (16, 22), (23, 23), (26, 28), (22, 30), (16, 29), (10, 30)],
         lambda x, y: LEATH[4] if x < 13 else LEATH[3] if x < 20 else LEATH[2])
    for x in range(8, 25):
        s.set(x, 30 if 10 <= x <= 22 else 29, LEATH[1])
    s.line(10, 30, 20, 35, LEATH[4])                                       # bandolier strap
    face(s, SHADE, brow=SHADE[0])
    # scarf / mask over the lower face
    poly(s, [(11, 17), (21, 17), (21, 23), (18, 25), (13, 25), (11, 22)],
         lambda x, y: LEATH[3] if x < 15 else LEATH[2])
    for (x, y) in ((12, 19), (13, 21), (14, 23), (18, 19), (19, 21)):
        s.set(x, y, LEATH[1])
    for x in range(12, 21):
        s.set(x, 17, LEATH[4] if x < 16 else LEATH[3])
    # wide-brimmed hat throwing the forehead into shadow
    for x in range(12, 20):
        s.set(x, 12, SHADE[0]); s.set(x, 13, SHADE[1] if x not in (13, 14, 17, 18, 19) else SHADE[0])
    poly(s, [(11, 11), (12, 5), (14, 4), (19, 4), (21, 6), (21, 11)],
         lambda x, y: LEATH[3] if x < 15 else LEATH[2])
    for x in range(12, 21):
        s.set(x, 9, LEATH[1])                                              # hat band
    for x in range(6, 27):
        y = 11 if x < 22 else 10
        s.set(x, y, LEATH[4] if x < 16 else LEATH[3])
        s.set(x, y + 1 if x < 11 or x > 20 else y, LEATH[2] if x < 11 or x > 20 else s.get(x, y))
    s.set(5, 12, LEATH[3]); s.set(27, 10, LEATH[2])
    for x in range(11, 21):
        s.set(x, 12, LEATH[1])                                             # under-brim shadow
    # silver crest brooch on the chest
    for (dx, dy, c) in ((0, 0, SV[5]), (1, 0, SV[4]), (-1, 1, SV[4]), (0, 1, SV[3]), (1, 1, SV[3]), (2, 1, SV[2]),
                        (0, 2, SV[3]), (1, 2, SV[2]), (0, 3, SV[2]), (1, 3, SV[1])):
        s.set(19 + dx, 26 + dy, c)
    frame(s)
    return s.img


def portrait_e():
    """A veiled woman in mourning: black lace veil over head and face, a black gown, a single pale lily."""
    s = Spr(32, 40)
    canvas_bg(s, "violet")
    poly(s, [(6, 35), (8, 26), (12, 22), (20, 22), (24, 26), (26, 35)],
         lambda x, y: LEATH[2] if x < 12 else LEATH[1])
    face(s, VEILD, brow=VEILD[1])
    s.set(15, 19, VEILD[1]); s.set(16, 19, VEILD[0])
    # the veil: drapes from a crown over the head down past the shoulders; sheer over the face (lace dots)
    VL = ramp("060408", "0e0a12", "181220", "241c2e")
    poly(s, [(15, 5), (19, 6), (22, 9), (23, 16), (24, 24), (26, 34), (22, 33), (21, 22), (20, 17), (20, 11),
             (16, 9), (12, 11), (11, 17), (10, 22), (9, 33), (5, 34), (7, 24), (8, 16), (9, 9), (12, 6)],
         lambda x, y: VL[2] if x < 13 else VL[1] if x < 20 else VL[0])
    for (x0, y0, y1) in ((9, 10, 32), (22, 11, 32), (10, 12, 26), (21, 14, 28)):
        for y in range(y0, y1, 2):
            s.set(x0, y, VL[3] if x0 < 16 else VL[1])
    for y in range(12, 22):                                                # sheer lace falling over the face
        for x in (11, 20):
            if s.get(x, y) in VEILD:
                s.set(x, y, VL[2])
    img = s.img
    pp = img.load()
    vl = set(VL[:3])
    edge = []
    for y in range(5, 35):
        for x in range(5, 27):
            if pp[x, y] in vl and (pp[x - 1, y] not in vl and pp[x - 1, y] not in VEILD):
                edge.append((x, y))
    for (x, y) in edge:
        pp[x, y] = VL[3]
    for x in range(12, 20):                                                # scalloped veil hem across the brow
        s.set(x, 11 if x % 2 else 12, VL[3])
    for (x, y) in ((13, 6), (14, 6), (15, 5), (16, 5), (17, 6)):
        s.set(x, y, VL[3])                                                 # jet crown / comb catching light
    # a white lily held at the breast
    for (x, y, c) in ((17, 27, LACE[4]), (18, 26, LACE[4]), (19, 26, LACE[3]), (18, 27, LACE[3]), (19, 27, LACE[2]),
                      (20, 27, LACE[2]), (18, 28, LACE[2]), (19, 28, LACE[1]), (17, 26, LACE[3]), (16, 29, IR[4]),
                      (15, 30, IR[4]), (14, 31, IR[3]), (13, 32, IR[3]), (20, 26, LACE[1])):
        s.set(x, y, c)
    frame(s)
    return s.img


# --------------------------------------------------------------------------- the tear
CANV = ramp("0e0909", "150d0c", "1c1210", "241713", "2e1d17")          # dark neutral canvas + lit canvas backs


def neutral_canvas(s):
    for y in range(5, 35):
        for x in range(5, 27):
            d = math.hypot((x + .5 - 15.5) / 11, (y + .5 - 18) / 15)
            v = 0.6 - 0.45 * d
            i = int(clamp(v) * 3 + (0.5 if (x * 3 + y) % 4 else 0.2))
            s.set(x, y, CANV[max(0, min(3, i))])


def slit_pts(t):
    """Along the tear diagonal (upper-right -> lower-left) at t in 0..1."""
    return 22 - 13 * t, 9 + 22 * t


def tear_frame(k):
    s = Spr(32, 40)
    neutral_canvas(s)
    # opening width along the slit per frame, as a function of t
    openw = [0.0, 0.8, 2.6, 4.6, 5.2, 6.4][k]
    if k == 0:
        # the canvas bulges: a pale stretched ridge along the diagonal, creases fanning from it
        for i in range(24):
            t = 0.2 + 0.6 * i / 23
            x, y = slit_pts(t)
            s.set(x, y, CANV[4]); s.set(x - 1, y, CANV[3])
        for (x0, y0, x1, y1) in ((17, 16, 21, 21), (14, 22, 11, 18), (16, 19, 20, 15)):
            s.line(x0, y0, x1, y1, CANV[3])
    else:
        # the gap: dark void, frayed lit edges (canvas backs), flaps peeling outward as it widens
        for i in range(60):
            t = i / 59
            w = openw * math.sin(t * math.pi) ** 0.8
            if k >= 5:
                w = openw * (0.55 + 0.45 * math.sin(t * math.pi))
            x, y = slit_pts(t)
            for j in range(-int(w) - 1, int(w) + 2):
                # perpendicular to the slit direction (-13, 22): normal ~ (22, 13)/|..|
                px_ = x + j * 0.86
                py_ = y + j * 0.5
                if abs(j) <= w:
                    s.set(px_, py_, VOID)
            for sg in (-1, 1):
                ex, ey = x + sg * (w + 1) * 0.86, y + sg * (w + 1) * 0.5
                if 5 <= ex <= 26 and 5 <= ey <= 34:
                    s.set(ex, ey, CANV[4] if h01(i, sg, 3) < 0.6 else CANV[3])
        if k >= 3:
            # peeled flaps (their pale backs) curling from the gap's edges
            for (fx, fy, dx, dy) in ((17, 14, 4, -2), (12, 25, -4, 3), (19, 18, 5, 1), (10, 21, -4, -1)):
                for i in range(4 + (k - 3)):
                    s.set(fx + dx * i / 4, fy + dy * i / 4, CANV[4] if i % 2 else CANV[3])
    if k in (2, 3, 4):
        hand(s, k)
    if k == 5:
        shreds(s)
    frame(s)
    return s.img


def hand(s, k):
    """A pale gaunt clawed hand pushing out through the tear (k=2 claw tips, 3 hand, 4 reaching further)."""
    HN = ramp("3c3038", "6a5a62", "9a8a8e", "c4b6b4", "e2d8d0")
    CLAW = (26, 18, 22, 255)
    if k == 2:
        # three long pale fingertips hooking through the slit, black claws curling over its lip
        for (x, y) in ((18, 16), (15, 20), (12, 24)):
            s.set(x, y, HN[2]); s.set(x + 1, y - 1, HN[3]); s.set(x + 2, y - 1, HN[4])
            s.set(x + 3, y - 1, CLAW); s.set(x + 4, y, CLAW)
            s.set(x, y + 1, K); s.set(x + 1, y, K); s.set(x + 2, y, K); s.set(x + 3, y, K)
        return
    ox, oy = (0, 0) if k == 3 else (2, -2)
    # wrist rising out of the gap, a gaunt back of hand, four long fingers splayed up-right with black claws
    for i in range(7):
        x, y = 13 + i * 0.7 + ox * 0.3, 27 - i * 1.1 + oy * 0.3
        for j in range(-1, 2):
            s.set(x + j, y, HN[3] if j < 0 else HN[2] if j == 0 else HN[1])
    poly(s, [(12 + ox, 20 + oy), (15 + ox, 16 + oy), (19 + ox, 17 + oy), (19 + ox, 21 + oy), (15 + ox, 23 + oy)],
         lambda x, y: HN[3] if x < 16 + ox else HN[2])
    fingers = [((15, 16), (15, 10)), ((17, 16), (19, 10)), ((19, 17), (23, 13)), ((19, 19), (24, 18)),
               ((12, 20), (9, 16))]
    for n, ((x0, y0), (x1, y1)) in enumerate(fingers):
        x0 += ox; x1 += ox; y0 += oy; y1 += oy
        if k == 4 and n < 4:
            x1 += 1; y1 -= 1
        steps = int(max(abs(x1 - x0), abs(y1 - y0)))
        for i in range(steps + 1):
            t = i / max(1, steps)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            s.set(x, y, HN[4] if i < 2 else HN[3] if i % 2 else HN[2])
            if i in (steps // 2,):
                s.set(x + 1, y, HN[1])                                     # knuckle
        s.set(x1 + (1 if x1 >= x0 else -1), y1 - 1, CLAW)
        s.set(x1 + (2 if x1 >= x0 else -2), y1 - 1, CLAW)
    # outline the hand so it pops against the void
    img = s.img
    px = img.load()
    hn = set(HN)
    hits = []
    for y in range(5, 35):
        for x in range(5, 27):
            if px[x, y] in hn or px[x, y] == CLAW:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < 32 and 0 <= Y < 40 and px[X, Y] in hn:
                    hits.append((x, y))
                    break
    for (x, y) in hits:
        px[x, y] = K


def shreds(s):
    """The canvas hangs in shreds: tattered strips drooping from the top and sides over the dark void."""
    for y in range(5, 35):
        for x in range(5, 27):
            s.set(x, y, VOID)
    strips = [(5, 3, 26, 0), (8, 2, 12, 1), (11, 2, 7, 2), (14, 1, 4, 3), (18, 2, 9, 4), (21, 2, 15, 5),
              (24, 3, 24, 6)]
    for (x0, w, ln, sd) in strips:
        for y in range(5, 5 + ln):
            t = (y - 5) / ln
            wv = max(1, int(round(w * (1 - 0.6 * t))))
            sway = int(round(0.8 * math.sin(t * 3 + sd)))
            for i in range(wv):
                x = x0 + i + sway
                c = CANV[3] if i == 0 else CANV[2] if i < wv - 1 else CANV[1]
                if y == 5 + ln - 1:
                    c = CANV[4] if (i + sd) % 2 else CANV[2]                # frayed ends catch the light
                s.set(x, y, c)
            if (y + sd) % 5 == 0:
                s.set(x0 + sway, y, CANV[4])
    # a flap folded down at the bottom-left, its pale back showing; a curl of canvas at the bottom right
    poly(s, [(5, 34), (5, 27), (12, 34)], lambda x, y: CANV[3] if (x + y) % 4 else CANV[4])
    s.line(5, 27, 12, 34, CANV[4])
    poly(s, [(20, 34), (26, 30), (26, 34)], lambda x, y: CANV[2])
    s.line(20, 34, 26, 30, CANV[3])


def build_portrait():
    frames, tags = [], []
    for tag, fn in (("a", portrait_a), ("b", portrait_b), ("c", portrait_c), ("d", portrait_d), ("e", portrait_e)):
        tags.append((tag, len(frames), len(frames)))
        frames.append({"ms": 1000, "cels": {"Portrait": fn()}})
    a = len(frames)
    for k, ms in enumerate((220, 120, 110, 140, 260, 200)):
        frames.append({"ms": ms, "cels": {"Portrait": tear_frame(k)}})
    tags.append(("tear", a, a + 5))
    tags.append(("torn", len(frames), len(frames)))
    frames.append({"ms": 1000, "cels": {"Portrait": tear_frame(5)}})
    return 32, 40, ["Portrait"], frames, tags


# =========================================================================== blood veil
def bloodveil_frame(f, n=6):
    W_, H_ = 32, 64
    img = blank(W_, H_)
    px = img.load()
    off = f * H_ / n                    # the flow moves one full period (64 px) per loop -> seamless in time
    TAU = 2 * math.pi
    for y in range(H_):
        yy = y - off
        # sheet edges wobble with the flow (period 64 in y so the column tiles vertically)
        le = 8.5 + 1.6 * math.sin(TAU * yy / 64 * 2 + 0.7) + 0.8 * math.sin(TAU * yy / 64 * 3 + 2.0)
        re = 23.5 + 1.4 * math.sin(TAU * yy / 64 * 2 + 2.9) + 0.9 * math.sin(TAU * yy / 64 * 5 + 0.3)
        for x in range(W_):
            xc = x + 0.5
            if xc < le - 1.2 or xc > re + 1.2:
                continue
            edge = xc < le or xc > re
            # base sheet: dark clotted red, faint flowing sheen, lit a little on the left
            u = (xc - le) / max(1.0, re - le)
            v = 0.24 + 0.1 * (1 - u) + 0.06 * math.sin(TAU * yy / 64 * 3 + x * 0.9)
            # rivulets: a few brighter crimson streams, surging downward in pulses
            for (rx, ph, sp) in ((12.2, 0.0, 2), (16.4, 2.1, 3), (20.3, 4.2, 2)):
                dxr = abs(xc - rx - 0.7 * math.sin(TAU * yy / 64 + ph))
                if dxr < 0.8:
                    pulse = 0.5 + 0.5 * math.sin(TAU * (y - f * H_ / n * sp) / 64 * sp + ph)
                    v = max(v, 0.42 + 0.36 * pulse ** 2)
            if xc - le < 1.2 and not edge:
                v = max(v, 0.46)                                           # lit left rim of the sheet
            if edge:
                v = min(v, 0.3)
            i = int(clamp(v) * (len(BL) - 1) + 0.5)
            c = BL[max(1, min(len(BL) - 1, i))]
            a = 255
            if edge:
                a = 200
            px[x, y] = (c[0], c[1], c[2], a)
    # droplets falling beside the sheet (they move 2 periods per loop: still seamless)
    for (x, y0, sp) in ((5, 7, 2), (26, 31, 2), (6, 45, 1), (27, 12, 1)):
        y = int((y0 + f * H_ / n * sp) % H_)
        for d in range(3):
            yy = (y - d) % H_
            c = BL[5] if d == 0 else BL[3]
            px[x, yy] = (c[0], c[1], c[2], 255 if d < 2 else 170)
    return img


def build_bloodveil():
    frames = [{"ms": 100, "cels": {"Veil": bloodveil_frame(f)}} for f in range(6)]
    return 32, 64, ["Veil"], frames, [("loop", 0, 5)]


# =========================================================================== statues
def plinth(s, x0=5, x1=26, top=50):
    """Black-marble plinth: cap slab, die with a panel, base."""
    for x in range(x0 - 1, x1 + 2):
        s.set(x, top, MB[5] if x < 16 else MB[4])
        s.set(x, top + 1, MB[3])
        s.set(x, top + 2, MB[1])
    for y in range(top + 3, 60):
        for x in range(x0 + 1, x1):
            c = MB[3] if x < x0 + 3 else MB[2] if x < x1 - 2 else MB[1]
            s.set(x, y, c)
    for x in range(x0 + 4, x1 - 3):                                       # sunk panel
        s.set(x, top + 5, MB[1]); s.set(x, 57, MB[3])
    for y in range(top + 5, 58):
        s.set(x0 + 4, y, MB[1]); s.set(x1 - 4, y, MB[3])
    for x in range(x0 - 1, x1 + 2):
        s.set(x, 60, MB[4] if x < 16 else MB[3])
        for y in range(61, 64):
            s.set(x, y, MB[2] if x < 16 else MB[1])


def shade_statue(s, base, R, mask_fn=None):
    """Rim-light pass on a flat-filled figure (colour `base`): upper-left edges lit, lower-right edges shaded."""
    img = s.img
    px = img.load()
    Wd, Hd = img.size
    out = []
    for y in range(Hd):
        for x in range(Wd):
            if px[x, y] != base:
                continue
            l = px[x - 1, y] if x > 0 else T
            u = px[x, y - 1] if y > 0 else T
            r = px[x + 1, y] if x < Wd - 1 else T
            d = px[x, y + 1] if y < Hd - 1 else T
            if l[3] == 0 or u[3] == 0:
                out.append((x, y, R[-1] if (l[3] == 0 and u[3] == 0) else R[-2]))
            elif r[3] == 0 or d[3] == 0:
                out.append((x, y, R[1]))
    for (x, y, c) in out:
        px[x, y] = c


def part_mask(Wd, Hd, shapes):
    """shapes: list of ('poly', pts) | ('ell', cx, cy, rx, ry) | ('line', x0, y0, x1, y1, w)."""
    m = Image.new("L", (Wd, Hd), 0)
    d = ImageDraw.Draw(m)
    for sh in shapes:
        if sh[0] == "poly":
            d.polygon([(float(x), float(y)) for x, y in sh[1]], fill=255)
        elif sh[0] == "ell":
            _, cx, cy, rx, ry = sh
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        elif sh[0] == "line":
            _, x0, y0, x1, y1, w = sh
            d.line([(x0, y0), (x1, y1)], fill=255, width=w)
    return m.load()


def sculpt(s, parts, R, light=(-0.72, -0.69), rim=0.0):
    """Paint rounded solid parts (in order, later parts in front) with distance-field normals lit from the
    upper-left. parts: list of (shapes, bias). Where a part overlaps an earlier one, a dark seam separates them."""
    Wd, Hd = s.w, s.h
    painted = [[False] * Hd for _ in range(Wd)]
    for shapes, bias in parts:
        m = part_mask(Wd, Hd, shapes)
        inside = [[m[x, y] > 0 for y in range(Hd)] for x in range(Wd)]
        INF = 99
        dist = [[INF if inside[x][y] else 0 for y in range(Hd)] for x in range(Wd)]
        for _ in range(2):
            for y in range(Hd):
                for x in range(Wd):
                    if dist[x][y]:
                        for dx, dy, c in ((-1, 0, 1), (0, -1, 1), (-1, -1, 1.4), (1, -1, 1.4)):
                            X, Y = x + dx, y + dy
                            v = dist[X][Y] if 0 <= X < Wd and 0 <= Y < Hd else 0
                            dist[x][y] = min(dist[x][y], v + c)
            for y in range(Hd - 1, -1, -1):
                for x in range(Wd - 1, -1, -1):
                    if dist[x][y]:
                        for dx, dy, c in ((1, 0, 1), (0, 1, 1), (1, 1, 1.4), (-1, 1, 1.4)):
                            X, Y = x + dx, y + dy
                            v = dist[X][Y] if 0 <= X < Wd and 0 <= Y < Hd else 0
                            dist[x][y] = min(dist[x][y], v + c)

        def D(x, y):
            return dist[x][y] if 0 <= x < Wd and 0 <= y < Hd else 0
        for y in range(Hd):
            for x in range(Wd):
                if not inside[x][y]:
                    continue
                gx = D(x + 1, y) - D(x - 1, y)
                gy = D(x, y + 1) - D(x, y - 1)
                n = math.hypot(gx, gy) or 1.0
                nx, ny = -gx / n, -gy / n
                edge = 1 - clamp((dist[x][y] - 1) / 4.0)
                l = 0.52 + 0.55 * (nx * light[0] + ny * light[1]) * edge + bias
                if dist[x][y] <= 1.0 and (nx * light[0] + ny * light[1]) > 0.3:
                    l += 0.15 + rim
                c = R[int(clamp(l) * (len(R) - 1) + 0.5)]
                seam = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < Wd and 0 <= Y < Hd and not inside[X][Y] and painted[X][Y]:
                        seam = True
                if seam and (nx * light[0] + ny * light[1]) < 0.4:
                    c = R[0]
                s.set(x, y, c)
                painted[x][y] = True


def statue_lady():
    s = Spr(32, 64)
    M = GR[1:]                     # marble ramp (grey-violet, restrained)
    parts = [
        # the long veil falling down her back (behind everything)
        ([("poly", [(15, 4), (18, 4), (17, 9), (15, 13), (13, 20), (11, 28), (10, 36), (9, 42), (6, 47), (6, 40),
                    (8, 30), (10, 20), (12, 11), (13, 6)])], -0.05),
        # the gown: narrow waist flaring to a pooled hem, a train behind
        ([("poly", [(13, 25), (19, 25), (21, 32), (23, 40), (26, 48), (26, 50), (4, 50), (5, 47), (8, 42), (10, 34),
                    (11, 29)])], 0.0),
        # torso, bent forward in grief
        ([("poly", [(13, 26), (12, 20), (13, 15), (16, 13), (19, 14), (20, 18), (19, 26)])], 0.05),
        # the bowed head (veiled)
        ([("ell", 17.5, 9.5, 3.2, 3.6)], 0.05),
        # the raised arm: upper arm down to the elbow, forearm up to the face
        ([("line", 18, 15, 21, 21, 3), ("line", 21, 21, 21, 12, 3)], 0.1),
        # hands pressed over the face
        ([("ell", 20.5, 10.5, 2.0, 2.4)], 0.15),
    ]
    sculpt(s, parts, M)
    # veil hem over the brow + a few carved folds in the gown
    for (x0, y0, x1, y1, c) in ((14, 30, 11, 48, M[1]), (17, 30, 17, 48, M[1]), (20, 33, 22, 48, M[1]),
                                (15, 31, 14, 47, M[4]), (19, 33, 20, 47, M[4])):
        s.line(x0, y0, x1, y1, c)
    s.set(22, 12, BL[3]); s.set(22, 13, BL[2]); s.set(22, 14, BL[1])     # a single red tear escaping the fingers
    plinth(s)
    s.outline()
    return s.img


def statue_gargoyle():
    s = Spr(32, 64)
    G = GR[:6]
    parts = [
        # folded bat wing rising behind the back, scalloped trailing edge
        ([("poly", [(19, 29), (17, 18), (14, 7), (13, 2), (12, 7), (10, 10), (9, 15), (7, 17), (7, 22), (6, 25),
                    (8, 30), (11, 34), (16, 34)])], -0.1),
        # the tail, curled down around the plinth's side
        ([("line", 9, 46, 6, 52, 2), ("line", 6, 52, 5, 58, 2), ("line", 5, 58, 7, 60, 2)], -0.05),
        # hunched body and haunch
        ([("poly", [(8, 49), (8, 42), (10, 36), (14, 32), (19, 28), (23, 26), (25, 29), (23, 34), (20, 38), (21, 44),
                    (20, 49)])], 0.0),
        ([("ell", 12.5, 43, 4.6, 5.6)], 0.05),                                # thigh
        ([("poly", [(14, 46), (19, 45), (22, 49), (22, 50), (13, 50)])], 0.05),  # hind foot
        # long forelimb reaching down to grip the plinth edge
        ([("line", 22, 30, 24, 39, 3), ("line", 24, 39, 25, 48, 3), ("poly", [(23, 47), (27, 47), (28, 50), (22, 50)])],
         0.08),
        # small, menacing head jutting forward, jaw open
        ([("poly", [(21, 25), (23, 21), (26, 20), (29, 22), (28, 24), (26, 24), (29, 26), (27, 28), (23, 28)])], 0.1),
        # swept-back horn
        ([("line", 23, 21, 19, 17, 2), ("line", 19, 17, 18, 14, 1)], 0.15),
    ]
    sculpt(s, parts, G)
    s.line(13, 31, 9, 15, G[4])                                              # wing finger bones
    s.line(15, 30, 13, 8, G[4])
    s.set(26, 22, K); s.set(26, 23, BL[3])                                   # deep-set eye, a dim red glint
    s.set(27, 25, K); s.set(28, 25, K); s.set(26, 25, BL[2])                # maw
    s.set(28, 24, G[5]); s.set(28, 26, G[5])                                 # fangs
    for (x, y) in ((27, 50), (25, 50), (21, 50)):
        s.set(x, y, G[5])                                                    # claws over the edge
    plinth(s)
    s.outline()
    return s.img


def build_statue():
    frames = [{"ms": 1000, "cels": {"Statue": statue_lady()}}, {"ms": 1000, "cels": {"Statue": statue_gargoyle()}}]
    return 32, 64, ["Statue"], frames, [("lady", 0, 0), ("gargoyle", 1, 1)]


# =========================================================================== fountain
def fountain_frame(f):
    Wd, Hd = 64, 48
    s = Spr(Wd, Hd)
    cx = 32
    # foot / plinth
    for y in range(43, 48):
        hw = 18 + (y - 43)
        for x in range(cx - hw, cx + hw):
            s.set(x, y, MB[4] if y == 43 else MB[2] if x < cx + hw - 3 else MB[1])
    # lower basin: front wall with mouldings (elliptical plan, rim at y 33)
    for x in range(4, 60):
        u = (x + .5 - cx) / 28
        if abs(u) > 1:
            continue
        rim = 33 + int(round(3 * math.sqrt(max(0.0, 1 - u * u))))
        for y in range(rim, 43):
            l = 0.55 - 0.4 * u - (y - rim) * 0.03
            c = MB[int(clamp(l) * 5 + 0.5)]
            if y == rim + 1:
                c = MB[5] if u < 0.2 else MB[3]
            if y == 40:
                c = MB[1]
            s.set(x, y, c)
    # blood pool surface inside the rim (ellipse), with a shimmer that drifts
    for y in range(29, 37):
        for x in range(4, 60):
            e = ((x + .5 - cx) / 27) ** 2 + ((y + .5 - 33) / 3.4) ** 2
            if e > 1:
                continue
            c = BL[3] if e > 0.7 else BL[4]
            if y <= 30:
                c = BL[2]
            ph = (x + f * 4 + (y % 2) * 7) % 16
            if y in (32, 34) and ph < 2 and e < 0.8:
                c = BL[5] if ph == 0 else BL[6]                            # drifting shimmer dashes
            s.set(x, y, c)
    # rim edge (lit back rim, thin)
    for x in range(4, 60):
        u = (x + .5 - cx) / 28
        if abs(u) > 1:
            continue
        yb = 33 - int(round(3.6 * math.sqrt(max(0.0, 1 - u * u))))
        s.set(x, yb, MB[4] if u < 0 else MB[3])
    # central pedestal
    def prof(y):
        if y in (32, 33): return 4.0
        if 24 <= y <= 31: return 2.2 + (0.8 if y in (27, 28) else 0)
        return 0
    turned(s, cx, 24, 33, prof, MB)
    # upper bowl
    for x in range(cx - 10, cx + 10):
        u = (x + .5 - cx) / 10
        for y in range(21, 25):
            if abs(u) > 1 - (y - 21) * 0.18:
                continue
            c = MB[5] if y == 21 and u < 0.3 else MB[4] if u < -0.3 else MB[3] if u < 0.4 else MB[1]
            if y == 21 and abs(u) < 0.85:
                c = BL[4] if (x + f) % 5 else BL[6]                        # the brimming blood
            s.set(x, y, c)
    # the weeping angel standing on the upper bowl: black marble, wings folded high behind, head bowed
    parts = [
        ([("poly", [(30, 20), (27, 11), (24, 4), (23, 0), (26, 1), (29, 5), (31, 10), (32, 20)])], -0.05),
        ([("poly", [(34, 20), (37, 11), (40, 4), (41, 0), (38, 1), (35, 5), (33, 10), (32, 20)])], -0.2),
        ([("poly", [(28, 21), (29, 15), (30, 11), (34, 11), (35, 15), (36, 21)])], 0.05),
        ([("ell", 33.0, 8.5, 2.4, 2.6)], 0.1),
        ([("line", 30, 13, 34, 10, 2)], 0.15),
    ]
    sculpt(s, parts, MB)
    for (x0, y0, x1, y1) in ((30, 14, 29, 20), (33, 14, 33, 20)):
        s.line(x0, y0, x1, y1, MB[1])                                      # robe folds
    # blood tears: from the eyes down the cheek, dripping into the bowl
    s.set(34, 9, BL[5]); s.set(34, 10, BL[4]); s.set(35, 11, BL[4])
    ty = 12 + (f % 4) * 2
    s.set(35, ty, BL[5]); s.set(35, ty + 1, BL[3])
    s.outline()
    # streams (not outlined): upper-bowl overflow falling into the pool, and lip trickles down the front wall
    for (sx, y0, y1) in ((22, 22, 32), (41, 22, 32)):
        for y in range(y0, y1):
            k = (y - f * 3) % 6
            s.set(sx, y, BL[6] if k == 0 else BL[4] if k < 3 else BL[3])
        s.set(sx - 1, y1 - 1, BL[5]); s.set(sx + 1, y1 - 1, BL[5])          # splash
    for (tx, ln) in ((14, 6), (27, 4), (45, 7), (52, 3)):
        u = (tx + .5 - cx) / 28
        rim = 33 + int(round(3 * math.sqrt(max(0.0, 1 - u * u))))
        for y in range(rim, rim + ln):
            k = (y - f * 2) % 4
            s.set(tx, y, BL[5] if k == 0 else BL[3])
        s.set(tx, rim + ln, BL[4] if f % 2 else BL[3])
    return s.img


def build_fountain():
    frames = [{"ms": 140, "cels": {"Fountain": fountain_frame(f)}} for f in range(4)]
    return 64, 48, ["Fountain"], frames, [("loop", 0, 3)]


PROPS = {
    "cm_portrait": build_portrait,
    "cm_bloodveil": build_bloodveil,
    "cm_statue": build_statue,
    "cm_fountain": build_fountain,
}
