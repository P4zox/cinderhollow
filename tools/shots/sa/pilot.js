// SA: a tiny input pilot for walking wings without teleporting. Prepended to the walk scripts.
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.talon = 1;
G.SAVE.seenAreas = G.SAVE.seenAreas || {}; for (const k of ['thornveil', 'barrows', 'crimson', 'cathedral', 'catacombs', 'ramparts']) G.SAVE.seenAreas[k] = 1;
const T = 16, LOG = [], ROOMSEQ = [];
let lastRoom = null, frames = 0;
const S = () => ({ x: G.P.x / T, y: G.P.y / T, st: G.P.state, gr: G.P.ground, vx: G.P.vx, vy: G.P.vy });
function step(hold = [], tap = []) {
  G.step(1, hold, tap); frames++;
  if (G.state !== 'play') G.step(1, [], ['pause']);
  for (const e of G.enemies) if (e.alive && !e.x3g) e.die && e.die({ dir: 1 });
  G.P.hp = Math.max(G.P.hp, 999);
  if (G.room !== lastRoom) { ROOMSEQ.push(G.room); LOG.push(`  -> ${G.room} @${S().x.toFixed(1)},${S().y.toFixed(1)} f${frames}`); lastRoom = G.room; }
}
const wait = n => { for (let i = 0; i < n; i++) step(); };
const tileAt = (tx, ty) => G.sa.tileAt(tx, ty);
const solidT = t => t === 1 || t === 5 || t === 7;
function run(tx, o = {}) {   // run to x (tiles); jump walls and gaps on the way
  const maxF = o.maxF || 900; let stuck = 0, room0 = G.room;
  for (let f = 0; f < maxF; f++) {
    const s = S(), d = tx - s.x; if (Math.abs(d) < (o.tol || 0.3) && s.gr) return true;
    if (o.room && G.room === o.room) return true;
    const dir = d > 0 ? 'right' : 'left', sgn = d > 0 ? 1 : -1, hold = [dir], tap = [];
    if (s.gr) {
      const fx = Math.floor(s.x + sgn * 0.8), fy = Math.floor(s.y + 0.05);
      const wall = solidT(tileAt(fx, fy - 1)) || solidT(tileAt(fx, fy - 2));
      const gap = !o.noGap && ((!solidT(tileAt(fx, fy)) && tileAt(fx, fy) !== 2) || tileAt(fx, fy - 1) === 35 || tileAt(fx + sgn, fy - 1) === 35 || tileAt(fx, fy) === 3) && Math.abs(d) > 1.2;
      if (Math.abs(s.vx) < 5) stuck++; else stuck = 0;
      if (!o.noJump && (wall || gap || stuck > 6)) { tap.push('jump'); stuck = 0; }
    }
    if (!s.gr && s.vy < 0) hold.push('jump');
    step(hold, tap);
  }
  return false;
}
function jump(dir, o = {}) {   // a full jump (hold frames), steering toward o.to (tiles) if given; returns on landing
  let f = 0; step(dir ? [dir] : [], ['jump']);
  for (; f < (o.maxF || 150); f++) {
    const s = S(), hold = [];
    if (f < (o.hold ?? 20)) hold.push('jump');
    if (o.to !== undefined) { const d = o.to - s.x; if (Math.abs(d) > 0.2) hold.push(d > 0 ? 'right' : 'left'); }
    else if (dir && f < (o.dirF ?? 999)) hold.push(dir);
    if (o.dash && f === o.dash) { step(hold, ['roll']); continue; }
    step(hold);
    if (f > 3 && S().gr) return true;
    if (o.room && G.room === o.room) return true;
  }
  return false;
}
function climb(untilY, dir = 'right', o = {}) {   // wall-jump up a chimney until standing above untilY
  let d = dir, f = 0; step([d], ['jump']);
  for (; f < (o.maxF || 600); f++) {
    const s = S();
    if (s.gr && s.y < untilY && (!o.room || G.room === o.room)) return true;
    if (s.st === 'wall') { step([d], ['jump']); d = d === 'right' ? 'left' : 'right'; continue; }
    if (s.gr) { step([d], ['jump']); continue; }
    step([d, ...(s.vy < 0 ? ['jump'] : [])]);
  }
  return false;
}
function drop(o = {}) { step(['down'], ['jump']); for (let f = 0; f < (o.maxF || 200); f++) { step(o.dir ? [o.dir] : []); if (f > 5 && S().gr) return true; } return false; }
function fall(dir, o = {}) { for (let f = 0; f < (o.maxF || 200); f++) { const s = S(); step(dir && (o.to === undefined || Math.abs(o.to - s.x) > 0.2) ? [o.to !== undefined ? (o.to > s.x ? 'right' : 'left') : dir] : []); if (f > 3 && S().gr) return true; } return false; }
function swim(tx, ty, o = {}) {
  for (let f = 0; f < (o.maxF || 600); f++) {
    const s = S(), dx = tx - s.x, dy = ty - s.y, hold = [];
    if (Math.abs(dx) < 0.4 && Math.abs(dy) < 0.5) return true;
    if (dx > 0.2) hold.push('right'); else if (dx < -0.2) hold.push('left');
    if (dy > 0.3) hold.push('down'); else if (dy < -0.3) hold.push(G.sa.DBS && G.sa.DBS.inWater ? 'up' : 'jump');
    step(hold, dy < -0.3 && G.sa.DBS && G.sa.DBS.inWater && s.st === 'swim' && G.sa.DBS.inWater && f % 20 === 0 ? [] : []);
    if (o.room && G.room === o.room) return true;
  }
  return false;
}
const use = () => { step([], ['interact']); wait(20); };
const here = tag => LOG.push(`${tag}: ${G.room} ${S().x.toFixed(1)},${S().y.toFixed(1)} ${S().st}`);
function platExt() {   // [left, right] (tiles) of what you stand on
  const s = S(), ty = Math.floor(s.y + 0.1), sup = x => { const t = tileAt(x, ty); return (solidT(t) || t === 2) && !solidT(tileAt(x, ty - 1)); };
  let l = Math.floor(s.x), r = l; while (sup(l - 1) && l > 0) l--; while (sup(r + 1) && r < 400) r++;
  return [l, r + 1];
}
function standOn() { const s = S(); return tileAt(Math.floor(s.x), Math.floor(s.y + 0.1)); }
function hop(tx, ty, o = {}) {   // get onto the platform whose top is row ty around column tx
  for (let tries = 0; tries < (o.tries || 4); tries++) {
    const s = S();
    if (s.gr && Math.abs(s.y - ty) < 0.2 && Math.abs(s.x - tx) < (o.tol || 1.2)) return true;
    if (ty < s.y - 0.4) {   // up: get under/near the target, then jump and steer onto it
      const sgn = tx > s.x ? 1 : -1, [pl, pr] = platExt();
      let near = o.from !== undefined ? o.from : tx - sgn * Math.min(2.2, Math.abs(tx - s.x));
      near = Math.max(pl + 0.35, Math.min(pr - 0.35, near));
      if (Math.abs(near - s.x) > 0.4) run(near, { noGap: true, noJump: true, tol: 0.35, maxF: 400 });
      const dyu = s.y - ty, dxu = Math.abs(tx - S().x); jump(null, { to: tx, hold: o.hold ?? (dyu >= 2.6 || dxu > 3 ? 22 : dyu >= 1.6 || dxu > 2 ? 12 : 7), maxF: 150 });
    } else if (ty > s.y + 0.4) {   // down: drop through a one-way or walk off the edge, steering onto the target
      if (standOn() === 2 && Math.abs(tx - s.x) < 2) drop({ dir: null });
      else { const d = tx > s.x ? 'right' : 'left'; for (let f = 0; f < 300; f++) { const q = S(); if (f > 3 && q.gr && (Math.abs(q.y - s.y) > 0.3 || Math.abs(q.x - tx) < 0.5)) break; const dd = tx - q.x; step(Math.abs(dd) > 0.25 ? [dd > 0 ? 'right' : 'left'] : []); } }
    } else run(tx, { tol: 0.4, maxF: 500 });
  }
  const s = S(); return s.gr && Math.abs(s.y - ty) < 0.2;
}
function slash(dir, n = 4) { for (let i = 0; i < n; i++) { step([dir], ['attack']); wait(18); } }
function leap(tx, o = {}) {   // out of the water onto a ledge at column tx
  for (let t = 0; t < (o.tries || 4); t++) {
    step([], ['jump']);
    for (let i = 0; i < 90; i++) { const s = S(), d = tx - s.x; step([...(Math.abs(d) > 0.2 ? [d > 0 ? 'right' : 'left'] : []), 'jump']); if (i > 4 && S().gr) return true; if (i > 4 && G.sa.DBS && G.sa.DBS.inWater && S().vy > 0) break; }
    swim(tx + (o.back || -1.5), S().y, { maxF: 90 });
  }
  return S().gr;
}
