// SC trial autopilot helpers (prepended to a trial script). G = window.__game.
const T16 = 16, S = () => window.__sys.SYS;
const px = () => G.P.x / T16, py = () => G.P.y / T16;          // py: feet in tiles (standing row + 1)
const att = () => (S().trial ? S().trial.attempts : -1);
const LOG = [];
const log = m => LOG.push(`[${(S().trial ? S().trial.t : 0).toFixed(2)}] ${m} @${px().toFixed(2)},${py().toFixed(2)} ${G.P.state}`);
function stepN(n, hold = [], tap = []) { G.step(n, hold, tap); }
// walk to tile-centre x on the ground
function walkTo(x, tol = 0.15, max = 400) {
  for (let i = 0; i < max; i++) { const d = x - px(); if (Math.abs(d) < tol && Math.abs(G.P.vx) < 30) return true; G.step(1, Math.abs(d) < tol ? [] : d > 0 ? ['right'] : ['left']); if (Math.abs(d) < 0.6 && Math.abs(d) >= tol) G.step(1); }
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
    const d = (tx + 0.5) * T16 - G.P.x, hold = ((G.P.vy < 0 && (o.holdT === undefined || t < o.holdT)) || o.glide) ? ['jump'] : [], tap = [];
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
G.step = (n = 60, h = [], t = []) => { const r = _gstep(n, h, t); if (TRACE && (TRACE.n++ % (TRACE.every || 4) === 0)) TRACE.out.push(`${px().toFixed(1)},${py().toFixed(1)} vy=${G.P.vy | 0} ${G.P.state} ${h.join('+')}${t.length ? ' !' + t.join('+') : ''}`); return r; };
// climb a chimney between walls at tile columns wl (left wall) and wr (right wall) until feet are above row topY
function chimney(wl, wr, topY, max = 600) {
  const a0 = att(); let dir = -1;
  for (let i = 0; i < max; i++) {
    if (att() !== a0) { log('RESET in chimney why=' + S().trial.why); return false; }
    if (G.P.y < topY * T16) { log('chimney top'); return true; }
    if (G.P.state === 'wall') { dir = -G.P.wallDir; G.step(1, ['jump'], ['jump']); continue; }
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
    const d = (tx + 0.5) * T16 - G.P.x, hold = [], tap = [];
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
    if (past && G.P.vx * dir > (o.minV ?? 90)) { G.step(1, [k], ['jump']); log('hook release'); return true; }
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
// NH16 The Glitch Run: a full scripted clear (needs talon, emberdash)
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1 });
G.tp('NH16', 4, 20); G.step(30); G.step(1, [], ['interact']); G.step(5); log('sigil');
walkTo(6.8);
const hop = (id, x, y, cur, flight = 0.55, o = {}) => { waitTakeoff(id, flight, cur); return leap(x, y, { jumps: 0, ...o }); };
hop('p0', 9, 18, null); hop('p1', 13, 17, 'p0'); hop('p2', 17, 16, 'p1');
waitTakeoff('p3', 0.5, 'p2'); hopDash(1, 3);
waitTakeoff('p3', 0.0, null, 0, 0.05); leap(28, 14, { jumps: 0 });
hop('p4', 32, 12, null, 0.6); hop('p5', 35, 9, 'p4'); leap(38, 8, { jumps: 0 });
waitTakeoff('p6', 0.55, null); leap(45, 8, { jumps: 0, dash: true, dashT: 3, dashAt: 20, holdT: 6 });
hop('p7', 49, 6, 'p6', 0.5, { holdT: 9 }); hop('p8', 53, 6, 'p7', 0.45, { holdT: 6 }); leap(59, 5, { jumps: 0, holdT: 8 }); walkTo(60.5);
for (let i = 0; i < 30; i++) G.step(1);
await snap('trial_nh16');

for (let i = 0; i < 260; i++) G.step(1);
const rec = window.__sys.x3().trials['NH16:glitch'];
return [...LOG, 'rec ' + JSON.stringify(rec), 'charm ' + G.SAVE.charms.includes('c_x3_glitch')];
