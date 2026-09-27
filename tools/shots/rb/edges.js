await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1 };
G.give({ items: { talon: 1, hook: 1, emberdash: 1 } });
const out = [];
const H = r => window.__sys.roomObj.def.h;
// [kind, room, x, y, expect]   drop: stand on the boards and ↓+jump · up: jump (holding up) from the platform under a hole · R/L: walk
const T = [
  ['drop', 'M7', 3, 22, 'M8'], ['up', 'M8', 3, 1, 'M7'], ['R', 'M8', 45, 9, 'M13'], ['L', 'M13', 2, 9, 'M8'],
  ['drop', 'M8', 41, 12, 'M10'], ['up', 'M10', 41, 1, 'M8'], ['R', 'M10', 45, 8, 'M14'], ['L', 'M14', 2, 8, 'M10'],
  ['drop', 'M10', 3, 14, 'M11'], ['up', 'M11', 3, 1, 'M10'], ['drop', 'M11', 37, 12, 'M9'], ['up', 'M9', 37, 1, 'M11'],
  ['R', 'M11', 39, 5, 'M12'], ['L', 'M12', 3, 5, 'M11'], ['R', 'M9', 39, 8, 'M12'], ['L', 'M12', 2, 22, 'M9'],
  ['up', 'A10', 11, 1, 'A8'], ['drop', 'A8', 21, 46, 'A10'], ['L', 'A8', 3, 44, 'A9'], ['R', 'A9', 36, 10, 'A8'],
  ['L', 'A8', 3, 30, 'A13'], ['R', 'A13', 37, 14, 'A8'], ['up', 'A8', 7, 1, 'A11'], ['drop', 'A11', 7, 14, 'A8'],
  ['R', 'A11', 53, 9, 'A14'], ['L', 'A14', 2, 9, 'A11'], ['R', 'A10', 21, 28, 'A15'], ['L', 'A15', 2, 28, 'A10'],
  ['up', 'A13', 4, 2, 'A12'], ['drop', 'A12', 4, 18, 'A13'],
  ['up', 'HF10', 53, 1, 'HF8'], ['drop', 'HF8', 5, 54, 'HF10'], ['up', 'HF10', 27, 1, 'HF13'], ['drop', 'HF13', 19, 20, 'HF10'],
  ['up', 'HF8', 43, 1, 'HF11'], ['drop', 'HF11', 75, 14, 'HF8'], ['drop', 'HF11', 3, 14, 'HF12'], ['up', 'HF12', 19, 1, 'HF11'],
  ['drop', 'HF12', 41, 16, 'HF9'], ['up', 'HF9', 41, 1, 'HF12'], ['drop', 'HF9', 21, 14, 'HF13'], ['up', 'HF13', 13, 1, 'HF9'],
  ['up', 'HF11', 71, 1, 'HF14'], ['drop', 'HF14', 27, 16, 'HF11'], ['up', 'HF11', 11, 1, 'HF15'], ['drop', 'HF15', 31, 20, 'HF11'],
];
for (const [k, r, x, y, want] of T) {
  G.tp(r, x, y); G.step(20);
  if (k === 'drop') { G.step(2, ['down']); G.step(1, ['down', 'jump'], ['jump']); G.step(60, ['down']); }
  else if (k === 'up') { G.step(1, ['up', 'jump'], ['jump']); G.step(40, ['up', 'jump']); G.step(20); }
  else G.step(80, [k === 'R' ? 'right' : 'left']);
  out.push(`${k} ${r}(${x},${y}) -> ${G.room} ${G.room === want ? 'OK' : 'FAIL want ' + want} @${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)}`);
}
return out;
