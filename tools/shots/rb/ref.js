await boot(); G.SETTINGS.god = true;
const spots = [['r_M1', 'M1', 8, 24], ['r_M2', 'M2', 22, 10], ['r_M4', 'M4', 5, 10], ['r_M3', 'M3', 8, 10], ['r_A2', 'A2', 22, 10], ['r_A5', 'A5', 22, 10], ['r_A4', 'A4', 10, 24], ['r_A1', 'A1', 10, 22],
  ['r_HF6', 'HF6', 8, 12], ['r_HF2', 'HF2', 8, 14], ['r_HF5', 'HF5', 10, 16], ['r_HF7', 'HF7', 10, 13], ['r_HF1', 'HF1', 34, 10]];
for (const [n, r, x, y] of spots) { G.tp(r, x, y); G.step(90); await snap(n); }
return 'ok';
