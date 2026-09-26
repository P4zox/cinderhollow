await boot();
const D = window.__db; D.SETTINGS.god = true;
G.give({ items: { hook: 1, talon: 1 } }); G.SAVE.flags['cut:choir'] = 1; G.SAVE.flags['cut:ferryman'] = 1; G.SAVE.seenAreas = { barrows: 1 };
const out = [];
// Choir: pin the player at each fog wall; sample the whole spine for terrain clipping / leaving the room
for (const [x, y] of [[2, 15], [53, 11], [27, 7]]) {
  G.tp('DB6', x, y); G.step(10);
  let bad = 0, maxOut = 0, n = 0;
  for (let i = 0; i < 900; i++) {
    G.step(2, x < 10 ? ['left'] : x > 50 ? ['right'] : []);
    const b = D.choir(); if (!b) break;
    for (const p of b.spine) { n++; if (D.solidAt(p.x, p.y)) bad++; if (p.x < 0 || p.y < 0 || p.x > 896 || p.y > 352) maxOut++; }
  }
  out.push(['choir pinned at', x, y, 'samples', n, 'in solid', bad, 'outside', maxOut, D.choir() && D.choir().bs]);
}
// Ferryman: pin at the fog wall and the jetty, check he stays on the lake
for (const [x, y] of [[43, 7], [8, 7]]) {
  G.tp('DB5', x, y); G.step(10);
  let minx = 1e9, maxx = -1e9, miny = 1e9;
  for (let i = 0; i < 900; i++) { G.step(2, x > 40 ? ['right'] : ['left']); const b = G.boss; if (!b) break; minx = Math.min(minx, b.x); maxx = Math.max(maxx, b.x); miny = Math.min(miny, b.y); }
  out.push(['ferryman pinned', x, 'x range', Math.round(minx), Math.round(maxx), 'min y', Math.round(miny), 'lake', 160, 640]);
}
return out;
