"""Shared helpers for agent X's generators (gen_secrets*.py): palette additions on top of enemy_kit,
previews, hitbox previews and meta helpers (same conventions as gen_kalden.py)."""
import math, os
from PIL import Image, ImageDraw
import enemy_kit as K
from enemy_kit import hash01, ip, line, mask_disc

ART = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(ART, "previews")

EXTRA = {
    # ochre-saffron sash (faded pilgrim's dye)
    "J0": "#1a1008", "J1": "#3a220e", "J2": "#5e3a14", "J3": "#875418", "J4": "#b07424", "J5": "#d49a3c",
    # weathered straw (the pilgrim's hat)
    "H0": "#16110b", "H1": "#2a2014", "H2": "#43341e", "H3": "#5e4a2a", "H4": "#7c6538", "H5": "#a08650",
    # old sun-dark skin
    "E0": "#1e1412", "E1": "#3a2622", "E2": "#5a3c32", "E3": "#7c5646", "E4": "#a07860", "E5": "#c49c80",
    # ash-wind (pale, fixed FX colours)
    "Z0": "#3a3a46", "Z1": "#6a6a7a", "Z2": "#a4a4b2", "Z3": "#d8d8e2", "Z4": "#f6f6fa",
    # blackened bronze plate (the Champion)
    "U0": "#0b0a0c", "U1": "#18151a", "U2": "#282228", "U3": "#3c3236", "U4": "#5a4a48", "U5": "#8a7464",
    # bone-white blade
    "N0": "#2a2a30", "N1": "#50505a", "N2": "#84848e", "N3": "#b8b6ba", "N4": "#e2ded8", "N5": "#fffaf0",
    # ember glow (fixed)
    "X0": "#5a1408", "X1": "#a02a0c", "X2": "#e0561a", "X3": "#ff9a3a", "X4": "#ffd88a",
}
for k, v in EXTRA.items():
    K.HEX[k] = v
    K.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
for k in EXTRA:
    r = K.RAMP.setdefault(k[0], [])
    if k not in r:
        r.append(k)
K.SHINY["U"] = 0.93
K.SHINY["N"] = 0.9
K.SMEAR["wind"] = ["Z4", "Z3", "Z2", "Z1"]
K.SMEAR["staff"] = ["B5", "B4", "J4", "J2"]
K.SMEAR["bonew"] = ["N5", "N4", "N3", "N2"]
K.SMEAR["emberw"] = ["X4", "X3", "X2", "X1"]
RGBA = K.RGBA

BG = (92, 92, 98, 255)


def tube(R, L, pts, r0, r1, mat, bias=0, ao=0):
    n = len(pts)
    m = set()
    for i in range(n - 1):
        t0, t1 = i / (n - 1), (i + 1) / (n - 1)
        m |= R.cap(L, pts[i], pts[i + 1], r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1, mat, bias, ao=ao)
    return m


def rag_hem(x0, x1, y, fi, seed, depth=2.5, sway=0.0):
    pts = []
    n = max(2, int(abs(x1 - x0) / 1.6))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = depth * (0.3 + hash01(i, fi // 2, seed)) if i % 2 == 0 else depth * 0.15
        pts.append((x + sway * (0.4 + 0.6 * t), y + d))
    return pts


def star(FX, c, core, arm_):
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], core)
    for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0)):
        FX.put([(x + d[0], y + d[1])], arm_)


def flat_arc(FX, spec, pal, exclude=(), back=None, floor=None):
    """Horizontal sweep seen side-on: a flattened crescent. spec: c, rx, ry, th0, th1 (deg), w, fade."""
    cols = K.SMEAR[pal]
    cx, cy = spec["c"]
    rx, ry, th0, th1, wd = spec["rx"], spec["ry"], spec["th0"], spec["th1"], spec.get("w", 5.0)
    fade = spec.get("fade", 0.0)
    hot = set()
    floor = K.H - 1 if floor is None else floor
    for y in range(int(cy - ry - wd - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            ux, uy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = math.hypot(ux, uy)
            if d == 0:
                continue
            th = math.degrees(math.atan2(uy, ux))
            if th1 > 180 and th < th0:
                th += 360
            t = (th - th0) / (th1 - th0) if th1 != th0 else 0
            if not (0 <= t <= 1):
                continue
            thick = wd * (0.25 + 0.75 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7) * (1 - fade * 0.6)
            grad = math.hypot(ux / rx, uy / ry) / d
            dd = (1 - d) / max(grad, 1e-6)
            if dd < -0.5 or dd > thick:
                continue
            if (x, y) in exclude or not K.inb(x, y) or y > floor:
                continue
            age = 1 - t
            if fade and hash01(x, y, 77) < fade * 0.7:
                continue
            if age > 0.7 and int(dd) % 2 == 1:
                continue
            if dd < 1.2 and age < 0.5:
                c = cols[0]
            elif dd < thick * 0.45:
                c = cols[1] if age < 0.6 else cols[2]
            else:
                c = cols[2] if age < 0.5 else cols[3]
            (back if (back is not None and uy < -0.2) else FX).put([(x, y)], c)
            if age < 0.8 and not fade:
                hot.add((x, y))
    return hot


def bbox(pts, pad=0):
    pts = [p for p in pts if K.inb(*p)]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(K.W - 1, max(xs) + pad), min(K.H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def attack(infos, tag, a, b, x_min, both=False, floor_reach=True, min_h=0):
    rs = {}
    for k in range(a, b + 1):
        pts = set(infos[tag][k]["hit"])
        if not both:
            pts = {q for q in pts if q[0] >= x_min}
        r = bbox(pts)
        if r is None:
            continue
        if floor_reach:
            r[3] = K.H - r[1]
        if min_h and r[3] < min_h:
            r[1] = max(0, r[1] + r[3] - min_h); r[3] = min_h
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def preview_rows(tags, flats, path, scale=3):
    W, H = K.W, K.H
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 12
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(230, 230, 230, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def hitbox_preview(tags, flats, meta, path, scale=3):
    W, H = K.W, K.H
    start = {t: (a, b) for t, a, b in tags}
    rows = [(t, d["windows"] if "windows" in d else [d]) for t, d in meta["attacks"].items()]
    rows.append((tags[0][0], []))
    pad, lab = 2, 12
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(rows) * (H + pad + lab) * scale), (40, 40, 46, 255))
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        dd.text((4, y0 + 4), t + "   " + "   ".join(f"active {w['active']} hit {w['hit']}" for w in wins), fill=(230, 230, 230, 255))
        tg = meta.get("telegraph", {}).get(t)
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rr = w.get("rects", {}).get(str(k), w["hit"])
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rect(rr, (255, 50, 50, 255), 2)
            if tg and tg["frame"] == k:
                x, y = tg["at"]
                d.ellipse([(x - 3) * scale, (y - 3) * scale, (x + 3) * scale, (y + 3) * scale], outline=(0, 255, 255, 255), width=2)
            d.line([(ax * scale - 5, ay * scale - 2), (ax * scale + 5, ay * scale - 2)], fill=(255, 255, 0, 255), width=2)
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def closeup(flats, idxs, path, scale=5):
    W, H = K.W, K.H
    c = Image.new("RGBA", (W * len(idxs), H), BG)
    for j, i in enumerate(idxs):
        c.alpha_composite(flats[i], (j * W, 0))
    c.resize((W * len(idxs) * scale, H * scale), Image.NEAREST).save(path)


def pole_px(grip, ang, u0, u1, fi=0, wood=("W1", "W2", "W3", "W4"), cap="G", ends=(3.0, 2.5), ring_at=None,
            wind=0, bells=None):
    """A straight quarterstaff through `grip` along angle `ang` (deg), from u0 (butt) to u1 (head), frame coords.
    ~2px thick dark wood with a lit edge, brass caps on both ends, optional brass ring/bells/ribbon near the head.
    Returns (pix dict, set of staff pixels, head point, butt point)."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    vdir = (-sa, ca)
    lit = -(vdir[0] * K.LIGHT[0] + vdir[1] * K.LIGHT[1]) > 0
    out, pts = {}, set()
    g0 = grip
    R_ = max(abs(u0), abs(u1)) + 3
    for y in range(int(g0[1] - R_), int(g0[1] + R_) + 1):
        for x in range(int(g0[0] - R_), int(g0[0] + R_) + 1):
            dx, dy = x + .5 - g0[0], y + .5 - g0[1]
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if not (u0 - 0.5 <= u <= u1 + 0.5):
                continue
            hw = 1.05
            capped = u < u0 + ends[0] or u > u1 - ends[1]
            if capped:
                hw = 1.25
            if abs(v) > hw:
                continue
            side = v if lit else -v
            if capped:
                c = (cap + "4") if side > 0.3 else (cap + "2") if side < -0.3 else (cap + "3")
                if abs(u - u0) < 0.8 or abs(u - u1) < 0.8:
                    c = cap + "1"
            else:
                c = wood[3] if side > 0.35 else wood[0] if side < -0.35 else wood[2]
                if int(u * 1.3 + 0.5) % 7 == 3 and abs(v) < 0.5:
                    c = wood[1]            # grain knots
            if ring_at is not None and abs(u - ring_at) < 0.8:
                c = cap + ("4" if side > 0 else "2")
            out[(x, y)] = c
            pts.add((x, y))
    head = (g0[0] + ca * u1, g0[1] + sa * u1)
    butt = (g0[0] + ca * u0, g0[1] + sa * u0)
    return out, pts, head, butt
