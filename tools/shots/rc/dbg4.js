await boot(); G.grantTechniques(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { crown: 1 }; const log = [];
for (const on of [false, true]) {
  G.SAVE.charms = on ? ['c_x3_crown'] : []; G.SAVE.charmsEq = on ? ['c_x3_crown'] : [];
  G.tp('D9', 12, 37); G.step(60); const tr = [G.state];
  G.step(1, ['jump'], ['jump']); for (let i = 0; i < 12; i++) { G.step(1, ['jump']); tr.push(G.P.state[0] + Math.round(G.P.y)); }
  G.P.st = 50; G.step(1, ['down'], ['heavy']); tr.push(G.P.state + ' st ' + G.P.st.toFixed(1));
  log.push((on ? 'crown ' : 'plain ') + tr.join(' ')); G.step(60);
}
return log;
