await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = {}; for (const k of Object.keys(G.lx ? G.lx.LX_AMB : {})) G.SAVE.seenAreas[k] = 1; G.giveArmory();
const o = ['gl ' + G.GFX.ok + ' lx ' + JSON.stringify({ on: G.lx.LX.on, bad: G.lx.LX.bad, NL: G.lx.LX.NL })];
const R = (typeof QR !== 'undefined') ? QR : [['C2', 24, 10]];
for (const [r, x, y] of R) { G.tp(r, x, y); G.enemies.length = 0; G.P.hp = 99999; for (let i = 0; i < 6; i++) { G.step(40); if (G.state !== 'play') G.step(1, [], ['pause']); }
  for (const m of [0, 2]) { G.SETTINGS.light = m; G.step(1); await snap('q_' + r + '_' + m); }
  o.push(r + ' n=' + G.lx.LX.n + ' amb=' + G.lx.LX.amb.map(v => v.toFixed(2))); }
return o;
