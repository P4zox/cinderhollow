await boot();
const out = {};
for (const [id, tx, ty, type] of [['CM1', 20, 10, 'cm_servant'], ['CM5', 44, 7, 'cm_hound'], ['CM2', 16, 13, 'cm_gargoyle']]) {
  G.tp(id, tx, ty); let dmg = 0;
  for (let k = 0; k < 600; k++) { const h = G.P.hp; G.step(1); dmg += Math.max(0, h - G.P.hp); G.P.hp = G.D.maxHp; if (k === 200) await snap('en_' + type); }
  const es = G.enemies.filter(e => e.type === type);
  // now kill one with attacks
  const e = es[0]; let kills = 0;
  if (e) { for (let k = 0; k < 80 && e.alive; k++) { G.P.x = e.x - 18 * (e.face || 1); G.P.y = e.cfg.flying ? G.P.y : e.y; G.P.face = e.x > G.P.x ? 1 : -1; G.P.hp = G.D.maxHp; G.step(8, [], ['attack']); } kills = e.alive ? 0 : 1; }
  out[type] = { dmg: Math.round(dmg), n: es.length, states: es.map(e => e.state), killed: kills };
}
return out;
