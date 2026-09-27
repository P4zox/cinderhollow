await boot(); G.SAVE.seenAreas = { archives: 1 }; G.give({ items: { talon: 1, hook: 1 } }); G.P.hp = 999;
const S = window.__sys, RB = window.__rb, sim = RB.sim, out = []; const P = () => G.P;
G.tp('A15', 3, 28); G.step(30); sim(1, [], ['interact']); sim(20);
const moves = [[1,0,6,-1,18,0],[1,10,6,-1,12,10],[1,30,6,-1,18,10],[1,0,6,-1,2,0],[1,30,6,-1,12,0]];
for (const [dir, pre, hold, dash, hookAt, rel] of moves) {
  if (P().hook) { if (pre) sim(pre, ['right']); if (rel) sim(rel); sim(1, ['right', 'jump'], ['jump']); } else { sim(1, ['right', 'jump'], ['jump']); }
  for (let f = 1; f < 160; f++) { sim(1, f < hold ? ['right', 'jump'] : ['right'], f === hookAt ? ['hook'] : []); if (P().hook && !P().hook.zip) break; }
  out.push(`hooked ${(P().hook.h.x-8)/16},${(P().hook.h.y-8)/16} P ${(P().x/16).toFixed(1)},${(P().y/16).toFixed(1)} len ${P().hook.len.toFixed(0)}`);
}
G.step(1); await snap('a15_hang');
for (let f = 0; f < 60; f++) { sim(1, ['right']); if (f % 4 === 0) out.push(`pump ${f} P ${(P().x/16).toFixed(1)},${(P().y/16).toFixed(1)} av ${P().hook.av.toFixed(2)} ang ${P().hook.ang.toFixed(2)}`); }
sim(1, ['right', 'jump'], ['jump']);
for (let f = 0; f < 50; f++) { sim(1, f < 10 ? ['right', 'jump'] : ['right']); if (f % 3 === 0) out.push(`rel ${f} ${P().state} P ${(P().x/16).toFixed(1)},${(P().y/16).toFixed(1)} vx ${Math.round(P().vx)} vy ${Math.round(P().vy)}`); }
return out;
