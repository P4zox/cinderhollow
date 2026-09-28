// world map (widest zoom) centred on each SC region, every room visited; then the travel menu with the SC shrines lit
await boot(); G.SETTINGS.god = 1;
const ids = Object.keys(window.__sys.x3 ? {} : {}); const all = window.__ra ? Object.keys(window.__ra.rooms) : [];
for (const id of all) G.SAVE.visited[id] = 1;
const out = [];
for (const [r, x, y, z] of [['SF11', 60, 26, 0], ['NH8', 12, 60, 0], ['E5', 7, 27, 0], ['H2', 6, 10, 0], ['SF11', 60, 26, 1]]) {
  G.tp(r, x, y); G.step(10);
  G.step(1, [], ['map']); G.step(5);
  for (let i = 0; i < (z === 0 ? 2 : 0); i++) { G.step(1, [], ['confirm']); G.step(3); }
  G.step(60); out.push(r + ' map ' + G.state); await snap(`map_${r}_z${z}`);
  G.step(1, [], ['map']); G.step(5); if (G.state !== 'play') { G.step(1, [], ['pause']); G.step(5); }
}
const shr = ['SF10', 'SF11', 'NH8', 'NH11', 'E4', 'E5', 'H2'];
for (const id of shr.concat(['SF1', 'SF3', 'NH1', 'E1', 'H1'])) if (!G.SAVE.shrines.includes(id)) G.SAVE.shrines.push(id);
for (const r of ['SF10', 'NH8', 'E5', 'H2']) { const d = window.__ra.rooms[r]; const s = (d.spawns || []).find(o => o.t === 'shrine') || {}; G.tp(r, 6, 6); G.step(10); G.xs.travel(); G.step(40); out.push('travel ' + G.state); await snap('travel_' + r); G.step(1, [], ['pause']); G.step(5); }
out.push('shrine names: ' + shr.map(id => id + '=' + window.__ra.rooms[id].shrine).join(' / '));
return out;
