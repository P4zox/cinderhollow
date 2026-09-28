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

G.SETTINGS.god = true; W.noFoes = true; G.SAVE.items.talon = 1; G.SAVE.items.wings = 1;
const out = [], D = { drop: true };
const act = () => { st1([], ['interact']); for (let i = 0; i < 20; i++) st1([], []); };
const wait = n => { for (let i = 0; i < n; i++) st1([], []); };
const leg = async (name, steps) => { const f0 = W.frames; const ok = await route(steps); out.push(`${ok ? 'OK ' : 'BAD'} ${name} (${W.frames - f0} frames)${ok ? '' : ' :: ' + W.fail}`); W.fail = null; return ok; };
G.tp('K1', 20, 10); wait(20); W.last = G.room;
// ---- in: K1 -> up through its vault -> K5 -> K7 -> east -> K8 -> lever -> down into K2
await leg('K1 vault stair -> K5', [['K1', 14, 8], ['K1', 22, 6], ['K1', 30, 3], ['K1', 31, 0], ['K5', 15, 12], ['K5', 20, 10]]);
await leg('K5 -> up into K7', [['K5', 29, 7], ['K5', 29, 4], ['K5', 29, 1], ['K7', 43, 28], ['K7', 50, 26]]);
await leg('K7 floor east -> down into K8', [['K7', 80, 26], ['K7', 89, 28, { pass: true }], ['K8', 34, 1, D], ['K8', 30, 10, D]]);
await leg('K8 booths -> lever', [['K8', 7, 10]]); act(); out.push('K8 gate open: ' + G.KIT.byId.gk.on);
await leg('K8 -> drop into K2', [['K8', 2, 12], ['K2', 10, 1, D], ['K2', 20, 10, D]]);
// ---- back: K2 -> K8 -> K7 -> K5 -> K1
await leg('K2 vault stair -> K8', [['K2', 9, 7], ['K2', 11, 4], ['K2', 10, 1], ['K8', 2, 12], ['K8', 10, 10]]);
await leg('K8 -> up into K7', [['K8', 37, 7], ['K8', 33, 4], ['K8', 34, 1], ['K7', 87, 28], ['K7', 80, 26]]);
await leg('K7 -> west -> drop into K5', [['K7', 50, 26], ['K7', 45, 28, { pass: true }], ['K5', 29, 1, D], ['K5', 20, 10, D]]);
await leg('K5 -> drop into K1', [['K5', 15, 12], ['K1', 31, 0, D], ['K1', 26, 10, D]]);
// ---- branches
await leg('K1 -> K5 -> the altar wall', [['K1', 14, 8], ['K1', 22, 6], ['K1', 30, 3], ['K1', 31, 0], ['K5', 15, 12], ['K5', 4, 10]]);
G.P.face = -1; for (let i = 0; i < 8; i++) { st1([], ['attack']); wait(14); }
await leg('K5 -> K13 sacristy -> back', [['K13', 8, 10], ['K5', 6, 10]]);
await leg('K5 -> K7 -> chimney -> clerestory walk', [['K5', 29, 7], ['K5', 29, 4], ['K5', 29, 1], ['K7', 43, 28], ['K7', 20, 26], ['K7', 2, 26], ['K7', 5, 7, { wall: true, jx: 60, max: 1400 }]]);
await leg('K7 walk east -> K11 rose window -> back', [['K7', 22, 7], ['K7', 31, 7], ['K7', 60, 7], ['K7', 70, 7], ['K7', 75, 4], ['K7', 75, 1], ['K11', 18, 18], ['K11', 11, 16], ['K11', 18, 18], ['K7', 75, 1, D], ['K7', 80, 7, D]]);
await leg('K7 walk west -> K9 stair -> back down to K7 -> up again', [['K7', 70, 7], ['K7', 60, 7], ['K7', 31, 7], ['K7', 22, 7], ['K7', 5, 7], ['K7', 3, 4], ['K7', 3, 1], ['K9', 3, 18], ['K7', 3, 1, D], ['K9', 3, 18], ['K9', 3, 15], ['K9', 3, 12], ['K9', 5, 10]]);
await leg('K9 chandeliers -> east platform', [['K9', 10, 10], ['K9', 16, 9], ['K9', 22, 11], ['K9', 28, 9], ['K9', 34, 8], ['K9', 40, 9], ['K9', 46, 7]]);
await leg('K9 -> K10 organ loft -> back', [['K9', 49, 4], ['K9', 49, 1], ['K10', 26, 16], ['K10', 20, 14], ['K10', 26, 16], ['K9', 49, 1, D], ['K9', 50, 7, D]]);
// ---- the K3s branch: the Reliquary of Wings -> K6 -> K12
G.tp('K3s', 10, 8); wait(20); W.last = G.room;
await leg('K3s ceiling -> K6', [['K3s', 3, 5], ['K3s', 3, 2], ['K6', 3, 26], ['K6', 8, 24], ['K6', 16, 24], ['K6', 6, 21]]);
await leg('K6 stair up -> K12 floor', [['K6', 8, 20], ['K6', 12, 18], ['K6', 16, 16], ['K6', 20, 15], ['K6', 18, 12], ['K6', 14, 10], ['K6', 10, 8], ['K6', 5, 7], ['K6', 9, 4], ['K6', 9, 1], ['K12', 8, 40], ['K12', 14, 38]]);
await leg('K12 -> down K6 -> K3s', [['K12', 8, 40, D], ['K6', 9, 1, D], ['K6', 9, 4, D], ['K6', 3, 7, D], ['K6', 10, 8], ['K6', 14, 10], ['K6', 18, 12], ['K6', 20, 15], ['K6', 12, 24], ['K6', 3, 26], ['K3s', 3, 2, D], ['K3s', 10, 8, D]]);
out.push('rooms crossed: ' + W.log.join(', '));
return out;
