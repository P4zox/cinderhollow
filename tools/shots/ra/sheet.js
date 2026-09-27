// full-room renders: window.__ids = [[room, tx, ty], ...] (the player stands there; lights come from the last update)
await boot(); G.grantTechniques(); G.SAVE.items.wings = 1;
const L = window.__ids || [];
for (const [r, x, y, hideP] of L) { G.tp(r, x, y); G.P.hp = 99999; G.step(40); if (G.state !== 'play') G.step(1, [], ['pause']); if (hideP) { G.P.x = -999; } G.step(1); await window.__save('sheet_' + r, window.__ra.sheet()); }
return 'ok';
