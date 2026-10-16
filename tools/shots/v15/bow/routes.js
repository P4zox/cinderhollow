// v15 bow: every move from real inputs, the levels, the sweet spot, rank gates, mashing, turning
// (tools/shots/wm/run.sh: the WM prelude gives W(), E, arena()).
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
arena();
const go = (r = 1, dx = 44) => {
  W().reset('bow', r); E('P.x = 160; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.bwLv = 1; P.bwIdle = 0; P.bwSteps = 0; P.bwDived = false; BW.log = []; BW.arrows = []; projectiles.length = 0');
  W().frame(2); if (dx !== null) W().dummy(dx); E('BW.log = []');
};
const L = () => E('BW.log');
const sumOf = (id) => L().filter(h => !id || h.id === id).reduce((a, h) => a + h.dmg, 0);
const f2 = x => (+x).toFixed(2);
const hold = (b, n) => { W().down(b); W().frame(n); W().up(b); };
const states = n => { const s = []; for (let i = 0; i < n; i++) { W().frame(1); const st = E('P.state'); if (s[s.length - 1] !== st) s.push(st); } return s; };

// ---- J J J J: levels 1, 2, 3 then the pinning shot
go(1, 44);
let seen = [];
for (let i = 0; i < 4; i++) { W().tap('attack', 2); for (let k = 0; k < 8; k++) { W().frame(1); const st = E('P.state'); if (seen[seen.length - 1] !== st) seen.push(st); } }
for (let k = 0; k < 100; k++) { W().frame(1); const st = E('P.state'); if (seen[seen.length - 1] !== st) seen.push(st); }
const lv = L().map(h => h.id + ':' + h.lv);
ok(seen.filter(s => s.startsWith('bw_')).join() === 'bw_1,bw_2,bw_3,bw_pin', 'J J J J plays ' + seen.join(' '));
ok(L().filter(h => h.id === 'bw_1').length === 1 && L().filter(h => h.id === 'bw_2').length === 2 && L().filter(h => h.id === 'bw_3').length === 3,
  'quick shots loose 1 / 2 / 3 arrows (levels 1, 2, 3): ' + lv.join(' '));
ok(Math.abs(sumOf() - 4.1) < 0.15, 'J J J J deals 0.4 x (1 + 2 + 3) + 1.7 = 4.1 in the sweet spot (got ' + f2(sumOf()) + ')');
ok(E('P.bwLv') === 1, 'the pinning shot spends the level (bwLv ' + E('P.bwLv') + ')');

// ---- mashing stops at the finisher
go(1, 44); seen = [];
for (let i = 0; i < 14; i++) { W().tap('attack', 2); for (let k = 0; k < 4; k++) { W().frame(1); const st = E('P.state'); if (seen[seen.length - 1] !== st) seen.push(st); } }
for (let k = 0; k < 60; k++) { W().frame(1); const st = E('P.state'); if (seen[seen.length - 1] !== st) seen.push(st); }
ok(seen.indexOf('bw_pin') > 0 && seen.slice(seen.indexOf('bw_pin') + 1).every(s => !s.startsWith('bw_')), 'mashing J ends at the pinning shot: ' + seen.join(' '));

// ---- hold K: the draw levels
for (const [ms, want, dm] of [[300, 1, 0.9], [700, 2, 1.4], [1150, 3, 2.0]]) {
  go(1, 44); hold('heavy', Math.round(ms / 16.67)); W().frame(50);
  const h = L().filter(x => x.id === 'bw_power');
  ok(h.length === 1 && h[0].lv === want && Math.abs(h[0].dmg - dm) < 0.08, `hold K ${ms} ms -> power shot lv${want} (${dm}): ` + JSON.stringify(h.map(x => [x.lv, f2(x.dmg)])));
}
go(1, 44); W().down('heavy'); W().frame(30); E('P.vx = 0'); W().down('right'); W().frame(30); const vx = E('P.vx'), stw = E('P.anim.tag'); W().up('right'); W().up('heavy'); W().frame(40);
ok(Math.abs(vx - 122 * 0.4) < 6 && stw === 'bw_drawwalk', `walking while drawn: ${f2(vx)} px/s (40% of 122), tag ${stw}`);
// turning while drawn
go(1, null); W().down('heavy'); W().frame(20); W().down('left'); W().frame(4); const fd = E('P.face'); W().up('left'); W().up('heavy'); W().frame(40);
ok(fd === -1, 'the draw turns with the stick (face ' + fd + ')');
// tap K: the banked level
go(1, 44); W().tap('heavy', 2); W().frame(50);
ok(L().length === 1 && L()[0].id === 'bw_power' && L()[0].lv === 1, 'tap K -> a level-1 power shot: ' + JSON.stringify(L().map(h => [h.id, h.lv])));
// lv3 pierces: two foes in a line both take it
go(1, 44); E(`enemies.push({ ...enemies.find(e => e.wmDummy), x: P.x + 70, wmDummy: false, hit(info) { window.__wm.log.push({ st: 'second', dmg: info.dmg, light: D.light }); } })`);
hold('heavy', 70); W().frame(50);
ok(W().log.some(l => l.st === 'second') && L().filter(h => h.id === 'bw_power').length >= 2, 'a level 3 power shot pierces through the first foe into the second');
E('enemies = enemies.filter(e => e.wmDummy)');

// ---- the sweet spot (v15b: x0.9 under 12 px, x1.0 at 12-56, easing to x0.6 at the burn-out ~86 px; nothing past it)
for (const [dx, k] of [[14, 0.9], [24, 1.0], [56, 1.0], [80, 1 - 0.4 * (80 - 8 - 56) / 30], [100, null], [190, null]]) {
  go(1, dx); W().tap('heavy', 2); W().frame(70);
  const h = L()[0];
  if (k === null) ok(!h, `foe at ${dx} px (edge ${dx - 8}): the arrow burns out before it (${h ? 'HIT x' + f2(h.k) : 'no hit'})`);
  else ok(h && Math.abs(h.k - k) < 0.03, `sweet spot: foe at ${dx} px (edge ${h ? h.d : '?'}) -> x${h ? f2(h.k) : '?'} (want ${f2(k)})`);
}
// ---- range: no arrow of any kind ever hits past the burn-out (72 px of flight, ~86 px from the archer)
{
  const far = [];
  for (const dx of [70, 84, 90, 94, 100, 110]) {
    for (const route of ['JJJJ', 'K', 'Khold', 'L J', 'air J']) {
      go(5, dx);
      if (route === 'JJJJ') { for (let i = 0; i < 4; i++) { W().tap('attack', 2); W().frame(8); } W().frame(60); }
      else if (route === 'K') { W().tap('heavy', 2); W().frame(60); }
      else if (route === 'Khold') { hold('heavy', 70); W().frame(60); }
      else if (route === 'L J') { W().down('right'); W().tap('roll', 2); W().up('right'); W().frame(10); W().tap('attack', 2); W().frame(40); }
      else { W().tap('jump', 2); W().frame(8); W().tap('attack', 2); W().frame(50); }
      for (const h of L()) far.push({ dx, route, flown: h.flown, d: h.d });
    }
  }
  const worst = far.reduce((m, h) => Math.max(m, h.flown), 0), worstD = far.reduce((m, h) => Math.max(m, h.d), 0);
  ok(far.length > 0 && worst <= 74 && worstD <= 88, `no arrow hits past the burn-out: ${far.length} hits on foes 70-110 px away, max ${worst} px of flight, max ${worstD} px from the archer`);
}
go(1, null); W().tap('heavy', 2); let burned = 0, flying = 0; for (let i = 0; i < 60 && !burned; i++) { W().frame(1); burned = E('BW.burn.length'); flying = E('BW.arrows.length'); }
ok(burned === 1 && flying === 0, `an arrow that meets nothing burns out (ash + embers), it doesn't fly on (burning ${burned}, flying ${flying})`);
// the glint
const glint = dx => { go(1, dx); W().frame(3); return E('P.bwSweet'); };
const gl = [[14, false], [22, true], [44, true], [64, true], [66, false], [90, false]].map(([dx, want]) => [dx, glint(dx), want]);
ok(gl.every(([, g, w]) => g === w), 'sweet-spot glint follows the 12-56 px band (foe at dx: on?): ' + gl.map(([dx, g]) => dx + ':' + (g ? 'on' : 'off')).join(' '));
E('render()'); await new Promise(r => setTimeout(r, 300)); E('render()');
ok(!!E('bwTip()'), 'the arrowhead is found in the overlay frame: ' + JSON.stringify(E('bwTip()')));

// ---- J -> K tap: arrow stab; -> K tap: recoil shot (hops back)
go(1, 30); W().tap('attack', 2); W().frame(6); W().tap('heavy', 2); W().frame(30);
const stab = W().log.filter(l => l.st === 'bw_stab');
ok(stab.length === 1 && Math.abs(stab[0].dmg / stab[0].light - 0.8) < 0.06 && stab[0].melee, 'J -> K tap: the arrow stab lands as a melee jab (0.8): ' + stab.map(l => f2(l.dmg / l.light)));
let x0 = E('P.x'); W().tap('heavy', 2); W().frame(50);
const rec = L().filter(h => h.id === 'bw_recoil');
ok(rec.length === 1 && Math.abs(rec[0].dmg - 1.2) < 0.08, 'stab -> K tap: the recoil shot (1.2, no point-blank cut): ' + rec.map(h => f2(h.dmg) + ' k' + h.k));
ok(x0 - E('P.x') >= 20 && x0 - E('P.x') <= 40, `the recoil shot hops you back ${f2(x0 - E('P.x'))} px`);
// J -> hold K: the draw starts at the banked level 2
go(1, 44); W().tap('attack', 2); W().frame(4); W().down('heavy'); W().frame(30); const dl = E('P.bwDrawLv'), dst = E('P.state'); W().up('heavy'); W().frame(50);
ok(dst === 'bw_draw' && dl === 2, `J -> hold K: drawing (${dst}) from the banked level ${dl}`);

// ---- L: the charge step
go(1, 44); W().tap('roll', 2); W().frame(4); const st1 = E('P.state + "/" + P.anim.tag'), l1 = E('P.bwLv'); W().frame(30);
ok(l1 === 2 && st1 === 'roll/bw_step', `L: charge step (${st1}), next shot level ${l1}`);
go(1, 44); W().tap('roll', 2); W().frame(12); W().tap('roll', 2); W().frame(30); const r1 = E('P.bwLv');
go(2, 44); W().tap('roll', 2); W().frame(12); W().tap('roll', 2); W().frame(30); const r2 = E('P.bwLv');
ok(r1 === 2 && r2 === 3, `L L: a second step stacks only at Mastery II (rank I lv${r1}, rank II lv${r2})`);
// L -> J dash shot (at the banked level 2: 1.0)
go(1, 44); W().tap('roll', 2); W().frame(10); W().tap('attack', 2); W().frame(40);
ok(L().filter(h => h.id === 'bw_dash').length === 2 && Math.abs(sumOf('bw_dash') - 1.0) < 0.06, 'L -> J: dash shot at level 2 (2 arrows, 1.0): ' + f2(sumOf('bw_dash')));
// L -> K tap: leaping point-blank (1.5, point-blank)
go(1, 30); W().tap('roll', 2); W().frame(10); W().tap('heavy', 2); W().frame(60);
ok(L().filter(h => h.id === 'bw_leap').length === 3 && Math.abs(sumOf('bw_leap') - 1.5) < 0.08, 'L -> K tap: leaping point-blank, a fan of three (1.5): ' + f2(sumOf('bw_leap')));
// L -> hold K: the draw from level 2
go(1, 44); W().tap('roll', 2); W().frame(10); W().down('heavy'); W().frame(20); const ld = E('P.state + " lv" + P.bwDrawLv'); W().up('heavy'); W().frame(40);
ok(ld === 'bw_draw lv2', 'L -> hold K: the draw starts at level 2 (' + ld + ')');

// ---- hollow piercer: lv3 power shot -> K tap (Mastery III)
for (const r of [2, 3]) {
  go(r, 44); hold('heavy', 70); W().frame(12); W().tap('heavy', 2); W().frame(90);
  const hp = L().filter(h => h.id === 'bw_hollow');
  if (r === 2) ok(hp.length === 0, 'hollow piercer is locked below Mastery III');
  else ok(hp.length === 6 && Math.abs(sumOf('bw_hollow') - 2.4) < 0.15, 'III: lv3 power shot -> K tap: hollow piercer drills 6 x 0.4 = ' + f2(sumOf('bw_hollow')));
}

// ---- up J: arc shot (5 arrows, 7 at IV) rains 40-90 px ahead
for (const r of [1, 4]) {
  go(r, 64); W().down('up'); W().tap('attack', 2); W().up('up'); W().frame(25); const n0 = E('BW.arrows.filter(p => p.bw.rain).length'); W().frame(60);
  ok(n0 === (r === 4 ? 7 : 5) && L().some(h => h.id === 'bw_arc'), `↑J arc shot (rank ${r}): ${n0} rain arrows; ${L().filter(h => h.id === 'bw_arc').length} hit a foe at 64 px`);
}

go(4, null); E('BW.stuck = []; enemies = enemies.filter(e => !e.wmDummy)'); W().down('up'); W().tap('attack', 2); W().up('up'); W().frame(92);
const land = E('BW.stuck.map(q => Math.round((q.x - P.x) * P.face))');
ok(land.length >= 7 && Math.max(...land) <= 86 && Math.min(...land) >= 24, 'arc shot rain lands 30-82 px ahead (stuck at ' + land.join(' ') + ')');

// ---- I: limb deflect -> counter shot
go(1, 30); W().tap('parry', 2); W().frame(2);
const neg = E("hurtPlayer(20, -1, 'bwtest', { parryable: true })"), cst = E('P.state'); W().frame(40);
ok(!neg && cst === 'bw_counter' && L().some(h => h.id === 'bw_counter' && Math.abs(h.dmg - 1.6) < 0.1), `I: a parryable blow in the window is turned (${neg === false}), counter shot 1.6 (${cst}; ${f2(sumOf('bw_counter'))})`);
// v15 balance: an unparryable blow is only turned aside (block-cost stamina, no counter shot)
go(1, 30); W().tap('parry', 2); W().frame(2); const stD = E('P.st'), hpD = E('P.hp');
const neg2 = E("hurtPlayer(20, -1, 'bwtest3', {})"), cst2 = E('P.state'); W().frame(4);
ok(!neg2 && E('P.hp') === hpD && cst2 !== 'bw_counter' && stD - E('P.st') > 5, `I: an unparryable blow is turned aside for stamina, no counter (${cst2}, stam -${f2(stD - E('P.st'))})`);
go(1, 30); W().tap('parry', 2); W().frame(14); const hp0 = E('P.hp'); E("hurtPlayer(20, -1, 'bwtest2', {})"); W().frame(30);
ok(E('P.hp') < hp0, 'a blow after the 150 ms window lands');

// ---- air
go(1, 40); W().tap('jump', 2); W().frame(8); W().tap('attack', 2); W().frame(40);
ok(L().some(h => h.id === 'bw_air'), 'air J: aerial shot hits a foe below-ahead: ' + f2(sumOf('bw_air')));
go(1, null); W().tap('jump', 2); W().frame(18); W().dummy(0); W().down('down'); W().tap('attack', 2); W().frame(30); W().up('down'); W().frame(40);
ok(W().log.some(l => l.st === 'bw_down'), 'air ↓J: talon stomp lands (pogo)');
go(1, 60); W().tap('jump', 2); W().frame(14); W().tap('heavy', 2); const dsts = states(80);
ok(dsts.includes('bw_dive') && dsts.includes('bw_diveshot') && L().filter(h => h.id === 'bw_diveshot').length >= 2, "air K: hunter's dive -> dive shot: " + dsts.join(' ') + ' ' + f2(sumOf('bw_diveshot')));

// ---- V: point-blank burst
for (const r of [4, 5]) {
  go(r, 14); hold('heavy', 70); W().frame(40);
  const extra = W().log.filter(l => l.kind === 'heavy' && l.st !== 'x').length;
  if (r === 4) var e4 = W().log.length; else ok(W().log.length === e4 + 1, `V: a lv3 shot inside 20 px bursts (+1 hit: rank IV ${e4} hits, rank V ${W().log.length})`);
}

// ---- level decay, turning between chain steps, lunges
go(1, 44); W().tap('roll', 2); W().frame(20); const a1 = E('P.bwLv'); W().frame(100); const a2 = E('P.bwLv');
ok(a1 === 2 && a2 === 1, `the banked level falls back after 1.5 s (${a1} -> ${a2})`);
go(1, null); W().tap('attack', 2); W().frame(4); W().down('left'); W().tap('attack', 2); W().frame(20); const tf = E('P.face + " " + P.state'); W().up('left'); W().frame(30);
ok(tf === '-1 bw_2', 'each chain step turns with the stick (' + tf + ')');
const lunges = E("Object.values(MV.defs).filter(d => d.type === 'bow' && Math.abs(d.lunge || 0) > 36).map(d => d.id)");
ok(lunges.length === 0, 'no bow move travels more than 36 px: ' + JSON.stringify(E("Object.values(MV.defs).filter(d => d.type === 'bow' && d.lunge).map(d => d.id + ':' + d.lunge)")));
ok(E("['bw_1','bw_2','bw_3','bw_pin','bw_draw','bw_drawwalk','bw_power','bw_hollow','bw_stab','bw_recoil','bw_arc','bw_step','bw_dash','bw_leap','bw_deflect','bw_counter','bw_air','bw_down','bw_dive','bw_diveshot'].every(t => pHas(t))"), 'all 20 bw_ animation tags are in the sheet');
ok(E("Object.values(MV.defs).filter(d => d.type === 'bow').every(d => pHas(d.tags[0]))"), 'every bow move plays its own tag (no fallback)');
ok(E("WEAPON_UNLOCKS.bow.length") === 4 && E("MV.types.bow.combos.every(c => c.desc.length <= 70)"), 'unlocks II-V listed; every combo desc <= 70 chars');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
