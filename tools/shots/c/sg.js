await boot();
G.give({ items: { emberdash: 1 } });
G.tp('CM7', 6, 14); G.step(30, ['right']);
const log = [];
for (let i = 0; i < 400 && G.state === 'cut'; i++) G.step(10);
log.push({ state: G.state, boss: G.step(1).boss, cutflag: G.SAVE.flags['cut:sanguine'] });
await snap('sg_00_after_intro');
const B = G.boss, P = G.P;
const out = {};
for (const m of ['flurry', 'lunge', 'whip', 'lances', 'batport', 'dance']) {
  // stand at a sensible distance, full hp, then force the move and watch damage
  G.P.hp = G.D.maxHp; P.x = B.x - 55 * (Math.random() < 2 ? 1 : 1); P.y = 240; B.x = 400; P.x = 400 - (m === 'flurry' ? 50 : m === 'lances' ? 150 : 110); B.face = -1; B.state = 'idle'; B.cool = 99;
  window.__cm.force(m); const hp0 = P.hp; let shots = 0;
  for (let k = 0; k < 150; k++) { G.step(1); if (k % 25 === 5 && shots < 6) { shots++; await snap(`sg_${m}_${String(k).padStart(3, '0')}`); } }
  out[m] = { dmg: Math.round(hp0 - P.hp), bx: Math.round(B.x), st: B.state };
}
log.push(out);
return log;
