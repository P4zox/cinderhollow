// a whole fight, start to finish, by the roll-on-telegraph bot (player HP topped up): no stuck states, all moves seen
await boot(); G.give({ stats: { vig: 30, mnd: 15, end: 25, str: 30, dex: 18, fth: 10, arc: 8 } });
G.SAVE.flags['cut:kalden'] = 1; delete G.SAVE.flags['cutp2:kalden']; delete G.SAVE.flags['boss:kalden'];
G.tp('M5', 6, 10); const b = G.boss;
const seen = {}, states = {}; let t = 0, rollAt = -1, stuck = 0, lastSig = '', maxStuck = 0, guardHits = 0;
const saw = new WeakSet();
for (let i = 0; i < 30 * 60 * 6 && b.alive; i++) {
  t += 1 / 30;
  if (G.state === 'cut' || G.state === 'cine') { G.step(2, [], i % 20 === 0 ? ['pause'] : []); continue; }
  for (const f of window.__kd.fx) if (!saw.has(f)) { saw.add(f); if (f.name === 'telegraph' && rollAt < 0) rollAt = t + 0.2; }
  const d = Math.abs(b.x - G.P.x), to = b.x < G.P.x ? 'left' : 'right';
  let hold = [], tap = [];
  if (rollAt >= 0 && t >= rollAt) { tap = ['roll']; rollAt = -1; }
  else if (d > 44) hold = [to];
  else if (b.state !== 'attack' && G.P.st > 25) tap = [Math.random() < 0.2 ? 'heavy' : 'attack'];
  G.step(2, hold, tap);
  if (b.state === 'attack') seen[b.atk] = (seen[b.atk] || 0) + 1;
  states[b.state] = (states[b.state] || 0) + 1;
  if (b.state === 'guard') guardHits++;
  const sig = `${b.state}:${b.atk}:${b.anim.i}:${Math.round(b.x)}`;
  if (sig === lastSig) { stuck++; maxStuck = Math.max(maxStuck, stuck); } else stuck = 0; lastSig = sig;
  if (G.P.hp < 150) G.P.hp = G.D.maxHp;
  if (G.P.state === 'dead') { G.P.hp = G.D.maxHp; }
  if (i % 900 === 0) await snap('fight_' + i);
}
await new Promise(r => setTimeout(r, 11000)); G.step(2);
return { secs: Math.round(t), alive: b.alive, phase: b.phase, hp: Math.round(b.hp), maxStuckFrames: maxStuck, states, moves: Object.keys(seen).sort().join(' '), flag: !!G.SAVE.flags['boss:kalden'], weapon: G.SAVE.weapons.kalden !== undefined, staggers: b.staggers || 0 };
