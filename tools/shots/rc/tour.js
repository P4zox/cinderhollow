// screenshots of every RC room from a few viewpoints: node tools/shots/shot.js tools/shots/rc/tour.js tools/shots/rc/out
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.talon = 1; G.SAVE.items.wings = 1;
for (const f of ['boss:cindervane', 'boss:sovereign', 'dp:sluice']) G.SAVE.flags[f] = 1;
G.SAVE.seenAreas = {}; for (const b of ['ramparts','catacombs','cathedral','mire','crown','archives','hoarfrost','spire','deep','lastfield','thornveil','barrows','crimson','necropolis','dunes','starfall','neohallow','ember','hermit']) G.SAVE.seenAreas[b] = 1;
const V = window.__TOUR || {
  SP9: [[40,10],[20,10]], SP10: [[44,10],[10,10]], SP11: [[40,10],[12,10],[37,3]], SP12: [[15,56],[7,35],[6,8]],
  SP8: [[20,17],[40,14],[62,14],[92,14],[81,6],[40,22],[120,14]], SP15: [[25,17],[11,6]], SP14: [[5,14],[40,13]], SP17: [[2,11],[16,2]],
  SP13: [[6,45],[20,43],[28,32],[16,3]], SP16: [[5,33],[20,20],[35,7],[5,4]], LF1: [[8,16],[30,16],[60,16],[80,15],[100,15]],
  D9: [[4,5],[12,37],[20,31]], D10: [[50,11],[25,11],[5,11]], D11: [[85,15],[80,35],[40,35],[46,28],[10,10],[5,35]], D12: [[5,7],[30,8],[58,7]],
  D13: [[30,4],[20,19],[3,7]], D14: [[10,10],[25,10]], D15: [[10,12],[30,12]], D16: [[6,61],[17,52],[12,4]], D17: [[8,11]],
  X6: [[6,11],[30,11],[44,11]], X10: [[10,11],[34,11]], X11: [[20,19],[40,19]], X7: [[5,44],[36,44],[20,37],[36,8],[65,11],[50,26]],
  X8: [[5,28],[12,14]], X9: [[3,16],[30,10],[52,11]], X12: [[4,28],[25,22],[40,27],[47,3],[5,6]] };
const only = window.__ONLY; const log = [];
for (const [id, pts] of Object.entries(V)) {
  if (only && !only.includes(id)) continue;
  for (let i = 0; i < pts.length; i++) {
    try { G.tp(id, pts[i][0], pts[i][1]); G.step(250); for (let k = 0; k < 4 && G.state !== 'play'; k++) G.step(1, [], ['pause']); G.step(20); await snap(`t_${id}_${i}`); log.push(id + ':' + i + ' ' + G.state); }
    catch (e) { log.push(id + ' ERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]); }
  }
}
return log.filter(l => /ERR/.test(l)).concat([log.length + ' shots']);
