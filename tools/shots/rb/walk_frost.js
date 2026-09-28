await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1, hook: 1 } });
const W = window.__walker, t0 = performance.now();
const up1 = [{ x: 2, y: 43 }, { x: 9, y: 37 }, { x: 9, y: 31 }, { x: 6, y: 25 }], up2 = [{ x: 6, y: 19 }, { x: 2, y: 16 }, { x: 6, y: 13 }, { x: 2, y: 10 }, { x: 10, y: 7 }, { x: 24, y: 7 }, { x: 35, y: 4 }];   // the Falls' west stair
const route = ['HF16', 'HF10', 'HF8', ...up1, ...up2, 'HF11', 'HF14', 'HF11', 'HF15', 'HF11', 'HF12', 'HF11', 'HF12', 'HF9', 'HF12', 'HF9', 'HF13', 'HF9', 'HF8', 'HF9', 'HF8',
  ...up2, 'HF11', 'HF8', 'HF10', 'HF13', 'HF10', 'HF16', 'HF6'];
const r = W.route(['HF6', 8, 12], route, { budget: 1500, progress: 'progress_frost' });
r.log.push(`ok ${r.ok} total ${Math.round((performance.now() - t0) / 1000)} s`);
return r.log;
