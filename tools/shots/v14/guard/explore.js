// exploration: SnS + Spear, real inputs (v14 guard agent)
const res = {};
const P = () => G.P, st = () => G.P.state;
let hid = 0;
const hurt = (dmg, o = {}) => E(`(() => { const d = enemies.find(e => e.wmDummy); return hurtPlayer(${dmg}, ${o.dir ?? -1}, 'gx${++hid}', { src: d, parryable: ${!!o.parryable} }); })()`);
const setup = (type, rank = 1, far = 26) => { W().reset(type, rank); arena(); W().reset(type, rank); E('P.lastHit = null'); W().dummy(far); E('window.__wm.follow = ' + far); };
const trace = (n) => { const seen = []; for (let k = 0; k < n; k++) { W().frame(1); const s = st(); if (seen[seen.length - 1] !== s) seen.push(s); } return seen.join(' '); };
const dmgs = () => W().log.map(h => h.st + ':' + (h.dmg / h.light).toFixed(2)).join(' ');
// ---- SnS perfect rush: press timing sweep (frames after the previous press)
for (const gap of [6, 10, 12, 14, 16, 19, 21, 24]) {
  setup('sns', 2); E('D.maxSt = 1e6; P.st = 1e6');
  W().tap('attack'); W().frame(gap - 1); W().tap('attack'); W().frame(gap - 1); W().tap('heavy');
  res['prush_gap' + gap] = trace(70) + ' | ' + dmgs();
}
// ---- SnS tap I lengths: parry vs guard
for (const hold of [2, 4, 6, 8, 12]) { setup('sns'); W().down('parry'); W().frame(hold); W().up('parry'); res['sns_I_hold' + hold] = trace(40); }
// counterBonus persistence
setup('sns', 5); W().down('parry'); W().frame(2); hurt(30); W().frame(2); W().up('parry'); W().frame(300); res.sns_cbonus_after5s = E('P.counterBonus');
// slam from guard without a block
setup('sns', 3); W().down('parry'); W().frame(20); W().tap('heavy'); res.sns_guardK_r3 = trace(60); W().up('parry');
// backhop -> leap travel
setup('sns'); const x0 = P().x; W().tap('roll'); W().frame(10); W().tap('attack'); res.sns_leap = trace(60) + ' dx ' + (P().x - x0).toFixed(0) + ' | ' + dmgs();
// heal walking
setup('sns'); E('P.flasksR = 3; P.hp = 50'); const hx = P().x; W().down('right'); W().tap('heal'); W().frame(60); W().up('right'); res.sns_healwalk = 'dx ' + (P().x - hx).toFixed(0) + ' ' + st();
// ---- Spear counter: tap lengths at rank III
for (const hold of [3, 5, 6, 7, 8, 10, 14]) {
  setup('spear', 3); W().down('parry'); W().frame(10); E('P.gcT = 0.5'); W().down('heavy'); W().frame(hold); W().up('heavy'); res['sp_counter_hold' + hold] = trace(60); W().up('parry');
}
// spear guard poke loop: blocking fraction + dps
setup('spear', 1, 44); E('D.maxSt = 1e6; P.st = 1e6'); W().down('parry'); W().frame(6);
let blockF = 0, N = 0; const t0 = W().ms; W().log = [];
for (let k = 0; k < 360; k++) { if (k % 6 === 0) W().tap('attack'); else W().frame(1); N++; if (E('isBlocking()')) blockF++; E('P.st = 1e6'); }
res.sp_gpoke_loop = { dps: +(W().log.reduce((a, h) => a + h.dmg / h.light, 0) / ((W().ms - t0) / 1000)).toFixed(2), blocking: (blockF / N).toFixed(2), hits: W().log.length };
W().up('parry');
// spear charge dash short loop: hold K while moving, release right after the run starts
setup('spear', 1, 34); E('P.st = 100'); const s0 = P().st; const ct0 = W().ms; W().log = [];
for (let r = 0; r < 4; r++) { W().down('right'); W().down('heavy'); W().frame(27); W().up('heavy'); W().up('right'); for (let i = 0; i < 60 && st() !== 'idle'; i++) W().frame(1); }
res.sp_dash_loop = { dps: +(W().log.reduce((a, h) => a + h.dmg / h.light, 0) / ((W().ms - ct0) / 1000)).toFixed(2), stamUsed: +(s0 - P().st).toFixed(1), hits: dmgs(), secs: ((W().ms - ct0) / 1000).toFixed(2) };
// hop directions: hold back
setup('spear'); const hx0 = P().x; W().down('left'); W().tap('roll'); W().frame(20); W().up('left'); res.sp_hop_back = 'face ' + P().face + ' dx ' + (P().x - hx0).toFixed(0);
setup('spear'); const hx1 = P().x; W().tap('roll'); W().frame(20); res.sp_hop_neutral = 'face ' + P().face + ' dx ' + (P().x - hx1).toFixed(0);
// spear guard turn
setup('spear'); W().down('parry'); W().frame(10); W().down('left'); W().frame(40); res.sp_guard_hold_left = 'face ' + P().face + ' vx ' + P().vx.toFixed(0) + ' ' + st(); W().up('left'); W().up('parry');
// power guard spam stamina
setup('spear', 4); W().down('parry'); W().frame(10); const ps = P().st; for (let i = 0; i < 5; i++) { W().tap('heavy'); W().frame(30); } res.sp_pguard_spam = 'st ' + (ps - P().st).toFixed(1) + ' power ' + E('P.spPower').toFixed(2) + ' tag ' + E('P.anim.tag'); W().up('parry');
return res;
