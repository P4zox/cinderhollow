// v15 Switch Axe: every move from real inputs, the Switch Gauge rules, rank gates, mashing, turning, the two overlays.
// Run: SHOT_HTML=web/dist/v15_saxe.html sh tools/shots/wm/run.sh tools/shots/v15/saxe/routes.js tools/shots/v15/saxe/out
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
arena();
const go = (r = 1, o = {}) => { W().reset('saxe', r); E('P.x = 140; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; sxReset(); MV.sxWhiffs = 0'); if (o.g !== undefined) E(`P.sxG = ${o.g}`); if (o.axe) E('sxSetAxe(true); P.sxG = ' + (o.g ?? 100)); W().frame(2); W().log = []; };
const G_ = () => +E('P.sxG').toFixed(2);
const sts = () => W().log.map(l => l.st);
const uniq = a => [...new Set(a)];
const dm = st => +(W().log.filter(l => l.st === st).reduce((a, l) => a + l.dmg / l.light, 0)).toFixed(2);
const runUntilIdle = (max = 300) => { for (let i = 0; i < max; i++) { W().frame(1); if (['idle', 'run', 'land'].includes(E('P.state'))) return i; } return max; };
const pressAt = (b, st, msLeft) => {   // press button b when state st has <= msLeft of its total left
  for (let i = 0; i < 200; i++) { if (E('P.state') === st && E('ATK[P.state].mv.total - P.mvT') <= msLeft) break; W().frame(1); }
  W().tap(b, 2);
};

// ---- 1. equip + the blade chain
go(1); ok(E('wtype()') === 'saxe' && E('SAVE.weapon') === 'gravegrinder' && !E('P.sxAxe') && G_() === 0, 'equip: Gravegrinder in blade mode, gauge 0');
W().dummy(26);
for (let i = 0; i < 4; i++) { W().tap('attack', 2); W().frame(8); }
runUntilIdle();
ok(uniq(sts()).join() === 'sx_1,sx_2,sx_3,sx_4', 'J J J J -> ' + uniq(sts()).join(' ') + ' dmg ' + ['sx_1', 'sx_2', 'sx_3', 'sx_4'].map(dm).join('/'));
const gChain = G_();
ok(gChain >= 24 && gChain <= 40, `J J J J (tapped early) fills ${gChain} (4 x4 + rush 10 = 26, beats more)`);

// ---- 2. on the beat: presses in the last 150 ms
go(1); W().dummy(26); W().tap('attack', 2); pressAt('attack', 'sx_1', 120); pressAt('attack', 'sx_2', 120); pressAt('attack', 'sx_3', 120);
runUntilIdle();
const gBeat = G_();
ok(uniq(sts()).join() === 'sx_1,sx_2,sx_3,sx_4' && gBeat >= 36, `J J J J on the beat fills ${gBeat} (4 + 7 + 7x2 + 13 = 38)`);

// ---- 3. whiff, hurt, bleed
go(1, { g: 50 }); W().dummy(70); W().tap('attack', 2); runUntilIdle(); W().frame(2);
ok(Math.abs(G_() - 40) < 0.6, `a whiff with a foe near: 50 -> ${G_()} (-10)`);
go(1, { g: 50 }); E('enemies = enemies.filter(e => !e.wmDummy)'); W().tap('attack', 2); runUntilIdle(); W().frame(2);
ok(Math.abs(G_() - 50) < 0.6, `a swing with nobody about costs nothing: 50 -> ${G_()}`);
go(1, { g: 50 }); E('P.inv = 0; hurtPlayer(10, -1, "sxT1")'); W().frame(2);
ok(Math.abs(G_() - 25) < 0.6, `taking a hit: 50 -> ${G_()} (-25)`);
go(1, { g: 50 }); W().frame(60 * 3);
ok(G_() < 50 && G_() > 45, `bleed after 2 s idle: 50 -> ${G_()} over 3 s (-4/s after 2 s)`);

// ---- 4. K, K K, J K, hold K = Hone
go(1); W().dummy(26); W().tap('heavy', 2); runUntilIdle();
ok(uniq(sts()).join() === 'sx_heavy', 'K -> Phial thrust ' + dm('sx_heavy'));
go(1); W().dummy(26); W().tap('heavy', 2); W().frame(10); W().tap('heavy', 2); runUntilIdle();
ok(uniq(sts()).join() === 'sx_heavy,sx_twist' && W().log.filter(l => l.st === 'sx_twist').length === 2, 'K K -> Ratchet twist (2 bites) ' + dm('sx_twist'));
ok(G_() >= 15, `K K fills ${G_()} (thrust 4 + twist 12)`);
go(1); W().dummy(26); W().tap('attack', 2); W().frame(8); W().tap('heavy', 2); runUntilIdle();
ok(uniq(sts()).join() === 'sx_1,sx_hook', 'J K -> Hook heave ' + dm('sx_hook'));
go(1); W().dummy(26); const hx0 = E('P.x'); W().down('heavy'); W().frame(60 * 2); const honeSt = E('P.state'), gHone = G_(); W().up('heavy'); W().frame(4);
ok(honeSt === 'sx_hone' && gHone > 15 && gHone < 20 && Math.abs(E('P.x') - hx0) < 6, `hold K 2 s -> Hone: gauge ${gHone} (10/s), rooted (moved ${(E('P.x') - hx0).toFixed(1)} px), released: ${E('P.state')}`);
go(1, { g: 50 }); W().down('heavy'); W().frame(40); E('P.inv = 0; hurtPlayer(10, -1, "sxT2")'); W().frame(2); W().up('heavy');
ok(E('P.state') !== 'sx_hone' && G_() < 32, `a hit cancels the Hone and costs 25: ${G_()}`);

// ---- 5. Ratchet cut (II): J J (pause) J
go(1); W().dummy(26); W().tap('attack', 2); W().frame(8); W().tap('attack', 2); for (let i = 0; i < 80 && E('P.state') !== 'idle'; i++) W().frame(1); W().frame(12); W().tap('attack', 2); runUntilIdle();
ok(!sts().includes('sx_ratchet'), 'rank I: J J (pause) J has no Ratchet cut (' + uniq(sts()).join(' ') + ')');
go(2); W().dummy(26); W().tap('attack', 2); W().frame(8); W().tap('attack', 2); for (let i = 0; i < 80 && E('P.state') !== 'idle'; i++) W().frame(1); W().frame(12); W().tap('attack', 2); runUntilIdle();
ok(W().log.filter(l => l.st === 'sx_ratchet').length === 3, 'rank II: J J (pause) J -> Ratchet cut, 3 bites ' + dm('sx_ratchet'));

// ---- 6. I: dry rev below 100; lock at 100; Morph slash
go(1, { g: 60 }); W().tap('parry', 2); W().frame(4);
ok(['idle', 'run'].includes(E('P.state')) && !E('P.sxAxe') && E('MV.sxDry') >= 1, 'I below 100: a dry rev, nothing happens (' + E('P.state') + ')');
go(1, { g: 97 }); W().dummy(26); W().tap('attack', 2); runUntilIdle();
ok(G_() === 100 && E('P.sxLock'), 'reaching 100 locks the gauge: ' + G_());
E('P.inv = 0; hurtPlayer(10, -1, "sxT3")'); W().frame(70);
ok(G_() === 100, 'locked: a hit and idling cost nothing: ' + G_());
W().log = []; W().tap('parry', 2); runUntilIdle();
ok(E('P.sxAxe') && sts().includes('sx_morph') && Math.abs(dm('sx_morph') - 2.0) < 0.05, 'I at 100 -> Morph slash ' + dm('sx_morph') + ', axe mode: ' + E('P.sxAxe') + ', gauge ' + G_());
ok(E("sheet('wpn_gravegrinder').name") === (E('!!ASSETS.wpn_gravegrinder_axe') ? 'wpn_gravegrinder_axe' : 'wpn_gravegrinder'), 'axe mode draws the _axe overlay: ' + E("sheet('wpn_gravegrinder').name"));
ok(E('mvIdleTag("idle")') === (E("pHas('sx_aidle')") ? 'sx_aidle' : 'idle') && E('mvWalkMul()') === 0.75, 'axe idle / walk tags, walk 75%');

// ---- 7. axe mode: J J J, K, K K (II), hold K grind, up J, air J, L, L -> J
go(1, { axe: true }); W().dummy(28); for (let i = 0; i < 3; i++) { W().tap('attack', 2); W().frame(12); } runUntilIdle();
ok(uniq(sts()).join() === 'sx_a1,sx_a2,sx_a3' && W().log.filter(l => l.st === 'sx_a3').length === 5, 'axe J J J -> ' + uniq(sts()).join(' ') + ' dmg ' + ['sx_a1', 'sx_a2', 'sx_a3'].map(dm).join('/'));
ok(G_() < 100 - 12 && G_() > 60, `axe J J J drains the gauge: 100 -> ${G_()}`);
go(1, { axe: true }); W().dummy(28); W().tap('heavy', 2); runUntilIdle();
ok(W().log.filter(l => l.st === 'sx_arev').length === 4, 'axe K -> Rev thrust, 4 bites ' + dm('sx_arev'));
go(1, { axe: true }); W().dummy(28); W().tap('heavy', 2); W().frame(12); W().tap('heavy', 2); runUntilIdle();
ok(!sts().includes('sx_rip'), 'rank I: axe K K has no Ripping heave');
go(2, { axe: true }); W().dummy(28); W().tap('heavy', 2); W().frame(12); W().tap('heavy', 2); runUntilIdle();
ok(sts().includes('sx_rip'), 'rank II: axe K K -> Ripping heave ' + dm('sx_rip'));
go(1, { axe: true }); W().dummy(28); W().down('heavy'); W().frame(60 * 2); const gst = E('P.state'), gG = G_(); W().up('heavy'); W().frame(4);
const grindN = W().log.filter(l => l.st === 'sx_grind' || l.st === 'idle').length;
ok(gst === 'sx_grind' && grindN >= 18 && gG < 66, `hold K (axe) -> chainsaw grind: ${grindN} bites in ~1.7 s (${dm('sx_grind') || (W().log.reduce((a, l) => a + l.dmg / l.light, 0)).toFixed(2)} dmg), gauge 100 -> ${gG}`);
go(1, { axe: true }); W().dummy(20); W().down('up'); W().tap('attack', 2); W().up('up'); runUntilIdle();
ok(sts().includes('sx_aup'), 'axe up J -> Rising grinder ' + dm('sx_aup'));
go(1, { axe: true }); W().dummy(22); W().tap('jump', 2); W().frame(8); W().tap('attack', 2); W().frame(50);
ok(sts().includes('sx_aair'), 'axe air J -> Falling cleave ' + dm('sx_aair'));
go(1, { axe: true }); const sx0 = E('P.x'); W().tap('roll', 2); W().frame(4); const dodgeTag = E('P.anim.tag'); W().frame(40);
ok(dodgeTag === (E("pHas('sx_astep')") ? 'sx_astep' : 'roll') && Math.abs(E('P.x') - sx0) < 45, `axe L -> heavy sidestep (${dodgeTag}), ${(E('P.x') - sx0).toFixed(1)} px`);
go(1, { axe: true }); W().dummy(60); W().tap('roll', 2); W().frame(16); W().tap('attack', 2); W().frame(80);
ok(sts().includes('sx_a1'), 'axe L -> J -> the overhead');
go(1); W().dummy(110); W().tap('roll', 2); W().frame(14); W().tap('attack', 2); W().frame(50);
ok(sts().includes('sx_rollj'), 'blade L -> J -> Lunging edge ' + dm('sx_rollj'));
go(1); W().dummy(20); W().down('up'); W().tap('attack', 2); W().up('up'); runUntilIdle();
ok(sts().includes('sx_up'), 'blade up J -> Skyward edge');
go(1); W().dummy(22); W().tap('jump', 2); W().frame(8); W().tap('attack', 2); W().frame(40);
ok(sts().includes('sx_air'), 'blade air J -> Air edge');
go(1); W().tap('jump', 2); W().frame(18); W().dummy(0); W().down('down'); W().tap('attack', 2); W().frame(30); W().up('down'); W().frame(40);
ok(sts().includes('sx_down'), 'air down J -> pogo');

// ---- 8. I in axe mode: Morph back (< 40 / rank < III), Full Release (III, >= 40), Grinding halo (V); vent at 0
go(1, { axe: true, g: 80 }); W().dummy(26); W().tap('parry', 2); runUntilIdle();
ok(sts().includes('sx_unmorph') && !E('P.sxAxe') && G_() === 0, 'rank I, axe I -> Morph back ' + dm('sx_unmorph') + ', blade, gauge 0');
go(3, { axe: true, g: 30 }); W().dummy(26); W().tap('parry', 2); runUntilIdle();
ok(sts().includes('sx_unmorph') && !E('P.sxAxe'), 'rank III, gauge 30: axe I -> Morph back');
for (const g of [45, 100]) {
  go(3, { axe: true, g }); W().dummy(26); W().tap('parry', 2); runUntilIdle(240);
  const n = W().log.filter(l => l.st === 'sx_release').length;
  ok(n === 9 && !E('P.sxAxe') && G_() === 0, `rank III, gauge ${g}: Full Release ${n} hits = ${dm('sx_release')} (want ~${(3 + 3 * (g - 40) / 60).toFixed(1)}, the gauge drains a little before I), blade after, gauge ${G_()}`);
}
go(5, { axe: true, g: 70 }); W().dummy(26); W().tap('parry', 2); runUntilIdle(240);
ok(G_() === 30 && W().log.length >= 10, `rank V: Grinding halo refunds 30 (${G_()}), ring burst hits (${W().log.length} hits)`);
go(1, { axe: true, g: 3 }); W().frame(60);
ok(E('MV.sxVents') >= 1 && !E('P.sxAxe'), 'gauge runs dry -> vented (' + E('P.state') + '), blade');
go(1, { axe: true, g: 3 }); let ventMs = 0; for (let i = 0; i < 120; i++) { W().frame(1); if (E('P.state') === 'sx_vent') ventMs += 1000 / 60; }
ok(ventMs > 550 && ventMs < 680, `the vent stagger lasts ${ventMs.toFixed(0)} ms`);
go(4, { axe: true, g: 100 }); W().frame(60 * 5); const g4 = G_();
go(1, { axe: true, g: 100 }); W().frame(60 * 5); const g1 = G_();
ok(Math.abs((100 - g4) - 0.7 * (100 - g1)) < 1, `Overdrive (IV): 5 s idle in axe drains ${(100 - g4).toFixed(1)} vs ${(100 - g1).toFixed(1)}`);

// ---- 9. mashing stops at finishers; turning between steps
go(1); W().dummy(26); for (let i = 0; i < 40; i++) { if (i % 3 === 0) W().tap('attack', 1); else W().frame(1); } runUntilIdle();
const mash = uniq(sts());
ok(mash.join() === 'sx_1,sx_2,sx_3,sx_4', 'mash J: stops at the Edge rush: ' + sts().join(' '));
go(1); W().dummy(26); W().tap('attack', 2); W().frame(6); E('held.add("left")'); W().tap('attack', 2); for (let i = 0; i < 40 && E('P.state') === 'sx_1'; i++) W().frame(1); W().frame(3);
ok(E('P.state') === 'sx_2' && E('P.face') === -1, 'holding back turns the next step round (' + E('P.state') + ', face ' + E('P.face') + ')'); E('held.delete("left")');

// ---- 10. lunges (pushing forward) stay <= ~36 px unless a dash
const lunge = (ids, axe, presses) => {
  go(2, axe ? { axe: true } : {}); E('enemies = enemies.filter(e => !e.wmDummy)'); E('held.add("right")');
  const x0 = E('P.x'); for (const p of presses) { W().tap(p, 2); W().frame(4); } runUntilIdle(); E('held.delete("right")');
  return +(E('P.x') - x0).toFixed(1);
};
ok(lunge(0, false, ['attack', 'attack', 'attack', 'attack']) < 4 * 36, 'blade chain pushing forward travels ' + lunge(0, false, ['attack', 'attack', 'attack', 'attack']) + ' px over 4 steps');

out.push('', 'fails: ' + fail.length);
return out;
