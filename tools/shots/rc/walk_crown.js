// Crown wing walk (talon; after the Sovereign): X5 → X6 → X10 → X7 ↔ X11 → X9 → X8 → X12 and back, every link both ways.
await wlBoot();
G.SAVE.flags['boss:sovereign'] = 1;
G.tp('X5', 40, 12); idle(30); wlWatch();
const legs = [
  ['X6', { X5: [['E', '7:10'], 'X6'] }], ['X10', { X6: [['N', '20:22'], 'X10'] }], ['X7', { X10: [['E', '7:10'], 'X7'] }],
  ['X11', { X7: [['W', '11:14'], 'X11'] }], ['X7', { X11: [['E', '16:19'], 'X7'] }], ['X9', { X7: [['E', '8:11'], 'X9'] }],
  ['X8', { X9: [['S', '10:13'], 'X8'] }], ['X12', { X8: [['E', '25:28'], 'X12'] }], ['X8', { X12: [['W', '25:28'], 'X8'] }],
  ['X9', { X8: [['N', '10:13'], 'X9'] }], ['X7', { X9: [['W', '13:16'], 'X7'] }], ['X10', { X7: [['W', '26:29'], 'X10'] }],
  ['X6', { X10: [['S', '20:22'], 'X6'] }], ['X7', { X6: [['E', '8:11'], 'X7'] }], ['X8', { X7: [['E', '41:44'], 'X8'] }],
  ['X7', { X8: [['W', '25:28'], 'X7'] }], ['X6', { X7: [['W', '41:44'], 'X6'] }], ['X5', { X6: [['W', '7:10'], 'X5'] }]];
let ok = true;
for (const [to, map] of legs) { if (!ok) break; ok = await walkTo2(map, to); }
await snap('walk_cr');
return { ok, log: WL.log, crossings: WL.crossings, fails: WL.fails, dev: WL.dev.slice(0, 25), at: G.room + ' ' + wlCell() };
