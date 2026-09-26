await boot();
G.give({ items: { talon: 1 } });
G.SAVE.seenAreas = { barrows: 1, crown: 1 };
const out = [], S = () => [G.room, Math.round(G.P.x), Math.round(G.P.y), G.P.state, +window.__db.DBS.breath.toFixed(1), Math.round(G.P.hp)];
// A. no hook: try to swim/jump west across the tide
G.tp('DB2', 31, 9); G.step(10);
G.step(30, ['left']);
for (let i = 0; i < 40; i++) { G.step(14, ['left'], i % 2 ? ['jump'] : []); G.P.hp = G.D.maxHp; }
out.push(['no-hook after 10s of trying', S()]); await snap('w1_nohook');
// climb out by the east wall
for (let i = 0; i < 10; i++) G.step(6, ['right'], ['jump']);
G.step(40, ['right']); out.push(['back on east landing', S()]);
// B. Tidebreath: dive under the tide and cross
G.give({ items: { talon: 1, tidebreath: 1 } });
G.tp('DB2', 31, 9); G.step(10); G.step(30, ['left']);
G.step(40, ['left', 'down']);
for (let i = 0; i < 30; i++) { G.step(10, ['left', 'down']); G.P.hp = G.D.maxHp; }
out.push(['TB under the tide', S()]);
for (let i = 0; i < 20; i++) { G.step(10, ['left', 'up']); }
for (let i = 0; i < 10; i++) G.step(6, ['left'], ['jump']);
G.step(30, ['left']);
out.push(['TB crossed', S()]); await snap('w2_tb');
// C. generic room (Proving Grounds T0): inject a pool and swim with/without the item
const def = G.room && null;
return out;
