// v14 guard group (Sword & Shield, Spear): every new combo and every fix, played from real inputs (taps / holds / waits).
// run: SHOT_HTML=web/dist/v14_guard.html sh tools/shots/wm/run.sh tools/shots/v14/guard/routes.js <outdir>
const R = [];
const T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const P = () => G.P, st = () => G.P.state;
let hid = 0;
const hurt = (dmg, o = {}) => E(`(() => { const d = enemies.find(e => e.wmDummy); return hurtPlayer(${dmg}, ${o.dir ?? -1}, 'gr${++hid}', { src: d, parryable: ${!!o.parryable} }); })()`);
const setup = (type, rank = 1, far = 26) => { W().reset(type, rank); arena(); W().reset(type, rank); E('P.lastHit = null; D.maxSt = 1e6; P.st = 1e6'); W().dummy(far); E('window.__wm.follow = ' + far); };
const seenAll = []; const trace = (n) => { const seen = []; for (let k = 0; k < n; k++) { W().frame(1); const s = st(); if (seen[seen.length - 1] !== s) seen.push(s); } return seen; };
const per = id => W().log.filter(h => h.st === id).map(h => +(h.dmg / h.light).toFixed(2));
// wait until the current move is in its last `ms` (the flash), or until it ends
const toLate = (ms = 120) => { for (let i = 0; i < 60 && E('!!ATK[P.state] && ATK[P.state].mv.total - P.mvT > ' + ms); i++) W().frame(1); };
const nextLate = (id, ms = 120) => { for (let i = 0; i < 60 && st() !== id; i++) W().frame(1); toLate(ms); };
const toEnd = () => { for (let i = 0; i < 90 && E('!!ATK[P.state]'); i++) W().frame(1); };
const tags = E("['sh_jab','sh_rim','sh_charge','sh_wheel','sp_drive','sp_hoplunge','sp_wheel','sp_rsweep'].filter(t => !pHas(t))");
T('art: every new tag is in the sheet', tags.length === 0, tags.join(','));

// ================================================================== Sword & Shield
setup('sns'); W().tap('attack'); toLate(); W().tap('heavy'); let s = trace(60);
T('SnS J K -> shield jab (rank I)', s.includes('sh_jab') && per('sh_jab')[0] === 0.7, s.join(' ') + ' ' + per('sh_jab'));
setup('sns'); W().tap('attack'); toLate(); W().tap('heavy'); nextLate('sh_jab'); W().tap('attack'); nextLate('sh_3'); W().tap('attack'); s = trace(80);
T('SnS J K J J -> jab carries on into the 3rd cut and the finisher', s.includes('sh_3') && s.includes('sh_4'), s.join(' '));
setup('sns'); W().tap('attack'); toLate(); W().tap('attack'); nextLate('sh_2'); W().tap('attack'); nextLate('sh_3'); W().tap('heavy'); s = trace(70);
T('SnS J J J K -> rim upper (rank I)', s.includes('sh_rim') && per('sh_rim')[0] === 1.2, s.join(' ') + ' ' + per('sh_rim'));
setup('sns'); W().tap('roll'); W().frame(9); W().tap('heavy'); s = trace(50);
T('SnS L -> K (during the hop) -> shield charge (rank I)', s.includes('sh_charge') && per('sh_charge').length === 1, s.join(' ') + ' ' + per('sh_charge'));
setup('sns'); W().tap('roll'); W().frame(24); W().tap('heavy'); s = trace(50);
T('SnS L, land, K (within 0.25 s) -> shield charge', s.includes('sh_charge'), s.join(' '));
setup('sns', 2); W().tap('attack'); toLate(); W().tap('attack'); toEnd(); W().frame(9); W().tap('attack'); s = trace(50);
T('SnS II J J (pause 150 ms) J -> wheel cut, 2 hits', s.includes('sh_wheel') && per('sh_wheel').length === 2, s.join(' ') + ' ' + per('sh_wheel'));
setup('sns', 1); W().tap('attack'); toLate(); W().tap('attack'); toEnd(); W().frame(9); W().tap('attack'); s = trace(50);
T('SnS rank I: J J (pause) J is a fresh J (no wheel)', !s.includes('sh_wheel'), s.join(' '));
setup('sns', 2); W().tap('attack'); toLate(); W().tap('attack'); nextLate('sh_2'); W().tap('attack'); s = trace(40);
T('SnS II J J J without a pause is still the 3rd cut', s.includes('sh_3') && !s.includes('sh_wheel'), s.join(' '));
// wheel hits behind too
setup('sns', 2, -20); E('P.face = 1'); W().tap('attack'); toLate(); W().tap('attack'); toEnd(); W().frame(9); W().tap('attack'); trace(50);
T('SnS wheel cut hits a foe behind you', per('sh_wheel').length >= 1, String(per('sh_wheel')));
// perfect rush on the beat: the press made on the very frame the cut ends counts (was a miss)
let okBeat = 0;
for (const late of [0, 1, 2]) {
  setup('sns', 2); W().tap('attack'); for (let i = 0; i < 60 && E('!!ATK[P.state] && ATK[P.state].mv.total - P.mvT > 17'); i++) W().frame(1); W().frame(late); W().tap('attack');
  for (let i = 0; i < 60 && E('!!ATK[P.state] && (P.state !== "sh_2" || ATK[P.state].mv.total - P.mvT > 17)'); i++) W().frame(1); W().frame(late); W().tap('heavy'); trace(50);
  if (per('sh_prush').length === 1) okBeat++;
}
T('SnS II perfect rush: presses on the end frame (and up to 2 frames after) count', okBeat === 3, okBeat + '/3');
setup('sns', 2); W().tap('attack'); W().frame(4); W().tap('attack'); toLate(); W().tap('heavy'); trace(50);
T('SnS II: an early press is no perfect rush (just the bash)', per('sh_prush').length === 0 && per('sh_heavy').length === 1, per('sh_heavy') + '');
// parry window kept whole when I is held; holding still ends in the guard; the press that became a block is free
setup('sns'); W().down('parry'); W().frame(8); const pk = hurt(30, { parryable: true }) === false && E('P.parried');
T('SnS: holding I keeps the 170 ms parry (a parryable hit 133 ms in is parried)', pk, String(pk)); W().up('parry');
setup('sns'); E('P.st = 100; D.maxSt = 100'); W().down('parry'); W().frame(20); const gst = st(), gs = P().st; W().up('parry');
T('SnS: hold I -> guard, the parry cost refunded', (gst === 'guard' || gst === 'block') && gs >= 99, gst + ' st ' + gs.toFixed(1));
setup('sns', 5); W().down('parry'); W().frame(2); hurt(30); W().up('parry'); W().frame(60);
T('SnS V: the perfect-guard counter bonus expires with its window', E('P.counterBonus') === 0, String(E('P.counterBonus')));
// perfect guard reflects a real missile toward the foe
setup('sns', 5); E(`projectiles.push({ owner: 'enemy', kind: 'arrow', x: P.x + 30, y: P.y - 16, vx: -230, vy: 0, g: 0, dmg: 12, life: 2, r: 3, t: 0, id: 99001, hits: new Set() })`);
W().frame(4); W().down('parry'); W().frame(4); W().up('parry'); const rf = E("(projectiles.find(p => p.id === 99001) || {}).owner"); W().frame(20);
T('SnS V: a perfectly guarded arrow flies back at the foe', rf === 'player' && W().log.some(h => !h.melee), rf + ' hits ' + W().log.length);

// ================================================================== Spear
setup('spear', 1, 44); W().tap('attack'); toLate(); W().tap('attack'); nextLate('sp_2'); W().tap('attack'); nextLate('sp_3'); W().tap('heavy'); s = trace(70);
T('SP J J J K -> impaling drive, 2 hits (rank I)', s.includes('sp_drive') && per('sp_drive').length === 2, s.join(' ') + ' ' + per('sp_drive'));
setup('spear', 1, 44); W().down('right'); W().tap('attack'); toLate(); W().tap('attack'); nextLate('sp_2'); W().tap('attack'); nextLate('sp_3'); W().tap('heavy'); s = trace(70); W().up('right');
T('SP J J J K holding forward is still the drive (not the charge dash)', s.includes('sp_drive') && !s.includes('sp_cwind'), s.join(' '));
setup('spear', 1, 50); W().tap('roll'); W().frame(10); W().tap('heavy'); s = trace(50);
T('SP L -> K -> hop lunge (rank I)', s.includes('sp_hoplunge') && per('sp_hoplunge').length === 1, s.join(' ') + ' ' + per('sp_hoplunge'));
setup('spear', 2, 30); W().tap('attack'); toLate(); W().tap('attack'); toEnd(); W().frame(9); W().tap('attack'); s = trace(60);
T('SP II J J (pause) J -> wheeling haft, 2 hits', s.includes('sp_wheel') && per('sp_wheel').length === 2, s.join(' ') + ' ' + per('sp_wheel'));
setup('spear', 2, 44); W().tap('attack'); toLate(); W().tap('attack'); nextLate('sp_2'); W().tap('attack'); s = trace(40);
T('SP II J J J without a pause is still the 3rd poke', s.includes('sp_3') && !s.includes('sp_wheel'), s.join(' '));
setup('spear', 3, 44); W().down('parry'); W().frame(10); hurt(20); W().frame(2); W().tap('heavy'); W().frame(4); W().tap('attack'); s = trace(70); W().up('parry');
T('SP III block -> K -> J -> rising sweep', s.includes('sp_counter') && s.includes('sp_rsweep') && per('sp_rsweep').length === 1, s.join(' ') + ' ' + per('sp_rsweep'));
setup('spear', 2, 44); W().down('parry'); W().frame(10); hurt(20); W().frame(2); W().tap('heavy'); W().frame(4); W().tap('attack'); s = trace(70); W().up('parry');
T('SP rank II: counter -> J does not sweep', !s.includes('sp_rsweep'), s.join(' '));
// the counter: taps up to ~140 ms stay quick, holds of 150+ ms charge
const cc = {};
for (const f of [4, 6, 8, 9, 10, 12]) { setup('spear', 3, 44); W().down('parry'); W().frame(10); hurt(20); W().frame(2); W().down('heavy'); W().frame(f); W().up('heavy'); cc[f] = trace(60).includes('sp_ccounter'); W().up('parry'); }
T('SP III charged counter: K held >= 150 ms (taps of <= 133 ms stay quick)', !cc[4] && !cc[6] && !cc[8] && cc[10] && cc[12], JSON.stringify(cc));
// guard poke: the guard opens for the thrust only
setup('spear', 1, 44); W().down('parry'); W().frame(10); W().tap('attack'); W().frame(2); const g0 = E('isBlocking()'); W().frame(8); const g1 = E('isBlocking()'); W().frame(12); const g2 = E('isBlocking()'); W().up('parry');
T('SP guard poke: guarded in the coil, open in the thrust, guarded again after', g0 && !g1 && g2, `${g0} ${g1} ${g2}`);
// charge dash finisher: costs 12; a quick release is the 1.4 thrust, a 400 ms run the 2.2
setup('spear', 1, 34); E('P.st = 100; D.maxSt = 100'); W().down('right'); W().down('heavy'); W().frame(26); W().up('heavy'); W().up('right'); trace(40);
const quick = per('sp_finish');
setup('spear', 1, 80); E('P.st = 100; D.maxSt = 100; window.__wm.follow = 0'); W().down('right'); W().down('heavy'); W().frame(52); W().up('heavy'); W().up('right'); trace(40);
const full = per('sp_finish');
T('SP charge dash: quick release 1.4, after a 400 ms run 2.2', quick[0] === 1.4 && full[0] === 2.2, quick + ' / ' + full);
// hops keep facing: from the guard, hold back + L hops back facing forward; forward + L hops forward
setup('spear'); W().down('parry'); W().frame(10); const hx = P().x; W().down('left'); W().tap('roll'); W().frame(8); const hb = { face: P().face, dx: P().x - hx }; W().up('left'); W().up('parry'); W().frame(30);
T('SP hop (holding back): hops back, still facing the foe', hb.face === 1 && hb.dx < -15, JSON.stringify(hb));
setup('spear'); const hx2 = P().x; W().down('right'); W().tap('roll'); W().frame(8); W().up('right'); const hf = { face: P().face, dx: P().x - hx2 };
T('SP hop (holding forward): hops forward', hf.face === 1 && hf.dx > 15, JSON.stringify(hf));
setup('spear', 2); W().tap('roll'); W().frame(10); W().down('left'); W().tap('roll'); W().frame(10); W().tap('roll'); W().frame(3); W().up('left');
T('SP II hop chain keeps facing (3 hops, holding back)', E('P.dg ? P.dg.n : 0') === 3 && P().face === 1, 'n ' + E('P.dg ? P.dg.n : 0') + ' face ' + P().face);
setup('spear', 2, 44); W().tap('attack'); toLate(); W().tap('attack'); toEnd(); W().tap('roll'); W().frame(10); W().tap('attack'); s = trace(40);
T('SP hop -> J continues the chain (after the 2nd poke: the 3rd)', s.includes('sp_3'), s.join(' '));
setup('spear', 4); W().down('parry'); W().frame(10); W().tap('heavy'); W().frame(4); const pg = E('P.anim.tag + " " + P.spPower.toFixed(2)'); W().tap('heavy'); W().frame(2); const pg2 = E('P.spPower'); W().up('parry');
T('SP IV power guard: its pose, not re-armed while up', pg.startsWith('sp_pguard') && pg2 < 1, pg + ' / ' + pg2.toFixed(2));
// move lists
const cl = E("({ sns: (MV.types.sns.combos || []).length, spear: (MV.types.spear.combos || []).length, bad: [...MV.types.sns.combos, ...MV.types.spear.combos].filter(c => c.desc.length > 70).map(c => c.name) })");
T('combos: both move lists present, desc <= 70 chars', cl.sns >= 15 && cl.spear >= 15 && !cl.bad.length, JSON.stringify(cl));
return R;
