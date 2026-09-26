await boot(); G.give({ items: { talon: 1 } });
const out = {};
for (const [id, x, y] of [['C2', 3, 10], ['TV1', 2, 12], ['TV2', 20, 10], ['TV3', 30, 10], ['TV4', 30, 10], ['TV5', 12, 23], ['TV5', 20, 9], ['TV6', 10, 9], ['TV6', 40, 9], ['TV7', 20, 9], ['TV8', 10, 10]]) {
  G.tp(id, x, y); G.step(40); await snap(`${id}_${x}_${y}`);
  out[id + x] = G.step(1).p;
}
return out;
