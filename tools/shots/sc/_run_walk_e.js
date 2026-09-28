// SC trial autopilot helpers (prepended to a trial script). G = window.__game.
const T16 = 16, S = () => window.__sys.SYS;
let MIRROR = 0;   // a room built mirrored: MIRROR = its pixel width; the pilot then works in the unmirrored frame
const PXp = () => MIRROR ? MIRROR - G.P.x : G.P.x, VXp = () => MIRROR ? -G.P.vx : G.P.vx, WDp = () => MIRROR ? -G.P.wallDir : G.P.wallDir;
const px = () => PXp() / T16, py = () => G.P.y / T16;          // py: feet in tiles (standing row + 1)
const att = () => (S().trial ? S().trial.attempts : -1);
const LOG = [];
const log = m => LOG.push(`[${(S().trial ? S().trial.t : 0).toFixed(2)}] ${m} @${px().toFixed(2)},${py().toFixed(2)} ${G.P.state}`);
function stepN(n, hold = [], tap = []) { G.step(n, hold, tap); }
// walk to tile-centre x on the ground
function walkTo(x, tol = 0.15, max = 400) {
  for (let i = 0; i < max; i++) { const d = x - px(); if (Math.abs(d) < tol && Math.abs(VXp()) < 30) return true; G.step(1, Math.abs(d) < tol ? [] : d > 0 ? ['right'] : ['left']); if (Math.abs(d) < 0.6 && Math.abs(d) >= tol) G.step(1); }
  return false;
}
// a jump arc toward a target standing cell (tx, ty = the row you stand in). jumps: max extra jumps to spend; dash: allow an air dash
function leap(tx, ty, o = {}) {
  const a0 = att(), feet = (ty + 1) * T16, jumps = o.jumps ?? 2, dir0 = Math.sign(tx + 0.5 - px());
  let used = 0, dashed = false, t = 0, lastJ = 0;
  G.step(1, [...(o.run !== false && dir0 ? [dir0 > 0 ? 'right' : 'left'] : []), 'jump'], ['jump']);
  if (att() !== a0) { log('RESET at takeoff to ' + tx + ',' + ty + ' why=' + S().trial.why); return false; }
  for (t = 0; t < (o.max || 240); t++) {
    if (att() !== a0) { log('RESET during leap to ' + tx + ',' + ty + ' why=' + S().trial.why); return false; }
    const d = (tx + 0.5) * T16 - PXp(), hold = ((G.P.vy < 0 && (o.holdT === undefined || t < o.holdT)) || o.glide) ? ['jump'] : [], tap = [];
    if (o.steer !== false) { if (Math.abs(d) > (o.tol || 3)) hold.push(d > 0 ? 'right' : 'left'); }
    if (o.delaySteer && t < o.delaySteer) { const j = hold.includes('jump'); hold.length = 0; if (j) hold.push('jump'); hold.push(dir0 > 0 ? 'right' : 'left'); }
    const below = G.P.y > feet - (o.margin ?? 6);
    if (G.P.vy > (o.jv ?? -20) && below && used < jumps && t - lastJ > 8 && !G.P.ground && (Math.abs(d) > (o.over ?? 9) || G.P.y > feet + 2)) { tap.push('jump'); used++; lastJ = t; }
    if (o.dash && !dashed && !G.P.ground && Math.abs(d) > (o.dashAt || 48) && G.P.vy > -40 && t > (o.dashT || 6)) { tap.push('roll'); dashed = true; }
    if (o.slam && !G.P.ground && Math.abs(d) < 6 && G.P.y < feet - 4) { hold.push('down'); tap.push('heavy'); }
    G.step(1, hold, tap);
    if (att() !== a0) { log('RESET during leap to ' + tx + ',' + ty + ' why=' + S().trial.why + ' t=' + t); return false; }
    if (G.P.ground && t > 3) break;
  }
  G.step(2);
  const ok = Math.abs(py() - (ty + 1)) < 0.2 && Math.abs(px() - (tx + 0.5)) < 1.6;
  log(`${ok ? 'landed' : 'MISSED'} ${tx},${ty} jumps=${used} dash=${dashed}`);
  return ok;
}
const K = id => G.xs.KIT.byId[id];
// wait (standing) until kit phase `id` has been solid for `after` s (it just landed) — or until it will be solid in `lead` s
function waitSolid(id, lead = 0, max = 600, span = 0.5) {
  const o = K(id); if (!o) { log('no kit ' + id); return false; }
  for (let i = 0; i < max; i++) { let ok = true; for (let k = 0; k <= 5; k++) if (!o.phaseAt(G.xs.KIT.t + lead + span * k / 5)) ok = false; if (ok) return true; G.step(1); }
  return false;
}
let TRACE = null;
const _gstep = G.step.bind(G);
const _swap = a => a.map(k => MIRROR ? (k === 'left' ? 'right' : k === 'right' ? 'left' : k) : k);
G.step = (n = 60, h = [], t = []) => { const r = _gstep(n, _swap(h), _swap(t)); if (TRACE && (TRACE.n++ % (TRACE.every || 4) === 0)) TRACE.out.push(`${px().toFixed(1)},${py().toFixed(1)} vy=${G.P.vy | 0} ${G.P.state} ${h.join('+')}${t.length ? ' !' + t.join('+') : ''}`); return r; };
// climb a chimney between walls at tile columns wl (left wall) and wr (right wall) until feet are above row topY
function chimney(wl, wr, topY, max = 600, done = null) {
  const a0 = att(); let dir = -1;
  for (let i = 0; i < max; i++) {
    if (att() !== a0) { log('RESET in chimney why=' + S().trial.why); return false; }
    if (done ? done() : G.P.y < topY * T16) { log('chimney top'); return true; }
    if (G.P.state === 'wall') { dir = -WDp(); G.step(1, ['jump'], ['jump']); continue; }
    if (G.P.ground) { G.step(1, [dir > 0 ? 'right' : 'left', 'jump'], ['jump']); continue; }
    const hold = [dir > 0 ? 'right' : 'left']; if (G.P.vy < 0) hold.push('jump');
    G.step(1, hold);
  }
  log('chimney timeout'); return false;
}
// a low hop (jump tapped, not held) with an air dash at the top, holding a direction; returns when grounded
function hopDash(dir, dashAfter = 6, max = 120) {
  const a0 = att(), k = dir > 0 ? 'right' : 'left';
  G.step(1, [k, 'jump'], ['jump']);
  for (let i = 0; i < max; i++) {
    G.step(1, [k], i === dashAfter ? ['roll'] : []);
    if (att() !== a0) { log('RESET in hopDash why=' + S().trial.why); return false; }
    if (G.P.ground && i > 3) break;
  }
  G.step(2); log('hopDash done'); return true;
}
// wait for the right takeoff moment: target kit phase solid over [t+flight-pre, t+flight+post], current (if given) solid at t
function waitTakeoff(target, flight, cur = null, pre = 0.08, post = 0.3) {
  const o = K(target), c = cur ? K(cur) : null, T0 = G.xs.KIT.t;
  for (let k = 0; k < 300; k++) {
    const t = T0 + k / 60; let ok = !c || (c.phaseAt(t) && c.phaseAt(t + 1 / 60));
    for (let j = 0; j <= 6 && ok; j++) if (!o.phaseAt(t + flight - pre + (pre + post) * j / 6)) ok = false;
    if (ok) { G.step(k); return true; }
  }
  log('no takeoff window for ' + target); return false;
}
// already airborne: steer to a standing cell like leap() does (air jumps / dash / glide as allowed)
function airTo(tx, ty, o = {}) {
  const a0 = att(), feet = (ty + 1) * T16, jumps = o.jumps ?? 2; let used = 0, dashed = false, lastJ = -20;
  for (let t = 0; t < (o.max || 300); t++) {
    const d = (tx + 0.5) * T16 - PXp(), hold = [], tap = [];
    if ((G.P.vy < 0 && (o.holdT === undefined || t < o.holdT)) || (o.glide && G.P.vy > 0)) hold.push('jump');
    if (Math.abs(d) > (o.tol || 3)) hold.push(d > 0 ? 'right' : 'left');
    const below = G.P.y > feet - (o.margin ?? 6);
    if (G.P.vy > (o.jv ?? -20) && below && used < jumps && t - lastJ > 8 && !G.P.ground && (Math.abs(d) > (o.over ?? 9) || G.P.y > feet + 2)) { tap.push('jump'); used++; lastJ = t; }
    if (o.dash && !dashed && Math.abs(d) > (o.dashAt || 48) && t > (o.dashT || 0)) { tap.push('roll'); dashed = true; }
    G.step(1, hold, tap);
    if (att() !== a0) { log('RESET in airTo ' + tx + ',' + ty + ' why=' + S().trial.why + ' t=' + t); return false; }
    if (G.P.ground && t > 2) break;
  }
  G.step(2);
  const ok = Math.abs(py() - (ty + 1)) < 0.2 && Math.abs(px() - (tx + 0.5)) < 1.6;
  log(`${ok ? 'airTo ok' : 'airTo MISSED'} ${tx},${ty} jumps=${used} dash=${dashed}`); return ok;
}
// Root Hook: jump toward dir, hook the nearest point, pump, let go past relX moving that way
function hookSwing(dir, relX, o = {}) {
  const a0 = att(), k = dir > 0 ? 'right' : 'left';
  if (G.P.ground) { G.step(1, [k, 'jump'], ['jump']); for (let i = 0; i < (o.pre ?? 8); i++) G.step(1, [k, 'jump']); }
  G.step(1, [k], ['hook']);
  if (G.P.state !== 'hook') { log('hook: no attach'); return false; }
  for (let i = 0; i < 300; i++) {
    const past = dir > 0 ? px() > relX : px() < relX;
    if (past && VXp() * dir > (o.minV ?? 90)) { G.step(1, [k], ['jump']); log('hook release'); return true; }
    G.step(1, [k]);
    if (att() !== a0) { log('RESET in hook why=' + S().trial.why); return false; }
  }
  log('hook timeout'); return false;
}
function hopDashTo(dir, tx, ty, dashAfter = 3, o = {}) {
  const k = dir > 0 ? 'right' : 'left';
  G.step(1, [k, 'jump'], ['jump']);
  for (let i = 0; i < dashAfter; i++) G.step(1, [k]);
  G.step(1, [k], ['roll']);
  for (let i = 0; i < (o.dashFrames ?? 8); i++) G.step(1, [k]);
  return airTo(tx, ty, { jumps: 0, ...o });
}
function hopTo(fromX, tx, ty, o = {}) { walkTo(fromX, 0.2); return leap(tx, ty, o); }
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
// The Ember, walked without teleporting: E1 -> E5 -> E7 -> E5 -> (the tower, the roof grate) E6 -> E5 -> E4 -> (the flue) E3 ->
// E4 -> E5 -> (the basalt shelves) E1
G.tp('E1', 18, 22); G.step(30); log('start');
wander(1, 'E5'); until(() => G.P.ground, [], 60); walkTo(6.5); until(() => G.P.ground && py() > 27, [], 300);
go(108); wander(1, 'E7'); walkTo(8); wander(-1, 'E5');
go(51);
leap(47, 24); walkTo(48.4, 0.1); leap(54, 21); walkTo(52.6, 0.1); leap(47, 18); walkTo(48.4, 0.1); leap(54, 15); walkTo(52.6, 0.1); leap(47, 12); walkTo(48.4, 0.1); leap(54, 9); walkTo(52.6, 0.1); leap(47, 6); walkTo(48.4, 0.1); leap(51, 3); for (let k = 0; k < 4 && G.room !== 'E6'; k++) { G.step(1, ['jump'], ['jump']); until(() => G.P.ground, ['jump'], 90); }
until(() => G.room === 'E6' && G.P.ground, [], 90); expect('E6'); walkTo(20); walkTo(15.5, 0.3);
for (let k = 0; k < 6 && !(G.room === 'E5' && py() > 8); k++) { dropThrough(); until(() => G.P.ground, [], 120); }
until(() => G.P.ground && py() > 26, [], 300); go(3); wander(-1, 'E4');
walkTo(40); walkTo(21.5, 0.2); log('under the flue');
chimney(19, 23, 0, 600, () => G.room === 'E3'); for (let i = 0; i < 90 && !G.P.ground; i++) G.step(1, ['right', 'jump'], i === 10 ? ['jump'] : []);
until(() => G.P.ground, [], 120); expect('E3'); walkTo(30); walkTo(37.5, 0.3); until(() => G.room === 'E4', [], 200); until(() => G.P.ground, [], 200);
wander(1, 'E5');
go(6.5); G.step(1, ['jump'], ['jump']); G.step(8, ['jump']); chimney(5, 8, 3.6); for (let i = 0; i < 60 && !(G.P.ground && py() < 5); i++) G.step(1, ['left', 'jump']); log('flue top'); wander(-1, 'E1');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };
