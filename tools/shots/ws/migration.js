// old saves -> the nine types (contract §5): best level per type, rank II for every type owned, the weapon in hand -> its
// type's weapon, removed arts dropped, Arsenal nodes refunded. Covers the current journey and one in the old-journeys list.
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const base = JSON.parse(E('JSON.stringify(newSave())'));
delete base.wv; delete base.mastery; delete base.masteryBoss;
const old = Object.assign({}, base, {
  stats: { vig: 30, mnd: 15, end: 20, str: 30, dex: 20, fth: 12 }, shrine: 'R1', shrines: ['R1'], skillv: 2, progv: 3,
  weapon: 'first_ember', lastCls: 'twin', artPinned: 1, x3: { wbLastW: 'twinborne' },
  weapons: { longsword: 1, dagger: 2, pagecutter: 4, twinfangs: 1, greatsword: 0, briar_scythe: 3, colossus_hammer: 5, bell_hammer: 2, maul: 1,
             twinborne: 4, overseer_bulwark: 2, stormfang: 3, orrery_whip: 0, first_ember: 2, kalden: 3, windstaff: 1 },
  arts: ['crescent', 'bloodstep', 'warcry', 'echo', 'twin_tempest', 'lash'], art: 'echo',
  skills: ['keen_edge', 'm_sword', 'm_twin', 'heavy_hand', 'm_great'],
});
localStorage.setItem('cinderhollow_save_v1', JSON.stringify(old));
const old2 = Object.assign({}, base, { weapon: 'starblade', weapons: { starblade: 2, plasma_katana: 4, sanguine_rapier: 1 }, stats: { ...base.stats, vig: 22 }, shrine: 'R1', shrines: ['R1'], skillv: 2 });
localStorage.setItem('cinderhollow_old_saves_v1', JSON.stringify([{ t: Date.now(), data: JSON.stringify(old2) }]));
out.push('old slot line before load: ' + E('saveMeta(oldSaves()[0].data).line2'));
G.continueGame(); G.step(30);
const S = G.SAVE;
out.push('weapons ' + JSON.stringify(S.weapons) + ' in hand ' + S.weapon);
out.push('mastery ' + JSON.stringify(S.mastery));
ok(Object.keys(S.weapons).length === 14, 'fourteen weapons in the save (v15)');
ok(S.weapon === 'longsword', 'First Ember (mirror) in hand -> the Longsword');
ok(S.weapons.longsword === 3, 'longsword level = best of longsword 1 / kalden 3 / first_ember 2 -> 3');
ok(S.weapons.twinfangs === 4, 'dual = best of dagger 2 / pagecutter 4 / twinfangs 1 -> 4');
ok(S.weapons.requiem_scythe === 3 && S.weapons.greatsword === 0, 'v15: briar_scythe +3 -> the Scythe (requiem_scythe +3); greatsword stays 0');
ok(S.weapons.maul === 5, 'maul = best of colossus 5 / bell 2 / maul 1 -> 5');
ok(S.weapons.knight_shield === 4, 'sns = best of twinborne 4 / bulwark 2 -> 4');
ok(S.weapons.spear === 3 && S.weapons.headsman_chain === 0 && S.weapons.quarterstaff === 1 && S.weapons.katana === 0, 'spear 3, whip 0, staff 1, katana 0 (not owned)');
for (const t of ['longsword', 'dual', 'greatsword', 'maul', 'sns', 'spear', 'whip', 'staff']) ok(G.ws.rank(t) === 2, `${t} owned -> Mastery II`);
ok(G.ws.rank('katana') === 1, 'katana never owned -> Mastery I');
// v15: bloodstep / warcry are the Martial Arts' / Warbell's default arts again, so they're kept
ok(S.art === 'crescent' && !S.arts.includes('echo') && S.arts.every(a => E('WTYPES.map(t => WTYPE_INFO[t].art)').includes(a)), 'arts no type uses dropped, art = crescent: ' + JSON.stringify(S.arts));
ok(!S.skills.some(id => /^m_/.test(id)) && S.skills.includes('keen_edge') && S.skills.includes('heavy_hand'), 'Arsenal nodes removed, others kept: ' + JSON.stringify(S.skills));
ok(S.wv === 9 && !(S.x3 && S.x3.wbLastW) && S.artPinned === undefined, 'wv 9, mirror / art-pin leftovers cleaned');
ok(E('D.wid') === 'longsword' && E('D.W.name') === 'Ashen Longsword', 'derived stats use the migrated weapon');
G.step(5); const toasts = E('toasts.map(t => t.msg)'); ok(toasts.some(m => /reforged/.test(m)), 'migration toast: ' + toasts[0]);
await new Promise(r => setTimeout(r, 2800)); G.step(3);
ok(E('toasts.map(t => t.msg)').some(m => /refunded/.test(m)), 'refund toast');
const stored = JSON.parse(localStorage.getItem('cinderhollow_save_v1'));
ok(stored.wv === 9 && stored.weapon === 'longsword' && E(`saveCheck(localStorage.getItem('cinderhollow_save_v1'))`) === 'ok', 'saved migrated + signed');
// a second load must not migrate again (levels / mastery stay)
G.ws.gain('katana', 10); E('saveGame()'); G.continueGame(); G.step(5);
ok(G.ws.xp('katana') === 10 && G.SAVE.weapons.maul === 5, 'reload keeps the migrated save as is');
// the old-journeys slot: migrated when it is loaded
E('loadOld(0)'); G.step(20);
out.push('old journey: weapons ' + JSON.stringify(G.SAVE.weapons) + ' in hand ' + G.SAVE.weapon + ' mastery ' + JSON.stringify(G.SAVE.mastery));
ok(G.SAVE.weapon === 'katana' && G.SAVE.weapons.katana === 4 && G.SAVE.weapons.longsword === 1, 'old slot: starblade -> katana, best katana level 4, rapier -> longsword 1');
ok(G.ws.rank('katana') === 2 && G.ws.rank('longsword') === 2 && G.ws.rank('maul') === 1, 'old slot: katana + longsword at II');
await snap('migrated');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
