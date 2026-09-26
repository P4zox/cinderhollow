await boot();
const res = {};
async function climb(talon, wings) {
  G.SAVE.items.talon = talon ? 1 : 0; G.SAVE.items.wings = wings ? 1 : 0;
  G.tp("C2", 3, 10); G.enemies.length = 0; G.step(20);
  let maxUp = 999, rooms = new Set();
  let dir = -1;
  for (let i = 0; i < 900; i++) {
    const P = G.P;
    rooms.add(G.room);
    if (G.room === 'TV2') break;
    let hold = [], tap = [];
    if (G.room === 'TV1' && P.y < 6 * 16 && P.y > 2 * 16) hold = ['left'];
    else if (P.state === 'wall') { tap = ['jump']; dir = -P.wallDir; hold = [dir > 0 ? 'right' : 'left']; }
    else if (P.ground) { tap = ['jump']; hold = ['left']; dir = -1; }
    else { hold = [dir > 0 ? 'right' : 'left', 'jump']; if (P.airJumps > 0 && P.vy > 0) tap = ['jump']; }
    G.enemies.length = 0; G.step(1, hold, tap);
    if (G.room === 'C2') maxUp = Math.min(maxUp, P.y);
  }
  return { talon, wings, end: G.room, rooms: [...rooms].join(','), p: G.step(1).p, minY_C2: Math.round(maxUp) };
}
res.noTalon = await climb(false, false);
res.wingsOnly = await climb(false, true);
res.talon = await climb(true, false);
await snap('climb_end');
return res;
