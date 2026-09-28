await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = []; T.start(); G.step(5);
for (const k of (window.__only || 'colossus,choir').split(',')) {
  T.summon(k); const b = G.boss;
  out.push(k + ' hp=' + b.hp + ' max=' + b.maxHp + ' parts=' + (b.parts ? b.parts.length + ':' + b.parts.map(p => p.hp).join('/') : '-') + ' x=' + Math.round(b.x) + ' y=' + Math.round(b.y) + ' floor=' + b.floor);
  for (let i = 0; i < 12; i++) { G.step(30); G.P.hp = 9999; out.push(`  t${i} s=${b.state} hp=${Math.round(b.hp)} ph=${b.phase} act=${b.active} x=${Math.round(b.x)} y=${Math.round(b.y)} P=${Math.round(G.P.x)},${Math.round(G.P.y)} tg=${G.trn.targets.length}`); }
  await snap('diag_' + k);
  T.clear(); G.step(3);
}
return out;
