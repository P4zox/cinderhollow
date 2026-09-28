await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, catacombs: 1 };
G.give({ items: { talon: 1 } });
const W = window.__walker, RB = window.__rb, out = [];
const r = W.route(['M1', 10, 24], ['W3', 'M7', 'M8'], { budget: 300 });
out.push(...r.log);
const S = RB.snap(); out.push(`in: ${G.room} ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state} vy ${Math.round(G.P.vy)} g ${G.P.ground}`);
const cs = [{ k: 'J', d: 1, run: 0, h: 20, dash: -1 }, { k: 'W', d: 1, n: 16 }, { k: 'DROP', d: 1 }, { k: 'DROP', d: 0 }, { k: 'WAIT', n: 90 }];
for (const c of cs) {
  RB.restore(S); RB.clearFoes(); const q = W.play({ ...c }); out.push(`${JSON.stringify(c)} -> ${JSON.stringify(q)} ${G.room} ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state} g ${G.P.ground}`);
  if (!q.changed) for (const c2 of [{ k: 'DROP', d: 1 }, { k: 'DROP', d: 0 }]) { const st = RB.snap(); const q2 = W.play({ ...c2 }); out.push(`    then ${JSON.stringify(c2)} -> ${JSON.stringify(q2)} ${G.room} ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state}`); RB.restore(st); }
}
return out;
