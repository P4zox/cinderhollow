// v17 FOES: every Cold Forge room with AREA's placements: the foes are there, wake, act; no page errors. God mode on.
// SHOT_HTML=$PWD/web/dist/v17_foes.html sh tools/shots/wm/run.sh tools/shots/v17/foes/rooms.js tools/shots/v17/foes/out_rooms
E(`SETTINGS.god = true`);
const ids = E(`ROOMS.filter(r => r.biome === 'forge').map(r => r.id)`);
const res = {};
for (const id of ids) {
  const sp = E(`(ROOM_BY['${id}'].spawns || []).filter(s => s.t === 'enemy' || s.t === 'cf_swarm' || s.t === 'cf_foe').map(s => [s.t === 'enemy' ? s.type : s.t, s.x, s.y])`);
  if (!sp.length) { res[id] = 'no foes'; continue; }
  G.tp(id, sp[0][1] - 6 > 1 ? sp[0][1] - 6 : sp[0][1] + 6, sp[0][2]); W().frame(10);
  E(`P.x = clamp(enemies.length ? enemies[0].x - 70 : P.x, 24, room.pw - 24); P.vx = 0`);
  await new Promise(r => setTimeout(r, 300));
  const states = {};
  for (let f = 0; f < 360; f++) { W().frame(1); if (f % 60 === 0) for (const s of E(`enemies.filter(e => e.type.startsWith('cf_')).map(e => e.type + ':' + e.state)`)) states[s] = 1; if (f === 200) { E('hitstop = 0; areaCard = null; bannerMsg = null; regionCard = null; toasts.length = 0; render()'); await snap(`room_${id}`); } }
  res[id] = { placed: sp.map(s => s[0]).join(','), live: E(`enemies.map(e => e.type + (e.wt ? '/' + e.wt : '')).join(',')`), states: Object.keys(states).join(' ') };
}
return res;
