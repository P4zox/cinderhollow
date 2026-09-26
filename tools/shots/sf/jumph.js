await boot();
G.give({ items: { wings: 1, talon: 1, moonstep: 1 } });
Object.assign(G.SAVE.flags, { 'boss:astrel': 1 });
const res = {};
for (const n of [1, 2, 3]) {
  G.tp('SF7', 20, 16); S(20);
  const y0 = G.P.y; let minY = y0, j = 1, log = [];
  S(1, [], ['jump']);
  for (let i = 0; i < 200; i++) {
    if (G.P.vy > -30 && j < n && !G.P.ground) { S(1, [], ['jump']); j++; log.push(Math.round(G.P.vy)); continue; }
    S(1, ['jump']); minY = Math.min(minY, G.P.y);
    if (G.P.ground && i > 5) break;
  }
  res['j' + n] = { rise: Math.round(y0 - minY), log, aj: G.P.airJumps };
}
return res;
