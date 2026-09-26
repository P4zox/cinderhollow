await boot(); window.__godS = true;
const res = {};
for (const ms of [0, 1]) {
  G.give({ items: { wings: 1, talon: 1, moonstep: ms } });
  G.tp('R1', 20, 10); S(20); await flush();
  const y0 = G.P.y; let minY = y0, j = 1; S(1, [], ['jump']);
  for (let i = 0; i < 200; i++) { if (G.P.vy > -30 && j < 3 && !G.P.ground) { S(1, [], ['jump']); j++; continue; } S(1, ['jump']); minY = Math.min(minY, G.P.y); if (G.P.ground && i > 5) break; }
  res['moonstep' + ms] = Math.round(y0 - minY);
}
return res;
