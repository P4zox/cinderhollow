await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.give({ items: { talon: 1, wings: 1, tidebreath: 1, moonstep: 1 } }); const S = window.__sys, RB = window.__rb, log = [];
const mine = 'W3,M7,M8,M9,M10,M11,M12,M13,M14,W5,A8,A9,A10,A11,A12,A13,A14,A15,A16,HF8,HF9,HF10,HF11,HF12,HF13,HF14,HF15,HF16'.split(',');
for (const id of Object.keys(RB.ROOM_BY)) if (!RB.ROOM_BY[id].test) G.SAVE.visited[id] = 1;
G.SAVE.seenAreas = Object.fromEntries(Object.keys(RB.ROOM_BY).map(k => [RB.ROOM_BY[k].biome, 1]));
G.SAVE.shrines.push(...Object.keys(RB.ROOM_BY).filter(k => RB.ROOM_BY[k].shrine));
log.push('my shrines: ' + mine.filter(k => RB.ROOM_BY[k].shrine).map(k => k + ' ' + RB.ROOM_BY[k].shrine).join(' | '));
// travel map from the Weeping Tree shrine
G.tp('M7', 6, 20); G.step(30); G.step(1, [], ['interact']); for (let i = 0; i < 40; i++) G.step(1); await new Promise(r => setTimeout(r, 900)); G.step(2);
log.push('menu ' + (G.menu && G.menu.screen));
for (let i = 0; i < 3; i++) { G.step(1, [], ['down']); G.step(2); } G.step(1, [], ['confirm']); for (let i = 0; i < 40; i++) G.step(1);
log.push('menu ' + (G.menu && G.menu.screen) + ' at ' + (G.menu && G.menu.id));
await snap('map_travel_mire');
for (let k = 0; k < 40 && G.menu && !/^A(8|10)$/.test(G.menu.id); k++) { G.step(1, [], ['down']); G.step(3); }
for (let i = 0; i < 30; i++) G.step(1); await snap('map_travel_arch'); log.push('travel at ' + (G.menu && G.menu.id));
for (let k = 0; k < 60 && G.menu && !/^HF1[01]$/.test(G.menu.id); k++) { G.step(1, [], ['down']); G.step(3); }
for (let i = 0; i < 30; i++) G.step(1); await snap('map_travel_frost'); log.push('travel at ' + (G.menu && G.menu.id));
G.step(1, [], ['pause']); G.step(5); G.step(1, [], ['pause']); G.step(5);
// the world map, zoomed out, centred on each wing
for (const [n, r, x, y] of [['map_world_mire', 'M10', 20, 10], ['map_world_arch', 'A8', 30, 30], ['map_world_frost', 'HF8', 10, 30]]) {
  G.tp(r, x, y); G.step(20); G.step(1, [], ['map']); G.step(3);
  for (let z = 0; z < 3; z++) { for (let k = 0; k < 30; k++) G.step(1); await snap(n + '_z' + (S.mapv && S.mapv.z)); G.step(1, [], ['confirm']); }
  log.push(n + ' state ' + G.state);
  G.step(1, [], ['map']); G.step(3);
}
return log;
