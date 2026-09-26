// difficulty probe: boss damage/minute against a standing dummy and a roll-on-telegraph bot, per phase
await boot(); G.give({ stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10, arc: 8 }, level: 40 });
G.SAVE.flags['sc:seal'] = 1;
const CASES = (window.__CASES || (window.__ONLY && [['M5','kalden',6,10]]) || [['C5','hound',6,10],['M5','kalden',6,10],['K4','omen',6,10]]);
const SECS = window.__SECS || 60, REP = window.__REP || 1;
const out = {};
const seen = new WeakSet();
function run(k, r, tx, ty, mode, phase) {
  delete G.SAVE.flags['boss:' + k]; G.SAVE.flags['cut:' + k] = 1; G.SAVE.flags['cutp2:' + k] = 1;
  G.tp(r, tx, ty); G.P.hp = 99999; G.P.rot = 0; G.P.rotT = 0;
  const b = G.boss; if (!b) return 'NO BOSS';
  for (let i = 0; i < 300 && !b.active; i++) { const d = b.x < G.P.x ? 'left' : 'right'; G.step(2, Math.abs(b.x - G.P.x) > 80 ? [d] : []); G.P.hp = 99999; if (G.state === 'cut') G.step(1, [], ['pause']); }
  if (!b.active) return 'never active';
  for (let i = 0; i < 200 && (b.introT > 0 || b.state === 'intro'); i++) { G.step(2); G.P.hp = 99999; }
  if (phase === 2) {
    b.hp = Math.round(b.maxHp * 0.45);
    for (let i = 0; i < 600 && b.phase !== 2; i++) { G.step(2); G.P.hp = 99999; }
    for (let i = 0; i < 200 && (G.state === 'cut' || G.state === 'cine'); i++) G.step(1, [], ['pause']);
    for (let i = 0; i < 60; i++) { G.step(2); G.P.hp = 99999; if (G.state === 'cut') G.step(1, [], ['pause']); }
  }
  for (const f of window.__kd.fx) seen.add(f);
  const lo = phase === 1 ? b.maxHp * 0.6 : b.maxHp * 0.12, hi = phase === 1 ? b.maxHp : b.maxHp * 0.45;
  const tally = {}; let dot = 0, taken = 0, hits = 0, dealt = 0, rollAt = -1, t = 0, rolls = 0, rotProcs = 0, prevRotT = 0;
  const N = SECS * 30;
  for (let i = 0; i < N; i++) {
    t += 2 / 60;
    let hold = [], tap = [];
    if (mode === 'bot') {
      for (const f of window.__kd.fx) if (!seen.has(f)) { seen.add(f); if (f.name === 'telegraph' && Math.abs(b.x - G.P.x) < 220 && rollAt < 0) rollAt = t + 0.2; }
      const d = Math.abs(b.x - G.P.x), away = b.x < G.P.x ? 'right' : 'left', to = b.x < G.P.x ? 'left' : 'right';
      if (rollAt >= 0 && t >= rollAt) { tap = ['roll']; hold = [away]; rollAt = -1; rolls++; }
      else if (d > 46) hold = [to];
      else if (b.state !== 'attack' || b.state === 'stagger') { if (G.P.st > 25) tap = ['attack']; }
    } else { for (const f of window.__kd.fx) seen.add(f); }
    const hp0 = G.P.hp, bh0 = b.hp;
    G.step(2, hold, tap);
    if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']);
    if (G.P.hp < hp0) { const src = G.P.inv > 0.45 ? (b.state === 'attack' ? b.atk : 'hz:' + b.state) : 'dot'; tally[src] = (tally[src] || 0) + hp0 - G.P.hp; taken += hp0 - G.P.hp; if (G.P.inv > 0.45) hits++; else dot += hp0 - G.P.hp; }
    if (b.hp < bh0) dealt += bh0 - b.hp;
    if (G.P.rotT > 0 && prevRotT <= 0) rotProcs++; prevRotT = G.P.rotT;
    if (G.P.state === 'dead' || G.P.hp < 5000) { G.P.hp = 99999; }
    if (G.P.hp > 99999) G.P.hp = 99999;
    if (b.hp < lo) b.hp = hi; if (!b.alive) return 'boss died';
  }
  return { dotPm: Math.round(dot / SECS * 60), dpm: Math.round(taken / SECS * 60), hitsPm: +(hits / SECS * 60).toFixed(1), myDpm: Math.round(dealt / SECS * 60), rollsPm: +(rolls / SECS * 60).toFixed(1), rotProcs, maxHp: b.maxHp, tally: Object.entries(tally).sort((a, b) => b[1] - a[1]).map(([k, v]) => k + ':' + Math.round(v)).join(' ') };
}
for (const [r, k, tx, ty] of CASES) {
  for (const mode of ['dummy', 'bot']) for (const ph of [1, 2]) {
    const res = [];
    for (let rep = 0; rep < REP; rep++) { try { res.push(run(k, r, tx, ty, mode, ph)); } catch (e) { res.push('EXC ' + e.message + ' ' + e.stack.split('\n')[1]); } }
    out[`${k}.${mode}.p${ph}`] = JSON.stringify(res.length === 1 ? res[0] : res);
  }
}
out.maxHpPlayer = G.D.maxHp;
return out;
