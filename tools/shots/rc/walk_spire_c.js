// Spire wing walk C (talon + Gale Cloak): SP3 → … → SP14 ↔ SP17 (Crow's Nest) → SP13 ↔ SP16 (Gale Trial). Inputs only.
await wlBoot();   // the Gale Cloak is handed over in Kite Lines (the way there is talon-only; gliding would change those routes)
G.SAVE.flags['boss:cindervane'] = 1;
G.tp('SP3', 4, 25); idle(30); wlWatch();
const SWF = [{ from: [0, 7, 15], edge: 7, chain: [{ swing: 0 }, { swing: 1 }, { land: [25, 28, 13] }] },
             { from: [25, 28, 13], edge: 28, chain: [{ swing: 2 }, { swing: 3 }, { land: [47, 79, 14] }] }];
const TG = 'talon,gale';
const fwd = { SP3: [['W', '22:25'], 'SP9'], SP9: [['W', '8:10'], 'SP10'], SP10: [['S', '2:4'], 'SP11'], SP11: [['N', '10:13'], 'SP12'],
  SP12: [['N', '10:13'], 'SP8'], SP8: [['E', '11:14'], 'SP14'] };
let ok = await walkTo2(fwd, 'SP14');
await go([5, 14]); await wlSwingRun(SWF, 1, 'SP14'); G.SAVE.items.gale = 1;
ok = ok && await walkTo2({ SP14: [['N', '55:57'], 'SP17', TG] }, 'SP17');
ok = ok && await go([17, 2], 'talon,gale') && (WL.log.push('  SP17 nest shelf reached'), true);
ok = ok && await walkTo2({ SP17: [['S', '7:9'], 'SP14', 'talon,gale'] }, 'SP14');
ok = ok && await walkTo2({ SP14: [['E', '10:13'], 'SP13', 'talon,gale'] }, 'SP13');
// the Crumbling Stair is a talon room: climb it without the cloak (a held jump would glide where the plan clings), put it on for the trial
delete G.SAVE.items.gale;
ok = ok && await walkTo2({ SP13: [['N', '2:4'], 'SP16'] }, 'SP16');
ok = ok && await go([2, 33]) && (WL.log.push('  SP16 sigil ledge reached'), true);
ok = ok && await walkTo2({ SP16: [['S', '5:7'], 'SP13'] }, 'SP13');
G.SAVE.items.gale = 1;
await snap('walk_sp_c');
return { ok, log: WL.log, crossings: WL.crossings, fails: WL.fails, dev: WL.dev.slice(0, 25), at: G.room + ' ' + wlCell() };
