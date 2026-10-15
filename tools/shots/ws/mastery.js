// Weapon Mastery: XP for hits, kills, elites and bosses, the rank thresholds, the rank-up banner, gating API, NG+ carry
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
ok(JSON.stringify(G.ws.MASTERY_XP) === '[0,300,900,2000,4000]', 'MASTERY_XP');
ok(G.ws.rank('longsword') === 1 && G.ws.xp('longsword') === 0, 'a new journey starts at rank I, 0 XP');
// hits and a kill with the Longsword
E('SETTINGS.god = 1'); const P = G.P;
const e = G.w.spawn('hollow_soldier', Math.round(P.x / 16) + 2, Math.round(P.y / 16) - 1);
let hits = 0;
for (let i = 0; i < 60 && e.alive; i++) { P.face = e.x > P.x ? 1 : -1; G.step(1, [], ['attack']); G.step(14); }
const lx = G.ws.xp('longsword'), log = G.ws.WM.log.filter(l => l[0] === 'longsword');
hits = log.filter(l => l[2] === 'hit').length;
ok(!e.alive && log.some(l => l[2] === 'kill' && l[1] === 5), `the soldier died: a kill gives 5 (log ${JSON.stringify(log.slice(-3))})`);
ok(hits >= 1 && lx === hits + 5, `hits give 1 each: ${hits} hits + 5 = ${lx}`);
// an elite kill
const el = G.w.spawn('grave_knight', Math.round(P.x / 16) + 2, Math.round(P.y / 16) - 1); el.cfg = { ...el.cfg, elite: true };
const x0 = G.ws.xp('longsword'); el.hit({ dmg: 99999, poise: 0, dir: 1, kind: 'light', x: el.x, y: el.y - 10 }); G.step(2);
ok(G.ws.xp('longsword') - x0 === 20, 'an elite kill gives 20: ' + (G.ws.xp('longsword') - x0));
// only the weapon in hand earns
const k0 = G.ws.xp('katana'); ok(k0 === 0, 'katana untouched while the longsword fights');
// bosses: 300 the first time, 150 after (per boss, ever)
const b = G.w.spawnBoss('hound', 10, 10); const y0 = G.ws.xp('longsword'); E('boss.rewards()'); G.step(2);
ok(G.ws.xp('longsword') - y0 === 300, 'first Gravetusk kill: 300');
const b2 = G.w.spawnBoss('hound', 10, 10); const y1 = G.ws.xp('longsword'); E('boss.rewards()'); G.step(2);
ok(G.ws.xp('longsword') - y1 === 150, 'again: 150');
// ranks
ok(G.ws.rank('longsword') === (G.ws.xp('longsword') >= 900 ? 3 : 2), `rank ${G.ws.rank('longsword')} at ${G.ws.xp('longsword')} XP`);
ok(G.ws.WM.rankUps.some(r => r[0] === 'longsword' && r[1] === 2), 'rank-up to II recorded');
const ban = E('bannerMsg'); out.push('banner: ' + (ban && ban.title) + ' | ' + (ban && ban.desc));
ok(ban && /Longsword Mastery II: /.test(ban.title), 'rank-up banner "Longsword Mastery II: <unlock>"');
await snap('rankup_banner');
G.step(200); await snap('rankup_tryit');
for (const [xp, r] of [[0, 1], [299, 1], [300, 2], [899, 2], [900, 3], [1999, 3], [2000, 4], [3999, 4], [4000, 5], [9999, 5]]) { G.SAVE.mastery.spear = xp; ok(G.ws.rank('spear') === r, `spear ${xp} XP -> rank ${r}`); }
G.SAVE.mastery.spear = 3990; G.ws.gain('spear', 50, 'test'); ok(G.ws.xp('spear') === 4000 && G.ws.rank('spear') === 5, 'XP caps at 4000 (rank V)');
ok(G.ws.gain('spear', 50) === 0, 'no more XP past V');
// WM's counter hook
const c0 = G.ws.xp('longsword'); E("masteryGain(wtype(), 5, 'counter')"); ok(G.ws.xp('longsword') - c0 === 5, "masteryGain(wtype(), 5, 'counter') +5");
// API shape
ok(E('typeof masteryRank') === 'function' && E('typeof masteryXP') === 'function' && E('typeof masteryGain') === 'function', 'masteryRank / masteryXP / masteryGain exist');
ok(E('WTYPES.join()') === 'longsword,katana,greatsword,maul,sns,dual,spear,staff,whip', 'WTYPES order');
ok(E("WTYPE_INFO.sns.weapon") === 'knight_shield' && E("WTYPE_INFO.whip.art") === 'lash' && E("WTYPE_INFO.dual.prefix") === 'tw_', 'WTYPE_INFO fields');
ok(G.ws.unlocks('longsword').length === 4 && G.ws.unlocks('whip')[3].name === 'Thousand lashes', 'unlock lists (WM or the doc tables)');
// NG+ keeps mastery
const before = JSON.stringify(G.SAVE.mastery); E('startNGPlus()'); G.step(10);
ok(JSON.stringify(G.SAVE.mastery) === before && G.SAVE.ngp === 1, 'New Game+ keeps mastery ' + before);
ok(G.SAVE.masteryBoss && G.SAVE.masteryBoss.hound === 1, 'and remembers first boss kills');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
