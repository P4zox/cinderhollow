await boot(); G.give({ items: { talon: 1 } });
for (const k of ['boss:coven', 'cut:coven', 'boss:warden', 'cut:warden']) G.SAVE.flags[k] = 1;
const T = 16, log = [];
async function goTo(tx, ty, maxF = 600) {       // walk/jump to stand on cell (tx, ty) of the current room
  const fx = tx * T + 8, fy = (ty + 1) * T;
  for (let i = 0; i < maxF; i++) {
    G.enemies.length = 0;
    const P = G.P, dx = fx - P.x;
    if (P.ground && Math.abs(dx) < 6 && Math.abs(P.y - fy) < 2) return true;
    const hold = [], tap = [];
    if (Math.abs(dx) > 4) hold.push(dx > 0 ? 'right' : 'left');
    const higher = fy < P.y - 4;
    const ahead = P.x + Math.sign(dx) * 8, gnd = [1, 2, 3].some(k => { const t = G.tileAt(Math.floor(ahead / T), Math.floor((P.y + 2) / T)); return t === 1 || t === 2; });
    if (P.ground && ((higher && Math.abs(dx) < 5.5 * T) || (!gnd && Math.abs(dx) > 10))) { tap.push('jump'); hold.push('jump'); }
    if (!P.ground && (higher || Math.abs(dx) > 24)) hold.push('jump');
    if (P.state === 'wall' && higher) tap.push('jump');
    G.step(1, hold, tap);
  }
  return false;
}
async function route(name, room, start, pts) {
  if (G.state !== 'play') { G.step(200, [], ['jump']); } G.tp(room, ...start); G.P.hp = 999; G.step(10);
  for (const [x, y] of pts) { const ok = await goTo(x, y); if (!ok) { log.push(`${name}: FAILED at target ${x},${y} p=${JSON.stringify(G.step(1).p)} room=${G.room}`); return; } }
  log.push(`${name}: OK (room ${G.room})`);
}
await route('TV5 climb', 'TV5', [8, 23], [[15, 20], [9, 17], [13, 14], [12, 12], [18, 9]]);
await route('TV6 pit', 'TV6', [3, 9], [[23, 7], [32, 7], [40, 7], [45, 9]]);
await route('TV3 shelf', 'TV3', [20, 10], [[15, 7], [12, 4]]);
await route('TV2 to shaft', 'TV2', [12, 10], [[9, 7], [5, 4]]);
await snap('route_end');
return log;
