await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1 } });
G.SAVE.flags['x3:A13:cipher'] = 1;   // the Cipher Wall's puzzle (solved in puzzles.js) opens A13 -> A12
const W = window.__walker, t0 = performance.now();
const route = ['A8', 'A5', 'A8', 'A13', 'A12', 'A13', 'A8', 'A10', 'A15', 'A10', 'A9', 'A15', 'A9', 'A16', 'A9', 'A10', 'A11', 'A14', 'A11', 'A10', 'A8', 'A4'];
const r = W.route(['A5', 20, 10], route, { budget: 1500, extra: { A9: () => [{ k: 'ATK', d: 1 }] } });
r.log.push(`ok ${r.ok} total ${Math.round((performance.now() - t0) / 1000)} s`);
return r.log;
