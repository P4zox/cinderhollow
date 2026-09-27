await boot(); G.grantTechniques(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { crown: 1 }; const out = [];
for (const [r, x, y] of [['X3', 30, 10], ['X3', 10, 10], ['X4', 5, 10], ['X2', 10, 26]]) {
  G.tp(r, x, y); G.step(60); const s0 = G.state; G.step(1, ['jump'], ['jump']); G.step(8, ['jump']);
  out.push(`${r}(${x},${y}) ${s0} -> y ${Math.round(G.P.y)} ${G.P.state} ctrl ${G.P.ctrlLock && G.P.ctrlLock.toFixed(2)} cut ${!!G.cut}`);
}
return out;
