"""FX sheets for THE FERRYMAN (Drowned Barrows).  Used by art/gen_barrows_ferryman.py.

    fx_db_wave  48x32, 4 frames loop, pivot bottom-centre: curling black-teal water wave with a pale foam crest, travelling RIGHT
    fx_db_wisp  12x12, 4 frames loop, centred: small teal soul-wisp flame with a faint face, travelling RIGHT
    fx_db_hook  16x16, 2 frames, centred: the thrown hook-lantern head (iron boat-hook + small glowing lantern), facing RIGHT
Each returns a list of asebuild frames ({"ms", "cels"}) using the layers named in LAYERS_*.
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import barrows_ferryman_draw as D  # noqa: E402  (registers the ferryman palette)
from enemy_kit import Layer, FXLayer, hash01, poly_mask, n_plate, n_dome, mask_disc, line, ip, norm3  # noqa: E402

LAYERS_WAVE = ["Water", "Foam"]
LAYERS_WISP = ["Wisp"]
LAYERS_HOOK = ["Glow", "Hook"]


def _restore():
    K.setup(D.W, D.H)


# =========================================================================== wave
def fx_db_wave():
    w, h = 48, 32
    K.setup(w, h)
    B = h - 1
    frames = []
    for i in range(4):
        ph = i / 4.0
        Wt, Fo = Layer("Water"), FXLayer("Foam")
        curl = 1.2 * math.sin(ph * 2 * math.pi)              # lip rolls forward / back
        rise = 0.8 * math.cos(ph * 2 * math.pi)
        prof = [(0.0, B + 1.0), (4.0, B - 0.6), (10.0, B - 3.0), (16.0, B - 7.0), (21.0, B - 12.0 - rise * 0.5),
                (25.5, B - 17.0 - rise), (29.5, B - 20.5 - rise), (33.5, B - 21.6 - rise), (37.0, B - 20.4 - rise),
                (40.0 + curl, B - 17.6 - rise * 0.6), (41.6 + curl, B - 14.4), (40.6 + curl, B - 11.8),
                (38.6 + curl * 0.6, B - 13.2), (36.8, B - 14.2), (35.4, B - 12.2), (35.8, B - 8.0), (38.0, B - 4.2),
                (41.8, B - 1.4), (44.5, B + 1.0)]
        m = {q for q in poly_mask(prof) if 0 <= q[0] < w and 0 <= q[1] <= B}
        # normals: the back slope faces up-left (lit), the curling face faces right (shadow)
        nm = n_plate(m, 3.2, (-0.1, -0.2), 1.2,
                     fold=lambda x, y: (0.12 * math.sin(x * 0.55 - y * 0.35 + ph * 6.28), 0.0))
        Wt.paint(nm, "N", -2, ao=0)
        # the barrel under the lip: deepest black
        barrel = poly_mask([(36.6, B - 13.6), (39.0 + curl * 0.6, B - 12.6), (39.6 + curl * 0.4, B - 9.0),
                            (37.4, B - 7.0), (36.4, B - 10.0)])
        Wt.decal([q for q in barrel if q in m], ("N", 0))
        # streaks running back down the swell (travel with the wave)
        for k in range(5):
            x0 = (8 + k * 6 - i * 2.0) % 30 + 3
            seg = line((x0, B - 1), (x0 + 5, B - 6 - k % 2 * 2))
            Wt.decal([q for q in seg if q in m and hash01(q[0], q[1], 5) < 0.8], ("N", 2))
        # a cold teal glow line inside the face (the drowned light)
        face = line((36.2, B - 11.4), (37.0, B - 6.2)) + line((37.0, B - 6.2), (40.0, B - 2.6))
        Wt.decal([q for q in face if q in m], "Z2")
        Wt.decal([q for j, q in enumerate(face) if q in m and (j + i) % 3 == 0], "Z3")
        # foam crest: pale along the top edge from the swell to the lip, broken up
        top = {}
        for (x, y) in m:
            if (x, y - 1) not in m and x >= 19:
                top[(x, y)] = True
        for (x, y) in top:
            n = hash01(x, i, 11)
            Fo.put([(x, y)], "N5" if n < 0.75 else "Z4")
            if x >= 26 and n < 0.55:
                Fo.put([(x, y + 1)], "N4")
        # the lip: bright curl
        lip = ip((41.0 + curl, B - 15.0))
        Fo.put([lip, (lip[0], lip[1] + 1), (lip[0] - 1, lip[1] + 2)], "N5")
        # spray ahead of the lip + drops falling from it
        for k in range(7):
            a = -math.pi * (0.1 + 0.55 * hash01(k, i, 21))
            r = 2 + 6 * hash01(k, i, 22)
            q = ip((42.5 + curl + math.cos(a) * r, B - 16.5 + math.sin(a) * r + (i % 2)))
            if 0 <= q[0] < w and 0 <= q[1] <= B:
                Fo.put([q], "N5" if k % 3 else "Z4")
        for k in range(3):
            y = B - 10 + ((i * 3 + k * 4) % 9)
            Fo.put([(int(41 + curl * 0.6 + (k % 2)), y)], "N4")
        # surface foam line at the base, trailing behind
        for x in range(0, 46):
            if hash01(x + i * 3, 1, 31) < 0.45 and (x, B) not in m:
                Fo.put([(x, B)], "N4" if x > 40 else "N3")
        frames.append({"ms": 90, "cels": {"Water": K.render_layer(Wt), "Foam": Fo.image()}})
    _restore()
    return frames


# =========================================================================== wisp
def fx_db_wisp():
    w, h = 12, 12
    K.setup(w, h)
    frames = []
    for i in range(4):
        L = FXLayer("Wisp")
        ph = i * math.pi / 2
        hc = (7.2 + 0.3 * math.sin(ph), 5.6 + 0.4 * math.cos(ph))
        # tapering flame tail streaming back (left), wavering
        tail = {}
        for k in range(26):
            t = k / 25
            x = hc[0] - t * 6.6
            y = hc[1] + math.sin(t * 4.0 + ph) * 1.4 * t
            r = 2.6 * (1 - t) ** 0.9 + 0.2
            for q in mask_disc((x, y), r, r * 0.9):
                if 0 <= q[0] < w and 0 <= q[1] < h:
                    tail[q] = min(tail.get(q, 9), t)
        for q, t in tail.items():
            L.put([q], "Z3" if t < 0.35 else "Z2" if t < 0.7 else "Z1")
        # head: bright soul core
        head = mask_disc(hc, 2.9, 2.7)
        for q in head:
            dx, dy = q[0] + .5 - hc[0], q[1] + .5 - hc[1]
            r = math.hypot(dx, dy)
            L.put([q], "Z5" if r < 1.3 else "Z4" if r < 2.2 else "Z3")
        # a faint face: two hollow eyes and a moaning mouth
        e1, e2 = ip((hc[0] - 0.2, hc[1] - 0.8)), ip((hc[0] + 1.6, hc[1] - 0.8))
        L.put([e1, e2], "Z2")
        L.put([ip((hc[0] + 0.8, hc[1] + 1.0 + (0.5 if i % 2 else 0)))], "Z2")
        # dark rim so it reads on teal/grey backgrounds
        rim = set()
        for (x, y) in list(L.px):
            for dx, dy in ((1, 0), (0, -1), (0, 1)):
                q = (x + dx, y + dy)
                if q not in L.px and 0 <= q[0] < w and 0 <= q[1] < h and x >= hc[0] - 1:
                    rim.add(q)
        L.put(rim, "Z0")
        # a mote shed behind
        m = ip((hc[0] - 6.0 - (i % 2), hc[1] + (1 if i < 2 else -1)))
        if 0 <= m[0] < w:
            L.put([m], "Z2")
        frames.append({"ms": 80, "cels": {"Wisp": L.image()}})
    _restore()
    return frames


# =========================================================================== hook
def fx_db_hook():
    w, h = 16, 16
    K.setup(w, h)
    frames = []
    for i in range(2):
        Hk, G, FX = Layer("Hook"), FXLayer("Glow"), FXLayer("FX")
        # iron boat-hook head: socket ring at the left (chain end), spike pointing right, barb curling up-back
        D.tube(Hk, [(1.4, 3.5), (3.8, 3.5)], [1.4, 1.4], "X", 0, ao=0, floor=h - 1)
        D.tube(Hk, [(3.8, 3.5), (15.2, 3.5)], [1.0, 0.55], "X", 1, ao=0, floor=h - 1)
        barb = D.curve([(9.4, 4.0), (11.4, 6.6), (13.6, 7.6), (15.0, 6.4)], n=5)
        D.tube(Hk, barb, [0.95] * (len(barb) - 2) + [0.75, 0.55], "X", 1, ao=0, floor=h - 1)
        info = {}
        sway = (-6.0, 4.0)[i]
        D.draw_lantern(Hk, G, FX, (5.4, 4.4), sway, 1.0, i, info, floor=h - 1, chain=0.6)
        c = info["lantern"]
        G.px = {q: "GA2" if math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1]) < 3.6 else "GA1" for q, v in G.px.items()
                if math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1]) < 4.8 + i * 0.5}
        FX.px = {}
        img = K.render_layer(Hk)
        fx = FX.image()
        img.alpha_composite(fx)
        frames.append({"ms": 90, "cels": {"Glow": G.image(), "Hook": img}})
    _restore()
    return frames
