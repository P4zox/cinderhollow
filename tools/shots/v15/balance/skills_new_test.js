// v15 phase 2b: skill-tree nodes on the five new types (bow arrows, Hundred fists, Hone, draw, styles).
// SHOT_HTML=web/dist/v15_balance.html sh tools/shots/wm/run.sh tools/shots/v15/balance/skills_new_test.js /tmp/skn
const R = {}, fail = [];
const rec = (id, txt, ok) => { R[id] = txt + (ok ? '' : '  <-- FAIL'); if (!ok) fail.push(id); };
const setSk = sk => E('SAVE.skills = ' + JSON.stringify(sk) + '; refreshDerived(false); P.hp = D.maxHp; P.st = D.maxSt; P.fp = D.maxFp');
const prep = (ty, sk, dx = 44, rank = 1) => { W().reset(ty, rank); arena(); W().reset(ty, rank); setSk(sk); E('D.maxSt = 1e4; P.st = 1e4'); if (dx !== null) { W().dummy(dx); E('window.__wm.follow = ' + dx); } };
// ---- Bloodthirst on arrows: each arrow's bleed follows its own multiplier, not the move playing when it lands
{ prep('bow', ['bloodthirst']);
  const v = E("[skBleedUnits(false, 0.4), skBleedUnits(true, 2.0), bleedAmt(false)]");
  rec('bloodthirst.bow', `quick-shot arrow (0.4) ${v[0].toFixed(1)}, lv3 power (2.0) ${v[1].toFixed(1)}, a bare call ${v[2].toFixed(1)}`, Math.abs(v[0] - 4.8) < 0.3 && Math.abs(v[1] - 24) < 0.5); }
// ---- Charged Arts: the bow's draw climbs faster; the Switch Axe's Hone does NOT (noSkillCharge)
for (const sk of [[], ['charged_arts']]) {
  prep('bow', sk); E('P.bwLv = 1; P.bwDrawLv = 1; P.bwDrawMs = 0'); W().frame(30); W().down('heavy'); let f = 0; for (; f < 120 && !(E('P.bwDrawLv') >= 3); f++) W().frame(1); W().up('heavy'); W().frame(40);
  R['bow draw lv3 ' + (sk.length ? '+CA' : '-')] = Math.round(f * 16.67) + ' ms';
  prep('saxe', sk, 30); E('P.sxG = 0; P.sxAxe = false; P.sxLock = false'); W().down('heavy'); W().frame(60); W().up('heavy'); W().frame(2);
  R['saxe hone 1 s ' + (sk.length ? '+CA' : '-')] = E('P.sxG').toFixed(1) + ' gauge';
}
rec('charged_arts.bow', R['bow draw lv3 -'] + ' -> ' + R['bow draw lv3 +CA'], parseInt(R['bow draw lv3 +CA']) < parseInt(R['bow draw lv3 -']) * 0.8);
rec('charged_arts.hone', R['saxe hone 1 s -'] + ' -> ' + R['saxe hone 1 s +CA'], Math.abs(parseFloat(R['saxe hone 1 s -']) - parseFloat(R['saxe hone 1 s +CA'])) < 1);
// ---- Blade Dancer: speeds the Swift jabs (light), not the Hundred fists loop; bow shots (noHit, but they carry dmg) count
{ const sp = E("(() => { SAVE.skills = ['blade_dancer']; wmEquip('fist', { quiet: true }); const a = mvSpeed(ATK.ft_jab), b = mvSpeed(ATK.ft_hundred); wmEquip('bow', { quiet: true }); const c = mvSpeed(ATK.bw_1), d = mvSpeed(ATK.bw_deflect); return [a, b, c, d]; })()");
  rec('blade_dancer.new', `fist jab x${sp[0].toFixed(2)}, Hundred fists x${sp[1].toFixed(2)}, bow quick shot x${sp[2].toFixed(2)}, limb deflect x${sp[3].toFixed(2)}`, sp[0] > 1.1 && sp[1] === 1 && sp[2] > 1.1 && sp[3] === 1); }
// ---- Measured Cut on the bow: only the first shot of a J J J volley is an opener (arrows used to count as "no strike")
{ prep('bow', ['measured_cut']); W().frame(60);
  const n = []; for (let i = 0; i < 3; i++) { W().tap('attack', 2); W().frame(2); n.push(E('P.skOpenN === P.skMvN')); W().frame(16); }
  W().frame(60); rec('measured_cut.bow', 'opener flags ' + n.join('/'), n[0] === true && n[1] === false && n[2] === false); }
// ---- Deflect / Executioner: the bow's limb deflect pays only on a parryable blow
{ prep('bow', ['deflect'], 30); E('P.st = 20; P.hp = D.maxHp * 0.5; P.skDefT = -9'); W().tap('parry', 2); W().frame(2); const h0 = E('P.hp');
  E("hurtPlayer(20, -1, 'skn1', {})"); const h1 = E('P.hp');
  prep('bow', ['deflect'], 30); E('P.st = 20; P.hp = D.maxHp * 0.5; P.skDefT = -9'); W().tap('parry', 2); W().frame(2); const h2 = E('P.hp');
  E("hurtPlayer(20, -1, 'skn2', { parryable: true })"); const h3 = E('P.hp');
  rec('deflect.bow', `unparryable: hp +${(h1 - h0).toFixed(0)}; parryable: hp +${(h3 - h2).toFixed(0)}`, h1 - h0 === 0 && h3 - h2 > 0); }
return { fail, R };
