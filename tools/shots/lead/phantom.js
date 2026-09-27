await boot(); G.grantTechniques(); G.giveArmory(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1; G.SETTINGS.god = 0;
const spots = SPOTS, found = [];
const order = [...spots, ...spots.slice().reverse()];
let prev = '';
for (const [id, pts] of order) {
  for (const [x, y] of pts) {
    try { G.tp(id, x, y); } catch (e) { found.push(`${id} tp fail ${e}`); continue; }
    for (const e of G.enemies) { e.alive = false; e.gone = true; } G.enemies.length = 0;
    G.P.hp = 99999; G.P.inv = 0; let lost = 0;
    for (let f = 0; f < 150; f++) { const h0 = G.P.hp; G.step(1); for (const e of G.enemies) { e.alive = false; } G.enemies.length = 0; if (G.P.hp < h0) lost += h0 - G.P.hp; if (G.state !== 'play') G.step(1, [], ['pause']); }
    if (lost > 0) found.push(`${prev} -> ${id} @${x},${y}: lost ${Math.round(lost)} at p=${Math.round(G.P.x)},${Math.round(G.P.y)} room=${G.room}`);
  }
  prev = id;
}
return found;
