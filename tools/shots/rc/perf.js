await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { spire: 1, deep: 1, crown: 1, lastfield: 1 }; const out = [];
for (const [r, x, y] of [['SP2', 30, 10], ['SP8', 62, 14], ['D11', 60, 35], ['D5', 24, 10], ['X7', 36, 26], ['X3', 24, 10], ['LF1', 60, 16], ['D13', 30, 4]]) {
  G.tp(r, x, y); G.step(60);
  const t0 = performance.now(); for (let i = 0; i < 240; i++) G.step(1, [i % 120 < 60 ? 'right' : 'left']); const ms = (performance.now() - t0) / 240;
  out.push(`${r}: ${ms.toFixed(2)} ms/frame (update+render)`);
}
out.push('shaders ' + G.SETTINGS.shaders + ' light ' + G.SETTINGS.light);
return out;
