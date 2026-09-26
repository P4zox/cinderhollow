await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 } });
const out = {};
for (const up of [0, 1]) {
  if (up) G.SAVE.flags['sf:stair'] = 1; else delete G.SAVE.flags['sf:stair'];
  G.tp('X4', 1, 2); S(2);
  let minY = 1e9;
  for (let k = 0; k < 6; k++) { G.P.y = 40; G.P.vy = -420; G.P.x = 1 * 16 + 8; for (let i = 0; i < 20; i++) { S(1, ['up']); minY = Math.min(minY, G.P.y); } }
  out[up ? 'afterStair' : 'beforeStair'] = { minY: Math.round(minY), room: G.room };
}
return out;
