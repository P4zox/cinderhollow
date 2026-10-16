await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1, hook: 1 });
const SP = window.__cfSpots || [['CF8', 44, 17, 1], ['CF6', 20, 15], ['CT1', 10, 13], ['CT1', 30, 13], ['CF4', 60, 11], ['CF5', 30, 5], ['CF3', 14, 26]];
const out = [];
for (const [r, x, y, bossdone] of SP) {
  if (bossdone) G.SAVE.flags['boss:hearthkeeper'] = 1; else delete G.SAVE.flags['boss:hearthkeeper'];
  G.tp(r, x, y); for (let i = 0; i < 90; i++) { G.step(1); G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); }
  if (G.xs) G.xs.clean(); G.step(2); await snap(`l2_${r}_${x}`); out.push(r + ' ' + G.state);
}
return out;
