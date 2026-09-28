window.__spots = "[[\"R5\",121,8],[\"R6\",20,10],[\"R7\",15,10],[\"R8\",30,6],[\"R9\",5,25],[\"R10\",3,7],[\"R11\",15,5],[\"R12\",10,16],[\"R13\",20,10],[\"R14\",8,6], [\"C7\",20,12],[\"C8\",40,28],[\"C9\",4,7],[\"C10\",10,10],[\"C11\",19,27],[\"C12\",20,13],[\"C13\",31,10],[\"C14\",8,9],[\"C15\",8,9],[\"W2\",2,12], [\"K5\",6,10],[\"K6\",15,24],[\"K7\",40,26],[\"K8\",20,10],[\"K9\",5,10],[\"K10\",15,14],[\"K11\",13,16],[\"K12\",4,38],[\"K13\",8,10]]";
await boot(); G.SETTINGS.god = true; const out = [];

for (const [r, x, y, gid] of [['R13', 12, 10, 'gM'], ['C13', 23, 11, 'gC']]) {
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
