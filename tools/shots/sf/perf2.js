await boot(); window.__godS = true;
G.giveArmory(); G.give({ stats: { vig: 40, mnd: 30, end: 40, str: 30, dex: 25, fth: 20 } });
G.SAVE.flags['cut:astrel'] = 1;
const out = {};
const key = (code, down) => window.dispatchEvent(new KeyboardEvent(down ? 'keydown' : 'keyup', { code }));
const measure = async (label, wid, ms, pattern) => {
  G.SAVE.weapon = wid; delete G.SAVE.flags['boss:astrel'];
  G.tp('SF7', 26, 16); S(3); const b = G.boss;
  for (let i = 0; i < 100 && !b.active; i++) S(2, ['right']);
  const iv = []; let last = performance.now(), run = true, maxP = 0;
  let frozen = 0, slow = 0, maxHs = 0, maxSm = 0; const loop = t => { iv.push(t - last); last = t; const d = window.__sfDbg; if (d.hs() > 0) frozen++; if (d.sm() > 0) slow++; maxHs = Math.max(maxHs, d.hs()); maxSm = Math.max(maxSm, d.sm()); maxP = Math.max(maxP, window.__sfDbg.particles()); if (run) requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  const t0 = performance.now();
  while (performance.now() - t0 < ms) {
    G.P.hp = G.D.maxHp;
    const tt = performance.now() - t0;
    await pattern(tt);
  }
  run = false; key('KeyK', false); key('KeyJ', false);
  iv.sort((a, b) => a - b);
  out[label] = { frames: iv.length, med: +iv[iv.length >> 1].toFixed(1), p95: +iv[Math.floor(iv.length * 0.95)].toFixed(1), max: +iv[iv.length - 1].toFixed(1), maxP, frozen, slow, maxHs: +maxHs.toFixed(2), maxSm: +maxSm.toFixed(2), bossHp: Math.round(b.hp), bstate: b.state };
};
const heavySpam = async tt => { key('KeyK', true); await new Promise(r => setTimeout(r, 650)); key('KeyK', false); await new Promise(r => setTimeout(r, 250)); };
await measure('light_ls', 'longsword', 6000, async () => { key('KeyJ', true); await new Promise(r => setTimeout(r, 60)); key('KeyJ', false); await new Promise(r => setTimeout(r, 200)); });
await measure('heavy_ls', 'longsword', 6000, heavySpam);
await measure('heavy_gs', 'greatsword', 6000, heavySpam);
await measure('heavy_star', 'starblade', 6000, heavySpam);
return out;
