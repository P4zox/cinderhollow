// v15 platform: saves. A v14 (nine-type, wv 9) journey loads with the five new weapons added at +0 and nothing else
// touched; a v15 journey keeps a new weapon in hand, its tempering and its mastery across save / load; a pre-revamp
// journey still migrates; New Game+ keeps the new types' mastery. (run with tools/shots/shot.js)
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const NEW = { saxe: 'gravegrinder', bow: 'ashstring', fist: 'penitent_knuckles', scythe: 'requiem_scythe', bell: 'dirge_bell' };
localStorage.removeItem('cinderhollow_old_saves_v1');
// (a) a v14 save: nine weapons, wv 9
const base = JSON.parse(E('JSON.stringify(SAVE)'));
const v14 = { ...base, weapon: 'spear', art: 'thunder_lunge', weapons: { longsword: 1, katana: 0, greatsword: 0, maul: 2, knight_shield: 0, twinfangs: 0, spear: 3, quarterstaff: 0, headsman_chain: 0 },
  mastery: { spear: 950, maul: 300 }, masteryBoss: { hound: 1 }, wv: 9 };
localStorage.setItem('cinderhollow_save_v1', JSON.stringify(v14));
G.continueGame(); G.step(30);
let S = G.SAVE;
ok(S.weapon === 'spear' && S.weapons.spear === 3 && S.weapons.maul === 2 && S.weapons.longsword === 1, 'v14 save: weapon in hand and levels kept');
ok(Object.keys(S.weapons).length === 14 && Object.values(NEW).every(id => S.weapons[id] === 0), 'v14 save: the five new weapons added at +0');
ok(G.ws.rank('spear') === 3 && G.ws.rank('maul') === 2 && Object.keys(NEW).every(t => G.ws.rank(t) === 1), 'v14 save: mastery kept (spear III, maul II), new types at I');
ok(S.wv === 9 && !E('toasts.map(t => t.msg)').some(m => /reforged/.test(m)), 'v14 save: not re-migrated (no reforged toast)');
// (b) a v15 journey with the Gravegrinder +2 and Switch Axe mastery
E("wmEquip('saxe')"); G.SAVE.weapons.gravegrinder = 2; E("SAVE.mastery.saxe = 2000; SAVE.mastery.bell = 450; refreshDerived(false); saveGame()");
G.continueGame(); G.step(20); S = G.SAVE;
ok(S.weapon === 'gravegrinder' && S.weapons.gravegrinder === 2 && E('wtype()') === 'saxe' && S.art === 'magma_quake', 'v15 save: Gravegrinder +2 in hand after reload, art Magma Quake');
ok(G.ws.rank('saxe') === 4 && G.ws.rank('bell') === 2, 'v15 save: Switch Axe IV, Warbell II after reload');
ok(E('D.wid') === 'gravegrinder' && E("JSON.parse(localStorage.getItem('cinderhollow_save_v1')).weapon") === 'gravegrinder', 'derived stats + stored save use it');
// a save naming a weapon id that doesn't exist falls back safely
const bad = { ...JSON.parse(localStorage.getItem('cinderhollow_save_v1')), weapon: 'no_such_weapon' };
localStorage.setItem('cinderhollow_save_v1', JSON.stringify(bad)); G.continueGame(); G.step(10);
ok(G.SAVE.weapon === 'longsword', 'an unknown weapon id in a save falls back to the Longsword: ' + G.SAVE.weapon);
// (c) a pre-revamp save (no wv) still migrates; old scythes still become the Greatsword (contract §5; see platform.md)
const old = { ...base, weapon: 'briar_scythe', weapons: { longsword: 1, briar_scythe: 3, antler_scythe: 1 }, arts: ['crescent', 'reap'], art: 'reap' };
delete old.wv; delete old.mastery; delete old.masteryBoss;
localStorage.setItem('cinderhollow_save_v1', JSON.stringify(old)); G.continueGame(); G.step(20); S = G.SAVE;
ok(S.wv === 9 && Object.keys(S.weapons).length === 14 && S.weapon === 'greatsword' && S.weapons.greatsword === 3, `pre-revamp save migrates: ${S.weapon} +${S.weapons.greatsword}, ${Object.keys(S.weapons).length} weapons`);
// (d) New Game+ keeps every type's mastery
E("SAVE.mastery.scythe = 900; SAVE.mastery.fist = 4000; saveGame()");
let ngp = 'n/a';
try { E('startNGPlus()'); G.step(10); ngp = `${G.ws.rank('scythe')} / ${G.ws.rank('fist')}`; } catch (e) { ngp = 'error ' + e; }
ok(ngp === '3 / 5', 'New Game+ keeps the new types\' mastery (scythe / fist ranks): ' + ngp);
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
