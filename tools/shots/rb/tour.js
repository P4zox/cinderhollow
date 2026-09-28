await boot(); G.SETTINGS.god = true;
G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, ramparts: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1, hook: 1, emberdash: 1, wings: 1 } });
const only = (window.__only || '').split(',').filter(Boolean);
const spots = [
  ['M7a', 'M7', 72, 6], ['M7b', 'M7', 36, 16], ['M7c', 'M7', 10, 20], ['M8', 'M8', 20, 8], ['M8b', 'M8', 42, 9], ['M13', 'M13', 12, 10], ['M10', 'M10', 40, 8], ['M10b', 'M10', 12, 10],
  ['M14', 'M14', 13, 8], ['M11', 'M11', 6, 5], ['M11b', 'M11', 30, 5], ['M9', 'M9', 10, 10], ['M9b', 'M9', 30, 10], ['M12', 'M12', 5, 5], ['M12b', 'M12', 20, 22],
  ['A10', 'A10', 5, 46], ['A10b', 'A10', 18, 10], ['A10c', 'A10', 19, 42], ['A8a', 'A8', 21, 44], ['A8b', 'A8', 8, 30], ['A8c', 'A8', 56, 32], ['A8d', 'A8', 30, 6], ['A9', 'A9', 20, 10], ['A13', 'A13', 19, 14],
  ['A12', 'A12', 17, 11], ['A11', 'A11', 4, 10], ['A11b', 'A11', 40, 9], ['A14', 'A14', 10, 9], ['A16', 'A16', 2, 8], ['A15', 'A15', 3, 28], ['A15b', 'A15', 36, 14],
  ['HF10', 'HF10', 5, 9], ['HF10b', 'HF10', 40, 9], ['HF8a', 'HF8', 10, 52], ['HF8b', 'HF8', 24, 30], ['HF8c', 'HF8', 38, 4], ['HF11', 'HF11', 72, 11], ['HF11b', 'HF11', 30, 11],
  ['HF14', 'HF14', 14, 14], ['HF15', 'HF15', 28, 18], ['HF15b', 'HF15', 40, 5], ['HF12', 'HF12', 19, 14], ['HF12b', 'HF12', 36, 10], ['HF9', 'HF9', 10, 12], ['HF9b', 'HF9', 35, 12],
  ['HF13', 'HF13', 13, 6], ['HF13b', 'HF13', 20, 20], ['HF16', 'HF16', 3, 6], ['W3a', 'W3', 8, 23], ['W3b', 'W3', 3, 43], ['W5', 'W5', 3, 30],
  ['o_M1', 'M1', 16, 3], ['o_A5', 'A5', 30, 6], ['o_A4', 'A4', 4, 24], ['o_HF6', 'HF6', 8, 12],
];
const out = [];
for (const [n, r, x, y] of spots) {
  if (only.length && !only.includes(r) && !only.includes(n)) continue;
  G.tp(r, x, y); G.step(240); await snap('t_' + n);
  out.push(n + ' ' + JSON.stringify(G.step(1).p));
}
return out;
