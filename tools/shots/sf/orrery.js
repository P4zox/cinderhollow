await boot();
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 }, stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10 } });
const out = { moves: {} };
G.tp('SF5', 5, 12); S(10);
for (let i = 0; i < 120 && G.state !== 'cut'; i++) S(2, ['right']);
for (let i = 0; i < 8 && G.state === 'cut'; i++) { S(25); await snap('o0_cut' + i); }
for (let i = 0; i < 50 && G.state === 'cut'; i++) S(1, [], ['pause']);
const b = G.boss; let shot = 0, dmg = 0;
for (let i = 0; i < 1400; i++) {
  const d = Math.abs(b.x - G.P.x), to = b.x < G.P.x ? 'left' : 'right';
  let hold = [], tap = [];
  if (d > 30) hold = [to]; else if (G.P.st > 25 && i % 6 === 0) tap = ['attack'];
  if (i % 40 === 0) tap = ['jump'];
  const h0 = G.P.hp; S(2, hold, tap); if (G.P.hp < h0) dmg += h0 - G.P.hp;
  G.P.hp = Math.max(G.P.hp, 200);
  const k = b.state; out.moves[k] = (out.moves[k] || 0) + 1;
  if (i % 70 === 0 && shot < 16) await snap('o1_' + String(shot++).padStart(2, '0'));
  if (i === 600) b.hp = Math.round(b.maxHp * 0.45);
  if (G.state === 'cut') { for (let j = 0; j < 60 && G.state === 'cut'; j++) S(1, [], ['pause']); }
  if (!b.alive) break;
}
out.final = { hp: b.hp, phase: b.phase, state: b.state, x: Math.round(b.x), y: Math.round(b.y), dmgTaken: Math.round(dmg) };
b.hp = 1; b.hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: b.x, y: b.y - 50, melee: true });
S(200); await snap('o2_dead'); S(400);
out.after = { items: Object.keys(G.SAVE.items), weapons: Object.keys(G.SAVE.weapons), shards: G.SAVE.shards, flag: G.SAVE.flags['boss:orrery'], fog: G.props.filter(p => p.type === 'fog' && p.on()).length };
return out;
