"""New Pale Sovereign moves (phases 1-2) -- installed into gen_sovereign's namespace by main().

    import sovereign_moves; sovereign_moves.install(module)

Adds FX functions (light blade + arc smear, halo orbs, floor glyph ring, crown flare, ...) and the new
animation tags: lash, combo, petals, grab, grabhold, orbs, beam, spears, vanish, cross, rings, crown.
Every tag is posed with the same rig (P_ poses), so phase 2 (burning robes, shattered crown) comes for free.
"""
import math

S = None   # the gen_sovereign module (set by install)


# =========================================================================== FX
def fx_blade(FX, info, j, p, fi, prev, ang, length, solid=1.0):
    """Slender blade of light held in the near hand, pointing along ang (deg, 0 = right, 90 = down)."""
    c = info["hand_n"]
    d, n = S.dirv(ang), S.dirv(ang + 90)
    F = FX["FX"]
    st = S.add(c, S.mul(d, 1.5))
    tip = S.add(st, S.mul(d, length))
    w0 = 1.9
    poly = [S.add(st, S.mul(n, w0)), S.add(S.add(st, S.mul(d, length * 0.8)), S.mul(n, w0 * 0.9)), tip,
            S.add(S.add(st, S.mul(d, length * 0.8)), S.mul(n, -w0 * 0.9)), S.add(st, S.mul(n, -w0))]
    m = S.poly_mask(poly) | set(S.line(st, tip))
    pts = set()
    for q in m:
        if not S.inb(*q):
            continue
        ox, oy = q[0] + .5 - st[0], q[1] + .5 - st[1]
        t = (ox * d[0] + oy * d[1]) / length
        pd = abs(ox * n[0] + oy * n[1])
        if solid < 1 and S.hash01(q[0], q[1] + fi * 7, 21) > solid:
            if S.hash01(q[0], q[1], 22 + fi) > 0.7:
                F.put([q], "Y2")
            continue
        c_ = "L" if pd < 0.75 else "Y3" if pd < 1.4 else "Y2"
        if t > 0.9:
            c_ = "L" if pd < 1.0 else "Y3"
        F.put([q], c_)
        pts.add(q)
    # thin gold rim so the blade reads against the pale sky
    for q in list(pts):
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r = (q[0] + a, q[1] + b)
            if r not in pts and S.inb(*r):
                F.under([r], "Y1", 190)
    # root-guard: a short curled cross-guard at the hand
    for s_ in (-1, 1):
        g0 = S.add(st, S.mul(n, s_ * 2))
        g1 = S.add(S.add(st, S.mul(n, s_ * 4.5)), S.mul(d, -1.5))
        for q in S.line(g0, g1):
            F.put([q], "G4" if s_ < 0 else "G3")
    info.setdefault("blade_px", set()).update(pts)
    info["blade"] = (st, tip)


def fx_bsmear(FX, info, j, p, fi, prev, a0, a1, length, r0=8):
    """Crescent smear swept by the blade tip from angle a0 to a1 around the hand."""
    c = info["hand_n"]
    F = FX["FX"]
    span = a1 - a0
    sg = 1 if span >= 0 else -1
    span = abs(span)
    R = length + 2
    best = set()
    for y in range(int(c[1] - R) - 1, int(c[1] + R) + 2):
        for x in range(int(c[0] - R) - 1, int(c[0] + R) + 2):
            if not S.inb(x, y):
                continue
            ox, oy = x + .5 - c[0], y + .5 - c[1]
            r = math.hypot(ox, oy)
            if r < r0 or r > R:
                continue
            phi = math.degrees(math.atan2(oy, ox))
            k = ((phi - a0) * sg) % 360
            if k > span:
                continue
            u = k / max(1e-6, span)
            age = 1 - u
            radial = (r - r0) / max(1.0, R - r0)          # 1 at the tip ring
            v = age * 0.9 + (1 - radial) * 0.9
            if v > 0.95:
                continue
            if v > 0.6 and (x + y) % 2:
                continue
            F.put([(x, y)], S.smear_color(v, 0.5 if radial > 0.9 else 2.0))
            best.add((x, y))
    info["smear"] |= best


def fx_gather_at(FX, info, j, p, fi, prev, where, R, prog, n):
    c = j["Hc"] if where == "halo" else info["hand_f"] if where == "handf" else info["hand_n"]
    S.fx_converge(FX["FX"], c, R, prog, n, fi, seed=len(where) + 3)


def fx_halo_orbs(FX, info, j, p, fi, prev, n, r, R=19):
    c = j["Hc"]
    pts = []
    for k in range(n):
        a = -90 + (k - (n - 1) / 2) * (150 / max(1, n - 1)) + math.sin(fi * 0.7 + k) * 4
        q = S.add(c, S.mul(S.dirv(a), R))
        S.fx_orb(FX["FX"], FX["FXBack"], q, r, fi, rays=6 if r > 2.5 else 0)
        pts.append(q)
    info["halo_orbs"] = pts


def fx_glyph_ring(FX, info, j, p, fi, prev, k):
    """Flat ring of light traced on the floor under her (ring-nova telegraph)."""
    cx = j["Hm"][0]
    F = FX["FX"]
    for rr, col in ((22 + 60 * k, "Y2"), (12 + 30 * k, "Y1")):
        for t in range(0, 360, 2):
            x = cx + math.cos(math.radians(t + fi * 9)) * rr
            y = S.FLOOR - 1 + math.sin(math.radians(t + fi * 9)) * 2.2
            if S.inb(int(x), int(y)) and (t // 2 + fi) % 5:
                F.put([(int(x), int(y))], col)
    for t in range(0, 360, 30):
        x = cx + math.cos(math.radians(t - fi * 6)) * (22 + 60 * k)
        F.put([(int(x), S.FLOOR - 2), (int(x), S.FLOOR - 3)], "Y3")


def fx_crown_flare(FX, info, j, p, fi, prev, k):
    c = j["Hc"]
    S.fx_rays(FX["FX"], c, 17, 17 + 14 * k, 12, fi * 9, "Y3")
    S.fx_star(FX["FX"], S.add(c, (0, -17)), int(2 + 4 * k))
    info["crown_c"] = c


def fx_hand_star(FX, info, j, p, fi, prev, side, r):
    S.fx_star(FX["FX"], info["hand_" + side], r)


def fx_petal_burst(FX, info, j, p, fi, prev, n, reach):
    """Petal blades flung forward off the near wing."""
    c = info["heart"]
    for k in range(n):
        a = -40 + S.hash01(k, 3, 61) * 70
        dd = 20 + S.hash01(k, 4, 62) * reach
        q = S.add(c, S.mul(S.dirv(a), dd))
        S.petal(FX["FX"], q, a + S.hash01(k, fi, 63) * 90, big=k % 2 == 0)


def fx_streaks(FX, info, j, p, fi, prev, side, n=3):
    c = info["hand_" + side]
    for k in range(n):
        yy = int(c[1]) - 3 + k * 3
        for x in range(int(c[0]) - 30, int(c[0]) - 4):
            if (x + k * 3) % 8 < 5:
                FX["FXBack"].put([(x, yy)], "Y2" if k == 1 else "Y1", 190)


NEW_FX = {"blade": fx_blade, "bsmear": fx_bsmear, "gat": fx_gather_at, "haloorbs": fx_halo_orbs,
          "glyph": fx_glyph_ring, "crownflare": fx_crown_flare, "hstar": fx_hand_star, "pburst": fx_petal_burst,
          "streaks": fx_streaks}


# =========================================================================== animations
def arm_at(a, r=26, sh=(104, 55)):
    """Near-hand position for an arm pointing along angle a from the near shoulder."""
    return (sh[0] + math.cos(math.radians(a)) * r, sh[1] + math.sin(math.radians(a)) * r)


def anim_lash():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, lean, hn, hnd, hf, hfd, wl, wr, tendrils, fx
        (100, 0, -1, (122, 62), -20, (70, 64), 200, (WL0 + 4, 1.0, 1.0), (WR0 - 4, 1.0, 0.92), 0, ()),
        (110, -3, -4, (126, 46), -70, (68, 46), 250, (WL0 + 14, 1.1, 1.0), (WR0 - 14, 1.1, 0.95), 0,
         (("orb", "n", 1.5), ("orb", "f", 1.5))),
        (150, -5, -6, (125, 38), -85, (70, 38), 265, (WL0 + 20, 1.15, 1.0), (WR0 - 20, 1.15, 0.95), 0,
         (("orb", "n", 3.5, 8), ("orb", "f", 2.5))),                                              # telegraph
        (60, 2, 8, (138, 92), 60, (96, 98), 80, (WL0 - 10, 1.05, 1.0), (WR0 + 30, 1.1, 1.0), 0.6,
         (("groundglow", 0.6), ("streaks", "n", 2))),
        (80, 4, 10, (140, 100), 80, (98, 104), 90, (WL0 - 14, 1.0, 1.0), (WR0 + 36, 1.1, 1.02), 1.0,
         (("dust", 130, 1.4, 0), ("groundglow", 1.0))),                                           # spawn
        (110, 4, 9, (140, 100), 80, (98, 104), 90, (WL0 - 14, 1.0, 1.0), (WR0 + 34, 1.1, 1.0), 1.0,
         (("dust", 130, 1.4, 1), ("groundglow", 0.8))),
        (120, 3, 7, (138, 96), 80, (97, 100), 90, (WL0 - 10, 1.0, 1.0), (WR0 + 26, 1.05, 1.0), 0.9, (("groundglow", 0.5),)),
        (130, 2, 5, (132, 88), 70, (92, 92), 100, (WL0 - 6, 1.0, 1.0), (WR0 + 16, 1.0, 0.96), 0.6, ()),
        (130, 1, 3, (126, 80), 60, (82, 82), 120, (WL0 - 2, 1.0, 1.0), (WR0 + 8, 1.0, 0.94), 0.3, ()),
        (140, 0, 1, (121, 75), 50, (74, 72), 140, (WL0, 1.0, 1.0), (WR0 + 2, 1.0, 0.92), 0.1, ()),
        (160, 0, 0, (119, 73), 50, (71, 69), 150, (WL0, 1.0, 1.0), (WR0, 1.0, 0.92), 0.0, ()),
    ]
    fr = []
    for i, (ms, bob, lean, hn, hd, hf, hfd, wl, wr, tn, fx) in enumerate(K):
        fr.append((ms, S.P_(bob=bob, lean=lean, hn=hn, hn_dir=hd, hf=hf, hf_dir=hfd, wl=wl, wr=wr, tendrils=tn,
                            eln=(0.6, 0.6), elf=(-0.6, 0.6), eyes=1.0 if 2 <= i <= 6 else 0.3,
                            halo=1.0 + (0.6 if 1 <= i <= 4 else 0), wind=(0, 0, 0, 3, 4, 3, 2, 1, 0, 0, 0)[i], fx=fx)))
    return fr


def anim_combo():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, lean, dx, hn, hnd, blade(ang, len, solid) | None, extra fx
        (90, 0, -1, 0, (116, 60), -40, (-60, 30, 0.35), (("gat", "hand", 20, 0.5, 12),)),
        (100, -2, -4, 0, (112, 40), -100, (-110, 42, 1.0), ()),
        (150, -3, -6, 0, (111, 38), -105, (-116, 40, 1.0), (("hstar", "n", 3),)),                      # telegraph
        (60, 2, 8, 3, (134, 72), 40, (45, 70, 1.0), (("bsmear", -116, 45, 70),)),                       # slash 1
        (70, 3, 9, 4, (134, 78), 70, (75, 68, 1.0), (("bsmear", 35, 75, 68),)),
        (90, 2, 5, 3, (120, 88), 120, (130, 52, 1.0), ()),                                              # rewind low
        (60, -1, 6, 5, (134, 74), 20, (30, 70, 1.0), (("bsmear", 130, 30, 70),)),                       # slash 2 (rising)
        (70, -3, 4, 5, (132, 56), -40, (-40, 60, 1.0), (("bsmear", 30, -40, 60),)),
        (110, -1, -6, 1, (104, 66), 40, (40, 56, 1.0), ()),                                             # draw back
        (170, -1, -8, 0, (100, 66), 42, (42, 58, 1.0), (("hstar", "n", 2),)),                           # hold (delay)
        (230, -1, -9, -1, (99, 66), 42, (42, 60, 1.0), (("orb", "n", 2.5, 8),)),                        # hold longer
        (50, 2, 12, 8, (138, 70), 55, (58, 80, 1.0), (("streaks", "n", 3),)),                          # thrust
        (80, 2, 12, 9, (139, 71), 55, (58, 80, 1.0), (("streaks", "n", 2),)),
        (110, 1, 6, 5, (132, 72), 60, (62, 50, 0.6), ()),
        (130, 0, 2, 2, (124, 74), 70, (70, 30, 0.3), ()),
        (150, 0, 0, 0, (119, 73), 50, None, ()),
    ]
    fr = []
    for i, (ms, bob, lean, dx, hn, hd, bl, fx) in enumerate(K):
        fxs = tuple(fx) + ((("blade",) + bl,) if bl else ())
        # the smear is drawn before the blade so the blade stays on top
        fxs = tuple(f for f in fxs if f[0] == "bsmear") + tuple(f for f in fxs if f[0] != "bsmear")
        fr.append((ms, S.P_(bob=bob, lean=lean, dx=dx, hn=hn, hn_dir=hd, hf=(74 - dx * 0.3, 70), hf_dir=200,
                            eln=(0.3, 1), elf=(-0.4, 1), eyes=1.0 if 1 <= i <= 12 else 0.3,
                            shake=(1 if i == 10 else 0),
                            wl=(WL0 + (10 if i in (1, 2, 8, 9, 10) else -6 if i in (3, 4, 11, 12) else 0), 1.05, 1.0),
                            wr=(WR0 + (-14 if i in (1, 2, 8, 9, 10) else 12 if i in (3, 4, 11, 12) else 0), 1.05, 0.92),
                            wind=(-1, -2, -2, 5, 5, 2, 4, 3, -2, -3, -3, 6, 6, 3, 1, 0)[i], fx=fxs)))
    return fr


def anim_petals():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, lean, wr, wl, hn, hf, fx
        (110, 0, -2, (WR0 - 40, 0.9, 0.95), (WL0 + 30, 0.9, 1.0), (110, 62), (88, 62), (("petals", 6, 50, 0.2),)),
        (120, -2, -4, (WR0 - 70, 1.0, 1.0), (WL0 + 50, 1.0, 1.0), (108, 58), (86, 58), (("petals", 10, 70, 0.4),)),
        (150, -3, -5, (WR0 - 86, 1.05, 1.0), (WL0 + 62, 1.05, 1.0), (108, 56), (86, 56), (("petals", 14, 80, 0.6),)),
        (60, 2, 6, (WR0 + 30, 1.25, 1.15), (WL0 - 16, 1.1, 1.0), (134, 64), (84, 70), (("wsmear", "wr"), ("pburst", 8, 40))),
        (80, 3, 7, (WR0 + 42, 1.3, 1.2), (WL0 - 20, 1.1, 1.0), (136, 66), (84, 72), (("wsmear", "wr"), ("pburst", 12, 70))),
        (110, 2, 5, (WR0 + 36, 1.2, 1.15), (WL0 - 12, 1.05, 1.0), (132, 68), (82, 70), (("pburst", 6, 90),)),
        (120, -2, -3, (WR0 - 40, 1.05, 1.0), (WL0 + 40, 1.05, 1.0), (112, 60), (86, 58), (("petals", 10, 70, 0.5),)),
        (60, 2, 5, (WR0 + 26, 1.2, 1.12), (WL0 - 30, 1.15, 1.05), (134, 64), (80, 70), (("wsmear", "wr"), ("pburst", 8, 40))),
        (80, 3, 6, (WR0 + 38, 1.25, 1.15), (WL0 - 34, 1.2, 1.05), (136, 66), (78, 72), (("wsmear", "wr"), ("pburst", 12, 70))),
        (120, 2, 3, (WR0 + 20, 1.1, 1.05), (WL0 - 16, 1.05, 1.0), (128, 70), (76, 70), ()),
        (140, 1, 1, (WR0 + 6, 1.0, 0.95), (WL0 - 4, 1.0, 1.0), (122, 72), (72, 69), ()),
        (160, 0, 0, (WR0, 1.0, 0.92), (WL0, 1.0, 1.0), (119, 73), (71, 69), ()),
    ]
    fr = []
    for i, (ms, bob, lean, wr, wl, hn, hf, fx) in enumerate(K):
        fr.append((ms, S.P_(bob=bob, lean=lean, wr=wr, wl=wl, hn=hn, hn_dir=10, hf=hf, hf_dir=190,
                            eyes=1.0 if 2 <= i <= 8 else 0.3, halo=1.0 + (0.5 if 2 <= i <= 8 else 0),
                            wsway=2.0 if i in (3, 4, 7, 8) else 5.0,
                            wind=(0, -1, -2, 6, 6, 3, -2, 6, 6, 3, 1, 0)[i], fx=fx)))
    return fr


def anim_grab():
    """The near root-wing lunges down and seizes the player on the ground."""
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, lean, dx, wr, hn, hnd, fx
        (100, 0, -2, 0, (WR0 - 10, 1.0, 0.92), (116, 66), 20, ()),
        (110, -2, -5, -1, (-62, 0.85, 1.0), (110, 58), -30, (("orb", "n", 1.5),)),
        (170, -3, -7, -2, (-84, 0.75, 1.06), (108, 54), -50, (("orb", "n", 3.0, 8), ("gat", "hand", 18, 0.7, 10))),  # tel
        (60, 3, 10, 6, (48, 0.7, 1.36), (136, 70), 30, (("wsmear", "wr"), ("orb", "n", 2.0))),        # lunge
        (80, 4, 11, 8, (66, 0.62, 1.42), (138, 74), 50, (("wsmear", "wr"), ("dust", 150, 1.2, 0))),
        (90, 4, 11, 8, (72, 0.5, 1.4), (136, 76), 80, (("dust", 150, 1.2, 1),)),
        (120, 3, 8, 6, (60, 0.7, 1.25), (132, 76), 70, ()),
        (130, 2, 5, 4, (36, 0.85, 1.1), (126, 76), 60, ()),
        (130, 1, 3, 2, (10, 0.95, 1.0), (122, 75), 55, ()),
        (140, 0, 1, 1, (WR0 + 4, 1.0, 0.95), (120, 74), 50, ()),
        (160, 0, 0, 0, (WR0, 1.0, 0.92), (119, 73), 50, ()),
    ]
    fr = []
    for i, (ms, bob, lean, dx, wr, hn, hd, fx) in enumerate(K):
        fr.append((ms, S.P_(bob=bob, lean=lean, dx=dx, hn=hn, hn_dir=hd, hf=(72 - dx * 0.5, 68), hf_dir=200,
                            eln=(0.2, 1), eyes=1.0 if 1 <= i <= 6 else 0.3, wr=wr,
                            wl=(WL0 + (8 if i <= 2 else -8 if 3 <= i <= 5 else 0), 1.0, 1.0),
                            wsway=2.0 if 3 <= i <= 5 else 5.0,
                            wind=(0, -1, -2, 7, 7, 5, 3, 2, 1, 0, 0)[i], fx=fx)))
    return fr


def anim_grabhold():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, lean, dx, wr, hn, hnd, tendrils, fx
        (120, 4, 11, 8, (72, 0.5, 1.4), (136, 72), 60, 0.4, (("orb", "n", 2.5),)),
        (120, 3, 10, 8, (73, 0.45, 1.4), (134, 60), 0, 0.7, (("orb", "n", 3.0, 6),)),
        (140, 2, 9, 7, (73, 0.45, 1.4), (130, 48), -50, 0.9, (("orb", "n", 4.0, 8), ("gat", "hand", 22, 0.5, 12))),
        (180, 1, 8, 7, (74, 0.42, 1.4), (128, 42), -70, 1.0, (("orb", "n", 5.0, 12), ("gat", "hand", 22, 0.9, 16))),  # tel
        (60, 3, 12, 8, (70, 0.6, 1.42), (140, 82), 70, 0.8, (("hstar", "n", 6), ("streaks", "n", 3))),       # burst
        (90, 3, 11, 8, (66, 0.75, 1.36), (138, 80), 70, 0.4, (("hstar", "n", 3),)),
        (120, 2, 8, 6, (44, 0.9, 1.2), (132, 78), 60, 0.1, ()),
        (130, 1, 5, 4, (16, 0.95, 1.05), (126, 76), 55, 0.0, ()),
        (140, 0, 2, 2, (WR0 + 4, 1.0, 0.95), (122, 74), 50, 0.0, ()),
        (160, 0, 0, 0, (WR0, 1.0, 0.92), (119, 73), 50, 0.0, ()),
    ]
    fr = []
    for i, (ms, bob, lean, dx, wr, hn, hd, tn, fx) in enumerate(K):
        fr.append((ms, S.P_(bob=bob, lean=lean, dx=dx, hn=hn, hn_dir=hd, hf=(72 - dx * 0.5, 68), hf_dir=200, wr=wr,
                            eln=(0.4, 1), eyes=1.0 if i <= 5 else 0.3, tendrils=tn, halo=1.0 + (1.0 if 2 <= i <= 4 else 0),
                            crack=0.3 if 2 <= i <= 4 else 0.0, wsway=1.5 if i <= 5 else 5.0,
                            wl=(WL0 - (8 if i <= 5 else 0), 1.0, 1.0),
                            wind=(4, 3, 2, 1, 5, 3, 2, 1, 0, 0)[i], fx=fx)))
    return fr


def anim_orbs():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, hn, hnd, hf, hfd, fx
        (100, 0, (120, 60), -30, (76, 58), 210, ()),
        (110, -2, (124, 44), -70, (70, 44), 250, (("orb", "n", 2.0), ("orb", "f", 2.0))),
        (120, -3, (125, 40), -80, (69, 40), 260, (("orb", "n", 3.0), ("orb", "f", 3.0), ("haloorbs", 3, 1.5))),
        (130, -4, (125, 38), -80, (69, 38), 260, (("orb", "n", 4.0, 8), ("orb", "f", 3.5, 6), ("haloorbs", 3, 2.5))),
        (170, -5, (125, 37), -80, (69, 37), 260, (("orb", "n", 5.0, 12), ("orb", "f", 4.0, 8), ("haloorbs", 5, 3.2))),  # tel
        (60, 1, (140, 60), 0, (122, 64), 10, (("streaks", "n", 3), ("orb", "n", 3.0), ("haloorbs", 5, 2.0))),
        (90, 2, (141, 61), 0, (123, 65), 10, (("hstar", "n", 4),)),                                                   # spawn
        (120, 1, (136, 64), 20, (112, 66), 40, ()),
        (130, 0, (128, 68), 40, (96, 68), 120, ()),
        (140, 0, (122, 72), 50, (80, 69), 150, ()),
        (150, 0, (119, 73), 50, (71, 69), 150, ()),
    ]
    fr = []
    for i, (ms, bob, hn, hd, hf, hfd, fx) in enumerate(K):
        fr.append((ms, S.P_(bob=bob, hn=hn, hn_dir=hd, hf=hf, hf_dir=hfd, eln=(0.7, 0.3), elf=(-0.7, 0.3),
                            lean=(0, -2, -3, -4, -5, 7, 7, 4, 2, 1, 0)[i], eyes=1.0 if 2 <= i <= 7 else 0.3,
                            halo=1.0 + (0.9 if 2 <= i <= 5 else 0),
                            wl=(WL0 + (14 if 2 <= i <= 4 else -6 if 5 <= i <= 7 else 0), 1.1 if 2 <= i <= 4 else 1.0, 1.0),
                            wr=(WR0 - (14 if 2 <= i <= 4 else -10 if 5 <= i <= 7 else 0), 1.1 if 2 <= i <= 4 else 1.0, 0.92),
                            wind=(0, -1, -1, -2, -2, 6, 5, 3, 1, 0, 0)[i], fx=fx)))
    return fr


BEAM_ANG = [None, -35, -30, -25, -22, -20, -11, -2, 7, 15, 24, 32, 30, None, None, None]


def anim_beam():
    WL0, WR0 = S.WL0, S.WR0
    fr = []
    for i in range(16):
        a = BEAM_ANG[i]
        if a is None:
            hn, hd = ((118, 66), 30) if i == 0 else ((126, 72), 40) if i == 13 else ((122, 73), 50) if i == 14 else ((119, 73), 50)
        else:
            hn, hd = arm_at(a, 27), a
        fx = ()
        if i == 1:
            fx = (("gat", "hand", 20, 0.3, 10),)
        elif i == 2:
            fx = (("gat", "hand", 22, 0.6, 12), ("orb", "n", 2.0))
        elif i == 3:
            fx = (("gat", "hand", 22, 0.9, 14), ("orb", "n", 3.5, 8))
        elif i == 4:
            fx = (("orb", "n", 5.0, 12), ("hstar", "n", 5))                 # telegraph
        elif 5 <= i <= 11:
            fx = (("orb", "n", 4.0 + (i % 2), 10), ("hstar", "n", 6))      # firing: the beam itself is drawn by the engine
        elif i == 12:
            fx = (("orb", "n", 2.0),)
        ms = (100, 110, 120, 130, 190, 90, 90, 90, 90, 90, 90, 90, 120, 130, 140, 160)[i]
        lean = (0, -2, -3, -4, -5, -3, -1, 1, 2, 3, 5, 6, 5, 3, 1, 0)[i]
        fr.append((ms, S.P_(bob=(0, -1, -2, -2, -3, -2, -2, -1, -1, 0, 0, 1, 1, 0, 0, 0)[i], lean=lean, hn=hn, hn_dir=hd,
                            hf=(70, 70), hf_dir=200, eln=(0.3, 1), elf=(-0.5, 1),
                            eyes=1.0 if 2 <= i <= 12 else 0.3, halo=1.0 + (0.6 if 3 <= i <= 11 else 0),
                            wl=(WL0 + (8 if 1 <= i <= 4 else -6 if 5 <= i <= 11 else 0), 1.05, 1.0),
                            wr=(WR0 + (-10 if 1 <= i <= 4 else 8 if 5 <= i <= 11 else 0), 1.05, 0.92),
                            wind=(0, 0, -1, -1, -1, -3, -3, -3, -3, -3, -3, -3, -2, -1, 0, 0)[i], fx=fx)))
    return fr


def anim_spears():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, hn, hnd, hf, hfd, tendrils, halo, fx
        (100, 0, (120, 84), 90, (74, 84), 90, 0.0, 1.0, ()),
        (120, 2, (122, 90), 90, (72, 90), 90, 0.3, 1.1, (("orb", "n", 1.5), ("orb", "f", 1.5))),
        (130, 3, (123, 92), 90, (71, 92), 90, 0.5, 1.3, (("groundglow", 0.4), ("orb", "n", 2.5), ("orb", "f", 2.5))),
        (170, 2, (123, 76), -90, (71, 76), -90, 0.6, 1.6, (("groundglow", 0.8), ("orb", "n", 3.5, 8), ("orb", "f", 3.0, 6))),  # tel
        (60, -4, (126, 34), -90, (66, 34), -90, 0.3, 2.0, (("hstar", "n", 4), ("hstar", "f", 3))),
        (80, -5, (126, 32), -90, (66, 32), -90, 0.0, 2.0, (("hstar", "n", 3), ("hstar", "f", 2), ("dust", 96, 3.0, 0))),  # spawn
        (110, -4, (126, 34), -90, (66, 34), -90, 0.0, 1.7, (("dust", 96, 3.0, 1),)),
        (130, -3, (125, 44), -70, (67, 44), 250, 0.0, 1.4, ()),
        (140, -1, (122, 58), -20, (69, 58), 200, 0.0, 1.2, ()),
        (150, 0, (120, 68), 30, (70, 66), 170, 0.0, 1.0, ()),
        (160, 0, (119, 73), 50, (71, 69), 150, 0.0, 1.0, ()),
    ]
    fr = []
    for i, (ms, bob, hn, hd, hf, hfd, tn, halo, fx) in enumerate(K):
        up = 4 <= i <= 6
        fr.append((ms, S.P_(bob=bob, hn=hn, hn_dir=hd, hf=hf, hf_dir=hfd, tendrils=tn, halo=halo,
                            eln=(0.8, 0.4) if not up else (0.9, -0.2), elf=(-0.8, 0.4) if not up else (-0.9, -0.2),
                            eyes=1.0 if 2 <= i <= 7 else 0.3, lean=(0, 2, 3, 1, -4, -5, -4, -2, -1, 0, 0)[i],
                            wl=(WL0 + (-14 if i <= 3 else 22 if up else 6), 1.0 if i <= 3 else 1.2, 1.0),
                            wr=(WR0 - (-14 if i <= 3 else 22 if up else 6), 1.0 if i <= 3 else 1.2, 0.92),
                            wind=(0, 1, 2, 1, -3, -4, -3, -2, -1, 0, 0)[i], fx=fx)))
    return fr


def anim_vanish():
    WL0, WR0 = S.WL0, S.WR0
    fr = []
    for i in range(7):
        k = i / 6
        fr.append(((90, 90, 80, 80, 80, 80, 110)[i],
                   S.P_(bob=-int(k * 4), hn=(112, 64), hn_dir=190, hf=(86, 64), hf_dir=-10, eln=(0.6, 1), elf=(-0.6, 1),
                        wl=(WL0 + 20 * k, 1.0 - 0.3 * k, 1.0), wr=(WR0 - 20 * k, 1.0 - 0.3 * k, 0.92), eyes=1.0,
                        halo=1.0 + k, dissolve=(0.0, 0.12, 0.3, 0.5, 0.7, 0.92, 1.25)[i],
                        fx=(("petals", 8 + i * 3, 70, k * 1.5),))))
    return fr


def anim_cross():
    K = [  # ms, dissolve, lean, wr, wl, fx
        (80, 0.85, -4, (-100, 1.1, 1.0), (250, 1.1, 1.0), (("petals", 16, 70, 0.8),)),
        (80, 0.55, -4, (-102, 1.12, 1.0), (252, 1.12, 1.0), (("petals", 10, 70, 0.5),)),
        (80, 0.25, -5, (-104, 1.14, 1.02), (255, 1.14, 1.02), ()),
        (150, 0.0, -6, (-108, 1.15, 1.02), (258, 1.15, 1.02), (("flash", 3),)),                       # telegraph
        (60, 0.0, 8, (40, 1.25, 1.3), (380, 1.25, 1.25), (("wsmear", "wr"), ("wsmear", "wl"))),       # X slash
        (70, 0.0, 9, (62, 1.3, 1.35), (395, 1.3, 1.3), (("wsmear", "wr"), ("wsmear", "wl"), ("dust", 140, 1.6, 0))),
        (110, 0.0, 7, (56, 1.2, 1.3), (388, 1.2, 1.25), (("dust", 140, 1.6, 1),)),
        (130, 0.0, 4, (20, 1.1, 1.1), (330, 1.05, 1.05), ()),
        (140, 0.0, 2, (0, 1.05, 1.0), (275, 1.0, 1.0), ()),
        (150, 0.0, 1, (-12, 1.0, 0.95), (235, 1.0, 1.0), ()),
        (160, 0.0, 0, (S.WR0, 1.0, 0.92), (S.WL0 + 8, 1.0, 1.0), ()),
        (160, 0.0, 0, (S.WR0, 1.0, 0.92), (S.WL0, 1.0, 1.0), ()),
    ]
    fr = []
    for i, (ms, dis, lean, wr, wl, fx) in enumerate(K):
        fr.append((ms, S.P_(lean=lean, wr=wr, wl=wl, dissolve=dis, eyes=1.0 if i <= 6 else 0.3,
                            hn=(122, 68) if i < 4 else (130, 78) if i <= 6 else (120, 73), hn_dir=40,
                            hf=(74, 66) if i < 4 else (84, 76) if i <= 6 else (71, 69), hf_dir=180,
                            bob=(-3, -3, -2, -3, 2, 3, 2, 1, 0, 0, 0, 0)[i],
                            wsway=2.0 if i in (4, 5) else 5.0, wind=(0, 0, -1, -2, 6, 6, 3, 2, 1, 0, 0, 0)[i], fx=fx)))
    return fr


def anim_rings():
    WL0, WR0 = S.WL0, S.WR0
    K = [  # ms, bob, hn, hf, halo, glyph, fx
        (100, 0, (124, 74), (70, 74), 1.1, 0, ()),
        (110, -2, (132, 82), (62, 82), 1.3, 0, ()),
        (120, -4, (133, 82), (61, 82), 1.6, 0.4, (("groundglow", 0.3),)),
        (130, -5, (133, 81), (61, 81), 1.8, 0.7, ()),
        (140, -6, (134, 80), (60, 80), 2.0, 1.0, (("flash", 2),)),
        (180, -6, (134, 80), (60, 80), 2.2, 1.0, (("flash", 4),)),                                    # tel 1
        (60, 2, (136, 98), (58, 98), 2.2, 1.0, (("groundglow", 1.0), ("dust", 96, 3.0, 0))),          # burst 1
        (90, 2, (136, 98), (58, 98), 1.8, 0.6, (("dust", 96, 3.0, 1),)),
        (110, -3, (133, 84), (61, 84), 2.0, 0.8, ()),
        (170, -5, (134, 80), (60, 80), 2.4, 1.0, (("flash", 4),)),                                    # tel 2
        (60, 2, (136, 98), (58, 98), 2.2, 1.0, (("groundglow", 1.0), ("dust", 96, 3.0, 0))),          # burst 2
        (110, 1, (130, 90), (64, 90), 1.6, 0.3, (("dust", 96, 3.0, 1),)),
        (140, 0, (124, 80), (68, 78), 1.2, 0, ()),
        (160, 0, (119, 73), (71, 69), 1.0, 0, ()),
    ]
    fr = []
    for i, (ms, bob, hn, hf, halo, gl, fx) in enumerate(K):
        slam = i in (6, 7, 10, 11)
        fxs = tuple(fx) + ((("glyph", gl),) if gl else ())
        fr.append((ms, S.P_(bob=bob, hn=hn, hn_dir=100 if not slam else 90, hf=hf, hf_dir=80 if not slam else 90,
                            eln=(0.8, -0.3), elf=(-0.8, -0.3), halo=halo, crack=0.2 if halo > 1.9 else 0.0,
                            eyes=1.0 if 3 <= i <= 11 else 0.3,
                            wl=(WL0 + (18 if not slam and 1 <= i <= 10 else -10 if slam else 0), 1.2 if 1 <= i <= 10 else 1.0, 1.0),
                            wr=(WR0 - (18 if not slam and 1 <= i <= 10 else -10 if slam else 0), 1.2 if 1 <= i <= 10 else 1.0, 0.92),
                            wind=(0, 0, 0, 0, 0, 0, 4, 3, 0, 0, 4, 2, 0, 0)[i], fx=fxs)))
    return fr


def anim_crown():
    WL0, WR0 = S.WL0, S.WR0
    fr = []
    for i in range(14):
        fire = 5 <= i <= 11
        halo = (1.0, 1.4, 1.8, 2.2, 2.6, 2.6, 2.6, 2.6, 2.6, 2.6, 2.6, 2.6, 1.6, 1.0)[i]
        fx = ()
        if 2 <= i <= 3:
            fx = (("gat", "halo", 30, 0.4 + 0.3 * (i - 2), 14),)
        elif i == 4:
            fx = (("crownflare", 0.6),)
        elif fire:
            fx = (("crownflare", 1.0 if i % 2 else 0.8),)
        fr.append(((100, 110, 120, 140, 190, 90, 90, 90, 90, 90, 90, 90, 130, 150)[i],
                   S.P_(bob=(0, -1, -2, -3, -4, -4, -4, -4, -3, -3, -2, -2, -1, 0)[i],
                        head=(0, -1) if 1 <= i <= 11 else (0, 0), htilt=-4 if 2 <= i <= 11 else 0,
                        lean=(0, -2, -3, -4, -5, -4, -2, 0, 1, 2, 3, 3, 2, 0)[i],
                        hn=(126, 82) if 1 <= i <= 11 else (119, 73), hn_dir=100, hf=(66, 80) if 1 <= i <= 11 else (71, 69), hf_dir=80,
                        eln=(0.8, -0.3), elf=(-0.8, -0.3), halo=halo, crack=0.3 if fire else 0.0,
                        eyes=1.0 if 2 <= i <= 11 else 0.3,
                        wl=(WL0 + (16 if 1 <= i <= 11 else 0), 1.15 if 1 <= i <= 11 else 1.0, 1.0),
                        wr=(WR0 - (16 if 1 <= i <= 11 else 0), 1.15 if 1 <= i <= 11 else 1.0, 0.92),
                        wind=-1, fx=fx)))
    return fr


NEW_TAGS = [("lash", anim_lash, 11), ("combo", anim_combo, 16), ("petals", anim_petals, 12), ("grab", anim_grab, 11),
            ("grabhold", anim_grabhold, 10), ("orbs", anim_orbs, 11), ("beam", anim_beam, 16),
            ("spears", anim_spears, 11), ("vanish", anim_vanish, 7), ("cross", anim_cross, 12),
            ("rings", anim_rings, 14), ("crown", anim_crown, 14)]


def install(mod):
    global S
    S = mod
    mod.FX_FUNCS.update(NEW_FX)
    have = {t for t, _ in mod.TAGDEFS}
    for name, fn, n in NEW_TAGS:
        if name not in have:
            mod.TAGDEFS.append((name, fn))
        mod.COUNTS[name] = n
