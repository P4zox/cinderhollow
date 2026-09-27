await boot(); G.SETTINGS.god = 1; for (const k of ['hook','emberdash','slam','wings']) delete G.SAVE.items[k]; G.SAVE.items.gale = 1; G.SAVE.items.talon = 1;
G.tp('SP16', 20, 20); G.step(30); const tr = [];
G.step(1, ['right', 'jump'], ['jump']);
for (let i = 0; i < 150; i++) { const r = G.step(1, ['right', 'jump'], []); if (i % 6 === 0) tr.push(`${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)}${G.P.state[0]}${Math.round(G.P.vy)}`); }
return [tr.join(' '), 'updrafts ' + G.xrc.room.updrafts.length];
