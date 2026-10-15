// v15 platform: the five new types, checked for what the platform owns (run with tools/shots/wm/run.sh: the WM prelude
// gives W(), E, arena()). Nothing here hard-codes a moveset id: the moves are read from MV.types[t] / MV.defs / ATK.
// Each type: equips (weapon, type, art lock, derived stats, overlay + icon, item), its table is well-formed (every
// T move id and every string route exists, every move has a tag the player sheet can play, combos / unlocks are complete),
// its first light (J from neutral) and its K hit a dummy, hits earn mastery XP, rank-gated moves are gated, tempering raises
// the attack, the forge tempers it; and the nine keep working.
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const NEW = ['saxe', 'bow', 'fist', 'scythe', 'bell'];
ok(E('WTYPES.length') === 14 && NEW.every(t => E('WTYPES').includes(t)), 'WTYPES: the nine + the five: ' + E('WTYPES.join(" ")'));
ok(E('MOVESETS_TYPES.length') === 14 && NEW.every(t => !!E(`MV.types['${t}'] && MOVESETS['${t}']`)), 'MOVESETS_TYPES, MV.types and MOVESETS know all five');
arena();
const go = (t, r) => { W().reset(t, r); E('P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; MV.later = []; projectiles.length = 0'); W().frame(2); };   // back to the arena's start each time
const kill = () => E('enemies = enemies.filter(e => !e.wmDummy)');
const typeOf = st => E(`(ATK['${st}'] && ATK['${st}'].mv && ATK['${st}'].mv.type) || null`);
for (const t of NEW) {
  const I = E(`WTYPE_INFO['${t}']`), id = I.weapon;
  go(t, 1); W().frame(3);
  ok(E('SAVE.weapon') === id && E('wtype()') === t && E('wcls()') === t && E('mvType()') === t && E(`WEAPON_CLASS['${id}']`) === t && E('D.wid') === id, `${t}: ${id} in hand, wtype/wcls/mvType ${t}, derived stats use it`);
  ok(E('SAVE.art') === I.art && !!E(`ARTS['${I.art}']`), `${t}: art locked to ${I.art}`);
  ok(E(`sheet('wpn_${id}').ok`) && E(`sheet('wpn_${id}').frames.length`) === E(`sheet('player').frames.length`), `${t}: overlay wpn_${id} matches the player sheet frame for frame`);
  ok(E(`ICON_SHEETS.some(n => sheet(n).ok && sheet(n).has('w_${id}'))`), `${t}: icon w_${id}`);
  ok(E(`ITEMS['w:${id}'] && ITEMS['w:${id}'].weapon`) === id && E(`WEAPONS['${id}'].base`) === 42, `${t}: WEAPONS + ITEMS entry, base 42`);
  ok(I.diff >= 1 && I.diff <= 5 && I.name && I.desc && I.str && I.weak && I.mech && I.short, `${t}: info complete (${I.name}, ${'★'.repeat(I.diff)})`);
  ok(E(`sheet('player').has(wmFirstTag('${t}'))`), `${t}: the select / shrine preview plays ${E(`wmFirstTag('${t}')`)}`);
  // the table: T's move ids, string routes and tags all resolve
  const chk = E(`(() => {
    const T = MV.types['${t}'], bad = [], defs = Object.values(MV.defs).filter(d => d.type === '${t}');
    for (const k of ['K', 'up', 'air', 'down', 'counter', 'rollJ']) { const v = T[k]; if (typeof v === 'string' && !ATK[v]) bad.push(k + ':' + v); }
    for (const v of T.light || []) if (!ATK[v]) bad.push('light:' + v);
    for (const d of defs) {
      for (const b of ['J', 'K', 'I']) { const r = d.next && d.next[b]; if (typeof r === 'string' && r[0] !== '@' && !ATK[r]) bad.push(d.id + '.' + b + '->' + r); if (r && typeof r === 'object' && r.id && !ATK[r.id]) bad.push(d.id + '.' + b + '->' + r.id); }
      if (!d.tags || !d.tags.some(g => pHas(g))) bad.push(d.id + ' has no playable tag');
    }
    const C = T.combos || [], U = T.unlocks || [];
    const cBad = C.filter(c => !(c.rank >= 1 && c.rank <= 5 && c.name && c.input && c.desc)).map(c => c.name);
    const uBad = U.filter(u => !(u.rank >= 2 && u.rank <= 5 && u.id && u.name && u.input && u.desc)).map(u => u.id);
    const uRanks = [2, 3, 4, 5].filter(r => U.some(u => u.rank === r));
    return { moves: defs.length, bad, combos: C.length, cBad, unlocks: U.length, uBad, uRanks, ranked: defs.filter(d => d.rank >= 2).map(d => d.id) };
  })()`);
  ok(chk.bad.length === 0, `${t}: ${chk.moves} moves, every T id / route / tag resolves ${chk.bad.length ? JSON.stringify(chk.bad.slice(0, 6)) : ''}`);
  ok(chk.combos >= 8 && chk.cBad.length === 0, `${t}: Move List has ${chk.combos} well-formed entries ${chk.cBad.length ? JSON.stringify(chk.cBad) : ''}`);
  ok(chk.uBad.length === 0 && chk.uRanks.join() === '2,3,4,5', `${t}: ${chk.unlocks} unlocks, something at every rank II-V (${chk.uRanks.join(',')})`);
  ok(E(`wmMoveList('${t}').length`) === chk.combos && E(`wmUnlocks('${t}').length`) === chk.unlocks, `${t}: the mastery screen reads them`);
  // the first light: J from neutral
  go(t, 1); W().dummy(24); const x0 = E(`masteryXP('${t}')`);
  W().tap('attack', 2); W().frame(70);
  const j = W().log[0];
  ok(!!j && typeOf(j.st) === t, `${t}: J from neutral hits the dummy (${j ? j.st + ' ' + (j.dmg / j.light).toFixed(2) : 'no hit'})`);
  ok(E(`masteryXP('${t}')`) > x0, `${t}: hits earn mastery XP (${x0} -> ${E(`masteryXP('${t}')`)})`);
  // K from neutral (a tap; some types release on letting go, so give it time)
  go(t, 1); W().dummy(24); W().tap('heavy', 4); W().frame(150);
  const k = W().log[0];
  ok(!!k, `${t}: K from neutral hits the dummy (${k ? k.st + ' ' + (k.dmg / k.light).toFixed(2) : 'no hit'})`);
  // rank gating: moves with rank >= 2 never start at Mastery I; at V some do (others may still need their own condition: a gauge, a style)
  if (chk.ranked.length) {
    go(t, 1); const lo = chk.ranked.filter(id => { const r = E(`mvStart('${id}')`); E("P.state = 'idle'; P.anim.set('idle', true)"); return r; });
    go(t, 5); const hi = chk.ranked.filter(id => { const r = E(`mvStart('${id}')`); E("P.state = 'idle'; P.anim.set('idle', true)"); return r; });
    ok(lo.length === 0 && hi.length > 0, `${t}: rank-gated moves blocked at I (${lo.join(',') || 'none start'}), ${hi.length}/${chk.ranked.length} start at V`);
  } else ok(false, `${t}: no rank-gated move`);
  // tempering: +3 raises the attack rating
  E(`MV.rank = null; SAVE.weapons['${id}'] = 0; refreshDerived(false)`); const a0 = E('D.light');
  E(`SAVE.weapons['${id}'] = 3; refreshDerived(false)`); const a3 = E('D.light');
  ok(a3 > a0 * 1.25, `${t}: +3 tempering raises the attack (${a0.toFixed(1)} -> ${a3.toFixed(1)})`);
  E(`SAVE.weapons['${id}'] = 0; refreshDerived(false)`);
  kill();
}
// mastery: rank-ups with a banner
E("SAVE.mastery.bell = 0"); E("masteryGain('bell', 300, 'test')");
ok(E("masteryRank('bell')") === 2 && E("WM.rankUps.some(r => r[0] === 'bell' && r[1] === 2)"), 'bell: 300 XP -> Mastery II with a rank-up banner');
// the forge tempers a new weapon (Enter on its row)
E("SAVE.inv.emberstone = 5; SAVE.cinders = 5000; SAVE.weapons.dirge_bell = 0; menu = { screen: 'forge', sel: Object.keys(SAVE.weapons).filter(id => WEAPONS[id]).indexOf('dirge_bell') }; state = 'menu'");
E("forgeInput('confirm')");
ok(E('SAVE.weapons.dirge_bell') === 1 && E('SAVE.inv.emberstone') === 4, 'the forge tempers the Dirgebell to +1 (1 Emberstone)');
E('menu = null; state = "play"');
// loot conversion leaves the new weapons alone
ok(E("wmLoot('w:gravegrinder')") === 'w:gravegrinder' && E("wmLoot('w:antler_scythe')") === 'wc_cache', 'loot: a new weapon id is kept, an old scythe still becomes a cache');
// the nine still pass through the same engine unchanged
go('longsword', 1); W().dummy(26); for (let i = 0; i < 4; i++) { W().tap('attack', 2); W().frame(30); } W().frame(40);
ok([...new Set(W().log.map(l => l.st))].join() === 'attack1,attack2,attack3,attack4', 'longsword J J J J unchanged');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
