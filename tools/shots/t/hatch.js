await boot(); G.give({ items: { talon: 1 } });
const out = {};
// 1) closed hatch: try to climb the shaft from TV2
async function climbShaft(tag) {
  G.tp('TV2', 5, 4); G.enemies.length = 0; G.step(10);
  let dir = -1, rooms = new Set(), minY = 999;
  for (let i = 0; i < 500; i++) {
    const P = G.P; rooms.add(G.room);
    if (G.room === 'TV7' && P.ground && P.y <= 160) break;
    let hold = [], tap = [];
    if (P.state === 'wall') { tap = ['jump']; dir = -P.wallDir; hold = [dir > 0 ? 'right' : 'left']; }
    else if (P.ground) { tap = ['jump']; hold = []; }
    else { hold = ['jump', dir > 0 ? 'right' : 'left']; }
    G.step(1, hold, tap); minY = Math.min(minY, G.room === 'TV2' ? P.y : P.y - 208);
  }
  out[tag] = { room: G.room, p: G.step(1).p, rooms: [...rooms].join(','), minY: Math.round(minY) };
  await snap('hatch_' + tag);
}
await climbShaft('closed');
// 2) pull the lever in TV7 and drop through
G.tp('TV7', 24, 9); G.step(10); G.step(2, [], ['interact']); G.step(60);
out.flag = !!G.SAVE.flags['lever:TV7'];
await snap('hatch_opened');
G.tp('TV7', 29, 9); let r2 = null; for (let i = 0; i < 120 && !r2; i++) { G.step(1); if (G.room !== 'TV7') r2 = G.room; }
out.drop = r2 + ' ' + JSON.stringify(G.step(20).p);
await climbShaft('open');
// 3) thorn wall cutting
G.tp('TV3', 26, 10); G.enemies.length = 0; G.step(10);
let hits = 0; for (let i = 0; i < 12; i++) { G.enemies.length = 0; G.step(28, ['right'], ['attack']); }
out.cut = !!G.SAVE.flags['tvcut:TV3:28,7'];
G.step(40, ['right']); out.afterCut = G.step(1).p;
await snap('cut');
return out;
