await boot(); G.SETTINGS.god = 1; const S = window.__sys, log = [];
const gate = () => { const d = S.roomObj.dyn.find(q => q.kit && q.kit.id === 'gL'); return d ? (d.y1 - d.y0 > 8 ? 'closed' : 'open') : 'none'; };
G.tp('T2', 81, 26); G.step(60); log.push('before: gate ' + gate());
await snap('g01_marker');
G.step(1, [], ['interact']); G.step(30); log.push('started: ' + !!S.SYS.gaunt + ' gate ' + (G.step(60), gate()));
await snap('g02_intro');
const killWave = async (name) => {
  for (let i = 0; i < 200 && S.SYS.gaunt && S.SYS.gaunt.state !== 'wave'; i++) G.step(1);
  for (let i = 0; i < 80; i++) G.step(1);   // portents, enemies drop in
  if (name) await snap(name);
  const n = G.enemies.length; for (const e of window.__game.enemies) if (e.alive && e.x3g) e.die({ dir: 1 });
  log.push('wave ' + (S.SYS.gaunt && S.SYS.gaunt.wave + 1) + ' killed ' + n);
  for (let i = 0; i < 90; i++) G.step(1);
};
await killWave('g03_wave1'); await killWave('g04_wave2'); await killWave('g05_wave3');
for (let i = 0; i < 60; i++) G.step(1); await snap('g06_cleared');
log.push('after: running ' + !!S.SYS.gaunt + ' gate ' + gate() + ' flag ' + G.SAVE.flags['x3:T2:g1'] + ' shards ' + G.SAVE.shards);
for (let i = 0; i < 300; i++) G.step(1);
log.push('rewards: emberstone ' + (G.SAVE.inv.emberstone||0) + ' shards ' + G.SAVE.shards + ' cinders ' + G.SAVE.cinders);
// replay grants cinders only; death resets
G.step(1, [], ['interact']); G.step(60); log.push('replay gate ' + gate());
G.SETTINGS.god = 0; G.P.hp = 1; window.__game.P.inv = 0;
for (let i = 0; i < 400 && G.state === 'play'; i++) { G.step(1); if (G.enemies.some(e => e.alive && e.x3g)) { const e = G.enemies.find(e => e.alive && e.x3g); G.P.x = e.x - 10; } }
log.push('death: state ' + G.state + ' gaunt ' + !!S.SYS.gaunt);
for (let i = 0; i < 400 && G.state !== 'play'; i++) G.step(1);
log.push('respawned in ' + G.room + ' gaunt ' + !!S.SYS.gaunt);
return log;
