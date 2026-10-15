// v14 Dual Blades: every new route starts from real inputs (press / hold / timing), plus the v14 rule changes.
// run: SHOT_HTML=web/dist/v14_dual.html sh tools/shots/wm/run.sh tools/shots/v14/dual/routes.js tools/shots/v14/dual/out
const R = [];
const T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const st = () => G.P.state;
const setup = (rank = 1, far = 24) => { W().reset('dual', rank); arena(); W().reset('dual', rank); E('D.maxSt = 300; P.st = 300; P.lastHit = null; P.inv = 0'); W().dummy(far); E('window.__wm.follow = ' + far); };
// play a script: 'J' 'K' 'I' 'L' tap, 'hK<ms>' hold K, 'w<n>' wait n frames, 'demon' / 'arch' set state, 'jump', 'up+J', 'right'
function play(seq) {
  const seen = [];
  const rec = () => { const s = st(); if (seen[seen.length - 1] !== s) seen.push(s); };
  for (const a of seq) {
    if (a === 'demon') { E('P.demon = true'); continue; }
    if (a === 'arch') { E('P.demon = true; P.arch = true; P.gauge = 1'); continue; }
    if (a[0] === 'w') { for (let i = 0; i < +a.slice(1); i++) { W().frame(1); rec(); } continue; }
    if (a.startsWith('hK')) { W().down('heavy'); for (let i = 0; i < Math.round(+a.slice(2) / 16.67); i++) { W().frame(1); rec(); } W().up('heavy'); continue; }
    const key = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll', jump: 'jump' }[a];
    if (a === 'up+J') { W().down('up'); W().tap('attack'); W().up('up'); rec(); continue; }
    W().tap(key); rec();
  }
  for (let i = 0; i < 90; i++) { W().frame(1); rec(); }
  return seen;
}
const hitsOf = id => W().log.filter(h => h.st === id && h.melee).map(h => +(h.dmg / h.light).toFixed(2));
// wait until the current move has ended (the chain is free) -- for the "pause" routes
const untilFree = (max = 60) => { for (let i = 0; i < max && !['idle', 'run', 'land'].includes(st()); i++) W().frame(1); };

// 1) J J (pause) J -> fang barrage (rank I): a press 110-450 ms after the 2nd slash ends
for (const pauseF of [8, 14, 24]) {   // 133, 233, 400 ms
  setup(); W().tap('attack'); W().frame(8); W().tap('attack'); for (let i = 0; i < 40 && st() !== 'tw_2'; i++) W().frame(1); untilFree(); W().frame(pauseF);
  const s = play(['J', 'w30', 'J']);
  T(`J J (pause ${Math.round(pauseF * 16.7)} ms) J -> fang barrage -> J -> spin`, s.includes('tw_barrage') && s.includes('tw_4') && hitsOf('tw_barrage').length === 5, s.join(' ') + ' | ' + hitsOf('tw_barrage').join('/'));
}
setup(); W().tap('attack'); W().frame(8); W().tap('attack'); for (let i = 0; i < 40 && st() !== 'tw_2'; i++) W().frame(1); untilFree(); W().frame(2);
{ const s = play(['J']); T('J J J without a pause is still the rising cross (tw_3)', s.includes('tw_3') && !s.includes('tw_barrage'), s.join(' ')); }
setup(); { const s = play(['J', 'w13', 'J', 'w13', 'J', 'w13', 'J']); T('a steady J J J J rhythm (every 0.23 s) stays on the chain', s.join(' ').includes('tw_1 tw_2 tw_3 tw_4') && !s.includes('tw_barrage'), s.join(' ')); }

// 2) J J J K -> skyward fangs: you rise; J -> twin spin; J -> crossfall to the floor
setup(); let peakY = 1e9; const y0 = E('P.y');
{
  const seen = [];
  const rec = () => { const s = st(); if (seen[seen.length - 1] !== s) seen.push(s); peakY = Math.min(peakY, E('P.y')); };
  for (const a of ['J', 'w13', 'J', 'w13', 'J', 'w13', 'K', 'w20', 'J', 'w14', 'J']) { if (a[0] === 'w') { for (let i = 0; i < +a.slice(1); i++) { W().frame(1); rec(); } } else { W().tap(a === 'J' ? 'attack' : 'heavy'); rec(); } }
  for (let i = 0; i < 60; i++) { W().frame(1); rec(); }
  T('J J J K -> skyward fangs (rises ~50 px) -> J twin spin -> J crossfall, lands', seen.includes('tw_skyward') && seen.includes('tw_air') && seen.includes('tw_crossfall') && E('P.ground') && y0 - peakY > 30,
    seen.join(' ') + ` | rise ${Math.round(y0 - peakY)} px | sky ${hitsOf('tw_skyward').join('/')} cross ${hitsOf('tw_crossfall').join('/')}`);
}
// 3) air J J from a plain jump -> crossfall; the 3rd air attack is refused (air limit 2)
setup(); W().down('jump'); W().frame(10); W().up('jump'); { const s = play(['J', 'w10', 'J']); T('jump, J J -> twin spin -> crossfall (lands planted)', s.includes('tw_air') && s.includes('tw_crossfall') && E('P.ground'), s.join(' ') + ' | ' + hitsOf('tw_crossfall').join('/')); }

// 4) Demon J x6 -> K -> rending cyclone (rank II); rank I: K after the 6th is the demon flurry
for (const rank of [1, 2]) {
  setup(rank); E('P.demon = true');
  const s = play(['J', 'w11', 'J', 'w11', 'J', 'w11', 'J', 'w20', 'J', 'w11', 'J', 'w8', 'K']);
  if (rank === 2) T('R2 Demon J x6 -> K -> rending cyclone', s.includes('tw_d6') && s.includes('tw_dfin') && hitsOf('tw_dfin').length === 4, s.join(' ') + ' | ' + hitsOf('tw_dfin').join('/'));
  else T('R1 Demon J x6 -> K: no rending cyclone below II (the early K is dropped: d6 is a finisher)', s.includes('tw_d6') && !s.includes('tw_dfin'), s.join(' '));
}
// 5) L -> K -> reversal cut (rank III); perfect dodge -> K = silver reversal x1.5; rank I: L -> K = the lunge
setup(3); { const s = play(['L', 'w12', 'K']); T('R3 L -> K -> reversal cut', s.includes('tw_reversal') && hitsOf('tw_reversal').length === 2, s.join(' ') + ' | ' + hitsOf('tw_reversal').join('/')); }
setup(1); { const s = play(['L', 'w12', 'K']); T('R1 L -> K is the lunge (no reversal below III)', s.includes('tw_heavy') && !s.includes('tw_reversal'), s.join(' ')); }
setup(3); W().tap('roll'); W().frame(3); E(`hurtPlayer(20, -1, 'rv1', { src: enemies.find(e => e.wmDummy) })`);
{ const pd = E('P.dg && P.dg.perfect'); W().tap('heavy'); W().frame(2); const s0 = st(); W().frame(40); const h = hitsOf('tw_reversal');
  T('R3 L (perfect) -> K -> silver reversal at once, x1.5', pd && s0 === 'tw_reversal' && h.length === 2 && Math.abs(h[0] - 0.675) < 0.06, `${pd} ${s0} ${h.join('/')}`); }
setup(3); E('P.demon = true'); { const s = play(['L', 'w4', 'K']); T('R3 demon dash -> K (not perfect) is the demon flurry', s.includes('tw_dflurry') && !s.includes('tw_reversal'), s.join(' ')); }

// 6) I mid-chain toggles Demon Mode when the move ends
setup(); { const s = play(['J', 'w6', 'I']); T('J then I mid-swing: Demon Mode on as the swing ends', s.includes('tw_demon') && E('P.demon'), s.join(' ')); }
// 7) counter flurry still instant; dash slash still continues the chain
setup(); W().tap('roll'); W().frame(3); E(`hurtPlayer(20, -1, 'cf1', { src: enemies.find(e => e.wmDummy) })`); W().tap('attack'); W().frame(2);
T('L (perfect) -> J = counter flurry, at once', st() === 'tw_cflurry', st());
setup(); { const s = play(['L', 'w16', 'J', 'w8', 'J']); T('L -> J dash slash -> J -> tw_2', s.includes('tw_dashslash') && s.includes('tw_2'), s.join(' ')); }

// ---- v14 rule changes
// demon chain damage
setup(); E('P.demon = true'); play(['J', 'w11', 'J', 'w11', 'J', 'w11', 'J', 'w20', 'J', 'w11', 'J']);
T('demon chain 5/6: 2 x 0.35 / 3 x 0.3', hitsOf('tw_d5').join('/') === '0.35/0.35' && hitsOf('tw_d6').join('/') === '0.3/0.3/0.3', hitsOf('tw_d5').join('/') + ' ' + hitsOf('tw_d6').join('/'));
// half-cost attacks in Demon Mode
setup(); E('P.demon = true; P.st = 200'); W().tap('attack'); W().frame(2); const dc = 200 - E('P.st');
T('Demon Mode: tw_1 costs 4 (half of 8) + the drain', dc > 3.9 && dc < 4.6, dc.toFixed(2));
// dash-through: no i-frames of its own
setup(2); E('P.demon = true'); W().tap('roll'); W().frame(3); W().tap('attack'); W().frame(10);
{ const s0 = st(); const inv = E('mvIframes()'); T('R2 dash-through cut: no i-frames during the cut', s0 === 'tw_dthrough' && !inv, `${s0} inv ${inv}`); }
// blade dance armour 0.2
T('Blade Dance armour is 0.2 of max HP', E('ATK.tw_dance.mv.armor') === 0.2 && E('ATK.tw_dance2.mv.armor') === 0.2);
// the perfect-dodge window is a full 100 ms (6 frames) and not 7
for (const [f, want] of [[5, true], [6, false]]) {
  setup(); W().tap('roll'); W().frame(f); E(`hurtPlayer(20, -1, 'win${f}', { src: enemies.find(e => e.wmDummy) })`);
  const el = E('P.dg ? Math.round(P.dg.t) : -1'), pd = !!E('P.dg && P.dg.perfect');
  T(`roll, blow ${el} ms in: perfect = ${want}`, pd === want, `${el} ms ${pd}`);
}
// anti-farm: body contact; a ticking mist (id_n); a multi-window attack (one refund); fresh attacks refund again
setup(); W().tap('roll'); W().frame(2); E(`hurtPlayer(10, -1, 'c' + 77 + 3)`);
T('bumping into a foe (contact damage) is not a perfect dodge', !E('P.dg.perfect'));
setup(); E('P.st = 100'); let gains = 0, rolls = 0;
for (let i = 0; i < 4; i++) { W().tap('roll'); W().frame(2); const s0 = E('P.st'); E(`hurtPlayer(10, -1, 'mist9_' + ${i})`); gains += E('P.st') - s0 > 20 ? 1 : 0; rolls += E('P.dg && P.dg.t < 60') ? 1 : 0; W().frame(60); }   // (the slow-motion stretches a perfect roll)
T('a ticking mist (mist_<tick>) gives one perfect dodge, not one per roll', gains === 1 && rolls === 4, 'refunds ' + gains + ' fresh rolls ' + rolls);
setup(); E('P.st = 100; enemies.find(e => e.wmDummy).atkId = 501');
let refunds = 0, perf = 0;
for (let wi = 0; wi < 3; wi++) { W().tap('roll'); W().frame(2); const s0 = E('P.st'); E(`hurtPlayer(10, -1, 5010 + ${wi}, { src: enemies.find(e => e.wmDummy) })`); perf += E('P.dg && P.dg.perfect') ? 1 : 0; refunds += E('P.st') - s0 > 20 ? 1 : 0; W().frame(60); }
E('enemies.find(e => e.wmDummy).atkId = 502; P.inv = 0'); W().tap('roll'); W().frame(2); { const s0 = E('P.st'); E(`hurtPlayer(10, -1, 5020, { src: enemies.find(e => e.wmDummy) })`); refunds += E('P.st') - s0 > 20 ? 1 : 0; }
T('a 3-window attack: 3 perfect dodges (counter each), 1 stamina refund; the next attack refunds again', perf === 3 && refunds === 2, `perfect ${perf} refunds ${refunds}`);
// a projectile flying in (no src): roll k frames before it arrives
{
  const row = [];
  for (let k = 0; k <= 8; k++) {
    setup(); E('enemies = enemies.filter(e => !e.wmDummy); MV.pd = 0; P.face = 1');
    // an arrow 60 px ahead flying back at 240 px/s reaches the hurtbox in ~13 frames
    E(`projectiles.push({ owner: 'enemy', kind: 'arrow', x: P.x + 64, y: P.y - 14, vx: -240, vy: 0, dmg: 10, life: 2.5, r: 3, t: 0, id: ++hazardId })`);
    let hitF = -1;
    for (let f = 0; f < 30; f++) { if (f === 13 - k) W().tap('roll'); else W().frame(1); if (hitF < 0 && E('MV.pd') > 0) hitF = f; }
    row.push(k + (E('MV.pd') > 0 ? 'P' : '-'));
  }
  T('projectile: a roll just before an arrow arrives is perfect', row.filter(x => x.endsWith('P')).length >= 3, row.join(' '));
}
// Archfiend (V): the dash trail is an embellishment: 0.15 per 0.4 s, gone after 1 s
setup(5, 30); E('P.demon = true; window.__wm.follow = 0'); W().tap('roll'); W().frame(8); W().tap('roll'); W().frame(4); W().log = []; W().frame(150);
{ const tr = W().log.filter(h => h.st !== 'tw_dthrough').map(h => +(h.dmg / h.light).toFixed(2)); const sum = tr.reduce((a, b) => a + b, 0);
  T('R5 archfiend trail: a few 0.15 ticks, <= 0.5 total from two dashes', tr.length >= 1 && tr.every(x => x <= 0.17) && sum <= 0.5, tr.join('/')); }
return R;
