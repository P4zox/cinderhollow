await boot();
const D = window.__db; window.__dbLog = [];
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.flags['cut:choir'] = 1; G.SAVE.seenAreas = { barrows: 1 };
const out = [];
const run = (n) => { for (let i = 0; i < n; i++) { G.step(20); G.P.hp = G.D.maxHp; if (G.state !== 'play') break; } };
G.tp('DB6', 19, 10); G.step(5);
run(60 * 3 / 1);
const tally = {}; for (const h of window.__dbLog) tally[h[1]] = (tally[h[1]] || 0) + 1;
out.push(['platform-stander hits over 60s', window.__dbLog.length, tally]);
// dodging player: rolls whenever something is close
window.__dbLog = [];
for (let i = 0; i < 180; i++) {
  const b = D.choir(); const c = b.headC(); const near = Math.hypot(c.x - G.P.x, c.y - G.P.y) < 80 || (D.DBW.wails||[]).some(w => Math.abs(Math.hypot(G.P.x - w.x, G.P.y - 13 - w.y) - w.r) < 30);
  G.step(20, [], near ? ['roll'] : []); G.P.hp = G.D.maxHp;
}
const t2 = {}; for (const h of window.__dbLog) t2[h[1]] = (t2[h[1]] || 0) + 1;
out.push(['roller hits over 60s', window.__dbLog.length, t2]);
return out;
