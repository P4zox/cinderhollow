G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1 });
const out = [];
for (const [r, x, y] of [['E6', 20, 14], ['E6', 27, 14], ['E5', 50, 26], ['D5', 10, 10], ['NV7', 20, 14], ['CM7', 20, 14], ['DB6', 20, 18], ['SP7', 20, 14], ['A7', 10, 10], ['K4', 20, 10]]) {
  try { G.tp(r, x, y); G.step(90); G.enemies.length = 0; G.step(2); await snap('ref_' + r + '_' + x); out.push(r + ' ok'); } catch (e) { out.push(r + ' ERR ' + e.message); }
}
return out;
