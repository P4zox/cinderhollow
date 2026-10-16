"""v16 fatality tags for the heavy group (stub: the weapon agent fills it in). Same register(G) contract as
player_v16_fatal_blade.py: return [(tag, fn) or (tag, fn, opts)]; one <prefix>_fatal tag per weapon type."""

G = None   # gen_player, set by register()


def register(g):
    global G
    G = g
    return []
