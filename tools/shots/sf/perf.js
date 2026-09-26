await boot(); window.__godS = true;
G.giveArmory(); G.give({ stats: { vig: 30, mnd: 30, end: 30, str: 30, dex: 25, fth: 20 } });
G.SAVE.flags['cut:astrel'] = 1; G.SAVE.flags['cutp2:astrel'] = 1; G.SAVE.flags['cutp3:astrel'] = 1;
const out = {}; const cv = [...document.querySelectorAll('canvas')].sort((a,b)=>b.width*b.height-a.width*a.height)[0]; const cx2 = cv.getContext('2d');
async function trial(label, wid, act, passive = true) {
  G.SAVE.weapon = wid; G.SAVE.weapons[wid] = G.SAVE.weapons[wid] || 0;
  delete G.SAVE.flags['boss:astrel'];
  G.tp('SF7', 20, 16); S(5);
  const b = G.boss; for (let i = 0; i < 100 && !b.active; i++) S(2, ['right']);
  S(60);
  const times = []; let maxP = 0, maxFx = 0, maxH = 0;
  for (let i = 0; i < 360; i++) {
    if (passive) b.cool = Math.max(b.cool, 0.5);   // keep her mostly passive so we measure *our* hits
    G.P.x = b.x - 26 * (b.face || 1); G.P.face = b.x > G.P.x ? 1 : -1;
    const t0 = performance.now();
    act(i); cx2.getImageData(0, 0, 1, 1);
    times.push(performance.now() - t0);
    maxP = Math.max(maxP, window.__sfDbg.particles()); out.gh = Math.max(out.gh || 0, b.ghosts.length); if (times[times.length-1] > 30 && !out['slow_' + label]) out['slow_' + label] = [i, b.state, b.atk, G.P.state, times[times.length-1].toFixed(1)]; maxFx = Math.max(maxFx, window.__sfDbg.fx()); maxH = Math.max(maxH, window.__sfDbg.hazards());
  }
  times.sort((a, b) => a - b);
  out[label] = { med: +times[180].toFixed(2), p95: +times[342].toFixed(2), max: +times[359].toFixed(2), maxP, maxFx, maxH, hp: b.hp };
}
await trial('light', 'longsword', i => S(1, [], i % 12 === 0 ? ['attack'] : []));
await trial('heavy', 'longsword', i => S(1, i % 50 < 40 ? ['heavy'] : [], i % 50 === 0 ? ['heavy'] : []));
await trial('heavyGS', 'greatsword', i => S(1, i % 60 < 45 ? ['heavy'] : [], i % 60 === 0 ? ['heavy'] : []));
await trial('heavyMaul', 'maul', i => S(1, i % 60 < 45 ? ['heavy'] : [], i % 60 === 0 ? ['heavy'] : []));
await trial('heavyStar', 'starblade', i => S(1, i % 50 < 40 ? ['heavy'] : [], i % 50 === 0 ? ['heavy'] : []));
await trial('art', 'longsword', i => { G.P.fp = 999; S(1, [], i % 40 === 0 ? ['art'] : []); });
await trial('spell', 'longsword', i => { G.P.fp = 999; S(1, [], i % 40 === 0 ? ['cast'] : []); });
for (const [lab, w] of [['live_heavy', 'longsword'], ['live_heavyGS', 'greatsword'], ['live_heavyStar', 'starblade'], ['live_kalden', 'kalden']]) await trial(lab, w, i => S(1, i % 50 < 40 ? ['heavy'] : [], i % 50 === 0 ? ['heavy'] : []), false);
for (const k of ['p2', 'p3']) { await trial('live_' + k, 'greatsword', i => { if (i === 0) { G.boss.hp = G.boss.maxHp * (k === 'p2' ? 0.45 : 0.19); } S(1, i % 50 < 40 ? ['heavy'] : [], i % 50 === 0 ? ['heavy'] : []); }, false); }
return out;
