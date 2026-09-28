# TRAINING GROUNDS (agent TR): a white dev test chamber reached only from the title screen (web/src/65_training.js).
# test=True: off the map, out of completion and reachability. Two sealed rooms joined by a doorway:
#   TR1  Test Chamber 01: movement + damage lab (wall-jump chimney, platforms, spike strip, hook ring, bramble patch, dummy)
#   TR2  Test Chamber 02: a wide, flat arena every boss is summoned into (the panel re-enters it with the boss's biome)
# Both share the same floor line (surface row 19) so the doorway is level. Runs inside tools/rooms.py's namespace.

TR_FLOOR = 19   # floor surface row; the standing row is 18

_a = Room('TR1', 'Test Chamber 01', 'training', -700, 0, 48, 22, indoor=True, test=True)
_a.walls().fill(0, TR_FLOOR, 47, 21).open('E', 15, 18)
_a.fill(5, 4, 5, 15)                      # wall-jump chimney (cols 1-4); walk in under its foot
_a.fill(6, 4, 11, 4, '=')                 # the ledge you climb out onto
_a.fill(14, 15, 18, 15, '=').fill(19, 11, 23, 11, '=').fill(13, 7, 17, 7, '=')   # a stair of one-way platforms
_a.fill(26, 18, 31, 18, '^')              # spike strip (pogo with a downward strike)
_a.put(28, 10, '@')                       # hook ring over the spikes
_a.fill(36, 18, 40, 18, '(')              # bramble patch (Thornveil tile: pogo off it too)
_a.put(16, 18, 'P')
_a.kw['spawns'] = [{'t': 'trn_dummy', 'x': 10, 'y': 18}]

_b = Room('TR2', 'Test Chamber 02', 'training', -652, 0, 56, 22, indoor=True, test=True)
_b.walls().fill(0, TR_FLOOR, 55, 21).open('W', 15, 18)
_b.fill(3, 12, 7, 12, '=').fill(48, 12, 52, 12, '=')   # two high perches, clear of the floor fight
_b.put(8, 18, 'P')
