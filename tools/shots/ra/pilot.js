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
