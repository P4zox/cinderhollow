"""Rig helper for The Unwritten (boss of the Ashen Archives).

Re-uses the approved concept's drawing code (art/concepts/gen_unwritten.py, concept v3) as a library and adds
what the animation sheets need:
  * a bigger canvas (the concept is 144x144; attacks reach further) -- every draw_* function keeps working in
    concept coordinates, only the final images are offset by (OX, OY)
  * loop-safe secondary motion (the concept's cloak used ph*0.5 / ph*1.1, which pops at a loop seam)
  * the orbiting pages are removed from the sprite (the engine draws them, so they can become projectiles)
  * scythe posed by (grip, angle, lengths) so swings rotate rigidly; swept ink smears between frames
  * phase-2 transformation cracks, ink sink/rise clipping, death dissolve
"""
import importlib.util
import math
import os

from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("unwritten_concept", os.path.join(ART, "concepts", "gen_unwritten.py"))
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

FW, FH = 224, 176           # frame size
OX, OY = 44, 32             # concept (0,0) -> frame (OX, OY)
AX, AY = OX + 70, FH        # anchor: body centre, frame bottom (= concept y 144, the floor under the lowest wisp)

add, sub, mul, lerp, unit, perp, ipt = C.add, C.sub, C.mul, C.lerp, C.unit, C.perp, C.ipt
bezier, qbez, curve_px, poly_mask, clean, hash01 = C.bezier, C.qbez, C.curve_px, C.poly_mask, C.clean, C.hash01
RGBA, N4 = C.RGBA, C.N4


def fr(q):
    """concept coords -> frame coords"""
    return (q[0] + OX, q[1] + OY)


# =========================================================================== canvas patch
def _inb(x, y):
    return -OX <= x < FW - OX and -OY <= y < FH - OY


C.inb = _inb


def _render_layer(layer, rimcol="RIM", sil=None):
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    pix = img.load()
    col, lvl = {}, {}
    for (x, y), e in layer.px.items():
        if e[0] is None or isinstance(e[3], str):
            col[(x, y)] = e[3]
            continue
        i = C.level_of(e, x, y)
        lvl[(x, y)] = i
        col[(x, y)] = C.RAMP[e[0]][i]
    for (x, y), e in layer.px.items():
        if not e[5] or isinstance(e[3], str):
            continue
        S_ = sil if sil is not None else layer.px
        if (x + 1, y) not in S_ and (x + 1, y) not in layer.px:
            if lvl.get((x, y), 0) <= 3 and y < 106:
                col[(x, y)] = rimcol
    for (x, y) in layer.px:
        for a, b in N4:
            q = (x + a, y + b)
            if not _inb(*q) or q in layer.px:
                continue
            e = layer.px[(x, y)]
            c = "OUT"
            if (a, b) in ((-1, 0), (0, -1)) and e[0] is not None and lvl.get((x, y), 0) >= len(C.RAMP[e[0]]) - 2:
                c = C.RAMP[e[0]][1]
            fq = (q[0] + OX, q[1] + OY)
            cur = pix[fq]
            if cur[3] == 0 or c == "OUT":
                pix[fq] = RGBA[c]
    for p, c in col.items():
        pix[(p[0] + OX, p[1] + OY)] = RGBA[c]
    return img


def _fx_image(self):
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    pix = img.load()
    for p, c in self.px.items():
        if _inb(*p):
            pix[(p[0] + OX, p[1] + OY)] = c
    return img


C.render_layer = _render_layer
C.FXLayer.image = _fx_image
Layer, FXLayer = C.Layer, C.FXLayer


# =========================================================================== loop-safe cloak
def tail_pts(j, k, spec):
    X, ph, wind = j["X"], j["ph"], j["wind"]
    (sx, sy), w0, (ex, ey), lay, sd = spec
    s = X((sx, sy))
    back = (5 - k) / 5.0
    lift = j.get("lift", 0.0)
    e = (ex - wind * (0.6 + back * 1.4) + 2.4 * math.sin(ph + sd),
         ey - wind * back * 0.9 + 1.5 * math.cos(ph + sd + 0.7) + j["bob"] * 0.5 + lift * (0.5 + back * 0.5))
    c1 = (s[0] - 1.0 - back * 2, s[1] + (e[1] - s[1]) * 0.6)
    c2 = (e[0] + (s[0] - e[0]) * 0.5 + 1.5 * math.sin(ph + sd + 1), e[1] - 3 - back * 6)
    return bezier(s, c1, c2, e, 30), w0


C.tail_pts = tail_pts


def draw_cloak(L, j, p, info):
    X, ph, wind = j["X"], j["ph"], j["wind"]
    info["tails"] = []
    Cp = L["TailsB"]
    sw = 1.5 * math.sin(ph) - wind * 0.8
    left = bezier(X((49, 47)), X((42, 60)), (X((37, 76))[0] + sw, X((37, 76))[1]), (X((36, 88))[0] + sw * 1.4,
                  X((36, 88))[1]), 16)
    poly = left + [X((56, 94)), X((66, 88)), X((78, 64)), X((84, 48)), X((68, 43))]
    cape = clean(poly_mask(poly))

    def cfold(x, y):
        u = x + (y - 50) * 0.55
        t = max(0.0, min(1.0, (y - 48) / 40))
        return (0.7 * math.sin(u * 0.33 + 0.8 * math.sin(ph)) * (0.3 + 0.7 * t), -0.1)
    Cp.paint(C.n_plate(cape, bevel=6, tilt=(0.05, -0.05), strength=1.2, fold=cfold), "K", bias=-1, rim=True)
    for k, spec in enumerate(C.TAILS):
        if spec[3] != "b":
            continue
        pts, w0 = tail_pts(j, k, spec)
        m, par, _ = C.ribbon(pts, w0, 0.5, bulge=0.15, ex=0.8)
        Cp.paint(C.n_ribbon(m, par, seed=spec[4] + 0.6 * math.sin(ph)), "K", bias=-1 if k == 0 else 0, rim=True)
        if k == 2:
            C.ink_script(Cp, pts, 0.2, 0.65, k, 0.5)
        info["tails"].append((Cp, m, par))
    R = L["Robe"]
    back = bezier(X((57, 49)), X((58, 64)), X((61, 80)), X((63, 93)), 14)
    front = bezier(X((78, 93)), X((82, 80)), X((86, 66)), X((88, 50)), 14)
    robe = clean(poly_mask(back + [X((70, 95))] + front + [X((74, 45))]))
    apex = X((73, 30))

    def rfold(x, y):
        a = math.atan2(x + .5 - apex[0], y + .5 - apex[1])
        w = 0.5 * math.sin(a * 7.5 + 0.8 + 0.3 * math.sin(ph)) + 0.1 * math.sin(a * 15 + 2.0)
        cx = X((72 - (y - 50) * 0.08, y))[0]
        w += 0.9 * max(-1.0, min(1.0, (x + .5 - cx) / 13.0))
        return (w, -0.1)
    R.paint(C.n_plate(robe, bevel=7, tilt=(0.02, -0.12), strength=1.5, fold=rfold), "K", rim=True)
    C.ink_script(R, bezier(X((80, 60)), X((79, 70)), X((76, 80)), X((72, 94)), 30), 0.0, 1.0, 11, 0.0)
    info["robe"] = robe
    for k, spec in enumerate(C.TAILS):
        if spec[3] != "f":
            continue
        pts, w0 = tail_pts(j, k, spec)
        m, par, _ = C.ribbon(pts, w0, 0.5, bulge=0.2, ex=0.8)
        R.paint(C.n_ribbon(m, par, seed=spec[4] + 1.0 + 0.6 * math.sin(ph)), "K", rim=True)
        if k == 4:
            C.ink_script(R, pts, 0.12, 0.66, k, -0.5)
        info["tails"].append((R, m, par))
    if p.get("phase", 1) == 1 and not p.get("no_wisps"):
        for k in (0, 1, 3, 5):
            pts, _ = tail_pts(j, k, C.TAILS[k])
            e = pts[-1]
            d = unit(sub(pts[-1], pts[-4]))
            wp = qbez(add(e, mul(d, -1.0)), add(e, add(mul(d, 4), (-1, 0.5))),
                      add(e, (-6 - k * 0.5, 1.0 + 1.2 * math.sin(ph + k))), 10)
            px = curve_px(wp)[:-1]
            lay = Cp if C.TAILS[k][3] == "b" else R
            lay.paint({q: (-0.4, -0.6, 0.7) for q in px if q not in lay.px}, "K", bias=0, ao=0)


C.draw_cloak = draw_cloak


# =========================================================================== scythe by (grip, angle)
def scythe_from(sc):
    """sc: dict(g=(x,y) grip, ang=deg (butt->head), lh, lb, s, k[, g2=offset along haft for 2nd hand])"""
    u = (math.cos(math.radians(sc["ang"])), math.sin(math.radians(sc["ang"])))
    g = sc["g"]
    head = add(g, mul(u, sc.get("lh", 66.7)))
    butt = sub(g, mul(u, sc.get("lb", 47.6)))
    grips = [g]
    if sc.get("g2") is not None:
        grips.append(sub(g, mul(u, sc["g2"])))
    return dict(head=head, butt=butt, s=sc.get("s", 1), k=sc.get("k", 0.88), grips=grips)


def blade_poly(sc):
    s = scythe_from(sc)
    Hd, Bt, u, v, k, Wd = C.scythe_frame(s)
    poly = [Wd(q) for q in C.BLADE_SPINE] + [Wd(q) for q in C.BLADE_EDGE[1:]]
    return poly, [Wd(q) for q in C.BLADE_EDGE], Wd(C.BLADE_SPINE[-1])


def lerp_sc(a, b, t):
    da = (b["ang"] - a["ang"] + 540) % 360 - 180
    out = dict(a)
    out["g"] = lerp(a["g"], b["g"], t)
    out["ang"] = a["ang"] + da * t
    for key in ("lh", "lb", "k"):
        out[key] = a.get(key, {"lh": 66.7, "lb": 47.6, "k": 0.88}[key]) * (1 - t) + \
            b.get(key, {"lh": 66.7, "lb": 47.6, "k": 0.88}[key]) * t
    return out


def fx_swept(F, sc0, sc1, n=12, ink=True, tipline=True, info=None):
    """Swept smear of the blade between two scythe poses: bright cutting line on the leading edge, violet
    bands, a translucent ink body fading toward the older end."""
    age = {}
    edge = {}
    for i in range(n + 1):
        t = i / n
        s = lerp_sc(sc0, sc1, t)
        poly, ecurve, tip = blade_poly(s)
        a = 1.0 - t
        for q in poly_mask(poly):
            if q not in age or a < age[q]:
                age[q] = a
        for q in curve_px(ecurve[len(ecurve) // 3:]):
            if q not in edge or a < edge[q]:
                edge[q] = a
    cur = set(poly_mask(blade_poly(sc1)[0]))
    swept = set()
    for q, a in age.items():
        if q in cur:
            continue
        swept.add(q)
        if q in edge and edge[q] < 0.75:
            F.put([q], "V4" if edge[q] < 0.35 else "V3", 255)
        elif a < 0.3:
            F.put([q], "V2", 255)
        elif a < 0.6:
            F.put([q], "V1", 190)
        elif a < 0.85:
            F.put([q], "K5" if ink else "V0", 130)
        else:
            F.put([q], "K4", 70)
    if info is not None:
        info["smear"] = swept
    return swept


# =========================================================================== render
NAMES = ["TailsB", "FarSleeve", "FarArm", "FarHand", "Robe", "NearSleeve", "Mantle", "Hood", "Head", "Scythe",
         "NearArm", "NearHand", "Chain"]
ORDER_IDLE = ["FXB", "TailsB", "FarSleeve", "FarArm", "FarHand", "Robe", "NearSleeve", "Mantle", "Hood", "Head",
              "Smear", "Scythe", "NearArm", "NearHand", "Chain", "Glow", "FX"]
BODY = set(NAMES) - {"Scythe"}


def finalize(p):
    """Pose coordinates for wrists / scythe / ring are authored in absolute concept space for bob = 0;
    here the vertical bob is added so the whole figure floats together."""
    b = p.get("bob", 0.0)
    sh = lambda q: (q[0], q[1] + b)
    p = dict(p)
    for key in ("near", "far"):
        a = dict(p[key])
        a["wrist"] = sh(a["wrist"])
        p[key] = a
    sc = dict(p["sc"])
    sc["g"] = sh(sc["g"])
    p["sc"] = sc
    if "ring" in p:
        r = dict(p["ring"])
        r["c"] = sh(r["c"]); r["palm"] = sh(r["palm"])
        p["ring"] = r
    if "sc_prev" in p and p["sc_prev"] is not None:
        sp = dict(p["sc_prev"]); sp["g"] = sh(sp["g"]); p["sc_prev"] = sp
    return p


def render(p, fi=0):
    """-> (dict of FWxFH layer images, info)"""
    p = finalize(p)
    j = C.joints(p)
    j["lift"] = p.get("lift", 0.0)
    info = {"j": j, "p": p}
    L = {n: Layer(n) for n in NAMES}
    G = FXLayer("Glow")
    F = FXLayer("FX")
    Fb = FXLayer("FXB")
    Sm = FXLayer("Smear")
    phase = p.get("phase", 1)
    draw_cloak(L, j, p, info)
    sc = scythe_from(p["sc"])
    info["sc"] = sc
    hu = unit(sub(sc["head"], sc["butt"]))
    arms = {}
    for key in ("far", "near"):
        arm = dict(p[key])
        for gp in sc["grips"]:
            if math.hypot(*sub(gp, arm["wrist"])) < 5.5:
                arm["grip"] = gp; arm["haft_u"] = hu
        arms[key] = arm
    C.draw_arm(L["FarSleeve"], L["FarArm"], L["FarHand"], j, arms["far"], info, "far", far=True)
    C.draw_arm(L["NearSleeve"], L["NearArm"], L["NearHand"], j, arms["near"], info, "near")
    pc = dict(p)
    C.draw_chain(L["Chain"], G, j, pc, info, phase)
    C.draw_mantle(L, j, p, info)
    if phase == 1:
        C.draw_hood(L, G, j, p, info)
        if p.get("crack", 0) > 0:
            hood_cracks(L["Hood"], G, info, p["crack"], fi)
    else:
        C.draw_torn_hood(L, j, p, info)
        C.draw_skull(L, G, j, p, info)
        if p.get("crown", 1.0) > 0:
            crown(F, j, info, fi, p.get("crown", 1.0))
    if p.get("scythe", True):
        C.draw_scythe(L["Scythe"], G, j, sc, info, phase)
    info["blade_tip"] = blade_poly(p["sc"])[2]
    if phase == 2 and p.get("burn", 1.0) > 0:
        C.burn_tails(L, info, F, fi)
    if p.get("sc_prev") is not None:
        fx_swept(Sm, p["sc_prev"], p["sc"], info=info)
    if "ring" in p:
        ring(Fb, F, p["ring"], fi, phase)
    if p.get("eyes", 0) > 0 and "eye" in info:
        eye_flare(G, F, info["eye"], p["eyes"], phase)
    sil = set()
    for n in NAMES:
        sil |= set(L[n].px)
    rim = "RIMR" if phase == 2 else "RIM"
    imgs = {n: _render_layer(L[n], rim, sil) for n in NAMES}
    imgs["Glow"], imgs["FX"], imgs["FXB"], imgs["Smear"] = G.image(), F.image(), Fb.image(), Sm.image()
    info["body_px"] = {q for n in NAMES if n != "Scythe" for q in L[n].px}
    info["blade_px"] = set(info.get("blade", set()))
    info["FX"] = F
    info["FXB"] = Fb
    info["Glow"] = G
    return imgs, info


def flatten(imgs, order):
    out = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    for n in order:
        if n in imgs:
            out.alpha_composite(imgs[n])
    return out


# =========================================================================== extra decoration
def hood_cracks(Hd, G, info, k, fi):
    """transformation: crimson fractures spread across the hood, the eyes turn from violet to red"""
    Hx = info["Hx"]
    lines = [[(56, 6), (60, 12), (58, 18), (63, 24)], [(66, 10), (68, 16), (66, 22), (70, 27)],
             [(62, 30), (65, 36), (63, 41)], [(78, 12), (80, 18), (84, 24)]]
    for li, cr in enumerate(lines):
        if k < 0.2 + li * 0.18:
            continue
        px = curve_px([Hx(q) for q in cr])
        n = int(len(px) * min(1.0, (k - 0.2 - li * 0.18) * 3 + 0.3))
        Hd.decal(px[:n], "R2")
        Hd.decal(px[1:n:2], "R4" if k > 0.6 else "R3")
        G.under([(q[0] + 1, q[1]) for q in px[:n]] + [(q[0] - 1, q[1]) for q in px[:n]], "R1", 70)


def crown(F, j, info, fi, k):
    if k >= 1.0:
        return C.crown_of_script(F, j, info, fi)
    tmp = FXLayer("tmp")
    C.crown_of_script(tmp, j, info, fi)
    c = info["Hx"]((75.5, 19.6))
    for q, col in tmp.px.items():
        # grow from the ring outward: keep pixels near the ring line first, flames last
        d = abs(q[1] - c[1]) / 12.0
        if d < k * 1.2:
            F.px[q] = col


def ring(Fb, F, rg, fi, phase):
    r = rg["r"]
    if r <= 0:
        return
    if r < 7:          # early charge: a converging knot of glyph light at the palm
        h = ipt(rg["palm"])
        cols = ("V4", "V3", "V1") if phase == 1 else ("R5", "R4", "R2")
        F.put([h], cols[0])
        F.put([(h[0] + a, h[1] + b) for a, b in N4], cols[1], 190)
        for kk in range(int(4 + r * 2)):
            a = hash01(kk, fi, 3) * 6.28
            d = (8 - r) * (0.6 + 0.8 * hash01(kk, fi, 4))
            F.put([(h[0] + math.cos(a) * d, h[1] + math.sin(a) * d)], cols[1] if kk % 2 else cols[2], 190)
        return
    tmpb, tmpf = FXLayer("b"), FXLayer("f")
    C.fx_glyph_ring(tmpb, tmpf, rg, fi)
    if phase == 2:
        remap = {RGBA["V0"][:3]: "R0", RGBA["V1"][:3]: "R1", RGBA["V2"][:3]: "R2", RGBA["V3"][:3]: "R4",
                 RGBA["V4"][:3]: "R5"}
        for lay, dst in ((tmpb, Fb), (tmpf, F)):
            for q, c in lay.px.items():
                nc = remap.get(c[:3])
                dst.px[q] = (RGBA[nc][:3] + (c[3],)) if nc else c
    else:
        Fb.px.update(tmpb.px)
        F.px.update(tmpf.px)
    if rg.get("flash"):
        c = rg["c"]
        for kk in range(16):
            a = 2 * math.pi * kk / 16 + 0.2
            for d in range(r + 2, r + 2 + rg["flash"]):
                F.put([(c[0] + math.cos(a) * d, c[1] + math.sin(a) * d)], "V4" if phase == 1 else "R5",
                      255 if d < r + 4 else 190)


def eye_flare(G, F, e, k, phase):
    col = ("V2", "V3", "V4") if phase == 1 else ("R2", "R4", "R5")
    F.put([e, (e[0] + 1, e[1])], col[2])
    n = int(2 + 5 * k)
    F.put([(e[0] + 2 + i, e[1] - (i // 3)) for i in range(n)], col[1], 190)
    F.put([(e[0] + 2 + i, e[1] - (i // 3) + 1) for i in range(n // 2)], col[0], 130)
    G.under([(e[0] + a, e[1] + b) for a in range(-3, 5) for b in range(-3, 4) if abs(a) + abs(b) <= 4], col[0], 70)


# =========================================================================== post effects on frame images
def clip_below(imgs, y_surface, names, fi, phase=1):
    """ink sink: everything below the ink surface line disappears; a violet meniscus where the body enters"""
    rim = RGBA["V2" if phase == 1 else "R3"]
    rim2 = RGBA["V1" if phase == 1 else "R1"]
    ys = int(y_surface)
    for n in names:
        im = imgs.get(n)
        if im is None:
            continue
        px = im.load()
        for y in range(max(0, ys), FH):
            for x in range(FW):
                if px[x, y][3]:
                    if y <= ys + 1 and n not in ("FX", "Glow"):
                        px[x, y] = rim if y == ys else rim2
                    else:
                        px[x, y] = (0, 0, 0, 0)


def puddle(F, cx, cy, rx, ry, phase=1, fi=0, splash=0.0):
    """ink pool on the floor (concept coords): black glossy ellipse, violet rim, ripples"""
    hi = "V2" if phase == 1 else "R3"
    mid = "V1" if phase == 1 else "R1"
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            e = ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2
            if e > 1.0:
                continue
            if e > 0.72:
                F.put([(x, y)], hi if y < cy else mid, 255 if y < cy else 190)
            else:
                F.put([(x, y)], "K1" if (y - cy) > -ry * 0.3 else "K2")
    for kk in range(3):
        rr = rx * (0.35 + 0.22 * kk + 0.1 * ((fi * 0.37 + kk * 0.3) % 1.0))
        for i in range(int(rr * 3)):
            a = math.pi * (0.15 + 0.7 * i / max(1, rr * 3 - 1))
            q = (cx + math.cos(a) * rr, cy - math.sin(a) * rr * ry / rx * 0.8)
            F.put([q], mid, 130)
    if splash > 0:
        for kk in range(int(10 * splash) + 4):
            a = math.pi * (0.1 + 0.8 * hash01(kk, fi, 31))
            d = rx * (0.4 + 0.9 * hash01(kk, fi, 32)) * splash
            h = 6 + 26 * splash * hash01(kk, fi, 33)
            q = (cx + math.cos(a) * d, cy - h * math.sin(a))
            F.put([q, (q[0], q[1] + 1)], "K3")
            F.put([(q[0], q[1] - 1)], hi, 190)


def dissolve(imgs, d, names, fi, phase=1):
    """death: the body unravels into ink from the tails upward; the front of the dissolve burns violet"""
    if d <= 0:
        return
    edge1 = RGBA["V3" if phase == 1 else "R4"]
    edge2 = RGBA["V1" if phase == 1 else "R2"]
    for n in names:
        im = imgs.get(n)
        if im is None:
            continue
        px = im.load()
        for y in range(FH):
            ky = (FH - 6 - y) / (FH - 10)
            for x in range(FW):
                if not px[x, y][3]:
                    continue
                # vertical ink runs: whole columns unravel at slightly different speeds (no speckle)
                key = ky * 0.78 + C.vnoise(x / 3.0, 77) * 0.22
                thr = d * 1.12
                if key < thr:
                    px[x, y] = (0, 0, 0, 0)
                elif key < thr + 0.018:
                    px[x, y] = edge1
                elif key < thr + 0.045:
                    px[x, y] = edge2
