await boot();
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 } });
G.SAVE.flags['sf:stair'] = 1; G.SAVE.seenAreas = { starfall: 1, crown: 1 };
const shots = [['X4', 6, 10], ['SF1', 4, 22], ['SF1', 18, 4], ['SF2', 6, 12], ['SF2', 30, 12], ['SF2', 50, 12], ['SF3', 10, 12], ['SF4', 5, 48], ['SF4', 12, 21], ['SF4', 16, 12], ['SF5', 8, 12], ['SF6', 4, 12], ['SF6', 6, 48], ['SF8', 20, 12], ['SF7', 6, 16], ['SF9', 6, 12]];
for (const [r, x, y] of shots) { G.tp(r, x, y); G.step(40); await snap(`${r}_${x}_${y}`); }
return 'ok';
