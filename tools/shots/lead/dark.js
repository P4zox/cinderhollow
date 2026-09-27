await boot(); G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1;
for (const [r, x, y] of [['NV10', 20, 56], ['TV9', 20, 28], ['DB11', 10, 10], ['CM9', 10, 22], ['NV4', 20, 16], ['C8', 10, 28]]) {
  try { G.tp(r, x, y); } catch (e) { continue; }
  for (const b of [1, 2]) { G.SETTINGS.bright = b; G.step(30); await snap(`dk_${r}_${b}`); }
}
G.SETTINGS.bright = 1; return 'ok';
