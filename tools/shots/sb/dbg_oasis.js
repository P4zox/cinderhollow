G.SETTINGS.god = 1; G.SAVE.items.slam = 1; G.tp('DU15', 10, 12); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
const out = []; const R = window.__sys.roomObj;
const col = () => [13,14,15,16,17].map(y => R.grid[y * R.w + 10]).join('');
out.push('grid col10 rows13-17 ' + col());
G.step(1, ['jump'], ['jump']); for (let i = 0; i < 14; i++) G.step(1, ['jump']); G.step(1, ['down'], ['heavy']);
for (let i = 0; i < 60; i++) { G.step(1, ['down']); if (i % 10 === 0) out.push(i + ' ' + G.P.state + ' y ' + (G.P.y / 16).toFixed(2) + ' g ' + G.P.ground + ' ' + col()); }
for (let i = 0; i < 60 && G.room === 'DU15'; i++) { G.step(1, ['down', 'jump'], i % 10 === 0 ? ['jump'] : []); if (i % 10 === 0) out.push('d ' + G.P.state + ' y ' + (G.P.y / 16).toFixed(2)); }
out.push(G.room);
return out;
