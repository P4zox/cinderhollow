await boot();
G.SAVE.seenAreas = { barrows: 1, necropolis: 1, catacombs: 1 }; window.__db.SETTINGS.god = true;
const out = [], S = () => [G.room, Math.round(G.P.x), Math.round(G.P.y), G.P.state, +window.__db.DBS.breath.toFixed(1)];
G.tp('NV1', 8, 21); G.step(10);
G.step(40, ['left']); G.step(80, ['down']); out.push(['noTB', S()]);
G.give({ items: { tidebreath: 1 } });
G.step(60, ['down', 'left']); out.push(['dive', S()]);
for (let i = 0; i < 40; i++) { G.step(10, ['right', 'down']); if (G.P.x > 280) break; }
out.push(['under', S()]);
G.step(90, ['up', 'right']); out.push(['emerge', S()]);
for (let i = 0; i < 5; i++) G.step(8, ['right'], ['jump']);
G.step(30, ['right']); out.push(['out', S()]);
await snap('n1');
return out;
