// Spire wing walk: SP3 → … → SP13 → (roof) SP7 → LF1, with side trips, then back again. Only inputs; no teleports inside the wing.
await wlBoot();
G.SAVE.flags['boss:cindervane'] = 1;
const start = window.__START || ['SP3', 4, 25];
G.tp(start[0], start[1], start[2]); idle(30); wlWatch();
const fwd = { SP3: [['W', '22:25'], 'SP9'], SP9: [['W', '8:10'], 'SP10'], SP10: [['S', '2:4'], 'SP11'], SP11: [['N', '10:13'], 'SP12'],
  SP12: [['N', '10:13'], 'SP8'], SP8: [['E', '11:14'], 'SP14'], SP14: [async () => {
    await go([5, 14]);
    await wlSwingRun([{ from: [0, 7, 15], edge: 7, chain: [{ swing: 0 }, { swing: 1 }, { land: [25, 28, 13] }] },
                { from: [25, 28, 13], edge: 28, chain: [{ swing: 2 }, { swing: 3 }, { land: [47, 79, 14] }] }], 1, 'SP14');
    await go(['E', '10:13']);
  }, 'SP13'], SP13: [async () => { G.SAVE.playTime += 400; /* five minutes since Cindervane fell: the Last Field's crack opens */ await go(['S', '18:20']); }, 'SP7'], SP7: [['W', '13:15'], 'LF1'] };
let ok = await walkTo2(fwd, 'LF1');
// the Last Field and back through its crack, both ways
ok = ok && await walkTo2({ LF1: [['E', '13:15'], 'SP7'] }, 'SP7');
ok = ok && await walkTo2({ SP7: [['W', '13:15'], 'LF1'] }, 'LF1');
await snap('walk_sp_a');
return { ok, log: WL.log, crossings: WL.crossings, fails: WL.fails, dev: WL.dev.slice(0, 25), at: G.room + ' ' + wlCell() };
