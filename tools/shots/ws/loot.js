// weapons left the world: room items / chests, boss rewards and shops became Emberstones + cinders
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const rooms = E('ROOMS'), wItems = [];
for (const r of rooms) for (const k of ['items', 'chests']) for (const id of r[k] || []) if (/^w:/.test(id)) wItems.push(r.id + ':' + id);
ok(!wItems.length, 'no room item or chest names a weapon ' + JSON.stringify(wItems));
const caches = []; for (const r of rooms) for (const k of ['items', 'chests']) for (const id of r[k] || []) if (/^wc_/.test(id)) caches.push(`${r.id} ${k.slice(0, -1)} ${id}`);
out.push('caches in rooms (' + caches.length + '): ' + caches.join(' · '));
ok(caches.length === 18, '18 former weapon spots now hold caches');
const B = E('BOSS_INFO'), bw = Object.entries(B).filter(([k, b]) => (b.reward || []).some(id => /^w:/.test(id)));
ok(!bw.length, 'no boss reward is a weapon ' + JSON.stringify(bw.map(x => x[0])));
out.push('boss loot: ' + Object.entries(G.ws.WM_BOSS_LOOT).map(([k, [a, b]]) => `${k} ${a}->${b}`).join(' · '));
ok(Object.keys(G.ws.WM_BOSS_LOOT).length >= 25, 'boss weapon rewards converted: ' + Object.keys(G.ws.WM_BOSS_LOOT).length);
const shopW = []; for (const [k, L] of Object.entries(E('SHOPS'))) for (const e of L) if (/^w:/.test(e.item)) shopW.push(k + ':' + e.item);
ok(!shopW.length, 'no shop sells a weapon ' + JSON.stringify(shopW));
out.push('ashwright: ' + E('SHOPS.ashwright').map(e => `${e.item}x${e.stock}`).join(', '));
// granting a cache
const s0 = G.SAVE.inv.emberstone || 0, c0 = G.SAVE.cinders;
E("grantItem('wc_cache', P.x, P.y - 20)"); G.step(3);
ok((G.SAVE.inv.emberstone || 0) === s0 + 2 && G.SAVE.cinders > c0, `wc_cache: emberstones ${s0} -> ${G.SAVE.inv.emberstone}, cinders ${c0} -> ${G.SAVE.cinders}`);
await snap('cache_banner');
const s1 = G.SAVE.inv.emberstone; E("grantItem('w:dagger', P.x, P.y - 20)"); G.step(3);
ok(G.SAVE.inv.emberstone === s1 + 2 && !('dagger' in G.SAVE.weapons) && Object.keys(G.SAVE.weapons).length === 14, 'a stray old weapon id grants a cache, not a weapon');
// a boss's rewards through BossBase.rewards
const b = G.w.spawnBoss('hound', 10, 10); const r0 = JSON.stringify(E("BOSS_INFO.hound.reward")); const s2 = G.SAVE.inv.emberstone;
E("boss.rewards()"); await new Promise(r => setTimeout(r, 2600 + 2400 * 3 + 500)); G.step(3);
ok(G.SAVE.inv.emberstone >= s2 + 2 && Object.keys(G.SAVE.weapons).length === 14, `hound rewards ${r0}: emberstones ${s2} -> ${G.SAVE.inv.emberstone}`);
// the armory cheat gives the nine
E('giveArmory()'); G.step(3);
ok(Object.keys(G.SAVE.weapons).length === 14 && E('bannerMsg && bannerMsg.desc').includes('14 weapons'), 'armory: fourteen weapons, banner says so');
// SIGS are gone
ok(Object.keys(E('SIGS')).length === 0 && typeof E('sigLimit()') === 'number', 'SIGS empty, helpers still there');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;
