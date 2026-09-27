// quick look-dev: apply TUNE, shoot classic + dynamic+shadows in a few rooms, pair them per room
await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = {}; for (const k of Object.keys(G.lx.LX_AMB)) G.SAVE.seenAreas[k] = 1;
const TUNE = {};
Object.assign(G.lx.LX_TUNE, TUNE);
const R = [['C2', 24, 10], ['K1', 24, 10], ['D2', 6, 10], ['A2', 24, 10]];
for (const [r, x, y] of R) { G.tp(r, x, y); G.enemies.length = 0; for (let i = 0; i < 8; i++) { G.step(40); if (G.state !== 'play') G.step(1, [], ['pause']); }
  for (const m of [0, 2]) { G.SETTINGS.light = m; G.step(1); await snap('t_' + r + '_' + m); } }
return 'ok';
