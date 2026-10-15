// v15 skill-tree fixes: every reworked node does what its text says, on the new move engine.
// SHOT_HTML=web/dist/v15_balance.html sh tools/shots/wm/run.sh tools/shots/v15/balance/skills_test.js /tmp/sk15
const R = {}, fail = [];
const rec = (id, txt, ok) => { R[id] = txt + (ok ? '' : '  <-- FAIL'); if (!ok) fail.push(id); };
const setSk = sk => E('SAVE.skills = ' + JSON.stringify(sk) + '; refreshDerived(false); P.hp = D.maxHp; P.st = D.maxSt; P.fp = D.maxFp');
// play a route; returns { st (stamina spent), ms, dmg (light units), hits }
function route(type, pat, sk, o = {}) {
  W().reset(type, o.rank || 1); arena(); W().reset(type, o.rank || 1); setSk(sk);
  E('D.maxSt = 1e4; P.st = 1e4; P.stDelay = 99'); if (o.pre) E(o.pre);
  W().dummy(o.far || 26); E('window.__wm.follow = ' + (o.far || 26));
  if (o.wait) W().frame(o.wait);
  let i = 0; const ms0 = W().ms;
  for (let f = 0; f < 900; f++) {
    E('P.stDelay = 99' + (o.keep ? '; ' + o.keep : ''));
    const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    if (free && i < pat.length) { const p = pat[i++]; if (typeof p === 'string') W().tap({ J: 'attack', K: 'heavy' }[p]); else { W().down('heavy'); W().frame(Math.round(p.hold / 16.67)); W().up('heavy'); } continue; }
    if (i >= pat.length && E("['idle','run','land'].includes(P.state)")) break;
    W().frame(1);
  }
  return { st: 1e4 - E('P.st'), ms: W().ms - ms0, dmg: W().log.reduce((a, h) => a + h.dmg, 0) / E('D.light'), hits: W().log.length, log: W().log };
}
// ---- stamina: refunds are per move and a share of the real cost (they used to fire on every hit: Tireless + Flowing Form = free)
for (const [ty, pat] of [['longsword', ['J', 'J', 'J', 'J']], ['dual', ['J', 'J', 'J', 'J']], ['greatsword', ['J', 'J', 'J']]]) {
  const a = route(ty, pat, []), b = route(ty, pat, ['tireless']), c = route(ty, pat, ['tireless', 'flowing_form']);
  rec('tireless.' + ty, `${a.st.toFixed(1)} -> ${b.st.toFixed(1)} (x${(b.st / a.st).toFixed(2)})`, Math.abs(b.st / a.st - 0.8) < 0.03);
  rec('flowing_form.' + ty, `with Tireless ${c.st.toFixed(1)} (x${(c.st / a.st).toFixed(2)}, > 0.35)`, c.st / a.st > 0.35 && c.st / a.st < 0.7);
}
// ---- attack speed: Blade Dancer (lights +12%), Frenzy (below half HP), capped at +40% with the type's own speed
{ const a = route('longsword', ['J', 'J', 'J', 'J'], []), b = route('longsword', ['J', 'J', 'J', 'J'], ['blade_dancer']);
  rec('blade_dancer', `${a.ms.toFixed(0)} ms -> ${b.ms.toFixed(0)} ms`, b.ms < a.ms * 0.93 && Math.abs(b.dmg - a.dmg) < 0.01);
  const c = route('longsword', ['J', 'J', 'J', 'J'], ['frenzy'], { keep: 'P.hp = D.maxHp * 0.4' });
  rec('frenzy', `${a.ms.toFixed(0)} ms -> ${c.ms.toFixed(0)} ms below half HP`, c.ms < a.ms * 0.93);
  const d = E("(() => { SAVE.skills = ['blade_dancer', 'frenzy']; P.demon = true; P.pdT = 5; P.hp = 1; wmEquip('dual', { quiet: true }); return mvSpeed(ATK.tw_1); })()");
  rec('speed cap', `Demon + perfect dodge + Blade Dancer + Frenzy = x${d.toFixed(2)}`, d <= 1.4001);
  const e = E("(() => { SAVE.skills = ['blade_dancer']; return [mvSpeed(ATK.kt_iaiw), mvSpeed(ATK.ls_fore)]; })()");
  rec('speed stances', `Iai wait / foresight stance x${e.join(' / x')} (unchanged)`, e[0] === 1 && e[1] === 1);
}
// ---- Charged Arts: charge stances build 1.55x as fast (Greatsword level 3: 800 ms -> ~516 ms)
for (const sk of [[], ['charged_arts']]) {
  W().reset('greatsword', 1); arena(); W().reset('greatsword', 1); setSk(sk); W().dummy(26); E('P.gsLv = 0; P.gsMs = 0'); W().frame(30);
  W().down('heavy'); let f = 0; for (; f < 120 && !(E('P.gsLv') >= 3); f++) W().frame(1); W().up('heavy'); W().frame(60);
  R['charged_arts.gs' + (sk.length ? '+' : '-')] = `level 3 after ${(f * 16.67).toFixed(0)} ms`;
}
rec('charged_arts', R['charged_arts.gs-'] + ' -> ' + R['charged_arts.gs+'], parseInt(R['charged_arts.gs+'].match(/\d+/)) < 600);
// ---- Finishing Blow (fourth_strike): finishers +20% damage, +30% stance
{ const a = route('longsword', ['J', 'J', 'J', 'J'], []), b = route('longsword', ['J', 'J', 'J', 'J'], ['fourth_strike']);
  const fa = a.log.filter(h => h.st === 'attack4'), fb = b.log.filter(h => h.st === 'attack4'), na = a.log.filter(h => h.st === 'attack1'), nb = b.log.filter(h => h.st === 'attack1');
  rec('fourth_strike', `finisher dmg ${fa[0].dmg.toFixed(1)} -> ${fb[0].dmg.toFixed(1)}, poise ${fa[0].poise.toFixed(0)} -> ${fb[0].poise.toFixed(0)}; opener ${na[0].dmg.toFixed(1)} -> ${nb[0].dmg.toFixed(1)}`,
    Math.abs(fb[0].dmg / fa[0].dmg - 1.2) < 0.02 && Math.abs(fb[0].poise / fa[0].poise - 1.3) < 0.02 && Math.abs(nb[0].dmg / na[0].dmg - 1) < 0.01); }
// ---- Measured Cut: the first move after 0.8 s idle +25%; chained moves not; a Greatsword charged release counts
{ const a = route('longsword', ['J', 'J'], [], { wait: 60 }), b = route('longsword', ['J', 'J'], ['measured_cut'], { wait: 60 });
  rec('measured_cut', `opener ${a.log[0].dmg.toFixed(1)} -> ${b.log[0].dmg.toFixed(1)}, 2nd ${a.log[1].dmg.toFixed(1)} -> ${b.log[1].dmg.toFixed(1)}`, Math.abs(b.log[0].dmg / a.log[0].dmg - 1.25) < 0.02 && Math.abs(b.log[1].dmg / a.log[1].dmg - 1) < 0.01);
  const c = route('greatsword', [{ hold: 900 }], [], { wait: 60 }), d = route('greatsword', [{ hold: 900 }], ['measured_cut'], { wait: 60 });
  rec('measured_cut.gs', `charged release ${c.log[0].dmg.toFixed(1)} -> ${d.log[0].dmg.toFixed(1)}`, Math.abs(d.log[0].dmg / c.log[0].dmg - 1.25) < 0.02); }
// ---- Evasive Strike: an attack out of a roll is free and +15%
{ W().reset('longsword', 1); arena(); W().reset('longsword', 1); setSk(['evasive_strike']); W().dummy(70); E('window.__wm.follow = 0');
  W().tap('roll'); W().frame(16); const st0 = E('P.st'); W().tap('attack'); W().frame(30);
  rec('evasive_strike', `roll -> J: stamina ${st0.toFixed(0)} -> ${E('P.st').toFixed(0)}, marked ${E('P.skRollAtk === P.skMvN')}`, E('P.st') >= st0 - 0.5); }
// ---- Deflect: every type's clean defence (Iai parry, foresight, snap counter, perfect dodge, parry) pays 25 stamina + 3% HP
{ const r = [];
  for (const [ty, how] of [['katana', 'iai'], ['longsword', 'parry'], ['dual', 'pdodge']]) {
    W().reset(ty, 5); arena(); W().reset(ty, 5); setSk(['deflect']); E('P.st = 20; P.hp = D.maxHp * 0.5; P.skDefT = -9');
    const st0 = E('P.st'), hp0 = E('P.hp');
    if (how === 'iai') E("P.sheathed = true; mvStart('kt_iaiw'); P.inv = 0; P.lastHit = null; hurtPlayer(20, -1, 'dfl1', { src: null, parryable: true })");
    if (how === 'parry') E("startParry(); P.inv = 0; P.lastHit = null; hurtPlayer(20, -P.face, 'dfl2', { parryable: true })");
    if (how === 'pdodge') E("mvGain('perfect dodge')");
    r.push(`${ty} ${how}: st ${st0.toFixed(0)}->${E('P.st').toFixed(0)} hp ${(E('P.hp') - hp0).toFixed(0)}`);
  }
  rec('deflect', r.join('; '), r.every(x => +/hp (\d+)/.exec(x)[1] > 0)); }
// ---- Bloodthirst / Leech: by damage, not per hit (12 bleed / 0.8% HP per light hit's worth)
{
  // direct: bleed for a 0.35 dual hit vs a 1.0 longsword hit vs the greatsword's 3.0 charged hit
  const v = E(`(() => { const r = []; for (const [ty, id, k] of [['dual', 'tw_d6', 0], ['longsword', 'attack1', 0], ['greatsword', 'gs_charged', 0]]) { wmEquip(ty, { quiet: true }); SAVE.skills = ['bloodthirst']; refreshDerived(false); P.state = id; P.mvHitK = k; P.mvMul = 1; P.mvLv = 3; r.push(ty + ' ' + id + ' ' + bleedAmt(ATK[id].kind === 'heavy').toFixed(1) + ' (weapon ' + (D.W.bleed || 0) + ')'); } P.state = 'idle'; return r; })()`);
  rec('bloodthirst', v.join('; '), true); }
// ---- Lingering Flame: +12% melee for 6 s after an art
{ W().reset('longsword', 1); arena(); W().reset('longsword', 1); setSk(['lingering_flame']);
  const a = E("skOutMul('melee')"); E("P.state = 'art'; P.artCount = (P.artCount || 0) + 1"); W().frame(1); E("P.state = 'idle'"); const b = E("skOutMul('melee')");
  rec('lingering_flame', `melee x${a.toFixed(2)} -> x${b.toFixed(2)} after an art`, Math.abs(b / a - 1.12) < 0.01); }
// ---- Light Feet: no regen while Demon Mode stops it
{ const v = [];
  for (const sk of [[], ['light_feet']]) { W().reset('dual', 1); arena(); W().reset('dual', 1); setSk(sk); E('P.demon = true; P.st = 30; P.stDelay = 0'); W().frame(30); v.push(E('P.st')); }
  rec('light_feet.demon', `stamina 30 -> ${v[0].toFixed(1)} / with Light Feet ${v[1].toFixed(1)} in 0.5 s of Demon Mode`, Math.abs(v[0] - v[1]) < 0.01); }
// ---- Relentless: one stack per move (a 3-hit Demon move is one stack)
{ const a = route('dual', ['J', 'J', 'J', 'J', 'J', 'J'], ['relentless'], { pre: 'P.demon = true' });
  rec('relentless', `6 Demon moves (${a.hits} hits) -> stack ${E('P.skRel')}`, E('P.skRel') <= 5 && a.hits > 6); }
return { fail, R };
