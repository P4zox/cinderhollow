await boot(); G.SETTINGS.god = true; G.give({ items: { talon: 1, hook: 1, emberdash: 1 } });
const RB = window.__rb; G.tp('M8', 20, 8); G.step(5);
const t0 = performance.now(); RB.sim(3000, ['right']); const t1 = performance.now();
G.tp('A8', 44, 44); G.step(5); const t2 = performance.now(); RB.sim(3000, ['left']); const t3 = performance.now();
return [(t1 - t0) / 3000, (t3 - t2) / 3000];
