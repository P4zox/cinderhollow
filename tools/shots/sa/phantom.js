// SA: phantom damage — stand 3 s on every standable floor cell of every new room (enemies removed), log any HP loss
// that isn't next to a visible hazard (spikes, brambles, snares, pendulums, deep water without breath).
await boot(); G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.talon = 1;
G.SAVE.seenAreas = { thornveil: 1, barrows: 1, crimson: 1 };
const ROOMS_SA = ['TV9', 'TV10', 'TV11', 'TV12', 'TV13', 'TV14', 'TV15', 'TV16', 'W4', 'DB10', 'DB11', 'DB12', 'DB13', 'DB14', 'DB15', 'DB16', 'DB17',
  'CM9', 'CM10', 'CM11', 'CM12', 'CM13', 'CM14', 'CM15', 'CM16', 'CM17'];
const SOLID = new Set(['#', 'B', 'Y', ')']), HAZ = new Set(['^', 'v', '(', '*']);
const out = []; let total = 0, cells = 0;
for (const rid of ROOMS_SA) {
  G.tp(rid, 1, 1); G.step(2);
  const def = G.sa.room.def, M = def.map, H = def.h, Wd = def.w;
  const near = (x, y) => { for (let dy = -3; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { const r = M[y + dy]; if (r && HAZ.has(r[x + dx])) return true; } return false; };
  let bad = [];
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < Wd - 1; x++) {
    const c = M[y][x], up = M[y - 1][x], dn = M[y + 1][x];
    if (SOLID.has(c) || SOLID.has(up) || !(SOLID.has(dn) || dn === '=')) continue;
    if (c === '"' || up === '"' || near(x, y)) continue;
    cells++;
    G.tp(rid, x, y); G.SETTINGS.god = 0; G.P.hp = 99999; G.P.inv = 0;
    let hp0 = G.P.hp, hurt = 0;
    for (let f = 0; f < 18; f++) {
      for (const e of G.enemies) e.alive && e.die && e.die({ dir: 1 });
      G.step(10); if (G.state !== 'play') G.step(1, [], ['pause']);
    }
    hurt = hp0 - G.P.hp;
    const sa = G.sa.SA, px = G.P.x, py = G.P.y;
    const nearHaz = G.props.some(p => ((p.type === 'xsa_snare' || p.type === 'kit_pendulum') && Math.abs(p.x - px) < 90 && Math.abs(p.y - py) < 110) || (p.type === 'tv_pod' && Math.abs(p.x - px) < 60 && py > p.y && p.st !== 'idle'));
    if (hurt > 0 && !nearHaz) bad.push(`${x},${y} -${hurt} ${G.room}`);
  }
  total += bad.length; out.push(`${rid}: ${bad.length ? 'HURT at ' + bad.slice(0, 8).join(' | ') : 'clean'}`);
  G.SETTINGS.god = 1;
}
out.push(`cells tested ${cells}, hurt ${total}`);
return out;
