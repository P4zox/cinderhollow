"""v15 tags for the Scythe (scythe, prefix sc_, weapon requiem_scythe) -- docs/WEAPON_REVAMP.md C4. Note: the v9 tags sc_1 sc_2 sc_3 sc_heavy sc_up sc_air sc_down already exist (gen_player V9_MOVES) and the skeleton plays them.

STUB (platform agent): the moveset agent for this type owns this file. Same register(G) contract as player_v13_a.py /
player_v14_*.py: return [(tag, fn, opts)], fn() -> [(cels, ms)]; opts: active=(i0, i1), hits=[...], kinds=(...), both=True,
up=True, down=True, hit=[x0, y0, x1, y1], fxat=(x, y) ... (see gen_player._v13_take). Tags must start with the type's
prefix so their hit boxes are measured with this type's weapon (MOVE_CLASS, set by art/player_v15_weapons.py).
gen_player loads the v15 modules after V14 in the fixed order saxe, bow, fist, scythe, bell; a module that fails is
skipped with a warning. To restyle the weapon itself, set G.WPN / G.SMEAR for its id here (see player_v15_weapons.py).
"""

G = None   # gen_player, set by register()


def register(g):
    global G
    G = g
    return []
