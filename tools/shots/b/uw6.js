await boot();
const D = window.__db; G.give({ items: { tidebreath: 1 } }); G.SAVE.seenAreas = { barrows: 1 }; G.SAVE.flags['cut:choir'] = 1;
G.tp('DB2', 20, 13); G.step(40);
await snap('a');
return [G.P.x, G.P.y, D.cam.x, D.cam.y, G.P.state, G.P.anim.tag, G.P.anim.frame, D.DBS.inWater];
