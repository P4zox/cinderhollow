// SA: gauntlets, vistas, the portrait riddle, the three keys, the Drowned Bell, the Witch's Larder, the tide, snares.
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.talon = 1;
G.SAVE.seenAreas = { thornveil: 1, barrows: 1, crimson: 1 };
const S = window.__sys, A = G.sa, log = [];
const gauntlet = async (r, x, y, id, pre) => {
  G.tp(r, x, y); G.step(60); G.step(1, [], ['interact']); G.step(30);
  log.push(`${r} gauntlet started ${!!S.SYS.gaunt}`);
  for (let w = 0; w < 6 && S.SYS.gaunt; w++) {
    for (let i = 0; i < 200 && S.SYS.gaunt && S.SYS.gaunt.state !== 'wave'; i++) G.step(1);
    for (let i = 0; i < 90; i++) G.step(1);
    if (w === 0 || w === 3) await snap(pre + '_wave' + (w + 1));
    const alive = G.enemies.filter(e => e.alive && e.x3g); log.push(`  wave ${w + 1}: ${alive.map(e => e.type).join(',')}`);
    for (const e of alive) e.die({ dir: 1 });
    for (let i = 0; i < 90; i++) G.step(1);
  }
  for (let i = 0; i < 300; i++) G.step(1);
  log.push(`  cleared flag ${G.SAVE.flags['x3:' + r + ':' + id]} running ${!!S.SYS.gaunt} ember ${G.SAVE.inv.emberstone || 0} cinders ${G.SAVE.cinders}`);
};
await gauntlet('TV13', 15, 11, 'coven', 'coven');
await gauntlet('CM15', 20, 11, 'quarters', 'quarters');
// vistas
for (const [r, x, y] of [['TV14', 14, 13], ['DB15', 8, 10], ['CM16', 10, 16]]) {
  G.tp(r, x, y); G.step(120); G.step(1, [], ['interact']); G.step(200); await snap('vista_' + r);
  log.push(`${r} seated ${!!S.SYS.vista} enemies ${G.enemies.length}`); G.step(1, [], ['jump']); G.step(60);
}
log.push('vistas ' + JSON.stringify(Object.keys(S.x3().vistas)));
// the portrait riddle: a wrong order three times (hint), then the right one
G.tp('CM13', 20, 15); G.step(60);
const hit = id => { A.KIT.byId[id].onHit({ kind: 'test', dir: 1 }); G.step(20); };
for (let k = 0; k < 3; k++) { hit('f1'); G.step(40); }
for (const f of ['f4', 'f2', 'f6', 'f1', 'f5']) hit(f);
G.step(120); log.push('riddle solved ' + A.kitOn('gaze') + ' gate ' + A.kitOn('gK'));
await snap('riddle_solved');
G.tp('CM13', 34, 7); for (let i = 0; i < 40; i++) G.step(1, ['right']); G.step(60);
log.push('key2 ' + !!G.SAVE.items.xsa_key2);
// a real strike reaches a portrait (jump attack under f2)
G.tp('CM13', 8, 15); G.step(30); const f2 = A.KIT.byId.f2, fl0 = f2.flash; G.step(1, [], ['jump']); G.step(8, ['jump']); G.step(1, ['jump'], ['attack']); G.step(10); log.push('jump strike reaches a portrait ' + (f2.flash > 0 || f2.lit));
// the false bookcase in the East Wing
G.tp('CM9', 79, 7); G.step(30); G.P.face = 1; for (let i = 0; i < 4; i++) { G.step(1, ['right'], ['attack']); G.step(20); } log.push('bookcase flag ' + G.SAVE.flags['x3:CM9:bookcase']); for (let i = 0; i < 80 && G.room === 'CM9'; i++) G.step(1, ['right']); log.push('through the bookcase -> ' + G.room);
// the keys and the study hatch
G.tp('CM17', 4, 6); G.step(60); log.push('key1 ' + !!G.SAVE.items.xsa_key1);
G.tp('CM12', 36, 5); G.step(60); log.push('key3 ' + !!G.SAVE.items.xsa_key3);
G.tp('CM14', 2, 15); G.step(30); log.push('gate before ' + A.kitOn('gS')); G.step(1, [], ['interact']); G.step(90); log.push('study unlocked ' + G.SAVE.flags['xsa:study'] + ' gate ' + A.kitOn('gS'));
for (let i = 0; i < 60; i++) G.step(1, ['left']); log.push('walked west through the study gate -> ' + G.room); G.step(120); await snap('study');
// the Drowned Bell: break the well cover in the Tide Steps, dive
G.tp('DB13', 17, 21); G.step(10); for (let i = 0; i < 6; i++) { G.step(1, ['down'], ['attack']); G.step(25, ['down']); }
for (let i = 0; i < 200 && G.room === 'DB13'; i++) G.step(1, ['down']);
log.push('well -> ' + G.room); G.step(60); await snap('bell');
// the Witch's Larder: dash through the thorn curtain
G.tp('TV9', 108, 11); G.step(30); G.P.face = 1; G.step(1, ['right'], ['roll']); for (let i = 0; i < 60 && G.room === 'TV9'; i++) G.step(1, ['right']);
log.push('thorn curtain -> ' + G.room); G.step(60); await snap('larder');
// the tide over one cycle (row of the line)
G.tp('DB13', 3, 17); const ys = []; for (let i = 0; i < 17; i++) { G.step(60); ys.push(A.tideY() === null ? -1 : +A.tideY().toFixed(1)); } log.push('tide rows over 17 s: ' + ys.join(' '));
// the snare on the Hunter's Trail
G.tp('TV10', 13, 11); G.SETTINGS.god = 0; G.P.hp = 999; const hp0 = G.P.hp; for (let i = 0; i < 90; i++) G.step(1, ['right']); log.push('snare hurt ' + (hp0 - G.P.hp)); G.SETTINGS.god = 1;
// Thornstep Ring: three strikes in the air
G.SAVE.charmsEq = ['c_x3_thorn']; G.tp('TV9', 36, 27); G.step(30); G.step(1, [], ['jump']); let n = 0;
for (let i = 0; i < 60; i++) { const was = G.P.state; G.step(1, ['jump'], i % 8 === 2 ? ['attack'] : []); if (G.P.state === 'air_attack' && was !== 'air_attack') n++; }
log.push('air attacks in one jump with the ring: ' + n);
return log;
