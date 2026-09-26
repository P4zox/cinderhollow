"""db_eel -- the lantern eel (72x32, anchor = body centre [36,16], faces right). See gen_barrows_enemies.py.

A long sleek black-green eel that hunts in the black tide: glossy skin, a pale belly line, a faint row of
bioluminescent pores along the flank, a dark fin ridge along the back running into a ribbon tail, a narrow head
with needle teeth and an anglerfish lure (thin stalk + glowing teal bulb) rising from the head.
The spine is built by integrating a travelling-wave curvature along a FIXED arc length, so the body keeps the
same length and girth in every frame; each pose is re-centred on the anchor.
Tags: swim(6 loop) lunge(8) hurt(2) death(6).
"""
import math
import enemy_kit as K
from enemy_kit import Layer, FXLayer, ip, line, hash01, n_plate, n_dome, poly_mask, dirv, mask_disc
import spire_enemy_kit as S
from spire_enemy_kit import mk, madd, curve
import barrows_enemy_kit as B

SPEC = dict(swim=6, lunge=8, hurt=2, death=6)
LAYERS = ["FinB", "Body", "Head", "Lure", "FX"]
CX, CY = 36.0, 16.0
LEN = 58.0          # snout -> tail tip (arc length)
HINGE = 9.0         # jaw hinge (arc length from the snout)
DS = 0.5

NEU = dict(A=36.0, lam=34.0, ph=0.0, env0=0.22, curl=0.0, head=0.0, align=True, dx=0.0, dy=0.0, gape=0.0,
           glow=1.0, flare=0.0, streak=0, snap=False, flash=False, limp=0.0, wind=0.0, eye=2, lsway=0.0,
           bubbles=True, bbox=False)
EP = mk(NEU)


def radius(s):
    pts = [(0.0, 2.8), (HINGE, 3.0), (12.0, 3.35), (18.0, 3.6), (30.0, 3.3), (40.0, 2.6), (48.0, 1.75), (54.0, 1.0),
           (LEN, 0.6)]
    for (a, ra), (b, rb) in zip(pts, pts[1:]):
        if a <= s <= b:
            t = (s - a) / (b - a)
            return ra + (rb - ra) * t
    return 0.55


def spine(p):
    """Return list of (point, dir) from the snout (s=0) to the tail tip, dir = tail->head unit vector."""
    n = int(LEN / DS) + 1
    ang = []
    for i in range(n):
        s = i * DS
        env = p["env0"] + (1 - p["env0"]) * min(1.0, s / (LEN * 0.8))
        a = p["A"] * env * math.sin(2 * math.pi * s / p["lam"] - p["ph"]) + p["curl"] * s
        ang.append(math.radians(p["head"] + a))
    # integrate backwards from the snout
    pts = [(0.0, 0.0)]
    for i in range(1, n):
        a = ang[i]
        x, y = pts[-1]
        pts.append((x - math.cos(a) * DS, y - math.sin(a) * DS))
    if p["align"]:
        # rotate so the tail -> snout chord of the body (not the head) is horizontal
        tx, ty = pts[-1]
        hx, hy = pts[int(10 / DS)]
        rot = -math.atan2(hy - ty, hx - tx)
        c, s_ = math.cos(rot), math.sin(rot)
        pts = [(x * c - y * s_, x * s_ + y * c) for x, y in pts]
        ang = [a + rot for a in ang]
    # centre: mean of the spine (body mass) on the anchor (bbox centre for curled/limp poses)
    if p["bbox"]:
        mx = (min(x for x, _ in pts) + max(x for x, _ in pts)) / 2
        my = (min(y for _, y in pts) + max(y for _, y in pts)) / 2
    else:
        mx = sum(x for x, _ in pts) / len(pts)
        my = sum(y for _, y in pts) / len(pts)
    ox, oy = CX - mx + p["dx"], CY - my + p["dy"]
    return [((x + ox, y + oy), (math.cos(a), math.sin(a))) for (x, y), a in zip(pts, ang)]


def tube(samples, start):
    """Variable-radius tube along the spine samples from index `start` -> {pix: (normal, u, s)};
    u = signed offset across the body / r (+ = belly side)."""
    xs = [q[0][0] for q in samples[start:]]
    ys = [q[0][1] for q in samples[start:]]
    out = {}
    for y in range(int(min(ys)) - 5, int(max(ys)) + 6):
        for x in range(int(min(xs)) - 5, int(max(xs)) + 6):
            px, py = x + .5, y + .5
            best = None
            for i in range(start, len(samples)):
                (sx, sy), d = samples[i]
                r = radius(i * DS)
                dx, dy = px - sx, py - sy
                if abs(dx) > r or abs(dy) > r:
                    continue
                q = (dx * dx + dy * dy) / (r * r)
                if q <= 1 and (best is None or q < best[0]):
                    bn = (-d[1], d[0])
                    best = (q, dx / r, dy / r, (dx * bn[0] + dy * bn[1]) / r, i * DS)
            if best:
                _, nx, ny, u, s = best
                out[(x, y)] = (K.norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny))), u, s)
    return out


def draw_eel(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    sp = spine(p)
    hi = int(HINGE / DS)
    # ---- body
    Bd = Ls["Body"]
    tb = tube(sp, hi - 2)
    Bd.paint({q: v[0] for q, v in tb.items()}, "dE", 0)
    limp = p["limp"]
    # pale belly line: a clean 1px line along the lower flank, fading toward the tail
    bl = []
    for i in range(hi, len(sp) - int(5 / DS)):
        (x, y), d = sp[i]
        r = radius(i * DS)
        bl.append((x - d[1] * 0.6 * r, y + d[0] * 0.6 * r))
    for j, q in enumerate(dict.fromkeys(K.polyline([ip(q) for q in bl]))):
        if q in Bd.px:
            Bd.decal([q], ("dF", 4 if j < len(bl) * 0.35 else 3 if j < len(bl) * 0.7 else 2))
    # lateral line of bioluminescent pores (sparse, restrained)
    if p["glow"] > 0.1:
        for k, s in enumerate((14, 19, 24, 29, 34, 39)):
            (x, y), d = sp[int(s / DS)]
            bn = (-d[1], d[0])
            q = ip((x + bn[0] * 0.3 * radius(s), y + bn[1] * 0.3 * radius(s)))
            if q in Bd.px:
                on = (k + fi) % 3 != 0 or p["flare"] > 0
                Bd.fixed({q: ("dG3" if p["flare"] > 0.5 else "dG2") if on else "dG1"})
    # gill slit behind the head
    (gx, gy), gd = sp[int(10.5 / DS)]
    bn = (-gd[1], gd[0])
    Bd.decal([q for q in line((gx - bn[0] * 1.6, gy - bn[1] * 1.6), (gx + bn[0] * 1.4, gy + bn[1] * 1.4))
              if q in Bd.px], ("dE", 1))
    # ---- fins: dorsal ridge into a ribbon tail, small ventral fin
    Fn = Ls["FinB"]
    edge_top, edge_bot, base_top, base_bot = [], [], [], []
    for i in range(int(12 / DS), len(sp)):
        s = i * DS
        (x, y), d = sp[i]
        bn = (-d[1], d[0])
        r = radius(s)
        h = 0.0
        if s < 22:
            h = 3.0 * (s - 12) / 10
        elif s < 44:
            h = 3.0 - 1.2 * (s - 22) / 22
        else:
            h = 1.8 + 1.4 * (s - 44) / (LEN - 44)
        wav = 0.35 * math.sin(s * 0.9 + fi * 1.4)
        base_top.append((x - bn[0] * (r - 0.4), y - bn[1] * (r - 0.4)))
        edge_top.append((x - bn[0] * (r + h + wav), y - bn[1] * (r + h + wav)))
        if s > 34:
            hb = 1.4 * (s - 34) / (LEN - 34) + 0.6
            base_bot.append((x + bn[0] * (r - 0.4), y + bn[1] * (r - 0.4)))
            edge_bot.append((x + bn[0] * (r + hb - wav), y + bn[1] * (r + hb - wav)))
    tipx, tipy = sp[-1][0]
    tail_tip = madd((tipx, tipy), (sp[-1][1], -2.2))
    fin = poly_mask(base_top + [tail_tip] + edge_top[::-1])
    fin |= poly_mask(base_bot + [tail_tip] + edge_bot[::-1])
    Fn.paint(n_plate(fin, 0.8, (-0.1, -0.3), 0.8), "dE", -1, ao=0)
    fedge = set(K.polyline([ip(q) for q in edge_top])) | set(K.polyline([ip(q) for q in edge_bot]))
    Fn.decal([q for q in fedge if q in Fn.px], ("dE", 5))
    for k, i in enumerate(range(0, len(edge_top), 5)):          # fin rays
        Fn.decal([q for q in line(base_top[i], edge_top[i]) if q in Fn.px], ("dE", 3))
    for k, i in enumerate(range(2, len(edge_bot), 5)):
        Fn.decal([q for q in line(base_bot[i], edge_bot[i]) if q in Fn.px], ("dE", 3))
    # ---- head: upper + lower jaw hinged at s = HINGE
    Hl = Ls["Head"]
    (hx, hy), hd = sp[hi]
    hang = math.degrees(math.atan2(hd[1], hd[0]))
    g = p["gape"]
    ua, la = hang - g * 0.55, hang + g * 0.45
    hinge = madd((hx, hy), ((-hd[1], hd[0]), 0.5))

    def jaw(ang, pts_uv):
        d = dirv(ang)
        n = (-d[1], d[0])
        return [(hinge[0] + d[0] * u + n[0] * v, hinge[1] + d[1] * u + n[1] * v) for u, v in pts_uv]
    up_pts = jaw(ua, [(-2.0, -3.6), (2.4, -3.3), (6.0, -2.1), (9.2, -0.7), (10.2, 0.25), (7.0, 0.4), (-2.0, 0.4)])
    lo_pts = jaw(la, [(-2.0, 0.0), (8.2, 0.0), (9.2, 0.4), (7.8, 1.4), (3.0, 2.7), (-2.0, 3.1)])
    lom = poly_mask(lo_pts)
    upm = poly_mask(up_pts)
    Hl.paint(n_plate(lom, 1.0, (-0.05, 0.25), 1.0), "dE", 0, ao=0)
    Hl.decal([q for q in lom if hash01(*q, 1) < 2 and q[1] >= min(y for _, y in lo_pts) + 1.5], ("dF", 2))
    Hl.paint(n_plate(upm, 1.2, (-0.15, -0.3), 1.0), "dE", 1, ao=0)
    if g > 6:          # lit lip ridges so the open jaws read as two blades
        Hl.decal([q for q in line(jaw(ua, [(0.0, -2.6)])[0], jaw(ua, [(9.0, -0.4)])[0]) if q in upm], ("dE", 5))
        Hl.decal([q for q in line(jaw(la, [(0.0, 2.2)])[0], jaw(la, [(8.0, 0.8)])[0]) if q in lom], ("dE", 4))
    info["hit"] |= lom | upm
    # mouth: dark gape between the jaws + needle teeth
    if g > 6:
        d_u, d_l = dirv(ua), dirv(la)
        mouth = poly_mask([madd(hinge, (d_u, -0.5)), (hinge[0] + d_u[0] * 6.4, hinge[1] + d_u[1] * 6.4),
                           (hinge[0] + d_l[0] * 5.8, hinge[1] + d_l[1] * 5.8)]) - upm - lom
        Hl.fixed({q: ("dG0" if math.hypot(q[0] + .5 - hinge[0], q[1] + .5 - hinge[1]) < 4.5 else "dC1")
                  for q in mouth})
        Hl.noout |= mouth
        teeth = {}
        for k, u in enumerate((2.6, 4.4, 6.2, 8.0)):
            a = ip((hinge[0] + d_u[0] * u - d_u[1] * 1.0, hinge[1] + d_u[1] * u + d_u[0] * 1.0))
            teeth[a] = "dB5" if k % 2 else "dB4"
        for k, u in enumerate((3.4, 5.2, 7.0)):
            b_ = ip((hinge[0] + d_l[0] * u + d_l[1] * 1.0, hinge[1] + d_l[1] * u - d_l[0] * 1.0))
            teeth[b_] = "dB4" if k % 2 else "dB5"
        Hl.fixed(teeth)
        info["hit"] |= set(teeth) | mouth
    else:
        d_u = dirv(hang)
        seam = line(hinge, (hinge[0] + d_u[0] * 8.8, hinge[1] + d_u[1] * 8.8))
        Hl.fixed({q: "OUT" for q in seam[:-1]})
        # needle teeth overlapping the closed lips
        for k, q in enumerate(seam[2:-1]):
            if k % 2 == 0:
                Hl.fixed({(q[0], q[1] + (1 if k % 4 == 0 else -1)): "dB4"})
    # eye: a small pale-teal bead
    eye = ip(madd(hinge, (dirv(ua), 4.4), ((-dirv(ua)[1], dirv(ua)[0]), -1.8)))
    ecol = {0: "dE1", 1: "dG1", 2: "dG2", 3: "dG4"}[p["eye"]]
    Hl.fixed({eye: ecol})
    info["eye"] = eye
    # ---- lure: thin stalk from the crown, curving forward, glowing bulb
    Lu = Ls["Lure"]
    du = dirv(ua)
    nu = (-du[1], du[0])
    base = madd(hinge, (du, 2.6), (nu, -3.0))
    lean = p["lsway"] + sw * 0.35
    c1 = madd(base, (du, -0.5 + lean * 0.3), (nu, -3.6))
    c2 = madd(base, (du, 1.6 + lean * 0.7), (nu, -6.6))
    bulb = madd(base, (du, 4.2 + lean), (nu, -7.2 + abs(lean) * 0.2))
    stalk = K.polyline([ip(q) for q in K.bezier(base, c1, c2, bulb, 10)])
    Lu.fixed({q: ("dF2" if i < len(stalk) * 0.4 else "dF3") for i, q in enumerate(stalk[:-1])})
    Lu.noout |= set(stalk)
    gl = p["glow"] + p["flare"]
    info["lure"] = bulb
    if gl > 0.05:
        if gl > 1.6:
            B.halo_dots(FX, bulb, 3.0 + p["flare"] * 1.2, 12, fi, ("dG2", "dG1", "dG0"), skip=set(stalk))
        elif gl > 0.6:
            B.halo_dots(FX, bulb, 2.6, 8, fi, ("dG1", "dG0"), skip=set(stalk))
        core = {}
        r = 1.25 + 0.35 * min(1.0, p["flare"])
        for q in mask_disc(bulb, r, r):
            dd = math.hypot(q[0] + .5 - bulb[0], q[1] + .5 - bulb[1]) / r
            core[q] = ("dG4" if gl > 1.2 else "dG3") if dd < 0.5 else ("dG3" if gl > 0.7 else "dG2") if dd < 0.9 \
                else "dG2"
        if not core:
            core = {ip(bulb): "dG3"}
        Lu.fixed(core)
        Lu.noout |= set(core)
        if p["flare"] > 0.6:
            B.star(FX, bulb, 3)
    else:
        Lu.fixed({ip(bulb): "dE3", (ip(bulb)[0] + 1, ip(bulb)[1]): "dE2"})
    # ---- teal light on the head from the lure (restrained)
    if gl > 0.5:
        B.glow_rim(Hl, bulb, 3.5 + gl * 1.2)
    # ---- fx
    if p["streak"]:
        for k, o in enumerate((-2.5, 0.0, 2.5)):
            (x, y), d = sp[int((12 + k * 6) / DS)]
            y0 = int(y + o)
            L_ = 6 + 3 * (k % 2)
            for j in range(L_):
                q = (int(x) - 3 - j - k * 2, y0)
                if q not in Bd.px and q not in Fn.px:
                    FX.put([q], "dW6" if j < 2 else "dW5" if j < 5 else "dW4")
    if p["snap"]:
        tip = madd(hinge, (dirv(hang), 10.4))
        B.star(FX, tip, 2, cols=("dB5", "dB4", "dW5"))
    if p["flash"]:
        B.star(FX, eye, 2, cols=("dG4", "dG3", "dG2"), diag=False)
    if p["bubbles"]:
        for k in range(3):
            t = ((fi / 6.0 + k / 3.0) % 1.0)
            (x, y), _ = sp[int((HINGE + 1) / DS)]
            q = ip((x - 2 - t * 6 + math.sin(k * 2 + t * 6) * 1.0, y - 3 - t * 9))
            if q[1] >= 0 and q not in Lu.px:
                FX.put([q], "dW6" if t < 0.4 else "dW5")
    return Ls, info


# =========================================================================== animation
def a_swim():
    return [(110, EP(ph=2 * math.pi * i / 6, lsway=0.6 * math.sin(2 * math.pi * i / 6 - 0.8),
                     glow=(1.0, 1.15, 1.25, 1.15, 1.0, 0.9)[i])) for i in range(6)]


def a_lunge():
    return [
        (120, EP(A=46.0, lam=28.0, ph=0.9, env0=0.35, dx=-2.0, lsway=-0.8, glow=1.3, eye=2)),
        (140, EP(A=64.0, lam=24.0, ph=1.4, env0=0.45, dx=-4.0, lsway=-1.4, glow=1.6, eye=3, gape=6)),
        (280, EP(A=70.0, lam=23.0, ph=1.6, env0=0.45, dx=-4.5, lsway=-1.6, glow=1.4, flare=1.2, eye=3, gape=12)),
        (60, EP(A=9.0, lam=40.0, ph=2.2, dx=3.4, lsway=-2.2, glow=1.4, flare=0.3, eye=3, gape=70, streak=1,
                wind=3, bubbles=False)),
        (70, EP(A=5.0, lam=44.0, ph=2.8, dx=4.2, lsway=-2.0, glow=1.3, eye=3, gape=78, streak=1, wind=3,
                bubbles=False)),
        (80, EP(A=7.0, lam=40.0, ph=3.4, dx=4.0, lsway=-1.2, glow=1.2, eye=3, gape=48, streak=1)),
        (110, EP(A=12.0, lam=36.0, ph=4.0, dx=3.0, lsway=0.6, glow=1.1, eye=2, gape=0, snap=True)),
        (150, EP(A=18.0, lam=34.0, ph=4.8, dx=0.8, lsway=1.0, glow=1.0, eye=2)),
    ]


def a_hurt():
    return [(90, EP(A=26.0, lam=60.0, ph=1.2, glow=0.6, flare=0.0, eye=3, gape=20, flash=True, lsway=1.6)),
            (140, EP(A=20.0, lam=44.0, ph=2.2, glow=0.9, eye=2, gape=6, lsway=0.8))]


def a_death():
    return [
        (100, EP(A=30.0, lam=56.0, ph=1.0, glow=0.9, eye=3, gape=24, flash=True, lsway=1.8)),
        (130, EP(A=14.0, lam=50.0, ph=1.6, curl=-1.0, bbox=True, glow=0.6, eye=1, gape=14, lsway=2.2)),
        (150, EP(A=8.0, lam=50.0, ph=2.0, curl=-1.9, bbox=True, glow=0.4, eye=1, gape=12, lsway=2.6)),
        (160, EP(A=4.0, lam=50.0, ph=2.2, curl=-2.6, bbox=True, glow=0.25, eye=0, gape=10, lsway=3.0,
                 bubbles=False)),
        (200, EP(A=2.0, lam=50.0, ph=2.3, curl=-3.0, bbox=True, glow=0.1, eye=0, gape=8, lsway=3.2, bubbles=False)),
        (900, EP(A=0.0, lam=50.0, ph=2.3, curl=-3.2, bbox=True, glow=0.0, eye=0, gape=8, lsway=3.4, bubbles=False)),
    ]


def build(build_ase):
    K.setup(72, 32)
    anims, infos = S.render_anims(SPEC, LAYERS, draw_eel,
                                  [("swim", a_swim), ("lunge", a_lunge), ("hurt", a_hurt), ("death", a_death)],
                                  sway_key="lsway", loops=("swim",))
    hb = S.hurtbox(anims, ["Body", "Head"], inset=(4, 1, 2, 1), floor=False, tag=0)
    hit = S.hit_rect(infos, "lunge", [3, 4, 5], floor=False)
    meta = {"native": 1, "frame": [72, 32], "anchor": [36, 16], "swimming": True,
            "hurtbox": hb,
            "attacks": {"lunge": {"active": [3, 5], "hit": hit}},
            "telegraph": {"lunge": {"frame": 2, "at": S.spawn_pt(infos["lunge"][2]["lure"])}},
            "light": {"lure_swim": S.spawn_pt(infos["swim"][0]["lure"]), "color": "#8ff0e0"},
            "notes": "faces right; lives underwater, anchor = body centre (not feet). The body keeps the same length "
                     "and girth in every frame and is re-centred on the anchor, so the engine can rotate the sprite "
                     "about the anchor along its velocity (e.g. when it leaps out of the water). swim: 6-frame "
                     "sinuous loop. lunge: 0-2 coil into a compressed S (2 = held, the lure flares bright = "
                     "telegraph), 3-5 ACTIVE: body straightens forward, jaws gape wide at the right end of the frame "
                     "(engine drives it forward on 3-5), 6 jaws snap shut, 7 recoil. death: goes limp and curls, "
                     "lure fades out (hold last; engine may let it sink). The lure bulb is a small teal light "
                     "source (optional point light at `light.lure_swim`)."}
    S.export("db_eel", LAYERS, anims, meta, build_ase)
    return meta
