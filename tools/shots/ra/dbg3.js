await boot();
G.SETTINGS.god = true; W.noFoes = true; G.SAVE.items.talon = 1;
G.tp('K9', 48, 7); for (let i = 0; i < 20; i++) st1([], []); W.last = G.room;
W.trace = []; const ok = await route([['K9', 40, 9], ['K9', 34, 8]]);
return [ok, W.fail, W.log.join(','), ...W.trace.slice(0, 120).filter((_, i) => i % 3 == 0)];
