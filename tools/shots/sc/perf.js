await boot(); G.SETTINGS.god = 1; const out = [];
for (const [r, x, y] of [['SF2', 32, 9], ['SF11', 58, 20], ['SF11', 20, 26], ['NH8', 20, 24], ['NH11', 30, 12], ['E5', 42, 27], ['SF16', 5, 10], ['H3', 20, 10], ['NH2', 28, 10]]) {
  G.tp(r, x, y); G.step(60);
  const t0 = performance.now(); for (let i = 0; i < 200; i++) G.step(1); const dt = (performance.now() - t0) / 200;
  out.push(`${r}@${x},${y}: ${dt.toFixed(2)} ms/frame (update+render)`);
}
return out;
