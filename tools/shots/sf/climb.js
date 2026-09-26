await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 } });
const out = {};
for (const [side, tx, dir, away] of [['E', 21, 'right', 'left'], ['W', 2, 'left', 'right']]) {
  G.tp('X4', tx, 10); S(20); await flush();
  let minY = 1e9, rooms = new Set();
  for (let k = 0; k < 40; k++) {
    // jump at the wall, double jump, cling, then wall-jump repeatedly back into it
    S(1, [dir], ['jump']); S(12, [dir, 'jump']); S(1, [dir], ['jump']); S(14, [dir, 'jump']);
    for (let w = 0; w < 6; w++) { S(4, [dir]); S(1, [], ['jump']); S(6, [away, 'jump']); S(10, [dir]); minY = Math.min(minY, G.P.y); rooms.add(G.room); }
    minY = Math.min(minY, G.P.y); rooms.add(G.room);
    if (G.room !== 'X4') break;
    G.tp('X4', tx, 10); S(10); await flush();
  }
  out[side] = { minY: Math.round(minY), rooms: [...rooms] };
}
return out;
