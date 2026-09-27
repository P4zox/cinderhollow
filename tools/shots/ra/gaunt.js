await boot(); G.SETTINGS.god = true; const out = [];
for (const [r, x, y, gid] of [['R13', 24, 10, 'gM'], ['C13', 22, 11, 'gC']]) {
  G.tp(r, x, y); G.step(20); out.push(`${r} gate open before: ${G.KIT.byId[gid].on}`);
  G.step(1, [], ['interact']); G.step(90); out.push(`${r} started: gate ${G.KIT.byId[gid].on}, foes ${G.enemies.filter(e => e.alive).length}`);
  if (r === 'R13') await snap('g_r13_fight');
  let waves = 0;
  for (let k = 0; k < 40; k++) {
    const al = G.enemies.filter(e => e.alive);
    if (al.length) { waves++; for (const e of al) e.die({ dir: 1 }); }
    G.step(120);
    if (G.KIT.byId[gid].on && !G.enemies.some(e => e.alive)) break;
  }
  G.step(120);
  out.push(`${r} cleared: gate ${G.KIT.byId[gid].on}, kill rounds ${waves}, flag ${G.SAVE.flags['x3:' + r + ':' + (r === 'R13' ? 'muster' : 'charnel')]}, shards ${G.SAVE.shards}, inv ${JSON.stringify(G.SAVE.inv)}`);
}
return out;
