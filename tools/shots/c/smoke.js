await boot();
const out = {};
for (const [id, tx, ty] of [['CM1', 20, 8], ['CM2', 5, 36], ['CM3', 6, 9], ['CM6', 3, 9], ['CM4', 20, 10], ['CM8', 3, 10], ['CM7', 4, 14], ['CM5', 3, 7]]) {
  G.tp(id, tx, ty); G.step(40);
  out[id] = { room: G.room, p: [Math.round(G.P.x), Math.round(G.P.y)], en: G.enemies.length, boss: G.boss && G.boss.kind };
  await snap('room_' + id);
}
return out;
