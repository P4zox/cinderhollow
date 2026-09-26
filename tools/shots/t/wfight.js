await boot(); G.give({ items: { talon: 1 } }); G.SAVE.flags['cut:warden'] = 1;
G.tp('TV8', 12, 10); G.step(5);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) G.step(2, ['right']);
const b = G.boss, moves = { p1: {}, p2: {} }, states = new Set(); let lastMove = null, t1 = 0, t2 = 0, hits = 0, last = G.P.hp, minX = 1e9, maxX = -1e9, stuck = 0, lastX = b.x, k = 0;
for (let i = 0; i < 60 * 150; i++) {
  const P = G.P, d = b.x - P.x, hold = [], tap = [];
  if (Math.abs(d) > 60) hold.push(d > 0 ? 'right' : 'left');
  if (i % 24 === 0 && Math.abs(d) < 110) tap.push('attack');
  if (i % 97 === 0) tap.push('roll');
  G.step(1, hold, tap);
  if (G.state === 'cut') G.step(1, [], ['pause']);
  if (G.P.hp < last) hits++; G.P.hp = 999; last = 999;
  if (b.move !== lastMove && b.move) { const ph = b.form === 'stag' ? 'p2' : 'p1'; moves[ph][b.move] = (moves[ph][b.move] || 0) + 1; lastMove = b.move; }
  if (b.form === 'stag') t2++; else t1++;
  states.add(b.form + ':' + b.state); minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x);
  if (!b.alive) break;
  if (i === 60 * 40) b.hp = Math.min(b.hp, b.maxHp * 0.52);
  if (i % 900 === 450) await snap('wf_' + (k++));
}
return { moves, secs: [Math.round(t1 / 60), Math.round(t2 / 60)], hits, hp: b.hp, form: b.form, states: [...states].join(' '), x: [minX / 16, maxX / 16] };
