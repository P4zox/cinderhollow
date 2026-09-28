await boot(); G.SAVE.seenAreas = { hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1, emberdash: 1 } }); G.P.hp = 999;
const W = window.__walker, RB = window.__rb, out = [];
G.tp('HF15', 28, 18); RB.sim(30);
const S = RB.snap(); const h = W.hop(S, 'HF14', { budget: 300 });
RB.restore(S);
for (const pr of h.path || []) { const r = W.play({ ...pr }); out.push(`${pr.k}${pr.d ?? pr.side ?? ''} -> ${G.room} ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state} hp ${Math.round(G.P.hp)}`); }
return out;
