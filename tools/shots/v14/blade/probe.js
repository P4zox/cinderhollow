// v14 blade probe: real-input measurements for the Longsword and Katana critique (travel per move, input windows,
// hold/tap latencies, exploit checks). Run: SHOT_HTML=web/dist/v14_blade.html sh tools/shots/wm/run.sh tools/shots/v14/blade/probe.js <out>
const res = {};
const P = () => G.P, st = () => G.P.state;
const keyOf = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' };
let hid = 0;
const hurt = (dmg, o = {}) => E(`(() => { const d = enemies.find(e => e.wmDummy); return hurtPlayer(${dmg}, ${o.dir ?? -1}, 'pb${++hid}', { src: d, parryable: ${!!o.parryable} }); })()`);
const setup = (type, rank = 1, far = 26) => { W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6; P.lastHit = null'); if (far) W().dummy(far); };
// run a script, recording for each ATTACK state the x travelled while in it (summed per state visit)
// ops: J K I L (taps of 1 frame), w<n> wait, hK<ms> / hJ<ms> hold, R+ / R- hold / release forward (right), sheathed, E:<js>
function run(script, { keepX = false } = {}) {
  const w = W(); const visits = []; let cur = null;
  const tick = () => {
    const s = st(), x = P().x;
    if (!cur || cur.s !== s) { if (cur) cur.dx = Math.round(x - cur.x0); cur = { s, x0: x, dx: 0 }; visits.push(cur); }
    if (!keepX && W().follow) {}
  };
  const fr = n => { for (let i = 0; i < n; i++) { w.frame(1); tick(); } };
  for (const s of script) {
    if (keyOf[s]) { w.down(keyOf[s]); fr(1); w.up(keyOf[s]); }
    else if (s[0] === 'w') fr(+s.slice(1));
    else if (s.startsWith('hK')) { w.down('heavy'); fr(Math.round(+s.slice(2) / (1000 / 60))); w.up('heavy'); }
    else if (s.startsWith('hJ')) { w.down('attack'); fr(Math.round(+s.slice(2) / (1000 / 60))); w.up('attack'); }
    else if (s.startsWith('dK')) w.down('heavy');
    else if (s.startsWith('uK')) w.up('heavy');
    else if (s === 'R+') w.down('right');
    else if (s === 'R-') w.up('right');
    else if (s === 'L+') w.down('left');
    else if (s === 'L-') w.up('left');
    else if (s === 'jump') { w.down('jump'); fr(6); w.up('jump'); }
    else if (s === 'sheathed') E('P.sheathed = true');
    else if (s.startsWith('E:')) E(s.slice(2));
  }
  fr(90);
  if (cur) cur.dx = Math.round(P().x - cur.x0);
  w.up('right'); w.up('left');
  return visits.filter(v => !['idle', 'run', 'land', 'air'].includes(v.s)).map(v => v.s + ':' + v.dx).join(' ');
}
// ---- 1) travel per move (px), standing still vs holding forward the whole time; no target in range (dummy far away)
const LS = {
  attack4: ['J', 'w12', 'J', 'w14', 'J', 'w24', 'J'],
  heavy: ['K'], ls_kc: ['hK750'], ls_jjk: ['J', 'w12', 'J', 'w14', 'K'], ls_jjjk: ['J', 'w12', 'J', 'w14', 'J', 'w24', 'K'],
  ls_pommel: ['J', 'w12', 'J', 'w14', 'J', 'w26', 'hK300'], ls_jk: ['J', 'w12', 'K'], ls_rollk: ['L', 'w14', 'K'],
  ls_wheel: ['J', 'w12', 'J', 'w20', 'w10', 'J'], ls_riposte: ['E:P.gcT = 0.6; P.parried = true', 'J'],
  ls_quick: ['L', 'w16', 'J'], ls_step: ['R+', 'L', 'w2', 'J'], ls_fore_cut: ['I', 'w3', 'K', 'w4', 'E:hurtPlayer(30, -1, "fc", {})'],
};
res.travel_ls = {};
for (const [id, sc] of Object.entries(LS)) {
  setup('longsword', 5, 400); const still = run(sc);
  setup('longsword', 5, 400); const fwd = run(['R+', ...sc]);
  res.travel_ls[id] = { still, fwd };
}
const KT = {
  kt_1: ['J'], kt_3: ['J', 'w6', 'J', 'w6', 'J'], kt_rush: ['K'], kt_iai: ['sheathed', 'K'], kt_focus: ['sheathed', 'hK600'],
  kt_iaicut: ['sheathed', 'I', 'w3', 'E:hurtPlayer(30, -1, "kc", {})'], kt_draw: ['sheathed', 'J'], kt_jjk: ['J', 'w14', 'J', 'w14', 'K'],
  kt_tsubame: ['sheathed', 'K', 'w14', 'J'], kt_turn: ['sheathed', 'hK600', 'w6', 'K'], kt_stepcut: ['L', 'w8', 'J'], kt_flash: ['sheathed', 'L'],
};
res.travel_kt = {};
for (const [id, sc] of Object.entries(KT)) {
  setup('katana', 5, 400); const still = run(sc);
  setup('katana', 5, 400); const fwd = run(['R+', ...sc]);
  res.travel_kt[id] = { still, fwd };
}
// ---- 2) pommel (J J J -> hold K): K pressed at frame f after attack3 starts, held for h ms
res.pommel = {};
for (const f of [3, 10, 18, 24, 30]) for (const h of [100, 160, 250]) {
  setup('longsword', 4, 26); W().tap('attack'); W().frame(6); W().tap('attack'); W().frame(14); W().tap('attack');
  for (let i = 0; i < 60 && st() !== 'attack3'; i++) W().frame(1);
  W().frame(f); W().down('heavy'); const seen = []; for (let i = 0; i < Math.round(h / 16.67); i++) { W().frame(1); if (seen[seen.length - 1] !== st()) seen.push(st()); }
  W().up('heavy'); for (let i = 0; i < 60; i++) { W().frame(1); if (seen[seen.length - 1] !== st()) seen.push(st()); }
  res.pommel[`at${f}f_hold${h}`] = seen.join('>');
}
// ---- 3) foresight (I -> K): K pressed n frames after I
res.foresight = {};
for (const n of [0, 2, 6, 10, 15, 20, 30]) {
  setup('longsword', 3, 26); W().tap('parry'); W().frame(n); W().tap('heavy'); W().frame(3); res.foresight['gap' + n + 'f'] = st();
}
// ---- 4) ember edge: 4th J pressed at attack3's mvT = t ms; did the burning follow-up land?
res.ember = {};
for (const t of [150, 220, 260, 280, 320, 380, 410, 440, 480]) {
  setup('longsword', 5, 26); E('window.__wm.follow = 26');
  W().tap('attack'); W().frame(6); W().tap('attack'); W().frame(14); W().tap('attack');
  for (let i = 0; i < 60 && st() !== 'attack3'; i++) W().frame(1);
  for (let k = 0; k < 80 && st() === 'attack3' && E('P.mvT') < t; k++) W().frame(1);
  if (t > 420) W().frame(Math.round((t - 420) / 16.67));
  W().tap('attack'); W().frame(70);
  const a4 = W().log.filter(h => h.st === 'attack4').length; res.ember['t' + t] = a4 === 2 ? 'EMBER' : a4 === 1 ? 'plain' : 'none';
}
// ---- 5) katana: sheathed K tap latency (press -> hit), by tap length
res.iai_latency = {};
for (const tapF of [1, 4, 6, 9]) {
  setup('katana', 1, 30); E('P.sheathed = true; window.__wm.log = []'); const t0 = W().ms; W().down('heavy'); W().frame(tapF); W().up('heavy');
  for (let i = 0; i < 60 && !W().log.length; i++) W().frame(1);
  res.iai_latency['tap' + tapF + 'f'] = W().log.length ? Math.round(W().log[0].t - t0) + 'ms ' + W().log[0].st : 'no hit';
}
// ---- 6) katana: mashing I while sheathed -- how much of the time is a blow negated? stamina spent?
{
  setup('katana', 1, 26); E('P.sheathed = true; D.maxSt = 100; P.st = 100');
  let neg = 0, n = 0; const st0 = E('P.st');
  for (let i = 0; i < 120; i++) { if (i % 6 === 0) W().tap('parry'); else W().frame(1); if (i % 10 === 5) { n++; const hp = P().hp; E('P.lastHit = null; P.inv = 0'); hurt(1); if (P().hp === hp) neg++; E('P.hp = D.maxHp'); } }
  res.iai_parry_mash = { negated: neg + '/' + n, stamSpent: Math.round(st0 - E('P.st')), state: st() };
}
// ---- 7) foresight mash: I K I K ... how much is negated
{
  setup('longsword', 3, 26); E('D.maxSt = 100; P.st = 100');
  let neg = 0, n = 0; const st0 = E('P.st');
  for (let i = 0; i < 120; i++) { if (i % 30 === 0) W().tap('parry'); else if (i % 30 === 3) W().tap('heavy'); else W().frame(1); if (i % 10 === 5) { n++; const hp = P().hp; E('P.lastHit = null; P.inv = 0'); hurt(1); if (P().hp === hp) neg++; E('P.hp = D.maxHp'); } }
  res.foresight_mash = { negated: neg + '/' + n, stamSpent: Math.round(st0 - E('P.st')) };
}
// ---- 8) charge holds: can you turn while holding?
setup('longsword', 1, 0); W().down('heavy'); W().frame(20); W().down('left'); W().frame(10); res.turn_ls_hold = st() + ' face ' + P().face; W().up('left'); W().up('heavy'); W().frame(60);
setup('katana', 1, 0); E('P.sheathed = true'); W().down('heavy'); W().frame(10); W().down('left'); W().frame(10); res.turn_kt_hold = st() + ' face ' + P().face; W().up('left'); W().up('heavy'); W().frame(60);
// ---- 9) sheathed J / K->K loop / flash step stamina
setup('katana', 1, 30); E('P.sheathed = true'); W().tap('attack'); W().frame(2); res.kt_sheathedJ = st() + ' sheathed ' + E('P.sheathed');
return res;
