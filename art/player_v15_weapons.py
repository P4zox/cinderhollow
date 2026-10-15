"""v15: the five new weapon types' overlay weapons (wpn_<id>), installed into gen_player by install(G).

  type     prefix  weapon id            name                    style
  saxe     sx_     gravegrinder         Gravegrinder            switch axe, axe mode: folded sword blade along the haft,
                                                                a toothed crescent axe head, an ember phial
  bow      bw_     ashstring            Ashstring Recurve       recurve bow held at the grip, an arrow nocked along the
                                                                swing line (the "blade"), two more fanned in the bow hand
  fist     ft_     penitent_knuckles    Penitent's Knuckles     spiked iron knuckles over the fist, wraps trailing back
  scythe   sc_     requiem_scythe       Requiem                 long black haft, a pale bone-silver blade with a violet
                                                                soul-edge (shares the v9 scythe haft path)
  bell     wb_     dirge_bell           Dirgebell               a black-iron war-bell on a chained haft, mouth to the foe
                                                                (maul style: rests its head on the floor when planted)

Shapes are authored in blade space exactly like gen_player's shp_* (u = along the weapon from the grip / hand,
v = across, s = which side faces the light, L = the pose's length, tip at u = L + 1.5). Colours are RGB tuples.

A moveset agent may restyle its own weapon from its art/player_v15_<type>.py register(G) (it runs after install):
    G.WPN["<id>"] = (shape, nominal_length, reach_behind_hand, extent_across, "blade" | "maul")
    G.SMEAR["<id>"] = (rim, body, tail)          # swing smear tones
Never edit another type's entry here.
"""
import math

V15_TYPES = ("saxe", "bow", "fist", "scythe", "bell")
V15_WPN = {"saxe": "gravegrinder", "bow": "ashstring", "fist": "penitent_knuckles", "scythe": "requiem_scythe",
           "bell": "dirge_bell"}
V15_PREFIX = {"saxe": "sx", "bow": "bw", "fist": "ft", "scythe": "sc", "bell": "wb"}

IRON = ((150, 150, 166), (96, 96, 112), (52, 50, 62), (30, 28, 36))
EMBER = ((255, 230, 150), (255, 150, 60), (190, 70, 30))


def _lit(vl, hi, mid, lo, k=0.3):
    return hi if vl > k else (lo if vl < -k else mid)


# ---------------------------------------------------------------- saxe: Gravegrinder (axe mode)
def shp_gravegrinder(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 8.0                                   # axe head span along the haft
    if h0 <= u <= tip + 0.3:                         # crescent axe head on the +v side, toothed edge
        t = (u - h0) / 8.0
        vmax = 1.8 + 4.4 * math.sin(math.pi * min(1.0, t)) ** 0.7
        if 0.6 <= v <= vmax:
            if v > vmax - 0.95:                      # the chain-toothed edge
                return (236, 236, 244) if int(math.floor(u * 1.4)) % 2 else (130, 130, 146)
            if abs(v - (vmax - 1.9)) < 0.4 and 0.2 < t < 0.85:
                return EMBER[2]                      # the grinding channel, ember-hot
            return _lit(vl, IRON[0], IRON[1], IRON[2])
        if -2.1 <= v < 0.6 and u >= tip - 3.2:       # spine counterweight / beak
            return _lit(vl, IRON[1], IRON[2], IRON[3])
    if 2.0 <= u < h0 and -2.0 <= v <= -0.85:         # the folded sword blade along the haft
        if v < -1.6:
            return (214, 220, 236)                   # its edge
        return (118, 124, 146) if vl > 0 else (70, 74, 92)
    if h0 - 2.6 <= u < h0 - 0.8 and abs(v) <= 1.0:  # phial housing with an ember core
        return EMBER[0] if abs(v) < 0.45 else (EMBER[1] if vl > 0 else EMBER[2])
    if -7.0 <= u < h0 and abs(v) <= 0.72:           # haft
        iu = int(math.floor(u))
        if iu in (-1, 5) or iu == int(h0) - 4:
            return (200, 160, 80)                    # gold bands
        return (70, 54, 48) if vl > 0 else (38, 28, 26)
    if -8.4 <= u < -7.0 and abs(v) <= 1.1:          # iron butt
        return IRON[1] if vl > 0 else IRON[3]
    return None


# ---------------------------------------------------------------- bow: Ashstring Recurve
def shp_ashstring(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    # the limbs: from the grip out to v = +-8.5, bowed toward the archer (-u) and flicked forward at the tips (recurve)
    av = abs(v)
    if av <= 8.8:
        t = av / 8.5
        uc = 1.2 - 3.0 * math.sin(math.pi * min(t, 1.0) * 0.8) + (2.6 * (t - 0.8) / 0.2 if t > 0.8 else 0.0)
        w = 0.95 if t < 0.85 else 0.6
        if abs(u - uc) <= w and av >= 0.6:
            if t > 0.88:
                return (220, 200, 150)               # horn nocks
            return (110, 66, 44) if (u - uc) * s * -1 > 0 else (62, 34, 26)
    if av <= 0.9 and -0.6 <= u <= 1.6:               # grip wrap
        return (150, 120, 80) if vl > 0 else (90, 70, 46)
    # the string: a straight chord between the limb tips, behind the grip
    if abs(u - (-1.6 + 0.05 * av)) <= 0.38 and 1.0 < av <= 8.2:
        return (210, 206, 196)
    # the nocked arrow along v = 0: shaft, broadhead at the tip, fletching at the string
    if abs(v) <= 0.45 and -2.6 <= u <= tip - 2.6:
        if u < -0.8:
            return (190, 60, 50)                     # fletching
        return (176, 150, 110)
    if tip - 2.6 <= u <= tip and abs(v) <= 1.3 * (tip - u) / 2.6 + 0.2:
        return (230, 236, 250) if vl >= 0 else (130, 136, 160)
    return None


# ---------------------------------------------------------------- fist: Penitent's Knuckles
def shp_penitent_knuckles(u, v, s, L):
    vl = v * s
    if 0.8 <= u <= 2.8 and abs(v) <= 2.4:            # the knuckle plate over the fist
        if u > 2.2:
            return (176, 176, 190) if vl > -0.5 else IRON[1]
        return _lit(vl, IRON[1], IRON[2], IRON[3])
    if 2.8 < u <= 4.6:                               # three spikes
        for c in (-1.6, 0.0, 1.6):
            if abs(v - c) <= 0.6 * (4.6 - u) / 1.8 + 0.05:
                return (220, 222, 236) if vl > -0.3 else (120, 120, 136)
    if -2.8 <= u < 0.8 and abs(v) <= 1.25:          # the wrapped wrist (bandage bands, old blood)
        iu = int(math.floor(u * 1.2 + v * 0.6))
        if iu % 4 == 0:
            return (120, 40, 36)
        return (214, 200, 168) if vl > 0 else (150, 136, 108)
    if -5.6 <= u < -2.8:                             # a loose wrap end trailing back
        c = 0.9 * math.sin(u * 1.3)
        if abs(v - c) <= 0.45:
            return (200, 186, 156) if u > -4.6 else (150, 136, 108)
    return None


# ---------------------------------------------------------------- scythe: Requiem
def _requiem(G):
    def shp_requiem_scythe(u, v, s, L, back=6.5):
        tip = L + 1.5
        b = G._scythe_blade(u, v, tip, reach=13.0, sweep=7.0, w0=2.7)
        if b:
            e, sp, t = b
            if e < 0.8:
                return (206, 170, 255)               # the soul-edge
            if e < 1.5:
                return (236, 232, 246)
            return (176, 170, 186) if sp > 1.0 else (104, 98, 116)
        if tip - 2.2 <= u <= tip and abs(v) <= 1.4:   # skull-iron collar at the head
            return (210, 204, 190) if v * s > 0 else (110, 100, 96)
        if -back <= u < tip - 2.2 and abs(v) <= 0.72:
            iu = int(math.floor(u))
            if iu % 7 == 3:
                return (150, 110, 210)               # violet rings
            return (54, 46, 60) if v * s > 0 else (24, 20, 28)
        if -back - 1.6 <= u < -back and abs(v) <= 1.0:
            return (110, 100, 96)
        return None
    return shp_requiem_scythe


# ---------------------------------------------------------------- bell: Dirgebell
def shp_dirge_bell(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 8.5
    if h0 <= u <= tip:
        t = (u - h0) / 8.5                           # a real bell: domed crown, straight waist, flared lip
        hw = 2.9 * math.sqrt(t / 0.18) if t < 0.18 else 2.9 + 0.5 * (t - 0.18) / 0.57 if t < 0.75 else 3.4 + 2.0 * ((t - 0.75) / 0.25) ** 1.4
        if abs(v) <= hw:
            if u > tip - 0.9 and abs(v) < hw - 1.4:
                if abs(v) < 0.8:
                    return (220, 190, 120)           # the clapper in the mouth
                return (18, 12, 16)                  # dark mouth
            if u > tip - 1.3 or abs(v) > hw - 0.7:
                return (236, 206, 130) if vl > 0 else (150, 112, 52)   # pale-gold lip / rim
            if abs(u - (tip - 3.0)) < 0.45 or abs(u - (h0 + 2.0)) < 0.4:
                return (150, 112, 52)                # sound-bow band
            if ((int(u * 1.3) * 5 + int(v * 1.1) * 3) % 13) == 0 and vl > -1:
                return (200, 120, 60)                # ember glint in the rune cuts
            return _lit(vl, (92, 88, 104), (56, 52, 66), (30, 28, 38), 1.0)
    if h0 - 2.0 <= u < h0 and 0.5 <= abs(v) <= 1.6:  # crown loop
        return (150, 112, 52) if vl > 0 else (76, 54, 30)
    if -3.4 <= u < h0 - 0.8 and abs(v - 0.4) <= 0.75:  # haft, chain-wound below the head
        iu = int(math.floor(u))
        if u > h0 - 5.5 and (iu + (1 if v > 0.4 else 0)) % 2 == 0:
            return IRON[0] if vl > 0 else IRON[2]
        return (92, 64, 44) if vl > 0 else (56, 38, 28)
    if -4.8 <= u < -3.4 and abs(v - 0.4) <= 1.2:
        return IRON[1] if vl > 0 else IRON[3]
    return None


SMEARS = {
    "gravegrinder": ((255, 236, 200), (240, 150, 70), (130, 60, 34)),
    "ashstring": ((244, 240, 228), (196, 180, 150), (110, 96, 78)),
    "penitent_knuckles": ((250, 236, 214), (210, 170, 130), (120, 84, 64)),
    "requiem_scythe": ((240, 228, 255), (170, 130, 240), (80, 56, 140)),
    "dirge_bell": ((255, 240, 196), (226, 178, 96), (124, 86, 44)),
}


def install(G):
    """Add the five weapons to gen_player: shapes, smears, haft paths, the overlay list and the move-class prefixes."""
    req = _requiem(G)
    G.WPN.update({
        "gravegrinder":      (shp_gravegrinder, 22, 9.0, 6.0, "blade"),
        "ashstring":         (shp_ashstring, 15, 3.5, 9.0, "blade"),
        "penitent_knuckles": (shp_penitent_knuckles, 4, 6.0, 2.5, "blade"),
        "requiem_scythe":    (req, 23, 8.5, 13.5, "blade"),
        "dirge_bell":        (shp_dirge_bell, 21, 5.0, 6.4, "maul"),
    })
    G.STAFF_BACK["requiem_scythe"] = 6.5          # both ends of the haft drawn, like the v9 scythes
    G.SCYTHE_BACK["requiem_scythe"] = 6.5
    G.SMEAR.update(SMEARS)
    for t in V15_TYPES:
        if V15_WPN[t] not in G.WPN_IDS:
            G.WPN_IDS.append(V15_WPN[t])
    # hit boxes of <prefix>_* tags are measured with the type's own weapon (sc_ was the v9 Briar Scythe's)
    G.MOVE_CLASS.update({V15_PREFIX[t]: (V15_WPN[t],) for t in V15_TYPES})
