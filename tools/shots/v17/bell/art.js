// v17 Warbell art, Funeral Peal: from the art key with the bell equipped, FP cost, tap and hold, damage, both rings, the notes
// it writes into the staff, the stun, missile swallowing, ends in idle, old saves corrected; then snapshots.
// Run: SHOT_HTML=$PWD/web/dist/v17_bell.html sh tools/shots/wm/run.sh tools/shots/v17/bell/art.js tools/shots/v17/bell/out
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
arena();
const go = (r = 1) => {
  W().reset('bell', r);
  E('P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.belNotes = []; P.belBuff = {}; P.belEchoN = 0; MV.later = []; P.cds = {}; projectiles.length = 0');
  E('enemies = enemies.filter(e => !e.wmDummy && !e.fplT)'); W().frame(2); W().log = [];
};
const notes = () => E('belNotes().join("")');
const idle = () => E("['idle','run','land'].includes(P.state)");
const until = (fn, max = 240) => { let i = 0; for (; i < max && !fn(); i++) W().frame(1); return i; };
const art = (holdF = 0) => { W().down('art'); W().frame(Math.max(1, holdF)); W().up('art'); };
const mulsOf = () => W().log.filter(l => l.st === 'art').map(l => +(l.dmg / l.light).toFixed(2));
// a second test foe that logs like the wm dummy (W().dummy keeps only one)
const foe2 = dx => E(`(() => { const W = window.__wm, d = { ...enemies.find(e => e.wmDummy) }; d.wmDummy = false; d.fplT = true; d.x = P.x + ${dx};
  d.hurtbox = function () { return rect(this.x - 8, this.y - 40, this.x + 8, this.y); }; d.hit = function (info) { W.log.push({ st: P.state, dmg: info.dmg, light: D.light, kind: info.kind, x: this.x }); }; enemies.push(d); })()`);

// ---- registration and the save lock
go();
ok(E("SAVE.art") === 'funeral_peal' && E("WEAPONS.dirge_bell.art") === 'funeral_peal' && E("WTYPE_INFO.bell.art") === 'funeral_peal', `the Warbell's art is Funeral Peal (SAVE.art ${E('SAVE.art')})`);
E("SAVE.art = 'warcry'"); W().frame(2);
ok(E("SAVE.art") === 'funeral_peal', `an old save holding the borrowed War Cry is corrected (${E('SAVE.art')})`);
ok(E("ARTS.funeral_peal.fp") === 14 && E("cdBase('art','funeral_peal')") === 6.5, `fp ${E('ARTS.funeral_peal.fp')} cd ${E("cdBase('art','funeral_peal')")}`);
ok(E("(() => { for (const n of ICON_SHEETS) { const s = sheet(n); if (s.ok && s.has('a_funeral_peal')) return n; } return null; })()") === 'ui_icons17_bell', 'icon a_funeral_peal found through ICON_SHEETS');
ok(E("ART_IMPL.funeral_peal && ART_IMPL.tolling_blow && ART_IMPL.funeral_peal !== ART_IMPL.tolling_blow"), 'no collision with the Bell Hammer\'s tolling_blow');
const own = E("pHas('art_funeral_peal')");
out.push(`info  dedicated tag art_funeral_peal in the sheet: ${own} (else the wb_toll fallback plays)`);

// ---- tap, a foe in front: Ember, one hit of 2.8, the FP spent, back to idle
go(); W().dummy(30);
const fp0 = E('P.fp'); art(1); const st1 = E('P.state'); const tag1 = E('P.anim.tag');
const nIdle = until(idle);
ok(st1 === 'art' && fp0 - E('P.fp') === 14, `tap: art starts (${st1}, ${tag1}), costs ${fp0 - E('P.fp')} FP`);
ok(mulsOf().length === 1 && Math.abs(mulsOf()[0] - 2.8) < 0.05 && W().log[0].kind === 'heavy', `tap: one blunt hit ${mulsOf().join('/')} x light (kind ${W().log[0] && W().log[0].kind})`);
ok(notes() === 'E', `tap, foe ahead: staff ${notes()} (Ember)`);
ok(idle() && nIdle < 200, `ends in ${E('P.state')} after ${nIdle} frames (${(nIdle / 60).toFixed(2)} s)`);
ok(E("cdLeft('art','funeral_peal')") > 4.5, `cooldown running (${(+E("cdLeft('art','funeral_peal')")).toFixed(2)} s left)`);

// ---- tap, a foe behind: the back ring rings Ash
go(); W().dummy(-40); art(1); until(idle);
ok(mulsOf().length === 1 && notes() === 'A', `tap, foe behind: hit ${mulsOf().join('/')}, staff ${notes()} (Ash)`);
// ---- tap, both sides: Ember then Ash; a note per foe, each foe once
go(); W().dummy(30); foe2(-46); art(1); until(idle);
ok(W().log.length === 2 && notes() === 'EA', `tap, both sides: ${W().log.length} hits, staff ${notes()}`);
// ---- a whiff rings nothing, and the peal does not empty or play the staff
go(); E("P.belNotes = ['G']"); art(1); until(idle);
ok(W().log.length === 0 && notes() === 'G' && !Object.keys(E('P.belBuff') || {}).length, `whiff: no hit, staff kept (${notes()}), no toll played`);
// ---- range: tap reaches ~88 px from the lip, not 120
go(); W().dummy(120); art(1); until(idle);
ok(W().log.length === 0, `tap does not reach a foe 120 px away (${W().log.length} hits)`);
// ---- cap: three foes, tap writes two notes
go(); W().dummy(30); foe2(50); foe2(-40); art(1); until(idle);
ok(W().log.length === 3 && notes().length === 2, `tap, three foes: ${W().log.length} hits, ${notes().length} notes (${notes()})`);

// ---- hold: charged, further, harder, three notes
go(); W().dummy(120); foe2(-60); foe2(60);
art(75); const ch = E('P.artCharged'); until(idle);
ok(ch && mulsOf().length === 3 && mulsOf().every(m => Math.abs(m - 3.4) < 0.05), `hold: charged ${ch}, hits ${mulsOf().join('/')} (120 px foe reached)`);
ok(notes().length === 3, `hold: ${notes().length} notes (${notes()})`);

// ---- hold stuns a small real foe; a tap doesn't
const realFoe = (dx) => { E(`(() => { const e = makeEnemy('hollow_soldier', P.x + ${dx}, P.y, 'fpl_' + Math.random()); e.hp = e.maxHp = 30000; e.fplT = true; enemies.push(e); window.__t = e; })()`); W().frame(1); };
go(); realFoe(40); art(1); until(() => E('__t.hp') < 30000, 60); const tapStun = E('__t.gStun || 0'); until(idle);
go(); realFoe(40); art(75); until(() => E('__t.hp') < 30000, 60); const holdStun = E('__t.gStun || 0'); until(idle);
ok(!(tapStun > 0) && holdStun > 1, `stun: tap ${(+tapStun).toFixed(2)} s, hold ${(+holdStun).toFixed(2)} s`);

// ---- the ring swallows an enemy missile in its path
go(); E("projectiles.push({ owner: 'enemy', kind: 'arrow', x: P.x + 60, y: P.y - 14, vx: -20, vy: 0, dmg: 10, life: 3, r: 3, t: 0, id: 99991 })");
art(1); until(() => !E("projectiles.some(p => p.id === 99991 && p.life > 0)"), 60);
ok(!E("projectiles.some(p => p.id === 99991 && p.life > 0)") && E('P.hp') === E('D.maxHp'), 'the ring swallows an arrow flying at the knight');
until(idle);

// ---- not enough FP / cooldown: denied, no state change
go(); E('P.fp = 5'); art(1); ok(E('P.state') !== 'art', `5 FP: denied (${E('P.state')})`);

// ---- it feeds the Perform: Ember Ember from the peal -> Fury
go(); W().dummy(30); foe2(44); art(1); until(idle); const pre = notes(); W().tap('parry'); until(idle);
ok(pre === 'EE' && E('P.belBuff.fury') > 25, `peal ${pre} -> Perform plays Fury (${(+E('P.belBuff.fury')).toFixed(1)} s)`);
// ---- in the air: the bell waits for the floor
go(); E('P.y -= 40; P.ground = false; P.vy = 0'); W().dummy(30); E('enemies.find(e => e.wmDummy).y = 304'); art(1); until(idle, 300);
ok(idle() && W().log.length === 1, `started airborne: lands, then strikes (${W().log.length} hit), ends ${E('P.state')}`);

out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
