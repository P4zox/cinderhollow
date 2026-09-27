# KS proving room (Expansion 3 kit systems). Debug only: test=True rooms are sealed, off the map, reached via __game.tp.
# T2  : doors (arch / portal / hatch / crack-auto), a hidden passage into a sealed closet, a lore tablet, a vista bench,
#       a trial over a spike floor, and a gauntlet arena behind a kit gate.
# T2b : the partner room for the four doors.
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).

_t = Room('T2', 'Proving Hall of Systems', 'spire', -300, 0, 96, 30, indoor=True, test=True, needs=['start'], x3=True, trial=True, gauntlet=True, vista=True,
          spawns=[
              # the sealed closet (x 1..6): a crack door back from T2b and a lore page
              {'t': 'sys', 'kind': 'door', 'x': 2, 'y': 26, 'id': 'd4', 'to': 'T2b', 'toId': 'd4', 'look': 'crack', 'auto': True},
              {'t': 'sys', 'kind': 'lore', 'x': 5, 'y': 26, 'page': 'ks_3', 'look': 'corpse'},
              {'t': 'sys', 'kind': 'passage', 'x': 7, 'y': 26, 'w': 1, 'h': 3, 'id': 'seal',
               'cond': {'flag': 'x3test:seal', 'restAfter': True, 'minTime': 300}, 'drift': 'seed'},
              # doors to T2b
              {'t': 'sys', 'kind': 'door', 'x': 16, 'y': 26, 'id': 'd1', 'to': 'T2b', 'toId': 'd1', 'look': 'arch'},
              {'t': 'sys', 'kind': 'door', 'x': 20, 'y': 26, 'id': 'd2', 'to': 'T2b', 'toId': 'd2', 'look': 'portal', 'skin': 'neon'},
              {'t': 'sys', 'kind': 'lore', 'x': 24, 'y': 26, 'page': 'ks_1', 'look': 'tablet'},
              {'t': 'sys', 'kind': 'bench', 'x': 28, 'y': 26, 'id': 'bench', 'view': [44, 16], 'lore': 'ks_2'},
              # the trial: sigil, pillars over spikes, goal on the high ledge
              {'t': 'sys', 'kind': 'trial', 'x': 32, 'y': 26, 'id': 'tr1', 'par': 12, 'reward': 'emberstone', 'region': 'Proving Hall', 'bonus': 200},
              {'t': 'sys', 'kind': 'trial_goal', 'x': 60, 'y': 13, 'trial': 'tr1'},
              {'t': 'kit', 'kind': 'crumble', 'x': 50, 'y': 16, 'w': 3, 'delay': 0.6, 'respawn': 4},   # reset by the trial
              {'t': 'sys', 'kind': 'door', 'x': 65, 'y': 26, 'id': 'd3', 'to': 'T2b', 'toId': 'd3', 'look': 'hatch'},
              # the gauntlet arena behind gate gL
              {'t': 'kit', 'kind': 'gate', 'x': 68, 'y': 26, 'id': 'gL', 'open': True},
              {'t': 'sys', 'kind': 'gauntlet', 'x': 81, 'y': 26, 'id': 'g1', 'look': 'banner', 'name': 'The Proving Muster', 'gates': ['gL'],
               'waves': [[{'type': 'hollow_soldier', 'x': 75, 'y': 26}, {'type': 'hollow_soldier', 'x': 90, 'y': 26}],
                         [{'type': 'rot_crawler', 'x': 74, 'y': 26}, {'type': 'rot_crawler', 'x': 91, 'y': 26}, {'type': 'hollow_archer', 'x': 88, 'y': 26}],
                         [{'type': 'shield_warden', 'x': 86, 'y': 26}, {'type': 'gloom_wisp', 'x': 76, 'y': 22}]],
               'reward': ['emberstone', 'shard']},
          ])
_t.walls().fill(0, 27, 95, 29).fill(0, 0, 95, 1)
_t.fill(7, 2, 7, 23)                      # closet wall; its bottom three cells are the hidden passage (open in the map)
_t.fill(34, 26, 63, 26, '^')              # spike floor under the trial
_t.fill(35, 24, 36, 26).fill(40, 21, 41, 26).fill(45, 18, 46, 26)   # pillars, 3 up each
_t.fill(56, 14, 63, 15)                   # the goal ledge
_t.fill(68, 2, 68, 19)                    # wall over the arena gate (the 7-tall gate reaches it: no jumping over)
for _x, _y, _ch in [(9, 26, 'P'), (11, 26, 'S'), (10, 2, 'l'), (30, 2, 'l'), (50, 2, 'l'), (78, 2, 'l'), (90, 2, 'l'), (3, 2, 'l')]:
    _t.put(_x, _y, _ch)

_b = Room('T2b', 'Proving Antechamber', 'catacombs', -520, 0, 28, 14, indoor=True, test=True, needs=['start'], x3=True,
          spawns=[
              {'t': 'sys', 'kind': 'door', 'x': 3, 'y': 10, 'id': 'd3', 'to': 'T2', 'toId': 'd3', 'look': 'ladder'},
              {'t': 'sys', 'kind': 'door', 'x': 9, 'y': 10, 'id': 'd1', 'to': 'T2', 'toId': 'd1', 'look': 'arch'},
              {'t': 'sys', 'kind': 'door', 'x': 15, 'y': 10, 'id': 'd2', 'to': 'T2', 'toId': 'd2', 'look': 'portal', 'skin': 'neon'},
              {'t': 'sys', 'kind': 'door', 'x': 25, 'y': 10, 'id': 'd4', 'to': 'T2', 'toId': 'd4', 'look': 'crack', 'auto': True},
          ])
_b.walls().fill(0, 11, 27, 13).fill(0, 0, 27, 1)
for _x, _y, _ch in [(6, 2, 'l'), (20, 2, 'l'), (12, 10, 'k'), (22, 10, 'b')]:
    _b.put(_x, _y, _ch)
