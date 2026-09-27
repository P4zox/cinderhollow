await boot(); G.SAVE.items.wings = 1; G.SETTINGS.god = true;
const out = [], K = G.KIT;
G.tp('T1', 27, 32); G.step(230);
// run and jump off the ledge toward the first rope
for (let i = 0; i < 8; i++) G.step(1, ['right']);
G.step(1, ['right'], ['jump']);
let grabbed = -1;
for (let i = 0; i < 60; i++) { G.step(1, ['right', 'jump']); if (G.P.state === 'hook') { grabbed = i; break; } }
out.push('grabbed at ' + grabbed + ' state ' + G.P.state);
for (let i = 0; i < 4; i++) { G.step(12, [i % 2 ? 'left' : 'right']); await snap('sw_' + i); }
// pump then let go toward the next rope
for (let i = 0; i < 90; i++) G.step(1, [Math.floor(i / 25) % 2 ? 'left' : 'right']);
let r = K.objs.filter(q => q.kind === 'swing'); out.push('held ' + r.map(q => q.held).join(','));
let best = null; for (let i = 0; i < 60; i++) { G.step(1, ['right']); if (G.P.hook && G.P.hook.av > 1.5) { best = i; break; } }
G.step(1, ['right'], ['jump']); out.push('released vx ' + Math.round(G.P.vx) + ' vy ' + Math.round(G.P.vy));
let next = -1; for (let i = 0; i < 70; i++) { G.step(1, ['right']); if (r[1].held) { next = i; break; } }
out.push('grabbed rope2 after ' + next);
await snap('sw_4');
return out;
