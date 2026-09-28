await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1 } });
const r = window.__walker.route(['M1', 10, 24], ['W3', 'M7'], { budget: 300 });
return r.log;
