await boot(); G.SETTINGS.god = 0; G.SAVE.seenAreas = G.SAVE.seenAreas || {}; for (const k of ['necropolis','dunes','catacombs','ramparts','nv_void']) G.SAVE.seenAreas[k] = 1;
G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.talon = 1; G.SAVE.hints = G.SAVE.hints || {};
const settle = () => { for (let i = 0; i < 12 && G.state !== 'play'; i++) G.step(1, [], ['pause']); };
const shot = async (r, x, y, name, opt = {}) => { G.tp(r, x, y); if (opt.noenemy) G.enemies.length = 0; for (let i = 0; i < 8; i++) { G.step(30); G.P.hp = 99999; settle(); } if (opt.fn) opt.fn(); G.step(opt.wait || 1); await snap(name || (r + '_' + x + '_' + y)); };
