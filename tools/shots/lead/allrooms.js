await boot(); G.grantTechniques(); G.giveArmory(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1; G.SETTINGS.god = 1;
const spots = SPOTS; const bad = []; let n = 0;
const acts = ['left', 'right', 'jump', 'attack', 'heavy', 'roll', 'up', 'down', 'cast', 'art', 'interact'];
for (const [id, x, y] of spots) {
  try {
    G.tp(id, x, y); n++;
    for (let k = 0; k < 40; k++) { const h = [acts[(k * 7) % 3]], t = Math.random() < 0.3 ? [acts[Math.floor(Math.random() * acts.length)]] : []; G.step(3, h, t); if (G.state !== 'play') G.step(1, [], ['pause']); if (G.state === 'menu') G.step(1, [], ['pause']); }
  } catch (e) { bad.push(id + ': ' + String(e).slice(0, 160)); }
}
return { visited: n, bad };
