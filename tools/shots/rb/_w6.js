await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { archives: 1 }; G.give({ items: { talon: 1 } });
const W = window.__walker, RB = window.__rb, out = [];
const pos = () => `${G.room} ${(G.P.x/16).toFixed(2)},${(G.P.y/16).toFixed(2)} ${G.P.state} g${G.P.ground}`;
G.tp('A16', 2, 8); RB.sim(30); out.push('start ' + pos());
for (let i = 0; i < 40; i++) { RB.sim(1, ['left']); if (i % 4 === 0) out.push(i + ' ' + pos()); }
G.tp('A9', 45, 6); RB.sim(30); out.push('A9 gallery ' + pos());
for (let i = 0; i < 30; i++) { RB.sim(1, ['right']); if (i % 4 === 0) out.push(i + ' ' + pos()); }
out.push('brk ' + [4,5,6].map(y => G.SAVE.flags[`brk:A9:47,${y}`]).join());
return out;
