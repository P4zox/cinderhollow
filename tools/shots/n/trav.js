// Traversal: doors both ways, the grate drop, the dry gate lever, bell walkways, the hanging platform, the sealed stair.
await boot(); G.give({ stats: { vig: 60, end: 40 }, items: { talon: 1, wings: 1 } });
const out = [];
const walkTo = (dir, n = 400, stop) => { for (let i = 0; i < n; i++) { G.step(2, [dir]); G.P.hp = 99999; if (stop && stop()) return true; } return false; };
// 1. C2 grate: stand on it, drop through (down+jump)
G.tp('C2', 37, 10); G.step(30); await snap('t1_grate');
G.step(2, ['down'], ['jump']); for (let i = 0; i < 60 && G.room === 'C2'; i++) G.step(3);
out.push(`grate drop -> ${G.room} at ${Math.round(G.P.x)},${Math.round(G.P.y)}`);
for (let i = 0; i < 80; i++) G.step(3);
out.push(`fell to ${G.room} y=${Math.round(G.P.y / 16)}`);
// 2. NV1 dry gate: closed from the west, the lever on the east opens it
G.tp('NV1', 12, 21); const gateClosed = !walkTo('right', 120, () => G.P.x > 17 * 16);
out.push(`NV1 gate blocks from the west: ${gateClosed} (x=${Math.round(G.P.x)})`);
G.tp('NV1', 20, 21); G.step(10); G.step(2, [], ['interact']); G.step(60);
out.push(`lever flag ${!!G.SAVE.flags['lever:NV1']}`);
G.tp('NV1', 12, 21); G.step(60); const passed = walkTo('right', 300, () => G.room === 'NV2'); out.push(`gate prop open: ${G.props.filter(p => p.type === 'gate').map(p => p.open)} x=${Math.round(G.P.x)}`);
out.push(`NV1 -> NV2 through the opened gate: ${passed}`);
await snap('t2_nv2');
walkTo('left', 300, () => G.room === 'NV1'); out.push(`NV2 -> NV1 back: ${G.room === 'NV1'}`);
// 3. NV2 -> NV3 and back
G.tp('NV2', 30, 10); out.push(`NV2 -> NV3: ${walkTo('right', 200, () => G.room === 'NV3')}`);
G.step(20); out.push(`NV3 -> NV2: ${walkTo('left', 200, () => G.room === 'NV2')}`);
// 4. bell walkways: a bridge vanishes under you (you fall to the ledge below); a bridge never closes on a body
G.tp('NV3', 8, 11); G.step(10); const nvr = G.NVR || window.__game.NVR;
out.push(`on bridge A: ground ${G.P.ground} y=${Math.round(G.P.y)} phase ${nvr.bell.phase}`);
G.nvToll(); G.step(60); out.push(`after toll: y=${Math.round(G.P.y)} (fell to the next level ${Math.round(G.P.y / 16)})`);
await snap('t4_bell');
// stand inside a B-bridge cell when it returns: must stay passable until you leave
G.tp('NV3', 10, 18); G.step(2); const w = nvr.walks.find(w => w.set === 1 && w.x === 10 && w.y === 18);
G.P.x = 10 * 16 + 8; G.P.y = 18 * 16 + 12; G.P.vy = 0;
G.nvToll(); G.step(1);
out.push(`walkway B cell with a body inside: on=${w && w.on} (must be false)`);
// 5. NV3 bottom -> NV4 and back
G.tp('NV3', 3, 41); out.push(`NV3 -> NV4: ${walkTo('left', 200, () => G.room === 'NV4')}`);
G.step(20); out.push(`NV4 -> NV3: ${walkTo('right', 200, () => G.room === 'NV3')}`);
// 6. the hanging platform over the second pit
G.tp('NV4', 37, 16); G.step(10); const pl = nvr.plats[0];
out.push(`on platform: ground ${G.P.ground} x=${Math.round(G.P.x)} plat x0=${Math.round(pl.d.x0)}`);
G.nvToll(); G.step(150); out.push(`carried: x=${Math.round(G.P.x)} plat x0=${Math.round(pl.d.x0)} ground ${G.P.ground} hp ${Math.round(G.P.hp)}`);
walkTo('right', 30); out.push(`stepped off onto the street x=${Math.round(G.P.x / 16)} y=${Math.round(G.P.y / 16)}`);
await snap('t6_plat');
// 7. the sealed stair: gate closed from inside the attic; the lever on the ledge opens it
G.tp('NV4', 59, 4); G.step(10); const blocked = !walkTo('right', 100, () => G.P.x > 63 * 16);
out.push(`attic gate blocks: ${blocked}`);
G.tp('NV4', 65, 4); G.step(10); G.step(2, [], ['interact']); G.step(60);
G.tp('NV4', 59, 4); out.push(`attic -> ledge after lever: ${walkTo('right', 100, () => G.P.x > 64 * 16)}`);
// 8. the bottom tier doors: NV4 -> NV5 -> NV6 -> NV7 and back (bosses cleared so fog is down)
G.SAVE.flags['boss:executioners'] = 1; G.SAVE.flags['boss:vael'] = 1;
G.tp('NV4', 4, 16); out.push(`NV4 -> NV5: ${walkTo('left', 200, () => G.room === 'NV5')}`);
out.push(`NV5 -> NV6: ${walkTo('left', 600, () => G.room === 'NV6')}`);
out.push(`NV6 -> NV7: ${walkTo('left', 600, () => G.room === 'NV7')}`);
out.push(`NV7 -> NV6: ${walkTo('right', 900, () => G.room === 'NV6')}`);
out.push(`NV6 -> NV5: ${walkTo('right', 600, () => G.room === 'NV5')}`);
out.push(`NV5 -> NV4: ${walkTo('right', 600, () => G.room === 'NV4')}`);
return out;
