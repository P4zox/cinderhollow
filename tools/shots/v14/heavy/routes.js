// v14 heavy route test: every new Greatsword / Maul combo and every v14 fix, driven by real inputs only (press / hold /
// release / wait). Run: SHOT_HTML=web/dist/v14_heavy.html sh tools/shots/wm/run.sh tools/shots/v14/heavy/routes.js
// heavy-group probe helpers (real inputs only): play(type, rank, steps, o) -> { tl, hits, dx, stam }
// steps: 'J' 'K' 'L' 'I' 'jump' taps (1 frame) | 'hK600' hold K 600 ms | 'hI300' hold I | 'w20' wait 20 frames |
//        'dK' / 'uK' / 'dR' / 'uR' / 'dL' / 'uL' / 'dU' / 'uU' / 'dD' / 'uD' / 'dI' / 'uI' press / release | 'E:js' eval
const KEYS = { J: 'attack', K: 'heavy', L: 'roll', I: 'parry', R: 'right', Lf: 'left', U: 'up', D: 'down' };
function play(type, rank, steps, o = {}) {
  W().reset(type, rank); arena(); W().reset(type, rank);
  if (o.inf !== false) E('D.maxSt = 1e6; P.st = 1e6');
  if (o.dummy !== false) { W().dummy(o.dx || 30, o.dopt || {}); if (o.follow !== false) E('window.__wm.follow = ' + (o.dx || 30)); }
  if (o.pre) E(o.pre);
  const tl = []; let last = null; const x0 = E('P.x'), st0 = E('P.st'), t0 = W().ms;
  const rec = () => { const s = E('P.state + (ATK[P.state] && P.mvLv ? ":" + P.mvLv : "")'); if (s !== last) { tl.push(s + '@' + Math.round(W().ms - t0)); last = s; } };
  const fr = n => { for (let i = 0; i < n; i++) { W().frame(1); if (o.inf !== false) E('P.st = Math.max(P.st, 1e5)'); if (o.each) E(o.each); rec(); } };
  rec();
  for (const s of steps) {
    if (s.startsWith('E:')) { E(s.slice(2)); continue; }
    let m;
    if ((m = /^w(\d+)$/.exec(s))) { fr(+m[1]); continue; }
    if ((m = /^h([JKLI])(\d+)$/.exec(s))) { W().down(KEYS[m[1]]); fr(Math.round(+m[2] / (1000 / 60))); W().up(KEYS[m[1]]); continue; }
    if ((m = /^([du])(J|K|L|I|R|Lf|U|D)$/.exec(s))) { (m[1] === 'd' ? W().down : W().up)(KEYS[m[2]]); continue; }
    if ((m = /^hjump(\d+)$/.exec(s))) { W().down('jump'); fr(Math.round(+m[1] / (1000 / 60))); W().up('jump'); continue; }
    if (s === 'dJump') { W().down('jump'); continue; }
    if (s === 'uJump') { W().up('jump'); continue; }
    if (s === 'jump') { W().down('jump'); fr(1); W().up('jump'); continue; }
    if (KEYS[s]) { W().down(KEYS[s]); fr(1); W().up(KEYS[s]); continue; }
    throw new Error('bad step ' + s);
  }
  fr(o.tail ?? 90);
  const L = G.D.light;
  return { tl: tl.join(' '), hits: W().log.map(h => `${h.st}${h.lv ? ':' + h.lv : ''} ${(h.dmg / L).toFixed(2)}/${Math.round(h.poise)}@${Math.round(h.t - t0)}`).join(' | '), dx: Math.round(E('P.x') - x0), stam: o.inf === false ? Math.round(st0 - E('P.st')) : undefined };
}
const res = [], T = (name, ok, info) => res.push((ok ? 'PASS ' : 'FAIL ') + name + (info ? '  [' + info + ']' : ''));
const has = (r, s) => r.tl.split(' ').some(x => x.split('@')[0].split(':')[0] === s);
const hit = (r, s) => r.hits.split(' | ').filter(h => h.split(' ')[0].split(':')[0] === s).map(h => +h.split(' ')[1].split('/')[0]);
const ev = (r) => r.tl + ' || ' + r.hits.split(' | ').filter(h => !/ 0\.\d+\/0@/.test(h)).join(' | ');
let r;
// ---------------- Greatsword: new combos
r = play('greatsword', 1, ['J', 'w10', 'K']); T('GS J -> K: hilt bash (tap: no charge)', has(r, 'gs_bash') && hit(r, 'gs_bash')[0] > 0.7 && !has(r, 'gs_charge'), ev(r));
r = play('greatsword', 1, ['J', 'w10', 'hK1600']); T('GS J -> hold K: bash, then the charge goes on from level 2', has(r, 'gs_bash') && /gs_charged:[23]/.test(r.tl), ev(r));
r = play('greatsword', 1, ['J', 'w30', 'J', 'w10', 'hK2000']); T('GS J J -> hold K: bash -> charge', has(r, 'gs_bash') && /gs_charge@/.test(r.tl), ev(r));
r = play('greatsword', 1, ['J', 'w30', 'J', 'w30', 'J', 'w10', 'K'], { tail: 150 }); T('GS J J J -> K: momentum cleave 2.6', Math.abs((hit(r, 'gs_mcleave')[0] || 0) - 2.6) < 0.1, ev(r));
r = play('greatsword', 1, ['dI', 'w10', 'E:hurtPlayer(40, -1, 991, {})', 'w10', 'J', 'uI']); T('GS block a blow -> J: retort 1.8', Math.abs((hit(r, 'gs_retort')[0] || 0) - 1.8) < 0.1, ev(r));
r = play('greatsword', 1, ['dI', 'w10', 'E:hurtPlayer(40, -1, 992, {})', 'w10', 'uI', 'w10', 'J']); T('GS block, let go, J inside 0.7 s: retort', has(r, 'gs_retort'), ev(r));
r = play('greatsword', 1, ['dI', 'w20', 'J', 'uI']); T('GS guard -> J with nothing blocked: the plain light', has(r, 'gs_1') && !has(r, 'gs_retort'), ev(r));
r = play('greatsword', 3, ['dK', 'w55', 'L', 'w5', 'J', 'w20', 'uK']); T('GS III hold K -> L -> J: leaping wide slash (lv3 2.8)', Math.abs((hit(r, 'gs_leap')[0] || 0) - 2.8) < 0.1, ev(r));
r = play('greatsword', 2, ['dK', 'w55', 'L', 'w5', 'J', 'w20', 'uK']); T('GS II: no leap below rank III (the charge resumes)', !has(r, 'gs_leap') && has(r, 'gs_tackle'), ev(r));
// ---------------- Greatsword: fixes
r = play('greatsword', 1, ['K']); T('GS K tap: the heave takes 180 ms before the swing', /gs_charged:1@(1[6-9]\d|2\d\d)/.test(r.tl), r.tl);
r = play('greatsword', 1, ['hK1350']); T('GS lv3 holds to 1.4 s (was 1.3)', /gs_charged:3/.test(r.tl), r.tl);
r = play('greatsword', 1, ['hK1500']); T('GS past 1.4 s: overcharged to level 2', /gs_charged:2/.test(r.tl), r.tl);
r = play('greatsword', 1, ['hK1000', 'w5', 'hK1600', 'w10', 'hK1400']); T('GS hold K through the strong slash (rank I): the next charge starts', /gs_strong:3@\d+ gs_charge@/.test(r.tl), r.tl);
r = play('greatsword', 1, ['J', 'w30', 'J', 'w30', 'J', 'w10', 'K', 'w45', 'hK2400']); T('GS hold K through the momentum cleave: the charge starts', /gs_mcleave@\d+ gs_charge@/.test(r.tl), r.tl);
r = play('greatsword', 1, ['K', 'w6', 'K', 'w6', 'K', 'w6', 'K', 'w6', 'K', 'w6', 'K']); T('GS K mash stops after the strong slash', !/gs_strong.*gs_charge/.test(r.tl), r.tl);
r = play('greatsword', 2, ['dK', 'w20', 'L', 'w20', 'L', 'w40', 'uK']); T('GS II: one tackle per charge (the 2nd L rolls)', (r.tl.match(/gs_tackle/g) || []).length === 1 && has(r, 'roll'), r.tl);
r = play('greatsword', 5, ['hK1600']); T('GS V: wrath at 1.6 s', /gs_wrath:4/.test(r.tl), r.tl);
r = play('greatsword', 5, ['hK2300']); T('GS V: wrath overcharges past 2.1 s', /gs_charged:2/.test(r.tl), r.tl);
r = play('greatsword', 5, ['hK1000', 'w5', 'hK2000']); T('GS V: no wrath level on the strong charge', /gs_strong:2/.test(r.tl), r.tl);
// ---------------- Maul: new combos
r = play('maul', 1, ['I', 'w10', 'E:hurtPlayer(40, -1, 993, {})', 'w5', 'K']); T('ML brace a blow -> K: payback 2.0 (stun x2)', Math.abs((hit(r, 'ml_payback')[0] || 0) - 2.0) < 0.1, ev(r));
r = play('maul', 1, ['I', 'w34', 'E:hurtPlayer(40, -1, 994, {})', 'w10', 'K']); T('ML a blow at the end of the brace still leaves time for payback', has(r, 'ml_payback'), ev(r));
r = play('maul', 1, ['dK', 'w20', 'J', 'w40', 'uK']); T('ML hold K -> J: haft jab, then back to the charge', /ml_jab@\d+ ml_charge@/.test(r.tl) && hit(r, 'ml_jab').length === 1, ev(r));
r = play('maul', 1, ['dK', 'w40', 'J', 'w5', 'uK']); T('ML jab, K let go: the charge releases at its level', /ml_jab@\d+ ml_(double|upswing)/.test(r.tl), ev(r));
r = play('maul', 1, ['dK', 'w20', 'J', 'w30', 'J', 'w30', 'uK']); T('ML one jab per charge', (r.tl.match(/ml_jab/g) || []).length === 1, r.tl);
r = play('maul', 2, ['hK600', 'w20', 'K']); T('ML II double smash -> K: third pound 1.6', Math.abs((hit(r, 'ml_pound')[0] || 0) - 1.6) < 0.1, ev(r));
r = play('maul', 2, ['hK600', 'w20', 'hK800']); T('ML II double smash -> hold K: a fresh charge instead', !has(r, 'ml_pound') && /ml_double@\d+ ml_charge@/.test(r.tl), r.tl);
r = play('maul', 1, ['hK600', 'w20', 'K']); T('ML I: no pound below rank II (the tap is dropped)', !has(r, 'ml_pound') && !/ml_double@\d+ ml_charge/.test(r.tl), r.tl);
r = play('maul', 4, ['dJump', 'w3', 'J', 'w8', 'J', 'w20', 'uJump'], { dx: 26, dopt: { tall: 90 }, follow: false }); T('ML IV air J J: hammer spike', Math.abs((hit(r, 'ml_spike')[0] || 0) - 1.3) < 0.1, ev(r));
// ---------------- Maul: fixes
r = play('maul', 1, ['K']); T('ML K tap: 150 ms heave before the upswing', /ml_upswing@(1[3-9]\d|2\d\d)/.test(r.tl), r.tl);
r = play('maul', 1, ['hK1350']); T('ML 1.35 s released: still the big smash (window to 1.4 s)', has(r, 'ml_bigsmash'), r.tl);
r = play('maul', 1, ['hK1600']); T('ML I held to 1.4 s standing: the spin', has(r, 'ml_spin'), r.tl);
r = play('maul', 5, ['hK1600']); T('ML V held to 1.4 s standing still: earthshaker (1.0 wave)', has(r, 'ml_quake') && hit(r, 'ml_quake').some(d => Math.abs(d - 1.0) < 0.1), ev(r));
r = play('maul', 5, ['dR', 'hK1600', 'uR']); T('ML V held to 1.4 s walking: the spin', has(r, 'ml_spin') && !has(r, 'ml_quake'), r.tl);
r = play('maul', 1, ['J', 'w25', 'J', 'w25', 'J', 'w10', 'hK1300']); T('ML J J J -> hold K (rank I): the charge starts after the upswing', /ml_3@\d+ ml_charge@/.test(r.tl), r.tl);
r = play('maul', 1, ['L', 'w15', 'hK400']); T('ML L -> hold K: the charge out of the roll', has(r, 'ml_charge') && has(r, 'ml_upswing'), r.tl);
r = play('maul', 1, ['I', 'w38', 'hK300']); T('ML brace, no blow, K after the window: leaves the brace at once', /brace@\d+ idle@(6[0-9]\d)/.test(r.tl) && has(r, 'ml_charge'), r.tl);
r = play('maul', 3, ['J', 'w25', 'J', 'w25', 'J', 'w25', 'K', 'w30', 'K', 'w30', 'K', 'w30', 'K']); T('ML III Big Bang: J J J then K on each blow plays all four', has(r, 'ml_bb4'), r.tl);
r = play('maul', 3, ['J', 'w25', 'J', 'w25', 'J', 'w25', ...Array(16).fill(['K', 'w8']).flat()]); T('ML III Big Bang: K mashed after J J J plays all four, then stops', has(r, 'ml_bb4') && !/ml_bb4@\d+ ml_charge/.test(r.tl), r.tl);
{ const pre = 'window.__minY = 1e9', each = 'window.__minY = Math.min(window.__minY, P.y)';
  r = play('maul', 1, ['hjump400', 'w10', 'dD', 'J', 'uD', 'w60'], { dx: 0.01, dopt: { tall: 70 }, follow: false, pre, each }); const ml = 304 - E('window.__minY');
  r = play('greatsword', 1, ['hjump400', 'w10', 'dD', 'J', 'uD', 'w60'], { dx: 0.01, dopt: { tall: 70 }, follow: false, pre, each }); const gs = 304 - E('window.__minY');
  T('ML ground pound bounces higher than a plain pogo', ml > gs + 6, `maul ${Math.round(ml)} px vs greatsword ${Math.round(gs)} px`); }
return { pass: res.filter(x => x.startsWith('PASS')).length, fail: res.filter(x => x.startsWith('FAIL')).length, res };
