await boot(); G.SETTINGS.god = true;
const mine = ['R5', 'R7', 'C8', 'C10', 'K5', 'K8', 'K6'];
for (const id of mine.concat(['R1', 'C2', 'C4', 'K1'])) if (!G.SAVE.shrines.includes(id)) G.SAVE.shrines.push(id);
const out = [];
for (const r of ['R5', 'C8', 'K5']) { G.tp(r, r === 'R5' ? 104 : r === 'C8' ? 48 : 22, r === 'R5' ? 8 : r === 'C8' ? 28 : 10); G.step(10); window.__ra.travel(); G.step(40); out.push(G.state + ' ' + (G.menu && G.menu.id)); await snap('travel_' + r); G.step(1, [], ['pause']); G.step(5); }
out.push('shrine names: ' + mine.map(id => window.__ra.rooms[id].shrine).join(' / '));
return out;
