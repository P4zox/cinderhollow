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
// SA: every side edge crossed both ways by walking (each test starts from one teleport into the first room).
const R = [];
const edge = (name, fn) => { const a = ROOMSEQ.length; try { fn(); } catch (e) { LOG.push(name + ' EXC ' + e.message); } R.push(`${name}: ${ROOMSEQ.slice(Math.max(0, a - 1)).join(' > ')}`); };
edge('TV10<>TV13', () => { G.tp('TV10', 4, 11); wait(20); run(-3, { room: 'TV13' }); run(33, { tol: 0.5 }); run(45, { room: 'TV10' }); wait(10); });
edge('TV9<>TV12', () => { G.tp('TV9', 9, 27); wait(20); run(5.5, { noJump: true, noGap: true, room: 'TV12' }); fall(); hop(8, 13); hop(3, 10); hop(8, 7); hop(5.5, 4); climb(27.5, 'right', { room: 'TV9' }); });
edge('TV12<>TV15', () => { G.tp('TV12', 58, 10); wait(20); run(70, { room: 'TV15' }); wait(10); run(2, { tol: 0.5 }); run(-5, { room: 'TV12' }); wait(10); });
edge('TV9<>TV14', () => { G.tp('TV9', 104, 27); wait(20); run(115, { room: 'TV14' }); wait(10); run(-5, { room: 'TV9' }); wait(10); });
edge('TV14<>TV15', () => { G.tp('TV14', 8, 13); wait(20); run(5.2, { noJump: true, noGap: true, room: 'TV15' }); fall(); here('nook'); climb(13.5, 'left', { room: 'TV14' }); wait(10); });
edge('TV9<>TV16', () => { G.tp('TV9', 104, 11); wait(20); run(108.5, { tol: 0.4 }); step(['right'], ['roll']); run(115, { room: 'TV16' }); wait(10); run(3, { tol: 0.5 }); step(['left'], ['roll']); run(-5, { room: 'TV9' }); wait(10); });
edge('K2<>W4<>DB1', () => { G.tp('K2', 37, 10); wait(20); run(39.5, { tol: 0.3 }); drop(); for (let i = 0; i < 40 && S().y < 88.5; i++) { fall(); if (S().y < 88.5) drop(); } run(5.6, { noJump: true, noGap: true, room: 'DB1' }); fall(); here('DB1');
  hop(4.5, 6); climb(88, 'right', { room: 'W4' }); here('W4 foot');
  for (let y = 84; y >= 3; y -= 3) { let xs = []; for (let x = 1; x <= 6; x++) if (tileAt(x, y) === 2) xs.push(x); const cx = xs.length ? (xs[0] + xs[xs.length - 1]) / 2 + 0.5 : 3.5; hop(cx, y, { tries: 3 }); }
  here('W4 top'); jump(null, { to: 4, hold: 22 }); here('grate?'); climb(11.2, 'left', { room: 'K2', maxF: 300 }); wait(10); });
edge('W4<>DB14', () => { G.tp('W4', 5, 5); wait(20); run(12, { room: 'DB14' }); wait(10); run(-4, { room: 'W4' }); wait(10); });
edge('W4<>DB16', () => { G.tp('W4', 2, 20); wait(20); run(-4, { room: 'DB16' }); wait(10); run(70, { room: 'W4' }); wait(10); });
edge('W4<>DB10', () => { G.tp('W4', 2, 50); wait(20); run(-4, { room: 'DB10' }); wait(10); run(90, { room: 'W4' }); wait(10); });
edge('W4<>DB13', () => { G.tp('W4', 5, 62); wait(20); run(12, { room: 'DB13' }); wait(10); run(-4, { room: 'W4' }); wait(10); });
edge('DB14>DB15>W4', () => { G.tp('DB14', 25, 21); wait(20); G.sa.kitForce('gX', true); wait(5); run(40, { noJump: true, room: 'DB15' }); fall(); drop(); drop(); wait(60);
  swim(13, 12); for (let i = 0; i < 40; i++) { step(['left', 'jump'], i === 0 ? ['jump'] : []); if (i > 3 && S().gr) break; } run(4.6, { tol: 0.3 }); use(); wait(60); run(-4, { room: 'W4' }); wait(10); run(12, { room: 'DB15' }); wait(10); });
edge('DB15>DB14 (drain up)', () => { G.tp('DB15', 25, 12); wait(30); swim(29, 11.8); leap(31.2); hop(33.5, 6); hop(33.5, 3); climb(21.5, 'left', { room: 'DB14' }); wait(10); });
edge('DB13<>DB17', () => { G.tp('DB13', 17, 21); wait(20); for (let i = 0; i < 6 && G.room === 'DB13'; i++) { step(['down'], ['attack']); wait(25); } for (let i = 0; i < 200 && G.room === 'DB13'; i++) step(['down']);
  swim(5, 3, { maxF: 400 }); for (let i = 0; i < 200 && G.room === 'DB17'; i++) step(['up', 'jump'], i % 30 === 0 ? ['jump'] : []); wait(10); });
edge('CM10<>CM15', () => { G.tp('CM10', 20, 11); wait(20); run(30, { room: 'CM15' }); wait(10); run(-4, { room: 'CM10' }); wait(10); });
edge('CM10<>CM12', () => { G.tp('CM10', 5, 2); wait(20); jump(null, { to: 5.5, hold: 22 }); hop(11.5, 16, { tries: 2 }); here('turret'); hop(8, 14); here('roof');
  run(10.5, { noJump: true, noGap: true, tol: 0.3 }); drop(); for (let i = 0; i < 8 && G.room === 'CM12'; i++) { fall(); drop(); } fall(); });
edge('CM11<>CM13', () => { G.tp('CM11', 40, 11); wait(20); run(60, { room: 'CM13' }); wait(10); run(-4, { room: 'CM11' }); wait(10); });
edge('CM13<>CM14', () => { G.SAVE.items.xsa_key1 = G.SAVE.items.xsa_key2 = G.SAVE.items.xsa_key3 = 1; G.tp('CM14', 3, 15); wait(20); use(); wait(60); G.tp('CM13', 34, 15); wait(20); run(50, { room: 'CM14' }); wait(10); run(-4, { room: 'CM13' }); wait(10); });
edge('CM9<>CM17', () => { G.tp('CM9', 79, 7); wait(20); G.P.face = 1; for (let i = 0; i < 4; i++) { step(['right'], ['attack']); wait(20); } run(95, { room: 'CM17' }); wait(10); run(-4, { room: 'CM9' }); wait(10); });
edge('CM9<>CM16', () => { G.tp('CM9', 78, 26); wait(20); run(95, { room: 'CM16' }); wait(10); run(-4, { room: 'CM9' }); wait(10); });
LOG.push(...R.map(r => 'EDGE ' + r));
return LOG.concat(["ROOMS " + ROOMSEQ.join(" ")]);
