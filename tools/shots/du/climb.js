await boot(); G.grantTechniques(); G.give({ items: { talon: 1 } }); const o = [];
G.SAVE.flags['boss:scarab'] = 1; G.SAVE.flags['boss:pharaoh'] = 1;
const pos = () => [G.room, Math.round(G.P.x/16*10)/10, Math.round(G.P.y/16*10)/10, G.P.state].join(' ');
// climb to a platform: (tx, ty) = tile col, the row the player stands in (one above the platform)
const ORG = { DU1: [400, 84], DU7: [408, 102], DU8: [400, 128], DU4: [560, 84] };
async function to(tx, ty, room, label, max = 400, inRoom = null) {
  const R0 = inRoom || room || G.room, gxy = [ORG[R0][0] + tx, ORG[R0][1] + ty];
  for (let i = 0; i < max; i++) {
    const o_ = ORG[G.room] || [0, 0], X = (gxy[0] - o_[0]) * 16 + 8, Y = (gxy[1] - o_[1] + 1) * 16;
    G.P.hp = G.D.maxHp; for (const e of G.enemies) if (e.alive) { e.hp = 0; e.state = 'dead'; }
    if (room && G.room !== room) { o.push(label + ' left room ' + pos()); return false; }
    const dx = X - G.P.x, above = G.P.y - Y;
    if (Math.abs(dx) < 6 && Math.abs(above) < 3 && G.P.ground) { o.push(label + ' ok ' + pos()); return true; }
    const key = Math.abs(dx) < 3 ? [] : [dx > 0 ? 'right' : 'left'];
    if (G.P.ground && above > 8 && Math.abs(dx) < 5 * 16) { G.step(1, key, ['jump']); for (let k = 0; k < 18; k++) G.step(1, [...key, 'jump']); continue; }
    if (G.P.ground && above < -8 && Math.abs(dx) < 10) { G.step(1, ['down'], ['jump']); G.step(8); continue; }
    G.step(1, key);
  }
  o.push(label + ' FAIL ' + pos()); await snap('climb_fail_' + label.replace(/\W/g, '_')); return false;
}
// DU4: bottom -> top door (zigzag platforms)
G.tp('DU4', 12, 35); G.step(10);
for (const [x, y, l] of [[17, 32, 'p33'], [11, 29, 'p30'], [5, 26, 'p27'], [11, 23, 'p24'], [17, 20, 'p21'], [11, 17, 'p18'], [4, 14, 'ledge']]) await to(x, y, 'DU4', 'DU4 ' + l);
for (let i = 0; i < 40 && G.room === 'DU4'; i++) G.step(2, ['left']);
o.push('DU4 top exit ' + pos());
// DU4 alcove (shard)
G.tp('DU4', 4, 14); G.step(5);
for (const [x, y, l] of [[10, 11, 'p12'], [17, 8, 'p9'], [21, 5, 'alcove']]) await to(x, y, 'DU4', 'DU4 ' + l);
await snap('c_du4_alcove');
// DU7: lever, then up the shaft into DU1
G.tp('DU7', 29, 17); G.step(5); G.step(1, [], ['interact']); G.step(40); o.push('lever ' + JSON.stringify(!!G.SAVE.flags['lever:DU7']));
for (const [x, y, l] of [[30, 14, 'plat'], [33, 13, 's14'], [34, 10, 's11'], [33, 7, 's8'], [34, 4, 's5'], [33, 1, 's2']]) await to(x, y, 'DU7', 'DU7 ' + l);
await to(41, 16, null, 'DU1 s17', 400, 'DU1'); await to(42, 13, null, 'DU1 s14', 400, 'DU1'); await to(41, 10, null, 'DU1 top', 400, 'DU1');
await snap('c_du1_hatch');
// back down: drop through the hatch into DU7
G.step(1, ['down'], ['jump']); G.step(60); o.push('drop ' + pos());
// DU7 stairwell drop into the Sanctum, then climb back out
G.tp('DU7', 2, 17); G.step(5); G.step(1, ['down'], ['jump']); G.step(90); o.push('sanctum drop ' + pos());
await snap('c_du8_drop');
G.tp('DU8', 8, 14); G.step(5);
for (const [x, y, l] of [[6, 11, 'p12'], [11, 8, 'p9'], [6, 5, 'p6'], [11, 4, 'p5'], [11, 1, 'p2']]) await to(x, y, 'DU8', 'DU8 ' + l);
for (const [x, y, l] of [[3, 24, 'st25'], [4, 21, 'st22'], [4, 18, 'st19'], [3, 17, 'hall']]) await to(x, y, null, 'DU7 ' + l, 400, 'DU7');
await snap('c_du7_back');
return o;
