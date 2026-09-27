await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { mire: 1 }; G.give({ items: { talon: 1 } });
const S = window.__sys, log = [];
const gate = () => window.__rb.kit.byId.gW.on ? 'open' : 'closed';
G.tp('M13', 15, 10); G.step(60); log.push('before: gate ' + gate());
G.step(1, [], ['interact']); G.step(90); log.push('started: ' + !!S.SYS.gaunt + ' gate ' + gate());
for (let w = 0; w < 4; w++) {
  for (let i = 0; i < 300 && S.SYS.gaunt && S.SYS.gaunt.state !== 'wave'; i++) G.step(1);
  G.step(90); if (w === 0) await snap('gm13_w1'); if (w === 3) await snap('gm13_elite');
  const alive = G.enemies.filter(e => e.alive && e.x3g); log.push(`wave ${w + 1}: ${alive.map(e => e.type).join(',')}`);
  for (const e of alive) e.die({ dir: 1 });
  G.step(120);
}
G.step(300); await new Promise(r => setTimeout(r, 400));
log.push(`after: running ${!!S.SYS.gaunt} gate ${gate()} flag ${G.SAVE.flags['x3:M13:leech']} emberstone ${G.SAVE.inv.emberstone || 0} cinders ${G.SAVE.cinders}`);
return log;
