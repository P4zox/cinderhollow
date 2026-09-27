await boot(); G.SAVE.items.wings = 1;
const spots = [['g_f0a', 14, 16], ['g_f0b', 50, 16], ['g_f0c', 72, 16], ['g_f0d', 89, 16], ['g_f1a', 12, 36], ['g_f1b', 42, 32], ['g_f1c', 72, 36],
  ['g_f2a', 12, 56], ['g_f2b', 44, 56], ['g_f2c', 68, 56], ['g_f2d', 86, 56], ['g_f3a', 12, 76], ['g_f3b', 36, 76], ['g_f3c', 60, 76], ['g_f3d', 86, 76],
  ['g_f4a', 3, 96], ['g_f4b', 40, 96], ['g_f4c', 70, 96], ['g_f4d', 88, 96]];
for (const [n, x, y] of spots) { G.tp('T1', x, y); G.SETTINGS.god = true; G.step(230); await snap(n); }
return 'ok';
