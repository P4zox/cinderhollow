#!/usr/bin/env python3
"""Phase 3 of the final boss -- "The Pale Root, Unbound": a vast serpentine star-beast (Elden-Beast-like).

    python3 art/gen_sovbeast.py              build every sheet (Aseprite) + previews
    python3 art/gen_sovbeast.py --preview    previews only

The body is not one giant sprite: it is assembled in the engine along a swimming spine, so it can coil and
swim freely around (and beyond) the screen.  Every piece is pre-rendered here, at every angle, with the same
normal-mapped material method as gen_sovereign.py (so edges stay crisp at any angle -- nothing is rotated at
runtime except thin light FX):

    sov_seg_RR   body capsule pieces, radius RR px, 16 angles over 180 deg; tags fill0..fill2 (star variants), line
                 (1px dark silhouette drawn first for every piece so the whole body gets one clean outline)
    sov_head     small elegant masked head, 17 angles (-90..90, engine mirrors for leftward), tags closed / open
    sov_fin      luminous root-ribbed fin sail, 17 angles x 2 sway frames (mirrored like the head), tags f0 / f1
    sov_tail     filament tail fan, 32 angles x 2 sway frames, tags t0 / t1
    sov_halo     the great ring that floats behind her neck, 8 frames (tag loop)
    fx_sov_*     beam, beam impact, star, meteor, ring wave, root whip, root spear, petal blade, orb, ring band,
                 floor mark, gravity well, root bind, transformation burst
    bg_sov_void_far / _mid   the starry void inside the Root's heart (phase-3 arena)

Palette: ivory/gold upper body (luminous), deep violet "cosmos" belly with star dust, gold filament threads.
"""
import math, os, sys, json
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild            # noqa: E402
import gen_sovereign as G  # noqa: E402  (material ramps, masks, Layer / render_layer, FXLayer)

# cosmic belly ramp
G.HEX.update({"K0": "#07061a", "K1": "#120e30", "K2": "#211a4c", "K3": "#34286c", "K4": "#4f3d92", "K5": "#7a66b8"})
for k in ("K0", "K1", "K2", "K3", "K4", "K5"):
    v = G.HEX[k]
    G.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
G.RAMP["K"] = ["K0", "K1", "K2", "K3", "K4", "K5"]
C = G.RGBA
PV = os.path.join(ART, "previews")
os.makedirs(PV, exist_ok=True)

SEG_L = 8                       # spine spacing (px) -- the engine uses the same value
RADII = [2, 3, 4, 5, 6, 7, 8, 10, 12, 14]
SEG_ANG = 16                    # 0 .. 168.75 deg
LIT = (-0.45, -0.9)             # screen direction the lit side faces


def hsh(x, y, k=0):
    return G.hash01(x, y, k)


def blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def seg_frames(r):
    F = 2 * r + SEG_L + 6
    c = (F / 2, F / 2)
    fills = {v: [] for v in range(3)}
    lines = []
    for ai in range(SEG_ANG):
        a = math.radians(ai * 180 / SEG_ANG)
        d = (math.cos(a), math.sin(a))
        n = (-d[1], d[0])
        if n[0] * LIT[0] + n[1] * LIT[1] < 0:
            n = (-n[0], -n[1])
        ln = blank(F, F)
        lp = ln.load()
        for var in range(3):
            im = blank(F, F)
            px = im.load()
            for y in range(F):
                for x in range(F):
                    ox, oy = x + .5 - c[0], y + .5 - c[1]
                    t = ox * d[0] + oy * d[1]
                    v = ox * n[0] + oy * n[1]
                    dist = abs(v) if abs(t) <= SEG_L / 2 else math.hypot(abs(t) - SEG_L / 2, v)
                    if var == 0 and dist <= r + 1.25:
                        lp[x, y] = C["OUT"]
                    if dist > r + 0.3:
                        continue
                    u = max(-1.0, min(1.0, v / max(r, 1)))
                    if r <= 3:
                        col = "W5" if u > 0.5 else "W3" if u > 0.0 else "K3" if u > -0.6 else "K2"
                    else:
                        col = ("W5" if u > 0.8 else "W4" if u > 0.48 else "W3" if u > 0.16 else "W2" if u > -0.06
                               else "K4" if u > -0.3 else "K3" if u > -0.62 else "K2" if u > -0.88 else "K4")
                        # golden threads running the length of the body
                        for u0, cc in ((0.3, "G4"),) + (((0.64, "G3"), (-0.55, "G2")) if r >= 10 else ()):
                            if abs(v - u0 * r) < 0.55:
                                col = cc
                        if u < -0.12 and u > -0.9:
                            hv = hsh(x + var * 37 + ai * 5, y + var * 11, 71)
                            if hv > 0.985:
                                col = "L"
                            elif hv > 0.95:
                                col = "Y2"
                    px[x, y] = C[col]
            fills[var].append(im)
        lines.append(ln)
    return F, fills, lines


def build_segments(preview_only):
    rows = []
    for r in RADII:
        F, fills, lines = seg_frames(r)
        frames, tags = [], []
        for nm, lst in (("fill0", fills[0]), ("fill1", fills[1]), ("fill2", fills[2]), ("line", lines)):
            tags.append((nm, len(frames), len(frames) + len(lst) - 1))
            frames += [{"ms": 100, "cels": {"Body": im}} for im in lst]
        if not preview_only:
            asebuild.build(f"sov_seg_{r:02d}", F, F, ["Body"], frames, tags)
        rows.append((F, fills[0], lines))
    return rows


# =========================================================================== head
HEAD_F = 72
HEAD_ANGS = [-90 + i * 11.25 for i in range(17)]
CX, CY = 96, 80          # head pivot (neck joint) on the 192x160 working canvas


def xf(theta):
    ct, st = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return lambda p: (CX + p[0] * ct - p[1] * st, CY + p[0] * st + p[1] * ct)


def smooth(pts, n=6):
    """Catmull-Rom through pts (closed polygon)."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


SKULL_UP = [(-7, -6.0), (0, -7.6), (6, -9.4), (11, -9.0), (15, -6.8), (21, -5.2), (28, -3.2), (33, -1.2), (36, 0.6)]
SKULL_LO_CLOSED = [(35, 2.0), (29, 3.2), (20, 4.8), (11, 6.2), (2, 6.8), (-7, 6.2)]
SKULL_LO_OPEN = [(33, 0.6), (26, 1.6), (18, 2.4), (10, 3.0), (2, 6.8), (-7, 6.2)]
JAW = [(3, 3.4), (12, 5.4), (21, 8.2), (29, 11.0), (31, 12.6), (24, 12.4), (14, 10.2), (5, 8.2), (0, 6.2)]


def head_render(theta, open_=False, sway=0.0):
    T = xf(theta)
    L = {"Horn": G.Layer("Horn"), "Head": G.Layer("Head"), "Jaw": G.Layer("Jaw")}
    FX = G.FXLayer("FX")
    FB = G.FXLayer("FXBack")
    # mane: fine gold filaments streaming back from the crown (the engine adds long flowing ones)
    for k in range(7):
        y0 = -6 + k * 2.0
        e = (-26 - (k % 3) * 5, y0 * 1.6 + sway * (0.5 + k * 0.1))
        cv = [T(q) for q in G.qbez((-2, y0), (-12, y0 * 1.1 - 2), e, 18)]
        for i_ in range(2, len(cv) - 1):
            FB.put(G.line(cv[i_], cv[i_ + 1]), "G4" if k % 2 else "Y1", 190 if i_ < 12 else 130)
    # swept-back root crown: a long elegant curl, two lesser tines
    for (b, m, e, r0) in (((8, -8.5), (-6, -18), (-26, -19), 2.3), ((3, -7.5), (-8, -12), (-22, -10), 1.7),
                          ((13, -8), (8, -15), (0, -20), 1.2)):
        e = (e[0], e[1] + sway)
        pts = [T(q) for q in G.qbez(b, m, e, 18)]
        nm, _ = G.tube(pts, r0, 0.5, ex=1.4)
        L["Horn"].paint(nm, "G", ao=0)
        FX.put([G.ipt(pts[-1])], "L")
        for q in pts[4:-2:4]:
            FX.put([G.ipt(q)], "Y2", 190)
    lo = SKULL_LO_OPEN if open_ else SKULL_LO_CLOSED
    skull = smooth(SKULL_UP + lo, 4)
    sm = G.poly_mask([T(q) for q in skull])
    L["Head"].paint(G.n_plate(sm, bevel=3.0, strength=1.3), "K")
    # porcelain mask: brow, cheek and snout
    mask = smooth([(5, -9.0), (11, -8.8), (15, -6.6), (21, -5.0), (28, -3.0), (33, -1.0), (36, 0.5),
                   (31, 1.2), (22, 1.0), (14, 0.6), (8, -0.4), (3, -3.5)], 3)
    mm = G.poly_mask([T(q) for q in mask]) & sm
    L["Head"].paint(G.n_plate(mm, bevel=1.8, strength=1.1), "P", ao=0)
    edge = {q for q in mm if any((q[0] + a, q[1] + b) not in mm and (q[0] + a, q[1] + b) in sm
                                 for a, b in ((0, 1), (1, 0), (-1, 0), (0, -1)))}
    L["Head"].decal(edge, ("G", 3))
    # gold threads along the dark skull, echoing the body
    for (p0, p1, p2) in (((-7, 2.5), (6, 3.6), (20, 3.6)), ((-7, -2.5), (0, -3.0), (4, -4.5))):
        for q in G.qbez(p0, p1, p2, 14):
            q = G.ipt(T(q))
            if q in sm and q not in mm:
                L["Head"].decal([q], ("G", 3))
    if open_:
        jm = G.poly_mask([T(q) for q in smooth(JAW, 3)])
        L["Jaw"].paint(G.n_plate(jm, bevel=2.0, strength=1.1), "K", bias=-1)
        for q in G.qbez(JAW[0], (14, 7.6), (28, 11.2), 14):
            q = G.ipt(T(q))
            if q in jm:
                L["Jaw"].decal([q], ("G", 3))
        inner = G.poly_mask([T(q) for q in [(4, 2.4), (33, 0.4), (30, 11.0), (6, 7.0)]])
        for q in inner:
            if q in sm or q in jm:
                continue
            ct, st = math.cos(math.radians(theta)), math.sin(math.radians(theta))
            x_ = (q[0] - CX) * ct + (q[1] - CY) * st
            FB.put([q], "L" if x_ < 16 else "Y3" if x_ < 25 else "Y2")
    else:
        for q in G.qbez((12, 2.0), (22, 2.2), (34, 1.3), 16):
            q = G.ipt(T(q))
            if q in sm:
                L["Head"].decal([q], ("V", 0))
    # eye: a narrow burning slit in a dark socket
    for dy in (-0.9, 0.0, 0.9):
        for q in G.line(T((13.5, -4.6 + dy)), T((20.5, -3.2 + dy))):
            L["Head"].decal([q], ("K", 0))
    for q in G.line(T((14.5, -4.3)), T((19.5, -3.2))):
        FX.put([q], "Y2")
    FX.put([G.ipt(T((17, -3.8)))], "L")
    FX.put([G.ipt(T((12.5, -4.9)))], "Y1")
    for q in G.mask_disc(T((17, -4.0)), 3.6):
        FB.under([q], "Y2", 130)
    imgs = [FB.image(), G.render_layer(L["Horn"]), G.render_layer(L["Jaw"]), G.render_layer(L["Head"]), FX.image()]
    out = blank(G.W, G.H)
    for im in imgs:
        out.alpha_composite(im)
    h = HEAD_F // 2
    return out.crop((CX - h, CY - h, CX + h, CY + h))


def build_head(preview_only):
    frames, tags, prev = [], [], []
    for nm, op in (("closed", False), ("open", True)):
        a = len(frames)
        for th in HEAD_ANGS:
            im = head_render(th, op)
            frames.append({"ms": 100, "cels": {"Head": im}})
            prev.append(im)
        tags.append((nm, a, len(frames) - 1))
    if not preview_only:
        asebuild.build("sov_head", HEAD_F, HEAD_F, ["Head"], frames, tags)
    return prev


# =========================================================================== fin (dorsal sail) and tail fan
FIN_F = 104


def fin_render(theta, sway):
    """Dorsal sail: root ribs fanning up-and-back from the spine, luminous membrane between them."""
    T = xf(theta)
    L = G.Layer("Fin")
    FB = G.FXLayer("FXBack")
    FX = G.FXLayer("FX")
    ribs = []
    for k, (ang, ln) in enumerate(((194, 30), (210, 44), (226, 48), (242, 38))):
        a = ang + sway * (3 + k * 2)
        tip = (math.cos(math.radians(a)) * ln, math.sin(math.radians(a)) * ln)
        mid = (tip[0] * 0.5 + 2, tip[1] * 0.5 - 2)
        hook = (tip[0] + 3, tip[1] - 1)
        pts = G.qbez((0, 0), mid, hook, 16)
        ribs.append(pts)
    for A, B_ in zip(ribs, ribs[1:]):
        poly = [T(q) for q in A[1:] + list(reversed(B_[1:]))]
        m = G.poly_mask(poly)
        for q in m:
            dd = math.hypot(q[0] + .5 - CX, q[1] + .5 - CY)
            c, al = ("L", 190) if dd < 16 else ("Y3", 190) if dd < 30 else ("Y2", 190) if dd < 40 else ("Y1", 130)
            FB.under([q], c, al)
    for k, pts in enumerate(ribs):
        nm, _ = G.tube([T(q) for q in pts], 1.7 - k * 0.15, 0.5, ex=1.3)
        L.paint(nm, "G" if k % 2 == 0 else "B", ao=0)
        FX.put([G.ipt(T(pts[-1]))], "L")
        for q in pts[3:-3:3]:
            FX.put([G.ipt(T(q))], "Y2", 190)
    out = blank(G.W, G.H)
    for im in (FB.image(), G.render_layer(L), FX.image()):
        out.alpha_composite(im)
    h = FIN_F // 2
    return out.crop((CX - h, CY - h, CX + h, CY + h))


TAIL_F = 80
TAIL_N = 24


def tail_render(theta, sway):
    """Tail fan: seven streaming light filaments with a faint sail between the middle ones."""
    T = xf(theta)
    F = G.FXLayer("FX")
    FB = G.FXLayer("FXBack")
    strands = []
    for k in range(7):
        a = -36 + k * 12
        ln = 38 - abs(k - 3) * 3
        cv = 7 * (1 if k % 2 else -1) * (0.6 + sway * 0.8)
        tip = (math.cos(math.radians(a)) * ln, math.sin(math.radians(a)) * ln)
        mid = (tip[0] * 0.55 - math.sin(math.radians(a)) * cv, tip[1] * 0.55 + math.cos(math.radians(a)) * cv)
        strands.append(G.qbez((0, 0), mid, tip, 20))
    for A, B_ in zip(strands[1:5], strands[2:6]):
        for q in G.poly_mask([T(q) for q in A[2:15] + list(reversed(B_[2:15]))]):
            dd = math.hypot(q[0] + .5 - CX, q[1] + .5 - CY)
            FB.under([q], "Y2" if dd < 12 else "Y1", 130 if dd < 12 else 70)
    for k, pts in enumerate(strands):
        wp = [T(q) for q in pts]
        for i in range(len(wp) - 1):
            t = i / len(wp)
            F.put(G.line(wp[i], wp[i + 1]), "L" if t < 0.2 else "Y3" if t < 0.5 else "Y2" if t < 0.8 else "Y1",
                  255 if t < 0.8 else 190)
        G.fx_star(F, wp[-1], 1)
    for q in G.mask_disc((CX, CY), 3.5):
        F.put([q], "Y3")
    out = blank(G.W, G.H)
    out.alpha_composite(FB.image())
    out.alpha_composite(F.image())
    h = TAIL_F // 2
    return out.crop((CX - h, CY - h, CX + h, CY + h))


# =========================================================================== halo
HALO_F = 120


def halo_render(fi):
    """A ring of light (not metal): bright core line, soft corona, a fine root strand twining around it,
    gold thorns radiating outward -- longest at the top like a sunburst crown."""
    L = G.Layer("Halo")
    FB = G.FXLayer("FXBack")
    FX = G.FXLayer("FX")
    c = (CX, CY)
    R = 44.0
    rot = fi * (360 / 16) / 8
    for q in G.mask_disc(c, R + 7):
        d = math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1])
        e = abs(d - R)
        if e < 0.7:
            FX.put([q], "L")
        elif e < 1.6:
            FX.put([q], "Y3")
        elif e < 2.6:
            FX.put([q], "Y2", 190)
        elif e < 4.5:
            FB.put([q], "Y1", 130)
        elif e < 7:
            FB.put([q], "Y1", 70)
    # the root strand twining around the light
    pts = []
    for i in range(0, 361):
        th = 2 * math.pi * i / 360
        rr = R + 2.4 * math.sin(th * 9 + math.radians(rot) * 9 / 1.0)
        pts.append((c[0] + math.cos(th) * rr, c[1] + math.sin(th) * rr))
    nm, _ = G.tube(pts, 1.0, 1.0)
    L.paint(nm, "G", ao=0)
    # thorns
    for k in range(16):
        thd = (k * 22.5 + rot) % 360
        th = math.radians(thd)
        up = -math.sin(th)
        ln = 3 + 13 * max(0.0, up) ** 1.4
        base = (c[0] + math.cos(th) * (R + 1.5), c[1] + math.sin(th) * (R + 1.5))
        tip = (c[0] + math.cos(th) * (R + 1.5 + ln), c[1] + math.sin(th) * (R + 1.5 + ln))
        m, sp = G.spike_mask(base, tip, 1.0 if ln > 8 else 0.7, bend=G.mul(G.dirv(thd + 90), 1.2))
        L.paint({q: G.norm3(math.cos(th) * 0.6, math.sin(th) * 0.6, 0.8) for q in m}, "G", ao=0)
        if ln > 6:
            FX.put([G.ipt(tip)], "L")
            for q in sp[2:-2]:
                FX.put([G.ipt(q)], "Y3")
    for thd in (270, 30, 150):
        th = math.radians(thd + rot)
        q = (c[0] + math.cos(th) * R, c[1] + math.sin(th) * R)
        G.fx_star(FX, q, 3)
    out = blank(G.W, G.H)
    for im in (FB.image(), FX.image(), G.render_layer(L)):
        out.alpha_composite(im)
    h = HALO_F // 2
    return out.crop((CX - h, CY - h, CX + h, CY + h))


# =========================================================================== FX sheets
class FXC:
    """Small FX canvas with the house alpha steps."""
    def __init__(self, w, h):
        self.w, self.h, self.px = w, h, {}

    def put(self, pts, c, a=255, under=False):
        a = min(G.ALPHA_STEPS, key=lambda s: abs(s - a)) if a < 255 else 255
        rgba = C[c][:3] + (a,)
        for p in pts:
            p = (int(math.floor(p[0])), int(math.floor(p[1])))
            if 0 <= p[0] < self.w and 0 <= p[1] < self.h and not (under and p in self.px):
                self.px[p] = rgba

    def disc(self, c, r, col, a=255, under=False):
        self.put([(x, y) for y in range(int(c[1] - r) - 1, int(c[1] + r) + 2) for x in range(int(c[0] - r) - 1, int(c[0] + r) + 2)
                  if (x + .5 - c[0]) ** 2 + (y + .5 - c[1]) ** 2 <= r * r], col, a, under)

    def line(self, a, b, col, al=255):
        self.put(G.line(a, b), col, al)

    def star(self, c, r):
        x, y = int(c[0]), int(c[1])
        self.put([(x, y)], "L")
        for k in range(1, r + 1):
            cc = "Y3" if k <= max(1, r // 2) else "Y1"
            self.put([(x + k, y), (x - k, y), (x, y + k), (x, y - k)], cc)
        if r >= 3:
            self.put([(x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)], "Y2")

    def image(self):
        im = blank(self.w, self.h)
        p = im.load()
        for q, c in self.px.items():
            p[q] = c
        return im


def glow_disc(F, c, r, core="L"):
    for q_r, col, al in ((r + 4, "Y1", 70), (r + 2, "Y1", 130), (r, "Y2", 255), (r * 0.7, "Y3", 255), (r * 0.4, core, 255)):
        F.disc(c, q_r, col, al)


def fx_beam():
    out = []
    for fi in range(4):
        F = FXC(24, 20)
        for x in range(24):
            wob = math.sin((x + fi * 6) * 0.52) * 0.6
            for y in range(20):
                e = abs(y + .5 - 10 - wob)
                if e < 2.2:
                    F.put([(x, y)], "L")
                elif e < 3.6:
                    F.put([(x, y)], "Y3")
                elif e < 5.0:
                    F.put([(x, y)], "Y2")
                elif e < 6.2:
                    F.put([(x, y)], "Y1", 190)
                elif e < 8.5 and (x + y + fi) % 2 == 0:
                    F.put([(x, y)], "Y1", 70)
        for k in range(3):
            sx = (k * 8 + fi * 6) % 24
            F.put([(sx, 10 + (k - 1) * 4)], "L")
        out.append(F.image())
    return out


def fx_beamend():
    out = []
    for fi in range(4):
        F = FXC(48, 48)
        glow_disc(F, (24, 24), 7 + (fi % 2))
        for k in range(10):
            a = k * 36 + fi * 13
            ln = 12 + (k % 3) * 5 + fi % 2 * 2
            F.line(G.add((24, 24), G.mul(G.dirv(a), 8)), G.add((24, 24), G.mul(G.dirv(a), ln)), "Y2" if k % 2 else "Y3")
        for k in range(6):
            q = (24 + math.cos(k * 1.7 + fi) * (14 + fi * 3), 24 - abs(math.sin(k * 1.3 + fi)) * (10 + fi * 3))
            F.put([q], "Y3")
        out.append(F.image())
    return out


def fx_star_orb():
    out = []
    for fi in range(4):
        F = FXC(16, 16)
        glow_disc(F, (8, 8), 3.2)
        ln = 6 + (fi % 2)
        for a in (0, 90, 180, 270):
            a2 = a + fi * 22.5
            F.line(G.add((8, 8), G.mul(G.dirv(a2), 3)), G.add((8, 8), G.mul(G.dirv(a2), ln)), "Y3")
        out.append(F.image())
    return out


def fx_meteor():
    out = []
    for fi in range(4):
        F = FXC(16, 48)
        for y in range(0, 40):
            w = (y / 40) * 3.2
            for x in range(16):
                e = abs(x + .5 - 8 + math.sin(y * 0.4 + fi) * 0.4)
                if e < w * 0.4:
                    F.put([(x, y)], "L" if y > 30 else "Y3")
                elif e < w * 0.8:
                    F.put([(x, y)], "Y2" if y > 20 else "Y1", 190 if y > 20 else 130)
                elif e < w + 0.6 and (x + y + fi) % 2 == 0:
                    F.put([(x, y)], "Y1", 70)
        glow_disc(F, (8, 41), 3.4)
        F.star((8, 41), 5 if fi % 2 else 4)
        out.append(F.image())
    return out


def fx_ringwave():
    out = []
    for fi in range(4):
        F = FXC(24, 32)
        for y in range(32):
            t = 1 - y / 32
            xc = 12 + math.sin(t * math.pi) * 4 - 2
            wv = 2 + (1 - t) * 3
            for x in range(24):
                e = abs(x + .5 - xc)
                if e < wv * 0.35:
                    F.put([(x, y)], "L")
                elif e < wv * 0.7:
                    F.put([(x, y)], "Y3")
                elif e < wv:
                    F.put([(x, y)], "Y2", 190)
                elif e < wv + 3 and (x + y + fi) % 2 == 0:
                    F.put([(x, y)], "Y1", 130 if y > 16 else 70)
        for k in range(5):
            F.put([(8 + (k * 5 + fi * 3) % 12, 30 - ((k * 7 + fi * 5) % 28))], "L")
        out.append(F.image())
    return out


def root_curve(base, pts_local, n=24):
    return [G.add(base, q) for q in G.bezier(*pts_local, n)] if len(pts_local) == 4 else [G.add(base, q) for q in G.qbez(*pts_local, n)]


def paint_root(F, pts, r0, r1, glow=True):
    """Root tendril: pale bark tube (flat 3-tone shading) with a sap-gold core seam."""
    n = len(pts) - 1
    for i, c in enumerate(pts):
        r = r1 + (r0 - r1) * (1 - i / n) ** 1.2
        F.disc(c, r + 1.0, "OUT", under=True)
    for i, c in enumerate(pts):
        r = r1 + (r0 - r1) * (1 - i / n) ** 1.2
        F.disc(c, r, "B3")
        F.disc(G.add(c, (-r * 0.35, -r * 0.35)), r * 0.55, "B4")
    for i, c in enumerate(pts[:-2]):
        if glow and i % 2 == 0:
            F.put([c], "Y2" if (i // 2) % 3 else "L")
    F.put([pts[-1]], "Y3")


def fx_whip():
    """Root whip: ground crack (0-2) -> erupts (3) -> curls over (4-5) -> lashes forward low (6) -> sinks (7-9)."""
    out = []
    base = (16, 79)
    shapes = {3: [(0, 0), (2, -30), (0, -52), (4, -66)], 4: [(0, 0), (4, -34), (18, -58), (30, -52)],
              5: [(0, 0), (8, -30), (30, -40), (40, -26)], 6: [(0, 0), (10, -18), (26, -14), (44, -4)],
              7: [(0, 0), (6, -14), (18, -12), (28, -6)], 8: [(0, 0), (3, -8), (8, -8), (12, -4)]}
    for fi in range(10):
        F = FXC(48, 80)
        if fi <= 2 or fi >= 7:
            k = (fi + 1) / 3 if fi <= 2 else (10 - fi) / 3
            for x in range(int(16 - 10 * k), int(16 + 10 * k) + 1):
                F.put([(x, 79)], "L" if abs(x - 16) < 3 * k else "Y2")
                if abs(x - 16) < 6 * k and (x + fi) % 2:
                    F.put([(x, 78)], "Y1", 190)
        if fi in shapes:
            pts = [G.add(base, q) for q in G.bezier(*shapes[fi], 26)]
            paint_root(F, pts, 5.0, 1.2)
            if fi in (4, 5, 6):
                for q in pts[10::2]:
                    F.put([G.add(q, (-2, 2))], "Y1", 130, under=True)
        if fi in (3, 6):
            for k in range(8):
                F.put([(base[0] + (k - 4) * 3 + (fi == 6) * 12, 79 - (k % 3))], "B4")
        out.append(F.image())
    return out


def fx_spear():
    out = []
    for fi in range(10):
        F = FXC(24, 96)
        if fi <= 2:
            k = (fi + 1) / 3
            for x in range(int(12 - 9 * k), int(12 + 9 * k) + 1):
                F.put([(x, 95)], "L" if abs(x - 12) < 3 * k else "Y2")
            F.disc((12, 95), 4 * k, "Y1", 130, under=True)
            for s_ in range(int(12 * k)):
                if s_ % 3 == 0:
                    F.put([(12 + (s_ % 5) - 2, 94 - s_)], "Y2")
        else:
            h = {3: 60, 4: 92, 5: 90, 6: 86, 7: 60, 8: 34, 9: 12}[fi]
            top = 95 - h
            for y in range(top, 96):
                t = (y - top) / max(1, h)
                w = 0.6 + 5.2 * t ** 0.8
                for x in range(24):
                    e = x + .5 - 12 - math.sin(t * 5) * 1.2 * t
                    if abs(e) <= w + 1:
                        F.put([(x, y)], "OUT")
                    if abs(e) <= w:
                        col = "B4" if e < -w * 0.3 else "B3" if e < w * 0.4 else "B2"
                        if abs(e) < 0.8 and (y + fi) % 3:
                            col = "Y3" if fi <= 5 else "Y1"
                        F.put([(x, y)], col)
            if fi <= 5:
                F.put([(12, top), (12, top + 1)], "L")
            if fi >= 7:
                for k in range(6):
                    F.put([(4 + k * 3, 95 - (k * 5 + fi) % 10)], "B3")
        out.append(F.image())
    return out


def outlined(F):
    """Dark 1px outline around everything drawn so light FX still read against the pale sky."""
    pts = set(F.px)
    for (x, y) in pts:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if q not in pts and 0 <= q[0] < F.w and 0 <= q[1] < F.h:
                F.px[q] = C["OUT"]


def fx_petal_blade():
    out = []
    for fi in range(4):
        F = FXC(16, 16)
        a = fi * 45
        d, n = G.dirv(a), G.dirv(a + 90)
        c = (8, 8)
        pts = [G.add(c, G.mul(d, -6.5)), G.add(G.add(c, G.mul(n, 3.0)), G.mul(d, -1)), G.add(c, G.mul(d, 6.5)),
               G.add(G.add(c, G.mul(n, -1.8)), G.mul(d, 1.5))]
        m = G.poly_mask(pts)
        for q in m:
            F.put([q], "G3")
        for q in m:
            if all((q[0] + a_, q[1] + b_) in m for a_, b_ in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                F.put([q], "W5")
        F.line(G.add(c, G.mul(d, -5)), G.add(c, G.mul(d, 5)), "Y1")
        outlined(F)
        out.append(F.image())
    return out


def fx_orb():
    out = []
    for fi in range(4):
        F = FXC(16, 16)
        glow_disc(F, (8, 8), 4 + (fi % 2) * 0.6)
        for k in range(8):
            a = k * 45 + fi * 12
            F.put([G.add((8, 8), G.mul(G.dirv(a), 7))], "Y2" if k % 2 else "Y3")
        out.append(F.image())
    return out


def fx_band():
    out = []
    hs = [12, 36, 50, 46, 28, 10]
    for fi in range(6):
        F = FXC(32, 56)
        h = hs[fi]
        for x in range(32):
            hh = h * (0.75 + 0.25 * math.sin(x * 0.9 + fi * 1.7))
            for y in range(int(56 - hh), 56):
                t = (56 - y) / max(1, hh)
                col = "L" if t < 0.25 else "Y3" if t < 0.5 else "Y2" if t < 0.75 else "Y1" if t < 0.9 else "Y0"
                if fi >= 4:
                    col = "Y2" if t < 0.4 else "Y1" if t < 0.8 else "Y0"
                F.put([(x, y)], col)
        for k in range(4):
            F.put([((k * 9 + fi * 5) % 32, 56 - int(h * 0.95) - k * 3)], "Y3")
        outlined(F)
        out.append(F.image())
    return out


def fx_mark():
    out = []
    for fi in range(4):
        F = FXC(16, 10)
        for x in range(16):
            on = (x + fi * 2) % 6 < 4
            F.put([(x, 9)], "Y2" if on else "Y0")
            F.put([(x, 8)], "Y0" if on else "G2")
            if on and x % 3 == 1:
                F.put([(x, 7)], "Y1")
                F.put([(x, 6)], "Y2" if fi % 2 else "Y1")
        F.put([((fi * 5) % 16, 4)], "L")
        outlined(F)
        out.append(F.image())
    return out


def fx_well():
    """Gravity well: a black star with a golden accretion spiral winding into it."""
    out = []
    for fi in range(8):
        F = FXC(80, 80)
        c = (40, 40)
        for q_r, col, al in ((30, "K1", 70), (24, "K1", 130), (17, "K0", 255)):
            F.disc(c, q_r, col, al)
        for arm in range(3):
            for s_ in range(220):
                t = s_ / 220
                r = 34 * (1 - t) + 11
                a = arm * 120 + t * 300 - fi * 15
                q = G.add(c, G.mul(G.dirv(a), r))
                F.put([q], "L" if t > 0.8 else "Y3" if t > 0.5 else "Y2", 255 if t > 0.3 else 190)
                if t > 0.4:
                    F.put([G.add(q, G.mul(G.dirv(a + 90), 1))], "Y1", 190)
        for t in range(0, 360, 3):
            q = G.add(c, G.mul(G.dirv(t), 17.5))
            F.put([q], "Y2" if (t // 3 + fi) % 4 else "L")
        out.append(F.image())
    return out


def fx_bind():
    """Roots burst up around the seized player and coil shut over them."""
    out = []
    for fi in range(6):
        F = FXC(32, 40)
        k = min(1.0, (fi + 1) / 3)
        for side in (-1, 1):
            h = 34 * k
            pts = [(16 + side * 11 * math.cos(t * (1.2 + 0.9 * k)) * (1 - 0.2 * t), 39 - h * math.sin(t * 1.4) - t * 4)
                   for t in [i / 18 for i in range(19)]]
            paint_root(F, pts, 3.2, 1.0)
        if fi >= 3:
            for y in (32, 24):
                pts = [(6 + t * 20, y + math.sin(t * math.pi) * 3 + (fi % 2)) for t in [i / 10 for i in range(11)]]
                paint_root(F, pts, 1.4, 1.0, glow=False)
        out.append(F.image())
    return out


def fx_burst():
    out = []
    for fi in range(8):
        F = FXC(96, 96)
        c = (48, 48)
        k = fi / 7
        r = 6 + k * 40
        if fi < 3:
            glow_disc(F, c, 8 + fi * 5)
        for t in range(0, 360, 2):
            q = G.add(c, G.mul(G.dirv(t), r))
            if (t // 2 + fi) % 7 or fi < 4:
                F.put([q], "L" if fi < 3 else "Y3" if fi < 5 else "Y1", 255 if fi < 6 else 190)
                F.put([G.add(c, G.mul(G.dirv(t), r - 1.5))], "Y2", 190)
        for j in range(16):
            a = j * 22.5 + fi * 3
            F.line(G.add(c, G.mul(G.dirv(a), r * 0.3)), G.add(c, G.mul(G.dirv(a), r * (0.7 if j % 2 else 0.95))),
                   "Y3" if fi < 4 else "Y1", 255 if fi < 5 else 130)
        out.append(F.image())
    return out


FX_SHEETS = [  # name, w, h, frames fn, tag, ms
    ("fx_sov_beam", 24, 20, fx_beam, "sov_beam", 60), ("fx_sov_beamend", 48, 48, fx_beamend, "sov_beamend", 60),
    ("fx_sov_star", 16, 16, fx_star_orb, "sov_star", 80), ("fx_sov_meteor", 16, 48, fx_meteor, "sov_meteor", 70),
    ("fx_sov_ringwave", 24, 32, fx_ringwave, "sov_ringwave", 70), ("fx_sov_whip", 48, 80, fx_whip, "sov_whip", 70),
    ("fx_sov_spear", 24, 96, fx_spear, "sov_spear", 70), ("fx_sov_petal", 16, 16, fx_petal_blade, "sov_petal", 60),
    ("fx_sov_orb", 16, 16, fx_orb, "sov_orb", 80), ("fx_sov_band", 32, 56, fx_band, "sov_band", 60),
    ("fx_sov_mark", 16, 10, fx_mark, "sov_mark", 90), ("fx_sov_well", 80, 80, fx_well, "sov_well", 80),
    ("fx_sov_bind", 32, 40, fx_bind, "sov_bind", 80), ("fx_sov_burst", 96, 96, fx_burst, "sov_burst", 60),
]


# =========================================================================== phase-3 arena: the void inside the Root's heart
BW, BH = 512, 216
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
VOID = ["#040309", "#07060f", "#0a0816", "#0e0b1e", "#130f28", "#1a1434"]
VOIDC = [tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for v in VOID]


def fbm(x, y, k):
    v, a, f = 0.0, 0.5, 1.0
    for o in range(4):
        v += a * (G.vnoise(x * f / 40 + G.vnoise(y * f / 53 + o, k + 7) * 1.5, k + o) * 0.5 +
                  G.vnoise(y * f / 37 + x * f / 91, k + o + 20) * 0.5)
        a *= 0.5
        f *= 2.0
    return v


def dith(v, x, y, pal):
    n = len(pal) - 1
    f = max(0.0, min(0.999, v)) * n
    i = int(f)
    return pal[min(n, i + (1 if (f - i) * 16 > BAYER[y % 4][x % 4] else 0))]


def bg_far_frames():
    base = blank(BW, BH)
    px = base.load()
    for y in range(BH):
        for x in range(BW):
            g_ = 0.15 + 0.55 * (y / BH)
            # periodic (x wraps at 512) nebula
            n = 0.5 * fbm(x, y, 3) + 0.5 * fbm(x - BW, y, 3) * 0 if False else fbm(x % BW, y, 3)
            xs = x / BW * 2 * math.pi
            n = 0.55 * fbm(math.cos(xs) * 80 + 80, y + math.sin(xs) * 80, 3) + 0.45 * fbm(math.sin(xs) * 60, y * 1.3, 9)
            v = g_ + max(0.0, n - 0.45) * 1.6
            px[x, y] = dith(v, x, y, VOIDC)
    # the Root's heart: vast pale filaments descending from far above, branching like veins of light
    F = FXC(BW, BH)

    def branch(p, ang, ln, depth, seed):
        pts = [p]
        a = ang
        for i in range(int(ln / 3)):
            a += (G.hash01(i, seed, 5) - 0.5) * 16
            p = G.add(p, G.mul(G.dirv(a), 3))
            pts.append(p)
        for i in range(len(pts) - 1):
            F.put(G.line(pts[i], pts[i + 1]), "K5" if depth == 0 else "K4", 130 if depth == 0 else 70)
            if depth == 0 and (i + seed) % 9 == 0:
                F.put([pts[i]], "Y2")
        if depth < 3:
            for k in range(2):
                q = pts[int(len(pts) * (0.45 + 0.3 * k))]
                branch(q, a + (28 if k else -30) + (G.hash01(k, seed, 9) - 0.5) * 20, ln * 0.55, depth + 1, seed * 3 + k + 1)
    for k, x0 in enumerate((150, 256, 360)):
        branch((x0, -4), 90 + (k - 1) * 9, 150 - abs(k - 1) * 30, 0, 11 + k)
    base.alpha_composite(F.image())
    frames = []
    for fi in range(4):
        im = base.copy()
        p = im.load()
        for s_ in range(260):
            x = int(G.hash01(s_, 1, 31) * BW)
            y = int(G.hash01(s_, 2, 32) ** 1.3 * (BH - 20))
            b = G.hash01(s_, 3, 33)
            tw = (s_ + fi) % 4 == 0
            col = C["L"] if b > 0.93 and not tw else C["Y3"] if b > 0.8 else C["K5"] if b > 0.45 else C["K4"]
            if tw and b > 0.8:
                col = C["Y2"]
            p[x, y] = col
            if b > 0.965 and not tw:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < BW and 0 <= y + dy < BH:
                        p[x + dx, y + dy] = C["Y1"]
        frames.append(im)
    return frames


def bg_mid_frames():
    """Floating root-islands and a vast ring arc far away (transparent sky)."""
    F = FXC(BW, BH)
    # distant ring arc
    for t in range(0, 3600):
        a = math.radians(t / 10)
        q = (256 + math.cos(a) * 300, 300 + math.sin(a) * 250)
        if 0 <= q[1] < BH - 30 and (t // 12) % 3:
            F.put([q], "K5", 70)
    im = F.image()
    p = im.load()
    # drifting root islands (dark silhouettes with a gold rim of light on top)
    for k, (cx, cy, w, h) in enumerate(((70, 150, 64, 14), (250, 176, 90, 18), (420, 140, 56, 12), (500, 190, 40, 10))):
        for y in range(int(cy - h), int(cy + h * 2.4)):
            for x in range(int(cx - w), int(cx + w)):
                u = (x - cx) / w
                top = cy - h * (1 - u * u) + math.sin(x * 0.3 + k) * 1.2
                bot = cy + h * 2.2 * (1 - abs(u)) ** 1.4 + math.sin(x * 0.7) * 2
                xx = x % BW
                if top <= y <= bot and 0 <= y < BH:
                    p[xx, y] = C["K0"] if y > top + 2 else C["K2"]
                    if y < top + 1:
                        p[xx, y] = C["K4"] if (x + k) % 7 else C["Y1"]
        for s_ in range(6):   # dangling root tendrils
            x = int(cx - w * 0.6 + s_ * w * 0.24) % BW
            for y in range(int(cy + h), int(cy + h * 2.2 + 10 + (s_ % 3) * 6)):
                if 0 <= y < BH:
                    p[(x + int(math.sin(y * 0.2 + s_) * 1.5)) % BW, y] = C["K1"]
    return [im]


# =========================================================================== composite preview (mirrors the engine's assembly)
def radius_at(u):
    r = 5.5 + 6.5 * min(1.0, u / 0.32) ** 0.9
    if u > 0.45:
        r *= max(0.0, 1 - (u - 0.45) / 0.55) ** 0.85
    return max(2.0, r)


def snap_r(r):
    return min(RADII, key=lambda q: abs(q - r))


def compose(spine, seg_imgs, head, fin, tail, halo, bgcol=(10, 8, 22, 255), size=(480, 270)):
    can = Image.new("RGBA", size, bgcol)
    N = len(spine)

    def at(im, c):
        can.alpha_composite(im, (int(round(c[0] - im.width / 2)), int(round(c[1] - im.height / 2))))

    at(halo[0], G.add(spine[6], (0, -14)))
    # dorsal fin behind the body
    i = 9
    a = math.degrees(math.atan2(spine[i - 1][1] - spine[i][1], spine[i - 1][0] - spine[i][0]))
    flip = math.cos(math.radians(a)) < 0
    aa = (180 - a) if flip else a
    aa = ((aa + 180) % 360) - 180
    fi = min(range(17), key=lambda k: abs(HEAD_ANGS[k] - aa))
    fim = fin[fi]
    if flip:
        fim = fim.transpose(Image.FLIP_LEFT_RIGHT)
    at(fim, spine[i])
    for pas in ("line", "fill"):
        for i in range(N - 2, -1, -1):
            p0, p1 = spine[i], spine[i + 1]
            ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180
            ai = int(round(ang / (180 / SEG_ANG))) % SEG_ANG
            r = snap_r(radius_at(i / (N - 1)))
            F, fills, lines = seg_imgs[RADII.index(r)]
            at((lines if pas == "line" else fills)[ai], ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2))
    # tail fan
    ta = math.degrees(math.atan2(spine[-1][1] - spine[-2][1], spine[-1][0] - spine[-2][0])) % 360
    at(tail[int(round(ta / (360 / TAIL_N))) % TAIL_N], spine[-1])
    # head
    a = math.degrees(math.atan2(spine[0][1] - spine[1][1], spine[0][0] - spine[1][0]))
    flip = math.cos(math.radians(a)) < 0
    aa = (180 - a) if flip else a
    aa = ((aa + 180) % 360) - 180
    hi = min(range(17), key=lambda k: abs(HEAD_ANGS[k] - aa))
    him = head[hi]
    if flip:
        him = him.transpose(Image.FLIP_LEFT_RIGHT)
    at(him, spine[0])
    return can


def test_spine(N=44, kind=0):
    pts = []
    for i in range(N):
        t = i / (N - 1)
        if kind == 0:     # rearing S-curve
            pts.append((330 - t * 300 + math.sin(t * 5) * 20, 70 + math.sin(t * 6.0 + 0.5) * 55 + t * 60))
        else:             # coiled, head low and left
            a = t * 5.2
            pts.append((140 + math.cos(a) * (40 + t * 90), 150 - math.sin(a) * (30 + t * 60)))
    # resample to SEG_L spacing
    out = [pts[0]]
    i = 1
    while len(out) < N and i < len(pts):
        d = math.hypot(pts[i][0] - out[-1][0], pts[i][1] - out[-1][1])
        if d >= SEG_L:
            k = SEG_L / d
            out.append((out[-1][0] + (pts[i][0] - out[-1][0]) * k, out[-1][1] + (pts[i][1] - out[-1][1]) * k))
        else:
            i += 1
    return out


def main():
    prev_only = "--preview" in sys.argv
    if "--fx" in sys.argv:          # quick path: only the fx_sov_* sheets
        for name, w, h, fn, tag, ms in FX_SHEETS:
            fr = fn()
            asebuild.build(name, w, h, ["FX"], [{"ms": ms, "cels": {"FX": im}} for im in fr], [(tag, 0, len(fr) - 1)])
        return
    segs = build_segments(prev_only)
    print("segments", flush=True)
    head = build_head(prev_only)
    fins = {sw: [fin_render(a, sw) for a in HEAD_ANGS] for sw in (0, 1)}
    tails = {sw: [tail_render(a * 360 / TAIL_N, sw * 0.8) for a in range(TAIL_N)] for sw in (0, 1)}
    halo = [halo_render(fi) for fi in range(8)]
    print("parts", flush=True)
    if not prev_only:
        asebuild.build("sov_fin", FIN_F, FIN_F, ["Fin"], [{"ms": 100, "cels": {"Fin": im}} for sw in (0, 1) for im in fins[sw]],
                       [("f0", 0, 16), ("f1", 17, 33)])
        asebuild.build("sov_tail", TAIL_F, TAIL_F, ["Tail"], [{"ms": 100, "cels": {"Tail": im}} for sw in (0, 1) for im in tails[sw]],
                       [("t0", 0, TAIL_N - 1), ("t1", TAIL_N, 2 * TAIL_N - 1)])
        asebuild.build("sov_halo", HALO_F, HALO_F, ["Halo"], [{"ms": 110, "cels": {"Halo": im}} for im in halo], [("loop", 0, 7)])
        for name, w, h, fn, tag, ms in FX_SHEETS:
            fr = fn()
            asebuild.build(name, w, h, ["FX"], [{"ms": ms, "cels": {"FX": im}} for im in fr], [(tag, 0, len(fr) - 1)])
        far, mid = bg_far_frames(), bg_mid_frames()
        asebuild.build("bg_sov_void_far", BW, BH, ["Sky"], [{"ms": 160, "cels": {"Sky": im}} for im in far], [("loop", 0, len(far) - 1)])
        asebuild.build("bg_sov_void_mid", BW, BH, ["Mid"], [{"ms": 100, "cels": {"Mid": im}} for im in mid], [("loop", 0, 0)])
        meta = {"seg_l": SEG_L, "radii": RADII, "seg_angles": SEG_ANG, "head_angles": HEAD_ANGS, "tail_angles": TAIL_N,
                "notes": "body assembled along a spine in web/src/26_sovereign2.js; head/fin mirrored for leftward angles"}
        json.dump(meta, open(os.path.join(asebuild.ASSETS, "sov_beast_meta.json"), "w"), indent=1)
    # previews
    far = bg_far_frames()[0]
    shots = []
    for kind in (0, 1):
        sp = test_spine(44, kind)
        bg = far.crop((0, 0, 480, 216)).resize((480, 270))
        c = compose(sp, segs, head[:17], fins[0], tails[0], halo)
        can = bg.copy()
        can.alpha_composite(c.crop((0, 0, 480, 270)) if False else c)
        shots.append(compose(sp, segs, head[:17], fins[0], tails[0], halo, bgcol=(0, 0, 0, 0)))
    sheet = Image.new("RGBA", (960, 270), (0, 0, 0, 255))
    for k, s_ in enumerate(shots):
        bgc = far.crop((k * 32, 0, k * 32 + 480, 216)).resize((480, 270), Image.NEAREST)
        bgc.alpha_composite(s_)
        sheet.paste(bgc, (k * 480, 0))
    sheet.resize((1920, 540), Image.NEAREST).save(os.path.join(PV, "sovbeast.png"))
    print("preview", os.path.join(PV, "sovbeast.png"))


if __name__ == "__main__":
    main()
