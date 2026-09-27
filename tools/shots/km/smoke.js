await boot(); G.grantTechniques(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1;
const out = [];
const spots = [['f0a', 12, 16], ['f0b', 45, 16], ['f0c', 72, 16], ['f0d', 88, 16], ['f1a', 12, 36], ['f1b', 40, 32], ['f1c', 72, 36],
  ['f2a', 10, 56], ['f2b', 44, 56], ['f2c', 70, 56], ['f2d', 86, 56], ['f3a', 12, 76], ['f3b', 34, 76], ['f3c', 58, 76], ['f3d', 86, 76],
  ['f4a', 12, 96], ['f4b', 40, 96], ['f4c', 70, 96], ['f4d', 88, 96]];
for (const [n, x, y] of spots) {
  G.tp('T1', x, y); G.step(40);
  await snap(n);
  out.push(n + ' ' + JSON.stringify(G.step(1).p));
}
out.push('objs ' + G.KIT.objs.length);
return out;
