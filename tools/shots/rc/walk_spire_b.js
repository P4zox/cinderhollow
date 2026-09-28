// Spire wing walk B (talon only): SP3 → … → SP8 ↔ SP15 → SP14 → SP13, then all the way back west to SP3. Inputs only.
await wlBoot();
G.SAVE.flags['boss:cindervane'] = 1;
G.tp('SP3', 4, 25); idle(30); wlWatch();
const SWF = [{ from: [0, 7, 15], edge: 7, chain: [{ swing: 0 }, { swing: 1 }, { land: [25, 28, 13] }] },
             { from: [25, 28, 13], edge: 28, chain: [{ swing: 2 }, { swing: 3 }, { land: [47, 79, 14] }] }];
const SWB = [{ from: [47, 79, 14], edge: 47, chain: [{ swing: 3 }, { swing: 2 }, { land: [25, 28, 13] }] },
             { from: [25, 28, 13], edge: 25, chain: [{ swing: 1 }, { swing: 0 }, { land: [0, 7, 15] }] }];
const fwd = { SP3: [['W', '22:25'], 'SP9'], SP9: [['W', '8:10'], 'SP10'], SP10: [['S', '2:4'], 'SP11'], SP11: [['N', '10:13'], 'SP12'],
  SP12: [['N', '10:13'], 'SP8'] };
let ok = await walkTo2(fwd, 'SP8');
ok = ok && await walkTo2({ SP8: [['N', '1:30'], 'SP15'] }, 'SP15');
ok = ok && await walkTo2({ SP15: [['S', '1:30'], 'SP8'] }, 'SP8');
ok = ok && await walkTo2({ SP8: [['E', '11:14'], 'SP14'], SP14: [async () => { await go([5, 14]); await wlSwingRun(SWF, 1, 'SP14'); await go(['E', '10:13']); }, 'SP13'] }, 'SP13');
const back = { SP13: [['W', '29:32'], 'SP14'], SP14: [async () => { await go([60, 13]); await wlSwingRun(SWB, -1, 'SP14'); await go(['W', '11:14']); }, 'SP8'],
  SP8: [['S', '10:13'], 'SP12'], SP12: [['S', '10:13'], 'SP11'], SP11: [['N', '34:36'], 'SP10'], SP10: [['E', '8:10'], 'SP9'], SP9: [['E', '7:10'], 'SP3'] };
ok = ok && await walkTo2(back, 'SP3');
await snap('walk_sp_b');
return { ok, log: WL.log, crossings: WL.crossings, fails: WL.fails, dev: WL.dev.slice(0, 25), at: G.room + ' ' + wlCell() };
