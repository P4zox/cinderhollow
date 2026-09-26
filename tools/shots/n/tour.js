await boot();
G.give({ items: { talon: 1, wings: 1 } });
const out = {};
for (const [id, x, y] of [['C2', 37, 10], ['NV1', 10, 21], ['NV1', 20, 21], ['NV2', 6, 10], ['NV3', 3, 11], ['NV3', 10, 41], ['NV4', 20, 16], ['NV4', 60, 16], ['NV5', 30, 10], ['NV6', 30, 14], ['NV7', 40, 12]]) {
  G.tp(id, x, y); G.step(40);
  await snap(`${id}_${x}_${y}`);
  out[id + x] = G.step(1);
}
return out;
