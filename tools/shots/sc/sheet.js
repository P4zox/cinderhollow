// full-room renders of every SC room (player parked at a floor cell, foes cleared) -> out/sheet_<ROOM>.png
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { moonstep: 1, wings: 1, talon: 1 });
for (const f of ['boss:astrel', 'boss:first_ember', 'boss:oswin', 'sc:seal', 'sf:stair']) G.SAVE.flags[f] = 1;
const out = [];
for (const [r, x, y] of SPOTS) {
  G.tp(r, x, y); G.step(60); if (G.state !== 'play') G.step(1, [], ['pause']);
  G.enemies.length = 0; G.xs.clean(); G.step(2);
  await window.__save('sheet_' + r, G.xs.sheet()); out.push(r);
}
return out;
