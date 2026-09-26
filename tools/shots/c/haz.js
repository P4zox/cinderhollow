await boot();
const P = () => G.P, log = {};
const C = window.__cm.CM;
// pool: stand in the court basin
G.tp('CM2', 10, 37); G.step(5); let h0 = P().hp; G.step(120); log.pool = { lost: Math.round(h0 - P().hp), fp: Math.round(P().fp), inPool: C.pools.length };
await snap('haz_pool');
// rain: force a downpour, stand in the open vs sheltered
G.tp('CM2', 5, 36); G.step(5); C.rain.st = 'pour'; C.rain.t = 3; h0 = P().hp = G.D.maxHp; G.step(90); log.rainOpen = Math.round(h0 - P().hp);
await snap('haz_rain');
G.tp('CM2', 19, 36); G.step(5); C.rain.st = 'pour'; C.rain.t = 3; h0 = P().hp = G.D.maxHp; G.step(90); log.rainShelter = Math.round(h0 - P().hp);
// chandelier: stand under the first gallery chandelier
G.tp('CM4', 19, 10); G.step(2); h0 = P().hp = G.D.maxHp; let hit = -1;
for (let k = 0; k < 240; k++) { G.step(1); P().x = 19 * 16 + 8; if (P().hp < h0 && hit < 0) hit = k; if (k === 40) await snap('haz_chand'); }
log.chandelier = { hitAt: hit, lost: Math.round(h0 - P().hp) };
// portrait ambush
G.tp('CM4', 11, 10); G.step(5); const n0 = G.enemies.length; for (let k = 0; k < 8; k++) G.step(1, ['right']);
G.step(40); await snap('haz_ambush'); log.ambush = { before: n0, after: G.enemies.length, types: G.enemies.map(e => e.type + ':' + e.state) };
G.step(60); await snap('haz_ambush2');
return log;
