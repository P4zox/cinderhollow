await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { archives: 1 }; G.give({ items: { talon: 1 } });
const W = window.__walker, RB = window.__rb, out = [];
const pos = () => `${G.room} ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state}`;
G.tp('A5', 25, 6); RB.sim(20); out.push('start ' + pos());
for (const c of [{ k: 'J', d: 1, run: 0, h: 20, dash: -1 }, { k: 'J', d: 1, run: 0, h: 20, dash: -1 }, { k: 'J', d: 0, run: 0, h: 20, dash: -1 }, { k: 'J', d: 0, run: 0, h: 20, dash: -1 }]) {
  const r = W.play({ ...c }); out.push(JSON.stringify(c) + ' -> ' + JSON.stringify(r) + ' ' + pos());
}
G.tp('A5', 32, 1); RB.sim(20); out.push('on top ledge: ' + pos());
const r = W.play({ k: 'J', d: 0, run: 0, h: 20, dash: -1 }); out.push('jump -> ' + JSON.stringify(r) + ' ' + pos());
return out;
