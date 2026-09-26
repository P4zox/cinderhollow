await boot(); G.give({ stats: { vig: 60 } }); G.SAVE.items.tidebreath = 1;
const shots = [['NV3', 8, 11], ['NV3', 10, 29], ['NV4', 22, 16], ['NV4', 38, 16], ['NV4', 64, 16], ['NV2', 8, 10], ['NV6', 14, 7], ['NV1', 10, 21], ['C2', 37, 10]];
for (const [r, x, y] of shots) {
  G.tp(r, x, y); for (let i = 0; i < 20; i++) { G.step(6); G.P.hp = 9999; }
  await snap(`${r}_${x}_a`);
  if (r === 'NV3' || r === 'NV4') { G.nvToll(); G.step(100); await snap(`${r}_${x}_b`); }
}
return 'ok';
