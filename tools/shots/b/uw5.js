await boot();
const D = window.__db; G.give({ items: { tidebreath: 1 } }); G.SAVE.seenAreas = { barrows: 1 }; G.SAVE.flags['cut:choir'] = 1;
G.tp('DB6', 10, 17); G.step(30); D.DBS.breath = 0.5; G.step(90);
await snap('vis_deep_drowning');
G.tp('DB2', 20, 13); G.step(20); await snap('vis_db2');
return 'ok';
