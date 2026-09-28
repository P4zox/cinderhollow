await boot();
G.SETTINGS.god = true; W.noFoes = true; G.grantTechniques();
const out = [];
const act = () => { st1([], ['interact']); for (let i = 0; i < 20; i++) st1([], []); };
const wait = n => { for (let i = 0; i < n; i++) st1([], []); };
const leg = async (name, steps) => { const f0 = W.frames; const ok = await route(steps); out.push(`${ok ? 'OK ' : 'BAD'} ${name} (${W.frames - f0} frames)${ok ? '' : ' :: ' + W.fail}`); W.fail = null; return ok; };
G.tp('C2', 30, 10); wait(20); W.last = G.room;
const D = { drop: true }, GP = { gapdy: 60 };
// ---- in: C2 -> the Ossuary Well (W2) -> C8 -> up to C7 -> gate -> C3
await leg('C2 -> down the well W2 -> C8 floor', [['C2', 37, 10], ['W2', 1, 12, D], ['W2', 3, 14, D], ['C8', 21, 22, D], ['C8', 19, 28, D]]);
const upC7 = [['C8', 36, 25], ['C8', 33, 22], ['C8', 44, 19], ['C8', 48, 16], ['C8', 48, 13], ['C8', 40, 10], ['C8', 33, 7], ['C8', 29, 4], ['C8', 31, 4], ['C8', 32, 1], ['C7', 5, 14]];
await leg('C8 shelves -> up into C7', upC7);
await leg('C7 -> the lever', [['C7', 20, 12], ['C7', 28, 12]]); act(); out.push('gate open: ' + (G.KIT.byId.gt && G.KIT.byId.gt.on) + ' in ' + G.room);
await leg('C7 -> climb into C3 (Hall of Roots)', [['C7', 36, 12], ['C7', 44, 9], ['C7', 39, 6], ['C7', 44, 3], ['C7', 45, 0], ['C3', 14, 11], ['C3', 20, 10]]);
// ---- back: C3 -> C7 -> C8 -> up the well -> C2
await leg('C3 -> drop into C7 -> west -> C8', [['C3', 14, 11], ['C7', 45, 9, D], ['C7', 36, 12, D], ['C7', 14, 12], ['C8', 32, 1], ['C8', 33, 7, D], ['C8', 40, 10, D], ['C8', 48, 13], ['C8', 50, 19], ['C8', 58, 28], ['C8', 40, 28]]);
await leg('C8 -> up the well -> C2', [['C8', 36, 25], ['C8', 33, 22], ['C8', 44, 19], ['C8', 48, 16], ['C8', 48, 13], ['C8', 26, 10], ['C8', 21, 7], ['C8', 21, 4], ['C8', 21, 1],
  ['W2', 3, 14], ['W2', 1, 12], ['W2', 3, 9], ['W2', 1, 6], ['W2', 3, 3], ['W2', 2, 0], ['C2', 37, 12], ['C2', 37, 10], ['C2', 30, 10]]);
// ---- branches
await leg('C2 -> W2 -> C13 Charnel Pit', [['C2', 37, 10], ['W2', 1, 12, D], ['C13', 31, 10], ['C13', 15, 11]]);
await leg('C13 -> W2 -> C8', [['C13', 31, 10], ['W2', 1, 12], ['W2', 3, 14, D], ['C8', 21, 1, D], ['C8', 21, 4, D]]);
G.P.face = -1; for (let i = 0; i < 8; i++) { st1([], ['attack']); wait(14); } out.push('gallery wall broken: ' + !window.__ra.solid(window.__ra.tile(19, 3)) + ' at ' + G.room + ' ' + (G.P.x/16).toFixed(1) + ',' + (G.P.y/16).toFixed(1));
await leg('C8 gallery (cracked wall) -> C11 top -> back', [['C8', 12, 5], ['C11', 16, 5], ['C8', 12, 5], ['C8', 21, 4]]);
await leg('C8 -> C11 lower door -> back', [['C8', 21, 22, D], ['C8', 19, 28, D], ['C8', 8, 28], ['C8', 2, 27], ['C11', 20, 27], ['C8', 2, 27], ['C8', 12, 28]]);
await leg('C8 -> drop shaft C9 -> C10', [['C8', 22, 28], ['C9', 13, 1], ['C9', 14, 4, D], ['C9', 6, 7, GP], ['C9', 18, 10, GP], ['C10', 5, 10]]);
await leg('C10 -> the false tomb', [['C10', 35, 10]]);
for (let i = 0; i < 8 && G.room === 'C10'; i++) { st1([], ['jump']); wait(6); st1(['down'], ['attack']); for (let k = 0; k < 40 && G.room === 'C10'; k++) st1([], []); }
out.push('after the tomb: ' + G.room);
await leg('C10 -> C14 stash -> back up', [['C14', 3, 6, D], ['C14', 12, 9], ['C14', 3, 6], ['C14', 6, 3], ['C14', 5, 0], ['C10', 33, 11], ['C10', 10, 10]]);
await leg('C10 -> C9 -> C12 crypt -> back', [['C9', 18, 10], ['C9', 5, 11, GP], ['C9', 15, 14, GP], ['C9', 5, 17, GP], ['C9', 15, 20, GP], ['C9', 5, 23, GP], ['C9', 15, 26, GP], ['C9', 4, 29, GP], ['C12', 36, 13], ['C9', 4, 29]]);
await leg('C9 -> down onto the Necropolis roof (NV1) -> back up C9 -> C8', [['C9', 15, 32, GP], ['C9', 5, 35, GP], ['C9', 12, 38, GP], ['C9', 7, 40, GP], ['NV1', 13, 1, D],
  ...[[7, 40], [13, 38], [5, 35], [15, 32], [5, 29], [15, 26], [5, 23], [15, 20], [5, 17], [15, 14], [5, 11], [16, 10], [6, 7], [13, 4], [13, 1]].map(([x, y]) => ['C9', x, y, { jx: 90 }]), ['C8', 24, 30]]);
await leg('C8 -> slam through the sealed floor', [['C8', 6, 28]]);
for (let i = 0; i < 4 && G.room === 'C8'; i++) { st1([], ['jump']); wait(18); st1(['down'], ['heavy']); wait(60); }
await leg('C15 -> out into C9', [['C15', 6, 9], ['C15', 5, 6], ['C15', 10, 3], ['C9', 6, 7]]);
out.push('rooms crossed: ' + W.log.join(', '));
return out;
