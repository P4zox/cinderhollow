window.__ids = ["K9", "K10", "K11", "K12", "K13"];
// stand still 3 s on every standable floor spot of each new room (foes removed); any HP loss away from a visible hazard is a bug
await boot(); G.SETTINGS.god = false; G.SAVE.items.talon = 1; G.SAVE.items.wings = 1;
const ids = window.__ids;
const RB = window.__ra.rooms, SOL = new Set(['#', 'B', 'Y']), out = []; let total = 0;
for (const id of ids) {
  const d = RB[id], M = d.map, spots = [];
  for (let y = 1; y < d.h - 1; y++) for (let x = 1; x < d.w - 1; x++) {
    const c = M[y][x], up = M[y - 1][x], dn = M[y + 1][x];
    if (!SOL.has(c) && !SOL.has(up) && c !== '=' && up !== '=' && (SOL.has(dn) || dn === '=') && c !== '^' && c !== 'v') spots.push([x, y]);
  }
  const pick = spots;
  let bad = [];
  for (const [x, y] of pick) {
    G.tp(id, x, y); window.__ra.kill(); G.P.hp = G.D.maxHp; const hp0 = G.P.hp; let hurt = 0;
    G.step(2); window.__ra.kill(); G.P.hp = G.D.maxHp; G.step(178); if (G.state !== 'play') G.step(1, [], ['pause']); hurt = Math.max(0, hp0 - G.P.hp);
    let near = false;
    for (let yy = y - 2; yy <= y + 2; yy++) for (let xx = x - 2; xx <= x + 2; xx++) { const c = (M[yy] || '')[xx]; if (c === '^' || c === 'v') near = true; }
    if (id === 'R11' && y >= 16) near = true;   // the Perch's mist-drop is a visible hazard
    total++;
    if (hurt > 0 && !near) bad.push(`(${x},${y}) -${hurt} in ${G.room}`);
  }
  out.push(`${id}: ${pick.length} spots, ${bad.length ? 'PHANTOM ' + bad.slice(0, 6).join(' ') : 'clean'}`);
}
out.push('total spots ' + total);
return out;
