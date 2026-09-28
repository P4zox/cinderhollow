// waypoint navigator: drives real inputs toward standing cells; never teleports. log = room changes.
G.SETTINGS.god = 1;
const NAV = { log: [], room: null, fails: [] };
const Pp = () => G.P;
const ft = () => ({ x: Pp().x / 16, y: Pp().y / 16 - 1 });   // standing cell (row the player stands in)
const tick = (h = [], t = []) => {
  const r0 = G.room; G.step(1, h, t); G.enemies.length = 0; G.P.hp = Math.max(G.P.hp, 50);
  if (G.state !== 'play') { for (let i = 0; i < 10 && G.state !== 'play'; i++) G.step(1, [], ['pause']); }
  if (G.room !== r0) NAV.log.push(r0 + '>' + G.room);
};
const at = (tx, ty, tol = 0.45) => Pp().ground && Math.abs(Pp().x - (tx * 16 + 8)) < tol * 16 && Math.abs(Pp().y - (ty + 1) * 16) < (Pp().duSlope ? 56 : 3);
// go to standing cell (tx, ty) in the current room. opts: drop (hold down+jump when above), max frames, exit (stop on room change)
function go(tx, ty, o = {}) {
  const room0 = G.room, max = o.max || 900; let jumpHold = 0, lastWall = 0;
  for (let i = 0; i < max; i++) {
    if (G.room !== room0) return true;
    if (!o.exit && at(tx, ty)) { for (let k = 0; k < 3; k++) tick(); return true; }
    const p = Pp(), c = ft(), dx = tx * 16 + 8 - p.x, dir = dx > 0 ? 'right' : 'left', adx = Math.abs(dx);
    const hold = adx > 3 ? [dir] : [];
    if (p.state === 'wall') { // wall-jump when climbing
      if (ty < c.y - 0.5) { tick([p.wallDir > 0 ? 'left' : 'right', 'jump'], ['jump']); jumpHold = 14; lastWall = 10; continue; }
    }
    if (p.ground) {
      if ((ty < c.y - 0.6 || (o.jump && adx > 20)) && (adx < (o.reach || 6.5) * 16)) { tick(hold.concat(['jump']), ['jump']); jumpHold = o.hj || 20; continue; }
      if (ty > c.y + 0.6 && adx < 10 && o.drop !== false && !p.duSlope) {
        const below = G.room && true;
        if (o.drop || adx < 10) { tick(['down', 'jump'].concat(adx > 8 ? hold : []), ['jump']); for (let k = 0; k < 6; k++) tick(['down'].concat(hold)); continue; }
      }
      tick(hold); continue;
    }
    // airborne: steer, keep holding jump while rising
    const h2 = adx > 2 ? [dir] : [];
    if (lastWall > 0) { lastWall--; }
    if (jumpHold > 0) { jumpHold--; tick(h2.concat(['jump'])); } else tick(o.glide ? h2.concat(['jump']) : h2);
  }
  NAV.fails.push(room0 + ' stuck going to ' + tx + ',' + ty + ' at ' + ft().x.toFixed(1) + ',' + ft().y.toFixed(1) + ' ' + Pp().state);
  return false;
}
function exitDir(dir, max = 400) { const r0 = G.room; for (let i = 0; i < max && G.room === r0; i++) tick([dir]); return G.room !== r0 || (NAV.fails.push(r0 + ' exit ' + dir + ' failed at ' + ft().x.toFixed(1) + ',' + ft().y.toFixed(1)), false); }
function dropThrough(max = 200) { const r0 = G.room; for (let i = 0; i < max && G.room === r0; i++) { if (Pp().ground) tick(['down', 'jump'], ['jump']); else tick(['down']); } return G.room !== r0 || (NAV.fails.push(r0 + ' drop failed at ' + ft().x.toFixed(1) + ',' + ft().y.toFixed(1)), false); }
function climbOut(from, max = 400) {
  const r0 = from || G.room;
  for (let att = 0; att < 4; att++) {
    for (let i = 0; i < max && G.room === r0; i++) { if (Pp().ground) tick(['jump'], ['jump']); else tick(Pp().vy < 0 ? ['jump'] : []); }
    for (let i = 0; i < 120 && G.room !== r0 && !Pp().ground; i++) tick(Pp().vy < 0 ? ['jump'] : []);
    if (G.room !== r0 && Pp().ground) return true;
  }
  NAV.fails.push(r0 + ' climb out failed at ' + ft().x.toFixed(1) + ',' + ft().y.toFixed(1)); return false;
}
function path(pts) { for (const p of pts) { if (typeof p === 'function') { if (p() === false) return false; continue; } if (!go(p[0], p[1], p[2] || {})) return false; } return true; }
function hop(tx, hold = 26) { const r0 = G.room; tick([tx * 16 + 8 > Pp().x ? 'right' : 'left', 'jump'], ['jump']); for (let i = 0; i < 100; i++) { const d = tx * 16 + 8 - Pp().x; tick((Math.abs(d) < 3 ? [] : d > 0 ? ['right'] : ['left']).concat(i < hold ? ['jump'] : [])); if (Pp().ground && i > 3) break; } return true; }
function slam(stay) { const r0 = G.room; tick(['jump'], ['jump']); for (let i = 0; i < 14; i++) tick(['jump']); tick(['down'], ['heavy']); for (let i = 0; i < 90 && G.room === r0; i++) tick(['down']); for (let i = 0; i < 120 && G.room === r0; i++) { if (Pp().ground) tick(['down', 'jump'], ['jump']); else tick(['down']); } return stay || G.room !== r0 || (NAV.fails.push(r0 + ' slam failed'), false); }
function lever(dir) { tick([dir]); tick([], ['attack']); for (let i = 0; i < 120; i++) tick(); return true; }
// wall-jump up a chimney to standing row ty (then step toward tx)
function chimney(tx, ty, first = 'left', max = 600) {
  const r0 = G.room; let side = first === 'left' ? -1 : 1, tap = 0, started = false;
  for (let i = 0; i < max && G.room === r0; i++) {
    const p = Pp(), L = side < 0 ? 'left' : 'right';
    if (p.ground && p.y / 16 - 1 <= ty + 0.2) return go(tx, ty);
    if (p.ground) { tick([L, 'jump'], ['jump']); tap = 4; continue; }
    if (p.state === 'wall' && tap <= 0) { side = -side; tap = 8; tick([side < 0 ? 'left' : 'right', 'jump'], ['jump']); continue; }
    tap--; tick(p.vy < 0 ? [L, 'jump'] : [L]);
  }
  NAV.fails.push(r0 + ' chimney failed at ' + ft().x.toFixed(1) + ',' + ft().y.toFixed(1)); return false;
}
