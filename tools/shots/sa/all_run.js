const QR = [['TV9', 104, 27], ['TV9', 70, 27], ['TV9', 40, 18], ['TV9', 60, 10], ['TV10', 40, 9], ['TV11', 10, 10], ['TV12', 20, 15], ['TV13', 15, 12], ['TV14', 12, 13], ['TV15', 30, 12], ['TV16', 8, 12], ['TV13', 36, 12],
  ['DB11', 5, 10], ['DB11', 30, 7], ['DB12', 20, 12], ['DB10', 88, 9], ['DB10', 51, 12], ['DB10', 20, 9], ['DB10', 60, 30], ['DB13', 10, 18], ['DB17', 13, 2], ['DB14', 20, 4], ['DB15', 32, 9], ['DB16', 3, 9], ['DB16', 30, 13],
  ['CM12', 5, 15], ['CM12', 30, 8], ['CM10', 12, 31], ['CM10', 12, 15], ['CM13', 20, 14], ['CM9', 20, 6], ['CM9', 52, 14], ['CM9', 20, 22], ['CM16', 9, 21], ['CM11', 15, 9], ['CM15', 16, 9], ['CM14', 12, 16], ['CM17', 5, 12]];
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
