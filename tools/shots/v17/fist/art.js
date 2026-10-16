// v17 A2 Litany of Fists: the art from the art key, both styles, tap and hold, Focus, the knee launch, the Iron shove,
// the guard break, the end state, the old-save art fix. SHOT_HTML=$PWD/web/dist/v17_fist.html sh tools/shots/wm/run.sh tools/shots/v17/fist/art.js tools/shots/v17/fist/out
const out = {};
const go = (style) => { W().reset('fist', 1); arena(); W().reset('fist', 1); E(`P.face = 1; P.ftStyle = '${style}'; P.ftFlow = 0; P.ftPdT = 0; P.inv = 0; P.cds = {}; P.fp = D.maxFp`); W().frame(4); };
const runArt = (hold) => {
  const fp0 = E('P.fp'); W().down('art'); W().frame(hold ? 50 : 1); W().up('art');
  const st = E('P.state'), tag = E('P.anim.tag'); let f = 0; while (E("P.state === 'art'") && f++ < 600) W().frame(1);
  W().frame(2);
  return { started: st === 'art', tag, fpCost: fp0 - E('P.fp'), frames: f, end: E('P.state'), flow: E('P.ftFlow') };
};
const sum = () => { const L = W().log; return { hits: L.length, light: +(L.reduce((a, h) => a + h.dmg, 0) / (L[0] ? L[0].light : 1)).toFixed(3), poise: L.reduce((a, h) => a + h.poise, 0), kinds: [...new Set(L.map(h => h.kind))] }; };
out.icon = E("ICON_SHEETS.includes('ui_icons17_fist') && sheet('ui_icons17_fist').ok && sheet('ui_icons17_fist').has('a_litany')");
out.art = E('[SAVE.art, ARTS.litany && ARTS.litany.name, ARTS.litany.fp, cdBase("art","litany"), WEAPONS.penitent_knuckles.art, WTYPE_INFO.fist.art]');
for (const style of ['swift', 'iron']) for (const hold of [false, true]) {
  go(style); W().dummy(26); W().log = [];
  const r = runArt(hold); out[style + (hold ? '_hold' : '_tap')] = { ...r, ...sum(), styleAfter: E('P.ftStyle') };
}
// Focus: +10% per hit (and reach)
for (const style of ['swift', 'iron']) { go(style); W().dummy(26); W().log = []; E('P.ftPdT = 6'); const r = runArt(false); out[style + '_focus'] = { ...sum(), end: r.end }; }
// the art's own rules on real foes: the knee launches a small foe (Swift), the palm/wave shove (Iron), the hold breaks a raised guard
const foe = (type, dx, face = -1) => E(`enemies = enemies.filter(e => e.wmDummy && false); const e = makeEnemy('${type}', P.x + ${dx}, P.y, 'lt_' + Math.random()); e.hp = e.maxHp = 99999; e.face = ${face}; e.aggro = false; enemies.push(e); window.__t = e; 1`);
go('swift'); foe('hollow_soldier', 26); W().frame(1); { const vy = []; W().down('art'); W().frame(1); W().up('art'); let f = 0; while (E("P.state === 'art'") && f++ < 600) { W().frame(1); vy.push(E('__t.vy')); } out.swift_launch = { minVy: Math.min(...vy), launches: E('MV.ltLaunch || 0'), foeState: E('__t.state') }; }
go('iron'); foe('hollow_soldier', 24); W().frame(1); { const x0 = E('__t.x'); runArt(false); W().frame(20); out.iron_shove = { dx: Math.round(E('__t.x') - x0), shoves: E('MV.ltShove || 0') }; }
go('iron'); foe('hollow_soldier', 70); W().frame(1); { const hp0 = E('__t.hp'); runArt(false); out.iron_wave_far = { dmg: hp0 - E('__t.hp') }; }
for (const hold of [false, true]) { go('iron'); E('MV.ltGuardBreaks = 0'); foe('shield_warden', 26); E("__t.update = function () { if (this.state !== 'stagger') { this.state = 'guard'; this.face = -1; } }; __t.state = 'guard'"); W().frame(1); const r = runArt(hold); out['guard_' + (hold ? 'hold' : 'tap')] = { breaks: E('MV.ltGuardBreaks'), foeState: E('__t.state'), end: r.end }; }
// the Iron armour: a small blow during the palm doesn't flinch, a big one does
go('iron'); W().down('art'); W().frame(1); W().up('art'); W().frame(6); E("P.inv = 0; hurtPlayer(Math.round(D.maxHp * 0.1), -1, 'lt_small', {})"); out.iron_armor_small = E('P.state');
go('iron'); W().down('art'); W().frame(1); W().up('art'); W().frame(6); E("P.inv = 0; hurtPlayer(Math.round(D.maxHp * 0.3), -1, 'lt_big', {})"); out.iron_armor_big = E('P.state');
go('swift'); W().down('art'); W().frame(1); W().up('art'); W().frame(6); E("P.inv = 0; hurtPlayer(Math.round(D.maxHp * 0.1), -1, 'lt_sw', {})"); out.swift_flinch = E('P.state');
// an old save holding the borrowed art id is corrected
go('swift'); E("SAVE.art = 'bloodstep'"); W().frame(2); out.oldSave = E('SAVE.art');
// FP and cooldown deny
go('swift'); E('P.fp = 3'); W().tap('art', 1); out.noFp = E('P.state');
go('swift'); runArt(false); W().tap('art', 1); out.onCd = E('P.state');
out.pass = ['swift_tap', 'swift_hold', 'iron_tap', 'iron_hold'].every(k => out[k].started && out[k].end === 'idle' && out[k].fpCost === 14 && out[k].hits > 0)
  && out.swift_hold.hits > out.swift_tap.hits && out.iron_hold.light > out.iron_tap.light && out.swift_launch.launches > 0 && out.iron_shove.dx > 10
  && out.guard_hold.breaks > 0 && out.iron_armor_small === 'art' && out.iron_armor_big === 'hurt' && out.oldSave === 'litany' && out.noFp !== 'art' && out.onCd !== 'art'
  && out.icon === true && out.swift_focus.light > out.swift_tap.light && out.iron_focus.light > out.iron_tap.light;
return out;
