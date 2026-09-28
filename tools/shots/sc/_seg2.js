G.tp('NH12', 19, 18); G.step(20); walkTo(20.7, 0.1);
const o = K('bb3'); waitSolid('bb3', 0.15, 600, 1.4); const t0 = G.xs.KIT.t;
TRACE = { n: 0, out: [], every: 3 }; leap(25, 15, { jumps: 1 }); const tr = TRACE.out; TRACE = null;
return [...LOG, `bb3 d ${o.d.x0/16},${o.d.y0/16} w ${o.w/16} solid ${o.solidNow} t0 ${t0.toFixed(2)} now ${G.xs.KIT.t.toFixed(2)}`, ...tr.slice(0, 40)];
