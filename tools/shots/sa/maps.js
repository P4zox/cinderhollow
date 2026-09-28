await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.give({ items: { talon: 1, tidebreath: 1 } }); const S = window.__sys, log = [];
const ROOM_BY = {}; for (const r of (window.__rb ? Object.values(window.__rb.ROOM_BY) : [])) ROOM_BY[r.id] = r;
const ids = Object.keys(ROOM_BY);
for (const id of ids) if (!ROOM_BY[id].test) G.SAVE.visited[id] = 1;
G.SAVE.seenAreas = Object.fromEntries(ids.map(k => [ROOM_BY[k].biome, 1]));
G.SAVE.shrines.push(...ids.filter(k => ROOM_BY[k].shrine));
const mine = ids.filter(k => /^(TV(9|1\d)|DB1\d|CM(9|1\d))$/.test(k));
log.push('my shrines: ' + mine.filter(k => ROOM_BY[k].shrine).map(k => k + ' ' + ROOM_BY[k].shrine).join(' | '));
// travel map from the Snarewood shrine
G.tp('TV10', 47, 11); G.step(30); G.step(1, [], ['interact']); for (let i = 0; i < 40; i++) G.step(1); await new Promise(r => setTimeout(r, 900)); G.step(2);
for (let i = 0; i < 3; i++) { G.step(1, [], ['down']); G.step(2); } G.step(1, [], ['confirm']); for (let i = 0; i < 40; i++) G.step(1);
log.push('menu ' + (G.menu && G.menu.screen) + ' at ' + (G.menu && G.menu.id));
await snap('map_travel_thornveil');
G.step(1, [], ['pause']); G.step(5); G.step(1, [], ['pause']); G.step(5);
for (const [n, r, x, y] of [['map_world_thornveil', 'TV9', 60, 27], ['map_world_barrows', 'DB10', 72, 10], ['map_world_crimson', 'CM9', 20, 26]]) {
  G.tp(r, x, y); G.step(20); G.step(1, [], ['map']); G.step(3);
  for (let z = 0; z < 3; z++) { for (let k = 0; k < 30; k++) G.step(1); await snap(n + '_z' + (S.mapv && S.mapv.z)); G.step(1, [], ['confirm']); }
  G.step(1, [], ['map']); G.step(3);
}
return log;
