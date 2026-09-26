await boot();
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1 };
const out = []; window.__dbLog = [];
const run = (n, hold = [], tapf) => { for (let i = 0; i < n; i++) { G.step(10, hold, tapf ? tapf(i) : []); G.P.hp = G.D.maxHp; } };
// pilgrim + barnacle on level B/C of DB4; eel in the chapel pool
G.tp('DB4', 12, 17); run(1);
out.push(['DB4 enemies', G.enemies.map(e => `${e.type}:${e.state}:${Math.round(e.x)},${Math.round(e.y)}`)]);
run(80);
await snap('e1');
out.push(['hits standing', window.__dbLog.map(h => h[2]).reduce((a, k) => (a[k] = (a[k] || 0) + 1, a), {})]);
// fight back: attack toward the barnacle
window.__dbLog = [];
run(60, [], i => ['attack']);
out.push(['after attacking', G.enemies.map(e => `${e.type}:${e.state}:${e.hp}`)]);
await snap('e2');
// eel: stand at the DB2 west landing edge over water; walk near
G.tp('DB2', 6, 9); run(1); window.__dbLog = [];
run(120);
out.push(['eel hits on landing', window.__dbLog.length, G.enemies.map(e => `${e.type}:${e.st || ''}:${e.state}:${Math.round(e.x)},${Math.round(e.y)}`)]);
await snap('e3');
// hidden pilgrim in level C rises
G.tp('DB4', 17, 24); run(1); const hp0 = G.enemies.find(e => e.type === 'db_pilgrim' && e.y > 380); out.push(['hidden', hp0 && hp0.state]);
G.step(40, ['left']); out.push(['after approach', hp0 && hp0.state]);
return out;
