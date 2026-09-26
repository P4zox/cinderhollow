await boot(); G.give({ items: { talon: 1, hook: 1 } });
G.tp('TV5', 16, 9); G.step(20);
const tr = []; let hooks = 0, rel = 0;
G.step(1, ['left'], ['hook']); hooks++;
for (let i = 0; i < 700; i++) {
  const P = G.P; G.enemies.length = 0; G.P.hp = 999;
  if (P.state === 'hook') {
    const hold = [P.vx < 0 ? 'left' : 'right'];
    if (P.hook && !P.hook.zip && P.x < P.hook.h.x - P.hook.len * 0.55 && P.vy < 0) { G.step(1, ['left'], ['jump']); rel++; tr.push(['rel', Math.round(P.x), Math.round(P.y)]); continue; }
    G.step(1, hold); continue;
  }
  if (!P.ground && P.vy > 0 && hooks < 4 && P.x < 15 * 16) { G.step(1, ['left'], ['hook']); if (G.P.state === 'hook') { hooks++; tr.push(['hook', Math.round(G.P.x), Math.round(G.P.y)]); } continue; }
  G.step(1, ['left']);
  if (G.SAVE.flags['item:TV5:0']) break;
  if (P.ground && P.y > 11 * 16) break;
}
tr.push(G.step(1).p);
await snap('hook_end');
return { tr, hooks, rel, got: !!G.SAVE.flags['item:TV5:0'] };
