await boot();
G.SETTINGS.god = true; W.noFoes = true;
const out = [];
const act = n => { for (let i = 0; i < (n || 1); i++) st1([], ['interact']); for (let i = 0; i < 20; i++) st1([], []); };
const wait = n => { for (let i = 0; i < n; i++) st1([], []); };
G.tp('R2', 40, 10); wait(20); W.last = G.room;
const leg = async (name, steps) => { const f0 = W.frames; const ok = await route(steps); out.push(`${ok ? 'OK ' : 'BAD'} ${name} (${W.frames - f0} frames)${ok ? '' : ' :: ' + W.fail}`); W.fail = null; return ok; };
// ---- in: R2 -> R3 -> up through its roof onto the Long Wall -> west along the walk -> tower -> Barracks
await leg('R2 -> R3', [['R3', 5, 10]]);
await leg('R3 roof stair -> R5 east shaft', [['R3', 4, 7], ['R3', 2, 4], ['R3', 2, 1], ['R5', 125, 20], ['R5', 123, 17], ['R5', 120, 14], ['R5', 123, 11], ['R5', 122, 8]]);
await leg('R5 wall-walk west -> west tower', [['R5', 60, 8], ['R5', 27, 8], ['R5', 11, 8]]);
await leg('R5 tower -> R7 Barracks', [['R5', 16, 5], ['R5', 5, 4], ['R7', 44, 10]]);
await leg('R7 -> down into R8 upper tunnel', [['R7', 10, 10], ['R8', 5, 3], ['R8', 10, 6]]);
await leg('R8 winch lever', [['R8', 16, 6]]); out.push(`at lever: ${G.room} ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} before ${G.KIT.byId.winch.active} state ${G.P.state} ${G.state}`); G.step(1, [], ['interact']); G.step(10); out.push('winch after G.step interact: ' + G.KIT.byId.winch.active); act(); out.push('winch on: ' + G.KIT.byId.winch.active);
await leg('R8 call the lift, ride down', [['R8', 18, 6]]); wait(150); await leg('R8 step on', [['R8', 21, 6]]); wait(200);
await leg('R8 lower tunnel -> R5 sally port', [['R8', 21, 11], ['R8', 44, 11], ['R5', 8, 19], ['R8', 40, 11], ['R5', 8, 19], ['R5', 28, 19]]);
await leg('R5 sally port -> drop to R1 (first shrine)', [['R1', 6, 10, { nojump: true }]]);
// ---- back: R1 -> R2 -> R3 -> R5 -> R7 -> R8 -> R7 -> R5 -> drop back into R3
await leg('R1 -> R2 -> R3', [['R1', 44, 10], ['R2', 17, 8], ['R2', 22, 6], ['R2', 33, 10], ['R2', 44, 7], ['R3', 5, 10]]);
await leg('R3 -> R5 again', [['R3', 4, 7], ['R3', 2, 4], ['R3', 2, 1], ['R5', 125, 20], ['R5', 123, 17], ['R5', 120, 14], ['R5', 123, 11], ['R5', 122, 8], ['R5', 27, 8], ['R5', 11, 8], ['R5', 16, 5], ['R5', 5, 4], ['R7', 44, 10], ['R7', 10, 10], ['R8', 5, 3]]);
await leg('R8 -> back up into R7 -> R5', [['R8', 4, 3], ['R8', 4, 0], ['R7', 3, 12], ['R7', 44, 10], ['R5', 5, 4]]);
await leg('R5 -> east -> drop into R3', [['R5', 11, 8], ['R5', 27, 8], ['R5', 122, 8], ['R5', 123, 11], ['R5', 120, 14], ['R5', 123, 17], ['R5', 125, 20], ['R3', 2, 1, { drop: true }]]);
// ---- branches
await leg('R3 -> R5 -> tower -> R9 signal stair', [['R3', 2, 4, { drop: true }], ['R3', 4, 7], ['R3', 2, 4], ['R3', 2, 1], ['R5', 125, 20], ['R5', 123, 17], ['R5', 120, 14], ['R5', 123, 11], ['R5', 122, 8], ['R5', 27, 8], ['R5', 11, 8], ['R5', 16, 5], ['R5', 8, 2], ['R5', 10, 0], ['R9', 10, 25]]);
await leg('R9 climb -> R10', [['R9', 15, 22], ['R9', 6, 19], ['R9', 15, 16], ['R9', 6, 13], ['R9', 11, 10], ['R9', 18, 7], ['R10', 3, 7]]);
await leg('R10 crenel run -> R11 perch', [['R10', 11, 7], ['R10', 17, 8], ['R10', 23, 7], ['R10', 28, 6], ['R10', 34, 8], ['R10', 38, 8], ['R10', 42, 7], ['R10', 48, 7], ['R10', 53, 6], ['R10', 60, 7], ['R11', 4, 7]]);
await leg('R11 -> back through R10 -> R9', [['R11', 2, 7], ['R10', 60, 7], ['R10', 53, 6], ['R10', 48, 7], ['R10', 43, 7], ['R10', 38, 8], ['R10', 34, 8], ['R10', 28, 6], ['R10', 23, 7], ['R10', 17, 8], ['R10', 11, 7], ['R10', 3, 7], ['R9', 18, 7]]);
await leg('R9 -> break the cracked wall -> R14', [['R9', 11, 10], ['R9', 6, 13], ['R9', 12, 25], ['R9', 17, 22], ['R9', 21, 22]]);
for (let i = 0; i < 10; i++) { st1(['right'], ['attack']); wait(14); }
await leg('R9 -> R14 cache', [['R14', 6, 6]]);
await leg('R14 -> R9 -> down to R5', [['R9', 18, 22], ['R9', 12, 25], ['R5', 10, 0, { drop: true }], ['R5', 10, 2, { drop: true }], ['R5', 16, 5]]);
await leg('R5 -> R7 -> up into R6', [['R5', 5, 4], ['R7', 44, 10], ['R7', 40, 7], ['R7', 44, 4], ['R7', 41, 1], ['R6', 38, 12]]);
await leg('R6 -> R13 muster yard', [['R6', 10, 10], ['R13', 30, 10], ['R13', 10, 10]]);
await leg('R13 -> R6 -> down to R7', [['R13', 33, 10], ['R6', 20, 10], ['R7', 41, 1], ['R7', 40, 7, { drop: true }], ['R7', 30, 10]]);
await leg('R7 -> R8 -> R12 winch house', [['R7', 10, 10], ['R8', 5, 3], ['R8', 2, 6], ['R12', 27, 12]]);
await leg('R12 -> back to R8', [['R12', 29, 12], ['R8', 3, 6]]);
out.push('rooms crossed: ' + W.log.join(', '));
return out;
