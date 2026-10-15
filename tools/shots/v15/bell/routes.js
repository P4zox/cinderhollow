// Warbell (bell) routes: every move from real inputs, the rank gates, the notes / tolls / Perform trait, mashing, turning.
// Run: SHOT_HTML=web/dist/v15_bell.html sh tools/shots/wm/run.sh tools/shots/v15/bell/routes.js tools/shots/v15/bell/out
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
arena();
const go = (r = 1, o = {}) => {
  W().reset('bell', r);
  E('P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.belNotes = []; P.belBuff = {}; P.belEchoN = 0; P.belMendCd = 0; MV.later = []');
  W().frame(2); E('enemies = enemies.filter(e => !e.wmDummy)'); if (o.dummy !== undefined) W().dummy(o.dummy, o.d || {});
};
const sts = () => W().log.map(l => l.st);
const uniq = a => a.filter((x, i) => i === 0 || a[i - 1] !== x);
const notes = () => E('belNotes().join("")');
const mul = st => W().log.filter(l => l.st === st).map(l => +(l.dmg / l.light).toFixed(2));
const J = (n = 2) => W().tap('attack', n), K = (n = 2) => W().tap('heavy', n), I = (n = 2) => W().tap('parry', n), L = (n = 2) => W().tap('roll', n);
const upJ = () => { W().down('up'); J(); W().up('up'); };
const idle = () => E("['idle','run','land'].includes(P.state)");
const until = (fn, max = 200) => { for (let i = 0; i < max && !fn(); i++) W().frame(1); };

// ---- every move id has its own drawn tag (no fallback-only moves)
const ids = E("Object.keys(MV.defs).filter(k => MV.defs[k].type === 'bell')");
const fb = ids.filter(id => !E(`mvResolve(ATK['${id}']).real`));
ok(ids.length >= 20 && fb.length === 0, `all ${ids.length} bell moves play their own wb_* tag (fallback: ${fb.join(' ') || 'none'})`);
ok(E("pHas('wb_kwind') && pHas('wb_plunge')"), 'hold tags wb_kwind / wb_plunge are in the sheet');

// ---- Ash chain: J J J, notes A A A
go(1, { dummy: 26 }); for (let i = 0; i < 3; i++) { J(); W().frame(10); } W().frame(80);
ok(uniq(sts()).join() === 'wb_1,wb_2,wb_3' && notes() === 'AAA', `J J J -> ${uniq(sts()).join(' ')} ${W().log.map(l => (l.dmg / l.light).toFixed(2)).join('/')}, staff ${notes()}`);
// a whiff rings nothing
go(1); J(); W().frame(40);
ok(notes() === '', `a whiffed swing rings no note (staff '${notes()}')`);
// J J (pause) J: rank I keeps the chain going (2nd J restarts) / rank II = chime spin both sides
for (const r of [1, 2]) {
  go(r, { dummy: -24 });   // the foe BEHIND: only a both-sides move reaches it
  E('P.face = 1'); J(); W().frame(8); J(); until(idle); W().frame(14); J(); W().frame(70);
  const s = uniq(E('MV.last ? [MV.last] : []'));
  if (r === 1) ok(!sts().includes('wb_chime') && E("MV.last") !== 'wb_chime', 'rank I: J J (pause) J is no chime spin');
  else ok(sts().filter(x => x === 'wb_chime').length === 2, `rank II: J J (pause) J -> chime spin hits the foe behind twice (${mul('wb_chime').join('/')})`);
}
// J J J -> K: knell
go(1, { dummy: 26 }); for (let i = 0; i < 3; i++) { J(); W().frame(10); } W().frame(20); K(); W().frame(100);
ok(sts().includes('wb_knell') && notes() === 'AAE', `J J J K -> knell (${mul('wb_knell')}), staff ${notes()}`);
// J -> K backswing, -> J overhead clang
go(1, { dummy: 26 }); J(); W().frame(10); K(); W().frame(20); J(); W().frame(110);
ok(uniq(sts()).join() === 'wb_1,wb_back,wb_3', `J K J -> ${uniq(sts()).join(' ')}`);

// ---- Ember: K, K K, hold K
go(1, { dummy: 26 }); K(); W().frame(10); K(); W().frame(110);
ok(uniq(sts()).join() === 'wb_slam,wb_dslam' && sts().filter(x => x === 'wb_dslam').length === 2 && notes() === 'EEE', `K K -> slam + double slam x2, staff ${notes()}`);
go(1, { dummy: 26 }); W().down('heavy'); W().frame(18); W().up('heavy'); W().frame(70);
ok(uniq(sts()).join() === 'wb_slam', `K held 0.3 s (not wound) -> forward slam (${uniq(sts()).join()})`);
go(1, { dummy: 26 }); W().down('heavy'); W().frame(30); const winding = E('P.state'); W().frame(15); const wound = E('P.belWound'); W().up('heavy'); W().frame(70);
ok(winding === 'wb_kwind' && wound && uniq(sts()).join() === 'wb_toll' && mul('wb_toll')[0] === 2.4, `hold K 0.75 s -> wind-up (${winding}, wound ${wound}) -> wind-up toll ${mul('wb_toll')}`);
// K kept held through a swing: the wind-up starts as it ends
go(1, { dummy: 26 }); J(); W().frame(4); W().down('heavy'); W().frame(80); const st2 = E('P.state'); W().up('heavy'); W().frame(70);
ok(st2 === 'wb_kwind' || sts().includes('wb_toll'), `J then K held through it -> wind-up (${st2})`);

// ---- Gold: up J, up J -> J, up J up J
go(1, { dummy: 20 }); upJ(); W().frame(50);
ok(sts().includes('wb_up') && notes() === 'G', `up J -> peal uppercut, staff ${notes()}`);
go(1, { dummy: 24 }); upJ(); W().frame(10); J(); W().frame(70);
ok(uniq(sts()).join() === 'wb_up,wb_peal' && notes() === 'GA', `up J -> J -> falling peal (${uniq(sts()).join(' ')}), staff ${notes()}`);
go(1, { dummy: 20 }); upJ(); W().frame(10); upJ(); W().frame(70);
ok(sts().filter(x => x === 'wb_up').length === 2 && notes() === 'GG', `up J up J -> two peals, staff ${notes()}`);

// ---- Perform: nothing in the staff = a dull clank, nothing happens
go(1, { dummy: 26 }); I(); W().frame(4);
ok(E('P.state') !== 'wb_perform' && E('P.belDeny > 0'), 'I with an empty staff: no Perform (deny)');
// each toll
const perf = (seq, r = 1) => { go(r, { dummy: 26 }); E(`P.belNotes = ${JSON.stringify(seq.split(''))}`); I(); W().frame(70); return E('JSON.stringify(Object.fromEntries(Object.entries(P.belBuff).filter(([k, v]) => v > 0).map(([k, v]) => [k, Math.round(v)])))'); };
let b = perf('AA'); ok(b.includes('swift') && E('mvRegenMul()') === 1.25 && notes() === '', `Ash Ash -> Swiftness ${b}, regen x${E('mvRegenMul()')}, staff emptied`);
ok(mul('wb_perform').length === 1 && mul('wb_perform')[0] === 1.2, `Perform rings the foe for ${mul('wb_perform')}`);
b = perf('AE'); ok(b === '{"iron":29}', `Ash Ember -> Iron hymn ${b}`);
b = perf('EE'); ok(b === '{"fury":29}', `Ember Ember -> Fury ${b}`);
W().log = []; J(); W().frame(50); ok(mul('wb_1')[0] === +(1.1 * 1.08).toFixed(2), `Fury: the left swing deals ${mul('wb_1')} (1.1 x 1.08)`);
b = perf('AAE'); ok(b.includes('swift') && b.includes('iron'), `Ash Ash Ember -> two tolls at once ${b}`);
b = perf('GG'); ok(b === '{"echo":29}' && E('P.belEchoN') === 3, `Gold Gold -> Echo ${b}, 3 charges`);
W().log = []; for (let i = 0; i < 4; i++) { J(); W().frame(10); } W().frame(110);
{ const ec = W().log.filter(l => Math.abs(l.dmg / l.light - 0.3 * 1.1) < 0.01 || Math.abs(l.dmg / l.light - 0.3 * 1.15) < 0.01 || Math.abs(l.dmg / l.light - 0.3 * 1.8) < 0.01).length;
  ok(ec === 3 && E('P.belEchoN') === 0, `Echo: the next 3 hits ring again for 30% (${ec} echoes; ${W().log.map(l => (l.dmg / l.light).toFixed(2)).join('/')})`); }
b = perf('AGE', 1); ok(b === '{}', `rank I: Ash Gold Ember -> no toll ${b}`);
b = perf('AGE', 2); E('P.hp = D.maxHp * 0.5'); const hp0 = E('P.hp'); W().frame(600); const hp1 = E('P.hp');
ok(b.includes('mend') && Math.abs((hp1 - hp0) / E('D.maxHp') - 0.1) < 0.012, `rank II: Mending ${b} heals ${((hp1 - hp0) / E('D.maxHp') * 100).toFixed(1)}% over 10 s`);
E(`P.belNotes = ['A','G','E']`); E('P.state = "idle"; P.anim.set("idle", true)'); I(); W().frame(70);
ok(!(E('P.belBuff.mend') > 0) && E('P.belMendCd') > 0, `Mending again within 60 s: nothing (cooldown ${E('P.belMendCd').toFixed(0)} s)`);
// buffs tick down and end
perf('EE'); W().frame(60 * 31); ok(!(E('P.belBuff.fury') > 0), 'Fury ends after 30 s');

// ---- Encore (III), echo wave (IV), Grand toll (V)
for (const r of [2, 3]) {
  go(r, { dummy: 26 }); E(`P.belNotes = ['A','A']`); I(); W().frame(20); I(); W().frame(110);
  if (r === 2) ok(!sts().includes('wb_encore'), 'rank II: Perform -> I is no Encore');
  else { E('P.belBuff.fury = 5'); ok(sts().includes('wb_encore') && mul('wb_encore')[0] === 1.4, `rank III: Perform -> I -> Encore ${mul('wb_encore')}`); }
}
go(3, { dummy: 26 }); E(`P.belNotes = ['E','E']`); I(); W().frame(20); E('P.belBuff.fury = 4'); I(); W().frame(110);
ok(E('Math.round(P.belBuff.fury)') >= 28, `Encore refreshes Fury to 30 s (${E('P.belBuff.fury').toFixed(1)})`);
for (const r of [3, 4]) {
  go(r, { dummy: 56 }); E(`P.belNotes = ['A']`); I(); W().frame(70);
  const w = W().log.map(l => +(l.dmg / l.light).toFixed(2));
  ok(r === 3 ? w.length === 0 : (w.length === 1 && w[0] === 0.6), `rank ${r}: a foe 56 px away ${r === 3 ? 'is out of the ring' : 'takes the echo wave'} (${w.join('/') || 'nothing'})`);
}
{ let broke = 0;
  go(5, { dummy: 26, d: { breakStance() { broke++; } } }); E(`P.belNotes = ['A','A','E']`); I(); W().frame(70);
  ok(broke === 1, `rank V: a full-staff Perform stuns a small foe (breakStance x${broke})`);
  go(5, { dummy: 26, d: { boss: true } }); E(`P.belNotes = ['A','A','E']`); I(); W().frame(70); const pg = W().log.filter(l => l.st === 'wb_perform').map(l => l.poise)[0];
  go(4, { dummy: 26, d: { boss: true } }); E(`P.belNotes = ['A','A','E']`); I(); W().frame(70); const pn = W().log.filter(l => l.st === 'wb_perform').map(l => l.poise)[0];
  ok(Math.abs(pg - pn - 60) < 1, `rank V: Grand toll adds 60 stance damage to a boss (${pn.toFixed(0)} -> ${pg.toFixed(0)})`); }
// blunt
go(1, { dummy: 26 }); J(); W().frame(40); ok(Math.abs(W().log[0].poise - 18 * 1.3) < 0.6, `bell hits are blunt: the left swing's 18 poise lands as ${W().log[0].poise.toFixed(1)}`);
// Iron hymn: the overhead clang holds through a small hit
for (const iron of [false, true]) {
  go(1, { dummy: 26 }); if (iron) E('P.belBuff.iron = 30'); J(); W().frame(8); J(); W().frame(8); J(); until(() => E("P.state === 'wb_3'")); W().frame(4);
  E('hurtPlayer(Math.round(D.maxHp * 0.1), -1, "test")'); W().frame(1);
  const st = E('P.state'); ok(iron ? st === 'wb_3' : st !== 'wb_3', `Iron hymn ${iron ? 'on' : 'off'}: a 10% hit during the clang -> ${st}`);
}
// wind-up armour
go(1); W().down('heavy'); W().frame(20); E('hurtPlayer(Math.round(D.maxHp * 0.15), -1, "test")'); W().frame(1); const wa = E('P.state'); W().up('heavy'); W().frame(60);
ok(wa === 'wb_kwind', `winding the toll holds through a 15% hit (${wa})`);

// ---- roll, air
go(1, { dummy: 110 }); L(); W().frame(14); J(); W().frame(60);
ok(sts().includes('wb_rollj'), `L -> J -> ringing lunge (${mul('wb_rollj')})`);
go(1, { dummy: 110 }); L(); W().frame(18); K(); W().frame(70);
ok(sts().includes('wb_rollk'), `L -> K -> bell drop at rank I (${mul('wb_rollk')})`);
go(1, { dummy: 22 }); W().tap('jump', 2); W().frame(8); J(); W().frame(40);
ok(sts().includes('wb_air') && notes() === 'A', `air J -> air swing, staff ${notes()}`);
go(1); W().tap('jump', 2); W().frame(18); W().dummy(0); W().down('down'); J(); W().frame(30); W().up('down'); W().frame(40);
ok(sts().includes('wb_down') && E('P.pogoed !== undefined'), `air down J -> bell pogo (${mul('wb_down')})`);
go(1, { dummy: 26 }); W().tap('jump', 2); W().frame(6); K(); W().frame(80);
ok(sts().includes('wb_plunge') && notes() === 'E', `air K onto a foe -> bell plunge ${mul('wb_plunge')} + bounce, staff ${notes()}`);
go(1, { dummy: 42 }); W().tap('jump', 2); W().frame(6); K(); let landed = false; for (let i = 0; i < 90; i++) { W().frame(1); if (E("P.state === 'wb_pland'")) landed = true; }
ok(landed && W().log.length >= 1, `air K to the floor -> landing blow + shock ring reaches a foe 42 px off (${W().log.map(l => l.st + ' ' + (l.dmg / l.light).toFixed(2)).join(', ')})`);

// ---- mashing stops at the finisher; turning between steps
go(1, { dummy: 26 }); { let seen3 = false; for (let f = 0; f < 170; f++) { const st = E('P.state'); if (st === 'wb_3') seen3 = true; if (f % 6 === 0 && (!seen3 || (st === 'wb_3' && E('P.mvT') < 560))) J(1); else W().frame(1); } } W().frame(60);
ok(uniq(sts()).join() === 'wb_1,wb_2,wb_3', `mashing J (not in the clang's last 120 ms) stops at the overhead clang (${uniq(sts()).join(' ')})`);
go(1, { dummy: 26 }); J(); W().frame(6); W().down('left'); J(); W().frame(40); const face = E('P.face'); W().up('left'); W().frame(30);
ok(face === -1 && E("MV.last") === 'wb_2', `holding back during the left swing turns the right swing round (face ${face})`);
// moves don't travel far: the overhead clang chain
go(1); const x0 = E('P.x'); W().down('right'); for (let i = 0; i < 3; i++) { J(); W().frame(10); } W().frame(80); W().up('right');
ok(Math.abs(E('P.x') - x0) < 3 * 36, `J J J while pushing forward travels ${(E('P.x') - x0).toFixed(0)} px over three steps`);
// changing weapon drops the staff and the buffs
go(1); E(`P.belNotes = ['A','E']; P.belBuff = { fury: 20 }`); E("wmEquip('maul', { quiet: true })"); W().frame(2); E("wmEquip('bell', { quiet: true })"); W().frame(2);
ok(E('belNotes().length') === 0 && !(E('P.belBuff.fury') > 0), 'changing weapon drops the staff and the tolls');
// mastery XP, lists
ok(E("WEAPON_UNLOCKS.bell.length") === 5 && E("MV.types.bell.combos.length") >= 20 && E("MV.types.bell.combos.every(c => c.desc.length <= 70)"), `unlocks ${E('WEAPON_UNLOCKS.bell.length')}, combos ${E('MV.types.bell.combos.length')} (desc <= 70 chars)`);
return { pass: out.length - fail.length, fail: fail.length, out };
