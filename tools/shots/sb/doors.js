const out = []; G.SETTINGS.god = 1; const K = G.KIT;
const tpS = (r, x, y) => { G.tp(r, x, y); for (let i = 0; i < 4; i++) { G.step(10); settle(); } G.enemies.length = 0; };
const use = () => { const r0 = G.room; G.step(1, [], ['interact']); for (let i = 0; i < 150 && G.room === r0; i++) G.step(1); for (let i = 0; i < 40; i++) { G.step(1); settle(); } G.enemies.length = 0; return G.room + '@' + (G.P.x / 16 | 0) + ',' + ((G.P.y / 16 | 0) - 1); };
const walkTo = (tx, n = 400) => { for (let i = 0; i < n && Math.abs(G.P.x - (tx * 16 + 8)) > 3; i++) G.step(1, [G.P.x < tx * 16 + 8 ? 'right' : 'left']); G.step(10); return (G.P.x / 16).toFixed(1); };
tpS('NV3', 15, 41); out.push('NV3 door -> ' + use()); out.push('  back -> ' + use());
tpS('NV4', 14, 16); out.push('NV4 door -> ' + use() + ' barred hint ' + G.sb.hint.bar + ' gate ' + K.byId.bar.on);
out.push('  walk left blocked at x ' + walkTo(30, 200));
tpS('NV10', 36, 28); G.step(1, ['right']); G.step(1, [], ['attack']); for (let i = 0; i < 180; i++) G.step(1);
out.push('  lever pulled: gate ' + K.byId.bar.on + ' flag ' + G.SAVE.flags['x3:NV10:bar']);
out.push('  walk to door x ' + walkTo(44) + ' -> ' + use());
tpS('NV10', 20, 7); out.push('NV10 summit before the Executioners: passage cell solid ' + !!(G.room && window.__sys.roomObj.grid[6 * 48 + 38]));
G.SAVE.flags['boss:executioners'] = 1; tpS('NV8', 10, 10); tpS('NV10', 20, 7);
out.push('  after: passage open ' + (window.__sys.roomObj.grid[6 * 48 + 38] === 0) + ' walk x ' + walkTo(44) + ' -> ' + use());
await snap('door_nv6');
out.push('  NV6 door -> ' + use());
await snap('door_nv10_summit');
tpS('DU4', 17, 35); out.push('DU4 door -> ' + use()); out.push('  back -> ' + use());
tpS('DU5', 15, 11); out.push('DU5 door -> ' + use() + ' barred hint ' + G.sb.hint.bar + ' gate ' + K.byId.bar.on);
tpS('DU11', 15, 11); G.step(1, ['left']); G.step(1, [], ['attack']); for (let i = 0; i < 180; i++) G.step(1);
out.push('  lever pulled: gate ' + K.byId.bar.on);
out.push('  walk x ' + walkTo(3) + ' -> ' + use());
// the Ossuary: slam through the throne landing
G.SAVE.items.slam = 1; tpS('NV10', 2, 7); G.step(1, ['jump'], ['jump']); for (let i = 0; i < 14; i++) G.step(1, ['jump']); G.step(1, ['down'], ['heavy']); for (let i = 0; i < 60; i++) G.step(1, ['down']);
out.push('slam: y ' + (G.P.y / 16).toFixed(1) + ' broke ' + (window.__sys.roomObj.grid[8 * 48 + 2] === 0));
for (let i = 0; i < 200 && G.room === 'NV10'; i++) G.step(1, ['left']);
out.push('  -> ' + G.room);
// the Nameless Tomb: slam the oasis mound
tpS('DU15', 10, 12); G.step(1, ['jump'], ['jump']); for (let i = 0; i < 14; i++) G.step(1, ['jump']); G.step(1, ['down'], ['heavy']); for (let i = 0; i < 90 && G.room === 'DU15'; i++) G.step(1, ['down']);
for (let i = 0; i < 90 && G.room === 'DU15'; i++) G.step(1, ['down', 'jump'], i % 10 === 0 ? ['jump'] : []);
out.push('oasis slam -> ' + G.room + ' at ' + (G.P.x / 16).toFixed(1) + ',' + (G.P.y / 16).toFixed(1));
// the vista bench at the oasis
tpS('DU15', 31, 12); G.step(1, [], ['interact']); for (let i = 0; i < 120; i++) G.step(1);
out.push('vista seated ' + !!window.__sys.SYS.vista + ' enemies ' + G.enemies.length + ' logged ' + JSON.stringify(window.__sys.x3().vistas) + ' lore ' + JSON.stringify(window.__sys.x3().lore));
await snap('vista_oasis');
G.step(1, ['left']); for (let i = 0; i < 90; i++) G.step(1);
return out;
