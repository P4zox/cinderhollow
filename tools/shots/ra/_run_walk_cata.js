window.__spots = "[[\"R5\",121,8],[\"R6\",20,10],[\"R7\",15,10],[\"R8\",30,6],[\"R9\",5,25],[\"R10\",3,7],[\"R11\",15,5],[\"R12\",10,16],[\"R13\",20,10],[\"R14\",8,6], [\"C7\",20,12],[\"C8\",40,28],[\"C9\",4,7],[\"C10\",10,10],[\"C11\",19,27],[\"C12\",20,13],[\"C13\",31,10],[\"C14\",8,9],[\"C15\",8,9],[\"W2\",2,12], [\"K5\",6,10],[\"K6\",15,24],[\"K7\",40,26],[\"K8\",20,10],[\"K9\",5,10],[\"K10\",15,14],[\"K11\",13,16],[\"K12\",4,38],[\"K13\",8,10]]";
await boot();
// shared walker for the wing walk tests: goto(room, tx, ty) steers the player to a standing cell by input only
const TL = 16, RA_ = window.__ra, RB = RA_.rooms;
const W = { log: [], last: G.room, frames: 0, fail: null };
const gp = () => { const r = RB[G.room]; return { x: r.gx * TL + G.P.x, y: r.gy * TL + G.P.y }; };
const tileG = (gx, gy) => { const r = RB[G.room]; return RA_.tile(Math.floor(gx / TL) - r.gx, Math.floor(gy / TL) - r.gy); };
const st1 = (hold, tap) => {
  G.step(1, hold, tap); W.frames++;
  if (G.room !== W.last) { W.log.push(`${W.last} -> ${G.room}`); W.last = G.room; }
  if (W.noFoes) RA_.kill();
  G.P.hp = Math.max(G.P.hp, 50);
  if (G.state !== 'play') G.step(1, [], ['pause']);
};
// opt: jx (px: jump when this close horizontally), wall (wall-jump climb), drop (↓+jump through a platform), dj (use the double jump), max frames
async function goto(room, tx, ty, opt = {}) {
  const r = RB[room], tgx = r.gx * TL + tx * TL + 8, tgy = r.gy * TL + (ty + 1) * TL;
  let jt = 99, dj = false, wj = 0; W.stuck = 0; W.wd = 0;
  for (let f = 0; f < (opt.max || 900); f++) {
    const p = gp(), dx = tgx - p.x, dy = tgy - p.y, P = G.P, dir = Math.sign(dx) || 1;
    if (opt.pass && G.room === room && Math.abs(dx) < 8) return true;
    if (G.room === room && Math.abs(dx) < 6 && Math.abs(dy) < 3 && P.ground) { for (let i = 0; i < 4; i++) st1([], []); return true; }
    const hold = [], tap = [];
    if (P.state === 'hook' && !opt.rope) { st1(['down'], ['roll']); continue; }
    const near = Math.abs(dx) < (opt.jx ?? 40);
    if (!P.ground && P.state !== 'wall' && !opt.noaim) {   // aim the landing: time to fall to the target's height, the speed that lands on it
      const vy = P.vy, tr = vy < 0 ? -vy / 640 : 0, hA = vy < 0 ? vy * vy / 1280 : 0, fall = dy + hA, v0 = Math.max(vy, 0);
      if (fall >= 0 && dy > -60) {
        const t = tr + (-v0 + Math.sqrt(v0 * v0 + 2 * 860 * fall)) / 860, want = Math.max(-122, Math.min(122, dx / Math.max(t, 0.05)));
        if (P.vx < want - 12) hold.push('right'); else if (P.vx > want + 12) hold.push('left');
      } else if (Math.abs(dx) > 4) hold.push(dx > 0 ? 'right' : 'left');
    } else if (Math.abs(dx) > 4) hold.push(dx > 0 ? 'right' : 'left');
    if (P.ground) {
      jt = 99; dj = false;
      const ahead = tileG(p.x + dir * 12, p.y + 4), gapAhead = !RA_.solid(ahead) && ahead !== RA_.T_PLAT;
      W.stuck = (f > 3 && Math.abs(P.vx) < 1 && Math.abs(dx) > 4) ? (W.stuck || 0) + 1 : 0;
      const onPlat = tileG(p.x, p.y + 4) === RA_.T_PLAT;
      if (W.stuck > 3 && dy > 12 && onPlat) { hold.length = 0; hold.push('down'); tap.push('jump'); W.stuck = 0; }
      else if ((dy < -12 && near) || W.stuck > 3) { tap.push('jump'); jt = 0; W.stuck = 0; }
      else if (dy > 12 && Math.abs(dx) < 12 && (opt.drop || tileG(p.x, p.y + 4) === RA_.T_PLAT)) { hold.length = 0; hold.push('down'); tap.push('jump'); }
      else if (gapAhead && dy <= (opt.gapdy ?? 40) && Math.abs(dx) > 20 && !opt.nojump) { tap.push('jump'); jt = 0; }
    } else {
      jt++;
      if (jt < 18) hold.push('jump');
      if (P.state === 'wall' && (opt.wall || dy < -12)) { tap.push('jump'); jt = 0; wj++; W.wd = P.wallDir; }
      if (opt.wall && W.wd && P.state !== 'wall' && dy < -8) { hold.length = 0; hold.push(W.wd > 0 ? 'left' : 'right'); if (jt < 18) hold.push('jump'); }
      if (opt.dj && !dj && P.vy > -40 && dy < -20) { tap.push('jump'); dj = true; jt = 0; }
    }
    if (W.trace) W.trace.push(`${f} ${(G.P.x/16).toFixed(2)},${(G.P.y/16).toFixed(2)} vx=${G.P.vx.toFixed(0)} vy=${G.P.vy.toFixed(0)} g=${G.P.ground} ${G.P.state} h=${hold} t=${tap}`);
    st1(hold, tap);
  }
  W.fail = W.fail || `stuck going to ${room}(${tx},${ty}); at ${G.room}(${(G.P.x / TL).toFixed(1)},${(G.P.y / TL - 1).toFixed(1)})`;
  return false;
}
async function route(steps) {
  for (const s of steps) { const ok = await goto(...s); if (!ok) return false; }
  return true;
}

G.SETTINGS.god = true; W.noFoes = true; G.grantTechniques();
const out = [];
const act = () => { st1([], ['interact']); for (let i = 0; i < 20; i++) st1([], []); };
const wait = n => { for (let i = 0; i < n; i++) st1([], []); };
const leg = async (name, steps) => { const f0 = W.frames; const ok = await route(steps); out.push(`${ok ? 'OK ' : 'BAD'} ${name} (${W.frames - f0} frames)${ok ? '' : ' :: ' + W.fail}`); W.fail = null; return ok; };
G.tp('C2', 30, 10); wait(20); W.last = G.room;
const D = { drop: true }, GP = { gapdy: 60 };
// ---- in: C2 -> the Ossuary Well (W2) -> C8 -> up to C7 -> gate -> C3
await leg('C2 -> down the well W2 -> C8 floor', [['C2', 37, 10], ['W2', 1, 12, D], ['W2', 3, 14, D], ['C8', 21, 22, D], ['C8', 19, 28, D]]);
const upC7 = [['C8', 36, 25], ['C8', 33, 22], ['C8', 44, 19], ['C8', 48, 16], ['C8', 48, 13], ['C8', 40, 10], ['C8', 33, 7], ['C8', 29, 4], ['C8', 31, 4], ['C8', 32, 1], ['C7', 5, 14]];
await leg('C8 shelves -> up into C7', upC7);
await leg('C7 -> the lever', [['C7', 20, 12], ['C7', 28, 12]]); act(); out.push('gate open: ' + (G.KIT.byId.gt && G.KIT.byId.gt.on) + ' in ' + G.room);
await leg('C7 -> climb into C3 (Hall of Roots)', [['C7', 36, 12], ['C7', 44, 9], ['C7', 39, 6], ['C7', 44, 3], ['C7', 45, 0], ['C3', 14, 11], ['C3', 20, 10]]);
// ---- back: C3 -> C7 -> C8 -> up the well -> C2
await leg('C3 -> drop into C7 -> west -> C8', [['C3', 14, 11], ['C7', 45, 9, D], ['C7', 36, 12, D], ['C7', 14, 12], ['C8', 32, 1], ['C8', 33, 7, D], ['C8', 40, 10, D], ['C8', 48, 13], ['C8', 50, 19], ['C8', 58, 28], ['C8', 40, 28]]);
await leg('C8 -> up the well -> C2', [['C8', 36, 25], ['C8', 33, 22], ['C8', 44, 19], ['C8', 48, 16], ['C8', 48, 13], ['C8', 26, 10], ['C8', 21, 7], ['C8', 21, 4], ['C8', 21, 1],
  ['W2', 3, 14], ['W2', 1, 12], ['W2', 3, 9], ['W2', 1, 6], ['W2', 3, 3], ['W2', 2, 0], ['C2', 37, 12], ['C2', 37, 10], ['C2', 30, 10]]);
// ---- branches
await leg('C2 -> W2 -> C13 Charnel Pit', [['C2', 37, 10], ['W2', 1, 12, D], ['C13', 31, 10], ['C13', 15, 11]]);
await leg('C13 -> W2 -> C8', [['C13', 31, 10], ['W2', 1, 12], ['W2', 3, 14, D], ['C8', 21, 1, D], ['C8', 21, 4, D]]);
G.P.face = -1; for (let i = 0; i < 8; i++) { st1([], ['attack']); wait(14); } out.push('gallery wall broken: ' + !window.__ra.solid(window.__ra.tile(19, 3)) + ' at ' + G.room + ' ' + (G.P.x/16).toFixed(1) + ',' + (G.P.y/16).toFixed(1));
await leg('C8 gallery (cracked wall) -> C11 top -> back', [['C8', 12, 5], ['C11', 16, 5], ['C8', 12, 5], ['C8', 21, 4]]);
await leg('C8 -> C11 lower door -> back', [['C8', 21, 22, D], ['C8', 19, 28, D], ['C8', 8, 28], ['C8', 2, 27], ['C11', 20, 27], ['C8', 2, 27], ['C8', 12, 28]]);
await leg('C8 -> drop shaft C9 -> C10', [['C8', 22, 28], ['C9', 13, 1], ['C9', 14, 4, D], ['C9', 6, 7, GP], ['C9', 18, 10, GP], ['C10', 5, 10]]);
await leg('C10 -> the false tomb', [['C10', 35, 10]]);
for (let i = 0; i < 8 && G.room === 'C10'; i++) { st1([], ['jump']); wait(6); st1(['down'], ['attack']); for (let k = 0; k < 40 && G.room === 'C10'; k++) st1([], []); }
out.push('after the tomb: ' + G.room);
await leg('C10 -> C14 stash -> back up', [['C14', 3, 6, D], ['C14', 12, 9], ['C14', 3, 6], ['C14', 6, 3], ['C14', 5, 0], ['C10', 33, 11], ['C10', 10, 10]]);
await leg('C10 -> C9 -> C12 crypt -> back', [['C9', 18, 10], ['C9', 5, 11, GP], ['C9', 15, 14, GP], ['C9', 5, 17, GP], ['C9', 15, 20, GP], ['C9', 5, 23, GP], ['C9', 15, 26, GP], ['C9', 4, 29, GP], ['C12', 36, 13], ['C9', 4, 29]]);
await leg('C9 -> down onto the Necropolis roof (NV1) -> back up C9 -> C8', [['C9', 15, 32, GP], ['C9', 5, 35, GP], ['C9', 12, 38, GP], ['C9', 7, 40, GP], ['NV1', 13, 1, D],
  ...[[7, 40], [13, 38], [5, 35], [15, 32], [5, 29], [15, 26], [5, 23], [15, 20], [5, 17], [15, 14], [5, 11], [16, 10], [6, 7], [13, 4], [13, 1]].map(([x, y]) => ['C9', x, y, { jx: 90 }]), ['C8', 24, 30]]);
await leg('C8 -> slam through the sealed floor', [['C8', 6, 28]]);
for (let i = 0; i < 4 && G.room === 'C8'; i++) { st1([], ['jump']); wait(18); st1(['down'], ['heavy']); wait(60); }
await leg('C15 -> out into C9', [['C15', 6, 9], ['C15', 5, 6], ['C15', 10, 3], ['C9', 6, 7]]);
out.push('rooms crossed: ' + W.log.join(', '));
return out;
