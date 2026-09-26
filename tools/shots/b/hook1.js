await boot();
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1 };
const out = [];
const S = () => [G.room, Math.round(G.P.x), Math.round(G.P.y), G.P.state];
const rings = [424, 312, 200];
let attempts = [];
for (let tr = 0; tr < 4; tr++) {
  G.tp('DB2', 31, 9); G.step(10);
  let ri = 0, log = [];
  G.step(8, ['left']); G.step(1, ['left'], ['jump']);
  for (let i = 0; i < 600; i++) {
    const p = G.P;
    if (p.state === 'hook') {
      const h = p.hook; const past = p.x < h.h.x - 30 - tr * 6 && p.vx < 60;
      if (!h.zip && past) { G.step(1, ['left'], ['jump']); ri++; log.push(['rel', Math.round(p.x), Math.round(p.y)]); continue; }
      G.step(1, ['left']); continue;
    }
    if (ri < 3 && !p.ground && Math.abs(p.x - rings[ri]) < 110 && p.x > rings[ri] - 30 && p.state !== 'swim') { G.step(1, ['left'], ['hook']); if (G.P.state === 'hook') log.push(['hook', ri, Math.round(p.x), Math.round(p.y)]); continue; }
    G.step(1, ['left']);
    if (p.ground && p.x < 112) break;
    if (p.state === 'swim' && i > 30) { log.push(['fell', Math.round(p.x)]); break; }
  }
  attempts.push([tr, S(), log]);
  if (G.P.x < 112 && G.P.ground) break;
}
out.push(attempts);
await snap('h_end');
return out;
