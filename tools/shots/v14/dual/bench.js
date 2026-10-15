// v14 Dual Blades bench (a copy of tools/shots/wm/bench.js limited to the dual rows, plus the v14 routes and a Demon boss run).
// run: SHOT_HTML=web/dist/v14_dual.html sh tools/shots/wm/run.sh tools/shots/v14/dual/bench.js tools/shots/v14/dual/out
// dmg/s per route vs the table (WEAPON_REVAMP.md A2-A10, A12), modelled on tools/shots/wb/bench_real.js.
// 1) "table" bench: each route looped for ROUTE_SECS against a target that never moves, infinite stamina, no hitstop
//    from the target: total damage / AR / time -- the number the tables quote (Dmg/s = route damage / route time).
// 2) "boss" bench: Gravetusk held in place swings every 2 s (a 1.3 s opening, then a roll through the swing), real
//    stamina, real hitstop; each type's main combo. Reported as dmg/s in AR units (x1 = one Longsword light per second).
const SECS = (typeof ROUTE_SECS !== 'undefined' && ROUTE_SECS) || (window.__wmSecs || 12), BSECS = (typeof BOSS_SECS !== 'undefined' && BOSS_SECS) || 30;
// pattern: buttons pressed in order whenever nothing is queued; {b: 'K', hold: ms} holds K; 'demon' etc. set state first
const ROUTES_ALL = [
  ['longsword', 1, 'J J J J', ['J', 'J', 'J', 'J'], 2.81],
  ['longsword', 1, 'J J K', ['J', 'J', 'K'], 2.68],
  ['longsword', 1, 'J J J K', ['J', 'J', 'J', 'K'], 2.69],
  ['katana', 1, 'J J J', ['J', 'J', 'J'], 2.50],
  ['katana', 1, 'K -> K loop', ['K'], 3.16],
  ['greatsword', 1, 'J J J', ['J', 'J', 'J'], 1.97],
  ['greatsword', 1, 'lv3 -> strong lv3', [{ b: 'K', hold: 1200 }, { b: 'K', hold: 1660 }], 2.31, { note: 'table: 8.1 over 3.5 s (1.2 s holds; the 2nd hold starts inside the 1st release)' }],
  ['maul', 1, 'J J J', ['J', 'J', 'J'], 2.07],
  ['maul', 1, 'double smash (lv2) loop', [{ b: 'K', hold: 600 }], 2.67, { idleOnly: true, exclHold: true, note: 'table: 2.4 per 0.9 s release; the hold time is left out as in the table' }],
  ['sns', 1, 'J J J J', ['J', 'J', 'J', 'J'], 2.56],
  ['sns', 2, 'perfect rush J J K', ['J', 'J', 'K'], 3.36, { perfect: true }],
  ['dual', 1, 'J J J J', ['J', 'J', 'J', 'J'], 2.82],
  ['dual', 1, 'Demon J x6', ['J', 'J', 'J', 'J', 'J', 'J'], 3.4, { pre: 'P.demon = true' }],
  ['dual', 1, 'Demon J x6 + perfect-dodge buff', ['J', 'J', 'J', 'J', 'J', 'J'], 3.7, { pre: 'P.demon = true', keep: 'P.pdT = 6' }],
  ['spear', 1, 'J J J', ['J', 'J', 'J'], 2.67, { far: 44 }],
  ['staff', 1, 'J J J J', ['J', 'J', 'J', 'J'], 2.41],
  ['whip', 1, 'J J J untipped', ['J', 'J', 'J'], 1.90, { far: 22 }],
  ['whip', 1, 'J J J tipped', ['J', 'J', 'J'], 2.24, { far: 70 }],
  ['whip', 1, 'tipped K loop', ['K'], 2.68, { far: 70, keep: 'P.crack = 0', note: 'thunderclaps kept out (the table leaves them out)' }],
  ['whip', 1, 'tipped K loop + thunderclaps', ['K'], 2.68, { far: 70 }],
];
const ROUTES = ROUTES_ALL.filter(r => r[0] === 'dual');
const out = { table: [], boss: [] };
if (window.__wmNoBoss) var NOBOSS = true;
for (const [type, rank, name, pat, want, o = {}] of ROUTES) {
  W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6'); if (o.pre) E(o.pre);
  W().dummy(o.far || 26); E('window.__wm.follow = ' + (o.far || 26));
  let i = 0, holdLeft = 0, f = 0, t0 = null, heldMs = 0;
  const N = Math.round(SECS * 60);
  for (; f < N + 600; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6; if (P.x > 330) P.x -= 200' + (o.keep ? '; ' + o.keep : ''));   // stay inside the chamber (the target follows)
    const busy = E('!!ATK[P.state] && !!P.mvQ'), free = o.idleOnly ? E("['idle','run','land'].includes(P.state)") : E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    if (holdLeft === 0 && free && !busy) {
      const p = pat[i % pat.length];
      // perfect timing: press in the last 120 ms of the move
      if (o.perfect && E('!!ATK[P.state]') && E('ATK[P.state].mv.total - P.mvT') > 120) { W().frame(1); continue; }
      if (typeof p === 'string') { W().down({ J: 'attack', K: 'heavy' }[p]); W().frame(1); W().up({ J: 'attack', K: 'heavy' }[p]); }
      else { W().down('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); if (o.exclHold && t0 !== null) heldMs += p.hold; W().frame(1); }
      i++;
      if (t0 === null) { t0 = W().ms; W().log = []; }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0 - heldMs) / 1000, L = G.D.light;
  const dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg, 0) / L;
  const dps = dmg / secs;
  const tally = {}; for (const h of W().log.filter(h => h.melee)) tally[h.st] = (tally[h.st] || 0) + 1;
  out.table.push({ type, rank, route: name, measured: +dps.toFixed(2), table: want, diff: Math.round((dps / want - 1) * 100) + '%', note: o.note || '', hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
// ---- v14 routes, scripted (press / wait frames), looped for SECS: dmg/s = all damage / all time (pauses and rolls included)
// tokens: 'J' / 'K' / 'L' press; 'q' wait until the move in progress can take the next press (as a player chaining
// would); 'e' wait until it has ended (idle / run / land); a number waits that many frames (the "pause")
const SCRIPTED = [
  ['J J J J  (reference, same driver)', 1, '', ['J', 'q', 'J', 'q', 'J', 'q', 'J', 'e']],
  ['J J (pause) J J  (barrage -> spin)', 1, '', ['J', 'q', 'J', 'e', 10, 'J', 'q', 'J', 'e']],
  ['J J J K J J  (skyward -> twin spin -> crossfall)', 1, '', ['J', 'q', 'J', 'q', 'J', 'q', 'K', 'q', 'J', 'q', 'J', 'e']],
  ['Demon J x6 (reference, same driver)', 1, 'P.demon = true', ['J', 'q', 'J', 'q', 'J', 'q', 'J', 'q', 'J', 'q', 'J', 'e']],
  ['Demon J x6 -> K  (rending cyclone, II)', 2, 'P.demon = true', ['J', 'q', 'J', 'q', 'J', 'q', 'J', 'q', 'J', 'q', 'J', 'q', 'K', 'e']],
  ['L -> K loop  (reversal cut, III)', 3, '', ['L', 12, 'K', 'e']],
  ['L -> K loop  (rank I: roll -> lunge)', 1, '', ['L', 12, 'K', 'e']],
  ['L (perfect) -> J loop  (counter flurry)', 1, '', ['L', 3, 'pd', 'J', 'e']],
  ['L (perfect) -> K loop  (silver reversal, III)', 3, '', ['L', 3, 'pd', 'K', 'e']],
  // v14c
  ['K J J J  (lunge -> spiral pursuit -> rising cross -> spin)', 1, '', ['K', 'q', 'J', 'q', 'J', 'q', 'J', 'e']],
  ['K K  (lunge -> fang pounce)', 1, '', ['K', 'q', 'K', 'e']],
  ['J J K J J  (hooking cross -> rising cross -> spin)', 1, '', ['J', 'q', 'J', 'q', 'K', 'q', 'J', 'q', 'J', 'e']],
  ['Demon K J J J K  (flurry -> bloodwheel -> chain 5, 6 -> cyclone, II)', 2, 'P.demon = true', ['K', 'q', 'J', 'q', 'J', 'q', 'J', 'q', 'K', 'e']],
  ['Demon K loop (reference)', 1, 'P.demon = true', ['K', 'e']],
];
out.scripted = [];
for (const [name, rank, pre, seq] of SCRIPTED) {
  W().reset('dual', rank); arena(); W().reset('dual', rank); E('D.maxSt = 1e6; P.st = 1e6'); if (pre) E(pre);
  W().dummy(26); E('window.__wm.follow = 26'); W().log = [];
  const keep = () => E('P.st = 1e6; P.inv = 0; slowmo = 0; if (P.x > 330) P.x -= 200' + (pre ? '; ' + pre : ''));
  const step = () => { W().frame(1); keep(); };
  const t0 = W().ms; let n = 0;
  while (W().ms - t0 < SECS * 1000) {
    for (const a of seq) {
      if (typeof a === 'number') { for (let i = 0; i < a; i++) step(); }
      else if (a === 'q') { for (let i = 0; i < 90 && !E("['idle','run','land','air'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && P.mvT < ATK[P.state].mv.total)"); i++) step(); }
      else if (a === 'e') { for (let i = 0; i < 120 && !E("['idle','run','land'].includes(P.state)"); i++) step(); }
      else if (a === 'pd') E(`hurtPlayer(1, -1, 'bpd' + (++window.__wm.ms), { src: enemies.find(e => e.wmDummy) })`);
      else W().tap({ J: 'attack', K: 'heavy', L: 'roll' }[a]);
    }
    n++;
  }
  const secs = (W().ms - t0) / 1000, dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg, 0) / G.D.light;
  const tally = {}; for (const h of W().log.filter(h => h.melee)) tally[h.st] = (tally[h.st] || 0) + 1;
  out.scripted.push({ route: name, rank, dps: +(dmg / secs).toFixed(2), loops: n, hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
// ---- the boss bench (bench_real.js rules)
E(`(() => { if (window.__wmB) return; window.__wmB = 1; })()`);
for (const [type, demonBoss] of [['dual', false], ['dual', true]]) {
  W().reset(type, 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset(type, 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  const bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  let sum = 0; const oh = b.hit; b.hit = function (info) { if (info.melee) sum += info.dmg / (info.fire && G.D.W.fire && info.kind === 'heavy' ? 1 + G.D.W.fire : 1); return oh.call(this, info); };
  const px = bx - 34; G.P.x = px; G.P.face = 1;
  const pat = { longsword: 'JJJJ', katana: 'JJJ', greatsword: 'JJJ', maul: 'JJJ', sns: 'JJJJ', dual: 'JJJJ', spear: 'JJJ', staff: 'JJJJ', whip: 'JJJ' }[type];
  let swings = 0, demonT = 0, exh = 0;
  for (let f = 0; f < 60 * BSECS; f++) {
    const c = f % 120;
    const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40)");
    const cost = E(`ATK[MOVESETS[mvType()].combo[0]].cost`);
    if (demonBoss && free && !E('P.demon') && E('P.exhT') <= 0 && G.P.st > G.D.maxSt * 0.8 && c < 60) { W().tap('parry'); continue; }   // re-enter Demon Mode once the bar is back
    if (demonBoss && E('P.demon')) demonT++; if (demonBoss && E('P.exhT > 1.45')) exh++;
    if (c < 78 && free && G.P.st > cost + 1 && G.P.state !== 'roll') { W().tap('attack'); swings++; continue; }
    if (c === 102) E("hitstop = 0; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) mvDodgeStart(0); }");
    W().frame(1); G.P.hp = G.D.maxHp;
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  b.hit = oh;
  out.boss.push({ type: type + (demonBoss ? ' (Demon Mode when the bar is 80%+)' : ''), combo: pat, dps: +(sum / G.D.light / BSECS).toFixed(2), presses: swings, demonSecs: +(demonT / 60).toFixed(1), exhausted: exh });
}
return out;
