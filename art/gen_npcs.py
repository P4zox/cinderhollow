#!/usr/bin/env python3
"""NPC sheets + dialogue portraits -- docs/ART_SPEC2.md section G.

    python3 art/gen_npcs.py                 build every NPC sheet + portrait (Aseprite)
    python3 art/gen_npcs.py --preview       previews only (no Aseprite)
    python3 art/gen_npcs.py --only venn,portraits [--preview]

Sheets (face RIGHT, feet on the bottom row):
    npc_venn       32x48  idle(6 loop) talk(4 loop)       Sister Venn, shrine keeper (black habit, silver hair; see draw_venn)
    npc_ashwright  48x48  idle(8 loop, hammering) talk(4)  Old Ashwright, smith (with his work anvil)
    npc_scribe     32x56  idle(6 loop, book floats) talk(4) the Hollow Scribe
    npc_kalden     48x48  idle(4) talk(4) kneel(1)         Ser Kalden the Oathless
Portraits (64x64, tag `p`, 1 frame, framed bust, transparent outside the frame):
    portrait_venn / portrait_ashwright / portrait_scribe / portrait_kalden / portrait_player
Previews: art/previews/npcs.png (all sheets, 4x, one row per tag + the portraits).

Method = the enemy kit (art/enemy_kit.py): normal-field shaded parts, hue-shifted ramps, decals,
per-layer sel-out outline; a few NPC-specific materials are registered here at import time.
"""
import math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, arm, leg, blade_px, dirv, flame)

BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

# =========================================================================== extra materials
EXTRA = {
    # Venn's pale grey robe (cool)
    "N0": "#1c1b23", "N1": "#302f3a", "N2": "#4c4a56", "N3": "#716f7a", "N4": "#9b98a0", "N5": "#cbc7c4",
    # skin
    "S0": "#2b1b1d", "S1": "#553632", "S2": "#845a4a", "S3": "#b48670", "S4": "#dcb89c",
    # soot-black leather
    "J0": "#0f0d0e", "J1": "#1b1718", "J2": "#2b2524", "J3": "#3e3531", "J4": "#574a42",
    # scribe's dusty indigo
    "U0": "#110f1b", "U1": "#1d1a2e", "U2": "#2b2743", "U3": "#3d375b", "U4": "#554d77", "U5": "#776d96",
    # Kalden's white plate
    "E0": "#1f2228", "E1": "#3b4049", "E2": "#5f6670", "E3": "#8c939b", "E4": "#b9bec3", "E5": "#e6e8e3",
    # teal trim
    "X0": "#0e2427", "X1": "#174241", "X2": "#22615b", "X3": "#34857a", "X4": "#58ab9b",
    # blue cloak
    "Z0": "#0d1122", "Z1": "#161e3a", "Z2": "#212e55", "Z3": "#2f4271", "Z4": "#465c8f",
    # pale skin (Venn)
    "f0": "#3d2b31", "f1": "#6f5153", "f2": "#a17f77", "f3": "#ccac9c", "f4": "#ebd6c6",
    # grey beard / hair
    "H0": "#1f1c1c", "H1": "#3a3534", "H2": "#5c5553", "H3": "#837a74", "H4": "#aca197",
    # Venn (agent VN, after the reference / portrait_venn): black habit, silver-white hair, silver thread, white light
    "b0": "#070609", "b1": "#0f0d13", "b2": "#18151e", "b3": "#241f2c", "b4": "#352f40", "b5": "#4d4659",
    "h0": "#4f4d5a", "h1": "#716f7d", "h2": "#9795a3", "h3": "#bcbac7", "h4": "#dddbe5", "h5": "#f4f3f8",
    "g0": "#4a4755", "g1": "#7a7788", "g2": "#aeabbb", "g3": "#dcdae6", "g4": "#ffffff",
    "w0": "#b9b6c8", "w1": "#dcdae6", "w2": "#f2f0f6", "w3": "#ffffff",
    "k0": "#5d4b52", "k1": "#8c767d", "k2": "#b8a3a8", "k3": "#d9c8ca", "k4": "#eee3e2",
}
for k_, v_ in EXTRA.items():
    K.HEX[k_] = v_
    K.RGBA[k_] = tuple(int(v_[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k_[0], [])
    if k_ not in K.RAMP[k_[0]]:
        K.RAMP[k_[0]].append(k_)
K.SHINY["E"] = 0.93


def rgba(c):
    return K.RGBA[c]


class Glow:
    """Un-outlined FX pixels; may carry a few alpha steps (soft light)."""
    def __init__(self, name):
        self.name = name
        self.px = {}

    def put(self, pts, c, a=255):
        col = rgba(c)[:3] + (a,) if isinstance(c, str) else c
        for p in pts:
            if K.inb(*p):
                old = self.px.get(p)
                if old is None or old[3] <= col[3]:
                    self.px[p] = col

    def halo(self, c, r0, r1, col, alphas=(70, 38)):
        """two-step soft glow ring around c (inner r0, outer r1)."""
        for q in mask_disc(c, r1):
            d = math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1])
            a = alphas[0] if d <= r0 else alphas[1]
            self.put([q], col, a)

    def image(self):
        img = Image.new("RGBA", (K.W, K.H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.px.items():
            pix[p] = c
        return img


def render(Ls, order):
    out = {}
    base = K.LIGHT
    for n in order:
        v = Ls.get(n)
        if v is None:
            continue
        lt = getattr(v, "light", None)
        if lt:
            l_ = math.sqrt(sum(c * c for c in lt))
            K.LIGHT = tuple(c / l_ for c in lt)
        out[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
        K.LIGHT = base
    return out


def n_ell(mask, c, rx, ry, flat=1.0):
    """ellipsoid normals over an arbitrary mask (for faces / skulls)."""
    out = {}
    for (x, y) in mask:
        ex, ey = (x + .5 - c[0]) / rx * flat, (y + .5 - c[1]) / ry * flat
        e = min(0.95, ex * ex + ey * ey)
        l_ = math.sqrt(ex * ex + ey * ey + (1 - e))
        out[(x, y)] = (ex / l_, ey / l_, math.sqrt(1 - e) / l_)
    return out


def rim_light(imgs, names, src, radius, col, dark, strength=0.55):
    """Warm rim light from a point light: silhouette edges of `names` facing `src` pick up light."""
    W_, H_ = K.W, K.H
    union = set()
    for n in names:
        if n in imgs:
            px = imgs[n].load()
            for y in range(H_):
                for x in range(W_):
                    if px[x, y][3]:
                        union.add((x, y))
    for n in names:
        if n not in imgs:
            continue
        im = imgs[n].copy()
        px = im.load()
        src_px = imgs[n].load()
        for y in range(H_):
            for x in range(W_):
                c = src_px[x, y]
                if not c[3]:
                    continue
                dx, dy = src[0] - x, src[1] - y
                d = math.hypot(dx, dy)
                if d > radius or d < 0.5:
                    continue
                sx = int(round(dx / d)) if abs(dx) / d > 0.38 else 0
                sy = int(round(dy / d)) if abs(dy) / d > 0.38 else 0
                if (x + sx, y + sy) in union:
                    continue
                f = strength * (1 - d / radius) ** 0.6
                base = dark if c[:3] == K.RGBA["OUT"][:3] else col
                px[x, y] = tuple(int(c[i] + (base[i] - c[i]) * (1.0 if base is dark else f)) for i in range(3)) + (255,)
                ix, iy = x - sx, y - sy
                if (ix, iy) in union and c[:3] == K.RGBA["OUT"][:3]:
                    ci = src_px[ix, iy]
                    if ci[3] and ci[:3] != K.RGBA["OUT"][:3]:
                        px[ix, iy] = tuple(int(ci[i] + (col[i] - ci[i]) * f) for i in range(3)) + (255,)
        imgs[n] = im
    return imgs


def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def edge_of(m, dirs=((1, 0), (-1, 0), (0, -1), (0, 1))):
    return [q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in dirs)]


# =========================================================================== SISTER VENN
VENN_L = ["BackArm", "Robe", "Capelet", "Head", "FrontArm", "Lantern", "FX"]
V_NEU = dict(P=(14.0, 38.5), C=(14.6, 29.0), Hd=(15.6, 24.6), hup=(0.12, -1), hf=(21.0, 35.0), hb=None,
             csw=0.0, fire=1.0, hem=0, sway=0.0, talk=0)
VP = mk(V_NEU)


def lantern(Ls, hand, ang, fi, fire, glow_col="w1"):
    """Small iron candle-lantern hanging from `hand` (ring), swinging by ang degrees; a pale white flame."""
    La = Ls["Lantern"]
    FX = Ls["FX"]
    ca, sa = math.sin(math.radians(ang)), math.cos(math.radians(ang))
    top = (hand[0] + ca * 1.6, hand[1] + sa * 1.6)
    La.fill(line(hand, top), "g1", noout=True)
    cx, cy = top[0] + ca * 3.0, top[1] + sa * 3.0
    c = ip((cx, cy))
    x, y = c
    pix = {}
    # cap (peaked), cage, glass, base -- blackened iron with silver fittings
    pix[(x, y - 3)] = "g2"
    for dx in (-1, 0, 1):
        pix[(x + dx, y - 2)] = "b4" if dx < 1 else "b3"
    for yy in (y - 1, y, y + 1):
        pix[(x - 2, yy)] = "b4"
        pix[(x + 2, yy)] = "b3"
        for dx in (-1, 0, 1):
            pix[(x + dx, yy)] = "w1" if fire > 0 else "b2"
    if fire > 0:
        pix[(x, y)] = "w3"
        pix[(x, y - 1)] = "w2"
        pix[(x, y + 1)] = "h4"      # the candle stub
    for dx in (-2, -1, 0, 1, 2):
        pix[(x + dx, y + 2)] = "g2" if dx < 1 else "g1"
    La.fixed(pix)
    if fire > 0:
        FX.halo((cx + .5, cy + .5), 4.2 + 0.4 * fire, 7.5 + 0.8 * fire, glow_col, (46, 20))
        if fi % 3 == 1:
            FX.put([(x, y - 4)], "w2", 150)
    return (cx, cy)


def draw_venn(p, fi, sw):
    """Sister Venn as in the reference / portrait_venn: a young nun in a black habit and layered mantle, black veil
    with a silver-embroidered brow band over long silver-white hair, a silver chain and cross; a pale lantern."""
    Ls = {n: Layer(n) for n in VENN_L if n != "FX"}
    Ls["FX"] = Glow("FX")
    R = ID
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    floor = K.H - 1.0
    shF, shB = F(1.4, -ln + 1.6), F(-1.8, -ln + 1.8)
    # ---- back arm (only in talk: the free hand opens toward the listener)
    if p["hb"]:
        arm(R, Ls["BackArm"], shB, p["hb"], 4.0, 4.2, 1.5, 1.6, "b", bias=0, fist="k", fist_r=0.9, pref=(0, 1))
        hq = ip(p["hb"])
        Ls["BackArm"].fixed({hq: "k4", (hq[0] + 1, hq[1] - 1): "k3", (hq[0] - 1, hq[1]): "g2"})
    # ---- habit: slender black bell to the floor, soft vertical folds, silver-embroidered hem
    Rb = Ls["Robe"]
    s = p["sway"]
    hem = floor + 0.4
    pts = [F(-2.6, -ln + 0.4), F(2.4, -ln + 0.2), F(3.2, -4.0), F(3.8, 1.5), (P[0] + 5.6 + s * 0.3, hem - 1.0)]
    n = 8
    for i in range(n + 1):
        t = i / n
        x = P[0] + 5.6 + s * 0.3 - (11.6) * t + s * 0.5 * t
        d = 0.8 if (i + p["hem"]) % 3 == 0 else 0.0
        pts.append((x, hem + d))
    pts += [(P[0] - 6.0 + s * 0.8, hem - 1.2), F(-4.2, 1.0), F(-3.4, -4.0)]
    m = R.mask(pts)
    Rb.paint(n_plate(m, 2.0, (-0.1, 0.0), 1.0,
                     fold=lambda x, y: (0.55 * math.sin((x - P[0] - s * 0.3) * 1.25) * min(1.0, max(0.0, (y - P[1] + 6) / 9)), 0)),
             "b", bias=0)
    ybot = max(q[1] for q in m)
    Rb.decal([q for q in m if q[1] >= ybot], ("b", 1))
    Rb.decal([q for q in m if q[1] == ybot - 1], ("g", 1))              # silver hem band
    R.dline(Rb, F(-3.4, -3.4), F(3.2, -3.6), ("b", 0))                 # cord belt
    R.decal(Rb, [F(2.6, -3.0), F(2.6, -2.0)], ("g", 1))               # hanging chain end
    # ---- layered mantle over the shoulders, silver trim
    Cl = Ls["Capelet"]
    cp = [F(-3.2, -ln - 0.4), F(2.8, -ln - 0.2), F(4.2, -ln + 4.4), F(2.6, -ln + 6.0), F(0.0, -ln + 5.4),
          F(-2.6, -ln + 6.6), F(-4.8, -ln + 5.0)]
    cm = R.mask(cp)
    Cl.paint(n_plate(cm, 1.6, (-0.2, -0.1), 1.2), "b", bias=1)
    Cl.decal([q for q in cm if (q[0], q[1] + 1) not in cm], ("g", 1))
    # ---- head: black veil, silver brow band, silver hair framing a pale face
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    # hair behind the face (under the veil's edge) and spilling down the back of the neck
    hair = [G(-0.6, -2.2), G(0.4, -1.6), G(-0.2, 1.8), G(0.2, 4.6), G(-1.6, 6.2), G(-2.4, 3.0), G(-2.2, -1.0)]
    R.plate(Hl, hair, "h", bevel=1.0, tilt=(-0.1, -0.2), strength=0.8, bias=1)
    face = [G(0.2, -1.6), G(2.6, -1.4), G(3.4, 0.6), G(3.0, 2.6), G(1.2, 3.4), G(0.0, 1.6)]
    fm = R.plate(Hl, face, "k", bevel=1.0, tilt=(0.3, 0.2), bias=1)
    hood = [G(-3.8, 3.8), G(-4.2, -0.4), G(-3.0, -3.6), G(-0.6, -4.8), G(1.8, -4.4), G(3.6, -2.6), G(4.0, -1.4),
            G(2.2, -2.2), G(0.4, -1.8), G(-0.8, -1.0), G(-1.6, 1.4), G(-1.8, 3.6), G(-2.4, 4.8)]
    hm = R.plate(Hl, hood, "b", bevel=1.6, tilt=(-0.15, -0.25), strength=1.25, bias=0)
    # silver-embroidered band where the veil meets the brow
    band = [q for q in hm if any((q[0] + a, q[1] + b) in fm for a, b in ((0, 1), (1, 1), (-1, 1)))]
    Hl.decal(band, ("g", 3))
    Hl.decal([q for q in band if q[0] % 2 == 0], ("g", 2))
    # fringe over the brow; half-lidded grey eye; lit chin
    top = min(q[1] for q in fm)
    Hl.decal([q for q in fm if q[1] == top], ("h", 4))
    eye = ip(G(2.0, -0.2))
    Hl.decal([(eye[0], eye[1] - 1)], ("k", 0))
    Hl.decal([eye], ("h", 1))
    Hl.decal([(eye[0] + 1, eye[1])], ("k", 2))
    Hl.decal([ip(G(3.2, 0.8))], ("k", 4))   # nose tip
    Hl.decal([ip(G(2.2, 2.0))], ("k", 1) if not p["talk"] else ("k", 0))  # mouth
    if p["talk"] == 2:
        Hl.decal([ip(G(2.2, 2.6))], ("k", 1))
    # high black collar
    col = [ip(G(0.6, 4.2)), ip(G(1.4, 4.2)), ip(G(0.4, 5.0)), ip(G(1.4, 5.0))]
    Hl.fixed({q: "b2" for q in col})
    # ---- chain and silver cross at the breast
    Fx = Ls["FX"]
    cx_ = ip(F(2.3, -ln + 3.6))
    Cl.fixed({ip(F(1.2, -ln + 1.2)): "g1", ip(F(1.6, -ln + 2.2)): "g2"})
    cross = {(cx_[0], cx_[1] - 1): "g3", cx_: "g4", (cx_[0] - 1, cx_[1]): "g2", (cx_[0] + 1, cx_[1]): "g2",
             (cx_[0], cx_[1] + 1): "g2", (cx_[0], cx_[1] + 2): "g1"}
    Fx.put([q for q in [(cx_[0] + a, cx_[1] + b) for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2, 3)]
            if q not in cross and any((q[0] + a, q[1] + b) in cross for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))], "b0")
    for q, c_ in cross.items():
        Fx.put([q], c_)
    # a long lock of silver hair over the shoulder, in front of the mantle
    lock = [ip(G(0.0, 3.0)), ip(G(0.2, 4.0)), ip(F(0.8, -ln + 1.0)), ip(F(0.9, -ln + 2.2)), ip(F(0.6, -ln + 3.4))]
    Cl.fixed({q: ("h4" if i < 2 else "h3" if i < 4 else "h2") for i, q in enumerate(lock)})
    # ---- front arm: black sleeve to the lantern hand, a silver chain at the wrist
    Fa = Ls["FrontArm"]
    el = arm(R, Fa, shF, p["hf"], 4.2, 4.2, 1.6, 1.8, "b", bias=1, fist="k", fist_r=0.9, pref=(-0.6, 1))
    cuff = lerp(el, p["hf"], 0.72)
    R.dome(Fa, cuff, 1.6, 1.6, "b", bias=1)
    Fa.decal([ip(add(cuff, (0.8, 0.9)))], "g2")    # the wrist chain
    # ---- lantern
    lc = lantern(Ls, (p["hf"][0] + 0.6, p["hf"][1] + 0.6), p["csw"], fi, p["fire"])
    rim = [(lc, 13, (214, 212, 232), (38, 36, 50), ["Robe", "Capelet", "FrontArm", "BackArm", "Head"], 0.45)]
    return Ls, {"rim": rim}


def venn_idle():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        b = 0.5 + 0.5 * math.sin(ph)
        fr.append((160, VP(C=(14.6, 29.0 + b * 0.6), Hd=(15.6, 24.6 + b * 0.7), hf=(21.0, 35.0 + b * 0.4),
                           csw=7 * math.sin(ph + 0.6), fire=(1.0, 1.2, 0.9, 1.1, 1.25, 0.95)[i], hem=i,
                           sway=0.6 * math.sin(ph))))
    return fr


def venn_talk():
    fr = []
    for i in range(4):
        b = (0, 0.5, 0.2, 0.6)[i]
        fr.append((170, VP(C=(14.8, 29.0 + b * 0.5), Hd=(16.0, 24.4 + b * 0.5), hup=(0.28 - 0.08 * (i % 2), -1),
                           hf=(20.6, 35.2), hb=(21.6 - 0.6 * (i % 2), 31.6 + 0.4 * b), csw=(3, -2, 2, -3)[i],
                           fire=(1.1, 0.95, 1.2, 1.0)[i], hem=i, talk=(1, 2, 1, 0)[i])))
    return fr


# =========================================================================== OLD ASHWRIGHT
ASH_L = ["Anvil", "BackArm", "BackLeg", "FrontLeg", "Body", "Apron", "Shoulder", "Head", "Work", "Hammer",
         "FrontArm", "FX"]
A_NEU = dict(P=(14.5, 36.0), C=(16.0, 26.2), Hd=(20.2, 21.6), hup=(0.42, -1), hf=(25.5, 30.5), hang=40.0,
             hb=(27.0, 33.4), fb=(9.5, 47), ff=(20.0, 47), spark=0, heat=1.0, talk=0, rest=False, jaw=0)
AP = mk(A_NEU)
ANVIL_TOP = 37          # anvil face row
WORK = (29, 36)         # glowing bar on the anvil face (left end)


def hammer(L, hand, ang, head_len=3.4):
    """Smith's hammer: wooden haft from the fist along ang, heavy iron head across the far end."""
    ca, sa = dirv(ang)
    pix = {}
    end = (hand[0] + ca * 6.6, hand[1] + sa * 6.6)
    for i, q in enumerate(line((hand[0] - ca * 1.4, hand[1] - sa * 1.4), end)):
        pix[q] = "W4" if i % 3 else "W3"
    px, py = -sa, ca
    head = {}
    for u in (5.4, 5.9, 6.4, 6.9, 7.4):
        for v in (-2.2, -1.6, -1.0, -0.4, 0.2, 0.8, 1.4, 2.0):
            q = ip((hand[0] + ca * u + px * v + .5, hand[1] + sa * u + py * v + .5))
            head[q] = (u, v)
    ys = [q[1] for q in head]
    for q in head:
        up_ = (q[0], q[1] - 1) not in head
        lf = (q[0] - 1, q[1]) not in head
        pix[q] = "I5" if up_ and lf else "I4" if (up_ or lf) else "I3"
    L.fixed(pix)
    return (hand[0] + ca * 6.4, hand[1] + sa * 6.4)


ASH_HEAD_KEY = {"K": "OUT", "a": "S1", "b": "S2", "c": "S3", "d": "S4", "g": "H1", "h": "H2", "H": "H3", "j": "H4",
                "m": "S0", "r": "C3", "R": "C4"}
# (user reference) wild grey mane falling behind to the shoulders, red headband, heavy brow, long beard; faces right
ASH_HEAD = [
    "..K..KK.K.....",
    ".KhK.KjKHK....",
    ".KhhKjHjjjK...",
    "KhHhjHjjHjHK..",
    "KghhRRRRRRRRK.",
    "KgHhrrbccdddcK",
    "KghHhbcjjcdjjK",
    "KgHhbbcKccdKcK",
    "KhgHhbbcccdddK",
    "KgHhhbjjjjjjK.",
    "KghHjjjjHHjjK.",
    ".KgHjjjHjjjjK.",
    ".KhgHjjjjjjjK.",
    ".KgghjjjHjjK..",
    "..KgHKjjjjjK..",
    "..KgK.KhjjK...",
    "...K...KhK....",
    "........K.....",
]
ASH_HEAD_TALK = [r for r in ASH_HEAD]
ASH_HEAD_TALK[10] = "KghHjjjmmjjjK."
ASH_HEAD_TALK[11] = ".KgHjjjjmjjjK."


def stamp(L, rows, key, org):
    """Stamp a hand-pixelled part (rows of chars) into a Layer as fixed colours; '.' = empty."""
    pix = {}
    hh, ww = len(rows), max(len(r) for r in rows)

    def at(x, y):
        return rows[y][x] if 0 <= y < hh and 0 <= x < len(rows[y]) else "."
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "K" and any(at(x + a, y + b) == "." for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue          # silhouette outline comes from the layer's own sel-out pass
            pix[(org[0] + x, org[1] + y)] = key[ch]
    L.fixed(pix)
    return pix


def draw_anvil(L, W_):
    """Squat work anvil standing right of the smith (own layer)."""
    top = ANVIL_TOP
    face = [(27.0, top), (41.0, top), (45.5, top + 0.6), (41.0, top + 2.6), (37.0, top + 3.2), (36.0, top + 5.5),
            (38.5, top + 7.6), (39.5, 47.9), (26.5, 47.9), (27.5, top + 7.6), (30.0, top + 5.5), (29.0, top + 3.2),
            (27.0, top + 2.6)]
    m = poly_mask(face)
    L.paint(n_plate(m, 1.4, (-0.1, 0.1), 1.2), "I", bias=-1)
    L.decal([q for q in m if q[1] == top], ("I", 4))
    L.decal([q for q in m if q[1] == top + 1 and q[0] < 42], ("I", 3))
    L.decal([q for q in m if q[1] >= 46], ("I", 1))


def draw_ash(p, fi, sw):
    Ls = {n: Layer(n) for n in ASH_L if n != "FX"}
    FX = Glow("FX")
    Ls["FX"] = FX
    R = ID
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(3.2, -ln + 1.6), F(-3.6, -ln + 2.0)
    draw_anvil(Ls["Anvil"], 48)
    # ---- hot work-piece (in the tongs) on the anvil face
    heat = p["heat"]
    wx, wy = WORK
    Wk = Ls["Work"]
    wp = {}
    for dx in range(6):
        wp[(wx + dx, wy)] = ("O5" if heat > 1.4 else "O4") if 1 <= dx <= 3 else "O3" if dx < 5 else "O2"
    Wk.fixed(wp)
    FX.halo((wx + 3, wy), 3.0, 5.5 + heat, "O3", (40 + int(heat * 18), 18 + int(heat * 8)))
    # ---- back arm (flesh) with tongs clamped on the bar
    Ba = Ls["BackArm"]
    el = arm(R, Ba, shB, p["hb"], 5.2, 5.2, 2.3, 2.0, "S", bias=-1, fist="S", fist_r=1.4, pref=(0, 1))
    if not p["talk"]:
        tp = {}
        for q in line(p["hb"], (wx + 1.2, wy - 0.2)):
            tp[q] = "I3"
        for q in line((p["hb"][0], p["hb"][1] + 1), (wx + 0.8, wy + 0.8)):
            tp.setdefault(q, "I2")
        Ba.fixed(tp)
    # ---- legs: stout, dark trousers, heavy boots
    for nm, hip, ft, bias in (("BackLeg", F(-2.8, 0.6), p["fb"], -1), ("FrontLeg", F(2.6, 0.6), p["ff"], 0)):
        leg(R, Ls[nm], hip, ft, 5.4, 5.6, 2.7, 2.3, "L", bias=bias - 1, boot="J", flen=3.4, heel=1.8, boot_h=3.0,
            pref=(1, -0.2))
    # ---- torso: barrel chest in a dark sleeveless jerkin
    Bd = Ls["Body"]
    torso = [F(-5.4, 1.0), F(-6.6, -ln + 4.0), F(-5.0, -ln - 0.8), F(2.4, -ln - 1.6), F(6.4, -ln + 1.8),
             F(6.8, -ln + 6.4), F(5.6, 1.0)]
    tm = R.plate(Bd, torso, "S", bevel=3.0, tilt=(-0.3, -0.2), strength=1.4, bias=-1)   # bare, muscled (reference)
    R.dline(Bd, F(-5.4, 0.2), F(5.6, 0.2), ("J", 2))               # belt
    R.decal(Bd, [F(-3.4, 0.2), F(-2.6, 0.2)], ("G", 3))             # buckle
    R.dline(Bd, F(-4.8, -ln + 3.0), F(-4.4, -1.0), ("S", 1))         # back muscle shadow
    R.dline(Bd, F(-5.0, -ln + 1.0), F(-1.0, 0.0), ("J", 3))           # riveted shoulder strap across the back
    R.decal(Bd, [F(-3.6, -ln + 4.0), F(-2.2, -ln + 7.6)], ("A", 4))
    # ---- apron: soot-black leather bib to the knees, strap over the neck
    Ap = Ls["Apron"]
    ap = [F(0.4, -ln + 2.6), F(4.6, -ln + 2.4), F(6.0, -ln + 6.0), F(6.2, 2.0), F(6.8, 9.4), F(4.4, 10.0),
          F(1.0, 9.8), F(-1.8, 9.0), F(-1.6, 1.0), F(-0.4, -ln + 6.0)]
    am = R.mask(ap)
    Ap.paint(n_plate(am, 1.8, (-0.1, 0.0), 1.1, fold=lambda x, y: (0.35 * math.sin(x * 1.4), 0)), "C", bias=0)   # red leather
    Ap.decal([q for q in am if hash01(q[0], q[1], 11) < 0.06], ("C", 1))   # scorch marks
    Ap.decal([q for q in am if (q[0], q[1] + 1) not in am], ("C", 1))
    R.dline(Ap, F(1.6, 3.2), F(5.4, 3.2), ("C", 2))                         # pocket
    R.decal(Ap, [F(1.6, 4.2), F(5.2, 4.4)], ("C", 2))
    R.dline(Ap, F(0.8, -ln + 2.4), add(Hd, (-1.8, 3.6)), ("J", 3))       # neck strap
    # ---- head: hand-pixelled (bald dome, heavy grey brow, long soot-grey beard)
    Hl = Ls["Head"]
    R.cap(Hl, F(0.6, -ln - 0.6), add(Hd, (-1.0, 3.0)), 2.6, 2.4, "S", bias=-1)   # bull neck
    head = ASH_HEAD_TALK if p["jaw"] else ASH_HEAD
    stamp(Hl, head, ASH_HEAD_KEY, (int(round(Hd[0])) - 7, int(round(Hd[1])) - 7))
    # ---- front arm: the gold prosthetic, swinging the hammer
    Fa = Ls["FrontArm"]
    Sh = Ls["Shoulder"]
    R.dome(Sh, shF, 3.0, 2.8, "S", bias=-1)                       # the stump shoulder (flesh)
    R.dline(Sh, add(shF, (-1.6, -2.2)), add(shF, (1.8, 1.6)), ("J", 3))    # harness strap
    el = ik(shF, p["hf"], 4.8, 5.0, (0.2, 1))
    R.cap(Fa, add(shF, (0.4, 0.8)), el, 1.9, 1.6, "G", bias=0)
    R.cap(Fa, el, p["hf"], 1.6, 1.4, "G", bias=0)
    R.dome(Fa, el, 1.5, 1.5, "I", bias=0)                          # elbow joint
    R.dome(Fa, p["hf"], 1.6, 1.6, "G", bias=0)                     # gauntlet fist
    Fa.decal([ip(lerp(el, p["hf"], 0.5))], ("G", 1))               # plate seam
    Fa.decal([ip(lerp(add(shF, (0.4, 0.8)), el, 0.5))], ("G", 1))
    # ---- hammer
    if p["rest"]:
        head = hammer(Ls["Hammer"], p["hf"], p["hang"])
    else:
        head = hammer(Ls["Hammer"], p["hf"], p["hang"])
    # ---- sparks
    if p["spark"]:
        st = p["spark"]
        ox, oy = wx + 3, wy - 1
        for k in range(12):
            a = -math.pi * (0.05 + 0.9 * hash01(k, st, 5))
            r = (1.5 + 7 * hash01(k, st, 6)) * (0.7 if st == 1 else 1.3)
            q = ip((ox + math.cos(a) * r * 1.3, oy + math.sin(a) * r + (0 if st == 1 else 0.12 * r * r)))
            FX.put([q], ("Y3", "Y2", "O4")[k % 3] if st == 1 else ("O4", "O3", "O2")[k % 3])
            if st == 1 and k % 3 == 0:
                FX.put([ip((ox + math.cos(a) * r * 0.9, oy + math.sin(a) * r * 0.7))], "Y2")
        if st == 1:
            FX.put([(ox, oy), (ox - 1, oy), (ox + 1, oy), (ox, oy - 1)], "Y3")
            FX.halo((ox + .5, oy + .5), 3, 6, "Y1", (90, 40))
    rim = [((wx + 3, wy - 1), 16 + 3 * heat, (240, 150, 70), (52, 22, 14),
            ["BackArm", "FrontLeg", "Body", "Apron", "Shoulder", "Head", "FrontArm", "Hammer"], 0.35 + 0.15 * heat)]
    return Ls, {"rim": rim}


def ik(s, h, l1, l2, pref):
    return K.ik(s, h, l1, l2, pref)


def ash_idle():
    rest = dict(hf=(25.0, 31.0), hang=52)
    return [
        (170, AP(**rest)),
        (110, AP(hf=(23.0, 25.5), hang=-20, C=(15.6, 26.0), Hd=(19.6, 21.4))),
        (110, AP(hf=(19.0, 18.0), hang=-115, C=(15.2, 25.6), Hd=(19.2, 21.0), hup=(0.3, -1))),
        (170, AP(hf=(16.8, 15.6), hang=-160, C=(14.9, 25.4), Hd=(19.0, 20.8), hup=(0.25, -1))),
        (60, AP(hf=(25.8, 29.6), hang=40, C=(16.3, 26.6), Hd=(20.6, 22.0), spark=1, heat=1.6)),
        (100, AP(hf=(26.0, 30.4), hang=44, C=(16.3, 26.8), Hd=(20.6, 22.2), spark=2, heat=1.5)),
        (110, AP(hf=(25.2, 28.4), hang=20, C=(16.0, 26.4), Hd=(20.3, 21.8), heat=1.3)),
        (150, AP(hf=(25.0, 30.6), hang=48, heat=1.1)),
    ]


def ash_talk():
    fr = []
    for i in range(4):
        b = (0, 0.5, 0.2, 0.6)[i]
        fr.append((180, AP(C=(15.4, 26.0 + b * 0.4), Hd=(18.8, 20.8 + b * 0.4), hup=(0.12, -1),
                           hf=(24.0, 32.0), hang=78, hb=(9.6, 34.0), talk=1, jaw=(1, 0, 1, 0)[i], heat=0.8)))
    return fr


def build_ash():
    SHEETS["npc_ashwright"] = (48, 48) + build_sheet("npc_ashwright", 48, 48, ASH_L, draw_ash,
                                                      [("idle", ash_idle), ("talk", ash_talk)])


# =========================================================================== THE HOLLOW SCRIBE
SCRIBE_L = ["BackArm", "Robe", "Stole", "Head", "Book", "FrontArm", "Quill", "FX"]
SC_NEU = dict(P=(12.6, 42.0), C=(13.4, 27.6), Hd=(14.8, 20.6), hf=(20.2, 31.6), qang=-62, hb=None,
              book=(24.0, 30.0), flip=-1, jaw=0, hem=0, sway=0.0, glow=1.0)
SCP = mk(SC_NEU)
SKULL_KEY = {"K": "OUT", "u": "U2", "v": "U3", "w": "U4", "o": "U0", "d": "B2", "b": "B3", "B": "B4", "C": "B5",
             "r": "Q3", "m": "OUT"}
SKULL = [
    ".....KK....",
    "....KwvK...",
    "...KwvvuK..",
    "..KwvvvvuK.",
    "..KwvvooouK",
    ".KwvvooBBoK",
    ".KwvooBCCBK",
    "KuwvoBBKKCK",
    "KuwvodBKKbK",
    "KuuvodBBdBK",
    "KuuvoddBbBK",
    ".KuuvoBdBdK",
    ".KuuvvodbK.",
    "..KuuuuKK..",
]
SKULL_TALK = list(SKULL)
SKULL_TALK[11] = ".KuuvoBdBdK"
SKULL_TALK[12] = ".KuuvooKKK."
SKULL_TALK.insert(13, "..KuuvodbK.")
SKULL_TALK[14] = "..KuuuuKK.."
BOOK = [
    ".KKKK.KKKK.",
    "KCCdCKBBCBK",
    "KCdCCKBdBBK",
    "KCCCdKBBdbK",
    "KrrrrKrrrrK",
    ".KKKKKKKKK.",
]
BOOK_KEY = {"K": "OUT", "C": "B5", "B": "B4", "b": "B3", "d": "B2", "r": "R2"}


def draw_scribe(p, fi, sw):
    Ls = {n: Layer(n) for n in SCRIBE_L if n != "FX"}
    FX = Glow("FX")
    Ls["FX"] = FX
    R = ID
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    floor = K.H - 1.0
    shF, shB = F(1.2, -ln + 1.4), F(-1.8, -ln + 1.6)
    s = p["sway"]
    if p["hb"]:
        arm(R, Ls["BackArm"], shB, p["hb"], 5.2, 5.4, 1.4, 1.8, "U", bias=-1, fist="B", fist_r=0.9, pref=(0, 1))
    # ---- robe: tall narrow column, flaring slightly, gold-edged hem
    Rb = Ls["Robe"]
    hem = floor + 0.4
    pts = [F(-2.8, -ln + 0.2), F(2.4, -ln - 0.2), F(3.0, -8.0), F(3.4, 2.0), (P[0] + 5.2 + s * 0.3, hem - 1.0)]
    n = 7
    for i in range(n + 1):
        t = i / n
        x = P[0] + 5.2 + s * 0.3 - 10.8 * t + s * 0.6 * t
        pts.append((x, hem + (0.8 if (i + p["hem"]) % 3 == 1 else 0.0)))
    pts += [(P[0] - 5.6 + s * 0.8, hem - 1.2), F(-3.8, 2.0), F(-3.4, -8.0)]
    m = R.mask(pts)
    Rb.paint(n_plate(m, 2.0, (-0.1, 0.0), 1.0,
                     fold=lambda x, y: (0.55 * math.sin((x - P[0] - s * 0.3) * 1.3) * min(1.0, max(0.0, (y - P[1] + 10) / 12)), 0)),
             "U", bias=0)
    ybot = max(q[1] for q in m)
    Rb.decal([q for q in m if q[1] == ybot - 1 or q[1] == ybot], ("G", 2))
    Rb.decal([q for q in m if q[1] == ybot - 1 and q[0] % 2 == 1], ("G", 3))
    R.dline(Rb, F(-3.2, -9.0), F(2.8, -9.4), ("L", 2))       # sash
    # scroll cases at the hip
    for k, dx in enumerate((-3.6, -2.2)):
        a0 = F(dx, -8.4)
        R.cap(Rb, a0, add(a0, (-0.4, 4.2 - k)), 0.8, 0.8, "L", bias=0, ao=0)
        Rb.decal([ip(add(a0, (-0.4, 4.2 - k)))], ("G", 3))
    # ---- stole: gold-embroidered band down the front edge
    St = Ls["Stole"]
    sp = [F(0.6, -ln - 0.2), F(2.6, -ln + 0.2), F(3.4, 8.0), (P[0] + 4.4 + s * 0.35, hem - 3.0),
          (P[0] + 2.6 + s * 0.35, hem - 2.2), F(1.2, 8.0)]
    sm = R.mask(sp)
    St.paint(n_plate(sm, 1.0, (-0.2, 0.0), 0.6), "G", bias=-1)
    St.decal([q for q in sm if q[1] % 5 == 0 and (q[0] + 1, q[1]) in sm], ("G", 4))   # embroidered glyphs
    St.decal([q for q in sm if q[1] >= max(r[1] for r in sm) - 0.5], ("G", 3))
    # ---- head
    stamp(Ls["Head"], SKULL_TALK if p["jaw"] else SKULL, SKULL_KEY, (int(round(Hd[0])) - 5, int(round(Hd[1])) - 7))
    er = (int(round(Hd[0])) - 5 + 8, int(round(Hd[1])) - 7 + 8)
    FX.put([er], "Q3", 255)
    FX.put([(er[0], er[1] - 1)], "Q1", 255)
    # ---- the floating book
    bx, by = p["book"]
    org = (int(round(bx)) - 5, int(round(by)) - 3)
    stamp(Ls["Book"], BOOK, BOOK_KEY, org)
    bk = Ls["Book"]
    if p["flip"] >= 0:            # a page turning over the spine (right -> left)
        t = p["flip"]
        sx0 = org[0] + 5
        tip = (sx0 + math.cos(math.pi * t) * 4.2, org[1] + 1 - math.sin(math.pi * t) * 3.2)
        bk.fixed({q: "B5" for q in line((sx0, org[1] + 1), tip)})
        bk.fixed({q: "B4" for q in line((sx0, org[1] + 2), (tip[0], tip[1] + 1))})
    gl = p["glow"]
    FX.halo((bx + .5, by - 1.0), 4.0, 7.5, "Y1", (int(34 * gl), int(16 * gl)))
    for k in range(3):             # glyph motes rising off the pages
        ph = (fi / 6.0 + k / 3.0) % 1.0
        q = ip((bx - 2 + k * 2.2 + math.sin(ph * 6 + k) * 1.0, by - 3 - ph * 9))
        FX.put([q], "Y2" if ph < 0.4 else "G4", 255 if ph < 0.7 else 150)
    # ---- near arm: wide sleeve, bony hand holding the quill over the page
    Fa = Ls["FrontArm"]
    el = arm(R, Fa, shF, p["hf"], 5.0, 5.2, 1.5, 2.1, "U", bias=0, fist="B", fist_r=0.9, pref=(-0.4, 1))
    cuff = lerp(el, p["hf"], 0.7)
    cm = R.dome(Fa, cuff, 2.0, 1.8, "U", bias=1)
    Fa.decal([q for q in cm if (q[0] + 1, q[1]) not in cm], ("G", 3))
    Q = Ls["Quill"]
    ca, sa = dirv(p["qang"])
    h = p["hf"]
    nib = (h[0] - ca * 1.5, h[1] - sa * 1.5)
    tip = (h[0] + ca * 8.0, h[1] + sa * 8.0)
    qp = {q: "B5" for q in line(nib, tip)}
    for k in range(3, 8):          # feather vane on the lower side
        b = (h[0] + ca * k + sa * 1.0, h[1] + sa * k - ca * 1.0)
        qp.setdefault(ip(b), "B3" if k % 2 else "B4")
    qp[ip(nib)] = "I1"
    Q.fixed(qp)
    return Ls, {"rim": [((bx, by - 1), 11, (255, 214, 140), (60, 44, 30), ["Robe", "Stole", "Head", "FrontArm", "BackArm"], 0.45)]}


def scribe_idle():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        bob = math.sin(ph)
        wr = (0, 1, 0, -1, 0, 1)[i] * 0.6
        fr.append((150, SCP(book=(24.0, 30.0 + bob * 1.2), hf=(19.6 + wr, 31.4 + 0.3 * abs(wr)), qang=-62 + wr * 6,
                            C=(13.4, 27.6 + 0.4 * (1 + bob) * 0.5), Hd=(14.8, 20.6 + 0.4 * (1 + bob) * 0.5), hem=i,
                            flip=(-1, -1, 0.15, 0.5, 0.85, -1)[i], sway=0.5 * math.sin(ph), glow=1.0 + 0.2 * bob)))
    return fr


def scribe_talk():
    fr = []
    for i in range(4):
        bob = (0, 1, 0, -1)[i]
        fr.append((170, SCP(book=(24.4, 30.4 + bob * 0.8), hf=(19.2, 30.2 - 0.5 * (i % 2)), qang=-48 - 6 * (i % 2),
                            Hd=(15.0, 20.4 + 0.3 * (i % 2)), jaw=(1, 0, 1, 0)[i], hem=i, flip=-1)))
    return fr


def build_scribe():
    SHEETS["npc_scribe"] = (32, 56) + build_sheet("npc_scribe", 32, 56, SCRIBE_L, draw_scribe,
                                                   [("idle", scribe_idle), ("talk", scribe_talk)])


# =========================================================================== SER KALDEN (NPC)
KAL_L = ["Cape", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "Weapon", "FrontArm", "FX"]
KSWORD = dict(pommel=-3.2, grip_end=1.6, grip="L2", grip_w=0.7, pommel_c="G4", guard=(1.8, 2.8, 4.4), guard_c="G3",
              guard_hi="G4", b0=2.8, end=18.6, w_edge=2.0, w_spine=1.6, taper=0.14, fuller="X2",
              edge_hi="K4", edge="K2", spine="K1")
K_NEU = dict(P=(19.0, 36.4), C=(19.8, 27.4), Hd=(21.0, 20.8), hup=(0.1, -1), fb=(14.6, 47), ff=(23.6, 47),
             hf=(28.6, 27.4), hb=(27.8, 28.6), grip=(28.4, 29.6), kb=None, kf=None, sway=0.0, hem=0, bow=0.0,
             talk=0)
KP = mk(K_NEU)


def draw_kalden(p, fi, sw):
    Ls = {n: Layer(n) for n in KAL_L if n != "FX"}
    FX = Glow("FX")
    Ls["FX"] = FX
    R = ID
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(1.6, -ln + 1.6), F(-2.6, -ln + 1.8)
    hB, hF = F(-2.0, 0.6), F(2.0, 0.6)
    floor = K.H - 1
    # ---- greatsword planted point-down (black blade, teal-gold filigree)
    pix, blade, tip = blade_px(ID, p["grip"], 90, KSWORD)
    pix = {q: c for q, c in pix.items() if q[1] <= floor}
    gx = p["grip"][0]
    for q in list(pix):                     # filigree: gold flecks climbing the teal fuller
        if q in blade and pix[q] == "X2" and (q[1] % 3 == 0):
            pix[q] = "G4" if q[1] % 2 else "X4"
    Ls["Weapon"].fixed(pix)
    # ---- tattered blue cloak
    Cp = Ls["Cape"]
    s = p["sway"]
    ctop = F(-2.4, -ln - 0.2)
    hem = floor - 2.4 + p["bow"] * 1.0
    pts = [add(ctop, (3.4, -0.6)), F(0.6, -ln + 2.0), F(-2.6, 0.0), (P[0] - 3.0 + s * 0.3, hem - 1.2)]
    n = 7
    x0, x1 = P[0] - 11.0 + s * 1.1, P[0] - 3.0 + s * 0.3
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = 2.6 * (0.3 + hash01(i, p["hem"] // 2, 41)) if i % 2 == 0 else 0.2
        pts.append((x, hem + d - 1.0))
    pts += [(P[0] - 10.2 + s * 1.0, P[1] + 1.0), add(ctop, (-3.6, 3.0))]
    cm = R.mask(pts)
    Cp.paint(n_plate(cm, 2.0, (0.2, 0.05), 1.0, fold=lambda x, y: (0.6 * math.sin((x - P[0] - s * 0.3) * 1.0), 0)),
             "Z", bias=0, ao=0)
    Cp.decal([q for q in cm if hash01(q[0], q[1], 43) < 0.05], ("Z", 1))
    # ---- back arm
    arm(R, Ls["BackArm"], shB, p["hb"], 5.0, 5.2, 1.8, 1.6, "E", bias=-1, fist_r=1.4, pref=(-1, 0.6))
    # ---- legs: white plate, teal-trimmed poleyns
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(R, Ls[nm], hip, ft, 5.6, 5.8, 2.1, 1.8, "E", bias=bias, flen=3.4, heel=1.6, boot_h=2.6, knee=kn)
        R.dome(Ls[nm], add(k, (0.5, 0.0)), 1.9, 1.7, "E", bias=bias)
        R.dline(Ls[nm], add(k, (-1.0, 1.6)), add(k, (1.4, 1.6)), ("X", 2 + bias))
    # ---- torso: breastplate, teal tabard, belt
    Bd = Ls["Body"]
    faulds = [F(-4.2, -1.4), F(3.8, -1.4), F(4.4, 3.2), F(-4.6, 3.2)]
    R.plate(Bd, faulds, "E", bevel=1.2, tilt=(0.0, 0.2), bias=-1)
    R.dline(Bd, F(-4.4, 0.8), F(4.2, 0.8), ("E", 1))
    torso = [F(-4.0, -0.6), F(-4.8, -ln + 2.8), F(-3.2, -ln - 1.0), F(2.0, -ln - 1.4), F(4.4, -ln + 1.0),
             F(4.6, -ln + 4.8), F(3.6, -0.6)]
    tm = R.plate(Bd, torso, "E", bevel=2.4, tilt=(-0.35, -0.15), strength=1.35)
    R.dline(Bd, F(1.2, -ln - 1.0), F(1.6, -1.6), ("E", 5))           # ridge
    R.dline(Bd, F(-3.0, -ln - 0.8), F(2.0, -ln - 1.2), ("X", 3))       # teal neck trim
    R.dline(Bd, F(-4.0, -1.0), F(3.8, -1.0), ("L", 2))                 # belt
    R.decal(Bd, [F(2.4, -1.0)], ("G", 3))
    # battle damage: dents + scratches
    for (a, b) in ((-1.6, -ln + 3.0), (2.8, -ln + 5.4), (-2.4, -3.2)):
        R.decal(Bd, [F(a, b)], ("E", 1))
        R.decal(Bd, [F(a + 0.8, b - 0.8)], ("E", 4))
    R.dline(Bd, F(-0.6, -ln + 5.0), F(1.2, -ln + 6.6), ("E", 2))
    tab = [F(0.2, -1.6), F(3.6, -1.6), F(4.2, 7.8), F(3.0, 6.8), F(2.0, 8.6), F(0.8, 7.2), F(-0.2, 8.0)]
    tb = R.plate(Bd, tab, "Z", bevel=1.0, tilt=(-0.2, 0.0), fold=lambda x, y: (0.4 * math.sin(x * 1.5), 0), bias=0)
    Bd.decal([q for q in tb if (q[0] - 1, q[1]) not in tb], ("X", 3))
    R.cap(Bd, F(0.3, -ln - 0.6), add(Hd, (-0.6, 3.6)), 1.9, 1.8, "E", bias=-1)    # gorget
    # ---- head: white great helm, teal visor band, tattered teal plume
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    sp_ = p["sway"]
    plume = [G(-0.6, -3.6), G(0.4, -4.8), G(-1.8, -4.8), G(-4.2, -3.2), G(-6.0, -0.4 + sp_ * 0.3),
             G(-6.6, 2.8 + sp_ * 0.4), G(-5.4, 1.6), G(-5.8, 3.8 + sp_ * 0.4), G(-4.4, 0.4), G(-2.6, -2.2)]
    pm = R.plate(Hl, plume, "X", bevel=1.0, tilt=(0.0, -0.3), strength=1.0, bias=0)
    helm = [G(-3.2, 3.6), G(-3.6, -1.4), G(-2.6, -3.8), G(1.6, -4.2), G(3.4, -2.4), G(3.8, 1.0), G(3.2, 3.6)]
    hm = R.plate(Hl, helm, "E", bevel=1.6, tilt=(-0.3, -0.2), strength=1.3)
    R.dline(Hl, G(1.4, -1.0), G(3.8, -1.0), ("X", 2))            # teal visor band
    R.dline(Hl, G(2.0, -0.4), G(3.8, -0.4), "OUT")               # eye slit
    R.dline(Hl, G(-3.0, 3.2), G(3.0, 3.2), ("X", 3))
    R.decal(Hl, [G(-1.2, -2.6)], ("E", 1))                       # dent
    R.decal(Hl, [G(2.6, 1.4), G(2.6, 2.2)], "OUT")               # breaths
    # ---- near arm + pauldron (teal rim)
    Fa = Ls["FrontArm"]
    arm(R, Fa, shF, p["hf"], 5.0, 5.2, 1.9, 1.7, "E", bias=0, fist_r=1.5, pref=(-1, 0.7))
    for (dx, dy, rx, ry) in ((0.4, 1.2, 3.0, 2.0), (0.0, -0.6, 3.4, 2.6)):
        m = R.dome(Fa, add(shF, (dx, dy)), rx, ry, "E", tilt=(0.05, 0.1))
        Fa.decal([q for q in m if (q[0], q[1] + 1) not in m], ("X", 3))
    R.decal(Fa, [add(shF, (-0.6, -2.0))], ("E", 1))
    return Ls, {}


def kal_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((220, KP(C=(19.8, 27.4 + b * 0.5), Hd=(21.0, 20.8 + b * 0.5), hf=(28.6, 27.4 + b * 0.2),
                           hb=(27.8, 28.6 + b * 0.2), sway=(0, 0.6, 1.0, 0.6)[i], hem=i)))
    return fr


def kal_talk():
    fr = []
    for i in range(4):
        b = (0, 0.4, 0.2, 0.5)[i]
        fr.append((200, KP(C=(19.6, 27.2 + b * 0.4), Hd=(20.8, 20.4 + b * 0.4), hup=(-0.05 + 0.08 * (i % 2), -1),
                           hf=(28.6, 27.4), hb=(24.6 + 0.6 * (i % 2), 26.8 - 0.8 * (i % 2)), sway=(0.4, 0.8, 0.4, 0)[i],
                           hem=i)))
    return fr


def kal_kneel():
    return [(1000, KP(P=(18.6, 41.0), C=(20.4, 32.4), Hd=(22.6, 27.2), hup=(0.55, -1), fb=(12.4, 47), ff=(24.4, 47),
                      kb=(15.6, 46.2), kf=(26.0, 39.4), hf=(28.6, 30.4), hb=(27.6, 31.6), grip=(28.4, 32.6), bow=1.0))]


def build_kalden():
    SHEETS["npc_kalden"] = (48, 48) + build_sheet("npc_kalden", 48, 48, KAL_L, draw_kalden,
                                                   [("idle", kal_idle), ("talk", kal_talk), ("kneel", kal_kneel)])


# =========================================================================== PORTRAITS (64x64)
PW = 64
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _bt(x, y):
    return (BAYER[y & 3][x & 3] + 0.5) / 16.0


def _pick(ramp, v, x, y):
    v = max(0.0, min(1.0, v))
    f = v * (len(ramp) - 1)
    i = int(f)
    if f - i > _bt(x, y):
        i += 1
    return ramp[min(i, len(ramp) - 1)]


def arch_inside(x, y, inset=0):
    """tombstone window: round top (centre 31.5,30 r 28), straight sides, flat bottom."""
    x0, x1, y1 = 4 + inset, 59 - inset, 59 - inset
    if not (x0 <= x <= x1 and y <= y1):
        return False
    if y >= 30:
        return True
    return (x + .5 - 32) ** 2 + (y + .5 - 30.5) ** 2 <= (28.0 - inset) ** 2


def backdrop(ramp, glow_at, glow_r=26, glow_amt=0.55):
    img = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    px = img.load()
    for y in range(PW):
        for x in range(PW):
            if arch_inside(x, y):
                d = math.hypot(x - glow_at[0], y - glow_at[1]) / glow_r
                v = 0.10 + 0.25 * (y / 64) + glow_amt * max(0.0, 1 - d) ** 1.6
                px[x, y] = tuple(int(c) for c in ramp_col(ramp, v, x, y))
    return img


def ramp_col(ramp, v, x, y):
    c = _pick(ramp, v, x, y)
    return rgba(c) if isinstance(c, str) else c


def frame_img(accent="G"):
    """Ornate arched frame: outline, gold moulding, dark inner lip, corner studs; outside transparent."""
    img = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    px = img.load()
    for y in range(PW):
        for x in range(PW):
            a0 = arch_inside(x, y, -3)
            if not a0:
                continue
            if arch_inside(x, y, 0):
                continue
            # ring depth: 3 = outermost
            if not arch_inside(x, y, -2):
                c = "OUT"
            elif not arch_inside(x, y, -1):
                lit = (x + y) < 64 and y < 50
                c = "G4" if lit and (x < 32 or y < 12) else "G3" if lit else "G2"
            else:
                c = "G1"
            px[x, y] = rgba(c)
    # keystone + base studs
    for (cx, cy) in ((32, 2), (4, 59), (59, 59), (4, 30), (59, 30)):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if abs(dx) + abs(dy) <= 1:
                    px[cx + dx, cy + dy] = rgba("G4" if (dx, dy) in ((0, -1), (-1, 0), (0, 0)) else "G2")
        for (dx, dy) in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            if 0 <= cx + dx < PW and 0 <= cy + dy < PW and px[cx + dx, cy + dy][3] == 0:
                px[cx + dx, cy + dy] = rgba("OUT")
    return img


def clip_arch(img, inset=0):
    out = img.copy()
    px = out.load()
    for y in range(PW):
        for x in range(PW):
            if not arch_inside(x, y, inset):
                px[x, y] = (0, 0, 0, 0)
    return out


def portrait(name, bg_ramp, glow_at, draw, rims=(), glow_r=26, glow_amt=0.55):
    K.setup(PW, PW)
    Ls = draw()
    order = [n for n in Ls]
    imgs = render(Ls, order)
    for (src, rad, col, dark, names, st) in rims:
        imgs = rim_light(imgs, names, src, rad, col, dark, st)
    fig = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    for n in order:
        fig.alpha_composite(imgs[n])
    layers = {"Backdrop": backdrop(bg_ramp, glow_at, glow_r, glow_amt), "Figure": clip_arch(fig),
              "Frame": frame_img()}
    flat = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    for n in ("Backdrop", "Figure", "Frame"):
        flat.alpha_composite(layers[n])
    PORTRAITS[name] = flat
    if BUILD:
        asebuild.build(name, PW, PW, ["Backdrop", "Figure", "Frame"], [{"ms": 1000, "cels": layers}], [("p", 0, 0)])
    zd = os.environ.get("NPCZOOM")
    if zd:
        flat.resize((PW * 8, PW * 8), Image.NEAREST).save(os.path.join(zd, f"{name}_zoom.png"))


# ---------------------------------------------------------------- the Ashbound knight (player)
def draw_p_player():
    Ls = {n: Layer(n) for n in ("Cape", "Body", "Head", "Face")}
    Ls["Glint"] = Glow("Glint")
    R = ID
    # crimson mantle draped over both shoulders, gathered high behind the helm
    cape = [(0, 64), (2, 50), (8, 42), (14, 36), (22, 33), (40, 36), (52, 40), (60, 48), (64, 56), (64, 64)]
    cm = R.mask(cape)
    Ls["Cape"].paint(n_plate(cm, 5.0, (-0.15, -0.1), 1.3,
                             fold=lambda x, y: (0.55 * math.sin(x * 0.42 + y * 0.08) * min(1, max(0, (y - 40) / 10)), 0)),
                     "C", bias=0)
    # pauldrons (blackened steel, layered lames)
    Bd = Ls["Body"]
    for (c, rx, ry, b) in (((13, 54), 11, 9, -1), ((50, 53), 12, 10, 0)):
        m = R.dome(Bd, c, rx, ry, "K", bias=b, tilt=(0.0, -0.15))
        for k in (3, 6):
            Bd.decal([q for q in m if q[1] == c[1] + k], ("K", 1))
        Bd.decal([q for q in m if q[1] == c[1] - ry + 2 and abs(q[0] - c[0]) < rx - 3], ("G", 3))
    R.plate(Bd, [(22, 64), (23, 49), (29, 44), (40, 44), (45, 49), (46, 64)], "K", bevel=3, tilt=(-0.2, -0.3), bias=-1)
    R.dline(Bd, (35, 46), (35, 64), ("K", 4))
    # helm: rounded great helm in 3/4 (face toward the right), crest spike at the back
    Hl = Ls["Head"]
    R.plate(Hl, [(20, 16), (22, 5), (25, 1), (27, 6), (28, 15)], "K", bevel=1.5, tilt=(-0.4, -0.3), strength=1.2)
    hm = R.dome(Hl, (31.5, 27.5), 14.5, 15.5, "K", tilt=(-0.05, -0.05))
    # face plate (the front of the helm, catching the key light on its ridge)
    Fc = Ls["Face"]
    face = [(35, 13), (42, 15), (47, 20), (49.5, 27), (49, 35), (46, 42), (38, 44), (35, 30)]
    fm = R.plate(Fc, face, "K", bevel=3.0, tilt=(0.25, -0.1), strength=1.5)
    R.dline(Fc, (38, 14), (41, 43), ("K", 5))        # ridge highlight
    R.dline(Fc, (39, 14), (42, 43), ("K", 2))
    # visor slit (wraps around the helm) with the red glow
    slit = polyline([(19, 25), (27, 27), (35, 27), (43, 26), (49, 25)])
    for (x, y) in slit:
        for dy in (0, 1):
            Hl.decal([(x, y + dy)], "OUT")
            Fc.decal([(x, y + dy)], "OUT")
    for (x, y) in slit:
        if 36 <= x <= 48:
            Ls["Glint"].put([(x, y)], (240, 36, 50, 255))
            if 39 <= x <= 45:
                Ls["Glint"].put([(x, y)], (255, 150, 120, 255))
            Ls["Glint"].put([(x, y - 1)], (240, 36, 50, 70))
            Ls["Glint"].put([(x, y + 2)], (240, 36, 50, 50))
    # breaths on the cheek, rivets, gold neck band, scratches
    for k, y in enumerate((32, 34, 36)):
        R.dline(Fc, (43, y), (46, y - 0.5), "OUT")
    for (x, y) in ((22, 19), (21, 33), (27, 38)):
        Hl.decal([(x, y)], ("K", 5))
        Hl.decal([(x + 1, y + 1)], ("K", 0))
    R.dline(Hl, (19, 40), (34, 44), ("G", 2))
    R.dline(Fc, (35, 44), (46, 42), ("G", 3))
    Hl.decal([(24, 12), (25, 13), (26, 13)], ("K", 1))
    return Ls


def vein(L, pts, seed, bright=True):
    """a thin root-like gold vein along pts (1px), glinting every few pixels."""
    path = polyline(pts)
    L.fixed({q: ("Y1" if i % 4 == 1 else "G3") if bright else "G2" for i, q in enumerate(path)})


# ---------------------------------------------------------------- Sister Venn
def draw_p_venn():
    Ls = {n: Layer(n) for n in ("Robe", "Neck", "Face", "Hood")}
    Ls["Veins"] = Layer("Veins")
    R = ID
    # robe + collar
    Rb = Ls["Robe"]
    rb = [(4, 64), (8, 54), (18, 48), (30, 50), (46, 50), (56, 54), (62, 64)]
    R.plate(Rb, rb, "N", bevel=4, tilt=(-0.1, -0.2), fold=lambda x, y: (0.4 * math.sin(x * 0.5), 0), bias=0)
    # neck
    Ls["Neck"].light = (0.5, 0.2, 0.85)
    R.cap(Ls["Neck"], (38, 42), (39, 56), 4.6, 5.0, "f", bias=-1)
    # face (3/4 right): soft jaw, small nose, lidded gold eyes
    face = [(29, 22), (34, 18), (41, 18), (45, 21), (46.5, 27), (47.2, 31), (48.6, 35.2), (47.2, 36.6), (47.4, 38.8),
            (46.4, 40.6), (45.2, 43.6), (41.5, 46.2), (36, 45.4), (31, 40), (28.5, 33)]
    Fc = Ls["Face"]
    Fc.light = (0.5, 0.2, 0.85)            # lit from the lantern, low and to the right
    fm = R.mask(face)
    Fc.paint(n_ell(fm, (40, 32), 13, 17, 0.9), "f", bias=0)
    for (x0, x1, y, far) in ((34, 39, 30, False), (42.5, 45.5, 30, True)):
        R.dline(Fc, (x0, y - 1), (x1, y - 1), "OUT")               # lashes / upper lid
        Fc.decal([(int(x1), y - 2)] if not far else [], "OUT")       # outer flick
        R.dline(Fc, (x0 + 0.5, y - 2), (x1 - 1, y - 2), ("f", 4))   # lid highlight
        ix = int(x1) - 2 if not far else int(x1) - 1
        Fc.decal([(ix, y), (ix - 1, y)] if not far else [(ix, y)], "G4")
        Fc.decal([(ix - (2 if not far else 1), y)], ("f", 1))
        Fc.decal([(x, y + 1) for x in range(int(x0) + 1, int(x1))], ("f", 3))
    R.dline(Fc, (33, 26.5), (38.5, 25.8), ("H", 3))                  # fine brows
    R.dline(Fc, (42.5, 26), (45, 26.6), ("H", 3))
    Fc.decal([(47, 35), (46, 36)], ("f", 1))                          # nostril shadow
    R.dline(Fc, (43.6, 39.6), (46, 39.4), ("f", 1))                   # lips
    Fc.decal([(44, 40), (45, 40)], ("C", 4))
    # hood: heavy pale cowl framing the face, deep shadow inside the rim
    Hd = Ls["Hood"]
    hood = [(6, 64), (8, 44), (12, 26), (20, 12), (30, 6), (42, 7), (51, 12), (56, 20), (58, 30), (57, 42), (53, 44),
            (51, 30), (46, 19), (36, 15.5), (29, 19), (26, 28), (27, 40), (32, 48), (26, 52), (18, 56), (14, 64)]
    hm = R.plate(Hd, hood, "N", bevel=5.0, tilt=(-0.2, -0.15), strength=1.3,
                 fold=lambda x, y: (0.35 * math.sin(x * 0.35 + y * 0.2), 0))
    inner = [q for q in hm if any((q[0] + a, q[1] + b) in fm for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2))]
    Hd.decal(inner, ("N", 1))
    Hd.decal([q for q in hm if (q[0] + 1, q[1]) in fm or (q[0] - 1, q[1]) in fm or (q[0], q[1] + 1) in fm], ("N", 0))
    # a lock of pale hair escaping the hood along the temple
    for k in range(3):
        R.dline(Fc, (30 + k * 1.4, 19), (28.6 + k * 0.8, 31 - k * 3), ("H", 4 - k % 2))
    # gold veins rising from the collar up the throat to the jaw
    V = Ls["Veins"]
    vein(V, [(36, 55), (36.5, 50), (36, 47.5)], 1)
    vein(V, [(36.5, 50), (38, 48.5)], 4, bright=False)
    vein(V, [(42, 54), (42.6, 49), (44, 45.5)], 2)
    vein(V, [(44, 45.5), (45.5, 43.5)], 3, bright=False)
    return Ls


# ---------------------------------------------------------------- Old Ashwright
def draw_p_ash():
    Ls = {n: Layer(n) for n in ("Body", "Gold", "Head", "Beard")}
    R = ID
    Bd = Ls["Body"]
    # jerkin + soot-black apron bib + neck strap
    R.plate(Bd, [(0, 64), (2, 50), (12, 43), (30, 42), (52, 44), (62, 52), (64, 64)], "A", bevel=4, tilt=(-0.1, -0.2), bias=-1)
    R.plate(Bd, [(26, 64), (28, 52), (48, 50), (54, 64)], "J", bevel=2.5, tilt=(-0.2, -0.1), bias=0)
    R.dline(Bd, (29, 52), (36, 40), ("J", 3))
    R.dline(Bd, (47, 50), (46, 40), ("J", 3))
    # the gold prosthetic shoulder + upper arm (near side), riveted plates
    Gd = Ls["Gold"]
    m = R.dome(Gd, (13, 52), 12, 10, "G", tilt=(0.0, -0.1))
    for k in (4, 8):
        Gd.decal([q for q in m if q[1] == 52 + k - 6 + (q[0] - 13) // 6], ("G", 1))
    for (x, y) in ((8, 47), (14, 45), (20, 47), (6, 55), (19, 56)):
        Gd.decal([(x, y)], ("G", 5))
        Gd.decal([(x + 1, y + 1)], ("G", 1))
    R.dline(Gd, (4, 44), (24, 60), ("J", 2))            # harness strap across the joint
    R.dline(Gd, (5, 44), (25, 60), ("J", 3))
    # head: broad bald dome in 3/4, heavy brow, big nose
    Hd = Ls["Head"]
    head = [(20, 20), (24, 11), (32, 6), (41, 6), (48, 11), (51, 19), (52, 25), (55, 31), (53.5, 34), (52, 38),
            (46, 44), (30, 44), (22, 36), (19, 28)]
    hm = R.mask(head)
    Hd.light = (0.45, -0.35, 0.8)          # forge light from the right, a little overhead
    Hd.paint(n_ell(hm, (36, 22), 18, 21, 0.9), "S", bias=1)
    Hd.decal([q for q in hm if hash01(q[0] // 3, q[1] // 2, 71) < 0.1 and 12 < q[1] < 20 and q[0] < 40], ("S", 2))
    R.dline(Hd, (30, 10), (35, 8), ("S", 4))                                     # scalp shine
    R.dline(Hd, (29, 11), (31, 10), ("S", 4))
    # ear
    em = R.dome(Hd, (26, 28), 2.4, 3.6, "S", bias=0)
    Hd.decal([(26, 28), (26, 29)], ("S", 1))
    # brow ridge + deep-set eyes that catch the forge light
    R.dline(Hd, (34, 22), (44, 21), ("H", 2))
    R.dline(Hd, (34, 23), (44, 22), ("H", 3))
    R.dline(Hd, (46, 22), (50, 22.5), ("H", 3))
    R.dline(Hd, (35, 25), (41, 25), ("S", 0))
    R.dline(Hd, (36, 26), (40, 26), ("S", 1))
    Hd.decal([(39, 25)], "O4")
    Hd.decal([(47, 25), (48, 25)], ("S", 0))
    Hd.decal([(48, 25)], "O3")
    R.dline(Hd, (33, 20), (38, 18.5), ("S", 2))        # forehead creases
    R.dline(Hd, (36, 16), (43, 15.5), ("S", 2))
    # nose
    R.dline(Hd, (50, 24), (54, 31), ("S", 3))
    Hd.decal([(52, 32), (51, 33), (50, 33)], ("S", 1))
    # beard: great soot-grey cascade over the chest, moustache
    Br = Ls["Beard"]
    beard = [(30, 30), (36, 33), (46, 33), (53, 34), (55, 40), (54, 50), (50, 58), (46, 64), (30, 64), (27, 54),
             (26, 42), (27, 35)]
    bm = R.mask(beard)
    Br.paint(n_ell(bm, (40, 42), 16, 22, 0.8), "H", bias=1)
    for k in range(9):          # combed strands
        x0 = 30 + k * 3
        Br.decal(polyline([(x0, 36 + (k % 3)), (x0 - 1 + (k % 2), 48), (x0 - 2, 62)]), ("H", 1 if k % 2 else 2))
    R.dline(Br, (44, 36), (53, 36), ("H", 4))             # moustache
    R.dline(Br, (43, 37), (52, 38), ("H", 3))
    R.dline(Br, (46, 39), (51, 39), ("H", 1))             # mouth shadow
    return Ls


# ---------------------------------------------------------------- the Hollow Scribe
def draw_p_scribe():
    Ls = {n: Layer(n) for n in ("Robe", "Hood", "Skull", "Jaw", "Quill")}
    Ls["Glint"] = Glow("Glint")
    R = ID
    R.plate(Ls["Robe"], [(2, 64), (6, 50), (18, 44), (46, 44), (58, 50), (62, 64)], "U", bevel=4, tilt=(-0.1, -0.2),
            fold=lambda x, y: (0.4 * math.sin(x * 0.5), 0))
    # gold-embroidered stole
    st = R.plate(Ls["Robe"], [(38, 46), (46, 46), (50, 64), (40, 64)], "G", bevel=1.5, tilt=(-0.2, 0.0), bias=-1)
    Ls["Robe"].decal([q for q in st if q[1] % 4 == 0 and q[0] % 2 == 0], ("G", 4))
    # tall pointed cowl
    Hd = Ls["Hood"]
    hood = [(6, 64), (8, 46), (12, 30), (18, 16), (26, 6), (34, 1), (40, 4), (48, 12), (54, 24), (56, 38), (55, 48),
            (50, 46), (50, 30), (45, 19), (36, 15), (28, 20), (24, 32), (26, 46), (30, 52), (20, 56), (14, 64)]
    hm = R.plate(Hd, hood, "U", bevel=5.0, tilt=(-0.2, -0.15), strength=1.3,
                 fold=lambda x, y: (0.35 * math.sin(x * 0.3 + y * 0.15), 0))
    Hd.decal([q for q in hm if (q[0] + 1, q[1]) not in hm and q[0] > 44 and q[1] > 20], ("G", 3))   # gold hem
    # skull (3/4 right)
    Sk = Ls["Skull"]
    Sk.light = (0.35, 0.1, 0.9)
    skull = [(28, 26), (31, 18), (38, 15), (45, 17), (49, 23), (50.5, 30), (51, 36), (49, 40), (46, 42), (38, 42),
             (32, 40), (28, 34)]
    sm = R.mask(skull)
    Sk.paint(n_ell(sm, (40, 28), 14, 16, 0.9), "B", bias=0)
    # sockets: near large, far narrow; teal pinpoints
    near = mask_disc((39.5, 29.5), 3.4, 3.0)
    far = mask_disc((48.0, 29.5), 1.6, 2.6)
    Sk.decal(list(near | far), "OUT")
    Sk.decal([q for q in near if (q[0], q[1] - 1) not in near], ("B", 1))
    Sk.decal([(x, 26) for x in range(37, 43)], ("B", 5))                      # brow ridge
    Sk.decal([(x, 26) for x in range(46, 50)], ("B", 4))
    Ls["Glint"].put([(40, 30)], (180, 255, 236, 255))
    Ls["Glint"].put([(41, 30), (40, 29)], (79, 191, 168, 255))
    Ls["Glint"].put([(48, 30)], (79, 191, 168, 255))
    Ls["Glint"].put([(39, 29), (41, 31)], (79, 191, 168, 90))
    # nasal cavity, cheekbone, temple hollow, cracks
    Sk.decal([(46, 34), (47, 34), (46, 35), (47, 35), (46, 36)], "OUT")
    R.dline(Sk, (35, 35), (43, 36), ("B", 2))
    R.dline(Sk, (32, 27), (32, 34), ("B", 2))
    Sk.decal(polyline([(34, 19), (36, 22), (35, 24)]), ("B", 1))
    # jaw + teeth
    Jw = Ls["Jaw"]
    Jw.light = (0.35, 0.1, 0.9)
    jaw = [(35, 40), (47, 40), (49, 44), (45, 48), (38, 48), (34, 44)]
    jm = R.mask(jaw)
    Jw.paint(n_ell(jm, (42, 42), 10, 8), "B", bias=-1)
    for x in range(38, 49, 2):
        Jw.decal([(x, 40), (x, 41)], "OUT")
    for x in range(39, 49, 2):
        Jw.decal([(x, 40)], ("B", 5))
    # the quill, rising from below
    Q = Ls["Quill"]
    qp = {}
    for i, q in enumerate(line((60, 64), (52, 40))):
        qp[q] = "B5"
    for k in range(4, 20):
        t = k / 24
        cx, cy = 60 - 8 * t, 64 - 24 * t
        for d in range(1, 3 + (k % 3 == 0)):
            qp.setdefault((int(cx + d), int(cy + d * 0.3)), "B4" if d == 1 else "B3")
    Q.fixed(qp)
    return Ls


# ---------------------------------------------------------------- Ser Kalden
def draw_p_kalden():
    Ls = {n: Layer(n) for n in ("Cloak", "Plume", "Plate", "Helm", "Visor")}
    Ls["Glint"] = Glow("Glint")
    R = ID
    # tattered blue cloak over the shoulders
    Ls["Cloak"].paint(n_plate(R.mask([(0, 64), (2, 46), (14, 38), (30, 40), (50, 40), (62, 46), (64, 64)]), 4.0,
                              (-0.1, -0.1), 1.2, fold=lambda x, y: (0.5 * math.sin(x * 0.45), 0)), "Z", bias=0)
    # teal horsehair plume streaming back
    pl = [(26, 10), (30, 6), (26, 5), (18, 8), (10, 16), (5, 28), (4, 40), (9, 34), (8, 44), (13, 32), (16, 22),
          (22, 15)]
    pm = R.mask(pl)
    Ls["Plume"].paint(n_plate(pm, 2.0, (0.0, -0.2), 1.0, fold=lambda x, y: (0.8 * math.sin(x * 0.9 + y * 0.3), 0)),
                      "X", bias=0)
    # white pauldrons with teal rims, gorget
    Pt = Ls["Plate"]
    for (c, rx, ry, b) in (((12, 55), 12, 9, -1), ((52, 54), 12, 9, 0)):
        m = R.dome(Pt, c, rx, ry, "E", bias=b, tilt=(0.0, -0.15))
        Pt.decal([q for q in m if (q[0], q[1] - 1) not in m], ("X", 3))
        for (x, y) in ((c[0] - 5, c[1] - 2), (c[0] + 3, c[1] + 1)):
            Pt.decal([(x, y)], ("E", 1))       # dents
            Pt.decal([(x - 1, y - 1)], ("E", 5))
    R.plate(Pt, [(22, 64), (23, 46), (30, 42), (42, 42), (46, 46), (46, 64)], "E", bevel=3, tilt=(-0.2, -0.3), bias=-1)
    R.dline(Pt, (34, 44), (34, 64), ("E", 4))
    R.dline(Pt, (24, 50), (45, 50), ("X", 2))
    # helm: tall white great helm, 3/4 right, battered
    Hl = Ls["Helm"]
    helm = [(21, 42), (19, 24), (22, 13), (30, 7), (40, 7), (47, 12), (50, 20), (51, 30), (50, 42)]
    hm = R.mask(helm)
    Hl.paint(n_ell(hm, (35, 24), 17, 22, 0.85), "E", bias=0)
    R.dline(Hl, (40, 8), (43, 41), ("E", 5))      # face ridge
    R.dline(Hl, (41, 8), (44, 41), ("E", 2))
    for (x, y) in ((26, 16), (31, 33), (47, 16)):  # dents & scratches
        Hl.decal([(x, y), (x + 1, y)], ("E", 1))
        Hl.decal([(x - 1, y - 1)], ("E", 5))
    Hl.decal(polyline([(24, 30), (28, 26), (29, 27)]), ("E", 2))
    # teal visor band + slit, gold filigree
    Vs = Ls["Visor"]
    band = R.mask([(20, 23), (51, 21), (51, 28), (20, 30)])
    Vs.paint(n_plate(band, 1.5, (0.0, -0.2), 1.0), "X", bias=0)
    R.dline(Vs, (27, 25.5), (51, 24), "OUT")
    R.dline(Vs, (27, 26.5), (51, 25), "OUT")
    Ls["Glint"].put([(44, 25)], (230, 240, 236, 255))                  # the man behind the steel
    Ls["Glint"].put([(38, 26)], (160, 190, 190, 255))
    for x in range(22, 50, 3):
        Vs.decal([(x, 22 + (x - 20) * -2 // 31)], ("G", 4))
    for k, y in enumerate((33, 35, 37)):                              # breaths
        R.dline(Hl, (44, y), (48, y - 0.5), "OUT")
    R.dline(Hl, (20, 40), (50, 40), ("X", 3))
    R.dline(Hl, (20, 41), (50, 41), ("G", 3))
    return Ls


PORTRAIT_SPECS = {}


def build_portraits():
    portrait("portrait_player", ["K0", "C0", "C1", "C2", "C3"], (24, 22), draw_p_player,
             rims=[((70, 30), 44, (220, 70, 70), (60, 12, 20), ["Cape", "Body", "Head", "Face"], 0.45)],
             glow_r=30, glow_amt=0.45)
    # portrait_venn is drawn by art/gen_venn_portrait.py (redrawn from the user's reference)
    # portrait_ashwright is drawn by art/gen_ash_portrait.py (redrawn from the user's reference)
    portrait("portrait_scribe", ["U0", "U1", "U2", "X0", "X1"], (40, 30), draw_p_scribe,
             rims=[((64, 64), 40, (255, 214, 140), (70, 50, 30), ["Robe", "Hood", "Skull", "Jaw"], 0.45)],
             glow_r=30, glow_amt=0.55)
    portrait("portrait_kalden", ["Z0", "X0", "Z1", "X1", "Z2"], (26, 20), draw_p_kalden,
             rims=[((70, 20), 40, (120, 200, 190), (20, 50, 50), ["Cloak", "Plate", "Helm", "Plume"], 0.35)],
             glow_r=32, glow_amt=0.55)


# =========================================================================== driver
def build_sheet(name, w, h, layers, draw, anims, loops=()):
    K.setup(w, h)
    out = []
    for tag, fn in anims:
        lst = []
        for k, (ms, p) in enumerate(fn()):
            Ls, info = draw(p, k, 0.0)
            imgs = render(Ls, layers)
            for (src, rad, col, dark, names, st) in info.get("rim", []):
                imgs = rim_light(imgs, names, src, rad, col, dark, st)
            lst.append((ms, imgs))
        out.append((tag, lst))
    tags, flats = K.export(name, layers, out, None, build=BUILD)
    zd = os.environ.get("NPCZOOM")      # debug: 8x close-up on dark + grey backgrounds
    if zd:
        sc = 8
        sheet = Image.new("RGBA", (len(flats) * (w + 1) * sc, 2 * (h + 1) * sc), (0, 0, 0, 255))
        for r, bg in enumerate(((24, 22, 32, 255), K.BG_CELL)):
            for i, f in enumerate(flats):
                c = Image.new("RGBA", (w, h), bg)
                c.alpha_composite(f)
                sheet.paste(c.resize((w * sc, h * sc), Image.NEAREST), (i * (w + 1) * sc, r * (h + 1) * sc))
        sheet.save(os.path.join(zd, f"{name}_zoom.png"))
    return tags, flats


SHEETS = {}
PORTRAITS = {}


def build_venn():
    SHEETS["npc_venn"] = (32, 48) + build_sheet("npc_venn", 32, 48, VENN_L, draw_venn,
                                                 [("idle", venn_idle), ("talk", venn_talk)])


def preview_all():
    """art/previews/npcs.png: every sheet (4x), one row per tag, then the portraits."""
    sc = 4
    rows = []
    for name, (w, h, tags, flats) in SHEETS.items():
        for t, a, b in tags:
            rows.append((f"{name}  {t} ({b - a + 1})", w, h, flats[a:b + 1]))
    cols_w = max(len(r[3]) * (r[1] + 2) for r in rows) * sc if rows else 64
    tot_h = sum((r[2] + 12) * sc for r in rows)
    ports = PORTRAITS
    if ports:
        tot_h += (64 + 12) * sc
        cols_w = max(cols_w, len(ports) * 68 * sc)
    sheet = Image.new("RGBA", (cols_w + 8, tot_h + 8), K.BG)
    d = ImageDraw.Draw(sheet)
    y = 4
    for lab, w, h, fl in rows:
        d.text((4, y), lab, fill=(235, 235, 240, 255))
        for i, f in enumerate(fl):
            fr = Image.new("RGBA", (w, h), K.BG_CELL)
            fr.alpha_composite(f)
            sheet.alpha_composite(fr.resize((w * sc, h * sc), Image.NEAREST), (4 + i * (w + 2) * sc, y + 10 * sc // 2 + 6))
        y += (h + 12) * sc
    if ports:
        d.text((4, y), "portraits: " + "  ".join(ports), fill=(235, 235, 240, 255))
        for i, (nm, im) in enumerate(ports.items()):
            fr = Image.new("RGBA", (64, 64), K.BG_CELL)
            fr.alpha_composite(im)
            sheet.alpha_composite(fr.resize((64 * sc, 64 * sc), Image.NEAREST), (4 + i * 68 * sc, y + 26))
    sheet.save(os.path.join(ART, "previews", "npcs.png"))



BUILDERS = {"venn": build_venn, "ash": build_ash, "scribe": build_scribe, "kalden": build_kalden, "portraits": build_portraits}


def main():
    for k, fn in BUILDERS.items():
        if ONLY is None or k in ONLY:
            fn()
    preview_all()


if __name__ == "__main__":
    main()
