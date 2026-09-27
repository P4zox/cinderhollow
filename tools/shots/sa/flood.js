// DB14 The Floodgates: the jam rule, the wheel pairs, the chest, the drain, persistence.
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.seenAreas = { barrows: 1 };
const A = G.sa, log = [];
const st = () => ['lA', 'lB', 'lC'].map(id => A.KIT.byId[id] ? (A.KIT.byId[id].idx) : '?').join('') + ' gX ' + (A.kitOn('gX') ? 'open' : 'shut') + ' wheels ' + ['wA', 'wB', 'wC'].map(w => +A.kitOn(w)).join('');
const settle = () => { for (let i = 0; i < 240; i++) G.step(1); };
G.tp('DB14', 9, 4); settle(); log.push('start ' + st()); await snap('fg0_start');
// the jam: B's wheel is under water at the start
G.tp('DB14', 16, 21); G.step(20); G.step(1, [], ['interact']); settle(); log.push('B wheel under water -> ' + st());
G.step(1, [], ['interact']); G.step(30); G.step(1, [], ['interact']); G.step(30); log.push('two more jams -> ' + st());
// A is dry: turn A's wheel -> A fills, B drains
G.tp('DB14', 5, 21); G.step(20); G.step(1, [], ['interact']); settle(); log.push('A wheel -> ' + st()); await snap('fg1_A');
// B now dry: turn B's wheel -> B fills, C drains, the drain opens
G.tp('DB14', 16, 21); G.step(20); G.step(1, [], ['interact']); settle(); log.push('B wheel -> ' + st()); await snap('fg2_B');
// the chest in B's niche (swim up to it)
G.tp('DB14', 15, 9); G.step(30); G.P.face = -1; for (let i = 0; i < 4; i++) { G.step(1, ['left'], ['attack']); G.step(20); } settle(); log.push('emberstones ' + (G.SAVE.inv.emberstone || 0));
// persistence
G.tp('DB13', 3, 17); G.step(30); G.tp('DB14', 9, 4); settle(); log.push('re-entered ' + st());
// out through the drain to the Pearl Lagoon
G.tp('DB14', 35, 21); G.step(20); for (let i = 0; i < 180 && G.room === 'DB14'; i++) G.step(1, ['right']); log.push('walked east -> ' + G.room);
await snap('fg3_lagoon');
return log;
