G.tp('SF18', 28, 3); G.step(20);
TRACE = { n: 0, out: [], every: 4 };
until(() => !G.P.ground, ['right'], 60); G.step(1, ['right'], ['roll']); until(() => G.P.ground, ['right'], 120); walkTo(44.8, 0.2);
for (let i = 0; i < 8 && G.room === 'SF18'; i++) { G.step(1, ['right'], ['attack']); G.step(14, ['right']); }
const t = TRACE.out; TRACE = null; return [...LOG, ...t.slice(-12), ...ROOMLOG];
