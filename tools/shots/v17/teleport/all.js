// Cheats › Teleport: every group lists rooms; teleporting into each room lands safely (alive, on the ground, not in a wall).
// SHOT_HTML=web/dist/tp.html node tools/shots/shot.js tools/shots/v17/teleport/all.js <out>
await boot(); const E = G.sk.ev; G.SETTINGS.god = 0;
const groups = E(`__game.tp_groups().map(g => [g.name, g.rooms.length])`);
const ids = E(`[...new Set(__game.tp_groups().flatMap(g => g.rooms.map(d => d.id)))]`);
const bad = [];
for (const id of ids) {
  const r = E(`(() => { try { __game.tp_go('${id}'); for (let i = 0; i < 60; i++) { update(1 / 60); if (state === 'cut' || state === 'dialog' || state === 'menu') { menu = null; dialog = null; state = 'play'; } } P.hp = D.maxHp;
    const tx = Math.floor(P.x / TILE), ty = Math.floor((P.y - 8) / TILE);
    return { room: room.id, dead: P.state === 'dead', inWall: isSolidT(tileAt(tx, ty)), ground: !!P.ground, y: Math.round(P.y), ph: room.ph }; } catch (e) { return { err: String(e) }; } })()`);
  if (r.err || r.room !== id || r.dead || r.inWall || r.y > r.ph + 8) bad.push([id, r]);
}
// open the menu once for a screenshot
E(`menu = { tab: 'settings' }; state = 'menu';`);
return { groups, rooms: ids.length, bad, cheated: E('SAVE.cheated') };
