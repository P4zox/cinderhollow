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
// Starfall wing, walked without teleporting: SF7 -> SF10 -> SF16 -> SF10 -> SF13 -> SF14 -> SF17 -> SF14 -> SF11 -> SF18 ->
// SF11 -> SF12 -> SF15 -> SF12 -> SF11 -> (the pool) SF9 -> SF6 -> SF7 -> SF10 -> SF13 -> SF14 -> SF11, then back down:
// SF11 -> SF14 -> SF13 -> SF10 -> SF7
G.tp('SF7', 40, 16); G.step(30); log('start');
const met = (id, x, y) => { waitSolid(id, 0.35, 600, 0.9); return leap(x, y, { jumps: 1 }); };
const climbWing = () => {   // SF7 -> SF10 -> (SF16 and back) -> SF13 -> SF14 -> (SF17 and back) -> SF11
  wander(1, 'SF10');
  hopTo(18, 21, 8); leap(24, 5); leap(27, 4); walkTo(35.5); hopTo(35.5, 42, 9);
  exitTo(1, 'SF16'); walkTo(20); exitTo(-1, 'SF10');
  hopTo(44, 46, 7); leap(49, 4); leap(51, 2); leap(51, 20, { jumps: 1 }); expect('SF13');
  met('m0', 46, 19); leap(42, 16); met('m1', 38, 14); met('m2', 34, 12); leap(30, 11); met('m3', 25, 9); met('m4', 21, 8); leap(17, 8);
  met('m5', 13, 7); leap(5, 6); leap(7, 3); leap(7, 0); leap(6, 26, { jumps: 1 }); expect('SF14');
  leap(12, 23); leap(20, 20); leap(28, 17); leap(36, 14); leap(43, 16); exitTo(1, 'SF17'); walkTo(9); exitTo(-1, 'SF14');
  leap(36, 14); leap(28, 11); leap(19, 8); leap(10, 6); leap(4, 4); exitTo(-1, 'SF11');
};
climbWing();
// the Expanse: up the east shelves to the high road, up into the Moonstep Spire and back, west to the canyon
hopTo(116, 114, 21); leap(106, 18); leap(98, 15); leap(88, 14); leap(77, 11); leap(80, 6); leap(83, 2); leap(82, 44, { jumps: 1 });
until(() => G.room === 'SF18', ['jump'], 60); until(() => G.P.ground, [], 120); expect('SF18');
walkTo(31.5); dropThrough(); dropThrough(); until(() => G.room === 'SF11' && G.P.ground, [], 200); expect('SF11');
walkTo(80); walkTo(76.5); leap(68, 9); leap(59, 6); leap(49, 7); leap(41, 3); leap(33, 6); leap(25, 9); leap(17, 11); leap(8, 14); exitTo(-1, 'SF12');
walkTo(36); walkTo(24); walkTo(16); wander(-1, 'SF15'); walkTo(30); wander(1, 'SF12');
walkTo(19); leap(22, 13); leap(32, 10); leap(41, 7); exitTo(1, 'SF11');
// the low road east to the starlight pool: it drains into the Last Light, which opens onto the Crater Rim (the loop back)
walkTo(13); walkTo(17); until(() => G.P.ground, [], 60); hopTo(18, 24, 23); wander(1, 'SF9');
until(() => G.P.ground, [], 200); wander(-1, 'SF6'); wander(1, 'SF7');
climbWing();
// and back down the wing
wander(1, 'SF14'); walkTo(4); leap(10, 6, { jumps: 0 }); for (let i = 0; i < 90 && !(G.P.ground && py() > 20); i++) G.step(1, ['right']); walkTo(11); leap(6, 26, { jumps: 0 });
dropThrough(); until(() => G.room === 'SF13' && G.P.ground, [], 200);
for (let k = 0; k < 3 && py() < 7; k++) { dropThrough(); until(() => G.P.ground, [], 120); }
met('m5', 13, 7); leap(17, 8); met('m4', 21, 8); met('m3', 25, 9); leap(30, 11); met('m2', 34, 12); met('m1', 38, 14); leap(42, 16); met('m0', 46, 19); leap(51, 20);
for (let k = 0; k < 6 && !(G.room === 'SF10' && py() > 11); k++) { dropThrough(); until(() => G.P.ground, [], 120); }
walkTo(46); hopTo(45, 42, 9); leap(34, 8); leap(31, 5); leap(27, 4); leap(24, 5); leap(21, 8); walkTo(15); wander(-1, 'SF7');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };
