await boot(); G.SETTINGS.god = true; const out = [];
out.push('shaders ' + G.SETTINGS.shaders + ' light ' + G.SETTINGS.light);
for (const [r, x, y] of [['K1', 24, 10], ['K7', 40, 32], ['K7', 60, 21], ['R5', 60, 11], ['C8', 40, 28], ['K9', 3, 10], ['K11', 13, 16]]) {
  G.tp(r, x, y); G.step(30);
  const t0 = performance.now(); for (let i = 0; i < 300; i++) G.step(1, [(i >> 5) % 2 ? 'left' : 'right']); const dt = (performance.now() - t0) / 300;
  out.push(`${r}@${x},${y}: ${dt.toFixed(2)} ms/frame (update+render, 300 frames)`);
}
return out;
