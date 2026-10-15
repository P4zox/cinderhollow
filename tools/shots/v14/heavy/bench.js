// v14 heavy bench (Greatsword + Maul). Run: SHOT_HTML=web/dist/v14_heavy.html sh tools/shots/wm/run.sh tools/shots/v14/heavy/bench.js
// 1) "table": each route looped for SECS on the WM dummy (follows you), infinite stamina: dmg/s in light-AR units, as
//    tools/shots/wm/bench.js (presses go in whenever nothing is queued; {hold: ms} holds K from the press, KI waits for
//    idle first). Hold time counts (the WM bench leaves the maul's lv2 hold out).
// 2) "boss": Gravetusk held in place (it doesn't attack), REAL stamina, the route pressed whenever free for BSECS:
//    dmg/s, staggers and seconds spent staggered -- the stun check (bosses get 7 s of stance immunity after a stagger).
const SECS = window.__hvSecs || 12, BSECS = window.__hvBossSecs || 40;
const K = ms => ({ hold: ms }), KI = ms => ({ hold: ms, idle: true });   // KI: wait until the last move has ended
const TABLE = [
  ['greatsword', 1, 'J J J', ['J', 'J', 'J']],
  ['greatsword', 1, 'K tap loop', ['K']],
  ['greatsword', 1, 'lv3 loop (hold 1.0 s)', [KI(1000)]],
  ['greatsword', 1, 'lv3 -> strong lv3', [KI(1200), K(1660)]],
  ['greatsword', 1, 'J -> hold K (hilt bash -> lv3)', ['J', K(1500)]],
  ['greatsword', 1, 'J J J -> K (momentum cleave)', ['J', 'J', 'J', 'K']],
  ['greatsword', 3, 'lv3 -> strong lv3 -> true lv3', [KI(1200), K(1660), K(1660)]],
  ['greatsword', 5, 'wrath loop (hold 1.6 s)', [KI(1600)]],
  ['greatsword', 1, 'v14c lv3 -> J -> J (upheaval, spin)', [KI(1000), 'J', 'J']],
  ['greatsword', 1, 'v14c J -> K -> J (turning sweep)', ['J', 'K', 'J']],
  ['greatsword', 2, 'v14c J J J -> K -> K (earthsplitter)', ['J', 'J', 'J', 'K', 'K']],
  ['maul', 1, 'J J J', ['J', 'J', 'J']],
  ['maul', 1, 'K tap loop (upswing)', ['K']],
  ['maul', 1, 'lv2 double smash loop', [KI(600)]],
  ['maul', 1, 'lv3 big smash loop', [KI(1000)]],
  ['maul', 2, 'double smash -> K (third pound)', [KI(600), 'K']],
  ['maul', 3, 'J J J -> K K K K (Big Bang)', ['J', 'J', 'J', 'K', 'K', 'K', 'K']],
  ['maul', 5, 'earthshaker loop (hold 1.5 s still)', [KI(1500)]],
  ['maul', 1, 'v14c J -> K -> J (side blow, upswing)', ['J', 'K', 'J']],
  ['maul', 2, 'v14c J -> K -> K (side blow, backswing slam)', ['J', 'K', 'K']],
  ['maul', 1, 'v14c K -> J -> J (upswing, drop, upswing)', ['K', 'J', 'J']],
];
const BOSS = [
  ['longsword', 1, 'J J J J (reference)', ['J', 'J', 'J', 'J']],
  ['greatsword', 1, 'J J J', ['J', 'J', 'J']],
  ['greatsword', 1, 'K tap', ['K']],
  ['greatsword', 1, 'lv3 loop', [KI(1000)]],
  ['greatsword', 1, 'lv3 -> strong lv3', [KI(1000), K(1300)]],
  ['greatsword', 1, 'J -> hold K (bash -> lv3)', ['J', K(1500)]],
  ['greatsword', 3, 'lv3 -> strong -> true', [KI(1000), K(1300), K(1300)]],
  ['maul', 1, 'J J J', ['J', 'J', 'J']],
  ['maul', 1, 'K tap', ['K']],
  ['maul', 1, 'lv2 loop', [KI(600)]],
  ['maul', 1, 'lv3 loop', [KI(1000)]],
  ['maul', 3, 'Big Bang', ['J', 'J', 'J', 'K', 'K', 'K', 'K']],
  ['maul', 5, 'earthshaker loop', [KI(1500)]],
];
const only = window.__hvOnly;
function press(p, st) {
  if (typeof p === 'string') { const b = { J: 'attack', K: 'heavy' }[p]; W().down(b); W().frame(1); W().up(b); return 0; }
  W().down('heavy'); W().frame(1); return Math.round(p.hold / (1000 / 60)) - 1;
}
const idleJs = "['idle','run','land'].includes(P.state)";
const freeJs = "['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)";
const out = { table: [], boss: [] };
for (const [type, rank, name, pat] of TABLE) {
  if (only && !only.includes(type)) continue;
  W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6');
  W().dummy(26); E('window.__wm.follow = 26');
  let i = 0, holdLeft = 0, t0 = null;
  for (let f = 0; f < SECS * 60 + 900; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6; if (P.x > 330) P.x -= 200');
    if (holdLeft === 0 && E(pat[i % pat.length].idle ? idleJs : freeJs)) { holdLeft = press(pat[i++ % pat.length]); if (t0 === null) { t0 = W().ms; W().log = []; } continue; }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const L = G.D.light, hits = W().log.filter(h => h.melee), dmg = hits.reduce((a, h) => a + h.dmg, 0) / L;
  const tally = {}; for (const h of hits) tally[h.st] = (tally[h.st] || 0) + 1;
  out.table.push({ type, rank, route: name, dps: +(dmg / ((W().ms - t0) / 1000)).toFixed(2), hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
for (const [type, rank, name, pat] of BOSS) {
  if (only && !only.includes(type) || window.__hvNoBoss) continue;
  W().reset(type, rank); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset(type, rank); E('enemies = enemies.filter(e => !e.wmDummy)');
  const bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7; b.staggers = 0; b.stance = 0; b.stanceImmune = 0; b.stanceMax = b.stanceBase || b.stanceMax;
  let sum = 0, stagT = 0, first = null; const oh = b.hit;
  b.hit = function (info) { if (info.melee) sum += info.dmg / (info.fire && G.D.W.fire && info.kind === 'heavy' ? 1 + G.D.W.fire : 1); return oh.call(this, info); };
  const px = bx - 34; G.P.x = px; G.P.face = 1;
  let i = 0, holdLeft = 0;
  for (let f = 0; f < 60 * BSECS; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    if (holdLeft === 0 && G.P.st > 20 && E(pat[i % pat.length].idle ? idleJs : freeJs)) holdLeft = press(pat[i++ % pat.length]);
    else W().frame(1);
    if (b.state === 'stagger') { stagT += 1 / 60; if (first === null) first = f / 60; }
    G.P.hp = G.D.maxHp;
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  W().up('heavy'); b.hit = oh;
  out.boss.push({ type, rank, route: name, dps: +(sum / G.D.light / BSECS).toFixed(2), staggers: b.staggers, stagSecs: +stagT.toFixed(1), firstStagger: first && +first.toFixed(1) });
}
return out;
