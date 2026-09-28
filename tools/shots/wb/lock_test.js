// locked arts (agent WB, B4): the art always equals the weapon's, the menus can't change it, old saves migrate,
// old "Ash of X" items and the A7 chest pay out a tempering cache. Screenshots of the read-only displays.
// SHOT_HTML=web/dist/wb.html node tools/shots/shot.js tools/shots/wb/lock_test.js tools/shots/wb/out
await boot(); G.giveArmory();
const E = G.sk.ev, R = { ok: [], bad: [] };
const check = (cond, msg) => (cond ? R.ok : R.bad).push(msg);
G.step(2);
// 1) every weapon, equipped through the equipment screen's own code path, carries its own art (First Ember: its Echo)
for (const id of E('Object.keys(WEAPONS)')) {
  E(`applyEquip({ k: 'weapon' }, ${JSON.stringify(id)})`); G.step(1);
  const want = E(`WEAPONS[${JSON.stringify(id)}].art`);
  if (G.SAVE.art !== want) R.bad.push(`${id}: art ${G.SAVE.art}, want ${want}`);
}
check(E("applyEquip({ k: 'weapon' }, 'first_ember'), SAVE.art") === 'echo', 'mirror: the First Ember carries Echo');
check(E("toasts.some(t => /First Ember takes the shape of your/.test(t.msg))"), 'mirror: equip toast names the mirrored class');
check(/Mirrors your/.test(E("WEAPONS.first_ember.sigInfo")), 'mirror: detail line names the mirrored class');
// 2) the menus can't change it
E("applyEquip({ k: 'weapon' }, 'longsword')"); G.step(1);
E("changeEquip({ k: 'art' }, 1)"); check(G.SAVE.art === 'crescent', 'quick-cycle on the art row changes nothing');
E("applyEquip({ k: 'art' }, 'lash')"); check(G.SAVE.art === 'crescent', 'applyEquip(art) changes nothing');
E("menu = { screen: 'pause', tab: 0, sel: 1 }; state = 'menu'; openPicker(menu, equipRows()[1])"); check(!E('menu.pick'), 'no art picker opens');
check(E("pickIds({ k: 'art' }).length") === 0, 'art picker list is empty');
G.SAVE.art = 'lash';
E("menu = null; state = 'play'"); G.step(1); check(G.SAVE.art === 'crescent', 'a forced SAVE.art snaps back to the weapon\'s on the next frame');
// 3) screenshots: equipment art slot (read-only), weapon detail (art + signature), inventory arts
E("applyEquip({ k: 'weapon' }, 'omen'); menu = { screen: 'pause', tab: 0, sel: 1 }; state = 'menu'"); G.step(1); await snap('lock_art_slot');
E("menu.sel = 0"); G.step(1); await snap('lock_weapon_detail');
E("applyEquip({ k: 'weapon' }, 'first_ember'); menu = { screen: 'pause', tab: 0, sel: 0 }"); G.step(1); await snap('lock_first_ember');
E("menu = { screen: 'pause', tab: 1, sel: 0, cat: 1, isel: 0, bar: false }"); G.step(1); await snap('lock_inv_arts');
E("menu = null; state = 'play'"); G.step(1);
// 4) old save: a pinned foreign art and the obsolete arts list
E("applyEquip({ k: 'weapon' }, 'longsword')"); G.step(1);
E("SAVE.art = 'lash'; SAVE.artPinned = true; SAVE.arts = ['crescent', 'lash', 'magma_quake']; saveGame()");
E("continueGame()"); G.step(2);
check(G.SAVE.art === 'crescent' && !G.SAVE.artPinned, `old save: art ${G.SAVE.art}, pinned ${G.SAVE.artPinned}`);
// NG+ keeps the lock
if (E("typeof startNGPlus") === 'function') { E('startNGPlus()'); for (let i = 0; i < 60 && G.state !== 'play'; i++) G.step(5, [], ['pause']); G.step(2); check(G.SAVE.art === E('WEAPONS[SAVE.weapon].art'), `NG+: art ${G.SAVE.art} for ${G.SAVE.weapon}`); }
// 5) "Ash of X" and the old chest: an emberstone and 300 cinders
{ const s0 = G.SAVE.inv.emberstone || 0, c0 = G.SAVE.cinders, a0 = G.SAVE.art;
  E("grantItem('art:backstep_slash', P.x, P.y)");
  check((G.SAVE.inv.emberstone || 0) === s0 + 1 && G.SAVE.cinders - c0 >= 300 && G.SAVE.art === a0, `art:backstep_slash -> emberstone ${s0}->${G.SAVE.inv.emberstone}, cinders +${G.SAVE.cinders - c0} (x NG+ cinder bonus)`); }
check(/ash_cache/.test(JSON.stringify(E('ROOM_BY.A7 && ROOM_BY.A7.chests'))), 'A7 (Unbound Folio) chest holds a tempering cache');
check(!E("Object.values(SHOPS).some(l => l.some(e => /^art:/.test(e.item)))"), 'no shop sells an art');
check(E("Object.keys(ITEMS).filter(k => /^art:/.test(k)).every(k => ITEMS[k].cache && !ITEMS[k].art)"), 'every art: item is a cache now');
// 6) the boss-fight sustain budget exists and resets
check(E("typeof WB_SUS === 'object' && typeof wbFlaskHp() === 'number'"), 'sustain budget present');
return R;
