await boot();
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 }, stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10 } });
const out = { states: {}, moves: {}, errs: [] };
G.tp('SF7', 5, 16); S(10);
await snap('a00_enter');
for (let i = 0; i < 120 && G.state !== 'cut'; i++) S(2, ['right']);
out.cut = G.state;
// watch the cutscene
for (let i = 0; i < 12; i++) { S(20); if (G.state !== 'cut') break; if (i % 2 === 0) await snap('a01_cut' + i); }
for (let i = 0; i < 50 && G.state === 'cut'; i++) S(1, [], ['pause']);
S(30);
const b = G.boss; out.active = b && b.active;
// fight: bot swings when close, rolls on telegraphs sometimes; god-ish hp
let shot = 0;
for (let i = 0; i < 1500; i++) {
  const d = Math.abs(b.x - G.P.x), to = b.x < G.P.x ? 'left' : 'right';
  let hold = [], tap = [];
  if (d > 44) hold = [to]; else if (G.P.st > 25 && i % 8 === 0) tap = ['attack'];
  if (i % 97 === 0) tap = ['jump'];
  S(2, hold, tap);
  G.P.hp = Math.max(G.P.hp, 150); if (G.P.state === 'dead') break;
  out.states[b.state] = (out.states[b.state] || 0) + 1;
  const k = b.state === 'attack' ? b.atk : b.state === 'cast' ? 'cast:' + b.castKind : b.state; out.moves[k] = (out.moves[k] || 0) + 1;
  if (i % 60 === 0 && shot < 14) await snap('a1_fight' + String(shot++).padStart(2, '0'));
  if (i === 500) { b.hp = Math.round(b.maxHp * 0.45); }
  if (G.state === 'cut') { await snap('a2_p2cut'); for (let j = 0; j < 60 && G.state === 'cut'; j++) S(1, [], ['pause']); }
  if (i === 1000) b.hp = Math.round(b.maxHp * 0.18);
  if (b.state === 'nova' && !out.novaShot) { out.novaShot = 1; S(90); await snap('a3_nova1'); S(200); await snap('a3_nova2'); }
}
out.final = { hp: b.hp, phase: b.phase, state: b.state, cons: b.cons, php: Math.round(G.P.hp) };
return out;
