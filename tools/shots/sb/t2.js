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
G.tp('DU16', 5, 3); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
TR.done0 = S.SYS.result; TR.room = 'DU16'; TR.home = [5 * 16 + 8, 5, 3];
const P = () => G.P;
const B = [[10, 14], [17, 4], [24, 11], [31, 16], [38, 7], [45, 2], [52, 10]], tg = y => { for (const [r, c] of B) if (y < (r + 1) * 16 + 28) return c * 16 + 8; return 248; };
const glide = (bias) => i => {
  const p = P(); if (p.ground && p.y < 100) return p.x < 13 * 16 ? [['right'], []] : (i % 6 === 0 ? [['down', 'jump'], ['jump']] : [['down'], []]);
  const z = [0, tg(p.y)];
  const tx = z[1] + bias, d = tx - p.x;
  const h = Math.abs(d) < 3 ? [] : d > 0 ? ['right'] : ['left'];
  return [h.concat(p.vy > 0 || !p.ground ? ['jump'] : []), []];
};
let r = null;
for (let t = 0; t < 12 && !(r && r.ok); t++) r = TR.run([], () => false, { fn: glide((t % 5) * 3 - 6), max: 1400 });
TR.log.push('fall ' + JSON.stringify(S.SYS.result && { t: S.SYS.result.time, gold: S.SYS.result.gold }) + ' at ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' why ' + (r && r.why));
for (let i = 0; i < 240; i++) G.step(1);
TR.log.push('charm ' + G.SAVE.charms.includes('c_x3_scarab'));
await snap('du16_goal');
// back up the updraft
for (let i = 0; i < 40; i++) G.step(1, ['right']);
G.step(1, ['right', 'jump'], ['jump']); for (let i = 0; i < 900 && P().y > 70; i++) G.step(1, ['right']);
TR.log.push('updraft top y ' + (P().y / 16).toFixed(1) + ' x ' + (P().x / 16).toFixed(1));
for (let i = 0; i < 90; i++) G.step(1, ['left']);
TR.log.push('landing ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' ground ' + P().ground);
await snap('du16_back');
return TR.log;
