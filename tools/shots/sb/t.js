// deterministic replay search for trials: plans are per-frame [hold, tap] pairs replayed from a fresh sigil start
const S = window.__sys;
const TR = { log: [] };
TR.start = () => { if (TR.room && (G.room !== TR.room || !S.SYS.trial && Math.abs(G.P.x - TR.home[0]) > 4)) { G.tp(TR.room, TR.home[1], TR.home[2]); for (let i = 0; i < 3; i++) { G.step(10); settle(); } } G.step(1, [], ['interact']); G.step(1); };
TR.run = (plan, check, extra) => {   // replay plan; then optionally run a policy fn(frame)->[hold,tap] until check() or fail
  TR.start(); const a0 = S.SYS.trial ? S.SYS.trial.attempts : -1; if (a0 < 0) return { ok: false, why: 'nostart' };
  const alive = () => (S.SYS.result && S.SYS.result.time !== undefined && !S.SYS.trial && TR.done0 !== S.SYS.result) || (S.SYS.trial && S.SYS.trial.attempts === a0);
  for (let i = 0; i < plan.length; i++) { G.step(1, plan[i][0], plan[i][1]); if (!alive()) return { ok: false, frame: i, why: 'prefix' }; }
  const rec = [];
  if (extra) for (let i = 0; i < (extra.max || 400); i++) {
    if (check()) return { ok: true, rec };
    const inp = extra.fn(i); if (!inp) break; rec.push(inp); G.step(1, inp[0], inp[1]);
    if (S.SYS.result && TR.done0 !== S.SYS.result) return { ok: true, rec, done: true };
    if (!alive()) return { ok: false, frame: i, rec, why: S.SYS.trial && S.SYS.trial.why };
  }
  return { ok: check(), rec };
};
// random chunk policy (dir = -1 left / +1 right)
TR.chunks = (dir, opts = {}) => {
  const L = dir < 0 ? 'left' : 'right', seq = [];
  const n = 2 + Math.floor(Math.random() * (opts.n || 6));
  for (let k = 0; k < n; k++) {
    const r = Math.random();
    if (r < 0.35) { const m = 3 + Math.floor(Math.random() * 20); for (let i = 0; i < m; i++) seq.push([[L], []]); }
    else if (r < 0.75) { const h = 4 + Math.floor(Math.random() * 22), m = 20 + Math.floor(Math.random() * 30); seq.push([[L, 'jump'], ['jump']]); for (let i = 0; i < m; i++) seq.push([i < h ? [L, 'jump'] : [L], []]); }
    else if (r < 0.9 || !opts.roll) { const m = 1 + Math.floor(Math.random() * 30); for (let i = 0; i < m; i++) seq.push([[], []]); }
    else { seq.push([[L], ['roll']]); for (let i = 0; i < 20; i++) seq.push([[L], []]); }
  }
  for (let i = 0; i < 200; i++) seq.push([[L], []]);
  return seq;
};
TR.search = (prefix, check, dir, tries, opts = {}) => {
  for (let t = 0; t < tries; t++) {
    const seq = opts.gen ? opts.gen() : TR.chunks(dir, opts);
    const r = TR.run(prefix, check, { fn: i => seq[i], max: seq.length });
    if (r.ok) { TR.log.push('seg ok after ' + (t + 1) + ' tries, +' + r.rec.length + ' frames'); return prefix.concat(r.rec); }
  }
  TR.log.push('seg FAILED'); return null;
};
// depth-first search over short action chunks with full replays on backtrack (the trial resets deterministically)
TR.dfs = (prefix, goal, acts, stepN, maxDepth, budget = 4000) => {
  const choice = [0];
  let replays = 0;
  const replay = () => { replays++; TR.start(); const a0 = S.SYS.trial.attempts; for (const f of prefix) G.step(1, f[0], f[1]); for (let d = 0; d < choice.length - 1; d++) for (let k = 0; k < stepN; k++) { const a = acts[choice[d]]; G.step(1, a[0], k === 0 ? a[1] : []); } return a0; };
  let a0 = replay();
  while (choice.length && replays < budget) {
    const d = choice.length - 1;
    if (choice[d] >= acts.length) { choice.pop(); if (!choice.length) break; choice[choice.length - 1]++; a0 = replay(); continue; }
    const a = acts[choice[d]]; let dead = false;
    for (let k = 0; k < stepN; k++) { G.step(1, a[0], k === 0 ? a[1] : []); if (!S.SYS.trial || S.SYS.trial.attempts !== a0 || G.room !== TR.room) { dead = true; break; } }
    if (!dead && goal()) { TR.log.push('dfs ok depth ' + choice.length + ' replays ' + replays); const out = prefix.slice(); for (const c of choice) for (let k = 0; k < stepN; k++) out.push([acts[c][0], k === 0 ? acts[c][1] : []]); return out; }
    if (dead || choice.length >= maxDepth) { choice[d]++; a0 = replay(); continue; }
    choice.push(0);
  }
  TR.log.push('dfs FAILED replays ' + replays + ' depth ' + choice.length); return null;
};
G.SAVE.items.emberdash = 1; G.tp('NV15', 51, 12); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
TR.done0 = S.SYS.result; TR.room = 'NV15'; TR.home = [51 * 16 + 8, 51, 12];
const P = () => G.P;
const onFloor = (x0, x1, y) => P().ground && P().x > x0 && P().x < x1 && Math.abs(P().y - y) < 1;
const acts = [[['left'], []], [['left', 'jump'], ['jump']], [[], []], [['left'], ['roll']], [['right'], []], [['jump'], ['jump']]];
let plan = TR.dfs([], () => onFloor(368, 386, 208), acts, 4, 90, 6000);
if (!plan) return TR.log;
plan = TR.search(plan, () => onFloor(290, 352, 208), -1, 300, { gen: () => { const s = []; const w = Math.floor(Math.random() * 12); for (let i = 0; i < w; i++) s.push([[], []]); s.push([['left'], ['roll']]); for (let i = 0; i < 60; i++) s.push([Math.random() < 0.5 ? ['left'] : [], []]); return s; } });
if (!plan) return TR.log;
const climb = () => { let side = -1, tap = 0, ph = 0;
  return i => {
    const p = P(); const L = side < 0 ? 'left' : 'right';
    if (ph === 0) { if (p.x > 283) return [['left'], []]; ph = 1; return [['left', 'jump'], ['jump']]; }
    if (p.y < 60) return [['left'], []];
    if (p.state === 'wall' && tap <= 0) { side = -side; tap = 8; return [[side < 0 ? 'left' : 'right', 'jump'], ['jump']]; }
    tap--; return [p.vy < 0 ? [L, 'jump'] : [L], []];
  }; };
let got = null;
for (let t = 0; t < 40 && !got; t++) {
  const w = t % 10, f = climb();
  const r = TR.run(plan, () => onFloor(16, 190, 64), { fn: i => i < w ? [[], []] : f(i - w), max: 400 });
  if (r.ok) got = plan.concat(r.rec);
}
TR.log.push('climb ' + !!got); if (!got) return TR.log; plan = got;
TR.run(plan, () => false, { fn: i => [['left'], []], max: 200 });
TR.log.push('result ' + JSON.stringify(S.SYS.result && { t: S.SYS.result.time, gold: S.SYS.result.gold, first: S.SYS.result.first }) + ' plan frames ' + plan.length);
for (let i = 0; i < 260; i++) G.step(1);
TR.log.push('charm ' + G.SAVE.charms.includes('c_x3_hood'));
await snap('nv15_done');
return { log: TR.log, plan: plan.map(f => (f[0].join('+') || '_') + (f[1].length ? '!' + f[1].join('+') : '')).join(' ') };
