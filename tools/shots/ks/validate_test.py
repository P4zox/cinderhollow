# Deliberately broken system spawns: every one must produce an ERR from tools/rooms.py validate_sys().
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import reach as RC
m = RC._load_rooms()
r = m.Room('ZZ1', 'Broken', 'spire', 5000, 0, 24, 14, indoor=True, test=True, spawns=[
    {'t': 'sys', 'kind': 'door', 'x': 3, 'y': 10, 'id': 'a', 'to': 'ZZ2', 'toId': 'b'},      # partner points elsewhere
    {'t': 'sys', 'kind': 'door', 'x': 6, 'y': 10, 'id': 'c', 'to': 'NOPE'},                  # no such room
    {'t': 'sys', 'kind': 'door', 'x': 9, 'y': 6, 'id': 'd', 'to': 'ZZ2', 'toId': 'zz'},      # floating + missing partner
    {'t': 'sys', 'kind': 'trial', 'x': 12, 'y': 10, 'id': 't'},                              # no goal
    {'t': 'sys', 'kind': 'trial_goal', 'x': 14, 'y': 10, 'trial': 'q'},                      # no sigil q
    {'t': 'sys', 'kind': 'gauntlet', 'x': 16, 'y': 10, 'id': 'g', 'gates': ['nope'], 'waves': []},
    {'t': 'sys', 'kind': 'lore', 'x': 18, 'y': 10},
    {'t': 'sys', 'kind': 'passage', 'x': 23, 'y': 10, 'h': 3},                               # in the wall
    {'t': 'sys', 'kind': 'teleporter', 'x': 20, 'y': 10},
])
r.walls().fill(0, 11, 23, 13)
r2 = m.Room('ZZ2', 'Broken 2', 'spire', 5100, 0, 24, 14, indoor=True, test=True, spawns=[
    {'t': 'sys', 'kind': 'door', 'x': 3, 'y': 10, 'id': 'b', 'to': 'ZZ1', 'toId': 'c'}])
r2.walls().fill(0, 11, 23, 13)
errs = [e for e in m.validate_sys() if e.startswith('ZZ')]
for e in errs: print('ERR', e)
print(len(errs), 'errors (expect 12: one per broken spec + the partner back-pointer)')
