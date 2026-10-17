// Greatsword perfect guard: a guard raised <= 150 ms before a blow is free (no stamina, no chip) and the Retort that
// follows hits x1.5 with x1.6 stance damage; a late (ordinary) block keeps the old costs.
// SHOT_HTML=... sh tools/shots/wm/run.sh tools/shots/v17/gsguard/perfect.js <out>
G.tp('K4', 6, 10); W().frame(60);
const out = {}, res = [];
let hid = 0;   // unique blow ids (the prelude pins Math.random, and a repeated id counts as the same blow)
const trial = (lagFrames) => {
  W().reset('greatsword', 1); W().dummy(30);
  W().down('parry'); W().frame(lagFrames);
  const st0 = E('P.st'), hp0 = E('P.hp');
  E(`hurtPlayer(40, -P.face, 'gsg${++hid}', {})`);
  const r = { lag: lagFrames, stLost: Math.round(st0 - E('P.st')), hpLost: Math.round(hp0 - E('P.hp')), bonus: E('P.counterBonus || 0'), pbonus: E('P.counterPoiseBonus || 0') };
  W().frame(2); W().up('parry'); W().log = [];
  W().tap('attack', 1); let st = null; for (let i = 0; i < 60; i++) { W().frame(1); const s = E('P.state'); if (!st && s.startsWith('gs_')) st = s; }
  const L = W().log.filter(l => l.st === 'gs_retort');
  r.move = st; r.retortDmg = L.length ? +L[0].dmg.toFixed(1) : 0; r.retortPoise = L.length ? +L[0].poise.toFixed(1) : 0;
  return r;
};
out.perfect = trial(4);     // ~67 ms after raising
out.edge = trial(9);        // 150 ms
out.late = trial(30);       // 500 ms: an ordinary block
out.moveList = E(`(MV.types.greatsword.combos.find(c => c.name === 'Perfect guard') || {}).desc`);
const ok = (c, m) => res.push((c ? 'OK   ' : 'FAIL ') + m);
ok(out.perfect.stLost === 0 && out.perfect.hpLost === 0, `perfect: no stamina (${out.perfect.stLost}) and no chip (${out.perfect.hpLost})`);
ok(out.perfect.move === 'gs_retort', `perfect: J plays the Retort (${out.perfect.move})`);
ok(out.late.stLost > 0 && out.late.hpLost > 0, `late block keeps its cost: stamina ${out.late.stLost}, chip ${out.late.hpLost}`);
ok(out.late.move === 'gs_retort', `late block: J still plays the Retort (${out.late.move})`);
ok(Math.abs(out.perfect.retortDmg / out.late.retortDmg - 1.5) < 0.02, `perfect Retort damage x${(out.perfect.retortDmg / out.late.retortDmg).toFixed(2)} (${out.perfect.retortDmg} vs ${out.late.retortDmg})`);
ok(Math.abs(out.perfect.retortPoise / out.late.retortPoise - 1.6) < 0.02, `perfect Retort stance x${(out.perfect.retortPoise / out.late.retortPoise).toFixed(2)}`);
ok(out.edge.stLost === 0, `150 ms is still perfect (stamina ${out.edge.stLost})`);
ok(!!out.moveList, 'Move List row: ' + out.moveList);
out.errs = E('(window.__errs || []).length');
return { res, out };
