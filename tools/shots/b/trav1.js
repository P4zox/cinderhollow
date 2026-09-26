await boot();
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1, cathedral: 1 };
const out = [];
const S = () => [G.room, Math.round(G.P.x), Math.round(G.P.y), G.P.state];
// 1. K2 grate: stand on it, drop through
G.tp('K2', 39, 10); G.step(20); out.push(['on grate', S()]); await snap('t00_grate');
G.step(2, ['down'], ['jump']); G.step(120); out.push(['dropped', S()]); await snap('t01_db1');
// 2. climb back out: wall-jump up the chimney
G.tp('DB1', 4, 5); G.step(10); out.push(['rung', S()]);
let best = 999;
G.step(1, [], ['jump']);
for (let i = 0; i < 300; i++) {
  const p = G.P;
  if (p.state === 'wall') { G.step(1, [], ['jump']); continue; }
  const lx = G.room === 'K2' ? p.x - 624 : p.x - 48; const toward = lx < 16 ? 'left' : 'right';
  G.step(1, p.vy > 0 ? [toward] : ['jump']);
  if (p.ground && p.state !== 'wall' && i > 20) G.step(1, [], ['jump']);
  if (G.room === 'K2' && G.P.ground && G.P.y <= 177) { best = i; break; }
}
G.step(40); out.push(['climbed', S(), best]); await snap('t02_back');
return out;
