// Phantom-damage check: stand still for 3 s on every standable cell of every RB room (foes removed); any HP loss that
// isn't explained by a visible hazard at that spot is reported.
await boot(); G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1, catacombs: 1, cathedral: 1 };
G.give({ items: { talon: 1, hook: 1, emberdash: 1 } });
const RB = window.__rb, out = [], rooms = (window.__rooms || 'W3,M7,M8,M9,M10,M11,M12,M13,M14,W5,A8,A9,A10,A11,A12,A13,A14,A15,A16,HF8,HF9,HF10,HF11,HF12,HF13,HF14,HF15,HF16').split(',');
let spots = 0, bad = [], hazardHits = 0;
for (const id of rooms) {
  const D = RB.ROOM_BY[id], M = D.map, W = D.w, H = D.h;
  const solid = ch => '#_B{}?)Y$&12'.includes(ch) && ch !== '', open = ch => !solid(ch);
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    const ch = M[y][x], below = M[y + 1][x], up = M[y - 1][x];
    if (!open(ch) || !open(up) || !(solid(below) || below === '=')) continue;
    if ('~:9"^v*%|'.includes(ch) || '~:9"'.includes(up)) continue;       // standing in a visible hazard / water
    spots++;
    G.tp(id, x, y); RB.clearFoes();
    const P = G.P; G.SETTINGS.god = false; P.hp = 9999; P.inv = 0; const hp0 = P.hp;
    let lost = 0, why = '';
    for (let f = 0; f < 180; f++) { RB.sim(1); RB.clearFoes(); if (P.hp < hp0 - 0.5 && !why) { why = `f${f}`; } if (G.room !== id) { why = 'left room'; break; } }
    lost = hp0 - P.hp;
    if (lost > 0.5 || why === 'left room') {
      // visible hazards near the spot: icicles above, pendulums in the room, spikes around, water under
      const near = [];
      for (let yy = 0; yy < y; yy++) if (M[yy][x] === ',') near.push('icicle');
      if ((D.spawns || []).some(s => s.t === 'xrb_icicle' && Math.abs(s.x - x) <= 1)) near.push('icicle');
      if ((D.spawns || []).some(s => s.kind === 'pendulum' && Math.abs(s.x - x) <= (s.len || 4) + 1)) near.push('blade');
      for (const [dx, dy] of [[0, 0], [-1, 0], [1, 0], [0, 1], [0, -1]]) { const c = M[y + dy] && M[y + dy][x + dx]; if (c && '^v*9~:"'.includes(c)) near.push('tile ' + c); }
      if (near.length) hazardHits++; else bad.push(`${id} (${x},${y}) lost ${Math.round(lost)} ${why}`);
    }
  }
}
G.SETTINGS.god = true;
out.push(`spots ${spots}, damage from visible hazards at ${hazardHits}, phantom ${bad.length}`);
out.push(...bad.slice(0, 40));
return out;
