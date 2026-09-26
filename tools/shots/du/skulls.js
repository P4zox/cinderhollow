await boot(); G.grantTechniques(); const o = [];
G.SAVE.flags['cut:pharaoh'] = 1; G.SAVE.flags['cutp2:pharaoh'] = 1;
G.tp('DU8', 24, 14); G.step(5); const b = G.boss; b.activate(); G.step(200);
const park = () => { b.x = b.R; b.setS('idle', 'idle'); b.cool = 99; b.state = 'idle'; };
async function run(pat, policy, label) {
  G.P.x = 30 * 16 + 8; G.P.y = b.floor; G.P.hp = G.D.maxHp; G.P.inv = 0; park(); G.du.skulls(pat);
  let hits = 0, last = G.P.hp, snapped = 0, minTel = 9;
  for (let i = 0; i < 360; i++) {
    b.cool = 99; if (b.state !== 'idle') park();
    const tap = policy ? policy(i) : [];
    if (tap.includes('jump')) o.jh = 22;
    const hold = (tap.includes('right') ? ['right'] : tap.includes('left') ? ['left'] : []).concat(o.jh > 0 ? ['jump'] : []);
    G.step(1, hold, tap.filter(t => t === 'roll' || (t === 'jump' && G.P.ground))); o.jh = (o.jh || 0) - 1;
    if (G.P.hp < last) hits++; G.P.hp = G.D.maxHp; last = G.P.hp;
    for (const s of G.du.DU.blasters) minTel = Math.min(minTel, s.tel);
    if (!snapped && G.du.DU.blasters.some(s => s.t > 0.3 + s.tel + 0.1)) { snapped = 1; await snap('sk_' + label); }
    if (i > 30 && !G.du.DU.blasters.length) break;
  }
  o.push(`${label}: hits=${hits} minTelegraph=${minTel}`);
}
await run('cross', null, 'cross_stand');
await run('cross', i => i > 20 && i < 60 ? ['left'] : [], 'cross_move');
await run('volley', null, 'volley_stand');
// jump each low beam as it fires: beams are low on even indices; jump when a low beam is about to fire
await run('volley', i => { const lows = G.du.DU.blasters.filter(s => s.low && s.t > 0.3 + s.tel - 0.12 && s.t < 0.3 + s.tel - 0.05); return lows.length ? ['jump'] : []; }, 'volley_jump');
await run('rain', null, 'rain_stand');
await run('rain', i => i > 10 && i < 110 ? ['left'] : [], 'rain_run');
b.hp = b.maxHp * 0.45; G.step(80); for (let i = 0; i < 30 && G.state === 'cut'; i++) G.step(20); G.step(60);
await run('sweep', null, 'sweep_stand');
await run('sweep', i => { const s = G.du.DU.blasters[0]; if (!s || s.t < 0.3 + s.tel) return []; const m = { x: s.x, y: s.y }; const bx = m.x + Math.tan(Math.PI / 2 - s.ang) * (b.floor - m.y); return Math.abs(bx - G.P.x) < 70 && G.P.state !== 'roll' ? ['roll', bx < G.P.x ? 'left' : 'right'] : []; }, 'sweep_roll');
await run('crossrain', null, 'crossrain_stand');
// the storm: walls + lightning over 12 s
let walls = 0, bolts = 0, hits = 0, last = G.P.hp; park();
for (let i = 0; i < 720; i++) { b.cool = 99; if (b.state !== 'idle') park(); G.step(1); const S = G.du.DU.storm; if (S) { walls = Math.max(walls, S.walls.length); } if (G.P.hp < last) hits++; G.P.hp = G.D.maxHp; last = G.P.hp; if (i === 300) await snap('storm_mid'); if (S && S.walls.some(w => w.warn <= 0 && Math.abs(w.x - G.P.x) < 100) && !o.wallSnap) { o.wallSnap = 1; await snap('storm_wall'); } }
o.push('storm: maxWalls=' + walls + ' hits=' + hits + ' k=' + G.du.DU.storm.k.toFixed(2));
return o;
