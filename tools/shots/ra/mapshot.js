await boot(); G.SETTINGS.god = true;
for (const id of Object.keys(window.__ra.rooms)) G.SAVE.visited[id] = 1;
const out = [];
for (const [r, x, y, z] of [['R5', 60, 8, 0], ['C8', 40, 28, 0], ['K7', 40, 26, 0], ['R5', 60, 8, 1], ['C8', 40, 28, 1], ['K7', 40, 26, 1]]) {
  G.tp(r, x, y); G.step(10);
  G.step(1, [], ['map']); G.step(5);
  for (let i = 0; i < (z === 0 ? 2 : 0); i++) { G.step(1, [], ['confirm']); G.step(3); }   // 1 -> 2 -> 0 (widest)
  G.step(60); out.push(r + ' map state ' + G.state); await snap(`map_${r}_z${z}`);
  G.step(1, [], ['map']); G.step(5); if (G.state !== 'play') { G.step(1, [], ['pause']); G.step(5); }
}
return out;
