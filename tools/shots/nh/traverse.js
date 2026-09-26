await boot();
const log = [];
G.give({ items: {} });   // NO wall-jump / double jump: basic moves only
G.nhGod(true);
const R = () => G.nhRoom();
const solid = (tx, ty) => { const r = R(); if (tx < 0 || ty < 0 || tx >= r.w || ty >= r.h) return true; const t = r.grid[ty * r.w + tx]; return t === 1 || t === 5 || t === 7 || t >= 60; };
const plat = (tx, ty) => { const r = R(); if (tx < 0 || ty < 0 || tx >= r.w || ty >= r.h) return false; return r.grid[ty * r.w + tx] === 2; };
async function walk(dir, maxIter = 900, until = null) {
  const key = dir > 0 ? 'right' : 'left', start = G.room;
  for (let i = 0; i < maxIter; i++) {
    if (until ? until() : G.room !== start) return true;
    const p = G.P, tx = Math.floor((p.x + dir * 11) / 16), ty = Math.floor((p.y + 2) / 16);
    const wall = solid(Math.floor((p.x + dir * 8) / 16), Math.floor((p.y - 10) / 16));
    const gap = !solid(tx, ty) && !plat(tx, ty);
    if (p.ground && (gap || wall)) { G.step(1, [key, 'jump'], ['jump']); G.step(16, [key, 'jump']); }
    else G.step(3, [key]);
  }
  return false;
}
const st = () => { const p = G.P; return `${G.room} ${Math.round(p.x / 16)},${Math.round(p.y / 16)} ${p.state}`; };
// --- C6 -> portal -> NH1
G.tp('C6', 12, 21); G.step(10);
for (let i = 0; i < 6; i++) { G.P.face = 1; G.step(20, [], ['attack']); G.step(10); }
await walk(1, 200, () => G.room === 'NH1'); for (let i = 0; i < 80; i++) G.step(1);
log.push(['portal in', st()]);
// --- NH1 -> NH2 -> NH3
log.push(['NH1->NH2', await walk(1), st()]);
log.push(['NH2->NH3', await walk(1), st()]); await snap('t_nh3_arrive');
// --- NH3: ride the car. Walk to the west platform edge, wait for the car at the west dock, step on, ride
await walk(1, 200, () => G.P.x > 11 * 16);
let tr = G.NHR.trains[0];
for (let i = 0; i < 600 && !(tr.st === 'wait' && tr.dir > 0 && tr.x === tr.A); i++) G.step(2);
G.step(20, ['right']); log.push(['on car?', st(), G.P.ground, Math.round(tr.x)]);
for (let i = 0; i < 300 && tr.st === 'go' || i < 30; i++) { G.step(2); if (i === 60) await snap('t_nh3_ride'); }
for (let i = 0; i < 200 && !(tr.x === tr.B); i++) G.step(2);
log.push(['car at east', st(), Math.round(tr.x), tr.B]);
log.push(['NH3->NH4', await walk(1), st()]);
// --- NH4: hack STAIR (terminal at col 4, ground floor) then climb
G.tp('NH4', 5, 24); G.P.face = -1; G.step(5); G.step(20, [], ['attack']); G.step(30);
log.push(['plats on', G.NHR.plats.map(p => p.on).join(',')]);
async function jumpTo(tx, ty, dir) { // run-up toward dir, jump, steer to tx in the air
  const X = tx * 16 + 8;
  const k = () => Math.abs(X - G.P.x) < 3 ? [] : [X > G.P.x ? 'right' : 'left'];
  G.step(1, [...k(), 'jump'], ['jump']);
  for (let i = 0; i < 26; i++) G.step(1, [...k(), 'jump']);
  for (let i = 0; i < 60 && !G.P.ground; i++) G.step(1, k());
  G.step(4);
  return `${Math.floor(G.P.x / 16)},${Math.floor(G.P.y / 16) - 1} g=${G.P.ground} want ${tx},${ty}`;
}
for (let i = 0; i < 80 && G.P.x < 11 * 16 + 4; i++) G.step(1, ['right']); G.step(6);   // walk (a tp would rebuild the room)
log.push(['floor->catwalk', await jumpTo(10, 21, -1)]);
log.push(['catwalk->HL1', await jumpTo(14, 18, 1)]);
log.push(['HL1->HL2', await jumpTo(19, 15, 1)]);
log.push(['HL2->HL3', await jumpTo(24, 12, 1)]);
log.push(['HL3->exit balcony', await jumpTo(29, 12, 1)]);
  for (let i = 0; i < 20; i++) G.step(1, ['right']);
await snap('t_nh4_top');
// VAULT terminal on the balcony at col 30, then back west to the vault
for (let i = 0; i < 60 && Math.abs(G.P.x - 488) > 6; i++) G.step(1, [G.P.x < 488 ? 'right' : 'left']); G.step(4); G.step(20, [], ['interact']); G.step(20);
log.push(['door open', G.NHR.doors.map(d => d.open).join(',')]);
log.push(['balcony->HL3', await jumpTo(24, 12, -1)]); log.push(['HL3->HL2', await jumpTo(19, 15, -1)]); for (let i = 0; i < 30 && G.P.x > 18 * 16 + 6; i++) G.step(1, ['left']); log.push(['HL2->vault balcony', await jumpTo(14, 12, -1)]);
await walk(-1, 200, () => G.P.x < 7 * 16); log.push(['in vault', st()]); await snap('t_nh4_vault');
log.push(['vault->NH5 (back out)', await jumpTo(19, 15, 1), await jumpTo(24, 12, 1), await jumpTo(29, 12, 1), await walk(1), st()]);
// --- bosses marked dead for the walk-through
G.SAVE.flags['boss:enforcer'] = 1; G.SAVE.flags['boss:saint0'] = 1;
G.tp('NH5', 3, 12); G.step(10);
log.push(['NH5->NH6', await walk(1), st()]);
log.push(['NH6->NH7', await walk(1), st()]);
// --- and back
log.push(['NH7->NH6', await walk(-1), st()]);
log.push(['NH6->NH5', await walk(-1), st()]);
log.push(['NH5->NH4', await walk(-1), st()]);
// down through NH4 to the west door (drop off the balcony)
log.push(['NH4 down', await walk(-1, 900, () => G.room !== 'NH4'), st()]);
// NH3: wait at the east dock for the car
await walk(-1, 200, () => G.P.x < 53 * 16); tr = G.NHR.trains[0];
for (let i = 0; i < 900 && !(tr.st === 'wait' && tr.x === tr.B && tr.dir < 0 && tr.t > 1.6); i++) G.step(2);
for (let i = 0; i < 60 && G.P.x > tr.x + tr.w - 24; i++) G.step(1, ['left']); log.push(['on car W', st(), G.P.ground]);
for (let i = 0; i < 900 && !(tr.x === tr.A); i++) G.step(2);
log.push(['NH3->NH2', await walk(-1), st()]);
log.push(['NH2->NH1', await walk(-1), st()]);
log.push(['NH1->portal->C6', await walk(-1, 400, () => G.room === 'C6'), st()]);
for (let i = 0; i < 80; i++) G.step(1);
log.push(['C6 out of pocket', await walk(-1, 200, () => G.P.x < 12 * 16), st()]);
return log;
