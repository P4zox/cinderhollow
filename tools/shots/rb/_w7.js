await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1 } });
const W = window.__walker, RB = window.__rb, out = [];
G.tp('HF8', 5, 54); RB.sim(30); out.push(`start ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state}`);
let S = RB.snap(), pre = [];
for (const g of [{ x: 2, y: 43 }, { x: 2, y: 37 }, { x: 8, y: 35 }, { x: 9, y: 32 }, { x: 8, y: 28 }, { x: 6, y: 25 }, { x: 6, y: 19 }, { x: 2, y: 16 }, { x: 6, y: 13 }, { x: 15, y: 13 }, { x: 28, y: 10 }, { x: 24, y: 7 }, { x: 35, y: 4 }]) {
  const t0 = performance.now(); const h = W.hop(S, g, { budget: 200, prefix: pre, ms: 120000 });
  out.push(`${JSON.stringify(g)}: ${h.fail ? 'FAIL exp ' + h.exp + ' seen ' + h.seen : h.path.length + ' progs ' + h.exp + ' exp'} ${Math.round(performance.now() - t0)} ms`);
  if (h.fail) break; pre = [...pre, ...h.path];
}
return out;
