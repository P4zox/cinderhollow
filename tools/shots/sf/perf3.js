await boot(); window.__godS = true;
G.giveArmory(); G.give({ stats: { vig: 40, mnd: 30, end: 40, str: 30, dex: 25, fth: 20 } });
G.SAVE.skills.push('charged_arts');
G.SAVE.flags['cut:astrel'] = 1; G.SAVE.flags['cutp2:astrel'] = 1; G.SAVE.flags['cutp3:astrel'] = 1;
const key = (code, down) => window.dispatchEvent(new KeyboardEvent(down ? 'keydown' : 'keyup', { code }));
// time spent inside every rAF callback (the game's frame)
const cb = []; const raf0 = window.requestAnimationFrame.bind(window);
window.requestAnimationFrame = f => raf0(t => { const a = performance.now(); f(t); cb.push([performance.now() - a, window.__sfDbg ? window.__sfDbg.particles() : -1, G.boss && G.boss.state, G.P.state]); });
await new Promise(r => setTimeout(r, 300));
const out = {};
for (const [label, wid, ph] of [['p1_gs', 'greatsword', 1], ['p1_star', 'starblade', 1], ['p2_gs', 'greatsword', 2], ['p2_ls', 'longsword', 2]]) {
  G.SAVE.weapon = wid; delete G.SAVE.flags['boss:astrel'];
  G.tp('SF7', 26, 16); S(3); const b = G.boss;
  for (let i = 0; i < 100 && !b.active; i++) S(2, ['right']);
  if (ph === 2) { b.hp = b.maxHp * 0.45; }
  cb.length = 0;
  const t0 = performance.now();
  while (performance.now() - t0 < 12000) {
    G.P.hp = G.D.maxHp; G.P.st = G.D.maxSt;
    // walk into her and charge heavies
    const dir = b.x > G.P.x ? 'KeyD' : 'KeyA'; key(dir, true); await new Promise(r => setTimeout(r, 120)); key(dir, false);
    key('KeyK', true); await new Promise(r => setTimeout(r, 900)); key('KeyK', false);
    await new Promise(r => setTimeout(r, 300));
  }
  const ts = cb.map(c => c[0]).sort((a, b) => a - b);
  const worst = cb.slice().sort((a, b) => b[0] - a[0]).slice(0, 3).map(c => c.map(v => typeof v === 'number' ? +v.toFixed(1) : v).join('/'));
  out[label] = { n: ts.length, med: +ts[ts.length >> 1].toFixed(2), p95: +ts[Math.floor(ts.length * .95)].toFixed(2), max: +ts[ts.length - 1].toFixed(1), worst, hp: Math.round(b.hp) };
}
return out;
