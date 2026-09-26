// shared helpers (prepended to test scripts)
const S = (n, h = [], t = []) => { const r = G.step(n, h, t); if (window.__godS && G.P && G.D) G.P.hp = G.D.maxHp; return r; };
const pos = () => { const p = G.P; return { st: G.state, room: G.room, tx: Math.floor(p.x / 16), ty: Math.floor((p.y - 1) / 16), x: Math.round(p.x), y: Math.round(p.y), g: p.ground, s: p.state }; };
// steer a jump toward a standing cell (tx, ty = row the player stands in), using up to maxJ jumps
function jumpTo(tx, ty, maxJ = 2, steerBelow = 40) {
  const X = tx * 16 + 8, Y = (ty + 1) * 16;
  S(1, [], ['jump']); let j = 1;
  for (let i = 0; i < 160; i++) {
    const p = G.P, dx = X - p.x, dir = Math.abs(dx) > 3 ? (dx > 0 ? 'right' : 'left') : null;
    const steer = dir && (p.y < Y - 2 || p.y - Y < steerBelow);
    if (p.vy > -40 && p.y > Y - 6 && j < maxJ && !p.ground) { S(1, steer ? [dir] : [], ['jump']); j++; continue; }
    S(1, steer ? ['jump', dir] : ['jump']);
    if (G.P.ground && i > 3) break;
  }
  for (let i = 0; i < 60 && !G.P.ground; i++) S(1);
  S(2); return { ...pos(), j };
}
function walkTo(tx, maxF = 400) {
  const X = tx * 16 + 8;
  for (let i = 0; i < maxF; i++) { const dx = X - G.P.x; if (Math.abs(dx) < 3) break; S(1, [dx > 0 ? 'right' : 'left']); }
  S(2); return pos();
}
function walk(dir, n) { S(n, [dir]); S(2); return pos(); }
// run in a direction, hopping over steps and gaps; stops at room change or after maxF frames
function run(dir, maxF = 900, stopRoom = null) {
  const r0 = G.room;
  for (let i = 0; i < maxF; i++) {
    const p = G.P, d = dir === 'right' ? 1 : -1;
    const wall = G.P.ground && (solidAhead(p.x + d * 9, p.y - 6) || solidAhead(p.x + d * 9, p.y - 20));
    const gap = G.P.ground && !solidAhead(p.x + d * 12, p.y + 4) && !solidAhead(p.x + d * 30, p.y + 20);
    if (wall || gap) { S(1, [dir], ['jump']); for (let k = 0; k < 16; k++) S(1, [dir, 'jump']); S(1, [dir], ['jump']); for (let k = 0; k < 14; k++) S(1, [dir, 'jump']); continue; }
    S(1, [dir]);
    if (G.room !== r0 && (!stopRoom || G.room === stopRoom)) { S(10, [dir]); break; }
  }
  return pos();
}
function solidAhead(x, y) { return window.__sfSolid ? window.__sfSolid(x, y) : false; }
function clearFoes() { G.enemies.forEach(e => { e.hp = 0; e.state = 'dead'; e.gone = true; }); }
// multi-jump straight up holding `dir`, then steer `late` once above targetY (px feet)
function tower(dir, jumps, late, targetY) {
  let j = 1; S(1, dir ? [dir] : [], ['jump']);
  for (let i = 0; i < 160; i++) {
    const p = G.P, h = (p.y < targetY - 4 && late) ? [late] : dir ? [dir] : [];
    if (p.vy > -40 && j < jumps && !p.ground) { S(1, h, ['jump']); j++; continue; }
    S(1, [...h, 'jump']);
    if (G.P.ground && i > 4) break;
  }
  for (let i = 0; i < 60 && !G.P.ground; i++) S(1, late ? [late] : []);
  S(2); return pos();
}
const flush = () => new Promise(r => setTimeout(r, 260));
