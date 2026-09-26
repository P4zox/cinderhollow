await boot();
const D = window.__db; G.give({ items: { tidebreath: 1 } }); G.SAVE.seenAreas = { barrows: 1 };
G.tp('DB2', 20, 13); G.step(40);
const shots = [];
for (const tag of ['tread', 'swim', 'idle', 'glide']) { G.P.anim.set(tag, true); G.P.anim.update(0); window.__game.step(0); await snap('t_' + tag); shots.push([tag, G.P.anim.frame]); }
G.tp('DB2', 32, 9); G.step(10); await snap('t_land');
return shots;
