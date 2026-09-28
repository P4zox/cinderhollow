await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, catacombs: 1 };
G.give({ items: { talon: 1 } });
const W = window.__walker, RB = window.__rb, out = [];
W.route(['M1', 10, 24], ['W3', 'M7', 'M8'], { budget: 300 });
const S = RB.snap();
const replay = path => { RB.restore(S); RB.clearFoes(); for (const pr of path) { const r = W.play({ ...pr }); if (r.changed || r.dead) return r; } return {}; };
const k = () => `${G.room}:${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)}:${G.P.state}`;
replay([]); out.push('root ' + k());
const J = { k: 'J', d: 1, run: 0, h: 20, dash: -1 };
for (const c of [J, { k: 'DROP', d: 1 }]) { replay([]); const r = W.play({ ...c }); out.push('root+' + c.k + ' ' + JSON.stringify(r) + ' ' + k()); }
for (const c of [{ k: 'DROP', d: 1 }, { k: 'DROP', d: 0 }, { k: 'W', d: -1, n: 16 }]) { const r0 = replay([J]); out.push(' replay ' + JSON.stringify(r0) + ' ' + k()); const r = W.play({ ...c }); out.push('  J+' + c.k + c.d + ' ' + JSON.stringify(r) + ' ' + k()); }
return out;
