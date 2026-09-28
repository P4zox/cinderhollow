const ids = ['NV8','NV9','NV10','NV11','NV12','NV13','NV14','NV15','NV16','NV17','NV18','NV1','NV2','NVs','NV3','NV4','NV5','NV6','NV7','DU1','DU2','DU3','DU4','DU5','DU6','DU7','DU8',
  'DU9','DU10','DU11','DU12','DU13','DU14','DU15','DU16','DU17','DU18','DU19','C1','C2','C3','C4','C5','C6','M1','M2','M3','M4','M5','M6','D1','D2','D3','D4','D5','D6','D7','D8','CM1','CM2','CM3','CM4','CM5','CM6','CM7','CM8','W2','W3'];
for (const r of ids) G.SAVE.visited[r] = 1;
for (const r of ['NV10', 'NV17', 'DU11', 'DU19', 'NV2', 'NV4', 'NV6', 'DU2', 'DU5', 'DU7']) if (!G.SAVE.shrines.includes(r)) G.SAVE.shrines.push(r);
const shotMap = async (room, x, y, name, zooms) => {
  G.tp(room, x, y); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
  G.step(1, [], ['map']); G.step(20);
  for (let k = 0; k < zooms; k++) { G.step(1, [], ['confirm']); G.step(20); }
  await snap(name); G.step(1, [], ['map']); G.step(10); settle();
};
await shotMap('NV10', 20, 22, 'map_nv_mid', 0);
await shotMap('NV10', 20, 22, 'map_nv_far', 2);
await shotMap('DU10', 60, 17, 'map_du_mid', 0);
await shotMap('DU10', 60, 17, 'map_du_far', 2);
// travel map from the Mourners' Shrine
G.tp('NV17', 5, 54); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
G.step(1, [], ['interact']); G.step(10); await new Promise(r => setTimeout(r, 800)); G.step(2);
for (let k = 0; k < 3; k++) { G.step(1, [], ['down']); G.step(2); }
G.step(1, [], ['confirm']); G.step(20); await snap('travel_nv');
return G.state + ' ' + JSON.stringify(window.__ui.menu && window.__ui.menu.screen);
