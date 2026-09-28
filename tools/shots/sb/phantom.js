// phantom-damage check: stand still 3 s on every standable floor cell (every other column) of each new room, no enemies
G.SETTINGS.god = 0; G.SAVE.flags['boss:executioners'] = 1;
const rooms = ['NV8','NV9','NV10','NV11','NV12','NV13','NV14','NV15','NV16','NV17','NV18','DU9','DU10','DU11','DU12','DU13','DU14','DU15','DU16','DU17','DU18','DU19'];
const out = [], bad = []; let spots = 0;
for (const id of rooms) {
  G.tp(id, 2, 2); for (let i = 0; i < 3; i++) { G.step(10); settle(); }
  const R = window.__sys.roomObj, def = R.def, W = R.w;
  const solid = t => t !== 0 && t !== 2 ? true : false;
  const cells = [];
  for (let y = 1; y < R.h - 1; y++) for (let x = 1; x < W - 1; x += 2) {
    const ch = def.map[y][x], below = def.map[y + 1][x];
    if (!'.xkbrS'.includes(ch) || !'.xkbrS'.includes(def.map[y - 1][x])) continue;
    if (!('#='.includes(below))) continue;
    cells.push([x, y]);
  }
  let hurtN = 0;
  for (const [x, y] of cells) {
    G.tp(id, x, y); G.enemies.length = 0; G.P.hp = G.D.maxHp; G.P.inv = 0;
    for (let i = 0; i < 6; i++) { G.step(30); G.enemies.length = 0; if (G.state !== 'play') settle(); }
    spots++;
    if (G.room !== id || G.P.hp < G.D.maxHp - 0.5) { hurtN++; bad.push(id + ' (' + x + ',' + y + ') hp ' + Math.round(G.P.hp) + '/' + G.D.maxHp + (G.room !== id ? ' moved to ' + G.room : '') + ' now at ' + (G.P.x / 16).toFixed(1) + ',' + (G.P.y / 16 - 1).toFixed(1)); }
  }
  out.push(id + ': ' + cells.length + ' spots, ' + hurtN + ' with damage');
}
return { spots, out, bad: bad.slice(0, 80) };
