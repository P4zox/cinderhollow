// v15 Martial Arts: every move from real inputs (run with tools/shots/wm/run.sh: the WM prelude gives W(), E, arena()).
// SHOT_HTML=web/dist/v15_fist.html sh tools/shots/wm/run.sh tools/shots/v15/fist/routes.js tools/shots/v15/fist/out
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
arena();
const go = (r = 1, style = 'swift') => { W().reset('fist', r); E(`P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.ftStyle = '${style}'; P.ftFlow = 0; P.ftFlowT = 0; P.ftShiftQ = null; P.inv = 0`); W().frame(2); reset(); };
const B = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' };
const tap = (b, n = 2) => W().tap(B[b] || b, n);
const sts = () => [...new Set(W().log.filter(l => l.melee).map(l => l.st))];
const hitsOf = id => W().log.filter(l => l.st === id);
const dmg = id => +(hitsOf(id).reduce((a, l) => a + l.dmg / l.light, 0)).toFixed(2);
const state = () => E('P.state'), style = () => E('P.ftStyle || "swift"');
const until = (cond, max = 120) => { for (let i = 0; i < max; i++) { if (E(cond)) return i; W().frame(1); } return -1; };
E(`(() => { const W = window.__wm; if (W.seen) return; const f = W.frame; W.seen = []; W.frame = (n = 1) => { for (let i = 0; i < n; i++) { f(1); if (W.seen[W.seen.length - 1] !== P.state) W.seen.push(P.state); } }; })()`);
const reset = () => E('window.__wm.seen.length = 0');   // every state passed through (sampled per frame)
const run = n => W().frame(n);
const trail = () => E('window.__wm.seen').filter(s => s.startsWith('ft_')).join(' ');

// ---------------------------------------------------------------- SWIFT
go(); W().dummy(24); for (let i = 0; i < 4; i++) { tap('J'); W().frame(8); } W().frame(80);
ok(sts().join() === 'ft_jab,ft_cross,ft_hook,ft_knee' && hitsOf('ft_knee').length === 3, `Swift J J J J -> ${sts().join(' ')} (knee hits ${hitsOf('ft_knee').length}; ${W().log.map(l => (l.dmg / l.light).toFixed(2)).join('/')})`);
go(); W().dummy(24); for (let i = 0; i < 12; i++) { tap('J', 1); W().frame(3); } W().frame(120);
ok(sts().join() === 'ft_jab,ft_cross,ft_hook,ft_knee', `mashing J stops at the knee rush finisher (${sts().join(' ')})`);
// J J (pause) J: rank II backfist; rank I the hook
go(2); W().dummy(24); tap('J'); W().frame(6); tap('J'); until("P.state === 'idle'"); W().frame(10); tap('J'); W().frame(50);
ok(sts().includes('ft_backfist'), `II: J J (pause) J -> ${sts().join(' ')}`);
go(1); W().dummy(24); tap('J'); W().frame(6); tap('J'); until("P.state === 'idle'"); W().frame(10); tap('J'); W().frame(50);
ok(!sts().includes('ft_backfist') && sts().includes('ft_hook'), `I: J J (pause) J -> the hook (${sts().join(' ')})`);
go(2); W().dummy(24); tap('J'); W().frame(6); tap('J'); until("P.state === 'idle'"); W().frame(10); tap('J'); W().frame(10); tap('J'); W().frame(60);
ok(sts().join() === 'ft_jab,ft_cross,ft_backfist,ft_knee', `II: J J (pause) J J -> backfist -> knee rush (${sts().join(' ')})`);
// K, K K, J K, J J K
go(); W().dummy(26); tap('K'); W().frame(60);
ok(sts().join() === 'ft_snap', `Swift K -> snap kick (${dmg('ft_snap')})`);
go(); W().dummy(26); tap('K'); W().frame(10); tap('K'); W().frame(80);
ok(sts().join() === 'ft_snap,ft_round' && hitsOf('ft_round').length === 2, `Swift K K -> ${sts().join(' ')} (${hitsOf('ft_round').length} hits)`);
go(); W().dummy(24); tap('J'); W().frame(6); tap('K'); W().frame(60);
ok(sts().join() === 'ft_jab,ft_rknee', `Swift J K -> ${sts().join(' ')}`);
go(); W().dummy(24); E("window.__wmB2 = window.__wm.dummy(-20)"); W().dummy(24); E('enemies.push(window.__wmB2)');
tap('J'); W().frame(6); tap('J'); W().frame(6); tap('K'); W().frame(80);
ok(sts().includes('ft_whirl') && hitsOf('ft_whirl').length >= 2, `Swift J J K -> whirlwind kick, hits ${hitsOf('ft_whirl').length} (both sides)`);
E('enemies = enemies.filter(e => !e.wmDummy)');
// hold K: hundred fists (II), the snap kick at I
go(2); W().dummy(24); W().down('heavy'); W().frame(70); W().up('heavy'); W().frame(30);
const hf = hitsOf('ft_hundred').length;
ok(hf >= 12, `II: hold K (1.17 s) -> hundred fists, ${hf} hits, ${dmg('ft_hundred')} dmg`);
go(1); W().dummy(24); W().down('heavy'); W().frame(40); W().up('heavy'); W().frame(40);
ok(sts().join() === 'ft_snap', `I: hold K -> just the snap kick (${sts().join(' ')})`);
go(2); W().dummy(24); W().down('heavy'); W().frame(4); W().up('heavy'); W().frame(40);
ok(sts().join() === 'ft_snap' && hitsOf('ft_snap')[0].mvT < 170, `II: a K tap is still the snap kick, no delay (hit at ${hitsOf('ft_snap')[0] && hitsOf('ft_snap')[0].mvT.toFixed(0)} ms)`);
// up J
go(); W().dummy(18); W().down('up'); tap('J'); W().up('up'); W().frame(40);
ok(sts().join() === 'ft_upper', `Swift up J -> rising uppercut (${sts().join(' ')})`);
// L, L -> J, L -> K
go(); tap('L'); W().frame(1);
ok(E('P.state') === 'roll' && E('P.anim.tag') === 'ft_slip' || E('P.anim.tag') === 'roll', `Swift L -> slip step (tag ${E('P.anim.tag')}, total ${E('P.dg && P.dg.total')} ms, inv ${E('P.dg && P.dg.inv')})`);
go(); W().dummy(70); tap('L'); W().frame(8); tap('J'); W().frame(40);
ok(sts().join() === 'ft_sjab', `Swift L -> J -> shadow jab (${sts().join(' ')})`);
go(); W().dummy(70); tap('L'); W().frame(8); tap('K'); W().frame(50);
ok(sts().join() === 'ft_sweep', `Swift L -> K -> sliding sweep (${sts().join(' ')})`);
// perfect slip -> flowing counter (III): a blow lands 60 ms into the slip
for (const r of [3, 2]) {
  go(r); W().dummy(30); tap('L', 1); W().frame(3); E("hurtPlayer(20, -1, 'tblow', {})"); const perf = E('!!(P.dg && P.dg.perfect)'); tap('J'); W().frame(50);
  if (r === 3) ok(perf && sts().includes('ft_fcounter'), `III: perfect slip -> J -> flowing counter (${sts().join(' ')}, ${dmg('ft_fcounter')})`);
  else ok(!sts().includes('ft_fcounter'), `II: no flowing counter yet (${sts().join(' ') || 'nothing'})`);
}
// ---------------------------------------------------------------- STYLE CHANGE
go(); tap('I'); W().frame(1);
ok(state() === 'ft_toiron' && style() === 'iron', `I (neutral): change style -> ${style()} (${state()})`);
const sw = until("P.state === 'idle'");
ok(sw >= 15 && sw <= 20, `the flourish takes ~300 ms (${(sw + 1) * 16.7 | 0} ms)`);
W().frame(4); ok(E('P.anim.tag') === 'ft_ir_idle' || !E("pHas('ft_ir_idle')"), `Iron idle tag (${E('P.anim.tag')})`);
tap('I'); W().frame(20); ok(style() === 'swift', 'I again -> Swift');
// ---------------------------------------------------------------- IRON
go(1, 'iron'); W().dummy(26); for (let i = 0; i < 3; i++) { tap('J'); W().frame(10); } W().frame(120);
ok(sts().join() === 'ft_palm,ft_elbow,ft_shoulder', `Iron J J J -> ${sts().join(' ')} (${W().log.map(l => (l.dmg / l.light).toFixed(2)).join('/')}, poise ${W().log.map(l => l.poise | 0).join('/')})`);
go(1, 'iron'); W().dummy(26); tap('K'); W().frame(80);
ok(sts().join() === 'ft_hammer', `Iron K -> hammer fist (${dmg('ft_hammer')})`);
go(1, 'iron'); W().dummy(26); tap('K'); W().frame(10); tap('K'); W().frame(120);
ok(sts().join() === 'ft_hammer,ft_stomp' && hitsOf('ft_stomp').length >= 2, `Iron K K -> mountain stomp, ${hitsOf('ft_stomp').length} hits (blow + shockwave) ${dmg('ft_stomp')}`);
go(1, 'iron'); W().dummy(26); W().down('heavy'); W().frame(30); W().up('heavy'); W().frame(60);
ok(sts().join() === 'ft_ifist' && Math.abs(dmg('ft_ifist') - 1.8) < 0.05, `Iron hold K 0.5 s -> iron fist lv1 ${dmg('ft_ifist')}`);
go(1, 'iron'); W().dummy(26); W().down('heavy'); W().frame(60); W().up('heavy'); W().frame(60);
ok(sts().join() === 'ft_ifist' && Math.abs(dmg('ft_ifist') - 2.6) < 0.05, `Iron hold K 1 s -> iron fist lv2 ${dmg('ft_ifist')} (poise ${hitsOf('ft_ifist').map(l => l.poise | 0)})`);
go(1, 'iron'); W().dummy(26); W().down('heavy'); W().frame(5); W().up('heavy'); W().frame(70);
ok(sts().join() === 'ft_hammer', `Iron K tap (via the charge) -> hammer fist (${sts().join(' ')})`);
go(1, 'iron'); W().dummy(24); tap('J'); W().frame(10); tap('K'); W().frame(80);
ok(sts().join() === 'ft_palm,ft_throw', `Iron J K -> grapple throw (${sts().join(' ')})`);
go(1, 'iron'); W().dummy(24); tap('J'); W().frame(10); tap('J'); W().frame(10); tap('K'); W().frame(100);
ok(sts().join() === 'ft_palm,ft_elbow,ft_pillar', `Iron J J K -> pillar kick (${sts().join(' ')})`);
go(1, 'iron'); W().dummy(18); W().down('up'); tap('J'); W().up('up'); W().frame(60);
ok(sts().join() === 'ft_heaven', `Iron up J -> heaven's uppercut (${sts().join(' ')})`);
go(1, 'iron'); tap('L'); W().frame(1);
ok(E('P.dg && P.dg.kind') === 'istep', `Iron L -> iron step (${E('P.anim.tag')}, ${E('P.dg.total')} ms, ${E('P.dg.stam')} stam)`);
go(1, 'iron'); W().dummy(60); tap('L'); W().frame(12); tap('K'); W().frame(50);
ok(sts().join() === 'ft_bash', `Iron L -> K -> shoulder bash (${sts().join(' ')})`);
// armour: an Iron wind-up shrugs a 10% blow; a Swift jab flinches
go(1, 'iron'); W().dummy(30); tap('J'); W().frame(6); E("hurtPlayer(Math.round(D.maxHp * 0.1), -1, 'ta', {})"); W().frame(1);
ok(state() === 'ft_palm', `Iron palm wind-up: a 10% blow doesn't flinch (${state()})`);
go(1, 'iron'); W().dummy(30); tap('J'); W().frame(6); E("hurtPlayer(Math.round(D.maxHp * 0.3), -1, 'tb', {})"); W().frame(1);
ok(state() === 'hurt', `Iron palm wind-up: a 30% blow still flinches (${state()})`);
go(1); W().dummy(30); tap('J'); W().frame(2); E("hurtPlayer(Math.round(D.maxHp * 0.1), -1, 'tc', {})"); W().frame(1);
ok(state() === 'hurt', `Swift jab: a 10% blow flinches (${state()})`);
// ---------------------------------------------------------------- SHIFT STRIKES
go(); W().dummy(24); reset(); tap('J'); W().frame(6); tap('J'); W().frame(3); tap('I'); run(20); tap('J'); run(60);
ok(trail().startsWith('ft_jab ft_cross ft_fstar ft_elbow') && style() === 'iron', `Swift J J -> I -> J: ${trail()} (style ${style()})`);
const fs = hitsOf('ft_fstar')[0];
ok(fs && Math.abs(fs.dmg / fs.light - 1.4 * 1.15) < 0.03, `Falling star = 1.4 x 1.15 (${fs && (fs.dmg / fs.light).toFixed(2)})`);
const cr = hitsOf('ft_cross')[0];
ok(cr && fs && fs.t - cr.t - 260 < 100, `the cross cancels on its hit (falling star starts ${fs && cr ? (fs.t - cr.t - 260) | 0 : '?'} ms after the cross's hit + its 260 ms wind)`);
go(1, 'iron'); W().dummy(24); reset(); tap('J'); W().frame(8); tap('I'); run(30); tap('J'); run(40);
ok(trail().startsWith('ft_palm ft_wind ft_cross') && hitsOf('ft_wind').length === 4 && style() === 'swift', `Iron J -> I -> J: ${trail()} (wind cut ${hitsOf('ft_wind').length} hits ${dmg('ft_wind')})`);
// the full dance: Swift J J -> I -> J -> I -> J J
go(); W().dummy(24); reset();
tap('J'); W().frame(6); tap('J'); W().frame(3); tap('I'); run(22); tap('J'); run(10); tap('I'); run(22); tap('J'); run(8); tap('J'); run(60);
ok(trail() === 'ft_jab ft_cross ft_fstar ft_elbow ft_wind ft_cross ft_hook', `Swift -> Iron -> Swift: ${trail()}`);
// a late shift: I up to 150 ms after the move ended
go(); W().dummy(24); reset(); tap('J'); until("P.state === 'idle'"); W().frame(4); tap('I'); run(30);
ok(trail().includes('ft_fstar'), `late I (70 ms after the jab ended) is still a Shift: ${trail()}`);
go(); W().dummy(24); reset(); tap('J'); until("P.state === 'idle'"); W().frame(14); tap('I'); run(30);
ok(trail().includes('ft_toiron') && !trail().includes('ft_fstar'), `I 230 ms after: a style change, not a Shift: ${trail()}`);
// tempest to mountain (III): J J J -> I -> K
for (const r of [3, 1]) {
  go(r); W().dummy(24); reset(); tap('J'); W().frame(6); tap('J'); W().frame(6); tap('J'); W().frame(4); tap('I'); run(12); tap('K'); run(100);
  if (r === 3) ok(trail().includes('ft_fstar ft_tempest') && hitsOf('ft_tempest').length === 5, `III: J J J -> I -> K: ${trail()} (tempest ${hitsOf('ft_tempest').length} hits, ${dmg('ft_tempest')})`);
  else ok(trail().includes('ft_fstar ft_hammer'), `I: J J J -> I -> K: falling star -> hammer fist (${trail()})`);
}
// iron to wind release (IV)
for (const r of [4, 3]) {
  go(r, 'iron'); W().dummy(40); reset(); W().down('heavy'); W().frame(30); tap('I'); run(5); W().up('heavy'); run(50);
  if (r === 4) ok(trail().includes('ft_ichg ft_release') && style() === 'swift' && hitsOf('ft_release').length === 1, `IV: Iron hold K -> I: ${trail()} (${dmg('ft_release')}, style ${style()})`);
  else ok(!trail().includes('ft_release'), `III: no release yet (${trail()})`);
}
// Flow and the Ember palm (V)
go(5); W().dummy(24); for (let i = 0; i < 4; i++) { tap('J'); W().frame(8); } W().frame(60);
ok(E('P.ftFlow') === 2, `four landed moves build 2 Flow (${E('P.ftFlow')})`);
go(5); E('P.ftFlow = 5; P.ftFlowT = 6'); W().dummy(24); W().down('parry'); W().frame(20); W().up('parry'); W().frame(70);
ok(sts().join() === 'ft_ember' && Math.abs(dmg('ft_ember') - 3) < 0.08 && E('P.ftFlow') < 1, `V: hold I at 5 Flow -> ember palm ${dmg('ft_ember')} (flow after ${E('P.ftFlow')})`);
go(5); E('P.ftFlow = 5; P.ftFlowT = 6'); W().dummy(24); W().down('parry'); W().frame(3); W().up('parry'); W().frame(30);
ok(sts().length === 0 && style() === 'iron' && E('P.ftFlow') === 5, `V: tap I at 5 Flow -> just the style change (style ${style()}, flow ${E('P.ftFlow')}, ${trail()}, hits: ${sts().join(' ')})`);
go(4); E('P.ftFlow = 5; P.ftFlowT = 6'); W().dummy(24); W().down('parry'); W().frame(20); W().up('parry'); W().frame(70);
ok(!sts().includes('ft_ember'), `IV: no ember palm (${sts().join(' ') || 'style change'})`);
// ember shift (I-IV): a Shift at 5 Flow is x1.3 and spends it
go(1); E('P.ftFlow = 5; P.ftFlowT = 6'); W().dummy(24); tap('J'); W().frame(6); tap('I'); W().frame(50);
const es = hitsOf('ft_fstar')[0];
ok(es && Math.abs(es.dmg / es.light - 1.4 * 1.3) < 0.03 && E('P.ftFlow') <= 1, `Ember shift at 5 Flow: ${es && (es.dmg / es.light).toFixed(2)} (= 1.4 x 1.3), flow -> ${E('P.ftFlow')}`);
// ---------------------------------------------------------------- AIR
go(); W().dummy(20); tap('jump'); W().frame(8); tap('J'); W().frame(30);
ok(sts().join() === 'ft_akick', `Swift air J -> air kick (${sts().join(' ')})`);
go(); W().dummy(20); tap('jump'); W().frame(8); tap('J'); W().frame(10); tap('J'); W().frame(40);
ok(sts().join() === 'ft_akick,ft_akick3' && hitsOf('ft_akick3').length === 3, `Swift air J J -> triple air kick (${hitsOf('ft_akick3').length} hits)`);
go(1, 'iron'); W().dummy(30); tap('jump'); W().frame(14); tap('J'); W().frame(70);
ok(sts().join() === 'ft_aelbow' && E('P.ground'), `Iron air J -> diving elbow lands (${sts().join(' ') || 'no hit'}, ${dmg('ft_aelbow')})`);
go(); W().dummy(26); tap('jump'); W().frame(14); tap('K'); W().frame(70);
ok(sts().join() === 'ft_aheel', `air K -> diving heel (${sts().join(' ') || 'no hit'}, ${dmg('ft_aheel')})`);
go(); tap('jump'); W().frame(18); W().dummy(0); W().down('down'); tap('J'); W().frame(30); W().up('down'); W().frame(30);
ok(sts().join() === 'ft_astomp', `air down J -> stomp pogo (${sts().join(' ')})`);
go(); tap('jump'); W().frame(8); tap('I'); W().frame(2);
ok(style() === 'iron', `I in the air: an instant style change (${style()})`);
// ---------------------------------------------------------------- TURNING, LUNGES
go(); W().dummy(24); tap('J'); W().frame(4); W().down('left'); tap('J'); W().frame(14); W().up('left'); const f2 = E('P.face'); W().frame(40);
ok(f2 === -1, `turning between chain steps: hold left during the jab -> the cross faces left (${f2})`);
const travel = {};
for (const [id, style, inp] of [['ft_knee', 'swift', 'JJJJ'], ['ft_shoulder', 'iron', 'JJJ'], ['ft_sweep', 'swift', 'LK'], ['ft_bash', 'iron', 'LK'], ['ft_release', 'iron', 'hK']]) {
  go(4, style); E('enemies = enemies.filter(e => !e.wmDummy)'); W().down('right');
  if (inp === 'hK') { W().down('heavy'); W().frame(30); tap('I'); }
  else for (const c of inp) { tap(c); W().frame(c === 'L' ? 10 : 8); }
  until(`P.state === '${id}'`, 200); const x0 = E('P.x'); until(`P.state !== '${id}'`, 200); travel[id] = Math.round(E('P.x') - x0); W().up('right'); W().up('heavy');
}
ok(Object.entries(travel).every(([k, v]) => v <= 36 || ['ft_release', 'ft_bash'].includes(k)), `lunges (pushing forward): ${Object.entries(travel).map(([k, v]) => k + ' ' + v).join(', ')} px (release / bash are dashes)`);
// mastery ranks: the unlock list and the move list
ok(E("wmUnlocks('fist').length") === 6 && E("wmMoveList('fist').length") >= 30, `unlocks ${E("wmUnlocks('fist').length")}, move list ${E("wmMoveList('fist').length")} entries`);
ok(E("MV.types.fist.combos.every(c => c.desc.length <= 70)"), 'every combo desc <= 70 chars');
const real = E("Object.values(MV.defs).filter(d => d.type === 'fist').map(d => d.id + ':' + (pHas(d.tags[0]) ? 'own' : 'fallback'))");
ok(real.every(s => s.endsWith('own')), `own animation tags: ${real.filter(s => s.endsWith('own')).length}/${real.length}` + (real.some(s => s.endsWith('fallback')) ? ' (fallback: ' + real.filter(s => s.endsWith('fallback')).join(' ') + ')' : ''));
return { pass: out.length - fail.length, fail: fail.length, out };
