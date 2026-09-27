window.__TV = [["X7",36,44,"c_X7a"],["X7",36,8,"c_X7b"],["X7",20,23,"c_X7c"],["X9",20,16,"c_X9"],["X6",20,11,"c_X6"],["X10",30,11,"c_X10"],["X8",10,22,"c_X8"],["SP14",20,12,"c_SP14"]];
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.talon = 1;
G.SAVE.seenAreas = { spire: 1, deep: 1, crown: 1, lastfield: 1 };
const V = window.__TV; const log = [];
for (const [id, x, y, n] of V) { G.tp(id, x, y); G.step(250); await snap(n); log.push(n); }
return log;
