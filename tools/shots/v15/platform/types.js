// v15 platform: the five new types end to end (run with tools/shots/wm/run.sh: the WM prelude gives W(), E, arena()).
// Each type: equips (weapon, type, art, derived stats, overlay + icon), its skeleton moves all land on a dummy (J J J, K,
// up J, air J, air down J pogo, air K plunge, L, L -> J), the rank-II L -> K is gated by Mastery, hits earn mastery XP,
// tempering raises the attack, and the nine keep working the same way.
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const NEW = ['saxe', 'bow', 'fist', 'scythe', 'bell'];
ok(E('WTYPES.length') === 14 && NEW.every(t => E('WTYPES').includes(t)), 'WTYPES: the nine + the five: ' + E('WTYPES.join(" ")'));
ok(E('MOVESETS_TYPES.length') === 14 && NEW.every(t => !!E(`MV.types['${t}'] && MOVESETS['${t}']`)), 'MOVESETS_TYPES and MV.types know all five');
arena();
const go = (t, r) => { W().reset(t, r); E('P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1'); W().frame(2); };   // back to the arena's start each time
const kill = () => E('enemies = enemies.filter(e => !e.wmDummy)');
for (const t of NEW) {
  const I = E(`WTYPE_INFO['${t}']`), id = I.weapon, pre = I.prefix;
  go(t, 1); W().frame(3);
  ok(E('SAVE.weapon') === id && E('wtype()') === t && E('wcls()') === t && E(`WEAPON_CLASS['${id}']`) === t && E('D.wid') === id, `${t}: ${id} in hand, wtype/wcls ${t}, derived stats use it`);
  ok(E('SAVE.art') === I.art && !!E(`ARTS['${I.art}']`), `${t}: art locked to ${I.art}`);
  ok(E(`sheet('wpn_${id}').ok`) && E(`sheet('wpn_${id}').frames.length`) === E(`sheet('player').frames.length`), `${t}: overlay wpn_${id} matches the player sheet frame for frame`);
  ok(E(`ICON_SHEETS.some(n => sheet(n).ok && sheet(n).has('w_${id}'))`), `${t}: icon w_${id}`);
  ok(E(`ITEMS['w:${id}'] && ITEMS['w:${id}'].weapon`) === id && E(`WEAPONS['${id}'].base`) === 42, `${t}: WEAPONS + ITEMS entry, base 42`);
  ok(I.diff >= 1 && I.diff <= 5 && I.name && I.desc && I.str && I.weak && I.mech && I.short, `${t}: info complete (${I.name}, ${'★'.repeat(I.diff)})`);
  // the light chain
  W().dummy(26); const x0 = E(`masteryXP('${t}')`);
  for (let i = 0; i < 3; i++) { W().tap('attack', 2); W().frame(10); }   // presses queue during a move
  W().frame(80);
  const st = [...new Set(W().log.map(l => l.st))];
  ok(st.join() === [1, 2, 3].map(i => pre + i).join(), `${t}: J J J -> ${st.join(' ')} (${W().log.length} hits, ${W().log.map(l => (l.dmg / l.light).toFixed(2)).join('/')})`);
  ok(E(`masteryXP('${t}')`) > x0, `${t}: hits earn mastery XP (${x0} -> ${E(`masteryXP('${t}')`)})`);
  // K
  go(t, 1); W().dummy(26); W().tap('heavy', 2); W().frame(80);
  ok(W().log.some(l => l.st === pre + 'heavy'), `${t}: K -> ${pre}heavy lands`);
  // up J
  go(t, 1); W().dummy(20); W().down('up'); W().tap('attack', 2); W().up('up'); W().frame(60);
  ok(W().log.some(l => l.st === pre + 'up'), `${t}: up J -> ${pre}up lands`);
  // air J
  go(t, 1); W().dummy(22); W().tap('jump', 2); W().frame(8); W().tap('attack', 2); W().frame(40);
  ok(W().log.some(l => l.st === pre + 'air'), `${t}: air J -> ${pre}air lands`);
  // air down J (pogo): the dummy right under the feet
  go(t, 1); W().tap('jump', 2); W().frame(18); W().dummy(0); W().down('down'); W().tap('attack', 2); W().frame(30); W().up('down'); W().frame(40);
  ok(W().log.some(l => l.st === pre + 'down'), `${t}: air down J -> ${pre}down lands`);
  // L -> J
  go(t, 1); W().dummy(110); W().tap('roll', 2); W().frame(14); W().tap('attack', 2); W().frame(50);
  ok(W().log.some(l => l.st === pre + 'rollj'), `${t}: L -> J -> ${pre}rollj lands`);
  // L -> K: rank II only
  go(t, 1); W().dummy(110); W().tap('roll', 2); W().frame(14); W().tap('heavy', 2); W().frame(60);
  const r1 = W().log.some(l => l.st === pre + 'rollk');
  go(t, 2); W().dummy(110); W().tap('roll', 2); W().frame(14); W().tap('heavy', 2); W().frame(60);
  const r2 = W().log.some(l => l.st === pre + 'rollk');
  ok(!r1 && r2, `${t}: L -> K (${pre}rollk) needs Mastery II (rank I ${r1}, rank II ${r2})`);
  // tempering: +3 raises the attack rating; the forge's cost table is the shared one
  E(`MV.rank = null; SAVE.weapons['${id}'] = 0; refreshDerived(false)`); const a0 = E('D.light');
  E(`SAVE.weapons['${id}'] = 3; refreshDerived(false)`); const a3 = E('D.light');
  ok(a3 > a0 * 1.25, `${t}: +3 tempering raises the attack (${a0.toFixed(1)} -> ${a3.toFixed(1)})`);
  E(`SAVE.weapons['${id}'] = 0; refreshDerived(false)`);
  kill();
}
// mastery: rank-ups, the unlock list and the move list read from the type's table
E("SAVE.mastery.bell = 0"); E("masteryGain('bell', 300, 'test')");
ok(E("masteryRank('bell')") === 2 && E("WM.rankUps.some(r => r[0] === 'bell' && r[1] === 2)"), 'bell: 300 XP -> Mastery II with a rank-up banner');
ok(NEW.every(t => E(`wmUnlocks('${t}').length`) >= 1 && E(`wmMoveList('${t}').length`) >= 8), 'every new type has an unlock list and a move list');
// the forge tempers a new weapon (Enter on its row)
E("SAVE.inv.emberstone = 5; SAVE.cinders = 5000; SAVE.weapons.dirge_bell = 0; menu = { screen: 'forge', sel: Object.keys(SAVE.weapons).filter(id => WEAPONS[id]).indexOf('dirge_bell') }; state = 'menu'");
E("forgeInput('confirm')");
ok(E('SAVE.weapons.dirge_bell') === 1 && E('SAVE.inv.emberstone') === 4, 'the forge tempers the Dirgebell to +1 (1 Emberstone)');
E('menu = null; state = "play"');
// loot conversion leaves the new weapons alone, and no room / shop hands one out
ok(E("wmLoot('w:gravegrinder')") === 'w:gravegrinder' && E("wmLoot('w:antler_scythe')") === 'wc_cache', 'loot: a new weapon id is kept, an old scythe still becomes a cache');
// the nine still pass through the same engine unchanged
go('longsword', 1); W().dummy(26); for (let i = 0; i < 4; i++) { W().tap('attack', 2); W().frame(30); } W().frame(40);
ok([...new Set(W().log.map(l => l.st))].join() === 'attack1,attack2,attack3,attack4', 'longsword J J J J unchanged');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
