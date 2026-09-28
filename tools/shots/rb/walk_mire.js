await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1 } });
const W = window.__walker, t0 = performance.now();
const INT = () => [{ k: 'INT' }, { k: 'WAIT', n: 240 }];
const route = ['W3', 'M7', 'M8', 'M13', 'M8', 'M10', 'M14', 'M10', 'M11', 'M12', 'M9', 'M1', 'M9', 'M12', 'M11', 'M9', 'M11', 'M10', 'M8', 'M7', 'W3', 'M1'];
const r = W.route(['M1', 10, 24], route, { budget: 500, extra: { M9: INT, M12: INT } });
r.log.push(`ok ${r.ok} total ${Math.round((performance.now() - t0) / 1000)} s`);
window.__plan = r.plan;
return r.log;
