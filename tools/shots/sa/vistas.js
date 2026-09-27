await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.seenAreas = { thornveil: 1, barrows: 1, crimson: 1 };
const S = window.__sys;
for (const [r, x, y] of [['TV14', 12, 13], ['DB15', 32, 9], ['CM16', 9, 21], ['DB10', 51, 12], ['TV9', 56, 10]]) {
  G.tp(r, x, y); G.enemies.length = 0; G.step(240); await snap('v_' + r + '_walk');
  if (r !== 'DB10' && r !== 'TV9') { G.step(1, [], ['interact']); G.step(260); await snap('v_' + r + '_seated'); G.step(1, [], ['jump']); G.step(60); }
}
return 'ok';
