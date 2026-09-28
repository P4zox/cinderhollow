// in-page helpers for the RC wing walk tests (prepended to each script by walk_harness.js).
// go(goal) plans a route in the current room with tools/shots/rc/plan.py (the reach checker's physics) and plays it with
// real inputs, re-planning from wherever the player actually stands after each attempt. No teleports: only inputs.
const WL = { log: [], crossings: [], fails: [], last: null, noWind: true, dev: [] };
const sgn = v => v > 0 ? 1 : v < 0 ? -1 : 0;
function wlWatch() {
  if (G.room !== WL.last) {
    if (WL.last) WL.crossings.push(`${WL.last}>${G.room}`);
    WL.log.push(`${WL.last || '-'} -> ${G.room} @${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)}`);
    WL.last = G.room;
  }
  for (const e of G.enemies) if (e.alive && !e.wlDead) { e.wlDead = true; e.hp = 0; if (e.die) e.die({ dir: 1 }); }
  if (WL.noWind && G.SPR && G.SPR.wind) G.SPR.wind.cfg.push = 0;
  if (G.xrc) G.xrc.XRC.noPush = true;
  if (G.state !== 'play') { for (let i = 0; i < 6 && G.state !== 'play'; i++) G.step(1, [], ['pause']); }
}
function wlSpikesBelow() {   // thorns/spikes coming up under the feet (the checker's sim pogoes off them: so does a player)
  const R = G.xrc.room; if (!R || G.P.ground || G.P.vy <= 0 || G.P.state === 'hook') return false;
  const reach = G.P.y + 22 + G.P.vy / 60 * (WL.pogoLead ?? 6);   // where the down-strike's edge will be when it goes live
  for (const x of [G.P.x - 6, G.P.x, G.P.x + 6]) for (let y = G.P.y + 22; y <= reach; y += 3) {
    const tx = Math.floor(x / 16), ty = Math.floor(y / 16);
    if (tx >= 0 && ty >= 0 && tx < R.w && ty < R.h && R.grid[ty * R.w + tx] === 3) return true;
  }
  return false;
}
function st1(ax, jh, jp, rp, extra = []) {
  const hold = [...extra]; if (ax > 0) hold.push('right'); if (ax < 0) hold.push('left'); if (jh) hold.push('jump');
  const tap = []; if (jp) tap.push('jump'); if (rp) tap.push('roll');
  WL.pogoT = (WL.pogoT || 0) - 1;
  if (WL.pogoT <= 0 && wlSpikesBelow()) { hold.push('down'); tap.push('attack'); WL.pogoT = 24; }
  WL.lastIn = [ax, jh]; G.step(1, hold, tap); wlWatch();
}
function idle(n) { for (let i = 0; i < n; i++) st1(0, false, false, false); }
function onCrumble() {   // feet on a crumbling block: no time to stand around, it goes 0.5 s after you touch it
  return G.P.ground && G.xrc.kit().objs.some(o => o.kind === 'crumble' && o.solidNow && Math.abs(G.P.y - o.d.y0) < 3 && G.P.x > o.d.x0 - 6 && G.P.x < o.d.x1 + 6);
}
function settle(n = 120) {
  for (let i = 0; i < n && !(G.P.ground && ['idle', 'run', 'land'].includes(G.P.state)); i++) st1(0, false, false, false);
  if (onCrumble()) return;
  // riding a lift or a mover: wait until it stops (plans start from firm ground)
  let still = 0, y = G.P.y, x = G.P.x;
  for (let i = 0; i < 600 && still < 20; i++) { st1(0, false, false, false); still = (Math.abs(G.P.y - y) < 0.1 && Math.abs(G.P.x - x) < 0.1) ? still + 1 : 0; y = G.P.y; x = G.P.x; }
}
function wlCell() { return [Math.floor(G.P.x / 16), Math.round(G.P.y / 16) - 1]; }
function walkTo(x, room, tol = 1.5) {
  for (let i = 0; i < 400 && Math.abs(G.P.x - x) > tol && G.room === room; i++) {
    const dx = x - G.P.x;
    if (Math.abs(dx) > 8) st1(sgn(dx), false, false, false);
    else { st1(sgn(dx), false, false, false); idle(4); }
  }
  idle(4);
}
async function wlRoute(route, room) {
  for (const e of route) {
    if (G.room !== room) return;
    if (e.kind === 'walkout') { for (let i = 0; i < 500 && G.room === room; i++) st1(e.d, false, false, false); return; }
    if (e.kind === 'body') { /* mid-air start: play the inputs straight away */ }
    else if (e.kind === 'drop') {   // ↓ + jump through a one-way floor
      settle(); walkTo(e.x, room, 2);
      st1(0, false, true, false, ['down']); if (G.room !== room) return;
    }
    else if (e.kind === 'stand') {
      settle();
      if (e.d) {
        walkTo(e.x - e.d * 26, room, 2);
        for (let i = 0; i < 120 && (e.d > 0 ? G.P.x < e.x - 2 : G.P.x > e.x + 2) && G.room === room; i++) st1(e.d, false, false, false);
      } else if (onCrumble()) { for (let i = 0; i < 20 && Math.abs(G.P.x - e.x) > 5; i++) st1(sgn(e.x - G.P.x), false, false, false); }
      else walkTo(e.x, room, 1.2);
      WL.t0 = G.P.x;
    }
    for (const [ax, jh, jp, rp] of e.inputs) { st1(ax, jh, jp, rp); if (G.room !== room) return; }
    const last = e.inputs[e.inputs.length - 1] || [0, false, false, false];
    if (e.end && e.end[0] === 'wall') for (let i = 0; i < 24 && G.P.state !== 'wall' && !G.P.ground && G.room === room; i++) st1(e.end[3] > 0 ? 1 : e.end[3] < 0 ? -1 : last[0], last[1] && G.P.state !== 'glide', false, false);   // a glide won't cling: let go of jump
    if (e.end && e.end[0] === 'stand') for (let i = 0; i < 40 && !G.P.ground && G.room === room; i++) st1(Math.abs(G.P.x - e.end[1]) > 6 ? sgn(e.end[1] - G.P.x) : 0, last[1], false, false);
    if (e.end && e.end[0] === 'goal') return;
  }
}
// leave the current room by an exit ('W'|'E'|'N'|'S', 'a:b') or reach a cell ([x, y]); returns true on success
async function go(goal, needs = 'talon', tries = 30, nokit = true) {
  const room = G.room;
  let noplan = 0;
  for (let k = 0; k < tries; k++) {
    if (typeof goal[0] === 'string' && G.room !== room) return true;
    if (G.room !== room) { WL.fails.push(`${room}: fell out to ${G.room} going for ${goal}`); return false; }
    for (let i = 0; i < 30 && !G.P.ground && G.P.y > G.xrc.room.ph - 3 && G.room === room; i++) st1(WL.lastIn ? WL.lastIn[0] : 0, true, false, false);
    if (goal[0] === 'S' && G.P.ground && G.P.y >= G.xrc.room.ph - 2) {   // standing on the next room's one-way top: drop through
      st1(0, false, true, false, ['down']); for (let i = 0; i < 40 && G.room === room; i++) st1(0, false, false, false, ['down']);
      if (G.room !== room) return true;
    }
    const airborne = !G.P.ground && ['air', 'wall', 'glide'].includes(G.P.state);
    if (!airborne) { settle(); if (k > 0 && !onCrumble()) idle(200); }   // a retry: let crumbled ledges come back first
    if (typeof goal[0] === 'string' && G.room !== room) return true;
    const [tx, ty] = wlCell();
    const start = airborne ? JSON.stringify({ x: G.P.x, y: G.P.y, vx: G.P.vx, vy: G.P.vy, mode: G.P.state === 'wall' ? 'wall' : G.P.state === 'glide' ? 'glide' : 'air', wall: G.P.wallDir || G.P.face, dash: !!G.P.airDash }) : tx;
    const broken = Object.keys(G.SAVE.flags).filter(k => k.startsWith('brk:' + room + ':') && G.SAVE.flags[k]).map(k => k.split(':')[2]).join(';');   // walls/floors already broken
    let r = await window.__plan(room, start, ty, goal[0], goal[1], needs, nokit && noplan < 2, broken);
    if (!r) {   // nowhere the planner knows (in a thorn pit, a lip): hop out one way or the other, then think again
      noplan++; WL.fails.push(`${room}: no plan from ${tx},${ty}${airborne ? ' (air)' : ''} to ${goal}`);
      if (!airborne) { const d = noplan % 2 ? 1 : -1; st1(d, true, true, false); for (let i = 0; i < 24; i++) st1(d, true, false, false); }
      if (airborne) { for (let i = 0; i < 20; i++) st1(0, true, false, false); } else idle(20);   // (keep a glide going)
      continue;
    }
    const route = JSON.parse(r);
    // play edges while the body follows the plan; re-plan as soon as it drifts
    for (const e of route) {
      await wlRoute([e], room);
      if (G.room !== room) break;
      for (let i = 0; i < 90 && e.end && e.end[0] === 'exit' && !G.P.ground; i++) st1(0, false, false, false);
      if (e.end && (e.end[0] === 'stand' || e.end[0] === 'wall')) {
        const dx = G.P.x - e.end[1], dy = G.P.y - e.end[2];
        if (Math.hypot(dx, dy) > 10) { if (WL.dev.length < 60) WL.dev.push(`${room} ${e.kind}:${e.name}@${(e.x / 16).toFixed(1)},${(e.y / 16).toFixed(1)} want ${e.end[0]} ${(e.end[1] / 16).toFixed(1)},${(e.end[2] / 16).toFixed(1)} got ${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)} ${G.P.state} kit ${G.xrc.kit().objs.filter(o => o.kind === 'crumble').map(o => (o.d.x0 / 16).toFixed(0) + ',' + (o.d.y0 / 16).toFixed(0) + ':' + (o.st || o.state)).join(' ')} t${e.inputs.length}`); break; }
      }
    }
    for (let i = 0; i < 90 && G.room === room && !G.P.ground && G.P.state !== 'wall'; i++) st1(0, false, false, false);
    if (typeof goal[0] === 'string' ? G.room !== room : (Math.abs(G.P.x - (goal[0] * 16 + 8)) < 14 && Math.abs(G.P.y - (goal[1] + 1) * 16) < 24)) return true;
  }
  WL.fails.push(`${room}: gave up on ${goal} at ${wlCell()}`);
  return false;
}
async function wlBoot(extra = {}) {
  await boot(); window.requestAnimationFrame = () => 0;   // freeze the page's own loop: only G.step advances the game (plans are async)
  await new Promise(r => setTimeout(r, 100)); G.SETTINGS.god = 1; G.SETTINGS.infst = 1; G.grantTechniques(); G.SAVE.items.talon = 1;
  for (const k of ['hook', 'emberdash', 'slam', 'gale', 'wings', 'moonstep', 'tidebreath']) if (!extra[k]) delete G.SAVE.items[k];
  G.SAVE.seenAreas = { ramparts: 1, spire: 1, deep: 1, crown: 1, lastfield: 1, mire: 1, catacombs: 1, cathedral: 1 };
  G.SAVE.hints = new Proxy({}, { get: () => 1, set: () => true });
}
// walk room to room by a map { room: [goal, nextRoom] } until `target`; falls back (e.g. dropping back down a flue) are redone
async function walkTo2(map, target, maxSteps = 40) {
  for (let n = 0; n < maxSteps && G.room !== target; n++) {
    const r = G.room, step = map[r];
    if (!step) { WL.fails.push(`no step for ${r} (heading for ${target})`); return false; }
    if (typeof step[0] === 'function') await step[0]();
    else await go(step[0], step[2] || 'talon');
    if (G.room === r) { WL.fails.push(`stuck in ${r}`); return false; }
    if (G.room !== step[1]) WL.log.push(`  (${r} -> ${G.room}, meant ${step[1]})`);
  }
  return G.room === target;
}
// ---- rope swings (the checker's sim treats them as hook points; played here by trial and error, like a player would):
// legs = [{ from: [x0, x1, row], edge: x, chain: [{ swing: i } | { land: [x0, x1, row] }, ...] }, ...], dir = ±1
function wlSwings() { return G.xrc.kit().objs.filter(o => o.kind === 'swing'); }
function wlOn(sup) { return G.P.ground && G.P.x >= sup[0] * 16 - 4 && G.P.x <= (sup[1] + 1) * 16 + 4 && Math.abs(G.P.y - sup[2] * 16) < 4; }
function wlReached(t) { return t.swing !== undefined ? (G.P.state === 'hook' && G.P.hook && G.P.hook.kit === wlSwings()[t.swing]) : wlOn(t.land); }
function wlLeap(w, t, dir, dashAt = -1) {
  const hook = G.P.state === 'hook';
  for (let i = 0; i < w; i++) { st1(hook ? 0 : 0, false, false, false); if (hook && G.P.state !== 'hook') return false; }
  st1(dir, true, true, false);
  for (let i = 0; i < 200; i++) {
    st1(dir, i < 20, false, i === dashAt);
    if (wlReached(t)) { if (t.land) settle(); return true; }
    if (G.P.state === 'hook' || G.P.ground) return false;   // caught the wrong rope / landed short
  }
  return false;
}
async function wlSwingRun(legs, dir, room, maxTries = 300) {
  let tries = 0;
  for (let li = 0; li < legs.length && tries < maxTries; ) {
    if (G.room !== room) return true;
    const L = legs[li];
    settle(40);
    // where am I? resume from the last support I'm standing on
    const at = legs.findIndex(l => wlOn(l.from));
    if (at < 0) {
      if (legs.length && wlOn(legs[legs.length - 1].chain.slice(-1)[0].land)) return true;
      // somewhere unplanned (a ledge, a wall): walk back to the nearest support the run knows and carry on from there
      const near = legs.map(l => l.from).sort((a, b) => Math.abs((a[0] + a[1]) * 8 - G.P.x) - Math.abs((b[0] + b[1]) * 8 - G.P.x))[0];
      WL.log.push(`  swing run: off the plan at ${wlCell()}, back to ${near}`); tries += 5;
      await go([Math.round((near[0] + near[1]) / 2), near[2] - 1], 'talon', 6); continue;
    }
    li = at;
    walkTo(legs[li].edge * 16 + 8, room, 2);
    let ok = true;
    for (const [k, t] of legs[li].chain.entries()) {   // spread the take-off moments over the ropes' 3 s period
      const w = (tries * 37 + k * 53) % 180, dashAt = [-1, 4, 10, 16, 22][(tries * 3 + k) % 5]; tries++;
      if (!wlLeap(w, t, dir, dashAt)) { ok = false; WL.swstat = WL.swstat || {}; const key = `${li}.${k} ${G.P.state}${G.P.hook && G.P.hook.kit ? wlSwings().indexOf(G.P.hook.kit) : ''} ${(G.P.x / 16).toFixed(0)},${(G.P.y / 16).toFixed(0)}`; WL.swstat[key] = (WL.swstat[key] || 0) + 1; break; }
    }
    if (ok) li++;
    else { idle(40); }   // fell: the sea puts you back on the last safe ground; try again from there
  }
  WL.log.push(`  swing run: ${tries} leaps ${JSON.stringify(WL.swstat || {})}`);
  return tries < maxTries;
}
