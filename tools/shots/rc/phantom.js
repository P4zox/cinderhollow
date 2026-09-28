// phantom-damage check: stand still 3 s on every floor spot the checker can reach in the RC rooms, enemies removed, no god mode.
// Reports every spot that cost health (with where the body ended up), for a look at whether a visible hazard did it.
await wlBoot(); G.SAVE.flags['boss:cindervane'] = 1; G.SAVE.flags['boss:sovereign'] = 1;
const SPOTS = window.__SPOTS, hits = [], counts = {};
for (const [room, pts] of Object.entries(SPOTS)) {
  counts[room] = 0;
  for (const [x, y] of pts) {
    G.SETTINGS.god = 1; G.tp(room, x, y); WL.last = G.room; idle(4);
    G.SETTINGS.god = 0; G.P.hp = 99; G.P.inv = 0; const hp0 = G.P.hp;
    let lost = 0, at = null;
    for (let i = 0; i < 180; i++) { st1(0, false, false, false); if (G.P.hp < hp0 && !at) at = [i, (G.P.x / 16).toFixed(1), (G.P.y / 16).toFixed(1), G.P.state]; }
    lost = hp0 - G.P.hp; counts[room]++;
    if (lost > 0 || G.room !== room) hits.push({ room, x, y, lost, at, end: [G.room, (G.P.x / 16).toFixed(1), (G.P.y / 16).toFixed(1)] });
  }
}
return { counts, hits };
