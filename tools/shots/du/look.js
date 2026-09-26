await boot(); G.grantTechniques(); const o = [];
for (const [id, x, y, n] of [['DU1', 6, 10, 'du1'], ['DU1', 30, 10, 'du1b'], ['DU2', 8, 10, 'du2'], ['DU2', 26, 16, 'du2b'], ['DU3', 16, 14, 'du3'], ['DU3', 40, 18, 'du3b'], ['DU3', 56, 14, 'du3c'],
  ['DU4', 8, 20, 'du4'], ['DU5', 20, 11, 'du5'], ['DU5', 40, 8, 'du5b'], ['DU6', 20, 11, 'du6'], ['DU7', 20, 17, 'du7'], ['DU8', 30, 14, 'du8']]) {
  G.tp(id, x, y); G.step(45); await snap(n);
}
return o;
