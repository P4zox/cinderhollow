await boot();
G.give({ items: { emberdash: 1 } }); G.SAVE.flags['boss:butler'] = 1; G.SAVE.flags['cut:sanguine'] = 1;
const spots = [['CM1', 5, 10], ['CM1', 25, 8], ['CM2', 6, 36], ['CM2', 18, 26], ['CM2', 18, 13], ['CM3', 12, 9], ['CM6', 12, 9], ['CM4', 14, 10], ['CM4', 36, 10], ['CM8', 5, 10], ['CM7', 14, 14], ['CM5', 14, 7], ['CM5', 40, 7]];
let i = 0;
for (const [id, tx, ty] of spots) { G.tp(id, tx, ty); G.step(90); await snap('r' + String(i++).padStart(2, '0') + '_' + id); }
return i;
