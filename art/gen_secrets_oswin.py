#!/usr/bin/env python3
"""Oswin, the Ashen Pilgrim (agent X secret boss) -- a lean, weathered pilgrim-monk with a quarterstaff.

    python3 art/gen_secrets_oswin.py              full build: oswin + oswin_p2 (+ assets/oswin_meta.json)
    python3 art/gen_secrets_oswin.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_secrets_oswin.py --only combo,spin --preview

Frame 104x72, faces RIGHT, feet on the bottom row, anchor x = 44. ~48px tall under a wide straw pilgrim hat.
Phase 2 (oswin_p2): same frames, ash-wind wrapped around the staff and trailing off the robes, eyes pale.
Method: enemy_kit.py (normal-field shading, sel-out outlines, Rig) like gen_kalden.py.
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, n_plate, leg, arm, swept, thrust_lines, dirv)

W, H = 104, 72
K.setup(W, H)
import secrets_kit as S  # noqa: E402  (palette additions register on import)
from secrets_kit import tube, rag_hem, star, flat_arc, pole_px, bbox  # noqa: E402

FLOOR = H - 1
AX = 44
BUILD = "--preview" not in sys.argv
RGBA = K.RGBA

LAYERS = ["FXBack", "SashBack", "BackArm", "StaffBack", "BackLeg", "RobeBack", "Body", "FrontLeg", "Robe", "Head",
          "Hat", "Staff", "FrontArm", "Beard", "Wind", "FX"]
FXL = {"FXBack", "Wind", "FX"}

NEU = dict(P=(43.5, 50.5), C=(44.6, 39.6), Hd=(46.6, 30.6), hup=(0.26, -1), fb=(37.5, 71), ff=(51.0, 71), kb=None, kf=None,
           hf=(54.0, 45.0), wang=-94, hbu=None, hb=None, sl="Staff", u0=-26, u1=20, smear=None, smear2=None, flat=None,
           thrust=None, eye=1, wind=0.0, lift=0.0, dust=0, rot=0.0, piv=(46, 44), sit=False, dissolve=0.0, shake=0,
           glint=None, spark=None, tuck=False, kneel=False)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def M(*ds, **kw):
    d = dict(NEU)
    for x in ds:
        d.update(x)
    d.update(kw)
    return d


def up(p, dy, dx=0.0):
    q = dict(p)
    for k in ("P", "C", "Hd", "fb", "ff", "kb", "kf", "hf", "hb"):
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] - dy)
    return q


STANCE = dict(P=(43.0, 51.6), C=(43.8, 40.6), Hd=(45.8, 31.4), hup=(0.2, -1), fb=(35.0, 71), ff=(52.5, 71),
              hf=(55.0, 46.0), wang=8, hbu=-13)


# =========================================================================== drawing
def seated_legs(R, Ls, p):
    """Cross-legged on the ground: thighs forward, shins folded under (side view)."""
    Pp = p["P"]
    for nm, dx, bias in (("BackLeg", -1.5, -1), ("FrontLeg", 0.8, 0)):
        hip = (Pp[0] + dx, Pp[1] + 1.0)
        kn = (Pp[0] + dx + 10.5, FLOOR - 2.4)
        ft = (Pp[0] + dx + 0.5, FLOOR - 1.2)
        R.cap(Ls[nm], hip, kn, 2.6, 2.3, "A", bias)
        R.cap(Ls[nm], kn, ft, 2.1, 1.9, "P", bias)
        R.dome(Ls[nm], ft, 1.8, 1.4, "L", bias)
    return (Pp[0] + 11, FLOOR - 2), (Pp[0] + 9, FLOOR - 2)


def draw(p, fi, sw, phase):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, WI, FXB = FXLayer("FX"), FXLayer("Wind"), FXLayer("FXBack")
    Ls["FX"], Ls["Wind"], Ls["FXBack"] = FX, WI, FXB
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    shF, shB = F(2.2, -ln + 1.8), F(-2.8, -ln + 2.0)
    hB, hF = F(-2.0, 1.0), F(2.2, 1.0)
    info = {"hit": set(), "smear": set()}
    wind = p["wind"] + (1.6 if phase == 2 else 0.0)
    sx = sw * 1.0 - wind

    # ---------------- staff
    hf, wang = p["hf"], p["wang"]
    g0, a0 = R.T(hf), R.A(wang)
    ca, sa = dirv(a0)
    pix, staff, head, butt = pole_px(g0, a0, p["u0"], p["u1"], fi, ring_at=p["u1"] - 6, wood=("W0", "W1", "W2", "W3"))
    # bells + a faded ribbon tied under the head ring
    rb = (g0[0] + ca * (p["u1"] - 6.5), g0[1] + sa * (p["u1"] - 6.5))
    for k, off in enumerate((-1.6, 1.4)):
        q = ip((rb[0] - sa * off, rb[1] + ca * off))
        pix[q] = "G4" if k == 0 else "G3"
        staff.add(q)
    side = 1.8 if ca >= 0 else -1.8
    rb2 = (rb[0] - sa * side, rb[1] + ca * side)
    rib = bezier(rb2, add(rb2, (-0.6 - sx * 0.2, 1.6)), add(rb2, (-1.2 - sx * 0.5, 3.4)), add(rb2, (-1.8 - sx * 0.9, 5.0 - p["lift"] * 0.2)), n=6)
    for k, q in enumerate(rib[1:]):
        pix[ip(q)] = "C3" if k % 2 else "C2"
    pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
    staff = {q for q in staff if q[1] <= FLOOR}
    Ls[p["sl"]].fixed(pix)
    info["hit"] |= staff
    info["head"] = head
    info["butt"] = butt
    info["grip"] = g0
    # back hand: on the staff (hbu) or free (hb)
    if p["hbu"] is not None:
        hbk_frame = (g0[0] + ca * p["hbu"], g0[1] + sa * p["hbu"])
        # arms are drawn through the rig: express the frame point back in model coords
        hbk = inv(R, hbk_frame)
    else:
        hbk = p["hb"] or F(-4.2, -1.0)

    # ---------------- sash tails (behind) + robe back panel
    SB = Ls["SashBack"]
    knot = F(4.6, -0.6)
    for k, (dx, L0) in enumerate(((0.0, 9.5), (1.4, 7.5))):
        a_ = add(knot, (dx - 1.0, 0.8))
        tail = bezier(a_, add(a_, (-2.0 - sx * 0.3, 3.0)), add(a_, (-4.5 - sx * 0.8, 6.0 - p["lift"] * 0.2)),
                      add(a_, (-6.5 - sx * 1.4 - k, L0 - p["lift"] * 0.3)), n=8)
        tube(R, SB, tail, 1.3, 0.9, "J", bias=-1)

    # ---------------- legs
    if p["sit"]:
        kf, kb = seated_legs(R, Ls, p)
    elif p["kneel"]:
        kb = leg(R, Ls["BackLeg"], hB, p["fb"], 10.2, 10.2, 2.4, 1.9, "A", bias=-1, knee=p["kb"], boot="L", flen=3.4, heel=1.8, boot_h=2.4)
        kf = leg(R, Ls["FrontLeg"], hF, p["ff"], 10.2, 10.2, 2.4, 1.9, "A", bias=0, knee=p["kf"], boot="L", flen=3.4, heel=1.8, boot_h=2.4)
    else:
        kb = leg(R, Ls["BackLeg"], hB, p["fb"], 10.3, 10.3, 2.4, 1.9, "A", bias=-1, knee=p["kb"], boot="L", flen=3.4, heel=1.8, boot_h=2.4, pref=(1, -0.1))
        kf = leg(R, Ls["FrontLeg"], hF, p["ff"], 10.3, 10.3, 2.4, 1.9, "A", bias=0, knee=p["kf"], boot="L", flen=3.4, heel=1.8, boot_h=2.4, pref=(1, -0.1))
    # shin wraps (pale cloth bands) below the knee
    if not p["sit"]:
        for nm, kn, ft, bias in (("BackLeg", kb, p["fb"], -1), ("FrontLeg", kf, p["ff"], 0)):
            ank = (ft[0], ft[1] - 1.4)
            for k in range(4):
                t = 0.25 + k * 0.17
                q = lerp(kn, ank, t)
                R.dline(Ls[nm], add(q, (-1.8, 0.6)), add(q, (1.8, -0.4)), ("P", 3 + bias) if k % 2 else ("P", 2 + bias))

    # ---------------- robe skirt: back panel and front panel
    sway = sx
    hem_off = 2.6 if not p["sit"] else 0.0
    if p["sit"]:
        lap = [F(-6.0, -1.0), F(5.4, -1.0), (P[0] + 13.5, FLOOR - 4.0), (P[0] + 13.0, FLOOR - 0.5), (P[0] - 7.5, FLOOR - 0.5),
               (P[0] - 8.5, FLOOR - 4.0)]
        m = R.mask(lap)
        Ls["Robe"].paint(n_plate(m, 2.2, (0.0, -0.1), 1.0, fold=lambda x, y: (0.6 * math.sin(x * 0.7), 0)), "A", bias=0, ao=1)
    else:
        bk = add(kb, (-3.8 + sway * 0.4, hem_off))
        bk2 = add(kb, (3.0 + sway * 0.2, hem_off))
        back_panel = [F(-6.2, -1.2), F(1.0, -1.2)] + [add(q, (0, 0)) for q in rag_hem(bk[0], bk2[0], bk[1], fi, 61, 2.4, sway=sway * 0.3)][::-1] + \
            [add(bk, (-1.2 - p["lift"] * 0.15, -3.0))]
        m = R.mask(back_panel)
        Ls["RobeBack"].paint(n_plate(m, 2.0, (0.1, 0.0), 1.0, fold=lambda x, y: (0.55 * math.sin(x * 0.8 + y * 0.1), 0)), "A", bias=-1, ao=0)
        fk = add(kf, (3.6 + sway * 0.1, hem_off))
        fk2 = add(kf, (-3.0 + sway * 0.3, hem_off))
        front_panel = [F(-2.0, -1.2), F(5.8, -1.2), add(fk, (0.6, -3.0))] + rag_hem(fk2[0], fk[0], fk[1], fi, 62, 2.2, sway=sway * 0.2) + \
            [add(fk2, (-0.6, -2.0))]
        m2 = R.mask(front_panel)
        Ls["Robe"].paint(n_plate(m2, 2.0, (-0.2, 0.0), 1.0, fold=lambda x, y: (0.5 * math.sin(x * 0.9), 0)), "A", bias=0, ao=1)
        # a dark lining line where the panels part
        Ls["Robe"].decal([q for q in m2 if abs(q[0] - (lerp(F(-2.0, -1.2), fk2, 0.5)[0])) < 0.6], ("A", 0))
        info["robe"] = m | m2

    # ---------------- back arm (sleeve) + prayer beads
    arm(R, Ls["BackArm"], shB, hbk, 7.0, 7.0, 2.2, 1.8, "A", bias=-1, fist="E", fist_r=1.5, fore="P", pref=(-1, 0.6))
    if p["hbu"] is None and not p["sit"]:
        # prayer beads dangling from the free back hand
        hb_ = R.T(hbk)
        for k in range(6):
            q = (hb_[0] + math.sin(k * 0.9 + fi * 0.3) * 0.8, hb_[1] + 2 + k * 1.3)
            Ls["BackArm"].fixed({ip(q): "L3" if k != 3 else "G4"})

    # ---------------- torso: pale outer robe, dark inner wrap, sash, beads
    Bd = Ls["Body"]
    torso = [F(-4.8, -0.6), F(-5.8, -ln + 3.8), F(-4.2, -ln - 0.4), F(2.0, -ln - 1.3), F(5.0, -ln + 1.0),
             F(5.4, -ln + 6.4), F(4.4, -0.6)]
    tm = R.plate(Bd, torso, "A", bevel=2.8, tilt=(-0.3, -0.1), strength=1.3)
    info["torso"] = tm
    vneck = [F(0.2, -ln - 1.4), F(3.6, -ln - 0.6), F(2.6, -ln + 5.4)]
    R.plate(Bd, vneck, "K", bevel=1.0, bias=0)
    R.decal(Bd, [F(1.8, -ln + 0.2), F(2.0, -ln + 1.2)], ("E", 3))                    # a sliver of chest
    R.dline(Bd, F(-0.6, -ln - 1.2), F(3.0, -ln + 5.6), ("A", 1))                      # robe overlap fold
    R.dline(Bd, F(-3.8, -ln + 2.0), F(-3.4, -3.0), ("A", 1))                          # back fold
    # sash band + knot
    band = [F(-6.0, -2.4), F(5.8, -2.4), F(6.0, 1.0), F(-6.2, 1.0)]
    R.plate(Bd, band, "J", bevel=1.0, tilt=(0.0, -0.2))
    R.dline(Bd, F(-6.0, -0.6), F(5.8, -0.6), ("J", 2))
    R.dome(Bd, knot, 1.8, 1.6, "J", bias=0)
    # beads around the neck: a loop of dark beads, one gold
    for k in range(9):
        t = k / 8
        q = add(lerp(F(-2.6, -ln + 0.4), F(4.0, -ln + 1.0), t), (0, math.sin(t * math.pi) * 3.8))
        R.decal(Bd, [q], ("G", 4) if k == 6 else ("L", 3 if k % 2 else 2))

    # ---------------- head: old face under a wide straw hat, long grey beard
    G = basis(Hd, p["hup"])
    Hl = Ls["Head"]
    face = [G(-3.2, 3.0), G(-3.6, -1.6), G(-1.6, -3.4), G(2.4, -3.2), G(4.2, -0.6), G(4.6, 1.6), G(3.2, 3.8), G(-0.6, 4.2)]
    hm = R.plate(Hl, face, "E", bevel=1.8, tilt=(-0.2, -0.1), strength=1.2)
    info["head"] = hm
    R.decal(Hl, [G(4.8, 0.6), G(4.4, 1.0)], ("E", 3))                                  # nose
    R.dline(Hl, G(1.2, -1.2), G(3.6, -1.0), ("E", 0))                                  # brow shadow
    R.decal(Hl, [G(-1.8, 0.6), G(-2.2, 1.4)], ("E", 1))                                # ear shadow
    # eye glint
    e = R.pt(G(3.0, -0.4))
    if p["eye"]:
        FX.put([e], ("Z4" if phase == 2 else "Y2") if p["eye"] == 2 else ("Z3" if phase == 2 else "G4"))
        if p["eye"] == 2:
            FX.put([(e[0] + 1, e[1]), (e[0] - 1, e[1])], "Z2" if phase == 2 else "G3")
    # beard: long, wispy, swaying back with motion
    Bb = Ls["Beard"]
    ch = G(3.2, 3.4)
    bl = 12.0 if not p["sit"] else 10.0
    btip = add(ch, (-1.4 - sx * 0.5 - wind * 0.4, bl))
    beard = [add(ch, (-4.0, -1.2)), add(ch, (2.2, -0.8)), add(ch, (2.4, 3.4)), add(ch, (0.8, 6.4)), add(btip, (0.4, -0.8)), btip,
             add(btip, (-1.0, -2.4)), add(ch, (-2.0, 5.6)), add(ch, (-3.6, 2.6))]
    bm = R.mask(beard)
    Bb.paint(n_plate(bm, 1.6, (0.1, 0.1), 1.0, fold=lambda x, y: (0.8 * math.sin(x * 1.6), 0)), "B", bias=0, ao=1)
    Bb.decal([q for q in bm if hash01(q[0], q[1], 5) < 0.18], ("B", 2))
    R.dline(Bb, add(ch, (-1.0, 0.4)), add(btip, (0.2, -1.0)), ("B", 3))
    R.dline(Bb, add(ch, (-2.2, -0.6)), add(ch, (1.4, -0.6)), ("B", 5))                   # moustache line lit

    # ---------------- hat: a wide conical straw pilgrim hat, frayed brim, chin cord
    Ht = Ls["Hat"]
    bc = G(0.2, -3.2)
    brim = []
    for k in range(24):
        a = k / 24 * 2 * math.pi
        rr = 11.2 + (0.6 if hash01(k, 3, 7) > 0.7 else 0)
        brim.append(add(bc, (math.cos(a) * rr, math.sin(a) * 2.0 + (1.2 if math.cos(a) < -0.3 else 0.4) * abs(math.cos(a)))))
    brm = R.mask(brim)
    Ht.paint(n_plate(brm, 1.4, (-0.1, -0.5), 1.1), "H", bias=0, ao=0)
    crown = [add(bc, (-8.4, 0.4)), add(bc, (-3.4, -4.6)), add(bc, (0.4, -7.2)), add(bc, (3.6, -4.8)), add(bc, (8.2, 0.2))]
    crm = R.mask(crown)
    Ht.paint(n_plate(crm, 3.0, (-0.45, -0.25), 1.4), "H", bias=0, ao=1)
    # straw weave: radial strands on the crown, rings on the brim
    for k in range(6):
        s0 = add(bc, (0.4, -7.0))
        s1 = add(bc, (-7.6 + k * 3.0, 0.2))
        Ht.decal([q for q in line(R.T(lerp(s0, s1, 0.3)), R.T(s1)) if q in crm], ("H", 2))
    Ht.decal([q for q in brm if (q[0] + q[1]) % 4 == 0 and hash01(q[0], q[1], 9) < 0.5], ("H", 2))
    for k in range(7):                                                            # frayed straw ends
        a = (k / 7) * 2 * math.pi + 0.3
        q = add(bc, (math.cos(a) * 12.0, math.sin(a) * 2.2 + 0.8))
        Ht.fixed({R.pt(q): "H2" if k % 2 else "H3"})
    R.dline(Ht, add(bc, (-8.0, 0.2)), add(bc, (8.0, 0.0)), ("H", 1))              # band where crown meets brim
    info["hat"] = brm | crm
    # shadow under the brim across the face
    Hl.decal([q for q in hm if q[1] <= R.pt(G(0, -1.4))[1]], ("E", 1))
    # chin cord
    Hl.decal(line(R.T(G(-2.6, -2.4)), R.T(G(1.8, 3.4))), ("L", 2))

    # ---------------- front arm (sleeve, wrapped forearm, hand on the staff)
    Fa = Ls["FrontArm"]
    hfr = hf
    el = arm(R, Fa, shF, hfr, 7.0, 7.2, 2.6, 1.9, "A", bias=0, fist="E", fist_r=1.7, fore="P", pref=(-1, 0.7))
    cuff = lerp(el, hfr, 0.3)
    R.dome(Fa, cuff, 2.6, 2.2, "A", bias=0)                                       # wide sleeve mouth
    for k in range(3):
        R.dline(Fa, add(lerp(el, hfr, 0.5 + k * 0.14), (-1.2, 0.6)), add(lerp(el, hfr, 0.5 + k * 0.14), (1.2, -0.6)), ("P", 2))
    R.dome(Fa, add(shF, (0.2, -0.4)), 2.8, 2.4, "A", bias=0)                      # shoulder

    # ---------------- phase 2: ash-wind wrapped round the staff, streaming off the robe
    if phase == 2:
        L_ = p["u1"] - p["u0"]
        for k in range(int(L_ * 1.5)):
            u = p["u0"] + k / 1.5
            ph = u * 0.55 + fi * 1.7
            off = math.sin(ph) * 3.0
            q = ip((g0[0] + ca * u - sa * off, g0[1] + sa * u + ca * off))
            if q[1] <= FLOOR and q not in staff:
                col = "Z3" if math.cos(ph) > 0.3 else "Z2" if math.cos(ph) > -0.4 else "Z1"
                (WI if math.cos(ph) > -0.2 else FXB).put([q], col)
        for k in range(10):
            t = (fi * 0.23 + hash01(k, 3, 11)) % 1.0
            base = lerp(butt, head, hash01(k, 4, 11))
            q = ip((base[0] - 6 - t * 16 - sx * 2, base[1] - t * 6 + math.sin(k + fi) * 2))
            if K.inb(*q) and q[1] <= FLOOR:
                WI.put([q], "Z2" if t < 0.5 else "Z1")
        for k in range(6):
            t = (fi * 0.31 + hash01(k, 5, 12)) % 1.0
            q = ip((P[0] - 8 - t * 14, P[1] + 4 + hash01(k, 6, 12) * 10 - t * 5))
            if K.inb(*q) and q[1] <= FLOOR:
                WI.put([q], "Z1" if t > 0.4 else "Z2")

    # ---------------- FX: smears, thrusts, spins, glints
    pal = "staff" if phase == 1 else "wind"
    for sm in (p["smear"], p["smear2"]):
        if not sm:
            continue
        g_s = R.T(sm["g0"]) if not sm.get("frame") else sm["g0"]
        a_s = R.A(sm["a0"])
        g_e = g0 if not sm.get("g1") else R.T(sm["g1"])
        a_e = a0 if sm.get("a1") is None else R.A(sm["a1"])
        u1 = sm.get("u1", p["u1"])
        hot = swept(FX, g_s, a_s, g_e, a_e, sm.get("u0", u1 - 12), u1 + 0.5, hw=1.2, mid=sm.get("mid"), start=sm.get("start", 0.0),
                    pal=pal, exclude=staff, taper=sm.get("taper", 0.7), clip_y=FLOOR)
        info["hit"] |= hot
        info["smear"] |= hot
    if p["flat"]:
        hot = flat_arc(FX, p["flat"], pal, exclude=staff, back=FXB, floor=FLOOR)
        info["hit"] |= hot
        info["smear"] |= hot
    if p["thrust"]:
        th = p["thrust"]
        pts = thrust_lines(FX, g0, a0, th.get("u0", -20), th.get("u1", p["u1"]), th.get("offs", (-2, 1, 3)),
                           pal="steel" if phase == 1 else "wind", flash=th.get("flash"))
        info["hit"] |= {q for q in pts if q[0] > AX}
    if p["dust"]:
        for fx_ in ((p["fb"][0], -1), (p["ff"][0], 1)):
            for k in range(6):
                x = int(fx_[0] + fx_[1] * (1 + k * 1.3) + (hash01(k, fi, 9) - 0.5) * 2)
                y = FLOOR - int(hash01(k, fi, 10) * (2 + k * 0.5) * (1 if p["dust"] == 1 else 0.6))
                FX.put([(x, y)], ("A3", "A2", "P3")[k % 3] if p["dust"] == 1 else "A2")
    if p["glint"]:
        star(FX, p["glint"], "Y3" if phase == 1 else "Z4", "G4" if phase == 1 else "Z2")
    if p["spark"]:
        star(FX, p["spark"], "Y3", "Y1")
    return Ls, info


def inv(R, q):
    """Inverse of Rig.T for sx = sy = 1 (map a frame point back into model coords)."""
    x, y = q[0] - R.off[0] - R.piv[0], q[1] - R.off[1] - R.piv[1]
    c, s = R.c, R.s
    return (R.piv[0] + x * c + y * s, R.piv[1] - x * s + y * c)


# =========================================================================== animations
def a_idle():
    fr = []
    for i in range(6):
        b = (0, 0.4, 0.8, 1.0, 0.8, 0.4)[i]
        fr.append((190, P_(P=(43.5, 50.5 + b * 0.3), C=(44.6, 39.6 + b * 0.8), Hd=(46.6, 30.6 + b * 0.9),
                           hf=(54.0, 45.0 + b * 0.2), hb=(39.5, 53.0 + b * 0.5), wind=0.4 * math.sin(i * 1.05))))
    return fr


SIT = dict(P=(44.0, 64.5), C=(45.4, 53.8), Hd=(47.8, 45.0), hup=(0.36, -1), sit=True, hf=(52.0, 63.0), wang=0, u0=-28, u1=18,
           hb=(40.0, 61.5), sl="Staff")


def a_sit():
    return [(600, M(SIT)), (600, M(dict(SIT, C=(45.4, 54.2), Hd=(47.9, 45.5))))]


def a_rise():
    return [
        (160, M(dict(SIT, hf=(53.0, 60.0), wang=-60, u0=-20, u1=24))),
        (180, P_(P=(44.0, 62.5), C=(46.6, 52.4), Hd=(49.6, 44.0), hup=(0.5, -1), sit=True, hf=(55.0, 52.0), wang=-92, hb=(40.0, 58.0))),
        (180, P_(P=(43.0, 58.5), C=(45.6, 48.6), Hd=(48.6, 39.8), hup=(0.46, -1), kneel=True, kb=(38.5, 67.0), fb=(30.0, 71), ff=(52.0, 71),
                 kf=(50.0, 57.5), hf=(55.0, 48.0), wang=-92, hb=(42.0, 54.0))),
        (160, P_(P=(43.5, 53.5), C=(45.0, 42.6), Hd=(47.4, 33.6), hup=(0.34, -1), fb=(38.0, 71), ff=(51.0, 71), hf=(54.5, 46.5), wang=-93,
                 hb=(39.0, 51.0))),
        (220, P_(hb=(39.5, 53.0))),
    ]


def a_twirl():
    base = dict(STANCE, hbu=None, hb=(38.0, 50.0), u0=-23, u1=23)
    hf = (54.0, 42.0)
    fr = []
    angs = [0, 70, 150, 235, 320]
    for k, a in enumerate(angs):
        sm = None
        if k > 0:
            sm = dict(g0=hf, a0=angs[k - 1], u0=19, u1=23, taper=0.8)
        f = M(base, hf=hf, wang=a, smear=sm, smear2=dict(g0=hf, a0=angs[k - 1] + 180, a1=a + 180, u0=19, u1=23, taper=0.8) if k > 0 else None)
        fr.append((70 if k else 120, f))
    fr.append((260, M(STANCE, eye=2)))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        ff = (44.0 + 7.0 * c, 71 - max(0.0, -s) * 3.2)
        fb = (43.0 - 7.0 * c, 71 - max(0.0, s) * 3.2)
        bob = 1.3 * abs(c)
        fr.append((115, M(dict(STANCE, P=(43.4, 51.0 + bob), C=(44.6, 40.0 + bob), Hd=(46.6, 30.8 + bob), fb=fb, ff=ff,
                                  hf=(55.0 + 0.6 * c, 46.0 + bob), wang=8 + 2 * s))))
    return fr


def a_combo():
    lunge = dict(P=(47.0, 53.0), C=(51.0, 42.8), Hd=(54.4, 33.8), hup=(0.46, -1), fb=(35.0, 71), ff=(60.0, 71))
    smash = dict(P=(48.0, 54.0), C=(52.2, 44.0), Hd=(55.6, 35.4), hup=(0.5, -1), fb=(36.0, 71), ff=(62.0, 71))
    rise = dict(P=(49.0, 52.6), C=(52.6, 41.8), Hd=(55.2, 32.4), hup=(0.36, -1), fb=(37.0, 71), ff=(62.0, 71))
    return [
        (100, P_(P=(42.0, 51.4), C=(42.4, 40.4), Hd=(44.2, 31.2), hup=(0.12, -1), fb=(34.0, 71), ff=(50.5, 71), hf=(47.0, 45.5), wang=2, hbu=-12)),
        (260, P_(P=(41.0, 52.2), C=(40.4, 41.4), Hd=(41.8, 32.2), hup=(0.02, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(44.0, 45.5), wang=1, hbu=-12,
                 eye=2, glint=(64.0, 45.4))),
        (60, M(lunge, hf=(66.0, 44.0), wang=0, hbu=-13, wind=4, thrust=dict(u0=-18, u1=20, offs=(-2, 1, 3)))),
        (90, M(lunge, hf=(60.0, 39.0), wang=-58, hbu=-12, wind=2)),
        (160, P_(P=(45.0, 52.4), C=(45.4, 41.4), Hd=(47.0, 32.2), hup=(0.1, -1), fb=(35.0, 71), ff=(57.0, 71), hf=(49.0, 29.0), wang=-150,
                 hbu=-11, eye=2)),
        (60, M(smash, hf=(62.0, 46.0), wang=32, hbu=-12, wind=4, smear=dict(g0=(49.0, 29.0), a0=-150, mid=(60.0, 20.0), start=0.1))),
        (80, M(smash, hf=(60.0, 51.0), wang=62, hbu=-12, wind=3, smear=dict(g0=(62.0, 46.0), a0=32, taper=0.4, u0=12))),
        (170, P_(P=(46.0, 54.0), C=(45.6, 43.4), Hd=(47.0, 34.2), hup=(0.05, -1), fb=(35.0, 71), ff=(58.0, 71), hf=(48.0, 58.0), wang=165,
                 hbu=-11, eye=2)),
        (60, M(rise, hf=(62.0, 42.0), wang=-44, hbu=-12, wind=4, smear=dict(g0=(48.0, 58.0), a0=165, mid=(62.0, 68.0), start=0.1))),
        (90, M(rise, hf=(58.0, 33.0), wang=-82, hbu=-12, wind=3, smear=dict(g0=(62.0, 42.0), a0=-44, taper=0.3, u0=12, start=0.3))),
        (200, M(STANCE)),
    ]


def a_spin():
    crouch = dict(P=(43.0, 54.0), C=(42.6, 43.4), Hd=(44.2, 34.4), hup=(0.08, -1), fb=(33.0, 71), ff=(53.0, 71))
    spin = dict(P=(44.0, 53.4), C=(44.4, 42.6), Hd=(46.0, 33.4), hup=(0.14, -1), fb=(34.0, 71), ff=(54.0, 71))
    c = (44.0, 49.0)
    return [
        (140, M(crouch, hf=(49.0, 48.0), wang=178, hbu=-9)),
        (280, M(dict(crouch, C=(41.6, 43.8), Hd=(43.0, 34.8)), hf=(42.0, 48.5), wang=178, hbu=-9, eye=2, glint=(22.0, 48.0))),
        (60, M(spin, hf=(54.0, 47.0), wang=4, hbu=-11, wind=4, flat=dict(c=c, rx=34.0, ry=6.0, th0=-200, th1=12, w=5.0))),
        (60, M(spin, hf=(36.0, 47.5), wang=178, hbu=-11, wind=4, flat=dict(c=c, rx=34.0, ry=6.0, th0=12, th1=190, w=5.0))),
        (60, M(spin, hf=(54.0, 47.0), wang=2, hbu=-11, wind=4, flat=dict(c=c, rx=34.0, ry=6.0, th0=-170, th1=12, w=5.0))),
        (80, M(spin, hf=(38.0, 48.0), wang=176, hbu=-11, wind=3, flat=dict(c=c, rx=34.0, ry=6.0, th0=12, th1=190, w=3.5, fade=0.5))),
        (120, M(crouch, hf=(50.0, 47.0), wang=6, hbu=-12)),
        (180, P_(P=(43.2, 52.4), C=(43.8, 41.4), Hd=(45.6, 32.2), fb=(34.5, 71), ff=(52.5, 71), hf=(54.0, 46.0), wang=8, hbu=-13)),
        (200, M(STANCE)),
    ]


def a_vault():
    TUCK = dict(P=(45.0, 47.0), C=(46.4, 37.4), Hd=(48.6, 28.8), hup=(0.3, -1), fb=(41.0, 59.0), ff=(50.0, 57.0),
                kb=(37.0, 52.0), kf=(52.5, 49.0), hf=(51.0, 40.0), wang=-14, hbu=-11, piv=(46.0, 44.0))
    land = dict(P=(44.0, 57.0), C=(46.0, 47.0), Hd=(48.4, 38.0), hup=(0.3, -1), fb=(33.0, 71), ff=(53.0, 71))
    strike = dict(P=(47.0, 55.0), C=(50.6, 45.0), Hd=(53.4, 36.0), hup=(0.42, -1), fb=(35.0, 71), ff=(60.0, 71))
    return [
        (120, P_(P=(44.0, 54.0), C=(46.2, 43.8), Hd=(49.2, 35.0), hup=(0.36, -1), fb=(35.0, 71), ff=(54.0, 71), hf=(56.0, 50.0), wang=40, hbu=-12)),
        (220, P_(P=(44.0, 57.0), C=(46.4, 47.0), Hd=(49.6, 38.2), hup=(0.4, -1), fb=(34.0, 71), ff=(53.0, 71), hf=(58.0, 52.0), wang=56, hbu=-12,
                 eye=2, glint=(69.5, 67.0), dust=2)),
        (80, P_(P=(46.0, 48.0), C=(48.0, 37.6), Hd=(50.0, 28.6), hup=(0.24, -1), fb=(40.0, 66.0), ff=(47.0, 63.0), hf=(56.0, 40.0), wang=72,
                hbu=-12, dust=1, lift=6)),
        (70, M(TUCK, rot=70, lift=8)),
        (70, M(TUCK, rot=160, lift=8)),
        (70, M(TUCK, rot=250, lift=6)),
        (70, M(TUCK, rot=335, lift=2)),
        (70, M(land, hf=(40.0, 56.0), wang=172, hbu=-10, dust=1)),
        (60, M(strike, hf=(62.0, 55.0), wang=10, hbu=-12, wind=4, flat=dict(c=(48.0, 61.0), rx=36.0, ry=5.0, th0=-200, th1=12, w=5.0))),
        (80, M(strike, hf=(60.0, 50.0), wang=-24, hbu=-12, wind=3, flat=dict(c=(48.0, 61.0), rx=36.0, ry=5.0, th0=-60, th1=40, w=3.5, fade=0.5))),
        (220, M(STANCE)),
    ]


def a_counter():
    c = dict(P=(42.0, 54.0), C=(42.8, 43.4), Hd=(45.0, 34.6), hup=(0.2, -1), fb=(31.0, 71), ff=(54.0, 71), hf=(56.0, 42.0), wang=-4, hbu=-16, eye=2)
    return [(280, M(c)), (280, M(dict(c, P=(42.0, 54.3), C=(42.8, 43.7), Hd=(45.0, 34.9)), glint=(48.0, 42.0)))]


def a_riposte():
    lunge = dict(P=(47.6, 53.6), C=(52.0, 43.6), Hd=(55.6, 34.8), hup=(0.5, -1), fb=(34.0, 71), ff=(62.0, 71))
    return [
        (60, P_(P=(43.0, 52.0), C=(43.6, 41.0), Hd=(45.6, 31.8), hup=(0.14, -1), fb=(33.0, 71), ff=(53.0, 71), hf=(54.0, 38.0), wang=-62, hbu=-12,
                spark=(60.0, 28.0), eye=2)),
        (90, P_(P=(41.6, 52.4), C=(41.2, 41.6), Hd=(42.8, 32.4), fb=(33.0, 71), ff=(51.0, 71), hf=(45.0, 45.0), wang=0, hbu=-12, eye=2)),
        (50, M(lunge, hf=(69.0, 43.0), wang=-2, hbu=-13, wind=5, thrust=dict(u0=-22, u1=20, offs=(-3, -1, 1, 3), flash=21))),
        (60, M(lunge, hf=(64.0, 42.0), wang=38, hbu=-12, wind=3, smear=dict(g0=(69.0, 43.0), a0=-40, u0=10, taper=0.4))),
        (90, M(lunge, hf=(60.0, 46.0), wang=50, hbu=-12)),
        (150, P_(P=(45.0, 52.4), C=(46.6, 41.6), Hd=(48.6, 32.4), hup=(0.28, -1), fb=(35.0, 71), ff=(56.0, 71), hf=(56.0, 46.0), wang=20, hbu=-13)),
        (200, M(STANCE)),
    ]


def a_dash():
    low = dict(P=(42.0, 55.0), C=(43.6, 45.0), Hd=(46.2, 36.2), hup=(0.34, -1), fb=(32.0, 71), ff=(52.0, 71))
    dash = dict(P=(48.0, 56.0), C=(54.0, 48.0), Hd=(58.6, 40.6), hup=(0.7, -1), fb=(30.0, 70.0), ff=(62.0, 71))
    return [
        (140, M(low, hf=(41.0, 50.0), wang=178, hbu=-10)),
        (240, M(dict(low, P=(41.0, 57.0), C=(42.6, 47.4), Hd=(45.4, 38.6)), hf=(39.0, 52.0), wang=176, hbu=-10, eye=2, glint=(58.0, 38.0))),
        (70, P_(P=(46.0, 55.0), C=(51.0, 46.0), Hd=(55.0, 37.8), hup=(0.6, -1), fb=(34.0, 71), ff=(58.0, 70.0), hf=(56.0, 49.0), wang=6, hbu=-12, wind=4)),
        (60, M(dash, hf=(65.0, 48.0), wang=3, hbu=-12, wind=7, thrust=dict(u0=-40, u1=-4, offs=(-6, -3, 3, 6)))),
        (60, M(dash, hf=(66.0, 48.5), wang=4, hbu=-12, wind=7, thrust=dict(u0=-44, u1=-8, offs=(-5, -1, 4)))),
        (60, M(dash, hf=(65.0, 48.0), wang=2, hbu=-12, wind=6, thrust=dict(u0=-40, u1=-6, offs=(-4, 2, 5)))),
        (140, P_(P=(45.0, 55.0), C=(47.2, 45.0), Hd=(49.8, 36.2), hup=(0.36, -1), fb=(36.0, 71), ff=(56.0, 71), hf=(58.0, 44.0), wang=-30, hbu=-12,
                 dust=1)),
        (200, M(STANCE)),
    ]


def a_backstep():
    return [
        (90, P_(P=(43.0, 53.4), C=(44.6, 43.0), Hd=(46.6, 34.0), hup=(0.26, -1), fb=(35.0, 71), ff=(50.0, 71), hf=(54.0, 47.0), wang=6, hbu=-12)),
        (80, up(P_(P=(41.4, 51.0), C=(40.0, 40.4), Hd=(40.4, 31.4), hup=(-0.16, -1), fb=(34.0, 69.0), ff=(51.0, 71.0), hf=(51.0, 43.0), wang=-8, hbu=-12,
                   dust=1, wind=-2, lift=3), 2)),
        (110, up(P_(P=(40.0, 50.0), C=(39.0, 39.4), Hd=(39.6, 30.4), hup=(-0.1, -1), fb=(34.0, 66.0), ff=(47.0, 65.0), hf=(50.0, 42.0), wang=-10,
                    hbu=-12, wind=-4, lift=7), 6)),
        (100, P_(P=(41.0, 54.0), C=(42.0, 43.4), Hd=(44.0, 34.4), hup=(0.1, -1), fb=(33.0, 71), ff=(49.0, 71), hf=(53.0, 47.0), wang=4, hbu=-12, dust=1)),
        (160, M(STANCE)),
    ]


def a_stagger():
    return [
        (90, P_(P=(41.6, 52.0), C=(39.6, 41.6), Hd=(38.8, 32.4), hup=(-0.4, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(48.0, 38.0), wang=-120, hbu=-10, eye=0)),
        (130, P_(P=(42.0, 56.0), C=(43.0, 45.8), Hd=(45.0, 36.6), hup=(0.3, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(51.0, 56.0), wang=78, hbu=-10, eye=0)),
        (260, P_(P=(42.4, 57.0), C=(44.4, 47.0), Hd=(47.4, 38.4), hup=(0.52, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(52.0, 57.0), wang=82, hbu=-10, eye=0)),
        (260, P_(P=(42.2, 57.4), C=(44.0, 47.4), Hd=(46.8, 38.8), hup=(0.5, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(51.6, 57.4), wang=84, hbu=-10, eye=0)),
    ]


def a_death():
    KN = dict(P=(42.0, 60.0), C=(44.4, 49.6), Hd=(47.4, 41.0), hup=(0.55, -1), kneel=True, kb=(38.5, 69.0), fb=(29.5, 71), ff=(51.0, 71),
              kf=(49.0, 59.5), hf=(54.0, 50.0), wang=-92, hb=(46.0, 53.0), eye=0)
    fr = [
        (100, P_(P=(41.6, 52.0), C=(39.6, 41.6), Hd=(38.8, 32.4), hup=(-0.45, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(48.0, 40.0), wang=-110, hbu=-10, eye=2)),
        (180, P_(P=(42.0, 56.0), C=(43.6, 45.6), Hd=(46.0, 36.4), hup=(0.3, -1), fb=(33.0, 71), ff=(50.0, 71), hf=(53.0, 50.0), wang=-95, hb=(43.0, 50.0))),
        (220, M(KN)),
        (500, M(dict(KN, Hd=(47.8, 41.6), hup=(0.62, -1)))),
        (400, M(dict(KN, C=(44.6, 50.0), Hd=(48.2, 42.2), hup=(0.7, -1)))),
    ]
    for d, ms in ((0.16, 150), (0.34, 150), (0.52, 150), (0.74, 170), (0.97, 900)):
        fr.append((ms, M(dict(KN, C=(44.6, 50.0), Hd=(48.2, 42.2), hup=(0.7, -1)), dissolve=d)))
    return fr


TAGDEFS = [("idle", a_idle), ("sit", a_sit), ("rise", a_rise), ("twirl", a_twirl), ("walk", a_walk), ("combo", a_combo), ("spin", a_spin),
           ("vault", a_vault), ("counter", a_counter), ("riposte", a_riposte), ("dash", a_dash), ("backstep", a_backstep),
           ("stagger", a_stagger), ("death", a_death)]
LOOPS = ("idle", "walk", "counter", "sit")


# =========================================================================== render
def render_frame(p, fi, sw, phase):
    Ls, info = draw(p, fi, sw, phase)
    imgs = {}
    for n in LAYERS:
        v = Ls.get(n)
        if v is None:
            continue
        imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
    if p["dissolve"] > 0:
        pal = ("G4", "G3", "P4", "P3", "A2") if phase == 1 else ("Z4", "Z3", "Z2", "Z1", "Z0")
        imgs = K.ember_dissolve(imgs, p["dissolve"], [n for n in LAYERS if n not in ("FX", "Wind", "FXBack")], fx_name="FX", seed=5, rise=24, pal=pal)
    return imgs, info


def render_all(only=None):
    out = {1: [], 2: []}
    infos, tags = {}, []
    n = 0
    for tag, fn in TAGDEFS:
        fr = fn()
        if only and tag not in only:
            continue
        drv = [p["C"][0] for _, p in fr]
        sway = K.spring(drv, loop=tag in LOOPS, extra=[p.get("wind", 0.0) for _, p in fr])
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            for ph in (1, 2):
                imgs, info = render_frame(p, a + k, sway[k], ph)
                out[ph].append((ms, imgs))
                if ph == 1:
                    infos[tag].append(info)
            n += 1
        tags.append((tag, a, n - 1))
        print("rendered", tag, len(fr))
    return out, infos, tags


def build_meta(infos):
    idle = infos["idle"][0]
    tb = bbox(idle["torso"] | idle["head"] | idle["hat"])
    hurt = [tb[0] + 2, tb[1] + 2, tb[2] - 4, H - tb[1] - 2]
    at = S.attack
    meta = {
        "native": 1, "frame": [W, H], "anchor": [AX, H], "hurtbox": hurt,
        "attacks": {
            "combo": {"windows": [at(infos, "combo", 2, 2, AX + 2), at(infos, "combo", 5, 6, AX + 2), at(infos, "combo", 8, 9, AX + 2)]},
            "spin": at(infos, "spin", 2, 5, 0, both=True),
            "vault": at(infos, "vault", 8, 9, AX - 6),
            "riposte": {"windows": [at(infos, "riposte", 2, 2, AX + 2), at(infos, "riposte", 3, 3, AX + 2)]},
            "dash": at(infos, "dash", 3, 5, AX - 10),
        },
        "telegraph": {
            "combo": {"frame": 1, "at": [64, 45]},
            "spin": {"frame": 1, "at": [22, 48]},
            "vault": {"frame": 1, "at": [69, 66]},
            "dash": {"frame": 1, "at": [58, 38]},
        },
        "notes": "Oswin faces right, anchor = feet. combo = jab, overhead smash, rising sweep (3 windows). spin = 360 deg sweep, hits "
                 "BOTH sides (engine throws whirlwinds on frame 4 in phase 2). vault: frames 2-6 airborne (drawn in place, flips over "
                 "the player; engine moves him), landing back-sweep 8-9. counter = parry stance loop; riposte = its answer. "
                 "dash = phase-2 dash-through (engine moves him on 3-5). sit/rise/twirl = cutscene. oswin_p2 shares this meta.",
    }
    return meta


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    out, infos, tags = render_all(only)
    pv = S.PREV
    os.makedirs(pv, exist_ok=True)
    flats = {ph: [K.flatten(imgs, LAYERS) for _, imgs in out[ph]] for ph in (1, 2)}
    sfx = "_wip" if only else ""
    S.preview_rows(tags, flats[1], os.path.join(pv, f"oswin{sfx}.png"))
    S.preview_rows(tags, flats[2], os.path.join(pv, f"oswin_p2{sfx}.png"))
    S.closeup(flats[1] + flats[2], [0, len(flats[1])], os.path.join(pv, f"oswin_closeup{sfx}.png"))
    if only:
        return
    meta = build_meta(infos)
    S.hitbox_preview(tags, flats[1], meta, os.path.join(pv, "oswin_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "oswin_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        for w_ in d.get("windows", [d]):
            print("attack", t, w_["active"], w_["hit"])
    print("hurtbox", meta["hurtbox"])
    if BUILD:
        asebuild.build("oswin", W, H, LAYERS, [{"ms": ms, "cels": imgs} for ms, imgs in out[1]], tags)
        asebuild.build("oswin_p2", W, H, LAYERS, [{"ms": ms, "cels": imgs} for ms, imgs in out[2]], tags)


if __name__ == "__main__":
    main()
