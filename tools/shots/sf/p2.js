await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1 }, stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10 } });
G.SAVE.flags['cut:astrel'] = 1;
G.tp('SF7', 12, 16); S(10);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) S(2, ['right']);
const b = G.boss; S(120); await snap('p2_00_before');
b.hp = Math.round(b.maxHp * 0.49); b.state = 'idle'; S(3);
for (let i = 0; i < 12; i++) { S(8); await snap('p2_01_scene' + String(i).padStart(2, '0')); if (G.state !== 'cut') break; }
for (let i = 0; i < 60 && G.state === 'cut'; i++) S(1, [], ['pause']);
for (let i = 0; i < 6; i++) { S(25); await snap('p2_02_reveal' + i); }
const out = { pats: [] };
for (const m of ['barrage', 'march', 'pincer', 'ring', 'great']) {
  b.state = 'idle'; b.cool = 99; b.lastMet = null; S(1);
  const r0 = Math.random; let picked = null;
  // force the pattern
  b.metT = 99; const w0 = b.meteorPattern; Math.random = () => 0; 
  const orig = b.lastMet; b.lastMet = null;
  Math.random = r0;
  // call directly with a stubbed choice
  const saved = Object.getPrototypeOf(b).meteorPattern;
  b.meteorPattern = function () { const rr = Math.random; const order = ['barrage', 'march', 'pincer', 'ring', 'great']; let n = 0; Math.random = () => { n++; return n === 1 ? (order.indexOf(m) + 0.5) / 5 * 0.999 : rr(); }; try { saved.call(this); } finally { Math.random = rr; } };
  b.meteorPattern(); out.pats.push(b.lastMet); delete b.meteorPattern;
  S(40); await snap('p2_03_' + m + '_a'); S(40); await snap('p2_03_' + m + '_b'); S(60);
}
b.state = 'idle'; b.start('flurry'); S(12); await snap('p2_04_flurry'); S(20); await snap('p2_04_flurry2'); S(40);
b.state = 'idle'; b.start('wave'); S(30); await snap('p2_05_wave'); S(30); await snap('p2_05_wave2');
return out;
