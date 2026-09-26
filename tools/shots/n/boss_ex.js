// Twin Executioners: cutscene once, fight, hits land, duo techniques, one dies (roar/enrage), death, rewards, fog lifts.
await boot(); G.give({ stats: { vig: 60, mnd: 30, end: 40, str: 40, dex: 40, fth: 30, arc: 10 } });
const out = [], log = {};
delete G.SAVE.flags['boss:executioners']; delete G.SAVE.flags['cut:executioners'];
G.tp('NV5', 33, 10); G.P.hp = 99999;
const b = G.boss; if (!b) return ['NO BOSS'];
let sawCut = false;
for (let i = 0; i < 200 && !b.active; i++) { G.step(4, ['left']); if (G.state === 'cut') { sawCut = true; if (i % 3 === 0) await snap('ex_cut_' + i); G.step(30); } }
for (let i = 0; i < 400 && G.state === 'cut'; i++) G.step(10);
out.push(`cutscene seen ${sawCut}, active ${b.active}, cut flag ${!!G.SAVE.flags['cut:executioners']}`);
let hurt = 0, maxX = 0, minX = 9999, shots = 0;
const L = b.L, R = b.R;
for (let i = 0; i < 900; i++) {
  const live = b.parts.filter(q => q.alive); const tg = live[0]; if (!tg) break;
  const d = tg.x < G.P.x ? 'left' : 'right', far = Math.abs(tg.x - G.P.x) > 50;
  const prev = G.P.hp; G.step(3, far ? [d] : [], far ? (i % 17 === 0 ? ['roll'] : []) : ['attack']);
  if (G.state === 'cut') G.step(1, [], ['pause']);
  if (G.P.hp < prev) hurt++;
  G.P.hp = 99999; G.P.inv = 0;
  for (const q of b.parts) { if (q.alive) { minX = Math.min(minX, q.x); maxX = Math.max(maxX, q.x); } const k = q.who + ':' + (q.state === 'attack' ? q.atk : q.state); log[k] = (log[k] || 0) + 1; }
  if (b.duo && shots < 2) { await snap('ex_duo_' + shots); shots++; }
  if (i === 200) await snap('ex_fight_1');
  if (i === 400) { b.parts[1].hit({ dmg: 5000, poise: 0, dir: 1, kind: 'light', x: b.parts[1].x, y: b.parts[1].y - 20, melee: true }); }
  if (i === 410) await snap('ex_enraged');
}
out.push(`hits on player ${hurt}; x range ${Math.round(minX)}..${Math.round(maxX)} within ${L}..${R}: ${minX >= L - 1 && maxX <= R + 1}`);
out.push('states ' + JSON.stringify(log));
for (let n = 0; n < 300 && b.alive; n++) { for (const t of b.parts) if (t.alive) t.hit({ dmg: 300, poise: 0, dir: 1, kind: 'light', x: t.x, y: t.y - 20, melee: true }); G.step(2); G.P.hp = 99999; }
for (let i = 0; i < 80; i++) { G.step(10); G.P.hp = 99999; if (G.state === 'cut') G.step(1, [], ['pause']); }
await snap('ex_dead');
const fogs = G.props.filter(p => p.type === 'fog').map(p => p.on());
out.push(`dead ${!b.alive} flag ${!!G.SAVE.flags['boss:executioners']} fogs on ${JSON.stringify(fogs)} weapons ${JSON.stringify(Object.keys(G.SAVE.weapons))} shards ${G.SAVE.shards}`);
// re-enter: no boss, no fog
G.tp('NV5', 20, 10); out.push(`re-enter boss ${!!G.boss} fogs ${G.props.filter(p => p.type === 'fog').length}`);
return out;
