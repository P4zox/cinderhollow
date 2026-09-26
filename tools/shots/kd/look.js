await boot();
G.SAVE.flags['cut:kalden'] = 1; delete G.SAVE.flags['boss:kalden'];
G.tp('M5', 6, 10); const b = G.boss;
for (let i = 0; i < 200 && !b.active; i++) { G.step(2, ['right']); if (G.state === 'cut') G.step(1, [], ['pause']); }
for (let i = 0; i < 100 && b.introT > 0; i++) G.step(2);
b.hp = Math.round(b.maxHp * 0.45);
for (let i = 0; i < 400 && b.phase !== 2; i++) { G.step(1); G.P.hp = 99999; if (i % 12 === 0 && i < 100) await snap('p2scene_' + i); }
for (let i = 0; i < 300 && (G.state === 'cut' || G.state === 'cine'); i++) { G.step(2); if (i % 20 === 0) await snap('p2cut_' + i); }
for (let i = 0; i < 300 && (G.state === 'cut' || G.state === 'cine'); i++) G.step(1, [], ['pause']);
for (let i = 0; i < 60; i++) { G.step(2); G.P.hp = 99999; }
async function show(m, d, every, n, tag) {
  for (let i = 0; i < 60; i++) { G.step(2); G.P.hp = 99999; }
  b.x = 300; b.y = b.floor; G.P.x = 300 + d; G.P.y = b.floor; G.P.inv = 0; b.cool = 99; b.state = 'idle'; b.chain = 99; b.cds = {};
  b.start(m); b.chain = 99;
  for (let i = 0, k = 0; i < n * every; i++) { G.step(1); b.cool = 9; G.P.hp = 99999; if (i % every === every - 1) await snap(`${tag}_${k++}`); }
}
await show('tendrils', 150, 8, 8, 'tend');
await show('grab', 70, 10, 8, 'grab');
await show('rotring', 40, 10, 8, 'ring');
await show('berserk', 60, 12, 8, 'bers');
return 'ok';
