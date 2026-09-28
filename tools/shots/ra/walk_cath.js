await boot();
G.SETTINGS.god = true; W.noFoes = true; G.SAVE.items.talon = 1; G.SAVE.items.wings = 1;
const out = [], D = { drop: true };
const act = () => { st1([], ['interact']); for (let i = 0; i < 20; i++) st1([], []); };
const wait = n => { for (let i = 0; i < n; i++) st1([], []); };
const leg = async (name, steps) => { const f0 = W.frames; const ok = await route(steps); out.push(`${ok ? 'OK ' : 'BAD'} ${name} (${W.frames - f0} frames)${ok ? '' : ' :: ' + W.fail}`); W.fail = null; return ok; };
G.tp('K1', 20, 10); wait(20); W.last = G.room;
// ---- in: K1 -> up through its vault -> K5 -> K7 -> east -> K8 -> lever -> down into K2
await leg('K1 vault stair -> K5', [['K1', 14, 8], ['K1', 22, 6], ['K1', 30, 3], ['K1', 31, 0], ['K5', 15, 12], ['K5', 20, 10]]);
await leg('K5 -> up into K7', [['K5', 29, 7], ['K5', 29, 4], ['K5', 29, 1], ['K7', 43, 28], ['K7', 50, 26]]);
await leg('K7 floor east -> down into K8', [['K7', 80, 26], ['K7', 89, 28, { pass: true }], ['K8', 34, 1, D], ['K8', 30, 10, D]]);
await leg('K8 booths -> lever', [['K8', 7, 10]]); act(); out.push('K8 gate open: ' + G.KIT.byId.gk.on);
await leg('K8 -> drop into K2', [['K8', 2, 12], ['K2', 10, 1, D], ['K2', 20, 10, D]]);
// ---- back: K2 -> K8 -> K7 -> K5 -> K1
await leg('K2 vault stair -> K8', [['K2', 9, 7], ['K2', 11, 4], ['K2', 10, 1], ['K8', 2, 12], ['K8', 10, 10]]);
await leg('K8 -> up into K7', [['K8', 37, 7], ['K8', 33, 4], ['K8', 34, 1], ['K7', 87, 28], ['K7', 80, 26]]);
await leg('K7 -> west -> drop into K5', [['K7', 50, 26], ['K7', 45, 28, { pass: true }], ['K5', 29, 1, D], ['K5', 20, 10, D]]);
await leg('K5 -> drop into K1', [['K5', 15, 12], ['K1', 31, 0, D], ['K1', 26, 10, D]]);
// ---- branches
await leg('K1 -> K5 -> the altar wall', [['K1', 14, 8], ['K1', 22, 6], ['K1', 30, 3], ['K1', 31, 0], ['K5', 15, 12], ['K5', 4, 10]]);
G.P.face = -1; for (let i = 0; i < 8; i++) { st1([], ['attack']); wait(14); }
await leg('K5 -> K13 sacristy -> back', [['K13', 8, 10], ['K5', 6, 10]]);
await leg('K5 -> K7 -> chimney -> clerestory walk', [['K5', 29, 7], ['K5', 29, 4], ['K5', 29, 1], ['K7', 43, 28], ['K7', 20, 26], ['K7', 2, 26], ['K7', 5, 7, { wall: true, jx: 60, max: 1400 }]]);
await leg('K7 walk east -> K11 rose window -> back', [['K7', 22, 7], ['K7', 31, 7], ['K7', 60, 7], ['K7', 70, 7], ['K7', 75, 4], ['K7', 75, 1], ['K11', 18, 18], ['K11', 11, 16], ['K11', 18, 18], ['K7', 75, 1, D], ['K7', 80, 7, D]]);
await leg('K7 walk west -> K9 stair -> back down to K7 -> up again', [['K7', 70, 7], ['K7', 60, 7], ['K7', 31, 7], ['K7', 22, 7], ['K7', 5, 7], ['K7', 3, 4], ['K7', 3, 1], ['K9', 3, 18], ['K7', 3, 1, D], ['K9', 3, 18], ['K9', 3, 15], ['K9', 3, 12], ['K9', 5, 10]]);
await leg('K9 chandeliers -> east platform', [['K9', 10, 10], ['K9', 16, 9], ['K9', 22, 11], ['K9', 28, 9], ['K9', 34, 8], ['K9', 40, 9], ['K9', 46, 7]]);
await leg('K9 -> K10 organ loft -> back', [['K9', 49, 4], ['K9', 49, 1], ['K10', 26, 16], ['K10', 20, 14], ['K10', 26, 16], ['K9', 49, 1, D], ['K9', 50, 7, D]]);
// ---- the K3s branch: the Reliquary of Wings -> K6 -> K12
G.tp('K3s', 10, 8); wait(20); W.last = G.room;
await leg('K3s ceiling -> K6', [['K3s', 3, 5], ['K3s', 3, 2], ['K6', 3, 26], ['K6', 8, 24], ['K6', 16, 24], ['K6', 6, 21]]);
await leg('K6 stair up -> K12 floor', [['K6', 8, 20], ['K6', 12, 18], ['K6', 16, 16], ['K6', 20, 15], ['K6', 18, 12], ['K6', 14, 10], ['K6', 10, 8], ['K6', 5, 7], ['K6', 9, 4], ['K6', 9, 1], ['K12', 8, 40], ['K12', 14, 38]]);
await leg('K12 -> down K6 -> K3s', [['K12', 8, 40, D], ['K6', 9, 1, D], ['K6', 9, 4, D], ['K6', 3, 7, D], ['K6', 10, 8], ['K6', 14, 10], ['K6', 18, 12], ['K6', 20, 15], ['K6', 12, 24], ['K6', 3, 26], ['K3s', 3, 2, D], ['K3s', 10, 8, D]]);
out.push('rooms crossed: ' + W.log.join(', '));
return out;
