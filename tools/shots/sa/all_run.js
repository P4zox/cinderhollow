const QR = [['TV9', 104, 27], ['TV9', 70, 27], ['TV9', 40, 18], ['TV9', 60, 10], ['TV9', 20, 27], ['TV10', 40, 11], ['TV11', 30, 11], ['TV12', 20, 15], ['TV13', 15, 11], ['TV14', 14, 13], ['TV15', 30, 12], ['TV16', 8, 11],
  ['W4', 3, 50], ['W4', 5, 5], ['DB11', 5, 10], ['DB11', 30, 7], ['DB12', 20, 9], ['DB10', 72, 10], ['DB10', 41, 13], ['DB10', 20, 10], ['DB10', 60, 30], ['DB13', 10, 18], ['DB17', 13, 3], ['DB14', 20, 4], ['DB15', 8, 10], ['DB16', 3, 9], ['DB16', 30, 13],
  ['CM12', 10, 13], ['CM12', 35, 9], ['CM10', 10, 29], ['CM10', 12, 11], ['CM13', 20, 15], ['CM9', 20, 7], ['CM9', 52, 16], ['CM9', 20, 26], ['CM16', 10, 16], ['CM11', 20, 11], ['CM15', 20, 11], ['CM14', 12, 15], ['CM17', 5, 11],
  ['TV2', 9, 10], ['TV5', 11, 23], ['DB3', 18, 9], ['DB4', 16, 11], ['CM4', 49, 10], ['CM8', 6, 10]];
// SA: screenshots of rooms. QR = [[room, tx, ty, name?], ...] (set by a prelude line), else the defaults below.
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.talon = 1;
G.SAVE.seenAreas = G.SAVE.seenAreas || {}; for (const k of ['thornveil', 'barrows', 'crimson', 'catacombs', 'ramparts']) G.SAVE.seenAreas[k] = 1;
G.step(260);
const list = (typeof QR !== 'undefined') ? QR : [['TV9', 100, 27], ['TV9', 70, 27], ['TV9', 40, 27], ['TV9', 20, 18], ['TV9', 60, 10], ['TV10', 40, 9], ['TV11', 10, 10], ['TV12', 8, 15], ['TV12', 40, 10], ['TV13', 15, 12], ['TV14', 12, 13], ['TV15', 4, 10], ['TV15', 40, 8], ['TV16', 8, 12]];
const out = [];
for (const [r, x, y, nm] of list) {
  try { G.tp(r, x, y); G.enemies.length = 0; for (let i = 0; i < 4; i++) { G.step(60); if (G.state !== 'play') G.step(1, [], ['pause']); } G.P.hp = 99999;
    await snap((nm || r + '_' + x + '_' + y)); out.push(r + ' ok'); } catch (e) { out.push(r + ' ' + e.message); }
}
return out;
