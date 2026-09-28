// Route walker (runs in the page). It walks a list of rooms edge by edge with plain inputs (no teleport inside a route):
//  - search: from the exact state the player entered a room with (snapshot), a greedy best-first search over short input
//    programs (jumps with run-up / hold / dash, walk-offs, drop-throughs, wall jumps, reactive wall climbs, interact, wait,
//    strikes) finds a sequence that carries the player into the next room of the route. Every candidate is replayed from
//    the room-entry snapshot, so it is exact.
//  - verify: the whole route is then replayed from its start with no snapshot, restore or teleport, logging each room change.
window.__walker = (() => {
  const G = window.__game, RB = window.__rb, sim = RB.sim;
  const P = () => G.P;
  const clear = () => RB.clearFoes();
  const step = (hold = [], tap = []) => { sim(1, hold, tap); clear(); };
  const stable = () => P().ground && !['land', 'roll'].includes(P().state) && Math.abs(P().vx) < 30;
  const D = d => d < 0 ? 'left' : d > 0 ? 'right' : null;
  // ---- programs: run() plays it from the current state; returns {room change?, end state}
  function play(pr, maxF = 300) {
    const r0 = G.room; let air = !P().ground, f = 0, wallSeen = false;
    const H = (...a) => a.filter(Boolean);
    for (f = 0; f < maxF; f++) {
      const d = D(pr.d), p = P();
      let hold = [], tap = [];
      switch (pr.k) {
        case 'J': {   // run-up, jump (hold for pr.h frames), optional dash at pr.dash (or at the apex), steer pr.post after pr.sw
          if (f < pr.run) hold = H(d);
          else if (f === pr.run) { hold = H(d, 'jump'); tap = ['jump']; }
          else { const g = f - pr.run; hold = H(pr.sw && g >= pr.sw ? D(pr.post) : d); if (g < pr.h) hold.push('jump');
            if (pr.dash === 'apex' ? (!pr._dashed && p.vy >= 0 && g > 3) : g === pr.dash) { tap = ['roll']; pr._dashed = true; } }
          break;
        }
        case 'W': hold = H(d); if (f >= pr.n && !air) return fin(r0, f); break;
        case 'DROP': if (f < 2) hold = ['down']; else if (f === 2) { hold = ['down', 'jump']; tap = ['jump']; } else hold = H(d); break;
        case 'WJ': if (f === 0) { hold = H(D(-pr.side), 'jump'); tap = ['jump']; } else { hold = H(f < pr.t ? D(-pr.side) : D(pr.post)); if (f < 12) hold.push('jump'); } break;
        case 'CLIMB': hold = H(D(pr.side)); if (p.state === 'wall') { hold.push('jump'); tap = ['jump']; } else if (f < 10) hold.push('jump'); if (f === 0 && p.ground) tap = ['jump']; break;
        case 'INT': if (f === 0) tap = ['interact']; if (f >= 40) return fin(r0, f); break;
        case 'WAIT': if (f >= pr.n) return fin(r0, f); break;
        case 'ATK': hold = f % 20 < 2 ? H(d) : []; if (f % 20 === 2) tap = ['attack']; if (f >= 60) return fin(r0, f); break;
      }
      pr._pre && pr._pre(f);
      step(hold, tap);
      if (G.room !== r0) return { changed: true, f };
      if (!P().ground) air = true;
      if (P().state === 'wall') wallSeen = true;
      if (pr.k !== 'W' && pr.k !== 'INT' && pr.k !== 'WAIT' && pr.k !== 'ATK' && f > 3) {
        if (air && stable()) return fin(r0, f);
        if (P().state === 'wall' && f > 6 && pr.k !== 'CLIMB') return fin(r0, f);
        if (P().state === 'swim' && f > 30 && Math.abs(P().vy) < 20) return fin(r0, f);
      }
      if (pr.k === 'W' && air && stable()) return fin(r0, f);
      if (G.state === 'dead') return { dead: true };
    }
    return fin(r0, f);
  }
  function fin(r0, f) { for (let i = 0; i < 40 && P().ground && !stable(); i++) { step(); if (G.room !== r0) return { changed: true, f }; } return { f }; }
  // the candidate programs from a node (state-dependent)
  function cands(extra) {
    const p = P(), out = [];
    if (p.state === 'wall') {
      const s = p.wallDir || p.face;
      for (const t of [4, 10, 16]) for (const post of [s, 0, -s]) out.push({ k: 'WJ', side: s, t, post });
      out.push({ k: 'CLIMB', side: s }); out.push({ k: 'W', d: -s, n: 20 });
      return out;
    }
    for (const d of [1, -1, 0]) {
      for (const run of d ? [0, 10, 24] : [0]) for (const h of [5, 20]) for (const dash of [-1, 'apex'])
        out.push({ k: 'J', d, run, h, dash });
      if (d) { out.push({ k: 'J', d, run: 0, h: 20, dash: -1, sw: 14, post: 0 }); out.push({ k: 'J', d, run: 0, h: 20, dash: -1, sw: 10, post: -d }); }
      if (d) { out.push({ k: 'W', d, n: 16 }); out.push({ k: 'W', d, n: 48 }); out.push({ k: 'CLIMB', side: d }); }
      out.push({ k: 'DROP', d });
    }
    out.push({ k: 'WAIT', n: 90 });
    if (extra) out.push(...extra());
    return out;
  }
  const key = () => { const p = P(); return `${G.room}:${Math.floor(p.x / 16)},${Math.round(p.y / 16)}:${p.state === 'wall' ? 'w' + (p.wallDir || p.face) : p.state === 'swim' ? 's' : 'g'}:${Object.keys(G.SAVE.flags).length}`; };
  // the shared edge between two rooms, as a global point
  function edgePoint(a, b) {
    const A = RB.ROOM_BY[a], B = RB.ROOM_BY[b]; let sx = 0, sy = 0, n = 0;
    const open = (R, gx, gy) => { const x = gx - R.gx, y = gy - R.gy; return x >= 0 && y >= 0 && x < R.w && y < R.h && !'#_BY'.includes(R.map[y][x]); };
    for (let y = A.gy; y < A.gy + A.h; y++) for (let x = A.gx; x < A.gx + A.w; x++) {
      if (!open(A, x, y)) continue;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (open(B, x + dx, y + dy) && !(x + dx >= A.gx && x + dx < A.gx + A.w && y + dy >= A.gy && y + dy < A.gy + A.h)) { sx += x; sy += y; n++; }
    }
    return n ? { x: sx / n, y: sy / n } : { x: B.gx + B.w / 2, y: B.gy + B.h / 2 };
  }
  const gpos = () => { const R = RB.ROOM_BY[G.room]; return { x: R.gx + P().x / 16, y: R.gy + (P().y - 14) / 16 }; };
  // search one hop: from snapshot S (in room a), reach room b
  function hop(S, b, opt = {}) {
    const goal = edgePoint(S.room, b), t0 = performance.now();
    const onE = () => { const f = opt.onEnter && opt.onEnter[S.room]; if (f) f(); };
    const replay = path => { RB.restore(S); clear(); onE(); for (const pr of path) { const r = play({ ...pr }); if (r.changed || r.dead) return r; } return {}; };
    const h = () => { const q = gpos(); return Math.abs(q.x - goal.x) + Math.abs(q.y - goal.y) * 1.3; };
    const open = [{ path: [], h: 1e9 }], seen = new Set(); let exp = 0;
    RB.restore(S); clear(); onE(); seen.add(key());
    while (open.length && exp < (opt.budget || 400) && performance.now() - t0 < (opt.ms || 900000)) {
      open.sort((u, v) => u.h - v.h); const node = open.shift(); exp++;
      replay(node.path); if (G.room !== S.room) continue;
      const cs = cands(opt.extra);
      for (const c of cs) {
        replay(node.path); const r = play({ ...c });
        if (r.changed) { if (G.room === b) return { path: [...node.path, c], exp, ms: Math.round(performance.now() - t0) }; continue; }
        if (r.dead || G.room !== S.room) continue;
        const k = key(); if (seen.has(k)) continue; seen.add(k);
        open.push({ path: [...node.path, c], h: h() + node.path.length * 0.3 });
      }
    }
    return { fail: true, exp, seen: seen.size };
  }
  // walk a route: [startRoom, tx, ty] then room ids. Searches hop by hop, then verifies with one clean replay.
  function route(start, rooms, opt = {}) {
    const log = [], plan = [];
    G.tp(start[0], start[1], start[2]); for (let i = 0; i < 30; i++) step();
    const S0 = RB.snap(); let S = S0;
    for (const b of rooms) {
      const extra = (opt.extra && opt.extra[G.room]) || null;
      const r = hop(S, b, { ...opt, extra });
      if (!r.fail) log.push('  ' + r.path.map(p => p.k + (p.d !== undefined ? p.d : '') ).join(' '));
      if (r.fail) { log.push(`FAIL ${S.room} -> ${b} (expanded ${r.exp}, states ${r.seen})`); return { log, ok: false }; }
      RB.restore(S); clear(); if (opt.onEnter && opt.onEnter[S.room]) opt.onEnter[S.room](); for (const pr of r.path) { const q = play({ ...pr }); if (q.changed) break; }
      log.push(`search ${S.room} -> ${b}: ${r.path.length} programs, ${r.exp} expansions, ${r.ms} ms`);
      plan.push(...r.path.map(p => ({ ...p })));
      plan.push({ k: '@', room: b });
      S = RB.snap();
    }
    // clean replay: no restore, no teleport after the start
    RB.restore(S0); clear(); if (opt.onEnter && opt.onEnter[S0.room]) opt.onEnter[S0.room](); const seq = [S0.room];
    for (const pr of plan) {
      if (pr.k === '@') { if (G.room !== pr.room) { log.push(`VERIFY: expected ${pr.room}, in ${G.room}`); return { log, ok: false, seq }; } continue; }
      const r0 = G.room; play({ ...pr }); if (G.room !== r0) { seq.push(G.room); if (opt.onEnter && opt.onEnter[G.room]) opt.onEnter[G.room](); }
    }
    log.push('clean walk: ' + seq.join(' > '));
    return { log, ok: seq.join() === [S0.room, ...rooms].join(), seq, plan };
  }
  return { route, hop, play, edgePoint };
})();
await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1 } });
G.SAVE.flags['x3:A13:cipher'] = 1;   // the Cipher Wall's puzzle (solved in puzzles.js) opens A13 -> A12
const W = window.__walker, t0 = performance.now();
const route = ['A8', 'A5', 'A8', 'A13', 'A12', 'A13', 'A8', 'A10', 'A15', 'A10', 'A9', 'A15', 'A9', 'A16', 'A9', 'A10', 'A11', 'A14', 'A11', 'A10', 'A8', 'A4'];
const r = W.route(['A5', 20, 10], route, { budget: 1500, extra: { A9: () => [{ k: 'ATK', d: 1 }] } });
r.log.push(`ok ${r.ok} total ${Math.round((performance.now() - t0) / 1000)} s`);
return r.log;
