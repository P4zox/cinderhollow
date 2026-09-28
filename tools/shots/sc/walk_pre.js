// walk-test prelude (after pilot.js): every ability, bosses of the loops down, foes removed, every room change logged
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { moonstep: 1, wings: 1, talon: 1, tidebreath: 1 });
G.SETTINGS.god = 1;
for (const f of ['boss:astrel', 'boss:first_ember', 'boss:oswin', 'boss:orrery', 'sc:seal', 'sf:stair', 'boss:enforcer', 'boss:saint0']) G.SAVE.flags[f] = 1;
const ROOMLOG = []; let lastRoom = null;
{ const _s = G.step; G.step = (n = 60, h = [], t = []) => { let r; for (let i = 0; i < n; i++) { r = _s(1, h, t); G.enemies.length = 0; if (G.room !== lastRoom) { ROOMLOG.push(`${lastRoom || '-'} -> ${G.room} @${px().toFixed(1)},${py().toFixed(1)}`); lastRoom = G.room; } } return r; }; }
const until = (cond, hold = [], max = 600) => { for (let i = 0; i < max && !cond(); i++) G.step(1, hold); return cond(); };
const exitTo = (dir, room, max = 400) => { const k = dir > 0 ? 'right' : 'left'; for (let i = 0; i < max && G.room !== room; i++) G.step(1, [k]); log((G.room === room ? 'into ' : 'FAILED into ') + room); return G.room === room; };
const expect = room => { if (G.room !== room) { log('EXPECTED ' + room + ' got ' + G.room); return false; } return true; };
// hold a direction until the room changes to `room`; if stuck on the ground, hop; flip after a long stall
const wander = (dir, room, max = 2000) => {
  let lastX = G.P.x, stall = 0, flips = 0;
  for (let i = 0; i < max && G.room !== room; i++) {
    const k = dir > 0 ? 'right' : 'left';
    if (stall > 12 && G.P.ground) {   // blocked: a full jump (double jump at the top) toward the wall
      G.step(1, [k, 'jump'], ['jump']); for (let j = 0; j < 30 && !G.P.ground; j++) G.step(1, [k, 'jump'], j === 16 ? ['jump'] : []);
      stall = Math.abs(G.P.x - lastX) < 4 ? stall + 20 : 0; lastX = G.P.x;
      if (stall > 100) { dir = -dir; stall = 0; flips++; }
      continue;
    }
    G.step(1, [k]);
    if (Math.abs(G.P.x - lastX) < 0.5) stall++; else stall = 0; lastX = G.P.x;
  }
  log((G.room === room ? 'wandered into ' : 'FAILED wander to ') + room + (flips ? ' flips=' + flips : '')); return G.room === room;
};
const dropThrough = () => { G.step(1, ['down', 'jump'], ['jump']); G.step(30, ['down']); };
// walk to tile x, hopping over whatever blocks the way (a full jump, double jump at the top)
const go = (x, max = 1500) => {
  let lastX = G.P.x, stall = 0;
  for (let i = 0; i < max; i++) {
    const d = x - px(); if (Math.abs(d) < 0.3 && G.P.ground) break;
    const k = d > 0 ? 'right' : 'left';
    const ahead = [1].some(k => G.xs.hazardAt(Math.floor(px() + (d > 0 ? k : -k)), Math.floor(py())) || G.xs.hazardAt(Math.floor(px() + (d > 0 ? k : -k)), Math.floor(py()) - 1));
    if ((stall > 8 || ahead) && G.P.ground) { G.step(1, [k, 'jump'], ['jump']); for (let j = 0; j < 34 && !G.P.ground; j++) G.step(1, [k, 'jump'], j === 14 ? ['jump'] : []); stall = 0; lastX = G.P.x; continue; }
    G.step(1, [k]); if (Math.abs(G.P.x - lastX) < 0.3) stall++; else stall = 0; lastX = G.P.x;
  }
  const ok = Math.abs(x - px()) < 0.6; log((ok ? 'went to ' : 'FAILED go to ') + x); return ok;
};
