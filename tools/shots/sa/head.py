# ============================================================ EXPANSION 3 — agent SA: Thornveil Wood, Drowned Barrows, Crimson Manor
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, free_spot). Engine: web/src/53_sa.js.
# Art: art/gen_xsa*.py -> assets/xsa_*. Every module-level name here is prefixed _sa.
#
# Custom spawns (53_sa.js): xsa, kind = prop | skins | frontpaint | flies | motes | shaft | bubbles | pearls | petals | leak |
#   sign | rite | tide | floodgates | trialgate | gaze | bookcase | keygate | glasshouse | piano
#   prop      : decor sprite from the xsa_* sheets (sheet, tag), back=True paints it into the room's back layer
#   skins     : repaints solid cells of the front layer (bark trunks, leaf canopy, roof slates, glass) — _sa_skins()
#   bookcase  : a false bookcase over wall cells that are open in the map; solid until struck three times (a secret)
#   keygate   : a KM gate held shut until the three study keys are turned in it
# Wings (docs/EXPANSION3_CONTRACT.md §8: walkable, edge to edge, no doors):
#   Thornveil: TV2 (a root-hole in the floor) -> TV10 -> TV9 -> TV11 -> TV5 (a gate in TV11 opens the shortcut)
#   Barrows:   DB3 (a hole in the roof) -> DB11 -> DB10 -> DB12 -> DB4 (a gate in DB12 opens the shortcut).
#              W4, the drowned shaft from K2 down to DB1, is rebuilt here: side rooms open off it (it's the region's spine)
#   Crimson:   CM4 (the gallery's east window) -> CM9 -> CM11 -> CM10 -> CM8 (a gate in CM10 opens the shortcut)


def _sa_paint(r, rows, x0=0, y0=0):
    for y, row in enumerate(rows):
        if x0 == 0 and len(row) != r.w: print(f'SA PAINT {r.id} row {y0 + y}: {len(row)} cols, want {r.w}')
        for x, ch in enumerate(row):
            if ch != ' ':
                r.g[y0 + y][x0 + x] = ch
    return r


def _sa_prop(tag, x, y, sheet='xsa_tv', **kw):
    return dict(t='xsa', kind='prop', sheet=sheet, tag=tag, x=x, y=y, **kw)


def _sa_skins(r, *rects):
    """repaint solid cells of the front layer (bark, leaves, slates, glass...). The spawn sits in any open cell."""
    x, y = next((x, y) for y in range(r.h) for x in range(r.w) if r.g[y][x] == '.')
    r.kw.setdefault('spawns', []).append(dict(t='xsa', kind='skins', x=x, y=y, list=[list(q) for q in rects]))


def _sa_k(kind, x, y, **kw):
    return dict(t='kit', kind=kind, x=x, y=y, **kw)


def _sa_s(kind, x, y, **kw):
    return dict(t='sys', kind=kind, x=x, y=y, **kw)


def _sa_en(type_, x, y, **kw):
    return dict(t='enemy', type=type_, x=x, y=y, **kw)


def _sa_pt(x, y, subj, **kw):
    return dict(t='cm_portrait', x=x, y=y, subj=subj, **kw)


def _sa_tv(kind, x, y, **kw):
    return dict(t='tv_prop', kind=kind, x=x, y=y, **kw)


def _sa_db(kind, x, y, **kw):
    return dict(t='db_prop', kind=kind, x=x, y=y, **kw)


def _sa_cm(kind, x, y, **kw):
    return dict(t='cm_prop', kind=kind, x=x, y=y, **kw)


