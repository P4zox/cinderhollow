// smoke: a staggered regular foe + K
arena(); W().reset('longsword', 1);
const r = {};
r.types = E('Object.keys(MV.types).length');
E(`enemies = enemies.filter(e => !e.wmDummy); const e = makeEnemy('hollow_soldier', P.x + 26, P.y, 'fx_t1'); e.hp = e.maxHp = 5000; enemies.push(e); e.aggro = true; e.breakStance(); window.__t = e;`);
W().frame(2);
r.critable = E('__t.critable()');
r.ready = E('fatReady()');
W().tap('heavy', 2);
r.state = E('P.state'); r.on = E('!!FAT.on'); r.tag = E('P.anim.tag');
const snapsAt = [10, 30, 50, 70, 100];
for (let f = 0; f < 130; f++) { W().frame(1); if (snapsAt.includes(f)) { E('render()'); await snap('smoke_' + f); } }
r.after = E('P.state'); r.last = E('FAT.last'); r.thp = E('__t.hp'); r.tstate = E('__t.state'); r.upd = E('Object.prototype.hasOwnProperty.call(__t, "update")');
return r;
