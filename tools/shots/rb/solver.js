// generic trial solver (runs in the page): finds, move by move, input programs that carry the player from the sigil to the
// goal, replaying the moves found so far from a fresh start for every candidate (the game is deterministic from the sigil).
window.__solve = async function (roomId, sx, sy, moves, opt = {}) {
  const G = window.__game, S = window.__sys, RB = window.__rb, sim = RB.sim, log = [];
  G.tp(roomId, sx, sy); G.step(30);
  const T = () => S.SYS.trial;
  const restart = () => {
    const tr = T(), p = tr ? tr.p : G.props.find(q => q.type === 'sys_trial' || (q.s && q.s.kind === 'trial'));
    const P = G.P; if (P.hook) sim(1, [], ['jump']); P.x = p.x; P.y = p.y; P.vx = P.vy = 0; sim(40); P.x = p.x; P.y = p.y; sim(1, [], ['interact']); sim(20);
    return T();
  };
  const stand = () => G.P.ground && !G.P.hook;
  // one program: [dir, run frames, jump hold frames, dash at frame (or -1), extra: hook at frame / release at frame]
  const playHook = (m, c) => {   // c = [dir, pump|run, hold, dash, hookAt, relDelay]
    const [dir, pre, hold, dash, hookAt, rel] = c, d = dir < 0 ? 'left' : 'right', P = G.P;
    const a0 = T() ? T().attempts : 0;
    if (P.hook) { if (pre) sim(pre, [d]); if (rel) sim(rel); sim(1, [d, 'jump'], ['jump']); }
    else { if (pre) sim(pre, [d]); sim(1, [d, 'jump'], ['jump']); }
    let air = false;
    for (let f = 1; f < (m.max || 160); f++) {
      const hs = [d]; if (f < hold) hs.push('jump');
      const tap = []; if (f === dash) tap.push('roll'); if (f === hookAt) tap.push('hook');
      sim(1, hs, tap);
      if (!T() || T().attempts !== a0) return { fail: true, f, goal: !!S.SYS.result };
      if (m.ring && P.hook && P.hook.h && Math.abs(P.hook.h.x - (m.ring[0] * 16 + 8)) < 2 && Math.abs(P.hook.h.y - (m.ring[1] * 16 + 8)) < 2 && !P.hook.zip) return { ring: true, f };
      if (m.ring && P.hook && f > hookAt + 40) return { wrong: true };
      if (!P.ground) air = true;
      if (m.to && f > 3 && air && P.ground && !P.hook) { sim(m.settle ?? 10); return { f, x: P.x / 16, y: P.y / 16, g: P.ground }; }
      if (m.ring && P.ground && air) return { landed: true };
    }
    return { timeout: true };
  };
  const play = (m, c, until) => {
    if (m.hookMove) return playHook(m, c);
    const [dir, run, hold, dash, hookAt, relAt, tail] = c, d = dir < 0 ? 'left' : 'right';
    const a0 = T() ? T().attempts : 0;
    if (run > 0) sim(run, [d]);
    if (hold >= 0) sim(1, [d, 'jump'], ['jump']);
    let f = 0, ok = false, hooked = false, air = false;
    for (f = 1; f < (m.max || 150); f++) {
      const hs = [d]; if (f < hold) hs.push('jump');
      const tap = [];
      if (f === dash) tap.push('roll');
      if (f === hookAt) tap.push('hook');
      if (relAt > 0 && f === relAt) tap.push('jump');
      if (m.up) hs.push('up');
      sim(1, hs, tap);
      if (!T() || T().attempts !== a0) return { fail: true, f };
      if (T().done || S.SYS.result && S.SYS.result.t < 0.5 && !T()) return { goal: true };
      if (!G.P.ground) air = true;
      if (f > 3 && air && stand()) break;
    }
    if (tail) sim(tail, [d]);
    sim(m.settle ?? 10);   // landing lag: let it pass before the next move's inputs
    return { f, x: G.P.x / 16, y: G.P.y / 16, g: G.P.ground };
  };
  const found = [];
  for (let mi = 0; mi < moves.length; mi++) {
    const m = moves[mi]; let got = null, tries = 0;
    for (const c of m.cands) {
      tries++;
      if (!restart()) return { log, err: 'no trial' };
      let bad = false;
      let why = '';
      for (let k = 0; k < found.length; k++) { const r = play(moves[k], found[k]); if (r.fail) { bad = true; why = `k ${k} f ${r.f} why ${T() && T().why} at ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} cand ${tries} ${JSON.stringify(c)} ice ${G.props.filter(q => q.type === 'hf_icicle').map(q => q.st[0]).join('')}`; break; } }
      if (bad) return { log, err: 'prefix broke at move ' + mi + ' ' + why };
      const r = play(m, c);
      if (S.SYS.result && !T()) { got = c; log.push(`move ${mi} GOAL with ${JSON.stringify(c)} after ${tries}`); break; }
      if (r.fail) { if (opt.v) log.push(`  m${mi} c${JSON.stringify(c)} fail f${r.f} ${T() && T().why}`); continue; }
      if (opt.v && m.ring) log.push(`  m${mi} ${JSON.stringify(c)} ${JSON.stringify(r)} P ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} hook ${G.P.hook && G.P.hook.h ? ((G.P.hook.h.x-8)/16)+','+((G.P.hook.h.y-8)/16) : '-'}`);
      if (m.ring) { if (r.ring) { got = c; log.push(`move ${mi} ring ${JSON.stringify(c)} after ${tries}`); break; } continue; }
      const [x0, x1, row] = m.to;
      if (opt.v) log.push(`  m${mi} c${JSON.stringify(c)} -> ${r.x && r.x.toFixed(1)},${r.y && r.y.toFixed(1)}`);
      if (r.g && Math.abs(r.y - row) < 0.05 && r.x >= x0 && r.x <= x1 + 1) { got = c; log.push(`move ${mi} ok ${JSON.stringify(c)} -> ${r.x.toFixed(1)},${r.y.toFixed(1)} after ${tries}`); break; }
    }
    if (!got) return { log, err: 'no solution for move ' + mi, found };
    found.push(got);
    if (S.SYS.result && !T()) break;
  }
  // a clean timed run
  S.SYS.result = null; restart(); const t0 = performance.now(); let frames = 0;
  for (let k = 0; k < found.length; k++) { const r = play(moves[k], found[k]); log.push(`clean ${k}: ${JSON.stringify(r)} result ${!!S.SYS.result}`); }
  sim(60, [found[found.length - 1][0] < 0 ? 'left' : 'right']);
  return { log, found, result: S.SYS.result && { time: +S.SYS.result.time.toFixed(2), gold: S.SYS.result.gold, par: S.SYS.result.par, first: S.SYS.result.first }, rec: JSON.stringify(S.x3().trials) };
};
// candidate generator: dirs × run × hold × dash
window.__cands = (dirs, runs, holds, dashes, extra = [[-1, -1, 0]]) => {
  const out = [];
  for (const d of dirs) for (const r of runs) for (const h of holds) for (const ds of dashes) for (const e of extra) out.push([d, r, h, ds, ...e]);
  return out;
};
