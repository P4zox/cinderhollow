await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1 } });
const W = window.__walker, RB = window.__rb, out = [];
const pos = () => `${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state}`;
G.tp('HF8', 6, 19); RB.sim(30); out.push('start ' + pos());
const S = RB.snap();
for (const c of [{ k: 'J', d: -1, run: 0, h: 20, dash: -1 }, { k: 'J', d: -1, run: 0, h: 5, dash: -1 }, { k: 'J', d: 0, run: 0, h: 20, dash: -1 }, { k: 'J', d: -1, run: 0, h: 20, dash: -1, sw: 14, post: 0 }]) {
  RB.restore(S); const t0 = performance.now(); const r = W.play({ ...c }); out.push(JSON.stringify(c) + ' -> ' + JSON.stringify(r) + ' ' + pos() + ' ' + Math.round(performance.now() - t0) + 'ms');
}
return out;
